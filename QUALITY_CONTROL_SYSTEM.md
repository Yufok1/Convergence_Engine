# Quality-Controlled Recursive Expansion System

## Overview

The Quality-Controlled Recursive Expansion System prevents the language system from becoming a "yarn ball" of random associations while enabling meaningful relationship discovery and growth. It implements a three-phase learning curve (exploration → validation → convergence) with adaptive thresholds.

## Key Features

### 1. Relationship Discovery
- Organisms discover new semantic relationships through co-occurrence patterns
- Validation gates ensure only meaningful relationships are accepted
- Discovery cap prevents system thrashing (max 10 per generation by default)

### 2. Validation Framework
- **Semantic Frame Compatibility** (40% weight): Checks if word types can relate
- **Context Coherence** (60% weight): Validates words appear in similar organism states
- **Frequency Validation**: Requires minimum 3 co-occurrences before acceptance

### 3. Time-Based Learning Curve
- **Early Exploration (Gen 0-500)**: High exploration (20%), low confidence bar (0.3)
  - "Find ANY relationships, learn broadly"
- **Mid Validation (Gen 500-1500)**: Moderate exploration (10-15%), rising confidence (0.5-0.6)
  - "Validate what you found"
- **Late Convergence (Gen 1500+)**: Low exploration (5%), high confidence (0.7-0.8)
  - "Use only what works"

### 4. Quality Feedback Loop
- **Success Tracking**: Relationships that lead to good responses get strengthened
  - Confidence increases by 0.1, strength by 0.05
- **Failure Tracking**: Relationships that lead to poor responses get weakened
  - Confidence decreases by 0.15, strength by 0.1 (asymmetric - failure costs more)
- **Neural System Learning** ⭐ NEW: Neural system records relationship success/failure based on generation quality
  - Coherent generation (>50% semantic pairs) → strengthens relationships
  - Garbled generation (<20% semantic pairs) → weakens relationships
  - See [docs/NEURAL_RELATIONSHIP_LEARNING.md](./docs/NEURAL_RELATIONSHIP_LEARNING.md) for details
- **ML System Teaching** ⭐ NEW: ML system strengthens relationships when detecting strong co-occurrences
  - Strong co-occurrence (≥5) + semantic link (≥0.6 strength) → ML records success
  - See `ml_utils.py` semantic analysis for details

### 5. Convergence Mechanisms
- **Periodic Quality Review**: Every 100 generations, system-wide review
  - Strengthens high-quality relationships (success_rate > 0.6)
  - Weakens low-quality relationships (failure_rate > 0.4)
- **Pruning**: Removes very weak relationships
  - Confidence < 0.2
  - Unused for >100 generations
  - Failure rate > 0.7
- **Seeded Protection**: Base 326 concepts and JSON-loaded relationships are NEVER pruned

### 6. VP-Aware Exploration
- High VP (>0.7) temporarily boosts exploration by 50%
- Enables linguistic innovation during system crises

## Configuration Parameters

All parameters are controllable via CRA (Convergence Research Assistant):

### Core Settings
- `enabled` (bool, default: true) - Master toggle
- `min_discovery_count` (1-10, default: 3) - Minimum co-occurrences before accepting relationship
- `min_confidence_threshold` (0.0-1.0, default: 0.3) - Starting confidence threshold
- `confidence_growth_rate` (0.0-0.01, default: 0.0005) - Confidence growth per generation

### Exploration Settings
- `exploration_start` (0.0-1.0, default: 0.2) - Initial exploration rate (20%)
- `exploration_end` (0.0-1.0, default: 0.05) - Final exploration rate (5%)
- `exploration_decay_generations` (100-5000, default: 1000) - Generations to decay from start to end
- `max_discoveries_per_generation` (1-50, default: 10) - Cap on new relationships per generation

### VP Integration
- `vp_boost_exploration` (bool, default: true) - Boost exploration when VP > threshold
- `vp_boost_threshold` (0.0-1.0, default: 0.7) - VP threshold for exploration boost

### Pruning Settings
- `review_frequency` (10-500, default: 100) - Quality review every N generations
- `pruning_confidence_threshold` (0.0-1.0, default: 0.2) - Prune below this confidence
- `pruning_unused_generations` (10-500, default: 100) - Prune if unused for N generations
- `pruning_failure_rate` (0.0-1.0, default: 0.7) - Prune if failure rate > threshold

## CRA Integration

The CRA (Convergence Research Assistant) has full awareness and control of the quality control system:

### Awareness
- Complete knowledge of all 14 quality control parameters
- Understanding of three-phase learning curve
- Knowledge of validation mechanisms and pruning criteria

### Control
- Can tune all 14 parameters via `[[CONFIG_UPDATE: {...}]]` commands
- Example commands provided in CRA system prompt
- Monitoring guidelines for tracking system behavior after changes

### Example CRA Commands

```json
[[CONFIG_UPDATE: {
  "reason": "More relationship discovery",
  "correlation_id": "explore-more",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/knowledge_web/quality_control/exploration_start",
    "value": 0.3
  }]
}]]
```

```json
[[CONFIG_UPDATE: {
  "reason": "Higher quality relationships",
  "correlation_id": "stricter",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/knowledge_web/quality_control/min_confidence_threshold",
    "value": 0.5
  }]
}]]
```

## Monitoring

After quality control config changes, monitor:
- **Discovery rate**: How many new relationships per generation
- **Relationship quality**: Success vs failure rates
- **Pruning rate**: How many low-quality relationships removed
- **Exploration vs exploitation balance**: Is system exploring or converging?
- **Convergence trajectory**: Is system moving toward stable patterns?

## Implementation Status

✅ **Fully Implemented** - All phases complete:
- Phase 1: Confidence & Validation Framework ✅
- Phase 2: Time-Based Learning Curve ✅
- Phase 3: Discovery Triggers & Validation ✅
- Phase 4: Quality Feedback Loop ✅
- Phase 5: Convergence Mechanisms ✅
- Phase 6: Periodic Quality Review ✅
- Phase 7: Configuration ✅

## Files Modified

- `reality_simulator/language/linguistic_knowledge_web.py` - Core implementation
- `reality_simulator/language/language_teacher.py` - Integration with teaching system
- `reality_simulator/language/import_knowledge_base.py` - Mark seeded relationships
- `config.json` - Quality control configuration section
- `causation_web_ui.py` - CRA integration (CONFIG_GUARDRAILS + system prompt)
- `CRA_LINGUISTIC_AWARENESS_INTEGRATION.md` - Updated with quality control info

## Related Documentation

- `RECURSIVE_EXPANSION_DESIGN.md` - Original design document
- `CRA_LINGUISTIC_AWARENESS_INTEGRATION.md` - CRA integration details
- `KNOWLEDGE_BASE_CAPABILITIES.md` - Knowledge base overview

