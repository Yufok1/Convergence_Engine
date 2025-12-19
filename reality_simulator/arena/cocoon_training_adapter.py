"""
🎓 COCOON TRAINING ADAPTER

Enables post-export cocoons to continue training via:
- Sphere Arena (existing - already works)
- Proton Game Arena (gym environments)
- Drone Combat Arena (aerial warfare)

This adapter provides the missing training hooks that let
exported cocoons learn from new experiences.

Key Insight:
    Cocoons are frozen neural weights + atomic vocabulary.
    But they can still LEARN by:
    1. Recording experiences to their internal buffers
    2. Updating their VP (vitality/pleasure) based on outcomes
    3. Strengthening/weakening atomic concepts based on use
    4. Building new associations in knowledge web

Training Modes:
    INFERENCE_ONLY: Just run, no learning (fastest)
    EXPERIENCE_RECORD: Record experiences, learn later
    ONLINE_LEARN: Update weights after each episode
    FULL_TRAIN: Full training loop with backprop

The drone arena, sphere arena, and proton games all use this
adapter to provide consistent training behavior.
"""

import os
import sys
import time
import numpy as np
import logging
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class TrainingMode(Enum):
    """How to handle learning during play."""
    INFERENCE_ONLY = auto()     # No learning, maximum speed
    EXPERIENCE_RECORD = auto()  # Record for later training
    ONLINE_LEARN = auto()       # Learn after each episode
    FULL_TRAIN = auto()         # Full training with backprop


@dataclass
class TrainingConfig:
    """Configuration for cocoon training."""
    mode: TrainingMode = TrainingMode.EXPERIENCE_RECORD
    batch_size: int = 32
    learning_rate: float = 0.001
    update_frequency: int = 10  # Steps between updates
    experience_buffer_size: int = 10000
    discount_factor: float = 0.99
    
    # VP Learning
    vp_update_enabled: bool = True
    vp_win_boost: float = 0.1
    vp_loss_penalty: float = 0.05
    
    # Concept Learning
    concept_strength_update: bool = True
    concept_decay_rate: float = 0.99
    concept_boost_on_success: float = 0.05


@dataclass
class Experience:
    """Single training experience."""
    observation: np.ndarray
    action: int
    reward: float
    next_observation: np.ndarray
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)


