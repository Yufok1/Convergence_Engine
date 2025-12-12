"""
🥊 BATTLE ARENA
===============

Where organisms clash in multi-dimensional combat.

================================================================================
ATTRIBUTION: The absorption battle system is inspired by "Highlander" (1986),
directed by Russell Mulcahy, written by Gregory Widen.

    "There can be only one."

The Quickening - where an immortal gains the knowledge, skills, and power of
a defeated opponent - directly inspired this neural/concept/trait transfer system.
================================================================================

Battle is not just fitness comparison - it's a complex interaction:
- Neural outputs clash (who makes better decisions?)
- Concepts compete (richer vocabulary = strategic advantage)
- Traits counter each other (aggressive vs defensive)
- VP endurance matters (who can sustain the fight?)
- Random chaos keeps it unpredictable

The winner absorbs the loser's best capabilities:
- Neural patterns (partial weight transfer) 
- Concepts (vocabulary expansion)
- Configs (optimal hyperparameters)
- Traits (behavioral tendencies)

This creates TRUE evolutionary pressure where everything matters.

Author: Convergence Engine Team
Created: 2024
"""

import numpy as np
import torch
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import random


class BattleType(Enum):
    """Types of battles organisms can engage in."""
    NEURAL_DUEL = "neural_duel"         # Direct neural output comparison
    CONCEPT_CLASH = "concept_clash"     # Vocabulary/language competition
    TRAIT_MATCHUP = "trait_matchup"     # Trait-based rock-paper-scissors
    ENDURANCE = "endurance"             # VP-based survival test
    FULL_COMBAT = "full_combat"         # All dimensions combined
    PREDATOR_HUNT = "predator_hunt"     # Asymmetric hunt scenario
    COOPERATIVE_TEST = "cooperative"    # Can they work together?
    PROTON_GAME = "proton_game"         # Apprentice Adept style gym battles


class TraitAdvantage(Enum):
    """Trait matchup advantages (rock-paper-scissors style)."""
    AGGRESSIVE_BEATS_PASSIVE = ("aggressive", "passive")
    PASSIVE_BEATS_CURIOUS = ("passive", "curious")
    CURIOUS_BEATS_CAUTIOUS = ("curious", "cautious")
    CAUTIOUS_BEATS_AGGRESSIVE = ("cautious", "aggressive")
    SOCIAL_BEATS_SOLITARY = ("social", "solitary")
    SOLITARY_BEATS_DEPENDENT = ("solitary", "dependent")


