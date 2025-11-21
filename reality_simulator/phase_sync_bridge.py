"""
🌉 PHASE SYNCHRONIZATION BRIDGE

CORE INSIGHT: Chaos → Precision is the UNIVERSAL TRANSITION

All three systems implement the SAME fundamental transition:
- Reality Simulator: Distributed chaos → Consolidated precision
- Explorer: Genesis chaos → Sovereign precision
- Djinn Kernel: Trait divergence → Trait convergence

It's not three separate systems—it's ONE TRANSITION viewed from three angles.

The recursive event at ~500 organisms with 5 connections per organism
corresponds to Explorer's mathematical capability threshold (50 VP calculations).
The ratio 500:50 = 10:1 is the exploration-to-precision conversion factor.

Key Insight:
- Pre-collapse (distributed) = Genesis Phase = Trait Divergence (CHAOS)
- Post-collapse (consolidated) = Sovereign Phase = Trait Convergence (PRECISION)
- All are phase transitions from chaos to precision
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# Add Explorer to path
explorer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'explorer')
if explorer_path not in sys.path:
    sys.path.insert(0, explorer_path)

try:
    from sentinel import Sentinel
    from kernel import Kernel
    from breath_engine import BreathEngine
    from mirror_systems import MirrorOfInsight, MirrorOfPortent, BloomSystem
    EXPLORER_AVAILABLE = True
except ImportError:
    EXPLORER_AVAILABLE = False
    print("[Phase Bridge] Explorer not available - running in standalone mode")


@dataclass
class NetworkPhaseMetrics:
    """Metrics that indicate phase state in Reality Simulator"""
    organism_count: int = 0
    connection_count: int = 0
    clustering_coefficient: float = 0.0
    modularity: float = 0.0
    average_path_length: float = 0.0
    connectivity: float = 0.0
    stability_index: float = 0.0
    is_collapsed: bool = False
    
    def calculate_collapse_proximity(self, collapse_threshold: int = 500) -> float:
        """
        Calculate how close we are to collapse (0.0 = far, 1.0 = at/after collapse)
        
        The collapse happens at ~500 organisms with 5 connections per organism.
        This creates a percolation threshold where the network becomes globally connected.
        """
        if self.organism_count >= collapse_threshold:
            return 1.0
        
        # Normalize by threshold
        proximity = self.organism_count / collapse_threshold
        
        # Adjust based on network topology
        # High clustering + low modularity = closer to collapse
        topology_factor = (self.clustering_coefficient * (1.0 - self.modularity))
        
        # Combined proximity
        return min(1.0, proximity + (topology_factor * 0.3))
    
    def detect_collapse(self, collapse_threshold: int = 500) -> bool:
        """
        Detect if network has collapsed (transitioned from distributed to consolidated)
        
        Collapse indicators:
        1. Organism count >= 500
        2. High clustering coefficient (> 0.5)
        3. Low modularity (< 0.3) - fewer communities, more unified
        4. Low average path length (< 3.0) - efficient, coordinated
        """
        if self.organism_count < collapse_threshold:
            return False
        
        # Check topology indicators
        has_high_clustering = self.clustering_coefficient > 0.5
        has_low_modularity = self.modularity < 0.3
        has_efficient_paths = self.average_path_length < 3.0
        
        # Collapse = all indicators present
        collapsed = has_high_clustering and has_low_modularity and has_efficient_paths
        
        if collapsed and not self.is_collapsed:
            # First detection of collapse
            self.is_collapsed = True
        
        return collapsed


@dataclass
class ExplorerPhaseMetrics:
    """Metrics that indicate phase state in Explorer"""
    sovereign_id_count: int = 0
    vp_calculations: int = 0
    stability_score: float = 0.0
    breath_cycles: int = 0
    bloom_curvature: float = 0.0
    learning_success_rate: float = 0.0
    phase: str = 'genesis'  # 'genesis' or 'sovereign'
    
    def calculate_genesis_proximity(self) -> float:
        """
        Calculate how close Explorer is to Sovereign transition (0.0 = early genesis, 1.0 = ready for transition)
        
        Based on Explorer's mathematical capability assessment:
        - VP calculations >= 50
        - Stability score > 0.5
        - Breath cycles >= 25
        - Bloom curvature > 0.2
        - Learning success rate > 0.6
        """
        vp_progress = min(1.0, self.vp_calculations / 50.0)
        stability_progress = min(1.0, self.stability_score / 0.5) if self.stability_score > 0 else 0.0
        breath_progress = min(1.0, self.breath_cycles / 25.0)
        bloom_progress = min(1.0, self.bloom_curvature / 0.2) if self.bloom_curvature > 0 else 0.0
        learning_progress = min(1.0, self.learning_success_rate / 0.6) if self.learning_success_rate > 0 else 0.0
        
        # Weighted average
        proximity = (
            vp_progress * 0.3 +
            stability_progress * 0.2 +
            breath_progress * 0.2 +
            bloom_progress * 0.15 +
            learning_progress * 0.15
        )
        
        return min(1.0, proximity)
    
    def is_ready_for_transition(self) -> bool:
        """Check if Explorer is ready for Genesis → Sovereign transition"""
        return (
            self.vp_calculations >= 50 and
            self.stability_score > 0.5 and
            self.breath_cycles >= 25 and
            self.bloom_curvature > 0.2 and
            self.learning_success_rate > 0.6
        )


class PhaseSynchronizationBridge:
    """
    Synchronizes the UNIVERSAL TRANSITION: Chaos → Precision
    
    All three systems implement the SAME fundamental transition:
    - Reality Simulator: Distributed chaos → Consolidated precision (500 organisms)
    - Explorer: Genesis chaos → Sovereign precision (50 VP calculations)
    - Djinn Kernel: Trait divergence → Trait convergence (VP < 0.25)
    
    The ratio 500:50 = 10:1 is the exploration-to-precision conversion factor.
    
    When ANY system hits its threshold, ALL systems transition to precision phase.
    """
    
    def __init__(self, collapse_threshold: int = 500, max_connections_per_organism: int = 5):
        self.collapse_threshold = collapse_threshold
        self.max_connections_per_organism = max_connections_per_organism
        
        # Network phase tracking
        self.network_metrics = NetworkPhaseMetrics()
        self.network_history = []
        
        # Explorer phase tracking
        self.explorer_metrics = ExplorerPhaseMetrics()
        self.explorer_available = EXPLORER_AVAILABLE
        
        if self.explorer_available:
            try:
                self.explorer_sentinel = Sentinel()
                self.explorer_kernel = Kernel()
                self.explorer_breath = BreathEngine()
                self.explorer_insight = MirrorOfInsight()
                self.explorer_bloom = BloomSystem()
            except Exception as e:
                print(f"[Phase Bridge] Failed to initialize Explorer: {e}")
                self.explorer_available = False
        
        # Synchronization state
        self.last_sync_time = time.time()
        self.sync_interval = 1.0  # Sync every second
        self.phase_aligned = False
        
        # Unified exploration tracking (Chaos → Precision)
        self.exploration_to_precision_ratio = 10.0  # 500:50 = 10:1
        self.reality_sim_explorations = 0  # Organisms explored
        self.explorer_explorations = 0     # VP calculations
        self.transition_triggered = False  # Has chaos→precision transition occurred?
        
    def update_network_metrics(self, network_data: Dict[str, Any]):
        """
        Update network metrics from Reality Simulator
        
        Expected network_data:
        - organism_count: int
        - connection_count: int
        - clustering_coefficient: float
        - modularity: float
        - average_path_length: float
        - connectivity: float
        - stability_index: float
        """
        self.network_metrics.organism_count = network_data.get('organism_count', 0)
        self.network_metrics.connection_count = network_data.get('connection_count', 0)
        self.network_metrics.clustering_coefficient = network_data.get('clustering_coefficient', 0.0)
        self.network_metrics.modularity = network_data.get('modularity', 0.0)
        self.network_metrics.average_path_length = network_data.get('average_path_length', 0.0)
        self.network_metrics.connectivity = network_data.get('connectivity', 0.0)
        self.network_metrics.stability_index = network_data.get('stability_index', 0.0)
        
        # Update unified exploration counter
        self.reality_sim_explorations = self.network_metrics.organism_count
        
        # Detect collapse (chaos→precision transition)
        collapsed = self.network_metrics.detect_collapse(self.collapse_threshold)
        
        # Check unified transition (when ANY system hits threshold, ALL transition)
        if collapsed and not self.transition_triggered:
            self.transition_triggered = True
            print("[Phase Bridge] 🌉 CHAOS→PRECISION TRANSITION DETECTED")
            print(f"[Phase Bridge] Reality Sim: {self.reality_sim_explorations} organisms explored")
            print(f"[Phase Bridge] Explorer: {self.explorer_explorations} VP calculations")
            print(f"[Phase Bridge] Conversion factor: {self.exploration_to_precision_ratio}:1")
        
        # Store history
        self.network_history.append({
            'timestamp': time.time(),
            'metrics': self.network_metrics,
            'collapsed': collapsed,
            'explorations': {
                'reality_sim': self.reality_sim_explorations,
                'explorer': self.explorer_explorations
            }
        })
        
        # Keep only last 100 entries
        if len(self.network_history) > 100:
            self.network_history = self.network_history[-100:]
        
        return collapsed
    
    def update_explorer_metrics(self):
        """Update Explorer metrics from Explorer system"""
        if not self.explorer_available:
            return
        
        try:
            # Get sovereign IDs from kernel
            sovereign_ids = self.explorer_kernel.get_sovereign_ids()
            self.explorer_metrics.sovereign_id_count = len(sovereign_ids)
            
            # Get VP calculations from sentinel
            if hasattr(self.explorer_sentinel, 'vp_history'):
                self.explorer_metrics.vp_calculations = len(self.explorer_sentinel.vp_history)
                # Update unified exploration counter
                self.explorer_explorations = self.explorer_metrics.vp_calculations
            
            # Get stability from mirror
            if self.explorer_insight:
                self.explorer_metrics.stability_score = self.explorer_insight.get_stability_score()
            
            # Get breath cycles
            if self.explorer_breath:
                self.explorer_metrics.breath_cycles = self.explorer_breath.breath_cycle_count
            
            # Get bloom curvature
            if self.explorer_bloom:
                self.explorer_metrics.bloom_curvature = self.explorer_bloom.bloom_curvature
            
            # Get learning success rate (would need dynamic_operations)
            # For now, estimate from VP history
            if hasattr(self.explorer_sentinel, 'vp_history') and len(self.explorer_sentinel.vp_history) > 0:
                recent_vps = [entry['vp'] for entry in self.explorer_sentinel.vp_history[-10:]]
                low_vp_count = sum(1 for vp in recent_vps if vp < 1.0)
                self.explorer_metrics.learning_success_rate = low_vp_count / len(recent_vps)
        except Exception as e:
            print(f"[Phase Bridge] Error updating Explorer metrics: {e}")
    
    def synchronize_phases(self) -> Dict[str, Any]:
        """
        Synchronize phases between Reality Simulator and Explorer
        
        Returns synchronization state and recommendations
        """
        current_time = time.time()
        
        # Only sync at intervals
        if current_time - self.last_sync_time < self.sync_interval:
            return self._get_sync_state()
        
        self.last_sync_time = current_time
        
        # Update Explorer metrics
        self.update_explorer_metrics()
        
        # Calculate proximities
        network_proximity = self.network_metrics.calculate_collapse_proximity(self.collapse_threshold)
        explorer_proximity = self.explorer_metrics.calculate_genesis_proximity()
        
        # Check if phases are aligned
        network_collapsed = self.network_metrics.is_collapsed
        explorer_ready = self.explorer_metrics.is_ready_for_transition()
        
        # Phase alignment
        if network_collapsed and explorer_ready:
            self.phase_aligned = True
        elif not network_collapsed and not explorer_ready:
            self.phase_aligned = True  # Both in pre-transition
        else:
            self.phase_aligned = False
        
        return self._get_sync_state()
    
    def _get_sync_state(self) -> Dict[str, Any]:
        """Get current synchronization state"""
        return {
            'network': {
                'organism_count': self.network_metrics.organism_count,
                'collapse_proximity': self.network_metrics.calculate_collapse_proximity(self.collapse_threshold),
                'is_collapsed': self.network_metrics.is_collapsed,
                'clustering': self.network_metrics.clustering_coefficient,
                'modularity': self.network_metrics.modularity,
                'path_length': self.network_metrics.average_path_length
            },
            'explorer': {
                'sovereign_ids': self.explorer_metrics.sovereign_id_count,
                'genesis_proximity': self.explorer_metrics.calculate_genesis_proximity(),
                'is_ready': self.explorer_metrics.is_ready_for_transition(),
                'phase': self.explorer_metrics.phase,
                'vp_calculations': self.explorer_metrics.vp_calculations,
                'stability_score': self.explorer_metrics.stability_score,
                'breath_cycles': self.explorer_metrics.breath_cycles
            },
            'synchronization': {
                'aligned': self.phase_aligned,
                'network_proximity': self.network_metrics.calculate_collapse_proximity(self.collapse_threshold),
                'explorer_proximity': self.explorer_metrics.calculate_genesis_proximity(),
                'proximity_difference': abs(
                    self.network_metrics.calculate_collapse_proximity(self.collapse_threshold) -
                    self.explorer_metrics.calculate_genesis_proximity()
                )
            }
        }
    
    def trigger_explorer_transition(self):
        """
        Trigger Explorer's Genesis → Sovereign transition when Reality Simulator collapses
        
        This maps the recursive network collapse event to Explorer's mathematical capability threshold.
        """
        if not self.explorer_available:
            return False
        
        if self.network_metrics.is_collapsed and self.explorer_metrics.phase == 'genesis':
            print("[Phase Bridge] 🌉 NETWORK COLLAPSE DETECTED - Triggering Explorer transition...")
            print(f"[Phase Bridge] Organisms: {self.network_metrics.organism_count}, "
                  f"Clustering: {self.network_metrics.clustering_coefficient:.3f}, "
                  f"Modularity: {self.network_metrics.modularity:.3f}")
            
            # The collapse event IS the mathematical capability threshold
            # Force Explorer to recognize this as transition-ready
            # (In practice, Explorer would check this itself, but we're synchronizing)
            
            self.explorer_metrics.phase = 'sovereign'
            return True
        
        return False
    
    def get_collapse_prediction(self) -> Tuple[bool, float]:
        """
        Predict when network collapse will occur based on current metrics
        
        Returns: (will_collapse: bool, estimated_generations: float)
        """
        if self.network_metrics.is_collapsed:
            return (True, 0.0)
        
        proximity = self.network_metrics.calculate_collapse_proximity(self.collapse_threshold)
        
        if proximity < 0.1:
            return (False, float('inf'))
        
        # Estimate based on current growth rate
        if len(self.network_history) >= 2:
            recent = self.network_history[-1]
            older = self.network_history[-min(10, len(self.network_history))]
            
            growth_rate = (recent['metrics'].organism_count - older['metrics'].organism_count) / \
                         max(1, len(self.network_history) - min(10, len(self.network_history)))
            
            if growth_rate > 0:
                remaining = self.collapse_threshold - self.network_metrics.organism_count
                estimated_generations = remaining / growth_rate
                return (True, estimated_generations)
        
        return (False, float('inf'))


# Example usage
if __name__ == "__main__":
    bridge = PhaseSynchronizationBridge(collapse_threshold=500, max_connections_per_organism=5)
    
    # Simulate network growth
    for gen in range(600):
        network_data = {
            'organism_count': gen,
            'connection_count': gen * 2,  # Rough estimate
            'clustering_coefficient': min(0.8, gen / 1000.0),
            'modularity': max(0.1, 1.0 - (gen / 800.0)),
            'average_path_length': max(1.0, 10.0 - (gen / 100.0)),
            'connectivity': min(5.0, gen / 100.0),
            'stability_index': min(1.0, gen / 500.0)
        }
        
        collapsed = bridge.update_network_metrics(network_data)
        sync_state = bridge.synchronize_phases()
        
        if gen % 50 == 0 or collapsed:
            print(f"\n[Generation {gen}]")
            print(f"  Network: {sync_state['network']}")
            print(f"  Explorer: {sync_state['explorer']}")
            print(f"  Synchronized: {sync_state['synchronization']['aligned']}")
            
            if collapsed:
                bridge.trigger_explorer_transition()
                break

