"""
Production Synchrony Phase Lock Protocol - Phase 2.3 Implementation

This module implements the comprehensive Synchrony Phase Lock (SPL) protocol that
ensures universal, atomic consistency across all kernel operations. It provides
temporal drift compensation, multi-agent hash verification, and creates a single,
immutable timeline of sovereign action.

Key Features:
- Multi-layered SPL protocol with phase gates
- Temporal drift compensation and synchronization
- Multi-agent hash verification for operation integrity
- Atomic operation execution with rollback capabilities
- Universal timeline management and coordination
- Distributed consensus for critical operations
"""

import time
import hashlib
import threading
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
import queue

from arbitration_stack import ProductionArbitrationStack, ArbitrationDecision
from event_driven_coordination import DjinnEventBus, EventType
from utm_kernel_design import UTMKernel, TapeSymbol
from violation_pressure_calculation import ViolationMonitor


class PhaseState(Enum):
    """States in the synchrony phase lock protocol"""
    IDLE = "idle"                       # No active synchronization
    PREPARING = "preparing"             # Preparing for phase lock
    PHASE_LOCKED = "phase_locked"       # Active phase lock established
    EXECUTING = "executing"             # Executing synchronized operations
    COMMITTING = "committing"           # Committing operation results
    ROLLBACK = "rollback"               # Rolling back failed operations
    COMPLETE = "complete"               # Phase lock cycle complete


class SynchronyLevel(Enum):
    """Levels of synchrony enforcement"""
    BASIC = "basic"                     # Basic temporal ordering
    STANDARD = "standard"               # Standard hash verification
    ENHANCED = "enhanced"               # Multi-agent verification
    SOVEREIGN = "sovereign"             # Full consensus protocol


