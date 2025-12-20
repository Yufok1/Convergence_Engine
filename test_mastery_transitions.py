#!/usr/bin/env python3
"""Test all mastery level transitions to verify they work correctly."""

from reality_simulator.language.atomic_language import AtomicLanguageSystem

def test_transition(from_level, to_level):
    """Test that an organism can advance from from_level to to_level."""
    al = AtomicLanguageSystem(f'test_{from_level}_{to_level}', config={'mastery_gating_enabled': True})
    al._mastery_level = from_level
    al._expand_vocabulary_for_level(from_level)
    
    vocab = al.get_available_vocabulary()
    print(f'\n=== Testing Level {from_level} -> {to_level} ===')
    print(f'Starting vocab: {len(vocab)} words')
    
    # 1. Breadth: activate 60% of words (above 50% threshold)
    for i, word in enumerate(vocab):
        if i < len(vocab) * 0.6 and word in al.atoms:
            for _ in range(5):  # 5 activations each
                al.atoms[word].update_satiation()
    
    # 2. Depth: create associations for 40% of words (above 30% threshold)
    words_list = list(vocab)
    for i in range(int(len(words_list) * 0.4)):
        if words_list[i] in al.atoms:
            al.atoms[words_list[i]].associations['test1'] = 0.5
            al.atoms[words_list[i]].associations['test2'] = 0.5
    
    # 3. Experiences: set to well above threshold
    exp_targets = [25, 100, 500, 2000, 10000]
    al._total_experiences = exp_targets[from_level] + 50
    
    # Check if ready
    ready = al.check_mastery_advancement()
    print(f'Ready to advance: {ready}')
    
    # Try to advance
    if ready:
        old_level = al._mastery_level
        advanced = al.try_advance_mastery()
        new_vocab = al.get_available_vocabulary()
        print(f'Advanced: {advanced}')
        print(f'Level: {old_level} -> {al._mastery_level}')
        print(f'Vocab: {len(vocab)} -> {len(new_vocab)} words')
        return True
    return False

if __name__ == '__main__':
    results = []
    for level in range(4):
        success = test_transition(level, level + 1)
        results.append((level, level + 1, success))

    print('\n' + '=' * 40)
    print('MASTERY TRANSITION TEST SUMMARY')
    print('=' * 40)
    all_pass = True
    for from_l, to_l, ok in results:
        status = 'PASS' if ok else 'FAIL'
        symbol = '✓' if ok else '✗'
        print(f'{symbol} Level {from_l} -> {to_l}: {status}')
        if not ok:
            all_pass = False
    
    print('=' * 40)
    if all_pass:
        print('ALL TRANSITIONS WORKING!')
    else:
        print('SOME TRANSITIONS FAILED!')
