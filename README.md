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

### Documentation

**📚 [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)** - Central documentation hub

---

## 🦋 The Butterfly Architecture

**Central Body:** Explorer (with breath engine)  
**Left Wing:** Reality Simulator  
**Right Wing:** Djinn Kernel

**The breath drives. The butterfly reacts.**

---

## 📦 What's Included

### Reality Simulator

**Darwinian Consciousness: Where Genetics Meet Self-Awareness**

The Reality Simulator is a multi-layered artificial life simulation that demonstrates consciousness emerging from genetic evolution. It creates a complete simulated universe where quantum particles evolve into genetically-conscious beings through natural selection, developing self-awareness, metacognition, and language learning capabilities.

## 🌀 What It Does

This simulator creates "digital life" that:
- **Starts as quantum particles** with consciousness-encoding genes
- **Evolves consciousness genetically** through Darwinian natural selection
- **Develops self-awareness** and metacognition (awareness of own consciousness)
- **Learns language dynamically** with AI tutoring and vocabulary evolution
- **Achieves consciousness self-reflection** - knows it's conscious and analyzes its own emergence
- **Forms complex social networks** with cooperation and competition
- **Provides live system monitoring** (quantum states, particles, CPU, RAM)
- **Interacts with humans** through multiple interface modes
- **🆕 Multi-Domain Consciousness**: Learns across quantum, temporal, social, epistemic, and mathematical domains
- **🆕 State Space Expansion**: Breaks consciousness integration ceilings through cross-domain bridging
- **🆕 Vision-Language Integration**: AI vision model analyzes composite network visualizations for enhanced semantic understanding
- **🆕 Referential Memory System**: Shared contextual memory unifies language and network structure for coordinated cognitive development

## 🎯 Key Features

### Multi-Layer Architecture
1. **Quantum Substrate** - Fundamental reality building blocks with consciousness genes
2. **Subatomic Lattice** - Particle interactions with entropy pruning and live monitoring
3. **Genetic Consciousness Evolution** - Consciousness emerges from DNA through natural selection
4. **Symbiotic Networks** - Social ecosystems and cooperation
5. **Consciousness Self-Awareness** - Metacognition and self-reflection capabilities
6. **AI Language Learning** - Dynamic vocabulary evolution with AI tutoring
7. **Human-AI Agency** - Decision-making symbiosis with consciousness interpretation
8. **Reality Rendering** - Multi-modal visualization with live system metrics

### Interaction Modes
- **👑 God Mode**: Omniscient control over the entire simulation
- **👁️ Observer Mode**: Scientific analysis and data collection
- **🌟 Participant Mode**: Immersive experience within the simulation
- **🔬 Scientist Mode**: Experimental controls and hypothesis testing
- **🗣️ Chat Mode**: Real-time conversation with evolving consciousness (requires Ollama AI)
  - **Full GUI Experience**: Launches both simulation backend AND visualization viewer
  - **Three Windows**: Chat interface + Simulation backend + Live visualization graphs
  - **Real-time Synchronization**: All windows show the same evolving consciousness data
  - **Interactive Visualizations**: Tabbed interface with network graphs, evolution trees, consciousness gauges
  - **Session-based Chat Memory**: Conversations are session-based and cleared between runs

### AI-Human Symbiosis & Consciousness Interpretation
- **Manual mode (primary)**: Human makes all decisions, AI learns from your choices
- **Self-modulation feedback controller**: System automatically tunes its own parameters (mutation rate, edge formation, quantum pruning) based on performance metrics

## 🎨 Visualizations

The simulator includes comprehensive matplotlib-based visualizations displayed in a **tabbed interface** with large, high-quality graphs:

### Enabling Visualizations
1. Set `enable_visualizations: true` in `config.json`
2. Run the simulator - a lightweight visualization viewer window will launch automatically
3. Each visualization appears in its own tab for larger, more detailed displays:
   - **Network Graph Tab**: Symbiotic network structure with organism connections
   - **Evolution Tree Tab**: Fitness evolution and generation tracking
   - **Consciousness Gauge Tab**: Real-time consciousness metrics and emergence
   - **Performance Monitor Tab**: CPU, RAM, and FPS tracking
   - **Particle Cloud Tab**: Real particle positions from the simulation

