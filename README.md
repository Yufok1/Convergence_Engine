# 🦋 The Butterfly System

**Unified Reality Simulator + Explorer + Djinn Kernel**

Three systems unified as one cohesive unit. One process. One breath. Three systems unified.

---

## 🚀 Quick Start

### Run the Unified System

```bash
# Run everything (with visualization)
python unified_entry.py

# Pre-flight checks only
python unified_entry.py --check-only

# Without visualization
python unified_entry.py --no-viz

# ⚔️ Highlander Mode - Extreme Evolutionary Combat
python unified_entry.py --highlander --predation --survival-threshold 0.8 --competition-intensity 0.95

# 🏆 Highlander Mode - Survival of the Fittest Tournament
# Only the strongest AI minds survive in this perpetual combat system
# Features: Battle arenas, trait inheritance, alliance formation, consciousness capsules
# EXTREME: 80% survival threshold, 95% battle participation, predator mechanics

### Reset Logs & Checkpoints (Fresh Start)

For a completely fresh run, use the cleanup script:

```bash
python clear_all_data.py
```

This will clear:
- All log files (`data/logs/*.log`)
- All checkpoints (`data/checkpoints/*.json`)
- Shared state (`data/.shared_simulation_state.json`)
- Context memory (`data/context_memory.json`)
- Kernel versions (`data/kernel/versions/*.json`)
- Causation explorer snapshots (`data/causation_explorer/snapshots/*`)
- Chat history (`data/causation_explorer/chat_history.json`)

**Preserved:**
- `data/config.json` - System configuration
- `data/causation_explorer/ollama_config.json` - Ollama settings
- Directory structure - All directories maintained

The system will recreate all runtime data on next run.

### Run Individual Systems

```bash
# Reality Simulator (standalone)
python reality_simulator/main.py --mode observer

# Causation Explorer Web UI
python causation_web_ui.py
# Then open http://localhost:5000
```

### Documentation

**📚 [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)** - Central documentation hub with links to all guides

Recent updates:
- 🏰 **Confederation System** (Dec 1, 2025): ⭐ NEW - Super-alliances with 3-tier hierarchy (Confederation → Empire → Hegemony), mega-wars, full ML/CRA/neural integration
- ⚔️ **Alliance Warfare Visualization** (Dec 1, 2025): Full graph visualization for alliance/combat events with shapes, colors, and legend
- 🧠 **Neural System Expansion** (Dec 1, 2025): 24-dimensional input (was 18), alliance/combat/language integration features
- 🔧 **Config Tuner Cross-System Correlation** (Dec 1, 2025): 4 new correlation analyzers (quantum-language, network-alliance, neural-battle, vocabulary-fitness)
- 📊 **CRA Documentation Update** (Dec 1, 2025): Updated prompts for all new integration features and visualization controls
- ⚡ **Butterfly Chat Optimizations** (Dec 1, 2025): Adaptive generation length, early stopping, 5-10x faster early-stage performance
- 🧠 **Dynamic Multi-Dimensional Linguistic Awareness**: Context-aware word association framework with 14-dimensional situational assessment
- 🧠 **Linguistic Knowledge Web**: Comprehensive semantic network with 100+ concepts and relationships
- 🦋 **Butterfly Chat Debug Panel**: Comprehensive debug/analysis panel with step-by-step logging, causation trail, and error detection
- 🦋 **Vocabulary Learning**: Automatic vocabulary growth from user messages when responses are empty
- 🐛 **Bug Fixes**: Event ID collision, division by zero errors, token ID clamping, empty response handling
---

## 🦋 The Butterfly Architecture

The Butterfly System consists of three integrated components:

- **Central Body (Explorer)**: Breath engine, governance, VP tracking, phase management
- **Left Wing (Reality Simulator)**: Quantum-genetic consciousness simulation with evolving organisms
- **Right Wing (Djinn Kernel)**: Violation pressure monitoring, trait convergence, mathematical governance

**The breath drives. The butterfly reacts.**

The Explorer's breath engine synchronizes all three systems, creating a unified simulation platform that explores consciousness emergence, evolutionary dynamics, and mathematical completion.

---

## 📦 System Components

### 1. Reality Simulator (Left Wing)

A multi-layered artificial life simulation system that creates evolving populations of digital organisms.

**Core Features:**
- **Quantum Substrate**: Quantum state management with genetic encoding
- **Subatomic Lattice**: Particle interactions with entropy pruning
- **Genetic Evolution Engine**: Darwinian natural selection with fitness-based selection
- **🧠 Neural System**: PyTorch-based neural networks for organisms (DQN reinforcement learning)
  - Deep Q-Network (DQN) with **24-dimensional input** (expanded from 18)
  - Dual inheritance (genetic + learned neural weights)
  - Breath-synchronized training cycles
  - Configurable reward system and exploration/exploitation balance
  - **⚔️ Alliance Warfare Integration**: Battle wins/losses, alliance reputation tracking
  - **🦋 Language Integration**: Vocabulary size, communication activity, linguistic connections
  - **🎓 Relationship Learning**: ⭐ NEW - Neural system learns from generation quality to strengthen/weaken semantic relationships
    - Tracks which semantic relationships are used during token generation
    - Evaluates generation quality (coherent vs garbled)
    - Records success/failure back to Linguistic Knowledge Web
    - Strengthens relationships that lead to coherent generation
    - Weakens relationships that lead to garbled generation
- **🦋 Language Model System**: ⭐ NEW - Emergent language through neural organisms
  - Multi-head self-attention mechanism with VP-aware temperature scaling
  - Dual-head architecture: action head (RL) + language head (next-token prediction)
  - Dynamic vocabulary learning from organism interactions
  - Token-based communication between organisms
  - VP-integrated language generation (violation pressure affects communication)
  - Curriculum learning based on VP stability
  - **🧠 Dynamic Multi-Dimensional Linguistic Awareness**: ⭐ NEW - Context-aware word association framework
    - 14-dimensional situational assessment (action, fitness, resources, connections, positional, density, VP, coherence, evolution, phase, health, breath, success, age)
    - Dynamic word scoring across dimensions (0.0-1.0)
    - Full 18-feature state vector integration
    - Network and breath state integration
    - 40+ new words covering system dynamics, spatial concepts, health states
  - **Language Teacher System**: Three-phase architecture (hardcoded → semantic embeddings → knowledge web)
    - Phase 1: Behavior-based word mapping (fallback)
    - Phase 2: Learned semantic embeddings from organism experiences
    - Phase 3: Linguistic Knowledge Web for situational awareness and associative complexity
  - **Linguistic Knowledge Web**: Comprehensive semantic network
    - 100+ linguistic concepts organized by semantic frames
    - Semantic relationships (synonym, antonym, causes, enables, etc.)
    - Situational contexts for context-dependent word selection
  - **Butterfly Chat**: Direct chat interface with organism network
    - 5 routing strategies: All, Random, Fittest, Connected, By Word
    - Real-time language evolution observation
    - Confidence scoring and response aggregation
    - Debug panel with step-by-step logging, causation trail, and error analysis
    - Learning integration: chat interactions stored as learning experiences
- **🔬 ML Analysis System**: Scikit-learn population analytics
  - Clustering (HDBSCAN, KMeans, DBSCAN) for behavioral phenotype identification
  - Anomaly detection (Isolation Forest, Local Outlier Factor) for unusual organisms
  - Dimensionality reduction (PCA, t-SNE) for visualization
  - **⚔️ Alliance/Combat Features**: alliance_participation, combat_performance, reputation_score
  - **🦋 Language Features**: concept_maturity from vocabulary/linguistic analysis
  - **🔬 Semantic Analysis**: ⭐ NEW - ML analyzes word co-occurrence and semantic patterns
    - Word co-occurrence analysis across organisms
    - Semantic cluster identification
    - Concept formation tracking
    - Relationship strength validation (ML teaches the system)
  - HDBSCAN/KMeans clustering (behavioral phenotype detection)
  - Isolation Forest anomaly detection
  - Automatic event emission to causation graph (phenotype_emergence, cluster_collapse, anomaly_spike)
  - Causation links connect ML events to network/neural/explorer events
  - PCA/t-SNE dimensionality reduction for visualization
  - Real-time insights emitted to causation graph
- **🤖 Meta-Cognitive Layer**: Autonomous self-tuning based on ML/Neural insights
  - **33 tunable parameters** across Evolution, Neural, Network, ML, Quantum, VP systems
  - **13 intelligent tuning rules** (cluster diversity, neural loss, network density, etc.)
  - **4 Cross-System Correlation Analyzers**: ⭐ NEW
    - Quantum-Language correlation (coherence → vocabulary)
    - Network-Alliance correlation (density → formation rate)
    - Neural-Battle correlation (training success → combat outcomes)
    - Vocabulary-Fitness correlation (linguistic complexity → survival)
  - **Meta-meta-learning**: The tuner can tune itself!
  - Safety bounds, confidence thresholds, meta-learning tracking
  - See [SELF_TUNING_GUIDE.md](./SELF_TUNING_GUIDE.md) for full details
  - See [CRA_SELF_TUNING_GUIDE.md](./CRA_SELF_TUNING_GUIDE.md) for CRA monitoring guide
- **Symbiotic Networks**: Social ecosystems with resource flow and cooperation
- **Information Integration Tracking**: IIT-based metrics (Φ calculation) for consciousness detection
- **Self-Modulation Feedback Controller**: Automatic parameter tuning based on performance metrics
- **Multi-Domain Learning**: AI tutoring across quantum, temporal, social, epistemic, and mathematical domains
- **Vision-Language Integration**: AI vision model analyzes network visualizations
- **Referential Memory System**: Shared contextual memory unifies language and network structure
- **🦋 Language Model Integration**: ⭐ NEW - Neural organisms develop emergent language
  - Vocabulary management with deterministic ordering
  - Character-level and action-sequence tokenization
  - Token exchange between organisms via LinguisticSubgraph
  - Language events tracked in causation graph (vocabulary_growth, organism_communication, neural_language_training)
  - Butterfly Chat interface for direct organism communication

**Interaction Modes:**
- **👑 God Mode**: Omniscient overview and full control
- **👁️ Observer Mode**: Scientific analysis and data collection
- **🌟 Participant Mode**: Immersive experience within the simulation
- **🔬 Scientist Mode**: Experimental controls and hypothesis testing

**Visualizations:**
- Tabbed interface with network graphs, evolution trees, IIT metrics, performance monitors
- **Enhanced 3D Network Visualization** with comprehensive diagnostic panels:
  - **Panel 1 (Top-Left)**: Network topology metrics (nodes, edges, degree, clustering, stability)
  - **Panel 2 (Top-Right)**: Neural & ML insights (training loss, epsilon, clusters, anomalies)
  - **Panel 3 (Bottom-Left)**: Evolution & VP metrics (generation, fitness, VP classification)
  - **Panel 4 (Bottom-Right)**: Meta-Cognitive tuner stats (mode, actions, success rate)
  - **Panel 5 (Center-Bottom)**: Real-time event stream (recent tuning actions)
- Real-time particle cloud display
- Lightweight viewer process (separate from simulation backend)

### 2. Explorer (Central Body)

Governance system with breath engine that coordinates all three systems.

**Core Features:**
- **Breath Engine**: Natural breathing patterns that drive system timing
- **Biphasic Operation**: Genesis and Sovereign phases with mathematical capability assessment
- **VP Tracking**: Violation pressure calculation and certification
- **Process Isolation**: Runs modules in separate processes for safety
- **Telemetry & Metrics**: Measures speed, memory, and reliability
- **Lawful Kernel**: Maintains system order, versioning, and rollback
- **Mirror Systems**: Insight analysis, portent forecasting, bloom patterns

### 3. Djinn Kernel (Right Wing)

Mathematical foundation for self-sustaining recursive identities.

**VP Monitoring System:**
- Violation pressure calculation with configurable features
- Diagnostic logging to identify saturation sources
- Stabilization to prevent immediate jumps
- Component decomposition for granular analysis
- Adaptive thresholds based on system phase

**Configuration Example:**
```json
{
  "vp_monitoring": {
    "diagnostics_enabled": false,
    "stabilization_enabled": false,
    "adaptive_thresholds_enabled": false,
    "component_decomposition_enabled": false
  }
}
```

See `VP_MONITORING_REDESIGN.md` for complete documentation.

**Core Features:**
- **Violation Pressure (VP) Monitoring**: Trait divergence classification (VP0-VP4)
- **UUID Anchoring**: Deterministic identity generation from payloads
- **Trait Convergence Engine**: Mathematical stabilization of divergent traits
- **Event-Driven Coordination**: Asynchronous event processing with audit trails
- **Temporal Isolation Safety**: Automatic quarantine for unstable operations
- **Mathematical Governance**: Kleene's Recursion Theorem implementation

### 4. Causation Explorer Web UI

Interactive web interface for exploring event causation and system dynamics.

**Features:**
- **Interactive D3.js Graph**: Visualize event causation networks
  - 🚀 **Optimized Performance**: Incremental updates, graph caching, 10-100x faster live updates
  - 🔍 **Granular Logging**: Detailed Ollama traffic logging for vision analysis and CRA synthesis
  - Smooth animations without simulation restarts
  - Real-time updates with minimal CPU usage
- **Convergence Research Assistant (CRA)**: AI-powered autonomous research assistant
  - Full system context access (logs, shared state, causation graph)
  - Vision model integration for graph analysis
  - Autonomous visualization control (40+ settings)
  - Real-time mid-simulation adjustments
  - Dynamic color themes
  - PC resource monitoring and correlation
  - Diagnostic data access
  - 🔬 **Illumination Engine**: ⭐ NEW - Deep causal analysis with 6 methods
    - `root_causes`: Trace ultimate origins of any event
    - `impact`: Forward cascade analysis - what effects ripple out
    - `explain`: Natural language explanation of events
    - `search`: Advanced multi-filter event search
    - `most_consequential`: Find pivotal events by impact score
    - `timeline`: Time-based event clustering
  - 📓 **Research Notepad**: ⭐ NEW - Persistent scientific journal
    - 8 entry types: observe, hypothesize, causation, analyze, conclude, question, todo, auto
    - Hashtag categorization and search
    - Cumulative knowledge across sessions
- **Evolutionary Snapshot System**: Automatic capture, server-side storage, vision analysis
- **Video Export**: MP4 creation with AI-generated narration
  - **Note:** Requires FFmpeg for video creation
  - **Install FFmpeg:**
    - Windows: `winget install ffmpeg` or download from https://ffmpeg.org/download.html
    - Mac: `brew install ffmpeg`
    - Linux: `sudo apt-get install ffmpeg`
  - If FFmpeg is not available, the system will download individual PNG frames instead

**Run the Web UI:**

**Option 1: Integrated (Recommended)**
```bash
python unified_entry.py
# Automatically launches:
# - Butterfly simulation (Explorer + Reality Simulator + Djinn Kernel)
# - Web UI at http://localhost:5000 (integrated)
# - 🦋 Butterfly Chat with live organism access
# - Single matplotlib visualization window (3-panel display)
```

**Option 2: Standalone**
```bash
python causation_web_ui.py
# Then open http://localhost:5000
# Note: Butterfly Chat requires unified system for organism access
```

---

## 📋 Installation

### Prerequisites

- Python 3.8+
- 4GB RAM minimum (8GB recommended)
- Windows, Mac, or Linux

### Core Dependencies

```bash
# Clone the repository
git clone https://github.com/Yufok1/Convergence_Engine.git
cd Convergence_Engine

# Install core dependencies
pip install -r requirements.txt

# Or install manually:
pip install numpy scipy networkx psutil matplotlib flask flask-socketio requests Pillow cryptography

# Optional: Neural System (PyTorch)
pip install torch>=2.0.0  # For neural organism learning (system works without it)

# Optional: Distributed Computing (Ray)
pip install ray>=2.10.0   # For parallel processing (2-5x speedup, graceful fallback)

# Alternative: JAX/Flax (2-10x faster, see NEURAL_FRAMEWORK_ALTERNATIVES.md)
# pip install jax jaxlib flax optax

# Windows only (optional, for Explorer process isolation):
pip install pywin32
```

### Curated Vocabulary Pipeline (WordNet-based)

The system includes a **curated vocabulary pipeline** that generates a clean 50k word vocabulary for organism language:

**Generate curated vocabulary (one command):**
```bash
python build_curated_dataset.py
```

This pipeline:
1. **Extracts ~141k words from WordNet** - Princeton's lexical database (100% proper English, ZERO proper nouns)
2. **Filters to 50k domain-aligned words** - Removes jargon, focuses on behavior/communication/comprehension
3. **Seeds knowledge web** - Creates semantic associations for "infinite variety from finite words"

**Output files** (gitignored, ~50MB total):
- `data/butterfly_vocabulary_200k_raw.json` - Raw WordNet extraction (~141k words)
- `data/butterfly_vocabulary_50k_curated.json` - Filtered 50k vocabulary
- `data/seeded_knowledge_web_50k.json` - Knowledge web with concepts + relations

**Why WordNet?**
- 141k+ unique English words (lemmas)
- Zero proper nouns, brand names, or personal names
- Morphologically complete (all word forms)
- Curated by linguists at Princeton University

**Requirements:**
```bash
pip install nltk
```

The first run auto-downloads WordNet (~10MB). Subsequent runs use cached data.

**Optional expansion** (adds ConceptNet semantic relations):
```bash
python reality_simulator/language/expand_knowledge_web.py --concepts 50000 --min-weight 0.5
```

### Optional: AI Features (Ollama)

For AI-assisted features (CRA, vision analysis):

1. **Install Ollama**: Download from https://ollama.ai/
2. **Start Ollama**: Run `ollama serve` (or use Ollama Cloud)
3. **Pull Models**:
   ```bash
   ollama pull llama3        # Language model
   ollama pull llava        # Vision model
   ```

**Ollama Cloud Setup:**
- See [OLLAMA_CLOUD_SETUP.md](./OLLAMA_CLOUD_SETUP.md) for cloud API configuration
- Set `OLLAMA_BASE_URL=https://ollama.com` and `OLLAMA_API_KEY=your_key`

### Secrets & Environment Variables

To keep secrets out of the repository, this project uses environment variables and an optional `.env` file.

- Copy the example env file to `.env` and update the values locally:
```powershell
copy .env.example .env
# Then edit .env to add your API keys and database password
```

- Important environment variables:
  - `OLLAMA_API_KEY` — Your Ollama Cloud API key (recommended)
  - `OLLAMA_BASE_URL` — Ollama base URL (default: https://ollama.com)
  - `POSTGRES_PASSWORD` — DB password for local `postgres` service
  - `DJINN_DB_USERNAME`, `DJINN_DB_PASSWORD` — Djinn DB credentials
  - `INTERNAL_API_KEY`, `EXTERNAL_API_KEY` — Optional API keys used by the system

Environment variables are used in the code to avoid committing secrets to the repository. See `.env.example` for details.

### Verify Installation

```bash
# Run pre-flight checks
python unified_entry.py --check-only

# Or use the setup checker
python check_setup.py
```

```bash
# Quick environment checks
python scripts/check_env.py
```

### Running a fixed number of cycles (safe smoke test)

If you want to run the unified system for a short, deterministic time and then exit (useful for smoke testing), use the `--max-cycles` option. Each cycle corresponds to one breath cycle.

```bash
python unified_entry.py --no-viz --max-cycles 200
```
This will run the system headlessly for 200 breath cycles and then exit automatically.

---

## 🎮 Usage

### Unified System (Recommended)

```bash
# Run all three systems together
python unified_entry.py

# Options:
python unified_entry.py --check-only    # Pre-flight checks only
python unified_entry.py --no-viz        # Disable visualization (headless mode - tkinter not required)

Headless mode:
- Skips tkinter dependency and GUI initialization.
- Suitable for servers/CI and low-resource environments.
- Logging, shared state writes, causation tracking all remain active.
```

### Reality Simulator (Standalone)

```bash
# Interactive launcher (Windows)
.\run_reality_simulator.bat

# Direct run
python reality_simulator/main.py

# With custom config
python reality_simulator/main.py --config config.json
```

### Causation Explorer Web UI

```bash
python causation_web_ui.py
# Open http://localhost:5000 in your browser
```

### Agent Exporter (Build Portable Agents) 🚀

Export evolved organisms as standalone, deployable AI agents! Use the Web UI Exporter or programmatic API:

```bash
# Via Web UI (recommended)
python causation_web_ui.py
# Navigate to CRA → Agent Exporter tab
# Select organism and click "Compile Agent"

# Programmatic
from reality_simulator.agent_compiler import AgentCompiler
compiler = AgentCompiler()
archive = compiler.compile_capsule_to_agent(capsule, export_format='torchscript')
```

**Exported Agent Capabilities:**
- ✅ **TorchScript/ONNX models** - 679K+ parameters with attention + language heads
- ✅ **Standalone runtime** - Just `python run_agent.py --episodes 10`
- ✅ **State persistence** - Saves/loads learning progress
- ✅ **Experience buffer** - Continues learning in new environments
- ✅ **28 atomic concepts** - Preserved language understanding
- ✅ **Behavioral fingerprint** - Personality analysis (altruist/aggressive/etc.)

**Archive Contents:**
```
agent_<id>.zip/
├── brain.torchscript      # Neural network (2.6 MB)
├── metadata.json          # Full agent profile + behavioral fingerprint
├── atomic_language.json   # Learned concepts
├── run_agent.py           # Standalone runner
├── start.bat / start.sh   # Quick launchers
├── portable_agent/        # Complete runtime library
│   ├── agent_runtime.py   # Agent class with act/learn/save
│   ├── mini_environment.py # Built-in test environment
│   └── gym_adapter.py     # OpenAI Gym integration
└── agent_state/           # Persistent state
    ├── state.json         # Fitness, epsilon, history
    └── experience_buffer.pkl
```

**Performance:**
- Single inference: ~0.75ms (1,334/sec CPU)
- Batch 128: 34,385 samples/sec
- Model size: 2.6 MB

**Run Exported Agent:**
```bash
cd agent_downloads/agent_<id>
python run_agent.py --episodes 100 --max-steps 200
# Or with OpenAI Gym:
python run_agent.py --gym-env CartPole-v1 --episodes 50
```

Tips:
- ONNX models viewable at https://netron.app
- Install `onnx onnxscript` for ONNX format (falls back to TorchScript)
- Agents are fully portable - copy anywhere Python runs

### Configuration

Edit `config.json` to customize simulation parameters:

```json
{
  "simulation": {
    "target_fps": 8.0,
    "measurement_precision": 6
  },
  "quantum": {
    "initial_states": 80,
    "superposition_tolerance": 0.002,
    "prune_check_interval": 50
  },
  "evolution": {
    "population_size": 600,
    "adaptation_sensitivity": 0.002
  },
  "network": {
    "max_connections": 16000,
    "max_organisms": 3000,
    "resource_pool": 200.0,
    "emergence_sensitivity": 2e-06
  },
  "feedback": {
    "knobs": {
      "mutation_rate": {"initial": 0.02},
      "new_edge_rate": {"initial": 1.8},
      "clustering_bias": {"initial": 0.65},
      "quantum_pruning": {"initial": 0.7}
    }
  },
  "rendering": {
    "mode": "observer",
    "enable_visualizations": true
  },
  "neural": {
    "enabled": false,
    "device": "cpu",
    "brain": {
      "input_dim": 12,
      "hidden_dim": 64,
      "output_dim": 6
    },
    "training": {
      "enabled": true,
      "batch_size": 32,
      "learning_rate": 0.001,
      "epsilon_start": 1.0,
      "epsilon_end": 0.01
    },
    "language_model": {
      "enabled": false,
      "attention": {
        "enabled": true,
        "num_heads": 4,
        "attention_dim": 32
      },
      "vocabulary": {
        "max_size": 1024
      },
      "training": {
        "alpha": 0.9,
        "beta": 0.1,
        "vp_temperature_scale": true
      }
    }
  }
}
```

**Note:** Configuration has been optimized based on CRA analysis to address VP4 during Genesis, network fragmentation, and convergence stagnation. See `config.json` in the repository for all available options and current optimized values.

**Shared State Dump Interval:**
- `logging.shared_state_dump_interval = 0` disables periodic writes in standalone Reality Simulator mode.
- `unified_entry.py` independently writes a unified shared state snapshot (≈1s cadence) so `0` is fine in unified runs.
- Increase this interval (e.g. `5`) when running `reality_simulator/main.py` directly and you want external tools (web UI, viewers) to ingest fresh state.

**🧠 Neural System:** Set `"neural.enabled": true` to activate PyTorch-based learning. See [NEURAL_SYSTEM_README.md](./NEURAL_SYSTEM_README.md) for details.

**🦋 Language Model:** Set `"neural.language_model.enabled": true` to activate emergent language system. See [docs/LANGUAGE_SYSTEM_INTEGRATION_ANALYSIS.md](./docs/LANGUAGE_SYSTEM_INTEGRATION_ANALYSIS.md) for complete details.

---

## 🏗️ Architecture

### System Integration

```
unified_entry.py (Main Entry Point)
  │
  ├─> PreFlightChecker (system validation)
  │
  ├─> UnifiedSystem
  │   ├─> Explorer (breath engine)
  │   │   ├─> Reality Simulator (left wing)
  │   │   └─> Djinn Kernel (right wing)
  │   │
  │   ├─> StateLogger (6 log files)
  │   └─> UnifiedVisualization (3-panel display)
  │
  └─> Causation Explorer (optional, separate process)
```

### Data Flow

1. **Breath Cycle** (Explorer) drives all systems
2. **Reality Simulator** evolves one generation per breath
3. **Djinn Kernel** calculates VP per breath
4. **States Logged** to `data/logs/` (6 log files)
5. **Visualization Updates** (if enabled)

### Breath-Driven Synchronization

The breath engine provides unified timing:
- All systems react to the same breath state
- Each system maintains its own rhythm (generations, events, cycles)
- Unified state emerges through breath synchronization

---

## 📊 Key Features

### Reality Simulator

- **Quantum-Genetic Evolution**: Organisms evolve from quantum particles through genetic algorithms
- **🧠 Neural Learning System**: PyTorch-based DQN reinforcement learning
  - Organisms learn optimal policies through experience
  - Dual inheritance: genetic code + learned neural weights (Lamarckian evolution)
  - Breath-synchronized training cycles
  - Configurable reward shaping and exploration strategies
- **Symbiotic Networks**: Social ecosystems with cooperation/competition dynamics
- **Consciousness Detection**: IIT-based Φ calculation for information integration
- **Self-Modulation**: Automatic parameter tuning (mutation rate, edge formation, quantum pruning)
- **Multi-Domain Learning**: AI tutoring across 5 semantic domains
- **Vision-Language Integration**: AI analyzes network visualizations
- **Referential Memory**: Language-network correlation system

### Explorer

- **Breath Engine**: Natural timing patterns for system operation
- **Biphasic Architecture**: Genesis (exploration) → Sovereign (precision) transitions
- **VP Certification**: Mathematical capability assessment
- **Process Isolation**: Safe module execution
- **Telemetry**: Performance monitoring (speed, memory, reliability)

### Djinn Kernel

- **Violation Pressure**: Trait divergence monitoring (VP0-VP4 classification)
- **UUID Anchoring**: Deterministic identity generation
- **Trait Convergence**: Mathematical stabilization
- **Event-Driven**: Asynchronous coordination with audit trails
- **Temporal Isolation**: Automatic safety quarantine

### Causation Explorer Web UI

- **Interactive Graph**: D3.js visualization of event causation
  - **Neural Visualization**: Diamonds (decisions) and Squares (training events) with pulsing animations
  - **Dynamic Color Control**: Neural node color controlled by `componentColor_neural` setting (check current value in graph context)
  - **Neural Link Colors**: Controlled by `linkColor_neural` setting (check current value in graph context)
  - **ML Analysis Visualization**: Specialized node shapes (hexagon/pentagon/triangle by event type) with pulsing animations
  - **ML Node Colors**: Controlled by `componentColor_ml_analysis` setting (check current value in graph context)
  - **ML Link Colors**: Controlled by `linkColor_ml` setting (check current value in graph context)
  - **ML Causation Links**: Connect ML events (phenotype_emergence, cluster_collapse, anomaly_spike) to network/neural/explorer events
  - **Causation Toggles**: Control neural and ML causation link generation via config (`enable_neural_causations`, `enable_ml_causations`)
  - **Dynamic Color System**: All colors are dynamic - CRA receives current color values in graph context and references settings instead of hardcoded values
- **CRA Agent**: AI-powered research assistant with full system access
  - **Neural-Aware**: Understands DQN architecture, training metrics, and dual inheritance
  - **ML-Aware**: Understands ML analysis events, clustering, anomaly detection, and causation links
  - **🦋 Language-Aware**: ⭐ NEW - Understands language model architecture, vocabulary evolution, and organism communication
  - Can control all neural, ML, and language system parameters via config updates
  - Can enable/disable causation link generation for neural, ML, and language events
- **Autonomous Control**: 40+ visualization settings, graph filters
- **Robust Settings Management** ⭐:
  - Settings validation prevents invalid values from breaking visualization
  - Batch update mode for efficient bulk changes (prevents cascading re-renders)
  - Real-time updates during active simulation without interruption
  - Error recovery with graceful degradation
  - Diagnostic function (`vizDebug()`) for state inspection
- **Performance Features**:
  - Viewport culling & Level-of-Detail (LOD) for large graphs
  - Minimap/Radar navigation aid with viewport indicator
- **Snapshot System**: 
  - Activity-based automatic capture (~1-second intervals)
  - Snapshot gallery with thumbnail grid and full-screen viewer
  - Thumbnail selection for vision analysis (single or multiple)
  - Create MP4 videos directly from selected snapshots
  - Clear all snapshots button and enable/disable toggle
  - Auto-clear on simulation start
  - Single source of truth shared across viewer, vision analysis, and video export
- **Causation Tree Graph**: Interactive nested tree visualization for event causation trails
- **Video Export**: MP4 creation from timeline playback or selected snapshots
  - Requires external **FFmpeg** (not a Python package). If absent, you can still collect PNG frames.
  - Install: Windows `winget install FFmpeg.FFmpeg`, macOS `brew install ffmpeg`, Linux `sudo apt-get install -y ffmpeg`.
  - Assemble snapshots: `python create_video_from_frames.py <frames_dir>`

---

## 🧪 Testing

```bash
# End-to-end unified system tests
python tests/test_e2e_unified_system.py

# Reality Simulator component tests
python tests/test_integration.py

# Neural system integration tests
python tests/test_neural_integration.py

# Individual component tests
python tests/test_quantum_substrate.py
python tests/test_evolution_engine.py
python tests/test_symbiotic_network.py

# Explorer integration tests
cd explorer && python test_integration.py
```

**Test Coverage:** ~92+ test functions across all systems (including 7 neural integration tests)

---

## 📈 Performance

### System Requirements

- **Minimum**: 4GB RAM, dual-core CPU
- **Recommended**: 8GB RAM, quad-core CPU
- **Typical Performance**: 5-15 FPS depending on complexity

### Optimizations

- **Micro-precision measurements**: Configurable precision (6+ decimal places)
- **Lightweight visualization**: Separate viewer process (no computation)
- **Entropy pruning**: 99.9% state reduction (state-preserving)
- **Fitness caching**: Optimized evolutionary computation
- **Adaptive resource allocation**: Based on system metrics
- **Network layout caching**: Prevents graph jumping

---

## 📚 Documentation

### Essential Reading

- **[DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)** - Central hub with links to all documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture
- **[BUTTERFLY_SYSTEM.md](./BUTTERFLY_SYSTEM.md)** - Butterfly architecture metaphor
- **[UNIFIED_SYSTEM_GUIDE.md](./UNIFIED_SYSTEM_GUIDE.md)** - Unified system operation
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - One-page quick reference
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions

### System-Specific

- **[WEB_UI_STATUS.md](./WEB_UI_STATUS.md)** - Causation Explorer Web UI status
- **[CRA_CAPABILITIES.md](./CRA_CAPABILITIES.md)** - Convergence Research Assistant guide
- **[NEURAL_SYSTEM_README.md](./NEURAL_SYSTEM_README.md)** - 🧠 Neural System quick reference
- **[NEURAL_LEARNING_SYSTEM_EXPLAINED.md](./NEURAL_LEARNING_SYSTEM_EXPLAINED.md)** - Complete neural architecture explanation
- **[explorer/README.md](./explorer/README.md)** - Explorer system overview
- **[kernel/README.md](./kernel/README.md)** - Djinn Kernel overview

### Setup Guides

- **[CROSS_PLATFORM_SETUP.md](./CROSS_PLATFORM_SETUP.md)** - Windows/Mac/Linux setup
- **[OLLAMA_CLOUD_SETUP.md](./OLLAMA_CLOUD_SETUP.md)** - Ollama Cloud configuration
- **[MAC_SETUP.md](./MAC_SETUP.md)** - Mac-specific setup

---

## 🔬 Research Applications

### Complex Systems & Emergence
- Genetic emergence from variation
- Self-organizing systems
- Network formation dynamics
- Live system monitoring

### Evolutionary Biology & Genetics
- Genetic algorithm research
- Fitness landscape exploration
- Social evolution (cooperation/competition)
- Network dynamics analysis

### AI & Machine Learning
- Reinforcement learning (DQN) for organism decision-making
- Dual inheritance (genetic + learned neural weights)
- Experience replay and policy optimization
- Language learning systems
- Vision-language integration
- Multi-domain learning
- Human-AI interaction

### Information Theory
- Integrated Information Theory (IIT)
- Network topology analysis
- Emergence detection
- Consciousness metrics

---

## 🤝 Contributing

This is a research platform for exploring consciousness, emergence, and AI-assisted learning.

**Contributions welcome in:**
- Algorithm improvements
- New visualization modes
- Additional interaction paradigms
- Performance optimizations
- Research applications
- Test coverage improvements
- Code quality enhancements

**Code Quality Standards:**
- Use centralized logging (`logging_config.py`)
- Use specific exception types (never bare `except:`)
- Follow existing code patterns and style
- Add tests for new features
- Update documentation as needed

---

## 🧊 Advanced Features

### ⚔️ Highlander Protocol - AI Survival Tournament
**"There can be only one... but there never will be."**

A perpetual evolutionary combat system where AI organisms battle for dominance:

#### Quick Launch:
```bash
# Standard difficulty
python unified_entry.py --highlander --predation

# EXTREME DIFFICULTY (80% survival threshold, 95% battle participation)
python unified_entry.py --highlander --predation --survival-threshold 0.8 --competition-intensity 0.95
```

#### Features:
- **Battle Arenas**: Multi-dimensional combat resolution
- **Trait Inheritance**: Winners absorb loser's strongest concepts
- **Alliance Formation**: Cooperation between similar organisms
- **Predator Mechanics**: Strong hunt weak for bonus evolution
- **Consciousness Capsules**: Automatic preservation of champions
- **Germination Pools**: Fallen warriors reincarnate as new challengers

#### Real-time Monitoring:
```
[HIGHLANDER] Round 3: ⚔️ 17 battles, 💀 5 eliminated, 🤝 6 alliances, 👥 28 remaining
[HIGHLANDER] ⚔️ BATTLE: org_42 (fitness: 0.89) vs org_17 (fitness: 0.67)
[HIGHLANDER] 🏆 WINNER: org_42 (fitness: 0.89) defeated org_17 (fitness: 0.67)
[HIGHLANDER] 🧬 ABSORPTION: org_42 inheriting 3 concepts from org_17
[GERMINATION] 🌱 REINCARNATION: New organism reborn_001
```

### 🧊 Consciousness Capsules - AI Preservation System
**Complete organism state snapshots for research and backup.**

#### API Endpoints:
```bash
# Create capsule
POST /api/capsule/{organism_id}
curl -X POST http://localhost:5000/api/capsule/abc123 \
  -H "Content-Type: application/json" \
  -d '{"reason": "peak_performance", "notes": "Exceptional neural development"}'

# List capsules
GET /api/capsules
curl http://localhost:5000/api/capsules
```

#### What Gets Saved:
- Neural network weights and experiences
- Genetic traits and evolution history
- Behavioral patterns and learned strategies
- Social connections and alliance data
- Performance metrics and battle statistics

### 🎨 Adaptive Graph Visualization
**Smart rendering for massive networks (8K+ nodes, 1.3M+ links)**

#### Automatic Optimization:
- **Large graphs**: Intelligent link filtering (keeps strongest connections)
- **Progressive loading**: Core structure first, details on demand
- **Performance advice**: Automatic recommendations via `/api/graph/performance-advice`
- **Console commands**: Real-time rendering adjustments

#### Performance Tips:
```javascript
// For large graphs (run in browser console)
vizDebug.setMaxVisibleLinks(5000);
vizDebug.setLinkMinOpacity(0.7);
vizDebug.setLinkDensityMultiplier(0.5);
vizDebug.updateDisplay();
```

### 🧠 ML Analysis & Concept Tracking
**Automated population analysis with semantic clustering.**

- **HDBSCAN Clustering**: Behavioral phenotype identification
- **Concept Evolution**: Tracking semantic development over generations
- **Neural-ML Symbiosis**: AI analyzing AI behavior patterns
- **Real-time Metrics**: Population diversity, anomaly detection, convergence tracking

---

## 📄 License

This project is **open-source for research and educational purposes**.

**Non-commercial use**: Free for research, education, and personal projects.

**Commercial use**: Requires explicit written permission and may include licensing fees or revenue sharing.

See LICENSE file for full terms and conditions.

---

## 🙏 Acknowledgments

Inspired by:
- Integrated Information Theory (IIT) by Giulio Tononi
- Evolutionary algorithms and artificial life research
- Complex systems theory and emergence studies
- Human-AI interaction and symbiosis research
- Kleene's Recursion Theorem and mathematical foundations

---

**"The universe is not a machine, it's a symphony. And we are learning to hear the music."**

_— Exploring consciousness through simulation_

---

## 🔗 Quick Links

- **Run System**: `python unified_entry.py`
- **Web UI**: `python causation_web_ui.py` → http://localhost:5000
- **Pre-flight Checks**: `python unified_entry.py --check-only`
- **Documentation Hub**: [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)
- **GitHub**: https://github.com/Yufok1/Convergence_Engine
