"""
🥚🛸 COCOON-DRONE BRIDGE

Enables exported cocoons to control drones in realistic physics simulation.

A cocoon is a self-contained AI agent exported from Highlander training.
This bridge lets cocoons fly drones using their learned decision-making.

Usage:
    from reality_simulator.arena.cocoon_drone_bridge import CocoonDronePilot
    
    # Load your cocoon
    cocoon = CocoonAgent()  # From exported cocoon.py
    
    # Create a drone pilot
    pilot = CocoonDronePilot(cocoon, team="blue")
    
    # Run in physics simulation
    pilot.fly_mission(duration=30.0, visualize=True)
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import our physics engine
try:
    from .jsbsim_quadcopter import QuadcopterFDM, QuadcopterConfig, MultiQuadcopterEnv
    PHYSICS_AVAILABLE = True
except ImportError:
    PHYSICS_AVAILABLE = False
    logger.warning("QuadcopterFDM not available")

# Import drone adapter for action translation
try:
    from .drone_adapter import DroneAction, DroneState
    ADAPTER_AVAILABLE = True
except ImportError:
    ADAPTER_AVAILABLE = False


@dataclass
class CocoonDroneState:
    """State visible to cocoon for decision making."""
    # Position in arena (normalized to [-1, 1])
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    orientation: np.ndarray  # [roll, pitch, yaw]
    
    # Tactical info
    nearest_enemy_direction: np.ndarray  # Unit vector
    nearest_enemy_distance: float
    nearest_ally_direction: np.ndarray
    nearest_ally_distance: float
    
    # Status
    health: float
    battery: float
    altitude_danger: float  # 0=safe, 1=dangerous
    
    def to_observation(self) -> np.ndarray:
        """Convert to 28-dim observation for cocoon."""
        obs = np.zeros(28, dtype=np.float32)
        
        # Position (0-2)
        obs[0:3] = np.clip(self.position / 10.0, -1, 1)
        
        # Velocity (3-5)
        obs[3:6] = np.clip(self.velocity / 5.0, -1, 1)
        
        # Orientation (6-8)
        obs[6:9] = self.orientation / np.pi
        
        # Zeros for angular velocity (9-11)
        obs[9:12] = 0.0
        
        # Tactical (12-15)
        obs[12] = np.clip(self.nearest_ally_distance / 10.0, 0, 1)
        obs[13] = np.clip(self.nearest_enemy_distance / 10.0, 0, 1)
        obs[14] = 0.1  # Ally count placeholder
        obs[15] = 0.1  # Enemy count placeholder
        
        # Status (16-18)
        obs[16] = self.health
        obs[17] = 0.0  # Not tagged
        obs[18] = 0.0  # No cooldown
        
        # Directions (19-24)
        obs[19:22] = self.nearest_enemy_direction
        obs[22:25] = self.nearest_ally_direction
        
        # Altitude (25-27)
        obs[25] = np.clip(self.position[2] / 5.0, 0, 1)
        obs[26] = 1.0 if self.position[2] < 0.5 else 0.0
        obs[27] = 1.0 if self.position[2] > 9.0 else 0.0
        
        return obs


class CocoonDronePilot:
    """
    Wraps a cocoon to pilot a drone.
    
    The cocoon makes decisions (0-5 discrete actions).
    This class translates those to drone motor commands.
    """
    
    # Action to motor command mapping
    # Format: base_thrust, pitch_delta, roll_delta, yaw_delta
    ACTION_COMMANDS = {
        0: (0.55, 0.1, 0.0, 0.0),    # MOVE - forward thrust
        1: (0.50, 0.0, 0.0, 0.0),    # COOPERATE - hover/gentle
        2: (0.60, 0.15, 0.05, 0.0),  # COMPETE - aggressive
        3: (0.47, 0.0, 0.0, 0.0),    # REST - hover in place
        4: (0.45, 0.0, 0.0, 0.1),    # REPRODUCE - slow turn
        5: (0.55, 0.0, 0.1, 0.2),    # ISOLATE - evasive juke
    }
    
    def __init__(self, cocoon, team: str = "blue", drone_id: int = 0):
        """
        Args:
            cocoon: A CocoonAgent instance (from exported cocoon)
            team: "blue" or "red" for combat scenarios
            drone_id: Identifier for multi-drone scenarios
        """
        self.cocoon = cocoon
        self.team = team
        self.drone_id = drone_id
        
        # Physics
        self.fdm = QuadcopterFDM() if PHYSICS_AVAILABLE else None
        
        # State
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.health = 1.0
        self.alive = True
        
        # Stats
        self.flight_time = 0.0
        self.actions_taken = []
        self.distance_traveled = 0.0
        
        logger.info(f"🥚🛸 CocoonDronePilot created (team={team})")
    
    def get_cocoon_decision(self, state: CocoonDroneState) -> int:
        """Get action from cocoon based on current state."""
        obs = state.to_observation()
        
        # Cocoon returns discrete action 0-5
        action = self.cocoon.get_action(obs)
        
        return int(action)
    
    def action_to_motors(self, action: int) -> np.ndarray:
        """Convert discrete action to 4 motor commands."""
        base, pitch, roll, yaw = self.ACTION_COMMANDS.get(action, (0.47, 0, 0, 0))
        
        # Motor layout (X-config):
        #   1(CW)   2(CCW)
        #      \   /
        #       [+]
        #      /   \
        #   4(CCW)  3(CW)
        
        # Base hover
        motors = np.array([base, base, base, base])
        
        # Pitch adjustment (motors 1,2 vs 3,4)
        motors[0] += pitch
        motors[1] += pitch
        motors[2] -= pitch
        motors[3] -= pitch
        
        # Roll adjustment (motors 1,4 vs 2,3)
        motors[0] += roll
        motors[3] += roll
        motors[1] -= roll
        motors[2] -= roll
        
        # Yaw adjustment (CW vs CCW)
        motors[0] += yaw
        motors[2] += yaw
        motors[1] -= yaw
        motors[3] -= yaw
        
        return np.clip(motors, 0, 1)
    
    def step(self, dt: float = 0.01, 
             enemies: Optional[List[np.ndarray]] = None,
             allies: Optional[List[np.ndarray]] = None) -> Dict[str, Any]:
        """
        Execute one simulation step.
        
        Args:
            dt: Time step in seconds
            enemies: List of enemy positions
            allies: List of ally positions
            
        Returns:
            Dict with position, action, etc.
        """
        if not self.alive or self.fdm is None:
            return {'alive': False}
        
        # Build state for cocoon
        enemies = enemies or []
        allies = allies or []
        
        # Find nearest enemy
        if enemies:
            dists = [np.linalg.norm(e - self.position) for e in enemies]
            nearest_idx = np.argmin(dists)
            enemy_dir = enemies[nearest_idx] - self.position
            enemy_dist = dists[nearest_idx]
            if enemy_dist > 0:
                enemy_dir = enemy_dir / enemy_dist
        else:
            enemy_dir = np.array([1, 0, 0])
            enemy_dist = 100.0
        
        # Find nearest ally
        if allies:
            dists = [np.linalg.norm(a - self.position) for a in allies]
            nearest_idx = np.argmin(dists)
            ally_dir = allies[nearest_idx] - self.position
            ally_dist = dists[nearest_idx]
            if ally_dist > 0:
                ally_dir = ally_dir / ally_dist
        else:
            ally_dir = np.array([0, 1, 0])
            ally_dist = 100.0
        
        state = CocoonDroneState(
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            orientation=np.array([self.fdm.state.phi, self.fdm.state.theta, self.fdm.state.psi]),
            nearest_enemy_direction=enemy_dir,
            nearest_enemy_distance=enemy_dist,
            nearest_ally_direction=ally_dir,
            nearest_ally_distance=ally_dist,
            health=self.health,
            battery=self.fdm.state.battery_remaining,
            altitude_danger=1.0 if self.position[2] < 1.0 else 0.0
        )
        
        # Get cocoon's decision
        action = self.get_cocoon_decision(state)
        self.actions_taken.append(action)
        
        # Convert to motor commands
        motors = self.action_to_motors(action)
        
        # Step physics
        old_pos = self.position.copy()
        self.fdm.step(motors, dt=dt)
        
        # Update our state from physics
        self.position = np.array([self.fdm.state.x, self.fdm.state.y, self.fdm.state.z])
        self.velocity = np.array([self.fdm.state.u, self.fdm.state.v, self.fdm.state.w])
        
        # Track stats
        self.flight_time += dt
        self.distance_traveled += np.linalg.norm(self.position - old_pos)
        
        # Check for crash
        if self.position[2] < 0.1:
            self.alive = False
            logger.info(f"🛸💥 Drone {self.drone_id} crashed!")
        
        return {
            'alive': self.alive,
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'action': action,
            'motors': motors,
            'battery': self.fdm.state.battery_remaining
        }
    
    def fly_mission(self, duration: float = 10.0, 
                    visualize: bool = False,
                    wind: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Fly a solo mission for specified duration.
        
        Args:
            duration: Mission length in seconds
            visualize: If True, show ASCII visualization
            wind: Optional wind vector [wx, wy, wz]
            
        Returns:
            Mission statistics
        """
        if self.fdm is None:
            return {'error': 'No physics engine available'}
        
        # Initialize
        self.fdm.reset(position=np.array([0, 0, 5.0]))
        self.position = np.array([0, 0, 5.0])
        
        if wind is not None:
            self.fdm.set_wind(wind, turbulence=0.3)
        
        dt = 0.02  # 50 Hz
        steps = int(duration / dt)
        
        if visualize:
            print(f"\n🥚🛸 COCOON DRONE MISSION")
            print(f"Duration: {duration}s | Wind: {wind}")
            print("="*50)
        
        trajectory = []
        
        for step in range(steps):
            result = self.step(dt=dt)
            
            if not result.get('alive', True):
                break
            
            trajectory.append(result['position'].copy())
            
            if visualize and step % 50 == 0:  # Every second
                pos = result['position']
                action_names = ['MOVE', 'COOP', 'COMP', 'REST', 'REPR', 'ISOL']
                action_name = action_names[result['action']]
                print(f"t={step*dt:4.1f}s | pos=[{pos[0]:5.1f}, {pos[1]:5.1f}, {pos[2]:5.1f}] | "
                      f"action={action_name} | battery={result['battery']*100:4.0f}%")
        
        # Compile stats
        trajectory = np.array(trajectory)
        
        stats = {
            'flight_time': self.flight_time,
            'distance_traveled': self.distance_traveled,
            'final_position': self.position.tolist(),
            'final_battery': self.fdm.state.battery_remaining,
            'crashed': not self.alive,
            'actions_histogram': {
                'MOVE': self.actions_taken.count(0),
                'COOPERATE': self.actions_taken.count(1),
                'COMPETE': self.actions_taken.count(2),
                'REST': self.actions_taken.count(3),
                'REPRODUCE': self.actions_taken.count(4),
                'ISOLATE': self.actions_taken.count(5),
            },
            'max_altitude': float(trajectory[:, 2].max()) if len(trajectory) > 0 else 0,
            'min_altitude': float(trajectory[:, 2].min()) if len(trajectory) > 0 else 0,
        }
        
        if visualize:
            print("="*50)
            print(f"✅ Mission complete!")
            print(f"   Distance: {stats['distance_traveled']:.1f}m")
            print(f"   Battery: {stats['final_battery']*100:.0f}%")
            print(f"   Actions: {stats['actions_histogram']}")
        
        return stats


