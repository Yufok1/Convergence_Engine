"""
Germination Pool - Where New Life Emerges from the Fallen

In the Highlander Protocol, organisms battle and the weak perish.
But from death comes new life. The Germination Pool:

1. SEEDING: Captures genetic/neural essence from fallen warriors
2. RECOMBINATION: Mixes traits from multiple casualties  
3. MUTATION: Introduces novel variations
4. GERMINATION: Births new organisms from the primordial soup
5. INJECTION: Introduces new warriors into the tournament

The pool ensures the tournament never runs dry, and that each
generation of warriors is stronger than the last.

"From the ashes of the fallen, new champions rise."
"""

import time
import random
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class GerminationStrategy(Enum):
    """How to create new organisms"""
    CLONE = "clone"                    # Direct copy with minor mutations
    CROSSOVER = "crossover"            # Combine traits from two parents
    CHIMERA = "chimera"                # Frankenstein from multiple donors
    NOVA = "nova"                      # Completely random new organism
    PHOENIX = "phoenix"                # Resurrect from champion capsule
    HYBRID = "hybrid"                  # Mix of strategies


@dataclass
class GeneticMaterial:
    """Genetic essence extracted from a fallen organism"""
    
    donor_id: str
    timestamp: float
    
    # Neural essence
    neural_weights: Optional[Dict[str, Any]] = None
    weight_stats: Dict[str, float] = field(default_factory=dict)
    
    # Language/concept essence  
    concepts: Dict[str, Any] = field(default_factory=dict)
    vocabulary_sample: List[str] = field(default_factory=list)
    
    # Configuration essence
    config_atoms: Dict[str, Any] = field(default_factory=dict)
    
    # Trait essence
    traits: Dict[str, float] = field(default_factory=dict)
    
    # Battle record (for fitness weighting)
    victories: int = 0
    defeats: int = 1  # They lost at least once to be here
    battles_survived: int = 0
    
    # Cause of death
    death_reason: str = "unknown"
    killer_id: Optional[str] = None
    
    def fitness_score(self) -> float:
        """How valuable is this genetic material?"""
        win_rate = self.victories / max(1, self.victories + self.defeats)
        survival_bonus = min(1.0, self.battles_survived / 10)
        return (win_rate * 0.6 + survival_bonus * 0.4)


@dataclass
class GerminationCandidate:
    """A potential new organism ready to be born"""
    
    candidate_id: str
    strategy: GerminationStrategy
    parent_ids: List[str]
    
    # Assembled genetic material
    neural_template: Dict[str, Any] = field(default_factory=dict)
    concept_seed: Dict[str, Any] = field(default_factory=dict)
    config_template: Dict[str, Any] = field(default_factory=dict)
    trait_template: Dict[str, float] = field(default_factory=dict)
    
    # Birth parameters
    mutation_rate: float = 0.1
    vigor: float = 1.0  # Starting health/energy
    
    # Lineage tracking
    generation: int = 1
    ancestry_depth: int = 0


