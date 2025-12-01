"""
🔧 ATOMIC CONFIG SYSTEM
=======================

Atomized configuration parameters for causation-tracked meta-learning.

Every config parameter is now a trackable atom:
- Strength indicates confidence in the value
- Associations link related parameters
- Changes emit causation events
- AutoTuner adjustments become traceable

Integration points:
- scikit-learn: GridSearchCV results strengthen/weaken config atoms
- PyTorch: Training loss gradients inform config adjustments
- AutoTuner: Uses atomic configs instead of raw values
- Butterfly Engine: Explains "WHY did learning_rate change to 0.001?"

The Highlander Protocol can use this for:
- Fitness-based config inheritance (winner takes loser's best configs)
- Population-level config evolution
- Emergent hyperparameter optimization

Author: Convergence Engine Team
Created: 2024
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
import numpy as np
import time
import json
from enum import Enum


class ConfigDomain(Enum):
    """Domain categories for config parameters."""
    NEURAL = "neural"           # Hidden sizes, activations, layers
    LEARNING = "learning"       # Learning rates, optimizers, schedules
    EVOLUTION = "evolution"     # Mutation rates, selection pressure
    SIMULATION = "simulation"   # VP params, time steps, thresholds
    LANGUAGE = "language"       # Vocabulary, teaching rates
    ILLUMINATION = "illumination"  # Archive resolution, coverage
    HIGHLANDER = "highlander"   # Competition params (future!)


class ConfigType(Enum):
    """Type of config parameter for validation."""
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    CATEGORICAL = "categorical"


@dataclass
class ConfigAssociation:
    """
    Association between config parameters.
    
    "When learning_rate goes up, batch_size often goes down"
    """
    target_param: str
    correlation: float = 0.0  # -1 to 1 (negative = inverse correlation)
    formation_time: float = 0.0
    formation_reason: str = "unknown"
    observation_count: int = 0
    
    # Track joint success/failure
    joint_success_count: int = 0
    joint_failure_count: int = 0
    
    def update(self, success: bool, reason: str):
        """Update association based on joint outcome."""
        self.observation_count += 1
        if success:
            self.joint_success_count += 1
        else:
            self.joint_failure_count += 1
        self.formation_reason = reason
    
    @property
    def reliability(self) -> float:
        """How reliable is this association?"""
        total = self.joint_success_count + self.joint_failure_count
        if total == 0:
            return 0.5
        return self.joint_success_count / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target': self.target_param,
            'correlation': self.correlation,
            'reliability': self.reliability,
            'observations': self.observation_count
        }


@dataclass
class ConfigAtom:
    """
    Single trackable configuration parameter.
    
    Like a linguistic atom, but for hyperparameters and settings.
    Every change is causation-tracked for Butterfly Engine explainability.
    
    Attributes:
        param_name: Unique parameter identifier (e.g., 'learning_rate', 'vp_decay')
        value: Current parameter value
        strength: Confidence in this value (0.0 to 1.0)
        bounds: Valid range for numeric types
        domain: Which subsystem this belongs to
        config_type: Type for validation
    """
    param_name: str
    value: Any
    strength: float = 0.5  # Confidence in current value
    
    # Constraints
    bounds: Tuple[float, float] = (0.0, 1.0)
    allowed_values: List[Any] = field(default_factory=list)  # For categorical
    domain: ConfigDomain = ConfigDomain.SIMULATION
    config_type: ConfigType = ConfigType.FLOAT
    
    # Associations to other config params
    associations: Dict[str, ConfigAssociation] = field(default_factory=dict)
    
    # History tracking
    value_history: List[Tuple[float, Any, str]] = field(default_factory=list)  # (timestamp, value, reason)
    creation_time: float = 0.0
    last_update_time: float = 0.0
    update_count: int = 0
    
    # Performance tracking
    success_with_value: Dict[str, int] = field(default_factory=dict)  # value_str -> success_count
    failure_with_value: Dict[str, int] = field(default_factory=dict)  # value_str -> failure_count
    
    # Learning metadata
    sensitivity: float = 1.0  # How readily this param should change
    stability: float = 0.0    # How stable the value has been (0=volatile, 1=stable)
    
    # Event emitter (set by AtomicConfigSystem)
    _event_emitter: Optional[Callable] = field(default=None, repr=False)
    _system_id: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        if self.creation_time == 0.0:
            self.creation_time = time.time()
        # Initialize value_history with creation
        if not self.value_history:
            self.value_history.append((self.creation_time, self.value, "initialized"))
    
    def update_value(self, new_value: Any, reason: str, emit_event: bool = True) -> bool:
        """
        Update parameter value with causation tracking.
        
        Args:
            new_value: New parameter value
            reason: Why the change happened (for Butterfly Engine)
            emit_event: Whether to emit causation event
            
        Returns:
            True if value was updated, False if invalid
        """
        # Validate based on type
        if not self._validate_value(new_value):
            return False
        
        old_value = self.value
        self.value = new_value
        self.last_update_time = time.time()
        self.update_count += 1
        
        # Track history (keep last 50)
        self.value_history.append((self.last_update_time, new_value, reason))
        if len(self.value_history) > 50:
            self.value_history = self.value_history[-50:]
        
        # Update stability metric
        self._update_stability()
        
        # Emit causation event
        if emit_event and self._event_emitter:
            self._emit_config_update(old_value, reason)
        
        return True
    
    def _validate_value(self, value: Any) -> bool:
        """Validate value against constraints."""
        if self.config_type == ConfigType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            return self.bounds[0] <= value <= self.bounds[1]
        
        elif self.config_type == ConfigType.INT:
            if not isinstance(value, int):
                return False
            return self.bounds[0] <= value <= self.bounds[1]
        
        elif self.config_type == ConfigType.BOOL:
            return isinstance(value, bool)
        
        elif self.config_type == ConfigType.CATEGORICAL:
            return value in self.allowed_values
        
        return True
    
    def _update_stability(self):
        """Calculate how stable this parameter has been."""
        if len(self.value_history) < 3:
            self.stability = 0.0
            return
        
        # Look at recent values
        recent = [v for _, v, _ in self.value_history[-10:]]
        
        if self.config_type in [ConfigType.FLOAT, ConfigType.INT]:
            # Numeric stability = inverse of coefficient of variation
            values = np.array(recent, dtype=float)
            if np.mean(values) != 0:
                cv = np.std(values) / abs(np.mean(values))
                self.stability = max(0.0, 1.0 - cv)
            else:
                self.stability = 1.0 if np.std(values) == 0 else 0.0
        else:
            # Categorical/bool stability = mode frequency
            from collections import Counter
            counts = Counter(str(v) for v in recent)
            self.stability = counts.most_common(1)[0][1] / len(recent)
    
    def record_outcome(self, success: bool, context: str = ""):
        """
        Record whether current value led to success or failure.
        This enables learning which values work.
        """
        value_key = str(self.value)
        
        if success:
            self.success_with_value[value_key] = self.success_with_value.get(value_key, 0) + 1
            # Strengthen confidence
            self.strength = min(1.0, self.strength + 0.05)
        else:
            self.failure_with_value[value_key] = self.failure_with_value.get(value_key, 0) + 1
            # Weaken confidence
            self.strength = max(0.0, self.strength - 0.05)
    
    def get_value_performance(self, value: Any = None) -> float:
        """Get success rate for a specific value (or current value)."""
        value_key = str(value if value is not None else self.value)
        successes = self.success_with_value.get(value_key, 0)
        failures = self.failure_with_value.get(value_key, 0)
        total = successes + failures
        
        if total == 0:
            return 0.5  # No data
        return successes / total
    
    def suggest_value(self) -> Any:
        """
        Suggest best value based on historical performance.
        Uses Thompson Sampling-like approach.
        """
        if self.config_type in [ConfigType.FLOAT, ConfigType.INT]:
            # Find value with best performance from history
            best_value = self.value
            best_score = self.get_value_performance()
            
            for value_str in self.success_with_value.keys():
                try:
                    if self.config_type == ConfigType.FLOAT:
                        v = float(value_str)
                    else:
                        v = int(value_str)
                    score = self.get_value_performance(v)
                    if score > best_score:
                        best_score = score
                        best_value = v
                except ValueError:
                    continue
            
            return best_value
        
        elif self.config_type == ConfigType.CATEGORICAL:
            # Find best categorical value
            best_value = self.value
            best_score = -1
            
            for allowed in self.allowed_values:
                score = self.get_value_performance(allowed)
                if score > best_score:
                    best_score = score
                    best_value = allowed
            
            return best_value
        
        return self.value
    
    def form_association(self, target_param: str, correlation: float, reason: str):
        """Form or update association with another config parameter."""
        if target_param in self.associations:
            # Update existing
            assoc = self.associations[target_param]
            # Moving average of correlation
            assoc.correlation = 0.7 * assoc.correlation + 0.3 * correlation
            assoc.observation_count += 1
            assoc.formation_reason = reason
        else:
            # New association
            self.associations[target_param] = ConfigAssociation(
                target_param=target_param,
                correlation=correlation,
                formation_time=time.time(),
                formation_reason=reason
            )
    
    def _emit_config_update(self, old_value: Any, reason: str):
        """Emit causation event for Butterfly Engine."""
        if not self._event_emitter:
            return
        
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='config',
                event_type='config_atom_update',
                data={
                    'system_id': self._system_id,
                    'param_name': self.param_name,
                    'domain': self.domain.value,
                    'old_value': old_value,
                    'new_value': self.value,
                    'strength': self.strength,
                    'stability': self.stability,
                    'reason': reason,
                    'update_count': self.update_count
                }
            )
            self._event_emitter(event)
        except ImportError:
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'param_name': self.param_name,
            'value': self.value,
            'strength': self.strength,
            'bounds': list(self.bounds),
            'domain': self.domain.value,
            'type': self.config_type.value,
            'stability': self.stability,
            'update_count': self.update_count,
            'performance': self.get_value_performance(),
            'associations': {k: v.to_dict() for k, v in self.associations.items()}
        }


class AtomicConfigSystem:
    """
    Manages atomized configuration for a simulation/training run.
    
    Every config parameter is a trackable atom with:
    - Causation events on change
    - Performance tracking per value
    - Associations between parameters
    - History for temporal analysis
    
    Integration with ML frameworks:
    - scikit-learn: GridSearchCV/RandomizedSearchCV results update atoms
    - PyTorch: Training metrics inform config adjustments
    - AutoTuner: Uses atomic configs with full explainability
    """
    
    def __init__(self, system_id: str = "default", 
                 event_emitter: Optional[Callable] = None,
                 initial_config: Optional[Dict[str, Any]] = None):
        """
        Initialize atomic config system.
        
        Args:
            system_id: Unique identifier for this config system
            event_emitter: Callback to emit causation events
            initial_config: Initial configuration to atomize
        """
        self.system_id = system_id
        self.event_emitter = event_emitter
        
        # Core storage
        self.atoms: Dict[str, ConfigAtom] = {}
        
        # Domain groupings
        self.domains: Dict[ConfigDomain, Set[str]] = {d: set() for d in ConfigDomain}
        
        # Statistics
        self.total_updates = 0
        self.creation_time = time.time()
        
        # Initialize with default atoms
        self._initialize_default_atoms()
        
        # Override with initial config if provided
        if initial_config:
            self.update_from_dict(initial_config)
    
    def _initialize_default_atoms(self):
        """Initialize with standard Convergence Engine config parameters."""
        
        # ═══════════════════════════════════════════════════════════════
        # NEURAL DOMAIN
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='hidden_size',
            value=64,
            bounds=(16, 512),
            domain=ConfigDomain.NEURAL,
            config_type=ConfigType.INT,
            sensitivity=0.5  # Moderate sensitivity
        ))
        
        self._add_atom(ConfigAtom(
            param_name='num_layers',
            value=2,
            bounds=(1, 6),
            domain=ConfigDomain.NEURAL,
            config_type=ConfigType.INT,
            sensitivity=0.3  # Low sensitivity - architecture changes are risky
        ))
        
        self._add_atom(ConfigAtom(
            param_name='dropout_rate',
            value=0.1,
            bounds=(0.0, 0.5),
            domain=ConfigDomain.NEURAL,
            config_type=ConfigType.FLOAT,
            sensitivity=0.7
        ))
        
        self._add_atom(ConfigAtom(
            param_name='activation',
            value='relu',
            allowed_values=['relu', 'tanh', 'gelu', 'silu', 'leaky_relu'],
            domain=ConfigDomain.NEURAL,
            config_type=ConfigType.CATEGORICAL,
            sensitivity=0.4
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # LEARNING DOMAIN
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='learning_rate',
            value=0.001,
            bounds=(1e-6, 1.0),
            domain=ConfigDomain.LEARNING,
            config_type=ConfigType.FLOAT,
            sensitivity=0.9  # Very sensitive - small changes matter
        ))
        
        self._add_atom(ConfigAtom(
            param_name='batch_size',
            value=32,
            bounds=(4, 256),
            domain=ConfigDomain.LEARNING,
            config_type=ConfigType.INT,
            sensitivity=0.6
        ))
        
        self._add_atom(ConfigAtom(
            param_name='optimizer',
            value='adam',
            allowed_values=['adam', 'adamw', 'sgd', 'rmsprop', 'adagrad'],
            domain=ConfigDomain.LEARNING,
            config_type=ConfigType.CATEGORICAL,
            sensitivity=0.5
        ))
        
        self._add_atom(ConfigAtom(
            param_name='weight_decay',
            value=0.01,
            bounds=(0.0, 0.1),
            domain=ConfigDomain.LEARNING,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # EVOLUTION DOMAIN
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='mutation_rate',
            value=0.1,
            bounds=(0.01, 0.5),
            domain=ConfigDomain.EVOLUTION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.8
        ))
        
        self._add_atom(ConfigAtom(
            param_name='crossover_rate',
            value=0.7,
            bounds=(0.0, 1.0),
            domain=ConfigDomain.EVOLUTION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        self._add_atom(ConfigAtom(
            param_name='selection_pressure',
            value=2.0,
            bounds=(1.0, 10.0),
            domain=ConfigDomain.EVOLUTION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.7
        ))
        
        self._add_atom(ConfigAtom(
            param_name='elite_fraction',
            value=0.1,
            bounds=(0.0, 0.5),
            domain=ConfigDomain.EVOLUTION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.5
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # SIMULATION DOMAIN (VP system)
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='vp_decay_rate',
            value=0.01,
            bounds=(0.001, 0.1),
            domain=ConfigDomain.SIMULATION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.7
        ))
        
        self._add_atom(ConfigAtom(
            param_name='vp_critical_threshold',
            value=0.2,
            bounds=(0.05, 0.4),
            domain=ConfigDomain.SIMULATION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.8
        ))
        
        self._add_atom(ConfigAtom(
            param_name='vp_comfort_zone',
            value=0.7,
            bounds=(0.5, 0.95),
            domain=ConfigDomain.SIMULATION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.5
        ))
        
        self._add_atom(ConfigAtom(
            param_name='time_step_size',
            value=0.1,
            bounds=(0.01, 1.0),
            domain=ConfigDomain.SIMULATION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.4
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # LANGUAGE DOMAIN
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='vocabulary_growth_rate',
            value=0.05,
            bounds=(0.01, 0.2),
            domain=ConfigDomain.LANGUAGE,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        self._add_atom(ConfigAtom(
            param_name='concept_decay_rate',
            value=0.01,
            bounds=(0.001, 0.1),
            domain=ConfigDomain.LANGUAGE,
            config_type=ConfigType.FLOAT,
            sensitivity=0.5
        ))
        
        self._add_atom(ConfigAtom(
            param_name='teaching_effectiveness',
            value=0.5,
            bounds=(0.1, 1.0),
            domain=ConfigDomain.LANGUAGE,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # ILLUMINATION DOMAIN
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='archive_resolution',
            value=20,
            bounds=(5, 100),
            domain=ConfigDomain.ILLUMINATION,
            config_type=ConfigType.INT,
            sensitivity=0.4
        ))
        
        self._add_atom(ConfigAtom(
            param_name='min_samples_per_cell',
            value=1,
            bounds=(1, 10),
            domain=ConfigDomain.ILLUMINATION,
            config_type=ConfigType.INT,
            sensitivity=0.3
        ))
        
        self._add_atom(ConfigAtom(
            param_name='novelty_threshold',
            value=0.1,
            bounds=(0.01, 0.5),
            domain=ConfigDomain.ILLUMINATION,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        # ═══════════════════════════════════════════════════════════════
        # HIGHLANDER DOMAIN (Competition mechanics - THE FUTURE!)
        # ═══════════════════════════════════════════════════════════════
        self._add_atom(ConfigAtom(
            param_name='survival_threshold',
            value=0.3,
            bounds=(0.1, 0.7),
            domain=ConfigDomain.HIGHLANDER,
            config_type=ConfigType.FLOAT,
            sensitivity=0.8
        ))
        
        self._add_atom(ConfigAtom(
            param_name='competition_intensity',
            value=0.5,
            bounds=(0.0, 1.0),
            domain=ConfigDomain.HIGHLANDER,
            config_type=ConfigType.FLOAT,
            sensitivity=0.7
        ))
        
        self._add_atom(ConfigAtom(
            param_name='cooperation_bonus',
            value=0.2,
            bounds=(0.0, 0.5),
            domain=ConfigDomain.HIGHLANDER,
            config_type=ConfigType.FLOAT,
            sensitivity=0.6
        ))
        
        self._add_atom(ConfigAtom(
            param_name='predation_enabled',
            value=False,
            domain=ConfigDomain.HIGHLANDER,
            config_type=ConfigType.BOOL,
            sensitivity=0.3  # Big change, low sensitivity
        ))
        
        self._add_atom(ConfigAtom(
            param_name='germination_rate',
            value=0.1,
            bounds=(0.01, 0.3),
            domain=ConfigDomain.HIGHLANDER,
            config_type=ConfigType.FLOAT,
            sensitivity=0.5
        ))
        
        # Form known associations
        self._form_default_associations()
    
    def _add_atom(self, atom: ConfigAtom):
        """Add atom to system with proper setup."""
        atom._event_emitter = self.event_emitter
        atom._system_id = self.system_id
        self.atoms[atom.param_name] = atom
        self.domains[atom.domain].add(atom.param_name)
    
    def _form_default_associations(self):
        """Form known correlations between config parameters."""
        # Learning rate <-> batch size (often inverse)
        if 'learning_rate' in self.atoms and 'batch_size' in self.atoms:
            self.atoms['learning_rate'].form_association(
                'batch_size', -0.5, "Larger batch → often smaller LR"
            )
            self.atoms['batch_size'].form_association(
                'learning_rate', -0.5, "Larger LR → often smaller batch"
            )
        
        # Mutation rate <-> selection pressure
        if 'mutation_rate' in self.atoms and 'selection_pressure' in self.atoms:
            self.atoms['mutation_rate'].form_association(
                'selection_pressure', 0.3, "Higher mutation needs higher selection"
            )
        
        # VP decay <-> critical threshold
        if 'vp_decay_rate' in self.atoms and 'vp_critical_threshold' in self.atoms:
            self.atoms['vp_decay_rate'].form_association(
                'vp_critical_threshold', 0.4, "Faster decay → higher threshold needed"
            )
        
        # Dropout <-> weight decay (regularization pair)
        if 'dropout_rate' in self.atoms and 'weight_decay' in self.atoms:
            self.atoms['dropout_rate'].form_association(
                'weight_decay', 0.6, "Both are regularization"
            )
    
    def get(self, param_name: str, default: Any = None) -> Any:
        """Get current value of a parameter."""
        if param_name in self.atoms:
            return self.atoms[param_name].value
        return default
    
    def set(self, param_name: str, value: Any, reason: str = "manual_set") -> bool:
        """Set parameter value with causation tracking."""
        if param_name not in self.atoms:
            return False
        
        success = self.atoms[param_name].update_value(value, reason)
        if success:
            self.total_updates += 1
        return success
    
    def update_from_dict(self, config: Dict[str, Any], reason: str = "bulk_update"):
        """Update multiple parameters from dictionary."""
        for key, value in config.items():
            if key in self.atoms:
                self.set(key, value, reason)
    
    def to_dict(self, domain: Optional[ConfigDomain] = None) -> Dict[str, Any]:
        """Export current values as dictionary."""
        if domain:
            return {
                name: self.atoms[name].value 
                for name in self.domains[domain]
            }
        return {name: atom.value for name, atom in self.atoms.items()}
    
    def record_outcome(self, success: bool, domain: Optional[ConfigDomain] = None,
                      params: Optional[List[str]] = None, context: str = ""):
        """
        Record success/failure outcome for current config.
        Updates strength of relevant config atoms.
        """
        if params:
            target_atoms = [self.atoms[p] for p in params if p in self.atoms]
        elif domain:
            target_atoms = [self.atoms[p] for p in self.domains[domain]]
        else:
            target_atoms = list(self.atoms.values())
        
        for atom in target_atoms:
            atom.record_outcome(success, context)
        
        # Emit outcome event
        if self.event_emitter:
            self._emit_outcome_event(success, domain, params, context)
    
    def _emit_outcome_event(self, success: bool, domain: Optional[ConfigDomain],
                           params: Optional[List[str]], context: str):
        """Emit config outcome event."""
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='config',
                event_type='config_outcome',
                data={
                    'system_id': self.system_id,
                    'success': success,
                    'domain': domain.value if domain else 'all',
                    'params': params or list(self.atoms.keys()),
                    'context': context
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    # ═══════════════════════════════════════════════════════════════════
    # SCIKIT-LEARN INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    
    def from_sklearn_cv_results(self, cv_results: Dict[str, Any], 
                                param_mapping: Optional[Dict[str, str]] = None):
        """
        Update config atoms from scikit-learn GridSearchCV/RandomizedSearchCV results.
        
        Args:
            cv_results: The cv_results_ from a sklearn search object
            param_mapping: Map sklearn param names to our atom names
        """
        mapping = param_mapping or {}
        
        # Get best params
        best_idx = np.argmax(cv_results.get('mean_test_score', [0]))
        
        for key in cv_results.keys():
            if key.startswith('param_'):
                sklearn_param = key[6:]  # Remove 'param_' prefix
                our_param = mapping.get(sklearn_param, sklearn_param)
                
                if our_param in self.atoms:
                    # Get all values tried and their scores
                    values = cv_results[key]
                    scores = cv_results.get('mean_test_score', [0.5] * len(values))
                    
                    # Record performance for each value
                    for val, score in zip(values, scores):
                        if val is not None:
                            self.atoms[our_param].record_outcome(
                                success=(score > 0.5),  # Threshold for "success"
                                context=f"sklearn_cv_score={score:.3f}"
                            )
                    
                    # Update to best value
                    best_val = values[best_idx]
                    if best_val is not None:
                        self.set(our_param, best_val, 
                                reason=f"sklearn_best (score={scores[best_idx]:.3f})")
    
    def to_sklearn_param_grid(self, domain: Optional[ConfigDomain] = None,
                             params: Optional[List[str]] = None) -> Dict[str, List[Any]]:
        """
        Generate sklearn param_grid from config atoms.
        Uses bounds and performance history to suggest search space.
        """
        grid = {}
        
        target_params = params or (
            list(self.domains[domain]) if domain 
            else list(self.atoms.keys())
        )
        
        for param_name in target_params:
            if param_name not in self.atoms:
                continue
            
            atom = self.atoms[param_name]
            
            if atom.config_type == ConfigType.FLOAT:
                # Generate values around current value and historical best
                current = atom.value
                suggested = atom.suggest_value()
                low, high = atom.bounds
                
                # Logarithmic spacing for learning rates, linear otherwise
                if 'learning_rate' in param_name or 'rate' in param_name:
                    values = np.logspace(np.log10(max(low, 1e-7)), np.log10(high), 5)
                else:
                    values = np.linspace(low, high, 5)
                
                # Include current and suggested values
                values = list(set(values.tolist() + [current, suggested]))
                grid[param_name] = sorted([v for v in values if low <= v <= high])
            
            elif atom.config_type == ConfigType.INT:
                low, high = int(atom.bounds[0]), int(atom.bounds[1])
                # Reasonable spread of integer values
                step = max(1, (high - low) // 5)
                grid[param_name] = list(range(low, high + 1, step))
            
            elif atom.config_type == ConfigType.CATEGORICAL:
                grid[param_name] = atom.allowed_values
            
            elif atom.config_type == ConfigType.BOOL:
                grid[param_name] = [True, False]
        
        return grid
    
    # ═══════════════════════════════════════════════════════════════════
    # PYTORCH INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    
    def from_pytorch_training(self, metrics: Dict[str, float], 
                             epoch: int, is_improvement: bool):
        """
        Update config atoms based on PyTorch training metrics.
        
        Args:
            metrics: Dict with 'loss', 'accuracy', etc.
            epoch: Current epoch number
            is_improvement: Whether this epoch improved over previous best
        """
        # Record outcome for learning-related params
        self.record_outcome(
            success=is_improvement,
            domain=ConfigDomain.LEARNING,
            context=f"epoch_{epoch}_loss={metrics.get('loss', 0):.4f}"
        )
        
        # Adaptive learning rate adjustment suggestion
        if 'loss' in metrics and 'learning_rate' in self.atoms:
            loss = metrics['loss']
            lr_atom = self.atoms['learning_rate']
            
            # Simple heuristic: if loss is diverging, LR might be too high
            if loss > 10.0:  # Divergence indicator
                suggested_lr = lr_atom.value * 0.5
                lr_atom.form_association(
                    'loss_divergence', -0.8, 
                    f"Loss diverged at LR={lr_atom.value}"
                )
                # Don't auto-update, just track the observation
        
        # Emit training event
        if self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='config',
                    event_type='pytorch_training_update',
                    data={
                        'system_id': self.system_id,
                        'epoch': epoch,
                        'metrics': metrics,
                        'is_improvement': is_improvement,
                        'current_lr': self.get('learning_rate'),
                        'current_batch': self.get('batch_size')
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass
    
    def get_pytorch_optimizer_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for PyTorch optimizer from config atoms."""
        return {
            'lr': self.get('learning_rate', 0.001),
            'weight_decay': self.get('weight_decay', 0.01)
        }
    
    def get_pytorch_dataloader_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for PyTorch DataLoader from config atoms."""
        return {
            'batch_size': self.get('batch_size', 32),
            'shuffle': True
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # HIGHLANDER PROTOCOL SUPPORT
    # ═══════════════════════════════════════════════════════════════════
    
    def absorb_config(self, loser_config: 'AtomicConfigSystem', 
                     absorption_rate: float = 0.3) -> Dict[str, Any]:
        """
        HIGHLANDER: Winner absorbs loser's best config settings.
        
        When an organism defeats another, it can take the loser's
        best-performing config values as trophies.
        
        Args:
            loser_config: The defeated organism's config system
            absorption_rate: How much of loser's config to absorb (0-1)
            
        Returns:
            Dict of absorbed config changes
        """
        absorbed = {}
        
        for param_name, our_atom in self.atoms.items():
            if param_name not in loser_config.atoms:
                continue
            
            loser_atom = loser_config.atoms[param_name]
            
            # Only absorb if loser's config was performing better for this param
            our_performance = our_atom.get_value_performance()
            loser_performance = loser_atom.get_value_performance()
            
            if loser_performance > our_performance:
                # Absorb loser's value with probability based on performance difference
                if np.random.random() < absorption_rate * (loser_performance - our_performance):
                    old_value = our_atom.value
                    
                    # Blend values for numeric types
                    if our_atom.config_type in [ConfigType.FLOAT, ConfigType.INT]:
                        new_value = 0.7 * our_atom.value + 0.3 * loser_atom.value
                        if our_atom.config_type == ConfigType.INT:
                            new_value = int(round(new_value))
                    else:
                        new_value = loser_atom.value
                    
                    if our_atom.update_value(
                        new_value, 
                        f"highlander_absorbed_from_{loser_config.system_id}"
                    ):
                        absorbed[param_name] = {
                            'old': old_value,
                            'new': new_value,
                            'performance_gain': loser_performance - our_performance
                        }
        
        # Emit absorption event
        if absorbed and self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='config',
                    event_type='highlander_config_absorption',
                    data={
                        'winner_id': self.system_id,
                        'loser_id': loser_config.system_id,
                        'absorbed_params': absorbed,
                        'absorption_rate': absorption_rate
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass
        
        return absorbed
    
    def mutate_configs(self, mutation_rate: Optional[float] = None,
                      domain: Optional[ConfigDomain] = None) -> Dict[str, Any]:
        """
        Mutate config values for evolutionary exploration.
        Respects sensitivity of each parameter.
        """
        rate = mutation_rate or self.get('mutation_rate', 0.1)
        mutations = {}
        
        target_params = (
            list(self.domains[domain]) if domain 
            else list(self.atoms.keys())
        )
        
        for param_name in target_params:
            atom = self.atoms[param_name]
            
            # Mutation probability based on atom sensitivity and global rate
            if np.random.random() > rate * atom.sensitivity:
                continue
            
            old_value = atom.value
            
            if atom.config_type == ConfigType.FLOAT:
                # Gaussian mutation within bounds
                std = (atom.bounds[1] - atom.bounds[0]) * 0.1 * (1 - atom.stability)
                new_value = np.clip(
                    atom.value + np.random.normal(0, std),
                    atom.bounds[0], atom.bounds[1]
                )
            
            elif atom.config_type == ConfigType.INT:
                # Integer step mutation
                step = max(1, int((atom.bounds[1] - atom.bounds[0]) * 0.1))
                new_value = int(np.clip(
                    atom.value + np.random.randint(-step, step + 1),
                    atom.bounds[0], atom.bounds[1]
                ))
            
            elif atom.config_type == ConfigType.CATEGORICAL:
                # Random category
                new_value = np.random.choice(atom.allowed_values)
            
            elif atom.config_type == ConfigType.BOOL:
                new_value = not atom.value
            
            else:
                continue
            
            if atom.update_value(new_value, f"mutation_rate={rate}"):
                mutations[param_name] = {'old': old_value, 'new': new_value}
        
        return mutations
    
    def get_config_signature(self) -> np.ndarray:
        """
        Generate a numeric signature of current config for comparison.
        Useful for clustering similar configs or diversity calculation.
        """
        signature = []
        
        for param_name in sorted(self.atoms.keys()):
            atom = self.atoms[param_name]
            
            if atom.config_type == ConfigType.FLOAT:
                # Normalize to 0-1 range
                norm = (atom.value - atom.bounds[0]) / (atom.bounds[1] - atom.bounds[0])
                signature.append(norm)
            
            elif atom.config_type == ConfigType.INT:
                norm = (atom.value - atom.bounds[0]) / (atom.bounds[1] - atom.bounds[0])
                signature.append(norm)
            
            elif atom.config_type == ConfigType.CATEGORICAL:
                # One-hot encode (or just index)
                idx = atom.allowed_values.index(atom.value) if atom.value in atom.allowed_values else 0
                norm = idx / max(1, len(atom.allowed_values) - 1)
                signature.append(norm)
            
            elif atom.config_type == ConfigType.BOOL:
                signature.append(1.0 if atom.value else 0.0)
        
        return np.array(signature, dtype=np.float32)
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed report on config system health."""
        report = {
            'system_id': self.system_id,
            'total_atoms': len(self.atoms),
            'total_updates': self.total_updates,
            'uptime': time.time() - self.creation_time,
            'domains': {}
        }
        
        for domain in ConfigDomain:
            domain_atoms = [self.atoms[p] for p in self.domains[domain]]
            if domain_atoms:
                report['domains'][domain.value] = {
                    'params': len(domain_atoms),
                    'avg_strength': np.mean([a.strength for a in domain_atoms]),
                    'avg_stability': np.mean([a.stability for a in domain_atoms]),
                    'total_updates': sum(a.update_count for a in domain_atoms)
                }
        
        # Find most and least stable params
        sorted_by_stability = sorted(self.atoms.values(), key=lambda a: a.stability)
        report['least_stable'] = [a.param_name for a in sorted_by_stability[:3]]
        report['most_stable'] = [a.param_name for a in sorted_by_stability[-3:]]
        
        # Find best and worst performing
        sorted_by_perf = sorted(
            self.atoms.values(), 
            key=lambda a: a.get_value_performance()
        )
        report['worst_performing'] = [
            (a.param_name, a.get_value_performance()) 
            for a in sorted_by_perf[:3]
        ]
        report['best_performing'] = [
            (a.param_name, a.get_value_performance()) 
            for a in sorted_by_perf[-3:]
        ]
        
        return report
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONFIGTUNER COMPATIBILITY LAYER
    # These methods provide drop-in replacement for the legacy ConfigTuner
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get tuning statistics - ConfigTuner compatible interface.
        
        This method provides the same interface as the legacy ConfigTuner.get_stats()
        so AtomicConfigSystem can be used as a drop-in replacement.
        """
        # Calculate success metrics from atoms
        total_updates = self.total_updates
        successful_updates = sum(
            sum(a.success_with_value.values()) 
            for a in self.atoms.values()
        )
        total_outcomes = successful_updates + sum(
            sum(a.failure_with_value.values()) 
            for a in self.atoms.values()
        )
        
        # Per-parameter success rates
        param_success_rates = {}
        for param_name, atom in self.atoms.items():
            successes = sum(atom.success_with_value.values())
            failures = sum(atom.failure_with_value.values())
            total = successes + failures
            param_success_rates[param_name] = successes / total if total > 0 else 0.0
        
        # Get recent actions from atoms with updates
        recent_actions = []
        for param_name, atom in sorted(
            self.atoms.items(), 
            key=lambda x: x[1].value_history[-1][0] if x[1].value_history else 0,
            reverse=True
        )[:5]:
            if atom.value_history:
                timestamp, value, reason = atom.value_history[-1]
                old_value = atom.value_history[-2][1] if len(atom.value_history) > 1 else value
                recent_actions.append({
                    'param': param_name,
                    'change': f"{old_value} → {value}",
                    'reason': reason,
                    'success': atom.get_value_performance() > 0.5,
                    'trigger_metrics': {'strength': atom.strength, 'stability': atom.stability},
                    'expected_impact': f"Improve {atom.domain.value} performance",
                    'actual_impact': f"Performance: {atom.get_value_performance():.2%}"
                })
        
        return {
            'enabled': True,  # AtomicConfigSystem is always enabled
            'total_actions': total_updates,
            'successful_actions': successful_updates,
            'success_rate': successful_updates / total_outcomes if total_outcomes > 0 else 0.0,
            'param_success_rates': param_success_rates,
            'recent_actions': recent_actions,
            # Extended stats from AtomicConfigSystem
            'system_id': self.system_id,
            'total_atoms': len(self.atoms),
            'domains': {d.value: len(params) for d, params in self.domains.items() if params},
            'avg_stability': np.mean([a.stability for a in self.atoms.values()]) if self.atoms else 0.0,
            'avg_strength': np.mean([a.strength for a in self.atoms.values()]) if self.atoms else 0.0
        }
    
    def tune(self, metrics: Dict[str, Any], frame_count: int = 0) -> List[Dict[str, Any]]:
        """
        Tune configuration based on metrics - ConfigTuner compatible interface.
        
        Args:
            metrics: Dict with keys like 'fitness', 'cluster_count', 'anomaly_ratio', etc.
            frame_count: Current simulation frame
            
        Returns:
            List of tuning actions taken
        """
        actions = []
        
        # Extract key metrics
        fitness = metrics.get('avg_fitness', metrics.get('fitness', 0.5))
        is_improving = metrics.get('fitness_improving', fitness > 0.5)
        
        # Record outcomes for atoms based on metrics
        for param_name, atom in self.atoms.items():
            # Use domain-specific metrics to judge success
            domain_success = self._evaluate_domain_success(atom.domain, metrics)
            atom.record_outcome(domain_success, f"frame_{frame_count}")
        
        # Suggest improvements for underperforming params
        for param_name, atom in self.atoms.items():
            if atom.get_value_performance() < 0.4 and atom.update_count > 5:
                suggested = atom.suggest_value()
                if suggested != atom.value:
                    old_value = atom.value
                    if atom.update_value(suggested, f"auto_tune_frame_{frame_count}"):
                        actions.append({
                            'param': param_name,
                            'old_value': old_value,
                            'new_value': suggested,
                            'reason': 'Poor performance - trying historically better value',
                            'confidence': atom.strength
                        })
        
        return actions
    
    def _evaluate_domain_success(self, domain: ConfigDomain, metrics: Dict[str, Any]) -> bool:
        """Evaluate if a domain's metrics indicate success."""
        if domain == ConfigDomain.NEURAL:
            loss = metrics.get('neural_loss', metrics.get('loss', 1.0))
            return loss < 0.5 or metrics.get('neural_improving', False)
        
        elif domain == ConfigDomain.EVOLUTION:
            fitness = metrics.get('avg_fitness', 0.5)
            diversity = metrics.get('diversity', 0.5)
            return fitness > 0.4 and diversity > 0.3
        
        elif domain == ConfigDomain.LEARNING:
            return metrics.get('learning_progress', 0.5) > 0.4
        
        elif domain == ConfigDomain.SIMULATION:
            vp = metrics.get('vp', metrics.get('violation_pressure', 0.5))
            return 0.2 < vp < 0.8  # VP in healthy range
        
        elif domain == ConfigDomain.LANGUAGE:
            vocab_size = metrics.get('vocabulary_size', 0)
            return vocab_size > 10 or metrics.get('language_learning', False)
        
        elif domain == ConfigDomain.ILLUMINATION:
            coverage = metrics.get('archive_coverage', 0)
            return coverage > 0.1
        
        else:
            # Default: use overall fitness
            return metrics.get('avg_fitness', 0.5) > 0.4
    
    def __repr__(self) -> str:
        return f"AtomicConfigSystem(id={self.system_id}, atoms={len(self.atoms)}, updates={self.total_updates})"
    
    # ═══════════════════════════════════════════════════════════════════════
    # LEGACY CONFIGTUNER API COMPATIBILITY
    # These methods provide full API compatibility with the legacy ConfigTuner
    # so AtomicConfigSystem can be used as a drop-in replacement
    # ═══════════════════════════════════════════════════════════════════════
    
    def should_tune(self, frame_count: int, tuning_interval: int = 100) -> bool:
        """
        Check if tuning should occur - ConfigTuner compatible.
        
        Args:
            frame_count: Current frame number
            tuning_interval: Frames between tuning attempts
            
        Returns:
            True if enough frames have passed since last tuning
        """
        if not hasattr(self, '_last_tuning_frame'):
            self._last_tuning_frame = 0
        return frame_count - self._last_tuning_frame >= tuning_interval
    
    def analyze_and_tune(self,
                         ml_metrics: Dict[str, Any] = None,
                         neural_metrics: Dict[str, Any] = None,
                         evolution_metrics: Dict[str, Any] = None,
                         network_metrics: Dict[str, Any] = None,
                         frame_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        Analyze system state and propose config changes - ConfigTuner compatible.
        
        This is the main tuning interface matching the legacy ConfigTuner.
        Returns a TuningAction-like dict if a change is recommended, None otherwise.
        
        Args:
            ml_metrics: ML system metrics (clustering, anomalies, etc.)
            neural_metrics: Neural network training metrics
            evolution_metrics: Evolution system metrics (fitness, diversity)
            network_metrics: Network health metrics (VP, connectivity)
            frame_count: Current simulation frame
            
        Returns:
            Dict with tuning action if recommended, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Check tuning interval
        if not self.should_tune(frame_count):
            return None
        
        self._last_tuning_frame = frame_count
        
        # Merge all metrics for domain evaluation
        all_metrics = {}
        for metrics in [ml_metrics, neural_metrics, evolution_metrics, network_metrics]:
            if metrics:
                all_metrics.update(metrics)
        
        # Record outcomes for all atoms based on current metrics
        for param_name, atom in self.atoms.items():
            domain_success = self._evaluate_domain_success(atom.domain, all_metrics)
            atom.record_outcome(domain_success, f"frame_{frame_count}")
        
        # Find atoms that need tuning (poor performance, enough data)
        candidates = []
        for param_name, atom in self.atoms.items():
            performance = atom.get_value_performance()
            if performance < 0.4 and atom.update_count >= 3:
                suggested = atom.suggest_value()
                if suggested != atom.value:
                    # Calculate confidence based on performance history
                    confidence = min(0.9, 0.5 + (0.5 - performance) + (atom.strength * 0.2))
                    candidates.append({
                        'parameter_path': param_name,
                        'current_value': atom.value,
                        'proposed_value': suggested,
                        'confidence': confidence,
                        'reason': f"Performance {performance:.1%} below threshold, suggesting historically better value",
                        'trigger_metrics': {
                            'current_performance': performance,
                            'atom_strength': atom.strength,
                            'update_count': atom.update_count
                        },
                        'expected_impact': f"Improve {atom.domain.value} domain performance",
                        'timestamp': time.time()
                    })
        
        # Select best candidate (highest confidence)
        if candidates:
            best_action = max(candidates, key=lambda a: a['confidence'])
            
            # Only return if confidence is high enough
            if best_action['confidence'] > 0.6:
                logger.info(f"[ATOMIC_CONFIG] Proposing: {best_action['parameter_path']} "
                          f"{best_action['current_value']} → {best_action['proposed_value']} "
                          f"(confidence: {best_action['confidence']:.2f})")
                return best_action
        
        return None
    
    def apply_action(self, action: Dict[str, Any]) -> bool:
        """
        Apply a tuning action - ConfigTuner compatible.
        
        Args:
            action: Dict with 'parameter_path', 'proposed_value', and optionally 'reason'
            
        Returns:
            True if action was applied successfully
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if action is None:
            return False
        
        param_path = action.get('parameter_path')
        proposed_value = action.get('proposed_value')
        reason = action.get('reason', 'tuning_action')
        
        if not param_path or proposed_value is None:
            logger.warning(f"[ATOMIC_CONFIG] Invalid action: missing parameter_path or proposed_value")
            return False
        
        # Handle nested paths (e.g., 'neural.learning_rate')
        if '.' in param_path:
            # For nested paths, use the last component as the atom name
            atom_name = param_path.split('.')[-1]
        else:
            atom_name = param_path
        
        if atom_name in self.atoms:
            old_value = self.atoms[atom_name].value
            success = self.atoms[atom_name].update_value(proposed_value, reason)
            if success:
                logger.info(f"[ATOMIC_CONFIG] Applied: {param_path} {old_value} → {proposed_value}")
            return success
        else:
            # Create new atom for unknown parameters
            logger.info(f"[ATOMIC_CONFIG] Creating new atom for: {param_path}")
            self._add_atom(ConfigAtom(
                param_name=atom_name,
                value=proposed_value,
                domain=ConfigDomain.SIMULATION,  # Default domain
                config_type=self._infer_config_type(proposed_value)
            ))
            return True
    
    def _infer_config_type(self, value: Any) -> 'ConfigType':
        """Infer ConfigType from a value."""
        if isinstance(value, bool):
            return ConfigType.BOOL
        elif isinstance(value, int):
            return ConfigType.INT
        elif isinstance(value, float):
            return ConfigType.FLOAT
        elif isinstance(value, str):
            return ConfigType.CATEGORICAL
        elif isinstance(value, list):
            return ConfigType.LIST
        else:
            return ConfigType.FLOAT  # Default


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def create_config_from_json(filepath: str, system_id: str = "loaded",
                           event_emitter: Optional[Callable] = None) -> AtomicConfigSystem:
    """Load config from JSON file into atomic system."""
    with open(filepath, 'r') as f:
        config = json.load(f)
    
    return AtomicConfigSystem(
        system_id=system_id,
        event_emitter=event_emitter,
        initial_config=config
    )


def merge_configs(configs: List[AtomicConfigSystem], 
                 weights: Optional[List[float]] = None) -> AtomicConfigSystem:
    """
    Merge multiple config systems (e.g., for ensemble learning).
    
    Uses weighted average for numeric types, majority vote for categorical.
    """
    if not configs:
        return AtomicConfigSystem()
    
    if weights is None:
        weights = [1.0 / len(configs)] * len(configs)
    
    merged = AtomicConfigSystem(system_id="merged")
    
    for param_name in merged.atoms.keys():
        atom = merged.atoms[param_name]
        
        values = [c.get(param_name) for c in configs if param_name in c.atoms]
        if not values:
            continue
        
        if atom.config_type in [ConfigType.FLOAT, ConfigType.INT]:
            # Weighted average
            weighted_sum = sum(v * w for v, w in zip(values, weights[:len(values)]))
            new_value = weighted_sum / sum(weights[:len(values)])
            if atom.config_type == ConfigType.INT:
                new_value = int(round(new_value))
        
        elif atom.config_type == ConfigType.CATEGORICAL:
            # Weighted vote
            from collections import Counter
            weighted_counts = Counter()
            for v, w in zip(values, weights[:len(values)]):
                weighted_counts[v] += w
            new_value = weighted_counts.most_common(1)[0][0]
        
        elif atom.config_type == ConfigType.BOOL:
            # Majority vote
            new_value = sum(values) > len(values) / 2
        
        else:
            new_value = values[0]
        
        merged.set(param_name, new_value, f"merged_from_{len(configs)}_configs")
    
    return merged
