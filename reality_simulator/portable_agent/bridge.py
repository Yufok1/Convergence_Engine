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
        """Generate text using the neural network's language head."""
        if not TORCH_AVAILABLE or self.brain_type != 'torchscript':
            return ""
        
        state = state.astype(np.float32)
        if len(state.shape) == 1:
            state = state.reshape(1, -1)
        
        generated_tokens = []
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state)
            
            # Get model outputs - language logits should be second output if available
            outputs = self.brain(state_tensor)
            
            if isinstance(outputs, tuple) and len(outputs) >= 2:
                # outputs[0] = action probs, outputs[1] = language logits
                language_logits = outputs[1]
                
                if language_logits is not None and language_logits.numel() > 0:
                    # Sample tokens from logits
                    logits = language_logits[0] if len(language_logits.shape) > 1 else language_logits
                    
                    # Apply temperature
                    logits = logits / temperature
                    
                    # Sample multiple tokens
                    probs = torch.softmax(logits, dim=-1)
                    
                    for _ in range(max_tokens):
                        token_id = torch.multinomial(probs, 1).item()
                        
                        # Stop at END token or if we've repeated too much
                        if token_id == self.vocabulary.SPECIAL_TOKENS.get('<END>', 3):
                            break
                        if token_id < 4:  # Skip special tokens
                            continue
                            
                        generated_tokens.append(token_id)
                        
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
        # Import gym with helpful error message
        try:
            import gymnasium as gym
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
        print("\n[Butterfly] AgentBridge Interactive Mode")
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
        
        print("\nGoodbye! [Butterfly]")
    
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

