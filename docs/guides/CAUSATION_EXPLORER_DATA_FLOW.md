# 🔬 Causation Explorer - Data Flow Visualization

## Overview
This document shows exactly where the Causation Explorer gets its data for visualizations.

---

## 📊 Data Sources

The Causation Explorer loads data from **3 sources** (in priority order):

### 1️⃣ **Akashic Ledger** (Primary - Tape-Based)
**Location:** `data/kernel/akashic_ledger/`
- **Format:** Tape cells stored by Djinn Kernel (UTM Kernel)
- **What it contains:**
  - Agent actions
  - Tape cell states
  - Symbol writes/reads
  - Timestamped operations
- **How it's loaded:**
  ```python
  explorer.utm_kernel.akashic_ledger.read_cell(position)
  ```
  - Reads ALL tape cells sequentially
  - Converts each cell to an Event
  - Component: `djinn_kernel`
  - Event type: `tape_cell`
- **When:** Loaded on CausationExplorer initialization if UTM Kernel is available

### 2️⃣ **Log Files** (Secondary - Text-Based)
**Location:** `data/logs/*.log`
- **Log files used:**
  - `application.log` - General application events
  - `breath.log` - Explorer breath cycles
  - `djinn_kernel.log` - Djinn Kernel operations
  - `explorer.log` - Explorer state changes
  - `reality_sim.log` - Reality Simulator metrics
  - `state.log` - System state snapshots
  - `system.log` - System-level events

- **Format:** Pipe-delimited (`|`)
  ```
  timestamp|level|component|metric1:value1|metric2:value2|...
  ```

- **How it's loaded:**
  ```python
  for log_file in log_dir.glob('*.log'):
      for line in log_file:
          explorer._parse_log_line(line, log_file.stem)
  ```
  - Reads ALL log files in `data/logs/`
  - Parses each line into an Event
  - Extracts metrics (organism_count, modularity, VP, etc.)
  - Component: Log file name (e.g., `reality_sim`, `explorer`)
  - Event type: `state_change`

### 3️⃣ **Shared State File** (Tertiary - JSON)
**Location:** `data/.shared_simulation_state.json`
- **Format:** JSON snapshot
- **What it contains:**
  - Current frame count
  - All system states (reality_sim, explorer, djinn_kernel)
  - Real-time metrics
  - Organism positions
  - Network data
