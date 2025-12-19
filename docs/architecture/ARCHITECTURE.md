# 🏗️ System Architecture

**The Butterfly System - Complete Architecture**

---

## 🚦 Agency Router ↔ Event Bus Integration

**Clean Architecture Pattern:**
- **Agency Router**: Synchronous decision engine (state-aware)
- **Event Bus**: Asynchronous notification system (decoupled)
- **Integration**: All decisions automatically publish events

**Flow:**
```
Decision Request → Agency Router → System Decision Maker → Decision
                                                              ↓
                                                    Event Bus (async)
                                                              ↓
                                                    All Subscribers Notified
```

**Event Types:**
- `AGENCY_DECISION`: All agency router decisions
- `VIOLATION_PRESSURE`: VP calculations
- `IDENTITY_COMPLETION`: UUID anchoring
- `TRAIT_CONVERGENCE`: Trait convergence events
- `SYSTEM_HEALTH`: Health monitoring

**Status:** ✅ Fully integrated - All decisions publish to Event Bus automatically

See [EVENT_BUS_VS_AGENCY_ROUTER.md](./EVENT_BUS_VS_AGENCY_ROUTER.md) for details.

---

## 🦋 The Butterfly Architecture

```
                    🦋 THE BUTTERFLY SYSTEM 🦋
                           
                    ┌─────────────────┐
                    │   EXPLORER      │
                    │  (Body/Breath)  │
                    │                 │
                    │  Breath Engine  │
                    │     🜂 🜂 🜂      │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐      ┌────────▼───────┐
        │ REALITY SIM    │      │  DJINN KERNEL  │
        │ (Left Wing)    │      │ (Right Wing)   │
        │                │      │                │
        │ Organisms      │      │ VP Monitoring  │
        │ Networks       │      │ Trait Engine   │
        │ Evolution      │      │ UUID Anchor    │
        └────────────────┘      └────────────────┘
```

---

## 🔄 Data Flow

```
Breath Cycle (Explorer)
    │
    ├─> Breathe() → Breath State
    │
    ├─> Reality Simulator
    │   └─> network.update_network()
    │       └─> Organisms evolve
    │       └─> Network metrics update
    │       └─> State logged
    │
    ├─> Antennae (Collective Sensing) ⭐ NEW
    │   └─> antennae.sense(organisms, report)
    │       └─> Aggregate organism states
    │       └─> Update beliefs from outcomes
    │   └─> antennae.influence(config_tuner)
    │       └─> Generate governance signal
    │       └─> Apply parameter adjustments
    │
    ├─> Language System
    │   └─> atomic_language.check_mastery_advancement()
    │       └─> Check breadth (usage frequency)
    │       └─> Check depth (associations formed)
    │       └─> Advance level if criteria met
    │       └─> Add behavior-specialized words
    │
    ├─> Alliance Warfare (Dune Paradigm)
    │   └─> alliance_warfare.process_organism_alliance_decisions()
    │       └─> Calculate behavioral signatures
    │       └─> Find most divergent alliance
    │       └─> Neural propose_war decision
    │       └─> Curiosity drives conflict
    │
    ├─> Djinn Kernel
    │   └─> vp_monitor.compute_violation_pressure()
    │       └─> VP calculated from traits
    │       └─> VP classified (VP0-VP4)
    │       └─> State logged
    │
    └─> Explorer
        └─> Normal Genesis/Sovereign operation
        └─> VP history tracked
        └─> Mathematical capability assessed
```

---

## 🎯 Component Relationships

### Language Mastery (Vocabulary Progression) ⭐ NEW

**Responsibilities:**
- Track vocabulary usage (breadth)
- Track associations formed (depth)
- Gate vocabulary expansion
- Behavior-driven word selection

**Mastery Levels:**
| Level | Name | Words | Breadth | Depth |
|-------|------|-------|---------|-------|
| 0 | Novice | 6 | - | - |
| 1 | Adept | 26 | 50% used 3+ times | 30% have 2+ associations |
| 2 | Scholar | 76 | same | same |
| 3 | Master | 276 | same | same |
| 4 | Grandmaster | ∞ | same | same |

