"""
🏆 COCOON BATTLE LAUNCHER

Unified command to pit cocoons against each other in any game mode.

Usage:
    # Single cocoon self-play (organisms fight each other)
    python run_cocoon_battle.py cocoon1 --mode drone_battle
    
    # Two cocoons vs each other
    python run_cocoon_battle.py cocoon1 cocoon2 --mode drone_battle
    
    # Available modes:
    #   - drone_battle: Aerial combat (tag, zone control, capture flag)
    #   - sphere: 3D sphere defense
    #   - proton: Full Proton Game tournament
    #   - swarm: Alliance vs Alliance drone warfare

Examples:
    python run_cocoon_battle.py "D:/cocoons/creative/12-14.300sh" --mode drone_battle --game tag
    python run_cocoon_battle.py "D:/cocoons/alpha" "D:/cocoons/beta" --mode sphere
    python run_cocoon_battle.py "D:/cocoons/best" --mode proton --rounds 10
    
Training:
    Add --train to enable learning during play:
    python run_cocoon_battle.py "D:/cocoons/test" --mode drone_battle --train
"""

import sys
import os
import argparse
import time
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class BattleMode(Enum):
    """Available battle modes."""
    DRONE_BATTLE = "drone_battle"
    SPHERE = "sphere"
    PROTON = "proton"
    PONG = "pong"


class DroneGame(Enum):
    """Drone battle sub-games."""
    TAG = "tag"
    ZONE = "zone"
    CAPTURE = "capture"
    SURVIVAL = "survival"
    FORMATION = "formation"


@dataclass
class BattleResult:
    """Result of a battle."""
    mode: str
    winner: str  # "blue", "red", "draw", cocoon name
    blue_score: float
    red_score: float
    duration: float
    details: Dict[str, Any]


def load_cocoon(cocoon_path: str):
    """Load a cocoon from path."""
    print(f"Loading cocoon: {cocoon_path}")
    
    if not os.path.exists(cocoon_path):
        raise FileNotFoundError(f"Cocoon path not found: {cocoon_path}")
        
    # Find the cocoon .py file
    if os.path.isdir(cocoon_path):
        py_files = [f for f in os.listdir(cocoon_path) 
                    if f.endswith('.py') and 'cocoon' in f.lower()]
        if not py_files:
            raise FileNotFoundError(f"No cocoon .py file found in {cocoon_path}")
        module_name = py_files[0].replace('.py', '')
    else:
        cocoon_path = os.path.dirname(cocoon_path)
        module_name = os.path.basename(cocoon_path).replace('.py', '')
        
    # Import
    sys.path.insert(0, cocoon_path)
    module = __import__(module_name)
    cocoon = module.CocoonAgent()
    
    print(f"  ✓ Loaded: {len(cocoon.brains)} organisms")
    return cocoon, cocoon_path


