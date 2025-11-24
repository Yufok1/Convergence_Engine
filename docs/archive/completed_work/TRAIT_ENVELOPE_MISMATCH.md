# Critical Issue: Trait-Envelope Mismatch Causing VP4

## Problem Summary

The CRA's analysis identified trait values, but there's a **fundamental mismatch** between:
1. **Traits being collected** from Reality Simulator
2. **Stability envelopes defined** in ViolationMonitor

## Actual Traits Being Collected

From `explorer/main.py` lines 416-419:
```python
traits['organism_count'] = float(org_count)  # Raw count (e.g., 400)
traits['modularity'] = network.metrics.modularity  # 0.0-1.0
traits['clustering_coefficient'] = network.metrics.clustering_coefficient  # 0.0-1.0
traits['average_path_length'] = network.metrics.average_path_length  # Any positive number
```

## Stability Envelopes Defined

From `kernel/violation_pressure_calculation.py` lines 71-99:
- `violationpressure` (center=0.0, radius=0.25)
- `completionpressure` (center=0.0, radius=0.3)
- `convergencestability` (center=0.8, radius=0.15)
- `reflectionindex` (center=0.7, radius=0.2)
- `intimacy` (center=0.6, radius=0.3)
- `commitment` (center=0.7, radius=0.25)
- `caregiving` (center=0.65, radius=0.3)
- `attunement` (center=0.6, radius=0.25)
- `lineagepreference` (center=0.55, radius=0.35)

**NONE of these match the Reality Simulator traits!**

## What Happens When Traits Don't Match

From `violation_pressure_calculation.py` line 118:
```python
envelope = self.stability_envelopes.get(trait_name, StabilityEnvelope())
```

When a trait doesn't have a defined envelope, it uses the **default** `StabilityEnvelope()`:
- `center: float = 0.5` (default)
- `radius: float = 0.25` (default)
- `compression_factor: float = 1.0` (default)

## VP Calculation Impact

From `violation_pressure_calculation.py` lines 164-176:
```python
deviation = abs(trait_value - envelope.center)
normalized_radius = envelope.radius * envelope.compression_factor
vp = deviation / normalized_radius  # If radius > 0
```

### Example Calculations (Using Default Envelope):

1. **`organism_count = 400`**:
   - Deviation: |400 - 0.5| = 399.5
   - Normalized radius: 0.25 * 1.0 = 0.25
   - VP = 399.5 / 0.25 = **1,598.0** (clamped to 10.0 max)
   - **This alone would cause VP4!**

2. **`modularity = 0.563`**:
   - Deviation: |0.563 - 0.5| = 0.063
   - VP = 0.063 / 0.25 = **0.252** (VP1)

3. **`clustering_coefficient = 0.154`**:
   - Deviation: |0.154 - 0.5| = 0.346
   - VP = 0.346 / 0.25 = **1.384** (clamped to 10.0, but contributes heavily)

4. **`average_path_length`** (could be 5.0):
   - Deviation: |5.0 - 0.5| = 4.5
   - VP = 4.5 / 0.25 = **18.0** (clamped to 10.0)

## Root Cause

**The VP monitor expects traits in [0.0, 1.0] range with appropriate envelopes, but:**
- `organism_count` is a raw count (hundreds)
- `average_path_length` is an unbounded positive number
- These traits are **not normalized** before VP calculation
- **No stability envelopes are defined** for Reality Simulator traits

## Solution

We need to:

1. **Define proper stability envelopes** for Reality Simulator traits
2. **Normalize trait values** to [0.0, 1.0] range OR define envelopes with appropriate centers/radii
3. **Map trait names** correctly (or use trait hub translation)

### Proposed Stability Envelopes for Reality Simulator Traits

```python
# Normalized organism count (assuming max 1000 organisms)
self.stability_envelopes["organism_count"] = StabilityEnvelope(
    center=0.4,  # 400/1000 = 0.4 (normalized)
    radius=0.2,  # Allow 200-600 organisms (0.2-0.6 normalized)
    compression_factor=1.0
)

# Modularity (already 0.0-1.0)
self.stability_envelopes["modularity"] = StabilityEnvelope(
    center=0.3,  # Target moderate modularity
    radius=0.2,  # Allow 0.1-0.5 range
    compression_factor=1.0
)

# Clustering coefficient (already 0.0-1.0)
self.stability_envelopes["clustering_coefficient"] = StabilityEnvelope(
    center=0.2,  # Target moderate clustering
    radius=0.15,  # Allow 0.05-0.35 range
    compression_factor=1.0
)

# Average path length (needs normalization)
# Assuming max path length of 10, normalize to [0.0, 1.0]
self.stability_envelopes["average_path_length"] = StabilityEnvelope(
    center=0.5,  # Target path length of 5 (normalized)
    radius=0.3,  # Allow 2-8 path length (0.2-0.8 normalized)
    compression_factor=1.0
)
```

## Immediate Fix Required

1. **Add stability envelopes** for Reality Simulator traits in `ViolationMonitor._initialize_default_envelopes()`
2. **Normalize trait values** before passing to VP monitor (or handle normalization in VP calculation)
3. **Verify trait names** match between collection and envelope definitions

## Status

🔴 **CRITICAL** - This is the root cause of VP4 during Genesis. The system is calculating VP using default envelopes (center=0.5, radius=0.25) for traits that are completely out of range (like organism_count=400).

