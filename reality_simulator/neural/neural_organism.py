"""
NeuralOrganism - Organism with Neural Brain

Extends the base Organism class with PyTorch neural network capabilities
for decision-making through reinforcement learning.

Extended with:
- Sequence tracking for language model training
- Token sequence storage via deque sliding windows
- Communication pattern extraction
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import field
from collections import deque

# Import base Organism class
try:
    from ..evolution_engine import Organism, Genotype, Phenotype
except ImportError:
    try:
        from reality_simulator.evolution_engine import Organism, Genotype, Phenotype
    except ImportError:
        from evolution_engine import Organism, Genotype, Phenotype

# Import neural components
try:
    from .brain import OrganismBrain
    from .utils import get_device, get_breath_features, normalize_features
    from .experience import ExperienceBuffer
    PYTORCH_AVAILABLE = True
except ImportError:
    # Fallback to absolute imports
    try:
        from reality_simulator.neural.brain import OrganismBrain
        from reality_simulator.neural.utils import get_device, get_breath_features, normalize_features
        from reality_simulator.neural.experience import ExperienceBuffer
        PYTORCH_AVAILABLE = True
    except ImportError:
        PYTORCH_AVAILABLE = False
        OrganismBrain = None


class NeuralOrganism(Organism):
    """
    Organism with neural network brain for decision-making.
    
    Extends the base Organism class with:
    - Neural brain for action selection
    - Experience storage for training
    - State feature extraction
    - Brain inheritance during reproduction
    """
    
    def __init__(self, 
                 genotype: Genotype, 
                 phenotype: 'Phenotype' = None,
                 config: Optional[Dict[str, Any]] = None,
                 parent_brains: Optional[List['OrganismBrain']] = None,
                 parent_brain: Optional['OrganismBrain'] = None):  # Deprecated, use parent_brains
        """
        Initialize neural organism.
        
        Args:
            genotype: Organism genotype
            phenotype: Organism phenotype (defaults to new Phenotype)
            config: Neural configuration dictionary
            parent_brain: Parent brain for inheritance (optional)
        """
        # Initialize base Organism
        if phenotype is None:
            phenotype = Phenotype()
        super().__init__(genotype, phenotype)
        
        self.config = config or {}
        neural_config = self.config.get('neural', {})
        
        # Optional event emitter for causation graph visualization
        self.event_emitter = None  # Set by main.py or unified_entry.py
        
        # Initialize brain
        if PYTORCH_AVAILABLE and neural_config.get('enabled', False):
            brain_config = neural_config.get('brain', {})
            
            # Handle legacy parent_brain parameter
            if parent_brains is None and parent_brain is not None:
                parent_brains = [parent_brain]
            
            if parent_brains is not None and len(parent_brains) > 0:
                # Inherit from parent(s) with mutation
                inheritance_config = neural_config.get('inheritance', {})
                mutation_rate = inheritance_config.get('mutation_rate', 0.1)
                crossover_rate = inheritance_config.get('crossover_rate', 0.5)
                
                if len(parent_brains) >= 2:
                    # Two parents: proper crossover
                    self.brain = parent_brains[0].crossover(parent_brains[1], crossover_rate)
                else:
                    # Single parent: copy weights directly
                    from .brain import OrganismBrain
                    self.brain = OrganismBrain(
                        input_dim=brain_config.get('input_dim', 12),
                        hidden_dim=brain_config.get('hidden_dim', 64),
                        output_dim=brain_config.get('output_dim', 6),
                        activation=brain_config.get('activation', 'relu'),
                        dropout=brain_config.get('dropout', 0.1)
                    )
                    # Move to same device as parent
                    device = next(parent_brains[0].parameters()).device
                    self.brain = self.brain.to(device)
                    self.brain.load_state_dict(parent_brains[0].state_dict())
                
                # Add mutation
                self.brain.mutate(mutation_rate)
            else:
                # Create new brain
                try:
                    from .utils import create_brain
                except ImportError:
                    from reality_simulator.neural.utils import create_brain
                self.brain = create_brain(neural_config)
            
            # Experience storage
            self.experience_buffer = ExperienceBuffer(
                capacity=neural_config.get('training', {}).get('memory_size', 1000)
            )
            
            # Sequence tracking for language model (deque auto-truncates)
            language_config = neural_config.get('language_model', {})
            max_seq_len = language_config.get('max_sequence_length', 128)
            self.action_history = deque(maxlen=max_seq_len)  # Recent actions
            self.state_history = deque(maxlen=max_seq_len)   # Recent states
            self.token_sequence = deque(maxlen=max_seq_len)  # Token IDs for LM training
            
            # Track previous state for experience recording
            self.prev_state = None
            self.prev_action = None
            self.prev_fitness = self.fitness
            
            # Epsilon for exploration (starts high, decays)
            training_config = neural_config.get('training', {})
            self.epsilon = training_config.get('epsilon_start', 1.0)
            self.epsilon_end = training_config.get('epsilon_end', 0.01)
            self.epsilon_decay = training_config.get('epsilon_decay', 0.995)
        else:
            self.brain = None
            self.experience_buffer = None
            self.action_history = deque(maxlen=128)
            self.state_history = deque(maxlen=128)
            self.token_sequence = deque(maxlen=128)
            self.prev_state = None
            self.prev_action = None
            self.prev_fitness = self.fitness
            self.epsilon = 0.0
    
    def get_state_features(self, 
                          local_env: Optional[Dict[str, Any]] = None,
                          network_state: Optional[Dict[str, Any]] = None,
                          breath_state: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Extract state features for neural input.
        
        Args:
            local_env: Local environment information
            network_state: Network state information
            breath_state: Breath engine state
            
        Returns:
            Feature array of shape (input_dim,)
        """
        if self.brain is None:
            return np.zeros(12, dtype=np.float32)
        
        features = []
        
        # 1. Current fitness (normalized)
        features.append(np.clip(self.fitness, 0.0, 1.0))
        
        # 2. Resource level (from local_env or network_state)
        resource_level = 0.5  # Default
        if local_env:
            resource_level = local_env.get('resources', 0.5)
        elif network_state:
            # Try to get resource from network state
            resource_level = network_state.get('resource_pool', 200.0) / 200.0
        features.append(np.clip(resource_level, 0.0, 1.0))
        
        # 3. Number of connections (normalized)
        num_connections = 0.0
        if network_state:
            organism_id = self.species_id
            connections = network_state.get('connections', {})
            # Count connections for this organism
            num_connections = sum(1 for (a, b) in connections.keys() 
                                if a == organism_id or b == organism_id)
            # Normalize by max connections
            max_conn = network_state.get('max_connections_per_organism', 15)
            num_connections = min(num_connections / max_conn, 1.0)
        features.append(num_connections)
        
        # 4. Average neighbor fitness
        avg_neighbor_fitness = 0.5  # Default
        if network_state:
            # Calculate from network state if available
            neighbors = network_state.get('neighbors', {}).get(self.species_id, [])
            if neighbors:
                neighbor_fitnesses = [n.get('fitness', 0.5) for n in neighbors]
                avg_neighbor_fitness = np.mean(neighbor_fitnesses) if neighbor_fitnesses else 0.5
        features.append(np.clip(avg_neighbor_fitness, 0.0, 1.0))
        
        # 5-6. Resource flow in/out
        flow_in = 0.0
        flow_out = 0.0
        if network_state:
            flows = network_state.get('flows', {})
            # Calculate flows for this organism
            for (a, b), flow in flows.items():
                if a == self.species_id:
                    flow_out += abs(flow) if flow < 0 else 0
                    flow_in += flow if flow > 0 else 0
                elif b == self.species_id:
                    flow_in += abs(flow) if flow > 0 else 0
                    flow_out += flow if flow < 0 else 0
            # Normalize
            flow_in = np.clip(flow_in / 10.0, 0.0, 1.0)
            flow_out = np.clip(flow_out / 10.0, 0.0, 1.0)
        features.append(flow_in)
        features.append(flow_out)
        
        # 7. Network clustering coefficient (local)
        clustering = 0.5  # Default
        if network_state:
            clustering = network_state.get('clustering_coefficient', 0.5)
        features.append(np.clip(clustering, 0.0, 1.0))
        
        # 8. Distance to nearest neighbor
        distance = 1.0  # Default (far)
        if network_state:
            neighbors = network_state.get('neighbors', {}).get(self.species_id, [])
            if neighbors:
                distances = [n.get('distance', 1.0) for n in neighbors]
                distance = min(distances) if distances else 1.0
            # Normalize (assuming max distance of 10)
            distance = np.clip(distance / 10.0, 0.0, 1.0)
        features.append(distance)
        
        # 9. Generation age (normalized)
        age = 0.0  # Default
        if network_state:
            generation = network_state.get('generation', 0)
            # Normalize by max generations (assume 1000)
            age = np.clip(generation / 1000.0, 0.0, 1.0)
        features.append(age)
        
        # 10. Parent fitness average
        parent_fitness = 0.5  # Default
        if self.parent_ids:
            # Would need access to parent organisms to calculate
            # For now, use own fitness as proxy
            parent_fitness = self.fitness
        features.append(np.clip(parent_fitness, 0.0, 1.0))
        
        # 11-12. Breath features
        breath_features = get_breath_features(breath_state)
        features.extend(breath_features.tolist())

        # 13-17. Violation Pressure component features (system health perception)
        # Pull from network_state['vp_components'] if provided by SymbioticNetwork
        vp_comp = {}
        if network_state:
            vp_comp = network_state.get('vp_components', {}) or {}
        # Maintain stable feature order with safe defaults
        features.append(float(vp_comp.get('trait_divergence', 0.0)))
        features.append(float(vp_comp.get('network_coherence', 0.0)))
        features.append(float(vp_comp.get('quantum_entropy', 0.0)))
        features.append(float(vp_comp.get('evolution_pressure', 0.0)))
        features.append(float(vp_comp.get('phase_mismatch', 0.0)))
        
        # 18. System health (Quick Win #5) - unified ecosystem wellness signal
        # Pull from network_state['system_health'] if provided by SymbioticNetwork
        system_health = 0.5  # Neutral default
        if network_state:
            system_health = float(network_state.get('system_health', 0.5))
        features.append(np.clip(system_health, 0.0, 1.0))
        
        # Ensure we have exactly input_dim features
        input_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 12)
        feature_array = np.array(features[:input_dim], dtype=np.float32)
        
        # Pad or truncate to match input_dim
        if len(feature_array) < input_dim:
            feature_array = np.pad(feature_array, (0, input_dim - len(feature_array)), 
                                 constant_values=0.5)
        elif len(feature_array) > input_dim:
            feature_array = feature_array[:input_dim]
        
        return feature_array
    
    def _apply_vp_aware_adjustments(self, 
                                    action_probs: np.ndarray,
                                    vp_components: Dict[str, float]) -> np.ndarray:
        """
        Apply VP-aware adjustments to action probabilities.
        
        This implements ecosystem-aware decision making where organisms
        consider system health when choosing actions.
        
        Action indices:
            0 = move (exploration/dispersal)
            1 = cooperate (form connections, share resources)
            2 = compete (resource acquisition)
            3 = rest (stabilization, conservation)
            4 = reproduce (increase diversity)
            5 = isolate (reduce connections)
        
        VP Component Mappings:
            - High trait_divergence → boost reproduce (increase genetic diversity)
            - Low network_coherence → boost cooperate (improve connectivity)
            - High quantum_entropy → boost rest (stabilization)
            - High evolution_pressure → boost move (seek better environment)
            - High phase_mismatch → boost rest (synchronization)
        
        Args:
            action_probs: Base action probabilities from neural network
            vp_components: VP component values from network_state
            
        Returns:
            Adjusted action probabilities (normalized)
        """
        vp_config = self.config.get('neural', {}).get('vp_aware_planning', {})
        
        # Get adjustment weights (configurable)
        base_boost = vp_config.get('base_boost', 0.15)
        strong_boost = vp_config.get('strong_boost', 0.25)
        
        # Get thresholds for triggering adjustments
        high_threshold = vp_config.get('high_threshold', 0.5)
        low_threshold = vp_config.get('low_threshold', 0.3)
        
        # Make a copy to modify
        adjusted = action_probs.copy()
        
        # Track adjustments for logging
        adjustments_made = []
        
        # Rule 1: High trait_divergence → boost reproduce (action 4)
        # When genetic diversity is causing VP issues, encourage reproduction
        trait_div = vp_components.get('trait_divergence', 0.0)
        if trait_div > high_threshold:
            adjusted[4] += strong_boost  # reproduce
            adjustments_made.append(f"trait_div({trait_div:.2f})→reproduce+{strong_boost}")
        elif trait_div > low_threshold:
            adjusted[4] += base_boost
            adjustments_made.append(f"trait_div({trait_div:.2f})→reproduce+{base_boost}")
        
        # Rule 2: Low network_coherence → boost cooperate (action 1)
        # When network is fragmented, encourage connection formation
        net_coh = vp_components.get('network_coherence', 0.0)
        if net_coh > high_threshold:  # High VP means LOW coherence
            adjusted[1] += strong_boost  # cooperate
            adjusted[5] -= base_boost   # reduce isolate tendency
            adjustments_made.append(f"net_coh({net_coh:.2f})→cooperate+{strong_boost}")
        elif net_coh > low_threshold:
            adjusted[1] += base_boost
            adjustments_made.append(f"net_coh({net_coh:.2f})→cooperate+{base_boost}")
        
        # Rule 3: High quantum_entropy → boost rest (action 3)
        # When quantum layer is chaotic, encourage stabilization
        q_entropy = vp_components.get('quantum_entropy', 0.0)
        if q_entropy > high_threshold:
            adjusted[3] += strong_boost  # rest
            adjusted[0] -= base_boost   # reduce move (less chaos)
            adjustments_made.append(f"q_entropy({q_entropy:.2f})→rest+{strong_boost}")
        elif q_entropy > low_threshold:
            adjusted[3] += base_boost
            adjustments_made.append(f"q_entropy({q_entropy:.2f})→rest+{base_boost}")
        
        # Rule 4: High evolution_pressure → boost move (action 0)
        # When evolution is stressed, encourage exploration for better niches
        evo_pressure = vp_components.get('evolution_pressure', 0.0)
        if evo_pressure > high_threshold:
            adjusted[0] += strong_boost  # move
            adjusted[3] -= base_boost   # reduce rest (be active)
            adjustments_made.append(f"evo_pressure({evo_pressure:.2f})→move+{strong_boost}")
        elif evo_pressure > low_threshold:
            adjusted[0] += base_boost
            adjustments_made.append(f"evo_pressure({evo_pressure:.2f})→move+{base_boost}")
        
        # Rule 5: High phase_mismatch → boost rest (action 3)
        # When phase sync is off, encourage settling to resync
        phase_mis = vp_components.get('phase_mismatch', 0.0)
        if phase_mis > high_threshold:
            adjusted[3] += strong_boost  # rest
            adjustments_made.append(f"phase_mis({phase_mis:.2f})→rest+{strong_boost}")
        elif phase_mis > low_threshold:
            adjusted[3] += base_boost
            adjustments_made.append(f"phase_mis({phase_mis:.2f})→rest+{base_boost}")
        
        # Ensure no negative probabilities
        adjusted = np.maximum(adjusted, 0.01)
        
        # Renormalize to valid probability distribution
        adjusted = adjusted / adjusted.sum()
        
        return adjusted, adjustments_made
    
    def decide_action(self, 
                     local_env: Optional[Dict[str, Any]] = None,
                     network_state: Optional[Dict[str, Any]] = None,
                     breath_state: Optional[Dict[str, Any]] = None) -> int:
        """
        Decide action using neural network with optional VP-aware planning.
        
        Args:
            local_env: Local environment information
            network_state: Network state information (includes vp_components)
            breath_state: Breath engine state
            
        Returns:
            Action index (0-5: move, cooperate, compete, rest, reproduce, isolate)
        """
        # Fallback to genetic behavior if neural not enabled
        if self.brain is None:
            # Return random action as fallback
            return np.random.randint(0, 6)
        
        # Extract state features
        state = self.get_state_features(local_env, network_state, breath_state)
        
        # Check if VP-aware planning is enabled
        vp_planning_enabled = self.config.get('neural', {}).get('vp_aware_planning', {}).get('enabled', False)
        
        # Get action probabilities from brain
        import torch
        action_probs = None
        vp_adjustments = []
        
        if np.random.random() < self.epsilon:
            # Exploration: random action (but still get probs for logging)
            action = np.random.randint(0, 6)
            if hasattr(self.brain, 'forward'):
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
        else:
            # Exploitation: use neural network with optional VP adjustments
            self.brain.eval()
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
            
            # Apply VP-aware adjustments if enabled
            if vp_planning_enabled and network_state:
                vp_components = network_state.get('vp_components', {})
                if vp_components:
                    action_probs, vp_adjustments = self._apply_vp_aware_adjustments(
                        action_probs, vp_components
                    )
            
            # Select action from (possibly adjusted) probabilities
            action = int(np.argmax(action_probs))
        
        # Calculate confidence (max probability)
        confidence = float(np.max(action_probs)) if action_probs is not None else 0.5
        
        # Emit neural decision event for visualization
        # Allow events during exploration (high epsilon) OR when confidence is meaningful
        if self.event_emitter and (confidence > 0.5 or self.epsilon > 0.5):
            import time
            action_names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
            action_name = action_names[action] if 0 <= action < len(action_names) else 'unknown'
            
            event_data = {
                'organism_id': self.species_id,
                'action': action_name,
                'action_index': int(action),
                'confidence': confidence,
                'epsilon': float(self.epsilon),
                'fitness': float(self.fitness),
                'input_features': state.tolist() if isinstance(state, np.ndarray) else state,
                'action_probs': action_probs.tolist() if action_probs is not None else None,
                'vp_planning_enabled': vp_planning_enabled,
                'vp_adjustments': vp_adjustments if vp_adjustments else None
            }
            
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_decision',
                    data=event_data
                )
                self.event_emitter(event)
            except ImportError:
                pass  # CausationExplorer not available
        
        # Store for experience recording
        self.prev_state = state
        self.prev_action = action
        
        # Update sequence histories for language model training
        self.action_history.append(action)
        self.state_history.append(state.copy() if isinstance(state, np.ndarray) else state)
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        return action
    
    def get_action_sequence(self, length: Optional[int] = None) -> List[int]:
        """
        Get recent action history for language model training.
        
        Args:
            length: Maximum length to return (None = all)
            
        Returns:
            List of recent action indices
        """
        actions = list(self.action_history)
        if length is not None:
            return actions[-length:]
        return actions
    
    def get_token_sequence(self, length: Optional[int] = None) -> List[int]:
        """
        Get token sequence for language model training.
        
        Args:
            length: Maximum length to return (None = all)
            
        Returns:
            List of token IDs
        """
        tokens = list(self.token_sequence)
        if length is not None:
            return tokens[-length:]
        return tokens
    
    def append_tokens(self, token_ids: List[int]) -> None:
        """
        Append token IDs to the organism's sequence.
        
        Args:
            token_ids: Token IDs to append
        """
        for token_id in token_ids:
            self.token_sequence.append(token_id)
    
    def extract_communication_pattern(self, 
                                       network_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract communication pattern from recent organism activity.
        
        This creates a tokenizable representation of the organism's
        actions, connections, and resource flows.
        
        Args:
            network_state: Current network state
            
        Returns:
            Dictionary with communication pattern data
        """
        pattern = {
            'organism_id': self.species_id,
            'action_sequence': list(self.action_history),
            'fitness_trend': self._calculate_fitness_trend(),
            'connection_events': [],
            'resource_events': []
        }
        
        if network_state:
            # Extract connection information
            connections = network_state.get('connections', {})
            for (a, b), conn_data in connections.items():
                if a == self.species_id or b == self.species_id:
                    pattern['connection_events'].append({
                        'partner': b if a == self.species_id else a,
                        'type': conn_data.get('type', 'unknown'),
                        'strength': conn_data.get('strength', 0.0)
                    })
            
            # Extract resource flow
            flows = network_state.get('flows', {})
            for (a, b), flow in flows.items():
                if a == self.species_id:
                    pattern['resource_events'].append({'direction': 'out', 'amount': flow})
                elif b == self.species_id:
                    pattern['resource_events'].append({'direction': 'in', 'amount': flow})
        
        return pattern
    
    def _calculate_fitness_trend(self) -> str:
        """Calculate fitness trend from state history."""
        if len(self.state_history) < 2:
            return 'stable'
        
        # Fitness is first feature in state
        recent_fitness = [s[0] if isinstance(s, np.ndarray) and len(s) > 0 else 0.5 
                         for s in list(self.state_history)[-5:]]
        
        if len(recent_fitness) < 2:
            return 'stable'
        
        trend = recent_fitness[-1] - recent_fitness[0]
        if trend > 0.1:
            return 'improving'
        elif trend < -0.1:
            return 'declining'
        return 'stable'
    
    def record_experience(self, 
                         reward: float,
                         next_state: Optional[np.ndarray] = None,
                         done: bool = False):
        """
        Record experience for training.
        
        Args:
            reward: Reward received
            next_state: Next state (if None, uses current state)
            done: Whether episode is done
        """
        if (self.brain is None or 
            self.experience_buffer is None or 
            self.prev_state is None or 
            self.prev_action is None):
            return
        
        if next_state is None:
            # Use current state as next state
            next_state = self.prev_state.copy()
        
        # Add experience to buffer
        self.experience_buffer.add(
            state=self.prev_state,
            action=self.prev_action,
            reward=reward,
            next_state=next_state,
            done=done
        )
        
        # Update previous fitness
        self.prev_fitness = self.fitness
    
    def should_connect(self, 
                      other_organism: 'NeuralOrganism',
                      network_state: Optional[Dict[str, Any]] = None,
                      breath_state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Neural decision: Should this organism connect to another?
        
        Args:
            other_organism: Other organism to potentially connect to
            network_state: Network state information
            breath_state: Breath engine state
            
        Returns:
            True if should connect, False otherwise
        """
        if self.brain is None:
            # Fallback: use fitness difference heuristic
            fitness_diff = abs(self.fitness - other_organism.fitness)
            return fitness_diff < 0.3  # Connect if similar fitness
        
        # Get state features
        state = self.get_state_features(
            local_env={'other_fitness': other_organism.fitness},
            network_state=network_state,
            breath_state=breath_state
        )
        
        # Get action
        action = self.brain.get_action(state, epsilon=self.epsilon)
        
        # Action 1 (cooperate) means connect
        # Action 2 (compete) means don't connect
        return action == 1
    
    def generate_tokens(self, 
                         context_memory: Any = None,
                         max_length: int = 32,
                         vp_value: Optional[float] = None,
                         temperature: float = 1.0) -> List[int]:
        """
        Generate token sequence using the language head (autoregressive).
        
        VP gating: Only generates if VP is below threshold (stable system).
        Higher VP = more cautious = shorter/no generation.
        
        Args:
            context_memory: ContextMemory instance with vocabulary
            max_length: Maximum tokens to generate
            vp_value: Current VP value (if None, generates freely)
            temperature: Sampling temperature (higher = more random)
            
        Returns:
            List of generated token IDs
        """
        if self.brain is None:
            return []
        
        # VP gating - don't generate during high uncertainty
        if vp_value is not None and vp_value > 0.5:
            return []  # System too unstable for language generation
        
        import torch
        
        # Get vocabulary from context memory
        if context_memory is None or not hasattr(context_memory, 'vocabulary'):
            return []
        
        vocab = context_memory.vocabulary
        
        # Import special tokens for range checking
        try:
            from ..language_system import SPECIAL_TOKENS
        except ImportError:
            try:
                from reality_simulator.language_system import SPECIAL_TOKENS
            except ImportError:
                SPECIAL_TOKENS = {'<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3, '<VP_GATE>': 4}
        
        generated = [vocab.get_id('<START>')]
        
        self.brain.eval()
        with torch.no_grad():
            # Start with current state as context
            if len(self.state_history) > 0:
                state = self.state_history[-1]
                if isinstance(state, np.ndarray):
                    state_tensor = torch.FloatTensor(state).unsqueeze(0)
                else:
                    state_tensor = torch.zeros(1, 12)  # Default input dim
            else:
                state_tensor = torch.zeros(1, 12)
            
            for _ in range(max_length - 1):
                # Get language logits from brain
                output = self.brain.forward(state_tensor, vp_value=vp_value)
                
                # If brain has language head, use it
                if hasattr(self.brain, 'fc_language'):
                    language_logits = self.brain.fc_language(
                        torch.relu(self.brain.fc2(
                            torch.relu(self.brain.fc1(state_tensor))
                        ))
                    )
                    
                    # Clamp logits to vocabulary size to avoid out-of-range tokens
                    vocab_size = vocab.vocab_size
                    if language_logits.shape[-1] > vocab_size:
                        language_logits = language_logits[..., :vocab_size]
                    
                    # Apply temperature
                    logits = language_logits[0] / temperature
                    probs = torch.softmax(logits, dim=-1)
                    
                    # Sample next token, ensuring it's within vocabulary range
                    next_token = torch.multinomial(probs, 1).item()
                    next_token = min(next_token, vocab_size - 1)  # Clamp to valid range
                    
                    # Ensure token maps to an actual word (not UNK)
                    # If token is UNK, try to find a valid word token nearby
                    word = vocab.get_word(next_token)
                    if word == '<UNK>' and vocab_size > len(SPECIAL_TOKENS):
                        # Try nearby tokens to find a valid word
                        non_special_size = vocab_size - len(SPECIAL_TOKENS)
                        for offset in range(1, min(10, non_special_size)):
                            # Try both directions
                            for direction in [-1, 1]:
                                candidate = next_token + (offset * direction)
                                if candidate >= len(SPECIAL_TOKENS) and candidate < vocab_size:
                                    candidate_word = vocab.get_word(candidate)
                                    if candidate_word and candidate_word != '<UNK>':
                                        next_token = candidate
                                        break
                            if vocab.get_word(next_token) != '<UNK>':
                                break
                else:
                    # No language head, use action as pseudo-token
                    # Map action to a valid vocabulary token (use modulo to keep in range)
                    action_token = torch.argmax(output, dim=-1).item()
                    vocab_size = vocab.vocab_size
                    # Map action to vocabulary range (skip special tokens)
                    # Prevent division by zero if vocab only has special tokens
                    non_special_size = max(1, vocab_size - len(SPECIAL_TOKENS))
                    if non_special_size > 0:
                        # Map to valid word token range (after special tokens)
                        next_token = (action_token % non_special_size) + len(SPECIAL_TOKENS)
                        next_token = min(next_token, vocab_size - 1)
                        # Ensure token maps to an actual word (not just any ID)
                        # Try to find a valid word token by checking if it exists in vocabulary
                        max_attempts = min(10, non_special_size)
                        for attempt in range(max_attempts):
                            if next_token < vocab_size:
                                word = vocab.get_word(next_token)
                                if word and word != '<UNK>':
                                    break  # Found a valid word
                            # Try next token
                            next_token = ((next_token - len(SPECIAL_TOKENS) + 1) % non_special_size) + len(SPECIAL_TOKENS)
                    else:
                        # Vocabulary only has special tokens, use END to stop generation
                        next_token = vocab.get_id('<END>')
                
                generated.append(next_token)
                
                # Stop at END token
                if next_token == vocab.get_id('<END>'):
                    break
        
        return generated
    
    def inherit_brain(self, parent_brain: OrganismBrain, 
                     mutation_rate: float = 0.1,
                     crossover_rate: float = 0.5) -> Optional[OrganismBrain]:
        """
        Create new brain by inheriting from parent.
        
        Args:
            parent_brain: Parent brain to inherit from
            mutation_rate: Mutation rate for weights
            crossover_rate: Crossover rate for combining parents
            
        Returns:
            New brain, or None if PyTorch not available
        """
        if not PYTORCH_AVAILABLE or parent_brain is None:
            return None
        
        # Create new brain via crossover (with self if we have a brain)
        if self.brain is not None:
            new_brain = self.brain.crossover(parent_brain, crossover_rate)
        else:
            # Just copy and mutate parent
            from .brain import OrganismBrain
            neural_config = self.config.get('neural', {})
            brain_config = neural_config.get('brain', {})
            new_brain = OrganismBrain(
                input_dim=brain_config.get('input_dim', 12),
                hidden_dim=brain_config.get('hidden_dim', 64),
                output_dim=brain_config.get('output_dim', 6),
                activation=brain_config.get('activation', 'relu'),
                dropout=brain_config.get('dropout', 0.1)
            )
            # Copy parent weights
            new_brain.load_state_dict(parent_brain.state_dict())
        
        # Add mutation
        new_brain.mutate(mutation_rate)
        
        return new_brain

