"""
Experience Replay Buffer

Stores and samples experiences for reinforcement learning.
Extended with token sequence storage for language model training.
"""

import numpy as np
from typing import List, Tuple, Optional
from collections import deque
import random


class Experience:
    """
    Single experience tuple for DQN + Language Model training.
    
    Extended fields:
    - token_sequence: Token IDs for language model training (optional, backward compat)
    - input_tokens: User input tokens for seq2seq training (optional)
    - target_tokens: Desired response tokens for seq2seq training (optional)
    - vp_value: VP state at experience time (optional)
    
    For proper supervised learning, use input_tokens/target_tokens separation.
    token_sequence is maintained for backward compatibility and represents
    input_tokens + target_tokens concatenated.
    """
    
    def __init__(self, state: np.ndarray, action: int, reward: float,
                 next_state: np.ndarray, done: bool,
                 token_sequence: Optional[List[int]] = None,
                 input_tokens: Optional[List[int]] = None,
                 target_tokens: Optional[List[int]] = None,
                 vp_value: Optional[float] = None):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done
        # Language model extensions - explicit input/target separation
        self.input_tokens = input_tokens if input_tokens is not None else []
        self.target_tokens = target_tokens if target_tokens is not None else []
        # Backward compatibility: token_sequence = input + target if not explicitly provided
        if token_sequence is not None:
            self.token_sequence = token_sequence
        else:
            self.token_sequence = self.input_tokens + self.target_tokens
        self.vp_value = vp_value
    
    def has_seq2seq_data(self) -> bool:
        """Check if experience has proper input/target separation for seq2seq training."""
        return len(self.input_tokens) > 0 and len(self.target_tokens) > 0