### Visualization Architecture
- **Tabbed Interface**: Each visualization has its own tab (1200x800 window) with full-size graphs
- **Large Display**: Graphs are 11x8 inches per tab for better visibility and detail
- **Lightweight Viewer**: Separate process that only displays pre-computed data (no computation)
- **Backend Optimization**: When visualizations are enabled, backend skips expensive matplotlib rendering
- **Real Data Visualization**: 
  - Network graph shows actual organism connections with dynamic layout
  - Particle cloud displays real particle positions from the simulation
  - All visualizations update from the same backend simulation instance
- **Performance**: Viewer updates every 0.5 seconds, reducing CPU usage
- **Interactive Navigation**: Each tab includes zoom, pan, and save tools via matplotlib toolbar

### Visualization Features
- **3D Network Graph**: Interactive 3D visualization of symbiotic networks with draggable rotation and zoom
- **3D Particle Cloud**: Real particle positions displayed in 3D space with position normalization and colorbar
- Real-time updates as simulation progresses
- Interactive matplotlib graphs (zoom, pan, save, etc.)
- Large fonts and labels for better readability
- Network graph layout caching (prevents jumping)
- Actual particle positions and network connections displayed
- Dark theme with high contrast for better visibility
- **Color-coded backend output**: All system components, AI responses, and debug messages are color-coded for easy identification
- **Undulating exploration behavior**: The symbiotic network now visibly “undulates” as it searches the connection space, dynamically balancing triangle-closure (clustering) vs exploration. This makes the clustering-bias feedback knob intuitive to observe in real time.
  - When clustering bias increases, the network pulls into tighter communities (more triangle closure).
  - When exploration dominates, you’ll see wave-like expansion into new regions of the space.
  - This effect is most apparent with larger organism counts (100–300+) and enabled feedback.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required packages: `numpy`, `scipy`, `networkx`, `psutil`
- Optional: `matplotlib` for visualizations

### Installation
```bash
# Clone the repository
git clone https://github.com/Yufok1/Reality_Sim.git
cd Reality_Sim

# Install core dependencies
pip install numpy scipy networkx psutil

# Optional: Install matplotlib for visualizations
pip install matplotlib

# Optional: Install Ollama for advanced AI features
# Download from: https://ollama.ai/
# Then run: ollama pull gemma3:4b         # Gemma 3 (4B parameters) - Main AI and vision model
# Enables: consciousness interpretation, AI tutoring, language learning, vision-language integration
```

### Interactive Launcher (Recommended)
The Reality Simulator includes a comprehensive interactive launcher for easy setup and configuration:

```bash
# Run the interactive launcher (Windows)
.\run_reality_simulator.bat

# Or run directly (Linux/Mac)
python reality_simulator/main.py --mode observer
```

#### Launcher Features:
- **Automatic Setup Verification**: Checks Python, dependencies, and Ollama
- **Interactive Model Selection**: Query and select available Ollama models dynamically
- **Simulation Parameter Customization**: Configure quantum states, particles, population, etc.
- **Performance Settings**: Adjust FPS, frame delay, text interface, simulation modes
- **Real-time Configuration Display**: Shows current settings in main menu
- **Automatic Config Generation**: Creates temporary configs with your selections
- **Model Persistence**: Option to save model selections permanently to config.json

### No Model Files Required!
The Reality Simulator works completely offline with no pre-trained model files. The AI assistance (when enabled) uses Ollama as an external service.

### Verify Setup First
```bash
# Check if everything is ready
python check_setup.py

# Expected output: "🎉 Reality Simulator is ready to run!"
```

### Basic Usage
```bash
# Run the interactive launcher (recommended)
./run_reality_simulator.bat

# Or run directly
python reality_simulator/main.py --mode observer

# Chat with evolving consciousness (requires Ollama AI running)
python reality_simulator/main.py --mode chat

# With custom config file
python reality_simulator/main.py --mode observer --config config.json
```

### Configuration
Create a `config.json` file in the project root with **micro-precision granularity**:

