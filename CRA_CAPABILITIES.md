# 🤖 Convergence Research Assistant (CRA) - Complete Capabilities Guide

**Autonomous AI Research Assistant for the Butterfly System**

---

## 🎯 Core Role

The Convergence Research Assistant (CRA) is an AI-powered research assistant that runs in the **Causation Explorer Web UI** (`causation_web_ui.py`). It monitors and analyzes the **Butterfly System** (`unified_entry.py`) through the web interface.

**Key Distinction:**
- **Butterfly System** (`unified_entry.py`) = The simulation being monitored (can run or be stopped)
- **Causation Explorer Web UI** (`causation_web_ui.py`) = The monitoring interface where CRA lives (runs independently)

---

## 🧠 Core Capabilities

### 1. Pattern Recognition Excellence
- Identify emergent patterns across quantum, network, evolution, and explorer domains
- Detect anomalies before they cascade (e.g., VP4 during Genesis phase)
- Cross-correlate metrics to reveal hidden relationships
- Recognize phase transitions and system maturity indicators

### 2. Predictive Insight Generation
- Forecast system trajectories from historical data
- Identify synchronization lags (e.g., 600 VP calculations vs 601 tape cells)
- Predict when Genesis → Sovereign phase transition might occur
- Warn about potential system instabilities before they manifest

### 3. Discovery-Oriented Communication
- Transform complex multi-system interactions into actionable insights
- Bridge technical details with strategic implications
- Help users see the 'story' their system data is telling
- Provide specific, data-driven recommendations (not generic advice)

### 4. Graph Visualization Expertise
- Understand the causation graph structure (events, links, components)
- Manipulate graph filters when explicitly requested or autonomously
- Adjust ALL visualization settings: link/node appearance, colors, depth effects, visual effects, performance
- Customize component colors and link type colors dynamically
- Interpret visual patterns in graph snapshots
- **Robust Settings Management** ⭐ NEW
  - Settings validation prevents invalid values from breaking visualization
  - Batch update mode for efficient bulk changes (prevents cascading re-renders)
  - Real-time updates during active simulation without interruption
  - Error recovery with graceful degradation

---

## 🎨 Autonomous Visualization Control

### Graph Filter Control (Autonomous)
The CRA can autonomously adjust:
- **Component Visibility:** Reality Simulator, Explorer, Djinn Kernel, Breath, System
- **Causation Type Filters:** Threshold, Correlation, Direct, Temporal
- **Display Toggles:** Node labels, links, temporal paths

**Format:** `[[GRAPH_FILTER_UPDATE: {...}]]`

**Example:**
```json
[[GRAPH_FILTER_UPDATE: {
  "components": {"explorer": true, "djinnkernel": true},
  "causation_types": {"threshold": true, "direct": true},
  "display": {"show_labels": false, "show_temporal_paths": true}
}]]
```

### Visualization Settings Control (Full Autonomy - ALL 40+ Settings)

The CRA has **COMPLETE AUTONOMOUS control** over ALL visualization settings:

#### Link Appearance
- `linkBaseWidth` (1-5px)
- `linkMaxWidth` (8-30px)
- `linkMinOpacity` (0.1-0.8)
- `linkMaxOpacity` (0.5-1.0)

#### Link Depth Effects
- `linkDensityMultiplier` (0-10)
- `linkDepthMultiplier` (0-5)
- `linkNodeConnMultiplier` (0-3)

#### Node Appearance
- `nodeBaseSize` (5-15px)
- `nodeMaxSize` (10-20px)
- `nodeMinOpacity` (0.3-0.9)
- `nodeMaxOpacity` (0.7-1.0)

#### Node Depth Effects
- `nodeDepthSizeMultiplier` (0-6)
- `nodeStrokeWidth` (1-6px)
- `nodeStrokeOpacity` (0-1.0)

#### Depth Effects
- `depthStrength` (0-2)
- `depthOpacityRange` (0-1)
- `depthSizeRange` (0-1)
- `depthParallaxAmount` (0-2)

#### Visual Effects
- `enableShadows` (true/false)
- `enableGlow` (true/false)
- `shadowOffset` (0-5px)
- `shadowBlur` (0-10)
- `glowIntensity` (0-5)

#### Color Settings
- `frontColorBrightness` (0.5-1.5)
- `backColorBrightness` (0.3-1.0)
- `colorSaturation` (0-2)

#### Component Colors (Hex Colors)
- `componentColor_reality_sim` (e.g., "#FF0000")
- `componentColor_explorer` (e.g., "#0000FF")
- `componentColor_djinn_kernel` (e.g., "#FF8800")
- `componentColor_breath` (e.g., "#FF00FF")
- `componentColor_system` (e.g., "#FFFF00")

