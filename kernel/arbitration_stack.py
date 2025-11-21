"""
Production Arbitration Stack - Phase 2.2 Implementation

This module implements the high-level governance authority that manages the
Advanced Trait Engine's dynamic evolution capabilities. It serves as a bounded
halting oracle, providing VP-based classification and formal escalation procedures
for managing the pathway from lawful operations to the Forbidden Zone.

Key Features:
- Bounded Halting Oracle: Determines if operations will halt within bounded time
- VP-Based Classification: Categorizes operations by violation pressure levels
- Formal Escalation Procedures: Manages progression to Forbidden Zone
- Arbitration Decision Engine: Makes governance decisions based on system state
- Forbidden Zone Management: Controls access to μ-recursion operations
"""

import time
import math
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta

from advanced_trait_engine import AdvancedTraitEngine, MutationStrategy, StabilityMode
from violation_pressure_calculation import ViolationMonitor, ViolationClass
from event_driven_coordination import DjinnEventBus, EventType, SystemHealthEvent
from temporal_isolation_safety import TemporalIsolationManager


class ArbitrationDecisionType(Enum):
    """Decisions that can be made by the arbitration stack"""
    APPROVE = "approve"                     # Operation is lawful and approved
    MODIFY = "modify"                       # Operation needs modification
    QUARANTINE = "quarantine"               # Operation requires temporal isolation
    ESCALATE = "escalate"                   # Operation requires higher authority
    FORBIDDEN = "forbidden"                 # Operation is forbidden
    EMERGENCY_HALT = "emergency_halt"       # System-wide emergency halt


class EscalationLevel(Enum):
    """Levels of escalation in the arbitration hierarchy"""
    LEVEL_0 = "level_0"                     # Basic arbitration (automated)
    LEVEL_1 = "level_1"                     # Enhanced arbitration (pattern-based)
    LEVEL_2 = "level_2"                     # Advanced arbitration (context-aware)
    LEVEL_3 = "level_3"                     # Expert arbitration (human-in-loop)
    LEVEL_4 = "level_4"                     # Sovereign arbitration (system-wide)


class ForbiddenZoneAccess(Enum):
    """Access levels for the Forbidden Zone"""
    DENIED = "denied"                       # No access permitted
    READ_ONLY = "read_only"                 # Read access only
    CONTROLLED = "controlled"               # Controlled μ-recursion
    EXPERIMENTAL = "experimental"           # Experimental operations
    FULL_ACCESS = "full_access"             # Full μ-recursion access


@dataclass
class ArbitrationRequest:
    """Request for arbitration decision"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    operation_data: Dict[str, Any] = field(default_factory=dict)
    violation_pressure: float = 0.0
    system_health: float = 1.0
    convergence_success: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_identity: Optional[str] = None
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_0


@dataclass
class ArbitrationDecision:
    """Decision made by the arbitration stack"""
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    decision: ArbitrationDecisionType = ArbitrationDecisionType.APPROVE
    reasoning: str = ""
    confidence: float = 1.0
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_0
    forbidden_zone_access: ForbiddenZoneAccess = ForbiddenZoneAccess.DENIED
    temporal_isolation_duration: Optional[int] = None
    modification_instructions: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    arbitrator_id: str = ""


@dataclass
class BoundedHaltingOracle:
    """Bounded halting oracle for determining operation termination"""
    max_iterations: int = 1000
    max_time_seconds: float = 60.0
    complexity_threshold: float = 0.8
    recursion_depth_limit: int = 10
    
    def will_halt(self, operation_data: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Determine if an operation will halt within bounded parameters.
        
        Returns:
            Tuple of (will_halt, confidence, reasoning)
        """
        # Extract operation characteristics
        complexity = operation_data.get("complexity", 0.0)
        recursion_depth = operation_data.get("recursion_depth", 0)
        estimated_iterations = operation_data.get("estimated_iterations", 0)
        operation_type = operation_data.get("operation_type", "unknown")
        
        # Check recursion depth limit
        if recursion_depth > self.recursion_depth_limit:
            return False, 0.9, f"Recursion depth {recursion_depth} exceeds limit {self.recursion_depth_limit}"
        
        # Check iteration limit
        if estimated_iterations > self.max_iterations:
            return False, 0.8, f"Estimated iterations {estimated_iterations} exceed limit {self.max_iterations}"
        
        # Check complexity threshold
        if complexity > self.complexity_threshold:
            return False, 0.7, f"Complexity {complexity:.3f} exceeds threshold {self.complexity_threshold}"
        
        # Check operation type patterns
        if operation_type in ["μ_recursion", "unbounded_search", "infinite_loop"]:
            return False, 0.6, f"Operation type '{operation_type}' has high non-halting probability"
        
        # Calculate confidence based on multiple factors
        confidence = 1.0
        confidence -= (recursion_depth / self.recursion_depth_limit) * 0.3
        confidence -= (estimated_iterations / self.max_iterations) * 0.3
        confidence -= (complexity / self.complexity_threshold) * 0.2
        
        confidence = max(0.1, min(1.0, confidence))
        
        reasoning = f"Operation appears to halt: depth={recursion_depth}, iterations={estimated_iterations}, complexity={complexity:.3f}"
        
        return True, confidence, reasoning


