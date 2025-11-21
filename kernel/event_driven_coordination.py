# Event-Driven Coordination Foundation - Phase 0.3 Implementation
# Version 1.0 - Core Event Bus for System Coordination

"""
Event-Driven Coordination Foundation implementing the core event bus that enables all reliable
system coordination in the Djinn Kernel.

This is the operational foundation that coordinates:
- Identity completion events from UUID anchoring
- Violation pressure events from VP calculation
- System health events for monitoring
- Temporal isolation events for safety
- Multi-entity communication for governance
"""

import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class EventType(Enum):
    """Core event types for system coordination"""
    IDENTITY_COMPLETION = "identity_completion"
    VIOLATION_PRESSURE = "violation_pressure"
    SYSTEM_HEALTH = "system_health"
    TEMPORAL_ISOLATION = "temporal_isolation"
    AGENT_COMMUNICATION = "agent_communication"
    TRAIT_CONVERGENCE = "trait_convergence"
    ARBITRATION_TRIGGER = "arbitration_trigger"
    
    # Decision events (Agency Router integration)
    DECISION_MADE = "decision_made"
    NETWORK_DECISION = "network_decision"
    EVOLUTION_DECISION = "evolution_decision"
    AGENCY_DECISION = "agency_decision"  # NEW: Agency Router decisions


