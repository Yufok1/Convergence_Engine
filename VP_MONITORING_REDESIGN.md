# VP Monitoring System Redesign

## Overview

The VP (Violation Pressure) Monitoring System has been redesigned to address immediate saturation issues during the Genesis phase. The redesign includes diagnostic capabilities, stabilization, component decomposition, and adaptive thresholds while maintaining full backward compatibility.

## Problem Statement

The original VP system immediately saturated at 1.0 (VP4) during Genesis phase when it should be in VP0-VP1 range (0.0-0.5). This prevented meaningful study and monitoring of system behavior.

## Solution Architecture

The redesign consists of four phases, all implemented with feature flags to ensure backward compatibility:

### Phase 1: Diagnostic Layer

**Purpose:** Identify what's driving VP saturation without changing calculation logic.

**Features:**
- `VPDiagnostics` class for detailed logging
- Component breakdown logging to `data/logs/vp_diagnostics.log`
- `get_vp_diagnostics()` method for analysis
- Logs trait values, envelope centers, deviations, per-trait VPs, normalization factors

**Configuration:**
```json
{
  "vp_monitoring": {
    "diagnostics_enabled": false
  }
}
```

**Usage:**
```python
# Enable diagnostics
vp_monitor = ViolationMonitor(diagnostics_enabled=True)

# Calculate VP (logs diagnostic data automatically)
total_vp, breakdown = vp_monitor.compute_violation_pressure(traits)

# Get diagnostic breakdown
diagnostics = vp_monitor.get_vp_diagnostics(traits)
```

### Phase 2: VP Stabilization Layer

**Purpose:** Prevent immediate jumps to maximum VP by smoothing transitions.

**Features:**
- `VPStabilizer` class with weighted moving average
- Maximum jump limiting (configurable, default 0.1 per calculation)
- Smoothing factor (configurable, default 0.3)
- History buffer (last 10 VP values)

**Configuration:**
```json
{
  "vp_monitoring": {
    "stabilization_enabled": false,
    "stabilization": {
      "max_jump": 0.1,
      "smoothing_factor": 0.3,
      "history_size": 10
    }
  }
}
```

**Usage:**
```python
# Enable stabilization
vp_monitor = ViolationMonitor(
    stabilization_enabled=True,
    max_vp_jump=0.1,
    smoothing_factor=0.3
)

# VP values are automatically stabilized
total_vp, breakdown = vp_monitor.compute_violation_pressure(traits)
```

### Phase 3: Component Decomposition

**Purpose:** Break VP into weighted components to identify saturation sources.

**Features:**
- `VPComponentCalculator` class
- Weighted component breakdown:
  - `trait_divergence` (25%): Average deviation from stability centers
  - `network_coherence` (20%): Coherence of network traits
  - `phase_mismatch` (15%): Mismatch in prosocial traits
  - `evolution_pressure` (20%): Pressure from meta-traits
  - `quantum_entropy` (20%): Entropy in trait distribution
- Weighted geometric mean prevents single component domination
- Sigmoid smoothing applied to components

**Configuration:**
```json
{
  "vp_monitoring": {
    "component_decomposition_enabled": false,
    "component_weights": {
      "trait_divergence": 0.25,
      "network_coherence": 0.20,
      "phase_mismatch": 0.15,
      "evolution_pressure": 0.20,
      "quantum_entropy": 0.20
    }
  }
}
```

**Usage:**
```python
# Enable component decomposition
vp_monitor = ViolationMonitor(component_decomposition_enabled=True)

# Use decomposed calculation
total_vp, per_trait, component_breakdown = vp_monitor.compute_violation_pressure_decomposed(traits)

# component_breakdown contains:
# {
#   'trait_divergence': 0.3,
#   'network_coherence': 0.2,
#   'phase_mismatch': 0.1,
#   'evolution_pressure': 0.2,
#   'quantum_entropy': 0.15
# }
```

### Phase 4: Adaptive Thresholds

**Purpose:** Make thresholds adapt based on system phase for more accurate classification.

