#!/usr/bin/env python3
"""
Verify Innate Vocab Integration - Comprehensive test of the nuclear vocab system.

Tests:
1. innate_vocab.json data integrity
2. atomic_language.py loading and caching
3. Association wiring between concepts
4. VP affinity population
5. language_teacher.py compatibility
6. Full organism creation path
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_innate_vocab_integrity():
    """Test 1: Verify innate_vocab.json structure and data."""
    print("=" * 60)
    print("TEST 1: innate_vocab.json INTEGRITY")
    print("=" * 60)
    
    path = PROJECT_ROOT / "data" / "innate_vocab.json"
    with open(path, 'r', encoding='utf-8') as f:
        iv = json.load(f)
    
    errors = []
    
    # Required keys
    required_keys = ['version', 'tiers', 'tier_config', 'concepts', 'associations']
    for key in required_keys:
        if key not in iv:
            errors.append(f"Missing required key: {key}")
    
    print(f"Top-level keys: {list(iv.keys())}")
    
    # Tier structure
    tiers = iv.get('tiers', {})
    core = tiers.get('core', [])
    extended = tiers.get('extended', [])
    pool = tiers.get('pool', [])
    
    print(f"Tiers: core={len(core)}, extended={len(extended)}, pool={len(pool)}")
    
    if len(core) < 10:
        errors.append(f"Core tier too small: {len(core)}")
    
    # Concepts validation
    concepts = iv.get('concepts', {})
    print(f"Total concepts: {len(concepts)}")
    
    missing_frame = 0
    missing_vp = 0
    invalid_vp = 0
    
    for word, info in concepts.items():
        if 'frame' not in info:
            missing_frame += 1
        if 'vp' not in info:
            missing_vp += 1
        else:
            vp = info['vp']
            if not isinstance(vp, (list, tuple)) or len(vp) != 2:
                invalid_vp += 1
            elif not (0 <= vp[0] <= 1 and 0 <= vp[1] <= 1):
                invalid_vp += 1
    
    print(f"Missing frame: {missing_frame}")
    print(f"Missing VP: {missing_vp}")
    print(f"Invalid VP: {invalid_vp}")
    
    if missing_frame > 0:
        errors.append(f"{missing_frame} concepts missing frame")
    if missing_vp > 0:
        errors.append(f"{missing_vp} concepts missing vp")
    if invalid_vp > 0:
        errors.append(f"{invalid_vp} concepts with invalid vp values")
    
    # Associations validation
    associations = iv.get('associations', [])
    print(f"Total associations: {len(associations)}")
    
    orphan_count = 0
    for a in associations:
        src = a.get('source', '')
        tgt = a.get('target', '')
        if src not in concepts or tgt not in concepts:
            orphan_count += 1
    
    print(f"Orphan associations: {orphan_count}")
    if orphan_count > 0:
        errors.append(f"{orphan_count} associations reference non-existent concepts")
    
    # Tier coverage
    all_tier_words = set(core + extended + pool)
    if all_tier_words != set(concepts.keys()):
        diff = set(concepts.keys()) - all_tier_words
        errors.append(f"{len(diff)} concepts not in any tier")
    
    if errors:
        print(f"\n❌ ERRORS: {errors}")
        return False
    else:
        print(f"\n✓ innate_vocab.json integrity verified")
        return True


def test_atomic_language_loading():
    """Test 2: Verify AtomicLanguageSystem loads innate vocab correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: AtomicLanguageSystem LOADING")
    print("=" * 60)
    
    from reality_simulator.language.atomic_language import AtomicLanguageSystem
    import numpy as np
    
    errors = []
    
    # Test cache loading
    cache = AtomicLanguageSystem._load_innate_vocab()
    if cache is None:
        errors.append("Failed to load innate vocab cache")
        print("❌ Cache load failed")
        return False
    
    print(f"✓ Cache loaded: {len(cache.get('concepts', {}))} concepts")
    
    # Test organism creation
    np.random.seed(123)
    als = AtomicLanguageSystem("test_verify_1")
    
    print(f"Organism atoms: {len(als.atoms)}")
    
    if len(als.atoms) < 50:
        errors.append(f"Too few atoms: {len(als.atoms)}")
    
    # Check source distribution
    sources = {}
    for word, atom in als.atoms.items():
        sources[atom.source] = sources.get(atom.source, 0) + 1
    
    print(f"Sources: {sources}")
    
    if 'innate_core' not in sources:
        errors.append("No innate_core atoms found")
    elif sources['innate_core'] != 50:
        errors.append(f"Expected 50 core atoms, got {sources['innate_core']}")
    
    if errors:
        print(f"\n❌ ERRORS: {errors}")
        return False
    else:
        print(f"\n✓ AtomicLanguageSystem loading verified")
        return True


def test_associations_wired():
    """Test 3: Verify associations are actually formed between concepts."""
    print("\n" + "=" * 60)
    print("TEST 3: ASSOCIATIONS WIRING")
    print("=" * 60)
    
    from reality_simulator.language.atomic_language import AtomicLanguageSystem
    import numpy as np
    
    errors = []
    
    np.random.seed(456)
    als = AtomicLanguageSystem("test_verify_2")
    
    # Count total associations
    total_assocs = 0
    words_with_assocs = 0
    
    for word, atom in als.atoms.items():
        n_assocs = len(atom.associations)
        total_assocs += n_assocs
        if n_assocs > 0:
            words_with_assocs += 1
    
    print(f"Total associations formed: {total_assocs}")
    print(f"Words with associations: {words_with_assocs}/{len(als.atoms)}")
    
    if total_assocs == 0:
        errors.append("No associations were formed!")
    
    if words_with_assocs == 0:
        errors.append("No words have associations!")
    
    # Check specific associations
    sample_words = ['ignore', 'force', 'stop', 'release']
    print(f"\nSample associations:")
    for word in sample_words:
        if word in als.atoms:
            atom = als.atoms[word]
            assoc_targets = list(atom.associations.keys())[:5]
            print(f"  {word}: {assoc_targets}")
    
    if errors:
        print(f"\n❌ ERRORS: {errors}")
        return False
    else:
        print(f"\n✓ Associations wiring verified")
        return True


