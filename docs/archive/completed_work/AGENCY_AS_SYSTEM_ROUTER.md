# 🚦 Agency Router as Unified System Decision Coordinator

**Repurposing agency router to route decisions between Explorer, Djinn Kernel, and Reality Simulator**

---

## Current State

**Agency Router:**
- Designed for manual vs AI routing
- AI agents removed → always routes to manual
- Has decision routing configuration
- Has performance tracking
- Has mode switching

**Manual Agency:**
- Human-in-the-loop decisions
- Strategy presets (conservative, balanced, innovative, chaos)
- Decision logging
- Batch processing

---

## The Insight

**Now that AI agents are removed, the agency system can be repurposed to:**

1. **Route decisions between the three systems** (Explorer, Djinn Kernel, Reality Sim)
2. **Make granular system-driven decisions** instead of human input
3. **Coordinate decisions** based on system state (VP, phase, network metrics)
4. **Use system intelligence** instead of AI intelligence

---

## New Agency Modes

### Instead of: Manual vs AI
### Now: System-Driven Decision Routing

```python
class SystemAgencyMode(Enum):
    """Decision-making modes based on system state"""
    EXPLORER_DRIVEN = "explorer_driven"      # Explorer makes decision (VP-based)
    DJINN_KERNEL_DRIVEN = "djinn_kernel_driven"  # Djinn Kernel makes decision (trait-based)
    REALITY_SIM_DRIVEN = "reality_sim_driven"    # Reality Sim makes decision (network-based)
    UNIFIED_CONSENSUS = "unified_consensus"      # All three systems vote
    BREATH_DRIVEN = "breath_driven"             # Breath engine decides (rhythm-based)
    CHAOS_MODE = "chaos_mode"                   # Random/exploratory decisions
```

---

## Granular Decision Types

### Network Decisions
1. **Connection Formation**
   - Should organism A connect to organism B?
   - Options: `["connect", "reject", "defer"]`
   - Context: organism traits, network state, VP

2. **Connection Removal**
   - Should connection be removed?
   - Options: `["remove", "keep", "strengthen"]`
   - Context: connection health, network stability

3. **Resource Allocation**
   - How to allocate resources?
   - Options: `["equal", "fitness_based", "connection_based", "random"]`
   - Context: organism fitness, connection strength

4. **Organism Selection**
   - Which organism to select for operation?
   - Options: `["fittest", "most_connected", "random", "least_connected"]`
   - Context: network topology, organism fitness

### Phase Transition Decisions
5. **Transition Timing**
   - When to trigger chaos→precision transition?
   - Options: `["now", "wait", "accelerate"]`
   - Context: system readiness, VP levels

6. **System Coordination**
   - Which system should lead?
   - Options: `["explorer", "djinn_kernel", "reality_sim", "unified"]`
   - Context: system state, phase alignment

### Trait Decisions
7. **Trait Translation**
   - How to translate traits between systems?
   - Options: `["direct", "normalized", "weighted", "filtered"]`
   - Context: trait types, system compatibility

8. **VP Calculation Method**
   - Which VP calculation to use?
   - Options: `["explorer_vp", "djinn_kernel_vp", "unified_vp", "weighted"]`
   - Context: system phase, trait availability

---

## Decision Routing Logic

### By System State

**Explorer-Driven:**
- When: Explorer in Genesis phase, VP calculations < 50
- Decision style: Exploratory, experimental
- Use for: Connection formation, resource allocation

**Djinn Kernel-Driven:**
- When: VP < 0.25 (VP0), traits converged
- Decision style: Lawful, precise
- Use for: Critical decisions, phase transitions

**Reality Sim-Driven:**
- When: Network metrics stable, organisms < 500
- Decision style: Physics-based, network-aware
- Use for: Network topology, connection management

**Unified Consensus:**
- When: All systems in precision phase
- Decision style: Coordinated, balanced
- Use for: Major transitions, system coordination

**Breath-Driven:**
- When: Breath cycle phase (inhale/exhale)
- Decision style: Rhythmic, synchronized
- Use for: Timing decisions, cycle coordination

**Chaos Mode:**
- When: Early phase, exploration needed
- Decision style: Random, exploratory
- Use for: Initial connections, discovery

---

## Implementation Strategy

### 1. Repurpose AgencyMode Enum
```python
class SystemAgencyMode(Enum):
    EXPLORER_DRIVEN = "explorer_driven"
    DJINN_KERNEL_DRIVEN = "djinn_kernel_driven"
    REALITY_SIM_DRIVEN = "reality_sim_driven"
    UNIFIED_CONSENSUS = "unified_consensus"
    BREATH_DRIVEN = "breath_driven"
    CHAOS_MODE = "chaos_mode"
```

