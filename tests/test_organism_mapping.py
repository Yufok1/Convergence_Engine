# Test organism ID format and mapping logic
import numpy as np
from reality_simulator.evolution_engine import Organism, Genotype

# Create a test organism properly
genes = np.random.randint(0, 2, 64, dtype=np.uint8)
genotype = Genotype(genes=genes, generation=0)
org = Organism(genotype=genotype)

print(f'Organism ID: {org.species_id}')
print(f'Type: {type(org.species_id)}')

# Test hash-based mapping
test_words = ['energy', 'flow', 'network', 'evolution', 'consciousness']
available_orgs = ['species_0', 'species_1', 'species_2', 'species_3', 'species_4', 'species_5']

print("\nHash-based mapping test:")
for word in test_words:
    org_index = hash(word) % len(available_orgs)
    mapped_org = available_orgs[org_index]
    print(f'Word "{word}" -> organism "{mapped_org}"')

# Test deterministic mapping (same word always maps to same organism)
print("\nDeterministic mapping test:")
for _ in range(3):  # Run multiple times to verify consistency
    for word in test_words[:3]:
        org_index = hash(word) % len(available_orgs)
        mapped_org = available_orgs[org_index]
        print(f'Word "{word}" -> organism "{mapped_org}"')
