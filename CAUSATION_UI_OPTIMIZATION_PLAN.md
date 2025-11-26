# 🚀 Causation Web UI Visualization Optimization Plan

## Current Performance Issues

### 1. **Full Graph Reload on Every Update**
- **Problem**: `/api/graph` returns entire graph (all nodes + links) every time
- **Impact**: Large JSON payloads, full D3 re-render, simulation restart
- **Location**: `causation_web_ui.py:3388` (get_graph endpoint), `templates/causation_explorer.html:6933` (loadGraph on new events)

### 2. **D3 Force Simulation Restart**
- **Problem**: Every `renderGraph()` call creates new D3 force simulation
- **Impact**: Loses physics state, expensive to restart, causes jittery animations
- **Location**: `templates/causation_explorer.html:5073` (new simulation created every time)

### 3. **Shared State File Read on Every Request**
- **Problem**: Reads `data/.shared_simulation_state.json` on every `/api/graph` request
- **Impact**: File I/O overhead, unnecessary processing
- **Location**: `causation_web_ui.py:3434` (loads shared state on every graph request)

### 4. **No Incremental Updates**
- **Problem**: No API endpoint for "just new events since timestamp X"
- **Impact**: Must reload entire graph even for small changes
- **Location**: Missing - need to create incremental update endpoint

### 5. **Inefficient Live Mode Polling**
- **Problem**: Polls every 2 seconds, triggers full graph reload on each update
- **Impact**: Constant reloads, browser becomes unresponsive
- **Location**: `templates/causation_explorer.html:6867` (2s interval), `6911` (fetchNewEvents)

---

## Optimization Strategy

### Phase 1: Backend Optimizations (High Impact, Low Risk)

#### 1.1 Add Graph Data Caching
**Goal**: Cache processed graph data to avoid repeated file reads and processing

```python
# Add to causation_web_ui.py
graph_cache = {
    'nodes': [],
    'links': [],
    'last_update': 0,
    'cache_duration': 1.0  # Cache for 1 second
}

@app.route('/api/graph')
def get_graph():
    # Check cache first
    current_time = time.time()
    if current_time - graph_cache['last_update'] < graph_cache['cache_duration']:
        return jsonify({
            'nodes': graph_cache['nodes'],
            'links': graph_cache['links'],
            'cached': True
        })
    
    # ... existing graph loading logic ...
    
    # Update cache
    graph_cache['nodes'] = nodes
    graph_cache['links'] = links
    graph_cache['last_update'] = current_time
```

**Benefits**: 
- Reduces file I/O by ~95%
- Faster response times for rapid requests
- Lower CPU usage

---

#### 1.2 Add Incremental Update Endpoint
**Goal**: Only send new/changed events instead of full graph

```python
@app.route('/api/graph/incremental')
def get_incremental_updates():
    """Get only new events since last timestamp"""
    since_timestamp = request.args.get('since', 0, type=float)
    
    new_nodes = []
    new_links = []
    
    with explorer.graph_lock:
        for event_id, event in explorer.events.items():
            if event.timestamp > since_timestamp:
                # Add to new_nodes
                new_nodes.append({...})
        
        # Get new links (edges added since timestamp)
        # Need to track when links were created
        # ...
    
    return jsonify({
        'new_nodes': new_nodes,
        'new_links': new_links,
        'latest_timestamp': max(e.timestamp for e in explorer.events.values())
    })
```

**Benefits**:
- 90-99% reduction in JSON payload size
- Faster updates
- Less browser memory usage

---

#### 1.3 Track Last Graph Version
**Goal**: Only process shared state if file has actually changed

```python
last_shared_state_mtime = 0

@app.route('/api/graph')
def get_graph():
    shared_state_path = Path('data/.shared_simulation_state.json')
    
    if shared_state_path.exists():
        file_mtime = os.path.getmtime(shared_state_path)
        
        # Only reload if file actually changed
        if file_mtime > last_shared_state_mtime:
            explorer._load_from_shared_state(force_reload=False)
            last_shared_state_mtime = file_mtime
```

**Benefits**:
- Skips unnecessary file reads
- Faster response when no changes

---

### Phase 2: Frontend Optimizations (High Impact, Medium Risk)

#### 2.1 Incremental Graph Updates (Don't Restart Simulation)
**Goal**: Add/remove nodes/links without recreating D3 simulation

```javascript
function updateGraphIncremental(newData) {
    if (!simulation) {
        // First load - use full render
        renderGraph();
        return;
    }
    
    // Get current node/link IDs
    const existingNodeIds = new Set(allNodes.map(n => n.id));
    const existingLinkIds = new Set(allLinks.map(l => `${l.source.id}-${l.target.id}`));
    
    // Add new nodes
    const newNodes = newData.new_nodes.filter(n => !existingNodeIds.has(n.id));
    if (newNodes.length > 0) {
        allNodes.push(...newNodes);
        
        // Add to simulation
        simulation.nodes(allNodes);
        simulation.alpha(0.3).restart(); // Gentle restart to position new nodes
    }
    
    // Add new links
    const newLinks = newData.new_links.filter(l => {
        const linkId = `${l.source}-${l.target}`;
        return !existingLinkIds.has(linkId);
    });
    if (newLinks.length > 0) {
        allLinks.push(...newLinks);
        
        // Update link force
        simulation.force('link').links(allLinks);
        simulation.alpha(0.3).restart();
    }
    
    // Update DOM elements (incremental)
    updateNodesIncremental(newNodes);
    updateLinksIncremental(newLinks);
}
```