### 2. Create System Decision Makers
```python
class ExplorerDecisionMaker:
    """Makes decisions based on Explorer state"""
    def make_decision(self, decision_type, context, options):
        # Use Explorer's VP, phase, breath state
        pass

class DjinnKernelDecisionMaker:
    """Makes decisions based on Djinn Kernel state"""
    def make_decision(self, decision_type, context, options):
        # Use VP, trait convergence, UTM state
        pass

class RealitySimDecisionMaker:
    """Makes decisions based on Reality Sim state"""
    def make_decision(self, decision_type, context, options):
        # Use network metrics, organism state
        pass
```

### 3. Update Agency Router
```python
class AgencyRouter:
    def __init__(self, explorer, djinn_kernel, reality_sim, breath_engine):
        self.explorer = explorer
        self.djinn_kernel = djinn_kernel
        self.reality_sim = reality_sim
        self.breath_engine = breath_engine
        
        # System decision makers
        self.explorer_maker = ExplorerDecisionMaker(explorer)
        self.djinn_maker = DjinnKernelDecisionMaker(djinn_kernel)
        self.reality_maker = RealitySimDecisionMaker(reality_sim)
        
    def make_decision(self, decision_type, context, options):
        # Determine which system should decide
        mode = self._determine_mode(decision_type, context)
        
        # Route to appropriate system
        if mode == SystemAgencyMode.EXPLORER_DRIVEN:
            return self.explorer_maker.make_decision(decision_type, context, options)
        elif mode == SystemAgencyMode.DJINN_KERNEL_DRIVEN:
            return self.djinn_maker.make_decision(decision_type, context, options)
        # ... etc
```

---

## Granular Decision Examples

### Connection Formation (Granular)
```python
# Context includes:
context = {
    'org_a_id': 'org_123',
    'org_b_id': 'org_456',
    'org_a_fitness': 0.75,
    'org_b_fitness': 0.82,
    'org_a_connections': 3,
    'org_b_connections': 5,
    'network_modularity': 0.45,
    'network_clustering': 0.3,
    'explorer_vp': 0.35,
    'djinn_kernel_vp': 0.28,
    'breath_phase': 'inhale',
    'explorer_phase': 'genesis',
    'distance': 2.3,  # Network distance
    'compatibility_score': 0.67
}

# Options:
options = [
    "connect_immediate",      # Connect now
    "connect_delayed",         # Connect next cycle
    "reject",                  # Don't connect
    "connect_conditional",     # Connect if conditions met
    "defer_to_explorer",       # Let Explorer decide
    "defer_to_djinn_kernel"    # Let Djinn Kernel decide
]

# Decision routing:
if explorer_phase == 'genesis' and explorer_vp < 0.5:
    # Explorer-driven: More exploratory connections
    return "connect_immediate" if compatibility_score > 0.5 else "connect_delayed"
elif djinn_kernel_vp < 0.25:
    # Djinn Kernel-driven: Lawful, precise connections
    return "connect_immediate" if compatibility_score > 0.8 else "reject"
elif network_modularity < 0.3:
    # Reality Sim-driven: Network-aware connections
    return "connect_immediate" if distance < 2.0 else "reject"
```

---

## Integration Points

### 1. Network Connection Decisions
- Replace random connection attempts with agency routing
- Use system state to determine connection strategy
- Log all connection decisions

### 2. Resource Allocation
- Route resource decisions based on system phase
- Use VP to weight resource distribution
- Coordinate across all three systems

### 3. Phase Transitions
- Agency router decides when to transition
- Coordinates transition timing across systems
- Logs transition decisions

### 4. Trait Translation
- Routes trait translation decisions
- Chooses translation method based on system state
- Tracks translation quality

---

## Benefits

1. **Granular Control**: Fine-grained decisions instead of binary
2. **System Intelligence**: Uses actual system state, not AI
3. **Coordination**: Routes decisions to appropriate system
4. **Traceability**: All decisions logged and trackable
5. **Adaptability**: Decisions adapt to system phase and state

---

## ✅ Integration Complete!

**Status: Agency Router fully repurposed and integrated with Event Bus**

### Implementation Status:
- ✅ System decision makers created (`system_decision_makers.py`)
- ✅ Agency Router repurposed for system-driven decisions
- ✅ Network connection decisions routed through agency
- ✅ Event Bus integration complete
- ✅ All decisions automatically publish events
- ✅ Full audit trail enabled

### Next Steps:
- Wire into Explorer's breath loop (future enhancement)
- Add more decision types as needed
- Subscribe systems to AgencyDecisionEvent for reactive behavior

