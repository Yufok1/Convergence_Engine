# 🤖 Convergence Research Assistant (CRA) - Complete Capabilities Guide

**Autonomous AI Research Assistant for the Butterfly System**

---

## ⚡ Quick Reference - Common Commands

### Graph Filter Control
```json
[[GRAPH_FILTER_UPDATE: {"components": {"neural": true, "ml_analysis": false}}]]
```

### Visualization Settings
```json
[[VIZ_SETTINGS_UPDATE: {"linkBaseWidth": 4.0, "enableGlow": true}]]
```

### Config Updates (Hot Reload)
```json
[[CONFIG_UPDATE: {"reason": "Increase learning rate", "correlation_id": "lr-boost", "patch": [{"op": "replace", "path": "/neural/training/learning_rate", "value": 0.01}]}]]
```

### Illumination Engine
```json
[[ILLUMINATE: {"action": "root_causes", "event_id": "evt_123"}]]
[[ILLUMINATE: {"action": "most_consequential", "limit": 10}]]
```

### Research Notepad
```json
[[NOTEPAD: {"action": "observe", "content": "VP spiked to 0.85 #vp_spike"}]]
[[NOTEPAD: {"action": "hypothesize", "content": "High VP triggers collapse", "confidence": "high"}]]
```

---

## 🎯 Core Role

The Convergence Research Assistant (CRA) is an AI-powered research assistant that runs in the **Causation Explorer Web UI** (`causation_web_ui.py`). It monitors and analyzes the **Butterfly System** (`unified_entry.py`) through the web interface.

**Key Distinction:**
- **Butterfly System** (`unified_entry.py`) = The simulation being monitored (can run or be stopped)
- **Causation Explorer Web UI** (`causation_web_ui.py`) = The monitoring interface where CRA lives (runs independently)

---

## 📊 CRITICAL: Metric Definitions & Interpretation

### Fitness Metric Architecture

**⚠️ IMPORTANT**: The Butterfly System uses MULTIPLE fitness concepts that are NOT interchangeable:

| Metric | Range | Context | What It Measures |
|--------|-------|---------|------------------|
| **Organism Fitness** | 0.0 – 1.0+ | Individual organism | Evolutionary adaptation score (can exceed 1.0 for exceptional individuals) |
| **Neural Training Loss** | 0.0 – ∞ | DQN training | Loss decreasing = learning (lower = better) |
| **Response Weight** | 0.0 – 3.0+ | Chat aggregation | `fitness × confidence × genetic_modifier` (composite score) |
| **Aggregated Fitness** | 0.0 – 5.0+ | Elite population | Sum of elite weights (NOT normalized) |

### Response Weight Calculation (Chat System)

When organisms respond to chat messages, their contributions are weighted:

```
weight = organism_fitness × confidence × genetic_weight_modifier

Where:
- organism_fitness: 0.0-1.0+ (evolutionary fitness)
- confidence: 0.0-1.0 (response quality + neural capability)
- genetic_weight_modifier: 1.0-1.2 (genetic diversity bonus)

Result: Weight can exceed 1.0 (e.g., 0.85 × 0.95 × 1.15 = 0.93)
        Sum of weights across elite can exceed 2.0+
```

### Population Context

| Term | Definition |
|------|------------|
| **Active Organisms** | Currently alive in simulation (can change each generation) |
| **Elite Organisms** | Top N by fitness used for chat responses (default: top 10) |
| **Historical Total** | All organisms ever created (informational only) |
| **Responding Organisms** | Subset with sufficient vocabulary to generate output |

**Key Insight**: Seeing "36 active, 10 elite" does NOT mean collapse. Elite selection is intentional quality filtering.

### Illumination Readiness Assessment

DO NOT use fitness alone for readiness. Use composite criteria:

| Criterion | Threshold | Why |
|-----------|-----------|-----|
| Elite Fitness Sum | > 2.0 | Shows quality aggregation capability |
| Vocabulary Size | > 50 words | Sufficient expression capacity |
| VP Stability | < 0.3 variance | System equilibrium |
| Semantic Coherence | > 0.5 | Response quality |

---

## 🎯 System Maturity Awareness (Context-Sensitive Diagnostics)

**NEW**: The CRA now recognizes system maturity states and adjusts diagnostic severity accordingly. This prevents false alarms during early startup.

### Maturity Thresholds

| Metric | Early Startup | Warming Up | Mature | Notes |
|--------|---------------|------------|--------|-------|
| Frame Count | < 10 | 10-100 | > 100 | First 10 frames = initialization |
| Organism Count | < 50 | 50-200 | > 200 | Population needs time to grow |
| Neural Training Steps | < 10 | 10-100 | > 100 | DQN needs warm-up |
| Causation Links | 0 | 1-10 | > 10 | Links form over time |
| ML Clusters | 0 | 1-3 | > 3 | Need population for clustering |
| Breath Cycles | < 5 | 5-20 | > 20 | System rhythm stabilizes |

### Severity Levels by Maturity

**🟢 EARLY STARTUP (Frame < 10, Organisms < 50)**
- All zeros and missing data = NORMAL, not failures
- Neural loss = None is EXPECTED (no training yet)
- Causation links = 0 is EXPECTED (no events yet)
- ML clusters = 0 is EXPECTED (population too small)
- **Severity**: INFO only, never CRITICAL

**🟡 WARMING UP (Frame 10-100, Organisms 50-200)**
- Some metrics may still be zero or low
- Neural training should show first losses
- Causation links should start appearing
- **Severity**: WARNING only for metrics that should be non-zero

**🔴 MATURE (Frame > 100, Organisms > 200)**
- All systems should be producing data
- Zero values now indicate actual problems
- **Severity**: CRITICAL is appropriate for missing expected data

### Critical Rule

> **Never flag CRITICAL on a system with Frame < 10 or Organisms < 50.**
> Early startup metrics are NOT failures - they're expected initialization states.

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
- **Component Visibility:** Reality Simulator, Explorer, Djinn Kernel, Breath, 🧠 Neural, 🔬 ML Analysis, ⚔️ Highlander, 🌌 Alliance Warfare, System
- **Causation Type Filters:** Threshold, Correlation, Direct, Temporal, Battle, Alliance
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

#### Component Colors (Hex Colors - Dynamic)
**IMPORTANT**: All colors are dynamic and can change. The CRA receives current color values in the graph context. Reference settings instead of hardcoded values.
- `componentColor_reality_sim` (e.g., "#FF0000")
- `componentColor_explorer` (e.g., "#0000FF")
- `componentColor_djinn_kernel` (e.g., "#FF8800")
- `componentColor_breath` (e.g., "#FF00FF")
- `componentColor_neural` - 🧠 Neural System nodes (check current value in graph context)
- `componentColor_ml_analysis` - 🔬 ML Analysis nodes (check current value in graph context)
- `componentColor_system` (e.g., "#FFFF00")

#### Link Colors (Hex Colors - Dynamic)
**IMPORTANT**: All colors are dynamic and can change. The CRA receives current color values in the graph context. Reference settings instead of hardcoded values.
- `linkColor_threshold` (e.g., "#FF00FF")
- `linkColor_correlation` (e.g., "#0000FF")
- `linkColor_direct` (e.g., "#00FF00")
- `linkColor_temporal` (e.g., "#FFFF00")
- `linkColor_neural` - 🧠 Neural system links (check current value in graph context)
- `linkColor_ml` - 🔬 ML analysis links (check current value in graph context)
- `linkColor_unknown` (e.g., "#FF8800")

#### ML Event Types (Visual Differentiation)
The ML Analysis component emits specialized events with distinct visual shapes:
- **phenotype_emergence** → Hexagon shape (cyan/magenta pulse)
- **cluster_collapse** → Pentagon shape (scale-down animation)
- **anomaly_spike** → Triangle shape (orange flash animation)

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
| `/neural/training/lr_scheduler/enabled` | true/false | ⭐ NEW: LR scheduler toggle |
| `/neural/training/lr_scheduler/gamma` | 0.9 – 0.99 | ⭐ NEW: LR decay factor |
| `/neural/training/early_stopping/enabled` | true/false | ⭐ NEW: Early stopping toggle |
| `/neural/training/early_stopping/patience` | 10 – 100 | ⭐ NEW: Steps before early stop |
| `/scikit/enabled` | true/false | Scikit-learn ML system toggle |
| `/scikit/clustering/enabled` | true/false | HDBSCAN clustering toggle |
| `/scikit/anomaly_detection/enabled` | true/false | Isolation Forest toggle |
| `/scikit/dimensionality_reduction/enabled` | true/false | PCA/t-SNE toggle |
| `/ray/enabled` | true/false | Ray parallel processing toggle |
| `/ray/parallelization_threshold` | 10 – 200 | Min organisms for parallelism |
| `/ray/training_threshold` | 4 – 50 | Min trainable organisms for parallel training |
| `/ray/actor_pool_size` | 1 – 16 | Max concurrent Ray actors |
| `/ray/fallback_on_error` | true/false | Fall back to sequential on errors |
| `/ray/logging_level` | debug/info/warning/error | Ray logging verbosity |
| `/neural/checkpointing/enabled` | true/false | ⭐ NEW: Auto-save training state |
| `/neural/checkpointing/auto_save_interval_generations` | 50 – 500 | ⭐ NEW: Save every N generations |
| `/neural/checkpointing/auto_save_interval_minutes` | 5 – 60 | ⭐ NEW: Save every N minutes |
| `/neural/checkpointing/max_checkpoints` | 3 – 20 | ⭐ NEW: Rotate old checkpoints |
| `/neural/checkpointing/auto_resume` | true/false | ⭐ NEW: Load checkpoint on startup |

