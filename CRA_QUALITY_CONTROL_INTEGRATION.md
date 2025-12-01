# CRA Quality Control System Integration

## Summary

The CRA (Convergence Research Assistant) now has **complete awareness and control** over the Quality-Controlled Recursive Expansion System. This system prevents the language system from becoming a "yarn ball" of random associations while enabling meaningful relationship discovery and growth.

## What CRA Knows

### System Understanding
- **Three-Phase Learning Curve**: 
  - Early Exploration (Gen 0-500): High exploration (20%), low confidence (0.3)
  - Mid Validation (Gen 500-1500): Moderate exploration (10-15%), rising confidence (0.5-0.6)
  - Late Convergence (Gen 1500+): Low exploration (5%), high confidence (0.7-0.8)

- **Validation Mechanisms**:
  - Semantic frame compatibility (40% weight)
  - Context coherence (60% weight)
  - Frequency validation (minimum 3 co-occurrences)

- **Quality Feedback**:
  - Success tracking strengthens relationships
  - Failure tracking weakens relationships (asymmetric - failure costs more)

- **Convergence Mechanisms**:
  - Periodic quality review every 100 generations
  - Pruning of low-quality relationships
  - Seeded protection (base concepts never pruned)

## What CRA Can Control

### All 14 Quality Control Parameters

1. **Core Settings**:
   - `enabled` - Master toggle
   - `min_discovery_count` - Minimum co-occurrences (1-10, default: 3)
   - `min_confidence_threshold` - Starting confidence (0.0-1.0, default: 0.3)
   - `confidence_growth_rate` - Confidence growth per generation (0.0-0.01, default: 0.0005)

2. **Exploration Settings**:
   - `exploration_start` - Initial exploration rate (0.0-1.0, default: 0.2)
   - `exploration_end` - Final exploration rate (0.0-1.0, default: 0.05)
   - `exploration_decay_generations` - Decay speed (100-5000, default: 1000)
   - `max_discoveries_per_generation` - Discovery cap (1-50, default: 10)

3. **VP Integration**:
   - `vp_boost_exploration` - Enable VP boost (bool, default: true)
   - `vp_boost_threshold` - VP threshold (0.0-1.0, default: 0.7)

4. **Pruning Settings**:
   - `review_frequency` - Quality review frequency (10-500, default: 100)
   - `pruning_confidence_threshold` - Prune below this (0.0-1.0, default: 0.2)
   - `pruning_unused_generations` - Prune if unused (10-500, default: 100)
   - `pruning_failure_rate` - Prune if failure rate exceeds (0.0-1.0, default: 0.7)

## Example CRA Commands

### Increase Exploration
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

### Stricter Validation
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

### Faster Convergence
```json
[[CONFIG_UPDATE: {
  "reason": "Converge sooner",
  "correlation_id": "fast-converge",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/knowledge_web/quality_control/exploration_decay_generations",
    "value": 500
  }]
}]]
```

### More Discoveries
```json
[[CONFIG_UPDATE: {
  "reason": "Allow more relationship discovery",
  "correlation_id": "more-discovery",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/knowledge_web/quality_control/max_discoveries_per_generation",
    "value": 20
  }]
}]]
```

## Monitoring Guidelines

After quality control config changes, CRA should monitor:

1. **Discovery Rate**: How many new relationships per generation
2. **Relationship Quality**: Success vs failure rates
3. **Pruning Rate**: How many low-quality relationships removed
4. **Exploration vs Exploitation Balance**: Is system exploring or converging?
5. **Convergence Trajectory**: Is system moving toward stable patterns?

## Alignment Status

✅ **Fully Aligned** - No alignment issues:
- CRA has complete awareness of quality control system
- All 14 parameters are in CONFIG_GUARDRAILS
- System prompt includes comprehensive documentation
- Example commands provided
- Monitoring guidelines included

## Files Modified

- `causation_web_ui.py`: 
  - Added 14 quality control settings to CONFIG_GUARDRAILS
  - Enhanced system prompt with quality control documentation
- `CRA_LINGUISTIC_AWARENESS_INTEGRATION.md`: Updated with quality control info
- `QUALITY_CONTROL_SYSTEM.md`: New comprehensive documentation

## Related Documentation

- `QUALITY_CONTROL_SYSTEM.md` - Complete system documentation
- `CRA_LINGUISTIC_AWARENESS_INTEGRATION.md` - CRA integration details
- `RECURSIVE_EXPANSION_DESIGN.md` - Original design document

