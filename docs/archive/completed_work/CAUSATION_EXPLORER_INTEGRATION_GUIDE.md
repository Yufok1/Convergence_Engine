# 🔬 Causation Explorer: Complete Guide & Integration Plan

## What Is the Causation Explorer?

The Causation Explorer is a scientific exploration tool for understanding cause-and-effect relationships in your Butterfly System. Think of it as a "time machine" for your simulation data—you can ask "why did this happen?" or "what did this cause?" and trace the complete chain of events.

---

## The Core Idea

Instead of just watching charts go up and down, the Causation Explorer lets you click on any event and explore:

- 🔙 **Backwards:** "What caused the network to collapse?"
- 🔜 **Forwards:** "What did this breath cycle trigger?"
- 🛤️ **Paths:** "How did organism count affect phase transitions?"

---

## What It Aims To Be

### Vision: Your Scientific Investigation Partner

The Causation Explorer is designed to answer questions like:

**"Why did my network collapse at generation 200?"**
- Click the collapse event
- Trace backwards → see modularity dropped below 0.3
- Trace further → see organism count hit 500
- Trace to root → see evolution parameters

**"What happens when Violation Pressure drops below 0.25?"**
- Click a VP0 event
- Trace forwards → see phase transitions triggered
- See Explorer phase changes
- See mathematical capabilities activated

**"How are breath cycles connected to network behavior?"**
- Find path from breath → network update → VP calculation
- See the complete causation chain

---

## Key Capabilities

| Feature | What It Does |
|---------|-------------|
| **Threshold Detection** | Automatically detects when metrics cross critical thresholds (modularity < 0.3, VP < 0.25, etc.) |
| **Correlation Analysis** | Finds when multiple metrics change together |
| **Direct Causation** | Knows direct relationships (breath → network, network → VP) |
| **Interactive Exploration** | Click any event to explore backwards/forwards |
| **Path Finding** | Finds shortest causation chain between any two events |
| **Real-time Tracking** | Can track events as they happen (when integrated) |

---

## Current Implementation Status

### What Exists ✅

The Causation Explorer is fully built with ~575 lines of sophisticated code:

**Core Engine** (`causation_explorer.py`)
- Event tracking with timestamps
- Causation graph (NetworkX directed graph)
- Automatic causation detection
- Four causation types: threshold, correlation, direct, temporal

**Web UI** (`causation_web_ui.py`)
- Flask server with REST API
- D3.js visualization (mentioned in guide)
- Interactive graph interface
- Search and exploration endpoints

**Integration Capabilities**
- Can read from Akashic Ledger (UTM Kernel)
- Can read from log files (StateLogger)
- Can accept live events (`add_event()` method)

### What's Missing ❌

**Integration with main loop** - The Causation Explorer exists but is not connected to the main Butterfly System:

```python
# Current state:
# unified_entry.py - NO causation explorer instantiation
# explorer/main.py - NO causation explorer integration
# reality_simulator/main.py - NO causation explorer
# Web UI runs separately: python causation_web_ui.py
```

**Cursor's assessment was correct: 0% utilization in main system** ✅

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────┐
│          Causation Explorer                 │
│                                             │
│  Events ──→ Causation Detection ──→ Graph  │
│              ↓                              │
│         Thresholds  Correlations  Direct   │
│                                             │
│  Explore ←── Query ←── User/API             │
└─────────────────────────────────────────────┘
         ↑                    ↑
         │                    │
    Akashic Ledger      State Logs
    (UTM Kernel)      (StateLogger)