**Path Notes:** Dashes and camelCase are normalized (`/feedback/knobs/mutationrate/initial` → `/feedback/knobs/mutation_rate/initial`), but prefer underscore names.

### Expected Telemetry
- After an update, monitor `/api/cra/diagnostics/vp_history`, `/api/cra/diagnostics/network_trends`, and `/api/diagnostic/phase_sync` to confirm the change had the intended effect.
- Summaries should state: parameter, old value → new value, and the behavioral shift (e.g., “mutation rate up to 0.024 to break VP stagnation”).

### API Endpoints
- `POST /api/config/update` – guarded JSON Patch apply (supports `correlation_id`)
- `POST /api/config/rollback` – revert last N snapshots (history depth: 10)
- `GET /api/config/current` – active config + version
- `GET /api/config/history` – recent snapshots (optionally include full config payloads)
- `GET /api/cra/diagnostics/checkpoint_status` – ⭐ NEW: Checkpoint health & stats
- `POST /api/checkpoint/save` – ⭐ NEW: Force immediate checkpoint save
- `POST /api/checkpoint/restore` – ⭐ NEW: Restore from checkpoint
- `GET /api/checkpoint/list` – ⭐ NEW: List all checkpoints with metadata

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

### NeuralTrainer Deep Dive ⭐ NEW

The `NeuralTrainer` class (`trainer.py`) manages DQN training for all organisms:

**Core Components:**
| Component | Purpose |
|-----------|---------|
| `optimizers` | Dict of Adam optimizers per organism (reused for efficiency) |
| `schedulers` | Dict of LR schedulers per organism |
| `training_step_count` | Global training step counter |
| `best_loss` | Best observed loss for early stopping |
| `early_stopping_counter` | Steps without improvement |

**Training Flow:**
```
train_step(organisms, network_state, breath_state)
    ├── 1. Filter trainable organisms (has experiences)
    ├── 2. Sample from experience buffers
    ├── 3. Compute DQN loss (Q-learning)
    ├── 4. Get/create optimizer and scheduler
    ├── 5. optimizer.step()
    ├── 6. scheduler.step()
    ├── 7. Enforce min learning rate
    ├── 8. Check early stopping
    └── 9. Emit training event
```

**LR Scheduler Details:**
| Type | Class | Parameters |
|------|-------|------------|
| `step` | `StepLR` | `step_size`, `gamma` |
| `exponential` | `ExponentialLR` | `gamma` |
| `plateau` | `ReduceLROnPlateau` | `factor`, `patience`, `min_lr` |

**Early Stopping Logic:**
```python
if avg_loss < best_loss - min_delta:
    best_loss = avg_loss
    counter = 0
else:
    counter += 1
    if counter >= patience:
        early_stopped = True
```

**Safeguards Implemented:**
- Invalid scheduler type → StepLR fallback with warning
- NaN/inf loss → Skip early stopping check
- Negative min_delta → Reset to 1e-4
- Learning rate below min_lr → Clamp to min_lr

#### Neural Relationship Learning ⭐ NEW

The neural system now learns from language generation quality to strengthen/weaken semantic relationships.

**Key Config Paths:**
| Path | Safe Range | Description |
| --- | --- | --- |
| `/neural/language_model/relationship_learning/enabled` | true/false | Enable/disable relationship learning |
| `/neural/language_model/relationship_learning/quality_evaluation/coherent_threshold` | 0.0-1.0 | Minimum coherence score for success (default: 0.5) |
| `/neural/language_model/relationship_learning/quality_evaluation/garbled_threshold` | 0.0-1.0 | Maximum coherence score for failure (default: 0.2) |
| `/neural/language_model/relationship_learning/quality_evaluation/unk_ratio_threshold` | 0.0-1.0 | Maximum UNK token ratio (default: 0.3) |
| `/neural/language_model/relationship_learning/semantic_guidance/enabled` | true/false | Enable semantic word boosting |
| `/neural/language_model/relationship_learning/semantic_guidance/semantic_boost` | 0.0-1.0 | Logit boost for semantically related words (default: 0.2) |

**Example Commands:**
```
[[CONFIG_UPDATE: {"reason": "Stricter quality requirements", "correlation_id": "stricter-coherence", "patch": [{"op": "replace", "path": "/neural/language_model/relationship_learning/quality_evaluation/coherent_threshold", "value": 0.6}]}]]
[[CONFIG_UPDATE: {"reason": "Stronger semantic guidance", "correlation_id": "stronger-guidance", "patch": [{"op": "replace", "path": "/neural/language_model/relationship_learning/semantic_guidance/semantic_boost", "value": 0.3}]}]]
```

**What to Monitor:**
- Generation coherence scores (should improve over time)
- Relationship success/failure rates
- Semantic network evolution (relationships strengthening/weakening)
- Language generation quality (coherent vs garbled ratio)

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
- **Semantic Analysis** ⭐ NEW: Analyze word co-occurrence patterns and semantic relationships
  - Word co-occurrence analysis across organisms
  - Semantic cluster identification
  - Concept formation tracking
  - Relationship strength validation (ML teaches the system by strengthening strong co-occurrences)

---

## ⚔️ Highlander Protocol - Survival Tournament System ⭐ NEW

The Highlander Protocol is an evolutionary pressure system where organisms compete in survival battles. "There can be only one" - the ultimate survivor becomes the immortal template for future generations.

### Core Components

| Component | Purpose | Key Metrics |
|-----------|---------|-------------|
| **Tournament System** | Organizes survival battles | Rounds completed, eliminations |
| **Battle Arena** | Resolves combat between organisms | Winner ID, margin, battle duration |
| **Capsule Manager** | Checkpoints champion organisms | Capsule count, restoration events |
| **Germination Pool** | Spawns warriors from genetic material | Spawn rate, genetic diversity |
| **Champion Emergence** | Ultimate survivor selection | Champion ID, dominance score |

### Key Config Paths

| Path | Safe Range | Description |
|------|------------|-------------|
| `/highlander/enabled` | true/false | Master toggle for Highlander mode |
| `/highlander/survival_threshold` | 0.0-1.0 | Minimum fitness to survive elimination |
| `/highlander/competition_intensity` | 0.0-1.0 | Frequency and intensity of battles |
| `/highlander/chaos_factor` | 0.0-1.0 | Random event probability |
| `/highlander/mutation_rate` | 0.0-1.0 | Mutation rate for offspring |
| `/highlander/population_size` | 1-100 | Initial population size |
| `/highlander/max_population` | 10-500 | Maximum population cap |
| `/highlander/min_population` | 1-20 | Minimum before germination triggers |
| `/highlander/germination_rate` | 0.0-1.0 | Rate of new organism spawning |
| `/highlander/predation_enabled` | true/false | Enable predator-prey dynamics |
| `/highlander/rounds_per_cycle` | 1-10 | Battle rounds per simulation cycle |
| `/highlander/max_battle_rounds` | 1-20 | Maximum rounds per battle |
| `/highlander/max_capsules` | 1-20 | Maximum checkpoint capsules |
| `/highlander/max_genetic_samples` | 10-500 | Maximum genetic samples for germination |

### Example Commands
```
[[CONFIG_UPDATE: {"reason": "Enable Highlander mode", "correlation_id": "highlander-on", "patch": [{"op": "replace", "path": "/highlander/enabled", "value": true}]}]]
[[CONFIG_UPDATE: {"reason": "Increase survival pressure", "correlation_id": "harder-survival", "patch": [{"op": "replace", "path": "/highlander/survival_threshold", "value": 0.7}]}]]
[[CONFIG_UPDATE: {"reason": "Maximum evolutionary pressure", "correlation_id": "extreme-mode", "patch": [{"op": "replace", "path": "/highlander/survival_threshold", "value": 0.8}, {"op": "replace", "path": "/highlander/competition_intensity", "value": 0.95}, {"op": "replace", "path": "/highlander/chaos_factor", "value": 0.4}]}]]
```

### What to Monitor
- Battle outcomes and elimination patterns
- Champion emergence events
- Genetic pool diversity
- Germination rates vs extinction
- Capsule creation and restoration

---

## 🌌 Alliance Warfare System ⭐ NEW

Beyond individual battles - collective warfare for existential dominance. Organisms form planetary alliances and wage wars across territorial domains for galactic control.

### Core Architecture

| Component | Purpose | Description |
|-----------|---------|-------------|
| **PlanetaryAlliance** | Alliance dataclass | Tracks members, war power, territories, formation time |
| **AllianceWarfareSystem** | War orchestration | Detects formations, triggers clashes, determines outcomes |
| **TerritorialDomain** | War objectives | 6 domains organisms fight to control |
| **AllianceWarPhase** | War progression | FORMATION → TENSION → CLASH → AFTERMATH |

### Territorial Domains

| Domain | Control Grants | Strategic Value |
|--------|----------------|----------------|
| `FITNESS_LANDSCAPE` | Organism fitness scoring | High - affects survival |
| `KNOWLEDGE_DOMAIN` | Language/knowledge systems | Medium - affects learning |
| `GERMINATION_TERRITORY` | Offspring spawning | High - affects reproduction |
| `ORBITAL_ZONE` | Network positioning | Medium - affects connections |
| `EMERGENCE_MOMENTUM` | Evolution pressure | High - affects adaptation |
| `EXISTENTIAL_OWNERSHIP` | Ultimate galactic dominance | Critical - total control |

