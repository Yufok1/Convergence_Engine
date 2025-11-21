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

**Dependencies:**
- None (standalone, imported by Explorer)

**Exports:**
- Network metrics (organisms, connections, modularity, clustering)
- Generation state
- Collapse status

### Djinn Kernel (Right Wing)

**Responsibilities:**
- VP calculation
- Trait convergence
- Identity anchoring
- Mathematical governance

**Dependencies:**
- None (standalone, imported by Explorer)

**Exports:**
- VP values
- VP classification
- Trait convergence status

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

