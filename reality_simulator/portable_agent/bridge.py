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
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from collections import deque, OrderedDict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
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

from enum import Enum


# =============================================================================
# ENSEMBLE VOTING STRATEGIES
# =============================================================================

class EnsembleVotingStrategy(Enum):
    """
    Voting strategies for ensemble decision making.
    
    Modeled after ButterflyChatRouter's aggregation system.
    """
    SINGLE = "single"                     # Use only first organism (legacy behavior)
    MAJORITY = "majority"                 # Democratic: each organism votes, most common wins
    FITNESS_WEIGHTED = "fitness_weighted" # Weight votes by organism fitness
    SOFTMAX_ENSEMBLE = "softmax_ensemble" # Softmax aggregate across all Q-values
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # Weight by Q-value confidence
    FITTEST_TOP_K = "fittest_top_k"       # Only top K fittest organisms vote
    ADAPTIVE = "adaptive"                 # Automatically select best strategy per situation


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class OrganismVote:
    """Individual organism's vote in the ensemble."""
    organism_idx: int
    organism_id: str
    action: int
    q_values: List[float]
    confidence: float
    fitness: float
    weight: float  # Combined weight for aggregation


@dataclass
class EnsembleResult:
    """Detailed result from ensemble voting."""
    winning_action: int
    action_name: str
    votes: List[OrganismVote]
    vote_counts: Dict[int, int]          # Action -> count
    weighted_votes: Dict[int, float]     # Action -> weighted sum
    agreement_ratio: float               # % of organisms that agreed
    total_weight: float
    strategy_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'winning_action': self.winning_action,
            'action_name': self.action_name,
            'vote_counts': self.vote_counts,
            'weighted_votes': self.weighted_votes,
            'agreement_ratio': self.agreement_ratio,
            'total_weight': self.total_weight,
            'strategy_used': self.strategy_used,
            'num_voters': len(self.votes)
        }


@dataclass
class BridgeResult:
    """Unified result from any bridge operation."""
    action: int                          # Discrete action (0-5)
    action_name: str                     # Human-readable action name
    response: str                        # Language response (if applicable)
    confidence: float                    # Decision confidence (0-1)
    q_values: List[float]               # Raw Q-values for all actions
    state_vector: List[float]           # The 24D state used for decision
    metadata: Dict[str, Any] = field(default_factory=dict)
    ensemble_result: Optional['EnsembleResult'] = None  # Detailed voting info if ensemble
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'action': self.action,
            'action_name': self.action_name,
            'response': self.response,
            'confidence': self.confidence,
            'q_values': self.q_values,
            'state_vector': self.state_vector,
            'metadata': self.metadata
        }
        if self.ensemble_result:
            result['ensemble'] = self.ensemble_result.to_dict()
        return result


@dataclass  
class AgentConfig:
    """Configuration for the bridge."""
    # Action space
    action_names: List[str] = field(default_factory=lambda: [
        'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'
    ])
    num_actions: int = 6
    
    # State space (24D to match current neural system)
    state_dim: int = 24
    
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
    
    # Ensemble configuration
    is_ensemble: bool = False
    member_count: int = 1
    voting_strategy: str = "fitness_weighted"  # Default: weight by organism fitness
    top_k_voters: int = 5                       # For fittest_top_k strategy
    member_fitness: List[float] = field(default_factory=list)  # Fitness per organism
    member_ids: List[str] = field(default_factory=list)        # IDs per organism
    
    # Advanced features
    adaptive_strategy: bool = True              # Auto-select best strategy per situation
    temperature_scaling: bool = True            # Dynamic temperature based on confidence
    min_temperature: float = 0.3                # Temperature floor (high confidence)
    max_temperature: float = 2.0                # Temperature ceiling (low confidence)
    cache_enabled: bool = True                  # Enable response caching
    cache_size: int = 256                       # LRU cache size
    cache_ttl: float = 60.0                     # Cache entry TTL in seconds
    parallel_inference: bool = True             # Enable parallel organism execution
    max_workers: int = 4                        # Thread pool size for parallel inference
    
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
            'temperature': self.temperature,
            'is_ensemble': self.is_ensemble,
            'member_count': self.member_count,
            'voting_strategy': self.voting_strategy,
            'top_k_voters': self.top_k_voters
        }


# =============================================================================
# INPUT ADAPTERS - Convert various inputs to unified 24D state
# =============================================================================

class InputAdapter:
    """Base class for input adapters."""
    
    def to_state(self, input_data: Any, context: Optional[Dict] = None) -> np.ndarray:
        """Convert input to 24D state vector."""
        raise NotImplementedError


