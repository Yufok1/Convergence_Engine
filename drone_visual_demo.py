#!/usr/bin/env python3
"""
🛸 DRONE VISUAL DEMO

Watch organisms control drones in real-time 3D simulation!

Requirements:
    pip install PyFlyt gymnasium

Usage:
    python drone_visual_demo.py              # Single drone hover demo
    python drone_visual_demo.py --battle     # 1v1 dogfight (requires 2 drones)
    python drone_visual_demo.py --race       # Racing through gates
    python drone_visual_demo.py --swarm      # Multi-drone formation
"""

import sys
import time
import argparse
import numpy as np

# Check for PyFlyt
try:
    import gymnasium
    import PyFlyt.gym_envs
    PYFLYT_AVAILABLE = True
    print("✅ PyFlyt available - 3D visualization enabled!")
except ImportError:
    PYFLYT_AVAILABLE = False
    print("❌ PyFlyt not installed. Install with:")
    print("   pip install PyFlyt")
    print("\nPyFlyt provides:")
    print("   - Real physics simulation (PyBullet)")
    print("   - 3D visualization")
    print("   - Multiple drone types (QuadX, Rocket, etc)")
    sys.exit(1)


def create_mock_organism(name: str, strategy: str = "random"):
    """Create a mock organism with different strategies."""
    class MockOrganism:
        def __init__(self, name, strategy):
            self.organism_id = f"{name}_{np.random.randint(1000, 9999)}"
            self.strategy = strategy
            self.step_count = 0
            
        def decide(self):
            """Make a decision based on strategy."""
            self.step_count += 1
            
            if self.strategy == "random":
                return np.random.randint(0, 6)
            elif self.strategy == "aggressive":
                # Mostly COMPETE (2) and MOVE (0)
                return np.random.choice([0, 2, 2, 2, 0, 5], p=[0.2, 0.3, 0.2, 0.15, 0.1, 0.05])
            elif self.strategy == "defensive":
                # Mostly REST (3) and ISOLATE (5)
                return np.random.choice([3, 5, 5, 1, 0, 4], p=[0.3, 0.25, 0.2, 0.15, 0.05, 0.05])
            elif self.strategy == "cooperative":
                # Mostly COOPERATE (1)
                return np.random.choice([1, 1, 0, 3, 1, 2], p=[0.35, 0.2, 0.15, 0.15, 0.1, 0.05])
            elif self.strategy == "cyclic":
                # Cycle through actions
                return self.step_count % 6
            else:
                return np.random.randint(0, 6)
    
    return MockOrganism(name, strategy)


def demo_single_drone():
    """Demo: Single drone controlled by organism."""
    print("\n" + "="*60)
    print("🛸 SINGLE DRONE DEMO")
    print("="*60)
    print("Watch an organism learn to control a drone!")
    print("Actions: MOVE, COOPERATE, COMPETE, REST, REPRODUCE, ISOLATE")
    print("\nPress Ctrl+C to stop\n")
    
    from reality_simulator.arena.drone_adapter import OrganismDroneAdapter, DroneAction
    
    # Create organism and adapter
    org = create_mock_organism("pilot", strategy="cyclic")
    adapter = OrganismDroneAdapter(org, drone_id=0, team="blue")
    
    # Create environment with rendering
    env = gymnasium.make("PyFlyt/QuadX-Hover-v4", render_mode="human")
    
    obs, info = env.reset()
    adapter.update_state(obs)
    
    total_reward = 0
    step = 0
    
    try:
        while True:
            # Get organism's decision
            action_idx, drone_cmd = adapter.get_action()
            action_name = DroneAction(action_idx).name
            
            # Execute in environment
            obs, reward, terminated, truncated, info = env.step(drone_cmd)
            
            # Update adapter
            adapter.update_state(obs)
            adapter.tick(0.02)
            
            total_reward += reward
            step += 1
            
            # Print status every 50 steps
            if step % 50 == 0:
                print(f"Step {step:4d} | Action: {action_name:10s} | Reward: {reward:+.2f} | Total: {total_reward:.1f}")
            
            if terminated or truncated:
                print(f"\n🔄 Episode ended. Total reward: {total_reward:.1f}")
                obs, info = env.reset()
                adapter.update_state(obs)
                total_reward = 0
                step = 0
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    finally:
        env.close()


def demo_racing():
    """Demo: Drone racing through gates."""
    print("\n" + "="*60)
    print("🏁 DRONE RACING DEMO")
    print("="*60)
    print("Watch organism race through waypoints!")
    print("\nPress Ctrl+C to stop\n")
    
    from reality_simulator.arena.drone_adapter import OrganismDroneAdapter, DroneAction
    
    # Create organism
    org = create_mock_organism("racer", strategy="aggressive")
    adapter = OrganismDroneAdapter(org, drone_id=0, team="blue")
    
    # Try waypoint environment
    try:
        env = gymnasium.make("PyFlyt/QuadX-Waypoints-v4", render_mode="human")
    except:
        print("Waypoints env not available, using Hover")
        env = gymnasium.make("PyFlyt/QuadX-Hover-v4", render_mode="human")
    
    obs, info = env.reset()
    adapter.update_state(obs)
    
    total_reward = 0
    step = 0
    
    try:
        while True:
            action_idx, drone_cmd = adapter.get_action()
            
            # Boost forward thrust for racing
            drone_cmd[0] = min(1.0, drone_cmd[0] + 0.3)
            
            obs, reward, terminated, truncated, info = env.step(drone_cmd)
            adapter.update_state(obs)
            adapter.tick(0.02)
            
            total_reward += reward
            step += 1
            
            if step % 100 == 0:
                action_name = DroneAction(action_idx).name
                print(f"Step {step:4d} | Action: {action_name:10s} | Pos: {adapter.state.position}")
            
            if terminated or truncated:
                print(f"\n🏁 Race ended! Score: {total_reward:.1f}")
                obs, info = env.reset()
                adapter.update_state(obs)
                total_reward = 0
                step = 0
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    finally:
        env.close()


