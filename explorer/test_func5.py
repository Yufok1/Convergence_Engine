"""
Integration Coordinator
Explorer integration module: Coordinates all three systems
"""

import sys
import os
import json
import time
from pathlib import Path

def main():
    """
    Coordinate Reality Simulator, Explorer, and Djinn Kernel.
    
    Returns traits indicating coordination health and sync status.
    """
    # Add paths
    reality_sim_path = Path(__file__).parent.parent / 'reality_simulator'
    kernel_path = Path(__file__).parent.parent / 'kernel'
    
    if str(reality_sim_path) not in sys.path:
        sys.path.insert(0, str(reality_sim_path))
    if str(kernel_path) not in sys.path:
        sys.path.insert(0, str(kernel_path))
    
    try:
        coordination_status = {
            'reality_simulator': 'unknown',
            'explorer': 'unknown',
            'djinn_kernel': 'unknown'
        }
        
        # Check Reality Simulator
        shared_state_path = Path(__file__).parent.parent / 'data' / 'shared_state.json'
        if shared_state_path.exists():
            # Check if recently updated (within last 10 seconds)
            mtime = shared_state_path.stat().st_mtime
            if time.time() - mtime < 10:
                coordination_status['reality_simulator'] = 'active'
            else:
                coordination_status['reality_simulator'] = 'stale'
        else:
            coordination_status['reality_simulator'] = 'inactive'
        
        # Check Explorer
        try:
            from sentinel import Sentinel
            from kernel import Kernel
            sentinel = Sentinel()
            kernel = Kernel()
            if sentinel and kernel:
                coordination_status['explorer'] = 'active'
        except:
            coordination_status['explorer'] = 'inactive'
        
        # Check Djinn Kernel
        try:
            from violation_pressure_calculation import ViolationMonitor
            vp_monitor = ViolationMonitor()
            if vp_monitor:
                coordination_status['djinn_kernel'] = 'active'
        except:
            coordination_status['djinn_kernel'] = 'inactive'
        
        # Calculate coordination health
        active_count = sum(1 for status in coordination_status.values() if status == 'active')
        coordination_health = active_count / 3.0
        
        # Check synchronization
        all_active = all(status == 'active' for status in coordination_status.values())
        sync_status = 'synchronized' if all_active else 'partial' if active_count > 0 else 'unsynchronized'
        
        # Return traits
        traits = {
            'coordination_health': coordination_health,
            'sync_status': sync_status,
            'reality_simulator_status': coordination_status['reality_simulator'],
            'explorer_status': coordination_status['explorer'],
            'djinn_kernel_status': coordination_status['djinn_kernel'],
            'active_systems': active_count,
            'all_systems_active': 1 if all_active else 0,
            'timestamp': time.time()
        }
        
        # Output traits
        print(json.dumps(traits))
        return traits
        
    except Exception as e:
        # Return error traits
        print(f"[ERROR] Integration coordinator: {e}", file=sys.stderr)
        return {
            'coordination_health': 0.0,
            'sync_status': 'error',
            'reality_simulator_status': 'unknown',
            'explorer_status': 'unknown',
            'djinn_kernel_status': 'unknown',
            'active_systems': 0,
            'all_systems_active': 0,
            'timestamp': time.time(),
            'error': str(e)
        }

if __name__ == "__main__":
    traits = main()
    print("Coordination traits:", json.dumps(traits, indent=2))