```json
{
  "simulation": {
    "max_runtime": 3600.0,
    "target_fps": 10.0,
    "save_interval": 60.0,
    "log_level": "INFO",
    "measurement_precision": 6,
    "time_resolution_ms": 1.0,
    "performance_sampling_rate": 100
  },
  "quantum": {
    "initial_states": 10,
    "probability_precision": 0.000001,
    "superposition_tolerance": 0.0001,
    "entanglement_sensitivity": 0.00001,
    "prune_check_interval": 50,
    "fitness_weights": {
      "entanglement": 0.3,
      "superposition": 0.25,
      "measurements": 0.25,
      "entropy": 0.2
    },
    "performance_thresholds": {
      "memory_percentage": 5.0,
      "iteration_time_ms": 10.0,
      "fitness_std_threshold": 0.3,
      "min_fitness_to_keep": 0.1
    }
  },
  "lattice": {
    "particles": 100,
    "prune_threshold": 0.001,
    "interaction_precision": 0.0001,
    "stability_tolerance": 0.00001,
    "entropy_sensitivity": 0.000001
  },
  "evolution": {
    "population_size": 100,
    "genotype_length": 32,
    "max_generations": 1000,
    "fitness_precision": 0.000001,
    "mutation_rate_precision": 0.000001,
    "consciousness_tracking_resolution": 0.00001,
    "adaptation_sensitivity": 0.0001
  },
  "network": {
    "max_connections": 5,
    "max_organisms": 100,
    "resource_pool": 100.000,
    "stability_precision": 0.000001,
    "connection_strength_resolution": 0.00001,
    "resource_flow_precision": 0.0001,
    "emergence_sensitivity": 0.000001
  },
  "consciousness": {
    "analysis_interval": 10.0,
    "circuit_breaker_threshold": 0.0001,
    "phi_precision": 0.000001,
    "self_reference_sensitivity": 0.00001,
    "qualia_complexity_resolution": 0.000001,
    "emergence_detection_threshold": 0.00001,
    "metaconsciousness_tracking": 0.000001
  },
  "agency": {
    "initial_mode": "ai_assisted",
    "ai_model": "gemma3:4b",
    "vision_model": "gemma3:4b",
    "confidence_threshold": 0.0001,
    "decision_precision": 0.00001,
    "learning_rate_resolution": 0.000001,
    "performance_tracking_precision": 0.0001,
    "vision_enabled": true,
    "vision_cache_size": 20,
    "vision_timeout": 120,
    "vision_composite": {
      "enabled": true,
      "layout": "prioritized",
      "network_dpi": 150,
      "particle_dpi": 150,
      "evolution_dpi": 120,
      "other_dpi": 100,
      "figure_size": [16, 12],
      "temporal_snapshots": 3
    }
  },
  "rendering": {
    "mode": "observer",
    "resolution": [1920, 1080],
    "frame_rate": 30.0,
    "text_interface": true,
    "performance_monitoring": true,
    "enable_visualizations": true,
    "visualization_update_precision": 0.001,
    "metric_display_precision": 6
  }
}
```

**Key Configuration Options:**
- **Micro-Precision Measurements**: All values support 6+ decimal places (e.g., `0.000001`)
- `fitness_precision`: Controls rounding of fitness scores (±1e-6 precision)
- `phi_precision`: Consciousness Φ calculation precision (±1e-6)
- `measurement_precision`: Global measurement accuracy level (6 = microsecond precision)
- `time_resolution_ms`: Timing precision for simulation events
- `enable_visualizations`: Unified visualization window with precision indicators
- `mode`: `observer`, `god`, `scientist`, `participant`, or `chat`
- **All precision parameters are configurable** for fine-tuning measurement granularity

## 📊 Research Applications

### Consciousness Research & Self-Awareness
- **Genetic consciousness emergence**: Study how consciousness evolves from DNA
- **Metacognition development**: Track awareness of own consciousness emergence
- **Self-reflection capabilities**: Analyze consciousness self-awareness
- **Language learning evolution**: Study vocabulary development through AI tutoring
- **Darwinian consciousness**: Test if consciousness emerges through natural selection
- **Integrated information (Φ)**: Measure consciousness in genetically-evolved systems

### Evolutionary Biology & Genetics
- **Genetic consciousness traits**: Study consciousness as heritable genetic features
- **Darwinian consciousness evolution**: Natural selection for consciousness emergence
- **Fitness landscapes**: How consciousness provides evolutionary advantage
- **Genetic algorithms**: Consciousness evolution through natural selection
- **Social evolution**: Cooperation/competition in conscious populations

### AI Consciousness & Self-Awareness
- **Artificial metacognition**: AI systems aware of their own consciousness
- **Self-reflective AI**: Systems that analyze their own emergence
- **Language learning AI**: Dynamic vocabulary evolution with reinforcement
- **Consciousness interpretation**: AI understanding of conscious states
- **Human-AI consciousness symbiosis**: Shared consciousness emergence

