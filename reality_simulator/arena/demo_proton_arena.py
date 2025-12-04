"""
🎮 PROTON GAME ARENA DEMO
=========================

Demonstrates the Apprentice Adept inspired game selection and battle system.

This shows:
1. The 4x4 game selection grid
2. AI-driven game selection based on organism traits
3. Gym-based battle execution
4. Winner determination

Usage:
    python demo_proton_arena.py
"""

import sys
import os

# Add parent directories to path
script_dir = os.path.dirname(os.path.abspath(__file__))
reality_simulator_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(reality_simulator_dir)
sys.path.insert(0, project_root)

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import random


@dataclass
class MockOrganism:
    """Mock organism for testing."""
    organism_id: str
    fitness: float = 0.5
    traits: Dict[str, float] = field(default_factory=dict)
    energy: float = 0.8
    
    def __post_init__(self):
        if not self.traits:
            self.traits = {
                'physical': random.uniform(0.3, 0.8),
                'mental': random.uniform(0.3, 0.8),
                'luck': random.uniform(0.2, 0.6),
                'creativity': random.uniform(0.3, 0.7),
                'balance': random.uniform(0.3, 0.7),
                'speed': random.uniform(0.3, 0.7),
                'planning': random.uniform(0.3, 0.7),
            }


class MockBridge:
    """Mock AgentBridge for testing without full system."""
    
    def __init__(self, organism_id: str, skill_level: float = 0.5):
        self.organism_id = organism_id
        self.skill_level = skill_level
        self.vocabulary = MockVocab()
    
    def run_gym(self, env_name: str, episodes: int = 3, **kwargs) -> Dict[str, Any]:
        """Simulate running a gym environment."""
        # Simulate scores based on skill level with some randomness
        base_score = self.skill_level * 100
        scores = [base_score + random.uniform(-20, 30) for _ in range(episodes)]
        
        mean_reward = sum(scores) / len(scores)
        
        print(f"  🎮 {self.organism_id[:8]} played {env_name}:")
        print(f"     Scores: {[f'{s:.1f}' for s in scores]}")
        print(f"     Mean: {mean_reward:.1f}")
        
        return {
            'mean_reward': mean_reward,
            'max_reward': max(scores),
            'min_reward': min(scores),
            'episodes': episodes,
            'env': env_name
        }
    
    def process(self, text: str = "") -> Any:
        """Mock text processing."""
        class MockResult:
            response = "mock response words here"
            confidence = 0.7
        return MockResult()


class MockVocab:
    vocab_size = random.randint(100, 500)


def main():
    print("=" * 70)
    print("🎮 PROTON GAME ARENA DEMO")
    print("=" * 70)
    print()
    
    # Import the arena
    from reality_simulator.arena import (
        ProtonGameArena, 
        ChallengeType, 
        ResourceType,
        GAME_GRID
    )
    
    # Create the arena
    arena = ProtonGameArena()
    
    # Display the game grid
    print("\n📊 GAME SELECTION GRID:")
    arena.display_grid()
    
    # Create mock organisms
    print("\n\n🦋 CREATING COMBATANTS...")
    
    org_a = MockOrganism(
        organism_id="alpha-warrior-001",
        fitness=0.7,
        traits={
            'physical': 0.8,
            'mental': 0.5,
            'balance': 0.7,
            'speed': 0.6,
            'luck': 0.3,
        }
    )
    
    org_b = MockOrganism(
        organism_id="beta-strategist-002", 
        fitness=0.65,
        traits={
            'physical': 0.5,
            'mental': 0.8,
            'planning': 0.7,
            'probability_sense': 0.6,
            'luck': 0.5,
        }
    )
    
    print(f"\n  🔴 {org_a.organism_id}")
    print(f"     Fitness: {org_a.fitness}")
    print(f"     Traits: {org_a.traits}")
    
    print(f"\n  🔵 {org_b.organism_id}")
    print(f"     Fitness: {org_b.fitness}")
    print(f"     Traits: {org_b.traits}")
    
    # Create mock bridges
    bridge_a = MockBridge(org_a.organism_id, skill_level=0.6)
    bridge_b = MockBridge(org_b.organism_id, skill_level=0.55)
    
    # Run the game selection process
    print("\n\n⚔️ INITIATING PROTON GAME SELECTION...")
    print("-" * 50)
    
    # Step 1: Begin selection (random row/column assignment)
    state = arena.begin_selection(org_a.organism_id, org_b.organism_id)
    
    print(f"\n  📌 Row chooser (Challenge): {state.row_chooser[:15]}")
    print(f"  📌 Column chooser (Resource): {state.column_chooser[:15]}")
    
    # Step 2: AI selects challenge based on traits
    traits_a = org_a.traits
    traits_b = org_b.traits
    
    if state.row_chooser == org_a.organism_id:
        challenge = arena.ai_select_challenge(state, traits_a, traits_b)
        arena.choose_challenge(state, org_a.organism_id, challenge)
    else:
        challenge = arena.ai_select_challenge(state, traits_b, traits_a)
        arena.choose_challenge(state, org_b.organism_id, challenge)
    
    # Step 3: AI selects resource
    if state.column_chooser == org_a.organism_id:
        resource = arena.ai_select_resource(state, traits_a, traits_b)
        arena.choose_resource(state, org_a.organism_id, resource)
    else:
        resource = arena.ai_select_resource(state, traits_b, traits_a)
        arena.choose_resource(state, org_b.organism_id, resource)
    
    # Step 4: Select final game
    arena.select_final_game(state)
    
    print("\n" + "-" * 50)
    print(f"  🎯 SELECTED: {state.final_game.name}")
    print(f"     Category: {state.challenge_choice.value.upper()} × {state.resource_choice.value.upper()}")
    print(f"     Environment: {state.final_game.gym_env}")
    print(f"     Difficulty: {state.final_game.difficulty.name}")
    print("-" * 50)
    
    # Step 5: Execute battle
    print("\n\n🎮 EXECUTING BATTLE...")
    print("=" * 50)
    
    result = arena.execute_battle(state, bridge_a, bridge_b, episodes=3)
    
    # Show results
    print("\n" + "=" * 50)
    print("📊 BATTLE RESULTS")
    print("=" * 50)
    print(f"\n  🔴 {result.organism_a_id[:15]}: {result.score_a:.2f}")
    print(f"  🔵 {result.organism_b_id[:15]}: {result.score_b:.2f}")
    
    if result.winner_id:
        print(f"\n  🏆 WINNER: {result.winner_id[:15]}")
        print(f"     Margin: {result.margin:.2f}")
    else:
        print(f"\n  🤝 TIE!")
    
    print(f"\n  ⏱️ Duration: {result.battle_duration:.2f}s")
    print(f"  📊 Episodes: {result.total_episodes}")
    
    # Apply consequences (mock)
    print("\n\n💀 APPLYING CONSEQUENCES...")
    consequences = arena.apply_consequences(result, org_a, org_b, highlander_mode=False)
    
    print(f"  Fitness transferred: {consequences['fitness_transferred']:.3f}")
    print(f"  Resources transferred: {consequences['resources_transferred']:.3f}")
    
    # Show arena stats
    print("\n\n📈 ARENA STATISTICS:")
    stats = arena.get_statistics()
    print(f"  Total battles: {stats['total_battles']}")
    print(f"  Games played: {stats['game_play_counts']}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    main()
