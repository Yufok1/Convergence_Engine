# 🚦 Event Bus vs Agency Router: Two Complementary Systems

**Understanding the difference and how they work together**

---

## What is an Event Bus?

An **event bus** is a publish-subscribe messaging system that allows components to communicate asynchronously without direct coupling.

### Our Event Bus: `DjinnEventBus`

**Location:** `kernel/event_driven_coordination.py`

**How it works:**
```python
# Publisher (any component)
event_bus.publish(ViolationPressureEvent(vp=0.3, trait="organism_count"))

# Subscriber (any component)
event_bus.subscribe(EventType.VIOLATION_PRESSURE, my_handler_function)

# Handler is called automatically when event is published
def my_handler_function(event):
    print(f"VP changed: {event.vp}")
```

**Key Features:**
- **Asynchronous**: Events are queued and processed asynchronously
- **Decoupled**: Publishers don't know who subscribes
- **Broadcast**: One event can trigger multiple handlers
- **Event History**: All events are logged for audit trail
- **Type-based**: Events are categorized by `EventType` enum

**Event Types:**
- `IDENTITY_COMPLETION` - UUID anchoring events
- `VIOLATION_PRESSURE` - VP calculation events
- `SYSTEM_HEALTH` - Health monitoring events
- `TEMPORAL_ISOLATION` - Safety/quarantine events
- `AGENT_COMMUNICATION` - Agent coordination events
- `TRAIT_CONVERGENCE` - Trait convergence events
- `ARBITRATION_TRIGGER` - Arbitration events
- `AGENCY_DECISION` - Agency router decisions

---

## What is the Agency Router?

The **agency router** is a **synchronous decision-making coordinator** that routes decisions to appropriate system-driven decision makers.

### Our Agency Router: `AgencyRouter`

**Location:** `reality_simulator/agency/agency_router.py`

**How it works:**
```python
# Request a decision (synchronous)
decision = agency_router.make_decision(
    decision_type="network_connection",
    context={
        'org_a_id': 'org_123',
        'org_b_id': 'org_456',
        'compatibility_score': 0.67,
        'explorer_vp': 0.35,
        'djinn_kernel_vp': 0.28,
        'network_modularity': 0.45
    },
    options=["connect_immediate", "connect_delayed", "reject"]
)

# Returns: "connect_immediate" (based on system state)
```

**Key Features:**
- **Synchronous**: Returns decision immediately
- **State-aware**: Uses current system state (VP, phase, metrics)
- **System-driven**: Routes to Explorer, Djinn Kernel, or Reality Sim
- **Granular**: Fine-grained decision options
- **Consensus**: Can use unified consensus voting
- **Logged**: All decisions are logged

**Decision Types:**
- `network_connection` - Should organisms connect?
- `resource_allocation` - How to allocate resources?
- `organism_selection` - Which organism to select?
- `phase_transition` - When to transition?
- `trait_translation` - How to translate traits?

---

## Comparison