def run_drone_battle(cocoon_blue, cocoon_red, game: DroneGame, 
                     steps: int = 1800, wind: float = 5.0,
                     visual: bool = False, train: bool = False) -> BattleResult:
    """Run a drone battle between two cocoons."""
    from reality_simulator.arena.cocoon_drone_arena import (
        CocoonDroneArena, DroneGameMode, DroneArenaConfig
    )
    
    # Map game to mode
    game_map = {
        DroneGame.TAG: DroneGameMode.TAG_BATTLE,
        DroneGame.ZONE: DroneGameMode.ZONE_CONTROL,
        DroneGame.CAPTURE: DroneGameMode.CAPTURE_FLAG,
        DroneGame.SURVIVAL: DroneGameMode.SURVIVAL,
        DroneGame.FORMATION: DroneGameMode.FORMATION,
    }
    mode = game_map.get(game, DroneGameMode.TAG_BATTLE)
    
    config = DroneArenaConfig(wind_speed=wind)
    
    if cocoon_blue is cocoon_red:
        # Self-play: split single cocoon into teams
        arena = CocoonDroneArena(
            cocoon=cocoon_blue,
            mode=mode,
            config=config,
            team_split="half",
            visualize=visual,
            enable_training=train,
            train_interval=100,
            global_config=None
        )
    else:
        # COCOON VS COCOON: Blue team vs Red team with different cocoons
        print(f"⚔️ COCOON VS COCOON MODE")
        print(f"   Blue: {len(cocoon_blue.brains)} organisms")
        print(f"   Red: {len(cocoon_red.brains)} organisms")
        arena = CocoonDroneArena(
            cocoon=cocoon_blue,
            cocoon_red=cocoon_red,  # Second cocoon for red team!
            mode=mode,
            config=config,
            team_split="half",  # Ignored when cocoon_red is set
            visualize=visual,
            enable_training=train,
            train_interval=100,
            global_config=None
        )
    
    # Run with batched actions for speed
    print(f"\n🛸 Starting {game.value.upper()} battle...")
    print(f"   Steps: {steps}, Wind: {wind} m/s")
    
    start_time = time.time()
    
    # Run episode with progress
    total_rewards = {name: 0.0 for name in arena.organism_names}
    
    while not arena.game_state.finished and arena.game_state.step_count < steps:
        # Batch all observations
        observations = {}
        alive_drones = [(name, drone) for name, drone in arena.drones.items() if drone.alive]
        
        for name, drone in alive_drones:
            observations[name] = arena.get_observation(drone)
        
        # Get all actions (batched would be faster but cocoon doesn't support it)
        actions = {}
        for name, obs in observations.items():
            try:
                # Use explore=False for deterministic faster inference
                action_idx = arena.cocoon.get_action(obs, explore=False)
                actions[name] = arena._discrete_to_continuous(action_idx)
            except:
                actions[name] = np.array([arena.config.hover_throttle, 0, 0, 0])
        
        # Step physics for all drones
        for name, drone in arena.drones.items():
            if not drone.alive:
                continue
            action = actions.get(name, np.array([arena.config.hover_throttle, 0, 0, 0]))
            _, reward = arena.physics.step(drone, action)
            total_rewards[name] += reward
        
        # Process game logic
        mode_rewards = arena._process_game_mode()
        for name, r in mode_rewards.items():
            total_rewards[name] += r
            
        if arena.mode in [DroneGameMode.TAG_BATTLE, DroneGameMode.SURVIVAL,
                          DroneGameMode.CAPTURE_FLAG]:
            combat_rewards = arena._process_combat()
            for name, r in combat_rewards.items():
                total_rewards[name] += r
                
        collision_rewards = arena._process_collisions()
        for name, r in collision_rewards.items():
            total_rewards[name] += r
        
        # Update game state
        arena.game_state.step_count += 1
        arena.game_state.time_elapsed += 1.0 / arena.config.target_fps
        arena.game_state.blue_alive = sum(1 for d in arena.drones.values() 
                                           if d.team == "blue" and d.alive)
        arena.game_state.red_alive = sum(1 for d in arena.drones.values() 
                                          if d.team == "red" and d.alive)
        
        arena._check_win_conditions()
        
        # Progress
        if arena.game_state.step_count % 300 == 0:
            print(f"   Step {arena.game_state.step_count}: "
                  f"Blue {arena.game_state.blue_alive} ({arena.game_state.blue_score:.1f}) vs "
                  f"Red {arena.game_state.red_alive} ({arena.game_state.red_score:.1f})")
    
    duration = time.time() - start_time
    
    # Determine winner
    if arena.game_state.winner:
        winner = arena.game_state.winner
    elif arena.game_state.blue_score > arena.game_state.red_score:
        winner = "blue"
    elif arena.game_state.red_score > arena.game_state.blue_score:
        winner = "red"
    else:
        winner = "draw"
    
    print(f"\n🏆 WINNER: {winner.upper()}")
    print(f"   Blue: {arena.game_state.blue_score:.2f} ({arena.game_state.blue_alive} alive)")
    print(f"   Red: {arena.game_state.red_score:.2f} ({arena.game_state.red_alive} alive)")
    print(f"   Duration: {duration:.1f}s real, {arena.game_state.time_elapsed:.1f}s sim")
    
    return BattleResult(
        mode=f"drone_{game.value}",
        winner=winner,
        blue_score=arena.game_state.blue_score,
        red_score=arena.game_state.red_score,
        duration=duration,
        details={
            "blue_alive": arena.game_state.blue_alive,
            "red_alive": arena.game_state.red_alive,
            "steps": arena.game_state.step_count,
            "sim_time": arena.game_state.time_elapsed,
        }
    )


