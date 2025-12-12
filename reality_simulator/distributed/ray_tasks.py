# Ray Tasks - Stateless parallel task definitions
# These are @ray.remote decorated functions for embarrassingly parallel work

"""
Ray Tasks for Convergence Engine

Stateless task definitions for:
- ML feature extraction (lowest risk, highest speedup)
- Battle resolution (stateless during computation)
- Connection evaluation

These tasks have NO state management complexity - they receive
all inputs as arguments and return results.

SEMANTIC CONVERGENCE COMPATIBILITY NOTE:
    Ray workers serialize/deserialize data - PyTorch nn.Embedding updates inside
    Ray workers happen on COPIES and do NOT propagate back to the main process.
    
    This is BY DESIGN: Semantic convergence word embedding updates happen in the
    main process via LanguageTeacher.teach_network(), which is called AFTER Ray
    batch operations complete. The teach_network() flow:
    
    1. Ray batch training completes
    2. Main process calls teach_network(organisms, context_memory, generation, trainer)
    3. teach_organism() extracts organism.get_language_embedding() 
    4. link_word_to_node() updates word_embedding in main process memory
    
    This ensures embedding updates are properly accumulated centrally.
"""

import logging
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Conditional Ray import
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False


# ==================== ML FEATURE EXTRACTION ====================
# LOWEST RISK - Pure computation, no state management

def extract_organism_features_local(org_state: dict, context: dict = None) -> List[float]:
    """
    Extract feature vector from organism state (non-Ray version).
    
    This is the core feature extraction logic that can run with or without Ray.
    
    Args:
        org_state: Organism state dictionary
        context: Optional context (network state, etc.)
        
    Returns:
        Feature vector as list of floats
    """
    features = []
    
    # Basic traits (if available)
    traits = org_state.get('traits', {})
    features.extend([
        traits.get('aggression', 0.5),
        traits.get('cooperation', 0.5),
        traits.get('exploration', 0.5),
        traits.get('exploitation', 0.5),
        traits.get('adaptability', 0.5),
    ])
    
    # Fitness and resources
    features.append(org_state.get('fitness', 0.5))
    features.append(org_state.get('resources', 0.5))
    features.append(org_state.get('energy', 0.5))
    
    # Neural state features (if available)
    neural_state = org_state.get('neural_state', {})
    features.extend([
        neural_state.get('epsilon', 0.5),
        neural_state.get('learning_rate', 0.001),
        neural_state.get('experience_count', 0) / 1000.0,  # Normalized
    ])
    
    # Network features (if context provided)
    if context:
        features.append(context.get('neighbor_count', 0) / 10.0)  # Normalized
        features.append(context.get('alliance_size', 0) / 5.0)   # Normalized
    else:
        features.extend([0.0, 0.0])
    
    # Ensure consistent length (pad or truncate to 24 dimensions)
    target_len = 24
    if len(features) < target_len:
        features.extend([0.0] * (target_len - len(features)))
    elif len(features) > target_len:
        features = features[:target_len]
    
    return features


if RAY_AVAILABLE:
    @ray.remote
    def extract_organism_features_remote(org_state: dict, context: dict = None) -> List[float]:
        """
        Ray remote task for feature extraction.
        
        Wraps the local function for parallel execution.
        """
        return extract_organism_features_local(org_state, context)


def extract_features_batch(org_states: List[dict], context: dict = None, 
                           use_ray: bool = True) -> List[List[float]]:
    """
    Extract features from multiple organisms, optionally using Ray.
    
    Args:
        org_states: List of organism state dicts
        context: Optional shared context
        use_ray: Whether to use Ray parallelization
        
    Returns:
        List of feature vectors
    """
    if not use_ray or not RAY_AVAILABLE or len(org_states) < 50:
        # Sequential extraction
        return [extract_organism_features_local(state, context) for state in org_states]
    
    # Parallel extraction with Ray
    try:
        # Put context in object store (shared across all tasks)
        context_ref = ray.put(context) if context else None
        
        # Submit all tasks
        futures = [
            extract_organism_features_remote.remote(state, context_ref)
            for state in org_states
        ]
        
        # Wait for results
        return ray.get(futures)
        
    except Exception as e:
        logger.warning(f"[RayTasks] Feature extraction failed, falling back: {e}")
        return [extract_organism_features_local(state, context) for state in org_states]


# ==================== BATTLE RESOLUTION ====================
# MEDIUM RISK - Stateless during computation, mutations happen after

