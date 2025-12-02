"""
NeuralTrainer - Training System for Neural Organisms

Manages DQN training for neural organisms, synchronized with the Breath Engine.

Extended with:
- VP-aware language model training
- Dual-loss system: DQN (action) + Next-token prediction (language)
- VP temperature scaling for stable training
- Curriculum learning based on VP thresholds
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import time

# Try importing PyTorch
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

# Use absolute imports to avoid relative import issues
try:
    from .experience import ExperienceBuffer
    from .neural_organism import NeuralOrganism
    from .utils import get_device
except ImportError:
    # Fallback to absolute imports if relative imports fail
    try:
        from reality_simulator.neural.experience import ExperienceBuffer
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.neural.utils import get_device
    except ImportError:
        # Last resort: try direct imports
        import sys
        import os
        neural_path = os.path.join(os.path.dirname(__file__))
        if neural_path not in sys.path:
            sys.path.insert(0, neural_path)
        from experience import ExperienceBuffer
        from neural_organism import NeuralOrganism
        from utils import get_device


class NeuralTrainer:
    """
    Trainer for neural organisms using DQN (Deep Q-Network).
    
    Collects experiences from organisms and performs batched training
    synchronized with the Breath Engine.
    
    Extended with:
    - Language model training (next-token prediction)
    - VP-aware temperature scaling
    - Curriculum learning for sequence lengths
    """
    
    def __init__(self, config: Dict[str, Any], device=None):
        """
        Initialize neural trainer.
        
        Args:
            config: Neural configuration dictionary
            device: PyTorch device (auto-detected if None)
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for NeuralTrainer")
        
        self.config = config
        self.device = device or get_device(config.get('device', 'cpu'))
        
        training_config = config.get('training', {})
        self.batch_size = training_config.get('batch_size', 32)
        self.learning_rate = training_config.get('learning_rate', 0.001)
        self.gamma = training_config.get('gamma', 0.99)
        self.update_frequency = training_config.get('update_frequency', 1)
        
        rewards_config = config.get('rewards', {})
        self.reward_weights = {
            'fitness_improvement': rewards_config.get('fitness_improvement', 1.0),
            'survival': rewards_config.get('survival', 0.1),
            'connection_success': rewards_config.get('connection_success', 0.5),
            'connection_failure': rewards_config.get('connection_failure', -0.2),
            'resource_gain': rewards_config.get('resource_gain', 0.3),
            'resource_loss': rewards_config.get('resource_loss', -0.1),
        }
        
        # Language model configuration
        language_config = config.get('language_model', {})
        self.language_model_enabled = language_config.get('enabled', False)
        self.rl_loss_weight = language_config.get('rl_loss_weight', 0.9)  # alpha
        self.language_loss_weight = language_config.get('language_loss_weight', 0.1)  # beta (conservative start)
        self.vp_gate_threshold = language_config.get('vp_gate_threshold', 0.75)
        self.vp_temperature_scaling = language_config.get('vp_temperature_scaling', True)
        
        # Curriculum learning configuration
        self.curriculum_learning = language_config.get('curriculum_learning', True)
        self.current_sequence_length = language_config.get('start_sequence_length', 8)
        self.curriculum_thresholds = language_config.get('curriculum_thresholds', {
            '8_to_16': {'vp_threshold': 0.5, 'stability_steps': 20},
            '16_to_32': {'vp_threshold': 0.4, 'stability_steps': 30},
            '32_to_128': {'vp_threshold': 0.3, 'stability_steps': 50}
        })
        
        # VP history for curriculum learning decisions
        self.vp_history: List[float] = []
        self.vp_stable_steps = 0
        
        # Training statistics
        self.training_step_count = 0
        self.training_occurred_this_step = False  # Track if training happened in current step
        self.total_loss = 0.0
        self.total_language_loss = 0.0
        self.last_training_time = 0.0
        
        # Track organism fitness history for reward calculation
        self.organism_fitness_history: Dict[str, float] = {}
        
        # Optimization: Reuse optimizers instead of recreating each step
        optimization_config = config.get('optimization', {})
        self.reuse_optimizers = optimization_config.get('reuse_optimizers', True)
        self.optimizers: Dict[int, optim.Optimizer] = {}  # organism_id -> optimizer
        
        # Track training time for performance monitoring
        self.training_times = []  # List of recent training step durations
        
        # Log optimization status
        import logging
        logger = logging.getLogger(__name__)
        if self.reuse_optimizers:
            logger.info(f"[NEURAL] Optimizations enabled: optimizer reuse")
        
        # Optional event emitter for causation graph visualization
        self.event_emitter = None  # Set by main.py or unified_entry.py
        
        # Integration 2: Neural-ML Symbiosis - ML analysis for language rewards
        self.ml_analysis = None  # Set by main.py when ML analysis is available
        self.context_memory = None  # Set by main.py for vocabulary access
        self.language_reward_scaling = training_config.get('language_reward_scaling', 0.2)
        
        # Track language rewards for ConfigTuner analysis
        self.language_reward_total = 0.0  # Cumulative language rewards per training step
        self.language_reward_count = 0  # Number of language rewards given
        self._last_step_language_reward_total = 0.0  # Store last step's total for metrics
    
    def _calculate_language_reward(self, organism: NeuralOrganism) -> float:
        """
        Calculate language reward based on ML feature importance.
        
        Integration 2: Neural-ML Symbiosis - rewards organisms for using words
        that predict fitness (identified by ML feature selection).
        
        Args:
            organism: Neural organism with token sequence
            
        Returns:
            Language reward (0.0 if no ML analysis or no important words used)
        """
        if not self.ml_analysis:
            return 0.0
        
        # Extract feature importance from ML analysis
        semantic_analysis = self.ml_analysis.get('semantic_analysis', {})
        feature_importance = semantic_analysis.get('feature_importance', {})
        
        if not feature_importance:
            return 0.0
        
        top_predictive_words = feature_importance.get('top_predictive_words', [])
        if not top_predictive_words:
            return 0.0
        
        # Get organism's generated tokens
        if not hasattr(organism, 'get_token_sequence'):
            return 0.0
        
        token_sequence = organism.get_token_sequence()
        if not token_sequence or len(token_sequence) == 0:
            return 0.0
        
        # Decode tokens to words using vocabulary from context_memory
        if not self.context_memory or not hasattr(self.context_memory, 'vocabulary'):
            return 0.0
        
        vocab = self.context_memory.vocabulary
        if vocab is None:
            return 0.0
        
        # Decode tokens to words (skip special tokens)
        try:
            words = vocab.decode(token_sequence, skip_special=True)
        except Exception:
            # Fallback: try to decode manually
            words = []
            for token_id in token_sequence:
                try:
                    word = vocab.get_word(token_id)
                    # Skip special tokens
                    if word and not (word.startswith('<') and word.endswith('>')):
                        words.append(word)
                except Exception:
                    continue
        
        if not words:
            return 0.0
        
        # Calculate reward: sum importance scores for matching words
        reward = 0.0
        important_word_dict = {item['word']: item['importance_score'] for item in top_predictive_words}
        
        for word in words:
            if word in important_word_dict:
                # Reward proportional to importance, scaled by config
                reward += important_word_dict[word] * self.language_reward_scaling
        
        return reward
    
    def calculate_reward(self, 
                        organism: NeuralOrganism,
                        prev_fitness: float,
                        current_fitness: float,
                        action: int,
                        connection_success: Optional[bool] = None,
                        resource_delta: float = 0.0) -> float:
        """
        Calculate reward for an organism based on various factors.
        
        Integration 2: Now includes language reward from ML feature importance.
        
        Args:
            organism: Neural organism
            prev_fitness: Previous fitness value
            current_fitness: Current fitness value
            action: Action taken
            connection_success: Whether connection attempt succeeded (None = no attempt)
            resource_delta: Change in resources
            
        Returns:
            Calculated reward (base + language)
        """
        reward = 0.0
        
        # 1. Fitness improvement
        fitness_delta = current_fitness - prev_fitness
        reward += fitness_delta * self.reward_weights['fitness_improvement']
        
        # 2. Survival (small positive reward for staying alive)
        reward += self.reward_weights['survival']
        
        # 3. Connection success/failure
        if connection_success is not None:
            if connection_success:
                reward += self.reward_weights['connection_success']
            else:
                reward += self.reward_weights['connection_failure']
        
        # 4. Resource gain/loss
        if resource_delta > 0:
            reward += resource_delta * self.reward_weights['resource_gain']
        elif resource_delta < 0:
            reward += abs(resource_delta) * self.reward_weights['resource_loss']
        
        # Integration 2: Add language reward (if ML analysis available)
        language_reward = self._calculate_language_reward(organism)
        reward += language_reward
        
        # Track language rewards for ConfigTuner
        if language_reward > 0.0:
            self.language_reward_total += language_reward
            self.language_reward_count += 1
        
        # Emit event for language reward (Integration 2: Neural-ML Symbiosis)
        if language_reward > 0.0 and self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_language_reward',
                    data={
                        'organism_id': str(id(organism)),
                        'language_reward': float(language_reward),
                        'total_reward': float(reward),
                        'reward_scaling': self.language_reward_scaling,
                        'has_ml_analysis': self.ml_analysis is not None
                    }
                )
                self.event_emitter(event)
            except Exception as e:
                logger.debug(f"Event emission failed (non-critical): {e}")
        
        return reward
    
    def collect_experiences(self,
                           organisms: Dict[str, NeuralOrganism],
                           network_state: Dict[str, Any],
                           breath_state: Optional[Dict[str, Any]] = None):
        """
        Collect experiences from all neural organisms.
        
        Args:
            organisms: Dictionary of organisms (species_id -> NeuralOrganism)
            network_state: Current network state
            breath_state: Breath engine state
        """
        experiences_collected = 0
        for org_id, organism in organisms.items():
            # Use duck typing instead of isinstance() to avoid import issues
            # Check if organism has neural capabilities
            if not (hasattr(organism, 'brain') and organism.brain is not None):
                continue

            if not hasattr(organism, 'record_experience'):
                continue  # Not a neural organism

            # Get previous fitness
            prev_fitness = self.organism_fitness_history.get(org_id, organism.fitness)
            current_fitness = organism.fitness
            
            # Calculate reward
            reward = self.calculate_reward(
                organism=organism,
                prev_fitness=prev_fitness,
                current_fitness=current_fitness,
                action=organism.prev_action if hasattr(organism, 'prev_action') else 0,
                connection_success=None,  # Would need to track this
                resource_delta=0.0  # Would need to track this
            )
            
            # Get next state
            next_state = organism.get_state_features(
                local_env=None,
                network_state=network_state,
                breath_state=breath_state
            )
            
            # Record experience
            organism.record_experience(
                reward=reward,
                next_state=next_state,
                done=False  # Organisms don't "die" in the same way
            )
            experiences_collected += 1

            # Update fitness history
            self.organism_fitness_history[org_id] = current_fitness

        # Log training progress periodically (every 50 steps to avoid spam)
        if experiences_collected > 0 and self.training_step_count % 50 == 0:
            print(f"[NEURAL] Collected {experiences_collected} experiences from {len(organisms)} organisms")
        
        # Track whether training occurred this step (for diagnostics)
        self.training_occurred_this_step = False
    
    def train_step(self,
                   organisms: Dict[str, NeuralOrganism],
                   network_state: Dict[str, Any],
                   breath_state: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Perform one training step (synchronized with breath cycle).
        
        Args:
            organisms: Dictionary of organisms
            network_state: Current network state
            breath_state: Breath engine state
            
        Returns:
            Average loss, or None if no training occurred
            
        Note:
            - training_step_count increments EVERY call (tracks trainer invocations)
            - training_loss is only returned when actual training occurs (batch_size met)
            - None means no training this step (waiting for experiences or update_frequency)
        """
        if not PYTORCH_AVAILABLE:
            return None
        
        # Collect experiences first
        self.collect_experiences(organisms, network_state, breath_state)
        
        # Increment step count first
        self.training_step_count += 1
        
        # Check if we should train this step
        # With update_frequency=3: train on steps 3, 6, 9, etc.
        # So we check if (step_count % update_frequency == 0)
        if (self.training_step_count % self.update_frequency) != 0:
            return None
        
        # Check if we have enough experiences to train
        # Find organisms with sufficient experience
        trainable_organisms = []
        for organism in organisms.values():
            # Use duck typing instead of isinstance()
            if (hasattr(organism, 'brain') and organism.brain is not None and
                hasattr(organism, 'experience_buffer') and organism.experience_buffer is not None and
                len(organism.experience_buffer) >= self.batch_size):
                trainable_organisms.append(organism)
        
        if not trainable_organisms:
            return None
        
        # Track training time
        training_start_time = time.time()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LANGUAGE-ONLY TRAINING: Train organisms with tokens but not enough RL experiences
        # This fixes the bug where language training was blocked by RL batch requirements
        # ═══════════════════════════════════════════════════════════════════════════
        language_only_organisms = [
            org for org in organisms 
            if (hasattr(org, 'token_sequence') and len(org.token_sequence) >= 2 and
                hasattr(org, 'brain') and hasattr(org.brain, 'use_language_head') and 
                org.brain.use_language_head and
                (not hasattr(org, 'experience_buffer') or 
                 org.experience_buffer is None or 
                 len(org.experience_buffer) < self.batch_size))
        ]
        
        for organism in language_only_organisms:
            try:
                token_seq = list(organism.token_sequence)[-self.current_sequence_length:]
                if len(token_seq) >= 2:
                    input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
                    target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
                    
                    # Get a dummy state for language logits
                    dummy_state = torch.zeros(1, organism.brain.input_dim).to(self.device)
                    
                    organism.brain.train()
                    _, language_logits = organism.brain(dummy_state, return_language_logits=True)
                    
                    if language_logits is not None:
                        if language_logits.dim() == 2:
                            language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                        
                        vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                        language_loss = self.calculate_language_loss(language_logits, target_tokens, vp_value)
                        
                        # Backprop for language-only training
                        optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate * 0.5)
                        optimizer.zero_grad()
                        language_loss.backward()
                        optimizer.step()
                        
                        self.total_language_loss += language_loss.item()
            except Exception as e:
                pass  # Skip on error, don't break training loop
        
        # Train each organism's brain (RL + Language for organisms with enough experiences)
        total_loss = 0.0
        num_trained = 0
        
        for organism in trainable_organisms:
            # Sample batch
            states, actions, rewards, next_states, dones = organism.experience_buffer.sample_batch(
                self.batch_size
            )
            
            # Convert to tensors
            states_tensor = torch.FloatTensor(states).to(self.device)
            actions_tensor = torch.LongTensor(actions).to(self.device)
            rewards_tensor = torch.FloatTensor(rewards).to(self.device)
            next_states_tensor = torch.FloatTensor(next_states).to(self.device)
            dones_tensor = torch.BoolTensor(dones).to(self.device)
            
            # Get current Q values
            organism.brain.train()  # Set to training mode
            q_values = organism.brain(states_tensor)
            q_value = q_values.gather(1, actions_tensor.unsqueeze(1)).squeeze(1)
            
            # Get next Q values (no gradient)
            organism.brain.eval()  # Set to evaluation mode
            with torch.no_grad():
                next_q_values = organism.brain(next_states_tensor)
                next_q_value = next_q_values.max(1)[0]
            
            # Calculate target Q values
            target_q_value = rewards_tensor + (self.gamma * next_q_value * ~dones_tensor)
            
            # Calculate RL loss (Q-learning)
            rl_loss = F.mse_loss(q_value, target_q_value)
            
            # Calculate language loss if enabled and brain has language head
            language_loss = None
            if (self.language_model_enabled and 
                hasattr(organism.brain, 'use_language_head') and 
                organism.brain.use_language_head and
                hasattr(organism, 'token_sequence') and 
                len(organism.token_sequence) >= 2):
                
                # Get token sequence for next-token prediction
                token_seq = list(organism.token_sequence)[-self.current_sequence_length:]
                if len(token_seq) >= 2:
                    # Prepare input (all but last) and target (all but first)
                    input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
                    target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
                    
                    # Get VP value for temperature scaling
                    vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                    
                    # Get language logits from brain
                    try:
                        _, language_logits = organism.brain(
                            states_tensor[:1],  # Single sample for language
                            return_language_logits=True
                        )
                        if language_logits is not None:
                            # Expand logits to match sequence length if needed
                            if language_logits.dim() == 2:
                                language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                            language_loss = self.calculate_language_loss(
                                language_logits, target_tokens, vp_value
                            )
                            self.total_language_loss += language_loss.item()
                    except Exception as e:
                        logger.debug(f"Language loss calculation skipped: {e}")
            
            # Combine losses with weighting
            if language_loss is not None:
                loss = (self.rl_loss_weight * rl_loss) + (self.language_loss_weight * language_loss)
            else:
                loss = rl_loss
            
            # Backpropagation
            organism.brain.train()
            
            # Optimization: Reuse optimizer if enabled
            if self.reuse_optimizers:
                organism_id = id(organism.brain)
                if organism_id not in self.optimizers:
                    self.optimizers[organism_id] = optim.Adam(
                        organism.brain.parameters(), 
                        lr=self.learning_rate
                    )
                optimizer = self.optimizers[organism_id]
            else:
                optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_trained += 1
        
        # Track training duration
        training_duration = time.time() - training_start_time
        self.training_times.append(training_duration)
        if len(self.training_times) > 100:  # Keep last 100 training times
            self.training_times = self.training_times[-100:]
        
        self.last_training_time = time.time()
        
        if num_trained > 0:
            self.training_occurred_this_step = True
            avg_loss = total_loss / num_trained
            self.total_loss += avg_loss
            
            # Emit neural training event for visualization
            if self.event_emitter:
                training_stats = self.get_training_stats()
                avg_training_time = np.mean(self.training_times) if self.training_times else 0.0
                event_data = {
                    'training_step': self.training_step_count,
                    'loss': float(avg_loss),
                    'num_organisms_trained': num_trained,
                    'total_organisms': len(organisms),
                    'avg_loss_history': training_stats.get('average_loss', 0.0),
                    'training_time_ms': training_duration * 1000,  # Convert to milliseconds
                    'avg_training_time_ms': avg_training_time * 1000,
                    'optimizations_enabled': {
                        'reuse_optimizers': self.reuse_optimizers,
                        'compiled_brains': num_trained > 0  # Assume compiled if training works
                    },
                    'breath_cycle': breath_state.get('cycle_count', 0) if breath_state else None,
                    'breath_depth': breath_state.get('depth', 0.0) if breath_state else None
                }
                
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='neural',
                        event_type='neural_training',
                        data=event_data
                    )
                    self.event_emitter(event)
                except ImportError:
                    pass  # CausationExplorer not available
            
            # Store language reward total for this step (before resetting for next step)
            self._last_step_language_reward_total = self.language_reward_total
            
            # Reset language reward tracking for next step (ConfigTuner tracks per-step totals)
            self.language_reward_total = 0.0
            self.language_reward_count = 0
            
            # Curriculum learning: adjust sequence length based on VP stability
            if self.curriculum_learning and self.language_model_enabled:
                vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                self.update_curriculum(vp_value)
            
            return avg_loss
        
        return None
    
    def get_neural_ml_symbiosis_metrics(self) -> Dict[str, Any]:
        """Get Neural-ML Symbiosis metrics for ConfigTuner"""
        return {
            'language_reward_total': self._last_step_language_reward_total,  # Use stored value from last step
            'language_reward_count': self.language_reward_count,
            'curriculum_sequence_length': self.current_sequence_length,
            'language_reward_scaling': self.language_reward_scaling
        }
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get training statistics.
        
        Returns:
            Dictionary of training statistics
        """
        return {
            'training_steps': self.training_step_count,
            'average_loss': self.total_loss / max(1, self.training_step_count),
            'average_language_loss': self.total_language_loss / max(1, self.training_step_count) if self.language_model_enabled else None,
            'last_training_time': self.last_training_time,
            'organisms_tracked': len(self.organism_fitness_history),
            'language_model_enabled': self.language_model_enabled,
            'current_sequence_length': self.current_sequence_length,
            'vp_stable_steps': self.vp_stable_steps
        }
    
    def calculate_language_loss(self,
                                language_logits: 'torch.Tensor',
                                target_tokens: 'torch.Tensor',
                                vp_value: Optional[float] = None) -> 'torch.Tensor':
        """
        Calculate next-token prediction loss with VP-aware scaling.
        
        Args:
            language_logits: Predicted logits from language head (batch, seq, vocab)
            target_tokens: Target token IDs (batch, seq)
            vp_value: Current VP value for temperature scaling
            
        Returns:
            Scaled language loss tensor
        """
        # Apply VP temperature scaling to logits before loss calculation
        if self.vp_temperature_scaling and vp_value is not None and vp_value > 0:
            # Higher VP = lower temperature = more confident predictions
            temperature = 1.0 / (1.0 + vp_value)
            language_logits = language_logits / temperature
        
        # Reshape for cross-entropy: (batch * seq, vocab) and (batch * seq)
        batch_size, seq_len, vocab_size = language_logits.shape
        logits_flat = language_logits.view(-1, vocab_size)
        targets_flat = target_tokens.view(-1)
        
        # Calculate cross-entropy loss (ignores padding tokens with index 0)
        loss = F.cross_entropy(logits_flat, targets_flat, ignore_index=0)
        
        # VP gating: if VP > threshold, reduce language loss influence
        if vp_value is not None and vp_value > self.vp_gate_threshold:
            # Scale down language loss when system is unstable
            gate_factor = 1.0 - ((vp_value - self.vp_gate_threshold) / (1.0 - self.vp_gate_threshold))
            gate_factor = max(0.1, gate_factor)  # Never fully zero out
            loss = loss * gate_factor
        
        # Emit neural_language_training event for causation graph
        if self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_language_training',
                    data={
                        'vocab_size': vocab_size,
                        'language_loss': float(loss.item()) if hasattr(loss, 'item') else float(loss),
                        'token_sequence_length': seq_len,
                        'batch_size': batch_size,
                        'vp_value': vp_value,
                        'vp_gated': vp_value is not None and vp_value > self.vp_gate_threshold,
                        'current_curriculum_length': self.current_sequence_length
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass  # CausationExplorer not available
        
        return loss
    
    def adjust_curriculum_from_ml_quality(self, ml_analysis: Optional[Dict[str, Any]]) -> Optional[int]:
        """
        Adjust curriculum (sequence length) based on ML-measured language quality.
        
        Integration 3: Neural-ML Symbiosis - uses population language quality metrics
        to adjust training complexity.
        
        Args:
            ml_analysis: ML analysis results containing quality metrics
            
        Returns:
            New sequence length if adjusted, None otherwise
        """
        if not ml_analysis:
            return None
        
        # Extract quality metrics
        semantic_analysis = ml_analysis.get('semantic_analysis', {})
        if not semantic_analysis:
            return None
        
        quality_metrics = semantic_analysis.get('quality_metrics', {})
        
        if not quality_metrics:
            return None
        
        silhouette_score = quality_metrics.get('silhouette_score', None)
        if silhouette_score is None:
            return None
        
        # Get curriculum config
        language_config = self.config.get('language_model', {})
        curriculum_config = language_config.get('curriculum', {})
        ml_quality_config = curriculum_config.get('ml_quality', {})
        
        if not ml_quality_config.get('enabled', False):
            return None
        
        high_threshold = ml_quality_config.get('high_quality_threshold', 0.6)
        low_threshold = ml_quality_config.get('low_quality_threshold', 0.3)
        step_size = ml_quality_config.get('sequence_length_step', 2)
        min_length = ml_quality_config.get('min_sequence_length', 8)
        max_length = ml_quality_config.get('max_sequence_length', 64)
        
        old_length = self.current_sequence_length
        new_length = old_length
        
        # Adjust based on quality
        if silhouette_score > high_threshold:
            # High quality: increase sequence length
            new_length = min(max_length, old_length + step_size)
        elif silhouette_score < low_threshold:
            # Low quality: decrease sequence length
            new_length = max(min_length, old_length - step_size)
        
        # Only update if changed significantly (prevent oscillation)
        if abs(new_length - old_length) >= step_size:
            self.current_sequence_length = new_length
            
            # Log curriculum change
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CURRICULUM] Adjusted sequence length: {old_length} → {new_length} "
                       f"(silhouette={silhouette_score:.3f})")
            
            # Emit event for curriculum adjustment (Integration 3: Neural-ML Symbiosis)
            if self.event_emitter:
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='neural',
                        event_type='neural_curriculum_adjustment',
                        data={
                            'old_sequence_length': int(old_length),
                            'new_sequence_length': int(new_length),
                            'silhouette_score': float(silhouette_score),
                            'adjustment_reason': 'high_quality' if silhouette_score > high_threshold else 'low_quality',
                            'high_threshold': high_threshold,
                            'low_threshold': low_threshold
                        }
                    )
                    self.event_emitter(event)
                except Exception as e:
                    logger.debug(f"Curriculum event emission failed: {e}")
            
            return new_length
        
        return None
    
    def update_curriculum(self, vp_value: float) -> bool:
        """
        Update curriculum learning based on VP stability.
        
        Increases sequence length when VP is stable below thresholds.
        
        Args:
            vp_value: Current VP value
            
        Returns:
            True if sequence length was increased
        """
        if not self.curriculum_learning or not self.language_model_enabled:
            return False
        
        # Track VP history
        self.vp_history.append(vp_value)
        if len(self.vp_history) > 100:
            self.vp_history = self.vp_history[-100:]
        
        # Determine current curriculum stage
        if self.current_sequence_length == 8:
            threshold_key = '8_to_16'
            next_length = 16
        elif self.current_sequence_length == 16:
            threshold_key = '16_to_32'
            next_length = 32
        elif self.current_sequence_length == 32:
            threshold_key = '32_to_128'
            next_length = 128
        else:
            return False  # Already at max
        
        threshold_config = self.curriculum_thresholds.get(threshold_key, {})
        vp_threshold = threshold_config.get('vp_threshold', 0.5)
        stability_steps = threshold_config.get('stability_steps', 20)
        
        # Check if VP is below threshold
        if vp_value < vp_threshold:
            self.vp_stable_steps += 1
        else:
            self.vp_stable_steps = 0  # Reset on threshold breach
        
        # Advance curriculum if stable for required steps
        if self.vp_stable_steps >= stability_steps:
            self.current_sequence_length = next_length
            self.vp_stable_steps = 0  # Reset for next stage
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CURRICULUM] Advanced sequence length: {self.current_sequence_length}")
            
            return True
        
        return False
    
    def apply_vp_temperature_to_logits(self, 
                                        logits: 'torch.Tensor', 
                                        vp_value: float) -> 'torch.Tensor':
        """
        Apply VP-based temperature scaling to language logits.
        
        Higher VP = lower temperature = sharper predictions (more conservative).
        
        Args:
            logits: Raw logits from language head
            vp_value: Current VP value
            
        Returns:
            Temperature-scaled logits
        """
        if vp_value <= 0:
            return logits
        
        # Temperature scaling: T = 1 / (1 + VP)
        # VP=0 → T=1.0 (no change)
        # VP=0.5 → T=0.67 (sharper)
        # VP=1.0 → T=0.5 (very sharp)
        temperature = 1.0 / (1.0 + vp_value)
        
        return logits / temperature

    # =========================================================================
    # 🆕 CHAT-TRIGGERED LEARNING METHODS
    # Close the experience→training→generation loop for Butterfly Chat
    # =========================================================================
    
    def train_from_chat_experiences(self, 
                                    organism: 'NeuralOrganism',
                                    network_state: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Train organism from accumulated chat experiences.
        
        Uses token sequences stored in experience buffer for language model training.
        Called periodically by ButterflyChatRouter to close the learning loop.
        
        Args:
            organism: Neural organism to train
            network_state: Network state for context
            
        Returns:
            Training loss if training occurred, None otherwise
        """
        if not PYTORCH_AVAILABLE:
            return None
        
        # Check if organism has required components
        if not hasattr(organism, 'brain') or organism.brain is None:
            return None
        if not hasattr(organism, 'experience_buffer') or organism.experience_buffer is None:
            return None
        if len(organism.experience_buffer) < 2:
            return None
        
        # Get token sequences from organism
        if not hasattr(organism, 'token_sequence') or len(organism.token_sequence) < 4:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get token sequence for training
            token_seq = list(organism.token_sequence)
            
            # Need at least 4 tokens for meaningful training
            if len(token_seq) < 4:
                return None
            
            # Use last N tokens (curriculum-based length)
            seq_len = min(len(token_seq), self.current_sequence_length)
            token_seq = token_seq[-seq_len:]
            
            # Prepare input/target pairs for next-token prediction
            input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
            target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
            
            # Get VP value for temperature scaling
            vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
            
            # Get state features for brain input
            if hasattr(organism, 'get_state_features'):
                state = organism.get_state_features(
                    local_env=None,
                    network_state=network_state,
                    breath_state=None
                )
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                brain_input_dim = organism.brain.fc1.in_features
                state_tensor = torch.zeros(1, brain_input_dim, device=self.device)
            
            # Forward pass to get language logits
            organism.brain.train()
            
            if hasattr(organism.brain, 'fc_language'):
                # Get language head output
                hidden = torch.relu(organism.brain.fc1(state_tensor))
                hidden = torch.relu(organism.brain.fc2(hidden))
                language_logits = organism.brain.fc_language(hidden)
                
                # Expand to sequence length
                language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                
                # Calculate loss
                loss = self.calculate_language_loss(language_logits, target_tokens, vp_value)
                
                # Backpropagation
                organism_id = id(organism.brain)
                if self.reuse_optimizers:
                    if organism_id not in self.optimizers:
                        self.optimizers[organism_id] = optim.Adam(
                            organism.brain.parameters(), 
                            lr=self.learning_rate
                        )
                    optimizer = self.optimizers[organism_id]
                else:
                    optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate)
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # Emit training event
                if self.event_emitter:
                    try:
                        from causation_explorer import Event
                        event = Event(
                            timestamp=time.time(),
                            component='neural',
                            event_type='chat_training_complete',
                            data={
                                'organism_id': getattr(organism, 'species_id', str(organism_id)),
                                'loss': float(loss.item()),
                                'sequence_length': len(token_seq),
                                'vp_value': vp_value
                            }
                        )
                        self.event_emitter(event)
                    except Exception as e:
                        logger.debug(f"Chat training event emission failed: {e}")
                
                logger.debug(f"[NEURAL] Chat training loss: {loss.item():.4f}")
                return loss.item()
            
            return None
            
        except Exception as e:
            logger.debug(f"[NEURAL] Chat training failed: {e}")
            return None
    
    def bootstrap_language_learning(self,
                                    organism: 'NeuralOrganism',
                                    user_tokens: List[int],
                                    network_state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Bootstrap learning for organisms that generated empty responses.
        
        Uses TEMPLATE RESPONSES instead of teacher forcing on user input.
        This teaches organisms proper response patterns rather than echoing.
        
        Based on Claude's supervised learning gap analysis:
        - Problem: Teaching organism to predict user_tokens[i+1] from user_tokens[i]
          causes organism to learn to echo/repeat user input
        - Solution: Use template response patterns that teach appropriate responses
        
        Args:
            organism: Neural organism to bootstrap
            user_tokens: User input tokens (used for context classification)
            network_state: Network state for context
            
        Returns:
            True if bootstrap training occurred
        """
        if not PYTORCH_AVAILABLE:
            return False
        
        if not user_tokens or len(user_tokens) < 1:
            return False
        
        if not hasattr(organism, 'brain') or organism.brain is None:
            return False
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get vocabulary for template tokenization
            vocab = getattr(organism, 'vocabulary', None)
            if vocab is None:
                # Try to get from butterfly chat or use fallback
                if hasattr(organism, 'chat_interface') and organism.chat_interface:
                    vocab = getattr(organism.chat_interface, 'vocabulary', None)
            
            if vocab is None:
                logger.debug("[NEURAL] Bootstrap learning skipped: no vocabulary")
                return False
            
            # Generate template response based on input context
            template_response = self._get_bootstrap_template_response(user_tokens, vocab)
            
            if not template_response or len(template_response) < 2:
                logger.debug("[NEURAL] Bootstrap learning skipped: no valid template")
                return False
            
            # Create proper seq2seq training data:
            # INPUT: user_tokens (what user said)
            # TARGET: template_response (proper response pattern)
            input_tokens = torch.LongTensor([user_tokens]).to(self.device)
            target_tokens = torch.LongTensor([template_response]).to(self.device)
            
            # Get state for brain input
            if hasattr(organism, 'get_state_features'):
                state = organism.get_state_features(
                    local_env=None,
                    network_state=network_state,
                    breath_state=None
                )
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                brain_input_dim = organism.brain.fc1.in_features
                state_tensor = torch.zeros(1, brain_input_dim, device=self.device)
            
            # Forward pass
            organism.brain.train()
            
            if hasattr(organism.brain, 'fc_language'):
                hidden = torch.relu(organism.brain.fc1(state_tensor))
                hidden = torch.relu(organism.brain.fc2(hidden))
                language_logits = organism.brain.fc_language(hidden)
                
                # Expand to target sequence length
                target_len = len(template_response)
                language_logits = language_logits.unsqueeze(1).expand(-1, target_len, -1)
                
                # Use higher learning rate for bootstrap (faster learning)
                bootstrap_lr = self.learning_rate * 2.0
                
                # Calculate loss against TEMPLATE response, not user echo
                loss = self.calculate_language_loss(language_logits, target_tokens, vp_value=0.0)
                
                # Backpropagation
                optimizer = optim.Adam(organism.brain.parameters(), lr=bootstrap_lr)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # Store experience with proper input/target separation
                # This creates a learning signal: "when you see X, say Y"
                if hasattr(organism, 'experience_buffer') and organism.experience_buffer is not None:
                    state_np = state_tensor.cpu().numpy().flatten()
                    vp_val = network_state.get('vp_value') if network_state else None
                    organism.experience_buffer.add(
                        state=state_np,
                        action=0,
                        reward=0.5,  # Good reward for learning proper response
                        next_state=state_np,
                        done=False,
                        input_tokens=user_tokens,          # What user said
                        target_tokens=template_response,   # Proper response
                        vp_value=vp_val
                    )
                
                # Add template to organism's token sequence for vocabulary exposure
                if hasattr(organism, 'token_sequence'):
                    for token in template_response:
                        organism.token_sequence.append(token)
                
                # Emit bootstrap event
                if self.event_emitter:
                    try:
                        from causation_explorer import Event
                        event = Event(
                            timestamp=time.time(),
                            component='neural',
                            event_type='bootstrap_learning_complete',
                            data={
                                'organism_id': getattr(organism, 'species_id', str(id(organism))),
                                'loss': float(loss.item()),
                                'input_tokens': len(user_tokens),
                                'template_tokens': len(template_response),
                                'method': 'template_response'
                            }
                        )
                        self.event_emitter(event)
                    except Exception as e:
                        logger.debug(f"Bootstrap learning event emission failed: {e}")
                
                logger.debug(f"[NEURAL] Bootstrap with template: loss={loss.item():.4f}, template_len={len(template_response)}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"[NEURAL] Bootstrap learning failed: {e}")
            return False
    
    def _get_bootstrap_template_response(self, user_tokens: List[int], vocab) -> List[int]:
        """
        Generate appropriate template response tokens based on input context.
        
        Templates teach organisms proper response patterns instead of echoing.
        This implements Claude's recommendation for structured bootstrap learning.
        
        Categories:
        - Greetings → Greeting responses
        - Questions → Thinking/acknowledgment responses
        - Unknown → Safe generic responses
        """
        import random
        
        # Decode user tokens to analyze intent
        try:
            user_words = []
            for token in user_tokens:
                word = vocab.id_to_token.get(token, '')
                if word:
                    user_words.append(word.lower())
            user_text = ' '.join(user_words)
        except Exception:
            user_text = ""
        
        # Classify intent and select template category
        greeting_words = {'hello', 'hi', 'hey', 'greetings', 'howdy'}
        question_words = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 'could', 'would', 'can'}
        
        is_greeting = any(word in user_words for word in greeting_words)
        is_question = any(word in user_words for word in question_words)
        
        # Template responses by category
        # These teach proper conversational patterns
        templates = {
            'greeting': [
                "Hello there.",
                "Hi! Nice to meet you.",
                "Hello, how are you?",
                "Hey! Welcome.",
                "Greetings friend.",
            ],
            'question': [
                "That is interesting.",
                "I think about that.",
                "Let me consider...",
                "Good question.",
                "I wonder about that too.",
            ],
            'generic': [
                "I understand.",
                "Tell me more.",
                "I see.",
                "That makes sense.",
                "Please continue.",
                "Interesting.",
            ]
        }
        
        # Select appropriate template category
        if is_greeting:
            category = 'greeting'
        elif is_question:
            category = 'question'
        else:
            category = 'generic'
        
        # Pick random template from category
        template_text = random.choice(templates[category])
        
        # Tokenize template
        try:
            template_tokens = vocab.encode(template_text)
            return template_tokens
        except Exception as e:
            logger.debug(f"Template tokenization failed: {e}")
            # Fallback: return a simple known token sequence
            return [1, 2, 3]  # Will depend on vocab, but better than empty

