"""
Seed Linguistic Knowledge Web from Curated Vocabulary

Takes the curated 50k vocabulary and initializes the knowledge web with:
- All 50k words as concepts
- Basic semantic frames (inferred from word categories)
- Ready for ConceptNet/WordNet expansion

This provides the "huge dataset of tailored words and their associations"
that the butterfly organisms can use for communication.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reality_simulator.language.linguistic_knowledge_web import (
    LinguisticKnowledgeWeb, LinguisticConcept, SemanticRelation
)

def load_curated_vocabulary(vocab_path: str) -> List[str]:
    """Load words from curated vocabulary JSON."""
    with open(vocab_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('words', [])


def infer_semantic_frame(word: str, domain_categories: Dict[str, Set[str]]) -> str:
    """Infer semantic frame from word based on domain categories."""
    word = word.lower()
    
    # Check domain categories from refine_vocabulary.py
    if word in domain_categories.get('behavior', set()):
        return 'action'
    elif word in domain_categories.get('cognition', set()):
        return 'mental_state'
    elif word in domain_categories.get('social', set()):
        return 'relationship'
    elif word in domain_categories.get('temporal', set()):
        return 'temporal'
    elif word in domain_categories.get('spatial', set()):
        return 'spatial'
    elif word in domain_categories.get('perception', set()):
        return 'perception'
    elif word in domain_categories.get('survival', set()):
        return 'state'
    elif word in domain_categories.get('causal', set()):
        return 'causal'
    elif word in domain_categories.get('communication', set()):
        return 'communication'
    elif word in domain_categories.get('governance', set()):
        return 'governance'
    
    # Heuristic frame detection for general words
    if word.endswith('ing'):
        return 'action'
    elif word.endswith('ly'):
        return 'quality'
    elif word.endswith('ness') or word.endswith('ity'):
        return 'state'
    elif word in {'i', 'you', 'we', 'they', 'he', 'she', 'it'}:
        return 'entity'
    elif word in {'and', 'or', 'but', 'if', 'then', 'because'}:
        return 'logical'
    else:
        return 'general'


def calculate_organism_relevance(word: str, semantic_frame: str) -> float:
    """Calculate relevance to organism experiences (0.0-1.0)."""
    # High relevance frames
    high_relevance = {'action', 'state', 'relationship', 'perception', 'survival', 'communication'}
    if semantic_frame in high_relevance:
        return 1.0
    
    # Medium relevance
    medium_relevance = {'mental_state', 'causal', 'temporal', 'spatial'}
    if semantic_frame in medium_relevance:
        return 0.8
    
    # Lower relevance for abstract/general
    return 0.5


def build_domain_categories() -> Dict[str, Set[str]]:
    """Build domain category sets matching refine_vocabulary.py."""
    return {
        'behavior': {
            'move','rest','explore','search','hunt','gather','build','destroy','attack','defend',
            'cooperate','compete','share','steal','help','lead','follow','adapt','evolve','grow',
            'learn','remember','forget','predict','signal','communicate','negotiate','strategize',
            'persist','recover','retreat','advance','allocate','distribute','cluster','organize',
            'observe','innovate','optimize','transform','stabilize'
        },
        'social': {
            'ally','rival','friend','enemy','partner','group','team','confederation','empire',
            'hegemony','coalition','consensus','influence','trust','betray','reconcile','support',
            'oppose','collaborate','coordinate','mediate','broker','summon','delegate','represent',
            'govern','elect','vote','dissent','compromise','converge','diverge'
        },
        'cognition': {
            'think','reason','analyze','evaluate','infer','deduce','classify','cluster','model',
            'abstract','generalize','specialize','focus','reflect','plan','decide','choose',
            'estimate','approximate','calculate','optimize','simulate','forecast','hypothesize',
            'explain','summarize','compare','contrast','prioritize'
        },
        'survival': {
            'survive','thrive','struggle','endure','persist','recover','heal','weaken','strengthen',
            'mutate','inherit','birth','reproduce','die','regress','progress','stabilize','escalate',
            'decay','consolidate','expand','diversify','compete','dominate','protect','safeguard',
            'exploit','forage','consume','store','reserve','scarcity','abundance'
        },
        'temporal': {
            'now','soon','later','instant','cycle','phase','epoch','interval','duration','sequence',
            'timeline','evolution','emergence','iteration','feedback','recurrence','delay',
            'acceleration','deceleration','transition','threshold','moment','persistence','latency',
            'timing','cadence','tempo','rhythm','pulse'
        },
        'causal': {
            'cause','effect','influence','impact','trigger','propagate','cascade','chain','link',
            'derive','emerge','interact','feedback','converge','diverge','correlate','predict',
            'induce','mediate','moderate','transform','stabilize','destabilize','amplify','attenuate',
            'suppress','reinforce','invert','redirect'
        },
        'communication': {
            'say','tell','ask','reply','explain','describe','announce','broadcast','whisper','shout',
            'signal','warn','advise','query','request','respond','inform','document','log','encode',
            'decode','translate','frame','contextualize'
        },
        'perception': {
            'sense','observe','detect','monitor','scan','track','trace','highlight','focus','notice',
            'perceive','recognize','identify','classify','locate','map','visualize','measure',
            'quantify','audit','inspect','assess','diagnose'
        },
        'spatial': {
            'network','graph','node','edge','link','cluster','layer','lattice','field','space',
            'region','zone','sector','boundary','interface','surface','dimension','vector','matrix',
            'topology','density','distribution','gradient','coordinate','center','perimeter','radius',
            'orbit','domain'
        },
        'governance': {
            'govern','regulate','audit','certify','authorize','authenticate','validate','version',
            'rollback','stabilize','orchestrate','synchronize','coordinate','calibrate','tune',
            'optimize','allocate','provision','schedule','prioritize','instrument','profile',
            'benchmark','trace','log','persist','index','archive','restore','sandbox','isolate'
        }
    }


def seed_knowledge_web_from_curated(
    vocab_path: str,
    output_path: str,
    include_base_concepts: bool = True
) -> Dict[str, Any]:
    """
    Seed knowledge web with curated 50k vocabulary.
    
    Args:
        vocab_path: Path to butterfly_vocabulary_50k_curated.json
        output_path: Path for output seeded_knowledge_web.json
        include_base_concepts: Whether to include original 326 base concepts
        
    Returns:
        Statistics dictionary
    """
    print(f"Loading curated vocabulary from {vocab_path}...")
    words = load_curated_vocabulary(vocab_path)
    print(f"Loaded {len(words)} words")
    
    print("Building domain categories...")
    domain_cats = build_domain_categories()
    
    print("Initializing knowledge web...")
    web = LinguisticKnowledgeWeb()
    
    if include_base_concepts:
        print(f"Keeping {len(web.concepts)} base concepts")
        base_count = len(web.concepts)
    else:
        web.concepts.clear()
        web.word_to_concept.clear()
        base_count = 0
    
    print("Creating concepts from vocabulary...")
    added = 0
    for word in words:
        if word in web.word_to_concept:
            continue  # Skip if already exists (base concept)
        
        frame = infer_semantic_frame(word, domain_cats)
        relevance = calculate_organism_relevance(word, frame)
        
        concept = LinguisticConcept(
            word=word,
            definition=f"Curated vocabulary term: {word}",
            semantic_frame=frame,
            organism_relevance=relevance,
            associations=[],
            contexts=[],
            abstraction_level=0 if frame in {'action','state','entity'} else 1
        )
        
        web.concepts[word] = concept
        web.word_to_concept[word] = word
        added += 1
        
        if added % 5000 == 0:
            print(f"  Processed {added} words...")
    
    print(f"Added {added} new concepts (total: {len(web.concepts)})")
    
    # Serialize to JSON
    print(f"Writing seeded knowledge web to {output_path}...")
    web_data = {
        'version': '1.0-seeded',
        'source': 'curated_vocabulary_50k',
        'concept_count': len(web.concepts),
        'relation_count': len(web.relations),
        'concepts': {
            cid: {
                'word': c.word,
                'definition': c.definition,
                'semantic_frame': c.semantic_frame,
                'organism_relevance': c.organism_relevance,
                'associations': c.associations,
                'contexts': c.contexts,
                'abstraction_level': c.abstraction_level
            }
            for cid, c in web.concepts.items()
        },
        'relations': [
            {
                'source': r.source,
                'target': r.target,
                'relation_type': r.relation_type,
                'strength': r.strength,
                'context': r.context,
                'confidence': r.confidence
            }
            for r in web.relations
        ],
        'metadata': {
            'base_concepts': base_count,
            'added_concepts': added,
            'ready_for_expansion': True
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, indent=2)
    
    stats = {
        'total_concepts': len(web.concepts),
        'base_concepts': base_count,
        'added_concepts': added,
        'total_relations': len(web.relations),
        'output_path': output_path
    }
    
    print(f"\n✅ Seeded knowledge web created successfully!")
    print(f"   Total concepts: {stats['total_concepts']}")
    print(f"   Base concepts: {stats['base_concepts']}")
    print(f"   Added concepts: {stats['added_concepts']}")
    print(f"   Relations: {stats['total_relations']}")
    print(f"   Output: {output_path}")
    print(f"\nNext step: Run expand_knowledge_web.py to add ConceptNet/WordNet relations")
    
    return stats


if __name__ == '__main__':
    # Paths
    vocab_path = os.path.join('data', 'butterfly_vocabulary_50k_curated.json')
    output_path = os.path.join('data', 'seeded_knowledge_web_50k.json')
    
    if not os.path.exists(vocab_path):
        print(f"❌ Curated vocabulary not found: {vocab_path}")
        print("Run: python reality_simulator/refine_vocabulary.py")
        exit(1)
    
    seed_knowledge_web_from_curated(vocab_path, output_path)
