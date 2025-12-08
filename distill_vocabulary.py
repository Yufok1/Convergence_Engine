#!/usr/bin/env python3
"""
🧪 VOCABULARY DISTILLATION TOOL
===============================
One-time dataset purification tool to concentrate the vocabulary pool.

Removes low-quality, obscure, or irrelevant words from the base vocabulary
and knowledge web BEFORE organisms start learning from it.

Metrics used for distillation:
1. Word frequency (common English usage)
2. Semantic connectivity (words with more relations = more useful)
3. Domain relevance (behavior, cognition, social, survival terms)
4. Abstractness score (prefer concrete over hyper-abstract)
5. Length penalty (very long words often technical jargon)

Usage:
    python distill_vocabulary.py --input data/knowledge_web.json --output data/distilled_knowledge_web.json
    python distill_vocabulary.py --input data/vocabulary.json --target 50000 --preview
"""

import json
import argparse
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import math

# ============================================================================
# DOMAIN RELEVANCE SCORING
# ============================================================================

# High-value domains for organism simulation
PRIORITY_DOMAINS = {
    # Core survival/behavior
    'behavior': ['move', 'rest', 'eat', 'drink', 'sleep', 'hide', 'flee', 'attack', 'defend', 'hunt', 'forage'],
    'social': ['cooperate', 'compete', 'share', 'trade', 'ally', 'betray', 'trust', 'help', 'harm', 'group'],
    'cognition': ['think', 'learn', 'remember', 'forget', 'decide', 'plan', 'predict', 'recognize', 'understand'],
    'emotion': ['fear', 'joy', 'anger', 'sad', 'happy', 'calm', 'stress', 'comfort', 'pain', 'pleasure'],
    'perception': ['see', 'hear', 'smell', 'touch', 'sense', 'detect', 'notice', 'observe', 'watch'],
    'physical': ['strong', 'weak', 'fast', 'slow', 'big', 'small', 'heavy', 'light', 'hard', 'soft'],
    'spatial': ['near', 'far', 'left', 'right', 'up', 'down', 'inside', 'outside', 'between', 'around'],
    'temporal': ['now', 'before', 'after', 'soon', 'later', 'always', 'never', 'sometimes', 'often'],
    'quantity': ['many', 'few', 'more', 'less', 'all', 'none', 'some', 'most', 'enough', 'too'],
    'quality': ['good', 'bad', 'better', 'worse', 'best', 'worst', 'safe', 'dangerous', 'useful', 'useless'],
}

# Words that are almost always junk in this context
BLACKLIST_PATTERNS = [
    r'^[A-Z]',           # Proper nouns (capitalized)
    r'\d',               # Contains numbers
    r'^.{20,}$',         # Very long words (20+ chars)
    r'^.{1,2}$',         # Very short (1-2 chars)
    r'aceae$',           # Taxonomic family names
    r'idae$',            # Taxonomic family names
    r'inae$',            # Taxonomic subfamily
    r'itis$',            # Medical inflammation terms
    r'osis$',            # Medical condition terms
    r'ectomy$',          # Surgical terms
    r'oscopy$',          # Medical procedure terms
    r'^pseudo',          # Pseudo- prefix (often technical)
    r'^anti[a-z]{10,}',  # Long anti- compounds
    r'^[a-z]+ization$',  # Heavy nominalizations
]

# Specific words to always remove (domain-specific junk found in WordNet)
BLACKLIST_WORDS = {
    # Scientific jargon
    'sciaenops', 'pharmacokinetics', 'chromatography', 'spectrophotometry',
    'electroencephalography', 'psychopharmacology', 'immunohistochemistry',
    # Obscure taxonomic terms
    'actinopterygii', 'chondrichthyes', 'gymnophiona', 'rhynchocephalia',
    # Medical/clinical
    'lymphadenopathy', 'thrombocytopenia', 'hyperbilirubinemia',
    # Technical chemistry
    'polymerization', 'depolymerization', 'transesterification',
}

