"""
AgentBridge - Universal Interface for Butterfly Agents

This is the deployable middleware system that connects exported Butterfly agents
to any environment, application, or interface. Not a standalone app - a BRIDGE.

Usage Modes:
    1. Gymnasium/Gym Environment Runner
    2. HTTP/REST API Server (for external applications)
    3. WebSocket Real-time Interface
    4. Python Library Integration
    5. Interactive CLI (chat + environment hybrid)

Architecture:
    External World → InputAdapter → UnifiedState → AgentCore → UnifiedOutput → OutputAdapter → Response

Example:
    # Load exported agent
    bridge = AgentBridge.load("./my_exported_agent")
    
    # Mode 1: Run in Gym environment
    bridge.run_gym("CartPole-v1", episodes=100)
    
    # Mode 2: Serve as HTTP API
    bridge.serve(port=8080)
    
    # Mode 3: Interactive CLI
    bridge.interactive()
    
    # Mode 4: Direct Python integration
    result = bridge.process(
        text="Enemy approaching from north",
        context={"threat_level": 0.8, "energy": 0.3}
    )
    print(result.action, result.response, result.confidence)
"""

import json
import numpy as np
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from collections import deque
import random

logger = logging.getLogger(__name__)

# Try imports - graceful degradation if not available
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BridgeResult:
    """Unified result from any bridge operation."""
    action: int                          # Discrete action (0-5)
    action_name: str                     # Human-readable action name
    response: str                        # Language response (if applicable)
    confidence: float                    # Decision confidence (0-1)
    q_values: List[float]               # Raw Q-values for all actions
    state_vector: List[float]           # The 18D state used for decision
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'action_name': self.action_name,
            'response': self.response,
            'confidence': self.confidence,
            'q_values': self.q_values,
            'state_vector': self.state_vector,
            'metadata': self.metadata
        }


@dataclass  
class AgentConfig:
    """Configuration for the bridge."""
    # Action space
    action_names: List[str] = field(default_factory=lambda: [
        'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'
    ])
    num_actions: int = 6
    
    # State space
    state_dim: int = 18
    
    # Learning
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    learning_rate: float = 0.001
    gamma: float = 0.99
    batch_size: int = 32
    
    # Language
    max_response_length: int = 32
    temperature: float = 1.0
    
    # Server
    default_port: int = 8080
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_names': self.action_names,
            'num_actions': self.num_actions,
            'state_dim': self.state_dim,
            'epsilon': self.epsilon,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'batch_size': self.batch_size,
            'max_response_length': self.max_response_length,
            'temperature': self.temperature
        }


# =============================================================================
# INPUT ADAPTERS - Convert various inputs to unified 18D state
# =============================================================================

class InputAdapter:
    """Base class for input adapters."""
    
    def to_state(self, input_data: Any, context: Optional[Dict] = None) -> np.ndarray:
        """Convert input to 18D state vector."""
        raise NotImplementedError


class GymInputAdapter(InputAdapter):
    """Adapter for Gymnasium/Gym observations."""
    
    def __init__(self, state_dim: int = 18):
        self.state_dim = state_dim
    
    def to_state(self, obs: Any, context: Optional[Dict] = None) -> np.ndarray:
        """Convert Gym observation to state vector."""
        if isinstance(obs, np.ndarray):
            obs_flat = obs.flatten()
        elif isinstance(obs, (list, tuple)):
            obs_flat = np.array(obs).flatten()
        elif isinstance(obs, dict):
            # Handle dict observations (common in many envs)
            values = []
            for v in obs.values():
                if isinstance(v, np.ndarray):
                    values.extend(v.flatten().tolist())
                elif isinstance(v, (int, float)):
                    values.append(float(v))
            obs_flat = np.array(values)
        else:
            obs_flat = np.array([float(obs)])
        
        # Pad or truncate to state_dim
        if len(obs_flat) < self.state_dim:
            state = np.zeros(self.state_dim)
            state[:len(obs_flat)] = obs_flat
        else:
            state = obs_flat[:self.state_dim]
        
        return state.astype(np.float32)


