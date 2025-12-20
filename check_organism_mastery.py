"""
Quick check of live organism mastery state via web API
"""
import requests
import json

try:
    resp = requests.get('http://localhost:5000/api/organisms', timeout=5)
    orgs = resp.json()  # It's a list, not a dict
    
    print(f"\n{'='*70}")
    print(f"ORGANISM MASTERY CHECK ({len(orgs)} organisms)")
    print(f"{'='*70}")
    
    # Group by mastery level
    by_level = {}
    violations = []
    
    for org in orgs:
        level = org.get('mastery_level', 0)
        vocab_cap = org.get('mastery_vocab_limit', 6)
        atoms = org.get('vocabulary_size', vocab_cap)  # May not be in API
        
        if level not in by_level:
            by_level[level] = []
        by_level[level].append((org.get('id', '?')[:8], atoms, vocab_cap))
        
        # Check for violations
        if atoms > vocab_cap:
            violations.append((org.get('id', '?')[:8], level, atoms, vocab_cap))
    
    # Print summary
    for level in sorted(by_level.keys()):
        orgs_at_level = by_level[level]
        vocab_cap = [6, 26, 76, 276, 20000][min(level, 4)]
        atom_counts = [a for _, a, _ in orgs_at_level]
        print(f"\nLevel {level} (cap={vocab_cap}): {len(orgs_at_level)} organisms")
        print(f"  Atom counts: min={min(atom_counts)}, max={max(atom_counts)}, avg={sum(atom_counts)/len(atom_counts):.1f}")
        if max(atom_counts) > vocab_cap:
            print(f"  ⚠️  VIOLATION: {max(atom_counts)} > {vocab_cap}")
    
    if violations:
        print(f"\n{'='*70}")
        print(f"⚠️  VOCAB CAP VIOLATIONS:")
        print(f"{'='*70}")
        for org_id, level, atoms, cap in violations:
            print(f"  {org_id}: Level {level}, {atoms}/{cap} atoms")
    else:
        print(f"\n✅ No vocab cap violations detected")
    
    # Show experience counts for a sample
    print(f"\n{'='*70}")
    print(f"SAMPLE ORGANISM DETAILS (first 5)")
    print(f"{'='*70}")
    for org in orgs[:5]:
        print(f"\n  {org.get('id', '?')[:8]}:")
        print(f"    Mastery: {org.get('mastery_level', '?')}")
        print(f"    Vocab Limit: {org.get('mastery_vocab_limit', '?')}")
        print(f"    Vocab Size: {org.get('vocabulary_size', 'N/A')}")
        print(f"    Experiences: {org.get('experience_buffer_size', '?')}")
        print(f"    Age: {org.get('age', '?')}")
        print(f"    Fitness: {org.get('fitness', '?'):.3f}")

except Exception as e:
    print(f"Error: {e}")
    print("Make sure the system is running with web UI at localhost:5000")
