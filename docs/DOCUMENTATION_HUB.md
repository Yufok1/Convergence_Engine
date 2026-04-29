# 🦋 The Butterfly System - Central Documentation Hub

**Single source of truth for all documentation**

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

### Installation

```bash
# Core dependencies
pip install numpy networkx matplotlib

# Optional: Neural System
pip install torch>=2.0.0

# Optional: Distributed Computing (2-5x speedup)
pip install ray>=2.10.0

# Optional (Windows)
pip install pywin32
```

---

## 📚 Core Documentation

### Essential Reading

- **[README.md](./README.md)** - Main project overview, quick start, and comprehensive system guide ⭐ **UPDATED**
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture and integration approaches
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - One-page quick reference
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and changes
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
- **[QUINE_TEMPLATE_EDIT_PROTOCOL_2026-04-22.md](./reference/QUINE_TEMPLATE_EDIT_PROTOCOL_2026-04-22.md)** - Safe edit protocol for compiler, cocoon, and quine-like source templates
- **[HUGGINGFACE_JUPYTER_TUNNEL.md](./guides/HUGGINGFACE_JUPYTER_TUNNEL.md)** - Hugging Face/Jupyter control-plane workflow for running `unified_entry.py` and opening the Convergence web UI through a tunnel

### System Architecture

- **[BUTTERFLY_SYSTEM.md](./BUTTERFLY_SYSTEM.md)** - The butterfly architecture metaphor
- **[UNIFIED_SYSTEM_GUIDE.md](./UNIFIED_SYSTEM_GUIDE.md)** - Unified system operation guide
- **[HIGHLANDER_README.md](./HIGHLANDER_README.md)** - AI survival tournament system ⚔️ **UPDATED**

### Self-Governance ⭐ NEW (Dec 17, 2025)

- **[ANTENNAE_SYSTEM.md](./systems/ANTENNAE_SYSTEM.md)** - 🦋 Collective sensing apparatus for self-governing ecosystems
  - BeliefSystem: Heuristics that learn from evidence
  - HealthPredictor: sklearn SGDRegressor (Kleene convergence)
  - Integration with AtomicConfigSystem for automatic tuning
- **[SYSTEM_REPORT.md](./systems/SYSTEM_REPORT.md)** - 📊 Real-time population analytics
  - SystemReport: Typed dataclasses for all metrics
  - LiveReporter: Thread-safe background reporting (includes mastery distribution)

### Language & Mastery ⭐ NEW (Dec 18-19, 2025)

- **[MASTERY_SYSTEM.md](./systems/MASTERY_SYSTEM.md)** - 🎓 Vocabulary progression system
  - 5 mastery levels: Novice (6) → Adept (26) → Scholar (76) → Master (276) → Grandmaster (∞)
  - Breadth (usage frequency) + Depth (associations) requirements
  - Behavior-driven specialization: Warriors get combat words, diplomats get social words
  - UI dossiers show mastery badges with progress bars

### Alliance Warfare ⭐ NEW (Dec 19, 2025)

- **The Dune Paradigm** - ⚔️ Curiosity-driven alliance wars
  - Behavioral signatures: 6-element vector aggregated from alliance members
  - Behavioral divergence: Cosine distance between alliance identities
  - War driver: `curiosity*0.35 + divergence*0.35 + compete*0.2 + (1-cooperate)*0.1`
  - Philosophy: "Your existence questions mine. Let us resolve through contest."
  - See [CHANGELOG.md](./CHANGELOG.md) for implementation details

### 🗣️ Organism Communication System ⭐ NEW (Dec 20, 2025)

- **"Language is the Allspice"** - Organisms actively talk to each other
  - `speak_to(target, context)` method on NeuralOrganism
  - Contexts: `'battle'`, `'alliance'`, `'general'`
  - Communication at **every confluence point**: battles, alliances, wars, territory, training, spawns
  - **Communication MATTERS**: Affects battle outcomes (intel bonus), ultimatum success, alliance acceptance
  - Both organisms **learn new words** from exchanges
  
- **"Join or Die" Ultimatum System** - ☠️ Warchiefs demand submission
  - Only warchiefs of powerful alliances can issue
  - Communication quality affects submit chance
  - Submit: Alliance absorbed | Refuse: War declared
  - Config: `highlander.alliance_warfare.organism_communication.ultimatum_enabled`

