#!/usr/bin/env python3
"""
LANGUAGE COLLAPSE DIAGNOSTIC
============================

This script diagnoses why organisms produce repetitive single-word outputs
like "big big big hide big hide..." instead of coherent sentences.

HYPOTHESIS:
-----------
The language-game bridge's learn_from_outcome() keeps boosting `atom.strength`
for a small set of combat/action concepts (victory, attack, survive, etc.).

Since generate_tokens() sorts vocabulary by strength DESCENDING and assigns
the LOWEST token IDs to the HIGHEST strength words, these battle-boosted
concepts get IDs 5, 6, 7, etc.

Neural networks naturally favor low token IDs, so even with repetition penalty,
the same few words dominate the output.

RUN THIS TO:
1. Load organisms from state
2. Check their atomic_language strength distributions
3. Identify if combat concepts have collapsed to max strength (1.0)
4. Show which words would get the lowest token IDs

Usage:
    python diagnose_language_collapse.py
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def check_atomic_language_distribution(atomic_language):
    """Analyze the strength distribution of atomic language concepts."""
    if not atomic_language or not hasattr(atomic_language, 'atoms'):
        return None
    
    atoms = atomic_language.atoms
    
    # Get all concepts sorted by strength
    sorted_concepts = sorted(
        atoms.keys(),
        key=lambda w: (
            -atoms[w].strength,
            -atoms[w].usage_count,
            -atoms[w].last_used_time if hasattr(atoms[w], 'last_used_time') else 0
        )
    )
    
    # Analyze strength distribution
    strengths = [atoms[w].strength for w in sorted_concepts]
    magnetisms = [atoms[w].curiosity_magnetism for w in sorted_concepts if hasattr(atoms[w], 'curiosity_magnetism')]
    
    # Check for max-strength concepts (these would get lowest token IDs)
    max_strength_concepts = [w for w in sorted_concepts if atoms[w].strength >= 0.99]
    high_strength_concepts = [w for w in sorted_concepts if atoms[w].strength >= 0.8]
    
    # Combat concepts that language_game_bridge boosts
    COMBAT_CONCEPTS = {
        'victory', 'success', 'win', 'triumph', 'dominance', 'power',
        'defeat', 'loss', 'fail', 'retreat',
        'attack', 'hit', 'strike', 'target', 'precision',
        'evade', 'dodge', 'escape', 'defense',
        'survive', 'endure', 'persist', 'strong', 'resilient',
        'crash', 'fall', 'mistake', 'careful', 'avoid',
        'cooperate', 'team', 'ally', 'formation', 'coordinate',
        'control', 'territory', 'capture', 'dominate'
    }
    
    # Check if combat concepts have inflated strengths
    combat_in_top_20 = []
    for i, word in enumerate(sorted_concepts[:20]):
        if word.lower() in COMBAT_CONCEPTS:
            combat_in_top_20.append((i, word, atoms[word].strength))
    
    return {
        'total_concepts': len(atoms),
        'max_strength_count': len(max_strength_concepts),
        'high_strength_count': len(high_strength_concepts),
        'max_strength_words': max_strength_concepts[:20],  # First 20
        'top_20_by_strength': [(w, atoms[w].strength) for w in sorted_concepts[:20]],
        'bottom_20_by_strength': [(w, atoms[w].strength) for w in sorted_concepts[-20:]],
        'combat_in_top_20': combat_in_top_20,
        'strength_stats': {
            'max': max(strengths) if strengths else 0,
            'min': min(strengths) if strengths else 0,
            'avg': sum(strengths) / len(strengths) if strengths else 0,
            'at_max_count': sum(1 for s in strengths if s >= 0.99),
            'at_zero_count': sum(1 for s in strengths if s <= 0.01),
        },
        'magnetism_stats': {
            'max': max(magnetisms) if magnetisms else 0,
            'min': min(magnetisms) if magnetisms else 0,
            'avg': sum(magnetisms) / len(magnetisms) if magnetisms else 0,
        } if magnetisms else None
    }


def diagnose_organism(organism, org_id):
    """Diagnose an organism's language system."""
    print(f"\n{'='*60}")
    print(f"ORGANISM: {org_id}")
    print(f"{'='*60}")
    
    if not hasattr(organism, 'atomic_language') or organism.atomic_language is None:
        print("  ❌ No atomic_language found!")
        return
    
    analysis = check_atomic_language_distribution(organism.atomic_language)
    if not analysis:
        print("  ❌ Could not analyze atomic_language")
        return
    
    # Summary
    print(f"\n📊 STRENGTH DISTRIBUTION:")
    print(f"   Total concepts: {analysis['total_concepts']}")
    print(f"   Max strength (≥0.99): {analysis['max_strength_count']} concepts")
    print(f"   High strength (≥0.80): {analysis['high_strength_count']} concepts")
    print(f"   Stats: max={analysis['strength_stats']['max']:.3f}, min={analysis['strength_stats']['min']:.3f}, avg={analysis['strength_stats']['avg']:.3f}")
    
    if analysis['magnetism_stats']:
        print(f"\n🧲 MAGNETISM DISTRIBUTION:")
        print(f"   Stats: max={analysis['magnetism_stats']['max']:.3f}, min={analysis['magnetism_stats']['min']:.3f}, avg={analysis['magnetism_stats']['avg']:.3f}")
    
    # Top 20 concepts (these get lowest token IDs!)
    print(f"\n🎯 TOP 20 CONCEPTS (will get token IDs 5-24, most likely to be sampled):")
    for i, (word, strength) in enumerate(analysis['top_20_by_strength']):
        marker = " ⚔️" if word.lower() in {'victory', 'success', 'win', 'attack', 'survive', 'dominance', 'power', 'evade', 'dodge', 'escape', 'strong', 'resilient'} else ""
        print(f"   [{i+5:2d}] {word:20s} strength={strength:.3f}{marker}")
    
    # Combat concept analysis
    if analysis['combat_in_top_20']:
        print(f"\n⚠️ COMBAT CONCEPTS IN TOP 20 (inflated by game outcomes):")
        for idx, word, strength in analysis['combat_in_top_20']:
            print(f"   Position {idx+1}: '{word}' (strength={strength:.3f})")
    else:
        print(f"\n✅ No combat concepts in top 20")
    
    # Bottom 20 concepts (lowest strength, highest token IDs - rarely sampled)
    print(f"\n📉 BOTTOM 20 CONCEPTS (high token IDs, rarely sampled):")
    for i, (word, strength) in enumerate(analysis['bottom_20_by_strength']):
        print(f"   {word:20s} strength={strength:.3f}")
    
    return analysis