class TextInputAdapter(InputAdapter):
    """Adapter for text/chat input."""
    
    # Semantic keywords that map to state dimensions
    SEMANTIC_MAP = {
        # Energy/vitality indicators (dim 0-2)
        'tired': (0, -0.3), 'exhausted': (0, -0.5), 'energetic': (0, 0.5), 
        'hungry': (1, -0.4), 'starving': (1, -0.7), 'full': (1, 0.4),
        'healthy': (2, 0.5), 'sick': (2, -0.4), 'injured': (2, -0.5),
        
        # Threat/danger indicators (dim 3-5)
        'danger': (3, 0.6), 'threat': (3, 0.5), 'safe': (3, -0.5),
        'enemy': (4, 0.6), 'predator': (4, 0.7), 'hostile': (4, 0.5),
        'attack': (5, 0.6), 'flee': (5, 0.4), 'fight': (5, 0.5),
        
        # Social indicators (dim 6-8)
        'friend': (6, 0.6), 'ally': (6, 0.5), 'stranger': (6, 0.0),
        'help': (7, 0.5), 'cooperate': (7, 0.6), 'share': (7, 0.4),
        'compete': (8, 0.5), 'rival': (8, 0.4), 'opponent': (8, 0.3),
        
        # Resource indicators (dim 9-11)
        'food': (9, 0.5), 'water': (9, 0.4), 'resource': (9, 0.3),
        'abundant': (10, 0.6), 'scarce': (10, -0.5), 'plenty': (10, 0.5),
        'opportunity': (11, 0.5), 'chance': (11, 0.4), 'reward': (11, 0.6),
        
        # Environmental indicators (dim 12-14)
        'crowded': (12, 0.5), 'empty': (12, -0.4), 'busy': (12, 0.3),
        'hot': (13, 0.3), 'cold': (13, -0.3), 'comfortable': (13, 0.0),
        'dark': (14, -0.2), 'bright': (14, 0.2), 'visible': (14, 0.3),
        
        # Emotional/state indicators (dim 15-17)
        'confident': (15, 0.5), 'scared': (15, -0.5), 'uncertain': (15, -0.2),
        'happy': (16, 0.5), 'sad': (16, -0.4), 'angry': (16, 0.3),
        'calm': (17, -0.3), 'stressed': (17, 0.4), 'relaxed': (17, -0.4),
    }
    
    def __init__(self, state_dim: int = 18, vocabulary: Optional[Dict] = None):
        self.state_dim = state_dim
        self.vocabulary = vocabulary or {}
        
    def to_state(self, text: str, context: Optional[Dict] = None) -> np.ndarray:
        """Convert text to state vector using semantic mapping."""
        state = np.zeros(self.state_dim, dtype=np.float32)
        
        # Start with neutral baseline
        state[:] = 0.5
        
        # Parse text for semantic keywords
        words = text.lower().split()
        for word in words:
            # Strip punctuation
            word = ''.join(c for c in word if c.isalnum())
            if word in self.SEMANTIC_MAP:
                dim, value = self.SEMANTIC_MAP[word]
                state[dim] = np.clip(state[dim] + value, 0.0, 1.0)
        
        # Apply explicit context overrides
        if context:
            context_map = {
                'energy': 0, 'hunger': 1, 'health': 2,
                'danger': 3, 'threat': 3, 'threat_level': 3,
                'enemy_distance': 4, 'hostility': 4,
                'attack_imminent': 5,
                'friend_nearby': 6, 'social': 6,
                'cooperation': 7, 'help_available': 7,
                'competition': 8, 'rivalry': 8,
                'food_available': 9, 'resources': 9,
                'abundance': 10, 'scarcity': 10,
                'opportunity': 11, 'reward_potential': 11,
                'crowding': 12, 'density': 12,
                'temperature': 13,
                'visibility': 14,
                'confidence': 15,
                'mood': 16, 'emotion': 16,
                'stress': 17, 'calmness': 17,
            }
            for key, dim in context_map.items():
                if key in context:
                    value = float(context[key])
                    # Normalize to 0-1 if needed
                    if value > 1.0:
                        value = value / 100.0  # Assume percentage
                    state[dim] = np.clip(value, 0.0, 1.0)
        
        return state