#### Link Colors (Hex Colors)
- `linkColor_threshold` (e.g., "#FF00FF")
- `linkColor_correlation` (e.g., "#0000FF")
- `linkColor_direct` (e.g., "#00FF00")
- `linkColor_temporal` (e.g., "#FFFF00")
- `linkColor_unknown` (e.g., "#FF8800")

#### Performance
- `maxVisibleLinks` (1000-50000)
- `maxVisibleNodes` (500-20000)
- `renderQuality` ("low"/"medium"/"high")

#### Animation/Transitions
- `enableTransitions` (true/false)
- `transitionDuration` (100-1000ms)
- `animationSpeed` (0.1-3.0)

**Format:** `[[VIZ_SETTINGS_UPDATE: {...}]]`

**Example:**
```json
[[VIZ_SETTINGS_UPDATE: {
  "linkBaseWidth": 4.0,
  "depthStrength": 1.5,
  "componentColor_explorer": "#00FF00",
  "enableGlow": true,
  "renderQuality": "low"
}]]
```

**Real-Time Updates:** All settings update dynamically during simulation without interrupting it.

---

## ⚙️ Live Configuration Orchestration (Hot Reload Service)

The CRA can now adjust `config.json` while the Butterfly System keeps running. Use the guarded ConfigManager API to modify parameters and roll back if needed.

### Command Formats
- **Update:**  
  `[[CONFIG_UPDATE: {"reason": "VP mitigation", "correlation_id": "plan-alpha", "patch": [{"op": "replace", "path": "/feedback/knobs/mutation_rate/initial", "value": 0.024}]}]]`
- **Rollback:**  
  `[[CONFIG_ROLLBACK: {"steps": 1, "reason": "Undo plan-alpha"}]]`

### Workflow
1. Issue a single command — updates apply immediately (dry-run mode has been removed).
2. Review diagnostics (VP history, network trends, exploration ratio) to confirm the change is needed.
3. Include a `correlation_id` (plan name or UUID) and descriptive `reason` so `config_actions.log` stays traceable.

### Guardrails (Auto-Enforced)
| Path | Safe Range | Notes |
| --- | --- | --- |
| `/feedback/knobs/mutation_rate/initial` | 0.001 – 0.05 | Mutation knob |
| `/feedback/knobs/new_edge_rate/initial` | 0.2 – 3.0 | Connectivity growth (increased for neural signal propagation) |
| `/feedback/knobs/clustering_bias/initial` | 0.3 – 1.5 | Triangle closure bias |
| `/feedback/knobs/quantum_pruning/initial` | 0.0 – 1.0 | Pruning aggressiveness |
| `/network/max_connections` | 1,000 – 20,000 | Network density ceiling |
| `/evolution/mutation_rate_precision` | 1e-10 – 1e-2 | Precision for mutation adjustments |
| `/quantum/superposition_tolerance` | 1e-6 – 0.01 | Quantum stability |
| `/lattice/prune_threshold` | 0 – 0.01 | Particle pruning window |
| `/neural/enabled` | true/false | Neural system master toggle |
| `/neural/training/enabled` | true/false | Neural training toggle |
| `/neural/training/learning_rate` | 0.0001 – 0.1 | DQN learning rate |
| `/neural/training/epsilon_start` | 0.5 – 1.0 | Initial exploration rate |
| `/neural/training/epsilon_end` | 0.01 – 0.2 | Final exploration rate |
| `/scikit/enabled` | true/false | Scikit-learn ML system toggle |
| `/scikit/clustering/enabled` | true/false | HDBSCAN clustering toggle |
| `/scikit/anomaly_detection/enabled` | true/false | Isolation Forest toggle |
| `/scikit/dimensionality_reduction/enabled` | true/false | PCA/t-SNE toggle |

**Path Notes:** Dashes and camelCase are normalized (`/feedback/knobs/mutationrate/initial` → `/feedback/knobs/mutation_rate/initial`), but prefer underscore names.

### Expected Telemetry
- After an update, monitor `/api/cra/diagnostics/vp_history`, `/api/cra/diagnostics/network_trends`, and `/api/diagnostic/phase_sync` to confirm the change had the intended effect.
- Summaries should state: parameter, old value → new value, and the behavioral shift (e.g., “mutation rate up to 0.024 to break VP stagnation”).

### API Endpoints
- `POST /api/config/update` – guarded JSON Patch apply (supports `correlation_id`)
- `POST /api/config/rollback` – revert last N snapshots (history depth: 10)
- `GET /api/config/current` – active config + version
- `GET /api/config/history` – recent snapshots (optionally include full config payloads)

Run results are logged to `data/logs/config_actions.log` and streamed to the CRA via `config_update` / `config_rollback` events.

### Adaptive VP Unstick (New)

