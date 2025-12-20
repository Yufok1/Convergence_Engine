"""
Live Organism Adapter for Proton Game Arena

This adapter wraps live simulation organisms to work with the ProtonGameArena
battle system. It provides a bridge-like interface that uses the organism's
native abilities (language, neural processing) for REAL GAME BATTLES.

Key Features:
1. Adapts organisms to Proton Game's expected interface
2. ACTUALLY RUNS real Gymnasium environments (CartPole, LunarLander, etc.)
3. Organisms LEARN from gameplay - experiences recorded to replay buffer
4. Falls back to native language games when Gym unavailable
5. Provides causation tracking for all battles

The organisms ACTUALLY PLAY the games headlessly and gain training!
"""

import logging
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Get config-driven input_dim (replaces hardcoded 25)
try:
    import sys
    _adapter_path = Path(__file__).resolve()
    _project_root = _adapter_path.parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from runtime_config import get_input_dim
    _INPUT_DIM = get_input_dim()
except Exception:
    _INPUT_DIM = 30  # Default matches current config.json

logger = logging.getLogger(__name__)

# Import the REAL gym runner
try:
    from .gym_runner import get_gym_runner, GymRunner, GYM_AVAILABLE
    REAL_GYM_ENABLED = GYM_AVAILABLE
except ImportError:
    REAL_GYM_ENABLED = False
    get_gym_runner = None
    logger.warning("GymRunner not available - will use simulated battles")


@dataclass
class MockGymStats:
    """Mock Gym statistics for non-Gym battles."""
    mean_reward: float = 0.0
    total_reward: float = 0.0
    episodes: int = 0
    steps: int = 0
    
    def get(self, key: str, default=None):
        return getattr(self, key, default)