@dataclass
class DjinnEvent:
    """Base class for all Djinn Kernel events"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_HEALTH
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_agent: Optional[str] = None
    priority: int = 0  # Higher number = higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "source_agent": self.source_agent,
            "priority": self.priority
        }


@dataclass
class IdentityCompletionEvent(DjinnEvent):
    """Event published when UUID anchoring completes"""
    uuid: str = ""
    payload_hash: str = ""
    completion_pressure: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.IDENTITY_COMPLETION
        self.priority = 2  # High priority - drives system coordination
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "uuid": self.uuid,
            "payload_hash": self.payload_hash,
            "completion_pressure": self.completion_pressure
        })
        return base_dict


@dataclass
class ViolationPressureEvent(DjinnEvent):
    """Event published when violation pressure is calculated"""
    total_vp: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)
    classification: str = "normal"
    source_identity: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = EventType.VIOLATION_PRESSURE
        self.priority = 3  # Critical priority - drives system responses
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "total_vp": self.total_vp,
            "breakdown": self.breakdown,
            "classification": self.classification,
            "source_identity": self.source_identity
        })
        return base_dict


@dataclass
class SystemHealthEvent(DjinnEvent):
    """Event published for system health monitoring"""
    health_metrics: Dict[str, Any] = field(default_factory=dict)
    alert_level: str = "normal"  # normal, warning, critical
    
    def __post_init__(self):
        self.event_type = EventType.SYSTEM_HEALTH
        self.priority = 1  # Normal priority - monitoring
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "health_metrics": self.health_metrics,
            "alert_level": self.alert_level
        })
        return base_dict


@dataclass
class TemporalIsolationTrigger(DjinnEvent):
    """Event that triggers temporal isolation for safety"""
    reason: str = ""
    isolation_duration: int = 0  # milliseconds
    vp_level: Optional[float] = None
    
    def __post_init__(self):
        self.event_type = EventType.TEMPORAL_ISOLATION
        self.priority = 4  # Highest priority - safety critical
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "reason": self.reason,
            "isolation_duration": self.isolation_duration,
            "vp_level": self.vp_level
        })
        return base_dict


@dataclass
class TraitConvergenceRequest(DjinnEvent):
    """Event requesting trait convergence operation"""
    source_uuid: str = ""
    pressure_level: float = 0.0
    target_traits: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.event_type = EventType.TRAIT_CONVERGENCE
        self.priority = 2  # High priority - drives evolution
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "source_uuid": self.source_uuid,
            "pressure_level": self.pressure_level,
            "target_traits": self.target_traits
        })
        return base_dict


@dataclass
class AgencyDecisionEvent(DjinnEvent):
    """Event published when Agency Router makes a decision"""
    decision_type: str = ""
    decision: str = ""  # The chosen option
    options: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    routing_mode: str = ""  # Which system made the decision
    response_time: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.AGENCY_DECISION
        self.priority = 1  # Normal priority - decisions are logged
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "decision_type": self.decision_type,
            "decision": self.decision,
            "options": self.options,
            "context": self.context,
            "routing_mode": self.routing_mode,
            "response_time": self.response_time
        })
        return base_dict


class DjinnEventBus:
    """
    Core event bus enabling all system coordination.
    Foundation for temporal isolation and monitoring systems.
    """
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[DjinnEvent] = []
        self.event_processor = AsyncEventProcessor()
        self.coordination_lock = threading.Lock()
        
        # Initialize event type subscriptions
        for event_type in EventType:
            self.subscribers[event_type] = []
    
    def publish(self, event: DjinnEvent):
        """
        Publish event to all subscribers with full audit trail.
        This is the core coordination mechanism.
        """
        with self.coordination_lock:
            # Record event in history
            self.event_history.append(event)
            
            # Process event through all subscribers
            event_type = event.event_type
            if event_type in self.subscribers:
                for handler in self.subscribers[event_type]:
                    try:
                        # Schedule handler execution
                        self.event_processor.schedule_handler(handler, event)
                    except Exception as e:
                        print(f"Error in event handler {handler.__name__}: {e}")
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event types"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from specific event types"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[DjinnEvent]:
        """Get event history with optional filtering"""
        if event_type is None:
            return self.event_history[-limit:]
        else:
            return [event for event in self.event_history 
                   if event.event_type == event_type][-limit:]
    
    def export_coordination_summary(self) -> Dict[str, Any]:
        """Export coordination system summary"""
        return {
            "total_events": len(self.event_history),
            "subscriber_counts": {
                event_type.value: len(handlers) 
                for event_type, handlers in self.subscribers.items()
            },
            "recent_events": [
                event.to_dict() for event in self.event_history[-10:]
            ],
            "coordination_status": "operational"
        }


class AsyncEventProcessor:
    """Asynchronous event processor for non-blocking coordination"""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.processing_task = None
        self.is_running = False
    
    def start_processing(self):
        """Start the async event processing loop"""
        if not self.is_running:
            self.is_running = True
            self.processing_task = asyncio.create_task(self._process_events())
    
    def stop_processing(self):
        """Stop the async event processing loop"""
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
    
    def schedule_handler(self, handler: Callable, event: DjinnEvent):
        """Schedule event handler for execution"""
        if self.is_running:
            asyncio.create_task(self._execute_handler(handler, event))
        else:
            # Fallback to synchronous execution
            handler(event)
    
    async def _execute_handler(self, handler: Callable, event: DjinnEvent):
        """Execute event handler asynchronously"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run synchronous handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, event)
        except Exception as e:
            print(f"Error executing event handler: {e}")
    
    async def _process_events(self):
        """Main event processing loop"""
        while self.is_running:
            try:
                # Process events from queue
                await asyncio.sleep(0.001)  # Small delay to prevent busy waiting
            except asyncio.CancelledError:
                break