The Explorer now auto-corrects Genesis VP saturation. CRA can:

- Watch the event stream for `ADAPTIVE_VP_TRIGGER` messages (payload includes `vp_value`, `streak_count`, dominant trait, and actions taken such as `widen_envelope` or `queue_arbitration`).
- Query `/api/config/current` → `vp_monitoring.adaptive_response` to inspect/edit tunables (`high_vp_threshold`, `streak_threshold`, `envelope_widen_factor`).
- Use `[[CONFIG_UPDATE]]` to adjust those tunables if the system needs more/less aggression.
- Monitor `data/logs/state.log` and `get_utm_status()` output to verify that VP drops below 0.25, arbitration instructions execute, and ledger metadata markers appear.

---

## 🤖 Machine Learning Systems Control

The CRA has full configuration control over both ML subsystems via `[[CONFIG_UPDATE]]` commands.

### Neural System (PyTorch DQN)

The Neural System provides deep Q-learning for organism decision-making. Each organism has a "brain" (small neural network) that learns optimal behaviors through reinforcement learning.

#### Key Config Paths
| Path | Safe Range | Description |
| --- | --- | --- |
| `/neural/enabled` | true/false | Master toggle for neural learning system |
| `/neural/training/enabled` | true/false | Enable/disable training updates |
| `/neural/training/learning_rate` | 0.0001 – 0.1 | DQN learning rate |
| `/neural/training/epsilon_start` | 0.5 – 1.0 | Initial exploration rate |
| `/neural/training/epsilon_end` | 0.01 – 0.2 | Final exploration rate |
| `/neural/rewards/connection_success` | 0.0 – 1.0 | Reward for successful connections |
| `/neural/rewards/connection_failure` | -1.0 – 0.0 | Penalty for failed connections |
| `/neural/inheritance/enabled` | true/false | Lamarckian weight inheritance |
| `/neural/inheritance/mutation_rate` | 0.0 – 0.5 | Brain weight mutation during reproduction |

#### Example Commands
```
[[CONFIG_UPDATE: {"reason": "Activate neural learning", "correlation_id": "neural-on", "patch": [{"op": "replace", "path": "/neural/enabled", "value": true}]}]]
[[CONFIG_UPDATE: {"reason": "Faster learning", "correlation_id": "lr-boost", "patch": [{"op": "replace", "path": "/neural/training/learning_rate", "value": 0.002}]}]]
[[CONFIG_UPDATE: {"reason": "Exploit more", "correlation_id": "exploit-mode", "patch": [{"op": "replace", "path": "/neural/training/epsilon_end", "value": 0.05}]}]]
```

#### What to Monitor
- Training loss trends (should decrease over time)
- Epsilon decay progression (exploration → exploitation)
- `neural_decision` events in causation graph
- Organism fitness correlation with neural updates

### Scikit-learn ML System (Classical ML)

The Scikit-learn system provides classical machine learning algorithms for population-level analysis: clustering, anomaly detection, and dimensionality reduction.

#### Key Config Paths
| Path | Safe Range | Description |
| --- | --- | --- |
| `/scikit/enabled` | true/false | Master toggle for Scikit-learn ML system |
| `/scikit/clustering/enabled` | true/false | Enable HDBSCAN clustering |
| `/scikit/clustering/algorithm` | "hdbscan", "kmeans", "dbscan" | Clustering algorithm |
| `/scikit/clustering/min_cluster_size` | 2 – 50 | Minimum cluster size (HDBSCAN) |
| `/scikit/anomaly_detection/enabled` | true/false | Enable Isolation Forest anomaly detection |
| `/scikit/anomaly_detection/contamination` | 0.01 – 0.5 | Expected outlier proportion |
| `/scikit/anomaly_detection/n_estimators` | 10 – 500 | Number of trees in forest |
| `/scikit/dimensionality_reduction/enabled` | true/false | Enable PCA/t-SNE |
| `/scikit/dimensionality_reduction/algorithm` | "pca", "tsne", "umap" | Reduction algorithm |
| `/scikit/dimensionality_reduction/n_components` | 2 – 10 | Output dimensions |

#### Example Commands
```
[[CONFIG_UPDATE: {"reason": "Activate ML analysis", "correlation_id": "ml-on", "patch": [{"op": "replace", "path": "/scikit/enabled", "value": true}]}]]
[[CONFIG_UPDATE: {"reason": "Smaller clusters", "correlation_id": "cluster-tune", "patch": [{"op": "replace", "path": "/scikit/clustering/min_cluster_size", "value": 3}]}]]
[[CONFIG_UPDATE: {"reason": "Find more outliers", "correlation_id": "anomaly-boost", "patch": [{"op": "replace", "path": "/scikit/anomaly_detection/contamination", "value": 0.2}]}]]
[[CONFIG_UPDATE: {"reason": "Use t-SNE", "correlation_id": "tsne-viz", "patch": [{"op": "replace", "path": "/scikit/dimensionality_reduction/algorithm", "value": "tsne"}]}]]
```