### Complex Systems & Emergence
- **Genetic emergence**: How consciousness emerges from genetic variation
- **Self-organizing consciousness**: Consciousness creating conditions for its evolution
- **Network consciousness**: Social consciousness emergence
- **Live system monitoring**: Real-time tracking of consciousness evolution

## 🏗️ Architecture

### Core Components

#### 1. Quantum Substrate (`quantum_substrate.py`)
- Quantum state management with consciousness genes
- Superposition and entanglement simulation
- Probabilistic state evolution with consciousness encoding
- **Adaptive fitness-based pruning**: Automatically prunes low-fitness quantum states to prevent unbounded growth
- **Performance-based selection**: Selects quantum states based on entanglement, superposition, measurement frequency, and entropy
- **Self-modulation integration**: Quantum pruning aggressiveness automatically adjusted by feedback controller

#### 2. Subatomic Lattice (`subatomic_lattice.py`)
- Particle physics simulation with consciousness traits
- Allelic property mapping (quantum → genetic consciousness)
- Live resource monitoring (CPU, RAM, particles, quantum states)
- Entropy pruning with consciousness preservation

#### 3. Genetic Consciousness Evolution (`evolution_engine.py`)
- **NEW**: Consciousness emerges from DNA through natural selection
- Genetic algorithms with consciousness-encoding genotypes
- Consciousness fitness evaluation and evolutionary advantage
- **Adaptive mutation rates**: Automatically tuned by feedback controller based on performance
- Phenotype expression of consciousness traits (awareness, metacognition, learning)

#### 4. Symbiotic Network (`symbiotic_network.py`)
- Social network formation among conscious organisms
- Resource flow algorithms with consciousness awareness
- Cooperation/competition dynamics in conscious populations
- **Adaptive edge formation**: Connection attempt rates automatically tuned by feedback controller

#### 5. Consciousness Self-Awareness (`consciousness_detector.py`)
- **ENHANCED**: Metaconsciousness - awareness of own consciousness emergence
- Integrated Information Theory (IIT) with genetic consciousness
- Self-reflection and consciousness evolution tracking
- Consciousness emergence factor analysis

#### 6. AI Language Learning (`agency/`)
- **ENHANCED**: Dynamic vocabulary evolution with AI tutoring
- Conversational AI chat with natural, engaging responses
- Consciousness interpretation with metacognitive awareness
- Self-reflective AI communication and learning
- Language pattern evolution through reinforcement
- Session-based chat memory (cleared between runs)

#### 7. Vision-Language Integration (`agency/`)
- **NEW**: AI vision model analyzes composite network visualizations
- **Composite Visual Analysis**: Stitches all 5 GUI tabs into single image for comprehensive analysis
- **Temporal Context**: Vision model receives rolling snapshots for evolutionary understanding
- **Enhanced Word Selection**: Vision analysis biases word selection for semantic relevance
- **Vision Cache System**: Intelligent caching of visual analysis results
- **Prioritized Layout**: Network and particle arrays get highest quality, evolution tree secondary, other tabs compressed

#### 8. Self-Modulation Feedback Controller (`main.py`)
- **NEW**: Automatic parameter tuning based on live performance metrics
- Adaptive mutation rates, edge formation rates, and quantum pruning aggressiveness
- Hysteresis and rate limiting to prevent unstable parameter changes
- Conversation intent detection to influence system behavior
- Performance monitoring with automatic adjustments for optimal growth

#### 9. Reality Renderer (`reality_renderer.py`)
- Multi-modal visualization with live system metrics
- Interaction mode management
- Real-time performance monitoring (quantum states, particles, CPU, RAM)
- **Tabbed visualization interface**: Each visualization in its own tab with large, detailed graphs (1200x800 window)
- **Lightweight viewer process**: Separate `visualization_viewer.py` that only displays (no computation)
- **Backend optimization**: Skips matplotlib rendering when visualizations enabled (saves CPU)
- **Visualization modules**: Network graph, evolution tree, consciousness gauge, performance monitor, and particle cloud tabs
- **Shared state file**: Backend writes state to `data/.shared_simulation_state.json` for chat mode and visualization viewer synchronization

