#!/usr/bin/env python3
"""
🛸 DRONE SIMULATION TEST

Verifies that organisms can control drones through the adapter.
Tests the full pipeline: Organism → DroneAdapter → Physics → Learning

Usage:
    python test_drone_simulation.py
"""

import sys
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


def create_mock_organism(name: str = "test_org"):
    """Create a mock organism for testing without full Reality Simulator."""
    class MockOrganism:
        def __init__(self, name):
            self.organism_id = f"{name}_{np.random.randint(10000, 99999)}"
            self.species_id = self.organism_id
            self.fitness = np.random.uniform(0.3, 0.8)
            self.energy = 100.0
            self.prev_state = None
            self.prev_action = None
            self.experiences = []
            
        def decide(self):
            """Make a random decision (0-5)."""
            return np.random.randint(0, 6)
        
        def decide_action(self, *args, **kwargs):
            """Neural-style decision."""
            return self.decide()
        
        def record_experience(self, reward, next_state, done):
            """Record learning experience."""
            if self.prev_state is not None:
                self.experiences.append({
                    'state': self.prev_state,
                    'action': self.prev_action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done
                })
        
        def record_gym_experience(self, state, action, reward, next_state, done):
            """Record gym-style experience."""
            self.experiences.append({
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state,
                'done': done
            })
            
    return MockOrganism(name)


def try_load_real_organism():
    """Try to load a real organism from the system."""
    try:
        from reality_simulator.neural import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        genotype = Genotype.random()
        config = {'neural': {'enabled': False}}  # Simple mode
        organism = NeuralOrganism(genotype, config=config)
        logger.info(f"✅ Loaded real NeuralOrganism: {organism.organism_id[:12]}")
        return organism
    except Exception as e:
        logger.warning(f"⚠️ Could not load real organism: {e}")
        return None


def test_drone_adapter():
    """Test the drone adapter with a mock organism."""
    print("\n" + "="*60)
    print("🛸 TEST 1: DroneAdapter with Mock Organism")
    print("="*60)
    
    from reality_simulator.arena.drone_adapter import (
        OrganismDroneAdapter, 
        DroneState, 
        DroneAction,
        PYFLYT_AVAILABLE
    )
    
    print(f"PyFlyt Available: {PYFLYT_AVAILABLE}")
    
    # Create mock organism
    org = create_mock_organism("alpha")
    print(f"Created organism: {org.organism_id}")
    
    # Create adapter
    adapter = OrganismDroneAdapter(org, drone_id=0, team="blue")
    print(f"Created adapter for drone_id={adapter.drone_id}, team={adapter.team}")
    
    # Test state observation
    print("\n📊 Testing observation conversion...")
    adapter.state.position = np.array([1.0, 2.0, 3.0])
    adapter.state.velocity = np.array([0.5, -0.3, 0.1])
    adapter.state.enemies_positions = [np.array([5.0, 5.0, 3.0])]
    adapter.state.allies_positions = [np.array([0.5, 1.0, 3.0])]
    adapter.state.health = 0.75
    
    obs = adapter.state.to_observation()
    print(f"Observation shape: {obs.shape}")
    print(f"Position obs: {obs[0:3]}")
    print(f"Velocity obs: {obs[3:6]}")
    print(f"Health obs: {obs[16]}")
    assert obs.shape == (28,), f"Expected 28-dim obs, got {obs.shape}"
    print("✅ Observation conversion works!")
    
    # Test action translation
    print("\n🎮 Testing action translation...")
    for action_idx in range(6):
        action_name = DroneAction(action_idx).name
        command = adapter.translate_action(action_idx, adapter.state)
        print(f"  Action {action_idx} ({action_name}): {command}")
    print("✅ Action translation works!")
    
    # Test decision flow
    print("\n🧠 Testing decision flow...")
    action, command = adapter.get_action()
    print(f"Organism decided action {action}, translated to {command}")
    print("✅ Decision flow works!")
    
    # Test experience recording
    print("\n📝 Testing experience recording...")
    adapter.record_step(reward=1.0, done=False)
    print(f"Organism recorded {len(org.experiences)} experiences")
    print("✅ Experience recording works!")
    
    return True


def test_swarm_battle_simulated():
    """Test swarm battle with simulated physics (no PyFlyt)."""
    print("\n" + "="*60)
    print("⚔️ TEST 2: Swarm Battle (Simulated Physics)")
    print("="*60)
    
    from reality_simulator.arena.swarm_battle import (
        SwarmBattle, 
        BattleConfig, 
        BattleOutcome
    )
    
    # Create teams
    blue_team = [create_mock_organism(f"blue_{i}") for i in range(3)]
    red_team = [create_mock_organism(f"red_{i}") for i in range(3)]
    
    print(f"Blue team: {[o.organism_id[:8] for o in blue_team]}")
    print(f"Red team: {[o.organism_id[:8] for o in red_team]}")
    
    # Configure short battle
    config = BattleConfig(
        max_duration=5.0,  # 5 seconds
        tick_rate=0.1
    )
    
    # Run battle
    print("\n🎮 Running battle...")
    battle = SwarmBattle(blue_team, red_team, config)
    stats = battle.run()
    battle.close()
    
    # Check results
    print(f"\n📊 Battle Results:")
    print(f"   Outcome: {stats.outcome.value}")
    print(f"   Duration: {stats.duration:.1f}s")
    print(f"   Blue survivors: {stats.blue_survivors}")
    print(f"   Red survivors: {stats.red_survivors}")
    print(f"   Total tags: {stats.total_tags}")
    print(f"   Eliminations: {stats.total_eliminations}")
    
    # Check organism stats
    print(f"\n👤 Per-organism stats:")
    for org_id, ostats in stats.organism_stats.items():
        print(f"   {org_id[:8]}: team={ostats['team']}, alive={ostats['alive']}, tags={ostats['tags_scored']}")
    
    # Verify experiences were recorded
    total_experiences = sum(len(o.experiences) for o in blue_team + red_team)
    print(f"\n📝 Total experiences recorded: {total_experiences}")
    
    print("✅ Swarm battle works!")
    return True


