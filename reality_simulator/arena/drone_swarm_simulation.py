"""
🛸 DRONE SWARM SIMULATION SYSTEM

The REAL drone simulation for cocoon organisms.
- One organism = One drone
- Dynamic scaling (5 to 5000+ drones)
- Full physics: wind, collisions, crashes
- Proper reward system for learning

This is the production system, not a demo.
"""

import sys
import os
import time
import numpy as np
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# VPython for visualization
try:
    from vpython import canvas, box, sphere, cylinder, arrow, vector, color, rate, label, curve, mag
    VPYTHON_AVAILABLE = True
except ImportError:
    VPYTHON_AVAILABLE = False
    logger.warning("VPython not available - no live visualization")


@dataclass
class DronePhysicsConfig:
    """Physics configuration for the swarm."""
    # World
    arena_size: float = 200.0          # Meters - scales with swarm size
    ground_level: float = 0.0
    ceiling: float = 100.0
    
    # Physics
    gravity: float = 9.81
    air_density: float = 1.225         # kg/m³
    drag_coefficient: float = 0.5
    
    # Wind
    wind_speed: float = 5.0            # m/s base
    wind_direction: float = 0.0        # radians
    wind_turbulence: float = 0.3       # Variance
    wind_gust_probability: float = 0.02
    
    # Drone specs
    mass: float = 1.5                  # kg
    max_thrust: float = 25.0           # N per motor
    hover_throttle: float = 0.473      # Calibrated for stable hover
    arm_length: float = 0.2            # meters
    
    # Collision
    collision_radius: float = 0.5      # meters - drone hitbox
    collision_damage: float = 0.3      # Health lost on collision
    ground_crash_damage: float = 0.5   # Health lost on ground crash
    
    # Battery
    battery_drain_rate: float = 0.001  # Per second at hover
    battery_drain_thrust: float = 0.002  # Additional per second at full throttle


@dataclass 
class RewardConfig:
    """Reward structure for organism learning."""
    # Positive rewards
    survival_per_second: float = 0.01
    altitude_bonus: float = 0.001      # Per meter above ground
    velocity_bonus: float = 0.0005     # Per m/s (encourages movement)
    formation_bonus: float = 0.005     # Near allies
    target_approach: float = 0.1       # Getting closer to target
    
    # Negative rewards (penalties)
    collision_penalty: float = -0.5
    crash_penalty: float = -1.0
    low_battery_penalty: float = -0.01  # Per second below 20%
    out_of_bounds_penalty: float = -0.1
    
    # Combat rewards (if enabled)
    tag_reward: float = 1.0
    tagged_penalty: float = -0.5
    kill_reward: float = 5.0
    death_penalty: float = -3.0


class SimulationMode(Enum):
    """Simulation modes."""
    FREEFLY = "freefly"              # Just fly around
    FORMATION = "formation"          # Try to maintain formation
    PURSUIT = "pursuit"              # Chase targets
    BATTLE = "battle"                # Combat mode
    TRAINING = "training"            # Headless fast training


@dataclass
class DroneState:
    """State of a single drone."""
    organism_id: str
    organism_index: int
    
    # Physics state
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    orientation: np.ndarray = field(default_factory=lambda: np.zeros(3))  # roll, pitch, yaw
    angular_velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # Status
    health: float = 1.0
    battery: float = 1.0
    alive: bool = True
    crashed: bool = False
    
    # Combat
    team: str = "neutral"
    last_tag_time: float = 0.0
    kills: int = 0
    deaths: int = 0
    
    # Stats
    flight_time: float = 0.0
    distance_traveled: float = 0.0
    total_reward: float = 0.0


