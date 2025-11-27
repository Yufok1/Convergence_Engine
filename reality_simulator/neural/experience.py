"""
Experience Replay Buffer

Stores and samples experiences for reinforcement learning.
"""

import numpy as np
from typing import List, Tuple, Optional
from collections import deque
import random


class Experience:
    """Single experience tuple (state, action, reward, next_state, done)."""
    
    def __init__(self, state: np.ndarray, action: int, reward: float,
                 next_state: np.ndarray, done: bool):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done


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
            next_state: np.ndarray, done: bool):
        """
        Add experience to buffer.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        experience = Experience(state, action, reward, next_state, done)
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
        Sample a batch and return as numpy arrays.
        
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

