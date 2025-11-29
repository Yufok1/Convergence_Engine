"""
OrganismBrain - Neural Network for Organisms

A PyTorch neural network that serves as the "brain" for organisms,
enabling decision-making through reinforcement learning.
"""

import numpy as np
from typing import Optional, Tuple
import os

# Try importing PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    nn = None
    F = None
    torch = None


class OrganismBrain(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Neural network brain for organisms.
    
    Architecture:
    - Input Layer: input_dim (sensory data)
    - Hidden Layer 1: hidden_dim + ReLU + Dropout
    - Hidden Layer 2: hidden_dim + ReLU + Dropout
    - Output Layer: output_dim + Softmax (action probabilities)
    """
    
    def __init__(self, 
                 input_dim: int = 12,
                 hidden_dim: int = 64,
                 output_dim: int = 6,
                 activation: str = 'relu',
                 dropout: float = 0.1):
        """
        Initialize the organism brain.
        
        Args:
            input_dim: Number of input features
            hidden_dim: Hidden layer dimension
            output_dim: Number of output actions
            activation: Activation function ('relu', 'tanh', 'sigmoid')
            dropout: Dropout probability
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for OrganismBrain")
        
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.activation_name = activation
        self.dropout_rate = dropout
        
        # Define layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._initialize_weights()
        
        # Optimization: Script forward pass for faster inference (optional)
        self._forward_scripted = None
        self._use_scripted_inference = False
    
    def _initialize_weights(self):
        """Initialize network weights using Xavier initialization."""
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.xavier_uniform_(self.fc2.weight)
        nn.init.xavier_uniform_(self.fc3.weight)
        nn.init.zeros_(self.fc1.bias)
        nn.init.zeros_(self.fc2.bias)
        nn.init.zeros_(self.fc3.bias)
    
    def _get_activation(self, x):
        """Get activation function."""
        if self.activation_name == 'relu':
            return torch.relu(x)
        elif self.activation_name == 'tanh':
            return torch.tanh(x)
        elif self.activation_name == 'sigmoid':
            return torch.sigmoid(x)
        else:
            return torch.relu(x)  # Default
    
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim)
            
        Returns:
            Action probabilities of shape (batch_size, output_dim)
        """
        x = self._get_activation(self.fc1(x))
        x = self.dropout(x)
        x = self._get_activation(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        # Softmax for action probabilities
        return x.softmax(dim=-1)
    
    def get_action(self, state: np.ndarray, epsilon: float = 0.0) -> int:
        """
        Get action using epsilon-greedy policy.
        
        Args:
            state: State array of shape (input_dim,)
            epsilon: Exploration probability (0.0 = pure exploitation)
            
        Returns:
            Action index (0 to output_dim - 1)
        """
        if np.random.random() < epsilon:
            # Explore: random action
            return np.random.randint(0, self.output_dim)
        
        # Exploit: use neural network
        self.eval()  # Set to evaluation mode
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            # Optimization: Use scripted forward pass if available (faster inference)
            if self._use_scripted_inference and self._forward_scripted is not None:
                action_probs = self._forward_scripted(state_tensor)
            else:
                action_probs = self.forward(state_tensor)
            
            action = torch.argmax(action_probs, dim=1).item()
        
        return action
    
    def enable_scripted_inference(self):
        """
        Enable scripted inference for faster action selection.
        Only call this after the model is fully initialized.
        """
        if not PYTORCH_AVAILABLE:
            return
        
        try:
            if hasattr(torch.jit, 'script'):
                self._forward_scripted = torch.jit.script(self.forward)
                self._use_scripted_inference = True
        except Exception:
            # Fallback if scripting fails
            self._use_scripted_inference = False
    
    def mutate(self, mutation_rate: float = 0.1):
        """
        Add noise to weights for genetic variation.
        
        Args:
            mutation_rate: Standard deviation of noise to add
        """
        with torch.no_grad():
            for param in self.parameters():
                noise = torch.randn_like(param) * mutation_rate
                param.add_(noise)
    
    def crossover(self, other_brain: 'OrganismBrain', crossover_rate: float = 0.5):
        """
        Create new brain by combining weights from two parents.
        
        Args:
            other_brain: Second parent brain
            crossover_rate: Probability of taking weights from other_brain
            
        Returns:
            New OrganismBrain with combined weights
        """
        child = OrganismBrain(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim,
            activation=self.activation_name,
            dropout=self.dropout_rate
        )
        
        with torch.no_grad():
            for child_param, self_param, other_param in zip(
                child.parameters(), self.parameters(), other_brain.parameters()
            ):
                # Randomly select weights from each parent
                mask = torch.rand_like(child_param) < crossover_rate
                child_param.copy_(torch.where(mask, other_param, self_param))
        
        return child
    
    def save(self, path: str):
        """
        Save brain weights to file.
        
        Args:
            path: File path to save weights
        """
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        torch.save(self.state_dict(), path)
    
    def load(self, path: str):
        """
        Load brain weights from file.
        
        Args:
            path: File path to load weights from
        """
        if os.path.exists(path):
            self.load_state_dict(torch.load(path))
        else:
            raise FileNotFoundError(f"Brain weights not found at {path}")

