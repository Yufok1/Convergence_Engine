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
import logging
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
    REGRESSED = "regressed"            # Earlier developmental state (less evolved)
    CALIBRATED = "calibrated"          # Tuned to current population fitness level


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
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAGNETISM INHERITANCE - Bonds that persist across death
    # Healed organisms encode their fixed-point attractor in magnetism
    # ═══════════════════════════════════════════════════════════════════════════
    magnetism_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {concept_id: {base_magnetism, curiosity_magnetism, outcome_history, satiation}}
    association_strengths: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # {concept_id: {target_id: strength}}
    
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
    
    # Developmental stage (for regression strategy)
    developmental_stage: float = 1.0  # 0.0 = newborn, 1.0 = fully developed
    age_at_capture: float = 0.0
    
    def fitness_score(self) -> float:
        """How valuable is this genetic material?"""
        win_rate = self.victories / max(1, self.victories + self.defeats)
        survival_bonus = min(1.0, self.battles_survived / 10)
        return (win_rate * 0.6 + survival_bonus * 0.4)
    
    def semantic_coherence(self) -> float:
        """
        Calculate semantic coherence - stability of magnetism landscape.
        
        High coherence = stable fixed-point attractor (healed phenotype)
        Low coherence = oscillating/unstable (trapped phenotype)
        """
        if not self.magnetism_states:
            return 0.5  # Neutral if no magnetism data
        
        # Calculate magnetism stability (low variance = high coherence)
        magnetism_values = [
            state.get('curiosity_magnetism', 0.5) 
            for state in self.magnetism_states.values()
        ]
        if len(magnetism_values) < 2:
            return 0.5
        
        mean_mag = sum(magnetism_values) / len(magnetism_values)
        variance = sum((m - mean_mag) ** 2 for m in magnetism_values) / len(magnetism_values)
        stability = 1.0 / (1.0 + variance * 10)  # Higher variance = lower stability
        
        # Calculate outcome history consistency (positive trends = healed)
        positive_outcomes = 0
        total_outcomes = 0
        for state in self.magnetism_states.values():
            history = state.get('outcome_history', [])
            for outcome in history:
                total_outcomes += 1
                if outcome > 0:
                    positive_outcomes += 1
        
        outcome_positivity = positive_outcomes / max(1, total_outcomes)
        
        # Coherence = weighted combination
        coherence = (stability * 0.6 + outcome_positivity * 0.4)
        return min(1.0, max(0.0, coherence))
    
    def magnetism_stability(self) -> float:
        """
        Variance in magnetism values - lower is more stable.
        Returns 0-1 where 1 = perfectly stable.
        """
        if not self.magnetism_states:
            return 0.5
        
        magnetism_values = [
            state.get('curiosity_magnetism', 0.5) 
            for state in self.magnetism_states.values()
        ]
        if len(magnetism_values) < 2:
            return 0.5
        
        mean_mag = sum(magnetism_values) / len(magnetism_values)
        variance = sum((m - mean_mag) ** 2 for m in magnetism_values) / len(magnetism_values)
        return 1.0 / (1.0 + variance * 10)


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
    vocabulary_words: List[str] = field(default_factory=list)  # RESTORED: Full vocabulary inheritance
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAGNETISM INHERITANCE - Attractor landscape from parents
    # ═══════════════════════════════════════════════════════════════════════════
    magnetism_template: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {concept_id: {base_magnetism, curiosity_magnetism, outcome_history}}
    association_template: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # {concept_id: {target_id: strength}}
    
    # Birth phenotype classification
    birth_phenotype: str = "unknown"  # "healed", "numb", or "trapped"
    coherence_at_birth: float = 0.0
    
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
    
    Population-Correlated Germination:
    - Tracks board state (population fitness distribution, network topology)
    - Spawns challengers calibrated to current population strength
    - Uses historical organism states to create less-developed variants
    - Maintains evolutionary pressure without overwhelming/underwhelming
    """
    
    def __init__(
        self,
        causation_explorer: Optional[Any] = None,
        max_genetic_samples: int = 100,
        min_population: int = 5,
        max_population: int = 50,
        germination_rate: float = 0.1,
        mutation_base_rate: float = 0.05,
        crossover_bias: float = 0.3,
        context_memory: Optional[Any] = None  # For vocabulary extraction
    ):
        self.causation_explorer = causation_explorer
        self.context_memory = context_memory  # For extracting organism vocabularies
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
        # ═══════════════════════════════════════════════════════════════════════════
        # CHIMERA @ 100% - Bonds persist across death
        # Healed organisms encode fixed-point attractors that offspring inherit
        # "Make survival heritable"
        # ═══════════════════════════════════════════════════════════════════════════
        self.strategy_weights = {
            GerminationStrategy.CLONE: 0.0,
            GerminationStrategy.CROSSOVER: 0.25,    # 25% - Structural novelty
            GerminationStrategy.CHIMERA: 0.40,      # 40% - Multi-parent blending (powerful, not dominant)
            GerminationStrategy.NOVA: 0.18,         # 18% - Fresh genetic material
            GerminationStrategy.PHOENIX: 0.0,
            GerminationStrategy.HYBRID: 0.0,
            GerminationStrategy.REGRESSED: 0.0,
            GerminationStrategy.CALIBRATED: 0.17   # 17% - Targeted variations
        }
        
        # Champion capsules for phoenix resurrection
        self.champion_capsules: List[Any] = []
        
        # ═══════════════════════════════════════════════════════════════
        # POPULATION STATE TRACKING (Board Correlation)
        # ═══════════════════════════════════════════════════════════════
        self.population_state_history: List[Dict[str, Any]] = []
        self.max_state_history = 100  # Keep last 100 population snapshots
        
        # Historical organism snapshots for regression strategy
        self.historical_snapshots: Dict[str, List[Dict[str, Any]]] = {}  # organism_id -> [snapshots]
        self.max_snapshots_per_organism = 10
        
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
            
        # Extract vocabulary - try multiple sources
        vocab_words = []
        if hasattr(organism, 'vocabulary') and organism.vocabulary:
            vocab = organism.vocabulary
            if hasattr(vocab, 'get_all_words'):
                vocab_words = list(vocab.get_all_words())
            elif hasattr(vocab, 'word_to_id'):
                vocab_words = list(vocab.word_to_id.keys())
        
        # Also check for inherited vocabulary from previous resurrection
        if hasattr(organism, '_inherited_vocabulary') and organism._inherited_vocabulary:
            vocab_words = list(set(vocab_words) | set(organism._inherited_vocabulary))
        
        # Check context_memory for this organism's words (primary source)
        if hasattr(self, 'context_memory') and self.context_memory:
            org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
            if hasattr(self.context_memory, 'node_word_associations'):
                org_words = self.context_memory.node_word_associations.get(org_id_int, set())
                if org_words:
                    vocab_words = list(set(vocab_words) | set(org_words))
        
        material.vocabulary_sample = vocab_words  # FULL vocab - they earned it
                
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
        
        # ═══════════════════════════════════════════════════════════════════════════
        # EXTRACT MAGNETISM - Bonds that persist across death
        # Healed organisms encode their fixed-point attractor in magnetism
        # ═══════════════════════════════════════════════════════════════════════════
        if hasattr(organism, 'linguistic_atoms') and organism.linguistic_atoms:
            lang_system = organism.linguistic_atoms
            if hasattr(lang_system, 'atoms'):
                for concept_id, atom in lang_system.atoms.items():
                    # Extract magnetism state
                    material.magnetism_states[concept_id] = {
                        'base_magnetism': getattr(atom, 'base_magnetism', 0.5),
                        'curiosity_magnetism': getattr(atom, 'curiosity_magnetism', 0.5),
                        'outcome_history': getattr(atom, 'outcome_history', [])[-10:],
                        'satiation_level': getattr(atom, 'satiation_level', 0.0),
                        'strength': getattr(atom, 'strength', 0.5)
                    }
                    # Extract association strengths
                    if hasattr(atom, 'associations') and atom.associations:
                        material.association_strengths[concept_id] = {
                            target: assoc.strength 
                            for target, assoc in atom.associations.items()
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
    
    # ═══════════════════════════════════════════════════════════════
    # POPULATION STATE TRACKING (Board Correlation)
    # ═══════════════════════════════════════════════════════════════
    
    def update_population_state(self, organisms: List[Any]) -> Dict[str, Any]:
        """
        Snapshot current population state for calibration.
        
        Called periodically to track board state - this is the DATABASE
        that germination correlates against, not any one organism.
        
        Returns the computed population state.
        """
        if not organisms:
            return {}
            
        # Compute population statistics
        fitness_values = []
        ages = []
        concept_counts = []
        battle_records = []
        
        for org in organisms:
            # Fitness
            if hasattr(org, 'fitness'):
                fitness_values.append(org.fitness)
            elif hasattr(org, 'calculate_fitness'):
                fitness_values.append(org.calculate_fitness())
            
            # Age
            if hasattr(org, 'age'):
                ages.append(org.age)
            
            # Concept richness
            if hasattr(org, 'concepts'):
                concept_counts.append(len(org.concepts))
            elif hasattr(org, 'atomic_language') and org.atomic_language:
                concept_counts.append(len(org.atomic_language.atoms))
            
            # Battle record
            wins = getattr(org, 'victories', 0)
            losses = getattr(org, 'defeats', 0)
            if wins + losses > 0:
                battle_records.append(wins / (wins + losses))
        
        # Build state snapshot
        state = {
            'timestamp': time.time(),
            'population_size': len(organisms),
            'generation': self.generation_counter,
            
            # Fitness distribution
            'avg_fitness': sum(fitness_values) / len(fitness_values) if fitness_values else 0.5,
            'max_fitness': max(fitness_values) if fitness_values else 0.5,
            'min_fitness': min(fitness_values) if fitness_values else 0.5,
            'fitness_std': self._std(fitness_values) if fitness_values else 0.0,
            
            # Developmental distribution
            'avg_age': sum(ages) / len(ages) if ages else 0.0,
            'max_age': max(ages) if ages else 0.0,
            
            # Conceptual richness
            'avg_concepts': sum(concept_counts) / len(concept_counts) if concept_counts else 0.0,
            
            # Battle competitiveness
            'avg_win_rate': sum(battle_records) / len(battle_records) if battle_records else 0.5
        }
        
        # Track history
        self.population_state_history.append(state)
        if len(self.population_state_history) > self.max_state_history:
            self.population_state_history = self.population_state_history[-self.max_state_history:]
        
        return state
    
    def _std(self, values: List[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def snapshot_organism(self, organism: Any, developmental_stage: float = None):
        """
        Take a developmental snapshot of an organism.
        
        These snapshots are used by REGRESSED strategy to resurrect
        organisms at earlier developmental states.
        
        Args:
            organism: The organism to snapshot
            developmental_stage: 0.0=newborn to 1.0=mature (auto-computed if None)
        """
        org_id = getattr(organism, 'id', str(id(organism)))
        
        # Compute developmental stage if not provided
        if developmental_stage is None:
            age = getattr(organism, 'age', 0)
            max_expected_age = 1000  # Normalize against expected lifespan
            developmental_stage = min(1.0, age / max_expected_age)
        
        snapshot = {
            'timestamp': time.time(),
            'developmental_stage': developmental_stage,
            'age': getattr(organism, 'age', 0),
            'fitness': getattr(organism, 'fitness', 0.5),
            'neural_weights': None,
            'concepts': {},
            'traits': {},
            'config': {},
            'magnetism_states': {},      # Attractor landscape
            'association_strengths': {}  # Knowledge web
        }
        
        # Capture neural state
        if hasattr(organism, 'neural_layer') and organism.neural_layer:
            try:
                snapshot['neural_weights'] = organism.neural_layer.get_state()
            except Exception:
                pass
        
        # Capture concepts
        if hasattr(organism, 'concepts'):
            snapshot['concepts'] = dict(organism.concepts)
        elif hasattr(organism, 'atomic_language') and organism.atomic_language:
            snapshot['concepts'] = {c: a.strength for c, a in organism.atomic_language.atoms.items()}
        
        # Capture traits
        if hasattr(organism, 'traits'):
            snapshot['traits'] = dict(organism.traits)
        
        # Capture config
        if hasattr(organism, 'config'):
            snapshot['config'] = dict(organism.config)
        
        # CAPTURE MAGNETISM - Bonds that persist across death
        if hasattr(organism, 'linguistic_atoms') and organism.linguistic_atoms:
            lang_system = organism.linguistic_atoms
            if hasattr(lang_system, 'atoms'):
                for concept_id, atom in lang_system.atoms.items():
                    snapshot['magnetism_states'][concept_id] = {
                        'base_magnetism': getattr(atom, 'base_magnetism', 0.5),
                        'curiosity_magnetism': getattr(atom, 'curiosity_magnetism', 0.5),
                        'outcome_history': getattr(atom, 'outcome_history', [])[-10:],
                        'satiation_level': getattr(atom, 'satiation_level', 0.0),
                        'strength': getattr(atom, 'strength', 0.5)
                    }
                    if hasattr(atom, 'associations') and atom.associations:
                        snapshot['association_strengths'][concept_id] = {
                            target: assoc.strength 
                            for target, assoc in atom.associations.items()
                        }
        
        # Store
        if org_id not in self.historical_snapshots:
            self.historical_snapshots[org_id] = []
        
        self.historical_snapshots[org_id].append(snapshot)
        
        # Prune old snapshots
        if len(self.historical_snapshots[org_id]) > self.max_snapshots_per_organism:
            self.historical_snapshots[org_id] = self.historical_snapshots[org_id][-self.max_snapshots_per_organism:]
    
    def get_regressed_snapshot(self, target_stage: float = 0.3) -> Optional[Dict[str, Any]]:
        """
        Find a historical snapshot at approximately the target developmental stage.
        
        Args:
            target_stage: Desired developmental stage (0.0-1.0)
            
        Returns:
            Historical snapshot closest to target stage, or None
        """
        best_snapshot = None
        best_distance = float('inf')
        
        for org_id, snapshots in self.historical_snapshots.items():
            for snap in snapshots:
                stage = snap.get('developmental_stage', 1.0)
                distance = abs(stage - target_stage)
                if distance < best_distance:
                    best_distance = distance
                    best_snapshot = snap
        
        return best_snapshot
    
    def get_calibration_target(self) -> Dict[str, float]:
        """
        Get target parameters for population-calibrated germination.
        
        This looks at the CURRENT BOARD STATE to determine what kind
        of challengers should be spawned:
        - If population is strong: spawn slightly weaker (fair challenge)
        - If population is weak: spawn at similar level (competitive)
        - If population is stagnant: spawn with novel traits (innovation)
        """
        if not self.population_state_history:
            return {'fitness_target': 0.5, 'mutation_boost': 0.0, 'vigor_modifier': 1.0}
        
        current = self.population_state_history[-1]
        
        # Compare to historical average
        if len(self.population_state_history) >= 5:
            recent_avg = sum(
                s['avg_fitness'] for s in self.population_state_history[-5:]
            ) / 5
        else:
            recent_avg = current['avg_fitness']
        
        # Fitness trend detection
        fitness_trend = current['avg_fitness'] - recent_avg
        
        # Stagnation detection
        if len(self.population_state_history) >= 10:
            fitness_variance = self._std([s['avg_fitness'] for s in self.population_state_history[-10:]])
            is_stagnant = fitness_variance < 0.05
        else:
            is_stagnant = False
        
        # Calibration logic
        if current['avg_fitness'] > 0.7:
            # Strong population - spawn slightly weaker challengers
            fitness_target = current['avg_fitness'] * 0.8
            vigor_modifier = 0.9
            mutation_boost = 0.0
        elif current['avg_fitness'] < 0.3:
            # Weak population - spawn at similar level
            fitness_target = current['avg_fitness']
            vigor_modifier = 1.0
            mutation_boost = 0.05
        else:
            # Normal population
            fitness_target = current['avg_fitness'] * 0.9
            vigor_modifier = 1.0
            mutation_boost = 0.0
        
        # Stagnation override - introduce novelty
        if is_stagnant:
            mutation_boost = 0.15
            vigor_modifier = 1.1
        
        return {
            'fitness_target': fitness_target,
            'mutation_boost': mutation_boost,
            'vigor_modifier': vigor_modifier,
            'is_stagnant': is_stagnant,
            'current_avg_fitness': current['avg_fitness'],
            'fitness_trend': fitness_trend
        }
                
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
        elif strategy == GerminationStrategy.REGRESSED:
            self._apply_regressed_strategy(candidate)
        elif strategy == GerminationStrategy.CALIBRATED:
            self._apply_calibrated_strategy(candidate)
            
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
        candidate.vocabulary_words = list(parent.vocabulary_sample)  # FULL vocab inheritance
        
        # MAGNETISM INHERITANCE - Clone gets parent's attractor landscape
        candidate.magnetism_template = dict(parent.magnetism_states)
        candidate.association_template = dict(parent.association_strengths)
        
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
        
        # Crossover vocabulary (union of both parents' words)
        vocab_union = set(parent1.vocabulary_sample) | set(parent2.vocabulary_sample)
        candidate.vocabulary_words = list(vocab_union)
        
        # MAGNETISM INHERITANCE - Crossover gets simple union (chimera does weighted merge)
        merged_magnetism = {}
        merged_magnetism.update(parent1.magnetism_states)
        merged_magnetism.update(parent2.magnetism_states)  # parent2 overwrites conflicts
        candidate.magnetism_template = merged_magnetism
        
        merged_associations = {}
        merged_associations.update(parent1.association_strengths)
        merged_associations.update(parent2.association_strengths)
        candidate.association_template = merged_associations
        
        candidate.mutation_rate = 0.1
        candidate.ancestry_depth = max(
            getattr(parent1, 'ancestry_depth', 0),
            getattr(parent2, 'ancestry_depth', 0)
        ) + 1
        
    def _apply_chimera_strategy(self, candidate: GerminationCandidate):
        """
        ═══════════════════════════════════════════════════════════════════════════
        CHIMERA @ 100% - Bonds Persist Across Death
        
        Parent Selection: highest_fitness + semantic_coherence
        State Merge: weighted_average(fitness_score, magnetism_stability, vocab_overlap)
        Semantic Inheritance:
          - linguistic_knowledge_web: merge_both_parents
          - concept_associations: average_strength  
          - learned_words: union_with_parent_weighting
        Phenotype Blend:
          - curiosity: geometric_mean(parent_a, parent_b)
          - traits: element_wise_average
          - development_stage: max(parents)
        
        Output:
          - log_coherence_before: true
          - log_coherence_after: true
          - track_healed_vs_trapped: true
        ═══════════════════════════════════════════════════════════════════════════
        """
        import math
        import logging
        logger = logging.getLogger(__name__)
        
        # Need at least 2 donors for chimera
        if len(self.genetic_pool) < 2:
            self._apply_nova_strategy(candidate)
            return
        
        # ═══════════════════════════════════════════════════════════════════════
        # PARENT SELECTION: highest_fitness + semantic_coherence
        # ═══════════════════════════════════════════════════════════════════════
        pool_items = list(self.genetic_pool.items())
        
        # Calculate combined score for each donor
        scored_donors = []
        for donor_id, donor in pool_items:
            fitness = donor.fitness_score()
            coherence = donor.semantic_coherence()
            # Combined score: 60% fitness, 40% coherence
            combined_score = (fitness * 0.6) + (coherence * 0.4)
            scored_donors.append((donor_id, donor, combined_score, fitness, coherence))
        
        # Sort by combined score, take top 2
        scored_donors.sort(key=lambda x: x[2], reverse=True)
        parent1_id, parent1, score1, fit1, coh1 = scored_donors[0]
        parent2_id, parent2, score2, fit2, coh2 = scored_donors[1] if len(scored_donors) > 1 else scored_donors[0]
        
        candidate.parent_ids = [parent1_id, parent2_id]
        
        # ═══════════════════════════════════════════════════════════════════════
        # HEALING PROTOCOL: Check if parents are trapped, clean before inheritance
        # "trapped" parents have high oscillation - we don't want to pass that on
        # ═══════════════════════════════════════════════════════════════════════
        parent1_trapped = coh1 < 0.5  # Low coherence = trapped/oscillating
        parent2_trapped = coh2 < 0.5
        trapped_filter_active = parent1_trapped or parent2_trapped
        
        if trapped_filter_active:
            # Log warning about trapped parents
            trapped_info = []
            if parent1_trapped:
                trapped_info.append(f"{parent1_id[:8]}(coh={coh1:.2f})")
            if parent2_trapped:
                trapped_info.append(f"{parent2_id[:8]}(coh={coh2:.2f})")
            logger.info(f"[CHIMERA] ⚠️ TRAPPED PARENTS detected: {', '.join(trapped_info)} - applying healing filter")
        
        # Log coherence BEFORE merge
        logger.info(f"[CHIMERA] Parent selection: {parent1_id[:8]}(fit={fit1:.2f},coh={coh1:.2f}) + {parent2_id[:8]}(fit={fit2:.2f},coh={coh2:.2f})")
        
        # ═══════════════════════════════════════════════════════════════════════
        # STATE MERGE: weighted_average by fitness, magnetism_stability, vocab_overlap
        # ═══════════════════════════════════════════════════════════════════════
        
        # Calculate weights for each parent
        p1_fitness = parent1.fitness_score()
        p2_fitness = parent2.fitness_score()
        p1_stability = parent1.magnetism_stability()
        p2_stability = parent2.magnetism_stability()
        
        # Vocabulary contribution - how much does each parent bring?
        vocab1 = set(parent1.vocabulary_sample)
        vocab2 = set(parent2.vocabulary_sample)
        union_size = len(vocab1 | vocab2)
        p1_vocab_contribution = len(vocab1) / max(1, union_size)
        p2_vocab_contribution = len(vocab2) / max(1, union_size)
        
        # Parent weights: fitness(40%) + stability(40%) + vocab_contribution(20%)
        p1_weight = (p1_fitness * 0.4) + (p1_stability * 0.4) + (p1_vocab_contribution * 0.2)
        p2_weight = (p2_fitness * 0.4) + (p2_stability * 0.4) + (p2_vocab_contribution * 0.2)
        total_weight = p1_weight + p2_weight
        
        w1 = p1_weight / total_weight if total_weight > 0 else 0.5
        w2 = p2_weight / total_weight if total_weight > 0 else 0.5
        
        # ═══════════════════════════════════════════════════════════════════════
        # NEURAL: Take from higher-fitness parent (neural weights are fragile)
        # ═══════════════════════════════════════════════════════════════════════
        best_neural_parent = parent1 if p1_fitness >= p2_fitness else parent2
        candidate.neural_template = dict(best_neural_parent.neural_weights or {})
        
        # ═══════════════════════════════════════════════════════════════════════
        # SEMANTIC INHERITANCE: merge_both_parents
        # ═══════════════════════════════════════════════════════════════════════
        
        # 1. Vocabulary: union_with_parent_weighting
        all_vocab = vocab1 | vocab2
        candidate.vocabulary_words = list(all_vocab)
        
        # 2. Concepts: merge both
        merged_concepts = {}
        merged_concepts.update(parent1.concepts)
        merged_concepts.update(parent2.concepts)
        candidate.concept_seed = merged_concepts
        
        # 3. MAGNETISM: weighted average of both parents' attractor landscapes
        merged_magnetism = {}
        all_concept_ids = set(parent1.magnetism_states.keys()) | set(parent2.magnetism_states.keys())
        
        for concept_id in all_concept_ids:
            state1 = parent1.magnetism_states.get(concept_id, {})
            state2 = parent2.magnetism_states.get(concept_id, {})
            
            # Weighted average of magnetism values
            base_mag = (
                state1.get('base_magnetism', 0.5) * w1 +
                state2.get('base_magnetism', 0.5) * w2
            )
            curiosity_mag = (
                state1.get('curiosity_magnetism', 0.5) * w1 +
                state2.get('curiosity_magnetism', 0.5) * w2
            )
            strength = (
                state1.get('strength', 0.5) * w1 +
                state2.get('strength', 0.5) * w2
            )
            
            # Merge outcome histories (interleave, recent bias)
            hist1 = state1.get('outcome_history', [])
            hist2 = state2.get('outcome_history', [])
            # Interleave with bias toward better parent
            merged_history = []
            for i in range(max(len(hist1), len(hist2))):
                if i < len(hist1):
                    merged_history.append(hist1[i])
                if i < len(hist2):
                    merged_history.append(hist2[i])
            merged_history = merged_history[-10:]  # Keep last 10
            
            # ═══════════════════════════════════════════════════════════════════
            # HEALING FILTER: Skip highly oscillating states from trapped parents
            # "vulnerability spreads faster than strength" - don't inherit the trap
            # ═══════════════════════════════════════════════════════════════════
            skip_concept = False
            if trapped_filter_active:
                # Check if this concept's magnetism was oscillating in either parent
                state1_variance = 0.0
                state2_variance = 0.0
                if state1.get('outcome_history'):
                    hist = state1['outcome_history']
                    if len(hist) >= 3:
                        mean_h = sum(hist) / len(hist)
                        state1_variance = sum((h - mean_h) ** 2 for h in hist) / len(hist)
                if state2.get('outcome_history'):
                    hist = state2['outcome_history']
                    if len(hist) >= 3:
                        mean_h = sum(hist) / len(hist)
                        state2_variance = sum((h - mean_h) ** 2 for h in hist) / len(hist)
                
                # High variance = oscillating = skip from trapped parent's contribution
                if parent1_trapped and state1_variance > 0.3:
                    # Don't trust parent1's state for this concept
                    base_mag = state2.get('base_magnetism', 0.5)
                    curiosity_mag = state2.get('curiosity_magnetism', 0.5)
                    strength = state2.get('strength', 0.5)
                    merged_history = state2.get('outcome_history', [])[-10:]
                if parent2_trapped and state2_variance > 0.3:
                    # Don't trust parent2's state for this concept
                    base_mag = state1.get('base_magnetism', 0.5)
                    curiosity_mag = state1.get('curiosity_magnetism', 0.5)
                    strength = state1.get('strength', 0.5)
                    merged_history = state1.get('outcome_history', [])[-10:]
            
            merged_magnetism[concept_id] = {
                'base_magnetism': base_mag,
                'curiosity_magnetism': curiosity_mag,
                'outcome_history': merged_history,
                'satiation_level': 0.0,  # Fresh start on satiation
                'strength': strength
            }
        
        candidate.magnetism_template = merged_magnetism
        
        # 4. ASSOCIATIONS: average_strength
        merged_associations = {}
        all_source_concepts = set(parent1.association_strengths.keys()) | set(parent2.association_strengths.keys())
        
        for source_id in all_source_concepts:
            assoc1 = parent1.association_strengths.get(source_id, {})
            assoc2 = parent2.association_strengths.get(source_id, {})
            all_targets = set(assoc1.keys()) | set(assoc2.keys())
            
            merged_associations[source_id] = {}
            for target_id in all_targets:
                str1 = assoc1.get(target_id, 0.0)
                str2 = assoc2.get(target_id, 0.0)
                # Weighted average
                merged_associations[source_id][target_id] = str1 * w1 + str2 * w2
        
        candidate.association_template = merged_associations
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHENOTYPE BLEND
        # ═══════════════════════════════════════════════════════════════════════
        
        # 1. Curiosity: geometric_mean(parent_a, parent_b)
        p1_curiosity = parent1.traits.get('curiosity', parent1.traits.get('adaptability', 0.5))
        p2_curiosity = parent2.traits.get('curiosity', parent2.traits.get('adaptability', 0.5))
        geometric_curiosity = math.sqrt(max(0.01, p1_curiosity) * max(0.01, p2_curiosity))
        
        # 2. Traits: element_wise_average
        blended_traits = {}
        all_trait_names = set(parent1.traits.keys()) | set(parent2.traits.keys())
        for trait_name in all_trait_names:
            t1 = parent1.traits.get(trait_name, 0.5)
            t2 = parent2.traits.get(trait_name, 0.5)
            blended_traits[trait_name] = (t1 + t2) / 2.0
        
        # Override curiosity with geometric mean
        blended_traits['curiosity'] = geometric_curiosity
        blended_traits['adaptability'] = geometric_curiosity  # Sync both
        
        candidate.trait_template = blended_traits
        
        # 3. Development stage: max(parents)
        p1_stage = parent1.developmental_stage
        p2_stage = parent2.developmental_stage
        max_stage = max(p1_stage, p2_stage)
        
        # Blend configs
        blended_config = {}
        for key in set(parent1.config_atoms.keys()) | set(parent2.config_atoms.keys()):
            v1 = parent1.config_atoms.get(key)
            v2 = parent2.config_atoms.get(key)
            if v1 is not None and v2 is not None:
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    blended_config[key] = v1 * w1 + v2 * w2
                else:
                    blended_config[key] = v1 if w1 >= w2 else v2
            else:
                blended_config[key] = v1 if v1 is not None else v2
        candidate.config_template = blended_config
        
        # ═══════════════════════════════════════════════════════════════════════
        # BIRTH PHENOTYPE CLASSIFICATION: healed / numb / trapped
        # ═══════════════════════════════════════════════════════════════════════
        
        # Calculate coherence of the merged state
        if merged_magnetism:
            magnetism_values = [s.get('curiosity_magnetism', 0.5) for s in merged_magnetism.values()]
            mean_mag = sum(magnetism_values) / len(magnetism_values) if magnetism_values else 0.5
            variance = sum((m - mean_mag) ** 2 for m in magnetism_values) / max(1, len(magnetism_values))
            stability = 1.0 / (1.0 + variance * 10)
            
            # Count positive outcomes in merged history
            positive_count = 0
            total_count = 0
            for state in merged_magnetism.values():
                for outcome in state.get('outcome_history', []):
                    total_count += 1
                    if outcome > 0:
                        positive_count += 1
            positivity = positive_count / max(1, total_count)
            
            coherence_after = stability * 0.6 + positivity * 0.4
        else:
            coherence_after = 0.5
        
        candidate.coherence_at_birth = coherence_after
        
        # Classify phenotype
        # healed: high coherence (>0.7) + high mean magnetism (stable +1)
        # numb: high coherence (>0.7) + low mean magnetism (stable 0)  
        # trapped: low coherence (<0.5) (oscillating)
        if coherence_after >= 0.7:
            if merged_magnetism:
                mean_mag = sum(s.get('curiosity_magnetism', 0.5) for s in merged_magnetism.values()) / len(merged_magnetism)
            else:
                mean_mag = 0.5
            if mean_mag >= 0.6:
                candidate.birth_phenotype = "healed"
            else:
                candidate.birth_phenotype = "numb"
        elif coherence_after < 0.5:
            candidate.birth_phenotype = "trapped"
        else:
            candidate.birth_phenotype = "drifting"  # In between
        
        # Low mutation for chimera - inheritance is the point
        candidate.mutation_rate = 0.05
        candidate.ancestry_depth = max(
            getattr(parent1, 'ancestry_depth', 0),
            getattr(parent2, 'ancestry_depth', 0)
        ) + 1
        
        # Log coherence AFTER merge
        logger.info(
            f"[CHIMERA] Birth: {candidate.candidate_id[:8]} "
            f"phenotype={candidate.birth_phenotype} "
            f"coherence={coherence_after:.2f} "
            f"vocab={len(candidate.vocabulary_words)} "
            f"magnetism_concepts={len(merged_magnetism)}"
        )
        
        # Emit causation event
        self._emit_event('chimera_birth', {
            'candidate_id': candidate.candidate_id,
            'parent_ids': candidate.parent_ids,
            'birth_phenotype': candidate.birth_phenotype,
            'coherence_at_birth': coherence_after,
            'vocabulary_size': len(candidate.vocabulary_words),
            'magnetism_concepts': len(merged_magnetism),
            'parent1_fitness': fit1,
            'parent1_coherence': coh1,
            'parent2_fitness': fit2,
            'parent2_coherence': coh2
        })
        
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
        # RESTORE VOCABULARY: Phoenix rises with ALL their words
        if hasattr(capsule, 'vocabulary_words'):
            candidate.vocabulary_words = list(capsule.vocabulary_words)
        elif hasattr(capsule, 'vocabulary_sample'):
            candidate.vocabulary_words = list(capsule.vocabulary_sample)
        
        # RESTORE MAGNETISM: Phoenix rises with attractor landscape intact
        if hasattr(capsule, 'magnetism_states'):
            candidate.magnetism_template = dict(capsule.magnetism_states)
        if hasattr(capsule, 'association_strengths'):
            candidate.association_template = dict(capsule.association_strengths)
            
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
    
    def _apply_regressed_strategy(self, candidate: GerminationCandidate):
        """
        Create organism from an earlier developmental state.
        
        This uses historical snapshots to resurrect organisms at
        LESS DEVELOPED stages - younger, weaker versions that must
        fight their way up again.
        
        "What if this champion had to start over from age 100?"
        """
        # Determine target developmental stage based on population state
        calibration = self.get_calibration_target()
        
        if calibration.get('current_avg_fitness', 0.5) > 0.6:
            # Strong population - use earlier snapshot (more challenge)
            target_stage = 0.2  # Very early development
        elif calibration.get('is_stagnant', False):
            # Stagnant - use mid-development for fresh blood
            target_stage = 0.4
        else:
            # Normal - use mid-development
            target_stage = 0.3
        
        snapshot = self.get_regressed_snapshot(target_stage)
        
        if not snapshot:
            # No snapshots available, fall back to nova
            self._apply_nova_strategy(candidate)
            return
        
        candidate.parent_ids = [f"regressed_from_snapshot"]
        
        # Restore from historical snapshot
        if snapshot.get('neural_weights'):
            candidate.neural_template = dict(snapshot['neural_weights'])
        
        if snapshot.get('concepts'):
            candidate.concept_seed = dict(snapshot['concepts'])
        
        if snapshot.get('config'):
            candidate.config_template = dict(snapshot['config'])
        
        if snapshot.get('traits'):
            candidate.trait_template = dict(snapshot['traits'])
        else:
            # Default traits for young organism
            candidate.trait_template = {
                'aggression': 0.3 + random.random() * 0.2,
                'cooperation': 0.4 + random.random() * 0.2,
                'adaptability': 0.5 + random.random() * 0.3,  # Young = adaptable
                'resilience': 0.3 + random.random() * 0.2,
                'innovation': 0.5 + random.random() * 0.3    # Young = innovative
            }
        
        # MAGNETISM INHERITANCE from snapshot
        if snapshot.get('magnetism_states'):
            candidate.magnetism_template = dict(snapshot['magnetism_states'])
        if snapshot.get('association_strengths'):
            candidate.association_template = dict(snapshot['association_strengths'])
        
        # Regressed organisms need room to grow
        candidate.mutation_rate = 0.08
        candidate.vigor = 0.8  # Slightly weaker (younger)
        candidate.ancestry_depth = 0  # Fresh start
        
        self._emit_event('regressed_germination', {
            'target_stage': target_stage,
            'actual_stage': snapshot.get('developmental_stage', 'unknown'),
            'snapshot_age': snapshot.get('age', 0)
        })
    
    def _apply_calibrated_strategy(self, candidate: GerminationCandidate):
        """
        Create organism calibrated to current POPULATION STATE.
        
        This is the key population-correlated strategy:
        - Reads the BOARD STATE (population fitness distribution)
        - Creates challengers tuned to be competitive but not overwhelming
        - Adapts based on population health and trends
        
        "The tournament spawns challengers matched to the competition level."
        """
        calibration = self.get_calibration_target()
        
        # Use elite material as base, then calibrate
        if self.elite_samples:
            parent_id = random.choice(self.elite_samples)
            parent = self.genetic_pool.get(parent_id)
            
            if parent:
                candidate.parent_ids = [parent_id]
                candidate.neural_template = dict(parent.neural_weights or {})
                candidate.concept_seed = dict(parent.concepts)
                candidate.config_template = dict(parent.config_atoms)
                candidate.trait_template = dict(parent.traits)
                # MAGNETISM INHERITANCE
                candidate.magnetism_template = dict(parent.magnetism_states)
                candidate.association_template = dict(parent.association_strengths)
        else:
            # No elites, start from scratch
            candidate.parent_ids = []
            candidate.trait_template = {
                'aggression': 0.5,
                'cooperation': 0.5,
                'adaptability': 0.5,
                'resilience': 0.5,
                'innovation': 0.5
            }
        
        # Apply calibration adjustments
        fitness_target = calibration.get('fitness_target', 0.5)
        current_fitness = calibration.get('current_avg_fitness', 0.5)
        
        # Scale traits to approximate fitness target
        fitness_ratio = fitness_target / max(0.1, current_fitness)
        for trait in candidate.trait_template:
            scaled = candidate.trait_template[trait] * fitness_ratio
            # Add noise to prevent exact clones
            scaled += random.gauss(0, 0.1)
            candidate.trait_template[trait] = max(0.0, min(1.0, scaled))
        
        # Apply calibration modifiers
        candidate.mutation_rate = 0.05 + calibration.get('mutation_boost', 0.0)
        candidate.vigor = calibration.get('vigor_modifier', 1.0)
        
        # If stagnant, inject more novelty into concepts
        if calibration.get('is_stagnant', False):
            # Add some random concepts
            novel_concepts = ['adapt', 'evolve', 'transform', 'overcome', 'emerge']
            for concept in random.sample(novel_concepts, k=min(2, len(novel_concepts))):
                candidate.concept_seed[concept] = {'strength': random.random()}
        
        self._emit_event('calibrated_germination', {
            'fitness_target': fitness_target,
            'current_avg_fitness': current_fitness,
            'vigor': candidate.vigor,
            'is_stagnant': calibration.get('is_stagnant', False),
            'fitness_trend': calibration.get('fitness_trend', 0)
        })

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
            
            # RESTORE VOCABULARY: Give them back ALL their words
            if candidate.vocabulary_words:
                if hasattr(organism, 'vocabulary') and organism.vocabulary:
                    for word in candidate.vocabulary_words:
                        try:
                            organism.vocabulary.add_word(word)
                        except Exception:
                            pass  # Word might already exist
                # Also store for context_memory linking later
                organism._inherited_vocabulary = candidate.vocabulary_words
            
            # ═══════════════════════════════════════════════════════════════════════
            # APPLY MAGNETISM TEMPLATE - Inherited attractor landscape
            # "Build bonds that persist across death"
            # ═══════════════════════════════════════════════════════════════════════
            if candidate.magnetism_template and hasattr(organism, 'linguistic_atoms'):
                lang_system = organism.linguistic_atoms
                if hasattr(lang_system, 'atoms'):
                    for concept_id, mag_state in candidate.magnetism_template.items():
                        if concept_id in lang_system.atoms:
                            atom = lang_system.atoms[concept_id]
                            # Apply inherited magnetism
                            atom.base_magnetism = mag_state.get('base_magnetism', atom.base_magnetism)
                            atom.curiosity_magnetism = mag_state.get('curiosity_magnetism', atom.curiosity_magnetism)
                            atom.outcome_history = mag_state.get('outcome_history', [])
                            atom.satiation_level = mag_state.get('satiation_level', 0.0)
                            if 'strength' in mag_state:
                                atom.strength = mag_state['strength']
                        else:
                            # Create new atom with inherited magnetism
                            try:
                                from reality_simulator.language.atomic_language import LinguisticAtom
                                new_atom = LinguisticAtom(
                                    concept_id=concept_id,
                                    strength=mag_state.get('strength', 0.5),
                                    source='inherited',
                                    base_magnetism=mag_state.get('base_magnetism', 0.5),
                                    curiosity_magnetism=mag_state.get('curiosity_magnetism', 0.5)
                                )
                                new_atom.outcome_history = mag_state.get('outcome_history', [])
                                # Wire event emitter from parent system
                                new_atom._event_emitter = getattr(lang_system, '_event_emitter', None)
                                new_atom._organism_id = getattr(lang_system, 'organism_id', None)
                                lang_system.atoms[concept_id] = new_atom
                            except ImportError:
                                pass
            
            # Apply inherited associations
            if candidate.association_template and hasattr(organism, 'linguistic_atoms'):
                lang_system = organism.linguistic_atoms
                if hasattr(lang_system, 'atoms'):
                    for source_id, targets in candidate.association_template.items():
                        if source_id in lang_system.atoms:
                            atom = lang_system.atoms[source_id]
                            if hasattr(atom, 'associations'):
                                for target_id, strength in targets.items():
                                    if target_id in atom.associations:
                                        atom.associations[target_id].strength = strength
                                    else:
                                        try:
                                            from reality_simulator.language.atomic_language import ConceptAssociation
                                            atom.associations[target_id] = ConceptAssociation(
                                                target_concept=target_id,
                                                strength=strength,
                                                formation_reason='inherited'
                                            )
                                        except ImportError:
                                            pass
            
            # Store birth phenotype for tracking
            if hasattr(candidate, 'birth_phenotype'):
                organism._birth_phenotype = candidate.birth_phenotype
                organism._coherence_at_birth = candidate.coherence_at_birth
                
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
                'total_germinated': self.total_germinated,
                # CHIMERA tracking
                'birth_phenotype': getattr(candidate, 'birth_phenotype', 'unknown'),
                'coherence_at_birth': getattr(candidate, 'coherence_at_birth', 0.0),
                'magnetism_concepts_inherited': len(getattr(candidate, 'magnetism_template', {})),
                'vocabulary_inherited': len(candidate.vocabulary_words)
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
        
        # Get calibration target for current board state
        calibration = self.get_calibration_target()
        
        # Count historical snapshots
        total_snapshots = sum(len(snaps) for snaps in self.historical_snapshots.values())
        
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
            'strategy_weights': {s.value: w for s, w in self.strategy_weights.items()},
            # Population correlation stats
            'population_state_history_size': len(self.population_state_history),
            'historical_snapshots': total_snapshots,
            'organisms_with_snapshots': len(self.historical_snapshots),
            # Current calibration state
            'calibration': {
                'fitness_target': calibration.get('fitness_target', 0.5),
                'current_avg_fitness': calibration.get('current_avg_fitness', 0.5),
                'is_stagnant': calibration.get('is_stagnant', False),
                'vigor_modifier': calibration.get('vigor_modifier', 1.0)
            }
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
    organism_factory: Callable[..., Any],
    alliance_warfare: Any = None,
    context_memory: Any = None  # NEW: Pass context_memory for vocabulary restoration
) -> Callable:
    """
    Wire the germination pool into the Highlander Protocol.
    
    Returns a callback that should be called after each tournament round.
    
    Population-Correlated Features:
    - Updates population state each round for calibration
    - Takes periodic snapshots for regression strategy  
    - Spawns challengers tuned to current board state
    
    GERMINATION WAVE ALLIANCES:
    - Each germination wave creates a PRE-ALLIED cohort
    - Newcomers are born into "Generation N" alliance
    - Gives the fallen a fighting chance against veterans
    """
    
    snapshot_interval = 50  # Take developmental snapshot every N frames
    frame_counter = [0]  # Mutable counter for closure
    alliance_warfare_ref = [alliance_warfare]  # Mutable reference for later update
    context_memory_ref = [context_memory]  # Mutable reference for vocabulary restoration
    
    def set_alliance_warfare(aws):
        """Update the alliance_warfare reference after initialization."""
        alliance_warfare_ref[0] = aws
    
    def set_context_memory(cm):
        """Update the context_memory reference after initialization."""
        context_memory_ref[0] = cm
    
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
    
    def on_round_complete(organisms: List[Any]):
        """
        Called after each tournament round.
        
        Updates population state for calibration, takes periodic developmental
        snapshots, and runs HEALING PROTOCOL on trapped organisms.
        """
        # Update population state (BOARD CORRELATION)
        germination_pool.update_population_state(organisms)
        
        # Take periodic snapshots for regression strategy
        frame_counter[0] += 1
        if frame_counter[0] % snapshot_interval == 0:
            for org in organisms:
                germination_pool.snapshot_organism(org)
        
        # ═══════════════════════════════════════════════════════════════════════
        # HEALING PROTOCOL - DISABLED
        # Was causing issues with language generation - organisms need to learn
        # from their own patterns, not have them "healed" away
        # ═══════════════════════════════════════════════════════════════════════
        # NOTE: Code preserved but disabled - can re-enable if needed
        
    def check_and_germinate() -> List[Any]:
        """Check if germination is needed and spawn new organisms"""
        current_pop = len(highlander_protocol.active_organisms)
        needs, count = germination_pool.check_population_needs(current_pop)

        # DEBUG: Germination check
        logger = logging.getLogger(__name__)
        # Ensure console output for germination logs
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('[GERMINATION] %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

        if needs:
            logger.info(f"🌱 GERMINATION TRIGGERED: Population {current_pop} -> need {count} new organisms")
            logger.info(f"   Generation: {germination_pool.generation_counter}")
            logger.info(f"   Strategy weights: {germination_pool.strategy_weights}")
        else:
            logger.debug(f"Population stable: {current_pop} organisms")

        # Also update population state before germination decision
        if hasattr(highlander_protocol, 'active_organisms'):
            germination_pool.update_population_state(list(highlander_protocol.active_organisms))
        
        if not needs:
            return []
            
        # Prepare and germinate candidates
        candidates = germination_pool.prepare_germination(count)
        new_organisms = []
        
        for candidate in candidates:
            organism = germination_pool.germinate(candidate, organism_factory)
            if organism:
                # Register with highlander protocol (pass ID, not object)
                org_id = organism.id if hasattr(organism, 'id') else str(id(organism))
                highlander_protocol.register_organism(org_id)
                new_organisms.append(organism)
                
                # RESTORE VOCABULARY: Link inherited words to new organism in context_memory
                if hasattr(organism, '_inherited_vocabulary') and organism._inherited_vocabulary:
                    cm = context_memory_ref[0]  # Use the reference from closure
                    if cm:
                        org_id = organism.id if hasattr(organism, 'id') else hash(str(id(organism)))
                        for word in organism._inherited_vocabulary:
                            try:
                                cm.link_word_to_node(word, org_id)
                            except Exception:
                                pass  # Word linking failed, but organism still lives
                        reincarnation_logger = logging.getLogger(__name__)
                        reincarnation_logger.info(f"   📚 Restored {len(organism._inherited_vocabulary)} inherited words")

                # DEBUG: Reincarnation logging
                reincarnation_logger = logging.getLogger(__name__)
                reincarnation_logger.info(f"🌱 REINCARNATION: New organism {org_id}")
                reincarnation_logger.info(f"   Strategy: {candidate.strategy}")
                reincarnation_logger.info(f"   Parent lineage: {', '.join(candidate.parent_ids[:2])}{'...' if len(candidate.parent_ids) > 2 else ''}")
                if hasattr(organism, 'atomic_language') and organism.atomic_language:
                    inherited_concepts = len(organism.atomic_language.atoms) if hasattr(organism.atomic_language, 'atoms') else 0
                    reincarnation_logger.info(f"   Inherited concepts: {inherited_concepts}")
                reincarnation_logger.info(f"   Ready for battle round {highlander_protocol.round_number + 1}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🏛️ GERMINATION WAVE ALLIANCE - The fallen rise TOGETHER
        # Each wave of newcomers is pre-allied as a generation cohort.
        # This gives them a fighting chance against established veterans.
        # ═══════════════════════════════════════════════════════════════════════
        aws = alliance_warfare_ref[0]  # Get current alliance_warfare reference
        if new_organisms and aws and len(new_organisms) >= 2:
            generation = germination_pool.generation_counter
            wave_alliance_name = f"Generation {generation} Rising"
            
            # Create the wave alliance with the first organism as founder
            founder = new_organisms[0]
            founder_id = getattr(founder, 'id', getattr(founder, 'species_id', str(id(founder))))
            
            try:
                # Create alliance directly (bypassing proposal system for wave cohorts)
                from reality_simulator.evolution.alliance_warfare import PlanetaryAlliance, AllianceRole
                
                wave_alliance_id = f"wave_gen_{generation}_{int(time.time())}"
                wave_alliance = PlanetaryAlliance(
                    alliance_id=wave_alliance_id,
                    name=wave_alliance_name,
                    founder_id=founder_id
                )
                
                # Add all wave members
                wave_alliance.add_member(founder_id, AllianceRole.FOUNDER)
                for org in new_organisms[1:]:
                    org_id = getattr(org, 'id', getattr(org, 'species_id', str(id(org))))
                    wave_alliance.add_member(org_id, AllianceRole.MEMBER)
                    # Set alliance_id on organism
                    if hasattr(org, 'alliance_id'):
                        org.alliance_id = wave_alliance_id
                
                # Set founder's alliance_id
                if hasattr(founder, 'alliance_id'):
                    founder.alliance_id = wave_alliance_id
                
                # Register with alliance warfare system
                aws.alliances[wave_alliance_id] = wave_alliance
                
                # Create alliance history for illumination progression
                if hasattr(aws, '_get_or_create_history'):
                    aws._get_or_create_history(wave_alliance_id)
                
                # Record founding event
                if hasattr(aws, 'record_historical_event'):
                    from reality_simulator.evolution.alliance_warfare import HistoricalEventType
                    aws.record_historical_event(
                        alliance_id=wave_alliance_id,
                        event_type=HistoricalEventType.ALLIANCE_FOUNDED,
                        description=f"Generation {generation} rises from the fallen! {len(new_organisms)} warriors born allied.",
                        primary_organism_id=founder_id,
                        outcome="success"
                    )
                
                reincarnation_logger = logging.getLogger(__name__)
                reincarnation_logger.info(f"🏛️ WAVE ALLIANCE FORMED: '{wave_alliance_name}'")
                reincarnation_logger.info(f"   Members: {len(new_organisms)} warriors born allied")
                reincarnation_logger.info(f"   Founder: {founder_id}")
                reincarnation_logger.info(f"   🛡️ The fallen rise TOGETHER - they have a fighting chance!")
                
            except Exception as e:
                reincarnation_logger = logging.getLogger(__name__)
                reincarnation_logger.warning(f"Could not create wave alliance: {e}")
                
        if new_organisms:
            germination_pool.advance_generation()
            
        return new_organisms
        
    # Wire callbacks
    if hasattr(highlander_protocol, 'on_elimination_callback'):
        highlander_protocol.on_elimination_callback = on_organism_eliminated
    if hasattr(highlander_protocol, 'on_champion_callback'):
        highlander_protocol.on_champion_callback = on_champion_crowned
    if hasattr(highlander_protocol, 'on_round_complete_callback'):
        highlander_protocol.on_round_complete_callback = on_round_complete
    
    # Attach the setters so alliance_warfare and context_memory can be wired later
    check_and_germinate.set_alliance_warfare = set_alliance_warfare
    check_and_germinate.set_context_memory = set_context_memory
        
    return check_and_germinate
