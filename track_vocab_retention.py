"""
Vocabulary Retention Tracker for Butterfly Chat

Extracts and displays vocabulary retention stats from context_memory.json
"""

import json
import os
from collections import Counter
from datetime import datetime

def main():
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'context_memory.json')
    
    if not os.path.exists(data_path):
        print(f"ERROR: Could not find {data_path}")
        return
    
    print(f"Loading context memory from {data_path}...")
    print(f"File size: {os.path.getsize(data_path) / 1024 / 1024:.2f} MB")
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            cm = json.load(f)
    except Exception as e:
        print(f"ERROR loading JSON: {e}")
        return
    
    print("Loaded successfully!\n")
    
    # Get node word associations (organism -> learned words)
    node_assocs = cm.get('node_word_associations', {})
    
    print("=" * 50)
    print("       VOCABULARY RETENTION STATS")
    print("=" * 50)
    print(f"Last updated: {cm.get('last_updated', 'unknown')}")
    print(f"Total organisms with vocab: {len(node_assocs)}")
    print()
    
    if not node_assocs:
        print("No vocabulary data found!")
        return
    
    # Calculate per-organism stats
    word_counts = []
    all_words = set()
    for org_id, words in node_assocs.items():
        word_counts.append(len(words))
        all_words.update(words)
    
    print(f"Unique words across all organisms: {len(all_words)}")
    print(f"Avg words per organism: {sum(word_counts)/len(word_counts):.1f}")
    print(f"Min words: {min(word_counts)}, Max words: {max(word_counts)}")
    print()
    
    # Top organisms by vocabulary size
    print("=" * 50)
    print("       TOP 10 ORGANISMS BY VOCAB SIZE")
    print("=" * 50)
    sorted_orgs = sorted(node_assocs.items(), key=lambda x: -len(x[1]))[:10]
    for i, (org_id, words) in enumerate(sorted_orgs, 1):
        print(f"{i:2}. {org_id[:20]:20} : {len(words):3} words")
    print()
    
    # Most common words (appear in most organisms)
    word_appearances = Counter()
    for words in node_assocs.values():
        for w in words:
            word_appearances[w] += 1
    
    print("=" * 50)
    print("       TOP 20 MOST RETAINED WORDS")
    print("=" * 50)
    print(f"{'Word':<25} {'Orgs':>6} {'Retention':>10}")
    print("-" * 45)
    for word, count in word_appearances.most_common(20):
        pct = count / len(node_assocs) * 100
        print(f"{word:<25} {count:>6} {pct:>9.0f}%")
    print()
    
    # Show least retained words (rare vocabulary)
    print("=" * 50)
    print("       LEAST RETAINED (RARE) WORDS")
    print("=" * 50)
    rare_words = word_appearances.most_common()[-10:]
    for word, count in reversed(rare_words):
        pct = count / len(node_assocs) * 100
        print(f"{word:<25} {count:>6} {pct:>9.1f}%")
    
    print()
    print("=" * 50)
    print("       VOCABULARY CATEGORIES")
    print("=" * 50)
    
    # Categorize words
    action_words = {'move', 'rest', 'compete', 'cooperate', 'reproduce', 'isolate', 
                    'explore', 'travel', 'fight', 'search', 'wander', 'journey',
                    'withdraw', 'retreat', 'challenge', 'share', 'assist', 'help',
                    'collaborate', 'rival', 'pause', 'sleep', 'recover', 'wait'}
    
    state_words = {'alone', 'isolated', 'lone', 'only', 'sole', 'separated', 'strong'}
    
    outcome_words = {'succeed', 'prosper', 'flourish', 'thrive', 'grow', 'expand',
                     'spread', 'excel', 'multiply', 'deliver the goods', 'conflict'}
    
    action_retained = sum(1 for w in all_words if w in action_words)
    state_retained = sum(1 for w in all_words if w in state_words)
    outcome_retained = sum(1 for w in all_words if w in outcome_words)
    
    print(f"Action words retained: {action_retained}/{len(action_words)} ({action_retained/len(action_words)*100:.0f}%)")
    print(f"State words retained:  {state_retained}/{len(state_words)} ({state_retained/len(state_words)*100:.0f}%)")
    print(f"Outcome words retained: {outcome_retained}/{len(outcome_words)} ({outcome_retained/len(outcome_words)*100:.0f}%)")

if __name__ == '__main__':
    main()
