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
            
            # Neural-ML Symbiosis (Integration 1-3) ⭐ NEW
            'scikit.clustering.use_neural_embeddings': (0, 1),  # Boolean as 0/1
            'neural.training.language_reward_scaling': (0.0, 1.0),
            'neural.language_model.curriculum.ml_quality.enabled': (0, 1),  # Boolean
            'neural.language_model.curriculum.ml_quality.high_quality_threshold': (0.5, 0.9),
            'neural.language_model.curriculum.ml_quality.low_quality_threshold': (0.1, 0.4),
            'neural.language_model.curriculum.ml_quality.max_sequence_length': (8, 128),
            'neural.language_model.curriculum.ml_quality.min_sequence_length': (4, 32),
            'neural.language_model.curriculum.ml_quality.sequence_length_step': (1, 8),
            
            # Language-Game Bridge ⭐ Cross-system correlation tuning
            'neural.language_game_bridge.bias_strength': (0.1, 0.7),  # How much vocab biases actions
            'neural.language_game_bridge.learning_rate': (0.01, 0.3),  # How fast bridge learns from outcomes

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
            
            # Neural-ML Symbiosis ⭐ NEW
            'scikit.clustering.use_neural_embeddings': 1,  # Toggle
            'neural.training.language_reward_scaling': 0.05,
            'neural.language_model.curriculum.ml_quality.enabled': 1,  # Toggle
            'neural.language_model.curriculum.ml_quality.high_quality_threshold': 0.05,
            'neural.language_model.curriculum.ml_quality.low_quality_threshold': 0.05,
            'neural.language_model.curriculum.ml_quality.max_sequence_length': 4,
            'neural.language_model.curriculum.ml_quality.min_sequence_length': 2,
            'neural.language_model.curriculum.ml_quality.sequence_length_step': 1,
            
            # Language-Game Bridge ⭐ Cross-system correlation tuning
            'neural.language_game_bridge.bias_strength': 0.05,  # Gentle adjustments
            'neural.language_game_bridge.learning_rate': 0.02,  # Careful learning rate changes

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
        
        # Neural-ML Symbiosis tracking ⭐ NEW
        self.embedding_quality_history: List[float] = []  # Silhouette scores with embeddings
        self.language_reward_history: List[float] = []  # Total language rewards per training step
        self.curriculum_adjustment_history: List[int] = []  # Sequence length adjustments
        self.vocabulary_growth_history: List[int] = []  # Vocabulary size over time

        # Meta-learning: track which actions work
        self.action_success_rates: Dict[str, Tuple[int, int]] = {}  # param -> (successes, total)
        
        # Event emitter for causation graph (set by RealitySimulator)
        self.event_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Track recent events for causation linking (last 10 events)
        self.recent_events: List[Dict[str, Any]] = []  # Store recent ML/neural events for causation
        
        # Live report data storage for meta-brain analysis
        self._live_report_cache: Optional[Dict[str, Any]] = None
        self._live_report_timestamp: float = 0.0

        # Reference to HighlanderProtocol for propagating bridge parameter changes
        self._highlander_protocol: Optional[Any] = None

    def set_highlander_protocol(self, highlander) -> None:
        """
        Wire the HighlanderProtocol for propagating bridge parameter updates.
        
        This enables ConfigTuner to push bias_strength/learning_rate changes
        directly to the running LanguageGameBridge.
        """
        self._highlander_protocol = highlander
        if highlander and hasattr(highlander, 'language_bridge') and highlander.language_bridge:
            logger.info("[CONFIG_TUNER] 🔗 Wired to HighlanderProtocol.language_bridge for parameter propagation")

    def ingest_live_report(self, report_data: Dict[str, Any]) -> None:
        """
        Accept live_report data for meta-brain analysis.
        
        The live_report is the OUTPUT of system monitoring - it contains
        runtime observations that the ConfigTuner uses to make tuning decisions.
        This completes the loop: config.json → runtime → live_report → tuning → config.json
        
        Args:
            report_data: Full live_report data (timestamp, frame_count, all metric sections)
        """
        import time
        self._live_report_cache = report_data
        self._live_report_timestamp = time.time()
        
        # Log receipt of live report for debugging feedback loop
        lgb = report_data.get('language_game_bridge', {}) if report_data else {}
        if lgb.get('episodes_tracked', 0) > 0:
            logger.debug(f"[CONFIG_TUNER] 📊 Live report ingested: "
                        f"episodes={lgb.get('episodes_tracked', 0)}, "
                        f"alignment={lgb.get('vocabulary_game_alignment', 0):.3f}, "
                        f"diversity={lgb.get('concept_diversity', 0):.3f}")
        
        # Extract and integrate metrics into our analysis histories
        if not report_data:
            return
            
        # Extract Language-Game Bridge metrics for correlation analysis
        lgb_metrics = report_data.get('language_game_bridge', {}) or {}
        if lgb_metrics and lgb_metrics.get('active'):
            # Track vocabulary-game alignment trend
            alignment = lgb_metrics.get('vocabulary_game_alignment', 0.0)
            if not hasattr(self, 'vocab_game_alignment_history'):
                self.vocab_game_alignment_history: List[float] = []
            self.vocab_game_alignment_history.append(alignment)
            if len(self.vocab_game_alignment_history) > 100:
                self.vocab_game_alignment_history.pop(0)
            
            # Track language decision influence
            influence = lgb_metrics.get('language_decision_influence', 0.0)
            if not hasattr(self, 'lang_decision_influence_history'):
                self.lang_decision_influence_history: List[float] = []
            self.lang_decision_influence_history.append(influence)
            if len(self.lang_decision_influence_history) > 100:
                self.lang_decision_influence_history.pop(0)
                
        # Extract evolution metrics for fitness tracking
        evolution = report_data.get('evolution', {}) or {}
        if evolution:
            best_fitness = evolution.get('best_fitness', 0.0)
            if best_fitness > 0:
                self.fitness_history.append(best_fitness)
                if len(self.fitness_history) > 100:
                    self.fitness_history.pop(0)
        
        # Extract ML metrics
        ml = report_data.get('ml_metrics', {}) or {}
        if ml and ml.get('enabled'):
            clustering = ml.get('clustering', {}) or {}
            n_clusters = clustering.get('n_clusters', 0)
            if n_clusters > 0:
                self.cluster_count_history.append(n_clusters)
                if len(self.cluster_count_history) > 100:
                    self.cluster_count_history.pop(0)
        
        # Extract network health
        network = report_data.get('network', {}) or {}
        if network:
            density = network.get('density', 0.0)
            if density > 0:
                self.network_density_history.append(density)
                if len(self.network_density_history) > 100:
                    self.network_density_history.pop(0)

    def get_cached_live_report(self) -> Optional[Dict[str, Any]]:
        """Return the most recent live_report data for analysis."""
        return self._live_report_cache

    def analyze_with_live_report(self, frame_count: int) -> Optional['TuningAction']:
        """
        Run analysis using cached live_report data.
        
        This is an alternative entry point that uses live_report data
        instead of requiring explicit metric dictionaries.
        """
        if not self._live_report_cache:
            return None
            
        report = self._live_report_cache
        
        # Convert live_report structure to analyze_and_tune parameters
        # Use 'or {}' to handle None values from explicit null keys
        ml_metrics = report.get('ml_metrics', {}) or {}
        neural_metrics = report.get('neural', {}) or {}
        evolution_metrics = report.get('evolution', {}) or {}
        network_metrics = report.get('network', {}) or {}
        
        # Merge language_game_bridge into network_metrics for analyzer access
        lgb = report.get('language_game_bridge', {}) or {}
        if lgb:
            network_metrics['language_game_bridge'] = lgb
        
        return self.analyze_and_tune(
            ml_metrics=ml_metrics,
            neural_metrics=neural_metrics,
            evolution_metrics=evolution_metrics,
            network_metrics=network_metrics,
            frame_count=frame_count
        )

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

        # Phase 4 - Language-Aware Tuning ⭐ NEW
        language_action = self._analyze_language_quality(ml_metrics, neural_metrics)
        if language_action:
            actions.append(language_action)
        
        # Phase 4.5 - Neural-ML Symbiosis Effectiveness ⭐ NEW
        symbiosis_action = self._analyze_neural_ml_symbiosis(ml_metrics, neural_metrics)
        if symbiosis_action:
            actions.append(symbiosis_action)

        # Phase 4.6 - Cross-System Correlation Analysis ⭐ INTEGRATION
        # Quantum-Language correlation
        quantum_metrics = (network_metrics.get('quantum', {}) or {}) if network_metrics else {}
        quantum_lang_action = self._analyze_quantum_language_correlation(quantum_metrics, ml_metrics)
        if quantum_lang_action:
            actions.append(quantum_lang_action)
        
        # Network-Alliance correlation
        alliance_metrics = (network_metrics.get('alliances', {}) or {}) if network_metrics else {}
        network_alliance_action = self._analyze_network_alliance_correlation(network_metrics, alliance_metrics)
        if network_alliance_action:
            actions.append(network_alliance_action)
        
        # Neural-Battle correlation
        battle_metrics = (network_metrics.get('battles', {}) or {}) if network_metrics else {}
        neural_battle_action = self._analyze_neural_battle_correlation(neural_metrics, battle_metrics)
        if neural_battle_action:
            actions.append(neural_battle_action)
        
        # Vocabulary-Fitness correlation
        language_metrics = (ml_metrics.get('language', {}) or {}) if ml_metrics else {}
        vocab_fitness_action = self._analyze_vocabulary_fitness_correlation(language_metrics, evolution_metrics)
        if vocab_fitness_action:
            actions.append(vocab_fitness_action)
        
        # Language-Game Bridge correlation ⭐ NEW 5th Analyzer
        # Use live report cache since language_game_bridge is at TOP LEVEL, not under network_metrics
        language_game_metrics = {}
        if self._live_report_cache:
            language_game_metrics = self._live_report_cache.get('language_game_bridge', {}) or {}
        lang_game_action = self._analyze_language_game_correlation(language_game_metrics, battle_metrics)
        if lang_game_action:
            actions.append(lang_game_action)

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

    def _analyze_language_quality(self, ml_metrics: Dict[str, Any], neural_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze language quality metrics and tune language learning parameters.
        
        Uses TF-IDF, vocabulary diversity, and language-behavior alignment to optimize
        language learning and generation.
        """
        if not ml_metrics or not ml_metrics.get('enabled'):
            return None
        
        semantic_analysis = ml_metrics.get('semantic_analysis', {})
        if not semantic_analysis:
            return None
        
        tfidf_results = semantic_analysis.get('tfidf_analysis', {})
        quality_metrics = semantic_analysis.get('quality_metrics', {})
        
        # Track vocabulary size for convergence detection
        if tfidf_results:
            vocab_size = tfidf_results.get('vocabulary_size', 0)
            if not hasattr(self, 'vocabulary_size_history'):
                self.vocabulary_size_history = []
            self.vocabulary_size_history.append(vocab_size)
            if len(self.vocabulary_size_history) > 50:
                self.vocabulary_size_history.pop(0)
        
        # 1. Vocabulary too small → increase language exploration
        if tfidf_results and len(self.vocabulary_size_history) >= 10:
            avg_vocab_size = sum(self.vocabulary_size_history[-10:]) / 10
            if avg_vocab_size < 30:  # Too small vocabulary
                param = 'neural.language_model.teacher.exploration_rate'
                current = self._get_param_value(param)
                if current is None:
                    # Try alternative path
                    param = 'neural.language_model.relationship_learning.semantic_guidance.semantic_boost'
                    current = self._get_param_value(param) or 0.2
                
                proposed = min(current + 0.05, 0.5) if current else 0.25
                
                if proposed > (current or 0):
                    causation_event_id = self._find_recent_event('ml_analysis', 'semantic_analysis')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current or 0.2,
                        proposed_value=proposed,
                        reason=f"Vocabulary too small ({avg_vocab_size:.1f} < 30 words) - increasing language exploration",
                        confidence=0.75,
                        trigger_metrics={
                            'vocabulary_size': float(avg_vocab_size),
                            'target_size': 30.0,
                            'top_words': len(tfidf_results.get('top_important_words', []))
                        },
                        causation_event_id=causation_event_id,
                        expected_impact="Should increase vocabulary diversity and word discovery within 10-20 generations"
                    )
        
        # 2. Vocabulary converging too fast → slow down learning (prevent premature convergence)
        if tfidf_results and len(self.vocabulary_size_history) >= 20:
            recent_vocab = self.vocabulary_size_history[-10:]
            older_vocab = self.vocabulary_size_history[-20:-10]
            
            if len(recent_vocab) > 0 and len(older_vocab) > 0:
                recent_avg = sum(recent_vocab) / len(recent_vocab)
                older_avg = sum(older_vocab) / len(older_vocab)
                
                # If vocabulary is growing very fast, might be premature convergence
                growth_rate = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
                
                if growth_rate > 0.5:  # 50% growth in 10 cycles = very fast
                    param = 'neural.language_model.relationship_learning.semantic_guidance.semantic_boost'
                    current = self._get_param_value(param) or 0.2
                    proposed = max(current - 0.05, 0.1)  # Reduce semantic guidance
                    
                    if proposed < current:
                        causation_event_id = self._find_recent_event('ml_analysis', 'semantic_analysis')
                        
                        return TuningAction(
                            parameter_path=param,
                            current_value=current,
                            proposed_value=proposed,
                            reason=f"Vocabulary growing too fast ({growth_rate*100:.1f}% > 50% threshold) - reducing semantic guidance to prevent premature convergence",
                            confidence=0.7,
                            trigger_metrics={
                                'vocabulary_growth_rate': float(growth_rate),
                                'recent_vocab_size': float(recent_avg),
                                'older_vocab_size': float(older_avg),
                                'growth_threshold': 0.5
                            },
                            causation_event_id=causation_event_id,
                            expected_impact="Should slow vocabulary convergence and allow more exploration within 15-25 generations"
                        )
        
        # 3. Low language quality (silhouette score) → improve language learning
        if quality_metrics:
            silhouette = quality_metrics.get('silhouette_score', None)
            if silhouette is not None and silhouette < 0.3:  # Low quality clusters
                param = 'neural.language_model.relationship_learning.quality_evaluation.coherent_threshold'
                current = self._get_param_value(param) or 0.5
                proposed = max(current - 0.1, 0.3)  # Lower threshold = more lenient
                
                if proposed < current:
                    causation_event_id = self._find_recent_event('ml_analysis', 'semantic_analysis')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Low language cluster quality (silhouette={silhouette:.3f} < 0.3) - relaxing quality threshold to allow more learning",
                        confidence=0.65,
                        trigger_metrics={
                            'silhouette_score': float(silhouette),
                            'n_clusters': quality_metrics.get('n_clusters', 0),
                            'quality_threshold': 0.3
                        },
                        causation_event_id=causation_event_id,
                        expected_impact="Should improve language cluster formation and communication quality within 20-30 generations"
                    )
        
        return None

    def _analyze_neural_ml_symbiosis(self, ml_metrics: Dict[str, Any], neural_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze Neural-ML Symbiosis effectiveness and tune integration parameters.
        
        Integration 1: Neural Embeddings → ML Features
        Integration 2: ML Feature Importance → Neural Rewards
        Integration 3: ML Quality Metrics → Neural Curriculum
        """
        if not ml_metrics or not ml_metrics.get('enabled'):
            return None
        
        semantic_analysis = ml_metrics.get('semantic_analysis', {}) or {}
        if not semantic_analysis:
            return None
        
        quality_metrics = semantic_analysis.get('quality_metrics', {}) or {}
        clustering = ml_metrics.get('clustering', {}) or {}
        
        # Track embedding quality (silhouette score when embeddings are used)
        use_embeddings = self._get_param_value('scikit.clustering.use_neural_embeddings')
        if use_embeddings > 0.5:  # Enabled
            silhouette = quality_metrics.get('silhouette_score', None)
            if silhouette is not None:
                self.embedding_quality_history.append(silhouette)
                if len(self.embedding_quality_history) > 50:
                    self.embedding_quality_history.pop(0)
        
        # Track language rewards from neural_metrics
        if neural_metrics and 'language_reward_total' in neural_metrics:
            lang_reward = neural_metrics.get('language_reward_total', 0.0)
            self.language_reward_history.append(lang_reward)
            if len(self.language_reward_history) > 50:
                self.language_reward_history.pop(0)
        
        # Track curriculum adjustments
        if neural_metrics and 'curriculum_sequence_length' in neural_metrics:
            seq_len = neural_metrics.get('curriculum_sequence_length', 0)
            self.curriculum_adjustment_history.append(seq_len)
            if len(self.curriculum_adjustment_history) > 50:
                self.curriculum_adjustment_history.pop(0)
        
        # 1. Integration 1: Embedding quality analysis
        if len(self.embedding_quality_history) >= 10:
            avg_embedding_quality = sum(self.embedding_quality_history[-10:]) / 10
            use_embeddings = self._get_param_value('scikit.clustering.use_neural_embeddings')
            
            # If embeddings enabled but quality is low, might need to disable or improve
            if use_embeddings > 0.5 and avg_embedding_quality < 0.2:
                # Try disabling embeddings to see if behavioral features work better
                param = 'scikit.clustering.use_neural_embeddings'
                current = use_embeddings
                proposed = 0.0  # Disable
                
                causation_event_id = self._find_recent_event('ml_analysis', 'semantic_analysis')
                
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Neural embeddings quality low (silhouette={avg_embedding_quality:.3f} < 0.2) - disabling to use behavioral features",
                    confidence=0.7,
                    trigger_metrics={
                        'embedding_quality': float(avg_embedding_quality),
                        'quality_threshold': 0.2,
                        'n_clusters': clustering.get('n_clusters', 0)
                    },
                    causation_event_id=causation_event_id,
                    expected_impact="Should improve clustering quality by using behavioral features instead of low-quality embeddings"
                )
            
            # If embeddings disabled but we have good neural organisms, try enabling
            elif use_embeddings < 0.5 and avg_embedding_quality > 0.4:
                param = 'scikit.clustering.use_neural_embeddings'
                current = use_embeddings
                proposed = 1.0  # Enable
                
                causation_event_id = self._find_recent_event('neural', 'neural_training')
                
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Neural embeddings available and quality good (silhouette={avg_embedding_quality:.3f} > 0.4) - enabling semantic clustering",
                    confidence=0.75,
                    trigger_metrics={
                        'embedding_quality': float(avg_embedding_quality),
                        'quality_threshold': 0.4
                    },
                    causation_event_id=causation_event_id,
                    expected_impact="Should improve clustering by using semantic embeddings instead of behavioral features"
                )
        
        # 2. Integration 2: Language reward scaling analysis
        if len(self.language_reward_history) >= 10:
            avg_reward = sum(self.language_reward_history[-10:]) / 10
            current_scaling = self._get_param_value('neural.training.language_reward_scaling')
            
            # If rewards are too low, increase scaling
            if avg_reward < 0.1 and current_scaling < 0.5:
                param = 'neural.training.language_reward_scaling'
                proposed = min(current_scaling + 0.1, 1.0)
                
                causation_event_id = self._find_recent_event('neural', 'neural_language_reward')
                
                return TuningAction(
                    parameter_path=param,
                    current_value=current_scaling,
                    proposed_value=proposed,
                    reason=f"Language rewards too low (avg={avg_reward:.3f} < 0.1) - increasing scaling to {proposed:.2f}",
                    confidence=0.7,
                    trigger_metrics={
                        'avg_language_reward': float(avg_reward),
                        'current_scaling': float(current_scaling),
                        'target_reward': 0.1
                    },
                    causation_event_id=causation_event_id,
                    expected_impact="Should increase language reward influence and improve vocabulary learning"
                )
            
            # If rewards are too high, decrease scaling (might be overwhelming base rewards)
            elif avg_reward > 2.0 and current_scaling > 0.1:
                param = 'neural.training.language_reward_scaling'
                proposed = max(current_scaling - 0.1, 0.0)
                
                causation_event_id = self._find_recent_event('neural', 'neural_language_reward')
                
                return TuningAction(
                    parameter_path=param,
                    current_value=current_scaling,
                    proposed_value=proposed,
                    reason=f"Language rewards too high (avg={avg_reward:.3f} > 2.0) - reducing scaling to {proposed:.2f} to balance with base rewards",
                    confidence=0.65,
                    trigger_metrics={
                        'avg_language_reward': float(avg_reward),
                        'current_scaling': float(current_scaling),
                        'target_reward': 2.0
                    },
                    causation_event_id=causation_event_id,
                    expected_impact="Should balance language rewards with base rewards for more stable learning"
                )
        
        # 3. Integration 3: Curriculum adjustment analysis
        if len(self.curriculum_adjustment_history) >= 10:
            recent_seq = self.curriculum_adjustment_history[-10:]
            older_seq = self.curriculum_adjustment_history[-20:-10] if len(self.curriculum_adjustment_history) >= 20 else []
            
            if len(recent_seq) > 0 and len(older_seq) > 0:
                recent_avg = sum(recent_seq) / len(recent_seq)
                older_avg = sum(older_seq) / len(older_seq)
                
                # If sequence length is oscillating wildly, adjust step size
                seq_variance = sum((s - recent_avg) ** 2 for s in recent_seq) / len(recent_seq)
                
                if seq_variance > 100:  # High variance = oscillating
                    param = 'neural.language_model.curriculum.ml_quality.sequence_length_step'
                    current = self._get_param_value(param)
                    proposed = max(current - 1, 1)  # Reduce step size
                    
                    causation_event_id = self._find_recent_event('neural', 'neural_curriculum_adjustment')
                    
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Curriculum sequence length oscillating (variance={seq_variance:.1f} > 100) - reducing step size to {proposed} for stability",
                        confidence=0.7,
                        trigger_metrics={
                            'sequence_variance': float(seq_variance),
                            'recent_avg_length': float(recent_avg),
                            'older_avg_length': float(older_avg),
                            'stability_threshold': 100.0
                        },
                        causation_event_id=causation_event_id,
                        expected_impact="Should stabilize curriculum adjustments and prevent oscillation"
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

    # === CROSS-SYSTEM CORRELATION ANALYSIS METHODS (Integration: Neural-ML-Alliance) ===
    
    def _analyze_quantum_language_correlation(self, 
                                              quantum_metrics: Dict[str, Any],
                                              ml_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze correlation between quantum state coherence and language generation quality.
        
        When quantum entropy is high, language generation tends to be more creative but
        less coherent. When entropy is low, language is more structured but potentially
        repetitive. Find the optimal balance.
        """
        if not quantum_metrics or not ml_metrics:
            return None
            
        # Get quantum entropy from metrics
        quantum_entropy = quantum_metrics.get('entropy', 0.5)
        
        # Get language quality from ML metrics (if available)
        language_quality = ml_metrics.get('language_quality', {})
        coherence = language_quality.get('coherence', 0.5)
        creativity = language_quality.get('creativity', 0.5)
        
        # Detect imbalance: high entropy + low coherence = too chaotic
        if quantum_entropy > 0.7 and coherence < 0.3:
            param = 'quantum.entanglement_sensitivity'
            current = self._get_param_value(param)
            proposed = max(current - self.step_sizes[param], self.param_bounds[param][0])
            
            if proposed < current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"High quantum entropy ({quantum_entropy:.2f}) + low coherence ({coherence:.2f}) - reducing sensitivity for more stable language",
                    confidence=0.65,
                    trigger_metrics={
                        'quantum_entropy': float(quantum_entropy),
                        'language_coherence': float(coherence),
                        'language_creativity': float(creativity)
                    },
                    causation_event_id=self._find_recent_event('quantum_substrate', 'entropy_calculated'),
                    expected_impact="Should improve language coherence by reducing quantum chaos influence"
                )
        
        # Detect imbalance: low entropy + low creativity = too rigid
        if quantum_entropy < 0.3 and creativity < 0.3:
            param = 'quantum.entanglement_sensitivity'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Low quantum entropy ({quantum_entropy:.2f}) + low creativity ({creativity:.2f}) - increasing sensitivity for more varied language",
                    confidence=0.6,
                    trigger_metrics={
                        'quantum_entropy': float(quantum_entropy),
                        'language_coherence': float(coherence),
                        'language_creativity': float(creativity)
                    },
                    causation_event_id=self._find_recent_event('quantum_substrate', 'entropy_calculated'),
                    expected_impact="Should improve language creativity by allowing more quantum influence"
                )
        
        return None
    
    def _analyze_network_alliance_correlation(self, 
                                               network_metrics: Dict[str, Any],
                                               alliance_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze correlation between network topology and alliance formation success.
        
        Networks with high clustering coefficients tend to form stronger alliances.
        Networks with low density may need connection incentives.
        """
        if not network_metrics:
            return None
            
        # Get network topology metrics
        clustering_coef = network_metrics.get('clustering_coefficient', 0.5)
        network_density = network_metrics.get('density', 0.5)
        
        # Get alliance metrics (if available)
        alliance_metrics = alliance_metrics or {}
        alliance_count = alliance_metrics.get('active_alliances', 0)
        avg_alliance_size = alliance_metrics.get('avg_size', 0)
        formation_rate = alliance_metrics.get('formation_rate', 0)
        
        # Low clustering + low alliance formation = need more edge creation
        if clustering_coef < 0.3 and formation_rate < 0.1:
            param = 'feedback.knobs.new_edge_rate.initial'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Low clustering ({clustering_coef:.2f}) + low alliance formation ({formation_rate:.2f}) - increasing edge rate to promote social structure",
                    confidence=0.6,
                    trigger_metrics={
                        'clustering_coefficient': float(clustering_coef),
                        'network_density': float(network_density),
                        'alliance_formation_rate': float(formation_rate),
                        'active_alliances': int(alliance_count)
                    },
                    causation_event_id=self._find_recent_event('network', 'topology_updated'),
                    expected_impact="Should improve alliance formation by creating more connection opportunities"
                )
        
        # High density but few alliances = organisms are connected but not cooperating
        if network_density > 0.6 and alliance_count < 3:
            param = 'feedback.knobs.clustering_bias.initial'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"High network density ({network_density:.2f}) but few alliances ({alliance_count}) - increasing clustering bias to encourage local cooperation",
                    confidence=0.55,
                    trigger_metrics={
                        'clustering_coefficient': float(clustering_coef),
                        'network_density': float(network_density),
                        'active_alliances': int(alliance_count),
                        'avg_alliance_size': float(avg_alliance_size)
                    },
                    causation_event_id=self._find_recent_event('alliance_warfare', 'alliance_formed'),
                    expected_impact="Should promote alliance formation among already-connected organisms"
                )
        
        return None
    
    def _analyze_neural_battle_correlation(self, 
                                           neural_metrics: Dict[str, Any],
                                           battle_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze correlation between neural learning and battle success.
        
        Organisms that learn well should perform better in battles.
        If battle success doesn't correlate with learning, adjust rewards.
        """
        if not neural_metrics or not battle_metrics:
            return None
            
        # Get neural training metrics
        avg_loss = neural_metrics.get('avg_loss', 1.0)
        learning_rate_effective = neural_metrics.get('effective_lr', 0.001)
        
        # Get battle metrics
        avg_win_rate = battle_metrics.get('avg_win_rate', 0.5)
        battle_count = battle_metrics.get('total_battles', 0)
        
        if battle_count < 10:
            return None  # Not enough data
        
        # Low loss (good learning) but low win rate = reward signal may be wrong
        if avg_loss < 0.3 and avg_win_rate < 0.3:
            param = 'neural.rewards.fitness_improvement'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Good learning (loss={avg_loss:.3f}) but poor battle performance ({avg_win_rate:.1%}) - increasing fitness reward to better align learning with survival",
                    confidence=0.7,
                    trigger_metrics={
                        'avg_loss': float(avg_loss),
                        'avg_win_rate': float(avg_win_rate),
                        'total_battles': int(battle_count)
                    },
                    causation_event_id=self._find_recent_event('neural', 'training_step'),
                    expected_impact="Should improve correlation between neural learning and battle success"
                )
        
        # High loss (poor learning) but high win rate = may be over-relying on fitness
        if avg_loss > 0.7 and avg_win_rate > 0.7:
            param = 'neural.training.learning_rate'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Poor learning (loss={avg_loss:.3f}) but high win rate ({avg_win_rate:.1%}) - increasing learning rate so neural decisions matter more",
                    confidence=0.6,
                    trigger_metrics={
                        'avg_loss': float(avg_loss),
                        'avg_win_rate': float(avg_win_rate),
                        'total_battles': int(battle_count)
                    },
                    causation_event_id=self._find_recent_event('neural', 'training_step'),
                    expected_impact="Should make neural decisions more relevant to battle outcomes"
                )
        
        return None
    
    def _analyze_vocabulary_fitness_correlation(self, 
                                                 language_metrics: Dict[str, Any],
                                                 evolution_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze correlation between vocabulary richness and organism fitness.
        
        Organisms with larger vocabularies should have fitness advantages
        if language is contributing to survival. If not, adjust language rewards.
        """
        if not language_metrics or not evolution_metrics:
            return None
            
        # Get language metrics
        avg_vocab_size = language_metrics.get('avg_vocabulary_size', 0)
        vocab_diversity = language_metrics.get('vocabulary_diversity', 0)
        
        # Get fitness metrics
        avg_fitness = evolution_metrics.get('avg_fitness', 0.5)
        fitness_variance = evolution_metrics.get('fitness_variance', 0.1)
        
        # Calculate if vocabulary correlates with fitness (simplified heuristic)
        vocab_fitness_alignment = language_metrics.get('vocab_fitness_correlation', None)
        
        # If we have explicit correlation data
        if vocab_fitness_alignment is not None:
            if vocab_fitness_alignment < 0.2:
                # Low correlation - language isn't helping fitness
                param = 'neural.training.language_reward_scaling'
                current = self._get_param_value(param)
                proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
                
                if proposed > current:
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Low vocab-fitness correlation ({vocab_fitness_alignment:.2f}) - increasing language reward to make vocabulary matter more",
                        confidence=0.65,
                        trigger_metrics={
                            'vocab_fitness_correlation': float(vocab_fitness_alignment),
                            'avg_vocab_size': float(avg_vocab_size),
                            'avg_fitness': float(avg_fitness)
                        },
                        causation_event_id=self._find_recent_event('language', 'generation_evaluated'),
                        expected_impact="Should increase fitness benefits for organisms with rich vocabularies"
                    )
        
        # Heuristic: high vocab diversity but low average fitness = language costs too much
        if vocab_diversity > 0.7 and avg_fitness < 0.3:
            param = 'neural.rewards.survival'
            current = self._get_param_value(param)
            proposed = min(current + self.step_sizes[param], self.param_bounds[param][1])
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"High vocabulary diversity ({vocab_diversity:.2f}) but low fitness ({avg_fitness:.2f}) - increasing survival reward to balance language investment",
                    confidence=0.55,
                    trigger_metrics={
                        'vocabulary_diversity': float(vocab_diversity),
                        'avg_vocab_size': float(avg_vocab_size),
                        'avg_fitness': float(avg_fitness),
                        'fitness_variance': float(fitness_variance)
                    },
                    causation_event_id=self._find_recent_event('evolution', 'fitness_evaluated'),
                    expected_impact="Should help organisms survive while developing language capabilities"
                )
        
        return None

    def _analyze_language_game_correlation(self,
                                            language_game_metrics: Dict[str, Any],
                                            battle_metrics: Dict[str, Any]) -> Optional[TuningAction]:
        """
        Analyze correlation between Language-Game Bridge performance and battle/game outcomes.
        
        ⭐ NEW - 5th Cross-System Correlation Analyzer
        
        The Language-Game Bridge connects vocabulary concepts to gameplay decisions.
        This analyzer ensures the correlation is productive:
        - High vocabulary-game alignment + high win rate = working well
        - High alignment + low win rate = language misleading decisions
        - Low alignment + high win rate = language not contributing (unused)
        - Low alignment + low win rate = both systems struggling
        
        Also uses HISTORY TRENDS to detect:
        - Declining alignment = vocabulary losing relevance
        - Declining influence = language being ignored
        """
        if not language_game_metrics:
            return None
        
        # Get Language-Game Bridge metrics
        vocab_game_alignment = language_game_metrics.get('vocabulary_game_alignment', 0.0)
        lang_decision_influence = language_game_metrics.get('language_decision_influence', 0.0)
        concept_diversity = language_game_metrics.get('concept_diversity', 0.0)
        episodes_tracked = language_game_metrics.get('episodes_tracked', 0)
        
        if episodes_tracked < 20:
            return None  # Need more data
        
        # Get battle/game outcomes
        battle_metrics = battle_metrics or {}
        avg_win_rate = battle_metrics.get('avg_win_rate', 
                       language_game_metrics.get('win_rate', 0.5))
        
        # ⭐ NEW: Analyze TRENDS from history arrays
        alignment_trend = self._compute_trend(getattr(self, 'vocab_game_alignment_history', []))
        influence_trend = self._compute_trend(getattr(self, 'lang_decision_influence_history', []))
        
        # Case 0: DECLINING alignment trend = vocabulary losing relevance to games
        # Solution: Increase learning rate to re-learn what matters
        if alignment_trend < -0.1 and len(getattr(self, 'vocab_game_alignment_history', [])) >= 10:
            param = 'neural.language_game_bridge.learning_rate'
            current = self._get_param_value(param) or 0.1
            proposed = min(current + 0.03, 0.3)
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Vocabulary-game alignment DECLINING (trend={alignment_trend:.3f}) - concepts losing relevance. Boosting learning rate to re-adapt.",
                    confidence=0.75,
                    trigger_metrics={
                        'alignment_trend': float(alignment_trend),
                        'current_alignment': float(vocab_game_alignment),
                        'history_length': len(self.vocab_game_alignment_history)
                    },
                    causation_event_id=self._find_recent_event('language_game_bridge', 'correlation_update'),
                    expected_impact="Should help vocabulary re-learn from current game patterns"
                )
        
        # Case 0b: DECLINING influence trend = language being ignored
        # Solution: Increase bias strength to make vocabulary more impactful
        if influence_trend < -0.05 and len(getattr(self, 'lang_decision_influence_history', [])) >= 10:
            param = 'neural.language_game_bridge.bias_strength'
            current = self._get_param_value(param) or 0.3
            proposed = min(current + 0.05, 0.6)
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Language decision influence DECLINING (trend={influence_trend:.3f}) - vocabulary being ignored. Increasing bias strength.",
                    confidence=0.65,
                    trigger_metrics={
                        'influence_trend': float(influence_trend),
                        'current_influence': float(lang_decision_influence),
                        'history_length': len(self.lang_decision_influence_history)
                    },
                    causation_event_id=self._find_recent_event('language_game_bridge', 'bias_event'),
                    expected_impact="Should increase vocabulary's weight in decision-making"
                )
        
        # Case 1: High alignment but LOW win rate = vocabulary is MISLEADING decisions
        # Solution: Reduce bias strength so neural network has more control
        if vocab_game_alignment > 0.3 and avg_win_rate < 0.3:
            param = 'neural.language_game_bridge.bias_strength'
            current = self._get_param_value(param) or 0.3
            proposed = max(current - 0.05, 0.05)  # Reduce bias
            
            if proposed < current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"High vocab-game alignment ({vocab_game_alignment:.2f}) but low win rate ({avg_win_rate:.1%}) - vocabulary may be MISLEADING decisions. Reducing bias strength.",
                    confidence=0.7,
                    trigger_metrics={
                        'vocabulary_game_alignment': float(vocab_game_alignment),
                        'avg_win_rate': float(avg_win_rate),
                        'language_decision_influence': float(lang_decision_influence),
                        'concept_diversity': float(concept_diversity)
                    },
                    causation_event_id=self._find_recent_event('language_game_bridge', 'correlation_update'),
                    expected_impact="Should reduce vocabulary's negative influence on game decisions"
                )
        
        # Case 2: LOW alignment but high win rate = vocabulary NOT contributing
        # Solution: Increase bias strength to get language involved
        if vocab_game_alignment < -0.1 and avg_win_rate > 0.6:
            param = 'neural.language_game_bridge.bias_strength'
            current = self._get_param_value(param) or 0.3
            proposed = min(current + 0.05, 0.5)  # Increase bias
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Low vocab-game alignment ({vocab_game_alignment:.2f}) but high win rate ({avg_win_rate:.1%}) - vocabulary is UNUSED. Increasing bias to integrate language.",
                    confidence=0.6,
                    trigger_metrics={
                        'vocabulary_game_alignment': float(vocab_game_alignment),
                        'avg_win_rate': float(avg_win_rate),
                        'language_decision_influence': float(lang_decision_influence)
                    },
                    causation_event_id=self._find_recent_event('language_game_bridge', 'correlation_update'),
                    expected_impact="Should increase vocabulary's contribution to decision-making"
                )
        
        # Case 3: Low concept diversity = vocabulary too narrow
        # Solution: Increase learning rate to acquire new concepts faster
        if concept_diversity < 0.2 and episodes_tracked > 50:
            param = 'neural.language_game_bridge.learning_rate'
            current = self._get_param_value(param) or 0.1
            proposed = min(current + 0.02, 0.3)
            
            if proposed > current:
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Low concept diversity ({concept_diversity:.2f}) after {episodes_tracked} episodes - vocabulary too narrow. Increasing learning rate.",
                    confidence=0.55,
                    trigger_metrics={
                        'concept_diversity': float(concept_diversity),
                        'episodes_tracked': int(episodes_tracked),
                        'vocabulary_game_alignment': float(vocab_game_alignment)
                    },
                    causation_event_id=self._find_recent_event('language_game_bridge', 'learning_event'),
                    expected_impact="Should accelerate vocabulary expansion from game experiences"
                )
        
        # Case 4: Both working well (positive alignment + high win rate)
        if vocab_game_alignment > 0.2 and avg_win_rate > 0.5:
            # Optimal state - language and games are synergizing
            pass  # Log only in debug
        
        return None

    def _get_param_value(self, path: str) -> float:
        """Get current value of a config parameter by path"""
        parts = path.split('.')
        value = self.config
        for part in parts:
            if value is None or not isinstance(value, dict):
                return 0.0
            value = value.get(part, {})
        return float(value) if isinstance(value, (int, float)) else 0.0
    
    def _compute_trend(self, history: List[float], window: int = 10) -> float:
        """
        Compute trend (slope) of a history array using linear regression.
        
        Returns:
            Positive = increasing trend
            Negative = decreasing trend
            Near zero = stable
            
        Uses last `window` samples for trend calculation.
        """
        if len(history) < 3:
            return 0.0
        
        # Use last N samples
        samples = history[-window:] if len(history) > window else history
        n = len(samples)
        
        # Simple linear regression slope: (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        sum_x = sum(range(n))  # 0 + 1 + ... + (n-1)
        sum_y = sum(samples)
        sum_xy = sum(i * y for i, y in enumerate(samples))
        sum_x2 = sum(i * i for i in range(n))
        
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
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
        
        For language_game_bridge parameters, also propagates changes to the
        running LanguageGameBridge via update_parameters().
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

        # Propagate language_game_bridge changes to running bridge
        if 'language_game_bridge' in action.parameter_path:
            self._propagate_bridge_parameter(action.parameter_path, action.proposed_value)

        return True

    def _propagate_bridge_parameter(self, parameter_path: str, new_value: float) -> None:
        """
        Propagate a language_game_bridge parameter change to the running bridge.
        
        This ensures ConfigTuner changes actually affect organism behavior.
        """
        if not self._highlander_protocol:
            logger.debug("[CONFIG_TUNER] No HighlanderProtocol wired - cannot propagate bridge change")
            return
            
        bridge = getattr(self._highlander_protocol, 'language_bridge', None)
        if not bridge:
            logger.debug("[CONFIG_TUNER] HighlanderProtocol has no language_bridge - cannot propagate")
            return
            
        # Check if bridge has update_parameters method
        if not hasattr(bridge, 'update_parameters'):
            logger.warning("[CONFIG_TUNER] LanguageGameBridge missing update_parameters method")
            return
        
        # Determine which parameter changed
        if 'bias_strength' in parameter_path:
            changes = bridge.update_parameters(bias_strength=new_value)
            logger.info(f"[CONFIG_TUNER] 🔗 Propagated bias_strength to bridge: {changes}")
        elif 'learning_rate' in parameter_path:
            changes = bridge.update_parameters(learning_rate=new_value)
            logger.info(f"[CONFIG_TUNER] 🔗 Propagated learning_rate to bridge: {changes}")

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