class GymInputAdapter(InputAdapter):
    """Adapter for Gymnasium/Gym observations."""
    
    def __init__(self, state_dim: int = 24):
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
        
        # Extended state indicators (dim 18-23)
        'alliance': (18, 0.5), 'battle': (19, 0.5), 'victory': (19, 0.7), 'defeat': (19, -0.5),
        'vocabulary': (20, 0.5), 'communicate': (21, 0.5), 'language': (21, 0.4),
        'vp': (22, 0.5), 'pressure': (22, 0.4), 'violation': (22, 0.6),
        'coherence': (23, 0.5), 'stability': (23, 0.4),
    }
    
    def __init__(self, state_dim: int = 24, vocabulary: Optional[Dict] = None):
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
    
    def __init__(self, state_dim: int = 24):
        self.state_dim = state_dim
        
    def to_state(self, context: Dict[str, Any], _: Optional[Dict] = None) -> np.ndarray:
        """Convert context dict directly to state vector."""
        state = np.zeros(self.state_dim, dtype=np.float32)
        
        # Direct mapping for known keys (24 dimensions)
        mapping = [
            'energy', 'hunger', 'health',                     # 0-2: vitality
            'danger', 'enemy_distance', 'attack_imminent',    # 3-5: threat
            'friend_nearby', 'cooperation', 'competition',    # 6-8: social
            'food_available', 'abundance', 'opportunity',     # 9-11: resources
            'crowding', 'temperature', 'visibility',          # 12-14: environment
            'confidence', 'mood', 'stress',                   # 15-17: emotional
            'alliance_strength', 'battle_performance',        # 18-19: alliance/combat
            'vocabulary_size', 'communication_activity',      # 20-21: language
            'violation_pressure', 'coherence'                 # 22-23: VP/stability
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
        """Load vocabulary from atomic_language.json or similar file."""
        if not path.exists():
            return cls._create_default_vocabulary()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vocab = cls()
        
        # Handle different atomic_language.json formats
        if 'word_to_id' in data:
            vocab.word_to_id = data['word_to_id']
        elif 'concepts' in data and data['concepts']:
            # Extract words from atomic concepts
            for concept_id, concept_data in data['concepts'].items():
                vocab.add_word(concept_id)
        elif 'vocabulary' in data and data['vocabulary']:
            for word in data['vocabulary']:
                vocab.add_word(word)
        elif 'semantic_associations' in data and data['semantic_associations']:
            # Extract words from semantic associations
            for word in data['semantic_associations'].keys():
                vocab.add_word(word)
        
        # If vocabulary is still basically empty, use default
        if vocab.vocab_size <= 5:
            print(f"  [!] Vocabulary file has no words, using built-in vocabulary")
            return cls._create_default_vocabulary()
        
        vocab.id_to_word = {int(v): k for k, v in vocab.word_to_id.items()}
        return vocab
    
    @classmethod
    def _create_default_vocabulary(cls) -> 'PortableVocabulary':
        """Create a default vocabulary with common organism-relevant words."""
        vocab = cls()
        
        # Basic action/state words
        default_words = [
            # Actions
            'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate',
            'explore', 'search', 'attack', 'defend', 'flee', 'hide',
            # States
            'energy', 'health', 'danger', 'safe', 'threat', 'opportunity',
            'hungry', 'tired', 'strong', 'weak', 'alive', 'dying',
            # Environment
            'food', 'water', 'shelter', 'resource', 'territory', 'home',
            'crowded', 'empty', 'dark', 'light', 'hot', 'cold',
            # Social
            'friend', 'enemy', 'ally', 'rival', 'group', 'alone',
            'help', 'share', 'fight', 'trust', 'fear', 'hope',
            # Descriptors
            'good', 'bad', 'better', 'worse', 'best', 'worst',
            'high', 'low', 'near', 'far', 'fast', 'slow',
            # Connectors
            'and', 'but', 'or', 'the', 'a', 'to', 'is', 'are',
            'i', 'we', 'they', 'it', 'this', 'that', 'here', 'there',
            # Organism-specific
            'survive', 'thrive', 'adapt', 'evolve', 'grow', 'learn',
            'sense', 'feel', 'know', 'want', 'need', 'must',
        ]
        
        for word in default_words:
            vocab.add_word(word)
        
        print(f"  [OK] Created default vocabulary: {vocab.vocab_size} words")
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
        self.has_language_head = False  # Track if model has language generation capability
        if brain_path:
            self._load_brain(brain_path)
        
        # State tracking
        self.current_state: Optional[np.ndarray] = None
        self.last_action: Optional[int] = None
        self.total_steps: int = 0
        self.episode_rewards: List[float] = []
        
        # Online learning (disabled by default)
        self._online_learning_enabled = False
        self._optimizer = None
        self._train_steps = 0
        self._total_loss = 0.0
        self._train_batch_size = 32
        self._gamma = 0.99
        
        # Server (lazy init)
        self._server_app = None
        self._server_thread = None
        
        # Advanced features
        # Response cache: OrderedDict for LRU behavior with TTL
        self._response_cache: OrderedDict = OrderedDict()
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_lock = threading.Lock()
        
        # Temperature tracking for adaptive scaling
        self._recent_confidences: deque = deque(maxlen=50)
        self._current_temperature: float = self.config.temperature
        
        # Thread pool for parallel inference
        self._executor: Optional[ThreadPoolExecutor] = None
        if self.config.parallel_inference and self.config.is_ensemble:
            self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Strategy selection history for adaptive mode
        self._strategy_performance: Dict[str, List[float]] = {
            'majority': [],
            'fitness_weighted': [],
            'softmax_ensemble': [],
            'confidence_weighted': [],
            'fittest_top_k': []
        }
        
        logger.info(f"AgentBridge initialized (brain: {self.brain_type}, vocab: {self.vocabulary.vocab_size}, language_head: {self.has_language_head})")
        if self.config.is_ensemble:
            features = []
            if self.config.adaptive_strategy: features.append('adaptive')
            if self.config.temperature_scaling: features.append('temp_scale')
            if self.config.cache_enabled: features.append('cache')
            if self.config.parallel_inference: features.append('parallel')
            logger.info(f"  Ensemble features: {', '.join(features) if features else 'none'}")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_executor') and self._executor is not None:
            self._executor.shutdown(wait=False)
    
    def shutdown(self):
        """Explicitly shutdown the bridge and release resources."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None
        self.clear_cache()
        logger.info("AgentBridge shutdown complete")
    
    def _load_brain(self, path: Path):
        """Load neural network model and detect capabilities."""
        path = Path(path)
        
        if path.suffix == '.onnx' and ONNX_AVAILABLE:
            try:
                self.brain = ort.InferenceSession(str(path))
                self.brain_type = 'onnx'
                # Check for language head in ONNX outputs
                output_names = [o.name for o in self.brain.get_outputs()]
                self.has_language_head = len(output_names) > 1
                print(f"  [OK] Loaded ONNX model ({len(output_names)} outputs)")
            except Exception as e:
                print(f"  [X] Failed to load ONNX model: {e}")
            
        elif path.suffix in ('.pt', '.pth', '.torchscript') and TORCH_AVAILABLE:
            try:
                self.brain = torch.jit.load(str(path))
                self.brain.eval()
                self.brain_type = 'torchscript'
                
                # Test inference to detect language head
                try:
                    dummy = torch.zeros(1, self.config.state_dim)
                    with torch.no_grad():
                        outputs = self.brain(dummy)
                    if isinstance(outputs, tuple) and len(outputs) >= 2:
                        self.has_language_head = True
                        print(f"  [OK] Loaded TorchScript model (with language head)")
                    else:
                        print(f"  [OK] Loaded TorchScript model")
                except Exception:
                    print(f"  [OK] Loaded TorchScript model")
                    
            except Exception as e:
                print(f"  [X] Failed to load TorchScript model: {e}")
        
        elif path.suffix in ('.pt', '.pth', '.torchscript') and not TORCH_AVAILABLE:
            print(f"  [X] PyTorch not available - cannot load {path.suffix} model")
            print(f"    Install with: pip install torch")
            
        else:
            print(f"  [X] Unknown model format: {path.suffix}")
    
    def _infer(self, state: np.ndarray) -> Tuple[int, List[float], float, Optional[EnsembleResult]]:
        """
        Run inference on state, return (action, q_values, confidence, ensemble_result).
        
        For ensemble models, uses voting strategies to aggregate decisions from all organisms.
        For single models, uses standard inference.
        
        Features:
        - Response caching for repeated states
        - Adaptive strategy selection
        - Temperature scaling based on confidence
        """
        if self.brain is None:
            # Random action if no brain
            action = random.randint(0, self.config.num_actions - 1)
            return action, [0.0] * self.config.num_actions, 0.0, None
        
        # Ensure correct shape
        state = state.astype(np.float32)
        if len(state.shape) == 1:
            state = state.reshape(1, -1)
        
        # Check cache first
        cache_key = self._cache_key(state)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        
        # Epsilon-greedy exploration (skip caching for exploration)
        if random.random() < self.config.epsilon:
            action = random.randint(0, self.config.num_actions - 1)
            q_values = [0.0] * self.config.num_actions
            return action, q_values, 0.0, None
        
        # Check if this is an ensemble model that needs voting
        if self.config.is_ensemble and self.config.member_count > 1:
            ensemble_result = self._infer_ensemble(state)
            # Cache ensemble result
            self._cache_set(cache_key, ensemble_result)
            return ensemble_result
        
        # Standard single-organism inference
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
        
        # Cache result
        result = (action, q_values, confidence, None)
        self._cache_set(cache_key, result)
        
        return result
    
    def _infer_ensemble(self, state: np.ndarray) -> Tuple[int, List[float], float, EnsembleResult]:
        """
        Run ensemble inference with voting aggregation.
        
        Extracts outputs from all organisms and uses the configured voting strategy.
        Mirrors ButterflyChatRouter's _aggregate_responses logic.
        """
        num_organisms = self.config.member_count
        num_actions = self.config.num_actions
        
        # Get all organism outputs
        all_q_values = []
        all_language_logits = []
        
        if self.brain_type == 'onnx':
            input_name = self.brain.get_inputs()[0].name
            outputs = self.brain.run(None, {input_name: state})
            # Ensemble ONNX outputs are flat: [q1, q2, ..., qN, lang1, lang2, ..., langN]
            flat_outputs = outputs[0][0]
            
            # Split into per-organism Q-values
            for i in range(num_organisms):
                start_idx = i * num_actions
                end_idx = start_idx + num_actions
                if end_idx <= len(flat_outputs):
                    all_q_values.append(flat_outputs[start_idx:end_idx].tolist())
            
            # Language outputs start after all Q-values
            lang_start = num_organisms * num_actions
            if len(flat_outputs) > lang_start:
                for i in range(num_organisms):
                    # Assume language logits follow Q-values
                    lang_idx = lang_start + i
                    if lang_idx < len(flat_outputs):
                        all_language_logits.append(flat_outputs[lang_idx])
                        
        elif self.brain_type == 'torchscript':
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state)
                outputs = self.brain(state_tensor)
                
                if isinstance(outputs, tuple):
                    # outputs = (q_values_flat, language_logits_flat)
                    # q_values_flat shape: [1, num_organisms * num_actions]
                    # language_logits_flat shape: [1, num_organisms * vocab_size] or [1, num_organisms]
                    q_flat = outputs[0][0].numpy()
                    
                    for i in range(num_organisms):
                        start_idx = i * num_actions
                        end_idx = start_idx + num_actions
                        if end_idx <= len(q_flat):
                            all_q_values.append(q_flat[start_idx:end_idx].tolist())
                    
                    if len(outputs) > 1 and outputs[1] is not None:
                        lang_flat = outputs[1][0].numpy()
                        # Store for potential language aggregation
                        for i in range(min(num_organisms, len(lang_flat))):
                            all_language_logits.append(lang_flat[i])
                else:
                    # Single tensor output - treat as flat Q-values
                    q_flat = outputs[0].numpy()
                    for i in range(num_organisms):
                        start_idx = i * num_actions
                        end_idx = start_idx + num_actions
                        if end_idx <= len(q_flat):
                            all_q_values.append(q_flat[start_idx:end_idx].tolist())
        
        # Fallback if we couldn't extract organism outputs
        if not all_q_values:
            # Use single inference as fallback
            action = random.randint(0, num_actions - 1)
            return action, [0.0] * num_actions, 0.0, None
        
        # Build votes from each organism
        votes: List[OrganismVote] = []
        for i, q_values in enumerate(all_q_values):
            # Get fitness for this organism (default 1.0 if not available)
            fitness = self.config.member_fitness[i] if i < len(self.config.member_fitness) else 1.0
            org_id = self.config.member_ids[i] if i < len(self.config.member_ids) else f"organism_{i}"
            
            # Calculate organism confidence from its Q-values
            q_array = np.array(q_values)
            exp_q = np.exp(q_array - np.max(q_array))
            probs = exp_q / np.sum(exp_q)
            org_action = int(np.argmax(q_values))
            org_confidence = float(probs[org_action])
            
            # Weight = fitness * confidence (matching butterfly_chat)
            weight = max(fitness, 0.0) * max(org_confidence, 0.0)
            
            votes.append(OrganismVote(
                organism_idx=i,
                organism_id=org_id,
                action=org_action,
                q_values=q_values,
                confidence=org_confidence,
                fitness=fitness,
                weight=weight
            ))
        
        # Apply voting strategy (with adaptive selection if enabled)
        strategy = self.config.voting_strategy.lower()
        
        # Adaptive strategy selection
        if strategy == "adaptive" or (self.config.adaptive_strategy and strategy == "fitness_weighted"):
            strategy = self._adaptive_select_strategy(votes)
        
        if strategy == "single":
            result = self._vote_single(votes)
        elif strategy == "majority":
            result = self._vote_majority(votes)
        elif strategy == "fitness_weighted":
            result = self._vote_fitness_weighted(votes)
        elif strategy == "softmax_ensemble":
            result = self._vote_softmax_ensemble(votes)
        elif strategy == "confidence_weighted":
            result = self._vote_confidence_weighted(votes)
        elif strategy == "fittest_top_k":
            result = self._vote_fittest_top_k(votes, self.config.top_k_voters)
        else:
            # Default to fitness_weighted
            result = self._vote_fitness_weighted(votes)
        
        # Aggregate Q-values for reporting (weighted average)
        total_weight = sum(v.weight for v in votes) or 1.0
        aggregated_q_values = [0.0] * num_actions
        for vote in votes:
            for j, qv in enumerate(vote.q_values):
                aggregated_q_values[j] += qv * vote.weight / total_weight
        
        # Update adaptive temperature based on ensemble confidence
        self._compute_adaptive_temperature(votes, result)
        
        # Cache result (use state from closure)
        final_result = (result.winning_action, aggregated_q_values, result.agreement_ratio, result)
        # Note: We need to pass cache_key from _infer - for now ensemble caching happens at _infer level
        
        return final_result
    
    def _vote_single(self, votes: List[OrganismVote]) -> EnsembleResult:
        """Use only the first organism (legacy behavior)."""
        if not votes:
            return self._empty_ensemble_result("single")
        
        first = votes[0]
        return EnsembleResult(
            winning_action=first.action,
            action_name=self.ACTION_NAMES[first.action],
            votes=votes,
            vote_counts={first.action: 1},
            weighted_votes={first.action: first.weight},
            agreement_ratio=first.confidence,
            total_weight=first.weight,
            strategy_used="single"
        )
    
    def _vote_majority(self, votes: List[OrganismVote]) -> EnsembleResult:
        """Democratic voting - each organism gets one vote, most common wins."""
        if not votes:
            return self._empty_ensemble_result("majority")
        
        # Count votes per action
        vote_counts: Dict[int, int] = {}
        for vote in votes:
            vote_counts[vote.action] = vote_counts.get(vote.action, 0) + 1
        
        # Find winner
        winning_action = max(vote_counts.keys(), key=lambda a: vote_counts[a])
        winner_count = vote_counts[winning_action]
        agreement_ratio = winner_count / len(votes)
        
        return EnsembleResult(
            winning_action=winning_action,
            action_name=self.ACTION_NAMES[winning_action],
            votes=votes,
            vote_counts=vote_counts,
            weighted_votes={a: float(c) for a, c in vote_counts.items()},
            agreement_ratio=agreement_ratio,
            total_weight=float(len(votes)),
            strategy_used="majority"
        )
    
    def _vote_fitness_weighted(self, votes: List[OrganismVote]) -> EnsembleResult:
        """
        Weight votes by organism fitness (matching butterfly_chat's aggregation).
        
        weight = fitness * confidence
        """
        if not votes:
            return self._empty_ensemble_result("fitness_weighted")
        
        # Accumulate weighted votes per action
        vote_counts: Dict[int, int] = {}
        weighted_votes: Dict[int, float] = {}
        total_weight = 0.0
        
        for vote in votes:
            vote_counts[vote.action] = vote_counts.get(vote.action, 0) + 1
            weighted_votes[vote.action] = weighted_votes.get(vote.action, 0.0) + vote.weight
            total_weight += vote.weight
        
        # Find winner by weighted votes
        if total_weight == 0:
            # Fallback to majority if all weights are zero
            winning_action = max(vote_counts.keys(), key=lambda a: vote_counts[a])
        else:
            winning_action = max(weighted_votes.keys(), key=lambda a: weighted_votes[a])
        
        # Agreement = proportion of weight that agreed
        winner_weight = weighted_votes.get(winning_action, 0.0)
        agreement_ratio = winner_weight / total_weight if total_weight > 0 else 0.0
        
        return EnsembleResult(
            winning_action=winning_action,
            action_name=self.ACTION_NAMES[winning_action],
            votes=votes,
            vote_counts=vote_counts,
            weighted_votes=weighted_votes,
            agreement_ratio=agreement_ratio,
            total_weight=total_weight,
            strategy_used="fitness_weighted"
        )
    
    def _vote_confidence_weighted(self, votes: List[OrganismVote]) -> EnsembleResult:
        """Weight votes by Q-value confidence only (ignores fitness)."""
        if not votes:
            return self._empty_ensemble_result("confidence_weighted")
        
        vote_counts: Dict[int, int] = {}
        weighted_votes: Dict[int, float] = {}
        total_weight = 0.0
        
        for vote in votes:
            vote_counts[vote.action] = vote_counts.get(vote.action, 0) + 1
            weighted_votes[vote.action] = weighted_votes.get(vote.action, 0.0) + vote.confidence
            total_weight += vote.confidence
        
        if total_weight == 0:
            winning_action = max(vote_counts.keys(), key=lambda a: vote_counts[a])
        else:
            winning_action = max(weighted_votes.keys(), key=lambda a: weighted_votes[a])
        
        winner_weight = weighted_votes.get(winning_action, 0.0)
        agreement_ratio = winner_weight / total_weight if total_weight > 0 else 0.0
        
        return EnsembleResult(
            winning_action=winning_action,
            action_name=self.ACTION_NAMES[winning_action],
            votes=votes,
            vote_counts=vote_counts,
            weighted_votes=weighted_votes,
            agreement_ratio=agreement_ratio,
            total_weight=total_weight,
            strategy_used="confidence_weighted"
        )
    
    def _vote_softmax_ensemble(self, votes: List[OrganismVote]) -> EnsembleResult:
        """
        Aggregate all Q-values via weighted softmax.
        
        This treats the ensemble as a single unified network by:
        1. Computing weighted average of all organism Q-values
        2. Applying softmax to get final action probabilities
        """
        if not votes:
            return self._empty_ensemble_result("softmax_ensemble")
        
        num_actions = self.config.num_actions
        
        # Compute fitness-weighted average Q-values
        total_fitness = sum(v.fitness for v in votes) or 1.0
        aggregated_q = np.zeros(num_actions)
        
        for vote in votes:
            weight = vote.fitness / total_fitness
            aggregated_q += np.array(vote.q_values) * weight
        
        # Softmax to get probabilities
        exp_q = np.exp(aggregated_q - np.max(aggregated_q))
        probs = exp_q / np.sum(exp_q)
        
        # Select action with highest probability
        winning_action = int(np.argmax(probs))
        confidence = float(probs[winning_action])
        
        # Count how many organisms would have chosen this action
        vote_counts: Dict[int, int] = {}
        for vote in votes:
            vote_counts[vote.action] = vote_counts.get(vote.action, 0) + 1
        
        agreement_count = vote_counts.get(winning_action, 0)
        agreement_ratio = agreement_count / len(votes)
        
        return EnsembleResult(
            winning_action=winning_action,
            action_name=self.ACTION_NAMES[winning_action],
            votes=votes,
            vote_counts=vote_counts,
            weighted_votes={winning_action: confidence},
            agreement_ratio=agreement_ratio,
            total_weight=total_fitness,
            strategy_used="softmax_ensemble"
        )
    
    def _vote_fittest_top_k(self, votes: List[OrganismVote], k: int = 5) -> EnsembleResult:
        """Only top K fittest organisms vote (elitist strategy)."""
        if not votes:
            return self._empty_ensemble_result("fittest_top_k")
        
        # Sort by fitness descending
        sorted_votes = sorted(votes, key=lambda v: v.fitness, reverse=True)
        top_k_votes = sorted_votes[:k]
        
        # Use fitness-weighted voting among top K
        vote_counts: Dict[int, int] = {}
        weighted_votes: Dict[int, float] = {}
        total_weight = 0.0
        
        for vote in top_k_votes:
            vote_counts[vote.action] = vote_counts.get(vote.action, 0) + 1
            weighted_votes[vote.action] = weighted_votes.get(vote.action, 0.0) + vote.weight
            total_weight += vote.weight
        
        if total_weight == 0:
            winning_action = max(vote_counts.keys(), key=lambda a: vote_counts[a])
        else:
            winning_action = max(weighted_votes.keys(), key=lambda a: weighted_votes[a])
        
        winner_weight = weighted_votes.get(winning_action, 0.0)
        agreement_ratio = winner_weight / total_weight if total_weight > 0 else 0.0
        
        return EnsembleResult(
            winning_action=winning_action,
            action_name=self.ACTION_NAMES[winning_action],
            votes=top_k_votes,  # Only include the votes that counted
            vote_counts=vote_counts,
            weighted_votes=weighted_votes,
            agreement_ratio=agreement_ratio,
            total_weight=total_weight,
            strategy_used=f"fittest_top_{k}"
        )
    
    def _empty_ensemble_result(self, strategy: str) -> EnsembleResult:
        """Return empty result when no votes available."""
        return EnsembleResult(
            winning_action=0,
            action_name=self.ACTION_NAMES[0],
            votes=[],
            vote_counts={},
            weighted_votes={},
            agreement_ratio=0.0,
            total_weight=0.0,
            strategy_used=strategy
        )
    
    # =========================================================================
    # ADVANCED FEATURES: Adaptive Strategy, Temperature Scaling, Caching
    # =========================================================================
    
    def _adaptive_select_strategy(self, votes: List[OrganismVote]) -> str:
        """
        Intelligently select the best voting strategy based on ensemble state.
        
        Analyzes:
        - Disagreement level (high disagreement → softmax_ensemble)
        - Fitness distribution (skewed → fittest_top_k)  
        - Confidence spread (high variance → confidence_weighted)
        - Recent strategy performance
        
        Returns optimal strategy name.
        """
        if not votes or len(votes) < 2:
            return "single"
        
        # Analyze vote distribution
        action_votes: Dict[int, int] = {}
        for vote in votes:
            action_votes[vote.action] = action_votes.get(vote.action, 0) + 1
        
        # Calculate disagreement (entropy-like measure)
        vote_counts = list(action_votes.values())
        total_votes = len(votes)
        disagreement = 1.0 - (max(vote_counts) / total_votes)  # 0 = unanimous, 1 = split
        
        # Analyze fitness distribution
        fitnesses = [v.fitness for v in votes]
        fitness_mean = np.mean(fitnesses)
        fitness_std = np.std(fitnesses)
        fitness_skew = (max(fitnesses) - fitness_mean) / (fitness_std + 0.001)  # How skewed toward top
        
        # Analyze confidence distribution
        confidences = [v.confidence for v in votes]
        conf_std = np.std(confidences)
        conf_mean = np.mean(confidences)
        
        # Decision logic
        if disagreement < 0.2:
            # Strong agreement - majority is fine (fast)
            return "majority"
        elif fitness_skew > 2.0 and fitness_std > 0.1:
            # Very skewed fitness - trust the elite
            return "fittest_top_k"
        elif disagreement > 0.6:
            # High disagreement - blend via softmax
            return "softmax_ensemble"
        elif conf_std > 0.2 and conf_mean > 0.5:
            # High confidence variance with decent overall confidence
            return "confidence_weighted"
        else:
            # Default: trust fitness weighting
            return "fitness_weighted"
    
    def _compute_adaptive_temperature(self, votes: List[OrganismVote], 
                                       ensemble_result: Optional[EnsembleResult] = None) -> float:
        """
        Dynamically adjust temperature based on confidence and agreement.
        
        - High confidence/agreement → lower temperature (more deterministic)
        - Low confidence/disagreement → higher temperature (more exploration)
        
        Returns scaled temperature value.
        """
        if not self.config.temperature_scaling:
            return self.config.temperature
        
        base_temp = self.config.temperature
        min_temp = self.config.min_temperature
        max_temp = self.config.max_temperature
        
        # Calculate confidence metrics
        if ensemble_result:
            agreement = ensemble_result.agreement_ratio
        else:
            agreement = 0.5
        
        if votes:
            avg_confidence = np.mean([v.confidence for v in votes])
            max_confidence = max(v.confidence for v in votes)
        else:
            avg_confidence = 0.5
            max_confidence = 0.5
        
        # Track recent confidences for smoothing
        self._recent_confidences.append(avg_confidence)
        smoothed_conf = np.mean(list(self._recent_confidences))
        
        # Compute temperature multiplier
        # High confidence + high agreement = low temperature
        confidence_factor = 1.0 - (smoothed_conf * 0.5 + agreement * 0.5)
        
        # Map to temperature range
        temp_range = max_temp - min_temp
        scaled_temp = min_temp + (confidence_factor * temp_range)
        
        # Smooth transition
        self._current_temperature = 0.8 * self._current_temperature + 0.2 * scaled_temp
        
        return np.clip(self._current_temperature, min_temp, max_temp)
    
    def _cache_key(self, state: np.ndarray) -> str:
        """Generate cache key from state vector."""
        # Round state to reduce cache misses from minor variations
        rounded = np.round(state, decimals=3)
        return hashlib.md5(rounded.tobytes()).hexdigest()
    
    def _cache_get(self, key: str) -> Optional[Tuple[int, List[float], float, Optional[EnsembleResult]]]:
        """Get cached result if valid."""
        if not self.config.cache_enabled:
            return None
        
        with self._cache_lock:
            if key not in self._response_cache:
                return None
            
            # Check TTL
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp > self.config.cache_ttl:
                # Expired - remove
                del self._response_cache[key]
                del self._cache_timestamps[key]
                return None
            
            # Move to end (LRU)
            self._response_cache.move_to_end(key)
            return self._response_cache[key]
    
    def _cache_set(self, key: str, value: Tuple[int, List[float], float, Optional[EnsembleResult]]):
        """Store result in cache."""
        if not self.config.cache_enabled:
            return
        
        with self._cache_lock:
            # Evict oldest if at capacity
            while len(self._response_cache) >= self.config.cache_size:
                oldest_key = next(iter(self._response_cache))
                del self._response_cache[oldest_key]
                del self._cache_timestamps[oldest_key]
            
            self._response_cache[key] = value
            self._cache_timestamps[key] = time.time()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                'enabled': self.config.cache_enabled,
                'size': len(self._response_cache),
                'max_size': self.config.cache_size,
                'ttl': self.config.cache_ttl,
                'hit_rate': 'N/A'  # Would need hit/miss tracking
            }
    
    def clear_cache(self):
        """Clear the response cache."""
        with self._cache_lock:
            self._response_cache.clear()
            self._cache_timestamps.clear()
        logger.info("Response cache cleared")
    
    def get_current_temperature(self) -> float:
        """Get the current adaptive temperature value."""
        return self._current_temperature
    
    def _generate_response(self, state: np.ndarray, action: int) -> str:
        """Generate language response using the language head if available."""
        # Try to use the language head for real generation
        if self.has_language_head and self.vocabulary.vocab_size > 10 and self.brain is not None:
            try:
                response = self._generate_from_language_head(state)
                if response and len(response) > 2:
                    return response
            except Exception as e:
                logger.debug(f"Language generation failed: {e}")
        
        # Fallback to enhanced action-based responses
        action_responses = {
            0: self._get_contextual_response("move", state),
            1: self._get_contextual_response("cooperate", state),
            2: self._get_contextual_response("compete", state),
            3: self._get_contextual_response("rest", state),
            4: self._get_contextual_response("reproduce", state),
            5: self._get_contextual_response("isolate", state),
        }
        return action_responses.get(action, "")
    
    def _generate_from_language_head(self, state: np.ndarray, max_tokens: int = 16, temperature: float = 1.0) -> str:
        """
        Generate text using the neural network's language head.
        
        Includes:
        - Repetition penalty to prevent "was was was" patterns
        - Top-k sampling for quality output
        - Vocabulary masking for valid tokens only
        """
        if not TORCH_AVAILABLE or self.brain_type != 'torchscript':
            return ""
        
        state = state.astype(np.float32)
        if len(state.shape) == 1:
            state = state.reshape(1, -1)
        
        generated_tokens = []
        recent_tokens = []  # Track recent tokens for repetition penalty
        
        # Generation parameters
        top_k = 40  # Only sample from top 40 tokens
        repetition_penalty = 2.0  # Penalty for recent tokens
        strong_repetition_penalty = 3.0  # Stronger penalty for very recent
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state)
            
            # Get model outputs - language logits should be second output if available
            outputs = self.brain(state_tensor)
            
            if isinstance(outputs, tuple) and len(outputs) >= 2:
                # outputs[0] = action probs, outputs[1] = language logits
                language_logits = outputs[1]
                
                if language_logits is not None and language_logits.numel() > 0:
                    # Get base logits
                    base_logits = language_logits[0] if len(language_logits.shape) > 1 else language_logits
                    
                    for _ in range(max_tokens):
                        # Start with fresh copy of base logits
                        logits = base_logits.clone()
                        
                        # Apply temperature
                        logits = logits / temperature
                        
                        # ═══════════════════════════════════════════════════
                        # REPETITION PENALTY - Prevent "was was was" patterns
                        # ═══════════════════════════════════════════════════
                        if recent_tokens:
                            for i, prev_token in enumerate(recent_tokens):
                                recency = len(recent_tokens) - i
                                if recency <= 2:
                                    # Very recent: strong penalty (SUBTRACT, not divide)
                                    logits[prev_token] = logits[prev_token] - strong_repetition_penalty
                                else:
                                    # Less recent: moderate penalty
                                    logits[prev_token] = logits[prev_token] - repetition_penalty
                        
                        # ═══════════════════════════════════════════════════
                        # VOCABULARY MASKING - Only valid tokens
                        # ═══════════════════════════════════════════════════
                        vocab_size = self.vocabulary.vocab_size
                        if vocab_size < len(logits):
                            logits[vocab_size:] = float('-inf')
                        
                        # Mask special tokens (0-4)
                        logits[:5] = float('-inf')
                        
                        # ═══════════════════════════════════════════════════
                        # TOP-K SAMPLING - Quality over randomness
                        # ═══════════════════════════════════════════════════
                        if top_k > 0 and top_k < len(logits):
                            top_k_values, top_k_indices = torch.topk(logits, top_k)
                            
                            # Create mask and apply
                            mask = torch.full_like(logits, float('-inf'))
                            mask.scatter_(0, top_k_indices, top_k_values)
                            logits = mask
                        
                        # Sample from distribution
                        probs = torch.softmax(logits, dim=-1)
                        token_id = torch.multinomial(probs, 1).item()
                        
                        # Stop at END token
                        if token_id == self.vocabulary.SPECIAL_TOKENS.get('<END>', 3):
                            break
                        if token_id < 5:  # Skip special tokens
                            continue
                        
                        generated_tokens.append(token_id)
                        
                        # Track for repetition penalty (keep last 8)
                        recent_tokens.append(token_id)
                        if len(recent_tokens) > 8:
                            recent_tokens.pop(0)
                        
                        # Early stop if we have enough
                        if len(generated_tokens) >= max_tokens:
                            break
        
        # Decode tokens to words
        if generated_tokens:
            words = self.vocabulary.decode(generated_tokens, skip_special=True)
            return ' '.join(words)
        
        return ""
    
    def _get_contextual_response(self, action: str, state: np.ndarray) -> str:
        """Generate contextual response based on action and state."""
        # Enhanced responses that consider state context
        base_responses = {
            'move': [
                "Moving to explore the environment.",
                "Relocating to a better position.",
                "Seeking new opportunities elsewhere.",
            ],
            'cooperate': [
                "Seeking cooperation with nearby entities.",
                "Offering to work together.",
                "Building alliances for mutual benefit.",
            ],
            'compete': [
                "Competing for available resources.",
                "Asserting dominance in this situation.",
                "Fighting for what I need.",
            ],
            'rest': [
                "Resting to conserve energy.",
                "Taking a moment to recover.",
                "Pausing to assess the situation.",
            ],
            'reproduce': [
                "Conditions favor reproduction.",
                "Passing on my knowledge to the next generation.",
                "Creating offspring to continue my legacy.",
            ],
            'isolate': [
                "Isolating for safety.",
                "Withdrawing from potential threats.",
                "Finding solitude to regroup.",
            ],
        }
        
        responses = base_responses.get(action, ["Taking action."])
        
        # Use state to pick contextually appropriate response
        if len(state) >= 8:
            # Use energy/health state to modulate
            energy_level = state[6] if len(state) > 6 else 0.5
            if energy_level < 0.3:
                # Low energy responses
                modifiers = {
                    'move': "Despite low energy, I'm moving.",
                    'rest': "Desperately need to rest.",
                    'compete': "Struggling but competing.",
                }
                if action in modifiers:
                    return modifiers[action]
        
        # Random selection from base responses for variety
        return responses[self.total_steps % len(responses)]
    
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
            BridgeResult with action, response, confidence, ensemble voting details
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
        
        # Run inference (now returns 4-tuple with ensemble_result)
        action, q_values, confidence, ensemble_result = self._infer(state)
        self.last_action = action
        self.total_steps += 1
        
        # Generate language response (with ensemble awareness)
        if ensemble_result and self.config.is_ensemble:
            response = self._generate_ensemble_response(state, action, ensemble_result)
        else:
            response = self._generate_response(state, action)
        
        # Decay epsilon
        if self.config.epsilon > self.config.epsilon_min:
            self.config.epsilon *= self.config.epsilon_decay
        
        # Build metadata
        metadata = {
            'total_steps': self.total_steps,
            'epsilon': self.config.epsilon,
            'input_type': 'obs' if obs is not None else ('text' if text is not None else 'context')
        }
        
        # Add ensemble info if applicable
        if self.config.is_ensemble:
            metadata['is_ensemble'] = True
            metadata['voting_strategy'] = self.config.voting_strategy
            metadata['member_count'] = self.config.member_count
        
        # Create result
        result = BridgeResult(
            action=action,
            action_name=self.ACTION_NAMES[action],
            response=response,
            confidence=confidence,
            q_values=q_values,
            state_vector=state.tolist(),
            metadata=metadata,
            ensemble_result=ensemble_result
        )
        
        return result
    
    def _generate_ensemble_response(self, state: np.ndarray, action: int, 
                                     ensemble_result: EnsembleResult) -> str:
        """
        Generate response for ensemble decision with agreement context.
        
        Mirrors butterfly_chat's approach of selecting best response from
        organisms that voted for the winning action.
        """
        # Try language head first
        if self.has_language_head and self.vocabulary.vocab_size > 10:
            try:
                response = self._generate_from_language_head(state)
                if response and len(response) > 2:
                    return response
            except Exception:
                pass
        
        # Build contextual response with ensemble awareness
        agreement_pct = ensemble_result.agreement_ratio * 100
        voter_count = len(ensemble_result.votes)
        
        # Base action responses
        base_responses = {
            0: "Moving to a new position.",
            1: "Seeking cooperation.",
            2: "Competing for resources.",
            3: "Resting to recover.",
            4: "Reproducing.",
            5: "Isolating for safety.",
        }
        
        action_text = base_responses.get(action, f"Taking action {action}.")
        
        # Add ensemble context if agreement is notable
        if agreement_pct >= 80:
            return f"{action_text} (Strong consensus: {agreement_pct:.0f}% of {voter_count} organisms)"
        elif agreement_pct >= 50:
            return f"{action_text} (Majority decision: {agreement_pct:.0f}% agreement)"
        elif agreement_pct >= 30:
            return f"{action_text} (Contested vote: {agreement_pct:.0f}% agreement)"
        else:
            return f"{action_text} (Divided opinion: {agreement_pct:.0f}% consensus)"
    
    def set_voting_strategy(self, strategy: str):
        """
        Change the ensemble voting strategy at runtime.
        
        Args:
            strategy: One of 'single', 'majority', 'fitness_weighted', 
                     'softmax_ensemble', 'confidence_weighted', 'fittest_top_k'
        """
        valid_strategies = ['single', 'majority', 'fitness_weighted', 
                           'softmax_ensemble', 'confidence_weighted', 'fittest_top_k']
        if strategy.lower() not in valid_strategies:
            raise ValueError(f"Invalid strategy. Choose from: {valid_strategies}")
        self.config.voting_strategy = strategy.lower()
        logger.info(f"Voting strategy changed to: {strategy}")
    
    def get_ensemble_stats(self) -> Dict[str, Any]:
        """Get statistics about the ensemble configuration and advanced features."""
        if not self.config.is_ensemble:
            return {'is_ensemble': False}
        
        return {
            'is_ensemble': True,
            'member_count': self.config.member_count,
            'voting_strategy': self.config.voting_strategy,
            'top_k_voters': self.config.top_k_voters,
            'fitness_stats': {
                'min': min(self.config.member_fitness) if self.config.member_fitness else 0,
                'max': max(self.config.member_fitness) if self.config.member_fitness else 0,
                'mean': sum(self.config.member_fitness) / len(self.config.member_fitness) if self.config.member_fitness else 0
            },
            'member_ids': self.config.member_ids[:5],  # First 5 for brevity
            # Advanced features
            'advanced_features': {
                'adaptive_strategy': self.config.adaptive_strategy,
                'temperature_scaling': self.config.temperature_scaling,
                'current_temperature': round(self._current_temperature, 3),
                'cache_enabled': self.config.cache_enabled,
                'cache_size': len(self._response_cache),
                'cache_max_size': self.config.cache_size,
                'parallel_inference': self.config.parallel_inference,
                'recent_confidences': list(self._recent_confidences)[-5:] if self._recent_confidences else []
            }
        }
    
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
        
        # Online learning: train if enabled and buffer has enough samples
        if self._online_learning_enabled and len(self.experience_buffer.buffer) >= self._train_batch_size:
            self._train_step()
    
    # =========================================================================
    # ONLINE LEARNING - Independent Training Outside Butterfly
    # =========================================================================
    
    def enable_online_learning(self, learning_rate: float = 0.001) -> bool:
        """
        Enable online learning for this agent.
        
        This allows the agent to update its weights during gym runs,
        learning independently from the Butterfly ecosystem.
        
        Returns True if online learning was successfully enabled.
        Requires PyTorch and a non-frozen model format.
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - cannot enable online learning")
            return False
        
        if self.brain is None:
            logger.warning("No brain loaded - cannot enable online learning")
            return False
        
        # TorchScript models can be made trainable
        if self.brain_type == 'torchscript':
            try:
                # Create a trainable version of the model
                # TorchScript models have parameters that can be optimized
                self._optimizer = torch.optim.Adam(
                    self.brain.parameters(), 
                    lr=learning_rate
                )
                self._train_batch_size = 32
                self._train_steps = 0
                self._total_loss = 0.0
                self._online_learning_enabled = True
                self._gamma = 0.99  # Discount factor for Q-learning
                
                logger.info(f"Online learning enabled (TorchScript, lr={learning_rate})")
                return True
            except Exception as e:
                logger.warning(f"Failed to enable online learning: {e}")
                return False
        
        elif self.brain_type == 'onnx':
            logger.warning("ONNX models are frozen - cannot enable online learning")
            logger.info("  Export your agent as TorchScript for online learning")
            return False
        
        return False
    
    def disable_online_learning(self):
        """Disable online learning and freeze the model."""
        self._online_learning_enabled = False
        if hasattr(self, '_optimizer'):
            del self._optimizer
        logger.info("Online learning disabled")
    
    def _train_step(self):
        """Perform one training step using experience buffer."""
        if not self._online_learning_enabled or self.brain is None:
            return
        
        if not TORCH_AVAILABLE:
            return
        
        try:
            # Sample batch from experience buffer
            batch = self.experience_buffer.sample(self._train_batch_size)
            if len(batch) < self._train_batch_size:
                return
            
            # Convert to tensors
            states = torch.tensor(
                np.array([exp['state'] for exp in batch]), 
                dtype=torch.float32
            )
            actions = torch.tensor(
                [exp['action'] for exp in batch], 
                dtype=torch.long
            )
            rewards = torch.tensor(
                [exp['reward'] for exp in batch], 
                dtype=torch.float32
            )
            next_states = torch.tensor(
                np.array([exp['next_state'] for exp in batch]), 
                dtype=torch.float32
            )
            dones = torch.tensor(
                [exp['done'] for exp in batch], 
                dtype=torch.float32
            )
            
            # Get current Q values
            self.brain.train()  # Enable training mode
            outputs = self.brain(states)
            
            # Handle different output formats
            if isinstance(outputs, tuple):
                q_values = outputs[0]
            else:
                q_values = outputs
            
            # Get Q values for taken actions
            current_q = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
            
            # Compute target Q values (no gradient for targets)
            with torch.no_grad():
                next_outputs = self.brain(next_states)
                if isinstance(next_outputs, tuple):
                    next_q_values = next_outputs[0]
                else:
                    next_q_values = next_outputs
                
                max_next_q = next_q_values.max(1)[0]
                target_q = rewards + (1 - dones) * self._gamma * max_next_q
            
            # Compute loss (MSE)
            loss = torch.nn.functional.mse_loss(current_q, target_q)
            
            # Backprop
            self._optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.brain.parameters(), max_norm=1.0)
            
            self._optimizer.step()
            
            # Track stats
            self._train_steps += 1
            self._total_loss += loss.item()
            
            self.brain.eval()  # Back to eval mode
            
            if self._train_steps % 100 == 0:
                avg_loss = self._total_loss / self._train_steps
                logger.info(f"Online learning step {self._train_steps}, avg_loss={avg_loss:.4f}")
                
        except Exception as e:
            logger.warning(f"Training step failed: {e}")
            self.brain.eval()  # Ensure we're back in eval mode
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get online learning statistics."""
        if not hasattr(self, '_online_learning_enabled') or not self._online_learning_enabled:
            return {'online_learning': False}
        
        return {
            'online_learning': True,
            'training_steps': self._train_steps,
            'total_loss': self._total_loss,
            'avg_loss': self._total_loss / max(1, self._train_steps),
            'buffer_size': len(self.experience_buffer.buffer),
            'batch_size': self._train_batch_size
        }
    
    def save_trained_model(self, path: Path):
        """Save the trained model after online learning."""
        if not TORCH_AVAILABLE or self.brain is None:
            logger.warning("Cannot save model - PyTorch not available or no brain")
            return False
        
        path = Path(path)
        try:
            if self.brain_type == 'torchscript':
                # Save updated TorchScript model
                self.brain.save(str(path))
                logger.info(f"Saved trained model to {path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to save model: {e}")
        return False

    # =========================================================================
    # MODE 1: Gymnasium/Gym Environment Runner
    # =========================================================================
    
    def list_environments(self) -> Dict[str, List[str]]:
        """List all available gymnasium environments by category."""
        try:
            import gymnasium as gym
            try:
                import ale_py
                gym.register_envs(ale_py)
            except ImportError:
                pass
        except ImportError:
            return {'error': 'gymnasium not installed'}
        
        envs = list(gym.envs.registry.keys())
        
        categories = {
            'classic_control': sorted([e for e in envs if any(x in e for x in 
                ['CartPole', 'MountainCar', 'Pendulum', 'Acrobot', 'LunarLander']) and 'ALE' not in e]),
            'tabular': sorted([e for e in envs if any(x in e for x in 
                ['FrozenLake', 'Taxi', 'Blackjack', 'Cliff']) and 'ALE' not in e]),
            'box2d': sorted([e for e in envs if any(x in e for x in 
                ['Bipedal', 'CarRacing', 'LunarLander']) and 'ALE' not in e]),
            'mujoco': sorted([e for e in envs if any(x in e for x in 
                ['Ant-', 'Cheetah', 'Hopper-', 'Humanoid', 'Walker2d', 'Swimmer', 'Pusher', 'Reacher', 'Inverted'])]),
            'atari': sorted([e for e in envs if 'ALE/' in e]),
            'total_count': len(envs)
        }
        return categories
    
    def get_environment_info(self, env_spec: str) -> Dict[str, Any]:
        """Get detailed information about a specific environment."""
        try:
            import gymnasium as gym
            try:
                import ale_py
                gym.register_envs(ale_py)
            except ImportError:
                pass
        except ImportError:
            return {'error': 'gymnasium not installed'}
        
        try:
            env = gym.make(env_spec)
            info = {
                'name': env_spec,
                'action_space': str(env.action_space),
                'observation_space': str(env.observation_space),
                'reward_range': getattr(env, 'reward_range', 'unknown'),
                'max_episode_steps': getattr(env.spec, 'max_episode_steps', None) if env.spec else None,
            }
            
            # Get action meanings if available
            if hasattr(env.action_space, 'n'):
                info['num_actions'] = env.action_space.n
                if hasattr(env, 'get_action_meanings'):
                    info['action_meanings'] = env.get_action_meanings()
                elif hasattr(env.unwrapped, 'get_action_meanings'):
                    info['action_meanings'] = env.unwrapped.get_action_meanings()
            
            # Get observation shape
            if hasattr(env.observation_space, 'shape'):
                info['obs_shape'] = env.observation_space.shape
            
            env.close()
            return info
        except Exception as e:
            return {'error': str(e)}
    
    def run_gym(self, 
                env_spec: str,
                episodes: int = 10,
                max_steps: Optional[int] = None,
                render: bool = False,
                learn: bool = True,
                verbose: bool = True,
                save_best: bool = False) -> Dict[str, Any]:
        """
        Run agent in a Gymnasium environment with rich progress display.
        
        Args:
            env_spec: Gym environment spec (e.g., 'CartPole-v1')
            episodes: Number of episodes to run
            max_steps: Max steps per episode (None = no limit)
            render: Whether to render environment visually
            learn: Whether to enable online learning
            verbose: Whether to show detailed progress
            save_best: Whether to save model when new best score achieved
            
        Returns:
            Comprehensive statistics dict
        """
        # Import gym with helpful error message
        try:
            import gymnasium as gym
            try:
                import ale_py
                gym.register_envs(ale_py)
            except ImportError:
                pass
        except ImportError:
            try:
                import gym
            except ImportError:
                print("\n❌ Gym environment not available.")
                print("   Install with one of:")
                print("     pip install gymnasium    (recommended)")
                print("     pip install gym          (legacy)")
                print("")
                return {'error': 'gymnasium/gym not installed', 'episodes': 0, 'total_rewards': [], 'episode_lengths': []}
        
        # Get environment info first
        env_info = self.get_environment_info(env_spec)
        if 'error' in env_info:
            print(f"\n❌ Environment error: {env_info['error']}")
            return {'error': env_info['error']}
        
        # Display environment info if verbose
        if verbose:
            print("\n" + "="*60)
            print(f"🎮 GYMNASIUM ARENA: {env_spec}")
            print("="*60)
            print(f"  Action Space:      {env_info.get('action_space', 'unknown')}")
            print(f"  Observation Space: {env_info.get('observation_space', 'unknown')}")
            if 'num_actions' in env_info:
                print(f"  Num Actions:       {env_info['num_actions']}")
            if 'action_meanings' in env_info:
                print(f"  Action Meanings:   {env_info['action_meanings'][:6]}...")
            if env_info.get('max_episode_steps'):
                print(f"  Max Steps/Episode: {env_info['max_episode_steps']}")
            print("-"*60)
            print(f"  Episodes: {episodes} | Render: {render} | Online Learning: {learn}")
            print("="*60 + "\n")
        
        # Create environment with render mode if requested
        if render:
            env = gym.make(env_spec, render_mode='human')
        else:
            env = gym.make(env_spec)
        
        # Initialize stats tracking
        stats = {
            'env': env_spec,
            'env_info': env_info,
            'episodes': episodes,
            'total_rewards': [],
            'episode_lengths': [],
            'actions_taken': [],
            'best_reward': float('-inf'),
            'best_episode': 0,
            'worst_reward': float('inf'),
            'worst_episode': 0,
            'render': render,
            'online_learning': learn
        }
        
        # Track action distribution
        action_counts = {}
        start_time = time.time()
        
        for ep in range(episodes):
            obs, info = env.reset() if hasattr(env, 'reset') else (env.reset(), {})
            done = False
            total_reward = 0
            steps = 0
            ep_actions = []
            
            while not done:
                if render:
                    env.render()
                
                # Get action
                result = self.process(obs=obs)
                action = result.action
                
                # Ensure action is valid for this env
                if hasattr(env.action_space, 'n'):
                    action = action % env.action_space.n
                
                # Track action
                ep_actions.append(action)
                action_counts[action] = action_counts.get(action, 0) + 1
                
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
            
            # Track episode stats
            stats['total_rewards'].append(total_reward)
            stats['episode_lengths'].append(steps)
            stats['actions_taken'].append(ep_actions)
            
            # Track best/worst
            if total_reward > stats['best_reward']:
                stats['best_reward'] = total_reward
                stats['best_episode'] = ep + 1
            if total_reward < stats['worst_reward']:
                stats['worst_reward'] = total_reward
                stats['worst_episode'] = ep + 1
            
            # Display progress
            if verbose:
                # Progress bar
                progress = (ep + 1) / episodes
                bar_width = 30
                filled = int(bar_width * progress)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # Running stats
                running_mean = np.mean(stats['total_rewards'])
                running_std = np.std(stats['total_rewards']) if len(stats['total_rewards']) > 1 else 0
                
                # Episode indicator
                trend = "📈" if total_reward >= running_mean else "📉"
                if total_reward == stats['best_reward']:
                    trend = "🏆"
                
                print(f"\r  [{bar}] {ep+1}/{episodes} | "
                      f"Reward: {total_reward:7.2f} {trend} | "
                      f"Avg: {running_mean:7.2f} ± {running_std:5.2f} | "
                      f"Steps: {steps:4d}", end='')
                
                if (ep + 1) % 10 == 0 or ep == episodes - 1:
                    print()  # New line every 10 episodes
        
        env.close()
        
        # Calculate final statistics
        elapsed = time.time() - start_time
        stats['elapsed_time'] = elapsed
        stats['mean_reward'] = np.mean(stats['total_rewards'])
        stats['std_reward'] = np.std(stats['total_rewards'])
        stats['min_reward'] = min(stats['total_rewards'])
        stats['max_reward'] = max(stats['total_rewards'])
        stats['mean_steps'] = np.mean(stats['episode_lengths'])
        stats['total_steps'] = sum(stats['episode_lengths'])
        stats['steps_per_second'] = stats['total_steps'] / elapsed if elapsed > 0 else 0
        
        # Action distribution
        total_actions = sum(action_counts.values())
        stats['action_distribution'] = {
            a: {'count': c, 'percentage': c/total_actions*100} 
            for a, c in sorted(action_counts.items())
        }
        
        # Add training stats if online learning was active
        if hasattr(self, '_online_learning_enabled') and self._online_learning_enabled:
            train_stats = self.get_training_stats()
            stats['training_steps'] = train_stats['training_steps']
            stats['final_loss'] = train_stats['avg_loss']
        
        # Display final summary if verbose
        if verbose:
            print("\n" + "="*60)
            print("📊 FINAL RESULTS")
            print("="*60)
            print(f"  Environment:     {env_spec}")
            print(f"  Episodes:        {episodes}")
            print(f"  Total Steps:     {stats['total_steps']:,}")
            print(f"  Time Elapsed:    {elapsed:.2f}s ({stats['steps_per_second']:.0f} steps/sec)")
            print("-"*60)
            print(f"  Mean Reward:     {stats['mean_reward']:.2f} ± {stats['std_reward']:.2f}")
            print(f"  Best Reward:     {stats['best_reward']:.2f} (Episode {stats['best_episode']})")
            print(f"  Worst Reward:    {stats['worst_reward']:.2f} (Episode {stats['worst_episode']})")
            print(f"  Mean Steps/Ep:   {stats['mean_steps']:.1f}")
            print("-"*60)
            print("  Action Distribution:")
            for action, data in stats['action_distribution'].items():
                bar = '█' * int(data['percentage'] / 5)
                action_name = env_info.get('action_meanings', {})
                if isinstance(action_name, list) and action < len(action_name):
                    action_name = action_name[action]
                else:
                    action_name = f"Action {action}"
                print(f"    {action_name:15} {bar:20} {data['percentage']:5.1f}% ({data['count']:,})")
            
            if learn and hasattr(self, '_online_learning_enabled') and self._online_learning_enabled:
                print("-"*60)
                print(f"  🧠 Online Learning:")
                print(f"     Training Steps: {stats.get('training_steps', 0)}")
                print(f"     Final Loss:     {stats.get('final_loss', 0):.6f}")
            
            print("="*60 + "\n")
        
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
        print(f"\n[Butterfly] AgentBridge HTTP Server")
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
    # MODE 3.5: Proton Game Arena (Apprentice Adept Style)
    # =========================================================================
    
    def _handle_arena_command(self, command: str):
        """
        Handle /arena commands for Proton Game Arena interaction.
        
        Commands:
            /arena              - Show game selection grid
            /arena games        - List all arena games
            /arena games <cat>  - Games by category (physical/mental/chance/arts)
            /arena play <game>  - Play a specific arena game
        """
        parts = command.lower().strip().split()
        
        # Get arena data (embedded - no external imports needed)
        ARENA_GAMES = {
            ('physical', 'naked'): [
                ('Balance Beam', 'CartPole-v1', 'NOVICE', 'Pure balance challenge'),
                ('Mountain Climb', 'MountainCar-v0', 'APPRENTICE', 'Build momentum to climb'),
                ('Gymnast Swing', 'Acrobot-v1', 'JOURNEYMAN', 'Swing using body momentum'),
            ],
            ('physical', 'tool'): [
                ('Lunar Landing', 'LunarLander-v3', 'JOURNEYMAN', 'Land spacecraft with thrusters'),
                ('Pendulum Control', 'Pendulum-v1', 'APPRENTICE', 'Control pendulum with force'),
            ],
            ('physical', 'machine'): [
                ('Road Racing', 'CarRacing-v3', 'EXPERT', 'Race car around track'),
                ('Endurance Rally', 'ALE/Enduro-v5', 'EXPERT', 'Endless racing endurance'),
            ],
            ('physical', 'animal'): [
                ('Bipedal Walk', 'BipedalWalker-v3', 'EXPERT', 'Walk on two legs'),
            ],
            ('mental', 'naked'): [
                ('Frozen Lake', 'FrozenLake-v1', 'NOVICE', 'Navigate slippery ice'),
                ('Cliff Walking', 'CliffWalking-v0', 'APPRENTICE', 'Navigate cliffs safely'),
            ],
            ('mental', 'tool'): [
                ('Blackjack', 'Blackjack-v1', 'APPRENTICE', 'Card counting and probability'),
                ('Taxi Navigation', 'Taxi-v3', 'JOURNEYMAN', 'Optimal pickup/dropoff'),
            ],
            ('mental', 'machine'): [
                ('Brick Breaker', 'ALE/Breakout-v5', 'JOURNEYMAN', 'Strategic brick destruction'),
                ('Space Defense', 'ALE/SpaceInvaders-v5', 'JOURNEYMAN', 'Defend against waves'),
                ('Pac Maze', 'ALE/MsPacman-v5', 'EXPERT', 'Navigate maze, avoid ghosts'),
            ],
            ('chance', 'naked'): [
                ('Coin Fate', 'coin_flip', 'NOVICE', 'Pure luck - coin flip'),
            ],
            ('chance', 'tool'): [
                ('Card Draw', 'Blackjack-v1', 'APPRENTICE', 'Luck meets strategy'),
            ],
        }
        
        if len(parts) == 1:
            # /arena - Show grid
            print("\n" + "="*70)
            print("  🎮 PROTON GAME ARENA - Game Selection Grid")
            print("  (Inspired by Piers Anthony's Apprentice Adept)")
            print("="*70)
            print()
            print("  " + " "*15 + "NAKED        TOOL         MACHINE      ANIMAL")
            print("  " + "-"*65)
            for challenge in ['physical', 'mental', 'chance', 'arts']:
                row = f"  {challenge.upper():12}"
                for resource in ['naked', 'tool', 'machine', 'animal']:
                    games = ARENA_GAMES.get((challenge, resource), [])
                    if games:
                        row += f"  [{len(games)} games]  "
                    else:
                        row += "     ---      "
                print(row)
            print("  " + "-"*65)
            print("\n  Commands:")
            print("    /arena games         - List all games")
            print("    /arena games <cat>   - Games by category")
            print("    /arena play <game>   - Play specific game")
            print("="*70 + "\n")
            return
        
        subcommand = parts[1] if len(parts) > 1 else ""
        
        if subcommand == 'games':
            # /arena games [category]
            category_filter = parts[2] if len(parts) > 2 else None
            
            print("\n" + "="*60)
            print("  📋 ARENA GAMES")
            print("="*60)
            
            for (challenge, resource), games in ARENA_GAMES.items():
                if category_filter and challenge != category_filter:
                    continue
                    
                if games:
                    print(f"\n  {challenge.upper()} + {resource.upper()}:")
                    for name, env, difficulty, desc in games:
                        print(f"    • {name}")
                        print(f"      Env: {env} ({difficulty})")
                        print(f"      {desc}")
            
            print("\n" + "="*60 + "\n")
            return
        
        elif subcommand == 'play':
            # /arena play <game_name>
            if len(parts) < 3:
                print("\n  Usage: /arena play <game>")
                print("  Example: /arena play 'Balance Beam'")
                print("  Use /arena games to see available games\n")
                return
            
            game_name = ' '.join(parts[2:]).strip("'\"")
            
            # Find the game
            found_game = None
            for (challenge, resource), games in ARENA_GAMES.items():
                for name, env, difficulty, desc in games:
                    if name.lower() == game_name.lower():
                        found_game = (name, env, difficulty, desc, challenge, resource)
                        break
                if found_game:
                    break
            
            if not found_game:
                print(f"\n  ❌ Game '{game_name}' not found")
                print("  Use /arena games to see available games\n")
                return
            
            name, env, difficulty, desc, challenge, resource = found_game
            
            print("\n" + "="*60)
            print(f"  🎮 ARENA: {name}")
            print(f"  Category: {challenge.upper()} × {resource.upper()}")
            print(f"  Difficulty: {difficulty}")
            print(f"  {desc}")
            print("="*60)
            
            # Check if gym env exists
            if env.startswith('ALE/') or env in ['CartPole-v1', 'MountainCar-v0', 'Acrobot-v1',
                                                    'LunarLander-v3', 'Pendulum-v1', 'CarRacing-v3',
                                                    'BipedalWalker-v3', 'FrozenLake-v1', 'CliffWalking-v0',
                                                    'Blackjack-v1', 'Taxi-v3']:
                print("\n  Running 5 episodes...")
                print("-"*60)
                self.run_gym(env, episodes=5, render=False, learn=True, verbose=True)
            else:
                print(f"\n  ⚠️ Custom game '{env}' - not a standard gym environment")
                print("  This game requires special handling\n")
            
            print("="*60 + "\n")
            return
        
        else:
            print(f"\n  Unknown arena command: {subcommand}")
            print("  Use /arena for help\n")
    
    # =========================================================================
    # MODE 3: Interactive CLI
    # =========================================================================
    
    def interactive(self):
        """
        Start interactive CLI mode with comprehensive gym integration.
        
        Commands:
            <text>            - Send text to agent
            /act <json>       - Send structured action request
            /gym <env>        - Run in Gym environment
            /envs             - Browse available environments
            /info <env>       - Get environment details
            /train            - Show training stats
            /state            - Show current state
            /config           - Show configuration
            /help             - Show all commands
            /quit             - Exit
        """
        print("\n" + "="*60)
        print("  🦋 BUTTERFLY AGENT - Interactive Mode")
        print("="*60)
        print("  Type messages to chat, or use commands:")
        print("  /gym, /envs, /arena, /train, /state, /help, /quit")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_input:
                continue
            
            if user_input.lower() == '/quit':
                break
            
            elif user_input.lower() == '/help':
                print("\n" + "-"*50)
                print("  📖 COMMANDS")
                print("-"*50)
                print("  Chat:")
                print("    <text>              - Chat with the agent")
                print("    /act {json}         - Send structured input")
                print()
                print("  Gymnasium:")
                print("    /gym <env>          - Run 3 episodes")
                print("    /gym <env> N        - Run N episodes")
                print("    /gym <env> render   - With visual rendering")
                print("    /gym <env> learn    - With online learning")
                print("    /gym <env> 10 render learn  - Combined")
                print("    /envs               - Browse all environments")
                print("    /envs <category>    - Filter by category")
                print("    /info <env>         - Environment details")
                print()
                print("  Proton Arena:")
                print("    /arena              - Show Proton Game grid")
                print("    /arena games        - List all arena games")
                print("    /arena games <cat>  - Games by category")
                print("    /arena play <game>  - Play specific arena game")
                print()
                print("  Status:")
                print("    /train              - Training statistics")
                print("    /state              - Agent state")
                print("    /config             - Configuration")
                print("-"*50 + "\n")
                continue
            
            elif user_input.lower() == '/state':
                print(f"\nState: {self.current_state}")
                print(f"Steps: {self.total_steps}, Epsilon: {self.config.epsilon:.4f}")
                print()
                continue
            
            elif user_input.lower() == '/config':
                print(f"\nConfig: {json.dumps(self.config.to_dict(), indent=2)}")
                print()
                continue
            
            elif user_input.lower() == '/train':
                stats = self.get_training_stats()
                print(f"\nTraining stats: {json.dumps(stats, indent=2)}")
                print()
                continue
            
            elif user_input.lower().startswith('/arena'):
                self._handle_arena_command(user_input)
                continue
            
            elif user_input.lower().startswith('/envs'):
                parts = user_input.split()
                category = parts[1].lower() if len(parts) > 1 else None
                
                categories = self.list_environments()
                if 'error' in categories:
                    print(f"\n❌ {categories['error']}")
                    continue
                
                print("\n" + "="*60)
                print("  🎮 GYMNASIUM ENVIRONMENTS")
                print("="*60)
                
                cat_map = {
                    'classic': 'classic_control',
                    'control': 'classic_control',
                    'tabular': 'tabular',
                    'grid': 'tabular',
                    'box2d': 'box2d',
                    'physics': 'box2d',
                    'mujoco': 'mujoco',
                    'robot': 'mujoco',
                    'atari': 'atari',
                    'arcade': 'atari'
                }
                
                if category and category in cat_map:
                    cat_key = cat_map[category]
                    envs = categories.get(cat_key, [])
                    print(f"\n  📁 {cat_key.upper()} ({len(envs)} environments)")
                    print("-"*50)
                    for env in envs[:30]:
                        print(f"    {env}")
                    if len(envs) > 30:
                        print(f"    ... and {len(envs)-30} more")
                else:
                    print(f"\n  Total Environments: {categories.get('total_count', '?')}")
                    print()
                    for cat_name in ['classic_control', 'tabular', 'box2d', 'mujoco', 'atari']:
                        envs = categories.get(cat_name, [])
                        sample = envs[:3] if envs else []
                        print(f"  📁 {cat_name.upper()} ({len(envs)})")
                        for env in sample:
                            print(f"      {env}")
                        if len(envs) > 3:
                            print(f"      ...")
                        print()
                    print("  Use /envs <category> for full list")
                    print("  Categories: classic, tabular, box2d, mujoco, atari")
                
                print("="*60 + "\n")
                continue
            
            elif user_input.lower().startswith('/info '):
                env_spec = user_input[6:].strip()
                info = self.get_environment_info(env_spec)
                
                if 'error' in info:
                    print(f"\n❌ {info['error']}")
                else:
                    print("\n" + "-"*50)
                    print(f"  📋 {env_spec}")
                    print("-"*50)
                    for key, value in info.items():
                        if key != 'name':
                            print(f"  {key}: {value}")
                    print("-"*50 + "\n")
                continue
            
            elif user_input.lower().startswith('/gym'):
                parts = user_input[4:].strip().split()
                
                if not parts:
                    # Show quick help
                    print("\n  Usage: /gym <env> [episodes] [render] [learn]")
                    print("  Example: /gym CartPole-v1 10 render learn")
                    print("  Use /envs to see available environments\n")
                    continue
                
                env_spec = parts[0]
                
                # Parse options
                episodes = 3
                render = False
                learn = False
                
                for p in parts[1:]:
                    if p.isdigit():
                        episodes = int(p)
                    elif p.lower() == 'render':
                        render = True
                    elif p.lower() == 'learn':
                        learn = True
                
                if learn:
                    print("  Enabling online learning...")
                    if self.enable_online_learning():
                        print("  ✅ Online learning enabled")
                    else:
                        print("  ⚠️ Could not enable online learning (frozen model?)")
                
                # Run with the comprehensive run_gym
                stats = self.run_gym(env_spec, episodes=episodes, render=render, learn=learn, verbose=True)
                
                if 'error' in stats:
                    print(f"\n❌ Error: {stats['error']}\n")
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
        
        print("\n  Goodbye! 🦋\n")
    
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
                print(f"  [OK] Found brain: {brain_path.name}")
                break
        
        if brain_path is None:
            print(f"  [!] No brain file found in {directory}")
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
        
        # Load metadata for ensemble information (fitness scores, member IDs)
        metadata_path = directory / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract ensemble member data
            ensemble_info = metadata.get('ensemble', {})
            members = ensemble_info.get('members', [])
            
            if members:
                config.is_ensemble = True
                config.member_count = len(members)
                
                # Extract fitness and IDs for each member
                config.member_fitness = []
                config.member_ids = []
                
                for member in members:
                    # Extract fitness (try multiple possible keys)
                    fitness = member.get('fitness')
                    if fitness is None:
                        fitness = member.get('core', {}).get('fitness', 1.0)
                    if fitness is None:
                        fitness = 1.0
                    config.member_fitness.append(float(fitness))
                    
                    # Extract organism ID
                    org_id = member.get('organism_id', member.get('id', f'org_{len(config.member_ids)}'))
                    config.member_ids.append(str(org_id))
                
                print(f"  [OK] Ensemble: {config.member_count} organisms")
                
                # Show fitness distribution
                if config.member_fitness:
                    min_fit = min(config.member_fitness)
                    max_fit = max(config.member_fitness)
                    avg_fit = sum(config.member_fitness) / len(config.member_fitness)
                    print(f"       Fitness range: {min_fit:.4f} - {max_fit:.4f} (avg: {avg_fit:.4f})")
        
        # Load vocabulary
        vocab = PortableVocabulary()
        vocab_path = directory / 'vocabulary.json'
        if not vocab_path.exists():
            vocab_path = directory / 'atomic_language.json'
        if vocab_path.exists():
            vocab = PortableVocabulary.load(vocab_path)
            print(f"  [OK] Loaded vocabulary: {vocab.vocab_size} words")
        else:
            print(f"  [!] No vocabulary file found")
        
        # Create bridge
        bridge = cls(
            brain_path=brain_path,
            config=config,
            vocabulary=vocab
        )
        
        # Override has_language_head from config if not detected from model
        # (for models that were compiled with language head support)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            if config_data.get('has_language_head', False) and not bridge.has_language_head:
                bridge.has_language_head = True
                print(f"  [OK] Language head enabled from config")
        
        # Report voting strategy for ensemble
        if config.is_ensemble:
            print(f"  [OK] Voting strategy: {config.voting_strategy}")
        
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
    parser.add_argument(
        '--render', '-r',
        action='store_true',
        help='Enable visual rendering for gym mode'
    )
    parser.add_argument(
        '--online-learn', '-l',
        action='store_true',
        help='Enable online learning (updates weights during gym run)'
    )
    parser.add_argument(
        '--learning-rate', '-lr',
        type=float,
        default=0.001,
        help='Learning rate for online learning (default: 0.001)'
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
        # Enable online learning if requested
        if args.online_learn:
            if bridge.enable_online_learning(learning_rate=args.learning_rate):
                print(f"  [OK] Online learning enabled (lr={args.learning_rate})")
            else:
                print(f"  [!] Online learning not available (frozen model)")
        
        stats = bridge.run_gym(
            args.gym_env, 
            episodes=args.episodes,
            render=args.render,
            learn=args.online_learn
        )
        print(f"\nResults:")
        if 'error' in stats:
            print(f"  Error: {stats['error']}")
            print(f"  Install gymnasium with: pip install gymnasium")
        else:
            print(f"  Mean reward: {stats['mean_reward']:.2f} ± {stats['std_reward']:.2f}")
            print(f"  Episodes: {stats['episodes']}")
            if args.online_learn and 'training_steps' in stats:
                print(f"  Training steps: {stats['training_steps']}")
                print(f"  Final loss: {stats.get('final_loss', 'N/A')}")


if __name__ == '__main__':
    main()

