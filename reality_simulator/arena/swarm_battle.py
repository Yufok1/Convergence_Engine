"""
⚔️ SWARM BATTLE ENGINE

Alliance vs Alliance drone combat.
Each organism in an alliance controls a drone.
Last team with surviving drones wins.

The battlefield is where language becomes tactics:
- Organisms that evolved "defend" together survive longer
- Organisms that share "attack" vocabulary coordinate strikes
- Alliances with communication have advantage over loners

Combat Mechanics:
- TAG: Close proximity (< 1m) = hit, 4 hits = elimination
- RAM: Collision at high speed = mutual damage
- ZONE: Control center for bonus points
- SURVIVAL: Points per second alive

Victory Conditions:
- ELIMINATION: All enemy drones destroyed
- TIMEOUT: Most surviving drones + highest total health
- ZONE CONTROL: Hold center longest (alternative mode)
"""

import logging
import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import drone adapter
from .drone_adapter import (
    OrganismDroneAdapter, 
    DroneState,
    PYFLYT_AVAILABLE
)

if PYFLYT_AVAILABLE:
    import gymnasium


class BattleOutcome(Enum):
    """Possible battle results."""
    BLUE_WINS = "blue_wins"
    RED_WINS = "red_wins"
    DRAW = "draw"
    TIMEOUT = "timeout"


@dataclass
class BattleConfig:
    """Configuration for swarm battle."""
    # Arena
    arena_size: float = 20.0           # Meters, cube arena
    spawn_separation: float = 10.0      # Initial team separation
    
    # Combat
    tag_distance: float = 1.0           # Meters for tag hit
    tag_damage: float = 0.25            # Health lost per tag (4 tags = death)
    tag_cooldown: float = 2.0           # Seconds between tags
    ram_damage: float = 0.5             # Collision damage
    ram_speed_threshold: float = 3.0    # Min closing speed for ram
    
    # Time
    max_duration: float = 60.0          # Seconds
    tick_rate: float = 0.1              # Simulation timestep
    
    # Rewards (for learning)
    reward_tag: float = 1.0             # Reward for tagging enemy
    reward_tagged: float = -0.5         # Penalty for being tagged
    reward_kill: float = 5.0            # Reward for eliminating enemy
    reward_death: float = -3.0          # Penalty for being eliminated
    reward_survival: float = 0.01       # Per-tick survival bonus
    reward_ally_proximity: float = 0.005  # Bonus for staying near allies
    reward_win: float = 10.0            # Team victory bonus
    reward_lose: float = -5.0           # Team defeat penalty


