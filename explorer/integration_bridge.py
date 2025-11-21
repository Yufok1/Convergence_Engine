"""
Explorer Integration Bridge
Connects Explorer to Reality Simulator and Djinn Kernel using built-in facilities
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
parent_path = Path(__file__).parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

try:
    from trait_hub import TraitHub
    TRAIT_HUB_AVAILABLE = True
except ImportError:
    TRAIT_HUB_AVAILABLE = False

try:
    from sentinel import Sentinel
    from kernel import Kernel
    from breath_engine import BreathEngine
    from mirror_systems import MirrorOfInsight, MirrorOfPortent, BloomSystem
    EXPLORER_COMPONENTS_AVAILABLE = True
except ImportError:
    EXPLORER_COMPONENTS_AVAILABLE = False


class ExplorerIntegrationBridge:
    """
    Integration bridge using Explorer's built-in facilities:
    - Trait Hub for trait translation
    - Sentinel for VP tracking
    - Kernel for sovereign ID management
    - Breath Engine for timing
    - Mirror Systems for analysis
    """
    
    def __init__(self):
        self.trait_hub = TraitHub() if TRAIT_HUB_AVAILABLE else None
        self.sentinel = Sentinel() if EXPLORER_COMPONENTS_AVAILABLE else None
        self.kernel = Kernel() if EXPLORER_COMPONENTS_AVAILABLE else None
        self.breath_engine = BreathEngine() if EXPLORER_COMPONENTS_AVAILABLE else None
        self.mirror_insight = MirrorOfInsight() if EXPLORER_COMPONENTS_AVAILABLE else None
        self.mirror_portent = MirrorOfPortent() if EXPLORER_COMPONENTS_AVAILABLE else None
        self.bloom_system = BloomSystem() if EXPLORER_COMPONENTS_AVAILABLE else None
        
        # Integration state
        self.integration_active = False
        self.last_sync_time = time.time()
        
    def collect_reality_simulator_traits(self) -> Dict[str, Any]:
        """Collect traits from Reality Simulator using test_func1"""
        try:
            # Import and run test_func1
            sys.path.insert(0, str(Path(__file__).parent))
            from test_func1 import main as collect_network_state
            traits = collect_network_state()
            
            # Translate using trait hub
            if self.trait_hub:
                translated = self.trait_hub.translate(traits)
                return {t['trait']: t['value'] for t in translated}
            
            return traits
        except Exception as e:
            print(f"[Integration Bridge] Error collecting Reality Simulator traits: {e}")
            return {}
    
    def collect_djinn_kernel_traits(self) -> Dict[str, Any]:
        """Collect traits from Djinn Kernel using test_func2"""
        try:
            # Import and run test_func2
            sys.path.insert(0, str(Path(__file__).parent))
            from test_func2 import main as calculate_vp
            traits = calculate_vp()
            
            # Translate using trait hub
            if self.trait_hub:
                translated = self.trait_hub.translate(traits)
                return {t['trait']: t['value'] for t in translated}
            
            return traits
        except Exception as e:
            print(f"[Integration Bridge] Error collecting Djinn Kernel traits: {e}")
            return {}
    
    def detect_phase_transition(self) -> Dict[str, Any]:
        """Detect phase transition using test_func3"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from test_func3 import main as detect_transition
            return detect_transition()
        except Exception as e:
            print(f"[Integration Bridge] Error detecting phase transition: {e}")
            return {'phase': 'chaos', 'transition_ready': 0}
    
    def track_exploration(self) -> Dict[str, Any]:
        """Track exploration using test_func4"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from test_func4 import main as track_exploration
            return track_exploration()
        except Exception as e:
            print(f"[Integration Bridge] Error tracking exploration: {e}")
            return {'total_exploration': 0.0}
    
    def coordinate_systems(self) -> Dict[str, Any]:
        """Coordinate all systems using test_func5"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from test_func5 import main as coordinate
            return coordinate()
        except Exception as e:
            print(f"[Integration Bridge] Error coordinating systems: {e}")
            return {'coordination_health': 0.0, 'sync_status': 'error'}
    
    def calculate_unified_vp(self, reality_sim_traits: Dict, djinn_kernel_traits: Dict) -> float:
        """Calculate unified VP across all systems"""
        if not self.sentinel:
            return 0.0
        
        # Combine traits from both systems
        combined_traits = {
            **reality_sim_traits,
            **djinn_kernel_traits
        }
        
        # Use Explorer's stability center and envelope
        stability_center = {
            'organism_count': 500.0,  # Target: collapse threshold
            'modularity': 0.3,         # Target: post-collapse
            'clustering_coefficient': 0.5,  # Target: post-collapse
            'average_path_length': 3.0,  # Target: post-collapse
            'violation_pressure': 0.0,   # Target: VP0
            'trait_convergence': 1.0    # Target: fully converged
        }
        
        stability_envelope = {
            'organism_count': (0, 1000),
            'modularity': (0.0, 1.0),
            'clustering_coefficient': (0.0, 1.0),
            'average_path_length': (0.0, 10.0),
            'violation_pressure': (0.0, 1.0),
            'trait_convergence': (0.0, 1.0)
        }
        
        # Calculate VP using Explorer's metrics
        from metrics import calculate_vp
        unified_vp = calculate_vp(combined_traits, stability_center, stability_envelope)
        
        return unified_vp
    
    def sync_all_systems(self) -> Dict[str, Any]:
        """Synchronize all three systems"""
        sync_result = {
            'timestamp': time.time(),
            'reality_simulator': {},
            'djinn_kernel': {},
            'explorer': {},
            'phase_transition': {},
            'exploration': {},
            'coordination': {},
            'unified_vp': 0.0
        }
        
        # Collect from all systems
        reality_sim_traits = self.collect_reality_simulator_traits()
        djinn_kernel_traits = self.collect_djinn_kernel_traits()
        
        sync_result['reality_simulator'] = reality_sim_traits
        sync_result['djinn_kernel'] = djinn_kernel_traits
        
        # Detect phase transition
        transition_data = self.detect_phase_transition()
        sync_result['phase_transition'] = transition_data
        
        # Track exploration
        exploration_data = self.track_exploration()
        sync_result['exploration'] = exploration_data
        
        # Coordinate systems
        coordination_data = self.coordinate_systems()
        sync_result['coordination'] = coordination_data
        
        # Calculate unified VP
        unified_vp = self.calculate_unified_vp(reality_sim_traits, djinn_kernel_traits)
        sync_result['unified_vp'] = unified_vp
        
        # Update Explorer state
        if self.sentinel:
            # Record unified VP in Sentinel's history
            self.sentinel.vp_history.append({
                'vp': unified_vp,
                'traits': {**reality_sim_traits, **djinn_kernel_traits},
                'timestamp': time.time(),
                'context': 'unified_integration'
            })
        
        # Mirror analysis
        if self.mirror_insight:
            system_state = {
                'phase': transition_data.get('phase', 'chaos'),
                'kernel_sovereign_ids': self.kernel.get_sovereign_ids() if self.kernel else [],
                'breath_state': self.breath_engine.get_breath_state() if self.breath_engine else {}
            }
            insights = self.mirror_insight.reflect(system_state)
            sync_result['explorer']['insights'] = insights
        
        self.last_sync_time = time.time()
        return sync_result
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            'trait_hub_available': TRAIT_HUB_AVAILABLE,
            'explorer_components_available': EXPLORER_COMPONENTS_AVAILABLE,
            'integration_active': self.integration_active,
            'last_sync_time': self.last_sync_time,
            'sentinel_vp_count': len(self.sentinel.vp_history) if self.sentinel else 0,
            'kernel_sovereign_ids': len(self.kernel.get_sovereign_ids()) if self.kernel else 0
        }


# Example usage
if __name__ == "__main__":
    bridge = ExplorerIntegrationBridge()
    print("Integration Status:", json.dumps(bridge.get_integration_status(), indent=2))
    print("\nSyncing all systems...")
    sync_result = bridge.sync_all_systems()
    print("\nSync Result:", json.dumps(sync_result, indent=2))

