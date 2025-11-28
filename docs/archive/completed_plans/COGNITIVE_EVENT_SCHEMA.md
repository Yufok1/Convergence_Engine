# 🧠 Cognitive Event Schema

**Structured event definitions for cognitive agent operations**

---

## Event Types

### Goal Events

```python
@dataclass
class GoalSetEvent:
    """Agent set a new goal"""
    event_type: str = "goal_set"
    agent_id: str
    goal_id: str
    goal_description: str
    priority: float  # 0.0-1.0
    deadline: Optional[datetime] = None
    parent_goal_id: Optional[str] = None  # For hierarchical goals
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Intention Events

```python
@dataclass
class IntentionFormedEvent:
    """Agent formed an intention to act"""
    event_type: str = "intention_formed"
    agent_id: str
    intention_id: str
    goal_id: str  # Which goal this serves
    action_type: str  # "tool_execution", "coordination", "reflection"
    target: str  # What/who the action targets
    expected_outcome: str
    confidence: float  # 0.0-1.0
    reasoning: str  # Why this intention
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Action Events

```python
@dataclass
class ActionExecutedEvent:
    """Agent executed an action"""
    event_type: str = "action_executed"
    agent_id: str
    action_id: str
    intention_id: str
    action_type: str
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float
    success: bool
    result: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Reflection Events

```python
@dataclass
class ReflectionRecordedEvent:
    """Agent reflected on an action"""
    event_type: str = "reflection_recorded"
    agent_id: str
    reflection_id: str
    action_id: str
    intention_id: str
    goal_id: str
    
    # Reflection content
    expected_outcome: str
    actual_outcome: str
    deviation: float  # 0.0-1.0: How different was actual from expected
    success: bool
    
    # Learning
    lessons_learned: List[str]
    capability_updates: Dict[str, float]  # capability_name -> new_confidence
    cause_of_deviation: Optional[str] = None  # "tool_failure", "planning_error", "capability_overestimate", etc.
    
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Capability Events

```python
@dataclass
class CapabilityUpdatedEvent:
    """Agent updated a capability confidence"""
    event_type: str = "capability_updated"
    agent_id: str
    capability_name: str
    old_confidence: float
    new_confidence: float
    reason: str  # "success", "failure", "calibration", "decay"
    reflection_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Planning Events

```python
@dataclass
class PlanCreatedEvent:
    """Agent created a hierarchical plan"""
    event_type: str = "plan_created"
    agent_id: str
    plan_id: str
    goal_id: str
    task_count: int
    estimated_duration_seconds: float
    dependencies: List[Tuple[str, str]]  # [(task_a, task_b)] = task_b depends on task_a
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PlanTaskCompletedEvent:
    """Agent completed a plan task"""
    event_type: str = "plan_task_completed"
    agent_id: str
    plan_id: str
    task_id: str
    success: bool
    next_tasks: List[str]  # Tasks now unblocked
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Safety Events

```python
@dataclass
class SafetyCheckEvent:
    """Safety policy check performed"""
    event_type: str = "safety_check"
    agent_id: str
    action_id: str
    policy_rules_checked: List[str]
    risk_score: float  # 0.0-1.0
    allowed: bool
    violations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionBlockedEvent:
    """Action was blocked by safety system"""
    event_type: str = "action_blocked"
    agent_id: str
    action_id: str
    reason: str
    policy_rule: str
    risk_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Coordination Events

```python
@dataclass
class TaskDelegatedEvent:
    """Agent delegated a task to another agent"""
    event_type: str = "task_delegated"
    delegator_id: str
    delegatee_id: str
    task_id: str
    goal_id: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CoordinationConflictEvent:
    """Conflict detected in multi-agent coordination"""
    event_type: str = "coordination_conflict"
    agent_ids: List[str]
    conflict_type: str  # "resource_contention", "goal_conflict", "task_preemption"
    resolution: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Event Publishing

### Integration with Event Bus

```python
from kernel.event_driven_coordination import DjinnEventBus, EventType

# Extend EventType enum
class CognitiveEventType(Enum):
    GOAL_SET = "goal_set"
    INTENTION_FORMED = "intention_formed"
    ACTION_EXECUTED = "action_executed"
    REFLECTION_RECORDED = "reflection_recorded"
    CAPABILITY_UPDATED = "capability_updated"
    PLAN_CREATED = "plan_created"
    SAFETY_CHECK = "safety_check"
    ACTION_BLOCKED = "action_blocked"
    TASK_DELEGATED = "task_delegated"
    COORDINATION_CONFLICT = "coordination_conflict"

# Publish cognitive events
event_bus.publish(
    EventType.COGNITIVE,  # Or new CognitiveEventType
    GoalSetEvent(
        agent_id="agent_123",
        goal_id="goal_456",
        goal_description="Research neural architectures",
        priority=0.8
    )
)
```

