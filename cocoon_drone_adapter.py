#!/usr/bin/env python3
"""
🛸 COCOON DRONE ADAPTER - Fly Drones with Exported Butterfly Cocoons

This adapter bridges your exported cocoon organisms to the NASA JSBSim-grade
drone simulation arena. Your Highlander-trained warriors can now fly!

ALL 8 GAME MODES:
    FREE_FLY       - Basic flight training
    FORMATION      - Swarm coordination (team)
    PURSUIT        - Chase moving targets
    TAG_BATTLE     - Combat: tag enemies, avoid being tagged
    ZONE_CONTROL   - Control airspace zones
    CAPTURE_FLAG   - Team objective game
    SURVIVAL       - Last drone flying wins
    ESCORT         - Protect VIP drone

SETUP OPTIONS:

Option A - Same folder as cocoon.py:
    your_export_folder/
    ├── cocoon.py                  ← Your exported agent
    └── cocoon_drone_adapter.py    ← This file
    
Option B - Import the cocoon directly:
    from your_export_folder.cocoon import CocoonAgent
    from cocoon_drone_adapter import fly_drones, DroneArenaRunner

USAGE:
    python cocoon_drone_adapter.py                    # Interactive mode picker
    python cocoon_drone_adapter.py --mode tag_battle  # Specific mode
    python cocoon_drone_adapter.py --mode survival --time 180  # 3 min survival
    python cocoon_drone_adapter.py --all              # Run all modes sequentially
    python cocoon_drone_adapter.py --visual           # With 3D visualization (requires PyFlyt)

REQUIREMENTS:
    - numpy, torch (bundled in cocoon.py)
    - matplotlib (for trajectory plots)
    - PyFlyt (optional, for 3D visualization: pip install PyFlyt)

Author: The Butterfly System / Convergence Engine
"""

import sys
import os
import time
import argparse
import json
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS - Try local cocoon first, then from package
# ═══════════════════════════════════════════════════════════════════════════════

COCOON_AVAILABLE = False
CocoonAgent = None

def _load_cocoon():
    """Try to load cocoon from various locations."""
    global COCOON_AVAILABLE, CocoonAgent
    
    # Try 1: Local cocoon.py in same directory
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from cocoon import CocoonAgent as CA
        CocoonAgent = CA
        COCOON_AVAILABLE = True
        print("✅ Loaded cocoon from local cocoon.py")
        return True
    except ImportError:
        pass
    
    # Try 2: Find any cocoon_ensemble_*.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(current_dir):
        if f.startswith('cocoon_ensemble_') and f.endswith('.py'):
            try:
                module_name = f[:-3]
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(current_dir, f))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                CocoonAgent = module.CocoonAgent
                COCOON_AVAILABLE = True
                print(f"✅ Loaded cocoon from {f}")
                return True
            except:
                continue
    
    # Try 3: From reality_simulator (development mode)
    try:
        from reality_simulator.agent_compiler import compile_cocoon_agent
        print("⚠️ No cocoon.py found - will use compile_cocoon_agent for development")
        COCOON_AVAILABLE = "compile"
        return True
    except ImportError:
        pass
    
    print("❌ No cocoon found. Export one first with: python butterfly_system.py --export")
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# DRONE ARENA INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Try to import drone arena from various locations
ARENA_AVAILABLE = False
JSBSIM_PHYSICS_AVAILABLE = False

