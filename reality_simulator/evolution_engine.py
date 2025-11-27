"""
🧬 GENETIC EVOLUTION ENGINE (Layer 2)

Darwinian evolution through genetic algorithms - where quantum particles
become organisms with heritable traits, fitness evaluation, and natural selection.

Features:
- BitArray genotypes for memory efficiency
- Recursive genotype → phenotype mapping
- Adaptive mutation rates based on fitness landscape
- Cached fitness evaluation
- Generational batching for performance
- Tournament selection and elitism
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib


class GenotypeEncoding(Enum):
    """Different ways to encode genetic information"""
    BIT_ARRAY = "bit_array"  # Binary string
    REAL_VALUED = "real_valued"  # Floating point genes
    INTEGER = "integer"  # Integer genes
    MIXED = "mixed"  # Combination of types


@dataclass
class Genotype:
    """
    Genetic representation of an organism

    Uses efficient bit array encoding for memory optimization
    Now includes consciousness emergence traits
    """
    genes: np.ndarray  # Bit array (uint8 for memory efficiency)
    encoding: GenotypeEncoding = GenotypeEncoding.BIT_ARRAY
    fitness: Optional[float] = None
    age: int = 0
    generation: int = 0

    def __post_init__(self):
        if self.encoding == GenotypeEncoding.BIT_ARRAY:
            # Ensure genes are binary
            self.genes = (self.genes > 0).astype(np.uint8)



    def get_hash(self) -> str:
        """Get unique hash for this genotype (for caching)"""
        return hashlib.md5(self.genes.tobytes()).hexdigest()[:16]

    def copy(self) -> 'Genotype':
        """Create a deep copy"""
        return Genotype(
            genes=self.genes.copy(),
            encoding=self.encoding,
            fitness=self.fitness,
            age=self.age + 1,
            generation=self.generation
        )

    def mutate(self, rate: float = 0.01) -> 'Genotype':
        """Apply random mutations"""
        if self.encoding == GenotypeEncoding.BIT_ARRAY:
            return self._mutate_bit_array(rate)
        else:
            return self._mutate_real_valued(rate)

    def _mutate_bit_array(self, rate: float) -> 'Genotype':
        """Bit flip mutations for binary encoding"""
        mutated = self.copy()

        # Flip bits with given probability
        mutation_mask = np.random.random(len(self.genes)) < rate
        mutated.genes = (mutated.genes + mutation_mask.astype(np.uint8)) % 2

        return mutated

    def _mutate_real_valued(self, rate: float) -> 'Genotype':
        """Gaussian mutations for real-valued genes"""
        mutated = self.copy()

        # Add Gaussian noise to genes
        noise = np.random.normal(0, 0.1, len(self.genes))
        mutation_mask = np.random.random(len(self.genes)) < rate
        mutated.genes = mutated.genes + (noise * mutation_mask)

        # Clamp to reasonable bounds
        mutated.genes = np.clip(mutated.genes, 0.0, 1.0)

        return mutated

    def crossover(self, other: 'Genotype', method: str = 'single_point') -> Tuple['Genotype', 'Genotype']:
        """Crossover with another genotype"""
        if self.encoding == GenotypeEncoding.BIT_ARRAY:
            return self._crossover_bit_array(other, method)
        else:
            return self._crossover_real_valued(other)

    def _crossover_bit_array(self, other: 'Genotype', method: str) -> Tuple['Genotype', 'Genotype']:
        """Single/multi-point crossover for binary genes"""
        if method == 'uniform':
            # Uniform crossover
            mask = np.random.random(len(self.genes)) > 0.5
            child1_genes = np.where(mask, self.genes, other.genes)
            child2_genes = np.where(mask, other.genes, self.genes)
        else:
            # Single-point crossover
            point = np.random.randint(1, len(self.genes))
            child1_genes = np.concatenate([self.genes[:point], other.genes[point:]])
            child2_genes = np.concatenate([other.genes[:point], self.genes[point:]])

        child1 = Genotype(genes=child1_genes, encoding=self.encoding,
                         generation=max(self.generation, other.generation) + 1)
        child2 = Genotype(genes=child2_genes, encoding=self.encoding,
                         generation=max(self.generation, other.generation) + 1)

        return child1, child2

    def _crossover_real_valued(self, other: 'Genotype') -> Tuple['Genotype', 'Genotype']:
        """Blend crossover for real-valued genes"""
        alpha = np.random.uniform(0.1, 0.9)
        child1_genes = alpha * self.genes + (1 - alpha) * other.genes
        child2_genes = (1 - alpha) * self.genes + alpha * other.genes

        child1 = Genotype(genes=child1_genes, encoding=self.encoding,
                         generation=max(self.generation, other.generation) + 1)
        child2 = Genotype(genes=child2_genes, encoding=self.encoding,
                         generation=max(self.generation, other.generation) + 1)

        return child1, child2


@dataclass
class Phenotype:
    """
    Observable traits and characteristics of an organism

    Maps genotype to expressed traits through recursive development
    Now includes consciousness emergence phenotypes
    """
    traits: Dict[str, float] = field(default_factory=dict)
    development_stage: int = 0
    environmental_factors: Dict[str, float] = field(default_factory=dict)

    def express_trait(self, trait_name: str, genotype_value: float,
                     environmental_modifier: float = 1.0) -> float:
        """Express a trait from genotype with environmental influence"""
        # Base expression
        base_value = genotype_value

        # Environmental modification
        modified_value = base_value * environmental_modifier

        # Development stage affects expression (default to 1.0 if development_stage is 0)
        if self.development_stage == 0:
            development_factor = 1.0
        else:
            development_factor = min(1.0, self.development_stage / 10.0)
        final_value = modified_value * development_factor

        # Store the trait
        self.traits[trait_name] = final_value
        return final_value

    def get_fitness_contribution(self, trait_name: str, target_value: float) -> float:
        """Calculate how well this trait contributes to fitness"""
        if trait_name not in self.traits:
            return 0.0

        actual_value = self.traits[trait_name]
        deviation = abs(actual_value - target_value)

        # Fitness decreases with deviation (Gaussian fitness)
        return np.exp(-deviation**2)


@dataclass
class Organism:
    """
    Complete organism with genotype, phenotype, and evolutionary history
    """
    genotype: Genotype
    phenotype: Phenotype = field(default_factory=Phenotype)
    fitness: float = 0.0
    species_id: Optional[str] = None
    parent_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.species_id is None:
            self.species_id = self.genotype.get_hash()

    def develop_phenotype(self, environmental_factors: Dict[str, float] = None):
        """Develop phenotype from genotype with consciousness emergence"""
        if environmental_factors:
            self.phenotype.environmental_factors.update(environmental_factors)

        # Express traditional traits from genotype genes
        num_traits = min(len(self.genotype.genes), 10)  # Limit traits for simplicity

        for i in range(num_traits):
            trait_name = f"trait_{i}"
            genotype_value = self.genotype.genes[i] / 255.0  # Normalize to [0, 1]

            # Environmental modifier (default 1.0 if no environmental factor)
            env_modifier = self.phenotype.environmental_factors.get(trait_name, 1.0)

            expressed_value = self.phenotype.express_trait(
                trait_name, genotype_value, env_modifier
            )

        # Increase development stage
        self.phenotype.development_stage += 1

    def calculate_fitness(self, fitness_targets: Dict[str, float]) -> float:
        """Calculate overall fitness based on trait targets including consciousness"""
        total_fitness = 0.0

        # Traditional trait fitness
        for trait_name, target_value in fitness_targets.items():
            contribution = self.phenotype.get_fitness_contribution(trait_name, target_value)
            total_fitness += contribution

        # Normalize by number of traits
        if fitness_targets:
            total_fitness /= len(fitness_targets)

        # Clamp fitness to valid bounds [0, 1] with high precision
        total_fitness = np.clip(total_fitness, 0.0, 1.0)

        # Apply high-precision rounding based on config
        fitness_precision = getattr(self, 'fitness_precision', 0.000001)
        total_fitness = round(total_fitness / fitness_precision) * fitness_precision

        self.fitness = total_fitness
        self.genotype.fitness = total_fitness

        return total_fitness


class FitnessCache:
    """
    Caches fitness calculations to avoid recomputation

    Uses genotype hash for efficient lookup
    """

    def __init__(self, max_cache_size: int = 10000):
        self.cache: Dict[str, float] = {}
        self.max_cache_size = max_cache_size
        self.access_order: List[str] = []  # For LRU eviction

    def get(self, genotype_hash: str) -> Optional[float]:
        """Get cached fitness value"""
        if genotype_hash in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(genotype_hash)
            self.access_order.append(genotype_hash)
            return self.cache[genotype_hash]
        return None

    def put(self, genotype_hash: str, fitness: float):
        """Cache fitness value"""
        if genotype_hash in self.cache:
            # Update existing
            self.access_order.remove(genotype_hash)
        elif len(self.cache) >= self.max_cache_size:
            # Evict least recently used
            evicted = self.access_order.pop(0)
            del self.cache[evicted]

        self.cache[genotype_hash] = fitness
        self.access_order.append(genotype_hash)

    def clear(self):
        """Clear all cached values"""
        self.cache.clear()
        self.access_order.clear()

    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_cache_size,
            'hit_rate_estimate': 0  # Would need hit/miss tracking
        }


class SelectionEngine:
    """
    Handles parent selection and survival using various strategies
    """

    def __init__(self, tournament_size: int = 5, elitism_rate: float = 0.1):
        self.tournament_size = tournament_size
        self.elitism_rate = elitism_rate

    def tournament_selection(self, population: List[Organism], num_parents: int) -> List[Organism]:
        """Tournament selection for parent selection"""
        parents = []

        for _ in range(num_parents):
            # Select random tournament participants
            tournament = np.random.choice(population, self.tournament_size, replace=False)

            # Find winner (highest fitness)
            winner = max(tournament, key=lambda org: org.fitness)
            parents.append(winner)

        return parents

    def elitism_selection(self, population: List[Organism], num_elites: int) -> List[Organism]:
        """Select top performers for direct survival"""
        sorted_pop = sorted(population, key=lambda org: org.fitness, reverse=True)
        return sorted_pop[:num_elites]

    def rank_based_selection(self, population: List[Organism], num_selected: int) -> List[Organism]:
        """Rank-based selection (fitness proportional to rank)"""
        sorted_pop = sorted(population, key=lambda org: org.fitness, reverse=True)

        # Calculate selection probabilities based on rank
        ranks = np.arange(1, len(sorted_pop) + 1)
        probabilities = 1.0 / ranks  # Higher rank = higher probability
        probabilities /= probabilities.sum()

        # Select based on probabilities
        selected_indices = np.random.choice(len(sorted_pop), num_selected, p=probabilities)
        selected = [sorted_pop[i] for i in selected_indices]

        return selected


class MutationEngine:
    """
    Handles mutation operations with adaptive rates
    """

    def __init__(self, base_rate: float = 0.01, adaptive: bool = True):
        self.base_rate = base_rate
        self.adaptive = adaptive
        self.generation_stats = {
            'avg_fitness': [],
            'mutation_rates': []
        }

    def get_adaptive_rate(self, population: List[Organism], current_gen: int) -> float:
        """Calculate adaptive mutation rate based on population diversity and progress"""
        if not self.adaptive or len(self.generation_stats['avg_fitness']) < 2:
            return self.base_rate

        # Calculate fitness trend
        recent_fitness = self.generation_stats['avg_fitness'][-5:]  # Last 5 generations
        fitness_trend = np.polyfit(range(len(recent_fitness)), recent_fitness, 1)[0]

        # Calculate population diversity (coefficient of variation)
        fitnesses = [org.fitness for org in population]
        diversity = np.std(fitnesses) / (np.mean(fitnesses) + 1e-10)

        # Adaptive rate calculation
        if fitness_trend < 0.001:  # Stagnation
            rate = self.base_rate * 2.0  # Increase exploration
        elif diversity < 0.1:  # Low diversity
            rate = self.base_rate * 1.5  # Increase variation
        elif fitness_trend > 0.01:  # Strong progress
            rate = self.base_rate * 0.8  # Decrease disruption
        else:
            rate = self.base_rate  # Maintain baseline

        # Clamp to reasonable bounds
        rate = np.clip(rate, 0.001, 0.1)

        self.generation_stats['mutation_rates'].append(rate)
        return rate

    def apply_mutations(self, offspring: List[Genotype], rate: float) -> List[Genotype]:
        """Apply mutations to a generation of offspring"""
        mutated = []

        for genotype in offspring:
            if np.random.random() < 0.3:  # 30% chance of mutation
                mutated_genotype = genotype.mutate(rate)
                mutated.append(mutated_genotype)
            else:
                mutated.append(genotype)

        return mutated

    def update_stats(self, population: List[Organism]):
        """Update generation statistics"""
        avg_fitness = np.mean([org.fitness for org in population])
        self.generation_stats['avg_fitness'].append(avg_fitness)

        # Keep only recent stats
        max_stats = 50
        if len(self.generation_stats['avg_fitness']) > max_stats:
            self.generation_stats['avg_fitness'] = self.generation_stats['avg_fitness'][-max_stats:]
            if len(self.generation_stats['mutation_rates']) > max_stats:
                self.generation_stats['mutation_rates'] = self.generation_stats['mutation_rates'][-max_stats:]


class EvolutionEngine:
    """
    Main evolution engine coordinating all genetic operations
    """

    def __init__(self,
                 population_size: int = 100,
                 genotype_length: int = 32,
                 max_generations: int = 1000,
                 fitness_targets: Optional[Dict[str, float]] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.population_size = population_size
        self.genotype_length = genotype_length
        self.max_generations = max_generations
        self.config = config or {}

        # Initialize components
        self.selection = SelectionEngine()
        self.mutation = MutationEngine()
        self.fitness_cache = FitnessCache()

        # Fitness targets for evaluation
        self.fitness_targets = fitness_targets or {
            'trait_0': 0.8,  # Target high values for some traits
            'trait_1': 0.2,  # Target low values for others
            'trait_2': 0.5,  # Target medium values
        }

        # Population tracking
        self.population: List[Organism] = []
        self.generation = 0
        self.best_fitness_history = []
        self.average_fitness_history = []

        # Initialize population
        self._initialize_population()

    def _initialize_population(self):
        """Create initial random population"""
        self.population = []

        for _ in range(self.population_size):
            # Random binary genotype
            genes = np.random.randint(0, 2, self.genotype_length, dtype=np.uint8)
            genotype = Genotype(genes=genes, generation=0)

            organism = self._create_organism(genotype)
            self.population.append(organism)



    def evolve_generation(self) -> Dict[str, Any]:
        """Run one generation of evolution with consciousness tracking"""
        start_time = time.time()

        # Evaluate fitness (with caching)
        self._evaluate_population()

        # Track statistics
        fitnesses = [org.fitness for org in self.population]
        self.best_fitness_history.append(max(fitnesses))
        self.average_fitness_history.append(np.mean(fitnesses))

        # Selection
        num_elites = int(self.population_size * self.selection.elitism_rate)
        elites = self.selection.elitism_selection(self.population, num_elites)
        num_parents = self.population_size - num_elites
        parents = self.selection.tournament_selection(self.population, num_parents)

        # Reproduction
        offspring = self._create_offspring(parents, num_parents)

        # Mutation
        mutation_rate = self.mutation.get_adaptive_rate(self.population, self.generation)
        mutated_offspring = self.mutation.apply_mutations(offspring, mutation_rate)

        # Update mutation stats
        self.mutation.update_stats(self.population)

        # Create new population
        new_population = elites.copy()
        for genotype in mutated_offspring:
            organism = self._create_organism(genotype, parents=parents)
            new_population.append(organism)

        self.population = new_population[:self.population_size]
        self.generation += 1

        # Performance metrics
        elapsed = time.time() - start_time

        return {
            'generation': self.generation,
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'mutation_rate': mutation_rate,
            'elapsed_seconds': elapsed,
            'population_diversity': np.std(fitnesses)
        }

    def _evaluate_population(self):
        """Evaluate fitness for all organisms (with caching)"""
        for organism in self.population:
            # Check cache first
            genotype_hash = organism.genotype.get_hash()
            cached_fitness = self.fitness_cache.get(genotype_hash)

            if cached_fitness is not None:
                organism.fitness = cached_fitness
                organism.genotype.fitness = cached_fitness
            else:
                # Develop phenotype and calculate fitness
                organism.develop_phenotype()
                fitness = organism.calculate_fitness(self.fitness_targets)

                # Cache result
                self.fitness_cache.put(genotype_hash, fitness)

    def _create_offspring(self, parents: List[Organism], num_offspring: int) -> List[Genotype]:
        """Create offspring from selected parents"""
        offspring = []

        while len(offspring) < num_offspring:
            # Select two random parents
            parent1, parent2 = np.random.choice(parents, 2, replace=False)

            # Crossover
            child1_genotype, child2_genotype = parent1.genotype.crossover(parent2.genotype)

            offspring.extend([child1_genotype, child2_genotype])

        return offspring[:num_offspring]

    def evolve_for_generations(self, num_generations: int = 100,
                              progress_callback: Optional[Callable] = None) -> Dict[str, List]:
        """Run evolution for multiple generations"""
        history = {
            'generations': [],
            'best_fitness': [],
            'avg_fitness': [],
            'mutation_rates': [],
            'elapsed_times': [],
            'diversity': []
        }

        for gen in range(num_generations):
            if gen >= self.max_generations:
                break

            stats = self.evolve_generation()

            # Record history with correct key mapping
            history['generations'].append(stats.get('generation', 0))
            history['best_fitness'].append(stats.get('best_fitness', 0.0))
            history['avg_fitness'].append(stats.get('avg_fitness', 0.0))
            history['mutation_rates'].append(stats.get('mutation_rate', 0.0))
            history['elapsed_times'].append(stats.get('elapsed_seconds', 0.0))
            history['diversity'].append(stats.get('population_diversity', 0.0))

            # Progress callback
            if progress_callback:
                progress_callback(stats)

        return history

    def get_population_stats(self) -> Dict[str, Any]:
        """Get comprehensive population statistics"""
        if not self.population:
            return {}

        fitnesses = [org.fitness for org in self.population]
        genotypes = [org.genotype for org in self.population]

        return {
            'population_size': len(self.population),
            'generation': self.generation,
            'best_fitness': max(fitnesses),
            'avg_fitness': np.mean(fitnesses),
            'fitness_std': np.std(fitnesses),
            'genotype_diversity': len(set(g.get_hash() for g in genotypes)),
            'cache_stats': self.fitness_cache.stats(),
            'mutation_stats': self.mutation.generation_stats
        }

    def get_best_organism(self) -> Optional[Organism]:
        """Get the organism with highest fitness"""
        if not self.population:
            return None
        return max(self.population, key=lambda org: org.fitness)

    def set_mutation_rate(self, rate: float):
        """Set the base mutation rate for the mutation engine"""
        self.mutation.base_rate = max(0.001, min(0.1, rate))  # Clamp to reasonable bounds

    def get_mutation_rate(self) -> float:
        """Get the current base mutation rate"""
        return self.mutation.base_rate
    
    def _create_organism(self, genotype: Genotype, parents: Optional[List[Organism]] = None) -> Organism:
        """
        Factory method for organism creation.
        Creates NeuralOrganism if neural is enabled, otherwise standard Organism.
        
        Args:
            genotype: Organism genotype
            parents: Parent organisms (for brain inheritance)
            
        Returns:
            Organism or NeuralOrganism instance
        """
        neural_config = self.config.get('neural', {})
        
        if neural_config.get('enabled', False):
            try:
                from .neural.neural_organism import NeuralOrganism
                
                # Try to inherit brain from parents if available
                parent_brain = None
                if parents and len(parents) > 0:
                    # Check if any parent is a NeuralOrganism with a brain
                    for parent in parents:
                        if hasattr(parent, 'brain') and parent.brain is not None:
                            parent_brain = parent.brain
                            break
                
                return NeuralOrganism(
                    genotype=genotype,
                    config=self.config,
                    parent_brain=parent_brain
                )
            except ImportError:
                # PyTorch not available, fall back to standard Organism
                return Organism(genotype=genotype)
        else:
            return Organism(genotype=genotype)


# Utility functions for easy use
def create_evolution_engine(population_size: int = 100,
                          genotype_length: int = 32,
                          fitness_targets: Optional[Dict[str, float]] = None,
                          config: Optional[Dict[str, Any]] = None) -> EvolutionEngine:
    """Create a ready-to-use evolution engine"""
    return EvolutionEngine(
        population_size=population_size,
        genotype_length=genotype_length,
        fitness_targets=fitness_targets,
        config=config
    )


def simple_fitness_function(organism: Organism) -> float:
    """Simple fitness function for testing"""
    # Reward organisms with balanced traits
    total_balance = 0.0
    for trait_name, trait_value in organism.phenotype.traits.items():
        # Ideal trait values depend on trait name
        if 'trait_0' in trait_name:
            ideal = 0.8
        elif 'trait_1' in trait_name:
            ideal = 0.2
        else:
            ideal = 0.5

        balance = 1.0 - abs(trait_value - ideal)
        total_balance += balance

    return total_balance / max(1, len(organism.phenotype.traits))


# Module-level docstring
"""
🧬 EVOLUTION ENGINE = GENETIC ALGORITHMS FOR LIFE

This module brings Darwinian evolution to the simulator:
- Organisms with heritable traits compete and reproduce
- Fitness evaluation drives natural selection
- Mutations introduce variation
- Caching prevents redundant calculations
- Adaptive rates respond to evolutionary pressure

Where quantum particles become living, evolving organisms.
"""

