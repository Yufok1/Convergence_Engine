"""
Unified Transition Manager
Manages chaos→precision transition across all three systems using Explorer facilities
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add paths
parent_path = Path(__file__).parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

try:
    from explorer.reality_simulator_connector import RealitySimulatorConnector
    from explorer.djinn_kernel_connector import DjinnKernelConnector
    from explorer.integration_bridge import ExplorerIntegrationBridge
    from sentinel import Sentinel
    from kernel import Kernel
    CONNECTORS_AVAILABLE = True
except ImportError:
    CONNECTORS_AVAILABLE = False


@dataclass
class TransitionState:
    """State of chaos→precision transition"""
    reality_sim_ready: bool = False
    explorer_ready: bool = False
    djinn_kernel_ready: bool = False
    transition_triggered: bool = False
    transition_time: Optional[float] = None


class UnifiedTransitionManager:
    """
    Manages the unified chaos→precision transition using Explorer's facilities.
    
    Uses:
    - Reality Simulator Connector for network state
    - Djinn Kernel Connector for VP state
    - Explorer's Sentinel for mathematical capability
    - Explorer's Breath Engine for timing
    - Explorer's Mirror Systems for analysis
    """
    
    def __init__(self):
        self.reality_sim_connector = RealitySimulatorConnector() if CONNECTORS_AVAILABLE else None
        self.djinn_kernel_connector = DjinnKernelConnector() if CONNECTORS_AVAILABLE else None
        self.integration_bridge = ExplorerIntegrationBridge() if CONNECTORS_AVAILABLE else None
        
        # Transition state
        self.transition_state = TransitionState()
        self.exploration_to_precision_ratio = 10.0  # 500:50 = 10:1
        
        # Explorer components
        try:
            from sentinel import Sentinel
            from breath_engine import BreathEngine
            from mirror_systems import MirrorOfInsight
            self.sentinel = Sentinel()
            self.breath_engine = BreathEngine()
            self.mirror_insight = MirrorOfInsight()
        except:
            self.sentinel = None
            self.breath_engine = None
            self.mirror_insight = None
    
    def check_reality_simulator_ready(self) -> bool:
        """Check if Reality Simulator is ready for transition"""
        if not self.reality_sim_connector:
            return False
        
        return self.reality_sim_connector.is_collapsed()
    
    def check_explorer_ready(self) -> bool:
        """Check if Explorer is ready for transition (mathematical capability)"""
        if not self.sentinel:
            return False
        
        return self.sentinel.check_mathematical_capability()
    
    def check_djinn_kernel_ready(self) -> bool:
        """Check if Djinn Kernel is ready for transition (VP < 0.25)"""
        if not self.djinn_kernel_connector:
            return False
        
        return self.djinn_kernel_connector.is_precision_phase()
    
    def check_unified_transition(self) -> Dict[str, Any]:
        """Check if unified transition should occur"""
        # Check each system
        reality_sim_ready = self.check_reality_simulator_ready()
        explorer_ready = self.check_explorer_ready()
        djinn_kernel_ready = self.check_djinn_kernel_ready()
        
        # Update transition state
        self.transition_state.reality_sim_ready = reality_sim_ready
        self.transition_state.explorer_ready = explorer_ready
        self.transition_state.djinn_kernel_ready = djinn_kernel_ready
        
        # Transition when ANY system is ready (unified trigger)
        transition_ready = reality_sim_ready or explorer_ready or djinn_kernel_ready
        
        # Get exploration counts
        reality_sim_explorations = (
            self.reality_sim_connector.get_exploration_count() 
            if self.reality_sim_connector else 0
        )
        explorer_explorations = (
            len(self.sentinel.vp_history) if self.sentinel else 0
        )
        djinn_kernel_explorations = (
            self.djinn_kernel_connector.get_exploration_count()
            if self.djinn_kernel_connector else 0
        )
        
        # Normalize explorations
        reality_sim_norm = reality_sim_explorations / 500.0
        explorer_norm = explorer_explorations / 50.0
        djinn_kernel_norm = djinn_kernel_explorations / 50.0
        
        total_exploration = (reality_sim_norm + explorer_norm + djinn_kernel_norm) / 3.0
        
        # Trigger transition if ready and not already triggered
        if transition_ready and not self.transition_state.transition_triggered:
            self.transition_state.transition_triggered = True
            self.transition_state.transition_time = time.time()
            self._trigger_transition()
        
        return {
            'reality_sim_ready': reality_sim_ready,
            'explorer_ready': explorer_ready,
            'djinn_kernel_ready': djinn_kernel_ready,
            'transition_ready': transition_ready,
            'transition_triggered': self.transition_state.transition_triggered,
            'reality_sim_explorations': reality_sim_explorations,
            'explorer_explorations': explorer_explorations,
            'djinn_kernel_explorations': djinn_kernel_explorations,
            'total_exploration': total_exploration,
            'phase': 'precision' if transition_ready else 'chaos'
        }
    
    def _trigger_transition(self):
        """Trigger precision phase in all systems"""
        print("[Unified Transition] 🌉 CHAOS→PRECISION TRANSITION TRIGGERED")
        print(f"[Unified Transition] Reality Simulator: {self.transition_state.reality_sim_ready}")
        print(f"[Unified Transition] Explorer: {self.transition_state.explorer_ready}")
        print(f"[Unified Transition] Djinn Kernel: {self.transition_state.djinn_kernel_ready}")
        
        # Synchronize breath engine
        if self.breath_engine:
            # Adjust breath rate for precision phase (slower, more stable)
            self.breath_engine.adjust_breath_rate(0.5)  # Slower breathing
        
        # Update mirror systems
        if self.mirror_insight:
            system_state = {
                'phase': 'precision',
                'transition_time': self.transition_state.transition_time
            }
            self.mirror_insight.reflect(system_state)
    
    def get_transition_status(self) -> Dict[str, Any]:
        """Get current transition status"""
        transition_check = self.check_unified_transition()
        
        return {
            'transition_state': {
                'reality_sim_ready': self.transition_state.reality_sim_ready,
                'explorer_ready': self.transition_state.explorer_ready,
                'djinn_kernel_ready': self.transition_state.djinn_kernel_ready,
                'transition_triggered': self.transition_state.transition_triggered,
                'transition_time': self.transition_state.transition_time
            },
            'current_check': transition_check,
            'exploration_ratio': self.exploration_to_precision_ratio
        }


# Example usage
if __name__ == "__main__":
    manager = UnifiedTransitionManager()
    status = manager.get_transition_status()
    print("Transition Status:", json.dumps(status, indent=2, default=str))

