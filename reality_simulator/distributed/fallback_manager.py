# Sequential Fallback Manager
# Drop-in replacement when Ray is unavailable - maintains same interface

"""
Sequential Fallback Manager

Provides the same interface as RayManager but executes everything sequentially.
This allows code to be written once and work whether Ray is available or not.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SequentialFallback:
    """
    Drop-in replacement for RayManager when Ray is unavailable.
    
    All operations execute sequentially on the main thread.
    Maintains the same interface for transparent degradation.
    """
    
    def __init__(self, config: dict = None):
        """Initialize fallback manager."""
        self.config = config or {}
        self._initialized = False
        self._stats = {
            'total_tasks': 0,
            'total_time_ms': 0,
            'fallback_reason': 'ray_unavailable'
        }
        logger.info("[SequentialFallback] Initialized - Ray not available")
    
    def is_initialized(self) -> bool:
        """Ray is never initialized in fallback mode."""
        return False
    
    def init(self) -> bool:
        """No-op in fallback mode."""
        return False
    
    def shutdown(self) -> None:
        """No-op in fallback mode."""
        pass
    
    def map_parallel(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """
        Execute function on items sequentially.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            **kwargs: Additional arguments passed to func
            
        Returns:
            List of results
        """
        start_time = time.time()
        results = []
        
        for item in items:
            try:
                result = func(item, **kwargs) if kwargs else func(item)
                results.append(result)
            except Exception as e:
                logger.warning(f"[SequentialFallback] Task failed: {e}")
                results.append(None)
        
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats['total_tasks'] += len(items)
        self._stats['total_time_ms'] += elapsed_ms
        
        return results
    
    def map_parallel_with_index(self, func: Callable, items: List[Any], **kwargs) -> Dict[int, Any]:
        """
        Execute function on items sequentially, returning dict with indices.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            **kwargs: Additional arguments passed to func
            
        Returns:
            Dict mapping index to result
        """
        results = self.map_parallel(func, items, **kwargs)
        return {i: result for i, result in enumerate(results)}
    
    def parallel_decide_all(self, organisms: dict, network_state: dict, 
                            breath_state: dict = None) -> Dict[str, Any]:
        """
        Execute organism decisions sequentially.
        
        Args:
            organisms: Dict of org_id -> organism
            network_state: Current network state
            breath_state: Current breath state (optional)
            
        Returns:
            Dict of org_id -> action
        """
        start_time = time.time()
        decisions = {}
        
        for org_id, organism in organisms.items():
            if hasattr(organism, 'decide_action') and hasattr(organism, 'brain') and organism.brain is not None:
                try:
                    local_env = {
                        'resources': getattr(organism, 'resources', 0.5),
                        'neighbors': 0  # Simplified in fallback
                    }
                    action = organism.decide_action(
                        local_env=local_env,
                        network_state=network_state,
                        breath_state=breath_state
                    )
                    decisions[org_id] = action
                except Exception as e:
                    logger.warning(f"[SequentialFallback] Decision failed for {org_id}: {e}")
        
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats['total_tasks'] += len(organisms)
        self._stats['total_time_ms'] += elapsed_ms
        
        return decisions
    
    def parallel_extract_features(self, organisms: dict, feature_extractor: Callable) -> List[Any]:
        """
        Extract features from organisms sequentially.
        
        Args:
            organisms: Dict of org_id -> organism
            feature_extractor: Function to extract features from organism
            
        Returns:
            List of feature vectors
        """
        return self.map_parallel(feature_extractor, list(organisms.values()))
    
    def parallel_resolve_battles(self, battle_pairs: List[tuple], 
                                  battle_resolver: Callable) -> List[Any]:
        """
        Resolve battles sequentially.
        
        Args:
            battle_pairs: List of (org_a, org_b) tuples
            battle_resolver: Function to resolve a battle
            
        Returns:
            List of battle results
        """
        return self.map_parallel(
            lambda pair: battle_resolver(pair[0], pair[1]),
            battle_pairs
        )
    
    def get_stats(self) -> dict:
        """Get execution statistics."""
        return {
            **self._stats,
            'mode': 'sequential_fallback',
            'ray_available': False,
            'avg_time_per_task_ms': (
                self._stats['total_time_ms'] / max(1, self._stats['total_tasks'])
            )
        }
    
    def get_resources(self) -> dict:
        """Get available resources (minimal in fallback mode)."""
        import os
        return {
            'num_cpus': os.cpu_count() or 1,
            'num_gpus': 0,
            'object_store_memory': 0,
            'mode': 'sequential_fallback'
        }


# Convenience function for testing
def create_fallback() -> SequentialFallback:
    """Create a new SequentialFallback instance."""
    return SequentialFallback()
