#!/usr/bin/env python3
"""
Merge Nuclear Vocab - Consolidates all CSV extractions into unified knowledge web format.

Reads all CSVs from docs/plans/csv/, deduplicates, merges relations, and outputs:
1. data/nuclear_vocab.json - Merged vocabulary with weighted scoring
2. Prints statistics on coverage and density

CSV Format Expected:
Word,Synonyms,Antonyms,Causes,Caused_By,Category[,Interconnections]
"""

import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Paths
PROJECT_ROOT = Path(__file__).parent
CSV_DIR = PROJECT_ROOT / "docs" / "plans" / "csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "nuclear_vocab.json"

# Scoring weights (from nuclear analysis)
WEIGHTS = {
    'synonym': 3,
    'antonym': 5,  # Most valuable - defines through contrast
    'causes': 4,
    'caused_by': 4,
    'base': 1
}


def parse_list(field: str) -> List[str]:
    """Parse comma-separated field into list of cleaned words."""
    if not field or field.strip() == '':
        return []
    items = [w.strip().lower() for w in field.split(',')]
    return [w for w in items if w and len(w) > 1]


def load_csv(filepath: Path) -> List[dict]:
    """Load a single CSV file and return parsed rows."""
    rows = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('Word', '').strip().lower()
                if not word or len(word) < 2:
                    continue
                    
                rows.append({
                    'word': word,
                    'synonyms': parse_list(row.get('Synonyms', '')),
                    'antonyms': parse_list(row.get('Antonyms', '')),
                    'causes': parse_list(row.get('Causes', '')),
                    'caused_by': parse_list(row.get('Caused_By', '')),
                    'category': row.get('Category', '').strip(),
                    'interconnections': int(row.get('Interconnections', 0) or 0)
                })
    except Exception as e:
        print(f"  ERROR loading {filepath.name}: {e}")
    return rows


def merge_all_csvs() -> Tuple[Dict, Dict]:
    """
    Load and merge all CSVs into unified structures.
    
    Returns:
        concepts: Dict[word] -> {categories, interconnections}
        relations: Dict[(source, target, type)] -> strength
    """
    concepts = defaultdict(lambda: {'categories': set(), 'interconnections': 0})
    relations = defaultdict(float)  # (source, target, type) -> strength
    
    csv_files = list(CSV_DIR.glob('*.csv'))
    print(f"\nLoading {len(csv_files)} CSV files from {CSV_DIR}")
    print("=" * 60)
    
    for csv_file in sorted(csv_files):
        rows = load_csv(csv_file)
        if rows:
            print(f"  {csv_file.name}: {len(rows)} words")
        
        for row in rows:
            word = row['word']
            
            # Update concept
            if row['category']:
                concepts[word]['categories'].add(row['category'])
            concepts[word]['interconnections'] = max(
                concepts[word]['interconnections'], 
                row['interconnections']
            )
            
            # Add relations - synonyms
            for syn in row['synonyms']:
                # Bidirectional
                key1 = tuple(sorted([word, syn])) + ('synonym',)
                relations[key1] = max(relations[key1], 0.85)
                
            # Add relations - antonyms  
            for ant in row['antonyms']:
                # Bidirectional
                key1 = tuple(sorted([word, ant])) + ('antonym',)
                relations[key1] = max(relations[key1], 0.95)  # Higher strength
                
            # Add relations - causes (directional)
            for cause in row['causes']:
                key = (word, cause, 'causes')
                relations[key] = max(relations[key], 0.80)
                
            # Add relations - caused_by (directional)
            for caused in row['caused_by']:
                key = (caused, word, 'causes')  # Reverse direction
                relations[key] = max(relations[key], 0.80)
    
    return concepts, relations