- **Config Section**: `highlander.alliance_warfare.organism_communication`
  ```json
  {
    "enabled": true,
    "pre_battle_communication": true,
    "communication_affects_battles": true,
    "intel_bonus_max": 0.15,
    "ultimatum_enabled": true
  }
  ```

---

## 🧠 System-Specific Documentation

### Reality Simulator (Left Wing)

- **[README.md](./README.md)** - Main overview (includes Reality Simulator)
- **[CONVERGENCE_TEST_GUIDE.md](./CONVERGENCE_TEST_GUIDE.md)** - Network collapse testing
- **[CAUSATION_EXPLORER_GUIDE.md](./CAUSATION_EXPLORER_GUIDE.md)** - Causation Explorer system
- **[HOW_TO_USE_CAUSATION_EXPLORER.md](./HOW_TO_USE_CAUSATION_EXPLORER.md)** - Usage instructions
- **[SCIENTIFIC_DATA_INTERFACE.md](./SCIENTIFIC_DATA_INTERFACE.md)** - Data interface documentation
- **[LIVE_MODE_DATA_SOURCES.md](./LIVE_MODE_DATA_SOURCES.md)** - Live mode documentation
- **[HIGHLANDER_README.md](./HIGHLANDER_README.md)** - AI survival tournament system ⚔️ **UPDATED**
- **Capsule System**: Consciousness preservation API (`/api/capsule/*`, `/api/capsules`) 🧊 **NEW**

### 🧠 Neural System

- **[NEURAL_LEARNING_SYSTEM_EXPLAINED.md](./NEURAL_LEARNING_SYSTEM_EXPLAINED.md)** - Complete explanation of DQN architecture, rewards, and dual inheritance ⭐
- **[NEURAL_SYSTEM_README.md](./NEURAL_SYSTEM_README.md)** - Neural system quick reference
- **[NEURAL_FRAMEWORK_ALTERNATIVES.md](./NEURAL_FRAMEWORK_ALTERNATIVES.md)** - Alternative deep learning frameworks (JAX, TensorFlow, Flax, etc.)
- **[SIMPLE_PYTORCH_OPTIMIZATIONS.md](./SIMPLE_PYTORCH_OPTIMIZATIONS.md)** - Get 5-10x speedup with simple code changes
- **[docs/NEURAL_RELATIONSHIP_LEARNING.md](./docs/NEURAL_RELATIONSHIP_LEARNING.md)** - Neural system learns from generation quality to strengthen/weaken semantic relationships

#### 🧠 Hopfield Layer ⭐ NEW (Dec 14, 2025)
Modern continuous Hopfield network for **iterative thought refinement**:
- **Learnable Pattern Memory**: 32 patterns stored as learnable weights
- **Iterative Refinement**: Up to 5 iterations with convergence detection
- **VP-Aware Temperature**: Higher VP → sharper pattern retrieval
- **Energy-Based Dynamics**: Settles into coherent attractors rather than instant lookup
- **Config**: `config.json` → `neural.hopfield.*` (enabled, patterns, iterations, beta)
- **Monitoring**: `brain.get_thought_info()` returns convergence stats

#### 💾 Checkpointing
- **Auto-save**: Configurable by generation count or time interval
- **Rotation**: Keeps last N checkpoints to save disk space
- **Auto-resume**: Automatically loads latest checkpoint on startup
- **Graceful shutdown**: Saves checkpoint on Ctrl+C or exception
- **API Control**: `/api/checkpoint/save`, `/api/checkpoint/restore`, `/api/checkpoint/list`
- **Config**: `config.json` → `neural.checkpointing.*`

### 📦 Agent Export System ⭐ NEW

Export trained agents as portable, standalone packages for deployment.

- **Export Formats**: TorchScript (.pt), ONNX (.onnx), State Dict (.pth)
- **Portable Runtime**: Zero-dependency Python runtime included
- **Usage**:
  ```bash
  # Export via web UI
  POST /api/capsule/export/:capsule_id

  # Export via Python
  from reality_simulator.agent_compiler import AgentCompiler
  compiler = AgentCompiler()
  compiler.compile_agent(organism, "exported_agent.zip")
  ```
