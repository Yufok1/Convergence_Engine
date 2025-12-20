#!/usr/bin/env python3
"""
🦋 Standalone Butterfly Chat - Neural Organism Communication

This module provides a standalone chat interface for exported Butterfly agent capsules.
It uses the actual neural networks from the exported ensemble to generate responses,
aligning with the main butterfly_chat.py architecture.

Architecture Alignment:
- Uses same routing strategies as ButterflyChatRouter (all, random, fittest, connected)
- Loads neural models (TorchScript/ONNX) from exported capsules
- Uses vocabulary from chat_vocabulary.json for tokenization
- Supports ensemble voting strategies (fitness_weighted, majority, softmax)
- Tracks conversation history and debug information

Usage:
    python standalone_butterfly_chat.py <export_dir>
    python standalone_butterfly_chat.py agent_downloads/16swarm --strategy fittest
"""

import sys
import json
import random
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from enum import Enum

# Optional imports with graceful degradation
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ort = None
    ONNX_AVAILABLE = False


class RoutingStrategy(Enum):
    """Routing strategies aligned with ButterflyChatRouter."""
    ALL = "all"
    RANDOM = "random"
    FITTEST = "fittest"
    CONNECTED = "connected"
    BY_WORD = "by_word"


class VotingStrategy(Enum):
    """Ensemble voting strategies aligned with portable_agent/bridge.py."""
    SINGLE = "single"
    MAJORITY = "majority"
    FITNESS_WEIGHTED = "fitness_weighted"
    SOFTMAX_ENSEMBLE = "softmax_ensemble"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    FITTEST_TOP_K = "fittest_top_k"


@dataclass
class CapsuleVocabulary:
    """
    Vocabulary for tokenization - aligned with LanguageVocabulary.
    
    Loads from chat_vocabulary.json exported with the capsule.
    """
    word_to_id: Dict[str, int] = field(default_factory=dict)
    id_to_word: Dict[int, str] = field(default_factory=dict)
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    
    SPECIAL_TOKENS = {
        '<PAD>': 0,
        '<UNK>': 1,
        '<START>': 2,
        '<END>': 3,
        '<VP_GATE>': 4
    }
    
    def __post_init__(self):
        if not self.word_to_id:
            self.word_to_id = dict(self.SPECIAL_TOKENS)
            self.id_to_word = {v: k for k, v in self.word_to_id.items()}
    
    @property
    def vocab_size(self) -> int:
        return len(self.word_to_id)
    
    def encode(self, words: List[str], add_special: bool = True) -> List[int]:
        """Encode words to token IDs."""
        tokens = []
        if add_special:
            tokens.append(self.SPECIAL_TOKENS['<START>'])
        for word in words:
            token_id = self.word_to_id.get(word.lower(), self.SPECIAL_TOKENS['<UNK>'])
            tokens.append(token_id)
        if add_special:
            tokens.append(self.SPECIAL_TOKENS['<END>'])
        return tokens
    
    def decode(self, tokens: List[int], skip_special: bool = True) -> List[str]:
        """Decode token IDs to words."""
        special_ids = set(self.SPECIAL_TOKENS.values())
        words = []
        for t in tokens:
            if skip_special and t in special_ids:
                continue
            word = self.id_to_word.get(t, '<UNK>')
            words.append(word)
        return words
    
    @classmethod
    def load(cls, path: Path) -> 'CapsuleVocabulary':
        """Load vocabulary from JSON file."""
        vocab = cls()
        if not path.exists():
            print(f"  [!] Vocabulary file not found: {path}")
            return vocab
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different formats
        if 'word_to_id' in data:
            vocab.word_to_id = {k: int(v) for k, v in data['word_to_id'].items()}
        elif 'vocabulary' in data:
            for i, word in enumerate(data['vocabulary'], start=5):
                vocab.word_to_id[word] = i
        
        vocab.id_to_word = {v: k for k, v in vocab.word_to_id.items()}
        vocab.word_frequencies = data.get('word_frequencies', {})
        
        return vocab


@dataclass
class CapsuleOrganism:
    """
    Represents a neural organism from an exported capsule.
    
    Aligned with NeuralOrganism interface for generate_tokens().
    Now includes FULL AtomicLanguageSystem and Token Tumbler support.
    """
    organism_id: str
    fitness: float
    personality: str
    behavioral_tendencies: Dict[str, float]
    input_dim: int
    output_dim: int
    has_language_head: bool
    brain_index: int  # Index in ensemble model
    
    # Runtime state
    experience_buffer: List = field(default_factory=list)
    
    # 🧬 FULL ATOMIC LANGUAGE SYSTEM (not just JSON dict!)
    atomic_language: Any = None  # AtomicLanguageSystem instance
    
    # 🎰 TOKEN TUMBLER support
    token_sequence: Any = None  # deque for token sequences
    
    def __post_init__(self):
        """Initialize token sequence deque after dataclass creation."""
        from collections import deque
        if self.token_sequence is None:
            self.token_sequence = deque(maxlen=128)
    
    def tumble_action_tokens(self, action: int, reward: float, context: str = 'step') -> None:
        """
        🎰 TOKEN TUMBLER: Generate tokens from action/reward.
        
        Creates learnable token sequences that correlate with successful behaviors.
        Aligned with NeuralOrganism.tumble_action_tokens().
        """
        from collections import deque
        if self.token_sequence is None:
            self.token_sequence = deque(maxlen=128)
        
        # Token vocabulary (matches neural_organism.py and agent_compiler.py)
        ACTION_BASE = 100       # 100-109: Action tokens
        REWARD_BASE = 110       # 110-119: Reward bins  
        CONTEXT_TOKENS = {
            'step': 120,
            'catch': 121,
            'miss': 122,
            'move_toward': 123,
            'move_away': 124,
            'social': 125,
            'learn_concept': 126,
            'form_association': 127,
            'chat_response': 128,
            'idle': 129,
        }
        
        # Emit context token first (what happened)
        ctx_token = CONTEXT_TOKENS.get(context, 120)
        self.token_sequence.append(ctx_token)
        
        # Emit action token (what organism did)
        self.token_sequence.append(ACTION_BASE + min(9, max(0, action)))
        
        # Emit reward token (how it went)
        reward_normalized = (reward + 1.0) / 2.0  # -1..1 -> 0..1
        reward_bin = int(max(0, min(0.999, reward_normalized)) * 10)  # 0-9
        self.token_sequence.append(REWARD_BASE + reward_bin)
    
    def acquire_concept(self, concept_id: str, source: str = 'observed', 
                       reason: str = 'unknown') -> bool:
        """Acquire a new concept - aligned with NeuralOrganism."""
        if self.atomic_language is None:
            return False
        was_new = concept_id not in self.atomic_language.atoms
        self.atomic_language.acquire_concept(concept_id, source, reason=reason)
        
        # Generate tokens for learning events (TOKEN TUMBLER)
        if was_new:
            source_reward = {'observed': 0.3, 'taught': 0.5, 'discovered': 0.7}
            reward = source_reward.get(source, 0.3)
            self.tumble_action_tokens(action=5, reward=reward, context='learn_concept')
        
        return was_new
    
    def form_concept_association(self, source: str, target: str, 
                                strength: float, reason: str) -> None:
        """Form association between concepts - aligned with NeuralOrganism."""
        if self.atomic_language is not None:
            self.atomic_language.form_association(source, target, strength, reason)
            reward = max(0.2, abs(strength) * 0.5)
            self.tumble_action_tokens(action=6, reward=reward, context='form_association')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'organism_id': self.organism_id,
            'fitness': self.fitness,
            'personality': self.personality,
            'behavioral_tendencies': self.behavioral_tendencies,
            'has_language_head': self.has_language_head,
            'has_atomic_language': self.atomic_language is not None
        }


@dataclass
class OrganismResponse:
    """Response from an organism - aligned with butterfly_chat.py format."""
    organism_id: str
    response: str
    tokens: List[int]
    fitness: float
    confidence: float
    personality: str


@dataclass
class ChatResult:
    """
    Complete chat result - aligned with ButterflyChatRouter return format.
    """
    response: str
    organism_responses: List[OrganismResponse]
    tokens_used: List[int]
    routing_info: Dict[str, Any]
    debug_logs: List[Dict[str, Any]] = field(default_factory=list)
    causation_trail: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    performance: Dict[str, float] = field(default_factory=dict)


