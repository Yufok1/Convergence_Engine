# 🦋 The Antennae System

**Collective Sensing Apparatus for Self-Governing Ecosystems**

---

## Overview

The Antennae is NOT a separate intelligence - it IS the organisms, aggregated. High-fitness butterflies contribute more to what's sensed. The governance emerges FROM perception, not imposed upon it.

```
Each butterfly feels a part. Together they sense the whole.
```

---

## Philosophy: Occam's Razor Design

The original implementation used a PyTorch neural network to learn governance policies. We applied Occam's Razor and realized:

| Approach | Complexity | Justification |
|----------|------------|---------------|
| Neural Net (9→32→32→6) | High | Overkill for 6 parameters |
| **Beliefs + Regression** | Low | Organisms already have cognition systems |

The organisms have skepticism, curiosity, and semantic understanding. The Antennae task is simpler: map 6 ecosystem metrics → 6 tuning parameters. We use:

1. **BeliefSystem**: Heuristics that learn from evidence (like organism cognition)
2. **HealthPredictor**: sklearn SGDRegressor (Kleene convergence to truth)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANTENNAE                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    sense()     ┌──────────────────┐          │
│  │  Organisms   │ ─────────────> │  AntennaReading  │          │
│  │  (Dict)      │                │  (9 dimensions)  │          │
│  └──────────────┘                └────────┬─────────┘          │
│                                           │                     │
│                                           ▼                     │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    get_signal()                       │      │
│  │  ┌──────────────┐         ┌─────────────────┐        │      │
│  │  │ BeliefSystem │ 70%     │ HealthPredictor │ 30%    │      │
│  │  │ (heuristics) │ ──────> │ (sklearn)       │ ─────> │ BLEND│
│  │  └──────────────┘         └─────────────────┘        │      │
│  └──────────────────────────────────────────────────────┘      │
│                                           │                     │
│                                           ▼                     │
│                                  ┌──────────────────┐          │
│                                  │ GovernanceSignal │          │
│                                  │ (6 dimensions)   │          │
│                                  └────────┬─────────┘          │
│                                           │                     │
│                                           ▼                     │
│                            influence()    │                     │
│  ┌──────────────┐  <──────────────────────┘                    │
│  │ ConfigTuner  │                                               │
│  │ (AtomicConfig)│                                              │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## AntennaReading (9 Dimensions)

What the collective perceives at a moment in time:

| Field | Range | Description |
|-------|-------|-------------|
| `population_pressure` | -1 to +1 | Dying ↔ Thriving |
| `fitness_momentum` | -1 to +1 | Declining ↔ Improving |
| `diversity_sense` | 0 to 1 | Monoculture ↔ Diverse |
| `exploration_level` | 0 to 1 | Exploiting ↔ Exploring |
| `learning_rate_feel` | -1 to +1 | Stagnant ↔ Rapid learning |
| `alliance_cohesion` | 0 to 1 | Fragmented ↔ Unified |
| `conflict_intensity` | 0 to 1 | Peaceful ↔ War |
| `resource_abundance` | 0 to 1 | Scarce ↔ Abundant |
| `overall_health` | -1 to +1 | Crisis ↔ Flourishing |

---

## GovernanceSignal (6 Dimensions)

What the Antennae suggests for system tuning:

| Field | Description |
|-------|-------------|
| `survival_threshold_delta` | Adjust minimum fitness for survival |
| `competition_intensity_delta` | Adjust battle/competition intensity |
| `learning_rate_delta` | Adjust neural learning rate |
| `exploration_delta` | Adjust epsilon (exploration vs exploitation) |
| `germination_rate_delta` | Adjust reproduction rate |
| `cooperation_bonus_delta` | Adjust alliance cooperation bonus |

All values are in range [-1, +1] and represent deltas (changes), not absolute values.

---

## BeliefSystem: Heuristics That Learn

The BeliefSystem implements Kleene-style iteration: start with prior beliefs → observe outcomes → update → repeat.

### Prior Beliefs

```python
beliefs = {
    'survival_down_pop_up': Belief(
        cause='survival_threshold_decrease',
        effect='population_increase',
        confidence=0.7
    ),
    'survival_up_quality_up': Belief(
        cause='survival_threshold_increase',
        effect='fitness_increase',
        confidence=0.6
    ),
    'competition_down_diversity_up': Belief(
        cause='competition_decrease',
        effect='diversity_increase',
        confidence=0.6
    ),
    # ... more beliefs
}
```

### Belief Update (Bayesian-ish)

```python
def update(self, confirmed: bool):
    if confirmed:
        self.confirmations += 1
    else:
        self.refutations += 1
    self.confidence = self.confirmations / (self.confirmations + self.refutations)
```

### How Beliefs Weight Heuristics

