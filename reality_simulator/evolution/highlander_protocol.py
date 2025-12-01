"""
⚔️ THE HIGHLANDER PROTOCOL
==========================

"There can be only one... but there never will be."

A perpetual evolutionary tournament where organisms compete for survival.
The fittest absorb the fallen, growing stronger with each victory.
But the germination pool ensures eternal competition - new challengers arise.

Mechanics:
- SURVIVAL: Organisms below fitness threshold are culled
- COMPETITION: Direct fitness battles, winner absorbs loser's best traits
- COOPERATION: Alliances form, mutual concept sharing, survival bonuses
- PREDATION: High-fitness organisms can hunt lower ones (optional)
- GERMINATION: Constant influx of fresh challengers

This creates evolutionary pressure impossible to game:
- Pure fitness isn't enough (need to survive battles)
- Social dynamics emerge (alliances, betrayals)
- Knowledge accumulation (concepts, configs absorbed from fallen)
- True survival of the fittest with emergent strategies

The last survivor gets checkpointed.
Then the arena resets and it begins again.

Author: Convergence Engine Team  
Created: 2024
"""

import numpy as np
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from collections import defaultdict


class HighlanderPhase(Enum):
    """Phases of the Highlander Protocol."""
    GERMINATION = "germination"     # New organisms entering
    COMPETITION = "competition"     # Active battles
    COOPERATION = "cooperation"     # Alliance building
    PREDATION = "predation"         # Hunting phase
    CULLING = "culling"             # Removing weak organisms
    ABSORPTION = "absorption"       # Winners absorbing losers
    EQUILIBRIUM = "equilibrium"     # Stable state (temporary)
    CHAMPION = "champion"           # Only one remains


class RelationshipType(Enum):
    """Types of relationships between organisms."""
    NEUTRAL = "neutral"
    ALLIED = "allied"
    RIVAL = "rival"
    PREDATOR = "predator"
    PREY = "prey"


@dataclass
class BattleResult:
    """Result of a competition between two organisms."""
    winner_id: str
    loser_id: str
    winner_fitness: float
    loser_fitness: float
    battle_type: str  # 'fitness', 'concept', 'random'
    margin: float  # How decisive the victory was
    concepts_transferred: List[str]
    configs_transferred: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'winner': self.winner_id,
            'loser': self.loser_id,
            'type': self.battle_type,
            'margin': self.margin,
            'concepts': self.concepts_transferred,
            'configs': self.configs_transferred,
            'time': self.timestamp
        }


@dataclass
class Alliance:
    """
    An alliance between organisms.
    
    In real life, weaker units that group together become stronger.
    This models emergent cooperation - organisms can achieve through
    unity what they cannot achieve alone.
    
    Alliance benefits:
    - Survival bonus: Allied organisms less likely to be culled
    - Combat bonus: Alliance size provides strength multiplier
    - Concept sharing: Members share knowledge freely
    - Collective defense: Allies avoid fighting each other
    """
    members: Set[str]
    formation_time: float
    strength: float = 1.0  # Alliance cohesion
    shared_concepts: Set[str] = field(default_factory=set)
    betrayal_count: int = 0
    collective_fitness: float = 0.0  # Sum of member fitness
    total_battles_won: int = 0  # Collective victories
    
    def add_member(self, organism_id: str):
        self.members.add(organism_id)
    
    def remove_member(self, organism_id: str):
        self.members.discard(organism_id)
    
    def is_member(self, organism_id: str) -> bool:
        return organism_id in self.members
    
    def weaken(self, amount: float = 0.1):
        self.strength = max(0.0, self.strength - amount)
    
    def strengthen(self, amount: float = 0.1):
        self.strength = min(1.0, self.strength + amount)
    
    def get_collective_strength_bonus(self) -> float:
        """
        Weaker units together become stronger.
        
        Bonus scales with:
        - Number of members (more = stronger)
        - Alliance cohesion (strength)
        - Shared concepts (knowledge synergy)
        """
        size_bonus = min(1.0, len(self.members) * 0.15)  # Up to 100% at 7 members
        cohesion_bonus = self.strength * 0.2  # Up to 20%
        knowledge_bonus = min(0.15, len(self.shared_concepts) * 0.01)  # Up to 15%
        
        return size_bonus + cohesion_bonus + knowledge_bonus
    
    def share_concept(self, concept: str):
        """Add a concept to the alliance's shared knowledge pool."""
        self.shared_concepts.add(concept)