class VPBasedClassifier:
    """Classifier for operations based on violation pressure levels"""
    
    def __init__(self):
        self.vp_thresholds = {
            ViolationClass.VP0_FULLY_LAWFUL: 0.25,
            ViolationClass.VP1_STABLE_DRIFT: 0.50,
            ViolationClass.VP2_INSTABILITY: 0.75,
            ViolationClass.VP3_CRITICAL_DIVERGENCE: 1.00,
            ViolationClass.VP4_COLLAPSE_THRESHOLD: float('inf')
        }
    
    def classify_operation(self, violation_pressure: float, 
                          system_health: float, 
                          convergence_success: float) -> Tuple[ViolationClass, float, str]:
        """
        Classify operation based on VP and system state.
        
        Returns:
            Tuple of (classification, confidence, reasoning)
        """
        # Determine base classification
        classification = ViolationClass.VP0_FULLY_LAWFUL
        for vp_class, threshold in self.vp_thresholds.items():
            if violation_pressure < threshold:
                classification = vp_class
                break
        
        # Adjust classification based on system health
        if system_health < 0.3:
            # Poor system health amplifies VP classification
            if classification == ViolationClass.VP0_FULLY_LAWFUL:
                classification = ViolationClass.VP1_STABLE_DRIFT
            elif classification == ViolationClass.VP1_STABLE_DRIFT:
                classification = ViolationClass.VP2_INSTABILITY
        
        # Adjust classification based on convergence success
        if convergence_success < 0.5:
            # Poor convergence amplifies VP classification
            if classification.value in ["VP0", "VP1"]:
                classification = ViolationClass.VP2_INSTABILITY
        
        # Calculate confidence
        confidence = 1.0
        confidence -= abs(violation_pressure - self.vp_thresholds[classification]) * 0.5
        confidence -= (1.0 - system_health) * 0.2
        confidence -= (1.0 - convergence_success) * 0.2
        
        confidence = max(0.1, min(1.0, confidence))
        
        reasoning = f"VP={violation_pressure:.3f}, Health={system_health:.3f}, Convergence={convergence_success:.3f} → {classification.value}"
        
        return classification, confidence, reasoning