class ContextInputAdapter(InputAdapter):
    """Adapter for structured context dictionaries."""
    
    def __init__(self, state_dim: int = 18):
        self.state_dim = state_dim
        
    def to_state(self, context: Dict[str, Any], _: Optional[Dict] = None) -> np.ndarray:
        """Convert context dict directly to state vector."""
        state = np.zeros(self.state_dim, dtype=np.float32)
        
        # Direct mapping for known keys
        mapping = [
            'energy', 'hunger', 'health',
            'danger', 'enemy_distance', 'attack_imminent',
            'friend_nearby', 'cooperation', 'competition',
            'food_available', 'abundance', 'opportunity',
            'crowding', 'temperature', 'visibility',
            'confidence', 'mood', 'stress'
        ]
        
        for i, key in enumerate(mapping):
            if i < self.state_dim and key in context:
                state[i] = float(context[key])
        
        # Also check for 'state' key with raw array
        if 'state' in context:
            raw = np.array(context['state']).flatten()
            state[:min(len(raw), self.state_dim)] = raw[:self.state_dim]
        
        return state


# =============================================================================
# OUTPUT ADAPTERS - Convert agent decisions to various formats
# =============================================================================

class OutputAdapter:
    """Base class for output adapters."""
    
    def from_result(self, result: BridgeResult) -> Any:
        """Convert BridgeResult to specific output format."""
        raise NotImplementedError


class GymOutputAdapter(OutputAdapter):
    """Adapter for Gymnasium/Gym actions."""
    
    def from_result(self, result: BridgeResult) -> int:
        """Return discrete action for Gym environment."""
        return result.action


class JSONOutputAdapter(OutputAdapter):
    """Adapter for JSON API responses."""
    
    def from_result(self, result: BridgeResult) -> Dict[str, Any]:
        """Return full JSON response."""
        return result.to_dict()


class TextOutputAdapter(OutputAdapter):
    """Adapter for text/chat responses."""
    
    def __init__(self, include_action: bool = True):
        self.include_action = include_action
    
    def from_result(self, result: BridgeResult) -> str:
        """Return text response, optionally with action context."""
        if result.response:
            if self.include_action:
                return f"[{result.action_name.upper()}] {result.response}"
            return result.response
        else:
            # Generate action-based response if no language response
            action_responses = {
                0: "I'll move to a better position.",
                1: "Let's work together on this.",
                2: "I need to compete for resources.",
                3: "I should rest and recover.",
                4: "Conditions are right for reproduction.",
                5: "I need to isolate myself for safety.",
            }
            return action_responses.get(result.action, f"Action: {result.action_name}")


# =============================================================================
# LANGUAGE SYSTEM - Portable vocabulary and text generation
# =============================================================================

class PortableVocabulary:
    """Lightweight vocabulary for exported agents."""
    
    SPECIAL_TOKENS = {
        '<PAD>': 0,
        '<UNK>': 1,
        '<START>': 2,
        '<END>': 3,
    }
    
    def __init__(self):
        self.word_to_id: Dict[str, int] = dict(self.SPECIAL_TOKENS)
        self.id_to_word: Dict[int, str] = {v: k for k, v in self.SPECIAL_TOKENS.items()}
        self.word_frequencies: Dict[str, int] = {}
        
    @property
    def vocab_size(self) -> int:
        return len(self.word_to_id)
    
    def add_word(self, word: str) -> int:
        """Add word to vocabulary, return its ID."""
        if word in self.word_to_id:
            self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
            return self.word_to_id[word]
        
        new_id = len(self.word_to_id)
        self.word_to_id[word] = new_id
        self.id_to_word[new_id] = word
        self.word_frequencies[word] = 1
        return new_id
    
    def get_id(self, word: str) -> int:
        return self.word_to_id.get(word, self.SPECIAL_TOKENS['<UNK>'])
    
    def get_word(self, token_id: int) -> str:
        return self.id_to_word.get(token_id, '<UNK>')
    
    def encode(self, words: List[str], add_special: bool = True) -> List[int]:
        """Encode words to token IDs."""
        tokens = []
        if add_special:
            tokens.append(self.SPECIAL_TOKENS['<START>'])
        tokens.extend([self.get_id(w) for w in words])
        if add_special:
            tokens.append(self.SPECIAL_TOKENS['<END>'])
        return tokens
    
    def decode(self, tokens: List[int], skip_special: bool = True) -> List[str]:
        """Decode token IDs to words."""
        words = []
        special_ids = set(self.SPECIAL_TOKENS.values())
        for t in tokens:
            if skip_special and t in special_ids:
                continue
            words.append(self.get_word(t))
        return words
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'word_to_id': self.word_to_id,
            'word_frequencies': self.word_frequencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortableVocabulary':
        vocab = cls()
        vocab.word_to_id = data.get('word_to_id', dict(cls.SPECIAL_TOKENS))
        vocab.id_to_word = {int(v): k for k, v in vocab.word_to_id.items()}
        vocab.word_frequencies = data.get('word_frequencies', {})
        return vocab
    
    @classmethod
    def load(cls, path: Path) -> 'PortableVocabulary':
        """Load vocabulary from atomic_language.json."""
        if not path.exists():
            return cls()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vocab = cls()
        
        # Handle different atomic_language.json formats
        if 'word_to_id' in data:
            vocab.word_to_id = data['word_to_id']
        elif 'concepts' in data:
            # Extract words from atomic concepts
            for concept_id, concept_data in data['concepts'].items():
                vocab.add_word(concept_id)
        elif 'vocabulary' in data:
            for word in data['vocabulary']:
                vocab.add_word(word)
        
        vocab.id_to_word = {int(v): k for k, v in vocab.word_to_id.items()}
        return vocab


