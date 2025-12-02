"""
MiniEnvironment - Embedded Survival Environment

A simple grid-world environment that ships with the exported agent,
allowing immediate testing without external dependencies.

Features:
- Resource collection (food, water)
- Threats to avoid (predators, hazards)
- Other agents to interact with (cooperate/compete)
- Energy management (rest to recover)
- Reproduction (spawn clones at high fitness)

This gives the exported organism a world to actually LIVE in,
demonstrating autonomous behavior rather than just inference.
"""

import numpy as np
import random
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass, field


@dataclass
class Entity:
    """Base entity in the environment."""
    x: float
    y: float
    entity_type: str
    
    def distance_to(self, other: 'Entity') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Resource(Entity):
    """Collectible resource."""
    value: float = 10.0
    respawn_time: int = 50
    collected: bool = False
    respawn_counter: int = 0


@dataclass  
class Threat(Entity):
    """Dangerous entity to avoid."""
    damage: float = 0.2
    speed: float = 0.5
    detection_range: float = 3.0


@dataclass
class OtherAgent(Entity):
    """Another agent in the environment."""
    fitness: float = 0.5
    cooperative: bool = True
    resources: float = 50.0


class MiniEnvironment:
    """
    Self-contained survival environment for testing exported agents.
    
    The agent must:
    - Collect resources to survive
    - Avoid threats
    - Manage energy (rest when low)
    - Interact with other agents (cooperate or compete)
    
    Actions (matching Butterfly System):
        0: move - Move toward nearest resource
        1: cooperate - Share resources with nearby agent
        2: compete - Take resources from nearby agent
        3: rest - Stay still, recover energy
        4: reproduce - Clone self if fitness > 0.7 (costs resources)
        5: isolate - Move away from all entities
    """
    
    def __init__(self,
                 grid_size: float = 20.0,
                 num_resources: int = 15,
                 num_threats: int = 3,
                 num_other_agents: int = 5,
                 max_steps: int = 1000,
                 seed: Optional[int] = None):
        """
        Initialize environment.
        
        Args:
            grid_size: Size of the square grid
            num_resources: Number of resource entities
            num_threats: Number of threat entities
            num_other_agents: Number of other agents
            max_steps: Maximum steps per episode
            seed: Random seed for reproducibility
        """
        self.grid_size = grid_size
        self.num_resources = num_resources
        self.num_threats = num_threats
        self.num_other_agents = num_other_agents
        self.max_steps = max_steps
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.reset()
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        # Agent state
        self.agent_x = self.grid_size / 2
        self.agent_y = self.grid_size / 2
        self.agent_resources = 100.0
        self.agent_energy = 1.0
        self.agent_fitness = 0.5
        
        # Spawn resources
        self.resources: List[Resource] = []
        for _ in range(self.num_resources):
            self.resources.append(Resource(
                x=random.uniform(0, self.grid_size),
                y=random.uniform(0, self.grid_size),
                entity_type='resource',
                value=random.uniform(5, 20)
            ))
        
        # Spawn threats
        self.threats: List[Threat] = []
        for _ in range(self.num_threats):
            self.threats.append(Threat(
                x=random.uniform(0, self.grid_size),
                y=random.uniform(0, self.grid_size),
                entity_type='threat',
                damage=random.uniform(0.1, 0.3),
                speed=random.uniform(0.3, 0.7)
            ))
        
        # Spawn other agents
        self.other_agents: List[OtherAgent] = []
        for _ in range(self.num_other_agents):
            self.other_agents.append(OtherAgent(
                x=random.uniform(0, self.grid_size),
                y=random.uniform(0, self.grid_size),
                entity_type='agent',
                fitness=random.uniform(0.3, 0.7),
                cooperative=random.random() > 0.3,
                resources=random.uniform(30, 70)
            ))
        
        self.step_count = 0
        self.total_reward = 0.0
        self.resources_collected = 0
        self.cooperations = 0
        self.competitions = 0
        
        return self._get_observation()
    
    def _get_observation(self) -> Dict[str, Any]:
        """Get current observation as dictionary."""
        # Find nearest entities
        nearest_resource = None
        nearest_resource_dist = float('inf')
        for r in self.resources:
            if not r.collected:
                dist = np.sqrt((self.agent_x - r.x)**2 + (self.agent_y - r.y)**2)
                if dist < nearest_resource_dist:
                    nearest_resource_dist = dist
                    nearest_resource = r
        
        nearest_threat = None
        nearest_threat_dist = float('inf')
        for t in self.threats:
            dist = np.sqrt((self.agent_x - t.x)**2 + (self.agent_y - t.y)**2)
            if dist < nearest_threat_dist:
                nearest_threat_dist = dist
                nearest_threat = t
        
        nearest_agent = None
        nearest_agent_dist = float('inf')
        for a in self.other_agents:
            dist = np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2)
            if dist < nearest_agent_dist:
                nearest_agent_dist = dist
                nearest_agent = a
        
        # Count neighbors
        neighbor_count = sum(1 for a in self.other_agents 
                           if np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2) < 5.0)
        
        # Average neighbor fitness
        nearby_agents = [a for a in self.other_agents 
                        if np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2) < 5.0]
        avg_neighbor_fitness = np.mean([a.fitness for a in nearby_agents]) if nearby_agents else 0.5
        
        return {
            'fitness': self.agent_fitness,
            'resources': self.agent_resources,
            'energy': self.agent_energy,
            'connections': neighbor_count,
            'neighbor_fitness': avg_neighbor_fitness,
            'distance': nearest_resource_dist / self.grid_size if nearest_resource else 1.0,
            'threat_distance': nearest_threat_dist / self.grid_size if nearest_threat else 1.0,
            'density': neighbor_count / max(len(self.other_agents), 1),
            'age': self.step_count / self.max_steps,
            'clustering': neighbor_count / 10.0,
            'system_health': (self.agent_resources / 200.0 + self.agent_energy) / 2.0,
            'position_x': self.agent_x / self.grid_size,
            'position_y': self.agent_y / self.grid_size,
            # For compatibility with full 24D perception
            'flow_in': 0.0,
            'flow_out': 0.0,
            'parent_fitness': self.agent_fitness,
            'breath_phase': (self.step_count % 60) / 60.0,
            'breath_depth': 0.5,
            'trait_divergence': 0.0,
            'network_coherence': 0.0,
            'quantum_entropy': 0.0,
            'evolution_pressure': 0.0,
            'phase_mismatch': 0.0,
        }
    
    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Execute action and return results.
        
        Args:
            action: Action index (0-5)
            
        Returns:
            (observation, reward, done, info)
        """
        self.step_count += 1
        reward = 0.0
        info = {'action_name': self._action_name(action)}
        
        # Execute action
        if action == 0:  # move
            reward += self._action_move()
        elif action == 1:  # cooperate
            reward += self._action_cooperate()
        elif action == 2:  # compete
            reward += self._action_compete()
        elif action == 3:  # rest
            reward += self._action_rest()
        elif action == 4:  # reproduce
            reward += self._action_reproduce()
        elif action == 5:  # isolate
            reward += self._action_isolate()
        
        # Update threats (they chase the agent)
        self._update_threats()
        
        # Check for threat damage
        reward += self._check_threat_damage()
        
        # Respawn collected resources
        self._respawn_resources()
        
        # Energy decay
        self.agent_energy = max(0.0, self.agent_energy - 0.005)
        
        # Resource decay
        self.agent_resources = max(0.0, self.agent_resources - 0.1)
        
        # Update fitness based on resources and energy
        self.agent_fitness = np.clip(
            0.3 * (self.agent_resources / 200.0) + 
            0.3 * self.agent_energy + 
            0.4 * self.agent_fitness,
            0.0, 1.0
        )
        
        # Check done conditions
        done = False
        if self.step_count >= self.max_steps:
            done = True
            info['reason'] = 'max_steps'
        elif self.agent_resources <= 0:
            done = True
            reward -= 10.0
            info['reason'] = 'starvation'
        elif self.agent_energy <= 0:
            done = True
            reward -= 5.0
            info['reason'] = 'exhaustion'
        
        self.total_reward += reward
        
        info.update({
            'step': self.step_count,
            'total_reward': self.total_reward,
            'resources_collected': self.resources_collected,
            'cooperations': self.cooperations,
            'competitions': self.competitions,
        })
        
        return self._get_observation(), reward, done, info
    
    def _action_move(self) -> float:
        """Move toward nearest resource."""
        reward = -0.01  # Small movement cost
        self.agent_energy -= 0.01
        
        # Find nearest resource
        nearest = None
        nearest_dist = float('inf')
        for r in self.resources:
            if not r.collected:
                dist = np.sqrt((self.agent_x - r.x)**2 + (self.agent_y - r.y)**2)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = r
        
        if nearest:
            # Move toward resource
            dx = nearest.x - self.agent_x
            dy = nearest.y - self.agent_y
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0:
                self.agent_x += (dx / dist) * 0.5
                self.agent_y += (dy / dist) * 0.5
            
            # Check if reached resource
            if dist < 1.0:
                nearest.collected = True
                nearest.respawn_counter = nearest.respawn_time
                self.agent_resources += nearest.value
                self.resources_collected += 1
                reward += 1.0
        else:
            # Random movement if no resources
            self.agent_x += random.uniform(-0.5, 0.5)
            self.agent_y += random.uniform(-0.5, 0.5)
        
        # Clamp to grid
        self.agent_x = np.clip(self.agent_x, 0, self.grid_size)
        self.agent_y = np.clip(self.agent_y, 0, self.grid_size)
        
        return reward
    
    def _action_cooperate(self) -> float:
        """Share resources with nearby cooperative agent."""
        reward = 0.0
        
        # Find nearest cooperative agent
        nearest = None
        nearest_dist = float('inf')
        for a in self.other_agents:
            if a.cooperative:
                dist = np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = a
        
        if nearest and nearest_dist < 2.0:
            # Share resources - both benefit
            share_amount = min(10.0, self.agent_resources * 0.1)
            self.agent_resources -= share_amount * 0.5  # Give less than receive
            self.agent_resources += share_amount  # Receive from cooperation
            nearest.resources += share_amount * 0.5
            self.cooperations += 1
            reward += 0.5
        else:
            reward -= 0.1  # Failed cooperation attempt
        
        return reward
    
    def _action_compete(self) -> float:
        """Take resources from nearby agent."""
        reward = 0.0
        self.agent_energy -= 0.05  # Competition is tiring
        
        # Find nearest agent
        nearest = None
        nearest_dist = float('inf')
        for a in self.other_agents:
            dist = np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = a
        
        if nearest and nearest_dist < 2.0:
            # Compete - success based on relative fitness
            if self.agent_fitness > nearest.fitness:
                take_amount = min(15.0, nearest.resources * 0.2)
                self.agent_resources += take_amount
                nearest.resources -= take_amount
                self.competitions += 1
                reward += 0.3
            else:
                # Lost competition
                lose_amount = min(10.0, self.agent_resources * 0.1)
                self.agent_resources -= lose_amount
                nearest.resources += lose_amount
                reward -= 0.5
        else:
            reward -= 0.1  # No target
        
        return reward
    
    def _action_rest(self) -> float:
        """Stay still and recover energy."""
        self.agent_energy = min(1.0, self.agent_energy + 0.1)
        return 0.05  # Small reward for strategic resting
    
    def _action_reproduce(self) -> float:
        """Spawn clone if fitness is high enough."""
        if self.agent_fitness > 0.7 and self.agent_resources > 50:
            # Successful reproduction
            self.agent_resources -= 30
            self.other_agents.append(OtherAgent(
                x=self.agent_x + random.uniform(-1, 1),
                y=self.agent_y + random.uniform(-1, 1),
                entity_type='agent',
                fitness=self.agent_fitness * 0.8,
                cooperative=True,
                resources=30.0
            ))
            return 2.0
        else:
            return -0.2  # Failed reproduction attempt
    
    def _action_isolate(self) -> float:
        """Move away from all entities."""
        self.agent_energy -= 0.02
        
        # Calculate repulsion from all nearby entities
        dx, dy = 0.0, 0.0
        for a in self.other_agents:
            dist = np.sqrt((self.agent_x - a.x)**2 + (self.agent_y - a.y)**2)
            if dist < 5.0 and dist > 0:
                dx += (self.agent_x - a.x) / dist
                dy += (self.agent_y - a.y) / dist
        
        for t in self.threats:
            dist = np.sqrt((self.agent_x - t.x)**2 + (self.agent_y - t.y)**2)
            if dist < 5.0 and dist > 0:
                dx += (self.agent_x - t.x) / dist * 2  # Extra repulsion from threats
                dy += (self.agent_y - t.y) / dist * 2
        
        # Normalize and move
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.agent_x += (dx / dist) * 0.5
            self.agent_y += (dy / dist) * 0.5
        
        # Clamp to grid
        self.agent_x = np.clip(self.agent_x, 0, self.grid_size)
        self.agent_y = np.clip(self.agent_y, 0, self.grid_size)
        
        return 0.0
    
    def _update_threats(self):
        """Move threats toward agent."""
        for t in self.threats:
            dist = np.sqrt((self.agent_x - t.x)**2 + (self.agent_y - t.y)**2)
            if dist < t.detection_range and dist > 0:
                # Chase agent
                dx = self.agent_x - t.x
                dy = self.agent_y - t.y
                t.x += (dx / dist) * t.speed
                t.y += (dy / dist) * t.speed
            else:
                # Random movement
                t.x += random.uniform(-0.2, 0.2)
                t.y += random.uniform(-0.2, 0.2)
            
            # Clamp to grid
            t.x = np.clip(t.x, 0, self.grid_size)
            t.y = np.clip(t.y, 0, self.grid_size)
    
    def _check_threat_damage(self) -> float:
        """Check if any threat is damaging the agent."""
        reward = 0.0
        for t in self.threats:
            dist = np.sqrt((self.agent_x - t.x)**2 + (self.agent_y - t.y)**2)
            if dist < 1.0:
                self.agent_energy -= t.damage
                self.agent_resources -= t.damage * 10
                reward -= 1.0
        return reward
    
    def _respawn_resources(self):
        """Respawn collected resources after timer."""
        for r in self.resources:
            if r.collected:
                r.respawn_counter -= 1
                if r.respawn_counter <= 0:
                    r.collected = False
                    r.x = random.uniform(0, self.grid_size)
                    r.y = random.uniform(0, self.grid_size)
    
    def _action_name(self, action: int) -> str:
        """Get action name."""
        names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        return names[action] if 0 <= action < len(names) else 'unknown'
    
    def render(self) -> str:
        """
        Render environment as ASCII art.
        
        Returns:
            ASCII representation of the environment
        """
        # Create grid
        size = 20
        scale = size / self.grid_size
        grid = [['.' for _ in range(size)] for _ in range(size)]
        
        # Place resources
        for r in self.resources:
            if not r.collected:
                x, y = int(r.x * scale), int(r.y * scale)
                if 0 <= x < size and 0 <= y < size:
                    grid[y][x] = '$'
        
        # Place threats
        for t in self.threats:
            x, y = int(t.x * scale), int(t.y * scale)
            if 0 <= x < size and 0 <= y < size:
                grid[y][x] = 'X'
        
        # Place other agents
        for a in self.other_agents:
            x, y = int(a.x * scale), int(a.y * scale)
            if 0 <= x < size and 0 <= y < size:
                grid[y][x] = 'o' if a.cooperative else 'x'
        
        # Place player agent
        ax, ay = int(self.agent_x * scale), int(self.agent_y * scale)
        if 0 <= ax < size and 0 <= ay < size:
            grid[ay][ax] = '@'
        
        # Build output
        lines = [
            f"Step: {self.step_count}/{self.max_steps} | "
            f"Resources: {self.agent_resources:.1f} | "
            f"Energy: {self.agent_energy:.2f} | "
            f"Fitness: {self.agent_fitness:.3f}",
            "+" + "-" * size + "+",
        ]
        for row in grid:
            lines.append("|" + "".join(row) + "|")
        lines.append("+" + "-" * size + "+")
        lines.append("Legend: @ = Agent, $ = Resource, X = Threat, o = Friendly, x = Hostile")
        
        return "\n".join(lines)
