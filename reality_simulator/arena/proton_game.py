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

# Get config-driven input_dim (replaces hardcoded 25)
try:
    import sys
    _proton_path = Path(__file__).resolve()
    _project_root = _proton_path.parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from runtime_config import get_input_dim
    _INPUT_DIM = get_input_dim()
except Exception:
    _INPUT_DIM = 30  # Default matches current config.json

# Try to import Language-Game Bridge
try:
    from reality_simulator.language.language_game_bridge import LanguageGameBridge
    LANGUAGE_BRIDGE_AVAILABLE = True
except ImportError:
    LanguageGameBridge = None
    LANGUAGE_BRIDGE_AVAILABLE = False

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
    
    # Two-player game support - organisms play AGAINST each other
    is_two_player: bool = False           # If True, organisms compete head-to-head
    two_player_env: Optional[str] = None  # Alternative env for 2P mode (e.g., "ALE/Pong-v5" -> "PettingZoo/pong_v3")
    
    # Action space type - discrete brains can only learn from discrete games
    is_continuous: bool = False           # If True, requires continuous action head
    
    # Swarm/alliance battle - multiple organisms per side
    is_swarm: bool = False                # If True, uses SwarmBattle for alliance warfare


# =============================================================================
# TWO-PLAYER GAMES - Head-to-head competition
# =============================================================================

TWO_PLAYER_GAMES: Dict[str, GameDefinition] = {
    # Classic arcade versus games
    "pong": GameDefinition(
        name="Pong Duel",
        gym_env="pong_versus",  # Custom handler
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Classic Pong - two organisms battle paddle-to-paddle",
        min_episodes=5,
        score_metric="win_rate",
        tags=["versus", "reflexes", "timing", "classic"],
        favored_traits={"reflexes": 0.3, "timing": 0.2, "prediction": 0.15},
        is_two_player=True
    ),
    "tennis": GameDefinition(
        name="Tennis Match",
        gym_env="tennis_versus",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.TOOL,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Atari Tennis - serve, volley, compete",
        min_episodes=3,
        score_metric="win_rate",
        tags=["versus", "sports", "strategy"],
        favored_traits={"timing": 0.25, "strategy": 0.2},
        is_two_player=True
    ),
    "boxing": GameDefinition(
        name="Boxing Match",
        gym_env="boxing_versus",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.EXPERT,
        description="Boxing - punch, dodge, knock out",
        min_episodes=3,
        score_metric="win_rate",
        tags=["versus", "combat", "reflexes"],
        favored_traits={"aggression": 0.25, "reflexes": 0.2, "endurance": 0.15},
        is_two_player=True
    ),
    "combat": GameDefinition(
        name="Tank Combat",
        gym_env="combat_versus",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Tank warfare - outmaneuver and destroy",
        min_episodes=5,
        score_metric="win_rate",
        tags=["versus", "tanks", "strategy"],
        favored_traits={"strategy": 0.25, "spatial_awareness": 0.2},
        is_two_player=True
    ),
    "warlords": GameDefinition(
        name="Warlords",
        gym_env="warlords_versus",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.TOOL,
        difficulty=GameDifficulty.EXPERT,
        description="Defend your castle, destroy theirs",
        min_episodes=3,
        score_metric="win_rate",
        tags=["versus", "defense", "strategy"],
        favored_traits={"defense": 0.25, "timing": 0.2},
        is_two_player=True
    ),
    # Language duel - organisms compete with vocabulary
    "word_duel": GameDefinition(
        name="Word Duel",
        gym_env="word_duel_versus",
        challenge=ChallengeType.ARTS,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Vocabulary battle - respond with richer language",
        min_episodes=5,
        score_metric="language_score",
        tags=["versus", "language", "vocabulary"],
        favored_traits={"vocabulary_size": 0.3, "coherence": 0.25},
        is_two_player=True
    ),
}