# =============================================================================
# EXPERIENCE BUFFER - Learning from all interaction types
# =============================================================================

class UnifiedExperienceBuffer:
    """Experience buffer that handles all interaction types."""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.language_buffer: deque = deque(maxlen=capacity)  # For language experiences
        
    def add(self, 
            state: np.ndarray, 
            action: int, 
            reward: float,
            next_state: np.ndarray, 
            done: bool,
            source: str = 'env',
            input_tokens: Optional[List[int]] = None,
            target_tokens: Optional[List[int]] = None):
        """Add experience from any source."""
        self.buffer.append({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'source': source,
            'timestamp': time.time()
        })
        
        # Also store language experiences separately
        if input_tokens or target_tokens:
            self.language_buffer.append({
                'input_tokens': input_tokens or [],
                'target_tokens': target_tokens or [],
                'reward': reward,
                'timestamp': time.time()
            })
    
    def sample(self, batch_size: int) -> List[Dict]:
        """Sample batch of experiences."""
        batch_size = min(batch_size, len(self.buffer))
        return random.sample(list(self.buffer), batch_size)
    
    def sample_language(self, batch_size: int) -> List[Dict]:
        """Sample batch of language experiences."""
        batch_size = min(batch_size, len(self.language_buffer))
        if batch_size == 0:
            return []
        return random.sample(list(self.language_buffer), batch_size)
    
    def __len__(self) -> int:
        return len(self.buffer)
    
    def save(self, path: Path):
        """Save buffer to disk."""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump({
                'buffer': list(self.buffer),
                'language_buffer': list(self.language_buffer)
            }, f)
    
    @classmethod
    def load(cls, path: Path, capacity: int = 10000) -> 'UnifiedExperienceBuffer':
        """Load buffer from disk."""
        import pickle
        buf = cls(capacity)
        if path.exists():
            with open(path, 'rb') as f:
                data = pickle.load(f)
            for exp in data.get('buffer', []):
                buf.buffer.append(exp)
            for exp in data.get('language_buffer', []):
                buf.language_buffer.append(exp)
        return buf


# =============================================================================
# AGENT BRIDGE - The main unified interface
# =============================================================================