```

### Causation Detection System

The explorer automatically detects four types of causation:

#### 1. Threshold Causation (Strength: 0.9)

Detects when metrics cross critical thresholds:

```python
thresholds = {
    'modularity': {'collapse': 0.3, 'direction': 'below'},
    'organism_count': {'collapse': 500, 'direction': 'above'},
    'violation_pressure': {'vp0': 0.25, 'vp1': 0.50, 'vp2': 0.75}
}
```

**Example:** modularity drops from 0.35 → 0.28 → **CAUSATION DETECTED** → network collapse event

#### 2. Correlation Causation (Strength: 0.7)

Detects when multiple metrics change together:

```python
# If 2+ metrics change by >10% simultaneously → correlation detected
# Example: modularity ↓ 15%, clustering ↓ 20%, density ↑ 25%
# → Correlated causation link created
```

#### 3. Direct Causation (Strength: 0.8)

Known direct relationships:

```python
direct_causations = {
    ('breath', 'reality_sim'): 'Breath cycle drives network update',
    ('breath', 'djinn_kernel'): 'Breath cycle drives VP calculation',
    ('reality_sim', 'djinn_kernel'): 'Network metrics feed into VP',
    ('explorer', 'reality_sim'): 'Explorer phase affects network'
}
```

#### 4. Temporal Causation (Strength: Variable)

Events that happened in sequence (within 1 second).

---

## Integration Plan: Getting It Working

### Phase 1: Simple Integration (Recommended First Step)

**Goal:** Add Causation Explorer to unified system without breaking anything

```python
# unified_entry.py - Add to UnifiedSystem.__init__()
from causation_explorer import CausationExplorer

class UnifiedSystem:
    def __init__(self, ...):
        # ... existing code ...
        
        # Initialize Causation Explorer
        self.causation_explorer = CausationExplorer(
            state_logger=self.logger,
            log_dir=self.logger.log_dir,
            utm_kernel=self.djinn_kernel if hasattr(self, 'djinn_kernel') else None
        )
        
        print("[UNIFIED] [PASS] Causation Explorer initialized")
```

**Benefit:** Explorer will automatically load existing log files and build causation graph

---

### Phase 2: Real-Time Event Tracking

**Goal:** Feed live events into explorer as system runs

```python
# In StateLogger.log_breath() method:
def log_breath(self, cycle: int, depth: float, quality: float, ...):
    # ... existing logging ...
    
    # Feed event to causation explorer
    if hasattr(self, 'causation_explorer'):
        event = Event(
            timestamp=time.time(),
            component='breath',
            event_type='breath_cycle',
            data={
                'cycle': cycle,
                'depth': depth,
                'quality': quality,
                'coherence': coherence
            }
        )
        self.causation_explorer.add_event(event)
```

Apply same pattern to:
- `log_reality_sim()` - Network metrics
- `log_djinn_kernel()` - VP calculations
- `log_explorer()` - Explorer state

---

### Phase 3: Phase Transition Tracking

**Goal:** Detect and track phase transitions automatically

```python
# In main loop where transitions are detected:
if transition_detected:
    event = Event(
        timestamp=time.time(),
        component='system',
        event_type='phase_transition',
        data={
            'from_phase': old_phase,
            'to_phase': new_phase,
            'trigger': 'network_collapse',  # or 'vp_threshold', etc.
            'modularity': current_modularity,
            'vp': current_vp
        }
    )
    self.causation_explorer.add_event(event)
```

---

### Phase 4: Web UI Integration

**Goal:** Run web UI alongside main system

**Option A: Separate Process**

```bash
# Terminal 1: Main system
python unified_entry.py

# Terminal 2: Causation Explorer UI
python causation_web_ui.py

# Then open http://localhost:5000
```

**Option B: Integrated (Advanced)**

```python
# unified_entry.py - Add Flask app in separate thread
import threading
from causation_web_ui import app

def run_web_ui():
    app.run(debug=False, port=5000, use_reloader=False)

# In UnifiedSystem.__init__()
self.web_thread = threading.Thread(target=run_web_ui, daemon=True)
self.web_thread.start()
print("[UNIFIED] [PASS] Causation Explorer Web UI on http://localhost:5000")
```

---

## Practical Usage Examples

### Example 1: Debugging Network Collapse

```python
explorer = system.causation_explorer

# Search for collapse events
collapses = explorer.search_events("collapse")

# Pick the most recent one
event_id = collapses[0]['event_id']

# Trace backwards to find root cause
trail = explorer.explore_backwards(event_id, max_depth=5)

# Print the causation chain
for item in trail:
    print(f"Depth {item['depth']}: {item['event']}")

# Output:
# Depth 5: organism_count reached 500
# Depth 4: connections increased rapidly  
# Depth 3: modularity dropped to 0.28
# Depth 2: threshold crossed (modularity < 0.3)
# Depth 1: network collapse triggered
# Depth 0: phase transition initiated
```

### Example 2: Understanding VP Behavior

```python
# Find all VP0 events
vp0_events = explorer.search_events("vp0")

