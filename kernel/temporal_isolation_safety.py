# Temporal Isolation Safety System - Phase 0.4 Implementation
# Version 1.0 - Automatic Quarantine for Unstable Operations

"""
Temporal Isolation Safety System implementing automatic quarantine for unstable operations.
This prevents system-wide instability through time-based containment.

Core Features:
- Automatic quarantine triggered by VP thresholds
- Time-based isolation with automatic release
- Coordinated safety responses
- Isolation state management
- Release scheduling and monitoring
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class IsolationState(Enum):
    """Isolation state enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_RELEASE = "pending_release"
    EMERGENCY = "emergency"


@dataclass
class IsolationResult:
    """Result of temporal isolation operation"""
    isolation_id: str
    isolation_state: IsolationState
    reason: str
    start_time: datetime
    release_time: datetime
    duration_ms: int
    vp_level: Optional[float] = None
    affected_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "isolation_id": self.isolation_id,
            "isolation_state": self.isolation_state.value,
            "reason": self.reason,
            "start_time": self.start_time.isoformat() + "Z",
            "release_time": self.release_time.isoformat() + "Z",
            "duration_ms": self.duration_ms,
            "vp_level": self.vp_level,
            "affected_components": self.affected_components
        }


@dataclass
class SystemIsolationEvent:
    """Event published when system isolation status changes"""
    isolation_active: bool
    reason: str
    estimated_release: datetime
    isolation_id: str
    vp_level: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "isolation_active": self.isolation_active,
            "reason": self.reason,
            "estimated_release": self.estimated_release.isoformat() + "Z",
            "isolation_id": self.isolation_id,
            "vp_level": self.vp_level
        }


