"""
🦋 THE ANTENNAE - Collective Sensing Apparatus

Each butterfly feels a part. Together they sense the whole.

The Antennae is NOT a separate intelligence - it IS the organisms,
aggregated. High-fitness butterflies contribute more to what's sensed.
The governance emerges FROM perception, not imposed upon it.

Occam's Razor Design:
    - Heuristic rules (prior beliefs)
    - Sklearn regression (converges to truth via Kleene iteration)
    - No neural nets needed for 6 parameters

Usage:
    antennae = Antennae()
    antennae.sense(organisms, report)  # Update perception
    signal = antennae.get_signal()     # What the collective feels
    antennae.influence(config_tuner)   # Let perception guide tuning
"""

import time
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import deque
import statistics

# Scikit-learn for Kleene-style convergence (optional)
try:
    from sklearn.linear_model import SGDRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class AntennaReading:
    """What the Antennae perceives at a moment in time."""
    timestamp: float = 0.0
    
    # Population feel
    population_pressure: float = 0.0      # -1 (dying) to +1 (thriving)
    fitness_momentum: float = 0.0         # -1 (declining) to +1 (improving)
    diversity_sense: float = 0.0          # 0 (monoculture) to 1 (diverse)
    
    # Learning feel
    exploration_level: float = 0.0        # 0 (exploiting) to 1 (exploring)
    learning_rate_feel: float = 0.0       # -1 (stagnant) to +1 (rapid learning)
    
    # Social feel
    alliance_cohesion: float = 0.0        # 0 (fragmented) to 1 (unified)
    conflict_intensity: float = 0.0       # 0 (peaceful) to 1 (war)
    
    # Resource feel
    resource_abundance: float = 0.0       # 0 (scarce) to 1 (abundant)
    
    # Aggregate
    overall_health: float = 0.0           # -1 (crisis) to +1 (flourishing)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'population_pressure': self.population_pressure,
            'fitness_momentum': self.fitness_momentum,
            'diversity_sense': self.diversity_sense,
            'exploration_level': self.exploration_level,
            'learning_rate_feel': self.learning_rate_feel,
            'alliance_cohesion': self.alliance_cohesion,
            'conflict_intensity': self.conflict_intensity,
            'resource_abundance': self.resource_abundance,
            'overall_health': self.overall_health
        }


@dataclass
class GovernanceSignal:
    """What the Antennae suggests for system tuning."""
    # Range: -1 (decrease) to +1 (increase) for each parameter
    survival_threshold_delta: float = 0.0
    competition_intensity_delta: float = 0.0
    learning_rate_delta: float = 0.0
    exploration_delta: float = 0.0
    germination_rate_delta: float = 0.0
    cooperation_bonus_delta: float = 0.0
    
    confidence: float = 0.0  # How confident the signal is (0-1)
    source: str = "heuristic"  # "heuristic" or "learned"
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'survival_threshold': self.survival_threshold_delta,
            'competition_intensity': self.competition_intensity_delta,
            'learning_rate': self.learning_rate_delta,
            'exploration': self.exploration_delta,
            'germination_rate': self.germination_rate_delta,
            'cooperation_bonus': self.cooperation_bonus_delta,
            'confidence': self.confidence,
            'source': self.source
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BELIEFS - Simple causal beliefs that converge via experience
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Belief:
    """A causal belief: 'if X then Y' with confidence from evidence."""
    cause: str           # e.g., "survival_threshold_down"
    effect: str          # e.g., "population_up"
    confidence: float    # 0-1, grows with confirming evidence
    confirmations: int   # Times we've seen this work
    refutations: int     # Times it failed
    
    def update(self, confirmed: bool):
        """Update belief based on observed outcome."""
        if confirmed:
            self.confirmations += 1
        else:
            self.refutations += 1
        # Bayesian-ish update
        total = self.confirmations + self.refutations
        self.confidence = self.confirmations / max(total, 1)


