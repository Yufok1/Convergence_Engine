"""
Language System for Butterfly Ecosystem

Provides vocabulary management, tokenization, and language primitives
for the neural language model integration.

This module bridges the existing language_anchors structure in ContextMemory
with the neural network's language modeling capabilities.
"""

import json
import logging
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
    - Special tokens: Reserved IDs 0-4 for control tokens.
    - Extensible: New words can be added during runtime.
    - Serializable: Can persist to/from JSON for checkpoint/restore.
    
    Attributes:
        word_to_id: Mapping from word strings to integer IDs
        id_to_word: Mapping from integer IDs to word strings
        word_frequencies: Count of how often each word appears
        max_vocab_size: Maximum vocabulary size (default 32768 - balanced for CPU performance)
        frozen: If True, no new words can be added
    """
    
    word_to_id: Dict[str, int] = field(default_factory=dict)
    id_to_word: Dict[int, str] = field(default_factory=dict)
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    max_vocab_size: int = 12288
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
        for token in SPECIAL_TOKENS:
            self.word_frequencies[token] = 0
    
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
        
        # CRITICAL: Sort for deterministic ordering
        sorted_words = sorted(all_words)
        
        # Add words to vocabulary
        words_added = 0
        next_id = len(self.word_to_id)
        
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
                next_id += 1
                words_added += 1
        
        logger.info(f"Built vocabulary: {words_added} new words, {self.vocab_size} total")
        return words_added
    
    def add_word(self, word: str) -> int:
        """
        Add a single word to the vocabulary.
        
        Args:
            word: Word to add
            
        Returns:
            ID of the word (existing or newly assigned)
        """
        if word in self.word_to_id:
            self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
            return self.word_to_id[word]
        
        if self.frozen:
            logger.debug(f"Vocabulary frozen, returning <UNK> for: {word}")
            return SPECIAL_TOKENS['<UNK>']
        
        if self.vocab_size >= self.max_vocab_size:
            logger.debug(f"Vocabulary full, returning <UNK> for: {word}")
            return SPECIAL_TOKENS['<UNK>']
        
        new_id = len(self.word_to_id)
        self.word_to_id[word] = new_id
        self.id_to_word[new_id] = word
        self.word_frequencies[word] = 1
        
        # Only emit vocabulary_growth event for milestone sizes (quality over quantity)
        # Match neural training event frequency - only significant vocabulary growth
        if hasattr(self, 'event_emitter') and self.event_emitter:
            # Much less frequent - only emit at major vocabulary milestones (every 50 words)
            if self.vocab_size % 50 == 0:
                try:
                    import time
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
    
    def get_id(self, word: str) -> int:
        """
        Get the ID for a word, returning <UNK> if not found.
        
        Args:
            word: Word to look up
            
        Returns:
            Integer ID for the word
        """
        return self.word_to_id.get(word, SPECIAL_TOKENS['<UNK>'])
    
    def get_token_id(self, word: str) -> int:
        """
        Alias for get_id() for backward compatibility.
        
        Args:
            word: Word to look up
            
        Returns:
            Integer ID for the word
        """
        return self.get_id(word)
    
    def get_word(self, token_id: int) -> str:
        """
        Get the word for an ID, returning <UNK> if not found.
        
        Args:
            token_id: ID to look up
            
        Returns:
            Word string for the ID
        """
        return self.id_to_word.get(token_id, '<UNK>')
    
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
        action_tokens = [
            f'{self.ACTION_PREFIX}REST',      # Action 0
            f'{self.ACTION_PREFIX}MOVE',      # Action 1
            f'{self.ACTION_PREFIX}EAT',       # Action 2
            f'{self.ACTION_PREFIX}REPRODUCE', # Action 3
            f'{self.ACTION_PREFIX}ATTACK',    # Action 4
            f'{self.ACTION_PREFIX}COOPERATE', # Action 5
        ]
        
        for token in action_tokens:
            self.vocab.add_word(token)
    
    def action_to_token(self, action_idx: int) -> str:
        """Convert action index to token string."""
        action_names = ['REST', 'MOVE', 'EAT', 'REPRODUCE', 'ATTACK', 'COOPERATE']
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
