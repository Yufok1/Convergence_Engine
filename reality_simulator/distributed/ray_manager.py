# Ray Manager - Core Ray lifecycle and parallel execution management
# Handles Ray initialization, resource monitoring, and parallel task dispatch

"""
Ray Manager for Convergence Engine

Provides Ray-based parallelization with:
- Lifecycle management (init/shutdown)
- Resource monitoring
- Parallel task dispatch
- Graceful error handling with fallback
- Config-driven behavior
"""

import logging
import time
import os
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Import Ray (already validated in __init__.py)
try:
    import ray
    from ray.util.state import list_actors, list_tasks
except ImportError:
    ray = None


@dataclass
class RayConfig:
    """Configuration for Ray execution."""
    enabled: bool = True
    num_cpus: Optional[int] = None
    num_gpus: Optional[int] = None
    object_store_memory: Optional[int] = None
    parallelization_threshold: int = 50
    actor_pool_size: int = 4
    batch_inference_size: int = 32
    fallback_on_error: bool = True
    logging_level: str = "warning"
    
    # State synchronization
    snapshot_strategy: str = "breath_cycle"
    consistency_model: str = "sequential"
    max_state_age_ms: int = 100
    
    # Memory management
    max_object_refs: int = 100
    cleanup_on_organism_death: bool = True
    
    @classmethod
    def from_dict(cls, config: dict) -> 'RayConfig':
        """Create RayConfig from config dict."""
        ray_config = config.get('ray', {})
        state_sync = ray_config.get('state_synchronization', {})
        memory_mgmt = ray_config.get('memory_management', {})
        
        return cls(
            enabled=ray_config.get('enabled', True),
            num_cpus=ray_config.get('num_cpus'),
            num_gpus=ray_config.get('num_gpus'),
            object_store_memory=ray_config.get('object_store_memory'),
            parallelization_threshold=ray_config.get('parallelization_threshold', 50),
            actor_pool_size=ray_config.get('actor_pool_size', 4),
            batch_inference_size=ray_config.get('batch_inference_size', 32),
            fallback_on_error=ray_config.get('fallback_on_error', True),
            logging_level=ray_config.get('logging_level', 'warning'),
            snapshot_strategy=state_sync.get('snapshot_strategy', 'breath_cycle'),
            consistency_model=state_sync.get('consistency_model', 'sequential'),
            max_state_age_ms=state_sync.get('max_state_age_ms', 100),
            max_object_refs=memory_mgmt.get('max_object_refs', 100),
            cleanup_on_organism_death=memory_mgmt.get('cleanup_on_organism_death', True),
        )