**Behavior-Driven Specialization:**
- Warriors (high compete) → combat, battle, dominate words
- Diplomats (high cooperate) → alliance, trust, negotiate words
- Explorers (high move) → discover, wander, journey words
- Hermits (high isolate) → solitude, withdraw, meditate words

**Dependencies:**
- AtomicLanguage (word storage)
- Neural organism (behavioral fingerprint)
- Innate vocabulary frames

### Alliance Warfare (Dune Paradigm) ⭐ NEW

**Philosophy:**
> "Your existence questions mine. Let us resolve through contest."

**Responsibilities:**
- Calculate behavioral signatures for alliances
- Measure behavioral divergence (cosine distance)
- Drive war proposals from curiosity, not resources

**War Driver Formula:**
```
score = curiosity*0.35 + divergence*0.35 + compete*0.2 + (1-cooperate)*0.1
threshold = 0.45 * (1 + skepticism*0.3)
if score > threshold: propose_war()
```

**Dependencies:**
- PlanetaryAlliance (member management)
- Neural organism (propose_war decision)
- Organism behavioral fingerprints

### Antennae (Self-Governance) ⭐ NEW

**Responsibilities:**
- Collective sensing (aggregate organism states)
- Governance signal generation
- Belief tracking and updating
- Health prediction (Kleene convergence)
- Automatic parameter tuning

**Dependencies:**
- Reality Simulator (organisms, network)
- AtomicConfigSystem (parameter adjustment)
- SystemReport (population analytics)

**Exports:**
- AntennaReading (9-dimensional perception)
- GovernanceSignal (6-dimensional tuning)
- Belief system state
- Health predictor insights

### Explorer (Central Body)

**Responsibilities:**
- Breath engine (primary driver)
- System coordination
- VP tracking and certification
- Phase management (Genesis/Sovereign)

**Dependencies:**
- Reality Simulator (imported)
- Djinn Kernel (imported)

**Exports:**
- Breath state
- VP history
- Phase state

### Reality Simulator (Left Wing)

**Responsibilities:**
- Organism evolution
- Network formation
- Collapse detection
- Network metrics
- **🧠 Neural System**: PyTorch-based learning for organisms

**Dependencies:**
- None (standalone, imported by Explorer)
- Optional: PyTorch (for neural features)

**Exports:**
- Network metrics (organisms, connections, modularity, clustering)
- Generation state
- Collapse status
- Neural metrics (training loss, epsilon, training steps)

### Djinn Kernel (Right Wing)

**Responsibilities:**
- VP calculation
- Trait convergence
- Identity anchoring
- Mathematical governance

**VP Monitoring Features:**
- **Diagnostics**: Detailed logging of VP components (optional)
- **Stabilization**: Smoothing to prevent immediate saturation (optional)
- **Component Decomposition**: Weighted breakdown of VP sources (optional)
- **Adaptive Thresholds**: Phase-aware threshold adjustment (optional)

**Dependencies:**
- None (standalone, imported by Explorer)

**Exports:**
- VP values
- VP classification
- Trait convergence status
- VP diagnostic data (if enabled)
- Component breakdown (if decomposition enabled)

---

## 🔗 Integration Points

### 1. Import Level

```python
# Explorer imports both
from main import RealitySimulator
from utm_kernel_design import UTMKernel
from violation_pressure_calculation import ViolationMonitor
```

### 2. Initialization Level

```python
# Explorer initializes both
self.reality_sim = RealitySimulator(config_path='../config.json')
self.utm_kernel = UTMKernel()
self.vp_monitor = ViolationMonitor()
```

### 3. Execution Level

```python
# Breath drives both
breath_data = self.breath_engine.breathe()
network.update_network()  # Reality Sim
vp = vp_monitor.compute_violation_pressure(traits)  # Djinn Kernel
```

### 4. State Level

```python
# Unified state collection
reality_sim_state = get_reality_sim_state()
explorer_state = get_explorer_state()
djinn_kernel_state = get_djinn_kernel_state()
```