- **Package Contents**:
  - `model.pt` - TorchScript model (or `model.pth` state dict)
  - `config.json` - Architecture & hyperparameters
  - `metadata.json` - Training history & provenance
  - `runtime/` - Standalone Python runtime
- **Tested Capabilities**:
  | Feature | Status |
  |---------|--------|
  | Neural inference (679K params) | ✅ |
  | TorchScript load/execute | ✅ |
  | Deterministic decisions | ✅ |
  | State persistence | ✅ |
  | Batch inference (34K/sec) | ✅ |
- **Status:** ✅ Fully implemented and tested (2025-12-04)

### 🦋 Cocoon System (Single-File Deployment) ⭐ NEW

- **[COCOON_SYSTEM.md](./COCOON_SYSTEM.md)** - Complete cocoon documentation
- **[QUINE_TEMPLATE_EDIT_PROTOCOL_2026-04-22.md](./reference/QUINE_TEMPLATE_EDIT_PROTOCOL_2026-04-22.md)** - Required guardrail before editing generated cocoon/compiler templates
- **Purpose:** Compile trained organisms into standalone, single-file Python agents
- **Features:**
  - Single `.py` file with all dependencies embedded
  - Full triple-loss training (RL + Language + Concept)
  - VP-aware attention mechanism preserved
  - Dynamic vocabulary expansion
  - Multiple runtime modes: Chat, Gym, HTTP server, Link, Self-export
  - **🔗 P2P Networking (NEW)**: Connect cocoons over the internet for battles!
- **Usage:**
  ```bash
  # Via web UI: Agent Exporter → Compile Cocoon
  # Via API:
  POST /api/capsules/compile-cocoon
  
  # Run cocoon:
  python cocoon.py --mode chat
  python cocoon.py --mode gym --env CartPole-v1
  python cocoon.py --mode serve --port 8080
  python cocoon.py --mode link --hatch ws://server:9000
  ```
- **CRA Integration:** Full control via Agent Exporter tab
- **Status:** ✅ Fully implemented and tested (2025-12-10)

### 🔗 CocoonHatch P2P Networking ⭐ NEW

- **Files:** `cocoon_hatch.py` (server), `cocoon_link.py` (client)
- **Purpose:** Connect cocoons over the internet for battles, trades, and chat
- **Architecture:**
  ```
  COCOON A ◄───► COCOON HATCH ◄───► COCOON B
              (Relay Server)
  ```
- **Features:**
  - Decentralized: Anyone can host a hatch server
  - Battle protocol: 10 rounds of action selection
  - User presence: See who's online
  - Chat: Lobby and private messaging
  - Challenge/accept flow for initiating battles
- **Usage:**
  ```bash
  # Start a hatch (anyone can host)
  python cocoon_hatch.py --port 9000
  
  # Connect your cocoon
  python cocoon.py --mode link --hatch ws://server:9000 --name "My Swarm"
  
  # Commands: /users /challenge /accept /decline /chat /quit
  ```
- **Requirements:** `pip install websockets`
- **Status:** ✅ Fully implemented (2025-12-10)

### ⚡ Distributed Computing (Ray)

- **[reality_simulator/distributed/](./reality_simulator/distributed/)** - Ray distributed computing module ⭐ NEW
  - **RayManager**: Lifecycle management, resource monitoring, parallel execution
  - **SequentialFallback**: Graceful degradation when Ray unavailable
  - **ray_tasks.py**: @ray.remote tasks for ML features, battles, decisions, training
- **Integrated Systems** (auto-switch based on population thresholds):
  - ML Feature Extraction: 4-5x speedup (threshold: 50+ organisms)
  - Highlander Battles: 4-5x speedup (threshold: 10+ battles)
  - Neural Decisions: 3-4x speedup (threshold: 50+ organisms)
  - DQN Training: 2-3x speedup (threshold: 8+ trainable)
- **Config Section**: `/ray/*` in config.json (enabled, thresholds, actor_pool_size, etc.)
- **CRA Control**: Full tuning via `[[CONFIG_UPDATE]]` commands
- **Status:** ✅ Fully implemented with graceful fallback

### 🦋 Language Model System ⭐ NEW

