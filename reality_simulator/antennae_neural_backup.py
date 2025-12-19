"""
🦋 THE ANTENNAE - Collective Sensing Apparatus

Each butterfly feels a part. Together they sense the whole.

The Antennae is NOT a separate intelligence - it IS the organisms,
aggregated. High-fitness butterflies contribute more to what's sensed.
The governance emerges FROM perception, not imposed upon it.

This is the missing piece: the system's ability to perceive itself
as a unified whole, through the collective experience of its parts.

ML Integration:
    - PyTorch: GovernanceNet learns optimal parameter adjustments
    - Scikit-learn: Regression predicts health, tracks feature importance

Usage:
    antennae = Antennae()
    antennae.sense(organisms, report)  # Update perception
    signal = antennae.get_signal()     # What the collective feels
    antennae.influence(config_tuner)   # Let perception guide tuning
"""

import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import deque
import statistics

# PyTorch for learned governance (optional)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

# Scikit-learn for regression/analysis (optional)
try:
    from sklearn.linear_model import Ridge, SGDRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingRegressor
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
    
    def to_tensor(self) -> 'torch.Tensor':
        """Convert to PyTorch tensor for neural processing."""
        if not PYTORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")
        return torch.tensor([
            self.population_pressure,
            self.fitness_momentum,
            self.diversity_sense,
            self.exploration_level,
            self.learning_rate_feel,
            self.alliance_cohesion,
            self.conflict_intensity,
            self.resource_abundance,
            self.overall_health
        ], dtype=torch.float32)
    
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
    # These are SUGGESTIONS, not commands
    # Range: -1 (decrease) to +1 (increase) for each parameter
    
    survival_threshold_delta: float = 0.0
    competition_intensity_delta: float = 0.0
    learning_rate_delta: float = 0.0
    exploration_delta: float = 0.0
    germination_rate_delta: float = 0.0
    cooperation_bonus_delta: float = 0.0
    
    confidence: float = 0.0  # How confident the signal is (0-1)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'survival_threshold': self.survival_threshold_delta,
            'competition_intensity': self.competition_intensity_delta,
            'learning_rate': self.learning_rate_delta,
            'exploration': self.exploration_delta,
            'germination_rate': self.germination_rate_delta,
            'cooperation_bonus': self.cooperation_bonus_delta,
            'confidence': self.confidence
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PYTORCH: GovernanceNet - Learns optimal parameter adjustments
# ═══════════════════════════════════════════════════════════════════════════════