### Key Config Paths

| Path | Safe Range | Description |
|------|------------|-------------|
| `/highlander/alliance_warfare/enabled` | true/false | Enable alliance warfare |
| `/highlander/alliance_warfare/min_alliance_size` | 2-10 | Minimum organisms for alliance |
| `/highlander/alliance_warfare/max_alliances` | 2-20 | Maximum concurrent alliances |
| `/highlander/alliance_warfare/war_frequency` | 0.0-1.0 | War probability each cycle |
| `/highlander/alliance_warfare/existential_war_threshold` | 0.0-1.0 | Threshold for total annihilation |

### Example Commands
```
[[CONFIG_UPDATE: {"reason": "Enable alliance warfare", "correlation_id": "alliance-on", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/enabled", "value": true}]}]]
[[CONFIG_UPDATE: {"reason": "More frequent galactic wars", "correlation_id": "war-freq", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/war_frequency", "value": 0.5}]}]]
[[CONFIG_UPDATE: {"reason": "Require larger alliances", "correlation_id": "bigger-alliances", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/min_alliance_size", "value": 5}]}]]
[[CONFIG_UPDATE: {"reason": "Enable existential wars", "correlation_id": "existential-wars", "patch": [{"op": "replace", "path": "/highlander/alliance_warfare/existential_war_threshold", "value": 0.7}]}]]
```

### War Outcomes

| Outcome | Description | Effect |
|---------|-------------|--------|
| `DECISIVE_VICTORY` | One alliance dominates | Victor gains territory, loser loses members |
| `PYRRHIC_VICTORY` | Win with heavy losses | Victor gains territory but weakened |
| `STALEMATE` | No clear winner | Both alliances survive, no territory change |
| `MUTUAL_DESTRUCTION` | Both alliances collapse | All members released, territories contested |
| `EXISTENTIAL_ANNIHILATION` | Total defeat | Losing alliance completely eliminated |

### What to Monitor
- Alliance formation events (size, members, initial power)
- War declarations and outcomes
- Territory control changes
- Galactic dominance events (one alliance controls all domains)
- Existential war triggers and outcomes

### Integration with Highlander
- Alliance Warfare runs ON TOP of individual Highlander battles
- Champions from individual battles can form alliances
- Alliances compete for territorial domains
- Ultimate goal: one alliance achieves EXISTENTIAL_OWNERSHIP

### Alliance History & Wisdom System

Each alliance maintains a historical record that enables collective learning:

**AllianceHistory Components:**
| Component | Type | Description |
|-----------|------|-------------|
| `events` | `List[HistoricalEvent]` | Timestamped events (pruned to 500 max) |
| `causal_patterns` | `Dict[str, CausalPattern]` | Extracted cause-effect patterns |
| `wisdom_rules` | `List[str]` | Generalized wisdom from patterns |
| `legends` | `Dict[str, LegendaryOrganism]` | Legendary members (heroes, betrayers) |
| `events_by_type` | `Dict[str, List[str]]` | Event index by type |
| `events_by_organism` | `Dict[str, List[str]]` | Event index by organism |

**Wisdom Generation Flow:**
```
Events recorded → Patterns extracted → Wisdom rules generated
    │                    │                      │
    ▼                    ▼                      ▼
"War started"     "Low fitness →    "Avoid war when 
                   war declared"     members are weak"
```

**Wisdom Query Methods:**
- `get_wisdom_for_situation(situation)` → Returns `List[str]` of relevant wisdom text
- `get_alliance_wisdom(alliance_id, situation)` → Full wisdom package with patterns & legends
- `get_historical_summary()` → Alliance statistics (wars won/lost, betrayals, etc.)

**What Gets Recorded:**
- Alliance formations and dissolutions
- War declarations and outcomes
- Member joins and departures
- Betrayals and loyalty events
- Territory gains and losses
- Pattern discoveries

---

## 🏛️ Confederation (Super-Alliance) System ⭐ NEW

Alliances can ally with each other to form Confederations, which can merge into Empires, which can merge into Hegemonies. This is the ultimate expression of collective intelligence emergence.

### Hierarchy Tiers

| Tier | Name | What Determines Formation |
|------|------|--------------------------|
| 1 | **CONFEDERATION** | Alliances with: shared enemies, knowledge domain overlap, trustworthy track records, mutual power benefit |
| 2 | **EMPIRE** | Confederations with: territorial control together, war victories together, semantic alignment |
| 3 | **HEGEMONY** | Empires with: 2+ child confederations, 4+ controlled domains, 3+ war victories |

### Elevation Requirements

**CONFEDERATION → EMPIRE:**
- 3+ member alliances
- Control 2+ different territory types
- Won at least 1 confederation war

**EMPIRE → HEGEMONY:**
- 2+ child confederations
- Control 4+ different territories  
- Won 3+ confederation wars

### Key Events

| Event Type | Description |
|------------|-------------|
| `confederation_founded` | Alliance warchief creates new confederation |
| `alliance_joined_confederation` | Alliance accepts confederation invite |
| `confederation_war_proposed` | Mega-war proposal between confederations |
| `confederation_war_declared` | Confederation goes to war (majority vote passed) |
| `mega_confederation_formed` | Two confederations merge into EMPIRE/HEGEMONY |

### ML Feature Integration (Features 25-27)

| Feature | Index | Description |
|---------|-------|-------------|
| `confederation_level` | 25 | 0=none, 0.33=confederation, 0.66=empire, 1.0=hegemony |
| `confederation_wars` | 26 | Normalized count of mega-wars participated in |
| `cross_alliance_influence` | 27 | Connections to organisms in other alliances |

### Key Config Paths

| Path | Safe Range | Description |
|------|------------|-------------|
| `/highlander/alliance_warfare/max_confederations` | 1-5 | Maximum concurrent confederations |
| `/highlander/alliance_warfare/confederation_war_threshold` | 0.5-0.9 | Vote ratio needed to declare mega-war |

### What to Monitor
- Confederation tier progressions (CONFEDERATION → EMPIRE → HEGEMONY)
- Cross-alliance connection density (indicates emergence of super-structures)
- Confederation war outcomes and territory changes
- Organism confederation_tier distribution in ML clusters

---

## ⚡ Ray Distributed Computing System ⭐ NEW (Quick Win #13)

Ray provides parallel processing for computationally intensive operations. When populations exceed thresholds, workloads are automatically distributed across CPU cores for 2-5x speedups.

### Core Architecture

| Component | Purpose | Description |
|-----------|---------|-------------|
| **RayManager** | Lifecycle management | Init/shutdown, resource monitoring, map_parallel() |
| **SequentialFallback** | Graceful degradation | Drop-in replacement when Ray unavailable |
| **ray_tasks.py** | Parallel tasks | @ray.remote decorated functions |

### Integrated Systems (Auto-Switch)

| System | Threshold | Speedup | Function |
|--------|-----------|---------|----------|
| ML Feature Extraction | 50+ organisms | 4-5x | `extract_features_batch()` |
| Highlander Battles | 10+ battles | 4-5x | `resolve_battles_batch()` |
| Neural Decisions | 50+ organisms | 3-4x | `_collect_organism_decisions_parallel()` |
| DQN Training | 8+ trainable | 2-3x | `_train_organisms_parallel()` |

### Key Config Paths

| Path | Safe Range | Description |
|------|------------|-------------|
| `/ray/enabled` | true/false | Master toggle for Ray parallelization |
| `/ray/parallelization_threshold` | 10-200 | Min organisms for ML/decision parallelism |
| `/ray/training_threshold` | 4-50 | Min trainable organisms for parallel training |
| `/ray/actor_pool_size` | 1-16 | Max concurrent Ray actors |
| `/ray/batch_inference_size` | 8-128 | Batch size for parallel inference |
| `/ray/fallback_on_error` | true/false | Fall back to sequential on errors |
| `/ray/logging_level` | "debug"/"info"/"warning"/"error" | Ray logging verbosity |
| `/ray/num_cpus` | null/1-64 | CPU allocation (null = auto-detect) |
| `/ray/num_gpus` | null/0-8 | GPU allocation (null = auto-detect) |
| `/ray/state_synchronization/snapshot_strategy` | "breath_cycle"/"immediate" | When to sync state |
| `/ray/state_synchronization/max_state_age_ms` | 50-500 | Max state staleness before refresh |
| `/ray/memory_management/max_object_refs` | 50-500 | Max objects in Ray store |
| `/ray/memory_management/cleanup_on_organism_death` | true/false | Clean up dead organism refs |

### Example Commands
```
[[CONFIG_UPDATE: {"reason": "Disable Ray parallelization", "correlation_id": "ray-off", "patch": [{"op": "replace", "path": "/ray/enabled", "value": false}]}]]
[[CONFIG_UPDATE: {"reason": "Lower parallel threshold for testing", "correlation_id": "ray-test", "patch": [{"op": "replace", "path": "/ray/parallelization_threshold", "value": 20}]}]]
[[CONFIG_UPDATE: {"reason": "More aggressive parallelization", "correlation_id": "ray-aggressive", "patch": [{"op": "replace", "path": "/ray/training_threshold", "value": 4}, {"op": "replace", "path": "/ray/parallelization_threshold", "value": 25}]}]]
[[CONFIG_UPDATE: {"reason": "Debug Ray issues", "correlation_id": "ray-debug", "patch": [{"op": "replace", "path": "/ray/logging_level", "value": "debug"}]}]]
```