**Features:**
- `AdaptiveThresholdManager` class
- Phase-aware thresholds:
  - Genesis phase: More sensitive (lower thresholds)
  - Sovereign phase: Less sensitive (higher thresholds)
- Historical variance-based adjustments
- Automatic threshold calculation from last 100 VP values

**Configuration:**
```json
{
  "vp_monitoring": {
    "adaptive_thresholds_enabled": false
  }
}
```

**Usage:**
```python
# Enable adaptive thresholds
vp_monitor = ViolationMonitor(adaptive_thresholds_enabled=True)

# Pass system phase when calculating VP
total_vp, breakdown = vp_monitor.compute_violation_pressure(
    traits,
    system_phase='genesis'  # or 'sovereign'
)
```

## Complete Configuration Example

```json
{
  "vp_monitoring": {
    "diagnostics_enabled": false,
    "stabilization_enabled": false,
    "adaptive_thresholds_enabled": false,
    "component_decomposition_enabled": false,
    "stabilization": {
      "max_jump": 0.1,
      "smoothing_factor": 0.3,
      "history_size": 10
    },
    "component_weights": {
      "trait_divergence": 0.25,
      "network_coherence": 0.20,
      "phase_mismatch": 0.15,
      "evolution_pressure": 0.20,
      "quantum_entropy": 0.20
    }
  }
}
```

## Backward Compatibility

**All new features are disabled by default.** Existing code continues to work unchanged:

- `compute_violation_pressure()` signature unchanged (system_phase is optional)
- Default behavior matches original implementation
- All new methods are additions, not replacements
- Configuration-driven activation

## Integration

The VP monitoring system is automatically initialized with configuration from `config.json` in:

- `explorer/main.py`: Initializes ViolationMonitor with config
- `unified_entry.py`: Uses VP monitor from explorer controller

Phase awareness is automatically included when calling `compute_violation_pressure()`:

```python
# In explorer/main.py
current_phase = 'genesis' if self.breath_engine.phase == 'genesis' else 'sovereign'
vp, breakdown = self.vp_monitor.compute_violation_pressure(traits, system_phase=current_phase)
```

## Diagnostic Logging

When diagnostics are enabled, detailed breakdowns are logged to `data/logs/vp_diagnostics.log`:

```
14:23:45.123|vp_diagnostics|trait_breakdown|{"trait_name": "intimacy", "trait_value": 0.8, ...}
14:23:45.234|vp_diagnostics|calculation_summary|{"total_vp": 0.45, "trait_count": 5, ...}
```

## Testing

Comprehensive tests are available in `kernel/test_vp_monitoring_redesign.py`:

- Backward compatibility tests
- Diagnostic tests
- Stabilization tests
- Component decomposition tests
- Adaptive threshold tests
- Integration tests

Run tests:
```bash
python kernel/test_vp_monitoring_redesign.py
```

## Rollout Strategy

1. **Week 1:** Enable diagnostics to identify root cause
2. **Week 2:** Enable stabilization if needed
3. **Week 3:** Enable component decomposition for analysis
4. **Week 4:** Enable adaptive thresholds for fine-tuning
5. **Week 5:** Full integration and optimization

## Success Criteria

✅ VP no longer immediately saturates at 1.0 during Genesis  
✅ VP shows gradual progression through VP0-VP4 range  
✅ Diagnostic data identifies root cause of saturation  
✅ System remains stable with new monitoring enabled  
✅ All existing functionality continues to work  
✅ Performance impact < 5% with all features enabled

## Files Modified

- `kernel/violation_pressure_calculation.py`: Core implementation
- `config.json`: Configuration section
- `explorer/main.py`: Integration with phase awareness
- `unified_entry.py`: VP monitor access (via controller)

## Documentation

- This file: `VP_MONITORING_REDESIGN.md`
- Updated: `VP_THRESHOLD_CLARIFICATION.md` (adaptive thresholds)
- Updated: `ARCHITECTURE.md` (VP monitoring architecture)
- Updated: `README.md` (configuration examples)

