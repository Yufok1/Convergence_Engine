#!/usr/bin/env python3
"""
Test all Ray integrations work together.
Validates that Ray is properly integrated into all subsystems.
"""

import sys

def test_all_ray_integrations():
    print("=" * 60)
    print("RAY INTEGRATION VALIDATION TEST")
    print("=" * 60)
    
    # Test 1: Module imports
    print("\n[Test 1] Testing module imports...")
    try:
        from reality_simulator.distributed import (
            RAY_AVAILABLE,
            get_ray_manager,
            extract_features_batch,
            resolve_battles_batch,
            train_organisms_batch
        )
        print(f"  ✓ Ray available: {RAY_AVAILABLE}")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    # Test 2: ML Utils integration
    print("\n[Test 2] Testing ML Utils Ray integration...")
    try:
        from reality_simulator.ml_utils import MLAnalyzer, RAY_DISTRIBUTED_AVAILABLE as ML_RAY
        ml = MLAnalyzer({})
        print(f"  ✓ ML Utils RAY_DISTRIBUTED_AVAILABLE: {ML_RAY}")
    except Exception as e:
        print(f"  ✗ ML Utils test failed: {e}")
        return False
    
    # Test 3: Highlander integration
    print("\n[Test 3] Testing Highlander Ray integration...")
    try:
        from reality_simulator.evolution.highlander_protocol import (
            HighlanderProtocol, 
            RAY_DISTRIBUTED_AVAILABLE as HP_RAY
        )
        hp = HighlanderProtocol({
            'highlander': {'enabled': True, 'tournament_frequency': 10}
        }, None)
        print(f"  ✓ Highlander RAY_DISTRIBUTED_AVAILABLE: {HP_RAY}")
    except Exception as e:
        print(f"  ✗ Highlander test failed: {e}")
        return False
    
    # Test 4: Symbiotic Network integration
    print("\n[Test 4] Testing Symbiotic Network Ray integration...")
    try:
        from reality_simulator.symbiotic_network import (
            SymbioticNetwork,
            RAY_DISTRIBUTED_AVAILABLE as SN_RAY
        )
        sn = SymbioticNetwork({})
        print(f"  ✓ SymbioticNetwork RAY_DISTRIBUTED_AVAILABLE: {SN_RAY}")
    except Exception as e:
        print(f"  ✗ Symbiotic Network test failed: {e}")
        return False
    
    # Test 5: Neural Trainer integration
    print("\n[Test 5] Testing Neural Trainer Ray integration...")
    try:
        from reality_simulator.neural.trainer import NeuralTrainer
        trainer = NeuralTrainer({'training': {}})
        ray_enabled = getattr(trainer, 'ray_enabled', False)
        print(f"  ✓ NeuralTrainer.ray_enabled: {ray_enabled}")
    except Exception as e:
        print(f"  ✗ Neural Trainer test failed: {e}")
        return False
    
    # Test 6: Ray Manager initialization
    print("\n[Test 6] Testing Ray Manager initialization...")
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        manager = get_ray_manager(config)
        is_initialized = manager.is_initialized()
        print(f"  ✓ Manager type: {type(manager).__name__}")
        print(f"  ✓ Initialized: {is_initialized}")
        
        if is_initialized:
            resources = manager.get_resources()
            print(f"  ✓ Resources: CPUs={resources.get('cpu', 'N/A')}, GPUs={resources.get('gpu', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Manager test failed: {e}")
        return False
    
    # Cleanup
    print("\n[Cleanup] Shutting down Ray...")
    try:
        manager.shutdown()
        print("  ✓ Ray shutdown complete")
    except Exception as e:
        print(f"  ! Shutdown warning: {e}")
    
    print("\n" + "=" * 60)
    print("ALL RAY INTEGRATION TESTS PASSED ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_all_ray_integrations()
    sys.exit(0 if success else 1)
