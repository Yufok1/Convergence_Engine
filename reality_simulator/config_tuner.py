"""
ConfigTuner - Self-Tuning Configuration System

Interprets ML insights and neural metrics to autonomously adjust
configuration parameters for optimal system performance.

The butterfly learns to tune itself based on population-level patterns.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TuningAction:
    """A proposed configuration change with structured explanations (Quick Win #3)"""
    parameter_path: str  # e.g., "evolution.mutation_rate.initial"
    current_value: float
    proposed_value: float
    reason: str
    confidence: float  # 0-1, how confident we are this will help
    timestamp: float = field(default_factory=time.time)
    
    # NEW: Structured explanation fields (Quick Win #3)
    trigger_metrics: Dict[str, float] = field(default_factory=dict)  # What caused this action
    causation_event_id: Optional[str] = None  # Link to event that triggered this
    expected_impact: str = ""  # What we expect to happen
    actual_impact: Optional[str] = None  # What actually happened (filled later)


@dataclass
class TuningHistory:
    """Track the outcome of a tuning action"""
    action: TuningAction
    fitness_before: float
    fitness_after: Optional[float] = None
    success: Optional[bool] = None  # Did it improve things?
    frames_elapsed: int = 0


class ConfigTuner:
    """
    Autonomous configuration tuning based on ML and neural insights.

    The ConfigTuner observes:
    - ML clustering (are behavioral phenotypes diverse?)
    - Anomaly detection (is the population healthy?)
    - Neural training (are organisms learning?)
    - Fitness trends (is evolution progressing?)

    Then adjusts parameters to optimize system behavior.
    """

    def __init__(self, config: Dict[str, Any], enabled: bool = True):
        self.config = config
        self.enabled = enabled

        # Tuning constraints (safety bounds) - FULL EXPANSION
        self.param_bounds = {
            # Evolution (Phase 1 - Original + Expanded)
            'evolution.mutation_rate.initial': (0.001, 0.15),
            'evolution.diversity_guard.penalty': (0.01, 0.2),
            'evolution.diversity_guard.frequency_threshold': (0.05, 0.3),
            'evolution.diversity_guard.hash_similarity_threshold': (0.8, 0.98),
            'evolution.population_size': (500, 5000),
            'evolution.adaptation_sensitivity': (0.0001, 0.01),

            # Feedback Knobs (Phase 1 - Original)
            'feedback.knobs.mutation_rate.initial': (0.002, 0.06),
            'feedback.knobs.new_edge_rate.initial': (0.2, 6.0),
            'feedback.knobs.clustering_bias.initial': (0.3, 1.6),
            'feedback.knobs.quantum_pruning.initial': (0.0, 1.0),

            # Neural Learning (Phase 1 - Neural Expansion)
            'neural.training.learning_rate': (0.0001, 0.01),
            'neural.training.gamma': (0.9, 0.999),
            'neural.training.epsilon_decay': (0.9, 0.999),
            'neural.training.batch_size': (32, 256),
            'neural.rewards.fitness_improvement': (0.5, 5.0),
            'neural.rewards.connection_success': (0.2, 3.0),
            'neural.rewards.survival': (0.1, 2.0),
            'neural.inheritance.crossover_rate': (0.5, 1.0),
            'neural.inheritance.mutation_rate': (0.05, 0.4),

            # Network Dynamics (Phase 2)
            'network.max_organisms': (500, 5000),
            'network.max_connections': (1000, 30000),
            'network.resource_pool': (100, 1000),

            # ML Analysis (Phase 3 - Meta-tuning!)
            'scikit.clustering.min_cluster_size': (2, 20),
            'scikit.anomaly_detection.contamination': (0.01, 0.3),
            'scikit.anomaly_detection.n_estimators': (50, 500),

            # Quantum Substrate (Phase 5)
            'quantum.initial_states': (20, 200),
            'quantum.entanglement_sensitivity': (1e-07, 1e-04),
            'quantum.prune_check_interval': (10, 200),

            # VP Monitoring (Phase 6)
            'vp_monitoring.adaptive_response.high_vp_threshold': (0.5, 0.95),
            'vp_monitoring.stabilization.smoothing_factor': (0.1, 0.5),
            'causation_detection.correlation_threshold': (0.3, 0.9),

            # META-META: Self-tuning the tuner! (CRAZY Phase)
            'meta_cognitive.self_tuning.tuning_interval_frames': (10, 200),
            'meta_cognitive.self_tuning.min_confidence_threshold': (0.3, 0.95),
        }

        # Tuning aggressiveness (how much to change per adjustment)
        self.step_sizes = {
            # Evolution
            'evolution.mutation_rate.initial': 0.005,
            'evolution.diversity_guard.penalty': 0.01,
            'evolution.diversity_guard.frequency_threshold': 0.02,
            'evolution.diversity_guard.hash_similarity_threshold': 0.02,
            'evolution.population_size': 100,
            'evolution.adaptation_sensitivity': 0.0005,

            # Feedback
            'feedback.knobs.mutation_rate.initial': 0.002,
            'feedback.knobs.new_edge_rate.initial': 0.2,
            'feedback.knobs.clustering_bias.initial': 0.05,
            'feedback.knobs.quantum_pruning.initial': 0.05,

            # Neural
            'neural.training.learning_rate': 0.0005,
            'neural.training.gamma': 0.005,
            'neural.training.epsilon_decay': 0.005,
            'neural.training.batch_size': 16,
            'neural.rewards.fitness_improvement': 0.2,
            'neural.rewards.connection_success': 0.2,
            'neural.rewards.survival': 0.1,
            'neural.inheritance.crossover_rate': 0.05,
            'neural.inheritance.mutation_rate': 0.02,

            # Network
            'network.max_organisms': 200,
            'network.max_connections': 1000,
            'network.resource_pool': 50,

            # ML
            'scikit.clustering.min_cluster_size': 2,
            'scikit.anomaly_detection.contamination': 0.02,
            'scikit.anomaly_detection.n_estimators': 50,

            # Quantum
            'quantum.initial_states': 10,
            'quantum.entanglement_sensitivity': 1e-06,
            'quantum.prune_check_interval': 10,

            # VP
            'vp_monitoring.adaptive_response.high_vp_threshold': 0.05,
            'vp_monitoring.stabilization.smoothing_factor': 0.05,
            'causation_detection.correlation_threshold': 0.05,

            # Meta-meta
            'meta_cognitive.self_tuning.tuning_interval_frames': 10,
            'meta_cognitive.self_tuning.min_confidence_threshold': 0.05,
        }

        # History tracking
        self.tuning_history: List[TuningHistory] = []
        self.last_tuning_time = 0
        self.tuning_interval = self.config.get('meta_cognitive', {}).get('self_tuning', {}).get('tuning_interval_frames', 50)

        # Performance tracking
        self.fitness_history: List[float] = []
        self.cluster_count_history: List[int] = []
        self.anomaly_ratio_history: List[float] = []
        self.neural_loss_history: List[float] = []
        self.network_density_history: List[float] = []
        self.vp_history: List[float] = []

        # Meta-learning: track which actions work
        self.action_success_rates: Dict[str, Tuple[int, int]] = {}  # param -> (successes, total)
        
        # Event emitter for causation graph (set by RealitySimulator)
        self.event_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Track recent events for causation linking (last 10 events)
        self.recent_events: List[Dict[str, Any]] = []  # Store recent ML/neural events for causation

        logger.info(f"[CONFIG_TUNER] Initialized ({'ENABLED' if enabled else 'DISABLED'})")

    def should_tune(self, frame_count: int) -> bool:
        """Determine if it's time to consider tuning"""
        if not self.enabled:
            return False

        frames_since_last = frame_count - self.last_tuning_time
        return frames_since_last >= self.tuning_interval

    def analyze_and_tune(self,
                         ml_metrics: Dict[str, Any],
                         neural_metrics: Dict[str, Any],
                         evolution_metrics: Dict[str, Any],
                         network_metrics: Dict[str, Any],
                         frame_count: int) -> Optional[TuningAction]:
        """
        Main tuning logic: analyze system state and propose config changes.

        Returns a TuningAction if a change is recommended, None otherwise.
        """
        if not self.should_tune(frame_count):
            return None

        # Update history
        self._update_history(ml_metrics, neural_metrics, evolution_metrics)

        # Analyze different aspects (ALL PHASES!)
        actions = []

        # Phase 1 - Evolution & Diversity
        cluster_action = self._analyze_cluster_diversity(ml_metrics, evolution_metrics)
        if cluster_action:
            actions.append(cluster_action)

        anomaly_action = self._analyze_anomalies(ml_metrics)
        if anomaly_action:
            actions.append(anomaly_action)

        fitness_action = self._analyze_fitness_trends(evolution_metrics)
        if fitness_action:
            actions.append(fitness_action)

        # Phase 1 - Neural Learning
        neural_action = self._analyze_neural_learning(neural_metrics)
        if neural_action:
            actions.append(neural_action)

        # Phase 2 - Network Health
        network_action = self._analyze_network_health(network_metrics)
        if network_action:
            actions.append(network_action)

        # Phase 3 - ML Meta-Tuning
        ml_action = self._analyze_ml_effectiveness(ml_metrics)
        if ml_action:
            actions.append(ml_action)

        # Phase 5 - Quantum (placeholder for now)
        # quantum_action = self._analyze_quantum_stability(quantum_metrics)
        # if quantum_action:
        #     actions.append(quantum_action)

        # Phase 6 - VP Health
        vp_value = network_metrics.get('vp', None) if network_metrics else None
        vp_action = self._analyze_vp_health(vp_value)
        if vp_action:
            actions.append(vp_action)

        # CRAZY PHASE - Meta-Meta Learning (tune the tuner!)
        meta_action = self._analyze_meta_tuning_performance()
        if meta_action:
            actions.append(meta_action)

        # Select best action (highest confidence)
        if actions:
            best_action = max(actions, key=lambda a: a.confidence)

            # Meta-learning: boost confidence if this param has worked before
            param = best_action.parameter_path
            if param in self.action_success_rates:
                successes, total = self.action_success_rates[param]
                if total > 0:
                    success_rate = successes / total
                    best_action.confidence *= (0.5 + 0.5 * success_rate)  # Boost up to 1.0x

            # Only apply if confidence is high enough
            if best_action.confidence > 0.6:
                self.last_tuning_time = frame_count

                # Record the action for tracking
                history = TuningHistory(
                    action=best_action,
                    fitness_before=self.fitness_history[-1] if self.fitness_history else 0.0
                )
                self.tuning_history.append(history)

                # Emit structured tuning event to causation graph
                self._emit_tuning_event(best_action)
                
                logger.info(f"[CONFIG_TUNER] Proposing: {best_action.parameter_path} "
                          f"{best_action.current_value:.4f} → {best_action.proposed_value:.4f} "
                          f"(confidence: {best_action.confidence:.2f}) | {best_action.reason}")
                if best_action.trigger_metrics:
                    logger.info(f"[CONFIG_TUNER] Trigger metrics: {best_action.trigger_metrics}")
                if best_action.expected_impact:
                    logger.info(f"[CONFIG_TUNER] Expected impact: {best_action.expected_impact}")

                return best_action

        return None

    def _update_history(self, ml_metrics, neural_metrics, evolution_metrics):
        """Update performance history"""
        # Track fitness
        if evolution_metrics and 'best_fitness' in evolution_metrics:
            self.fitness_history.append(evolution_metrics['best_fitness'])
            if len(self.fitness_history) > 100:
                self.fitness_history.pop(0)

        # Track cluster count
        if ml_metrics and ml_metrics.get('enabled'):
            clustering = ml_metrics.get('clustering', {})
            n_clusters = clustering.get('n_clusters', 0)
            self.cluster_count_history.append(n_clusters)
            if len(self.cluster_count_history) > 100:
                self.cluster_count_history.pop(0)

        # Track anomaly ratio
        if ml_metrics and ml_metrics.get('enabled'):
            anomalies = ml_metrics.get('anomalies', {})
            ratio = anomalies.get('anomaly_ratio', 0.0)
            self.anomaly_ratio_history.append(ratio)
            if len(self.anomaly_ratio_history) > 100:
                self.anomaly_ratio_history.pop(0)

        # Update success tracking for recent actions
        if len(self.tuning_history) > 0 and len(self.fitness_history) >= 2:
            for history in self.tuning_history[-5:]:  # Check last 5 actions
                if history.fitness_after is None and history.frames_elapsed > 20:
                    # Evaluate if action helped
                    history.fitness_after = self.fitness_history[-1]
                    
                    # Improved success detection: handle zero fitness std case
                    # If fitness hasn't changed, check other metrics (cluster diversity, anomaly ratio, etc.)
                    fitness_improved = history.fitness_after > history.fitness_before
                    
                    # Calculate actual impact for structured explanation
                    action = history.action
                    actual_impact_parts = []
                    
                    # Fitness change
                    fitness_change = history.fitness_after - history.fitness_before
                    if abs(fitness_change) > 1e-6:
                        actual_impact_parts.append(f"Fitness: {history.fitness_before:.4f} → {history.fitness_after:.4f} ({'+' if fitness_change > 0 else ''}{fitness_change:.4f})")
                    
                    # Cluster diversity change (if available)
                    if len(self.cluster_count_history) >= 2:
                        clusters_before = self.cluster_count_history[-history.frames_elapsed] if history.frames_elapsed < len(self.cluster_count_history) else self.cluster_count_history[0]
                        clusters_after = self.cluster_count_history[-1]
                        if clusters_after != clusters_before:
                            actual_impact_parts.append(f"Clusters: {clusters_before} → {clusters_after}")
                    
                    # Anomaly ratio change (if available)
                    if len(self.anomaly_ratio_history) >= 2:
                        anomaly_before = self.anomaly_ratio_history[-history.frames_elapsed] if history.frames_elapsed < len(self.anomaly_ratio_history) else self.anomaly_ratio_history[0]
                        anomaly_after = self.anomaly_ratio_history[-1]
                        if abs(anomaly_after - anomaly_before) > 0.01:
                            actual_impact_parts.append(f"Anomaly ratio: {anomaly_before:.3f} → {anomaly_after:.3f}")
                    
                    # Build actual impact string
                    if actual_impact_parts:
                        action.actual_impact = "; ".join(actual_impact_parts)
                    else:
                        action.actual_impact = "No significant metric changes detected"
                    
                    # If fitness is stagnant (no change), use alternative metrics
                    if abs(history.fitness_after - history.fitness_before) < 1e-6:
                        # Check if other metrics improved (cluster diversity, anomaly ratio, etc.)
                        # For now, mark as neutral (not success, not failure) if fitness unchanged
                        # This prevents false negatives when fitness std is zero
                        history.success = None  # Neutral - can't determine
                    else:
                        history.success = fitness_improved

                    # Update success rates (only count if we have a definitive answer)
                    param = history.action.parameter_path
                    if param not in self.action_success_rates:
                        self.action_success_rates[param] = (0, 0)

                    if history.success is not None:  # Only update if we have a definitive result
                        successes, total = self.action_success_rates[param]
                        self.action_success_rates[param] = (
                            successes + (1 if history.success else 0),
                            total + 1
                        )
                else:
                    history.frames_elapsed += 1

    def _analyze_cluster_diversity(self, ml_metrics, evolution_metrics) -> Optional[TuningAction]:
        """Analyze cluster diversity and suggest mutations if needed"""
        if not ml_metrics or not ml_metrics.get('enabled'):
            return None

        clustering = ml_metrics.get('clustering', {})
        n_clusters = clustering.get('n_clusters', 0)

        # Low diversity: increase mutation to create more variety
        if len(self.cluster_count_history) >= 10:
            avg_clusters = sum(self.cluster_count_history[-10:]) / 10

            if avg_clusters < 3:
                param = 'evolution.mutation_rate.initial'
                current = self._get_param_value(param)
                proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

                if proposed > current:
                    # Find recent ML event that might have triggered this
                    causation_event_id = self._find_recent_event('ml_analysis', 'phenotype_emergence')
                    
                    # Get current metrics for trigger context
                    clustering = ml_metrics.get('clustering', {})
                    anomalies = ml_metrics.get('anomalies', {})
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Low cluster diversity ({avg_clusters:.1f} < 3 target) - increasing mutation for variety",
                        confidence=0.8,
                        trigger_metrics={
                            'cluster_count': float(avg_clusters),
                            'target_diversity': 3.0,
                            'anomaly_ratio': anomalies.get('anomaly_ratio', 0.0),
                            'cluster_sizes': len(clustering.get('cluster_sizes', {}))
                        },
                        causation_event_id=causation_event_id,
                        expected_impact=f"Should increase cluster diversity to 3-4 clusters within 20-30 cycles"
                    )

        return None

    def _analyze_anomalies(self, ml_metrics) -> Optional[TuningAction]:
        """Analyze anomaly ratio and suggest diversity guard adjustments"""
        if not ml_metrics or not ml_metrics.get('enabled'):
            return None

        anomalies = ml_metrics.get('anomalies', {})
        ratio = anomalies.get('anomaly_ratio', 0.0)

        # Too many anomalies: tighten diversity guard
        if len(self.anomaly_ratio_history) >= 10:
            avg_ratio = sum(self.anomaly_ratio_history[-10:]) / 10

            if avg_ratio > 0.20:
                param = 'evolution.diversity_guard.penalty'
                current = self._get_param_value(param)
                proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

                if proposed > current:
                    causation_event_id = self._find_recent_event('ml_analysis', 'anomaly_spike')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"High anomaly ratio ({avg_ratio:.2f} > 0.20 target) - strengthening diversity guard",
                        confidence=0.75,
                        trigger_metrics={
                            'anomaly_ratio': float(avg_ratio),
                            'target_ratio': 0.20,
                            'anomaly_count': anomalies.get('anomaly_count', 0)
                        },
                        causation_event_id=causation_event_id,
                        expected_impact=f"Should reduce anomaly ratio to 0.15-0.20 within 15-25 cycles"
                    )

        return None

    def _analyze_fitness_trends(self, evolution_metrics) -> Optional[TuningAction]:
        """Analyze fitness stagnation and suggest network growth"""
        if len(self.fitness_history) < 20:
            return None

        # Check for stagnation (low variance in recent fitness)
        recent_fitness = self.fitness_history[-20:]
        avg = sum(recent_fitness) / len(recent_fitness)
        variance = sum((f - avg) ** 2 for f in recent_fitness) / len(recent_fitness)
        std_dev = variance ** 0.5

        if std_dev < 0.05:  # Very low variance = stagnation
            param = 'feedback.knobs.new_edge_rate.initial'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

            if proposed > current:
                avg_fitness = sum(recent_fitness) / len(recent_fitness)
                causation_event_id = self._find_recent_event('evolution', 'generation')
                
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Fitness stagnating (std={std_dev:.4f} < 0.05 threshold) - increasing network connectivity",
                    confidence=0.7,
                    trigger_metrics={
                        'fitness_std': float(std_dev),
                        'fitness_mean': float(avg_fitness),
                        'stagnation_threshold': 0.05
                    },
                    causation_event_id=causation_event_id,
                    expected_impact=f"Should increase fitness variance and enable new evolutionary paths within 20-30 cycles"
                )

        return None

    def _analyze_neural_learning(self, neural_metrics) -> Optional[TuningAction]:
        """Analyze neural training and suggest adjustments if learning is poor"""
        if not neural_metrics or not neural_metrics.get('enabled'):
            return None

        # Track neural loss (only track non-None values)
        if 'training_loss' in neural_metrics:
            loss = neural_metrics['training_loss']
            # Only append if loss is a valid number (not None - happens during buffer warmup)
            if loss is not None:
                self.neural_loss_history.append(loss)
                if len(self.neural_loss_history) > 100:
                    self.neural_loss_history.pop(0)

        # Check if loss is increasing (learning getting worse)
        if len(self.neural_loss_history) >= 20:
            # Filter out any None values that might have slipped through
            recent_loss = [l for l in self.neural_loss_history[-10:] if l is not None]
            older_loss = [l for l in self.neural_loss_history[-20:-10] if l is not None]

            if len(recent_loss) > 0 and len(older_loss) > 0:
                avg_recent = sum(recent_loss) / len(recent_loss)
                avg_older = sum(older_loss) / len(older_loss)

                # Loss increasing = learning degrading
                if avg_recent > avg_older * 1.2:  # 20% worse
                    param = 'neural.training.learning_rate'
                    current = self._get_param_value(param)
                    proposed = max(current * 0.8, self.param_bounds[param][0])  # Decrease by 20%

                    if proposed < current:
                        causation_event_id = self._find_recent_event('neural', 'neural_training')
                        
                        return TuningAction(
                            parameter_path=param,
                            current_value=current,
                            proposed_value=proposed,
                            reason=f"Neural loss increasing ({avg_recent:.4f} > {avg_older:.4f} baseline, +{((avg_recent/avg_older - 1) * 100):.1f}%) - reducing learning rate",
                            confidence=0.75,
                            trigger_metrics={
                                'current_loss': float(avg_recent),
                                'baseline_loss': float(avg_older),
                                'loss_increase_ratio': float(avg_recent / avg_older),
                                'training_steps': neural_metrics.get('training_steps', 0)
                            },
                            causation_event_id=causation_event_id,
                            expected_impact=f"Should stabilize loss and improve learning convergence within 10-20 training cycles"
                        )

        return None

    def _analyze_network_health(self, network_metrics) -> Optional[TuningAction]:
        """Analyze network density and resource availability"""
        if not network_metrics:
            return None

        organism_count = network_metrics.get('organism_count', 0)
        connection_count = network_metrics.get('connection_count', 0)

        if organism_count > 0:
            density = connection_count / max(organism_count, 1)
            self.network_density_history.append(density)
            if len(self.network_density_history) > 100:
                self.network_density_history.pop(0)

        # Network too dense = performance issues
        if len(self.network_density_history) >= 10:
            avg_density = sum(self.network_density_history[-10:]) / 10

            if avg_density > 8.0:  # Very high connections per organism
                param = 'network.max_organisms'
                current = self._get_param_value(param)
                proposed = max(current - self.step_sizes[param], self.param_bounds[param][0])

                if proposed < current:
                    causation_event_id = self._find_recent_event('network', 'connection')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Network too dense (avg {avg_density:.1f} > 8.0 conn/org threshold) - reducing max organisms",
                        confidence=0.7,
                        trigger_metrics={
                            'connection_density': float(avg_density),
                            'density_threshold': 8.0,
                            'organism_count': network_metrics.get('organism_count', 0),
                            'connection_count': network_metrics.get('connection_count', 0)
                        },
                        causation_event_id=causation_event_id,
                        expected_impact=f"Should reduce connection density to 6-7 conn/org and improve performance within 10-15 cycles"
                    )

        return None

    def _analyze_ml_effectiveness(self, ml_metrics) -> Optional[TuningAction]:
        """Meta-tune the ML analyzer itself!"""
        if not ml_metrics or not ml_metrics.get('enabled'):
            return None

        clustering = ml_metrics.get('clustering', {})
        cluster_sizes = clustering.get('cluster_sizes', {})

        # Too many tiny clusters = min_cluster_size too small
        if cluster_sizes:
            tiny_clusters = sum(1 for size in cluster_sizes.values() if size < 5)
            total_clusters = len(cluster_sizes)

            if total_clusters > 0 and tiny_clusters / total_clusters > 0.5:
                param = 'scikit.clustering.min_cluster_size'
                current = self._get_param_value(param)
                proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

                if proposed > current:
                    causation_event_id = self._find_recent_event('ml_analysis', 'phenotype_emergence')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Too many tiny clusters ({tiny_clusters}/{total_clusters} = {(tiny_clusters/total_clusters)*100:.1f}% > 50% threshold) - increasing min size",
                        confidence=0.65,
                        trigger_metrics={
                            'tiny_clusters': float(tiny_clusters),
                            'total_clusters': float(total_clusters),
                            'tiny_ratio': float(tiny_clusters / total_clusters),
                            'current_min_size': float(current)
                        },
                        causation_event_id=causation_event_id,
                        expected_impact=f"Should reduce tiny clusters and improve cluster quality within 5-10 ML analysis cycles"
                    )

        return None

    def _analyze_quantum_stability(self, quantum_metrics) -> Optional[TuningAction]:
        """Analyze quantum substrate performance"""
        # Placeholder for quantum metrics
        # Could check: pruning frequency, state count, entanglement levels
        return None

    def _analyze_vp_health(self, vp_value: float) -> Optional[TuningAction]:
        """Analyze VP levels and stabilization"""
        if vp_value is not None:
            self.vp_history.append(vp_value)
            if len(self.vp_history) > 100:
                self.vp_history.pop(0)

        # Check if VP is oscillating wildly
        if len(self.vp_history) >= 20:
            recent_vp = self.vp_history[-20:]
            vp_variance = sum((v - sum(recent_vp)/len(recent_vp))**2 for v in recent_vp) / len(recent_vp)
            vp_std = vp_variance ** 0.5

            if vp_std > 0.3:  # High variance = unstable
                param = 'vp_monitoring.stabilization.smoothing_factor'
                current = self._get_param_value(param)
                proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

                if proposed > current:
                    causation_event_id = self._find_recent_event('djinn_kernel', 'vp_calculation')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"VP unstable (std={vp_std:.3f} > 0.3 threshold) - increasing smoothing",
                        confidence=0.65,
                        trigger_metrics={
                            'vp_std': float(vp_std),
                            'vp_mean': float(sum(recent_vp) / len(recent_vp)),
                            'stability_threshold': 0.3,
                            'current_vp': float(vp_value) if vp_value is not None else 0.0
                        },
                        causation_event_id=causation_event_id,
                        expected_impact=f"Should reduce VP oscillations and stabilize system pressure within 15-25 cycles"
                    )

        return None

    def _analyze_meta_tuning_performance(self) -> Optional[TuningAction]:
        """META-META: Tune the tuner itself!"""
        if len(self.tuning_history) < 10:
            return None

        # Check recent success rate
        recent_actions = self.tuning_history[-10:]
        successful = sum(1 for h in recent_actions if h.success)
        success_rate = successful / len(recent_actions) if recent_actions else 0

        # Low success rate = being too aggressive, increase confidence threshold
        if success_rate < 0.3:
            param = 'meta_cognitive.self_tuning.min_confidence_threshold'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])

            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Low tuning success rate ({success_rate:.1%} < 30% threshold) - requiring higher confidence",
                    confidence=0.8,
                    trigger_metrics={
                        'success_rate': float(success_rate),
                        'target_rate': 0.30,
                        'recent_actions': len(recent_actions),
                        'successful_actions': float(successful)
                    },
                    causation_event_id=None,  # Meta-tuning doesn't have external trigger
                    expected_impact=f"Should improve tuning action quality by requiring higher confidence threshold"
                )

        # High success rate = can be more aggressive, decrease interval
        elif success_rate > 0.7:
            param = 'meta_cognitive.self_tuning.tuning_interval_frames'
            current = self._get_param_value(param)
            proposed = max(current - self.step_sizes[param], self.param_bounds[param][0])

            if proposed < current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"High tuning success rate ({success_rate:.1%} > 70% threshold) - tuning more frequently",
                    confidence=0.7,
                    trigger_metrics={
                        'success_rate': float(success_rate),
                        'target_rate': 0.70,
                        'recent_actions': len(recent_actions),
                        'successful_actions': float(successful)
                    },
                    causation_event_id=None,  # Meta-tuning doesn't have external trigger
                    expected_impact=f"Should enable more frequent optimization opportunities while maintaining quality"
                )

        return None

    def _get_param_value(self, path: str) -> float:
        """Get current value of a config parameter by path"""
        parts = path.split('.')
        value = self.config
        for part in parts:
            value = value.get(part, {})
        return float(value) if isinstance(value, (int, float)) else 0.0
    
    def _find_recent_event(self, component: str, event_type: str) -> Optional[str]:
        """
        Find most recent event matching component and event_type.
        Returns event_id if found, None otherwise.
        
        Used for causation linking in structured explanations.
        """
        for event in reversed(self.recent_events):  # Most recent first
            if event.get('component') == component and event.get('event_type') == event_type:
                return event.get('event_id')
        return None
    
    def track_event(self, event: Dict[str, Any]):
        """
        Track recent events for causation linking.
        Called by RealitySimulator when events are emitted.
        """
        # Store event with event_id if available
        event_copy = {
            'component': event.get('component', 'unknown'),
            'event_type': event.get('event_type', 'unknown'),
            'event_id': event.get('event_id', f"evt_{int(time.time() * 1000)}"),
            'timestamp': event.get('timestamp', time.time())
        }
        
        self.recent_events.append(event_copy)
        
        # Keep only last 20 events
        if len(self.recent_events) > 20:
            self.recent_events.pop(0)

    def apply_action(self, action: TuningAction) -> bool:
        """
        Apply a tuning action to the config.

        Note: This modifies self.config in-memory. For persistent changes,
        the config should be written to disk.
        """
        parts = action.parameter_path.split('.')

        # Navigate to the parent dict
        current = self.config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        old_value = current.get(parts[-1], action.current_value)
        current[parts[-1]] = action.proposed_value

        logger.info(f"[CONFIG_TUNER] Applied: {action.parameter_path} "
                   f"{old_value:.4f} → {action.proposed_value:.4f}")

        return True

    def _emit_tuning_event(self, action: TuningAction):
        """
        Emit tuning action event to causation graph with structured explanation data.
        """
        if not self.event_emitter:
            return
        
        try:
            event = {
                'timestamp': action.timestamp,
                'component': 'config_tuner',
                'event_type': 'tuning_action',
                'data': {
                    'parameter_path': action.parameter_path,
                    'current_value': action.current_value,
                    'proposed_value': action.proposed_value,
                    'reason': action.reason,
                    'confidence': action.confidence,
                    'trigger_metrics': action.trigger_metrics,
                    'causation_event_id': action.causation_event_id,
                    'expected_impact': action.expected_impact,
                    'actual_impact': action.actual_impact  # May be None if not evaluated yet
                }
            }
            
            self.event_emitter(event)
            
            # Also track this event for future causation linking
            event['event_id'] = event['data'].get('causation_event_id') or f"tuning_{int(action.timestamp * 1000)}"
            self.track_event(event)
            
        except Exception as e:
            logger.warning(f"[CONFIG_TUNER] Error emitting tuning event: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tuning statistics with structured explanation data"""
        total_actions = len(self.tuning_history)
        successful_actions = sum(1 for h in self.tuning_history if h.success)

        return {
            'enabled': self.enabled,
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': successful_actions / total_actions if total_actions > 0 else 0.0,
            'param_success_rates': {
                param: successes / total if total > 0 else 0.0
                for param, (successes, total) in self.action_success_rates.items()
            },
            'recent_actions': [
                {
                    'param': h.action.parameter_path,
                    'change': f"{h.action.current_value:.4f} → {h.action.proposed_value:.4f}",
                    'reason': h.action.reason,
                    'success': h.success,
                    'trigger_metrics': h.action.trigger_metrics,
                    'expected_impact': h.action.expected_impact,
                    'actual_impact': h.action.actual_impact
                }
                for h in self.tuning_history[-5:]
            ]
        }
