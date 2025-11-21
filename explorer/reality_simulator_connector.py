"""
Reality Simulator Connector for Explorer
Direct connection to Reality Simulator using phase sync bridge
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add Reality Simulator to path
reality_sim_path = Path(__file__).parent.parent / 'reality_simulator'
if str(reality_sim_path) not in sys.path:
    sys.path.insert(0, str(reality_sim_path))

try:
    from phase_sync_bridge import PhaseSynchronizationBridge, NetworkPhaseMetrics
    PHASE_BRIDGE_AVAILABLE = True
except ImportError:
    PHASE_BRIDGE_AVAILABLE = False


class RealitySimulatorConnector:
    """
    Connects Explorer directly to Reality Simulator's phase sync bridge.
    Uses Explorer's facilities to process Reality Simulator data.
    """
    
    def __init__(self):
        self.phase_bridge = PhaseSynchronizationBridge() if PHASE_BRIDGE_AVAILABLE else None
        
    def get_network_metrics(self) -> Optional[NetworkPhaseMetrics]:
        """Get current network metrics from phase bridge"""
        if not self.phase_bridge:
            return None
        return self.phase_bridge.network_metrics
    
    def update_network_state(self, network_data: Dict[str, Any]) -> bool:
        """Update network state and detect collapse"""
        if not self.phase_bridge:
            return False
        
        collapsed = self.phase_bridge.update_network_metrics(network_data)
        return collapsed
    
    def get_collapse_proximity(self) -> float:
        """Get how close network is to collapse"""
        if not self.phase_bridge:
            return 0.0
        
        metrics = self.phase_bridge.network_metrics
        return metrics.calculate_collapse_proximity()
    
    def is_collapsed(self) -> bool:
        """Check if network has collapsed"""
        if not self.phase_bridge:
            return False
        
        metrics = self.phase_bridge.network_metrics
        return metrics.detect_collapse()
    
    def get_exploration_count(self) -> int:
        """Get unified exploration count from phase bridge"""
        if not self.phase_bridge:
            return 0
        
        return self.phase_bridge.reality_sim_explorations

