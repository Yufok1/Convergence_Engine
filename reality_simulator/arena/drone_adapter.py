"""
🛸 ORGANISM-DRONE ADAPTER

Bridges the gap between organism cognition and drone physics.
Organisms think in discrete actions (move, cooperate, compete, rest, reproduce, isolate).
Drones need continuous thrust vectors.

This adapter translates organism intent → drone control.

Architecture:
    Organism.decide() → action (0-5)
           ↓
    DroneAdapter.translate() → drone_command (continuous)
           ↓
    QuadcopterFDM.step() → realistic physics simulation
           ↓
    Observation → Organism.record_experience()

The organism learns that certain actions in certain states lead to 
survival, victory, or death. Over generations, they evolve tactical instincts.

Physics Backend:
    - Primary: JSBSim-based QuadcopterFDM (realistic 6-DOF, wind, drag)
    - Fallback: Simulated physics (when neither JSBSim nor PyFlyt available)
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Check for physics backend availability
QUADCOPTER_FDM_AVAILABLE = False
PYFLYT_AVAILABLE = False

# Try our JSBSim-based quadcopter first (no C++ needed)
try:
    from reality_simulator.arena.jsbsim_quadcopter import QuadcopterFDM, QuadcopterEnv, MultiQuadcopterEnv
    QUADCOPTER_FDM_AVAILABLE = True
    logger.info("✅ JSBSim QuadcopterFDM available (realistic physics)")
except ImportError:
    logger.debug("JSBSim QuadcopterFDM not available")

# PyFlyt as secondary option (requires C++ build tools on Windows)
try:
    import gymnasium
    import PyFlyt.gym_envs  # Registers PyFlyt environments
    PYFLYT_AVAILABLE = True
    logger.info("✅ PyFlyt drone simulator available")
except ImportError:
    logger.debug("PyFlyt not installed")
    gymnasium = None

# Import gymnasium if not already
if gymnasium is None:
    try:
        import gymnasium
    except ImportError:
        pass


class DroneAction(Enum):
    """
    Maps organism's 6 world actions to drone maneuvers.
    
    The organism doesn't know it's controlling a drone.
    It just knows these actions lead to outcomes.
    """
    MOVE = 0        # Thrust forward - aggressive pursuit
    COOPERATE = 1   # Formation tighten - move toward allies
    COMPETE = 2     # Attack run - dive toward nearest enemy
    REST = 3        # Hover - maintain position, conserve energy
    REPRODUCE = 4   # Deploy decoy/split attention
    ISOLATE = 5     # Evasive - break formation, random juke


@dataclass
class DroneState:
    """Observable state from drone's perspective."""
    position: np.ndarray          # [x, y, z]
    velocity: np.ndarray          # [vx, vy, vz]
    orientation: np.ndarray       # [roll, pitch, yaw]
    angular_velocity: np.ndarray  # [wx, wy, wz]
    
    # Tactical awareness
    allies_positions: List[np.ndarray] = field(default_factory=list)
    enemies_positions: List[np.ndarray] = field(default_factory=list)
    nearest_ally_distance: float = float('inf')
    nearest_enemy_distance: float = float('inf')
    
    # Combat state
    health: float = 1.0
    is_tagged: bool = False
    tag_cooldown: float = 0.0
    
    def to_observation(self) -> np.ndarray:
        """Convert to 28-dim observation for organism's brain."""
        obs = np.zeros(28, dtype=np.float32)
        
        # Position (normalized to arena bounds ~[-10, 10])
        obs[0:3] = np.clip(self.position / 10.0, -1, 1)
        
        # Velocity (normalized)
        obs[3:6] = np.clip(self.velocity / 5.0, -1, 1)
        
        # Orientation (already ~[-pi, pi], normalize to [-1, 1])
        obs[6:9] = self.orientation / np.pi
        
        # Angular velocity
        obs[9:12] = np.clip(self.angular_velocity / 3.0, -1, 1)
        
        # Tactical features
        obs[12] = np.clip(self.nearest_ally_distance / 10.0, 0, 1)
        obs[13] = np.clip(self.nearest_enemy_distance / 10.0, 0, 1)
        obs[14] = len(self.allies_positions) / 10.0  # Ally count (normalized)
        obs[15] = len(self.enemies_positions) / 10.0  # Enemy count
        
        # Combat state
        obs[16] = self.health
        obs[17] = 1.0 if self.is_tagged else 0.0
        obs[18] = np.clip(self.tag_cooldown / 5.0, 0, 1)
        
        # Direction to nearest enemy (if exists)
        if self.enemies_positions and len(self.enemies_positions) > 0:
            nearest_enemy = min(self.enemies_positions, 
                               key=lambda p: np.linalg.norm(p - self.position))
            direction = nearest_enemy - self.position
            dist = np.linalg.norm(direction)
            if dist > 0:
                obs[19:22] = direction / dist  # Unit vector to enemy
        
        # Direction to nearest ally (if exists)
        if self.allies_positions and len(self.allies_positions) > 0:
            nearest_ally = min(self.allies_positions,
                              key=lambda p: np.linalg.norm(p - self.position))
            direction = nearest_ally - self.position
            dist = np.linalg.norm(direction)
            if dist > 0:
                obs[22:25] = direction / dist  # Unit vector to ally
        
        # Altitude danger (too low or too high)
        obs[25] = np.clip(self.position[2] / 5.0, 0, 1)  # Height
        obs[26] = 1.0 if self.position[2] < 0.5 else 0.0  # Ground danger
        obs[27] = 1.0 if self.position[2] > 9.0 else 0.0  # Ceiling danger
        
        return obs