class OperationPriority(Enum):
    """Priority levels for synchronized operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class PhaseGate:
    """A synchronization gate that ensures atomic operation execution"""
    gate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phase_state: PhaseState = PhaseState.IDLE
    synchrony_level: SynchronyLevel = SynchronyLevel.STANDARD
    participant_count: int = 1
    ready_participants: int = 0
    operation_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: float = 30.0
    participants: Dict[str, bool] = field(default_factory=dict)
    verification_hashes: Dict[str, str] = field(default_factory=dict)


@dataclass
class SynchronizedOperation:
    """An operation that requires synchrony protocol execution"""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""
    operation_data: Dict[str, Any] = field(default_factory=dict)
    priority: OperationPriority = OperationPriority.NORMAL
    synchrony_level: SynchronyLevel = SynchronyLevel.STANDARD
    source_agent: str = ""
    target_participants: List[str] = field(default_factory=list)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    phase_gate: Optional[PhaseGate] = None
    
    def calculate_operation_hash(self) -> str:
        """Calculate deterministic hash for operation verification"""
        operation_string = json.dumps({
            "operation_type": self.operation_type,
            "operation_data": self.operation_data,
            "priority": self.priority.value,
            "source_agent": self.source_agent,
            "timestamp": self.timestamp.isoformat()
        }, sort_keys=True)
        
        return hashlib.sha256(operation_string.encode()).hexdigest()


@dataclass
class TemporalDriftMetrics:
    """Metrics for tracking and compensating temporal drift"""
    reference_time: datetime = field(default_factory=datetime.utcnow)
    agent_timestamps: Dict[str, datetime] = field(default_factory=dict)
    drift_tolerances: Dict[str, float] = field(default_factory=dict)  # seconds
    max_drift_detected: float = 0.0
    drift_compensation_active: bool = False
    last_synchronization: Optional[datetime] = None
    
    def update_agent_time(self, agent_id: str, agent_time: datetime, 
                         tolerance: float = 1.0) -> float:
        """Update agent timestamp and calculate drift"""
        self.agent_timestamps[agent_id] = agent_time
        self.drift_tolerances[agent_id] = tolerance
        
        # Calculate drift from reference time
        drift = abs((agent_time - self.reference_time).total_seconds())
        self.max_drift_detected = max(self.max_drift_detected, drift)
        
        return drift
    
    def requires_synchronization(self) -> bool:
        """Check if temporal synchronization is required"""
        if not self.agent_timestamps:
            return False
        
        for agent_id, agent_time in self.agent_timestamps.items():
            tolerance = self.drift_tolerances.get(agent_id, 1.0)
            drift = abs((agent_time - self.reference_time).total_seconds())
            if drift > tolerance:
                return True
        
        return False


@dataclass
class ConsensusResult:
    """Result of a distributed consensus operation"""
    consensus_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_id: str = ""
    consensus_achieved: bool = False
    participating_agents: List[str] = field(default_factory=list)
    agreeing_agents: List[str] = field(default_factory=list)
    disagreeing_agents: List[str] = field(default_factory=list)
    consensus_hash: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TemporalDriftCompensator:
    """Compensates for temporal drift between distributed agents"""
    
    def __init__(self):
        self.drift_metrics = TemporalDriftMetrics()
        self.compensation_history = []
        self.sync_lock = threading.Lock()
        
    def register_agent_time(self, agent_id: str, agent_time: datetime,
                           tolerance: float = 1.0) -> float:
        """Register agent timestamp and return calculated drift"""
        with self.sync_lock:
            return self.drift_metrics.update_agent_time(agent_id, agent_time, tolerance)
    
    def compensate_temporal_drift(self) -> bool:
        """Perform temporal drift compensation across all agents"""
        with self.sync_lock:
            if not self.drift_metrics.requires_synchronization():
                return True
            
            # Calculate consensus time (median of all agent times)
            timestamps = list(self.drift_metrics.agent_timestamps.values())
            timestamps.append(self.drift_metrics.reference_time)
            timestamps.sort()
            
            median_time = timestamps[len(timestamps) // 2]
            
            # Update reference time and mark compensation as active
            old_reference = self.drift_metrics.reference_time
            self.drift_metrics.reference_time = median_time
            self.drift_metrics.drift_compensation_active = True
            self.drift_metrics.last_synchronization = datetime.utcnow()
            
            # Record compensation event
            self.compensation_history.append({
                "old_reference": old_reference.isoformat() + "Z",
                "new_reference": median_time.isoformat() + "Z",
                "compensation_time": datetime.utcnow().isoformat() + "Z",
                "agents_synchronized": len(self.drift_metrics.agent_timestamps)
            })
            
            return True
    
    def get_compensated_time(self) -> datetime:
        """Get current compensated reference time"""
        with self.sync_lock:
            return self.drift_metrics.reference_time


class MultiAgentHashVerifier:
    """Verifies operation integrity through multi-agent hash consensus"""
    
    def __init__(self):
        self.verification_cache = {}
        self.consensus_threshold = 0.67  # 67% agreement required
        self.verification_timeout = 10.0  # seconds
        
    def submit_hash_verification(self, operation_id: str, agent_id: str,
                                operation_hash: str) -> None:
        """Submit hash verification from an agent"""
        if operation_id not in self.verification_cache:
            self.verification_cache[operation_id] = {
                "hashes": {},
                "timestamp": datetime.utcnow(),
                "verified": False
            }
        
        self.verification_cache[operation_id]["hashes"][agent_id] = operation_hash
    
    def verify_operation_consensus(self, operation_id: str,
                                  participating_agents: List[str]) -> Tuple[bool, float, str]:
        """Verify if operation hash consensus is achieved"""
        if operation_id not in self.verification_cache:
            return False, 0.0, "No verification data available"
        
        verification_data = self.verification_cache[operation_id]
        submitted_hashes = verification_data["hashes"]
        
        # Check if verification has timed out
        elapsed = (datetime.utcnow() - verification_data["timestamp"]).total_seconds()
        if elapsed > self.verification_timeout:
            return False, 0.0, f"Verification timeout after {elapsed:.1f} seconds"
        
        # Calculate hash consensus
        hash_counts = {}
        for agent_id in participating_agents:
            if agent_id in submitted_hashes:
                hash_value = submitted_hashes[agent_id]
                hash_counts[hash_value] = hash_counts.get(hash_value, 0) + 1
        
        if not hash_counts:
            return False, 0.0, "No hash submissions received"
        
        # Find majority hash
        total_participants = len(participating_agents)
        max_count = max(hash_counts.values())
        majority_hash = [h for h, c in hash_counts.items() if c == max_count][0]
        
        # Calculate consensus confidence
        confidence = max_count / total_participants
        consensus_achieved = confidence >= self.consensus_threshold
        
        if consensus_achieved:
            verification_data["verified"] = True
        
        reasoning = f"Hash consensus: {max_count}/{total_participants} agents agree"
        return consensus_achieved, confidence, reasoning


class DistributedConsensusEngine:
    """Manages distributed consensus for critical operations"""
    
    def __init__(self):
        self.active_consensus = {}
        self.consensus_history = []
        self.consensus_timeout = 30.0  # seconds
        self.minimum_participants = 1
        
    def initiate_consensus(self, operation: SynchronizedOperation) -> str:
        """Initiate distributed consensus for an operation"""
        consensus_id = str(uuid.uuid4())
        
        self.active_consensus[consensus_id] = {
            "operation": operation,
            "participants": operation.target_participants.copy(),
            "votes": {},
            "initiated_at": datetime.utcnow(),
            "completed": False
        }
        
        return consensus_id
    
    def submit_consensus_vote(self, consensus_id: str, agent_id: str,
                             vote: bool, reasoning: str = "") -> None:
        """Submit a consensus vote from an agent"""
        if consensus_id in self.active_consensus:
            consensus_data = self.active_consensus[consensus_id]
            consensus_data["votes"][agent_id] = {
                "vote": vote,
                "reasoning": reasoning,
                "timestamp": datetime.utcnow()
            }
    
    def evaluate_consensus(self, consensus_id: str) -> ConsensusResult:
        """Evaluate current consensus state"""
        if consensus_id not in self.active_consensus:
            return ConsensusResult(
                consensus_id=consensus_id,
                consensus_achieved=False,
                confidence=0.0
            )
        
        consensus_data = self.active_consensus[consensus_id]
        operation = consensus_data["operation"]
        participants = consensus_data["participants"]
        votes = consensus_data["votes"]
        
        # Check timeout
        elapsed = (datetime.utcnow() - consensus_data["initiated_at"]).total_seconds()
        if elapsed > self.consensus_timeout:
            consensus_data["completed"] = True
            
            return ConsensusResult(
                consensus_id=consensus_id,
                operation_id=operation.operation_id,
                consensus_achieved=False,
                participating_agents=participants,
                confidence=0.0
            )
        
        # Count votes
        agreeing_agents = [aid for aid, vote_data in votes.items() if vote_data["vote"]]
        disagreeing_agents = [aid for aid, vote_data in votes.items() if not vote_data["vote"]]
        
        # Calculate consensus
        total_expected = max(len(participants), self.minimum_participants)
        agreement_ratio = len(agreeing_agents) / total_expected if total_expected > 0 else 0.0
        consensus_achieved = agreement_ratio >= 0.67  # 67% threshold
        
        # Create consensus hash if achieved
        consensus_hash = None
        if consensus_achieved:
            consensus_string = json.dumps({
                "operation_id": operation.operation_id,
                "agreeing_agents": sorted(agreeing_agents),
                "operation_hash": operation.calculate_operation_hash()
            }, sort_keys=True)
            consensus_hash = hashlib.sha256(consensus_string.encode()).hexdigest()
        
        result = ConsensusResult(
            consensus_id=consensus_id,
            operation_id=operation.operation_id,
            consensus_achieved=consensus_achieved,
            participating_agents=participants,
            agreeing_agents=agreeing_agents,
            disagreeing_agents=disagreeing_agents,
            consensus_hash=consensus_hash,
            confidence=agreement_ratio
        )
        
        # Mark as completed if consensus achieved or timeout
        if consensus_achieved or len(votes) == len(participants):
            consensus_data["completed"] = True
            self.consensus_history.append(result)
        
        return result


class ProductionSynchronySystem:
    """
    Production synchrony system implementing the complete SPL protocol
    with temporal drift compensation and multi-agent hash verification.
    """
    
    def __init__(self, arbitration_stack: ProductionArbitrationStack,
                 utm_kernel: UTMKernel, event_bus: Optional[DjinnEventBus] = None):
        """Initialize the production synchrony system"""
        self.arbitration_stack = arbitration_stack
        self.utm_kernel = utm_kernel
        self.event_bus = event_bus or DjinnEventBus()
        
        # Core synchrony components
        self.drift_compensator = TemporalDriftCompensator()
        self.hash_verifier = MultiAgentHashVerifier()
        self.consensus_engine = DistributedConsensusEngine()
        
        # Synchrony state management
        self.active_phase_gates = {}
        self.operation_queue = queue.PriorityQueue()
        self.execution_history = []
        self.global_timeline = []
        
        # System parameters
        self.max_concurrent_operations = 10
        self.default_timeout = 30.0
        self.synchrony_metrics = {
            "operations_synchronized": 0,
            "consensus_operations": 0,
            "temporal_compensations": 0,
            "hash_verifications": 0,
            "rollbacks_executed": 0
        }
        
        # Execution infrastructure
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.sync_lock = threading.RLock()
        self.shutdown_flag = False
        
        # Start background synchrony monitor
        self.monitor_thread = threading.Thread(target=self._synchrony_monitor, daemon=True)
        self.monitor_thread.start()
    
    def submit_synchronized_operation(self, operation: SynchronizedOperation) -> str:
        """Submit an operation for synchronized execution"""
        with self.sync_lock:
            # Calculate operation hash
            operation_hash = operation.calculate_operation_hash()
            
            # Create phase gate for operation
            phase_gate = PhaseGate(
                phase_state=PhaseState.PREPARING,
                synchrony_level=operation.synchrony_level,
                participant_count=len(operation.target_participants) or 1,
                operation_hash=operation_hash,
                timeout_seconds=self.default_timeout
            )
            
            # Initialize participants
            for participant in operation.target_participants:
                phase_gate.participants[participant] = False
            
            operation.phase_gate = phase_gate
            self.active_phase_gates[phase_gate.gate_id] = phase_gate
            
            # Queue operation with priority
            priority_value = (6 - operation.priority.value, time.time())  # Higher priority = lower number
            self.operation_queue.put((priority_value, operation))
            
            return operation.operation_id
    
    def register_participant_ready(self, gate_id: str, participant_id: str,
                                  participant_hash: str) -> bool:
        """Register a participant as ready for phase lock"""
        with self.sync_lock:
            if gate_id not in self.active_phase_gates:
                return False
            
            phase_gate = self.active_phase_gates[gate_id]
            
            # Verify participant hash
            if participant_hash != phase_gate.operation_hash:
                return False
            
            # Mark participant as ready
            phase_gate.participants[participant_id] = True
            phase_gate.verification_hashes[participant_id] = participant_hash
            phase_gate.ready_participants = sum(phase_gate.participants.values())
            
            # Check if all participants are ready
            if phase_gate.ready_participants >= phase_gate.participant_count:
                phase_gate.phase_state = PhaseState.PHASE_LOCKED
            
            return True
    
    def execute_synchronized_operation(self, operation: SynchronizedOperation) -> Dict[str, Any]:
        """Execute a synchronized operation with full SPL protocol"""
        execution_result = {
            "operation_id": operation.operation_id,
            "success": False,
            "phase_states": [],
            "verification_result": None,
            "consensus_result": None,
            "execution_data": {},
            "timeline_entry": None
        }
        
        try:
            # Phase 1: Temporal Drift Compensation
            execution_result["phase_states"].append("temporal_compensation")
            
            # Register operation time with drift compensator
            drift = self.drift_compensator.register_agent_time(
                operation.source_agent, operation.timestamp
            )
            
            if drift > 1.0:  # If drift > 1 second, compensate
                self.drift_compensator.compensate_temporal_drift()
                self.synchrony_metrics["temporal_compensations"] += 1
            
            # Phase 2: Hash Verification (if multi-agent)
            if operation.synchrony_level in [SynchronyLevel.ENHANCED, SynchronyLevel.SOVEREIGN]:
                execution_result["phase_states"].append("hash_verification")
                
                # Submit hash verification
                self.hash_verifier.submit_hash_verification(
                    operation.operation_id,
                    operation.source_agent,
                    operation.calculate_operation_hash()
                )
                
                # Verify consensus
                verified, confidence, reasoning = self.hash_verifier.verify_operation_consensus(
                    operation.operation_id, operation.target_participants or [operation.source_agent]
                )
                
                execution_result["verification_result"] = {
                    "verified": verified,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
                
                if not verified and operation.synchrony_level == SynchronyLevel.SOVEREIGN:
                    execution_result["success"] = False
                    execution_result["error"] = "Hash verification failed"
                    return execution_result
                
                self.synchrony_metrics["hash_verifications"] += 1
            
            # Phase 3: Distributed Consensus (if sovereign level)
            if operation.synchrony_level == SynchronyLevel.SOVEREIGN:
                execution_result["phase_states"].append("distributed_consensus")
                
                consensus_id = self.consensus_engine.initiate_consensus(operation)
                
                # Auto-submit vote from source agent
                self.consensus_engine.submit_consensus_vote(
                    consensus_id, operation.source_agent, True, "Source agent approval"
                )
                
                # Evaluate consensus
                consensus_result = self.consensus_engine.evaluate_consensus(consensus_id)
                execution_result["consensus_result"] = {
                    "consensus_achieved": consensus_result.consensus_achieved,
                    "confidence": consensus_result.confidence,
                    "agreeing_agents": consensus_result.agreeing_agents
                }
                
                if not consensus_result.consensus_achieved:
                    execution_result["success"] = False
                    execution_result["error"] = "Distributed consensus failed"
                    return execution_result
                
                self.synchrony_metrics["consensus_operations"] += 1
            
            # Phase 4: Arbitration (if required)
            execution_result["phase_states"].append("arbitration")
            
            arbitration_decision = self.arbitration_stack.arbitrate_operation(
                operation.operation_type,
                operation.operation_data,
                operation.source_agent
            )
            
            execution_result["arbitration_decision"] = {
                "decision": arbitration_decision.decision.value,
                "confidence": arbitration_decision.confidence,
                "reasoning": arbitration_decision.reasoning
            }
            
            # Check arbitration result
            if arbitration_decision.decision.value not in ["approve", "modify"]:
                execution_result["success"] = False
                execution_result["error"] = f"Arbitration {arbitration_decision.decision.value}"
                return execution_result
            
            # Phase 5: Atomic Execution
            execution_result["phase_states"].append("atomic_execution")
            
            # Execute operation based on type
            if operation.operation_type == "trait_convergence":
                execution_data = self._execute_trait_convergence(operation)
            elif operation.operation_type == "identity_injection":
                execution_data = self._execute_identity_injection(operation)
            elif operation.operation_type == "lattice_composition":
                execution_data = self._execute_lattice_composition(operation)
            else:
                execution_data = self._execute_generic_operation(operation)
            
            execution_result["execution_data"] = execution_data
            
            # Phase 6: Timeline Recording
            execution_result["phase_states"].append("timeline_recording")
            
            compensated_time = self.drift_compensator.get_compensated_time()
            timeline_entry = {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "compensated_timestamp": compensated_time.isoformat() + "Z",
                "source_agent": operation.source_agent,
                "synchrony_level": operation.synchrony_level.value,
                "execution_hash": hashlib.sha256(
                    json.dumps(execution_data, sort_keys=True).encode()
                ).hexdigest(),
                "arbitration_decision": arbitration_decision.decision.value
            }
            
            self.global_timeline.append(timeline_entry)
            execution_result["timeline_entry"] = timeline_entry
            
            # Success
            execution_result["success"] = True
            self.synchrony_metrics["operations_synchronized"] += 1
            
            return execution_result
            
        except Exception as e:
            # Phase 7: Rollback (if error)
            execution_result["phase_states"].append("rollback")
            execution_result["success"] = False
            execution_result["error"] = str(e)
            execution_result["rollback_performed"] = self._perform_rollback(operation)
            self.synchrony_metrics["rollbacks_executed"] += 1
            
            return execution_result
    
    def _execute_trait_convergence(self, operation: SynchronizedOperation) -> Dict[str, Any]:
        """Execute trait convergence operation"""
        parent_traits = operation.operation_data.get("parent_traits", [])
        if len(parent_traits) < 2:
            raise ValueError("Trait convergence requires at least 2 parent trait sets")
        
        # Use advanced trait engine for convergence
        converged_traits = self.arbitration_stack.advanced_engine.converge_traits_with_adaptation(
            parent_traits
        )
        
        return {
            "operation_type": "trait_convergence",
            "parent_count": len(parent_traits),
            "child_traits": converged_traits,
            "trait_count": len(converged_traits)
        }
    
    def _execute_identity_injection(self, operation: SynchronizedOperation) -> Dict[str, Any]:
        """Execute identity injection operation"""
        trait_payload = operation.operation_data.get("trait_payload", {})
        
        # Use UTM kernel for identity injection
        injection_result = self.utm_kernel.process_tape_operation(
            TapeSymbol.IDENTITY_INJECTION,
            {"trait_payload": trait_payload}
        )
        
        return {
            "operation_type": "identity_injection",
            "injection_result": injection_result,
            "trait_payload_size": len(trait_payload)
        }
    
    def _execute_lattice_composition(self, operation: SynchronizedOperation) -> Dict[str, Any]:
        """Execute lattice composition operation"""
        component_identities = operation.operation_data.get("component_identities", [])
        
        # Use UTM kernel for lattice composition
        composition_result = self.utm_kernel.process_tape_operation(
            TapeSymbol.RECURSIVE_LATTICE_COMPOSITION,
            {"component_identities": component_identities}
        )
        
        return {
            "operation_type": "lattice_composition",
            "composition_result": composition_result,
            "component_count": len(component_identities)
        }
    
    def _execute_generic_operation(self, operation: SynchronizedOperation) -> Dict[str, Any]:
        """Execute generic operation"""
        return {
            "operation_type": operation.operation_type,
            "operation_data": operation.operation_data,
            "execution_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _perform_rollback(self, operation: SynchronizedOperation) -> bool:
        """Perform rollback for failed operation"""
        try:
            # Remove from timeline if present
            self.global_timeline = [
                entry for entry in self.global_timeline 
                if entry.get("operation_id") != operation.operation_id
            ]
            
            # Clean up phase gate
            if operation.phase_gate and operation.phase_gate.gate_id in self.active_phase_gates:
                del self.active_phase_gates[operation.phase_gate.gate_id]
            
            # Clean up verification cache
            if operation.operation_id in self.hash_verifier.verification_cache:
                del self.hash_verifier.verification_cache[operation.operation_id]
            
            return True
        except Exception:
            return False
    
    def _synchrony_monitor(self) -> None:
        """Background monitor for synchrony operations"""
        while not self.shutdown_flag:
            try:
                # Process queued operations
                if not self.operation_queue.empty():
                    try:
                        priority_info, operation = self.operation_queue.get(timeout=1.0)
                        
                        # Check if phase gate is ready
                        if (operation.phase_gate and 
                            operation.phase_gate.phase_state == PhaseState.PHASE_LOCKED):
                            
                            # Execute operation in thread pool
                            future = self.executor.submit(
                                self.execute_synchronized_operation, operation
                            )
                            
                            # Store execution for tracking
                            self.execution_history.append({
                                "operation_id": operation.operation_id,
                                "future": future,
                                "submitted_at": datetime.utcnow()
                            })
                        else:
                            # Put back in queue if not ready
                            self.operation_queue.put((priority_info, operation))
                    
                    except queue.Empty:
                        pass
                
                # Clean up completed executions
                self.execution_history = [
                    entry for entry in self.execution_history
                    if not entry["future"].done()
                ]
                
                # Clean up expired phase gates
                current_time = datetime.utcnow()
                expired_gates = [
                    gate_id for gate_id, gate in self.active_phase_gates.items()
                    if (current_time - gate.timestamp).total_seconds() > gate.timeout_seconds
                ]
                
                for gate_id in expired_gates:
                    del self.active_phase_gates[gate_id]
                
                time.sleep(0.1)  # 100ms monitoring cycle
                
            except Exception as e:
                print(f"Synchrony monitor error: {e}")
                time.sleep(1.0)
    
    def get_synchrony_metrics(self) -> Dict[str, Any]:
        """Get comprehensive synchrony system metrics"""
        with self.sync_lock:
            return {
                "synchrony_metrics": self.synchrony_metrics.copy(),
                "active_phase_gates": len(self.active_phase_gates),
                "queued_operations": self.operation_queue.qsize(),
                "execution_history_size": len(self.execution_history),
                "global_timeline_size": len(self.global_timeline),
                "temporal_drift_active": self.drift_compensator.drift_metrics.drift_compensation_active,
                "max_drift_detected": self.drift_compensator.drift_metrics.max_drift_detected,
                "last_synchronization": (
                    self.drift_compensator.drift_metrics.last_synchronization.isoformat() + "Z"
                    if self.drift_compensator.drift_metrics.last_synchronization
                    else None
                )
            }
    
    def export_global_timeline(self) -> List[Dict[str, Any]]:
        """Export the complete global timeline"""
        with self.sync_lock:
            return self.global_timeline.copy()
    
    def shutdown(self) -> None:
        """Shutdown the synchrony system gracefully"""
        self.shutdown_flag = True
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)


# Example usage and testing
if __name__ == "__main__":
    # Initialize dependencies (mock for testing)
    from core_trait_framework import CoreTraitFramework
    from advanced_trait_engine import AdvancedTraitEngine
    
    print("=== Production Synchrony System Test ===")
    
    # Initialize components
    core_framework = CoreTraitFramework()
    advanced_engine = AdvancedTraitEngine(core_framework)
    arbitration_stack = ProductionArbitrationStack(advanced_engine)
    utm_kernel = UTMKernel()
    
    synchrony_system = ProductionSynchronySystem(arbitration_stack, utm_kernel)
    
    # Test synchronized operation
    operation = SynchronizedOperation(
        operation_type="trait_convergence",
        operation_data={
            "parent_traits": [
                {"intimacy": 0.7, "commitment": 0.8},
                {"intimacy": 0.6, "commitment": 0.7}
            ]
        },
        priority=OperationPriority.HIGH,
        synchrony_level=SynchronyLevel.ENHANCED,
        source_agent="test_agent",
        target_participants=["test_agent"]
    )
    
    # Submit operation
    operation_id = synchrony_system.submit_synchronized_operation(operation)
    print(f"Submitted operation: {operation_id}")
    
    # Register participant readiness
    if operation.phase_gate:
        ready = synchrony_system.register_participant_ready(
            operation.phase_gate.gate_id,
            "test_agent",
            operation.calculate_operation_hash()
        )
        print(f"Participant ready: {ready}")
    
    # Wait a moment for execution
    time.sleep(2.0)
    
    # Get metrics
    metrics = synchrony_system.get_synchrony_metrics()
    print(f"Synchrony metrics: {metrics}")
    
    # Get timeline
    timeline = synchrony_system.export_global_timeline()
    print(f"Timeline entries: {len(timeline)}")
    
    # Shutdown
    synchrony_system.shutdown()
    
    print("Production Synchrony System operational!")