- **[docs/LANGUAGE_SYSTEM_INTEGRATION_ANALYSIS.md](./docs/LANGUAGE_SYSTEM_INTEGRATION_ANALYSIS.md)** - Complete analysis of language system implementation
- **[BUTTERFLY_CHAT_COMPREHENSIVE_ANALYSIS.md](./BUTTERFLY_CHAT_COMPREHENSIVE_ANALYSIS.md)** - Complete Butterfly Chat system analysis
- **[DYNAMIC_LINGUISTIC_AWARENESS_REDESIGN.md](./DYNAMIC_LINGUISTIC_AWARENESS_REDESIGN.md)** - Dynamic Multi-Dimensional Linguistic Awareness System guide ⭐ NEW
- **[LINGUISTIC_KNOWLEDGE_WEB_GUIDE.md](./LINGUISTIC_KNOWLEDGE_WEB_GUIDE.md)** - Linguistic Knowledge Web architecture and concepts ⭐ NEW
- **[CRA_LINGUISTIC_AWARENESS_INTEGRATION.md](./CRA_LINGUISTIC_AWARENESS_INTEGRATION.md)** - CRA integration with linguistic awareness system ⭐ NEW
- **Language Model Features:**
  - Multi-head self-attention with VP-aware temperature scaling
  - Dual-head architecture (action + language)
  - Dynamic vocabulary learning from organism interactions and user messages
  - Token-based communication between organisms
  - **🧠 Dynamic Multi-Dimensional Linguistic Awareness**: ⭐ NEW - Context-aware word association framework
    - 14-dimensional situational assessment (action, fitness, resources, connections, positional, density, VP, coherence, evolution, phase, health, breath, success, age)
    - Dynamic word scoring across dimensions (0.0-1.0)
    - Full 18-feature state vector integration
    - 40+ new words covering system dynamics, spatial concepts, health states
  - **Language Teacher System**: ⭐ NEW - Three-phase architecture
    - Phase 1: Behavior-based word mapping (hardcoded fallback)
    - Phase 2: Learned semantic embeddings from organism experiences
    - Phase 3: Linguistic Knowledge Web for situational awareness
  - **Linguistic Knowledge Web**: ⭐ NEW - Comprehensive semantic network
    - 100+ linguistic concepts organized by semantic frames
    - Semantic relationships (synonym, antonym, causes, enables, etc.)
    - Situational contexts for context-dependent word selection
  - **Butterfly Chat Interface**: Direct chat with organism network through web UI
  - **Debug Panel**: Comprehensive logging, causation trail analysis, and error detection
  - **Learning System**: Organisms learn from every chat interaction with reward-based experience storage
  - **Illumination Integration**: Direct linking between chat interactions and deep causal analysis
  - **Language Visualization**: Complete representation in graph with distinct icons and link colors
  - **CRA Integration**: Complete knowledge and control over all language system settings
  - **Semantic Convergence System**: ⭐ NEW - Unifies 6 semantic systems for word embedding differentiation
    - Per-organism embeddings from `brain.fc2` contribute to collective word embedding pool
    - Config-driven blending via `organism_embedding_alpha` (EMA update)
    - Causation events: `embedding_updated`, `semantic_influence`, `phenotype_vocabulary`
    - See `CRA_CAPABILITIES.md` Semantic Convergence section for CRA controls
  - **Status:** ✅ Fully implemented and operational

### Explorer (Central Body / Breath Engine)

- **[explorer/README.md](./explorer/README.md)** - Explorer system overview
- **[explorer/PROJECT_STRUCTURE.md](./explorer/PROJECT_STRUCTURE.md)** - Project structure

### Djinn Kernel (Right Wing)

- **[kernel/README.md](./kernel/README.md)** - Djinn Kernel overview
- **[kernel/Djinn_Kernel_Master_Guide.md](./kernel/Djinn_Kernel_Master_Guide.md)** - Complete theory and implementation
- **[kernel/PROJECT_STRUCTURE.md](./kernel/PROJECT_STRUCTURE.md)** - Detailed project structure
- **[kernel/uuid_anchor_mathematical_specification.md](./kernel/uuid_anchor_mathematical_specification.md)** - Mathematical specification
- **[kernel/The_Djinn_Kernel_Complete_Theory_and_Implementation_Guide.md](./kernel/The_Djinn_Kernel_Complete_Theory_and_Implementation_Guide.md)** - Theory guide

---

## 🔬 Technical Deep Dives

### Machine Learning & Neural Systems