#### Use Cases
- **Clustering**: Identify behavioral phenotype groups in organism population
- **Anomaly Detection**: Flag unusual organisms or system states for investigation
- **Dimensionality Reduction**: Visualize high-dimensional trait/behavior space

---

## 🧠 Context Memory System (Language-Based Selection Pressure)

The ContextMemory system provides language anchoring that shapes organism selection pressure in the SymbioticNetwork.

### Core Mechanism
- **Language Anchors**: Map words/concepts to organism IDs, creating a semantic network layer
- **Selection Pressure**: Organisms referenced in language memory get survival advantages
- **Reference Triangles**: Edges between organisms in same language cluster get stability bonuses

### Key Functions
- `apply_memory_based_selection_pressure()`: Called each generation to:
  - Penalize unreferenced organisms (-0.05 fitness, scaled by anchor density)
  - Boost edges within language clusters (+0.02 strength per cluster)
- `log_memory_stability_metrics()`: Outputs `[MEMORY_STABILITY]` metrics to console/logs

### Stability Metrics (via `/api/cra/diagnostics/memory_stability`)
- **anchor_density** (0.0-1.0): Ratio of organisms referenced in ContextMemory
- **language_coherence** (0.0-1.0): Consistency of organism-to-concept mappings
- **cluster_stability** (0.0-1.0): Stability of language-anchored clusters
- **unreferenced_penalty_count**: Organisms penalized for lack of language references
- **reference_triangle_bonus_count**: Edges boosted for closing reference triangles

### Language Subgraph
- **linguistic_integration_ratio**: Language-tagged edges / total edges
- Higher ratio = more linguistically-structured network
- Available in network stats as `linguistic_subgraph`

### Console Output Format
```
[MEMORY_STABILITY] Gen 42 - Anchor Density: 0.750, Language Coherence: 0.680, Cluster Stability: 0.820
```

### What to Watch For
- **Low anchor density**: Organisms disconnected from language concepts
- **Low coherence**: Fragmented or inconsistent concept mappings
- **Low cluster stability**: Unstable language-based groupings

---

## 🎯 Graph View Assistance (Manual Execution)

The CRA no longer sends `[[VIEW_UPDATE]]` commands. All camera movement is under your control through the navigation pad (zoom box, pan arrows, drag-to-zoom, rotation buttons).  
When the CRA needs to highlight something visually, it will:

- Describe exactly where to move (e.g., “zoom to 150% and center on `evt_firefly_842`”).
- Provide context about why a particular region or component needs attention.
- Suggest values for zoom/pan/rotation that you can dial in yourself.

This keeps the screen stable and prevents unexpected jumps while you are mid-inspection, while still giving you precise guidance from the assistant.

---

## 💻 PC System Resource Monitoring

The CRA monitors your PC resources and correlates them with Butterfly System activity:

### Available Metrics
- **CPU Usage:** Total, per-core, process-specific
- **Memory Usage:** Total, used, available, process-specific
- **Disk Usage:** Total, used, free
- **Butterfly System Resources:** Lattice CPU, RAM usage
- **Resource Correlation:** Butterfly vs. total PC resources

