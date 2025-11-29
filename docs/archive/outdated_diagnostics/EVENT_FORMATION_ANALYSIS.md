# Event Formation Analysis - Neural/ML Events

## ✅ Backend Event Formation: **CORRECT**

### Neural Events
- **Component**: `'neural'` ✓
- **Event Types**: `'neural_training'`, `'state_change'` ✓
- **Data Structure**: Properly formed with all required fields ✓
  - `training_steps`: 161
  - `organisms_tracked`: 813
  - `avg_loss`, `avg_epsilon`, etc.

### ML Events
- **Component**: `'ml_analysis'` ✓
- **Event Types**: `'phenotype_emergence'`, `'anomaly_spike'`, `'state_change'` ✓
- **Data Structure**: Properly formed with all required fields ✓
  - `n_clusters`: 5 (phenotype_emergence)
  - `anomaly_ratio`: 0.18 (anomaly_spike)

## 🔧 Issues Found & Fixed

### 1. Component Normalization (FIXED)
**Problem**: Graph endpoint didn't explicitly handle 'neural' and 'ml_analysis' components
**Fix**: Added explicit mapping in `causation_web_ui.py`:
```python
elif 'neural' in component:
    component = 'neural'  # Keep 'neural' for neural system events
elif 'ml' in component or 'analysis' in component:
    component = 'ml_analysis'  # Standardize ML component name
```

### 2. ML Events Have No Causation Links (ISSUE)
**Problem**: ML events (0/4) have no causation links, making them isolated nodes
**Neural Events**: 208/278 have links (good!)
**Root Cause**: ML events may not match causation detection criteria:
- No threshold crossings detected
- No correlations with other events
- No direct relationships defined

**Impact**: Isolated nodes might be:
- Hidden by viewport culling
- Filtered out if "show isolated nodes" is disabled
- Hard to see without connections

## 📊 Current Status

### Event Counts
- **Total Events**: 7,003
- **Neural Events**: 278 (1 neural_training, 277 state_change)
- **ML Events**: 4 (1 phenotype_emergence, 1 anomaly_spike, 2 state_change)

### Causation Links
- **Neural Events with Links**: 208/278 (75%)
- **ML Events with Links**: 0/4 (0%) ⚠️

## 🎯 Recommendations

1. **Force Reload Graph**: Click "Load Full Graph" button in web UI to refresh
2. **Check Filters**: Ensure `filter-neural` and `filter-ml_analysis` checkboxes are checked
3. **View Isolated Nodes**: Check if viewport culling is hiding isolated ML nodes
4. **Add Causation Logic**: Consider adding explicit causation detection for ML events:
   - Link phenotype_emergence to network state changes
   - Link anomaly_spike to organism fitness changes
   - Link ML events to neural training events

## ✅ Verification

Run `python test_event_formation.py` to verify:
- Events are properly formed
- Component names are correct
- Data fields are present