# Words to always keep (core vocabulary)
WHITELIST_WORDS = {
    # Actions
    'move', 'rest', 'eat', 'drink', 'sleep', 'wake', 'run', 'walk', 'jump', 'climb',
    'swim', 'fly', 'hide', 'seek', 'find', 'lose', 'take', 'give', 'share', 'keep',
    'make', 'break', 'build', 'destroy', 'grow', 'shrink', 'live', 'die', 'born',
    'attack', 'defend', 'flee', 'chase', 'catch', 'escape', 'hunt', 'forage',
    # Social
    'friend', 'enemy', 'ally', 'rival', 'leader', 'follower', 'group', 'alone',
    'cooperate', 'compete', 'help', 'harm', 'trust', 'betray', 'love', 'hate',
    # Cognition
    'think', 'know', 'learn', 'teach', 'remember', 'forget', 'decide', 'choose',
    'plan', 'goal', 'want', 'need', 'hope', 'fear', 'expect', 'surprise',
    # Physical
    'big', 'small', 'fast', 'slow', 'strong', 'weak', 'hot', 'cold', 'wet', 'dry',
    'hard', 'soft', 'heavy', 'light', 'sharp', 'dull', 'loud', 'quiet',
    # Spatial
    'here', 'there', 'near', 'far', 'up', 'down', 'left', 'right', 'front', 'back',
    'inside', 'outside', 'above', 'below', 'between', 'around', 'through',
    # Temporal
    'now', 'then', 'before', 'after', 'soon', 'late', 'early', 'always', 'never',
    # Resources
    'food', 'water', 'shelter', 'territory', 'resource', 'energy', 'health',
    # States
    'alive', 'dead', 'healthy', 'sick', 'hungry', 'full', 'tired', 'rested',
    'safe', 'danger', 'calm', 'stress', 'happy', 'sad', 'angry', 'scared',
}