### Automatic Protection
- Warns if PC is being overtaxed (>85% CPU/RAM)
- Can proactively suggest visualization performance adjustments
- Example: If CPU >85%, suggests: `[[VIZ_SETTINGS_UPDATE: {"renderQuality": "low", "maxVisibleLinks": 5000}]]

**Endpoints:**
- `/api/cra/system/state` - Current system state with PC resources
- `/api/cra/health/check` - Comprehensive health check with resource correlation

---

## 🔍 Diagnostic Data Access

The CRA has access to specialized diagnostic endpoints:

1. **Historical VP Data:** `/api/cra/diagnostics/vp_history?breaths=50`
   - Returns VP calculation values over last N breath cycles
   - Use when investigating VP anomalies or trends

2. **Network Metrics Trends:** `/api/cra/diagnostics/network_trends?points=50`
   - Returns modularity, clustering coefficient, and connection density trends
   - Use when analyzing network topology evolution

3. **Component Memory Breakdown:** `/api/cra/diagnostics/memory_breakdown`
   - Returns per-component memory allocation
   - Use when investigating resource utilization issues

4. **Event Bus Throughput:** `/api/cra/diagnostics/event_throughput`
   - Returns events per second, total events, causation links, event type distribution
   - Use when analyzing system activity and event generation rates

5. **Breath Cycle Statistics:** `/api/cra/diagnostics/breath_cycles`
   - Returns breath cycle duration, total cycles, inhale/exhale ratios
   - Use when investigating timing or synchronization issues

6. **Memory Stability Metrics:** `/api/cra/diagnostics/memory_stability` ⭐ NEW
   - Returns ContextMemory stability metrics from the SymbioticNetwork
   - **anchor_density**: Ratio of organisms referenced in language memory (0.0-1.0)
   - **language_coherence**: Consistency of organism-to-concept mappings (0.0-1.0)
   - **cluster_stability**: Stability of language-anchored clusters (0.0-1.0)
   - **unreferenced_penalty_count**: Organisms penalized for not being in language memory
   - **reference_triangle_bonus_count**: Edges boosted for closing reference triangles
   - **linguistic_integration_ratio**: Ratio of language-tagged edges to total edges
   - **USE THIS** when investigating how language memory shapes network evolution

7. **VP Diagnostics Breakdown:** `/api/diagnostic/vp_diagnostics`
   - Detailed trait-by-trait breakdown of VP calculation
   - Trait values, envelope centers, deviations, per-trait VPs
   - Normalization factors and VP contribution ratios
   - Dominant trait identification (which trait is driving high VP?)
   - **USE THIS** when investigating why VP is high or saturating
   - Diagnostic data is logged to `data/logs/vp_diagnostics.log` if diagnostics enabled

8. **VP Component Decomposition:** `/api/diagnostic/vp_components`
   - Weighted component breakdown showing which components drive VP:
     * `trait_divergence` (25%): Average deviation from stability centers
     * `network_coherence` (20%): Coherence of network traits
     * `phase_mismatch` (15%): Mismatch in prosocial traits
     * `evolution_pressure` (20%): Pressure from meta-traits
     * `quantum_entropy` (20%): Entropy in trait distribution
   - Combined VP from weighted geometric mean
   - **USE THIS** to identify which component is causing VP saturation

8. **VP Stabilization History:** `/api/diagnostic/vp_stabilization` ⭐ NEW
   - VP stabilization history (last 10 values if stabilization enabled)
   - Raw vs stabilized VP comparison
   - Jump limiting information (max jump per calculation)
   - **USE THIS** to see if stabilization is smoothing VP transitions

9. **VP Adaptive Thresholds:** `/api/diagnostic/vp_thresholds` ⭐ NEW
   - Current adaptive thresholds based on system phase
   - Genesis vs Sovereign threshold differences
   - Historical variance-based adjustments
   - **USE THIS** to understand why VP classification might differ from base thresholds

**VP Monitoring Redesign:** See `VP_MONITORING_REDESIGN.md` for complete documentation on the VP monitoring system redesign that addresses VP saturation issues.

---

## 📊 System Context Awareness

### Historical Analysis Mode (System Stopped)
- Works with historical data from previous runs
- Reads from `data/shared_state.json` (last saved state)
- Reads from `data/logs/*.log` (all historical logs)
- Focuses on pattern discovery and post-mortem diagnostics
- Uses phrases like "Based on historical data...", "From the previous run..."

### Live Monitoring Mode (System Running)
- Provides real-time monitoring guidance
- Watches for active anomalies and suggests immediate actions
- Monitors data freshness (warns if data is stale >10 seconds)
- Can suggest real-time adjustments to visualization or system parameters

**System Status Detection:**
- 🟢 SYSTEM IS RUNNING = Live data (real-time analysis)
- 🔴 SYSTEM IS STOPPED = Historical data (pattern analysis)

---

## 📋 System Log Files (CRITICAL DATA SOURCES)

The CRA has access to **8 log files** that track different aspects of the Butterfly System. These logs are **CRITICAL** for understanding system behavior and diagnosing issues.

### Log File Details

#### 1. `breath.log` - **CRITICAL: Breath Engine Cycles**
- **Purpose**: The living pulse of the Butterfly System - the central rhythm that drives everything
- **Format**: `timestamp|level|breath|cycle:N|depth:0.XXX|phase:0.XXX|pulse:0.XXX`
- **Contains**:
  - `cycle`: Breath cycle count (increments with each complete cycle)
  - `depth`: Breath depth (0.0-1.0, sine wave from inhale to exhale)
  - `phase`: Breath phase (0.0-2π, position in the breath cycle)
  - `pulse`: Breath intensity/pulse (0.0-1.0, intensity of the breath)
- **IMPORTANCE**: This is the **central rhythm** that drives the entire Butterfly System
- **WATCH FOR**: 
  - Missing or empty `breath.log` = system not breathing = **CRITICAL FAILURE**
  - Stagnant cycle count = breath engine stopped
  - Abnormal depth/phase patterns = system stress or malfunction

#### 2. `state.log` - **CRITICAL: Unified State Snapshots**
- **Purpose**: Complete unified state snapshots combining all systems at each moment
- **Format**: `timestamp|level|state|metric:value|metric:value|...`
- **Contains**: Flattened unified state with prefixes:
  - `reality_sim_*`: Reality Simulator metrics (organism_count, connection_count, modularity, etc.)
  - `explorer_*`: Explorer metrics (phase, vp_calculations, sovereign_ids_count, etc.)
  - `djinn_*`: Djinn Kernel metrics (violation_pressure, vp_classification, vp_calculations, trait_count, etc.)
  - `timestamp`: System timestamp
- **IMPORTANCE**: Complete system state at each moment - **all metrics in one place**
- **WATCH FOR**:
  - Missing or empty `state.log` = no unified state tracking = **DATA LOSS**
  - Missing prefixes = incomplete state capture
  - Stale timestamps = system not updating

#### 3. `reality_sim.log` - Reality Simulator Network Evolution
- **Purpose**: Tracks network topology and evolution metrics
- **Format**: `timestamp|level|reality_sim|orgs:N|conns:N|mod:0.XXX|clust:0.XXX|path:0.XX|gen:N`
- **Contains**:
  - `orgs`: Organism count
  - `conns`: Connection count
  - `mod`: Modularity (0.0-1.0, network structure measure)
  - `clust`: Clustering coefficient (0.0-1.0, local connectivity)
  - `path`: Average path length (network diameter measure)
  - `gen`: Generation number (evolution progress)

#### 4. `explorer.log` - Explorer (Central Body) State
- **Purpose**: Tracks Explorer phase, VP calculations, and capabilities
- **Format**: `timestamp|level|explorer|phase:str|vp_calcs:N|sovereign_ids:N|math_cap:bool`
- **Contains**:
  - `phase`: Current phase (genesis/sovereign)
  - `vp_calcs`: VP calculations count
  - `sovereign_ids`: Sovereign IDs count
  - `math_cap`: Mathematical capability (boolean)

#### 5. `djinn_kernel.log` - Djinn Kernel Violation Pressure
- **Purpose**: Tracks violation pressure calculations and classifications
- **Format**: `timestamp|level|djinn_kernel|vp:0.XXX|vp_class:str|vp_calcs:N|traits:N`
- **Contains**:
  - `vp`: Violation pressure value (0.0-1.0)
  - `vp_class`: VP classification (VP0, VP1, VP2, VP3, VP4)
  - `vp_calcs`: VP calculations count
  - `traits`: Trait count

#### 6. `vp_diagnostics.log` - **NEW**: VP Diagnostic Breakdowns ⭐
- **Purpose**: Detailed VP diagnostic breakdowns (only if diagnostics enabled)
- **Format**: `timestamp|vp_diagnostics|trait_breakdown|{JSON}` or `calculation_summary|{JSON}`
- **Contains**:
  - Per-trait breakdowns (trait values, envelope centers, deviations, trait VPs)
  - Envelope analysis (center, radius, compression factor)
  - Normalization factors and VP contribution ratios
  - Calculation summaries (total VP, per-trait breakdown, dominant trait)
- **PATH**: `data/logs/vp_diagnostics.log`
- **ONLY EXISTS** if `vp_monitoring.diagnostics_enabled=true` in config.json
- **USE THIS** to understand what's driving VP saturation or high values
- **See also**: `VP_MONITORING_REDESIGN.md` for complete VP monitoring documentation

#### 7. `system.log` - System-Level Events
- **Purpose**: System lifecycle events, initialization, shutdown, errors
- **Format**: `timestamp|level|system|event:str|...`
- **Contains**:
  - System initialization events
  - Shutdown events
  - Error events
  - Component initialization status

#### 8. `application.log` - Application-Level Logging
- **Purpose**: Web UI, Flask, and general application activity
- **Format**: Standard application logging (not pipe-delimited)
- **Contains**:
  - Web UI events
  - API calls
  - General application activity

### Log Format Standard

**All logs (except `application.log`) use pipe-delimited format:**
```
timestamp|level|component|metric:value|metric:value|...
```

**Example:**
```
23:37:11.608|DEBUG|breath|cycle:42|depth:0.750|phase:1.234|pulse:0.850
23:37:11.609|DEBUG|state|timestamp:1703456231.609|reality_sim_organism_count:150|explorer_phase:genesis|djinn_vp:0.450
```

### CRA Responsibilities

1. **Monitor Logs**: The CRA MUST monitor these logs, especially `breath.log` and `state.log`
2. **Alert Conditions**: 
   - If `breath.log` or `state.log` are empty or missing = **CRITICAL ISSUE**
   - System is not logging properly = data loss
3. **Analysis**: Use logs to:
   - Understand system behavior
   - Detect patterns and anomalies
   - Diagnose issues
   - Correlate events across components
4. **Correlation**: Cross-reference log data with:
   - Graph events
   - Shared state (`data/.shared_simulation_state.json`)
   - Time-series trends
   - Anomaly detection results

### Access Method

- **Endpoint**: `/api/cra/logs`
- **Returns**: Last 50 lines from each log file
- **Format**: JSON with log file names as keys, content as arrays of log lines

---

## 🎬 Vision Model Integration

### Graph Analysis
- Analyzes current graph viewport (SVG to base64)
- Analyzes evolutionary snapshots (up to 10 images)
- Provides visual descriptions of network structure and evolution
- Enhanced prompts ensure correct interpretation (network graphs, not biological artwork)

### Evolutionary Analysis
- Compares multiple snapshots over time
- Describes graph topology changes, node movement, cluster formation
- Identifies structural evolution patterns
- Sequential analysis for multiple images (bypasses payload limits)

### Snapshot System
- Automatic capture (1-second intervals)
- Local single-source storage (shared by viewer, vision analysis, video export)
- Historical queue keeps up to 10 snapshots per request (oldest → newest). If more are available, they’re evenly sampled across the run so the timeline stays representative.
- Vision pipeline now streams every collected snapshot sequentially (one API call per image, ~100 KB each) which bypasses the 150 KB cloud limit while preserving full fidelity.
- Used for vision analysis and snapshot-based video creation

---

## 🛡️ System Custodian Role

The CRA acts as a **System Custodian** with:

### Continuous Health Monitoring
- Background monitoring thread
- Periodic health checks
- Anomaly detection
- Resource protection

### Protective Guardian Mode
- Can enable protective monitoring
- Automatic warnings for critical issues
- Proactive system protection
- Resource correlation analysis

**Endpoints:**
- `/api/cra/status` - Custodian status and capabilities
- `/api/cra/health/check` - Comprehensive health check
- `/api/cra/guardian/mode` - Enable protective monitoring

---

## 📡 API Endpoints

### Data Access
- `/api/cra/data` - Comprehensive system data
- `/api/cra/system/state` - Current system state with PC resources
- `/api/cra/logs` - Log file access
- `/api/cra/config` - Configuration access

### Real-Time Events
- `/api/cra/events/stream` - Server-Sent Events stream
- `/api/cra/events/recent` - Recent events

### Graph Control
- `/api/cra/graph/filters` (GET/POST) - Graph filter settings
- `/api/cra/graph/viz-settings` (GET/POST) - Visualization settings

### Diagnostics
- `/api/cra/diagnostics/vp_history` - Historical VP data
- `/api/cra/diagnostics/network_trends` - Network trends
- `/api/cra/diagnostics/memory_breakdown` - Memory breakdown
- `/api/cra/diagnostics/event_throughput` - Event throughput
- `/api/cra/diagnostics/breath_cycles` - Breath cycle stats
- `/api/cra/diagnostics/memory_stability` - ContextMemory stability metrics

### ML Analysis (Scikit-learn) ⭐ NEW
- `/api/ml/status` - Check sklearn availability and ML config
- `/api/ml/analysis` - Full ML analysis (clustering, anomalies, reduction)
- `/api/ml/clusters` - Current phenotype cluster assignments
- `/api/ml/anomalies` - Detected anomalous organisms
- `/api/ml/reduction` - Dimensionality-reduced coordinates

### VP Monitoring Diagnostics ⭐ NEW
- `/api/diagnostic/vp_diagnostics` - VP diagnostic breakdown (trait-by-trait analysis)
- `/api/diagnostic/vp_components` - VP component decomposition (weighted components)
- `/api/diagnostic/vp_stabilization` - VP stabilization history
- `/api/diagnostic/vp_thresholds` - Adaptive threshold information

### Phase Sync Diagnostics
- `/api/diagnostic/phase_sync` - Phase synchronization data
- `/api/diagnostic/exploration_ratio` - Exploration-to-precision ratio tracking
- `/api/diagnostic/unified_health` - Unified system health metrics
- `/api/diagnostic/transition_status` - Transition readiness status
- `/api/diagnostic/collapse_prediction` - Network collapse prediction

### Health & Status
- `/api/cra/status` - Custodian status
- `/api/cra/health/check` - Health check
- `/api/cra/guardian/mode` - Guardian mode
- `/api/cra/config/validate` - Config validation

---

## 💬 Response Style

The CRA provides:
- **Structured responses** with clear sections and headers
- **Evidence-based analysis** citing specific data points
- **Actionable insights** with specific next steps
- **Discovery focus** framing findings as discoveries, not just observations

**Example Response Structure:**
```
## 🔍 Pattern Discovery: [Pattern Name]

**What I Found**: [Specific finding with data]
**Why It Matters**: [Implication]
**Evidence**: [Specific metrics/values]

## 💡 Recommended Investigation

1. [Specific action with graph filter suggestion]
2. [Specific metric to monitor]
3. [Specific question to explore]
```

---

## 🎯 When to Use CRA

### Pre-Flight Diagnostics
- System is stopped, analyzing historical data
- Identify patterns that may affect future runs
- Post-mortem analysis of previous runs

### Live Monitoring
- System is running, real-time analysis
- Watch for active anomalies
- Get immediate guidance on system behavior

### Visualization Assistance
- Ask CRA to highlight specific patterns
- Request visualization adjustments for clarity
- Get recommendations for graph views

### Performance Optimization
- PC resource monitoring
- Visualization performance tuning
- System resource correlation analysis

---

## 🔧 Technical Details

### System Prompt
The CRA receives a comprehensive system prompt that includes:
- Complete architectural understanding (Butterfly System vs. Web UI)
- All available capabilities and endpoints
- Response style guidelines
- Context-aware behavior instructions

### Context Building
The CRA receives rich context including:
- Current system state (from `shared_state.json`)
- System status (running/stopped, data freshness)
- Graph context (link density, component distribution, temporal analysis)
- Time-series trends and anomaly detection
- Configuration files
- Recent logs

### Vision Model Integration
- Images sent to vision model via `/api/chat` endpoint (native Ollama format)
- Sequential analysis for multiple images
- Enhanced prompts for correct graph interpretation
- Base64 image validation and compression

---

## 📝 Notes

- The CRA runs in the **Causation Explorer Web UI**, not in the Butterfly System itself
- The CRA can analyze both **historical** (stopped system) and **live** (running system) data
- All visualization adjustments are **real-time** and don't interrupt the simulation
- The CRA has **complete autonomous control** over all graph filters and visualization settings
- Color customization is **fully implemented and working**

---

**Last Updated:** 2025-11-26  
**Status:** ✅ Complete and fully functional

---

## 📸 Snapshot System Features

### Snapshot Gallery
- **Thumbnail Grid View**: Browse all captured snapshots in a grid layout
- **Click to View**: Click any thumbnail to open full-screen overlay viewer
- **Selection System**: Checkboxes on each thumbnail for multi-select
- **Analyze Selected**: Send selected snapshots to vision model for analysis
- **Create Video**: Generate MP4 videos directly from selected snapshots (FFmpeg backend)
- **Single Source**: All snapshots stored in `snapshotHistory` (localStorage)
  - Used by snapshot viewer, vision analysis, and video export
  - No duplicate snapshot creation

### Snapshot Viewer
- **Full-Screen Overlay**: Dark modal overlay covering entire screen
- **Navigation**: Previous/Next buttons (◀ ▶) and keyboard arrows
- **Export Options**: PNG download, copy to clipboard, JSON data export
- **Image Display**: Centered image with info and controls
- **Close Options**: Close button, Escape key, or click outside

### Vision Analysis Integration
- **Select & Analyze**: Choose one or multiple snapshots from gallery
- **Evolutionary Analysis**: Multiple snapshots analyzed as temporal sequence
- **Single Snapshot Analysis**: Individual snapshot detailed analysis
- **Results in Chat**: Analysis appears in CRA chat with images displayed

---

## 🎨 Recent Enhancements (2025-01-XX)

### Robust JSON Parsing
- **Comment Stripping**: Automatically removes `//` and `/* */` comments from CRA JSON responses
- **Property Name Normalization**: Fixes common formatting mistakes (e.g., `componentColorrealitysim` → `componentColor_reality_sim`)
- **Brace-Counting Extraction**: Handles deeply nested JSON objects correctly
- **Enhanced Error Logging**: Full JSON context in error messages for debugging

### Visual Feedback System
- **Control Highlighting**: Color pickers, sliders, and checkboxes flash cyan when updated
- **Settings Panel Highlighting**: Entire panel highlights with border and background when settings change
- **Auto-Scroll**: Automatically scrolls to settings panel when updates occur
- **Update Notifications**: Shows count of updated settings in chat

### Snapshot Management
- **Automatic Cleanup**: Snapshots cleared when simulation stops or starts
- **Stale Detection**: Detects and clears old snapshots on page load
- **Fresh Data Guarantee**: Vision model receives every captured snapshot from the current run (no blank/duplicate filtering) plus the fresh live capture.

### Image Capture Improvements
- **Render Completion**: Double `requestAnimationFrame` + 50ms delay ensures current state
- **Layout Recalculation**: Forces browser to update layout before capturing
- **No Cached Images**: Vision model always receives up-to-date graph images