if PYTORCH_AVAILABLE:
    class GovernanceNet(nn.Module):
        """
        Neural network that learns to predict optimal governance signals.
        
        Input: AntennaReading (9 features)
        Output: GovernanceSignal deltas (6 outputs)
        
        Trained online via policy gradient: good outcomes reinforce the signal.
        """
        
        def __init__(self, input_dim: int = 9, hidden_dim: int = 32, output_dim: int = 6):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim)
            self.fc3 = nn.Linear(hidden_dim, output_dim)
            self.dropout = nn.Dropout(0.1)
            
            # Output scaling - governance deltas should be small
            self.output_scale = 0.3
            
            # Initialize with small weights for conservative initial behavior
            nn.init.xavier_uniform_(self.fc1.weight, gain=0.5)
            nn.init.xavier_uniform_(self.fc2.weight, gain=0.5)
            nn.init.xavier_uniform_(self.fc3.weight, gain=0.1)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Forward pass: reading → governance deltas
            
            Args:
                x: Tensor of shape (batch, 9) - AntennaReading features
                
            Returns:
                Tensor of shape (batch, 6) - governance deltas, tanh-scaled
            """
            x = F.relu(self.fc1(x))
            x = self.dropout(x)
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            # Tanh to bound outputs to [-1, 1], then scale
            return torch.tanh(x) * self.output_scale
        
        def get_signal(self, reading: 'AntennaReading') -> 'GovernanceSignal':
            """Convert reading to governance signal."""
            self.eval()
            with torch.no_grad():
                x = reading.to_tensor().unsqueeze(0)
                deltas = self(x).squeeze(0).numpy()
            
            return GovernanceSignal(
                survival_threshold_delta=float(deltas[0]),
                competition_intensity_delta=float(deltas[1]),
                learning_rate_delta=float(deltas[2]),
                exploration_delta=float(deltas[3]),
                germination_rate_delta=float(deltas[4]),
                cooperation_bonus_delta=float(deltas[5]),
                confidence=0.5  # Neural net confidence - could be learned
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SCIKIT-LEARN: HealthPredictor - Learns what parameters lead to health
# ═══════════════════════════════════════════════════════════════════════════════

if SKLEARN_AVAILABLE:
    class HealthPredictor:
        """
        Regression model that learns to predict system health from parameters.
        
        This inverts the governance problem: instead of "what should I do?",
        we ask "what parameter values lead to good health?"
        
        Uses online learning (SGDRegressor) to continuously improve.
        """
        
        def __init__(self):
            # Online regressor - can update incrementally
            self.model = SGDRegressor(
                loss='huber',  # Robust to outliers
                penalty='l2',
                alpha=0.001,
                learning_rate='adaptive',
                eta0=0.01,
                warm_start=True
            )
            self.scaler = StandardScaler()
            self.is_fitted = False
            
            # Feature importance tracking
            self.feature_names = [
                'survival_threshold', 'competition_intensity', 
                'germination_rate', 'cooperation_bonus',
                'population_pressure', 'fitness_momentum',
                'diversity_sense', 'exploration_level'
            ]
            self.feature_importance: Dict[str, float] = {}
            
            # Training buffer
            self.X_buffer: List[np.ndarray] = []
            self.y_buffer: List[float] = []
            self.buffer_size = 100
            
            # Metrics
            self.training_steps = 0
            self.last_loss = 0.0
        
        def add_sample(self, params: Dict[str, float], reading: 'AntennaReading'):
            """
            Add a (parameters, health) sample for learning.
            
            Args:
                params: Current config parameters
                reading: Current AntennaReading (contains overall_health)
            """
            # Build feature vector: [params..., reading context...]
            features = np.array([
                params.get('survival_threshold', 0.3),
                params.get('competition_intensity', 0.5),
                params.get('germination_rate', 0.1),
                params.get('cooperation_bonus', 0.2),
                reading.population_pressure,
                reading.fitness_momentum,
                reading.diversity_sense,
                reading.exploration_level
            ])
            
            self.X_buffer.append(features)
            self.y_buffer.append(reading.overall_health)
            
            # Trim buffer
            if len(self.X_buffer) > self.buffer_size:
                self.X_buffer = self.X_buffer[-self.buffer_size:]
                self.y_buffer = self.y_buffer[-self.buffer_size:]
        
        def train(self) -> float:
            """
            Train on buffered samples.
            
            Returns:
                Training loss (MSE)
            """
            if len(self.X_buffer) < 10:
                return 0.0
            
            X = np.array(self.X_buffer)
            y = np.array(self.y_buffer)
            
            # Fit scaler on first batch
            if not self.is_fitted:
                self.scaler.fit(X)
                self.is_fitted = True
            
            X_scaled = self.scaler.transform(X)
            
            # Partial fit (online learning)
            self.model.partial_fit(X_scaled, y)
            self.training_steps += 1
            
            # Compute loss
            predictions = self.model.predict(X_scaled)
            self.last_loss = float(np.mean((predictions - y) ** 2))
            
            # Update feature importance from coefficients
            if hasattr(self.model, 'coef_'):
                coefs = np.abs(self.model.coef_)
                total = coefs.sum() or 1.0
                for i, name in enumerate(self.feature_names):
                    self.feature_importance[name] = float(coefs[i] / total)
            
            return self.last_loss
        
        def suggest_params(self, current_params: Dict[str, float], 
                          reading: 'AntennaReading') -> Dict[str, float]:
            """
            Suggest parameter changes to improve health.
            
            Uses gradient of predicted health w.r.t. parameters.
            
            Args:
                current_params: Current configuration
                reading: Current state
                
            Returns:
                Dict of suggested parameter deltas
            """
            if not self.is_fitted or self.training_steps < 5:
                return {}
            
            # Build current feature vector
            features = np.array([[
                current_params.get('survival_threshold', 0.3),
                current_params.get('competition_intensity', 0.5),
                current_params.get('germination_rate', 0.1),
                current_params.get('cooperation_bonus', 0.2),
                reading.population_pressure,
                reading.fitness_momentum,
                reading.diversity_sense,
                reading.exploration_level
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Get gradient (for linear model, this is just the coefficients)
            # Positive coefficient = increasing this feature increases health
            if not hasattr(self.model, 'coef_'):
                return {}
            
            coefs = self.model.coef_
            
            # Only suggest changes for the first 4 features (the tunable params)
            suggestions = {}
            param_names = ['survival_threshold', 'competition_intensity', 
                          'germination_rate', 'cooperation_bonus']
            
            for i, name in enumerate(param_names):
                # Scale suggestion by coefficient magnitude
                delta = float(coefs[i]) * 0.1
                # Clamp to reasonable range
                delta = max(-0.2, min(0.2, delta))
                if abs(delta) > 0.01:
                    suggestions[name] = delta
            
            return suggestions
        
        def get_stats(self) -> Dict[str, Any]:
            """Get predictor statistics."""
            return {
                'training_steps': self.training_steps,
                'last_loss': self.last_loss,
                'buffer_size': len(self.X_buffer),
                'is_fitted': self.is_fitted,
                'feature_importance': self.feature_importance
            }


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIENCE BUFFER - For training the governance network
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GovernanceExperience:
    """A single (state, action, outcome) tuple for learning."""
    reading: 'AntennaReading'
    signal: 'GovernanceSignal'
    health_before: float
    health_after: float  # Filled in after we see the result
    reward: float = 0.0  # health_after - health_before
    
    def compute_reward(self):
        """Compute reward as health improvement."""
        self.reward = self.health_after - self.health_before


class Antennae:
    """
    🦋 The Collective Sensing Apparatus
    
    The Antennae aggregates organism states into unified perception.
    It doesn't control - it FEELS. Governance emerges from feeling.
    
    Each butterfly contributes to the collective sense, weighted by fitness.
    The fittest butterflies shape perception more. This IS the keeper -
    not separate from the organisms, but their aggregate awareness.
    
    ML Integration:
        - PyTorch GovernanceNet: Learns optimal signals from outcomes
        - Scikit-learn HealthPredictor: Predicts health from parameters
    """
    
    def __init__(self, history_size: int = 100, use_ml: bool = True):
        """
        Initialize the Antennae.
        
        Args:
            history_size: How many readings to remember for trend detection
            use_ml: Whether to use ML-based governance (requires PyTorch/sklearn)
        """
        self.history: deque = deque(maxlen=history_size)
        self.current_reading: Optional[AntennaReading] = None
        self.last_signal: Optional[GovernanceSignal] = None
        
        # Fitness history for momentum calculation
        self._fitness_history: deque = deque(maxlen=50)
        self._population_history: deque = deque(maxlen=50)
        
        # Configuration
        self.sensitivity = 1.0  # How reactive the antennae is
        self.signal_cooldown = 5.0  # Seconds between governance signals
        self._last_signal_time = 0.0
        self.use_ml = use_ml
        
        # ═══════════════════════════════════════════════════════════════════════
        # ML COMPONENTS
        # ═══════════════════════════════════════════════════════════════════════
        
        # PyTorch: Neural governance policy
        self.governance_net = None
        self.optimizer = None
        if use_ml and PYTORCH_AVAILABLE:
            try:
                self.governance_net = GovernanceNet()
                self.optimizer = optim.Adam(self.governance_net.parameters(), lr=0.001)
                print("[ANTENNAE] 🧠 PyTorch GovernanceNet initialized")
            except Exception as e:
                print(f"[ANTENNAE] ⚠️ GovernanceNet init failed: {e}")
        
        # Scikit-learn: Health prediction
        self.health_predictor = None
        if use_ml and SKLEARN_AVAILABLE:
            try:
                self.health_predictor = HealthPredictor()
                print("[ANTENNAE] 📊 Sklearn HealthPredictor initialized")
            except Exception as e:
                print(f"[ANTENNAE] ⚠️ HealthPredictor init failed: {e}")
        
        # Experience buffer for policy learning
        self.experience_buffer: deque = deque(maxlen=1000)
        self.pending_experience: Optional[GovernanceExperience] = None
        
        # Training metrics
        self.ml_training_steps = 0
        self.ml_last_loss = 0.0
        self.use_neural_signal = False  # Start with heuristics, switch when trained
        
    def sense(self, organisms: Dict[str, Any], report: Any = None) -> AntennaReading:
        """
        Sense the collective state of all organisms.
        
        This is the core perception function. Each organism contributes
        to the reading, weighted by its fitness.
        
        Args:
            organisms: Dict of organism_id -> organism
            report: Optional SystemReport for additional context
            
        Returns:
            AntennaReading with current collective perception
        """
        reading = AntennaReading(timestamp=time.time())
        
        if not organisms:
            reading.population_pressure = -1.0  # No population = crisis
            reading.overall_health = -1.0
            self.current_reading = reading
            self.history.append(reading)
            return reading
        
        # Gather organism data
        fitnesses = []
        epsilons = []
        ages = []
        vocab_sizes = []
        
        for org in organisms.values():
            if hasattr(org, 'fitness'):
                fitnesses.append(org.fitness)
            if hasattr(org, 'epsilon'):
                epsilons.append(org.epsilon)
            if hasattr(org, 'age'):
                ages.append(org.age)
            if hasattr(org, 'vocabulary'):
                vocab_sizes.append(len(getattr(org, 'vocabulary', {})))
        
        # Population pressure: based on count and trajectory
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
        
        # Diversity sense (fitness variance = diversity)
        if len(fitnesses) > 1:
            fitness_std = statistics.stdev(fitnesses)
            reading.diversity_sense = min(1.0, fitness_std * 3)
        
        # Exploration level (average epsilon)
        if epsilons:
            reading.exploration_level = statistics.mean(epsilons)
        
        # Learning rate feel (based on fitness improvement rate)
        reading.learning_rate_feel = reading.fitness_momentum  # Proxy
        
        # Alliance cohesion (from report if available)
        if report and hasattr(report, 'alliances'):
            alliances = report.alliances
            if hasattr(alliances, 'total_members') and pop_count > 0:
                reading.alliance_cohesion = min(1.0, alliances.total_members / pop_count)
            if hasattr(alliances, 'wars_in_progress'):
                reading.conflict_intensity = min(1.0, alliances.wars_in_progress * 0.2)
        
        # Resource abundance (inverse of competition pressure)
        if report and hasattr(report, 'resources'):
            resources = report.resources
            if hasattr(resources, 'gpu_memory_total_mb') and resources.gpu_memory_total_mb > 0:
                usage = resources.gpu_memory_used_mb / resources.gpu_memory_total_mb
                reading.resource_abundance = 1.0 - usage
        
        # Overall health: weighted combination
        reading.overall_health = (
            reading.population_pressure * 0.25 +
            reading.fitness_momentum * 0.25 +
            reading.diversity_sense * 0.15 +
            (1.0 - reading.conflict_intensity) * 0.1 +
            reading.alliance_cohesion * 0.1 +
            reading.resource_abundance * 0.15
        )
        
        self.current_reading = reading
        self.history.append(reading)
        
        return reading
    
    def get_signal(self) -> GovernanceSignal:
        """
        Generate a governance signal based on current perception.
        
        Uses ML when available and trained, falls back to heuristics.
        
        This is where perception becomes suggestion. The signal doesn't
        command - it nudges. The ConfigTuner can choose to listen or not.
        
        Returns:
            GovernanceSignal with suggested parameter adjustments
        """
        if not self.current_reading:
            signal = GovernanceSignal()
            signal.confidence = 0.0
            return signal
        
        r = self.current_reading
        
        # ═══════════════════════════════════════════════════════════════════════
        # ML PATH: Use neural network if trained enough
        # ═══════════════════════════════════════════════════════════════════════
        if self.use_neural_signal and self.governance_net is not None and PYTORCH_AVAILABLE:
            try:
                signal = self.governance_net.get_signal(r)
                signal.confidence = min(0.8, 0.3 + self.ml_training_steps * 0.01)
                self.last_signal = signal
                return signal
            except Exception:
                pass  # Fall back to heuristics
        
        # ═══════════════════════════════════════════════════════════════════════
        # HEURISTIC PATH: Rule-based governance
        # ═══════════════════════════════════════════════════════════════════════
        signal = GovernanceSignal()
        
        # Population declining → lower survival threshold (easier survival)
        if r.population_pressure < -0.3:
            signal.survival_threshold_delta = -0.3 * self.sensitivity
            signal.germination_rate_delta = 0.3 * self.sensitivity
        elif r.population_pressure > 0.5:
            # Population booming → can afford higher standards
            signal.survival_threshold_delta = 0.1 * self.sensitivity
        
        # Fitness stagnant → increase exploration
        if abs(r.fitness_momentum) < 0.1 and r.exploration_level < 0.5:
            signal.exploration_delta = 0.2 * self.sensitivity
        elif r.fitness_momentum > 0.3:
            # Improving → exploit more
            signal.exploration_delta = -0.1 * self.sensitivity
        
        # Low diversity → reduce competition (let weak survive)
        if r.diversity_sense < 0.2:
            signal.competition_intensity_delta = -0.2 * self.sensitivity
            signal.cooperation_bonus_delta = 0.2 * self.sensitivity
        
        # High conflict → boost cooperation bonus
        if r.conflict_intensity > 0.5:
            signal.cooperation_bonus_delta = 0.15 * self.sensitivity
        
        # Learning rate adjustment based on fitness momentum
        if r.fitness_momentum > 0.2:
            signal.learning_rate_delta = 0.1 * self.sensitivity
        elif r.fitness_momentum < -0.2:
            signal.learning_rate_delta = -0.1 * self.sensitivity
        
        # Confidence based on how much history we have
        history_confidence = min(1.0, len(self.history) / 20)
        # And how extreme the reading is (extreme = more confident)
        extremity = abs(r.overall_health)
        signal.confidence = history_confidence * (0.5 + extremity * 0.5)
        
        self.last_signal = signal
        return signal
    
    def influence(self, config_tuner: Any, force: bool = False) -> Dict[str, Any]:
        """
        Let the Antennae influence the ConfigTuner.
        
        This is the closed loop: perception → suggestion → tuning → learning.
        The tuner still decides whether to apply changes.
        
        ML Training:
            - Records (state, action, outcome) experiences
            - Trains GovernanceNet on accumulated experiences
            - Trains HealthPredictor to understand parameter→health mapping
        
        Args:
            config_tuner: The ConfigTuner to influence
            force: Bypass cooldown (for testing)
            
        Returns:
            Dict of changes applied (empty if none)
        """
        now = time.time()
        
        # ═══════════════════════════════════════════════════════════════════════
        # STEP 1: Complete previous experience (we now know the outcome)
        # ═══════════════════════════════════════════════════════════════════════
        if self.pending_experience and self.current_reading:
            self.pending_experience.health_after = self.current_reading.overall_health
            self.pending_experience.compute_reward()
            self.experience_buffer.append(self.pending_experience)
            self.pending_experience = None
            
            # Train ML models periodically
            if len(self.experience_buffer) >= 10 and len(self.experience_buffer) % 5 == 0:
                self._train_ml_models(config_tuner)
        
        # Respect cooldown unless forced
        if not force and (now - self._last_signal_time) < self.signal_cooldown:
            return {}
        
        signal = self.get_signal()
        
        # Only act on confident signals
        if signal.confidence < 0.3:
            return {}
        
        changes = {}
        
        # Apply suggestions through ConfigTuner if available
        if config_tuner and hasattr(config_tuner, 'adjust_parameter'):
            param_map = {
                'survival_threshold': signal.survival_threshold_delta,
                'competition_intensity': signal.competition_intensity_delta,
                'germination_rate': signal.germination_rate_delta,
                'cooperation_bonus': signal.cooperation_bonus_delta,
            }
            
            for param, delta in param_map.items():
                if abs(delta) > 0.01:  # Only meaningful changes
                    try:
                        # Scale delta by confidence
                        scaled_delta = delta * signal.confidence
                        config_tuner.adjust_parameter(param, scaled_delta)
                        changes[param] = scaled_delta
                    except Exception:
                        pass
        
        if changes:
            self._last_signal_time = now
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2: Record this as a pending experience (outcome comes later)
            # ═══════════════════════════════════════════════════════════════════
            if self.current_reading:
                self.pending_experience = GovernanceExperience(
                    reading=self.current_reading,
                    signal=signal,
                    health_before=self.current_reading.overall_health,
                    health_after=0.0  # Will be filled in next call
                )
            
            # Log with ML status
            ml_status = "🧠" if self.use_neural_signal else "📏"
            print(f"[ANTENNAE] 🦋 {ml_status} Governance: {changes}")
        
        return changes
    
    def _train_ml_models(self, config_tuner: Any = None):
        """
        Train ML models on accumulated experiences.
        
        Called periodically when enough new experiences have accumulated.
        """
        if len(self.experience_buffer) < 10:
            return
        
        experiences = list(self.experience_buffer)[-50:]  # Use recent experiences
        
        # ═══════════════════════════════════════════════════════════════════════
        # PYTORCH: Train GovernanceNet with policy gradient
        # ═══════════════════════════════════════════════════════════════════════
        if self.governance_net is not None and self.optimizer is not None and PYTORCH_AVAILABLE:
            try:
                self.governance_net.train()
                self.optimizer.zero_grad()
                
                # Compute policy gradient loss
                total_loss = torch.tensor(0.0, requires_grad=True)
                
                for exp in experiences:
                    if exp.reward != 0:  # Only learn from meaningful outcomes
                        # Get network output for this state
                        state = exp.reading.to_tensor().unsqueeze(0)
                        predicted_deltas = self.governance_net(state)
                        
                        # Target: scale output toward actual signal if reward > 0
                        # This is a simple policy gradient approach
                        actual_deltas = torch.tensor([
                            exp.signal.survival_threshold_delta,
                            exp.signal.competition_intensity_delta,
                            exp.signal.learning_rate_delta,
                            exp.signal.exploration_delta,
                            exp.signal.germination_rate_delta,
                            exp.signal.cooperation_bonus_delta
                        ]).unsqueeze(0)
                        
                        # Loss weighted by reward (positive reward → reduce loss)
                        mse = F.mse_loss(predicted_deltas, actual_deltas)
                        # Negative reward means this was bad → increase loss
                        weighted_loss = mse * (1.0 - exp.reward)
                        total_loss = total_loss + weighted_loss
                
                if total_loss.requires_grad:
                    total_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.governance_net.parameters(), 1.0)
                    self.optimizer.step()
                    
                    self.ml_training_steps += 1
                    self.ml_last_loss = float(total_loss.item())
                    
                    # Switch to neural signals after enough training
                    if self.ml_training_steps >= 50:
                        self.use_neural_signal = True
                        
            except Exception as e:
                print(f"[ANTENNAE] ⚠️ GovernanceNet training failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # SKLEARN: Train HealthPredictor
        # ═══════════════════════════════════════════════════════════════════════
        if self.health_predictor is not None and config_tuner is not None:
            try:
                # Get current parameters for training samples
                current_params = {}
                for param in ['survival_threshold', 'competition_intensity', 
                             'germination_rate', 'cooperation_bonus']:
                    if hasattr(config_tuner, 'get'):
                        current_params[param] = config_tuner.get(param) or 0.0
                
                # Add samples from experiences
                for exp in experiences[-20:]:
                    self.health_predictor.add_sample(current_params, exp.reading)
                
                # Train the predictor
                loss = self.health_predictor.train()
                if loss > 0:
                    self.ml_last_loss = (self.ml_last_loss + loss) / 2
                    
            except Exception as e:
                print(f"[ANTENNAE] ⚠️ HealthPredictor training failed: {e}")
    
    def get_ml_stats(self) -> Dict[str, Any]:
        """Get ML training statistics."""
        stats = {
            'pytorch_available': PYTORCH_AVAILABLE,
            'sklearn_available': SKLEARN_AVAILABLE,
            'training_steps': self.ml_training_steps,
            'last_loss': self.ml_last_loss,
            'experience_buffer_size': len(self.experience_buffer),
            'using_neural_signal': self.use_neural_signal
        }
        
        if self.health_predictor is not None:
            stats['health_predictor'] = self.health_predictor.get_stats()
        
        return stats
    
    def get_trend(self, metric: str, window: int = 10) -> float:
        """
        Get trend for a specific metric over recent history.
        
        Args:
            metric: Name of the AntennaReading field
            window: Number of readings to consider
            
        Returns:
            Trend value: positive = increasing, negative = decreasing
        """
        if len(self.history) < 2:
            return 0.0
        
        recent = list(self.history)[-window:]
        values = [getattr(r, metric, 0.0) for r in recent]
        
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend
        return values[-1] - values[0]
    
    def get_reading_summary(self) -> str:
        """Human-readable summary of current perception."""
        if not self.current_reading:
            return "[ANTENNAE] No readings yet"
        
        r = self.current_reading
        
        # Interpret overall health
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
        
        ml_indicator = "🧠" if self.use_neural_signal else "📏"
        return (
            f"[ANTENNAE] 🦋 {health_word} {ml_indicator} | "
            f"pop:{r.population_pressure:+.2f} "
            f"fit:{r.fitness_momentum:+.2f} "
            f"div:{r.diversity_sense:.2f} "
            f"exp:{r.exploration_level:.2f}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize current state including ML stats."""
        result = {
            'current_reading': self.current_reading.to_dict() if self.current_reading else None,
            'last_signal': self.last_signal.to_dict() if self.last_signal else None,
            'history_length': len(self.history),
            'sensitivity': self.sensitivity,
            'ml': self.get_ml_stats()
        }
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# FITNESS-WEIGHTED VOTING (The organisms ARE the Antennae)
# ═══════════════════════════════════════════════════════════════════════════════