class OrganismDroneAdapter:
    """
    Wraps a single organism to control a single drone.
    
    The organism's brain outputs discrete actions (0-5).
    This adapter translates to continuous drone commands.
    
    Over time, the organism learns:
    - action 2 (COMPETE) when enemy is close → reward (tag)
    - action 1 (COOPERATE) when allies near → survival
    - action 5 (ISOLATE) when outnumbered → escape
    """
    
    # Thrust magnitude for each action type
    ACTION_THRUST = {
        DroneAction.MOVE: 0.8,       # Strong forward
        DroneAction.COOPERATE: 0.3,  # Gentle toward allies
        DroneAction.COMPETE: 1.0,    # Full attack thrust
        DroneAction.REST: 0.0,       # Hover
        DroneAction.REPRODUCE: 0.2,  # Slow, spawn decoy
        DroneAction.ISOLATE: 0.9,    # Fast evasive
    }
    
    def __init__(self, organism, drone_id: int = 0, team: str = "blue"):
        """
        Args:
            organism: The organism controlling this drone
            drone_id: ID in multi-drone environment
            team: "blue" or "red" for combat
        """
        self.organism = organism
        self.drone_id = drone_id
        self.team = team
        
        # State tracking
        self.state = DroneState(
            position=np.zeros(3),
            velocity=np.zeros(3),
            orientation=np.zeros(3),
            angular_velocity=np.zeros(3)
        )
        
        # Combat tracking
        self.tags_scored = 0
        self.times_tagged = 0
        self.flight_time = 0.0
        self.alive = True
        
        # For experience recording
        self.prev_state = None
        self.prev_action = None
        
        logger.debug(f"🛸 DroneAdapter created for organism {organism.organism_id[:8]}")
    
    def translate_action(self, action: int, state: DroneState) -> np.ndarray:
        """
        Translate organism's discrete action to continuous drone command.
        
        Args:
            action: 0-5 (organism's world action)
            state: Current drone state
            
        Returns:
            np.ndarray: [thrust, roll_rate, pitch_rate, yaw_rate] or env-specific
        """
        drone_action = DroneAction(action)
        thrust_mag = self.ACTION_THRUST[drone_action]
        
        # Base command: [thrust, roll, pitch, yaw] in range [-1, 1]
        command = np.zeros(4, dtype=np.float32)
        
        if drone_action == DroneAction.MOVE:
            # Forward thrust
            command[0] = thrust_mag  # Throttle up
            command[2] = -0.3        # Pitch forward
            
        elif drone_action == DroneAction.COOPERATE:
            # Move toward nearest ally
            if state.allies_positions:
                nearest_ally = min(state.allies_positions,
                                  key=lambda p: np.linalg.norm(p - state.position))
                direction = nearest_ally - state.position
                direction = direction / (np.linalg.norm(direction) + 1e-6)
                
                command[0] = thrust_mag
                command[2] = -direction[0] * 0.5  # Pitch toward
                command[1] = direction[1] * 0.3   # Roll toward
            else:
                # No allies, just hover
                command[0] = 0.5  # Maintain altitude
                
        elif drone_action == DroneAction.COMPETE:
            # Aggressive attack toward nearest enemy
            if state.enemies_positions:
                nearest_enemy = min(state.enemies_positions,
                                   key=lambda p: np.linalg.norm(p - state.position))
                direction = nearest_enemy - state.position
                dist = np.linalg.norm(direction)
                direction = direction / (dist + 1e-6)
                
                command[0] = thrust_mag
                command[2] = -direction[0] * 0.8  # Strong pitch toward
                command[1] = direction[1] * 0.5   # Roll toward
                
                # Extra thrust if close (ram potential)
                if dist < 2.0:
                    command[0] = 1.0
            else:
                # No enemies, patrol forward
                command[0] = 0.7
                command[2] = -0.2
                
        elif drone_action == DroneAction.REST:
            # Hover in place
            command[0] = 0.5  # Counter gravity
            # Small corrections based on velocity to stabilize
            command[1] = -state.velocity[1] * 0.3
            command[2] = -state.velocity[0] * 0.3
            
        elif drone_action == DroneAction.REPRODUCE:
            # Slow, deploy decoy (future: actually spawn decoy drone)
            command[0] = 0.4
            command[3] = 0.5  # Spin (disorienting)
            
        elif drone_action == DroneAction.ISOLATE:
            # Evasive maneuver - random juke
            command[0] = thrust_mag
            command[1] = np.random.uniform(-0.8, 0.8)  # Random roll
            command[2] = np.random.uniform(-0.8, 0.8)  # Random pitch
            command[3] = np.random.uniform(-0.5, 0.5)  # Random yaw
        
        return np.clip(command, -1.0, 1.0)
    
    def update_state(self, raw_obs: np.ndarray, 
                     allies: List['OrganismDroneAdapter'] = None,
                     enemies: List['OrganismDroneAdapter'] = None):
        """
        Update internal state from environment observation.
        
        Args:
            raw_obs: Raw observation from PyFlyt
            allies: Other adapters on same team
            enemies: Adapters on opposing team
        """
        # PyFlyt QuadX observation structure (varies by env)
        # Typically: [pos(3), vel(3), quat(4), ang_vel(3), ...] = 13+ dims
        
        if len(raw_obs) >= 13:
            self.state.position = raw_obs[0:3].copy()
            self.state.velocity = raw_obs[3:6].copy()
            # Quaternion to euler (simplified - just use first 3)
            self.state.orientation = raw_obs[6:9].copy() if len(raw_obs) >= 9 else np.zeros(3)
            self.state.angular_velocity = raw_obs[9:12].copy() if len(raw_obs) >= 12 else np.zeros(3)
        else:
            # Fallback for different obs structure
            self.state.position = raw_obs[:min(3, len(raw_obs))].copy()
        
        # Update tactical awareness
        if allies:
            self.state.allies_positions = [a.state.position for a in allies if a.alive and a != self]
            if self.state.allies_positions:
                self.state.nearest_ally_distance = min(
                    np.linalg.norm(p - self.state.position) 
                    for p in self.state.allies_positions
                )
        
        if enemies:
            self.state.enemies_positions = [e.state.position for e in enemies if e.alive]
            if self.state.enemies_positions:
                self.state.nearest_enemy_distance = min(
                    np.linalg.norm(p - self.state.position)
                    for p in self.state.enemies_positions
                )
    
    def get_action(self, epsilon: float = None) -> Tuple[int, np.ndarray]:
        """
        Get organism's decision and translate to drone command.
        
        Returns:
            Tuple of (discrete_action, continuous_command)
        """
        # Convert state to observation for organism
        obs = self.state.to_observation()
        
        # Store for experience recording
        self.prev_state = obs.copy()
        
        # Get organism's decision
        if hasattr(self.organism, 'decide_with_state'):
            action = self.organism.decide_with_state(obs, epsilon)
        elif hasattr(self.organism, 'decide'):
            # Inject state temporarily
            old_state = getattr(self.organism, 'current_state', None)
            self.organism.current_state = obs
            action = self.organism.decide()
            if old_state is not None:
                self.organism.current_state = old_state
        else:
            # Fallback random
            action = np.random.randint(0, 6)
        
        self.prev_action = action
        
        # Translate to drone command
        command = self.translate_action(action, self.state)
        
        return action, command
    
    def record_step(self, reward: float, done: bool = False):
        """Record experience for organism learning."""
        if self.prev_state is None or self.prev_action is None:
            return
            
        next_obs = self.state.to_observation()
        
        # Use gym-specific recording if available
        if hasattr(self.organism, 'record_gym_experience'):
            self.organism.record_gym_experience(
                state=self.prev_state,
                action=self.prev_action,
                reward=reward,
                next_state=next_obs,
                done=done
            )
        elif hasattr(self.organism, 'record_experience'):
            self.organism.prev_state = self.prev_state
            self.organism.prev_action = self.prev_action
            self.organism.record_experience(
                reward=reward,
                next_state=next_obs,
                done=done
            )
    
    def check_tag(self, enemies: List['OrganismDroneAdapter'], 
                  tag_distance: float = 1.0) -> Optional['OrganismDroneAdapter']:
        """
        Check if this drone tags an enemy.
        
        Args:
            enemies: List of enemy adapters
            tag_distance: Distance threshold for tag
            
        Returns:
            Tagged enemy adapter or None
        """
        if not self.alive or self.state.tag_cooldown > 0:
            return None
            
        for enemy in enemies:
            if not enemy.alive:
                continue
            dist = np.linalg.norm(self.state.position - enemy.state.position)
            if dist < tag_distance:
                self.tags_scored += 1
                self.state.tag_cooldown = 2.0  # 2 second cooldown
                return enemy
        
        return None
    
    def receive_tag(self, damage: float = 0.25):
        """Called when this drone is tagged."""
        self.times_tagged += 1
        self.state.health -= damage
        self.state.is_tagged = True
        
        if self.state.health <= 0:
            self.alive = False
            logger.info(f"💀 Drone {self.drone_id} ({self.organism.organism_id[:8]}) eliminated!")
    
    def tick(self, dt: float = 0.1):
        """Update time-based state."""
        self.flight_time += dt
        if self.state.tag_cooldown > 0:
            self.state.tag_cooldown = max(0, self.state.tag_cooldown - dt)
        self.state.is_tagged = False  # Reset per-frame