def resolve_battle_local(org_a_state: dict, org_b_state: dict, 
                         config: dict = None) -> dict:
    """
    Resolve a battle between two organisms (non-Ray version).
    
    This is STATELESS - no mutations occur during resolution.
    State changes (trait absorption) happen AFTER all battles complete.
    
    Args:
        org_a_state: First organism's state
        org_b_state: Second organism's state
        config: Battle configuration
        
    Returns:
        Battle result dict with winner, loser, and details
    """
    config = config or {}
    chaos_factor = config.get('chaos_factor', 0.15)
    
    import random
    
    # Calculate effective fitness
    fitness_a = org_a_state.get('fitness', 0.5)
    fitness_b = org_b_state.get('fitness', 0.5)
    
    # Apply traits to battle
    traits_a = org_a_state.get('traits', {})
    traits_b = org_b_state.get('traits', {})
    
    # Aggression bonus
    effective_a = fitness_a * (1 + traits_a.get('aggression', 0.5) * 0.2)
    effective_b = fitness_b * (1 + traits_b.get('aggression', 0.5) * 0.2)
    
    # Apply chaos factor
    effective_a *= (1 + random.uniform(-chaos_factor, chaos_factor))
    effective_b *= (1 + random.uniform(-chaos_factor, chaos_factor))
    
    # Determine winner
    if effective_a > effective_b:
        winner_id = org_a_state.get('id', 'org_a')
        loser_id = org_b_state.get('id', 'org_b')
        winner_fitness = fitness_a
        loser_fitness = fitness_b
    else:
        winner_id = org_b_state.get('id', 'org_b')
        loser_id = org_a_state.get('id', 'org_a')
        winner_fitness = fitness_b
        loser_fitness = fitness_a
    
    return {
        'winner_id': winner_id,
        'loser_id': loser_id,
        'winner_fitness': winner_fitness,
        'loser_fitness': loser_fitness,
        'effective_a': effective_a,
        'effective_b': effective_b,
        'margin': abs(effective_a - effective_b),
        'timestamp': time.time()
    }


if RAY_AVAILABLE:
    @ray.remote
    def resolve_battle_remote(org_a_state: dict, org_b_state: dict, 
                              config_ref) -> dict:
        """
        Ray remote task for battle resolution.
        
        Wraps the local function for parallel execution.
        config_ref can be an ObjectRef or direct dict.
        """
        # Handle ObjectRef
        config = ray.get(config_ref) if hasattr(config_ref, '__class__') and 'ObjectRef' in config_ref.__class__.__name__ else config_ref
        return resolve_battle_local(org_a_state, org_b_state, config)


def resolve_battles_batch(battle_pairs: List[Tuple[dict, dict]], 
                          config: dict = None,
                          use_ray: bool = True) -> List[dict]:
    """
    Resolve multiple battles, optionally using Ray.
    
    Args:
        battle_pairs: List of (org_a_state, org_b_state) tuples
        config: Battle configuration
        use_ray: Whether to use Ray parallelization
        
    Returns:
        List of battle results
    """
    if not use_ray or not RAY_AVAILABLE or len(battle_pairs) < 10:
        # Sequential resolution
        return [resolve_battle_local(a, b, config) for a, b in battle_pairs]
    
    # Parallel resolution with Ray
    try:
        # Put config in object store (shared across all tasks)
        config_ref = ray.put(config) if config else None
        
        # Submit all tasks
        futures = [
            resolve_battle_remote.remote(a, b, config_ref)
            for a, b in battle_pairs
        ]
        
        # Wait for results
        return ray.get(futures)
        
    except Exception as e:
        logger.warning(f"[RayTasks] Battle resolution failed, falling back: {e}")
        return [resolve_battle_local(a, b, config) for a, b in battle_pairs]


# ==================== CONNECTION EVALUATION ====================
# LOW RISK - Stateless network analysis

def evaluate_connection_local(connection: Tuple[str, str], 
                               network_state: dict) -> dict:
    """
    Evaluate a network connection strength.
    
    Args:
        connection: (node_a_id, node_b_id) tuple
        network_state: Current network state
        
    Returns:
        Connection evaluation dict
    """
    node_a, node_b = connection
    
    # Get node states
    nodes = network_state.get('nodes', {})
    state_a = nodes.get(node_a, {})
    state_b = nodes.get(node_b, {})
    
    # Calculate connection strength
    fitness_similarity = 1.0 - abs(
        state_a.get('fitness', 0.5) - state_b.get('fitness', 0.5)
    )
    
    trait_compatibility = 0.5  # Default
    if 'traits' in state_a and 'traits' in state_b:
        # Cooperation attracts, aggression repels
        coop_a = state_a['traits'].get('cooperation', 0.5)
        coop_b = state_b['traits'].get('cooperation', 0.5)
        trait_compatibility = (coop_a + coop_b) / 2
    
    strength = (fitness_similarity + trait_compatibility) / 2
    
    return {
        'connection': connection,
        'strength': strength,
        'fitness_similarity': fitness_similarity,
        'trait_compatibility': trait_compatibility
    }