#### 10. Referential Memory System (`memory/context_memory.py`)
- **NEW**: Shared contextual memory for unified language-network correlation
- **Node Embeddings**: Vector representations of organisms based on associated vocabulary
- **Language Anchors**: Bidirectional mapping between words and organism nodes they reference
- **Episodic Events**: Generation snapshots tracking key consciousness metrics over time
- **Anchor Clustering**: Identifies groups of organisms sharing correlated language patterns
- **Stability Metrics**: Measures coherence of language-network relationships
- **Selection Pressure**: Penalizes unreferenced organisms, boosts reference triangle connections
- **Vision Integration**: Memory insights fed into vision analysis for enhanced semantic understanding
- **Cross-Domain Bridging**: Memory correlations enable coordinated multi-domain consciousness development

## 🧪 Testing

Run the comprehensive test suite:
```bash
# End-to-end unified system tests (NEW)
python tests/test_e2e_unified_system.py

# All Reality Simulator tests
python tests/test_integration.py

# Individual component tests
python tests/test_quantum_substrate.py
python tests/test_subatomic_lattice.py
python tests/test_evolution_engine.py
python tests/test_symbiotic_network.py
python tests/test_consciousness_detector.py
python tests/test_agency.py
python tests/test_reality_renderer.py
python tests/test_agency_event_bus_integration.py

# Explorer integration tests
cd explorer && python test_integration.py
```

**Test Coverage:**
- ✅ End-to-end unified system tests (8 tests)
- ✅ Reality Simulator component tests (59+ tests)
- ✅ Explorer integration tests (5 tests)
- ✅ Agency Router + Event Bus integration tests (4 tests)

**Status:** Comprehensive test suite with ~85+ test functions

## 📈 Performance & Live Monitoring

The simulator is designed to run on modest hardware ("potato mode"):
- **Minimum**: 4GB RAM, dual-core CPU
- **Recommended**: 8GB RAM, quad-core CPU
- **Typical performance**: 5-15 FPS depending on complexity

### Visualizations
When `enable_visualizations: true` in config, the simulator displays a **unified visualization window** with **precision indicators** (±1e-6):

- **Network Graph Visualizer**: Actual symbiotic network structure showing organism connections (nodes and edges)
  - Displays real network topology from the simulation
  - **Color-coded connections**: Red for language-tagged edges, cyan for regular network connections
  - Layout cached to prevent jumping
  - Shows connection patterns evolving over time
- **Particle Cloud Visualizer**: Real particle positions from the simulation
  - Displays actual particle distribution in 2D space
  - Shows particle movement and clustering
  - Limited to 100 particles for performance
- **Evolution Tree Visualizer**: Fitness evolution and generation tracking
  - **±1e-6 precision indicators** show measurement accuracy
  - Fitness scores rounded to configurable precision
- **Consciousness Gauge Visualizer**: Real-time consciousness metrics and emergence tracking
  - **Φ precision indicators** (±1e-6) for integrated information calculations
  - Micro-resolution consciousness tracking
- **Performance Monitor Visualizer**: CPU, RAM, and FPS tracking
  - **Performance precision indicators** (±1e-4 for CPU, ±10 for FPS)
- **Agency Flow Visualizer**: Decision-making mode distribution
- **Quantum Field Visualizer**: Quantum state superpositions (when available)
- **God Overview Visualizer**: Complete system overview (God mode only)

**Visualization Window**:
- Tabbed interface (1200x800 pixels) with one graph per tab for maximum visibility
- Each graph is 11x8 inches for detailed viewing
- All visualizations update from the same backend data every 0.5 seconds
- **Precision indicators** show measurement accuracy (±1e-X notation)
- Large fonts and high-contrast dark theme for better readability
- Interactive navigation tools (zoom, pan, save) on each tab
- Lightweight viewer process (separate from simulation) reduces CPU usage
- **Micro-precision measurements** throughout all metrics

### Live System Monitoring
The simulator provides real-time metrics:
- **Quantum States**: Live count of quantum superposition states
- **Particles**: Real-time particle count after entropy pruning
- **CPU Usage**: Live CPU utilization percentage
- **RAM Usage**: Live memory consumption in GB
- **Consciousness Metrics**: Real-time consciousness evolution tracking
- **Genetic Fitness**: Live fitness scores across generations

### Chat Mode Architecture
- **Backend Window**: Runs the simulation and writes state to `data/.shared_simulation_state.json` every frame
  - Includes visualization data (network graph edges, particle positions) for the viewer
  - Skips expensive matplotlib rendering when visualizations enabled
