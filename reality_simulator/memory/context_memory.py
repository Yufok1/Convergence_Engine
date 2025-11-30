"""
Context Memory System for Referential Storage

Provides shared contextual memory to unify organism nodes in contextual reference.
Enables organisms to correlate language patterns with network structure.

Extended with:
- Integration with LanguageVocabulary for tokenization
- Optional nn.Embedding for learned word representations
- Token sequence storage for language model training
"""

import json
import os
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import numpy as np

# Try importing PyTorch for nn.Embedding
try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    nn = None

# Import LanguageVocabulary if available
try:
    from reality_simulator.language_system import LanguageVocabulary, SPECIAL_TOKENS
    LANGUAGE_SYSTEM_AVAILABLE = True
except ImportError:
    LANGUAGE_SYSTEM_AVAILABLE = False
    LanguageVocabulary = None
    SPECIAL_TOKENS = {}


class ContextMemory:
    """
    Shared reference store for correlating language and network structure.

    Key structures:
    - node_embeddings: vector representations of organisms
    - language_anchors: words mapped to node IDs they reference
    - episodic_events: generation snapshots of key metrics
    - vocabulary: LanguageVocabulary for tokenization (optional)
    - word_embedding: nn.Embedding for learned representations (optional)
    - organism_sequences: token sequences for each organism (for LM training)
    """

    def __init__(self, persistence_path: str = "data/context_memory.json",
                 use_learned_embeddings: bool = False,
                 embedding_dim: int = 64,
                 max_vocab_size: int = 10000):
        """
        Initialize context memory.
        
        Args:
            persistence_path: Path for JSON persistence
            use_learned_embeddings: Use nn.Embedding for learned word representations
            embedding_dim: Dimension for learned embeddings
            max_vocab_size: Maximum vocabulary size
        """
        self.persistence_path = persistence_path
        self.use_learned_embeddings = use_learned_embeddings and PYTORCH_AVAILABLE
        self.embedding_dim = embedding_dim
        self.max_vocab_size = max_vocab_size
        
        # Core data structures
        self.node_embeddings: Dict[int, List[float]] = {}  # organism_id -> embedding vector
        self.language_anchors: Dict[str, Set[int]] = defaultdict(set)  # word -> set of organism_ids
        self.episodic_events: Dict[int, Dict[str, Any]] = {}  # generation -> metrics snapshot
        self.word_frequencies: Dict[str, int] = defaultdict(int)  # word usage counts
        self.node_word_associations: Dict[int, Set[str]] = defaultdict(set)  # organism_id -> words
        
        # Language model integration
        self.vocabulary: Optional['LanguageVocabulary'] = None
        self.word_embedding: Optional['nn.Embedding'] = None
        self.organism_sequences: Dict[int, List[int]] = defaultdict(list)  # organism_id -> token_ids
        
        # Initialize vocabulary if available
        if LANGUAGE_SYSTEM_AVAILABLE:
            self.vocabulary = LanguageVocabulary(max_vocab_size=max_vocab_size)
        
        # Initialize learned embeddings if enabled
        if self.use_learned_embeddings:
            self._initialize_learned_embeddings()

        # Load existing data if available
        self._load_persistence()
    
    def _initialize_learned_embeddings(self):
        """Initialize PyTorch nn.Embedding for learned word representations."""
        if not PYTORCH_AVAILABLE:
            print("[CONTEXT_MEMORY] PyTorch not available, using frequency-based embeddings")
            self.use_learned_embeddings = False
            return
        
        self.word_embedding = nn.Embedding(
            num_embeddings=self.max_vocab_size,
            embedding_dim=self.embedding_dim,
            padding_idx=SPECIAL_TOKENS.get('<PAD>', 0) if SPECIAL_TOKENS else 0
        )
        
        # Xavier initialization
        nn.init.xavier_uniform_(self.word_embedding.weight)
        
        print(f"[CONTEXT_MEMORY] Initialized learned embeddings: {self.max_vocab_size} x {self.embedding_dim}")
    
    def build_vocabulary_from_anchors(self) -> int:
        """
        Build vocabulary from existing language_anchors structure.
        
        Returns:
            Number of words added to vocabulary
        """
        if not LANGUAGE_SYSTEM_AVAILABLE or self.vocabulary is None:
            print("[CONTEXT_MEMORY] LanguageVocabulary not available, skipping vocabulary build")
            return 0
        
        words_added = self.vocabulary.build_from_language_anchors(
            language_anchors=dict(self.language_anchors),
            node_word_associations={k: v for k, v in self.node_word_associations.items()}
        )
        
        return words_added
    
    def get_word_embedding(self, word: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for a word.
        
        Uses learned embeddings if available, otherwise frequency-based.
        
        Args:
            word: Word to get embedding for
            
        Returns:
            Embedding vector as numpy array, or None if not found
        """
        if self.use_learned_embeddings and self.word_embedding is not None and self.vocabulary is not None:
            token_id = self.vocabulary.get_id(word)
            with torch.no_grad():
                embedding = self.word_embedding(torch.tensor([token_id]))
            return embedding.squeeze().numpy()
        
        # Fallback to frequency-based embedding
        if word in self.word_frequencies:
            # Simple one-hot style embedding based on word index
            word_idx = list(self.word_frequencies.keys()).index(word)
            embedding = np.zeros(min(len(self.word_frequencies), 100))
            if word_idx < len(embedding):
                embedding[word_idx] = self.word_frequencies[word]
            return embedding
        
        return None
    
    def tokenize_sequence(self, words: List[str], add_special: bool = True) -> List[int]:
        """
        Tokenize a sequence of words to token IDs.
        
        Args:
            words: List of words to tokenize
            add_special: Add <START> and <END> tokens
            
        Returns:
            List of token IDs
        """
        if self.vocabulary is None:
            # Fallback: return word indices
            token_ids = []
            word_list = list(self.word_frequencies.keys())
            for word in words:
                if word in word_list:
                    token_ids.append(word_list.index(word))
                else:
                    token_ids.append(0)  # Unknown
            return token_ids
        
        return self.vocabulary.encode(words, add_special=add_special)
    
    def detokenize_sequence(self, token_ids: List[int], skip_special: bool = True) -> List[str]:
        """
        Convert token IDs back to words.
        
        Args:
            token_ids: List of token IDs
            skip_special: Skip special tokens in output
            
        Returns:
            List of words
        """
        if self.vocabulary is None:
            # Fallback: return words by index
            word_list = list(self.word_frequencies.keys())
            words = []
            for idx in token_ids:
                if 0 <= idx < len(word_list):
                    words.append(word_list[idx])
                else:
                    words.append('<UNK>')
            return words
        
        return self.vocabulary.decode(token_ids, skip_special=skip_special)
    
    def record_organism_sequence(self, organism_id: int, token_ids: List[int], 
                                  max_length: int = 128) -> None:
        """
        Record token sequence for an organism (for LM training).
        
        Args:
            organism_id: Organism ID
            token_ids: Token IDs to append
            max_length: Maximum sequence length to maintain
        """
        self.organism_sequences[organism_id].extend(token_ids)
        
        # Truncate to max length (keep most recent)
        if len(self.organism_sequences[organism_id]) > max_length:
            self.organism_sequences[organism_id] = self.organism_sequences[organism_id][-max_length:]
    
    def get_organism_sequence(self, organism_id: int) -> List[int]:
        """
        Get the token sequence for an organism.
        
        Args:
            organism_id: Organism ID
            
        Returns:
            List of token IDs
        """
        return self.organism_sequences.get(organism_id, [])
    
    def clear_organism_sequence(self, organism_id: int) -> None:
        """
        Clear sequence data for a dead organism.
        
        Args:
            organism_id: Organism ID to clear
        """
        if organism_id in self.organism_sequences:
            del self.organism_sequences[organism_id]

    def _load_persistence(self) -> None:
        """Load context memory from disk if it exists."""
        try:
            if os.path.exists(self.persistence_path):
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    self.node_embeddings = {int(k): v for k, v in data.get('node_embeddings', {}).items()}
                    # Convert back to defaultdict to maintain auto-creation behavior
                    self.language_anchors = defaultdict(set, {k: set(v) for k, v in data.get('language_anchors', {}).items()})
                    self.episodic_events = {int(k): v for k, v in data.get('episodic_events', {}).items()}
                    self.word_frequencies = defaultdict(int, data.get('word_frequencies', {}))
                    # Convert back to defaultdict to maintain auto-creation behavior
                    self.node_word_associations = defaultdict(set, {int(k): set(v) for k, v in data.get('node_word_associations', {}).items()})
        except Exception as e:
            print(f"[CONTEXT_MEMORY] Warning: Could not load persistence data: {e}")

    def _save_persistence(self) -> None:
        """Save context memory to disk."""
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            data = {
                'node_embeddings': self.node_embeddings,
                'language_anchors': {k: list(v) for k, v in self.language_anchors.items()},
                'episodic_events': self.episodic_events,
                'word_frequencies': dict(self.word_frequencies),
                'node_word_associations': {k: list(v) for k, v in self.node_word_associations.items()},
                'last_updated': datetime.now().isoformat()
            }
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CONTEXT_MEMORY] Warning: Could not save persistence data: {e}")

    def record_generation_state(self, generation: int, metrics: Dict[str, Any]) -> None:
        """
        Record key metrics snapshot for a generation.

        Args:
            generation: Current generation number
            metrics: Dictionary of key metrics (organism_count, connection_count, etc.)
        """
        self.episodic_events[generation] = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics.copy()
        }
        self._save_persistence()

    def link_word_to_node(self, word: str, organism_id: int, generation: int = None) -> None:
        """
        Create language anchor linking a word to an organism node.

        Args:
            word: The word being associated
            organism_id: ID of the organism node
            generation: Optional generation when this link was made
        """
        print(f"[CONTEXT_MEMORY_DEBUG] link_word_to_node called: word='{word}', organism_id={organism_id}")
        # Update language anchors
        self.language_anchors[word].add(organism_id)

        # Update node associations
        self.node_word_associations[organism_id].add(word)

        # Update word frequency
        self.word_frequencies[word] += 1

        # Create/update embedding for this node
        self._update_node_embedding(organism_id, word)

        # Persist changes periodically
        if len(self.language_anchors) % 10 == 0:  # Save every 10 links
            self._save_persistence()

    def _update_node_embedding(self, organism_id: int, word: str) -> None:
        """
        Update or create embedding vector for a node based on associated words.

        Simple embedding: vector of word frequencies for this node's vocabulary.
        """
        if organism_id not in self.node_embeddings:
            self.node_embeddings[organism_id] = []

        # For now, use a simple frequency-based embedding
        # In a more sophisticated system, this could be semantic embeddings
        embedding_dim = max(50, len(self.word_frequencies))  # Dynamic dimension

        if len(self.node_embeddings[organism_id]) < embedding_dim:
            self.node_embeddings[organism_id].extend([0.0] * (embedding_dim - len(self.node_embeddings[organism_id])))

        # Simple frequency encoding - could be improved with semantic vectors
        word_idx = list(self.word_frequencies.keys()).index(word) if word in self.word_frequencies else 0
        if word_idx < len(self.node_embeddings[organism_id]):
            self.node_embeddings[organism_id][word_idx] += 1.0

    def query_related_nodes(self, word: str, max_results: int = 5) -> List[Tuple[int, float]]:
        """
        Find organism nodes related to a given word via language anchors.

        Args:
            word: Word to find related nodes for
            max_results: Maximum number of results to return

        Returns:
            List of (organism_id, relevance_score) tuples, sorted by relevance
        """
        if word not in self.language_anchors:
            return []

        related_nodes = []
        anchored_nodes = self.language_anchors[word]

        for node_id in anchored_nodes:
            # Calculate relevance based on embedding similarity and word association strength
            relevance = len(self.node_word_associations.get(node_id, set()))
            related_nodes.append((node_id, relevance))

        # Sort by relevance and return top results
        related_nodes.sort(key=lambda x: x[1], reverse=True)
        return related_nodes[:max_results]

    def get_node_context(self, organism_id: int) -> Dict[str, Any]:
        """
        Get full context information for a specific organism node.

        Args:
            organism_id: The organism ID to query

        Returns:
            Dictionary with embedding, associated words, and metadata
        """
        return {
            'organism_id': organism_id,
            'embedding': self.node_embeddings.get(organism_id, []),
            'associated_words': list(self.node_word_associations.get(organism_id, set())),
            'word_count': len(self.node_word_associations.get(organism_id, set())),
            'language_anchors': [word for word, nodes in self.language_anchors.items() if organism_id in nodes]
        }

    def get_anchor_clusters(self, min_cluster_size: int = 2) -> List[Dict[str, Any]]:
        """
        Identify clusters of nodes that share language anchors.

        Args:
            min_cluster_size: Minimum nodes in a cluster to be reported

        Returns:
            List of cluster dictionaries with shared words and node IDs
        """
        clusters = []

        # Group nodes by shared words
        word_to_nodes = defaultdict(set)
        for word, nodes in self.language_anchors.items():
            if len(nodes) >= min_cluster_size:
                word_to_nodes[word] = nodes

        # Find overlapping clusters
        processed_nodes = set()
        for word, nodes in word_to_nodes.items():
            if len(nodes) >= min_cluster_size:
                cluster = {
                    'shared_words': [word],
                    'nodes': list(nodes),
                    'size': len(nodes),
                    'common_words': set()
                }

                # Find other words shared by these nodes
                for other_word, other_nodes in self.language_anchors.items():
                    if other_word != word and nodes.issubset(other_nodes):
                        cluster['shared_words'].append(other_word)
                        cluster['common_words'].add(other_word)

                clusters.append(cluster)
                processed_nodes.update(nodes)

        # Sort clusters by size
        clusters.sort(key=lambda x: x['size'], reverse=True)
        return clusters

    def get_stability_metrics(self) -> Dict[str, float]:
        """
        Calculate stability metrics based on memory coherence.

        Returns:
            Dictionary of stability metrics
        """
        # Friendly debug: when empty, make it clear it's a normal initial state
        if len(self.language_anchors) == 0 and len(self.node_word_associations) == 0:
            print("[Context Memory] No anchors yet – metrics default to 0 (will populate as the system runs)")
        else:
            print(f"[CONTEXT_MEMORY_DEBUG] get_stability_metrics called: language_anchors={len(self.language_anchors)}, node_word_associations={len(self.node_word_associations)}")
        metrics = {}

        # Anchor density: how many nodes have language anchors
        total_nodes = len(set().union(*self.node_word_associations.values()))
        anchored_nodes = len(self.node_word_associations)
        metrics['anchor_density'] = anchored_nodes / max(total_nodes, 1)
        if total_nodes == 0:
            print("[Context Memory] Anchor density: 0.0 (no nodes yet)")
        else:
            print(f"[CONTEXT_MEMORY_DEBUG] anchor_density calculation: anchored_nodes={anchored_nodes}, total_nodes={total_nodes}, density={metrics['anchor_density']}")

        # Language coherence: average words per anchored node
        if anchored_nodes > 0:
            avg_words_per_node = sum(len(words) for words in self.node_word_associations.values()) / anchored_nodes
            metrics['language_coherence'] = avg_words_per_node / max(len(self.word_frequencies), 1)
        else:
            metrics['language_coherence'] = 0.0

        # Cluster stability: ratio of clustered to total anchored nodes
        clusters = self.get_anchor_clusters(min_cluster_size=2)
        clustered_nodes = set()
        for cluster in clusters:
            clustered_nodes.update(cluster['nodes'])

        total_anchored = len(self.node_word_associations)
        metrics['cluster_stability'] = len(clustered_nodes) / max(total_anchored, 1)

        return metrics

    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"ContextMemory: {len(self.node_embeddings)} nodes, "
                f"{len(self.language_anchors)} word anchors, "
                f"{len(self.episodic_events)} episodes")