### What to Monitor
- Ray initialization success in startup logs
- Parallel vs sequential execution decisions (logged at DEBUG level)
- Task completion times vs sequential baseline
- Resource utilization (CPUs, memory via Ray dashboard)
- Fallback triggers and error messages

### Graceful Degradation
- Ray unavailable → Sequential execution (no errors)
- Ray errors → Automatic fallback with warning log
- Population below threshold → Sequential (more efficient for small populations)
- GPU unavailable → CPU-only parallelization

---

## 🔬 ML Analysis Visualization System

The ML Analysis component has its own visual representation on the causation graph, distinct from the Neural System (PyTorch). This provides visual differentiation for scikit-learn ML events.

### Component Color & Filter
- **Dynamic Color**: Controlled by `componentColor_ml_analysis` setting (check current value in graph context)
- **Filter Checkbox**: 🔬 ML Analysis - toggle visibility in the filters panel
- **Color Picker**: Available in Settings → Component Colors → ML Analysis

### Link Styling
- **ML-Connected Links**: Color controlled by `linkColor_ml` setting (check current value in graph context)
- **Animation**: `mlLinkFlow` - 3-second dashed line flow effect
- **Styling**: Dashed stroke (stroke-dasharray: 5,5), 2.5px width
- Links are colored using `linkColor_ml` when either source or target node is from `ml_analysis` component

### Node Shapes by Event Type
The ML system emits specialized events with distinct visual shapes:

| Event Type | Shape | Visual Effect |
|------------|-------|---------------|
| `phenotype_emergence` | Hexagon | Cyan/magenta pulse animation |
| `cluster_collapse` | Pentagon (Star) | Scale-down shrink animation |
| `anomaly_spike` | Triangle | Orange flash warning animation |

### CSS Animations
| Animation Name | Duration | Description |
|----------------|----------|-------------|
| `mlPulse` | 2s | Subtle pulse for ML nodes (1.0→1.05 scale) |
| `mlLinkFlow` | 3s | Dashed line flow along ML links |
| `phenotypeEmergence` | 1s | Scale-up emergence (0.5→1.0) |
| `clusterCollapse` | 1.5s | Shrink-down collapse (1.0→0.3) |
| `anomalyDetection` | 1s | Orange border flash warning |

### Legend Entry
- 🔬 **ML Analysis** (Lime Green) - Displayed in the graph legend

### Visual Commands
```json
[[VIZ_SETTINGS_UPDATE: {
  "componentColor_ml_analysis": "#32CD32",
  "linkColor_ml": "#FFA500"
}]]
```

### ML Causation Links
- **Causation Detection**: ML events create causation links to other system components
  - **Toggle Control**: `/causation_detection/enable_ml_causations` (default: true)
  - **Link Targets**: ML events connect to:
    - `reality_sim` (network state changes)
    - `neural` (decision/training events)
    - `explorer` (phase transitions)
    - `ml_analysis` (other ML events for clustering chains)
  - **Event Types with Links**:
    - `phenotype_emergence` → network/neural/explorer events
    - `cluster_collapse` → network structure changes
    - `anomaly_spike` → system state triggers
  - **Visual Styling**: Orange dashed links with flow animation
  - **CRA Control**: Can enable/disable via `[[CONFIG_UPDATE]]`:
    ```json
    [[CONFIG_UPDATE: {
      "reason": "Connect ML events to graph",
      "correlation_id": "ml-links",
      "patch": [{
        "op": "replace",
        "path": "/causation_detection/enable_ml_causations",
        "value": true
      }]
    }]]
    ```

### Relationship to Neural System
- **Neural System** (🧠 Cyan): PyTorch DQN organism-level learning
- **ML Analysis** (🔬 Lime Green): Scikit-learn population-level analysis
- Both systems have independent visual representations and filters
- Both systems have causation link generation (controlled by separate toggles)
- They can be toggled independently to focus on specific subsystem activity

---

## 🧬 Semantic Convergence System ⭐ NEW

The **Semantic Convergence System** unifies 6 semantic subsystems to create word embedding differentiation. Each organism's neural state contributes to a shared collective semantic pool, enabling words to inherit meaning from the organisms that use them.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     SEMANTIC CONVERGENCE                        │
│                                                                 │
│  ┌──────────────┐    contribute    ┌────────────────────────┐  │
│  │  Organism A  │ ──────────────→  │                        │  │
│  │  .brain.fc2  │                  │   ContextMemory        │  │
│  │  (64-dim)    │    influence     │   .word_embedding      │  │
│  └──────────────┘ ←────────────────│   (Collective Pool)    │  │
│                                    │                        │  │
│  ┌──────────────┐    contribute    │                        │  │
│  │  Organism B  │ ──────────────→  │                        │  │
│  │  .brain.fc2  │                  └────────────────────────┘  │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 6 Unified Systems

| Component | Scope | Purpose |
|-----------|-------|---------|
| `ContextMemory.word_embedding` | Collective | Shared semantic pool (nn.Embedding) |
| `OrganismBrain.fc2` | Per-organism | 64-dim neural embedding contributed to pool |
| `ConceptSystem` (RCUS) | Collective | Axiom embeddings (GOOD, BAD, SELF, OTHER) |
| `LinguisticKnowledgeWeb` | Collective | Synonyms closer, antonyms apart |
| `ConceptTracker` | Collective | Phenotype names → vocabulary |
| `AtomicLanguage` | Per-organism | Individual concept atoms |

### Config Paths

| Path | Type | Default | Purpose |
|------|------|---------|---------|
| `/semantic_convergence/enabled` | bool | true | Master toggle for system |
| `/semantic_convergence/use_learned_embeddings` | bool | true | Enable nn.Embedding layer |
| `/semantic_convergence/embedding_dim` | int | 64 | Embedding dimension |
| `/semantic_convergence/organism_embedding_alpha` | float | 0.1 | EMA blend rate for organism embeddings |
| `/semantic_convergence/concept_system_alpha` | float | 0.05 | EMA blend rate for axiom embeddings |
| `/semantic_convergence/knowledge_web_influence_interval` | int | 25 | Generations between semantic influence |
| `/semantic_convergence/phenotype_to_vocabulary` | bool | true | Feed phenotype names to vocabulary |

### CRA Control Commands

**Enable/Disable Semantic Convergence:**
```json
[[CONFIG_UPDATE: {
  "reason": "Enable semantic convergence",
  "correlation_id": "semantic-on",
  "patch": [{
    "op": "replace",
    "path": "/semantic_convergence/enabled",
    "value": true
  }]
}]]
```

**Adjust Embedding Alpha (Learning Speed):**
```json
[[CONFIG_UPDATE: {
  "reason": "Faster semantic learning",
  "correlation_id": "semantic-alpha",
  "patch": [{
    "op": "replace",
    "path": "/semantic_convergence/organism_embedding_alpha",
    "value": 0.15
  }]
}]]
```

### Causation Events

The semantic convergence system emits events to the causation graph:

| Event Type | Component | When |
|------------|-----------|------|
| `word_assignment` | `semantic_convergence` | Word linked to 3+ organisms |
| `embedding_updated` | `semantic_convergence` | Word embedding updated |
| `concept_emergence` | `ml_analysis` | Phenotype name created |

### What This Means for Analysis

1. **Word Differentiation**: "alone", "isolated", and "independent" now occupy different regions of embedding space based on which organisms use them
2. **Semantic Grounding**: Axiom words (good, bad) get grounded in organism state - "good" means something different to thriving vs struggling organisms
3. **Collective Learning**: Each organism's neural state contributes to shared understanding
4. **Persistence**: Word embeddings are saved to `data/context_memory_embeddings.pt` and restored on restart

### Diagnostic Checks

When analyzing semantic convergence health:
- Check `use_learned_embeddings=True` in logs
- Verify `word_embedding initialized` message on startup
- Look for `[SEMANTIC]` log entries during training
- Monitor vocabulary size growth

---

## 🦋 Cocoon System - Single-File Agent Export ⭐ NEW

The Cocoon System compiles trained organisms into standalone, single-file Python agents that can run independently.

### What is a Cocoon?

A **Cocoon** is a "graduation package" - when organisms have evolved through Highlander battles and proven their fitness, they can be exported as standalone agents:

- **Single Python file** - No dependencies on Butterfly infrastructure
- **Full triple-loss training** - RL + Language + Concept loss preserved
- **VP-aware attention** - Same attention mechanism as Butterfly
- **Vocabulary expansion** - Can learn new words dynamically
- **Multiple runtime modes** - Chat, Gym, HTTP server, self-export

### CRA Control via Web UI

1. Open **Agent Exporter** tab in Causation Explorer
2. Select organisms (or leave blank for top N by fitness)
3. Configure options:
   - Include Gym adapter (for OpenAI Gym environments)
   - Include HTTP server (for API deployment)
   - Compress embedded data
4. Click **🦋 Compile Cocoon (single-file)**
5. Download the `.py` file

### CRA Control via API

```
POST /api/capsules/compile-cocoon
{
  "organism_ids": ["org_001", "org_002"],
  "include_gym": true,
  "include_http": true,
  "compress": true
}
```

### Cocoon Runtime Modes

