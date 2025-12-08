"""Inspect random portions of the expanded knowledge web."""
import json
import random
from collections import Counter

with open('data/expanded_knowledge_web.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== EXPANDED KNOWLEDGE WEB INSPECTION ===')
print(f'Total concepts: {len(data["concepts"]):,}')
print(f'Total relations: {len(data["relations"]):,}')

concepts = list(data['concepts'].keys())
print(f'\n--- 15 RANDOM CONCEPTS ---')
for c in random.sample(concepts, 15):
    info = data['concepts'][c]
    cat = info.get('category', 'N/A')
    wt = info.get('weight', 'N/A')
    print(f'  {c}: category={cat}, weight={wt}')

print(f'\n--- 20 RANDOM RELATIONS ---')
for rel in random.sample(data['relations'], 20):
    src = rel['source']
    tgt = rel['target']
    rtype = rel.get('relation_type', rel.get('type', 'unknown'))
    wt = rel.get('strength', rel.get('weight', 0))
    print(f'  {src} --[{rtype}]--> {tgt} (strength={wt:.2f})')

rel_types = Counter(r.get('relation_type', r.get('type', 'unknown')) for r in data['relations'])
print(f'\n--- RELATION TYPE DISTRIBUTION ---')
for rtype, count in rel_types.most_common(15):
    print(f'  {rtype}: {count:,}')

# Show some specific semantic clusters
print(f'\n--- SAMPLE SEMANTIC NEIGHBORHOODS ---')
sample_words = ['food', 'water', 'danger', 'friend', 'learn']
for word in sample_words:
    if word in data['concepts']:
        related = [r for r in data['relations'] if r['source'] == word][:5]
        if related:
            print(f'\n  "{word}" connects to:')
            for r in related:
                print(f'    --[{r.get("relation_type", "unknown")}]--> {r["target"]}')
