"""
NeuralOrganism - Organism with Neural Brain

Extends the base Organism class with PyTorch neural network capabilities
for decision-making through reinforcement learning.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import field

# Import base Organism class
try:
    from ..evolution_engine import Organism, Genotype, Phenotype
except ImportError:
    from evolution_engine import Organism, Genotype, Phenotype

# Import neural components
try:
    from .brain import OrganismBrain
    from .utils import get_device, get_breath_features, normalize_features
    from .experience import ExperienceBuffer
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
                 phenotype: Optional[Phenotype] = None,
                 config: Optional[Dict[str, Any]] = None,
                 parent_brain: Optional[OrganismBrain] = None):
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
            
            if parent_brain is not None:
                # Inherit from parent with mutation
                inheritance_config = neural_config.get('inheritance', {})
                mutation_rate = inheritance_config.get('mutation_rate', 0.1)
                crossover_rate = inheritance_config.get('crossover_rate', 0.5)
                
                # Create new brain via crossover
                self.brain = parent_brain.crossover(parent_brain, crossover_rate)
                # Add mutation
                self.brain.mutate(mutation_rate)
            else:
                # Create new brain
                from .utils import create_brain
                self.brain = create_brain(neural_config)
            
            # Experience storage
            self.experience_buffer = ExperienceBuffer(
                capacity=neural_config.get('training', {}).get('memory_size', 1000)
            )
            
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
    
    def decide_action(self, 
                     local_env: Optional[Dict[str, Any]] = None,
                     network_state: Optional[Dict[str, Any]] = None,
                     breath_state: Optional[Dict[str, Any]] = None) -> int:
        """
        Decide action using neural network.
        
        Args:
            local_env: Local environment information
            network_state: Network state information
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
        
        # Get action from brain
        action = self.brain.get_action(state, epsilon=self.epsilon)
        
        # Get action probabilities for event emission
        action_probs = None
        if hasattr(self.brain, 'get_action_probs'):
            action_probs = self.brain.get_action_probs(state)
        elif hasattr(self.brain, 'forward'):
            import torch
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
        
        # Calculate confidence (max probability)
        confidence = float(np.max(action_probs)) if action_probs is not None else 0.5
        
        # Emit neural decision event for visualization
        if self.event_emitter and confidence > 0.8:  # Only emit high-confidence decisions
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
                'action_probs': action_probs.tolist() if action_probs is not None else None
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
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        return action
    
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