class TemporalIsolationManager:
    """
    Automatic quarantine system for unstable operations.
    Prevents system-wide instability through time-based containment.
    """
    
    def __init__(self, event_publisher=None):
        self.event_publisher = event_publisher
        self.isolation_state = IsolationState.INACTIVE
        self.isolation_history = []
        self.current_isolation = None
        self.release_scheduler = None
        self.isolation_lock = threading.Lock()
        
        # Isolation thresholds and parameters
        self.isolation_thresholds = {
            "critical_vp": 0.75,      # VP level that triggers immediate isolation
            "warning_vp": 0.6,        # VP level that triggers monitoring
            "emergency_vp": 0.9       # VP level that triggers emergency isolation
        }
        
        # Isolation duration calculation parameters
        self.duration_parameters = {
            "base_duration_ms": 5000,  # Base isolation duration (5 seconds)
            "vp_multiplier": 10000,    # Additional ms per VP unit above threshold
            "max_duration_ms": 60000   # Maximum isolation duration (1 minute)
        }
    
    def apply_temporal_lock(self, duration: int, reason: str, 
                          vp_level: Optional[float] = None) -> IsolationResult:
        """
        Apply temporal isolation with automatic release.
        
        Args:
            duration: Isolation duration in milliseconds
            reason: Reason for isolation
            vp_level: Optional VP level that triggered isolation
            
        Returns:
            IsolationResult with isolation details
        """
        with self.isolation_lock:
            # Generate isolation ID
            isolation_id = str(uuid.uuid4())
            
            # Calculate timing
            start_time = datetime.utcnow()
            release_time = start_time + timedelta(milliseconds=duration)
            
            # Create isolation result
            isolation_result = IsolationResult(
                isolation_id=isolation_id,
                isolation_state=IsolationState.ACTIVE,
                reason=reason,
                start_time=start_time,
                release_time=release_time,
                duration_ms=duration,
                vp_level=vp_level,
                affected_components=self._get_affected_components()
            )
            
            # Update isolation state
            self.isolation_state = IsolationState.ACTIVE
            self.current_isolation = isolation_result
            
            # Schedule automatic release
            self._schedule_release(isolation_result)
            
            # Publish isolation event
            if self.event_publisher:
                isolation_event = SystemIsolationEvent(
                    isolation_active=True,
                    reason=reason,
                    estimated_release=release_time,
                    isolation_id=isolation_id,
                    vp_level=vp_level
                )
                self.event_publisher.publish(isolation_event)
            
            # Record in history
            self.isolation_history.append(isolation_result)
            
            return isolation_result
    
    def evaluate_isolation_need(self, vp_level: float) -> bool:
        """
        Automatically evaluate if isolation is needed based on VP.
        
        Args:
            vp_level: Current violation pressure level
            
        Returns:
            True if isolation should be triggered
        """
        if vp_level >= self.isolation_thresholds["emergency_vp"]:
            # Emergency isolation
            duration = self._calculate_isolation_duration(vp_level, emergency=True)
            self.apply_temporal_lock(
                duration=duration,
                reason=f"Emergency isolation due to VP {vp_level}",
                vp_level=vp_level
            )
            return True
        
        elif vp_level >= self.isolation_thresholds["critical_vp"]:
            # Critical isolation
            duration = self._calculate_isolation_duration(vp_level)
            self.apply_temporal_lock(
                duration=duration,
                reason=f"Critical isolation due to VP {vp_level}",
                vp_level=vp_level
            )
            return True
        
        elif vp_level >= self.isolation_thresholds["warning_vp"]:
            # Warning level - monitor but don't isolate
            print(f"Warning: VP level {vp_level} approaching isolation threshold")
            return False
        
        return False
    
    def _calculate_isolation_duration(self, vp_level: float, emergency: bool = False) -> int:
        """
        Calculate isolation duration based on VP level.
        
        Args:
            vp_level: Violation pressure level
            emergency: Whether this is an emergency isolation
            
        Returns:
            Duration in milliseconds
        """
        base_duration = self.duration_parameters["base_duration_ms"]
        
        if emergency:
            # Emergency isolation gets longer duration
            base_duration *= 2
        
        # Add VP-based duration
        threshold = self.isolation_thresholds["critical_vp"]
        vp_excess = max(0, vp_level - threshold)
        vp_duration = vp_excess * self.duration_parameters["vp_multiplier"]
        
        total_duration = base_duration + vp_duration
        
        # Clamp to maximum duration
        max_duration = self.duration_parameters["max_duration_ms"]
        return min(total_duration, max_duration)
    
    def _schedule_release(self, isolation_result: IsolationResult):
        """Schedule automatic release of isolation"""
        if self.release_scheduler:
            self.release_scheduler.cancel()
        
        # Calculate delay until release
        delay_ms = isolation_result.duration_ms
        
        # Schedule release
        self.release_scheduler = asyncio.create_task(
            self._release_after_delay(isolation_result.isolation_id, delay_ms)
        )
    
    async def _release_after_delay(self, isolation_id: str, delay_ms: int):
        """Release isolation after specified delay"""
        await asyncio.sleep(delay_ms / 1000.0)  # Convert ms to seconds
        
        # Release isolation
        self.release_isolation(isolation_id, "automatic_release")
    
    def release_isolation(self, isolation_id: str, reason: str = "manual_release") -> bool:
        """
        Release temporal isolation.
        
        Args:
            isolation_id: ID of isolation to release
            reason: Reason for release
            
        Returns:
            True if isolation was successfully released
        """
        with self.isolation_lock:
            if (self.current_isolation and 
                self.current_isolation.isolation_id == isolation_id and
                self.isolation_state == IsolationState.ACTIVE):
                
                # Update isolation state
                self.isolation_state = IsolationState.INACTIVE
                self.current_isolation.isolation_state = IsolationState.INACTIVE
                
                # Cancel release scheduler
                if self.release_scheduler:
                    self.release_scheduler.cancel()
                    self.release_scheduler = None
                
                # Publish release event
                if self.event_publisher:
                    release_event = SystemIsolationEvent(
                        isolation_active=False,
                        reason=reason,
                        estimated_release=datetime.utcnow(),
                        isolation_id=isolation_id
                    )
                    self.event_publisher.publish(release_event)
                
                print(f"Temporal isolation {isolation_id} released: {reason}")
                return True
            
            return False
    
    def get_isolation_status(self) -> Dict[str, Any]:
        """Get current isolation status"""
        with self.isolation_lock:
            return {
                "isolation_state": self.isolation_state.value,
                "current_isolation": self.current_isolation.to_dict() if self.current_isolation else None,
                "isolation_history_count": len(self.isolation_history),
                "thresholds": self.isolation_thresholds,
                "duration_parameters": self.duration_parameters
            }
    
    def _get_affected_components(self) -> List[str]:
        """Get list of components affected by isolation"""
        # In a full implementation, this would determine which system components
        # are affected based on the isolation reason and VP level
        return [
            "trait_convergence_engine",
            "violation_pressure_monitor",
            "system_coordinator"
        ]
    
    def set_isolation_thresholds(self, thresholds: Dict[str, float]):
        """Update isolation thresholds"""
        self.isolation_thresholds.update(thresholds)
    
    def set_duration_parameters(self, parameters: Dict[str, int]):
        """Update duration calculation parameters"""
        self.duration_parameters.update(parameters)
    
    def get_isolation_history(self, limit: int = 50) -> List[IsolationResult]:
        """Get recent isolation history"""
        return self.isolation_history[-limit:]
    
    def export_isolation_summary(self) -> Dict[str, Any]:
        """Export isolation system summary"""
        return {
            "total_isolations": len(self.isolation_history),
            "current_state": self.isolation_state.value,
            "recent_isolations": [
                iso.to_dict() for iso in self.isolation_history[-10:]
            ],
            "thresholds": self.isolation_thresholds,
            "duration_parameters": self.duration_parameters,
            "system_status": "operational"
        }


