"""
LIVE TEST: Mastery Gate Blocking
Shows actual values and behavior, not just PASSED/FAILED
"""
import json
from reality_simulator.language.atomic_language import AtomicLanguageSystem

config = json.load(open('config.json'))

print('='*60)
print('TEST 1: Level 0 organism initialization')
print('='*60)
als = AtomicLanguageSystem(organism_id='test', event_emitter=None, config=config)
print(f'Mastery Level: {als._mastery_level}')
print(f'Atom count: {len(als.atoms)}')
print(f'Atoms: {list(als.atoms.keys())}')
print(f'Vocab cap for level 0: {als._mastery_vocab_sizes[0]}')

print()
print('='*60)
print('TEST 2: Try to acquire external words (should be BLOCKED)')
print('='*60)
for source in ['battle_absorption', 'taught', 'chat_heard', 'alliance']:
    word = f'word_from_{source}'
    result = als.acquire_concept(word, source)
    status = 'BLOCKED' if result is None else 'ALLOWED'
    print(f'  acquire_concept("{word}", "{source}") -> {status}')
print(f'Atoms after attempts: {len(als.atoms)}')

print()
print('='*60)
print('TEST 3: Advance to Level 1 and check vocab expansion')
print('='*60)
als.mastery_level = 1
print(f'Mastery Level: {als._mastery_level}')
print(f'Atom count: {len(als.atoms)}')
print(f'Vocab cap for level 1: {als._mastery_vocab_sizes[1]}')
new_atoms = [a for a in als.atoms.keys() if a not in ['move','cooperate','compete','rest','reproduce','isolate']]
print(f'New atoms added ({len(new_atoms)}): {new_atoms[:10]}...')

print()
print('='*60)
print('TEST 4: Try to acquire beyond Level 1 cap (should be BLOCKED)')
print('='*60)
result = als.acquire_concept('extra_word_beyond_cap', 'external')
status = 'BLOCKED' if result is None else 'ALLOWED'
print(f'  acquire_concept("extra_word_beyond_cap", "external") -> {status}')
print(f'Atoms after attempt: {len(als.atoms)}')

print()
print('='*60)
print('TEST 5: Existing word should STRENGTHEN (not be blocked)')
print('='*60)
old_strength = als.atoms['move'].strength
result = als.acquire_concept('move', 'reinforcement')
status = 'STRENGTHENED' if result is not None else 'BLOCKED'
print(f'  acquire_concept("move", "reinforcement") -> {status}')
print(f'  Strength: {old_strength:.3f} -> {als.atoms["move"].strength:.3f}')

print()
print('='*60)
print('SUMMARY')
print('='*60)
print(f'Level 0 blocks external acquisition: {"YES" if len(als.atoms) == 26 else "NO - LEAK DETECTED"}')
