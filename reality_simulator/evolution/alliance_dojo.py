"""
🥋 ALLIANCE DOJO SYSTEM - Non-Lethal Training Facility
=======================================================

"If we're positioning them for existential crisis, it's only fair 
to allow them the ability to train themselves."

The Dojo is a safe space where alliance members can:
- Spar against each other in Proton Games
- Practice without lethal consequences
- Build muscle memory through repetition
- Improve before the real wars come

NO DEATHS. NO ABSORPTION. JUST TRAINING.

Organisms still gain:
- Experience points in their replay buffer
- Motor skill development
- Win/loss records (tracked separately as "sparring")
- Skill mastery for specific games

This is how organisms PREPARE for tournament warfare.

================================================================================
ATTRIBUTION
================================================================================

🎮 PROTON GAME SYSTEM:
Inspired by "The Game" from Piers Anthony's "Apprentice Adept" series (1980-1990).
The 4x4 game selection grid concept is the creative work of Piers Anthony.

🥋 DOJO CONCEPT:
Training grounds where warriors practice without mortal stakes.

Author: Convergence Engine Team  
Created: 2024-12
"""

import random
import time
import logging
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Optional imports
try:
    from ..arena.gym_runner import GymRunner
    HAS_GYM_RUNNER = True
except ImportError:
    HAS_GYM_RUNNER = False


# =============================================================================
# TRAINING TYPES
# =============================================================================

class TrainingType(Enum):
    """Types of dojo training sessions."""
    SPARRING = "sparring"          # 1v1 practice match
    DRILL = "drill"                # Solo skill practice
    ROUND_ROBIN = "round_robin"    # Everyone vs everyone
    LADDER = "ladder"              # Continuous ranked matches
    BOOTCAMP = "bootcamp"          # Intensive multi-game session


class SkillFocus(Enum):
    """What skill to focus on during training."""
    REFLEXES = "reflexes"          # CartPole, Acrobot
    PRECISION = "precision"        # LunarLander, Pendulum
    STRATEGY = "strategy"          # FrozenLake, Taxi
    PERSISTENCE = "persistence"    # MountainCar
    RISK_ASSESSMENT = "risk"       # Blackjack


# =============================================================================
# TRAINING RESULTS
# =============================================================================

@dataclass
class SparringResult:
    """Result of a single sparring match."""
    fighter_a_id: str
    fighter_b_id: str
    game: str
    winner_id: Optional[str]
    score_a: float
    score_b: float
    experiences_gained_a: int = 0
    experiences_gained_b: int = 0
    duration_seconds: float = 0.0
    
    @property
    def is_draw(self) -> bool:
        return self.winner_id is None


@dataclass
class DrillResult:
    """Result of a solo training drill."""
    organism_id: str
    game: str
    episodes: int
    mean_score: float
    best_score: float
    worst_score: float
    experiences_gained: int = 0
    improvement: float = 0.0  # vs previous best


@dataclass
class DojoSession:
    """Complete record of a dojo training session."""
    session_id: str
    alliance_id: str
    training_type: TrainingType
    participants: List[str]
    games_played: List[str]
    
    # Results
    sparring_matches: List[SparringResult] = field(default_factory=list)
    drill_results: List[DrillResult] = field(default_factory=list)
    
    # Stats
    total_experiences: int = 0
    total_matches: int = 0
    duration_seconds: float = 0.0
    
    # Leaderboard
    session_rankings: Dict[str, int] = field(default_factory=dict)  # org_id -> points


# =============================================================================
# ALLIANCE DOJO
# =============================================================================

