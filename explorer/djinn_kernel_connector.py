"""
Djinn Kernel Connector for Explorer
Direct connection to Djinn Kernel components
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add kernel to path
kernel_path = Path(__file__).parent.parent / 'kernel'
if str(kernel_path) not in sys.path:
    sys.path.insert(0, str(kernel_path))

try:
    from violation_pressure_calculation import ViolationMonitor, ViolationClass
    from uuid_anchor_mechanism import UUIDanchor
    from event_driven_coordination import DjinnEventBus, SystemCoordinator
    DJINN_KERNEL_AVAILABLE = True
except ImportError:
    DJINN_KERNEL_AVAILABLE = False


class DjinnKernelConnector:
    """
    Connects Explorer directly to Djinn Kernel components.
    Uses Explorer's facilities to process Djinn Kernel data.
    """
    
    def __init__(self):
        if DJINN_KERNEL_AVAILABLE:
            self.vp_monitor = ViolationMonitor()
            self.uuid_anchor = UUIDanchor()
            self.event_bus = DjinnEventBus()
            self.coordinator = SystemCoordinator(self.event_bus)
        else:
            self.vp_monitor = None
            self.uuid_anchor = None
            self.event_bus = None
            self.coordinator = None
    
    def calculate_vp_from_traits(self, trait_payload: Dict[str, float], 
                                 source_identity: Optional[str] = None) -> Tuple[float, Dict[str, float]]:
        """Calculate VP from trait payload"""
        if not self.vp_monitor:
            return 0.0, {}
        
        return self.vp_monitor.compute_violation_pressure(trait_payload, source_identity)
    
    def get_vp_classification(self, vp: float) -> str:
        """Get VP classification"""
        if not self.vp_monitor:
            return 'VP0'
        
        classification = self.vp_monitor._classify_violation_pressure(vp)
        return classification.value
    
    def anchor_trait_payload(self, payload: Dict[str, Any]) -> Optional[str]:
        """Anchor trait payload using UUID mechanism"""
        if not self.uuid_anchor:
            return None
        
        uuid = self.uuid_anchor.anchor_trait(payload)
        return str(uuid)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get Djinn Kernel system health metrics"""
        if not self.vp_monitor:
            return {'error': 'Djinn Kernel not available'}
        
        return self.vp_monitor.calculate_system_health_metrics()
    
    def get_vp_history(self) -> list:
        """Get VP calculation history"""
        if not self.vp_monitor:
            return []
        
        return self.vp_monitor.vp_history
    
    def get_exploration_count(self) -> int:
        """Get exploration count (number of VP calculations)"""
        if not self.vp_monitor:
            return 0
        
        return len(self.vp_monitor.vp_history)
    
    def is_precision_phase(self) -> bool:
        """Check if in precision phase (VP < 0.25, VP0)"""
        if not self.vp_monitor or not self.vp_monitor.vp_history:
            return False
        
        recent_vp = self.vp_monitor.vp_history[-1]
        total_vp = recent_vp.get('total_vp', 1.0)
        return total_vp < 0.25  # VP0 threshold

