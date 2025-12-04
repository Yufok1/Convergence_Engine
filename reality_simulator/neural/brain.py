"""
OrganismBrain - Neural Network for Organisms

A PyTorch neural network that serves as the "brain" for organisms,
enabling decision-making through reinforcement learning.

Extended with:
- Multi-head self-attention mechanism (optional)
- Dual-head architecture: action head + language head
- VP-aware temperature scaling for attention
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
import os
import math

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

# Import concept system (optional)
try:
    from .concept_system import ConceptHead, ConceptSystem
    CONCEPT_SYSTEM_AVAILABLE = True
except ImportError:
    try:
        from reality_simulator.neural.concept_system import ConceptHead, ConceptSystem
        CONCEPT_SYSTEM_AVAILABLE = True
    except ImportError:
        CONCEPT_SYSTEM_AVAILABLE = False
        ConceptHead = None
        ConceptSystem = None


class MultiHeadAttention(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Multi-head self-attention mechanism with VP-aware temperature scaling.
    
    Key features:
    - Standard scaled dot-product attention
    - Optional VP temperature scaling: scores / (1.0 + vp_value)
    - Supports sequence modeling for language generation
    """
    
    def __init__(self, 
                 embed_dim: int = 64,
                 num_heads: int = 4,
                 dropout: float = 0.1):
        """
        Initialize multi-head attention.
        
        Args:
            embed_dim: Embedding dimension (must be divisible by num_heads)
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for MultiHeadAttention")
            
        super().__init__()
        
        # Runtime validation instead of assert (asserts disabled with -O flag)
        if embed_dim % num_heads != 0:
            raise ValueError(f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads})")
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = math.sqrt(self.head_dim)
        
        # Linear projections for Q, K, V
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Xavier initialization for attention projections."""
        nn.init.xavier_uniform_(self.q_proj.weight)
        nn.init.xavier_uniform_(self.k_proj.weight)
        nn.init.xavier_uniform_(self.v_proj.weight)
        nn.init.xavier_uniform_(self.out_proj.weight)
        nn.init.zeros_(self.q_proj.bias)
        nn.init.zeros_(self.k_proj.bias)
        nn.init.zeros_(self.v_proj.bias)
        nn.init.zeros_(self.out_proj.bias)
    
    def forward(self, 
                x: 'torch.Tensor',
                vp_value: Optional[float] = None,
                attention_mask: Optional['torch.Tensor'] = None) -> 'torch.Tensor':
        """
        Forward pass with optional VP temperature scaling.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, embed_dim)
            vp_value: Optional VP value for temperature scaling
            attention_mask: Optional mask for attention scores
            
        Returns:
            Attended output of shape (batch_size, seq_len, embed_dim)
        """
        batch_size, seq_len, _ = x.shape
        
        # Project to Q, K, V
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape for multi-head attention: (batch, seq, heads, head_dim) -> (batch, heads, seq, head_dim)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / self.scale
        
        # VP temperature scaling: higher VP = lower entropy (more focused attention)
        if vp_value is not None and vp_value > 0:
            scores = scores / (1.0 + vp_value)
        
        # Apply attention mask if provided
        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, float('-inf'))
        
        # Softmax and dropout
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)
        
        # Reshape back: (batch, heads, seq, head_dim) -> (batch, seq, embed_dim)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.embed_dim)
        
        # Final projection
        output = self.out_proj(attn_output)
        
        return output


