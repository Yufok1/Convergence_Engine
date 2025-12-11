#!/usr/bin/env python3
"""
Inject Nuclear Vocab - Merges nuclear_vocab.json into expanded_knowledge_web.json

This script:
1. Loads nuclear_vocab.json (merged extraction)
2. Loads expanded_knowledge_web.json (existing knowledge)
3. Merges new concepts and relations (deduped)
4. Outputs updated expanded_knowledge_web.json
5. Generates injection report

Run after merge_nuclear_vocab.py
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Paths
PROJECT_ROOT = Path(__file__).parent
NUCLEAR_VOCAB = PROJECT_ROOT / "data" / "nuclear_vocab.json"
KNOWLEDGE_WEB = PROJECT_ROOT / "data" / "expanded_knowledge_web.json"
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"


def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, filepath: Path):
    """Save JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def relation_key(r: dict) -> tuple:
    """Create unique key for a relation."""
    src = r.get('source', '').lower()
    tgt = r.get('target', '').lower()
    rtype = r.get('relation_type', '').lower()
    
    # For bidirectional relations, normalize order
    if rtype in ('synonym', 'antonym'):
        return tuple(sorted([src, tgt])) + (rtype,)
    return (src, tgt, rtype)


def merge_knowledge(nuclear: dict, existing: dict) -> Tuple[dict, dict]:
    """
    Merge nuclear vocab into existing knowledge web.
    
    Returns:
        merged: Updated knowledge web
        report: Statistics about the merge
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'nuclear_concepts': len(nuclear.get('concepts', [])),
        'nuclear_relations': len(nuclear.get('relations', [])),
        'existing_concepts': len(existing.get('concepts', [])),
        'existing_relations': len(existing.get('relations', [])),
        'new_concepts_added': 0,
        'new_relations_added': 0,
        'relations_updated': 0,
        'duplicates_skipped': 0
    }
    
    # Build existing concept set
    existing_concepts = set()
    for c in existing.get('concepts', []):
        word = c.get('word', c.get('name', '')).lower()
        if word:
            existing_concepts.add(word)
    
    # Build existing relation index
    existing_relations = {}
    for r in existing.get('relations', []):
        key = relation_key(r)
        existing_relations[key] = r
    
    print(f"Existing knowledge web: {len(existing_concepts)} concepts, {len(existing_relations)} relations")
    
    # Add new concepts from nuclear vocab
    new_concepts = []
    for c in nuclear.get('concepts', []):
        word = c.get('word', '').lower()
        if word and word not in existing_concepts:
            new_concepts.append({
                'word': word,
                'name': word,
                'source': 'nuclear_extraction'
            })
            existing_concepts.add(word)
            report['new_concepts_added'] += 1
    
    print(f"New concepts to add: {report['new_concepts_added']}")
    
    # Add new relations from nuclear vocab
    new_relations = []
    for r in nuclear.get('relations', []):
        key = relation_key(r)
        
        if key in existing_relations:
            # Check if we should update strength
            old = existing_relations[key]
            new_strength = r.get('strength', 0.5)
            old_strength = old.get('strength', 0.5)
            
            if new_strength > old_strength:
                old['strength'] = new_strength
                report['relations_updated'] += 1
            else:
                report['duplicates_skipped'] += 1
        else:
            # New relation
            new_rel = {
                'source': r['source'].lower(),
                'target': r['target'].lower(),
                'relation_type': r['relation_type'],
                'strength': r.get('strength', 0.8),
                'context': r.get('context', 'nuclear_extraction')
            }
            new_relations.append(new_rel)
            existing_relations[key] = new_rel
            report['new_relations_added'] += 1
    
    print(f"New relations to add: {report['new_relations_added']}")
    print(f"Relations updated: {report['relations_updated']}")
    print(f"Duplicates skipped: {report['duplicates_skipped']}")
    
    # Build merged output
    merged = {
        'concepts': existing.get('concepts', []) + new_concepts,
        'relations': existing.get('relations', []) + new_relations
    }
    
    report['final_concepts'] = len(merged['concepts'])
    report['final_relations'] = len(merged['relations'])
    
    return merged, report


def main():
    print("=" * 60)
    print("NUCLEAR VOCAB INJECTION")
    print("=" * 60)
    
    # Check files exist
    if not NUCLEAR_VOCAB.exists():
        print(f"ERROR: {NUCLEAR_VOCAB} not found. Run merge_nuclear_vocab.py first.")
        return
    
    if not KNOWLEDGE_WEB.exists():
        print(f"ERROR: {KNOWLEDGE_WEB} not found.")
        return
    
    # Load data
    print(f"\nLoading nuclear vocab from {NUCLEAR_VOCAB}...")
    nuclear = load_json(NUCLEAR_VOCAB)
    
    print(f"Loading knowledge web from {KNOWLEDGE_WEB}...")
    existing = load_json(KNOWLEDGE_WEB)
    
    # Create backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"expanded_knowledge_web_backup_{timestamp}.json"
    
    print(f"\nCreating backup at {backup_file}...")
    save_json(existing, backup_file)
    
    # Merge
    print("\nMerging...")
    merged, report = merge_knowledge(nuclear, existing)
    
    # Save merged result
    print(f"\nSaving merged knowledge web to {KNOWLEDGE_WEB}...")
    save_json(merged, KNOWLEDGE_WEB)
    
    # Save report
    report_file = PROJECT_ROOT / "data" / f"injection_report_{timestamp}.json"
    save_json(report, report_file)
    print(f"Report saved to {report_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("INJECTION COMPLETE")
    print("=" * 60)
    print(f"\nBefore:")
    print(f"  Concepts: {report['existing_concepts']}")
    print(f"  Relations: {report['existing_relations']}")
    
    print(f"\nNuclear Vocab:")
    print(f"  Concepts: {report['nuclear_concepts']}")
    print(f"  Relations: {report['nuclear_relations']}")
    
    print(f"\nAfter:")
    print(f"  Concepts: {report['final_concepts']} (+{report['new_concepts_added']})")
    print(f"  Relations: {report['final_relations']} (+{report['new_relations_added']})")
    
    # Calculate new density
    avg_density = report['final_relations'] * 2 / max(report['final_concepts'], 1)
    print(f"\nNew average density: {avg_density:.2f} relations/concept")
    
    return report


if __name__ == '__main__':
    main()