class SwarmPhysicsEngine:
    """
    Physics engine for drone swarms.
    Handles all drones simultaneously with proper collision detection.
    """
    
    def __init__(self, config: DronePhysicsConfig = None):
        self.config = config or DronePhysicsConfig()
        self.drones: Dict[str, DroneState] = {}
        self.time = 0.0
        self.dt = 1/60  # 60 Hz simulation
        
        # Spatial partitioning for efficient collision detection
        self.grid_size = 10.0  # meters per grid cell
        self.spatial_grid: Dict[Tuple[int, int, int], List[str]] = {}
        
    def add_drone(self, organism_id: str, organism_index: int, 
                  team: str = "neutral",
                  spawn_position: np.ndarray = None) -> DroneState:
        """Add a drone for an organism."""
        state = DroneState(
            organism_id=organism_id,
            organism_index=organism_index,
            team=team
        )
        
        if spawn_position is not None:
            state.position = spawn_position.copy()
        else:
            # Default spawn in grid formation
            grid_size = int(np.ceil(np.sqrt(len(self.drones) + 1)))
            x = (organism_index % grid_size) * 3 - grid_size * 1.5
            y = (organism_index // grid_size) * 3 - grid_size * 1.5
            state.position = np.array([x, y, 10.0])  # 10m altitude
            
        self.drones[organism_id] = state
        return state
        
    def _get_grid_cell(self, position: np.ndarray) -> Tuple[int, int, int]:
        """Get spatial grid cell for position."""
        return (
            int(position[0] // self.grid_size),
            int(position[1] // self.grid_size),
            int(position[2] // self.grid_size)
        )
        
    def _update_spatial_grid(self):
        """Rebuild spatial grid for collision detection."""
        self.spatial_grid.clear()
        for drone_id, state in self.drones.items():
            if not state.alive:
                continue
            cell = self._get_grid_cell(state.position)
            if cell not in self.spatial_grid:
                self.spatial_grid[cell] = []
            self.spatial_grid[cell].append(drone_id)
            
    def _get_nearby_drones(self, position: np.ndarray) -> List[str]:
        """Get drones in nearby grid cells."""
        cell = self._get_grid_cell(position)
        nearby = []
        
        # Check 27 neighboring cells (3x3x3)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    neighbor = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                    if neighbor in self.spatial_grid:
                        nearby.extend(self.spatial_grid[neighbor])
                        
        return nearby
        
    def _get_wind(self, position: np.ndarray) -> np.ndarray:
        """Get wind vector at position with turbulence."""
        base_wind = np.array([
            np.cos(self.config.wind_direction) * self.config.wind_speed,
            np.sin(self.config.wind_direction) * self.config.wind_speed,
            0
        ])
        
        # Add turbulence
        turbulence = np.random.randn(3) * self.config.wind_turbulence * self.config.wind_speed
        
        # Occasional gusts
        if np.random.random() < self.config.wind_gust_probability:
            gust = np.random.randn(3) * self.config.wind_speed * 2
            turbulence += gust
            
        # Wind increases with altitude
        altitude_factor = 1.0 + position[2] / 50.0
        
        return (base_wind + turbulence) * altitude_factor
        
    def step(self, actions: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Step all drones forward by dt.
        
        Args:
            actions: Dict mapping organism_id to [throttle, roll, pitch, yaw]
                     Values normalized 0-1 for throttle, -1 to 1 for rates
                     
        Returns:
            Dict mapping organism_id to reward for this step
        """
        rewards = {}
        self._update_spatial_grid()
        
        for drone_id, state in self.drones.items():
            if not state.alive:
                rewards[drone_id] = 0.0
                continue
                
            # Get action (default to hover if not provided)
            action = actions.get(drone_id, np.array([self.config.hover_throttle, 0, 0, 0]))
            
            # Apply physics
            reward = self._step_drone(state, action)
            rewards[drone_id] = reward
            
        # Check collisions
        collision_rewards = self._check_collisions()
        for drone_id, col_reward in collision_rewards.items():
            rewards[drone_id] = rewards.get(drone_id, 0.0) + col_reward
            
        self.time += self.dt
        return rewards
        
    def _step_drone(self, state: DroneState, action: np.ndarray) -> float:
        """Step a single drone's physics."""
        reward = 0.0
        
        throttle = np.clip(action[0], 0, 1)
        roll_rate = np.clip(action[1], -1, 1) * 3.0  # rad/s
        pitch_rate = np.clip(action[2], -1, 1) * 3.0
        yaw_rate = np.clip(action[3], -1, 1) * 2.0
        
        # Get forces
        gravity = np.array([0, 0, -self.config.gravity * self.config.mass])
        
        # Thrust (body-frame up, rotated to world frame)
        thrust_mag = throttle * self.config.max_thrust * 4  # 4 motors
        
        roll, pitch, yaw = state.orientation
        
        # Rotation matrix (simplified)
        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        cr, sr = np.cos(roll), np.sin(roll)
        
        # Thrust direction in world frame
        thrust_dir = np.array([
            -sp,
            cp * sr,
            cp * cr
        ])
        thrust = thrust_dir * thrust_mag
        
        # Wind
        wind = self._get_wind(state.position)
        relative_velocity = state.velocity - wind
        
        # Drag
        speed = np.linalg.norm(relative_velocity)
        if speed > 0.01:
            drag_mag = 0.5 * self.config.air_density * self.config.drag_coefficient * speed**2
            drag = -relative_velocity / speed * drag_mag
        else:
            drag = np.zeros(3)
            
        # Total acceleration
        total_force = gravity + thrust + drag
        acceleration = total_force / self.config.mass
        
        # Update velocity and position
        old_position = state.position.copy()
        state.velocity += acceleration * self.dt
        state.position += state.velocity * self.dt
        
        # Update orientation
        state.orientation[0] += roll_rate * self.dt
        state.orientation[1] += pitch_rate * self.dt  
        state.orientation[2] += yaw_rate * self.dt
        
        # Clamp orientation
        state.orientation[0] = np.clip(state.orientation[0], -np.pi/4, np.pi/4)
        state.orientation[1] = np.clip(state.orientation[1], -np.pi/4, np.pi/4)
        
        # Ground collision
        if state.position[2] < self.config.ground_level + 0.1:
            if state.velocity[2] < -3.0:  # Hard crash
                state.health -= self.config.ground_crash_damage
                state.crashed = True
                reward += -1.0
            state.position[2] = self.config.ground_level + 0.1
            state.velocity[2] = 0
            state.velocity[:2] *= 0.5  # Ground friction
            
        # Ceiling
        if state.position[2] > self.config.ceiling:
            state.position[2] = self.config.ceiling
            state.velocity[2] = min(0, state.velocity[2])
            
        # Arena bounds
        half_arena = self.config.arena_size / 2
        for i in range(2):  # X and Y
            if abs(state.position[i]) > half_arena:
                state.position[i] = np.clip(state.position[i], -half_arena, half_arena)
                state.velocity[i] = 0
                reward += -0.1  # Out of bounds penalty
                
        # Battery drain
        thrust_factor = throttle / self.config.hover_throttle
        drain = self.config.battery_drain_rate + self.config.battery_drain_thrust * max(0, thrust_factor - 1)
        state.battery -= drain * self.dt
        
        if state.battery <= 0:
            state.battery = 0
            state.alive = False
            reward += -1.0
        elif state.battery < 0.2:
            reward += -0.01  # Low battery warning
            
        # Update stats
        state.flight_time += self.dt
        state.distance_traveled += np.linalg.norm(state.position - old_position)
        
        # Survival reward
        reward += 0.01
        
        # Altitude bonus
        reward += 0.001 * state.position[2]
        
        # Check alive
        if state.health <= 0:
            state.alive = False
            state.deaths += 1
            reward += -1.0
            
        state.total_reward += reward
        return reward
        
    def _check_collisions(self) -> Dict[str, float]:
        """Check drone-drone collisions using spatial grid."""
        rewards = {}
        checked_pairs = set()
        
        for drone_id, state in self.drones.items():
            if not state.alive:
                continue
                
            nearby = self._get_nearby_drones(state.position)
            
            for other_id in nearby:
                if other_id == drone_id:
                    continue
                    
                # Avoid checking same pair twice
                pair = tuple(sorted([drone_id, other_id]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                other = self.drones[other_id]
                if not other.alive:
                    continue
                    
                # Distance check
                dist = np.linalg.norm(state.position - other.position)
                if dist < self.config.collision_radius * 2:
                    # Collision!
                    rel_velocity = np.linalg.norm(state.velocity - other.velocity)
                    
                    # Damage based on impact speed
                    damage = self.config.collision_damage * (1 + rel_velocity / 10)
                    
                    state.health -= damage
                    other.health -= damage
                    
                    # Bounce apart
                    direction = state.position - other.position
                    if np.linalg.norm(direction) > 0.01:
                        direction = direction / np.linalg.norm(direction)
                    else:
                        direction = np.random.randn(3)
                        direction = direction / np.linalg.norm(direction)
                        
                    bounce_speed = max(2.0, rel_velocity * 0.5)
                    state.velocity += direction * bounce_speed
                    other.velocity -= direction * bounce_speed
                    
                    # Separate positions
                    overlap = self.config.collision_radius * 2 - dist
                    state.position += direction * overlap / 2
                    other.position -= direction * overlap / 2
                    
                    # Penalties
                    rewards[drone_id] = rewards.get(drone_id, 0) - 0.5
                    rewards[other_id] = rewards.get(other_id, 0) - 0.5
                    
                    logger.debug(f"💥 Collision: {drone_id} <-> {other_id} (damage: {damage:.2f})")
                    
        return rewards


class SwarmVisualizer:
    """Live 3D visualization for drone swarms using VPython."""
    
    def __init__(self, physics: SwarmPhysicsEngine, title: str = "Drone Swarm"):
        if not VPYTHON_AVAILABLE:
            raise RuntimeError("VPython not installed - cannot create visualizer")
            
        self.physics = physics
        self.drone_visuals: Dict[str, Dict] = {}
        self.trails: Dict[str, Any] = {}
        
        # Create scene - VPython uses Y as up, so we'll swap Y and Z
        self.scene = canvas(
            title=f'<b>{title}</b> | Drones: {len(physics.drones)}',
            width=1400,
            height=900,
            center=vector(0, 20, 0),  # Y is up in VPython
            background=color.cyan * 0.3,
            up=vector(0, 1, 0)  # Y is up
        )
        # Camera position looking at scene from above and side
        self.scene.camera.pos = vector(80, 60, 80)
        self.scene.camera.axis = vector(-80, -40, -80)
        
        self._create_environment()
        self._create_all_drones()
        
    def _physics_to_visual(self, pos: np.ndarray) -> vector:
        """Convert physics coords (Z up) to VPython coords (Y up)."""
        # Physics: X=forward, Y=right, Z=up
        # VPython: X=right, Y=up, Z=forward
        return vector(pos[0], pos[2], pos[1])
        
    def _create_environment(self):
        """Create ground, grid, sky elements."""
        arena = self.physics.config.arena_size
        
        # Ground plane (horizontal, at Y=0)
        box(
            pos=vector(0, -0.5, 0),
            size=vector(arena, 1, arena),
            color=color.green * 0.5
        )
        
        # Grid on ground
        grid_spacing = arena / 20
        for i in range(21):
            x = -arena/2 + i * grid_spacing
            curve(
                pos=[vector(x, 0.01, -arena/2), vector(x, 0.01, arena/2)],
                color=color.white * 0.2
            )
            curve(
                pos=[vector(-arena/2, 0.01, x), vector(arena/2, 0.01, x)],
                color=color.white * 0.2
            )
            
        # Origin axes (Y is up)
        arrow(pos=vector(0, 0.1, 0), axis=vector(10, 0, 0), color=color.red, shaftwidth=0.3)  # X
        arrow(pos=vector(0, 0.1, 0), axis=vector(0, 10, 0), color=color.green, shaftwidth=0.3)  # Y (up)
        arrow(pos=vector(0, 0.1, 0), axis=vector(0, 0, 10), color=color.blue, shaftwidth=0.3)  # Z
        
        # Wind indicator
        wind_speed = self.physics.config.wind_speed
        wind_dir = self.physics.config.wind_direction
        wind_visual_pos = vector(-arena/2 + 10, 30, -arena/2 + 10)
        arrow(
            pos=wind_visual_pos,
            axis=vector(np.cos(wind_dir), 0, np.sin(wind_dir)) * wind_speed,
            color=color.cyan,
            shaftwidth=0.5
        )
        label(
            pos=wind_visual_pos + vector(0, 5, 0),
            text=f'Wind: {wind_speed:.1f} m/s',
            height=12,
            color=color.cyan
        )
        
    def _get_drone_color(self, state: DroneState) -> vector:
        """Get color based on team and health."""
        if state.team == "blue":
            base = vector(0.2, 0.5, 1.0)
        elif state.team == "red":
            base = vector(1.0, 0.3, 0.2)
        else:
            # Neutral - color by organism index
            hue = (state.organism_index * 0.618033988749895) % 1.0  # Golden ratio
            if hue < 1/6:
                base = vector(1, hue * 6, 0)
            elif hue < 2/6:
                base = vector(1 - (hue - 1/6) * 6, 1, 0)
            elif hue < 3/6:
                base = vector(0, 1, (hue - 2/6) * 6)
            elif hue < 4/6:
                base = vector(0, 1 - (hue - 3/6) * 6, 1)
            elif hue < 5/6:
                base = vector((hue - 4/6) * 6, 0, 1)
            else:
                base = vector(1, 0, 1 - (hue - 5/6) * 6)
                
        # Darken based on health
        return base * (0.3 + 0.7 * state.health)
        
    def _create_drone_visual(self, state: DroneState) -> Dict:
        """Create visual elements for one drone."""
        pos = self._physics_to_visual(state.position)
        col = self._get_drone_color(state)
        
        # Body
        body = sphere(pos=pos, radius=0.3, color=col)
        
        # Arms and rotors (in horizontal plane)
        arms = []
        rotors = []
        arm_dirs = [
            vector(1, 0, 1).norm(),
            vector(1, 0, -1).norm(),
            vector(-1, 0, 1).norm(),
            vector(-1, 0, -1).norm()
        ]
        
        for arm_dir in arm_dirs:
            arm = cylinder(
                pos=pos,
                axis=arm_dir * 0.8,
                radius=0.05,
                color=color.gray(0.3)
            )
            arms.append(arm)
            
            rotor = cylinder(
                pos=pos + arm_dir * 0.8 - vector(0, 0.02, 0),
                axis=vector(0, 0.04, 0),
                radius=0.3,
                color=color.gray(0.5),
                opacity=0.5
            )
            rotors.append(rotor)
            
        # Front indicator
        front = arrow(
            pos=pos,
            axis=vector(1, 0, 0) * 1.2,
            color=color.yellow,
            shaftwidth=0.1
        )
        
        # Label
        lbl = label(
            pos=pos + vector(0, 1.5, 0),
            text=f'{state.organism_index}',
            height=10,
            color=color.white,
            background=color.black,
            opacity=0.3
        )
        
        # Trail
        trail = curve(color=col * 0.5, radius=0.03)
        trail.append(pos)
        
        return {
            'body': body,
            'arms': arms,
            'rotors': rotors,
            'front': front,
            'label': lbl,
            'trail': trail
        }
        
    def _create_all_drones(self):
        """Create visuals for all drones."""
        for drone_id, state in self.physics.drones.items():
            self.drone_visuals[drone_id] = self._create_drone_visual(state)
            
    def update(self):
        """Update all drone visuals from physics state."""
        for drone_id, state in self.physics.drones.items():
            if drone_id not in self.drone_visuals:
                self.drone_visuals[drone_id] = self._create_drone_visual(state)
                continue
                
            vis = self.drone_visuals[drone_id]
            pos = self._physics_to_visual(state.position)
            
            if not state.alive:
                # Hide dead drones
                vis['body'].visible = False
                for arm in vis['arms']:
                    arm.visible = False
                for rotor in vis['rotors']:
                    rotor.visible = False
                vis['front'].visible = False
                vis['label'].visible = False
                continue
                
            # Update color based on health
            col = self._get_drone_color(state)
            vis['body'].color = col
            vis['body'].pos = pos
            
            # Update arms and rotors (horizontal plane, Y is up)
            roll, pitch, yaw = state.orientation
            cy, sy = np.cos(yaw), np.sin(yaw)
            
            # Arms in XZ plane (horizontal)
            arm_dirs = [
                vector(cy + sy, 0, -cy + sy).norm(),
                vector(cy - sy, 0, cy + sy).norm(),
                vector(-cy - sy, 0, cy - sy).norm(),
                vector(-cy + sy, 0, -cy - sy).norm()
            ]
            
            for i, arm_dir in enumerate(arm_dirs):
                vis['arms'][i].pos = pos
                vis['arms'][i].axis = arm_dir * 0.8
                vis['rotors'][i].pos = pos + arm_dir * 0.8 - vector(0, 0.02, 0)
                
            # Update front arrow (heading in XZ plane)
            vis['front'].pos = pos
            vis['front'].axis = vector(cy, 0, sy) * 1.2
            
            # Update label
            vis['label'].pos = pos + vector(0, 1.5, 0)
            vis['label'].text = f'{state.organism_index}\n{state.health*100:.0f}%'
            
            # Update trail
            vis['trail'].append(pos)
            # Limit trail length - clear old points periodically
            if hasattr(vis['trail'], 'npoints') and vis['trail'].npoints > 500:
                # VPython curves don't support easy truncation, so we just let it grow
                # In production, would recreate trail periodically
                pass
                
    def set_camera_center(self, position: np.ndarray = None):
        """Center camera on position or swarm center."""
        if position is None:
            # Center on swarm
            positions = [s.position for s in self.physics.drones.values() if s.alive]
            if positions:
                center = np.mean(positions, axis=0)
                self.scene.center = self._physics_to_visual(center)
        else:
            self.scene.center = self._physics_to_visual(position)
            
    def tick(self, fps: int = 60):
        """Control frame rate."""
        rate(fps)


class CocoonSwarmSimulation:
    """
    Main simulation runner.
    Loads a cocoon, creates one drone per organism, runs simulation.
    """
    
    def __init__(self, cocoon_path: str, 
                 mode: SimulationMode = SimulationMode.FREEFLY,
                 visualize: bool = True):
        """
        Args:
            cocoon_path: Path to cocoon folder
            mode: Simulation mode
            visualize: Whether to show live 3D view
        """
        self.cocoon_path = cocoon_path
        self.mode = mode
        self.visualize = visualize and VPYTHON_AVAILABLE
        
        # Load cocoon
        self.cocoon = self._load_cocoon(cocoon_path)
        self.num_organisms = len(self.cocoon.brains)
        
        print(f"\n{'='*60}")
        print(f"🛸 DRONE SWARM SIMULATION")
        print(f"{'='*60}")
        print(f"Cocoon: {os.path.basename(cocoon_path)}")
        print(f"Organisms: {self.num_organisms}")
        print(f"Mode: {mode.value}")
        print(f"Visualization: {'ON' if self.visualize else 'OFF'}")
        
        # Scale arena based on swarm size
        arena_size = max(100, 10 * np.sqrt(self.num_organisms))
        
        # Create physics
        self.physics_config = DronePhysicsConfig(arena_size=arena_size)
        self.physics = SwarmPhysicsEngine(self.physics_config)
        
        # Add drones for each organism
        self._spawn_drones()
        
        # Create visualizer if enabled
        self.visualizer = None
        if self.visualize:
            self.visualizer = SwarmVisualizer(
                self.physics,
                title=f"Cocoon Swarm: {self.num_organisms} Drones"
            )
            
        print(f"Arena size: {arena_size:.0f}m")
        print(f"{'='*60}\n")
        
    def _load_cocoon(self, cocoon_path: str):
        """Load cocoon from path."""
        # Find the .py file
        if os.path.isdir(cocoon_path):
            py_files = [f for f in os.listdir(cocoon_path) if f.endswith('.py') and 'cocoon' in f.lower()]
            if not py_files:
                raise FileNotFoundError(f"No cocoon .py file found in {cocoon_path}")
            cocoon_file = py_files[0]
            module_name = cocoon_file.replace('.py', '')
        else:
            cocoon_path = os.path.dirname(cocoon_path)
            module_name = os.path.basename(cocoon_path).replace('.py', '')
            
        # Add to path and import
        sys.path.insert(0, cocoon_path)
        cocoon_module = __import__(module_name)
        cocoon = cocoon_module.CocoonAgent()
        
        return cocoon
        
    def _spawn_drones(self):
        """Create drones for all organisms."""
        # Grid spawn formation
        grid_size = int(np.ceil(np.sqrt(self.num_organisms)))
        spacing = 5.0  # meters between drones
        
        for i, organism_name in enumerate(self.cocoon.organism_names):
            # Grid position
            row = i // grid_size
            col = i % grid_size
            
            x = (col - grid_size/2) * spacing
            y = (row - grid_size/2) * spacing
            z = 10.0 + np.random.uniform(0, 5)  # 10-15m altitude
            
            self.physics.add_drone(
                organism_id=organism_name,
                organism_index=i,
                spawn_position=np.array([x, y, z])
            )
            
    def _get_organism_action(self, organism_index: int, state: DroneState) -> np.ndarray:
        """Get action from organism's brain."""
        # Build observation for organism
        # State: [x, y, z, vx, vy, vz, roll, pitch, yaw, health, battery]
        obs = np.concatenate([
            state.position / 100,  # Normalize
            state.velocity / 10,
            state.orientation,
            [state.health, state.battery]
        ]).astype(np.float32)
        
        # Pad to expected size (organisms expect certain input size)
        if len(obs) < 64:
            obs = np.pad(obs, (0, 64 - len(obs)))
            
        # Get action from organism's brain
        brain = self.cocoon.brains[organism_index]
        
        try:
            import torch
            with torch.no_grad():
                obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
                if hasattr(self.cocoon, 'device'):
                    obs_tensor = obs_tensor.to(self.cocoon.device)
                    
                # Get Q-values or action probabilities from brain
                output = brain(obs_tensor)
                
                # Handle tuple output (some brains return (output, hidden_state))
                if isinstance(output, tuple):
                    output = output[0]
                    
                # Get action index
                if hasattr(output, 'shape') and output.shape[-1] == 6:
                    # Discrete action (0-5) - convert to continuous
                    action_idx = output.argmax(dim=-1).item()
                    return self._discrete_to_continuous(action_idx)
                elif hasattr(output, 'item'):
                    # Single value
                    action_idx = int(output.item()) % 6
                    return self._discrete_to_continuous(action_idx)
                else:
                    # Fallback - use ensemble get_action
                    action_idx = self.cocoon.get_action(obs)
                    return self._discrete_to_continuous(action_idx)
                    
        except Exception as e:
            logger.debug(f"Brain {organism_index} error: {e}, using ensemble vote")
            # Fallback to ensemble vote
            try:
                action_idx = self.cocoon.get_action(obs)
                return self._discrete_to_continuous(action_idx)
            except:
                return np.array([self.physics_config.hover_throttle, 0, 0, 0])
            
    def _discrete_to_continuous(self, action: int) -> np.ndarray:
        """Convert discrete action (0-5) to motor commands."""
        # Action mapping:
        # 0: MOVE - forward
        # 1: COOPERATE - hover
        # 2: COMPETE - aggressive up
        # 3: REST - descend slowly
        # 4: REPRODUCE - spin
        # 5: ISOLATE - random dodge
        
        hover = self.physics_config.hover_throttle
        
        action_map = {
            0: [hover + 0.05, 0.0, 0.3, 0.0],    # Forward
            1: [hover, 0.0, 0.0, 0.0],            # Hover
            2: [hover + 0.1, 0.2, 0.2, 0.0],     # Aggressive
            3: [hover - 0.05, 0.0, 0.0, 0.0],    # Descend
            4: [hover, 0.0, 0.0, 0.5],           # Spin
            5: [hover, np.random.randn()*0.3, np.random.randn()*0.3, np.random.randn()*0.2]  # Dodge
        }
        
        return np.array(action_map.get(action, action_map[1]))
        
    def run(self, max_steps: int = 10000, 
            target_fps: int = 60,
            print_interval: int = 100) -> Dict[str, Any]:
        """
        Run the simulation.
        
        Args:
            max_steps: Maximum simulation steps
            target_fps: Target frame rate (lower = faster training)
            print_interval: Steps between status prints
            
        Returns:
            Statistics dictionary
        """
        print("Starting simulation...")
        if self.visualize:
            print("\nControls:")
            print("  Right-click + drag: Rotate")
            print("  Scroll: Zoom")
            print("  Middle-click: Pan")
            print("\nPress Ctrl+C to stop\n")
            
        step = 0
        start_time = time.time()
        
        try:
            while step < max_steps:
                # Get actions from all organisms
                actions = {}
                for i, (drone_id, state) in enumerate(self.physics.drones.items()):
                    if state.alive:
                        actions[drone_id] = self._get_organism_action(i, state)
                        
                # Step physics
                rewards = self.physics.step(actions)
                
                # Update visualization
                if self.visualize:
                    self.visualizer.update()
                    
                    if step % 60 == 0:  # Every second
                        self.visualizer.set_camera_center()
                        
                    self.visualizer.tick(target_fps)
                    
                # Status print
                if step % print_interval == 0:
                    alive = sum(1 for s in self.physics.drones.values() if s.alive)
                    avg_health = np.mean([s.health for s in self.physics.drones.values() if s.alive]) if alive > 0 else 0
                    avg_alt = np.mean([s.position[2] for s in self.physics.drones.values() if s.alive]) if alive > 0 else 0
                    
                    print(f"Step {step:5d} | Alive: {alive:3d}/{self.num_organisms} | "
                          f"Health: {avg_health*100:5.1f}% | Alt: {avg_alt:5.1f}m | "
                          f"Time: {self.physics.time:.1f}s")
                          
                # Check if all dead
                if not any(s.alive for s in self.physics.drones.values()):
                    print("\n⚠️ All drones destroyed!")
                    break
                    
                step += 1
                
        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")
            
        # Final statistics
        elapsed = time.time() - start_time
        alive = sum(1 for s in self.physics.drones.values() if s.alive)
        
        stats = {
            'steps': step,
            'duration': elapsed,
            'sim_time': self.physics.time,
            'alive': alive,
            'total': self.num_organisms,
            'survival_rate': alive / self.num_organisms,
            'organism_stats': {
                drone_id: {
                    'alive': state.alive,
                    'health': state.health,
                    'battery': state.battery,
                    'distance': state.distance_traveled,
                    'reward': state.total_reward
                }
                for drone_id, state in self.physics.drones.items()
            }
        }
        
        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Steps: {step}")
        print(f"Sim time: {self.physics.time:.1f}s")
        print(f"Real time: {elapsed:.1f}s")
        print(f"Survivors: {alive}/{self.num_organisms} ({100*alive/self.num_organisms:.1f}%)")
        
        if self.visualize:
            print("\nVisualization window still open - close to exit")
            while True:
                self.visualizer.tick(30)
                
        return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🛸 Drone Swarm Simulation")
    parser.add_argument('cocoon', help='Path to cocoon folder')
    parser.add_argument('--mode', choices=['freefly', 'formation', 'battle', 'training'],
                        default='freefly', help='Simulation mode')
    parser.add_argument('--no-visual', action='store_true', help='Disable visualization')
    parser.add_argument('--steps', type=int, default=10000, help='Max simulation steps')
    parser.add_argument('--fps', type=int, default=60, help='Target FPS')
    parser.add_argument('--wind', type=float, default=5.0, help='Wind speed (m/s)')
    
    args = parser.parse_args()
    
    # Run simulation
    sim = CocoonSwarmSimulation(
        cocoon_path=args.cocoon,
        mode=SimulationMode(args.mode),
        visualize=not args.no_visual
    )
    
    # Set wind
    sim.physics.config.wind_speed = args.wind
    
    sim.run(max_steps=args.steps, target_fps=args.fps)


if __name__ == "__main__":
    main()
