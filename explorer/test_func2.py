"""
Djinn Kernel VP Calculator
Explorer integration module: Calculates VP from Djinn Kernel traits
"""

import sys
import os
import json
from pathlib import Path

def main():
    """
    Calculate VP from Djinn Kernel traits.
    
    This function is called by Explorer's Sentinel to get VP from Djinn Kernel.
    Returns traits in Explorer format for VP calculation.
    """
    # Add kernel to path
    kernel_path = Path(__file__).parent.parent / 'kernel'
    if str(kernel_path) not in sys.path:
        sys.path.insert(0, str(kernel_path))
    
    try:
        # Try to import Djinn Kernel components
        from violation_pressure_calculation import ViolationMonitor
        from event_driven_coordination import DjinnEventBus
        
        # Initialize VP monitor (if not already initialized)
        # In practice, this would connect to running Djinn Kernel instance
        vp_monitor = ViolationMonitor()
        
        # Get system health metrics
        health_metrics = vp_monitor.calculate_system_health_metrics()
        
        # Get recent VP history
        if vp_monitor.vp_history:
            recent_vp = vp_monitor.vp_history[-1]
            total_vp = recent_vp.get('total_vp', 0.0)
            classification = recent_vp.get('classification', 'VP0')
        else:
            total_vp = 0.0
            classification = 'VP0'
        
        # Return traits in Explorer format
        traits = {
            'violation_pressure': total_vp,
            'total_vp': total_vp,
            'vp_classification': classification,
            'system_health': health_metrics.get('average_vp', 0.0),
            'vp_calculations': len(vp_monitor.vp_history),
            'trait_convergence': 1.0 - total_vp if total_vp < 1.0 else 0.0,  # Inverse of VP
            'convergence_success': 1.0 if total_vp < 0.25 else 0.0,  # VP0 = successful
            'trait_divergence': total_vp,  # Same as VP
            'stability_envelope_deviation': total_vp,  # VP measures deviation
            'completion_pressure': total_vp,  # VP is completion pressure
            'uuid_anchored': 1 if len(vp_monitor.vp_history) > 0 else 0,
            'identity_completion': 1.0 - total_vp if total_vp < 1.0 else 0.0
        }
        
        # Output traits (Explorer will capture this)
        print(json.dumps(traits))
        return traits
        
    except ImportError:
        # Djinn Kernel not available - return default traits
        return {
            'violation_pressure': 0.0,
            'total_vp': 0.0,
            'vp_classification': 'VP0',
            'system_health': 1.0,
            'vp_calculations': 0,
            'trait_convergence': 1.0,
            'convergence_success': 1.0,
            'trait_divergence': 0.0,
            'stability_envelope_deviation': 0.0,
            'completion_pressure': 0.0,
            'uuid_anchored': 0,
            'identity_completion': 1.0
        }
    except Exception as e:
        # Return error traits
        print(f"[ERROR] Djinn Kernel calculator: {e}", file=sys.stderr)
        return {
            'violation_pressure': 1.0,  # High VP = error
            'total_vp': 1.0,
            'vp_classification': 'VP4',
            'system_health': 0.0,
            'vp_calculations': 0,
            'trait_convergence': 0.0,
            'convergence_success': 0.0,
            'trait_divergence': 1.0,
            'stability_envelope_deviation': 1.0,
            'completion_pressure': 1.0,
            'uuid_anchored': 0,
            'identity_completion': 0.0,
            'error': str(e)
        }

if __name__ == "__main__":
    traits = main()
    print("Calculated traits:", json.dumps(traits, indent=2))