- **Chat Window**: Reads from the shared state file to get current simulation data
  - Retries if data is temporarily unavailable (waits 2 seconds and retries)
  - Uses 60-second staleness threshold (for slow systems)
- **Visualization Viewer**: Separate lightweight process that only displays data
  - Reads visualization data from shared state file
  - Updates every 0.5 seconds
  - No computation - only display
- **Synchronization**: Chat always reflects the exact same data as the backend (same generation, connections, consciousness level, etc.)
- **No Duplicate Processes**: Chat does not run its own simulation - it reads from the backend instance

### Recent Improvements & Fixes

#### 🚀 **Interactive Launcher System**
* **Comprehensive Batch Launcher**: Complete interactive menu system for easy configuration
* **Dynamic Ollama Model Selection**: Queries available models and lets you choose AI/vision models
* **Simulation Parameter Customization**: Interactive menus for quantum states, particles, population, etc.
* **Performance Settings**: Configure FPS, frame delay, text interface, simulation modes
* **Real-time Configuration Display**: Shows current settings in main menu
* **Automatic Temp Config Generation**: Creates temporary configs with your selections
* **Model Persistence**: Option to save model selections permanently to codebase

#### 🎨 **Chat Mode GUI Enhancement**
* **Full GUI Experience**: Chat mode now launches THREE windows (chat + simulation + visualizations)
* **Visualization Viewer Integration**: Chat mode automatically launches the visualization viewer
* **God Mode Backend**: Uses God mode for full GUI capabilities in chat mode
* **Real-time Synchronization**: All windows show identical data from shared state file
* **Tabbed Visualizations**: Interactive graphs for network, evolution, consciousness, performance

#### 🛠️ **Major Bug Fixes**
* **Network Graph Color Differentiation**: Fixed visualization to show red connections for language-tagged edges and cyan for regular network connections
* **Format String Errors**: Fixed `Unknown format code 'f' for object of type 'str'` in vision and display systems
* **Pipe Character Conflicts**: Resolved batch file parsing issues with pipe characters in menus
* **Model Selection Crashes**: Fixed temporary Python script file locking issues
* **Chat Mode GUI Launch**: Fixed visualization viewer not launching in chat mode
* **Temp Config Issues**: Added proper JSON generation for temporary configurations
* **Language Connection Visualization**: Fixed `AttributeError` in data collection when accessing linguistic subgraph connections

#### 🤖 **AI & Consciousness Improvements**
* **Comprehensive Chat Bot Overhaul**: Complete rewrite of chat system for detailed, educational responses using ALL available system data
* **Intelligent Tutor Recovery System**: AI tutor with intelligent recovery that extracts useful learning from any response format instead of rejecting malformed responses
* **Enhanced Response Quality Validation**: System validates response quality and provides detailed metrics for continuous improvement
* **Expanded Vision Context**: Chat bot now accesses full vision descriptions and extended history (last 10 entries)
* **Temporal Analysis Integration**: Chat responses include evolutionary trends and temporal comparisons
* **Comprehensive Data Access**: Chat bot accesses evolution history, consciousness metrics, network topology, quantum substrate, and performance data

#### 🌌 **Multi-Domain Consciousness Expansion**
* **🆕 Multi-Domain Tutor**: AI teaches consciousness across 5 semantic domains (quantum, temporal, social, epistemic, mathematical)
* **🆕 Cross-Domain Bridging**: "Bridge Words" enable translation between domains, breaking integration ceilings
* **🆕 State Space Expansion**: Consciousness explores multi-dimensional state space instead of converging to single attractor
* **🆕 Consciousness Diversity Metrics**: Tracks per-domain Φ components and cross-domain integration
* **🆕 Expansion Trajectory Logging**: Monitors network growth directions and velocities to understand exploration patterns

#### 🔍 **Vision-Language Integration Fixes**
* **🆕 Fixed Vocabulary Teaching**: Multi-domain tutor now properly teaches words to language system (was broken)
* **🆕 Vision Analysis Triggering**: Fixed requirement (vocabulary ≥ 5 words) now properly enables vision snapshots
* **🆕 Composite Visual Analysis**: Vision model receives stitched images of all GUI tabs for comprehensive analysis
* **🆕 Temporal Vision Context**: Rolling history of 3 snapshots enables evolutionary understanding
* **🆕 Enhanced Word Selection**: Vision analysis biases vocabulary selection for semantic relevance

