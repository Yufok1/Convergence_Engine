"""
🧪 VALIDATION FRAMEWORK - Measuring Learning vs Oscillation

This module provides benchmarking infrastructure to validate that the
Butterfly System is actually LEARNING and not just randomly exploring.

Core Questions to Answer:
1. Does dual inheritance (genetic + neural) outperform pure genetic?
2. Does meta-cognitive tuning improve evolution rate?
3. Does VP monitoring enable open-ended evolution?
4. Are emergent behaviors reproducible?

Usage:
    python validation_framework.py --mode baseline
    python validation_framework.py --mode dual_inheritance
    python validation_framework.py --mode comparison
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import argparse


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run"""
    name: str
    duration_generations: int
    population_size: int
    neural_enabled: bool
    meta_cognitive_enabled: bool
    random_seed: Optional[int] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'duration_generations': self.duration_generations,
            'population_size': self.population_size,
            'neural_enabled': self.neural_enabled,
            'meta_cognitive_enabled': self.meta_cognitive_enabled,
            'random_seed': self.random_seed,
            'description': self.description
        }


@dataclass
class EvolutionMetrics:
    """Metrics collected during an evolution run"""
    generation: int
    timestamp: float
    
    # Fitness metrics
    max_fitness: float
    mean_fitness: float
    median_fitness: float
    fitness_std: float
    
    # Diversity metrics
    genotype_diversity: float  # Shannon entropy of genotypes
    phenotype_diversity: float  # Number of unique phenotypes
    behavior_diversity: float   # Variance in action patterns
    
    # Network metrics
    organism_count: int
    connection_count: int
    modularity: float
    clustering_coefficient: float
    
    # Neural metrics (if enabled)
    neural_training_loss: Optional[float] = None
    avg_epsilon: Optional[float] = None
    neural_organisms_count: Optional[int] = None
    
    # ML metrics (if enabled)
    cluster_count: Optional[int] = None
    anomaly_ratio: Optional[float] = None
    
    # VP metrics
    violation_pressure: float = 0.0
    vp_classification: str = "VP0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'generation': self.generation,
            'timestamp': self.timestamp,
            'max_fitness': self.max_fitness,
            'mean_fitness': self.mean_fitness,
            'median_fitness': self.median_fitness,
            'fitness_std': self.fitness_std,
            'genotype_diversity': self.genotype_diversity,
            'phenotype_diversity': self.phenotype_diversity,
            'behavior_diversity': self.behavior_diversity,
            'organism_count': self.organism_count,
            'connection_count': self.connection_count,
            'modularity': self.modularity,
            'clustering_coefficient': self.clustering_coefficient,
            'neural_training_loss': self.neural_training_loss,
            'avg_epsilon': self.avg_epsilon,
            'neural_organisms_count': self.neural_organisms_count,
            'cluster_count': self.cluster_count,
            'anomaly_ratio': self.anomaly_ratio,
            'violation_pressure': self.violation_pressure,
            'vp_classification': self.vp_classification
        }


@dataclass
class ExperimentResults:
    """Results from a complete experiment"""
    config: ExperimentConfig
    metrics_history: List[EvolutionMetrics] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Summary statistics
    final_max_fitness: Optional[float] = None
    fitness_improvement_rate: Optional[float] = None  # Fitness gain per generation
    convergence_generation: Optional[int] = None  # When fitness plateaus
    diversity_collapse_generation: Optional[int] = None  # When diversity drops
    
    def calculate_summary(self):
        """Calculate summary statistics from metrics history"""
        if not self.metrics_history:
            return
        
        # Final fitness
        self.final_max_fitness = self.metrics_history[-1].max_fitness
        
        # Fitness improvement rate (linear regression)
        generations = [m.generation for m in self.metrics_history]
        max_fitnesses = [m.max_fitness for m in self.metrics_history]
        
        if len(generations) > 1:
            # Simple linear regression
            x = np.array(generations)
            y = np.array(max_fitnesses)
            slope = np.polyfit(x, y, 1)[0]
            self.fitness_improvement_rate = slope
        
        # Detect convergence (fitness plateau)
        window_size = 20
        plateau_threshold = 0.01  # < 1% change over window
        
        for i in range(window_size, len(max_fitnesses)):
            window = max_fitnesses[i-window_size:i]
            if (max(window) - min(window)) / (max(window) + 1e-6) < plateau_threshold:
                self.convergence_generation = generations[i]
                break
        
        # Detect diversity collapse
        diversities = [m.genotype_diversity for m in self.metrics_history]
        collapse_threshold = 0.1  # Shannon entropy < 0.1
        
        for i, diversity in enumerate(diversities):
            if diversity < collapse_threshold:
                self.diversity_collapse_generation = generations[i]
                break
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'config': self.config.to_dict(),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': (self.end_time - self.start_time) if self.end_time else None,
            'final_max_fitness': self.final_max_fitness,
            'fitness_improvement_rate': self.fitness_improvement_rate,
            'convergence_generation': self.convergence_generation,
            'diversity_collapse_generation': self.diversity_collapse_generation,
            'metrics_history': [m.to_dict() for m in self.metrics_history]
        }


