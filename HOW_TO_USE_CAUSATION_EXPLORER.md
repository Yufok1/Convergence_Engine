# 🔬 How to Use the Causation Explorer - Quick Start Guide

**Interactive tool for exploring "why did this happen?" and "what did this cause?"**

---

## 🚀 Quick Start

### Option 1: Use in Python Script (Recommended for Quick Exploration)

```python
from unified_entry import UnifiedSystem
import time

# Start the unified system
system = UnifiedSystem()
print("[CAUSATION] System started - Causation Explorer ready!")

# Run for a bit to generate events
print("\n[CAUSATION] Running simulation to generate events...")
print("Press Ctrl+C after a few seconds to stop and explore\n")

try:
    # Run for a short time
    for i in range(50):  # Run 50 cycles
        system.controller.run_genesis_phase()
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

# Now explore causation!
explorer = system.causation_explorer

# Get statistics
stats = explorer.get_causation_stats()
print(f"\n📊 Causation Graph Stats:")
print(f"  Total Events: {stats['total_events']}")
print(f"  Causation Links: {stats['total_links']}")
print(f"  Components: {stats['components']}")

# Search for events
print("\n🔍 Searching for 'breath' events...")
breath_events = explorer.search_events("breath")
print(f"  Found {len(breath_events)} breath events")

if breath_events:
    # Pick the most recent breath event
    event = breath_events[0]
    event_id = event['event_id']
    
    print(f"\n🔙 What caused this breath cycle?")
    backwards = explorer.explore_backwards(event_id, max_depth=5)
    for item in backwards[:3]:  # Show top 3
        print(f"  Depth {item['depth']}: {item['event']['component']} - {item['event']['event_type']}")
    
    print(f"\n🔜 What did this breath cycle cause?")
    forwards = explorer.explore_forwards(event_id, max_depth=5)
    for item in forwards[:3]:  # Show top 3
        print(f"  Depth {item['depth']}: {item['event']['component']} - {item['event']['event_type']}")
```

---

## 📋 Common Use Cases

### 1. Find What Caused Network Collapse

```python
# After running system
explorer = system.causation_explorer

# Search for collapse events
collapses = explorer.search_events("collapse")

if collapses:
    event_id = collapses[0]['event_id']
    
    # Trace backwards to root cause
    trail = explorer.explore_backwards(event_id, max_depth=10)
    
    print("🔬 Causation Trail (deepest = root cause):")
    for item in trail:
        print(f"  Depth {item['depth']}:")
        print(f"    Component: {item['event']['component']}")
        print(f"    Type: {item['event']['event_type']}")
        print(f"    Data: {item['event']['data']}")
        if 'caused_by' in item:
            print(f"    Caused by: {len(item['caused_by'])} events")
        print()
```

### 2. See What a VP Drop Triggered

```python
explorer = system.causation_explorer

# Find VP0 events (VP < 0.25)
vp0_events = explorer.search_events("vp0")

if vp0_events:
    event_id = vp0_events[0]['event_id']
    
    # What did VP0 cause?
    effects = explorer.explore_forwards(event_id, max_depth=10)
    
    print("🔜 Effects of VP0 Classification:")
    for item in effects:
        print(f"  {item['event']['component']}: {item['event']['event_type']}")
        if 'data' in item['event']:
            print(f"    → {item['event']['data']}")
```

### 3. Find Path Between Two Events

```python
explorer = system.causation_explorer

# Find two different events
breath_events = explorer.search_events("breath")
vp_events = explorer.search_events("violation_pressure")

if breath_events and vp_events:
    from_id = breath_events[0]['event_id']
    to_id = vp_events[0]['event_id']
    
    # Find the causation path
    path = explorer.find_path(from_id, to_id)
    
    if path:
        print(f"🛤️  Causation Path ({len(path)} steps):")
        for i, event_id in enumerate(path):
            event = explorer.events[event_id]
            print(f"  Step {i+1}: {event.component} - {event.event_type}")
    else:
        print("  No direct path found")
```

### 4. Get Complete Event Summary

