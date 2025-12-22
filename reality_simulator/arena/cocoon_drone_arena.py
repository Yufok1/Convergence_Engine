"""
🛸 COCOON DRONE ARENA

The unified drone warfare training system for cocoons.
One organism = One drone. Full swarm coordination.

Game Modes (adapted from Proton Game):
    1. FREE_FLY        - Basic flight training, learn controls
    2. FORMATION       - Maintain swarm formation (team coordination)
    3. PURSUIT         - Chase moving targets
    4. TAG_BATTLE      - Combat: tag enemies, avoid being tagged
    5. ZONE_CONTROL    - Control airspace zones
    6. CAPTURE_FLAG    - Team objective game
    7. SURVIVAL        - Last drone flying wins
    8. ESCORT          - Protect VIP drone
    
Physics Standards (NASA JSBSim-compatible):
    - 6-DOF rigid body dynamics
    - Realistic wind/turbulence model
    - Proper thrust-to-weight ratios
    - Collision detection and damage
    - Battery drain simulation
    
Reward Structure (RL-compatible):
    - Immediate rewards for actions
    - Episode rewards for objectives
    - Fitness transfer for evolution
    
Integration:
    - Works with CocoonAgent.brains[] (individual organisms)
    - Compatible with ProtonGameArena selection
    - Exports learning data for training
    - LanguageGameBridge: Uses vocabulary to bias actions!
"""

import sys
import os
import time
import numpy as np
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

# PyFlyt/PyBullet - LAZY LOAD to avoid slow startup
# These are only loaded when visualization is actually requested
PYFLYT_AVAILABLE = None  # None = not checked yet
PYBULLET_AVAILABLE = None
Aviary = None
p = None

def _lazy_load_pyflyt():
    """Load PyFlyt only when needed."""
    global PYFLYT_AVAILABLE, Aviary
    if PYFLYT_AVAILABLE is None:
        try:
            from PyFlyt.core import Aviary as _Aviary
            Aviary = _Aviary
            PYFLYT_AVAILABLE = True
        except ImportError:
            PYFLYT_AVAILABLE = False
            logger.debug("PyFlyt not available - 3D visualization disabled")
    return PYFLYT_AVAILABLE

def _lazy_load_pybullet():
    """Load PyBullet only when needed."""
    global PYBULLET_AVAILABLE, p
    if PYBULLET_AVAILABLE is None:
        try:
            import pybullet as _p
            import pybullet_data
            p = _p
            PYBULLET_AVAILABLE = True
        except ImportError:
            PYBULLET_AVAILABLE = False
            logger.debug("PyBullet not available")
    return PYBULLET_AVAILABLE

# Import language-game bridge for vocabulary-enhanced action selection
try:
    from reality_simulator.language.language_game_bridge import (
        LanguageGameBridge, 
        ActivatedConcepts,
        create_bridge_for_organism
    )
    LANGUAGE_BRIDGE_AVAILABLE = True
except ImportError:
    LANGUAGE_BRIDGE_AVAILABLE = False
    logger.debug("LanguageGameBridge not available - running without language enhancement")


class DroneGameMode(Enum):
    """Available game modes for drone arena."""
    FREE_FLY = "free_fly"
    FORMATION = "formation"
    PURSUIT = "pursuit"
    TAG_BATTLE = "tag_battle"
    ZONE_CONTROL = "zone_control"
    CAPTURE_FLAG = "capture_flag"
    SURVIVAL = "survival"
    ESCORT = "escort"
    
    
@dataclass
class DroneArenaConfig:
    """Configuration for drone arena simulations."""
    # Arena
    arena_size: float = 200.0       # meters
    min_altitude: float = 1.0       # meters (ground + safety)
    max_altitude: float = 100.0     # meters
    
    # Physics
    gravity: float = 9.81           # m/s²
    air_density: float = 1.225      # kg/m³ (sea level)
    wind_speed: float = 5.0         # m/s base wind
    wind_direction: float = 0.0     # radians
    turbulence: float = 0.3         # turbulence intensity
    
    # Drone specs (realistic quadcopter)
    drone_mass: float = 1.5         # kg
    max_thrust: float = 32.0        # N total (4 motors)
    hover_throttle: float = 0.473   # calibrated for stable hover
    drag_coefficient: float = 0.25
    
    # Combat
    tag_distance: float = 2.0       # meters to register tag
    tag_cooldown: float = 3.0       # seconds between tags
    tag_damage: float = 0.25        # health per tag (4 tags = kill)
    collision_damage: float = 0.3   # health per collision
    crash_damage: float = 0.5       # health for ground crash
    
    # Game settings
    max_episode_steps: int = 3000   # ~50 seconds at 60Hz
    target_fps: int = 60
    
    # Rewards (RL-standard)
    reward_survival: float = 0.01       # per step alive
    reward_altitude: float = 0.001      # per meter altitude
    reward_tag: float = 1.0             # for tagging enemy
    reward_tagged: float = -0.5         # for being tagged
    reward_kill: float = 5.0            # for eliminating enemy
    reward_death: float = -3.0          # for being eliminated
    reward_zone: float = 0.1            # per step in objective zone
    reward_formation: float = 0.05      # per step in formation
    reward_collision: float = -0.5      # for collision
    reward_crash: float = -1.0          # for ground crash
    reward_win: float = 10.0            # team victory
    reward_loss: float = -5.0           # team defeat


@dataclass
class DroneState:
    """State of a single drone."""
    organism_id: str
    organism_index: int
    team: str = "neutral"
    
    # Physics (NED-like: X forward, Y right, Z up)
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    orientation: np.ndarray = field(default_factory=lambda: np.zeros(3))  # roll, pitch, yaw
    
    # Status
    health: float = 1.0
    battery: float = 1.0
    alive: bool = True
    
    # Reference to controlling cocoon (for cocoon vs cocoon battles)
    cocoon_ref: Any = None
    
    # Combat
    last_tag_time: float = -999.0
    tags_given: int = 0
    tags_received: int = 0
    kills: int = 0
    
    # Objective
    in_zone: bool = False
    zone_time: float = 0.0
    has_flag: bool = False
    is_vip: bool = False            # ESCORT mode
    waypoints_hit: int = 0          # FREE_FLY mode
    pursuit_time_near: float = 0.0  # PURSUIT mode - time spent near target
    
    # Stats
    flight_time: float = 0.0
    distance_traveled: float = 0.0
    total_reward: float = 0.0


@dataclass 
class GameState:
    """State of the current game."""
    mode: DroneGameMode
    time_elapsed: float = 0.0
    step_count: int = 0
    
    # Teams
    blue_alive: int = 0
    red_alive: int = 0
    blue_score: float = 0.0
    red_score: float = 0.0
    
    # Zones (ZONE_CONTROL)
    zones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Flags (CAPTURE_FLAG)
    blue_flag_pos: np.ndarray = None
    red_flag_pos: np.ndarray = None
    blue_flag_captured: bool = False
    red_flag_captured: bool = False
    
    # Waypoints (FREE_FLY)
    waypoints: List[np.ndarray] = field(default_factory=list)
    waypoint_radius: float = 5.0
    
    # Formation (FORMATION)
    formation_offsets: List[np.ndarray] = field(default_factory=list)
    
    # Pursuit target (PURSUIT)
    target_pos: np.ndarray = None
    target_vel: np.ndarray = None
    pursuit_radius: float = 5.0
    
    # Survival (SURVIVAL)
    arena_radius: float = 100.0
    shrink_rate: float = 0.5
    min_arena_radius: float = 20.0
    
    # VIP (ESCORT)
    blue_vip: str = None
    red_vip: str = None
    
    # Outcome
    finished: bool = False
    winner: str = None  # "blue", "red", "draw"


# Import NASA JSBSim-grade physics (try local first for standalone mode)
JSBSIM_PHYSICS_AVAILABLE = False

