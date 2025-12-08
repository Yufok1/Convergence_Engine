#!/usr/bin/env python3
"""
🎮 STANDALONE PROTON TOURNAMENT - Self-Training Battle System for Exported Agents

================================================================================
ATTRIBUTION & ACKNOWLEDGMENT
================================================================================

🎮 GAME SELECTION SYSTEM:
Inspired by "The Game" from Piers Anthony's "Apprentice Adept" series (1980-1990).
The 4x4 game selection grid concept is the creative work of Piers Anthony.

⚔️ ABSORPTION BATTLE SYSTEM:
The "winner absorbs the loser's power" mechanic is inspired by "Highlander" (1986),
directed by Russell Mulcahy, written by Gregory Widen. "There can be only one."

================================================================================

This module provides a portable tournament system for exported Butterfly cocoons.
Organisms can battle each other in various gym environments to self-improve.

USAGE:
    from standalone_proton_tournament import ProtonTournament
    
    # Load your cocoon agent
    from cocoon import CocoonAgent
    agent = CocoonAgent()
    
    # Create tournament
    tournament = ProtonTournament(agent)
    
    # Run battles
    tournament.round_robin()           # All vs All
    tournament.elimination()           # Single elimination bracket
    tournament.ladder(episodes=50)     # Continuous ladder matches
    
    # Or run specific battles
    result = tournament.battle(org_a_idx=0, org_b_idx=1, game='cartpole')

Author: The Butterfly System / Convergence Engine
"""

import random
import time
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable
from enum import Enum
from pathlib import Path

# =============================================================================
# ENUMS - Game Categories (Apprentice Adept Grid)
# =============================================================================

class ChallengeType(Enum):
    """Row categories - Nature of the challenge"""
    PHYSICAL = "physical"   # Body, speed, endurance, reflexes
    MENTAL = "mental"       # Strategy, puzzle, planning, memory
    CHANCE = "chance"       # Luck, randomness, probability
    ARTS = "arts"          # Creativity, expression, language


class ResourceType(Enum):
    """Column categories - Available resources"""
    NAKED = "naked"         # Unassisted, raw ability only
    TOOL = "tool"           # Simple tools, extensions of self
    MACHINE = "machine"     # Complex machines, automation
    ANIMAL = "animal"       # Living partners, symbiosis


class GameDifficulty(Enum):
    """Difficulty tiers"""
    NOVICE = 1
    APPRENTICE = 2
    JOURNEYMAN = 3
    EXPERT = 4
    MASTER = 5


# =============================================================================
# GAME DEFINITIONS
# =============================================================================

@dataclass
class GameDefinition:
    """Definition of a tournament game."""
    name: str
    gym_env: str
    challenge: ChallengeType
    resource: ResourceType
    difficulty: GameDifficulty
    description: str
    min_episodes: int = 3
    max_steps: Optional[int] = None
    score_metric: str = "mean_reward"
    tags: List[str] = field(default_factory=list)
    favored_traits: Dict[str, float] = field(default_factory=dict)
    is_two_player: bool = False


