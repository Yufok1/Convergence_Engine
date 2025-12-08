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
    
    def __init__(self, state_dim: int = 24, embedding_dim: int = 64, vocab_size: int = 1000):
        """
        Initialize semantic embedding teacher.
        
        Args:
            state_dim: Dimension of organism state vector (default: 24)
            embedding_dim: Dimension of semantic embedding space (default: 64)
            vocab_size: Maximum vocabulary size (default: 1000, ensemble for full coverage)
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
        self.vocab_size = teacher_config.get('vocab_size', 1000)  # Ensemble strategy: 1000 per organism
        self.embedding_dim = teacher_config.get('embedding_dim', 64)
        self.state_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 24)
        
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
            
            # Try to load expanded/seeded knowledge web first
            from pathlib import Path
            data_dir = Path(__file__).parent.parent.parent / "data"
            
            # Check for expanded web first (has ConceptNet data), then seeded web
            seeded_web_path = data_dir / "seeded_knowledge_web_50k.json"
            expanded_web_path = data_dir / "expanded_knowledge_web.json"
            
            # Prefer expanded web (388K+ relations from ConceptNet) over seeded web
            web_path = expanded_web_path if expanded_web_path.exists() else seeded_web_path
            
            if web_path.exists():
                logger.info(f"[LANGUAGE_TEACHER] Loading knowledge web from {web_path}")
                try:
                    self.knowledge_web.load_from_file(str(web_path))
                    logger.info(f"[LANGUAGE_TEACHER] Successfully loaded knowledge web with {len(self.knowledge_web.concepts)} concepts")
                except Exception as e:
                    logger.error(f"[LANGUAGE_TEACHER] Failed to load knowledge web: {e}")
                    logger.info("[LANGUAGE_TEACHER] Falling back to base knowledge initialization")
            else:
                logger.info("[LANGUAGE_TEACHER] No expanded knowledge web found, using base initialization")
            
            # Load comprehensive knowledge base from JSON files (if expanded web wasn't loaded)
            if len(self.knowledge_web.concepts) < 10000:  # Only load if we don't have expanded web
                try:
                    from .import_knowledge_base import KnowledgeBaseImporter
                    
                    if data_dir.exists():
                        importer = KnowledgeBaseImporter(data_dir=str(data_dir))
                        import_results = importer.import_all(self.knowledge_web, grammar_learner=None)
                        logger.info(f"[LANGUAGE_TEACHER] Knowledge base loaded: {import_results['concepts']} concepts, "
                                   f"{import_results['relations']} relations, {import_results['patterns']} patterns")
                        logger.info(f"[LANGUAGE_TEACHER] Total in web: {import_results['total_concepts']} concepts, "
                                   f"{import_results['total_relations']} relations")
                    else:
                        logger.warning(f"[LANGUAGE_TEACHER] Data directory not found: {data_dir}. Skipping knowledge base import.")
                except ImportError as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Could not import knowledge base: {e}. Using base knowledge only.")
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Error loading knowledge base: {e}. Using base knowledge only.")
            
            logger.info(f"[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled ({len(self.knowledge_web.concepts)} concepts)")
            
            # Quality control configuration
            quality_config = language_config.get('knowledge_web', {}).get('quality_control', {})
            self.review_frequency = quality_config.get('review_frequency', 100)  # Every 100 generations
            self.last_review_generation = 0
            self.current_generation = 0
            self.discoveries_this_generation = 0
            self.discovery_cooldown = teacher_config.get('discovery_cooldown', 5)  # Generations
            self.decay_frequency = teacher_config.get('decay_frequency', 50)  # Generations
        else:
            self.knowledge_web = None
            logger.warning("[LANGUAGE_TEACHER] Knowledge web disabled in config")
            self.review_frequency = 100
            self.last_review_generation = 0
            self.current_generation = 0
            self.discoveries_this_generation = 0
            self.discovery_cooldown = 5
            self.decay_frequency = 50
        
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
        # SEMANTIC CONVERGENCE: Extract organism neural embedding
        # This 64-dim embedding from fc2 layer will flow into word embeddings
        # ============================================================
        organism_embedding = None
        if hasattr(organism, 'get_language_embedding'):
            try:
                organism_embedding = organism.get_language_embedding(context_memory)
            except Exception as e:
                logger.debug(f"[LANGUAGE_TEACHER] Could not get organism embedding: {e}")
        
        # ============================================================
        # SEMANTIC CONVERGENCE: Export ConceptSystem axiom embeddings
        # Axiom words (good, bad, self, other) get state-grounded embeddings
        # NOTE: ConceptSystem is on NeuralTrainer, not organism. Access via self.trainer if available.
        # ============================================================
        concept_system = None
        # Try to get concept_system from trainer (set by teach_network)
        if hasattr(self, '_current_trainer') and self._current_trainer is not None:
            if hasattr(self._current_trainer, 'concept_system'):
                concept_system = self._current_trainer.concept_system
        # Fallback: check organism (legacy path, usually None)
        if concept_system is None and hasattr(organism, 'concept_system'):
            concept_system = organism.concept_system
        
        if concept_system is not None:
            try:
                # Get organism state for grounding
                if hasattr(organism, 'get_state_features'):
                    state_np = organism.get_state_features(None, None, None)
                    if state_np is not None and len(state_np) >= 18:
                        import torch
                        state_tensor = torch.from_numpy(state_np).float()
                        # Export grounded axiom embeddings
                        axiom_embeds = concept_system.export_concept_embeddings(state_tensor)
                        # Read alpha from config (default 0.05)
                        semantic_config = self.config.get('semantic_convergence', {})
                        concept_alpha = semantic_config.get('concept_system_alpha', 0.05)
                        # Push axiom embeddings to word embeddings
                        for axiom_name, embed in axiom_embeds.items():
                            axiom_word = axiom_name.lower()  # GOOD -> good
                            context_memory.update_word_embedding_from_organism(axiom_word, embed, alpha=concept_alpha)
            except Exception as e:
                logger.debug(f"[LANGUAGE_TEACHER] Could not export concept embeddings: {e}")
        
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
                    context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                    words_assigned += 1
                    self.stats['words_by_type']['situational'] += 1
                    self.stats['situational_words'] += 1
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Failed to link situational word '{word}': {e}")
            
            # Add semantically related words (associative complexity)
            # GAP 7 FIX: Use min_confidence_for_use to filter word assignments
            for base_word in situational_words[:4]:  # Top 4 base words
                similar_words = self.knowledge_web.get_similar_words(
                    base_word, 
                    min_strength=max(0.6, self.min_confidence_for_use)  # GAP 7: Apply confidence threshold
                )
                for word in similar_words[:2]:  # Top 2 similar words
                    if word not in situational_words:  # Avoid duplicates
                        try:
                            context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                            words_assigned += 1
                            self.stats['words_by_type']['associative'] += 1
                            self.stats['associative_words'] += 1
                            
                            # 🔄 RECURSIVE EXPANSION: Discover relationship between words used together
                            if hasattr(self.knowledge_web, 'discover_relationship'):
                                # Get VP value for VP-aware exploration
                                vp_value = 0.0
                                if network_state:
                                    vp_value = float(network_state.get('vp_value', 0.0))
                                
                                # Check discovery cooldown and cap
                                if (generation - self.last_review_generation >= self.discovery_cooldown and
                                    self.discoveries_this_generation < self.knowledge_web.max_discoveries_per_generation):
                                    discovered = self.knowledge_web.discover_relationship(
                                        word1=base_word,
                                        word2=word,
                                        context={
                                            'organism_id': organism_id,
                                            'generation': generation,
                                            'organism_state': organism_state.tolist() if hasattr(organism_state, 'tolist') else None,
                                            'discovery_type': 'co_occurrence'
                                        },
                                        strength=0.6,
                                        generation=generation,
                                        vp_value=vp_value
                                    )
                                    if discovered:
                                        self.discoveries_this_generation += 1
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
            # Action-based words (using knowledge web with SEMANTIC SEEDING)
            if hasattr(organism, 'get_action_sequence'):
                # Neural organism with action history
                recent_actions = organism.get_action_sequence(length=10)  # Last 10 actions
                if len(recent_actions) >= self.min_action_history:
                    for action in recent_actions:
                        # Use dynamic method for diverse per-organism vocabulary
                        if hasattr(self.knowledge_web, 'get_words_for_action_dynamic'):
                            words = self.knowledge_web.get_words_for_action_dynamic(action, organism_id)
                        else:
                            words = self.knowledge_web.get_words_for_action(action) if self.knowledge_web else []
                        
                        for word in words:
                            try:
                                context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                                words_assigned += 1
                                self.stats['words_by_type']['action'] += 1
                            except Exception as e:
                                logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            elif hasattr(organism, 'prev_action'):
                # Organism with single previous action
                action = organism.prev_action
                if action is not None:
                    # Use dynamic method for diverse per-organism vocabulary
                    if hasattr(self.knowledge_web, 'get_words_for_action_dynamic'):
                        words = self.knowledge_web.get_words_for_action_dynamic(action, organism_id)
                    else:
                        words = self.knowledge_web.get_words_for_action(action) if self.knowledge_web else []
                    
                    for word in words[:2]:  # Limit to 2 words for single action
                        try:
                            context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                            words_assigned += 1
                            self.stats['words_by_type']['action'] += 1
                        except Exception as e:
                            logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
            
            # State-based words (using knowledge web with SEMANTIC SEEDING)
            # Fitness-based words
            if hasattr(organism, 'fitness'):
                fitness = organism.fitness
                if fitness > 0.7:
                    state_type = 'high_fitness'
                elif fitness < 0.3:
                    state_type = 'low_fitness'
                else:
                    state_type = 'medium_fitness'
                
                # Use dynamic method for diverse per-organism vocabulary
                if hasattr(self.knowledge_web, 'get_words_for_state_dynamic'):
                    words = self.knowledge_web.get_words_for_state_dynamic(state_type, organism_id)
                else:
                    words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                # Assign top 2-3 words based on fitness
                for word in words[:3]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
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
                
                # Use dynamic method for diverse per-organism vocabulary
                if hasattr(self.knowledge_web, 'get_words_for_state_dynamic'):
                    words = self.knowledge_web.get_words_for_state_dynamic(state_type, organism_id)
                else:
                    words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                # Assign top 2 words
                for word in words[:2]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
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
                    
                    # Use dynamic method for diverse per-organism vocabulary
                    if hasattr(self.knowledge_web, 'get_words_for_state_dynamic'):
                        words = self.knowledge_web.get_words_for_state_dynamic(state_type, organism_id)
                    else:
                        words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                    
                    for word in words[:2]:
                        context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                        words_assigned += 1
                        self.stats['words_by_type']['connections'] += 1
                except (AttributeError, KeyError, TypeError) as e:
                    logger.debug(f"Connection word assignment skipped: {e}")
            
            # Resource-based words (if available)
            if hasattr(organism, 'resources'):
                resources = organism.resources
                if resources > 0.7:
                    state_type = 'high_resources'
                elif resources < 0.3:
                    state_type = 'low_resources'
                else:
                    state_type = 'medium_resources'
                
                # Use dynamic method for diverse per-organism vocabulary
                if hasattr(self.knowledge_web, 'get_words_for_state_dynamic'):
                    words = self.knowledge_web.get_words_for_state_dynamic(state_type, organism_id)
                else:
                    words = self.knowledge_web.get_words_for_state(state_type) if self.knowledge_web else []
                
                for word in words[:2]:
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation, organism_embedding)
                        words_assigned += 1
                        self.stats['words_by_type']['resources'] += 1
                    except Exception as e:
                        logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        
        # ============================================================
        # 🆕 ATOMIC LANGUAGE INTEGRATION
        # Update organism's atomic language system with taught concepts
        # ============================================================
        if hasattr(organism, 'atomic_language') and organism.atomic_language is not None:
            try:
                # Get all words that were assigned in this teaching session
                assigned_words = []
                
                # Strengthen concepts based on situational words
                if 'situational_words' in dir() and situational_words:
                    for word in situational_words[:8]:
                        if word in organism.atomic_language.atoms:
                            organism.atomic_language.strengthen_concept(
                                word, 0.05, f"taught_situational_gen{generation}"
                            )
                        else:
                            # Acquire new concept from teaching
                            organism.atomic_language.acquire_concept(
                                word, 'taught', 
                                semantic_frame='situational',
                                reason=f"language_teacher_gen{generation}"
                            )
                        assigned_words.append(word)
                
                # Form associations between co-taught concepts
                if len(assigned_words) >= 2:
                    for i, word1 in enumerate(assigned_words[:4]):
                        for word2 in assigned_words[i+1:5]:
                            if word1 != word2:
                                organism.atomic_language.form_association(
                                    word1, word2, 0.3,
                                    f"co_occurrence_gen{generation}"
                                )
                
                # Decay unused concepts periodically
                if generation % 10 == 0:
                    organism.atomic_language.decay_unused(0.005)
                    
            except Exception as e:
                logger.debug(f"[LANGUAGE_TEACHER] Atomic language update failed: {e}")
        
        # Update statistics
        if words_assigned > 0:
            self.stats['organisms_taught'] += 1
            self.stats['words_assigned'] += words_assigned
        
        return words_assigned
    
    def teach_network(self, organisms: Dict[str, Any], context_memory, generation: int, 
                      trainer=None) -> Dict[str, Any]:
        """
        Teach all organisms in the network.
        
        Args:
            organisms: Dictionary of organism_id -> organism
            context_memory: ContextMemory instance
            generation: Current generation number
            trainer: Optional NeuralTrainer instance (provides ConceptSystem for semantic convergence)
            
        Returns:
            Dictionary with teaching statistics
        """
        # SEMANTIC CONVERGENCE: Store trainer reference for teach_organism to access ConceptSystem
        self._current_trainer = trainer
        if not self.enabled:
            return {'enabled': False, 'organisms_taught': 0, 'words_assigned': 0}
        
        # Check teaching frequency
        if generation % self.teaching_frequency != 0:
            return {'skipped': True, 'reason': 'teaching_frequency'}
        
        # Update generation for time-based learning curve
        self.current_generation = generation
        if self.knowledge_web:
            self.knowledge_web.update_generation(generation)
        
        # Reset discoveries counter for new generation
        self.discoveries_this_generation = 0
        
        self.stats['total_teachings'] += 1
        organisms_taught = 0
        total_words = 0
        
        for organism_id, organism in organisms.items():
            words_assigned = self.teach_organism(organism, context_memory, generation)
            if words_assigned > 0:
                organisms_taught += 1
                total_words += words_assigned
        
        # Periodic quality review (every N generations)
        if generation - self.last_review_generation >= self.review_frequency:
            self._perform_quality_review(generation)
            self.last_review_generation = generation
        
        # Periodic decay (every N generations, more frequent than review)
        if self.knowledge_web and generation % self.decay_frequency == 0:
            quality_config = self.config.get('neural', {}).get('language_model', {}).get('knowledge_web', {}).get('quality_control', {})
            self.knowledge_web.decay_relationships(
                generation=generation,
                pruning_confidence_threshold=quality_config.get('pruning_confidence_threshold', 0.2),
                pruning_unused_generations=quality_config.get('pruning_unused_generations', 100),
                pruning_failure_rate=quality_config.get('pruning_failure_rate', 0.7)
            )
        
        # ============================================================
        # SEMANTIC CONVERGENCE: Push semantic relations into word embeddings
        # Synonyms pulled closer, antonyms pushed apart
        # ============================================================
        semantic_config = self.config.get('semantic_convergence', {})
        semantic_influence_interval = semantic_config.get('knowledge_web_influence_interval', 25)
        if semantic_config.get('enabled', True) and self.knowledge_web and generation % semantic_influence_interval == 0:
            try:
                influenced = self.knowledge_web.influence_context_memory(context_memory)
                if influenced > 0:
                    logger.debug(f"[LANGUAGE_TEACHER] Semantic convergence: influenced {influenced} word embeddings")
            except Exception as e:
                logger.warning(f"[LANGUAGE_TEACHER] Semantic convergence failed: {e}")
        
        result = {
            'enabled': True,
            'generation': generation,
            'organisms_taught': organisms_taught,
            'total_organisms': len(organisms),
            'words_assigned': total_words,
            'discoveries_this_generation': self.discoveries_this_generation,
            'stats': dict(self.stats)
        }
        
        # 🆕 DIALECT ANALYSIS: Analyze population-level linguistic patterns
        if generation % 50 == 0:  # Every 50 generations
            try:
                from .atomic_language import DialectAnalyzer
                
                # Collect atomic language systems from organisms
                language_systems = {}
                for org_id, organism in organisms.items():
                    if hasattr(organism, 'atomic_language') and organism.atomic_language is not None:
                        language_systems[org_id] = organism.atomic_language
                
                if len(language_systems) >= 3:
                    analyzer = DialectAnalyzer()
                    dialect_analysis = analyzer.analyze_dialects(language_systems)
                    result['dialect_analysis'] = dialect_analysis
                    
                    if dialect_analysis.get('num_clusters', 0) > 1:
                        logger.info(
                            f"[LANGUAGE_TEACHER] Dialect emergence: {dialect_analysis['num_clusters']} distinct dialects, "
                            f"diversity={dialect_analysis['diversity']:.2%}"
                        )
            except Exception as e:
                logger.debug(f"[LANGUAGE_TEACHER] Dialect analysis failed: {e}")
        
        # Log periodically
        if generation % 10 == 0:
            logger.info(
                f"[LANGUAGE_TEACHER] Gen {generation}: Taught {organisms_taught}/{len(organisms)} organisms, "
                f"{total_words} words assigned, {self.discoveries_this_generation} discoveries"
            )
        
        return result
    
    def _perform_quality_review(self, generation: int):
        """
        Perform system-wide quality review of discovered relationships.
        
        Strengthens high-quality ones, weakens low-quality ones, prunes very weak ones.
        GAP 7 FIX: Updates learning_confidence based on relationship quality.
        """
        if not self.knowledge_web:
            return
        
        logger.info(f"[LANGUAGE_TEACHER] Performing quality review at generation {generation}")
        
        strengthened = 0
        weakened = 0
        pruned = 0
        total_quality_score = 0.0
        rated_count = 0
        
        for relation in self.knowledge_web.discovered_relations:
            if relation.is_seeded:
                continue  # Skip seeded relationships
            
            total_uses = relation.success_count + relation.failure_count
            if total_uses == 0:
                continue  # Skip unused relationships
            
            success_rate = relation.success_count / total_uses
            failure_rate = relation.failure_count / total_uses
            
            # Track quality for learning_confidence
            total_quality_score += success_rate
            rated_count += 1
            
            # Strengthen high-quality relationships
            if success_rate > 0.6:
                relation.strength = min(1.0, relation.strength + 0.05 * success_rate)
                relation.confidence = min(1.0, relation.confidence + 0.1 * success_rate)
                strengthened += 1
            
            # Weaken low-quality relationships
            if failure_rate > 0.4:
                relation.strength = max(0.1, relation.strength - 0.1 * failure_rate)
                relation.confidence = max(0.0, relation.confidence - 0.15 * failure_rate)
                weakened += 1
        
        # GAP 7 FIX: Update learning_confidence based on overall quality
        # This transitions the system from hardcoded to learned word selection
        if rated_count > 0:
            avg_quality = total_quality_score / rated_count
            # Smoothly update confidence (exponential moving average)
            self.learning_confidence = 0.9 * self.learning_confidence + 0.1 * avg_quality
            
            # Log if confidence crosses the min_confidence threshold
            if self.learning_confidence >= self.min_confidence_for_use:
                logger.info(f"[LANGUAGE_TEACHER] Learning confidence {self.learning_confidence:.3f} >= "
                           f"min_confidence {self.min_confidence_for_use:.3f} - using learned relationships")
        
        # Pruning is handled by decay_relationships, but we log the review
        logger.info(f"[LANGUAGE_TEACHER] Quality review complete: {strengthened} strengthened, "
                   f"{weakened} weakened, learning_confidence={self.learning_confidence:.3f}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get teaching statistics."""
        stats = dict(self.stats)
        # GAP 7 FIX: Include learning_confidence in stats
        stats['learning_confidence'] = self.learning_confidence
        stats['min_confidence_for_use'] = self.min_confidence_for_use
        stats['using_learned'] = self.learning_confidence >= self.min_confidence_for_use
        return stats
    
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

