# 🔬 Live Mode Data Sources - What's Actually Being Accessed

## Current Situation

### ✅ **Data EXISTS:**
1. **Log Files** (`data/logs/*.log`)
   - `reality_sim.log` - HAS DATA (e.g., `orgs:10|conns:0|mod:0.000|...`)
   - Format: `timestamp|level|component|metric:value|metric:value|...`
   - Example: `23:37:11.608|DEBUG|reality_sim|orgs:10|conns:0|mod:0.000|clust:0.000|path:0.00|gen:0`

2. **Shared State File** (`data/.shared_simulation_state.json`)
   - ✅ EXISTS (32,771 lines!)
   - Contains complete system state (reality_sim, explorer, djinn_kernel)
   - Updates continuously when `unified_entry.py` is running
   - ❌ **NOT CURRENTLY LOADED** by CausationExplorer

3. **Akashic Ledger** (`data/kernel/akashic_ledger/`)
   - May or may not exist
   - Loaded if UTM Kernel is available

---

## 🔍 What "Live Mode" Actually Accesses

### **Current Flow (Restored from Git):**

```
┌──────────────────────────────────────────────────────────┐
│         CausationExplorer Initialization                 │
│                                                           │
│  ┌────────────────────────────────────────────┐          │
│  │  _load_state_history()                     │          │
│  │                                             │          │
│  │  1. Try Akashic Ledger (if available)      │          │
│  │     → Reads tape cells                     │          │
│  │     → Converts to Events                   │          │
│  │                                             │          │
│  │  2. Load Log Files (fallback)              │          │
│  │     → Reads data/logs/*.log                │          │
│  │     → Parses each line                     │          │
│  │     → _parse_log_line()                    │          │
│  │     → Creates Events                       │          │
│  │                                             │          │
│  │  ❌ Does NOT load shared state file!        │          │
│  └────────────────────────────────────────────┘          │
│                                                           │
│  ┌────────────────────────────────────────────┐          │
│  │  Stores in Memory:                         │          │
│  │  - explorer.events{}                       │          │
│  │  - explorer.causation_graph                │          │
│  └────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│              Web UI Endpoints                             │
│                                                           │
│  ┌────────────────────────────────────────────┐          │
│  │  /api/graph                                │          │
│  │  → Returns ALL events from                 │          │
│  │     explorer.events{}                      │          │
│  │     explorer.causation_graph               │          │
│  └────────────────────────────────────────────┘          │
│                                                           │
│  ┌────────────────────────────────────────────┐          │
│  │  /api/live/status                          │          │
│  │  → Checks explorer.events{} timestamps     │          │
│  │  → Sees if any events exist within 10s     │          │
│  │  → Returns:                                │          │
│  │     {                                       │          │
│  │       "live": true/false,                  │          │
│  │       "last_event_time": timestamp,        │          │
│  │       "event_count": count                 │          │
│  │     }                                       │          │
│  └────────────────────────────────────────────┘          │
│                                                           │
│  ┌────────────────────────────────────────────┐          │
│  │  /api/live/events?since=TIMESTAMP          │          │
│  │  → Filters explorer.events{}               │          │
│  │  → Returns events where                    │          │
│  │     event.timestamp > since_timestamp      │          │
│  │  → Returns:                                │          │
│  │     {                                       │          │
│  │       "events": [...],                     │          │
│  │       "event_count": count,                │          │
│  │       "latest_timestamp": timestamp        │          │
│  │     }                                       │          │
│  └────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────┘
```

---

## ⚠️ **The Problem**

### **"Live Mode" is NOT Actually Live!**

It's just **filtering already-loaded data** by timestamp. Here's what's happening:

1. **On Startup:**
   - CausationExplorer loads events from log files (once)
   - Stores them in `explorer.events{}`
   - Builds causation graph

2. **When "Live Mode" is Enabled:**
   - Frontend polls `/api/live/status` every 2 seconds
   - Backend checks if any events in `explorer.events{}` have recent timestamps
   - Returns `{"live": true}` if recent events found
   - Frontend then polls `/api/live/events?since=TIMESTAMP`
   - Backend filters `explorer.events{}` and returns "new" events