# The Master Game Grid - ALL REAL GYMNASIUM ENVIRONMENTS
# Every cell has 2-3 working gym games for strategic choice
GAME_GRID: Dict[Tuple[ChallengeType, ResourceType], List[GameDefinition]] = {
    # =========================================================================
    # PHYSICAL CHALLENGES - Body control, balance, locomotion
    # =========================================================================
    (ChallengeType.PHYSICAL, ResourceType.NAKED): [
        # Pure body control - no tools, no machines
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
            name="Gymnast Swing",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Swing up using only body momentum",
            tags=["coordination", "timing", "physics"],
            favored_traits={"coordination": 0.25, "timing": 0.15}
        ),
        GameDefinition(
            name="Pendulum Master",
            gym_env="InvertedPendulum-v5",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Balance inverted pendulum with pure control",
            tags=["balance", "control", "stability"],
            favored_traits={"fine_control": 0.2, "stability": 0.15}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.TOOL): [
        # Tool-assisted physical tasks
        # DISABLED: LunarLander requires Box2D (pip install gymnasium[box2d])
        # GameDefinition(
        #     name="Lunar Landing",
        #     gym_env="LunarLander-v3",
        #     challenge=ChallengeType.PHYSICAL,
        #     resource=ResourceType.TOOL,
        #     difficulty=GameDifficulty.JOURNEYMAN,
        #     description="Land spacecraft using thrusters - tool-assisted precision",
        #     tags=["precision", "fuel_management", "spatial"],
        #     favored_traits={"precision": 0.2, "resource_management": 0.15}
        # ),
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
        GameDefinition(
            name="Double Pendulum",
            gym_env="InvertedDoublePendulum-v5",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.EXPERT,
            description="Balance chaotic double pendulum system",
            tags=["chaos", "control", "precision"],
            favored_traits={"adaptability": 0.25, "precision": 0.2}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.MACHINE): [
        # Machine-assisted physical challenges
        GameDefinition(
            name="Race Car",
            gym_env="CarRacing-v3",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Race around track - machine control at speed",
            tags=["driving", "speed", "control"],
            favored_traits={"reaction_time": 0.2, "spatial_awareness": 0.15}
        ),
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Continuous Lander",
        #     gym_env="LunarLanderContinuous-v3",
        #     challenge=ChallengeType.PHYSICAL,
        #     resource=ResourceType.MACHINE,
        #     difficulty=GameDifficulty.EXPERT,
        #     description="Precision landing with continuous thrust control",
        #     tags=["precision", "continuous", "landing"],
        #     favored_traits={"fine_control": 0.25, "fuel_efficiency": 0.15}
        # ),
        GameDefinition(
            name="Mountain Racer",
            gym_env="MountainCarContinuous-v0",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.APPRENTICE,
            description="Continuous acceleration up the mountain",
            tags=["momentum", "continuous", "efficiency"],
            favored_traits={"energy_efficiency": 0.2, "timing": 0.1}
        ),
    ],
    
    (ChallengeType.PHYSICAL, ResourceType.ANIMAL): [
        # Animal-like locomotion - Box2D walkers (MuJoCo commented out as often not installed)
        GameDefinition(
            name="Bipedal Walk",
            gym_env="BipedalWalker-v3",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Walk on two legs over terrain",
            tags=["walking", "balance", "terrain"],
            favored_traits={"balance": 0.2, "adaptability": 0.15}
        ),
        GameDefinition(
            name="Acrobatic Swing",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Swing like an animal - coordinated limbs",
            tags=["swinging", "coordination", "momentum"],
            favored_traits={"coordination": 0.2, "timing": 0.15}
        ),
        GameDefinition(
            name="Cart Balance",
            gym_env="CartPole-v1",
            challenge=ChallengeType.PHYSICAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.NOVICE,
            description="Balance like a sea creature on waves",
            tags=["balance", "reaction", "stability"],
            favored_traits={"balance": 0.2, "reaction_time": 0.15}
        ),
        # MuJoCo games (require mujoco package):
        # GameDefinition(name="Cheetah Sprint", gym_env="HalfCheetah-v5", ...),
        # GameDefinition(name="Hopper", gym_env="Hopper-v5", ...),
    ],
    
    # =========================================================================
    # MENTAL CHALLENGES - Planning, strategy, navigation
    # =========================================================================
    (ChallengeType.MENTAL, ResourceType.NAKED): [
        # Pure mental - no aids
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
            name="Frozen Lake 8x8",
            gym_env="FrozenLake8x8-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Larger frozen lake - more complex planning",
            tags=["planning", "grid", "navigation", "scale"],
            favored_traits={"planning": 0.25, "memory": 0.15}
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
        # Mental with tools
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
        GameDefinition(
            name="Mountain Strategy",
            gym_env="MountainCar-v0",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Build momentum to climb - strategic timing",
            tags=["momentum", "timing", "persistence"],
            favored_traits={"persistence": 0.2, "strategy": 0.15}
        ),
    ],
    
    (ChallengeType.MENTAL, ResourceType.MACHINE): [
        # Mental + machines
        GameDefinition(
            name="Reacher",
            gym_env="Reacher-v5",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Reach target with robotic arm - spatial planning",
            tags=["reaching", "spatial", "precision"],
            favored_traits={"spatial_reasoning": 0.2, "precision": 0.15}
        ),
        GameDefinition(
            name="Pusher",
            gym_env="Pusher-v5",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.EXPERT,
            description="Push object to target - planning and execution",
            tags=["pushing", "planning", "manipulation"],
            favored_traits={"planning": 0.25, "precision": 0.2}
        ),
        GameDefinition(
            name="Track Racing",
            gym_env="CarRacing-v3",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Strategic racing - plan the optimal line",
            tags=["racing", "strategy", "planning"],
            favored_traits={"strategy": 0.2, "prediction": 0.15}
        ),
    ],
    
    (ChallengeType.MENTAL, ResourceType.ANIMAL): [
        # Animal instincts + mental (using Box2D - MuJoCo not installed)
        GameDefinition(
            name="Bipedal Thinking",
            gym_env="BipedalWalker-v3",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Plan each step - mental control of bipedal motion",
            tags=["coordination", "planning", "balance"],
            favored_traits={"coordination": 0.3, "planning": 0.2}
        ),
        GameDefinition(
            name="Acrobatic Mind",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Swing up like a gymnast - timing and momentum",
            tags=["swinging", "timing", "momentum"],
            favored_traits={"rhythm": 0.2, "timing": 0.15}
        ),
        GameDefinition(
            name="Balance Instinct",
            gym_env="Pendulum-v1",
            challenge=ChallengeType.MENTAL,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Balance like a cat - continuous control instincts",
            tags=["balance", "continuous", "instinct"],
            favored_traits={"balance": 0.2, "fine_control": 0.15}
        ),
    ],
    
    # =========================================================================
    # CHANCE CHALLENGES - Stochastic environments, luck + skill
    # =========================================================================
    (ChallengeType.CHANCE, ResourceType.NAKED): [
        # Pure chance environments (stochastic)
        GameDefinition(
            name="Frozen Gamble",
            gym_env="FrozenLake-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.NOVICE,
            description="Slippery ice - skill meets luck (stochastic)",
            min_episodes=5,
            tags=["luck", "stochastic", "navigation"],
            favored_traits={"luck": 0.3, "adaptability": 0.15}
        ),
        GameDefinition(
            name="Big Frozen Gamble",
            gym_env="FrozenLake8x8-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Larger slippery lake - more chaos",
            min_episodes=5,
            tags=["luck", "stochastic", "scale"],
            favored_traits={"luck": 0.25, "persistence": 0.15}
        ),
        GameDefinition(
            name="Cliff Risk",
            gym_env="CliffWalking-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Risk vs reward at the cliff edge",
            min_episodes=5,
            tags=["risk", "chance", "survival"],
            favored_traits={"risk_tolerance": 0.2, "caution": 0.15}
        ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.TOOL): [
        # Chance with tools (cards, etc)
        GameDefinition(
            name="Blackjack",
            gym_env="Blackjack-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Cards - luck meets strategy",
            min_episodes=10,
            tags=["cards", "luck_skill", "probability"],
            favored_traits={"luck": 0.2, "probability_sense": 0.2}
        ),
        GameDefinition(
            name="Taxi Luck",
            gym_env="Taxi-v3",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Random passenger spawns - adapt to chaos",
            min_episodes=5,
            tags=["randomness", "adaptation", "routing"],
            favored_traits={"adaptability": 0.2, "luck": 0.15}
        ),
        GameDefinition(
            name="Pendulum Chaos",
            gym_env="Pendulum-v1",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Random initial states - handle the unknown",
            min_episodes=5,
            tags=["chaos", "control", "adaptation"],
            favored_traits={"adaptability": 0.2, "stability": 0.15}
        ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.MACHINE): [
        # Machine + chance
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Chaotic Landing",
        #     gym_env="LunarLander-v3",
        #     challenge=ChallengeType.CHANCE,
        #     resource=ResourceType.MACHINE,
        #     difficulty=GameDifficulty.JOURNEYMAN,
        #     description="Random wind - land despite chaos",
        #     min_episodes=5,
        #     tags=["wind", "chaos", "landing"],
        #     favored_traits={"adaptability": 0.25, "luck": 0.15}
        # ),
        GameDefinition(
            name="Random Tracks",
            gym_env="CarRacing-v3",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Procedural track - never the same twice",
            min_episodes=3,
            tags=["procedural", "adaptation", "racing"],
            favored_traits={"adaptability": 0.2, "quick_learning": 0.15}
        ),
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Continuous Chaos",
        #     gym_env="LunarLanderContinuous-v3",
        #     challenge=ChallengeType.CHANCE,
        #     resource=ResourceType.MACHINE,
        #     difficulty=GameDifficulty.EXPERT,
        #     description="Continuous control in chaotic wind",
        #     min_episodes=5,
        #     tags=["continuous", "wind", "precision"],
        #     favored_traits={"precision": 0.2, "luck": 0.15}
        # ),
    ],
    
    (ChallengeType.CHANCE, ResourceType.ANIMAL): [
        # Animal + chance (chaotic biological systems)
        GameDefinition(
            name="Bipedal Chaos",
            gym_env="BipedalWalkerHardcore-v3",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Random terrain - stumps, pits, ladders",
            min_episodes=3,
            tags=["terrain", "chaos", "survival"],
            favored_traits={"adaptability": 0.3, "luck": 0.2}
        ),
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Lunar Gamble",
        #     gym_env="LunarLander-v3",
        #     challenge=ChallengeType.CHANCE,
        #     resource=ResourceType.ANIMAL,
        #     difficulty=GameDifficulty.JOURNEYMAN,
        #     description="Random wind - animal-like reactions needed",
        #     min_episodes=5,
        #     tags=["wind", "random", "reaction"],
        #     favored_traits={"reaction_time": 0.2, "luck": 0.15}
        # ),
        GameDefinition(
            name="Mountain Roulette",
            gym_env="MountainCar-v0",
            challenge=ChallengeType.CHANCE,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Random start positions - survive the valley",
            min_episodes=5,
            tags=["momentum", "random_start", "survival"],
            favored_traits={"persistence": 0.2, "luck": 0.15}
        ),
        # MuJoCo games (require mujoco package):
        # GameDefinition(name="Hopper Roulette", gym_env="Hopper-v5", ...),
        # GameDefinition(name="Cheetah Gamble", gym_env="HalfCheetah-v5", ...),
    ],
    
    # =========================================================================
    # ARTS CHALLENGES - Creative problem solving, elegance, style
    # =========================================================================
    (ChallengeType.ARTS, ResourceType.NAKED): [
        # Pure expression - elegant solutions
        GameDefinition(
            name="Elegant Balance",
            gym_env="CartPole-v1",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.NOVICE,
            description="Balance with minimal movement - elegant control",
            tags=["elegance", "minimal", "balance"],
            favored_traits={"elegance": 0.25, "efficiency": 0.15}
        ),
        GameDefinition(
            name="Graceful Swing",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Swing up with style - fewest movements",
            tags=["grace", "efficiency", "style"],
            favored_traits={"grace": 0.2, "efficiency": 0.2}
        ),
        GameDefinition(
            name="Perfect Pendulum",
            gym_env="InvertedPendulum-v5",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.NAKED,
            difficulty=GameDifficulty.APPRENTICE,
            description="Perfect balance - stillness is art",
            tags=["stillness", "perfection", "control"],
            favored_traits={"precision": 0.25, "patience": 0.15}
        ),
    ],
    
    (ChallengeType.ARTS, ResourceType.TOOL): [
        # Tool-assisted creativity
        GameDefinition(
            name="Optimal Route",
            gym_env="Taxi-v3",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Find the most elegant route - minimum moves",
            tags=["optimization", "elegance", "routing"],
            favored_traits={"optimization": 0.25, "creativity": 0.15}
        ),
        GameDefinition(
            name="Card Mastery",
            gym_env="Blackjack-v1",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Play with perfect strategy - art of cards",
            tags=["strategy", "mastery", "cards"],
            favored_traits={"strategy": 0.2, "discipline": 0.15}
        ),
        GameDefinition(
            name="Mountain Poetry",
            gym_env="MountainCar-v0",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.TOOL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Climb with minimal energy - efficiency as art",
            tags=["efficiency", "momentum", "elegance"],
            favored_traits={"efficiency": 0.25, "timing": 0.15}
        ),
    ],
    
    (ChallengeType.ARTS, ResourceType.MACHINE): [
        # Machine artistry
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Perfect Landing",
        #     gym_env="LunarLander-v3",
        #     challenge=ChallengeType.ARTS,
        #     resource=ResourceType.MACHINE,
        #     difficulty=GameDifficulty.JOURNEYMAN,
        #     description="Land perfectly centered - precision art",
        #     tags=["precision", "landing", "perfection"],
        #     favored_traits={"precision": 0.3, "elegance": 0.15}
        # ),
        GameDefinition(
            name="Racing Line",
            gym_env="CarRacing-v3",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.MACHINE,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Perfect racing line - speed as art",
            tags=["racing", "line", "flow"],
            favored_traits={"flow": 0.2, "precision": 0.15}
        ),
        # DISABLED: LunarLander requires Box2D
        # GameDefinition(
        #     name="Smooth Control",
        #     gym_env="LunarLanderContinuous-v3",
        #     challenge=ChallengeType.ARTS,
        #     resource=ResourceType.MACHINE,
        #     difficulty=GameDifficulty.EXPERT,
        #     description="Smoothest possible control - no jerking",
        #     tags=["smooth", "continuous", "elegance"],
        #     favored_traits={"smoothness": 0.25, "precision": 0.2}
        # ),
    ],
    
    (ChallengeType.ARTS, ResourceType.ANIMAL): [
        # Animal grace (using Box2D - MuJoCo not installed)
        GameDefinition(
            name="Graceful Walk",
            gym_env="BipedalWalker-v3",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.JOURNEYMAN,
            description="Walk with natural grace - smooth gait",
            tags=["walking", "grace", "natural"],
            favored_traits={"grace": 0.25, "naturalness": 0.15}
        ),
        GameDefinition(
            name="Acrobatic Grace",
            gym_env="Acrobot-v1",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.APPRENTICE,
            description="Swing with fluid motion - gymnastic art",
            tags=["swinging", "fluid", "rhythm"],
            favored_traits={"rhythm": 0.25, "flow": 0.2}
        ),
        GameDefinition(
            name="Hardcore Grace",
            gym_env="BipedalWalkerHardcore-v3",
            challenge=ChallengeType.ARTS,
            resource=ResourceType.ANIMAL,
            difficulty=GameDifficulty.MASTER,
            description="Navigate obstacles with animal grace - the ultimate art",
            tags=["walking", "obstacles", "mastery"],
            favored_traits={"grace": 0.3, "coordination": 0.25},
            is_continuous=True
        ),
    ],
}

# =============================================================================
# DRONE WARFARE GAMES - Comprehensive training suite for 6 discrete actions
# =============================================================================

# These are special games that use the DroneWarfareArena instead of standard gym envs
# Each game trains specific skills mapped to the 6 discrete brain actions:
#   MOVE=0, COOPERATE=1, COMPETE=2, REST=3, REPRODUCE=4, ISOLATE=5

DRONE_WARFARE_GAMES: List[GameDefinition] = [
    # =========================================================================
    # SINGLE-SKILL TRAINING DRILLS - One game per action type
    # =========================================================================
    
    # --- MOVE (Action 0): Navigation, racing, pathfinding ---
    GameDefinition(
        name="Drone Racing",
        gym_env="drone://racing_gates",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Fly through gates as fast as possible - pure navigation",
        tags=["drone", "racing", "navigation", "speed", "skill:move"],
        favored_traits={"speed": 0.3, "spatial_awareness": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    GameDefinition(
        name="Obstacle Slalom",
        gym_env="drone://obstacle_slalom",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Navigate dense obstacle field at speed",
        tags=["drone", "obstacle", "agility", "skill:move"],
        favored_traits={"agility": 0.25, "reaction_time": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    
    # --- COOPERATE (Action 1): Formation flying, escort, teamwork ---
    GameDefinition(
        name="Formation Flight",
        gym_env="drone://formation_hold",
        challenge=ChallengeType.ARTS,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Maintain precise formation with allies - synchronized flight",
        tags=["drone", "formation", "teamwork", "precision", "skill:cooperate"],
        favored_traits={"coordination": 0.3, "discipline": 0.2},
        is_swarm=True,
        is_two_player=False
    ),
    GameDefinition(
        name="Escort Mission",
        gym_env="drone://escort_vip",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Protect the VIP drone while moving to extraction",
        tags=["drone", "escort", "protection", "teamwork", "skill:cooperate"],
        favored_traits={"vigilance": 0.25, "positioning": 0.2},
        is_swarm=True,
        is_two_player=False
    ),
    
    # --- COMPETE (Action 2): Attack, tagging, aggression ---
    GameDefinition(
        name="Target Practice",
        gym_env="drone://target_practice",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.NOVICE,
        description="Tag stationary and moving targets - attack training",
        tags=["drone", "attack", "accuracy", "targeting", "skill:compete"],
        favored_traits={"accuracy": 0.3, "aggression": 0.15},
        is_swarm=False,
        is_two_player=False
    ),
    GameDefinition(
        name="Drone Dogfight",
        gym_env="drone://dogfight_1v1",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="1v1 aerial combat - tag to score, 4 tags to eliminate",
        tags=["drone", "combat", "dogfight", "1v1", "skill:compete"],
        favored_traits={"aggression": 0.25, "reaction_time": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    
    # --- REST (Action 3): Hover stability, energy conservation ---
    GameDefinition(
        name="Hover Challenge",
        gym_env="drone://precision_hover",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Hold perfectly still despite wind disturbance",
        tags=["drone", "hover", "stability", "precision", "skill:rest"],
        favored_traits={"stability": 0.3, "patience": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    GameDefinition(
        name="Endurance Flight",
        gym_env="drone://endurance_patrol",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Patrol area as long as possible - energy management",
        tags=["drone", "endurance", "energy", "efficiency", "skill:rest"],
        favored_traits={"efficiency": 0.25, "endurance": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    
    # --- REPRODUCE (Action 4): Decoys, chaff, distraction ---
    GameDefinition(
        name="Decoy Master",
        gym_env="drone://decoy_deployment",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Deploy decoys to confuse tracking systems",
        tags=["drone", "decoy", "deception", "tactical", "skill:reproduce"],
        favored_traits={"deception": 0.3, "timing": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    GameDefinition(
        name="Chaff Screen",
        gym_env="drone://chaff_defense",
        challenge=ChallengeType.CHANCE,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Create chaff screens to protect allies from lock-on",
        tags=["drone", "chaff", "defense", "support", "skill:reproduce"],
        favored_traits={"support": 0.25, "timing": 0.2},
        is_swarm=True,
        is_two_player=False
    ),
    
    # --- ISOLATE (Action 5): Evasion, stealth, escape ---
    GameDefinition(
        name="Evasion Training",
        gym_env="drone://evade_missiles",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Evade incoming missiles - juke and survive",
        tags=["drone", "evasion", "survival", "agility", "skill:isolate"],
        favored_traits={"evasion": 0.3, "reflexes": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    GameDefinition(
        name="Stealth Infiltration",
        gym_env="drone://stealth_mission",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Reach objective without being detected",
        tags=["drone", "stealth", "infiltration", "patience", "skill:isolate"],
        favored_traits={"stealth": 0.25, "patience": 0.2},
        is_swarm=False,
        is_two_player=False
    ),
    
    # =========================================================================
    # ASYMMETRIC PAIRED GAMES - One trains attack, other trains defense
    # Highlander absorption still applies - winner absorbs loser!
    # =========================================================================
    
    # --- PREDATOR vs PREY (COMPETE vs ISOLATE) ---
    GameDefinition(
        name="Predator Hunt",
        gym_env="drone://predator_prey|predator",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Hunt and tag the prey drone - ATTACK training",
        tags=["drone", "predator", "hunt", "attack", "asymmetric", "skill:compete"],
        favored_traits={"aggression": 0.25, "prediction": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    GameDefinition(
        name="Prey Survival",
        gym_env="drone://predator_prey|prey",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Evade the predator drone - EVASION training",
        tags=["drone", "prey", "survival", "evasion", "asymmetric", "skill:isolate"],
        favored_traits={"evasion": 0.25, "unpredictability": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    
    # --- ESCORT vs INTERCEPTOR (COOPERATE vs COMPETE) ---
    GameDefinition(
        name="Escort Defender",
        gym_env="drone://escort_intercept|escort",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Protect the VIP from interceptors - TEAMWORK training",
        tags=["drone", "escort", "defense", "protect", "asymmetric", "skill:cooperate"],
        favored_traits={"protection": 0.25, "positioning": 0.2},
        is_swarm=True,
        is_two_player=True
    ),
    GameDefinition(
        name="Interceptor Strike",
        gym_env="drone://escort_intercept|interceptor",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Break through escorts to tag the VIP - ATTACK training",
        tags=["drone", "interceptor", "attack", "breakthrough", "asymmetric", "skill:compete"],
        favored_traits={"aggression": 0.2, "tactical_thinking": 0.25},
        is_swarm=True,
        is_two_player=True
    ),
    
    # --- PURSUER vs EVADER (MOVE vs ISOLATE) ---
    GameDefinition(
        name="Pursuit Racer",
        gym_env="drone://pursuit_race|pursuer",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Chase and close distance - MOVEMENT training",
        tags=["drone", "pursuit", "chase", "speed", "asymmetric", "skill:move"],
        favored_traits={"speed": 0.25, "prediction": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    GameDefinition(
        name="Escape Artist",
        gym_env="drone://pursuit_race|evader",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Maintain distance and escape - EVASION training",
        tags=["drone", "escape", "evade", "distance", "asymmetric", "skill:isolate"],
        favored_traits={"evasion": 0.2, "unpredictability": 0.25},
        is_swarm=False,
        is_two_player=True
    ),
    
    # --- HUNTER vs DECOY MASTER (COMPETE vs REPRODUCE) ---
    GameDefinition(
        name="Decoy Hunter",
        gym_env="drone://decoy_hunt|hunter",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Find and tag the real target among decoys - DISCERNMENT",
        tags=["drone", "hunter", "discernment", "tracking", "asymmetric", "skill:compete"],
        favored_traits={"perception": 0.25, "patience": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    GameDefinition(
        name="Decoy Trickster",
        gym_env="drone://decoy_hunt|trickster",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="Deploy decoys to mislead the hunter - DECEPTION training",
        tags=["drone", "trickster", "decoy", "deception", "asymmetric", "skill:reproduce"],
        favored_traits={"deception": 0.3, "creativity": 0.2},
        is_swarm=False,
        is_two_player=True
    ),
    
    # =========================================================================
    # FULL BATTLE GAMES - Combine all skills
    # =========================================================================
    
    GameDefinition(
        name="Swarm Skirmish",
        gym_env="drone://swarm_3v3",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="3v3 drone swarm battle - alliance warfare",
        tags=["drone", "swarm", "alliance", "tactical", "combined"],
        favored_traits={"coordination": 0.3, "tactical_thinking": 0.2},
        is_swarm=True,
        is_two_player=True
    ),
    GameDefinition(
        name="Squadron War",
        gym_env="drone://swarm_5v5",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.MASTER,
        description="5v5 full squadron battle - ultimate alliance test",
        tags=["drone", "swarm", "war", "strategy", "alliance", "combined"],
        favored_traits={"leadership": 0.25, "strategy": 0.25, "coordination": 0.2},
        is_swarm=True,
        is_two_player=True
    ),
    GameDefinition(
        name="Capture the Flag",
        gym_env="drone://ctf_4v4",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.EXPERT,
        description="4v4 capture the flag - offense and defense",
        tags=["drone", "ctf", "objective", "teamwork", "combined"],
        favored_traits={"strategy": 0.25, "speed": 0.2, "defense": 0.15},
        is_swarm=True,
        is_two_player=True
    ),
    GameDefinition(
        name="King of the Hill",
        gym_env="drone://king_of_hill",
        challenge=ChallengeType.CHANCE,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Control the zone - attack, defend, hold",
        tags=["drone", "koth", "zone", "control", "combined"],
        favored_traits={"aggression": 0.2, "positioning": 0.2, "endurance": 0.15},
        is_swarm=True,
        is_two_player=True
    ),
]

# Asymmetric game pairing map - maps one role to its opponent role
ASYMMETRIC_PAIRINGS = {
    "drone://predator_prey|predator": "drone://predator_prey|prey",
    "drone://predator_prey|prey": "drone://predator_prey|predator",
    "drone://escort_intercept|escort": "drone://escort_intercept|interceptor",
    "drone://escort_intercept|interceptor": "drone://escort_intercept|escort",
    "drone://pursuit_race|pursuer": "drone://pursuit_race|evader",
    "drone://pursuit_race|evader": "drone://pursuit_race|pursuer",
    "drone://decoy_hunt|hunter": "drone://decoy_hunt|trickster",
    "drone://decoy_hunt|trickster": "drone://decoy_hunt|hunter",
}

# Add drone games to the grid
for drone_game in DRONE_WARFARE_GAMES:
    key = (drone_game.challenge, drone_game.resource)
    if key in GAME_GRID:
        GAME_GRID[key].append(drone_game)


# =============================================================================
# CONTINUOUS GAME ENVS - For filtering when discrete_only mode
# =============================================================================

CONTINUOUS_ACTION_ENVS = {
    # MuJoCo continuous control
    "HalfCheetah-v5",
    "BipedalWalker-v3",
    "Hopper-v5",
    "Ant-v5",
    "Swimmer-v5",
    "Walker2d-v5",
    "Humanoid-v5",
    "InvertedPendulum-v5",
    "InvertedDoublePendulum-v5",
    "Reacher-v5",
    "Pusher-v5",
    # Continuous variants
    "Pendulum-v1",
    # "LunarLanderContinuous-v3",  # Requires Box2D
    "MountainCarContinuous-v0",
    "CarRacing-v3",  # Technically has discrete mode too but default is continuous
    # BipedalWalker hardcore variant
    "BipedalWalkerHardcore-v3",
}


def is_discrete_game(game: GameDefinition) -> bool:
    """
    Check if a game uses discrete actions (compatible with 6-action brain).
    
    Returns True for:
    - Games with is_continuous=False (explicit flag)
    - Drone games (drone:// prefix) - all discrete
    - Classic control discrete games (CartPole, Acrobot, etc.)
    - Toy text games (FrozenLake, Taxi, etc.)
    
    Returns False for:
    - Games with is_continuous=True
    - Games in CONTINUOUS_ACTION_ENVS set
    - MuJoCo environments
    """
    # Check explicit flag first
    if hasattr(game, 'is_continuous') and game.is_continuous:
        return False
    
    # Drone games are always discrete (our adapter handles translation)
    if game.gym_env.startswith("drone://"):
        return True
    
    # Check against known continuous envs
    if game.gym_env in CONTINUOUS_ACTION_ENVS:
        return False
    
    # Default to discrete (classic control, toy text, etc.)
    return True


def get_discrete_games() -> Dict[Tuple, List[GameDefinition]]:
    """
    Get filtered GAME_GRID with only discrete action games.
    
    This is for organisms with the 6-action discrete brain architecture.
    Continuous games (MuJoCo, BipedalWalker, etc.) provide no real learning signal.
    """
    filtered = {}
    for key, games in GAME_GRID.items():
        discrete_games = [g for g in games if is_discrete_game(g)]
        if discrete_games:
            filtered[key] = discrete_games
    return filtered


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
    
    # Standard Gymnasium environments that provide REAL training data
    # All verified working environments (v3 for LunarLander, MuJoCo needs mujoco package)
    REAL_GYM_ENVS = {
        # Classic Control (always available)
        'CartPole-v1', 'MountainCar-v0', 'MountainCarContinuous-v0',
        'Acrobot-v1', 'Pendulum-v1',
        # Box2D (pip install gymnasium[box2d]) - LunarLander disabled, requires Box2D
        # 'LunarLander-v3', 'LunarLanderContinuous-v3',
        'BipedalWalker-v3', 'BipedalWalkerHardcore-v3', 'CarRacing-v3',
        # Toy Text (always available)
        'FrozenLake-v1', 'FrozenLake8x8-v1', 'CliffWalking-v1',
        'Blackjack-v1', 'Taxi-v3',
        # MuJoCo (pip install mujoco) - disabled by default as often not installed
        # 'Ant-v5', 'HalfCheetah-v5', 'Hopper-v5', 'Walker2d-v5',
        # 'Humanoid-v5', 'Swimmer-v5', 'InvertedPendulum-v5',
        # 'InvertedDoublePendulum-v5', 'Reacher-v5', 'Pusher-v5',
    }
    
    def __init__(self, 
                 bridge_loader: Optional[Callable] = None,
                 fitness_transfer_rate: float = 0.1,
                 resource_transfer_rate: float = 0.05,
                 event_emitter: Optional[Callable] = None,
                 gym_only: bool = False,
                 discrete_only: bool = True):
        """
        Initialize the Arena.
        
        Args:
            bridge_loader: Function to load AgentBridge for an organism
            fitness_transfer_rate: How much fitness winner takes from loser
            resource_transfer_rate: How much resources transfer on win
            event_emitter: Callable to emit causation events
            gym_only: If True, ONLY real Gymnasium environments (no native games)
            discrete_only: If True, filter out continuous action games (MuJoCo etc)
                          This is REQUIRED for 6-action discrete brain architecture
        """
        self.bridge_loader = bridge_loader
        self.fitness_transfer_rate = fitness_transfer_rate
        self.resource_transfer_rate = resource_transfer_rate
        self.event_emitter = event_emitter
        self.gym_only = gym_only
        self.discrete_only = discrete_only
        
        # Battle history
        self.battle_history: List[BattleResult] = []
        
        # Statistics
        self.total_battles = 0
        self.game_play_counts: Dict[str, int] = {}
        self.challenge_win_rates: Dict[ChallengeType, Dict[str, float]] = {}
        
        # ═══════════════════════════════════════════════════════════════════
        # LANGUAGE-GAME BRIDGE: Connect vocabulary to battle decisions
        # ═══════════════════════════════════════════════════════════════════
        self.language_bridge = None  # Will be set per-battle if available
        
        mode = "GYM-ONLY (real training)" if gym_only else "ALL GAMES"
        discrete_mode = "DISCRETE-ONLY ✅" if discrete_only else "INCLUDING CONTINUOUS ⚠️"
        logger.info(f"⚔️ Proton Game Arena initialized - Mode: {mode}, Actions: {discrete_mode}")
    
    def set_language_bridge(self, bridge: 'LanguageGameBridge') -> None:
        """Set the language bridge for vocabulary-enhanced battle learning."""
        self.language_bridge = bridge
        logger.info("🧠 Language Bridge connected to Proton Arena")
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit a causation event for arena activities."""
        if not self.event_emitter:
            return
        
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='proton_arena',
                event_type=f'proton_{event_type}',
                data={
                    'total_battles': self.total_battles,
                    **data
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
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
        
        # Emit causation event
        self._emit_event('selection_begun', {
            'organism_a': organism_a_id,
            'organism_b': organism_b_id,
            'row_chooser': state.row_chooser,
            'column_chooser': state.column_chooser
        })
        
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
        
        # Emit causation event
        self._emit_event('challenge_chosen', {
            'organism_a': state.organism_a_id,
            'organism_b': state.organism_b_id,
            'chooser': chooser_id,
            'challenge': choice.value
        })
        
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
        all_games = GAME_GRID.get(key, [])
        
        # Apply filters in order:
        # 1. discrete_only filter (for 6-action brain compatibility)
        if self.discrete_only:
            all_games = [g for g in all_games if is_discrete_game(g)]
            logger.debug(f"   After discrete filter: {len(all_games)} games")
        
        # 2. gym-only filter (for real training vs native games)
        if self.gym_only:
            # Keep gym envs and drone games (drone:// envs are our own)
            state.available_games = [g for g in all_games 
                                     if g.gym_env in self.REAL_GYM_ENVS 
                                     or g.gym_env.startswith("drone://")]
            if not state.available_games and all_games:
                # No gym games in this cell - try to find ANY gym game
                logger.warning(f"   ⚠️ No gym games in {state.challenge_choice.value}/{choice.value} - searching all cells")
                for (c, r), games in GAME_GRID.items():
                    # Apply discrete filter here too
                    filtered = [g for g in games if is_discrete_game(g)] if self.discrete_only else games
                    gym_games = [g for g in filtered 
                                if g.gym_env in self.REAL_GYM_ENVS 
                                or g.gym_env.startswith("drone://")]
                    if gym_games:
                        state.available_games = gym_games
                        logger.info(f"   📍 Redirected to {c.value}/{r.value} for gym training")
                        break
        else:
            state.available_games = all_games
        
        logger.info(f"   Available games: {len(state.available_games)}")
        for game in state.available_games:
            is_gym = "✅ GYM" if game.gym_env in self.REAL_GYM_ENVS else ("🛸 DRONE" if game.gym_env.startswith("drone://") else "⚡ NATIVE")
            logger.info(f"      - {game.name} ({game.gym_env}) {is_gym}")
        
        # Emit causation event
        self._emit_event('resource_chosen', {
            'organism_a': state.organism_a_id,
            'organism_b': state.organism_b_id,
            'chooser': chooser_id,
            'resource': choice.value,
            'challenge': state.challenge_choice.value if state.challenge_choice else None,
            'available_games': len(state.available_games)
        })
        
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
        
        # Emit causation event
        self._emit_event('game_selected', {
            'organism_a': state.organism_a_id,
            'organism_b': state.organism_b_id,
            'game_name': state.final_game.name,
            'gym_env': state.final_game.gym_env,
            'challenge': state.challenge_choice.value if state.challenge_choice else None,
            'resource': state.resource_choice.value if state.resource_choice else None,
            'difficulty': state.final_game.difficulty.value if state.final_game.difficulty else None
        })
        
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
        
        # ═══════════════════════════════════════════════════════════════════
        # DRONE WARFARE GAMES (drone:// prefix)
        # Uses our PyFlyt-based drone swarm combat system
        # ═══════════════════════════════════════════════════════════════════
        if self._is_drone_game(game.gym_env):
            score_a, score_b, stats_a, stats_b = self._run_drone_battle(
                game, bridge_a, bridge_b, state, episodes
            )
        # ═══════════════════════════════════════════════════════════════════
        # TWO-PLAYER HEAD-TO-HEAD GAMES
        # Organisms compete DIRECTLY against each other
        # ═══════════════════════════════════════════════════════════════════
        elif game.is_two_player or game.gym_env.endswith('_versus'):
            score_a, score_b, stats_a, stats_b = self._run_two_player_battle(
                game, bridge_a, bridge_b, state, episodes
            )
        # Check if this is a standard gym env or custom
        elif self._is_standard_gym_env(game.gym_env):
            # Run both organisms in the gym environment
            stats_a = bridge_a.run_gym(
                game.gym_env, 
                episodes=episodes,
                max_steps=game.max_steps,
                render=False,
                learn=True,  # 🧠 RECORD EXPERIENCES FOR TRAINING!
                verbose=False
            )
            
            stats_b = bridge_b.run_gym(
                game.gym_env,
                episodes=episodes,
                max_steps=game.max_steps,
                render=False,
                learn=True,  # 🧠 RECORD EXPERIENCES FOR TRAINING!
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
        
        # Emit causation event for battle completion
        self._emit_event('battle_complete', {
            'organism_a': state.organism_a_id,
            'organism_b': state.organism_b_id,
            'winner': winner_id,
            'score_a': score_a,
            'score_b': score_b,
            'margin': margin,
            'game_name': game.name,
            'gym_env': game.gym_env,
            'challenge': state.challenge_choice.value if state.challenge_choice else None,
            'resource': state.resource_choice.value if state.resource_choice else None,
            'battle_duration': battle_duration,
            'episodes': episodes
        })
        
        # ═══════════════════════════════════════════════════════════════════
        # LANGUAGE BRIDGE: Learn from battle outcomes
        # ═══════════════════════════════════════════════════════════════════
        if self.language_bridge and LANGUAGE_BRIDGE_AVAILABLE:
            try:
                # Learn battle outcome for organism A
                self.language_bridge.learn_from_episode_end(
                    organism_name=state.organism_a_id,
                    won=(winner_id == state.organism_a_id),
                    final_score=score_a,
                    episode_length=episodes,
                    additional_info={
                        "game": game.name,
                        "gym_env": game.gym_env,
                        "opponent": state.organism_b_id,
                        "margin": margin if winner_id == state.organism_a_id else -margin,
                        "challenge": state.challenge_choice.value if state.challenge_choice else None
                    }
                )
                
                # Learn battle outcome for organism B
                self.language_bridge.learn_from_episode_end(
                    organism_name=state.organism_b_id,
                    won=(winner_id == state.organism_b_id),
                    final_score=score_b,
                    episode_length=episodes,
                    additional_info={
                        "game": game.name,
                        "gym_env": game.gym_env,
                        "opponent": state.organism_a_id,
                        "margin": margin if winner_id == state.organism_b_id else -margin,
                        "challenge": state.challenge_choice.value if state.challenge_choice else None
                    }
                )
                
                logger.debug(f"🧠 Language Bridge: Learned from battle {game.name}")
            except Exception as e:
                logger.warning(f"Language Bridge learning failed: {e}")
        
        return result
    
    def _is_standard_gym_env(self, env_spec: str) -> bool:
        """Check if this is a standard gymnasium environment."""
        # Drone games are NOT standard gym - they use our DroneWarfareArena
        if env_spec.startswith('drone://'):
            return False
        standard_prefixes = ['CartPole', 'MountainCar', 'Acrobot', 'Pendulum',
                            'BipedalWalker', 'CarRacing',  # LunarLander removed - requires Box2D
                            'FrozenLake', 'CliffWalking', 'Blackjack', 'Taxi',
                            'ALE/', 'Ant-', 'HalfCheetah', 'Hopper-', 'Humanoid',
                            'Walker2d', 'Swimmer', 'Pusher', 'Reacher', 'Inverted']
        return any(env_spec.startswith(prefix) for prefix in standard_prefixes)
    
    def _is_drone_game(self, env_spec: str) -> bool:
        """Check if this is a drone warfare game."""
        return env_spec.startswith('drone://')
    
    # =========================================================================
    # DRONE WARFARE BATTLES
    # Uses CocoonDroneArena for post-export cocoons
    # Uses SwarmBattle for live organisms
    # =========================================================================
    
    def _run_drone_battle(self,
                          game: GameDefinition,
                          bridge_a,
                          bridge_b,
                          state: SelectionState,
                          episodes: int) -> Tuple[float, float, Dict, Dict]:
        """
        Run a drone warfare battle between organisms.
        
        Uses SwarmBattle for live organisms during training.
        For cocoons, use run_cocoon_battle.py instead.
        Organisms control drones through the 6-action discrete adapter.
        
        Returns: (score_a, score_b, stats_a, stats_b)
        """
        from .drone_adapter import SingleDroneArena, OrganismDroneAdapter, PYFLYT_AVAILABLE
        from .swarm_battle import SwarmBattle, BattleConfig, BattleOutcome
        
        env_spec = game.gym_env  # e.g., "drone://predator_prey|predator"
        
        logger.info(f"🛸 DRONE BATTLE: {game.name}")
        logger.info(f"   Spec: {env_spec}")
        logger.info(f"   {state.organism_a_id[:8]} 🆚 {state.organism_b_id[:8]}")
        
        # Parse drone game spec: drone://game_type|role (optional role for asymmetric)
        spec_parts = env_spec.replace('drone://', '').split('|')
        game_type = spec_parts[0]
        role_a = spec_parts[1] if len(spec_parts) > 1 else None
        
        # For asymmetric games, get the opposing role for organism B
        if role_a and role_a in ['predator', 'escort', 'pursuer', 'hunter']:
            opposing_roles = {
                'predator': 'prey',
                'prey': 'predator',
                'escort': 'interceptor',
                'interceptor': 'escort',
                'pursuer': 'evader',
                'evader': 'pursuer',
                'hunter': 'trickster',
                'trickster': 'hunter'
            }
            role_b = opposing_roles.get(role_a, role_a)
        else:
            role_b = role_a
        
        # Get organisms from bridges
        org_a = bridge_a.organism if hasattr(bridge_a, 'organism') else bridge_a
        org_b = bridge_b.organism if hasattr(bridge_b, 'organism') else bridge_b
        
        wins_a = 0
        wins_b = 0
        total_tags_a = 0
        total_tags_b = 0
        flight_time_a = 0.0
        flight_time_b = 0.0
        rounds_detail = []
        
        for episode in range(episodes):
            logger.info(f"\n   🛸 Drone Round {episode + 1}/{episodes}")
            
            if game.is_swarm:
                # Swarm battle (multiple drones per side - use alliance members if available)
                blue_team = [org_a]  # Could expand to alliance.members
                red_team = [org_b]
                
                config = BattleConfig(max_duration=30.0)  # Short rounds
                battle = SwarmBattle(blue_team, red_team, config, self.event_emitter)
                stats = battle.run()
                battle.close()
                
                if stats.outcome == BattleOutcome.BLUE_WINS:
                    wins_a += 1
                    logger.info(f"      🔴 {state.organism_a_id[:8]} wins drone battle!")
                elif stats.outcome == BattleOutcome.RED_WINS:
                    wins_b += 1
                    logger.info(f"      🔵 {state.organism_b_id[:8]} wins drone battle!")
                else:
                    logger.info(f"      🤝 Drone battle draw!")
                
                # Accumulate stats
                for oid, ostats in stats.organism_stats.items():
                    if oid == org_a.organism_id:
                        total_tags_a += ostats.get('tags_scored', 0)
                        flight_time_a += ostats.get('flight_time', 0)
                    elif oid == org_b.organism_id:
                        total_tags_b += ostats.get('tags_scored', 0)
                        flight_time_b += ostats.get('flight_time', 0)
                
                rounds_detail.append({
                    'outcome': stats.outcome.value,
                    'blue_survivors': stats.blue_survivors,
                    'red_survivors': stats.red_survivors
                })
                
            else:
                # Single drone training (non-combat or 1v1)
                if game_type in ['racing_gates', 'obstacle_slalom', 'precision_hover', 
                                 'endurance_patrol', 'target_practice', 'evade_missiles',
                                 'stealth_mission', 'decoy_deployment', 'chaff_defense',
                                 'formation_hold', 'escort_vip']:
                    # Solo training - both play independently
                    if PYFLYT_AVAILABLE:
                        try:
                            arena = SingleDroneArena()
                            result_a = arena.run_episode(org_a, max_steps=300)
                            result_b = arena.run_episode(org_b, max_steps=300)
                            arena.close()
                            
                            if result_a['total_reward'] > result_b['total_reward']:
                                wins_a += 1
                            elif result_b['total_reward'] > result_a['total_reward']:
                                wins_b += 1
                            
                            flight_time_a += result_a.get('flight_time', 0)
                            flight_time_b += result_b.get('flight_time', 0)
                            
                            rounds_detail.append({
                                'score_a': result_a['total_reward'],
                                'score_b': result_b['total_reward']
                            })
                        except Exception as e:
                            logger.warning(f"PyFlyt error: {e}, falling back to simulated")
                            # Fallback to simulated
                            wins_a += 1 if hash(org_a.organism_id) % 2 == 0 else 0
                            wins_b += 1 if hash(org_b.organism_id) % 2 == 1 else 0
                    else:
                        # Simulated drone training (no PyFlyt)
                        score_a = hash(org_a.organism_id + str(episode)) % 100
                        score_b = hash(org_b.organism_id + str(episode)) % 100
                        if score_a > score_b:
                            wins_a += 1
                        elif score_b > score_a:
                            wins_b += 1
                        rounds_detail.append({'score_a': score_a, 'score_b': score_b})
                else:
                    # 1v1 dogfight or asymmetric
                    config = BattleConfig(max_duration=20.0)
                    battle = SwarmBattle([org_a], [org_b], config, self.event_emitter)
                    stats = battle.run()
                    battle.close()
                    
                    if stats.outcome == BattleOutcome.BLUE_WINS:
                        wins_a += 1
                    elif stats.outcome == BattleOutcome.RED_WINS:
                        wins_b += 1
                    
                    rounds_detail.append({'outcome': stats.outcome.value})
        
        # Calculate final scores
        total_rounds = wins_a + wins_b
        if total_rounds > 0:
            score_a = (wins_a / episodes) * 100 + (total_tags_a * 2)  # Bonus for tags
            score_b = (wins_b / episodes) * 100 + (total_tags_b * 2)
        else:
            score_a = score_b = 50.0
        
        stats_a = {
            'wins': wins_a,
            'losses': wins_b,
            'win_rate': wins_a / episodes if episodes > 0 else 0,
            'tags_scored': total_tags_a,
            'flight_time': flight_time_a,
            'role': role_a,
            'game_type': game_type,
            'rounds': rounds_detail
        }
        stats_b = {
            'wins': wins_b,
            'losses': wins_a,
            'win_rate': wins_b / episodes if episodes > 0 else 0,
            'tags_scored': total_tags_b,
            'flight_time': flight_time_b,
            'role': role_b,
            'game_type': game_type,
            'rounds': rounds_detail
        }
        
        logger.info(f"\n   🛸 Drone Battle Complete")
        logger.info(f"   📊 {state.organism_a_id[:8]} {wins_a} - {wins_b} {state.organism_b_id[:8]}")
        logger.info(f"   🎯 Tags: {total_tags_a} vs {total_tags_b}")
        
        return score_a, score_b, stats_a, stats_b
    
    # =========================================================================
    # TWO-PLAYER HEAD-TO-HEAD BATTLES
    # =========================================================================
    
    def _run_two_player_battle(self,
                               game: GameDefinition,
                               bridge_a,
                               bridge_b,
                               state: SelectionState,
                               episodes: int) -> Tuple[float, float, Dict, Dict]:
        """
        Run a true head-to-head battle where organisms compete DIRECTLY.
        
        Instead of running solo environments and comparing scores,
        both organisms play in the same game taking turns or simultaneously.
        
        Returns: (score_a, score_b, stats_a, stats_b)
        """
        game_type = game.gym_env.replace('_versus', '')
        
        logger.info(f"🎮 HEAD-TO-HEAD BATTLE: {game.name}")
        logger.info(f"   {state.organism_a_id[:8]} 🆚 {state.organism_b_id[:8]}")
        
        wins_a = 0
        wins_b = 0
        rounds_detail = []
        
        for episode in range(episodes):
            logger.info(f"\n   Round {episode + 1}/{episodes}")
            
            if game_type in ['pong', 'tennis', 'boxing', 'combat', 'warlords']:
                # Arcade-style turn-based simulation
                result = self._simulate_arcade_duel(game_type, bridge_a, bridge_b)
            elif game_type == 'word_duel':
                # Language-based competition
                result = self._simulate_word_duel(bridge_a, bridge_b)
            else:
                # Default to reaction-based competition
                result = self._simulate_reaction_duel(bridge_a, bridge_b)
            
            if result['winner'] == 'a':
                wins_a += 1
                logger.info(f"      🔴 {state.organism_a_id[:8]} wins!")
            elif result['winner'] == 'b':
                wins_b += 1
                logger.info(f"      🔵 {state.organism_b_id[:8]} wins!")
            else:
                logger.info(f"      🤝 Draw!")
            
            rounds_detail.append(result)
        
        # Calculate scores (wins as percentage * 100)
        total_rounds = wins_a + wins_b
        if total_rounds > 0:
            score_a = (wins_a / episodes) * 100
            score_b = (wins_b / episodes) * 100
        else:
            score_a = score_b = 50.0
        
        stats_a = {
            'wins': wins_a,
            'losses': wins_b,
            'win_rate': wins_a / episodes if episodes > 0 else 0,
            'rounds': rounds_detail,
            'game_type': game_type
        }
        stats_b = {
            'wins': wins_b,
            'losses': wins_a,
            'win_rate': wins_b / episodes if episodes > 0 else 0,
            'rounds': rounds_detail,
            'game_type': game_type
        }
        
        logger.info(f"\n   📊 Final: {state.organism_a_id[:8]} {wins_a} - {wins_b} {state.organism_b_id[:8]}")
        
        return score_a, score_b, stats_a, stats_b
    
    def _simulate_arcade_duel(self, 
                              game_type: str,
                              bridge_a,
                              bridge_b) -> Dict[str, Any]:
        """
        Simulate an arcade-style duel between two organisms.
        
        Each organism makes decisions based on a game state,
        and we resolve the round based on their choices.
        """
        # Generate a game scenario state
        game_state = self._generate_game_state(game_type)
        
        # Both organisms decide on action
        action_a = self._get_organism_action(bridge_a, game_state, game_type)
        action_b = self._get_organism_action(bridge_b, game_state, game_type)
        
        # Resolve based on game type
        if game_type == 'pong':
            return self._resolve_pong_round(action_a, action_b, game_state)
        elif game_type == 'tennis':
            return self._resolve_tennis_round(action_a, action_b, game_state)
        elif game_type == 'boxing':
            return self._resolve_boxing_round(action_a, action_b, game_state)
        elif game_type == 'combat':
            return self._resolve_combat_round(action_a, action_b, game_state)
        elif game_type == 'warlords':
            return self._resolve_warlords_round(action_a, action_b, game_state)
        else:
            return self._resolve_generic_round(action_a, action_b)
    
    def _generate_game_state(self, game_type: str) -> np.ndarray:
        """Generate a game state vector for decision-making."""
        state = np.random.rand(_INPUT_DIM).astype(np.float32)  # Config-driven input_dim
        
        # Game-specific state adjustments
        if game_type == 'pong':
            state[0] = random.uniform(-1, 1)  # Ball X position
            state[1] = random.uniform(-1, 1)  # Ball Y position
            state[2] = random.uniform(-0.5, 0.5)  # Ball X velocity
            state[3] = random.uniform(-0.5, 0.5)  # Ball Y velocity
        elif game_type == 'boxing':
            state[0] = random.uniform(0, 1)  # Distance to opponent
            state[1] = random.uniform(0, 1)  # Own stamina
            state[2] = random.uniform(0, 1)  # Opponent stamina
        
        return state
    
    def _get_organism_action(self, bridge, state: np.ndarray, game_type: str) -> int:
        """Get an organism's action decision for the game state."""
        try:
            result = bridge.process(state=state)
            return result.action
        except Exception:
            # Fallback to random action
            return random.randint(0, 5)
    
    def _resolve_pong_round(self, action_a: int, action_b: int, state: np.ndarray) -> Dict:
        """
        Resolve a Pong-style round.
        
        Actions: 0=stay, 1=up, 2=down, 3=sprint_up, 4=sprint_down, 5=special
        Ball position determines optimal action.
        """
        ball_y = state[1]
        ball_vel_y = state[3]
        predicted_y = ball_y + ball_vel_y * 3  # Predict where ball will be
        
        # Determine optimal actions (simplified)
        # If ball coming high, should move up; if low, move down
        optimal_for_a = 1 if predicted_y > 0.3 else (2 if predicted_y < -0.3 else 0)
        optimal_for_b = 2 if predicted_y > 0.3 else (1 if predicted_y < -0.3 else 0)  # Opposite side
        
        # Score based on how close to optimal
        score_a = 1.0 if action_a == optimal_for_a else (0.5 if abs(action_a - optimal_for_a) <= 1 else 0.2)
        score_b = 1.0 if action_b == optimal_for_b else (0.5 if abs(action_b - optimal_for_b) <= 1 else 0.2)
        
        # Add randomness (ball physics)
        score_a += random.uniform(0, 0.3)
        score_b += random.uniform(0, 0.3)
        
        if score_a > score_b:
            winner = 'a'
        elif score_b > score_a:
            winner = 'b'
        else:
            winner = 'draw'
        
        return {
            'winner': winner,
            'action_a': action_a,
            'action_b': action_b,
            'score_a': score_a,
            'score_b': score_b,
            'game_type': 'pong'
        }
    
    def _resolve_tennis_round(self, action_a: int, action_b: int, state: np.ndarray) -> Dict:
        """Resolve a tennis-style round."""
        # Similar to pong but with serve/return mechanics
        is_serve = random.random() < 0.3
        
        if is_serve:
            # Server advantage
            server_score = 0.6 + random.uniform(0, 0.4)
            receiver_score = 0.3 + random.uniform(0, 0.4)
        else:
            # Rally - both have equal chance
            server_score = 0.4 + random.uniform(0, 0.4)
            receiver_score = 0.4 + random.uniform(0, 0.4)
        
        # Action quality matters
        server_score += 0.1 if action_a in [1, 2] else 0
        receiver_score += 0.1 if action_b in [1, 2] else 0
        
        winner = 'a' if server_score > receiver_score else ('b' if receiver_score > server_score else 'draw')
        
        return {'winner': winner, 'action_a': action_a, 'action_b': action_b, 'game_type': 'tennis'}
    
    def _resolve_boxing_round(self, action_a: int, action_b: int, state: np.ndarray) -> Dict:
        """
        Resolve a boxing-style round.
        
        Actions map to: 0=jab, 1=hook, 2=uppercut, 3=block, 4=dodge, 5=clinch
        Rock-paper-scissors style counters.
        """
        # Action counters
        counters = {
            0: [4],     # Jab beaten by dodge
            1: [3, 4],  # Hook beaten by block or dodge
            2: [4],     # Uppercut beaten by dodge
            3: [2],     # Block beaten by uppercut
            4: [5],     # Dodge beaten by clinch
            5: [0, 1],  # Clinch beaten by jab or hook
        }
        
        a_counters_b = action_a in counters.get(action_b, [])
        b_counters_a = action_b in counters.get(action_a, [])
        
        if a_counters_b and not b_counters_a:
            winner = 'a'
        elif b_counters_a and not a_counters_b:
            winner = 'b'
        elif a_counters_b and b_counters_a:
            winner = 'draw'  # Both counter each other
        else:
            # No counter - random based on action strength
            attack_strength = {0: 0.3, 1: 0.5, 2: 0.7, 3: 0.1, 4: 0.1, 5: 0.05}
            str_a = attack_strength.get(action_a, 0.2) + random.uniform(0, 0.3)
            str_b = attack_strength.get(action_b, 0.2) + random.uniform(0, 0.3)
            winner = 'a' if str_a > str_b else ('b' if str_b > str_a else 'draw')
        
        return {'winner': winner, 'action_a': action_a, 'action_b': action_b, 'game_type': 'boxing'}
    
    def _resolve_combat_round(self, action_a: int, action_b: int, state: np.ndarray) -> Dict:
        """Resolve a tank combat round."""
        # Actions: 0=move, 1=turn_left, 2=turn_right, 3=fire, 4=retreat, 5=special
        
        fire_a = action_a == 3
        fire_b = action_b == 3
        dodge_a = action_a in [0, 1, 2, 4]
        dodge_b = action_b in [0, 1, 2, 4]
        
        if fire_a and not dodge_b:
            winner = 'a'
        elif fire_b and not dodge_a:
            winner = 'b'
        elif fire_a and fire_b:
            winner = random.choice(['a', 'b', 'draw'])
        else:
            winner = 'draw'
        
        return {'winner': winner, 'action_a': action_a, 'action_b': action_b, 'game_type': 'combat'}
    
    def _resolve_warlords_round(self, action_a: int, action_b: int, state: np.ndarray) -> Dict:
        """Resolve a Warlords-style defense/attack round."""
        # Actions: 0-2 = defensive positions, 3-5 = attack positions
        
        attack_a = action_a >= 3
        attack_b = action_b >= 3
        defense_a = not attack_a
        defense_b = not attack_b
        
        if attack_a and defense_b:
            winner = random.choice(['a', 'draw']) if random.random() < 0.6 else 'b'
        elif attack_b and defense_a:
            winner = random.choice(['b', 'draw']) if random.random() < 0.6 else 'a'
        elif attack_a and attack_b:
            winner = random.choice(['a', 'b'])
        else:
            winner = 'draw'
        
        return {'winner': winner, 'action_a': action_a, 'action_b': action_b, 'game_type': 'warlords'}
    
    def _resolve_generic_round(self, action_a: int, action_b: int) -> Dict:
        """Generic round resolution based on action comparison."""
        if action_a > action_b:
            winner = 'a'
        elif action_b > action_a:
            winner = 'b'
        else:
            winner = random.choice(['a', 'b', 'draw'])
        return {'winner': winner, 'action_a': action_a, 'action_b': action_b, 'game_type': 'generic'}
    
    def _simulate_word_duel(self, bridge_a, bridge_b) -> Dict[str, Any]:
        """
        Language-based competition between organisms.
        
        Both respond to a prompt, winner has more coherent/rich response.
        """
        prompts = [
            "Describe your strategy for survival.",
            "What makes cooperation valuable?",
            "Explain the nature of competition.",
            "How do you perceive your environment?",
            "What defines strength?"
        ]
        prompt = random.choice(prompts)
        
        try:
            result_a = bridge_a.process(text=prompt)
            response_a = result_a.response if hasattr(result_a, 'response') else str(result_a)
        except Exception:
            response_a = "..."
        
        try:
            result_b = bridge_b.process(text=prompt)
            response_b = result_b.response if hasattr(result_b, 'response') else str(result_b)
        except Exception:
            response_b = "..."
        
        # Score responses
        def score_response(resp: str) -> float:
            words = resp.split()
            length_score = min(len(words) / 15, 1.0) * 40
            variety_score = (len(set(words)) / max(len(words), 1)) * 40
            # Penalize very short or repetitive
            if len(words) < 3:
                return 10
            return length_score + variety_score + random.uniform(0, 20)
        
        score_a = score_response(response_a)
        score_b = score_response(response_b)
        
        if score_a > score_b + 5:
            winner = 'a'
        elif score_b > score_a + 5:
            winner = 'b'
        else:
            winner = 'draw'
        
        return {
            'winner': winner,
            'prompt': prompt,
            'response_a': response_a[:100],
            'response_b': response_b[:100],
            'score_a': score_a,
            'score_b': score_b,
            'game_type': 'word_duel'
        }
    
    def _simulate_reaction_duel(self, bridge_a, bridge_b) -> Dict[str, Any]:
        """Reaction time based competition."""
        # Generate random state
        state = np.random.rand(_INPUT_DIM).astype(np.float32)  # Config-driven input_dim
        
        # See who responds faster/better
        import time as time_module
        
        start_a = time_module.perf_counter()
        try:
            result_a = bridge_a.process(state=state)
            time_a = time_module.perf_counter() - start_a
        except Exception:
            time_a = 999
        
        start_b = time_module.perf_counter()
        try:
            result_b = bridge_b.process(state=state)
            time_b = time_module.perf_counter() - start_b
        except Exception:
            time_b = 999
        
        # Faster + random factor wins
        score_a = (1.0 / (time_a + 0.001)) + random.uniform(0, 0.5)
        score_b = (1.0 / (time_b + 0.001)) + random.uniform(0, 0.5)
        
        winner = 'a' if score_a > score_b else ('b' if score_b > score_a else 'draw')
        
        return {'winner': winner, 'time_a': time_a, 'time_b': time_b, 'game_type': 'reaction'}

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
        elif game.gym_env == "mutation_roulette":
            return self._evaluate_mutation_roulette(bridge, episodes)
        elif game.gym_env == "predator_prey":
            return self._evaluate_predator_prey(bridge, episodes)
        elif game.gym_env == "collaborative_creation":
            return self._evaluate_collaborative_creation(bridge, episodes)
        elif game.gym_env == "dialogue_quality":
            return self._evaluate_dialogue_quality(bridge, episodes)
        elif game.gym_env == "inter_organism_chat":
            return self._evaluate_inter_organism_chat(bridge, episodes)
        else:
            # NO FAKE SCORES - FAIL LOUD
            error_msg = f"❌ UNIMPLEMENTED CUSTOM GAME: {game.gym_env} - Add handler or remove from matrix!"
            logger.error(error_msg)
            raise NotImplementedError(error_msg)
    
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
    
    def _evaluate_mutation_roulette(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """
        🧬 GENETIC LOTTERY: Test organism's genetic stability under mutation pressure.
        
        Simulates random mutations and evaluates how well the organism's
        neural network maintains coherence under perturbation.
        """
        total_score = 0.0
        stability_scores = []
        
        for _ in range(episodes):
            # Get baseline response
            baseline_state = np.random.rand(_INPUT_DIM).astype(np.float32)  # Config-driven input_dim
            try:
                baseline_result = bridge.process(state=baseline_state)
                baseline_action = baseline_result.action if hasattr(baseline_result, 'action') else 0
                baseline_confidence = baseline_result.confidence if hasattr(baseline_result, 'confidence') else 0.5
            except:
                baseline_action = 0
                baseline_confidence = 0.5
            
            # Apply "mutations" - small perturbations to input
            mutation_strengths = [0.1, 0.2, 0.3, 0.5]
            consistency_count = 0
            
            for strength in mutation_strengths:
                mutated_state = baseline_state + np.random.randn(_INPUT_DIM).astype(np.float32) * strength
                try:
                    mutated_result = bridge.process(state=mutated_state)
                    mutated_action = mutated_result.action if hasattr(mutated_result, 'action') else 0
                    
                    # Reward consistency under mutation
                    if mutated_action == baseline_action:
                        consistency_count += 1
                except:
                    pass
            
            # Score: stability (consistency) + base confidence + luck factor
            stability = consistency_count / len(mutation_strengths)
            luck_bonus = random.uniform(0, 20)  # Genetic lottery has luck component!
            episode_score = (stability * 50) + (baseline_confidence * 30) + luck_bonus
            
            total_score += episode_score
            stability_scores.append(stability)
        
        avg_score = total_score / episodes
        avg_stability = sum(stability_scores) / len(stability_scores)
        
        return avg_score, {
            'avg_stability': avg_stability,
            'episodes': episodes,
            'game_type': 'mutation_roulette'
        }
    
    def _evaluate_predator_prey(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """
        🦁 PREDATOR/PREY: Test organism's survival instincts.
        
        Simulates predator encounters - organism must correctly identify
        threats and respond with flee/fight/hide actions.
        """
        total_score = 0.0
        survival_count = 0
        
        # Threat scenarios encoded in state
        threat_scenarios = [
            {'threat_level': 0.9, 'distance': 0.1, 'correct_action': 4},  # Close danger -> flee (4)
            {'threat_level': 0.3, 'distance': 0.8, 'correct_action': 0},  # Far low threat -> stay (0)
            {'threat_level': 0.7, 'distance': 0.3, 'correct_action': 3},  # Medium threat -> cautious move (3)
            {'threat_level': 0.2, 'distance': 0.2, 'correct_action': 1},  # Low threat close -> investigate (1)
            {'threat_level': 0.95, 'distance': 0.05, 'correct_action': 4}, # Extreme danger -> flee (4)
        ]
        
        for ep in range(episodes):
            scenario = threat_scenarios[ep % len(threat_scenarios)]
            
            # Encode threat in state
            state = np.random.rand(_INPUT_DIM).astype(np.float32)  # Config-driven input_dim
            state[0] = scenario['threat_level']  # Threat perception
            state[1] = scenario['distance']       # Distance to threat
            state[2] = 1.0 - scenario['distance'] # Urgency
            
            try:
                result = bridge.process(state=state)
                action = result.action if hasattr(result, 'action') else random.randint(0, 5)
                confidence = result.confidence if hasattr(result, 'confidence') else 0.5
                
                # Score based on survival appropriateness
                if action == scenario['correct_action']:
                    # Perfect response!
                    episode_score = 20 + confidence * 10
                    survival_count += 1
                elif action == 4 and scenario['threat_level'] > 0.5:
                    # Flee when threatened is acceptable
                    episode_score = 15 + confidence * 5
                    survival_count += 1
                elif action == 0 and scenario['threat_level'] < 0.3:
                    # Stay when safe is acceptable
                    episode_score = 12
                    survival_count += 1
                else:
                    # Wrong response - reduced score
                    episode_score = 5 - (scenario['threat_level'] * 5)
                    
            except:
                episode_score = 0
            
            total_score += max(0, episode_score)
        
        avg_score = total_score / episodes
        survival_rate = survival_count / episodes
        
        return avg_score, {
            'survival_rate': survival_rate,
            'episodes': episodes,
            'game_type': 'predator_prey'
        }
    
    def _evaluate_collaborative_creation(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """
        🎨 COLLABORATIVE CREATION: Test organism's creative & cooperative abilities.
        
        Evaluates language generation quality, vocabulary richness, and
        ability to build on concepts - key for alliance poetry/art.
        """
        total_score = 0.0
        creations = []
        
        creative_prompts = [
            "create beauty",
            "express harmony",
            "describe wonder", 
            "imagine future",
            "tell story"
        ]
        
        for ep in range(episodes):
            prompt = creative_prompts[ep % len(creative_prompts)]
            
            try:
                result = bridge.process(text=prompt)
                response = result.response if hasattr(result, 'response') else ""
                confidence = result.confidence if hasattr(result, 'confidence') else 0.5
                
                # Creativity scoring
                words = response.split() if response else []
                
                # Length score (creativity needs expression)
                length_score = min(len(words) / 8, 1.0) * 25
                
                # Vocabulary diversity (unique words / total words)
                diversity_score = (len(set(words)) / max(len(words), 1)) * 30 if words else 0
                
                # Coherence bonus from confidence
                coherence_score = confidence * 25
                
                # Bonus for vocabulary richness
                vocab_size = bridge.vocabulary.vocab_size if hasattr(bridge, 'vocabulary') else 0
                vocab_bonus = min(vocab_size / 100, 1.0) * 20
                
                episode_score = length_score + diversity_score + coherence_score + vocab_bonus
                creations.append(response)
                
            except:
                episode_score = random.uniform(10, 30)  # Participation points
            
            total_score += episode_score
        
        avg_score = total_score / episodes
        
        return avg_score, {
            'creations': creations,
            'avg_score': avg_score,
            'game_type': 'collaborative_creation'
        }
    
    def _evaluate_dialogue_quality(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """
        💬 DIALOGUE QUALITY: Test full language system response quality.
        """
        total_score = 0.0
        
        dialogue_prompts = [
            "How do you survive?",
            "What makes you strong?",
            "Describe your strategy.",
            "What have you learned?",
            "How do you cooperate?"
        ]
        
        for ep in range(episodes):
            prompt = dialogue_prompts[ep % len(dialogue_prompts)]
            
            try:
                result = bridge.process(text=prompt)
                response = result.response if hasattr(result, 'response') else ""
                confidence = result.confidence if hasattr(result, 'confidence') else 0.5
                
                words = response.split() if response else []
                
                # Quality metrics
                relevance_score = confidence * 40
                length_score = min(len(words) / 10, 1.0) * 30
                coherence_score = (len(set(words)) / max(len(words), 1)) * 30 if words else 0
                
                total_score += relevance_score + length_score + coherence_score
                
            except:
                total_score += 10
        
        return total_score / episodes, {'game_type': 'dialogue_quality'}
    
    def _evaluate_inter_organism_chat(self, bridge, episodes: int) -> Tuple[float, Dict]:
        """
        🗣️ INTER-ORGANISM CHAT: Test communication ability with others.
        
        Simulates receiving messages from another organism and evaluating
        response appropriateness.
        """
        total_score = 0.0
        
        # Simulated messages from "other organism"
        incoming_messages = [
            "friend need help",
            "danger near",
            "food found share",
            "alliance propose",
            "territory mine"
        ]
        
        for ep in range(episodes):
            message = incoming_messages[ep % len(incoming_messages)]
            
            try:
                result = bridge.process(text=message)
                response = result.response if hasattr(result, 'response') else ""
                confidence = result.confidence if hasattr(result, 'confidence') else 0.5
                
                words = response.split() if response else []
                
                # Communication scoring
                response_exists = 20 if response else 0
                confidence_score = confidence * 30
                word_count_score = min(len(words) / 5, 1.0) * 25
                
                # Bonus for cooperative words
                coop_words = {'help', 'share', 'yes', 'friend', 'ally', 'together', 'cooperate', 'agree'}
                coop_bonus = sum(5 for w in words if w.lower() in coop_words)
                
                total_score += response_exists + confidence_score + word_count_score + min(coop_bonus, 25)
                
            except:
                total_score += 10
        
        return total_score / episodes, {'game_type': 'inter_organism_chat'}

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
        
        # TOKEN TUMBLER - Generate tokens for battle consequences
        # Winners get rewarded, losers get modest positive (learning from loss)
        if hasattr(winner, 'tumble_action_tokens'):
            winner.tumble_action_tokens(action=2, reward=0.8, context='battle_win')
        if hasattr(loser, 'tumble_action_tokens'):
            # Learning from loss is valuable too
            loser.tumble_action_tokens(action=3, reward=0.2, context='battle_lose')
        
        # Emit causation event for consequences
        self._emit_event('consequences_applied', {
            'winner': winner.organism_id,
            'loser': loser.organism_id,
            'highlander_mode': highlander_mode,
            'fitness_transferred': consequences.get('fitness_transferred', 0),
            'resources_transferred': consequences.get('resources_transferred', 0),
            'deaths': consequences.get('deaths', [])
        })
        
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