**Benefits**:
- No simulation restart = smoother animations
- Faster updates (only render new elements)
- Preserves user's zoom/pan state

---

#### 2.2 Optimize D3 Force Simulation Settings
**Goal**: Make simulation faster and more stable

```javascript
simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .alphaDecay(0.02)  // Faster decay = settles quicker
    .velocityDecay(0.6)
    .alphaMin(0.01)    // Stop earlier
    .stop();           // Don't auto-start, control manually

// Run simulation for fixed number of ticks
for (let i = 0; i < 300; i++) {
    simulation.tick();
}

// Then update DOM once
updateVisualization();
```

**Benefits**:
- 70% faster initial layout
- Less jittery animations
- Better control over when updates happen

---

#### 2.3 Better Live Mode Throttling
**Goal**: Smarter polling that doesn't trigger unnecessary reloads

```javascript
let lastUpdateTimestamp = 0;
let pendingUpdate = false;

function fetchNewEvents() {
    if (pendingUpdate) {
        return; // Already queued
    }
    
    pendingUpdate = true;
    
    fetch(`/api/graph/incremental?since=${lastUpdateTimestamp}`)
        .then(response => response.json())
        .then(data => {
            pendingUpdate = false;
            
            if (data.new_nodes.length === 0 && data.new_links.length === 0) {
                return; // No updates
            }
            
            // Update timestamp
            lastUpdateTimestamp = data.latest_timestamp;
            
            // Incremental update (doesn't restart simulation)
            updateGraphIncremental(data);
        });
}
```

**Benefits**:
- Only updates when there are actual changes
- Prevents update queue buildup
- Smoother experience

---

#### 2.4 Debounce Rapid Updates
**Goal**: Batch multiple rapid updates into single render

```javascript
let updateDebounceTimer = null;

function scheduleGraphUpdate(data) {
    // Clear existing timer
    if (updateDebounceTimer) {
        clearTimeout(updateDebounceTimer);
    }
    
    // Accumulate updates
    accumulatedUpdates.push(data);
    
    // Schedule update after 500ms of inactivity
    updateDebounceTimer = setTimeout(() => {
        // Apply all accumulated updates at once
        const merged = mergeUpdates(accumulatedUpdates);
        updateGraphIncremental(merged);
        accumulatedUpdates = [];
        updateDebounceTimer = null;
    }, 500);
}
```

**Benefits**:
- Fewer renders = better performance
- Smoother animations
- Less CPU usage

---

### Phase 3: Advanced Optimizations (Medium Impact, Higher Risk)

#### 3.1 Web Workers for Graph Processing
**Goal**: Move heavy graph calculations to background thread

- Process node/link filtering in Web Worker
- Calculate layouts in parallel
- Only send results to main thread for rendering

#### 3.2 Virtual Scrolling for Large Graphs
**Goal**: Only render nodes/links visible in viewport

- Use quadtree for spatial queries
- Render only visible + buffer zone
- Update as user pans/zooms

#### 3.3 Canvas Rendering for Large Graphs
**Goal**: Switch from SVG to Canvas for better performance

- Canvas is faster for 1000+ elements
- Keep SVG for interactive elements (tooltips, labels)
- Hybrid approach: Canvas for background, SVG overlay for UI

---

## Implementation Priority

### **HIGH PRIORITY** (Implement First)
1. ✅ Graph data caching (backend)
2. ✅ Incremental update endpoint (backend)
3. ✅ Incremental graph updates (frontend - don't restart simulation)
4. ✅ Better live mode throttling

**Expected Impact**: 5-10x faster updates, 80% less CPU usage

### **MEDIUM PRIORITY** (Implement After High Priority)
5. Track last graph version (skip unchanged files)
6. Optimize D3 simulation settings
7. Debounce rapid updates

**Expected Impact**: 2-3x faster initial load, smoother animations

### **LOW PRIORITY** (Future Enhancements)
8. Web Workers for processing
9. Virtual scrolling
10. Canvas rendering

**Expected Impact**: Handle 10x larger graphs, better on low-end machines

---

## Testing Strategy

### Before Optimization
- Measure: Time to load graph, FPS during updates, CPU usage
- Test with: 100, 1000, 10000 nodes

### After Each Phase
- Re-measure same metrics
- Compare performance improvements
- Check for regressions (broken features)

### Performance Targets
- **Initial Load**: < 1 second for 1000 nodes
- **Incremental Update**: < 100ms for 10 new nodes
- **Animation FPS**: 60 FPS during updates
- **CPU Usage**: < 20% during live mode

---

## Risk Assessment

### Low Risk (Safe to implement)
- Graph caching
- Better throttling
- Simulation optimization

### Medium Risk (Test thoroughly)
- Incremental updates (need to handle edge cases)
- Don't restart simulation (need to handle node removal)

### High Risk (Needs careful testing)
- Web Workers (browser compatibility)
- Canvas rendering (lose SVG benefits)

---

## Next Steps

1. **Start with Phase 1 (Backend)**: Lowest risk, highest impact
2. **Test thoroughly** after each optimization
3. **Measure improvements** to validate approach
4. **Iterate** based on results

Would you like me to start implementing these optimizations?

