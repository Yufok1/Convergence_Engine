#!/usr/bin/env python3
"""
🌐 SPHERE ARENA - 3D Swarm Defense Training with Hierarchical Command Chain

A 3D arena where organisms collectively defend the ENTIRE sphere surface.
All organisms share ONE zone - the whole sphere. They must self-organize,
coordinate, and work as a UNIT to intercept the ball.

═══════════════════════════════════════════════════════════════════════════════
HIERARCHICAL COMMAND CHAIN SYSTEM
═══════════════════════════════════════════════════════════════════════════════

When an organism intercepts the ball, it becomes COMMANDER:
1. Commander predicts where ball will hit next (ray-sphere intersection)
2. Commander broadcasts predicted impact point to entire swarm
3. All organisms receive the directive in their observation space
4. Organisms move toward the commanded position
5. The organism that catches next becomes the NEW commander

PERFORMANCE-BASED SUCCESSION:
- Catching the ball = you become commander
- Following commands well = higher compliance score  
- Best followers who intercept = best leaders
- Creates emergent leadership hierarchy based on COMPETENCE

This models:
- Military command structures with tactical handoffs
- Swarm robotics with dynamic leader election
- Distributed sensor networks with coordinator rotation
- Collective decision making with performance feedback

═══════════════════════════════════════════════════════════════════════════════

This tests:
- Emergent swarm coordination
- Self-organization without explicit roles
- Collective defense capabilities
- Distributed interception strategies
- Command-following behavior (NEW!)
- Performance-based leadership (NEW!)

Future applications:
- Defensive targeting systems (missile defense)
- Distributed threat response networks
- Swarm robotics coordination
- Collective intelligence evaluation
- Multi-agent reinforcement learning

"The swarm is ONE. The interceptor commands. The best follower leads next."

Author: The Butterfly System / Convergence Engine
For use with exported Cocoon agents.
"""

import math
import time
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

# Try to import pygame and OpenGL
try:
    import pygame
    from pygame.locals import *
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

# =============================================================================
# CONSTANTS
# =============================================================================

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
SPHERE_RADIUS = 2.0  # Radius of the arena sphere
BALL_RADIUS = 0.08   # Ball size relative to sphere
PADDLE_ANGULAR_RADIUS = 0.25  # Radians - size of circular paddle zone
BALL_SPEED = 0.03    # Initial ball speed
MAX_BALL_SPEED = 0.08
ORGANISM_MOVE_SPEED = 0.04  # Radians per frame

# Observation size for neural network
# Base: 15 (ball state, position, distances, game state)
# Command chain: 5 (command target, distance to command, is_commander, has_command)
OBSERVATION_SIZE = 24  # With padding room

# Colors (RGB floats for OpenGL)
COLORS = [
    (1.0, 0.4, 0.4),   # Red
    (0.4, 1.0, 0.4),   # Green
    (0.4, 0.4, 1.0),   # Blue
    (1.0, 1.0, 0.4),   # Yellow
    (1.0, 0.4, 1.0),   # Magenta
    (0.4, 1.0, 1.0),   # Cyan
    (1.0, 0.7, 0.4),   # Orange
    (0.7, 0.4, 1.0),   # Purple
    (0.4, 1.0, 0.7),   # Teal
    (1.0, 0.4, 0.7),   # Pink
    (0.7, 1.0, 0.4),   # Lime
    (0.4, 0.7, 1.0),   # Sky Blue
]

# =============================================================================
# 3D MATH UTILITIES
# =============================================================================

def spherical_to_cartesian(theta: float, phi: float, r: float = SPHERE_RADIUS) -> Tuple[float, float, float]:
    """
    Convert spherical coordinates to Cartesian.
    theta: azimuthal angle (0 to 2π) - longitude
    phi: polar angle (0 to π) - latitude from top
    """
    x = r * math.sin(phi) * math.cos(theta)
    y = r * math.cos(phi)
    z = r * math.sin(phi) * math.sin(theta)
    return (x, y, z)