```python
explorer = system.causation_explorer

# Find an interesting event
events = explorer.search_events("transition")

if events:
    event_id = events[0]['event_id']
    
    # Get comprehensive summary
    summary = explorer.get_event_summary(event_id)
    
    print(f"📊 Event Summary:")
    print(f"  Event: {summary['event']}")
    print(f"  Caused by: {summary['caused_by']} events")
    print(f"  Caused: {summary['caused']} events")
    print(f"\n  Predecessors (causes):")
    for pred in summary['predecessor_events'][:3]:
        print(f"    - {pred['component']}: {pred['event_type']}")
    print(f"\n  Successors (effects):")
    for succ in summary['successor_events'][:3]:
        print(f"    - {succ['component']}: {succ['event_type']}")
```

---

## 🌐 Web UI (Visual Exploration)

### Start Web Server

```bash
# Terminal 1: Run main system (optional - web UI can load from log files)
python unified_entry.py

# Terminal 2: Start Causation Explorer Web UI
python causation_web_ui.py
```

**Note:** You may need to install Flask first:
```bash
pip install flask
```

### Open Browser

Open http://localhost:5000 in your browser.

**Features:**
- Interactive D3.js graph visualization
- Click nodes to explore backwards/forwards
- Search events by keyword
- View causation trails visually
- **Export Art:** Export as Cinematic MP4 video or interactive HTML
- **Filters:** Filter by component or causation type (preserves graph positions)
- **Navigation:** 3D rotation, pan, zoom (default 5% view)
- **Live Mode:** Real-time updates when backend is running

---

## 🔍 Search Examples

### By Component
```python
breath_events = explorer.search_events("breath")
reality_events = explorer.search_events("reality_sim")
explorer_events = explorer.search_events("explorer")
djinn_events = explorer.search_events("djinn_kernel")
```

### By Event Type
```python
transitions = explorer.search_events("transition")
collapses = explorer.search_events("collapse")
vp_events = explorer.search_events("vp")
```

### By Metric
```python
modularity_events = explorer.search_events("modularity")
organism_events = explorer.search_events("organism")
```

---

## 🎬 Export Art (Web UI Only)

The web UI includes powerful export functionality to create shareable visualizations:

### Cinematic MP4 Export
- Records video of the graph visualization with smooth camera movements
- **Camera Movement:** Automatically zooms out from 5% to 2% as graph expands (matches expansion)
- **Duration:** Configurable (5-600 seconds, default: 60 seconds)
- **FPS:** Configurable (15-60 FPS, default: 30 FPS)
- **Output:** Downloads as `.mp4` file
- **Use Case:** Create shareable videos showing graph evolution

### Interactive HTML Export
- Creates self-contained HTML file with full interactivity
- **Includes:** All graph data, D3.js visualization, filters, navigation
- **Output:** Downloads as `.html` file
- **Use Case:** Share interactive visualization that works offline

### How to Export
1. Open web UI at http://localhost:5000
2. Wait for graph to load
3. In the "Export Art" panel:
   - Choose format: "Cinematic MP4" or "Zoomable HTML"
   - Set Duration (seconds): Default 60, range 5-600
   - Set FPS: Default 30, range 15-60
   - Click "Export Video" button
4. Wait for export to complete (shows progress)
5. File will download automatically

**Example:** Export 60 seconds at 30 FPS = 1,800 frames of graph evolution

---

## 🤖 Convergence Research Assistant (CRA)

The Causation Explorer includes an AI-powered research assistant that helps you understand the system and explore the graph visualization.

### Features

**Vision Model:**
- Analyzes the current graph viewport to understand what you're seeing
- Describes visible nodes, clusters, connections, and patterns
- Responds to questions like "What am I looking at?" or "Describe this view"

**Research Model:**
- Answers complex questions about the Butterfly System
- Uses full context from shared state, logs, and graph data
- Knows everything about system components, settings, and their functions
- Provides meaningful insights and discovery-oriented guidance

**Context-Aware:**
- Automatically includes system state from `.shared_simulation_state.json`
- Includes view state (zoom, pan, rotation, selected nodes)
- Includes recent log entries from all system logs
- Updates context in real-time as you navigate

### Using the CRA Agent

**1. Start the Web UI:**
```bash
python causation_web_ui.py
```

**2. Open the Chat Panel:**
- The CRA chat panel is located below the graph visualization
- It's positioned to the right of the settings panel

**3. Select Models:**
- **Research Model:** Choose your preferred language model (e.g., `llama3`, `mistral`)
- **Vision Model:** Choose a vision-capable model (e.g., `llava`, `bakllava`)
- Models are dynamically loaded from your local Ollama installation

