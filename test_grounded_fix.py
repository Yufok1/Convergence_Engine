"""
Test that grounded mode organisms stay at 6 words (ACTION_HEADS only)
and don't acquire new words through association formation.
"""
import sys
import os

# Direct import to avoid broken import chain (Ray/arrow conflict)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "atomic_language", 
    os.path.join(os.path.dirname(__file__), "reality_simulator", "language", "atomic_language.py")
)
atomic_language_module = importlib.util.module_from_spec(spec)
sys.modules['atomic_language'] = atomic_language_module
spec.loader.exec_module(atomic_language_module)
AtomicLanguageSystem = atomic_language_module.AtomicLanguageSystem

import json

# Load actual config 
with open('config.json', 'r') as f:
    config = json.load(f)

# Ensure grounded mode with level 0
config['language'] = config.get('language', {})
config['language']['grounded'] = config['language'].get('grounded', {})
config['language']['grounded']['initial_mastery_level'] = 0

print("=" * 60)
print("TEST: Grounded Mode Vocabulary Enforcement")
print("=" * 60)

# Create level 0 organism (grounded mode) - use named parameter!
als = AtomicLanguageSystem('test_org', config=config)

print(f"\n1. Initial state:")
print(f"   Atoms count: {len(als.atoms)}")
print(f"   Atoms: {list(als.atoms.keys())}")
print(f"   Mastery level: {als._mastery_level}")

# Simulate multiple experiences with different actions
context = {'vp_state': (0.7, 0.6)}

print(f"\n2. Applying 60 experiences (10 per action type)...")
for _ in range(10):
    for action in range(6):
        als.apply_experience(action=action, outcome=0.5, context=context)

print(f"\n3. After experiences:")
print(f"   Atoms count: {len(als.atoms)}")
print(f"   Atoms: {list(als.atoms.keys())}")
print(f"   Total experiences: {als._total_experiences}")
print(f"   Total associations: {als.total_associations_formed}")

# Check associations for each action head
print(f"\n4. Associations per action head:")
for action in ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']:
    if action in als.atoms:
        assocs = list(als.atoms[action].associations.keys())
        print(f"   {action}: {assocs}")

# Verify test
expected_atoms = {'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'}
actual_atoms = set(als.atoms.keys())

print(f"\n{'=' * 60}")
if actual_atoms == expected_atoms:
    print("✅ SUCCESS: Vocabulary stayed at exactly 6 ACTION_HEADS!")
    print("   No implicit word acquisition through associations.")
else:
    extra = actual_atoms - expected_atoms
    print(f"❌ FAILURE: Extra atoms acquired: {extra}")
    print(f"   Expected 6, got {len(actual_atoms)}")

print(f"\n5. Associations formed: {als.total_associations_formed}")
if als.total_associations_formed > 0:
    print("✅ Associations formed between existing atoms only (good!)")
else:
    print("⚠️  No associations formed (may need more experiences)")

print("=" * 60)