def cartesian_to_spherical(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert Cartesian to spherical coordinates (r, theta, phi)."""
    r = math.sqrt(x**2 + y**2 + z**2)
    if r == 0:
        return (0, 0, 0)
    phi = math.acos(y / r)  # Polar angle from Y axis
    theta = math.atan2(z, x)  # Azimuthal angle
    return (r, theta, phi)


def normalize_vector(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Normalize a 3D vector."""
    length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if length == 0:
        return (0, 0, 0)
    return (v[0]/length, v[1]/length, v[2]/length)


def dot_product(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    """Dot product of two 3D vectors."""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def cross_product(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Cross product of two 3D vectors."""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    )


def reflect_vector(v: Tuple[float, float, float], n: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Reflect vector v off surface with normal n."""
    d = dot_product(v, n)
    return (
        v[0] - 2*d*n[0],
        v[1] - 2*d*n[1],
        v[2] - 2*d*n[2]
    )


def angular_distance(theta1: float, phi1: float, theta2: float, phi2: float) -> float:
    """
    Calculate angular distance between two points on a sphere (great-circle distance).
    Returns angle in radians.
    """
    # Convert to Cartesian, compute dot product, get angle
    p1 = spherical_to_cartesian(theta1, phi1, 1.0)
    p2 = spherical_to_cartesian(theta2, phi2, 1.0)
    dot = max(-1.0, min(1.0, dot_product(p1, p2)))
    return math.acos(dot)


def point_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Euclidean distance between two 3D points."""
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SphereOrganism:
    """An organism defending a zone on the sphere surface."""
    organism_idx: int
    theta: float  # Azimuthal position (longitude)
    phi: float    # Polar position (latitude)
    color: Tuple[float, float, float]
    alive: bool = True
    catches: int = 0  # Successful interceptions
    misses: int = 0   # Times ball passed through zone
    
    # Command chain stats
    commands_issued: int = 0      # Times this organism commanded the swarm
    commands_followed: int = 0    # How well this organism followed orders
    command_score: float = 0.0    # Accumulated command-following performance
    leadership_score: float = 0.0 # How good were this organism's commands
    
    # Current command state
    last_command_received: Optional[Tuple[float, float]] = None  # (target_theta, target_phi)
    command_compliance: float = 0.0  # How well following current command (0-1)
    
    # Multi-ball assignment
    assigned_ball: Optional[int] = None  # Which ball this organism is tracking (None = unassigned)
    is_ball_commander: bool = False       # Is this organism commanding a ball's squad?
    is_supreme_commander: bool = False    # Is this the overall supreme commander?
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get 3D Cartesian position on sphere surface."""
        return spherical_to_cartesian(self.theta, self.phi)
    
    def get_normal(self) -> Tuple[float, float, float]:
        """Get outward normal at this position (points away from center)."""
        pos = self.get_position()
        return normalize_vector(pos)
    
    def move(self, d_theta: float, d_phi: float):
        """Move on sphere surface."""
        self.theta = (self.theta + d_theta) % (2 * math.pi)
        self.phi = max(0.1, min(math.pi - 0.1, self.phi + d_phi))


@dataclass
class Ball3D:
    """A ball bouncing inside the sphere in 3D."""
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    last_hit_by: Optional[int] = None
    
    def get_position(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def get_velocity(self) -> Tuple[float, float, float]:
        return (self.vx, self.vy, self.vz)
    
    def move(self):
        """Move ball by velocity."""
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
    
    def speed_up(self, factor: float = 1.02):
        """Increase ball speed."""
        self.vx *= factor
        self.vy *= factor
        self.vz *= factor
        # Cap speed
        speed = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
        if speed > MAX_BALL_SPEED:
            scale = MAX_BALL_SPEED / speed
            self.vx *= scale
            self.vy *= scale
            self.vz *= scale
    
    def get_speed(self) -> float:
        return math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)


# =============================================================================
# GAME MODES
# =============================================================================

class GameMode(Enum):
    """Arena game modes."""
    SWARM_DEFENSE = "swarm_defense"  # All organisms defend together (default)
    ELIMINATION = "elimination"      # Last survivor wins (solo testing)
    COOPERATIVE = "cooperative"      # Shared lives, harsh penalty


# =============================================================================
# SPHERE ARENA
# =============================================================================

class SphereArena:
    """
    🌐 3D Sphere Swarm Defense Arena
    
    All organisms share ONE zone - the ENTIRE sphere surface.
    They must self-organize and coordinate to intercept the ball.
    ANY organism can catch. Success = collective. Failure = collective.
    
    This evaluates:
    - Swarm coordination capability
    - Emergent role distribution  
    - Collective reaction time
    - Coverage optimization
    - HIERARCHICAL COMMAND CHAIN (new!)
    
    Command Chain System:
    - The organism that intercepts becomes COMMANDER
    - Commander broadcasts predicted impact point to swarm
    - Other organisms follow the command (move toward predicted point)
    - The organism that follows best AND intercepts next = new commander
    - Creates emergent leadership based on PERFORMANCE
    
    Game Modes:
    - SWARM_DEFENSE: Main mode - collective defense, shared score
    - ELIMINATION: Individual testing mode
    - COOPERATIVE: Shared lives with harsh miss penalty
    """
    
    def __init__(
        self,
        agent,  # CocoonAgent with brains
        organism_indices: Optional[List[int]] = None,
        max_misses: int = 10,  # Collective misses before game over
        headless: bool = False,
        seed: Optional[int] = None,
        mode: GameMode = GameMode.SWARM_DEFENSE,
        teams: Optional[Dict[str, List[int]]] = None,  # For team vs team mode
        enable_command_chain: bool = True,  # Enable hierarchical command system
        num_balls: int = 1,  # Number of balls in play (multi-ball chaos!)
        enable_training: bool = False,  # Enable post-snapshot training during gameplay
        train_interval: int = 100,  # Train every N frames when training enabled
        verbose: bool = False  # Enable granular debug logging
    ):
        self.agent = agent
        self.max_misses = max_misses  # Collective miss limit
        self.headless = headless
        self.mode = mode
        self.enable_command_chain = enable_command_chain
        self.num_balls = max(1, min(num_balls, 5))  # 1-5 balls
        self.verbose = verbose  # Granular debug logging
        
        # ═══════════════════════════════════════════════════════════════════
        # DEBUG LOGGING SYSTEM
        # ═══════════════════════════════════════════════════════════════════
        # When verbose=True, logs:
        #   - Every brain decision (action probs, chosen action)
        #   - Every experience added (state, action, reward)
        #   - Every training step (loss, gradients)
        #   - Ball tracking (position, velocity, impact prediction)
        #   - Command chain (orders given, compliance scores)
        # ═══════════════════════════════════════════════════════════════════
        self.debug_log: Dict[str, List[Dict]] = {
            'actions': [],       # Brain decisions 
            'experiences': [],   # Experience buffer entries
            'training': [],      # Training steps
            'commands': [],      # Command chain orders
            'catches': [],       # Successful catches
            'misses': [],        # Missed balls
            'events': [],        # General events (for _log_debug)
        }
        self.experience_log: List[Dict] = []  # Detailed experience tracking
        
        # ═══════════════════════════════════════════════════════════════════
        # POST-SNAPSHOT TRAINING SYSTEM
        # ═══════════════════════════════════════════════════════════════════
        # When enabled, organisms learn from arena experiences:
        #   - Catches: +1.0 reward (reinforces interception behavior)
        #   - Misses: -0.5 reward (penalizes bad positioning)
        #   - Near misses: +0.2 reward (encourages approach)
        # Weights are updated via agent.train_step() every train_interval frames
        # ═══════════════════════════════════════════════════════════════════
        self.enable_training = enable_training
        self.train_interval = train_interval
        self.training_losses: List[float] = []  # Track training progress
        self.last_observations: Dict[int, np.ndarray] = {}  # For experience tracking
        self.last_actions: Dict[int, int] = {}  # Action taken from observation
        
        # Swarm stats
        self.collective_catches = 0
        self.collective_misses = 0
        self.catch_streak = 0
        self.best_streak = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # HIERARCHICAL COMMAND CHAIN SYSTEM (Multi-Ball Support)
        # ═══════════════════════════════════════════════════════════════════
        # 
        # Structure with multiple balls:
        #   👑 SUPREME COMMANDER (best overall performer)
        #       │
        #       ├── ⚽ Ball #0 Commander + Squad
        #       ├── ⚽ Ball #1 Commander + Squad  
        #       └── ⚽ Ball #2 Commander + Squad
        #
        # Supreme Commander: Assigns organisms to balls based on threat/proximity
        # Ball Commanders: Issue intercept orders for their specific ball
        # ═══════════════════════════════════════════════════════════════════
        
        # Legacy single-ball (backward compat)
        self.current_commander: Optional[int] = None
        self.current_command: Optional[Tuple[float, float]] = None
        self.command_history: List[Dict] = []
        self.predicted_impact: Optional[Tuple[float, float]] = None
        self.command_broadcast_frame: int = 0
        
        # Multi-ball command structure
        self.supreme_commander: Optional[int] = None  # Best overall performer
        self.ball_commanders: Dict[int, Optional[int]] = {}  # ball_idx -> commander organism
        self.ball_commands: Dict[int, Optional[Tuple[float, float]]] = {}  # ball_idx -> (theta, phi)
        self.ball_squads: Dict[int, List[int]] = {}  # ball_idx -> list of assigned organisms
        self.reassignment_cooldown: int = 0  # Frames until next reassignment allowed
        
        # Team configuration (optional)
        self.teams = teams or {}
        self.team_lives: Dict[str, int] = {}
        self.organism_to_team: Dict[int, str] = {}
        
        # RNG
        self.seed = seed
        self.rng = random.Random(seed)
        if seed is not None:
            np.random.seed(seed)
        
        # Select organisms
        if organism_indices is None:
            organism_indices = list(range(min(len(agent.brains), 8)))
        self.organism_indices = organism_indices
        
        # Verify agent wiring
        self._verify_agent_wiring()
        
        # Setup teams if specified
        if self.teams:
            self._setup_teams()
        
        # Initialize
        self.reset()
        
        # Graphics setup
        self.screen = None
        self.clock = None
        if not headless:
            if not PYGAME_AVAILABLE:
                raise RuntimeError("pygame required for rendering")
            if not OPENGL_AVAILABLE:
                print("⚠️ OpenGL not available, falling back to wireframe mode")
            self._init_graphics()
    
    def _init_graphics(self):
        """Initialize Pygame and OpenGL."""
        pygame.init()
        pygame.display.set_caption("🌐 Sphere Arena - 3D Elimination Battle")
        
        if OPENGL_AVAILABLE:
            self.screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT), 
                DOUBLEBUF | OPENGL
            )
            self._setup_opengl()
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        self.clock = pygame.time.Clock()
    
    def _setup_opengl(self):
        """Configure OpenGL rendering."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Light position
        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
        
        # Perspective
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    
    def _verify_agent_wiring(self):
        """Verify the CocoonAgent is properly wired for arena use."""
        issues = []
        
        # Check brains exist
        if not hasattr(self.agent, 'brains') or not self.agent.brains:
            issues.append("❌ agent.brains missing or empty")
        else:
            print(f"   ✅ Brains: {len(self.agent.brains)} organisms")
        
        # Check brain dimensions
        for i, org_idx in enumerate(self.organism_indices):
            if org_idx >= len(self.agent.brains):
                issues.append(f"❌ organism_idx {org_idx} exceeds brain count {len(self.agent.brains)}")
                continue
            
            brain = self.agent.brains[org_idx]
            input_dim = getattr(brain, 'input_dim', getattr(brain, 'input_size', None))
            output_dim = getattr(brain, 'output_dim', getattr(brain, 'output_size', None))
            
            if input_dim is None:
                issues.append(f"❌ Brain {org_idx} has no input_dim")
            if output_dim is None:
                issues.append(f"❌ Brain {org_idx} has no output_dim")
        
        # Check VP runtime (optional but useful)
        if hasattr(self.agent, 'vp_runtime'):
            print(f"   ✅ VP Runtime: enabled")
        else:
            print(f"   ⚠️ VP Runtime: not available (fallback to 0.5)")
        
        # Check vocabulary (optional)
        if hasattr(self.agent, 'vocabulary') and self.agent.vocabulary:
            vocab_size = len(self.agent.vocabulary.get('word_to_id', {}))
            print(f"   ✅ Vocabulary: {vocab_size:,} words")
        
        # Check organism names
        if hasattr(self.agent, 'organism_names') and self.agent.organism_names:
            print(f"   ✅ Organism names: {self.agent.organism_names[:3]}...")
        
        # Check fitness tracking
        if hasattr(self.agent, 'organism_fitness') and self.agent.organism_fitness:
            print(f"   ✅ Fitness tracking: {len(self.agent.organism_fitness)} values")
        
        if issues:
            print("\n⚠️ WIRING ISSUES DETECTED:")
            for issue in issues:
                print(f"   {issue}")
            raise RuntimeError(f"Agent wiring check failed: {len(issues)} issues")
        else:
            print("   ✅ All wiring checks passed")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GRANULAR DEBUG LOGGING SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _log_debug(self, event_type: str, data: Dict):
        """Log a debug event with timestamp."""
        if not self.verbose:
            return
        
        event = {
            'frame': self.frame_count,
            'type': event_type,
            'time': time.time(),
            **data
        }
        
        # Store in appropriate category
        if event_type == 'BRAIN_DECISION':
            self.debug_log['actions'].append(event)
        elif event_type == 'EXPERIENCE_ADDED':
            self.debug_log['experiences'].append(event)
        elif event_type == 'TRAINING_STEP':
            self.debug_log['training'].append(event)
        elif event_type == 'COMMAND_ISSUED':
            self.debug_log['commands'].append(event)
        elif event_type == 'CATCH':
            self.debug_log['catches'].append(event)
        elif event_type == 'MISS':
            self.debug_log['misses'].append(event)
        else:
            self.debug_log['events'].append(event)
        
        # Print to console in verbose mode
        self._print_debug_event(event_type, data)
    
    def _print_debug_event(self, event_type: str, data: Dict):
        """Print formatted debug event to console."""
        frame = self.frame_count
        prefix = f"[F{frame:05d}]"
        
        if event_type == 'BRAIN_DECISION':
            # Only print brain decisions every 50 frames to reduce verbosity
            # (still stored in debug_log for full analysis)
            if frame % 50 != 0 and frame > 1:
                return
            org = data['organism']
            action = data['action_idx']
            probs = data.get('action_probs', [])
            conf = data.get('confidence', 0)
            move = data.get('movement', (0, 0))
            probs_str = ','.join([f'{p:.2f}' for p in probs[:6]]) if probs else 'N/A'
            print(f"{prefix} 🧠 Org#{org} → action={action} conf={conf:.3f} move=({move[0]:+.3f},{move[1]:+.3f}) probs=[{probs_str}]")
        
        elif event_type == 'EXPERIENCE_ADDED':
            org = data['organism']
            reward = data['reward']
            action = data['action']
            buf_size = data.get('buffer_size', '?')
            reason = data.get('reason', '')
            print(f"{prefix} 📦 Org#{org} EXP: reward={reward:+.3f} action={action} buf={buf_size} ({reason})")
        
        elif event_type == 'TRAINING_STEP':
            loss = data.get('loss', 0)
            step = data.get('step', 0)
            trained = data.get('brains_trained', 0)
            print(f"{prefix} 📈 TRAIN: step={step} loss={loss:.6f} brains={trained}")
        
        elif event_type == 'BALL_STATE':
            for i, ball_data in enumerate(data.get('balls', [])):
                pos = ball_data['position']
                vel = ball_data['velocity']
                speed = ball_data['speed']
                print(f"{prefix} ⚽ Ball#{i}: pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f}) vel=({vel[0]:+.3f},{vel[1]:+.3f},{vel[2]:+.3f}) speed={speed:.3f}")
        
        elif event_type == 'ORGANISM_POSITIONS':
            for org_idx, pos_data in data.get('organisms', {}).items():
                theta, phi = pos_data['theta'], pos_data['phi']
                nearest_ball = pos_data.get('nearest_ball_dist', 999)
                cmd = pos_data.get('command_dist', 999)
                print(f"{prefix} 🦠 Org#{org_idx}: θ={theta:.2f} φ={phi:.2f} ball_dist={nearest_ball:.2f} cmd_dist={cmd:.2f}")
        
        elif event_type == 'COMMAND_ISSUED':
            commander = data['commander']
            target = data['target']
            print(f"{prefix} 📢 COMMAND: Org#{commander} → target=({target[0]:.2f},{target[1]:.2f})")
        
        elif event_type == 'CATCH':
            catcher = data['catcher']
            ball = data.get('ball_idx', 0)
            streak = data.get('streak', 0)
            print(f"{prefix} 🎯 CATCH: Org#{catcher} caught ball#{ball} streak={streak}")
        
        elif event_type == 'MISS':
            ball = data.get('ball_idx', 0)
            pos = data.get('position', (0, 0))
            nearest = data.get('nearest_organism', '?')
            nearest_dist = data.get('nearest_dist', 999)
            print(f"{prefix} ❌ MISS: ball#{ball} at ({pos[0]:.2f},{pos[1]:.2f}) nearest=Org#{nearest} dist={nearest_dist:.2f}")
    
    def _log_ball_states(self):
        """Log current state of all balls."""
        if not self.verbose:
            return
        
        balls_data = []
        for ball in self.balls:
            pos = ball.get_position()
            vel = ball.get_velocity()
            balls_data.append({
                'position': pos,
                'velocity': vel,
                'speed': ball.get_speed()
            })
        
        self._log_debug('BALL_STATE', {'balls': balls_data})
    
    def _log_organism_positions(self):
        """Log current positions of all organisms."""
        if not self.verbose:
            return
        
        org_data = {}
        for org_idx in self.alive_organisms:
            org = self.organisms[org_idx]
            
            # Find nearest ball
            min_dist = float('inf')
            for ball in self.balls:
                ball_pos = ball.get_position()
                _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
                dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                min_dist = min(min_dist, dist)
            
            # Command distance
            cmd_dist = 999
            if org.last_command_received:
                cmd_theta, cmd_phi = org.last_command_received
                cmd_dist = angular_distance(org.theta, org.phi, cmd_theta, cmd_phi)
            
            org_data[org_idx] = {
                'theta': org.theta,
                'phi': org.phi,
                'nearest_ball_dist': min_dist,
                'command_dist': cmd_dist
            }
        
        self._log_debug('ORGANISM_POSITIONS', {'organisms': org_data})
    
    def _setup_teams(self):
        """Setup team mode configuration."""
        if not self.teams:
            # Auto-assign teams: split organisms evenly
            mid = len(self.organism_indices) // 2
            self.teams = {
                'alpha': self.organism_indices[:mid],
                'beta': self.organism_indices[mid:]
            }
            print(f"   🔴 Auto-assigned teams: alpha={self.teams['alpha']}, beta={self.teams['beta']}")
        
        # Build reverse lookup
        for team_name, members in self.teams.items():
            for org_idx in members:
                self.organism_to_team[org_idx] = team_name
        
        # Initialize team lives
        for team_name in self.teams:
            self.team_lives[team_name] = self.lives_per_organism * len(self.teams[team_name])
        
        # Assign team colors (organisms on same team get similar colors)
        team_colors = {
            'alpha': (1.0, 0.3, 0.3),   # Red team
            'beta': (0.3, 0.3, 1.0),    # Blue team
        }
        # Override organism colors by team
        for team_name, members in self.teams.items():
            base_color = team_colors.get(team_name, COLORS[hash(team_name) % len(COLORS)])
            for i, org_idx in enumerate(members):
                # Slight variation within team
                variation = 0.1 * (i / max(1, len(members) - 1) - 0.5)
                COLORS[org_idx % len(COLORS)]  # Keep original for now
    
    def reset(self):
        """Reset arena for new game."""
        self.alive_organisms: List[int] = list(self.organism_indices)
        
        # Reset swarm stats
        self.collective_catches = 0
        self.collective_misses = 0
        self.catch_streak = 0
        self.best_streak = 0
        self.eliminations: List[Tuple[int, int]] = []  # (frame, org_idx) for elimination mode
        
        # Distribute organisms evenly on sphere using Fibonacci spiral
        # This gives good initial coverage for swarm defense
        self.organisms: Dict[int, SphereOrganism] = {}
        n = len(self.alive_organisms)
        
        for i, org_idx in enumerate(self.alive_organisms):
            # Fibonacci sphere distribution for optimal coverage
            golden_ratio = (1 + math.sqrt(5)) / 2
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2*(i + 0.5)/n)
            
            color = COLORS[org_idx % len(COLORS)]
            self.organisms[org_idx] = SphereOrganism(
                organism_idx=org_idx,
                theta=theta,
                phi=phi,
                color=color
            )
        
        # Create balls at center with random directions
        self.balls: List[Ball3D] = []
        for ball_idx in range(self.num_balls):
            direction = self._random_direction()
            # Offset starting positions slightly so balls don't collide immediately
            offset = 0.1 * ball_idx
            ball = Ball3D(
                x=offset * direction[0], 
                y=offset * direction[1], 
                z=offset * direction[2],
                vx=direction[0] * BALL_SPEED,
                vy=direction[1] * BALL_SPEED,
                vz=direction[2] * BALL_SPEED
            )
            self.balls.append(ball)
        
        # Keep self.ball as primary for backward compatibility
        self.ball = self.balls[0] if self.balls else None
        
        # ═══════════════════════════════════════════════════════════════════
        # INITIALIZE MULTI-BALL COMMAND CHAIN
        # ═══════════════════════════════════════════════════════════════════
        self.supreme_commander = None
        self.ball_commanders = {i: None for i in range(self.num_balls)}
        self.ball_commands = {i: None for i in range(self.num_balls)}
        self.ball_squads = {i: [] for i in range(self.num_balls)}
        self.reassignment_cooldown = 0
        
        # Initial squad assignment: distribute organisms evenly across balls
        if self.num_balls > 1 and self.enable_command_chain:
            self._assign_initial_squads()
        
        # Game state
        self.game_over = False
        self.winner = None
        self.frame_count = 0
        self.catch_log: List[Tuple[int, int, int]] = []  # (frame, catcher_idx, streak)
        self.miss_log: List[Tuple[int, Tuple[float, float]]] = []  # (frame, ball_position_theta_phi)
        
        # Camera rotation
        self.camera_angle = 0
        
        # Visual effects state
        self.impact_effects: List[Dict] = []  # Red shockwaves on miss
        self.catch_effects: List[Dict] = []   # Green flashes on catch
        self.ball_trails: Dict[int, List[Tuple[float, float, float]]] = {}  # Motion trails
        
        # Reset training tracking
        self.last_observations = {}
        self.last_actions = {}
    
    def _random_direction(self) -> Tuple[float, float, float]:
        """Generate random unit vector."""
        theta = self.rng.uniform(0, 2*math.pi)
        phi = self.rng.uniform(0.3, math.pi - 0.3)  # Avoid poles
        return (
            math.sin(phi) * math.cos(theta),
            math.cos(phi),
            math.sin(phi) * math.sin(theta)
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MULTI-BALL HIERARCHICAL COMMAND SYSTEM
    # ═══════════════════════════════════════════════════════════════════════
    
    def _assign_initial_squads(self):
        """
        Initially distribute organisms across balls evenly.
        Called at game start when num_balls > 1.
        """
        organisms_per_ball = len(self.alive_organisms) // self.num_balls
        remainder = len(self.alive_organisms) % self.num_balls
        
        org_list = list(self.alive_organisms)
        idx = 0
        
        for ball_idx in range(self.num_balls):
            # How many for this ball
            count = organisms_per_ball + (1 if ball_idx < remainder else 0)
            squad = org_list[idx:idx + count]
            
            self.ball_squads[ball_idx] = squad
            
            # Mark organisms with their assignment
            for org_idx in squad:
                self.organisms[org_idx].assigned_ball = ball_idx
            
            idx += count
        
        print(f"   📋 Initial squad assignment: {[len(s) for s in self.ball_squads.values()]} organisms per ball")
    
    def _update_supreme_commander(self):
        """
        Update who the supreme commander is based on total performance.
        Supreme commander is the organism with most total catches.
        """
        if not self.enable_command_chain or self.num_balls <= 1:
            return
        
        best_org = None
        best_catches = -1
        
        for org_idx in self.alive_organisms:
            org = self.organisms[org_idx]
            if org.catches > best_catches:
                best_catches = org.catches
                best_org = org_idx
        
        if best_org is not None and best_org != self.supreme_commander:
            # Crown new supreme commander
            if self.supreme_commander is not None:
                self.organisms[self.supreme_commander].is_supreme_commander = False
            
            self.supreme_commander = best_org
            self.organisms[best_org].is_supreme_commander = True
            
            if best_catches > 0:  # Only announce if they've actually caught something
                print(f"   👑 NEW SUPREME COMMANDER: Organism #{best_org} ({best_catches} catches)")
    
    def _reassign_squads_by_threat(self):
        """
        Supreme Commander reassigns organisms to balls based on threat assessment.
        
        Threat = ball speed + proximity to sphere surface
        More threatening balls get more defenders.
        
        Called periodically (with cooldown to prevent constant shuffling).
        """
        if not self.enable_command_chain or self.num_balls <= 1:
            return
        
        if self.reassignment_cooldown > 0:
            self.reassignment_cooldown -= 1
            return
        
        # Calculate threat level for each ball
        threats = []
        for ball_idx, ball in enumerate(self.balls):
            ball_pos = ball.get_position()
            dist_to_surface = SPHERE_RADIUS - math.sqrt(
                ball_pos[0]**2 + ball_pos[1]**2 + ball_pos[2]**2
            )
            speed = ball.get_speed()
            
            # Threat = inversely proportional to distance, proportional to speed
            threat = speed / max(0.1, dist_to_surface)
            threats.append((ball_idx, threat))
        
        # Sort balls by threat (highest first)
        threats.sort(key=lambda x: x[1], reverse=True)
        
        # Assign more organisms to higher threat balls
        total_threat = sum(t[1] for t in threats) or 1.0
        org_list = list(self.alive_organisms)
        self.rng.shuffle(org_list)  # Randomize who gets reassigned
        
        idx = 0
        for ball_idx, threat in threats:
            # Proportion of organisms based on threat
            proportion = threat / total_threat
            count = max(1, int(len(org_list) * proportion))
            
            # Don't overshoot
            count = min(count, len(org_list) - idx)
            
            squad = org_list[idx:idx + count]
            
            # Update assignments
            old_squad = self.ball_squads[ball_idx]
            if set(squad) != set(old_squad):
                self.ball_squads[ball_idx] = squad
                for org_idx in squad:
                    self.organisms[org_idx].assigned_ball = ball_idx
            
            idx += count
        
        # Cooldown before next reassignment (60 frames = ~1 second)
        self.reassignment_cooldown = 60
    
    def _get_ball_for_organism(self, organism_idx: int) -> Optional[Ball3D]:
        """
        Get the ball this organism should be tracking.
        Returns the assigned ball, or the closest ball if unassigned.
        """
        org = self.organisms.get(organism_idx)
        if org is None:
            return self.balls[0] if self.balls else None
        
        # If assigned to a specific ball, track that one
        if org.assigned_ball is not None and org.assigned_ball < len(self.balls):
            return self.balls[org.assigned_ball]
        
        # Otherwise track closest ball
        org_pos = org.get_position()
        closest_ball = None
        closest_dist = float('inf')
        
        for ball in self.balls:
            ball_pos = ball.get_position()
            dist = point_distance_3d(org_pos, ball_pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_ball = ball
        
        return closest_ball or (self.balls[0] if self.balls else None)

    def _get_observation(self, organism_idx: int) -> np.ndarray:
        """Get observation for organism's neural network."""
        org = self.organisms.get(organism_idx)
        if org is None or not org.alive:
            return np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        
        # Get the ball this organism is tracking
        ball = self._get_ball_for_organism(organism_idx)
        if ball is None:
            ball = self.ball  # Fallback
        
        ball_pos = ball.get_position()
        ball_vel = ball.get_velocity()
        org_pos = org.get_position()
        
        # Relative ball position
        rel_ball = (
            ball_pos[0] - org_pos[0],
            ball_pos[1] - org_pos[1],
            ball_pos[2] - org_pos[2]
        )
        
        # Distance to ball
        dist = point_distance_3d(ball_pos, org_pos)
        
        # Ball's spherical coordinates (for intercept prediction)
        ball_r, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
        
        # Angular distance to ball's projected sphere position
        angular_dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
        
        # Number alive
        num_alive = len(self.alive_organisms)
        
        # ═══════════════════════════════════════════════════════════════════
        # COMMAND CHAIN OBSERVATION
        # The organism can "hear" the commander's directive
        # ═══════════════════════════════════════════════════════════════════
        cmd_theta, cmd_phi = 0.0, 0.0
        cmd_dist = 0.0
        is_commander = 0.0
        has_command = 0.0
        
        if self.enable_command_chain and self.current_command is not None:
            cmd_theta, cmd_phi = self.current_command
            has_command = 1.0
            
            # Angular distance to commanded position
            cmd_dist = angular_distance(org.theta, org.phi, cmd_theta, cmd_phi)
            
            # Am I the commander?
            if self.current_commander == organism_idx:
                is_commander = 1.0
        
        obs = np.array([
            # Ball state (6)
            ball_pos[0] / SPHERE_RADIUS,
            ball_pos[1] / SPHERE_RADIUS,
            ball_pos[2] / SPHERE_RADIUS,
            ball_vel[0] / MAX_BALL_SPEED,
            ball_vel[1] / MAX_BALL_SPEED,
            ball_vel[2] / MAX_BALL_SPEED,
            # Own position (2)
            org.theta / (2 * math.pi),
            org.phi / math.pi,
            # Relative ball (3)
            rel_ball[0] / (2 * SPHERE_RADIUS),
            rel_ball[1] / (2 * SPHERE_RADIUS),
            rel_ball[2] / (2 * SPHERE_RADIUS),
            # Distances (2)
            dist / (2 * SPHERE_RADIUS),
            angular_dist / math.pi,
            # Game state (2)
            num_alive / 10,
            org.catches / 10,
            # ═══ COMMAND CHAIN INFO (5) ═══
            cmd_theta / (2 * math.pi),     # Commanded target theta
            cmd_phi / math.pi,              # Commanded target phi
            cmd_dist / math.pi,             # Distance to command target
            is_commander,                   # Am I the commander? (0/1)
            has_command,                    # Is there an active command? (0/1)
        ], dtype=np.float32)
        
        # Pad to observation size
        if len(obs) < OBSERVATION_SIZE:
            obs = np.pad(obs, (0, OBSERVATION_SIZE - len(obs)))
        
        return obs
    
    def _get_organism_action(self, organism_idx: int, state: np.ndarray) -> Tuple[float, float]:
        """
        Get action from organism's brain.
        Returns (d_theta, d_phi) movement deltas.
        
        The brain outputs action_probs (softmax over discrete actions).
        We interpret the action distribution as movement intention:
        - Use top actions to determine direction bias
        - NO perfect prediction - brain must "see" and "decide"
        
        Multi-ball: Each organism tracks its ASSIGNED ball (from supreme commander)
        """
        org = self.organisms.get(organism_idx)
        if not org:
            return (0, 0)
        
        # Get the ball this organism is assigned to track
        ball = self._get_ball_for_organism(organism_idx)
        if ball is None:
            ball = self.ball  # Fallback
        
        ball_pos = ball.get_position()
        ball_vel = ball.get_velocity()
        _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
        
        # Simple reactive: which direction is ball relative to me?
        theta_to_ball = ball_theta - org.theta
        while theta_to_ball > math.pi: theta_to_ball -= 2*math.pi
        while theta_to_ball < -math.pi: theta_to_ball += 2*math.pi
        phi_to_ball = ball_phi - org.phi
        
        # If commander gave orders for THIS ball, blend in that info
        cmd_bias_theta = 0.0
        cmd_bias_phi = 0.0
        if self.enable_command_chain and org.last_command_received is not None:
            cmd_theta, cmd_phi = org.last_command_received
            cmd_bias_theta = cmd_theta - org.theta
            while cmd_bias_theta > math.pi: cmd_bias_theta -= 2*math.pi
            while cmd_bias_theta < -math.pi: cmd_bias_theta += 2*math.pi
            cmd_bias_phi = cmd_phi - org.phi
        
        # Query brain for movement decision
        d_theta = 0.0
        d_phi = 0.0
        
        try:
            import torch
            
            brain = self.agent.brains[organism_idx]
            obs = np.asarray(state, dtype=np.float32).flatten()
            
            # Match brain input size
            target_dim = getattr(brain, 'input_dim', getattr(brain, 'input_size', OBSERVATION_SIZE))
            if len(obs) < target_dim:
                obs = np.pad(obs, (0, target_dim - len(obs)))
            elif len(obs) > target_dim:
                obs = obs[:target_dim]
            
            # VP integration if available
            vp_value = 0.5
            if hasattr(self.agent, 'vp_runtime'):
                try:
                    vp_data = self.agent.vp_runtime.compute_from_state(obs, [])
                    vp_value = vp_data.get('violation_pressure', 0.5)
                except:
                    pass
            
            device = getattr(self.agent, 'device', 'cpu')
            state_tensor = torch.FloatTensor(obs).unsqueeze(0).to(device)
            
            brain.eval()
            with torch.no_grad():
                output = brain(state_tensor, vp_value=vp_value, return_language_logits=False)
                
                if isinstance(output, tuple):
                    action_probs = output[0]
                else:
                    action_probs = output
                
                probs = action_probs.detach().cpu().numpy().flatten()
                
                # ═══════════════════════════════════════════════════════════
                # BRAIN-DRIVEN MOVEMENT (no cheating!)
                # ═══════════════════════════════════════════════════════════
                # Use the probability distribution to create movement intent
                # Higher values in certain action indices = direction preference
                
                n_actions = len(probs)
                
                # Method: Use probability values directly as "attention weights"
                # Split action space into directional buckets
                # This creates a mapping from action distribution -> 2D movement
                
                if n_actions >= 4:
                    # Divide action space into 4 quadrants
                    quarter = n_actions // 4
                    
                    # Sum probabilities in each directional bucket
                    up_weight = np.sum(probs[:quarter])           # Move -phi (up)
                    right_weight = np.sum(probs[quarter:2*quarter])  # Move +theta (right)
                    down_weight = np.sum(probs[2*quarter:3*quarter]) # Move +phi (down)
                    left_weight = np.sum(probs[3*quarter:])          # Move -theta (left)
                    
                    # Net movement from brain's "vote"
                    theta_vote = (right_weight - left_weight) * 2.0  # Scale up
                    phi_vote = (down_weight - up_weight) * 2.0
                    
                    # Confidence affects speed
                    confidence = float(np.max(probs))
                    speed = ORGANISM_MOVE_SPEED * (0.5 + confidence)
                    
                    # ═══════════════════════════════════════════════════════════
                    # 100% BRAIN-DRIVEN MOVEMENT - NO CHEATING!
                    # ═══════════════════════════════════════════════════════════
                    # The organism must LEARN to chase the ball through training.
                    # No reactive hand-holding. Pure neural network decision.
                    
                    # Command component still matters (20%) - following orders is learned behavior
                    # But only if there's an active command
                    cmd_theta_dir = np.sign(cmd_bias_theta) if abs(cmd_bias_theta) > 0.05 else 0
                    cmd_phi_dir = np.sign(cmd_bias_phi) if abs(cmd_bias_phi) > 0.05 else 0
                    
                    has_command = 1.0 if (abs(cmd_bias_theta) > 0.05 or abs(cmd_bias_phi) > 0.05) else 0.0
                    command_weight = 0.2 * has_command
                    brain_weight = 1.0 - command_weight
                    
                    # Final movement: brain controls everything (with optional command influence)
                    d_theta = speed * (
                        brain_weight * np.tanh(theta_vote) +
                        command_weight * cmd_theta_dir
                    )
                    d_phi = speed * (
                        brain_weight * np.tanh(phi_vote) +
                        command_weight * cmd_phi_dir
                    )
                    
                    # Add personality jitter based on entropy
                    entropy = -np.sum(probs * np.log(probs + 1e-8))
                    max_entropy = np.log(n_actions)
                    exploration = entropy / max_entropy if max_entropy > 0 else 0.5
                    
                    if exploration > 0.6:
                        # High uncertainty = some random exploration
                        d_theta += self.rng.uniform(-0.02, 0.02)
                        d_phi += self.rng.uniform(-0.01, 0.01)
                else:
                    # Too few actions - brain output directly maps to movement
                    # Still no cheating! Use whatever the brain outputs
                    d_theta = ORGANISM_MOVE_SPEED * np.tanh(probs[0] if len(probs) > 0 else 0)
                    d_phi = ORGANISM_MOVE_SPEED * np.tanh(probs[1] if len(probs) > 1 else 0)
                    
        except Exception as e:
            # Fallback on error: stay still (no cheating even in error case)
            d_theta = 0.0
            d_phi = 0.0
        
        # Clamp to max speed
        d_theta = np.clip(d_theta, -ORGANISM_MOVE_SPEED * 1.5, ORGANISM_MOVE_SPEED * 1.5)
        d_phi = np.clip(d_phi, -ORGANISM_MOVE_SPEED * 1.5, ORGANISM_MOVE_SPEED * 1.5)
        
        return (d_theta, d_phi)
    
    def _get_organism_action_with_idx(self, organism_idx: int, state: np.ndarray) -> Tuple[float, float, int]:
        """
        Get action from organism's brain, also returning the discrete action index.
        Used for training experience tracking.
        Returns (d_theta, d_phi, action_idx).
        """
        d_theta, d_phi = self._get_organism_action(organism_idx, state)
        
        # Get brain's output dimension to stay in bounds
        brain = self.agent.brains[organism_idx] if organism_idx < len(self.agent.brains) else self.agent.brains[0]
        output_dim = getattr(brain, 'output_dim', getattr(brain, 'output_size', 8))
        
        # Convert movement to discrete action index for experience buffer
        # Map to: 0=stay, 1=up, 2=right, 3=down, 4=left, 5=up-right, 6=down-right, 7=down-left
        # (capped at output_dim - 1 to avoid index errors)
        threshold = ORGANISM_MOVE_SPEED * 0.3
        
        up = d_phi < -threshold
        down = d_phi > threshold
        right = d_theta > threshold
        left = d_theta < -threshold
        
        if up and right:
            action_idx = 5
        elif down and right:
            action_idx = 6
        elif down and left:
            action_idx = 7
        elif up and left:
            action_idx = min(7, output_dim - 1)  # Clamp to max output dim
        elif up:
            action_idx = 1
        elif right:
            action_idx = 2
        elif down:
            action_idx = 3
        elif left:
            action_idx = 4
        else:
            action_idx = 0  # stay
        
        # Ensure action is within valid range
        action_idx = min(action_idx, output_dim - 1)
        
        # Debug log the action decision
        action_names = ['stay', 'up', 'right', 'down', 'left', 'up-right', 'down-right', 'down-left']
        action_name = action_names[action_idx] if action_idx < len(action_names) else f'action_{action_idx}'
        self._log_debug('BRAIN_DECISION', {
            'organism': organism_idx,
            'action_idx': action_idx,
            'action_name': action_name,
            'movement': (d_theta, d_phi),
            'confidence': 0.0,  # Would need brain query for real confidence
        })
        
        return (d_theta, d_phi, action_idx)
    
    def _add_experience(self, organism_idx: int, reward: float, done: bool = False):
        """
        Add an experience to the organism's buffer for training.
        Uses the stored last_observation and last_action.
        """
        if not self.enable_training:
            return
        
        if organism_idx not in self.last_observations:
            return
        
        last_obs = self.last_observations[organism_idx]
        action = self.last_actions.get(organism_idx, 0)
        
        # Get current observation as next_state
        next_obs = self._get_observation(organism_idx)
        
        # Pad states to match brain's expected input dimension
        # This is critical: brains expect their full input_dim, not arena's OBSERVATION_SIZE
        if hasattr(self.agent, 'brains') and organism_idx < len(self.agent.brains):
            brain = self.agent.brains[organism_idx]
            target_dim = getattr(brain, 'input_dim', getattr(brain, 'input_size', OBSERVATION_SIZE))
            
            # Pad last_obs
            last_obs = np.asarray(last_obs, dtype=np.float32).flatten()
            if len(last_obs) < target_dim:
                last_obs = np.pad(last_obs, (0, target_dim - len(last_obs)))
            elif len(last_obs) > target_dim:
                last_obs = last_obs[:target_dim]
            
            # Pad next_obs
            next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
            if len(next_obs) < target_dim:
                next_obs = np.pad(next_obs, (0, target_dim - len(next_obs)))
            elif len(next_obs) > target_dim:
                next_obs = next_obs[:target_dim]
        
        # Add to agent's experience buffer
        if hasattr(self.agent, 'experience_buffers') and organism_idx < len(self.agent.experience_buffers):
            self.agent.experience_buffers[organism_idx].add(
                state=last_obs,
                action=action,
                reward=reward,
                next_state=next_obs,
                done=done,
                input_tokens=None,
                target_tokens=None,
                vp_value=0.5
            )
            
            # Debug log the experience
            buffer_size = len(self.agent.experience_buffers[organism_idx])
            self._log_debug('EXPERIENCE_ADDED', {
                'organism': organism_idx,
                'action': action,
                'reward': reward,
                'done': done,
                'buffer_size': buffer_size,
                'reason': 'proximity' if abs(reward) < 0.3 else ('catch' if reward > 0 else 'miss'),
            })
    
    def _do_training_step(self):
        """
        Perform a training step on accumulated experiences.
        Called periodically during gameplay when enable_training=True.
        """
        if not hasattr(self.agent, 'train_step'):
            return
        
        # Debug: show buffer sizes periodically
        if hasattr(self.agent, 'experience_buffers'):
            buf_sizes = [len(buf) for buf in self.agent.experience_buffers[:min(8, len(self.agent.experience_buffers))]]
            batch_size = getattr(self.agent, 'batch_size', 32)
            if self.frame_count % 500 == 100:
                print(f"   📊 Buffer sizes: {buf_sizes} (need {batch_size} each)")
        
        try:
            loss = self.agent.train_step()
            print(f"   [DEBUG] train_step returned: {loss}")
            
            # Track training (handle NaN loss)
            import math
            if loss is not None and not math.isnan(loss):
                if loss > 0:
                    self.training_losses.append(loss)
                    if len(self.training_losses) % 5 == 1:
                        print(f"   📈 Training: step={len(self.training_losses)}, loss={loss:.4f}")
                    
                    # Debug log training step
                    buf_sizes = [len(buf) for buf in self.agent.experience_buffers[:8]] if hasattr(self.agent, 'experience_buffers') else []
                    self._log_debug('TRAINING_STEP', {
                        'step': len(self.training_losses),
                        'loss': loss,
                        'total_loss': loss,
                        'buffer_sizes': buf_sizes,
                        'batch_size': getattr(self.agent, 'batch_size', 32),
                        'brains_trained': len(self.agent.brains) if hasattr(self.agent, 'brains') else 0,
                    })
            elif loss is not None and math.isnan(loss):
                # NaN loss - numerical instability - still log it
                buf_sizes = [len(buf) for buf in self.agent.experience_buffers[:8]] if hasattr(self.agent, 'experience_buffers') else []
                self._log_debug('TRAINING_STEP', {
                    'step': len(self.training_losses),
                    'loss': float('nan'),
                    'total_loss': float('nan'),
                    'buffer_sizes': buf_sizes,
                    'batch_size': getattr(self.agent, 'batch_size', 32),
                    'brains_trained': 0,
                    'error': 'NaN loss - numerical instability',
                })
                if self.frame_count % 500 == 100:
                    print(f"   ⚠️ Training returned NaN (numerical instability)")
        except Exception as e:
            # Show training errors
            if self.frame_count % 500 == 100:
                print(f"   ❌ Training error: {type(e).__name__}: {e}")
    
    def _check_ball_collision(self):
        """
        Check ball collision with sphere surface for ALL balls.
        In SWARM_DEFENSE mode: ANY organism can catch - it's collective defense.
        """
        for ball_idx, ball in enumerate(self.balls):
            ball_pos = ball.get_position()
            dist_from_center = math.sqrt(ball_pos[0]**2 + ball_pos[1]**2 + ball_pos[2]**2)
            
            # Check if ball reached sphere surface
            if dist_from_center >= SPHERE_RADIUS - BALL_RADIUS:
                _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
                
                # SWARM DEFENSE: Check if ANY organism intercepts
                catcher = None
                min_catch_dist = float('inf')
                
                for org_idx in self.alive_organisms:
                    org = self.organisms[org_idx]
                    ang_dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                    
                    if ang_dist <= PADDLE_ANGULAR_RADIUS and ang_dist < min_catch_dist:
                        min_catch_dist = ang_dist
                        catcher = org_idx
                
                if catcher is not None:
                    # SWARM CATCH! Any organism intercepted this ball
                    self._handle_swarm_catch(ball, ball_pos, dist_from_center, catcher, ball_idx)
                else:
                    # SWARM MISS - collective failure
                    self._handle_swarm_miss(ball_theta, ball_phi, ball_idx)
    
    def _handle_swarm_catch(self, ball: Ball3D, ball_pos, dist_from_center, catcher_idx, ball_idx: int = 0):
        """
        Handle a successful swarm interception.
        
        COMMAND CHAIN SYSTEM:
        1. Evaluate how well the catcher followed the previous command
        2. The catcher becomes the NEW COMMANDER
        3. Commander predicts next impact point
        4. Commander broadcasts command to entire swarm
        5. All organisms receive the directive
        """
        # ✨ VISUAL EFFECT: Green ripple on catch
        catcher_color = self.organisms[catcher_idx].color if catcher_idx < len(self.organisms) else (0.4, 1.0, 0.4)
        self.catch_effects.append({
            'position': ball_pos,
            'frame': self.frame_count,
            'radius': 0.0,
            'max_radius': PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * 2,
            'color': catcher_color,
            'intensity': 1.0
        })
        
        # Reflect ball
        normal = normalize_vector(ball_pos)
        vel = ball.get_velocity()
        new_vel = reflect_vector(vel, normal)
        
        ball.vx = new_vel[0]
        ball.vy = new_vel[1]
        ball.vz = new_vel[2]
        
        # Speed up slightly (increases difficulty)
        ball.speed_up(1.02)
        
        # Move ball inside sphere
        scale = (SPHERE_RADIUS - BALL_RADIUS - 0.01) / dist_from_center
        ball.x *= scale
        ball.y *= scale
        ball.z *= scale
        
        # Update basic stats
        self.collective_catches += 1
        self.catch_streak += 1
        self.best_streak = max(self.best_streak, self.catch_streak)
        self.organisms[catcher_idx].catches += 1
        ball.last_hit_by = catcher_idx
        
        # ═══════════════════════════════════════════════════════════════════
        # POST-SNAPSHOT TRAINING: REWARD ON CATCH
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_training:
            # Catcher gets big reward (+1.0)
            self._add_experience(catcher_idx, reward=1.0, done=False)
            
            # Nearby organisms get small reward for good positioning (+0.2)
            # Organisms far from catch get tiny negative for being out of position (-0.1)
            _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
            for org_idx in self.alive_organisms:
                if org_idx == catcher_idx:
                    continue
                org = self.organisms[org_idx]
                dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                if dist < PADDLE_ANGULAR_RADIUS * 2:
                    # Near the action - good backup position
                    self._add_experience(org_idx, reward=0.2, done=False)
                elif dist > PADDLE_ANGULAR_RADIUS * 4:
                    # Too far away - could have been better positioned
                    self._add_experience(org_idx, reward=-0.1, done=False)
        
        # ═══════════════════════════════════════════════════════════════════
        # COMMAND CHAIN LOGIC (single-ball or per-ball commander)
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_command_chain:
            if self.num_balls > 1:
                # Multi-ball: catcher becomes BALL COMMANDER for this specific ball
                self._process_ball_command_chain(catcher_idx, ball_idx)
            else:
                # Single ball: legacy behavior
                self._process_command_chain(catcher_idx)
        
        # Log the catch
        self.catch_log.append((self.frame_count, catcher_idx, self.catch_streak))
        
        # Debug log the catch event
        self._log_debug('CATCH', {
            'catcher': catcher_idx,
            'ball_idx': ball_idx,
            'streak': self.catch_streak,
            'total_catches': self.collective_catches,
        })
        
        cmd_info = ""
        if self.enable_command_chain:
            if self.num_balls > 1 and self.ball_commanders.get(ball_idx) == catcher_idx:
                cmd_info = f" [BALL #{ball_idx} COMMANDER]"
            elif self.current_commander == catcher_idx:
                cmd_info = " [NOW COMMANDING]"
        
        ball_label = f" (ball #{ball_idx})" if self.num_balls > 1 else ""
        print(f"   🎯 SWARM CATCH by #{catcher_idx}!{cmd_info}{ball_label} (streak: {self.catch_streak})")
    
    def _process_command_chain(self, new_catcher_idx: int):
        """
        Process the hierarchical command chain transfer.
        
        The catcher becomes commander and broadcasts the next directive.
        Their command quality is judged by how well the swarm responds.
        """
        catcher = self.organisms[new_catcher_idx]
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Evaluate command compliance (how well did catcher follow orders?)
        # ─────────────────────────────────────────────────────────────────
        if self.current_commander is not None and self.current_command is not None:
            old_commander = self.organisms[self.current_commander]
            
            # Calculate how well the catcher followed the command
            cmd_theta, cmd_phi = self.current_command
            compliance = self._calculate_compliance(
                catcher.theta, catcher.phi,
                cmd_theta, cmd_phi
            )
            
            # Update catcher's command-following score
            catcher.commands_followed += 1
            catcher.command_score += compliance
            catcher.command_compliance = compliance
            
            # Update old commander's leadership score based on catch success
            # Good commands lead to catches!
            old_commander.leadership_score += 1.0  # Successful interception
            
            # Log the command result
            self.command_history[-1]['result'] = 'caught'
            self.command_history[-1]['catcher'] = new_catcher_idx
            self.command_history[-1]['compliance'] = compliance
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Transfer command to the catcher
        # ─────────────────────────────────────────────────────────────────
        self.current_commander = new_catcher_idx
        catcher.commands_issued += 1
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 3: Predict next impact point (commander's tactical analysis)
        # ─────────────────────────────────────────────────────────────────
        predicted_theta, predicted_phi = self._predict_impact_point()
        self.predicted_impact = (predicted_theta, predicted_phi)
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 4: Commander broadcasts directive to swarm
        # ─────────────────────────────────────────────────────────────────
        self.current_command = self._generate_swarm_command(
            new_catcher_idx, predicted_theta, predicted_phi
        )
        self.command_broadcast_frame = self.frame_count
        
        # Broadcast to all organisms
        for org_idx in self.alive_organisms:
            if org_idx != new_catcher_idx:
                self.organisms[org_idx].last_command_received = self.current_command
                self.organisms[org_idx].command_compliance = 0.0  # Reset for new command
        
        # Log the new command
        self.command_history.append({
            'frame': self.frame_count,
            'commander': new_catcher_idx,
            'command': self.current_command,
            'predicted_impact': self.predicted_impact,
            'result': None,  # Will be filled on next catch/miss
            'catcher': None,
            'compliance': None
        })
        
        # Debug log the command
        self._log_debug('COMMAND_ISSUED', {
            'commander': new_catcher_idx,
            'target': self.current_command,
            'predicted_impact': self.predicted_impact,
        })
    
    def _process_ball_command_chain(self, catcher_idx: int, ball_idx: int):
        """
        Process command chain for a specific ball in multi-ball mode.
        
        Each ball has its own commander who issues orders to their squad.
        """
        catcher = self.organisms[catcher_idx]
        ball = self.balls[ball_idx]
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 1: Catcher becomes this ball's commander
        # ─────────────────────────────────────────────────────────────────
        old_commander = self.ball_commanders.get(ball_idx)
        if old_commander is not None and old_commander in self.organisms:
            self.organisms[old_commander].is_ball_commander = False
        
        self.ball_commanders[ball_idx] = catcher_idx
        catcher.is_ball_commander = True
        catcher.commands_issued += 1
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 2: Predict where THIS ball will hit
        # ─────────────────────────────────────────────────────────────────
        predicted_theta, predicted_phi = self._predict_ball_impact(ball)
        
        # ─────────────────────────────────────────────────────────────────
        # STEP 3: Issue command to organisms assigned to this ball
        # ─────────────────────────────────────────────────────────────────
        self.ball_commands[ball_idx] = (predicted_theta, predicted_phi)
        
        # Broadcast to squad members only
        squad = self.ball_squads.get(ball_idx, [])
        for org_idx in squad:
            if org_idx != catcher_idx and org_idx in self.organisms:
                self.organisms[org_idx].last_command_received = (predicted_theta, predicted_phi)
                self.organisms[org_idx].command_compliance = 0.0
    
    def _predict_ball_impact(self, ball: Ball3D) -> Tuple[float, float]:
        """Predict where a specific ball will hit the sphere surface."""
        bx, by, bz = ball.x, ball.y, ball.z
        vx, vy, vz = ball.vx, ball.vy, ball.vz
        
        # Ray-sphere intersection
        a = vx*vx + vy*vy + vz*vz
        b = 2 * (bx*vx + by*vy + bz*vz)
        c = bx*bx + by*by + bz*bz - SPHERE_RADIUS*SPHERE_RADIUS
        
        discriminant = b*b - 4*a*c
        
        if discriminant < 0 or a == 0:
            speed = math.sqrt(vx*vx + vy*vy + vz*vz)
            if speed > 0:
                impact_x = SPHERE_RADIUS * vx / speed
                impact_y = SPHERE_RADIUS * vy / speed
                impact_z = SPHERE_RADIUS * vz / speed
            else:
                impact_x, impact_y, impact_z = SPHERE_RADIUS, 0, 0
        else:
            t1 = (-b + math.sqrt(discriminant)) / (2*a)
            t2 = (-b - math.sqrt(discriminant)) / (2*a)
            t = max(t1, t2)
            if t < 0:
                t = min(t1, t2) if min(t1, t2) > 0 else 1.0
            
            impact_x = bx + t * vx
            impact_y = by + t * vy
            impact_z = bz + t * vz
        
        _, impact_theta, impact_phi = cartesian_to_spherical(impact_x, impact_y, impact_z)
        return (impact_theta, impact_phi)

    def _predict_impact_point(self) -> Tuple[float, float]:
        """
        Predict where the ball will hit the sphere surface next.
        
        Uses ray-sphere intersection to find the impact point.
        This is what the commander "sees" and broadcasts.
        """
        # Current ball state
        bx, by, bz = self.ball.x, self.ball.y, self.ball.z
        vx, vy, vz = self.ball.vx, self.ball.vy, self.ball.vz
        
        # Ray-sphere intersection
        # Ball travels from (bx,by,bz) in direction (vx,vy,vz)
        # Find t where |pos + t*vel| = SPHERE_RADIUS
        
        # Quadratic: |p + tv|^2 = R^2
        # (p·p) + 2t(p·v) + t^2(v·v) = R^2
        a = vx*vx + vy*vy + vz*vz
        b = 2 * (bx*vx + by*vy + bz*vz)
        c = bx*bx + by*by + bz*bz - SPHERE_RADIUS*SPHERE_RADIUS
        
        discriminant = b*b - 4*a*c
        
        if discriminant < 0 or a == 0:
            # Fallback: use velocity direction projected onto sphere
            speed = math.sqrt(vx*vx + vy*vy + vz*vz)
            if speed > 0:
                impact_x = SPHERE_RADIUS * vx / speed
                impact_y = SPHERE_RADIUS * vy / speed
                impact_z = SPHERE_RADIUS * vz / speed
            else:
                impact_x, impact_y, impact_z = SPHERE_RADIUS, 0, 0
        else:
            # Take the positive t (future intersection)
            t1 = (-b + math.sqrt(discriminant)) / (2*a)
            t2 = (-b - math.sqrt(discriminant)) / (2*a)
            t = max(t1, t2)  # Want future intersection
            if t < 0:
                t = min(t1, t2) if min(t1, t2) > 0 else 1.0
            
            impact_x = bx + t * vx
            impact_y = by + t * vy
            impact_z = bz + t * vz
        
        # Convert to spherical coordinates
        _, impact_theta, impact_phi = cartesian_to_spherical(impact_x, impact_y, impact_z)
        
        return (impact_theta, impact_phi)
    
    def _generate_swarm_command(
        self, 
        commander_idx: int, 
        predicted_theta: float, 
        predicted_phi: float
    ) -> Tuple[float, float]:
        """
        Generate the swarm command from the commander.
        
        The command is the predicted impact point, possibly modified by
        the commander's neural network output to add tactical adjustment.
        
        This is where the commander's "mind expands through the swarm".
        """
        # Base command is the predicted impact point
        cmd_theta = predicted_theta
        cmd_phi = predicted_phi
        
        # Optional: Let commander's brain influence the command
        # This allows evolved tactical behavior
        try:
            brain = self.agent.brains[commander_idx]
            
            # Create a "command observation" - what the commander sees
            obs = self._get_observation(commander_idx)
            
            # Get commander's neural output
            vp_value = self.agent.vp_runtime if hasattr(self.agent, 'vp_runtime') else 0.5
            if hasattr(brain, 'forward'):
                output = brain.forward(obs, vp_value=vp_value)
                
                # Use output to adjust command (small tactical tweaks)
                # Output[0], Output[1] could modify the target slightly
                if len(output) >= 2:
                    # Allow up to ±0.3 radians adjustment
                    cmd_theta += 0.3 * float(output[0])
                    cmd_phi += 0.2 * float(output[1])
                    cmd_phi = max(0.1, min(math.pi - 0.1, cmd_phi))
        except Exception:
            pass  # Use raw prediction if brain query fails
        
        return (cmd_theta, cmd_phi)
    
    def _calculate_compliance(
        self, 
        org_theta: float, 
        org_phi: float, 
        cmd_theta: float, 
        cmd_phi: float
    ) -> float:
        """
        Calculate how well an organism followed the command.
        
        Returns 0.0 (far from target) to 1.0 (exactly at target).
        """
        ang_dist = angular_distance(org_theta, org_phi, cmd_theta, cmd_phi)
        
        # Convert to compliance score (1.0 if at target, 0.0 if far)
        # Using exponential decay with characteristic scale
        compliance = math.exp(-ang_dist / 0.5)  # 0.5 radian characteristic distance
        
        return compliance

    def _handle_swarm_miss(self, ball_theta, ball_phi, ball_idx: int = 0):
        """Handle a collective miss - the swarm failed to intercept."""
        self.collective_misses += 1
        old_streak = self.catch_streak
        self.catch_streak = 0  # Reset streak
        
        # 💥 VISUAL EFFECT: Red shockwave on miss
        impact_pos = spherical_to_cartesian(ball_theta, ball_phi, SPHERE_RADIUS)
        self.impact_effects.append({
            'position': impact_pos,
            'frame': self.frame_count,
            'radius': 0.0,
            'max_radius': PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * 3,
            'intensity': 1.0,
            'streak_broken': old_streak
        })
        
        # Find nearest organism to the miss
        nearest_org = None
        nearest_dist = float('inf')
        for org_idx in self.alive_organisms:
            org = self.organisms[org_idx]
            dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_org = org_idx
        
        # Log the miss location
        self.miss_log.append((self.frame_count, (ball_theta, ball_phi)))
        
        # Debug log the miss event
        self._log_debug('MISS', {
            'ball_idx': ball_idx,
            'position': (ball_theta, ball_phi),
            'nearest_organism': nearest_org,
            'nearest_dist': nearest_dist,
            'total_misses': self.collective_misses,
        })
        
        ball_label = f" (ball #{ball_idx})" if self.num_balls > 1 else ""
        print(f"   ❌ SWARM MISS!{ball_label} ({self.collective_misses}/{self.max_misses}) - Gap at θ={ball_theta:.2f}, φ={ball_phi:.2f}")
        
        # ═══════════════════════════════════════════════════════════════════
        # POST-SNAPSHOT TRAINING: PENALTY ON MISS
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_training:
            # Penalize organisms based on how far they were from the miss point
            for org_idx in self.alive_organisms:
                org = self.organisms[org_idx]
                dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                
                if dist < PADDLE_ANGULAR_RADIUS * 2:
                    # Was close but missed - moderate penalty
                    self._add_experience(org_idx, reward=-0.3, done=False)
                elif dist < PADDLE_ANGULAR_RADIUS * 4:
                    # Was in range but not close enough - small penalty
                    self._add_experience(org_idx, reward=-0.5, done=False)
                else:
                    # Was far away - bigger penalty for bad positioning
                    self._add_experience(org_idx, reward=-0.8, done=False)
        
        # Check if game over
        is_final = self.collective_misses >= self.max_misses
        
        if is_final:
            self.game_over = True
            self.winner = None  # No winner - swarm failed
            print(f"   💀 SWARM DEFENSE FAILED! Best streak: {self.best_streak}, Total catches: {self.collective_catches}")
            
            # Add terminal experience for all organisms
            if self.enable_training:
                for org_idx in self.alive_organisms:
                    self._add_experience(org_idx, reward=-1.0, done=True)
        else:
            self._reset_ball(ball_idx)
    
    def _reset_ball(self, ball_idx: int = 0):
        """Reset specific ball to center with random direction."""
        if ball_idx >= len(self.balls):
            return
        ball = self.balls[ball_idx]
        ball.x = 0
        ball.y = 0
        ball.z = 0
        direction = self._random_direction()
        ball.vx = direction[0] * BALL_SPEED
        ball.vy = direction[1] * BALL_SPEED
        ball.vz = direction[2] * BALL_SPEED
    
    def step(self) -> bool:
        """Advance one frame."""
        if self.game_over:
            return False
        
        self.frame_count += 1
        
        # ═══════════════════════════════════════════════════════════════════
        # MULTI-BALL COMMAND CHAIN UPDATES
        # ═══════════════════════════════════════════════════════════════════
        if self.num_balls > 1 and self.enable_command_chain:
            # Update supreme commander based on performance
            if self.frame_count % 30 == 0:  # Every ~0.5 seconds
                self._update_supreme_commander()
            
            # Supreme commander can reassign squads based on threat
            if self.supreme_commander is not None:
                self._reassign_squads_by_threat()
        
        # Get actions and move organisms (tracking for training)
        for org_idx in self.alive_organisms:
            obs = self._get_observation(org_idx)
            
            # Store observation before action for experience buffer
            if self.enable_training:
                self.last_observations[org_idx] = obs.copy()
            
            d_theta, d_phi, action_idx = self._get_organism_action_with_idx(org_idx, obs)
            self.organisms[org_idx].move(d_theta, d_phi)
            
            # Store action for experience buffer
            if self.enable_training:
                self.last_actions[org_idx] = action_idx
        
        # Move all balls and track trails
        for ball_idx, ball in enumerate(self.balls):
            # 🎯 VISUAL EFFECT: Track ball trail for motion blur
            if ball_idx not in self.ball_trails:
                self.ball_trails[ball_idx] = []
            self.ball_trails[ball_idx].append(ball.get_position())
            if len(self.ball_trails[ball_idx]) > 8:
                self.ball_trails[ball_idx].pop(0)
            
            ball.move()
        
        # ═══════════════════════════════════════════════════════════════════
        # CONTINUOUS EXPERIENCE COLLECTION (every 10 frames)
        # ═══════════════════════════════════════════════════════════════════
        # Add small reward/penalty based on positioning relative to nearest ball
        # This gives organisms feedback BEFORE catch/miss events
        if self.enable_training and self.frame_count % 10 == 0:
            for org_idx in self.alive_organisms:
                org = self.organisms[org_idx]
                
                # Find nearest ball and distance
                min_dist = float('inf')
                for ball in self.balls:
                    ball_pos = ball.get_position()
                    _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
                    dist = angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                    min_dist = min(min_dist, dist)
                
                # Reward for being close to a ball, penalty for being far
                if min_dist < PADDLE_ANGULAR_RADIUS * 2:
                    # Very close - good positioning
                    self._add_experience(org_idx, reward=0.1, done=False)
                elif min_dist < PADDLE_ANGULAR_RADIUS * 4:
                    # Moderate distance - neutral
                    self._add_experience(org_idx, reward=0.0, done=False)
                else:
                    # Far from all balls - bad positioning
                    self._add_experience(org_idx, reward=-0.05, done=False)
        
        # Check collisions for all balls
        self._check_ball_collision()
        
        # ═══════════════════════════════════════════════════════════════════
        # POST-SNAPSHOT TRAINING
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_training and self.frame_count % self.train_interval == 0:
            self._do_training_step()
        
        return not self.game_over
    
    def render(self):
        """Render the arena."""
        if self.headless:
            return
        
        if OPENGL_AVAILABLE:
            self._render_opengl()
        else:
            self._render_2d_fallback()
    
    def _render_opengl(self):
        """Render with OpenGL."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera position - rotate around scene
        self.camera_angle += 0.2
        cam_dist = 6
        cam_x = cam_dist * math.sin(math.radians(self.camera_angle))
        cam_z = cam_dist * math.cos(math.radians(self.camera_angle))
        gluLookAt(cam_x, 3, cam_z, 0, 0, 0, 0, 1, 0)
        
        # Draw wireframe sphere
        glColor3f(0.2, 0.2, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        quad = gluNewQuadric()
        gluSphere(quad, SPHERE_RADIUS, 24, 16)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Draw organisms as colored patches
        for org_idx in self.alive_organisms:
            org = self.organisms[org_idx]
            pos = org.get_position()
            
            glPushMatrix()
            glTranslatef(*pos)
            
            # Draw paddle as disk facing outward
            glColor3f(*org.color)
            
            # Align disk to sphere normal
            normal = org.get_normal()
            # Calculate rotation to align Z axis with normal
            up = (0, 1, 0)
            right = cross_product(up, normal)
            right = normalize_vector(right) if right != (0,0,0) else (1,0,0)
            up = cross_product(normal, right)
            
            # Draw small sphere for organism
            quad = gluNewQuadric()
            gluSphere(quad, 0.12, 12, 8)
            
            glPopMatrix()
            
            # Draw paddle zone indicator (circle on sphere)
            self._draw_paddle_zone(org)
        
        # Draw balls (support multiple)
        ball_colors = [(1.0, 1.0, 0.0), (1.0, 0.5, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0), (0.5, 1.0, 0.5)]
        for ball_idx, ball in enumerate(self.balls):
            ball_pos = ball.get_position()
            color = ball_colors[ball_idx % len(ball_colors)]
            
            # 🎯 VISUAL EFFECT 1: Ball motion trail
            if ball_idx in self.ball_trails and len(self.ball_trails[ball_idx]) > 1:
                trail = self.ball_trails[ball_idx]
                for i, trail_pos in enumerate(trail[:-1]):
                    alpha = (i + 1) / len(trail) * 0.4
                    trail_radius = BALL_RADIUS * (0.3 + 0.7 * (i + 1) / len(trail))
                    
                    glPushMatrix()
                    glTranslatef(*trail_pos)
                    glColor4f(color[0], color[1], color[2], alpha)
                    quad = gluNewQuadric()
                    gluSphere(quad, trail_radius, 6, 4)
                    glPopMatrix()
            
            # 🎯 VISUAL EFFECT 2: Depth-based shading
            ball_dist = math.sqrt(ball_pos[0]**2 + ball_pos[1]**2 + ball_pos[2]**2)
            depth_factor = 0.5 + 0.5 * (1 - ball_dist / (SPHERE_RADIUS * 1.2))
            depth_factor = max(0.4, min(1.0, depth_factor))
            
            # 🎯 VISUAL EFFECT 3: Size scaling with depth
            size_scale = 0.8 + 0.4 * depth_factor
            
            # 🎯 VISUAL EFFECT 4: Pulsing glow
            pulse = 0.8 + 0.2 * math.sin(self.frame_count * 0.15 + ball_idx)
            
            # Draw main ball
            glPushMatrix()
            glTranslatef(*ball_pos)
            glColor3f(color[0] * depth_factor * pulse, color[1] * depth_factor * pulse, color[2] * depth_factor * pulse)
            quad = gluNewQuadric()
            gluSphere(quad, BALL_RADIUS * size_scale, 12, 8)
            glPopMatrix()
            
            # 🎯 VISUAL EFFECT 5: Ball shadow on sphere surface
            if ball_dist > 0:
                shadow_pos = (
                    ball_pos[0] * SPHERE_RADIUS / ball_dist,
                    ball_pos[1] * SPHERE_RADIUS / ball_dist,
                    ball_pos[2] * SPHERE_RADIUS / ball_dist
                )
                shadow_alpha = 0.3 * (1 - abs(ball_dist - SPHERE_RADIUS) / SPHERE_RADIUS)
                shadow_alpha = max(0.05, min(0.3, shadow_alpha))
                
                glPushMatrix()
                glTranslatef(*shadow_pos)
                glColor4f(0.0, 0.0, 0.0, shadow_alpha)
                quad = gluNewQuadric()
                gluSphere(quad, BALL_RADIUS * 0.8, 8, 4)
                glPopMatrix()
        
        # 💥 VISUAL EFFECT 6: Red shockwave on miss
        effects_to_remove = []
        for i, effect in enumerate(self.impact_effects):
            age = self.frame_count - effect['frame']
            if age > 30:
                effects_to_remove.append(i)
                continue
            
            progress = age / 30.0
            effect['radius'] = effect['max_radius'] * progress
            effect['intensity'] = 1.0 - progress
            
            streak_multiplier = 1.0 + 0.2 * min(effect.get('streak_broken', 0), 5)
            radius = effect['radius'] * streak_multiplier
            
            pos = effect['position']
            normal = normalize_vector(pos)
            
            up = (0, 1, 0)
            if abs(dot_product(normal, up)) > 0.9:
                up = (1, 0, 0)
            tangent1 = normalize_vector(cross_product(normal, up))
            tangent2 = cross_product(normal, tangent1)
            
            glColor4f(1.0, 0.2, 0.1, effect['intensity'] * 0.8)
            glLineWidth(2.0 + 3.0 * effect['intensity'])
            
            glBegin(GL_LINE_LOOP)
            for j in range(48):
                angle = 2 * math.pi * j / 48
                offset_x = radius * math.cos(angle)
                offset_y = radius * math.sin(angle)
                point = (
                    pos[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                    pos[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                    pos[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
                )
                point = normalize_vector(point)
                point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
                glVertex3f(*point)
            glEnd()
            glLineWidth(1.0)
        
        for i in reversed(effects_to_remove):
            self.impact_effects.pop(i)
        
        # ✨ VISUAL EFFECT 7: Green ripple on catch
        effects_to_remove = []
        for i, effect in enumerate(self.catch_effects):
            age = self.frame_count - effect['frame']
            if age > 20:
                effects_to_remove.append(i)
                continue
            
            progress = age / 20.0
            effect['radius'] = effect['max_radius'] * progress
            effect['intensity'] = 1.0 - progress
            
            pos = effect['position']
            dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
            if dist > 0:
                pos = (pos[0]*SPHERE_RADIUS/dist, pos[1]*SPHERE_RADIUS/dist, pos[2]*SPHERE_RADIUS/dist)
            
            normal = normalize_vector(pos)
            
            up = (0, 1, 0)
            if abs(dot_product(normal, up)) > 0.9:
                up = (1, 0, 0)
            tangent1 = normalize_vector(cross_product(normal, up))
            tangent2 = cross_product(normal, tangent1)
            
            c = effect['color']
            glColor4f(c[0] * 0.5 + 0.5, c[1] * 0.5 + 0.5, c[2] * 0.3, effect['intensity'] * 0.7)
            glLineWidth(3.0 * effect['intensity'] + 1.0)
            
            glBegin(GL_LINE_LOOP)
            for j in range(32):
                angle = 2 * math.pi * j / 32
                offset_x = effect['radius'] * math.cos(angle)
                offset_y = effect['radius'] * math.sin(angle)
                point = (
                    pos[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                    pos[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                    pos[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
                )
                point = normalize_vector(point)
                point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
                glVertex3f(*point)
            glEnd()
            glLineWidth(1.0)
        
        for i in reversed(effects_to_remove):
            self.catch_effects.pop(i)
        
        pygame.display.flip()
    
    def _draw_paddle_zone(self, org: SphereOrganism):
        """Draw the paddle zone as a circle on the sphere."""
        if not OPENGL_AVAILABLE:
            return
        
        glColor4f(*org.color, 0.3)
        glBegin(GL_LINE_LOOP)
        
        # Draw circle around organism position on sphere
        center = org.get_position()
        normal = org.get_normal()
        
        # Find two perpendicular vectors on the tangent plane
        up = (0, 1, 0)
        if abs(dot_product(normal, up)) > 0.9:
            up = (1, 0, 0)
        tangent1 = normalize_vector(cross_product(normal, up))
        tangent2 = cross_product(normal, tangent1)
        
        # Draw circle
        for i in range(32):
            angle = 2 * math.pi * i / 32
            # Point on circle in tangent plane
            offset_x = PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * math.cos(angle)
            offset_y = PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * math.sin(angle)
            
            point = (
                center[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                center[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                center[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
            )
            # Project back to sphere
            point = normalize_vector(point)
            point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
            glVertex3f(*point)
        
        glEnd()
    
    def _render_2d_fallback(self):
        """Simple 2D projection fallback when OpenGL unavailable."""
        self.screen.fill((0, 0, 0))
        
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        scale = 150
        
        # Draw sphere outline
        pygame.draw.circle(self.screen, (50, 50, 80), (cx, cy), int(SPHERE_RADIUS * scale), 2)
        
        # Draw organisms (projected to 2D)
        for org_idx in self.alive_organisms:
            org = self.organisms[org_idx]
            pos = org.get_position()
            # Simple projection
            screen_x = int(cx + pos[0] * scale)
            screen_y = int(cy - pos[1] * scale)
            color = tuple(int(c * 255) for c in org.color)
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), 15)
            
            # Label
            font = pygame.font.Font(None, 20)
            label = font.render(f"#{org_idx}", True, color)
            self.screen.blit(label, (screen_x - 10, screen_y - 25))
        
        # Draw ball
        ball_pos = self.ball.get_position()
        screen_x = int(cx + ball_pos[0] * scale)
        screen_y = int(cy - ball_pos[1] * scale)
        pygame.draw.circle(self.screen, (255, 255, 0), (screen_x, screen_y), 8)
        
        # Info
        font = pygame.font.Font(None, 30)
        info = font.render(f"Alive: {len(self.alive_organisms)} | Frame: {self.frame_count}", True, (255, 255, 255))
        self.screen.blit(info, (10, 10))
        
        pygame.display.flip()
    
    def run(self, fps: int = 60, max_frames: int = 10000) -> Dict[str, Any]:
        """Run the arena until game over or time limit."""
        mode_str = self.mode.value.upper()
        print(f"\n🌐 SPHERE ARENA - 3D {mode_str}")
        print(f"   Mode: {mode_str}")
        print(f"   Organisms: {len(self.organism_indices)}")
        
        if self.mode == GameMode.SWARM_DEFENSE:
            print(f"   Max Misses: {self.max_misses} (collective)")
            print(f"   Rule: ANY organism can catch - swarm succeeds as ONE")
        elif self.mode == GameMode.ELIMINATION:
            print(f"   Individual competition mode")
        
        print(f"   Ball bounces in full 3D inside sphere")
        print()
        
        running = True
        
        while running and self.frame_count < max_frames:
            if not self.headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
            
            if not self.step():
                running = False
            
            self.render()
            
            if self.clock:
                self.clock.tick(fps)
        
        if self.frame_count >= max_frames and not self.game_over:
            self.game_over = True
            print(f"   ⏱️ Time limit reached!")
            if self.mode == GameMode.SWARM_DEFENSE:
                print(f"   🏆 SWARM SURVIVED! Catches: {self.collective_catches}, Best streak: {self.best_streak}")
        
        if not self.headless:
            pygame.quit()
        
        # Build results dictionary
        results = {
            'mode': self.mode.value,
            'total_frames': self.frame_count,
            'seed': self.seed,
            'final_stats': {idx: {
                'catches': o.catches, 
                'misses': o.misses,
                'commands_issued': o.commands_issued,
                'commands_followed': o.commands_followed,
                'command_score': o.command_score,
                'leadership_score': o.leadership_score,
            } for idx, o in self.organisms.items()},
        }
        
        # Add swarm defense specific stats
        if self.mode == GameMode.SWARM_DEFENSE:
            results.update({
                'collective_catches': self.collective_catches,
                'collective_misses': self.collective_misses,
                'best_streak': self.best_streak,
                'catch_log': self.catch_log,
                'miss_log': self.miss_log,
                'survived': self.collective_misses < self.max_misses,
            })
            
            # ═══════════════════════════════════════════════════════════════════
            # COMMAND CHAIN RESULTS
            # ═══════════════════════════════════════════════════════════════════
            if self.enable_command_chain:
                # Find best commander (highest leadership score)
                best_commander = max(
                    self.organisms.items(),
                    key=lambda x: x[1].leadership_score,
                    default=(None, None)
                )
                
                # Find best follower (highest command compliance average)
                best_follower = max(
                    self.organisms.items(),
                    key=lambda x: x[1].command_score / max(1, x[1].commands_followed),
                    default=(None, None)
                )
                
                results.update({
                    'command_history': self.command_history,
                    'best_commander': best_commander[0] if best_commander[1] else None,
                    'best_follower': best_follower[0] if best_follower[1] else None,
                    'total_commands': len(self.command_history),
                    'command_chain_enabled': True,
                })
        else:
            results.update({
                'winner': self.winner,
                'eliminations': self.eliminations,
            })
        
        # ═══════════════════════════════════════════════════════════════════
        # POST-SNAPSHOT TRAINING RESULTS
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_training:
            results['training'] = {
                'enabled': True,
                'training_steps': len(self.training_losses),
                'avg_loss': sum(self.training_losses) / max(1, len(self.training_losses)),
                'final_loss': self.training_losses[-1] if self.training_losses else 0.0,
            }
            
            if self.training_losses:
                print(f"\n📈 TRAINING SUMMARY:")
                print(f"   Training steps: {len(self.training_losses)}")
                print(f"   Average loss: {results['training']['avg_loss']:.4f}")
                print(f"   Final loss: {results['training']['final_loss']:.4f}")
                
                # Offer to save updated weights
                if not self.headless:
                    save_prompt = input("\n💾 Save trained weights? (y/N): ").strip().lower()
                    if save_prompt == 'y':
                        self._save_trained_weights()
        
        # ═══════════════════════════════════════════════════════════════════
        # VERBOSE DEBUG SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        if self.verbose:
            print(f"\n🔍 VERBOSE DEBUG SUMMARY")
            print("=" * 60)
            
            # Action summary
            action_counts = {}
            for entry in self.debug_log['actions']:
                action = entry.get('action_name', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
            
            print(f"\n📍 ACTIONS ({len(self.debug_log['actions'])} total):")
            for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
                print(f"   {action}: {count}")
            
            # Experience summary
            print(f"\n📦 EXPERIENCES ({len(self.debug_log['experiences'])} total):")
            if self.debug_log['experiences']:
                rewards = [e.get('reward', 0) for e in self.debug_log['experiences']]
                print(f"   Reward range: [{min(rewards):.2f}, {max(rewards):.2f}]")
                print(f"   Mean reward: {sum(rewards)/len(rewards):.3f}")
                
                # Experience by organism
                by_org = {}
                for e in self.debug_log['experiences']:
                    org = e.get('organism', -1)
                    by_org[org] = by_org.get(org, 0) + 1
                print(f"   Per organism: {dict(sorted(by_org.items()))}")
            
            # Training summary
            print(f"\n🧠 TRAINING ({len(self.debug_log['training'])} steps):")
            if self.debug_log['training']:
                losses = [t.get('total_loss', 0) for t in self.debug_log['training'] 
                         if not isinstance(t.get('total_loss'), float) or not (t.get('total_loss') != t.get('total_loss'))]  # filter NaN
                if losses:
                    print(f"   Loss range: [{min(losses):.4f}, {max(losses):.4f}]")
                nan_count = sum(1 for t in self.debug_log['training'] 
                               if isinstance(t.get('total_loss'), float) and t.get('total_loss') != t.get('total_loss'))
                if nan_count:
                    print(f"   ⚠️ NaN losses: {nan_count}")
            
            # Command summary
            print(f"\n📢 COMMANDS ({len(self.debug_log['commands'])} total):")
            if self.debug_log['commands']:
                by_issuer = {}
                for c in self.debug_log['commands']:
                    issuer = c.get('commander', c.get('issuer', -1))
                    by_issuer[issuer] = by_issuer.get(issuer, 0) + 1
                print(f"   By organism: {dict(sorted(by_issuer.items()))}")
            
            # ═══════════════════════════════════════════════════════════════
            # PER-ORGANISM ACTIVITY SUMMARY
            # ═══════════════════════════════════════════════════════════════
            print(f"\n🦠 PER-ORGANISM SUMMARY")
            print("-" * 60)
            
            for org_idx in sorted(self.organisms.keys()):
                org = self.organisms[org_idx]
                
                # Get organism name if available
                org_name = ""
                if hasattr(self.agent, 'organism_names') and org_idx < len(self.agent.organism_names):
                    org_name = f" ({self.agent.organism_names[org_idx][:8]}...)"
                
                print(f"\n   Organism #{org_idx}{org_name}:")
                
                # Catches and misses
                print(f"      🎯 Catches: {org.catches}")
                
                # Commands issued/followed
                if self.enable_command_chain:
                    print(f"      📢 Commands issued: {org.commands_issued}")
                    print(f"      📋 Commands followed: {org.commands_followed}")
                    print(f"      ⭐ Leadership score: {org.leadership_score:.2f}")
                
                # Actions taken (from debug log)
                org_actions = [a for a in self.debug_log['actions'] if a.get('organism') == org_idx]
                if org_actions:
                    action_dist = {}
                    for a in org_actions:
                        act = a.get('action_name', f"action_{a.get('action_idx', '?')}")
                        action_dist[act] = action_dist.get(act, 0) + 1
                    top_actions = sorted(action_dist.items(), key=lambda x: -x[1])[:3]
                    actions_str = ", ".join([f"{act}:{cnt}" for act, cnt in top_actions])
                    print(f"      🎮 Top actions: {actions_str}")
                
                # Experiences collected
                org_exps = [e for e in self.debug_log['experiences'] if e.get('organism') == org_idx]
                if org_exps:
                    rewards = [e.get('reward', 0) for e in org_exps]
                    total_reward = sum(rewards)
                    print(f"      📦 Experiences: {len(org_exps)} (total reward: {total_reward:+.2f})")
                
                # Movement stats
                org_moves = [a.get('movement', (0, 0)) for a in org_actions]
                if org_moves:
                    avg_d_theta = sum(m[0] for m in org_moves) / len(org_moves)
                    avg_d_phi = sum(m[1] for m in org_moves) / len(org_moves)
                    print(f"      🧭 Avg movement: θ={avg_d_theta:+.4f}, φ={avg_d_phi:+.4f}")
            
            print()
            
            # Include full debug log in results for post-analysis
            results['debug_log'] = self.debug_log
            print()
        
        return results
    
    def _save_trained_weights(self):
        """Save the trained brain weights back to .pt files."""
        import torch
        import os
        
        # Find the cocoon directory
        cocoon_dir = None
        if hasattr(self.agent, 'cocoon_dir'):
            cocoon_dir = self.agent.cocoon_dir
        else:
            # Try to find brain_ensemble.pt in current directory or parent
            for check_path in ['.', '..', os.path.dirname(os.path.abspath(__file__))]:
                pt_path = os.path.join(check_path, 'brain_ensemble.pt')
                if os.path.exists(pt_path):
                    cocoon_dir = check_path
                    break
        
        if cocoon_dir is None:
            print("   ⚠️ Could not find cocoon directory to save weights")
            return
        
        try:
            # Save individual brain weights
            for i, brain in enumerate(self.agent.brains):
                pt_path = os.path.join(cocoon_dir, f'brain_{i}_trained.pt')
                torch.save(brain.state_dict(), pt_path)
            
            # Also save as ensemble
            ensemble_path = os.path.join(cocoon_dir, 'brain_ensemble_trained.pt')
            torch.save({
                f'brain_{i}': brain.state_dict() 
                for i, brain in enumerate(self.agent.brains)
            }, ensemble_path)
            
            print(f"   ✅ Saved trained weights to {cocoon_dir}")
            print(f"      - Individual: brain_{{0..{len(self.agent.brains)-1}}}_trained.pt")
            print(f"      - Ensemble: brain_ensemble_trained.pt")
            
        except Exception as e:
            print(f"   ❌ Failed to save weights: {e}")


# =============================================================================
# TOURNAMENT RUNNER
# =============================================================================

def run_swarm_defense(
    agent,
    organism_indices: Optional[List[int]] = None,
    max_misses: int = 10,
    headless: bool = False,
    seed: Optional[int] = None,
    num_balls: int = 1,
    enable_training: bool = False,
    train_interval: int = 100,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a Swarm Defense challenge - the PRIMARY game mode.
    
    All organisms work together to defend the ENTIRE sphere.
    ANY organism can catch the ball. Success is collective.
    The swarm fails when they accumulate too many misses.
    
    COMMAND CHAIN SYSTEM (enabled by default):
    - The organism that intercepts becomes COMMANDER
    - Commander predicts next impact and broadcasts directive
    - Swarm follows the command - organisms track their compliance
    - Best follower who intercepts becomes new commander
    - Creates EMERGENT LEADERSHIP based on performance
    
    MULTI-BALL MODE:
    - Use num_balls > 1 for extra chaos!
    - Swarm must coordinate to track multiple threats
    
    POST-SNAPSHOT TRAINING (when enable_training=True):
    - Organisms learn from catches (+1.0 reward)
    - Near-catch positioning rewarded (+0.2)
    - Misses penalized (-0.5 to -1.0)
    - Weights updated every train_interval frames
    - At session end, prompted to save updated weights
    
    VERBOSE MODE (when verbose=True):
    - Logs all organism actions with brain output details
    - Logs all experience collection (state, action, reward)
    - Logs all training steps with loss breakdown
    
    This tests:
    - Swarm coordination and cooperation
    - Emergent role distribution
    - Collective intelligence
    - Coverage optimization
    - Hierarchical command following (NEW!)
    - Performance-based leadership succession (NEW!)
    
    Args:
        agent: CocoonAgent with organism brains
        organism_indices: Which organisms to include (default: all up to 8)
        max_misses: How many collective misses before failure
        headless: Run without display
        seed: Random seed for reproducibility
        num_balls: Number of balls in play (1-5, default 1)
        enable_training: Enable post-snapshot training (weights updated during gameplay)
        train_interval: How many frames between training steps (default: 100)
        verbose: Enable granular debug logging of actions, experiences, and training
    
    Returns:
        Results with catches, misses, streak, command chain stats, and leadership metrics
    """
    arena = SphereArena(
        agent=agent,
        organism_indices=organism_indices,
        max_misses=max_misses,
        headless=headless,
        seed=seed,
        mode=GameMode.SWARM_DEFENSE,
        enable_command_chain=True,  # Always enable for swarm defense
        num_balls=num_balls,
        enable_training=enable_training,
        train_interval=train_interval,
        verbose=verbose
    )
    
    return arena.run()


def run_elimination_mode(
    agent,
    organism_indices: Optional[List[int]] = None,
    max_misses: int = 3,
    headless: bool = False,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run elimination mode - individual testing (NOT the main mode).
    
    This is for comparing individual organism performance.
    Each organism has their own zone; misses in your zone = penalty.
    
    Args:
        agent: CocoonAgent with organism brains
        organism_indices: Which organisms to include
        max_misses: Per-organism miss limit
        headless: Run without display
        seed: Random seed
    
    Returns:
        Results with individual stats and winner
    """
    arena = SphereArena(
        agent=agent,
        organism_indices=organism_indices,
        max_misses=max_misses,
        headless=headless,
        seed=seed,
        mode=GameMode.ELIMINATION
    )
    
    return arena.run()


# =============================================================================
# DEMO MODE - Preview arena without a cocoon
# =============================================================================

class DummyBrain:
    """Simple AI brain for demo mode - just chases the ball."""
    def __init__(self, idx):
        self.idx = idx
        self.input_dim = OBSERVATION_SIZE
        self.output_dim = 4
    
    def forward(self, x, **kwargs):
        """Return random-ish movement."""
        import torch
        return torch.randn(1, 4) * 0.5
    
    def eval(self):
        pass
    
    def __call__(self, x, **kwargs):
        return self.forward(x, **kwargs)


class DummyAgent:
    """Fake CocoonAgent for demo mode."""
    def __init__(self, num_organisms: int = 6):
        self.brains = [DummyBrain(i) for i in range(num_organisms)]
        self.vp_runtime = None
        self.organism_fitness = [1.0] * num_organisms
        self.organism_names = [f"Demo_{i}" for i in range(num_organisms)]
        self.device = 'cpu'


def run_demo(num_organisms: int = 6, max_misses: int = 10):
    """
    Run a DEMO of the sphere arena with dummy AI.
    
    This lets you preview the visuals without needing an exported cocoon.
    The dummy organisms use simple ball-chasing AI.
    
    Args:
        num_organisms: How many dummy organisms (default 6)
        max_misses: Misses before game over
    """
    if not PYGAME_AVAILABLE:
        print("❌ pygame required for demo mode")
        print("   Install with: pip install pygame PyOpenGL")
        return None
    
    print("🎮 DEMO MODE - Preview with dummy AI")
    print("   (Not using trained organisms)")
    print()
    
    dummy_agent = DummyAgent(num_organisms)
    
    arena = SphereArena(
        agent=dummy_agent,
        organism_indices=list(range(num_organisms)),
        max_misses=max_misses,
        headless=False,
        mode=GameMode.SWARM_DEFENSE,
        enable_command_chain=True
    )
    
    return arena.run()


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Demo the Sphere Arena - 3D Swarm Defense Training."""
    import sys
    import os
    
    # Check for --demo flag
    demo_mode = '--demo' in sys.argv
    
    # Check for --train flag (enable post-snapshot training)
    enable_training = '--train' in sys.argv
    
    # Check for --verbose flag (granular debug logging)
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    # Check for --cocoon flag (path to cocoon directory)
    cocoon_path = None
    for i, arg in enumerate(sys.argv):
        if arg == '--cocoon' and i + 1 < len(sys.argv):
            cocoon_path = sys.argv[i + 1]
            # Resolve to absolute path
            cocoon_path = os.path.abspath(cocoon_path)
    
    # Check for --balls flag (e.g., --balls 3)
    num_balls = 1
    for i, arg in enumerate(sys.argv):
        if arg == '--balls' and i + 1 < len(sys.argv):
            try:
                num_balls = int(sys.argv[i + 1])
                num_balls = max(1, min(5, num_balls))  # Clamp 1-5
            except ValueError:
                pass
    
    # Check for --misses flag (e.g., --misses 100)
    max_misses = 10
    for i, arg in enumerate(sys.argv):
        if arg == '--misses' and i + 1 < len(sys.argv):
            try:
                max_misses = int(sys.argv[i + 1])
                max_misses = max(1, max_misses)  # At least 1
            except ValueError:
                pass
    
    # Check for --organisms flag (e.g., --organisms 50)
    num_organisms_override = None
    for i, arg in enumerate(sys.argv):
        if arg == '--organisms' and i + 1 < len(sys.argv):
            try:
                num_organisms_override = int(sys.argv[i + 1])
                num_organisms_override = max(1, num_organisms_override)  # At least 1
            except ValueError:
                pass
    
    # Check for --help flag
    if '--help' in sys.argv or '-h' in sys.argv:
        print("🌐 Sphere Arena - 3D Swarm Defense")
        print()
        print("Usage: python sphere_arena.py [options]")
        print()
        print("Options:")
        print("  --cocoon PATH    Path to cocoon directory (contains cocoon.py)")
        print("                   Example: --cocoon agent_downloads/small_export")
        print("  --demo           Run demo mode with dummy AI")
        print("  --organisms N    Number of organisms to use (default: all available)")
        print("  --balls N        Number of balls (1-5, default: 1)")
        print("  --misses N       Max collective misses before game over (default: 10)")
        print("  --train          Enable post-snapshot training")
        print("                   Organisms learn from catches (+reward) and misses (-penalty)")
        print("                   Weights updated every 100 frames")
        print("                   Prompted to save trained weights at end")
        print("  --verbose, -v    Enable granular debug logging")
        print("                   Shows all organism actions, experience collection, and training")
        print("  --help, -h       Show this help message")
        print()
        print("Examples:")
        print("  # Run with specific cocoon:")
        print("  python sphere_arena.py --cocoon agent_downloads/small_export --train")
        print()
        print("  # Run with 2 balls and verbose logging:")
        print("  python sphere_arena.py --cocoon ./my_cocoon --balls 2 --verbose")
        print()
        print("  # Demo mode (no cocoon needed):")
        print("  python sphere_arena.py --demo")
        print()
        print("Training mode:")
        print("  When --train is enabled, organisms gain knowledge during gameplay:")
        print("    • Catches: +1.0 reward (reinforces successful intercepts)")
        print("    • Near misses: +0.2 reward (good positioning)")
        print("    • Misses: -0.5 penalty (bad positioning)")
        print("    • Game over: -1.0 terminal penalty")
        print()
        print("  After the game, you'll be prompted to save trained weights as:")
        print("    • brain_X_trained.pt (individual)")
        print("    • brain_ensemble_trained.pt (combined)")
        return
    
    print("🌐 Sphere Arena - 3D Swarm Defense Training")
    print("=" * 60)
    print()
    print("A 3D arena where the ENTIRE SWARM defends the sphere together.")
    print("Ball bounces inside the sphere in full 3D.")
    print("ANY organism can catch - the swarm succeeds or fails as ONE.")
    print()
    print("COMMAND CHAIN SYSTEM:")
    print("  • Interceptor becomes COMMANDER")
    print("  • Commander broadcasts predicted impact to swarm")
    print("  • Best follower who catches = new commander")
    print("  • Emergent leadership based on performance!")
    print()
    if num_balls > 1:
        print(f"⚠️  MULTI-BALL MODE: {num_balls} balls in play!")
        print()
    
    if demo_mode:
        # Run demo with dummy AI
        print("━" * 60)
        print("🎮 DEMO MODE ACTIVATED")
        print("━" * 60)
        print()
        
        results = run_demo(num_organisms=6, max_misses=10)
        
        if results:
            print("\n" + "=" * 60)
            print("📊 DEMO RESULTS")
            print("=" * 60)
            print(f"   Total Catches: {results.get('collective_catches', 0)}")
            print(f"   Total Misses:  {results.get('collective_misses', 0)}")
            print(f"   Best Streak:   {results.get('best_streak', 0)}")
        return
    
    # Normal mode - try to load cocoon
    print("Usage with exported cocoon:")
    print()
    print("  python sphere_arena.py --cocoon agent_downloads/small_export --train")
    print()
    print("Or run with --demo flag to preview visuals:")
    print("  python sphere_arena.py --demo")
    print()
    print("Controls:")
    print("  ESC - Quit")
    print("  Camera auto-rotates around the sphere")
    print()
    
    # Try to run with cocoon
    try:
        # If --cocoon path specified, add it to sys.path
        if cocoon_path:
            if os.path.isdir(cocoon_path):
                sys.path.insert(0, cocoon_path)
                print(f"Loading cocoon from: {cocoon_path}")
            else:
                print(f"❌ Cocoon path not found: {cocoon_path}")
                return
        else:
            sys.path.insert(0, '.')
        
        from cocoon import CocoonAgent
        
        print("Found cocoon.py - starting Swarm Defense!")
        agent = CocoonAgent()
        
        # Store cocoon directory on agent for save functionality
        if cocoon_path:
            agent.cocoon_dir = cocoon_path
        
        # Use all available organisms, or override with --organisms flag
        if num_organisms_override is not None:
            num_players = min(num_organisms_override, len(agent.brains))
        else:
            num_players = len(agent.brains)  # Use ALL available
        
        if not PYGAME_AVAILABLE:
            print("pygame not installed; running headless")
        
        print(f"\n--- SWARM DEFENSE MODE WITH COMMAND CHAIN ---")
        print(f"    Organisms: {num_players}")
        print(f"    Balls: {num_balls}")
        print(f"    Max misses: {max_misses} (collective)")
        print(f"    Command chain: ENABLED")
        if enable_training:
            print(f"    📈 Training: ENABLED (post-snapshot learning)")
        if verbose:
            print(f"    🔍 Verbose: ENABLED (debug logging active)")
        print()
        
        results = run_swarm_defense(
            agent,
            organism_indices=list(range(num_players)),
            max_misses=max_misses,
            headless=not PYGAME_AVAILABLE,
            num_balls=num_balls,
            enable_training=enable_training,
            verbose=verbose
        )
        
        print("\n" + "=" * 60)
        print("📊 SWARM DEFENSE RESULTS")
        print("=" * 60)
        print(f"   Total Catches: {results.get('collective_catches', 0)}")
        print(f"   Total Misses:  {results.get('collective_misses', 0)}")
        print(f"   Best Streak:   {results.get('best_streak', 0)}")
        print(f"   Total Frames:  {results.get('total_frames', 0)}")
        print()
        
        if results.get('command_chain_enabled'):
            print("🎖️  COMMAND CHAIN STATISTICS:")
            print(f"   Total Commands Issued: {results.get('total_commands', 0)}")
            print(f"   Best Commander: Organism #{results.get('best_commander', '?')}")
            print(f"   Best Follower:  Organism #{results.get('best_follower', '?')}")
            print()
        
        if 'final_stats' in results:
            print("   Individual Contributions:")
            for idx, stats in sorted(results['final_stats'].items(), 
                                    key=lambda x: x[1].get('catches', 0), 
                                    reverse=True):
                catches = stats.get('catches', 0)
                cmds_issued = stats.get('commands_issued', 0)
                
                role_badge = ""
                if idx == results.get('best_commander'):
                    role_badge = " 👑 BEST COMMANDER"
                elif idx == results.get('best_follower'):
                    role_badge = " 🎯 BEST FOLLOWER"
                
                print(f"      Organism #{idx}: {catches} catches, {cmds_issued} commands issued{role_badge}")
        
    except ImportError as e:
        print(f"Note: Could not load cocoon.py ({e})")
        print("Run with --demo to preview visuals, or export a cocoon first.")


if __name__ == "__main__":
    main()
