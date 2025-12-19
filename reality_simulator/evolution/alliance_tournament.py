"""
⚔️🏆💀 ALLIANCE TOURNAMENT SYSTEM - LETHAL Skill-Based Warfare
===============================================================

"In war, the loser doesn't just lose - they DIE."

When alliances go to war, they don't just compare fitness numbers.
They send champions to FIGHT in actual Proton Game tournaments.

⚠️  EVERY BATTLE IS TO THE DEATH ⚠️
- Winner KILLS the loser
- Winner ABSORBS the loser's knowledge, skills, vocabulary
- Winner brings absorbed knowledge back to their alliance

Tournament Format:
- Skirmish → Champion Duel (best of 3, loser dies)
- Border War → Single Elimination (one loss = death)
- Total War → Double Elimination (two losses = death)

"There can be only one."

================================================================================
ATTRIBUTION
================================================================================

🎮 PROTON GAME SYSTEM:
Inspired by "The Game" from Piers Anthony's "Apprentice Adept" series (1980-1990).
The 4x4 game selection grid concept is the creative work of Piers Anthony.

⚔️ ABSORPTION MECHANICS:
Inspired by "Highlander" (1986), dir. Russell Mulcahy, written by Gregory Widen.
"There can be only one."

Author: Convergence Engine Team
Created: 2024-12
"""

import numpy as np
import random
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Optional imports - graceful fallback if not available
try:
    from ..proton_game import ProtonGameArena
    HAS_PROTON_ARENA = True
except ImportError:
    HAS_PROTON_ARENA = False

try:
    from ..arena.gym_runner import GymRunner
    HAS_GYM_RUNNER = True
except ImportError:
    try:
        # Direct import fallback
        from Convergence_Engine.reality_simulator.arena.gym_runner import GymRunner
        HAS_GYM_RUNNER = True
    except ImportError:
        HAS_GYM_RUNNER = False


# =============================================================================
# TOURNAMENT TYPES
# =============================================================================

class TournamentFormat(Enum):
    """How the alliance tournament is structured."""
    SINGLE_ELIMINATION = "single_elimination"  # One loss = out
    DOUBLE_ELIMINATION = "double_elimination"  # Two losses = out
    ROUND_ROBIN = "round_robin"                # Everyone fights everyone
    CHAMPION_DUEL = "champion_duel"            # Top organism from each side


class WarSeverity(Enum):
    """How severe is the conflict? Determines tournament format."""
    SKIRMISH = "skirmish"       # Minor conflict → Champion duel
    BORDER_WAR = "border_war"   # Territory dispute → Single elimination
    TOTAL_WAR = "total_war"     # Existential conflict → Double elimination


# =============================================================================
# TOURNAMENT RESULTS
# =============================================================================

@dataclass
class ChampionRecord:
    """Record of a champion's performance in the tournament."""
    organism_id: str
    alliance_id: str
    is_alive: bool = True  # 💀 Track survival - LETHAL BATTLES
    wins: int = 0
    losses: int = 0
    kills: int = 0  # 💀 How many opponents this champion has killed
    games_played: List[str] = field(default_factory=list)
    total_score: float = 0.0
    skills_unlocked: List[str] = field(default_factory=list)
    absorbed_from: List[str] = field(default_factory=list)  # 🧬 IDs of absorbed opponents
    
    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0


@dataclass
class AllianceTournamentResult:
    """Complete result of an alliance war tournament."""
    tournament_id: str
    alliance_a_id: str
    alliance_b_id: str
    format: TournamentFormat
    severity: WarSeverity
    
    # Results
    winner_alliance: Optional[str] = None
    winning_margin: float = 0.0
    
    # Champion records
    alliance_a_wins: int = 0
    alliance_b_wins: int = 0
    
    champions_a: List[ChampionRecord] = field(default_factory=list)
    champions_b: List[ChampionRecord] = field(default_factory=list)
    
    # 💀 DEATH TRACKING - Lethal battles!
    fallen: List[str] = field(default_factory=list)  # IDs of dead organisms
    total_deaths: int = 0
    alliance_a_deaths: int = 0
    alliance_b_deaths: int = 0
    
    # 🧬 Absorption tracking
    total_absorptions: int = 0
    vocabulary_transferred: int = 0
    
    # Battle log
    battles: List[Dict[str, Any]] = field(default_factory=list)
    
    # Skills/experiences gained (for motor skill retention)
    experiences_recorded: int = 0
    skills_unlocked: List[str] = field(default_factory=list)
    
    @property
    def is_decisive(self) -> bool:
        """Was this a decisive victory?"""
        return self.winning_margin > 0.5


# =============================================================================
# ALLIANCE TOURNAMENT SYSTEM
# =============================================================================

