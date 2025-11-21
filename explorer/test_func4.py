"""
Unified Exploration Counter
Explorer integration module: Tracks exploration across all three systems
"""

import sys
import os
import json
from pathlib import Path

def main():
    """
    Track total exploration across Reality Simulator, Explorer, and Djinn Kernel.
    
    Returns traits indicating exploration progress and conversion factors.
    """
    # Add paths
    reality_sim_path = Path(__file__).parent.parent / 'reality_simulator'
    kernel_path = Path(__file__).parent.parent / 'kernel'
    
    if str(reality_sim_path) not in sys.path:
        sys.path.insert(0, str(reality_sim_path))
    if str(kernel_path) not in sys.path:
        sys.path.insert(0, str(kernel_path))
    
    try:
        # Get Reality Simulator exploration (organism count)
        shared_state_path = Path(__file__).parent.parent / 'data' / 'shared_state.json'
        reality_sim_explorations = 0
        
        if shared_state_path.exists():
            with open(shared_state_path, 'r') as f:
                shared_state = json.load(f)
            network_data = shared_state.get('network', {})
            reality_sim_explorations = network_data.get('organisms', 0)
        
        # Get Explorer exploration (VP calculations)
        explorer_explorations = 0
        try:
            from sentinel import Sentinel
            sentinel = Sentinel()
            explorer_explorations = len(sentinel.vp_history)
        except:
            pass
        
        # Get Djinn Kernel exploration (trait explorations)
        djinn_kernel_explorations = 0
        try:
            from violation_pressure_calculation import ViolationMonitor
            vp_monitor = ViolationMonitor()
            djinn_kernel_explorations = len(vp_monitor.vp_history)
        except:
            pass
        
        # Conversion factor: 500:50 = 10:1
        exploration_to_precision_ratio = 10.0
        
        # Normalize explorations
        reality_sim_norm = reality_sim_explorations / 500.0  # Threshold: 500
        explorer_norm = explorer_explorations / 50.0         # Threshold: 50
        djinn_kernel_norm = djinn_kernel_explorations / 50.0  # Threshold: 50 (same as Explorer)
        
        # Weighted average (all systems contribute equally)
        total_exploration = (reality_sim_norm + explorer_norm + djinn_kernel_norm) / 3.0
        
        # Check if any system has hit threshold
        reality_sim_at_threshold = reality_sim_explorations >= 500
        explorer_at_threshold = explorer_explorations >= 50
        djinn_kernel_at_threshold = djinn_kernel_explorations >= 50
        
        any_at_threshold = reality_sim_at_threshold or explorer_at_threshold or djinn_kernel_at_threshold
        
        # Return traits
        traits = {
            'reality_sim_explorations': reality_sim_explorations,
            'reality_sim_normalized': reality_sim_norm,
            'reality_sim_at_threshold': 1 if reality_sim_at_threshold else 0,
            
            'explorer_explorations': explorer_explorations,
            'explorer_normalized': explorer_norm,
            'explorer_at_threshold': 1 if explorer_at_threshold else 0,
            
            'djinn_kernel_explorations': djinn_kernel_explorations,
            'djinn_kernel_normalized': djinn_kernel_norm,
            'djinn_kernel_at_threshold': 1 if djinn_kernel_at_threshold else 0,
            
            'total_exploration': total_exploration,
            'exploration_to_precision_ratio': exploration_to_precision_ratio,
            'any_at_threshold': 1 if any_at_threshold else 0,
            'all_at_threshold': 1 if (reality_sim_at_threshold and explorer_at_threshold and djinn_kernel_at_threshold) else 0
        }
        
        # Output traits
        print(json.dumps(traits))
        return traits
        
    except Exception as e:
        # Return error traits
        print(f"[ERROR] Exploration counter: {e}", file=sys.stderr)
        return {
            'reality_sim_explorations': 0,
            'reality_sim_normalized': 0.0,
            'reality_sim_at_threshold': 0,
            'explorer_explorations': 0,
            'explorer_normalized': 0.0,
            'explorer_at_threshold': 0,
            'djinn_kernel_explorations': 0,
            'djinn_kernel_normalized': 0.0,
            'djinn_kernel_at_threshold': 0,
            'total_exploration': 0.0,
            'exploration_to_precision_ratio': 10.0,
            'any_at_threshold': 0,
            'all_at_threshold': 0,
            'error': str(e)
        }

if __name__ == "__main__":
    traits = main()
    print("Exploration traits:", json.dumps(traits, indent=2))