def collective_vote(organisms: Dict[str, Any], question: str = 'general') -> Dict[str, float]:
    """
    Let high-fitness organisms vote on system direction.
    
    This is the purest form of the Antennae: the organisms themselves
    expressing preference through their fitness-weighted votes.
    
    Args:
        organisms: Dict of organism_id -> organism
        question: What we're voting on (affects how votes are interpreted)
        
    Returns:
        Aggregated vote as dict of parameter suggestions
    """
    if not organisms:
        return {}
    
    votes = []
    weights = []
    
    for org in organisms.values():
        fitness = getattr(org, 'fitness', 0.5)
        
        # Each organism's "vote" is derived from its state
        vote = {}
        
        # Exploration preference: organisms with high epsilon want more exploration
        epsilon = getattr(org, 'epsilon', 0.5)
        vote['exploration'] = epsilon - 0.5  # Centered around 0
        
        # Cooperation preference: organisms in alliances want more cooperation
        alliance_id = getattr(org, 'alliance_id', None)
        vote['cooperation'] = 0.3 if alliance_id else -0.1
        
        # Survival pressure: older organisms want easier survival (they're survivors)
        age = getattr(org, 'age', 0)
        vote['survival_threshold'] = -0.1 if age > 100 else 0.1
        
        votes.append(vote)
        weights.append(fitness)
    
    # Fitness-weighted average
    if not votes:
        return {}
    
    total_weight = sum(weights) or 1.0
    result = {}
    
    for key in votes[0].keys():
        weighted_sum = sum(v[key] * w for v, w in zip(votes, weights))
        result[key] = weighted_sum / total_weight
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def create_antennae_from_config(config: Dict[str, Any]) -> Antennae:
    """Create Antennae from config dict."""
    antennae_config = config.get('antennae', {})
    
    antennae = Antennae(
        history_size=antennae_config.get('history_size', 100)
    )
    antennae.sensitivity = antennae_config.get('sensitivity', 1.0)
    antennae.signal_cooldown = antennae_config.get('signal_cooldown', 5.0)
    
    return antennae