if RAY_AVAILABLE:
    @ray.remote
    def evaluate_connection_remote(connection: Tuple[str, str], 
                                    network_state_ref) -> dict:
        """Ray remote task for connection evaluation."""
        network_state = ray.get(network_state_ref) if hasattr(network_state_ref, '__class__') and 'ObjectRef' in network_state_ref.__class__.__name__ else network_state_ref
        return evaluate_connection_local(connection, network_state)


def evaluate_connections_batch(connections: List[Tuple[str, str]], 
                                network_state: dict,
                                use_ray: bool = True) -> List[dict]:
    """
    Evaluate multiple connections, optionally using Ray.
    
    Args:
        connections: List of (node_a, node_b) tuples
        network_state: Current network state
        use_ray: Whether to use Ray parallelization
        
    Returns:
        List of connection evaluations
    """
    if not use_ray or not RAY_AVAILABLE or len(connections) < 100:
        # Sequential evaluation
        return [evaluate_connection_local(conn, network_state) for conn in connections]
    
    # Parallel evaluation with Ray
    try:
        # Put network state in object store (shared across all tasks)
        state_ref = ray.put(network_state)
        
        # Submit all tasks
        futures = [
            evaluate_connection_remote.remote(conn, state_ref)
            for conn in connections
        ]
        
        # Wait for results
        return ray.get(futures)
        
    except Exception as e:
        logger.warning(f"[RayTasks] Connection evaluation failed, falling back: {e}")
        return [evaluate_connection_local(conn, network_state) for conn in connections]


# ==================== NEURAL TRAINING ====================
# MEDIUM-HIGH RISK - Per-organism gradient computation
# State sync handled by returning updated weights

