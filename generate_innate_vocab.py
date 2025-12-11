#!/usr/bin/env python3
"""
Generate Innate Vocab - Converts nuclear_vocab.json into innate vocabulary format.

This script:
1. Loads nuclear_vocab.json (curated high-density verbs)
2. Generates VP affinities based on semantic categories
3. Assigns semantic frames based on category
4. Outputs data/innate_vocab.json for AtomicLanguageSystem to load

The innate vocab becomes what organisms are BORN knowing.
Environmental vocab (expanded_knowledge_web.json) is what they LEARN.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import random

PROJECT_ROOT = Path(__file__).parent
NUCLEAR_VOCAB = PROJECT_ROOT / "data" / "nuclear_vocab.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "innate_vocab.json"

# Category to semantic frame mapping
CATEGORY_TO_FRAME = {
    # Action categories
    'AERIAL': 'action', 'AQUATIC': 'action', 'TERRESTRIAL': 'action',
    'TERRESTRIAL BIPEDAL': 'action', 'MANIPULATION': 'action', 'GRASPING': 'action',
    'EATING': 'action', 'DRINKING': 'action', 'BREATHING': 'action',
    'CREATING': 'action', 'BUILDING': 'action', 'PRODUCING': 'action',
    'AGGRESSIVE': 'action', 'DEFENSIVE': 'action', 'EVASIVE': 'action',
    'EVASIVE/DIRECTIONAL': 'action', 'HUNTING': 'action', 'PURSUING': 'action',
    'FORCING': 'action', 'ENABLING': 'action', 'PREVENTING': 'action',
    'EXTRACTING': 'action', 'DEPLETING': 'action', 'ABSORBING': 'action',
    'METABOLIZING': 'action', 'EMITTING': 'action', 'TRANSFORMING': 'action',
    
    # Cognitive categories
    'COGNITIVE': 'cognitive', 'THINKING': 'cognitive', 'REASONING': 'cognitive',
    'LEARNING': 'cognitive', 'MEMORY': 'cognitive', 'FORGETTING': 'cognitive',
    'REMEMBERING': 'cognitive', 'DECIDING': 'cognitive', 'PLANNING': 'cognitive',
    'ANALYZING': 'cognitive', 'ATTENTION': 'cognitive', 'DETECTION': 'cognitive',
    
    # Perception categories
    'PERCEPTION': 'perception', 'VISUAL': 'perception', 'AUDITORY': 'perception',
    'TACTILE': 'perception', 'OLFACTORY': 'perception', 'GUSTATORY': 'perception',
    
    # Social categories
    'SOCIAL': 'relationship', 'AFFILIATIVE': 'relationship', 'COOPERATIVE': 'relationship',
    'COMPETITIVE': 'relationship', 'VERBAL': 'communication', 'EXPRESSING': 'communication',
    'COMMUNICATING': 'communication', 'DECEPTIVE': 'relationship', 'HIERARCHY': 'relationship',
    
    # State categories
    'STATE': 'state', 'IMPROVEMENT': 'quality', 'DETERIORATION': 'quality',
    'TRANSFORMATION': 'state', 'QUALITY': 'quality', 'CONDITION': 'state',
    'LIFECYCLE': 'state', 'DEVELOPMENT': 'state',
    
    # Temporal/Causal
    'TEMPORAL': 'temporal', 'TIMING': 'temporal', 'SEQUENCING': 'temporal',
    'CAUSAL': 'causal', 'CAUSATION': 'causal', 'INFLUENCING': 'causal',
    'RESULTING': 'causal',
    
    # Resource
    'RESOURCE': 'resource', 'CONSUMPTION': 'resource',
}

# VP (Vitality-Pleasure) mapping by semantic frame and category
def get_vp_affinity(word: str, categories: List[str], frame: str) -> Tuple[float, float]:
    """
    Assign VP affinities based on semantic meaning.
    
    Vitality: 0=low energy, 1=high energy
    Pleasure: 0=negative valence, 1=positive valence
    """
    word_lower = word.lower()
    
    # Specific word overrides
    VP_OVERRIDES = {
        # High vitality, high pleasure (positive action)
        'create': (0.8, 0.8), 'build': (0.7, 0.7), 'grow': (0.7, 0.8),
        'help': (0.6, 0.8), 'share': (0.5, 0.8), 'cooperate': (0.6, 0.8),
        'succeed': (0.8, 0.9), 'thrive': (0.8, 0.9), 'flourish': (0.8, 0.9),
        
        # High vitality, low pleasure (aggressive/threatening)
        'attack': (0.9, 0.2), 'fight': (0.9, 0.3), 'destroy': (0.8, 0.2),
        'force': (0.8, 0.3), 'crush': (0.9, 0.2), 'dominate': (0.8, 0.3),
        'chase': (0.8, 0.4), 'hunt': (0.8, 0.4), 'pursue': (0.7, 0.4),
        
        # Low vitality, low pleasure (negative states)
        'fail': (0.3, 0.2), 'die': (0.1, 0.1), 'suffer': (0.3, 0.1),
        'weaken': (0.2, 0.3), 'decay': (0.2, 0.2), 'collapse': (0.2, 0.2),
        'abandon': (0.3, 0.2), 'neglect': (0.2, 0.3), 'ignore': (0.2, 0.3),
        
        # Low vitality, high pleasure (rest/calm)
        'rest': (0.2, 0.7), 'relax': (0.2, 0.8), 'sleep': (0.1, 0.7),
        'calm': (0.3, 0.7), 'peace': (0.3, 0.8), 'settle': (0.3, 0.6),
        
        # Neutral/balanced
        'move': (0.5, 0.5), 'change': (0.5, 0.5), 'wait': (0.3, 0.5),
        'observe': (0.4, 0.5), 'watch': (0.4, 0.5), 'think': (0.4, 0.5),
    }
    
    if word_lower in VP_OVERRIDES:
        return VP_OVERRIDES[word_lower]
    
    # Frame-based defaults with noise
    base_vp = {
        'action': (0.6, 0.5),
        'cognitive': (0.4, 0.5),
        'perception': (0.4, 0.5),
        'relationship': (0.5, 0.6),
        'communication': (0.5, 0.6),
        'state': (0.4, 0.5),
        'quality': (0.5, 0.5),
        'temporal': (0.5, 0.5),
        'causal': (0.5, 0.5),
        'resource': (0.5, 0.6),
        'spatial': (0.5, 0.5),
        'unknown': (0.5, 0.5),
    }
    
    v, p = base_vp.get(frame, (0.5, 0.5))
    
    # Category modifiers
    for cat in categories:
        cat_upper = cat.upper()
        if cat_upper in ['AGGRESSIVE', 'FORCING', 'HUNTING', 'ATTACKING']:
            v += 0.2
            p -= 0.2
        elif cat_upper in ['AFFILIATIVE', 'COOPERATIVE', 'CREATING']:
            p += 0.15
        elif cat_upper in ['DETERIORATION', 'DEPLETING', 'FORGETTING']:
            v -= 0.1
            p -= 0.15
        elif cat_upper in ['IMPROVEMENT', 'LEARNING', 'REMEMBERING']:
            p += 0.1
    
    # Clamp and add noise
    v = max(0.1, min(0.9, v + random.uniform(-0.05, 0.05)))
    p = max(0.1, min(0.9, p + random.uniform(-0.05, 0.05)))
    
    return (round(v, 2), round(p, 2))


def get_frame(categories: List[str]) -> str:
    """Get semantic frame from categories."""
    for cat in categories:
        cat_upper = cat.upper()
        if cat_upper in CATEGORY_TO_FRAME:
            return CATEGORY_TO_FRAME[cat_upper]
    return 'action'  # Default for verbs


def convert_nuclear_to_innate(nuclear: dict) -> dict:
    """Convert nuclear vocab format to innate vocab format."""
    
    concepts = {}
    associations = []
    
    # Process concepts
    for c in nuclear.get('concepts', []):
        word = c.get('word', '').lower()
        if not word or len(word) < 2:
            continue
            
        categories = c.get('categories', [])
        frame = get_frame(categories)
        vp = get_vp_affinity(word, categories, frame)
        
        # Determine abstraction level based on connections
        conn = c.get('connections', 0)
        level = 0 if conn < 10 else (1 if conn < 30 else 2)
        
        concepts[word] = {
            'frame': frame,
            'level': level,
            'vp': vp,
            'nuclear_score': c.get('nuclear_score', 0),
            'categories': categories
        }
    
    # Process relations into associations
    for r in nuclear.get('relations', []):
        src = r.get('source', '').lower()
        tgt = r.get('target', '').lower()
        rtype = r.get('relation_type', '')
        strength = r.get('strength', 0.5)
        
        if src in concepts and tgt in concepts:
            associations.append({
                'source': src,
                'target': tgt,
                'strength': strength,
                'relation_type': rtype
            })
    
    # Build tiered structure for initialization
    # Tier 1: Core innate (top 50 by nuclear score) - all organisms get these
    # Tier 2: Extended innate (next 200) - organisms get random subset
    # Tier 3: Full pool (remaining) - rare random additions
    
    ranked = sorted(concepts.keys(), key=lambda w: concepts[w]['nuclear_score'], reverse=True)
    
    tier1 = ranked[:50]    # Core - everyone gets
    tier2 = ranked[50:250]  # Extended - random subset
    tier3 = ranked[250:]    # Pool - rare additions
    
    # Build association lookup for tiers
    assoc_by_word = {}
    for a in associations:
        src, tgt = a['source'], a['target']
        if src not in assoc_by_word:
            assoc_by_word[src] = []
        assoc_by_word[src].append(a)
    
    output = {
        'version': '1.0',
        'source': 'nuclear_vocab_extraction',
        'description': 'Innate vocabulary for organisms - curated high-density action verbs',
        'tiers': {
            'core': tier1,
            'extended': tier2,
            'pool': tier3
        },
        'tier_config': {
            'core_count': len(tier1),
            'extended_sample_range': [20, 50],  # Organisms get 20-50 from extended
            'pool_sample_range': [0, 10]        # Organisms get 0-10 from pool
        },
        'concepts': concepts,
        'associations': associations,
        'stats': {
            'total_concepts': len(concepts),
            'total_associations': len(associations),
            'tier1_count': len(tier1),
            'tier2_count': len(tier2),
            'tier3_count': len(tier3)
        }
    }
    
    return output


def main():
    print("=" * 60)
    print("GENERATE INNATE VOCAB")
    print("=" * 60)
    
    # Load nuclear vocab
    print(f"\nLoading nuclear vocab from {NUCLEAR_VOCAB}...")
    with open(NUCLEAR_VOCAB, 'r', encoding='utf-8') as f:
        nuclear = json.load(f)
    
    print(f"  Concepts: {len(nuclear.get('concepts', []))}")
    print(f"  Relations: {len(nuclear.get('relations', []))}")
    
    # Convert
    print("\nConverting to innate format...")
    innate = convert_nuclear_to_innate(nuclear)
    
    # Save
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(innate, f, indent=2, ensure_ascii=False)
    
    # Stats
    print("\n" + "=" * 60)
    print("INNATE VOCAB GENERATED")
    print("=" * 60)
    print(f"\nTotal Concepts: {innate['stats']['total_concepts']}")
    print(f"Total Associations: {innate['stats']['total_associations']}")
    print(f"\nTier Structure:")
    print(f"  Core (all organisms): {innate['stats']['tier1_count']} words")
    print(f"  Extended (random 20-50): {innate['stats']['tier2_count']} words")
    print(f"  Pool (random 0-10): {innate['stats']['tier3_count']} words")
    
    print(f"\nTop 10 Core Words:")
    for i, word in enumerate(innate['tiers']['core'][:10], 1):
        c = innate['concepts'][word]
        print(f"  {i}. {word}: score={c['nuclear_score']:.0f}, frame={c['frame']}, vp={c['vp']}")
    
    return innate


if __name__ == '__main__':
    main()
