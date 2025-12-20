"""
🛸⚔️ DRONE WARFARE ARENA

Top-level integration of drone swarm combat with Highlander system.
Alliance wars are settled in the sky.

When two alliances clash:
1. Each organism becomes a drone pilot
2. Swarm battle determines winner
3. Losing alliance is ABSORBED (Highlander rules)
4. Flight skills, vocabulary, maneuvers transfer

This module bridges:
- AllianceWarfareSystem (who fights)
- SwarmBattle (how they fight)
- HighlanderProtocol (consequences)
- VocabularyTransfer (what's inherited)

The vocabulary organisms evolved becomes their tactical language.
Alliances that developed coherent group vocabulary have coordinated attacks.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)

from .swarm_battle import (
    SwarmBattle,
    BattleConfig,
    BattleStatistics,
    BattleOutcome,
    run_alliance_battle
)
from .drone_adapter import PYFLYT_AVAILABLE


@dataclass
class WarfareConfig:
    """Configuration for alliance drone warfare."""
    # When to use drone combat vs abstract fitness
    min_alliance_size: int = 2          # Need at least 2 drones per side
    max_alliance_size: int = 20         # Performance limit
    
    # Battle parameters
    battle_config: BattleConfig = field(default_factory=BattleConfig)
    
    # Consequences
    absorb_vocabulary: bool = True      # Winner gets loser's words
    absorb_flight_skills: bool = True   # Winner gets flight XP bonus
    skill_transfer_rate: float = 0.3    # 30% of loser's flight XP transfers
    
    # Vocabulary influence on combat
    vocab_coordination_bonus: float = 0.1  # Bonus per shared tactical word
    tactical_words: List[str] = field(default_factory=lambda: [
        'attack', 'defend', 'retreat', 'flank', 'surround',
        'scatter', 'converge', 'chase', 'evade', 'target',
        'sphere', 'line', 'formation', 'split', 'merge',
        'high', 'low', 'fast', 'slow', 'wait',
        'ally', 'enemy', 'danger', 'safe', 'go'
    ])


class DroneWarfareArena:
    """
    Manages drone warfare between alliances.
    
    Integrates with the Highlander system to settle alliance disputes
    through actual drone combat rather than abstract fitness comparisons.
    
    Usage:
        arena = DroneWarfareArena(config, event_emitter, context_memory)
        
        # When AllianceWarfareSystem triggers a conflict:
        winner = arena.resolve_conflict(alliance_a, alliance_b)
        
        # Winner absorbs loser through Highlander
    """
    
    def __init__(self,
                 config: WarfareConfig = None,
                 event_emitter: Any = None,
                 context_memory: Any = None,
                 highlander_protocol: Any = None):
        """
        Args:
            config: Warfare configuration
            event_emitter: For broadcasting events
            context_memory: For vocabulary transfer
            highlander_protocol: For absorption consequences
        """
        self.config = config or WarfareConfig()
        self.event_emitter = event_emitter
        self.context_memory = context_memory
        self.highlander_protocol = highlander_protocol
        
        # Statistics
        self.battles_fought = 0
        self.total_eliminations = 0
        self.vocabulary_transfers = 0
        
        logger.info("🛸⚔️ DroneWarfareArena initialized")
        if not PYFLYT_AVAILABLE:
            logger.warning("⚠️ PyFlyt not available - will use simulated physics")
    
    def _get_alliance_organisms(self, alliance) -> List[Any]:
        """Extract organisms from alliance object."""
        if hasattr(alliance, 'members'):
            if isinstance(alliance.members, dict):
                return list(alliance.members.values())
            return list(alliance.members)
        elif hasattr(alliance, 'organisms'):
            return list(alliance.organisms)
        elif isinstance(alliance, (list, tuple)):
            return list(alliance)
        else:
            logger.warning(f"Unknown alliance type: {type(alliance)}")
            return []
    
    def _calculate_vocab_bonus(self, organisms: List[Any]) -> float:
        """
        Calculate coordination bonus based on shared tactical vocabulary.
        
        Alliances whose members share more tactical words fight better together.
        """
        if not self.context_memory or not organisms:
            return 0.0
        
        shared_tactical = 0
        tactical_set = set(self.config.tactical_words)
        
        # Get words for each organism
        org_words = []
        for org in organisms:
            org_id = getattr(org, 'organism_id', str(id(org)))
            if hasattr(self.context_memory, 'node_word_associations'):
                words = self.context_memory.node_word_associations.get(org_id, set())
                org_words.append(set(words) & tactical_set)
            else:
                org_words.append(set())
        
        if len(org_words) < 2:
            return 0.0
        
        # Count words shared by at least 2 organisms
        from collections import Counter
        all_words = [w for words in org_words for w in words]
        word_counts = Counter(all_words)
        
        for word, count in word_counts.items():
            if count >= 2:  # At least 2 organisms share this word
                shared_tactical += 1
        
        bonus = shared_tactical * self.config.vocab_coordination_bonus
        
        if shared_tactical > 0:
            logger.debug(f"🗣️ Alliance shares {shared_tactical} tactical words: +{bonus:.2f} coordination")
        
        return bonus
    
    def _apply_vocab_bonus(self, adapters: List, bonus: float):
        """Apply vocabulary coordination bonus to damage/health."""
        if bonus <= 0:
            return
        
        for adapter in adapters:
            # Bonus translates to slight health advantage
            adapter.state.health = min(1.0, adapter.state.health + bonus * 0.5)
    
    def _transfer_vocabulary(self, winner_orgs: List, loser_orgs: List):
        """
        Transfer vocabulary from losers to winners.
        
        Highlander Quickening - absorb the fallen's knowledge.
        MASTERY-GATED: Respects vocabulary caps.
        """
        if not self.context_memory:
            return
        
        transferred = 0
        
        for loser in loser_orgs:
            loser_id = getattr(loser, 'organism_id', str(id(loser)))
            
            # Get loser's vocabulary
            if hasattr(self.context_memory, 'node_word_associations'):
                loser_words = self.context_memory.node_word_associations.get(loser_id, set())
            else:
                continue
            
            if not loser_words:
                continue
            
            # Distribute to survivors (weighted by combat performance if available)
            for winner in winner_orgs:
                winner_id = getattr(winner, 'organism_id', str(id(winner)))
                
                # MASTERY CHECK: Only transfer if winner can acquire more vocab
                if hasattr(winner, 'atomic_language'):
                    winner_lang = winner.atomic_language
                    if hasattr(winner_lang, 'can_acquire') and not winner_lang.can_acquire():
                        logger.debug(f"[MASTERY_GATE] {winner_id[:8]}: Drone vocab transfer blocked - at cap")
                        continue
                    
                    # Calculate how many words we can transfer
                    max_vocab = winner_lang._mastery_vocab_sizes[winner_lang._mastery_level] if winner_lang._mastery_level < len(winner_lang._mastery_vocab_sizes) else 20000
                    current_vocab = len(winner_lang.atoms)
                    space_left = max(0, max_vocab - current_vocab)
                    
                    if space_left == 0:
                        continue
                
                # Transfer words
                if hasattr(self.context_memory, 'node_word_associations'):
                    existing = self.context_memory.node_word_associations.get(winner_id, set())
                    new_words = list(loser_words - existing)
                    
                    # Cap at space_left if we have mastery tracking
                    if hasattr(winner, 'atomic_language') and hasattr(winner.atomic_language, '_mastery_level'):
                        new_words = new_words[:space_left]
                    
                    for word in new_words:
                        self.context_memory.node_word_associations[winner_id].add(word)
                        
                        # Update language anchors
                        if hasattr(self.context_memory, 'language_anchors'):
                            self.context_memory.language_anchors[word].add(winner_id)
                        
                        transferred += 1
        
        if transferred > 0:
            logger.info(f"📚 Vocabulary transfer: {transferred} words absorbed by victors")
            self.vocabulary_transfers += transferred
            
            self._emit_event('vocabulary_absorbed', {
                'words_transferred': transferred,
                'winners': [getattr(w, 'organism_id', str(id(w)))[:8] for w in winner_orgs],
                'losers': [getattr(l, 'organism_id', str(id(l)))[:8] for l in loser_orgs]
            })
    
    def _transfer_flight_skills(self, winner_orgs: List, loser_orgs: List, stats: BattleStatistics):
        """
        Transfer flight experience from losers to winners.
        
        The winners absorb combat instincts from the fallen.
        """
        # Calculate total loser flight XP
        loser_xp = 0
        for loser in loser_orgs:
            loser_id = getattr(loser, 'organism_id', str(id(loser)))
            loser_stats = stats.organism_stats.get(loser_id, {})
            loser_xp += loser_stats.get('flight_time', 0)
            loser_xp += loser_stats.get('tags_scored', 0) * 5  # Tags are valuable XP
        
        if loser_xp <= 0:
            return
        
        # Transfer portion to winners
        transfer = loser_xp * self.config.skill_transfer_rate / len(winner_orgs)
        
        for winner in winner_orgs:
            # Boost winner's fitness slightly
            if hasattr(winner, 'fitness'):
                boost = transfer * 0.01  # Small fitness boost per XP
                winner.fitness = min(1.0, winner.fitness + boost)
                
                logger.debug(f"🎯 {getattr(winner, 'organism_id', '')[:8]} absorbed {transfer:.1f} flight XP (+{boost:.3f} fitness)")
        
        self._emit_event('skills_absorbed', {
            'total_xp': loser_xp,
            'xp_per_winner': transfer
        })
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit warfare event."""
        if self.event_emitter:
            try:
                # Standard pattern: event_emitter is callable, not object with .emit()
                from causation_explorer import Event
                event = Event(
                    timestamp=__import__('time').time(),
                    component='drone_warfare',
                    event_type=f'drone_warfare_{event_type}',
                    data=data
                )
                self.event_emitter(event)
            except Exception:
                pass  # Silent failure for event emission
    
    def can_drone_battle(self, alliance_a, alliance_b) -> bool:
        """
        Check if alliances can engage in drone combat.
        
        Requirements:
        - Both alliances have enough members
        - Not too many (performance limit)
        """
        a_orgs = self._get_alliance_organisms(alliance_a)
        b_orgs = self._get_alliance_organisms(alliance_b)
        
        a_size = len(a_orgs)
        b_size = len(b_orgs)
        
        if a_size < self.config.min_alliance_size:
            return False
        if b_size < self.config.min_alliance_size:
            return False
        if a_size > self.config.max_alliance_size:
            return False
        if b_size > self.config.max_alliance_size:
            return False
        
        return True
    
    def resolve_conflict(self, 
                         alliance_a, 
                         alliance_b,
                         reason: str = "territorial") -> Tuple[Any, BattleStatistics]:
        """
        Resolve alliance conflict through drone warfare.
        
        Args:
            alliance_a: First alliance (blue team)
            alliance_b: Second alliance (red team)
            reason: Why they're fighting
            
        Returns:
            Tuple of (winning_alliance, battle_statistics)
        """
        a_orgs = self._get_alliance_organisms(alliance_a)
        b_orgs = self._get_alliance_organisms(alliance_b)
        
        logger.info(f"🛸⚔️ DRONE WARFARE: {len(a_orgs)} vs {len(b_orgs)} ({reason})")
        
        self._emit_event('conflict_start', {
            'alliance_a_size': len(a_orgs),
            'alliance_b_size': len(b_orgs),
            'reason': reason
        })
        
        # Calculate vocabulary bonuses
        a_bonus = self._calculate_vocab_bonus(a_orgs)
        b_bonus = self._calculate_vocab_bonus(b_orgs)
        
        # Run the swarm battle
        battle = SwarmBattle(
            blue_team=a_orgs,
            red_team=b_orgs,
            config=self.config.battle_config,
            event_emitter=self.event_emitter
        )
        
        # Apply vocab bonuses
        self._apply_vocab_bonus(battle.blue_adapters, a_bonus)
        self._apply_vocab_bonus(battle.red_adapters, b_bonus)
        
        # FIGHT
        stats = battle.run()
        battle.close()
        
        self.battles_fought += 1
        self.total_eliminations += stats.total_eliminations
        
        # Determine winner
        if stats.outcome == BattleOutcome.BLUE_WINS:
            winner = alliance_a
            winner_orgs = a_orgs
            loser_orgs = b_orgs
        elif stats.outcome == BattleOutcome.RED_WINS:
            winner = alliance_b
            winner_orgs = b_orgs
            loser_orgs = a_orgs
        else:
            # Draw - higher total health wins
            if stats.blue_total_health >= stats.red_total_health:
                winner = alliance_a
                winner_orgs = a_orgs
                loser_orgs = b_orgs
            else:
                winner = alliance_b
                winner_orgs = b_orgs
                loser_orgs = a_orgs
        
        # Apply Highlander consequences
        if self.config.absorb_vocabulary:
            self._transfer_vocabulary(winner_orgs, loser_orgs)
        
        if self.config.absorb_flight_skills:
            self._transfer_flight_skills(winner_orgs, loser_orgs, stats)
        
        logger.info(f"🏆 VICTOR: {'Alliance A' if winner == alliance_a else 'Alliance B'}")
        
        self._emit_event('conflict_resolved', {
            'outcome': stats.outcome.value,
            'winner_size': len(winner_orgs),
            'loser_size': len(loser_orgs),
            'duration': stats.duration,
            'total_tags': stats.total_tags
        })
        
        return winner, stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get warfare statistics."""
        return {
            'battles_fought': self.battles_fought,
            'total_eliminations': self.total_eliminations,
            'vocabulary_transfers': self.vocabulary_transfers,
            'pyflyt_available': PYFLYT_AVAILABLE
        }


# =============================================================================
# Integration with existing Alliance Warfare System
# =============================================================================

def create_drone_warfare_arena(
    event_emitter=None,
    context_memory=None,
    highlander_protocol=None,
    config: Dict[str, Any] = None
) -> DroneWarfareArena:
    """
    Factory function to create DroneWarfareArena.
    
    Called from unified_entry.py or highlander_protocol.py during initialization.
    """
    warfare_config = WarfareConfig()
    
    if config:
        # Override from config dict
        if 'min_alliance_size' in config:
            warfare_config.min_alliance_size = config['min_alliance_size']
        if 'max_alliance_size' in config:
            warfare_config.max_alliance_size = config['max_alliance_size']
        if 'max_duration' in config:
            warfare_config.battle_config.max_duration = config['max_duration']
    
    return DroneWarfareArena(
        config=warfare_config,
        event_emitter=event_emitter,
        context_memory=context_memory,
        highlander_protocol=highlander_protocol
    )


# =============================================================================
# Testing
# =============================================================================

def test_drone_warfare():
    """Test drone warfare arena."""
    print("🛸⚔️ Testing DroneWarfareArena...")
    
    # Mock organisms
    class MockOrganism:
        def __init__(self, oid):
            self.organism_id = oid
            self.fitness = 0.5
        def decide(self):
            import numpy as np
            return np.random.randint(0, 6)
    
    # Mock alliances
    class MockAlliance:
        def __init__(self, name, size):
            self.name = name
            self.members = [MockOrganism(f"{name}_{i}") for i in range(size)]
    
    alliance_a = MockAlliance("Alpha", 4)
    alliance_b = MockAlliance("Beta", 3)
    
    # Create arena
    config = WarfareConfig()
    config.battle_config.max_duration = 15.0  # Short for testing
    
    arena = DroneWarfareArena(config=config)
    
    # Check if can battle
    if not arena.can_drone_battle(alliance_a, alliance_b):
        print("❌ Cannot drone battle (size requirements not met)")
        return
    
    # Resolve conflict
    winner, stats = arena.resolve_conflict(alliance_a, alliance_b, "test_conflict")
    
    print(f"✅ Battle complete!")
    print(f"   Winner: {winner.name}")
    print(f"   Outcome: {stats.outcome.value}")
    print(f"   Duration: {stats.duration:.1f}s")
    print(f"   Survivors: {stats.blue_survivors} blue, {stats.red_survivors} red")
    
    print(f"\n📊 Arena Stats:")
    print(f"   {arena.get_stats()}")


if __name__ == "__main__":
    test_drone_warfare()
