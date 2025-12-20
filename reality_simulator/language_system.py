"""
Language System for Butterfly Ecosystem

Provides vocabulary management, tokenization, and language primitives
for the neural language model integration.

This module bridges the existing language_anchors structure in ContextMemory
with the neural network's language modeling capabilities.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Special tokens for sequence modeling
SPECIAL_TOKENS = {
    '<PAD>': 0,      # Padding token for batch processing
    '<UNK>': 1,      # Unknown token for OOV words
    '<START>': 2,    # Sequence start marker
    '<END>': 3,      # Sequence end marker
    '<VP_GATE>': 4,  # VP-gated token (high violation pressure marker)
}

# Reverse mapping for decoding
SPECIAL_TOKEN_IDS = {v: k for k, v in SPECIAL_TOKENS.items()}


@dataclass
class LanguageVocabulary:
    """
    Vocabulary management for the organism language system.
    
    Builds and maintains word-to-id and id-to-word mappings from
    the existing language_anchors structure in ContextMemory.
    
    Key Design Decisions:
    - Deterministic ordering: Words are sorted before ID assignment
      to ensure consistent vocabulary across simulation restarts.
    - Special tokens: Reserved IDs 0-4 for control tokens (NEVER evicted).
    - Extensible: New words can be added during runtime.
    - Rolling vocabulary: When full, least-recently-used words are evicted
      to make room for new learning. The system keeps evolving.
    - Serializable: Can persist to/from JSON for checkpoint/restore.
    
    Attributes:
        word_to_id: Mapping from word strings to integer IDs
        id_to_word: Mapping from integer IDs to word strings
        word_frequencies: Count of how often each word appears
        word_last_used: Timestamp of last use for each word (for LRU eviction)
        max_vocab_size: Maximum vocabulary size (default 1000)
        frozen: If True, no new words can be added
    """
    
    word_to_id: Dict[str, int] = field(default_factory=dict)
    id_to_word: Dict[int, str] = field(default_factory=dict)
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    word_last_used: Dict[str, float] = field(default_factory=dict)  # LRU tracking
    max_vocab_size: int = 10000  # Organism max vocab (mastery level 4 cap)
    frozen: bool = False
    event_emitter: Any = None  # Optional callback for causation events
    
    def __post_init__(self):
        """Initialize with special tokens if empty."""
        if not self.word_to_id:
            self._initialize_special_tokens()
    
    def _initialize_special_tokens(self):
        """Set up special token mappings."""
        self.word_to_id = dict(SPECIAL_TOKENS)
        self.id_to_word = dict(SPECIAL_TOKEN_IDS)
        now = time.time()
        for token in SPECIAL_TOKENS:
            self.word_frequencies[token] = 0
            self.word_last_used[token] = float('inf')  # Special tokens NEVER get evicted
    
    @property
    def vocab_size(self) -> int:
        """Current vocabulary size including special tokens."""
        return len(self.word_to_id)
    
    @property
    def num_special_tokens(self) -> int:
        """Number of special tokens."""
        return len(SPECIAL_TOKENS)
    
    def build_from_language_anchors(
        self,
        language_anchors: Dict[str, Set[str]],
        node_word_associations: Optional[Dict[str, Set[str]]] = None
    ) -> int:
        """
        Build vocabulary from existing language_anchors structure.
        
        This method extracts all unique words from the language_anchors
        and node_word_associations dictionaries in ContextMemory.
        
        CRITICAL: Words are sorted before ID assignment to ensure
        deterministic ordering across simulation restarts.
        
        Args:
            language_anchors: Dict mapping word -> set of organism_ids
            node_word_associations: Optional dict mapping node_id -> set of words
            
        Returns:
            Number of new words added to vocabulary
        """
        # Collect all unique words
        all_words: Set[str] = set()
        
        # Extract from language_anchors (word -> organisms)
        if language_anchors:
            all_words.update(language_anchors.keys())
            # Update frequencies based on number of organisms using each word
            for word, organism_ids in language_anchors.items():
                self.word_frequencies[word] = self.word_frequencies.get(word, 0) + len(organism_ids)
        
        # Extract from node_word_associations (node -> words)
        if node_word_associations:
            for node_id, words in node_word_associations.items():
                all_words.update(words)
                for word in words:
                    self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
        
        # CRITICAL FIX: Sort by FREQUENCY (descending) then alphabetically for determinism
        # This prevents "A-word bias" where alphabetically-first words like "aalto", "aardvark"
        # get lowest token IDs and dominate neural network output (which tends to sample low IDs)
        # Now: most-used words get lowest IDs = more relevant output
        sorted_words = sorted(
            all_words,
            key=lambda w: (
                -self.word_frequencies.get(w, 0),  # Primary: highest frequency first (negative for descending)
                w  # Secondary: alphabetical for determinism when frequencies equal
            )
        )
        
        # Add words to vocabulary
        words_added = 0
        next_id = len(self.word_to_id)
        now = time.time()
        
        for word in sorted_words:
            if word not in self.word_to_id:
                if self.frozen:
                    logger.warning(f"Vocabulary frozen, cannot add word: {word}")
                    continue
                if next_id >= self.max_vocab_size:
                    logger.warning(f"Vocabulary full ({self.max_vocab_size}), cannot add: {word}")
                    break
                    
                self.word_to_id[word] = next_id
                self.id_to_word[next_id] = word
                self.word_last_used[word] = now  # Track for LRU eviction
                next_id += 1
                words_added += 1
        
        logger.info(f"Built vocabulary: {words_added} new words, {self.vocab_size} total")
        return words_added
    
    def add_word(self, word: str) -> int:
        """
        Add a single word to the vocabulary.
        
        If vocabulary is full, evicts least-recently-used words to make room.
        The system keeps evolving - there is no hard ceiling.
        
        Args:
            word: Word to add
            
        Returns:
            ID of the word (existing or newly assigned)
        """
        now = time.time()
        
        if word in self.word_to_id:
            self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
            self.word_last_used[word] = now  # Update LRU timestamp
            return self.word_to_id[word]
        
        if self.frozen:
            logger.debug(f"Vocabulary frozen, returning <UNK> for: {word}")
            return SPECIAL_TOKENS['<UNK>']
        
        # If at capacity, evict least-recently-used word to make room
        if self.vocab_size >= self.max_vocab_size:
            evicted = self._evict_lru_word()
            if not evicted:
                # Could not evict (shouldn't happen unless all are special tokens)
                logger.warning(f"Could not evict any words, returning <UNK> for: {word}")
                return SPECIAL_TOKENS['<UNK>']
        
        new_id = len(self.word_to_id)
        self.word_to_id[word] = new_id
        self.id_to_word[new_id] = word
        self.word_frequencies[word] = 1
        self.word_last_used[word] = now
        
        # Only emit vocabulary_growth event for milestone sizes (quality over quantity)
        # Match neural training event frequency - only significant vocabulary growth
        if hasattr(self, 'event_emitter') and self.event_emitter:
            # Much less frequent - only emit at major vocabulary milestones (every 50 words)
            if self.vocab_size % 50 == 0:
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='language',
                        event_type='vocabulary_growth',
                        data={
                            'word': word,
                            'word_id': new_id,
                            'vocab_size': self.vocab_size,
                            'word_frequency': 1,
                            'milestone': True  # Indicates this is a milestone event
                        }
                    )
                    self.event_emitter(event)
                except ImportError:
                    pass  # CausationExplorer not available
        
        return new_id
    
    def _evict_lru_word(self) -> Optional[str]:
        """
        Evict the least-recently-used word to make room for new learning.
        
        Special tokens (IDs 0-4) are NEVER evicted.
        
        Returns:
            The evicted word, or None if nothing could be evicted
        """
        # Find the word with oldest last_used timestamp (excluding special tokens)
        oldest_word = None
        oldest_time = float('inf')
        
        for word, last_used in self.word_last_used.items():
            # Skip special tokens
            if word in SPECIAL_TOKENS:
                continue
            if last_used < oldest_time:
                oldest_time = last_used
                oldest_word = word
        
        if oldest_word is None:
            return None
        
        # Get the ID before removal
        evicted_id = self.word_to_id[oldest_word]
        evicted_freq = self.word_frequencies.get(oldest_word, 0)
        
        # Remove from all mappings
        del self.word_to_id[oldest_word]
        del self.id_to_word[evicted_id]
        del self.word_frequencies[oldest_word]
        del self.word_last_used[oldest_word]
        
        # Emit eviction event for observability
        if hasattr(self, 'event_emitter') and self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='language',
                    event_type='vocabulary_eviction',
                    data={
                        'evicted_word': oldest_word,
                        'evicted_id': evicted_id,
                        'frequency_at_eviction': evicted_freq,
                        'time_since_last_use': time.time() - oldest_time,
                        'vocab_size': self.vocab_size
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass
        
        logger.debug(f"Evicted '{oldest_word}' (freq={evicted_freq}, unused for {time.time() - oldest_time:.1f}s)")
        return oldest_word
    
    def touch_word(self, word: str):
        """
        Update the last-used timestamp for a word without adding it.
        Call this when a word is accessed/used.
        """
        if word in self.word_last_used:
            self.word_last_used[word] = time.time()
            self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1

    def get_id(self, word: str, touch: bool = True) -> int:
        """
        Get the ID for a word, returning <UNK> if not found.
        
        Optionally updates last-used timestamp to keep word alive.
        
        Args:
            word: Word to look up
            touch: If True, update last-used timestamp (default True)
            
        Returns:
            Integer ID for the word
        """
        if word in self.word_to_id:
            if touch:
                self.touch_word(word)
            return self.word_to_id[word]
        return SPECIAL_TOKENS['<UNK>']
    
    def get_token_id(self, word: str) -> int:
        """
        Alias for get_id() for backward compatibility.
        
        Args:
            word: Word to look up
            
        Returns:
            Integer ID for the word
        """
        return self.get_id(word)
    
    def get_word(self, token_id: int, touch: bool = True) -> str:
        """
        Get the word for an ID, returning <UNK> if not found.
        
        Optionally updates last-used timestamp to keep word alive.
        
        Args:
            token_id: ID to look up
            touch: If True, update last-used timestamp (default True)
            
        Returns:
            Word string for the ID
        """
        word = self.id_to_word.get(token_id, '<UNK>')
        if touch and word != '<UNK>' and word in self.word_last_used:
            self.touch_word(word)
        return word
    
    def encode(self, words: List[str], add_special: bool = True) -> List[int]:
        """
        Encode a list of words to token IDs.
        
        Args:
            words: List of words to encode
            add_special: If True, add <START> and <END> tokens
            
        Returns:
            List of integer token IDs
        """
        token_ids = []
        
        if add_special:
            token_ids.append(SPECIAL_TOKENS['<START>'])
        
        for word in words:
            token_ids.append(self.get_id(word))
        
        if add_special:
            token_ids.append(SPECIAL_TOKENS['<END>'])
        
        return token_ids
    
    def decode(self, token_ids: List[int], skip_special: bool = True) -> List[str]:
        """
        Decode a list of token IDs to words.
        
        Args:
            token_ids: List of integer IDs to decode
            skip_special: If True, omit special tokens from output
            
        Returns:
            List of word strings
        """
        words = []
        special_ids = set(SPECIAL_TOKENS.values()) if skip_special else set()
        
        for token_id in token_ids:
            if token_id in special_ids:
                continue
            word = self.get_word(token_id)
            # Only add non-UNK words, or UNK if we want to show them
            # For now, skip UNK to avoid empty responses
            if word != '<UNK>':
                words.append(word)
        
        return words
    
    def pad_sequence(self, token_ids: List[int], max_length: int) -> List[int]:
        """
        Pad or truncate a sequence to a fixed length.
        
        Args:
            token_ids: Sequence to pad
            max_length: Target length
            
        Returns:
            Padded/truncated sequence
        """
        if len(token_ids) >= max_length:
            return token_ids[:max_length]
        
        padding = [SPECIAL_TOKENS['<PAD>']] * (max_length - len(token_ids))
        return token_ids + padding
    
    def freeze(self):
        """Freeze vocabulary - no new words can be added."""
        self.frozen = True
        logger.info(f"Vocabulary frozen at size {self.vocab_size}")
    
    def unfreeze(self):
        """Unfreeze vocabulary - allow new words."""
        self.frozen = False
        logger.info("Vocabulary unfrozen")
    
    def get_most_frequent(self, n: int = 100) -> List[Tuple[str, int]]:
        """
        Get the n most frequent words.
        
        Args:
            n: Number of words to return
            
        Returns:
            List of (word, frequency) tuples, sorted by frequency descending
        """
        # Exclude special tokens
        word_freqs = [
            (word, freq) for word, freq in self.word_frequencies.items()
            if word not in SPECIAL_TOKENS
        ]
        return sorted(word_freqs, key=lambda x: x[1], reverse=True)[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize vocabulary to dictionary for JSON storage."""
        return {
            'word_to_id': self.word_to_id,
            'id_to_word': {str(k): v for k, v in self.id_to_word.items()},  # JSON keys must be strings
            'word_frequencies': self.word_frequencies,
            'max_vocab_size': self.max_vocab_size,
            'frozen': self.frozen,
            'version': '1.0'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LanguageVocabulary':
        """Deserialize vocabulary from dictionary."""
        vocab = cls(
            word_to_id=data.get('word_to_id', {}),
            id_to_word={int(k): v for k, v in data.get('id_to_word', {}).items()},
            word_frequencies=data.get('word_frequencies', {}),
            max_vocab_size=data.get('max_vocab_size', 10000),
            frozen=data.get('frozen', False)
        )
        
        # Ensure special tokens are present
        for token, token_id in SPECIAL_TOKENS.items():
            if token not in vocab.word_to_id:
                vocab.word_to_id[token] = token_id
                vocab.id_to_word[token_id] = token
        
        return vocab
    
    def save(self, filepath: Path):
        """Save vocabulary to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved vocabulary ({self.vocab_size} words) to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path) -> 'LanguageVocabulary':
        """Load vocabulary from JSON file."""
        filepath = Path(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vocab = cls.from_dict(data)
        logger.info(f"Loaded vocabulary ({vocab.vocab_size} words) from {filepath}")
        return vocab
    
    # ===================== CREATIVE EXPRESSION SYSTEM =====================
    # Based on Grok-4's vocabulary creative expression design
    # Enables multi-token combinations and vocabulary expansion
    
    def get_creative_tokens(self, seed_tokens: List[int], creativity_level: float = 0.5) -> List[int]:
        """
        Generate creative token combinations for expression.
        
        Based on Grok-4's creative expression design:
        - creativity_level < 0.3: Use common word combinations
        - creativity_level 0.3-0.7: Mix common and experimental
        - creativity_level > 0.7: More experimental combinations
        
        Args:
            seed_tokens: Starting tokens for creative generation
            creativity_level: 0.0 = conservative, 1.0 = experimental
            
        Returns:
            List of tokens forming a creative expression
        """
        import random
        
        if not seed_tokens:
            return []
        
        # Get word associations for seed tokens
        seed_words = []
        for token in seed_tokens:
            word = self.id_to_word.get(token)
            if word and word not in SPECIAL_TOKEN_IDS.values():
                seed_words.append(word)
        
        if not seed_words:
            return seed_tokens
        
        # Build word association map from frequencies
        # Higher frequency words are more "related" in the vocabulary
        high_freq_words = self.get_most_frequent(50)
        freq_tokens = [self.word_to_id[w] for w, _ in high_freq_words if w in self.word_to_id]
        
        # Generate creative combination
        result_tokens = []
        
        if creativity_level < 0.3:
            # Conservative: use seed + common words
            result_tokens.extend(seed_tokens[:2])
            if freq_tokens:
                result_tokens.append(random.choice(freq_tokens))
        
        elif creativity_level < 0.7:
            # Mixed: seed + some variation
            result_tokens.append(random.choice(seed_tokens))
            if freq_tokens and len(freq_tokens) > 2:
                # Pick 2 different common words
                choices = random.sample(freq_tokens[:20], min(2, len(freq_tokens)))
                result_tokens.extend(choices)
        
        else:
            # Experimental: more random combinations
            all_tokens = list(self.id_to_word.keys())
            valid_tokens = [t for t in all_tokens if t >= 5]  # Skip special tokens
            
            if valid_tokens:
                result_tokens.append(random.choice(seed_tokens))
                # Add 2-3 random tokens for experimentation
                num_random = random.randint(2, 3)
                for _ in range(num_random):
                    result_tokens.append(random.choice(valid_tokens))
        
        return result_tokens
    
    def expand_vocabulary_from_pattern(self, pattern_tokens: List[int], 
                                        success_reward: float) -> bool:
        """
        Reinforce vocabulary based on successful multi-token patterns.
        
        When organisms create successful multi-token expressions (high reward),
        this boosts the frequency of individual words in the pattern.
        
        NOTE: No longer creates compound tokens (e.g., "hello_there") as these
        cause "sharp edges" in output. Learning happens through frequency
        reinforcement of individual words.
        
        Args:
            pattern_tokens: Token sequence that was successful
            success_reward: Reward received (higher = more successful)
            
        Returns:
            True if vocabulary was reinforced
        """
        # Only reinforce for highly successful patterns
        if success_reward < 0.7:
            return False
        
        if len(pattern_tokens) < 2:
            return False
        
        if self.frozen:
            return False
        
        # Decode pattern to words
        pattern_words = []
        for token in pattern_tokens[:4]:  # Max 4 words
            word = self.id_to_word.get(token)
            if word and word not in SPECIAL_TOKEN_IDS.values():
                pattern_words.append(word)
        
        if len(pattern_words) < 2:
            return False
        
        # Reinforce individual words instead of creating compounds
        # This preserves learning without polluting vocabulary with underscore-joined tokens
        reinforced = False
        for word in pattern_words:
            if word in self.word_to_id:
                boost = int(success_reward * 3) + 1
                self.word_frequencies[word] = self.word_frequencies.get(word, 0) + boost
                reinforced = True
        
        if reinforced:
            logger.debug(f"[VOCAB] Pattern reinforced: {pattern_words} (reward={success_reward:.2f})")
        
        return reinforced
    
    def get_phrase_suggestions(self, context_tokens: List[int], 
                               num_suggestions: int = 3) -> List[List[int]]:
        """
        Suggest multi-token phrases based on context.
        
        Implements Grok-4's phrase-based expression system.
        
        Args:
            context_tokens: Current context tokens
            num_suggestions: Number of phrase suggestions to return
            
        Returns:
            List of suggested token sequences (each is a phrase)
        """
        import random
        
        suggestions = []
        
        # Get context words for semantic matching
        context_words = set()
        for token in context_tokens:
            word = self.id_to_word.get(token, '')
            if word and word not in SPECIAL_TOKEN_IDS.values():
                context_words.add(word.lower())
        
        # Look for compound words that relate to context
        compound_matches = []
        for word, word_id in self.word_to_id.items():
            if '_' in word:  # Compound word
                parts = word.split('_')
                if any(part.lower() in context_words for part in parts):
                    compound_matches.append(word_id)
        
        # Suggest compound matches first
        for compound_id in compound_matches[:num_suggestions]:
            suggestions.append([compound_id])
        
        # Fill remaining with frequent word combinations
        if len(suggestions) < num_suggestions:
            frequent = self.get_most_frequent(30)
            freq_ids = [self.word_to_id[w] for w, _ in frequent if w in self.word_to_id]
            
            while len(suggestions) < num_suggestions and len(freq_ids) >= 2:
                # Create random 2-3 word phrase from frequent words
                phrase_len = random.randint(2, 3)
                phrase = random.sample(freq_ids, min(phrase_len, len(freq_ids)))
                if phrase not in suggestions:
                    suggestions.append(phrase)
        
        return suggestions


class CharacterTokenizer:
    """
    Simple character-level tokenizer.
    
    Useful for tokenizing organism communication patterns
    without requiring external dependencies.
    """
    
    def __init__(self, vocab: Optional[LanguageVocabulary] = None):
        """
        Initialize tokenizer.
        
        Args:
            vocab: Optional vocabulary to use. If None, creates new one.
        """
        self.vocab = vocab or LanguageVocabulary()
    
    def tokenize(self, text: str) -> List[str]:
        """
        Split text into character tokens.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of character tokens
        """
        return list(text)
    
    def encode(self, text: str, add_special: bool = True) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Text to encode
            add_special: If True, add <START> and <END> tokens
            
        Returns:
            List of integer token IDs
        """
        chars = self.tokenize(text)
        
        # Add characters to vocabulary if needed
        for char in chars:
            self.vocab.add_word(char)
        
        return self.vocab.encode(chars, add_special=add_special)
    
    def decode(self, token_ids: List[int], skip_special: bool = True) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of integer IDs
            skip_special: If True, omit special tokens
            
        Returns:
            Decoded text string
        """
        chars = self.vocab.decode(token_ids, skip_special=skip_special)
        return ''.join(chars)


class ActionSequenceTokenizer:
    """
    Tokenizer for organism action sequences.
    
    Converts action indices and patterns into token sequences
    suitable for next-token prediction training.
    """
    
    # Action type prefixes for semantic differentiation
    ACTION_PREFIX = 'ACT_'
    RESOURCE_PREFIX = 'RES_'
    CONNECTION_PREFIX = 'CON_'
    STATE_PREFIX = 'STA_'
    
    def __init__(self, vocab: Optional[LanguageVocabulary] = None):
        """
        Initialize action tokenizer.
        
        Args:
            vocab: Optional vocabulary to use. If None, creates new one.
        """
        self.vocab = vocab or LanguageVocabulary()
        self._initialize_action_tokens()
    
    def _initialize_action_tokens(self):
        """Add base action tokens to vocabulary."""
        # Standard action tokens (matching OrganismBrain output_dim=6)
        # Canonical order: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
        action_tokens = [
            f'{self.ACTION_PREFIX}MOVE',      # Action 0
            f'{self.ACTION_PREFIX}COOPERATE', # Action 1
            f'{self.ACTION_PREFIX}COMPETE',   # Action 2
            f'{self.ACTION_PREFIX}REST',      # Action 3
            f'{self.ACTION_PREFIX}REPRODUCE', # Action 4
            f'{self.ACTION_PREFIX}ISOLATE',   # Action 5
        ]
        
        for token in action_tokens:
            self.vocab.add_word(token)
    
    def action_to_token(self, action_idx: int) -> str:
        """Convert action index to token string."""
        # Canonical order: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
        action_names = ['MOVE', 'COOPERATE', 'COMPETE', 'REST', 'REPRODUCE', 'ISOLATE']
        if 0 <= action_idx < len(action_names):
            return f'{self.ACTION_PREFIX}{action_names[action_idx]}'
        return f'{self.ACTION_PREFIX}UNKNOWN'
    
    def encode_actions(self, action_indices: List[int], add_special: bool = True) -> List[int]:
        """
        Encode a sequence of action indices to token IDs.
        
        Args:
            action_indices: List of action indices (0-5)
            add_special: If True, add <START> and <END> tokens
            
        Returns:
            List of token IDs
        """
        tokens = [self.action_to_token(idx) for idx in action_indices]
        return self.vocab.encode(tokens, add_special=add_special)
    
    def encode_communication_pattern(
        self,
        actions: List[int],
        resource_changes: Optional[List[float]] = None,
        connection_events: Optional[List[str]] = None
    ) -> List[int]:
        """
        Encode a full communication pattern including actions,
        resource changes, and connection events.
        
        Args:
            actions: List of action indices
            resource_changes: Optional list of resource deltas
            connection_events: Optional list of connection event types
            
        Returns:
            List of token IDs representing the pattern
        """
        tokens = []
        
        # Add START token
        tokens.append(SPECIAL_TOKENS['<START>'])
        
        # Encode actions
        for action_idx in actions:
            token = self.action_to_token(action_idx)
            tokens.append(self.vocab.get_id(token))
        
        # Encode resource changes if provided
        if resource_changes:
            for delta in resource_changes:
                if delta > 0.5:
                    res_token = f'{self.RESOURCE_PREFIX}GAIN'
                elif delta < -0.5:
                    res_token = f'{self.RESOURCE_PREFIX}LOSS'
                else:
                    res_token = f'{self.RESOURCE_PREFIX}STABLE'
                self.vocab.add_word(res_token)
                tokens.append(self.vocab.get_id(res_token))
        
        # Encode connection events if provided
        if connection_events:
            for event in connection_events:
                con_token = f'{self.CONNECTION_PREFIX}{event.upper()}'
                self.vocab.add_word(con_token)
                tokens.append(self.vocab.get_id(con_token))
        
        # Add END token
        tokens.append(SPECIAL_TOKENS['<END>'])
        
        return tokens


# Convenience function for creating a vocabulary from ContextMemory
def create_vocabulary_from_context_memory(context_memory) -> LanguageVocabulary:
    """
    Create a LanguageVocabulary from an existing ContextMemory instance.
    
    Args:
        context_memory: ContextMemory instance with language_anchors
        
    Returns:
        Initialized LanguageVocabulary
    """
    vocab = LanguageVocabulary()
    
    # Get language_anchors from context memory
    language_anchors = getattr(context_memory, 'language_anchors', {})
    node_word_associations = getattr(context_memory, 'node_word_associations', {})
    
    # Build vocabulary
    vocab.build_from_language_anchors(
        language_anchors=language_anchors,
        node_word_associations=node_word_associations
    )
    
    return vocab
