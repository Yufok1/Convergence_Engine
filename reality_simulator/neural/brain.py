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
        
        Uses Flash Attention (scaled_dot_product_attention) when available for 
        significant performance gains on modern GPUs.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, embed_dim)
            vp_value: Optional VP value for temperature scaling
            attention_mask: Optional mask for attention scores
            
        Returns:
            Attended output of shape (batch_size, seq_len, embed_dim)
        """
        # Use .size() for TorchScript compatibility
        batch_size = x.size(0)
        seq_len = x.size(1)
        
        # Project to Q, K, V
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape for multi-head attention: (batch, seq, heads, head_dim) -> (batch, heads, seq, head_dim)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # VP temperature scaling factor
        scale = self.scale
        if vp_value is not None and vp_value > 0:
            # Higher VP = lower entropy (more focused attention)
            scale = self.scale * (1.0 + vp_value)
        
        # Use Flash Attention (PyTorch 2.0+) for better performance
        # This automatically selects optimal attention implementation:
        # - Flash Attention (fastest, memory efficient)
        # - Memory-efficient attention
        # - Standard attention (fallback)
        use_flash = hasattr(F, 'scaled_dot_product_attention')
        
        if use_flash and attention_mask is None:
            # Flash attention path - significantly faster on modern GPUs
            # dropout_p=0.0 during inference, self.dropout.p during training
            dropout_p = self.dropout.p if self.training else 0.0
            attn_output = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=None,
                dropout_p=dropout_p,
                scale=1.0 / scale,  # scale is applied as 1/scale in SDPA
                is_causal=False
            )
        else:
            # Fallback path for custom masks or older PyTorch
            scores = torch.matmul(q, k.transpose(-2, -1)) / scale
            
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


class HopfieldLayer(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Modern Continuous Hopfield Layer with iterative refinement.
    
    Implements energy-based pattern completion where hidden states
    converge toward learned attractor patterns through iteration.
    
    Energy function: E(ξ) = -β⁻¹ log Σᵢ exp(β xᵢᵀ ξ)
    Update rule: ξ' = softmax(β Xᵀ ξ) · X
    
    This allows organisms to "think" - refining their internal state
    before producing outputs.
    
    Key features:
    - Stores N patterns as learnable memory matrix
    - Iterative refinement until convergence or max iterations
    - Convergence detection for early stopping
    - VP-aware temperature scaling (higher VP = sharper retrieval)
    """
    
    def __init__(self,
                 hidden_dim: int = 64,
                 num_patterns: int = 32,
                 max_iterations: int = 5,
                 beta: float = 1.0,
                 convergence_threshold: float = 1e-3,
                 dropout: float = 0.1):
        """
        Initialize Hopfield layer.
        
        Args:
            hidden_dim: Dimension of hidden states
            num_patterns: Number of stored patterns (memory capacity)
            max_iterations: Maximum refinement iterations
            beta: Inverse temperature (higher = sharper pattern retrieval)
            convergence_threshold: Stop iterating if change falls below this
            dropout: Dropout probability
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for HopfieldLayer")
        
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_patterns = num_patterns
        self.max_iterations = max_iterations
        self.beta = beta
        self.convergence_threshold = convergence_threshold
        
        # Learnable pattern memory: each row is a stored pattern
        # These are the "attractors" the network settles toward
        self.patterns = nn.Parameter(torch.randn(num_patterns, hidden_dim) * 0.02)
        
        # Projection layers for query/key transformation (modern Hopfield)
        self.query_proj = nn.Linear(hidden_dim, hidden_dim)
        self.key_proj = nn.Linear(hidden_dim, hidden_dim)
        
        # Output projection with residual
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
        # Convergence tracking (for debugging/monitoring)
        self._last_iterations = 0
        self._last_converged = False
        self._last_delta = 0.0
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize weights for stable training."""
        nn.init.xavier_uniform_(self.query_proj.weight)
        nn.init.xavier_uniform_(self.key_proj.weight)
        nn.init.xavier_uniform_(self.out_proj.weight)
        nn.init.zeros_(self.query_proj.bias)
        nn.init.zeros_(self.key_proj.bias)
        nn.init.zeros_(self.out_proj.bias)
        
        # Initialize patterns as orthogonal for better capacity
        if self.num_patterns <= self.hidden_dim:
            nn.init.orthogonal_(self.patterns)
        else:
            nn.init.xavier_uniform_(self.patterns)
    
    def forward(self, x: 'torch.Tensor', 
                vp_value: Optional[float] = None) -> 'torch.Tensor':
        """
        Forward pass with iterative Hopfield refinement.
        
        Args:
            x: Input tensor of shape (batch_size, hidden_dim)
            vp_value: Optional VP value for temperature scaling
            
        Returns:
            Refined tensor of shape (batch_size, hidden_dim)
        """
        # VP-aware temperature: higher VP = sharper (more confident) retrieval
        beta = self.beta
        if vp_value is not None and vp_value > 0:
            beta = self.beta * (1.0 + vp_value * 0.5)
        
        # Handle 3D input (batch, seq, hidden) - process each position
        if x.dim() == 3:
            batch_size, seq_len, _ = x.size()
            x_flat = x.view(-1, self.hidden_dim)
            out_flat = self._iterate(x_flat, beta)
            return out_flat.view(batch_size, seq_len, self.hidden_dim)
        
        return self._iterate(x, beta)
    
    def _iterate(self, xi: 'torch.Tensor', beta: float) -> 'torch.Tensor':
        """
        Iterative refinement loop (fixed iterations, torch.compile friendly).
        
        Args:
            xi: Current state (batch_size, hidden_dim)
            beta: Inverse temperature
            
        Returns:
            Refined state (batch_size, hidden_dim)
            
        Note:
            Uses fixed iterations (no early exit) to avoid torch.compile graph breaks.
            The .item() call for convergence checking caused kernel launch overhead that
            exceeded the matmul cost. Fixed iterations are actually faster in practice.
        """
        # Project patterns to key space (shared across batch)
        keys = self.key_proj(self.patterns)  # (num_patterns, hidden_dim)
        
        # Fixed iteration refinement (no early exit, no .item() - fully compile friendly)
        for i in range(self.max_iterations):
            xi_prev = xi
            
            # Project current state to query space
            queries = self.query_proj(xi)  # (batch, hidden_dim)
            
            # Compute attention over patterns: softmax(β * q · kᵀ)
            # Shape: (batch, num_patterns)
            scores = torch.matmul(queries, keys.t()) * beta
            attention = F.softmax(scores, dim=-1)
            
            # Retrieve from patterns: weighted sum
            # Shape: (batch, hidden_dim)
            retrieved = torch.matmul(attention, self.patterns)
            
            # Update state with residual
            xi = xi + self.dropout(self.out_proj(retrieved))
            xi = self.norm(xi)
            
            # Track delta on GPU (no .item() - stays in graph)
            self._last_delta_tensor = (xi - xi_prev).abs().mean()
        
        # Update convergence tracking (iterations known, delta deferred)
        self._last_iterations = self.max_iterations
        self._last_converged = False  # Fixed iterations = always runs full
        
        return xi
    
    def get_convergence_info(self) -> Dict[str, Any]:
        """Get info about last forward pass convergence."""
        # Deferred .item() call - only when user queries, not in forward pass
        delta = self._last_delta_tensor.item() if hasattr(self, '_last_delta_tensor') else 0.0
        return {
            'iterations': self._last_iterations,
            'converged': self._last_converged,
            'final_delta': delta,
            'max_iterations': self.max_iterations,
            'threshold': self.convergence_threshold
        }