class ExperienceBuffer:
    """
    Experience replay buffer for DQN training.
    
    Uses a circular buffer to store experiences and provides
    efficient batch sampling.
    
    Set capacity=0 or None for UNLIMITED growth (no experience loss).
    """
    
    def __init__(self, capacity: int = 0, state_dim: int = 25):
        """
        Initialize experience buffer.
        
        Args:
            capacity: Maximum number of experiences to store.
                      0 or None = UNLIMITED (recommended for maximum learning)
            state_dim: Dimension of state vectors (default: 25)
        """
        self.capacity = capacity if capacity and capacity > 0 else None
        self.state_dim = state_dim
        # None maxlen = unlimited growth, no experience is ever lost
        self.buffer: deque = deque(maxlen=self.capacity)
        self.size = 0
    
    def add(self, state: np.ndarray, action: int, reward: float,
            next_state: np.ndarray, done: bool,
            token_sequence: Optional[List[int]] = None,
            input_tokens: Optional[List[int]] = None,
            target_tokens: Optional[List[int]] = None,
            vp_value: Optional[float] = None):
        """
        Add experience to buffer.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
            token_sequence: Token IDs for language model (optional, backward compat)
            input_tokens: User input tokens for seq2seq training (optional)
            target_tokens: Desired response tokens for seq2seq training (optional)
            vp_value: VP value at experience time (optional)
        """
        experience = Experience(state, action, reward, next_state, done,
                               token_sequence=token_sequence,
                               input_tokens=input_tokens,
                               target_tokens=target_tokens,
                               vp_value=vp_value)
        self.buffer.append(experience)
        self.size = len(self.buffer)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """
        Sample a batch of experiences.
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            List of Experience objects
        """
        if self.size < batch_size:
            batch_size = self.size
        
        return random.sample(list(self.buffer), batch_size)
    
    def sample_batch(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, 
                                                      np.ndarray, np.ndarray, 
                                                      np.ndarray]:
        """
        Sample a batch and return as numpy arrays (backward compatible).
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            Tuple of (states, actions, rewards, next_states, dones) as numpy arrays
        """
        experiences = self.sample(batch_size)
        
        # Normalize states to consistent shape to prevent inhomogeneous array errors
        def normalize_state(state):
            """Ensure state is exactly state_dim float32 array."""
            if state is None:
                return np.zeros(self.state_dim, dtype=np.float32)
            state_arr = np.asarray(state, dtype=np.float32).flatten()
            if len(state_arr) < self.state_dim:
                # Pad with zeros
                padded = np.zeros(self.state_dim, dtype=np.float32)
                padded[:len(state_arr)] = state_arr
                return padded
            elif len(state_arr) > self.state_dim:
                # Truncate
                return state_arr[:self.state_dim]
            return state_arr
        
        def normalize_action(action):
            """Ensure action is a scalar int for discrete action space."""
            if isinstance(action, np.ndarray):
                # Continuous action - take argmax or first element
                if action.size == 1:
                    return int(action.item())
                return int(np.argmax(action))  # Convert continuous to discrete
            return int(action)
        
        states = np.array([normalize_state(e.state) for e in experiences], dtype=np.float32)
        actions = np.array([normalize_action(e.action) for e in experiences], dtype=np.int64)
        rewards = np.array([e.reward for e in experiences], dtype=np.float32)
        next_states = np.array([normalize_state(e.next_state) for e in experiences], dtype=np.float32)
        dones = np.array([e.done for e in experiences], dtype=bool)
        
        return states, actions, rewards, next_states, dones

    def sample_batch_with_tokens(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, 
                                                                   np.ndarray, np.ndarray, 
                                                                   np.ndarray, List[List[int]],
                                                                   List[Optional[float]]]:
        """
        Sample a batch including token sequences and VP values.
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            Tuple of (states, actions, rewards, next_states, dones, token_sequences, vp_values)
        """
        experiences = self.sample(batch_size)
        
        # Reuse normalize_state from sample_batch
        def normalize_state(state):
            if state is None:
                return np.zeros(self.state_dim, dtype=np.float32)
            state_arr = np.asarray(state, dtype=np.float32).flatten()
            if len(state_arr) < self.state_dim:
                padded = np.zeros(self.state_dim, dtype=np.float32)
                padded[:len(state_arr)] = state_arr
                return padded
            elif len(state_arr) > self.state_dim:
                return state_arr[:self.state_dim]
            return state_arr
        
        def normalize_action(action):
            if isinstance(action, np.ndarray):
                if action.size == 1:
                    return int(action.item())
                return int(np.argmax(action))
            return int(action)
        
        states = np.array([normalize_state(e.state) for e in experiences], dtype=np.float32)
        actions = np.array([normalize_action(e.action) for e in experiences], dtype=np.int64)
        rewards = np.array([e.reward for e in experiences], dtype=np.float32)
        next_states = np.array([normalize_state(e.next_state) for e in experiences], dtype=np.float32)
        dones = np.array([e.done for e in experiences], dtype=bool)
        token_sequences = [e.token_sequence for e in experiences]
        vp_values = [e.vp_value for e in experiences]
        
        return states, actions, rewards, next_states, dones, token_sequences, vp_values

    def sample_batch_with_seq2seq(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, 
                                                                   np.ndarray, np.ndarray, 
                                                                   np.ndarray, List[List[int]],
                                                                   List[List[int]], List[float],
                                                                   List[Optional[float]]]:
        """
        Sample a batch with proper seq2seq input/target separation.
        
        GROK SWARM FIX: This method returns separated input_tokens and target_tokens
        for proper supervised language learning instead of concatenated token_sequence.
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            Tuple of (states, actions, rewards, next_states, dones, 
                      input_tokens_list, target_tokens_list, rewards_list, vp_values)
        """
        # Filter experiences that have proper seq2seq data
        seq2seq_experiences = [e for e in self.buffer if e.has_seq2seq_data()]
        
        if len(seq2seq_experiences) < batch_size:
            # Fall back to regular experiences if not enough seq2seq data
            experiences = self.sample(min(batch_size, self.size))
        else:
            experiences = random.sample(seq2seq_experiences, min(batch_size, len(seq2seq_experiences)))
        
        # Normalize states to prevent inhomogeneous array errors
        def normalize_state(state):
            if state is None:
                return np.zeros(self.state_dim, dtype=np.float32)
            state_arr = np.asarray(state, dtype=np.float32).flatten()
            if len(state_arr) < self.state_dim:
                padded = np.zeros(self.state_dim, dtype=np.float32)
                padded[:len(state_arr)] = state_arr
                return padded
            elif len(state_arr) > self.state_dim:
                return state_arr[:self.state_dim]
            return state_arr
        
        def normalize_action(action):
            if isinstance(action, np.ndarray):
                if action.size == 1:
                    return int(action.item())
                return int(np.argmax(action))
            return int(action)
        
        states = np.array([normalize_state(e.state) for e in experiences], dtype=np.float32)
        actions = np.array([normalize_action(e.action) for e in experiences], dtype=np.int64)
        rewards = np.array([e.reward for e in experiences], dtype=np.float32)
        next_states = np.array([normalize_state(e.next_state) for e in experiences], dtype=np.float32)
        dones = np.array([e.done for e in experiences], dtype=bool)
        input_tokens_list = [e.input_tokens for e in experiences]
        target_tokens_list = [e.target_tokens for e in experiences]
        rewards_list = [e.reward for e in experiences]
        vp_values = [e.vp_value for e in experiences]
        
        return states, actions, rewards, next_states, dones, input_tokens_list, target_tokens_list, rewards_list, vp_values
    
    def has_seq2seq_data(self, min_count: int = 1) -> bool:
        """Check if buffer has enough experiences with proper seq2seq data."""
        seq2seq_count = sum(1 for e in self.buffer if e.has_seq2seq_data())
        return seq2seq_count >= min_count
    
    def clear(self):
        """Clear all experiences from buffer."""
        self.buffer.clear()
        self.size = 0
    
    def __len__(self) -> int:
        """Get current buffer size."""
        return self.size
    
    def is_ready(self, batch_size: int) -> bool:
        """
        Check if buffer has enough experiences for sampling.
        
        Args:
            batch_size: Required batch size
            
        Returns:
            True if buffer has enough experiences
        """
        return self.size >= batch_size