### Causation Explorer Integration

```python
# Cognitive events automatically feed into causation graph
from causation_explorer import CausationExplorer

explorer.add_event(Event(
    timestamp=datetime.now(),
    component="cognitive_agent",
    event_type="goal_set",
    data={
        "agent_id": "agent_123",
        "goal_id": "goal_456",
        "goal_description": "Research neural architectures",
        "priority": 0.8
    }
))
```

---

## Event Subscriptions

### Subscribe to System Events

```python
# Agent subscribes to VP changes for pacing
event_bus.subscribe(EventType.VIOLATION_PRESSURE, handle_vp_change)

def handle_vp_change(event):
    """Adjust agent behavior based on VP"""
    if event.vp > 0.7:
        # High VP: Reduce exploration, focus on stability
        agent.set_exploration_rate(0.1)
    else:
        # Low VP: Normal exploration
        agent.set_exploration_rate(0.3)

# Agent subscribes to breath cycles for reflection timing
event_bus.subscribe(EventType.BREATH_CYCLE, handle_breath_cycle)

def handle_breath_cycle(event):
    """Reflect only on breath exhale"""
    if event.breath_phase == "exhale":
        agent.trigger_reflection()
```

---

## Metrics Extraction

### From Events

```python
# Goal completion rate
goal_events = [e for e in events if e.event_type == "goal_set"]
completion_events = [e for e in events if e.event_type == "goal_completed"]
completion_rate = len(completion_events) / len(goal_events)

# Average reflection latency
reflections = [e for e in events if e.event_type == "reflection_recorded"]
actions = {e.action_id: e.timestamp for e in events if e.event_type == "action_executed"}
latencies = [
    (r.timestamp - actions[r.action_id]).total_seconds()
    for r in reflections
    if r.action_id in actions
]
avg_latency = sum(latencies) / len(latencies) if latencies else 0

# Capability confidence drift
capability_updates = [e for e in events if e.event_type == "capability_updated"]
drifts = [abs(e.new_confidence - e.old_confidence) for e in capability_updates]
avg_drift = sum(drifts) / len(drifts) if drifts else 0
```

---

## Event Persistence

### Serialization

```python
import json
from dataclasses import asdict

def serialize_cognitive_event(event) -> str:
    """Serialize cognitive event to JSON"""
    data = asdict(event)
    # Convert datetime to ISO string
    if isinstance(data.get('timestamp'), datetime):
        data['timestamp'] = data['timestamp'].isoformat()
    return json.dumps(data)

def deserialize_cognitive_event(json_str: str, event_class):
    """Deserialize cognitive event from JSON"""
    data = json.loads(json_str)
    # Convert ISO string to datetime
    if 'timestamp' in data:
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    return event_class(**data)
```

### State Recovery

```python
# Save agent cognitive state
def save_cognitive_state(agent, filepath: Path):
    state = {
        'self_model': asdict(agent.self_model),
        'active_goals': [asdict(g) for g in agent.intentionality.active_goals.values()],
        'recent_reflections': [serialize_cognitive_event(r) for r in agent.reflection.recent_reflections[-100:]],
        'capabilities': {name: asdict(cap) for name, cap in agent.self_model.capabilities.items()}
    }
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2, default=str)

# Load agent cognitive state
def load_cognitive_state(agent, filepath: Path):
    with open(filepath, 'r') as f:
        state = json.load(f)
    
    # Restore self model
    agent.self_model = SelfModel(**state['self_model'])
    
    # Restore goals
    for goal_data in state['active_goals']:
        goal = Goal(**goal_data)
        agent.intentionality.active_goals[goal.goal_id] = goal
    
    # Restore reflections
    agent.reflection.recent_reflections = [
        deserialize_cognitive_event(r, ReflectionRecordedEvent)
        for r in state['recent_reflections']
    ]
```

---

## Integration Points

### Causation Explorer

All cognitive events automatically appear in causation graph:
- Goal → Intention → Action → Reflection chains
- Capability updates linked to reflections
- Planning dependencies visualized
- Safety blocks shown as failed actions

### VP Monitoring

Cognitive events can influence VP:
- High agent error rates → VP increase
- Successful coordination → VP decrease
- Capability calibration failures → trait divergence

### CRA Integration

CRA can subscribe to cognitive events:
- Monitor agent performance
- Suggest capability adjustments
- Identify coordination issues
- Provide adaptive recommendations

---

**Status:** Ready for implementation in Phase 0 (Safety & Instrumentation)

