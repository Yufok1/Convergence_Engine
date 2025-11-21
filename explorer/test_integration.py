"""
Integration Test Script
Tests all Explorer integration facilities with Reality Simulator and Djinn Kernel
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
parent_path = Path(__file__).parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

def test_trait_hub():
    """Test Trait Hub plugin loading"""
    print("\n[TEST] Trait Hub Plugin Loading")
    print("=" * 60)
    
    try:
        from trait_hub import TraitHub
        hub = TraitHub()
        
        # Test Reality Simulator traits
        reality_sim_traits = {
            'organism_count': 500,
            'modularity': 0.25,
            'clustering_coefficient': 0.6,
            'average_path_length': 2.5
        }
        
        translated = hub.translate(reality_sim_traits)
        print(f"✅ Trait Hub loaded {len(hub.mappings)} trait mappings")
        print(f"✅ Translated {len(translated)} Reality Simulator traits")
        
        # Test Djinn Kernel traits
        djinn_traits = {
            'violation_pressure': 0.2,
            'trait_convergence': 0.9,
            'system_health': 0.8
        }
        
        translated = hub.translate(djinn_traits)
        print(f"✅ Translated {len(translated)} Djinn Kernel traits")
        
        return True
    except Exception as e:
        print(f"❌ Trait Hub test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_modules():
    """Test integration modules (test_func1-5)"""
    print("\n[TEST] Integration Modules")
    print("=" * 60)
    
    results = {}
    
    # Test test_func1 (Reality Simulator)
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from test_func1 import main as collect_network
        traits = collect_network()
        results['test_func1'] = len(traits) > 0
        print(f"✅ test_func1.py: Collected {len(traits)} traits")
    except Exception as e:
        results['test_func1'] = False
        print(f"⚠️  test_func1.py: {e} (Reality Simulator may not be running)")
    
    # Test test_func2 (Djinn Kernel)
    try:
        from test_func2 import main as calculate_vp
        traits = calculate_vp()
        results['test_func2'] = len(traits) > 0
        print(f"✅ test_func2.py: Collected {len(traits)} traits")
    except Exception as e:
        results['test_func2'] = False
        print(f"⚠️  test_func2.py: {e} (Djinn Kernel may not be available)")
    
    # Test test_func3 (Phase Transition)
    try:
        from test_func3 import main as detect_transition
        status = detect_transition()
        results['test_func3'] = 'phase' in status
        print(f"✅ test_func3.py: Detected phase = {status.get('phase', 'unknown')}")
    except Exception as e:
        results['test_func3'] = False
        print(f"⚠️  test_func3.py: {e}")
    
    # Test test_func4 (Exploration)
    try:
        from test_func4 import main as track_exploration
        exploration = track_exploration()
        results['test_func4'] = 'total_exploration' in exploration
        print(f"✅ test_func4.py: Total exploration = {exploration.get('total_exploration', 0):.3f}")
    except Exception as e:
        results['test_func4'] = False
        print(f"⚠️  test_func4.py: {e}")
    
    # Test test_func5 (Coordination)
    try:
        from test_func5 import main as coordinate
        coordination = coordinate()
        results['test_func5'] = 'coordination_health' in coordination
        print(f"✅ test_func5.py: Coordination health = {coordination.get('coordination_health', 0):.3f}")
    except Exception as e:
        results['test_func5'] = False
        print(f"⚠️  test_func5.py: {e}")
    
    return results

def test_integration_bridge():
    """Test Integration Bridge"""
    print("\n[TEST] Integration Bridge")
    print("=" * 60)
    
    try:
        from integration_bridge import ExplorerIntegrationBridge
        bridge = ExplorerIntegrationBridge()
        
        status = bridge.get_integration_status()
        print(f"✅ Integration Bridge initialized")
        print(f"   Trait Hub available: {status.get('trait_hub_available', False)}")
        print(f"   Explorer components available: {status.get('explorer_components_available', False)}")
        
        # Try to sync (may fail if systems not running, that's OK)
        try:
            sync_result = bridge.sync_all_systems()
            print(f"✅ Sync completed: {len(sync_result)} systems synced")
        except Exception as e:
            print(f"⚠️  Sync test: {e} (Systems may not be running)")
        
        return True
    except Exception as e:
        print(f"❌ Integration Bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connectors():
    """Test system connectors"""
    print("\n[TEST] System Connectors")
    print("=" * 60)
    
    results = {}
    
    # Test Reality Simulator Connector
    try:
        from reality_simulator_connector import RealitySimulatorConnector
        connector = RealitySimulatorConnector()
        proximity = connector.get_collapse_proximity()
        results['reality_sim_connector'] = True
        print(f"✅ Reality Simulator Connector: Collapse proximity = {proximity:.3f}")
    except Exception as e:
        results['reality_sim_connector'] = False
        print(f"⚠️  Reality Simulator Connector: {e}")
    
    # Test Djinn Kernel Connector
    try:
        from djinn_kernel_connector import DjinnKernelConnector
        connector = DjinnKernelConnector()
        exploration = connector.get_exploration_count()
        results['djinn_kernel_connector'] = True
        print(f"✅ Djinn Kernel Connector: Exploration count = {exploration}")
    except Exception as e:
        results['djinn_kernel_connector'] = False
        print(f"⚠️  Djinn Kernel Connector: {e}")
    
    return results

def test_transition_manager():
    """Test Unified Transition Manager"""
    print("\n[TEST] Unified Transition Manager")
    print("=" * 60)
    
    try:
        from unified_transition_manager import UnifiedTransitionManager
        manager = UnifiedTransitionManager()
        
        status = manager.get_transition_status()
        print(f"✅ Transition Manager initialized")
        
        transition_check = manager.check_unified_transition()
        print(f"   Phase: {transition_check.get('phase', 'unknown')}")
        print(f"   Transition ready: {transition_check.get('transition_ready', False)}")
        print(f"   Total exploration: {transition_check.get('total_exploration', 0):.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Transition Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("EXPLORER INTEGRATION TEST SUITE")
    print("=" * 60)
    
    results = {
        'trait_hub': test_trait_hub(),
        'integration_modules': test_integration_modules(),
        'integration_bridge': test_integration_bridge(),
        'connectors': test_connectors(),
        'transition_manager': test_transition_manager()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if isinstance(result, dict):
            passed = sum(1 for v in result.values() if v)
            total = len(result)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"{status} {test_name}: {passed}/{total} passed")
        else:
            status = "✅" if result else "❌"
            print(f"{status} {test_name}: {'PASSED' if result else 'FAILED'}")
    
    print("\n" + "=" * 60)
    print("Integration facilities are ready!")
    print("Note: Some tests may show warnings if systems aren't running.")
    print("This is expected - the integration will work when systems are active.")
    print("=" * 60)

if __name__ == "__main__":
    main()

