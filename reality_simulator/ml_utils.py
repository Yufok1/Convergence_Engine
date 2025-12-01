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
    from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors, KNeighborsClassifier
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.feature_selection import SelectKBest, mutual_info_classif, f_classif
    from sklearn.metrics import (
        silhouette_score, adjusted_rand_score, mutual_info_score,
        accuracy_score, precision_score, recall_score
    )
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
        # Integration 1: Neural-ML Symbiosis - use neural embeddings for clustering
        self.use_neural_embeddings = self.config.get('use_neural_embeddings', False)
    
    def extract_features(self, organisms: Dict[str, Any], 
                        context_memory: Optional[Any] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Extract feature vectors from organisms.
        
        Integration 1: Neural-ML Symbiosis - can use neural embeddings instead of behavioral features.
        
        Features include (if use_neural_embeddings=False):
        - Phenotype traits (trait_0 through trait_9)
        - Fitness value
        - Resources (if available)
        - Connection count (if available)
        - Language features (if context_memory available):
          - Vocabulary size (normalized)
          - Communication activity (normalized)
          - Linguistic connections (normalized)
        
        If use_neural_embeddings=True and organism is NeuralOrganism:
        - 64-dim semantic embedding from fc2 hidden state
        """
        organism_ids = list(organisms.keys())
        features = []
        
        for org_id in organism_ids:
            org = organisms[org_id]
            
            # Integration 1: Try neural embedding first if enabled
            if self.use_neural_embeddings:
                # Check if organism is NeuralOrganism and has embedding method
                if hasattr(org, 'get_language_embedding'):
                    embedding = org.get_language_embedding(context_memory)
                    if embedding is not None and len(embedding) > 0:
                        # Use neural embedding (64-dim)
                        features.append(embedding)
                        continue
            
            # Fallback to behavioral features (original implementation)
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
        
        # NEW: Language analysis configuration
        language_config = self.config.get('language_analysis', {})
        self.language_analysis_enabled = language_config.get('enabled', True)
        self.tfidf_enabled = language_config.get('tfidf', {}).get('enabled', True)
        self.nearest_neighbors_enabled = language_config.get('nearest_neighbors', {}).get('enabled', True)
        self.feature_selection_enabled = language_config.get('feature_selection', {}).get('enabled', False)
        self.metrics_enabled = language_config.get('metrics', {}).get('enabled', True)
        
        # Initialize language analysis components
        if SKLEARN_AVAILABLE and self.language_analysis_enabled:
            # TF-IDF vectorizer for vocabulary analysis
            if self.tfidf_enabled:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=language_config.get('tfidf', {}).get('max_features', 1000),
                    ngram_range=tuple(language_config.get('tfidf', {}).get('ngram_range', [1, 2])),
                    min_df=language_config.get('tfidf', {}).get('min_df', 1),
                    max_df=language_config.get('tfidf', {}).get('max_df', 0.95)
                )
                self.count_vectorizer = CountVectorizer(
                    max_features=language_config.get('tfidf', {}).get('max_features', 1000),
                    ngram_range=tuple(language_config.get('tfidf', {}).get('ngram_range', [1, 2]))
                )
            else:
                self.tfidf_vectorizer = None
                self.count_vectorizer = None
            
            # Nearest Neighbors for semantic similarity
            if self.nearest_neighbors_enabled:
                nn_config = language_config.get('nearest_neighbors', {})
                self.nearest_neighbors = NearestNeighbors(
                    n_neighbors=nn_config.get('n_neighbors', 5),
                    metric=nn_config.get('metric', 'cosine'),
                    algorithm=nn_config.get('algorithm', 'auto')
                )
            else:
                self.nearest_neighbors = None
            
            # Feature selection
            if self.feature_selection_enabled:
                fs_config = language_config.get('feature_selection', {})
                self.feature_selector = SelectKBest(
                    score_func=mutual_info_classif if fs_config.get('method', 'mutual_info') == 'mutual_info' else f_classif,
                    k=fs_config.get('k', 10)
                )
            else:
                self.feature_selector = None
        else:
            self.tfidf_vectorizer = None
            self.count_vectorizer = None
            self.nearest_neighbors = None
            self.feature_selector = None
        
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
        
        # NEW: Semantic Analysis - Analyze language patterns, word co-occurrence, semantic clusters
        if context_memory and hasattr(context_memory, 'node_word_associations'):
            semantic_analysis = self._analyze_semantic_patterns(organisms, context_memory)
            results['semantic_analysis'] = semantic_analysis
        else:
            results['semantic_analysis'] = None
        
        self._last_analysis = results
        self._last_analysis_time = current_time
        
        return results
    
    def _analyze_semantic_patterns(self, organisms: Dict[str, Any], context_memory: Any) -> Dict[str, Any]:
        """
        Analyze semantic patterns: word co-occurrence, semantic clusters, concept formation.
        
        Enhanced with TF-IDF, Nearest Neighbors, and quality metrics.
        """
        if not context_memory or not hasattr(context_memory, 'node_word_associations'):
            return None
        
        # Get Linguistic Knowledge Web if available
        knowledge_web = None
        if hasattr(context_memory, 'knowledge_web'):
            knowledge_web = context_memory.knowledge_web
        elif hasattr(context_memory, 'language_teacher') and hasattr(context_memory.language_teacher, 'knowledge_web'):
            knowledge_web = context_memory.language_teacher.knowledge_web
        
        if not knowledge_web:
            return None
        
        # Build word-organism matrix and vocabulary strings for TF-IDF
        organism_ids = list(organisms.keys())
        word_organism_matrix = {}  # word -> set of organism_ids
        organism_vocabularies = []  # List of space-separated word strings for each organism
        
        for org_id in organism_ids:
            org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
            words = list(context_memory.node_word_associations.get(org_id_int, set()))
            organism_vocabularies.append(' '.join(words))
            
            for word in words:
                if word not in word_organism_matrix:
                    word_organism_matrix[word] = set()
                word_organism_matrix[word].add(org_id)
        
        # NEW: TF-IDF Analysis (if enabled and sklearn available)
        tfidf_results = None
        important_words = []
        if SKLEARN_AVAILABLE and self.tfidf_enabled and self.tfidf_vectorizer and len(organism_vocabularies) > 0:
            try:
                # Fit TF-IDF on organism vocabularies
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(organism_vocabularies)
                feature_names = self.tfidf_vectorizer.get_feature_names_out()
                
                # Get mean TF-IDF scores across all organisms (word importance)
                mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
                word_importance = list(zip(feature_names, mean_tfidf))
                word_importance.sort(key=lambda x: x[1], reverse=True)
                important_words = [{'word': word, 'tfidf_score': float(score)} for word, score in word_importance[:20]]
                
                # Count vectorizer for raw frequencies
                count_matrix = self.count_vectorizer.fit_transform(organism_vocabularies)
                total_counts = np.array(count_matrix.sum(axis=0)).flatten()
                count_feature_names = self.count_vectorizer.get_feature_names_out()
                word_counts = dict(zip(count_feature_names, total_counts))
                
                tfidf_results = {
                    'vocabulary_size': len(feature_names),
                    'top_important_words': important_words[:10],
                    'word_frequencies': {k: int(v) for k, v in list(word_counts.items())[:20]},
                    'ngram_range': self.tfidf_vectorizer.ngram_range
                }
            except Exception as e:
                logger.warning(f"[ML] TF-IDF analysis failed: {e}")
                tfidf_results = None
        
        # Analyze word co-occurrence (words that appear together) - keep basic version
        word_cooccurrence = {}
        for org_id in organism_ids:
            org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
            words = list(context_memory.node_word_associations.get(org_id_int, set()))
            # Count co-occurrences
            for i, word1 in enumerate(words):
                for word2 in words[i+1:]:
                    pair = tuple(sorted([word1, word2]))
                    word_cooccurrence[pair] = word_cooccurrence.get(pair, 0) + 1
        
        # NEW: Nearest Neighbors for semantic similarity (if enabled)
        similarity_results = None
        if SKLEARN_AVAILABLE and self.nearest_neighbors_enabled and self.nearest_neighbors and tfidf_results:
            try:
                # Use TF-IDF vectors for similarity search
                if 'tfidf_matrix' in locals() and tfidf_matrix.shape[0] > 1:
                    self.nearest_neighbors.fit(tfidf_matrix)
                    
                    # Find similar organisms for each organism
                    similar_organisms = {}
                    for i, org_id in enumerate(organism_ids[:min(10, len(organism_ids))]):  # Limit to first 10 for performance
                        distances, indices = self.nearest_neighbors.kneighbors(tfidf_matrix[i:i+1], return_distance=True)
                        similar_orgs = [
                            {
                                'organism_id': organism_ids[idx],
                                'similarity': float(1.0 - dist) if self.nearest_neighbors.metric == 'cosine' else float(1.0 / (1.0 + dist))
                            }
                            for dist, idx in zip(distances[0][1:], indices[0][1:])  # Skip self (first result)
                        ]
                        similar_organisms[org_id] = similar_orgs[:5]  # Top 5 similar
                    
                    similarity_results = {
                        'similarity_metric': self.nearest_neighbors.metric,
                        'n_neighbors': self.nearest_neighbors.n_neighbors,
                        'similar_organisms': similar_organisms
                    }
            except Exception as e:
                logger.warning(f"[ML] Nearest Neighbors analysis failed: {e}")
                similarity_results = None
        
        # Find semantic clusters (words with strong semantic relationships)
        semantic_clusters = []
        if knowledge_web:
            # Group words by semantic similarity
            processed_words = set()
            for word in word_organism_matrix.keys():
                if word in processed_words:
                    continue
                # Find semantically related words
                similar_words = knowledge_web.get_similar_words(word, min_strength=0.6)
                cluster_words = [w for w in similar_words if w in word_organism_matrix]
                if len(cluster_words) > 1:
                    semantic_clusters.append({
                        'words': cluster_words,
                        'size': len(cluster_words),
                        'organism_count': len(set.union(*[word_organism_matrix[w] for w in cluster_words]))
                    })
                    processed_words.update(cluster_words)
        
        # Analyze concept formation (words that form meaningful concepts)
        # ML system teaches and strengthens word formations through pattern recognition
        concept_formation = []
        top_cooccurrences = sorted(word_cooccurrence.items(), key=lambda x: x[1], reverse=True)[:20]
        for (word1, word2), count in top_cooccurrences:
            # Check if words have semantic relationship
            if knowledge_web:
                relations = knowledge_web.get_relations(word1)
                has_semantic_link = any(r.target == word2 or r.source == word2 for r in relations)
                if has_semantic_link:
                    # Get relationship strength to assess formation quality
                    relation_strength = 0.0
                    for r in relations:
                        if (r.target == word2 or r.source == word2) and hasattr(r, 'strength'):
                            relation_strength = max(relation_strength, r.strength)
                    
                    concept_formation.append({
                        'word1': word1,
                        'word2': word2,
                        'cooccurrence_count': count,
                        'semantic_relationship': True,
                        'relationship_strength': relation_strength,
                        'formation_quality': 'strong' if relation_strength >= 0.7 and count >= 3 else 'moderate'
                    })
                    
                    # STRENGTHEN FORMATIONS: If ML detects strong co-occurrence with semantic link,
                    # strengthen the relationship in knowledge web (ML teaching the system)
                    if count >= 5 and relation_strength >= 0.6:
                        # Find and strengthen the relationship
                        for r in relations:
                            if (r.target == word2 or r.source == word2) and hasattr(r, 'record_relationship_success'):
                                # ML detected pattern - strengthen it
                                knowledge_web.record_relationship_success(word1, word2, r.relation_type)
        
        # NEW: Feature Selection (if enabled)
        feature_importance = None
        if SKLEARN_AVAILABLE and self.feature_selection_enabled and self.feature_selector and tfidf_results:
            try:
                # Get organism fitness values for feature selection
                organism_fitnesses = []
                for org_id in organism_ids:
                    org = organisms.get(org_id)
                    fitness = getattr(org, 'fitness', 0.5) if org else 0.5
                    organism_fitnesses.append(fitness)
                
                if len(organism_fitnesses) > 5 and 'tfidf_matrix' in locals():
                    # Use TF-IDF features to predict fitness
                    # Convert fitness to binary classes (high/low) for classification
                    fitness_median = np.median(organism_fitnesses)
                    fitness_classes = np.array([1 if f > fitness_median else 0 for f in organism_fitnesses])
                    
                    # Fit feature selector
                    selected_features = self.feature_selector.fit_transform(tfidf_matrix, fitness_classes)
                    feature_scores = self.feature_selector.scores_
                    feature_names = self.tfidf_vectorizer.get_feature_names_out()
                    
                    # Get top important words (words that predict fitness)
                    word_importance = list(zip(feature_names, feature_scores))
                    word_importance.sort(key=lambda x: x[1], reverse=True)
                    important_words = [{'word': word, 'importance_score': float(score)} for word, score in word_importance[:20]]
                    
                    feature_importance = {
                        'top_predictive_words': important_words[:10],
                        'n_features_selected': int(selected_features.shape[1]),
                        'n_features_total': int(tfidf_matrix.shape[1])
                    }
            except Exception as e:
                logger.warning(f"[ML] Feature selection failed: {e}")
                feature_importance = None
        
        # NEW: Quality Metrics (if enabled and clustering results available)
        quality_metrics = None
        if SKLEARN_AVAILABLE and self.metrics_enabled and self._last_analysis:
            try:
                cluster_result = self._last_analysis.get('clustering')
                if cluster_result and 'labels' in cluster_result and cluster_result['labels']:
                    labels = np.array(cluster_result['labels'])
                    if len(labels) > 0 and len(set(labels)) > 1:
                        # Get features for silhouette score
                        features, _ = self.clusterer.extract_features(organisms, context_memory=context_memory)
                        if features.shape[0] == len(labels) and features.shape[0] > 1:
                            features_scaled = self.clusterer.scaler.fit_transform(features)
                            silhouette = silhouette_score(features_scaled, labels)
                            
                            quality_metrics = {
                                'silhouette_score': float(silhouette),
                                'n_clusters': int(len(set(labels))),
                                'n_samples': int(len(labels))
                            }
            except Exception as e:
                logger.warning(f"[ML] Quality metrics calculation failed: {e}")
                quality_metrics = None
        
        return {
            'word_organism_matrix_size': len(word_organism_matrix),
            'total_word_organism_links': sum(len(orgs) for orgs in word_organism_matrix.values()),
            'word_cooccurrence_pairs': len(word_cooccurrence),
            'top_cooccurrences': dict(top_cooccurrences[:10]),
            'semantic_clusters': semantic_clusters[:10],  # Top 10 clusters
            'concept_formation': concept_formation[:10],  # Top 10 concepts
            'tfidf_analysis': tfidf_results,  # NEW: TF-IDF results
            'similarity_analysis': similarity_results,  # NEW: Nearest Neighbors results
            'feature_importance': feature_importance,  # NEW: Feature selection results
            'quality_metrics': quality_metrics,  # NEW: Quality metrics
            'semantic_analysis_enabled': True,
            'ml_teaching': True  # ML is teaching/strengthening formations
        }
    
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
