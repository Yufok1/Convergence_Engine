#!/usr/bin/env python3
"""
🎮 SWARM PONG ARENA - Multi-Agent Elimination Battle

A custom Pygame arena where each organism defends an edge of a polygon.
As organisms are eliminated, the arena shrinks its geometry until one remains.

    8 agents = Octagon
    7 agents = Heptagon  
    6 agents = Hexagon
    5 agents = Pentagon
    4 agents = Square
    3 agents = Triangle
    2 agents = Final Duel (classic Pong)
    1 agent  = CHAMPION!

Inspired by:
- Piers Anthony's "Apprentice Adept" game selection
- "Highlander" elimination ("There can be only one")
- Classic Pong mechanics

Author: The Butterfly System / Convergence Engine
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None  # Allows headless use when pygame is absent
    PYGAME_AVAILABLE = False

import numpy as np
import math
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

# =============================================================================
# CONSTANTS
# =============================================================================

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BALL_COLOR = (255, 255, 0)  # Yellow ball

# Organism colors (rainbow for visibility)
ORGANISM_COLORS = [
    (255, 100, 100),   # Red
    (100, 255, 100),   # Green
    (100, 100, 255),   # Blue
    (255, 255, 100),   # Yellow
    (255, 100, 255),   # Magenta
    (100, 255, 255),   # Cyan
    (255, 180, 100),   # Orange
    (180, 100, 255),   # Purple
    (100, 255, 180),   # Teal
    (255, 100, 180),   # Pink
    (180, 255, 100),   # Lime
    (100, 180, 255),   # Sky Blue
]

# Game settings
WINDOW_SIZE = 800
CENTER = (WINDOW_SIZE // 2, WINDOW_SIZE // 2)
ARENA_RADIUS = 300
PADDLE_LENGTH = 60
PADDLE_THICKNESS = 10
BALL_RADIUS = 10
BALL_SPEED = 5
PADDLE_SPEED = 8
OBSERVATION_SIZE = 24  # Matches cocoon brain default input size

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Paddle:
    """A paddle on an edge of the polygon."""
    organism_idx: int
    edge_idx: int
    position: float  # 0.0 to 1.0 along the edge
    color: Tuple[int, int, int]
    alive: bool = True
    score: int = 0
    hits: int = 0
    
    def move(self, direction: int, edge_length: float):
        """Move paddle along edge. direction: -1, 0, or 1"""
        speed = PADDLE_SPEED / edge_length  # Normalize to edge length
        self.position = max(0.1, min(0.9, self.position + direction * speed))


@dataclass
class Ball:
    """The ball bouncing around the arena."""
    x: float
    y: float
    vx: float
    vy: float
    last_hit_by: Optional[int] = None  # organism_idx who last hit it
    
    def move(self):
        self.x += self.vx
        self.y += self.vy
    
    def speed_up(self, factor: float = 1.05):
        """Gradually increase speed for excitement."""
        self.vx *= factor
        self.vy *= factor
        # Cap maximum speed
        max_speed = 15
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > max_speed:
            self.vx = self.vx / speed * max_speed
            self.vy = self.vy / speed * max_speed


@dataclass
class ArenaState:
    """Current state of the arena for AI observation."""
    ball_x: float
    ball_y: float
    ball_vx: float
    ball_vy: float
    paddle_position: float
    edge_start: Tuple[float, float]
    edge_end: Tuple[float, float]
    num_alive: int
    my_score: int
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for neural network input."""
        return np.array([
            self.ball_x / WINDOW_SIZE,
            self.ball_y / WINDOW_SIZE,
            self.ball_vx / 10,
            self.ball_vy / 10,
            self.paddle_position,
            self.edge_start[0] / WINDOW_SIZE,
            self.edge_start[1] / WINDOW_SIZE,
            self.edge_end[0] / WINDOW_SIZE,
            self.edge_end[1] / WINDOW_SIZE,
            self.num_alive / 10,
            self.my_score / 10,
        ], dtype=np.float32)


# =============================================================================
# POLYGON GEOMETRY
# =============================================================================