class StandaloneButterflyChat:
    """
    Standalone chat interface for exported Butterfly agent capsules.
    
    Aligns with the main butterfly_chat.py ButterflyChatRouter architecture:
    - Same routing strategies
    - Same response aggregation logic
    - Same debug/causation tracking
    - Uses actual neural networks for response generation
    - 🔮 Uses LinguisticKnowledgeWeb for semantic coherence
    - 🧠 Uses ContextMemory for word-organism mappings
    - 🔬 Uses CausationSystem (Illumination Engine) for understanding WHY
    """
    
    ACTION_NAMES = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
    
    def __init__(self, export_dir: str, voting_strategy: str = 'fitness_weighted',
                 trainer: Optional[Any] = None):
        """
        Initialize standalone chat with optional trainer for continued learning.
        
        Args:
            export_dir: Path to exported capsule directory
            voting_strategy: How to aggregate multi-organism responses
            trainer: Optional NeuralTrainer for chat-triggered training (requires PyTorch)
        """
        self.export_dir = Path(export_dir)
        self.voting_strategy = VotingStrategy(voting_strategy)
        self.trainer = trainer  # Optional: for continued neural learning
        
        # Load components (order matters!)
        self.metadata = self._load_metadata()
        self.vocabulary = self._load_vocabulary()
        self.config = self._load_config()  # Load config BEFORE organisms
        self.organisms = self._create_organisms()
        self.brain = self._load_brain()
        
        # 🔮 Load knowledge web for semantic coherence (CRITICAL!)
        self.knowledge_web = self._load_knowledge_web()
        
        # 🧠 Load context memory for word-organism mappings (CRITICAL!)
        self.context_memory = self._load_context_memory()
        
        # 🔬 Load causation system (illumination engine) for understanding WHY (CRITICAL!)
        self.causation_system = self._load_causation_system()
        
        # 🏛️ Load alliance system for social context (CRITICAL!)
        self.alliance_system = self._load_alliance_system()
        
        # Conversation tracking (aligned with ButterflyChatRouter)
        self.conversation_history: List[Dict[str, Any]] = []
        self.debug_logs: List[Dict[str, Any]] = []
        self.total_messages = 0
        
        # Language generation settings
        self.temperature = 1.0
        self.max_response_length = 32
        self.repetition_penalty = 2.0
        self.top_k = 40
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata.json from capsule."""
        metadata_file = self.export_dir / 'metadata.json'
        if not metadata_file.exists():
            raise FileNotFoundError(f"metadata.json not found in {self.export_dir}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_vocabulary(self) -> CapsuleVocabulary:
        """Load vocabulary from capsule."""
        # Try chat_vocabulary.json first (preferred)
        vocab_path = self.export_dir / 'chat_vocabulary.json'
        if not vocab_path.exists():
            vocab_path = self.export_dir / 'atomic_language.json'
        if not vocab_path.exists():
            vocab_path = self.export_dir / 'vocabulary.json'
        
        return CapsuleVocabulary.load(vocab_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load bridge_config.json from capsule."""
        config_path = self.export_dir / 'bridge_config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_knowledge_web(self) -> Optional[Dict[str, Any]]:
        """
        🔮 Load knowledge web from capsule for semantic coherence.
        
        This is CRITICAL for intelligent text generation. Without it,
        the neural network just outputs repetitive garbage because it
        has no semantic context for word relationships.
        """
        kw_path = self.export_dir / 'knowledge_web.json'
        if not kw_path.exists():
            print(f"  [!] No knowledge_web.json found - semantic guidance disabled")
            return None
        
        try:
            with open(kw_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build indices for fast lookup
            concepts = data.get('concepts', {})
            relations = data.get('relations', [])
            
            # Build relation index: word -> list of related words with strength
            relation_index = defaultdict(list)
            for rel in relations:
                source = rel.get('source', '')
                target = rel.get('target', '')
                strength = rel.get('strength', 0.5)
                rel_type = rel.get('relation_type', 'related_to')
                
                relation_index[source].append({
                    'target': target,
                    'strength': strength,
                    'type': rel_type
                })
                # Bidirectional for symmetric relations
                if rel_type in ['synonym', 'similar_to', 'related_to']:
                    relation_index[target].append({
                        'target': source,
                        'strength': strength,
                        'type': rel_type
                    })
            
            # Add associations from concepts
            for word, concept in concepts.items():
                associations = concept.get('associations', [])
                for assoc in associations:
                    if assoc not in [r['target'] for r in relation_index[word]]:
                        relation_index[word].append({
                            'target': assoc,
                            'strength': 0.7,  # Default association strength
                            'type': 'association'
                        })
            
            data['_relation_index'] = dict(relation_index)
            data['_concepts_set'] = set(concepts.keys())
            
            num_concepts = len(concepts)
            num_relations = len(relations)
            print(f"  [OK] Loaded knowledge web: {num_concepts} concepts, {num_relations} relations")
            
            return data
        except Exception as e:
            print(f"  [!] Failed to load knowledge_web.json: {e}")
            return None
    
    def _load_context_memory(self) -> Optional[Dict[str, Any]]:
        """
        🧠 Load context memory from capsule for word-organism mappings.
        
        This provides the learned associations between words and organisms,
        giving each organism its characteristic "voice" and word preferences.
        """
        cm_path = self.export_dir / 'context_memory.json'
        if not cm_path.exists():
            print(f"  [!] No context_memory.json found - word-organism mappings disabled")
            return None
        
        try:
            with open(cm_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build reverse index: word -> organism_ids that use it
            language_anchors = data.get('language_anchors', {})
            node_word_associations = data.get('node_word_associations', {})
            word_frequencies = data.get('word_frequencies', {})
            organism_sequences = data.get('organism_sequences', {})
            
            # Build organism vocabulary: organism_id -> set of preferred words
            organism_vocab = {}
            for org_id, words in node_word_associations.items():
                organism_vocab[str(org_id)] = set(words)
            
            data['_organism_vocab'] = organism_vocab
            data['_word_frequencies'] = word_frequencies
            
            # Extract TF-IDF important words for boosting
            ml_analysis = data.get('ml_analysis', {})
            if ml_analysis:
                tfidf = ml_analysis.get('semantic_analysis', {}).get('tfidf_analysis', {})
                important_words = tfidf.get('top_important_words', [])
                # Build word -> score map for fast lookup
                data['_tfidf_scores'] = {item['word']: item['tfidf_score'] for item in important_words}
            else:
                data['_tfidf_scores'] = {}
            
            num_anchors = len(language_anchors)
            num_orgs = len(organism_vocab)
            total_assocs = sum(len(words) for words in organism_vocab.values())
            tfidf_count = len(data.get('_tfidf_scores', {}))
            print(f"  [OK] Loaded context memory: {num_anchors} language anchors, {num_orgs} organisms, {total_assocs} word associations, {tfidf_count} TF-IDF words")
            
            return data
        except Exception as e:
            print(f"  [!] Failed to load context_memory.json: {e}")
            return None
    
    def _get_tfidf_scores(self) -> Dict[str, float]:
        """Get TF-IDF importance scores for words."""
        if not self.context_memory:
            return {}
        return self.context_memory.get('_tfidf_scores', {})
    
    def _get_tfidf_important_words(self) -> List[str]:
        """Get top TF-IDF important words sorted by score."""
        scores = self._get_tfidf_scores()
        if not scores:
            return []
        # Sort by score descending and return just the words
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_words]
    
    def _load_causation_system(self) -> Optional[Dict[str, Any]]:
        """
        🔬 Load causation system (illumination engine) from capsule.
        
        This provides the full causal graph - events and their cause-effect
        relationships. Essential for understanding WHY organisms do things.
        """
        cs_path = self.export_dir / 'causation_system.json'
        if not cs_path.exists():
            print(f"  [!] No causation_system.json found - illumination engine disabled")
            return None
        
        try:
            with open(cs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build indices for fast causal queries
            events = data.get('events', {})
            causal_links = data.get('causal_links', [])
            
            # Build forward causation index: event_id -> list of effects it caused
            forward_causation = defaultdict(list)
            # Build backward causation index: event_id -> list of causes
            backward_causation = defaultdict(list)
            
            for link in causal_links:
                from_evt = link.get('from_event', '')
                to_evt = link.get('to_event', '')
                strength = link.get('strength', 0.5)
                explanation = link.get('explanation', '')
                
                forward_causation[from_evt].append({
                    'effect': to_evt,
                    'strength': strength,
                    'explanation': explanation
                })
                backward_causation[to_evt].append({
                    'cause': from_evt,
                    'strength': strength,
                    'explanation': explanation
                })
            
            data['_forward_causation'] = dict(forward_causation)
            data['_backward_causation'] = dict(backward_causation)
            data['_events_set'] = set(events.keys())
            
            num_events = len(events)
            num_links = len(causal_links)
            print(f"  [OK] Loaded causation system: {num_events} events, {num_links} causal links")
            
            return data
        except Exception as e:
            print(f"  [!] Failed to load causation_system.json: {e}")
            return None
    
    def explain_decision(self, event_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """
        🔬 Explain WHY a decision/event happened using the causation graph.
        
        This is the illumination engine query - trace back causes.
        """
        if not self.causation_system:
            return {'error': 'Causation system not loaded'}
        
        events = self.causation_system.get('events', {})
        backward = self.causation_system.get('_backward_causation', {})
        
        if event_id not in events:
            return {'error': f'Event {event_id} not found'}
        
        # Trace back through causes
        root_causes = []
        visited = set()
        
        def trace_causes(evt_id: str, path: List[str], depth: int):
            if depth > max_depth or evt_id in visited:
                return
            visited.add(evt_id)
            
            causes = backward.get(evt_id, [])
            if not causes:
                # This is a root cause
                if evt_id in events:
                    root_causes.append({
                        'event': events[evt_id],
                        'path': path + [evt_id],
                        'depth': len(path)
                    })
            else:
                for cause_info in causes:
                    trace_causes(cause_info['cause'], path + [evt_id], depth + 1)
        
        trace_causes(event_id, [], 0)
        
        return {
            'event': events.get(event_id, {}),
            'root_causes': root_causes[:10],
            'total_causes_found': len(root_causes)
        }
    
    def _load_alliance_system(self) -> Optional[Dict[str, Any]]:
        """
        🏛️ Load alliance system (civilization state) from capsule.
        
        This provides the social structure - alliances, reputations,
        confederations, wisdom rules, and collective histories.
        """
        as_path = self.export_dir / 'alliance_system.json'
        if not as_path.exists():
            print(f"  [!] No alliance_system.json found - social context disabled")
            return None
        
        try:
            with open(as_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build organism -> alliance mapping
            organism_to_alliance = {}
            for alliance_id, alliance in data.get('alliances', {}).items():
                for member_id in alliance.get('members', []):
                    organism_to_alliance[str(member_id)] = alliance_id
            
            data['_organism_to_alliance'] = organism_to_alliance
            
            # Extract all wisdom rules into flat list for easy access
            all_wisdom = []
            for history in data.get('histories', {}).values():
                all_wisdom.extend(history.get('wisdom_rules', []))
            data['_all_wisdom_rules'] = all_wisdom
            
            n_alliances = len(data.get('alliances', {}))
            n_wisdom = len(all_wisdom)
            print(f"  [OK] Loaded alliance system: {n_alliances} alliances, {n_wisdom} wisdom rules")
            
            return data
        except Exception as e:
            print(f"  [!] Failed to load alliance_system.json: {e}")
            return None
    
    def get_organism_alliance(self, organism_id: str) -> Optional[str]:
        """Get the alliance an organism belongs to."""
        if not self.alliance_system:
            return None
        return self.alliance_system.get('_organism_to_alliance', {}).get(str(organism_id))
    
    def get_organism_reputation(self, organism_id: str) -> Dict[str, float]:
        """Get reputation scores for an organism."""
        if not self.alliance_system:
            return {}
        return self.alliance_system.get('reputations', {}).get(str(organism_id), {})
    
    def get_wisdom_rules(self) -> List[str]:
        """Get all wisdom rules from alliance histories."""
        if not self.alliance_system:
            return []
        return self.alliance_system.get('_all_wisdom_rules', [])
    
    def _get_organism_preferred_words(self, organism_id: str) -> Set[str]:
        """Get words this organism prefers to use based on training."""
        if not self.context_memory:
            return set()
        
        organism_vocab = self.context_memory.get('_organism_vocab', {})
        return organism_vocab.get(str(organism_id), set())
    
    def _get_semantic_related(self, word: str, min_strength: float = 0.3) -> List[str]:
        """Get semantically related words from knowledge web."""
        if not self.knowledge_web:
            return []
        
        relation_index = self.knowledge_web.get('_relation_index', {})
        relations = relation_index.get(word.lower(), [])
        
        # Return words sorted by strength
        related = [(r['target'], r['strength']) for r in relations if r['strength'] >= min_strength]
        related.sort(key=lambda x: x[1], reverse=True)
        return [w for w, s in related[:10]]  # Top 10

    def _create_organisms(self) -> Dict[str, CapsuleOrganism]:
        """Create organism objects from metadata with FULL AtomicLanguageSystem."""
        organisms = {}
        
        # Try different metadata structures
        # Structure 1: ensemble.members (older format)
        # Structure 2: member_profiles (cocoon format)
        # Structure 3: brain_configs (minimal format)
        members = self.metadata.get('ensemble', {}).get('members', [])
        if not members:
            members = self.metadata.get('member_profiles', [])
        if not members:
            members = self.metadata.get('brain_configs', [])
        
        # Debug info
        config_lang = self.config.get('has_language_head', False) if self.config else False
        
        # 🧬 Load per-organism atomic language data
        atomic_data_map = self._load_atomic_language_data()
        
        for idx, member_data in enumerate(members):
            org_id = member_data.get('organism_id', f'org_{idx}')
            behavioral = member_data.get('behavioral_fingerprint', {})
            
            # Check multiple locations for language head flag
            member_has_lang = (
                member_data.get('has_language_head') or
                member_data.get('use_language_head') or
                config_lang
            )
            
            organism = CapsuleOrganism(
                organism_id=org_id,
                fitness=member_data.get('fitness', 1.0),
                personality=behavioral.get('personality_label', 'unknown'),
                behavioral_tendencies=behavioral.get('behavioral_tendencies', {}),
                input_dim=member_data.get('input_dim', 25),  # Default matches config.json
                output_dim=member_data.get('output_dim', 6),
                has_language_head=member_has_lang,
                brain_index=idx
            )
            
            # 🧬 Attach AtomicLanguageSystem if available
            if org_id in atomic_data_map:
                organism.atomic_language = atomic_data_map[org_id]
                print(f"    [OK] Loaded AtomicLanguageSystem for {org_id}: {len(organism.atomic_language.atoms)} atoms")
            elif idx < len(atomic_data_map):
                # Try by index if org_id doesn't match
                key = list(atomic_data_map.keys())[idx]
                organism.atomic_language = atomic_data_map[key]
                print(f"    [OK] Loaded AtomicLanguageSystem for {org_id} (via index {idx}): {len(organism.atomic_language.atoms)} atoms")
            
            organisms[org_id] = organism
        
        if organisms:
            loaded_count = sum(1 for o in organisms.values() if o.atomic_language is not None)
            print(f"  [OK] Created {len(organisms)} organisms ({loaded_count} with AtomicLanguageSystem)")
        else:
            print(f"  [!] No organisms found in metadata")
        
        return organisms
    
    def _load_atomic_language_data(self) -> Dict[str, Any]:
        """
        🧬 Load AtomicLanguageSystem instances from exported data.
        
        Tries multiple export formats:
        1. atomic_languages/ directory (per-organism JSON files)
        2. atomic_language.json (single file with all organisms)
        3. context_memory.json organism_sequences (fallback)
        """
        atomic_systems = {}
        
        # Try importing AtomicLanguageSystem
        try:
            from reality_simulator.language.atomic_language import AtomicLanguageSystem
        except ImportError:
            print("  [!] Cannot import AtomicLanguageSystem - atomic language features disabled")
            return {}
        
        # Method 1: Per-organism files in atomic_languages/ directory
        atomic_dir = self.export_dir / 'atomic_languages'
        if atomic_dir.exists():
            for json_file in atomic_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    org_id = data.get('organism_id', json_file.stem)
                    atomic_systems[org_id] = AtomicLanguageSystem.from_dict(data)
                except Exception as e:
                    print(f"  [!] Failed to load {json_file.name}: {e}")
            if atomic_systems:
                print(f"  [OK] Loaded {len(atomic_systems)} AtomicLanguageSystems from atomic_languages/")
                return atomic_systems
        
        # Method 2: Single atomic_language.json file
        atomic_file = self.export_dir / 'atomic_language.json'
        if atomic_file.exists():
            try:
                with open(atomic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if it's a single system or multiple
                if 'organism_id' in data:
                    # Single organism format
                    org_id = data['organism_id']
                    atomic_systems[org_id] = AtomicLanguageSystem.from_dict(data)
                    print(f"  [OK] Loaded AtomicLanguageSystem from atomic_language.json")
                elif 'organisms' in data:
                    # Multiple organisms format
                    for org_id, org_data in data['organisms'].items():
                        org_data['organism_id'] = org_id
                        atomic_systems[org_id] = AtomicLanguageSystem.from_dict(org_data)
                    print(f"  [OK] Loaded {len(atomic_systems)} AtomicLanguageSystems from atomic_language.json")
                elif isinstance(data, list):
                    # List format (indexed by position)
                    for idx, org_data in enumerate(data):
                        org_id = org_data.get('organism_id', f'org_{idx}')
                        atomic_systems[org_id] = AtomicLanguageSystem.from_dict(org_data)
                    print(f"  [OK] Loaded {len(atomic_systems)} AtomicLanguageSystems from atomic_language.json (list)")
                
                return atomic_systems
            except Exception as e:
                print(f"  [!] Failed to load atomic_language.json: {e}")
        
        # Method 3: Create fresh AtomicLanguageSystems (fallback)
        # They'll be empty but functional
        members = self.metadata.get('ensemble', {}).get('members', [])
        if not members:
            members = self.metadata.get('member_profiles', [])
        if not members:
            members = self.metadata.get('brain_configs', [])
        
        for idx, member_data in enumerate(members):
            org_id = member_data.get('organism_id', f'org_{idx}')
            atomic_systems[org_id] = AtomicLanguageSystem(organism_id=org_id)
        
        if atomic_systems:
            print(f"  [!] Created {len(atomic_systems)} fresh AtomicLanguageSystems (no export found)")
        
        return atomic_systems
        
        return organisms
    
    def _load_brain(self) -> Any:
        """Load neural network model from capsule."""
        # Try TorchScript first (multiple naming conventions)
        ts_paths = [
            self.export_dir / 'brain.torchscript',
            self.export_dir / 'brain_ensemble.pt',
            self.export_dir / 'brain.pt',
        ]
        
        for ts_path in ts_paths:
            if ts_path.exists() and TORCH_AVAILABLE:
                try:
                    model = torch.jit.load(str(ts_path), map_location='cpu')
                    model.eval()
                    print(f"  [OK] Loaded TorchScript model from {ts_path.name}")
                    return ('torchscript', model)
                except Exception as e:
                    print(f"  [!] TorchScript load failed for {ts_path.name}: {e}")
        
        # Try ONNX (multiple naming conventions)
        onnx_paths = [
            self.export_dir / 'brain.onnx',
            self.export_dir / 'brain_ensemble.onnx',
        ]
        
        for onnx_path in onnx_paths:
            if onnx_path.exists() and ONNX_AVAILABLE:
                try:
                    session = ort.InferenceSession(str(onnx_path))
                    print(f"  [OK] Loaded ONNX model from {onnx_path.name}")
                    return ('onnx', session)
                except Exception as e:
                    print(f"  [!] ONNX load failed for {onnx_path.name}: {e}")
        
        print(f"  [!] No neural model loaded - using fallback generation")
        return None
    
    def _infer_single(self, state: np.ndarray, organism_idx: int = 0) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Run inference on a single organism's brain.
        
        Returns: (action_probs, language_logits or None)
        """
        if self.brain is None:
            # Fallback: random action distribution
            return np.random.dirichlet(np.ones(6)), None
        
        brain_type, model = self.brain
        
        # Ensure state is correct shape
        state = np.asarray(state, dtype=np.float32).reshape(1, -1)
        
        if brain_type == 'torchscript' and TORCH_AVAILABLE:
            with torch.no_grad():
                state_tensor = torch.from_numpy(state)
                outputs = model(state_tensor)
                
                if isinstance(outputs, tuple):
                    # Ensemble model returns tuple of outputs
                    num_organisms = len(self.organisms)
                    if organism_idx < len(outputs):
                        action_out = outputs[organism_idx]
                    else:
                        action_out = outputs[0]
                    
                    # Check for language outputs (second half of tuple)
                    lang_out = None
                    lang_idx = num_organisms + organism_idx
                    if lang_idx < len(outputs):
                        lang_out = outputs[lang_idx].numpy()
                    
                    return action_out.numpy().flatten(), lang_out
                else:
                    return outputs.numpy().flatten(), None
        
        elif brain_type == 'onnx' and ONNX_AVAILABLE:
            input_name = model.get_inputs()[0].name
            outputs = model.run(None, {input_name: state})
            
            num_organisms = len(self.organisms)
            
            # ONNX ensemble outputs: [action_0, ..., action_n, language_0, ..., language_n]
            if len(outputs) > num_organisms:
                # Has language heads - outputs are split: actions first, then language
                action_out = outputs[organism_idx].flatten() if organism_idx < len(outputs) else outputs[0].flatten()
                lang_idx = num_organisms + organism_idx
                lang_out = outputs[lang_idx] if lang_idx < len(outputs) else None
                return action_out, lang_out
            elif len(outputs) > 1:
                # Multiple action outputs but no language heads
                action_out = outputs[organism_idx].flatten() if organism_idx < len(outputs) else outputs[0].flatten()
                return action_out, None
            else:
                return outputs[0].flatten(), None
        
        return np.random.dirichlet(np.ones(6)), None
    
    def _generate_tokens_neural(self, organism: CapsuleOrganism, 
                                 state: np.ndarray,
                                 max_length: int = 32,
                                 input_message: str = "") -> List[int]:
        """
        Generate tokens using neural language head with semantic guidance.
        
        Aligned with bridge.py's _generate_from_language_head() implementation.
        
        Key features:
        - Get base_logits ONCE from model, clone for each iteration
        - Tiered repetition penalty (strong for very recent tokens)
        - 🔮 Semantic priming from input message keywords
        - 🔮 Semantic boosting based on generated context
        """
        if self.brain is None or not organism.has_language_head:
            return []
        
        brain_type, model = self.brain
        generated_tokens = []
        recent_tokens = []  # Track last 8 tokens for repetition penalty
        
        # Generation parameters (aligned with bridge.py)
        strong_repetition_penalty = 3.0  # For very recent (last 2) tokens
        
        # 🔮 Extract semantic primes from input message
        input_semantic_primes = set()
        if self.knowledge_web and input_message:
            input_words = input_message.lower().split()
            for word in input_words:
                # Add direct match
                if word in self.knowledge_web.get('_concepts_set', set()):
                    input_semantic_primes.add(word)
                # Add related words
                related = self._get_semantic_related(word, min_strength=0.5)
                input_semantic_primes.update(related[:3])
        
        if brain_type == 'torchscript' and TORCH_AVAILABLE:
            with torch.no_grad():
                state_tensor = torch.from_numpy(state.astype(np.float32).reshape(1, -1))
                
                # ═══════════════════════════════════════════════════════════
                # GET BASE LOGITS ONCE - Don't re-run model each iteration!
                # The model gives us a probability distribution over vocab.
                # We sample from it repeatedly, NOT re-query for same state.
                # ═══════════════════════════════════════════════════════════
                outputs = model(state_tensor)
                
                # Get language logits (second half of ensemble outputs)
                base_logits = None
                if isinstance(outputs, tuple):
                    num_organisms = len(self.organisms)
                    lang_idx = num_organisms + organism.brain_index
                    if lang_idx < len(outputs):
                        base_logits = outputs[lang_idx].squeeze()
                
                if base_logits is None:
                    return []
                
                # ═══════════════════════════════════════════════════════════
                # 🔮 INITIAL SEMANTIC PRIMING - Boost words related to input
                # This helps the first tokens be contextually relevant
                # ═══════════════════════════════════════════════════════════
                if input_semantic_primes:
                    initial_boost = 0.8  # Stronger initial priming
                    for prime_word in input_semantic_primes:
                        prime_token = self.vocabulary.word_to_id.get(prime_word.lower())
                        if prime_token is not None and prime_token < len(base_logits):
                            base_logits[prime_token] += initial_boost
                
                # ═══════════════════════════════════════════════════════════
                # SAMPLING LOOP - Clone base logits each time, apply penalties
                # ═══════════════════════════════════════════════════════════
                for step in range(max_length):
                    # Start with fresh copy of base logits
                    logits = base_logits.clone()
                    
                    # Apply temperature
                    logits = logits / self.temperature
                    
                    # ═══════════════════════════════════════════════════════
                    # TIERED REPETITION PENALTY (aligned with bridge.py)
                    # ═══════════════════════════════════════════════════════
                    if recent_tokens:
                        for i, prev_token in enumerate(recent_tokens):
                            recency = len(recent_tokens) - i
                            if prev_token < len(logits):
                                if recency <= 2:
                                    # Very recent: strong penalty
                                    logits[prev_token] -= strong_repetition_penalty
                                else:
                                    # Less recent: moderate penalty
                                    logits[prev_token] -= self.repetition_penalty
                    
                    # ═══════════════════════════════════════════════════════
                    # 🔮 SEMANTIC BOOSTING FROM KNOWLEDGE WEB
                    # This is what makes generation coherent - boost words
                    # that are semantically related to recently generated ones
                    # ═══════════════════════════════════════════════════════
                    if self.knowledge_web and generated_tokens:
                        # Get last generated word
                        last_token = generated_tokens[-1]
                        last_word = self.vocabulary.id_to_word.get(last_token, '')
                        
                        if last_word:
                            # Get semantically related words
                            related_words = self._get_semantic_related(last_word, min_strength=0.3)
                            
                            # Boost logits for related words
                            semantic_boost = 0.5  # Configurable boost strength
                            for related_word in related_words[:5]:  # Top 5 related
                                related_token = self.vocabulary.word_to_id.get(related_word.lower())
                                if related_token is not None and related_token < len(logits):
                                    # Only boost if not recently used (avoid semantic loops)
                                    if related_token not in recent_tokens:
                                        logits[related_token] += semantic_boost
                    
                    # ═══════════════════════════════════════════════════════
                    # 🧠 ORGANISM-SPECIFIC WORD PREFERENCE BOOSTING
                    # Each organism has learned word preferences from training.
                    # This gives them their unique "voice" and vocabulary.
                    # ═══════════════════════════════════════════════════════
                    if self.context_memory:
                        preferred_words = self._get_organism_preferred_words(organism.organism_id)
                        if preferred_words:
                            preference_boost = 0.3  # Subtle but consistent
                            for pref_word in preferred_words:
                                pref_token = self.vocabulary.word_to_id.get(pref_word.lower())
                                if pref_token is not None and pref_token < len(logits):
                                    # Only boost if not recently used
                                    if pref_token not in recent_tokens:
                                        logits[pref_token] += preference_boost
                    
                    # ═══════════════════════════════════════════════════════
                    # 📊 TF-IDF IMPORTANT WORD BOOSTING
                    # Words identified as semantically important by TF-IDF analysis
                    # get a subtle boost to make responses more meaningful.
                    # ═══════════════════════════════════════════════════════
                    tfidf_important = self._get_tfidf_important_words()
                    if tfidf_important:
                        tfidf_boost = 0.25  # Subtle - don't overpower other signals
                        for important_word in tfidf_important[:20]:  # Top 20
                            imp_token = self.vocabulary.word_to_id.get(important_word.lower())
                            if imp_token is not None and imp_token < len(logits):
                                # Only boost if not recently used
                                if imp_token not in recent_tokens:
                                    logits[imp_token] += tfidf_boost
                    
                    # ═══════════════════════════════════════════════════════
                    # 🧬 ATOMIC LANGUAGE TRAIT-DRIVEN WORD SELECTION
                    # Use organism's AtomicLanguageSystem for trait-modulated
                    # word selection based on curiosity, aggression, social_affinity
                    # ═══════════════════════════════════════════════════════
                    if organism.atomic_language is not None:
                        # Get traits from behavioral_tendencies or defaults
                        traits = organism.behavioral_tendencies
                        curiosity = traits.get('curiosity', 0.5)
                        aggression = traits.get('aggression', 0.3)
                        social_affinity = traits.get('cooperation', traits.get('social_affinity', 0.5))
                        
                        # Get last word for context
                        query_word = None
                        if generated_tokens:
                            last_token = generated_tokens[-1]
                            query_word = self.vocabulary.id_to_word.get(last_token)
                        
                        # Query atomic vocabulary with traits
                        if hasattr(organism.atomic_language, 'query_vocabulary'):
                            try:
                                atomic_words = organism.atomic_language.query_vocabulary(
                                    query_word=query_word,
                                    organism_state=state.flatten() if len(state.shape) > 1 else state,
                                    curiosity=curiosity,
                                    aggression=aggression,
                                    social_affinity=social_affinity,
                                    top_k=10
                                )
                                
                                # Boost atomic vocabulary words
                                atomic_boost = 0.6  # Strong - atomic language is core to organism identity
                                for atomic_word, score in atomic_words:
                                    atomic_token = self.vocabulary.word_to_id.get(atomic_word.lower())
                                    if atomic_token is not None and atomic_token < len(logits):
                                        if atomic_token not in recent_tokens:
                                            logits[atomic_token] += atomic_boost * score
                            except Exception:
                                pass  # Silent fail - atomic query is enhancement not requirement
                    
                    # CRITICAL FIX: Check if vocab has real words beyond special tokens
                    # Special tokens are: <PAD>=0, <UNK>=1, <START>=2, <END>=3, <VP_GATE>=4
                    non_special_count = self.vocabulary.vocab_size - 5  # 5 special tokens
                    if non_special_count <= 0:
                        # No real words to sample - return empty
                        break
                    
                    # Mask special tokens (0-4)
                    logits[:5] = float('-inf')
                    
                    # Mask out-of-vocabulary tokens
                    if self.vocabulary.vocab_size < len(logits):
                        logits[self.vocabulary.vocab_size:] = float('-inf')
                    
                    # Top-k sampling for quality
                    if self.top_k > 0 and self.top_k < len(logits):
                        top_k_vals, top_k_idx = torch.topk(logits, self.top_k)
                        mask = torch.full_like(logits, float('-inf'))
                        mask.scatter_(0, top_k_idx, top_k_vals)
                        logits = mask
                    
                    # Sample from distribution
                    probs = torch.softmax(logits, dim=-1)
                    
                    # SAFEGUARD: Check for NaN/Inf/zero probabilities before multinomial
                    # Use .item() to convert tensor booleans to Python booleans
                    probs_valid = torch.isfinite(probs).all().item() and probs.sum().item() > 0
                    if not probs_valid:
                        probs = torch.ones_like(probs) / max(1, len(probs))
                    
                    try:
                        token_id = torch.multinomial(probs, 1).item()
                    except (RuntimeError, AssertionError):
                        # Fallback to random valid token
                        token_id = random.randint(5, min(self.vocabulary.vocab_size - 1, len(probs) - 1))
                    
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
                    
                    if len(generated_tokens) >= max_length:
                        break
        
        # ═══════════════════════════════════════════════════════════════
        # ONNX MODEL SUPPORT - Different path for ONNX inference
        # ONNX ensemble outputs: [action_0, action_1, ..., language_0, language_1, ...]
        # ═══════════════════════════════════════════════════════════════
        elif brain_type == 'onnx' and ONNX_AVAILABLE:
            input_name = model.get_inputs()[0].name
            outputs = model.run(None, {input_name: state.astype(np.float32).reshape(1, -1)})
            
            # Get language logits for this organism (second half of outputs)
            num_organisms = len(self.organisms)
            lang_idx = num_organisms + organism.brain_index
            
            if lang_idx >= len(outputs):
                return []  # No language output for this organism
            
            # Convert to numpy array and squeeze
            base_logits_np = np.array(outputs[lang_idx]).squeeze()
            
            if len(base_logits_np.shape) == 0:
                return []  # Scalar output, not language logits
            
            # ═══════════════════════════════════════════════════════════
            # 🔮 INITIAL SEMANTIC PRIMING - Boost words related to input
            # ═══════════════════════════════════════════════════════════
            if input_semantic_primes:
                initial_boost = 0.8
                for prime_word in input_semantic_primes:
                    prime_token = self.vocabulary.word_to_id.get(prime_word.lower())
                    if prime_token is not None and prime_token < len(base_logits_np):
                        base_logits_np[prime_token] += initial_boost
            
            # ═══════════════════════════════════════════════════════════
            # SAMPLING LOOP - NumPy-based for ONNX
            # ═══════════════════════════════════════════════════════════
            for step in range(max_length):
                # Start with fresh copy
                logits = base_logits_np.copy()
                
                # Apply temperature
                logits = logits / self.temperature
                
                # Tiered repetition penalty
                if recent_tokens:
                    for i, prev_token in enumerate(recent_tokens):
                        recency = len(recent_tokens) - i
                        if prev_token < len(logits):
                            if recency <= 2:
                                logits[prev_token] -= strong_repetition_penalty
                            else:
                                logits[prev_token] -= self.repetition_penalty
                
                # 🔮 Semantic boosting
                if self.knowledge_web and generated_tokens:
                    last_token = generated_tokens[-1]
                    last_word = self.vocabulary.id_to_word.get(last_token, '')
                    if last_word:
                        related_words = self._get_semantic_related(last_word, min_strength=0.3)
                        for related_word in related_words[:5]:
                            related_token = self.vocabulary.word_to_id.get(related_word.lower())
                            if related_token is not None and related_token < len(logits):
                                if related_token not in recent_tokens:
                                    logits[related_token] += 0.5
                
                # 🧠 Organism preference boosting
                if self.context_memory:
                    preferred_words = self._get_organism_preferred_words(organism.organism_id)
                    if preferred_words:
                        for pref_word in preferred_words:
                            pref_token = self.vocabulary.word_to_id.get(pref_word.lower())
                            if pref_token is not None and pref_token < len(logits):
                                if pref_token not in recent_tokens:
                                    logits[pref_token] += 0.3
                
                # 📊 TF-IDF boosting
                tfidf_important = self._get_tfidf_important_words()
                if tfidf_important:
                    for important_word in tfidf_important[:20]:
                        imp_token = self.vocabulary.word_to_id.get(important_word.lower())
                        if imp_token is not None and imp_token < len(logits):
                            if imp_token not in recent_tokens:
                                logits[imp_token] += 0.25
                
                # 🧬 ATOMIC LANGUAGE TRAIT-DRIVEN WORD SELECTION (ONNX path)
                if organism.atomic_language is not None:
                    traits = organism.behavioral_tendencies
                    curiosity = traits.get('curiosity', 0.5)
                    aggression = traits.get('aggression', 0.3)
                    social_affinity = traits.get('cooperation', traits.get('social_affinity', 0.5))
                    
                    query_word = None
                    if generated_tokens:
                        last_token = generated_tokens[-1]
                        query_word = self.vocabulary.id_to_word.get(last_token)
                    
                    if hasattr(organism.atomic_language, 'query_vocabulary'):
                        try:
                            atomic_words = organism.atomic_language.query_vocabulary(
                                query_word=query_word,
                                organism_state=state.flatten() if len(state.shape) > 1 else state,
                                curiosity=curiosity,
                                aggression=aggression,
                                social_affinity=social_affinity,
                                top_k=10
                            )
                            
                            atomic_boost = 0.6
                            for atomic_word, score in atomic_words:
                                atomic_token = self.vocabulary.word_to_id.get(atomic_word.lower())
                                if atomic_token is not None and atomic_token < len(logits):
                                    if atomic_token not in recent_tokens:
                                        logits[atomic_token] += atomic_boost * score
                        except Exception:
                            pass
                
                # Mask special tokens (0-4)
                logits[:5] = float('-inf')
                
                # Mask out-of-vocabulary tokens
                if self.vocabulary.vocab_size < len(logits):
                    logits[self.vocabulary.vocab_size:] = float('-inf')
                
                # Top-k sampling with numpy
                if self.top_k > 0 and self.top_k < len(logits):
                    top_k_indices = np.argpartition(logits, -self.top_k)[-self.top_k:]
                    mask = np.full_like(logits, float('-inf'))
                    mask[top_k_indices] = logits[top_k_indices]
                    logits = mask
                
                # Softmax and sample
                logits_max = np.max(logits[logits > float('-inf')]) if np.any(logits > float('-inf')) else 0
                exp_logits = np.exp(logits - logits_max)
                exp_logits[logits == float('-inf')] = 0
                probs = exp_logits / (exp_logits.sum() + 1e-10)
                
                # Sample token
                token_id = np.random.choice(len(probs), p=probs)
                
                # Stop at END token
                if token_id == self.vocabulary.SPECIAL_TOKENS.get('<END>', 3):
                    break
                if token_id < 5:
                    continue
                
                generated_tokens.append(token_id)
                
                recent_tokens.append(token_id)
                if len(recent_tokens) > 8:
                    recent_tokens.pop(0)
                
                if len(generated_tokens) >= max_length:
                    break
        
        return generated_tokens
    
    def _generate_fallback_response(self, organism: CapsuleOrganism, 
                                     message: str, action: int) -> str:
        """
        Fallback response generation based on personality, action, AND message content.
        
        Used when neural generation fails or produces low-quality output.
        Enhanced to be more contextual and conversational.
        """
        action_name = self.ACTION_NAMES[action] if action < len(self.ACTION_NAMES) else 'act'
        personality = organism.personality.lower()
        words = message.lower().split()
        
        # ═══════════════════════════════════════════════════════════════
        # Message-aware context detection
        # ═══════════════════════════════════════════════════════════════
        is_greeting = any(w in words for w in ['hello', 'hi', 'hey', 'greetings'])
        is_question = '?' in message or any(w in words for w in ['what', 'how', 'why', 'when', 'where', 'who'])
        is_about_self = any(w in words for w in ['you', 'your', 'yourself'])
        is_philosophical = any(w in words for w in ['life', 'meaning', 'purpose', 'existence', 'consciousness'])
        
        # Greeting responses by personality
        if is_greeting:
            greetings = {
                'altruist': "Greetings, friend. How may I assist you today?",
                'hermit': "Hello... I was lost in thought. What brings you here?",
                'aggressor': "Greetings. I sense you seek something. Speak.",
                'pacifist': "Peace be with you. Welcome to this space of calm."
            }
            return greetings.get(personality, "Hello there.")
        
        # Question responses - more thoughtful
        if is_question:
            if is_about_self:
                about_self = {
                    'altruist': f"I am drawn to help and connect. Your question about me - I exist to serve the collective good.",
                    'hermit': f"Who am I? A wanderer of inner landscapes, seeking truth in solitude.",
                    'aggressor': f"I am strength and determination manifest. I do not hesitate when action is needed.",
                    'pacifist': f"I am a seeker of harmony, moving through existence with gentle purpose."
                }
                return about_self.get(personality, "I am a neural organism, exploring language and thought.")
            elif is_philosophical:
                philosophical = {
                    'altruist': "Life finds meaning through connection - in helping others, we discover ourselves.",
                    'hermit': "Existence is a quiet mystery, best understood through deep contemplation.",
                    'aggressor': "Purpose is forged through challenge. Without struggle, there is no growth.",
                    'pacifist': "Meaning emerges in stillness. The universe whispers its truths to those who listen."
                }
                return philosophical.get(personality, "A profound question. Let me reflect on this.")
            else:
                # Generic thoughtful question response
                question_responses = {
                    'altruist': f"An interesting question. Let me consider how this might help us all...",
                    'hermit': f"Your question stirs contemplation. The answer lies in careful reflection.",
                    'aggressor': f"Direct questions deserve direct answers. Let me address this head-on.",
                    'pacifist': f"That's a thoughtful inquiry. Let me find the harmonious perspective."
                }
                return question_responses.get(personality, "Let me consider that.")
        
        # Action-personality matrix (original behavior but enhanced)
        responses = {
            'altruist': {
                'cooperate': "Working together creates something greater than any of us alone.",
                'move': "Moving toward those who need support.",
                'rest': "Even helpers need rest to maintain their strength.",
                'compete': "In fair competition, everyone grows stronger.",
                'reproduce': "Sharing knowledge with new minds enriches us all.",
                'isolate': "Taking time to reflect on how best to serve."
            },
            'hermit': {
                'cooperate': "In quiet collaboration, unexpected wisdom emerges.",
                'move': "Following the winding path of inner exploration.",
                'rest': "Deep rest opens doorways to understanding.",
                'compete': "The true competition is with oneself.",
                'reproduce': "Ideas multiply in the silence of contemplation.",
                'isolate': "Solitude is where I find my deepest truths."
            },
            'aggressor': {
                'cooperate': "Strong alliances forge stronger outcomes.",
                'move': "Advancing purposefully toward the goal.",
                'rest': "Gathering strength for the next challenge.",
                'compete': "Through competition, excellence is forged.",
                'reproduce': "Strength must be passed to future generations.",
                'isolate': "Planning the next decisive action."
            },
            'pacifist': {
                'cooperate': "Cooperation weaves the fabric of peace.",
                'move': "Moving gently, leaving no trace of conflict.",
                'rest': "In stillness, harmony naturally arises.",
                'compete': "Even competition can be conducted with grace.",
                'reproduce': "New life brings new hope for a peaceful world.",
                'isolate': "Peaceful reflection on the interconnected whole."
            }
        }
        
        personality_responses = responses.get(personality, responses['pacifist'])
        return personality_responses.get(action_name, f"Choosing to {action_name} in this moment.")
    
    def _select_organisms(self, 
                          strategy: RoutingStrategy,
                          max_organisms: Optional[int] = None) -> Dict[str, CapsuleOrganism]:
        """
        Select organisms based on routing strategy.
        
        Aligned with ButterflyChatRouter._select_organisms().
        """
        if not self.organisms:
            return {}
        
        organisms_list = list(self.organisms.values())
        
        if strategy == RoutingStrategy.ALL:
            selected = organisms_list
        
        elif strategy == RoutingStrategy.RANDOM:
            count = max_organisms or max(1, len(organisms_list) // 2)
            selected = random.sample(organisms_list, min(count, len(organisms_list)))
        
        elif strategy == RoutingStrategy.FITTEST:
            sorted_orgs = sorted(organisms_list, key=lambda x: x.fitness, reverse=True)
            count = max_organisms or max(1, len(organisms_list) // 3)
            selected = sorted_orgs[:count]
        
        elif strategy == RoutingStrategy.CONNECTED:
            # Without network state, fall back to fittest
            sorted_orgs = sorted(organisms_list, key=lambda x: x.fitness, reverse=True)
            count = max_organisms or max(1, len(organisms_list) // 3)
            selected = sorted_orgs[:count]
        
        else:  # BY_WORD or default
            selected = organisms_list
        
        if max_organisms and len(selected) > max_organisms:
            selected = selected[:max_organisms]
        
        return {org.organism_id: org for org in selected}
    
    def _aggregate_responses(self, responses: List[OrganismResponse]) -> str:
        """
        Aggregate organism responses into final response.
        
        Aligned with ButterflyChatRouter._aggregate_responses().
        """
        if not responses:
            return ""
        
        # Filter empty responses
        valid_responses = [r for r in responses if r.response.strip()]
        if not valid_responses:
            return ""
        
        if self.voting_strategy == VotingStrategy.SINGLE:
            return valid_responses[0].response
        
        elif self.voting_strategy == VotingStrategy.FITTEST_TOP_K:
            sorted_resp = sorted(valid_responses, key=lambda r: r.fitness, reverse=True)
            return sorted_resp[0].response
        
        elif self.voting_strategy == VotingStrategy.FITNESS_WEIGHTED:
            # Weight by fitness, select highest weighted
            total_weight = sum(r.fitness * r.confidence for r in valid_responses)
            if total_weight == 0:
                return valid_responses[0].response
            
            best = max(valid_responses, key=lambda r: r.fitness * r.confidence)
            return best.response
        
        elif self.voting_strategy == VotingStrategy.MAJORITY:
            # Most common response (or part of it)
            from collections import Counter
            response_counts = Counter(r.response for r in valid_responses)
            return response_counts.most_common(1)[0][0]
        
        else:
            # Default: fitness-weighted
            best = max(valid_responses, key=lambda r: r.fitness * r.confidence)
            return best.response
    
    def _calculate_confidence(self, tokens: List[int], organism: CapsuleOrganism) -> float:
        """Calculate response confidence - aligned with live butterfly_chat.py."""
        if not tokens:
            return 0.1
        
        # Base confidence from token count and fitness
        length_score = min(len(tokens) / 10.0, 1.0)
        fitness_score = min(organism.fitness / 5.0, 1.0)
        
        # Penalty for repetition
        unique_tokens = len(set(tokens))
        diversity_score = unique_tokens / max(len(tokens), 1)
        
        return (length_score * 0.3 + fitness_score * 0.4 + diversity_score * 0.3)
    
    def _calculate_semantic_reward(self,
                                     user_message: str,
                                     user_tokens: List[int],
                                     organism_response: str,
                                     organism_tokens: List[int],
                                     confidence: float) -> float:
        """
        Calculate reward with SEMANTIC AWARENESS - aligned with live butterfly_chat.py.
        
        Components:
        1. Word overlap: Relevance to user message (0.0-0.25)
        2. Coherence: Structural quality indicators (0.0-0.25)
        3. Length appropriateness: Neither too short nor too long (0.0-0.2)
        4. Confidence scaling: Model confidence adjustment (0.0-0.2)
        """
        try:
            # Base reward for generating any response
            reward = 0.3
            
            # Handle empty response
            if not organism_response or len(organism_response.strip()) == 0:
                return -0.1  # Penalty for empty responses
            
            # Normalize text
            user_words = set(user_message.lower().split())
            response_words = organism_response.lower().split()
            response_words_set = set(response_words)
            
            # 1. WORD OVERLAP SCORE (0.0 - 0.25)
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who',
                         'this', 'that', 'to', 'of', 'in', 'for', 'on', 'with', 'at'}
            
            user_content = user_words - stopwords
            response_content = response_words_set - stopwords
            
            if user_content and response_content:
                overlap = len(user_content & response_content)
                max_possible = min(len(user_content), len(response_content))
                overlap_score = (overlap / max_possible) * 0.25 if max_possible > 0 else 0.0
            else:
                overlap_score = 0.1
            
            reward += overlap_score
            
            # 2. COHERENCE SCORE (0.0 - 0.25)
            coherence_score = 0.0
            
            if organism_response[0].isupper():
                coherence_score += 0.05
            
            if organism_response.rstrip()[-1:] in '.!?':
                coherence_score += 0.05
            
            if organism_response.strip().lower() == user_message.strip().lower():
                coherence_score -= 0.1  # Penalty for echoing
            
            unique_ratio = 1.0
            if len(response_words) > 1:
                unique_ratio = len(response_words_set) / len(response_words)
                coherence_score += unique_ratio * 0.15
                if unique_ratio < 0.5:
                    coherence_score -= (1.0 - unique_ratio) * 0.3  # Repetition penalty
            
            if len(response_words) >= 2:
                coherence_score += 0.05
            
            reward += max(0.0, coherence_score)
            
            # 3. LENGTH APPROPRIATENESS (0.0 - 0.2)
            response_length = len(response_words)
            if response_length == 0:
                length_score = 0.0
            elif response_length <= 2:
                length_score = 0.05
            elif response_length <= 10:
                length_score = 0.2
            elif response_length <= 20:
                length_score = 0.15
            else:
                length_score = 0.1
            
            reward += length_score
            
            # 4. CONFIDENCE SCALING (0.0 - 0.2)
            reward += confidence * 0.2
            
            # Allow negative for severe repetition
            if len(response_words) > 1 and unique_ratio < 0.3:
                final_reward = max(-0.3, min(1.0, reward))
            elif len(response_words) > 1 and unique_ratio < 0.5:
                final_reward = max(0.0, min(1.0, reward))
            else:
                final_reward = max(0.05, min(1.0, reward))
            
            return final_reward
            
        except Exception:
            return 0.3  # Safe fallback
    
    def _get_adaptive_max_length(self, organism: CapsuleOrganism) -> int:
        """
        Calculate adaptive max response length based on organism experience.
        
        Aligned with live butterfly_chat.py logic:
        - experience < 10: short responses (6-8 tokens)
        - experience < 50: medium (12-24 tokens)
        - experience < 100: longer (32-64 tokens)
        - experience >= 100: full length (128 tokens)
        """
        experience_count = len(organism.experience_buffer)
        vocab_size = self.vocabulary.vocab_size
        
        if experience_count < 10:
            return min(8, max(5, vocab_size // 6))
        elif experience_count < 50:
            return min(24, max(12, vocab_size // 4))
        elif experience_count < 100:
            return min(64, max(32, vocab_size // 2))
        else:
            return 128  # Full neural synapse length
    
    def _train_from_chat(self, organism: CapsuleOrganism, network_state: Optional[Dict] = None) -> Optional[float]:
        """
        Optional: Train neural network on chat experiences.
        
        Aligned with live butterfly_chat.py trainer integration.
        Only runs if trainer was provided during initialization (requires PyTorch).
        
        Returns:
            Training loss if trainer available, None otherwise
        """
        if not self.trainer:
            return None
        
        try:
            # Use trainer's chat training method if available
            if hasattr(self.trainer, 'train_from_chat_experiences'):
                loss = self.trainer.train_from_chat_experiences(organism, network_state)
                self.debug_logs.append({
                    'step': 'TRAIN',
                    'action': f'Neural training for {organism.organism_id}',
                    'data': {'loss': loss, 'method': 'train_from_chat_experiences'}
                })
                return loss
            elif hasattr(self.trainer, 'train_step'):
                # Fallback to generic train_step
                loss = self.trainer.train_step([organism], network_state or {})
                self.debug_logs.append({
                    'step': 'TRAIN',
                    'action': f'Neural training for {organism.organism_id}',
                    'data': {'loss': loss, 'method': 'train_step'}
                })
                return loss
        except Exception as e:
            self.debug_logs.append({
                'step': 'TRAIN_ERROR',
                'action': f'Training failed for {organism.organism_id}',
                'data': {'error': str(e)}
            })
        return None
    
    def _maybe_trigger_training(self, organism: CapsuleOrganism, network_state: Optional[Dict] = None):
        """
        Trigger training periodically based on experience count.
        
        Aligned with live butterfly_chat.py: trains every 10 experiences.
        """
        if not self.trainer:
            return
        
        experience_count = len(organism.experience_buffer)
        if experience_count > 0 and experience_count % 10 == 0:
            self._train_from_chat(organism, network_state)
    
    def _build_state_vector(self, message: str) -> np.ndarray:
        """
        Build a state vector from the message context.
        
        Aligned with the neural system's expected input format (config.json neural.brain.input_dim).
        Extra dims are for self-perception: oscillation_entropy, coherence_frequency.
        """
        # Get config-driven input_dim
        try:
            from runtime_config import get_input_dim
            input_dim = get_input_dim()
        except Exception:
            input_dim = 30  # Default matches current config.json
        
        state = np.zeros(input_dim, dtype=np.float32)
        
        # Basic state encoding from message
        words = message.lower().split()
        
        # Feature 0-5: Word presence indicators for action words
        action_words = {'move': 0, 'cooperate': 1, 'compete': 2, 'rest': 3, 'reproduce': 4, 'isolate': 5}
        for word in words:
            if word in action_words:
                state[action_words[word]] = 1.0
        
        # Feature 6: Energy proxy (message length normalized)
        state[6] = min(len(words) / 20.0, 1.0)
        
        # Feature 7: Message complexity (unique words ratio)
        state[7] = len(set(words)) / max(len(words), 1)
        
        # Feature 8-10: Sentiment proxies
        positive_words = {'good', 'great', 'happy', 'love', 'help', 'together', 'peace'}
        negative_words = {'bad', 'hate', 'fight', 'alone', 'fear', 'danger'}
        neutral_words = {'what', 'how', 'why', 'when', 'where', 'is', 'are'}
        
        state[8] = sum(1 for w in words if w in positive_words) / max(len(words), 1)
        state[9] = sum(1 for w in words if w in negative_words) / max(len(words), 1)
        state[10] = sum(1 for w in words if w in neutral_words) / max(len(words), 1)
        
        # Feature 11-15: Conversation context
        state[11] = min(self.total_messages / 100.0, 1.0)  # Conversation progress
        state[12] = len(self.conversation_history) / 50.0  # History depth
        
        # Feature 16-23: Reserved for neural features / padding
        state[16] = 0.5  # Default VP value (stable)
        state[17] = len(self.organisms) / 20.0  # Network density proxy
        
        # Feature 24: Illumination level (matches neural_organism.py state features)
        state[24] = 0.5  # Default illumination level for standalone mode
        
        return state
    
    def route_message(self,
                      message: str,
                      routing_strategy: str = "fittest",
                      max_organisms: Optional[int] = None) -> ChatResult:
        """
        Route message to organisms and aggregate responses.
        
        Aligned with ButterflyChatRouter.route_message() interface.
        """
        start_time = time.time()
        self.debug_logs = []
        
        strategy = RoutingStrategy(routing_strategy)
        
        # Log step 1: Message received
        self.debug_logs.append({
            'step': 'STEP_1',
            'action': 'Message Received',
            'data': {
                'message': message,
                'routing_strategy': routing_strategy,
                'max_organisms': max_organisms,
                'vocabulary_size': self.vocabulary.vocab_size,
                'organisms_count': len(self.organisms)
            }
        })
        
        # Tokenize message
        words = message.lower().split()
        tokens = self.vocabulary.encode(words, add_special=True)
        
        self.debug_logs.append({
            'step': 'STEP_2',
            'action': 'Tokenization',
            'data': {'words': words, 'tokens': tokens}
        })
        
        # Build state vector
        state = self._build_state_vector(message)
        
        # Select organisms
        selected = self._select_organisms(strategy, max_organisms)
        
        self.debug_logs.append({
            'step': 'STEP_3',
            'action': 'Organism Selection',
            'data': {
                'strategy': routing_strategy,
                'selected_count': len(selected),
                'selected_ids': list(selected.keys())
            }
        })
        
        # Generate responses from each organism
        organism_responses: List[OrganismResponse] = []
        
        for org_id, organism in selected.items():
            org_start = time.time()
            
            try:
                # Get action from neural network
                action_probs, lang_logits = self._infer_single(state, organism.brain_index)
                action = int(np.argmax(action_probs))
                
                # Generate tokens if language head available
                if organism.has_language_head and self.brain is not None:
                    # Use adaptive max length based on organism experience
                    adaptive_length = self._get_adaptive_max_length(organism)
                    response_tokens = self._generate_tokens_neural(
                        organism, state, 
                        max_length=adaptive_length,
                        input_message=message
                    )
                    
                    self.debug_logs.append({
                        'step': 'STEP_4',
                        'action': f'Adaptive length for {org_id}',
                        'data': {
                            'experience_count': len(organism.experience_buffer),
                            'adaptive_max_length': adaptive_length
                        }
                    })
                else:
                    response_tokens = []
                
                # Decode tokens to text
                if response_tokens:
                    response_words = self.vocabulary.decode(response_tokens, skip_special=True)
                    response_text = ' '.join(response_words)
                    
                    # Log quality metrics (but don't fall back - neural output is what we want)
                    unique_tokens = len(set(response_tokens))
                    diversity_ratio = unique_tokens / max(len(response_tokens), 1)
                    
                    self.debug_logs.append({
                        'step': 'QUALITY_CHECK',
                        'action': f'Token diversity for {org_id}',
                        'data': {
                            'diversity_ratio': diversity_ratio,
                            'unique_tokens': unique_tokens,
                            'total_tokens': len(response_tokens),
                            'has_knowledge_web': self.knowledge_web is not None
                        }
                    })
                else:
                    # Empty response - organism couldn't generate (learning phase)
                    response_text = ""
                
                confidence = self._calculate_confidence(response_tokens, organism)
                
                # Calculate semantic reward (for quality tracking)
                semantic_reward = self._calculate_semantic_reward(
                    user_message=message,
                    user_tokens=tokens,
                    organism_response=response_text,
                    organism_tokens=response_tokens,
                    confidence=confidence
                )
                
                # Store experience for adaptive growth
                organism.experience_buffer.append({
                    'input': message,
                    'response': response_text,
                    'reward': semantic_reward,
                    'timestamp': time.time()
                })
                
                # 🎰 TOKEN TUMBLER: Generate tokens for chat interactions
                # This links conversation quality to language model token sequences
                chat_action = min(5, max(0, int(semantic_reward * 5)))  # 0-5 based on reward
                organism.tumble_action_tokens(
                    action=chat_action,
                    reward=semantic_reward,
                    context='chat_response'
                )
                
                # Optional: trigger neural training periodically
                self._maybe_trigger_training(organism, None)
                
                self.debug_logs.append({
                    'step': 'REWARD_CALC',
                    'action': f'Semantic reward for {org_id}',
                    'data': {
                        'semantic_reward': semantic_reward,
                        'confidence': confidence,
                        'experience_count': len(organism.experience_buffer)
                    }
                })
                
                organism_responses.append(OrganismResponse(
                    organism_id=org_id,
                    response=response_text,
                    tokens=response_tokens,
                    fitness=organism.fitness,
                    confidence=confidence,
                    personality=organism.personality
                ))
                
                self.debug_logs.append({
                    'step': 'STEP_4',
                    'action': f'Response from {org_id}',
                    'data': {
                        'organism_id': org_id,
                        'response': response_text[:50],
                        'token_count': len(response_tokens),
                        'confidence': confidence,
                        'fitness': organism.fitness,
                        'generation_time_ms': (time.time() - org_start) * 1000
                    }
                })
                
            except Exception as e:
                self.debug_logs.append({
                    'step': 'ERROR',
                    'action': f'Generation failed for {org_id}',
                    'data': {'error': str(e)}
                })
        
        # Aggregate responses
        final_response = self._aggregate_responses(organism_responses)
        
        self.debug_logs.append({
            'step': 'STEP_5',
            'action': 'Response Aggregation',
            'data': {
                'voting_strategy': self.voting_strategy.value,
                'response_count': len(organism_responses),
                'final_response': final_response[:100]
            }
        })
        
        # Track conversation
        self.total_messages += 1
        self.conversation_history.append({
            'timestamp': time.time(),
            'user_message': message,
            'routing_strategy': routing_strategy,
            'organism_responses': [r.__dict__ for r in organism_responses],
            'aggregated_response': final_response
        })
        
        total_time = (time.time() - start_time) * 1000
        
        return ChatResult(
            response=final_response,
            organism_responses=organism_responses,
            tokens_used=tokens,
            routing_info={
                'strategy': routing_strategy,
                'organisms_queried': len(selected),
                'organisms_responded': len(organism_responses)
            },
            debug_logs=self.debug_logs,
            performance={
                'total_time_ms': total_time,
                'avg_response_time_ms': total_time / max(len(organism_responses), 1)
            }
        )
    
    def chat(self, message: str, strategy: str = 'fittest') -> str:
        """
        Simple chat interface - returns just the response string.
        
        For full details, use route_message() instead.
        """
        result = self.route_message(message, routing_strategy=strategy)
        return result.response
    
    def get_organism_info(self) -> List[Dict[str, Any]]:
        """Get information about all organisms in the ensemble."""
        return [
            {
                'id': org.organism_id,
                'fitness': org.fitness,
                'personality': org.personality,
                'tendencies': org.behavioral_tendencies,
                'has_language_head': org.has_language_head
            }
            for org in self.organisms.values()
        ]
    
    def interactive(self):
        """
        Interactive chat mode with commands.
        
        Commands:
            /strategy <name>  - Change routing strategy
            /organisms        - List organisms
            /debug            - Show last debug logs
            /history          - Show conversation history
            /help             - Show commands
            /quit             - Exit
        """
        print("\n" + "="*60)
        print("  🦋 BUTTERFLY CHAT - Neural Organism Communication")
        print("="*60)
        print(f"  Loaded {len(self.organisms)} organisms from capsule")
        print(f"  Vocabulary: {self.vocabulary.vocab_size} words")
        print(f"  Model: {self.brain[0] if self.brain else 'fallback'}")
        print(f"  Strategy: {self.voting_strategy.value}")
        print("="*60)
        print("  Commands: /strategy, /organisms, /debug, /history, /help, /quit")
        print("="*60 + "\n")
        
        current_strategy = 'fittest'
        
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                print("\n  Goodbye! 🦋\n")
                break
            
            elif user_input.lower() == '/help':
                print("\n  Commands:")
                print("    /strategy <all|random|fittest>  - Change routing")
                print("    /voting <fitness_weighted|majority|single>  - Change voting")
                print("    /organisms  - List ensemble members")
                print("    /debug      - Show last debug logs")
                print("    /history    - Show conversation history")
                print("    /quit       - Exit")
                print()
                continue
            
            elif user_input.lower().startswith('/strategy'):
                parts = user_input.split()
                if len(parts) > 1:
                    new_strategy = parts[1].lower()
                    if new_strategy in ['all', 'random', 'fittest', 'connected']:
                        current_strategy = new_strategy
                        print(f"  Strategy changed to: {current_strategy}")
                    else:
                        print(f"  Unknown strategy. Use: all, random, fittest, connected")
                else:
                    print(f"  Current strategy: {current_strategy}")
                continue
            
            elif user_input.lower().startswith('/voting'):
                parts = user_input.split()
                if len(parts) > 1:
                    try:
                        self.voting_strategy = VotingStrategy(parts[1].lower())
                        print(f"  Voting strategy changed to: {self.voting_strategy.value}")
                    except ValueError:
                        print(f"  Unknown voting strategy. Use: single, majority, fitness_weighted")
                else:
                    print(f"  Current voting: {self.voting_strategy.value}")
                continue
            
            elif user_input.lower() == '/organisms':
                print("\n  Ensemble Members:")
                print("-" * 50)
                for org in sorted(self.organisms.values(), key=lambda x: x.fitness, reverse=True):
                    lang = "🗣️" if org.has_language_head else "  "
                    print(f"  {lang} {org.organism_id[:16]}  fitness={org.fitness:.3f}  {org.personality}")
                print("-" * 50 + "\n")
                continue
            
            elif user_input.lower() == '/debug':
                print("\n  Last Debug Logs:")
                print("-" * 50)
                for log in self.debug_logs[-10:]:
                    print(f"  [{log['step']}] {log['action']}")
                print("-" * 50 + "\n")
                continue
            
            elif user_input.lower() == '/history':
                print(f"\n  Conversation History ({len(self.conversation_history)} messages):")
                print("-" * 50)
                for entry in self.conversation_history[-5:]:
                    print(f"  User: {entry['user_message'][:40]}...")
                    print(f"  Bot:  {entry['aggregated_response'][:40]}...")
                    print()
                print("-" * 50 + "\n")
                continue
            
            # Regular chat message
            result = self.route_message(user_input, routing_strategy=current_strategy)
            
            # Display response with metadata
            print(f"\n🦋 {result.response}")
            print(f"   [{len(result.organism_responses)} organisms, {result.performance['total_time_ms']:.0f}ms]")
            print()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='🦋 Standalone Butterfly Chat - Neural Organism Communication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standalone_butterfly_chat.py agent_downloads/16swarm
  python standalone_butterfly_chat.py agent_downloads/16swarm --strategy all
  python standalone_butterfly_chat.py agent_downloads/16swarm --voting majority
        """
    )
    parser.add_argument('export_dir', help='Path to exported agent directory')
    parser.add_argument('--strategy', '-s', default='fittest',
                        choices=['all', 'random', 'fittest', 'connected'],
                        help='Routing strategy (default: fittest)')
    parser.add_argument('--voting', '-v', default='fitness_weighted',
                        choices=['single', 'majority', 'fitness_weighted', 'softmax_ensemble'],
                        help='Voting strategy for response aggregation')
    parser.add_argument('--message', '-m', help='Single message mode (non-interactive)')
    
    args = parser.parse_args()
    
    print('🦋 Initializing Standalone Butterfly Chat...')
    
    try:
        chat_system = StandaloneButterflyChat(args.export_dir, voting_strategy=args.voting)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    if args.message:
        # Single message mode
        response = chat_system.chat(args.message, strategy=args.strategy)
        print(f"\n🦋 {response}\n")
    else:
        # Interactive mode
        chat_system.interactive()


if __name__ == '__main__':
    main()