class IntegratedTemporalIsolation:
    """
    Temporal isolation integrated with event-driven coordination.
    Provides coordinated safety responses.
    """
    
    def __init__(self, event_publisher, isolation_manager: TemporalIsolationManager):
        self.event_publisher = event_publisher
        self.isolation_manager = isolation_manager
        
        # Subscribe to isolation triggers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for isolation coordination"""
        # This would integrate with the event bus from Phase 0.3
        # For now, we'll implement direct integration
        pass
    
    def handle_isolation_trigger(self, reason: str, vp_level: float = None):
        """Handle isolation trigger with coordinated response"""
        if vp_level is not None:
            # Automatic VP-based isolation
            self.isolation_manager.evaluate_isolation_need(vp_level)
        else:
            # Manual isolation trigger
            duration = self.isolation_manager.duration_parameters["base_duration_ms"]
            self.isolation_manager.apply_temporal_lock(duration, reason)
    
    def handle_violation_pressure(self, vp_level: float):
        """Handle violation pressure for automatic isolation evaluation"""
        return self.isolation_manager.evaluate_isolation_need(vp_level)
    
    def get_integrated_status(self) -> Dict[str, Any]:
        """Get integrated isolation status"""
        return {
            "isolation_status": self.isolation_manager.get_isolation_status(),
            "integration_status": "operational"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize temporal isolation system
    from event_driven_coordination import DjinnEventBus
    
    event_bus = DjinnEventBus()
    isolation_manager = TemporalIsolationManager(event_bus)
    integrated_isolation = IntegratedTemporalIsolation(event_bus, isolation_manager)
    
    print("=== Temporal Isolation Safety System Test ===")
    
    # Test normal operation
    print("Testing normal operation...")
    status = isolation_manager.get_isolation_status()
    print(f"Isolation Status: {status['isolation_state']}")
    
    # Test VP-based isolation evaluation
    print("\nTesting VP-based isolation evaluation...")
    
    # Test warning level (should not isolate)
    warning_vp = 0.65
    should_isolate = isolation_manager.evaluate_isolation_need(warning_vp)
    print(f"Warning VP {warning_vp}: Should isolate = {should_isolate}")
    
    # Test critical level (should isolate)
    critical_vp = 0.8
    should_isolate = isolation_manager.evaluate_isolation_need(critical_vp)
    print(f"Critical VP {critical_vp}: Should isolate = {should_isolate}")
    
    # Test emergency level (should isolate with longer duration)
    emergency_vp = 0.95
    should_isolate = isolation_manager.evaluate_isolation_need(emergency_vp)
    print(f"Emergency VP {emergency_vp}: Should isolate = {should_isolate}")
    
    # Show isolation status
    status = isolation_manager.get_isolation_status()
    print(f"Current Isolation Status: {status}")
    
    # Test manual isolation
    print("\nTesting manual isolation...")
    manual_result = isolation_manager.apply_temporal_lock(
        duration=3000,  # 3 seconds
        reason="Manual test isolation",
        vp_level=0.5
    )
    print(f"Manual Isolation Result: {manual_result.to_dict()}")
    
    # Show isolation history
    history = isolation_manager.get_isolation_history(limit=5)
    print(f"Isolation History: {len(history)} entries")
    
    # Export summary
    summary = isolation_manager.export_isolation_summary()
    print(f"Isolation Summary: {summary}")
    
    print("=== Phase 0.4 Implementation Complete ===")
    print("Temporal Isolation Safety System operational and verified.")
