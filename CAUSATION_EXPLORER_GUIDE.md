# 🔬 Causation Explorer - Curiosity Trail System

**Interactive tool for exploring "why did this happen?" and "what did this cause?"**

---

## Overview

The Causation Explorer is a scientific exploration tool that lets you follow curiosity trails through your system data. Instead of static visualizations, it provides interactive exploration of cause-effect relationships.

---

## Key Features

### 1. Click Any Event → See What Caused It
- Click "network collapsed" → see all contributing factors
- Click "VP dropped to 0.25" → see what triggered it
- Click "breath depth increased" → see upstream causes

### 2. Click Any Metric → See What It Affected
- Click "modularity" → see all events it influenced
- Click "organism_count" → see downstream effects
- Click "violation_pressure" → see what it triggered

### 3. Trace Backwards
- "Why did network collapse happen?"
- Follow the causation chain backwards to root causes
- See all contributing factors and their relationships

### 4. Trace Forwards
- "What did this breath cycle trigger?"
- Follow the causation chain forwards to see effects
- See all downstream consequences

### 5. Find Paths
- Find shortest causation path between any two events
- Understand how events are connected
- See the chain of causation

---

## Causation Types Detected

### 1. Threshold Causation
- Detects when metrics cross thresholds
- Example: `modularity < 0.3` → `network collapse`
- Example: `VP < 0.25` → `VP0 classification`
- Example: `organism_count >= 500` → `collapse trigger`

### 2. Correlation Causation
- Detects when multiple metrics change together
- Example: `modularity` and `clustering` both change → correlated event
- Identifies relationships between metrics

### 3. Direct Causation
- Known direct relationships
- Example: `breath cycle` → `network update`
- Example: `breath cycle` → `VP calculation`
- Example: `network metrics` → `VP calculation`

### 4. Temporal Causation
- Events that happened in sequence
- Time-based relationships
- Chronological cause-effect chains

---

## Usage

### Command Line

```python
from causation_explorer import CausationExplorer

explorer = CausationExplorer()

# Search for events
collapse_events = explorer.search_events("collapse")

# Explore what caused an event
if collapse_events:
    event_id = collapse_events[0]['event_id']
    backwards = explorer.explore_backwards(event_id)
    print("What caused this:")
    for item in backwards:
        print(f"  {item['event']}")

# Explore what an event caused
forwards = explorer.explore_forwards(event_id)
print("What this caused:")
for item in forwards:
    print(f"  {item['event']}")

# Find path between events
path = explorer.find_path(event1_id, event2_id)
```

### Web Interface

```bash
python causation_web_ui.py
```

Then open http://localhost:5000 in your browser.

**Features:**
- Interactive graph visualization (D3.js)
- Click nodes to explore
- Search events
- View causation trails
- See backwards/forwards exploration

---

## Example Exploration

### Scenario: Network Collapse

1. **Search for "collapse"**
   - Find event: `network collapsed at generation 200`

2. **Click event → Explore Backwards**
   - Shows: `modularity dropped to 0.28`
   - Click modularity → Shows: `connection formation increased`
   - Click connection → Shows: `organism count reached 500`
   - Click organism count → Shows: `evolution engine parameters`

3. **Click event → Explore Forwards**
   - Shows: `phase transition triggered`
   - Shows: `VP calculation updated`
   - Shows: `Explorer phase changed`

4. **Find Path**
   - From: `organism_count=500`
   - To: `phase transition`
   - Shows: Complete causation chain

---

## Integration

### With Unified System

```python
from unified_entry import UnifiedSystem, StateLogger
from causation_explorer import CausationExplorer

# Initialize systems
system = UnifiedSystem()
explorer = CausationExplorer(state_logger=system.logger)

# As system runs, events are automatically tracked
# You can explore at any time
```

### With Log Files

```python
# Load from existing log files
explorer = CausationExplorer(log_dir=Path('data/logs'))

# Events are automatically loaded and causation detected
```

---

## API Endpoints (Web UI)

- `GET /api/events/search?q=query` - Search events
- `GET /api/events/<event_id>` - Get event details
- `GET /api/events/<event_id>/backwards?depth=N` - Explore backwards
- `GET /api/events/<event_id>/forwards?depth=N` - Explore forwards
- `GET /api/path/<from_id>/<to_id>` - Find path between events
- `GET /api/stats` - Get causation graph statistics
- `GET /api/graph` - Get full graph for visualization

---

## Causation Detection

The system automatically detects causations by:

1. **Loading state history** from log files
2. **Tracking metric changes** over time
3. **Detecting threshold crossings** (modularity < 0.3, VP < 0.25, etc.)
4. **Finding correlations** (metrics changing together)
5. **Identifying direct relationships** (known component interactions)
6. **Building causation graph** (NetworkX directed graph)

---

## Thresholds Defined

```python
thresholds = {
    'modularity': {'collapse': 0.3, 'direction': 'below'},
    'organism_count': {'collapse': 500, 'direction': 'above'},
    'clustering_coefficient': {'collapse': 0.5, 'direction': 'above'},
    'violation_pressure': {'vp0': 0.25, 'vp1': 0.50, 'vp2': 0.75, 'vp3': 0.99},
    'vp_calculations': {'transition': 50, 'direction': 'above'},
}
```

---

## Known Consequences

The system knows that certain threshold crossings cause specific events:

- `modularity < 0.3` → `network collapse`, `phase transition`
- `organism_count >= 500` → `network collapse`, `phase transition`
- `VP < 0.25` → `VP0 classification`, `convergence`, `phase transition`
- `vp_calculations >= 50` → `phase transition`, `mathematical capability`

---

## Future Enhancements

- **Machine learning** for causation detection
- **Confidence scores** for causation links
- **Time-based filtering** (explore specific time ranges)
- **Metric-based filtering** (explore specific metrics)
- **Export capabilities** (export causation trails)
- **Visualization improvements** (better graph layouts, animations)

---

**This is your scientific exploration tool - follow your curiosity!** 🔬✨

