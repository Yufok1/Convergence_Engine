# Convergence Factor Test Guide

## What We're Testing

**Question**: Is the collapse at 500 organisms truly deterministic, or is it a proxy for something else?

**Hypothesis**: Collapse might be driven by:
1. **Organism count** (always at N organisms) - CURRENT ASSUMPTION
2. **Average degree** (always at X connections per organism)
3. **Network density** (always at Y% of possible connections)
4. **Topology formation** (depends on structure, not simple metrics)

## Test Configurations

| Name | Organisms | Max Connections | Expected? | Why |
|------|-----------|-----------------|-----------|-----|
| Baseline: 500 @ 5 | 500 | 5 | ✅ Yes | Current known working config |
| Linear: 300 @ 3 | 300 | 3 | ❓ Unknown | Linear scaling attempt |
| Same Capacity: 250 @ 10 | 250 | 10 | ❓ Unknown | Same total connection capacity (2500) |
| Same Degree: 1000 @ 5 | 1000 | 5 | ❓ Unknown | Same average degree, different size |
| Lower Degree: 500 @ 3 | 500 | 3 | ❓ Unknown | Lower degree, same size |
| Higher Degree: 200 @ 10 | 200 | 10 | ❓ Unknown | Higher degree, smaller size |
| Extreme: 100 @ 20 | 100 | 20 | ❓ Unknown | Very high degree, small size |

## What to Measure

### At Collapse (when all conditions met):
1. **Organism count** - How many organisms when collapse occurs?
2. **Connection count** - Total connections in network
3. **Average degree** - Connections per organism (2×connections/organisms)
4. **Network density** - Actual connections / possible connections
5. **Clustering coefficient** - Should be > 0.5
6. **Modularity** - Should be < 0.3
7. **Average path length** - Should be < 3.0

### Bottleneck Analysis:
Track when EACH condition is met separately:
- Generation when organism_count >= threshold
- Generation when clustering > 0.5
- Generation when modularity < 0.3
- Generation when path_length < 3.0

**Which condition is met LAST?** That's the bottleneck.

## How to Run

### Full Test Suite (All Experiments):
```bash
python test_convergence_factors.py
```

This will:
- Run all 7 experiment configurations
- Track metrics for each
- Generate analysis report
- Save results to `convergence_test_results.json`

### Single Experiment (Manual):
```python
from test_convergence_factors import ConvergenceFactorTester, ExperimentConfig

tester = ConvergenceFactorTester()
config = ExperimentConfig(
    name="Test: 300 @ 3",
    max_organisms=400,
    max_connections_per_organism=3,
    collapse_threshold=300
)
result = tester.run_experiment(config)
```

## What to Look For

### If Organism-Count Driven:
- **Pattern**: Collapse always at ~500 organisms (or scaled threshold)
- **Evidence**: Low variance in organism_count_at_collapse across experiments
- **Range**: < 50 organisms variation

### If Degree-Driven:
- **Pattern**: Collapse always at ~5 average degree (or scaled)
- **Evidence**: Low variance in average_degree_at_collapse
- **Range**: < 0.5 degree variation

### If Density-Driven:
- **Pattern**: Collapse always at same network density
- **Evidence**: Low variance in network_density_at_collapse
- **Range**: < 0.01 density variation

### If Topology-Driven:
- **Pattern**: Collapse depends on structure formation, not simple metrics
- **Evidence**: High variance in all metrics, but consistent topology indicators
- **Bottleneck**: Usually clustering or modularity is the last condition

## Expected Output

The script will print:
1. Real-time progress for each experiment
2. When each collapse condition is met
3. Final analysis report with:
   - Statistics for each metric at collapse
   - Bottleneck analysis
   - Conclusion about what drives collapse

## Interpretation

### If it's a "ruse" (not truly organism-count driven):
- You'll see collapse at different organism counts
- But consistent average degree or density
- This means the 500 threshold is a proxy, not the real driver

### If it's truly organism-count driven:
- Collapse always at ~500 (or scaled threshold)
- High variance in degree/density
- This means organism count IS the real driver

## Time Estimates

Each experiment may take:
- **Fast configs** (low organisms): 2-5 minutes
- **Medium configs** (500 organisms): 5-10 minutes  
- **Large configs** (1000 organisms): 10-20 minutes

**Total time**: ~1-2 hours for all experiments

## Quick Test (Just Baseline)

If you want to verify the baseline first:
```python
from test_convergence_factors import ConvergenceFactorTester, ExperimentConfig

tester = ConvergenceFactorTester()
config = ExperimentConfig(
    name="Baseline Test",
    max_organisms=600,
    max_connections_per_organism=5,
    collapse_threshold=500
)
result = tester.run_experiment(config)
print(f"Collapsed: {result is not None}")
if result:
    print(f"At {result.organism_count} organisms, {result.average_degree:.2f} avg degree")
```

