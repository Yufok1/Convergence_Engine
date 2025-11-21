"""
🦋 THE BUTTERFLY SYSTEM 🦋

The Breath: The primary driver (Explorer's breath engine)
The Butterfly: The entire system that reacts to the breath

- Central Body: Explorer (breathes and reacts to its own breath)
- Left Wing: Reality Simulator (reacts to breath)
- Right Wing: Djinn Kernel (reacts to breath)

The breath drives everything. The butterfly (all three systems) reacts to it.
"""

import sys
import os
import time
import math
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add paths
parent_path = Path(__file__).parent
explorer_path = parent_path / 'explorer'
reality_sim_path = parent_path / 'reality_simulator'
kernel_path = parent_path / 'kernel'

if str(explorer_path) not in sys.path:
    sys.path.insert(0, str(explorer_path))
if str(reality_sim_path) not in sys.path:
    sys.path.insert(0, str(reality_sim_path))
if str(kernel_path) not in sys.path:
    sys.path.insert(0, str(kernel_path))

try:
    from breath_engine import BreathEngine
    BREATH_AVAILABLE = True
except ImportError:
    BREATH_AVAILABLE = False


@dataclass
class ButterflyState:
    """The unified state of the butterfly system"""
    breath_phase: float  # 0.0 to 2π
    breath_depth: float  # 0.0 to 1.0
    breath_cycle: int
    
    # Left wing (Reality Simulator)
    left_wing_phase: str  # 'chaos' or 'precision'
    left_wing_organisms: int
    left_wing_proximity: float  # 0.0 to 1.0
    
    # Right wing (Djinn Kernel)
    right_wing_phase: str  # 'chaos' or 'precision'
    right_wing_vp: float
    right_wing_proximity: float  # 0.0 to 1.0
    
    # Unified state
    body_phase: str  # 'chaos' or 'precision' (Explorer's phase)
    unified_transition_ready: bool