class CocoonTrainingAdapter:
    """
    Wraps a post-export cocoon for continued training.
    
    Works with:
    - Single organism cocoons (1 brain)
    - Multi-organism ensembles (N brains)
    """
    
    def __init__(self, cocoon, config: Optional[TrainingConfig] = None):
        """
        Args:
            cocoon: Loaded CocoonAgent from exported cocoon
            config: Training configuration
        """
        self.cocoon = cocoon
        self.config = config or TrainingConfig()
        
        # Experience buffers (per organism)
        self.experience_buffers: Dict[str, List[Experience]] = {}
        self.episode_rewards: Dict[str, List[float]] = {}
        
        # Stats
        self.total_steps = 0
        self.total_episodes = 0
        self.training_updates = 0
        
        # Initialize buffers for all organisms
        if hasattr(cocoon, 'organism_names'):
            for name in cocoon.organism_names:
                self.experience_buffers[name] = []
                self.episode_rewards[name] = []
        else:
            # Single organism
            self.experience_buffers['default'] = []
            self.episode_rewards['default'] = []
            
        logger.info(f"🎓 CocoonTrainingAdapter initialized")
        logger.info(f"   Mode: {self.config.mode.name}")
        logger.info(f"   Organisms: {len(self.experience_buffers)}")
    
    @property
    def num_organisms(self) -> int:
        return len(self.experience_buffers)
    
    @property
    def organism_names(self) -> List[str]:
        return list(self.experience_buffers.keys())
    
    def get_action(self, observation: np.ndarray, 
                   organism_name: str = 'default',
                   explore: bool = True) -> int:
        """
        Get action from cocoon, optionally with exploration.
        
        This wraps cocoon.get_action() with exploration noise
        for training purposes.
        """
        if self.config.mode == TrainingMode.INFERENCE_ONLY:
            explore = False
            
        action = self.cocoon.get_action(observation, explore=explore)
        return action
    
    def record_experience(self, 
                          observation: np.ndarray,
                          action: int,
                          reward: float,
                          next_observation: np.ndarray,
                          done: bool,
                          organism_name: str = 'default',
                          info: Optional[Dict] = None):
        """Record a training experience."""
        if self.config.mode == TrainingMode.INFERENCE_ONLY:
            return
            
        exp = Experience(
            observation=observation.copy(),
            action=action,
            reward=reward,
            next_observation=next_observation.copy(),
            done=done,
            info=info or {}
        )
        
        buffer = self.experience_buffers.get(organism_name, 
                                              self.experience_buffers.get('default', []))
        buffer.append(exp)
        
        # Trim buffer if too large
        if len(buffer) > self.config.experience_buffer_size:
            buffer.pop(0)
        
        self.total_steps += 1
        
        # Online learning update
        if (self.config.mode in [TrainingMode.ONLINE_LEARN, TrainingMode.FULL_TRAIN] and
            self.total_steps % self.config.update_frequency == 0):
            self._do_training_update(organism_name)
    
    def record_episode_end(self, 
                           organism_name: str = 'default',
                           total_reward: float = 0.0,
                           won: bool = False,
                           info: Optional[Dict] = None):
        """Record end of episode with final outcome."""
        self.total_episodes += 1
        
        if organism_name in self.episode_rewards:
            self.episode_rewards[organism_name].append(total_reward)
        
        # VP updates based on outcome
        if self.config.vp_update_enabled and hasattr(self.cocoon, 'brains'):
            try:
                # Find the brain for this organism
                idx = self.cocoon.organism_names.index(organism_name) if organism_name != 'default' else 0
                if idx < len(self.cocoon.brains):
                    brain = self.cocoon.brains[idx]
                    
                    # Update VP based on outcome
                    if won:
                        if hasattr(brain, 'vitality'):
                            brain.vitality = min(1.0, brain.vitality + self.config.vp_win_boost)
                        if hasattr(brain, 'pleasure'):
                            brain.pleasure = min(1.0, brain.pleasure + self.config.vp_win_boost * 0.5)
                    else:
                        if hasattr(brain, 'vitality'):
                            brain.vitality = max(0.0, brain.vitality - self.config.vp_loss_penalty)
            except:
                pass
        
        # Concept strength updates
        if self.config.concept_strength_update and hasattr(self.cocoon, 'atomic_language'):
            self._update_concept_strengths(organism_name, won)
        
        logger.debug(f"Episode {self.total_episodes} complete: {organism_name} "
                    f"reward={total_reward:.2f} won={won}")
    
    def _do_training_update(self, organism_name: str):
        """Perform a training update from experience buffer."""
        buffer = self.experience_buffers.get(organism_name, [])
        if len(buffer) < self.config.batch_size:
            return
            
        # Sample batch
        indices = np.random.choice(len(buffer), self.config.batch_size, replace=False)
        batch = [buffer[i] for i in indices]
        
        # Compute TD targets (for value function if available)
        observations = np.array([e.observation for e in batch])
        actions = np.array([e.action for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_obs = np.array([e.next_observation for e in batch])
        dones = np.array([e.done for e in batch])
        
        # If cocoon has a value head, update it
        if hasattr(self.cocoon, 'update_from_batch'):
            self.cocoon.update_from_batch(observations, actions, rewards, next_obs, dones)
            self.training_updates += 1
            
    def _update_concept_strengths(self, organism_name: str, won: bool):
        """
        Update atomic concept magnetism based on outcome.
        
        ═══════════════════════════════════════════════════════════════════════════
        GROK FIX: Now updates curiosity_magnetism instead of strength!
        
        THE PROBLEM: Modifying strength was causing language collapse.
        - generate_tokens() sorts vocab by strength descending
        - Combat concepts with inflated strength got lowest token IDs
        - Neural network favored low IDs → same few words repeated forever
        
        THE FIX: Use curiosity_magnetism for game learning, leave strength alone.
        Magnetism reflects learned attraction to concepts, strength reflects 
        intrinsic word importance (should not be inflated by game outcomes).
        ═══════════════════════════════════════════════════════════════════════════
        """
        if not hasattr(self.cocoon, 'atomic_language'):
            return
            
        lang = self.cocoon.atomic_language
        if not hasattr(lang, 'atoms'):
            return
            
        # Combat/survival concepts to update magnetism for
        combat_concepts = ['attack', 'defend', 'evade', 'pursue', 'tag', 
                          'survive', 'victory', 'dominance', 'coordination']
        
        for concept_name in combat_concepts:
            if concept_name in lang.atoms:
                atom = lang.atoms[concept_name]
                if won:
                    # GROK FIX: Update magnetism, not strength
                    if hasattr(atom, 'curiosity_magnetism'):
                        atom.curiosity_magnetism = min(1.0, atom.curiosity_magnetism + self.config.concept_boost_on_success)
                else:
                    # Decay magnetism on loss
                    if hasattr(atom, 'curiosity_magnetism'):
                        atom.curiosity_magnetism *= self.config.concept_decay_rate
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        stats = {
            'total_steps': self.total_steps,
            'total_episodes': self.total_episodes,
            'training_updates': self.training_updates,
            'buffer_sizes': {name: len(buf) for name, buf in self.experience_buffers.items()},
            'mean_episode_rewards': {}
        }
        
        for name, rewards in self.episode_rewards.items():
            if rewards:
                stats['mean_episode_rewards'][name] = np.mean(rewards[-100:])
                
        return stats
    
    def save_experiences(self, path: str):
        """Save experience buffers to disk."""
        import pickle
        data = {
            'buffers': self.experience_buffers,
            'episode_rewards': self.episode_rewards,
            'stats': self.get_training_stats()
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Saved {self.total_steps} experiences to {path}")
        
    def load_experiences(self, path: str):
        """Load experience buffers from disk."""
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.experience_buffers = data['buffers']
        self.episode_rewards = data['episode_rewards']
        logger.info(f"Loaded experiences from {path}")


# =============================================================================
# ARENA INTEGRATION FUNCTIONS
# =============================================================================

def create_cocoon_training_session(cocoon_path: str, 
                                   mode: TrainingMode = TrainingMode.EXPERIENCE_RECORD
                                   ) -> Tuple[Any, CocoonTrainingAdapter]:
    """
    Load a cocoon and create a training adapter.
    
    Args:
        cocoon_path: Path to exported cocoon directory
        mode: Training mode
        
    Returns:
        (cocoon, adapter) tuple
    """
    # Load cocoon
    if not os.path.exists(cocoon_path):
        raise FileNotFoundError(f"Cocoon not found: {cocoon_path}")
        
    # Find cocoon .py file
    if os.path.isdir(cocoon_path):
        py_files = [f for f in os.listdir(cocoon_path) 
                    if f.endswith('.py') and 'cocoon' in f.lower()]
        if not py_files:
            raise FileNotFoundError(f"No cocoon .py file in {cocoon_path}")
        module_name = py_files[0].replace('.py', '')
    else:
        module_name = os.path.basename(cocoon_path).replace('.py', '')
        cocoon_path = os.path.dirname(cocoon_path)
        
    sys.path.insert(0, cocoon_path)
    module = __import__(module_name)
    cocoon = module.CocoonAgent()
    
    # Create adapter
    config = TrainingConfig(mode=mode)
    adapter = CocoonTrainingAdapter(cocoon, config)
    
    return cocoon, adapter


def train_cocoon_on_drone_arena(cocoon_path: str,
                                 episodes: int = 10,
                                 mode: str = 'tag_battle',
                                 steps_per_episode: int = 1800,
                                 save_experiences: bool = True) -> Dict[str, Any]:
    """
    Train a cocoon using the drone arena.
    
    Args:
        cocoon_path: Path to exported cocoon
        episodes: Number of training episodes
        mode: Drone game mode (tag_battle, zone_control, etc.)
        steps_per_episode: Max steps per episode
        save_experiences: Whether to save experiences to disk
        
    Returns:
        Training statistics
    """
    from .cocoon_drone_arena import CocoonDroneArena, DroneGameMode, DroneArenaConfig
    
    # Load cocoon with training adapter
    cocoon, adapter = create_cocoon_training_session(
        cocoon_path, 
        TrainingMode.EXPERIENCE_RECORD
    )
    
    # Parse mode
    mode_enum = getattr(DroneGameMode, mode.upper(), DroneGameMode.TAG_BATTLE)
    
    results = {
        'episodes': [],
        'total_rewards': [],
        'winners': [],
        'stats': None
    }
    
    print(f"\n🎓 DRONE TRAINING SESSION")
    print(f"   Cocoon: {cocoon_path}")
    print(f"   Mode: {mode_enum.value}")
    print(f"   Episodes: {episodes}")
    print(f"   Organisms: {adapter.num_organisms}")
    
    for ep in range(episodes):
        print(f"\n{'='*60}")
        print(f"Episode {ep + 1}/{episodes}")
        print(f"{'='*60}")
        
        # Create fresh arena for each episode
        config = DroneArenaConfig()
        # Note: global_config should be passed for Language-Game Bridge settings
        # In training context, we use defaults since cocoons are standalone
        arena = CocoonDroneArena(
            cocoon=cocoon,
            mode=mode_enum,
            config=config,
            team_split="half",
            global_config=None  # TODO: Pass runtime config when available
        )
        
        # Run episode with experience recording
        episode_rewards = {name: 0.0 for name in adapter.organism_names}
        prev_observations = {}
        
        # Get initial observations
        for drone_id, drone in arena.drones.items():
            if drone.alive:
                prev_observations[drone_id] = arena.get_observation(drone)
        
        while not arena.game_state.finished and arena.game_state.step_count < steps_per_episode:
            # Get actions and step
            step_rewards = arena.step()
            
            # Record experiences
            for drone_id, drone in arena.drones.items():
                if drone_id in prev_observations:
                    obs = arena.get_observation(drone)
                    reward = step_rewards.get(drone_id, 0.0)
                    done = not drone.alive or arena.game_state.finished
                    
                    # Map to organism name
                    org_name = drone_id if drone_id in adapter.organism_names else 'default'
                    
                    adapter.record_experience(
                        observation=prev_observations[drone_id],
                        action=0,  # TODO: track actual action
                        reward=reward,
                        next_observation=obs,
                        done=done,
                        organism_name=org_name,
                        info={'team': drone.team, 'step': arena.game_state.step_count}
                    )
                    
                    episode_rewards[org_name] = episode_rewards.get(org_name, 0.0) + reward
                    prev_observations[drone_id] = obs
        
        # Record episode ends
        for org_name, total_reward in episode_rewards.items():
            # Determine if this organism won
            drone = arena.drones.get(org_name)
            won = False
            if drone:
                won = (drone.team == arena.game_state.winner)
            
            adapter.record_episode_end(
                organism_name=org_name,
                total_reward=total_reward,
                won=won
            )
        
        # Record results
        results['episodes'].append(ep + 1)
        results['total_rewards'].append(sum(episode_rewards.values()))
        results['winners'].append(arena.game_state.winner)
        
        print(f"Winner: {arena.game_state.winner}")
        print(f"Blue: {arena.game_state.blue_score:.1f}, Red: {arena.game_state.red_score:.1f}")
    
    # Save experiences
    if save_experiences:
        exp_path = os.path.join(cocoon_path, f'drone_training_{mode}_{int(time.time())}.pkl')
        adapter.save_experiences(exp_path)
        results['experience_path'] = exp_path
    
    results['stats'] = adapter.get_training_stats()
    
    print(f"\n🎓 TRAINING COMPLETE")
    print(f"   Total steps: {results['stats']['total_steps']}")
    print(f"   Mean reward: {np.mean(results['total_rewards']):.2f}")
    
    return results


def train_cocoon_on_sphere_arena(cocoon_path: str,
                                  episodes: int = 10,
                                  balls: int = 1,
                                  max_misses: int = 10,
                                  save_experiences: bool = True) -> Dict[str, Any]:
    """
    Train a cocoon using the sphere arena (already works, this adds experience recording).
    """
    from sphere_arena import SphereArena, GameMode
    
    cocoon, adapter = create_cocoon_training_session(
        cocoon_path,
        TrainingMode.EXPERIENCE_RECORD
    )
    
    results = {
        'episodes': [],
        'scores': [],
        'stats': None
    }
    
    print(f"\n🌐 SPHERE TRAINING SESSION")
    print(f"   Cocoon: {cocoon_path}")
    print(f"   Episodes: {episodes}")
    print(f"   Balls: {balls}")
    
    for ep in range(episodes):
        print(f"\n--- Episode {ep + 1}/{episodes} ---")
        
        arena = SphereArena(
            agent=cocoon,
            max_misses=max_misses,
            mode=GameMode.SWARM_DEFENSE,
            headless=True,  # No rendering during training
            global_config=None  # Standalone training
        )
        
        # Run with training hooks
        result = arena.run()
        
        # SphereArena returns collective_catches/collective_misses, not score/misses
        score = result.get('collective_catches', 0)
        misses = result.get('collective_misses', 0)
        won = misses < max_misses
        
        # Record episode end for all organisms
        for org_name in adapter.organism_names:
            adapter.record_episode_end(
                organism_name=org_name,
                total_reward=score,
                won=won
            )
        
        results['episodes'].append(ep + 1)
        results['scores'].append(score)
        
        print(f"Score: {score}, Misses: {misses}")
    
    if save_experiences:
        exp_path = os.path.join(cocoon_path, f'sphere_training_{int(time.time())}.pkl')
        adapter.save_experiences(exp_path)
        results['experience_path'] = exp_path
    
    results['stats'] = adapter.get_training_stats()
    
    print(f"\n🌐 TRAINING COMPLETE")
    print(f"   Mean score: {np.mean(results['scores']):.2f}")
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train a cocoon on various arenas")
    parser.add_argument('cocoon_path', help='Path to exported cocoon')
    parser.add_argument('--arena', choices=['drone', 'sphere', 'proton'], default='drone')
    parser.add_argument('--mode', default='tag_battle', help='Game mode (for drone arena)')
    parser.add_argument('--episodes', type=int, default=5)
    parser.add_argument('--steps', type=int, default=1800)
    parser.add_argument('--no-save', action='store_true', help='Do not save experiences')
    
    args = parser.parse_args()
    
    if args.arena == 'drone':
        results = train_cocoon_on_drone_arena(
            args.cocoon_path,
            episodes=args.episodes,
            mode=args.mode,
            steps_per_episode=args.steps,
            save_experiences=not args.no_save
        )
    elif args.arena == 'sphere':
        results = train_cocoon_on_sphere_arena(
            args.cocoon_path,
            episodes=args.episodes,
            save_experiences=not args.no_save
        )
    else:
        print("Proton training not yet implemented via CLI")