def train_organism_local(
    brain_weights: dict,
    experience_batch: dict,
    training_config: dict,
    language_config: dict = None
) -> dict:
    """
    Train a single organism's brain on a batch of experiences.
    
    This performs one gradient update on the brain weights.
    State is passed in/out as serializable dicts.
    
    Args:
        brain_weights: Serialized brain state_dict
        experience_batch: Dict with states, actions, rewards, next_states, dones
        training_config: Training hyperparameters
        language_config: Optional language training config
        
    Returns:
        Dict with updated weights, loss, and training stats
    """
    try:
        import torch
        import torch.nn.functional as F
        import torch.optim as optim
    except ImportError:
        return {'success': False, 'error': 'PyTorch not available'}
    
    try:
        # Extract config
        learning_rate = training_config.get('learning_rate', 0.001)
        gamma = training_config.get('gamma', 0.995)  # Default matches config.json
        rl_loss_weight = training_config.get('rl_loss_weight', 0.8)
        language_loss_weight = training_config.get('language_loss_weight', 0.1)
        device = training_config.get('device', 'cpu')
        
        # Import brain class for reconstruction
        from reality_simulator.neural.brain import OrganismBrain
        
        # Reconstruct brain from weights
        input_dim = training_config.get('input_dim', 25)
        hidden_dim = training_config.get('hidden_dim', 64)
        output_dim = training_config.get('output_dim', 5)
        vocab_size = training_config.get('vocab_size', 128)
        use_language_head = training_config.get('use_language_head', False)
        
        brain = OrganismBrain(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            vocab_size=vocab_size,
            use_language_head=use_language_head,
            device=device
        )
        
        # Load weights (strict=False handles architecture changes)
        brain.load_state_dict(brain_weights, strict=False)
        brain.to(device)
        
        # Convert experiences to tensors
        states_tensor = torch.FloatTensor(experience_batch['states']).to(device)
        actions_tensor = torch.LongTensor(experience_batch['actions']).to(device)
        rewards_tensor = torch.FloatTensor(experience_batch['rewards']).to(device)
        next_states_tensor = torch.FloatTensor(experience_batch['next_states']).to(device)
        dones_tensor = torch.BoolTensor(experience_batch['dones']).to(device)
        
        # Get current Q values
        brain.train()
        q_values = brain(states_tensor)
        q_value = q_values.gather(1, actions_tensor.unsqueeze(1)).squeeze(1)
        
        # Get next Q values (no gradient)
        brain.eval()
        with torch.no_grad():
            next_q_values = brain(next_states_tensor)
            next_q_value = next_q_values.max(1)[0]
        
        # Calculate target Q values
        target_q_value = rewards_tensor + (gamma * next_q_value * ~dones_tensor)
        
        # Calculate RL loss
        rl_loss = F.mse_loss(q_value, target_q_value)
        loss = rl_loss_weight * rl_loss
        
        # Language loss if applicable
        language_loss_value = 0.0
        if language_config and language_config.get('enabled'):
            token_seq = language_config.get('token_sequence', [])
            if len(token_seq) >= 2:
                try:
                    input_tokens = torch.LongTensor([token_seq[:-1]]).to(device)
                    target_tokens = torch.LongTensor([token_seq[1:]]).to(device)
                    
                    brain.train()
                    _, language_logits = brain(states_tensor[:1], return_language_logits=True)
                    
                    if language_logits is not None:
                        if language_logits.dim() == 2:
                            language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                        
                        # Simple cross-entropy loss
                        lang_loss = F.cross_entropy(
                            language_logits.view(-1, language_logits.size(-1)),
                            target_tokens.view(-1)
                        )
                        loss = loss + language_loss_weight * lang_loss
                        language_loss_value = lang_loss.item()
                except Exception:
                    pass  # Skip language loss on error
        
        # Backpropagation
        brain.train()
        optimizer = optim.Adam(brain.parameters(), lr=learning_rate)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Extract updated weights
        updated_weights = {k: v.cpu().detach() for k, v in brain.state_dict().items()}
        
        return {
            'success': True,
            'updated_weights': updated_weights,
            'loss': loss.item(),
            'rl_loss': rl_loss.item(),
            'language_loss': language_loss_value,
            'batch_size': len(states_tensor)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if RAY_AVAILABLE:
    @ray.remote(num_cpus=1)
    def train_organism_remote(
        brain_weights: dict,
        experience_batch: dict,
        training_config_ref,
        language_config: dict = None
    ) -> dict:
        """
        Ray remote task for organism training.
        
        Wraps the local function for parallel execution.
        """
        # Resolve config ref if needed
        training_config = ray.get(training_config_ref) if hasattr(training_config_ref, '__class__') and 'ObjectRef' in training_config_ref.__class__.__name__ else training_config_ref
        return train_organism_local(brain_weights, experience_batch, training_config, language_config)


def train_organisms_batch(
    training_tasks: List[dict],
    training_config: dict,
    use_ray: bool = True
) -> List[dict]:
    """
    Train multiple organisms in parallel.
    
    Args:
        training_tasks: List of dicts with 'brain_weights', 'experience_batch', 'language_config'
        training_config: Shared training configuration
        use_ray: Whether to use Ray parallelization
        
    Returns:
        List of training results
    """
    # Disable Ray for training on Windows due to access violation issues
    # Use sequential training for now (can be re-enabled once Ray Windows compatibility is fixed)
    if not use_ray or not RAY_AVAILABLE or len(training_tasks) < 4 or sys.platform == 'win32':
        # Sequential training
        return [
            train_organism_local(
                task['brain_weights'],
                task['experience_batch'],
                training_config,
                task.get('language_config')
            )
            for task in training_tasks
        ]
    
    # Parallel training with Ray
    try:
        # Put config in object store (shared across all tasks)
        # Ensure config is fully serializable (deep copy of primitives only)
        import copy
        serializable_config = {
            k: copy.deepcopy(v) if isinstance(v, (dict, list, tuple)) else v
            for k, v in training_config.items()
            if isinstance(v, (int, float, str, bool, dict, list, tuple, type(None)))
        }
        config_ref = ray.put(serializable_config)
        
        # Submit all tasks
        futures = [
            train_organism_remote.remote(
                task['brain_weights'],
                task['experience_batch'],
                config_ref,
                task.get('language_config')
            )
            for task in training_tasks
        ]
        
        # Wait for results with timeout
        return ray.get(futures, timeout=30.0)
        
    except (ray.exceptions.RayError, ray.exceptions.RayActorError, MemoryError, OSError) as e:
        logger.warning(f"[RayTasks] Organism training failed (Ray error), falling back to sequential: {type(e).__name__}: {e}")
        return [
            train_organism_local(
                task['brain_weights'],
                task['experience_batch'],
                training_config,
                task.get('language_config')
            )
            for task in training_tasks
        ]
    except Exception as e:
        logger.warning(f"[RayTasks] Organism training failed (general error), falling back to sequential: {type(e).__name__}: {e}")
        import traceback
        logger.debug(f"[RayTasks] Traceback: {traceback.format_exc()}")
        return [
            train_organism_local(
                task['brain_weights'],
                task['experience_batch'],
                training_config,
                task.get('language_config')
            )
            for task in training_tasks
        ]
