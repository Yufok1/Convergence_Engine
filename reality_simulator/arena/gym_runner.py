"""
🎮 REAL GYMNASIUM GAME RUNNER

This module provides ACTUAL Gymnasium environment execution for organism battles.
Organisms play games HEADLESSLY and LEARN from the experience.

NO MORE FAKE SIMULATIONS - This is the real deal:
- CartPole: Balance a pole on a cart
- LunarLander: Land a spacecraft  
- Acrobot: Swing up a two-link robot
- MountainCar: Drive up a hill
- Blackjack: Beat the dealer
- FrozenLake: Navigate a frozen lake

Each run:
1. Creates the actual Gym environment
2. Organism's neural network observes state
3. Network outputs action
4. Action is executed in environment
5. Reward is received and RECORDED for training
6. Experience is stored in organism's replay buffer
"""

import logging
import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

# Get config-driven input_dim (replaces hardcoded 25)
try:
    import sys
    from pathlib import Path
    # Add parent dirs to path for runtime_config import
    _gym_runner_path = Path(__file__).resolve()
    _project_root = _gym_runner_path.parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from runtime_config import get_input_dim
    _INPUT_DIM = get_input_dim()
except Exception:
    _INPUT_DIM = 30  # Default matches current config.json

logger = logging.getLogger(__name__)

# Try to import gymnasium (preferred) or gym (fallback)
GYM_AVAILABLE = False
gym = None
try:
    import gymnasium as gym
    GYM_AVAILABLE = True
    logger.info("✅ Gymnasium available for REAL game battles")
except ImportError:
    try:
        import gym
        GYM_AVAILABLE = True
        logger.info("✅ OpenAI Gym available for REAL game battles")
    except ImportError:
        GYM_AVAILABLE = False
        logger.error("❌ GYMNASIUM NOT INSTALLED - Real battles will FAIL! Install with: pip install gymnasium")

# PyTorch for neural processing
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


@dataclass
class GymRunResult:
    """Results from running an organism in a Gym environment."""
    env_name: str
    episodes: int
    total_steps: int
    total_reward: float
    mean_reward: float
    max_reward: float
    min_reward: float
    episode_rewards: List[float]
    episode_lengths: List[int]
    experiences_recorded: int
    training_performed: bool
    duration_seconds: float
    
    def get(self, key: str, default=None):
        """Dict-like access for compatibility."""
        return getattr(self, key, default)


