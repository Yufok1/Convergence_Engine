"""
🎮 PROTON GAME ARENA - Apprentice Adept Inspired Competition System

================================================================================
ATTRIBUTION & ACKNOWLEDGMENT
================================================================================

🎮 GAME SELECTION SYSTEM:
The Proton Game Arena is inspired by and based on "The Game" from Piers Anthony's
"Apprentice Adept" science fiction/fantasy series (1980-1990).

The core concept of the 4x4 game selection grid:
    - Rows: PHYSICAL, MENTAL, CHANCE, ARTS
    - Columns: NAKED, TOOL, MACHINE, ANIMAL

...is the creative work of Piers Anthony, first introduced in "Split Infinity" (1980).

For the original, read:
    - "Split Infinity" (1980)
    - "Blue Adept" (1981) 
    - "Juxtaposition" (1982)

⚔️ ABSORPTION BATTLE SYSTEM:
The "winner absorbs the loser's power" battle mechanic is inspired by the film
"Highlander" (1986), directed by Russell Mulcahy, written by Gregory Widen.

    "There can be only one."
    
The Quickening - where an immortal gains the knowledge, skills, and power of
a defeated opponent - directly inspired our neural/concept/trait absorption system.

We acknowledge these creative works that shaped this implementation.
    
The Butterfly System / Convergence Engine uses these frameworks to teach reasoning
through gamified competition between AI organisms.

================================================================================

The selection process itself teaches:
- Self-awareness (knowing own strengths)
- Opponent modeling (theory of mind)
- Strategic communication (language negotiation)
- Categorical reasoning (grid navigation)
- Trade-off analysis (every choice has consequences)

Architecture:
    1. Primary 4x4 Grid: CHALLENGE TYPE × RESOURCE TYPE
    2. Secondary Subgrids: Narrowing to specific game categories
    3. Final 3x3 Grid: Specific game variants
    4. Gym Battle: Actual competition in selected environment
    5. Consequence: Resource/fitness transfer, survival

Author: The Butterfly System / Convergence Engine
Original Concept: Piers Anthony's "Apprentice Adept" Series (1980-1990)
"""

import random
import logging
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable
from enum import Enum, auto
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS - The Fundamental Categories
# =============================================================================

class ChallengeType(Enum):
    """Row categories - Nature of the challenge"""
    PHYSICAL = "physical"   # Body, speed, endurance, reflexes
    MENTAL = "mental"       # Strategy, puzzle, planning, memory
    CHANCE = "chance"       # Luck, randomness, probability
    ARTS = "arts"          # Creativity, expression, language, aesthetics


class ResourceType(Enum):
    """Column categories - Available resources/augmentation"""
    NAKED = "naked"         # Unassisted, raw ability only
    TOOL = "tool"           # Simple tools, extensions of self
    MACHINE = "machine"     # Complex machines, automation
    ANIMAL = "animal"       # Living partners, symbiosis


class GameDifficulty(Enum):
    """Difficulty tiers for tournament progression"""
    NOVICE = 1
    APPRENTICE = 2
    JOURNEYMAN = 3
    EXPERT = 4
    MASTER = 5
    GRANDMASTER = 6


# =============================================================================
# GAME DEFINITIONS - Mapping Grid Intersections to Gym Environments
# =============================================================================

@dataclass
class GameDefinition:
    """Definition of a game that can be played in the arena."""
    name: str
    gym_env: str                          # Gymnasium environment spec
    challenge: ChallengeType
    resource: ResourceType
    difficulty: GameDifficulty
    description: str
    min_episodes: int = 3                 # Minimum episodes for fair evaluation
    max_steps: Optional[int] = None       # Step limit per episode
    score_metric: str = "mean_reward"     # How to determine winner
    tags: List[str] = field(default_factory=list)
    
    # Trait bonuses - organisms with these traits get advantages
    favored_traits: Dict[str, float] = field(default_factory=dict)


