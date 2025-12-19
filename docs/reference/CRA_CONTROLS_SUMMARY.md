# 🤖 CRA Controls Summary - What Can the CRA Control?

## 🎯 Quick Answer

**The CRA can control EVERYTHING you see in the settings panel, plus system configuration!**

---

## 📋 What's Exposed in the Settings Panel (All CRA-Controllable)

### 🎨 **Component Colors** (8 Color Pickers)
- ✅ Reality Simulator (default: #FF0000 - Red)
- ✅ Explorer (default: #0000FF - Blue)
- ✅ Djinn Kernel (default: #FF8800 - Orange)
- ✅ Breath Engine (default: #FF00FF - Magenta)
- ✅ **🧠 Neural System** (default: #00FFFF - Electric Cyan)
- ✅ **⚔️ Highlander** (default: #DC143C - Crimson) ⭐ **NEW**
- ✅ **🌌 Alliance Warfare** (default: #9400D3 - Dark Violet) ⭐ **NEW**
- ✅ System (default: #FFFF00 - Yellow)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_neural": "#BF00FF"}]]`
**Highlander Format:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_highlander": "#FF0000"}]]`
**Alliance Format:** `[[VIZ_SETTINGS_UPDATE: {"componentColor_alliance": "#8B00FF"}]]`

### 🔗 **Link Colors** (7 Color Pickers)
- ✅ Threshold (default: #FF00FF - Magenta)
- ✅ Correlation (default: #0000FF - Blue)
- ✅ Direct (default: #00FF00 - Green)
- ✅ Temporal (default: #FFFF00 - Yellow)
- ✅ **Battle** (default: #DC143C - Crimson) ⭐ **NEW** - Highlander battle causations
- ✅ **Alliance** (default: #9400D3 - Dark Violet) ⭐ **NEW** - Alliance warfare causations
- ✅ Unknown (default: #FF8800 - Orange)

**CRA Format:** `[[VIZ_SETTINGS_UPDATE: {"linkColor_threshold": "#FF0000"}]]`
**Battle Format:** `[[VIZ_SETTINGS_UPDATE: {"linkColor_battle": "#FF4500"}]]`
**Alliance Format:** `[[VIZ_SETTINGS_UPDATE: {"linkColor_alliance": "#9932CC"}]]`

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

### Component Filters (10 Checkboxes)
- ✅ Reality Simulator
- ✅ Explorer
- ✅ Djinn Kernel
- ✅ Breath
- ✅ 🧠 Neural System
- ✅ 🦋 Language System (vocabulary growth, organism communication, language teacher)
- ✅ 🦋 Butterfly Chat (user chat interactions)
- ✅ ⚔️ Highlander ⭐ NEW (tournament battles, eliminations, champion emergence)
- ✅ 🌌 Alliance Warfare ⭐ NEW (alliance formation, galactic wars, territory control)
- ✅ System

**CRA Format:** `[[GRAPH_FILTER_UPDATE: {"components": {"explorer": true, "djinn_kernel": false, "language": true}}]]`
**Highlander Format:** `[[GRAPH_FILTER_UPDATE: {"components": {"highlander": true, "alliance_warfare": true}}]]`

### Causation Type Filters (6 Checkboxes)
- ✅ Threshold
- ✅ Correlation
- ✅ Direct
- ✅ Temporal
- ✅ Battle ⭐ NEW (Highlander battle causations)
- ✅ Alliance ⭐ NEW (Alliance warfare causations)

**CRA Format:** `[[GRAPH_FILTER_UPDATE: {"causation_types": {"threshold": true, "direct": false}}]]`
**Battle Format:** `[[GRAPH_FILTER_UPDATE: {"causation_types": {"battle": true, "alliance": true}}]]`

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

#### Language Model Configuration ⭐ NEW
- `neural.language_model.enabled` (true/false, default: false) - Master toggle for language model
- `neural.language_model.attention.enabled` (true/false) - Enable multi-head attention
- `neural.language_model.attention.num_heads` (1-8, default: 4) - Number of attention heads
- `neural.language_model.attention.attention_dim` (16-128, default: 32) - Attention dimension
- `neural.language_model.vocabulary.max_size` (256-4096, default: 1024) - Maximum vocabulary size
- `neural.language_model.sequence.max_length` (32-256, default: 128) - Maximum sequence length
- `neural.language_model.sequence.context_window` (8-64, default: 32) - Context window size
- `neural.language_model.training.alpha` (0.5-1.0, default: 0.9) - DQN loss weight
- `neural.language_model.training.beta` (0.0-0.5, default: 0.1) - Language loss weight
- `neural.language_model.training.vp_temperature_scale` (true/false) - VP-based temperature scaling
- `neural.language_model.curriculum.enabled` (true/false) - Enable curriculum learning
- `neural.language_model.curriculum.vp_thresholds.stage_*` (0.0-1.0) - VP thresholds for stages
- `neural.language_model.generation.max_length` (8-64, default: 32) - Max generation length
- `neural.language_model.generation.temperature` (0.1-2.0, default: 1.0) - Sampling temperature
- `neural.language_model.generation.vp_gate_threshold` (0.0-1.0, default: 0.5) - VP threshold for generation

**Examples:**
- `[[CONFIG_UPDATE: {"reason": "Enable language model", "patch": [{"op": "replace", "path": "/neural/language_model/enabled", "value": true}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Increase language loss weight", "patch": [{"op": "replace", "path": "/neural/language_model/training/beta", "value": 0.2}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Lower curriculum threshold", "patch": [{"op": "replace", "path": "/neural/language_model/curriculum/vp_thresholds/stage_1", "value": 0.4}]}]]`

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

#### Meta-Cognitive Self-Tuning
- `meta_cognitive.self_tuning.enabled` (true/false, default: true) - Enable/disable autonomous config tuning
- `meta_cognitive.self_tuning.mode` ("off"/"observing"/"learning"/"autonomous", default: "autonomous")
- `meta_cognitive.self_tuning.tuning_interval_frames` (10-200 frames, default: 50) - How often tuner analyzes system
- `meta_cognitive.self_tuning.min_confidence_threshold` (0.3-0.95, default: 0.6) - Minimum confidence to apply changes

**Examples:**
- `[[CONFIG_UPDATE: {"reason": "Speed up tuning for rapid adaptation", "patch": [{"op": "replace", "path": "/meta_cognitive/self_tuning/tuning_interval_frames", "value": 25}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Make tuner more conservative", "patch": [{"op": "replace", "path": "/meta_cognitive/self_tuning/min_confidence_threshold", "value": 0.8}]}]]`

#### Causation Detection ⭐ NEW
- `causation_detection.direct_causation_time_window` (0.1-10.0 seconds, default: 1.0)
- `causation_detection.phase_transition_time_window` (0.5-10.0 seconds, default: 2.0)
- `causation_detection.recent_events_window` (10-1000 events, default: 100)
- `causation_detection.correlation_threshold` (0.0-1.0, default: 0.7)
- `causation_detection.enable_neural_causations` (true/false, default: true) - Master toggle for all neural causations
- `causation_detection.enable_neural_decision_causations` (true/false, default: true) ⭐ NEW - Neural decision event links
- `causation_detection.enable_neural_training_causations` (true/false, default: true) ⭐ NEW - Neural training event links
- `causation_detection.enable_phase_transition_causations` (true/false, default: true)
- `causation_detection.enable_bidirectional_causations` (true/false, default: true)
- `causation_detection.thresholds.*` (all threshold values and directions)

**Examples:** 
- `[[CONFIG_UPDATE: {"reason": "Increase neural causation sensitivity", "patch": [{"op": "replace", "path": "/causation_detection/direct_causation_time_window", "value": 2.0}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Show only decision links", "patch": [{"op": "replace", "path": "/causation_detection/enable_neural_training_causations", "value": false}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Show only training links", "patch": [{"op": "replace", "path": "/causation_detection/enable_neural_decision_causations", "value": false}]}]]`

**Rollback:** `[[CONFIG_ROLLBACK: {"steps": 1, "reason": "Undo last change"}]]`

#### Highlander Protocol ⭐ NEW
The Highlander Protocol is a survival tournament system where organisms compete for dominance. "There can be only one" - the ultimate survivor becomes the immortal template.

- `highlander.enabled` (true/false, default: true) - Master toggle for Highlander mode
- `highlander.survival_threshold` (0.0-1.0, default: 0.5) - Minimum fitness to survive elimination
- `highlander.competition_intensity` (0.0-1.0, default: 0.8) - Frequency and intensity of battles
- `highlander.chaos_factor` (0.0-1.0, default: 0.15) - Random event probability
- `highlander.mutation_rate` (0.0-1.0, default: 0.05) - Mutation rate for offspring
- `highlander.population_size` (1-100, default: 10) - Initial population size
- `highlander.max_population` (10-500, default: 50) - Maximum population cap
- `highlander.min_population` (1-20, default: 5) - Minimum before germination triggers
- `highlander.germination_rate` (0.0-1.0, default: 0.1) - Rate of new organism spawning
- `highlander.predation_enabled` (true/false, default: true) - Enable predator-prey dynamics
- `highlander.rounds_per_cycle` (1-10, default: 1) - Battle rounds per simulation cycle
- `highlander.max_battle_rounds` (1-20, default: 10) - Maximum rounds per battle
- `highlander.max_capsules` (1-20, default: 5) - Maximum checkpoint capsules for champions
- `highlander.max_genetic_samples` (10-500, default: 100) - Maximum genetic samples for germination

**Examples:**
- `[[CONFIG_UPDATE: {"reason": "Enable Highlander mode", "patch": [{"op": "replace", "path": "/highlander/enabled", "value": true}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Increase survival pressure", "patch": [{"op": "replace", "path": "/highlander/survival_threshold", "value": 0.7}]}]]`
- `[[CONFIG_UPDATE: {"reason": "More intense battles", "patch": [{"op": "replace", "path": "/highlander/competition_intensity", "value": 0.95}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Enable extreme mode", "patch": [{"op": "replace", "path": "/highlander/chaos_factor", "value": 0.4}, {"op": "replace", "path": "/highlander/survival_threshold", "value": 0.8}]}]]`

#### Alliance Warfare System ⭐ NEW
Galactic-scale alliance warfare for collective existential dominance. Organisms form planetary alliances and wage wars across territorial domains.

- `highlander.alliance_warfare.enabled` (true/false, default: true) - Enable alliance warfare
- `highlander.alliance_warfare.min_alliance_size` (2-10, default: 3) - Minimum organisms for alliance formation
- `highlander.alliance_warfare.max_alliances` (2-20, default: 10) - Maximum concurrent alliances
- `highlander.alliance_warfare.war_frequency` (0.0-1.0, default: 0.3) - Probability of war each cycle
- `highlander.alliance_warfare.existential_war_threshold` (0.0-1.0, default: 0.8) - Threshold for total annihilation wars

**Territorial Domains (War Objectives):**
- `FITNESS_LANDSCAPE` - Control over organism fitness scoring
- `KNOWLEDGE_DOMAIN` - Control over language/knowledge systems  
- `GERMINATION_TERRITORY` - Control over offspring spawning
- `ORBITAL_ZONE` - Control over network positioning
- `EMERGENCE_MOMENTUM` - Control over evolution pressure
- `EXISTENTIAL_OWNERSHIP` - Ultimate galactic dominance

**Examples:**
- `[[CONFIG_UPDATE: {"reason": "Enable alliance warfare", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/enabled", "value": true}]}]]`
- `[[CONFIG_UPDATE: {"reason": "More frequent wars", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/war_frequency", "value": 0.5}]}]]`
- `[[CONFIG_UPDATE: {"reason": "Larger alliances required", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/min_alliance_size", "value": 5}]}]]`

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

### ✅ **FULLY CONTROLLABLE** (175+ Settings)

1. **All Visualization Settings** (45+ settings)
   - Link appearance (7 settings)
   - Node appearance (6 settings)
   - Depth effects (4 settings)
   - Visual effects (5 settings)
   - Color settings (3 settings)
   - Performance (4 settings)
   - Animation (3 settings)
   - Component colors (8 colors - including Highlander & Alliance)
   - Link colors (7 colors - including Battle & Alliance causations)

2. **Graph Filters** (19 settings)
   - Component visibility (10) - includes Highlander & Alliance Warfare
   - Causation type filters (6) - includes Battle & Alliance
   - Display toggles (3)

3. **System Configuration** (100+ settings)
   - Neural system parameters
   - Feedback controller knobs
   - Network settings
   - Evolution parameters
   - **🧬 Diversity Guard Settings**
     - `evolution.diversity_guard.enabled` (bool) - Enable/disable diversity guard
     - `evolution.diversity_guard.hash_similarity_threshold` (0.5-1.0) - Genotype similarity threshold
     - `evolution.diversity_guard.penalty` (0.0-0.2) - Fitness penalty for over-represented genotypes
     - `evolution.diversity_guard.frequency_threshold` (0.05-0.5) - Frequency above which penalty applies
   - Quantum settings
   - VP monitoring options

4. **⚔️ Highlander Protocol** (15+ settings) ⭐ NEW
   - `highlander.enabled` - Master toggle
   - `highlander.survival_threshold` - Minimum fitness to survive
   - `highlander.competition_intensity` - Battle intensity
   - `highlander.chaos_factor` - Random event probability
   - `highlander.mutation_rate` - Offspring mutation rate
   - `highlander.population_size` - Initial population
   - `highlander.max_population` / `min_population` - Population bounds
   - `highlander.germination_rate` - New organism spawn rate
   - `highlander.predation_enabled` - Predator-prey dynamics
   - `highlander.rounds_per_cycle` / `max_battle_rounds` - Battle configuration
   - `highlander.max_capsules` - Champion checkpoint limit
   - `highlander.max_genetic_samples` - Germination pool size

5. **🌌 Alliance Warfare** (5 settings) ⭐ NEW
   - `highlander.alliance_warfare.enabled` - Enable galactic warfare
   - `highlander.alliance_warfare.min_alliance_size` - Minimum alliance members
   - `highlander.alliance_warfare.max_alliances` - Maximum concurrent alliances
   - `highlander.alliance_warfare.war_frequency` - War probability per cycle
   - `highlander.alliance_warfare.existential_war_threshold` - Total annihilation threshold

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

### Example 5: Enable Diversity Guard ⭐ NEW
**You:** "Enable diversity guard to prevent premature convergence"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Enable diversity guard to maintain genetic diversity", "correlation_id": "diversity-enable", "patch": [{"op": "replace", "path": "/evolution/diversity_guard/enabled", "value": true}]}]]`

### Example 6: Adjust Diversity Penalty ⭐ NEW
**You:** "Increase diversity penalty to 0.08"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Increase diversity penalty to prevent genotype clustering", "correlation_id": "diversity-penalty", "patch": [{"op": "replace", "path": "/evolution/diversity_guard/penalty", "value": 0.08}]}]]`

### Example 7: Enable Highlander Mode ⭐ NEW
**You:** "Enable Highlander survival tournament"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Enable Highlander survival tournament mode", "correlation_id": "highlander-enable", "patch": [{"op": "replace", "path": "/highlander/enabled", "value": true}]}]]`

### Example 8: Increase Battle Intensity ⭐ NEW
**You:** "Make battles more intense"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Increase competition intensity for harder battles", "correlation_id": "battle-intensity", "patch": [{"op": "replace", "path": "/highlander/competition_intensity", "value": 0.95}]}]]`

### Example 9: Enable Alliance Warfare ⭐ NEW
**You:** "Enable galactic alliance wars"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Enable alliance warfare for collective battles", "correlation_id": "alliance-enable", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/enabled", "value": true}]}]]`

### Example 10: More Frequent Wars ⭐ NEW
**You:** "Trigger wars more often"
**CRA Response:** `[[CONFIG_UPDATE: {"reason": "Increase war frequency for more galactic conflict", "correlation_id": "war-freq", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/war_frequency", "value": 0.5}]}]]`

---

## 📝 **Notes**

- **All settings update in real-time** - no simulation interruption
- **Batch updates supported** - CRA can change multiple settings at once
- **Settings validation** - Invalid values are rejected gracefully
- **Visual feedback** - Controls flash cyan when updated by CRA
- **Settings panel highlighting** - Panel highlights when CRA makes changes

---

**Total CRA-Controllable Settings: 175+ settings** across visualization, filters, Highlander Protocol, Alliance Warfare, and system configuration!


**Last Updated:** 2025-12-01