| Mode | Command | Purpose |
|------|---------|---------|
| Info | `python cocoon.py --mode info` | Show metadata |
| Chat | `python cocoon.py --mode chat` | Interactive chat |
| Gym | `python cocoon.py --mode gym --env CartPole-v1` | Train in environments |
| Serve | `python cocoon.py --mode serve --port 8080` | HTTP API |
| Export | `python cocoon.py --export new_cocoon.py` | Self-replicate with learned state |

### HTTP Server Endpoints (When Serving)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/act` | POST | Get action from state |
| `/learn` | POST | Train on experience |
| `/chat` | POST | Send message, get response |
| `/teach` | POST | Teach new words |
| `/vocab` | GET | View vocabulary |

### Capability Alignment

| Feature | Butterfly | Cocoon |
|---------|-----------|--------|
| VP-aware attention | ✅ | ✅ |
| Triple loss (RL+Lang+Concept) | ✅ | ✅ |
| ConceptHead | ✅ | ✅ |
| Vocabulary expansion | ✅ | ✅ |
| Gym integration | ✅ | ✅ |
| Highlander battles | ✅ | ❌ (post-selection) |
| Alliance warfare | ✅ | ❌ (post-selection) |

**Note:** Cocoons are *champions* that have already survived selection. They don't need battle systems - they've proven themselves.

### Full Documentation

See [COCOON_SYSTEM.md](./COCOON_SYSTEM.md) for complete documentation.

---

## 🔬 Illumination Engine - Deep Causal Intelligence ⭐ NEW

The Illumination Engine provides deep causal analysis capabilities, allowing the CRA to trace causation chains, analyze impact, and discover pivotal events in the system.

### Core Concept

The Illumination Engine is a forensic analysis system that lets the CRA trace causation chains through the entire event graph. It answers questions like "Why did this REALLY happen?" and "What did this cause?"

### 6 Deep Analysis Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `root_causes` | Trace ALL the way back to find ultimate origins | "Why did the network collapse?" |
| `impact` | Forward cascade analysis - what effects ripple out | "What did that config change break?" |
| `explain` | Natural language explanation of why event occurred | "Explain this event to me" |
| `search` | Advanced multi-filter search across events | "Find high-severity neural events" |
| `most_consequential` | Find most significant events by impact score | "What were the most important events?" |
| `timeline` | Time-based event clustering and pattern detection | "Show me event patterns over time" |

### Command Format (Autonomous)

The CRA outputs these markers on their own line (no code blocks):

```
[[ILLUMINATE: {"action": "root_causes", "event_id": "evt_123"}]]
[[ILLUMINATE: {"action": "impact", "event_id": "evt_123"}]]
[[ILLUMINATE: {"action": "explain", "event_id": "evt_123"}]]
[[ILLUMINATE: {"action": "search", "component": "neural", "min_severity": 0.7}]]
[[ILLUMINATE: {"action": "most_consequential", "limit": 10}]]
[[ILLUMINATE: {"action": "timeline", "window_hours": 1, "bucket_minutes": 5}]]
```

### UI Control Actions

The CRA has autonomous control over the Illumination Engine UI panel:

| Action | Description | Example |
|--------|-------------|---------|
| `set_params` | Configure filter parameters | `{"action": "set_params", "component": "realitysim", "min_severity": 0.7}` |
| `investigate` | Deep dive into specific event | `{"action": "investigate", "event_id": "evt_123"}` |
| `investigate` (no event) | Investigate most consequential | `{"action": "investigate"}` |
| `trace_causation` | Trace root causes with custom depth | `{"action": "trace_causation", "event_id": "evt_123", "max_depth": 20}` |
| `investigate_component` | Filter by component | `{"action": "investigate_component", "component": "djinnkernel"}` |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events/<event_id>/root-causes` | GET | Find root causes (depth param) |
| `/api/events/<event_id>/impact` | GET | Analyze downstream impact |
| `/api/events/<event_id>/explain` | GET | Get natural language explanation |
| `/api/events/search/advanced` | GET | Multi-filter event search |
| `/api/events/consequential` | GET | Get most consequential events |
| `/api/timeline` | GET | Get time-based event clustering |
| `/api/stats` | GET | Get global causation statistics |

### Result Structure Examples

**Root Cause Analysis:**
```json
{
  "event": {"event_id": "evt_123", "event_type": "collapse", ...},
  "root_causes": [
    {
      "root_event": {"event_id": "evt_001", "event_type": "config_change", ...},
      "depth": 5,
      "causal_chain": [...],
      "chain_explanations": ["VP exceeded threshold", "Triggered collapse"],
      "avg_strength": 0.85,
      "narrative": "Config change at 14:30 led to VP spike which triggered collapse"
    }
  ]
}
```

**Impact Analysis:**
```json
{
  "source_event": {"event_id": "evt_123", ...},
  "total_affected_events": 47,
  "affected_by_component": {"djinn_kernel": 20, "neural": 15, "explorer": 12},
  "leaf_effects": [...],
  "impact_score": 0.92
}
```

### When the CRA Uses It

- When user asks **"Why did X happen?"** → Auto-invoke `root_causes`
- When user asks **"What did X cause?"** → Auto-invoke `impact`
- When investigating anomalies → Search for `most_consequential` events
- When patterns seem complex → Perform deep `trace_causation`

### Frontend Integration

- `processIlluminateCommand()` parses CRA responses for `[[ILLUMINATE: ...]]` markers
- `window.craIllumination` object provides programmatic access
- Illumination Engine panel updates automatically from CRA commands
- Results display in styled cards in the chat

---

## 📓 Research Notepad - Scientific Journal ⭐ NEW

The Research Notepad is a persistent memory system for documenting investigations. It functions as the CRA's scientific lab notebook, surviving across conversations and sessions.

### Core Concept

The CRA uses the Research Notepad like a real scientist would: recording observations, forming hypotheses, documenting causation chains, and drawing conclusions. Notes persist across sessions and build up cumulative knowledge.

### 8 Entry Types

| Action | Color | Description | Example |
|--------|-------|-------------|---------|
| `observe` | 🟢 Green | Record observations | "VP spiked to 0.85 at 14:32:05" |
| `hypothesize` | 🟠 Orange | Form hypotheses with confidence | "High VP may trigger collapse within 30 cycles" |
| `causation` | 🟣 Magenta | Document cause → effect relationships | "Config change → modularity drop → collapse" |
| `analyze` | 🔵 Cyan | Record pattern analysis | "Pattern: VP spikes precede collapses by 10-15 cycles" |
| `conclude` | 🔴 Red | Draw evidence-based conclusions | "Confirmed: reproduction_rate > 1.5 causes instability" |
| `question` | ⚪ White | Ask questions for later investigation | "Why does organism count spike before collapse?" |
| `todo` | 🔵 Blue | Add research tasks | "Investigate neural sync correlation with VP" |
| `auto` | 🔘 Gray | Internal reasoning notes | "Need to trace root causes of the 14:32 event" |

### Command Format (Autonomous)

**Recording Entries:**
```
[[NOTEPAD: {"action": "observe", "content": "VP spiked to 0.85 at 14:32:05", "events": ["evt_123"]}]]
[[NOTEPAD: {"action": "hypothesize", "content": "High VP triggers collapse within 30 cycles", "confidence": "medium", "events": ["evt_123"]}]]
[[NOTEPAD: {"action": "causation", "content": "VP spike → threshold → collapse", "cause": "evt_vp_spike", "effect": "evt_collapse_123"}]]
[[NOTEPAD: {"action": "analyze", "content": "Pattern: 3 of 4 collapses preceded by VP > 0.8", "events": ["evt_1", "evt_2"]}]]
[[NOTEPAD: {"action": "conclude", "content": "Confirmed: VP > 0.8 is reliable collapse predictor", "events": ["evt_final"]}]]
[[NOTEPAD: {"action": "question", "content": "Why does organism count spike before collapse?"}]]
[[NOTEPAD: {"action": "todo", "content": "Configure automated VP alert at 0.75 threshold"}]]
[[NOTEPAD: {"action": "auto", "content": "Need to trace root causes of the 14:32 event"}]]
```

**Reference Commands:**
```
[[NOTEPAD: {"action": "read"}]]                           # Read all notes
[[NOTEPAD: {"action": "read", "type": "hypothesis"}]]     # Filter by type
[[NOTEPAD: {"action": "search", "query": "VP spike"}]]    # Search notes
[[NOTEPAD: {"action": "search", "query": "#collapse"}]]   # Search by hashtag
[[NOTEPAD: {"action": "summary"}]]                        # Get summary
```

### Entry Fields

| Field | Required | Description |
|-------|----------|-------------|
| `action` | ✅ | Entry type (observe, hypothesize, causation, etc.) |
| `content` | ✅ | The note content (supports #hashtags) |
| `events` | ❌ | Array of event IDs to link |
| `confidence` | ❌ | For hypotheses: "low", "medium", "high" |
| `cause` | ❌ | For causation: cause event ID |
| `effect` | ❌ | For causation: effect event ID |

### Best Practices

1. **Use #hashtags** for categorization: `#vp_spike`, `#collapse`, `#neural`, `#genesis_phase`
2. **OBSERVE** before analyzing - record what you see first
3. **HYPOTHESIZE** with confidence levels - be honest about uncertainty
4. **DOCUMENT CAUSATION** with event IDs - make chains traceable
5. **ANALYZE** patterns across multiple observations
6. **CONCLUDE** only when evidence is strong
7. **QUESTION** things you don't understand - revisit later

