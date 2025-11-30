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
    
    def calculate_reward(self, 
                        organism: NeuralOrganism,
                        prev_fitness: float,
                        current_fitness: float,
                        action: int,
                        connection_success: Optional[bool] = None,
                        resource_delta: float = 0.0) -> float:
        """
        Calculate reward for an organism based on various factors.
        
        Args:
            organism: Neural organism
            prev_fitness: Previous fitness value
            current_fitness: Current fitness value
            action: Action taken
            connection_success: Whether connection attempt succeeded (None = no attempt)
            resource_delta: Change in resources
            
        Returns:
            Calculated reward
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
        
        # Train each organism's brain
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
            
            # Calculate loss
            loss = F.mse_loss(q_value, target_q_value)
            
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
            
            return avg_loss
        
        return None
    
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