---

## 🦋 Language Model System Architecture ⭐ NEW

### Overview

The Butterfly System includes a **complete neural language model (LLM) integration** that enables organisms to develop emergent language through token-based communication. The system integrates seamlessly with existing neural networks, causation tracking, and the web UI.

### Components

```
reality_simulator/language/
  ├─> language_system.py     # LanguageVocabulary, tokenizers
  └─> butterfly_chat.py      # ButterflyChatRouter (user→organism chat)

reality_simulator/neural/
  ├─> brain.py               # OrganismBrain with MultiHeadAttention + language head
  ├─> neural_organism.py     # Sequence modeling, generate_tokens()
  └─> trainer.py             # Dual-loss training (DQN + language)

reality_simulator/memory/
  └─> context_memory.py      # language_anchors, word associations

reality_simulator/symbiotic_network.py
  └─> LinguisticSubgraph    # Protected linguistic connections
```

### Architecture Flow

```
Organism State (18 features)
    ↓
OrganismBrain.forward()
    ↓
MultiHeadAttention (VP-aware temperature scaling)
    ↓
Dual Heads:
  ├─> Action Head → RL decisions
  └─> Language Head → Next-token prediction
    ↓
Token Generation (autoregressive)
    ↓
Vocabulary.decode() → Response text
    ↓
Event Emission → Causation Graph
```

### Key Features

- **Multi-Head Self-Attention**: VP-aware temperature scaling (`scores / (1.0 + vp_value)`)
- **Dual-Head Architecture**: Action head (RL) + Language head (next-token prediction)
- **Dynamic Vocabulary**: Grows from organism interactions via `language_anchors`
- **Token Exchange**: Organisms communicate via `LinguisticSubgraph`
- **VP Integration**: Violation pressure affects language generation
- **Curriculum Learning**: Sequence length increases based on VP stability
- **Butterfly Chat**: Direct user→organism communication interface

### Vocabulary Learning

**Current Status:** ⚠️ **CRITICAL GAP IDENTIFIED**

The system has vocabulary management but **no automatic word learning mechanism**. Words need to be associated with organisms through a "Language Teacher" system.

**Proposed Solution:** See [docs/LANGUAGE_TEACHER_ARCHITECTURE_PROPOSAL.md](./docs/LANGUAGE_TEACHER_ARCHITECTURE_PROPOSAL.md)

**Options:**
1. **Behavior-Based Mapping** (Simple): Map organism actions/states to words
2. **Embedding-Based Grounding** (Recommended): Use learned embeddings to map states→words
3. **Transformer Teacher** (Advanced): Sequence-aware word learning

### Integration Points

- **ContextMemory**: Stores `language_anchors` (word→organism mappings)
- **SymbioticNetwork**: `LinguisticSubgraph` for protected linguistic connections
- **Neural Trainer**: Dual-loss training (alpha * DQN + beta * language)
- **Causation Graph**: Language events tracked (`vocabulary_growth`, `organism_communication`, `neural_language_training`, `butterfly_chat_message`, `butterfly_chat_response`)
- **Web UI**: Butterfly Chat interface for direct organism communication

### Configuration

```json
{
  "neural": {
    "language_model": {
      "enabled": false,  // Master toggle
      "attention": {
        "enabled": true,
        "num_heads": 4,
        "attention_dim": 32
      },
      "vocabulary": {
        "max_size": 1024
      },
      "training": {
        "alpha": 0.9,  // DQN loss weight
        "beta": 0.1,   // Language loss weight
        "vp_temperature_scale": true
      }
    }
  }
}
```

---

## 🧠 Neural System Architecture

### Components

```
reality_simulator/neural/
  ├─> brain.py              # OrganismBrain (PyTorch nn.Module)
  ├─> neural_organism.py    # NeuralOrganism (extends Organism)
  ├─> trainer.py            # NeuralTrainer (DQN training)
  ├─> experience.py         # ExperienceBuffer (replay buffer)
  ├─> utils.py              # Device detection, feature extraction
  └─> __init__.py           # Module exports
```