class RayManager:
    """
    Central Ray lifecycle and execution manager.
    
    Handles:
    - Ray initialization and shutdown
    - Resource monitoring
    - Parallel task dispatch
    - Object store memory management
    - Graceful error handling
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize Ray Manager.
        
        Args:
            config: Config dict with /ray/* settings
        """
        self.config = RayConfig.from_dict(config or {})
        self._initialized = False
        self._object_refs: Dict[str, Any] = {}  # Track object store refs
        self._stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_time_ms': 0,
            'init_time': None
        }
        
        # Auto-initialize if enabled
        if self.config.enabled:
            self.init()
    
    def init(self) -> bool:
        """
        Initialize Ray runtime.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        if ray is None:
            logger.warning("[RayManager] Ray not installed")
            return False
        
        try:
            # Build init kwargs
            init_kwargs = {
                'ignore_reinit_error': True,
                'logging_level': getattr(logging, self.config.logging_level.upper(), logging.WARNING),
            }
            
            if self.config.num_cpus is not None:
                init_kwargs['num_cpus'] = self.config.num_cpus
            if self.config.num_gpus is not None:
                init_kwargs['num_gpus'] = self.config.num_gpus
            if self.config.object_store_memory is not None:
                init_kwargs['object_store_memory'] = self.config.object_store_memory
            
            # Initialize Ray
            ray.init(**init_kwargs)
            
            self._initialized = True
            self._stats['init_time'] = time.time()
            
            resources = self.get_resources()
            logger.info(f"[RayManager] Initialized - CPUs: {resources['num_cpus']}, "
                       f"GPUs: {resources['num_gpus']}, "
                       f"Object Store: {resources['object_store_memory'] / 1e9:.1f}GB")
            
            return True
            
        except Exception as e:
            logger.error(f"[RayManager] Initialization failed: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown Ray runtime."""
        if self._initialized and ray is not None:
            try:
                ray.shutdown()
                self._initialized = False
                logger.info("[RayManager] Shutdown complete")
            except Exception as e:
                logger.warning(f"[RayManager] Shutdown error: {e}")
    
    def is_initialized(self) -> bool:
        """Check if Ray is initialized and ready."""
        return self._initialized and ray is not None and ray.is_initialized()
    
    def get_resources(self) -> dict:
        """Get available Ray resources."""
        if not self.is_initialized():
            return {
                'num_cpus': os.cpu_count() or 1,
                'num_gpus': 0,
                'object_store_memory': 0,
                'mode': 'not_initialized'
            }
        
        try:
            resources = ray.available_resources()
            return {
                'num_cpus': resources.get('CPU', 0),
                'num_gpus': resources.get('GPU', 0),
                'object_store_memory': resources.get('object_store_memory', 0),
                'mode': 'ray'
            }
        except Exception:
            return {
                'num_cpus': os.cpu_count() or 1,
                'num_gpus': 0,
                'object_store_memory': 0,
                'mode': 'ray_error'
            }
    
    def should_parallelize(self, item_count: int) -> bool:
        """
        Determine if parallelization is worthwhile.
        
        Args:
            item_count: Number of items to process
            
        Returns:
            True if parallelization would be beneficial
        """
        if not self.is_initialized():
            return False
        return item_count >= self.config.parallelization_threshold
    
    def map_parallel(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """
        Execute function on items in parallel using Ray tasks.
        
        Falls back to sequential execution if:
        - Ray not initialized
        - Item count below threshold
        - Errors occur (if fallback_on_error=True)
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            **kwargs: Additional arguments passed to func
            
        Returns:
            List of results
        """
        # Check if parallelization is worthwhile
        if not self.should_parallelize(len(items)):
            return self._sequential_map(func, items, **kwargs)
        
        start_time = time.time()
        
        try:
            # Create remote function
            remote_func = ray.remote(func)
            
            # Submit all tasks
            if kwargs:
                futures = [remote_func.remote(item, **kwargs) for item in items]
            else:
                futures = [remote_func.remote(item) for item in items]
            
            # Wait for results
            results = ray.get(futures)
            
            # Update stats
            elapsed_ms = (time.time() - start_time) * 1000
            self._stats['total_tasks'] += len(items)
            self._stats['successful_tasks'] += len(items)
            self._stats['total_time_ms'] += elapsed_ms
            
            return results
            
        except Exception as e:
            logger.warning(f"[RayManager] Parallel execution failed: {e}")
            self._stats['failed_tasks'] += len(items)
            
            if self.config.fallback_on_error:
                logger.info("[RayManager] Falling back to sequential execution")
                return self._sequential_map(func, items, **kwargs)
            else:
                raise
    
    def _sequential_map(self, func: Callable, items: List[Any], **kwargs) -> List[Any]:
        """Execute function on items sequentially (fallback)."""
        start_time = time.time()
        results = []
        
        for item in items:
            try:
                result = func(item, **kwargs) if kwargs else func(item)
                results.append(result)
            except Exception as e:
                logger.warning(f"[RayManager] Sequential task failed: {e}")
                results.append(None)
        
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats['total_tasks'] += len(items)
        self._stats['total_time_ms'] += elapsed_ms
        
        return results
    
    def put(self, obj: Any, key: str = None) -> Any:
        """
        Put object in Ray Object Store.
        
        Args:
            obj: Object to store
            key: Optional key for tracking (for cleanup)
            
        Returns:
            ObjectRef
        """
        if not self.is_initialized():
            return obj  # Return object directly if Ray not available
        
        try:
            # Memory management - cleanup old refs if at limit
            if len(self._object_refs) >= self.config.max_object_refs:
                self._cleanup_oldest_refs()
            
            ref = ray.put(obj)
            
            if key:
                self._object_refs[key] = ref
            
            return ref
            
        except Exception as e:
            logger.warning(f"[RayManager] put() failed: {e}")
            return obj
    
    def get(self, ref_or_obj: Any) -> Any:
        """
        Get object from Ray Object Store or return directly.
        
        Args:
            ref_or_obj: ObjectRef or direct object
            
        Returns:
            The object
        """
        if not self.is_initialized():
            return ref_or_obj
        
        try:
            if hasattr(ref_or_obj, '__class__') and 'ObjectRef' in ref_or_obj.__class__.__name__:
                return ray.get(ref_or_obj)
            return ref_or_obj
        except Exception as e:
            logger.warning(f"[RayManager] get() failed: {e}")
            return ref_or_obj
    
    def cleanup_ref(self, key: str) -> None:
        """Remove tracked object reference."""
        if key in self._object_refs:
            del self._object_refs[key]
    
    def _cleanup_oldest_refs(self, count: int = 10) -> None:
        """Remove oldest tracked object references."""
        keys_to_remove = list(self._object_refs.keys())[:count]
        for key in keys_to_remove:
            del self._object_refs[key]
        logger.debug(f"[RayManager] Cleaned up {len(keys_to_remove)} object refs")
    
    def get_stats(self) -> dict:
        """Get execution statistics."""
        return {
            **self._stats,
            'mode': 'ray' if self.is_initialized() else 'fallback',
            'ray_available': ray is not None,
            'ray_initialized': self.is_initialized(),
            'tracked_object_refs': len(self._object_refs),
            'avg_time_per_task_ms': (
                self._stats['total_time_ms'] / max(1, self._stats['total_tasks'])
            ),
            'success_rate': (
                self._stats['successful_tasks'] / max(1, self._stats['total_tasks'])
            )
        }
    
    # ==================== SPECIALIZED PARALLEL METHODS ====================
    
    def parallel_extract_features(self, organisms: dict, 
                                   feature_extractor: Callable) -> List[Any]:
        """
        Extract features from organisms in parallel.
        
        This is the LOWEST RISK parallelization target - pure computation
        with no state management complexity.
        
        Args:
            organisms: Dict of org_id -> organism
            feature_extractor: Function to extract features from organism state
            
        Returns:
            List of feature vectors
        """
        if not self.should_parallelize(len(organisms)):
            return [feature_extractor(org) for org in organisms.values()]
        
        # Extract state dicts first (serializable)
        org_states = [
            org.get_state() if hasattr(org, 'get_state') else {'id': org_id}
            for org_id, org in organisms.items()
        ]
        
        return self.map_parallel(feature_extractor, org_states)
    
    def parallel_resolve_battles(self, battle_pairs: List[Tuple[Any, Any]], 
                                  battle_resolver: Callable) -> List[Any]:
        """
        Resolve battles in parallel.
        
        Battles are STATELESS during resolution - ideal for Ray tasks.
        State mutations (trait absorption) happen AFTER all battles complete.
        
        Args:
            battle_pairs: List of (org_a_state, org_b_state) tuples
            battle_resolver: Function to resolve a single battle
            
        Returns:
            List of battle results
        """
        if not self.should_parallelize(len(battle_pairs)):
            return [battle_resolver(a, b) for a, b in battle_pairs]
        
        # Wrap resolver to accept tuple
        def resolve_pair(pair):
            return battle_resolver(pair[0], pair[1])
        
        return self.map_parallel(resolve_pair, battle_pairs)


# Factory function
def create_ray_manager(config: dict = None) -> RayManager:
    """Create a new RayManager instance."""
    return RayManager(config)