def _try_local_jsbsim_import():
    """Try local jsbsim_quadcopter.py (from --unpack)."""
    global JSBSIM_PHYSICS_AVAILABLE
    local_dir = os.path.dirname(os.path.abspath(__file__))
    physics_path = os.path.join(local_dir, 'jsbsim_quadcopter.py')
    
    if os.path.exists(physics_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('jsbsim_quadcopter', physics_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            globals()['QuadcopterFDM'] = module.QuadcopterFDM
            globals()['QuadcopterConfig'] = module.QuadcopterConfig
            globals()['QuadcopterState'] = module.QuadcopterState
            JSBSIM_PHYSICS_AVAILABLE = True
            logger.info("✅ JSBSim physics loaded from local jsbsim_quadcopter.py")
            return True
        except Exception as e:
            logger.debug(f"Local jsbsim import failed: {e}")
    return False

def _try_package_jsbsim_import():
    """Try package import."""
    global JSBSIM_PHYSICS_AVAILABLE
    try:
        from reality_simulator.arena.jsbsim_quadcopter import QuadcopterFDM, QuadcopterConfig, QuadcopterState
        globals()['QuadcopterFDM'] = QuadcopterFDM
        globals()['QuadcopterConfig'] = QuadcopterConfig
        globals()['QuadcopterState'] = QuadcopterState
        JSBSIM_PHYSICS_AVAILABLE = True
        logger.info("✅ JSBSim-grade quadcopter physics loaded from package")
        return True
    except ImportError:
        return False

# Try local first (standalone from --unpack), then package
if not _try_local_jsbsim_import():
    if not _try_package_jsbsim_import():
        logger.warning("⚠️ JSBSim physics not available, using simplified model")


class DronePhysics:
    """
    Physics engine for drone simulation.
    NASA JSBSim-compatible 6-DOF model.
    
    NOW USES REAL JSBSIM PHYSICS when available!
    All 8 game modes use identical realistic physics.
    """
    
    def __init__(self, config: DroneArenaConfig = None, use_jsbsim: bool = True):
        self.config = config or DroneArenaConfig()
        self.dt = 1.0 / self.config.target_fps
        self.use_jsbsim = use_jsbsim and JSBSIM_PHYSICS_AVAILABLE
        
        # Per-drone FDM instances for JSBSim physics
        self._fdm_cache: Dict[str, 'QuadcopterFDM'] = {}
        
        if self.use_jsbsim:
            logger.info("🚀 DronePhysics using NASA JSBSim-grade 6-DOF dynamics")
        else:
            logger.info("📐 DronePhysics using simplified dynamics")
    
    def _get_fdm(self, drone_id: str) -> 'QuadcopterFDM':
        """Get or create JSBSim FDM for a drone."""
        if drone_id not in self._fdm_cache:
            fdm_config = QuadcopterConfig(
                mass=self.config.drone_mass,
                max_thrust_per_motor=self.config.max_thrust / 4,
                drag_coefficient=self.config.drag_coefficient,
            )
            fdm = QuadcopterFDM(config=fdm_config, use_jsbsim=True)
            self._fdm_cache[drone_id] = fdm
        return self._fdm_cache[drone_id]
    
    def _sync_state_to_fdm(self, state: DroneState, fdm: 'QuadcopterFDM'):
        """Copy DroneState to QuadcopterFDM state."""
        fdm.state.x = state.position[0]
        fdm.state.y = state.position[1]
        fdm.state.z = state.position[2]
        fdm.state.u = state.velocity[0]
        fdm.state.v = state.velocity[1]
        fdm.state.w = state.velocity[2]
        fdm.state.phi = state.orientation[0]
        fdm.state.theta = state.orientation[1]
        fdm.state.psi = state.orientation[2]
        fdm.state.battery_remaining = state.battery
    
    def _sync_fdm_to_state(self, fdm: 'QuadcopterFDM', state: DroneState):
        """Copy QuadcopterFDM state back to DroneState."""
        state.position[0] = fdm.state.x
        state.position[1] = fdm.state.y
        state.position[2] = fdm.state.z
        state.velocity[0] = fdm.state.u
        state.velocity[1] = fdm.state.v
        state.velocity[2] = fdm.state.w
        state.orientation[0] = fdm.state.phi
        state.orientation[1] = fdm.state.theta
        state.orientation[2] = fdm.state.psi
        state.battery = fdm.state.battery_remaining
    
    def _action_to_motor_commands(self, action: np.ndarray) -> np.ndarray:
        """
        Convert high-level action to 4 motor throttle commands.
        
        Input: [throttle, roll_rate, pitch_rate, yaw_rate]
        Output: [m1, m2, m3, m4] throttle (0-1)
        """
        throttle = np.clip(action[0], 0, 1)
        roll = np.clip(action[1], -1, 1) * 0.15  # Scale for mixing
        pitch = np.clip(action[2], -1, 1) * 0.15
        yaw = np.clip(action[3], -1, 1) * 0.1
        
        # X-config motor mixing (matching QuadcopterFDM layout)
        # Motor 1 (front-left, CCW), Motor 2 (front-right, CW)
        # Motor 3 (back-right, CCW), Motor 4 (back-left, CW)
        m1 = throttle + roll + pitch - yaw
        m2 = throttle - roll + pitch + yaw
        m3 = throttle - roll - pitch - yaw
        m4 = throttle + roll - pitch + yaw
        
        return np.clip([m1, m2, m3, m4], 0, 1)
    
    def step(self, state: DroneState, action: np.ndarray, wind: np.ndarray = None) -> Tuple[DroneState, float]:
        """
        Step drone physics forward using JSBSim-grade dynamics.
        
        Args:
            state: Current drone state  
            action: [throttle, roll_rate, pitch_rate, yaw_rate] (0-1, -1 to 1)
            wind: Wind vector [wx, wy, wz] in m/s
            
        Returns:
            Updated state and step reward
        """
        if not state.alive:
            return state, 0.0
            
        reward = 0.0
        old_pos = state.position.copy()
        
        # Get wind
        if wind is None:
            wind = self._get_wind(state.position)
        
        if self.use_jsbsim:
            # === JSBSIM PHYSICS PATH ===
            fdm = self._get_fdm(state.organism_id)
            
            # Sync state to FDM
            self._sync_state_to_fdm(state, fdm)
            
            # Set wind
            fdm.set_wind(wind, turbulence=self.config.turbulence)
            
            # Convert action to motor commands
            motor_cmds = self._action_to_motor_commands(action)
            
            # Step physics
            fdm.step(motor_cmds, dt=self.dt)
            
            # Sync back
            self._sync_fdm_to_state(fdm, state)
            
        else:
            # === SIMPLIFIED PHYSICS FALLBACK ===
            throttle = np.clip(action[0], 0, 1)
            roll_rate = np.clip(action[1], -1, 1) * 3.0
            pitch_rate = np.clip(action[2], -1, 1) * 3.0
            yaw_rate = np.clip(action[3], -1, 1) * 2.0
            
            # Gravity
            gravity = np.array([0, 0, -self.config.gravity * self.config.drone_mass])
            
            # Thrust
            thrust_mag = throttle * self.config.max_thrust
            roll, pitch, yaw = state.orientation
            cr, sr = np.cos(roll), np.sin(roll)
            cp, sp = np.cos(pitch), np.sin(pitch)
            
            thrust_dir = np.array([-sp, cp * sr, cp * cr])
            thrust = thrust_dir * thrust_mag
            
            # Drag
            relative_vel = state.velocity - wind
            speed = np.linalg.norm(relative_vel)
            if speed > 0.01:
                drag_mag = 0.5 * self.config.air_density * self.config.drag_coefficient * 0.04 * speed**2
                drag = -relative_vel / speed * drag_mag
            else:
                drag = np.zeros(3)
            
            # Integration
            total_force = gravity + thrust + drag
            acceleration = total_force / self.config.drone_mass
            state.velocity += acceleration * self.dt
            
            # Velocity limits
            speed = np.linalg.norm(state.velocity)
            if speed > 20.0:
                state.velocity *= 20.0 / speed
            
            state.position += state.velocity * self.dt
            
            # Orientation
            state.orientation[0] += roll_rate * self.dt
            state.orientation[1] += pitch_rate * self.dt
            state.orientation[2] += yaw_rate * self.dt
            state.orientation[0] = np.clip(state.orientation[0], -np.pi/3, np.pi/3)
            state.orientation[1] = np.clip(state.orientation[1], -np.pi/3, np.pi/3)
            state.orientation[2] = state.orientation[2] % (2 * np.pi)
        
        # === BOUNDARIES (common to both physics modes) ===
        
        # Ground collision
        if state.position[2] < self.config.min_altitude:
            if state.velocity[2] < -3.0:
                state.health -= self.config.crash_damage
                reward += self.config.reward_crash
            state.position[2] = self.config.min_altitude
            state.velocity[2] = 0
            state.velocity[:2] *= 0.5
            
        # Ceiling
        if state.position[2] > self.config.max_altitude:
            state.position[2] = self.config.max_altitude
            state.velocity[2] = min(0, state.velocity[2])
            
        # Arena bounds
        half = self.config.arena_size / 2
        for i in range(2):
            if abs(state.position[i]) > half:
                state.position[i] = np.clip(state.position[i], -half, half)
                state.velocity[i] = 0
                reward -= 0.1
                
        # === STATUS UPDATES ===
        
        # Battery drain
        throttle = action[0] if len(action) > 0 else 0.5
        drain_rate = 0.001 * (1 + (throttle - self.config.hover_throttle) * 2)
        state.battery -= drain_rate * self.dt
        state.battery = max(0, state.battery)
        
        if state.battery <= 0:
            state.alive = False
            reward += self.config.reward_death
            
        if state.health <= 0:
            state.alive = False
            reward += self.config.reward_death
            
        # Stats
        state.flight_time += self.dt
        state.distance_traveled += np.linalg.norm(state.position - old_pos)
        
        if state.alive:
            reward += self.config.reward_survival
            reward += self.config.reward_altitude * state.position[2] / 50
            
        state.total_reward += reward
        return state, reward
        
    def _get_wind(self, position: np.ndarray) -> np.ndarray:
        """Get wind vector at position with turbulence."""
        base = np.array([
            np.cos(self.config.wind_direction) * self.config.wind_speed,
            np.sin(self.config.wind_direction) * self.config.wind_speed,
            0
        ])
        alt_factor = 1.0 + position[2] / 50.0
        turb = np.random.randn(3) * self.config.turbulence * self.config.wind_speed
        return (base + turb) * alt_factor


class CocoonDroneArena:
    """
    Main arena for cocoon drone warfare.
    
    Usage:
        arena = CocoonDroneArena(cocoon, mode=DroneGameMode.TAG_BATTLE)
        result = arena.run_episode()
    """
    
    def __init__(self,
                 cocoon,
                 mode: DroneGameMode = DroneGameMode.FREE_FLY,
                 config: DroneArenaConfig = None,
                 team_split: str = "half",  # "half", "all_blue", "all_red", "random"
                 visualize: bool = False,
                 event_emitter: Callable = None,
                 global_config: Dict[str, Any] = None,
                 enable_training: bool = False,
                 train_interval: int = 100,
                 cocoon_red = None,
                 verbose: bool = False,
                 num_drones: int = None):
        """
        Args:
            cocoon: CocoonAgent instance (blue team)
            mode: Game mode to run
            config: Arena configuration
            team_split: How to split organisms into teams
            visualize: Whether to show live 3D view
            event_emitter: For causation events
            global_config: Global config dict (for reading neural.language_game_bridge settings)
            enable_training: Enable post-play training during gameplay
            train_interval: Train every N steps when training enabled
            cocoon_red: Optional second cocoon for red team (cocoon vs cocoon)
            verbose: Print detailed per-step organism actions and state
            num_drones: Limit number of drones (uses all cocoon organisms if None)
        """
        self.cocoon = cocoon
        self.cocoon_red = cocoon_red  # For cocoon vs cocoon battles
        self.mode = mode
        self.config = config or DroneArenaConfig()
        self.visualize = visualize
        self.verbose = verbose  # Detailed logging
        self.event_emitter = event_emitter
        self.global_config = global_config or {}
        
        # For verbose logging - stores last action index from cocoon
        self._last_action_indices = {}
        
        # For training - stores last observation per drone (like sphere_arena's last_observations)
        self._last_observations = {}
        
        # POST-PLAY TRAINING SYSTEM (like sphere_arena)
        # When enabled, organisms learn from drone experiences:
        #   - Actions stored in experience buffer
        #   - Rewards tracked per step
        #   - Weights updated via agent.train_step() every train_interval steps
        self.enable_training = enable_training
        self.train_interval = train_interval
        self.training_losses: List[float] = []
        self.step_count = 0
        
        # Get organisms - limit to num_drones if specified
        available_organisms = len(cocoon.brains)
        if num_drones is not None and num_drones < available_organisms:
            self.num_organisms = num_drones
            self.organism_names = cocoon.organism_names[:num_drones]
        else:
            self.num_organisms = available_organisms
            self.organism_names = cocoon.organism_names
        
        # Physics engine
        self.physics = DronePhysics(self.config)
        
        # Drone states
        self.drones: Dict[str, DroneState] = {}
        
        # Game state
        self.game_state = GameState(mode=mode)
        
        # Language-Game Bridge for vocabulary-enhanced actions
        self.language_bridge: Optional[LanguageGameBridge] = None
        self.use_language_bridge = LANGUAGE_BRIDGE_AVAILABLE
        if self.use_language_bridge:
            try:
                # Read config from global_config (meta-brain tunable) with fallbacks
                bridge_config = self.global_config.get('neural', {}).get('language_game_bridge', {})
                bias_strength = bridge_config.get('bias_strength', 0.3)
                learning_rate = bridge_config.get('learning_rate', 0.1)
                
                self.language_bridge = LanguageGameBridge(
                    atomic_language=getattr(cocoon, 'atomic_language', None),
                    knowledge_web=getattr(cocoon, 'knowledge_web', None),
                    context="drone",
                    bias_strength=bias_strength,
                    learning_rate=learning_rate
                )
                logger.info(f"🧠 LanguageGameBridge active - bias={bias_strength}, lr={learning_rate}")
            except Exception as e:
                logger.warning(f"LanguageGameBridge init failed: {e}")
                self.use_language_bridge = False
        
        # Assign teams
        self._assign_teams(team_split)
        
        # Setup game mode
        self._setup_game_mode()
        
        # PyFlyt Aviary (real quadcopter rendering)
        self._aviary = None
        self._drone_indices = {}  # Maps drone name -> aviary index
        
        # Legacy PyBullet fallback
        self._physics_client = None
        self._drone_bodies = {}
        
        # Initialize visualization if requested
        if self.visualize:
            if _lazy_load_pyflyt():
                self._init_pyflyt_visualization()
            elif _lazy_load_pybullet():
                self._init_pybullet_visualization()
            else:
                logger.warning("No visualization backend available (install PyFlyt or PyBullet)")
        
        logger.info(f"🛸 CocoonDroneArena created: {self.num_organisms} organisms, mode={mode.value}")
        if enable_training:
            logger.info(f"   📚 Training enabled: interval={train_interval} steps")
            
    def update_bridge_parameters(self, bias_strength: Optional[float] = None,
                                  learning_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Dynamically update LanguageGameBridge parameters at runtime.
        
        Called by ConfigTuner to propagate tuning changes to the cocoon's bridge.
        
        Args:
            bias_strength: New bias strength (0.0-1.0), or None to keep current
            learning_rate: New learning rate (0.01-0.5), or None to keep current
            
        Returns:
            Dict with old and new values for logging
        """
        if not self.language_bridge:
            return {'error': 'No language bridge active'}
        
        if hasattr(self.language_bridge, 'update_parameters'):
            return self.language_bridge.update_parameters(
                bias_strength=bias_strength,
                learning_rate=learning_rate
            )
        
        # Fallback for older bridges without update_parameters
        changes = {}
        if bias_strength is not None and hasattr(self.language_bridge, 'bias_computer'):
            old = getattr(self.language_bridge.bias_computer, 'bias_strength', 0.3)
            self.language_bridge.bias_computer.bias_strength = bias_strength
            changes['bias_strength_old'] = old
            changes['bias_strength_new'] = bias_strength
            
        if learning_rate is not None and hasattr(self.language_bridge, 'learner'):
            old = getattr(self.language_bridge.learner, 'learning_rate', 0.1)
            self.language_bridge.learner.learning_rate = learning_rate
            changes['learning_rate_old'] = old
            changes['learning_rate_new'] = learning_rate
            
        return changes
        if cocoon_red:
            logger.info(f"   ⚔️ Cocoon vs Cocoon: Blue has {len(cocoon.brains)} orgs, Red has {len(cocoon_red.brains)} orgs")
    
    def _init_pyflyt_visualization(self):
        """Initialize PyFlyt Aviary with real quadcopter models."""
        if not _lazy_load_pyflyt():
            logger.warning("PyFlyt not available for visualization")
            return
        
        print(f"🚁 Initializing PyFlyt Aviary with {len(self.drones)} quadcopters...")
        
        try:
            # Build position and orientation arrays for all drones
            drone_names = list(self.drones.keys())
            num_drones = len(drone_names)
            
            start_positions = np.zeros((num_drones, 3))
            start_orientations = np.zeros((num_drones, 3))
            
            for i, name in enumerate(drone_names):
                drone = self.drones[name]
                start_positions[i] = drone.position
                start_orientations[i] = drone.orientation
                self._drone_indices[name] = i
                
                team_emoji = "🔵" if drone.team == "blue" else "🔴"
                print(f"   {team_emoji} {name}: pos={drone.position.tolist()}")
            
            # PyFlyt requires physics_hz to be multiple of control_hz (default 120)
            # Use 240 Hz for smooth physics (240 = 120 * 2)
            pyflyt_physics_hz = 240
            
            # Create PyFlyt Aviary with real quadcopter URDFs
            self._aviary = Aviary(
                start_pos=start_positions,
                start_orn=start_orientations,
                drone_type="quadx",  # Real quadcopter with propellers
                render=True,
                physics_hz=pyflyt_physics_hz,
                world_scale=2.0  # Larger world for arena
            )
            
            # Store physics ratio for step timing
            self._pyflyt_steps_per_frame = pyflyt_physics_hz // self.config.target_fps
            
            # === VISUAL QUALITY MAXED OUT ===
            # Kill the ugly debug panels
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_GUI, 0)
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)
            
            # Enable all quality options
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_SHADOWS, 1)
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_RENDERING, 1)
            self._aviary.configureDebugVisualizer(self._aviary.COV_ENABLE_PLANAR_REFLECTION, 1)
            
            # Better lighting - move light to create dramatic shadows
            self._aviary.configureDebugVisualizer(
                lightPosition=[50, 30, 100]  # Sun position
            )
            
            # Set background color (sky blue instead of gray)
            self._aviary.configureDebugVisualizer(
                rgbBackground=[0.529, 0.808, 0.922]  # Light sky blue
            )
            
            # Camera setup - cinematic angle
            self._aviary.resetDebugVisualizerCamera(
                cameraDistance=35,
                cameraYaw=30,
                cameraPitch=-20,
                cameraTargetPosition=[0, 0, 10]
            )
            
            # Make the ground look better - add a textured plane
            try:
                # Create a larger, better looking ground
                ground_id = self._aviary.loadURDF(
                    "plane.urdf",
                    basePosition=[0, 0, -0.05],
                    useFixedBase=True
                )
                # Change ground color to grass-like green
                self._aviary.changeVisualShape(ground_id, -1, 
                    rgbaColor=[0.3, 0.5, 0.3, 1.0])
            except:
                pass
            
            # Set up team colors with BIGGER, BRIGHTER markers
            for name, drone in self.drones.items():
                idx = self._drone_indices[name]
                drone_id = self._aviary.drones[idx].Id
                
                if drone.team == "blue":
                    # Bright blue team marker - vertical beam
                    self._aviary.addUserDebugLine(
                        [0, 0, 0.3], [0, 0, 1.0],
                        lineColorRGB=[0.0, 0.5, 1.0],
                        lineWidth=10,
                        parentObjectUniqueId=drone_id,
                        parentLinkIndex=-1
                    )
                    # Add horizontal ring
                    for angle in range(0, 360, 45):
                        rad = angle * 3.14159 / 180
                        self._aviary.addUserDebugLine(
                            [0.3 * np.cos(rad), 0.3 * np.sin(rad), 0.3],
                            [0.3 * np.cos(rad + 0.8), 0.3 * np.sin(rad + 0.8), 0.3],
                            lineColorRGB=[0.0, 0.5, 1.0],
                            lineWidth=3,
                            parentObjectUniqueId=drone_id,
                            parentLinkIndex=-1
                        )
                else:
                    # Bright red team marker
                    self._aviary.addUserDebugLine(
                        [0, 0, 0.3], [0, 0, 1.0],
                        lineColorRGB=[1.0, 0.2, 0.0],
                        lineWidth=10,
                        parentObjectUniqueId=drone_id,
                        parentLinkIndex=-1
                    )
                    for angle in range(0, 360, 45):
                        rad = angle * 3.14159 / 180
                        self._aviary.addUserDebugLine(
                            [0.3 * np.cos(rad), 0.3 * np.sin(rad), 0.3],
                            [0.3 * np.cos(rad + 0.8), 0.3 * np.sin(rad + 0.8), 0.3],
                            lineColorRGB=[1.0, 0.2, 0.0],
                            lineWidth=3,
                            parentObjectUniqueId=drone_id,
                            parentLinkIndex=-1
                        )
            
            print(f"✅ PyFlyt Aviary ready with {num_drones} QuadX drones (enhanced visuals)")
            logger.info(f"🚁 PyFlyt visualization initialized with {num_drones} quadcopters")
            
        except Exception as e:
            logger.error(f"PyFlyt visualization init failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up any partial PyFlyt/PyBullet state before fallback
            if self._aviary is not None:
                try:
                    self._aviary.disconnect()
                except:
                    pass
            self._aviary = None
            self._drone_indices = {}
            
            # Fall back to PyBullet if available
            if _lazy_load_pybullet():
                logger.info("Falling back to PyBullet visualization...")
                self._init_pybullet_visualization()
            else:
                self.visualize = False

    def _render_pyflyt(self):
        """Update PyFlyt drone positions for visualization."""
        if self._aviary is None:
            return
        
        # Update each drone's position in the Aviary
        for name, drone in self.drones.items():
            if name in self._drone_indices:
                idx = self._drone_indices[name]
                
                # Set drone state in Aviary
                pos = drone.position
                orn = self._aviary.getQuaternionFromEuler(drone.orientation.tolist())
                vel = drone.velocity
                
                # Update the drone body directly in PyBullet (Aviary inherits from BulletClient)
                self._aviary.resetBasePositionAndOrientation(
                    self._aviary.drones[idx].Id,
                    pos.tolist(),
                    orn
                )
                self._aviary.resetBaseVelocity(
                    self._aviary.drones[idx].Id,
                    linearVelocity=vel.tolist(),
                    angularVelocity=[0, 0, drone.orientation[2] * 0.1]
                )
                
                # Draw flight trail (fading tail effect)
                if hasattr(self, '_last_positions'):
                    if name in self._last_positions:
                        last_pos = self._last_positions[name]
                        dist = np.linalg.norm(pos - last_pos)
                        if dist > 0.3:  # Only draw if moved enough
                            color = [0.0, 0.5, 1.0] if drone.team == "blue" else [1.0, 0.3, 0.0]
                            # Trail line with lifetime (fades after 2 seconds)
                            self._aviary.addUserDebugLine(
                                last_pos.tolist(),
                                pos.tolist(),
                                lineColorRGB=color,
                                lineWidth=2,
                                lifeTime=2.0  # Disappears after 2 seconds
                            )
                            self._last_positions[name] = pos.copy()
                else:
                    self._last_positions = {}
                if name not in getattr(self, '_last_positions', {}):
                    if not hasattr(self, '_last_positions'):
                        self._last_positions = {}
                    self._last_positions[name] = pos.copy()
        
        # Dynamic camera - smooth orbit around action
        alive_positions = [d.position for d in self.drones.values() if d.alive]
        if alive_positions:
            center = np.mean(alive_positions, axis=0)
            # Cinematic slow orbit
            orbit_speed = 3  # degrees per second
            yaw = 30 + (self.game_state.time_elapsed * orbit_speed) % 360
            self._aviary.resetDebugVisualizerCamera(
                cameraDistance=35,
                cameraYaw=yaw,
                cameraPitch=-20,
                cameraTargetPosition=center.tolist()
            )
        
        # Step Aviary physics for visual update
        self._aviary.step()
    
    def _init_pybullet_visualization(self):
        """Initialize PyBullet 3D visualization (fallback)."""
        if not _lazy_load_pybullet():
            logger.warning("PyBullet not available for visualization")
            return
        
        print(f"🎮 Initializing PyBullet fallback with {len(self.drones)} drones...")
        for name, drone in self.drones.items():
            print(f"   Drone {name}: pos={drone.position}, team={drone.team}")
            
        try:
            # Connect to PyBullet with GUI
            self._physics_client = p.connect(p.GUI)
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            
            # Setup scene
            p.setGravity(0, 0, -self.config.gravity)
            p.setRealTimeSimulation(0)  # We control timing
            
            # Load ground plane
            p.loadURDF("plane.urdf")
            
            # Disable rendering during setup for speed
            p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_TINY_RENDERER, 0)
            
            # Create drone visual bodies - BIGGER spheres (2m radius)
            self._drone_bodies = {}
            for name, drone in self.drones.items():
                # Color based on team
                if drone.team == "blue":
                    color = [0.1, 0.3, 1.0, 1.0]
                else:
                    color = [1.0, 0.1, 0.1, 1.0]
                
                # Create visual sphere - 2m radius so visible from distance
                visual_id = p.createVisualShape(
                    p.GEOM_SPHERE,
                    radius=2.0,
                    rgbaColor=color
                )
                body_id = p.createMultiBody(
                    baseMass=0,
                    baseVisualShapeIndex=visual_id,
                    basePosition=[drone.position[0], drone.position[1], drone.position[2]]
                )
                self._drone_bodies[name] = body_id
                print(f"   Created body {body_id} for {name} at {drone.position}")
            
            # Re-enable rendering
            p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)
            
            # Camera setup - close view tracking center of action
            p.resetDebugVisualizerCamera(
                cameraDistance=80,
                cameraYaw=45,
                cameraPitch=-30,
                cameraTargetPosition=[0, 0, 15]
            )
            
            print(f"✅ PyBullet ready with {len(self._drone_bodies)} drone bodies")
                
            logger.info(f"🎮 PyBullet 3D visualization initialized with {len(self._drone_bodies)} drones")
            
        except Exception as e:
            logger.error(f"PyBullet visualization init failed: {e}")
            import traceback
            traceback.print_exc()
            self._physics_client = None
            self.visualize = False
    
    def _render_pybullet(self):
        """Update PyBullet drone positions for visualization."""
        if self._physics_client is None:
            return
            
        for name, drone in self.drones.items():
            if name in self._drone_bodies:
                body_id = self._drone_bodies[name]
                
                # Update position
                pos = [drone.position[0], drone.position[1], drone.position[2]]
                
                # Convert orientation (roll, pitch, yaw) to quaternion
                orn = p.getQuaternionFromEuler([
                    drone.orientation[0],
                    drone.orientation[1],
                    drone.orientation[2]
                ])
                
                p.resetBasePositionAndOrientation(body_id, pos, orn)
                
                # Gray out dead drones
                if not drone.alive:
                    p.changeVisualShape(body_id, -1, rgbaColor=[0.3, 0.3, 0.3, 0.5])
        
        # Step PyBullet to update visuals (no physics, just rendering)
        p.stepSimulation()
    
    def close_visualization(self):
        """Clean up visualization (PyFlyt or PyBullet)."""
        # Close PyFlyt Aviary
        if self._aviary is not None:
            try:
                self._aviary.disconnect()
            except:
                pass
            self._aviary = None
            self._drone_indices = {}
            
        # Close PyBullet fallback
        if self._physics_client is not None:
            try:
                p.disconnect(self._physics_client)
            except:
                pass
            self._physics_client = None
            self._drone_bodies = {}
        
    def _assign_teams(self, team_split: str):
        """Assign organisms to teams and spawn drones.
        
        For cocoon vs cocoon battles (cocoon_red is set):
            - Blue team = all organisms from self.cocoon
            - Red team = all organisms from self.cocoon_red
        
        For single cocoon battles:
            - Uses team_split to divide organisms
        """
        if self.cocoon_red is not None:
            # COCOON VS COCOON MODE
            # Blue team from primary cocoon
            for i, name in enumerate(self.cocoon.organism_names):
                spawn_pos = self._get_spawn_position(i, "blue")
                self.drones[f"blue_{name}"] = DroneState(
                    organism_id=name,
                    organism_index=i,
                    team="blue",
                    position=spawn_pos,
                    cocoon_ref=self.cocoon  # Track which cocoon controls this drone
                )
            
            # Red team from secondary cocoon
            for i, name in enumerate(self.cocoon_red.organism_names):
                spawn_pos = self._get_spawn_position(i, "red")
                self.drones[f"red_{name}"] = DroneState(
                    organism_id=name,
                    organism_index=i,
                    team="red",
                    position=spawn_pos,
                    cocoon_ref=self.cocoon_red  # Track which cocoon controls this drone
                )
                
            # Update organism counts
            self.num_organisms = len(self.cocoon.brains) + len(self.cocoon_red.brains)
            self.organism_names = [f"blue_{n}" for n in self.cocoon.organism_names] + \
                                  [f"red_{n}" for n in self.cocoon_red.organism_names]
        else:
            # SINGLE COCOON MODE - split into teams
            for i, name in enumerate(self.organism_names):
                # Determine team
                if team_split == "half":
                    team = "blue" if i < self.num_organisms // 2 else "red"
                elif team_split == "all_blue":
                    team = "blue"
                elif team_split == "all_red":
                    team = "red"
                else:  # random
                    team = "blue" if np.random.random() > 0.5 else "red"
                    
                # Spawn position based on team
                spawn_pos = self._get_spawn_position(i, team)
                
                # Create drone state
                self.drones[name] = DroneState(
                    organism_id=name,
                    organism_index=i,
                    team=team,
                    position=spawn_pos,
                    cocoon_ref=self.cocoon  # All from same cocoon
                )
            
        # Count teams
        self.game_state.blue_alive = sum(1 for d in self.drones.values() if d.team == "blue")
        self.game_state.red_alive = sum(1 for d in self.drones.values() if d.team == "red")
        
    def _get_spawn_position(self, index: int, team: str) -> np.ndarray:
        """Get spawn position for a drone."""
        grid_size = int(np.ceil(np.sqrt(self.num_organisms / 2))) + 1
        spacing = 5.0
        
        # Team-based X offset - close enough for quick contact
        # At arena_size=100, teams spawn 10m from center (20m apart total)
        team_offset = -self.config.arena_size / 10 if team == "blue" else self.config.arena_size / 10
        
        # Grid position within team
        team_index = index if team == "blue" else index - self.num_organisms // 2
        row = team_index // grid_size
        col = team_index % grid_size
        
        return np.array([
            team_offset + (col - grid_size/2) * spacing,
            (row - grid_size/2) * spacing,
            10.0 + np.random.uniform(0, 5)
        ])
        
    def _setup_game_mode(self):
        """Configure arena for specific game mode."""
        if self.mode == DroneGameMode.FREE_FLY:
            # Basic flight - add waypoints for exploration reward
            self.game_state.waypoints = [
                np.array([0, 0, 20]),
                np.array([30, 30, 25]),
                np.array([-30, 30, 15]),
                np.array([-30, -30, 20]),
                np.array([30, -30, 25]),
            ]
            self.game_state.waypoint_radius = 5.0
            
        elif self.mode == DroneGameMode.FORMATION:
            # Formation targets - ideal positions relative to centroid
            self.game_state.formation_offsets = [
                np.array([5, 0, 0]),    # Right
                np.array([-5, 0, 0]),   # Left
                np.array([0, 5, 0]),    # Front
                np.array([0, -5, 0]),   # Back
                np.array([0, 0, 3]),    # High
                np.array([0, 0, -3]),   # Low
            ]
            
        elif self.mode == DroneGameMode.PURSUIT:
            # Moving target for pursuit training
            self.game_state.target_pos = np.array([0.0, 0.0, 15.0])
            self.game_state.target_vel = np.array([3.0, 2.0, 0.0])  # m/s
            self.game_state.pursuit_radius = 5.0
            
        elif self.mode == DroneGameMode.ZONE_CONTROL:
            # Create control zones
            self.game_state.zones = [
                {"center": np.array([0, 0, 20]), "radius": 15.0, "controller": None},
                {"center": np.array([30, 30, 15]), "radius": 10.0, "controller": None},
                {"center": np.array([-30, -30, 15]), "radius": 10.0, "controller": None},
            ]
            
        elif self.mode == DroneGameMode.CAPTURE_FLAG:
            # Flag positions
            self.game_state.blue_flag_pos = np.array([-50, 0, 5])
            self.game_state.red_flag_pos = np.array([50, 0, 5])
            
        elif self.mode == DroneGameMode.SURVIVAL:
            # Shrinking arena boundary for survival mode
            self.game_state.arena_radius = self.config.arena_size / 2
            self.game_state.shrink_rate = 0.5  # meters per second
            self.game_state.min_arena_radius = 20.0
            
        elif self.mode == DroneGameMode.ESCORT:
            # Mark first drone of each team as VIP
            blue_vip_set = False
            red_vip_set = False
            for drone in self.drones.values():
                if drone.team == "blue" and not blue_vip_set:
                    drone.health = 2.0  # VIP has more health
                    drone.is_vip = True
                    self.game_state.blue_vip = drone.organism_id
                    blue_vip_set = True
                    logger.info(f"Blue VIP: {drone.organism_id[:8]}")
                elif drone.team == "red" and not red_vip_set:
                    drone.health = 2.0
                    drone.is_vip = True
                    self.game_state.red_vip = drone.organism_id
                    red_vip_set = True
                    logger.info(f"Red VIP: {drone.organism_id[:8]}")
                    
    def get_observation(self, drone: DroneState) -> np.ndarray:
        """
        Get observation for a drone.
        
        Returns standard RL observation vector.
        """
        # Self state (11 values)
        self_state = np.concatenate([
            drone.position / 100,  # Normalize
            drone.velocity / 10,
            drone.orientation / np.pi,
            [drone.health, drone.battery]
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # SWARM AWARENESS - Like sphere_arena's shared ball position
        # Each drone has full knowledge of team and enemy positions
        # This enables triangulation and coordinated maneuvers
        # ═══════════════════════════════════════════════════════════════════
        
        allies = [d for d in self.drones.values() if d.team == drone.team and d.organism_id != drone.organism_id and d.alive]
        enemies = [d for d in self.drones.values() if d.team != drone.team and d.alive]
        
        # Team centroid (3 values) - where are my allies clustered?
        if allies:
            ally_positions = np.array([a.position for a in allies])
            team_centroid = ally_positions.mean(axis=0)
            team_centroid_rel = (team_centroid - drone.position) / 50
        else:
            team_centroid_rel = np.zeros(3)
            
        # Enemy centroid (3 values) - where are enemies clustered?
        if enemies:
            enemy_positions = np.array([e.position for e in enemies])
            enemy_centroid = enemy_positions.mean(axis=0)
            enemy_centroid_rel = (enemy_centroid - drone.position) / 50
        else:
            enemy_centroid_rel = np.zeros(3)
        
        # Nearest ally (6 values - relative pos, vel of closest)
        if allies:
            nearest_ally = min(allies, key=lambda a: np.linalg.norm(a.position - drone.position))
            ally_rel = np.concatenate([
                (nearest_ally.position - drone.position) / 50,
                (nearest_ally.velocity - drone.velocity) / 10
            ])
        else:
            ally_rel = np.zeros(6)
            
        # Nearest enemy (6 values)
        if enemies:
            nearest_enemy = min(enemies, key=lambda e: np.linalg.norm(e.position - drone.position))
            enemy_rel = np.concatenate([
                (nearest_enemy.position - drone.position) / 50,
                (nearest_enemy.velocity - drone.velocity) / 10
            ])
            nearest_enemy_dist = np.linalg.norm(nearest_enemy.position - drone.position) / 100
        else:
            enemy_rel = np.zeros(6)
            nearest_enemy_dist = 1.0  # Max distance
        
        # Second nearest enemy (for triangulation - 3 values)
        if len(enemies) >= 2:
            sorted_enemies = sorted(enemies, key=lambda e: np.linalg.norm(e.position - drone.position))
            second_enemy = sorted_enemies[1]
            second_enemy_rel = (second_enemy.position - drone.position) / 50
        else:
            second_enemy_rel = np.zeros(3)
            
        # Game mode specific (6 values)
        mode_obs = np.zeros(6)
        if self.mode == DroneGameMode.ZONE_CONTROL and self.game_state.zones:
            # Distance to nearest zone
            zone = self.game_state.zones[0]
            zone_rel = (zone["center"] - drone.position) / 50
            mode_obs[:3] = zone_rel
            mode_obs[3] = 1.0 if drone.in_zone else 0.0
            
        elif self.mode == DroneGameMode.CAPTURE_FLAG:
            # Distance to enemy flag
            target_flag = self.game_state.red_flag_pos if drone.team == "blue" else self.game_state.blue_flag_pos
            if target_flag is not None:
                mode_obs[:3] = (target_flag - drone.position) / 50
            mode_obs[3] = 1.0 if drone.has_flag else 0.0
            
        # Team counts (2 values) - situational awareness
        team_count = len(allies) + 1  # Include self
        enemy_count = len(enemies)
        counts = np.array([team_count / 10, enemy_count / 10])
            
        # Combine: 11 + 3 + 3 + 6 + 6 + 3 + 6 + 1 + 2 = 41 values, pad to 64
        obs = np.concatenate([
            self_state,           # 11: own state
            team_centroid_rel,    # 3: where is my team?
            enemy_centroid_rel,   # 3: where are enemies?
            ally_rel,             # 6: nearest ally
            enemy_rel,            # 6: nearest enemy
            second_enemy_rel,     # 3: second nearest enemy (triangulation)
            mode_obs,             # 6: game-specific
            [nearest_enemy_dist], # 1: distance to threat
            counts,               # 2: force counts
        ])
        if len(obs) < 64:
            obs = np.pad(obs, (0, 64 - len(obs)))
            
        return obs.astype(np.float32)
        
    def get_action(self, drone: DroneState) -> np.ndarray:
        """Get action from organism brain, enhanced by vocabulary."""
        obs = self.get_observation(drone)
        
        try:
            # Get discrete action from cocoon
            # explore=True when training enabled so organisms try different strategies
            action_idx = self.cocoon.get_action(obs, explore=self.enable_training)
            
            # Apply vocabulary bias if bridge available
            if self.use_language_bridge and self.language_bridge:
                # Interpret observation linguistically
                activated = self.language_bridge.interpret_observation(obs)
                
                # Get bias vector
                bias = self.language_bridge.get_action_bias(activated)
                
                # Apply bias: if bias strongly suggests different action, consider it
                if bias is not None and len(bias) == 6:
                    bias_action = int(np.argmax(bias))
                    bias_strength = bias[bias_action]
                    
                    # If bias is strong enough and different from neural choice, blend
                    if bias_strength > 0.3 and bias_action != action_idx:
                        # 30% chance to use vocabulary-suggested action
                        if np.random.random() < 0.3:
                            action_idx = bias_action
                            logger.debug(f"🧠 Vocab override: {action_idx} (bias={bias_strength:.2f})")
            
            # Convert to motor commands
            return self._discrete_to_continuous(action_idx)
        except Exception as e:
            logger.debug(f"Action error for {drone.organism_id}: {e}")
            # Default hover
            return np.array([self.config.hover_throttle, 0, 0, 0])
    
    def get_all_actions_fast(self) -> Dict[str, np.ndarray]:
        """
        Get actions for all alive drones in one batch.
        Much faster than calling get_action per drone.
        
        For cocoon vs cocoon battles, uses drone.cocoon_ref to get action
        from the correct cocoon (blue vs red).
        """
        actions = {}
        self._last_action_indices = {}  # Store for verbose logging
        alive_drones = [(name, drone) for name, drone in self.drones.items() if drone.alive]
        
        if not alive_drones:
            return actions
            
        # Get actions from appropriate cocoons
        for name, drone in alive_drones:
            obs = self.get_observation(drone)
            try:
                # Use drone's cocoon_ref if set (cocoon vs cocoon mode)
                # Otherwise fall back to self.cocoon
                cocoon = drone.cocoon_ref if drone.cocoon_ref else self.cocoon
                # explore=True when training enabled for better learning
                action_idx = cocoon.get_action(obs, explore=self.enable_training)
                self._last_action_indices[name] = action_idx  # Store for verbose
                actions[name] = self._discrete_to_continuous(action_idx)
            except:
                self._last_action_indices[name] = 1  # hover fallback
                actions[name] = np.array([self.config.hover_throttle, 0, 0, 0])
                
        return actions
        
    def _discrete_to_continuous(self, action: int) -> np.ndarray:
        """Convert discrete action (0-5) to [throttle, roll, pitch, yaw]."""
        hover = self.config.hover_throttle
        
        # Action semantics from cocoon training:
        # 0: MOVE - forward thrust
        # 1: COOPERATE - hover/hold position
        # 2: COMPETE - aggressive maneuver
        # 3: REST - descend slowly
        # 4: REPRODUCE - turn/scan
        # 5: ISOLATE - evasive maneuver
        
        # Increased magnitudes for faster gameplay
        action_map = {
            0: [hover + 0.15, 0.0, 0.6, 0.0],      # Forward (faster)
            1: [hover, 0.0, 0.0, 0.0],              # Hover
            2: [hover + 0.2, 0.4, 0.5, 0.2],       # Aggressive (faster)
            3: [hover - 0.05, 0.0, 0.0, 0.0],      # Descend
            4: [hover + 0.05, 0.0, 0.0, 0.6],      # Turn (faster)
            5: [hover + 0.1, 0.5, -0.4, 0.4],      # Evasive (faster)
        }
        
        return np.array(action_map.get(action, action_map[1]))
        
    def step(self) -> Dict[str, float]:
        """
        Step the simulation forward.
        
        Returns:
            Dict mapping organism_id to reward
        """
        rewards = {}
        
        # Get all actions at once (faster)
        all_actions = self.get_all_actions_fast()
        
        # Action names for verbose output
        ACTION_NAMES = {0: "FORWARD", 1: "HOVER", 2: "ATTACK", 3: "DESCEND", 4: "TURN", 5: "EVADE"}
        
        # Verbose header every 60 steps (1 second)
        if self.verbose and self.game_state.step_count % 60 == 0:
            print(f"\n{'='*80}")
            print(f"[T={self.game_state.time_elapsed:.1f}s] STEP {self.game_state.step_count}")
            print(f"{'='*80}")
        
        # Step physics for all drones
        for drone_id, drone in self.drones.items():
            if not drone.alive:
                rewards[drone_id] = 0.0
                continue
                
            # Get pre-computed action
            action = all_actions.get(drone_id, np.array([self.config.hover_throttle, 0, 0, 0]))
            
            # Store old state for delta computation
            old_pos = drone.position.copy()
            old_vel = drone.velocity.copy()
            
            # Step physics
            _, reward = self.physics.step(drone, action)
            rewards[drone_id] = reward
            
            # === VERBOSE OUTPUT ===
            if self.verbose:
                # Compute deltas
                delta_pos = drone.position - old_pos
                delta_vel = drone.velocity - old_vel
                speed = np.linalg.norm(drone.velocity)
                
                # Get action index from cocoon decision (stored in get_all_actions_fast)
                action_idx = self._last_action_indices.get(drone_id, 1)
                
                team = "🔵" if drone.team == "blue" else "🔴"
                action_name = ACTION_NAMES.get(action_idx, "UNK")
                
                # Full output every 30 steps (0.5s), compact output every step
                if self.game_state.step_count % 30 == 0:
                    print(f"  {team} {drone_id[:8]}: {action_name:7s} | "
                          f"pos=[{drone.position[0]:6.1f},{drone.position[1]:6.1f},{drone.position[2]:5.1f}] | "
                          f"vel=[{drone.velocity[0]:5.2f},{drone.velocity[1]:5.2f},{drone.velocity[2]:5.2f}] | "
                          f"spd={speed:4.1f}m/s | "
                          f"Δpos=[{delta_pos[0]:+5.2f},{delta_pos[1]:+5.2f},{delta_pos[2]:+5.2f}] | "
                          f"hp={drone.health:.0%} bat={drone.battery:.0%} | "
                          f"r={reward:+.3f}")
                else:
                    # Compact single-line per drone with raw action values
                    print(f"  {team}{drone_id[:6]}:{action_name:4s}({action_idx}) "
                          f"[{action[0]:.2f},{action[1]:+.2f},{action[2]:+.2f},{action[3]:+.2f}] "
                          f"z={drone.position[2]:.1f} v={speed:.1f} r={reward:+.2f}")
            
        # Process game mode logic
        mode_rewards = self._process_game_mode()
        for drone_id, r in mode_rewards.items():
            rewards[drone_id] = rewards.get(drone_id, 0.0) + r
            if self.verbose and abs(r) > 0.01:
                print(f"    📋 {drone_id[:8]}: mode_reward={r:+.3f}")
            
        # Process combat (if applicable)
        if self.mode in [DroneGameMode.TAG_BATTLE, DroneGameMode.SURVIVAL, 
                         DroneGameMode.CAPTURE_FLAG, DroneGameMode.ESCORT]:
            combat_rewards = self._process_combat()
            for drone_id, r in combat_rewards.items():
                rewards[drone_id] = rewards.get(drone_id, 0.0) + r
                if self.verbose and abs(r) > 0.01:
                    print(f"    ⚔️  {drone_id[:8]}: combat_reward={r:+.3f}")
                
        # Process collisions
        collision_rewards = self._process_collisions()
        for drone_id, r in collision_rewards.items():
            rewards[drone_id] = rewards.get(drone_id, 0.0) + r
            if self.verbose and abs(r) > 0.01:
                print(f"    💥 {drone_id[:8]}: collision_reward={r:+.3f}")
        
        # === STORE EXPERIENCES FOR TRAINING ===
        # Aligned with sphere_arena training pattern:
        # - Store (last_obs, action, reward, current_obs, done) tuples
        # - Pad observations to match brain input_dim
        # - Use agent.experience_buffers[organism_idx].add() directly
        if self.enable_training:
            for drone_id, drone in self.drones.items():
                if not drone.alive:
                    continue
                
                org_idx = drone.organism_index
                
                # Skip if no last observation stored
                if drone_id not in self._last_observations:
                    continue
                    
                last_obs = self._last_observations[drone_id]
                action_idx = self._last_action_indices.get(drone_id, 1)
                reward = rewards.get(drone_id, 0.0)
                next_obs = self.get_observation(drone)
                done = not drone.alive or self.game_state.finished
                
                # Get cocoon for this drone
                cocoon = drone.cocoon_ref if drone.cocoon_ref else self.cocoon
                
                # Pad observations to match brain input_dim (like sphere_arena)
                if hasattr(cocoon, 'brains') and org_idx < len(cocoon.brains):
                    brain = cocoon.brains[org_idx]
                    target_dim = getattr(brain, 'input_dim', getattr(brain, 'input_size', 64))
                    
                    last_obs = np.asarray(last_obs, dtype=np.float32).flatten()
                    if len(last_obs) < target_dim:
                        last_obs = np.pad(last_obs, (0, target_dim - len(last_obs)))
                    elif len(last_obs) > target_dim:
                        last_obs = last_obs[:target_dim]
                    
                    next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
                    if len(next_obs) < target_dim:
                        next_obs = np.pad(next_obs, (0, target_dim - len(next_obs)))
                    elif len(next_obs) > target_dim:
                        next_obs = next_obs[:target_dim]
                
                # Store directly to experience buffer (like sphere_arena)
                if hasattr(cocoon, 'experience_buffers') and org_idx < len(cocoon.experience_buffers):
                    try:
                        cocoon.experience_buffers[org_idx].add(
                            state=last_obs,
                            action=action_idx,
                            reward=reward,
                            next_state=next_obs,
                            done=done,
                            input_tokens=None,
                            target_tokens=None,
                            vp_value=0.5
                        )
                    except Exception as e:
                        logger.debug(f"Failed to store experience: {e}")
        
        # Store current observations for next step
        for drone_id, drone in self.drones.items():
            if drone.alive:
                self._last_observations[drone_id] = self.get_observation(drone)
            
        # Update game state
        self.game_state.step_count += 1
        self.game_state.time_elapsed += 1.0 / self.config.target_fps
        self.game_state.blue_alive = sum(1 for d in self.drones.values() if d.team == "blue" and d.alive)
        self.game_state.red_alive = sum(1 for d in self.drones.values() if d.team == "red" and d.alive)
        
        # Check win conditions
        self._check_win_conditions()
        
        # Increment step count for training
        self.step_count += 1
        
        # POST-PLAY TRAINING: Train on accumulated experiences
        if self.enable_training and self.step_count % self.train_interval == 0:
            self._do_training_step()
        
        # Render 3D visualization if enabled
        if self.visualize:
            if self._aviary is not None:
                self._render_pyflyt()
            elif self._physics_client is not None:
                self._render_pybullet()
        
        return rewards
    
    def _do_training_step(self):
        """
        Perform a training step on accumulated experiences.
        Called periodically during gameplay when enable_training=True.
        Aligned with sphere_arena's training system.
        """
        import math
        
        # Debug: show buffer sizes periodically (like sphere_arena)
        if hasattr(self.cocoon, 'experience_buffers'):
            buf_sizes = [len(buf) for buf in self.cocoon.experience_buffers[:min(8, len(self.cocoon.experience_buffers))]]
            batch_size = getattr(self.cocoon, 'batch_size', 32)
            if self.step_count % 500 == 100:
                print(f"   📊 Buffer sizes: {buf_sizes} (need {batch_size} each)")
        
        # Train blue cocoon
        if hasattr(self.cocoon, 'train_step'):
            try:
                loss = self.cocoon.train_step()
                
                # Handle NaN loss (like sphere_arena)
                if loss is not None and not math.isnan(loss) and loss > 0:
                    self.training_losses.append(loss)
                    if len(self.training_losses) % 5 == 1:
                        print(f"   📈 Training: step={len(self.training_losses)}, loss={loss:.4f}")
            except Exception as e:
                logger.debug(f"Blue training step failed: {e}")
        
        # Train red cocoon (if different from blue)
        if self.cocoon_red and self.cocoon_red is not self.cocoon:
            if hasattr(self.cocoon_red, 'train_step'):
                try:
                    loss = self.cocoon_red.train_step()
                    if loss is not None and not np.isnan(loss) and loss > 0:
                        logger.info(f"   📈 Red Training: loss={loss:.4f}")
                except Exception as e:
                    logger.debug(f"Red training step failed: {e}")
        
    def _process_game_mode(self) -> Dict[str, float]:
        """Process game-mode specific logic."""
        rewards = {}
        
        if self.mode == DroneGameMode.FREE_FLY:
            # Reward for exploring waypoints
            if hasattr(self.game_state, 'waypoints') and self.game_state.waypoints:
                for drone in self.drones.values():
                    if not drone.alive:
                        continue
                    for waypoint in self.game_state.waypoints:
                        dist = np.linalg.norm(drone.position - waypoint)
                        if dist < self.game_state.waypoint_radius:
                            drone.waypoints_hit += 1
                            rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.5
                            # Move waypoint to random position
                            waypoint[:] = np.random.uniform(-40, 40, 3)
                            waypoint[2] = np.random.uniform(10, 30)  # Keep altitude positive
                            
            # Reward for stable hovering (low velocity)
            for drone in self.drones.values():
                if drone.alive and np.linalg.norm(drone.velocity) < 1.0:
                    rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.01
                    
        elif self.mode == DroneGameMode.FORMATION:
            # Reward for maintaining formation
            for team in ["blue", "red"]:
                team_drones = [d for d in self.drones.values() if d.team == team and d.alive]
                if len(team_drones) < 2:
                    continue
                    
                # Calculate formation center
                center = np.mean([d.position for d in team_drones], axis=0)
                
                # Reward for being near ideal formation distance from center
                ideal_dist = 8.0  # meters
                for drone in team_drones:
                    dist_to_center = np.linalg.norm(drone.position - center)
                    error = abs(dist_to_center - ideal_dist)
                    if error < 3:  # Within tolerance
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + self.config.reward_formation
                    elif dist_to_center < 15:  # Still close
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + self.config.reward_formation * 0.5
                        
        elif self.mode == DroneGameMode.PURSUIT:
            # Move target
            if hasattr(self.game_state, 'target_pos') and self.game_state.target_pos is not None:
                dt = 1.0 / self.config.target_fps
                self.game_state.target_pos += self.game_state.target_vel * dt
                
                # Bounce off arena walls
                for i in range(3):
                    bound = self.config.arena_size / 2 if i < 2 else self.config.max_altitude
                    if abs(self.game_state.target_pos[i]) > bound * 0.8:
                        self.game_state.target_vel[i] *= -1
                        
                # Keep altitude positive
                if self.game_state.target_pos[2] < 5:
                    self.game_state.target_pos[2] = 5
                    self.game_state.target_vel[2] = abs(self.game_state.target_vel[2])
                    
                # Reward drones near target
                for drone in self.drones.values():
                    if not drone.alive:
                        continue
                    dist = np.linalg.norm(drone.position - self.game_state.target_pos)
                    if dist < self.game_state.pursuit_radius:
                        drone.pursuit_time_near += dt
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.1
                        if drone.team == "blue":
                            self.game_state.blue_score += 0.01
                        else:
                            self.game_state.red_score += 0.01
                    elif dist < self.game_state.pursuit_radius * 3:
                        # Small reward for being close
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.02
                        
        elif self.mode == DroneGameMode.TAG_BATTLE:
            # Combat handled by _process_combat()
            pass
                        
        elif self.mode == DroneGameMode.ZONE_CONTROL:
            # Reward for zone control
            for zone in self.game_state.zones:
                blue_in = 0
                red_in = 0
                
                for drone in self.drones.values():
                    if not drone.alive:
                        continue
                    dist = np.linalg.norm(drone.position - zone["center"])
                    drone.in_zone = dist < zone["radius"]
                    
                    if drone.in_zone:
                        if drone.team == "blue":
                            blue_in += 1
                        else:
                            red_in += 1
                        drone.zone_time += 1.0 / self.config.target_fps
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + self.config.reward_zone
                        
                # Update zone controller
                if blue_in > red_in:
                    zone["controller"] = "blue"
                    self.game_state.blue_score += 0.01
                elif red_in > blue_in:
                    zone["controller"] = "red"
                    self.game_state.red_score += 0.01
                    
        elif self.mode == DroneGameMode.CAPTURE_FLAG:
            # Check flag captures
            for drone in self.drones.values():
                if not drone.alive:
                    continue
                    
                # Pick up enemy flag
                if drone.team == "blue" and not drone.has_flag:
                    if self.game_state.red_flag_pos is not None:
                        if np.linalg.norm(drone.position - self.game_state.red_flag_pos) < 3:
                            drone.has_flag = True
                            self.game_state.red_flag_captured = True
                            rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 2.0
                            
                elif drone.team == "red" and not drone.has_flag:
                    if self.game_state.blue_flag_pos is not None:
                        if np.linalg.norm(drone.position - self.game_state.blue_flag_pos) < 3:
                            drone.has_flag = True
                            self.game_state.blue_flag_captured = True
                            rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 2.0
                            
                # Return flag to base
                if drone.has_flag:
                    home = self.game_state.blue_flag_pos if drone.team == "blue" else self.game_state.red_flag_pos
                    if home is not None:
                        if np.linalg.norm(drone.position - home) < 5:
                            # Scored!
                            if drone.team == "blue":
                                self.game_state.blue_score += 1
                            else:
                                self.game_state.red_score += 1
                            drone.has_flag = False
                            rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + self.config.reward_win
                            
        elif self.mode == DroneGameMode.SURVIVAL:
            # Shrink arena over time
            if hasattr(self.game_state, 'arena_radius'):
                dt = 1.0 / self.config.target_fps
                new_radius = self.game_state.arena_radius - self.game_state.shrink_rate * dt
                self.game_state.arena_radius = max(new_radius, self.game_state.min_arena_radius)
                
                # Damage drones outside arena
                for drone in self.drones.values():
                    if not drone.alive:
                        continue
                    dist_from_center = np.linalg.norm(drone.position[:2])  # XY distance
                    if dist_from_center > self.game_state.arena_radius:
                        # Damage for being outside
                        drone.health -= 0.005  # ~3 seconds to die
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) - 0.1
                        if drone.health <= 0:
                            drone.alive = False
                    else:
                        # Survival reward
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.005
                        
        elif self.mode == DroneGameMode.ESCORT:
            # Reward for protecting VIP, punish for VIP damage
            for team in ["blue", "red"]:
                vip_id = self.game_state.blue_vip if team == "blue" else self.game_state.red_vip
                if not vip_id or vip_id not in self.drones:
                    continue
                    
                vip = self.drones[vip_id]
                if not vip.alive:
                    continue
                    
                # Reward teammates for staying near VIP
                team_drones = [d for d in self.drones.values() if d.team == team and d.alive and d.organism_id != vip_id]
                for drone in team_drones:
                    dist_to_vip = np.linalg.norm(drone.position - vip.position)
                    if dist_to_vip < 10:  # Close escort
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.05
                    elif dist_to_vip < 20:  # Loose escort
                        rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + 0.02
                        
                # VIP survival reward
                rewards[vip_id] = rewards.get(vip_id, 0) + 0.01
                        
        return rewards
        
    def _process_combat(self) -> Dict[str, float]:
        """Process tag combat with proximity shaping rewards."""
        rewards = {}
        current_time = self.game_state.time_elapsed
        
        # PROXIMITY REWARD SHAPING: Encourage closing distance to enemies
        # This gives gradient signal so organisms learn to approach
        for drone in self.drones.values():
            if not drone.alive:
                continue
            enemies = [d for d in self.drones.values() if d.team != drone.team and d.alive]
            if enemies:
                nearest = min(enemies, key=lambda e: np.linalg.norm(e.position - drone.position))
                dist = np.linalg.norm(nearest.position - drone.position)
                # Proximity reward: inverse distance, capped
                # At 50m: +0.001, at 10m: +0.005, at 2m: +0.025
                proximity_reward = 0.05 / max(dist, 2.0)
                rewards[drone.organism_id] = rewards.get(drone.organism_id, 0) + proximity_reward
        
        for attacker in self.drones.values():
            if not attacker.alive:
                continue
            if current_time - attacker.last_tag_time < self.config.tag_cooldown:
                continue
                
            for defender in self.drones.values():
                if not defender.alive:
                    continue
                if defender.team == attacker.team:
                    continue
                    
                # Check tag distance
                dist = np.linalg.norm(attacker.position - defender.position)
                if dist < self.config.tag_distance:
                    # Tag hit!
                    attacker.last_tag_time = current_time
                    attacker.tags_given += 1
                    defender.tags_received += 1
                    defender.health -= self.config.tag_damage
                    
                    rewards[attacker.organism_id] = rewards.get(attacker.organism_id, 0) + self.config.reward_tag
                    rewards[defender.organism_id] = rewards.get(defender.organism_id, 0) + self.config.reward_tagged
                    
                    # 🧠 Language learning: update concept magnetism from combat outcome
                    if self.use_language_bridge and self.language_bridge:
                        # Attacker learns: attacking works!
                        self.language_bridge.learn_from_step('tag_enemy', 0.5)
                        # Defender learns: need to evade better
                        self.language_bridge.learn_from_step('got_tagged', -0.3)
                    
                    # Check kill
                    if defender.health <= 0:
                        defender.alive = False
                        attacker.kills += 1
                        rewards[attacker.organism_id] = rewards.get(attacker.organism_id, 0) + self.config.reward_kill
                        rewards[defender.organism_id] = rewards.get(defender.organism_id, 0) + self.config.reward_death
                        
                        # 🧠 Language learning: kill/death outcomes
                        if self.use_language_bridge and self.language_bridge:
                            self.language_bridge.learn_from_step('win', 1.0)
                        
                        # If killed flag carrier, drop flag
                        if defender.has_flag:
                            defender.has_flag = False
                            if defender.team == "blue":
                                self.game_state.red_flag_captured = False
                            else:
                                self.game_state.blue_flag_captured = False
                                
                    break  # Only one tag per step
                    
        return rewards
        
    def _process_collisions(self) -> Dict[str, float]:
        """Process drone-drone collisions."""
        rewards = {}
        checked = set()
        
        for d1 in self.drones.values():
            if not d1.alive:
                continue
            for d2 in self.drones.values():
                if not d2.alive or d1.organism_id == d2.organism_id:
                    continue
                    
                pair = tuple(sorted([d1.organism_id, d2.organism_id]))
                if pair in checked:
                    continue
                checked.add(pair)
                
                dist = np.linalg.norm(d1.position - d2.position)
                if dist < 1.0:  # Collision
                    # Damage both
                    rel_vel = np.linalg.norm(d1.velocity - d2.velocity)
                    damage = self.config.collision_damage * (1 + rel_vel / 10)
                    
                    d1.health -= damage
                    d2.health -= damage
                    
                    # Bounce
                    direction = d1.position - d2.position
                    if np.linalg.norm(direction) > 0.01:
                        direction = direction / np.linalg.norm(direction)
                    else:
                        direction = np.random.randn(3)
                        direction = direction / np.linalg.norm(direction)
                        
                    bounce = max(2.0, rel_vel * 0.3)
                    d1.velocity += direction * bounce
                    d2.velocity -= direction * bounce
                    
                    d1.position += direction * 0.5
                    d2.position -= direction * 0.5
                    
                    rewards[d1.organism_id] = rewards.get(d1.organism_id, 0) + self.config.reward_collision
                    rewards[d2.organism_id] = rewards.get(d2.organism_id, 0) + self.config.reward_collision
                    
        return rewards
        
    def _check_win_conditions(self):
        """Check if game should end."""
        if self.game_state.finished:
            return
            
        # Time limit
        if self.game_state.step_count >= self.config.max_episode_steps:
            self.game_state.finished = True
            if self.game_state.blue_score > self.game_state.red_score:
                self.game_state.winner = "blue"
            elif self.game_state.red_score > self.game_state.blue_score:
                self.game_state.winner = "red"
            else:
                self.game_state.winner = "draw"
            return
            
        # Mode-specific win conditions
        if self.mode == DroneGameMode.FREE_FLY:
            # No win condition - just training
            pass
            
        elif self.mode == DroneGameMode.FORMATION:
            # Team with best formation coherence wins (checked at time limit)
            pass
            
        elif self.mode == DroneGameMode.PURSUIT:
            # Score limit for pursuit
            if self.game_state.blue_score >= 10:
                self.game_state.finished = True
                self.game_state.winner = "blue"
            elif self.game_state.red_score >= 10:
                self.game_state.finished = True
                self.game_state.winner = "red"
            
        elif self.mode in [DroneGameMode.TAG_BATTLE, DroneGameMode.SURVIVAL]:
            # Elimination - check total alive for free-for-all survival
            total_alive = sum(1 for d in self.drones.values() if d.alive)
            
            if self.mode == DroneGameMode.SURVIVAL and self.game_state.red_alive == 0:
                # Free-for-all survival (all blue team) - last drone standing wins
                if total_alive <= 1:
                    self.game_state.finished = True
                    # Find the survivor
                    for name, drone in self.drones.items():
                        if drone.alive:
                            self.game_state.winner = name
                            break
                    else:
                        self.game_state.winner = "draw"
            elif self.game_state.blue_alive == 0:
                self.game_state.finished = True
                self.game_state.winner = "red"
            elif self.game_state.red_alive == 0 and self.mode == DroneGameMode.TAG_BATTLE:
                self.game_state.finished = True
                self.game_state.winner = "blue"
                
        elif self.mode == DroneGameMode.ZONE_CONTROL:
            # Score limit
            if self.game_state.blue_score >= 100:
                self.game_state.finished = True
                self.game_state.winner = "blue"
            elif self.game_state.red_score >= 100:
                self.game_state.finished = True
                self.game_state.winner = "red"
                
        elif self.mode == DroneGameMode.CAPTURE_FLAG:
            # Score limit
            if self.game_state.blue_score >= 3:
                self.game_state.finished = True
                self.game_state.winner = "blue"
            elif self.game_state.red_score >= 3:
                self.game_state.finished = True
                self.game_state.winner = "red"
                
        elif self.mode == DroneGameMode.ESCORT:
            # VIP death ends game
            blue_vip_alive = self.game_state.blue_vip and self.game_state.blue_vip in self.drones and self.drones[self.game_state.blue_vip].alive
            red_vip_alive = self.game_state.red_vip and self.game_state.red_vip in self.drones and self.drones[self.game_state.red_vip].alive
            
            if not blue_vip_alive and not red_vip_alive:
                self.game_state.finished = True
                self.game_state.winner = "draw"
            elif not blue_vip_alive:
                self.game_state.finished = True
                self.game_state.winner = "red"
            elif not red_vip_alive:
                self.game_state.finished = True
                self.game_state.winner = "blue"
                
    def run_episode(self, max_steps: int = None) -> Dict[str, Any]:
        """
        Run a complete episode.
        
        Returns:
            Episode statistics
        """
        max_steps = max_steps or self.config.max_episode_steps
        
        print(f"\n{'='*60}")
        print(f"🛸 COCOON DRONE ARENA - {self.mode.value.upper()}")
        print(f"{'='*60}")
        print(f"Organisms: {self.num_organisms}")
        print(f"Blue team: {self.game_state.blue_alive}")
        print(f"Red team: {self.game_state.red_alive}")
        print(f"{'='*60}\n")
        
        total_rewards = {name: 0.0 for name in self.organism_names}
        
        while not self.game_state.finished and self.game_state.step_count < max_steps:
            # Step simulation
            step_rewards = self.step()
            
            for name, r in step_rewards.items():
                total_rewards[name] += r
                
            # Progress report
            if self.game_state.step_count % 300 == 0:  # Every 5 seconds
                print(f"Step {self.game_state.step_count:5d} | "
                      f"Blue: {self.game_state.blue_alive}/{self.num_organisms//2} "
                      f"({self.game_state.blue_score:.1f}) | "
                      f"Red: {self.game_state.red_alive}/{self.num_organisms - self.num_organisms//2} "
                      f"({self.game_state.red_score:.1f})")
                      
        # Episode complete
        print(f"\n{'='*60}")
        print(f"EPISODE COMPLETE")
        print(f"{'='*60}")
        print(f"Winner: {self.game_state.winner or 'NONE'}")
        print(f"Duration: {self.game_state.time_elapsed:.1f}s")
        print(f"Blue score: {self.game_state.blue_score:.2f}")
        print(f"Red score: {self.game_state.red_score:.2f}")
        
        # Language bridge episode-end learning
        if self.language_bridge:
            for name, drone in self.drones.items():
                if name in self.organisms:
                    # Determine if this drone won
                    won = False
                    if self.game_state.winner == "blue" and drone.team == "blue":
                        won = True
                    elif self.game_state.winner == "red" and drone.team == "red":
                        won = True
                    
                    # Learn from episode outcome
                    outcome_info = {
                        "won": won,
                        "survived": drone.alive,
                        "kills": drone.kills,
                        "tags_given": drone.tags_given,
                        "tags_received": drone.tags_received,
                        "reward": total_rewards.get(name, 0.0)
                    }
                    self.language_bridge.learn_from_episode_end(
                        organism_name=name,
                        won=won,
                        final_score=total_rewards.get(name, 0.0),
                        episode_length=self.game_state.step_count,
                        additional_info=outcome_info
                    )
        
        # Compile statistics
        stats = {
            "mode": self.mode.value,
            "winner": self.game_state.winner,
            "duration": self.game_state.time_elapsed,
            "steps": self.game_state.step_count,
            "blue_survivors": self.game_state.blue_alive,
            "red_survivors": self.game_state.red_alive,
            "blue_score": self.game_state.blue_score,
            "red_score": self.game_state.red_score,
            "total_rewards": total_rewards,
            "drone_stats": {
                name: {
                    "team": drone.team,
                    "alive": drone.alive,
                    "health": drone.health,
                    "kills": drone.kills,
                    "tags_given": drone.tags_given,
                    "tags_received": drone.tags_received,
                    "distance": drone.distance_traveled,
                    "reward": total_rewards.get(name, 0.0)
                }
                for name, drone in self.drones.items()
            }
        }
        
        return stats


# =============================================================================
# INTEGRATION WITH PROTON GAME
# =============================================================================

def get_drone_games_for_proton() -> Dict[str, Dict[str, Any]]:
    """
    Get drone game configurations for ProtonGameArena integration.
    
    These can be added to the ProtonGameArena game selection grid.
    """
    return {
        "DroneTagBattle": {
            "mode": DroneGameMode.TAG_BATTLE,
            "description": "Aerial tag combat - eliminate enemies",
            "challenge_type": "PHYSICAL",
            "complexity": 3,
            "discrete_action": True,
        },
        "DroneZoneControl": {
            "mode": DroneGameMode.ZONE_CONTROL,
            "description": "Control airspace zones",
            "challenge_type": "MENTAL",
            "complexity": 2,
            "discrete_action": True,
        },
        "DroneCaptureFlag": {
            "mode": DroneGameMode.CAPTURE_FLAG,
            "description": "Team objective - capture enemy flag",
            "challenge_type": "PHYSICAL",
            "complexity": 4,
            "discrete_action": True,
        },
        "DroneSurvival": {
            "mode": DroneGameMode.SURVIVAL,
            "description": "Last drone flying wins",
            "challenge_type": "PHYSICAL",
            "complexity": 3,
            "discrete_action": True,
        },
        "DroneFormation": {
            "mode": DroneGameMode.FORMATION,
            "description": "Maintain swarm formation",
            "challenge_type": "SOCIAL",
            "complexity": 2,
            "discrete_action": True,
        },
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🛸 Cocoon Drone Arena")
    parser.add_argument('cocoon', help='Path to cocoon folder')
    parser.add_argument('--mode', choices=[m.value for m in DroneGameMode],
                        default='tag_battle', help='Game mode')
    parser.add_argument('--steps', type=int, default=3000, help='Max steps')
    parser.add_argument('--wind', type=float, default=5.0, help='Wind speed (m/s)')
    parser.add_argument('--visual', action='store_true', help='Enable visualization')
    
    args = parser.parse_args()
    
    # Load cocoon
    cocoon_path = args.cocoon
    if os.path.isdir(cocoon_path):
        py_files = [f for f in os.listdir(cocoon_path) if f.endswith('.py') and 'cocoon' in f.lower()]
        if py_files:
            module_name = py_files[0].replace('.py', '')
            sys.path.insert(0, cocoon_path)
            module = __import__(module_name)
            cocoon = module.CocoonAgent()
        else:
            print(f"No cocoon .py file found in {cocoon_path}")
            return
    else:
        print(f"Invalid cocoon path: {cocoon_path}")
        return
        
    # Create arena
    config = DroneArenaConfig(wind_speed=args.wind)
    arena = CocoonDroneArena(
        cocoon=cocoon,
        mode=DroneGameMode(args.mode),
        config=config,
        visualize=args.visual
    )
    
    # Run episode
    stats = arena.run_episode(max_steps=args.steps)
    
    # Print top performers
    print("\n🏆 TOP PERFORMERS:")
    sorted_drones = sorted(stats["drone_stats"].items(), 
                           key=lambda x: x[1]["reward"], reverse=True)
    for i, (name, data) in enumerate(sorted_drones[:5]):
        print(f"  {i+1}. {name[:8]} ({data['team']}): "
              f"Reward={data['reward']:.1f}, Kills={data['kills']}, "
              f"{'ALIVE' if data['alive'] else 'DEAD'}")


if __name__ == "__main__":
    main()