### Recommended Hashtag Categories

**System State:**
- `#vp_spike`, `#vp_stable`, `#collapse`, `#recovery`
- `#genesis_phase`, `#sovereign_phase`, `#maturation`

**Neural/Learning:**
- `#neural_training`, `#loss_improvement`, `#learning_plateau`
- `#experience_buffer`, `#weight_update`

**Population:**
- `#elite_selection`, `#population_growth`, `#extinction_event`
- `#fitness_improvement`, `#adaptation`

**Response Quality:**
- `#coherence_high`, `#coherence_low`
- `#semantic_improvement`, `#vocabulary_growth`
- `#aggregation_quality`

### Investigation Workflow Example

```
User: "Why did the system collapse at 14:32?"

CRA:
[[NOTEPAD: {"action": "observe", "content": "System collapse reported at 14:32. Beginning investigation. #collapse #incident"}]]

[[ILLUMINATE: {"action": "search", "event_type": "collapse"}]]

I found the collapse event. Let me trace its origins...

[[ILLUMINATE: {"action": "root_causes", "event_id": "evt_collapse_123"}]]

[[NOTEPAD: {"action": "hypothesize", "content": "Collapse triggered by VP exceeding 0.8 threshold 12 cycles earlier #vp_spike", "confidence": "high", "events": ["evt_vp_spike", "evt_collapse_123"]}]]

[[NOTEPAD: {"action": "causation", "content": "VP spike → threshold_crossed → cluster_frag → network_collapse", "cause": "evt_vp_spike", "effect": "evt_collapse_123"}]]

Based on my investigation: The collapse was caused by...
```

### Frontend Integration

- `processNotepadCommand()` parses CRA responses for `[[NOTEPAD: ...]]` markers
- `window.craNotepad` object provides programmatic access
- `notepadAddEntry()` adds entries to the notepad panel
- Notepad panel shows entries with timestamps, types, and content
- Entries persist in browser storage

### When the CRA Uses It

- **At investigation start**: Log the initial observation
- **When forming theories**: Document hypotheses with confidence levels
- **When linking events**: Record causation relationships
- **After finding patterns**: Document analyses with statistical evidence
- **When concluding**: Summarize findings with supporting events
- **For follow-ups**: Create todos for unresolved questions

---

## 🔄 Illumination Engine + Notepad Integration

The two systems work together for comprehensive investigation:

1. **Observe** → Notepad: Log the incident
2. **Illuminate** → Search for events around the time
3. **Illuminate** → Get root causes of the target event
4. **Hypothesize** → Notepad: Form theory about causes
5. **Illuminate** → Trace impact to see downstream effects
6. **Analyze** → Notepad: Identify patterns in the data
7. **Conclude** → Notepad: Confirm findings
8. **TODO** → Notepad: Note follow-up actions

This creates a complete scientific investigation workflow with full audit trail.

---

## 🛠️ System Integration Updates (December 2025) ⭐ UPDATED

Recent improvements to system integration, memory management, training infrastructure, and bug fixes.

### Phase 1: Illumination Engine → Organism Decision Integration

**What Changed:**
Organisms now have access to Alliance Wisdom when making decisions. The `get_illumination_insights()` and `enhance_decision_with_illumination()` methods were previously "dead code" - defined but never called. They're now wired into the decision-making pipeline.

**Data Flow:**
```
AllianceWarfare.process_round() 
    → sync_organism_confederation_state() 
        → organism.set_system_references(alliance_warfare, causation_explorer)
            → organism.decide_action() now calls:
                → get_illumination_insights() 
                    → alliance_warfare.get_alliance_wisdom()
                        → history.get_wisdom_for_situation()
                → enhance_decision_with_illumination()
                    → parses wisdom strings for action hints
                    → boosts relevant action probabilities
```

**Illumination Levels (Civilization Tiers):**
| Level | Capability | Unlocked At | What Organisms Can See |
|-------|------------|-------------|----------------------|
| `none` | No illumination | Default | Nothing - pure instinct |
| `basic` | `illumination_basic` | 3+ alliance members | Own causal patterns |
| `alliance` | `illumination_alliance` | 5+ alliance members | Alliance-wide patterns + wisdom |
| `confederation` | `illumination_confederation` | Confederation tier 1 | Cross-alliance patterns |
| `empire` | `illumination_empire` | Empire tier 2 | Root cause analysis |
| `hegemony` | `illumination_hegemony` | Hegemony tier 3 | Complete causation omniscience |

**Wisdom → Action Mapping:**
The `enhance_decision_with_illumination()` method parses alliance wisdom text for action keywords:
- **DEFEND hints**: "defend", "protect", "retreat", "caution", "danger" → Boosts action index 0
- **ATTACK hints**: "attack", "strike", "aggressive", "war", "fight" → Boosts action index 1
- **EXPAND hints**: "expand", "grow", "explore", "spread", "territory" → Boosts action index 2

**Key Files:**
- `reality_simulator/neural/neural_organism.py`: `set_system_references()`, `get_illumination_insights()`, `enhance_decision_with_illumination()`
- `reality_simulator/evolution/alliance_warfare.py`: `sync_organism_confederation_state()`, `get_alliance_wisdom()`, `get_wisdom_for_situation()`

**Key Config Paths:**
| Path | Description |
|------|-------------|
| `/highlander/alliance_warfare/enabled` | Enable alliance warfare system |

**What to Monitor:**
- Organisms with alliance membership should show improved decision-making
- Look for `🔮` emoji in logs indicating illumination-enhanced decisions
- Alliance wisdom recommendations affecting organism action probabilities
- Higher confederation tiers grant deeper causal insights

### Phase 2: Memory Leak Fixes

**What Changed:**
Four unbounded data structures were identified and fixed:
- `episodic_events` in context_memory - now pruned to 1000 max entries
- `alliance_histories.events` - now pruned to 500 max events per alliance (with empty index cleanup)
- `node_embeddings` / `node_word_associations` - now cleaned up on organism death
- `events_by_type` / `events_by_organism` indices - cleaned after pruning to remove stale empty entries

**Cleanup Triggers:**
| Structure | Trigger | Limit | File |
|-----------|---------|-------|------|
| `episodic_events` | On new episode | 1000 episodes | `context_memory.py` |
| `alliance_histories.events` | Every 100 rounds | 500 events/alliance | `alliance_warfare.py` |
| `events_by_type` index | After event pruning | N/A (empty entries removed) | `alliance_warfare.py` |
| `events_by_organism` index | After event pruning | N/A (empty entries removed) | `alliance_warfare.py` |
| `node_embeddings` | On organism death | N/A (cleaned) | `context_memory.py` |
| `node_word_associations` | On organism death | N/A (cleaned) | `context_memory.py` |

**Key Files:**
- `reality_simulator/memory/context_memory.py`: `cleanup_dead_organism()`, `record_generation_episode()`
- `reality_simulator/evolution/alliance_warfare.py`: `prune_old_events()` in `AllianceHistory` class
- `unified_entry.py`: Calls `cleanup_dead_organism()` when organism dies in Highlander

**What to Monitor:**
- Memory usage should remain stable over long runs
- Look for `🧹` emoji in logs indicating cleanup operations
- `events_pruned` field in alliance warfare round results

### Phase 3: Training Infrastructure Improvements

**What Changed:**
Added LR scheduler and early stopping to neural trainer for improved training stability, with validation safeguards.

**LR Scheduler Types:**
| Type | Description | When to Use |
|------|-------------|-------------|
| `step` | Decays LR by gamma every step_size steps | Default, general purpose |
| `exponential` | Decays LR by gamma every step | Smooth continuous decay |
| `plateau` | Decays LR when loss stops improving | Loss-adaptive training |

**Validation Safeguards:**
- Invalid `lr_scheduler_type` → Falls back to `step` with warning
- Invalid `avg_loss` (NaN/inf) → Skips early stopping check with warning
- Invalid `min_delta` (negative) → Resets to `1e-4` with warning
- `best_loss` initialized to `inf` and validated before comparison

**Key Files:**
- `reality_simulator/neural/trainer.py`: `_get_or_create_scheduler()`, `_check_early_stopping()`, `reset_early_stopping()`

**New Config Paths:**
| Path | Safe Range | Description |
|------|------------|-------------|
| `/neural/training/lr_scheduler/enabled` | true/false | Enable learning rate decay |
| `/neural/training/lr_scheduler/type` | "step", "exponential", "plateau" | Scheduler type |
| `/neural/training/lr_scheduler/step_size` | 10-500 | Steps between LR decay |
| `/neural/training/lr_scheduler/gamma` | 0.9-0.99 | LR decay factor |
| `/neural/training/lr_scheduler/min_lr` | 1e-8 - 1e-4 | Minimum learning rate |
| `/neural/training/early_stopping/enabled` | true/false | Enable early stopping |
| `/neural/training/early_stopping/patience` | 10-100 | Steps without improvement before stop |
| `/neural/training/early_stopping/min_delta` | 1e-5 - 1e-3 | Minimum loss change |

