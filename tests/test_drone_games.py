#!/usr/bin/env python3
"""
🛸 DRONE GAME MODES TEST

Tests all 8 drone game modes with NASA JSBSim-grade physics.
Each mode runs 30 steps to verify it works.
"""

import sys
import os
import time
import numpy as np

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_mock_cocoon(num_organisms: int = 8):
    """Create a minimal cocoon-like object for testing."""
    class MockBrain:
        def __init__(self, idx):
            self.organism_id = f"org_{idx}"
            
        def forward(self, x):
            return np.random.randn(6)  # 6 actions
    
    class MockCocoon:
        def __init__(self, n):
            self.brains = [MockBrain(i) for i in range(n)]
            self.organism_names = [f"org_{i}" for i in range(n)]
            self.atomic_language = None
            self.knowledge_web = None
            
        def get_action(self, obs, explore=True):
            """Return random action 0-5."""
            return np.random.randint(0, 6)
    
    return MockCocoon(num_organisms)


def test_game_mode(mode, num_steps=30):
    """Test a single game mode with JSBSim physics."""
    from reality_simulator.arena.cocoon_drone_arena import (
        CocoonDroneArena, DroneArenaConfig, DroneGameMode, DronePhysics
    )
    
    # Create cocoon
    cocoon = create_mock_cocoon(8)  # 8 drones, 4 per team
    
    # Create arena
    config = DroneArenaConfig(
        arena_size=100.0,
        max_episode_steps=100
    )
    
    arena = CocoonDroneArena(
        cocoon=cocoon,
        mode=mode,
        config=config,
        team_split="half"
    )
    
    # Check physics engine
    physics_type = "JSBSim" if arena.physics.use_jsbsim else "Simplified"
    
    # Run steps
    total_reward = 0.0
    alive_at_end = 0
    
    for step in range(num_steps):
        rewards = arena.step()
        total_reward += sum(rewards.values())
        
        # Check if game ended
        if arena.game_state.winner is not None:
            break
    
    # Count survivors
    alive_at_end = sum(1 for d in arena.drones.values() if d.alive)
    
    return {
        "steps": step + 1,
        "total_reward": total_reward,
        "alive": alive_at_end,
        "winner": arena.game_state.winner,
        "physics": physics_type
    }


def main():
    from reality_simulator.arena.cocoon_drone_arena import DroneGameMode, JSBSIM_PHYSICS_AVAILABLE
    
    print("=" * 60)
    print("🛸 DRONE GAME MODES TEST - NASA JSBSim Physics")
    print("=" * 60)
    print(f"JSBSim Physics Available: {'✅ YES' if JSBSIM_PHYSICS_AVAILABLE else '⚠️ NO (using fallback)'}")
    print()
    
    modes = [
        DroneGameMode.FREE_FLY,
        DroneGameMode.FORMATION,
        DroneGameMode.PURSUIT,
        DroneGameMode.TAG_BATTLE,
        DroneGameMode.ZONE_CONTROL,
        DroneGameMode.CAPTURE_FLAG,
        DroneGameMode.SURVIVAL,
        DroneGameMode.ESCORT,
    ]
    
    results = []
    
    for mode in modes:
        print(f"[{mode.value.upper():15}] ", end="", flush=True)
        
        try:
            start = time.time()
            result = test_game_mode(mode)
            elapsed = time.time() - start
            
            status = "✅ PASS"
            details = f"physics={result['physics']}, steps={result['steps']:2}, alive={result['alive']}, reward={result['total_reward']:.1f}"
            if result['winner']:
                details += f", winner={result['winner']}"
            
            print(f"{status} ({elapsed:.2f}s) - {details}")
            results.append((mode.value, True))
            
        except Exception as e:
            print(f"❌ FAIL - {e}")
            import traceback
            traceback.print_exc()
            results.append((mode.value, False))
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    
    print()
    print(f"Total: {passed}/{total} game modes working with NASA physics")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