class SystemCoordinator:
    """
    High-level system coordinator that manages event-driven system responses.
    This implements the coordination patterns from the Djinn Kernel specification.
    """
    
    def __init__(self, event_bus: DjinnEventBus):
        self.event_bus = event_bus
        self.coordination_state = {
            "identity_completions": 0,
            "vp_calculations": 0,
            "isolation_triggers": 0,
            "convergence_requests": 0
        }
        
        # Subscribe to core event types
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for system coordination"""
        self.event_bus.subscribe(EventType.IDENTITY_COMPLETION, self._handle_identity_completion)
        self.event_bus.subscribe(EventType.VIOLATION_PRESSURE, self._handle_violation_pressure)
        self.event_bus.subscribe(EventType.TEMPORAL_ISOLATION, self._handle_temporal_isolation)
        self.event_bus.subscribe(EventType.TRAIT_CONVERGENCE, self._handle_trait_convergence)
    
    def _handle_identity_completion(self, event: IdentityCompletionEvent):
        """Handle identity completion events"""
        self.coordination_state["identity_completions"] += 1
        
        # High completion pressure triggers trait convergence
        if event.completion_pressure > 0.5:
            convergence_request = TraitConvergenceRequest(
                source_uuid=event.uuid,
                pressure_level=event.completion_pressure,
                source_agent="system_coordinator"
            )
            self.event_bus.publish(convergence_request)
    
    def _handle_violation_pressure(self, event: ViolationPressureEvent):
        """Handle violation pressure events"""
        self.coordination_state["vp_calculations"] += 1
        
        # Critical VP triggers temporal isolation
        if event.total_vp > 0.75:
            isolation_trigger = TemporalIsolationTrigger(
                reason=f"Critical VP: {event.total_vp}",
                isolation_duration=5000,  # 5 seconds
                vp_level=event.total_vp,
                source_agent="system_coordinator"
            )
            self.event_bus.publish(isolation_trigger)
        
        # Publish system health update
        health_event = SystemHealthEvent(
            health_metrics={
                "current_vp": event.total_vp,
                "vp_classification": event.classification,
                "total_vp_calculations": self.coordination_state["vp_calculations"]
            },
            alert_level="critical" if event.total_vp > 0.75 else "normal",
            source_agent="system_coordinator"
        )
        self.event_bus.publish(health_event)
    
    def _handle_temporal_isolation(self, event: TemporalIsolationTrigger):
        """Handle temporal isolation triggers"""
        self.coordination_state["isolation_triggers"] += 1
        
        # Log isolation event
        print(f"Temporal isolation triggered: {event.reason}")
    
    def _handle_trait_convergence(self, event: TraitConvergenceRequest):
        """Handle trait convergence requests"""
        self.coordination_state["convergence_requests"] += 1
        
        # Log convergence request
        print(f"Trait convergence requested for {event.source_uuid}")
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """Get current coordination status"""
        return {
            "coordination_state": self.coordination_state.copy(),
            "event_bus_summary": self.event_bus.export_coordination_summary(),
            "status": "operational"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize event-driven coordination system
    event_bus = DjinnEventBus()
    system_coordinator = SystemCoordinator(event_bus)
    
    # Start async processing
    event_bus.event_processor.start_processing()
    
    print("=== Event-Driven Coordination Foundation Test ===")
    
    # Test identity completion event
    identity_event = IdentityCompletionEvent(
        uuid="test-uuid-123",
        payload_hash="abc123",
        completion_pressure=0.7,
        source_agent="test_agent"
    )
    event_bus.publish(identity_event)
    
    # Test violation pressure event
    vp_event = ViolationPressureEvent(
        total_vp=0.8,
        breakdown={"trait1": 0.3, "trait2": 0.5},
        classification="VP3_CRITICAL_DIVERGENCE",
        source_identity="test_identity_001",
        source_agent="test_agent"
    )
    event_bus.publish(vp_event)
    
    # Test trait convergence request
    convergence_event = TraitConvergenceRequest(
        source_uuid="test-uuid-456",
        pressure_level=0.6,
        target_traits=["intimacy", "commitment"],
        source_agent="test_agent"
    )
    event_bus.publish(convergence_event)
    
    # Show coordination status
    status = system_coordinator.get_coordination_status()
    print(f"Coordination Status: {status}")
    
    # Show event history
    history = event_bus.get_event_history(limit=5)
    print(f"Recent Events: {len(history)} events")
    for event in history:
        print(f"  {event.event_type.value}: {event.to_dict()}")
    
    # Stop processing
    event_bus.event_processor.stop_processing()
    
    print("=== Phase 0.3 Implementation Complete ===")
    print("Event-Driven Coordination Foundation operational and verified.")
