# 🤖 CRA Controls Summary - What Can the CRA Control?

## 🎯 Quick Answer

**The CRA can control EVERYTHING you see in the settings panel, plus system configuration!**

---

## 📋 What's Exposed in the Settings Panel (All CRA-Controllable)

### 🎨 **Component Colors** (6 Color Pickers)
- ✅ Reality Simulator (default: #FF0000 - Red)
- ✅ Explorer (default: #0000FF - Blue)
- ✅ Djinn Kernel (default: #FF8800 - Orange)
- ✅ Breath Engine (default: #FF00FF - Magenta)
- ✅ **🧠 Neural System** (default: #00FFFF - Electric Cyan) ⭐ **NEWLY ADDED**
- ✅ System (default: #FFFF00 - Yellow)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_neural": "#BF00FF"}]]`

### 🔗 **Link Colors** (5 Color Pickers)
- ✅ Threshold (default: #FF00FF - Magenta)
- ✅ Correlation (default: #0000FF - Blue)
- ✅ Direct (default: #00FF00 - Green)
- ✅ Temporal (default: #FFFF00 - Yellow)
- ✅ Unknown (default: #FF8800 - Orange)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"linkColor_threshold": "#FF0000"}]]`

### 🔗 **Link Appearance** (6 Sliders)
1. **Base Width** (1-5px, default: 2.5px)
2. **Max Width** (8-30px, default: 16px)
3. **Min Opacity** (0.1-0.8, default: 0.35)
4. **Max Opacity** (0.5-1.0, default: 1.0)
5. **Density Multiplier** (0-10, default: 6.0)
6. **Depth Multiplier** (0-5, default: 3.0)
7. **Node Conn Multiplier** (0-3, default: 2.0)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"linkBaseWidth": 4.0, "linkMaxWidth": 20}]]`

### ⚫ **Node Appearance** (6 Sliders)
1. **Base Size** (5-15px, default: 8px)
2. **Max Size** (10-20px, default: 12px)
3. **Min Opacity** (0.3-0.9, default: 0.6)
4. **Max Opacity** (0.7-1.0, default: 1.0)
5. **Depth Size Multiplier** (0-6, default: 4.0)
6. **Stroke Width** (1-6px, default: 3px)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"nodeBaseSize": 10, "nodeMaxSize": 15}]]`

### 🌊 **Depth Effects** (4 Sliders)
1. **Depth Strength** (0-2, default: 1.0)
2. **Opacity Range** (0-1, default: 0.5)
3. **Size Range** (0-1, default: 0.4)
4. **Parallax Amount** (0-2, default: 0.5)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"depthStrength": 1.5, "depthParallaxAmount": 1.0}]]`

### ✨ **Visual Effects** (2 Checkboxes + 3 Sliders)
1. **Enable Shadows** (checkbox, default: ON)
2. **Shadow Offset** (0-5px, default: 2px)
3. **Shadow Blur** (0-10, default: 3)
4. **Enable Glow** (checkbox, default: ON)
5. **Glow Intensity** (0-5, default: 2)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"enableShadows": false, "glowIntensity": 3}]]`

### 🎨 **Color Settings** (3 Sliders)
1. **Front Brightness** (0.5-1.5, default: 1.0)
2. **Back Brightness** (0.3-1.0, default: 0.7)
3. **Color Saturation** (0-2, default: 1.0)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"frontColorBrightness": 1.2, "colorSaturation": 1.5}]]`

### ⚡ **Performance** (1 Checkbox + 2 Sliders + 1 Dropdown)
1. **Viewport Culling** (checkbox, default: OFF)
2. **Max Visible Links** (1000-50000, default: 10000)
3. **Max Visible Nodes** (500-20000, default: 5000)
4. **Render Quality** (dropdown: "low"/"medium"/"high", default: "high")

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"renderQuality": "low", "maxVisibleLinks": 5000}]]`

### 🎬 **Animation/Transitions** (1 Checkbox + 2 Sliders)
1. **Enable Transitions** (checkbox, default: ON)
2. **Transition Duration** (100-1000ms, default: 300ms)
3. **Animation Speed** (0.1-3.0, default: 1.0)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"enableTransitions": true, "animationSpeed": 1.5}]]`

---

## 🎛️ **Graph Filters** (CRA Can Control)

### Component Filters (5 Checkboxes)
- ✅ Reality Simulator
- ✅ Explorer
- ✅ Djinn Kernel
- ✅ Breath
- ✅ System

**CRA Format:** `[[GRAPH_FILTER_UPDATE: {"components": {"explorer": true, "djinn_kernel": false}}]]`

### Causation Type Filters (4 Checkboxes)
- ✅ Threshold
- ✅ Correlation
- ✅ Direct
- ✅ Temporal

**CRA Format:** `[[GRAPH_FILTER_UPDATE: {"causation_types": {"threshold": true, "direct": false}}]]`

### Display Toggles (3 Checkboxes)
- ✅ Node Labels
- ✅ Causation Links
- ✅ Temporal Paths

**CRA Format:** `[[GRAPH_FILTER_UPDATE: {"display": {"show_labels": false, "show_temporal_paths": true}}]]`

---

## ⚙️ **System Configuration** (CRA Can Control via Hot Reload)

The CRA can modify `config.json` while the system is running using:

**Format:** `[[CONFIG_UPDATE: {"reason": "description", "correlation_id": "plan-name", "patch": [{"op": "replace", "path": "/path/to/setting", "value": newValue}]}]]`

### Controllable Config Sections:

#### Neural System Configuration
- `neural.enabled` (true/false)
- `neural.device` ("cpu"/"cuda")
- `neural.brain.input_dim`, `hidden_dim`, `output_dim`
- `neural.training.batch_size`, `learning_rate`, `epsilon_*`
- `neural.rewards.*` (all reward weights)
- `neural.inheritance.*` (mutation_rate, crossover_rate)

**Example:** `[[CONFIG_UPDATE: {"reason": "Increase neural learning rate", "patch": [{"op": "replace", "path": "/neural/training/learning_rate", "value": 0.002}]}]]`

#### Feedback Controller
- `feedback.knobs.mutation_rate.initial`
- `feedback.knobs.new_edge_rate.initial`
- `feedback.knobs.clustering_bias.initial`
- `feedback.knobs.quantum_pruning.initial`

#### Network Settings
- `network.max_connections` (1000-20000)
- `network.max_organisms` (500-5000)
- `network.resource_pool`

#### Evolution Settings
- `evolution.population_size`
- `evolution.mutation_rate.initial`
- `evolution.adaptation_sensitivity`

#### Quantum Settings
- `quantum.initial_states`
- `quantum.superposition_tolerance`
- `quantum.prune_check_interval`

#### VP Monitoring
- `vp_monitoring.diagnostics_enabled`
- `vp_monitoring.stabilization_enabled`
- `vp_monitoring.component_decomposition_enabled`
- `vp_monitoring.adaptive_thresholds_enabled`

**Rollback:** `[[CONFIG_ROLLBACK: {"steps": 1, "reason": "Undo last change"}]]`

---

## 📊 **What CRA CANNOT Control** (User-Only)

### Graph Navigation (Manual Only)
- ❌ Zoom (use zoom box or mouse wheel)
- ❌ Pan (drag the graph)
- ❌ Rotation (use rotation buttons)
- ❌ Viewport position

**Why:** CRA provides guidance like "zoom to 150% and center on node X" but doesn't move the camera automatically (prevents unexpected jumps).

---

## 🎯 **Complete CRA Control Summary**

### ✅ **FULLY CONTROLLABLE** (40+ Settings)

1. **All Visualization Settings** (40+ settings)
   - Link appearance (7 settings)
   - Node appearance (6 settings)
   - Depth effects (4 settings)
   - Visual effects (5 settings)
   - Color settings (3 settings)
   - Performance (4 settings)
   - Animation (3 settings)
   - Component colors (6 colors)
   - Link colors (5 colors)

2. **Graph Filters** (12 settings)
   - Component visibility (5)
   - Causation type filters (4)
   - Display toggles (3)

3. **System Configuration** (100+ settings)
   - Neural system parameters
   - Feedback controller knobs
   - Network settings
   - Evolution parameters
   - Quantum settings
   - VP monitoring options

### ❌ **NOT CONTROLLABLE** (User Manual Only)

1. **Graph Navigation**
   - Zoom level
   - Pan position
   - Rotation angle
   - Viewport position

---

## 💡 **How to Use CRA Controls**

### Example 1: Change Neural Color
**You:** "Make neural nodes purple"
**CRA Response:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_neural": "#BF00FF"}]]`

### Example 2: Improve Performance
**You:** "The graph is laggy"
**CRA Response:** `[[VIZ_SETTINGS_UPDATE: {"renderQuality": "low", "maxVisibleLinks": 5000, "enableShadows": false}]]`

### Example 3: Highlight Explorer Events
**You:** "Make Explorer nodes stand out"
**CRA Response:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_explorer": "#00FF00", "nodeBaseSize": 12, "enableGlow": true}]]`

### Example 4: Adjust Neural Learning
**You:** "Increase neural learning rate"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Increase neural learning rate for faster adaptation", "correlation_id": "neural-lr-increase", "patch": [{"op": "replace", "path": "/neural/training/learning_rate", "value": 0.002}]}]]`

---

## 📝 **Notes**

- **All settings update in real-time** - no simulation interruption
- **Batch updates supported** - CRA can change multiple settings at once
- **Settings validation** - Invalid values are rejected gracefully
- **Visual feedback** - Controls flash cyan when updated by CRA
- **Settings panel highlighting** - Panel highlights when CRA makes changes

---

**Total CRA-Controllable Settings: 150+ settings** across visualization, filters, and system configuration!