class VocabularyDistiller:
    """Distills vocabulary to concentrated, high-quality word pool."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.stats = defaultdict(int)
        self.blacklist_compiled = [re.compile(p) for p in BLACKLIST_PATTERNS]
        
    def log(self, msg: str):
        if self.verbose:
            print(msg)
    
    # ========================================================================
    # SCORING FUNCTIONS
    # ========================================================================
    
    def score_word_quality(self, word: str, relations: Dict = None) -> Tuple[float, List[str]]:
        """
        Score a word's quality for inclusion in distilled vocabulary.
        
        Returns:
            (score, reasons) - score 0-1, list of scoring factors
        """
        score = 0.5  # Start neutral
        reasons = []
        
        # Whitelist check (automatic include)
        if word.lower() in WHITELIST_WORDS:
            return 1.0, ['whitelist']
        
        # Blacklist check (automatic exclude)
        if word.lower() in BLACKLIST_WORDS:
            return 0.0, ['blacklist_word']
        
        # Pattern blacklist
        for pattern in self.blacklist_compiled:
            if pattern.search(word):
                return 0.0, ['blacklist_pattern']
        
        # Length scoring (prefer 3-12 char words)
        length = len(word)
        if 3 <= length <= 8:
            score += 0.15
            reasons.append('optimal_length')
        elif 9 <= length <= 12:
            score += 0.05
            reasons.append('acceptable_length')
        elif length > 15:
            score -= 0.2
            reasons.append('too_long')
        elif length < 3:
            score -= 0.3
            reasons.append('too_short')
        
        # Syllable complexity (rough estimate)
        vowels = len(re.findall(r'[aeiou]', word.lower()))
        if vowels <= 4:
            score += 0.1
            reasons.append('simple_pronunciation')
        elif vowels > 6:
            score -= 0.1
            reasons.append('complex_pronunciation')
        
        # Domain relevance
        word_lower = word.lower()
        for domain, keywords in PRIORITY_DOMAINS.items():
            if word_lower in keywords:
                score += 0.3
                reasons.append(f'priority_domain:{domain}')
                break
            # Partial match (word contains or is contained by keyword)
            for kw in keywords:
                if kw in word_lower or word_lower in kw:
                    score += 0.1
                    reasons.append(f'related_to:{domain}')
                    break
        
        # Connectivity scoring (if relations provided)
        if relations:
            num_relations = len(relations)
            if num_relations >= 10:
                score += 0.2
                reasons.append(f'high_connectivity:{num_relations}')
            elif num_relations >= 5:
                score += 0.1
                reasons.append(f'medium_connectivity:{num_relations}')
            elif num_relations == 0:
                score -= 0.15
                reasons.append('isolated')
        
        # Common English patterns (positive)
        if re.match(r'^[a-z]+$', word) and not re.search(r'([a-z])\1{2,}', word):
            score += 0.05
            reasons.append('clean_lowercase')
        
        # Technical suffix penalties
        technical_suffixes = ['ology', 'ography', 'ometry', 'ization', 'ification']
        for suffix in technical_suffixes:
            if word.endswith(suffix):
                score -= 0.15
                reasons.append(f'technical_suffix:{suffix}')
                break
        
        return max(0.0, min(1.0, score)), reasons
    
    # ========================================================================
    # DISTILLATION METHODS
    # ========================================================================
    
    def distill_knowledge_web(self, 
                              knowledge_web: Dict[str, Any],
                              target_concepts: int = None,
                              min_score: float = 0.3) -> Dict[str, Any]:
        """
        Distill a knowledge web to remove low-quality concepts.
        
        Args:
            knowledge_web: Full knowledge web dict
            target_concepts: Target number of concepts (None = use min_score only)
            min_score: Minimum quality score to keep
            
        Returns:
            Distilled knowledge web
        """
        concepts = knowledge_web.get('concepts', {})
        relations_raw = knowledge_web.get('relations', [])
        
        # Convert relations to dict format for scoring
        # Format could be list of edges or dict of {source: {target: weight}}
        relations = defaultdict(dict)
        if isinstance(relations_raw, list):
            for rel in relations_raw:
                src = rel.get('source')
                tgt = rel.get('target')
                weight = rel.get('strength', rel.get('weight', 0.5))
                if src and tgt:
                    relations[src][tgt] = weight
        elif isinstance(relations_raw, dict):
            relations = relations_raw
        
        self.log(f"\n🧪 DISTILLING KNOWLEDGE WEB")
        self.log(f"   Input: {len(concepts):,} concepts, {len(relations_raw) if isinstance(relations_raw, list) else sum(len(r) for r in relations_raw.values()):,} relations")
        
        # Score all concepts
        scored_concepts = []
        for concept_id, concept_data in concepts.items():
            word = concept_data.get('word', concept_id)
            concept_relations = relations.get(concept_id, {})
            score, reasons = self.score_word_quality(word, concept_relations)
            scored_concepts.append((concept_id, score, reasons, concept_data))
            
            # Track stats
            if score >= 0.7:
                self.stats['high_quality'] += 1
            elif score >= 0.4:
                self.stats['medium_quality'] += 1
            elif score > 0:
                self.stats['low_quality'] += 1
            else:
                self.stats['rejected'] += 1
        
        # Sort by score descending
        scored_concepts.sort(key=lambda x: x[1], reverse=True)
        
        # Determine cutoff
        if target_concepts and target_concepts < len(scored_concepts):
            # Take top N by score
            cutoff_score = scored_concepts[target_concepts - 1][1]
            self.log(f"   Target: {target_concepts:,} concepts (cutoff score: {cutoff_score:.3f})")
        else:
            cutoff_score = min_score
            self.log(f"   Using minimum score cutoff: {min_score:.3f}")
        
        # Filter concepts
        kept_concepts = {}
        kept_ids = set()
        removed_examples = []
        
        for concept_id, score, reasons, concept_data in scored_concepts:
            if score >= max(cutoff_score, min_score):
                kept_concepts[concept_id] = concept_data
                kept_ids.add(concept_id)
            else:
                if len(removed_examples) < 20:
                    removed_examples.append((concept_data.get('word', concept_id), score, reasons))
        
        # Filter relations (keep only relations between kept concepts)
        # Preserve original format (list or dict)
        if isinstance(relations_raw, list):
            kept_relations = [
                rel for rel in relations_raw
                if rel.get('source') in kept_ids and rel.get('target') in kept_ids
            ]
            original_rel_count = len(relations_raw)
            kept_rel_count = len(kept_relations)
        else:
            kept_relations = {}
            for concept_id, rels in relations.items():
                if concept_id in kept_ids:
                    filtered_rels = {
                        target: weight 
                        for target, weight in rels.items() 
                        if target in kept_ids
                    }
                    if filtered_rels:
                        kept_relations[concept_id] = filtered_rels
            original_rel_count = sum(len(r) for r in relations.values())
            kept_rel_count = sum(len(r) for r in kept_relations.values()) if isinstance(kept_relations, dict) else len(kept_relations)
        
        # Build output - preserve original structure
        distilled = {
            **{k: v for k, v in knowledge_web.items() if k not in ['concepts', 'relations', 'metadata']},
            'concepts': kept_concepts,
            'relations': kept_relations,
            'concept_count': len(kept_concepts),
            'relation_count': kept_rel_count,
            'metadata': {
                **knowledge_web.get('metadata', {}),
                'distilled': True,
                'original_concepts': len(concepts),
                'original_relations': original_rel_count,
                'distilled_concepts': len(kept_concepts),
                'distilled_relations': kept_rel_count,
                'min_score_used': max(cutoff_score, min_score),
            }
        }
        
        # Report
        self.log(f"\n📊 DISTILLATION RESULTS:")
        self.log(f"   Concepts: {len(concepts):,} → {len(kept_concepts):,} ({len(kept_concepts)/len(concepts)*100:.1f}% kept)")
        self.log(f"   Relations: {original_rel_count:,} → {kept_rel_count:,}")
        self.log(f"\n   Quality distribution:")
        self.log(f"     High (≥0.7):   {self.stats['high_quality']:,}")
        self.log(f"     Medium (0.4-0.7): {self.stats['medium_quality']:,}")
        self.log(f"     Low (0.0-0.4):    {self.stats['low_quality']:,}")
        self.log(f"     Rejected (0):     {self.stats['rejected']:,}")
        
        if removed_examples:
            self.log(f"\n   Sample removed words:")
            for word, score, reasons in removed_examples[:10]:
                self.log(f"     '{word}' (score={score:.2f}, {reasons[0] if reasons else 'low_score'})")
        
        return distilled
    
    def distill_vocabulary_file(self,
                                vocab_data: Dict[str, Any],
                                target_words: int = None,
                                min_score: float = 0.3) -> Dict[str, Any]:
        """
        Distill a simple vocabulary file (word list with metadata).
        """
        words = vocab_data.get('words', vocab_data.get('vocabulary', []))
        
        if isinstance(words, dict):
            # Dict format: {word: data}
            word_list = list(words.keys())
        else:
            # List format
            word_list = words
        
        self.log(f"\n🧪 DISTILLING VOCABULARY")
        self.log(f"   Input: {len(word_list):,} words")
        
        # Score all words
        scored_words = []
        for word in word_list:
            score, reasons = self.score_word_quality(word)
            scored_words.append((word, score, reasons))
        
        # Sort and filter
        scored_words.sort(key=lambda x: x[1], reverse=True)
        
        if target_words and target_words < len(scored_words):
            cutoff = max(scored_words[target_words - 1][1], min_score)
        else:
            cutoff = min_score
        
        kept_words = [w for w, s, r in scored_words if s >= cutoff]
        
        self.log(f"   Output: {len(kept_words):,} words ({len(kept_words)/len(word_list)*100:.1f}% kept)")
        
        # Preserve structure
        if isinstance(words, dict):
            distilled_words = {w: words[w] for w in kept_words if w in words}
        else:
            distilled_words = kept_words
        
        result = {
            **vocab_data,
            'words' if 'words' in vocab_data else 'vocabulary': distilled_words,
            'distillation_metadata': {
                'original_count': len(word_list),
                'distilled_count': len(kept_words),
                'min_score': cutoff,
            }
        }
        
        return result
    
    def preview_distillation(self, data: Dict[str, Any], sample_size: int = 50):
        """Show preview of what would be removed/kept without saving."""
        
        # Detect format and build relations lookup
        relations_lookup = defaultdict(dict)
        
        if 'concepts' in data:
            concepts = data['concepts']
            relations_raw = data.get('relations', [])
            
            # Build relations lookup
            if isinstance(relations_raw, list):
                for rel in relations_raw:
                    src = rel.get('source')
                    tgt = rel.get('target')
                    if src and tgt:
                        relations_lookup[src][tgt] = rel.get('strength', 0.5)
            elif isinstance(relations_raw, dict):
                relations_lookup = relations_raw
            
            # Build items list
            items = [(c.get('word', cid), relations_lookup.get(cid, {})) 
                     for cid, c in concepts.items()]
        else:
            words = data.get('words', data.get('vocabulary', []))
            if isinstance(words, dict):
                items = [(w, {}) for w in words.keys()]
            else:
                items = [(w, {}) for w in words]
        
        # Score sample
        scored = []
        for word, rels in items[:1000]:  # Score first 1000 for preview
            score, reasons = self.score_word_quality(word, rels if rels else None)
            scored.append((word, score, reasons))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        print("\n" + "="*60)
        print("DISTILLATION PREVIEW")
        print("="*60)
        
        print(f"\n🟢 TOP {sample_size} (would KEEP):")
        for word, score, reasons in scored[:sample_size]:
            print(f"  {score:.2f} | {word:20} | {', '.join(reasons[:2])}")
        
        print(f"\n🔴 BOTTOM {sample_size} (would REMOVE):")
        for word, score, reasons in scored[-sample_size:]:
            print(f"  {score:.2f} | {word:20} | {', '.join(reasons[:2]) if reasons else 'low_score'}")
        
        # Score distribution
        high = sum(1 for _, s, _ in scored if s >= 0.7)
        med = sum(1 for _, s, _ in scored if 0.4 <= s < 0.7)
        low = sum(1 for _, s, _ in scored if 0 < s < 0.4)
        zero = sum(1 for _, s, _ in scored if s == 0)
        
        print(f"\n📊 Score distribution (sample of {len(scored)}):")
        print(f"  High (≥0.7):   {high:4} ({high/len(scored)*100:.1f}%)")
        print(f"  Medium:        {med:4} ({med/len(scored)*100:.1f}%)")
        print(f"  Low:           {low:4} ({low/len(scored)*100:.1f}%)")
        print(f"  Rejected:      {zero:4} ({zero/len(scored)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Distill vocabulary/knowledge web to high-quality subset")
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: input_distilled.json)')
    parser.add_argument('--target', '-t', type=int, help='Target number of concepts/words')
    parser.add_argument('--min-score', type=float, default=0.3, help='Minimum quality score (0-1)')
    parser.add_argument('--preview', action='store_true', help='Preview only, no output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    # Load input
    print(f"📂 Loading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    distiller = VocabularyDistiller(verbose=not args.quiet)
    
    # Preview mode
    if args.preview:
        distiller.preview_distillation(data)
        return 0
    
    # Detect format and distill
    if 'concepts' in data:
        result = distiller.distill_knowledge_web(data, args.target, args.min_score)
    else:
        result = distiller.distill_vocabulary_file(data, args.target, args.min_score)
    
    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(input_path.stem + '_distilled.json')
    
    print(f"\n💾 Saving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Distillation complete!")
    return 0


if __name__ == '__main__':
    exit(main())
