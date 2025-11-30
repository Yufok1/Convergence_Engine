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
- ConceptTracker for semantic naming of stable behavioral clusters (Quick Win #2)
- Optional dependency - system works without scikit-learn installed
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import logging

# Concept tracking for semantic naming (Quick Win #2)
from .concept_tracker import ConceptTracker

logger = logging.getLogger(__name__)

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
    # NEW: Concept tracking fields (Quick Win #2)
    concept_tags: Dict[int, str] = field(default_factory=dict)  # cluster_id → concept_id
    
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
            'noise_count': int(np.sum(self.labels == -1)) if self.labels is not None else 0,
            'concept_tags': self.concept_tags  # NEW: semantic concept names
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
    
    def extract_features(self, organisms: Dict[str, Any], 
                        context_memory: Optional[Any] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Extract feature vectors from organisms.
        
        Features include:
        - Phenotype traits (trait_0 through trait_9)
        - Fitness value
        - Resources (if available)
        - Connection count (if available)
        - Language features (if context_memory available):
          - Vocabulary size (normalized)
          - Communication activity (normalized)
          - Linguistic connections (normalized)
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
            
            # NEW: Language features (if context_memory available)
            if context_memory and hasattr(context_memory, 'node_word_associations'):
                # Convert org_id to int for lookup
                org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
                
                # Vocabulary size (normalized to 0-1, assuming max 100 words)
                vocab_size = len(context_memory.node_word_associations.get(org_id_int, set()))
                feature_vec.append(min(1.0, vocab_size / 100.0))
                
                # Communication activity (normalized, assuming max 50 communications)
                comm_activity = getattr(org, 'communication_count', 0)
                feature_vec.append(min(1.0, comm_activity / 50.0))
                
                # Linguistic connections (normalized, assuming max 10 linguistic edges)
                linguistic_conns = getattr(org, 'linguistic_connection_count', 0)
                feature_vec.append(min(1.0, linguistic_conns / 10.0))
            else:
                # No language data available - use zeros
                feature_vec.extend([0.0] * 3)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_predict(self, organisms: Dict[str, Any],
                    context_memory: Optional[Any] = None) -> ClusteringResult:
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
        
        features, organism_ids = self.extract_features(organisms, context_memory=context_memory)
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Track which algorithm is actually used (separate from config setting)
        used_algorithm = self.algorithm
        
        # Select and run clustering algorithm
        if self.algorithm == 'hdbscan' and HDBSCAN_AVAILABLE:
            clusterer = HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples
            )
            labels = clusterer.fit_predict(features_scaled)
            centroids = None
            used_algorithm = 'hdbscan'
        elif self.algorithm == 'kmeans':
            n_clusters = min(self.n_clusters, len(organisms))
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = clusterer.fit_predict(features_scaled)
            centroids = clusterer.cluster_centers_
            used_algorithm = 'kmeans'
        elif self.algorithm == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=self.min_samples)
            labels = clusterer.fit_predict(features_scaled)
            centroids = None
            used_algorithm = 'dbscan'
        else:
            # Fallback to KMeans if HDBSCAN not available or unknown algorithm
            n_clusters = min(self.n_clusters, len(organisms))
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = clusterer.fit_predict(features_scaled)
            centroids = clusterer.cluster_centers_
            used_algorithm = 'kmeans_fallback'
        
        # Calculate cluster sizes
        unique_labels = set(labels)
        cluster_sizes = {int(label): int(np.sum(labels == label)) for label in unique_labels}
        n_clusters = len([l for l in unique_labels if l >= 0])  # Exclude noise (-1)
        
        self._last_result = ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            cluster_sizes=cluster_sizes,
            cluster_centroids=centroids,
            algorithm=used_algorithm  # Report actual algorithm used, not config setting
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
    
    def extract_features(self, organisms: Dict[str, Any],
                        context_memory: Optional[Any] = None) -> Tuple[np.ndarray, List[str]]:
        """Extract feature vectors from organisms (same as clustering, with language features)"""
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
            
            # NEW: Language features (if context_memory available)
            if context_memory and hasattr(context_memory, 'node_word_associations'):
                org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
                vocab_size = len(context_memory.node_word_associations.get(org_id_int, set()))
                feature_vec.append(min(1.0, vocab_size / 100.0))
                comm_activity = getattr(org, 'communication_count', 0)
                feature_vec.append(min(1.0, comm_activity / 50.0))
                linguistic_conns = getattr(org, 'linguistic_connection_count', 0)
                feature_vec.append(min(1.0, linguistic_conns / 10.0))
            else:
                feature_vec.extend([0.0] * 3)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_predict(self, organisms: Dict[str, Any], context_memory: Optional[Any] = None) -> AnomalyResult:
        """
        Detect anomalies in organism population.
        
        Args:
            organisms: Dict mapping organism IDs to Organism objects
            context_memory: Optional ContextMemory instance for language features
        
        Returns:
            AnomalyResult with detected anomalies
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
        
        features, organism_ids = self.extract_features(organisms, context_memory=context_memory)
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
    
    def extract_features(self, organisms: Dict[str, Any],
                        context_memory: Optional[Any] = None) -> Tuple[np.ndarray, List[str]]:
        """Extract feature vectors from organisms (with language features)"""
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
            
            # NEW: Language features (if context_memory available)
            if context_memory and hasattr(context_memory, 'node_word_associations'):
                org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
                vocab_size = len(context_memory.node_word_associations.get(org_id_int, set()))
                feature_vec.append(min(1.0, vocab_size / 100.0))
                comm_activity = getattr(org, 'communication_count', 0)
                feature_vec.append(min(1.0, comm_activity / 50.0))
                linguistic_conns = getattr(org, 'linguistic_connection_count', 0)
                feature_vec.append(min(1.0, linguistic_conns / 10.0))
            else:
                feature_vec.extend([0.0] * 3)
            
            features.append(feature_vec)
        
        return np.array(features), organism_ids
    
    def fit_transform(self, organisms: Dict[str, Any], context_memory: Optional[Any] = None) -> ReductionResult:
        """
        Reduce dimensionality of organism features.
        
        Args:
            organisms: Dict mapping organism IDs to Organism objects
            context_memory: Optional ContextMemory instance for language features
        
        Returns:
            ReductionResult with reduced coordinates
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
        
        features, organism_ids = self.extract_features(organisms, context_memory=context_memory)
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
    
    Includes ConceptTracker for semantic naming of stable behavioral clusters (Quick Win #2).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ML analyzer with configuration.
        
        Config structure expected:
        {
            "enabled": true/false,
            "clustering": {"enabled": true, "algorithm": "hdbscan", ...},
            "anomaly_detection": {"enabled": true, "algorithm": "isolation_forest", ...},
            "dimensionality_reduction": {"enabled": true, "algorithm": "pca", ...},
            "concept_tracking": {"enabled": true, "persistence_threshold": 3, ...}
        }
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        
        # Initialize subsystems
        clustering_config = self.config.get('clustering', {})
        anomaly_config = self.config.get('anomaly_detection', {})
        reduction_config = self.config.get('dimensionality_reduction', {})
        concept_config = self.config.get('concept_tracking', {})
        
        self.clusterer = PopulationClusterer(clustering_config)
        self.anomaly_detector = AnomalyDetector(anomaly_config)
        self.reducer = TraitReducer(reduction_config)
        
        # NEW: Concept tracking for semantic naming (Quick Win #2)
        self.concept_tracker = ConceptTracker(
            persistence_threshold=concept_config.get('persistence_threshold', 3),
            stale_threshold=concept_config.get('stale_threshold', 10.0),
            enabled=concept_config.get('enabled', True)
        )
        
        # Feature toggles
        self.clustering_enabled = clustering_config.get('enabled', True)
        self.anomaly_enabled = anomaly_config.get('enabled', True)
        self.reduction_enabled = reduction_config.get('enabled', True)
        self.concept_tracking_enabled = concept_config.get('enabled', True)
        
        # Last analysis results
        self._last_analysis: Dict[str, Any] = {}
        self._last_analysis_time: float = 0
        self._analysis_interval: float = 5.0  # Minimum seconds between analyses

        # Optional event emitter for causation graph visualization
        self.event_emitter = None  # Set by main.py or unified_entry.py
    
    def update_config(self, config: Dict[str, Any]):
        """Update configuration dynamically (for hot reload)"""
        self.config = config
        self.enabled = config.get('enabled', False)
        
        # Update subsystem configs
        clustering_config = config.get('clustering', {})
        anomaly_config = config.get('anomaly_detection', {})
        reduction_config = config.get('dimensionality_reduction', {})
        concept_config = config.get('concept_tracking', {})
        
        self.clusterer = PopulationClusterer(clustering_config)
        self.anomaly_detector = AnomalyDetector(anomaly_config)
        self.reducer = TraitReducer(reduction_config)
        
        # Update concept tracker settings (preserve history, just update config)
        self.concept_tracker.enabled = concept_config.get('enabled', True)
        self.concept_tracker.persistence_threshold = concept_config.get('persistence_threshold', 3)
        self.concept_tracker.stale_threshold = concept_config.get('stale_threshold', 10.0)
        
        self.clustering_enabled = clustering_config.get('enabled', True)
        self.anomaly_enabled = anomaly_config.get('enabled', True)
        self.reduction_enabled = reduction_config.get('enabled', True)
        self.concept_tracking_enabled = concept_config.get('enabled', True)
    
    def analyze(self, organisms: Dict[str, Any], force: bool = False, context_memory: Optional[Any] = None) -> Dict[str, Any]:
        """
        Run all enabled ML analyses on organism population.
        
        Args:
            organisms: Dict mapping organism IDs to Organism objects
            force: If True, run analysis regardless of interval
            context_memory: Optional ContextMemory instance for language features
            
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
                'reduction': None,
                'concept_tracking': None
            }
        
        results = {
            'enabled': True,
            'sklearn_available': True,
            'timestamp': current_time,
            'organism_count': len(organisms)
        }
        
        # Clustering
        cluster_result = None
        if self.clustering_enabled:
            cluster_result = self.clusterer.fit_predict(organisms, context_memory=context_memory)
            
            # NEW: Concept tracking - semantic naming of stable clusters (Quick Win #2)
            concept_tags = {}
            if self.concept_tracking_enabled and cluster_result.labels.size > 0:
                # Wire event emitter to concept tracker for causation graph events
                if self.event_emitter:
                    self.concept_tracker.event_emitter = self.event_emitter
                
                # Update concept tracking with clustering results
                concept_tags = self.concept_tracker.update(
                    cluster_labels=cluster_result.labels,
                    cluster_sizes=cluster_result.cluster_sizes,
                    organisms=organisms,
                    timestamp=current_time
                )
                
                # Attach concept tags to cluster result
                cluster_result.concept_tags = concept_tags
            
            results['clustering'] = cluster_result.to_dict()
            results['cluster_labels'] = cluster_result.labels.tolist() if cluster_result.labels.size > 0 else []
            results['concept_tags'] = concept_tags
            results['concept_summary'] = self.concept_tracker.get_concept_summary() if self.concept_tracking_enabled else None
        else:
            results['clustering'] = None
            results['concept_tags'] = {}
            results['concept_summary'] = None
        
        # Anomaly Detection
        if self.anomaly_enabled:
            anomaly_result = self.anomaly_detector.fit_predict(organisms, context_memory=context_memory)
            results['anomalies'] = anomaly_result.to_dict()
            results['anomaly_organisms'] = anomaly_result.get_anomaly_organisms(list(organisms.keys()))
        else:
            results['anomalies'] = None
        
        # Dimensionality Reduction
        if self.reduction_enabled:
            reduction_result = self.reducer.fit_transform(organisms, context_memory=context_memory)
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
            'concept_tracking_enabled': self.concept_tracking_enabled,
            'last_analysis_time': self._last_analysis_time,
            'clusterer_algorithm': self.clusterer.algorithm,
            'anomaly_algorithm': self.anomaly_detector.algorithm,
            'reducer_algorithm': self.reducer.algorithm,
            'active_concepts': len(self.concept_tracker.get_active_concepts()) if self.concept_tracking_enabled else 0
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