# Standard gymnasium games mapped to the grid
TOURNAMENT_GAMES: Dict[str, GameDefinition] = {
    # =========================================================================
    # PHYSICAL CHALLENGES
    # =========================================================================
    "cartpole": GameDefinition(
        name="Balance Beam",
        gym_env="CartPole-v1",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.NOVICE,
        description="Keep the pole balanced - pure reflexes",
        tags=["balance", "reflexes"],
        favored_traits={"stability": 0.2, "reflexes": 0.15}
    ),
    "mountaincar": GameDefinition(
        name="Mountain Climb",
        gym_env="MountainCar-v0",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.APPRENTICE,
        description="Build momentum to reach the peak",
        tags=["momentum", "persistence"],
        favored_traits={"persistence": 0.2}
    ),
    "acrobot": GameDefinition(
        name="Gymnast Swing",
        gym_env="Acrobot-v1",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Swing up using body momentum",
        tags=["coordination", "timing"],
        favored_traits={"coordination": 0.25}
    ),
    "pendulum": GameDefinition(
        name="Pendulum Control",
        gym_env="Pendulum-v1",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.TOOL,
        difficulty=GameDifficulty.APPRENTICE,
        description="Control the pendulum with torque",
        tags=["control", "continuous"],
        favored_traits={"precision": 0.2}
    ),
    "lunarlander": GameDefinition(
        name="Lunar Landing",
        gym_env="LunarLander-v2",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Land the spacecraft safely",
        tags=["piloting", "precision"],
        favored_traits={"precision": 0.25, "patience": 0.15}
    ),
    
    # =========================================================================
    # MENTAL CHALLENGES
    # =========================================================================
    "frozenlake": GameDefinition(
        name="Frozen Lake",
        gym_env="FrozenLake-v1",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.NOVICE,
        description="Navigate the slippery ice to the goal",
        tags=["navigation", "planning"],
        favored_traits={"planning": 0.2}
    ),
    "taxi": GameDefinition(
        name="Taxi Driver",
        gym_env="Taxi-v3",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Pick up and deliver passengers efficiently",
        tags=["planning", "efficiency"],
        favored_traits={"planning": 0.25, "efficiency": 0.2}
    ),
    "cliffwalking": GameDefinition(
        name="Cliff Walk",
        gym_env="CliffWalking-v0",
        challenge=ChallengeType.MENTAL,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Navigate the cliff edge without falling",
        tags=["risk", "caution"],
        favored_traits={"caution": 0.25}
    ),
    "blackjack": GameDefinition(
        name="Blackjack",
        gym_env="Blackjack-v1",
        challenge=ChallengeType.CHANCE,
        resource=ResourceType.NAKED,
        difficulty=GameDifficulty.APPRENTICE,
        description="Beat the dealer at 21",
        tags=["cards", "probability"],
        favored_traits={"risk_assessment": 0.2}
    ),
    
    # =========================================================================
    # ATARI GAMES (if ALE available)
    # =========================================================================
    "breakout": GameDefinition(
        name="Breakout",
        gym_env="ALE/Breakout-v5",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.TOOL,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Break all the bricks with the ball",
        tags=["arcade", "reflexes"],
        favored_traits={"reflexes": 0.25, "prediction": 0.2}
    ),
    "spaceinvaders": GameDefinition(
        name="Space Invaders",
        gym_env="ALE/SpaceInvaders-v5",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.JOURNEYMAN,
        description="Defend Earth from alien invasion",
        tags=["arcade", "shooting"],
        favored_traits={"aggression": 0.2, "timing": 0.2}
    ),
    "pong": GameDefinition(
        name="Pong",
        gym_env="ALE/Pong-v5",
        challenge=ChallengeType.PHYSICAL,
        resource=ResourceType.MACHINE,
        difficulty=GameDifficulty.APPRENTICE,
        description="Classic Pong against AI",
        tags=["arcade", "versus"],
        favored_traits={"reflexes": 0.25, "prediction": 0.2}
    ),
}

# The 4x4 Grid mapping
GAME_GRID: Dict[Tuple[ChallengeType, ResourceType], List[str]] = {
    (ChallengeType.PHYSICAL, ResourceType.NAKED): ["cartpole", "mountaincar", "acrobot"],
    (ChallengeType.PHYSICAL, ResourceType.TOOL): ["pendulum", "breakout"],
    (ChallengeType.PHYSICAL, ResourceType.MACHINE): ["lunarlander", "pong", "spaceinvaders"],
    (ChallengeType.PHYSICAL, ResourceType.ANIMAL): [],  # Future: multi-agent cooperation
    
    (ChallengeType.MENTAL, ResourceType.NAKED): ["frozenlake", "cliffwalking"],
    (ChallengeType.MENTAL, ResourceType.TOOL): [],
    (ChallengeType.MENTAL, ResourceType.MACHINE): ["taxi"],
    (ChallengeType.MENTAL, ResourceType.ANIMAL): [],
    
    (ChallengeType.CHANCE, ResourceType.NAKED): ["blackjack"],
    (ChallengeType.CHANCE, ResourceType.TOOL): [],
    (ChallengeType.CHANCE, ResourceType.MACHINE): [],
    (ChallengeType.CHANCE, ResourceType.ANIMAL): [],
    
    (ChallengeType.ARTS, ResourceType.NAKED): [],  # Word battles - custom
    (ChallengeType.ARTS, ResourceType.TOOL): [],
    (ChallengeType.ARTS, ResourceType.MACHINE): [],
    (ChallengeType.ARTS, ResourceType.ANIMAL): [],
}