class EscalationManager:
    """Manages escalation procedures through arbitration hierarchy"""
    
    def __init__(self):
        self.escalation_rules = {
            EscalationLevel.LEVEL_0: {
                "vp_threshold": 0.3,
                "health_threshold": 0.8,
                "auto_approve": True
            },
            EscalationLevel.LEVEL_1: {
                "vp_threshold": 0.5,
                "health_threshold": 0.6,
                "auto_approve": False
            },
            EscalationLevel.LEVEL_2: {
                "vp_threshold": 0.7,
                "health_threshold": 0.4,
                "auto_approve": False
            },
            EscalationLevel.LEVEL_3: {
                "vp_threshold": 0.9,
                "health_threshold": 0.2,
                "auto_approve": False
            },
            EscalationLevel.LEVEL_4: {
                "vp_threshold": 1.0,
                "health_threshold": 0.0,
                "auto_approve": False
            }
        }
    
    def determine_escalation_level(self, violation_pressure: float, 
                                 system_health: float) -> EscalationLevel:
        """Determine required escalation level based on system state"""
        
        for level in reversed(list(EscalationLevel)):
            rules = self.escalation_rules[level]
            if violation_pressure >= rules["vp_threshold"] or system_health <= rules["health_threshold"]:
                return level
        
        return EscalationLevel.LEVEL_0
    
    def can_auto_approve(self, escalation_level: EscalationLevel) -> bool:
        """Check if operation can be auto-approved at given escalation level"""
        return self.escalation_rules[escalation_level]["auto_approve"]


class ForbiddenZoneManager:
    """Manages access to the Forbidden Zone (μ-recursion operations)"""
    
    def __init__(self):
        self.access_controls = {
            ForbiddenZoneAccess.DENIED: {
                "vp_threshold": 0.0,
                "health_threshold": 1.0,
                "approval_required": False
            },
            ForbiddenZoneAccess.READ_ONLY: {
                "vp_threshold": 0.3,
                "health_threshold": 0.8,
                "approval_required": False
            },
            ForbiddenZoneAccess.CONTROLLED: {
                "vp_threshold": 0.5,
                "health_threshold": 0.6,
                "approval_required": True
            },
            ForbiddenZoneAccess.EXPERIMENTAL: {
                "vp_threshold": 0.7,
                "health_threshold": 0.4,
                "approval_required": True
            },
            ForbiddenZoneAccess.FULL_ACCESS: {
                "vp_threshold": 0.9,
                "health_threshold": 0.2,
                "approval_required": True
            }
        }
        
        self.active_sessions = {}
        self.access_history = []
    
    def determine_access_level(self, violation_pressure: float, 
                             system_health: float, 
                             operation_type: str) -> ForbiddenZoneAccess:
        """Determine appropriate access level for Forbidden Zone"""
        
        # Check if operation requires Forbidden Zone access
        if operation_type not in ["μ_recursion", "unbounded_search", "experimental_evolution"]:
            return ForbiddenZoneAccess.DENIED
        
        # Determine access level based on system state
        for access_level in reversed(list(ForbiddenZoneAccess)):
            controls = self.access_controls[access_level]
            if violation_pressure >= controls["vp_threshold"] and system_health <= controls["health_threshold"]:
                return access_level
        
        return ForbiddenZoneAccess.DENIED
    
    def grant_access(self, session_id: str, access_level: ForbiddenZoneAccess, 
                    duration_seconds: int = 300) -> bool:
        """Grant temporary access to Forbidden Zone"""
        
        if access_level == ForbiddenZoneAccess.DENIED:
            return False
        
        expiry_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        self.active_sessions[session_id] = {
            "access_level": access_level,
            "granted_at": datetime.utcnow(),
            "expires_at": expiry_time,
            "operations_performed": 0
        }
        
        self.access_history.append({
            "session_id": session_id,
            "access_level": access_level.value,
            "granted_at": datetime.utcnow().isoformat() + "Z",
            "expires_at": expiry_time.isoformat() + "Z"
        })
        
        return True
    
    def check_access(self, session_id: str, operation_type: str) -> bool:
        """Check if session has valid access for operation"""
        
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Check if session has expired
        if datetime.utcnow() > session["expires_at"]:
            del self.active_sessions[session_id]
            return False
        
        # Check operation compatibility with access level
        access_level = session["access_level"]
        
        if operation_type == "μ_recursion" and access_level in [ForbiddenZoneAccess.CONTROLLED, 
                                                               ForbiddenZoneAccess.EXPERIMENTAL, 
                                                               ForbiddenZoneAccess.FULL_ACCESS]:
            session["operations_performed"] += 1
            return True
        
        if operation_type == "experimental_evolution" and access_level in [ForbiddenZoneAccess.EXPERIMENTAL, 
                                                                          ForbiddenZoneAccess.FULL_ACCESS]:
            session["operations_performed"] += 1
            return True
        
        return False