def calculate_scores(concepts: Dict, relations: Dict) -> Dict[str, dict]:
    """Calculate nuclear scores for each word."""
    # Build connection counts
    word_stats = defaultdict(lambda: {
        'synonyms': set(),
        'antonyms': set(), 
        'causes': set(),
        'caused_by': set()
    })
    
    for (src, tgt, rel_type), _ in relations.items():
        if rel_type == 'synonym':
            word_stats[src]['synonyms'].add(tgt)
            word_stats[tgt]['synonyms'].add(src)
        elif rel_type == 'antonym':
            word_stats[src]['antonyms'].add(tgt)
            word_stats[tgt]['antonyms'].add(src)
        elif rel_type == 'causes':
            word_stats[src]['causes'].add(tgt)
            word_stats[tgt]['caused_by'].add(src)
    
    # Calculate weighted scores
    scores = {}
    for word in concepts:
        stats = word_stats[word]
        
        n_syn = len(stats['synonyms'])
        n_ant = len(stats['antonyms'])
        n_causes = len(stats['causes'])
        n_caused = len(stats['caused_by'])
        total_conn = n_syn + n_ant + n_causes + n_caused
        
        # Weighted score
        base = total_conn * WEIGHTS['base']
        syn_score = n_syn * WEIGHTS['synonym']
        ant_score = n_ant * WEIGHTS['antonym']
        cause_score = (n_causes + n_caused) * WEIGHTS['causes']
        
        # Bonus for "fully armed" words (have multiple relation types)
        types_present = sum([n_syn > 0, n_ant > 0, n_causes > 0 or n_caused > 0])
        multiplier = 1.5 if types_present >= 3 else (1.2 if types_present >= 2 else 1.0)
        
        weighted = (base + syn_score + ant_score + cause_score) * multiplier
        
        scores[word] = {
            'nuclear_score': round(weighted, 1),
            'connections': total_conn,
            'synonyms': n_syn,
            'antonyms': n_ant,
            'causes': n_causes,
            'caused_by': n_caused,
            'categories': list(concepts[word]['categories']),
            'interconnections': concepts[word]['interconnections']
        }
    
    return scores


def build_output_format(concepts: Dict, relations: Dict, scores: Dict) -> dict:
    """Build output JSON in knowledge web format."""
    
    # Convert relations to list format
    relations_list = []
    for (src, tgt, rel_type), strength in relations.items():
        relations_list.append({
            'source': src,
            'target': tgt,
            'relation_type': rel_type,
            'strength': strength,
            'context': 'nuclear_extraction'
        })
    
    # Sort concepts by nuclear score
    ranked_words = sorted(scores.keys(), key=lambda w: scores[w]['nuclear_score'], reverse=True)
    
    # Build concepts list
    concepts_list = []
    for word in ranked_words:
        s = scores[word]
        concepts_list.append({
            'word': word,
            'nuclear_score': s['nuclear_score'],
            'connections': s['connections'],
            'synonyms': s['synonyms'],
            'antonyms': s['antonyms'],
            'causes': s['causes'],
            'caused_by': s['caused_by'],
            'categories': s['categories']
        })
    
    return {
        'version': '1.0',
        'source': 'nuclear_vocab_extraction',
        'description': 'Merged vocabulary from deep research extraction across 10 domains',
        'weights': WEIGHTS,
        'stats': {
            'total_concepts': len(concepts_list),
            'total_relations': len(relations_list),
            'avg_connections': round(sum(s['connections'] for s in scores.values()) / max(len(scores), 1), 2),
            'avg_nuclear_score': round(sum(s['nuclear_score'] for s in scores.values()) / max(len(scores), 1), 2)
        },
        'concepts': concepts_list,
        'relations': relations_list
    }


def print_stats(output: dict, scores: Dict):
    """Print detailed statistics."""
    print("\n" + "=" * 60)
    print("NUCLEAR VOCAB STATISTICS")
    print("=" * 60)
    
    stats = output['stats']
    print(f"\nTotal Concepts: {stats['total_concepts']}")
    print(f"Total Relations: {stats['total_relations']}")
    print(f"Avg Connections: {stats['avg_connections']}")
    print(f"Avg Nuclear Score: {stats['avg_nuclear_score']}")
    
    # Relation type breakdown
    relations = output['relations']
    by_type = defaultdict(int)
    for r in relations:
        by_type[r['relation_type']] += 1
    
    print(f"\nRelations by Type:")
    for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {rtype}: {count}")
    
    # Top 25 nuclear words
    ranked = sorted(scores.keys(), key=lambda w: scores[w]['nuclear_score'], reverse=True)
    print(f"\nTOP 25 NUCLEAR WORDS:")
    print("-" * 60)
    for i, word in enumerate(ranked[:25], 1):
        s = scores[word]
        print(f"{i:2}. {word:20} score={s['nuclear_score']:5.1f}  "
              f"conn={s['connections']:3}  syn={s['synonyms']:2}  "
              f"ant={s['antonyms']:2}  causes={s['causes']:2}")
    
    # Category distribution
    cat_counts = defaultdict(int)
    for concept in output['concepts']:
        for cat in concept['categories']:
            cat_counts[cat] += 1
    
    print(f"\nCategories ({len(cat_counts)} unique):")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {cat}: {count}")


def main():
    print("=" * 60)
    print("NUCLEAR VOCAB MERGER")
    print("=" * 60)
    
    # Load and merge all CSVs
    concepts, relations = merge_all_csvs()
    
    # Calculate scores
    scores = calculate_scores(concepts, relations)
    
    # Build output
    output = build_output_format(concepts, relations, scores)
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to {OUTPUT_FILE}")
    
    # Print stats
    print_stats(output, scores)
    
    return output


if __name__ == '__main__':
    main()
