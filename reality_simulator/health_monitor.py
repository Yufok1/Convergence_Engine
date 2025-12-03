"""
HealthMonitor - Unified Ecosystem Health Scoring

Quick Win #5: Provides a single health metric (0.0-1.0) that aggregates
multiple ecosystem health dimensions into one unified optimization target.

Health Formula:
    health = (
        0.30 * coherence_score +      # Network connectivity & cooperation
        0.20 * diversity_score +       # Behavioral variety (cluster count)
        0.20 * adaptability_score +    # Learning progress (epsilon decay, losses)
        0.20 * lawfulness_score +      # 1.0 - violation_pressure
        0.10 * sustainability_score    # Resource balance & population stability
    )

This unified metric prevents gaming individual metrics and provides
organisms with a single signal representing ecosystem wellness.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthSnapshot:
    """A point-in-time health assessment"""
    timestamp: float
    health_score: float  # Unified score 0.0-1.0
    
    # Component scores (all 0.0-1.0)
    coherence_score: float = 0.5
    diversity_score: float = 0.5
    adaptability_score: float = 0.5
    lawfulness_score: float = 0.5
    sustainability_score: float = 0.5
    
    # Raw inputs used for calculation
    raw_inputs: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'timestamp': self.timestamp,
            'health_score': self.health_score,
            'components': {
                'coherence': self.coherence_score,
                'diversity': self.diversity_score,
                'adaptability': self.adaptability_score,
                'lawfulness': self.lawfulness_score,
                'sustainability': self.sustainability_score
            },
            'raw_inputs': self.raw_inputs
        }


class HealthMonitor:
    """
    Computes unified ecosystem health from multiple data sources.
    
    Aggregates signals from:
    - Network metrics (coherence, connectivity)
    - ML clustering results (diversity)
    - Neural training stats (adaptability/learning)
    - Violation pressure (lawfulness)
    - Resource/population data (sustainability)
    
    Emits health_change events when health crosses thresholds.
    """
    
    # Health thresholds for event emission
    CRITICAL_THRESHOLD = 0.3
    WARNING_THRESHOLD = 0.5
    HEALTHY_THRESHOLD = 0.7
    
    # Component weights (must sum to 1.0)
    WEIGHT_COHERENCE = 0.30
    WEIGHT_DIVERSITY = 0.20
    WEIGHT_ADAPTABILITY = 0.20
    WEIGHT_LAWFULNESS = 0.20
    WEIGHT_SUSTAINABILITY = 0.10
    
    def __init__(self,
                 enabled: bool = True,
                 history_size: int = 100,
                 event_emitter: Optional[Callable] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize health monitor.
        
        Args:
            enabled: Whether health monitoring is active
            history_size: Number of health snapshots to retain
            event_emitter: Callback for emitting health events
            config: Optional config overrides
        """
        self.enabled = enabled
        self.history_size = history_size
        self.event_emitter = event_emitter
        
        # Load config overrides
        if config:
            self.WEIGHT_COHERENCE = config.get('weight_coherence', self.WEIGHT_COHERENCE)
            self.WEIGHT_DIVERSITY = config.get('weight_diversity', self.WEIGHT_DIVERSITY)
            self.WEIGHT_ADAPTABILITY = config.get('weight_adaptability', self.WEIGHT_ADAPTABILITY)
            self.WEIGHT_LAWFULNESS = config.get('weight_lawfulness', self.WEIGHT_LAWFULNESS)
            self.WEIGHT_SUSTAINABILITY = config.get('weight_sustainability', self.WEIGHT_SUSTAINABILITY)
            self.CRITICAL_THRESHOLD = config.get('critical_threshold', self.CRITICAL_THRESHOLD)
            self.WARNING_THRESHOLD = config.get('warning_threshold', self.WARNING_THRESHOLD)
            self.HEALTHY_THRESHOLD = config.get('healthy_threshold', self.HEALTHY_THRESHOLD)
        
        # State
        self.health_history: List[HealthSnapshot] = []
        self.current_health: float = 0.5  # Start neutral
        self.last_state: str = "unknown"  # "critical", "warning", "healthy", "optimal"
        
        # Smoothing for adaptability (track trends)
        self._epsilon_history: List[float] = []
        self._loss_history: List[float] = []
        
        logger.info(f"[HEALTH] HealthMonitor initialized (enabled={enabled})")
    
    def compute_health(self,
                       network_metrics: Optional[Dict[str, float]] = None,
                       clustering_result: Optional[Any] = None,
                       neural_stats: Optional[Dict[str, float]] = None,
                       vp_components: Optional[Dict[str, float]] = None,
                       resource_data: Optional[Dict[str, float]] = None) -> HealthSnapshot:
        """
        Compute unified health score from all available data sources.
        
        Args:
            network_metrics: From EcosystemMetrics (connectivity, clustering_coefficient, etc.)
            clustering_result: From MLAnalyzer (n_clusters, cluster_sizes)
            neural_stats: From NeuralTrainer (avg_epsilon, avg_loss, training_steps)
            vp_components: VP breakdown (trait_divergence, network_coherence, etc.)
            resource_data: Resource pool and population stats
            
        Returns:
            HealthSnapshot with unified score and component breakdown
        """
        if not self.enabled:
            return HealthSnapshot(
                timestamp=time.time(),
                health_score=0.5,
                raw_inputs={}
            )
        
        raw_inputs = {}
        
        # === COHERENCE (30%) ===
        # Based on network connectivity and cooperation metrics
        coherence_score = self._compute_coherence(network_metrics, vp_components, raw_inputs)
        
        # === DIVERSITY (20%) ===
        # Based on behavioral variety from clustering
        diversity_score = self._compute_diversity(clustering_result, network_metrics, raw_inputs)
        
        # === ADAPTABILITY (20%) ===
        # Based on learning progress (epsilon decay, loss reduction)
        adaptability_score = self._compute_adaptability(neural_stats, raw_inputs)
        
        # === LAWFULNESS (20%) ===
        # Inverse of violation pressure - how well system follows its own rules
        lawfulness_score = self._compute_lawfulness(vp_components, raw_inputs)
        
        # === SUSTAINABILITY (10%) ===
        # Resource balance and population stability
        sustainability_score = self._compute_sustainability(resource_data, raw_inputs)
        
        # Weighted combination
        health_score = (
            self.WEIGHT_COHERENCE * coherence_score +
            self.WEIGHT_DIVERSITY * diversity_score +
            self.WEIGHT_ADAPTABILITY * adaptability_score +
            self.WEIGHT_LAWFULNESS * lawfulness_score +
            self.WEIGHT_SUSTAINABILITY * sustainability_score
        )
        
        # Clamp to [0, 1]
        health_score = float(np.clip(health_score, 0.0, 1.0))
        
        snapshot = HealthSnapshot(
            timestamp=time.time(),
            health_score=health_score,
            coherence_score=coherence_score,
            diversity_score=diversity_score,
            adaptability_score=adaptability_score,
            lawfulness_score=lawfulness_score,
            sustainability_score=sustainability_score,
            raw_inputs=raw_inputs
        )
        
        # Update state
        self.current_health = health_score
        self._update_history(snapshot)
        self._check_state_transitions(snapshot)
        
        # Log periodic health status (every 10 snapshots)
        if len(self.health_history) % 10 == 0:
            logger.info(f"[HEALTH] Computed: {health_score:.3f} (coh={coherence_score:.2f}, div={diversity_score:.2f}, adapt={adaptability_score:.2f}, law={lawfulness_score:.2f}, sust={sustainability_score:.2f})")
        
        return snapshot
    
    def _compute_coherence(self,
                           network_metrics: Optional[Dict[str, float]],
                           vp_components: Optional[Dict[str, float]],
                           raw_inputs: Dict) -> float:
        """
        Compute coherence score from network connectivity metrics.
        
        High coherence = organisms are well-connected and cooperating.
        """
        if not network_metrics:
            network_metrics = {}
        if not vp_components:
            vp_components = {}
        
        # Factors contributing to coherence
        connectivity = network_metrics.get('connectivity', 0.0)
        clustering_coeff = network_metrics.get('clustering_coefficient', 0.0)
        modularity = network_metrics.get('modularity', 0.0)
        
        # VP's network_coherence is actually a violation signal (high = bad)
        # So we invert it: coherence_from_vp = 1.0 - network_coherence_vp
        vp_net_coherence = vp_components.get('network_coherence', 0.0)
        coherence_from_vp = 1.0 - float(np.clip(vp_net_coherence, 0.0, 1.0))
        
        raw_inputs['coherence_connectivity'] = connectivity
        raw_inputs['coherence_clustering'] = clustering_coeff
        raw_inputs['coherence_vp_inverse'] = coherence_from_vp
        
        # Normalize connectivity (assume max ~10 connections is excellent)
        connectivity_normalized = min(connectivity / 10.0, 1.0)
        
        # Combine factors
        coherence = (
            0.3 * connectivity_normalized +
            0.3 * clustering_coeff +
            0.2 * modularity +
            0.2 * coherence_from_vp
        )
        
        return float(np.clip(coherence, 0.0, 1.0))
    
    def _compute_diversity(self,
                           clustering_result: Optional[Any],
                           network_metrics: Optional[Dict[str, float]],
                           raw_inputs: Dict) -> float:
        """
        Compute diversity score from behavioral variety.
        
        High diversity = multiple distinct behavioral phenotypes exist.
        """
        if not network_metrics:
            network_metrics = {}
        
        # From clustering: number of distinct clusters
        n_clusters = 0
        cluster_balance = 0.5  # How evenly distributed organisms are
        
        if clustering_result is not None:
            if hasattr(clustering_result, 'n_clusters'):
                n_clusters = clustering_result.n_clusters
            if hasattr(clustering_result, 'cluster_sizes') and clustering_result.cluster_sizes:
                sizes = list(clustering_result.cluster_sizes.values())
                if len(sizes) > 1 and sum(sizes) > 0:
                    # Balance = 1 - normalized std (more even = higher balance)
                    std = np.std(sizes)
                    mean = np.mean(sizes)
                    if mean > 0:
                        cluster_balance = 1.0 - min(std / mean, 1.0)
        
        # Species diversity from ecosystem metrics
        species_diversity = network_metrics.get('species_diversity', 0.0)
        
        raw_inputs['diversity_n_clusters'] = n_clusters
        raw_inputs['diversity_cluster_balance'] = cluster_balance
        raw_inputs['diversity_species'] = species_diversity
        
        # Normalize cluster count (2-8 clusters is healthy)
        cluster_score = 0.0
        if n_clusters >= 2:
            if n_clusters <= 8:
                cluster_score = n_clusters / 8.0
            else:
                # Too many clusters can indicate fragmentation
                cluster_score = max(0.5, 1.0 - (n_clusters - 8) / 16.0)
        
        diversity = (
            0.4 * cluster_score +
            0.3 * cluster_balance +
            0.3 * min(species_diversity, 1.0)
        )
        
        return float(np.clip(diversity, 0.0, 1.0))
    
    def _compute_adaptability(self,
                              neural_stats: Optional[Dict[str, float]],
                              raw_inputs: Dict) -> float:
        """
        Compute adaptability score from learning progress.
        
        High adaptability = system is learning and improving.
        """
        if not neural_stats:
            neural_stats = {}
        
        # Epsilon decay indicates learning is happening
        avg_epsilon = neural_stats.get('avg_epsilon', 1.0)
        avg_loss = neural_stats.get('avg_loss', 1.0)
        training_steps = neural_stats.get('training_steps', 0)
        
        raw_inputs['adaptability_epsilon'] = avg_epsilon
        raw_inputs['adaptability_loss'] = avg_loss
        raw_inputs['adaptability_steps'] = training_steps
        
        # Track trends for better scoring
        self._epsilon_history.append(avg_epsilon)
        self._loss_history.append(avg_loss)
        if len(self._epsilon_history) > 20:
            self._epsilon_history = self._epsilon_history[-20:]
        if len(self._loss_history) > 20:
            self._loss_history = self._loss_history[-20:]
        
        # Epsilon decay progress (1.0 → 0.01 is full learning)
        # Low epsilon = more exploitation = more learned
        epsilon_score = 1.0 - avg_epsilon
        
        # Loss reduction (lower is better, but cap at reasonable range)
        loss_normalized = min(avg_loss, 1.0)
        loss_score = 1.0 - loss_normalized
        
        # Training activity (has training happened?)
        activity_score = min(training_steps / 1000.0, 1.0) if training_steps > 0 else 0.3
        
        # Trend bonus: is epsilon decreasing over time?
        trend_bonus = 0.0
        if len(self._epsilon_history) >= 5:
            recent_avg = np.mean(self._epsilon_history[-5:])
            older_avg = np.mean(self._epsilon_history[:5])
            if older_avg > recent_avg:
                trend_bonus = 0.1  # Learning is progressing
        
        adaptability = (
            0.4 * epsilon_score +
            0.3 * loss_score +
            0.2 * activity_score +
            0.1 * trend_bonus
        )
        
        return float(np.clip(adaptability, 0.0, 1.0))
    
    def _compute_lawfulness(self,
                            vp_components: Optional[Dict[str, float]],
                            raw_inputs: Dict) -> float:
        """
        Compute lawfulness score from violation pressure.
        
        High lawfulness = system follows its internal rules well.
        """
        if not vp_components:
            vp_components = {}
        
        # Get individual VP components
        trait_divergence = vp_components.get('trait_divergence', 0.0)
        network_coherence = vp_components.get('network_coherence', 0.0)
        quantum_entropy = vp_components.get('quantum_entropy', 0.0)
        evolution_pressure = vp_components.get('evolution_pressure', 0.0)
        phase_mismatch = vp_components.get('phase_mismatch', 0.0)
        
        raw_inputs['lawfulness_trait_div'] = trait_divergence
        raw_inputs['lawfulness_net_coh'] = network_coherence
        raw_inputs['lawfulness_q_entropy'] = quantum_entropy
        raw_inputs['lawfulness_evo_pressure'] = evolution_pressure
        raw_inputs['lawfulness_phase_mismatch'] = phase_mismatch
        
        # Total VP (average of components, each in [0,1])
        total_vp = (
            trait_divergence +
            network_coherence +
            quantum_entropy +
            evolution_pressure +
            phase_mismatch
        ) / 5.0
        
        raw_inputs['lawfulness_total_vp'] = total_vp
        
        # Lawfulness is inverse of VP
        lawfulness = 1.0 - float(np.clip(total_vp, 0.0, 1.0))
        
        return lawfulness
    
    def _compute_sustainability(self,
                                resource_data: Optional[Dict[str, float]],
                                raw_inputs: Dict) -> float:
        """
        Compute sustainability score from resource balance.
        
        High sustainability = resources are balanced, population is stable.
        """
        if not resource_data:
            resource_data = {}
        
        # Resource pool health
        resource_pool = resource_data.get('resource_pool', 100.0)
        initial_resources = resource_data.get('initial_resources', 200.0)
        
        # Population stability
        population = resource_data.get('population', 50)
        target_population = resource_data.get('target_population', 100)
        
        raw_inputs['sustainability_resources'] = resource_pool
        raw_inputs['sustainability_population'] = population
        
        # Resource ratio (how much of initial resources remain)
        resource_ratio = resource_pool / max(initial_resources, 1.0)
        resource_score = float(np.clip(resource_ratio, 0.0, 1.0))
        
        # Population health (closeness to target)
        if target_population > 0:
            pop_ratio = population / target_population
            # Best score when population is at target
            if pop_ratio <= 1.0:
                pop_score = pop_ratio
            else:
                # Overpopulation penalty
                pop_score = max(0.0, 2.0 - pop_ratio)
        else:
            pop_score = 0.5 if population > 0 else 0.0
        
        raw_inputs['sustainability_resource_score'] = resource_score
        raw_inputs['sustainability_pop_score'] = pop_score
        
        sustainability = 0.5 * resource_score + 0.5 * pop_score
        
        return float(np.clip(sustainability, 0.0, 1.0))
    
    def _update_history(self, snapshot: HealthSnapshot):
        """Add snapshot to history, pruning old entries"""
        self.health_history.append(snapshot)
        if len(self.health_history) > self.history_size:
            self.health_history = self.health_history[-self.history_size:]
    
    def _check_state_transitions(self, snapshot: HealthSnapshot):
        """Check for health state changes and emit events"""
        health = snapshot.health_score
        
        # Determine current state
        if health < self.CRITICAL_THRESHOLD:
            new_state = "critical"
        elif health < self.WARNING_THRESHOLD:
            new_state = "warning"
        elif health < self.HEALTHY_THRESHOLD:
            new_state = "healthy"
        else:
            new_state = "optimal"
        
        # Emit event on state change
        if new_state != self.last_state and self.event_emitter:
            try:
                self.event_emitter({
                    'component': 'health_monitor',
                    'event_type': 'health_state_change',
                    'data': {
                        'previous_state': self.last_state,
                        'new_state': new_state,
                        'health_score': health,
                        'components': {
                            'coherence': snapshot.coherence_score,
                            'diversity': snapshot.diversity_score,
                            'adaptability': snapshot.adaptability_score,
                            'lawfulness': snapshot.lawfulness_score,
                            'sustainability': snapshot.sustainability_score
                        }
                    }
                })
                logger.info(f"[HEALTH] State change: {self.last_state} → {new_state} (health={health:.3f})")
            except Exception as e:
                logger.warning(f"[HEALTH] Failed to emit health event: {e}")
        
        self.last_state = new_state
    
    def get_current_health(self) -> float:
        """Get the most recent health score"""
        return self.current_health
    
    def get_health_trend(self, window: int = 10) -> str:
        """
        Get health trend over recent history.
        
        Returns: "improving", "stable", or "declining"
        """
        if len(self.health_history) < 2:
            return "stable"
        
        recent = self.health_history[-min(window, len(self.health_history)):]
        scores = [s.health_score for s in recent]
        
        if len(scores) < 2:
            return "stable"
        
        # Simple linear trend
        first_half = np.mean(scores[:len(scores)//2])
        second_half = np.mean(scores[len(scores)//2:])
        
        diff = second_half - first_half
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"
    
    def get_weakest_component(self) -> Tuple[str, float]:
        """Get the health component with lowest score"""
        if not self.health_history:
            return ("unknown", 0.5)
        
        latest = self.health_history[-1]
        components = {
            'coherence': latest.coherence_score,
            'diversity': latest.diversity_score,
            'adaptability': latest.adaptability_score,
            'lawfulness': latest.lawfulness_score,
            'sustainability': latest.sustainability_score
        }
        
        weakest = min(components.items(), key=lambda x: x[1])
        return weakest
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of health monitor state"""
        trend = self.get_health_trend()
        weakest_name, weakest_score = self.get_weakest_component()
        
        return {
            'enabled': self.enabled,
            'current_health': self.current_health,
            'state': self.last_state,
            'trend': trend,
            'weakest_component': weakest_name,
            'weakest_score': weakest_score,
            'history_length': len(self.health_history)
        }
    
    def reset(self):
        """Reset monitor state"""
        self.health_history.clear()
        self.current_health = 0.5
        self.last_state = "unknown"
        self._epsilon_history.clear()
        self._loss_history.clear()
        logger.info("[HEALTH] HealthMonitor reset")


# Module-level singleton pattern (optional)
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(config: Optional[Dict[str, Any]] = None,
                       event_emitter: Optional[Callable] = None) -> HealthMonitor:
    """Get or create the global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        health_config = {}
        if config:
            health_config = config.get('health_monitor', {})
        _health_monitor = HealthMonitor(
            enabled=health_config.get('enabled', True),
            history_size=health_config.get('history_size', 100),
            event_emitter=event_emitter,
            config=health_config
        )
    return _health_monitor


def reset_health_monitor():
    """Reset the global health monitor"""
    global _health_monitor
    if _health_monitor:
        _health_monitor.reset()
    _health_monitor = None