def main():
    """Main diagnostic entry point."""
    print("=" * 70)
    print("LANGUAGE COLLAPSE DIAGNOSTIC")
    print("Checking if game outcomes have collapsed vocabulary diversity")
    print("=" * 70)
    
    # Try to load from butterfly system
    try:
        from butterfly_system import ButterflyEngine
        engine = ButterflyEngine()
        
        # Try loading from checkpoint or existing state
        checkpoint_path = Path("checkpoints")
        state_files = list(checkpoint_path.glob("*.pt")) if checkpoint_path.exists() else []
        
        if state_files:
            print(f"\nFound {len(state_files)} checkpoint files")
            latest = max(state_files, key=lambda p: p.stat().st_mtime)
            print(f"Using latest: {latest}")
            # Note: You'd need to implement load logic
        
        # Check if engine has organisms
        if hasattr(engine, 'organisms') and engine.organisms:
            print(f"\nFound {len(engine.organisms)} organisms in ButterflyEngine")
            for org_id, organism in engine.organisms.items():
                diagnose_organism(organism, org_id)
        else:
            print("\n⚠️ No organisms loaded in ButterflyEngine")
            
    except ImportError as e:
        print(f"\n⚠️ Could not import ButterflyEngine: {e}")
    except Exception as e:
        print(f"\n⚠️ Error loading from ButterflyEngine: {e}")
    
    # Try to load from reality simulator
    try:
        from reality_simulator.neural import NeuralOrganism
        from reality_simulator.simulation import RealitySimulator
        
        # Try various ways to get organisms
        print("\nAttempting to load from RealitySimulator...")
        
        # Check for saved states
        state_path = Path("reality_state.json")
        if state_path.exists():
            print(f"Found {state_path}, but need to implement loading")
        
    except ImportError as e:
        print(f"\n⚠️ Could not import reality_simulator: {e}")
    except Exception as e:
        print(f"\n⚠️ Error loading from reality_simulator: {e}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("\nIf you see combat concepts (victory, attack, survive, etc.) in the")
    print("top 20, they are getting the lowest token IDs and will dominate output.")
    print("\nFIX OPTIONS:")
    print("1. Disable strength boosting in language_game_bridge.py learn_from_outcome()")
    print("2. Add strength decay/normalization to prevent runaway inflation")
    print("3. Change vocab sorting to NOT use strength, or randomize top positions")
    print("4. Increase repetition penalty in generate_tokens()")
    print("=" * 70)


if __name__ == "__main__":
    main()