class OrganismBrain(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Neural network brain for organisms.
    
    Architecture:
    - Input Layer: input_dim (sensory data)
    - Hidden Layer 1: hidden_dim + ReLU + Dropout
    - [Optional] Multi-head Self-Attention with VP temperature scaling
    - Hidden Layer 2: hidden_dim + ReLU + Dropout
    - Dual Output Heads:
      - Action Head: output_dim + Softmax (action probabilities) - for RL
      - Language Head: vocab_size (next token logits) - for language modeling
    """
    
    def __init__(self, 
                 input_dim: int = 24,
                 hidden_dim: int = 64,
                 output_dim: int = 6,
                 activation: str = 'relu',
                 dropout: float = 0.1,
                 # Language model parameters
                 use_attention: bool = False,
                 num_attention_heads: int = 4,
                 attention_dim: int = 64,
                 max_sequence_length: int = 32,
                 vocab_size: int = 12288,
                 use_language_head: bool = False,
                 use_concept_head: bool = False,
                 num_key_compositions: int = 20):  # ARCHITECTURE PARAM - must match config.json!
        """
        Initialize the organism brain.
        
        IMPORTANT: Architecture-defining parameters (input_dim, hidden_dim, output_dim,
        vocab_size, num_key_compositions) must match config.json values. Changing these
        after training will break saved model loading.
        
        Args:
            input_dim: Number of input features (24 with VP + extended features)
            hidden_dim: Hidden layer dimension
            output_dim: Number of output actions
            activation: Activation function ('relu', 'tanh', 'sigmoid')
            dropout: Dropout probability
            use_attention: Enable multi-head self-attention
            num_attention_heads: Number of attention heads
            attention_dim: Attention embedding dimension
            max_sequence_length: Maximum sequence length for attention
            vocab_size: Vocabulary size for language head
            use_language_head: Enable language prediction head
            use_concept_head: Enable concept understanding head (RCUS)
            num_key_compositions: Number of key concept compositions (must match config!)
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for OrganismBrain")
        
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.activation_name = activation
        self.dropout_rate = dropout
        
        # Language model parameters
        self.use_attention = use_attention
        self.num_attention_heads = num_attention_heads
        self.attention_dim = attention_dim
        self.max_sequence_length = max_sequence_length
        self.current_sequence_length = 8  # Start small for curriculum learning
        self.vocab_size = vocab_size
        self.use_language_head = use_language_head
        
        # Define layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        
        # Optional attention layer (inserted between fc1 and fc2)
        if self.use_attention:
            self.attention = MultiHeadAttention(
                embed_dim=hidden_dim,
                num_heads=num_attention_heads,
                dropout=dropout
            )
            # Layer norm for attention (standard practice)
            self.attention_norm = nn.LayerNorm(hidden_dim)
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Action head (original output layer for RL)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        
        # Language head (for next-token prediction)
        if self.use_language_head:
            self.fc_language = nn.Linear(hidden_dim, vocab_size)
        
        # Concept head (for compositional understanding - RCUS)
        self.use_concept_head = use_concept_head and CONCEPT_SYSTEM_AVAILABLE
        self.num_key_compositions = num_key_compositions
        if self.use_concept_head:
            self.concept_head = ConceptHead(
                hidden_dim=hidden_dim,
                num_axioms=18,  # 18 primitive axioms
                num_compositions=num_key_compositions
            )
        
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
        
        if self.use_language_head:
            nn.init.xavier_uniform_(self.fc_language.weight)
            nn.init.zeros_(self.fc_language.bias)
    
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
    
    def forward(self, x: 'torch.Tensor', 
                vp_value: Optional[float] = None,
                return_language_logits: bool = False,
                return_concept_outputs: bool = False) -> 'torch.Tensor':
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim) or 
               (batch_size, seq_len, input_dim) for sequence modeling
            vp_value: Optional VP value for attention temperature scaling
            return_language_logits: If True, also return language head logits
            return_concept_outputs: If True, also return concept head outputs
            
        Returns:
            If only action output: Action probabilities of shape (batch_size, output_dim)
            If return_language_logits: Tuple of (action_probs, language_logits)
            If return_concept_outputs: Tuple includes concept_outputs dict
            If both: Tuple of (action_probs, language_logits, concept_outputs)
        """
        # Handle both 2D (batch, input) and 3D (batch, seq, input) inputs
        is_sequence = len(x.shape) == 3
        
        if is_sequence:
            batch_size, seq_len, _ = x.shape
            # Apply fc1 to each position
            x = self._get_activation(self.fc1(x))
            x = self.dropout(x)
        else:
            # Standard 2D input - reshape for potential attention
            x = self._get_activation(self.fc1(x))
            x = self.dropout(x)
            if self.use_attention:
                # Reshape to (batch, 1, hidden) for attention
                x = x.unsqueeze(1)
                is_sequence = True
                seq_len = 1
        
        # Apply attention if enabled
        if self.use_attention and is_sequence:
            # Residual connection with layer norm (standard transformer pattern)
            attn_out = self.attention(x, vp_value=vp_value)
            x = self.attention_norm(x + attn_out)
        
        # Reshape back to 2D for remaining layers if we added a sequence dim
        if is_sequence and len(x.shape) == 3 and x.shape[1] == 1:
            x = x.squeeze(1)
            is_sequence = False  # No longer treating as sequence after squeezing
        elif is_sequence and len(x.shape) == 3:
            # For actual sequences, use the last position for action prediction
            x_for_action = x[:, -1, :]  # (batch, hidden)
        else:
            x_for_action = x
            is_sequence = False  # Ensure flag matches tensor shape
        
        # Apply fc2
        if is_sequence and len(x.shape) == 3 and x.shape[1] > 1:
            # For language modeling, process all positions
            x = self._get_activation(self.fc2(x))
            x = self.dropout(x)
            x_for_action = x[:, -1, :]  # Last position for action
        else:
            # 2D tensor or single-position sequence
            x_2d = x if len(x.shape) == 2 else x_for_action
            x = self._get_activation(self.fc2(x_2d))
            x = self.dropout(x)
            x_for_action = x
        
        # Action head (for RL decision-making)
        action_logits = self.fc3(x_for_action)
        action_probs = action_logits.softmax(dim=-1)
        
        # Concept head (for compositional understanding)
        concept_outputs = None
        if return_concept_outputs and self.use_concept_head:
            concept_outputs = self.concept_head(x_for_action)
        
        # Build return value based on requested outputs
        if return_language_logits and self.use_language_head:
            # Language head (for next-token prediction)
            # Apply to all sequence positions
            if is_sequence and len(x.shape) == 3:
                language_logits = self.fc_language(x)  # (batch, seq, vocab)
            else:
                language_logits = self.fc_language(x_for_action)  # (batch, vocab)
            
            if return_concept_outputs and concept_outputs is not None:
                return action_probs, language_logits, concept_outputs
            return action_probs, language_logits
        
        if return_concept_outputs and concept_outputs is not None:
            return action_probs, concept_outputs
        
        return action_probs
    
    def get_action(self, state: np.ndarray, epsilon: float = 0.0,
                   vp_value: Optional[float] = None) -> int:
        """
        Get action using epsilon-greedy policy.
        
        Args:
            state: State array of shape (input_dim,)
            epsilon: Exploration probability (0.0 = pure exploitation)
            vp_value: Optional VP value for attention temperature scaling
            
        Returns:
            Action index (0 to output_dim - 1)
        """
        if np.random.random() < epsilon:
            # Explore: random action
            return np.random.randint(0, self.output_dim)
        
        # Exploit: use neural network
        self.eval()  # Set to evaluation mode
        with torch.no_grad():
            device = next(self.parameters()).device
            state_tensor = torch.FloatTensor(state).to(device).unsqueeze(0)
            
            # Optimization: Use scripted forward pass if available (faster inference)
            if self._use_scripted_inference and self._forward_scripted is not None:
                action_probs = self._forward_scripted(state_tensor)
            else:
                action_probs = self.forward(state_tensor, vp_value=vp_value)
            
            action = torch.argmax(action_probs, dim=1).item()
        
        return action
    
    def generate_tokens(self, 
                       state: np.ndarray,
                       max_length: int = 32,
                       vp_value: Optional[float] = None,
                       temperature: float = 1.0) -> 'torch.Tensor':
        """
        Generate token sequence using the language head.
        
        Args:
            state: Initial state array
            max_length: Maximum sequence length to generate
            vp_value: VP value for temperature scaling
            temperature: Sampling temperature
            
        Returns:
            Generated token IDs tensor
        """
        if not self.use_language_head:
            raise ValueError("Language head not enabled. Set use_language_head=True")
        
        self.eval()
        
        with torch.no_grad():
            device = next(self.parameters()).device
            state_tensor = torch.FloatTensor(state).to(device).unsqueeze(0)
            
            # Get language logits
            _, language_logits = self.forward(
                state_tensor, 
                vp_value=vp_value,
                return_language_logits=True
            )
            
            # Apply VP gating: if VP > 0.75, mask high-entropy tokens
            if vp_value is not None and vp_value > 0.75:
                # Temperature scaling based on VP
                effective_temp = temperature * (1.0 + vp_value)
                language_logits = language_logits / effective_temp
            else:
                language_logits = language_logits / temperature
            
            # Sample from distribution
            probs = F.softmax(language_logits, dim=-1)
            token_ids = torch.multinomial(probs.squeeze(0) if len(probs.shape) > 2 else probs, 1)
            
        return token_ids
    
    def enable_scripted_inference(self):
        """
        Enable scripted inference for faster action selection.
        Only call this after the model is fully initialized.
        """
        if not PYTORCH_AVAILABLE:
            return
        
        try:
            # Use trace instead of script - script fails on complex control flow in Python 3.12
            was_training = self.training
            self.eval()  # Disable dropout for deterministic tracing
            dummy_input = torch.randn(1, self.input_dim, dtype=torch.float32)
            self._forward_scripted = torch.jit.trace(self, (dummy_input,))
            if was_training:
                self.train()  # Restore training mode if it was active
            self._use_scripted_inference = True
        except Exception:
            # Fallback if tracing fails
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
            dropout=self.dropout_rate,
            use_attention=self.use_attention,
            num_attention_heads=self.num_attention_heads,
            attention_dim=self.attention_dim,
            max_sequence_length=self.max_sequence_length,
            vocab_size=self.vocab_size,
            use_language_head=self.use_language_head,
            use_concept_head=self.use_concept_head,
            num_key_compositions=self.num_key_compositions
        )
        
        # Move child to same device as parent
        device = next(self.parameters()).device
        child = child.to(device)
        
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
            # Use strict=False to handle architecture changes gracefully
            self.load_state_dict(torch.load(path), strict=False)
        else:
            raise FileNotFoundError(f"Brain weights not found at {path}")