class CocoonSwarmBattle:
    """
    Run a battle between two teams of cocoon-controlled drones.
    """
    
    def __init__(self, 
                 blue_cocoons: List,
                 red_cocoons: List,
                 arena_size: float = 20.0):
        """
        Args:
            blue_cocoons: List of CocoonAgent instances for blue team
            red_cocoons: List of CocoonAgent instances for red team
            arena_size: Size of battle arena in meters
        """
        self.arena_size = arena_size
        
        # Create pilots
        self.blue_pilots = [
            CocoonDronePilot(c, team="blue", drone_id=i)
            for i, c in enumerate(blue_cocoons)
        ]
        self.red_pilots = [
            CocoonDronePilot(c, team="red", drone_id=i)
            for i, c in enumerate(red_cocoons)
        ]
        
        # Combat params
        self.tag_range = 2.0
        self.tag_damage = 0.25
        
        logger.info(f"⚔️ CocoonSwarmBattle: {len(blue_cocoons)} blue vs {len(red_cocoons)} red")
    
    def spawn_teams(self):
        """Spawn teams on opposite sides of arena."""
        # Blue on left side
        for i, pilot in enumerate(self.blue_pilots):
            x = -self.arena_size / 3
            y = (i - len(self.blue_pilots) / 2) * 3
            z = 5.0
            pilot.fdm.reset(position=np.array([x, y, z]))
            pilot.position = np.array([x, y, z])
            pilot.health = 1.0
            pilot.alive = True
        
        # Red on right side
        for i, pilot in enumerate(self.red_pilots):
            x = self.arena_size / 3
            y = (i - len(self.red_pilots) / 2) * 3
            z = 5.0
            pilot.fdm.reset(position=np.array([x, y, z]))
            pilot.position = np.array([x, y, z])
            pilot.health = 1.0
            pilot.alive = True
    
    def run_battle(self, duration: float = 30.0, 
                   visualize: bool = False) -> Dict[str, Any]:
        """
        Run the battle.
        
        Args:
            duration: Max battle time in seconds
            visualize: Show progress
            
        Returns:
            Battle results
        """
        self.spawn_teams()
        
        dt = 0.02
        steps = int(duration / dt)
        
        if visualize:
            print(f"\n⚔️ COCOON DRONE BATTLE")
            print(f"{len(self.blue_pilots)} BLUE vs {len(self.red_pilots)} RED")
            print("="*50)
        
        for step in range(steps):
            # Get positions
            blue_positions = [p.position for p in self.blue_pilots if p.alive]
            red_positions = [p.position for p in self.red_pilots if p.alive]
            
            # Step blue drones
            for pilot in self.blue_pilots:
                if pilot.alive:
                    pilot.step(dt=dt, enemies=red_positions, allies=blue_positions)
            
            # Step red drones
            for pilot in self.red_pilots:
                if pilot.alive:
                    pilot.step(dt=dt, enemies=blue_positions, allies=red_positions)
            
            # Check for tags (combat)
            self._process_combat()
            
            # Count survivors
            blue_alive = sum(1 for p in self.blue_pilots if p.alive)
            red_alive = sum(1 for p in self.red_pilots if p.alive)
            
            if visualize and step % 100 == 0:
                print(f"t={step*dt:4.1f}s | Blue: {blue_alive} alive | Red: {red_alive} alive")
            
            # Check for victory
            if blue_alive == 0 or red_alive == 0:
                break
        
        # Determine winner
        blue_alive = sum(1 for p in self.blue_pilots if p.alive)
        red_alive = sum(1 for p in self.red_pilots if p.alive)
        
        if blue_alive > red_alive:
            winner = "blue"
        elif red_alive > blue_alive:
            winner = "red"
        else:
            winner = "draw"
        
        results = {
            'winner': winner,
            'blue_survivors': blue_alive,
            'red_survivors': red_alive,
            'duration': step * dt,
            'blue_stats': [{'health': p.health, 'alive': p.alive} for p in self.blue_pilots],
            'red_stats': [{'health': p.health, 'alive': p.alive} for p in self.red_pilots],
        }
        
        if visualize:
            print("="*50)
            print(f"🏆 Winner: {winner.upper()}")
            print(f"   Blue survivors: {blue_alive}/{len(self.blue_pilots)}")
            print(f"   Red survivors: {red_alive}/{len(self.red_pilots)}")
        
        return results
    
    def _process_combat(self):
        """Check for tags between teams."""
        all_pilots = self.blue_pilots + self.red_pilots
        
        for attacker in all_pilots:
            if not attacker.alive:
                continue
            
            for defender in all_pilots:
                if not defender.alive:
                    continue
                if attacker.team == defender.team:
                    continue
                
                # Check range
                dist = np.linalg.norm(attacker.position - defender.position)
                if dist < self.tag_range:
                    # Tag!
                    defender.health -= self.tag_damage
                    if defender.health <= 0:
                        defender.alive = False
                        logger.info(f"💥 {attacker.team} drone eliminated {defender.team} drone!")