@dataclass
class CombatStats:
    """Combat statistics for battle resolution."""
    # Neural combat
    neural_score: float = 0.0
    decision_quality: float = 0.0
    reaction_speed: float = 0.0
    
    # Concept combat
    vocabulary_power: float = 0.0
    concept_depth: float = 0.0
    linguistic_coherence: float = 0.0
    
    # Trait combat
    trait_score: float = 0.0
    trait_counters: int = 0
    trait_synergies: int = 0
    
    # Endurance
    vp_reserve: float = 0.0
    stamina: float = 0.0
    recovery_rate: float = 0.0
    
    # Overall
    total_power: float = 0.0
    critical_chance: float = 0.0
    
    def compute_total(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Compute total combat power with optional dimension weights."""
        w = weights or {
            'neural': 0.3,
            'concept': 0.2,
            'trait': 0.2,
            'endurance': 0.2,
            'base': 0.1
        }
        
        self.total_power = (
            w.get('neural', 0.3) * (self.neural_score + self.decision_quality) / 2 +
            w.get('concept', 0.2) * (self.vocabulary_power + self.concept_depth) / 2 +
            w.get('trait', 0.2) * self.trait_score +
            w.get('endurance', 0.2) * (self.vp_reserve + self.stamina) / 2 +
            w.get('base', 0.1) * self.recovery_rate
        )
        
        return self.total_power


@dataclass
class BattleRound:
    """A single round of combat."""
    round_number: int
    attacker_id: str
    defender_id: str
    attack_type: str
    attack_power: float
    defense_power: float
    damage_dealt: float
    attacker_hp_after: float
    defender_hp_after: float
    critical_hit: bool = False
    counter_attack: bool = False
    narrative: str = ""


@dataclass
class BattleOutcome:
    """Complete battle outcome with full history."""
    battle_id: str
    battle_type: BattleType
    combatant_1_id: str
    combatant_2_id: str
    winner_id: str
    loser_id: str
    
    # Combat details
    rounds: List[BattleRound] = field(default_factory=list)
    total_rounds: int = 0
    
    # Final stats
    winner_final_hp: float = 0.0
    loser_final_hp: float = 0.0
    margin_of_victory: float = 0.0
    
    # Dimension scores
    winner_stats: Optional[CombatStats] = None
    loser_stats: Optional[CombatStats] = None
    dimension_breakdown: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Absorption details
    concepts_transferred: List[str] = field(default_factory=list)
    traits_transferred: List[str] = field(default_factory=list)
    config_changes: Dict[str, Any] = field(default_factory=dict)
    neural_transfer_rate: float = 0.0
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    duration_rounds: int = 0
    narrative_summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'battle_id': self.battle_id,
            'type': self.battle_type.value,
            'winner': self.winner_id,
            'loser': self.loser_id,
            'rounds': self.total_rounds,
            'margin': self.margin_of_victory,
            'concepts_transferred': self.concepts_transferred,
            'traits_transferred': self.traits_transferred,
            'narrative': self.narrative_summary
        }


class BattleArena:
    """
    The arena where organisms clash in multi-dimensional combat.
    
    Battles are resolved across multiple dimensions:
    1. Neural Combat - Who makes better decisions?
    2. Concept Warfare - Vocabulary and language mastery
    3. Trait Matchups - Behavioral counter-play
    4. VP Endurance - Survival and stamina
    5. Chaos Factor - Random upsets
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 event_emitter: Optional[Callable] = None):
        """
        Initialize the Battle Arena.
        
        Args:
            config: Arena configuration
            event_emitter: Callback for causation events
        """
        self.config = config or {}
        self.event_emitter = event_emitter
        
        # Battle parameters
        self.max_rounds = self.config.get('max_rounds', 50)  # Default matches config.json
        self.base_hp = self.config.get('base_hp', 100.0)
        self.critical_multiplier = self.config.get('critical_multiplier', 2.0)
        self.chaos_factor = self.config.get('chaos_factor', 0.0)  # Default matches config.json (disabled)
        self.dimension_weights = self.config.get('dimension_weights', {
            'neural': 0.30,
            'concept': 0.20,
            'trait': 0.20,
            'endurance': 0.20,
            'base': 0.10
        })
        
        # Trait matchup table (winner, loser)
        self.trait_counters = {
            'aggressive': ['passive', 'timid'],
            'defensive': ['aggressive', 'reckless'],
            'curious': ['cautious', 'fearful'],
            'cautious': ['reckless', 'aggressive'],
            'social': ['solitary', 'antisocial'],
            'cooperative': ['selfish', 'hoarding'],
            'adaptive': ['rigid', 'stubborn'],
            'fast': ['slow', 'lethargic'],
            'intelligent': ['instinctive', 'reactive']
        }
        
        # Battle history
        self.battle_count = 0
        self.battle_history: List[BattleOutcome] = []
    
    def calculate_combat_stats(self, organism: Any) -> CombatStats:
        """
        Calculate combat statistics for an organism.
        
        Examines all dimensions of the organism's capabilities.
        """
        stats = CombatStats()
        
        # ═══════════════════════════════════════════════════════════════
        # NEURAL COMBAT STATS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'brain') and organism.brain is not None:
            brain = organism.brain
            
            # Decision quality = how well-trained is the network?
            # Measured by parameter variance (well-trained = refined params)
            try:
                param_vars = []
                for p in brain.parameters():
                    if p.requires_grad:
                        param_vars.append(p.data.var().item())
                
                # Lower variance in later layers = more refined
                avg_var = np.mean(param_vars) if param_vars else 1.0
                stats.decision_quality = 1.0 / (1.0 + avg_var)
                
                # Neural score = total parameter magnitude (network "strength")
                total_magnitude = sum(p.data.abs().sum().item() for p in brain.parameters())
                num_params = sum(p.numel() for p in brain.parameters())
                stats.neural_score = min(1.0, total_magnitude / (num_params * 2))
                
                # Reaction speed = inverse of network depth/complexity
                depth = getattr(brain, 'num_layers', 2)
                stats.reaction_speed = 1.0 / depth
                
            except Exception:
                stats.neural_score = 0.5
                stats.decision_quality = 0.5
                stats.reaction_speed = 0.5
        
        # ═══════════════════════════════════════════════════════════════
        # CONCEPT WARFARE STATS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'atomic_language') and organism.atomic_language is not None:
            lang = organism.atomic_language
            
            # Vocabulary power = total concept strength
            if hasattr(lang, 'atoms'):
                total_strength = sum(a.strength for a in lang.atoms.values())
                num_concepts = len(lang.atoms)
                
                stats.vocabulary_power = min(1.0, total_strength / max(1, num_concepts))
                
                # Concept depth = average abstraction level
                avg_abstraction = np.mean([
                    a.abstraction_level for a in lang.atoms.values()
                ]) if lang.atoms else 0
                stats.concept_depth = min(1.0, avg_abstraction / 2.0)
                
                # Linguistic coherence = association density
                total_associations = sum(
                    len(a.associations) for a in lang.atoms.values()
                )
                stats.linguistic_coherence = min(1.0, total_associations / (num_concepts * 3))
        
        # ═══════════════════════════════════════════════════════════════
        # TRAIT COMBAT STATS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'traits') and organism.traits:
            traits = organism.traits
            
            # Count advantageous traits
            advantageous_count = 0
            for trait_name in traits:
                if trait_name.lower() in self.trait_counters:
                    advantageous_count += 1
            
            stats.trait_score = min(1.0, advantageous_count / 5.0)
            stats.trait_counters = advantageous_count
            
            # Synergies (compatible trait pairs)
            synergy_pairs = [
                ('aggressive', 'fast'),
                ('defensive', 'cautious'),
                ('social', 'cooperative'),
                ('intelligent', 'adaptive'),
                ('curious', 'explorer')
            ]
            
            trait_names = [t.lower() if isinstance(t, str) else str(t).lower() for t in traits]
            synergies = sum(1 for t1, t2 in synergy_pairs if t1 in trait_names and t2 in trait_names)
            stats.trait_synergies = synergies
        
        # ═══════════════════════════════════════════════════════════════
        # ENDURANCE STATS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'vitality') and hasattr(organism, 'pleasure'):
            # VP reserve = current VP state
            v = getattr(organism, 'vitality', 0.5)
            p = getattr(organism, 'pleasure', 0.5)
            stats.vp_reserve = (v + p) / 2
            
            # Stamina = historical VP stability
            v_history = getattr(organism, 'vitality_history', [v])[-20:]
            if len(v_history) > 1:
                v_stability = 1.0 - np.std(v_history)
                stats.stamina = max(0.0, v_stability)
            else:
                stats.stamina = 0.5
            
            # Recovery rate = how fast VP bounces back
            if len(v_history) > 2:
                recoveries = sum(1 for i in range(1, len(v_history)) if v_history[i] > v_history[i-1])
                stats.recovery_rate = recoveries / len(v_history)
            else:
                stats.recovery_rate = 0.5
        
        # ═══════════════════════════════════════════════════════════════
        # COMPUTE TOTAL
        # ═══════════════════════════════════════════════════════════════
        stats.compute_total(self.dimension_weights)
        
        # Critical hit chance based on traits and neural quality
        stats.critical_chance = 0.05 + (stats.decision_quality * 0.1) + (stats.trait_synergies * 0.02)
        
        return stats
    
    def resolve_battle(self, organism_1: Any, organism_2: Any,
                      battle_type: BattleType = BattleType.FULL_COMBAT,
                      bridge_1: Any = None, bridge_2: Any = None) -> BattleOutcome:
        """
        Resolve a battle between two organisms.
        
        Args:
            organism_1: First combatant
            organism_2: Second combatant
            battle_type: Type of battle to conduct
            bridge_1: Optional AgentBridge for organism 1 (required for PROTON_GAME)
            bridge_2: Optional AgentBridge for organism 2 (required for PROTON_GAME)
            
        Returns:
            Complete battle outcome
        """
        # ═══════════════════════════════════════════════════════════════
        # PROTON GAME ARENA (Gym-based battles)
        # ═══════════════════════════════════════════════════════════════
        if battle_type == BattleType.PROTON_GAME:
            return self._resolve_proton_game_battle(
                organism_1, organism_2, bridge_1, bridge_2
            )
        
        self.battle_count += 1
        battle_id = f"battle_{self.battle_count}_{int(time.time())}"
        
        org1_id = getattr(organism_1, 'id', 'organism_1')
        org2_id = getattr(organism_2, 'id', 'organism_2')
        
        # Calculate combat stats
        stats_1 = self.calculate_combat_stats(organism_1)
        stats_2 = self.calculate_combat_stats(organism_2)
        
        # Initialize HP
        hp_1 = self.base_hp * (1 + stats_1.vp_reserve * 0.2)
        hp_2 = self.base_hp * (1 + stats_2.vp_reserve * 0.2)
        
        rounds: List[BattleRound] = []
        
        # ═══════════════════════════════════════════════════════════════
        # BATTLE LOOP
        # ═══════════════════════════════════════════════════════════════
        for round_num in range(1, self.max_rounds + 1):
            if hp_1 <= 0 or hp_2 <= 0:
                break
            
            # Determine initiative (who attacks first this round)
            initiative_1 = stats_1.reaction_speed + np.random.uniform(-0.1, 0.1)
            initiative_2 = stats_2.reaction_speed + np.random.uniform(-0.1, 0.1)
            
            if initiative_1 >= initiative_2:
                first, second = (organism_1, stats_1, org1_id), (organism_2, stats_2, org2_id)
                first_hp, second_hp = hp_1, hp_2
            else:
                first, second = (organism_2, stats_2, org2_id), (organism_1, stats_1, org1_id)
                first_hp, second_hp = hp_2, hp_1
            
            # First attack
            attack_result = self._resolve_attack(
                first[1], second[1], 
                first[0], second[0],
                battle_type
            )
            
            damage = attack_result['damage']
            second_hp -= damage
            
            round_data = BattleRound(
                round_number=round_num,
                attacker_id=first[2],
                defender_id=second[2],
                attack_type=attack_result['type'],
                attack_power=attack_result['attack_power'],
                defense_power=attack_result['defense_power'],
                damage_dealt=damage,
                attacker_hp_after=first_hp,
                defender_hp_after=max(0, second_hp),
                critical_hit=attack_result['critical'],
                narrative=attack_result['narrative']
            )
            rounds.append(round_data)
            
            # Counter attack if defender survives
            if second_hp > 0:
                counter = self._resolve_attack(
                    second[1], first[1],
                    second[0], first[0],
                    battle_type
                )
                
                first_hp -= counter['damage']
                
                counter_round = BattleRound(
                    round_number=round_num,
                    attacker_id=second[2],
                    defender_id=first[2],
                    attack_type=counter['type'],
                    attack_power=counter['attack_power'],
                    defense_power=counter['defense_power'],
                    damage_dealt=counter['damage'],
                    attacker_hp_after=second_hp,
                    defender_hp_after=max(0, first_hp),
                    critical_hit=counter['critical'],
                    counter_attack=True,
                    narrative=counter['narrative']
                )
                rounds.append(counter_round)
            
            # Update HP tracking
            if initiative_1 >= initiative_2:
                hp_1, hp_2 = first_hp, second_hp
            else:
                hp_2, hp_1 = first_hp, second_hp
        
        # ═══════════════════════════════════════════════════════════════
        # DETERMINE WINNER
        # ═══════════════════════════════════════════════════════════════
        if hp_1 > hp_2:
            winner_id, loser_id = org1_id, org2_id
            winner, loser = organism_1, organism_2
            winner_stats, loser_stats = stats_1, stats_2
            winner_hp, loser_hp = hp_1, hp_2
        else:
            winner_id, loser_id = org2_id, org1_id
            winner, loser = organism_2, organism_1
            winner_stats, loser_stats = stats_2, stats_1
            winner_hp, loser_hp = hp_2, hp_1
        
        margin = (winner_hp - max(0, loser_hp)) / self.base_hp
        
        # ═══════════════════════════════════════════════════════════════
        # DETERMINE ABSORPTION
        # ═══════════════════════════════════════════════════════════════
        concepts_transferred = self._determine_concept_transfer(loser, margin)
        traits_transferred = self._determine_trait_transfer(loser, margin)
        config_changes = self._determine_config_transfer(loser, margin)
        neural_transfer = self._calculate_neural_transfer_rate(loser_stats, margin)
        
        # Build dimension breakdown
        dimension_breakdown = {
            'neural': (stats_1.neural_score, stats_2.neural_score),
            'concept': (stats_1.vocabulary_power, stats_2.vocabulary_power),
            'trait': (stats_1.trait_score, stats_2.trait_score),
            'endurance': (stats_1.vp_reserve, stats_2.vp_reserve),
            'total': (stats_1.total_power, stats_2.total_power)
        }
        
        # Generate narrative
        narrative = self._generate_battle_narrative(
            winner_id, loser_id, rounds, margin, 
            concepts_transferred, traits_transferred
        )
        
        outcome = BattleOutcome(
            battle_id=battle_id,
            battle_type=battle_type,
            combatant_1_id=org1_id,
            combatant_2_id=org2_id,
            winner_id=winner_id,
            loser_id=loser_id,
            rounds=rounds,
            total_rounds=len(rounds),
            winner_final_hp=winner_hp,
            loser_final_hp=max(0, loser_hp),
            margin_of_victory=margin,
            winner_stats=winner_stats,
            loser_stats=loser_stats,
            dimension_breakdown=dimension_breakdown,
            concepts_transferred=concepts_transferred,
            traits_transferred=traits_transferred,
            config_changes=config_changes,
            neural_transfer_rate=neural_transfer,
            duration_rounds=len(rounds),
            narrative_summary=narrative
        )
        
        self.battle_history.append(outcome)
        
        # Limit history to prevent memory growth
        if len(self.battle_history) > 500:
            self.battle_history = self.battle_history[-500:]
        
        self._emit_battle_event(outcome)
        
        # 🧠 NEURAL FEEDBACK: Record individual battle outcomes for learning
        # This wires up the previously orphaned BATTLE_FOUGHT concept
        winner_org = org1 if winner_id == org1_id else org2
        loser_org = org2 if winner_id == org1_id else org1
        if hasattr(winner_org, 'record_alliance_event'):
            winner_org.record_alliance_event("battle_won", True)
        if hasattr(loser_org, 'record_alliance_event'):
            loser_org.record_alliance_event("battle_lost", False)
        
        return outcome
    
    def _resolve_attack(self, attacker_stats: CombatStats, 
                       defender_stats: CombatStats,
                       attacker: Any, defender: Any,
                       battle_type: BattleType) -> Dict[str, Any]:
        """Resolve a single attack."""
        
        # Base attack power from stats
        if battle_type == BattleType.NEURAL_DUEL:
            attack_power = attacker_stats.neural_score + attacker_stats.decision_quality
            defense_power = defender_stats.neural_score + defender_stats.reaction_speed
            attack_type = "neural_pulse"
        
        elif battle_type == BattleType.CONCEPT_CLASH:
            attack_power = attacker_stats.vocabulary_power + attacker_stats.concept_depth
            defense_power = defender_stats.linguistic_coherence
            attack_type = "concept_assault"
        
        elif battle_type == BattleType.TRAIT_MATCHUP:
            attack_power = attacker_stats.trait_score + (attacker_stats.trait_synergies * 0.1)
            defense_power = defender_stats.trait_score
            attack_type = "trait_strike"
            
            # Check for trait counters
            attack_power += self._check_trait_advantage(attacker, defender) * 0.3
        
        elif battle_type == BattleType.ENDURANCE:
            attack_power = attacker_stats.stamina + attacker_stats.vp_reserve
            defense_power = defender_stats.recovery_rate + defender_stats.stamina
            attack_type = "endurance_test"
        
        else:  # FULL_COMBAT
            attack_power = attacker_stats.total_power
            defense_power = defender_stats.total_power * 0.5  # Defense is harder
            attack_type = "full_assault"
        
        # Add chaos factor
        attack_power *= (1 + np.random.uniform(-self.chaos_factor, self.chaos_factor))
        defense_power *= (1 + np.random.uniform(-self.chaos_factor, self.chaos_factor))
        
        # Check for critical hit
        critical = np.random.random() < attacker_stats.critical_chance
        if critical:
            attack_power *= self.critical_multiplier
        
        # Calculate damage
        raw_damage = max(0, attack_power - defense_power * 0.5) * 10
        damage = raw_damage * (1 + np.random.uniform(-0.1, 0.1))
        
        # Generate attack narrative
        narratives = {
            'neural_pulse': [
                "unleashes a devastating neural pulse",
                "fires synaptic lightning",
                "overwhelms with cognitive force"
            ],
            'concept_assault': [
                "launches a barrage of complex concepts",
                "weaponizes linguistic mastery",
                "drowns opponent in semantic complexity"
            ],
            'trait_strike': [
                "exploits behavioral weakness",
                "counters with superior traits",
                "adapts and overcomes"
            ],
            'endurance_test': [
                "maintains pressure through stamina",
                "outlasts with vital reserves",
                "wears down resistance"
            ],
            'full_assault': [
                "attacks on all fronts",
                "unleashes combined might",
                "brings full power to bear"
            ]
        }
        
        narrative = random.choice(narratives.get(attack_type, ["attacks"]))
        if critical:
            narrative = "CRITICAL! " + narrative
        
        return {
            'damage': damage,
            'attack_power': attack_power,
            'defense_power': defense_power,
            'critical': critical,
            'type': attack_type,
            'narrative': narrative
        }
    
    def _check_trait_advantage(self, attacker: Any, defender: Any) -> float:
        """Check if attacker has trait advantage over defender."""
        advantage = 0.0
        
        attacker_traits = set()
        defender_traits = set()
        
        if hasattr(attacker, 'traits'):
            attacker_traits = {str(t).lower() for t in attacker.traits}
        if hasattr(defender, 'traits'):
            defender_traits = {str(t).lower() for t in defender.traits}
        
        for winning_trait, losing_traits in self.trait_counters.items():
            if winning_trait in attacker_traits:
                for losing_trait in losing_traits:
                    if losing_trait in defender_traits:
                        advantage += 1.0
        
        return advantage
    
    def _determine_concept_transfer(self, loser: Any, margin: float) -> List[str]:
        """Determine which concepts transfer from loser to winner."""
        concepts = []
        
        if not hasattr(loser, 'atomic_language') or loser.atomic_language is None:
            return concepts
        
        lang = loser.atomic_language
        if not hasattr(lang, 'atoms'):
            return concepts
        
        # NO LIMIT - Winner takes ALL! The fallen's knowledge becomes yours
        # Sort by strength so strongest concepts are first
        sorted_concepts = sorted(
            lang.atoms.items(),
            key=lambda x: x[1].strength,
            reverse=True
        )
        
        # Transfer ALL concepts - no cap
        concepts = [c for c, _ in sorted_concepts]
        
        return concepts
    
    def _determine_trait_transfer(self, loser: Any, margin: float) -> List[str]:
        """Determine which traits transfer from loser to winner."""
        traits = []
        
        if not hasattr(loser, 'traits') or not loser.traits:
            return traits
        
        # Transfer ALL traits - no limit! Winner absorbs everything
        if isinstance(loser.traits, dict):
            sorted_traits = sorted(
                loser.traits.items(),
                key=lambda x: x[1] if isinstance(x[1], (int, float)) else 1,
                reverse=True
            )
            traits = [t for t, _ in sorted_traits]  # ALL traits
        else:
            traits = list(loser.traits)  # ALL traits
        
        return traits
    
    def _determine_config_transfer(self, loser: Any, margin: float) -> Dict[str, Any]:
        """Determine which configs transfer from loser to winner."""
        configs = {}
        
        if not hasattr(loser, 'config_system') or loser.config_system is None:
            return configs
        
        config_sys = loser.config_system
        if not hasattr(config_sys, 'atoms'):
            return configs
        
        # Transfer ALL configs - no limit! Winner absorbs everything
        best_configs = sorted(
            config_sys.atoms.items(),
            key=lambda x: x[1].get_value_performance(),
            reverse=True
        )
        
        # NO LIMIT - absorb ALL configs from the fallen
        for param_name, atom in best_configs:
            configs[param_name] = atom.value
        
        return configs
    
    def _calculate_neural_transfer_rate(self, loser_stats: CombatStats, 
                                        margin: float) -> float:
        """Calculate how much of loser's neural patterns to transfer."""
        # Higher margin = more transfer
        # Higher loser neural quality = more worth transferring
        base_rate = margin * 0.3
        quality_bonus = loser_stats.neural_score * 0.2
        
        return min(0.5, base_rate + quality_bonus)
    
    def _generate_battle_narrative(self, winner_id: str, loser_id: str,
                                   rounds: List[BattleRound], margin: float,
                                   concepts: List[str], traits: List[str]) -> str:
        """Generate a narrative summary of the battle."""
        total_rounds = len(rounds)
        
        if margin > 0.7:
            intensity = "DOMINANT"
        elif margin > 0.4:
            intensity = "decisive"
        elif margin > 0.2:
            intensity = "hard-fought"
        else:
            intensity = "nail-biting"
        
        crits = sum(1 for r in rounds if r.critical_hit)
        
        narrative = f"{intensity.upper()} victory for {winner_id} over {loser_id} "
        narrative += f"in {total_rounds} rounds. "
        
        if crits > 0:
            narrative += f"{crits} critical hits landed. "
        
        if concepts:
            narrative += f"Absorbed concepts: {', '.join(concepts[:3])}. "
        
        if traits:
            narrative += f"Gained traits: {', '.join(traits)}. "
        
        return narrative
    
    def _emit_battle_event(self, outcome: BattleOutcome):
        """Emit battle event for causation tracking."""
        if not self.event_emitter:
            return
        
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='battle_arena',
                event_type='battle_resolved',
                data={
                    'battle_id': outcome.battle_id,
                    'battle_type': outcome.battle_type.value,
                    'winner': outcome.winner_id,
                    'loser': outcome.loser_id,
                    'margin': outcome.margin_of_victory,
                    'rounds': outcome.total_rounds,
                    'concepts_transferred': outcome.concepts_transferred,
                    'traits_transferred': outcome.traits_transferred,
                    'neural_transfer_rate': outcome.neural_transfer_rate,
                    'narrative': outcome.narrative_summary
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    def execute_absorption(self, winner: Any, loser: Any, 
                          outcome: BattleOutcome) -> Dict[str, Any]:
        """
        Execute the actual absorption of loser's capabilities into winner.
        
        This is where the winner ACTUALLY gains the loser's power!
        """
        absorption_results = {
            'concepts_gained': 0,
            'traits_gained': 0,
            'configs_updated': 0,
            'neural_updated': False
        }
        
        # ═══════════════════════════════════════════════════════════════
        # ABSORB CONCEPTS
        # ═══════════════════════════════════════════════════════════════
        if outcome.concepts_transferred:
            if hasattr(winner, 'atomic_language') and hasattr(loser, 'atomic_language'):
                winner_lang = winner.atomic_language
                loser_lang = loser.atomic_language
                
                for concept_id in outcome.concepts_transferred:
                    if concept_id in loser_lang.atoms:
                        # Use teach_concept for proper transfer
                        if hasattr(loser_lang, 'teach_concept'):
                            result = loser_lang.teach_concept(concept_id, winner_lang)
                            if result.get('success', False):
                                absorption_results['concepts_gained'] += 1
                        else:
                            # Fallback: direct acquisition
                            if hasattr(winner_lang, 'acquire_concept'):
                                winner_lang.acquire_concept(
                                    concept_id,
                                    source='battle_absorption',
                                    initial_strength=loser_lang.atoms[concept_id].strength * 0.5,
                                    reason=f"absorbed_from_{outcome.loser_id}"
                                )
                                absorption_results['concepts_gained'] += 1
        
        # ═══════════════════════════════════════════════════════════════
        # ABSORB TRAITS
        # ═══════════════════════════════════════════════════════════════
        if outcome.traits_transferred:
            if hasattr(winner, 'traits') and hasattr(loser, 'traits'):
                for trait_name in outcome.traits_transferred:
                    if isinstance(winner.traits, dict):
                        if trait_name not in winner.traits:
                            # Get trait value from loser
                            if isinstance(loser.traits, dict):
                                trait_val = loser.traits.get(trait_name, 1.0)
                            else:
                                trait_val = 1.0
                            
                            winner.traits[trait_name] = trait_val * 0.5  # Partial transfer
                            absorption_results['traits_gained'] += 1
        
        # ═══════════════════════════════════════════════════════════════
        # ABSORB CONFIGS
        # ═══════════════════════════════════════════════════════════════
        if outcome.config_changes:
            if hasattr(winner, 'config_system') and hasattr(loser, 'config_system'):
                winner_config = winner.config_system
                loser_config = loser.config_system
                
                # Use atomic config absorption
                if hasattr(winner_config, 'absorb_config'):
                    absorbed = winner_config.absorb_config(
                        loser_config, 
                        absorption_rate=outcome.margin_of_victory * 0.5
                    )
                    absorption_results['configs_updated'] = len(absorbed)
        
        # ═══════════════════════════════════════════════════════════════
        # ABSORB NEURAL PATTERNS (ADVANCED)
        # ═══════════════════════════════════════════════════════════════
        if outcome.neural_transfer_rate > 0.1:
            if hasattr(winner, 'brain') and hasattr(loser, 'brain'):
                winner_brain = winner.brain
                loser_brain = loser.brain
                
                try:
                    # Blend neural weights
                    transfer_rate = outcome.neural_transfer_rate
                    
                    winner_state = winner_brain.state_dict()
                    loser_state = loser_brain.state_dict()
                    
                    blended_state = {}
                    for key in winner_state:
                        if key in loser_state and winner_state[key].shape == loser_state[key].shape:
                            # Blend: winner keeps most, absorbs some from loser
                            blended_state[key] = (
                                (1 - transfer_rate) * winner_state[key] +
                                transfer_rate * loser_state[key]
                            )
                        else:
                            blended_state[key] = winner_state[key]
                    
                    winner_brain.load_state_dict(blended_state)
                    absorption_results['neural_updated'] = True
                    
                except Exception as e:
                    print(f"Neural absorption failed: {e}")
        
        # Emit absorption event
        if self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='battle_arena',
                    event_type='absorption_complete',
                    data={
                        'winner': outcome.winner_id,
                        'loser': outcome.loser_id,
                        **absorption_results
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass
        
        return absorption_results
    
    # ═══════════════════════════════════════════════════════════════════
    # PROTON GAME ARENA INTEGRATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _resolve_proton_game_battle(self, 
                                    organism_1: Any, 
                                    organism_2: Any,
                                    bridge_1: Any = None,
                                    bridge_2: Any = None) -> BattleOutcome:
        """
        Resolve a battle using the Proton Game Arena (Gym-based combat).
        
        This uses the Apprentice Adept style game selection system where
        organisms compete in actual gymnasium environments.
        """
        self.battle_count += 1
        battle_id = f"proton_{self.battle_count}_{int(time.time())}"
        
        org1_id = getattr(organism_1, 'organism_id', getattr(organism_1, 'id', 'organism_1'))
        org2_id = getattr(organism_2, 'organism_id', getattr(organism_2, 'id', 'organism_2'))
        
        try:
            from reality_simulator.arena import ProtonGameArena
            proton_arena = ProtonGameArena()
            
            # Check if we have bridges
            if bridge_1 is None or bridge_2 is None:
                # Fall back to standard combat
                print("⚠️ Proton Game requires AgentBridge - falling back to standard combat")
                return self.resolve_battle(
                    organism_1, organism_2, 
                    battle_type=BattleType.FULL_COMBAT
                )
            
            # Run the Proton Game selection and battle
            proton_result = proton_arena.full_battle(
                organism_1, organism_2,
                bridge_1, bridge_2,
                highlander_mode=False,  # Consequences handled by our system
                ai_selection=True
            )
            
            # ═══════════════════════════════════════════════════════════════
            # FIX: Handle TIE correctly FIRST - if no winner_id, use fitness to determine
            # This MUST happen before we determine winner/loser for absorption
            # ═══════════════════════════════════════════════════════════════
            if proton_result.winner_id:
                actual_winner_id = proton_result.winner_id
            else:
                # TIE - use fitness to break the tie
                fitness_1 = getattr(organism_1, 'fitness', 0.5)
                fitness_2 = getattr(organism_2, 'fitness', 0.5)
                if fitness_1 != fitness_2:
                    actual_winner_id = org1_id if fitness_1 > fitness_2 else org2_id
                else:
                    # True tie - random coin flip
                    import random
                    actual_winner_id = random.choice([org1_id, org2_id])
                print(f"🎲 TIE resolved: winner={actual_winner_id[:8]} (fitness tiebreaker)")
            
            actual_loser_id = org2_id if actual_winner_id == org1_id else org1_id
            
            # Convert ProtonGameArena result to BattleOutcome (using resolved winner)
            winner = organism_1 if actual_winner_id == org1_id else organism_2
            loser = organism_2 if actual_winner_id == org1_id else organism_1
            
            # Determine absorption based on margin
            margin = abs(proton_result.score_a - proton_result.score_b) / max(
                max(proton_result.score_a, proton_result.score_b), 1.0
            )
            
            concepts_transferred = self._determine_concept_transfer(loser, margin)
            traits_transferred = self._determine_trait_transfer(loser, margin)
            config_changes = self._determine_config_transfer(loser, margin)
            
            # Generate narrative
            game_name = proton_result.game.name if proton_result.game else "Unknown"
            narrative = (
                f"⚔️ PROTON GAME: {game_name}\n"
                f"{org1_id[:8]}: {proton_result.score_a:.1f} vs "
                f"{org2_id[:8]}: {proton_result.score_b:.1f}\n"
                f"🏆 Winner: {actual_winner_id[:8]}"
                f"{' (TIE resolved)' if not proton_result.winner_id else ''}"
            )
            
            outcome = BattleOutcome(
                battle_id=battle_id,
                battle_type=BattleType.PROTON_GAME,
                combatant_1_id=org1_id,
                combatant_2_id=org2_id,
                winner_id=actual_winner_id,
                loser_id=actual_loser_id,
                rounds=[],  # Gym episodes tracked differently
                total_rounds=proton_result.total_episodes,
                winner_final_hp=proton_result.score_a if actual_winner_id == org1_id else proton_result.score_b,
                loser_final_hp=proton_result.score_b if actual_winner_id == org1_id else proton_result.score_a,
                margin_of_victory=margin,
                concepts_transferred=concepts_transferred,
                traits_transferred=traits_transferred,
                config_changes=config_changes,
                neural_transfer_rate=min(0.1 + margin * 0.2, 0.5),
                duration_rounds=proton_result.total_episodes,
                narrative_summary=narrative
            )
            
            self.battle_history.append(outcome)
            self._emit_battle_event(outcome)
            
            return outcome
            
        except ImportError as e:
            print(f"⚠️ Proton Game Arena not available: {e}")
            return self.resolve_battle(
                organism_1, organism_2,
                battle_type=BattleType.FULL_COMBAT
            )
        except Exception as e:
            print(f"⚠️ Proton Game battle failed: {e}")
            return self.resolve_battle(
                organism_1, organism_2,
                battle_type=BattleType.FULL_COMBAT
            )
    
    def get_arena_stats(self) -> Dict[str, Any]:
        """Get arena statistics."""
        if not self.battle_history:
            return {'total_battles': 0}
        
        margins = [b.margin_of_victory for b in self.battle_history]
        rounds = [b.total_rounds for b in self.battle_history]
        
        return {
            'total_battles': len(self.battle_history),
            'avg_margin': np.mean(margins),
            'avg_rounds': np.mean(rounds),
            'total_concepts_transferred': sum(
                len(b.concepts_transferred) for b in self.battle_history
            ),
            'total_traits_transferred': sum(
                len(b.traits_transferred) for b in self.battle_history
            ),
            'dimension_weights': self.dimension_weights
        }


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def quick_battle(org1: Any, org2: Any, 
                battle_type: BattleType = BattleType.FULL_COMBAT) -> BattleOutcome:
    """Quick battle between two organisms."""
    arena = BattleArena()
    return arena.resolve_battle(org1, org2, battle_type)


def tournament_bracket(organisms: List[Any], 
                      arena: Optional[BattleArena] = None) -> List[BattleOutcome]:
    """Run a single-elimination tournament bracket."""
    if arena is None:
        arena = BattleArena()
    
    results = []
    current_round = organisms.copy()
    
    while len(current_round) > 1:
        next_round = []
        random.shuffle(current_round)
        
        for i in range(0, len(current_round) - 1, 2):
            org1 = current_round[i]
            org2 = current_round[i + 1]
            
            outcome = arena.resolve_battle(org1, org2)
            results.append(outcome)
            
            # Winner advances
            if outcome.winner_id == getattr(org1, 'id', 'org1'):
                winner = org1
                loser = org2
            else:
                winner = org2
                loser = org1
            
            # Execute absorption
            arena.execute_absorption(winner, loser, outcome)
            next_round.append(winner)
        
        # Handle odd organism (gets a bye)
        if len(current_round) % 2 == 1:
            next_round.append(current_round[-1])
        
        current_round = next_round
    
    return results