### Neural Organism Lifecycle

```
1. Creation (Evolution Engine)
   ├─> Check config['neural']['enabled']
   ├─> If True: Create NeuralOrganism
   │   ├─> Initialize OrganismBrain
   │   ├─> Create ExperienceBuffer
   │   └─> Set epsilon (exploration rate)
   └─> If False: Create standard Organism

2. Decision Making (decide_action)
   ├─> Extract state features (fitness, resources, connections, breath)
   ├─> Forward pass through brain → Q-values
   ├─> Epsilon-greedy action selection
   ├─> Store prev_state and prev_action
   └─> Emit neural_decision event (if confidence > 0.8)

3. Experience Collection (trainer.collect_experiences)
   ├─> Calculate reward (fitness change, survival, connections, resources)
   ├─> Get next state
   └─> Record experience (state, action, reward, next_state)

4. Training (trainer.train_step)
   ├─> Check update_frequency (skip if not time)
   ├─> Sample batch from experience buffer
   ├─> Calculate DQN loss (MSE between Q and target Q)
   ├─> Backpropagation
   └─> Emit neural_training event

5. Reproduction (Evolution Engine)
   ├─> Brain inheritance (if parent has brain)
   │   ├─> Crossover: Blend parent brains
   │   └─> Mutation: Random weight perturbations
   └─> Create new NeuralOrganism with inherited brain
```

### Breath Synchronization

```
Breath Cycle
  ├─> Breath "Inhale" Phase (depth > threshold)
  │   └─> Neural Training Triggered
  │       ├─> collect_experiences()
  │       └─> train_step() (if update_frequency allows)
  │
  └─> Breath "Exhale" Phase
      └─> Organisms make decisions (using learned policies)
```

### Dual Inheritance (Lamarckian Evolution)

```
Standard Evolution (Darwinian):
  Parent Genotype → Child Genotype (genetic code only)

Neural Evolution (Lamarckian):
  Parent Genotype + Parent Brain → Child Genotype + Child Brain
  ├─> Genetic crossover (standard)
  ├─> Brain crossover (blend neural weights)
  └─> Brain mutation (perturb weights)
  
Result: Learned behaviors can be inherited!
```

## 📊 State Synchronization

### Breath State (Primary Driver)

```
Breath Engine
  ├─> breath_depth: 0.0-1.0
  ├─> breath_phase: 0.0-2π
  ├─> breath_cycle: int
  └─> breath_pulse: depth × intensity
```

### Reality Simulator State

```
Network Metrics
  ├─> organism_count: int
  ├─> connection_count: int
  ├─> modularity: float
  ├─> clustering_coefficient: float
  ├─> average_path_length: float
  └─> generation: int

Neural Metrics 🧠 NEW
  ├─> enabled: bool
  ├─> training_loss: float
  ├─> avg_epsilon: float (exploration rate)
  ├─> organisms_tracked: int
  ├─> training_steps: int
  └─> avg_loss: float
```

### Explorer State

```
Explorer Metrics
  ├─> phase: 'genesis' | 'sovereign'
  ├─> vp_calculations: int
  ├─> sovereign_ids_count: int
  ├─> mathematical_capability: bool
  └─> breath_state: dict
```

### Djinn Kernel State

```
VP Metrics
  ├─> violation_pressure: float
  ├─> vp_classification: 'VP0' | 'VP1' | 'VP2' | 'VP3' | 'VP4'
  ├─> vp_calculations: int
  └─> trait_count: int
```

---

## 🎨 Visualization Architecture

```
Unified Visualization (1920x1080)
  │
  ├─> Left Panel (Cyan)
  │   └─> Reality Simulator
  │       ├─> Organism count
  │       ├─> Connection count
  │       ├─> Modularity
  │       └─> Clustering
  │
  ├─> Middle Panel (Yellow)
  │   └─> Explorer
  │       ├─> Phase
  │       ├─> VP calculations
  │       ├─> Breath cycle
  │       └─> Breath depth
  │
  └─> Right Panel (Magenta)
      └─> Djinn Kernel
          ├─> VP value
          ├─> VP classification
          └─> VP calculations
```

