"""
Decision Events for Agency Router Integration

Event types published when the Agency Router makes decisions.
These events enable asynchronous notification of all decision outcomes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from .event_driven_coordination import DjinnEvent, EventType


@dataclass
class DecisionMadeEvent(DjinnEvent):
    """
    Published when any decision is made by the Agency Router.
    
    This is the base event for all decision types, providing:
    - Decision type and chosen option
    - Available options that were considered
    - Decision mode used (e.g., unified_consensus, explorer_driven)
    - Context snapshot at decision time
    - Confidence score (if applicable)
    """
    decision_type: str = ""
    chosen_option: str = ""
    available_options: List[str] = field(default_factory=list)
    decision_mode: str = ""  # e.g., "unified_consensus", "explorer_driven"
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    response_time_ms: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.DECISION_MADE
        self.priority = 2  # High priority - drives system coordination
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "decision_type": self.decision_type,
            "chosen_option": self.chosen_option,
            "available_options": self.available_options,
            "decision_mode": self.decision_mode,
            "context_snapshot": self.context_snapshot,
            "confidence": self.confidence,
            "response_time_ms": self.response_time_ms
        })
        return base_dict


@dataclass
class NetworkDecisionEvent(DecisionMadeEvent):
    """
    Published for network-related decisions (connections, resource allocation, etc.)
    
    Includes network-specific context:
    - Organism IDs involved
    - Network metrics at decision time
    - Connection/relationship details
    """
    org_a_id: Optional[str] = None
    org_b_id: Optional[str] = None
    network_metrics: Dict[str, float] = field(default_factory=dict)
    connection_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.NETWORK_DECISION
        self.priority = 2
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "org_a_id": self.org_a_id,
            "org_b_id": self.org_b_id,
            "network_metrics": self.network_metrics,
            "connection_details": self.connection_details
        })
        return base_dict


@dataclass
class EvolutionDecisionEvent(DecisionMadeEvent):
    """
    Published for evolution/mutation decisions.
    
    Includes evolution-specific context:
    - Organism ID being mutated
    - Mutation type
    - Trait changes
    - Fitness impact
    """
    organism_id: Optional[str] = None
    mutation_type: Optional[str] = None
    trait_changes: Dict[str, Any] = field(default_factory=dict)
    fitness_before: float = 0.0
    fitness_after: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.EVOLUTION_DECISION
        self.priority = 2
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "organism_id": self.organism_id,
            "mutation_type": self.mutation_type,
            "trait_changes": self.trait_changes,
            "fitness_before": self.fitness_before,
            "fitness_after": self.fitness_after
        })
        return base_dict


@dataclass
class PhaseTransitionDecisionEvent(DecisionMadeEvent):
    """
    Published for phase transition decisions (genesis → emergence, etc.)
    
    Includes phase-specific context:
    - Current phase
    - Target phase
    - Transition criteria met
    - System state at transition
    """
    current_phase: str = ""
    target_phase: str = ""
    transition_criteria: Dict[str, bool] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.DECISION_MADE  # Use base type for now
        self.priority = 3  # Critical - phase transitions are important
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "current_phase": self.current_phase,
            "target_phase": self.target_phase,
            "transition_criteria": self.transition_criteria,
            "system_state": self.system_state
        })
        return base_dict


# Utility functions

def create_decision_event(decision_type: str, chosen_option: str,
                         available_options: List[str], decision_mode: str,
                         context: Dict[str, Any], response_time_ms: float = 0.0,
                         **kwargs) -> DecisionMadeEvent:
    """
    Factory function to create the appropriate decision event type.
    
    Args:
        decision_type: Type of decision (e.g., "network_connection")
        chosen_option: The option that was chosen
        available_options: All options that were available
        decision_mode: Mode used to make decision (e.g., "unified_consensus")
        context: Decision context snapshot
        response_time_ms: Time taken to make decision (milliseconds)
        **kwargs: Additional event-specific parameters
    
    Returns:
        Appropriate DecisionMadeEvent subclass
    """
    # Network-related decisions
    if decision_type in ["network_connection", "resource_allocation", "organism_selection"]:
        return NetworkDecisionEvent(
            decision_type=decision_type,
            chosen_option=chosen_option,
            available_options=available_options,
            decision_mode=decision_mode,
            context_snapshot=context,
            response_time_ms=response_time_ms,
            org_a_id=kwargs.get("org_a_id"),
            org_b_id=kwargs.get("org_b_id"),
            network_metrics=kwargs.get("network_metrics", {}),
            connection_details=kwargs.get("connection_details", {})
        )
    
    # Evolution-related decisions
    elif decision_type in ["evolution_mutation", "trait_translation"]:
        return EvolutionDecisionEvent(
            decision_type=decision_type,
            chosen_option=chosen_option,
            available_options=available_options,
            decision_mode=decision_mode,
            context_snapshot=context,
            response_time_ms=response_time_ms,
            organism_id=kwargs.get("organism_id"),
            mutation_type=kwargs.get("mutation_type"),
            trait_changes=kwargs.get("trait_changes", {}),
            fitness_before=kwargs.get("fitness_before", 0.0),
            fitness_after=kwargs.get("fitness_after", 0.0)
        )
    
    # Phase transition decisions
    elif decision_type == "phase_transition":
        return PhaseTransitionDecisionEvent(
            decision_type=decision_type,
            chosen_option=chosen_option,
            available_options=available_options,
            decision_mode=decision_mode,
            context_snapshot=context,
            response_time_ms=response_time_ms,
            current_phase=kwargs.get("current_phase", ""),
            target_phase=kwargs.get("target_phase", ""),
            transition_criteria=kwargs.get("transition_criteria", {}),
            system_state=kwargs.get("system_state", {})
        )
    
    # Default: base DecisionMadeEvent
    else:
        return DecisionMadeEvent(
            decision_type=decision_type,
            chosen_option=chosen_option,
            available_options=available_options,
            decision_mode=decision_mode,
            context_snapshot=context,
            response_time_ms=response_time_ms
        )