# Convenience function
def run_cocoon_drone_demo(cocoon_path: str):
    """
    Run a demo with a cocoon flying a drone.
    
    Args:
        cocoon_path: Path to cocoon .py file
    """
    import sys
    import os
    
    # Add cocoon directory to path
    cocoon_dir = os.path.dirname(cocoon_path)
    sys.path.insert(0, cocoon_dir)
    
    # Import cocoon
    cocoon_name = os.path.basename(cocoon_path).replace('.py', '')
    cocoon_module = __import__(cocoon_name)
    cocoon = cocoon_module.CocoonAgent()
    
    print(f"✅ Loaded cocoon from {cocoon_path}")
    
    # Create pilot
    pilot = CocoonDronePilot(cocoon, team="blue")
    
    # Fly mission with wind
    stats = pilot.fly_mission(
        duration=15.0,
        visualize=True,
        wind=np.array([4.0, 2.0, 0])
    )
    
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run with specified cocoon
        run_cocoon_drone_demo(sys.argv[1])
    else:
        # Quick test with mock cocoon
        print("🥚🛸 Testing CocoonDronePilot with mock cocoon...")
        
        class MockCocoon:
            def get_action(self, obs):
                # Random action for testing
                return np.random.randint(0, 6)
        
        pilot = CocoonDronePilot(MockCocoon(), team="blue")
        stats = pilot.fly_mission(duration=10.0, visualize=True, wind=np.array([3, 0, 0]))
        print(f"\n📊 Final stats: {stats}")