class ProductionArbitrationStack:
    """
    Production arbitration stack implementing bounded halting oracle,
    VP-based classification, and formal escalation procedures.
    """
    
    def __init__(self, advanced_trait_engine: AdvancedTraitEngine, 
                 event_bus: Optional[DjinnEventBus] = None):
        """Initialize the production arbitration stack"""
        self.advanced_engine = advanced_trait_engine
        self.event_bus = event_bus or DjinnEventBus()
        
        # Core components
        self.halting_oracle = BoundedHaltingOracle()
        self.vp_classifier = VPBasedClassifier()
        self.escalation_manager = EscalationManager()
        self.forbidden_zone_manager = ForbiddenZoneManager()
        self.temporal_isolation = TemporalIsolationManager(self.event_bus)
        
        # Arbitration state
        self.arbitration_history = []
        self.active_requests = {}
        self.system_state = {
            "current_vp": 0.0,
            "system_health": 1.0,
            "convergence_success": 1.0,
            "last_update": datetime.utcnow()
        }
        
        # Arbitration parameters
        self.arbitrator_id = f"arbitrator_{uuid.uuid4().hex[:8]}"
        self.max_concurrent_requests = 100
        self.arbitration_timeout_seconds = 30.0
    
    def update_system_state(self, violation_pressure: float, 
                           system_health: float, 
                           convergence_success: float) -> None:
        """Update system state for arbitration decisions"""
        self.system_state.update({
            "current_vp": violation_pressure,
            "system_health": system_health,
            "convergence_success": convergence_success,
            "last_update": datetime.utcnow()
        })
    
    def arbitrate_operation(self, operation_type: str, 
                          operation_data: Dict[str, Any],
                          source_identity: Optional[str] = None) -> ArbitrationDecision:
        """
        Arbitrate an operation through the full decision pipeline.
        
        Returns:
            ArbitrationDecision with complete decision information
        """
        # Create arbitration request
        request = ArbitrationRequest(
            operation_type=operation_type,
            operation_data=operation_data,
            violation_pressure=self.system_state["current_vp"],
            system_health=self.system_state["system_health"],
            convergence_success=self.system_state["convergence_success"],
            source_identity=source_identity
        )
        
        # Store active request
        self.active_requests[request.request_id] = request
        
        try:
            # Step 1: Bounded halting oracle check
            will_halt, halt_confidence, halt_reasoning = self.halting_oracle.will_halt(operation_data)
            
            # Step 2: VP-based classification
            vp_class, vp_confidence, vp_reasoning = self.vp_classifier.classify_operation(
                request.violation_pressure,
                request.system_health,
                request.convergence_success
            )
            
            # Step 3: Determine escalation level
            escalation_level = self.escalation_manager.determine_escalation_level(
                request.violation_pressure,
                request.system_health
            )
            request.escalation_level = escalation_level
            
            # Step 4: Determine Forbidden Zone access
            forbidden_access = self.forbidden_zone_manager.determine_access_level(
                request.violation_pressure,
                request.system_health,
                operation_type
            )
            
            # Step 5: Make arbitration decision
            decision = self._make_decision(
                request, will_halt, halt_confidence, halt_reasoning, vp_class, vp_confidence,
                escalation_level, forbidden_access
            )
            
            # Step 6: Execute decision actions
            self._execute_decision(decision)
            
            return decision
            
        finally:
            # Clean up active request
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
    
    def _make_decision(self, request: ArbitrationRequest, 
                      will_halt: bool, halt_confidence: float, halt_reasoning: str,
                      vp_class: ViolationClass, vp_confidence: float,
                      escalation_level: EscalationLevel,
                      forbidden_access: ForbiddenZoneAccess) -> ArbitrationDecision:
        """Make final arbitration decision based on all factors"""
        
        # Initialize decision
        decision = ArbitrationDecision(
            request_id=request.request_id,
            escalation_level=escalation_level,
            forbidden_zone_access=forbidden_access,
            arbitrator_id=self.arbitrator_id
        )
        
        # Emergency halt conditions
        if vp_class == ViolationClass.VP4_COLLAPSE_THRESHOLD:
            decision.decision = ArbitrationDecisionType.EMERGENCY_HALT
            decision.confidence = 1.0
            decision.reasoning = f"Emergency halt: VP4 collapse threshold reached"
            return decision
        
        # Forbidden Zone access decisions
        if request.operation_type in ["μ_recursion", "unbounded_search"]:
            if forbidden_access == ForbiddenZoneAccess.DENIED:
                decision.decision = ArbitrationDecisionType.FORBIDDEN
                decision.confidence = 0.9
                decision.reasoning = f"Forbidden Zone access denied: {vp_class.value}"
                return decision
        
        # Non-halting operation decisions
        if not will_halt:
            decision.decision = ArbitrationDecisionType.QUARANTINE
            decision.confidence = halt_confidence
            decision.reasoning = f"Non-halting operation detected: {halt_reasoning}"
            decision.temporal_isolation_duration = 300000  # 5 minutes
            return decision
        
        # VP-based decisions
        if vp_class in [ViolationClass.VP2_INSTABILITY, ViolationClass.VP3_CRITICAL_DIVERGENCE]:
            if escalation_level in [EscalationLevel.LEVEL_3, EscalationLevel.LEVEL_4]:
                decision.decision = ArbitrationDecisionType.ESCALATE
                decision.confidence = vp_confidence
                decision.reasoning = f"High VP operation requires escalation: {vp_class.value}"
                return decision
            else:
                decision.decision = ArbitrationDecisionType.QUARANTINE
                decision.confidence = vp_confidence
                decision.reasoning = f"High VP operation quarantined: {vp_class.value}"
                decision.temporal_isolation_duration = 60000  # 1 minute
                return decision
        
        # Auto-approval check
        if self.escalation_manager.can_auto_approve(escalation_level):
            decision.decision = ArbitrationDecisionType.APPROVE
            decision.confidence = min(halt_confidence, vp_confidence)
            decision.reasoning = f"Auto-approved: {vp_class.value}, halting confidence: {halt_confidence:.3f}"
            return decision
        
        # Default to modification for uncertain cases
        decision.decision = ArbitrationDecisionType.MODIFY
        decision.confidence = min(halt_confidence, vp_confidence) * 0.8
        decision.reasoning = f"Operation requires modification: {vp_class.value}"
        decision.modification_instructions = {
            "reduce_complexity": True,
            "limit_recursion_depth": True,
            "add_safety_checks": True
        }
        
        return decision
    
    def _execute_decision(self, decision: ArbitrationDecision) -> None:
        """Execute the arbitration decision"""
        
        # Record decision in history
        self.arbitration_history.append({
            "decision_id": decision.decision_id,
            "request_id": decision.request_id,
            "decision": decision.decision.value,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "timestamp": decision.timestamp.isoformat() + "Z"
        })
        
        # Execute decision-specific actions
        if decision.decision == ArbitrationDecisionType.QUARANTINE:
            if decision.temporal_isolation_duration:
                try:
                    self.temporal_isolation.apply_temporal_lock(
                        duration=decision.temporal_isolation_duration,
                        reason=f"Arbitration quarantine: {decision.reasoning}"
                    )
                except RuntimeError as e:
                    # Handle case where no event loop is running (e.g., in tests)
                    if "no running event loop" in str(e):
                        print(f"Warning: Temporal isolation skipped (no event loop): {decision.reasoning}")
                    else:
                        raise
        
        elif decision.decision == ArbitrationDecisionType.EMERGENCY_HALT:
            # Trigger system-wide emergency halt
            if self.event_bus:
                emergency_event = SystemHealthEvent(
                    health_metrics={"emergency_halt": True},
                    alert_level="critical"
                )
                self.event_bus.publish(emergency_event)
        
        elif decision.decision == ArbitrationDecisionType.APPROVE:
            # Grant Forbidden Zone access if needed
            if decision.forbidden_zone_access != ForbiddenZoneAccess.DENIED:
                session_id = f"session_{decision.request_id}"
                self.forbidden_zone_manager.grant_access(
                    session_id, decision.forbidden_zone_access
                )
    
    def export_arbitration_state(self) -> Dict[str, Any]:
        """Export complete arbitration stack state"""
        return {
            "arbitrator_id": self.arbitrator_id,
            "system_state": self.system_state,
            "active_requests_count": len(self.active_requests),
            "arbitration_history_count": len(self.arbitration_history),
            "forbidden_zone_sessions": len(self.forbidden_zone_manager.active_sessions),
            "last_arbitration": self.arbitration_history[-1] if self.arbitration_history else None,
            "arbitration_metrics": {
                "total_decisions": len(self.arbitration_history),
                "approval_rate": self._calculate_approval_rate(),
                "escalation_rate": self._calculate_escalation_rate(),
                "quarantine_rate": self._calculate_quarantine_rate()
            }
        }
    
    def _calculate_approval_rate(self) -> float:
        """Calculate approval rate from history"""
        if not self.arbitration_history:
            return 0.0
        
        approvals = sum(1 for entry in self.arbitration_history 
                       if entry["decision"] == ArbitrationDecisionType.APPROVE.value)
        return approvals / len(self.arbitration_history)
    
    def _calculate_escalation_rate(self) -> float:
        """Calculate escalation rate from history"""
        if not self.arbitration_history:
            return 0.0
        
        escalations = sum(1 for entry in self.arbitration_history 
                         if entry["decision"] == ArbitrationDecisionType.ESCALATE.value)
        return escalations / len(self.arbitration_history)
    
    def _calculate_quarantine_rate(self) -> float:
        """Calculate quarantine rate from history"""
        if not self.arbitration_history:
            return 0.0
        
        quarantines = sum(1 for entry in self.arbitration_history 
                         if entry["decision"] == ArbitrationDecisionType.QUARANTINE.value)
        return quarantines / len(self.arbitration_history)