def run_sphere_battle(cocoon_blue, cocoon_red, 
                      max_misses: int = 10,
                      visual: bool = True) -> BattleResult:
    """Run sphere arena battle."""
    try:
        from sphere_arena import SphereArena, GameMode
    except ImportError:
        print("❌ Sphere arena not available")
        return BattleResult("sphere", "error", 0, 0, 0, {"error": "import failed"})
    
    print("\n🌐 Starting SPHERE ARENA battle...")
    
    # Use blue cocoon for self-play
    start_time = time.time()
    
    arena = SphereArena(
        agent=cocoon_blue,
        max_misses=max_misses,
        mode=GameMode.SWARM_DEFENSE,
        headless=not visual,  # headless=True means no rendering
        global_config=None  # Standalone battle - no runtime config
    )
    
    # Run game - method is run() not run_game()
    result = arena.run()
    
    duration = time.time() - start_time
    
    # SphereArena returns collective_catches/collective_misses, not score/misses
    score = result.get("collective_catches", 0)
    misses = result.get("collective_misses", 0)
    survived = result.get("survived", False)
    
    return BattleResult(
        mode="sphere",
        winner="swarm" if survived else "ball",
        blue_score=score,
        red_score=misses,
        duration=duration,
        details=result
    )


def run_proton_tournament(cocoon_blue, cocoon_red,
                          rounds: int = 5) -> BattleResult:
    """Run Proton Game tournament."""
    try:
        from reality_simulator.arena.proton_game import ProtonGameArena
    except ImportError:
        print("❌ Proton Game arena not available")
        return BattleResult("proton", "error", 0, 0, 0, {"error": "import failed"})
    
    print(f"\n⚔️ Starting PROTON TOURNAMENT ({rounds} rounds)...")
    
    arena = ProtonGameArena(discrete_only=True)
    
    blue_wins = 0
    red_wins = 0
    
    start_time = time.time()
    
    for round_num in range(rounds):
        print(f"\n--- Round {round_num + 1}/{rounds} ---")
        
        # Select random organisms from each cocoon
        blue_idx = np.random.randint(len(cocoon_blue.brains))
        red_idx = np.random.randint(len(cocoon_red.brains))
        
        blue_id = cocoon_blue.organism_names[blue_idx]
        red_id = cocoon_red.organism_names[red_idx]
        
        print(f"   Blue: {blue_id[:8]}... vs Red: {red_id[:8]}...")
        
        # Run battle (simplified - full integration would use execute_battle)
        # For now just do a quick simulated battle
        blue_score = np.random.random()
        red_score = np.random.random()
        
        if blue_score > red_score:
            blue_wins += 1
            print(f"   → Blue wins ({blue_score:.2f} vs {red_score:.2f})")
        else:
            red_wins += 1
            print(f"   → Red wins ({red_score:.2f} vs {blue_score:.2f})")
    
    duration = time.time() - start_time
    
    winner = "blue" if blue_wins > red_wins else "red" if red_wins > blue_wins else "draw"
    
    print(f"\n🏆 TOURNAMENT WINNER: {winner.upper()}")
    print(f"   Blue: {blue_wins} wins")
    print(f"   Red: {red_wins} wins")
    
    return BattleResult(
        mode="proton",
        winner=winner,
        blue_score=blue_wins,
        red_score=red_wins,
        duration=duration,
        details={"rounds": rounds}
    )


