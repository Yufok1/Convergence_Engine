#!/usr/bin/env python3
"""Quick verification test for all major systems."""

import time
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_tuner():
    """Test ConfigTuner system."""
    print("\n[1/3] Testing ConfigTuner...")
    try:
        from reality_simulator.tuning.atomic_config import AtomicConfigSystem
        tuner = AtomicConfigSystem(system_id="test")
        print(f"  System ID: {tuner.system_id}")
        print(f"  Atoms registered: {len(tuner.atoms)}")
        print(f"  Domains: {list(tuner.domains.keys())[:3]}...")
        print("  ✅ ConfigTuner OK")
        return True
    except Exception as e:
        print(f"  ❌ ConfigTuner FAILED: {e}")
        return False

def test_language_game_bridge():
    """Test Language-Game Bridge."""
    print("\n[2/3] Testing Language-Game Bridge...")
    try:
        from reality_simulator.language.language_game_bridge import LanguageGameBridge
        bridge = LanguageGameBridge(context="drone", bias_strength=0.3, learning_rate=0.1)
        print(f"  Context: {bridge.context}")
        print(f"  Interpreter: {bridge.interpreter is not None}")
        print(f"  Bias computer: {bridge.bias_computer is not None}")
        print(f"  Learner: {bridge.learner is not None}")
        print("  ✅ Language-Game Bridge OK")
        return True
    except Exception as e:
        print(f"  ❌ Language-Game Bridge FAILED: {e}")
        return False

def test_drone_arena():
    """Test Drone Arena imports and structures."""
    print("\n[3/4] Testing Drone Arena...")
    try:
        from reality_simulator.arena.cocoon_drone_arena import CocoonDroneArena, DroneGameMode, DroneArenaConfig
        from reality_simulator.arena.cocoon_drone_arena import DronePhysics, DroneState
        # Test enum values exist
        modes = [DroneGameMode.FREE_FLY, DroneGameMode.TAG_BATTLE, DroneGameMode.SURVIVAL]
        print(f"  Game modes: {[m.value for m in modes]}")
        # Test config
        config = DroneArenaConfig()
        print(f"  Arena size: {config.arena_size}")
        print(f"  Gravity: {config.gravity} m/s²")
        print(f"  Max thrust: {config.max_thrust} N")
        print("  ✅ Drone Arena OK")
        return True
    except Exception as e:
        print(f"  ❌ Drone Arena FAILED: {e}")
        return False

def test_reality_simulator_quick():
    """Quick RealitySimulator test - imports only, no heavy init."""
    print("\n[4/4] Testing RealitySimulator (imports only)...")
    try:
        from reality_simulator.main import RealitySimulator
        from reality_simulator.neural.trainer import NeuralTrainer
        from reality_simulator.symbiotic_network import SymbioticNetwork
        print("  ✅ RealitySimulator imports OK")
        return True
    except Exception as e:
        print(f"  ❌ RealitySimulator FAILED: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("CONVERGENCE ENGINE - QUICK VERIFICATION")
    print("=" * 50)
    
    results = []
    results.append(("ConfigTuner", test_config_tuner()))
    results.append(("Language-Game Bridge", test_language_game_bridge()))
    results.append(("Drone Arena", test_drone_arena()))
    results.append(("RealitySimulator", test_reality_simulator_quick()))
    
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    sys.exit(0 if passed == len(results) else 1)
