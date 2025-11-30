"""
Language Teacher - Enhanced Multi-Dimensional Situational Awareness

Automated system that observes organism behavior and state, then associates
words with organisms through ContextMemory. This enables vocabulary growth
and language learning.

Primary: Linguistic Knowledge Web (comprehensive semantic network)
- Situational awareness (context-appropriate words)
- Associative complexity (semantically related words)
- 14-dimensional state evaluation

Secondary: Learned semantic embeddings from organism experiences
- Gradually transitions from knowledge web to learned associations


Based on semantic grounding research and emergent language patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import numpy as np

# Try importing PyTorch for semantic embeddings
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None
    F = None

# Try importing Linguistic Knowledge Web
try:
    from .linguistic_knowledge_web import LinguisticKnowledgeWeb
    KNOWLEDGE_WEB_AVAILABLE = True
except ImportError:
    try:
        from reality_simulator.language.linguistic_knowledge_web import LinguisticKnowledgeWeb
        KNOWLEDGE_WEB_AVAILABLE = True
    except ImportError:
        KNOWLEDGE_WEB_AVAILABLE = False
        LinguisticKnowledgeWeb = None

logger = logging.getLogger(__name__)


class SemanticEmbeddingTeacher(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Phase 2: Learned semantic embeddings for word-state associations.
    
    Learns to map organism states to semantic space, then to words,
    based on actual organism experiences (state-action-reward sequences).
    """
    
    def __init__(self, state_dim: int = 18, embedding_dim: int = 64, vocab_size: int = 1000):
        """
        Initialize semantic embedding teacher.
        
        Args:
            state_dim: Dimension of organism state vector (default: 18)
            embedding_dim: Dimension of semantic embedding space (default: 64)
            vocab_size: Maximum vocabulary size (default: 1000)
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for SemanticEmbeddingTeacher")
        
        super().__init__()
        
        # State encoder: organism state → semantic embedding
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, embedding_dim),
            nn.LayerNorm(embedding_dim)
        )
        
        # Word embeddings (learned)
        self.word_embeddings = nn.Embedding(vocab_size, embedding_dim)
        
        # State → word prediction network
        self.state_to_word = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, vocab_size)
        )
        
        # Action encoder (optional, for action-aware word prediction)
        self.action_encoder = nn.Embedding(6, embedding_dim)  # 6 actions
        
        # Optimizer
        self.optimizer = optim.Adam(self.parameters(), lr=0.001)
        
        # Training statistics
        self.training_steps = 0
        self.loss_history = []
        
        # Initialize word embeddings with small random values
        nn.init.normal_(self.word_embeddings.weight, mean=0.0, std=0.1)
    
    def forward(self, state: torch.Tensor, action: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass: state → semantic embedding → word logits.
        
        Args:
            state: Organism state tensor (batch_size, state_dim)
            action: Optional action tensor (batch_size,)
            
        Returns:
            Word logits (batch_size, vocab_size)
        """
        # Encode state to semantic space
        state_emb = self.state_encoder(state)
        
        # Optionally incorporate action
        if action is not None:
            action_emb = self.action_encoder(action)
            # Combine state and action embeddings
            combined_emb = state_emb + 0.3 * action_emb
        else:
            combined_emb = state_emb
        
        # Predict words from semantic embedding
        word_logits = self.state_to_word(combined_emb)
        
        return word_logits
    
    def predict_words(self, state: np.ndarray, action: Optional[int] = None, 
                     top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Predict top-k words for a given state.
        
        Args:
            state: Organism state vector (state_dim,)
            action: Optional action index
            top_k: Number of top words to return
            
        Returns:
            List of (word_id, confidence) tuples
        """
        self.eval()
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            action_tensor = torch.LongTensor([action]) if action is not None else None
            
            word_logits = self.forward(state_tensor, action_tensor)
            probs = F.softmax(word_logits, dim=-1)
            
            top_probs, top_indices = torch.topk(probs, k=min(top_k, word_logits.size(1)), dim=1)
            
            return [(idx.item(), prob.item()) for idx, prob in zip(top_indices[0], top_probs[0])]
    
    def train_step(self, states: np.ndarray, actions: np.ndarray, 
                   target_words: List[List[int]], rewards: np.ndarray):
        """
        Train on a batch of experiences.
        
        Args:
            states: Batch of organism states (batch_size, state_dim)
            actions: Batch of actions (batch_size,)
            target_words: List of target word IDs for each experience
            rewards: Rewards for each experience (batch_size,)
        """
        self.train()
        
        # Convert to tensors
        state_tensor = torch.FloatTensor(states)
        action_tensor = torch.LongTensor(actions)
        reward_tensor = torch.FloatTensor(rewards)
        
        # Forward pass
        word_logits = self.forward(state_tensor, action_tensor)
        
        # Create target tensor (multi-label: multiple words can be correct)
        batch_size = len(target_words)
        vocab_size = word_logits.size(1)
        target_tensor = torch.zeros(batch_size, vocab_size)
        
        for i, word_ids in enumerate(target_words):
            for word_id in word_ids:
                if 0 <= word_id < vocab_size:
                    # Weight by reward (positive rewards reinforce word associations)
                    target_tensor[i, word_id] = max(0.0, reward_tensor[i].item())
        
        # Loss: binary cross-entropy with reward weighting
        loss = F.binary_cross_entropy_with_logits(
            word_logits, 
            target_tensor,
            reduction='mean'
        )
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        self.training_steps += 1
        self.loss_history.append(loss.item())
        
        return loss.item()


class LanguageTeacher:
    """
    Enhanced language teacher with multi-dimensional situational awareness.
    
    Primary: Linguistic Knowledge Web (comprehensive semantic network)
    - Situational awareness (context-appropriate words)
    - Associative complexity (semantically related words)
    - 14-dimensional state evaluation
    
    Secondary: Semantic embeddings (learned from experience)
    - Learns semantic embeddings from organism experiences
    - Gradually transitions from knowledge web to learned associations
    """
    
    # Old hardcoded maps removed - now using LinguisticKnowledgeWeb methods exclusively
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize language teacher.
        
        Args:
            config: Configuration dictionary with language_model settings
        """
        self.config = config or {}
        language_config = self.config.get('neural', {}).get('language_model', {})
        teacher_config = language_config.get('teacher', {})
        
        # Enable/disable flag
        self.enabled = language_config.get('enabled', False)
        
        # Teaching frequency (teach every N generations)
        self.teaching_frequency = language_config.get('teaching_frequency', 1)  # Every generation by default
        
        # Minimum action history length before teaching
        self.min_action_history = language_config.get('min_action_history', 3)
        
        # Semantic embedding teacher (Phase 2)
        self.use_semantic_embeddings = teacher_config.get('use_semantic_embeddings', True) and PYTORCH_AVAILABLE
        self.semantic_teacher = None
        self.vocab_size = teacher_config.get('vocab_size', 1000)
        self.embedding_dim = teacher_config.get('embedding_dim', 64)
        self.state_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 18)
        
        # Training configuration
        self.min_experiences_for_training = teacher_config.get('min_experiences', 100)
        self.training_frequency = teacher_config.get('training_frequency', 10)  # Train every N generations
        self.experience_buffer: List[Dict[str, Any]] = []  # Store experiences for training
        
        # Transition from hardcoded to learned (0.0 = all hardcoded, 1.0 = all learned)
        self.learning_confidence = 0.0  # Start with hardcoded
        self.min_confidence_for_use = teacher_config.get('min_confidence', 0.3)  # Use learned when confidence > 0.3
        
        # Linguistic Knowledge Web (comprehensive semantic network)
        # Required component - should always be available
        if not KNOWLEDGE_WEB_AVAILABLE:
            raise ImportError("LinguisticKnowledgeWeb is required but not available. Check imports.")
        
        self.use_knowledge_web = teacher_config.get('use_knowledge_web', True)
        if self.use_knowledge_web:
            self.knowledge_web = LinguisticKnowledgeWeb(config)
            logger.info(f"[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled ({len(self.knowledge_web.concepts)} concepts)")
        else:
            self.knowledge_web = None
            logger.warning("[LANGUAGE_TEACHER] Knowledge web disabled in config")
        
        if self.use_semantic_embeddings:
            try:
                self.semantic_teacher = SemanticEmbeddingTeacher(
                    state_dim=self.state_dim,
                    embedding_dim=self.embedding_dim,
                    vocab_size=self.vocab_size
                )
                logger.info(f"[LANGUAGE_TEACHER] Semantic embeddings enabled (state_dim={self.state_dim}, embedding_dim={self.embedding_dim})")
            except Exception as e:
                logger.warning(f"[LANGUAGE_TEACHER] Failed to initialize semantic teacher: {e}, falling back to hardcoded maps")
                self.use_semantic_embeddings = False
        
        # Track teaching statistics
        self.stats = {
            'organisms_taught': 0,
            'words_assigned': 0,
            'total_teachings': 0,
            'words_by_type': defaultdict(int),
            'hardcoded_words': 0,
            'learned_words': 0,
            'situational_words': 0,
            'associative_words': 0,
            'training_steps': 0,
            'learning_confidence': 0.0
        }
        
        logger.info(f"[LANGUAGE_TEACHER] Initialized (enabled={self.enabled}, knowledge_web={self.use_knowledge_web}, semantic={self.use_semantic_embeddings}, frequency={self.teaching_frequency})")
    
    def teach_organism(self, organism, context_memory, generation: int) -> int:
        """
        Teach words to an organism based on its behavior and state.
        
        Enhanced with Linguistic Knowledge Web for:
        - Situational awareness (context-appropriate words)
        - Associative complexity (semantically related words)
        - Reflexive thought (meta-linguistic reasoning)
        
        Args:
            organism: Organism instance (can be Organism or NeuralOrganism)
            context_memory: ContextMemory instance for storing associations
            generation: Current generation number
            
        Returns:
            Number of words assigned to this organism
        """
        if not self.enabled:
            return 0
        
        words_assigned = 0
        
        # Get organism ID (convert to int if needed for compatibility)
        species_id = organism.species_id if hasattr(organism, 'species_id') else str(id(organism))
        # Convert string ID to int (hash-based) for compatibility with link_word_to_node
        organism_id = hash(species_id) if isinstance(species_id, str) else species_id
        
        # ============================================================
        # ENHANCED: Dynamic Multi-Dimensional Situational Awareness
        # ============================================================
        if self.use_knowledge_web and self.knowledge_web:
            # Get full 18-feature state vector (if organism supports it)
            organism_state = None
            if hasattr(organism, 'get_state_features'):
                try:
                    organism_state = organism.get_state_features(
                        local_env=None,
                        network_state=context_memory.network_state if hasattr(context_memory, 'network_state') else None,
                        breath_state=context_memory.breath_state if hasattr(context_memory, 'breath_state') else None
                    )
                except Exception as e:
                    logger.debug(f"[LANGUAGE_TEACHER] Could not get full state features: {e}")
            
            # Fallback: build basic state vector if full state unavailable
            # get_situational_awareness expects a numpy array, not a dict
            if organism_state is None or not isinstance(organism_state, np.ndarray):
                # Build minimal 18-feature state vector from available organism attributes
                fitness = organism.fitness if hasattr(organism, 'fitness') else 0.5
                resources = organism.resources if hasattr(organism, 'resources') else 0.5
                num_connections = len(organism.connections) if hasattr(organism, 'connections') and hasattr(organism.connections, '__len__') else 0
                
                # Create minimal state vector (18 features with defaults)
                organism_state = np.array([
                    fitness,                    # 0: fitness
                    resources,                  # 1: resources
                    float(num_connections),     # 2: connections
                    0.5,                        # 3: pos_x (unknown)
                    0.5,                        # 4: pos_y (unknown)
                    0.5,                        # 5: action_success (unknown)
                    0.5,                        # 6: local_density (unknown)
                    0.5,                        # 7: nearest_distance (unknown)
                    0.0,                        # 8: generation_age (unknown)
                    0.5,                        # 9: parent_fitness (unknown)
                    0.5,                        # 10: breath_feat1 (unknown)
                    0.5,                        # 11: breath_feat2 (unknown)
                    0.0,                        # 12: trait_divergence (unknown)
                    0.5,                        # 13: network_coherence (unknown)
                    0.5,                        # 14: quantum_entropy (unknown)
                    0.0,                        # 15: evolution_pressure (unknown)
                    0.0,                        # 16: phase_mismatch (unknown)
                    0.5                         # 17: system_health (unknown)
                ], dtype=np.float32)
            
            # Get current action
            current_action = None
            if hasattr(organism, 'prev_action'):
                current_action = organism.prev_action
            elif hasattr(organism, 'get_action_sequence'):
                actions = organism.get_action_sequence(length=1)
                if actions:
                    current_action = actions[-1]
            
            # Get network state and breath state for full context
            network_state = context_memory.network_state if hasattr(context_memory, 'network_state') else None
            breath_state = context_memory.breath_state if hasattr(context_memory, 'breath_state') else None
            
            # Get dynamically aware words using all available context
            situational_words = self.knowledge_web.get_situational_awareness(
                organism_state=organism_state,
                organism_action=current_action,
                network_state=network_state,
                breath_state=breath_state,
                context_memory=context_memory
            )
            
            # Link situationally aware words
            for word in situational_words[:12]:  # Top 12 most relevant
                try:
                    context_memory.link_word_to_node(word, organism_id, generation)
                    words_assigned += 1
                    self.stats['words_by_type']['situational'] += 1
                    self.stats['situational_words'] += 1
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Failed to link situational word '{word}': {e}")
            
            # Add semantically related words (associative complexity)
            for base_word in situational_words[:4]:  # Top 4 base words
                similar_words = self.knowledge_web.get_similar_words(base_word, min_strength=0.6)
                for word in similar_words[:2]:  # Top 2 similar words
                    if word not in situational_words:  # Avoid duplicates
                        try:
                            context_memory.link_word_to_node(word, organism_id, generation)
                            words_assigned += 1
                            self.stats['words_by_type']['associative'] += 1
                            self.stats['associative_words'] += 1
                        except Exception as e:
                            logger.warning(f"[LANGUAGE_TEACHER] Failed to link associative word '{word}': {e}")
            
            # If we got words from knowledge web, use hardcoded maps as supplement
            if words_assigned > 0:
                # Knowledge web is primary, hardcoded maps provide reinforcement
                use_hardcoded = True  # Can be toggled
            else:
                use_hardcoded = True  # Fallback to hardcoded
        else:
            use_hardcoded = True  # No knowledge web, use hardcoded
        
        # ============================================================
        # SUPPLEMENT: Use knowledge web methods for action/state-based words
        # ============================================================
        if use_hardcoded:
            # Action-based words (using knowledge web)
            if hasattr(organism, 'get_action_sequence'):
                # Neural organism with action history
                recent_actions = organism.get_action_sequence(length=10)  # Last 10 actions
                if len(recent_actions) >= self.min_action_history:
                    for action in recent_actions:
                        words = self.knowledge_web.get_words_for_action(action) if self.knowledge_web else []
                        
                        for word in words:
                            try:
                                context_memory.link_word_to_node(word, organism_id, generation)
                                words_assigned += 1
                                self.stats['words_by_type']['action'] += 1
                            except Exception as e:
                                logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            elif hasattr(organism, 'prev_action'):
                # Organism with single previous action
                action = organism.prev_action
                if action is not None:
                    words = self.knowledge_web.get_words_for_action(action) if self.knowledge_web else []
                    
                    for word in words[:2]:  # Limit to 2 words for single action
                        try:
                            context_memory.link_word_to_node(word, organism_id, generation)
                            words_assigned += 1
                            self.stats['words_by_type']['action'] += 1
                        except Exception as e:
                            logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            
            # State-based words (using knowledge web)
            # Fitness-based words
            if hasattr(organism, 'fitness'):
                fitness = organism.fitness
                if fitness > 0.7:
                    state_type = 'high_fitness'
                elif fitness < 0.3:
                    state_type = 'low_fitness'
                else:
                    state_type = 'medium_fitness'
                
                words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                # Assign top 2-3 words based on fitness
                for word in words[:3]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation)
                        words_assigned += 1
                        self.stats['words_by_type']['fitness'] += 1
                    except Exception as e:
                        logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            
            # Connection-based words
            if hasattr(organism, 'connections'):
                num_connections = len(organism.connections) if hasattr(organism.connections, '__len__') else 0
                if num_connections > 5:
                    state_type = 'many_connections'
                elif num_connections == 0:
                    state_type = 'no_connections'
                else:
                    state_type = 'few_connections'
                
                words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                # Assign top 2 words
                for word in words[:2]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation)
                        words_assigned += 1
                        self.stats['words_by_type']['connections'] += 1
                    except Exception as e:
                        logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            elif hasattr(organism, 'get_connections'):
                # Alternative connection access
                try:
                    connections = organism.get_connections()
                    num_connections = len(connections) if connections else 0
                    if num_connections > 5:
                        state_type = 'many_connections'
                    elif num_connections == 0:
                        state_type = 'no_connections'
                    else:
                        state_type = 'few_connections'
                    
                    words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                    
                    for word in words[:2]:
                        context_memory.link_word_to_node(word, organism_id, generation)
                        words_assigned += 1
                        self.stats['words_by_type']['connections'] += 1
                except Exception:
                    pass  # Skip if connections not available
            
            # Resource-based words (if available)
            if hasattr(organism, 'resources'):
                resources = organism.resources
                if resources > 0.7:
                    state_type = 'high_resources'
                elif resources < 0.3:
                    state_type = 'low_resources'
                else:
                    state_type = 'medium_resources'
                
                words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                for word in words[:2]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation)
                        words_assigned += 1
                        self.stats['words_by_type']['resources'] += 1
                    except Exception as e:
                        logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        
        # Update statistics
        if words_assigned > 0:
            self.stats['organisms_taught'] += 1
            self.stats['words_assigned'] += words_assigned
        
        return words_assigned
    
    def teach_network(self, organisms: Dict[str, Any], context_memory, generation: int) -> Dict[str, Any]:
        """
        Teach all organisms in the network.
        
        Args:
            organisms: Dictionary of organism_id -> organism
            context_memory: ContextMemory instance
            generation: Current generation number
            
        Returns:
            Dictionary with teaching statistics
        """
        if not self.enabled:
            return {'enabled': False, 'organisms_taught': 0, 'words_assigned': 0}
        
        # Check teaching frequency
        if generation % self.teaching_frequency != 0:
            return {'skipped': True, 'reason': 'teaching_frequency'}
        
        self.stats['total_teachings'] += 1
        organisms_taught = 0
        total_words = 0
        
        for organism_id, organism in organisms.items():
            words_assigned = self.teach_organism(organism, context_memory, generation)
            if words_assigned > 0:
                organisms_taught += 1
                total_words += words_assigned
        
        result = {
            'enabled': True,
            'generation': generation,
            'organisms_taught': organisms_taught,
            'total_organisms': len(organisms),
            'words_assigned': total_words,
            'stats': dict(self.stats)
        }
        
        # Log periodically
        if generation % 10 == 0:
            logger.info(
                f"[LANGUAGE_TEACHER] Gen {generation}: Taught {organisms_taught}/{len(organisms)} organisms, "
                f"{total_words} words assigned"
            )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get teaching statistics."""
        return dict(self.stats)
    
    def reset_stats(self):
        """Reset teaching statistics."""
        self.stats = {
            'organisms_taught': 0,
            'words_assigned': 0,
            'total_teachings': 0,
            'words_by_type': defaultdict(int)
        }


# Convenience function for easy import
def create_language_teacher(config: Optional[Dict[str, Any]] = None) -> Optional[LanguageTeacher]:
    """
    Create a LanguageTeacher instance if language model is enabled.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        LanguageTeacher instance or None if disabled
    """
    if config is None:
        return None
    
    language_config = config.get('neural', {}).get('language_model', {})
    if language_config.get('enabled', False):
        return LanguageTeacher(config)
    return None

