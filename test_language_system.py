#!/usr/bin/env python3
"""
Test the new innate language system integration.
Run before GitHub push to verify everything works.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_language_system():
    print('=== LANGUAGE SYSTEM INTEGRATION TEST ===')
    print()
    errors = []

    # Test 1: AtomicLanguageSystem import
    print('1. Testing AtomicLanguageSystem import...')
    try:
        from reality_simulator.language.atomic_language import AtomicLanguageSystem, LinguisticAtom
        print('   OK')
    except Exception as e:
        errors.append(f"Import failed: {e}")
        print(f'   FAILED: {e}')
        return False

    # Test 2: Create organism with innate vocab
    print('2. Creating organism with innate vocabulary...')
    try:
        import numpy as np
        np.random.seed(12345)
        als = AtomicLanguageSystem('test_organism')
        
        core_count = sum(1 for a in als.atoms.values() if a.source == 'innate_core')
        ext_count = sum(1 for a in als.atoms.values() if a.source == 'innate_extended')
        
        print(f'   Total atoms: {len(als.atoms)}')
        print(f'   Core: {core_count}')
        print(f'   Extended: {ext_count}')
        
        if len(als.atoms) < 50:
            errors.append(f"Too few atoms: {len(als.atoms)}")
        if core_count != 50:
            errors.append(f"Expected 50 core, got {core_count}")
    except Exception as e:
        errors.append(f"Organism creation failed: {e}")
        print(f'   FAILED: {e}')

    # Test 3: Check associations
    print('3. Testing associations...')
    try:
        total_assocs = sum(len(a.associations) for a in als.atoms.values())
        print(f'   Total associations: {total_assocs}')
        if total_assocs == 0:
            errors.append("No associations formed")
    except Exception as e:
        errors.append(f"Association check failed: {e}")

    # Test 4: VP-based concept activation
    print('4. Testing VP-based concept activation...')
    try:
        vp = (0.8, 0.3)  # High vitality, low pleasure (combat/aggression)
        scored = []
        for word, atom in als.atoms.items():
            v_match = 1 - abs(vp[0] - atom.vp_vitality_affinity)
            p_match = 1 - abs(vp[1] - atom.vp_pleasure_affinity)
            score = atom.strength * (v_match + p_match) / 2
            scored.append((word, round(score, 3)))
        top5 = sorted(scored, key=lambda x: -x[1])[:5]
        print(f'   Top concepts for (V=0.8, P=0.3): {[c[0] for c in top5]}')
    except Exception as e:
        errors.append(f"VP activation failed: {e}")

    # Test 5: Tensor conversion
    print('5. Testing tensor conversion...')
    try:
        if hasattr(als, 'to_tensor'):
            tensor = als.to_tensor(dim=64)
            print(f'   Tensor shape: {tensor.shape}')
        else:
            print('   to_tensor not available (OK)')
    except Exception as e:
        print(f'   Warning: {e}')

    # Test 6: Concept acquisition
    print('6. Testing concept acquisition...')
    try:
        old_count = len(als.atoms)
        new_atom = als.acquire_concept('newword', source='learned', semantic_frame='action')
        print(f'   New atom: {new_atom.concept_id}, source={new_atom.source}')
        print(f'   Total atoms: {old_count} -> {len(als.atoms)}')
        if len(als.atoms) != old_count + 1:
            errors.append("Concept acquisition didn't add atom")
    except Exception as e:
        errors.append(f"Concept acquisition failed: {e}")

    # Test 7: Multiple organisms have different vocabs
    print('7. Testing vocabulary variation...')
    try:
        vocabs = []
        for i in range(3):
            np.random.seed(i * 999)
            test_als = AtomicLanguageSystem(f'test_{i}')
            vocabs.append(set(test_als.atoms.keys()))
        
        all_same = vocabs[0] == vocabs[1] == vocabs[2]
        print(f'   Sizes: {[len(v) for v in vocabs]}')
        print(f'   All different: {not all_same}')
        if all_same:
            errors.append("All organisms have identical vocab")
    except Exception as e:
        errors.append(f"Variation test failed: {e}")

    # Summary
    print()
    print('=' * 50)
    if errors:
        print(f'FAILED - {len(errors)} errors:')
        for e in errors:
            print(f'  - {e}')
        return False
    else:
        print('ALL TESTS PASSED')
        return True


if __name__ == '__main__':
    success = test_language_system()
    sys.exit(0 if success else 1)
