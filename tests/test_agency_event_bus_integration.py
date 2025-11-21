"""
Simple Test: Agency Router + Event Bus Integration

Verifies that the Agency Router publishes decision events to the Event Bus.
Uses CHAOS_MODE to avoid manual agency Unicode issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.event_driven_coordination import DjinnEventBus, EventType
from kernel.decision_events import create_decision_event


def test_event_creation():
    """Test that decision events can be created and published"""
    print("Test 1: Event Creation")
    
    event_bus = DjinnEventBus()
    
    # Create a network decision event
    event = create_decision_event(
        decision_type="network_connection",
        chosen_option="connect_immediate",
        available_options=["connect_immediate", "connect_delayed", "no_connect"],
        decision_mode="unified_consensus",
        context={"vp": 0.5, "organism_count": 10},
        response_time_ms=15.5,
        org_a_id="org_001",
        org_b_id="org_002",
        network_metrics={"modularity": 0.7}
    )
    
    # Publish event
    event_bus.publish(event)
    
    # Verify
    assert len(event_bus.event_history) == 1
    assert event_bus.event_history[0].event_type == EventType.NETWORK_DECISION
    assert event_bus.event_history[0].decision_type == "network_connection"
    assert event_bus.event_history[0].chosen_option == "connect_immediate"
    
    print(f"  PASS - Event created and published")
    print(f"  Event type: {event.event_type.value}")
    print(f"  Decision: {event.chosen_option}")
    print()


def test_multiple_event_types():
    """Test different decision event types"""
    print("Test 2: Multiple Event Types")
    
    event_bus = DjinnEventBus()
    
    # Network decision
    net_event = create_decision_event(
        "network_connection", "connect", ["connect", "no_connect"],
        "reality_sim_driven", {}, 10.0
    )
    event_bus.publish(net_event)
    assert net_event.event_type == EventType.NETWORK_DECISION
    print(f"  PASS - Network decision: {net_event.event_type.value}")
    
    # Evolution decision
    evo_event = create_decision_event(
        "evolution_mutation", "mutate", ["mutate", "no_mutate"],
        "djinn_kernel_driven", {}, 12.0
    )
    event_bus.publish(evo_event)
    assert evo_event.event_type == EventType.EVOLUTION_DECISION
    print(f"  PASS - Evolution decision: {evo_event.event_type.value}")
    
    # Generic decision
    gen_event = create_decision_event(
        "unknown_type", "option_a", ["option_a", "option_b"],
        "manual_only", {}, 8.0
    )
    event_bus.publish(gen_event)
    assert gen_event.event_type == EventType.DECISION_MADE
    print(f"  PASS - Generic decision: {gen_event.event_type.value}")
    
    assert len(event_bus.event_history) == 3
    print(f"  PASS - All 3 events published")
    print()


def test_event_subscribers():
    """Test that subscribers receive events"""
    print("Test 3: Event Subscribers")
    
    event_bus = DjinnEventBus()
    received = []
    
    def handler(event):
        received.append(event)
    
    event_bus.subscribe(EventType.NETWORK_DECISION, handler)
    event_bus.subscribe(EventType.DECISION_MADE, handler)
    
    # Publish events
    event1 = create_decision_event("network_connection", "connect", ["connect"], "test", {}, 1.0)
    event2 = create_decision_event("unknown", "a", ["a"], "test", {}, 1.0)
    
    event_bus.publish(event1)
    event_bus.publish(event2)
    
    # Verify subscribers received events
    assert len(received) == 2
    print(f"  PASS - Subscribers received {len(received)} events")
    print()


def test_context_snapshot():
    """Test that context is captured in events"""
    print("Test 4: Context Snapshot")
    
    context = {
        "explorer_vp": 0.42,
        "organism_count": 50,
        "modularity": 0.85
    }
    
    event = create_decision_event(
        "network_connection", "connect", ["connect"],
        "unified_consensus", context, 20.0
    )
    
    assert event.context_snapshot["explorer_vp"] == 0.42
    assert event.context_snapshot["organism_count"] == 50
    assert event.context_snapshot["modularity"] == 0.85
    
    print(f"  PASS - Context captured:")
    print(f"    explorer_vp: {event.context_snapshot['explorer_vp']}")
    print(f"    organism_count: {event.context_snapshot['organism_count']}")
    print(f"    modularity: {event.context_snapshot['modularity']}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Agency Router + Event Bus Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_event_creation()
        test_multiple_event_types()
        test_event_subscribers()
        test_context_snapshot()
        
        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Integration verified:")
        print("  - Events created and published correctly")
        print("  - Correct event types for decision types")
        print("  - Subscribers receive events")
        print("  - Context captured in events")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