class SingleDroneArena:
    """
    Simple single-drone environment for basic training.
    Organism learns to fly before combat.
    
    Args:
        env_name: PyFlyt environment (default QuadX-Hover-v4)
        render: If True, show 3D visualization. False for headless training.
    """
    
    def __init__(self, env_name: str = "PyFlyt/QuadX-Hover-v4", render: bool = False):
        if not PYFLYT_AVAILABLE:
            raise RuntimeError("PyFlyt not available. Install with: pip install PyFlyt")
        
        self.env_name = env_name
        self.render = render
        
        # render_mode=None for headless (fast training)
        # render_mode="human" for 3D visualization
        render_mode = "human" if render else None
        self.env = gymnasium.make(env_name, render_mode=render_mode)
        self.adapter = None
        
        mode = "🖥️ VISUAL" if render else "⚡ HEADLESS"
        logger.info(f"🛸 SingleDroneArena created with {env_name} ({mode})")
    
    def run_episode(self, organism, max_steps: int = 500) -> Dict[str, Any]:
        """
        Run single organism in drone environment.
        
        Args:
            organism: The organism controlling the drone
            max_steps: Maximum steps per episode
            
        Returns:
            Dict with episode statistics
        """
        self.adapter = OrganismDroneAdapter(organism, drone_id=0, team="blue")
        
        obs, info = self.env.reset()
        self.adapter.update_state(obs)
        
        total_reward = 0.0
        steps = 0
        
        for step in range(max_steps):
            # Get organism decision
            action, command = self.adapter.get_action()
            
            # Execute in environment
            next_obs, reward, terminated, truncated, info = self.env.step(command)
            
            # Update adapter state
            self.adapter.update_state(next_obs)
            self.adapter.tick()
            
            # Record experience
            done = terminated or truncated
            self.adapter.record_step(reward, done)
            
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        return {
            'total_reward': total_reward,
            'steps': steps,
            'flight_time': self.adapter.flight_time,
            'organism_id': organism.organism_id
        }
    
    def close(self):
        if self.env:
            self.env.close()


# =============================================================================
# Utility functions for testing
# =============================================================================

def test_drone_adapter():
    """Quick test of drone adapter without full organism."""
    if not PYFLYT_AVAILABLE:
        print("❌ PyFlyt not installed")
        return
    
    print("🛸 Testing DroneAdapter...")
    
    # Mock organism
    class MockOrganism:
        organism_id = "test_organism_12345678"
        def decide(self):
            return np.random.randint(0, 6)
    
    arena = SingleDroneArena()
    result = arena.run_episode(MockOrganism(), max_steps=100)
    
    print(f"✅ Test complete: {result}")
    arena.close()


if __name__ == "__main__":
    test_drone_adapter()