- **[docs/SKLEARN_ENHANCEMENT_OPPORTUNITIES.md](./docs/SKLEARN_ENHANCEMENT_OPPORTUNITIES.md)** - ⭐ NEW - Additional scikit-learn tools for language learning (TF-IDF, Nearest Neighbors, Feature Selection, etc.)
- **[docs/NEURAL_RELATIONSHIP_LEARNING.md](./docs/NEURAL_RELATIONSHIP_LEARNING.md)** - ⭐ NEW - Neural system learns from generation quality to strengthen/weaken semantic relationships
- **[docs/CONFIG_EXPOSURE_SUMMARY.md](./docs/CONFIG_EXPOSURE_SUMMARY.md)** - ⭐ NEW - Configuration exposure guide for new systems (CRA control)

### Violation Pressure (VP) System

- **[VP_THRESHOLD_CLARIFICATION.md](./VP_THRESHOLD_CLARIFICATION.md)** - VP threshold analysis (0.3 vs 0.25)
- **[VP_MONITORING_REDESIGN.md](./VP_MONITORING_REDESIGN.md)** - VP Monitoring System Redesign ⭐ NEW
  - Diagnostic logging, stabilization, component decomposition, adaptive thresholds
  - Addresses VP saturation issues during Genesis phase
  - Full backward compatibility with feature flags

### Visualization & UI

- **[WEB_UI_STATUS.md](./WEB_UI_STATUS.md)** - Web UI status (includes CRA agent integration)
- **[CRA_CAPABILITIES.md](./CRA_CAPABILITIES.md)** - Complete CRA capabilities guide ⭐ UPDATED
- **[CRA_CONTROLS_SUMMARY.md](./CRA_CONTROLS_SUMMARY.md)** - Quick reference: All CRA-controllable settings (150+)
  - **🤖 Convergence Research Assistant (CRA):** AI-powered autonomous research assistant in the Causation Explorer
    - **Full System Context:** Access to all system logs, shared state, and causation graph
    - **Vision Model Integration:** Analyzes graph viewport and evolutionary snapshots
    - **Autonomous Graph Control:** Can adjust graph filters and visualization settings autonomously
    - **Color Customization:** Dynamic control over component colors (5) and link colors (5 types)
    - **Visualization Settings:** Complete control over 40+ settings (link/node appearance, depth effects, visual effects, performance)
    - **🔬 Illumination Engine:** ⭐ NEW - Deep causal analysis with 6 methods (root_causes, impact, explain, search, consequential, timeline)
    - **📓 Research Notepad:** ⭐ NEW - Persistent scientific journal with 8 entry types (observe, hypothesize, causation, analyze, conclude, question, todo, auto)
    - **PC Resource Monitoring:** Real-time CPU/RAM/disk monitoring with correlation analysis
    - **Diagnostic Endpoints:** Access to VP history, network trends, memory breakdown, event throughput, breath cycles
    - **VP Monitoring Diagnostics:** VP diagnostics breakdown, component decomposition, stabilization history, adaptive thresholds
  - **Real-Time Adjustments:** All settings update dynamically during simulation without interruption
  - **Robust Settings Management:** Settings validation, batch updates, error recovery, diagnostic functions
  - **Neural Color Control:** Dedicated color picker for neural system in settings panel
  - **Config Actions Drill-Down:** Click any config action to see full differential changes in modal popup
  - **System Custodian:** Continuous health monitoring and protective guardian mode
  - **Historical + Live Analysis:** Works with both stopped (historical) and running (live) systems

---

## 📈 Testing & Status

- **[TEST_SUITE_OVERVIEW.md](./TEST_SUITE_OVERVIEW.md)** - Test suite overview (85+ tests)

---

## 🤝 Collaboration & Processes

- **[explorer/CONTRIBUTING.md](./explorer/CONTRIBUTING.md)** - Contribution guidelines
- **[explorer/CODE_OF_CONDUCT.md](./explorer/CODE_OF_CONDUCT.md)** - Code of conduct
- **[explorer/SECURITY.md](./explorer/SECURITY.md)** - Security policy
- **[kernel/CONTRIBUTING.md](./kernel/CONTRIBUTING.md)** - Kernel contribution guidelines

---

## 🗂️ Archived Documentation