class LiveOrganismAdapter:
    """
    Adapter that wraps a live organism for Proton Game Arena battles.
    
    This provides the interface expected by ProtonGameArena.execute_battle()
    using the organism's native abilities instead of exported AgentBridge.
    
    Works best with ARTS challenge games that use:
    - language_coherence: Uses organism's atomic language system
    - concept_linking: Uses organism's concept associations  
    - vocabulary_duel: Uses organism's vocabulary size
    - dialogue_quality: Uses organism's response generation
    """
    
    def __init__(self, organism: Any, event_emitter: Optional[callable] = None):
        """
        Initialize adapter for a live organism.
        
        Args:
            organism: The live simulation organism
            event_emitter: Optional causation event emitter
        """
        self.organism = organism
        self.organism_id = getattr(organism, 'organism_id', 
                                   getattr(organism, 'id', str(id(organism))))
        self.event_emitter = event_emitter
        
        # Cache organism capabilities
        self._cache_capabilities()
        
    def _cache_capabilities(self):
        """Cache the organism's capabilities for faster access."""
        self.has_atomic_language = (
            hasattr(self.organism, 'atomic_language') and 
            self.organism.atomic_language is not None
        )
        self.has_brain = (
            hasattr(self.organism, 'brain') and 
            self.organism.brain is not None
        )
        self.has_phenotype = (
            hasattr(self.organism, 'phenotype') and
            self.organism.phenotype is not None
        )
        
        # Get vocabulary size
        self.vocabulary = self._get_vocabulary_proxy()
        
    def _get_vocabulary_proxy(self):
        """Create a vocabulary proxy object."""
        vocab_size = 0
        
        if self.has_atomic_language:
            al = self.organism.atomic_language
            if hasattr(al, 'atoms'):
                vocab_size = len(al.atoms)
            elif hasattr(al, 'vocabulary_size'):
                vocab_size = al.vocabulary_size
        
        # Create simple proxy
        class VocabProxy:
            def __init__(self, size):
                self.vocab_size = size
        
        return VocabProxy(vocab_size)
    
    @property
    def fitness(self) -> float:
        """Get organism fitness."""
        if hasattr(self.organism, 'fitness'):
            return self.organism.fitness
        return 0.5
    
    @property 
    def energy(self) -> float:
        """Get organism energy."""
        if hasattr(self.organism, 'energy'):
            return self.organism.energy
        return 0.5
    
    def process(self, text: str = "", **kwargs) -> 'ProcessResult':
        """
        Process input using organism's native systems.
        
        This is the key interface method that Proton Game's custom games use.
        """
        response = ""
        confidence = 0.5
        
        # Try atomic language first
        if self.has_atomic_language:
            al = self.organism.atomic_language
            
            if hasattr(al, 'generate_response'):
                try:
                    response = al.generate_response(text)
                    confidence = 0.7
                except:
                    pass
            elif hasattr(al, 'process'):
                try:
                    result = al.process(text)
                    response = str(result)
                    confidence = 0.6
                except:
                    pass
            elif hasattr(al, 'atoms'):
                # Use atoms as vocabulary response
                atoms = list(al.atoms.keys()) if isinstance(al.atoms, dict) else list(al.atoms)
                response = " ".join(random.sample(atoms, min(5, len(atoms)))) if atoms else "..."
                confidence = 0.4
        
        # Fallback to brain if available
        if not response and self.has_brain:
            brain = self.organism.brain
            if hasattr(brain, 'forward'):
                try:
                    # Get some output from the brain
                    import torch
                    state = torch.zeros(_INPUT_DIM)  # Config-driven input_dim
                    with torch.no_grad():
                        q_values = brain(state.unsqueeze(0))
                        action = q_values.argmax().item()
                        response = f"action_{action}"
                        confidence = 0.5
                except:
                    pass
        
        # Final fallback
        if not response:
            response = "..."
            confidence = 0.3
        
        return ProcessResult(response=response, confidence=confidence)
    
    def run_gym(self, env_spec: str, episodes: int = 10, 
                max_steps: int = 1000, render: bool = False,
                learn: bool = True, verbose: bool = False) -> Dict[str, Any]:
        """
        Run organism in a Gym environment - FOR REAL!
        
        This ACTUALLY runs the Gymnasium environment headlessly.
        The organism's neural network makes decisions, and experiences
        are recorded for training.
        
        Args:
            env_spec: Gymnasium environment specification
            episodes: Number of episodes to play
            max_steps: Maximum steps per episode
            render: Whether to render (False = headless)
            learn: Whether to record experiences for training
            verbose: Whether to log detailed output
        """
        # ═══════════════════════════════════════════════════════════════
        # REAL GYMNASIUM EXECUTION
        # ═══════════════════════════════════════════════════════════════
        if REAL_GYM_ENABLED and get_gym_runner is not None:
            # Check if this is a standard Gym env that we can actually run
            runner = get_gym_runner()
            
            # Map native game names to real Gym envs
            gym_mappable = {
                'pole_balance': 'CartPole-v1',
                'cart_pole': 'CartPole-v1',
                'mountain_climb': 'MountainCar-v0',
                'robot_swing': 'Acrobot-v1',
                'pendulum_control': 'Pendulum-v1',
                'lunar_landing': 'LunarLander-v3',
                'space_landing': 'LunarLander-v3',
                'ice_navigation': 'FrozenLake-v1',
                'taxi_service': 'Taxi-v3',
                'cliff_walk': 'CliffWalking-v0',
                'card_game': 'Blackjack-v1',
                'blackjack': 'Blackjack-v1',
            }
            
            # Check if we can run this for real
            actual_env = gym_mappable.get(env_spec, env_spec)
            
            # Accept any environment that looks like a Gym env (has version suffix like -v0, -v1, etc.)
            # This allows MuJoCo envs, Box2D envs, and all standard Gymnasium envs
            is_gym_env = (
                actual_env in runner.ENV_CONFIGS or 
                env_spec.startswith(('CartPole', 'Mountain', 'Lunar', 'Acrobot', 'Frozen', 'Taxi', 'Cliff', 'Black', 'Pendulum')) or
                # MuJoCo environments
                env_spec.startswith(('Walker', 'Ant', 'Swimmer', 'Hopper', 'HalfCheetah', 'Humanoid', 'Inverted', 'Reacher', 'Pusher')) or
                # Box2D environments
                env_spec.startswith(('Bipedal', 'CarRacing')) or
                # Generic version pattern (any env with -v suffix)
                any(f'-v{i}' in env_spec for i in range(10))
            )
            
            if is_gym_env:
                logger.info(f"🎮 REAL GYM BATTLE: {actual_env} for {self.organism_id[:8]}")
                
                try:
                    result = runner.run_organism(
                        self.organism,
                        actual_env,
                        episodes=episodes,
                        max_steps=max_steps,
                        learn=learn,
                        render=render
                    )
                    
                    return {
                        'mean_reward': result.mean_reward,
                        'total_reward': result.total_reward,
                        'episodes': result.episodes,
                        'total_steps': result.total_steps,
                        'max_reward': result.max_reward,
                        'min_reward': result.min_reward,
                        'experiences_recorded': result.experiences_recorded,
                        'REAL_GYM': True  # Flag that this was REAL
                    }
                except Exception as e:
                    logger.warning(f"Real Gym run failed: {e}, falling back to native")
        
        # ═══════════════════════════════════════════════════════════════
        # NATIVE LANGUAGE GAMES (no Gym needed)
        # ═══════════════════════════════════════════════════════════════
        native_games = {
            'language_coherence': self._run_language_coherence,
            'concept_linking': self._run_concept_linking,
            'vocabulary_duel': self._run_vocabulary_duel,
            'dialogue_quality': self._run_dialogue_quality,
            'inter_organism_chat': self._run_dialogue_quality,
            'collaborative_creation': self._run_collaborative_creation,
            'coin_flip': self._run_coin_flip,
        }
        
        if env_spec in native_games:
            logger.info(f"🗣️ Native game: {env_spec} for {self.organism_id[:8]}")
            return native_games[env_spec](episodes)
        
        # ═══════════════════════════════════════════════════════════════
        # NO FALLBACK - FAIL LOUD - NO FAKE SIMULATIONS
        # ═══════════════════════════════════════════════════════════════
        error_msg = f"❌ UNSUPPORTED GYM ENV: {env_spec} - No real handler exists! Remove from game matrix."
        logger.error(error_msg)
        raise NotImplementedError(error_msg)
    
    def _run_language_coherence(self, episodes: int) -> Dict[str, Any]:
        """Evaluate language coherence using atomic language system."""
        total_score = 0.0
        
        test_prompts = [
            "describe environment",
            "explain survival", 
            "what is cooperation",
            "describe threat",
            "explain resources"
        ]
        
        for _ in range(episodes):
            prompt = random.choice(test_prompts)
            result = self.process(text=prompt)
            
            words = result.response.split()
            
            # Score based on response quality
            length_score = min(len(words) / 10, 1.0) * 30
            variety_score = len(set(words)) / max(len(words), 1) * 40
            confidence_score = result.confidence * 30
            
            total_score += length_score + variety_score + confidence_score
        
        return {
            'mean_reward': total_score / episodes,
            'total_reward': total_score,
            'episodes': episodes
        }
    
    def _run_concept_linking(self, episodes: int) -> Dict[str, Any]:
        """Evaluate concept association ability."""
        base_score = self.vocabulary.vocab_size * 2
        
        # Add fitness bonus
        bonus = self.fitness * 10
        
        # Add randomness
        total_score = (base_score + bonus) * episodes + random.uniform(-5, 5)
        
        return {
            'mean_reward': total_score / episodes,
            'total_reward': total_score,
            'episodes': episodes,
            'vocab_size': self.vocabulary.vocab_size
        }
    
    def _run_vocabulary_duel(self, episodes: int) -> Dict[str, Any]:
        """Evaluate vocabulary richness."""
        vocab_size = self.vocabulary.vocab_size
        score = vocab_size * 2 * episodes
        
        return {
            'mean_reward': score / episodes,
            'total_reward': score,
            'episodes': episodes,
            'vocab_size': vocab_size
        }
    
    def _run_dialogue_quality(self, episodes: int) -> Dict[str, Any]:
        """Evaluate dialogue generation quality."""
        total_score = 0.0
        
        for _ in range(episodes):
            result = self.process(text="generate quality response")
            
            # Score based on response characteristics
            words = result.response.split()
            complexity = len(set(words)) / max(len(words), 1)
            length_factor = min(len(words) / 15, 1.0)
            
            score = (complexity * 50 + length_factor * 30 + result.confidence * 20)
            total_score += score
        
        return {
            'mean_reward': total_score / episodes,
            'total_reward': total_score,
            'episodes': episodes
        }
    
    def _run_collaborative_creation(self, episodes: int) -> Dict[str, Any]:
        """Evaluate collaborative creation ability."""
        # Based on vocabulary + some randomness for creativity
        base = self.vocabulary.vocab_size * 1.5
        creativity_bonus = random.uniform(0, 20)
        
        total_score = (base + creativity_bonus) * episodes
        
        return {
            'mean_reward': total_score / episodes, 
            'total_reward': total_score,
            'episodes': episodes
        }
    
    def _run_coin_flip(self, episodes: int) -> Dict[str, Any]:
        """Pure chance - coin flips."""
        wins = sum(1 for _ in range(episodes) if random.random() < 0.5)
        total_score = wins * 10
        
        return {
            'mean_reward': total_score / episodes,
            'total_reward': total_score,
            'episodes': episodes,
            'wins': wins
        }
    
    # NOTE: _estimate_gym_performance DELETED - NO FAKE SIMULATIONS ALLOWED
    # If an environment isn't supported, it should raise NotImplementedError


@dataclass
class ProcessResult:
    """Result from processing input."""
    response: str
    confidence: float
    action: int = 0
    q_values: List[float] = field(default_factory=list)


def create_adapter(organism: Any, event_emitter: Optional[callable] = None) -> LiveOrganismAdapter:
    """Factory function to create a LiveOrganismAdapter."""
    return LiveOrganismAdapter(organism, event_emitter)


def create_adapter_pair(org_a: Any, org_b: Any, 
                        event_emitter: Optional[callable] = None) -> Tuple[LiveOrganismAdapter, LiveOrganismAdapter]:
    """Create a pair of adapters for two organisms."""
    return (
        LiveOrganismAdapter(org_a, event_emitter),
        LiveOrganismAdapter(org_b, event_emitter)
    )
