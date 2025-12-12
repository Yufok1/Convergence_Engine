#!/usr/bin/env python3
"""
Test script for the new ensemble voting system in AgentBridge.

This tests:
1. All voting strategies work correctly
2. Fitness weighting is applied properly
3. Ensemble results are included in output
4. Strategy switching works at runtime
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from reality_simulator.portable_agent.bridge import (
    AgentBridge, AgentConfig, OrganismVote, EnsembleResult,
    EnsembleVotingStrategy
)


def test_voting_strategies():
    """Test all voting strategy implementations with mock votes."""
    print("\n" + "="*60)
    print("Testing Voting Strategies")
    print("="*60)
    
    # Create a mock bridge for testing
    config = AgentConfig(
        is_ensemble=True,
        member_count=6,
        voting_strategy="majority",
        member_fitness=[1.0, 0.8, 1.2, 0.5, 1.5, 0.9],
        member_ids=["org_a", "org_b", "org_c", "org_d", "org_e", "org_f"]
    )
    bridge = AgentBridge(config=config)
    
    # Create mock votes with varied actions and confidences
    # Simulating 6 organisms voting
    mock_votes = [
        OrganismVote(0, "org_a", action=1, q_values=[0.1, 0.5, 0.2, 0.1, 0.05, 0.05], 
                    confidence=0.6, fitness=1.0, weight=0.6),
        OrganismVote(1, "org_b", action=2, q_values=[0.1, 0.2, 0.4, 0.15, 0.1, 0.05], 
                    confidence=0.5, fitness=0.8, weight=0.4),
        OrganismVote(2, "org_c", action=1, q_values=[0.05, 0.45, 0.3, 0.1, 0.05, 0.05], 
                    confidence=0.55, fitness=1.2, weight=0.66),
        OrganismVote(3, "org_d", action=3, q_values=[0.1, 0.1, 0.1, 0.5, 0.1, 0.1], 
                    confidence=0.7, fitness=0.5, weight=0.35),
        OrganismVote(4, "org_e", action=1, q_values=[0.0, 0.6, 0.2, 0.1, 0.05, 0.05], 
                    confidence=0.75, fitness=1.5, weight=1.125),
        OrganismVote(5, "org_f", action=2, q_values=[0.1, 0.15, 0.45, 0.15, 0.1, 0.05], 
                    confidence=0.55, fitness=0.9, weight=0.495),
    ]
    
    # Test each strategy
    strategies = [
        ("single", bridge._vote_single),
        ("majority", bridge._vote_majority),
        ("fitness_weighted", bridge._vote_fitness_weighted),
        ("confidence_weighted", bridge._vote_confidence_weighted),
        ("softmax_ensemble", bridge._vote_softmax_ensemble),
    ]
    
    results = {}
    for name, method in strategies:
        result = method(mock_votes)
        results[name] = result
        
        print(f"\n{name.upper()} Strategy:")
        print(f"  Winner: {result.action_name} (action {result.winning_action})")
        print(f"  Agreement: {result.agreement_ratio*100:.1f}%")
        print(f"  Vote counts: {result.vote_counts}")
        if result.weighted_votes:
            print(f"  Weighted votes: {dict((k, f'{v:.3f}') for k,v in result.weighted_votes.items())}")
    
    # Test fittest_top_k separately
    result = bridge._vote_fittest_top_k(mock_votes, k=3)
    results["fittest_top_3"] = result
    print(f"\nFITTEST_TOP_3 Strategy:")
    print(f"  Winner: {result.action_name} (action {result.winning_action})")
    print(f"  Agreement: {result.agreement_ratio*100:.1f}%")
    print(f"  Voters used: {len(result.votes)} (top 3 by fitness)")
    print(f"  Vote counts: {result.vote_counts}")
    
    # Verify expected behavior
    print("\n" + "-"*40)
    print("Verification:")
    
    # Single should use first organism's action (1 = cooperate)
    assert results["single"].winning_action == 1, "Single should use first organism"
    print("  [OK] Single strategy uses first organism")
    
    # Majority: action 1 has 3 votes, action 2 has 2 votes, action 3 has 1 vote
    assert results["majority"].winning_action == 1, "Majority should select action 1 (3 votes)"
    assert results["majority"].vote_counts[1] == 3, "Action 1 should have 3 votes"
    print("  [OK] Majority voting counts correctly")
    
    # Fitness-weighted: action 1 has organisms with fitness 1.0, 1.2, 1.5 voting for it
    # Sum of weights for action 1 = 0.6 + 0.66 + 1.125 = 2.385
    # This should be highest
    assert results["fitness_weighted"].winning_action == 1, "Fitness-weighted should favor action 1"
    print("  [OK] Fitness weighting applied correctly")
    
    print("\n[OK] All voting strategies passed verification")
    return True


def test_strategy_switching():
    """Test runtime strategy switching."""
    print("\n" + "="*60)
    print("Testing Runtime Strategy Switching")
    print("="*60)
    
    config = AgentConfig(
        is_ensemble=True,
        member_count=4,
        voting_strategy="single"
    )
    bridge = AgentBridge(config=config)
    
    print(f"  Initial strategy: {bridge.config.voting_strategy}")
    
    # Switch strategies
    for strategy in ["majority", "fitness_weighted", "softmax_ensemble", "single"]:
        bridge.set_voting_strategy(strategy)
        print(f"  Switched to: {bridge.config.voting_strategy}")
        assert bridge.config.voting_strategy == strategy
    
    # Test invalid strategy
    try:
        bridge.set_voting_strategy("invalid_strategy")
        print("  [X] Should have raised error for invalid strategy")
        return False
    except ValueError as e:
        print(f"  [OK] Correctly rejected invalid strategy: {e}")
    
    print("\n[OK] Strategy switching works correctly")
    return True


def test_ensemble_stats():
    """Test ensemble statistics retrieval."""
    print("\n" + "="*60)
    print("Testing Ensemble Statistics")
    print("="*60)
    
    # Non-ensemble
    bridge1 = AgentBridge()
    stats1 = bridge1.get_ensemble_stats()
    assert stats1['is_ensemble'] == False
    print("  [OK] Non-ensemble correctly reports is_ensemble=False")
    
    # Ensemble
    config = AgentConfig(
        is_ensemble=True,
        member_count=5,
        voting_strategy="fitness_weighted",
        member_fitness=[1.0, 0.8, 1.2, 0.5, 1.5],
        member_ids=["a", "b", "c", "d", "e"]
    )
    bridge2 = AgentBridge(config=config)
    stats2 = bridge2.get_ensemble_stats()
    
    print(f"  is_ensemble: {stats2['is_ensemble']}")
    print(f"  member_count: {stats2['member_count']}")
    print(f"  voting_strategy: {stats2['voting_strategy']}")
    print(f"  fitness_stats: {stats2['fitness_stats']}")
    print(f"  member_ids (first 5): {stats2['member_ids']}")
    
    assert stats2['is_ensemble'] == True
    assert stats2['member_count'] == 5
    assert stats2['fitness_stats']['min'] == 0.5
    assert stats2['fitness_stats']['max'] == 1.5
    
    print("\n[OK] Ensemble statistics correct")
    return True


def test_process_with_mock_ensemble():
    """Test process() with a simulated ensemble setup."""
    print("\n" + "="*60)
    print("Testing Process with Ensemble")
    print("="*60)
    
    config = AgentConfig(
        is_ensemble=True,
        member_count=3,
        voting_strategy="fitness_weighted",
        member_fitness=[1.0, 0.8, 1.2],
        member_ids=["org_1", "org_2", "org_3"],
        state_dim=25  # Matches config.json neural.brain.input_dim
    )
    bridge = AgentBridge(config=config)
    
    # Process without a brain (will use random actions)
    result = bridge.process(text="danger enemy attack")
    
    print(f"  Action: {result.action_name} ({result.action})")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Response: {result.response}")
    print(f"  Metadata: {result.metadata}")
    
    # Check that ensemble metadata is included
    assert result.metadata.get('is_ensemble') == True
    assert result.metadata.get('voting_strategy') == 'fitness_weighted'
    assert result.metadata.get('member_count') == 3
    print("\n  [OK] Ensemble metadata included in result")
    
    # Test strategy switching affects results
    bridge.set_voting_strategy("majority")
    result2 = bridge.process(text="danger enemy attack")
    assert result2.metadata.get('voting_strategy') == 'majority'
    print("  [OK] Strategy switch reflected in process results")
    
    print("\n[OK] Process with ensemble works correctly")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# ENSEMBLE VOTING SYSTEM TESTS")
    print("#"*60)
    
    tests = [
        ("Voting Strategies", test_voting_strategies),
        ("Strategy Switching", test_strategy_switching),
        ("Ensemble Stats", test_ensemble_stats),
        ("Process with Ensemble", test_process_with_mock_ensemble),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
                print(f"\n[FAIL] {name}")
        except Exception as e:
            failed += 1
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
