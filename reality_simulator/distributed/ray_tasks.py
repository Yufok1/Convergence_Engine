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
"""

import logging
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