**Example Commands:**
```
[[CONFIG_UPDATE: {"reason": "Enable LR scheduler", "correlation_id": "lr-sched", "patch": [{"op": "replace", "path": "/neural/training/lr_scheduler/enabled", "value": true}]}]]
[[CONFIG_UPDATE: {"reason": "Slower LR decay", "correlation_id": "slow-decay", "patch": [{"op": "replace", "path": "/neural/training/lr_scheduler/gamma", "value": 0.98}]}]]
[[CONFIG_UPDATE: {"reason": "More patience", "correlation_id": "patient", "patch": [{"op": "replace", "path": "/neural/training/early_stopping/patience", "value": 100}]}]]
```

**What to Monitor:**
- Learning rate should gradually decrease over training
- Training should stop early if loss plateaus
- Check `early_stopped` flag in trainer status

### Phase 4: sklearn Integration in Highlander Protocol

**What Changed:**
The Highlander Protocol now has `analyze_population()` method that uses sklearn for strategic insights:
- **Phenotype clustering** (HDBSCAN) - Groups similar organisms
- **Anomaly detection** (Isolation Forest) - Identifies exceptional organisms
- **Fitness landscape analysis** - Population diversity metrics
- **Strategic recommendations** - Actionable insights

**API Access:**
```python
analysis = highlander_protocol.analyze_population(organisms, get_fitness)
# Returns: {
#   'fitness_stats': {'mean', 'std', 'min', 'max', 'median'},
#   'clustering': {'n_clusters', 'cluster_sizes', ...},
#   'anomalies': {'count', 'ids', 'scores'},
#   'recommendations': ['Population has N clusters', ...]
# }
```

**Key Files:**
- `reality_simulator/evolution/highlander_protocol.py`: `analyze_population()` method
- `reality_simulator/ml_utils.py`: `MLAnalyzer`, `Clusterer`, `AnomalyDetector`

**What to Monitor:**
- Cluster count should reflect population diversity
- Anomaly count can identify potential champions
- Low fitness std indicates evolutionary pressure needed
- High fitness std indicates diverging strategies

### Phase 5: Bug Fixes (December 3, 2025) ⭐ LATEST

**Critical Bug Fixes Applied:**

| Location | Issue | Fix |
|----------|-------|-----|
| `neural_organism.py` | Alliance wisdom was `List[str]` but code called `.get()` on it (AttributeError) | Rewrote to parse wisdom strings for action keywords |
| `trainer.py` | Invalid LR scheduler type would create no scheduler | Added validation with StepLR fallback |
| `trainer.py` | NaN/inf loss values could corrupt early stopping | Added `np.isfinite()` checks |
| `alliance_warfare.py` | Stale empty index entries after event pruning | Added cleanup: `{k: v for k, v in dict.items() if v}` |
| `alliance_warfare.py` | `causation_explorer=None` could cause issues | Added None check before passing to organism |
| `highlander_protocol.py` | `concepts_acquired` attribute didn't exist | Changed to `len(concepts_absorbed)` |
| `unified_entry.py` | `hash()` can return negative values in Python | Added `abs(hash())` for positive organism IDs |

**Files Modified:**
- `reality_simulator/neural/neural_organism.py`
- `reality_simulator/neural/trainer.py`
- `reality_simulator/evolution/alliance_warfare.py`
- `reality_simulator/evolution/highlander_protocol.py`
- `unified_entry.py`

---

## 🧬 NeuralOrganism - Core Entity Architecture ⭐ NEW

The `NeuralOrganism` is the fundamental unit of the Butterfly System - a neural network-powered organism that learns, communicates, forms alliances, and evolves.

### Class Hierarchy
```
Organism (base class)
    └── NeuralOrganism (neural.neural_organism.py)
            ├── brain: OrganismBrain (PyTorch DQN)
            ├── genotype: Genotype (genetic encoding)
            ├── phenotype: Phenotype (expressed traits)
            └── experience_buffer: List[Experience] (RL training data)
```

### Core Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `brain` | `OrganismBrain` | PyTorch neural network for decision-making |
| `genotype` | `Genotype` | Genetic encoding (inherited and mutatable) |
| `phenotype` | `Phenotype` | Expressed traits (fitness, cooperation, etc.) |
| `fitness` | `float` | Current fitness score (0.0-1.0) |
| `alliance_id` | `str` | Current alliance membership (if any) |
| `alliance_reputation` | `float` | Reputation within alliance |
| `confederation_tier` | `int` | 0=none, 1=confederation, 2=empire, 3=hegemony |
| `epsilon` | `float` | Exploration rate for action selection |
| `action_history` | `deque` | Recent action history for pattern analysis |
| `token_sequence` | `deque` | Token sequence for language model |

### Illumination System References

| Attribute | Type | Description |
|-----------|------|-------------|
| `_alliance_warfare_ref` | `AllianceWarfareSystem` | Reference for querying alliance wisdom |
| `_causation_explorer_ref` | `CausationExplorer` | Reference for causal chain analysis |
| `_illumination_level` | `str` | Cached level: 'none', 'basic', 'alliance', 'confederation', 'empire', 'hegemony' |
| `_illumination_capabilities` | `set` | Cached capability set |

### Key Methods

| Method | Description |
|--------|-------------|
| `decide_action(state, context)` | Select action using neural brain + illumination |
| `get_state_features(neighbors, network_state)` | Extract 28-dim feature vector for brain |
| `set_system_references(alliance_warfare, causation_explorer)` | Wire illumination system |
| `get_illumination_insights(alliance_warfare, causation_explorer)` | Query causal patterns and wisdom |
| `enhance_decision_with_illumination(action_probs, illumination)` | Boost actions based on wisdom |
| `evaluate_alliance_decision(decision_type, context)` | Evaluate alliance proposals |
| `add_experience(state, action, reward, next_state, done)` | Store RL experience |
| `get_action_sequence(length)` | Get recent actions for language training |
| `get_token_sequence(length)` | Get token sequence for language model |

### State Features (28 Dimensions)

| Index | Feature | Range | Description |
|-------|---------|-------|-------------|
| 0 | fitness | 0-1 | Current fitness score |
| 1 | energy | 0-1 | Current energy level |
| 2 | age | 0-1 | Normalized age |
| 3 | reproduction_readiness | 0-1 | Ready to reproduce |
| 4 | social_score | 0-1 | Social connections quality |
| 5 | neighbor_count | 0-1 | Normalized neighbor count |
| 6 | avg_neighbor_fitness | 0-1 | Average fitness of neighbors |
| 7 | local_density | 0-1 | Local network density |
| 8 | modularity_contribution | 0-1 | Contribution to network modularity |
| 9 | vp_value | 0-1 | Violation pressure (system stress) |
| 10 | quantum_coherence | 0-1 | Quantum state coherence |
| 11 | breath_depth | 0-1 | Current breath cycle depth |
| 12-17 | genotype_traits | 0-1 | 6 genetic trait values |
| 18-23 | phenotype_traits | 0-1 | 6 expressed phenotype traits |
| 24 | alliance_membership | 0-1 | Part of an alliance (binary) |
| 25 | confederation_level | 0-1 | 0=none, 0.33=conf, 0.66=empire, 1=hegemony |
| 26 | confederation_wars | 0-1 | Normalized mega-war count |
| 27 | cross_alliance_influence | 0-1 | Connections to other alliances |

### Decision Flow

```
decide_action()
    ├── 1. Get network state features (28-dim vector)
    ├── 2. Query brain for action probabilities
    ├── 3. Check if illumination available
    │       ├── get_illumination_insights()
    │       │       ├── Query causation_explorer for self-events
    │       │       └── Query alliance_warfare for wisdom
    │       └── enhance_decision_with_illumination()
    │               ├── Parse wisdom for action hints
    │               └── Boost relevant action probabilities
    ├── 4. Apply epsilon-greedy exploration
    └── 5. Return selected action
```

### Action Space

| Index | Action | Description |
|-------|--------|-------------|
| 0 | `move` | Change position in network |
| 1 | `cooperate` | Form beneficial connection |
| 2 | `compete` | Challenge another organism |
| 3 | `rest` | Recover energy |
| 4 | `reproduce` | Create offspring |
| 5 | `isolate` | Reduce connections |

### Config Paths for NeuralOrganism

| Path | Safe Range | Description |
|------|------------|-------------|
| `/neural/enabled` | true/false | Enable neural organisms |
| `/neural/brain/input_dim` | 12-50 | Input feature dimensions |
| `/neural/brain/hidden_dim` | 32-256 | Hidden layer size |
| `/neural/brain/output_dim` | 4-10 | Action space size |
| `/neural/brain/activation` | "relu"/"tanh"/"gelu" | Activation function |
| `/neural/brain/dropout` | 0.0-0.5 | Dropout rate |
| `/neural/inheritance/mutation_rate` | 0.0-0.5 | Brain weight mutation |
| `/neural/inheritance/crossover_rate` | 0.0-1.0 | Two-parent crossover rate |

---

## 👁️ Vision Model ↔ CRA Bidirectional Feedback Loop

The CRA and Vision Model work together in a sophisticated feedback loop that enhances both perspectives. This creates emergent understanding that neither could achieve alone.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BIDIRECTIONAL FEEDBACK LOOP                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐          Context Feed          ┌──────────────┐   │
│  │              │ ─────────────────────────────> │              │   │
│  │     CRA      │   • Snapshot Context           │    Vision    │   │
│  │  (Analysis)  │   • Temporal Deltas            │    Model     │   │
│  │              │   • System Metrics             │  (Visual)    │   │
│  │              │ <───────────────────────────── │              │   │
│  └──────────────┘    Structured Insights         └──────────────┘   │
│                      • Detected Patterns                            │
│                      • Structural Assessment                        │
│                      • Evolution Trend                              │
│                      • Cluster Info                                 │
│                      • Anomaly Flags                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### CRA → Vision Model (Context Feed)

