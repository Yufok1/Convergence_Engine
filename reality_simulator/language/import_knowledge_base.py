"""
Import Knowledge Base - Load JSON files into LinguisticKnowledgeWeb

This script imports the comprehensive linguistic knowledge base from JSON files
and loads them into the LinguisticKnowledgeWeb and GrammarLearner systems.

Usage:
    python import_knowledge_base.py

Files Expected:
    - data/linguistic_concepts.json
    - data/semantic_relations.json  
    - data/ngram_patterns.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try importing the knowledge web
try:
    from reality_simulator.language.linguistic_knowledge_web import (
        LinguisticKnowledgeWeb, LinguisticConcept, SemanticRelation
    )
    KNOWLEDGE_WEB_AVAILABLE = True
except ImportError:
    try:
        from linguistic_knowledge_web import (
            LinguisticKnowledgeWeb, LinguisticConcept, SemanticRelation
        )
        KNOWLEDGE_WEB_AVAILABLE = True
    except ImportError:
        KNOWLEDGE_WEB_AVAILABLE = False
        logger.error("Could not import LinguisticKnowledgeWeb")


class KnowledgeBaseImporter:
    """Import and merge JSON knowledge base into LinguisticKnowledgeWeb."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the importer.

        Args:
            data_dir: Directory containing the JSON files
        """
        self.data_dir = Path(data_dir)
        self.concepts_loaded = 0
        self.relations_loaded = 0
        self.patterns_loaded = 0

    def load_concepts(self, knowledge_web: 'LinguisticKnowledgeWeb') -> int:
        """
        Load linguistic concepts from JSON into knowledge web.

        Args:
            knowledge_web: LinguisticKnowledgeWeb instance

        Returns:
            Number of concepts loaded
        """
        concepts_file = self.data_dir / "linguistic_concepts.json"

        if not concepts_file.exists():
            logger.warning(f"Concepts file not found: {concepts_file}")
            return 0

        with open(concepts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        concepts_added = 0

        # Load content words
        for concept_data in data.get('content_words', []):
            if self._add_concept(knowledge_web, concept_data):
                concepts_added += 1

        # Load function words
        for concept_data in data.get('function_words', []):
            if self._add_concept(knowledge_web, concept_data):
                concepts_added += 1

        self.concepts_loaded = concepts_added
        logger.info(f"Loaded {concepts_added} concepts from {concepts_file}")
        return concepts_added

    def _add_concept(self, knowledge_web: 'LinguisticKnowledgeWeb', 
                     concept_data: Dict[str, Any]) -> bool:
        """Add a single concept to the knowledge web."""
        word = concept_data.get('word', '')
        if not word:
            return False

        # Skip if already exists (don't overwrite)
        if word in knowledge_web.concepts:
            return False

        concept = LinguisticConcept(
            word=word,
            definition=concept_data.get('definition', ''),
            semantic_frame=concept_data.get('semantic_frame', 'state'),
            organism_relevance=concept_data.get('organism_relevance', 1.0),
            associations=concept_data.get('associations', []),
            contexts=concept_data.get('contexts', []),
            abstraction_level=concept_data.get('abstraction_level', 0)
        )

        # Store additional metadata
        if 'grammatical_role' in concept_data:
            concept.metadata['grammatical_role'] = concept_data['grammatical_role']
        if 'typical_positions' in concept_data:
            concept.metadata['typical_positions'] = concept_data['typical_positions']
        if 'common_patterns' in concept_data:
            concept.metadata['common_patterns'] = concept_data['common_patterns']

        knowledge_web.concepts[word] = concept
        knowledge_web.word_to_concept[word] = word

        return True

    def load_relations(self, knowledge_web: 'LinguisticKnowledgeWeb') -> int:
        """
        Load semantic relations from JSON into knowledge web.

        Args:
            knowledge_web: LinguisticKnowledgeWeb instance

        Returns:
            Number of relations loaded
        """
        relations_file = self.data_dir / "semantic_relations.json"

        if not relations_file.exists():
            logger.warning(f"Relations file not found: {relations_file}")
            return 0

        with open(relations_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        relations_added = 0

        for rel_data in data.get('relations', []):
            source = rel_data.get('source', '')
            target = rel_data.get('target', '')
            rel_type = rel_data.get('relation_type', '')

            if not source or not target or not rel_type:
                continue

            # Check if relation already exists
            existing = [r for r in knowledge_web.relation_index.get(source, [])
                       if r.target == target and r.relation_type == rel_type]
            if existing:
                continue

            knowledge_web._add_relation(
                source=source,
                target=target,
                relation_type=rel_type,
                strength=rel_data.get('strength', 0.7),
                context=rel_data.get('context', None),
                confidence=0.9,  # High confidence for seeded relationships
                is_seeded=True,  # Mark as seeded (from JSON knowledge base)
                generation=0  # Loaded at initialization
            )
            relations_added += 1

        self.relations_loaded = relations_added
        logger.info(f"Loaded {relations_added} relations from {relations_file}")
        return relations_added

    def load_ngram_patterns(self, grammar_learner=None) -> int:
        """
        Load n-gram patterns from JSON for grammar bootstrapping.

        Args:
            grammar_learner: Optional GrammarLearner instance

        Returns:
            Number of patterns loaded
        """
        patterns_file = self.data_dir / "ngram_patterns.json"

        if not patterns_file.exists():
            logger.warning(f"Patterns file not found: {patterns_file}")
            return 0

        with open(patterns_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        patterns = data.get('patterns', [])
        self.patterns_loaded = len(patterns)

        logger.info(f"Loaded {len(patterns)} n-gram patterns from {patterns_file}")

        # If grammar_learner provided, seed it with patterns
        if grammar_learner is not None:
            self._seed_grammar_learner(grammar_learner, patterns)

        return len(patterns)

    def _seed_grammar_learner(self, grammar_learner, patterns: List[Dict]):
        """Seed grammar learner with n-gram patterns."""
        for pattern_data in patterns:
            pattern = pattern_data.get('pattern', [])
            weight = pattern_data.get('frequency_weight', 0.5)

            if len(pattern) < 2:
                continue

            # Add bigrams
            for i in range(len(pattern) - 1):
                bigram = (pattern[i], pattern[i+1])
                if hasattr(grammar_learner, 'add_bigram'):
                    grammar_learner.add_bigram(bigram, weight)

            # Add trigrams
            for i in range(len(pattern) - 2):
                trigram = (pattern[i], pattern[i+1], pattern[i+2])
                if hasattr(grammar_learner, 'add_trigram'):
                    grammar_learner.add_trigram(trigram, weight)

            # Add pattern variations
            for variation in pattern_data.get('variations', []):
                if len(variation) >= 2:
                    for i in range(len(variation) - 1):
                        bigram = (variation[i], variation[i+1])
                        if hasattr(grammar_learner, 'add_bigram'):
                            grammar_learner.add_bigram(bigram, weight * 0.8)

    def import_all(self, knowledge_web: 'LinguisticKnowledgeWeb',
                   grammar_learner=None) -> Dict[str, int]:
        """
        Import all knowledge base components.

        Args:
            knowledge_web: LinguisticKnowledgeWeb instance
            grammar_learner: Optional GrammarLearner instance

        Returns:
            Dictionary with counts of imported items
        """
        logger.info("=" * 60)
        logger.info("IMPORTING LINGUISTIC KNOWLEDGE BASE")
        logger.info("=" * 60)

        # Load concepts
        concepts = self.load_concepts(knowledge_web)

        # Load relations
        relations = self.load_relations(knowledge_web)

        # Load patterns
        patterns = self.load_ngram_patterns(grammar_learner)

        # Rebuild indices
        knowledge_web._build_semantic_clusters()
        knowledge_web._build_organism_mappings()

        logger.info("=" * 60)
        logger.info("IMPORT COMPLETE")
        logger.info(f"  Concepts: {concepts}")
        logger.info(f"  Relations: {relations}")
        logger.info(f"  Patterns: {patterns}")
        logger.info(f"  Total in web: {len(knowledge_web.concepts)} concepts, "
                   f"{len(knowledge_web.relations)} relations")
        logger.info("=" * 60)

        return {
            'concepts': concepts,
            'relations': relations,
            'patterns': patterns,
            'total_concepts': len(knowledge_web.concepts),
            'total_relations': len(knowledge_web.relations)
        }


def main():
    """Main function to run the import."""
    if not KNOWLEDGE_WEB_AVAILABLE:
        logger.error("LinguisticKnowledgeWeb not available. Cannot import.")
        return

    # Create knowledge web
    knowledge_web = LinguisticKnowledgeWeb()

    # Create importer and run import
    importer = KnowledgeBaseImporter(data_dir="data")
    results = importer.import_all(knowledge_web, grammar_learner=None)

    # Test: Get situational awareness
    import numpy as np
    test_state = np.array([0.8, 0.7, 5.0] + [0.5] * 15)  # High fitness, resources, connections
    words = knowledge_web.get_situational_awareness(
        organism_state=test_state,
        organism_action=1  # cooperate
    )

    logger.info(f"\nTest situational awareness: {words[:10]}")

    return results


if __name__ == "__main__":
    main()