- **Note:** Currently **NOT loaded** by CausationExplorer (would need to be added)

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CausationExplorer.__init__()              │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  _load_state_history()                            │      │
│  │                                                    │      │
│  │  ┌─────────────────────────────────────────┐      │      │
│  │  │ 1. Try Akashic Ledger (if available)    │      │      │
│  │  │    _load_from_akashic_ledger()          │      │      │
│  │  │    → Reads all tape cells               │      │      │
│  │  │    → Converts to Events                 │      │      │
│  │  └─────────────────────────────────────────┘      │      │
│  │                                                    │      │
│  │  ┌─────────────────────────────────────────┐      │      │
│  │  │ 2. Load Log Files (fallback)            │      │      │
│  │  │    → data/logs/*.log                    │      │      │
│  │  │    → _parse_log_line()                  │      │      │
│  │  │    → Converts to Events                 │      │      │
│  │  └─────────────────────────────────────────┘      │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  For each Event:                                  │      │
│  │    add_event()                                    │      │
│  │    → Stores in explorer.events{}                 │      │
│  │    → Updates events_by_component{}               │      │
│  │    → Updates metric_history{}                    │      │
│  │    → _detect_causations()                        │      │
│  │      → Finds threshold crossings                 │      │
│  │      → Finds correlations                        │      │
│  │      → Finds direct relationships                │      │
│  │      → Creates causation links                   │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Web UI Endpoints (causation_web_ui.py)          │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  /api/graph                                       │      │
│  │  → Returns ALL nodes and links                    │      │
│  │  → Source: explorer.events{}                      │      │
│  │     Source: explorer.causation_graph              │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  /api/live/status                                 │      │
│  │  → Checks if recent events exist                  │      │
│  │  → Source: explorer.events{} (check timestamps)   │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  /api/live/events?since=TIMESTAMP                 │      │
│  │  → Returns events after timestamp                 │      │
│  │  → Source: explorer.events{} (filtered)           │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  /api/stats                                       │      │
│  │  → Returns graph statistics                       │      │
│  │  → Source: explorer.causation_graph               │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              HTML Template (causation_explorer.html)         │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  loadGraph()                                      │      │
│  │  → Calls /api/graph                               │      │
│  │  → Receives {nodes: [], links: []}                │      │
│  │  → Renders with D3.js                             │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Live Mode (if enabled)                           │      │
│  │  → Polls /api/live/status every 2 seconds         │      │
│  │  → Polls /api/live/events?since=TIMESTAMP         │      │
│  │  → Adds new events to graph                       │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Data Storage

### In-Memory (CausationExplorer)
```python
explorer.events = {
    'evt_123456789': Event(...),
    'evt_123456790': Event(...),
    ...
}

explorer.causation_graph = NetworkX DiGraph
    Nodes: Event IDs
    Edges: Causation links with:
        - causation_type ('threshold', 'correlation', 'direct', 'temporal')
        - strength (0.0-1.0)
        - explanation (text)
```

### On-Disk Sources
1. **Akashic Ledger:** `data/kernel/akashic_ledger/`
2. **Log Files:** `data/logs/*.log`
3. **Shared State:** `data/.shared_simulation_state.json` (NOT currently used)

---

## 🎯 What Gets Visualized

### Nodes (Events)
- **Source:** `explorer.events{}`
- **Properties:**
  - `id`: Event ID (unique)
  - `component`: Which system (reality_sim, explorer, djinn_kernel)
  - `type`: Event type (state_change, tape_cell, threshold_crossed, etc.)
  - `data`: All metrics/values
  - `timestamp`: When it happened

### Links (Causation Relationships)
- **Source:** `explorer.causation_graph.edges()`
- **Types:**
  - **Threshold Causation:** Event A crossed threshold → Event B happened
  - **Correlation Causation:** Metrics changed together
  - **Direct Causation:** Direct metric relationships
  - **Temporal Causation:** Time-based connections
- **Properties:**
  - `source`: From event ID
  - `target`: To event ID
  - `type`: Causation type
  - `strength`: How strong (0.0-1.0)
  - `explanation`: Human-readable explanation

---

## 🔍 Detection Logic

### Threshold Causations
```python
# Detects when thresholds are crossed
if prev_value < threshold <= new_value:
    # Threshold was crossed
    # Link: prev_event → new_event
```

**Examples:**
- `organism_count` crosses 500 → Network collapse event
- `modularity` drops below 0.3 → Collapse event
- `violation_pressure` crosses 0.25, 0.50, 0.75 → VP level events

### Correlation Causations
```python
# Detects when multiple metrics change together
if multiple_metrics_changed_together(prev_event, new_event):
    # Correlation detected
    # Link: prev_event → new_event
```

### Direct Causations
```python
# Detects direct metric relationships
if metric_A_in_prev_event affects metric_B_in_new_event:
    # Direct causation
    # Link: prev_event → new_event
```

---

## ⚠️ Current Limitations

1. **Shared State File NOT Loaded**
   - `data/.shared_simulation_state.json` exists but isn't parsed
   - Would need `_load_from_shared_state()` method

2. **Live Mode Detection**
   - Uses event timestamps (checks if recent events exist)
   - No heartbeat file checking (we removed that)
   - May not accurately detect if backend is truly running

3. **No Real-Time Updates**
   - Events are loaded once on initialization
   - Live mode just checks for new events already in memory
   - Events aren't being fed from `unified_entry.py` anymore

---

## 💡 How to Make It "Live"

To make live mode actually work:

1. **Feed Events from Backend:**
   ```python
   # In unified_entry.py, after logging state:
   if self.causation_explorer:
       event = Event(...)
       self.causation_explorer.add_event(event, is_historical=False)
   ```

2. **Load Shared State:**
   ```python
   # In causation_explorer.py:
   def _load_from_shared_state(self):
       # Read data/.shared_simulation_state.json
       # Extract events from current state
       # Add as historical or live events
   ```

3. **Poll for Updates:**
   - Frontend already polls `/api/live/events`
   - Backend just needs to feed events in real-time

---

## 📝 Summary

**Current State:**
- ✅ Loads from Akashic Ledger (if available)
- ✅ Loads from log files (always)
- ❌ Does NOT load from shared state file
- ❌ Does NOT receive real-time events from backend
- ⚠️ "Live mode" just checks timestamps, doesn't actually connect to backend

**What You're Seeing:**
- All **historical data** from logs and Akashic Ledger
- Events parsed from log files
- Causation links detected automatically
- Visualization of the causation graph

**What's NOT Working:**
- Real-time updates from `unified_entry.py`
- Live event feeding
- Shared state file parsing