| Aspect | Event Bus | Agency Router |
|--------|-----------|---------------|
| **Pattern** | Publish-Subscribe | Request-Response |
| **Timing** | Asynchronous | Synchronous |
| **Purpose** | **Notification** ("something happened") | **Decision** ("what should I do?") |
| **Coupling** | Decoupled (publisher doesn't know subscribers) | Coupled (caller waits for response) |
| **Direction** | One-to-many (broadcast) | One-to-one (direct) |
| **State** | Event-driven (reactive) | State-driven (proactive) |
| **Use Case** | "Tell everyone VP changed" | "Should I connect these organisms?" |

---

## How They Work Together

### Event Bus: "What Happened?"

**Example: Network Collapse Detected**
```python
# Reality Simulator detects collapse
if network_collapsed:
    event_bus.publish(NetworkCollapseEvent(
        organism_count=500,
        modularity=0.28,
        timestamp=time.time()
    ))

# Multiple subscribers react:
# - Explorer: "Oh! Time to transition to Sovereign phase"
# - Djinn Kernel: "Oh! Traits converged, VP should drop"
# - Phase Sync Bridge: "Oh! Update transition state"
```

**Flow:**
1. Event published → 2. All subscribers notified → 3. Each reacts independently

---

### Agency Router: "What Should I Do?"

**Example: Connection Decision**
```python
# Network needs to decide: connect or not?
decision = agency_router.make_decision(
    decision_type="network_connection",
    context={
        'org_a_id': 'org_123',
        'org_b_id': 'org_456',
        'explorer_vp': 0.35,
        'djinn_kernel_vp': 0.28,
        'network_modularity': 0.45
    },
    options=["connect_immediate", "connect_delayed", "reject"]
)

# Agency router:
# 1. Checks system state
# 2. Routes to appropriate decision maker (Explorer/Djinn/Reality Sim)
# 3. Returns decision: "connect_immediate"
# 4. Network executes decision
```

**Flow:**
1. Request decision → 2. Router checks state → 3. Routes to system → 4. Returns decision → 5. Caller executes

---

## Integration Example

**Combined Usage:**
```python
# 1. Agency Router makes decision
decision = agency_router.make_decision(
    "network_connection",
    context,
    options
)

# 2. Network executes decision
if decision == "connect_immediate":
    network.add_connection(org_a, org_b)
    
    # 3. Event Bus notifies everyone (automatic via Agency Router)
    # Agency Router automatically publishes decision events
```

**Flow:**
1. Agency Router makes decision → 2. Decision executed → 3. Event Bus automatically notified → 4. Subscribers react

---

## When to Use Each

### Use Event Bus When:
- ✅ **Something happened** (state change, event occurred)
- ✅ **Multiple systems need to know** (broadcast)
- ✅ **Asynchronous is OK** (don't need immediate response)
- ✅ **Decoupling is important** (publisher doesn't care who listens)

**Examples:**
- Network collapse detected → notify all systems
- VP threshold crossed → trigger monitoring
- Phase transition occurred → update all state
- Connection formed → log for causation tracking

### Use Agency Router When:
- ✅ **Need a decision** (what should I do?)
- ✅ **Need immediate answer** (synchronous)
- ✅ **State-aware decision** (use current system state)
- ✅ **Granular control** (fine-grained options)

**Examples:**
- Should organisms connect? → route to system decision maker
- How to allocate resources? → use VP/phase to decide
- When to transition? → check all system readiness
- Which organism to select? → use network metrics

---

## Current Integration Status

### Event Bus (`DjinnEventBus`)
- ✅ **Implemented** in `kernel/event_driven_coordination.py`
- ✅ **Used by** UTM Kernel for agent coordination
- ✅ **Used by** System Coordinator for system-wide events
- ✅ **WIRED** into Agency Router (all decisions publish events automatically)
- ✅ **Auto-initialized** from UTM Kernel in Reality Simulator

### Agency Router (`AgencyRouter`)
- ✅ **Implemented** in `reality_simulator/agency/agency_router.py`
- ✅ **System decision makers** created (Explorer, Djinn Kernel, Reality Sim)
- ✅ **Wired into** network connection formation
- ✅ **WIRED** to Event Bus (all decisions publish events automatically)
- ✅ **Integrated** into Reality Simulator initialization
- ✅ **Event Bus integration** complete

---

## ✅ Integration Complete!

**The Agency Router now publishes events to the Event Bus automatically:**

```python
class AgencyRouter:
    def __init__(self, ..., event_bus=None):
        self.event_bus = event_bus  # Auto-initialized from UTM Kernel
    
    def make_decision(self, decision_type, context, options):
        # Make decision
        decision = self._route_to_system(...)
        
        # Publish decision event (automatic)
        self._publish_decision_event(
            decision_type, decision, options, context, routing_mode, response_time
        )
        
        return decision
```

**Benefits (Now Realized):**
1. ✅ **Agency Router** makes decisions (synchronous, state-aware)
2. ✅ **Event Bus** notifies everyone (asynchronous, decoupled)
3. ✅ **Best of both worlds**: Immediate decisions + reactive notifications
4. ✅ **Full audit trail**: All decisions logged automatically
5. ✅ **Causation tracking**: Events feed into Akashic Ledger

---

## Summary

**Event Bus:**
- "Something happened" → "Tell everyone"
- Asynchronous, decoupled, broadcast
- Used for notifications and reactions

**Agency Router:**
- "What should I do?" → "Here's the decision"
- Synchronous, state-aware, direct
- Used for decisions and coordination

**Together:**
- Agency Router makes decisions → Event Bus notifies everyone
- Perfect complement: decisions + notifications

---

**Status: ✅ Fully integrated and operational!**