class BeliefSystem:
    """
    Antennae's understanding of cause→effect relationships.
    
    Converges to truth via Kleene-style iteration:
    Start with prior beliefs → observe outcomes → update → repeat
    """
    
    def __init__(self):
        # Prior beliefs (our heuristics, now as explicit beliefs)
        self.beliefs: Dict[str, Belief] = {
            # Population management
            'survival_down_pop_up': Belief(
                cause='survival_threshold_decrease',
                effect='population_increase',
                confidence=0.7,
                confirmations=7, refutations=3
            ),
            'survival_up_quality_up': Belief(
                cause='survival_threshold_increase', 
                effect='fitness_increase',
                confidence=0.6,
                confirmations=6, refutations=4
            ),
            # Diversity management
            'competition_down_diversity_up': Belief(
                cause='competition_decrease',
                effect='diversity_increase',
                confidence=0.6,
                confirmations=6, refutations=4
            ),
            # Cooperation
            'cooperation_up_cohesion_up': Belief(
                cause='cooperation_bonus_increase',
                effect='alliance_cohesion_increase',
                confidence=0.65,
                confirmations=7, refutations=4
            ),
            # Exploration
            'exploration_up_diversity_up': Belief(
                cause='exploration_increase',
                effect='diversity_increase',
                confidence=0.5,
                confirmations=5, refutations=5
            ),
        }
    
    def get_confidence(self, cause: str) -> float:
        """Get confidence in a causal relationship."""
        for belief in self.beliefs.values():
            if belief.cause == cause:
                return belief.confidence
        return 0.5  # Unknown = 50/50
    
    def update_from_outcome(self, action: str, expected_effect: str, 
                           actual_change: float, threshold: float = 0.05):
        """
        Update beliefs based on observed outcome.
        
        Args:
            action: What we did (e.g., 'survival_threshold_decrease')
            expected_effect: What we expected (e.g., 'population_increase')
            actual_change: Actual change in the metric
            threshold: Minimum change to count as confirmation
        """
        for belief in self.beliefs.values():
            if belief.cause == action and belief.effect == expected_effect:
                # Did the expected effect happen?
                if 'increase' in expected_effect:
                    confirmed = actual_change > threshold
                else:
                    confirmed = actual_change < -threshold
                belief.update(confirmed)
                break
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize beliefs."""
        return {
            name: {
                'cause': b.cause,
                'effect': b.effect,
                'confidence': b.confidence,
                'evidence': f"{b.confirmations}✓ {b.refutations}✗"
            }
            for name, b in self.beliefs.items()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH PREDICTOR - Sklearn regression (Kleene convergence)
# ═══════════════════════════════════════════════════════════════════════════════

class HealthPredictor:
    """
    Learns what parameters lead to health via gradient descent.
    
    This IS Kleene iteration: f(x) → f(f(x)) → ... → fixed point
    Each training step moves closer to the true parameter→health mapping.
    """
    
    def __init__(self):
        if not SKLEARN_AVAILABLE:
            self.model = None
            return
            
        self.model = SGDRegressor(
            loss='huber',
            penalty='l2',
            alpha=0.001,
            learning_rate='adaptive',
            eta0=0.01,
            warm_start=True
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        self.feature_names = [
            'survival_threshold', 'competition_intensity',
            'germination_rate', 'cooperation_bonus'
        ]
        self.feature_importance: Dict[str, float] = {}
        
        self.X_buffer: List[np.ndarray] = []
        self.y_buffer: List[float] = []
        self.buffer_size = 100
        self.training_steps = 0
    
    def add_sample(self, params: Dict[str, float], health: float):
        """Record (parameters, health) observation."""
        if self.model is None:
            return
            
        features = np.array([
            params.get('survival_threshold', 0.3),
            params.get('competition_intensity', 0.5),
            params.get('germination_rate', 0.1),
            params.get('cooperation_bonus', 0.2)
        ])
        
        self.X_buffer.append(features)
        self.y_buffer.append(health)
        
        if len(self.X_buffer) > self.buffer_size:
            self.X_buffer = self.X_buffer[-self.buffer_size:]
            self.y_buffer = self.y_buffer[-self.buffer_size:]
    
    def train(self) -> bool:
        """One Kleene iteration toward the fixed point."""
        if self.model is None or len(self.X_buffer) < 10:
            return False
        
        X = np.array(self.X_buffer)
        y = np.array(self.y_buffer)
        
        if not self.is_fitted:
            self.scaler.fit(X)
            self.is_fitted = True
        
        X_scaled = self.scaler.transform(X)
        self.model.partial_fit(X_scaled, y)
        self.training_steps += 1
        
        # Extract what we've learned
        if hasattr(self.model, 'coef_'):
            coefs = self.model.coef_
            for i, name in enumerate(self.feature_names):
                self.feature_importance[name] = float(coefs[i])
        
        return True
    
    def suggest(self, current_params: Dict[str, float]) -> Dict[str, float]:
        """
        What does the learned model suggest?
        
        Returns parameter deltas based on learned gradients.
        """
        if not self.is_fitted or self.training_steps < 10:
            return {}
        
        if not hasattr(self.model, 'coef_'):
            return {}
        
        suggestions = {}
        coefs = self.model.coef_
        
        for i, name in enumerate(self.feature_names):
            # Positive coef → increasing this param increases health
            delta = float(coefs[i]) * 0.05  # Conservative
            delta = max(-0.1, min(0.1, delta))
            if abs(delta) > 0.01:
                suggestions[name] = delta
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'training_steps': self.training_steps,
            'is_fitted': self.is_fitted,
            'feature_importance': self.feature_importance,
            'samples': len(self.X_buffer)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# THE ANTENNAE - Clean and simple
# ═══════════════════════════════════════════════════════════════════════════════

class Antennae:
    """
    🦋 The Collective Sensing Apparatus
    
    Aggregates organism states → generates governance signals.
    
    Two sources of wisdom:
    1. Beliefs (heuristics that update with evidence)
    2. HealthPredictor (sklearn regression, Kleene convergence)
    """
    
    def __init__(self, history_size: int = 100):
        self.history: deque = deque(maxlen=history_size)
        self.current_reading: Optional[AntennaReading] = None
        self.last_signal: Optional[GovernanceSignal] = None
        
        self._fitness_history: deque = deque(maxlen=50)
        self._population_history: deque = deque(maxlen=50)
        
        self.sensitivity = 1.0
        self.signal_cooldown = 5.0
        self._last_signal_time = 0.0
        
        # Belief system (heuristics that learn)
        self.beliefs = BeliefSystem()
        
        # Health predictor (Kleene convergence)
        self.predictor = HealthPredictor() if SKLEARN_AVAILABLE else None
        
        # For tracking outcomes
        self._last_reading: Optional[AntennaReading] = None
        self._last_action: Optional[str] = None
        
        print("[ANTENNAE] 🦋 Initialized (Occam's Razor edition)")
        if SKLEARN_AVAILABLE:
            print("[ANTENNAE] 📊 HealthPredictor ready (Kleene convergence)")
    
    def sense(self, organisms: Dict[str, Any], report: Any = None) -> AntennaReading:
        """Sense the collective state of all organisms."""
        reading = AntennaReading(timestamp=time.time())
        
        if not organisms:
            reading.population_pressure = -1.0
            reading.overall_health = -1.0
            self.current_reading = reading
            self.history.append(reading)
            return reading
        
        # Gather organism data
        fitnesses = []
        epsilons = []
        
        for org in organisms.values():
            if hasattr(org, 'fitness'):
                fitnesses.append(org.fitness)
            if hasattr(org, 'epsilon'):
                epsilons.append(org.epsilon)
        
        # Population pressure
        pop_count = len(organisms)
        self._population_history.append(pop_count)
        
        if len(self._population_history) >= 3:
            recent = list(self._population_history)[-10:]
            if recent[-1] > recent[0]:
                reading.population_pressure = min(1.0, (recent[-1] - recent[0]) / max(recent[0], 1) * 2)
            else:
                reading.population_pressure = max(-1.0, (recent[-1] - recent[0]) / max(recent[0], 1) * 2)
        
        # Fitness momentum
        if fitnesses:
            avg_fitness = statistics.mean(fitnesses)
            self._fitness_history.append(avg_fitness)
            
            if len(self._fitness_history) >= 3:
                recent = list(self._fitness_history)[-10:]
                momentum = recent[-1] - recent[0]
                reading.fitness_momentum = max(-1.0, min(1.0, momentum * 5))
        
        # Diversity
        if len(fitnesses) > 1:
            fitness_std = statistics.stdev(fitnesses)
            reading.diversity_sense = min(1.0, fitness_std * 3)
        
        # Exploration
        if epsilons:
            reading.exploration_level = statistics.mean(epsilons)
        
        reading.learning_rate_feel = reading.fitness_momentum
        
        # From report
        if report and hasattr(report, 'alliances'):
            alliances = report.alliances
            if hasattr(alliances, 'total_members') and pop_count > 0:
                reading.alliance_cohesion = min(1.0, alliances.total_members / pop_count)
            if hasattr(alliances, 'wars_in_progress'):
                reading.conflict_intensity = min(1.0, alliances.wars_in_progress * 0.2)
        
        if report and hasattr(report, 'resources'):
            resources = report.resources
            if hasattr(resources, 'gpu_memory_total_mb') and resources.gpu_memory_total_mb > 0:
                usage = resources.gpu_memory_used_mb / resources.gpu_memory_total_mb
                reading.resource_abundance = 1.0 - usage
        
        # Overall health
        reading.overall_health = (
            reading.population_pressure * 0.25 +
            reading.fitness_momentum * 0.25 +
            reading.diversity_sense * 0.15 +
            (1.0 - reading.conflict_intensity) * 0.1 +
            reading.alliance_cohesion * 0.1 +
            reading.resource_abundance * 0.15
        )
        
        # Update predictor with observation
        if self._last_reading and self.predictor:
            health_change = reading.overall_health - self._last_reading.overall_health
            if self._last_action:
                # Update beliefs based on what happened
                self._update_beliefs(self._last_action, self._last_reading, reading)
        
        self._last_reading = reading
        self.current_reading = reading
        self.history.append(reading)
        
        return reading
    
    def _update_beliefs(self, action: str, before: AntennaReading, after: AntennaReading):
        """Update beliefs based on observed outcome."""
        pop_change = after.population_pressure - before.population_pressure
        fitness_change = after.fitness_momentum - before.fitness_momentum
        diversity_change = after.diversity_sense - before.diversity_sense
        cohesion_change = after.alliance_cohesion - before.alliance_cohesion
        
        if 'survival_threshold' in action:
            if 'decrease' in action:
                self.beliefs.update_from_outcome(action, 'population_increase', pop_change)
            else:
                self.beliefs.update_from_outcome(action, 'fitness_increase', fitness_change)
        
        if 'competition' in action and 'decrease' in action:
            self.beliefs.update_from_outcome(action, 'diversity_increase', diversity_change)
        
        if 'cooperation' in action and 'increase' in action:
            self.beliefs.update_from_outcome(action, 'alliance_cohesion_increase', cohesion_change)
    
    def get_signal(self) -> GovernanceSignal:
        """Generate governance signal from heuristics + learned knowledge."""
        if not self.current_reading:
            return GovernanceSignal(confidence=0.0)
        
        r = self.current_reading
        signal = GovernanceSignal()
        
        # ═══════════════════════════════════════════════════════════════════
        # HEURISTIC RULES (weighted by belief confidence)
        # ═══════════════════════════════════════════════════════════════════
        
        # Population management
        if r.population_pressure < -0.3:
            conf = self.beliefs.get_confidence('survival_threshold_decrease')
            signal.survival_threshold_delta = -0.3 * self.sensitivity * conf
            signal.germination_rate_delta = 0.3 * self.sensitivity * conf
        elif r.population_pressure > 0.5:
            conf = self.beliefs.get_confidence('survival_threshold_increase')
            signal.survival_threshold_delta = 0.1 * self.sensitivity * conf
        
        # Diversity management
        if r.diversity_sense < 0.2:
            conf = self.beliefs.get_confidence('competition_decrease')
            signal.competition_intensity_delta = -0.2 * self.sensitivity * conf
            signal.cooperation_bonus_delta = 0.2 * self.sensitivity * conf
        
        # Exploration
        if abs(r.fitness_momentum) < 0.1 and r.exploration_level < 0.5:
            conf = self.beliefs.get_confidence('exploration_increase')
            signal.exploration_delta = 0.2 * self.sensitivity * conf
        elif r.fitness_momentum > 0.3:
            signal.exploration_delta = -0.1 * self.sensitivity
        
        # Cooperation
        if r.conflict_intensity > 0.5:
            conf = self.beliefs.get_confidence('cooperation_bonus_increase')
            signal.cooperation_bonus_delta = 0.15 * self.sensitivity * conf
        
        # Learning rate
        if r.fitness_momentum > 0.2:
            signal.learning_rate_delta = 0.1 * self.sensitivity
        elif r.fitness_momentum < -0.2:
            signal.learning_rate_delta = -0.1 * self.sensitivity
        
        # ═══════════════════════════════════════════════════════════════════
        # BLEND WITH LEARNED SUGGESTIONS (if predictor has enough data)
        # ═══════════════════════════════════════════════════════════════════
        
        if self.predictor and self.predictor.training_steps >= 20:
            current_params = {
                'survival_threshold': 0.3,  # Would get from config_tuner
                'competition_intensity': 0.5,
                'germination_rate': 0.1,
                'cooperation_bonus': 0.2
            }
            learned = self.predictor.suggest(current_params)
            
            # Blend: 70% heuristic, 30% learned
            blend = 0.3
            if 'survival_threshold' in learned:
                signal.survival_threshold_delta = (1-blend) * signal.survival_threshold_delta + blend * learned['survival_threshold']
            if 'competition_intensity' in learned:
                signal.competition_intensity_delta = (1-blend) * signal.competition_intensity_delta + blend * learned['competition_intensity']
            if 'germination_rate' in learned:
                signal.germination_rate_delta = (1-blend) * signal.germination_rate_delta + blend * learned['germination_rate']
            if 'cooperation_bonus' in learned:
                signal.cooperation_bonus_delta = (1-blend) * signal.cooperation_bonus_delta + blend * learned['cooperation_bonus']
            
            signal.source = "blended"
        
        # Confidence
        history_confidence = min(1.0, len(self.history) / 20)
        extremity = abs(r.overall_health)
        signal.confidence = history_confidence * (0.5 + extremity * 0.5)
        
        self.last_signal = signal
        return signal
    
    def influence(self, config_tuner: Any, force: bool = False) -> Dict[str, Any]:
        """Apply governance signal to config tuner."""
        now = time.time()
        
        if not force and (now - self._last_signal_time) < self.signal_cooldown:
            return {}
        
        signal = self.get_signal()
        
        if signal.confidence < 0.3:
            return {}
        
        changes = {}
        
        if config_tuner and hasattr(config_tuner, 'adjust_parameter'):
            param_map = {
                'survival_threshold': signal.survival_threshold_delta,
                'competition_intensity': signal.competition_intensity_delta,
                'germination_rate': signal.germination_rate_delta,
                'cooperation_bonus': signal.cooperation_bonus_delta,
            }
            
            for param, delta in param_map.items():
                if abs(delta) > 0.01:
                    try:
                        scaled_delta = delta * signal.confidence
                        config_tuner.adjust_parameter(param, scaled_delta)
                        changes[param] = scaled_delta
                        
                        # Record action for belief updates
                        direction = 'increase' if scaled_delta > 0 else 'decrease'
                        self._last_action = f"{param}_{direction}"
                    except Exception:
                        pass
            
            # Add sample to predictor
            if self.predictor and self.current_reading:
                current_params = {}
                for p in ['survival_threshold', 'competition_intensity', 'germination_rate', 'cooperation_bonus']:
                    if hasattr(config_tuner, 'get'):
                        current_params[p] = config_tuner.get(p) or 0.0
                self.predictor.add_sample(current_params, self.current_reading.overall_health)
                self.predictor.train()
        
        if changes:
            self._last_signal_time = now
            src = "📊" if signal.source == "blended" else "📏"
            print(f"[ANTENNAE] 🦋 {src} Governance: {changes}")
        
        return changes
    
    def get_reading_summary(self) -> str:
        """Human-readable summary."""
        if not self.current_reading:
            return "[ANTENNAE] No readings yet"
        
        r = self.current_reading
        
        if r.overall_health > 0.5:
            health_word = "THRIVING"
        elif r.overall_health > 0.2:
            health_word = "HEALTHY"
        elif r.overall_health > -0.2:
            health_word = "STABLE"
        elif r.overall_health > -0.5:
            health_word = "STRUGGLING"
        else:
            health_word = "CRISIS"
        
        return (
            f"[ANTENNAE] 🦋 {health_word} | "
            f"pop:{r.population_pressure:+.2f} "
            f"fit:{r.fitness_momentum:+.2f} "
            f"div:{r.diversity_sense:.2f}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state."""
        return {
            'current_reading': self.current_reading.to_dict() if self.current_reading else None,
            'last_signal': self.last_signal.to_dict() if self.last_signal else None,
            'history_length': len(self.history),
            'beliefs': self.beliefs.to_dict(),
            'predictor': self.predictor.get_stats() if self.predictor else None
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COLLECTIVE VOTING - Organisms ARE the Antennae
# ═══════════════════════════════════════════════════════════════════════════════

def collective_vote(organisms: Dict[str, Any]) -> Dict[str, float]:
    """Fitness-weighted voting on system direction."""
    if not organisms:
        return {}
    
    votes = []
    weights = []
    
    for org in organisms.values():
        fitness = getattr(org, 'fitness', 0.5)
        vote = {}
        
        epsilon = getattr(org, 'epsilon', 0.5)
        vote['exploration'] = epsilon - 0.5
        
        alliance_id = getattr(org, 'alliance_id', None)
        vote['cooperation'] = 0.3 if alliance_id else -0.1
        
        age = getattr(org, 'age', 0)
        vote['survival_threshold'] = -0.1 if age > 100 else 0.1
        
        votes.append(vote)
        weights.append(fitness)
    
    total_weight = sum(weights) or 1.0
    result = {}
    
    for key in votes[0].keys():
        weighted_sum = sum(v[key] * w for v, w in zip(votes, weights))
        result[key] = weighted_sum / total_weight
    
    return result


def create_antennae_from_config(config: Dict[str, Any]) -> Antennae:
    """Create Antennae from config dict."""
    antennae_config = config.get('antennae', {})
    antennae = Antennae(history_size=antennae_config.get('history_size', 100))
    antennae.sensitivity = antennae_config.get('sensitivity', 1.0)
    antennae.signal_cooldown = antennae_config.get('signal_cooldown', 5.0)
    return antennae