class ButterflySystem:
    """
    🦋 The Butterfly System 🦋
    
    Central Body (Explorer):
    - The breath engine is the heart
    - Breathes continuously
    - Phase transitions drive the wings
    
    Left Wing (Reality Simulator):
    - Responds to breath pulse
    - Evolves generations naturally
    - Flaps in response to breath depth
    
    Right Wing (Djinn Kernel):
    - Responds to breath pulse
    - Calculates VP on events
    - Flaps in response to breath depth
    """
    
    def __init__(self):
        # The central body - Explorer's breath
        if BREATH_AVAILABLE:
            self.breath = BreathEngine()
        else:
            self.breath = None
        
        # Wing states
        self.left_wing_state = {
            'organisms': 0,
            'generation': 0,
            'modularity': 1.0,
            'phase': 'chaos',
            'last_flap': time.time()
        }
        
        self.right_wing_state = {
            'vp': 1.0,
            'vp_calculations': 0,
            'phase': 'chaos',
            'last_flap': time.time()
        }
        
        # Body state (Explorer)
        self.body_state = {
            'phase': 'genesis',  # genesis or sovereign
            'vp_history_count': 0,
            'mathematical_capability': False
        }
        
        # Butterfly state
        self.butterfly_state = None
        self.last_breath_time = time.time()
    
    def breathe(self) -> Dict[str, Any]:
        """
        The breath drives the system.
        This is the primary driver - the butterfly reacts to it.
        """
        if not self.breath:
            return {'error': 'Breath engine not available'}
        
        # Breathe
        breath_data = self.breath.breathe()
        
        # Update body state based on breath
        breath_depth = breath_data['depth']
        breath_phase = breath_data['phase']
        
        # Determine body phase from breath
        # Inhale = chaos (gathering), Exhale = precision (releasing)
        if self.breath.is_inhale_phase():
            body_phase = 'chaos'
        else:
            body_phase = 'precision'
        
        # The breath pulse affects wing motion
        breath_pulse = self.breath.get_breath_pulse()
        
        return {
            'breath_data': breath_data,
            'breath_pulse': breath_pulse,
            'body_phase': body_phase,
            'inhale': self.breath.is_inhale_phase(),
            'exhale': self.breath.is_exhale_phase()
        }
    
    def flap_left_wing(self, reality_sim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Left wing (Reality Simulator) reacts to breath.
        The breath drives the reaction - the wing maintains its own rhythm but reacts to breath state.
        """
        if not self.breath:
            return {'error': 'Breath engine not available'}
        
        # Get current breath state
        breath_state = self.breath.get_breath_state()
        breath_pulse = self.breath.get_breath_pulse()
        
        # Update wing state from Reality Simulator data
        organisms = reality_sim_data.get('organism_count', 0)
        modularity = reality_sim_data.get('modularity', 1.0)
        generation = reality_sim_data.get('generation', 0)
        
        # Determine wing phase
        # Collapse = precision, pre-collapse = chaos
        if organisms >= 500 and modularity < 0.3:
            wing_phase = 'precision'
        else:
            wing_phase = 'chaos'
        
        # Proximity to transition (0.0 to 1.0)
        proximity = min(1.0, organisms / 500.0)
        
        # Wing responds to breath pulse
        # Higher breath pulse = more wing motion
        flap_intensity = breath_pulse * proximity
        
        # Update state
        self.left_wing_state.update({
            'organisms': organisms,
            'generation': generation,
            'modularity': modularity,
            'phase': wing_phase,
            'proximity': proximity,
            'flap_intensity': flap_intensity,
            'last_flap': time.time()
        })
        
        return {
            'wing_phase': wing_phase,
            'organisms': organisms,
            'proximity': proximity,
            'flap_intensity': flap_intensity,
            'breath_pulse': breath_pulse,
            'responding_to_breath': True
        }
    
    def flap_right_wing(self, djinn_kernel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Right wing (Djinn Kernel) reacts to breath.
        The breath drives the reaction - the wing maintains its own rhythm but reacts to breath state.
        """
        if not self.breath:
            return {'error': 'Breath engine not available'}
        
        # Get current breath state
        breath_state = self.breath.get_breath_state()
        breath_pulse = self.breath.get_breath_pulse()
        
        # Update wing state from Djinn Kernel data
        vp = djinn_kernel_data.get('violation_pressure', 1.0)
        vp_calculations = djinn_kernel_data.get('vp_calculations', 0)
        
        # Determine wing phase
        # VP < 0.25 (VP0) = precision, higher VP = chaos
        if vp < 0.25:
            wing_phase = 'precision'
        else:
            wing_phase = 'chaos'
        
        # Proximity to transition (inverse of VP)
        proximity = 1.0 - min(1.0, vp)
        
        # Wing responds to breath pulse
        # Higher breath pulse = more wing motion
        flap_intensity = breath_pulse * proximity
        
        # Update state
        self.right_wing_state.update({
            'vp': vp,
            'vp_calculations': vp_calculations,
            'phase': wing_phase,
            'proximity': proximity,
            'flap_intensity': flap_intensity,
            'last_flap': time.time()
        })
        
        return {
            'wing_phase': wing_phase,
            'vp': vp,
            'proximity': proximity,
            'flap_intensity': flap_intensity,
            'breath_pulse': breath_pulse,
            'responding_to_breath': True
        }
    
    def get_butterfly_state(self) -> ButterflyState:
        """
        Get the complete butterfly state.
        The breath is the central pulse, wings respond to it.
        """
        if not self.breath:
            return None
        
        breath_state = self.breath.get_breath_state()
        
        # Determine body phase (Explorer)
        if self.breath.is_inhale_phase():
            body_phase = 'chaos'
        else:
            body_phase = 'precision'
        
        # Check if unified transition is ready
        left_ready = (self.left_wing_state['phase'] == 'precision')
        right_ready = (self.right_wing_state['phase'] == 'precision')
        body_ready = (self.body_state['phase'] == 'sovereign')
        
        unified_transition_ready = left_ready or right_ready or body_ready
        
        return ButterflyState(
            breath_phase=breath_state['phase'],
            breath_depth=breath_state['depth'],
            breath_cycle=breath_state['cycle_count'],
            
            left_wing_phase=self.left_wing_state['phase'],
            left_wing_organisms=self.left_wing_state['organisms'],
            left_wing_proximity=self.left_wing_state.get('proximity', 0.0),
            
            right_wing_phase=self.right_wing_state['phase'],
            right_wing_vp=self.right_wing_state['vp'],
            right_wing_proximity=self.right_wing_state.get('proximity', 0.0),
            
            body_phase=body_phase,
            unified_transition_ready=unified_transition_ready
        )
    
    def fly(self, reality_sim_data: Optional[Dict] = None, 
            djinn_kernel_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        The butterfly flies.
        The breath drives, the butterfly (all systems) reacts.
        """
        # The breath drives (primary driver)
        breath_result = self.breathe()
        
        # Left wing reacts to breath
        if reality_sim_data:
            left_wing_result = self.flap_left_wing(reality_sim_data)
        else:
            left_wing_result = {'status': 'no_data'}
        
        # Right wing reacts to breath
        if djinn_kernel_data:
            right_wing_result = self.flap_right_wing(djinn_kernel_data)
        else:
            right_wing_result = {'status': 'no_data'}
        
        # Get unified butterfly state
        butterfly_state = self.get_butterfly_state()
        
        return {
            'breath': breath_result,
            'left_wing': left_wing_result,
            'right_wing': right_wing_result,
            'butterfly_state': butterfly_state,
            'timestamp': time.time()
        }


# Example usage
if __name__ == "__main__":
    butterfly = ButterflySystem()
    
    # Simulate flight
    print("🦋 The Butterfly System 🦋")
    print("=" * 60)
    
    # Simulate some data
    reality_sim_data = {
        'organism_count': 300,
        'modularity': 0.4,
        'generation': 50
    }
    
    djinn_kernel_data = {
        'violation_pressure': 0.3,
        'vp_calculations': 25
    }
    
    # Fly
    flight_result = butterfly.fly(reality_sim_data, djinn_kernel_data)
    
    print(f"\nBreath: Cycle {flight_result['breath']['breath_data']['cycle_count']}, "
          f"Depth: {flight_result['breath']['breath_data']['depth']:.3f}, "
          f"Phase: {flight_result['breath']['body_phase']}")
    
    print(f"\nLeft Wing (Reality Sim): {flight_result['left_wing'].get('wing_phase', 'unknown')}, "
          f"Organisms: {flight_result['left_wing'].get('organisms', 0)}, "
          f"Flap Intensity: {flight_result['left_wing'].get('flap_intensity', 0):.3f}")
    
    print(f"\nRight Wing (Djinn Kernel): {flight_result['right_wing'].get('wing_phase', 'unknown')}, "
          f"VP: {flight_result['right_wing'].get('vp', 0):.3f}, "
          f"Flap Intensity: {flight_result['right_wing'].get('flap_intensity', 0):.3f}")
    
    if flight_result['butterfly_state']:
        state = flight_result['butterfly_state']
        print(f"\n🦋 Unified State:")
        print(f"   Body Phase: {state.body_phase}")
        print(f"   Left Wing: {state.left_wing_phase} ({state.left_wing_organisms} organisms)")
        print(f"   Right Wing: {state.right_wing_phase} (VP: {state.right_wing_vp:.3f})")
        print(f"   Transition Ready: {state.unified_transition_ready}")