@dataclass
class BattleStatistics:
    """Post-battle statistics."""
    outcome: BattleOutcome
    duration: float
    
    # Team stats
    blue_survivors: int
    red_survivors: int
    blue_total_health: float
    red_total_health: float
    
    # Combat stats
    total_tags: int
    total_eliminations: int
    
    # Per-organism stats
    organism_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class SwarmBattle:
    """
    Runs a drone battle between two alliances.
    
    Each organism in alliance_a (blue team) fights organisms in alliance_b (red team).
    Organisms use their evolved behaviors and learned vocabulary to coordinate.
    
    Usage:
        battle = SwarmBattle(alliance_a_organisms, alliance_b_organisms)
        result = battle.run()
        # result.outcome == BattleOutcome.BLUE_WINS / RED_WINS / DRAW
    """
    
    def __init__(self,
                 blue_team: List[Any],  # List of organisms
                 red_team: List[Any],
                 config: BattleConfig = None,
                 event_emitter: Any = None,
                 render: bool = False):
        """
        Args:
            blue_team: List of organisms for blue alliance
            red_team: List of organisms for red alliance
            config: Battle configuration
            event_emitter: For broadcasting battle events
            render: If True, show 3D visualization. False for headless (training)
        """
        if not PYFLYT_AVAILABLE:
            logger.info("⚠️ PyFlyt not available - using simulated physics")
        
        self.config = config or BattleConfig()
        self.event_emitter = event_emitter
        self.render = render
        
        # Create adapters for each organism
        self.blue_adapters: List[OrganismDroneAdapter] = [
            OrganismDroneAdapter(org, drone_id=i, team="blue")
            for i, org in enumerate(blue_team)
        ]
        self.red_adapters: List[OrganismDroneAdapter] = [
            OrganismDroneAdapter(org, drone_id=i + len(blue_team), team="red")
            for i, org in enumerate(red_team)
        ]
        
        self.all_adapters = self.blue_adapters + self.red_adapters
        
        # Battle state
        self.time_elapsed = 0.0
        self.battle_active = False
        
        # Environment - use multi-drone formation env if PyFlyt available
        self.env = None
        total_drones = len(self.all_adapters)
        
        if PYFLYT_AVAILABLE:
            try:
                # render_mode=None for headless (fast training)
                # render_mode="human" for 3D visualization
                render_mode = "human" if render else None
                self.env = gymnasium.make(
                    "PyFlyt/QuadX-Hover-v4",
                    render_mode=render_mode
                    # Note: PyFlyt may need specific multi-agent setup
                    # This is a placeholder - actual multi-drone needs custom env
                )
                mode = "🖥️ VISUAL" if render else "⚡ HEADLESS"
                logger.info(f"✅ Using PyFlyt physics engine ({mode})")
            except Exception as e:
                logger.warning(f"Could not create PyFlyt env: {e}")
                logger.warning("Falling back to simulated physics")
                self.env = None
        else:
            logger.info("📊 Using simulated physics (PyFlyt not installed)")
        
        logger.info(f"⚔️ SwarmBattle initialized: {len(blue_team)} blue vs {len(red_team)} red")
    
    def _spawn_positions(self) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Generate initial spawn positions for both teams."""
        sep = self.config.spawn_separation / 2
        
        blue_positions = []
        for i, _ in enumerate(self.blue_adapters):
            # Blue team spawns on -X side
            pos = np.array([
                -sep + np.random.uniform(-2, 2),
                (i - len(self.blue_adapters)/2) * 2,
                2.0 + np.random.uniform(0, 2)
            ])
            blue_positions.append(pos)
        
        red_positions = []
        for i, _ in enumerate(self.red_adapters):
            # Red team spawns on +X side
            pos = np.array([
                sep + np.random.uniform(-2, 2),
                (i - len(self.red_adapters)/2) * 2,
                2.0 + np.random.uniform(0, 2)
            ])
            red_positions.append(pos)
        
        return blue_positions, red_positions
    
    def _init_positions(self):
        """Initialize drone positions."""
        blue_pos, red_pos = self._spawn_positions()
        
        for adapter, pos in zip(self.blue_adapters, blue_pos):
            adapter.state.position = pos.copy()
            adapter.state.velocity = np.zeros(3)
            adapter.alive = True
            adapter.state.health = 1.0
        
        for adapter, pos in zip(self.red_adapters, red_pos):
            adapter.state.position = pos.copy()
            adapter.state.velocity = np.zeros(3)
            adapter.alive = True
            adapter.state.health = 1.0
    
    def _simulate_physics(self, commands: Dict[int, np.ndarray], dt: float):
        """
        Simple physics simulation when full PyFlyt multi-drone isn't available.
        
        This is a fallback - real physics through PyFlyt is preferred.
        """
        for adapter in self.all_adapters:
            if not adapter.alive:
                continue
            
            cmd = commands.get(adapter.drone_id, np.zeros(4))
            
            # Simple thrust physics
            # cmd = [throttle, roll_rate, pitch_rate, yaw_rate]
            throttle = cmd[0]
            roll_rate = cmd[1] 
            pitch_rate = cmd[2]
            yaw_rate = cmd[3]
            
            # Gravity
            gravity = np.array([0, 0, -9.81])
            
            # Thrust (simplified - just vertical + direction based on pitch/roll)
            thrust_mag = throttle * 15.0  # Max thrust
            
            # Direction based on orientation
            pitch = adapter.state.orientation[1]
            roll = adapter.state.orientation[0]
            
            thrust = np.array([
                -thrust_mag * np.sin(pitch) * 0.3,
                thrust_mag * np.sin(roll) * 0.3,
                thrust_mag * np.cos(pitch) * np.cos(roll)
            ])
            
            # Update velocity (with drag)
            drag = 0.1
            accel = thrust + gravity
            adapter.state.velocity += accel * dt
            adapter.state.velocity *= (1 - drag * dt)
            
            # Update position
            adapter.state.position += adapter.state.velocity * dt
            
            # Update orientation
            adapter.state.orientation[0] += roll_rate * dt
            adapter.state.orientation[1] += pitch_rate * dt
            adapter.state.orientation[2] += yaw_rate * dt
            
            # Clamp to arena
            adapter.state.position = np.clip(
                adapter.state.position,
                -self.config.arena_size/2,
                self.config.arena_size/2
            )
            
            # Ground collision
            if adapter.state.position[2] < 0.1:
                adapter.state.position[2] = 0.1
                adapter.state.velocity[2] = 0
                # Crash damage if too fast
                if adapter.state.velocity[2] < -5:
                    adapter.receive_tag(damage=0.5)
    
    def _check_collisions(self) -> List[Tuple[OrganismDroneAdapter, OrganismDroneAdapter]]:
        """Check for drone-drone collisions (rams)."""
        collisions = []
        
        for i, a1 in enumerate(self.all_adapters):
            if not a1.alive:
                continue
            for a2 in self.all_adapters[i+1:]:
                if not a2.alive:
                    continue
                if a1.team == a2.team:
                    continue  # No friendly fire collisions
                
                dist = np.linalg.norm(a1.state.position - a2.state.position)
                if dist < 0.5:  # Collision threshold
                    # Check closing speed
                    rel_vel = np.linalg.norm(a1.state.velocity - a2.state.velocity)
                    if rel_vel > self.config.ram_speed_threshold:
                        collisions.append((a1, a2))
        
        return collisions
    
    def _process_combat(self) -> Dict[str, float]:
        """Process tags and collisions, return rewards per organism."""
        rewards = {a.organism.organism_id: 0.0 for a in self.all_adapters}
        
        # Check tags (blue attacks red)
        for blue in self.blue_adapters:
            if not blue.alive:
                continue
            tagged = blue.check_tag(self.red_adapters, self.config.tag_distance)
            if tagged:
                tagged.receive_tag(self.config.tag_damage)
                rewards[blue.organism.organism_id] += self.config.reward_tag
                rewards[tagged.organism.organism_id] += self.config.reward_tagged
                
                if not tagged.alive:
                    rewards[blue.organism.organism_id] += self.config.reward_kill
                    rewards[tagged.organism.organism_id] += self.config.reward_death
                    
                    self._emit_event('drone_eliminated', {
                        'killer': blue.organism.organism_id,
                        'victim': tagged.organism.organism_id,
                        'team_eliminated': 'red'
                    })
        
        # Check tags (red attacks blue)
        for red in self.red_adapters:
            if not red.alive:
                continue
            tagged = red.check_tag(self.blue_adapters, self.config.tag_distance)
            if tagged:
                tagged.receive_tag(self.config.tag_damage)
                rewards[red.organism.organism_id] += self.config.reward_tag
                rewards[tagged.organism.organism_id] += self.config.reward_tagged
                
                if not tagged.alive:
                    rewards[red.organism.organism_id] += self.config.reward_kill
                    rewards[tagged.organism.organism_id] += self.config.reward_death
                    
                    self._emit_event('drone_eliminated', {
                        'killer': red.organism.organism_id,
                        'victim': tagged.organism.organism_id,
                        'team_eliminated': 'blue'
                    })
        
        # Check ram collisions
        for a1, a2 in self._check_collisions():
            a1.receive_tag(self.config.ram_damage)
            a2.receive_tag(self.config.ram_damage)
            
            # Both take damage
            rewards[a1.organism.organism_id] += self.config.reward_tagged
            rewards[a2.organism.organism_id] += self.config.reward_tagged
            
            self._emit_event('drone_collision', {
                'drone_a': a1.organism.organism_id,
                'drone_b': a2.organism.organism_id
            })
        
        # Survival rewards
        for adapter in self.all_adapters:
            if adapter.alive:
                rewards[adapter.organism.organism_id] += self.config.reward_survival
        
        return rewards
    
    def _check_victory(self) -> Optional[BattleOutcome]:
        """Check if battle has ended."""
        blue_alive = sum(1 for a in self.blue_adapters if a.alive)
        red_alive = sum(1 for a in self.red_adapters if a.alive)
        
        if blue_alive == 0 and red_alive == 0:
            return BattleOutcome.DRAW
        elif blue_alive == 0:
            return BattleOutcome.RED_WINS
        elif red_alive == 0:
            return BattleOutcome.BLUE_WINS
        elif self.time_elapsed >= self.config.max_duration:
            # Timeout - most survivors wins
            if blue_alive > red_alive:
                return BattleOutcome.BLUE_WINS
            elif red_alive > blue_alive:
                return BattleOutcome.RED_WINS
            else:
                # Tiebreaker: total health
                blue_health = sum(a.state.health for a in self.blue_adapters if a.alive)
                red_health = sum(a.state.health for a in self.red_adapters if a.alive)
                if blue_health > red_health:
                    return BattleOutcome.BLUE_WINS
                elif red_health > blue_health:
                    return BattleOutcome.RED_WINS
                else:
                    return BattleOutcome.DRAW
        
        return None  # Battle continues
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit battle event if emitter available."""
        if self.event_emitter and hasattr(self.event_emitter, 'emit'):
            self.event_emitter.emit(f'swarm_battle_{event_type}', data)
    
    def run(self, render: bool = False) -> BattleStatistics:
        """
        Execute the swarm battle.
        
        Args:
            render: Whether to visualize (requires display)
            
        Returns:
            BattleStatistics with outcome and per-organism stats
        """
        logger.info(f"⚔️ SWARM BATTLE START: {len(self.blue_adapters)} vs {len(self.red_adapters)}")
        
        self._emit_event('battle_start', {
            'blue_count': len(self.blue_adapters),
            'red_count': len(self.red_adapters)
        })
        
        # Initialize
        self._init_positions()
        self.time_elapsed = 0.0
        self.battle_active = True
        dt = self.config.tick_rate
        
        start_time = time.time()
        
        while self.battle_active:
            # Each adapter decides and generates command
            commands = {}
            
            for adapter in self.all_adapters:
                if not adapter.alive:
                    continue
                
                # Update awareness of allies/enemies
                allies = self.blue_adapters if adapter.team == "blue" else self.red_adapters
                enemies = self.red_adapters if adapter.team == "blue" else self.blue_adapters
                adapter.update_state(
                    np.concatenate([adapter.state.position, adapter.state.velocity]),
                    allies=[a for a in allies if a != adapter],
                    enemies=enemies
                )
                
                # Get action
                action, command = adapter.get_action()
                commands[adapter.drone_id] = command
            
            # Simulate physics
            self._simulate_physics(commands, dt)
            
            # Process combat
            rewards = self._process_combat()
            
            # Record experiences
            for adapter in self.all_adapters:
                reward = rewards.get(adapter.organism.organism_id, 0.0)
                adapter.record_step(reward, not adapter.alive)
                adapter.tick(dt)
            
            # Update time
            self.time_elapsed += dt
            
            # Check victory
            outcome = self._check_victory()
            if outcome:
                self.battle_active = False
                break
        
        # Battle ended - apply final rewards
        outcome = outcome or BattleOutcome.TIMEOUT
        
        for adapter in self.blue_adapters:
            if outcome == BattleOutcome.BLUE_WINS:
                adapter.record_step(self.config.reward_win, True)
            else:
                adapter.record_step(self.config.reward_lose, True)
        
        for adapter in self.red_adapters:
            if outcome == BattleOutcome.RED_WINS:
                adapter.record_step(self.config.reward_win, True)
            else:
                adapter.record_step(self.config.reward_lose, True)
        
        # Compile statistics
        stats = BattleStatistics(
            outcome=outcome,
            duration=self.time_elapsed,
            blue_survivors=sum(1 for a in self.blue_adapters if a.alive),
            red_survivors=sum(1 for a in self.red_adapters if a.alive),
            blue_total_health=sum(a.state.health for a in self.blue_adapters if a.alive),
            red_total_health=sum(a.state.health for a in self.red_adapters if a.alive),
            total_tags=sum(a.tags_scored for a in self.all_adapters),
            total_eliminations=sum(1 for a in self.all_adapters if not a.alive),
            organism_stats={
                a.organism.organism_id: {
                    'team': a.team,
                    'alive': a.alive,
                    'health': a.state.health,
                    'tags_scored': a.tags_scored,
                    'times_tagged': a.times_tagged,
                    'flight_time': a.flight_time,
                }
                for a in self.all_adapters
            }
        )
        
        logger.info(f"⚔️ BATTLE COMPLETE: {outcome.value}")
        logger.info(f"   Duration: {self.time_elapsed:.1f}s")
        logger.info(f"   Survivors: {stats.blue_survivors} blue, {stats.red_survivors} red")
        
        self._emit_event('battle_end', {
            'outcome': outcome.value,
            'duration': self.time_elapsed,
            'blue_survivors': stats.blue_survivors,
            'red_survivors': stats.red_survivors
        })
        
        return stats
    
    def close(self):
        """Clean up resources."""
        if self.env:
            self.env.close()


