# Reality Simulator - Distributed Computing Module
# Ray integration for parallel organism decisions, training, and analysis
#
# This module provides optional Ray-based parallelization with graceful
# fallback to sequential execution when Ray is unavailable.

"""
Distributed Computing Integration for Convergence Engine

Provides Ray-based parallelization for:
- Neural organism decisions (3-4x speedup)
- DQN training (2-3x speedup)
- Highlander battle resolution (4-5x speedup)
- ML feature extraction (4-5x speedup)

Usage:
    from reality_simulator.distributed import get_ray_manager
    
    ray_manager = get_ray_manager()
    if ray_manager.is_initialized():
        results = ray_manager.map_parallel(func, items)
    else:
        results = [func(item) for item in items]
"""

import logging

logger = logging.getLogger(__name__)

# Check Ray availability
try:
    import ray
    RAY_AVAILABLE = True
    RAY_VERSION = ray.__version__
    logger.info(f"[Distributed] Ray {RAY_VERSION} available")
except ImportError:
    RAY_AVAILABLE = False
    RAY_VERSION = None
    ray = None
    logger.info("[Distributed] Ray not available - using sequential fallback")


def get_ray_manager(config: dict = None):
    """
    Get the appropriate execution manager based on Ray availability.
    
    Returns RayManager if Ray is available and enabled in config,
    otherwise returns SequentialFallback for transparent degradation.
    
    Args:
        config: Optional config dict with /ray/* settings
        
    Returns:
        RayManager or SequentialFallback instance
    """
    if RAY_AVAILABLE:
        # Check if Ray is enabled in config
        ray_config = config.get('ray', {}) if config else {}
        if ray_config.get('enabled', True):
            from .ray_manager import RayManager
            return RayManager(ray_config)
        else:
            logger.info("[Distributed] Ray disabled in config - using fallback")
    
    from .fallback_manager import SequentialFallback
    return SequentialFallback()


def is_ray_available() -> bool:
    """Check if Ray is available for import."""
    return RAY_AVAILABLE


def get_ray_version() -> str:
    """Get Ray version string or None if unavailable."""
    return RAY_VERSION


__all__ = [
    'get_ray_manager',
    'is_ray_available', 
    'get_ray_version',
    'RAY_AVAILABLE',
    'RAY_VERSION',
]

# Also export task functions for direct use
from .ray_tasks import (
    extract_organism_features_local,
    extract_features_batch,
    resolve_battle_local,
    resolve_battles_batch,
    evaluate_connection_local,
    evaluate_connections_batch,
)

__all__.extend([
    'extract_organism_features_local',
    'extract_features_batch',
    'resolve_battle_local',
    'resolve_battles_batch',
    'evaluate_connection_local',
    'evaluate_connections_batch',
])
