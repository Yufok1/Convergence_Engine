# 🧠 Self-Perception System

**Organisms that can feel their own dynamics**

---

## Overview

The Self-Perception System extends the organism feature vector from 25D to 28D, adding three introspective features that allow organisms to perceive their own behavioral patterns and relationship to the collective attractor landscape.

This creates a **closed feedback loop** where organisms don't just act in the world—they can *feel* the consequences of their actions reflected in their own internal dynamics.

---

## Feature Vector (28D)

| Index | Name | Range | Description |
|-------|------|-------|-------------|
| 0-24 | Base features | Various | Environment, resources, fitness, connections, actions, etc. |
| **25** | `oscillation_entropy` | 0.0-1.0 | "How chaotic am I?" - Shannon entropy of recent action distribution |
| **26** | `coherence_frequency` | 0.0-1.0 | "Am I trapped?" - Frequency of repeated action patterns |
| **27** | `attractor_proximity` | 0.0-1.0 | "How close to stability?" - Distance to nearest known fixed point |

### Feature 25: Oscillation Entropy

Measures how unpredictable the organism's recent actions are:
- **Low entropy (0.0-0.3)**: Repetitive behavior, stuck in patterns
- **Medium entropy (0.3-0.7)**: Balanced exploration/exploitation
- **High entropy (0.7-1.0)**: Chaotic, random behavior

```python
# Computed from action history
action_counts = Counter(recent_actions[-20:])
probabilities = [c/sum(counts) for c in action_counts.values()]
entropy = -sum(p * log2(p) for p in probabilities if p > 0)
oscillation_entropy = entropy / max_entropy  # Normalized to 0-1
```

### Feature 26: Coherence Frequency

Detects if the organism is trapped in behavioral loops:
- **Low coherence (0.0-0.3)**: Free, varied behavior
- **Medium coherence (0.3-0.6)**: Some patterns emerging
- **High coherence (0.6-1.0)**: Trapped in repetitive cycles

### Feature 27: Attractor Proximity

Distance to the nearest known stable configuration (fixed point) in the collective magnetism field:
- **Low proximity (0.0-0.3)**: Very close to a known attractor (stable)
- **Medium proximity (0.3-0.6)**: In basin of attraction (converging)
- **High proximity (0.6-1.0)**: Far from any attractor (exploring)

---

## Attractor Landscape Integration

The `AttractorLandscape` system observes the collective magnetism field and detects:

### Fixed Points (Kleene Fixed Points)
Stable configurations where the population settles:
```python
# Detected when variance < threshold for N consecutive snapshots
if coherence_variance < 0.02 and entropy_variance < 0.02:
    # for 5+ snapshots → Fixed point confirmed
```

### Bifurcations
Sudden shifts in the landscape:
```python
# Detected when metrics jump suddenly
if abs(coherence_delta) > 0.15 or abs(entropy_delta) > 0.20:
    emit('bifurcation_detected', {...})
```

### Events
| Event | Trigger | System Response |
|-------|---------|-----------------|
| `bifurcation_detected` | Sudden landscape shift | Boost epsilon, increase mutation |
| `fixed_point_reached` | Population stabilizes | Decay epsilon, record success |
| `fixed_point_broken` | Stability lost | Increase mutation for adaptation |

---

## Reward Shaping

The trainer uses self-perception features to shape rewards:

```json
"self_perception": {
  "enabled": true,
  "oscillation_entropy_threshold": 0.7,
  "oscillation_chaos_penalty": -0.1,
  "coherence_frequency_threshold": 0.6,
  "coherence_trap_penalty": -0.15,
  "proximity_near_threshold": 0.3,
  "proximity_near_bonus": 0.05,
  "proximity_medium_threshold": 0.6,
  "proximity_medium_bonus": 0.02
}
```

### Reward Logic
```python
# Penalize chaos (high oscillation entropy)
if oscillation_entropy > 0.7:
    reward -= 0.1 * (oscillation_entropy - 0.7) / 0.3

# Penalize being trapped (high coherence frequency)
if coherence_frequency > 0.6:
    reward -= 0.15 * (coherence_frequency - 0.6) / 0.4

# Reward approaching attractors
if 0.3 < attractor_proximity < 0.6:
    reward += 0.05  # Exploring basin
elif attractor_proximity < 0.3:
    reward += 0.02  # At attractor (stable but might be stuck)
```

---

## Hopfield Network Inspiration

The attractor landscape draws from **Hopfield networks** and **dynamical systems theory**:

- **Fixed Points**: Like memories in a Hopfield network—stable configurations the system naturally converges to
- **Basins of Attraction**: Regions that flow toward a fixed point
- **Bifurcations**: Phase transitions where the landscape topology changes

Organisms learn to navigate toward known attractors while avoiding getting permanently trapped at any single one.

---

## Configuration

### config.json
```json
"attractor_landscape": {
  "enabled": true,
  "window_size": 20,
  "fixed_point_persistence": 5,
  "fixed_point_variance_threshold": 0.02,
  "bifurcation_coherence_threshold": 0.15,
  "bifurcation_entropy_threshold": 0.20,
  "resonance_similarity_threshold": 0.1
}
```

### Case Study Tuning

**Creative Specialist** (high exploration):
```json
"self_perception": {
  "oscillation_chaos_penalty": -0.08,    // Reduced penalty
  "coherence_trap_penalty": -0.12,       // Less harsh
  "proximity_near_bonus": 0.04           // Lower stability reward
}
```

**Convergent Specialist** (high stability):
```json
"self_perception": {
  "oscillation_chaos_penalty": -0.15,    // Strong penalty
  "coherence_trap_penalty": -0.20,       // Harsh on loops
  "proximity_near_bonus": 0.10           // High stability reward
}
```

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLOSED LOOP                                   │
│                                                                      │
│  Organism acts ──► Magnetism field changes                          │
│       ▲                      │                                       │
│       │                      ▼                                       │
│       │          AttractorLandscape.observe()                       │
│       │                      │                                       │
│       │                      ▼                                       │
│       │          Detect fixed points / bifurcations                 │
│       │                      │                                       │
│       │                      ├──► Events fire ──► System adapts     │
│       │                      │                                       │
│       │                      ▼                                       │
│       │          Feature 28 = proximity                             │
│       │                      │                                       │
│       │                      ▼                                       │
│       │          Organism perceives state                           │
│       │                      │                                       │
│       │                      ▼                                       │
│       │          Trainer shapes reward                              │
│       │                      │                                       │
│       │                      ▼                                       │
│       │          Gradient updates weights                           │
│       │                      │                                       │
│       └──────────────────────┘                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- [NEURAL_SYSTEM_README.md](../NEURAL_SYSTEM_README.md) - Neural architecture overview
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [CONFIG_REFERENCE.md](../CONFIG_REFERENCE.md) - Configuration options
- [CHANGELOG.md](../CHANGELOG.md) - Version history