@dataclass 
class OrganismStats:
    """Highlander stats for an organism."""
    battles_won: int = 0
    battles_lost: int = 0
    organisms_absorbed: int = 0
    concepts_absorbed: List[str] = field(default_factory=list)
    configs_absorbed: Dict[str, Any] = field(default_factory=dict)
    survival_streak: int = 0
    peak_fitness: float = 0.0
    peak_fitness_time: float = 0.0
    lineage: List[str] = field(default_factory=list)
    alliance_id: Optional[str] = None
    kills: int = 0
    times_hunted: int = 0
    
    def record_win(self, loser_id: str, concepts: List[str], configs: Dict[str, Any]):
        self.battles_won += 1
        self.survival_streak += 1
        self.organisms_absorbed += 1
        self.concepts_absorbed.extend(concepts)
        self.configs_absorbed.update(configs)
        self.lineage.append(loser_id)
    
    def record_loss(self):
        self.battles_lost += 1
        self.survival_streak = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'battles_won': self.battles_won,
            'battles_lost': self.battles_lost,
            'organisms_absorbed': self.organisms_absorbed,
            'concepts_absorbed': self.concepts_absorbed,
            'configs_absorbed': self.configs_absorbed,
            'survival_streak': self.survival_streak,
            'peak_fitness': self.peak_fitness,
            'peak_fitness_time': self.peak_fitness_time,
            'lineage': self.lineage,
            'kills': self.kills
        }


