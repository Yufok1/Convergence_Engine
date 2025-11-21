"""
Convergence Factor Test Script

Tests different organism/connection configurations to determine what actually drives collapse.
Tracks all collapse indicators separately to identify the bottleneck.

Hypothesis: Is collapse driven by:
- Organism count (always at N organisms)?
- Average degree (always at X connections per organism)?
- Network density (always at Y% of possible connections)?
- Topology formation (depends on structure)?
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging_config not available
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
    logger = logging.getLogger(__name__)

from reality_simulator.main import RealitySimulator
from reality_simulator.symbiotic_network import SymbioticNetwork


@dataclass
class CollapseMetrics:
    """Metrics at the moment of collapse detection"""
    generation: int
    organism_count: int
    connection_count: int
    clustering_coefficient: float
    modularity: float
    average_path_length: float
    connectivity: float
    stability_index: float
    
    # Calculated metrics
    average_degree: float  # Average connections per organism
    network_density: float  # Actual connections / possible connections
    max_possible_connections: int  # N*(N-1)/2 for N organisms
    
    # When each condition was met
    gen_organism_threshold: Optional[int] = None  # When organism_count >= threshold
    gen_clustering_threshold: Optional[int] = None  # When clustering > 0.5
    gen_modularity_threshold: Optional[int] = None  # When modularity < 0.3
    gen_path_length_threshold: Optional[int] = None  # When path_length < 3.0
    gen_all_conditions_met: Optional[int] = None  # When collapse actually detected
    
    # Configuration
    max_connections_per_organism: int = 5
    collapse_threshold: int = 500


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment"""
    name: str
    max_organisms: int  # Config limit
    max_connections_per_organism: int
    collapse_threshold: int  # What we're testing against
    max_generations: int = 2000  # Safety limit
    expected_collapse: Optional[bool] = None