**4. Ask Questions:**
- **About the System:** "What does the breath engine do?" or "Explain violation pressure"
- **About the Graph:** "What am I looking at?" or "Describe this cluster"
- **About Settings:** "What does this setting do?" or "How do I adjust the zoom?"
- **Discovery Questions:** "What patterns do you see?" or "What should I investigate?"

**5. Get Visual Analysis:**
- The agent automatically captures the current graph viewport
- It uses the vision model to analyze what you're seeing
- Ask questions about the visualization to get detailed descriptions

### Example Interactions

**System Understanding:**
```
You: "What is the Butterfly System?"

CRA: "The Butterfly System is a unified architecture with three components:
- Left Wing: Reality Simulator (network evolution)
- Central Body: Explorer (breath engine, phase transitions)
- Right Wing: Djinn Kernel (violation pressure calculations)

The breath engine drives all three systems synchronously..."
```

**Graph Analysis:**
```
You: "What am I seeing in this graph?"

CRA: "You're viewing a causation graph with 342 nodes and 1,156 links.
The largest cluster (center-left) represents network events from the Reality
Simulator. The yellow nodes are Explorer phase transitions. The magenta
connections show VP calculations from the Djinn Kernel..."
```

**Discovery Guidance:**
```
You: "What should I investigate next?"

CRA: "Based on the graph structure, I notice strong connections between
modularity changes and network collapses. Consider exploring the backwards
trail from any collapse event to understand the contributing factors..."
```

### Requirements

**Ollama Installation:**
- Download and install from https://ollama.ai
- Run: `ollama serve` (default port: 11434)
- Install models: `ollama pull llama3` or `ollama pull llava`

**Model Recommendations:**
- **Research:** `llama3`, `mistral`, `codellama`
- **Vision:** `llava`, `bakllava`

**Note:** The agent dynamically detects available models from your Ollama installation, so you can use any models you have downloaded.

---

## 📊 Get Statistics

```python
explorer = system.causation_explorer

stats = explorer.get_causation_stats()

print(f"Total Events: {stats['total_events']}")
print(f"Total Links: {stats['total_links']}")
print(f"Components: {stats['components']}")
print(f"Event Types: {stats['event_types']}")
print(f"Graph Density: {stats['graph_density']:.3f}")

print("\n🔗 Strongest Causation Links:")
for link in stats['strongest_links'][:5]:
    print(f"  Strength: {link['strength']:.2f}")
    print(f"  Explanation: {link['explanation']}")
    print()
```

---

## 🔬 Advanced Exploration

### Explore with Custom Depth

```python
# Deep exploration (20 levels)
deep_trail = explorer.explore_backwards(event_id, max_depth=20)

# Shallow exploration (3 levels)
shallow_trail = explorer.explore_forwards(event_id, max_depth=3)
```

### Find Multiple Paths

```python
# Find shortest path
path1 = explorer.find_path(event1_id, event2_id)

# Find another path by exploring manually
backwards_from_2 = explorer.explore_backwards(event2_id)
forwards_from_1 = explorer.explore_forwards(event1_id)

# Look for intersection
common_events = set([e['event']['event_id'] for e in backwards_from_2]) & \
                set([e['event']['event_id'] for e in forwards_from_1])
```

### Filter by Causation Type

```python
# Get all causation links
graph = explorer.causation_graph

# Filter by type
threshold_links = [(u, v, data) for u, v, data in graph.edges(data=True)
                   if data.get('causation_type') == 'threshold']

correlation_links = [(u, v, data) for u, v, data in graph.edges(data=True)
                     if data.get('causation_type') == 'correlation']

print(f"Threshold causations: {len(threshold_links)}")
print(f"Correlation causations: {len(correlation_links)}")
```

---

## 💡 Practical Tips

### 1. Let System Run First
The Causation Explorer loads from historical log files. For best results:
- Run the system for at least 50-100 breath cycles
- This generates enough events to see interesting causation chains

### 2. Use Search First
```python
# Don't guess event IDs - search for them
events = explorer.search_events("your_search_term")
event_id = events[0]['event_id']  # Pick the first match
```

### 3. Check Statistics
```python
stats = explorer.get_causation_stats()
if stats['total_events'] < 10:
    print("⚠️  Not enough events yet. Run system longer.")
```