class HighlanderProtocol:
    """
    The Highlander Protocol - perpetual evolutionary tournament.
    
    "There can be only one... but there never will be."
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 event_emitter: Optional[Callable] = None,
                 capsule_manager: Optional[Any] = None,
                 battle_arena: Optional[Any] = None):
        """
        Initialize the Highlander Protocol.
        
        Args:
            config: Protocol configuration
            event_emitter: Callback for causation events
            capsule_manager: OrganismCapsuleManager for checkpointing
            battle_arena: BattleArena for multi-dimensional combat
        """
        self.config = config or {}
        self.event_emitter = event_emitter
        self.capsule_manager = capsule_manager
        
        # Initialize Battle Arena for real combat
        if battle_arena:
            self.battle_arena = battle_arena
        else:
            try:
                from reality_simulator.evolution.battle_arena import BattleArena
                arena_config = {
                    'chaos_factor': self.config.get('battle_randomness', 0.15),
                    'max_rounds': self.config.get('max_battle_rounds', 10)
                }
                self.battle_arena = BattleArena(config=arena_config, event_emitter=event_emitter)
            except ImportError:
                self.battle_arena = None
        
        # Protocol parameters (from atomic config if available)
        self.survival_threshold = self.config.get('survival_threshold', 0.3)
        self.competition_intensity = self.config.get('competition_intensity', 0.5)
        self.cooperation_bonus = self.config.get('cooperation_bonus', 0.2)
        self.predation_enabled = self.config.get('predation_enabled', False)
        self.germination_rate = self.config.get('germination_rate', 0.1)
        self.max_population = self.config.get('max_population', 100)
        self.min_population = self.config.get('min_population', 10)
        self.battle_randomness = self.config.get('battle_randomness', 0.1)
        
        # State
        self.phase = HighlanderPhase.GERMINATION
        self.round_number = 0
        self.organism_stats: Dict[str, OrganismStats] = {}
        self.alliances: Dict[str, Alliance] = {}
        self.relationships: Dict[Tuple[str, str], RelationshipType] = {}
        self.battle_history: List[BattleResult] = []
        self.fallen: List[str] = []  # IDs of eliminated organisms
        self.champion_history: List[Dict[str, Any]] = []
        
        # Current round state
        self.active_organisms: Set[str] = set()
        self.pending_battles: List[Tuple[str, str]] = []
        self.round_start_time = 0.0
    
    def register_organism(self, organism_id: str, initial_fitness: float = 0.5):
        """Register an organism in the protocol."""
        if organism_id not in self.organism_stats:
            self.organism_stats[organism_id] = OrganismStats(
                peak_fitness=initial_fitness,
                peak_fitness_time=time.time()
            )
        self.active_organisms.add(organism_id)
        
        self._emit_event('organism_registered', {
            'organism_id': organism_id,
            'initial_fitness': initial_fitness,
            'population_size': len(self.active_organisms)
        })
    
    def unregister_organism(self, organism_id: str, reason: str = "eliminated"):
        """Remove organism from active competition."""
        self.active_organisms.discard(organism_id)
        self.fallen.append(organism_id)
        
        # Remove from any alliances
        for alliance in self.alliances.values():
            alliance.remove_member(organism_id)
        
        self._emit_event('organism_fallen', {
            'organism_id': organism_id,
            'reason': reason,
            'final_stats': self.organism_stats[organism_id].to_dict() if organism_id in self.organism_stats else {},
            'remaining': len(self.active_organisms)
        })
    
    def run_round(self, organisms: Dict[str, Any], 
                 get_fitness: Callable[[Any], float]) -> Dict[str, Any]:
        """
        Run one round of the Highlander Protocol.
        
        Args:
            organisms: Dict of organism_id -> organism object
            get_fitness: Function to get fitness from organism
            
        Returns:
            Round results with battles, eliminations, etc.
        """
        self.round_number += 1
        self.round_start_time = time.time()
        
        results = {
            'round': self.round_number,
            'phase': self.phase.value,
            'battles': [],
            'eliminations': [],
            'alliances_formed': [],
            'predation_events': [],
            'germinations': 0,
            'champion': None
        }
        
        # Update active organisms
        self.active_organisms = set(organisms.keys())
        
        # Update fitness peaks
        for org_id, org in organisms.items():
            fitness = get_fitness(org)
            if org_id in self.organism_stats:
                if fitness > self.organism_stats[org_id].peak_fitness:
                    self.organism_stats[org_id].peak_fitness = fitness
                    self.organism_stats[org_id].peak_fitness_time = time.time()
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: CULLING - Remove organisms below threshold
        # ═══════════════════════════════════════════════════════════════
        if self.phase != HighlanderPhase.CHAMPION:
            eliminations = self._run_culling(organisms, get_fitness)
            results['eliminations'].extend(eliminations)
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: COMPETITION - Battles between organisms
        # ═══════════════════════════════════════════════════════════════
        if len(self.active_organisms) >= 2:
            battles = self._run_competition(organisms, get_fitness)
            results['battles'].extend(battles)
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 3: COOPERATION - Form/maintain alliances
        # ═══════════════════════════════════════════════════════════════
        alliances = self._run_cooperation(organisms, get_fitness)
        results['alliances_formed'].extend(alliances)
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 4: PREDATION - High fitness hunts low fitness
        # ═══════════════════════════════════════════════════════════════
        if self.predation_enabled:
            predation = self._run_predation(organisms, get_fitness)
            results['predation_events'].extend(predation)
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 5: GERMINATION - Spawn new challengers
        # ═══════════════════════════════════════════════════════════════
        if len(self.active_organisms) < self.min_population:
            # Signal that germination is needed
            needed = self.min_population - len(self.active_organisms)
            results['germinations'] = needed
            self._emit_event('germination_needed', {
                'current_population': len(self.active_organisms),
                'needed': needed
            })
        
        # ═══════════════════════════════════════════════════════════════
        # CHECK FOR CHAMPION
        # ═══════════════════════════════════════════════════════════════
        if len(self.active_organisms) == 1:
            champion_id = list(self.active_organisms)[0]
            results['champion'] = self._crown_champion(champion_id, organisms.get(champion_id))
            self.phase = HighlanderPhase.CHAMPION
        else:
            self.phase = HighlanderPhase.COMPETITION
        
        # Update phase based on population
        results['population'] = len(self.active_organisms)
        results['phase'] = self.phase.value
        
        return results
    
    def _run_culling(self, organisms: Dict[str, Any],
                    get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """Cull organisms below survival threshold."""
        eliminations = []
        
        # Get fitness values
        fitness_values = {
            org_id: get_fitness(org) 
            for org_id, org in organisms.items()
            if org_id in self.active_organisms
        }
        
        if not fitness_values:
            return eliminations
        
        # Calculate dynamic threshold based on population
        avg_fitness = np.mean(list(fitness_values.values()))
        threshold = self.survival_threshold * avg_fitness
        
        for org_id, fitness in fitness_values.items():
            # Alliance members get survival bonus
            survival_bonus = 0.0
            if org_id in self.organism_stats:
                alliance_id = self.organism_stats[org_id].alliance_id
                if alliance_id and alliance_id in self.alliances:
                    alliance = self.alliances[alliance_id]
                    survival_bonus = self.cooperation_bonus * alliance.strength
            
            effective_fitness = fitness + survival_bonus
            
            if effective_fitness < threshold:
                # Check survival probability based on how far below threshold
                survival_prob = effective_fitness / threshold
                
                if np.random.random() > survival_prob:
                    self.unregister_organism(org_id, reason="culled_low_fitness")
                    eliminations.append({
                        'organism_id': org_id,
                        'fitness': fitness,
                        'threshold': threshold,
                        'reason': 'culled'
                    })
        
        return eliminations
    
    def _run_competition(self, organisms: Dict[str, Any],
                        get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """Run competitive battles between organisms."""
        battles = []
        
        active_list = [oid for oid in self.active_organisms if oid in organisms]
        if len(active_list) < 2:
            return battles
        
        # Number of battles based on intensity
        num_battles = int(len(active_list) * self.competition_intensity)
        num_battles = max(1, min(num_battles, len(active_list) // 2))
        
        # Select battle pairs (avoid allies fighting each other)
        for _ in range(num_battles):
            if len(active_list) < 2:
                break
            
            # Select first combatant
            idx1 = np.random.randint(len(active_list))
            org1_id = active_list[idx1]
            
            # Select second combatant (preferring non-allies)
            candidates = [
                oid for oid in active_list 
                if oid != org1_id and not self._are_allied(org1_id, oid)
            ]
            
            if not candidates:
                # Must fight ally
                candidates = [oid for oid in active_list if oid != org1_id]
            
            if not candidates:
                continue
            
            org2_id = np.random.choice(candidates)
            
            # Conduct battle
            result = self._conduct_battle(
                org1_id, organisms[org1_id],
                org2_id, organisms[org2_id],
                get_fitness
            )
            
            if result:
                battles.append(result.to_dict())
                self.battle_history.append(result)
                
                # Winner absorbs loser's best traits
                self._absorb_loser(
                    result.winner_id, organisms.get(result.winner_id),
                    result.loser_id, organisms.get(result.loser_id)
                )
                
                # Loser is eliminated
                self.unregister_organism(result.loser_id, reason="defeated_in_battle")
                active_list.remove(result.loser_id)
        
        return battles
    
    def _conduct_battle(self, org1_id: str, org1: Any,
                       org2_id: str, org2: Any,
                       get_fitness: Callable[[Any], float]) -> Optional[BattleResult]:
        """
        Conduct a battle between two organisms.
        
        Uses the Battle Arena for multi-dimensional combat if available,
        otherwise falls back to fitness-based comparison.
        """
        
        # ═══════════════════════════════════════════════════════════════
        # USE BATTLE ARENA FOR REAL COMBAT
        # ═══════════════════════════════════════════════════════════════
        if self.battle_arena is not None:
            try:
                from reality_simulator.evolution.battle_arena import BattleType
                
                # Run full multi-dimensional combat!
                arena_outcome = self.battle_arena.resolve_battle(
                    org1, org2, 
                    battle_type=BattleType.FULL_COMBAT
                )
                
                # Convert arena outcome to our BattleResult format
                winner_id = arena_outcome.winner_id
                loser_id = arena_outcome.loser_id
                winner_fitness = get_fitness(org1 if winner_id == org1_id else org2)
                loser_fitness = get_fitness(org2 if winner_id == org1_id else org1)
                
                # Update stats with arena results
                if winner_id in self.organism_stats:
                    self.organism_stats[winner_id].record_win(
                        loser_id, 
                        arena_outcome.concepts_transferred,
                        arena_outcome.config_changes
                    )
                if loser_id in self.organism_stats:
                    self.organism_stats[loser_id].record_loss()
                
                # Execute actual absorption in the arena
                winner_org = org1 if winner_id == org1_id else org2
                loser_org = org2 if winner_id == org1_id else org1
                self.battle_arena.execute_absorption(winner_org, loser_org, arena_outcome)
                
                self._emit_event('battle_concluded', {
                    'winner': winner_id,
                    'loser': loser_id,
                    'battle_type': 'arena_full_combat',
                    'margin': arena_outcome.margin_of_victory,
                    'rounds': arena_outcome.total_rounds,
                    'concepts_transferred': arena_outcome.concepts_transferred,
                    'traits_transferred': arena_outcome.traits_transferred,
                    'neural_transfer': arena_outcome.neural_transfer_rate,
                    'narrative': arena_outcome.narrative_summary
                })
                
                return BattleResult(
                    winner_id=winner_id,
                    loser_id=loser_id,
                    winner_fitness=winner_fitness,
                    loser_fitness=loser_fitness,
                    battle_type='arena_combat',
                    margin=arena_outcome.margin_of_victory,
                    concepts_transferred=arena_outcome.concepts_transferred,
                    configs_transferred=arena_outcome.config_changes
                )
                
            except Exception as e:
                # Fall back to fitness-based if arena fails
                print(f"Arena battle failed, using fitness fallback: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # FALLBACK: FITNESS-BASED COMPARISON
        # ═══════════════════════════════════════════════════════════════
        fitness1 = get_fitness(org1)
        fitness2 = get_fitness(org2)
        
        # Add randomness to make battles unpredictable
        effective1 = fitness1 * (1 + np.random.uniform(-self.battle_randomness, self.battle_randomness))
        effective2 = fitness2 * (1 + np.random.uniform(-self.battle_randomness, self.battle_randomness))
        
        # Survival streak bonus
        if org1_id in self.organism_stats:
            streak1 = self.organism_stats[org1_id].survival_streak
            effective1 *= (1 + streak1 * 0.02)  # 2% bonus per streak
        if org2_id in self.organism_stats:
            streak2 = self.organism_stats[org2_id].survival_streak
            effective2 *= (1 + streak2 * 0.02)
        
        # ═══════════════════════════════════════════════════════════════
        # ALLIANCE COLLECTIVE STRENGTH BONUS
        # Weaker units together become stronger!
        # ═══════════════════════════════════════════════════════════════
        alliance_bonus_1 = 0.0
        alliance_bonus_2 = 0.0
        
        if org1_id in self.organism_stats:
            alliance1_id = self.organism_stats[org1_id].alliance_id
            if alliance1_id and alliance1_id in self.alliances:
                alliance = self.alliances[alliance1_id]
                alliance_bonus_1 = alliance.get_collective_strength_bonus()
                effective1 *= (1 + alliance_bonus_1)
        
        if org2_id in self.organism_stats:
            alliance2_id = self.organism_stats[org2_id].alliance_id
            if alliance2_id and alliance2_id in self.alliances:
                alliance = self.alliances[alliance2_id]
                alliance_bonus_2 = alliance.get_collective_strength_bonus()
                effective2 *= (1 + alliance_bonus_2)
        
        if effective1 > effective2:
            winner_id, loser_id = org1_id, org2_id
            winner_fitness, loser_fitness = fitness1, fitness2
        else:
            winner_id, loser_id = org2_id, org1_id
            winner_fitness, loser_fitness = fitness2, fitness1
        
        margin = abs(effective1 - effective2) / max(effective1, effective2)
        
        # Determine what gets transferred
        concepts_to_transfer = self._get_transferable_concepts(loser_id, organisms={org1_id: org1, org2_id: org2}.get(loser_id))
        configs_to_transfer = self._get_transferable_configs(loser_id)
        
        # Update stats
        if winner_id in self.organism_stats:
            self.organism_stats[winner_id].record_win(loser_id, concepts_to_transfer, configs_to_transfer)
            # Strengthen winner's alliance
            alliance_id = self.organism_stats[winner_id].alliance_id
            if alliance_id and alliance_id in self.alliances:
                self.alliances[alliance_id].strengthen(0.1)
                self.alliances[alliance_id].total_battles_won += 1
        
        if loser_id in self.organism_stats:
            self.organism_stats[loser_id].record_loss()
        
        self._emit_event('battle_concluded', {
            'winner': winner_id,
            'loser': loser_id,
            'battle_type': 'fitness_fallback',
            'margin': margin,
            'concepts_transferred': concepts_to_transfer,
            'alliance_bonus_winner': alliance_bonus_1 if winner_id == org1_id else alliance_bonus_2,
            'alliance_bonus_loser': alliance_bonus_2 if winner_id == org1_id else alliance_bonus_1
        })
        
        return BattleResult(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_fitness=winner_fitness,
            loser_fitness=loser_fitness,
            battle_type='fitness',
            margin=margin,
            concepts_transferred=concepts_to_transfer,
            configs_transferred=configs_to_transfer
        )
    
    def _get_transferable_concepts(self, loser_id: str, loser: Any = None) -> List[str]:
        """Get concepts that can be transferred from loser to winner."""
        concepts = []
        
        if loser and hasattr(loser, 'atomic_language'):
            lang = loser.atomic_language
            if hasattr(lang, 'atoms'):
                # Transfer strongest unique concepts
                sorted_concepts = sorted(
                    lang.atoms.items(),
                    key=lambda x: x[1].strength,
                    reverse=True
                )
                # Take top 5 concepts
                concepts = [c for c, _ in sorted_concepts[:5]]
        
        return concepts
    
    def _get_transferable_configs(self, loser_id: str) -> Dict[str, Any]:
        """Get configs that can be transferred from loser to winner."""
        configs = {}
        
        if loser_id in self.organism_stats:
            stats = self.organism_stats[loser_id]
            # Include any previously absorbed configs
            configs.update(stats.configs_absorbed)
        
        return configs
    
    def _absorb_loser(self, winner_id: str, winner: Any,
                     loser_id: str, loser: Any):
        """Winner absorbs loser's best traits."""
        if not winner or not loser:
            return
        
        # Absorb concepts
        if hasattr(winner, 'atomic_language') and hasattr(loser, 'atomic_language'):
            concepts = self._get_transferable_concepts(loser_id, loser)
            for concept in concepts:
                if hasattr(winner.atomic_language, 'learn_concept_from'):
                    loser.atomic_language.teach_concept(concept, winner.atomic_language)
        
        # Absorb configs
        if hasattr(winner, 'config_system') and hasattr(loser, 'config_system'):
            winner.config_system.absorb_config(loser.config_system, absorption_rate=0.3)
        
        self._emit_event('absorption_complete', {
            'winner': winner_id,
            'loser': loser_id,
            'concepts_absorbed': len(self._get_transferable_concepts(loser_id, loser))
        })
    
    def _run_cooperation(self, organisms: Dict[str, Any],
                        get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """
        Run cooperation phase - form and maintain alliances.
        
        Key insight: Weaker organisms actively seek alliances for survival.
        This models real-world cooperation where smaller units band together.
        """
        alliances_formed = []
        
        # Decay existing alliances
        for alliance_id in list(self.alliances.keys()):
            alliance = self.alliances[alliance_id]
            alliance.weaken(0.05)
            
            # Strengthen alliances where members share concepts
            if len(alliance.shared_concepts) > 3:
                alliance.strengthen(0.02)
            
            # Update collective fitness
            alliance.collective_fitness = sum(
                get_fitness(organisms[mid]) 
                for mid in alliance.members 
                if mid in organisms
            )
            
            # Remove dead alliances
            if alliance.strength <= 0 or len(alliance.members) < 2:
                for member in alliance.members:
                    if member in self.organism_stats:
                        self.organism_stats[member].alliance_id = None
                del self.alliances[alliance_id]
        
        # ═══════════════════════════════════════════════════════════════
        # STRATEGIC ALLIANCE FORMATION
        # Weaker organisms are MORE LIKELY to seek alliances
        # ═══════════════════════════════════════════════════════════════
        
        # Get fitness values for all unallied organisms
        unallied = [
            oid for oid in self.active_organisms
            if oid in organisms and (
                oid not in self.organism_stats or 
                self.organism_stats[oid].alliance_id is None
            )
        ]
        
        if len(unallied) < 2:
            return alliances_formed
        
        # Calculate average fitness
        fitness_values = {oid: get_fitness(organisms[oid]) for oid in unallied}
        avg_fitness = np.mean(list(fitness_values.values())) if fitness_values else 0.5
        
        # Weaker organisms are more motivated to ally
        # Probability scales inversely with fitness
        for org_id in unallied:
            org_fitness = fitness_values.get(org_id, 0.5)
            
            # Weakness factor: how far below average
            weakness_factor = max(0, (avg_fitness - org_fitness) / avg_fitness)
            
            # Base probability + weakness bonus (weak organisms 3x more likely to seek allies)
            alliance_probability = self.cooperation_bonus + (weakness_factor * 0.3)
            
            if np.random.random() < alliance_probability:
                # This organism seeks an alliance!
                # Find compatible partner (similar weakness OR complementary strengths)
                candidates = [
                    cid for cid in unallied 
                    if cid != org_id and not self._are_allied(org_id, cid)
                ]
                
                if not candidates:
                    continue
                
                # Score candidates: prefer similar fitness (solidarity) or slightly stronger (protection)
                def alliance_score(candidate_id):
                    c_fitness = fitness_values.get(candidate_id, 0.5)
                    fitness_diff = abs(org_fitness - c_fitness)
                    
                    # Prefer similar fitness (solidarity of the weak)
                    similarity_score = 1.0 - fitness_diff
                    
                    # Small bonus for slightly stronger partner (protection)
                    protection_bonus = 0.1 if c_fitness > org_fitness else 0
                    
                    return similarity_score + protection_bonus
                
                best_partner = max(candidates, key=alliance_score)
                
                # Form alliance
                alliance_id = f"alliance_{self.round_number}_{org_id[:4]}_{best_partner[:4]}"
                alliance = Alliance(
                    members={org_id, best_partner},
                    formation_time=time.time()
                )
                alliance.collective_fitness = org_fitness + fitness_values.get(best_partner, 0)
                
                self.alliances[alliance_id] = alliance
                
                for oid in [org_id, best_partner]:
                    if oid not in self.organism_stats:
                        self.organism_stats[oid] = OrganismStats()
                    self.organism_stats[oid].alliance_id = alliance_id
                
                # Share concepts immediately
                self._share_alliance_concepts(alliance, organisms, org_id, best_partner)
                
                alliances_formed.append({
                    'alliance_id': alliance_id,
                    'members': [org_id, best_partner],
                    'round': self.round_number,
                    'initiator_fitness': org_fitness,
                    'partner_fitness': fitness_values.get(best_partner, 0),
                    'weakness_factor': weakness_factor
                })
                
                self._emit_event('alliance_formed', {
                    'alliance_id': alliance_id,
                    'members': [org_id, best_partner],
                    'initiator': org_id,
                    'reason': 'weakness_cooperation' if weakness_factor > 0.2 else 'strategic',
                    'collective_strength': alliance.get_collective_strength_bonus()
                })
                
                # Remove from unallied to prevent double-allying
                unallied = [uid for uid in unallied if uid not in [org_id, best_partner]]
        
        return alliances_formed
    
    def _share_alliance_concepts(self, alliance: Alliance, organisms: Dict[str, Any],
                                 org1_id: str, org2_id: str):
        """Share concepts between newly allied organisms."""
        try:
            org1 = organisms.get(org1_id)
            org2 = organisms.get(org2_id)
            
            if not org1 or not org2:
                return
            
            # Get concepts from both organisms
            concepts1 = set()
            concepts2 = set()
            
            if hasattr(org1, 'atomic_language') and org1.atomic_language:
                concepts1 = set(org1.atomic_language.atoms.keys())
            if hasattr(org2, 'atomic_language') and org2.atomic_language:
                concepts2 = set(org2.atomic_language.atoms.keys())
            
            # Alliance shares all concepts
            alliance.shared_concepts = concepts1 | concepts2
            
            # Each organism learns concepts from the other
            new_concepts_1 = concepts2 - concepts1
            new_concepts_2 = concepts1 - concepts2
            
            # Teach concepts (simplified - just strengthen)
            for concept in new_concepts_1:
                if hasattr(org1, 'atomic_language') and org1.atomic_language:
                    try:
                        org1.atomic_language.acquire_concept(
                            concept, source='alliance', strength=0.3
                        )
                    except Exception:
                        pass
                        
            for concept in new_concepts_2:
                if hasattr(org2, 'atomic_language') and org2.atomic_language:
                    try:
                        org2.atomic_language.acquire_concept(
                            concept, source='alliance', strength=0.3
                        )
                    except Exception:
                        pass
                        
        except Exception:
            pass  # Don't break on concept sharing failure
        
        return alliances_formed
    
    def _are_allied(self, org1_id: str, org2_id: str) -> bool:
        """Check if two organisms are allies."""
        if org1_id not in self.organism_stats or org2_id not in self.organism_stats:
            return False
        
        alliance1 = self.organism_stats[org1_id].alliance_id
        alliance2 = self.organism_stats[org2_id].alliance_id
        
        return alliance1 is not None and alliance1 == alliance2
    
    def _run_predation(self, organisms: Dict[str, Any],
                      get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """Run predation phase - strong hunt weak."""
        predation_events = []
        
        if not self.predation_enabled:
            return predation_events
        
        active_list = list(self.active_organisms)
        if len(active_list) < 3:
            return predation_events
        
        # Sort by fitness
        fitness_ranking = sorted(
            [(oid, get_fitness(organisms[oid])) for oid in active_list if oid in organisms],
            key=lambda x: x[1],
            reverse=True
        )
        
        if len(fitness_ranking) < 3:
            return predation_events
        
        # Top organisms can hunt bottom organisms
        n_predators = max(1, len(fitness_ranking) // 5)
        n_prey = max(1, len(fitness_ranking) // 3)
        
        predators = [oid for oid, _ in fitness_ranking[:n_predators]]
        prey = [oid for oid, _ in fitness_ranking[-n_prey:]]
        
        for predator_id in predators:
            if not prey:
                break
            
            # Predator hunts with probability based on fitness difference
            prey_id = np.random.choice(prey)
            pred_fitness = get_fitness(organisms[predator_id])
            prey_fitness = get_fitness(organisms[prey_id])
            
            hunt_success_prob = (pred_fitness - prey_fitness) / max(pred_fitness, 0.01)
            hunt_success_prob = np.clip(hunt_success_prob, 0.1, 0.9)
            
            if np.random.random() < hunt_success_prob:
                # Successful hunt
                predation_events.append({
                    'predator': predator_id,
                    'prey': prey_id,
                    'success': True
                })
                
                if predator_id in self.organism_stats:
                    self.organism_stats[predator_id].kills += 1
                if prey_id in self.organism_stats:
                    self.organism_stats[prey_id].times_hunted += 1
                
                # Absorb prey
                self._absorb_loser(
                    predator_id, organisms.get(predator_id),
                    prey_id, organisms.get(prey_id)
                )
                
                self.unregister_organism(prey_id, reason="hunted")
                prey.remove(prey_id)
                
                self._emit_event('predation_success', {
                    'predator': predator_id,
                    'prey': prey_id
                })
        
        return predation_events
    
    def _crown_champion(self, champion_id: str, champion: Any) -> Dict[str, Any]:
        """Crown the last surviving organism as champion."""
        stats = self.organism_stats.get(champion_id, OrganismStats())
        
        champion_data = {
            'champion_id': champion_id,
            'round': self.round_number,
            'timestamp': time.time(),
            'stats': stats.to_dict(),
            'lineage_length': len(stats.lineage),
            'concepts_accumulated': len(stats.concepts_absorbed)
        }
        
        self.champion_history.append(champion_data)
        
        # Checkpoint the champion
        if self.capsule_manager and champion:
            try:
                capsule = self.capsule_manager.capture_organism(
                    champion,
                    reason='highlander_champion',
                    notes=f"Champion of round {self.round_number}",
                    tags=['champion', 'highlander', f'round_{self.round_number}']
                )
                filepath = self.capsule_manager.save_capsule(capsule)
                champion_data['capsule_path'] = filepath
                champion_data['capsule_id'] = capsule.capsule_id
            except Exception as e:
                champion_data['capsule_error'] = str(e)
        
        self._emit_event('champion_crowned', champion_data)
        
        return champion_data
    
    def reset_arena(self):
        """Reset the arena for a new tournament."""
        self.round_number = 0
        self.phase = HighlanderPhase.GERMINATION
        self.active_organisms.clear()
        self.alliances.clear()
        self.relationships.clear()
        self.pending_battles.clear()
        self.fallen.clear()
        # Keep stats and history for analysis
        
        self._emit_event('arena_reset', {
            'previous_champions': len(self.champion_history)
        })
    
    def get_leaderboard(self, organisms: Dict[str, Any],
                       get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """Get current leaderboard."""
        leaderboard = []
        
        for org_id in self.active_organisms:
            if org_id not in organisms:
                continue
            
            org = organisms[org_id]
            fitness = get_fitness(org)
            stats = self.organism_stats.get(org_id, OrganismStats())
            
            leaderboard.append({
                'rank': 0,  # Will be filled in
                'organism_id': org_id,
                'fitness': fitness,
                'battles_won': stats.battles_won,
                'survival_streak': stats.survival_streak,
                'concepts_absorbed': len(stats.concepts_absorbed),
                'alliance': stats.alliance_id,
                'kills': stats.kills
            })
        
        # Sort by fitness, then by battles won
        leaderboard.sort(key=lambda x: (x['fitness'], x['battles_won']), reverse=True)
        
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return leaderboard
    
    def get_protocol_status(self) -> Dict[str, Any]:
        """Get current protocol status."""
        return {
            'phase': self.phase.value,
            'round': self.round_number,
            'active_organisms': len(self.active_organisms),
            'total_fallen': len(self.fallen),
            'active_alliances': len(self.alliances),
            'total_battles': len(self.battle_history),
            'champions': len(self.champion_history),
            'predation_enabled': self.predation_enabled,
            'config': {
                'survival_threshold': self.survival_threshold,
                'competition_intensity': self.competition_intensity,
                'cooperation_bonus': self.cooperation_bonus,
                'germination_rate': self.germination_rate
            }
        }
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit a causation event."""
        if not self.event_emitter:
            return
        
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='highlander',
                event_type=f'highlander_{event_type}',
                data={
                    'round': self.round_number,
                    'phase': self.phase.value,
                    **data
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def create_highlander_from_atomic_config(config_system: Any) -> HighlanderProtocol:
    """Create Highlander Protocol from an AtomicConfigSystem."""
    config = {
        'survival_threshold': config_system.get('survival_threshold', 0.3),
        'competition_intensity': config_system.get('competition_intensity', 0.5),
        'cooperation_bonus': config_system.get('cooperation_bonus', 0.2),
        'predation_enabled': config_system.get('predation_enabled', False),
        'germination_rate': config_system.get('germination_rate', 0.1)
    }
    return HighlanderProtocol(config=config)


def run_tournament(organisms: Dict[str, Any],
                  get_fitness: Callable[[Any], float],
                  max_rounds: int = 100,
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a complete Highlander tournament until one organism remains.
    
    Args:
        organisms: Dict of organism_id -> organism
        get_fitness: Function to get fitness from organism
        max_rounds: Maximum rounds before forced termination
        config: Protocol configuration
        
    Returns:
        Tournament results with champion data
    """
    protocol = HighlanderProtocol(config=config)
    
    # Register all organisms
    for org_id, org in organisms.items():
        protocol.register_organism(org_id, get_fitness(org))
    
    # Run rounds until champion emerges
    for round_num in range(max_rounds):
        # Filter to active organisms only
        active_orgs = {
            oid: organisms[oid] 
            for oid in protocol.active_organisms 
            if oid in organisms
        }
        
        if len(active_orgs) <= 1:
            break
        
        result = protocol.run_round(active_orgs, get_fitness)
        
        if result.get('champion'):
            return {
                'champion': result['champion'],
                'rounds': round_num + 1,
                'total_battles': len(protocol.battle_history),
                'total_fallen': len(protocol.fallen),
                'status': protocol.get_protocol_status()
            }
    
    # Max rounds reached - crown highest fitness as champion
    if protocol.active_organisms:
        leaderboard = protocol.get_leaderboard(organisms, get_fitness)
        if leaderboard:
            return {
                'champion': {
                    'champion_id': leaderboard[0]['organism_id'],
                    'reason': 'max_rounds_reached'
                },
                'rounds': max_rounds,
                'total_battles': len(protocol.battle_history),
                'total_fallen': len(protocol.fallen),
                'status': protocol.get_protocol_status()
            }
    
    return {
        'champion': None,
        'reason': 'no_survivors',
        'rounds': max_rounds,
        'status': protocol.get_protocol_status()
    }