def _try_local_arena_import():
    """Try to import from local cocoon_drone_arena.py (from --unpack)."""
    global ARENA_AVAILABLE, JSBSIM_PHYSICS_AVAILABLE
    local_dir = os.path.dirname(os.path.abspath(__file__))
    arena_path = os.path.join(local_dir, 'cocoon_drone_arena.py')
    
    if os.path.exists(arena_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('cocoon_drone_arena', arena_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Import to global namespace
            globals()['CocoonDroneArena'] = module.CocoonDroneArena
            globals()['DroneArenaConfig'] = module.DroneArenaConfig
            globals()['DroneGameMode'] = module.DroneGameMode
            globals()['DronePhysics'] = module.DronePhysics
            globals()['DroneState'] = module.DroneState
            globals()['GameState'] = module.GameState
            JSBSIM_PHYSICS_AVAILABLE = getattr(module, 'JSBSIM_PHYSICS_AVAILABLE', False)
            ARENA_AVAILABLE = True
            print("✅ Loaded drone arena from local cocoon_drone_arena.py")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load local arena: {e}")
    return False

def _try_package_arena_import():
    """Try to import from reality_simulator package."""
    global ARENA_AVAILABLE, JSBSIM_PHYSICS_AVAILABLE
    try:
        from reality_simulator.arena.cocoon_drone_arena import (
            CocoonDroneArena, DroneArenaConfig, DroneGameMode, 
            DronePhysics, DroneState, GameState, JSBSIM_PHYSICS_AVAILABLE as JSB
        )
        globals()['CocoonDroneArena'] = CocoonDroneArena
        globals()['DroneArenaConfig'] = DroneArenaConfig
        globals()['DroneGameMode'] = DroneGameMode
        globals()['DronePhysics'] = DronePhysics
        globals()['DroneState'] = DroneState
        globals()['GameState'] = GameState
        JSBSIM_PHYSICS_AVAILABLE = JSB
        ARENA_AVAILABLE = True
        print("✅ Loaded drone arena from reality_simulator package")
        return True
    except ImportError:
        pass
    
    # Try relative import (one dir up)
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from reality_simulator.arena.cocoon_drone_arena import (
            CocoonDroneArena, DroneArenaConfig, DroneGameMode,
            DronePhysics, DroneState, GameState, JSBSIM_PHYSICS_AVAILABLE as JSB
        )
        globals()['CocoonDroneArena'] = CocoonDroneArena
        globals()['DroneArenaConfig'] = DroneArenaConfig
        globals()['DroneGameMode'] = DroneGameMode
        globals()['DronePhysics'] = DronePhysics
        globals()['DroneState'] = DroneState
        globals()['GameState'] = GameState
        JSBSIM_PHYSICS_AVAILABLE = JSB
        ARENA_AVAILABLE = True
        return True
    except ImportError:
        pass
    
    return False

# Try local first (standalone mode from --unpack), then package
if not _try_local_arena_import():
    if not _try_package_arena_import():
        print("⚠️ Drone arena not available - running in standalone mode")


# Visualization backends
MATPLOTLIB_AVAILABLE = False
PYFLYT_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass

try:
    import gymnasium
    import PyFlyt.gym_envs
    PYFLYT_AVAILABLE = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# GAME MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

GAME_MODES = {
    'free_fly': {
        'name': 'Free Fly',
        'description': 'Basic flight training - learn to hover, maneuver, land',
        'emoji': '🕊️',
        'team_game': False,
        'default_time': 60,
    },
    'formation': {
        'name': 'Formation',
        'description': 'Maintain swarm formation - team coordination',
        'emoji': '🔷',
        'team_game': True,
        'default_time': 90,
    },
    'pursuit': {
        'name': 'Pursuit',
        'description': 'Chase and intercept moving targets',
        'emoji': '🎯',
        'team_game': False,
        'default_time': 60,
    },
    'tag_battle': {
        'name': 'Tag Battle',
        'description': 'Combat: tag enemies, evade being tagged',
        'emoji': '⚔️',
        'team_game': True,
        'default_time': 120,
    },
    'zone_control': {
        'name': 'Zone Control',
        'description': 'Control airspace zones - team territory',
        'emoji': '🏰',
        'team_game': True,
        'default_time': 120,
    },
    'capture_flag': {
        'name': 'Capture the Flag',
        'description': 'Team objective - capture enemy flag',
        'emoji': '🚩',
        'team_game': True,
        'default_time': 180,
    },
    'survival': {
        'name': 'Survival',
        'description': 'Last drone flying wins - free for all',
        'emoji': '💀',
        'team_game': False,
        'default_time': 180,
    },
    'escort': {
        'name': 'Escort',
        'description': 'Protect VIP drone from enemies',
        'emoji': '🛡️',
        'team_game': True,
        'default_time': 120,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DRONE ARENA RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DroneRunResult:
    """Results from running a drone arena session."""
    mode: str
    duration: float
    total_steps: int
    blue_wins: int = 0
    red_wins: int = 0
    draws: int = 0
    total_reward: float = 0.0
    survivors: int = 0
    trajectories: Dict[str, List[np.ndarray]] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


class DroneArenaRunner:
    """
    Runs cocoon organisms in the drone arena.
    
    Handles:
    - Arena setup for each game mode
    - Cocoon-to-drone action mapping
    - Trajectory recording for visualization
    - Results aggregation
    """
    
    def __init__(self, cocoon_agent, num_drones: int = 8, visualize: bool = False):
        """
        Args:
            cocoon_agent: Loaded CocoonAgent instance
            num_drones: Number of drones (splits into 2 teams for team games)
            visualize: Enable real-time 3D visualization
        """
        self.cocoon = cocoon_agent
        self.num_drones = num_drones
        self.visualize = visualize and PYFLYT_AVAILABLE
        
        # Boost exploration for drone mode - cocoon needs to learn new domain
        if hasattr(cocoon_agent, 'epsilon'):
            cocoon_agent.epsilon = 0.5  # 50% random exploration to try different actions
            print(f"   🎲 Epsilon boosted to 0.5 for drone exploration")
        
        # Ensure cocoon has enough organisms
        if hasattr(cocoon_agent, 'brains'):
            available = len(cocoon_agent.brains)
            if available < num_drones:
                print(f"⚠️ Cocoon has {available} organisms, requested {num_drones}. Using {available}.")
                self.num_drones = available
        
        # Default config - using 10 FPS for faster simulation
        # (ensemble voting takes ~20ms per drone, so 60 FPS is too slow)
        self.config = DroneArenaConfig(
            arena_size=100.0,
            max_episode_steps=500,  # ~50 seconds at 10 FPS
            target_fps=10,  # Reduced from 60 - ensemble inference is slow
        ) if ARENA_AVAILABLE else None
        
        print(f"🛸 DroneArenaRunner initialized")
        print(f"   Organisms: {self.num_drones}")
        print(f"   Physics: {'NASA JSBSim' if JSBSIM_PHYSICS_AVAILABLE else 'Simplified'}")
        print(f"   Visualization: {'PyFlyt 3D' if self.visualize else 'Matplotlib trajectories'}")
    
    def run_mode(self, mode: str, duration_seconds: float = None, 
                 record_trajectories: bool = True) -> DroneRunResult:
        """
        Run a specific game mode for a duration.
        
        Args:
            mode: Game mode name (e.g., 'tag_battle', 'survival')
            duration_seconds: How long to run (uses mode default if None)
            record_trajectories: Record drone positions for plotting
            
        Returns:
            DroneRunResult with statistics
        """
        if not ARENA_AVAILABLE:
            print(f"❌ Arena not available - cannot run {mode}")
            return DroneRunResult(mode=mode, duration=0, total_steps=0)
        
        mode_info = GAME_MODES.get(mode.lower())
        if not mode_info:
            print(f"❌ Unknown mode: {mode}")
            return DroneRunResult(mode=mode, duration=0, total_steps=0)
        
        duration = duration_seconds or mode_info['default_time']
        
        print(f"\n{'='*60}")
        print(f"{mode_info['emoji']} {mode_info['name'].upper()}")
        print(f"{'='*60}")
        print(f"Description: {mode_info['description']}")
        print(f"Duration: {duration}s | Team game: {mode_info['team_game']}")
        print()
        
        # Map mode name to enum
        mode_enum = DroneGameMode[mode.upper()]
        
        # Create arena
        arena = CocoonDroneArena(
            cocoon=self.cocoon,
            mode=mode_enum,
            config=self.config,
            team_split="half" if mode_info['team_game'] else "all_blue",
            visualize=self.visualize,
            verbose=False,  # Less verbose for cleaner output
            enable_training=True,  # Let cocoon learn from drone experience!
            train_interval=10  # Train every 10 steps
        )
        
        # Run simulation
        start_time = time.time()
        target_steps = int(duration * self.config.target_fps)
        
        trajectories = {name: [] for name in arena.drones.keys()}
        events = []
        total_reward = 0.0
        step = 0
        
        print(f"Running {target_steps} steps ({duration}s at {self.config.target_fps} FPS)...")
        print()
        
        try:
            while step < target_steps and not arena.game_state.finished:
                # Step physics
                rewards = arena.step()
                total_reward += sum(rewards.values())
                
                # Record trajectories
                if record_trajectories and step % 10 == 0:  # Every 10th frame
                    for name, drone in arena.drones.items():
                        if drone.alive:
                            trajectories[name].append(drone.position.copy())
                
                # Progress display
                if step % 600 == 0:  # Every 10 seconds
                    elapsed = time.time() - start_time
                    alive = sum(1 for d in arena.drones.values() if d.alive)
                    blue = arena.game_state.blue_alive
                    red = arena.game_state.red_alive
                    print(f"  [{elapsed:5.1f}s] Step {step:5d} | "
                          f"Blue: {blue} | Red: {red} | "
                          f"Reward: {total_reward:.1f}")
                
                step += 1
                
        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")
        
        elapsed = time.time() - start_time
        
        # Determine winner
        gs = arena.game_state
        blue_wins = 1 if gs.winner == "blue" else 0
        red_wins = 1 if gs.winner == "red" else 0
        draws = 1 if gs.winner == "draw" or gs.winner is None else 0
        survivors = sum(1 for d in arena.drones.values() if d.alive)
        
        # Convert trajectories to arrays
        traj_arrays = {
            name: np.array(pts) if pts else np.array([]).reshape(0, 3)
            for name, pts in trajectories.items()
        }
        
        result = DroneRunResult(
            mode=mode,
            duration=elapsed,
            total_steps=step,
            blue_wins=blue_wins,
            red_wins=red_wins,
            draws=draws,
            total_reward=total_reward,
            survivors=survivors,
            trajectories=traj_arrays,
            events=events
        )
        
        # Print summary
        print()
        print(f"{'='*60}")
        print(f"RESULTS: {mode_info['name']}")
        print(f"{'='*60}")
        print(f"  Duration: {elapsed:.1f}s ({step} steps)")
        print(f"  Survivors: {survivors}/{self.num_drones}")
        print(f"  Total Reward: {total_reward:.2f}")
        if mode_info['team_game']:
            print(f"  Winner: {gs.winner or 'None (ongoing)'}")
            print(f"  Blue alive: {gs.blue_alive} | Red alive: {gs.red_alive}")
        
        return result
    
    def run_all_modes(self, duration_per_mode: float = 60) -> List[DroneRunResult]:
        """Run all 8 game modes sequentially."""
        results = []
        
        print("\n" + "="*60)
        print("🛸 RUNNING ALL DRONE GAME MODES")
        print("="*60)
        
        for mode_key in GAME_MODES.keys():
            result = self.run_mode(mode_key, duration_seconds=duration_per_mode)
            results.append(result)
            print()
        
        # Summary
        print("\n" + "="*60)
        print("📊 ALL MODES SUMMARY")
        print("="*60)
        
        for r in results:
            mode_info = GAME_MODES[r.mode]
            status = "✅" if r.total_steps > 0 else "❌"
            print(f"  {status} {mode_info['emoji']} {mode_info['name']:15} | "
                  f"{r.duration:5.1f}s | Survivors: {r.survivors} | Reward: {r.total_reward:.1f}")
        
        return results
    
    def plot_trajectories(self, result: DroneRunResult, save_path: str = None):
        """Plot drone trajectories from a run."""
        if not MATPLOTLIB_AVAILABLE:
            print("❌ Matplotlib not available for plotting")
            return
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        mode_info = GAME_MODES.get(result.mode, {})
        
        colors = {'blue': 'blue', 'red': 'red'}
        
        for drone_name, trajectory in result.trajectories.items():
            if len(trajectory) == 0:
                continue
            
            # Determine team color
            team = 'blue' if 'org_0' <= drone_name <= 'org_3' else 'red'
            color = colors.get(team, 'gray')
            
            ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                    color=color, alpha=0.7, linewidth=1.5, label=drone_name)
            
            # Start/end markers
            ax.scatter(*trajectory[0], color='green', s=50, marker='o')
            ax.scatter(*trajectory[-1], color=color, s=50, marker='x')
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Altitude (m)')
        ax.set_title(f"{mode_info.get('emoji', '🛸')} {mode_info.get('name', result.mode)} - "
                     f"Drone Trajectories ({result.duration:.0f}s)")
        
        # Ground plane
        arena_half = self.config.arena_size / 2 if self.config else 50
        xx, yy = np.meshgrid(
            np.linspace(-arena_half, arena_half, 10),
            np.linspace(-arena_half, arena_half, 10)
        )
        ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.1, color='green')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"📊 Saved trajectory plot: {save_path}")
        else:
            plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════════════

def fly_drones(cocoon_agent=None, mode: str = 'tag_battle', 
               duration: float = None, visualize: bool = False,
               num_drones: int = 8, plot: bool = True) -> DroneRunResult:
    """
    Convenient function to fly drones with a cocoon.
    
    Args:
        cocoon_agent: CocoonAgent instance (loads from cocoon.py if None)
        mode: Game mode to run
        duration: Duration in seconds (uses mode default if None)
        visualize: Enable 3D visualization
        num_drones: Number of drones
        plot: Show trajectory plot after
        
    Returns:
        DroneRunResult
    """
    # Load cocoon if needed
    if cocoon_agent is None:
        _load_cocoon()
        if not COCOON_AVAILABLE:
            raise RuntimeError("No cocoon available")
        cocoon_agent = CocoonAgent()
    
    runner = DroneArenaRunner(cocoon_agent, num_drones=num_drones, visualize=visualize)
    result = runner.run_mode(mode, duration_seconds=duration)
    
    if plot and MATPLOTLIB_AVAILABLE:
        runner.plot_trajectories(result)
    
    return result


def interactive_mode():
    """Interactive mode picker."""
    _load_cocoon()
    
    if not COCOON_AVAILABLE:
        print("\n❌ No cocoon found. Options:")
        print("   1. Export a cocoon: python butterfly_system.py --export")
        print("   2. Put cocoon.py in this folder")
        return
    
    print("\n" + "="*60)
    print("🛸 COCOON DRONE ARENA - Mode Selection")
    print("="*60)
    print()
    
    for i, (key, info) in enumerate(GAME_MODES.items(), 1):
        print(f"  {i}. {info['emoji']} {info['name']:15} - {info['description']}")
    
    print()
    print("  9. Run ALL modes (60s each)")
    print("  0. Exit")
    print()
    
    try:
        choice = input("Select mode (1-8, 9=all, 0=exit): ").strip()
        
        if choice == '0':
            return
        
        if choice == '9':
            cocoon = CocoonAgent()
            runner = DroneArenaRunner(cocoon)
            runner.run_all_modes(duration_per_mode=60)
            return
        
        mode_idx = int(choice) - 1
        if 0 <= mode_idx < len(GAME_MODES):
            mode_key = list(GAME_MODES.keys())[mode_idx]
            mode_info = GAME_MODES[mode_key]
            
            duration = input(f"Duration in seconds [{mode_info['default_time']}]: ").strip()
            duration = int(duration) if duration else mode_info['default_time']
            
            cocoon = CocoonAgent()
            result = fly_drones(cocoon, mode=mode_key, duration=duration)
            
        else:
            print("Invalid selection")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="🛸 Fly drones with your exported cocoon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python cocoon_drone_adapter.py                    # Interactive mode
    python cocoon_drone_adapter.py --mode survival    # Run survival mode
    python cocoon_drone_adapter.py --mode tag_battle --time 180  # 3 min battle
    python cocoon_drone_adapter.py --all              # All modes, 60s each
    python cocoon_drone_adapter.py --all --time 180   # All modes, 3 min each
        """
    )
    
    parser.add_argument('--mode', '-m', type=str, 
                        choices=list(GAME_MODES.keys()),
                        help='Game mode to run')
    parser.add_argument('--time', '-t', type=int, default=None,
                        help='Duration in seconds')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Run all game modes')
    parser.add_argument('--visual', '-v', action='store_true',
                        help='Enable 3D visualization (requires PyFlyt)')
    parser.add_argument('--drones', '-d', type=int, default=8,
                        help='Number of drones (default: 8)')
    parser.add_argument('--no-plot', action='store_true',
                        help='Skip trajectory plot')
    parser.add_argument('--save-plot', type=str, default=None,
                        help='Save trajectory plot to file')
    
    args = parser.parse_args()
    
    # Check dependencies
    print("🛸 COCOON DRONE ADAPTER")
    print("="*60)
    print(f"Arena: {'✅' if ARENA_AVAILABLE else '❌'}")
    print(f"JSBSim Physics: {'✅' if JSBSIM_PHYSICS_AVAILABLE else '⚠️ (using fallback)'}")
    print(f"Matplotlib: {'✅' if MATPLOTLIB_AVAILABLE else '❌'}")
    print(f"PyFlyt 3D: {'✅' if PYFLYT_AVAILABLE else '❌ (pip install PyFlyt)'}")
    
    if args.all:
        # Run all modes
        _load_cocoon()
        if not COCOON_AVAILABLE:
            print("❌ No cocoon available")
            return
        
        cocoon = CocoonAgent()
        runner = DroneArenaRunner(cocoon, num_drones=args.drones, visualize=args.visual)
        runner.run_all_modes(duration_per_mode=args.time or 60)
        
    elif args.mode:
        # Run specific mode
        _load_cocoon()
        if not COCOON_AVAILABLE:
            print("❌ No cocoon available")
            return
        
        cocoon = CocoonAgent()
        runner = DroneArenaRunner(cocoon, num_drones=args.drones, visualize=args.visual)
        result = runner.run_mode(args.mode, duration_seconds=args.time)
        
        if not args.no_plot and MATPLOTLIB_AVAILABLE:
            runner.plot_trajectories(result, save_path=args.save_plot)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
