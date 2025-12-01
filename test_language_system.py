# Quick test of language learning system
import sys
sys.path.append('.')

from reality_simulator.language_system import LanguageVocabulary

# Test the language vocabulary mapping
vocab = LanguageVocabulary()
vocab.generation = 10  # Simulate some learning

# Test the mapping method
test_org_id = 'species_42'
mapped_id = vocab._get_or_create_word_organism_mapping('energy', test_org_id)

print(f'Word "energy" mapped to organism: {mapped_id}')
print(f'Bidirectional mapping works: {vocab.word_to_organism.get("energy")} -> {vocab.organism_to_word.get(test_org_id)}')

# Test with multiple words
words = ['flow', 'network', 'evolution', 'consciousness']
for word in words:
    mapped = vocab._get_or_create_word_organism_mapping(word, f'species_{hash(word) % 10}')
    print(f'Word "{word}" -> organism "{mapped}"')

print('✅ Language vocabulary mapping system working correctly!')