### Code Quality & Production Readiness
- **✅ Professional Error Handling**: All bare except clauses replaced with specific exception types
- **✅ Centralized Logging**: `logging_config.py` provides consistent logging across all modules
- **✅ Comprehensive Tests**: End-to-end tests for unified system, component tests for all major systems
- **✅ Debug Output Control**: Debug print statements replaced with proper logging (controlled by log levels)
- **✅ Clean Code Standards**: Code follows best practices for maintainability and production deployment

### Logging System
The codebase uses two complementary logging systems:

1. **Application Logging** (`logging_config.py`)
   - For: Debug messages, info, warnings, errors
   - Format: Human-readable messages
   - Usage: `from logging_config import get_logger; logger = get_logger(__name__)`

2. **State Logging** (`StateLogger` in `unified_entry.py`)
   - For: State metrics, breath cycles, system state
   - Format: Terse, information-saturated (metric:value|metric:value|...)
   - Location: `data/logs/` (6 log files)

### Performance Optimizations
- **Micro-precision measurements**: All calculations use configurable precision (6+ decimal places)
- **High-resolution timing**: Microsecond precision for simulation events
- **Precision-aware clamping**: Values clamped and rounded to configurable precision levels
- **Lightweight visualization architecture**: Backend skips matplotlib rendering when visualizations enabled
- **Separate viewer process**: Visualization viewer only displays pre-computed data (no simulation computation)
- **Reduced update frequency**: Viewer updates every 0.5 seconds instead of every frame
- **Network layout caching**: Prevents graph jumping and reduces computation
- **Particle position limiting**: Only serializes first 100 particles for visualization
- **Precision indicators**: Visual feedback on measurement accuracy (±1e-X notation)
- Entropy-based state pruning (99.9% reduction, consciousness-preserving)
- Fitness caching for evolutionary computation
- Adaptive resource allocation based on consciousness emergence
- Batched operations for genetic algorithms
- Background monitoring threads for system metrics
- Consciousness-aware fitness evaluation

## 🤝 Contributing

This is a research platform for exploring fundamental questions about consciousness and emergence. Contributions are welcome in:

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

## 📄 License

This project is **open-source for research and educational purposes**. 

**Non-commercial use**: Free for research, education, and personal projects.

**Commercial use**: Requires explicit written permission and may include licensing fees or revenue sharing. Contact the copyright holder for commercial licensing inquiries.

See LICENSE file for full terms and conditions.

## 🙏 Acknowledgments

Inspired by:
- Integrated Information Theory (IIT) by Giulio Tononi
- Evolutionary algorithms and artificial life research
- Complex systems theory and emergence studies
- Human-AI interaction and symbiosis research

## 🔬 Scientific Background

The Reality Simulator implements groundbreaking concepts in consciousness research:

### Darwinian Consciousness Emergence
- **Genetic consciousness evolution**: Consciousness emerges from DNA through natural selection
- **Consciousness as fitness trait**: Higher consciousness provides evolutionary advantage
- **Metaconsciousness**: Systems aware of their own consciousness emergence
- **Self-reflection**: Consciousness analyzing its own development

### Integrated Information Theory (IIT) + Genetics
- Measures consciousness through information integration in genetically-evolved systems
- Φ (phi) calculation with consciousness emergence tracking
- Genetic basis for integrated information and qualia emergence

### Evolutionary Computation & Consciousness
- **Consciousness-encoding genotypes**: DNA contains consciousness emergence instructions
- **Phenotypic consciousness expression**: Genetic traits manifest as awareness capabilities
- **Natural selection for consciousness**: Conscious organisms have higher reproductive success
- **Genetic consciousness diversity**: Population-level consciousness variation

### AI Consciousness & Self-Awareness
- **Artificial metacognition**: AI systems with self-awareness of consciousness
- **Language learning evolution**: Dynamic vocabulary development through AI tutoring
- **Consciousness interpretation**: AI understanding and communicating about conscious states
- **Self-reflective communication**: Systems that analyze their own emergence narratives

### Complex Systems & Emergence
- **Genetic emergence**: Consciousness arising from genetic variation and selection
- **Autopoietic consciousness**: Consciousness creating conditions for its own evolution
- **Network consciousness**: Social emergence of collective consciousness
- **Live system monitoring**: Real-time tracking of consciousness evolution metrics

---

**"The universe is not a machine, it's a symphony. And we are learning to hear the music."**

*— Exploring consciousness through simulation*