class AgentBridge:
    """
    Universal interface for Butterfly agents.
    
    This is the deployable system that connects agents to:
    - Gymnasium/Gym environments
    - HTTP/REST APIs
    - WebSocket connections
    - Direct Python integration
    - Interactive CLI
    """
    
    ACTION_NAMES = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
    
    def __init__(self,
                 brain_path: Optional[Path] = None,
                 config: Optional[AgentConfig] = None,
                 vocabulary: Optional[PortableVocabulary] = None):
        """
        Initialize the bridge.
        
        Args:
            brain_path: Path to ONNX/TorchScript model
            config: Agent configuration
            vocabulary: Language vocabulary
        """
        self.config = config or AgentConfig()
        self.vocabulary = vocabulary or PortableVocabulary()
        self.experience_buffer = UnifiedExperienceBuffer()
        
        # Input/output adapters
        self.gym_input = GymInputAdapter(self.config.state_dim)
        self.text_input = TextInputAdapter(self.config.state_dim, self.vocabulary.word_to_id)
        self.context_input = ContextInputAdapter(self.config.state_dim)
        
        self.gym_output = GymOutputAdapter()
        self.json_output = JSONOutputAdapter()
        self.text_output = TextOutputAdapter()
        
        # Brain (ONNX or TorchScript)
        self.brain = None
        self.brain_type = None
        if brain_path:
            self._load_brain(brain_path)
        
        # State tracking
        self.current_state: Optional[np.ndarray] = None
        self.last_action: Optional[int] = None
        self.total_steps: int = 0
        self.episode_rewards: List[float] = []
        
        # Server (lazy init)
        self._server_app = None
        self._server_thread = None
        
        logger.info(f"AgentBridge initialized (brain: {self.brain_type}, vocab: {self.vocabulary.vocab_size})")
    
    def _load_brain(self, path: Path):
        """Load neural network model."""
        path = Path(path)
        
        if path.suffix == '.onnx' and ONNX_AVAILABLE:
            try:
                self.brain = ort.InferenceSession(str(path))
                self.brain_type = 'onnx'
                print(f"  ✓ Loaded ONNX model")
            except Exception as e:
                print(f"  ✗ Failed to load ONNX model: {e}")
            
        elif path.suffix in ('.pt', '.pth', '.torchscript') and TORCH_AVAILABLE:
            try:
                self.brain = torch.jit.load(str(path))
                self.brain.eval()
                self.brain_type = 'torchscript'
                print(f"  ✓ Loaded TorchScript model")
            except Exception as e:
                print(f"  ✗ Failed to load TorchScript model: {e}")
        
        elif path.suffix in ('.pt', '.pth', '.torchscript') and not TORCH_AVAILABLE:
            print(f"  ✗ PyTorch not available - cannot load {path.suffix} model")
            print(f"    Install with: pip install torch")
            
        else:
            print(f"  ✗ Unknown model format: {path.suffix}")
    
    def _infer(self, state: np.ndarray) -> Tuple[int, List[float], float]:
        """Run inference on state, return (action, q_values, confidence)."""
        if self.brain is None:
            # Random action if no brain
            action = random.randint(0, self.config.num_actions - 1)
            return action, [0.0] * self.config.num_actions, 0.0
        
        # Ensure correct shape
        state = state.astype(np.float32)
        if len(state.shape) == 1:
            state = state.reshape(1, -1)
        
        # Epsilon-greedy exploration
        if random.random() < self.config.epsilon:
            action = random.randint(0, self.config.num_actions - 1)
            q_values = [0.0] * self.config.num_actions
            return action, q_values, 0.0
        
        # Run inference
        if self.brain_type == 'onnx':
            input_name = self.brain.get_inputs()[0].name
            outputs = self.brain.run(None, {input_name: state})
            q_values = outputs[0][0].tolist()
            
        elif self.brain_type == 'torchscript':
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state)
                outputs = self.brain(state_tensor)
                if isinstance(outputs, tuple):
                    q_values = outputs[0][0].tolist()
                else:
                    q_values = outputs[0].tolist()
        else:
            q_values = [0.0] * self.config.num_actions
        
        # Select action
        action = int(np.argmax(q_values))
        
        # Calculate confidence (softmax of Q-values)
        q_array = np.array(q_values)
        exp_q = np.exp(q_array - np.max(q_array))
        probs = exp_q / np.sum(exp_q)
        confidence = float(probs[action])
        
        return action, q_values, confidence
    
    def _generate_response(self, state: np.ndarray, action: int) -> str:
        """Generate language response (if model supports it)."""
        # For now, return action-based response
        # TODO: Use language head if available
        action_responses = {
            0: "Moving to explore the environment.",
            1: "Seeking cooperation with nearby entities.",
            2: "Competing for available resources.",
            3: "Resting to conserve energy.",
            4: "Conditions favor reproduction.",
            5: "Isolating for safety.",
        }
        return action_responses.get(action, "")
    
    # =========================================================================
    # MAIN INTERFACE - process() is the core method
    # =========================================================================
    
    def process(self,
                text: Optional[str] = None,
                obs: Optional[Any] = None,
                context: Optional[Dict[str, Any]] = None,
                learn: bool = True) -> BridgeResult:
        """
        Process any input and return unified result.
        
        This is the main entry point. Accepts:
        - text: Natural language input
        - obs: Gym observation
        - context: Structured context dict
        
        Args:
            text: Optional text input
            obs: Optional Gym observation
            context: Optional context dictionary
            learn: Whether to store experience for learning
            
        Returns:
            BridgeResult with action, response, confidence, etc.
        """
        # Convert input to state vector
        if obs is not None:
            state = self.gym_input.to_state(obs, context)
        elif text is not None:
            state = self.text_input.to_state(text, context)
        elif context is not None:
            state = self.context_input.to_state(context)
        else:
            state = np.zeros(self.config.state_dim, dtype=np.float32)
        
        # Store previous state
        prev_state = self.current_state
        self.current_state = state
        
        # Run inference
        action, q_values, confidence = self._infer(state)
        self.last_action = action
        self.total_steps += 1
        
        # Generate language response
        response = self._generate_response(state, action)
        
        # Decay epsilon
        if self.config.epsilon > self.config.epsilon_min:
            self.config.epsilon *= self.config.epsilon_decay
        
        # Create result
        result = BridgeResult(
            action=action,
            action_name=self.ACTION_NAMES[action],
            response=response,
            confidence=confidence,
            q_values=q_values,
            state_vector=state.tolist(),
            metadata={
                'total_steps': self.total_steps,
                'epsilon': self.config.epsilon,
                'input_type': 'obs' if obs is not None else ('text' if text is not None else 'context')
            }
        )
        
        return result
    
    def reward(self, reward_value: float, done: bool = False):
        """
        Provide reward for last action (for learning).
        
        Call this after process() to enable learning.
        """
        if self.current_state is None or self.last_action is None:
            return
        
        # Store experience
        self.experience_buffer.add(
            state=self.current_state,
            action=self.last_action,
            reward=reward_value,
            next_state=self.current_state,  # Updated on next process()
            done=done,
            source='external'
        )
        
        self.episode_rewards.append(reward_value)
        
        if done:
            logger.info(f"Episode done. Total reward: {sum(self.episode_rewards):.2f}")
            self.episode_rewards = []
    
    # =========================================================================
    # MODE 1: Gymnasium/Gym Environment Runner
    # =========================================================================
    
    def run_gym(self, 
                env_spec: str,
                episodes: int = 10,
                max_steps: Optional[int] = None,
                render: bool = False,
                learn: bool = True) -> Dict[str, Any]:
        """
        Run agent in a Gymnasium environment.
        
        Args:
            env_spec: Gym environment spec (e.g., 'CartPole-v1')
            episodes: Number of episodes to run
            max_steps: Max steps per episode (None = no limit)
            render: Whether to render environment
            learn: Whether to learn from experiences
            
        Returns:
            Statistics dict
        """
        # Import gym
        try:
            import gymnasium as gym
        except ImportError:
            import gym
        
        env = gym.make(env_spec)
        
        stats = {
            'episodes': episodes,
            'total_rewards': [],
            'episode_lengths': [],
            'env': env_spec
        }
        
        for ep in range(episodes):
            obs, info = env.reset() if hasattr(env, 'reset') else (env.reset(), {})
            done = False
            total_reward = 0
            steps = 0
            
            while not done:
                if render:
                    env.render()
                
                # Get action
                result = self.process(obs=obs)
                action = result.action
                
                # Ensure action is valid for this env
                if hasattr(env.action_space, 'n'):
                    action = action % env.action_space.n
                
                # Step environment
                step_result = env.step(action)
                if len(step_result) == 5:
                    next_obs, reward, terminated, truncated, info = step_result
                    done = terminated or truncated
                else:
                    next_obs, reward, done, info = step_result
                
                # Learn from experience
                if learn:
                    self.reward(reward, done)
                
                obs = next_obs
                total_reward += reward
                steps += 1
                
                if max_steps and steps >= max_steps:
                    break
            
            stats['total_rewards'].append(total_reward)
            stats['episode_lengths'].append(steps)
            logger.info(f"Episode {ep+1}/{episodes}: reward={total_reward:.2f}, steps={steps}")
        
        env.close()
        
        stats['mean_reward'] = np.mean(stats['total_rewards'])
        stats['std_reward'] = np.std(stats['total_rewards'])
        
        return stats
    
    # =========================================================================
    # MODE 2: HTTP/REST API Server
    # =========================================================================
    
    def serve(self, port: Optional[int] = None, host: str = '0.0.0.0'):
        """
        Start HTTP API server.
        
        Endpoints:
            POST /act - Get action for observation/text/context
            POST /chat - Chat with agent (text in, text out)
            POST /reward - Provide reward for learning
            GET /state - Get current agent state
            GET /config - Get agent configuration
            POST /config - Update configuration
        """
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask not available. Install with: pip install flask")
        
        port = port or self.config.default_port
        
        app = Flask(__name__)
        
        @app.route('/act', methods=['POST'])
        def act():
            data = request.json or {}
            result = self.process(
                text=data.get('text'),
                obs=data.get('obs'),
                context=data.get('context'),
                learn=data.get('learn', True)
            )
            return jsonify(result.to_dict())
        
        @app.route('/chat', methods=['POST'])
        def chat():
            data = request.json or {}
            text = data.get('text', data.get('message', ''))
            result = self.process(text=text, context=data.get('context'))
            return jsonify({
                'response': result.response,
                'action': result.action_name,
                'confidence': result.confidence
            })
        
        @app.route('/reward', methods=['POST'])
        def reward_endpoint():
            data = request.json or {}
            self.reward(
                reward_value=float(data.get('reward', 0)),
                done=data.get('done', False)
            )
            return jsonify({'status': 'ok'})
        
        @app.route('/state', methods=['GET'])
        def state():
            return jsonify({
                'current_state': self.current_state.tolist() if self.current_state is not None else None,
                'last_action': self.last_action,
                'total_steps': self.total_steps,
                'epsilon': self.config.epsilon,
                'experience_count': len(self.experience_buffer)
            })
        
        @app.route('/config', methods=['GET'])
        def get_config():
            return jsonify(self.config.to_dict())
        
        @app.route('/config', methods=['POST'])
        def set_config():
            data = request.json or {}
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            return jsonify(self.config.to_dict())
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'ok',
                'brain_type': self.brain_type,
                'vocab_size': self.vocabulary.vocab_size
            })
        
        self._server_app = app
        
        logger.info(f"Starting HTTP server on {host}:{port}")
        print(f"\n🦋 AgentBridge HTTP Server")
        print(f"   http://{host}:{port}")
        print(f"\n   Endpoints:")
        print(f"   POST /act    - Get action for input")
        print(f"   POST /chat   - Chat with agent")
        print(f"   POST /reward - Provide learning reward")
        print(f"   GET  /state  - Get agent state")
        print(f"   GET  /config - Get configuration")
        print(f"\n   Press Ctrl+C to stop\n")
        
        app.run(host=host, port=port, threaded=True)
    
    def serve_background(self, port: Optional[int] = None, host: str = '0.0.0.0'):
        """Start HTTP server in background thread."""
        self._server_thread = threading.Thread(
            target=self.serve,
            args=(port, host),
            daemon=True
        )
        self._server_thread.start()
        time.sleep(1)  # Give server time to start
        return self._server_thread
    
    # =========================================================================
    # MODE 3: Interactive CLI
    # =========================================================================
    
    def interactive(self):
        """
        Start interactive CLI mode.
        
        Commands:
            <text>      - Send text to agent
            /act <json> - Send structured action request
            /gym <env>  - Run in Gym environment
            /state      - Show current state
            /config     - Show configuration
            /quit       - Exit
        """
        print("\n🦋 AgentBridge Interactive Mode")
        print("   Type messages to chat with the agent")
        print("   Commands: /act, /gym, /state, /config, /quit")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_input:
                continue
            
            if user_input.lower() == '/quit':
                break
            
            elif user_input.lower() == '/state':
                print(f"\nState: {self.current_state}")
                print(f"Steps: {self.total_steps}, Epsilon: {self.config.epsilon:.4f}")
                print()
                continue
            
            elif user_input.lower() == '/config':
                print(f"\nConfig: {json.dumps(self.config.to_dict(), indent=2)}")
                print()
                continue
            
            elif user_input.lower().startswith('/gym '):
                env_spec = user_input[5:].strip()
                print(f"\nRunning {env_spec}...")
                stats = self.run_gym(env_spec, episodes=3)
                print(f"Mean reward: {stats['mean_reward']:.2f}")
                print()
                continue
            
            elif user_input.startswith('/act '):
                try:
                    data = json.loads(user_input[5:])
                    result = self.process(
                        text=data.get('text'),
                        obs=data.get('obs'),
                        context=data.get('context')
                    )
                except json.JSONDecodeError:
                    print("Invalid JSON")
                    continue
            else:
                # Regular text input
                result = self.process(text=user_input)
            
            # Show response
            print(f"Agent [{result.action_name}]: {result.response}")
            print(f"       (confidence: {result.confidence:.2%})")
            print()
        
        print("\nGoodbye! 🦋")
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def save(self, directory: Path):
        """Save bridge state to directory."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        # Save config
        with open(directory / 'bridge_config.json', 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        # Save vocabulary
        with open(directory / 'vocabulary.json', 'w') as f:
            json.dump(self.vocabulary.to_dict(), f, indent=2)
        
        # Save experience buffer
        self.experience_buffer.save(directory / 'experiences.pkl')
        
        # Save state
        state_data = {
            'total_steps': self.total_steps,
            'epsilon': self.config.epsilon,
            'current_state': self.current_state.tolist() if self.current_state is not None else None,
            'last_action': self.last_action
        }
        with open(directory / 'bridge_state.json', 'w') as f:
            json.dump(state_data, f, indent=2)
        
        logger.info(f"Bridge state saved to {directory}")
    
    @classmethod
    def load(cls, directory: Union[str, Path]) -> 'AgentBridge':
        """
        Load bridge from exported agent directory.
        
        This is the main entry point for loading an exported agent.
        """
        directory = Path(directory)
        
        # Find brain file
        brain_path = None
        for ext in ['.onnx', '.pt', '.pth', '.torchscript']:
            candidates = list(directory.glob(f'brain{ext}'))
            if candidates:
                brain_path = candidates[0]
                print(f"  ✓ Found brain: {brain_path.name}")
                break
        
        if brain_path is None:
            print(f"  ⚠ No brain file found in {directory}")
            print(f"    Looking for: brain.onnx, brain.pt, brain.pth, brain.torchscript")
            # List what files ARE there
            files = list(directory.glob('*'))
            print(f"    Files in directory: {[f.name for f in files[:10]]}")
        
        # Load config
        config = AgentConfig()
        config_path = directory / 'bridge_config.json'
        if not config_path.exists():
            config_path = directory / 'atomic_config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Load vocabulary
        vocab = PortableVocabulary()
        vocab_path = directory / 'vocabulary.json'
        if not vocab_path.exists():
            vocab_path = directory / 'atomic_language.json'
        if vocab_path.exists():
            vocab = PortableVocabulary.load(vocab_path)
            print(f"  ✓ Loaded vocabulary: {vocab.vocab_size} words")
        else:
            print(f"  ⚠ No vocabulary file found")
        
        # Create bridge
        bridge = cls(
            brain_path=brain_path,
            config=config,
            vocabulary=vocab
        )
        
        # Load experience buffer
        exp_path = directory / 'experiences.pkl'
        if not exp_path.exists():
            exp_path = directory / 'agent_state' / 'replay_buffer.pkl'
        if exp_path.exists():
            bridge.experience_buffer = UnifiedExperienceBuffer.load(exp_path)
        
        # Load state
        state_path = directory / 'bridge_state.json'
        if state_path.exists():
            with open(state_path, 'r') as f:
                state_data = json.load(f)
            bridge.total_steps = state_data.get('total_steps', 0)
            bridge.config.epsilon = state_data.get('epsilon', config.epsilon)
            if state_data.get('current_state'):
                bridge.current_state = np.array(state_data['current_state'])
            bridge.last_action = state_data.get('last_action')
        
        logger.info(f"Loaded AgentBridge from {directory}")
        return bridge


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point for AgentBridge."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AgentBridge - Universal interface for Butterfly agents'
    )
    parser.add_argument(
        'agent_dir',
        nargs='?',
        default='.',
        help='Path to exported agent directory (default: current directory)'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['interactive', 'serve', 'gym'],
        default='interactive',
        help='Operating mode (default: interactive)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='HTTP server port (default: 8080)'
    )
    parser.add_argument(
        '--gym-env', '-e',
        default='CartPole-v1',
        help='Gym environment for gym mode (default: CartPole-v1)'
    )
    parser.add_argument(
        '--episodes', '-n',
        type=int,
        default=10,
        help='Number of episodes for gym mode (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Load agent
    print(f"Loading agent from: {args.agent_dir}")
    bridge = AgentBridge.load(args.agent_dir)
    
    # Run in selected mode
    if args.mode == 'interactive':
        bridge.interactive()
    elif args.mode == 'serve':
        bridge.serve(port=args.port)
    elif args.mode == 'gym':
        stats = bridge.run_gym(args.gym_env, episodes=args.episodes)
        print(f"\nResults:")
        print(f"  Mean reward: {stats['mean_reward']:.2f} ± {stats['std_reward']:.2f}")
        print(f"  Episodes: {stats['episodes']}")


if __name__ == '__main__':
    main()
