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
        enable_command_chain: bool = True  # Enable hierarchical command system
    ):
        self.agent = agent
        self.max_misses = max_misses  # Collective miss limit
        self.headless = headless
        self.mode = mode
        self.enable_command_chain = enable_command_chain
        
        # Swarm stats
        self.collective_catches = 0
        self.collective_misses = 0
        self.catch_streak = 0
        self.best_streak = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # COMMAND CHAIN SYSTEM - Hierarchical swarm coordination
        # ═══════════════════════════════════════════════════════════════════
        self.current_commander: Optional[int] = None  # Who is issuing orders
        self.current_command: Optional[Tuple[float, float]] = None  # (theta, phi) target
        self.command_history: List[Dict] = []  # Log of all commands issued
        self.predicted_impact: Optional[Tuple[float, float]] = None  # Where ball will hit
        self.command_broadcast_frame: int = 0  # When command was issued
        
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
        
        # Create ball at center with random direction
        direction = self._random_direction()
        self.ball = Ball3D(
            x=0, y=0, z=0,
            vx=direction[0] * BALL_SPEED,
            vy=direction[1] * BALL_SPEED,
            vz=direction[2] * BALL_SPEED
        )
        
        # Game state
        self.game_over = False
        self.winner = None
        self.frame_count = 0
        self.catch_log: List[Tuple[int, int, int]] = []  # (frame, catcher_idx, streak)
        self.miss_log: List[Tuple[int, Tuple[float, float]]] = []  # (frame, ball_position_theta_phi)
        
        # Camera rotation
        self.camera_angle = 0
    
    def _random_direction(self) -> Tuple[float, float, float]:
        """Generate random unit vector."""
        theta = self.rng.uniform(0, 2*math.pi)
        phi = self.rng.uniform(0.3, math.pi - 0.3)  # Avoid poles
        return (
            math.sin(phi) * math.cos(theta),
            math.cos(phi),
            math.sin(phi) * math.sin(theta)
        )
    
    def _get_observation(self, organism_idx: int) -> np.ndarray:
        """Get observation for organism's neural network."""
        org = self.organisms.get(organism_idx)
        if org is None or not org.alive:
            return np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        
        ball_pos = self.ball.get_position()
        ball_vel = self.ball.get_velocity()
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
        """
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
            vp_value = None
            if hasattr(self.agent, 'vp_runtime'):
                try:
                    vp_data = self.agent.vp_runtime.compute_from_state(obs, [])
                    vp_value = vp_data.get('violation_pressure', 0.5)
                except:
                    vp_value = 0.5
            
            device = getattr(self.agent, 'device', 'cpu')
            state_tensor = torch.FloatTensor(obs).unsqueeze(0).to(device)
            
            brain.eval()
            with torch.no_grad():
                output = brain(state_tensor, vp_value=vp_value, return_language_logits=False)
                
                if isinstance(output, tuple):
                    output = output[0]
                if isinstance(output, dict):
                    action_logits = output.get('action_probs') or output.get('actions') or output.get('logits')
                else:
                    action_logits = output
                
                if action_logits is None:
                    raise RuntimeError("No action logits")
                
                action_vec = action_logits.detach().cpu().numpy().flatten()
                
                # Interpret as movement: first 2 values -> theta, phi
                if len(action_vec) >= 2:
                    d_theta = np.tanh(action_vec[0]) * ORGANISM_MOVE_SPEED
                    d_phi = np.tanh(action_vec[1]) * ORGANISM_MOVE_SPEED
                    return (d_theta, d_phi)
                elif len(action_vec) >= 1:
                    return (np.tanh(action_vec[0]) * ORGANISM_MOVE_SPEED, 0)
        
        except Exception as e:
            pass
        
        # Fallback: simple AI - move toward ball's projected sphere position
        org = self.organisms.get(organism_idx)
        if org:
            ball_pos = self.ball.get_position()
            _, ball_theta, ball_phi = cartesian_to_spherical(*ball_pos)
            
            # Move toward ball's projection
            d_theta = 0
            d_phi = 0
            
            theta_diff = ball_theta - org.theta
            # Normalize to [-π, π]
            while theta_diff > math.pi: theta_diff -= 2*math.pi
            while theta_diff < -math.pi: theta_diff += 2*math.pi
            
            if abs(theta_diff) > 0.05:
                d_theta = ORGANISM_MOVE_SPEED * (1 if theta_diff > 0 else -1)
            
            phi_diff = ball_phi - org.phi
            if abs(phi_diff) > 0.05:
                d_phi = ORGANISM_MOVE_SPEED * (1 if phi_diff > 0 else -1)
            
            return (d_theta, d_phi)
        
        return (0, 0)
    
    def _check_ball_collision(self):
        """
        Check ball collision with sphere surface.
        In SWARM_DEFENSE mode: ANY organism can catch - it's collective defense.
        """
        ball_pos = self.ball.get_position()
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
                # SWARM CATCH! Any organism intercepted
                self._handle_swarm_catch(ball_pos, dist_from_center, catcher)
            else:
                # SWARM MISS - collective failure
                self._handle_swarm_miss(ball_theta, ball_phi)
    
    def _handle_swarm_catch(self, ball_pos, dist_from_center, catcher_idx):
        """
        Handle a successful swarm interception.
        
        COMMAND CHAIN SYSTEM:
        1. Evaluate how well the catcher followed the previous command
        2. The catcher becomes the NEW COMMANDER
        3. Commander predicts next impact point
        4. Commander broadcasts command to entire swarm
        5. All organisms receive the directive
        """
        # Reflect ball
        normal = normalize_vector(ball_pos)
        vel = self.ball.get_velocity()
        new_vel = reflect_vector(vel, normal)
        
        self.ball.vx = new_vel[0]
        self.ball.vy = new_vel[1]
        self.ball.vz = new_vel[2]
        
        # Speed up slightly (increases difficulty)
        self.ball.speed_up(1.02)
        
        # Move ball inside sphere
        scale = (SPHERE_RADIUS - BALL_RADIUS - 0.01) / dist_from_center
        self.ball.x *= scale
        self.ball.y *= scale
        self.ball.z *= scale
        
        # Update basic stats
        self.collective_catches += 1
        self.catch_streak += 1
        self.best_streak = max(self.best_streak, self.catch_streak)
        self.organisms[catcher_idx].catches += 1
        self.ball.last_hit_by = catcher_idx
        
        # ═══════════════════════════════════════════════════════════════════
        # COMMAND CHAIN LOGIC
        # ═══════════════════════════════════════════════════════════════════
        if self.enable_command_chain:
            self._process_command_chain(catcher_idx)
        
        # Log the catch
        self.catch_log.append((self.frame_count, catcher_idx, self.catch_streak))
        
        cmd_info = ""
        if self.enable_command_chain and self.current_commander == catcher_idx:
            cmd_info = " [NOW COMMANDING]"
        
        print(f"   🎯 SWARM CATCH by #{catcher_idx}!{cmd_info} (streak: {self.catch_streak})")
    
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

    def _handle_swarm_miss(self, ball_theta, ball_phi):
        """Handle a collective miss - the swarm failed to intercept."""
        self.collective_misses += 1
        self.catch_streak = 0  # Reset streak
        
        # Log the miss location
        self.miss_log.append((self.frame_count, (ball_theta, ball_phi)))
        
        print(f"   ❌ SWARM MISS! ({self.collective_misses}/{self.max_misses}) - Gap at θ={ball_theta:.2f}, φ={ball_phi:.2f}")
        
        # Check if game over
        if self.collective_misses >= self.max_misses:
            self.game_over = True
            self.winner = None  # No winner - swarm failed
            print(f"   💀 SWARM DEFENSE FAILED! Best streak: {self.best_streak}, Total catches: {self.collective_catches}")
        else:
            self._reset_ball()
    
    def _reset_ball(self):
        """Reset ball to center with random direction."""
        self.ball.x = 0
        self.ball.y = 0
        self.ball.z = 0
        direction = self._random_direction()
        self.ball.vx = direction[0] * BALL_SPEED
        self.ball.vy = direction[1] * BALL_SPEED
        self.ball.vz = direction[2] * BALL_SPEED
    
    def step(self) -> bool:
        """Advance one frame."""
        if self.game_over:
            return False
        
        self.frame_count += 1
        
        # Get actions and move organisms
        for org_idx in self.alive_organisms:
            obs = self._get_observation(org_idx)
            d_theta, d_phi = self._get_organism_action(org_idx, obs)
            self.organisms[org_idx].move(d_theta, d_phi)
        
        # Move ball
        self.ball.move()
        
        # Check collisions
        self._check_ball_collision()
        
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
        
        # Draw ball
        ball_pos = self.ball.get_position()
        glPushMatrix()
        glTranslatef(*ball_pos)
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        quad = gluNewQuadric()
        gluSphere(quad, BALL_RADIUS, 12, 8)
        glPopMatrix()
        
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
        
        return results


# =============================================================================
# TOURNAMENT RUNNER
# =============================================================================

def run_swarm_defense(
    agent,
    organism_indices: Optional[List[int]] = None,
    max_misses: int = 10,
    headless: bool = False,
    seed: Optional[int] = None
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
        enable_command_chain: Enable hierarchical command system (default True)
    
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
        enable_command_chain=True  # Always enable for swarm defense
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
# MAIN
# =============================================================================

def main():
    """Demo the Sphere Arena - 3D Swarm Defense Training."""
    print("🌐 Sphere Arena - 3D Swarm Defense Training")
    print("=" * 60)
    print()
    print("A 3D arena where the ENTIRE SWARM defends the sphere together.")
    print("Ball bounces inside the sphere in full 3D.")
    print("ANY organism can catch - the swarm succeeds or fails as ONE.")
    print()
    print("SWARM DEFENSE MODE (PRIMARY):")
    print("  • All organisms share ONE zone: the ENTIRE sphere surface")
    print("  • Any organism can intercept the ball")
    print("  • Success = collective, Failure = collective")
    print("  • Tests: coordination, self-organization, cooperation")
    print()
    print("This evaluates SWARM INTELLIGENCE - not individual performance.")
    print("Future applications: missile defense, distributed threat response.")
    print()
    print("Usage with exported cocoon:")
    print()
    print("  from cocoon import CocoonAgent")
    print("  from sphere_arena import run_swarm_defense, GameMode")
    print()
    print("  agent = CocoonAgent()")
    print()
    print("  # Run swarm defense challenge (default)")
    print("  results = run_swarm_defense(agent, max_misses=10)")
    print()
    print("  # Results include:")
    print("  # - collective_catches: total swarm catches")
    print("  # - collective_misses: swarm failures")
    print("  # - best_streak: longest rally without a miss")
    print("  # - best_commander: who led the swarm best")
    print("  # - command_history: full command chain log")
    print()
    print("Controls:")
    print("  ESC - Quit")
    print("  Camera auto-rotates around the sphere")
    print()
    
    # Try to run demo
    try:
        import sys
        sys.path.insert(0, '.')
        from cocoon import CocoonAgent
        
        print("Found cocoon.py - starting Swarm Defense demo!")
        agent = CocoonAgent()
        
        num_players = min(8, len(agent.brains))  # Up to 8 for good coverage
        
        if not PYGAME_AVAILABLE:
            print("pygame not installed; running headless")
        
        print(f"\n--- SWARM DEFENSE MODE WITH COMMAND CHAIN ---")
        print(f"    Organisms: {num_players}")
        print(f"    Max misses: 10 (collective)")
        print(f"    Command chain: ENABLED")
        print()
        
        results = run_swarm_defense(
            agent,
            organism_indices=list(range(num_players)),
            max_misses=10,
            headless=not PYGAME_AVAILABLE
        )
        
        print("\n" + "=" * 60)
        print("📊 SWARM DEFENSE RESULTS")
        print("=" * 60)
        print(f"   Total Catches: {results.get('collective_catches', 0)}")
        print(f"   Total Misses:  {results.get('collective_misses', 0)}")
        print(f"   Best Streak:   {results.get('best_streak', 0)}")
        print(f"   Total Frames:  {results.get('total_frames', 0)}")
        print()
        
        # ═══════════════════════════════════════════════════════════════════
        # COMMAND CHAIN RESULTS
        # ═══════════════════════════════════════════════════════════════════
        if results.get('command_chain_enabled'):
            print("🎖️  COMMAND CHAIN STATISTICS:")
            print(f"   Total Commands Issued: {results.get('total_commands', 0)}")
            print(f"   Best Commander: Organism #{results.get('best_commander', '?')}")
            print(f"   Best Follower:  Organism #{results.get('best_follower', '?')}")
            print()
        
        # Show per-organism stats
        if 'final_stats' in results:
            print("   Individual Contributions:")
            for idx, stats in sorted(results['final_stats'].items(), 
                                    key=lambda x: x[1].get('catches', 0), 
                                    reverse=True):
                catches = stats.get('catches', 0)
                cmds_issued = stats.get('commands_issued', 0)
                cmds_followed = stats.get('commands_followed', 0)
                leadership = stats.get('leadership_score', 0)
                
                role_badge = ""
                if idx == results.get('best_commander'):
                    role_badge = " 👑 BEST COMMANDER"
                elif idx == results.get('best_follower'):
                    role_badge = " 🎯 BEST FOLLOWER"
                
                print(f"      Organism #{idx}: {catches} catches, {cmds_issued} commands issued{role_badge}")
        
    except ImportError as e:
        print(f"Note: Could not load cocoon.py ({e})")
        print("Export a cocoon first, then run from that directory.")


if __name__ == "__main__":
    main()