# =============================================================================
# BATTLE RESULT
# =============================================================================

@dataclass
class BattleResult:
    """Result of a battle between two organisms."""
    game_name: str
    organism_a_idx: int
    organism_b_idx: int
    
    score_a: float = 0.0
    score_b: float = 0.0
    
    winner_idx: Optional[int] = None
    margin: float = 0.0
    
    episodes_played: int = 0
    total_steps: int = 0
    battle_duration: float = 0.0
    
    # Rewards per episode
    rewards_a: List[float] = field(default_factory=list)
    rewards_b: List[float] = field(default_factory=list)
    
    # Fitness changes applied
    fitness_transfer: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'game': self.game_name,
            'organisms': [self.organism_a_idx, self.organism_b_idx],
            'scores': [self.score_a, self.score_b],
            'winner': self.winner_idx,
            'margin': self.margin,
            'episodes': self.episodes_played,
            'fitness_transfer': self.fitness_transfer
        }


@dataclass
class TournamentStats:
    """Statistics for a tournament."""
    total_battles: int = 0
    battles_by_game: Dict[str, int] = field(default_factory=dict)
    wins_by_organism: Dict[int, int] = field(default_factory=dict)
    total_fitness_transferred: float = 0.0
    battle_history: List[BattleResult] = field(default_factory=list)
    
    def record_battle(self, result: BattleResult):
        self.total_battles += 1
        self.battles_by_game[result.game_name] = self.battles_by_game.get(result.game_name, 0) + 1
        if result.winner_idx is not None:
            self.wins_by_organism[result.winner_idx] = self.wins_by_organism.get(result.winner_idx, 0) + 1
        self.total_fitness_transferred += abs(result.fitness_transfer)
        self.battle_history.append(result)
    
    def get_leaderboard(self) -> List[Tuple[int, int]]:
        """Return organisms sorted by wins."""
        return sorted(self.wins_by_organism.items(), key=lambda x: -x[1])


# =============================================================================
# PROTON TOURNAMENT - The Main Tournament System
# =============================================================================