```python
# Population declining → lower survival threshold
if reading.population_pressure < -0.3:
    conf = self.beliefs.get_confidence('survival_threshold_decrease')
    signal.survival_threshold_delta = -0.3 * sensitivity * conf  # Weighted!
```

---

## HealthPredictor: Kleene Convergence

The HealthPredictor uses sklearn's SGDRegressor for online learning. Each training step is one Kleene iteration toward the true parameter→health mapping.

### How It Works

```python
# Each cycle:
predictor.add_sample(params, health)  # Observe (params, health)
predictor.train()                      # One Kleene iteration

# After enough iterations:
suggestions = predictor.suggest(current_params)  # Gradient-based
```

### Feature Importance

The model learns which parameters matter most:

```python
{
    'survival_threshold': 0.35,    # Most important
    'competition_intensity': 0.25,
    'germination_rate': 0.22,
    'cooperation_bonus': 0.18
}
```

---

## Integration with unified_entry.py

### Initialization (~line 1540)

```python
# Initialize Antennae - collective sensing apparatus
try:
    from reality_simulator.antennae import Antennae
    self.antennae = Antennae(history_size=100)
    self.antennae.sensitivity = 1.0
    self.antennae.signal_cooldown = 10.0  # Don't tune too frequently
    print("[UNIFIED] [ANTENNAE] 🦋 Collective sensing apparatus initialized")
except Exception as e:
    print(f"[UNIFIED] [WARN] Antennae not available: {e}")
    self.antennae = None
```

### Main Loop (~line 3060)

```python
# Antennae collective sensing
if self.antennae:
    try:
        self.antennae.sense(network.organisms, report)
        if config_tuner:
            changes = self.antennae.influence(config_tuner)
    except Exception as e:
        print(f"[UNIFIED] [WARN] Antennae sensing failed: {e}")
```

---

## AtomicConfigSystem Integration

The Antennae requires `adjust_parameter()` method on the ConfigTuner:

```python
def adjust_parameter(self, param_name: str, delta: float, reason: str = "antennae"):
    """
    Adjust a parameter by a delta value.
    
    Args:
        param_name: Name of the parameter to adjust
        delta: Amount to change (positive or negative)
        reason: Why this adjustment is being made
    """
    current = self.get(param_name)
    if current is None:
        return
    
    # Apply delta
    new_value = current + delta
    
    # Clamp to bounds
    atom = self.atoms.get(param_name)
    if atom:
        new_value = max(atom.bounds[0], min(atom.bounds[1], new_value))
    
    self.set(param_name, new_value, reason=reason)
```

---

## Configuration

```json
{
  "antennae": {
    "history_size": 100,
    "sensitivity": 1.0,
    "signal_cooldown": 10.0
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `history_size` | 100 | Readings to remember for trend detection |
| `sensitivity` | 1.0 | How reactive (multiplier on signals) |
| `signal_cooldown` | 10.0 | Seconds between governance signals |

---

## Collective Voting

The organisms themselves can vote on system direction (fitness-weighted):

```python
from reality_simulator.antennae import collective_vote

votes = collective_vote(organisms)
# Returns:
# {
#   'exploration': 0.15,      # High epsilon organisms want more
#   'cooperation': 0.25,      # Alliance members want more
#   'survival_threshold': -0.05  # Older organisms want easier
# }
```

---

## Monitoring & Debugging

### Reading Summary

```python
print(antennae.get_reading_summary())
# [ANTENNAE] 🦋 HEALTHY | pop:+0.15 fit:+0.22 div:0.45
```

### Full State

```python
state = antennae.to_dict()
# {
#   'current_reading': {...},
#   'last_signal': {...},
#   'history_length': 42,
#   'beliefs': {...},
#   'predictor': {'training_steps': 100, 'is_fitted': True, ...}
# }
```

### Belief Inspection

```python
print(antennae.beliefs.to_dict())
# {
#   'survival_down_pop_up': {
#     'cause': 'survival_threshold_decrease',
#     'effect': 'population_increase',
#     'confidence': 0.75,
#     'evidence': '15✓ 5✗'
#   },
#   ...
# }
```

---

## Files

| File | Purpose |
|------|---------|
| `reality_simulator/antennae.py` | Main implementation (666 lines) |
| `reality_simulator/antennae_neural_backup.py` | Old PyTorch version (backup) |
| `reality_simulator/tuning/atomic_config.py` | ConfigTuner with `adjust_parameter()` |
| `unified_entry.py` | Integration (~lines 1540, 3060) |

---

## Future Improvements

1. **Organism-Style Cognition**: Port full skepticism/curiosity systems from organisms
2. **Temporal Discounting**: Weight recent evidence more heavily
3. **Multi-Objective**: Balance competing goals (fitness vs diversity vs stability)
4. **Intervention Logging**: Track all governance actions for causal analysis
