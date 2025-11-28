"""
🧠 MACHINE LEARNING UTILITIES (Scikit-learn Integration)

Classical ML algorithms for population-level analysis of the Butterfly System.
Provides clustering, anomaly detection, and dimensionality reduction for
organism populations.

Features:
- HDBSCAN/KMeans clustering for behavioral phenotype identification
- Isolation Forest anomaly detection for unusual organisms
- PCA/t-SNE dimensionality reduction for visualization
- Config-driven enabling/disabling of each subsystem
- Optional dependency - system works without scikit-learn installed
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

# Optional scikit-learn import - graceful degradation if not installed
SKLEARN_AVAILABLE = False
try:
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
    
    # HDBSCAN is a separate package but commonly used with sklearn
    try:
        from hdbscan import HDBSCAN
        HDBSCAN_AVAILABLE = True
    except ImportError:
        HDBSCAN_AVAILABLE = False
except ImportError:
    HDBSCAN_AVAILABLE = False


@dataclass
class ClusteringResult:
    """Results from population clustering"""
    labels: np.ndarray  # Cluster assignment for each organism (-1 = noise/outlier)
    n_clusters: int  # Number of clusters found
    cluster_sizes: Dict[int, int]  # Count of organisms per cluster
    cluster_centroids: Optional[np.ndarray] = None  # Centroid positions if available
    algorithm: str = "none"
    timestamp: float = field(default_factory=time.time)
    
    def get_cluster_organisms(self, cluster_id: int, organism_ids: List[str]) -> List[str]:
        """Get organism IDs belonging to a specific cluster"""
        return [org_id for org_id, label in zip(organism_ids, self.labels) if label == cluster_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'n_clusters': self.n_clusters,
            'cluster_sizes': self.cluster_sizes,
            'algorithm': self.algorithm,
            'timestamp': self.timestamp,
            'noise_count': int(np.sum(self.labels == -1)) if self.labels is not None else 0
        }


@dataclass
class AnomalyResult:
    """Results from anomaly detection"""
    scores: np.ndarray  # Anomaly score for each organism (lower = more anomalous for IF)
    labels: np.ndarray  # -1 = anomaly, 1 = normal
    anomaly_indices: List[int]  # Indices of detected anomalies
    anomaly_ratio: float  # Proportion of anomalies detected
    algorithm: str = "none"
    timestamp: float = field(default_factory=time.time)
    
    def get_anomaly_organisms(self, organism_ids: List[str]) -> List[str]:
        """Get organism IDs flagged as anomalies"""
        return [organism_ids[i] for i in self.anomaly_indices]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'anomaly_count': len(self.anomaly_indices),
            'anomaly_ratio': self.anomaly_ratio,
            'algorithm': self.algorithm,
            'timestamp': self.timestamp
        }


@dataclass
class ReductionResult:
    """Results from dimensionality reduction"""
    coordinates: np.ndarray  # Reduced coordinates (n_organisms x n_components)
    n_components: int
    explained_variance: Optional[List[float]] = None  # For PCA
    algorithm: str = "none"
    timestamp: float = field(default_factory=time.time)
    
    def get_organism_coordinates(self, organism_ids: List[str]) -> Dict[str, List[float]]:
        """Get coordinates mapped to organism IDs"""
        return {org_id: coords.tolist() for org_id, coords in zip(organism_ids, self.coordinates)}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'n_components': self.n_components,
            'explained_variance': self.explained_variance,
            'algorithm': self.algorithm,
            'timestamp': self.timestamp,
            'sample_count': len(self.coordinates) if self.coordinates is not None else 0
        }


class PopulationClusterer:
    """
    Clusters organism population by behavioral/trait vectors.
    
    Identifies emergent phenotype groups without predefined K (using HDBSCAN)
    or with configurable K (using KMeans).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.algorithm = self.config.get('algorithm', 'hdbscan')
        self.min_cluster_size = self.config.get('min_cluster_size', 5)
        self.min_samples = self.config.get('min_samples', 3)
        self.n_clusters = self.config.get('n_clusters', 5)  # For KMeans
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._last_result: Optional[ClusteringResult] = None
    
    def extract_features(self, organisms: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """
        Extract feature vectors from organisms.
        
        Features include:
        - Phenotype traits (trait_0 through trait_9)
        - Fitness value
        - Resources (if available)
        - Connection count (if available)
        """
        organism_ids = list(organisms.keys())
        features = []
        
        for org_id in organism_ids:
            org = organisms[org_id]
            feature_vec = []
            
            # Extract phenotype traits
            if hasattr(org, 'phenotype') and hasattr(org.phenotype, 'traits'):
                for i in range(10):  # trait_0 through trait_9
                    trait_name = f"trait_{i}"
                    feature_vec.append(org.phenotype.traits.get(trait_name, 0.0))
            else:
                feature_vec.extend([0.0] * 10)
            
            # Fitness
            fitness = getattr(org, 'fitness', 0.0)
            feature_vec.append(fitness)
            
            # Resources (if available)
            resources = getattr(org, 'resources', 0.5)
            feature_vec.append(resources)
            
            # Genotype age
            if hasattr(org, 'genotype'):
                feature_vec.append(getattr(org.genotype, 'age', 0) / 100.0)  # Normalize
            else:
                feature_vec.append(0.0)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_predict(self, organisms: Dict[str, Any]) -> ClusteringResult:
        """
        Cluster organisms and return results.
        
        Returns empty result if sklearn not available or insufficient data.
        """
        if not SKLEARN_AVAILABLE:
            return ClusteringResult(
                labels=np.array([]),
                n_clusters=0,
                cluster_sizes={},
                algorithm="unavailable"
            )
        
        if len(organisms) < self.min_cluster_size:
            return ClusteringResult(
                labels=np.zeros(len(organisms), dtype=int),
                n_clusters=1 if organisms else 0,
                cluster_sizes={0: len(organisms)} if organisms else {},
                algorithm="insufficient_data"
            )
        
        features, organism_ids = self.extract_features(organisms)
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Select and run clustering algorithm
        if self.algorithm == 'hdbscan' and HDBSCAN_AVAILABLE:
            clusterer = HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples
            )
            labels = clusterer.fit_predict(features_scaled)
            centroids = None
        elif self.algorithm == 'kmeans':
            n_clusters = min(self.n_clusters, len(organisms))
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = clusterer.fit_predict(features_scaled)
            centroids = clusterer.cluster_centers_
        elif self.algorithm == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=self.min_samples)
            labels = clusterer.fit_predict(features_scaled)
            centroids = None
        else:
            # Fallback to KMeans if HDBSCAN not available
            n_clusters = min(self.n_clusters, len(organisms))
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = clusterer.fit_predict(features_scaled)
            centroids = clusterer.cluster_centers_
            self.algorithm = 'kmeans_fallback'
        
        # Calculate cluster sizes
        unique_labels = set(labels)
        cluster_sizes = {int(label): int(np.sum(labels == label)) for label in unique_labels}
        n_clusters = len([l for l in unique_labels if l >= 0])  # Exclude noise (-1)
        
        self._last_result = ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            cluster_sizes=cluster_sizes,
            cluster_centroids=centroids,
            algorithm=self.algorithm
        )
        
        return self._last_result
    
    @property
    def last_result(self) -> Optional[ClusteringResult]:
        return self._last_result