def test_vp_affinities():
    """Test 4: Verify VP affinities are populated correctly."""
    print("\n" + "=" * 60)
    print("TEST 4: VP AFFINITIES")
    print("=" * 60)
    
    from reality_simulator.language.atomic_language import AtomicLanguageSystem
    import numpy as np
    
    errors = []
    
    np.random.seed(789)
    als = AtomicLanguageSystem("test_verify_3")
    
    invalid_vitality = 0
    invalid_pleasure = 0
    
    for word, atom in als.atoms.items():
        v = atom.vp_vitality_affinity
        p = atom.vp_pleasure_affinity
        
        if v is None or not (0 <= v <= 1):
            invalid_vitality += 1
        if p is None or not (0 <= p <= 1):
            invalid_pleasure += 1
    
    print(f"Invalid vitality: {invalid_vitality}")
    print(f"Invalid pleasure: {invalid_pleasure}")
    
    if invalid_vitality > 0:
        errors.append(f"{invalid_vitality} atoms have invalid vitality affinity")
    if invalid_pleasure > 0:
        errors.append(f"{invalid_pleasure} atoms have invalid pleasure affinity")
    
    # Sample VP values
    print(f"\nSample VP values:")
    for word in ['force', 'rest', 'attack', 'cooperate', 'ignore']:
        if word in als.atoms:
            atom = als.atoms[word]
            print(f"  {word}: vitality={atom.vp_vitality_affinity:.2f}, pleasure={atom.vp_pleasure_affinity:.2f}")
    
    if errors:
        print(f"\n❌ ERRORS: {errors}")
        return False
    else:
        print(f"\n✓ VP affinities verified")
        return True


def test_variation_between_organisms():
    """Test 5: Verify organisms get different vocabularies."""
    print("\n" + "=" * 60)
    print("TEST 5: VOCABULARY VARIATION")
    print("=" * 60)
    
    from reality_simulator.language.atomic_language import AtomicLanguageSystem
    import numpy as np
    
    errors = []
    
    # Create multiple organisms
    organisms = []
    for i in range(5):
        np.random.seed(i * 1000)  # Different seeds
        als = AtomicLanguageSystem(f"test_var_{i}")
        organisms.append(set(als.atoms.keys()))
    
    # Check for variation
    all_same = all(orgs == organisms[0] for orgs in organisms)
    
    print(f"Organism vocab sizes: {[len(o) for o in organisms]}")
    
    # Count unique vocabs
    unique_vocabs = len(set(frozenset(o) for o in organisms))
    print(f"Unique vocabularies: {unique_vocabs}/5")
    
    if all_same:
        errors.append("All organisms have identical vocabularies!")
    
    # Check core overlap (should be 100%)
    core_words = set()
    with open(PROJECT_ROOT / "data" / "innate_vocab.json") as f:
        iv = json.load(f)
        core_words = set(iv.get('tiers', {}).get('core', []))
    
    for i, org in enumerate(organisms):
        core_in_org = core_words & org
        if len(core_in_org) != len(core_words):
            errors.append(f"Organism {i} missing core words: {len(core_in_org)}/{len(core_words)}")
    
    print(f"Core words in all organisms: {len(core_words)}")
    
    if errors:
        print(f"\n❌ ERRORS: {errors}")
        return False
    else:
        print(f"\n✓ Vocabulary variation verified")
        return True


def test_agent_compiler_compatibility():
    """Test 6: Check agent_compiler.py doesn't conflict."""
    print("\n" + "=" * 60)
    print("TEST 6: AGENT_COMPILER COMPATIBILITY")
    print("=" * 60)
    
    errors = []
    
    # Check if agent_compiler has its own INNATE_CONCEPTS
    ac_path = PROJECT_ROOT / "reality_simulator" / "agent_compiler.py"
    if ac_path.exists():
        with open(ac_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'INNATE_CONCEPTS' in content:
            print("⚠ agent_compiler.py has its own INNATE_CONCEPTS")
            # Check if it's in a class that might conflict
            if 'class' in content and 'INNATE_CONCEPTS' in content:
                print("  Note: May need to update agent_compiler.py to use new system")
        else:
            print("✓ No INNATE_CONCEPTS in agent_compiler.py")
    else:
        print("agent_compiler.py not found at expected path")
    
    print(f"\n✓ Agent compiler check complete")
    return True


def main():
    print("=" * 60)
    print("INNATE VOCAB INTEGRATION VERIFICATION")
    print("=" * 60)
    
    results = []
    
    results.append(("innate_vocab.json integrity", test_innate_vocab_integrity()))
    results.append(("AtomicLanguageSystem loading", test_atomic_language_loading()))
    results.append(("Associations wiring", test_associations_wired()))
    results.append(("VP affinities", test_vp_affinities()))
    results.append(("Vocabulary variation", test_variation_between_organisms()))
    results.append(("Agent compiler compatibility", test_agent_compiler_compatibility()))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATION TESTS PASSED")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED - Review above for details")
        return 1


if __name__ == '__main__':
    sys.exit(main())