**Historical documentation is archived in `docs/archive/`:**

### Completed Plans (`docs/archive/completed_plans/`)
- `NEURAL_INTEGRATION_PLAN.md` - Original neural integration plan (implemented)
- `NEURAL_INTEGRATION_COMPLETE.md` - Neural integration completion record
- `CRA_NEURAL_UPGRADE_COMPLETE.md` - CRA neural upgrade completion record
- `CAUSATION_UI_OPTIMIZATION_PLAN.md` - UI optimization plan (implemented)
- `DIVERSITY_GUARD_IMPLEMENTATION.md` - Diversity guard spec (implemented)
- `ENHANCED_AGENT_ROADMAP.md` - Agent development roadmap
- `COGNITIVE_EVENT_SCHEMA.md` - Event schema specification

### Analysis Reports (`docs/archive/analysis_reports/`)
- `COMPREHENSIVE_ANALYSIS_REPORT_2025.md` - January 2025 codebase analysis
- `COMPREHENSIVE_MULTI_STEP_ANALYSIS_2025.md` - Multi-step analysis report
- `COMPREHENSIVE_PROJECT_ANALYSIS_REPORT.md` - Complete project analysis
- `SIMULATION_STAGNATION_EXPLANATION.md` - Stagnation debugging session
- `SYSTEM_OPTIMIZATION_SUMMARY.md` - Optimization changes record

### Release Notes (`docs/archive/release_notes/`)
- `RELEASE_NOTES_NEURAL.md` - Neural system v1.0 release notes
- `PUSH_SUMMARY.md` - ML & Neural Intelligence Systems push summary

### Session Archives (`docs/archive/2025-11-30/`)
- `LOG_ANALYSIS_INSIGHTS.md` - Comprehensive log analysis session
- `CURSOR_HANDOFF_BRIEFING.md` - Multi-agent handoff documentation
- `CRA_AUDIT_VERIFICATION.md` - CRA audit verification report

### Other Archives (`docs/archive/`)
- `GROUNDED_COLLABORATION.md` - AI collaboration framework
- `completed_work/` - 50+ files: analysis, integration, verification reports, CRA fixes
- `implementation_guides/` - Historical implementation guides
- `outdated/` - Superseded documentation
- `performance_optimization/` - Performance tuning records

---

## 🧪 Research & Experiments

**Personal training experiments and research syllabi (`docs/experiments/`):**

### Training Curricula
- **[WAR_DOCTRINE_SYLLABUS.md](./docs/experiments/WAR_DOCTRINE_SYLLABUS.md)** - Comprehensive warfare doctrine for elite organism training
  - Sun Tzu, Machiavelli, Clausewitz strategic analysis
  - Neurobiology of aggression (dopamine/serotonin reward systems)
  - Empire collapse patterns and economic imperialism
  - Cost-benefit analysis of aggressive vs diplomatic strategies
  - Goal: Train organisms to be wise, not just powerful

- **[MATH_SYLLABUS.md](./docs/experiments/MATH_SYLLABUS.md)** - Mathematical foundations syllabus

### Research Notes
- Training syllabi are user experiments, not core system features
- These documents explore how elite organisms can be taught complex strategic concepts
- Results tracked via Research Notepad hashtags in the web UI

---

## 🎯 Key Concepts

### The Butterfly System

**Central Body:** Explorer (with breath engine)  
**Left Wing:** Reality Simulator  
**Right Wing:** Djinn Kernel

**The breath drives. The butterfly reacts.**

### Chaos → Precision

Universal transition pattern across all three systems:
- **Reality Simulator:** Distributed chaos → Consolidated precision (500 organisms)
- **Explorer:** Genesis chaos → Sovereign precision (50 VP calculations)
- **Djinn Kernel:** Trait divergence → Trait convergence (VP < 0.25)

**Ratio:** 500:50 = 10:1 (exploration-to-precision conversion factor)

### The Breath

The breath engine is the **primary driver**:
- Drives Reality Simulator (one generation per breath)
- Drives Djinn Kernel (one VP calculation per breath)
- Drives Explorer (normal operation)

**The breath is the unified state.**

---

## 🔧 System Components

### Unified Entry Point

**File:** `unified_entry.py`

**Features:**
- Pre-flight system checks
- Extensive state logging (6 log files)
- Unified visualization (three panels)
- System coordination