---

## 📝 Logging Architecture

```
State Logger
  │
  ├─> state.log (all states)
  ├─> breath.log (breath cycles)
  ├─> reality_sim.log (network metrics)
  ├─> explorer.log (Explorer state)
  ├─> djinn_kernel.log (VP calculations)
  ├─> neural.log (neural training metrics) 🧠 NEW
  └─> system.log (system events)

Format: timestamp|level|component|metric:value|metric:value|...
```

---

## 🔄 Event Flow

### Normal Operation

```
1. Breath Cycle Starts
   └─> breath_engine.breathe()
   
2. Reality Simulator Reacts
   └─> network.update_network()
   └─> One generation evolves
   
3. Djinn Kernel Reacts
   └─> vp_monitor.compute_violation_pressure()
   └─> One VP calculation
   
4. States Logged
   └─> All states written to log files
   
5. Visualization Updates
   └─> All panels refresh
   
6. Next Breath Cycle
```

### Transition Event

```
1. Any System Hits Threshold
   ├─> Reality Sim: 500 organisms + modularity < 0.3
   ├─> Explorer: 50 VP calculations + mathematical capability
   └─> Djinn Kernel: VP < 0.25 (VP0)
   
2. Unified Transition Triggered
   └─> All systems transition to precision phase
   
3. Breath Rate Adjusts
   └─> Slower, more stable breathing
   
4. States Synchronized
   └─> All systems in precision phase
```

---

## 🎯 Key Design Principles

### 1. Occam's Razor
- Simplest possible integration
- Just imports and method calls
- No bridges, no IPC, no complexity

### 2. Breath-Driven
- Breath is the primary driver
- All systems react to breath
- Unified state through breath

### 3. Unified State
- All systems share breath state
- States logged together
- Visualization shows all states

### 4. Graceful Degradation
- Systems work independently if needed
- Optional dependencies handled gracefully
- Warnings, not failures

---

## 📐 System Boundaries

### Explorer Boundary
- **Owns:** Breath engine, VP tracking, phase management
- **Imports:** Reality Simulator, Djinn Kernel
- **Coordinates:** All three systems

### Reality Simulator Boundary
- **Owns:** Organisms, networks, evolution
- **Exports:** Network metrics
- **Independent:** Can run standalone

### Djinn Kernel Boundary
- **Owns:** VP calculation, trait engine, identity
- **Exports:** VP values, classifications
- **Independent:** Can run standalone

---

## 🔐 Integration Contracts

### Reality Simulator Contract
```python
# Must provide:
- RealitySimulator(config_path) → instance
- instance.initialize_simulation() → bool
- instance.components['network'] → network object
- network.update_network() → dict
- network.organisms → dict
- network.metrics.modularity → float
```

### Djinn Kernel Contract
```python
# Must provide:
- UTMKernel() → instance
- ViolationMonitor() → instance
- monitor.compute_violation_pressure(traits) → (float, dict)
- monitor._classify_violation_pressure(vp) → ViolationClass
- monitor.vp_history → list
```

### Explorer Contract
```python
# Must provide:
- BiphasicController() → instance
- controller.breath_engine → BreathEngine
- controller.run_genesis_phase() → bool
- controller.sentinel.vp_history → list
- controller.kernel.get_sovereign_ids() → list
```

---

## 🎨 Visualization Contract

```python
# UnifiedVisualization must:
- initialize() → None
- update(reality_sim_state, explorer_state, djinn_kernel_state) → None
- running: bool (indicates if visualization is active)
```

---

## 📊 Logging Contract

```python
# StateLogger must:
- log_state(component, state) → None
- log_breath(breath_data) → None
- log_reality_sim(network_data) → None
- log_explorer(explorer_data) → None
- log_djinn_kernel(kernel_data) → None
```

---

## 🔄 Lifecycle

