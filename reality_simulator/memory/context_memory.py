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
import shutil
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
                 use_learned_embeddings: bool = True,
                 embedding_dim: int = 64,
                 max_vocab_size: int = 20000,  # Default matches config.json
                 organism_embedding_alpha: float = 0.1,
                 config: Optional[Dict] = None):
        """
        Initialize context memory.
        
        Args:
            persistence_path: Path for JSON persistence
            use_learned_embeddings: Use nn.Embedding for learned word representations
            embedding_dim: Dimension for learned embeddings
            max_vocab_size: Maximum vocabulary size
            organism_embedding_alpha: Alpha for blending organism embeddings (0.1 = 90% keep, 10% new)
            config: Full system config for grounded mode checking
        """
        # Convert relative paths to absolute paths based on project root
        if not os.path.isabs(persistence_path):
            # Get project root (Convergence_Engine directory)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            persistence_path = os.path.join(project_root, persistence_path)
        self.persistence_path = persistence_path
        
        # Create the data directory NOW - don't wait for save
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        
        self.use_learned_embeddings = use_learned_embeddings and PYTORCH_AVAILABLE
        self.embedding_dim = embedding_dim
        self.max_vocab_size = max_vocab_size
        self.organism_embedding_alpha = organism_embedding_alpha  # SEMANTIC CONVERGENCE: Config-driven alpha
        
        # Store config for grounded mode checking
        self.config = config or {}
        lang_config = self.config.get('language', {})
        grounded_config = lang_config.get('grounded', {})
        self.grounded_mode_enabled = grounded_config.get('enabled', False)
        self.mastery_gating_enabled = grounded_config.get('mastery_gating', False)
        
        # Core data structures
        self.node_embeddings: Dict[int, List[float]] = {}  # organism_id -> embedding vector
        self.language_anchors: Dict[str, Set[int]] = defaultdict(set)  # word -> set of organism_ids
        self.episodic_events: Dict[int, Dict[str, Any]] = {}  # generation -> metrics snapshot
        self.word_frequencies: Dict[str, int] = defaultdict(int)  # word usage counts
        self.node_word_associations: Dict[int, Set[str]] = defaultdict(set)  # organism_id -> words
        
        # Event emitter for word assignment events
        self.event_emitter: Optional[Any] = None
        
        # Thread safety for embedding updates (used when Ray parallelizes)
        import threading
        self._embedding_lock = threading.Lock()
        
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
    
    def update_word_embedding_from_organism(
        self, word: str, organism_embedding: np.ndarray, alpha: float = 0.1
    ) -> None:
        """
        Blend organism neural embedding into word embedding (EMA update).
        
        This creates SEMANTIC DIFFERENTIATION - words used by differently-tuned
        organisms will occupy different regions of embedding space.
        
        Thread-safe: Uses lock to prevent corruption during multi-threaded access.
        
        RAY COMPATIBILITY NOTE:
            Ray workers serialize and deserialize data - embedding updates inside
            Ray workers happen on COPIES and do NOT propagate back to the main
            process's word_embedding. For semantic convergence, this method should
            be called from the main process after Ray batch operations complete.
            The LanguageTeacher.teach_network() call happens in the main process,
            so embedding updates are properly accumulated there.
        
        Args:
            word: Word to update embedding for
            organism_embedding: 64-dim neural embedding from organism.brain.fc2
            alpha: EMA blending factor (0.1 = 90% keep, 10% new)
        """
        if not self.use_learned_embeddings or self.word_embedding is None:
            return
        if self.vocabulary is None:
            return
        
        token_id = self.vocabulary.get_id(word)
        if token_id is None or token_id >= self.max_vocab_size:
            return
        if organism_embedding is None or len(organism_embedding) != self.embedding_dim:
            return
        
        # Thread-safe embedding update
        with self._embedding_lock:
            with torch.no_grad():
                current = self.word_embedding.weight[token_id]
                org_tensor = torch.from_numpy(organism_embedding.astype(np.float32)).to(current.device)
                self.word_embedding.weight[token_id] = (1 - alpha) * current + alpha * org_tensor

    def update_embeddings_from_atomic(self, atomic_language: Any, learning_rate: float = 0.01) -> int:
        """
        Update word embeddings based on atomic association strengths (GROUNDED MODE).

        Words that are frequently associated in atomic_language should have similar embeddings.
        This makes semantic similarity EMERGE from behavioral experience, not pre-seeded semantics.

        Uses association strength to nudge embeddings:
        - Positive associations → pull embeddings closer
        - Negative associations → push embeddings apart

        Args:
            atomic_language: AtomicLanguageSystem instance with learned associations
            learning_rate: Base learning rate for embedding updates (default 0.01)

        Returns:
            Number of embedding pairs updated
        """
        if not self.use_learned_embeddings or self.word_embedding is None:
            return 0
        if self.vocabulary is None:
            return 0

        updates = 0

        with self._embedding_lock:
            with torch.no_grad():
                # For each association in atomic_language, nudge embeddings
                for concept_id, atom in atomic_language.atoms.items():
                    source_id = self.vocabulary.get_id(concept_id)
                    if source_id is None or source_id >= self.max_vocab_size:
                        continue
                    if source_id == self.vocabulary.get_id('<UNK>'):
                        continue

                    source_emb = self.word_embedding.weight[source_id]

                    for assoc in atom.associations.values():
                        target_id = self.vocabulary.get_id(assoc.target_concept)
                        if target_id is None or target_id >= self.max_vocab_size:
                            continue
                        if target_id == self.vocabulary.get_id('<UNK>'):
                            continue

                        target_emb = self.word_embedding.weight[target_id]

                        # Nudge embeddings based on association strength
                        # Positive association → embeddings should be similar
                        # Negative association → embeddings should be dissimilar
                        strength = assoc.strength
                        update_rate = learning_rate * abs(strength)

                        if strength > 0:
                            # Pull together (positive association)
                            direction = target_emb - source_emb
                            self.word_embedding.weight[source_id] += update_rate * direction
                        elif strength < 0:
                            # Push apart (negative association)
                            direction = source_emb - target_emb
                            direction = direction / (direction.norm() + 1e-8)  # Normalize
                            self.word_embedding.weight[source_id] += update_rate * direction

                        updates += 1

        return updates

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
    
    def cleanup_dead_organism(self, organism_id: int) -> None:
        """
        🧹 MEMORY LEAK FIX: Clean up ALL data for a dead organism.
        
        This should be called when an organism dies to prevent unbounded
        growth of node_embeddings, node_word_associations, and sequences.
        
        Args:
            organism_id: Organism ID to clean up
        """
        # Clear sequence data
        if organism_id in self.organism_sequences:
            del self.organism_sequences[organism_id]
        
        # Clear embedding data (MEMORY LEAK FIX)
        if organism_id in self.node_embeddings:
            del self.node_embeddings[organism_id]
        
        # Clear word associations (but keep language_anchors for history)
        if organism_id in self.node_word_associations:
            del self.node_word_associations[organism_id]

    def _load_persistence(self) -> None:
        """Load context memory from disk if it exists, falling back to backup on corruption."""

        def _load_from_path(path: str) -> Optional[dict]:
            if not os.path.exists(path):
                return None
            with open(path, 'r') as f:
                return json.load(f)

        data = None
        try:
            data = _load_from_path(self.persistence_path)
        except Exception as e:
            print(f"[CONTEXT_MEMORY] Warning: Could not load persistence data ({self.persistence_path}): {e}")

        if data is None:
            backup_path = f"{self.persistence_path}.backup"
            try:
                data = _load_from_path(backup_path)
                if data is not None:
                    print("[CONTEXT_MEMORY] Restored context memory from backup copy")
                    shutil.copy2(backup_path, self.persistence_path)
            except Exception as e:
                print(f"[CONTEXT_MEMORY] Warning: Could not load backup context memory: {e}")

        if not data:
            return

        self.node_embeddings = {int(k): v for k, v in data.get('node_embeddings', {}).items()}
        # Convert back to defaultdict to maintain auto-creation behavior
        self.language_anchors = defaultdict(set, {k: set(v) for k, v in data.get('language_anchors', {}).items()})
        self.episodic_events = {int(k): v for k, v in data.get('episodic_events', {}).items()}
        self.word_frequencies = defaultdict(int, data.get('word_frequencies', {}))
        # Convert back to defaultdict to maintain auto-creation behavior
        self.node_word_associations = defaultdict(set, {int(k): set(v) for k, v in data.get('node_word_associations', {}).items()})
        
        # SEMANTIC CONVERGENCE: Load learned word embeddings if they exist
        if self.use_learned_embeddings and self.word_embedding is not None and PYTORCH_AVAILABLE:
            embedding_path = self.persistence_path.replace('.json', '_embeddings.pt')
            if os.path.exists(embedding_path):
                try:
                    self.word_embedding.load_state_dict(torch.load(embedding_path, weights_only=True))
                    print(f"[CONTEXT_MEMORY] Loaded learned word embeddings from {embedding_path}")
                except Exception as e:
                    print(f"[CONTEXT_MEMORY] Warning: Could not load word embeddings: {e}")

    def _save_persistence(self) -> None:
        """Save context memory to disk."""
        directory = os.path.dirname(self.persistence_path) or '.'
        
        try:
            os.makedirs(directory, exist_ok=True)
            
            data = {
                'node_embeddings': self.node_embeddings,
                'language_anchors': {k: list(v) for k, v in self.language_anchors.items()},
                'episodic_events': self.episodic_events,
                'word_frequencies': dict(self.word_frequencies),
                'node_word_associations': {k: list(v) for k, v in self.node_word_associations.items()},
                'last_updated': datetime.now().isoformat()
            }

            # Direct write - atomic rename can fail on network filesystems
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f)
            
            # SEMANTIC CONVERGENCE: Save learned word embeddings
            if self.use_learned_embeddings and self.word_embedding is not None and PYTORCH_AVAILABLE:
                embedding_path = self.persistence_path.replace('.json', '_embeddings.pt')
                try:
                    torch.save(self.word_embedding.state_dict(), embedding_path)
                except Exception as e:
                    print(f"[CONTEXT_MEMORY] Warning: Could not save word embeddings: {e}")
                    
        except Exception as e:
            print(f"[CONTEXT_MEMORY] Warning: Could not save persistence data: {e}")

    def record_generation_state(self, generation: int, metrics: Dict[str, Any],
                                  max_episodes: int = 1000) -> None:
        """
        Record key metrics snapshot for a generation.
        
        🧹 MEMORY LEAK FIX: Prunes old episodic events to prevent unbounded growth.

        Args:
            generation: Current generation number
            metrics: Dictionary of key metrics (organism_count, connection_count, etc.)
            max_episodes: Maximum number of episodes to keep (default 1000)
        """
        self.episodic_events[generation] = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics.copy()
        }
        
        # 🧹 MEMORY LEAK FIX: Prune old episodes if over limit
        if len(self.episodic_events) > max_episodes:
            # Keep most recent episodes
            sorted_gens = sorted(self.episodic_events.keys())
            gens_to_remove = sorted_gens[:len(sorted_gens) - max_episodes]
            for gen in gens_to_remove:
                del self.episodic_events[gen]
        
        self._save_persistence()

    def link_word_to_node(self, word: str, organism_id: int, generation: int = None,
                          organism_embedding: Optional[np.ndarray] = None,
                          organism: Optional[Any] = None) -> bool:
        """
        Create language anchor linking a word to an organism node.

        Args:
            word: The word being associated
            organism_id: ID of the organism node
            generation: Optional generation when this link was made
            organism_embedding: Optional 64-dim neural embedding from organism.brain.fc2
                                If provided, blends into word embedding for semantic differentiation
            organism: Optional organism object for mastery level checking in grounded mode
        
        Returns:
            True if word was linked, False if rejected by mastery gating
        """
        # ═══════════════════════════════════════════════════════════════════════════
        # GROUNDED MODE: Enforce mastery gating - organisms must EARN vocabulary
        # This is a safety net check. Primary validation happens in callers:
        # - language_teacher.py returns early if level < 4 in grounded mode
        # - concept_tracker.py skips linking entirely in grounded mode
        # - germination_pool.py skips inheritance in grounded mode
        # ═══════════════════════════════════════════════════════════════════════════
        if self.grounded_mode_enabled and self.mastery_gating_enabled:
            # If organism is explicitly provided, verify mastery level
            if organism is not None and hasattr(organism, 'atomic_language'):
                mastery_level = getattr(organism.atomic_language, 'mastery_level', 0)
                if mastery_level < 4:
                    # Below level 4: Check if word is in organism's earned vocabulary
                    if hasattr(organism.atomic_language, 'can_use_word'):
                        if not organism.atomic_language.can_use_word(word):
                            return False  # Word not yet earned - reject silently
                    else:
                        # No can_use_word method - conservative rejection
                        return False
            # If organism=None, trust that caller has already validated (e.g., language_teacher)
        
        # Update language anchors
        self.language_anchors[word].add(organism_id)

        # Update node associations
        was_new_word = word not in self.node_word_associations[organism_id]
        self.node_word_associations[organism_id].add(word)

        # Update word frequency
        self.word_frequencies[word] += 1

        # Create/update embedding for this node
        self._update_node_embedding(organism_id, word)
        
        # NEW: Blend organism neural embedding into word embedding
        # Uses config-driven alpha for semantic convergence
        if organism_embedding is not None:
            self.update_word_embedding_from_organism(word, organism_embedding, alpha=self.organism_embedding_alpha)
        
        # Only emit word_assignment event for significant milestones (quality over quantity)
        # Match neural/ML event frequency - only emit when word reaches meaningful adoption
        if was_new_word:
            # Only emit if word is adopted by multiple organisms (significant language emergence)
            num_organisms_with_word = len(self.language_anchors[word])
            # SEMANTIC CONVERGENCE: Lower threshold to 3+ organisms for better causation tracking
            if self.event_emitter and num_organisms_with_word >= 3:
                try:
                    import time
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='semantic_convergence',  # Changed from 'language' for causation filtering
                        event_type='word_assignment',
                        data={
                            'word': word,
                            'organism_id': organism_id,
                            'generation': generation,
                            'total_words_for_organism': len(self.node_word_associations[organism_id]),
                            'total_organisms_with_word': num_organisms_with_word,
                            'word_frequency': self.word_frequencies[word]
                        }
                    )
                    self.event_emitter(event)
                except (ImportError, Exception) as e:
                    # Event emission failed - but don't break word assignment
                    import logging
                    logging.getLogger(__name__).warning(f"word_assignment event emission failed: {e}")
            # If event_emitter is None, word is still assigned but no event emitted
            # This is OK - events will start appearing once emitter is wired

        # Persist changes much less frequently (every 500 links) to avoid I/O bottleneck
        if len(self.language_anchors) % 500 == 0:
            self._save_persistence()
        
        return True  # Word was successfully linked

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
        # Friendly debug: when empty, make it clear it's a normal initial state (only log once)
        if len(self.language_anchors) == 0 and len(self.node_word_associations) == 0:
            if not hasattr(self, '_empty_metrics_logged'):
                self._empty_metrics_logged = True
                logging.debug("[Context Memory] No anchors yet – metrics default to 0 (will populate as the system runs)")
        # Removed verbose debug prints - metrics are already logged via StateLogger
        metrics = {}

        # Anchor density: how many nodes have language anchors
        total_nodes = len(set().union(*self.node_word_associations.values()))
        anchored_nodes = len(self.node_word_associations)
        metrics['anchor_density'] = anchored_nodes / max(total_nodes, 1)
        if total_nodes == 0 and not hasattr(self, '_density_logged'):
            self._density_logged = True
            logging.debug("[Context Memory] Anchor density: 0.0 (no nodes yet)")
        # Removed verbose debug print - anchor_density is already logged via StateLogger

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

    # ═══════════════════════════════════════════════════════════════════════════
    # VECTOR RETRIEVAL: Semantic similarity search over word embeddings
    # ═══════════════════════════════════════════════════════════════════════════
    
    def find_similar_words(self, 
                          query_word: str = None,
                          query_embedding: np.ndarray = None,
                          top_k: int = 10,
                          exclude_words: Set[str] = None,
                          min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """
        Find words most similar to query using learned embeddings (cosine similarity).
        
        This enables VECTOR RETRIEVAL for semantic word selection instead of
        relying on token ID position (which caused the A-words bug).
        
        Args:
            query_word: Word to find similar words for (uses its embedding)
            query_embedding: Direct embedding vector to query with (alternative to word)
            top_k: Number of similar words to return
            exclude_words: Set of words to exclude from results
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of (word, similarity_score) tuples, sorted by similarity descending
        """
        if not self.use_learned_embeddings or self.word_embedding is None:
            return []
        
        if self.vocabulary is None:
            return []
        
        exclude_words = exclude_words or set()
        
        # Get query embedding
        if query_embedding is not None:
            query_vec = torch.from_numpy(query_embedding.astype(np.float32))
        elif query_word is not None:
            token_id = self.vocabulary.get_id(query_word)
            if token_id is None or token_id >= self.max_vocab_size:
                return []
            with torch.no_grad():
                query_vec = self.word_embedding.weight[token_id]
        else:
            return []
        
        # Compute cosine similarity against all word embeddings
        with torch.no_grad():
            # Normalize query
            query_norm = query_vec / (query_vec.norm() + 1e-8)
            
            # Normalize all embeddings
            all_embeddings = self.word_embedding.weight
            all_norms = all_embeddings.norm(dim=1, keepdim=True) + 1e-8
            all_normalized = all_embeddings / all_norms
            
            # Cosine similarity
            similarities = torch.matmul(all_normalized, query_norm)
        
        # Convert to list and filter
        results = []
        for token_id, sim in enumerate(similarities.tolist()):
            if token_id >= len(self.vocabulary.id_to_word):
                continue
            word = self.vocabulary.id_to_word.get(token_id)
            if word is None:
                continue
            # Skip special tokens and excluded words
            if word in SPECIAL_TOKENS or word in exclude_words:
                continue
            if sim >= min_similarity:
                results.append((word, sim))
        
        # Sort by similarity descending and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def find_words_near_state(self,
                              organism_state: np.ndarray,
                              top_k: int = 10,
                              exclude_words: Set[str] = None) -> List[Tuple[str, float]]:
        """
        Find words whose embeddings are similar to an organism's state vector.
        
        This enables ASSOCIATIVE REASONING - organisms can retrieve words
        semantically related to their current state/situation.
        
        Args:
            organism_state: Organism's state/embedding vector (e.g., from brain.fc2)
            top_k: Number of words to return
            exclude_words: Words to exclude
            
        Returns:
            List of (word, similarity_score) tuples
        """
        if organism_state is None or len(organism_state) == 0:
            return []
        
        # Truncate or pad state to match embedding dimension
        state_vec = np.zeros(self.embedding_dim, dtype=np.float32)
        copy_len = min(len(organism_state), self.embedding_dim)
        state_vec[:copy_len] = organism_state[:copy_len]
        
        return self.find_similar_words(
            query_embedding=state_vec,
            top_k=top_k,
            exclude_words=exclude_words,
            min_similarity=0.1  # Require some similarity
        )

    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"ContextMemory: {len(self.node_embeddings)} nodes, "
                f"{len(self.language_anchors)} word anchors, "
                f"{len(self.episodic_events)} episodes")