# =============================================================================
# Alliance Battle Integration
# =============================================================================

def run_alliance_battle(alliance_a, alliance_b, 
                        event_emitter=None,
                        config: BattleConfig = None) -> Tuple[Any, BattleStatistics]:
    """
    Convenience function to run battle between two alliances.
    
    Args:
        alliance_a: Alliance object or list of organisms (blue team)
        alliance_b: Alliance object or list of organisms (red team)
        event_emitter: For battle events
        config: Battle configuration
        
    Returns:
        Tuple of (winning_alliance, battle_stats)
    """
    # Extract organisms from alliance objects if needed
    if hasattr(alliance_a, 'members'):
        blue_orgs = list(alliance_a.members.values()) if isinstance(alliance_a.members, dict) else list(alliance_a.members)
    else:
        blue_orgs = list(alliance_a)
    
    if hasattr(alliance_b, 'members'):
        red_orgs = list(alliance_b.members.values()) if isinstance(alliance_b.members, dict) else list(alliance_b.members)
    else:
        red_orgs = list(alliance_b)
    
    # Run battle
    battle = SwarmBattle(blue_orgs, red_orgs, config, event_emitter)
    stats = battle.run()
    battle.close()
    
    # Determine winner
    if stats.outcome == BattleOutcome.BLUE_WINS:
        winner = alliance_a
    elif stats.outcome == BattleOutcome.RED_WINS:
        winner = alliance_b
    else:
        # Draw - pick by total health or random
        if stats.blue_total_health >= stats.red_total_health:
            winner = alliance_a
        else:
            winner = alliance_b
    
    return winner, stats


# =============================================================================
# Testing
# =============================================================================

def test_swarm_battle():
    """Test swarm battle with mock organisms."""
    print("⚔️ Testing SwarmBattle...")
    
    # Mock organisms
    class MockOrganism:
        def __init__(self, oid):
            self.organism_id = oid
            self.fitness = np.random.uniform(0.5, 1.0)
        def decide(self):
            return np.random.randint(0, 6)
    
    blue = [MockOrganism(f"blue_{i}") for i in range(3)]
    red = [MockOrganism(f"red_{i}") for i in range(3)]
    
    config = BattleConfig(max_duration=10.0)  # Short battle for testing
    
    battle = SwarmBattle(blue, red, config)
    stats = battle.run()
    battle.close()
    
    print(f"✅ Battle complete: {stats.outcome.value}")
    print(f"   Blue survivors: {stats.blue_survivors}")
    print(f"   Red survivors: {stats.red_survivors}")
    print(f"   Total tags: {stats.total_tags}")
    
    return stats


if __name__ == "__main__":
    test_swarm_battle()