class GymRunner:
    """
    Runs organisms in REAL Gymnasium environments.
    
    This is the core of actual game-based training:
    - Organisms observe real game states
    - Make decisions using their neural networks
    - Receive real rewards from the environment
    - Learn from the experience
    """
    
    # Environment configurations
    ENV_CONFIGS = {
        # Classic Control - good for basic learning
        'CartPole-v1': {
            'action_space': 2,
            'obs_space': 4,
            'reward_threshold': 475,
            'max_steps': 500,
            'description': 'Balance a pole on a cart'
        },
        'MountainCar-v0': {
            'action_space': 3,
            'obs_space': 2,
            'reward_threshold': -110,
            'max_steps': 200,
            'description': 'Drive up a steep hill'
        },
        'Acrobot-v1': {
            'action_space': 3,
            'obs_space': 6,
            'reward_threshold': -100,
            'max_steps': 500,
            'description': 'Swing up a two-link robot'
        },
        'Pendulum-v1': {
            'action_space': 'continuous',  # Special case
            'obs_space': 3,
            'reward_threshold': -200,
            'max_steps': 200,
            'description': 'Swing up and balance a pendulum'
        },
        'LunarLander-v3': {
            'action_space': 4,
            'obs_space': 8,
            'reward_threshold': 200,
            'max_steps': 1000,
            'description': 'Land a spacecraft safely'
        },
        
        # Toy Text - discrete reasoning
        'FrozenLake-v1': {
            'action_space': 4,
            'obs_space': 16,  # One-hot encoded
            'reward_threshold': 0.78,
            'max_steps': 100,
            'description': 'Navigate a frozen lake'
        },
        'Taxi-v3': {
            'action_space': 6,
            'obs_space': 500,  # One-hot encoded
            'reward_threshold': 8,
            'max_steps': 200,
            'description': 'Pick up and drop off passengers'
        },
        'CliffWalking-v0': {
            'action_space': 4,
            'obs_space': 48,  # Grid position
            'reward_threshold': -13,
            'max_steps': 200,
            'description': 'Walk along a cliff edge'
        },
        'CliffWalking-v1': {
            'action_space': 4,
            'obs_space': 48,  # Grid position
            'reward_threshold': -13,
            'max_steps': 200,
            'description': 'Walk along a cliff edge'
        },
        'Blackjack-v1': {
            'action_space': 2,
            'obs_space': 3,  # (player_sum, dealer_card, usable_ace)
            'reward_threshold': 0,
            'max_steps': 100,
            'description': 'Beat the dealer at blackjack'
        },
        
        # Box2D environments
        'LunarLander-v3': {
            'action_space': 4,
            'obs_space': 8,
            'reward_threshold': 200,
            'max_steps': 1000,
            'description': 'Land a spacecraft safely'
        },
        'LunarLanderContinuous-v3': {
            'action_space': 'continuous',
            'obs_space': 8,
            'reward_threshold': 200,
            'max_steps': 1000,
            'description': 'Land spacecraft with continuous control'
        },
        'BipedalWalker-v3': {
            'action_space': 'continuous',
            'obs_space': 24,
            'reward_threshold': 300,
            'max_steps': 1600,
            'description': 'Walk with a bipedal robot'
        },
        'BipedalWalkerHardcore-v3': {
            'action_space': 'continuous',
            'obs_space': 24,
            'reward_threshold': 300,
            'max_steps': 2000,
            'description': 'Walk bipedal robot on rough terrain'
        },
        'CarRacing-v3': {
            'action_space': 'continuous',
            'obs_space': (96, 96, 3),  # Image observation
            'reward_threshold': 900,
            'max_steps': 1000,
            'description': 'Race around a track'
        },
        'MountainCarContinuous-v0': {
            'action_space': 'continuous',
            'obs_space': 2,
            'reward_threshold': 90,
            'max_steps': 999,
            'description': 'Drive up hill with continuous control'
        },
        'FrozenLake8x8-v1': {
            'action_space': 4,
            'obs_space': 64,  # 8x8 grid
            'reward_threshold': 0.99,
            'max_steps': 200,
            'description': 'Navigate a larger frozen lake'
        },
        
        # MuJoCo environments (v5)
        'Ant-v5': {
            'action_space': 'continuous',
            'obs_space': 27,
            'reward_threshold': 6000,
            'max_steps': 1000,
            'description': 'Control a quadruped ant robot'
        },
        'HalfCheetah-v5': {
            'action_space': 'continuous',
            'obs_space': 17,
            'reward_threshold': 4800,
            'max_steps': 1000,
            'description': 'Run fast with a cheetah robot'
        },
        'Hopper-v5': {
            'action_space': 'continuous',
            'obs_space': 11,
            'reward_threshold': 3800,
            'max_steps': 1000,
            'description': 'Hop forward with a one-legged robot'
        },
        'Walker2d-v5': {
            'action_space': 'continuous',
            'obs_space': 17,
            'reward_threshold': 4500,
            'max_steps': 1000,
            'description': 'Walk with a bipedal robot'
        },
        'Humanoid-v5': {
            'action_space': 'continuous',
            'obs_space': 376,
            'reward_threshold': 5000,
            'max_steps': 1000,
            'description': 'Control a humanoid robot'
        },
        'Swimmer-v5': {
            'action_space': 'continuous',
            'obs_space': 8,
            'reward_threshold': 360,
            'max_steps': 1000,
            'description': 'Swim forward with a snake robot'
        },
        'InvertedPendulum-v5': {
            'action_space': 'continuous',
            'obs_space': 4,
            'reward_threshold': 1000,
            'max_steps': 1000,
            'description': 'Balance an inverted pendulum'
        },
        'InvertedDoublePendulum-v5': {
            'action_space': 'continuous',
            'obs_space': 11,
            'reward_threshold': 9100,
            'max_steps': 1000,
            'description': 'Balance a double inverted pendulum'
        },
        'Reacher-v5': {
            'action_space': 'continuous',
            'obs_space': 11,
            'reward_threshold': -3.75,
            'max_steps': 50,
            'description': 'Reach a target with a robot arm'
        },
        'Pusher-v5': {
            'action_space': 'continuous',
            'obs_space': 23,
            'reward_threshold': 0,
            'max_steps': 100,
            'description': 'Push an object to a goal'
        },
    }
    
    # Map Proton Game env specs to real Gym envs
    ENV_MAPPING = {
        # Physical challenges
        'pole_balance': 'CartPole-v1',
        'cart_pole': 'CartPole-v1',
        'mountain_climb': 'MountainCar-v0',
        'robot_swing': 'Acrobot-v1',
        'pendulum_control': 'Pendulum-v1',
        'lunar_landing': 'LunarLander-v3',
        'space_landing': 'LunarLander-v3',
        
        # Mental challenges
        'ice_navigation': 'FrozenLake-v1',
        'taxi_service': 'Taxi-v3',
        'cliff_walk': 'CliffWalking-v1',
        
        # Chance challenges
        'card_game': 'Blackjack-v1',
        'blackjack': 'Blackjack-v1',
        
        # Lowercase aliases (for alliance_dojo)
        'cartpole': 'CartPole-v1',
        'lunarlander': 'LunarLander-v3',
        'mountaincar': 'MountainCar-v0',
        'acrobot': 'Acrobot-v1',
        'pendulum': 'Pendulum-v1',
        'frozenlake': 'FrozenLake-v1',
        'taxi': 'Taxi-v3',
        'cliffwalking': 'CliffWalking-v0',
        
        # Direct mappings - Classic Control
        'CartPole-v1': 'CartPole-v1',
        'MountainCar-v0': 'MountainCar-v0',
        'MountainCarContinuous-v0': 'MountainCarContinuous-v0',
        'Acrobot-v1': 'Acrobot-v1',
        'Pendulum-v1': 'Pendulum-v1',
        
        # Direct mappings - Box2D
        'LunarLander-v3': 'LunarLander-v3',
        'LunarLanderContinuous-v3': 'LunarLanderContinuous-v3',
        'BipedalWalker-v3': 'BipedalWalker-v3',
        'BipedalWalkerHardcore-v3': 'BipedalWalkerHardcore-v3',
        'CarRacing-v3': 'CarRacing-v3',
        
        # Direct mappings - Toy Text
        'FrozenLake-v1': 'FrozenLake-v1',
        'FrozenLake8x8-v1': 'FrozenLake8x8-v1',
        'Taxi-v3': 'Taxi-v3',
        'CliffWalking-v0': 'CliffWalking-v0',
        'CliffWalking-v1': 'CliffWalking-v1',
        'Blackjack-v1': 'Blackjack-v1',
        
        # Direct mappings - MuJoCo v5
        'Ant-v5': 'Ant-v5',
        'HalfCheetah-v5': 'HalfCheetah-v5',
        'Hopper-v5': 'Hopper-v5',
        'Walker2d-v5': 'Walker2d-v5',
        'Humanoid-v5': 'Humanoid-v5',
        'Swimmer-v5': 'Swimmer-v5',
        'InvertedPendulum-v5': 'InvertedPendulum-v5',
        'InvertedDoublePendulum-v5': 'InvertedDoublePendulum-v5',
        'Reacher-v5': 'Reacher-v5',
        'Pusher-v5': 'Pusher-v5',
    }
    
    def __init__(self, device: str = 'cuda'):
        """Initialize the Gym runner."""
        self.device = device if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'
        self.total_games_played = 0
        self.total_experiences_generated = 0
        
        if not GYM_AVAILABLE:
            logger.warning("⚠️ Gymnasium not available - install with: pip install gymnasium")
    
    def run_organism(self,
                     organism,
                     env_spec: str,
                     episodes: int = 10,
                     max_steps: Optional[int] = None,
                     learn: bool = True,
                     render: bool = False,
                     epsilon: Optional[float] = None) -> GymRunResult:
        """
        Run an organism in a REAL Gymnasium environment.
        
        Args:
            organism: The organism with a neural brain
            env_spec: Environment specification (mapped or direct)
            episodes: Number of episodes to play
            max_steps: Maximum steps per episode (None = use default)
            learn: Whether to record experiences for training
            render: Whether to render (False for headless)
            epsilon: Exploration rate override (None = use organism's)
            
        Returns:
            GymRunResult with performance statistics
        """
        if not GYM_AVAILABLE:
            error_msg = f"❌ GYMNASIUM NOT INSTALLED - cannot run {env_spec}! Install with: pip install gymnasium"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Map env spec to actual Gym env
        actual_env = self.ENV_MAPPING.get(env_spec, env_spec)
        env_config = self.ENV_CONFIGS.get(actual_env)
        
        if not env_config:
            logger.warning(f"Unknown env {actual_env}, trying direct creation")
        
        start_time = time.time()
        
        try:
            # Create the environment
            env = gym.make(actual_env, render_mode='human' if render else None)
            
            if max_steps is None and env_config:
                max_steps = env_config.get('max_steps', 1000)
            elif max_steps is None:
                max_steps = 1000
            
            logger.info(f"🎮 REAL GYM BATTLE: {actual_env}")
            logger.info(f"   Organism: {getattr(organism, 'organism_id', 'unknown')[:8]}")
            logger.info(f"   Episodes: {episodes}, Max steps: {max_steps}")
            
            # Run episodes
            episode_rewards = []
            episode_lengths = []
            total_experiences = 0
            
            for ep in range(episodes):
                obs, info = env.reset()
                episode_reward = 0.0
                steps = 0
                done = False
                truncated = False
                
                while not done and not truncated and steps < max_steps:
                    # Get action from organism's brain
                    action = self._get_action(organism, obs, env, epsilon)
                    
                    # Execute action in environment
                    next_obs, reward, done, truncated, info = env.step(action)
                    
                    # Record experience for training
                    if learn:
                        # Try the new gym-specific method first
                        if hasattr(organism, 'record_gym_experience'):
                            organism.record_gym_experience(
                                state=obs,
                                action=action,
                                reward=reward,
                                next_state=next_obs,
                                done=done or truncated
                            )
                            total_experiences += 1
                        elif hasattr(organism, 'record_experience'):
                            # Fallback to standard method (needs prev_state/prev_action set)
                            organism.prev_state = self._obs_to_state(obs, env_config)
                            organism.prev_action = action
                            organism.record_experience(
                                reward=reward,
                                next_state=self._obs_to_state(next_obs, env_config),
                                done=done or truncated
                            )
                            total_experiences += 1
                    
                    episode_reward += reward
                    obs = next_obs
                    steps += 1
                
                episode_rewards.append(episode_reward)
                episode_lengths.append(steps)
                
                logger.debug(f"   Episode {ep+1}: reward={episode_reward:.2f}, steps={steps}")
            
            env.close()
            
            # Calculate statistics
            duration = time.time() - start_time
            result = GymRunResult(
                env_name=actual_env,
                episodes=episodes,
                total_steps=sum(episode_lengths),
                total_reward=sum(episode_rewards),
                mean_reward=np.mean(episode_rewards),
                max_reward=max(episode_rewards),
                min_reward=min(episode_rewards),
                episode_rewards=episode_rewards,
                episode_lengths=episode_lengths,
                experiences_recorded=total_experiences,
                training_performed=learn,
                duration_seconds=duration
            )
            
            self.total_games_played += episodes
            self.total_experiences_generated += total_experiences
            
            # Decay organism's epsilon after gym run (enables gradual exploitation)
            if learn and hasattr(organism, 'epsilon') and hasattr(organism, 'epsilon_decay'):
                epsilon_decay = getattr(organism, 'epsilon_decay', 0.99)
                epsilon_end = getattr(organism, 'epsilon_end', 0.01)
                # Decay once per episode (not per step, that would be too aggressive)
                for _ in range(episodes):
                    organism.epsilon = max(epsilon_end, organism.epsilon * epsilon_decay)
            
            logger.info(f"   ✅ Complete: mean_reward={result.mean_reward:.2f}, "
                       f"experiences={total_experiences}")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ GYM RUN FAILED for {actual_env}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _get_action(self, organism, obs, env, epsilon: Optional[float] = None):
        """Get action from organism's neural network.
        
        Handles both discrete and continuous action spaces.
        """
        action_space = env.action_space
        
        # Check if continuous action space (Box)
        is_continuous = hasattr(action_space, 'shape') and len(action_space.shape) > 0
        
        if not TORCH_AVAILABLE or not hasattr(organism, 'brain') or organism.brain is None:
            # Random action fallback
            return action_space.sample()
        
        brain = organism.brain
        
        # Epsilon-greedy exploration
        if epsilon is None:
            epsilon = getattr(organism, 'epsilon', 0.1)
        
        if np.random.random() < epsilon:
            return action_space.sample()
        
        try:
            # Convert observation to tensor (config-driven input_dim)
            input_dim = _INPUT_DIM
            if isinstance(obs, (int, np.integer)):
                # Discrete observation (like FrozenLake position)
                obs_tensor = torch.zeros(input_dim)  # Pad to expected input dim
                obs_tensor[0] = float(obs) / 100.0  # Normalize
            elif isinstance(obs, tuple):
                # Tuple observation (like Blackjack)
                obs_tensor = torch.zeros(input_dim)
                for i, val in enumerate(obs[:input_dim]):
                    obs_tensor[i] = float(val) if isinstance(val, (int, float, bool)) else 0.0
            else:
                # Array observation (including images - flatten them)
                obs_array = np.array(obs).flatten()
                obs_tensor = torch.zeros(input_dim)
                obs_tensor[:min(len(obs_array), input_dim)] = torch.FloatTensor(obs_array[:input_dim])
            
            obs_tensor = obs_tensor.unsqueeze(0).to(self.device)
            
            # Forward pass through brain
            brain.eval()
            with torch.no_grad():
                output = brain(obs_tensor)
                
                if is_continuous:
                    # ═══════════════════════════════════════════════════════════════
                    # CONTINUOUS ACTION HANDLING (MuJoCo, Box2D, etc.)
                    # 
                    # NOTE: The brain is designed for DQN (discrete Q-values), not
                    # continuous control (SAC/PPO/DDPG). We adapt by:
                    # 1. Using hidden layer activations as action basis
                    # 2. Expanding to required dimensions via interpolation
                    # 3. Applying tanh squashing to action bounds
                    # 
                    # This is NOT optimal for continuous control but allows organisms
                    # to learn basic policies while maintaining architecture simplicity.
                    # ═══════════════════════════════════════════════════════════════
                    action_dim = action_space.shape[0]
                    brain_output_dim = output.shape[-1]
                    
                    # Get raw values from brain (before softmax interpretation)
                    # Use the hidden layer's activations, not softmax probabilities
                    if hasattr(brain, 'get_hidden_state'):
                        # Preferred: use pre-softmax hidden state for richer signal
                        hidden = brain.get_hidden_state(obs_tensor)
                        raw_values = hidden[0, :min(action_dim, hidden.shape[-1])].cpu().numpy()
                    else:
                        # Fallback: use output logits (not ideal but functional)
                        raw_values = output[0].cpu().numpy()
                    
                    # Handle dimension mismatch by repeating/interpolating
                    if len(raw_values) < action_dim:
                        # Repeat pattern to fill required dimensions
                        repeats = (action_dim // len(raw_values)) + 1
                        raw_values = np.tile(raw_values, repeats)[:action_dim]
                    elif len(raw_values) > action_dim:
                        # Truncate to required dimensions
                        raw_values = raw_values[:action_dim]
                    
                    # Get action space bounds
                    low = action_space.low
                    high = action_space.high
                    
                    # Use tanh squashing scaled to action bounds
                    # tanh maps (-inf, inf) -> (-1, 1), then scale to [low, high]
                    action = np.tanh(raw_values) * (high - low) / 2 + (high + low) / 2
                    action = np.clip(action, low, high)
                    
                    return action.astype(np.float32)
                else:
                    # Discrete action space - standard DQN argmax
                    n_actions = action_space.n
                    q_values = output[0, :n_actions]
                    action = q_values.argmax().item()
                    return action
            
        except Exception as e:
            logger.debug(f"Brain forward failed: {e}, using random action")
            return action_space.sample()
    
    def _obs_to_state(self, obs, env_config: Optional[Dict]) -> np.ndarray:
        """Convert observation to standard state vector (matches config.json neural.brain.input_dim)."""
        input_dim = _INPUT_DIM
        state = np.zeros(input_dim, dtype=np.float32)
        
        if isinstance(obs, (int, np.integer)):
            state[0] = float(obs) / 100.0
        elif isinstance(obs, tuple):
            for i, val in enumerate(obs[:input_dim]):
                state[i] = float(val) if isinstance(val, (int, float, bool)) else 0.0
        else:
            obs_array = np.array(obs).flatten()
            state[:min(len(obs_array), input_dim)] = obs_array[:input_dim]
        
        return state
    
    def get_available_envs(self) -> List[str]:
        """Get list of available Gym environments."""
        return list(self.ENV_CONFIGS.keys())
    
    # NOTE: _simulated_run DELETED - NO FAKE SIMULATIONS ALLOWED
    # If Gymnasium isn't installed, it should raise RuntimeError
    
    def get_env_info(self, env_spec: str) -> Optional[Dict[str, Any]]:
        """Get information about an environment."""
        actual_env = self.ENV_MAPPING.get(env_spec, env_spec)
        return self.ENV_CONFIGS.get(actual_env)


# Global runner instance
_gym_runner: Optional[GymRunner] = None

def get_gym_runner() -> GymRunner:
    """Get or create the global GymRunner instance."""
    global _gym_runner
    if _gym_runner is None:
        _gym_runner = GymRunner()
    return _gym_runner


def run_organism_in_gym(organism, 
                        env_spec: str,
                        episodes: int = 10,
                        learn: bool = True) -> GymRunResult:
    """
    Convenience function to run an organism in a Gym environment.
    
    Example:
        result = run_organism_in_gym(organism, 'CartPole-v1', episodes=5)
        print(f"Mean reward: {result.mean_reward}")
    """
    runner = get_gym_runner()
    return runner.run_organism(organism, env_spec, episodes=episodes, learn=learn)