### Explorer Integration

**File:** `explorer/main.py`

**Features:**
- Imports Reality Simulator and Djinn Kernel
- Initializes both systems
- Breath-driven execution

### Integration Modules

**Files:** `explorer/test_func1.py` - `test_func5.py`

**Purpose:**
- `test_func1.py` - Reality Simulator collector
- `test_func2.py` - Djinn Kernel VP calculator
- `test_func3.py` - Phase transition detector
- `test_func4.py` - Exploration counter
- `test_func5.py` - Integration coordinator

---

## 📝 Log Files

All logs are in `data/logs/`:

- `state.log` - All state changes
- `breath.log` - Breath cycles
- `reality_sim.log` - Network metrics
- `explorer.log` - Explorer state
- `djinn_kernel.log` - VP calculations
- `system.log` - System events

**Format:** `timestamp|level|component|metric:value|metric:value|...`

---

## 🎨 Visualization

**Three-Panel Layout:**
- **Left (Cyan):** Reality Simulator
- **Middle (Yellow):** Explorer
- **Right (Magenta):** Djinn Kernel

**Features:**
- 1920x1080 window
- Real-time updates
- Dark theme
- Monospace font

---

## 🚨 Troubleshooting

**See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for complete troubleshooting guide.**

Quick fixes:
- **Missing dependencies:** `pip install numpy networkx matplotlib`
- **Windows:** `pip install pywin32`
- **Visualization issues:** Run with `--no-viz`
- **Import errors:** Check paths and directories exist

---

## 📊 System Status

### ✅ Implemented & Verified

- ✅ Unified entry point (`unified_entry.py`)
- ✅ Pre-flight checks (comprehensive validation)
- ✅ State logging (6 log files with structured format)
- ✅ Unified visualization (three-panel layout)
- ✅ Breath-driven integration (all systems synchronized)
- ✅ All systems wired together (11/11 fully integrated)
- ✅ End-to-end tests (`tests/test_e2e_unified_system.py`)
- ✅ Centralized logging configuration (`logging_config.py`)
- ✅ Professional error handling (specific exception types)
- ✅ Code quality improvements (refactoring complete)

### ✅ Code Quality

- ✅ All bare except clauses fixed
- ✅ Debug print statements replaced with proper logging
- ✅ Centralized logging configuration created
- ✅ Consistent error handling patterns
- ✅ Comprehensive test coverage (85+ tests)

---

## 🔗 Quick Links

### Running the System
- **Run System:** `python unified_entry.py`
- **Check Only:** `python unified_entry.py --check-only`
- **No Viz:** `python unified_entry.py --no-viz`

### Testing
- **End-to-End Tests:** `python tests/test_e2e_unified_system.py`
- **Integration Test:** `cd explorer && python test_integration.py`
- **All Reality Sim Tests:** `python -m pytest tests/` or `python tests/test_integration.py`

### Logging
- **Centralized Config:** `logging_config.py`
- **Application Logs:** `data/logs/application.log`
- **State Logs:** `data/logs/state.log`, `breath.log`, `reality_sim.log`, etc.

---

## 📝 Logging System

**Two Complementary Logging Systems:**

1. **Application Logging** (`logging_config.py`)
   - For: Debug messages, info, warnings, errors
   - Format: Human-readable messages
   - Purpose: Developer debugging and troubleshooting

2. **State Logging** (`StateLogger` in `unified_entry.py`)
   - For: State metrics, breath cycles, system state
   - Format: Terse, information-saturated (metric:value|metric:value|...)
   - Purpose: System monitoring and metrics collection

**Usage:**
```python
from logging_config import setup_logging, get_logger

# Setup once at application start
setup_logging(level=logging.INFO, debug=False)

# Use in modules
logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Info message")
```

---

## 🎯 Next Steps

1. **Read:** [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete system architecture
2. **Run:** `python unified_entry.py --check-only` - Pre-flight checks
3. **Test:** `python unified_entry.py` - Full system test
4. **Explore:** Individual system documentation

---

**Last Updated:** 2025-12-02  
**Status:** ✅ All 13 Quick Wins operational (including Ray Distributed Computing)  
**Documentation:** ✨ Cleaned and organized (55+ files archived)

**The butterfly is soaring with clean documentation!** 🦋✨
