"""
Quick Relation Expansion for Knowledge Web

Adds semantic relations between words in the same domain categories.
This is a fast alternative to the full ConceptNet download.

Run: python quick_expand_relations.py
"""

import json
import random
from pathlib import Path
from itertools import combinations

# Domain categories from seed_knowledge_web_from_vocab.py
DOMAIN_CATEGORIES = {
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
    },
    'emotion': {
        'happy','sad','angry','fear','joy','love','hate','hope','despair','calm','anxious',
        'content','frustrated','excited','bored','curious','confused','confident','uncertain',
        'grateful','resentful','proud','ashamed','jealous','compassionate'
    },
    'quantity': {
        'one','two','three','many','few','all','none','some','most','least','more','less',
        'equal','double','half','increase','decrease','multiply','divide','sum','total',
        'average','maximum','minimum','count','measure'
    }
}

# Cross-domain relationships
CROSS_DOMAIN_RELATIONS = [
    ('behavior', 'survival', 'enables'),
    ('cognition', 'behavior', 'guides'),
    ('perception', 'cognition', 'informs'),
    ('social', 'behavior', 'influences'),
    ('emotion', 'behavior', 'motivates'),
    ('temporal', 'behavior', 'sequences'),
    ('causal', 'behavior', 'explains'),
    ('communication', 'social', 'facilitates'),
    ('governance', 'social', 'regulates'),
    ('spatial', 'behavior', 'constrains'),
]


def load_knowledge_web(path: str) -> dict:
    """Load existing knowledge web."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_knowledge_web(data: dict, path: str):
    """Save knowledge web."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def expand_relations(web_data: dict, max_relations_per_domain: int = 500) -> int:
    """Add intra-domain and cross-domain relations."""
    existing_relations = set()
    for rel in web_data.get('relations', []):
        existing_relations.add((rel['source'], rel['target']))
        existing_relations.add((rel['target'], rel['source']))
    
    concepts = set(web_data.get('concepts', {}).keys())
    new_relations = []
    
    print(f"Existing relations: {len(web_data.get('relations', []))}")
    print(f"Total concepts: {len(concepts)}")
    
    # 1. Add intra-domain relations (words in same category are related)
    for domain, words in DOMAIN_CATEGORIES.items():
        domain_words = [w for w in words if w in concepts]
        if len(domain_words) < 2:
            continue
        
        # Create relations between words in same domain
        pairs = list(combinations(domain_words, 2))
        random.shuffle(pairs)
        
        added = 0
        for w1, w2 in pairs[:max_relations_per_domain]:
            if (w1, w2) not in existing_relations:
                new_relations.append({
                    'source': w1,
                    'target': w2,
                    'relation_type': 'related_to',
                    'strength': 0.6 + random.random() * 0.3,  # 0.6-0.9
                    'context': domain,
                    'confidence': 0.8
                })
                existing_relations.add((w1, w2))
                existing_relations.add((w2, w1))
                added += 1
        
        print(f"  {domain}: added {added} relations from {len(domain_words)} words")
    
    # 2. Add cross-domain relations
    for domain1, domain2, rel_type in CROSS_DOMAIN_RELATIONS:
        words1 = [w for w in DOMAIN_CATEGORIES.get(domain1, set()) if w in concepts]
        words2 = [w for w in DOMAIN_CATEGORIES.get(domain2, set()) if w in concepts]
        
        if not words1 or not words2:
            continue
        
        # Sample cross-domain pairs
        added = 0
        for _ in range(min(100, len(words1) * len(words2) // 10)):
            w1 = random.choice(words1)
            w2 = random.choice(words2)
            if w1 != w2 and (w1, w2) not in existing_relations:
                new_relations.append({
                    'source': w1,
                    'target': w2,
                    'relation_type': rel_type,
                    'strength': 0.4 + random.random() * 0.3,  # 0.4-0.7
                    'context': f'{domain1}_{domain2}',
                    'confidence': 0.7
                })
                existing_relations.add((w1, w2))
                existing_relations.add((w2, w1))
                added += 1
        
        if added > 0:
            print(f"  {domain1} → {domain2}: added {added} cross-domain relations")
    
    # 3. Add synonym-like relations for common word patterns
    synonym_groups = [
        ['cooperate', 'collaborate', 'help', 'assist', 'support'],
        ['compete', 'rival', 'oppose', 'challenge', 'contest'],
        ['grow', 'expand', 'increase', 'develop', 'evolve'],
        ['reduce', 'decrease', 'shrink', 'diminish', 'decline'],
        ['think', 'reason', 'analyze', 'evaluate', 'consider'],
        ['move', 'travel', 'go', 'advance', 'proceed'],
        ['communicate', 'signal', 'express', 'convey', 'transmit'],
        ['survive', 'endure', 'persist', 'last', 'continue'],
        ['die', 'perish', 'expire', 'end', 'cease'],
        ['learn', 'understand', 'grasp', 'comprehend', 'absorb'],
    ]
    
    for group in synonym_groups:
        group_words = [w for w in group if w in concepts]
        for w1, w2 in combinations(group_words, 2):
            if (w1, w2) not in existing_relations:
                new_relations.append({
                    'source': w1,
                    'target': w2,
                    'relation_type': 'synonym',
                    'strength': 0.8 + random.random() * 0.15,  # 0.8-0.95
                    'context': 'synonym_group',
                    'confidence': 0.9
                })
                existing_relations.add((w1, w2))
                existing_relations.add((w2, w1))
    
    # 4. Add antonym relations
    antonym_pairs = [
        ('cooperate', 'compete'), ('friend', 'enemy'), ('ally', 'rival'),
        ('grow', 'shrink'), ('increase', 'decrease'), ('expand', 'contract'),
        ('advance', 'retreat'), ('attack', 'defend'), ('build', 'destroy'),
        ('remember', 'forget'), ('strengthen', 'weaken'), ('trust', 'betray'),
        ('happy', 'sad'), ('love', 'hate'), ('hope', 'despair'),
        ('converge', 'diverge'), ('stabilize', 'destabilize'),
    ]
    
    for w1, w2 in antonym_pairs:
        if w1 in concepts and w2 in concepts and (w1, w2) not in existing_relations:
            new_relations.append({
                'source': w1,
                'target': w2,
                'relation_type': 'antonym',
                'strength': 0.9,
                'context': 'antonym_pair',
                'confidence': 0.95
            })
            existing_relations.add((w1, w2))
            existing_relations.add((w2, w1))
    
    # Merge new relations
    web_data['relations'].extend(new_relations)
    web_data['relation_count'] = len(web_data['relations'])
    
    print(f"\nAdded {len(new_relations)} new relations")
    print(f"Total relations now: {len(web_data['relations'])}")
    
    return len(new_relations)


def main():
    web_path = Path('data/seeded_knowledge_web_50k.json')
    
    if not web_path.exists():
        print(f"❌ Knowledge web not found: {web_path}")
        return
    
    print(f"Loading knowledge web from {web_path}...")
    web_data = load_knowledge_web(web_path)
    
    print(f"\nExpanding relations...")
    added = expand_relations(web_data)
    
    # Save back
    print(f"\nSaving expanded knowledge web...")
    save_knowledge_web(web_data, web_path)
    
    print(f"\n✅ Done! Added {added} relations")
    print(f"   Concepts: {web_data['concept_count']}")
    print(f"   Relations: {web_data['relation_count']}")


if __name__ == '__main__':
    main()