def get_polygon_vertices(num_sides: int, radius: float, center: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Calculate vertices of a regular polygon."""
    vertices = []
    for i in range(num_sides):
        angle = 2 * math.pi * i / num_sides - math.pi / 2  # Start from top
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        vertices.append((x, y))
    return vertices


def get_edge_midpoint(v1: Tuple[float, float], v2: Tuple[float, float], t: float) -> Tuple[float, float]:
    """Get point along edge at position t (0.0 to 1.0)."""
    return (
        v1[0] + t * (v2[0] - v1[0]),
        v1[1] + t * (v2[1] - v1[1])
    )


def get_edge_normal(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
    """Get outward-facing normal vector for an edge."""
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    length = math.sqrt(dx**2 + dy**2)
    # Normal points inward (toward center)
    return (-dy / length, dx / length)


def point_to_line_distance(point: Tuple[float, float], 
                            line_start: Tuple[float, float], 
                            line_end: Tuple[float, float]) -> Tuple[float, float]:
    """Calculate distance from point to line segment and closest point parameter t."""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2), 0.5
    
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx**2 + dy**2)))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    distance = math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    return distance, t


def reflect_velocity(vx: float, vy: float, nx: float, ny: float) -> Tuple[float, float]:
    """Reflect velocity vector off a surface with normal (nx, ny)."""
    dot = vx * nx + vy * ny
    return (vx - 2 * dot * nx, vy - 2 * dot * ny)


# =============================================================================
# SWARM PONG ARENA
# =============================================================================

class SwarmPongArena:
    """
    🎮 Multi-agent Pong arena with polygon geometry.
    
    Each organism defends one edge of the polygon.
    When scored against, that organism is eliminated.
    Arena shrinks as organisms are eliminated.
    """
    
    def __init__(self, 
                 agent,  # CocoonAgent
                 organism_indices: Optional[List[int]] = None,
                 lives_per_organism: int = 3,
                 window_size: int = WINDOW_SIZE,
                 headless: bool = False,
                 seed: Optional[int] = None):
        """
        Initialize the arena.
        
        Args:
            agent: CocoonAgent with brains for each organism
            organism_indices: Which organisms to include (default: all)
            lives_per_organism: How many goals before elimination
            window_size: Pygame window size
            headless: Run without display (for training)
        """
        self.agent = agent
        self.window_size = window_size
        self.headless = headless
        self.lives_per_organism = lives_per_organism

        # Deterministic runs when seed is provided
        self.seed = seed
        self.rng = random.Random(seed)
        if seed is not None:
            np.random.seed(seed)
        
        # Select organisms
        if organism_indices is None:
            organism_indices = list(range(min(len(agent.brains), 12)))  # Max 12
        self.organism_indices = organism_indices
        
        # Initialize game state
        self.reset()
        
        # Pygame setup
        if not headless:
            if not PYGAME_AVAILABLE:
                raise RuntimeError("pygame is required for rendering; install it or set headless=True")
            pygame.init()
            pygame.display.set_caption("🎮 Swarm Pong Arena - Elimination Battle")
            self.screen = pygame.display.set_mode((window_size, window_size))
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        else:
            self.screen = None
            self.clock = None
    
    def reset(self):
        """Reset the arena for a new game."""
        self.alive_organisms = list(self.organism_indices)
        self.num_sides = len(self.alive_organisms)
        
        # Create paddles for each organism
        self.paddles: Dict[int, Paddle] = {}
        for i, org_idx in enumerate(self.alive_organisms):
            color = ORGANISM_COLORS[org_idx % len(ORGANISM_COLORS)]
            self.paddles[org_idx] = Paddle(
                organism_idx=org_idx,
                edge_idx=i,
                position=0.5,  # Start in middle of edge
                color=color,
                alive=True
            )
        
        # Calculate arena geometry
        self._update_geometry()
        
        # Create ball in center with random direction
        angle = self.rng.uniform(0, 2 * math.pi)
        self.ball = Ball(
            x=CENTER[0],
            y=CENTER[1],
            vx=BALL_SPEED * math.cos(angle),
            vy=BALL_SPEED * math.sin(angle)
        )
        
        # Game state
        self.game_over = False
        self.winner = None
        self.frame_count = 0
        self.eliminations: List[Tuple[int, int]] = []  # (frame, organism_idx)
    
    def _update_geometry(self):
        """Recalculate polygon vertices based on alive organisms."""
        self.num_sides = len(self.alive_organisms)
        if self.num_sides < 2:
            return
        
        # Calculate radius based on number of sides (shrink as we go)
        base_radius = ARENA_RADIUS
        shrink_factor = min(1.0, self.num_sides / 6)  # Shrink below hexagon
        self.current_radius = base_radius * (0.5 + 0.5 * shrink_factor)
        
        self.vertices = get_polygon_vertices(self.num_sides, self.current_radius, CENTER)
        
        # Update paddle edge indices
        for i, org_idx in enumerate(self.alive_organisms):
            if org_idx in self.paddles:
                self.paddles[org_idx].edge_idx = i
    
    def _get_edge(self, edge_idx: int) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the start and end vertices of an edge."""
        v1 = self.vertices[edge_idx]
        v2 = self.vertices[(edge_idx + 1) % self.num_sides]
        return v1, v2
    
    def _get_paddle_rect(self, paddle: Paddle) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the paddle's position on its edge."""
        v1, v2 = self._get_edge(paddle.edge_idx)
        
        # Calculate paddle center and extent
        edge_length = math.sqrt((v2[0] - v1[0])**2 + (v2[1] - v1[1])**2)
        paddle_extent = PADDLE_LENGTH / edge_length / 2  # Half-length as fraction
        
        t_start = max(0, paddle.position - paddle_extent)
        t_end = min(1, paddle.position + paddle_extent)
        
        p1 = get_edge_midpoint(v1, v2, t_start)
        p2 = get_edge_midpoint(v1, v2, t_end)
        
        return p1, p2
    
    def _get_observation(self, organism_idx: int) -> np.ndarray:
        """Get the game state observation for a specific organism."""
        paddle = self.paddles.get(organism_idx)
        if paddle is None or not paddle.alive:
            return np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        
        v1, v2 = self._get_edge(paddle.edge_idx)
        
        state = ArenaState(
            ball_x=self.ball.x,
            ball_y=self.ball.y,
            ball_vx=self.ball.vx,
            ball_vy=self.ball.vy,
            paddle_position=paddle.position,
            edge_start=v1,
            edge_end=v2,
            num_alive=len(self.alive_organisms),
            my_score=paddle.score
        )
        
        obs = state.to_array()
        
        # Pad to expected observation size for cocoon brains
        if len(obs) < OBSERVATION_SIZE:
            obs = np.pad(obs, (0, OBSERVATION_SIZE - len(obs)))
        
        return obs
    
    def _get_organism_action(self, organism_idx: int, state: np.ndarray) -> int:
        """Get action from organism's brain. Returns -1, 0, or 1."""
        try:
            import torch
            
            brain = self.agent.brains[organism_idx]
            # Normalize and pad observation to the brain's expected input size
            obs = np.asarray(state, dtype=np.float32).flatten()
            target_dim = getattr(brain, 'input_dim', getattr(brain, 'input_size', OBSERVATION_SIZE))
            if len(obs) < target_dim:
                obs = np.pad(obs, (0, target_dim - len(obs)))
            elif len(obs) > target_dim:
                obs = obs[:target_dim]

            # Optional violation pressure signal if the agent provides it
            vp_value = None
            if hasattr(self.agent, 'vp_runtime'):
                try:
                    reward_history = getattr(self.agent, 'reward_history', [])
                    vp_data = self.agent.vp_runtime.compute_from_state(obs, reward_history)
                    vp_value = vp_data.get('violation_pressure', 0.5)
                except Exception:
                    vp_value = 0.5

            # Move tensor to the agent's preferred device
            device = getattr(self.agent, 'device', 'cpu')
            state_tensor = torch.FloatTensor(obs).unsqueeze(0).to(device)

            brain.eval()
            with torch.no_grad():
                output = brain(state_tensor, vp_value=vp_value, return_language_logits=False)
                
                # Unwrap common output shapes
                if isinstance(output, tuple):
                    output = output[0]
                if isinstance(output, dict):
                    action_logits = output.get('action_probs') or output.get('actions') or output.get('logits')
                else:
                    action_logits = output
                if action_logits is None:
                    raise RuntimeError("No action logits returned from brain")

                action_vec = action_logits.detach().cpu().numpy().flatten()

                # If the brain exposes more than 3 actions, use the first 3 for paddle control
                if len(action_vec) >= 3:
                    return int(np.argmax(action_vec[:3]) - 1)

                if len(action_vec) == 0:
                    raise RuntimeError("Empty action vector from brain")

                # Fallback: treat first logit as a steering signal
                return int(np.sign(action_vec[0]))
        
        except Exception as e:
            pass
        
        # Fallback: simple AI - move toward ball
        paddle = self.paddles.get(organism_idx)
        if paddle:
            v1, v2 = self._get_edge(paddle.edge_idx)
            paddle_pos = get_edge_midpoint(v1, v2, paddle.position)
            
            # Project ball onto edge direction
            edge_vec = (v2[0] - v1[0], v2[1] - v1[1])
            ball_vec = (self.ball.x - v1[0], self.ball.y - v1[1])
            edge_len_sq = edge_vec[0]**2 + edge_vec[1]**2
            
            if edge_len_sq > 0:
                t = (edge_vec[0] * ball_vec[0] + edge_vec[1] * ball_vec[1]) / edge_len_sq
                t = max(0, min(1, t))
                
                if t < paddle.position - 0.05:
                    return -1
                elif t > paddle.position + 0.05:
                    return 1
        
        return 0
    
    def _check_ball_collision(self):
        """Check ball collision with paddles and walls."""
        # Check collision with each edge
        for i, org_idx in enumerate(self.alive_organisms):
            paddle = self.paddles[org_idx]
            if not paddle.alive:
                continue
            
            v1, v2 = self._get_edge(i)
            distance, t = point_to_line_distance((self.ball.x, self.ball.y), v1, v2)
            
            # Check if ball is near this edge
            if distance < BALL_RADIUS + PADDLE_THICKNESS:
                # Get paddle extent
                p1, p2 = self._get_paddle_rect(paddle)
                paddle_t_start = point_to_line_distance(p1, v1, v2)[1]
                paddle_t_end = point_to_line_distance(p2, v1, v2)[1]
                
                # Check if ball hit the paddle
                if paddle_t_start <= t <= paddle_t_end:
                    # Paddle hit! Reflect ball
                    normal = get_edge_normal(v1, v2)
                    self.ball.vx, self.ball.vy = reflect_velocity(
                        self.ball.vx, self.ball.vy, normal[0], normal[1]
                    )
                    
                    # Add some angle based on where it hit the paddle
                    hit_offset = (t - paddle.position) / 0.2  # -1 to 1
                    edge_vec = (v2[0] - v1[0], v2[1] - v1[1])
                    edge_len = math.sqrt(edge_vec[0]**2 + edge_vec[1]**2)
                    
                    self.ball.vx += hit_offset * edge_vec[0] / edge_len * 2
                    self.ball.vy += hit_offset * edge_vec[1] / edge_len * 2
                    
                    # Speed up slightly
                    self.ball.speed_up(1.02)
                    
                    # Record hit
                    paddle.hits += 1
                    paddle.score += 1
                    self.ball.last_hit_by = org_idx
                    
                    # Move ball outside edge
                    self.ball.x += normal[0] * (BALL_RADIUS + PADDLE_THICKNESS - distance + 1)
                    self.ball.y += normal[1] * (BALL_RADIUS + PADDLE_THICKNESS - distance + 1)
                    
                    return
                else:
                    # Missed paddle - GOAL! This organism loses a life
                    self._score_goal(org_idx)
                    return
        
        # Check if ball is outside arena (shouldn't happen with proper collision)
        dist_from_center = math.sqrt((self.ball.x - CENTER[0])**2 + (self.ball.y - CENTER[1])**2)
        if dist_from_center > self.current_radius + 50:
            # Reset ball to center
            self._reset_ball()
    
    def _score_goal(self, scored_on_idx: int):
        """Handle a goal scored against an organism."""
        paddle = self.paddles[scored_on_idx]
        paddle.score -= 1
        
        # Check if eliminated
        if paddle.score <= -self.lives_per_organism:
            self._eliminate_organism(scored_on_idx)
        else:
            self._reset_ball()
    
    def _eliminate_organism(self, organism_idx: int):
        """Remove an organism from the arena."""
        if organism_idx in self.alive_organisms:
            self.alive_organisms.remove(organism_idx)
            self.paddles[organism_idx].alive = False
            self.eliminations.append((self.frame_count, organism_idx))
            
            print(f"   💀 Organism {organism_idx} ELIMINATED! ({len(self.alive_organisms)} remain)")
            
            # Check for winner
            if len(self.alive_organisms) <= 1:
                self.game_over = True
                if self.alive_organisms:
                    self.winner = self.alive_organisms[0]
                    print(f"   🏆 CHAMPION: Organism {self.winner}!")
            else:
                # Shrink arena
                self._update_geometry()
                self._reset_ball()
    
    def _reset_ball(self):
        """Reset ball to center with random direction."""
        self.ball.x = CENTER[0]
        self.ball.y = CENTER[1]
        
        angle = self.rng.uniform(0, 2 * math.pi)
        self.ball.vx = BALL_SPEED * math.cos(angle)
        self.ball.vy = BALL_SPEED * math.sin(angle)
    
    def step(self) -> bool:
        """
        Advance one frame. Returns True if game continues.
        """
        if self.game_over:
            return False
        
        self.frame_count += 1
        
        # Get actions from all alive organisms
        for org_idx in self.alive_organisms:
            obs = self._get_observation(org_idx)
            action = self._get_organism_action(org_idx, obs)
            
            paddle = self.paddles[org_idx]
            v1, v2 = self._get_edge(paddle.edge_idx)
            edge_length = math.sqrt((v2[0] - v1[0])**2 + (v2[1] - v1[1])**2)
            paddle.move(action, edge_length)
        
        # Move ball
        self.ball.move()
        
        # Check collisions
        self._check_ball_collision()
        
        return not self.game_over
    
    def render(self):
        """Render the current game state."""
        if self.headless or self.screen is None:
            return
        
        self.screen.fill(BLACK)
        
        # Draw arena outline
        if self.num_sides >= 2:
            pygame.draw.polygon(self.screen, (50, 50, 50), self.vertices, 2)
        
        # Draw each edge with its paddle
        for i, org_idx in enumerate(self.alive_organisms):
            paddle = self.paddles[org_idx]
            v1, v2 = self._get_edge(i)
            
            # Draw edge (dim)
            pygame.draw.line(self.screen, (30, 30, 30), v1, v2, 3)
            
            # Draw paddle
            p1, p2 = self._get_paddle_rect(paddle)
            
            # Draw paddle with thickness
            normal = get_edge_normal(v1, v2)
            thickness = PADDLE_THICKNESS
            
            paddle_vertices = [
                (p1[0] - normal[0] * thickness/2, p1[1] - normal[1] * thickness/2),
                (p2[0] - normal[0] * thickness/2, p2[1] - normal[1] * thickness/2),
                (p2[0] + normal[0] * thickness/2, p2[1] + normal[1] * thickness/2),
                (p1[0] + normal[0] * thickness/2, p1[1] + normal[1] * thickness/2),
            ]
            pygame.draw.polygon(self.screen, paddle.color, paddle_vertices)
            
            # Draw organism label
            mid = get_edge_midpoint(v1, v2, 0.5)
            label_pos = (mid[0] + normal[0] * 40, mid[1] + normal[1] * 40)
            label = self.small_font.render(f"#{org_idx}", True, paddle.color)
            self.screen.blit(label, (label_pos[0] - 15, label_pos[1] - 10))
            
            # Draw score/lives
            lives_text = f"♥{self.lives_per_organism + paddle.score}"
            lives_label = self.small_font.render(lives_text, True, paddle.color)
            self.screen.blit(lives_label, (label_pos[0] - 15, label_pos[1] + 10))
        
        # Draw ball
        pygame.draw.circle(self.screen, BALL_COLOR, 
                          (int(self.ball.x), int(self.ball.y)), BALL_RADIUS)
        
        # Draw ball trail (last hitter indicator)
        if self.ball.last_hit_by is not None and self.ball.last_hit_by in self.paddles:
            color = self.paddles[self.ball.last_hit_by].color
            pygame.draw.circle(self.screen, color,
                             (int(self.ball.x), int(self.ball.y)), BALL_RADIUS + 3, 2)
        
        # Draw info
        info_text = f"Alive: {len(self.alive_organisms)} | Frame: {self.frame_count}"
        info_label = self.font.render(info_text, True, WHITE)
        self.screen.blit(info_label, (10, 10))
        
        # Draw elimination log
        y_offset = 50
        for frame, org_idx in self.eliminations[-5:]:  # Show last 5
            color = ORGANISM_COLORS[org_idx % len(ORGANISM_COLORS)]
            text = f"#{org_idx} eliminated at frame {frame}"
            label = self.small_font.render(text, True, color)
            self.screen.blit(label, (10, y_offset))
            y_offset += 20
        
        pygame.display.flip()
    
    def run(self, fps: int = 60, max_frames: int = 10000) -> Dict[str, Any]:
        """
        Run the arena until a winner is determined.
        
        Returns:
            Dict with results: winner, eliminations, scores
        """
        print(f"\n🎮 SWARM PONG ARENA")
        print(f"   Players: {len(self.organism_indices)} organisms")
        print(f"   Lives: {self.lives_per_organism} per player")
        print(f"   Arena: {self.num_sides}-sided polygon")
        print()
        
        running = True
        
        while running and self.frame_count < max_frames:
            # Handle Pygame events
            if not self.headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_SPACE:
                            # Pause/unpause
                            pass
            
            # Step simulation
            if not self.step():
                running = False
            
            # Render
            self.render()
            
            # Frame rate
            if self.clock:
                self.clock.tick(fps)

        # Handle frame budget exhaustion
        if self.frame_count >= max_frames and not self.game_over:
            self.game_over = True
            if self.alive_organisms:
                self.winner = self.alive_organisms[0]
            print(f"   Max frames reached ({max_frames}); declaring survivor {self.winner} as champion")
        
        # Game over
        if not self.headless:
            # Show winner screen briefly
            if self.winner is not None:
                self.screen.fill(BLACK)
                color = ORGANISM_COLORS[self.winner % len(ORGANISM_COLORS)]
                text = f"🏆 CHAMPION: Organism #{self.winner}!"
                label = self.font.render(text, True, color)
                rect = label.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
                self.screen.blit(label, rect)
                pygame.display.flip()
                pygame.time.wait(3000)
            
            pygame.quit()
        
        # Compile results
        results = {
            'winner': self.winner,
            'total_frames': self.frame_count,
            'eliminations': self.eliminations,
            'final_scores': {idx: p.score for idx, p in self.paddles.items()},
            'total_hits': {idx: p.hits for idx, p in self.paddles.items()},
            'seed': self.seed,
            'max_frames_reached': self.frame_count >= max_frames,
        }
        
        return results


# =============================================================================
# TOURNAMENT INTEGRATION
# =============================================================================

def run_swarm_pong_tournament(agent, 
                               organism_indices: Optional[List[int]] = None,
                               lives: int = 3,
                               headless: bool = False) -> Dict[str, Any]:
    """
    Run a Swarm Pong elimination tournament.
    
    Args:
        agent: CocoonAgent with organism brains
        organism_indices: Which organisms to include
        lives: Lives per organism
        headless: Run without display
    
    Returns:
        Tournament results
    """
    arena = SwarmPongArena(
        agent=agent,
        organism_indices=organism_indices,
        lives_per_organism=lives,
        headless=headless
    )
    
    return arena.run()


# =============================================================================
# MAIN - Demo
# =============================================================================

def main():
    """Demo the Swarm Pong Arena."""
    print("🎮 Swarm Pong Arena - Multi-Agent Elimination Battle")
    print("=" * 50)
    print()
    print("Usage with a cocoon agent:")
    print()
    print("  from cocoon import CocoonAgent")
    print("  from swarm_pong_arena import run_swarm_pong_tournament")
    print()
    print("  agent = CocoonAgent()")
    print("  results = run_swarm_pong_tournament(agent, lives=3)")
    print()
    print("  print(f'Winner: Organism #{results[\"winner\"]}')")
    print()
    print("Controls:")
    print("  ESC - Quit")
    print()
    
    # Try to run a demo if cocoon is available
    try:
        import sys
        sys.path.insert(0, '.')
        from cocoon import CocoonAgent
        
        print("Found cocoon.py - starting demo!")
        agent = CocoonAgent()
        
        # Use first 6 organisms for hexagon
        num_players = min(6, len(agent.brains))
        organism_indices = list(range(num_players))
        
        if not PYGAME_AVAILABLE:
            print("pygame not installed; running headless demo")

        results = run_swarm_pong_tournament(
            agent,
            organism_indices=organism_indices,
            lives=3,
            headless=not PYGAME_AVAILABLE
        )
        
        print("\n📊 RESULTS:")
        print(f"   Winner: Organism #{results['winner']}")
        print(f"   Total frames: {results['total_frames']}")
        print(f"   Elimination order: {[e[1] for e in results['eliminations']]}")
        
    except ImportError as e:
        print(f"Note: Could not load cocoon.py ({e})")
        print("Run this from an exported cocoon directory.")


if __name__ == "__main__":
    main()
