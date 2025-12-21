"""
⚔️ THE HIGHLANDER PROTOCOL
==========================

"There can be only one... but there never will be."

================================================================================
ATTRIBUTION: This system is inspired by "Highlander" (1986), directed by 
Russell Mulcahy, written by Gregory Widen.

The immortal combat system where warriors battle across centuries, and the 
victor claims "The Quickening" - absorbing the defeated's power, knowledge,
and life force - is the creative foundation of this evolutionary protocol.

    "I am Connor MacLeod of the Clan MacLeod. I was born in 1518 in the 
     village of Glenfinnan on the shores of Loch Shiel. And I am immortal."

We honor this iconic film that inspired our absorption battle system.
================================================================================

A perpetual evolutionary tournament where organisms compete for survival.
The fittest absorb the fallen, growing stronger with each victory.
But the germination pool ensures eternal competition - new challengers arise.

Mechanics:
- SURVIVAL: Organisms below fitness threshold are culled
- COMPETITION: Direct fitness battles, winner absorbs loser's best traits
- COOPERATION: Alliances form, mutual concept sharing, survival bonuses
- PREDATION: High-fitness organisms can hunt lower ones (optional)
- GERMINATION: Constant influx of fresh challengers
- RAY PARALLEL: Large tournaments use distributed battle resolution (4-5x speedup)

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
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from collections import defaultdict

# Try to import Language-Game Bridge
try:
    from reality_simulator.language.language_game_bridge import LanguageGameBridge
    LANGUAGE_BRIDGE_AVAILABLE = True
except ImportError:
    LanguageGameBridge = None
    LANGUAGE_BRIDGE_AVAILABLE = False

# Ray distributed computing - optional, graceful fallback
RAY_DISTRIBUTED_AVAILABLE = False
try:
    from ..distributed import get_ray_manager, RAY_AVAILABLE as _RAY_AVAIL
    from ..distributed.ray_tasks import resolve_battles_batch
    RAY_DISTRIBUTED_AVAILABLE = _RAY_AVAIL
except ImportError:
    pass


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
    formation_round: int = 0  # Round when alliance was formed
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
    confederation_tier: int = 0  # 0=none, 1=confederation, 2=empire, 3=hegemony
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

        # Set up logger with console output for battle debugging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Add console handler if not already present
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('[HIGHLANDER] %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            # Allow propagation so logs also go to application.log
            self.logger.propagate = True
        
        # Initialize Battle Arena for real combat
        if battle_arena:
            self.battle_arena = battle_arena
        else:
            try:
                from reality_simulator.evolution.battle_arena import BattleArena
                arena_config = {
                    'chaos_factor': self.config.get('battle_randomness', 0.15),
                    'max_rounds': self.config.get('max_battle_rounds', 10),
                    'gym_only': self.config.get('gym_only', False)  # 100% real gym battles when True
                }
                self.battle_arena = BattleArena(config=arena_config, event_emitter=event_emitter)
            except ImportError:
                self.battle_arena = None
        
        # Protocol parameters (from atomic config if available)
        self.survival_threshold = self.config.get('survival_threshold', 0.4)  # Default matches config.json
        self.competition_intensity = self.config.get('competition_intensity', 0.2)  # Default matches config.json
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
        
        # Callbacks for germination pool integration
        self.on_elimination_callback: Optional[Callable] = None
        self.on_champion_callback: Optional[Callable] = None
        self.on_round_complete_callback: Optional[Callable] = None
        
        # Context memory for vocabulary transfer on battle death
        self.context_memory: Optional[Any] = None
        
        # ═══════════════════════════════════════════════════════════════════
        # LANGUAGE-GAME BRIDGE: Connect vocabulary to battle decisions
        # ═══════════════════════════════════════════════════════════════════
        self.language_bridge = None
    
    def set_language_bridge(self, organism_names: List[str], 
                           atomic_language: Any = None,
                           knowledge_web: Any = None) -> None:
        """
        Initialize and connect the Language-Game Bridge.
        
        This connects the 62,000+ vocabulary concepts to game decision making,
        enabling bilateral learning:
        - Language helps games (vocabulary biases action selection)
        - Games help language (outcomes reinforce/weaken concepts)
        """
        if not LANGUAGE_BRIDGE_AVAILABLE:
            self.logger.warning("Language Bridge not available - vocabulary disconnected from games")
            return
        
        try:
            # Read config from self.config (meta-brain tunable) with fallbacks
            bridge_config = self.config.get('neural', {}).get('language_game_bridge', {})
            bias_strength = bridge_config.get('bias_strength', 0.3)
            learning_rate = bridge_config.get('learning_rate', 0.1)
            
            self.language_bridge = LanguageGameBridge(
                organism_names=organism_names,
                atomic_language=atomic_language,
                knowledge_web=knowledge_web,
                game_type="highlander_battle",
                bias_strength=bias_strength,
                learning_rate=learning_rate
            )
            
            # Wire to battle arena
            if self.battle_arena and hasattr(self.battle_arena, 'set_language_bridge'):
                self.battle_arena.set_language_bridge(self.language_bridge)
                self.logger.info(f"🔗 Language Bridge wired to Battle Arena")
            else:
                self.logger.warning(f"⚠️ Battle Arena NOT available for language bridge wiring (battle_arena={self.battle_arena is not None})")
            
            self.logger.info(f"🧠 Language Bridge: ACTIVE - {len(organism_names)} organisms (bias={bias_strength}, lr={learning_rate})")
        except Exception as e:
            self.logger.warning(f"Language Bridge init failed: {e}")
            self.language_bridge = None
    
    def set_context_memory(self, context_memory) -> None:
        """
        Wire ContextMemory for vocabulary transfer on battle death.
        
        CRITICAL: Without this, vocabulary is LOST when organisms die!
        The winner needs access to loser's word associations.
        """
        self.context_memory = context_memory
        self.logger.info("📚 ContextMemory linked - vocabulary will transfer on death!")
    
    def set_alliance_warfare_system(self, alliance_warfare_system) -> None:
        """
        Wire AllianceWarfareSystem into HighlanderProtocol.
        
        Called during unified_entry.py initialization to establish the bidirectional link.
        """
        self.alliance_warfare = alliance_warfare_system
        self.logger.info("🔗 AllianceWarfareSystem linked to HighlanderProtocol")

    def get_organism(self, organism_id: str):
        """
        Retrieve organism by ID for AllianceWarfareSystem to access.
        
        Needed because AllianceWarfareSystem.unlock_causation_for_alliance()
        must be able to get organisms to set their _illumination_level.
        """
        # We need to access the organisms dict passed to run_round usually.
        # But Highlander doesn't persist the full organism objects in self.
        # It gets them in run_round.
        # However, we might have a reference if integrated.
        # For now, we'll try to use a stored reference if we add one, 
        # or rely on the fact that run_round calls are active.
        
        # NOTE: This is a limitation. If get_organism is called OUTSIDE run_round,
        # we might fail. But Illumination grant happens DURING run_round (via sync).
        # So we can store a temporary reference in run_round?
        # Or rely on `self.active_organisms_ref` from run_round.
        return getattr(self, '_current_round_organisms', {}).get(organism_id)

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
    
    def unregister_organism(self, organism_id: str, reason: str = "eliminated", 
                           organism: Any = None, killer_id: Optional[str] = None):
        """Remove organism from active competition."""
        self.active_organisms.discard(organism_id)
        
        # Add to fallen list (avoid duplicates, limit memory growth)
        if organism_id not in self.fallen:
            self.fallen.append(organism_id)
            # Keep fallen list bounded (last 10000 deaths)
            if len(self.fallen) > 10000:
                self.fallen = self.fallen[-10000:]
        
        # Remove from any alliances
        for alliance in self.alliances.values():
            alliance.remove_member(organism_id)
        
        self._emit_event('organism_fallen', {
            'organism_id': organism_id,
            'reason': reason,
            'final_stats': self.organism_stats[organism_id].to_dict() if organism_id in self.organism_stats else {},
            'remaining': len(self.active_organisms)
        })
        
        # Call elimination callback for germination pool
        if self.on_elimination_callback and organism is not None:
            try:
                self.on_elimination_callback(organism, killer_id)
            except Exception:
                pass  # Don't let callback errors break protocol
    
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
        # Store organisms reference for get_organism() calls during this round
        self._current_round_organisms = organisms
        
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
        
        # Update active organisms - FILTER OUT FALLEN (don't resurrect the dead!)
        incoming_ids = set(organisms.keys())
        
        # If this is the first round, initialize active_organisms
        if not self.active_organisms:
            self.active_organisms = incoming_ids - set(self.fallen)
        else:
            # Only add NEW organisms (not previously fallen)
            new_organisms = incoming_ids - self.active_organisms - set(self.fallen)
            self.active_organisms.update(new_organisms)
            # Remove any that were eliminated but somehow still passed in
            self.active_organisms -= set(self.fallen)
        
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
        # Uses Ray parallel processing for large tournaments (4-5x speedup)
        # ═══════════════════════════════════════════════════════════════
        if len(self.active_organisms) >= 2:
            # Use parallel battles for large populations
            num_potential_battles = int(len(self.active_organisms) * self.competition_intensity)
            if RAY_DISTRIBUTED_AVAILABLE and num_potential_battles >= 10:
                battles = self._run_competition_parallel(organisms, get_fitness)
            else:
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
        
        # ═══════════════════════════════════════════════════════════════
        # ROUND COMPLETE CALLBACK - For population state tracking
        # ═══════════════════════════════════════════════════════════════
        if self.on_round_complete_callback:
            try:
                # Pass current organisms for population state update
                active_organisms = [organisms[oid] for oid in self.active_organisms if oid in organisms]
                self.on_round_complete_callback(active_organisms)
            except Exception:
                pass  # Don't let callback errors break protocol

        # DEBUG: Round summary
        battles_count = len(results.get('battles', []))
        culling_count = len(results.get('eliminations', []))
        predation_count = len(results.get('predation_events', []))
        # Total eliminations = battles (each has 1 loser) + culling + predation
        total_eliminations = battles_count + culling_count + predation_count
        alliances_count = len(self.alliances)
        active_count = len(self.active_organisms)

        self.logger.info(f"🎯 ROUND {self.round_number} COMPLETE:")
        self.logger.info(f"   ⚔️  Battles fought: {battles_count}")
        self.logger.info(f"   💀 Eliminations: {total_eliminations} (battles: {battles_count}, culled: {culling_count}, hunted: {predation_count})")
        self.logger.info(f"   🤝 Active alliances: {alliances_count}")
        self.logger.info(f"   👥 Population: {active_count}")
        self.logger.info(f"   📊 Phase: {self.phase.value}")
        
        # Update results with accurate elimination count
        results['total_eliminations'] = total_eliminations

        if results.get('champion'):
            self.logger.info(f"   👑 CHAMPION CROWNED: {results['champion']['champion_id']}")

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
            confederation_bonus = 0.0
            
            if org_id in self.organism_stats:
                alliance_id = self.organism_stats[org_id].alliance_id
                if alliance_id and alliance_id in self.alliances:
                    alliance = self.alliances[alliance_id]
                    survival_bonus = self.cooperation_bonus * alliance.strength
                    
                    # 🏛️ CONFEDERATION TIER BONUS - Higher tiers = better survival
                    # Tier 0 (none): +0.00
                    # Tier 1 (confederation): +0.05
                    # Tier 2 (empire): +0.10  
                    # Tier 3 (hegemony): +0.15
                    confederation_tier = getattr(
                        self.organism_stats[org_id], 'confederation_tier', 0
                    )
                    if confederation_tier > 0:
                        confederation_bonus = confederation_tier * 0.05
            
            effective_fitness = fitness + survival_bonus + confederation_bonus
            
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
        
        # MASTERY MATCHMAKING: Group by tier so vocab transfer always fits
        def get_mastery(org_id):
            org = organisms.get(org_id)
            if org and hasattr(org, 'atomic_language') and org.atomic_language:
                return getattr(org.atomic_language, '_mastery_level', 0)
            return 0
        
        mastery_pools = {}
        for org_id in active_list:
            level = get_mastery(org_id)
            if level not in mastery_pools:
                mastery_pools[level] = []
            mastery_pools[level].append(org_id)
        
        self.logger.info(f"🎯 MASTERY MATCHMAKING: {{{', '.join(f'{k}:{len(v)}' for k,v in sorted(mastery_pools.items()))}}}")
        
        # Battle within each mastery tier (only mastery 4+ can compete in Highlander)
        for mastery_level, pool in mastery_pools.items():
            if mastery_level < 4:
                # Protect developing organisms - no Highlander battles until mastery 4
                self.logger.debug(f"⏳ Mastery {mastery_level}: {len(pool)} organisms protected (need level 4+ for Highlander)")
                continue
            if len(pool) < 2:
                continue
            
            pool_battles = int(len(pool) * self.competition_intensity)
            pool_battles = max(1, min(pool_battles, len(pool) // 2))
            available = pool.copy()
            
            for _ in range(pool_battles):
                if len(available) < 2:
                    break
                
                idx1 = np.random.randint(len(available))
                org1_id = available[idx1]
                
                candidates = [
                    oid for oid in available 
                    if oid != org1_id and not self._are_allied(org1_id, oid)
                ]
                
                if not candidates:
                    candidates = [oid for oid in available if oid != org1_id]
                
                if not candidates:
                    continue
                
                org2_id = np.random.choice(candidates)
                
                if org1_id in available:
                    available.remove(org1_id)
                if org2_id in available:
                    available.remove(org2_id)
                
                    # Conduct battle
                result = self._conduct_battle(
                    org1_id, organisms[org1_id],
                    org2_id, organisms[org2_id],
                    get_fitness
                )
                
                if result:
                    battles.append(result.to_dict())
                    self.battle_history.append(result)
                    
                    if len(self.battle_history) > 1000:
                        self.battle_history = self.battle_history[-1000:]
                    
                    loser_org = organisms.get(result.loser_id)
                    if loser_org:
                        concepts_had = 0
                        if hasattr(loser_org, 'atomic_language') and loser_org.atomic_language:
                            concepts_had = len(loser_org.atomic_language.atoms) if hasattr(loser_org.atomic_language, 'atoms') else 0

                        self.logger.info(f"💀 ELIMINATED: {result.loser_id}")
                        self.logger.info(f"   Final fitness: {result.loser_fitness:.3f}")
                        self.logger.info(f"   Concepts lost: {concepts_had}")
                        self.logger.info(f"   Winner: {result.winner_id} (fitness: {result.winner_fitness:.3f})")
                        self.logger.info(f"   Will reincarnate via germination pool")

                    self.unregister_organism(result.loser_id, reason="defeated_in_battle")
                    if result.loser_id in active_list:
                        active_list.remove(result.loser_id)
        
        return battles
    
    def _run_competition_parallel(self, organisms: Dict[str, Any],
                                   get_fitness: Callable[[Any], float]) -> List[Dict[str, Any]]:
        """
        Run competitive battles using Ray parallel processing.
        
        For large populations (>10 battles), this provides 4-5x speedup by:
        1. Collecting all battle pairs upfront
        2. Resolving battles in parallel (stateless computation)
        3. Applying state mutations (absorptions, eliminations) sequentially after
        
        Falls back to sequential _run_competition if Ray unavailable or small population.
        """
        battles = []
        
        active_list = [oid for oid in self.active_organisms if oid in organisms]
        if len(active_list) < 2:
            return battles
        
        # Number of battles based on intensity
        num_battles = int(len(active_list) * self.competition_intensity)
        num_battles = max(1, min(num_battles, len(active_list) // 2))
        
        # Check if Ray parallelization is worthwhile (threshold: 10 battles)
        if not RAY_DISTRIBUTED_AVAILABLE or num_battles < 10:
            return self._run_competition(organisms, get_fitness)
        
        try:
            # MASTERY MATCHMAKING: Group by tier so vocab transfer always fits
            def get_mastery(org_id):
                org = organisms.get(org_id)
                if org and hasattr(org, 'atomic_language') and org.atomic_language:
                    return getattr(org.atomic_language, '_mastery_level', 0)
                return 0
            
            mastery_pools = {}
            for org_id in active_list:
                level = get_mastery(org_id)
                if level not in mastery_pools:
                    mastery_pools[level] = []
                mastery_pools[level].append(org_id)
            
            self.logger.info(f"🎯 RAY MASTERY MATCHMAKING: {{{', '.join(f'{k}:{len(v)}' for k,v in sorted(mastery_pools.items()))}}}")
            
            # Phase 1: Collect all battle pairs within mastery tiers (only mastery 4+ can compete)
            battle_pairs = []
            battle_pair_ids = []
            
            for mastery_level, pool in mastery_pools.items():
                if mastery_level < 4:
                    # Protect developing organisms - no Highlander battles until mastery 4
                    self.logger.debug(f"⏳ RAY Mastery {mastery_level}: {len(pool)} organisms protected (need level 4+ for Highlander)")
                    continue
                if len(pool) < 2:
                    continue
                
                pool_battles = int(len(pool) * self.competition_intensity)
                pool_battles = max(1, min(pool_battles, len(pool) // 2))
                available = pool.copy()
                
                for _ in range(pool_battles):
                    if len(available) < 2:
                        break
                    
                    idx1 = np.random.randint(len(available))
                    org1_id = available[idx1]
                    
                    candidates = [
                        oid for oid in available 
                        if oid != org1_id and not self._are_allied(org1_id, oid)
                    ]
                    
                    if not candidates:
                        candidates = [oid for oid in available if oid != org1_id]
                    
                    if not candidates:
                        continue
                    
                    org2_id = np.random.choice(candidates)
                    
                    org1_state = self._extract_battle_state(org1_id, organisms[org1_id], get_fitness)
                    org2_state = self._extract_battle_state(org2_id, organisms[org2_id], get_fitness)
                    
                    battle_pairs.append((org1_state, org2_state))
                    battle_pair_ids.append((org1_id, org2_id))
                    
                    if org1_id in available:
                        available.remove(org1_id)
                    if org2_id in available:
                        available.remove(org2_id)
            
            if not battle_pairs:
                return battles
            
            # Phase 2: Resolve battles in parallel (stateless - Ray)
            self.logger.info(f"⚡ RAY PARALLEL: Resolving {len(battle_pairs)} battles...")
            
            battle_config = {
                'chaos_factor': self.battle_randomness,
                'max_rounds': self.config.get('max_battle_rounds', 10)
            }
            
            parallel_results = resolve_battles_batch(battle_pairs, battle_config, use_ray=True)
            
            self.logger.info(f"⚡ RAY PARALLEL: {len(parallel_results)} battles resolved")
            
            # Phase 3: Apply results sequentially (state mutations)
            for (org1_id, org2_id), result in zip(battle_pair_ids, parallel_results):
                if not result:
                    continue
                
                # Convert parallel result to BattleResult
                winner_id = result['winner_id']
                loser_id = result['loser_id']
                
                battle_result = BattleResult(
                    winner_id=winner_id,
                    loser_id=loser_id,
                    winner_fitness=result['winner_fitness'],
                    loser_fitness=result['loser_fitness'],
                    battle_type='ray_parallel',
                    margin=result.get('margin', 0.0),
                    concepts_transferred=[],
                    configs_transferred={}
                )
                
                battles.append(battle_result.to_dict())
                self.battle_history.append(battle_result)
                
                # Update organism battle stats for card display
                winner_org = organisms.get(winner_id)
                loser_org = organisms.get(loser_id)
                if winner_org:
                    winner_org.battle_wins = getattr(winner_org, 'battle_wins', 0) + 1
                    # 🏆 Competition stats
                    winner_org.highlander_kills = getattr(winner_org, 'highlander_kills', 0) + 1
                    winner_org.win_streak = getattr(winner_org, 'win_streak', 0) + 1
                    if winner_org.win_streak > getattr(winner_org, 'best_win_streak', 0):
                        winner_org.best_win_streak = winner_org.win_streak
                if loser_org:
                    loser_org.battle_losses = getattr(loser_org, 'battle_losses', 0) + 1
                    loser_org.win_streak = 0  # Reset streak on death
                
                # Winner absorbs loser's traits
                self._absorb_loser(
                    winner_id, organisms.get(winner_id),
                    loser_id, organisms.get(loser_id)
                )
                
                # Loser eliminated
                self.logger.info(f"💀 ELIMINATED (Ray): {loser_id} by {winner_id}")
                self.unregister_organism(loser_id, reason="defeated_in_battle")
                if loser_id in active_list:
                    active_list.remove(loser_id)
            
            # Limit battle history
            if len(self.battle_history) > 1000:
                self.battle_history = self.battle_history[-1000:]
            
            return battles
            
        except Exception as e:
            self.logger.warning(f"Ray parallel battles failed, falling back: {e}")
            return self._run_competition(organisms, get_fitness)
    
    def _extract_battle_state(self, org_id: str, org: Any, 
                               get_fitness: Callable) -> dict:
        """
        Extract serializable battle state for Ray parallel processing.
        """
        fitness = get_fitness(org)
        
        traits = {}
        if hasattr(org, 'phenotype') and hasattr(org.phenotype, 'traits'):
            traits = dict(org.phenotype.traits)
        
        return {
            'id': org_id,
            'fitness': fitness,
            'traits': traits,
            'resources': getattr(org, 'resources', 0.5),
            'energy': getattr(org, 'energy', 0.5),
            'battle_wins': getattr(org, 'battle_wins', 0),
            'battle_losses': getattr(org, 'battle_losses', 0)
        }
    
    def _conduct_battle(self, org1_id: str, org1: Any,
                       org2_id: str, org2: Any,
                       get_fitness: Callable[[Any], float]) -> Optional[BattleResult]:
        """
        Conduct a battle between two organisms.

        Uses the Battle Arena for multi-dimensional combat if available,
        otherwise falls back to fitness-based comparison.
        """
        
        # ═══════════════════════════════════════════════════════════════
        # 🗣️ PRE-BATTLE COMMUNICATION - Organisms talk before fighting!
        # Language is the medium for coordination, intimidation, strategy
        # ═══════════════════════════════════════════════════════════════
        if hasattr(org1, 'speak_to') and hasattr(org2, 'speak_to'):
            try:
                exchange = org1.speak_to(org2, context='battle')
                if exchange.get('success'):
                    self.logger.info(f"🗣️ Pre-battle exchange: {org1_id[:8]} → {org2_id[:8]} "
                                   f"(quality: {exchange.get('exchange_quality', 0):.2f}, "
                                   f"shared vocab: {len(exchange.get('shared_words', []))})")
            except Exception as e:
                self.logger.debug(f"Pre-battle communication failed: {e}")

        # Get initial fitness scores for logging
        org1_fitness = get_fitness(org1)
        org2_fitness = get_fitness(org2)

        # DEBUG: Battle initiation
        self.logger.info(f"⚔️  BATTLE: {org1_id} (fitness: {org1_fitness:.3f}) vs {org2_id} (fitness: {org2_fitness:.3f})")
        if hasattr(org1, 'atomic_language') and org1.atomic_language:
            concepts1 = len(org1.atomic_language.atoms) if hasattr(org1.atomic_language, 'atoms') else 0
            self.logger.info(f"   {org1_id} has {concepts1} concepts")
        if hasattr(org2, 'atomic_language') and org2.atomic_language:
            concepts2 = len(org2.atomic_language.atoms) if hasattr(org2.atomic_language, 'atoms') else 0
            self.logger.info(f"   {org2_id} has {concepts2} concepts")

        # ═══════════════════════════════════════════════════════════════
        # USE BATTLE ARENA FOR REAL COMBAT
        # ═══════════════════════════════════════════════════════════════
        if self.battle_arena is not None:
            try:
                from reality_simulator.evolution.battle_arena import BattleType
                import random as rng
                
                # Determine battle type from config (respects arena.default_battle_type)
                default_battle_type_str = self.config.get('default_battle_type', 'FULL_COMBAT')
                
                # Check probabilities for mixed battle selection
                proton_probability = self.config.get('proton_game_probability', 1.0)
                drone_probability = self.config.get('drone_combat_probability', 0.0)  # Drone combat chance
                
                if isinstance(default_battle_type_str, str):
                    try:
                        battle_type = BattleType[default_battle_type_str.upper()]
                    except KeyError:
                        battle_type = BattleType.FULL_COMBAT
                else:
                    battle_type = BattleType.FULL_COMBAT
                
                # Mixed battle selection: Drone > Proton > FullCombat
                roll = rng.random()
                if drone_probability > 0 and roll < drone_probability:
                    battle_type = BattleType.DRONE_COMBAT
                    self.logger.info(f"🛸 Drone Combat selected (probability: {drone_probability})")
                elif proton_probability > 0 and roll < (drone_probability + proton_probability):
                    if battle_type != BattleType.PROTON_GAME:
                        battle_type = BattleType.PROTON_GAME
                        self.logger.info(f"🎮 Proton Game selected (probability: {proton_probability})")
                elif battle_type == BattleType.PROTON_GAME and proton_probability < 1.0:
                    if rng.random() > proton_probability:
                        battle_type = BattleType.FULL_COMBAT
                        self.logger.info(f"⚔️ Full Combat selected")
                
                self.logger.info(f"⚔️ Battle type: {battle_type.value}")
                
                # For PROTON_GAME, create LiveOrganismAdapters as bridges
                bridge_1 = None
                bridge_2 = None
                if battle_type == BattleType.PROTON_GAME:
                    try:
                        from reality_simulator.arena.live_organism_adapter import LiveOrganismAdapter
                        bridge_1 = LiveOrganismAdapter(org1)
                        bridge_2 = LiveOrganismAdapter(org2)
                        self.logger.info(f"🌉 Created LiveOrganismAdapters for Proton Game battle")
                    except ImportError as e:
                        self.logger.warning(f"LiveOrganismAdapter not available: {e}, falling back to FULL_COMBAT")
                        battle_type = BattleType.FULL_COMBAT
                
                # Run combat with configured battle type!
                arena_outcome = self.battle_arena.resolve_battle(
                    org1, org2, 
                    battle_type=battle_type,
                    bridge_1=bridge_1,
                    bridge_2=bridge_2
                )
                
                # Convert arena outcome to our BattleResult format
                winner_id = arena_outcome.winner_id
                loser_id = arena_outcome.loser_id
                winner_fitness = get_fitness(org1 if winner_id == org1_id else org2)
                loser_fitness = get_fitness(org2 if winner_id == org1_id else org1)

                # DEBUG: Battle result
                self.logger.info(f"🏆 WINNER: {winner_id} (fitness: {winner_fitness:.3f}) defeated {loser_id} (fitness: {loser_fitness:.3f})")
                if hasattr(arena_outcome, 'concepts_transferred'):
                    self.logger.info(f"   📚 {arena_outcome.concepts_transferred} concepts transferred")
                if hasattr(arena_outcome, 'damage_dealt'):
                    self.logger.info(f"   💥 Damage: {arena_outcome.damage_dealt:.1f}")
                if hasattr(arena_outcome, 'rounds_survived'):
                    self.logger.info(f"   ⏱️  Rounds survived: {arena_outcome.rounds_survived}")
                
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
                
                # Update organism objects' battle stats (for card display)
                winner_org.battle_wins = getattr(winner_org, 'battle_wins', 0) + 1
                loser_org.battle_losses = getattr(loser_org, 'battle_losses', 0) + 1
                
                # 🏆 Competition stats
                winner_org.highlander_kills = getattr(winner_org, 'highlander_kills', 0) + 1
                winner_org.win_streak = getattr(winner_org, 'win_streak', 0) + 1
                if winner_org.win_streak > getattr(winner_org, 'best_win_streak', 0):
                    winner_org.best_win_streak = winner_org.win_streak
                loser_org.win_streak = 0  # Reset streak on death

                # DEBUG: Show what will be absorbed
                transferable_concepts = self._get_transferable_concepts(loser_id, loser_org)
                self.logger.info(f"🧬 ABSORPTION: {winner_id} inheriting {len(transferable_concepts)} concepts from {loser_id}")
                if transferable_concepts:
                    self.logger.info(f"   Concepts: {', '.join(transferable_concepts[:3])}{'...' if len(transferable_concepts) > 3 else ''}")

                self.battle_arena.execute_absorption(winner_org, loser_org, arena_outcome)
                
                # ═══════════════════════════════════════════════════════════════════
                # CRITICAL FIX: Call _absorb_loser for FULL data transfer!
                # execute_absorption only transfers atomic_language concepts (30-50)
                # _absorb_loser transfers: context_memory vocab (8000+), neural weights,
                # experience buffer, and ALL linguistic traits!
                # ═══════════════════════════════════════════════════════════════════
                self._absorb_loser(winner_id, winner_org, loser_id, loser_org)
                self.logger.info(f"📦 FULL ABSORPTION COMPLETE: {winner_id} now has ALL of {loser_id}'s data")
                
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
                # Re-raise arena errors - no silent fallbacks!
                import traceback
                self.logger.error(f"Arena battle FAILED: {e}")
                self.logger.error(traceback.format_exc())
                raise  # Propagate error - fix the root cause!
        
        # ═══════════════════════════════════════════════════════════════
        # FALLBACK: FITNESS-BASED COMPARISON (only if arena not configured)
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
        # Get loser organism from the battle participants
        loser_organism = org1 if loser_id == org1_id else org2
        concepts_to_transfer = self._get_transferable_concepts(loser_id, loser=loser_organism)
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
        
        # Update organism objects' battle stats (for card display)
        winner_org = org1 if winner_id == org1_id else org2
        loser_org = org2 if winner_id == org1_id else org1
        winner_org.battle_wins = getattr(winner_org, 'battle_wins', 0) + 1
        loser_org.battle_losses = getattr(loser_org, 'battle_losses', 0) + 1
        
        # 🏆 Competition stats
        winner_org.highlander_kills = getattr(winner_org, 'highlander_kills', 0) + 1
        winner_org.win_streak = getattr(winner_org, 'win_streak', 0) + 1
        if winner_org.win_streak > getattr(winner_org, 'best_win_streak', 0):
            winner_org.best_win_streak = winner_org.win_streak
        loser_org.win_streak = 0  # Reset streak on death
        
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
                # Transfer ALL concepts - no limit! Winner absorbs everything
                sorted_concepts = sorted(
                    lang.atoms.items(),
                    key=lambda x: x[1].strength,
                    reverse=True
                )
                # NO LIMIT - absorb ALL concepts from the fallen
                concepts = [c for c, _ in sorted_concepts]
        
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
        """
        Winner absorbs loser's best traits.
        
        MISSION 5: Enhanced with linguistic trait inheritance.
        Battle winners now inherit valuable linguistic properties from losers,
        not just concepts but also communication patterns and vocabulary.
        """
        if not winner or not loser:
            return
        
        concepts_absorbed = 0
        linguistic_traits_inherited = 0
        
        # ═══════════════════════════════════════════════════════════════
        # MISSION 5: Absorb atomic language concepts (MASTERY-GATED)
        # ═══════════════════════════════════════════════════════════════
        if hasattr(winner, 'atomic_language') and hasattr(loser, 'atomic_language'):
            winner_lang = winner.atomic_language
            # MASTERY CHECK: Only transfer if winner can acquire
            if hasattr(winner_lang, 'can_acquire') and not winner_lang.can_acquire():
                self.logger.debug(f"[MASTERY_GATE] {winner_id[:8]}: Vocab absorption blocked - at cap")
            else:
                concepts = self._get_transferable_concepts(loser_id, loser)
                for concept in concepts:
                    # Re-check can_acquire for each concept (cap may be reached mid-loop)
                    if hasattr(winner_lang, 'can_acquire') and not winner_lang.can_acquire():
                        self.logger.debug(f"[MASTERY_GATE] {winner_id[:8]}: Stopped absorption at cap")
                        break
                    if hasattr(loser.atomic_language, 'teach_concept'):
                        try:
                            loser.atomic_language.teach_concept(concept, winner_lang)
                            concepts_absorbed += 1
                        except Exception as e:
                            self.logger.debug(f"Concept transfer failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # MISSION 5: Inherit linguistic traits (NEW)
        # Transfer vocabulary, communication patterns, and language stats
        # ═══════════════════════════════════════════════════════════════
        linguistic_inheritance = self._inherit_linguistic_traits(winner, loser)
        linguistic_traits_inherited = linguistic_inheritance.get('traits_inherited', 0)
        
        # 🏆 Transfer skills_mastered from loser to winner
        loser_skills = getattr(loser, 'skills_mastered', set())
        if loser_skills:
            winner_skills = getattr(winner, 'skills_mastered', set())
            winner.skills_mastered = winner_skills | loser_skills
        
        # Absorb configs
        if hasattr(winner, 'config_system') and hasattr(loser, 'config_system'):
            try:
                # FULL ABSORPTION - 100% rate for zero knowledge loss!
                winner.config_system.absorb_config(loser.config_system, absorption_rate=1.0)
            except Exception as e:
                self.logger.debug(f"Config absorption failed: {e}")
        
        self._emit_event('absorption_complete', {
            'winner': winner_id,
            'loser': loser_id,
            'concepts_absorbed': concepts_absorbed,
            'linguistic_traits_inherited': linguistic_traits_inherited,
            'inheritance_details': linguistic_inheritance
        })
        
        # [NEW] Sync updated alliance state if loser was in an alliance
        if loser_id in self.organism_stats:
            alliance_id = self.organism_stats[loser_id].alliance_id
            if alliance_id and alliance_id in self.alliances and hasattr(self, 'alliance_warfare') and self.alliance_warfare:
                alliance = self.alliances[alliance_id]
                self.alliance_warfare.sync_alliance_state(alliance_id, {
                    'members': list(alliance.members),
                    'formation_round': getattr(alliance, 'formation_round', self.round_number),
                    'stability_rounds': max(0, self.round_number - getattr(alliance, 'formation_round', self.round_number)),
                    'confederation_id': None,
                    'war_count': alliance.total_battles_won,
                    'betrayal_count': alliance.betrayal_count
                })
    
    def _inherit_linguistic_traits(self, winner: Any, loser: Any) -> Dict[str, Any]:
        """
        MISSION 5: Inherit linguistic traits from loser to winner.
        
        Transfers:
        - Token sequences (vocabulary exposure)
        - Communication success patterns
        - Language model weights (if neural)
        - Word associations
        
        Returns:
            Dictionary of inheritance results
        """
        result = {
            'traits_inherited': 0,
            'tokens_transferred': 0,
            'patterns_inherited': 0,
            'neural_transfer': False
        }
        
        # Transfer token sequences (vocabulary exposure)
        if hasattr(loser, 'token_sequence') and hasattr(winner, 'token_sequence'):
            loser_tokens = list(getattr(loser, 'token_sequence', []))
            if loser_tokens:
                # Add unique tokens from loser to winner's exposure
                winner_tokens = set(getattr(winner, 'token_sequence', []))
                new_tokens = [t for t in loser_tokens if t not in winner_tokens]
                
                # NO LIMIT - absorb ALL tokens! Big power fluctuations!
                if new_tokens and hasattr(winner, 'token_sequence'):
                    if isinstance(winner.token_sequence, list):
                        winner.token_sequence.extend(new_tokens)
                    elif hasattr(winner.token_sequence, 'extend'):
                        winner.token_sequence.extend(new_tokens)
                    
                    result['tokens_transferred'] = len(new_tokens)
                    result['traits_inherited'] += 1
        
        # Transfer word associations (if context memory available)
        # GROUNDED MODE: Skip vocabulary transfer - organisms must earn vocabulary through mastery
        grounded_enabled = self.config.get('language', {}).get('grounded', {}).get('enabled', False)
        if grounded_enabled:
            self.logger.info(f"🚫 GROUNDED MODE: Vocabulary transfer disabled - organisms must earn words")
        else:
            try:
                winner_id = getattr(winner, 'species_id', getattr(winner, 'organism_id', str(id(winner))))
                loser_id = getattr(loser, 'species_id', getattr(loser, 'organism_id', str(id(loser))))
                
                # Use HighlanderProtocol's wired context_memory (FIXED - don't go through organism)
                context_memory = self.context_memory
                if context_memory and hasattr(context_memory, 'node_word_associations'):
                    # Convert IDs to the format context_memory uses
                    # CRITICAL: Must match language_teacher.py line 398: hash(species_id_str)
                    def normalize_id(org_id):
                        # Language teacher uses: hash(species_id_str) - full hash, can be negative
                        if isinstance(org_id, str):
                            return hash(org_id)
                        return org_id  # Already an int
                    
                    loser_id_int = normalize_id(loser_id)
                    winner_id_int = normalize_id(winner_id)
                    
                    # DEBUG: Log what IDs we're looking for
                    all_stored_ids = list(context_memory.node_word_associations.keys())[:10]
                    self.logger.debug(f"🔍 VOCAB DEBUG: loser={loser_id} → int={loser_id_int}, winner={winner_id} → int={winner_id_int}")
                    self.logger.debug(f"🔍 VOCAB DEBUG: stored IDs sample: {all_stored_ids}")
                    
                    # Get loser's word associations BEFORE they might be cleaned up
                    loser_words = context_memory.node_word_associations.get(loser_id_int, set())
                    winner_words = context_memory.node_word_associations.get(winner_id_int, set())
                    
                    # Only transfer NEW words the winner doesn't already have
                    new_words = loser_words - winner_words
                    
                    self.logger.debug(f"🔍 VOCAB DEBUG: loser has {len(loser_words)} words, winner has {len(winner_words)}, new={len(new_words)}")
                    
                    if new_words:
                        # Transfer only new word associations to winner
                        if winner_id_int not in context_memory.node_word_associations:
                            context_memory.node_word_associations[winner_id_int] = set()
                        
                        # MASTERY CHECK: Limit word transfer to vocab cap
                        if hasattr(winner, 'atomic_language') and hasattr(winner.atomic_language, 'can_acquire'):
                            winner_lang = winner.atomic_language
                            max_vocab = winner_lang._mastery_vocab_sizes[winner_lang._mastery_level] if winner_lang._mastery_level < len(winner_lang._mastery_vocab_sizes) else 10000
                            current_vocab = len(winner_lang.atoms)
                            space_left = max(0, max_vocab - current_vocab)
                            # Only transfer up to remaining cap
                            new_words_list = list(new_words)[:space_left]
                            new_words = set(new_words_list)
                            if space_left == 0:
                                self.logger.debug(f"[MASTERY_GATE] {winner_id[:8]}: Context memory vocab blocked - at cap")
                        
                        if new_words:
                            # Inherit only NEW words from loser (capped by mastery)
                            context_memory.node_word_associations[winner_id_int].update(new_words)
                            
                            result['patterns_inherited'] = len(new_words)
                            result['traits_inherited'] += 1
                            
                            self.logger.info(f"📚 VOCABULARY ABSORBED: {len(new_words)} NEW words transferred to {winner_id[:8]}")
            except Exception as e:
                self.logger.warning(f"Word association transfer failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # FULL BRAIN TRANSFER - Winner absorbs ALL neural weights from loser!
        # ═══════════════════════════════════════════════════════════════════════════
        if (hasattr(loser, 'brain') and loser.brain is not None and
            hasattr(winner, 'brain') and winner.brain is not None):
            try:
                import torch
                
                # Transfer FULL brain weights (100% absorption)
                loser_state = loser.brain.state_dict()
                winner_state = winner.brain.state_dict()
                
                # Blend all weights - 100% from loser (full absorption)
                blend_ratio = 1.0
                for key in loser_state:
                    if key in winner_state and loser_state[key].shape == winner_state[key].shape:
                        winner_state[key] = (
                            (1 - blend_ratio) * winner_state[key] + 
                            blend_ratio * loser_state[key]
                        )
                
                winner.brain.load_state_dict(winner_state, strict=False)
                result['full_brain_transfer'] = True
                result['traits_inherited'] += 1
                
                self.logger.info(f"🧠 FULL BRAIN inheritance: {loser_id} → {winner_id} (100% neural weights absorbed)")
                    
            except Exception as e:
                self.logger.debug(f"Full brain transfer failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # EXPERIENCE BUFFER TRANSFER - Zero data loss! Winner inherits ALL experiences!
        # ═══════════════════════════════════════════════════════════════════════════
        if (hasattr(loser, 'experience_buffer') and loser.experience_buffer is not None and
            hasattr(winner, 'experience_buffer') and winner.experience_buffer is not None):
            try:
                # Get all experiences from loser's buffer
                loser_buffer = loser.experience_buffer.buffer if hasattr(loser.experience_buffer, 'buffer') else []
                
                if loser_buffer:
                    # Transfer Experience objects directly to winner's buffer
                    for exp in loser_buffer:
                        # Experience objects have: state, action, reward, next_state, done, token_sequence, etc.
                        winner.experience_buffer.buffer.append(exp)
                    
                    # Update size tracking
                    winner.experience_buffer.size = len(winner.experience_buffer.buffer)
                    
                    result['experiences_transferred'] = len(loser_buffer)
                    result['traits_inherited'] += 1
                    
                    self.logger.info(f"📚 Experience buffer inheritance: {loser_id} → {winner_id} ({len(loser_buffer)} experiences - ZERO DATA LOSS)")
            except Exception as e:
                self.logger.debug(f"Experience buffer transfer failed: {e}")
        
        # Transfer action/state history for language continuity
        if hasattr(loser, 'action_history') and hasattr(winner, 'action_history'):
            try:
                loser_actions = list(loser.action_history)
                if loser_actions:
                    winner.action_history.extend(loser_actions)
                    result['action_history_transferred'] = len(loser_actions)
                    self.logger.info(f"🎯 Action history inheritance: {loser_id} → {winner_id} ({len(loser_actions)} actions)")
            except Exception as e:
                self.logger.debug(f"Action history transfer failed: {e}")
        
        if hasattr(loser, 'state_history') and hasattr(winner, 'state_history'):
            try:
                loser_states = list(loser.state_history)
                if loser_states:
                    winner.state_history.extend(loser_states)
                    result['state_history_transferred'] = len(loser_states)
            except Exception as e:
                self.logger.debug(f"State history transfer failed: {e}")
        
        # Transfer fitness history for trend analysis
        if hasattr(loser, 'fitness_history') and hasattr(winner, 'fitness_history'):
            try:
                loser_fitness = list(loser.fitness_history) if loser.fitness_history else []
                if loser_fitness:
                    winner.fitness_history.extend(loser_fitness)
                    result['fitness_history_transferred'] = len(loser_fitness)
            except Exception as e:
                self.logger.debug(f"Fitness history transfer failed: {e}")
        
        # Transfer battle stats (accumulated knowledge)
        if hasattr(loser, 'battle_wins') and hasattr(winner, 'battle_wins'):
            winner.battle_wins += loser.battle_wins
            winner.battle_losses += loser.battle_losses
            result['battle_stats_transferred'] = True
        
        return result
    
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
            
            # [NEW] Sync updates to AllianceWarfareSystem (Critical for Illumination Stability)
            if hasattr(self, 'alliance_warfare') and self.alliance_warfare:
                self.alliance_warfare.sync_alliance_state(alliance_id, {
                    'members': list(alliance.members),
                    'formation_round': alliance.formation_round,
                    'stability_rounds': getattr(alliance, 'stability_rounds', self.round_number - alliance.formation_round),
                    'strength': alliance.strength
                })
            
            # Remove dead alliances
            if alliance.strength <= 0 or len(alliance.members) < 2:
                for member in alliance.members:
                    if member in self.organism_stats:
                        self.organism_stats[member].alliance_id = None
                    # 🔧 FIX: Also clear alliance_id on actual organism object
                    if member in organisms and hasattr(organisms[member], 'alliance_id'):
                        organisms[member].alliance_id = None
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
                    formation_time=time.time(),
                    formation_round=self.round_number
                )
                alliance.collective_fitness = org_fitness + fitness_values.get(best_partner, 0)

                # DEBUG: Alliance formation
                partner_fitness = fitness_values.get(best_partner, 0)
                self.logger.info(f"🤝 ALLIANCE FORMED: {alliance_id}")
                self.logger.info(f"   Members: {org_id} (fitness: {org_fitness:.3f}) + {best_partner} (fitness: {partner_fitness:.3f})")
                self.logger.info(f"   Collective fitness: {alliance.collective_fitness:.3f}")
                self.logger.info(f"   Reason: {'solidarity' if abs(org_fitness - partner_fitness) < 0.2 else 'protection'}")

                self.alliances[alliance_id] = alliance
                
                for oid in [org_id, best_partner]:
                    if oid not in self.organism_stats:
                        self.organism_stats[oid] = OrganismStats()
                    self.organism_stats[oid].alliance_id = alliance_id
                    # 🔧 FIX: Also set alliance_id on actual organism object for frontend display
                    if oid in organisms and hasattr(organisms[oid], 'alliance_id'):
                        organisms[oid].alliance_id = alliance_id
                
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
                
                # [NEW] Sync to AllianceWarfareSystem
                if hasattr(self, 'alliance_warfare') and self.alliance_warfare:
                    self.alliance_warfare.sync_alliance_state(alliance_id, {
                        'members': [org_id, best_partner],
                        'formation_round': self.round_number,
                        'stability_rounds': 0,
                        'confederation_id': None,
                        'war_count': 0,
                        'betrayal_count': 0
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
            
            # Teach concepts only if organism can acquire (mastery system check)
            if hasattr(org1, 'atomic_language') and org1.atomic_language:
                if hasattr(org1.atomic_language, 'can_acquire') and org1.atomic_language.can_acquire():
                    for concept in new_concepts_1:
                        try:
                            org1.atomic_language.acquire_concept(
                                concept, source='alliance', strength=0.3
                            )
                        except Exception:
                            pass
                        
            if hasattr(org2, 'atomic_language') and org2.atomic_language:
                if hasattr(org2.atomic_language, 'can_acquire') and org2.atomic_language.can_acquire():
                    for concept in new_concepts_2:
                        try:
                            org2.atomic_language.acquire_concept(
                                concept, source='alliance', strength=0.3
                            )
                        except Exception:
                            pass
                        
        except Exception:
            pass  # Don't break on concept sharing failure
    
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
        
        # Limit champion history
        if len(self.champion_history) > 100:
            self.champion_history = self.champion_history[-100:]
        
        # Checkpoint the champion
        capsule = None
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
        
        # Call champion callback for germination pool
        if self.on_champion_callback and champion and capsule:
            try:
                self.on_champion_callback(champion, capsule)
            except Exception:
                pass  # Don't let callback errors break protocol
        
        return champion_data
    
    def get_current_champion(self) -> Optional[Dict[str, Any]]:
        """
        Get the current champion if one exists.
        
        Returns:
            Champion data dict if in CHAMPION phase with single survivor,
            None otherwise.
        """
        if self.phase == HighlanderPhase.CHAMPION and len(self.active_organisms) == 1:
            champion_id = list(self.active_organisms)[0]
            stats = self.organism_stats.get(champion_id, OrganismStats())
            return {
                'id': champion_id,
                'stats': stats.to_dict(),
                'is_champion': True
            }
        return None
    
    def get_population_count(self) -> int:
        """Get the current active population count."""
        return len(self.active_organisms)
    
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
    
    def analyze_population(self, organisms: Dict[str, Any],
                          get_fitness: Callable[[Any], float]) -> Dict[str, Any]:
        """
        🧬 SKLEARN INTEGRATION: Analyze population for strategic insights.
        
        Phase 4 - Leverage sklearn for evolution intelligence:
        - Fitness landscape clustering
        - Anomaly detection (exceptional organisms)
        - Phenotype diversity analysis
        
        Args:
            organisms: Dict of organism_id -> organism
            get_fitness: Function to get fitness from organism
            
        Returns:
            Analysis results with clusters, anomalies, and recommendations
        """
        try:
            from ..ml_utils import MLAnalyzer, SKLEARN_AVAILABLE
            
            if not SKLEARN_AVAILABLE:
                return {'error': 'sklearn not available', 'available': False}
            
            # Filter to active organisms only
            active_orgs = {
                org_id: org for org_id, org in organisms.items()
                if org_id in self.active_organisms
            }
            
            if len(active_orgs) < 3:
                return {
                    'available': True,
                    'error': 'insufficient_organisms',
                    'count': len(active_orgs)
                }
            
            # Create analyzer with default config
            analyzer = MLAnalyzer({
                'enabled': True,
                'clustering': {'enabled': True, 'algorithm': 'hdbscan', 'min_cluster_size': 3},
                'anomaly_detection': {'enabled': True, 'algorithm': 'isolation_forest'},
                'dimensionality_reduction': {'enabled': False}
            })
            
            # Extract features and perform clustering
            features, organism_ids = analyzer.clusterer.extract_features(active_orgs)
            cluster_result = analyzer.clusterer.cluster(features, organism_ids)
            
            # Perform anomaly detection
            anomaly_result = analyzer.anomaly_detector.detect(features, organism_ids)
            
            # Calculate fitness statistics
            fitness_values = [get_fitness(active_orgs[org_id]) for org_id in organism_ids]
            fitness_array = np.array(fitness_values)
            
            # Enrich with Highlander-specific stats
            stats_features = []
            for org_id in organism_ids:
                stats = self.organism_stats.get(org_id, OrganismStats())
                stats_features.append({
                    'battles_won': stats.battles_won,
                    'battles_lost': stats.battles_lost,
                    'concepts_absorbed': len(stats.concepts_absorbed),
                    'peak_fitness': stats.peak_fitness
                })
            
            analysis = {
                'available': True,
                'organism_count': len(organism_ids),
                'fitness_stats': {
                    'mean': float(np.mean(fitness_array)),
                    'std': float(np.std(fitness_array)),
                    'min': float(np.min(fitness_array)),
                    'max': float(np.max(fitness_array)),
                    'median': float(np.median(fitness_array))
                },
                'clustering': cluster_result.to_dict() if cluster_result else None,
                'anomalies': {
                    'count': len(anomaly_result.anomaly_ids) if anomaly_result else 0,
                    'ids': anomaly_result.anomaly_ids[:10] if anomaly_result else [],
                    'scores': dict(list(anomaly_result.anomaly_scores.items())[:10]) if anomaly_result else {}
                },
                'recommendations': []
            }
            
            # Generate strategic recommendations
            if cluster_result and cluster_result.n_clusters > 1:
                analysis['recommendations'].append(
                    f"Population has {cluster_result.n_clusters} distinct phenotype clusters"
                )
                # Identify dominant cluster
                if cluster_result.cluster_sizes:
                    dominant = max(cluster_result.cluster_sizes.items(), key=lambda x: x[1])
                    analysis['recommendations'].append(
                        f"Cluster {dominant[0]} is dominant with {dominant[1]} members"
                    )
            
            if anomaly_result and len(anomaly_result.anomaly_ids) > 0:
                analysis['recommendations'].append(
                    f"Detected {len(anomaly_result.anomaly_ids)} exceptional organisms (potential champions)"
                )
            
            if fitness_array.std() < 0.1:
                analysis['recommendations'].append(
                    "Low fitness diversity - consider increasing mutation rate"
                )
            elif fitness_array.std() > 0.4:
                analysis['recommendations'].append(
                    "High fitness variance - population is diverging"
                )
            
            return analysis
            
        except ImportError as e:
            return {'error': f'import_error: {e}', 'available': False}
        except Exception as e:
            return {'error': str(e), 'available': False}
    
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
        'survival_threshold': config_system.get('survival_threshold', 0.4),  # Default matches config.json
        'competition_intensity': config_system.get('competition_intensity', 0.2),  # Default matches config.json
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
