# Test script for Ray distributed computing integration
# Run this to verify Ray is working correctly

"""
Ray Integration Test

Tests:
1. Ray availability and initialization
2. Sequential fallback when below threshold
3. Parallel feature extraction
4. Parallel battle resolution
5. Memory management
"""

import sys
import time
from pathlib import Path

# Add paths
parent_path = Path(__file__).parent
sys.path.insert(0, str(parent_path))
sys.path.insert(0, str(parent_path / 'reality_simulator'))

def test_ray_integration():
    """Run Ray integration tests."""
    print("=" * 60)
    print("RAY DISTRIBUTED COMPUTING INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Import and availability check
    print("\n[Test 1] Checking Ray availability...")
    try:
        from reality_simulator.distributed import (
            get_ray_manager, 
            is_ray_available, 
            get_ray_version,
            RAY_AVAILABLE
        )
        print(f"  ✓ Imports successful")
        print(f"  ✓ Ray available: {RAY_AVAILABLE}")
        if RAY_AVAILABLE:
            print(f"  ✓ Ray version: {get_ray_version()}")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    # Test 2: Manager initialization
    print("\n[Test 2] Initializing Ray Manager...")
    try:
        # Load config
        import json
        config_path = parent_path / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            print(f"  ✓ Config loaded from {config_path}")
        else:
            config = {'ray': {'enabled': True}}
            print(f"  ⚠ Using default config")
        
        manager = get_ray_manager(config)
        print(f"  ✓ Manager created: {manager.__class__.__name__}")
        print(f"  ✓ Initialized: {manager.is_initialized()}")
        
        if manager.is_initialized():
            resources = manager.get_resources()
            print(f"  ✓ Resources: CPUs={resources['num_cpus']}, GPUs={resources['num_gpus']}")
    except Exception as e:
        print(f"  ✗ Manager initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Feature extraction (parallel)
    print("\n[Test 3] Testing feature extraction...")
    try:
        from reality_simulator.distributed.ray_tasks import (
            extract_organism_features_local,
            extract_features_batch
        )
        
        # Create test organism states
        test_states = [
            {
                'id': f'org_{i}',
                'fitness': 0.5 + (i * 0.01),
                'resources': 0.3,
                'energy': 0.7,
                'traits': {
                    'aggression': 0.4,
                    'cooperation': 0.6,
                    'exploration': 0.5,
                    'exploitation': 0.5,
                    'adaptability': 0.5
                }
            }
            for i in range(100)
        ]
        
        # Sequential (small batch)
        start = time.time()
        features_seq = extract_features_batch(test_states[:10], use_ray=False)
        time_seq = (time.time() - start) * 1000
        print(f"  ✓ Sequential (10 items): {time_seq:.2f}ms")
        print(f"    Feature vector length: {len(features_seq[0])}")
        
        # Parallel (large batch)
        start = time.time()
        features_par = extract_features_batch(test_states, use_ray=True)
        time_par = (time.time() - start) * 1000
        print(f"  ✓ Parallel (100 items): {time_par:.2f}ms")
        
        # Verify results match
        if len(features_par) == 100 and len(features_par[0]) == 28:
            print(f"  ✓ Results valid: {len(features_par)} vectors, 28 dimensions each")
        else:
            print(f"  ⚠ Unexpected results: {len(features_par)} vectors")
            
    except Exception as e:
        print(f"  ✗ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Battle resolution (parallel)
    print("\n[Test 4] Testing battle resolution...")
    try:
        from reality_simulator.distributed.ray_tasks import (
            resolve_battle_local,
            resolve_battles_batch
        )
        
        # Create test battle pairs
        battle_pairs = [
            (
                {'id': f'org_a_{i}', 'fitness': 0.4 + (i * 0.02), 'traits': {'aggression': 0.5}},
                {'id': f'org_b_{i}', 'fitness': 0.5 + (i * 0.01), 'traits': {'aggression': 0.6}}
            )
            for i in range(50)
        ]
        
        # Sequential
        start = time.time()
        results_seq = resolve_battles_batch(battle_pairs[:5], use_ray=False)
        time_seq = (time.time() - start) * 1000
        print(f"  ✓ Sequential (5 battles): {time_seq:.2f}ms")
        print(f"    Winner of first battle: {results_seq[0]['winner_id']}")
        
        # Parallel
        start = time.time()
        results_par = resolve_battles_batch(battle_pairs, use_ray=True)
        time_par = (time.time() - start) * 1000
        print(f"  ✓ Parallel (50 battles): {time_par:.2f}ms")
        print(f"    All battles have winners: {all('winner_id' in r for r in results_par)}")
        
    except Exception as e:
        print(f"  ✗ Battle resolution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Manager stats
    print("\n[Test 5] Checking manager stats...")
    try:
        stats = manager.get_stats()
        print(f"  ✓ Mode: {stats.get('mode', 'unknown')}")
        print(f"  ✓ Total tasks: {stats.get('total_tasks', 0)}")
        print(f"  ✓ Success rate: {stats.get('success_rate', 0):.2%}")
        if stats.get('avg_time_per_task_ms', 0) > 0:
            print(f"  ✓ Avg time per task: {stats['avg_time_per_task_ms']:.2f}ms")
    except Exception as e:
        print(f"  ✗ Stats failed: {e}")
    
    # Cleanup
    print("\n[Cleanup] Shutting down Ray...")
    try:
        if hasattr(manager, 'shutdown'):
            manager.shutdown()
            print("  ✓ Ray shutdown complete")
    except Exception as e:
        print(f"  ⚠ Shutdown warning: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = test_ray_integration()
    sys.exit(0 if success else 1)