class OrganismBrain(nn.Module if PYTORCH_AVAILABLE else object):
    """
    Neural network brain for organisms.
    
    Architecture:
    - Input Layer: input_dim (sensory data)
    - Hidden Layer 1: hidden_dim + ReLU + Dropout
    - [Optional] Multi-head Self-Attention with VP temperature scaling
    - [Optional] Hopfield Layer for iterative thought refinement
    - Hidden Layer 2: hidden_dim + ReLU + Dropout
    - Dual Output Heads:
      - Action Head: output_dim + Softmax (action probabilities) - for RL
      - Language Head: vocab_size (next token logits) - for language modeling
    """
    
    def __init__(self, 
                 input_dim: int = 30,  # Default matches config.json neural.brain.input_dim
                 hidden_dim: int = 64,
                 output_dim: int = 6,
                 activation: str = 'relu',
                 dropout: float = 0.1,
                 # Language model parameters
                 use_attention: bool = False,
                 num_attention_heads: int = 4,
                 attention_dim: int = 32,  # Default matches config.json neural.language_model.attention.attention_dim
                 max_sequence_length: int = 32,
                 vocab_size: int = 10000,  # Organism max vocab (mastery level 4 cap)
                 use_language_head: bool = False,
                 use_concept_head: bool = False,
                 num_key_compositions: int = 30,  # ARCHITECTURE PARAM - must match config.json!
                 use_world_model: bool = True,  # ?? NEW: Enable predictive world model
                 # Hopfield layer parameters (iterative thought refinement)
                 use_hopfield: bool = False,
                 hopfield_patterns: int = 32,
                 hopfield_iterations: int = 5,
                 hopfield_beta: float = 1.0):
        """
        Initialize the organism brain.
        
        IMPORTANT: Architecture-defining parameters (input_dim, hidden_dim, output_dim,
        vocab_size, num_key_compositions) must match config.json values. Changing these
        after training will break saved model loading.
        
        Args:
            input_dim: Number of input features
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
            use_world_model: Enable predictive world model (predicts next state)
            use_hopfield: Enable Hopfield layer for iterative thought refinement
            hopfield_patterns: Number of patterns in Hopfield memory
            hopfield_iterations: Max iterations for convergence
            hopfield_beta: Inverse temperature for pattern retrieval
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
        
        # World model parameters
        self.use_world_model = use_world_model
        
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
        
        # Optional Hopfield layer (iterative thought refinement)
        self.use_hopfield = use_hopfield
        if self.use_hopfield:
            self.hopfield = HopfieldLayer(
                hidden_dim=hidden_dim,
                num_patterns=hopfield_patterns,
                max_iterations=hopfield_iterations,
                beta=hopfield_beta,
                dropout=dropout
            )
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Action head (original output layer for RL)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        
        # Language head (for next-token prediction)
        if self.use_language_head:
            self.fc_language = nn.Linear(hidden_dim, vocab_size)
            
        # World model head (predicts next state features based on action)
        if self.use_world_model:
            # Input: hidden_dim + output_dim (action one-hot)
            self.fc_world_model = nn.Linear(hidden_dim + output_dim, input_dim)
        
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
            
        if self.use_world_model:
            nn.init.xavier_uniform_(self.fc_world_model.weight)
            nn.init.zeros_(self.fc_world_model.bias)
    
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
                return_concept_outputs: bool = False,
                return_world_model_output: bool = False) -> 'torch.Tensor':
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim) or 
               (batch_size, seq_len, input_dim) for sequence modeling
            vp_value: Optional VP value for attention temperature scaling
            return_language_logits: If True, also return language head logits
            return_concept_outputs: If True, also return concept head outputs
            return_world_model_output: If True, also return world model predictions
            
        Returns:
            If only action output: Action probabilities of shape (batch_size, output_dim)
            Otherwise: Dictionary containing requested outputs
        """
        # Handle both 2D (batch, input) and 3D (batch, seq, input) inputs
        is_sequence = x.dim() == 3  # Use .dim() for TorchScript compatibility
        
        if is_sequence:
            batch_size, seq_len, _ = x.size()  # Use .size() for TorchScript
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
        
        # Apply Hopfield iterative refinement if enabled
        if self.use_hopfield:
            x = self.hopfield(x, vp_value=vp_value)
        
        # Reshape back to 2D for remaining layers if we added a sequence dim
        x_ndim = x.dim()  # Use .dim() instead of len(x.shape) for TorchScript compatibility
        if is_sequence and x_ndim == 3 and x.size(1) == 1:
            x = x.squeeze(1)
            is_sequence = False  # No longer treating as sequence after squeezing
        elif is_sequence and x_ndim == 3:
            # For actual sequences, use the last position for action prediction
            x_for_action = x[:, -1, :]  # (batch, hidden)
        else:
            x_for_action = x
            is_sequence = False  # Ensure flag matches tensor shape
        
        # Apply fc2
        x_ndim = x.dim()  # Refresh after potential squeeze
        if is_sequence and x_ndim == 3 and x.size(1) > 1:
            # For language modeling, process all positions
            x = self._get_activation(self.fc2(x))
            x = self.dropout(x)
            x_for_action = x[:, -1, :]  # Last position for action
        else:
            # 2D tensor or single-position sequence
            x_2d = x if x.dim() == 2 else x_for_action
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
            
        # World model head (predicts next state features based on action)
        world_model_output = None
        if return_world_model_output and self.use_world_model:
            # We need the selected action to predict the next state
            # Concatenate hidden state with action probabilities for 'soft' action selection
            combined = torch.cat([x_for_action, action_probs], dim=-1)
            world_model_output = self.fc_world_model(combined)
        
        # Build return value based on requested outputs
        # BACKWARD COMPATIBILITY: Return tuples for legacy callers, dict only when world_model requested
        if not any([return_language_logits, return_concept_outputs, return_world_model_output]):
            return action_probs
        
        # Calculate language logits if requested
        language_logits = None
        if return_language_logits and self.use_language_head:
            if is_sequence and x.dim() == 3:  # Use .dim() for TorchScript
                language_logits = self.fc_language(x)  # (batch, seq, vocab)
            else:
                language_logits = self.fc_language(x_for_action)  # (batch, vocab)
        
        # LEGACY TUPLE RETURNS (for existing callers expecting tuple unpacking)
        # Only use dict when world_model output is requested (new API)
        if not return_world_model_output:
            if return_language_logits and return_concept_outputs:
                return action_probs, language_logits, concept_outputs
            elif return_language_logits:
                return action_probs, language_logits
            elif return_concept_outputs:
                return action_probs, concept_outputs
        
        # NEW DICT API: Only when world_model is requested
        results = {'action_probs': action_probs}
        if language_logits is not None:
            results['language_logits'] = language_logits
        if concept_outputs is not None:
            results['concept_outputs'] = concept_outputs
        if world_model_output is not None:
            results['world_model_output'] = world_model_output
            
        return results
    
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
            
            # SAFEGUARD: Check for NaN/Inf/zero probabilities before multinomial
            probs_flat = probs.squeeze(0) if probs.dim() > 2 else probs
            # Use .item() to convert tensor booleans to Python booleans
            probs_valid = torch.isfinite(probs_flat).all().item() and probs_flat.sum().item() > 0
            if not probs_valid:
                # Fall back to uniform distribution
                probs_flat = torch.ones_like(probs_flat) / max(1, probs_flat.numel())
            
            try:
                token_ids = torch.multinomial(probs_flat, 1)
            except (RuntimeError, AssertionError):
                # Last resort: random token
                token_ids = torch.randint(0, probs_flat.shape[-1], (1,))
            
        return token_ids
    
    def get_thought_info(self) -> Optional[Dict[str, Any]]:
        """
        Get info about the last thought process (Hopfield convergence).
        
        Returns:
            Dict with convergence info if Hopfield enabled, else None
        """
        if self.use_hopfield:
            return self.hopfield.get_convergence_info()
        return None
    
    def get_hidden_state(self, x: torch.Tensor, vp_value: Optional[float] = None) -> torch.Tensor:
        """
        Get hidden state after full processing pipeline (fc1 → attention → hopfield → fc2).
        
        This is the proper way to get intermediate representations when you need
        hidden states for auxiliary heads (language, concept) while respecting
        the full architecture including Hopfield refinement.
        
        Args:
            x: Input tensor of shape (batch, input_dim)
            vp_value: Optional VP value for attention/hopfield temperature scaling
            
        Returns:
            Hidden state tensor of shape (batch, hidden_dim) after fc2
        """
        # fc1 → activation → dropout
        h = self.fc1(x)
        h = self._get_activation(h)
        h = self.dropout(h)
        
        # Optional attention
        if self.use_attention:
            # Reshape for attention: (batch, 1, hidden_dim)
            if h.dim() == 2:
                h = h.unsqueeze(1)
            attn_out = self.attention(h, vp_value=vp_value)
            h = self.attention_norm(h + attn_out)
            if h.dim() == 3 and h.size(1) == 1:
                h = h.squeeze(1)  # Back to (batch, hidden_dim)
        
        # Optional Hopfield refinement (iterative thought)
        if self.use_hopfield:
            h = self.hopfield(h, vp_value=vp_value)
        
        # fc2 → activation → dropout
        h = self.fc2(h)
        h = self._get_activation(h)
        h = self.dropout(h)
        
        return h
    
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
    
    def crossover(self, other_brain: 'OrganismBrain', crossover_rate: float = 0.9):  # Default matches config.json
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
            num_key_compositions=self.num_key_compositions,
            use_hopfield=self.use_hopfield,
            hopfield_patterns=self.hopfield.num_patterns if self.use_hopfield else 32,
            hopfield_iterations=self.hopfield.max_iterations if self.use_hopfield else 5,
            hopfield_beta=self.hopfield.beta if self.use_hopfield else 1.0
        )
        
        # ALWAYS keep brains on CPU for storage - prevents VRAM exhaustion with large populations
        # The trainer will move brains to GPU temporarily during training batches
        child = child.to('cpu')
        
        # For crossover, temporarily work on CPU to avoid VRAM issues
        # Get parent device but do crossover on CPU
        device = 'cpu'
        
        # Ensure both parents can be accessed (move copies to CPU if needed)
        other_device = next(other_brain.parameters()).device
        if other_device != device:
            other_brain = other_brain.to(device)
        
        with torch.no_grad():
            for child_param, self_param, other_param in zip(
                child.parameters(), self.parameters(), other_brain.parameters()
            ):
                # Move parent params to child device if needed, handle NaN/Inf
                self_p = self_param.to(device)
                other_p = other_param.to(device)
                
                # Replace any NaN/Inf with zeros to prevent cascade failures
                if torch.isnan(self_p).any() or torch.isinf(self_p).any():
                    self_p = torch.nan_to_num(self_p, nan=0.0, posinf=1.0, neginf=-1.0)
                if torch.isnan(other_p).any() or torch.isinf(other_p).any():
                    other_p = torch.nan_to_num(other_p, nan=0.0, posinf=1.0, neginf=-1.0)
                
                # Randomly select weights from each parent
                mask = torch.rand_like(child_param) < crossover_rate
                child_param.copy_(torch.where(mask, other_p, self_p))
        
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