class AnomalyDetector:
    """
    Detects unusual organisms in the population using Isolation Forest
    or Local Outlier Factor.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.algorithm = self.config.get('algorithm', 'isolation_forest')
        self.contamination = self.config.get('contamination', 0.1)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._last_result: Optional[AnomalyResult] = None
    
    def extract_features(self, organisms: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """Extract feature vectors from organisms (same as clustering)"""
        organism_ids = list(organisms.keys())
        features = []
        
        for org_id in organism_ids:
            org = organisms[org_id]
            feature_vec = []
            
            # Phenotype traits
            if hasattr(org, 'phenotype') and hasattr(org.phenotype, 'traits'):
                for i in range(10):
                    trait_name = f"trait_{i}"
                    feature_vec.append(org.phenotype.traits.get(trait_name, 0.0))
            else:
                feature_vec.extend([0.0] * 10)
            
            # Fitness
            feature_vec.append(getattr(org, 'fitness', 0.0))
            
            # Resources
            feature_vec.append(getattr(org, 'resources', 0.5))
            
            # Genotype age
            if hasattr(org, 'genotype'):
                feature_vec.append(getattr(org.genotype, 'age', 0) / 100.0)
            else:
                feature_vec.append(0.0)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_predict(self, organisms: Dict[str, Any]) -> AnomalyResult:
        """
        Detect anomalies in organism population.
        
        Returns empty result if sklearn not available or insufficient data.
        """
        if not SKLEARN_AVAILABLE:
            return AnomalyResult(
                scores=np.array([]),
                labels=np.array([]),
                anomaly_indices=[],
                anomaly_ratio=0.0,
                algorithm="unavailable"
            )
        
        if len(organisms) < 5:  # Need minimum samples for anomaly detection
            return AnomalyResult(
                scores=np.zeros(len(organisms)),
                labels=np.ones(len(organisms), dtype=int),
                anomaly_indices=[],
                anomaly_ratio=0.0,
                algorithm="insufficient_data"
            )
        
        features, organism_ids = self.extract_features(organisms)
        features_scaled = self.scaler.fit_transform(features)
        
        if self.algorithm == 'isolation_forest':
            detector = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=42
            )
            labels = detector.fit_predict(features_scaled)
            scores = detector.decision_function(features_scaled)
        elif self.algorithm == 'lof':
            detector = LocalOutlierFactor(
                contamination=self.contamination,
                novelty=False
            )
            labels = detector.fit_predict(features_scaled)
            scores = detector.negative_outlier_factor_
        else:
            # Default to Isolation Forest
            detector = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=42
            )
            labels = detector.fit_predict(features_scaled)
            scores = detector.decision_function(features_scaled)
        
        # Find anomaly indices (labels == -1)
        anomaly_indices = [i for i, label in enumerate(labels) if label == -1]
        anomaly_ratio = len(anomaly_indices) / len(organisms) if organisms else 0.0
        
        self._last_result = AnomalyResult(
            scores=scores,
            labels=labels,
            anomaly_indices=anomaly_indices,
            anomaly_ratio=anomaly_ratio,
            algorithm=self.algorithm
        )
        
        return self._last_result
    
    @property
    def last_result(self) -> Optional[AnomalyResult]:
        return self._last_result


class TraitReducer:
    """
    Reduces high-dimensional trait/behavior space to 2D/3D for visualization.
    Uses PCA or t-SNE depending on configuration.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.algorithm = self.config.get('algorithm', 'pca')
        self.n_components = self.config.get('n_components', 3)
        self.tsne_perplexity = self.config.get('tsne_perplexity', 30)
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._last_result: Optional[ReductionResult] = None
    
    def extract_features(self, organisms: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """Extract feature vectors from organisms"""
        organism_ids = list(organisms.keys())
        features = []
        
        for org_id in organism_ids:
            org = organisms[org_id]
            feature_vec = []
            
            # Phenotype traits
            if hasattr(org, 'phenotype') and hasattr(org.phenotype, 'traits'):
                for i in range(10):
                    trait_name = f"trait_{i}"
                    feature_vec.append(org.phenotype.traits.get(trait_name, 0.0))
            else:
                feature_vec.extend([0.0] * 10)
            
            # Fitness
            feature_vec.append(getattr(org, 'fitness', 0.0))
            
            # Resources
            feature_vec.append(getattr(org, 'resources', 0.5))
            
            # Genotype age
            if hasattr(org, 'genotype'):
                feature_vec.append(getattr(org.genotype, 'age', 0) / 100.0)
            else:
                feature_vec.append(0.0)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_transform(self, organisms: Dict[str, Any]) -> ReductionResult:
        """
        Reduce dimensionality of organism features.
        
        Returns empty result if sklearn not available or insufficient data.
        """
        if not SKLEARN_AVAILABLE:
            return ReductionResult(
                coordinates=np.array([]),
                n_components=0,
                algorithm="unavailable"
            )
        
        if len(organisms) < 3:
            return ReductionResult(
                coordinates=np.zeros((len(organisms), self.n_components)),
                n_components=self.n_components,
                algorithm="insufficient_data"
            )
        
        features, organism_ids = self.extract_features(organisms)
        features_scaled = self.scaler.fit_transform(features)
        
        # Limit n_components to number of features/samples
        n_components = min(self.n_components, features.shape[1], len(organisms))
        
        if self.algorithm == 'pca':
            reducer = PCA(n_components=n_components)
            coordinates = reducer.fit_transform(features_scaled)
            explained_variance = reducer.explained_variance_ratio_.tolist()
        elif self.algorithm == 'tsne':
            # t-SNE requires perplexity < n_samples
            perplexity = min(self.tsne_perplexity, len(organisms) - 1, 30)
            reducer = TSNE(
                n_components=min(n_components, 3),  # t-SNE max 3 components
                perplexity=max(5, perplexity),
                random_state=42
            )
            coordinates = reducer.fit_transform(features_scaled)
            explained_variance = None  # t-SNE doesn't have explained variance
        else:
            # Default to PCA
            reducer = PCA(n_components=n_components)
            coordinates = reducer.fit_transform(features_scaled)
            explained_variance = reducer.explained_variance_ratio_.tolist()
        
        self._last_result = ReductionResult(
            coordinates=coordinates,
            n_components=n_components,
            explained_variance=explained_variance,
            algorithm=self.algorithm
        )
        
        return self._last_result
    
    @property
    def last_result(self) -> Optional[ReductionResult]:
        return self._last_result


class MLAnalyzer:
    """
    Unified ML analysis interface for the Butterfly System.
    
    Coordinates clustering, anomaly detection, and dimensionality reduction,
    respecting configuration toggles.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ML analyzer with configuration.
        
        Config structure expected:
        {
            "enabled": true/false,
            "clustering": {"enabled": true, "algorithm": "hdbscan", ...},
            "anomaly_detection": {"enabled": true, "algorithm": "isolation_forest", ...},
            "dimensionality_reduction": {"enabled": true, "algorithm": "pca", ...}
        }
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        
        # Initialize subsystems
        clustering_config = self.config.get('clustering', {})
        anomaly_config = self.config.get('anomaly_detection', {})
        reduction_config = self.config.get('dimensionality_reduction', {})
        
        self.clusterer = PopulationClusterer(clustering_config)
        self.anomaly_detector = AnomalyDetector(anomaly_config)
        self.reducer = TraitReducer(reduction_config)
        
        # Feature toggles
        self.clustering_enabled = clustering_config.get('enabled', True)
        self.anomaly_enabled = anomaly_config.get('enabled', True)
        self.reduction_enabled = reduction_config.get('enabled', True)
        
        # Last analysis results
        self._last_analysis: Dict[str, Any] = {}
        self._last_analysis_time: float = 0
        self._analysis_interval: float = 5.0  # Minimum seconds between analyses
    
    def update_config(self, config: Dict[str, Any]):
        """Update configuration dynamically (for hot reload)"""
        self.config = config
        self.enabled = config.get('enabled', False)
        
        # Update subsystem configs
        clustering_config = config.get('clustering', {})
        anomaly_config = config.get('anomaly_detection', {})
        reduction_config = config.get('dimensionality_reduction', {})
        
        self.clusterer = PopulationClusterer(clustering_config)
        self.anomaly_detector = AnomalyDetector(anomaly_config)
        self.reducer = TraitReducer(reduction_config)
        
        self.clustering_enabled = clustering_config.get('enabled', True)
        self.anomaly_enabled = anomaly_config.get('enabled', True)
        self.reduction_enabled = reduction_config.get('enabled', True)
    
    def analyze(self, organisms: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """
        Run all enabled ML analyses on organism population.
        
        Args:
            organisms: Dict mapping organism IDs to Organism objects
            force: If True, run analysis regardless of interval
            
        Returns:
            Dict with clustering, anomaly, and reduction results
        """
        current_time = time.time()
        
        # Rate limiting (unless forced)
        if not force and (current_time - self._last_analysis_time) < self._analysis_interval:
            return self._last_analysis
        
        if not self.enabled or not SKLEARN_AVAILABLE:
            return {
                'enabled': False,
                'sklearn_available': SKLEARN_AVAILABLE,
                'clustering': None,
                'anomalies': None,
                'reduction': None
            }
        
        results = {
            'enabled': True,
            'sklearn_available': True,
            'timestamp': current_time,
            'organism_count': len(organisms)
        }
        
        # Clustering
        if self.clustering_enabled:
            cluster_result = self.clusterer.fit_predict(organisms)
            results['clustering'] = cluster_result.to_dict()
            results['cluster_labels'] = cluster_result.labels.tolist() if cluster_result.labels.size > 0 else []
        else:
            results['clustering'] = None
        
        # Anomaly Detection
        if self.anomaly_enabled:
            anomaly_result = self.anomaly_detector.fit_predict(organisms)
            results['anomalies'] = anomaly_result.to_dict()
            results['anomaly_organisms'] = anomaly_result.get_anomaly_organisms(list(organisms.keys()))
        else:
            results['anomalies'] = None
        
        # Dimensionality Reduction
        if self.reduction_enabled:
            reduction_result = self.reducer.fit_transform(organisms)
            results['reduction'] = reduction_result.to_dict()
            # Include coordinates for visualization
            if reduction_result.coordinates.size > 0:
                results['coordinates'] = reduction_result.get_organism_coordinates(list(organisms.keys()))
        else:
            results['reduction'] = None
        
        self._last_analysis = results
        self._last_analysis_time = current_time
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current ML analyzer status"""
        return {
            'enabled': self.enabled,
            'sklearn_available': SKLEARN_AVAILABLE,
            'hdbscan_available': HDBSCAN_AVAILABLE,
            'clustering_enabled': self.clustering_enabled,
            'anomaly_enabled': self.anomaly_enabled,
            'reduction_enabled': self.reduction_enabled,
            'last_analysis_time': self._last_analysis_time,
            'clusterer_algorithm': self.clusterer.algorithm,
            'anomaly_algorithm': self.anomaly_detector.algorithm,
            'reducer_algorithm': self.reducer.algorithm
        }


# Singleton instance for global access
_ml_analyzer: Optional[MLAnalyzer] = None


def get_ml_analyzer(config: Dict[str, Any] = None) -> MLAnalyzer:
    """Get or create the global ML analyzer instance"""
    global _ml_analyzer
    if _ml_analyzer is None or config is not None:
        _ml_analyzer = MLAnalyzer(config)
    return _ml_analyzer


def is_sklearn_available() -> bool:
    """Check if scikit-learn is available"""
    return SKLEARN_AVAILABLE