### Initialization
1. Pre-flight checks
2. Logging system initialized
3. Visualization initialized (if enabled)
4. Explorer initialized
5. Reality Simulator initialized (via Explorer)
6. Djinn Kernel initialized (via Explorer)

### Operation
1. Breath cycle starts
2. Systems react
3. States collected
4. States logged
5. Visualization updated
6. Repeat

### Shutdown
1. Graceful exit signal
2. Final states logged
3. Systems shut down
4. Logs saved

---

## 🎯 Architecture Principles

1. **Single Process:** One Python process, not three
2. **Breath-Driven:** Breath is the primary driver
3. **Unified State:** All systems share state through breath
4. **Graceful Degradation:** Systems work independently if needed
5. **Occam's Razor:** Simplest possible integration

---

## 📚 Integration Approaches

### Occam's Razor Integration

**Principle:** "Entities should not be multiplied beyond necessity"

**Implementation:**
- Explorer imports Reality Simulator and Djinn Kernel
- No bridges, no IPC, no complexity
- Just imports and method calls
- Breath drives both systems

**Result:** Simplest possible integration with maximum functionality

### Three-System Architecture

**Reality Simulator:**
- Organism substrate
- Network evolution
- Collapse detection at ~500 organisms

**Explorer:**
- Governance and coordination
- Breath engine (primary driver)
- VP tracking and certification

**Djinn Kernel:**
- Trait framework
- VP monitoring
- Mathematical validation

**Unified:** All three systems share the breath state

### Chaos → Precision Transition

**Universal Pattern:**
- Reality Simulator: 500 organisms (distributed → consolidated)
- Explorer: 50 VP calculations (Genesis → Sovereign)
- Djinn Kernel: VP < 0.25 (divergence → convergence)

**Ratio:** 500:50 = 10:1 (exploration-to-precision conversion factor)

**Trigger:** When ANY system hits threshold, ALL transition

---

---

## 🔧 Code Quality & Production Readiness

### Error Handling

**Status:** ✅ Professional error handling throughout

- ✅ All bare `except:` clauses replaced with specific exception types
- ✅ Proper exception handling patterns in all critical paths
- ✅ Better error visibility and debugging capability

**Files Updated:**
- `reality_simulator/symbiotic_network.py` - NetworkX operations
- `explorer/main.py` - VP calculation
- `reality_simulator/agency/agency_router.py` - State collection (5 locations)

### Logging Infrastructure

**Status:** ✅ Centralized logging configuration

**Two Complementary Systems:**

1. **Application Logging** (`logging_config.py`)
   - Centralized configuration (`setup_logging()`)
   - Module-level loggers (`get_logger(name)`)
   - Support for console and file logging
   - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
   - UTF-8 encoding for file handlers

2. **State Logging** (`StateLogger` in `unified_entry.py`)
   - Terse, information-saturated format
   - System metrics and monitoring
   - 6 log files for different components

**Benefits:**
- Cleaner console output (debug controlled by log levels)
- Professional logging infrastructure
- Consistent logging patterns across modules
- Better production readiness

### Testing

**Status:** ✅ Comprehensive test coverage

**Test Suite:**
- ✅ **End-to-End Tests** (`tests/test_e2e_unified_system.py`)
  - Pre-flight checks test
  - UnifiedSystem initialization test
  - State retrieval methods test
  - Run method logic test
  - Missing controller handling test
  - State logger test
  - Import paths test
  - PreFlightChecker structure test

- ✅ **Reality Simulator Tests** (59+ test functions)
  - Component tests for all major systems
  - Integration tests
  - Network collapse tests

- ✅ **Explorer Tests** (5 test functions)
  - Integration tests

- ✅ **Agency Router + Event Bus Tests** (4 test functions)
  - Integration tests

**Total Test Coverage:** ~85+ test functions

**All tests passing** ✅

### Production Readiness

**Status:** ✅ Production-ready standards met

- ✅ Professional error handling
- ✅ Centralized logging infrastructure
- ✅ Comprehensive test coverage
- ✅ Code quality improvements
- ✅ Best practices followed
- ✅ Clean, maintainable code

**For more details, see [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)**