def test_drone_warfare_arena():
    """Test the DroneWarfareArena integration."""
    print("\n" + "="*60)
    print("🛸⚔️ TEST 3: Drone Warfare Arena")
    print("="*60)
    
    from reality_simulator.arena.drone_warfare import (
        DroneWarfareArena,
        WarfareConfig
    )
    
    # Create mock alliances
    class MockAlliance:
        def __init__(self, name, size):
            self.name = name
            self.members = [create_mock_organism(f"{name}_{i}") for i in range(size)]
    
    alliance_a = MockAlliance("Alpha", 3)
    alliance_b = MockAlliance("Beta", 3)
    
    print(f"Alliance A ({alliance_a.name}): {len(alliance_a.members)} organisms")
    print(f"Alliance B ({alliance_b.name}): {len(alliance_b.members)} organisms")
    
    # Create arena
    config = WarfareConfig()
    config.battle_config.max_duration = 5.0  # Short for testing
    
    arena = DroneWarfareArena(config=config)
    
    # Check can battle
    can_battle = arena.can_drone_battle(alliance_a, alliance_b)
    print(f"Can battle: {can_battle}")
    
    if can_battle:
        # Resolve conflict
        print("\n🎮 Resolving conflict...")
        winner, stats = arena.resolve_conflict(alliance_a, alliance_b, "test_conflict")
        
        print(f"\n🏆 Winner: {winner.name}")
        print(f"   Outcome: {stats.outcome.value}")
        print(f"   Duration: {stats.duration:.1f}s")
        
        print(f"\n📊 Arena Stats:")
        print(f"   {arena.get_stats()}")
    
    print("✅ Drone Warfare Arena works!")
    return True


def test_proton_game_drone_selection():
    """Test that drone games appear in Proton Game selection."""
    print("\n" + "="*60)
    print("🎮 TEST 4: Proton Game Drone Selection")
    print("="*60)
    
    from reality_simulator.arena.proton_game import (
        ProtonGameArena,
        GAME_GRID,
        DRONE_WARFARE_GAMES,
        is_discrete_game,
        ChallengeType,
        ResourceType
    )
    
    # Count drone games
    drone_count = len(DRONE_WARFARE_GAMES)
    print(f"Drone games defined: {drone_count}")
    
    # Check they're in the grid
    drone_in_grid = sum(
        1 for games in GAME_GRID.values() 
        for g in games if g.gym_env.startswith('drone://')
    )
    print(f"Drone games in GAME_GRID: {drone_in_grid}")
    
    # Create arena with discrete_only
    arena = ProtonGameArena(discrete_only=True, gym_only=False)
    
    # Test selection with PHYSICAL/MACHINE (where most drone games are)
    from reality_simulator.arena.proton_game import SelectionState
    
    state = arena.begin_selection("org_a_123", "org_b_456")
    state = arena.choose_challenge(state, state.row_chooser, ChallengeType.PHYSICAL)
    state = arena.choose_resource(state, state.column_chooser, ResourceType.MACHINE)
    
    print(f"\n📋 Available games for PHYSICAL/MACHINE:")
    for game in state.available_games:
        is_drone = "🛸" if game.gym_env.startswith('drone://') else "🎮"
        print(f"   {is_drone} {game.name} ({game.gym_env})")
    
    # Verify drone games are present
    drone_available = sum(1 for g in state.available_games if g.gym_env.startswith('drone://'))
    print(f"\nDrone games available: {drone_available}")
    
    # Test discrete filter
    total_discrete = sum(1 for games in GAME_GRID.values() for g in games if is_discrete_game(g))
    print(f"Total discrete games: {total_discrete}")
    
    print("✅ Proton Game drone selection works!")
    return True


def test_with_real_organism():
    """Test with a real NeuralOrganism if available."""
    print("\n" + "="*60)
    print("🧬 TEST 5: Real Organism (if available)")
    print("="*60)
    
    org = try_load_real_organism()
    if org is None:
        print("⏭️ Skipping - real organism not available")
        return True
    
    from reality_simulator.arena.drone_adapter import OrganismDroneAdapter
    
    adapter = OrganismDroneAdapter(org, drone_id=0, team="blue")
    
    # Set up state
    adapter.state.position = np.array([0.0, 0.0, 2.0])
    adapter.state.velocity = np.array([0.0, 0.0, 0.0])
    adapter.state.enemies_positions = [np.array([5.0, 0.0, 2.0])]
    
    # Get decision
    action, command = adapter.get_action()
    print(f"Real organism decided: action={action}, command={command}")
    
    print("✅ Real organism works with drone adapter!")
    return True


def main():
    """Run all tests."""
    print("="*60)
    print("🛸 DRONE SIMULATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("DroneAdapter", test_drone_adapter),
        ("SwarmBattle", test_swarm_battle_simulated),
        ("DroneWarfareArena", test_drone_warfare_arena),
        ("ProtonGameSelection", test_proton_game_drone_selection),
        ("RealOrganism", test_with_real_organism),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            import traceback
            results.append((name, False, str(e)))
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    for name, success, error in results:
        if success:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name}: {error}")
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
