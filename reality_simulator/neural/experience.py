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
    - token_sequence: Token IDs for language model training (optional)
    - vp_value: VP state at experience time (optional)
    """
    
    def __init__(self, state: np.ndarray, action: int, reward: float,
                 next_state: np.ndarray, done: bool,
                 token_sequence: Optional[List[int]] = None,
                 vp_value: Optional[float] = None):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done
        # Language model extensions
        self.token_sequence = token_sequence if token_sequence is not None else []
        self.vp_value = vp_value


class ExperienceBuffer:
    """
    Experience replay buffer for DQN training.
    
    Uses a circular buffer to store experiences and provides
    efficient batch sampling.
    """
    
    def __init__(self, capacity: int = 1000):
        """
        Initialize experience buffer.
        
        Args:
            capacity: Maximum number of experiences to store
        """
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.size = 0
    
    def add(self, state: np.ndarray, action: int, reward: float,
            next_state: np.ndarray, done: bool,
            token_sequence: Optional[List[int]] = None,
            vp_value: Optional[float] = None):
        """
        Add experience to buffer.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
            token_sequence: Token IDs for language model (optional)
            vp_value: VP value at experience time (optional)
        """
        experience = Experience(state, action, reward, next_state, done,
                               token_sequence=token_sequence, vp_value=vp_value)
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
        
        states = np.array([e.state for e in experiences])
        actions = np.array([e.action for e in experiences])
        rewards = np.array([e.reward for e in experiences])
        next_states = np.array([e.next_state for e in experiences])
        dones = np.array([e.done for e in experiences])
        
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
        
        states = np.array([e.state for e in experiences])
        actions = np.array([e.action for e in experiences])
        rewards = np.array([e.reward for e in experiences])
        next_states = np.array([e.next_state for e in experiences])
        dones = np.array([e.done for e in experiences])
        token_sequences = [e.token_sequence for e in experiences]
        vp_values = [e.vp_value for e in experiences]
        
        return states, actions, rewards, next_states, dones, token_sequences, vp_values
    
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