class ValidationFramework:
    """
    Framework for validating learning in the Butterfly System.
    
    Provides:
    - Baseline experiments (pure genetic algorithm)
    - Treatment experiments (with neural/meta-cognitive)
    - Comparison analysis
    - Statistical significance testing
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / 'data' / 'validation'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Experiment definitions
        self.experiments = {
            'baseline_genetic': ExperimentConfig(
                name='baseline_genetic',
                duration_generations=500,
                population_size=2000,
                neural_enabled=False,
                meta_cognitive_enabled=False,
                description='Pure genetic algorithm baseline (no neural, no tuning)'
            ),
            'dual_inheritance': ExperimentConfig(
                name='dual_inheritance',
                duration_generations=500,
                population_size=2000,
                neural_enabled=True,
                meta_cognitive_enabled=False,
                description='Genetic + Neural (dual inheritance, no tuning)'
            ),
            'full_system': ExperimentConfig(
                name='full_system',
                duration_generations=500,
                population_size=2000,
                neural_enabled=True,
                meta_cognitive_enabled=True,
                description='Full system (genetic + neural + meta-cognitive tuning)'
            ),
        }
    
    def run_experiment(self, config: ExperimentConfig, replicate: int = 0) -> ExperimentResults:
        """
        Run a single experiment with given configuration.
        
        Args:
            config: Experiment configuration
            replicate: Replicate number (for multiple runs with different seeds)
        
        Returns:
            ExperimentResults with complete metrics history
        """
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING EXPERIMENT: {config.name} (replicate {replicate})")
        print(f"{'='*60}")
        print(f"Description: {config.description}")
        print(f"Duration: {config.duration_generations} generations")
        print(f"Population: {config.population_size} organisms")
        print(f"Neural: {config.neural_enabled}")
        print(f"Meta-Cognitive: {config.meta_cognitive_enabled}")
        print(f"Seed: {config.random_seed}")
        print()
        
        results = ExperimentResults(config=config)
        
        # TODO: Integrate with unified_entry.py to run actual simulation
        # For now, this is a skeleton that shows the structure
        
        print(f"⚠️  This is a validation framework skeleton.")
        print(f"⚠️  Integration with unified_entry.py required to run actual experiments.")
        print(f"⚠️  Expected implementation:")
        print(f"     1. Modify config.json based on ExperimentConfig")
        print(f"     2. Run unified_entry.py with --max-cycles flag")
        print(f"     3. Collect metrics from shared_state.json")
        print(f"     4. Record EvolutionMetrics for each generation")
        
        results.end_time = time.time()
        return results
    
    def compare_experiments(self, 
                           baseline_results: ExperimentResults,
                           treatment_results: ExperimentResults) -> Dict[str, Any]:
        """
        Compare two experiments and determine if treatment is significantly better.
        
        Returns:
            Comparison analysis with statistical tests
        """
        comparison = {
            'baseline': baseline_results.config.name,
            'treatment': treatment_results.config.name,
            'comparison_timestamp': time.time()
        }
        
        # Fitness comparison
        baseline_final = baseline_results.final_max_fitness
        treatment_final = treatment_results.final_max_fitness
        
        if baseline_final and treatment_final:
            improvement_pct = ((treatment_final - baseline_final) / baseline_final) * 100
            comparison['fitness_improvement_pct'] = improvement_pct
            comparison['winner'] = 'treatment' if improvement_pct > 0 else 'baseline'
        
        # Convergence speed comparison
        baseline_conv = baseline_results.convergence_generation
        treatment_conv = treatment_results.convergence_generation
        
        if baseline_conv and treatment_conv:
            speedup = baseline_conv / treatment_conv
            comparison['convergence_speedup'] = speedup
        
        # Diversity maintenance comparison
        baseline_collapse = baseline_results.diversity_collapse_generation
        treatment_collapse = treatment_results.diversity_collapse_generation
        
        if baseline_collapse and treatment_collapse:
            diversity_benefit = (treatment_collapse - baseline_collapse) / baseline_collapse
            comparison['diversity_benefit_pct'] = diversity_benefit * 100
        
        return comparison
    
    def run_full_validation(self, replicates: int = 3):
        """
        Run complete validation suite with multiple replicates.
        
        Args:
            replicates: Number of replicates per experiment (for statistical power)
        """
        print(f"\n{'='*60}")
        print(f"🦋 BUTTERFLY SYSTEM VALIDATION SUITE")
        print(f"{'='*60}")
        print(f"Running {len(self.experiments)} experiments with {replicates} replicates each")
        print(f"Total runs: {len(self.experiments) * replicates}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        all_results = {}
        
        for exp_name, exp_config in self.experiments.items():
            exp_results = []
            
            for rep in range(replicates):
                # Set different seed for each replicate
                config = ExperimentConfig(**exp_config.to_dict())
                config.random_seed = rep if config.random_seed is None else config.random_seed + rep
                
                result = self.run_experiment(config, replicate=rep)
                result.calculate_summary()
                exp_results.append(result)
                
                # Save individual result
                result_file = self.output_dir / f"{exp_name}_rep{rep}.json"
                with open(result_file, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)
            
            all_results[exp_name] = exp_results
        
        # Perform comparisons
        print(f"\n{'='*60}")
        print(f"📊 COMPARISON ANALYSIS")
        print(f"{'='*60}\n")
        
        if 'baseline_genetic' in all_results and 'dual_inheritance' in all_results:
            comparison = self.compare_experiments(
                all_results['baseline_genetic'][0],
                all_results['dual_inheritance'][0]
            )
            print(f"Baseline vs Dual Inheritance:")
            print(f"  Fitness improvement: {comparison.get('fitness_improvement_pct', 'N/A'):.2f}%")
            print(f"  Winner: {comparison.get('winner', 'N/A')}")
            print()
        
        if 'dual_inheritance' in all_results and 'full_system' in all_results:
            comparison = self.compare_experiments(
                all_results['dual_inheritance'][0],
                all_results['full_system'][0]
            )
            print(f"Dual Inheritance vs Full System:")
            print(f"  Fitness improvement: {comparison.get('fitness_improvement_pct', 'N/A'):.2f}%")
            print(f"  Winner: {comparison.get('winner', 'N/A')}")
            print()
        
        # Save summary
        summary_file = self.output_dir / 'validation_summary.json'
        summary = {
            'timestamp': time.time(),
            'replicates_per_experiment': replicates,
            'experiments': list(self.experiments.keys()),
            'results_directory': str(self.output_dir)
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Validation complete. Results saved to {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Butterfly System Validation Framework')
    parser.add_argument('--mode', choices=['baseline', 'dual', 'full', 'compare', 'all'],
                       default='all', help='Validation mode to run')
    parser.add_argument('--replicates', type=int, default=3,
                       help='Number of replicates per experiment')
    parser.add_argument('--output-dir', type=Path, default=None,
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    framework = ValidationFramework(output_dir=args.output_dir)
    
    if args.mode == 'all':
        framework.run_full_validation(replicates=args.replicates)
    else:
        print("Single experiment mode not yet implemented")


if __name__ == '__main__':
    main()
