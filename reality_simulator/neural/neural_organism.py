"""
NeuralOrganism - Organism with Neural Brain

Extends the base Organism class with PyTorch neural network capabilities
for decision-making through reinforcement learning.

Extended with:
- Sequence tracking for language model training
- Token sequence storage via deque sliding windows
- Communication pattern extraction
"""

import random
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import field
from collections import deque
import logging

logger = logging.getLogger(__name__)

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

# Import Atomic Language System
try:
    from ..language.atomic_language import AtomicLanguageSystem
    ATOMIC_LANGUAGE_AVAILABLE = True
except ImportError:
    try:
        from reality_simulator.language.atomic_language import AtomicLanguageSystem
        ATOMIC_LANGUAGE_AVAILABLE = True
    except ImportError:
        ATOMIC_LANGUAGE_AVAILABLE = False
        AtomicLanguageSystem = None


class NeuralOrganism(Organism):
    """
    Organism with neural network brain for decision-making.
    
    Extends the base Organism class with:
    - Neural brain for action selection
    - Experience storage for training
    - State feature extraction
    - Brain inheritance during reproduction
    
    Identity Note:
    - `species_id` is the canonical identifier (from genotype hash)
    - `organism_id` property aliases to `species_id` for clarity
    """
    
    @property
    def organism_id(self) -> str:
        """
        Canonical organism identifier.
        Aliases species_id for consistent naming across systems.
        """
        return self.species_id
    
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
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🔮 ILLUMINATION ENGINE SYSTEM REFERENCES
        # These are set externally when organism joins an alliance
        # If None, illumination is gracefully skipped (no breaking changes)
        # ═══════════════════════════════════════════════════════════════════════
        self._alliance_warfare_ref = None  # Set via set_system_references()
        self._causation_explorer_ref = None  # Set via set_system_references()
        self._landscape_ref = None  # AttractorLandscape for proximity sensing
        self._illumination_level = 'none'  # Cached level for quick checks
        self._illumination_capabilities = set()  # Cached capabilities
        
        # Initialize brain
        if PYTORCH_AVAILABLE and neural_config.get('enabled', False):
            brain_config = neural_config.get('brain', {})
            
            # Handle legacy parent_brain parameter
            if parent_brains is None and parent_brain is not None:
                parent_brains = [parent_brain]
            
            if parent_brains is not None and len(parent_brains) > 0:
                # Inherit from parent(s) with mutation
                inheritance_config = neural_config.get('inheritance', {})
                mutation_rate = inheritance_config.get('mutation_rate', 0.2)  # Default matches config.json
                crossover_rate = inheritance_config.get('crossover_rate', 0.9)  # Default matches config.json
                
                if len(parent_brains) >= 2:
                    # Two parents: proper crossover
                    self.brain = parent_brains[0].crossover(parent_brains[1], crossover_rate)
                else:
                    # Single parent: copy weights directly
                    from .brain import OrganismBrain
                    self.brain = OrganismBrain(
                        input_dim=brain_config.get('input_dim', 27),
                        hidden_dim=brain_config.get('hidden_dim', 64),
                        output_dim=brain_config.get('output_dim', 6),
                        activation=brain_config.get('activation', 'relu'),
                        dropout=brain_config.get('dropout', 0.1)
                    )
                    # Move to same device as parent
                    device = next(parent_brains[0].parameters()).device
                    self.brain = self.brain.to(device)
                    # Use strict=False to handle architecture changes (e.g., num_key_compositions)
                    self.brain.load_state_dict(parent_brains[0].state_dict(), strict=False)
                
                # Add mutation
                self.brain.mutate(mutation_rate)
            else:
                # Create new brain - pass FULL config so language_model section is accessible
                try:
                    from .utils import create_brain
                except ImportError:
                    from reality_simulator.neural.utils import create_brain
                self.brain = create_brain(self.config, silent=True)  # Silent mode for batch creation
            
            # Experience storage
            self.experience_buffer = ExperienceBuffer(
                capacity=neural_config.get('training', {}).get('memory_size', 20000)
            )
            
            # Sequence tracking for language model (deque auto-truncates)
            language_config = neural_config.get('language_model', {})
            max_seq_len = language_config.get('max_sequence_length', 128)
            self.action_history = deque(maxlen=max_seq_len)  # Recent actions
            self.state_history = deque(maxlen=max_seq_len)   # Recent states
        
        # Cache for language embeddings (Integration 1: Neural-ML Symbiosis)
        self._cached_embedding = None
        self._embedding_cache_state_hash = None
        
        # ?? ATOMIC LANGUAGE SYSTEM - Trackable linguistic units for Butterfly Engine
        self.atomic_language = None
        if ATOMIC_LANGUAGE_AVAILABLE:
            language_config = neural_config.get('language_model', {})
            if language_config.get('use_atomic_language', True):
                self.atomic_language = AtomicLanguageSystem(
                    organism_id=self.species_id,
                    event_emitter=self.event_emitter,
                    config=self.config
                )
        
        if PYTORCH_AVAILABLE and neural_config.get('enabled', False):
            # Sequence tracking for language model (deque auto-truncates)
            language_config = neural_config.get('language_model', {})
            max_seq_len = language_config.get('max_sequence_length', 128)
            self.token_sequence = deque(maxlen=max_seq_len)  # Token IDs for LM training
            
            # 🎰 TOKEN TUMBLER: Seed full sequence from phenotype for language training
            self._seed_token_sequence_from_phenotype(max_seq_len)
            
            # Track previous state for experience recording
            self.prev_state = None
            self.prev_action = None
            self.prev_fitness = self.fitness
            self.last_action = None  # For alliance system to check cooperation
            
            # Epsilon for exploration (starts high, decays)
            training_config = neural_config.get('training', {})
            self.epsilon = training_config.get('epsilon_start', 0.8)
            self.epsilon_end = training_config.get('epsilon_end', 0.01)
            self.epsilon_decay = training_config.get('epsilon_decay', 0.99)
            
            # Language epsilon for language exploration (alongside action epsilon)
            # Higher = more random token selection during inference (prevents mode collapse)
            # NOTE: Read from neural.language_model.training (NOT neural.training)
            language_training_config = neural_config.get('language_model', {}).get('training', {})
            self.language_epsilon = language_training_config.get('language_epsilon_start', 0.3)
            self.language_epsilon_end = language_training_config.get('language_epsilon_end', 0.05)
            self.language_epsilon_decay = language_training_config.get('language_epsilon_decay', 0.998)
            
            # Battle outcome tracking for learning (Integration: Neural-Alliance)
            self.battle_wins = 0
            self.battle_losses = 0
            
            # 🏆 Competition Stats (Tournament, Dojo, Highlander)
            self.tournament_wins = 0
            self.tournament_losses = 0
            self.dojo_sessions = 0
            self.skills_mastered = set()  # Games/skills organism has mastered
            self.win_streak = 0
            self.best_win_streak = 0
            self.gym_experiences = 0  # Total Gymnasium experiences recorded
            self.highlander_kills = 0  # Lethal tournament kills
            self.war_victories = 0  # Alliance wars won
            
            # Alliance/social tracking for extended features (Integration: Features 19-24)
            self.alliance_reputation = 0.5  # Neutral start
            self.fitness_history = []  # Track fitness over time for trend analysis
            self.age = 0  # Track organism age in simulation ticks
            
            # Confederation (Super-Alliance) tracking (Integration: Features 25-27)
            self.alliance_id = None  # Current alliance membership
            self.confederation_tier = 0  # 0=none, 1=confederation, 2=empire, 3=hegemony
            self.confederation_wars_participated = 0
            self.cross_alliance_connections = 0  # Connections to organisms in other alliances
        else:
            self.brain = None
            self.experience_buffer = None
            self.action_history = deque(maxlen=128)
            self.state_history = deque(maxlen=128)
            self.token_sequence = deque(maxlen=128)
            
            # 🎰 TOKEN TUMBLER: Seed even non-PyTorch organisms
            self._seed_token_sequence_from_phenotype(128)
            
            self.prev_state = None
            self.prev_action = None
            self.prev_fitness = self.fitness
            self.last_action = None  # For alliance system to check cooperation
            self.epsilon = 0.0
            self.language_epsilon = 0.0  # No exploration without PyTorch
            # Battle outcome tracking for learning
            self.battle_wins = 0
            self.battle_losses = 0
            
            # 🏆 Competition Stats (Tournament, Dojo, Highlander)
            self.tournament_wins = 0
            self.tournament_losses = 0
            self.dojo_sessions = 0
            self.skills_mastered = set()  # Games/skills organism has mastered
            self.win_streak = 0
            self.best_win_streak = 0
            self.gym_experiences = 0  # Total Gymnasium experiences recorded
            self.highlander_kills = 0  # Lethal tournament kills
            self.war_victories = 0  # Alliance wars won
            
            # Alliance/social tracking for extended features (Integration: Features 19-24)
            self.alliance_reputation = 0.5  # Neutral start
            self.fitness_history = []  # Track fitness over time for trend analysis
            self.age = 0  # Track organism age in simulation ticks
            
            # Confederation (Super-Alliance) tracking (Integration: Features 25-27)
            self.alliance_id = None  # Current alliance membership
            self.confederation_tier = 0  # 0=none, 1=confederation, 2=empire, 3=hegemony
            self.confederation_wars_participated = 0
            self.cross_alliance_connections = 0  # Connections to organisms in other alliances
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔮 ILLUMINATION ENGINE - System Reference Management
    # ═══════════════════════════════════════════════════════════════════════
    
    def set_system_references(self, 
                              alliance_warfare=None, 
                              causation_explorer=None,
                              attractor_landscape=None) -> None:
        """
        Set references to system-level components for illumination access.
        
        Called when organism joins an alliance or during system initialization.
        These references enable organisms to access collective wisdom.
        
        Note: Passing None for any argument preserves the existing reference
        (allows partial updates without wiping other references).
        
        Args:
            alliance_warfare: AllianceWarfareSystem instance (or None to preserve)
            causation_explorer: CausationExplorer instance (or None to preserve)
            attractor_landscape: AttractorLandscape instance (or None to preserve)
        """
        # Only update references that are explicitly provided (not None)
        if alliance_warfare is not None:
            self._alliance_warfare_ref = alliance_warfare
        if causation_explorer is not None:
            self._causation_explorer_ref = causation_explorer
        if attractor_landscape is not None:
            self._landscape_ref = attractor_landscape
        
        # Pre-cache illumination level if alliance warfare is available
        if alliance_warfare is not None:
            try:
                illumination = alliance_warfare.get_organism_illumination_level(self.species_id)
                self._illumination_level = illumination.get('level', 'none')
                self._illumination_capabilities = illumination.get('capabilities', set())
            except Exception:
                self._illumination_level = 'none'
                self._illumination_capabilities = set()
    
    def clear_system_references(self) -> None:
        """Clear system references (e.g., when organism leaves alliance)."""
        self._alliance_warfare_ref = None
        self._causation_explorer_ref = None
        self._landscape_ref = None
        self._illumination_level = 'none'
        self._illumination_capabilities = set()

    def get_illumination_level(self) -> str:
        """Get current illumination level."""
        return self._illumination_level

    def can_access_causation_features(self) -> bool:
        """Check if any causation features are accessible."""
        return self._illumination_level != 'none'

    def get_wisdom_from_causation(self, situation_context: Dict[str, Any]) -> List[str]:
        """
        Directly query causation engine for wisdom.
        
        Args:
            situation_context: Context for the query
            
        Returns:
            List of wisdom strings
        """
        if self._alliance_warfare_ref and self.alliance_id:
            return self._alliance_warfare_ref.get_alliance_wisdom(
                self.alliance_id, situation_context
            ).get('wisdom', [])
        return []

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
            return np.zeros(28, dtype=np.float32)  # 28D with self-perception
        
        features = []
        
        # 1. Current fitness (normalized)
        features.append(np.clip(self.fitness, 0.0, 1.0))
        
        # 2. Resource level (from local_env or network_state)
        resource_level = 0.5  # Default
        if local_env:
            resource_level = local_env.get('resources', 0.5)
        elif network_state:
            # Try to get resource from network state, normalize by config value
            max_resource = 600.0  # Default matches config.json network.resource_pool
            resource_level = network_state.get('resource_pool', max_resource) / max_resource
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
        
        # === FEATURES 19-24: Extended Integration Features (Neural-ML-Alliance) ===
        
        # 19. Battle history (win ratio, normalized)
        total_battles = self.battle_wins + self.battle_losses
        battle_ratio = self.battle_wins / total_battles if total_battles > 0 else 0.5
        features.append(np.clip(battle_ratio, 0.0, 1.0))
        
        # 20. Alliance reputation (social standing)
        features.append(np.clip(getattr(self, 'alliance_reputation', 0.5), 0.0, 1.0))
        
        # 21. Language fluency (vocabulary richness proxy)
        vocab_size = 0
        if hasattr(self, 'atomic_language') and self.atomic_language:
            vocab_size = len(getattr(self.atomic_language, 'vocabulary', set()))
        elif hasattr(self, 'token_sequence'):
            vocab_size = len(set(self.token_sequence))
        # Normalize language fluency - scale to expected max vocab (65536)
        # Use log scale for better discrimination across large vocab range
        language_fluency = np.clip(np.log1p(vocab_size) / np.log1p(65536), 0.0, 1.0)
        features.append(language_fluency)
        
        # 22. Environmental density (local crowding)
        environmental_density = 0.5  # Default moderate
        if network_state:
            neighbors = network_state.get('neighbors', {}).get(self.species_id, [])
            # More neighbors = higher density, normalize to max 20
            environmental_density = np.clip(len(neighbors) / 20.0, 0.0, 1.0)
        features.append(environmental_density)
        
        # 23. Learning progress (experience accumulation)
        learning_progress = 0.0
        if hasattr(self, 'experience_buffer') and self.experience_buffer:
            # Normalize by buffer capacity
            buffer_len = len(self.experience_buffer)
            buffer_cap = getattr(self.experience_buffer, 'capacity', 1000)
            learning_progress = np.clip(buffer_len / buffer_cap, 0.0, 1.0)
        features.append(learning_progress)
        
        # 24. Health trend (fitness trajectory)
        health_trend = 0.5  # Neutral default
        fitness_history = getattr(self, 'fitness_history', [])
        if len(fitness_history) >= 3:
            # Compare recent fitness to older fitness
            recent_avg = np.mean(fitness_history[-3:])
            older_avg = np.mean(fitness_history[:-3]) if len(fitness_history) > 3 else fitness_history[0]
            # Trend: >0.5 = improving, <0.5 = declining
            if older_avg > 0:
                health_trend = np.clip(0.5 + (recent_avg - older_avg) / older_avg, 0.0, 1.0)
        features.append(health_trend)
        
        # 25. Illumination Level (normalized 0-1)
        # Higher illumination = more processing power/awareness
        illum_map = {'none': 0.0, 'basic': 0.2, 'alliance': 0.4, 'confederation': 0.6, 'empire': 0.8, 'hegemony': 1.0}
        illum_val = illum_map.get(self._illumination_level, 0.0)
        features.append(illum_val)
        
        # === FEATURES 26-27: SELF-PERCEPTION (Magnetism Landscape) ===
        # "Know thyself first, then reach out" - Voyager frame
        # Organisms perceive their own attractor state before network awareness
        
        # 26. Oscillation Entropy (self-awareness of chaos/stability)
        # High entropy = chaotic magnetism changes, organism senses instability
        # Low entropy = stable magnetism trajectory, organism senses order
        oscillation_entropy = 0.0
        if hasattr(self, 'atomic_language') and self.atomic_language:
            try:
                oscillation_entropy = self.atomic_language._calculate_global_entropy()
            except Exception:
                pass
        features.append(np.clip(oscillation_entropy, 0.0, 1.0))
        
        # 27. Coherence Frequency (self-awareness of being trapped)
        # High coherence = oscillating in feedback loop, organism FEELS the trap
        # Low coherence = drifting freely, organism senses freedom
        coherence_frequency = 0.0
        if hasattr(self, 'atomic_language') and self.atomic_language:
            try:
                coherence_frequency = self.atomic_language._calculate_global_coherence()
            except Exception:
                pass
        features.append(np.clip(coherence_frequency, 0.0, 1.0))
        
        # 28. Attractor Proximity (swarm's distance to nearest known stable configuration)
        # High proximity (close to 1.0) = far from known attractors (unexplored territory)
        # Low proximity (close to 0.0) = near known attractor (stable basin)
        # This enables goal-directed collective behavior toward known stability
        attractor_proximity = 0.5  # Default: unknown territory
        if hasattr(self, '_landscape_ref') and self._landscape_ref is not None:
            try:
                attractor_proximity = self._landscape_ref.get_proximity_to_nearest_fixed_point()
            except Exception:
                pass
        features.append(np.clip(attractor_proximity, 0.0, 1.0))
        
        # Ensure we have exactly input_dim features
        input_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 28)
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
            - High trait_divergence ? boost reproduce (increase genetic diversity)
            - Low network_coherence ? boost cooperate (improve connectivity)
            - High quantum_entropy ? boost rest (stabilization)
            - High evolution_pressure ? boost move (seek better environment)
            - High phase_mismatch ? boost rest (synchronization)
        
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
        
        # Rule 1: High trait_divergence ? boost reproduce (action 4)
        # When genetic diversity is causing VP issues, encourage reproduction
        trait_div = vp_components.get('trait_divergence', 0.0)
        if trait_div > high_threshold:
            adjusted[4] += strong_boost  # reproduce
            adjustments_made.append(f"trait_div({trait_div:.2f})?reproduce+{strong_boost}")
        elif trait_div > low_threshold:
            adjusted[4] += base_boost
            adjustments_made.append(f"trait_div({trait_div:.2f})?reproduce+{base_boost}")
        
        # Rule 2: Low network_coherence ? boost cooperate (action 1)
        # When network is fragmented, encourage connection formation
        net_coh = vp_components.get('network_coherence', 0.0)
        if net_coh > high_threshold:  # High VP means LOW coherence
            adjusted[1] += strong_boost  # cooperate
            adjusted[5] -= base_boost   # reduce isolate tendency
            adjustments_made.append(f"net_coh({net_coh:.2f})?cooperate+{strong_boost}")
        elif net_coh > low_threshold:
            adjusted[1] += base_boost
            adjustments_made.append(f"net_coh({net_coh:.2f})?cooperate+{base_boost}")
        
        # Rule 3: High quantum_entropy ? boost rest (action 3)
        # When quantum layer is chaotic, encourage stabilization
        q_entropy = vp_components.get('quantum_entropy', 0.0)
        if q_entropy > high_threshold:
            adjusted[3] += strong_boost  # rest
            adjusted[0] -= base_boost   # reduce move (less chaos)
            adjustments_made.append(f"q_entropy({q_entropy:.2f})?rest+{strong_boost}")
        elif q_entropy > low_threshold:
            adjusted[3] += base_boost
            adjustments_made.append(f"q_entropy({q_entropy:.2f})?rest+{base_boost}")
        
        # Rule 4: High evolution_pressure ? boost move (action 0)
        # When evolution is stressed, encourage exploration for better niches
        evo_pressure = vp_components.get('evolution_pressure', 0.0)
        if evo_pressure > high_threshold:
            adjusted[0] += strong_boost  # move
            adjusted[3] -= base_boost   # reduce rest (be active)
            adjustments_made.append(f"evo_pressure({evo_pressure:.2f})?move+{strong_boost}")
        elif evo_pressure > low_threshold:
            adjusted[0] += base_boost
            adjustments_made.append(f"evo_pressure({evo_pressure:.2f})?move+{base_boost}")
        
        # Rule 5: High phase_mismatch ? boost rest (action 3)
        # When phase sync is off, encourage settling to resync
        phase_mis = vp_components.get('phase_mismatch', 0.0)
        if phase_mis > high_threshold:
            adjusted[3] += strong_boost  # rest
            adjustments_made.append(f"phase_mis({phase_mis:.2f})?rest+{strong_boost}")
        elif phase_mis > low_threshold:
            adjusted[3] += base_boost
            adjustments_made.append(f"phase_mis({phase_mis:.2f})?rest+{base_boost}")
        
        # Ensure no negative probabilities
        adjusted = np.maximum(adjusted, 0.01)
        
        # Renormalize to valid probability distribution
        adjusted = adjusted / adjusted.sum()
        
        return adjusted, adjustments_made
    
    def _generate_decision_reasoning(self, action: int, vp_components: Dict[str, float], 
                                      action_probs: np.ndarray, vp_adjustments: List[str]) -> str:
        """
        Generate natural language reasoning for why this decision was made.
        
        This provides human-readable explanations for the Illumination Engine
        based on the neural network's decision process and VP-aware adjustments.
        
        Args:
            action: The chosen action index
            vp_components: VP component values that influenced decision
            action_probs: The action probability distribution
            vp_adjustments: List of VP adjustments that were applied
            
        Returns:
            Human-readable reasoning string
        """
        action_names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        action_name = action_names[action] if 0 <= action < len(action_names) else 'unknown'
        
        # Build reasoning from VP components
        reasons = []
        primary_driver = None
        
        # Analyze VP components to explain the decision
        trait_div = vp_components.get('trait_divergence', 0.0)
        net_coh = vp_components.get('network_coherence', 0.0)
        q_entropy = vp_components.get('quantum_entropy', 0.0)
        evo_pressure = vp_components.get('evolution_pressure', 0.0)
        phase_mis = vp_components.get('phase_mismatch', 0.0)
        
        # Determine primary driver based on which VP component is highest
        vp_values = {
            'trait_divergence': trait_div,
            'network_coherence': net_coh,
            'quantum_entropy': q_entropy,
            'evolution_pressure': evo_pressure,
            'phase_mismatch': phase_mis
        }
        if vp_values:
            primary_driver = max(vp_values.items(), key=lambda x: x[1])
        
        # Action-specific reasoning
        if action == 0:  # move
            if evo_pressure > 0.3:
                reasons.append(f"evolution pressure is high ({evo_pressure:.2f}), seeking better environment")
            else:
                reasons.append("exploring for resources or better positioning")
                
        elif action == 1:  # cooperate
            if net_coh > 0.3:
                reasons.append(f"network fragmented ({net_coh:.2f}), forming connections to improve coherence")
            else:
                reasons.append("building alliances to share resources and increase fitness")
                
        elif action == 2:  # compete
            if self.fitness < 0.5:
                reasons.append(f"fitness is low ({self.fitness:.2f}), competing for resources")
            else:
                reasons.append("asserting dominance to secure resources")
                
        elif action == 3:  # rest
            if q_entropy > 0.3:
                reasons.append(f"quantum entropy high ({q_entropy:.2f}), stabilizing to reduce chaos")
            elif phase_mis > 0.3:
                reasons.append(f"phase mismatch detected ({phase_mis:.2f}), resting to resynchronize")
            else:
                reasons.append("conserving energy for future actions")
                
        elif action == 4:  # reproduce
            if trait_div > 0.3:
                reasons.append(f"trait divergence high ({trait_div:.2f}), reproducing to increase genetic diversity")
            elif self.fitness > 0.6:
                reasons.append(f"fitness is high ({self.fitness:.2f}), spreading successful genes")
            else:
                reasons.append("attempting to pass on genetic material")
                
        elif action == 5:  # isolate
            if net_coh < 0.2:
                reasons.append("network too dense, isolating to reduce resource competition")
            else:
                reasons.append("protecting resources from competitors")
        
        # Add VP adjustment context if any were made
        if vp_adjustments:
            adjustment_summary = ", ".join([adj.split("?")[0] for adj in vp_adjustments[:2]])
            reasons.append(f"VP factors: {adjustment_summary}")
        
        # Add confidence context
        confidence = float(np.max(action_probs)) if action_probs is not None else 0.5
        if confidence > 0.7:
            confidence_note = "with high confidence"
        elif confidence > 0.4:
            confidence_note = "with moderate confidence"
        else:
            confidence_note = "tentatively (exploring)"
        
        # Build final reasoning
        reason_text = " and ".join(reasons) if reasons else "based on neural network evaluation"
        return f"Chose to {action_name} {confidence_note} because {reason_text}"

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
                # Get the device from the brain's parameters
                device = next(self.brain.parameters()).device
                state_tensor = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
                with torch.no_grad():
                    action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
        else:
            # Exploitation: use neural network with optional VP adjustments
            self.brain.eval()
            with torch.no_grad():
                # Get the device from the brain's parameters
                device = next(self.brain.parameters()).device
                state_tensor = torch.FloatTensor(state).to(device).unsqueeze(0)
                action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
            
            # Apply VP-aware adjustments if enabled
            if vp_planning_enabled and network_state:
                vp_components = network_state.get('vp_components', {})
                if vp_components:
                    action_probs, vp_adjustments = self._apply_vp_aware_adjustments(
                        action_probs, vp_components
                    )
            
            # ═══════════════════════════════════════════════════════════════
            # 🔮 ILLUMINATION ENGINE INTEGRATION
            # Apply causation-aware adjustments if system references available
            # This is where dead code becomes ALIVE!
            # ═══════════════════════════════════════════════════════════════
            illumination_adjustments = []
            if self._alliance_warfare_ref is not None:
                try:
                    # Get illumination insights (was never called before!)
                    illumination = self.get_illumination_insights(
                        alliance_warfare=self._alliance_warfare_ref,
                        causation_explorer=self._causation_explorer_ref
                    )
                    
                    # Enhance decision with illumination (was never called before!)
                    if illumination.get('can_see_self', False):
                        action_probs, illumination_adjustments = self.enhance_decision_with_illumination(
                            action_probs, illumination
                        )
                        vp_adjustments.extend(illumination_adjustments)
                except Exception as e:
                    # Graceful degradation - illumination failure shouldn't crash decisions
                    pass
            
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
            
            # Get VP components for reasoning
            vp_components = network_state.get('vp_components', {}) if network_state else {}
            
            # Generate human-readable reasoning for Illumination Engine
            reasoning = self._generate_decision_reasoning(
                action, vp_components, action_probs, vp_adjustments
            )
            
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
                'vp_adjustments': vp_adjustments if vp_adjustments else None,
                # ?? NEW: Human-readable reasoning for Illumination Engine
                'reasoning': reasoning
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
        self.last_action = action  # Also store as last_action for alliance system

        # DEBUG: Log first decision per organism
        import logging
        _decision_logger = logging.getLogger(__name__)
        if not hasattr(self, '_decisions_made'):
            self._decisions_made = 0
        self._decisions_made += 1
        if self._decisions_made <= 2:
            _decision_logger.warning(f"[DECIDE] {self.species_id}: action={action}, state_shape={state.shape if hasattr(state, 'shape') else 'N/A'}, epsilon={self.epsilon:.3f}")
        
        # Update sequence histories for language model training
        self.action_history.append(action)
        self.state_history.append(state.copy() if isinstance(state, np.ndarray) else state)
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        return action
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🔮 ILLUMINATION ENGINE INTEGRATION
    # Organisms gain causation awareness through civilization
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_illumination_insights(self, 
                                   alliance_warfare=None,
                                   causation_explorer=None) -> Dict[str, Any]:
        """
        Query the Illumination Engine for causation insights.
        
        Organisms CANNOT see causation data alone - they ARE the state.
        But through their alliance's civilization level, they earn access.
        
        This is the organism's window into understanding WHY things happen.
        
        Args:
            alliance_warfare: The AllianceWarfareSystem instance
            causation_explorer: The CausationExplorer instance (optional)
            
        Returns:
            Dict with illumination level and any available insights
        """
        if alliance_warfare is None:
            return {
                'level': 'none',
                'message': 'No alliance system available - organism is isolated',
                'can_see_causation': False
            }
        
        # Get illumination level based on alliance membership
        illumination = alliance_warfare.get_organism_illumination_level(self.species_id)
        
        # Store for decision-making enhancement
        self._illumination_level = illumination['level']
        self._illumination_capabilities = illumination.get('capabilities', set())
        
        # Add organism-specific context
        illumination['organism_id'] = self.species_id
        illumination['fitness'] = self.fitness
        illumination['alliance_reputation'] = self.alliance_reputation
        
        # If we have causation access and an explorer, get relevant events
        if illumination['can_see_self'] and causation_explorer:
            try:
                # Get our own recent causal events
                results = alliance_warfare.query_illumination(
                    self.species_id, 
                    'self',
                    causation_explorer=causation_explorer
                )
                if not results.get('error'):
                    illumination['self_events'] = results.get('events', [])[:10]
                    illumination['total_self_events'] = results.get('total_events', 0)
            except Exception as e:
                illumination['query_error'] = str(e)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🏛️ ALLIANCE WISDOM INTEGRATION  
        # Query collective wisdom if organism is in an alliance (was NEVER called!)
        # ═══════════════════════════════════════════════════════════════════════
        if self.alliance_id and illumination.get('can_see_alliance', False):
            try:
                # Build current situation context for wisdom query
                current_situation = {
                    'organism_id': self.species_id,
                    'fitness': self.fitness,
                    'alliance_reputation': self.alliance_reputation,
                    'at_war': False,  # Could be enhanced with actual war state
                }
                
                # Query alliance wisdom (get_alliance_wisdom was NEVER called!)
                wisdom = alliance_warfare.get_alliance_wisdom(
                    self.alliance_id, 
                    current_situation
                )
                
                if not wisdom.get('error'):
                    illumination['alliance_wisdom'] = wisdom.get('wisdom', [])
                    illumination['relevant_patterns'] = wisdom.get('relevant_patterns', [])
                    illumination['legendary_guidance'] = wisdom.get('legendary_guidance', [])
            except Exception as e:
                illumination['wisdom_query_error'] = str(e)
        
        return illumination
    
    def enhance_decision_with_illumination(self,
                                            action_probs: np.ndarray,
                                            illumination: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """
        Enhance action probabilities using illumination insights.
        
        Higher civilization levels grant more strategic awareness:
        - Basic: See own causal patterns -> avoid repeating failures
        - Alliance: See ally patterns -> coordinate strategies  
        - Confederation: See macro patterns -> long-term planning
        - Empire: See root causes -> address underlying issues
        - Hegemony: See everything -> optimal strategies
        
        Args:
            action_probs: Base action probabilities from neural network
            illumination: Results from get_illumination_insights()
            
        Returns:
            Tuple of (adjusted probabilities, list of adjustments made)
        """
        level = illumination.get('level', 'none')
        adjustments = []
        
        if level == 'none':
            # No illumination - organism acts on instinct alone
            return action_probs, ['No illumination - pure instinct']
        
        adjusted = action_probs.copy()
        
        # BASIC illumination: Learn from own history
        if illumination.get('can_see_self'):
            self_events = illumination.get('self_events', [])
            if self_events:
                # Analyze recent failures and successes
                recent_actions = {}
                for event in self_events[:5]:
                    data = event.get('data', {}) if isinstance(event, dict) else {}
                    action = data.get('action_index')
                    reward = data.get('reward', 0)
                    if action is not None:
                        if action not in recent_actions:
                            recent_actions[action] = []
                        recent_actions[action].append(reward)
                
                # Boost actions that worked, reduce actions that failed
                for action, rewards in recent_actions.items():
                    avg_reward = np.mean(rewards)
                    if avg_reward > 0.5:
                        adjusted[action] *= (1.0 + avg_reward * 0.2)
                        adjustments.append(f"🔮 Boost {action} (self-history success)")
                    elif avg_reward < 0.3:
                        adjusted[action] *= (1.0 - (0.3 - avg_reward) * 0.15)
                        adjustments.append(f"🔮 Reduce {action} (self-history failure)")
        
        # ALLIANCE illumination: Coordinate with allies
        if illumination.get('can_see_alliance'):
            adjustments.append(f"🔮 Alliance awareness active")
            # Use alliance wisdom if available
            # NOTE: alliance_wisdom is a List[str] of wisdom text, not a dict
            wisdom_list = illumination.get('alliance_wisdom', [])
            if wisdom_list and isinstance(wisdom_list, list):
                # Parse wisdom strings for action hints
                # Keywords in wisdom text suggest actions
                wisdom_text = ' '.join(wisdom_list).lower()
                
                # Count action hints in wisdom
                defend_hints = sum(1 for kw in ['defend', 'protect', 'retreat', 'caution', 'danger'] 
                                   if kw in wisdom_text)
                attack_hints = sum(1 for kw in ['attack', 'strike', 'aggressive', 'war', 'fight'] 
                                   if kw in wisdom_text)
                expand_hints = sum(1 for kw in ['expand', 'grow', 'explore', 'spread', 'territory'] 
                                   if kw in wisdom_text)
                
                # Confidence based on number of matching hints
                total_hints = defend_hints + attack_hints + expand_hints
                if total_hints > 0:
                    if defend_hints > attack_hints and defend_hints > expand_hints:
                        confidence = min(0.9, 0.5 + defend_hints * 0.1)
                        if len(adjusted) > 0:
                            adjusted[0] *= (1.0 + confidence * 0.3)
                            adjustments.append(f"🔮 Wisdom: DEFEND (hints={defend_hints})")
                    elif attack_hints > defend_hints and attack_hints > expand_hints:
                        confidence = min(0.9, 0.5 + attack_hints * 0.1)
                        if len(adjusted) > 1:
                            adjusted[1] *= (1.0 + confidence * 0.25)
                            adjustments.append(f"🔮 Wisdom: ATTACK (hints={attack_hints})")
                    elif expand_hints > 0:
                        confidence = min(0.9, 0.5 + expand_hints * 0.1)
                        if len(adjusted) > 2:
                            adjusted[2] *= (1.0 + confidence * 0.2)
                            adjustments.append(f"🔮 Wisdom: EXPAND (hints={expand_hints})")
        
        # CONFEDERATION illumination: Macro-level strategy
        if illumination.get('can_see_confederation'):
            adjustments.append(f"🔮 Confederation vision active")
            # In future: adjust based on confederation-wide patterns
        
        # EMPIRE illumination: Root cause awareness
        if illumination.get('can_see_root_causes'):
            adjustments.append(f"🔮 Root cause analysis available")
            # In future: use deep causal insights
        
        # HEGEMONY illumination: Complete awareness
        if illumination.get('can_see_all'):
            adjustments.append(f"🔮 HEGEMONIC OMNISCIENCE - Full causation access")
            # Future: optimal strategy calculation
        
        # Normalize
        adjusted = np.maximum(adjusted, 0.01)
        adjusted = adjusted / adjusted.sum()
        
        return adjusted, adjustments

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
    
    def _seed_token_sequence_from_phenotype(self, max_seq_len: int = 128) -> None:
        """
        🎰 TOKEN TUMBLER: Seed organism with full token sequence from phenotype.
        
        This gives every organism initial "self-talk" tokens derived from their
        phenotype traits, ensuring language loss can train from birth.
        
        The tokens encode:
        - Trait values (speed, size, efficiency, social, aggression)
        - Special markers for high/low trait values
        - Repetition creates learnable patterns
        
        Args:
            max_seq_len: Maximum sequence length to fill
        """
        import random
        
        if not hasattr(self, 'token_sequence'):
            return
            
        # Base vocabulary mapping for phenotype traits
        # Using token IDs 10-99 for traits (avoiding special tokens 0-9)
        TRAIT_BASE = 10
        TRAIT_TOKENS = {
            'speed': TRAIT_BASE,           # 10-19: speed tokens
            'size': TRAIT_BASE + 10,       # 20-29: size tokens  
            'efficiency': TRAIT_BASE + 20, # 30-39: efficiency tokens
            'social': TRAIT_BASE + 30,     # 40-49: social tokens
            'aggression': TRAIT_BASE + 40, # 50-59: aggression tokens
        }
        
        # Special marker tokens
        HIGH_MARKER = 60   # Precedes high trait values (>0.7)
        LOW_MARKER = 61    # Precedes low trait values (<0.3)
        IDENTITY_MARKER = 62  # Organism identity token
        TRAIT_END = 63     # End of trait block
        ACTION_POTENTIAL = 64  # "Ready to act" marker
        
        # Get phenotype traits
        traits = {
            'speed': getattr(self.phenotype, 'speed', 0.5),
            'size': getattr(self.phenotype, 'size', 0.5),
            'efficiency': getattr(self.phenotype, 'efficiency', 0.5),
            'social': getattr(self.phenotype, 'social_affinity', 0.5),
            'aggression': getattr(self.phenotype, 'aggression', 0.5),
        }
        
        # Generate seed from species_id for reproducible but unique sequences
        seed = hash(self.species_id) % (2**32)
        rng = random.Random(seed)
        
        tokens = []
        
        # Start with identity marker
        tokens.append(IDENTITY_MARKER)
        
        # Add organism's "genetic signature" - hash of species_id to tokens
        species_hash = abs(hash(self.species_id))
        for i in range(4):
            tokens.append(70 + (species_hash >> (i * 8)) % 30)  # 70-99: signature tokens
        
        # Encode each trait with variation
        for trait_name, trait_value in traits.items():
            base_token = TRAIT_TOKENS[trait_name]
            
            # Add high/low marker if extreme
            if trait_value > 0.7:
                tokens.append(HIGH_MARKER)
            elif trait_value < 0.3:
                tokens.append(LOW_MARKER)
            
            # Convert trait to token offset (0-9 based on value)
            token_offset = int(trait_value * 9.99)  # 0-9
            tokens.append(base_token + token_offset)
            
            # Add some variance tokens for learning (repeating traits with noise)
            for _ in range(rng.randint(1, 3)):
                noisy_offset = max(0, min(9, token_offset + rng.randint(-1, 1)))
                tokens.append(base_token + noisy_offset)
        
        tokens.append(TRAIT_END)
        
        # Fill remaining space with action potential patterns
        # This creates learnable sequences the organism can build upon
        while len(tokens) < max_seq_len:
            # Repeat trait patterns with mutation (creates learnable structure)
            if rng.random() < 0.6:
                # Pick a trait and emit tokens based on it
                trait_name = rng.choice(list(traits.keys()))
                trait_value = traits[trait_name]
                base_token = TRAIT_TOKENS[trait_name]
                offset = int(trait_value * 9.99)
                tokens.append(base_token + max(0, min(9, offset + rng.randint(-2, 2))))
            else:
                # Action potential / ready state
                tokens.append(ACTION_POTENTIAL + rng.randint(0, 5))
        
        # Truncate to max length and add to sequence
        tokens = tokens[:max_seq_len]
        for token in tokens:
            self.token_sequence.append(token)
    
    def tumble_action_tokens(self, action: int, reward: float, context: str = 'step') -> None:
        """
        🎰 TOKEN TUMBLER: Generate tokens from an action/reward pair.
        
        Call this when organism takes an action to grow its token sequence
        with meaningful patterns that correlate with behavior.
        
        Args:
            action: Action taken (0-5 typically)
            reward: Reward received
            context: Context string ('step', 'catch', 'miss', 'move', etc.)
        """
        if not hasattr(self, 'token_sequence'):
            return
        
        # Action tokens: 100-109
        ACTION_BASE = 100
        # Reward tokens: 110-119 (binned)
        REWARD_BASE = 110
        # Context tokens: 120-129
        CONTEXT_TOKENS = {
            'step': 120,
            'catch': 121,
            'miss': 122,
            'move': 123,
            'idle': 124,
            'success': 125,
            'failure': 126,
            'explore': 127,
            'exploit': 128,
            'social': 129,
        }
        
        # Emit context token
        ctx_token = CONTEXT_TOKENS.get(context, 120)
        self.token_sequence.append(ctx_token)
        
        # Emit action token
        self.token_sequence.append(ACTION_BASE + min(9, action))
        
        # Emit reward token (binned to 0-9)
        reward_bin = int(max(0, min(0.99, (reward + 1) / 2)) * 9.99)  # Normalize -1..1 to 0..9
        self.token_sequence.append(REWARD_BASE + reward_bin)

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
        # DEBUG: Log why experiences might not be recorded
        import logging
        _logger = logging.getLogger(__name__)
        
        if self.brain is None:
            _logger.debug(f"[EXP] {self.species_id}: Skipped - no brain")
            return  # No brain, no experience recording
        if self.experience_buffer is None:
            _logger.debug(f"[EXP] {self.species_id}: Skipped - no buffer")
            return  # No buffer, no recording
        if self.prev_state is None or self.prev_action is None:
            # This is the most common issue - organism hasn't made a decision yet
            # This is expected on first frame, but should resolve after first decide_action()
            _logger.debug(f"[EXP] {self.species_id}: Skipped - no prev_state/action")
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
        
        # Track buffer size (no logging - was filling disk on large populations)
        buffer_len = len(self.experience_buffer)
        
        # ✨ Update atomic language system with experience
        if self.atomic_language is not None:
            # Get VP state from current state if available
            vp_state = (0.5, 0.5)  # Default
            if len(self.prev_state) >= 12:
                # VP components are typically in state features 10-11
                vp_state = (float(self.prev_state[10]), float(self.prev_state[11]))
            
            context = {
                'vp_state': vp_state,
                'fitness': self.fitness,
                'reward': reward
            }
            self.atomic_language.apply_experience(
                action=self.prev_action,
                outcome=reward,
                context=context
            )
        
        # Update previous fitness and track fitness history (for health_trend feature)
        self.prev_fitness = self.fitness
        if hasattr(self, 'fitness_history'):
            self.fitness_history.append(self.fitness)
            # Keep only last 20 fitness values for trend analysis
            if len(self.fitness_history) > 20:
                self.fitness_history = self.fitness_history[-20:]

    def record_gym_experience(self,
                              state: np.ndarray,
                              action: int,
                              reward: float,
                              next_state: np.ndarray,
                              done: bool = False):
        """
        Record experience from REAL GYM gameplay for training.
        
        This is different from record_experience() which uses internal
        prev_state/prev_action. This method accepts all components directly
        for external gym environment integration.
        
        Args:
            state: Observation from gym environment (will be padded/truncated to 28)
            action: Action taken (MUST be 0-5 for our 6-action brain)
            reward: Reward received
            next_state: Next observation
            done: Whether episode ended
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        if self.brain is None:
            return
        if self.experience_buffer is None:
            return
        
        # CRITICAL: Validate action is within our brain's action space (0-5)
        # Gym environments may have different action counts, but our brain
        # only supports 6 actions. Skip experiences with invalid actions.
        # For continuous actions (numpy arrays), convert to discrete action index
        if isinstance(action, np.ndarray):
            # Continuous action - convert to discrete by taking argmax of first 6 dims
            # or hashing the action vector to a consistent action index
            if len(action) > 0:
                action = int(np.abs(action).sum() * 1000) % 6  # Hash to 0-5
            else:
                action = 0
        elif not (0 <= action <= 5):
            _logger.debug(f"[GYM-EXP] Skipping experience with invalid action {action} (must be 0-5)")
            return
        
        # Normalize state to 28-dim (our standard input dimension)
        def normalize_state(obs):
            state_28 = np.zeros(28, dtype=np.float32)
            if isinstance(obs, (int, np.integer)):
                state_28[0] = float(obs) / 100.0
            elif isinstance(obs, tuple):
                for i, val in enumerate(obs[:28]):
                    if isinstance(val, (int, float, bool)):
                        state_28[i] = float(val)
            else:
                obs_flat = np.array(obs).flatten()
                state_28[:min(len(obs_flat), 28)] = obs_flat[:28]
            return state_28
        
        state_norm = normalize_state(state)
        next_state_norm = normalize_state(next_state)
        
        # ═══════════════════════════════════════════════════════════════════
        # REWARD NORMALIZATION for Gym environments
        # Different envs have wildly different reward scales:
        #   - CartPole: 0-500 per episode
        #   - MuJoCo Humanoid: -∞ to ~6000
        #   - LunarLander: -∞ to ~300
        #   - Blackjack: -1 to 1
        # 
        # We normalize to [-1, 1] range for stable DQN training.
        # ═══════════════════════════════════════════════════════════════════
        reward_normalized = reward
        if abs(reward) > 1.0:
            # Soft clip with tanh for large rewards
            # Maps (-∞, ∞) → (-1, 1) smoothly
            reward_normalized = np.tanh(reward / 10.0)  # /10 spreads out common range
        
        # Add to experience buffer
        self.experience_buffer.add(
            state=state_norm,
            action=action,
            reward=reward_normalized,
            next_state=next_state_norm,
            done=done
        )
        
        # Increment gym_experiences count
        self.gym_experiences = getattr(self, 'gym_experiences', 0) + 1
        
        # Log first few experiences
        buffer_len = len(self.experience_buffer)
        if buffer_len <= 3:
            _logger.info(f"[GYM-EXP] {self.species_id}: Gym experience recorded! "
                        f"buffer_size={buffer_len}, reward={reward:.3f}")
        
        # Update prev_state/action for consistency
        self.prev_state = state_norm
        self.prev_action = action

    def record_battle_outcome(self, won: bool, margin: float):
        """
        Record battle outcome as training reward.

        Args:
            won: True if organism won the battle
            margin: Victory margin (0.0-1.0, higher = more decisive)
        """
        # Base reward
        reward = 1.0 if won else -0.5

        # Scale by victory margin
        reward *= (1.0 + margin)

        # Track battle statistics
        if won:
            self.battle_wins += 1
        else:
            self.battle_losses += 1

        # Record experience
        self.record_experience(reward=reward)
        
        # 🎰 TOKEN TUMBLER: Generate battle outcome tokens
        context = 'success' if won else 'failure'
        self.tumble_action_tokens(action=0, reward=reward, context=context)

        # Emit event for Butterfly Engine tracking
        if self.event_emitter:
            event_data = {
                "event_type": "battle_outcome_recorded",
                "won": won,
                "margin": margin,
                "reward": reward,
                "battle_wins": self.battle_wins,
                "battle_losses": self.battle_losses,
                "fitness": self.fitness
            }
            self.event_emitter(event_data)

    def record_alliance_event(self, event_type: str, success: bool):
        """
        Record alliance-related events as training rewards.

        Args:
            event_type: Type of alliance event ("joined", "betrayed", "war_won", "war_lost", "battle_won", "battle_lost")
            success: True if the event was successful for this organism
        """
        # Reward mapping for different alliance events
        rewards = {
            "joined": 0.3,      # Positive for forming alliances
            "betrayed": -0.8,   # Negative for betrayal
            "war_won": 0.5,     # Positive for winning wars
            "war_lost": -0.3,   # Negative for losing wars
            "battle_won": 0.2,  # Positive for individual battle wins
            "battle_lost": -0.1 # Slight negative for individual losses
        }
        
        # Reputation adjustments for alliance events (Integration: Feature 20)
        reputation_deltas = {
            "joined": 0.05,     # Joining alliance builds reputation
            "betrayed": -0.2,   # Betrayal damages reputation significantly
            "war_won": 0.1,     # Victory improves standing
            "war_lost": -0.05,  # Loss slightly reduces reputation
            "battle_won": 0.02, # Individual wins build reputation
            "battle_lost": -0.01 # Individual losses minor impact
        }

        # Get base reward
        base_reward = rewards.get(event_type, 0.0)
        
        # Update alliance reputation
        rep_delta = reputation_deltas.get(event_type, 0.0)
        if not success:
            rep_delta *= -1  # Invert for unsuccessful events
        if hasattr(self, 'alliance_reputation'):
            self.alliance_reputation = max(0.0, min(1.0, self.alliance_reputation + rep_delta))

        # Invert if event was unsuccessful for this organism
        if not success:
            base_reward *= -1

        # Record experience
        self.record_experience(reward=base_reward)

        # Emit event for Butterfly Engine tracking
        if self.event_emitter:
            event_data = {
                "event_type": "alliance_event_recorded",
                "alliance_event_type": event_type,
                "success": success,
                "reward": base_reward,
                "fitness": self.fitness
            }
            self.event_emitter(event_data)

    def record_language_outcome(self, quality_score: float):
        """
        Record language generation quality as training reward.

        Args:
            quality_score: Quality score from _evaluate_generation_quality() (0.0-1.0)
        """
        # Center reward around 0, scale to reasonable range
        reward = (quality_score - 0.5) * 0.5

        # Record experience
        self.record_experience(reward=reward)

        # Emit event for Butterfly Engine tracking
        if self.event_emitter:
            event_data = {
                "event_type": "language_outcome_recorded",
                "quality_score": quality_score,
                "reward": reward,
                "fitness": self.fitness
            }
            self.event_emitter(event_data)

    def record_vp_contribution(self, vp_delta: float):
        """
        Record violation pressure change as training reward.

        Args:
            vp_delta: Change in VP (negative = improvement/stabilization)
        """
        # Negative VP change = stabilization = good
        # Scale reward appropriately
        reward = -vp_delta * 0.3

        # Record experience
        self.record_experience(reward=reward)

        # Emit event for Butterfly Engine tracking
        if self.event_emitter:
            event_data = {
                "event_type": "vp_contribution_recorded",
                "vp_delta": vp_delta,
                "reward": reward,
                "fitness": self.fitness
            }
            self.event_emitter(event_data)


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
                         max_length: int = 128,
                         vp_value: Optional[float] = None,
                         temperature: float = 1.0,
                         input_tokens: Optional[List[int]] = None) -> List[int]:
        """
        Generate token sequence using the language head (autoregressive).

        NEURAL SYNAPSE MODE: Longer responses create richer causation chains!
        Each token generates semantic edges in the knowledge web.

        Args:
            context_memory: ContextMemory instance with vocabulary and word embeddings
            max_length: Maximum tokens to generate
            vp_value: Current VP value (if None, generates freely)
            temperature: Sampling temperature (higher = more random)
            input_tokens: Optional list of input token IDs to condition generation on

        Returns:
            List of generated token IDs
        """
        if self.brain is None:
            return []
        
        # ---------------------------------------------------------------------------
        # VP-AWARE SCALING: Adaptive generation length based on VP (replaces binary gate)
        # Instead of blocking generation entirely at VP > 0.5, we scale response length
        # This allows learning during unstable phases while maintaining caution
        # ---------------------------------------------------------------------------
        vp_length_multiplier = 1.0
        if vp_value is not None:
            if vp_value > 0.85:
                # VP4/Critical: Very short, cautious responses (but still generate!)
                vp_length_multiplier = 0.2
            elif vp_value > 0.7:
                # VP3/High: Short responses
                vp_length_multiplier = 0.4
            elif vp_value > 0.5:
                # VP2/Moderate: Reduced length
                vp_length_multiplier = 0.6
            elif vp_value > 0.3:
                # VP1/Low: Slightly reduced
                vp_length_multiplier = 0.8
            # VP0/Stable: Full length (multiplier = 1.0)
        
        import torch
        
        # ---------------------------------------------------------------------------
        # BUILD ORGANISM-SPECIFIC VOCABULARY from atomic_language (NOT shared context_memory!)
        # Each organism has its OWN learned words - this is the whole point of evolution
        # ---------------------------------------------------------------------------
        from ..language_system import LanguageVocabulary, SPECIAL_TOKENS
        
        # Create this organism's personal vocabulary from their atomic_language
        vocab = LanguageVocabulary(max_vocab_size=20000)  # Fresh vocab for THIS organism
        
        if self.atomic_language is not None and hasattr(self.atomic_language, 'atoms'):
            # FIX: Sort words by atom STRENGTH (descending) so most relevant words get lowest IDs
            # Neural network tends to sample low token IDs, so this ensures important words appear
            # instead of alphabetically-first words like "aardvark", "aalii", etc.
            atoms = self.atomic_language.atoms
            organism_words = sorted(
                atoms.keys(),
                key=lambda w: (
                    -atoms[w].strength,           # Primary: highest strength first
                    -atoms[w].usage_count,        # Secondary: most used first  
                    -atoms[w].last_used_time      # Tertiary: most recently used first
                )
            )
            for word in organism_words:
                vocab.add_word(word)
            logger.info(f"[generate_tokens] {self.species_id}: Built personal vocab from {len(organism_words)} atomic_language atoms (sorted by strength)")
        else:
            logger.warning(f"[generate_tokens] {self.species_id}: No atomic_language - cannot build personal vocab")
            return []
        
        # Check vocab has actual words beyond special tokens
        word_count = len(vocab.word_to_id)
        if word_count <= 5:
            logger.warning(f"[generate_tokens] {self.species_id}: vocab has only {word_count} words (need >5)")
            return []
        
        # Log THIS organism's unique vocabulary (not the shared one!)
        sample_words = list(vocab.word_to_id.keys())[:15]
        logger.info(f"[generate_tokens] {self.species_id}: personal vocab OK with {word_count} words, sample={sample_words}")
        
        # ---------------------------------------------------------------------------
        # ADAPTIVE MAX_LENGTH: Scale response length based on experience
        # ---------------------------------------------------------------------------
        experience_count = len(self.experience_buffer) if hasattr(self, 'experience_buffer') and self.experience_buffer else 0
        vocab_size = vocab.vocab_size
        
        # Longer responses as organism gains experience
        if experience_count < 10:
            adaptive_max_length = min(8, max(5, vocab_size // 6))
        elif experience_count < 50:
            adaptive_max_length = min(24, max(12, vocab_size // 4))
        elif experience_count < 100:
            adaptive_max_length = min(64, max(32, vocab_size // 2))
        else:
            adaptive_max_length = max_length  # Full length when experienced (default 128)
        
        # Don't exceed provided max_length
        effective_max_length = min(adaptive_max_length, max_length)
        
        generated = [vocab.get_id('<START>')]
        # Get device from brain model (CPU or CUDA)
        device = next(self.brain.parameters()).device
        # Get correct input dimension from config
        input_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 27)
        self.brain.eval()
        
        # Early stopping for UNK sequences
        unk_count = 0
        max_unk_before_stop = 3
        
        with torch.no_grad():
            # Start with current state as context
            if len(self.state_history) > 0:
                state = self.state_history[-1]
                if isinstance(state, np.ndarray):
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                else:
                    state_tensor = torch.zeros(1, input_dim, device=device)  # Default input dim
            else:
                state_tensor = torch.zeros(1, input_dim, device=device)

            # ---------------------------------------------------------------------------
            # INPUT CONDITIONING: Encode user input tokens to condition generation
            # ---------------------------------------------------------------------------
            input_context_vector = None
            # DEBUG: Log what we received
            logger.info(f"[generate_tokens] {self.species_id}: input_tokens={len(input_tokens) if input_tokens else 0}, context_memory={context_memory is not None}, has_word_embedding={hasattr(context_memory, 'word_embedding') if context_memory else False}")
            if input_tokens and len(input_tokens) > 0 and context_memory is not None:
                # Use context_memory.word_embedding to encode input tokens
                if hasattr(context_memory, 'word_embedding') and context_memory.word_embedding is not None:
                    try:
                        # Convert to tensor and clamp to valid range
                        input_token_tensor = torch.LongTensor(input_tokens).to(device)
                        # Clamp to prevent out-of-range errors
                        max_vocab = context_memory.word_embedding.num_embeddings
                        input_token_tensor = torch.clamp(input_token_tensor, 0, max_vocab - 1)

                        # Encode: (seq_len,) -> (seq_len, 64)
                        input_embeddings = context_memory.word_embedding(input_token_tensor)

                        # Pool to single context vector: (seq_len, 64) -> (1, 64)
                        input_context_vector = input_embeddings.mean(dim=0, keepdim=True)

                        logger.info(f"[generate_tokens] {self.species_id}: Encoded {len(input_tokens)} input tokens -> context vector {input_context_vector.shape}")
                    except Exception as e:
                        logger.warning(f"[generate_tokens] {self.species_id}: Failed to encode input tokens: {e}")
                        input_context_vector = None

            for _ in range(effective_max_length - 1):
                # If brain has language head, use proper forward path with attention
                if hasattr(self.brain, 'fc_language') and self.brain.use_language_head:
                    # CONDITIONED FORWARD PASS: Inject input context into hidden state
                    if input_context_vector is not None:
                        # Manual forward to inject context at hidden layer
                        # fc1: (1, 25) -> (1, 64)
                        h1 = self.brain._get_activation(self.brain.fc1(state_tensor))
                        h1 = self.brain.dropout(h1)

                        # Inject input context: (1, 64) + (1, 64) -> (1, 64)
                        h1_conditioned = h1 + input_context_vector

                        # fc2: (1, 64) -> (1, 64)
                        h2 = self.brain._get_activation(self.brain.fc2(h1_conditioned))
                        h2 = self.brain.dropout(h2)

                        # Action head (not used in generation, but for completeness)
                        output = self.brain.fc3(h2).softmax(dim=-1)

                        # Language head: (1, 64) -> (1, 20000)
                        language_logits = self.brain.fc_language(h2)
                    else:
                        # Standard forward without conditioning
                        output, language_logits = self.brain.forward(
                            state_tensor,
                            vp_value=vp_value,
                            return_language_logits=True
                        )
                    
                    # Clamp logits to vocabulary size to avoid out-of-range tokens
                    vocab_size = vocab.vocab_size
                    if language_logits.shape[-1] > vocab_size:
                        language_logits = language_logits[..., :vocab_size]
                    
                    # Handle both 2D (batch, vocab) and 3D (batch, seq, vocab) outputs
                    if len(language_logits.shape) == 3:
                        # Use last sequence position for generation
                        logits = language_logits[0, -1, :] / temperature
                    else:
                        # Standard 2D: (batch, vocab)
                        logits = language_logits[0] / temperature

                    # ═══════════════════════════════════════════════════════════════
                    # GROUNDED MODE: Vocabulary Masking by Mastery Level
                    # ═══════════════════════════════════════════════════════════════
                    # Enforce that organisms can only generate tokens from their
                    # available vocabulary based on current mastery level.
                    # This prevents generating words they haven't "earned" yet.
                    if hasattr(self, 'atomic_language') and self.atomic_language is not None:
                        # Get available vocabulary for current mastery level
                        available_words = self.atomic_language.get_available_vocabulary()

                        # Get masking mode from config
                        lang_config = self.config.get('language', {})
                        grounded_config = lang_config.get('grounded', {})
                        masking_mode = grounded_config.get('vocabulary_masking', 'soft')
                        always_allow = grounded_config.get('always_allow_tokens', [])

                        if masking_mode != 'none' and available_words:
                            # Build set of available token IDs
                            available_token_ids = set()

                            # Add words from mastery-gated vocabulary
                            for word in available_words:
                                token_id = vocab.get_id(word)
                                if token_id is not None and token_id < logits.shape[-1]:
                                    available_token_ids.add(token_id)

                            # Always allow special tokens
                            for special in ['<START>', '<END>', '<PAD>', '<UNK>']:
                                tid = vocab.get_id(special)
                                if tid is not None and tid < logits.shape[-1]:
                                    available_token_ids.add(tid)

                            # Always allow connectors and punctuation
                            for always in always_allow:
                                tid = vocab.get_id(always)
                                if tid is not None and tid < logits.shape[-1]:
                                    available_token_ids.add(tid)

                            # Apply masking
                            if masking_mode == 'soft':
                                # Soft mask: Strong penalty but not impossible
                                penalty = torch.zeros_like(logits)
                                for idx in range(logits.shape[-1]):
                                    if idx not in available_token_ids:
                                        penalty[idx] = -10.0  # Strong penalty
                                logits = logits + penalty
                            elif masking_mode == 'hard':
                                # Hard mask: Impossible to generate unavailable tokens
                                mask = torch.full_like(logits, float('-inf'))
                                for tid in available_token_ids:
                                    mask[tid] = 0.0
                                logits = logits + mask

                            logger.debug(f"[generate_tokens] {self.species_id}: Vocabulary masked (mode={masking_mode}, level={self.atomic_language.mastery_level}, available={len(available_token_ids)})")
                else:
                    # Fallback: No language head, just get output
                    output = self.brain.forward(state_tensor, vp_value=vp_value)
                    language_logits = None

                # If brain has language head, process logits
                if language_logits is not None:
                    
                    # ?? SEMANTIC REASONING: Quality-controlled semantic guidance
                    # Only strengthens coherent formations, prevents garbled chains
                    if context_memory and hasattr(context_memory, 'vocabulary'):
                        # Get Linguistic Knowledge Web if available
                        knowledge_web = None
                        if hasattr(context_memory, 'knowledge_web'):
                            knowledge_web = context_memory.knowledge_web
                        elif hasattr(context_memory, 'language_teacher') and hasattr(context_memory.language_teacher, 'knowledge_web'):
                            knowledge_web = context_memory.language_teacher.knowledge_web
                        
                        if knowledge_web and len(generated) > 1:
                            # Get last generated word for semantic reasoning
                            last_token = generated[-1]
                            last_word = vocab.get_word(last_token)
                            
                            if last_word and last_word not in ['<START>', '<END>', '<PAD>', '<UNK>', '<VP_GATE>']:
                                # Get semantic guidance config
                                semantic_config = self.config.get('neural', {}).get('language_model', {}).get('relationship_learning', {}).get('semantic_guidance', {})
                                semantic_enabled = semantic_config.get('enabled', True)
                                # GROK-4 FIX: Lower threshold from 0.7 to 0.3 so semantic guidance actually activates
                                min_strength = semantic_config.get('min_strength_threshold', 0.3)
                                semantic_boost = semantic_config.get('semantic_boost', 0.2)
                                high_strength_boost = semantic_config.get('high_strength_boost', 0.1)
                                max_similar_words = semantic_config.get('max_similar_words', 5)
                                
                                if semantic_enabled:
                                    # QUALITY-CONTROLLED CASCADING: Only use high-confidence semantic relationships
                                    # Use higher strength threshold to prevent garbled chains
                                    similar_words = knowledge_web.get_similar_words(last_word, min_strength=min_strength)
                                    
                                    # PRIMARY: ATOMIC VOCABULARY VECTOR RETRIEVAL
                                    # Use organism's OWN atomic_language for semantic search (the root source)
                                    if self.atomic_language is not None and hasattr(self.atomic_language, 'find_similar_words'):
                                        atomic_similar = self.atomic_language.find_similar_words(
                                            last_word, 
                                            top_k=max_similar_words * 2,
                                            min_similarity=0.1
                                        )
                                        atomic_word_set = {w for w, _ in atomic_similar}
                                        similar_words = list(set(similar_words) | atomic_word_set)
                                        
                                        # Also get words matching current state
                                        if len(self.state_history) > 0:
                                            current_state = self.state_history[-1] if isinstance(self.state_history[-1], np.ndarray) else None
                                            if current_state is not None:
                                                state_words = self.atomic_language.find_words_for_state(
                                                    current_state, 
                                                    top_k=max_similar_words
                                                )
                                                state_word_set = {w for w, _ in state_words}
                                                similar_words = list(set(similar_words) | state_word_set)
                                        
                                        # TRAIT-DRIVEN QUERY: Use organism's reasoning traits
                                        if hasattr(self.atomic_language, 'query_vocabulary'):
                                            # Get organism traits for query mechanics
                                            curiosity = getattr(self.phenotype, 'curiosity', 0.5) if hasattr(self, 'phenotype') else 0.5
                                            aggression = getattr(self.phenotype, 'aggression', 0.5) if hasattr(self, 'phenotype') else 0.5
                                            social_affinity = getattr(self.phenotype, 'social_affinity', 0.5) if hasattr(self, 'phenotype') else 0.5
                                            # Exploration rate from config or default
                                            exploration_rate = semantic_config.get('exploration_rate', 0.1)
                                            
                                            trait_words = self.atomic_language.query_vocabulary(
                                                query_word=last_word,
                                                organism_state=current_state,
                                                curiosity=curiosity,
                                                aggression=aggression,
                                                social_affinity=social_affinity,
                                                exploration_rate=exploration_rate,
                                                top_k=max_similar_words * 2
                                            )
                                            trait_word_set = {w for w, _ in trait_words}
                                            similar_words = list(set(similar_words) | trait_word_set)
                                    
                                    # SECONDARY: Knowledge web expansion (if available)
                                    elif hasattr(knowledge_web, 'vector_query') and len(self.state_history) > 0:
                                        current_state = self.state_history[-1] if isinstance(self.state_history[-1], np.ndarray) else None
                                        if current_state is not None:
                                            vector_words = knowledge_web.vector_query(
                                                context_memory=context_memory,
                                                query_word=last_word,
                                                organism_state=current_state,
                                                top_k=max_similar_words * 2,
                                                expand_associations=True,
                                                expansion_depth=1,
                                                min_relation_strength=min_strength
                                            )
                                            vector_word_set = {w for w, _ in vector_words}
                                            similar_words = list(set(similar_words) | vector_word_set)
                                    
                                    # Limit total similar words
                                    similar_words = similar_words[:max_similar_words * 2]
                                    
                                    # Track which relationships we're using for success/failure recording
                                    used_relationships = []
                                    
                                    # Only boost if neural network already has some confidence (coherent reasoning)
                                    # Get current top predictions
                                    current_probs = torch.softmax(logits, dim=-1)
                                    # Safe topk: don't request more than available
                                    safe_k = min(10, len(current_probs))
                                    if safe_k > 0:
                                        top_probs, top_indices = torch.topk(current_probs, safe_k)
                                    else:
                                        top_indices = torch.tensor([], dtype=torch.long)
                                    
                                    # Boost logits for semantically related words that are ALREADY in top predictions
                                    # This ensures coherence - we strengthen existing good predictions, not random words
                                    for similar_word in similar_words[:max_similar_words]:
                                        try:
                                            similar_token = vocab.get_id(similar_word)
                                            if similar_token < vocab_size and similar_token >= 0:
                                                # Find the relationship we're using
                                                relations = knowledge_web.get_relations(last_word)
                                                for r in relations:
                                                    if (r.target == similar_word or r.source == similar_word) and r not in used_relationships:
                                                        used_relationships.append(r)
                                                        break
                                                
                                                # Only boost if word is already in top predictions (coherent)
                                                if similar_token in top_indices:
                                                    logits[similar_token] += semantic_boost
                                                # Or if it has very high semantic strength (strong formation)
                                                elif any(r.strength >= 0.8 and (r.target == similar_word or r.source == similar_word) 
                                                        for r in knowledge_web.get_relations(last_word)):
                                                    logits[similar_token] += high_strength_boost  # Smaller boost for high-strength
                                        except (KeyError, AttributeError, TypeError) as e:
                                            logger.debug(f"Semantic guidance lookup failed: {e}")
                                    
                                    # NEW: TF-IDF Importance Bias (if ML analysis available)
                                    # Boost words that are important across the population
                                    if hasattr(context_memory, '_ml_analysis_cache'):
                                        ml_analysis = context_memory._ml_analysis_cache
                                        if ml_analysis:
                                            semantic_analysis = ml_analysis.get('semantic_analysis', {})
                                            tfidf_results = semantic_analysis.get('tfidf_analysis', {})
                                            if tfidf_results:
                                                important_words = tfidf_results.get('top_important_words', [])
                                                # Create word -> TF-IDF score mapping
                                                tfidf_scores = {item['word']: item['tfidf_score'] for item in important_words}
                                                
                                                # Boost important words in logits
                                                for word, score in tfidf_scores.items():
                                                    try:
                                                        word_token = vocab.get_id(word)
                                                        if word_token < vocab_size and word_token >= 0:
                                                            # Boost by TF-IDF score (scaled)
                                                            logits[word_token] += score * 0.1  # Small boost for important words
                                                    except (KeyError, AttributeError, TypeError) as e:
                                                        logger.debug(f"TF-IDF boost failed for word: {e}")
                                    
                                    # Store used relationships for later success/failure recording
                                    if not hasattr(self, '_generation_relationships'):
                                        self._generation_relationships = []
                                    self._generation_relationships.extend(used_relationships)
                    
                    # CRITICAL FIX: Mask logits to only sample from ACTUAL vocabulary words
                    # Brain outputs 1000 logits but vocabulary may only have 5-50 actual words
                    # Without masking, most samples hit non-existent tokens → <UNK> → empty output
                    actual_vocab_size = len(vocab.word_to_id)  # Real vocab size including only actual words
                    
                    # SAFETY: Clamp actual_vocab_size to not exceed logits tensor size
                    # Vocabulary can grow beyond network capacity - use min to prevent IndexError
                    effective_vocab_size = min(actual_vocab_size, len(logits))
                    
                    # CRITICAL FIX: If vocab has no real words (only special tokens), can't generate
                    # Without this check, probs become all-zeros → multinomial throws AssertionError
                    # Special tokens are: <PAD>=0, <UNK>=1, <START>=2, <END>=3, <VP_GATE>=4
                    non_special_count = effective_vocab_size - len(SPECIAL_TOKENS)
                    if non_special_count <= 0:
                        logger.info(f"[NeuralOrganism] Cannot generate: no real words in vocab (actual={actual_vocab_size}, logits={len(logits)}, effective={effective_vocab_size}, special={len(SPECIAL_TOKENS)})")
                        break  # Exit generation loop - return what we have (just START token)
                    
                    if effective_vocab_size < len(logits):
                        # Create mask: -inf for tokens beyond actual vocabulary
                        mask = torch.full_like(logits, float('-inf'))
                        mask[:effective_vocab_size] = 0  # Keep actual vocabulary tokens
                        logits = logits + mask  # Apply mask (softmax will make -inf → 0 probability)
                    
                    # GROK-2 FIX: Apply repetition penalty to prevent "was was was" patterns
                    # Penalize tokens that appeared in recent generation window
                    # GROK REVIEW FIX: Use SUBTRACTION not division (division on negative logits increases probability!)
                    repetition_penalty = 2.0  # Penalty to subtract from logits (not divide)
                    recent_window = 5  # Look back this many tokens
                    if len(generated) > 0:
                        recent_tokens = generated[-recent_window:] if len(generated) >= recent_window else generated
                        for prev_token in recent_tokens:
                            if prev_token < len(logits):
                                # Reduce probability by subtracting from logits
                                logits[prev_token] = logits[prev_token] - repetition_penalty
                        # Extra penalty for immediately previous token (prevent "was was")
                        if generated[-1] < len(logits):
                            logits[generated[-1]] = logits[generated[-1]] - (repetition_penalty * 1.5)
                    
                    # GROK-2 FIX: Top-k sampling for better diversity
                    # Only sample from top-k most likely tokens
                    top_k = 40  # Number of top tokens to consider
                    # Count non-masked (finite) logits to avoid "selected index k out of range"
                    finite_count = torch.isfinite(logits).sum().item()
                    effective_k = min(top_k, finite_count, len(logits))
                    if effective_k > 0 and finite_count > effective_k:
                        # Get top-k indices (only if we have more finite values than k)
                        top_k_values, top_k_indices = torch.topk(logits, effective_k)
                        # Create mask keeping only top-k
                        top_k_mask = torch.full_like(logits, float('-inf'))
                        top_k_mask[top_k_indices] = 0
                        logits = logits + top_k_mask
                    
                    probs = torch.softmax(logits, dim=-1)
                    
                    # Check for NaN/Inf/zero probabilities
                    probs_sum = probs.sum().item()
                    nonzero_count = torch.count_nonzero(probs).item()
                    probs_valid = torch.isfinite(probs).all().item() and probs_sum > 1e-10 and nonzero_count > 0
                    
                    if not probs_valid:
                        # FALLBACK: If network can't decide, use uniform sampling over actual vocabulary
                        # This ensures 100% operation - every organism WILL respond
                        logger.debug(f"[ORGANISM] {self.species_id} using uniform fallback: sum={probs_sum}, nonzero={nonzero_count}")
                        # Create uniform distribution over actual words (skip special tokens)
                        uniform_probs = torch.zeros_like(probs)
                        word_start = len(SPECIAL_TOKENS)  # Skip <PAD>, <UNK>, <START>, <END>, <VP_GATE>
                        word_end = min(effective_vocab_size, len(uniform_probs))
                        if word_end > word_start:
                            # Uniform probability for actual words only
                            uniform_probs[word_start:word_end] = 1.0 / (word_end - word_start)
                            probs = uniform_probs
                            probs_valid = True
                        else:
                            # No actual words available - truly cannot generate
                            logger.warning(f"[ORGANISM] {self.species_id} no actual words for fallback: effective_vocab={effective_vocab_size}")
                            break
                    
                    # NEURAL SAMPLING: Let the network decide or stay silent
                    # No random fallbacks - if the network can't produce valid output, say nothing
                    next_token = None
                    sampling_success = False
                    
                    try:
                        next_token = torch.multinomial(probs, 1).item()
                        sampling_success = True
                    except (RuntimeError, AssertionError) as e:
                        # Network couldn't sample - organism stays silent
                        logger.warning(f"[ORGANISM] {self.species_id} multinomial FAILED: {e}, probs_sum={probs_sum}, nonzero={torch.count_nonzero(probs).item()}/{len(probs)}")
                        break
                    
                    # If sampling failed, stop generation
                    if not sampling_success or next_token is None:
                        break
                    
                    next_token = min(next_token, max(0, effective_vocab_size - 1))  # Clamp to valid range
                    
                    # Verify token maps to an actual word
                    word = vocab.get_word(next_token)
                    if word == '<UNK>' and effective_vocab_size > len(SPECIAL_TOKENS):
                        # Try nearby tokens to find a valid word
                        non_special_size = effective_vocab_size - len(SPECIAL_TOKENS)
                        found_valid = False
                        for offset in range(1, min(10, non_special_size)):
                            # Try both directions
                            for direction in [-1, 1]:
                                candidate = next_token + (offset * direction)
                                if candidate >= len(SPECIAL_TOKENS) and candidate < effective_vocab_size:
                                    candidate_word = vocab.get_word(candidate)
                                    if candidate_word and candidate_word != '<UNK>':
                                        next_token = candidate
                                        word = candidate_word
                                        found_valid = True
                                        break
                            if found_valid:
                                break
                        
                        # Track UNK count for early stopping
                        if not found_valid:
                            unk_count += 1
                        else:
                            unk_count = 0  # Reset on valid token
                    else:
                        unk_count = 0  # Reset on valid token
                    
                    # Early stopping: if too many consecutive UNKs, stop generation
                    if unk_count >= max_unk_before_stop:
                        break
                else:
                    # No language head, use action as pseudo-token
                    # Map action to a valid vocabulary token (use modulo to keep in range)
                    action_token = torch.argmax(output, dim=-1).item()
                    actual_vocab_size = len(vocab.word_to_id)  # Use actual vocabulary size
                    # Map action to vocabulary range (skip special tokens)
                    # Prevent division by zero if vocab only has special tokens
                    non_special_size = max(1, actual_vocab_size - len(SPECIAL_TOKENS))
                    if non_special_size > 0:
                        # Map to valid word token range (after special tokens)
                        next_token = (action_token % non_special_size) + len(SPECIAL_TOKENS)
                        next_token = min(next_token, actual_vocab_size - 1)
                        # Ensure token maps to an actual word (not just any ID)
                        # Try to find a valid word token by checking if it exists in vocabulary
                        max_attempts = min(10, non_special_size)
                        for attempt in range(max_attempts):
                            if next_token < actual_vocab_size:
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
        
        # ?? LEARNING FROM GENERATION: Record relationship success/failure
        # Evaluate generation quality and strengthen/weaken semantic relationships
        relationship_learning_enabled = self.config.get('neural', {}).get('language_model', {}).get('relationship_learning', {}).get('enabled', True)
        
        if relationship_learning_enabled and context_memory and hasattr(context_memory, 'vocabulary'):
            knowledge_web = None
            if hasattr(context_memory, 'knowledge_web'):
                knowledge_web = context_memory.knowledge_web
            elif hasattr(context_memory, 'language_teacher') and hasattr(context_memory.language_teacher, 'knowledge_web'):
                knowledge_web = context_memory.language_teacher.knowledge_web
            
            if knowledge_web and hasattr(self, '_generation_relationships') and self._generation_relationships:
                # Evaluate generation quality
                generation_quality = self._evaluate_generation_quality(generated, vocab, knowledge_web)
                
                # Record success/failure for each relationship used
                for relation in self._generation_relationships:
                    if generation_quality['is_coherent']:
                        # Successful use - strengthen relationship
                        try:
                            knowledge_web.record_relationship_success(
                                relation.source, relation.target, relation.relation_type
                            )
                        except Exception as e:
                            logger.debug(f"[NEURAL] Failed to record relationship success: {e}")
                    elif generation_quality['is_garbled']:
                        # Failed use - weaken relationship
                        try:
                            knowledge_web.record_relationship_failure(
                                relation.source, relation.target, relation.relation_type
                            )
                        except Exception as e:
                            logger.debug(f"[NEURAL] Failed to record relationship failure: {e}")
                
                # Clear tracked relationships for next generation
                self._generation_relationships = []
        
        # 🎲 DECAY LANGUAGE EPSILON: After each generation, reduce exploration rate
        # This allows organism to exploit learned knowledge as it matures
        if hasattr(self, 'language_epsilon') and hasattr(self, 'language_epsilon_end') and hasattr(self, 'language_epsilon_decay'):
            if self.language_epsilon > self.language_epsilon_end:
                self.language_epsilon = max(
                    self.language_epsilon_end, 
                    self.language_epsilon * self.language_epsilon_decay
                )
        
        # DECODE HERE - return text, not tokens. Vocab is local, only we can decode.
        response_words = vocab.decode(generated, skip_special=True)
        response_text = ' '.join(response_words) if response_words else ''
        
        # Return both for compatibility - text is primary, tokens for analysis
        return {'text': response_text, 'tokens': generated}
    
    def _evaluate_generation_quality(self, generated: List[int], vocab: Any, knowledge_web: Any) -> Dict[str, Any]:
        """
        Evaluate quality of generated token sequence.
        
        Assesses:
        - Coherence: Do words form semantically meaningful sequences?
        - Garbled: Are words randomly combined without semantic relationships?
        - Length: Is sequence appropriate length?
        - Special tokens: Too many UNK tokens indicates poor generation
        
        Args:
            generated: List of generated token IDs
            vocab: LanguageVocabulary instance
            knowledge_web: LinguisticKnowledgeWeb instance
            
        Returns:
            Dict with quality metrics:
            - is_coherent: bool - Words form meaningful semantic sequences
            - is_garbled: bool - Words are randomly combined
            - coherence_score: float - 0.0-1.0 semantic coherence
            - length_score: float - 0.0-1.0 appropriate length
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Get config for quality evaluation thresholds
        quality_config = self.config.get('neural', {}).get('language_model', {}).get('relationship_learning', {}).get('quality_evaluation', {})
        coherent_threshold = quality_config.get('coherent_threshold', 0.5)
        garbled_threshold = quality_config.get('garbled_threshold', 0.2)
        unk_ratio_threshold = quality_config.get('unk_ratio_threshold', 0.3)
        min_word_count = quality_config.get('min_word_count', 2)
        min_word_count_for_eval = quality_config.get('min_word_count_for_evaluation', 3)
        max_word_count = quality_config.get('max_word_count', 20)
        relationship_strength_threshold = quality_config.get('relationship_strength_threshold', 0.5)
        
        if not generated or len(generated) < 2:
            return {
                'is_coherent': False,
                'is_garbled': True,
                'coherence_score': 0.0,
                'length_score': 0.0
            }
        
        # Convert tokens to words
        words = []
        unk_count = 0
        special_tokens = {'<START>', '<END>', '<PAD>', '<UNK>', '<VP_GATE>'}
        
        for token in generated:
            word = vocab.get_word(token)
            if word:
                if word in special_tokens:
                    if word == '<UNK>':
                        unk_count += 1
                else:
                    words.append(word)
        
        # Too many UNK tokens = garbled
        unk_ratio = unk_count / len(generated) if generated else 0.0
        if unk_ratio > unk_ratio_threshold:
            return {
                'is_coherent': False,
                'is_garbled': True,
                'coherence_score': 0.0,
                'length_score': 0.0
            }
        
        # Too short = incomplete, too long = rambling
        word_count = len(words)
        if word_count < min_word_count:
            return {
                'is_coherent': False,
                'is_garbled': True,
                'coherence_score': 0.0,
                'length_score': 0.0
            }
        
        length_score = 1.0
        if word_count < min_word_count_for_eval:
            length_score = 0.5  # Too short
        elif word_count > max_word_count:
            length_score = 0.7  # Too long, might be rambling
        
        # Check semantic coherence: do consecutive words have semantic relationships?
        if not knowledge_web or word_count < min_word_count:
            return {
                'is_coherent': False,
                'is_garbled': True,
                'coherence_score': 0.0,
                'length_score': length_score
            }
        
        # Evaluate semantic relationships between consecutive words
        coherent_pairs = 0
        total_pairs = word_count - 1
        
        for i in range(len(words) - 1):
            word1 = words[i]
            word2 = words[i + 1]
            
            # Check if words have semantic relationship
            try:
                relations = knowledge_web.get_relations(word1)
                has_relationship = any(
                    (r.target == word2 or r.source == word2) and r.strength >= relationship_strength_threshold
                    for r in relations
                )
                
                # Also check reverse (word2 -> word1)
                if not has_relationship:
                    relations2 = knowledge_web.get_relations(word2)
                    has_relationship = any(
                        (r.target == word1 or r.source == word1) and r.strength >= relationship_strength_threshold
                        for r in relations2
                    )
                
                if has_relationship:
                    coherent_pairs += 1
            except Exception as e:
                logger.debug(f"[NEURAL] Error checking semantic relationship: {e}")
        
        coherence_score = coherent_pairs / total_pairs if total_pairs > 0 else 0.0
        
        # Determine if coherent or garbled (using config thresholds)
        is_coherent = coherence_score >= coherent_threshold
        is_garbled = coherence_score < garbled_threshold
        
        return {
            'is_coherent': is_coherent,
            'is_garbled': is_garbled,
            'coherence_score': coherence_score,
            'length_score': length_score,
            'word_count': word_count,
            'unk_ratio': unk_ratio
        }
    
    def get_language_embedding(self, context_memory: Any = None) -> Optional[np.ndarray]:
        """
        Extract semantic embedding from fc2 hidden state (post-attention, pre-language-head).
        
        Integration 1: Neural-ML Symbiosis - provides semantic representation for ML clustering.
        
        Args:
            context_memory: Optional context memory (not used but kept for API consistency)
            
        Returns:
            64-dim numpy array representing semantic embedding, or None if not available
        """
        if not PYTORCH_AVAILABLE or self.brain is None:
            return None
        
        if not hasattr(self.brain, 'use_language_head') or not self.brain.use_language_head:
            return None
        
        # Check cache - use cached embedding if state hasn't changed
        if len(self.state_history) > 0:
            current_state = self.state_history[-1]
            state_hash = hash(current_state.tobytes() if isinstance(current_state, np.ndarray) else str(current_state))
            
            if (self._cached_embedding is not None and 
                self._embedding_cache_state_hash == state_hash):
                return self._cached_embedding
        
        # Extract embedding from most recent state
        if len(self.state_history) == 0:
            return None
        
        state = self.state_history[-1]
        if not isinstance(state, np.ndarray):
            return None
        
        try:
            import torch
            
            # Get device from brain
            device = next(self.brain.parameters()).device
            
            # Convert state to tensor
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            
            # Forward pass through fc1 and fc2 (extract fc2 output)
            self.brain.eval()
            with torch.no_grad():
                # Forward through fc1
                x = self.brain.fc1(state_tensor)
                x = self.brain._get_activation(x)
                x = self.brain.dropout(x)
                
                # Apply attention if enabled
                if self.brain.use_attention:
                    # Reshape for attention: (batch, 1, hidden_dim)
                    x = x.unsqueeze(1)
                    x = self.brain.attention(x, vp_value=None)
                    x = self.brain.attention_norm(x)
                    x = x.squeeze(1)  # Back to (batch, hidden_dim)
                
                # Forward through fc2 (THIS IS THE EMBEDDING)
                embedding = self.brain.fc2(x)
                # Don't apply activation - keep raw 64-dim vector
                
                # Convert to numpy
                embedding_np = embedding.cpu().numpy().flatten()  # Shape: (64,)
            
            # Cache the embedding
            state_hash = hash(state.tobytes())
            self._cached_embedding = embedding_np
            self._embedding_cache_state_hash = state_hash
            
            return embedding_np
            
        except Exception as e:
            # Fallback: return zeros if extraction fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[NeuralOrganism] Failed to extract embedding: {e}")
            return np.zeros(64)  # Return zero vector as fallback
    
    def inherit_brain(self, parent_brain: OrganismBrain, 
                     mutation_rate: float = 0.2,  # Default matches config.json
                     crossover_rate: float = 0.9) -> Optional[OrganismBrain]:  # Default matches config.json
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
                input_dim=brain_config.get('input_dim', 27),
                hidden_dim=brain_config.get('hidden_dim', 64),
                output_dim=brain_config.get('output_dim', 6),
                activation=brain_config.get('activation', 'relu'),
                dropout=brain_config.get('dropout', 0.1)
            )
            # Copy parent weights (strict=False handles architecture changes)
            new_brain.load_state_dict(parent_brain.state_dict(), strict=False)
        
        # Add mutation
        new_brain.mutate(mutation_rate)
        
        return new_brain
    
    # ==========================================
    # ?? ATOMIC LANGUAGE SYSTEM METHODS
    # ==========================================
    
    def get_linguistic_atoms(self) -> Dict[str, Any]:
        """
        Get all linguistic atoms for this organism.
        
        Returns:
            Dictionary of concept_id -> atom data
        """
        if self.atomic_language is None:
            return {}
        return {cid: atom.to_dict() for cid, atom in self.atomic_language.atoms.items()}
    
    def get_activated_concepts(self, vp_state: tuple = None, top_k: int = 10) -> List[tuple]:
        """
        Get concepts most activated by current VP state.
        
        Args:
            vp_state: (vitality, pleasure) tuple
            top_k: Number of top concepts to return
            
        Returns:
            List of (concept_id, activation_score) tuples
        """
        if self.atomic_language is None:
            return []
        if vp_state is None:
            vp_state = (0.5, 0.5)
        return self.atomic_language.get_activated_concepts(vp_state, top_k=top_k)
    
    def acquire_concept(self, concept_id: str, source: str = 'observed', 
                       reason: str = 'unknown') -> bool:
        """
        Have the organism learn a new concept.
        
        Args:
            concept_id: The concept to learn
            source: How it was learned ('observed', 'taught', 'discovered')
            reason: Why it was learned
            
        Returns:
            True if concept was newly acquired, False if already known
        """
        if self.atomic_language is None:
            return False
        was_new = concept_id not in self.atomic_language.atoms
        self.atomic_language.acquire_concept(concept_id, source, reason=reason)
        
        # Generate tokens for learning events (TOKEN TUMBLER - concept acquisition)
        if was_new:
            # Learning new concepts is rewarding - strengthens language model
            source_reward = {'observed': 0.3, 'taught': 0.5, 'discovered': 0.7}
            reward = source_reward.get(source, 0.3)
            self.tumble_action_tokens(action=5, reward=reward, context='learn_concept')
        
        return was_new
    
    def form_concept_association(self, source: str, target: str, 
                                strength: float, reason: str) -> None:
        """
        Form an association between two concepts.
        
        Args:
            source: Source concept
            target: Target concept  
            strength: Association strength (-1 to 1)
            reason: Why the association formed
        """
        if self.atomic_language is not None:
            self.atomic_language.form_association(source, target, strength, reason)
            
            # Generate tokens for association formation (TOKEN TUMBLER - linking concepts)
            # Positive associations get positive reward, negative get modest positive
            # (learning any association is valuable, even negative ones)
            reward = max(0.2, abs(strength) * 0.5)
            self.tumble_action_tokens(action=6, reward=reward, context='form_association')
    
    def get_dialect_signature(self) -> np.ndarray:
        """
        Get this organism's linguistic signature for dialect analysis.
        
        Returns:
            Signature vector representing this organism's "dialect" (32-dim)
        """
        if self.atomic_language is None:
            return np.zeros(32)  # Matches compute_dialect_signature(fixed_length=32)
        return self.atomic_language.compute_dialect_signature()
    
    def get_concept_graph(self) -> Dict[str, Any]:
        """
        Get the organism's concept graph for visualization.
        
        Returns:
            Dictionary with 'nodes' and 'edges' for graph visualization
        """
        if self.atomic_language is None:
            return {'nodes': [], 'edges': []}
        return self.atomic_language.get_concept_graph()
    
    def get_linguistic_embedding(self, dim: int = 64) -> np.ndarray:
        """
        Get dense embedding from atomic language for neural network input.
        
        Args:
            dim: Desired embedding dimension
            
        Returns:
            Dense numpy array representing linguistic state
        """
        if self.atomic_language is None:
            return np.zeros(dim)
        return self.atomic_language.to_embedding(dim)
    
    # ==========================================
    # ?? ALLIANCE DECISION METHODS
    # Alliance decisions use the organism's neural 
    # network to evaluate social situations
    # ==========================================
    
    def evaluate_alliance_decision(self, 
                                   decision_type: str,
                                   context: Dict[str, Any],
                                   network_state: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str]:
        """
        Neural decision for alliance-related choices.
        
        This is the CORE method for organism agency in alliances.
        The organism's brain evaluates the situation and decides.
        
        Decision types:
            'propose_alliance' - Should I propose an alliance to this organism?
            'accept_alliance' - Should I accept this alliance proposal?
            'betray_alliance' - Should I betray my alliance?
            'vote_war' - Should I vote for war against this target?
            'challenge_leader' - Should I challenge for leadership?
            'leave_alliance' - Should I leave my current alliance?
        
        Args:
            decision_type: Type of alliance decision
            context: Context dict with relevant info:
                - target_id: ID of organism/alliance involved
                - target_fitness: Fitness of target organism
                - alliance_size: Current/proposed alliance size
                - my_reputation: My reputation in alliance
                - target_reputation: Target's reputation
                - trust_history: Dict of past interactions
                - war_target_threat: How threatening is war target
                - alliance_strength: Combined alliance strength
                - betrayal_count: How many times I've been betrayed
            network_state: Current network state
            
        Returns:
            Tuple of (decision: bool, confidence: float, reasoning: str)
        """
        # Build alliance-specific features from context
        alliance_features = self._extract_alliance_features(context)
        
        # Get base state features
        base_state = self.get_state_features(
            local_env={'alliance_context': context},
            network_state=network_state
        )
        
        # If brain not available, use heuristic decision
        if self.brain is None:
            return self._heuristic_alliance_decision(decision_type, context)
        
        import torch
        
        # Get action probabilities from brain
        self.brain.eval()
        with torch.no_grad():
            device = next(self.brain.parameters()).device
            state_tensor = torch.FloatTensor(base_state).to(device).unsqueeze(0)
            action_probs = self.brain.forward(state_tensor).cpu().numpy()[0]
        
        # Map brain outputs to alliance decision
        # Actions: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
        # Alliance mapping:
        #   cooperate (1) + compete (2) = social engagement
        #   isolate (5) = avoid/reject
        #   rest (3) = wait/uncertain
        
        cooperate_weight = action_probs[1]  # Cooperation tendency
        compete_weight = action_probs[2]    # Competition tendency
        isolate_weight = action_probs[5]    # Isolation tendency
        
        # Add alliance feature modifiers
        trust_mod = alliance_features.get('trust_level', 0.5)
        threat_mod = alliance_features.get('threat_level', 0.5)
        opportunity_mod = alliance_features.get('opportunity_score', 0.5)
        
        # Calculate decision score based on type
        if decision_type == 'propose_alliance':
            # Propose if: high cooperation, good trust, good opportunity
            score = (cooperate_weight * 0.4 + 
                    trust_mod * 0.3 + 
                    opportunity_mod * 0.3 -
                    isolate_weight * 0.2)
            threshold = 0.45
            
        elif decision_type == 'accept_alliance':
            # Accept if: high cooperation, proposer seems trustworthy
            score = (cooperate_weight * 0.5 + 
                    trust_mod * 0.3 +
                    (1 - threat_mod) * 0.2 -
                    isolate_weight * 0.2)
            threshold = 0.4
            
        elif decision_type == 'betray_alliance':
            # Betray if: high competition, low trust, high threat
            score = (compete_weight * 0.4 + 
                    threat_mod * 0.3 +
                    (1 - trust_mod) * 0.3 -
                    cooperate_weight * 0.3)
            threshold = 0.55  # Higher threshold - betrayal is serious
            
        elif decision_type == 'vote_war':
            # Vote war if: high competition, target is threat
            score = (compete_weight * 0.4 + 
                    threat_mod * 0.4 +
                    (1 - alliance_features.get('war_risk', 0.5)) * 0.2)
            threshold = 0.5
            
        elif decision_type == 'challenge_leader':
            # Challenge if: high competition, I'm strong, leader is weak
            my_fitness = self.fitness
            leader_fitness = context.get('leader_fitness', 0.5)
            fitness_advantage = my_fitness - leader_fitness
            
            score = (compete_weight * 0.4 + 
                    max(0, fitness_advantage) * 0.4 +
                    (1 - trust_mod) * 0.2)  # Distrust current leadership
            threshold = 0.55
            
        elif decision_type == 'leave_alliance':
            # Leave if: high isolation tendency, low trust, being exploited
            score = (isolate_weight * 0.4 + 
                    (1 - trust_mod) * 0.3 +
                    threat_mod * 0.3 -
                    cooperate_weight * 0.2)
            threshold = 0.5
            
        else:
            # Unknown decision type - default to cautious
            score = 0.3
            threshold = 0.5
        
        # Make decision
        decision = score > threshold
        confidence = abs(score - threshold) / (1.0 - threshold) if decision else abs(score - threshold) / threshold
        confidence = min(confidence, 1.0)
        
        # Generate reasoning
        reasoning = self._generate_alliance_reasoning(
            decision_type, decision, score, context, action_probs
        )
        
        # Emit event for Butterfly Engine tracking
        if self.event_emitter:
            import time
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='alliance',
                    event_type='alliance_decision',
                    data={
                        'organism_id': self.species_id,
                        'decision_type': decision_type,
                        'decision': decision,
                        'confidence': confidence,
                        'score': float(score),
                        'reasoning': reasoning,
                        'context': {k: v for k, v in context.items() 
                                   if isinstance(v, (int, float, str, bool))}
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass
        
        return decision, confidence, reasoning
    
    def _extract_alliance_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract normalized alliance features from context."""
        features = {}
        
        # Trust level (0-1, based on history)
        trust_history = context.get('trust_history', {})
        if trust_history:
            target_id = context.get('target_id')
            if target_id and target_id in trust_history:
                features['trust_level'] = trust_history[target_id].get('trust_score', 0.5)
            else:
                features['trust_level'] = 0.5  # Unknown = neutral
        else:
            features['trust_level'] = 0.5
        
        # Threat level (from context)
        features['threat_level'] = context.get('threat_level', 0.5)
        
        # Opportunity score (fitness differential, alliance benefits)
        target_fitness = context.get('target_fitness', 0.5)
        alliance_strength = context.get('alliance_strength', 0.5)
        features['opportunity_score'] = (target_fitness * 0.5 + alliance_strength * 0.5)
        
        # War risk (how risky is war declaration)
        features['war_risk'] = context.get('war_risk', 0.5)
        
        # Betrayal trauma (how many times betrayed)
        betrayal_count = context.get('betrayal_count', 0)
        features['betrayal_trauma'] = min(betrayal_count / 3.0, 1.0)  # Caps at 3 betrayals
        
        return features
    
    def _heuristic_alliance_decision(self, 
                                     decision_type: str, 
                                     context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Fallback heuristic when neural network unavailable."""
        import random
        
        # Extract key context
        target_fitness = context.get('target_fitness', 0.5)
        trust = context.get('trust_history', {}).get(context.get('target_id', ''), {}).get('trust_score', 0.5)
        threat = context.get('threat_level', 0.5)
        
        if decision_type == 'propose_alliance':
            # Propose to similar-fitness, trustworthy organisms
            fitness_diff = abs(self.fitness - target_fitness)
            score = 0.7 - fitness_diff * 0.5 + trust * 0.3
            decision = score > 0.5
            
        elif decision_type == 'accept_alliance':
            # Accept from trustworthy organisms
            score = trust * 0.6 + (1 - threat) * 0.4
            decision = score > 0.4
            
        elif decision_type == 'betray_alliance':
            # Betray rarely, based on distrust
            score = (1 - trust) * 0.5 + threat * 0.3
            decision = score > 0.6 and random.random() < 0.3
            
        elif decision_type == 'vote_war':
            # Vote for war if threat is high
            decision = threat > 0.6 and random.random() < 0.5
            
        elif decision_type == 'challenge_leader':
            # Challenge if significantly stronger
            leader_fitness = context.get('leader_fitness', 0.5)
            decision = self.fitness > leader_fitness + 0.2 and random.random() < 0.3
            
        else:
            decision = random.random() < 0.3
        
        reasoning = f"Heuristic {decision_type} decision (neural network unavailable)"
        return decision, 0.5, reasoning
    
    def _generate_alliance_reasoning(self, 
                                     decision_type: str, 
                                     decision: bool, 
                                     score: float,
                                     context: Dict[str, Any],
                                     action_probs: np.ndarray) -> str:
        """Generate human-readable reasoning for alliance decision."""
        action_names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        dominant_action = action_names[np.argmax(action_probs)]
        
        target_id = context.get('target_id', 'unknown')
        trust = context.get('trust_history', {}).get(target_id, {}).get('trust_score', 0.5)
        
        if decision_type == 'propose_alliance':
            if decision:
                return f"Proposing alliance to {target_id}: trust={trust:.2f}, tendency={dominant_action}, opportunity looks good"
            else:
                return f"Declining to propose alliance to {target_id}: trust too low or isolation preferred"
                
        elif decision_type == 'accept_alliance':
            if decision:
                return f"Accepting alliance proposal: cooperation tendency high, {target_id} seems trustworthy"
            else:
                return f"Rejecting alliance proposal: isolation preferred or {target_id} not trusted"
                
        elif decision_type == 'betray_alliance':
            if decision:
                return f"Choosing betrayal: competition drive high, trust has eroded, self-preservation"
            else:
                return f"Remaining loyal: cooperation outweighs competition, trust still holds"
                
        elif decision_type == 'vote_war':
            if decision:
                threat = context.get('threat_level', 0.5)
                return f"Voting FOR war: threat level {threat:.2f}, competition drive active"
            else:
                return f"Voting AGAINST war: risk too high or cooperation preferred"
                
        elif decision_type == 'challenge_leader':
            if decision:
                return f"Challenging leadership: fitness advantage detected, competition drive high"
            else:
                return f"Respecting current leader: not strong enough or cooperation preferred"
                
        else:
            return f"Alliance decision ({decision_type}): {'yes' if decision else 'no'} (score={score:.2f})"