class AllianceTournamentSystem:
    """
    ⚔️🏆 ALLIANCE TOURNAMENT - LETHAL SKILL-BASED WARFARE
    
    Resolves alliance wars through actual Proton Game tournaments.
    ⚠️ BATTLES ARE TO THE DEATH - winner absorbs loser.
    
    Each alliance sends champions. Champions battle in bracket.
    Losers DIE and are absorbed. Winners bring knowledge home.
    
    "There can be only one."
    """
    
    def __init__(self,
                 logger: Optional[logging.Logger] = None,
                 use_real_gym: bool = True,
                 record_experiences: bool = True,
                 # 💀 CRITICAL: Callbacks for lethal operations
                 on_kill: Optional[Callable[[str, str], None]] = None,  # (winner_id, loser_id)
                 on_absorb: Optional[Callable[[str, str], Dict]] = None,  # (winner_id, loser_id) -> result
                 get_organism: Optional[Callable[[str], Any]] = None):  # Get full organism object
        """
        Initialize the LETHAL Alliance Tournament System.
        
        Args:
            logger: Logger instance
            use_real_gym: Use real Gymnasium environments when available
            record_experiences: Record battle experiences to organism replay buffers
            on_kill: Callback(winner_id, loser_id) when organism is killed
            on_absorb: Callback(winner_id, loser_id) -> absorption result dict
            get_organism: Function to get full organism (not just brain)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.use_real_gym = use_real_gym and HAS_GYM_RUNNER
        self.record_experiences = record_experiences
        
        # 💀 LETHAL CALLBACKS
        self.on_kill = on_kill
        self.on_absorb = on_absorb
        self.get_organism = get_organism
        
        # Proton Arena for battles
        self.arena: Optional[Any] = None
        if HAS_PROTON_ARENA:
            self.arena = ProtonGameArena(logger=self.logger)
        
        # Gym Runner for real environments
        self.gym_runner: Optional[Any] = None
        if self.use_real_gym:
            self.gym_runner = GymRunner()
        
        # Tournament tracking
        self.tournament_count = 0
        self.total_battles = 0
        self.total_deaths = 0
        self.total_absorptions = 0
        self.total_experiences_recorded = 0
        
        # Skill tracking - which games organisms have mastered
        self.organism_skills: Dict[str, Set[str]] = defaultdict(set)
        
        # 💀 Kill tracking
        self.kill_counts: Dict[str, int] = defaultdict(int)
        
        # Available games for tournaments
        self.available_games = [
            "cartpole", "lunarlander", "mountaincar", "acrobot",
            "frozenlake", "taxi", "cliffwalking", "blackjack"
        ]
        
        self.logger.info("⚔️🏆💀 LETHAL Alliance Tournament System initialized")
        self.logger.info(f"   Real Gym: {'✅' if self.use_real_gym else '❌'}")
        self.logger.info(f"   Proton Arena: {'✅' if HAS_PROTON_ARENA else '❌'}")
        self.logger.info(f"   Experience Recording: {'✅' if self.record_experiences else '❌'}")
        kill_status = "✅" if self.on_kill else "❌ (deaths will not be registered)"
        absorb_status = "✅" if self.on_absorb else "❌ (no knowledge transfer)"
        self.logger.info(f"   Kill Callback: {kill_status}")
        self.logger.info(f"   Absorb Callback: {absorb_status}")
    
    # =========================================================================
    # MAIN TOURNAMENT API
    # =========================================================================
    
    def resolve_war(self,
                   alliance_a_id: str,
                   alliance_b_id: str,
                   alliance_a_members: List[str],
                   alliance_b_members: List[str],
                   get_organism_brain: Callable[[str], Any],
                   severity: WarSeverity = WarSeverity.BORDER_WAR,
                   max_champions_per_side: int = 4) -> AllianceTournamentResult:
        """
        🏆 RESOLVE A WAR THROUGH TOURNAMENT
        
        This is the main entry point. Called by alliance_warfare.py
        instead of the old fitness-summing method.
        
        Args:
            alliance_a_id: First alliance ID
            alliance_b_id: Second alliance ID  
            alliance_a_members: Organism IDs in alliance A
            alliance_b_members: Organism IDs in alliance B
            get_organism_brain: Function to get organism's neural network
            severity: How severe is the conflict (determines format)
            max_champions_per_side: Maximum champions each alliance sends
            
        Returns:
            AllianceTournamentResult with winner and all battle details
        """
        self.tournament_count += 1
        tournament_id = f"WAR_{self.tournament_count:04d}_{alliance_a_id[:8]}v{alliance_b_id[:8]}"
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"⚔️🏆 ALLIANCE WAR TOURNAMENT: {tournament_id}")
        self.logger.info(f"   Alliance A: {alliance_a_id} ({len(alliance_a_members)} members)")
        self.logger.info(f"   Alliance B: {alliance_b_id} ({len(alliance_b_members)} members)")
        self.logger.info(f"   Severity: {severity.value}")
        self.logger.info(f"{'='*60}\n")
        
        # Determine format based on severity
        format_map = {
            WarSeverity.SKIRMISH: TournamentFormat.CHAMPION_DUEL,
            WarSeverity.BORDER_WAR: TournamentFormat.SINGLE_ELIMINATION,
            WarSeverity.TOTAL_WAR: TournamentFormat.DOUBLE_ELIMINATION
        }
        tournament_format = format_map.get(severity, TournamentFormat.SINGLE_ELIMINATION)
        
        # Initialize result
        result = AllianceTournamentResult(
            tournament_id=tournament_id,
            alliance_a_id=alliance_a_id,
            alliance_b_id=alliance_b_id,
            format=tournament_format,
            severity=severity
        )
        
        # Select champions from each alliance
        champions_a = self._select_champions(
            alliance_a_members, max_champions_per_side, alliance_a_id
        )
        champions_b = self._select_champions(
            alliance_b_members, max_champions_per_side, alliance_b_id
        )
        
        result.champions_a = champions_a
        result.champions_b = champions_b
        
        self.logger.info(f"📋 Champions selected:")
        self.logger.info(f"   Alliance A: {[c.organism_id[:8] for c in champions_a]}")
        self.logger.info(f"   Alliance B: {[c.organism_id[:8] for c in champions_b]}")
        
        # Run tournament based on format
        if tournament_format == TournamentFormat.CHAMPION_DUEL:
            self._run_champion_duel(result, get_organism_brain)
        elif tournament_format == TournamentFormat.SINGLE_ELIMINATION:
            self._run_single_elimination(result, get_organism_brain)
        elif tournament_format == TournamentFormat.DOUBLE_ELIMINATION:
            self._run_double_elimination(result, get_organism_brain)
        else:
            self._run_round_robin(result, get_organism_brain)
        
        # Determine winner
        self._determine_winner(result)
        
        # Log results with DEATH INFO
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"🏆💀 TOURNAMENT COMPLETE: {tournament_id}")
        self.logger.info(f"   Winner: {result.winner_alliance}")
        self.logger.info(f"   Score: {result.alliance_a_wins} - {result.alliance_b_wins}")
        self.logger.info(f"   Margin: {result.winning_margin:.1%}")
        self.logger.info(f"   💀 TOTAL DEATHS: {result.total_deaths}")
        self.logger.info(f"      Alliance A losses: {result.alliance_a_deaths}")
        self.logger.info(f"      Alliance B losses: {result.alliance_b_deaths}")
        self.logger.info(f"   🧬 Absorptions: {result.total_absorptions}")
        self.logger.info(f"   📚 Experiences Recorded: {result.experiences_recorded}")
        self.logger.info(f"{'='*70}\n")
        
        return result
    
    # =========================================================================
    # CHAMPION SELECTION - MASTERY-AWARE
    # =========================================================================
    
    def _get_mastery_level(self, organism_id: str) -> int:
        """Get mastery level for an organism (0-4)."""
        if not self.get_organism:
            return 0
        org = self.get_organism(organism_id)
        if org and hasattr(org, 'atomic_language') and org.atomic_language:
            return getattr(org.atomic_language, '_mastery_level', 0)
        return 0
    
    def _select_champions(self,
                         member_ids: List[str],
                         max_champions: int,
                         alliance_id: str) -> List[ChampionRecord]:
        """
        Select champions from alliance members.
        
        MASTERY-AWARE: Prioritizes higher mastery organisms as champions.
        Better-trained organisms (higher mastery) fight on behalf of alliance.
        """
        # Don't select more champions than we have members
        num_champions = min(len(member_ids), max_champions)
        
        # Get mastery levels for all members
        member_mastery = [(mid, self._get_mastery_level(mid)) for mid in member_ids]
        
        # Sort by mastery level (highest first), with random tiebreaker
        random.shuffle(member_mastery)  # Shuffle first for random tiebreaker
        member_mastery.sort(key=lambda x: x[1], reverse=True)
        
        # Select top mastery organisms as champions
        selected = [mid for mid, level in member_mastery[:num_champions]]
        
        # Log mastery distribution
        mastery_counts = {}
        for mid, level in member_mastery:
            mastery_counts[level] = mastery_counts.get(level, 0) + 1
        self.logger.info(f"   📊 Alliance {alliance_id[:8]} mastery distribution: {mastery_counts}")
        self.logger.info(f"   🎖️ Champion mastery levels: {[self._get_mastery_level(s) for s in selected]}")
        
        return [
            ChampionRecord(organism_id=org_id, alliance_id=alliance_id)
            for org_id in selected
        ]
    
    # =========================================================================
    # TOURNAMENT FORMATS
    # =========================================================================
    
    def _run_champion_duel(self,
                          result: AllianceTournamentResult,
                          get_organism_brain: Callable) -> None:
        """
        🤺💀 CHAMPION DUEL - Top champion from each side fights
        
        Used for minor skirmishes. Quick resolution.
        Best of 3 games. LOSER DIES.
        """
        self.logger.info("\n🤺💀 CHAMPION DUEL - Best of 3 (LOSER DIES)")
        
        if not result.champions_a or not result.champions_b:
            self.logger.warning("Cannot run duel - missing champions")
            return
        
        champion_a = result.champions_a[0]
        champion_b = result.champions_b[0]
        
        games = random.sample(self.available_games, min(3, len(self.available_games)))
        wins_a, wins_b = 0, 0
        
        for game in games:
            battle_result = self._run_battle(
                champion_a, champion_b, game, get_organism_brain
            )
            result.battles.append(battle_result)
            
            if battle_result.get('winner_id') == champion_a.organism_id:
                result.alliance_a_wins += 1
                champion_a.wins += 1
                champion_b.losses += 1
                wins_a += 1
            else:
                result.alliance_b_wins += 1
                champion_b.wins += 1
                champion_a.losses += 1
                wins_b += 1
            
            # Early exit if one side has won 2
            if wins_a >= 2 or wins_b >= 2:
                break
        
        # 💀 THE LOSER OF THE DUEL DIES
        if wins_a > wins_b:
            self._execute_kill(champion_a, champion_b, result)
        else:
            self._execute_kill(champion_b, champion_a, result)
    
    def _mastery_aware_bracket(self, champions: List[ChampionRecord]) -> List[ChampionRecord]:
        """
        Arrange champions for mastery-fair matchups.
        
        WEIGHT CLASS MATCHING: Group by mastery tier, then interleave so
        similar mastery levels fight first. This ensures fair fights:
        - Level 0 vs Level 0 (both have 6 words)
        - Level 1 vs Level 1 (both have 26 words)
        - etc.
        
        Returns rearranged list where adjacent pairs have similar mastery.
        """
        # Get mastery for each champion
        with_mastery = [(c, self._get_mastery_level(c.organism_id)) for c in champions]
        
        # Group by mastery tier
        tiers: Dict[int, List[ChampionRecord]] = {}
        for champ, level in with_mastery:
            if level not in tiers:
                tiers[level] = []
            tiers[level].append(champ)
        
        # Shuffle within each tier for randomness
        for level in tiers:
            random.shuffle(tiers[level])
        
        # Build bracket: pair within same tier first, then cross-tier
        arranged = []
        
        # First, add complete pairs from each tier (same mastery fights)
        for level in sorted(tiers.keys()):
            tier_list = tiers[level]
            # Pair up within tier (take pairs of 2)
            while len(tier_list) >= 2:
                arranged.append(tier_list.pop())
                arranged.append(tier_list.pop())
        
        # Handle remaining unpaired (will fight cross-tier)
        remaining = []
        for level in tiers:
            remaining.extend(tiers[level])
        random.shuffle(remaining)
        arranged.extend(remaining)
        
        # Log mastery distribution
        mastery_dist = {}
        for champ, level in with_mastery:
            mastery_dist[level] = mastery_dist.get(level, 0) + 1
        self.logger.info(f"   🎯 MASTERY WEIGHT CLASSES: {mastery_dist}")
        
        return arranged
    
    def _run_single_elimination(self,
                                result: AllianceTournamentResult,
                                get_organism_brain: Callable) -> None:
        """
        🏆💀 SINGLE ELIMINATION BRACKET - MASTERY-AWARE
        
        All champions from both sides enter bracket.
        One loss = DEATH. Winner absorbs loser. Last alliance standing wins.
        
        WEIGHT CLASS MATCHING: Same mastery levels fight first when possible.
        """
        self.logger.info("\n🏆💀 SINGLE ELIMINATION BRACKET (ONE LOSS = DEATH)")
        
        # Combine all champions
        all_champions = result.champions_a + result.champions_b
        
        # MASTERY-AWARE BRACKET: Arrange so same mastery levels fight first
        all_champions = self._mastery_aware_bracket(all_champions)
        
        # Run bracket until we have a winner
        active = [c for c in all_champions if c.is_alive]
        round_num = 1
        
        while len(active) > 1:
            self.logger.info(f"\n📍 Round {round_num} - {len(active)} warriors remaining")
            
            next_round = []
            
            # Pair up fighters
            for i in range(0, len(active) - 1, 2):
                fighter_a = active[i]
                fighter_b = active[i + 1]
                
                # Log mastery matchup
                level_a = self._get_mastery_level(fighter_a.organism_id)
                level_b = self._get_mastery_level(fighter_b.organism_id)
                fair_match = "✅" if level_a == level_b else f"⚠️ L{level_a}vL{level_b}"
                self.logger.debug(f"   Matchup: {fighter_a.organism_id[:8]} vs {fighter_b.organism_id[:8]} {fair_match}")
                
                # Skip if either is already dead
                if not fighter_a.is_alive or not fighter_b.is_alive:
                    continue
                
                # Select game
                game = random.choice(self.available_games)
                
                # Battle!
                battle_result = self._run_battle(
                    fighter_a, fighter_b, game, get_organism_brain
                )
                result.battles.append(battle_result)
                
                # Winner advances, LOSER DIES
                winner_id = battle_result.get('winner_id')
                if winner_id == fighter_a.organism_id:
                    next_round.append(fighter_a)
                    fighter_a.wins += 1
                    fighter_b.losses += 1
                    
                    # 💀 KILL THE LOSER
                    self._execute_kill(fighter_a, fighter_b, result)
                    
                    if fighter_a.alliance_id == result.alliance_a_id:
                        result.alliance_a_wins += 1
                    else:
                        result.alliance_b_wins += 1
                else:
                    next_round.append(fighter_b)
                    fighter_b.wins += 1
                    fighter_a.losses += 1
                    
                    # 💀 KILL THE LOSER
                    self._execute_kill(fighter_b, fighter_a, result)
                    
                    if fighter_b.alliance_id == result.alliance_a_id:
                        result.alliance_a_wins += 1
                    else:
                        result.alliance_b_wins += 1
            
            # Handle odd number (bye)
            if len(active) % 2 == 1:
                next_round.append(active[-1])
                self.logger.info(f"   {active[-1].organism_id[:8]} gets a bye")
            
            active = next_round
            round_num += 1
        
        # Final champion
        if active:
            final_champion = active[0]
            self.logger.info(f"\n🥇 TOURNAMENT CHAMPION: {final_champion.organism_id[:8]}")
            self.logger.info(f"   From Alliance: {final_champion.alliance_id}")
    
    def _run_double_elimination(self,
                                result: AllianceTournamentResult,
                                get_organism_brain: Callable) -> None:
        """
        💀💀 DOUBLE ELIMINATION - Total War
        
        Two losses = DEATH. More chances, but still lethal.
        Losers bracket gets one more chance before death.
        """
        self.logger.info("\n💀💀 DOUBLE ELIMINATION - TOTAL WAR (TWO LOSSES = DEATH)")
        
        # Combine all champions
        all_champions = result.champions_a + result.champions_b
        random.shuffle(all_champions)
        
        # Winners bracket and losers bracket
        winners_bracket = [c for c in all_champions if c.is_alive]
        losers_bracket: List[ChampionRecord] = []
        
        round_num = 1
        max_rounds = 20  # Safety limit
        
        while len([c for c in winners_bracket + losers_bracket if c.is_alive]) > 1 and round_num < max_rounds:
            self.logger.info(f"\n📍 Round {round_num}")
            alive_winners = [c for c in winners_bracket if c.is_alive]
            alive_losers = [c for c in losers_bracket if c.is_alive]
            self.logger.info(f"   Winners: {len(alive_winners)}, Losers: {len(alive_losers)}")
            
            # Process winners bracket
            if len(alive_winners) >= 2:
                next_winners = []
                dropped = []
                
                for i in range(0, len(alive_winners) - 1, 2):
                    fighter_a = alive_winners[i]
                    fighter_b = alive_winners[i + 1]
                    
                    if not fighter_a.is_alive or not fighter_b.is_alive:
                        continue
                    
                    game = random.choice(self.available_games)
                    battle_result = self._run_battle(
                        fighter_a, fighter_b, game, get_organism_brain
                    )
                    result.battles.append(battle_result)
                    
                    winner_id = battle_result.get('winner_id')
                    if winner_id == fighter_a.organism_id:
                        next_winners.append(fighter_a)
                        dropped.append(fighter_b)  # Goes to losers bracket (1st loss)
                        fighter_a.wins += 1
                        fighter_b.losses += 1
                    else:
                        next_winners.append(fighter_b)
                        dropped.append(fighter_a)  # Goes to losers bracket (1st loss)
                        fighter_b.wins += 1
                        fighter_a.losses += 1
                    
                    # Count alliance wins
                    if winner_id:
                        for c in result.champions_a:
                            if c.organism_id == winner_id:
                                result.alliance_a_wins += 1
                                break
                        for c in result.champions_b:
                            if c.organism_id == winner_id:
                                result.alliance_b_wins += 1
                                break
                
                # Handle bye
                if len(alive_winners) % 2 == 1:
                    survivor = alive_winners[-1]
                    if survivor.is_alive:
                        next_winners.append(survivor)
                
                winners_bracket = next_winners
                losers_bracket.extend(dropped)
            
            # Process losers bracket - 2nd loss = DEATH
            alive_losers = [c for c in losers_bracket if c.is_alive]
            if len(alive_losers) >= 2:
                next_losers = []
                
                for i in range(0, len(alive_losers) - 1, 2):
                    fighter_a = alive_losers[i]
                    fighter_b = alive_losers[i + 1]
                    
                    if not fighter_a.is_alive or not fighter_b.is_alive:
                        continue
                    
                    game = random.choice(self.available_games)
                    battle_result = self._run_battle(
                        fighter_a, fighter_b, game, get_organism_brain
                    )
                    result.battles.append(battle_result)
                    
                    winner_id = battle_result.get('winner_id')
                    if winner_id == fighter_a.organism_id:
                        next_losers.append(fighter_a)
                        # 💀 fighter_b gets 2nd loss = DEATH
                        fighter_a.wins += 1
                        self._execute_kill(fighter_a, fighter_b, result)
                    else:
                        next_losers.append(fighter_b)
                        # 💀 fighter_a gets 2nd loss = DEATH
                        fighter_b.wins += 1
                        self._execute_kill(fighter_b, fighter_a, result)
                
                # Handle bye
                if len(alive_losers) % 2 == 1:
                    survivor = alive_losers[-1]
                    if survivor.is_alive:
                        next_losers.append(survivor)
                
                losers_bracket = next_losers
            
            round_num += 1
        
        # Grand finals
        alive_winners = [c for c in winners_bracket if c.is_alive]
        alive_losers = [c for c in losers_bracket if c.is_alive]
        
        if alive_winners and alive_losers:
            self.logger.info("\n🏆💀 GRAND FINALS (LOSER DIES)")
            game = random.choice(self.available_games)
            battle_result = self._run_battle(
                alive_winners[0], alive_losers[0], game, get_organism_brain
            )
            result.battles.append(battle_result)
            
            # 💀 Loser of grand finals DIES
            winner_id = battle_result.get('winner_id')
            if winner_id == alive_winners[0].organism_id:
                self._execute_kill(alive_winners[0], alive_losers[0], result)
            else:
                self._execute_kill(alive_losers[0], alive_winners[0], result)
    
    def _run_round_robin(self,
                         result: AllianceTournamentResult,
                         get_organism_brain: Callable) -> None:
        """
        🔄💀 ROUND ROBIN - Everyone fights everyone
        
        Most battles, most comprehensive skill testing.
        EVERY LOSS = DEATH. Most brutal format.
        """
        self.logger.info("\n🔄💀 ROUND ROBIN - All vs All (EVERY LOSS = DEATH)")
        
        all_champions = result.champions_a + result.champions_b
        
        for i, fighter_a in enumerate(all_champions):
            for fighter_b in all_champions[i+1:]:
                # Skip if either is already dead
                if not fighter_a.is_alive or not fighter_b.is_alive:
                    continue
                
                game = random.choice(self.available_games)
                
                battle_result = self._run_battle(
                    fighter_a, fighter_b, game, get_organism_brain
                )
                result.battles.append(battle_result)
                
                winner_id = battle_result.get('winner_id')
                if winner_id == fighter_a.organism_id:
                    fighter_a.wins += 1
                    fighter_b.losses += 1
                    
                    # 💀 KILL THE LOSER
                    self._execute_kill(fighter_a, fighter_b, result)
                    
                    if fighter_a.alliance_id == result.alliance_a_id:
                        result.alliance_a_wins += 1
                    else:
                        result.alliance_b_wins += 1
                else:
                    fighter_b.wins += 1
                    fighter_a.losses += 1
                    
                    # 💀 KILL THE LOSER
                    self._execute_kill(fighter_b, fighter_a, result)
                    
                    if fighter_b.alliance_id == result.alliance_a_id:
                        result.alliance_a_wins += 1
                    else:
                        result.alliance_b_wins += 1
    
    # =========================================================================
    # BATTLE EXECUTION
    # =========================================================================
    
    def _run_battle(self,
                   champion_a: ChampionRecord,
                   champion_b: ChampionRecord,
                   game: str,
                   get_organism_brain: Callable) -> Dict[str, Any]:
        """
        ⚔️ RUN A SINGLE BATTLE BETWEEN TWO CHAMPIONS
        
        This is where the REAL gameplay happens!
        Uses Gymnasium environments when available.
        Records experiences for motor skill retention.
        """
        self.total_battles += 1
        
        self.logger.info(f"\n⚔️ BATTLE: {champion_a.organism_id[:8]} vs {champion_b.organism_id[:8]}")
        self.logger.info(f"   Game: {game}")
        
        # Record game played
        champion_a.games_played.append(game)
        champion_b.games_played.append(game)
        
        # Get brains
        brain_a = get_organism_brain(champion_a.organism_id)
        brain_b = get_organism_brain(champion_b.organism_id)
        
        # Run battle
        if self.use_real_gym and self.gym_runner:
            # REAL GYMNASIUM GAMEPLAY!
            result = self._run_real_gym_battle(
                champion_a, champion_b, brain_a, brain_b, game
            )
        elif self.arena and HAS_PROTON_ARENA:
            # Use ProtonGameArena
            result = self._run_arena_battle(
                champion_a, champion_b, brain_a, brain_b, game
            )
        else:
            # NO FAKE SIMULATIONS - FAIL IF NO REAL BATTLE SYSTEM
            error_msg = f"❌ NO REAL BATTLE SYSTEM AVAILABLE for {game}! Need use_real_gym=True or ProtonGameArena"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Record skill unlock
        winner_id = result.get('winner_id')
        if winner_id:
            self.organism_skills[winner_id].add(game)
            
            if winner_id == champion_a.organism_id:
                champion_a.skills_unlocked.append(game)
            else:
                champion_b.skills_unlocked.append(game)
        
        self.logger.info(f"   Winner: {winner_id[:8] if winner_id else 'Draw'}")
        self.logger.info(f"   Score A: {result.get('score_a', 0):.1f}, Score B: {result.get('score_b', 0):.1f}")
        
        return result
    
    def _run_real_gym_battle(self,
                             champion_a: ChampionRecord,
                             champion_b: ChampionRecord,
                             brain_a: Any,
                             brain_b: Any,
                             game: str) -> Dict[str, Any]:
        """
        🎮 RUN BATTLE IN REAL GYMNASIUM ENVIRONMENT
        
        Both organisms play the same game. Higher score wins.
        Experiences are recorded for training!
        """
        # Run organism A - FIXED: use env_spec and learn (not env_name, record_experiences)
        result_a = self.gym_runner.run_organism(
            organism=brain_a,
            env_spec=game,  # FIXED: was env_name
            episodes=3,  # Best of 3 episodes
            learn=self.record_experiences  # FIXED: was record_experiences
        )
        
        # Run organism B  
        result_b = self.gym_runner.run_organism(
            organism=brain_b,
            env_spec=game,  # FIXED: was env_name
            episodes=3,
            learn=self.record_experiences  # FIXED: was record_experiences
        )
        
        score_a = result_a.get('mean_reward', 0.0)
        score_b = result_b.get('mean_reward', 0.0)
        
        # Count experiences recorded
        exp_a = result_a.get('experiences_recorded', 0)
        exp_b = result_b.get('experiences_recorded', 0)
        self.total_experiences_recorded += exp_a + exp_b
        
        # Update champion scores
        champion_a.total_score += score_a
        champion_b.total_score += score_b
        
        # Determine winner
        if score_a > score_b:
            winner_id = champion_a.organism_id
        elif score_b > score_a:
            winner_id = champion_b.organism_id
        else:
            # Tie - random winner
            winner_id = random.choice([champion_a.organism_id, champion_b.organism_id])
        
        return {
            'game': game,
            'champion_a': champion_a.organism_id,
            'champion_b': champion_b.organism_id,
            'score_a': score_a,
            'score_b': score_b,
            'winner_id': winner_id,
            'real_gym': True,
            'experiences_a': exp_a,
            'experiences_b': exp_b,
            'details_a': result_a,
            'details_b': result_b
        }
    
    def _run_arena_battle(self,
                          champion_a: ChampionRecord,
                          champion_b: ChampionRecord,
                          brain_a: Any,
                          brain_b: Any,
                          game: str) -> Dict[str, Any]:
        """
        🎮 RUN BATTLE IN PROTON GAME ARENA
        
        Uses the existing ProtonGameArena infrastructure.
        """
        # Create organism wrappers for arena
        # This bridges the brain to arena's expected interface
        class ArenaOrganism:
            def __init__(self, org_id, brain):
                self.id = org_id
                self.brain = brain
                self.fitness = 0.5  # Default
            
            def get_action(self, state):
                if brain is None:
                    return None
                try:
                    return brain.forward(state)
                except:
                    return None
        
        org_a = ArenaOrganism(champion_a.organism_id, brain_a)
        org_b = ArenaOrganism(champion_b.organism_id, brain_b)
        
        # Run through arena
        try:
            result = self.arena.battle(org_a, org_b, game_name=game)
            
            winner_id = result.get('winner', {}).get('id', None)
            
            return {
                'game': game,
                'champion_a': champion_a.organism_id,
                'champion_b': champion_b.organism_id,
                'score_a': result.get('score_a', 0),
                'score_b': result.get('score_b', 0),
                'winner_id': winner_id,
                'arena_battle': True,
                'arena_result': result
            }
        except Exception as e:
            error_msg = f"❌ ARENA BATTLE FAILED: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    # NOTE: _run_simulated_battle DELETED - NO FAKE SIMULATIONS ALLOWED
    # If real gym or arena unavailable, should raise RuntimeError
    
    # =========================================================================
    # WINNER DETERMINATION
    # =========================================================================
    
    def _determine_winner(self, result: AllianceTournamentResult) -> None:
        """Determine the winning alliance based on tournament results."""
        total_a = result.alliance_a_wins
        total_b = result.alliance_b_wins
        
        total = total_a + total_b
        
        if total == 0:
            result.winner_alliance = None
            result.winning_margin = 0.0
            return
        
        if total_a > total_b:
            result.winner_alliance = result.alliance_a_id
            result.winning_margin = (total_a - total_b) / total
        elif total_b > total_a:
            result.winner_alliance = result.alliance_b_id
            result.winning_margin = (total_b - total_a) / total
        else:
            # Tie - use total scores
            score_a = sum(c.total_score for c in result.champions_a)
            score_b = sum(c.total_score for c in result.champions_b)
            
            if score_a > score_b:
                result.winner_alliance = result.alliance_a_id
            elif score_b > score_a:
                result.winner_alliance = result.alliance_b_id
            else:
                # True tie - random
                result.winner_alliance = random.choice([
                    result.alliance_a_id, result.alliance_b_id
                ])
            
            result.winning_margin = 0.0
        
        # Update experiences recorded
        result.experiences_recorded = self.total_experiences_recorded
        
        # Collect all unlocked skills
        all_skills = set()
        for c in result.champions_a + result.champions_b:
            all_skills.update(c.skills_unlocked)
        result.skills_unlocked = list(all_skills)
    
    # =========================================================================
    # SKILL TRACKING
    # =========================================================================
    
    def get_organism_skills(self, organism_id: str) -> Set[str]:
        """Get skills/games an organism has mastered through tournament victories."""
        return self.organism_skills.get(organism_id, set())
    
    def get_tournament_stats(self) -> Dict[str, Any]:
        """Get overall tournament system statistics."""
        return {
            'total_tournaments': self.tournament_count,
            'total_battles': self.total_battles,
            'total_deaths': self.total_deaths,
            'total_absorptions': self.total_absorptions,
            'total_experiences_recorded': self.total_experiences_recorded,
            'organisms_with_skills': len(self.organism_skills),
            'top_killers': sorted(self.kill_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'real_gym_enabled': self.use_real_gym,
            'arena_available': HAS_PROTON_ARENA
        }
    
    def get_kill_count(self, organism_id: str) -> int:
        """Get how many opponents this organism has killed in war."""
        return self.kill_counts.get(organism_id, 0)
    
    # =========================================================================
    # 💀 KILL & ABSORPTION - THE LETHAL PART
    # =========================================================================
    
    def _execute_kill(self,
                     winner: ChampionRecord,
                     loser: ChampionRecord,
                     result: AllianceTournamentResult) -> None:
        """
        💀 EXECUTE KILL - Loser dies, winner absorbs
        
        This is the lethal part. The loser is:
        1. Marked as dead
        2. Absorbed by the winner
        3. Removed from the game (via callback)
        
        "There can be only one."
        """
        self.logger.info(f"\n💀 EXECUTION: {winner.organism_id[:8]} KILLS {loser.organism_id[:8]}")
        
        # Mark loser as dead
        loser.is_alive = False
        
        # Update counts
        winner.kills += 1
        winner.absorbed_from.append(loser.organism_id)
        self.kill_counts[winner.organism_id] += 1
        self.total_deaths += 1
        result.total_deaths += 1
        result.fallen.append(loser.organism_id)
        
        if loser.alliance_id == result.alliance_a_id:
            result.alliance_a_deaths += 1
        else:
            result.alliance_b_deaths += 1
        
        # 🧬 Perform absorption via callback
        if self.on_absorb:
            try:
                absorption_result = self.on_absorb(winner.organism_id, loser.organism_id)
                if absorption_result:
                    result.total_absorptions += 1
                    self.total_absorptions += 1
                    
                    # Track what was absorbed
                    vocab = absorption_result.get('vocabulary_transferred', 0)
                    result.vocabulary_transferred += vocab
                    
                    skills = absorption_result.get('skills_transferred', [])
                    for skill in skills:
                        winner.skills_unlocked.append(skill)
                    
                    self.logger.info(f"   🧬 Absorption complete!")
                    self.logger.info(f"      Vocabulary: +{vocab} words")
                    self.logger.info(f"      Skills: {skills}")
            except Exception as e:
                self.logger.warning(f"Absorption failed: {e}")
        
        # Trigger kill callback to remove from main system
        if self.on_kill:
            try:
                self.on_kill(winner.organism_id, loser.organism_id)
                self.logger.info(f"   🪦 {loser.organism_id[:8]} removed from game")
            except Exception as e:
                self.logger.warning(f"Kill callback failed: {e}")
        
        self.logger.info(f"   {winner.organism_id[:8]} now has {winner.kills} kills")


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def resolve_alliance_war(alliance_a_id: str,
                        alliance_b_id: str,
                        alliance_a_members: List[str],
                        alliance_b_members: List[str],
                        get_organism_brain: Callable[[str], Any],
                        severity: str = "border_war",
                        on_kill: Optional[Callable[[str, str], None]] = None,
                        on_absorb: Optional[Callable[[str, str], Dict]] = None) -> AllianceTournamentResult:
    """
    Convenience function to resolve an alliance war through LETHAL tournament.
    
    ⚠️ BATTLES ARE TO THE DEATH - losers are killed and absorbed.
    
    Args:
        alliance_a_id: First alliance
        alliance_b_id: Second alliance
        alliance_a_members: Organism IDs in A
        alliance_b_members: Organism IDs in B
        get_organism_brain: Function(org_id) -> neural_network
        severity: "skirmish", "border_war", or "total_war"
        on_kill: Callback(winner_id, loser_id) when kill happens
        on_absorb: Callback(winner_id, loser_id) -> absorption result
    
    Returns:
        AllianceTournamentResult with winner, deaths, and battle details
    """
    severity_map = {
        "skirmish": WarSeverity.SKIRMISH,
        "border_war": WarSeverity.BORDER_WAR,
        "total_war": WarSeverity.TOTAL_WAR
    }
    
    system = AllianceTournamentSystem(
        on_kill=on_kill,
        on_absorb=on_absorb
    )
    return system.resolve_war(
        alliance_a_id=alliance_a_id,
        alliance_b_id=alliance_b_id,
        alliance_a_members=alliance_a_members,
        alliance_b_members=alliance_b_members,
        get_organism_brain=get_organism_brain,
        severity=severity_map.get(severity, WarSeverity.BORDER_WAR)
    )
