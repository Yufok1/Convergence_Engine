"""
Phase Transition Detector
Explorer integration module: Detects chaos→precision transition across all systems
"""

import sys
import os
import json
from pathlib import Path

def main():
    """
    Detect phase transition (chaos→precision) across all three systems.
    
    Returns traits indicating transition status and proximity.
    """
    # Add paths
    reality_sim_path = Path(__file__).parent.parent / 'reality_simulator'
    kernel_path = Path(__file__).parent.parent / 'kernel'
    
    if str(reality_sim_path) not in sys.path:
        sys.path.insert(0, str(reality_sim_path))
    if str(kernel_path) not in sys.path:
        sys.path.insert(0, str(kernel_path))
    
    try:
        # Get Reality Simulator state
        shared_state_path = Path(__file__).parent.parent / 'data' / 'shared_state.json'
        reality_sim_ready = False
        reality_sim_proximity = 0.0
        
        if shared_state_path.exists():
            with open(shared_state_path, 'r') as f:
                shared_state = json.load(f)
            network_data = shared_state.get('network', {})
            org_count = network_data.get('organisms', 0)
            modularity = network_data.get('modularity', 1.0)
            clustering = network_data.get('clustering_coefficient', 0.0)
            path_length = network_data.get('average_path_length', float('inf'))
            
            # Check collapse conditions
            reality_sim_ready = (
                org_count >= 500 and
                modularity < 0.3 and
                clustering > 0.5 and
                path_length < 3.0
            )
            reality_sim_proximity = min(1.0, org_count / 500.0)
        
        # Get Explorer state (from current system)
        # Explorer needs 50 VP calculations and mathematical capability
        explorer_ready = False
        explorer_proximity = 0.0
        
        # This would be set by Explorer's main controller
        # For now, we'll check if we can detect it
        try:
            from sentinel import Sentinel
            sentinel = Sentinel()
            vp_calculations = len(sentinel.vp_history)
            explorer_proximity = min(1.0, vp_calculations / 50.0)
            explorer_ready = sentinel.check_mathematical_capability()
        except:
            pass
        
        # Get Djinn Kernel state
        djinn_kernel_ready = False
        djinn_kernel_proximity = 0.0
        
        try:
            from violation_pressure_calculation import ViolationMonitor
            vp_monitor = ViolationMonitor()
            if vp_monitor.vp_history:
                recent_vp = vp_monitor.vp_history[-1]
                total_vp = recent_vp.get('total_vp', 1.0)
                # VP < 0.25 (VP0) = ready for precision
                djinn_kernel_ready = total_vp < 0.25
                djinn_kernel_proximity = 1.0 - min(1.0, total_vp)  # Inverse of VP
        except:
            pass
        
        # Unified transition detection
        # Transition when ANY system is ready (chaos→precision)
        transition_ready = reality_sim_ready or explorer_ready or djinn_kernel_ready
        total_proximity = (reality_sim_proximity + explorer_proximity + djinn_kernel_proximity) / 3.0
        
        # Return traits
        traits = {
            'reality_sim_ready': 1 if reality_sim_ready else 0,
            'reality_sim_proximity': reality_sim_proximity,
            'explorer_ready': 1 if explorer_ready else 0,
            'explorer_proximity': explorer_proximity,
            'djinn_kernel_ready': 1 if djinn_kernel_ready else 0,
            'djinn_kernel_proximity': djinn_kernel_proximity,
            'transition_ready': 1 if transition_ready else 0,
            'total_proximity': total_proximity,
            'phase': 'precision' if transition_ready else 'chaos',
            'system_alignment': 1.0 if (reality_sim_ready and explorer_ready and djinn_kernel_ready) else 0.0
        }
        
        # Output traits
        print(json.dumps(traits))
        return traits
        
    except Exception as e:
        # Return error traits
        print(f"[ERROR] Phase transition detector: {e}", file=sys.stderr)
        return {
            'reality_sim_ready': 0,
            'reality_sim_proximity': 0.0,
            'explorer_ready': 0,
            'explorer_proximity': 0.0,
            'djinn_kernel_ready': 0,
            'djinn_kernel_proximity': 0.0,
            'transition_ready': 0,
            'total_proximity': 0.0,
            'phase': 'chaos',
            'system_alignment': 0.0,
            'error': str(e)
        }

if __name__ == "__main__":
    traits = main()
    print("Transition traits:", json.dumps(traits, indent=2))