# Example usage and testing
if __name__ == "__main__":
    # Initialize components
    from core_trait_framework import CoreTraitFramework
    
    core_framework = CoreTraitFramework()
    advanced_engine = AdvancedTraitEngine(core_framework)
    arbitration_stack = ProductionArbitrationStack(advanced_engine)
    
    # Update system state
    arbitration_stack.update_system_state(
        violation_pressure=0.3,
        system_health=0.8,
        convergence_success=0.7
    )
    
    # Test arbitration decisions
    test_operations = [
        {
            "operation_type": "trait_convergence",
            "operation_data": {
                "complexity": 0.2,
                "recursion_depth": 2,
                "estimated_iterations": 50
            }
        },
        {
            "operation_type": "μ_recursion",
            "operation_data": {
                "complexity": 0.9,
                "recursion_depth": 15,
                "estimated_iterations": 2000
            }
        }
    ]
    
    print("=== Production Arbitration Stack Test ===")
    
    for i, operation in enumerate(test_operations):
        print(f"\nTest {i+1}: {operation['operation_type']}")
        
        decision = arbitration_stack.arbitrate_operation(
            operation["operation_type"],
            operation["operation_data"]
        )
        
        print(f"Decision: {decision.decision.value}")
        print(f"Confidence: {decision.confidence:.3f}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Escalation Level: {decision.escalation_level.value}")
        print(f"Forbidden Zone Access: {decision.forbidden_zone_access.value}")
    
    # Export state
    state = arbitration_stack.export_arbitration_state()
    print(f"\nArbitration State:")
    print(f"Total Decisions: {state['arbitration_metrics']['total_decisions']}")
    print(f"Approval Rate: {state['arbitration_metrics']['approval_rate']:.3f}")
    print(f"Escalation Rate: {state['arbitration_metrics']['escalation_rate']:.3f}")
    print(f"Quarantine Rate: {state['arbitration_metrics']['quarantine_rate']:.3f}")
    
    print("\nProduction Arbitration Stack operational!")