class ProtonTournament:
    """
    🎮 Proton Tournament System for Exported Cocoon Agents
    
    Allows organisms within a cocoon ensemble to battle each other
    in various gym environments, learning and evolving through competition.
    
    Features:
    - Multiple tournament formats (round-robin, elimination, ladder)
    - Game selection via Apprentice Adept grid
    - Fitness transfer on win/loss (Highlander-style)
    - Training during battles (learn from competition)
    - Statistics tracking
    """
    
    def __init__(self,
                 agent,  # CocoonAgent instance
                 fitness_transfer_rate: float = 0.05,
                 learn_during_battle: bool = True,
                 verbose: bool = True):
        """
        Initialize the tournament.
        
        Args:
            agent: CocoonAgent with multiple organisms
            fitness_transfer_rate: How much fitness winner takes (0.0-1.0)
            learn_during_battle: Whether to train during battles
            verbose: Print battle progress
        """
        self.agent = agent
        self.fitness_transfer_rate = fitness_transfer_rate
        self.learn_during_battle = learn_during_battle
        self.verbose = verbose
        
        # Track organism fitness (starts at 1.0 for all)
        self.organism_fitness: Dict[int, float] = {}
        for i in range(len(agent.brains)):
            self.organism_fitness[i] = 1.0
        
        # Tournament statistics
        self.stats = TournamentStats()
        
        # Available games (filter to those that work)
        self.available_games = self._detect_available_games()
        
        if verbose:
            print(f"🎮 Proton Tournament initialized")
            print(f"   Organisms: {len(agent.brains)}")
            print(f"   Available games: {len(self.available_games)}")
            print(f"   Fitness transfer rate: {fitness_transfer_rate:.1%}")
    
    def _detect_available_games(self) -> List[str]:
        """Detect which games are available (gym environments installed)."""
        available = []
        
        try:
            import gymnasium as gym
        except ImportError:
            try:
                import gym
            except ImportError:
                print("[!] Gymnasium not available - no games detected")
                return []
        
        for game_key, game_def in TOURNAMENT_GAMES.items():
            try:
                # Try to create the environment briefly
                env = gym.make(game_def.gym_env)
                env.close()
                available.append(game_key)
            except Exception:
                pass  # Environment not available
        
        return available
    
    def _log(self, msg: str):
        """Print if verbose."""
        if self.verbose:
            print(msg)
    
    # =========================================================================
    # GAME SELECTION (Apprentice Adept Grid)
    # =========================================================================
    
    def select_game_by_grid(self,
                            challenge: Optional[ChallengeType] = None,
                            resource: Optional[ResourceType] = None) -> Optional[str]:
        """
        Select a game using the 4x4 grid.
        
        If challenge/resource not specified, randomly choose.
        """
        if challenge is None:
            challenge = random.choice(list(ChallengeType))
        if resource is None:
            resource = random.choice(list(ResourceType))
        
        games = GAME_GRID.get((challenge, resource), [])
        # Filter to available games
        games = [g for g in games if g in self.available_games]
        
        if not games:
            # Fall back to any available game
            if self.available_games:
                return random.choice(self.available_games)
            return None
        
        return random.choice(games)
    
    def select_game_random(self) -> Optional[str]:
        """Select a random available game."""
        if not self.available_games:
            return None
        return random.choice(self.available_games)
    
    # =========================================================================
    # BATTLE EXECUTION
    # =========================================================================
    
    def battle(self,
               org_a_idx: int,
               org_b_idx: int,
               game: Optional[str] = None,
               episodes: int = 5,
               max_steps: int = 500) -> BattleResult:
        """
        Run a battle between two organisms.
        
        Each organism plays the same game separately, and scores are compared.
        Winner takes fitness from loser.
        
        Args:
            org_a_idx: Index of first organism
            org_b_idx: Index of second organism
            game: Game key (or None for random)
            episodes: Number of episodes each plays
            max_steps: Max steps per episode
        
        Returns:
            BattleResult with scores and winner
        """
        # Select game
        if game is None:
            game = self.select_game_random()
        
        if game is None or game not in TOURNAMENT_GAMES:
            raise ValueError(f"No valid game available: {game}")
        
        game_def = TOURNAMENT_GAMES[game]
        
        self._log(f"\n⚔️ BATTLE: Organism {org_a_idx} vs Organism {org_b_idx}")
        self._log(f"   Game: {game_def.name} ({game_def.gym_env})")
        
        start_time = time.time()
        
        # Run organism A
        self._log(f"   🅰️ Organism {org_a_idx} playing...")
        rewards_a = self._run_organism(org_a_idx, game_def.gym_env, episodes, max_steps)
        score_a = np.mean(rewards_a) if rewards_a else 0.0
        
        # Run organism B
        self._log(f"   🅱️ Organism {org_b_idx} playing...")
        rewards_b = self._run_organism(org_b_idx, game_def.gym_env, episodes, max_steps)
        score_b = np.mean(rewards_b) if rewards_b else 0.0
        
        # Determine winner
        if score_a > score_b:
            winner_idx = org_a_idx
            loser_idx = org_b_idx
            margin = score_a - score_b
        elif score_b > score_a:
            winner_idx = org_b_idx
            loser_idx = org_a_idx
            margin = score_b - score_a
        else:
            winner_idx = None
            loser_idx = None
            margin = 0.0
        
        # Apply fitness transfer
        fitness_transfer = 0.0
        if winner_idx is not None:
            fitness_transfer = self._apply_fitness_transfer(winner_idx, loser_idx)
        
        duration = time.time() - start_time
        
        # Create result
        result = BattleResult(
            game_name=game,
            organism_a_idx=org_a_idx,
            organism_b_idx=org_b_idx,
            score_a=score_a,
            score_b=score_b,
            winner_idx=winner_idx,
            margin=margin,
            episodes_played=episodes * 2,
            battle_duration=duration,
            rewards_a=rewards_a,
            rewards_b=rewards_b,
            fitness_transfer=fitness_transfer
        )
        
        # Record in stats
        self.stats.record_battle(result)
        
        # Log result
        self._log(f"   📊 Scores: A={score_a:.1f}, B={score_b:.1f}")
        if winner_idx is not None:
            self._log(f"   🏆 Winner: Organism {winner_idx} (margin: {margin:.1f})")
            self._log(f"   💪 Fitness transfer: {fitness_transfer:.4f}")
        else:
            self._log(f"   🤝 Draw!")
        
        return result
    
    def _run_organism(self,
                      organism_idx: int,
                      env_name: str,
                      episodes: int,
                      max_steps: int) -> List[float]:
        """Run a single organism in an environment."""
        try:
            import gymnasium as gym
        except ImportError:
            import gym
        
        rewards = []
        
        try:
            env = gym.make(env_name)
            
            # Get action space size
            action_space_size = None
            if hasattr(env.action_space, 'n'):
                action_space_size = env.action_space.n
            
            for ep in range(episodes):
                obs, _ = env.reset()
                if isinstance(obs, dict):
                    obs = np.array(list(obs.values())).flatten()
                obs = np.asarray(obs, dtype=np.float32).flatten()
                
                done = False
                ep_reward = 0.0
                steps = 0
                
                while not done and steps < max_steps:
                    # Get action from specific organism
                    action = self._get_organism_action(
                        organism_idx, obs, action_space_size
                    )
                    
                    result = env.step(action)
                    if len(result) == 5:
                        next_obs, reward, terminated, truncated, info = result
                        done = terminated or truncated
                    else:
                        next_obs, reward, done, info = result
                    
                    if isinstance(next_obs, dict):
                        next_obs = np.array(list(next_obs.values())).flatten()
                    next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
                    
                    # Learn if enabled
                    if self.learn_during_battle:
                        self.agent.add_experience(obs, action, reward, next_obs, done)
                        if len(self.agent.experience_buffers[organism_idx]) >= self.agent.batch_size:
                            self.agent.train_step()
                    
                    obs = next_obs
                    ep_reward += reward
                    steps += 1
                
                rewards.append(ep_reward)
            
            env.close()
            
        except Exception as e:
            self._log(f"   [!] Error running organism {organism_idx}: {e}")
        
        return rewards
    
    def _get_organism_action(self,
                             organism_idx: int,
                             state: np.ndarray,
                             action_space_size: Optional[int] = None) -> int:
        """Get action from a specific organism (not ensemble vote)."""
        try:
            import torch
            
            brain = self.agent.brains[organism_idx]
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            with torch.no_grad():
                output = brain(state_tensor)
                if isinstance(output, dict):
                    action_probs = output.get('action_probs', output.get('actions'))
                else:
                    action_probs = output
                
                if action_probs is not None:
                    action_probs = action_probs.numpy().flatten()
                    
                    # Clip to action space if needed
                    if action_space_size and len(action_probs) > action_space_size:
                        action_probs = action_probs[:action_space_size]
                    
                    # Epsilon-greedy exploration
                    if random.random() < getattr(self.agent, 'epsilon', 0.1):
                        if action_space_size:
                            return random.randint(0, action_space_size - 1)
                        return random.randint(0, len(action_probs) - 1)
                    
                    return int(np.argmax(action_probs))
        
        except Exception:
            pass
        
        # Fallback: random action
        if action_space_size:
            return random.randint(0, action_space_size - 1)
        return 0
    
    def _apply_fitness_transfer(self, winner_idx: int, loser_idx: int) -> float:
        """Transfer fitness from loser to winner (Highlander-style)."""
        loser_fitness = self.organism_fitness.get(loser_idx, 1.0)
        transfer = loser_fitness * self.fitness_transfer_rate
        
        self.organism_fitness[loser_idx] = max(0.1, loser_fitness - transfer)
        self.organism_fitness[winner_idx] = self.organism_fitness.get(winner_idx, 1.0) + transfer
        
        return transfer
    
    # =========================================================================
    # TOURNAMENT FORMATS
    # =========================================================================
    
    def round_robin(self,
                    game: Optional[str] = None,
                    episodes_per_battle: int = 3) -> List[BattleResult]:
        """
        Run a round-robin tournament where everyone plays everyone.
        
        Returns all battle results.
        """
        num_organisms = len(self.agent.brains)
        results = []
        
        self._log(f"\n🏆 ROUND ROBIN TOURNAMENT")
        self._log(f"   Organisms: {num_organisms}")
        self._log(f"   Total battles: {num_organisms * (num_organisms - 1) // 2}")
        
        battle_num = 0
        for i in range(num_organisms):
            for j in range(i + 1, num_organisms):
                battle_num += 1
                self._log(f"\n--- Battle {battle_num} ---")
                
                # Randomly select game if not specified
                battle_game = game or self.select_game_random()
                
                result = self.battle(i, j, game=battle_game, episodes=episodes_per_battle)
                results.append(result)
        
        self._print_standings()
        return results
    
    def elimination(self,
                    game: Optional[str] = None,
                    episodes_per_battle: int = 5) -> Optional[int]:
        """
        Run single-elimination tournament.
        
        Returns the winning organism index.
        """
        num_organisms = len(self.agent.brains)
        
        # Create bracket
        remaining = list(range(num_organisms))
        random.shuffle(remaining)
        
        self._log(f"\n🏆 ELIMINATION TOURNAMENT")
        self._log(f"   Organisms: {num_organisms}")
        
        round_num = 1
        while len(remaining) > 1:
            self._log(f"\n=== Round {round_num} ({len(remaining)} competitors) ===")
            
            next_round = []
            
            # Pair up organisms
            for i in range(0, len(remaining) - 1, 2):
                org_a = remaining[i]
                org_b = remaining[i + 1]
                
                battle_game = game or self.select_game_random()
                result = self.battle(org_a, org_b, game=battle_game, episodes=episodes_per_battle)
                
                # Winner advances
                if result.winner_idx is not None:
                    next_round.append(result.winner_idx)
                else:
                    # Tie: random advance (or could do rematch)
                    next_round.append(random.choice([org_a, org_b]))
            
            # Handle odd number (bye)
            if len(remaining) % 2 == 1:
                bye_org = remaining[-1]
                self._log(f"   Organism {bye_org} gets a bye")
                next_round.append(bye_org)
            
            remaining = next_round
            round_num += 1
        
        winner = remaining[0] if remaining else None
        self._log(f"\n🥇 CHAMPION: Organism {winner}")
        self._log(f"   Final fitness: {self.organism_fitness.get(winner, 1.0):.4f}")
        
        return winner
    
    def ladder(self,
               total_battles: int = 50,
               game: Optional[str] = None,
               episodes_per_battle: int = 3) -> List[BattleResult]:
        """
        Run continuous ladder matches (random pairings).
        
        Good for extended training sessions.
        """
        num_organisms = len(self.agent.brains)
        results = []
        
        self._log(f"\n🏆 LADDER TOURNAMENT")
        self._log(f"   Organisms: {num_organisms}")
        self._log(f"   Total battles: {total_battles}")
        
        for battle_num in range(total_battles):
            # Random pairing
            org_a, org_b = random.sample(range(num_organisms), 2)
            
            # Select game (variety)
            battle_game = game or self.select_game_random()
            
            self._log(f"\n--- Ladder Match {battle_num + 1}/{total_battles} ---")
            result = self.battle(org_a, org_b, game=battle_game, episodes=episodes_per_battle)
            results.append(result)
            
            # Periodic standings
            if (battle_num + 1) % 10 == 0:
                self._print_standings()
        
        self._print_standings()
        return results
    
    def challenge_the_champion(self,
                               champion_idx: int,
                               challengers: Optional[List[int]] = None,
                               game: Optional[str] = None,
                               episodes_per_battle: int = 5) -> List[BattleResult]:
        """
        All challengers take on the champion one by one.
        
        Champion must defend against all comers.
        """
        if challengers is None:
            challengers = [i for i in range(len(self.agent.brains)) if i != champion_idx]
        
        results = []
        current_champion = champion_idx
        
        self._log(f"\n🏆 CHALLENGE THE CHAMPION")
        self._log(f"   Starting champion: Organism {champion_idx}")
        self._log(f"   Challengers: {len(challengers)}")
        
        for challenger in challengers:
            self._log(f"\n--- {challenger} challenges {current_champion} ---")
            
            battle_game = game or self.select_game_random()
            result = self.battle(current_champion, challenger, game=battle_game, episodes=episodes_per_battle)
            results.append(result)
            
            # Check if champion was dethroned
            if result.winner_idx == challenger:
                self._log(f"   👑 NEW CHAMPION: Organism {challenger}!")
                current_champion = challenger
        
        self._log(f"\n🥇 FINAL CHAMPION: Organism {current_champion}")
        return results
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def _print_standings(self):
        """Print current standings."""
        self._log(f"\n📊 CURRENT STANDINGS")
        self._log(f"   {'Org':>4} {'Wins':>6} {'Fitness':>8}")
        self._log(f"   {'-'*20}")
        
        # Sort by wins then fitness
        standings = []
        for org_idx in range(len(self.agent.brains)):
            wins = self.stats.wins_by_organism.get(org_idx, 0)
            fitness = self.organism_fitness.get(org_idx, 1.0)
            standings.append((org_idx, wins, fitness))
        
        standings.sort(key=lambda x: (-x[1], -x[2]))
        
        for org_idx, wins, fitness in standings:
            self._log(f"   {org_idx:>4} {wins:>6} {fitness:>8.4f}")
    
    def get_standings(self) -> List[Dict[str, Any]]:
        """Get standings as list of dicts."""
        standings = []
        for org_idx in range(len(self.agent.brains)):
            standings.append({
                'organism': org_idx,
                'wins': self.stats.wins_by_organism.get(org_idx, 0),
                'fitness': self.organism_fitness.get(org_idx, 1.0)
            })
        standings.sort(key=lambda x: (-x['wins'], -x['fitness']))
        return standings
    
    def export_stats(self, filepath: str):
        """Export tournament statistics to JSON."""
        data = {
            'total_battles': self.stats.total_battles,
            'battles_by_game': self.stats.battles_by_game,
            'standings': self.get_standings(),
            'fitness': dict(self.organism_fitness),
            'battle_history': [r.to_dict() for r in self.stats.battle_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self._log(f"📁 Stats exported to {filepath}")


# =============================================================================
# WORD BATTLE - Language-based competition
# =============================================================================

class WordBattle:
    """
    🗣️ Word Battle - Organisms compete through language generation.
    
    Two organisms take turns generating responses to prompts.
    Scored on vocabulary richness, coherence, and relevance.
    """
    
    def __init__(self, agent, verbose: bool = True):
        self.agent = agent
        self.verbose = verbose
    
    def battle(self,
               org_a_idx: int,
               org_b_idx: int,
               prompts: Optional[List[str]] = None,
               max_tokens: int = 50) -> Dict[str, Any]:
        """
        Run a word battle between two organisms.
        """
        if prompts is None:
            prompts = [
                "Describe the meaning of cooperation.",
                "What is survival?",
                "Tell me about learning.",
                "Explain competition.",
                "What makes life meaningful?"
            ]
        
        scores_a = []
        scores_b = []
        responses = []
        
        for prompt in prompts:
            # Organism A responds
            resp_a = self.agent.generate_response(prompt, organism_idx=org_a_idx, max_tokens=max_tokens)
            score_a = self._score_response(resp_a, prompt)
            
            # Organism B responds
            resp_b = self.agent.generate_response(prompt, organism_idx=org_b_idx, max_tokens=max_tokens)
            score_b = self._score_response(resp_b, prompt)
            
            scores_a.append(score_a)
            scores_b.append(score_b)
            
            responses.append({
                'prompt': prompt,
                'response_a': resp_a,
                'response_b': resp_b,
                'score_a': score_a,
                'score_b': score_b
            })
            
            if self.verbose:
                print(f"\n📝 Prompt: {prompt}")
                print(f"   A ({org_a_idx}): {resp_a[:60]}... [score: {score_a:.2f}]")
                print(f"   B ({org_b_idx}): {resp_b[:60]}... [score: {score_b:.2f}]")
        
        # Determine winner
        avg_a = np.mean(scores_a)
        avg_b = np.mean(scores_b)
        
        if avg_a > avg_b:
            winner = org_a_idx
        elif avg_b > avg_a:
            winner = org_b_idx
        else:
            winner = None
        
        if self.verbose:
            print(f"\n🏆 Word Battle Result:")
            print(f"   Organism {org_a_idx}: {avg_a:.2f}")
            print(f"   Organism {org_b_idx}: {avg_b:.2f}")
            print(f"   Winner: {'Draw' if winner is None else f'Organism {winner}'}")
        
        return {
            'winner': winner,
            'score_a': avg_a,
            'score_b': avg_b,
            'responses': responses
        }
    
    def _score_response(self, response: str, prompt: str) -> float:
        """Score a response for quality."""
        if not response or len(response.strip()) == 0:
            return 0.0
        
        words = response.lower().split()
        
        # Length score (longer is better, up to a point)
        length_score = min(len(words) / 20, 1.0) * 0.3
        
        # Vocabulary richness (unique words ratio)
        unique_ratio = len(set(words)) / max(len(words), 1)
        vocab_score = unique_ratio * 0.4
        
        # Relevance (overlap with prompt)
        prompt_words = set(prompt.lower().split())
        overlap = len(set(words) & prompt_words) / max(len(prompt_words), 1)
        relevance_score = overlap * 0.3
        
        return length_score + vocab_score + relevance_score


# =============================================================================
# MAIN - Demo usage
# =============================================================================

def main():
    """Demo the tournament system."""
    print("🎮 Proton Tournament System")
    print("=" * 50)
    print()
    print("Usage with a cocoon agent:")
    print()
    print("  from cocoon import CocoonAgent")
    print("  from standalone_proton_tournament import ProtonTournament")
    print()
    print("  agent = CocoonAgent()")
    print("  tournament = ProtonTournament(agent)")
    print()
    print("  # Run different tournament formats:")
    print("  tournament.round_robin()            # All vs All")
    print("  tournament.elimination()            # Single elimination")
    print("  tournament.ladder(total_battles=50) # Continuous matches")
    print()
    print("  # Or run specific battles:")
    print("  result = tournament.battle(0, 1, game='cartpole')")
    print()
    print("Available games:")
    for game_key, game_def in TOURNAMENT_GAMES.items():
        print(f"  - {game_key}: {game_def.name} ({game_def.gym_env})")


if __name__ == "__main__":
    main()