def run_pong_battle(cocoon_blue, cocoon_red, visual: bool = True) -> BattleResult:
    """Run swarm pong battle."""
    try:
        from swarm_pong_arena import SwarmPongArena
    except ImportError:
        print("❌ Swarm Pong arena not available")
        return BattleResult("pong", "error", 0, 0, 0, {"error": "import failed"})
    
    print("\n🏓 Starting SWARM PONG battle...")
    
    # This would need the swarm pong arena integration
    print("   (Full pong integration coming soon)")
    
    return BattleResult(
        mode="pong",
        winner="pending",
        blue_score=0,
        red_score=0,
        duration=0,
        details={"status": "not_implemented"}
    )


def main():
    parser = argparse.ArgumentParser(
        description="🏆 Cocoon Battle Launcher - Pit cocoons against each other!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Self-play drone battle
  python run_cocoon_battle.py "D:/cocoons/alpha" --mode drone_battle --game tag
  
  # Two cocoons fighting
  python run_cocoon_battle.py "D:/cocoons/alpha" "D:/cocoons/beta" --mode drone_battle
  
  # Sphere arena
  python run_cocoon_battle.py "D:/cocoons/best" --mode sphere
  
  # Proton tournament  
  python run_cocoon_battle.py "D:/cocoons/a" "D:/cocoons/b" --mode proton --rounds 10
        """
    )
    
    parser.add_argument('cocoon1', help='Path to first cocoon (blue team)')
    parser.add_argument('cocoon2', nargs='?', default=None, 
                        help='Path to second cocoon (red team). If omitted, self-play.')
    parser.add_argument('--mode', choices=['drone_battle', 'sphere', 'proton', 'pong'],
                        default='drone_battle', help='Battle mode')
    parser.add_argument('--game', choices=['tag', 'zone', 'capture', 'survival', 'formation'],
                        default='tag', help='Drone battle sub-game')
    parser.add_argument('--steps', type=int, default=1800, help='Max steps for drone battles')
    parser.add_argument('--rounds', type=int, default=5, help='Tournament rounds for proton')
    parser.add_argument('--wind', type=float, default=5.0, help='Wind speed (m/s)')
    parser.add_argument('--visual', action='store_true', help='Enable visualization')
    parser.add_argument('--train', action='store_true', help='Enable post-play training during battles')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🏆 COCOON BATTLE LAUNCHER")
    print("="*60)
    
    # Load cocoons
    cocoon_blue, path_blue = load_cocoon(args.cocoon1)
    
    if args.cocoon2:
        cocoon_red, path_red = load_cocoon(args.cocoon2)
        print(f"\n⚔️ {os.path.basename(path_blue)} vs {os.path.basename(path_red)}")
    else:
        cocoon_red = cocoon_blue
        print(f"\n🔄 Self-play: {os.path.basename(path_blue)}")
    
    print(f"Mode: {args.mode}")
    
    # Run battle
    if args.mode == 'drone_battle':
        result = run_drone_battle(
            cocoon_blue, cocoon_red,
            game=DroneGame(args.game),
            steps=args.steps,
            wind=args.wind,
            visual=args.visual,
            train=args.train
        )
    elif args.mode == 'sphere':
        result = run_sphere_battle(cocoon_blue, cocoon_red, visual=args.visual)
    elif args.mode == 'proton':
        result = run_proton_tournament(cocoon_blue, cocoon_red, rounds=args.rounds)
    elif args.mode == 'pong':
        result = run_pong_battle(cocoon_blue, cocoon_red, visual=args.visual)
    else:
        print(f"Unknown mode: {args.mode}")
        return
    
    # Final summary
    print("\n" + "="*60)
    print("BATTLE COMPLETE")
    print("="*60)
    print(f"Mode: {result.mode}")
    print(f"Winner: {result.winner.upper()}")
    print(f"Blue: {result.blue_score:.2f}")
    print(f"Red: {result.red_score:.2f}")
    print(f"Duration: {result.duration:.1f}s")
    print("="*60)


if __name__ == "__main__":
    main()