# The Master Game Grid
GAME_GRID: Dict[Tuple[ChallengeType, ResourceType], List[GameDefinition]] = {
    # =========================================================================
    # PHYSICAL CHALLENGES
    # =========================================================================
    (ChallengeType.PHYSICAL, ResourceType.NAKED): [
        GameDefinition(
            name="Balance Beam",
            gym_env="CartPole-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.NOVICE,
            description="Pure balance - keep the pole upright with body alone",
            tags=["balance", "reflexes", "endurance"],
            favored_traits={"stability": 0.2, "reflexes": 0.15}
        ),
        GameDefinition(
            name="Mountain Climb",
            gym_env="MountainCar-v0",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Build momentum to climb - raw physics intuition",
            tags=["momentum", "timing", "persistence"],
            favored_traits={"persistence": 0.2, "energy_efficiency": 0.1}
        ),
        GameDefinition(
            name="Gymnast Swing",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Swing up using only body momentum",
            tags=["coordination", "timing", "physics"],
            favored_traits={"coordination": 0.25, "timing": 0.15}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.TOOL): [
        GameDefinition(
            name="Lunar Landing",
            gym_env="LunarLander-v3",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Land spacecraft using thrusters - tool-assisted precision",
            tags=["precision", "fuel_management", "spatial"],
            favored_traits={"precision": 0.2, "resource_management": 0.15}
        ),
        GameDefinition(
            name="Pendulum Control",
            gym_env="Pendulum-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Control pendulum with continuous force application",
            tags=["control", "continuous", "balance"],
            favored_traits={"fine_control": 0.2, "patience": 0.1}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.MACHINE): [
        GameDefinition(
            name="Road Racing",
            gym_env="CarRacing-v3",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.EXPERT,
            description="Race car around track - machine mastery",
            tags=["racing", "vision", "speed"],
            favored_traits={"speed": 0.2, "spatial_awareness": 0.15}
        ),
        GameDefinition(
            name="Endurance Rally",
            gym_env="ALE/Enduro-v5",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.EXPERT,
            description="Endless racing endurance - outlast opponents",
            tags=["endurance", "racing", "atari"],
            favored_traits={"endurance": 0.25, "focus": 0.1}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.ANIMAL): [
        GameDefinition(
            name="Ant Colony",
            gym_env="Ant-v4",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Control multi-legged creature - embodied symbiosis",
            tags=["locomotion", "coordination", "mujoco"],
            favored_traits={"multi_limb_coord": 0.3, "adaptability": 0.1}
        ),
        GameDefinition(
            name="Cheetah Sprint",
            gym_env="HalfCheetah-v4",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Run as fast as possible - animal speed mastery",
            tags=["speed", "locomotion", "mujoco"],
            favored_traits={"speed": 0.25, "efficiency": 0.15}
        ),
        GameDefinition(
            name="Bipedal Walk",
            gym_env="BipedalWalker-v3",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.EXPERT,
            description="Walk on two legs across terrain",
            tags=["balance", "locomotion", "box2d"],
            favored_traits={"balance": 0.2, "adaptability": 0.15}
        ),
    ],
    
    # =========================================================================
    # MENTAL CHALLENGES
    # =========================================================================
    (ChallengeType.MENTAL, ResourceType.NAKED): [
        GameDefinition(
            name="Frozen Lake",
            gym_env="FrozenLake-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.NOVICE,
            description="Navigate slippery ice - pure planning",
            tags=["planning", "grid", "navigation"],
            favored_traits={"planning": 0.2, "caution": 0.1}
        ),
        GameDefinition(
            name="Cliff Walking",
            gym_env="CliffWalking-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Navigate cliffs - risk assessment",
            tags=["risk", "planning", "grid"],
            favored_traits={"risk_assessment": 0.25, "patience": 0.1}
        ),
    ],
    
    (ChallengeType.MENTAL, ResourceType.TOOL): [
        GameDefinition(
            name="Blackjack",
            gym_env="Blackjack-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Card counting and probability - tool-assisted calculation",
            tags=["cards", "probability", "counting"],
            favored_traits={"memory": 0.2, "probability_sense": 0.15}
        ),
        GameDefinition(
            name="Taxi Navigation",
            gym_env="Taxi-v3",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Optimal pickup/dropoff routing",
            tags=["routing", "optimization", "planning"],
            favored_traits={"optimization": 0.2, "spatial_memory": 0.1}
        ),
    ],
    
    (ChallengeType.MENTAL, ResourceType.MACHINE): [
        GameDefinition(
            name="Brick Breaker",
            gym_env="ALE/Breakout-v5",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Strategic brick destruction - machine-assisted angles",
            tags=["angles", "prediction", "atari"],
            favored_traits={"prediction": 0.2, "pattern_recognition": 0.15}
        ),
        GameDefinition(
            name="Space Defense",
            gym_env="ALE/SpaceInvaders-v5",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Defend against waves - tactical positioning",
            tags=["tactics", "defense", "atari"],
            favored_traits={"tactical_thinking": 0.2, "timing": 0.1}
        ),
        GameDefinition(
            name="Pac Maze",
            gym_env="ALE/MsPacman-v5",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.EXPERT,
            description="Navigate maze while avoiding ghosts",
            tags=["maze", "evasion", "collection"],
            favored_traits={"spatial_awareness": 0.2, "evasion": 0.15}
        ),
    ],
    
    (ChallengeType.MENTAL, ResourceType.ANIMAL): [
        # These are custom games we can implement
        GameDefinition(
            name="Predator Evasion",
            gym_env="predator_prey",  # Custom env
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.EXPERT,
            description="Evade predator using prey instincts",
            tags=["evasion", "survival", "custom"],
            favored_traits={"survival_instinct": 0.3, "speed": 0.1}
        ),
        GameDefinition(
            name="Cooperation Test",
            gym_env="cooperation_game",  # Custom env
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Work with another organism to achieve goal",
            tags=["cooperation", "communication", "custom"],
            favored_traits={"cooperation": 0.3, "communication": 0.2}
        ),
    ],
    
    # =========================================================================
    # CHANCE CHALLENGES
    # =========================================================================
    (ChallengeType.CHANCE, ResourceType.NAKED): [
        GameDefinition(
            name="Coin Fate",
            gym_env="coin_flip",  # Custom simple env
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.NOVICE,
            description="Pure luck - coin flip",
            min_episodes=10,  # Need more episodes for fair chance eval
            tags=["luck", "pure_chance"],
            favored_traits={"luck": 0.5}  # High luck bonus
        ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.TOOL): [
        GameDefinition(
            name="Card Draw",
            gym_env="Blackjack-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Cards with skill - luck meets strategy",
            min_episodes=10,
            tags=["cards", "luck_skill"],
            favored_traits={"luck": 0.2, "probability_sense": 0.15}
        ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.MACHINE): [
        GameDefinition(
            name="Slot Challenge",
            gym_env="ALE/Casino-v5",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.APPRENTICE,
            description="Machine gambling - manage the odds",
            min_episodes=5,
            tags=["gambling", "machine", "atari"],
            favored_traits={"luck": 0.3, "risk_tolerance": 0.1}
        ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.ANIMAL): [
        GameDefinition(
            name="Genetic Lottery",
            gym_env="mutation_roulette",  # Custom
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Random mutations - genetic fate",
            min_episodes=5,
            tags=["genetics", "mutation", "custom"],
            favored_traits={"genetic_stability": 0.2, "luck": 0.2}
        ),
    ],
    
    # =========================================================================
    # ARTS CHALLENGES (Language/Creative - Your System's Specialty!)
    # =========================================================================
    (ChallengeType.ARTS, ResourceType.NAKED): [
        GameDefinition(
            name="Word Coherence",
            gym_env="language_coherence",  # Custom - uses your language system
            challenge=ChallengeType.ARTS,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Generate coherent text - pure language ability",
            tags=["language", "coherence", "generation"],
            favored_traits={"vocabulary_size": 0.2, "coherence": 0.25}
        ),
        GameDefinition(
            name="Concept Association",
            gym_env="concept_linking",  # Custom
            challenge=ChallengeType.ARTS,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Link related concepts - semantic understanding",
            tags=["concepts", "semantics", "knowledge"],
            favored_traits={"concept_breadth": 0.2, "association_strength": 0.15}
        ),
    ],
    
    (ChallengeType.ARTS, ResourceType.TOOL): [
        GameDefinition(
            name="Vocabulary Battle",
            gym_env="vocabulary_duel",  # Custom
            challenge=ChallengeType.ARTS,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Use vocabulary tools to express complex ideas",
            tags=["vocabulary", "expression", "tools"],
            favored_traits={"vocabulary_size": 0.25, "expression": 0.15}
        ),
    ],
    
    (ChallengeType.ARTS, ResourceType.MACHINE): [
        GameDefinition(
            name="Response Quality",
            gym_env="dialogue_quality",  # Custom
            challenge=ChallengeType.ARTS,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.EXPERT,
            description="Generate high-quality responses - full language system",
            tags=["dialogue", "quality", "generation"],
            favored_traits={"language_head_strength": 0.3, "coherence": 0.2}
        ),
    ],
    
    (ChallengeType.ARTS, ResourceType.ANIMAL): [
        GameDefinition(
            name="Cross-Organism Dialogue",
            gym_env="inter_organism_chat",  # Custom
            challenge=ChallengeType.ARTS,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Communicate effectively with another organism",
            tags=["communication", "dialogue", "social"],
            favored_traits={"communication": 0.3, "empathy": 0.2}
        ),
        GameDefinition(
            name="Alliance Poetry",
            gym_env="collaborative_creation",  # Custom
            challenge=ChallengeType.ARTS,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.GRANDMASTER,
            description="Create together with alliance members",
            tags=["collaboration", "creativity", "alliance"],
            favored_traits={"creativity": 0.25, "cooperation": 0.2}
        ),
    ],
}


# =============================================================================
# SELECTION STATE - Tracks the game selection process
# =============================================================================

@dataclass
class SelectionState:
    """State of the game selection process between two organisms."""
    organism_a_id: str
    organism_b_id: str
    
    # Who chooses what (randomly assigned)
    row_chooser: str = ""      # Organism ID who chooses row (challenge type)
    column_chooser: str = ""   # Organism ID who chooses column (resource type)
    
    # Choices made
    challenge_choice: Optional[ChallengeType] = None
    resource_choice: Optional[ResourceType] = None
    
    # Subgrid navigation
    available_games: List[GameDefinition] = field(default_factory=list)
    final_game: Optional[GameDefinition] = None
    
    # Negotiation log (for language learning)
    negotiation_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Selection metadata
    selection_start_time: float = 0.0
    selection_end_time: float = 0.0
    
    def __post_init__(self):
        # Randomly assign row/column choosers
        if random.random() < 0.5:
            self.row_chooser = self.organism_a_id
            self.column_chooser = self.organism_b_id
        else:
            self.row_chooser = self.organism_b_id
            self.column_chooser = self.organism_a_id
        self.selection_start_time = time.time()


@dataclass 
class BattleResult:
    """Result of a completed arena battle."""
    game: GameDefinition
    organism_a_id: str
    organism_b_id: str
    
    # Scores
    score_a: float = 0.0
    score_b: float = 0.0
    
    # Winner
    winner_id: Optional[str] = None
    margin: float = 0.0
    
    # Detailed stats per organism
    stats_a: Dict[str, Any] = field(default_factory=dict)
    stats_b: Dict[str, Any] = field(default_factory=dict)
    
    # Selection process data
    selection_state: Optional[SelectionState] = None
    
    # Timing
    battle_duration: float = 0.0
    total_episodes: int = 0
    
    # Consequences applied
    fitness_transfer: float = 0.0
    resources_transferred: float = 0.0


# =============================================================================
# PROTON GAME ARENA - The Main Battle System
# =============================================================================

class ProtonGameArena:
    """
    The Proton Game Arena - where organisms compete through fair game selection.
    
    Implements the full Apprentice Adept game selection system:
    1. Random assignment of row/column choosers
    2. Primary 4x4 grid navigation
    3. Secondary subgrid refinement
    4. Final game selection
    5. Gym battle execution
    6. Consequence application
    """
    
    def __init__(self, 
                 bridge_loader: Optional[Callable] = None,
                 fitness_transfer_rate: float = 0.1,
                 resource_transfer_rate: float = 0.05):
        """
        Initialize the Arena.
        
        Args:
            bridge_loader: Function to load AgentBridge for an organism
            fitness_transfer_rate: How much fitness winner takes from loser
            resource_transfer_rate: How much resources transfer on win
        """
        self.bridge_loader = bridge_loader
        self.fitness_transfer_rate = fitness_transfer_rate
        self.resource_transfer_rate = resource_transfer_rate
        
        # Battle history
        self.battle_history: List[BattleResult] = []
        
        # Statistics
        self.total_battles = 0
        self.game_play_counts: Dict[str, int] = {}
        self.challenge_win_rates: Dict[ChallengeType, Dict[str, float]] = {}
        
        logger.info("⚔️ Proton Game Arena initialized")
    
    # =========================================================================
    # GAME SELECTION PROCESS
    # =========================================================================
    
    def begin_selection(self, 
                        organism_a_id: str, 
                        organism_b_id: str) -> SelectionState:
        """
        Begin the game selection process between two organisms.
        
        Returns a SelectionState with randomly assigned row/column choosers.
        """
        state = SelectionState(
            organism_a_id=organism_a_id,
            organism_b_id=organism_b_id
        )
        
        logger.info(f"🎮 Selection begun: {organism_a_id[:8]} vs {organism_b_id[:8]}")
        logger.info(f"   Row chooser: {state.row_chooser[:8]} (Challenge Type)")
        logger.info(f"   Column chooser: {state.column_chooser[:8]} (Resource Type)")
        
        return state
    
    def choose_challenge(self, 
                         state: SelectionState, 
                         chooser_id: str,
                         choice: ChallengeType) -> SelectionState:
        """Row chooser selects the Challenge Type."""
        if chooser_id != state.row_chooser:
            raise ValueError(f"{chooser_id} is not the row chooser!")
        
        state.challenge_choice = choice
        state.negotiation_log.append({
            'type': 'challenge_choice',
            'chooser': chooser_id,
            'choice': choice.value,
            'timestamp': time.time()
        })
        
        logger.info(f"   Challenge chosen: {choice.value}")
        return state
    
    def choose_resource(self,
                        state: SelectionState,
                        chooser_id: str,
                        choice: ResourceType) -> SelectionState:
        """Column chooser selects the Resource Type."""
        if chooser_id != state.column_chooser:
            raise ValueError(f"{chooser_id} is not the column chooser!")
        
        state.resource_choice = choice
        state.negotiation_log.append({
            'type': 'resource_choice',
            'chooser': chooser_id,
            'choice': choice.value,
            'timestamp': time.time()
        })
        
        logger.info(f"   Resource chosen: {choice.value}")
        
        # Now we can determine available games
        key = (state.challenge_choice, state.resource_choice)
        state.available_games = GAME_GRID.get(key, [])
        
        logger.info(f"   Available games: {len(state.available_games)}")
        for game in state.available_games:
            logger.info(f"      - {game.name} ({game.gym_env})")
        
        return state
    
    def select_final_game(self,
                          state: SelectionState,
                          game_index: Optional[int] = None) -> SelectionState:
        """
        Select the final game from available options.
        
        If game_index is None, randomly select (can be enhanced with
        organism preferences and subgrid negotiation later).
        """
        if not state.available_games:
            raise ValueError("No games available! Complete challenge/resource selection first.")
        
        if game_index is None:
            game_index = random.randint(0, len(state.available_games) - 1)
        
        state.final_game = state.available_games[game_index]
        state.selection_end_time = time.time()
        
        state.negotiation_log.append({
            'type': 'final_selection',
            'game': state.final_game.name,
            'gym_env': state.final_game.gym_env,
            'timestamp': time.time()
        })
        
        logger.info(f"   🎯 Final game: {state.final_game.name}")
        
        return state
    
    # =========================================================================
    # AI-DRIVEN SELECTION (Organisms choose based on their traits)
    # =========================================================================
    
    def ai_select_challenge(self,
                            state: SelectionState,
                            organism_traits: Dict[str, float],
                            opponent_traits: Optional[Dict[str, float]] = None) -> ChallengeType:
        """
        AI-driven challenge selection based on organism traits.
        
        The organism evaluates its strengths and chooses accordingly.
        """
        scores = {}
        
        for challenge in ChallengeType:
            score = 0.0
            
            # Get all games in this challenge category
            for resource in ResourceType:
                games = GAME_GRID.get((challenge, resource), [])
                for game in games:
                    # Score based on trait alignment
                    for trait, bonus in game.favored_traits.items():
                        if trait in organism_traits:
                            score += organism_traits[trait] * bonus
            
            scores[challenge] = score
        
        # Add some randomness for exploration
        for challenge in scores:
            scores[challenge] += random.uniform(0, 0.1)
        
        # Choose highest scoring challenge
        best = max(scores, key=scores.get)
        
        logger.debug(f"AI challenge scores: {scores}")
        logger.debug(f"AI chose: {best}")
        
        return best
    
    def ai_select_resource(self,
                           state: SelectionState,
                           organism_traits: Dict[str, float],
                           opponent_traits: Optional[Dict[str, float]] = None) -> ResourceType:
        """
        AI-driven resource selection based on organism traits.
        """
        if state.challenge_choice is None:
            raise ValueError("Challenge must be chosen first!")
        
        scores = {}
        
        for resource in ResourceType:
            games = GAME_GRID.get((state.challenge_choice, resource), [])
            score = 0.0
            
            for game in games:
                for trait, bonus in game.favored_traits.items():
                    if trait in organism_traits:
                        score += organism_traits[trait] * bonus
            
            # Penalize empty categories
            if not games:
                score -= 1.0
            
            scores[resource] = score
        
        # Add randomness
        for resource in scores:
            scores[resource] += random.uniform(0, 0.1)
        
        best = max(scores, key=scores.get)
        
        logger.debug(f"AI resource scores: {scores}")
        logger.debug(f"AI chose: {best}")
        
        return best
    
    # =========================================================================
    # BATTLE EXECUTION
    # =========================================================================
    
    def execute_battle(self,
                       state: SelectionState,
                       bridge_a,  # AgentBridge for organism A
                       bridge_b,  # AgentBridge for organism B
                       episodes: Optional[int] = None) -> BattleResult:
        """
        Execute the selected game battle between two organisms.
        
        Both organisms play the same environment independently,
        and scores are compared to determine the winner.
        """
        if state.final_game is None:
            raise ValueError("No game selected! Complete selection process first.")
        
        game = state.final_game
        episodes = episodes or game.min_episodes
        
        logger.info(f"\n⚔️ BATTLE: {game.name}")
        logger.info(f"   Environment: {game.gym_env}")
        logger.info(f"   Episodes: {episodes}")
        logger.info(f"   {state.organism_a_id[:8]} vs {state.organism_b_id[:8]}")
        
        start_time = time.time()
        
        # Check if this is a standard gym env or custom
        if self._is_standard_gym_env(game.gym_env):
            # Run both organisms in the gym environment
            stats_a = bridge_a.run_gym(
                game.gym_env, 
                episodes=episodes,
                max_steps=game.max_steps,
                render=False,
                learn=False,
                verbose=False
            )
            
            stats_b = bridge_b.run_gym(
                game.gym_env,
                episodes=episodes,
                max_steps=game.max_steps,
                render=False,
                learn=False,
                verbose=False
            )
            
            score_a = stats_a.get(game.score_metric, stats_a.get('mean_reward', 0))
            score_b = stats_b.get(game.score_metric, stats_b.get('mean_reward', 0))
        else:
            # Custom game - use internal evaluation
            score_a, stats_a = self._run_custom_game(game, bridge_a, episodes)
            score_b, stats_b = self._run_custom_game(game, bridge_b, episodes)
        
        # Determine winner
        if score_a > score_b:
            winner_id = state.organism_a_id
            margin = score_a - score_b
        elif score_b > score_a:
            winner_id = state.organism_b_id
            margin = score_b - score_a
        else:
            winner_id = None  # Tie
            margin = 0.0
        
        battle_duration = time.time() - start_time
        
        result = BattleResult(
            game=game,
            organism_a_id=state.organism_a_id,
            organism_b_id=state.organism_b_id,
            score_a=score_a,
            score_b=score_b,
            winner_id=winner_id,
            margin=margin,
            stats_a=stats_a,
            stats_b=stats_b,
            selection_state=state,
            battle_duration=battle_duration,
            total_episodes=episodes
        )
        
        # Log result
        self._log_battle_result(result)
        
        # Track statistics
        self.total_battles += 1
        self.game_play_counts[game.name] = self.game_play_counts.get(game.name, 0) + 1
        self.battle_history.append(result)
        
        return result
    
    def _is_standard_gym_env(self, env_spec: str) -> bool:
        """Check if this is a standard gymnasium environment."""
        standard_prefixes = ['CartPole', 'MountainCar', 'Acrobot', 'Pendulum',
                            'LunarLander', 'BipedalWalker', 'CarRacing',
                            'FrozenLake', 'CliffWalking', 'Blackjack', 'Taxi',
                            'ALE/', 'Ant-', 'HalfCheetah', 'Hopper-', 'Humanoid',
                            'Walker2d', 'Swimmer', 'Pusher', 'Reacher', 'Inverted']
        return any(env_spec.startswith(prefix) for prefix in standard_prefixes)
    
    def _run_custom_game(self, 
                         game: GameDefinition,
                         bridge,
                         episodes: int) -> Tuple[float, Dict]:
        """Run a custom game environment (language games, etc.)."""
        # Placeholder for custom game implementations
        # These will be implemented based on the specific game type
        
        if game.gym_env == "language_coherence":
            return self._evaluate_language_coherence(bridge, episodes)
        elif game.gym_env == "concept_linking":
            return self._evaluate_concept_linking(bridge, episodes)
        elif game.gym_env == "vocabulary_duel":
            return self._evaluate_vocabulary(bridge, episodes)
        elif game.gym_env == "coin_flip":
            return self._evaluate_coin_flip(episodes)
        else:
            # Default: random score for unimplemented games
            logger.warning(f"Custom game {game.gym_env} not implemented, using random score")
            score = random.uniform(0, 100)
            return score, {'note': 'placeholder'}
    
    def _evaluate_language_coherence(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """Evaluate organism's language coherence."""
        total_score = 0.0
        responses = []
        
        test_prompts = [
            "describe environment",
            "explain survival",
            "what is cooperation",
            "describe threat",
            "explain resources"
        ]
        
        for _ in range(episodes):
            prompt = random.choice(test_prompts)
            result = bridge.process(text=prompt)
            response = result.response
            responses.append(response)
            
            # Score based on:
            # - Response length (not too short, not too long)
            # - Word variety
            # - Confidence
            words = response.split()
            length_score = min(len(words) / 10, 1.0) * 30  # Up to 30 points for length
            variety_score = len(set(words)) / max(len(words), 1) * 40  # Up to 40 points for variety
            confidence_score = result.confidence * 30  # Up to 30 points for confidence
            
            total_score += length_score + variety_score + confidence_score
        
        avg_score = total_score / episodes
        return avg_score, {
            'responses': responses,
            'avg_score': avg_score
        }
    
    def _evaluate_concept_linking(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """Evaluate organism's concept association ability."""
        # Simplified evaluation
        score = random.uniform(30, 70) + bridge.vocabulary.vocab_size * 0.1
        return score, {'vocab_size': bridge.vocabulary.vocab_size}
    
    def _evaluate_vocabulary(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """Evaluate vocabulary richness."""
        vocab_size = bridge.vocabulary.vocab_size
        score = vocab_size * 2  # 2 points per word
        return score, {'vocab_size': vocab_size}
    
    def _evaluate_coin_flip(self, episodes: int) -> Tuple[float, Dict]:
        """Pure chance - coin flips."""
        wins = sum(1 for _ in range(episodes) if random.random() < 0.5)
        return wins * 10, {'wins': wins, 'total': episodes}
    
    def _log_battle_result(self, result: BattleResult):
        """Log battle result."""
        winner_str = result.winner_id[:8] if result.winner_id else "TIE"
        
        logger.info(f"\n📊 BATTLE RESULT: {result.game.name}")
        logger.info(f"   {result.organism_a_id[:8]}: {result.score_a:.2f}")
        logger.info(f"   {result.organism_b_id[:8]}: {result.score_b:.2f}")
        logger.info(f"   🏆 Winner: {winner_str} (margin: {result.margin:.2f})")
        logger.info(f"   Duration: {result.battle_duration:.2f}s")
    
    # =========================================================================
    # CONSEQUENCE APPLICATION
    # =========================================================================
    
    def apply_consequences(self,
                           result: BattleResult,
                           organism_a: Any,  # Organism object
                           organism_b: Any,
                           highlander_mode: bool = False) -> Dict[str, Any]:
        """
        Apply consequences of the battle to the organisms.
        
        In normal mode: fitness/resource transfer
        In highlander mode: loser dies
        """
        consequences = {
            'fitness_transferred': 0.0,
            'resources_transferred': 0.0,
            'deaths': []
        }
        
        if result.winner_id is None:
            # Tie - no consequences
            return consequences
        
        # Determine winner and loser
        if result.winner_id == result.organism_a_id:
            winner, loser = organism_a, organism_b
        else:
            winner, loser = organism_b, organism_a
        
        if highlander_mode:
            # THERE CAN BE ONLY ONE
            consequences['deaths'].append(loser.organism_id)
            logger.info(f"⚔️ HIGHLANDER: {loser.organism_id[:8]} has been eliminated!")
        else:
            # Transfer fitness
            fitness_transfer = loser.fitness * self.fitness_transfer_rate
            winner.fitness += fitness_transfer
            loser.fitness -= fitness_transfer
            consequences['fitness_transferred'] = fitness_transfer
            
            # Transfer resources (if applicable)
            if hasattr(loser, 'energy') and hasattr(winner, 'energy'):
                resource_transfer = loser.energy * self.resource_transfer_rate
                winner.energy = min(winner.energy + resource_transfer, 1.0)
                loser.energy = max(loser.energy - resource_transfer, 0.0)
                consequences['resources_transferred'] = resource_transfer
        
        return consequences
    
    # =========================================================================
    # FULL BATTLE ORCHESTRATION
    # =========================================================================
    
    def full_battle(self,
                    organism_a,
                    organism_b,
                    bridge_a,
                    bridge_b,
                    highlander_mode: bool = False,
                    ai_selection: bool = True) -> BattleResult:
        """
        Run a complete battle from selection to consequences.
        
        This is the main entry point for organism competitions.
        """
        logger.info("\n" + "="*60)
        logger.info("⚔️ PROTON GAME ARENA - BATTLE INITIATED")
        logger.info("="*60)
        
        # 1. Begin selection
        state = self.begin_selection(organism_a.organism_id, organism_b.organism_id)
        
        # 2. Challenge selection
        if ai_selection:
            # Get organism traits (simplified)
            traits_a = self._extract_traits(organism_a)
            traits_b = self._extract_traits(organism_b)
            
            # Row chooser selects challenge
            if state.row_chooser == organism_a.organism_id:
                challenge = self.ai_select_challenge(state, traits_a, traits_b)
                self.choose_challenge(state, organism_a.organism_id, challenge)
            else:
                challenge = self.ai_select_challenge(state, traits_b, traits_a)
                self.choose_challenge(state, organism_b.organism_id, challenge)
            
            # Column chooser selects resource
            if state.column_chooser == organism_a.organism_id:
                resource = self.ai_select_resource(state, traits_a, traits_b)
                self.choose_resource(state, organism_a.organism_id, resource)
            else:
                resource = self.ai_select_resource(state, traits_b, traits_a)
                self.choose_resource(state, organism_b.organism_id, resource)
        else:
            # Random selection
            challenge = random.choice(list(ChallengeType))
            resource = random.choice(list(ResourceType))
            self.choose_challenge(state, state.row_chooser, challenge)
            self.choose_resource(state, state.column_chooser, resource)
        
        # 3. Final game selection
        self.select_final_game(state)
        
        # 4. Execute battle
        result = self.execute_battle(state, bridge_a, bridge_b)
        
        # 5. Apply consequences
        consequences = self.apply_consequences(
            result, organism_a, organism_b, highlander_mode
        )
        result.fitness_transfer = consequences['fitness_transferred']
        result.resources_transferred = consequences['resources_transferred']
        
        logger.info("="*60 + "\n")
        
        return result
    
    def _extract_traits(self, organism) -> Dict[str, float]:
        """Extract trait dictionary from organism for AI selection."""
        traits = {}
        
        # Try to get traits from phenotype
        if hasattr(organism, 'phenotype') and organism.phenotype:
            if hasattr(organism.phenotype, 'traits'):
                for trait_name, trait_value in organism.phenotype.traits.items():
                    if isinstance(trait_value, (int, float)):
                        traits[trait_name] = float(trait_value)
        
        # Add fitness as a trait
        if hasattr(organism, 'fitness'):
            traits['fitness'] = organism.fitness
        
        # Add some derived traits
        if hasattr(organism, 'brain') and organism.brain:
            traits['neural_complexity'] = getattr(organism.brain, 'parameter_count', 0) / 10000
        
        # Default traits if empty
        if not traits:
            traits = {
                'physical': random.uniform(0.3, 0.7),
                'mental': random.uniform(0.3, 0.7),
                'luck': random.uniform(0.3, 0.7),
                'creativity': random.uniform(0.3, 0.7)
            }
        
        return traits
    
    # =========================================================================
    # TOURNAMENT MODES
    # =========================================================================
    
    def run_tournament(self,
                       organisms: List[Any],
                       bridges: Dict[str, Any],
                       tournament_type: str = "single_elimination",
                       highlander_mode: bool = False) -> List[BattleResult]:
        """
        Run a tournament between multiple organisms.
        
        tournament_type: "single_elimination", "double_elimination", "round_robin"
        """
        results = []
        
        if tournament_type == "single_elimination":
            results = self._single_elimination(organisms, bridges, highlander_mode)
        elif tournament_type == "round_robin":
            results = self._round_robin(organisms, bridges, highlander_mode)
        else:
            raise ValueError(f"Unknown tournament type: {tournament_type}")
        
        return results
    
    def _single_elimination(self,
                            organisms: List[Any],
                            bridges: Dict[str, Any],
                            highlander_mode: bool) -> List[BattleResult]:
        """Single elimination tournament."""
        results = []
        remaining = list(organisms)
        round_num = 1
        
        while len(remaining) > 1:
            logger.info(f"\n🏆 TOURNAMENT ROUND {round_num}")
            logger.info(f"   Remaining fighters: {len(remaining)}")
            
            random.shuffle(remaining)
            winners = []
            
            for i in range(0, len(remaining) - 1, 2):
                org_a = remaining[i]
                org_b = remaining[i + 1]
                
                bridge_a = bridges.get(org_a.organism_id)
                bridge_b = bridges.get(org_b.organism_id)
                
                if bridge_a and bridge_b:
                    result = self.full_battle(
                        org_a, org_b, bridge_a, bridge_b, highlander_mode
                    )
                    results.append(result)
                    
                    # Winner advances
                    if result.winner_id == org_a.organism_id:
                        winners.append(org_a)
                    elif result.winner_id == org_b.organism_id:
                        winners.append(org_b)
                    else:
                        # Tie - random winner advances
                        winners.append(random.choice([org_a, org_b]))
            
            # Handle odd organism (gets a bye)
            if len(remaining) % 2 == 1:
                winners.append(remaining[-1])
            
            remaining = winners
            round_num += 1
        
        if remaining:
            logger.info(f"\n🏆🏆🏆 TOURNAMENT CHAMPION: {remaining[0].organism_id[:8]} 🏆🏆🏆")
        
        return results
    
    def _round_robin(self,
                     organisms: List[Any],
                     bridges: Dict[str, Any],
                     highlander_mode: bool) -> List[BattleResult]:
        """Round robin - everyone fights everyone."""
        results = []
        
        for i, org_a in enumerate(organisms):
            for org_b in organisms[i+1:]:
                bridge_a = bridges.get(org_a.organism_id)
                bridge_b = bridges.get(org_b.organism_id)
                
                if bridge_a and bridge_b:
                    result = self.full_battle(
                        org_a, org_b, bridge_a, bridge_b, highlander_mode
                    )
                    results.append(result)
        
        return results
    
    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get arena statistics."""
        return {
            'total_battles': self.total_battles,
            'game_play_counts': self.game_play_counts,
            'most_played_game': max(self.game_play_counts, key=self.game_play_counts.get) if self.game_play_counts else None,
            'battle_history_count': len(self.battle_history)
        }
    
    def display_grid(self):
        """Display the game selection grid."""
        print("\n" + "="*80)
        print("🎮 PROTON GAME GRID - Available Games")
        print("="*80)
        
        # Header
        print(f"\n{'':15}", end='')
        for resource in ResourceType:
            print(f"{resource.value:15}", end='')
        print()
        print("-" * 75)
        
        # Rows
        for challenge in ChallengeType:
            print(f"{challenge.value:15}", end='')
            for resource in ResourceType:
                games = GAME_GRID.get((challenge, resource), [])
                count = len(games)
                if count > 0:
                    print(f"[{count} games]      ", end='')
                else:
                    print(f"{'---':15}", end='')
            print()
        
        print("="*80)
        print("\nUse arena.list_games() for full game list")
    
    def list_games(self, 
                   challenge: Optional[ChallengeType] = None,
                   resource: Optional[ResourceType] = None):
        """List all games, optionally filtered."""
        print("\n" + "="*60)
        print("📋 AVAILABLE GAMES")
        print("="*60)
        
        for (c, r), games in GAME_GRID.items():
            if challenge and c != challenge:
                continue
            if resource and r != resource:
                continue
            
            if games:
                print(f"\n{c.value.upper()} + {r.value.upper()}:")
                for game in games:
                    print(f"  • {game.name}")
                    print(f"    Env: {game.gym_env}")
                    print(f"    Difficulty: {game.difficulty.name}")
                    print(f"    {game.description}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_arena(**kwargs) -> ProtonGameArena:
    """Create a new Proton Game Arena."""
    return ProtonGameArena(**kwargs)


def quick_battle(organism_a, organism_b, bridge_a, bridge_b, 
                 highlander: bool = False) -> BattleResult:
    """Quick battle between two organisms."""
    arena = ProtonGameArena()
    return arena.full_battle(organism_a, organism_b, bridge_a, bridge_b, highlander)


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    # Demo the arena
    logging.basicConfig(level=logging.INFO)
    
    arena = ProtonGameArena()
    arena.display_grid()
    arena.list_games()
