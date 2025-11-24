# Systematic Issue Resolution Plan
## Working with CRA to Fix Critical Preflight Issues

**Status:** 🔴 SYSTEM IS STOPPED - Historical Data Analysis  
**CRA Awareness:** ✅ YES - CRA receives explicit "SYSTEM IS STOPPED" status header

---

## Issue Resolution Workflow

We'll work through each issue systematically, using the CRA to:
1. **Investigate** - Deep dive into root causes
2. **Diagnose** - Identify specific code locations and data flows
3. **Fix** - Implement solutions
4. **Validate** - Verify fixes work

---

## Issue #1: VP4 During Genesis Phase (CRITICAL)

### Current State
- **VP Value:** 1.0 (VP4 classification)
- **Expected:** VP0-VP1 (0.0-0.25) during Genesis
- **Impact:** System thinks it's in collapse state before launch

### Investigation Questions for CRA:
1. **What trait values are causing high VP?**
   - Which traits are being passed to VP monitor?
   - What are their actual values vs. stability centers?
   - Which trait has the highest individual VP contribution?

2. **Are stability envelopes appropriate?**
   - Current default: `center=0.0, radius=0.25, compression=2.0` for violationpressure
   - Formula: `VP = |actual - center| / (radius * compression)`
   - If trait value = 0.5, center = 0.0, radius = 0.25, compression = 2.0:
     - VP = |0.5 - 0.0| / (0.25 * 2.0) = 0.5 / 0.5 = 1.0 ✓ (This matches!)

3. **Is this a calibration issue or real system stress?**
   - Are trait values actually deviating from expected ranges?
   - Or are stability envelopes too strict for Genesis phase?

### Action Plan:
**Step 1:** Ask CRA to identify which traits are contributing to VP=1.0
**Step 2:** Check if trait values are reasonable for Genesis phase
**Step 3:** Decide: Recalibrate envelopes OR fix trait values
**Step 4:** Implement phase-aware VP thresholds (Genesis allows higher VP)

### Stability Envelope Analysis:
```python
# Current default for "violationpressure" trait:
center=0.0, radius=0.25, compression_factor=2.0

# VP calculation:
VP = |trait_value - 0.0| / (0.25 * 2.0)
VP = |trait_value| / 0.5

# To get VP=1.0:
1.0 = |trait_value| / 0.5
|trait_value| = 0.5

# So if any trait value is 0.5 or higher, VP reaches 1.0+
```

**Question:** Are trait values of 0.5+ normal during Genesis? If yes, envelopes need recalibration.

---

## Issue #2: Modularity = 0.0 (CRITICAL)

### Current State
- **Modularity:** 0.0 (should be 0.3-0.7 for healthy networks)
- **Root Cause:** Fragile calculation that fails silently

### Investigation Questions for CRA:
1. **Is the calculation actually failing?**
   - Check if NetworkX community detection is throwing errors
   - Verify network graph structure (is it too sparse?)
   - Check if `nx.community` module is available

2. **What's the actual network structure?**
   - How many connected components?
   - Are there any communities at all?
   - Is the graph completely disconnected?

### Action Plan:
**Step 1:** Ask CRA to check network graph structure
**Step 2:** Replace fragile calculation with proper NetworkX modularity
**Step 3:** Add error logging to catch calculation failures
**Step 4:** Handle sparse/disconnected graphs gracefully

### Code Fix Required:
```python
# Current (fragile):
communities = list(nx.community.greedy_modularity_communities(network_graph))
self.modularity = len(communities) / len(network_graph)  # Wrong!

# Should be:
try:
    communities = list(nx.community.greedy_modularity_communities(network_graph))
    if len(network_graph) > 0 and len(communities) > 0:
        self.modularity = nx.community.modularity(network_graph, communities)
    else:
        self.modularity = 0.0  # No communities = no modularity
except Exception as e:
    logger.warning(f"Modularity calculation failed: {e}")
    self.modularity = 0.0
```

---

## Issue #3: Organism/Population Mismatch (CRITICAL)

### Current State
- **Network Organisms:** 519
- **Evolution Population:** 400
- **Mismatch:** +119 "ghost organisms"

### Investigation Questions for CRA:
1. **How are organisms being added/removed?**
   - When are organisms added to network?
   - When are organisms removed from evolution population?
   - Is there a removal mechanism for network organisms?

2. **What's the lifecycle?**
   - Do organisms persist in network after being removed from evolution?
   - Are old organisms being pruned?
   - Is there a max_organisms limit being enforced?

### Action Plan:
**Step 1:** Ask CRA to trace organism lifecycle (add/remove events)
**Step 2:** Implement synchronization: remove network organisms when removed from population
**Step 3:** Add periodic cleanup to remove orphaned organisms
**Step 4:** Verify organism counts match after fix

### Code Fix Required:
```python
# After evolution step, synchronize:
population_ids = {org.species_id for org in evolution.population}
network_ids = set(network.organisms.keys())
orphaned_ids = network_ids - population_ids

# Remove orphaned organisms
for org_id in orphaned_ids:
    network.remove_organism(org_id)
    logger.debug(f"Removed orphaned organism {org_id} from network")
```

---

## Issue #4: Fitness = 1.0 at Generation 103 (WARNING)

### Current State
- **Best Fitness:** 1.0 (perfect score)
- **Generation:** 103 / 1000
- **Expected:** 0.15-0.25 at generation 103

### Investigation Questions for CRA:
1. **Is this legitimate convergence?**
   - What are the fitness targets?
   - Are they too easy to achieve?
   - Is the population actually diverse or all identical?

2. **Is diversity being maintained?**
   - What's the fitness variance?
   - Are mutations happening?
   - Is selection too aggressive?

### Action Plan:
**Step 1:** Ask CRA to analyze fitness distribution (not just best)
**Step 2:** Check fitness targets difficulty
**Step 3:** Add diversity tracking and warnings
**Step 4:** Consider adding diversity penalty to fitness

---

## Issue #5: Clustering Coefficient = 0.0 (WARNING)

### Current State
- **Clustering:** 0.0 (no triangles in network)
- **Connections/Organism:** 0.667 (sparse)
- **Expected:** 0.1-0.5 for healthy networks

### Investigation Questions for CRA:
1. **Is this expected for sparse networks?**
   - With 0.667 connections/organism, low clustering is normal
   - But 0.0 suggests NO triangles at all
   - Is connection formation logic working?

2. **Is clustering_bias being applied?**
   - Code shows `clustering_bias = 0.8` (should favor triangles)
   - Is this parameter actually used in connection formation?

### Action Plan:
**Step 1:** Ask CRA to verify connection formation logic
**Step 2:** Check if clustering_bias is being applied
**Step 3:** Verify if 0.0 clustering is expected for this network density
**Step 4:** If not expected, fix connection formation to create triangles

---

## Next Steps

1. **Start with Issue #1 (VP4)** - Most critical, affects system behavior
2. **Use CRA to investigate** - Ask specific questions about trait values
3. **Implement fix** - Based on CRA's findings
4. **Move to next issue** - Repeat process

**Ready to begin?** Ask the CRA: "For Issue #1 (VP4 during Genesis), can you identify which specific trait values are being passed to the violation pressure monitor, and what their individual VP contributions are?"

