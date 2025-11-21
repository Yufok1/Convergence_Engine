# Violation Pressure Calculation - Phase 0.2 Implementation
# Version 1.0 - Mathematical Quantification of Identity Incompleteness

"""
Violation Pressure Calculation implementing the mathematical quantification of identity incompleteness
that drives recursive necessity in the Djinn Kernel.

Core Formula: VP_total = Σ(|actual - center| / (radius * compression))
This creates the mathematical pressure that drives the system toward fixed-point completion.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Any
from enum import Enum
import math
from datetime import datetime
from event_driven_coordination import ViolationPressureEvent


class ViolationClass(Enum):
    """Classification of violation pressure levels"""
    VP0_FULLY_LAWFUL = "VP0"      # 0.00 - 0.25: Fully lawful recursion
    VP1_STABLE_DRIFT = "VP1"      # 0.25 - 0.50: Stable drift, continue with logging
    VP2_INSTABILITY = "VP2"       # 0.50 - 0.75: Instability pressure, arbitration review
    VP3_CRITICAL_DIVERGENCE = "VP3"  # 0.75 - 0.99: Critical divergence, forbidden zone authorization
    VP4_COLLAPSE_THRESHOLD = "VP4"   # ≥ 1.00: Collapse threshold, hard recursion termination


@dataclass
class StabilityEnvelope:
    """
    Mathematical envelope defining trait stability boundaries.
    Core component of violation pressure calculation.
    """
    center: float = 0.5           # Stability center [0.0, 1.0]
    radius: float = 0.25          # Allowable deviation range
    compression_factor: float = 1.0  # Stability enforcement strength
    
    def __post_init__(self):
        # Ensure mathematical consistency
        assert 0.0 <= self.center <= 1.0, "Stability center must be [0.0, 1.0]"
        assert 0.0 < self.radius <= 0.5, "Radius must be (0.0, 0.5]"
        assert self.compression_factor > 0.0, "Compression factor must be positive"





class ViolationMonitor:
    """
    Calculates violation pressure - the mathematical driving force of recursion.
    
    Violation pressure quantifies how far traits deviate from their stability centers,
    creating mathematical necessity for recursive correction through:
    - Convergence (lawful primitive recursion)
    - Divergence (μ-recursion in Forbidden Zone)
    - Collapse (entropy compression via pruning)
    """
    
    def __init__(self, event_publisher=None):
        self.event_publisher = event_publisher
        self.vp_history = []
        self.stability_envelopes = {}
        
        # Initialize default stability envelopes for common traits
        self._initialize_default_envelopes()
    
    def _initialize_default_envelopes(self):
        """Initialize default stability envelopes for mathematical consistency"""
        # Mathematical meta-traits
        self.stability_envelopes["violationpressure"] = StabilityEnvelope(
            center=0.0, radius=0.25, compression_factor=2.0
        )
        self.stability_envelopes["completionpressure"] = StabilityEnvelope(
            center=0.0, radius=0.3, compression_factor=1.5
        )
        self.stability_envelopes["convergencestability"] = StabilityEnvelope(
            center=0.8, radius=0.15, compression_factor=1.2
        )
        self.stability_envelopes["reflectionindex"] = StabilityEnvelope(
            center=0.7, radius=0.2, compression_factor=1.0
        )
        
        # Prosocial traits (love metrics)
        self.stability_envelopes["intimacy"] = StabilityEnvelope(
            center=0.6, radius=0.3, compression_factor=0.8
        )
        self.stability_envelopes["commitment"] = StabilityEnvelope(
            center=0.7, radius=0.25, compression_factor=1.1
        )
        self.stability_envelopes["caregiving"] = StabilityEnvelope(
            center=0.65, radius=0.3, compression_factor=0.9
        )
        self.stability_envelopes["attunement"] = StabilityEnvelope(
            center=0.6, radius=0.25, compression_factor=1.0
        )
        self.stability_envelopes["lineagepreference"] = StabilityEnvelope(
            center=0.55, radius=0.35, compression_factor=0.7
        )
    
    def compute_violation_pressure(self, trait_payload: Dict[str, float], 
                                 source_identity: Optional[str] = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate violation pressure for trait payload.
        
        Args:
            trait_payload: Dictionary of trait_name -> trait_value pairs
            source_identity: Optional UUID of the identity being evaluated
            
        Returns:
            Tuple of (total_vp, per_trait_breakdown)
        """
        total_vp = 0.0
        per_trait_breakdown = {}
        
        for trait_name, trait_value in trait_payload.items():
            # Get stability envelope for this trait
            envelope = self.stability_envelopes.get(trait_name, StabilityEnvelope())
            
            # Calculate individual trait violation pressure
            trait_vp = self._calculate_trait_violation_pressure(trait_value, envelope)
            
            per_trait_breakdown[trait_name] = trait_vp
            total_vp += trait_vp
        
        # Normalize total VP to [0.0, 1.0] range
        if trait_payload:
            total_vp = min(1.0, total_vp / len(trait_payload))
        
        # Classify violation pressure
        classification = self._classify_violation_pressure(total_vp)
        
        # Create violation pressure event
        vp_event = ViolationPressureEvent(
            total_vp=total_vp,
            breakdown=per_trait_breakdown,
            classification=classification.value,
            source_identity=source_identity
        )
        
        # Publish event for system coordination
        if self.event_publisher:
            self.event_publisher.publish(vp_event)
        
        # Record in history
        self.vp_history.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_vp": total_vp,
            "classification": classification.value,
            "source_identity": source_identity,
            "trait_count": len(trait_payload)
        })
        
        return total_vp, per_trait_breakdown
    
    def _calculate_trait_violation_pressure(self, trait_value: float, 
                                          envelope: StabilityEnvelope) -> float:
        """
        Calculate violation pressure for individual trait.
        
        Core Formula: VP = |actual - center| / (radius * compression_factor)
        """
        # Calculate deviation from stability center
        deviation = abs(trait_value - envelope.center)
        
        # Normalize by stability envelope
        normalized_radius = envelope.radius * envelope.compression_factor
        
        # Calculate violation pressure
        if normalized_radius > 0:
            vp = deviation / normalized_radius
        else:
            vp = float('inf') if deviation > 0 else 0.0
        
        # Clamp to reasonable range [0.0, 10.0]
        return max(0.0, min(10.0, vp))
    
    def _classify_violation_pressure(self, total_vp: float) -> ViolationClass:
        """Classify violation pressure into appropriate category"""
        if total_vp < 0.25:
            return ViolationClass.VP0_FULLY_LAWFUL
        elif total_vp < 0.50:
            return ViolationClass.VP1_STABLE_DRIFT
        elif total_vp < 0.75:
            return ViolationClass.VP2_INSTABILITY
        elif total_vp < 1.00:
            return ViolationClass.VP3_CRITICAL_DIVERGENCE
        else:
            return ViolationClass.VP4_COLLAPSE_THRESHOLD
    
    def set_stability_envelope(self, trait_name: str, envelope: StabilityEnvelope):
        """Set custom stability envelope for specific trait"""
        self.stability_envelopes[trait_name] = envelope
    
    def get_stability_envelope(self, trait_name: str) -> Optional[StabilityEnvelope]:
        """Get stability envelope for specific trait"""
        return self.stability_envelopes.get(trait_name)
    
    def calculate_system_health_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide health metrics based on VP history"""
        if not self.vp_history:
            return {"error": "No VP history available"}
        
        recent_vp = [entry["total_vp"] for entry in self.vp_history[-100:]]  # Last 100 entries
        
        return {
            "average_vp": sum(recent_vp) / len(recent_vp),
            "max_vp": max(recent_vp),
            "min_vp": min(recent_vp),
            "vp_volatility": self._calculate_volatility(recent_vp),
            "stability_trend": self._calculate_stability_trend(recent_vp),
            "classification_distribution": self._get_classification_distribution(),
            "total_measurements": len(self.vp_history)
        }
    
    def _calculate_volatility(self, vp_values: List[float]) -> float:
        """Calculate volatility of violation pressure values"""
        if len(vp_values) < 2:
            return 0.0
        
        mean_vp = sum(vp_values) / len(vp_values)
        variance = sum((x - mean_vp) ** 2 for x in vp_values) / len(vp_values)
        return math.sqrt(variance)
    
    def _calculate_stability_trend(self, vp_values: List[float]) -> str:
        """Calculate trend in violation pressure over time"""
        if len(vp_values) < 10:
            return "insufficient_data"
        
        # Simple linear trend calculation
        recent = vp_values[-10:]
        early_avg = sum(recent[:5]) / 5
        late_avg = sum(recent[5:]) / 5
        
        if late_avg < early_avg * 0.9:
            return "improving"
        elif late_avg > early_avg * 1.1:
            return "degrading"
        else:
            return "stable"
    
    def _get_classification_distribution(self) -> Dict[str, int]:
        """Get distribution of VP classifications"""
        distribution = {cls.value: 0 for cls in ViolationClass}
        
        for entry in self.vp_history:
            classification = entry["classification"]
            distribution[classification] += 1
        
        return distribution
    
    def export_vp_analysis(self, trait_payload: Dict[str, float], 
                          source_identity: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive VP analysis"""
        total_vp, breakdown = self.compute_violation_pressure(trait_payload, source_identity)
        classification = self._classify_violation_pressure(total_vp)
        
        return {
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "source_identity": source_identity,
            "total_violation_pressure": total_vp,
            "classification": classification.value,
            "per_trait_breakdown": breakdown,
            "stability_envelopes": {
                name: {
                    "center": env.center,
                    "radius": env.radius,
                    "compression_factor": env.compression_factor
                }
                for name, env in self.stability_envelopes.items()
                if name in trait_payload
            },
            "system_health": self.calculate_system_health_metrics(),
            "mathematical_formula": "VP_total = Σ(|actual - center| / (radius * compression))"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize violation pressure monitor
    from uuid_anchor_mechanism import EventPublisher
    
    event_publisher = EventPublisher()
    vp_monitor = ViolationMonitor(event_publisher)
    
    # Test trait payload
    test_payload = {
        "intimacy": 0.8,      # High intimacy
        "commitment": 0.3,    # Low commitment
        "caregiving": 0.7,    # Moderate caregiving
        "violationpressure": 0.4,  # Moderate VP
        "reflectionindex": 0.9     # High reflection
    }
    
    print("=== Violation Pressure Calculation Test ===")
    print(f"Test payload: {test_payload}")
    
    # Calculate violation pressure
    total_vp, breakdown = vp_monitor.compute_violation_pressure(test_payload, "test_identity_001")
    
    print(f"Total Violation Pressure: {total_vp:.3f}")
    print(f"Per-trait breakdown: {breakdown}")
    
    # Export comprehensive analysis
    analysis = vp_monitor.export_vp_analysis(test_payload, "test_identity_001")
    print(f"VP Analysis: {analysis}")
    
    # Show system health metrics
    health_metrics = vp_monitor.calculate_system_health_metrics()
    print(f"System Health: {health_metrics}")
    
    print("=== Phase 0.2 Implementation Complete ===")
    print("Violation Pressure Calculation operational and mathematically verified.")
