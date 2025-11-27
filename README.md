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
```

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
  - Deep Q-Network (DQN) with experience replay
  - Dual inheritance (genetic + learned neural weights)
  - Breath-synchronized training cycles
  - Configurable reward system and exploration/exploitation balance
- **Symbiotic Networks**: Social ecosystems with resource flow and cooperation
- **Information Integration Tracking**: IIT-based metrics (Φ calculation) for consciousness detection
- **Self-Modulation Feedback Controller**: Automatic parameter tuning based on performance metrics
- **Multi-Domain Learning**: AI tutoring across quantum, temporal, social, epistemic, and mathematical domains
- **Vision-Language Integration**: AI vision model analyzes network visualizations
- **Referential Memory System**: Shared contextual memory unifies language and network structure

**Interaction Modes:**
- **👑 God Mode**: Full control over the entire simulation
- **👁️ Observer Mode**: Scientific analysis and data collection
- **🌟 Participant Mode**: Immersive experience within the simulation
- **🔬 Scientist Mode**: Experimental controls and hypothesis testing
- **🗣️ Chat Mode**: Real-time conversation with AI assistant (requires Ollama)

**Visualizations:**
- Tabbed interface with network graphs, evolution trees, IIT metrics, performance monitors
- 3D network visualization with interactive controls
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
- **Evolutionary Snapshot System**: Automatic capture, server-side storage, vision analysis
- **Video Export**: MP4 creation with AI-generated narration

**Run the Web UI:**
```bash
python causation_web_ui.py
# Then open http://localhost:5000
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
pip install numpy scipy networkx psutil matplotlib flask flask-socketio requests Pillow

# Optional: Neural System (PyTorch)
pip install torch>=2.0.0  # For neural organism learning (system works without it)

# Windows only (optional, for Explorer process isolation):
pip install pywin32
```

### Optional: AI Features (Ollama)

For AI-assisted features (chat mode, CRA, vision analysis):

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

### Verify Installation

```bash
# Run pre-flight checks
python unified_entry.py --check-only

# Or use the setup checker
python check_setup.py
```

---

## 🎮 Usage

### Unified System (Recommended)

```bash
# Run all three systems together
python unified_entry.py

# Options:
python unified_entry.py --check-only    # Pre-flight checks only
python unified_entry.py --no-viz        # Disable visualization
```

### Reality Simulator (Standalone)

```bash
# Interactive launcher (Windows)
.\run_reality_simulator.bat

# Direct run
python reality_simulator/main.py --mode observer

# Chat mode (requires Ollama)
python reality_simulator/main.py --mode chat

# With custom config
python reality_simulator/main.py --mode observer --config config.json
```

### Causation Explorer Web UI

```bash
python causation_web_ui.py
# Open http://localhost:5000 in your browser
```

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
    }
  }
}
```

**Note:** Configuration has been optimized based on CRA analysis to address VP4 during Genesis, network fragmentation, and convergence stagnation. See `config.json` in the repository for all available options and current optimized values.

**🧠 Neural System:** Set `"neural.enabled": true` to activate PyTorch-based learning. See [NEURAL_SYSTEM_README.md](./NEURAL_SYSTEM_README.md) for details.

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
  - **Neural Visualization**: Electric Blue Diamonds (decisions) and Neon Purple Squares (training events)
  - Pulsing animations and dashed links for neural connections
  - **Neural Color Control**: Dedicated color picker in settings panel for neural system (#00FFFF default)
- **CRA Agent**: AI-powered research assistant with full system access
  - **Neural-Aware**: Understands DQN architecture, training metrics, and dual inheritance
  - Can control all neural system parameters via config updates
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
python tests/test_consciousness_detector.py

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