### 4. Explore Incrementally
Start with shallow exploration (max_depth=3), then go deeper:
```python
# Shallow first
shallow = explorer.explore_backwards(event_id, max_depth=3)

# If interesting, go deeper
deep = explorer.explore_backwards(event_id, max_depth=10)
```

---

## 📝 Example Session

```python
from unified_entry import UnifiedSystem
import time

# 1. Start system
print("🚀 Starting system...")
system = UnifiedSystem()
explorer = system.causation_explorer

# 2. Run simulation
print("⏱️  Generating events (running 100 cycles)...")
for i in range(100):
    system.controller.run_genesis_phase()
    time.sleep(0.05)

# 3. Check what we have
stats = explorer.get_causation_stats()
print(f"\n📊 Generated {stats['total_events']} events with {stats['total_links']} causation links")

# 4. Find interesting events
all_events = explorer.search_events("")
print(f"\n🔍 Found {len(all_events)} total events")

# 5. Explore most recent event
if all_events:
    recent = all_events[-1]  # Most recent
    event_id = recent['event_id']
    
    print(f"\n🔬 Exploring: {recent['component']} - {recent['event_type']}")
    
    # What caused it?
    causes = explorer.explore_backwards(event_id, max_depth=5)
    print(f"\n🔙 Caused by {len(causes)} events:")
    for cause in causes[:5]:
        print(f"  → {cause['event']['component']}: {cause['event']['event_type']}")
    
    # What did it cause?
    effects = explorer.explore_forwards(event_id, max_depth=5)
    print(f"\n🔜 Caused {len(effects)} events:")
    for effect in effects[:5]:
        print(f"  → {effect['event']['component']}: {effect['event']['event_type']}")

print("\n✅ Exploration complete!")
```

---

## 🎯 Key Methods Reference

| Method | What It Does | Example |
|--------|-------------|---------|
| `search_events(query)` | Find events by keyword | `explorer.search_events("collapse")` |
| `explore_backwards(id, depth)` | What caused this? | `explorer.explore_backwards(event_id, max_depth=10)` |
| `explore_forwards(id, depth)` | What did this cause? | `explorer.explore_forwards(event_id, max_depth=10)` |
| `find_path(from_id, to_id)` | Shortest causation path | `explorer.find_path(evt1, evt2)` |
| `get_event_summary(id)` | Full event details | `explorer.get_event_summary(event_id)` |
| `get_causation_stats()` | Graph statistics | `explorer.get_causation_stats()` |

---

## 🐛 Troubleshooting

### "No events found"
```python
# Check if explorer loaded data
stats = explorer.get_causation_stats()
print(f"Events: {stats['total_events']}")

# If 0, check log files exist
from pathlib import Path
log_dir = Path('data/logs')
print(f"Log directory exists: {log_dir.exists()}")
print(f"Log files: {list(log_dir.glob('*.log'))}")
```

### "Explorer is None"
```python
# Make sure system initialized properly
if system.causation_explorer is None:
    print("⚠️  Causation Explorer not initialized")
    print("   Check initialization logs for errors")
else:
    print("✅ Causation Explorer is ready")
```

### Web UI not loading / Showing plain text instead of HTML
```bash
# Install Flask
pip install flask

# Check if template exists
ls templates/causation_explorer.html

# Run web UI
python causation_web_ui.py

# Check health endpoint
curl http://localhost:5000/health
```

**If you see plain text instead of the rendered page:**
1. **Check the health endpoint** - Visit http://localhost:5000/health to see diagnostic info
2. **Check Flask console output** - Look for error messages in the terminal
3. **Verify template path** - The health endpoint will tell you if the template exists
4. **Check browser console** - Press F12 to see JavaScript errors
5. **Try a different browser** - Some browsers have strict security settings

**Common issues:**
- **Template not found** - Make sure `templates/causation_explorer.html` exists
- **Causation Explorer not initialized** - Check terminal for initialization errors
- **Flask error page** - If you see a Flask error/traceback, check the specific error message
- **JavaScript disabled** - The page requires JavaScript for D3.js visualization

---

## 📚 Next Steps

1. **Run the system** - Generate events by running `python unified_entry.py`
2. **Explore interactively** - Use Python script to explore causation
3. **Launch Web UI** - Visual exploration at http://localhost:5000
4. **Add real-time tracking** - Implement Phase 2 for live causation detection

**The Causation Explorer transforms "what happened" into "why it happened" - your scientific investigation partner!** 🔬🦋