class AllianceDojo:
    """
    🥋 ALLIANCE DOJO - Safe Training Ground for Organisms
    
    Alliance members can train against each other without death.
    Builds skills for actual tournament warfare.
    
    "Train hard, fight easy."
    """
    
    def __init__(self,
                 alliance_id: str,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a dojo for an alliance.
        
        Args:
            alliance_id: The alliance this dojo belongs to
            logger: Logger instance
        """
        self.alliance_id = alliance_id
        self.logger = logger or logging.getLogger(__name__)
        
        # Gym runner for real gameplay
        self.gym_runner: Optional[Any] = None
        if HAS_GYM_RUNNER:
            self.gym_runner = GymRunner()
        
        # Session tracking
        self.session_count = 0
        self.total_sparring_matches = 0
        self.total_drills = 0
        
        # Organism stats (non-lethal, separate from real battles)
        self.sparring_records: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {'wins': 0, 'losses': 0, 'draws': 0}
        )
        self.drill_scores: Dict[str, Dict[str, float]] = defaultdict(dict)  # org_id -> {game: best_score}
        self.training_sessions: Dict[str, int] = defaultdict(int)  # org_id -> session count
        
        # Game pools by skill focus
        self.skill_games = {
            SkillFocus.REFLEXES: ['cartpole', 'acrobot'],
            SkillFocus.PRECISION: ['lunarlander', 'pendulum'],
            SkillFocus.STRATEGY: ['frozenlake', 'taxi', 'cliffwalking'],
            SkillFocus.PERSISTENCE: ['mountaincar'],
            SkillFocus.RISK_ASSESSMENT: ['blackjack']
        }
        
        self.all_games = [
            'cartpole', 'lunarlander', 'mountaincar', 'acrobot',
            'frozenlake', 'taxi', 'blackjack'
        ]
        
        self.logger.info(f"🥋 Alliance Dojo initialized for {alliance_id}")
    
    # =========================================================================
    # MAIN TRAINING API
    # =========================================================================
    
    def run_training_session(self,
                            members: List[str],
                            get_organism_brain: Callable[[str], Any],
                            training_type: TrainingType = TrainingType.SPARRING,
                            skill_focus: Optional[SkillFocus] = None,
                            games: Optional[List[str]] = None,
                            rounds: int = 3) -> DojoSession:
        """
        🥋 RUN A TRAINING SESSION
        
        Main entry point for alliance training.
        
        Args:
            members: List of organism IDs to train
            get_organism_brain: Function to get organism's neural network
            training_type: Type of training session
            skill_focus: Optional skill to focus on (selects appropriate games)
            games: Specific games to use (overrides skill_focus)
            rounds: Number of rounds/matches per participant
            
        Returns:
            DojoSession with all results
        """
        self.session_count += 1
        session_id = f"DOJO_{self.alliance_id[:8]}_{self.session_count:04d}"
        
        start_time = time.time()
        
        # Select games
        if games:
            selected_games = games
        elif skill_focus:
            selected_games = self.skill_games.get(skill_focus, self.all_games)
        else:
            selected_games = self.all_games
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🥋 DOJO SESSION: {session_id}")
        self.logger.info(f"   Alliance: {self.alliance_id}")
        self.logger.info(f"   Type: {training_type.value}")
        self.logger.info(f"   Participants: {len(members)}")
        self.logger.info(f"   Games: {selected_games}")
        self.logger.info(f"{'='*60}\n")
        
        # Initialize session
        session = DojoSession(
            session_id=session_id,
            alliance_id=self.alliance_id,
            training_type=training_type,
            participants=list(members),
            games_played=list(selected_games)
        )
        
        # Run appropriate training
        if training_type == TrainingType.SPARRING:
            self._run_sparring(session, members, get_organism_brain, selected_games, rounds)
        elif training_type == TrainingType.DRILL:
            self._run_drills(session, members, get_organism_brain, selected_games, rounds)
        elif training_type == TrainingType.ROUND_ROBIN:
            self._run_round_robin(session, members, get_organism_brain, selected_games)
        elif training_type == TrainingType.LADDER:
            self._run_ladder(session, members, get_organism_brain, selected_games, rounds)
        elif training_type == TrainingType.BOOTCAMP:
            self._run_bootcamp(session, members, get_organism_brain, selected_games, rounds)
        
        session.duration_seconds = time.time() - start_time
        
        # Calculate session rankings
        self._calculate_rankings(session)
        
        # Update organism stats
        for org_id in members:
            self.training_sessions[org_id] += 1
            # Update organism's dojo_sessions property
            try:
                org = get_organism_brain(org_id)
                if hasattr(org, 'dojo_sessions'):
                    org.dojo_sessions = getattr(org, 'dojo_sessions', 0) + 1
            except Exception:
                pass
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🥋 SESSION COMPLETE: {session_id}")
        self.logger.info(f"   Total Matches: {session.total_matches}")
        self.logger.info(f"   Total Experiences: {session.total_experiences}")
        self.logger.info(f"   Duration: {session.duration_seconds:.1f}s")
        self.logger.info(f"{'='*60}\n")
        
        return session
    
    # =========================================================================
    # TRAINING TYPES
    # =========================================================================
    
    def _run_sparring(self,
                     session: DojoSession,
                     members: List[str],
                     get_organism_brain: Callable,
                     games: List[str],
                     rounds: int) -> None:
        """
        🥊 SPARRING - Random 1v1 matches
        
        Pairs up organisms randomly for practice bouts.
        """
        self.logger.info("🥊 SPARRING MODE")
        
        for round_num in range(rounds):
            self.logger.info(f"\n📍 Round {round_num + 1}/{rounds}")
            
            # Shuffle and pair
            shuffled = list(members)
            random.shuffle(shuffled)
            
            for i in range(0, len(shuffled) - 1, 2):
                fighter_a = shuffled[i]
                fighter_b = shuffled[i + 1]
                game = random.choice(games)
                
                result = self._spar(
                    fighter_a, fighter_b, game, get_organism_brain
                )
                session.sparring_matches.append(result)
                session.total_matches += 1
                session.total_experiences += result.experiences_gained_a + result.experiences_gained_b
                
                self.total_sparring_matches += 1
    
    def _run_drills(self,
                   session: DojoSession,
                   members: List[str],
                   get_organism_brain: Callable,
                   games: List[str],
                   rounds: int) -> None:
        """
        🎯 DRILL MODE - Solo practice
        
        Each organism practices games individually.
        """
        self.logger.info("🎯 DRILL MODE")
        
        for org_id in members:
            for game in games:
                result = self._drill(
                    org_id, game, get_organism_brain, episodes=rounds
                )
                session.drill_results.append(result)
                session.total_experiences += result.experiences_gained
                
                self.total_drills += 1
    
    def _run_round_robin(self,
                        session: DojoSession,
                        members: List[str],
                        get_organism_brain: Callable,
                        games: List[str]) -> None:
        """
        🔄 ROUND ROBIN - Everyone vs Everyone
        
        Each organism spars against every other organism.
        """
        self.logger.info("🔄 ROUND ROBIN MODE")
        
        for i, fighter_a in enumerate(members):
            for fighter_b in members[i + 1:]:
                game = random.choice(games)
                
                result = self._spar(
                    fighter_a, fighter_b, game, get_organism_brain
                )
                session.sparring_matches.append(result)
                session.total_matches += 1
                session.total_experiences += result.experiences_gained_a + result.experiences_gained_b
                
                self.total_sparring_matches += 1
    
    def _run_ladder(self,
                   session: DojoSession,
                   members: List[str],
                   get_organism_brain: Callable,
                   games: List[str],
                   rounds: int) -> None:
        """
        📊 LADDER MODE - Ranked continuous matches
        
        Organisms compete in a ladder. Winners move up, losers move down.
        More matches = more accurate ranking.
        """
        self.logger.info("📊 LADDER MODE")
        
        # Initialize ladder positions
        ladder = list(members)
        random.shuffle(ladder)
        
        for round_num in range(rounds * len(members)):
            # Match adjacent positions
            pos = round_num % (len(ladder) - 1)
            fighter_a = ladder[pos]
            fighter_b = ladder[pos + 1]
            game = random.choice(games)
            
            result = self._spar(
                fighter_a, fighter_b, game, get_organism_brain
            )
            session.sparring_matches.append(result)
            session.total_matches += 1
            session.total_experiences += result.experiences_gained_a + result.experiences_gained_b
            
            # Swap if lower position won
            if result.winner_id == fighter_b:
                ladder[pos], ladder[pos + 1] = ladder[pos + 1], ladder[pos]
            
            self.total_sparring_matches += 1
        
        # Store final ladder positions
        for pos, org_id in enumerate(ladder):
            session.session_rankings[org_id] = len(ladder) - pos  # Higher = better
    
    def _run_bootcamp(self,
                     session: DojoSession,
                     members: List[str],
                     get_organism_brain: Callable,
                     games: List[str],
                     rounds: int) -> None:
        """
        💪 BOOTCAMP - Intensive mixed training
        
        Combination of drills and sparring across all games.
        Maximum skill development.
        """
        self.logger.info("💪 BOOTCAMP MODE")
        
        # Phase 1: Drills on each game
        self.logger.info("\n🎯 Phase 1: Drills")
        for org_id in members:
            for game in games:
                result = self._drill(
                    org_id, game, get_organism_brain, episodes=max(1, rounds // 2)
                )
                session.drill_results.append(result)
                session.total_experiences += result.experiences_gained
        
        # Phase 2: Round robin sparring
        self.logger.info("\n🥊 Phase 2: Sparring")
        for i, fighter_a in enumerate(members):
            for fighter_b in members[i + 1:]:
                game = random.choice(games)
                
                result = self._spar(
                    fighter_a, fighter_b, game, get_organism_brain
                )
                session.sparring_matches.append(result)
                session.total_matches += 1
                session.total_experiences += result.experiences_gained_a + result.experiences_gained_b
                
                self.total_sparring_matches += 1
        
        # Phase 3: Final drill assessment
        self.logger.info("\n🎯 Phase 3: Final Assessment")
        for org_id in members:
            game = random.choice(games)
            result = self._drill(
                org_id, game, get_organism_brain, episodes=rounds
            )
            session.drill_results.append(result)
            session.total_experiences += result.experiences_gained
    
    # =========================================================================
    # CORE BATTLE METHODS
    # =========================================================================
    
    def _spar(self,
             fighter_a: str,
             fighter_b: str,
             game: str,
             get_organism_brain: Callable) -> SparringResult:
        """
        🥊 RUN A SINGLE SPARRING MATCH
        
        Non-lethal practice bout between two organisms.
        """
        self.logger.info(f"\n🥊 SPAR: {fighter_a[:8]} vs {fighter_b[:8]} ({game})")
        
        start_time = time.time()
        
        brain_a = get_organism_brain(fighter_a)
        brain_b = get_organism_brain(fighter_b)
        
        # Run each fighter in the game
        if self.gym_runner:
            # Real Gymnasium gameplay
            result_a = self.gym_runner.run_organism(
                organism=brain_a,
                env_spec=game,
                episodes=3,
                learn=True
            )
            result_b = self.gym_runner.run_organism(
                organism=brain_b,
                env_spec=game,
                episodes=3,
                learn=True
            )
            
            score_a = result_a.mean_reward if hasattr(result_a, 'mean_reward') else result_a.get('mean_reward', 0)
            score_b = result_b.mean_reward if hasattr(result_b, 'mean_reward') else result_b.get('mean_reward', 0)
            exp_a = result_a.experiences_recorded if hasattr(result_a, 'experiences_recorded') else result_a.get('experiences_recorded', 0)
            exp_b = result_b.experiences_recorded if hasattr(result_b, 'experiences_recorded') else result_b.get('experiences_recorded', 0)
        else:
            # NO FAKE SIMULATIONS - FAIL IF NO REAL GYM
            error_msg = f"❌ NO GYM RUNNER AVAILABLE for sparring! Cannot simulate scores."
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Determine winner
        if abs(score_a - score_b) < 0.01:
            winner_id = None  # Draw
            self.sparring_records[fighter_a]['draws'] += 1
            self.sparring_records[fighter_b]['draws'] += 1
        elif score_a > score_b:
            winner_id = fighter_a
            self.sparring_records[fighter_a]['wins'] += 1
            self.sparring_records[fighter_b]['losses'] += 1
        else:
            winner_id = fighter_b
            self.sparring_records[fighter_b]['wins'] += 1
            self.sparring_records[fighter_a]['losses'] += 1
        
        result = SparringResult(
            fighter_a_id=fighter_a,
            fighter_b_id=fighter_b,
            game=game,
            winner_id=winner_id,
            score_a=score_a,
            score_b=score_b,
            experiences_gained_a=exp_a,
            experiences_gained_b=exp_b,
            duration_seconds=time.time() - start_time
        )
        
        self.logger.info(f"   Winner: {winner_id[:8] if winner_id else 'DRAW'}")
        self.logger.info(f"   Scores: {score_a:.1f} vs {score_b:.1f}")
        
        return result
    
    def _drill(self,
              organism_id: str,
              game: str,
              get_organism_brain: Callable,
              episodes: int = 5) -> DrillResult:
        """
        🎯 RUN A SOLO DRILL
        
        Individual practice on a specific game.
        """
        self.logger.info(f"\n🎯 DRILL: {organism_id[:8]} practicing {game}")
        
        brain = get_organism_brain(organism_id)
        
        # Get previous best for improvement tracking
        prev_best = self.drill_scores[organism_id].get(game, 0)
        
        if self.gym_runner:
            # Real Gymnasium practice
            result = self.gym_runner.run_organism(
                organism=brain,
                env_spec=game,
                episodes=episodes,
                learn=True
            )
            
            mean_score = result.mean_reward if hasattr(result, 'mean_reward') else result.get('mean_reward', 0)
            best_score = result.max_reward if hasattr(result, 'max_reward') else result.get('max_reward', 0)
            worst_score = result.min_reward if hasattr(result, 'min_reward') else result.get('min_reward', 0)
            exp_gained = result.experiences_recorded if hasattr(result, 'experiences_recorded') else result.get('experiences_recorded', 0)
        else:
            # NO FAKE SIMULATIONS - FAIL IF NO REAL GYM
            error_msg = f"❌ NO GYM RUNNER AVAILABLE for drill! Cannot simulate scores."
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Update personal best
        if best_score > prev_best:
            self.drill_scores[organism_id][game] = best_score
        
        improvement = best_score - prev_best if prev_best > 0 else 0
        
        drill_result = DrillResult(
            organism_id=organism_id,
            game=game,
            episodes=episodes,
            mean_score=mean_score,
            best_score=best_score,
            worst_score=worst_score,
            experiences_gained=exp_gained,
            improvement=improvement
        )
        
        self.logger.info(f"   Mean: {mean_score:.1f}, Best: {best_score:.1f}")
        if improvement > 0:
            self.logger.info(f"   📈 NEW PERSONAL BEST! (+{improvement:.1f})")
        
        return drill_result
    
    # =========================================================================
    # STATISTICS & RANKINGS
    # =========================================================================
    
    def _calculate_rankings(self, session: DojoSession) -> None:
        """Calculate session rankings based on performance."""
        points = defaultdict(int)
        
        # Points from sparring
        for match in session.sparring_matches:
            if match.winner_id:
                points[match.winner_id] += 3
            else:
                points[match.fighter_a_id] += 1
                points[match.fighter_b_id] += 1
        
        # Points from drills (based on score)
        for drill in session.drill_results:
            points[drill.organism_id] += int(drill.mean_score / 10)
        
        session.session_rankings = dict(points)
    
    def get_sparring_record(self, organism_id: str) -> Dict[str, int]:
        """Get an organism's sparring win/loss record."""
        return dict(self.sparring_records[organism_id])
    
    def get_drill_scores(self, organism_id: str) -> Dict[str, float]:
        """Get an organism's best drill scores per game."""
        return dict(self.drill_scores[organism_id])
    
    def get_training_count(self, organism_id: str) -> int:
        """Get how many training sessions an organism has attended."""
        return self.training_sessions[organism_id]
    
    def get_dojo_stats(self) -> Dict[str, Any]:
        """Get overall dojo statistics."""
        return {
            'alliance_id': self.alliance_id,
            'total_sessions': self.session_count,
            'total_sparring_matches': self.total_sparring_matches,
            'total_drills': self.total_drills,
            'organisms_trained': len(self.training_sessions),
            'real_gym_available': self.gym_runner is not None
        }
    
    def get_leaderboard(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get a leaderboard of organisms by training performance.
        
        Returns list of (organism_id, stats) sorted by sparring wins.
        """
        leaderboard = []
        
        for org_id, record in self.sparring_records.items():
            total = record['wins'] + record['losses'] + record['draws']
            win_rate = record['wins'] / total if total > 0 else 0
            
            leaderboard.append((org_id, {
                'wins': record['wins'],
                'losses': record['losses'],
                'draws': record['draws'],
                'total_matches': total,
                'win_rate': win_rate,
                'training_sessions': self.training_sessions[org_id],
                'games_practiced': len(self.drill_scores[org_id])
            }))
        
        # Sort by wins, then win rate
        leaderboard.sort(key=lambda x: (x[1]['wins'], x[1]['win_rate']), reverse=True)
        
        return leaderboard


# =============================================================================
# DOJO MANAGER - For Multiple Alliances
# =============================================================================

class DojoManager:
    """
    Manages dojos for all alliances in the system.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.dojos: Dict[str, AllianceDojo] = {}
    
    def get_or_create_dojo(self, alliance_id: str) -> AllianceDojo:
        """Get existing dojo or create new one for alliance."""
        if alliance_id not in self.dojos:
            self.dojos[alliance_id] = AllianceDojo(alliance_id, self.logger)
        return self.dojos[alliance_id]
    
    def run_alliance_training(self,
                             alliance_id: str,
                             members: List[str],
                             get_organism_brain: Callable,
                             training_type: str = "sparring",
                             rounds: int = 3) -> DojoSession:
        """
        Convenience method to run training for an alliance.
        
        Args:
            alliance_id: Alliance to train
            members: Organism IDs
            get_organism_brain: Function to get brains
            training_type: "sparring", "drill", "round_robin", "ladder", "bootcamp"
            rounds: Number of rounds
        """
        type_map = {
            'sparring': TrainingType.SPARRING,
            'drill': TrainingType.DRILL,
            'round_robin': TrainingType.ROUND_ROBIN,
            'ladder': TrainingType.LADDER,
            'bootcamp': TrainingType.BOOTCAMP
        }
        
        dojo = self.get_or_create_dojo(alliance_id)
        return dojo.run_training_session(
            members=members,
            get_organism_brain=get_organism_brain,
            training_type=type_map.get(training_type, TrainingType.SPARRING),
            rounds=rounds
        )
    
    def get_global_leaderboard(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get leaderboard across all alliances."""
        all_records = {}
        
        for dojo in self.dojos.values():
            for org_id, stats in dojo.get_leaderboard():
                if org_id not in all_records:
                    all_records[org_id] = stats.copy()
                    all_records[org_id]['alliance'] = dojo.alliance_id
                else:
                    # Merge stats
                    all_records[org_id]['wins'] += stats['wins']
                    all_records[org_id]['losses'] += stats['losses']
                    all_records[org_id]['draws'] += stats['draws']
                    all_records[org_id]['total_matches'] += stats['total_matches']
                    all_records[org_id]['training_sessions'] += stats['training_sessions']
        
        # Recalculate win rates
        for stats in all_records.values():
            total = stats['wins'] + stats['losses'] + stats['draws']
            stats['win_rate'] = stats['wins'] / total if total > 0 else 0
        
        # Sort
        leaderboard = list(all_records.items())
        leaderboard.sort(key=lambda x: (x[1]['wins'], x[1]['win_rate']), reverse=True)
        
        return leaderboard