# Explore what caused VP to drop
event_id = vp0_events[0]['event_id']
causes = explorer.explore_backwards(event_id)

# Explore what VP0 triggered
effects = explorer.explore_forwards(event_id)

# See the complete picture
print("What caused VP0:", [c['event'] for c in causes])
print("What VP0 caused:", [e['event'] for e in effects])
```

### Example 3: Finding Causation Paths

```python
# Find how organism count affects phase transitions
organism_events = explorer.search_events("organism_count")
transition_events = explorer.search_events("phase_transition")

path = explorer.find_path(
    organism_events[0]['event_id'],
    transition_events[0]['event_id']
)

# path = ['evt_123', 'evt_456', 'evt_789', ...]
# Shows the shortest causation chain
```

---

## API Reference

### Core Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `add_event(event)` | Add event to tracker | None |
| `explore_backwards(event_id, depth=10)` | Find what caused this | List of events |
| `explore_forwards(event_id, depth=10)` | Find what this caused | List of events |
| `find_path(from_id, to_id)` | Shortest causation path | List of event IDs |
| `search_events(query)` | Search by keyword | List of events |
| `get_event_summary(event_id)` | Full event details | Dict with causation info |
| `get_causation_stats()` | Graph statistics | Dict with metrics |

### Event Structure

```python
Event(
    timestamp=1234567890.123,
    component='breath',           # 'breath', 'reality_sim', 'djinn_kernel', etc.
    event_type='state_change',    # 'threshold_crossed', 'transition', etc.
    data={'metric1': value1, ...} # Any relevant data
)
```

---

## Benefits of Integration

### 1. Scientific Understanding
- Answer "why" questions about system behavior
- Discover unexpected causation chains
- Validate theoretical predictions

### 2. Debugging
- Quick root cause analysis for problems
- Trace effects of parameter changes
- Identify feedback loops

### 3. Discovery
- Find hidden relationships between components
- Detect emergent patterns
- Understand system dynamics

### 4. Documentation
- Automatic causation documentation
- Reproducible exploration trails
- Visual causation graphs

---

## Recommended Implementation Steps

### Step 1: Basic Integration (30 minutes)
- Add `CausationExplorer` to `UnifiedSystem.__init__()`
- Test loading existing log files
- Verify causation graph builds correctly

### Step 2: Live Event Tracking (1 hour)
- Add event tracking to `StateLogger` methods
- Test real-time causation detection
- Verify thresholds are detected correctly

### Step 3: Web UI Launch (15 minutes)
- Run `causation_web_ui.py` in separate terminal
- Open http://localhost:5000
- Explore existing events

### Step 4: Testing & Validation (30 minutes)
- Run simulation for 100 cycles
- Search for specific events (collapses, transitions)
- Trace causation chains
- Verify accuracy

### Step 5: Refinement (Ongoing)
- Add more threshold definitions
- Tune causation strength values
- Add custom causation types
- Improve correlation detection

---

## Current Gaps & Solutions

### Gap 1: Not Integrated
**Solution:** Follow Phase 1 integration plan above

### Gap 2: No HTML Template
**Solution:** The guide references `causation_explorer.html` but it doesn't exist
- Need to create basic D3.js visualization
- OR use command-line interface for now

### Gap 3: Threshold Definitions May Need Tuning
**Solution:** Review and adjust thresholds based on your actual data

```python
# Current thresholds in causation_explorer.py line 80-86
# Adjust these based on your simulation's actual behavior
```

---

## Summary

### What It Is
A sophisticated causation tracking and exploration system that lets you interactively investigate cause-effect relationships in your Butterfly System.

### Current State
- **Code:** Fully built (~575 lines, professional quality) ✅
- **Integration:** Not connected to main loop ❌
- **Testing:** Standalone tested ✅
- **Documentation:** Complete guide exists ✅

### To Get It Working
- **5-minute version:** Instantiate in `UnifiedSystem.__init__()` → loads existing logs
- **30-minute version:** Add live event tracking → real-time causation
- **1-hour version:** Add web UI → interactive exploration

### Why It's Valuable
Transform from "watching metrics change" to "understanding why they change" - this is the difference between monitoring and scientific investigation.

---

**The Causation Explorer is your butterfly's journal—recording not just what happens, but why it happens.** 🔬🦋