class GerminationPool:
    """
    The primordial soup from which new warriors emerge.
    
    Collects genetic material from fallen organisms,
    recombines it, mutates it, and spawns new life.
    """
    
    def __init__(
        self,
        causation_explorer: Optional[Any] = None,
        max_genetic_samples: int = 100,
        min_population: int = 5,
        max_population: int = 50,
        germination_rate: float = 0.1,
        mutation_base_rate: float = 0.05,
        crossover_bias: float = 0.3
    ):
        self.causation_explorer = causation_explorer
        self.max_genetic_samples = max_genetic_samples
        self.min_population = min_population
        self.max_population = max_population
        self.germination_rate = germination_rate
        self.mutation_base_rate = mutation_base_rate
        self.crossover_bias = crossover_bias
        
        # Genetic material storage
        self.genetic_pool: Dict[str, GeneticMaterial] = {}
        self.elite_samples: List[str] = []  # Top performers
        
        # Germination queue
        self.candidates: List[GerminationCandidate] = []
        
        # Statistics
        self.total_collected = 0
        self.total_germinated = 0
        self.generation_counter = 1
        
        # Strategy weights (adaptable)
        self.strategy_weights = {
            GerminationStrategy.CLONE: 0.15,
            GerminationStrategy.CROSSOVER: 0.35,
            GerminationStrategy.CHIMERA: 0.20,
            GerminationStrategy.NOVA: 0.15,
            GerminationStrategy.PHOENIX: 0.10,
            GerminationStrategy.HYBRID: 0.05
        }
        
        # Champion capsules for phoenix resurrection
        self.champion_capsules: List[Any] = []
        
    def collect_essence(
        self,
        organism: Any,
        death_reason: str = "battle",
        killer_id: Optional[str] = None
    ) -> GeneticMaterial:
        """
        Extract genetic material from a fallen organism.
        
        This captures the essence of the organism before it
        is removed from the tournament.
        """
        org_id = getattr(organism, 'id', str(id(organism)))
        
        material = GeneticMaterial(
            donor_id=org_id,
            timestamp=time.time(),
            death_reason=death_reason,
            killer_id=killer_id
        )
        
        # Extract neural weights
        if hasattr(organism, 'neural_layer') and organism.neural_layer:
            try:
                state = organism.neural_layer.get_state()
                material.neural_weights = state
                
                # Compute weight statistics for recombination
                if 'hidden_weights' in state:
                    weights = state['hidden_weights']
                    material.weight_stats = {
                        'mean': sum(sum(row) for row in weights) / sum(len(row) for row in weights) if weights else 0,
                        'shape': f"{len(weights)}x{len(weights[0]) if weights else 0}"
                    }
            except Exception:
                pass
                
        # Extract concepts
        if hasattr(organism, 'concepts'):
            material.concepts = dict(organism.concepts)
        elif hasattr(organism, 'knowledge_base'):
            material.concepts = dict(organism.knowledge_base)
            
        # Extract vocabulary
        if hasattr(organism, 'vocabulary'):
            vocab = organism.vocabulary
            if hasattr(vocab, 'get_all_words'):
                material.vocabulary_sample = list(vocab.get_all_words())[:50]
            elif hasattr(vocab, 'word_to_id'):
                material.vocabulary_sample = list(vocab.word_to_id.keys())[:50]
                
        # Extract config atoms
        if hasattr(organism, 'config'):
            material.config_atoms = dict(organism.config)
        elif hasattr(organism, '_config'):
            material.config_atoms = dict(organism._config)
            
        # Extract traits
        if hasattr(organism, 'traits'):
            material.traits = dict(organism.traits)
        elif hasattr(organism, 'phenotype'):
            material.traits = dict(organism.phenotype)
        else:
            # Infer traits from organism properties
            material.traits = {
                'aggression': getattr(organism, 'aggression', 0.5),
                'cooperation': getattr(organism, 'cooperation', 0.5),
                'adaptability': getattr(organism, 'adaptability', 0.5),
                'resilience': getattr(organism, 'resilience', 0.5),
                'innovation': getattr(organism, 'innovation', 0.5)
            }
            
        # Extract battle record
        if hasattr(organism, 'victories'):
            material.victories = organism.victories
        if hasattr(organism, 'defeats'):
            material.defeats = organism.defeats
        if hasattr(organism, 'battles_survived'):
            material.battles_survived = organism.battles_survived
            
        # Store in pool
        self.genetic_pool[org_id] = material
        self.total_collected += 1
        
        # Update elite samples (top 20% by fitness)
        self._update_elite_samples()
        
        # Prune if over capacity
        self._prune_pool()
        
        # Emit event
        self._emit_event('essence_collected', {
            'donor_id': org_id,
            'death_reason': death_reason,
            'killer_id': killer_id,
            'fitness_score': material.fitness_score(),
            'pool_size': len(self.genetic_pool)
        })
        
        return material
        
    def _update_elite_samples(self):
        """Keep track of the highest-fitness genetic material"""
        samples = sorted(
            self.genetic_pool.items(),
            key=lambda x: x[1].fitness_score(),
            reverse=True
        )
        elite_count = max(1, len(samples) // 5)  # Top 20%
        self.elite_samples = [s[0] for s in samples[:elite_count]]
        
    def _prune_pool(self):
        """Remove lowest-fitness samples when over capacity"""
        if len(self.genetic_pool) <= self.max_genetic_samples:
            return
            
        # Sort by fitness (lowest first)
        samples = sorted(
            self.genetic_pool.items(),
            key=lambda x: x[1].fitness_score()
        )
        
        # Remove lowest until under capacity
        to_remove = len(self.genetic_pool) - self.max_genetic_samples
        for donor_id, _ in samples[:to_remove]:
            if donor_id not in self.elite_samples:  # Protect elites
                del self.genetic_pool[donor_id]
                
    def prepare_germination(
        self,
        count: int = 1,
        strategy: Optional[GerminationStrategy] = None
    ) -> List[GerminationCandidate]:
        """
        Prepare candidate organisms for germination.
        
        Returns a list of candidates ready to be instantiated.
        """
        candidates = []
        
        for _ in range(count):
            if strategy is None:
                # Choose strategy based on weights
                chosen_strategy = self._choose_strategy()
            else:
                chosen_strategy = strategy
                
            candidate = self._create_candidate(chosen_strategy)
            if candidate:
                candidates.append(candidate)
                self.candidates.append(candidate)
                
        return candidates
        
    def _choose_strategy(self) -> GerminationStrategy:
        """Choose a germination strategy based on weights"""
        strategies = list(self.strategy_weights.keys())
        weights = list(self.strategy_weights.values())
        return random.choices(strategies, weights=weights)[0]
        
    def _create_candidate(self, strategy: GerminationStrategy) -> Optional[GerminationCandidate]:
        """Create a germination candidate using the specified strategy"""
        
        candidate_id = hashlib.md5(
            f"{time.time()}-{random.random()}".encode()
        ).hexdigest()[:12]
        
        candidate = GerminationCandidate(
            candidate_id=candidate_id,
            strategy=strategy,
            parent_ids=[],
            generation=self.generation_counter
        )
        
        if strategy == GerminationStrategy.CLONE:
            self._apply_clone_strategy(candidate)
        elif strategy == GerminationStrategy.CROSSOVER:
            self._apply_crossover_strategy(candidate)
        elif strategy == GerminationStrategy.CHIMERA:
            self._apply_chimera_strategy(candidate)
        elif strategy == GerminationStrategy.NOVA:
            self._apply_nova_strategy(candidate)
        elif strategy == GerminationStrategy.PHOENIX:
            self._apply_phoenix_strategy(candidate)
        elif strategy == GerminationStrategy.HYBRID:
            self._apply_hybrid_strategy(candidate)
            
        # Apply mutations
        self._apply_mutations(candidate)
        
        return candidate
        
    def _apply_clone_strategy(self, candidate: GerminationCandidate):
        """Clone from a single elite sample with minor mutations"""
        if not self.elite_samples:
            # Fall back to nova if no elites
            self._apply_nova_strategy(candidate)
            return
            
        parent_id = random.choice(self.elite_samples)
        parent = self.genetic_pool.get(parent_id)
        
        if not parent:
            self._apply_nova_strategy(candidate)
            return
            
        candidate.parent_ids = [parent_id]
        candidate.neural_template = dict(parent.neural_weights or {})
        candidate.concept_seed = dict(parent.concepts)
        candidate.config_template = dict(parent.config_atoms)
        candidate.trait_template = dict(parent.traits)
        candidate.mutation_rate = 0.05  # Low mutation for clones
        candidate.ancestry_depth = 1
        
    def _apply_crossover_strategy(self, candidate: GerminationCandidate):
        """Combine traits from two parents"""
        if len(self.genetic_pool) < 2:
            self._apply_clone_strategy(candidate)
            return
            
        # Select two parents (prefer elites)
        pool = list(self.genetic_pool.keys())
        weights = [
            2.0 if pid in self.elite_samples else 1.0
            for pid in pool
        ]
        
        parent_ids = random.choices(pool, weights=weights, k=2)
        parent1 = self.genetic_pool[parent_ids[0]]
        parent2 = self.genetic_pool[parent_ids[1]]
        
        candidate.parent_ids = parent_ids
        
        # Crossover neural weights (average or interleave)
        candidate.neural_template = self._crossover_neural(parent1, parent2)
        
        # Crossover concepts (union with preference to fitter parent)
        candidate.concept_seed = self._crossover_concepts(parent1, parent2)
        
        # Crossover config (blend)
        candidate.config_template = self._crossover_config(parent1, parent2)
        
        # Crossover traits (weighted average)
        candidate.trait_template = self._crossover_traits(parent1, parent2)
        
        candidate.mutation_rate = 0.1
        candidate.ancestry_depth = max(
            getattr(parent1, 'ancestry_depth', 0),
            getattr(parent2, 'ancestry_depth', 0)
        ) + 1
        
    def _apply_chimera_strategy(self, candidate: GerminationCandidate):
        """Frankenstein from 3-5 donors"""
        donor_count = min(len(self.genetic_pool), random.randint(3, 5))
        
        if donor_count < 3:
            self._apply_crossover_strategy(candidate)
            return
            
        pool = list(self.genetic_pool.keys())
        donor_ids = random.sample(pool, donor_count)
        donors = [self.genetic_pool[did] for did in donor_ids]
        
        candidate.parent_ids = donor_ids
        
        # Take best neural weights
        best_neural_donor = max(donors, key=lambda d: d.fitness_score())
        candidate.neural_template = dict(best_neural_donor.neural_weights or {})
        
        # Merge all concepts
        all_concepts = {}
        for donor in donors:
            all_concepts.update(donor.concepts)
        candidate.concept_seed = all_concepts
        
        # Blend configs
        blended_config = {}
        for donor in donors:
            for key, value in donor.config_atoms.items():
                if key not in blended_config:
                    blended_config[key] = []
                blended_config[key].append(value)
        # Average numeric values
        for key, values in blended_config.items():
            if all(isinstance(v, (int, float)) for v in values):
                blended_config[key] = sum(values) / len(values)
            else:
                blended_config[key] = random.choice(values)
        candidate.config_template = blended_config
        
        # Take extreme traits
        extreme_traits = {}
        for trait in ['aggression', 'cooperation', 'adaptability', 'resilience', 'innovation']:
            values = [d.traits.get(trait, 0.5) for d in donors]
            # Take the most extreme value (furthest from 0.5)
            extreme_traits[trait] = max(values, key=lambda x: abs(x - 0.5))
        candidate.trait_template = extreme_traits
        
        candidate.mutation_rate = 0.15  # Higher mutation for chimeras
        candidate.ancestry_depth = max(getattr(d, 'ancestry_depth', 0) for d in donors) + 1
        
    def _apply_nova_strategy(self, candidate: GerminationCandidate):
        """Create a completely new random organism"""
        candidate.parent_ids = []
        
        # Random neural weights (placeholder structure)
        candidate.neural_template = {
            'hidden_weights': [[random.gauss(0, 0.1) for _ in range(16)] for _ in range(8)],
            'output_weights': [[random.gauss(0, 0.1) for _ in range(8)] for _ in range(4)]
        }
        
        # Empty concept seed
        candidate.concept_seed = {}
        
        # Default config
        candidate.config_template = {}
        
        # Random traits
        candidate.trait_template = {
            'aggression': random.random(),
            'cooperation': random.random(),
            'adaptability': random.random(),
            'resilience': random.random(),
            'innovation': random.random()
        }
        
        candidate.mutation_rate = 0.2  # High mutation for novelty
        candidate.vigor = 0.7  # Slightly weaker starting position
        candidate.ancestry_depth = 0
        
    def _apply_phoenix_strategy(self, candidate: GerminationCandidate):
        """Resurrect from a champion capsule"""
        if not self.champion_capsules:
            # No champions to resurrect, fall back to elite clone
            self._apply_clone_strategy(candidate)
            return
            
        capsule = random.choice(self.champion_capsules)
        
        candidate.parent_ids = [getattr(capsule, 'organism_id', 'unknown_champion')]
        
        # Restore from capsule
        if hasattr(capsule, 'neural_snapshot'):
            candidate.neural_template = capsule.neural_snapshot
        if hasattr(capsule, 'concept_snapshot'):
            candidate.concept_seed = capsule.concept_snapshot
        if hasattr(capsule, 'config_snapshot'):
            candidate.config_template = capsule.config_snapshot
        if hasattr(capsule, 'trait_snapshot'):
            candidate.trait_template = capsule.trait_snapshot
            
        candidate.mutation_rate = 0.03  # Very low - champions are proven
        candidate.vigor = 1.2  # Extra vigor for champions
        candidate.ancestry_depth = getattr(capsule, 'generation', 0) + 1
        
    def _apply_hybrid_strategy(self, candidate: GerminationCandidate):
        """Mix of multiple strategies"""
        strategies = [
            GerminationStrategy.CLONE,
            GerminationStrategy.CROSSOVER,
            GerminationStrategy.CHIMERA
        ]
        
        # Apply each strategy partially
        for strategy in strategies:
            temp_candidate = GerminationCandidate(
                candidate_id=candidate.candidate_id,
                strategy=strategy,
                parent_ids=[]
            )
            
            if strategy == GerminationStrategy.CLONE:
                self._apply_clone_strategy(temp_candidate)
            elif strategy == GerminationStrategy.CROSSOVER:
                self._apply_crossover_strategy(temp_candidate)
            elif strategy == GerminationStrategy.CHIMERA:
                self._apply_chimera_strategy(temp_candidate)
                
            # Merge partial results
            candidate.parent_ids.extend(temp_candidate.parent_ids)
            
        # Take random portions from each temp result
        candidate.mutation_rate = 0.12
        
    def _crossover_neural(
        self,
        parent1: GeneticMaterial,
        parent2: GeneticMaterial
    ) -> Dict[str, Any]:
        """Crossover neural weights from two parents"""
        if not parent1.neural_weights and not parent2.neural_weights:
            return {}
        if not parent1.neural_weights:
            return dict(parent2.neural_weights)
        if not parent2.neural_weights:
            return dict(parent1.neural_weights)
            
        # Simple crossover: randomly pick from each parent
        result = {}
        for key in set(parent1.neural_weights.keys()) | set(parent2.neural_weights.keys()):
            w1 = parent1.neural_weights.get(key)
            w2 = parent2.neural_weights.get(key)
            
            if w1 is None:
                result[key] = w2
            elif w2 is None:
                result[key] = w1
            elif random.random() < self.crossover_bias:
                # Prefer fitter parent
                if parent1.fitness_score() > parent2.fitness_score():
                    result[key] = w1
                else:
                    result[key] = w2
            else:
                # Average if numeric
                if isinstance(w1, (list, tuple)) and isinstance(w2, (list, tuple)):
                    # Try to average weight matrices
                    try:
                        result[key] = [
                            [(a + b) / 2 for a, b in zip(row1, row2)]
                            for row1, row2 in zip(w1, w2)
                        ]
                    except Exception:
                        result[key] = random.choice([w1, w2])
                else:
                    result[key] = random.choice([w1, w2])
                    
        return result
        
    def _crossover_concepts(
        self,
        parent1: GeneticMaterial,
        parent2: GeneticMaterial
    ) -> Dict[str, Any]:
        """Crossover concepts from two parents"""
        result = {}
        
        # Union of concepts
        all_keys = set(parent1.concepts.keys()) | set(parent2.concepts.keys())
        
        for key in all_keys:
            c1 = parent1.concepts.get(key)
            c2 = parent2.concepts.get(key)
            
            if c1 is None:
                result[key] = c2
            elif c2 is None:
                result[key] = c1
            else:
                # Both have this concept - prefer fitter parent
                if parent1.fitness_score() > parent2.fitness_score():
                    result[key] = c1
                else:
                    result[key] = c2
                    
        return result
        
    def _crossover_config(
        self,
        parent1: GeneticMaterial,
        parent2: GeneticMaterial
    ) -> Dict[str, Any]:
        """Crossover config atoms from two parents"""
        result = {}
        
        all_keys = set(parent1.config_atoms.keys()) | set(parent2.config_atoms.keys())
        
        for key in all_keys:
            v1 = parent1.config_atoms.get(key)
            v2 = parent2.config_atoms.get(key)
            
            if v1 is None:
                result[key] = v2
            elif v2 is None:
                result[key] = v1
            elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Blend numeric values
                result[key] = (v1 + v2) / 2
            else:
                result[key] = random.choice([v1, v2])
                
        return result
        
    def _crossover_traits(
        self,
        parent1: GeneticMaterial,
        parent2: GeneticMaterial
    ) -> Dict[str, float]:
        """Crossover traits from two parents (weighted average)"""
        result = {}
        
        # Weight by fitness
        f1 = parent1.fitness_score()
        f2 = parent2.fitness_score()
        total_fitness = f1 + f2
        
        if total_fitness == 0:
            w1, w2 = 0.5, 0.5
        else:
            w1 = f1 / total_fitness
            w2 = f2 / total_fitness
            
        all_traits = set(parent1.traits.keys()) | set(parent2.traits.keys())
        
        for trait in all_traits:
            t1 = parent1.traits.get(trait, 0.5)
            t2 = parent2.traits.get(trait, 0.5)
            result[trait] = t1 * w1 + t2 * w2
            
        return result
        
    def _apply_mutations(self, candidate: GerminationCandidate):
        """Apply random mutations to the candidate"""
        mutation_rate = candidate.mutation_rate + self.mutation_base_rate
        
        # Mutate traits
        for trait, value in candidate.trait_template.items():
            if random.random() < mutation_rate:
                # Gaussian mutation
                delta = random.gauss(0, 0.1)
                candidate.trait_template[trait] = max(0, min(1, value + delta))
                
        # Mutate config
        for key, value in candidate.config_template.items():
            if random.random() < mutation_rate:
                if isinstance(value, float):
                    delta = random.gauss(0, value * 0.1) if value != 0 else random.gauss(0, 0.1)
                    candidate.config_template[key] = value + delta
                elif isinstance(value, int):
                    candidate.config_template[key] = value + random.randint(-1, 1)
                    
        # Neural weight mutations are applied during actual organism creation
        
    def germinate(
        self,
        candidate: GerminationCandidate,
        organism_factory: Callable[..., Any]
    ) -> Optional[Any]:
        """
        Instantiate a new organism from the germination candidate.
        
        Args:
            candidate: The prepared candidate
            organism_factory: Function to create organism instances
            
        Returns:
            The newly created organism, or None if germination failed
        """
        try:
            # Create organism with candidate's template
            organism = organism_factory(
                organism_id=f"germinated_{candidate.candidate_id}",
                initial_traits=candidate.trait_template,
                initial_config=candidate.config_template
            )
            
            # Apply neural template
            if candidate.neural_template and hasattr(organism, 'neural_layer'):
                try:
                    organism.neural_layer.set_state(candidate.neural_template)
                except Exception:
                    pass
                    
            # Apply concepts
            if candidate.concept_seed and hasattr(organism, 'concepts'):
                organism.concepts.update(candidate.concept_seed)
                
            # Apply vigor
            if hasattr(organism, 'energy'):
                organism.energy *= candidate.vigor
            if hasattr(organism, 'health'):
                organism.health *= candidate.vigor
                
            # Mark lineage
            organism.parent_ids = candidate.parent_ids
            organism.generation = candidate.generation
            organism.germination_strategy = candidate.strategy.value
            
            self.total_germinated += 1
            
            # Remove from candidates list
            if candidate in self.candidates:
                self.candidates.remove(candidate)
                
            # Emit event
            self._emit_event('organism_germinated', {
                'organism_id': organism.id if hasattr(organism, 'id') else str(id(organism)),
                'strategy': candidate.strategy.value,
                'parent_ids': candidate.parent_ids,
                'generation': candidate.generation,
                'vigor': candidate.vigor,
                'total_germinated': self.total_germinated
            })
            
            return organism
            
        except Exception as e:
            self._emit_event('germination_failed', {
                'candidate_id': candidate.candidate_id,
                'strategy': candidate.strategy.value,
                'error': str(e)
            })
            return None
            
    def check_population_needs(
        self,
        current_population: int
    ) -> Tuple[bool, int]:
        """
        Check if the population needs reinforcement.
        
        Returns:
            (needs_germination, count_needed)
        """
        if current_population >= self.min_population:
            return (False, 0)
            
        needed = self.min_population - current_population
        
        # Apply germination rate as a throttle
        if random.random() > self.germination_rate:
            return (False, 0)
            
        return (True, needed)
        
    def add_champion_capsule(self, capsule: Any):
        """Add a champion capsule for phoenix resurrection"""
        self.champion_capsules.append(capsule)
        
        # Keep only top 10 champions
        if len(self.champion_capsules) > 10:
            self.champion_capsules = self.champion_capsules[-10:]
            
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about the germination pool"""
        fitness_scores = [m.fitness_score() for m in self.genetic_pool.values()]
        
        return {
            'genetic_samples': len(self.genetic_pool),
            'elite_count': len(self.elite_samples),
            'pending_candidates': len(self.candidates),
            'champion_capsules': len(self.champion_capsules),
            'total_collected': self.total_collected,
            'total_germinated': self.total_germinated,
            'generation': self.generation_counter,
            'avg_fitness': sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0,
            'max_fitness': max(fitness_scores) if fitness_scores else 0,
            'strategy_weights': {s.value: w for s, w in self.strategy_weights.items()}
        }
        
    def advance_generation(self):
        """Advance the generation counter (called after tournament round)"""
        self.generation_counter += 1
        
        # Adapt strategy weights based on success
        # (Could track which strategies produce winners)
        
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit a germination event"""
        if not self.causation_explorer:
            return
            
        try:
            from causation_explorer import CausationEvent
            event = CausationEvent(
                timestamp=time.time(),
                component='germination_pool',
                event_type=event_type,
                data=data
            )
            self.causation_explorer.add_event(event, is_historical=False)
        except Exception:
            pass


# ============================================================================
# Germination Pool Integration with Highlander Protocol
# ============================================================================

def integrate_germination_with_highlander(
    highlander_protocol: Any,
    germination_pool: GerminationPool,
    organism_factory: Callable[..., Any]
) -> Callable:
    """
    Wire the germination pool into the Highlander Protocol.
    
    Returns a callback that should be called after each tournament round.
    """
    
    def on_organism_eliminated(organism: Any, killer_id: Optional[str] = None):
        """Called when an organism is eliminated"""
        # Collect genetic material before removal
        germination_pool.collect_essence(
            organism,
            death_reason='tournament_elimination',
            killer_id=killer_id
        )
        
    def on_champion_crowned(organism: Any, capsule: Any):
        """Called when a champion emerges"""
        germination_pool.add_champion_capsule(capsule)
        
    def check_and_germinate() -> List[Any]:
        """Check if germination is needed and spawn new organisms"""
        current_pop = len(highlander_protocol.organisms)
        needs, count = germination_pool.check_population_needs(current_pop)
        
        if not needs:
            return []
            
        # Prepare and germinate candidates
        candidates = germination_pool.prepare_germination(count)
        new_organisms = []
        
        for candidate in candidates:
            organism = germination_pool.germinate(candidate, organism_factory)
            if organism:
                # Register with highlander protocol
                highlander_protocol.register_organism(organism)
                new_organisms.append(organism)
                
        if new_organisms:
            germination_pool.advance_generation()
            
        return new_organisms
        
    # Wire callbacks
    if hasattr(highlander_protocol, 'on_elimination_callback'):
        highlander_protocol.on_elimination_callback = on_organism_eliminated
    if hasattr(highlander_protocol, 'on_champion_callback'):
        highlander_protocol.on_champion_callback = on_champion_crowned
        
    return check_and_germinate