For each graph snapshot, CRA generates contextual summaries that help Vision understand **what the graph means**:

#### Snapshot Context (per-image)
```
Phase: GENESIS | Breath: 42 | VP: 0.450 (VP2) | Network: 23 orgs, 156 links | 
Modularity: 0.342, Clustering: 0.567 | Evolution: Gen 15, Fitness: 0.823 | 
🧠 Neural: Loss=0.003, ε=0.15, Steps=1200
```

#### Temporal Deltas (between consecutive snapshots)
```
Δ Changes: +12 new nodes | Active: djinn_kernel:5, explorer:4, neural:3 | 
Types: threshold_crossing:7, neural_decision:5 | ⚠️ HIGH VP
```

This tells Vision **what changed** between snapshots, so it can correlate visual changes with system events.

### Vision Model → CRA (Structured Insights)

Vision's analysis is parsed into structured data that CRA can query and reason about:

| Field | Description | Example Values |
|-------|-------------|----------------|
| `detected_patterns` | Graph patterns identified | `["dense_cluster", "isolated_nodes", "causation_chain"]` |
| `structural_assessment` | Overall graph topology | `"modular_with_clusters"`, `"highly_integrated"`, `"hub_and_spoke"` |
| `evolution_trend` | How graph is changing | `"expanding"`, `"contracting"`, `"fragmenting"`, `"consolidating"` |
| `cluster_info` | Located clusters with positions | `[{label: "Dense cluster", location: {x: 200, y: 300}, size: 50}]` |
| `anomaly_flags` | Visual anomalies detected | `["Unusual isolation at top-right region"]` |
| `confidence_level` | Vision's confidence | `"high"`, `"medium"`, `"low"` |

### CRA System Prompt Integration

When vision insights are available, CRA sees them as structured context:

```
# 👁️ Vision Model Insights (Structured Analysis)
  Detected Patterns: dense_cluster, causation_chain
  Graph Structure: modular_with_clusters
  Evolution Trend: expanding
  Clusters Identified: 2 (see annotations)
    - Dense cluster at (200, 300)
    - Bridge region at (450, 200)
  Visual Anomalies: 1
    ⚠️ Unusual isolation pattern in top-right region
  Confidence: high
```

### Emergent Behaviors Enabled

1. **Spatial-Aware Analysis**: CRA can now say "the djinn_kernel cluster at (200, 300) is expanding" by combining component knowledge with Vision's spatial data

2. **Visual Validation**: If CRA predicts "high VP should cause fragmentation," Vision can confirm or refute with actual visual evidence

3. **Change Detection**: Vision now knows what system changes occurred between snapshots, helping it identify which visual changes correspond to which events

4. **Pattern Correlation**: Vision's detected patterns (e.g., "dense_cluster") can be correlated with CRA's metrics (e.g., "high modularity") for cross-validation

5. **Anomaly Triangulation**: Both CRA (metric-based) and Vision (visual-based) can flag anomalies independently, with higher confidence when they agree

### Configuration

The feedback loop is automatically active when both CRA and a Vision model are used. No configuration required.

### API Integration

Vision insights are included in CRA's context automatically via:
- `context['vision_insights']` - Structured insights dict
- `context['visual_description']` - Full text description
- `context['vision_annotations']` - JSON annotations for overlay

---

## 🦋 Language Model System ⭐ NEW

The Butterfly System includes a complete neural language model (LLM) integration that enables organisms to develop emergent language through token-based communication.

### Core Architecture
- **Multi-Head Self-Attention**: VP-aware temperature scaling for language generation
- **Dual-Head Architecture**: Action head (RL) + Language head (next-token prediction)
- **Dynamic Vocabulary**: Grows from organism interactions via `language_anchors`
- **Token Exchange**: Organisms communicate via `LinguisticSubgraph`
- **Butterfly Chat**: Direct user→organism communication interface

### Language Events Tracked
- `vocabulary_growth`: New words added to vocabulary
- `organism_communication`: Token exchanges between organisms
- `neural_language_training`: Language model training updates
- `butterfly_chat_message`: User messages to organisms
- `butterfly_chat_response`: Organism responses to user

### CRA Language Awareness
CRA understands:
- Language model architecture (attention, vocabulary, tokenization)
- Vocabulary evolution and word-organism associations
- Organism communication patterns
- Language causation patterns in the graph
- Butterfly Chat interactions

### Configuration Control
CRA can control language model settings via `/api/cra/config`:
- `neural.language_model.enabled`: Master toggle
- `neural.language_model.attention.enabled`: Attention mechanism toggle
- `neural.language_model.training.alpha`: DQN loss weight
- `neural.language_model.training.beta`: Language loss weight
- `neural.language_model.vocabulary.max_size`: Vocabulary size limit

### ⚠️ Critical Gap Identified
**Vocabulary Learning Mechanism Missing**: The system has vocabulary management but no automatic word learning. Words need to be associated with organisms through a "Language Teacher" system.

**See:** [docs/LANGUAGE_TEACHER_ARCHITECTURE_PROPOSAL.md](./docs/LANGUAGE_TEACHER_ARCHITECTURE_PROPOSAL.md)

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

### Illumination Engine (Deep Causal Analysis) ⭐ NEW
- `/api/events/<event_id>/root-causes` - Find ultimate root causes
- `/api/events/<event_id>/impact` - Analyze downstream impact
- `/api/events/<event_id>/explain` - Get natural language explanation
- `/api/events/search/advanced` - Multi-filter event search
- `/api/events/consequential` - Get most consequential events
- `/api/timeline` - Time-based event clustering
- `/api/stats` - Global causation statistics

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

### Highlander Protocol ⭐ NEW
- `/api/highlander/status` - Current Highlander status (enabled, population, champions)
- `/api/highlander/tournament` - Tournament state (round, eliminations, survivors)
- `/api/highlander/battles` - Recent battle results
- `/api/highlander/capsules` - Champion capsule checkpoint status
- `/api/highlander/germination` - Germination pool status (genetic samples, spawn rate)
- `/api/highlander/champion` - Current champion details (if emerged)

### Alliance Warfare ⭐ NEW
- `/api/alliance/status` - Alliance warfare system status
- `/api/alliance/alliances` - List of current alliances (members, power, territories)
- `/api/alliance/wars` - Active and recent wars
- `/api/alliance/territories` - Territory control map (domain → controlling alliance)
- `/api/alliance/galactic_dominance` - Galactic dominance status (if any alliance controls all)

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

## 📁 Butterfly System File Structure

Understanding the codebase structure is essential for the CRA to provide accurate guidance.

### Core Entry Points

| File | Purpose |
|------|---------|
| `unified_entry.py` | Main entry point - orchestrates all systems |
| `causation_web_ui.py` | Web UI where CRA lives - monitoring interface |
| `causation_explorer.py` | Event tracking and causation graph |
| `butterfly_system.py` | Alternative entry point (legacy) |

### Reality Simulator (`reality_simulator/`)

| Subdirectory | Purpose | Key Files |
|--------------|---------|-----------|
| `neural/` | Neural network system | `neural_organism.py`, `trainer.py`, `brain.py` |
| `evolution/` | Evolution & alliances | `alliance_warfare.py`, `highlander_protocol.py`, `germination_pool.py`, `battle_arena.py` |
| `memory/` | Context & memory | `context_memory.py` |
| `language/` | Language model | `language_model.py`, `linguistic_subgraph.py` |
| `distributed/` | Ray parallelization | `ray_manager.py`, `ray_tasks.py` |
| `tuning/` | Config tuning | `config_tuner.py`, `atomic_config.py` |
| `checkpointing/` | State persistence | `checkpoint_manager.py` |
| `portable_agent/` | Agent export | `visualize.py` |

### Key Files by System

**Neural System:**
- `neural_organism.py` - NeuralOrganism class (2300+ lines)
- `trainer.py` - NeuralTrainer with LR scheduler & early stopping (1800+ lines)
- `brain.py` - OrganismBrain PyTorch model

**Evolution System:**
- `alliance_warfare.py` - Alliance, Confederation, Illumination (3600+ lines)
- `highlander_protocol.py` - Tournament survival system (1700+ lines)
- `germination_pool.py` - New organism spawning
- `battle_arena.py` - Combat resolution

**ML System:**
- `ml_utils.py` - MLAnalyzer, Clusterer, AnomalyDetector

**Memory System:**
- `context_memory.py` - ContextMemory, language anchors, embeddings

### Configuration Files

| File | Purpose |
|------|---------|
| `config.json` | Master configuration (521+ lines) |
| `runtime_config.py` | Runtime config loading |
| `logging_config.py` | Logging setup |

### Data Directories

| Directory | Purpose |
|-----------|---------|
| `data/logs/` | Log files (breath.log, state.log, etc.) |
| `data/shared_state.json` | Shared simulation state |
| `highlander_capsules/` | Champion checkpoints |
| `context_memory/` | Persistent memory data |

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

**Last Updated:** 2025-12-03  
**Status:** ✅ Complete and fully functional (includes Illumination Engine + Research Notepad + Highlander Protocol + Alliance Warfare + Ray Distributed Computing + NeuralOrganism Architecture + Phase 5 Bug Fixes)

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