def demo_battle():
    """Demo: 1v1 drone dogfight (simulated in single env)."""
    print("\n" + "="*60)
    print("⚔️ DRONE DOGFIGHT DEMO")
    print("="*60)
    print("Aggressive vs Defensive organism!")
    print("(Note: True multi-drone requires PyFlyt multi-agent setup)")
    print("\nPress Ctrl+C to stop\n")
    
    from reality_simulator.arena.drone_adapter import OrganismDroneAdapter, DroneAction
    
    # Create two organisms with different strategies
    org_red = create_mock_organism("aggressor", strategy="aggressive")
    org_blue = create_mock_organism("defender", strategy="defensive")
    
    adapter_red = OrganismDroneAdapter(org_red, drone_id=0, team="red")
    adapter_blue = OrganismDroneAdapter(org_blue, drone_id=1, team="blue")
    
    # Single drone view (alternating control for demo)
    env = gymnasium.make("PyFlyt/QuadX-Hover-v4", render_mode="human")
    
    obs, info = env.reset()
    
    # Set up fake enemy positions
    adapter_red.state.enemies_positions = [np.array([3.0, 0.0, 2.0])]
    adapter_blue.state.enemies_positions = [np.array([-3.0, 0.0, 2.0])]
    
    current_adapter = adapter_red
    other_adapter = adapter_blue
    step = 0
    
    print("🔴 Red = Aggressive | 🔵 Blue = Defensive")
    print("Switching control every 100 steps\n")
    
    try:
        while True:
            current_adapter.update_state(obs)
            
            action_idx, drone_cmd = current_adapter.get_action()
            action_name = DroneAction(action_idx).name
            
            obs, reward, terminated, truncated, info = env.step(drone_cmd)
            current_adapter.tick(0.02)
            
            step += 1
            
            # Switch every 100 steps
            if step % 100 == 0:
                team = "🔴 RED" if current_adapter.team == "red" else "🔵 BLUE"
                print(f"Step {step:4d} | {team} | Last action: {action_name}")
                current_adapter, other_adapter = other_adapter, current_adapter
                print(f"         Switching to {'🔴 RED' if current_adapter.team == 'red' else '🔵 BLUE'}")
            
            if terminated or truncated:
                obs, info = env.reset()
                step = 0
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    finally:
        env.close()


def demo_formation():
    """Demo: Formation flying concept."""
    print("\n" + "="*60)
    print("🛸🛸🛸 FORMATION DEMO")
    print("="*60)
    print("Cooperative organisms trying to maintain formation")
    print("\nPress Ctrl+C to stop\n")
    
    from reality_simulator.arena.drone_adapter import OrganismDroneAdapter, DroneAction
    
    # Create cooperative organism
    org = create_mock_organism("wingman", strategy="cooperative")
    adapter = OrganismDroneAdapter(org, drone_id=0, team="blue")
    
    # Set ally positions (formation targets)
    adapter.state.allies_positions = [
        np.array([2.0, 2.0, 2.0]),
        np.array([-2.0, 2.0, 2.0]),
    ]
    
    env = gymnasium.make("PyFlyt/QuadX-Hover-v4", render_mode="human")
    obs, info = env.reset()
    adapter.update_state(obs)
    
    step = 0
    
    try:
        while True:
            action_idx, drone_cmd = adapter.get_action()
            action_name = DroneAction(action_idx).name
            
            obs, reward, terminated, truncated, info = env.step(drone_cmd)
            adapter.update_state(obs)
            adapter.tick(0.02)
            
            step += 1
            
            if step % 100 == 0:
                ally_dist = adapter.state.nearest_ally_distance
                print(f"Step {step:4d} | Action: {action_name:10s} | Ally dist: {ally_dist:.2f}m")
            
            if terminated or truncated:
                obs, info = env.reset()
                adapter.update_state(obs)
                step = 0
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    finally:
        env.close()


def list_available_envs():
    """List all available PyFlyt environments."""
    print("\n📋 Available PyFlyt Environments:")
    print("-" * 40)
    
    pyflyt_envs = [
        ("PyFlyt/QuadX-Hover-v4", "Quadrotor hover stabilization"),
        ("PyFlyt/QuadX-Waypoints-v4", "Fly through waypoints"),
        ("PyFlyt/Rocket-Landing-v4", "SpaceX-style landing"),
        ("PyFlyt/Fixedwing-Waypoints-v4", "Fixed-wing aircraft"),
    ]
    
    for env_id, desc in pyflyt_envs:
        try:
            gymnasium.make(env_id)
            status = "✅"
        except:
            status = "❌"
        print(f"  {status} {env_id}: {desc}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="🛸 Drone Visual Demo")
    parser.add_argument("--battle", action="store_true", help="1v1 dogfight demo")
    parser.add_argument("--race", action="store_true", help="Racing demo")
    parser.add_argument("--formation", action="store_true", help="Formation flying demo")
    parser.add_argument("--list", action="store_true", help="List available environments")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_envs()
    elif args.battle:
        demo_battle()
    elif args.race:
        demo_racing()
    elif args.formation:
        demo_formation()
    else:
        demo_single_drone()


if __name__ == "__main__":
    main()
