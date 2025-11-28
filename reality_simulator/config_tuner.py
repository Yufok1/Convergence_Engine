"""
ConfigTuner - Self-Tuning Configuration System

Interprets ML insights and neural metrics to autonomously adjust
configuration parameters for optimal system performance.

The butterfly learns to tune itself based on population-level patterns.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TuningAction:
    """A proposed configuration change"""
    parameter_path: str  # e.g., "evolution.mutation_rate.initial"
    current_value: float
    proposed_value: float
    reason: str
    confidence: float  # 0-1, how confident we are this will help
    timestamp: float = field(default_factory=time.time)


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

        # Tuning constraints (safety bounds)
        self.param_bounds = {
            'evolution.mutation_rate.initial': (0.001, 0.15),
            'feedback.knobs.mutation_rate.initial': (0.002, 0.06),
            'feedback.knobs.new_edge_rate.initial': (0.2, 6.0),
            'feedback.knobs.clustering_bias.initial': (0.3, 1.6),
            'evolution.diversity_guard.penalty': (0.01, 0.2),
            'evolution.diversity_guard.frequency_threshold': (0.05, 0.3),
        }

        # Tuning aggressiveness (how much to change per adjustment)
        self.step_sizes = {
            'evolution.mutation_rate.initial': 0.005,
            'feedback.knobs.mutation_rate.initial': 0.002,
            'feedback.knobs.new_edge_rate.initial': 0.2,
            'feedback.knobs.clustering_bias.initial': 0.05,
            'evolution.diversity_guard.penalty': 0.01,
            'evolution.diversity_guard.frequency_threshold': 0.02,
        }

        # History tracking
        self.tuning_history: List[TuningHistory] = []
        self.last_tuning_time = 0
        self.tuning_interval = 50  # Frames between tuning actions

        # Performance tracking
        self.fitness_history: List[float] = []
        self.cluster_count_history: List[int] = []
        self.anomaly_ratio_history: List[float] = []

        # Meta-learning: track which actions work
        self.action_success_rates: Dict[str, Tuple[int, int]] = {}  # param -> (successes, total)

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

        # Analyze different aspects
        actions = []

        # 1. Cluster diversity analysis
        cluster_action = self._analyze_cluster_diversity(ml_metrics, evolution_metrics)
        if cluster_action:
            actions.append(cluster_action)

        # 2. Anomaly analysis
        anomaly_action = self._analyze_anomalies(ml_metrics)
        if anomaly_action:
            actions.append(anomaly_action)

        # 3. Fitness stagnation analysis
        fitness_action = self._analyze_fitness_trends(evolution_metrics)
        if fitness_action:
            actions.append(fitness_action)

        # 4. Neural learning analysis
        neural_action = self._analyze_neural_learning(neural_metrics)
        if neural_action:
            actions.append(neural_action)

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

                logger.info(f"[CONFIG_TUNER] Proposing: {best_action.parameter_path} "
                          f"{best_action.current_value:.4f} → {best_action.proposed_value:.4f} "
                          f"(confidence: {best_action.confidence:.2f}) | {best_action.reason}")

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
                    history.success = history.fitness_after > history.fitness_before

                    # Update success rates
                    param = history.action.parameter_path
                    if param not in self.action_success_rates:
                        self.action_success_rates[param] = (0, 0)

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
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"Low cluster diversity ({avg_clusters:.1f} clusters) - increasing mutation for variety",
                        confidence=0.8
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
                    return TuningAction(
                        parameter_path=param,
                        current_value=current,
                        proposed_value=proposed,
                        reason=f"High anomaly ratio ({avg_ratio:.2f}) - strengthening diversity guard",
                        confidence=0.75
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
                return TuningAction(
                    parameter_path=param,
                    current_value=current,
                    proposed_value=proposed,
                    reason=f"Fitness stagnating (std={std_dev:.4f}) - increasing network connectivity",
                    confidence=0.7
                )

        return None

    def _analyze_neural_learning(self, neural_metrics) -> Optional[TuningAction]:
        """Analyze neural training and suggest adjustments if learning is poor"""
        if not neural_metrics or not neural_metrics.get('enabled'):
            return None

        # Could add: if training loss not decreasing, adjust learning rate
        # For now, placeholder
        return None

    def _get_param_value(self, path: str) -> float:
        """Get current value of a config parameter by path"""
        parts = path.split('.')
        value = self.config
        for part in parts:
            value = value.get(part, {})
        return float(value) if isinstance(value, (int, float)) else 0.0

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

    def get_stats(self) -> Dict[str, Any]:
        """Get tuning statistics"""
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
                    'success': h.success
                }
                for h in self.tuning_history[-5:]
            ]
        }
