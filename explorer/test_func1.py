"""
Reality Simulator Network State Collector
Explorer integration module: Collects network metrics from Reality Simulator
"""

import sys
import os
import json
from pathlib import Path

def main():
    """
    Collect network state from Reality Simulator and return as traits.
    
    This function is called by Explorer's Sentinel to collect network metrics.
    Returns traits in Explorer format for VP calculation.
    """
    # Add Reality Simulator to path
    reality_sim_path = Path(__file__).parent.parent / 'reality_simulator'
    if str(reality_sim_path) not in sys.path:
        sys.path.insert(0, str(reality_sim_path))
    
    try:
        # Try to read from shared state (if Reality Simulator is running)
        shared_state_path = Path(__file__).parent.parent / 'data' / 'shared_state.json'
        
        if shared_state_path.exists():
            with open(shared_state_path, 'r') as f:
                shared_state = json.load(f)
            
            # Extract network metrics
            network_data = shared_state.get('network', {})
            
            if network_data:
                # Return traits in Explorer format
                traits = {
                    'organism_count': network_data.get('organisms', 0),
                    'connection_count': network_data.get('connections', 0),
                    'clustering_coefficient': network_data.get('clustering_coefficient', 0.0),
                    'modularity': network_data.get('modularity', 0.0),
                    'average_path_length': network_data.get('average_path_length', 0.0),
                    'connectivity': network_data.get('connectivity', 0.0),
                    'stability_index': network_data.get('stability', 0.0),
                    'generation': network_data.get('generation', 0)
                }
                
                # Calculate derived metrics
                org_count = traits['organism_count']
                conn_count = traits['connection_count']
                
                if org_count > 0:
                    traits['average_degree'] = (2 * conn_count) / org_count
                    max_possible = (org_count * (org_count - 1)) / 2 if org_count > 1 else 0
                    traits['network_density'] = conn_count / max_possible if max_possible > 0 else 0.0
                else:
                    traits['average_degree'] = 0.0
                    traits['network_density'] = 0.0
                
                # Calculate collapse proximity
                collapse_threshold = 500
                if org_count >= collapse_threshold:
                    traits['collapse_proximity'] = 1.0
                    traits['is_collapsed'] = 1  # Collapsed
                else:
                    traits['collapse_proximity'] = org_count / collapse_threshold
                    traits['is_collapsed'] = 0  # Not collapsed
                
                # Output traits (Explorer will capture this)
                print(json.dumps(traits))
                return traits
        
        # If no shared state, return empty traits
        return {
            'organism_count': 0,
            'connection_count': 0,
            'clustering_coefficient': 0.0,
            'modularity': 0.0,
            'average_path_length': 0.0,
            'connectivity': 0.0,
            'stability_index': 0.0,
            'generation': 0,
            'average_degree': 0.0,
            'network_density': 0.0,
            'collapse_proximity': 0.0,
            'is_collapsed': 0
        }
        
    except Exception as e:
        # Return error traits
        print(f"[ERROR] Reality Simulator collector: {e}", file=sys.stderr)
        return {
            'organism_count': 0,
            'connection_count': 0,
            'clustering_coefficient': 0.0,
            'modularity': 0.0,
            'average_path_length': 0.0,
            'connectivity': 0.0,
            'stability_index': 0.0,
            'generation': 0,
            'average_degree': 0.0,
            'network_density': 0.0,
            'collapse_proximity': 0.0,
            'is_collapsed': 0,
            'error': str(e)
        }

if __name__ == "__main__":
    traits = main()
    print("Collected traits:", json.dumps(traits, indent=2))