3. **The Issue:**
   - ❌ Events are **NOT** being fed from `unified_entry.py` in real-time
   - ❌ Shared state file is **NOT** being loaded
   - ❌ New events from running system are **NOT** added to CausationExplorer
   - ✅ It only shows events that were loaded from logs on startup

---

## 🔧 **What's Missing for TRUE Live Mode**

### **Phase 2: Real-Time Event Streaming**

To make it actually live, we need:

1. **Event Feeding from Backend:**
   ```python
   # In unified_entry.py, after logging state:
   if self.causation_explorer:
       event = Event(
           timestamp=current_time,
           component='reality_sim',
           event_type='state_change',
           data=reality_sim_state
       )
       self.causation_explorer.add_event(event, is_historical=False)
   ```

2. **Shared State File Loading:**
   ```python
   # In causation_explorer.py:
   def _load_from_shared_state(self):
       # Read data/.shared_simulation_state.json
       # Extract events from current state
       # Add as live events (not historical)
   ```

3. **Periodic Updates:**
   - Web UI polls for new events
   - Backend checks shared state file for updates
   - New events are added to CausationExplorer
   - Causation links are detected in real-time

---

## 📊 **Current Data Flow (What You're Seeing)**

### **Historical Mode (What Actually Works):**

```
Run unified_entry.py
    ↓
Generates log files (data/logs/*.log)
    ↓
Stop unified_entry.py
    ↓
Start causation_web_ui.py
    ↓
CausationExplorer._load_state_history()
    ↓
Reads log files → Creates Events → Builds Graph
    ↓
Visualizes historical data
```

### **"Live Mode" (Doesn't Actually Work):**

```
Start causation_web_ui.py (loads old log files)
    ↓
Enable "Live Mode" checkbox
    ↓
Frontend polls /api/live/status
    ↓
Backend checks timestamps of loaded events
    ↓
Returns {"live": true} if recent events found
    ↓
Frontend polls /api/live/events?since=TIMESTAMP
    ↓
Backend filters already-loaded events
    ↓
Shows "new" events (but they're just filtered old data)
```

**Problem:** No connection to running `unified_entry.py`!

---

## 💡 **Why Visualization Might Be Blank**

1. **Log Files Might Be Empty:**
   - Check: `Get-Content data/logs/reality_sim.log`
   - If empty or just headers, no events to load

2. **Log Parsing Might Be Failing:**
   - Check log format matches expected format
   - Format should be: `timestamp|level|component|metric:value|...`

3. **Shared State File Not Loaded:**
   - File exists (`data/.shared_simulation_state.json`)
   - But CausationExplorer doesn't load it
   - Missing `_load_from_shared_state()` method

4. **No Events Being Fed:**
   - `unified_entry.py` doesn't feed events to CausationExplorer
   - Missing `causation_explorer.add_event()` calls

---

## 🎯 **Quick Diagnosis**

Check what's actually in CausationExplorer:

```python
# In Python shell:
from causation_explorer import CausationExplorer
explorer = CausationExplorer()
print(f"Events loaded: {len(explorer.events)}")
print(f"Links created: {len(explorer.causation_graph.edges())}")
```

If both are 0 → No data loaded
If events > 0 but links = 0 → Events loaded but no causation detected
If both > 0 → Data exists, might be filtering issue

---

## 📝 **Summary**

**What "Live Mode" Accesses:**
- ❌ NOT the running backend (`unified_entry.py`)
- ❌ NOT the shared state file (`data/.shared_simulation_state.json`)
- ✅ Only events loaded from log files on startup
- ✅ Filters already-loaded events by timestamp

**What's Missing:**
- Real-time event feeding from `unified_entry.py`
- Shared state file loading
- Live event streaming
- Connection between running system and CausationExplorer

**Current State:**
- Historical mode works (if log files have data)
- "Live mode" is just timestamp filtering, not actually live
- Visualization blank if no log data or parsing fails