class ConvergenceFactorTester:
    """Test convergence factors across different configurations"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        
    def run_experiment(self, config: ExperimentConfig) -> Optional[CollapseMetrics]:
        """Run a single experiment configuration"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: {config.name}")
        print(f"  Max organisms: {config.max_organisms}")
        print(f"  Max connections per organism: {config.max_connections_per_organism}")
        print(f"  Collapse threshold: {config.collapse_threshold}")
        print(f"{'='*60}\n")
        
        # Create simulator with custom config
        custom_config = self._create_custom_config(config)
        
        # Debug: Verify config
        logger.debug(f"Config rendering.enable_visualizations = {custom_config.get('rendering', {}).get('enable_visualizations', 'NOT SET')}")
        
        try:
            # Create simulator with custom config BEFORE initialization
            simulator = RealitySimulator(config_path=None)
            simulator.config = custom_config
            
            # Ensure headless mode is set (double-check)
            if 'rendering' not in simulator.config:
                simulator.config['rendering'] = {}
            simulator.config['rendering']['enable_visualizations'] = False
            simulator.config['rendering']['text_interface'] = False
            
            # Debug: Verify after override
            logger.debug(f"After override: rendering.enable_visualizations = {simulator.config.get('rendering', {}).get('enable_visualizations', 'NOT SET')}")
            
            # Initialize simulation
            if not simulator.initialize_simulation():
                print(f"[ERROR] Failed to initialize simulation for {config.name}")
                return None
            
            # Override network settings AFTER initialization
            network = simulator.components.get('network')
            if network:
                # CRITICAL: Override the initialization's aggressive settings
                # main.py sets max_connections_per_organism to at least 12, we need to reset it
                network.max_connections_per_organism = config.max_connections_per_organism
                
                # Ensure new_edge_rate allows proper connection formation
                # Use 2.0 like normal runs to ensure connections form at expected rate
                if hasattr(network, 'set_new_edge_rate'):
                    network.set_new_edge_rate(2.0)  # Match normal run behavior
                elif hasattr(network, 'new_edge_rate'):
                    network.new_edge_rate = 2.0
                
                # IMPORTANT: Set max_organisms HIGH so network can grow to 500+
                # Don't cap it at 600 - let it grow naturally to see collapse
                simulator.config['network']['max_organisms'] = max(config.max_organisms, 1000)  # At least 1000 to allow growth
                
                # Debug: Verify network settings
                logger.debug("Network settings after override:")
                logger.debug(f"  max_connections_per_organism: {network.max_connections_per_organism}")
                logger.debug(f"  new_edge_rate: {getattr(network, 'new_edge_rate', 'NOT SET')}")
                logger.debug(f"  max_organisms (config): {simulator.config['network']['max_organisms']}")
                logger.debug(f"  current organisms: {len(network.organisms)}")
                logger.debug(f"  current connections: {len(network.connections)}")
                
                # Verify connection formation is working
                initial_conns = len(network.connections)
                logger.debug(f"Initial connection count: {initial_conns}")
                
                # Check if feedback controller might interfere
                if simulator.feedback_controller and simulator.feedback_controller.enabled:
                    logger.debug("Feedback controller is ENABLED - may adjust new_edge_rate dynamically")
                else:
                    logger.debug(f"Feedback controller is DISABLED - connection rate fixed at {getattr(network, 'new_edge_rate', 'NOT SET')}")
            
            # Track metrics over time
            collapse_metrics = self._track_collapse(simulator, config)
            
            return collapse_metrics
            
        except Exception as e:
            print(f"[ERROR] Experiment {config.name} failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_custom_config(self, config: ExperimentConfig) -> Dict[str, Any]:
        """Create custom config for experiment"""
        # Load base config
        base_config_path = Path(__file__).parent / "config.json"
        if base_config_path.exists():
            with open(base_config_path, 'r') as f:
                base_config = json.load(f)
        else:
            # Default config
            base_config = {
                "simulation": {"max_runtime": 3600.0, "target_fps": 8.0},
                "quantum": {"initial_states": 40},
                "lattice": {"particles": 2400},
                "evolution": {"population_size": 400, "max_generations": config.max_generations},
                "network": {
                    "max_connections": config.max_connections_per_organism,
                    "max_organisms": max(config.max_organisms, 1000),  # Allow growth to 500+
                    "resource_pool": 100.0
                },
                "agency": {"initial_mode": "manual_only"},
                "rendering": {
                    "mode": "observer", 
                    "text_interface": False,
                    "enable_visualizations": False  # Fully headless - no GUI windows
                }
            }
        
        # Override network settings
        # IMPORTANT: Set max_organisms HIGH to allow natural growth to 500+
        base_config['network']['max_organisms'] = max(config.max_organisms, 1000)  # At least 1000
        base_config['network']['max_connections'] = config.max_connections_per_organism
        base_config['evolution']['max_generations'] = config.max_generations
        
        # Ensure headless mode (no visualizations)
        if 'rendering' not in base_config:
            base_config['rendering'] = {}
        base_config['rendering']['enable_visualizations'] = False
        base_config['rendering']['text_interface'] = False
        
        # Enable feedback controller like normal runs (but it won't interfere if disabled)
        if 'feedback' not in base_config:
            base_config['feedback'] = {}
        # Keep feedback enabled if it was in base config, otherwise disable
        # (Normal runs have it enabled, but we can test with it disabled too)
        
        return base_config
    
    def _track_collapse(self, simulator: RealitySimulator, config: ExperimentConfig) -> Optional[CollapseMetrics]:
        """Track network metrics until collapse or max generations"""
        
        network = simulator.components.get('network')
        if not network:
            print("[ERROR] Network component not found")
            return None
        
        # Track when each condition is met
        organism_threshold_met = False
        clustering_threshold_met = False
        modularity_threshold_met = False
        path_length_threshold_met = False
        all_conditions_met = False
        
        gen_organism = None
        gen_clustering = None
        gen_modularity = None
        gen_path_length = None
        gen_collapse = None
        
        print("Tracking metrics... (this may take a while)")
        print("Generation | Organisms | Connections | Clustering | Modularity | Path Len | Collapsed | Time/gen")
        print("-" * 95)
        
        # Timing diagnostics
        start_time = time.time()
        last_print_time = start_time
        
        # Run simulation and track metrics
        for generation in range(config.max_generations):
            gen_start = time.time()
            
            # Update simulation (same as normal run)
            simulator._update_simulation_components()
            
            # Apply feedback controller if enabled (like normal run)
            if simulator.feedback_controller and simulator.feedback_controller.enabled:
                metrics = simulator.feedback_controller.collect_feedback_metrics(simulator)
                knob_changes = simulator.feedback_controller.update(generation, metrics)
                simulator._apply_feedback_changes(knob_changes)
            
            gen_elapsed = time.time() - gen_start
            
            # Get current metrics
            organism_count = len(network.organisms)
            
            # Count connections - use both methods to verify
            connection_count_dict = len(network.connections)
            connection_count_graph = len(network.network_graph.edges()) if hasattr(network, 'network_graph') else 0
            
            # Use graph edges as source of truth (matches what collapse detection uses)
            connection_count = connection_count_graph
            
            # Debug: Check if dict and graph are out of sync
            if abs(connection_count_dict - connection_count_graph) > 5:
                print(f"[WARNING] Gen {generation}: Connection count mismatch!")
                print(f"  Dict count: {connection_count_dict}, Graph count: {connection_count_graph}")
            
            # Debug: Check connection growth rate (should be ~2x organism count)
            if generation > 0 and generation % 50 == 0:
                expected_connections = organism_count * 2
                ratio = connection_count / organism_count if organism_count > 0 else 0
                if ratio < 1.5:
                    print(f"[WARNING] Gen {generation}: Connection ratio is {ratio:.2f} (expected ~2.0)")
                    print(f"  Organisms: {organism_count}, Connections: {connection_count}, Expected: ~{expected_connections}")
                    print(f"  max_connections_per_organism: {network.max_connections_per_organism}")
                    print(f"  new_edge_rate: {getattr(network, 'new_edge_rate', 'NOT SET')}")
                    print(f"  Graph edges: {connection_count_graph}, Dict entries: {connection_count_dict}")
            
            # Update network metrics
            if hasattr(network, 'network_graph') and len(network.network_graph) > 0:
                network.metrics.update_from_network(network.network_graph, network.organisms)
            
            clustering = network.metrics.clustering_coefficient
            modularity = network.metrics.modularity
            path_length = network.metrics.average_path_length
            connectivity = network.metrics.connectivity
            stability = network.metrics.stability_index
            
            # Calculate derived metrics
            avg_degree = (2 * connection_count / organism_count) if organism_count > 0 else 0.0
            max_possible = (organism_count * (organism_count - 1)) / 2 if organism_count > 1 else 0
            density = connection_count / max_possible if max_possible > 0 else 0.0
            
            # Check when each condition is met
            if not organism_threshold_met and organism_count >= config.collapse_threshold:
                organism_threshold_met = True
                gen_organism = generation
            
            if not clustering_threshold_met and clustering > 0.5:
                clustering_threshold_met = True
                gen_clustering = generation
            
            if not modularity_threshold_met and modularity < 0.3:
                modularity_threshold_met = True
                gen_modularity = generation
            
            if not path_length_threshold_met and path_length < 3.0 and path_length > 0:
                path_length_threshold_met = True
                gen_path_length = generation
            
            # Check if all conditions met (collapse detected)
            if (not all_conditions_met and 
                organism_count >= config.collapse_threshold and
                clustering > 0.5 and
                modularity < 0.3 and
                path_length < 3.0 and path_length > 0):
                all_conditions_met = True
                gen_collapse = generation
                
                # Create collapse metrics
                collapse_metrics = CollapseMetrics(
                    generation=generation,
                    organism_count=organism_count,
                    connection_count=connection_count,
                    clustering_coefficient=clustering,
                    modularity=modularity,
                    average_path_length=path_length,
                    connectivity=connectivity,
                    stability_index=stability,
                    average_degree=avg_degree,
                    network_density=density,
                    max_possible_connections=int(max_possible),
                    gen_organism_threshold=gen_organism,
                    gen_clustering_threshold=gen_clustering,
                    gen_modularity_threshold=gen_modularity,
                    gen_path_length_threshold=gen_path_length,
                    gen_all_conditions_met=gen_collapse,
                    max_connections_per_organism=config.max_connections_per_organism,
                    collapse_threshold=config.collapse_threshold
                )
                
                print(f"{generation:>10} | {organism_count:>9} | {connection_count:>11} | "
                      f"{clustering:>10.3f} | {modularity:>9.3f} | {path_length:>8.2f} | YES")
                print(f"\n[COLLAPSE DETECTED] Generation {generation}")
                return collapse_metrics
            
            # Progress update every 50 generations, or every 10 when approaching threshold
            should_print = (generation % 50 == 0 or generation < 10 or 
                          (organism_count >= config.collapse_threshold - 50 and generation % 10 == 0))
            if should_print:
                collapsed_marker = "YES" if all_conditions_met else "NO"
                # Show which conditions are met
                conditions = []
                if organism_count >= config.collapse_threshold:
                    conditions.append("ORG✓")
                if clustering > 0.5:
                    conditions.append("CLUST✓")
                if modularity < 0.3:
                    conditions.append("MOD✓")
                if path_length < 3.0 and path_length > 0:
                    conditions.append("PATH✓")
                condition_str = " ".join(conditions) if conditions else "---"
                time_per_gen = gen_elapsed * 1000  # Convert to ms
                print(f"{generation:>10} | {organism_count:>9} | {connection_count:>11} | "
                      f"{clustering:>10.3f} | {modularity:>9.3f} | {path_length:>8.2f} | {collapsed_marker:>8} | {time_per_gen:>6.1f}ms | {condition_str}")
                
                # Warn if going suspiciously fast (might indicate simulation not running properly)
                if time_per_gen < 1.0 and generation > 10:
                    print(f"[WARNING] Generation {generation} completed in {time_per_gen:.2f}ms - very fast! Network may not be evolving properly.")
                    print(f"  Organisms: {organism_count}, Connections: {connection_count}")
                    print(f"  Check if network.update_network() is being called correctly.")
            
            # Note: Continue running even after max_organisms - collapse might happen later
            # Only stop if we hit max_generations or detect collapse
        
        # If we didn't detect collapse, return None
        total_time = time.time() - start_time
        avg_time_per_gen = (total_time / config.max_generations) * 1000 if config.max_generations > 0 else 0
        
        if not all_conditions_met:
            print(f"\n[NO COLLAPSE] Reached max generations ({config.max_generations}) without collapse")
            print(f"[TIMING] Total time: {total_time:.2f}s ({total_time/60:.1f} min)")
            print(f"[TIMING] Average: {avg_time_per_gen:.2f}ms per generation")
            print(f"[TIMING] Final state: {organism_count} organisms, {connection_count} connections")
            
            # Diagnostic: Check if network is actually evolving
            if organism_count < 10:
                print(f"[WARNING] Very few organisms ({organism_count}) - network may not be growing properly!")
            if connection_count < organism_count:
                print(f"[WARNING] Very few connections ({connection_count} for {organism_count} organisms) - network may not be forming connections!")
            
            return None
        
        return None
    
    def run_all_experiments(self) -> List[Dict[str, Any]]:
        """Run all experiment configurations"""
        
        experiments = [
            # Current baseline
            ExperimentConfig(
                name="Baseline: 500 @ 5",
                max_organisms=600,
                max_connections_per_organism=5,
                collapse_threshold=500,
                expected_collapse=True
            ),
            
            # Linear scaling attempt
            ExperimentConfig(
                name="Linear: 300 @ 3",
                max_organisms=400,
                max_connections_per_organism=3,
                collapse_threshold=300,
                expected_collapse=None
            ),
            
            # Same total connection capacity (2500 total)
            ExperimentConfig(
                name="Same Capacity: 250 @ 10",
                max_organisms=300,
                max_connections_per_organism=10,
                collapse_threshold=250,
                expected_collapse=None
            ),
            
            # Same average degree, different size
            ExperimentConfig(
                name="Same Degree: 1000 @ 5",
                max_organisms=1200,
                max_connections_per_organism=5,
                collapse_threshold=1000,
                expected_collapse=None
            ),
            
            # Lower degree, same size
            ExperimentConfig(
                name="Lower Degree: 500 @ 3",
                max_organisms=600,
                max_connections_per_organism=3,
                collapse_threshold=500,
                expected_collapse=None
            ),
            
            # Higher degree, smaller size
            ExperimentConfig(
                name="Higher Degree: 200 @ 10",
                max_organisms=250,
                max_connections_per_organism=10,
                collapse_threshold=200,
                expected_collapse=None
            ),
            
            # Extreme: Very high degree
            ExperimentConfig(
                name="Extreme: 100 @ 20",
                max_organisms=150,
                max_connections_per_organism=20,
                collapse_threshold=100,
                expected_collapse=None
            ),
        ]
        
        print("="*80)
        print("CONVERGENCE FACTOR EXPERIMENTS")
        print("="*80)
        print(f"Running {len(experiments)} experiments...")
        print("Goal: Determine what actually drives collapse")
        print()
        
        results = []
        for exp_config in experiments:
            collapse_metrics = self.run_experiment(exp_config)
            
            result = {
                "config": asdict(exp_config),
                "collapse_metrics": asdict(collapse_metrics) if collapse_metrics else None,
                "collapsed": collapse_metrics is not None
            }
            results.append(result)
            
            # Brief pause between experiments
            time.sleep(1)
        
        self.results = results
        return results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze results to determine convergence factors"""
        
        if not self.results:
            return {}
        
        collapsed_experiments = [r for r in self.results if r['collapsed']]
        
        if not collapsed_experiments:
            return {"error": "No experiments resulted in collapse"}
        
        # Extract metrics at collapse
        organism_counts = [r['collapse_metrics']['organism_count'] for r in collapsed_experiments]
        avg_degrees = [r['collapse_metrics']['average_degree'] for r in collapsed_experiments]
        densities = [r['collapse_metrics']['network_density'] for r in collapsed_experiments]
        connection_counts = [r['collapse_metrics']['connection_count'] for r in collapsed_experiments]
        
        # Calculate statistics
        analysis = {
            "total_experiments": len(self.results),
            "collapsed_experiments": len(collapsed_experiments),
            "collapse_rate": len(collapsed_experiments) / len(self.results),
            
            "organism_count_at_collapse": {
                "mean": float(np.mean(organism_counts)),
                "std": float(np.std(organism_counts)),
                "min": int(min(organism_counts)),
                "max": int(max(organism_counts)),
                "range": int(max(organism_counts) - min(organism_counts))
            },
            
            "average_degree_at_collapse": {
                "mean": float(np.mean(avg_degrees)),
                "std": float(np.std(avg_degrees)),
                "min": float(min(avg_degrees)),
                "max": float(max(avg_degrees)),
                "range": float(max(avg_degrees) - min(avg_degrees))
            },
            
            "network_density_at_collapse": {
                "mean": float(np.mean(densities)),
                "std": float(np.std(densities)),
                "min": float(min(densities)),
                "max": float(max(densities)),
                "range": float(max(densities) - min(densities))
            },
            
            "connection_count_at_collapse": {
                "mean": float(np.mean(connection_counts)),
                "std": float(np.std(connection_counts)),
                "min": int(min(connection_counts)),
                "max": int(max(connection_counts)),
                "range": int(max(connection_counts) - min(connection_counts))
            },
            
            "bottleneck_analysis": self._analyze_bottlenecks(collapsed_experiments)
        }
        
        return analysis
    
    def _analyze_bottlenecks(self, collapsed_experiments: List[Dict]) -> Dict[str, Any]:
        """Analyze which condition is the bottleneck"""
        
        bottlenecks = {
            "organism_threshold_first": 0,
            "clustering_first": 0,
            "modularity_first": 0,
            "path_length_first": 0,
            "all_simultaneous": 0
        }
        
        for exp in collapsed_experiments:
            metrics = exp['collapse_metrics']
            gen_org = metrics.get('gen_organism_threshold')
            gen_clust = metrics.get('gen_clustering_threshold')
            gen_mod = metrics.get('gen_modularity_threshold')
            gen_path = metrics.get('gen_path_length_threshold')
            
            # Find which condition was met last (bottleneck)
            gens = [g for g in [gen_org, gen_clust, gen_mod, gen_path] if g is not None]
            if not gens:
                continue
            
            last_gen = max(gens)
            
            if gen_org == last_gen:
                bottlenecks["organism_threshold_first"] += 1
            elif gen_clust == last_gen:
                bottlenecks["clustering_first"] += 1
            elif gen_mod == last_gen:
                bottlenecks["modularity_first"] += 1
            elif gen_path == last_gen:
                bottlenecks["path_length_first"] += 1
            
            # Check if all conditions met simultaneously
            if gen_org == gen_clust == gen_mod == gen_path:
                bottlenecks["all_simultaneous"] += 1
        
        return bottlenecks
    
    def print_report(self):
        """Print comprehensive analysis report"""
        
        analysis = self.analyze_results()
        
        print("\n" + "="*80)
        print("CONVERGENCE FACTOR ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nExperiments: {analysis.get('total_experiments', 0)} total, "
              f"{analysis.get('collapsed_experiments', 0)} collapsed "
              f"({analysis.get('collapse_rate', 0)*100:.1f}%)")
        
        print("\n" + "-"*80)
        print("METRICS AT COLLAPSE:")
        print("-"*80)
        
        org_stats = analysis.get('organism_count_at_collapse', {})
        print(f"\nOrganism Count:")
        print(f"  Mean: {org_stats.get('mean', 0):.1f} ± {org_stats.get('std', 0):.1f}")
        print(f"  Range: {org_stats.get('min', 0)} - {org_stats.get('max', 0)} "
              f"(span: {org_stats.get('range', 0)})")
        
        degree_stats = analysis.get('average_degree_at_collapse', {})
        print(f"\nAverage Degree (connections per organism):")
        print(f"  Mean: {degree_stats.get('mean', 0):.3f} ± {degree_stats.get('std', 0):.3f}")
        print(f"  Range: {degree_stats.get('min', 0):.3f} - {degree_stats.get('max', 0):.3f} "
              f"(span: {degree_stats.get('range', 0):.3f})")
        
        density_stats = analysis.get('network_density_at_collapse', {})
        print(f"\nNetwork Density (actual / possible connections):")
        print(f"  Mean: {density_stats.get('mean', 0):.4f} ± {density_stats.get('std', 0):.4f}")
        print(f"  Range: {density_stats.get('min', 0):.4f} - {density_stats.get('max', 0):.4f} "
              f"(span: {density_stats.get('range', 0):.4f})")
        
        conn_stats = analysis.get('connection_count_at_collapse', {})
        print(f"\nTotal Connections:")
        print(f"  Mean: {conn_stats.get('mean', 0):.1f} ± {conn_stats.get('std', 0):.1f}")
        print(f"  Range: {conn_stats.get('min', 0)} - {conn_stats.get('max', 0)} "
              f"(span: {conn_stats.get('range', 0)})")
        
        print("\n" + "-"*80)
        print("BOTTLENECK ANALYSIS:")
        print("-"*80)
        
        bottlenecks = analysis.get('bottleneck_analysis', {})
        total = sum(bottlenecks.values())
        if total > 0:
            print(f"\nWhich condition is met LAST (the bottleneck):")
            for condition, count in bottlenecks.items():
                if condition != "all_simultaneous":
                    pct = (count / total) * 100 if total > 0 else 0
                    print(f"  {condition}: {count} ({pct:.1f}%)")
            print(f"\n  All simultaneous: {bottlenecks.get('all_simultaneous', 0)}")
        
        print("\n" + "-"*80)
        print("CONCLUSION:")
        print("-"*80)
        
        # Determine what drives collapse
        org_range = org_stats.get('range', 0)
        degree_range = degree_stats.get('range', 0)
        density_range = density_stats.get('range', 0)
        
        print("\nConvergence Factor Hypothesis:")
        
        if org_range < 50:  # Very consistent organism count
            print("  ✓ ORGANISM-COUNT DRIVEN: Collapse happens at consistent organism count")
            print(f"    (Range: {org_range} organisms, very consistent)")
        else:
            print("  ✗ NOT organism-count driven (too much variation)")
        
        if degree_range < 0.5:  # Very consistent average degree
            print("  ✓ DEGREE-DRIVEN: Collapse happens at consistent average degree")
            print(f"    (Range: {degree_range:.3f}, very consistent)")
        else:
            print("  ✗ NOT degree-driven (too much variation)")
        
        if density_range < 0.01:  # Very consistent density
            print("  ✓ DENSITY-DRIVEN: Collapse happens at consistent network density")
            print(f"    (Range: {density_range:.4f}, very consistent)")
        else:
            print("  ✗ NOT density-driven (too much variation)")
        
        print("\n" + "="*80)
    
    def save_results(self, filename: str = "convergence_test_results.json"):
        """Save results to JSON file"""
        output = {
            "experiments": self.results,
            "analysis": self.analyze_results(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        output_path = Path(__file__).parent / filename
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n[SAVED] Results saved to {output_path}")


def main():
    """Main entry point"""
    print("="*80)
    print("CONVERGENCE FACTOR TESTER")
    print("="*80)
    print("\nThis script tests different organism/connection configurations")
    print("to determine what actually drives network collapse.")
    print("\nHypothesis: Is collapse driven by organism count, average degree,")
    print("network density, or topology formation?")
    print("\nWARNING: This will run multiple long simulations.")
    print("Each experiment may take several minutes.")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    tester = ConvergenceFactorTester()
    results = tester.run_all_experiments()
    
    tester.print_report()
    tester.save_results()
    
    print("\n[COMPLETE] All experiments finished!")


if __name__ == "__main__":
    main()

