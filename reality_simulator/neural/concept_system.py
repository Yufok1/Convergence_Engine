"""
ConceptSystem - Recursive Conceptual Understanding System (RCUS)

Integrates compositional concept learning into the existing neural architecture.
This is NOT a parallel system - it extends OrganismBrain with a concept head.

Design Principles:
1. EXTEND, don't duplicate - works with existing OrganismBrain
2. GROUND in reality - concepts are modulated by organism state
3. COMPOSE novel understanding - FROM combinations OF primitives
4. LEARN from experience - useful compositions get reinforced

Architecture Integration:
- ConceptSystem: Manages axiom embeddings and composition operators
- ConceptHead: Third head in OrganismBrain (alongside action + language)
- concept_loss: Added to NeuralTrainer's triple-loss system
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import OrderedDict
import logging
import os
import json
import threading  # GAP FIX C4: Thread safety

logger = logging.getLogger(__name__)

# Check PyTorch availability
try:
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


# =============================================================================
# AXIOM DEFINITIONS - Grounded in organism state features
# =============================================================================

@dataclass
class AxiomDefinition:
    """Definition of a primitive axiom with grounding information."""
    name: str
    category: str  # existence, comparison, agency, value, action, time, space
    feature_indices: List[int]  # Which 24D state features ground this axiom
    grounding_fn: str  # How to compute grounding: 'direct', 'inverse', 'diff', 'mean'
    description: str


# The 18 axioms mapped to actual 24D organism state features
# Features (from neural_organism.py get_state_features):
#  0: fitness
#  1: resource_level
#  2: num_connections
#  3: avg_neighbor_fitness
#  4: flow_in
#  5: flow_out
#  6: clustering_coefficient
#  7: distance_to_nearest
#  8: generation_age
#  9: parent_fitness
# 10: breath_phase
# 11: breath_amplitude
# 12: trait_divergence (VP)
# 13: network_coherence (VP)
# 14: quantum_entropy (VP)
# 15: evolution_pressure (VP)
# 16: phase_mismatch (VP)
# 17: system_health
# 18: battle_ratio
# 19: alliance_reputation
# 20: language_fluency
# 21: environmental_density
# 22: learning_progress
# 23: health_trend

AXIOM_DEFINITIONS = OrderedDict([
    # EXISTENCE - Am I here? Is there stuff?
    ('EXIST', AxiomDefinition('EXIST', 'existence', [0, 17], 'mean',
        'Being alive and present - grounded in fitness + system health')),
    ('ONE', AxiomDefinition('ONE', 'existence', [2], 'inverse',
        'Being singular/alone - inverse of connection count')),
    ('MANY', AxiomDefinition('MANY', 'existence', [2, 21], 'mean',
        'Plurality/abundance - connections + environmental density')),
    
    # COMPARISON - How do I compare?
    ('MORE', AxiomDefinition('MORE', 'comparison', [0, 3], 'diff',
        'Having more than others - fitness vs neighbor fitness')),
    ('LESS', AxiomDefinition('LESS', 'comparison', [3, 0], 'diff',
        'Having less than others - neighbor fitness vs own')),
    ('SAME', AxiomDefinition('SAME', 'comparison', [0, 3], 'inverse_diff',
        'Being equal - inverse of fitness difference')),
    
    # AGENCY - Who am I? Who are others?
    ('SELF', AxiomDefinition('SELF', 'agency', [0, 18, 19], 'mean',
        'Self-identity - fitness + battle history + reputation')),
    ('OTHER', AxiomDefinition('OTHER', 'agency', [3, 21], 'mean',
        'Others around me - neighbor fitness + density')),
    ('WITH', AxiomDefinition('WITH', 'agency', [2, 6], 'mean',
        'Togetherness/connection - connections + clustering')),
    
    # VALUE - Is it good or bad?
    ('GOOD', AxiomDefinition('GOOD', 'value', [0, 23, 17], 'mean',
        'Positive value - fitness + health trend + system health')),
    # AUDIT FIX: Added [13,14] (network_coherence, quantum_entropy) for complete VP coverage
    ('BAD', AxiomDefinition('BAD', 'value', [12, 13, 14, 15, 16], 'mean',
        'Negative value - VP components (trait_divergence, network_coherence, quantum_entropy, evolution_pressure, phase_mismatch)')),
    
    # ACTION - What can I do?
    ('DO', AxiomDefinition('DO', 'action', [22, 18], 'mean',
        'Taking action - learning progress + battle ratio (agency evidence)')),
    ('CAUSE', AxiomDefinition('CAUSE', 'action', [4, 5], 'mean',
        'Causal effect - resource flows (in/out shows impact)')),
    
    # TIME - When is it?
    ('BEFORE', AxiomDefinition('BEFORE', 'time', [8, 9], 'mean',
        'Past/prior - generation age + parent fitness (history)')),
    ('AFTER', AxiomDefinition('AFTER', 'time', [23, 22], 'mean',
        'Future/next - health trend + learning progress (potential)')),
    ('NOW', AxiomDefinition('NOW', 'time', [10, 11], 'mean',
        'Present moment - breath phase + amplitude (immediate state)')),
    
    # SPACE - Where is it?
    ('HERE', AxiomDefinition('HERE', 'space', [6, 7], 'inverse',
        'Local position - high clustering, low distance = here')),
    ('THERE', AxiomDefinition('THERE', 'space', [7], 'direct',
        'Distant position - distance to nearest neighbor')),
])


# =============================================================================
# COMPOSITION OPERATORS - Bilinear tensor combinations
# =============================================================================

class CompositionOperator(nn.Module):
    """Base class for composition operators."""
    
    def __init__(self, embed_dim: int, name: str):
        super().__init__()
        self.embed_dim = embed_dim
        self.name = name
    
    def forward(self, embed_a: torch.Tensor, embed_b: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError


class WithOperator(CompositionOperator):
    """
    WITH: Symmetric conjunction/joint presence.
    "SELF WITH OTHER" = social connection
    "GOOD WITH DO" = purposeful beneficial action
    
    Mathematical property: WITH(A, B) = WITH(B, A) (enforced via symmetric operations)
    """
    
    def __init__(self, embed_dim: int):
        super().__init__(embed_dim, 'WITH')
        self.bilinear = nn.Bilinear(embed_dim, embed_dim, embed_dim)
        self.gate = nn.Linear(embed_dim * 2, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, embed_a: torch.Tensor, embed_b: torch.Tensor) -> torch.Tensor:
        # AUDIT FIX: Enforce symmetry by averaging bilinear(a,b) and bilinear(b,a)
        bilinear_ab = self.bilinear(embed_a, embed_b)
        bilinear_ba = self.bilinear(embed_b, embed_a)
        bilinear_out = (bilinear_ab + bilinear_ba) / 2  # Symmetric!
        
        # AUDIT FIX: Gate must also be symmetric - average both orderings
        concat_ab = torch.cat([embed_a, embed_b], dim=-1)
        concat_ba = torch.cat([embed_b, embed_a], dim=-1)
        gate = (torch.sigmoid(self.gate(concat_ab)) + torch.sigmoid(self.gate(concat_ba))) / 2  # Symmetric gate!
        
        interaction = embed_a * embed_b * gate  # Element-wise product is symmetric
        return self.norm(bilinear_out + interaction)


class CauseOperator(CompositionOperator):
    """
    CAUSE: Asymmetric causal relationship.
    "DO CAUSE GOOD" = actions lead to positive outcomes
    Note: A CAUSE B ≠ B CAUSE A (asymmetric)
    
    Uses LeakyReLU to preserve negative information (important for causality).
    """
    
    def __init__(self, embed_dim: int):
        super().__init__(embed_dim, 'CAUSE')
        self.cause_transform = nn.Linear(embed_dim, embed_dim)
        self.effect_transform = nn.Linear(embed_dim, embed_dim)
        self.combine = nn.Linear(embed_dim * 2, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, cause: torch.Tensor, effect: torch.Tensor) -> torch.Tensor:
        # AUDIT FIX: Use leaky_relu to preserve negative information
        cause_repr = F.leaky_relu(self.cause_transform(cause), negative_slope=0.1)
        effect_repr = F.leaky_relu(self.effect_transform(effect), negative_slope=0.1)
        combined = torch.cat([cause_repr, effect_repr], dim=-1)
        return self.norm(self.combine(combined))


class ModifyOperator(CompositionOperator):
    """
    MODIFY: Attribute modification (adjective-like).
    "MORE GOOD" = better
    "LESS BAD" = not as bad
    
    Scale has minimum 0.1 to prevent base destruction.
    """
    
    def __init__(self, embed_dim: int):
        super().__init__(embed_dim, 'MODIFY')
        self.modifier_scale = nn.Linear(embed_dim, embed_dim)
        self.modifier_shift = nn.Linear(embed_dim, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, modifier: torch.Tensor, base: torch.Tensor) -> torch.Tensor:
        # AUDIT FIX: scale = 0.1 + 0.9 * sigmoid(...) ensures minimum 10% base preservation
        raw_scale = torch.sigmoid(self.modifier_scale(modifier))
        scale = 0.1 + 0.9 * raw_scale  # Range [0.1, 1.0] - never destroys base!
        shift = torch.tanh(self.modifier_shift(modifier))
        return self.norm(base * scale + shift)


class SequenceOperator(CompositionOperator):
    """
    SEQUENCE: Temporal ordering.
    "BEFORE DO AFTER GOOD" = action precedes reward
    """
    
    def __init__(self, embed_dim: int):
        super().__init__(embed_dim, 'SEQUENCE')
        self.temporal = nn.GRU(embed_dim, embed_dim, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, first: torch.Tensor, second: torch.Tensor) -> torch.Tensor:
        # Handle different input shapes
        if first.dim() == 1:
            first = first.unsqueeze(0)
            second = second.unsqueeze(0)
        
        sequence = torch.stack([first, second], dim=1)
        _, final = self.temporal(sequence)
        return self.norm(final.squeeze(0))


# =============================================================================
# CONCEPT SYSTEM - Core module managing all concepts
# =============================================================================

class ConceptSystem(nn.Module):
    """
    Core concept system for compositional understanding.
    
    This module:
    1. Maintains learnable axiom embeddings
    2. Grounds axioms in organism state
    3. Composes axioms using operators
    4. Tracks concept utility from experience
    5. Predicts value of concepts
    """
    
    def __init__(self,
                 state_dim: int = 24,
                 embed_dim: int = 64,
                 device: str = 'cpu',
                 max_concept_memory: int = 1000):  # GAP FIX C7: Memory limit
        super().__init__()
        self.state_dim = state_dim
        self.embed_dim = embed_dim
        self.device_str = device
        self.max_concept_memory = max_concept_memory  # GAP FIX C7
        
        # GAP FIX C4: Thread safety lock for shared state
        self._memory_lock = threading.RLock()
        
        # Axiom embeddings (learnable base representations)
        self.num_axioms = len(AXIOM_DEFINITIONS)
        self.axiom_embeddings = nn.Embedding(self.num_axioms, embed_dim)
        self.axiom_names = list(AXIOM_DEFINITIONS.keys())
        self.axiom_to_idx = {name: i for i, name in enumerate(self.axiom_names)}
        
        # Grounding network: modulates axiom embeddings based on state
        self.grounding_net = nn.Sequential(
            nn.Linear(state_dim, embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim, embed_dim),
            nn.Tanh()
        )
        
        # Composition operators
        self.operators = nn.ModuleDict({
            'WITH': WithOperator(embed_dim),
            'CAUSE': CauseOperator(embed_dim),
            'MODIFY': ModifyOperator(embed_dim),
            'SEQUENCE': SequenceOperator(embed_dim),
        })
        
        # Value prediction: concept → expected reward
        # AUDIT FIX: Added Tanh for bounded output in [-1, 1] range
        self.value_head = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 2),
            nn.ReLU(),
            nn.Linear(embed_dim // 2, 1),
            nn.Tanh()  # Bounded output!
        )
        
        # Concept memory: stores learned compositions and their utilities
        # GAP FIX C7: Use OrderedDict for LRU-friendly access
        self.concept_memory: OrderedDict[str, torch.Tensor] = OrderedDict()
        self.concept_utility: Dict[str, float] = {}
        self.concept_use_count: Dict[str, int] = {}
        
        # Initialize
        self._initialize_weights()
        self.to(device)
    
    def _initialize_weights(self):
        """Initialize with small random weights for stable training."""
        nn.init.normal_(self.axiom_embeddings.weight, mean=0, std=0.1)
        for module in self.grounding_net:
            if hasattr(module, 'weight'):
                nn.init.xavier_uniform_(module.weight)
        for module in self.value_head:
            if hasattr(module, 'weight'):
                nn.init.xavier_uniform_(module.weight)
    
    def _compute_grounding_signal(self, 
                                   state: torch.Tensor, 
                                   axiom_def: AxiomDefinition) -> torch.Tensor:
        """Compute grounding signal from state features for an axiom."""
        if state.dim() == 1:
            state = state.unsqueeze(0)
        
        # Extract relevant features
        indices = axiom_def.feature_indices
        # Clamp indices to valid range
        valid_indices = [i for i in indices if i < state.shape[-1]]
        if not valid_indices:
            return torch.zeros(1, device=state.device)
        
        features = state[:, valid_indices]
        
        # Apply grounding function
        if axiom_def.grounding_fn == 'direct':
            return features.mean(dim=-1, keepdim=True)
        elif axiom_def.grounding_fn == 'inverse':
            return 1.0 - features.mean(dim=-1, keepdim=True)
        elif axiom_def.grounding_fn == 'diff':
            if len(valid_indices) >= 2:
                return (features[:, 0:1] - features[:, 1:2]) * 0.5 + 0.5
            return features.mean(dim=-1, keepdim=True)
        elif axiom_def.grounding_fn == 'inverse_diff':
            if len(valid_indices) >= 2:
                diff = torch.abs(features[:, 0:1] - features[:, 1:2])
                return 1.0 - diff
            return torch.ones(state.shape[0], 1, device=state.device)
        else:  # 'mean'
            return features.mean(dim=-1, keepdim=True)
    
    def get_axiom_embedding(self, 
                            axiom: str, 
                            state: torch.Tensor) -> torch.Tensor:
        """
        Get grounded embedding for an axiom given current state.
        
        The embedding is modulated by state features, so GOOD means
        something different when organism is thriving vs struggling.
        """
        if axiom not in self.axiom_to_idx:
            raise ValueError(f"Unknown axiom: {axiom}")
        
        # GAP FIX C8: Validate state dimension
        if state.shape[-1] != self.state_dim:
            raise ValueError(
                f"State dimension mismatch: expected {self.state_dim}, "
                f"got {state.shape[-1]}"
            )
        
        # GAP FIX H5: Handle NaN/Inf in state
        if torch.isnan(state).any() or torch.isinf(state).any():
            logger.warning("Invalid state values detected, replacing with zeros")
            state = torch.nan_to_num(state, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Move state to same device as axiom_embeddings to prevent device mismatch
        embed_device = self.axiom_embeddings.weight.device
        state = state.to(embed_device)
        
        # Get base embedding
        idx = torch.tensor([self.axiom_to_idx[axiom]], device=embed_device)
        base_embed = self.axiom_embeddings(idx).squeeze(0)
        
        # Get state-based grounding
        if state.dim() == 1:
            state = state.unsqueeze(0)
        grounding = self.grounding_net(state).squeeze(0)
        
        # Get axiom-specific feature signal
        axiom_def = AXIOM_DEFINITIONS[axiom]
        feature_signal = self._compute_grounding_signal(state, axiom_def)
        
        # Modulate: base embedding + grounding * feature_signal
        # This makes the axiom context-dependent
        grounded_embed = base_embed + grounding * feature_signal
        
        return grounded_embed
    
    def compose(self,
                axiom_a: str,
                operator: str,
                axiom_b: str,
                state: torch.Tensor,
                store: bool = True) -> Tuple[torch.Tensor, str]:
        """
        Compose two axioms using an operator.
        
        Args:
            axiom_a: First axiom name
            operator: Operator name (WITH, CAUSE, MODIFY, SEQUENCE)
            axiom_b: Second axiom name
            state: Organism state for grounding
            store: Whether to store in concept memory
            
        Returns:
            (composed_embedding, concept_name)
        """
        embed_a = self.get_axiom_embedding(axiom_a, state)
        embed_b = self.get_axiom_embedding(axiom_b, state)
        
        if operator not in self.operators:
            raise ValueError(f"Unknown operator: {operator}")
        
        composed = self.operators[operator](embed_a, embed_b)
        concept_name = f"{axiom_a}_{operator}_{axiom_b}"
        
        if store:
            # GAP FIX C4: Thread-safe memory access
            with self._memory_lock:
                # GAP FIX C7: Prune if over limit
                if len(self.concept_memory) >= self.max_concept_memory:
                    self._prune_concept_memory()
                
                self.concept_memory[concept_name] = composed.detach().clone()
                self.concept_use_count[concept_name] = self.concept_use_count.get(concept_name, 0) + 1
                
                # Move to end for LRU tracking
                self.concept_memory.move_to_end(concept_name)
        
        return composed, concept_name
    
    def _prune_concept_memory(self):
        """GAP FIX C7: Prune least useful concepts when memory limit exceeded."""
        # Sort by utility (lowest first)
        sorted_concepts = sorted(
            list(self.concept_memory.keys()),
            key=lambda x: self.concept_utility.get(x, 0.0)
        )
        
        # Remove bottom 20%
        remove_count = max(1, len(sorted_concepts) // 5)
        for name in sorted_concepts[:remove_count]:
            del self.concept_memory[name]
            # Keep utility/use_count for statistics
        
        logger.debug(f"Pruned {remove_count} low-utility concepts")
    
    def predict_value(self, concept: torch.Tensor) -> torch.Tensor:
        """Predict expected reward/value for a concept."""
        if concept.dim() == 1:
            concept = concept.unsqueeze(0)
        return self.value_head(concept).squeeze(-1)
    
    def update_utility(self, concept_name: str, actual_reward: float, alpha: float = 0.1):
        """Update utility estimate for a concept based on actual reward."""
        # GAP FIX C4: Thread-safe utility update
        with self._memory_lock:
            if concept_name not in self.concept_utility:
                self.concept_utility[concept_name] = 0.0
            
            # Exponential moving average
            self.concept_utility[concept_name] = (
                (1 - alpha) * self.concept_utility[concept_name] + 
                alpha * actual_reward
            )
    
    def get_all_axiom_embeddings(self, state: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Get grounded embeddings for all axioms."""
        return {name: self.get_axiom_embedding(name, state) 
                for name in self.axiom_names}
    
    def export_concept_embeddings(self, state: torch.Tensor) -> Dict[str, np.ndarray]:
        """
        Export grounded axiom embeddings as numpy arrays for language system integration.
        
        SEMANTIC CONVERGENCE: These embeddings flow into ContextMemory's word embeddings,
        so axiom words like 'good', 'bad', 'self', 'other' inherit semantic meaning
        from the organism's current state-grounded understanding.
        
        Args:
            state: Organism state tensor (state_dim,) or (batch, state_dim)
            
        Returns:
            Dict mapping axiom name -> 64-dim numpy array
        """
        embeddings = {}
        with torch.no_grad():
            for axiom_name in self.axiom_names:
                try:
                    embed = self.get_axiom_embedding(axiom_name, state)
                    # Flatten to ensure 1D 64-dim array
                    embed_np = embed.cpu().numpy().astype(np.float32).flatten()
                    if len(embed_np) >= self.embed_dim:
                        embeddings[axiom_name] = embed_np[:self.embed_dim]
                    else:
                        embeddings[axiom_name] = embed_np
                except Exception as e:
                    logger.debug(f"Could not export embedding for {axiom_name}: {e}")
        return embeddings
    
    def get_useful_concepts(self, top_k: int = 10) -> List[Tuple[str, float, int]]:
        """Get most useful concepts: (name, utility, use_count)."""
        scored = [
            (name, self.concept_utility.get(name, 0.0), self.concept_use_count.get(name, 0))
            for name in self.concept_memory.keys()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def check_utility_health(self) -> Dict[str, Any]:
        """
        GAP FIX C6: Monitor utility distribution for convergence.
        
        Returns health metrics including whether utilities have converged
        (which would make the concept system useless).
        """
        utilities = list(self.concept_utility.values())
        if not utilities:
            return {'healthy': True, 'reason': 'no utilities yet', 'converged': False}
        
        mean_u = sum(utilities) / len(utilities)
        variance = sum((u - mean_u) ** 2 for u in utilities) / len(utilities)
        std_u = variance ** 0.5
        
        # Coefficient of variation (relative std)
        cv = std_u / abs(mean_u) if abs(mean_u) > 1e-6 else std_u
        
        # Converged if all utilities within 10% of mean
        converged = cv < 0.1 and len(utilities) > 1
        
        return {
            'healthy': not converged,
            'mean': mean_u,
            'std': std_u,
            'cv': cv,
            'converged': converged,
            'num_concepts': len(utilities),
            'utilities': dict(self.concept_utility)
        }
    
    def add_exploration_bonus(self, concept_name: str, bonus: float = 0.05):
        """
        GAP FIX C6: Add exploration bonus to underused concepts.
        
        Call this periodically to prevent utility convergence by boosting
        concepts that haven't been explored much.
        """
        use_count = self.concept_use_count.get(concept_name, 0)
        if use_count < 10:  # Underused
            with self._memory_lock:
                self.concept_utility[concept_name] = (
                    self.concept_utility.get(concept_name, 0.0) + bonus
                )
    
    def save_state(self, path: str):
        """Save concept system state."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        state = {
            'version': '1.1',  # GAP FIX H6: Add version for compatibility
            'model_state_dict': self.state_dict(),
            'concept_utility': self.concept_utility,
            'concept_use_count': self.concept_use_count,
        }
        torch.save(state, path)
        logger.info(f"ConceptSystem saved to {path}")
    
    def load_state(self, path: str):
        """Load concept system state."""
        if os.path.exists(path):
            state = torch.load(path, map_location=self.device_str)
            
            # GAP FIX H6: Version compatibility check
            version = state.get('version', '1.0')
            if version != '1.1':
                logger.warning(f"Loading older concept system state (v{version})")
            
            self.load_state_dict(state['model_state_dict'])
            self.concept_utility = state.get('concept_utility', {})
            self.concept_use_count = state.get('concept_use_count', {})
            logger.info(f"ConceptSystem loaded from {path} (v{version})")
        else:
            logger.warning(f"No concept system state found at {path}")


# =============================================================================
# CONCEPT HEAD - Third head for OrganismBrain
# =============================================================================

class ConceptHead(nn.Module):
    """
    Concept prediction head for OrganismBrain.
    
    Takes hidden state from brain and outputs:
    1. Axiom relevance scores (which axioms are active)
    2. Composition value predictions
    3. Context embedding for concept grounding
    """
    
    def __init__(self,
                 hidden_dim: int = 64,
                 num_axioms: int = 18,
                 num_compositions: int = 15):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_axioms = num_axioms
        self.num_compositions = num_compositions
        
        # Axiom relevance: which axioms are currently active
        self.axiom_relevance = nn.Linear(hidden_dim, num_axioms)
        
        # Composition value: predicted value of key compositions
        self.composition_value = nn.Linear(hidden_dim, num_compositions)
        
        # Context embedding: feeds into concept system grounding
        self.context_embed = nn.Linear(hidden_dim, hidden_dim)
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        nn.init.xavier_uniform_(self.axiom_relevance.weight)
        nn.init.xavier_uniform_(self.composition_value.weight)
        nn.init.xavier_uniform_(self.context_embed.weight)
        nn.init.zeros_(self.axiom_relevance.bias)
        nn.init.zeros_(self.composition_value.bias)
        nn.init.zeros_(self.context_embed.bias)
    
    def forward(self, hidden: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through concept head.
        
        Args:
            hidden: Hidden state from brain (batch, hidden_dim)
            
        Returns:
            Dict with 'axiom_relevance', 'composition_value', 'context'
        """
        return {
            'axiom_relevance': torch.sigmoid(self.axiom_relevance(hidden)),
            'composition_value': self.composition_value(hidden),
            'context': self.context_embed(hidden),
        }


# =============================================================================
# KEY COMPOSITIONS - Standard compositions for decision making
# =============================================================================

# These are the compositions that organisms use for understanding their situation
# Expanded from 5 to 15 to cover comprehensive situational awareness
KEY_COMPOSITIONS = [
    # SURVIVAL & EXISTENCE (2)
    ('SELF', 'WITH', 'EXIST'),      # Basic self-awareness of being alive
    ('EXIST', 'CAUSE', 'GOOD'),     # Survival instinct - living is valuable
    
    # SOCIAL DYNAMICS (4)
    ('SELF', 'WITH', 'OTHER'),      # Social connection awareness
    ('OTHER', 'CAUSE', 'GOOD'),     # Others can benefit me (cooperation)
    ('OTHER', 'CAUSE', 'BAD'),      # Others can harm me (threat detection)
    ('MANY', 'WITH', 'SELF'),       # Crowd/density awareness (alliances)
    
    # ACTION-CONSEQUENCE (3)
    ('DO', 'CAUSE', 'GOOD'),        # Actions lead to rewards
    ('DO', 'CAUSE', 'BAD'),         # Actions can backfire
    ('DO', 'SEQUENCE', 'GOOD'),     # Sequential planning leads to rewards
    
    # RESOURCE & VALUE (2)
    ('MORE', 'MODIFY', 'GOOD'),     # More resources = better
    ('SELF', 'WITH', 'BAD'),        # I'm struggling (triggers rest/isolate)
    
    # TEMPORAL AWARENESS (2)
    ('NOW', 'CAUSE', 'AFTER'),      # Present shapes future (delayed gratification)
    ('BEFORE', 'CAUSE', 'NOW'),     # Past shapes present (learning from history)
    
    # SPATIAL/ENVIRONMENTAL (1)
    ('THERE', 'MODIFY', 'GOOD'),    # Better opportunities elsewhere (move motivation)
    
    # COMPETITIVE (1)
    ('SELF', 'WITH', 'MORE'),       # I'm stronger (compete confidence)
]


def get_concept_config_defaults() -> Dict[str, Any]:
    """
    Get default configuration for concept system.
    
    IMPORTANT: These defaults must match config.json values!
    Architecture params like num_key_compositions define layer sizes.
    """
    return {
        'enabled': True,
        'embed_dim': 64,
        'concept_loss_weight': 0.1,  # Weight in triple-loss
        'utility_update_alpha': 0.1,
        'key_compositions': KEY_COMPOSITIONS,
        'num_key_compositions': 20,  # ARCHITECTURE PARAM - must match config.json!
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_concept_system(config: Dict[str, Any], device: str = 'cpu') -> Optional[ConceptSystem]:
    """Create concept system from config."""
    concept_config = config.get('neural', {}).get('concept_system', {})
    if not concept_config.get('enabled', False):
        return None
    
    return ConceptSystem(
        state_dim=config.get('neural', {}).get('brain', {}).get('input_dim', 25),
        embed_dim=concept_config.get('embed_dim', 64),
        device=device
    )


def compute_concept_loss(concept_system: ConceptSystem,
                         state: torch.Tensor,
                         reward: torch.Tensor,
                         compositions: Optional[List[Tuple[str, str, str]]] = None) -> torch.Tensor:
    """
    Compute concept learning loss.
    
    This loss encourages:
    1. Concept value predictions to match actual rewards
    2. Useful compositions to be reinforced
    
    Args:
        concept_system: The concept system
        state: Organism state tensor (batch, state_dim)
        reward: Actual rewards (batch,)
        compositions: Which compositions to evaluate
        
    Returns:
        Concept loss scalar
    """
    if compositions is None:
        compositions = KEY_COMPOSITIONS
    
    # GAP FIX C5: Handle empty compositions list
    if not compositions:
        return torch.tensor(0.0, device=state.device, requires_grad=True)
    
    if state.dim() == 1:
        state = state.unsqueeze(0)
    if reward.dim() == 0:
        reward = reward.unsqueeze(0)
    
    total_loss = torch.tensor(0.0, device=state.device)
    
    for axiom_a, op, axiom_b in compositions:
        composed, name = concept_system.compose(axiom_a, op, axiom_b, state)
        predicted_value = concept_system.predict_value(composed)
        
        # Value prediction loss
        loss = F.mse_loss(predicted_value, reward)
        total_loss = total_loss + loss
        
        # Update utility tracking (no grad needed)
        with torch.no_grad():
            for i, r in enumerate(reward):
                concept_system.update_utility(name, r.item())
    
    # GAP FIX C5: Safe division
    return total_loss / max(len(compositions), 1)


# =============================================================================
# LANGUAGE BRIDGE - Connect Concepts to Vocabulary
# =============================================================================

class ConceptLanguageBridge:
    """
    Bridges between concept system and language system.
    
    Enables organisms to:
    - Express concepts using vocabulary words
    - Ground vocabulary words in concepts
    - Map between symbolic (words) and subsymbolic (embeddings) representations
    
    This connects RCUS to the existing LanguageTeacher system.
    """
    
    # AUDIT FIX: Stopwords to filter during phrase parsing
    STOPWORDS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'on', 'at', 'for'}
    
    # Mapping from axioms to associated vocabulary words
    AXIOM_VOCABULARY = {
        'EXIST': ['exist', 'be', 'presence', 'alive', 'real', 'is'],
        'ONE': ['one', 'single', 'alone', 'individual', 'only', 'sole'],
        'MANY': ['many', 'multiple', 'several', 'group', 'all', 'numerous'],
        'MORE': ['more', 'greater', 'higher', 'increased', 'better', 'larger'],
        'LESS': ['less', 'fewer', 'lower', 'decreased', 'smaller', 'reduced'],
        'SAME': ['same', 'equal', 'identical', 'similar', 'equivalent', 'like'],
        'SELF': ['self', 'me', 'I', 'myself', 'own', 'mine'],
        'OTHER': ['other', 'them', 'they', 'neighbor', 'external', 'different'],
        'WITH': ['with', 'together', 'connected', 'joined', 'alongside', 'and'],
        'GOOD': ['good', 'positive', 'beneficial', 'helpful', 'right', 'success'],
        'BAD': ['bad', 'negative', 'harmful', 'dangerous', 'wrong', 'failure'],
        'DO': ['do', 'act', 'perform', 'execute', 'make', 'take'],
        'CAUSE': ['cause', 'effect', 'result', 'lead', 'create', 'produce'],
        'BEFORE': ['before', 'prior', 'earlier', 'past', 'previous', 'ago'],
        'AFTER': ['after', 'later', 'future', 'next', 'following', 'then'],
        'NOW': ['now', 'current', 'present', 'moment', 'today', 'here'],
        'HERE': ['here', 'local', 'near', 'close', 'this', 'place'],
        'THERE': ['there', 'distant', 'far', 'away', 'remote', 'elsewhere'],
    }
    
    # Operator words for composition
    OPERATOR_VOCABULARY = {
        'WITH': ['with', 'and', 'together', 'plus'],
        'CAUSE': ['causes', 'leads', 'creates', 'makes'],
        'MODIFY': ['more', 'less', 'very', 'slightly'],
        'SEQUENCE': ['then', 'after', 'before', 'next'],
    }
    
    def __init__(self, concept_system: ConceptSystem, vocabulary: Any = None):
        """
        Initialize language bridge.
        
        Args:
            concept_system: The concept system to bridge
            vocabulary: Optional vocabulary object (from LanguageTeacher)
        """
        self.concept_system = concept_system
        self.vocabulary = vocabulary
        
        # Build reverse mapping: word -> axiom
        self.word_to_axiom: Dict[str, str] = {}
        for axiom, words in self.AXIOM_VOCABULARY.items():
            for word in words:
                self.word_to_axiom[word.lower()] = axiom
        
        # Build operator mapping
        self.word_to_operator: Dict[str, str] = {}
        for op, words in self.OPERATOR_VOCABULARY.items():
            for word in words:
                self.word_to_operator[word.lower()] = op
    
    def concept_to_phrase(self, concept_name: str) -> str:
        """
        Convert concept name to natural language phrase.
        
        Example: "SELF_WITH_OTHER" → "self with other"
        """
        parts = concept_name.split('_')
        
        if len(parts) == 3:
            axiom_a, op, axiom_b = parts
            word_a = self.AXIOM_VOCABULARY.get(axiom_a, [axiom_a.lower()])[0]
            word_op = op.lower()
            word_b = self.AXIOM_VOCABULARY.get(axiom_b, [axiom_b.lower()])[0]
            return f"{word_a} {word_op} {word_b}"
        else:
            return concept_name.lower().replace('_', ' ')
    
    def phrase_to_concept(self, phrase: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse natural language phrase into concept components.
        
        Example: "self with other" → ('SELF', 'WITH', 'OTHER')
        Example: "the self with the other" → ('SELF', 'WITH', 'OTHER')  # stopwords filtered
        """
        words = phrase.lower().split()
        
        # AUDIT FIX: Filter stopwords for more robust parsing
        words = [w for w in words if w not in self.STOPWORDS]
        
        if len(words) < 3:
            return None
        
        # Try to match axiom-operator-axiom pattern
        matched_a = self.word_to_axiom.get(words[0])
        matched_b = self.word_to_axiom.get(words[-1])
        
        # Find operator in middle words
        matched_op = None
        for word in words[1:-1]:
            if word in self.word_to_operator:
                matched_op = self.word_to_operator[word]
                break
            # Check if word is an operator name directly
            if word.upper() in self.concept_system.operators:
                matched_op = word.upper()
                break
        
        if matched_a and matched_op and matched_b:
            return (matched_a, matched_op, matched_b)
        
        return None
    
    def get_axiom_from_word(self, word: str) -> Optional[str]:
        """Get axiom associated with a vocabulary word."""
        return self.word_to_axiom.get(word.lower())
    
    def get_words_for_axiom(self, axiom: str) -> List[str]:
        """Get vocabulary words associated with an axiom."""
        return self.AXIOM_VOCABULARY.get(axiom, [])
    
    def explain_concept(self, concept_name: str) -> str:
        """
        Generate a natural language explanation of a concept.
        
        Example: "DO_CAUSE_GOOD" → "Taking action leads to positive outcomes"
        """
        parts = concept_name.split('_')
        
        if len(parts) == 3:
            axiom_a, op, axiom_b = parts
            
            # Get axiom definitions
            def_a = AXIOM_DEFINITIONS.get(axiom_a)
            def_b = AXIOM_DEFINITIONS.get(axiom_b)
            
            if def_a and def_b:
                if op == 'WITH':
                    return f"{def_a.description} together with {def_b.description.lower()}"
                elif op == 'CAUSE':
                    return f"{def_a.description} leads to {def_b.description.lower()}"
                elif op == 'MODIFY':
                    return f"{def_a.description} modifies {def_b.description.lower()}"
                elif op == 'SEQUENCE':
                    return f"{def_a.description} followed by {def_b.description.lower()}"
        
        return f"Concept: {self.concept_to_phrase(concept_name)}"
    
    def get_grounded_axiom_words(self, 
                                  state: torch.Tensor,
                                  threshold: float = 0.3) -> List[str]:
        """
        Get vocabulary words for axioms that are strongly grounded in current state.
        
        This allows organisms to "speak" about their current situation
        using words that match their grounded experience.
        
        Args:
            state: Current organism state
            threshold: Minimum grounding strength to include (default 0.3 for better coverage)
            
        Returns:
            List of relevant vocabulary words
        """
        relevant_words = []
        
        for axiom_name, axiom_def in AXIOM_DEFINITIONS.items():
            # Compute grounding signal for this axiom
            grounding = self.concept_system._compute_grounding_signal(state, axiom_def)
            strength = grounding.mean().item()
            
            if strength > threshold:
                # Add associated words, weighted by strength
                words = self.AXIOM_VOCABULARY.get(axiom_name, [])
                relevant_words.extend(words[:int(1 + strength * 2)])  # More words for stronger grounding
        
        return relevant_words
    
    def seed_vocabulary_with_axioms(self, vocabulary: Any) -> int:
        """
        Seed a vocabulary object with axiom words.
        
        Ensures all axiom-related words are in the vocabulary.
        
        Args:
            vocabulary: Vocabulary object with add_word method
            
        Returns:
            Number of words added
        """
        added = 0
        if vocabulary is None:
            return added
        
        # Add all axiom words
        for axiom, words in self.AXIOM_VOCABULARY.items():
            for word in words:
                try:
                    if hasattr(vocabulary, 'add_word'):
                        vocabulary.add_word(word)
                        added += 1
                    elif hasattr(vocabulary, 'add'):
                        vocabulary.add(word)
                        added += 1
                except Exception:
                    pass  # Word may already exist
        
        # Add operator words
        for op, words in self.OPERATOR_VOCABULARY.items():
            for word in words:
                try:
                    if hasattr(vocabulary, 'add_word'):
                        vocabulary.add_word(word)
                        added += 1
                    elif hasattr(vocabulary, 'add'):
                        vocabulary.add(word)
                        added += 1
                except Exception:
                    pass
        
        logger.info(f"Seeded vocabulary with {added} axiom/operator words")
        return added

