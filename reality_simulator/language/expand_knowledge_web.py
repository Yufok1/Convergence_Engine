"""
Expand Linguistic Knowledge Web with ConceptNet + WordNet

This script downloads and integrates open-source linguistic datasets:
- ConceptNet 5.7: Semantic relationships and common-sense knowledge
- WordNet (via NLTK): Synonyms, antonyms, definitions

Expands the knowledge web from ~326 concepts to 100,000+ concepts with 500,000+ relations.

Usage:
    python expand_knowledge_web.py [--concepts 100000] [--min-weight 2.0]
"""

import json
import logging
import argparse
import requests
import gzip
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from reality_simulator.language.linguistic_knowledge_web import (
        LinguisticKnowledgeWeb, LinguisticConcept, SemanticRelation
    )
except ImportError:
    logger.error("Could not import LinguisticKnowledgeWeb. Make sure you're in the correct directory.")
    exit(1)

# Try importing NLTK WordNet
try:
    import nltk
    from nltk.corpus import wordnet as wn
    WORDNET_AVAILABLE = True
except ImportError:
    WORDNET_AVAILABLE = False
    logger.warning("NLTK not installed. WordNet integration will be skipped.")


class KnowledgeWebExpander:
    """Expand linguistic knowledge web with open-source datasets."""
    
    CONCEPTNET_ASSERTIONS_URL = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"
    
    # Relation type mappings: ConceptNet → LinguisticKnowledgeWeb
    RELATION_MAP = {
        '/r/Synonym': 'synonym',
        '/r/Antonym': 'antonym',
        '/r/Causes': 'causes',
        '/r/CausesDesire': 'causes',
        '/r/CreatedBy': 'causes',
        '/r/CapableOf': 'enables',
        '/r/UsedFor': 'enables',
        '/r/HasPrerequisite': 'requires',
        '/r/MotivatedByGoal': 'enables',
        '/r/IsA': 'is_a',
        '/r/PartOf': 'part_of',
        '/r/HasA': 'has_a',
        '/r/MadeOf': 'part_of',
        '/r/DefinedAs': 'defined_as',
        '/r/SimilarTo': 'similar_to',
        '/r/RelatedTo': 'related_to',
        '/r/HasProperty': 'has_property',
        '/r/HasContext': 'has_context',
        '/r/MannerOf': 'similar_to',
        '/r/LocatedNear': 'near',
        '/r/AtLocation': 'located_at'
    }
    
    # Semantic frames for common word types
    FRAME_PATTERNS = {
        'verb': 'action',
        'noun': 'state',
        'adj': 'quality',
        'adv': 'quality'
    }
    
    def __init__(self, 
                 data_dir: str = "data/knowledge",
                 max_concepts: int = 100000,
                 min_weight: float = 2.0,
                 organism_boost: float = 2.0):
        """
        Initialize the expander.
        
        Args:
            data_dir: Directory to store downloaded data
            max_concepts: Maximum number of concepts to import
            min_weight: Minimum ConceptNet weight (confidence) threshold
            organism_boost: Weight boost for organism-relevant concepts
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concepts = max_concepts
        self.min_weight = min_weight
        self.organism_boost = organism_boost
        
        # Statistics
        self.stats = {
            'concepts_added': 0,
            'relations_added': 0,
            'wordnet_synonyms': 0,
            'wordnet_antonyms': 0,
            'conceptnet_relations': 0,
            'skipped_low_weight': 0,
            'skipped_non_english': 0
        }
        
        # Organism-relevant keywords for boosting relevance
        self.organism_keywords = {
            'move', 'act', 'do', 'go', 'travel', 'explore', 'wander',
            'eat', 'food', 'hunger', 'consume', 'feed', 'nutrition',
            'cooperate', 'collaborate', 'help', 'share', 'team', 'together',
            'compete', 'fight', 'battle', 'challenge', 'rival', 'conflict',
            'survive', 'live', 'exist', 'endure', 'persist', 'thrive',
            'grow', 'develop', 'evolve', 'adapt', 'change', 'transform',
            'die', 'death', 'extinct', 'perish', 'eliminate',
            'social', 'group', 'network', 'connect', 'link', 'interact',
            'resource', 'energy', 'power', 'strength', 'fitness', 'health',
            'danger', 'threat', 'risk', 'safe', 'protect', 'defend',
            'learn', 'know', 'understand', 'think', 'reason', 'decide',
            'sense', 'perceive', 'see', 'feel', 'detect', 'aware'
        }
    
    def download_conceptnet(self) -> Path:
        """Download ConceptNet assertions if not already cached."""
        cache_path = self.data_dir / "conceptnet-assertions-5.7.0.csv.gz"
        
        if cache_path.exists():
            logger.info(f"ConceptNet data already cached at {cache_path}")
            return cache_path
        
        logger.info(f"Downloading ConceptNet from {self.CONCEPTNET_ASSERTIONS_URL}")
        logger.info("This is a large file (~1.5GB), may take several minutes...")
        
        response = requests.get(self.CONCEPTNET_ASSERTIONS_URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB ({percent:.1f}%)")
        
        logger.info(f"ConceptNet downloaded to {cache_path}")
        return cache_path
    
    def parse_conceptnet_uri(self, uri: str) -> Tuple[str, str]:
        """
        Parse ConceptNet URI to extract language and term.
        
        Args:
            uri: ConceptNet URI like '/c/en/hungry' or '/c/en/eat_food'
            
        Returns:
            (language, term) tuple, e.g., ('en', 'hungry')
        """
        parts = uri.strip().split('/')
        if len(parts) < 4:
            return ('', '')
        
        lang = parts[2]
        term = parts[3]
        
        # Clean up term (remove POS tags, handle underscores)
        term = term.split('/')[0]  # Remove any sub-paths
        term = term.replace('_', ' ')  # Replace underscores with spaces
        
        return (lang, term)
    
    def calculate_organism_relevance(self, term: str) -> float:
        """
        Calculate how relevant a term is to organism experiences.
        
        Args:
            term: The word/phrase
            
        Returns:
            Relevance score 0.0-1.0
        """
        term_lower = term.lower()
        words = set(term_lower.split())
        
        # Check for direct keyword matches
        if words & self.organism_keywords:
            return 1.0
        
        # Check for partial matches (e.g., "movement" contains "move")
        for keyword in self.organism_keywords:
            if keyword in term_lower or term_lower in keyword:
                return 0.8
        
        # Default relevance based on word type
        # Concrete nouns and action verbs are more relevant
        if len(words) == 1:
            # Single word - might be abstract
            return 0.5
        else:
            # Multi-word phrases - likely specific and relevant
            return 0.6
    
    def load_conceptnet_relations(self, filepath: Path, knowledge_web: LinguisticKnowledgeWeb) -> int:
        """
        Load ConceptNet relations into knowledge web.
        
        Args:
            filepath: Path to ConceptNet CSV file
            knowledge_web: LinguisticKnowledgeWeb instance
            
        Returns:
            Number of relations added
        """
        logger.info(f"Loading ConceptNet relations from {filepath}")
        
        # Track concepts and relations for filtering
        concept_scores = defaultdict(float)
        relations_buffer = []
        
        # First pass: Read all relations, score concepts
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i % 100000 == 0:
                    logger.info(f"Processed {i} ConceptNet assertions...")
                
                parts = line.strip().split('\t')
                if len(parts) < 5:
                    continue
                
                rel_uri = parts[0]
                start_uri = parts[1]
                end_uri = parts[2]
                info = json.loads(parts[3])
                
                weight = info.get('weight', 1.0)
                
                # Filter by weight
                if weight < self.min_weight:
                    self.stats['skipped_low_weight'] += 1
                    continue
                
                # Parse URIs
                start_lang, start_term = self.parse_conceptnet_uri(start_uri)
                end_lang, end_term = self.parse_conceptnet_uri(end_uri)
                
                # Only English
                if start_lang != 'en' or end_lang != 'en':
                    self.stats['skipped_non_english'] += 1
                    continue
                
                # Filter empty terms
                if not start_term or not end_term:
                    continue
                
                # Map relation type
                rel_type = self.RELATION_MAP.get(rel_uri, 'related_to')
                
                # Calculate organism relevance boost
                start_relevance = self.calculate_organism_relevance(start_term)
                end_relevance = self.calculate_organism_relevance(end_term)
                
                # Boost weight for organism-relevant concepts
                if start_relevance > 0.7 or end_relevance > 0.7:
                    weight *= self.organism_boost
                
                # Score concepts by their weighted connections
                concept_scores[start_term] += weight
                concept_scores[end_term] += weight
                
                # Buffer relation
                relations_buffer.append({
                    'source': start_term,
                    'target': end_term,
                    'relation': rel_type,
                    'weight': weight,
                    'start_relevance': start_relevance,
                    'end_relevance': end_relevance
                })
        
        logger.info(f"Found {len(concept_scores)} unique concepts")
        logger.info(f"Buffered {len(relations_buffer)} relations")
        
        # Select top concepts by score
        top_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)[:self.max_concepts]
        selected_concepts = {term for term, score in top_concepts}
        
        logger.info(f"Selected top {len(selected_concepts)} concepts")
        
        # Second pass: Add concepts and relations
        for term in selected_concepts:
            if term not in knowledge_web.concepts:
                relevance = self.calculate_organism_relevance(term)
                
                # Determine semantic frame (simplified)
                if any(kw in term.lower() for kw in ['move', 'go', 'do', 'act', 'make', 'create']):
                    frame = 'action'
                elif any(kw in term.lower() for kw in ['is', 'has', 'be', 'state', 'condition']):
                    frame = 'state'
                else:
                    frame = 'quality'
                
                concept = LinguisticConcept(
                    word=term,
                    definition=f"Concept from ConceptNet: {term}",
                    semantic_frame=frame,
                    organism_relevance=relevance,
                    associations=[],
                    contexts=[],
                    abstraction_level=1
                )
                
                knowledge_web.concepts[term] = concept
                knowledge_web.word_to_concept[term] = term
                self.stats['concepts_added'] += 1
        
        # Add relations for selected concepts
        for rel_data in relations_buffer:
            source = rel_data['source']
            target = rel_data['target']
            
            # Only add if both concepts are selected
            if source in selected_concepts and target in selected_concepts:
                knowledge_web._add_relation(
                    source=source,
                    target=target,
                    relation_type=rel_data['relation'],
                    strength=min(rel_data['weight'] / 5.0, 1.0),  # Normalize to 0-1
                    confidence=0.8,  # ConceptNet is high confidence
                    is_seeded=False,  # Mark as imported, not hand-crafted
                    generation=0
                )
                self.stats['relations_added'] += 1
                self.stats['conceptnet_relations'] += 1
        
        logger.info(f"Added {self.stats['concepts_added']} concepts and {self.stats['relations_added']} relations")
        return self.stats['relations_added']
    
    def integrate_wordnet(self, knowledge_web: LinguisticKnowledgeWeb) -> int:
        """
        Integrate WordNet synonyms and antonyms.
        
        Args:
            knowledge_web: LinguisticKnowledgeWeb instance
            
        Returns:
            Number of relations added
        """
        if not WORDNET_AVAILABLE:
            logger.warning("NLTK WordNet not available, skipping")
            return 0
        
        logger.info("Integrating WordNet synonyms and antonyms...")
        
        # Try to download WordNet if not present
        try:
            wn.ensure_loaded()
        except:
            logger.info("Downloading WordNet corpus...")
            nltk.download('wordnet')
            nltk.download('omw-1.4')
        
        relations_added = 0
        
        # For each concept in knowledge web, find WordNet relationships
        for word in list(knowledge_web.concepts.keys()):
            # Get synsets for this word
            synsets = wn.synsets(word.replace(' ', '_'))
            
            if not synsets:
                continue
            
            # Get synonyms (lemmas in same synset)
            synonyms = set()
            for synset in synsets[:3]:  # Limit to top 3 meanings
                for lemma in synset.lemmas():
                    syn = lemma.name().replace('_', ' ')
                    if syn != word and syn.lower() != word.lower():
                        synonyms.add(syn)
                
                # Get antonyms
                for lemma in synset.lemmas():
                    for antonym in lemma.antonyms():
                        ant = antonym.name().replace('_', ' ')
                        if ant not in knowledge_web.concepts:
                            # Add antonym as concept
                            concept = LinguisticConcept(
                                word=ant,
                                definition=f"Antonym of {word}",
                                semantic_frame=knowledge_web.concepts[word].semantic_frame,
                                organism_relevance=knowledge_web.concepts[word].organism_relevance,
                                associations=[word],
                                contexts=knowledge_web.concepts[word].contexts,
                                abstraction_level=knowledge_web.concepts[word].abstraction_level
                            )
                            knowledge_web.concepts[ant] = concept
                            knowledge_web.word_to_concept[ant] = ant
                        
                        # Add antonym relation
                        knowledge_web._add_relation(
                            source=word,
                            target=ant,
                            relation_type='antonym',
                            strength=0.9,
                            confidence=0.95,  # WordNet is very high confidence
                            is_seeded=False,
                            generation=0
                        )
                        relations_added += 1
                        self.stats['wordnet_antonyms'] += 1
            
            # Add synonym relations
            for syn in list(synonyms)[:10]:  # Limit to 10 synonyms per word
                if syn not in knowledge_web.concepts:
                    # Add synonym as concept
                    concept = LinguisticConcept(
                        word=syn,
                        definition=f"Synonym of {word}",
                        semantic_frame=knowledge_web.concepts[word].semantic_frame,
                        organism_relevance=knowledge_web.concepts[word].organism_relevance,
                        associations=[word],
                        contexts=knowledge_web.concepts[word].contexts,
                        abstraction_level=knowledge_web.concepts[word].abstraction_level
                    )
                    knowledge_web.concepts[syn] = concept
                    knowledge_web.word_to_concept[syn] = syn
                
                knowledge_web._add_relation(
                    source=word,
                    target=syn,
                    relation_type='synonym',
                    strength=0.9,
                    confidence=0.95,
                    is_seeded=False,
                    generation=0
                )
                relations_added += 1
                self.stats['wordnet_synonyms'] += 1
        
        logger.info(f"Added {relations_added} WordNet relations ({self.stats['wordnet_synonyms']} synonyms, {self.stats['wordnet_antonyms']} antonyms)")
        return relations_added
    
    def expand(self, output_path: str = "data/expanded_knowledge_web.json") -> LinguisticKnowledgeWeb:
        """
        Main expansion pipeline.
        
        Args:
            output_path: Path to save expanded knowledge web
            
        Returns:
            Expanded LinguisticKnowledgeWeb
        """
        logger.info("=" * 80)
        logger.info("LINGUISTIC KNOWLEDGE WEB EXPANSION")
        logger.info("=" * 80)
        
        # Start with base knowledge web (your hand-crafted 326 concepts)
        logger.info("Initializing base knowledge web...")
        knowledge_web = LinguisticKnowledgeWeb()
        base_concepts = len(knowledge_web.concepts)
        base_relations = len(knowledge_web.relations)
        logger.info(f"Base: {base_concepts} concepts, {base_relations} relations")
        
        # Download and load ConceptNet
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: ConceptNet Integration")
        logger.info("=" * 80)
        conceptnet_path = self.download_conceptnet()
        self.load_conceptnet_relations(conceptnet_path, knowledge_web)
        
        # Integrate WordNet
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: WordNet Integration")
        logger.info("=" * 80)
        self.integrate_wordnet(knowledge_web)
        
        # Rebuild indices
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Rebuilding Indices")
        logger.info("=" * 80)
        knowledge_web._build_semantic_clusters()
        knowledge_web._build_organism_mappings()
        
        # Save expanded web
        logger.info(f"\nSaving expanded knowledge web to {output_path}")
        knowledge_web.save_to_file(output_path)
        
        # Print statistics
        logger.info("\n" + "=" * 80)
        logger.info("EXPANSION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Base concepts: {base_concepts}")
        logger.info(f"Final concepts: {len(knowledge_web.concepts)} (+{len(knowledge_web.concepts) - base_concepts})")
        logger.info(f"Base relations: {base_relations}")
        logger.info(f"Final relations: {len(knowledge_web.relations)} (+{len(knowledge_web.relations) - base_relations})")
        logger.info(f"\nConceptNet relations: {self.stats['conceptnet_relations']}")
        logger.info(f"WordNet synonyms: {self.stats['wordnet_synonyms']}")
        logger.info(f"WordNet antonyms: {self.stats['wordnet_antonyms']}")
        logger.info(f"\nSkipped (low weight): {self.stats['skipped_low_weight']}")
        logger.info(f"Skipped (non-English): {self.stats['skipped_non_english']}")
        logger.info("=" * 80)
        
        return knowledge_web


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Expand Linguistic Knowledge Web")
    parser.add_argument('--concepts', type=int, default=100000,
                       help='Maximum number of concepts to import (default: 100000)')
    parser.add_argument('--min-weight', type=float, default=2.0,
                       help='Minimum ConceptNet weight threshold (default: 2.0)')
    parser.add_argument('--organism-boost', type=float, default=2.0,
                       help='Weight boost for organism-relevant concepts (default: 2.0)')
    parser.add_argument('--output', type=str, default='data/expanded_knowledge_web.json',
                       help='Output path for expanded knowledge web')
    parser.add_argument('--data-dir', type=str, default='data/knowledge',
                       help='Directory for cached data files')
    
    args = parser.parse_args()
    
    # Create expander
    expander = KnowledgeWebExpander(
        data_dir=args.data_dir,
        max_concepts=args.concepts,
        min_weight=args.min_weight,
        organism_boost=args.organism_boost
    )
    
    # Run expansion
    start_time = time.time()
    knowledge_web = expander.expand(output_path=args.output)
    elapsed = time.time() - start_time
    
    logger.info(f"\nTotal time: {elapsed / 60:.1f} minutes")
    logger.info(f"Knowledge web saved to: {args.output}")
    logger.info("\nTo use the expanded knowledge web, update your configuration to load from this file.")


if __name__ == '__main__':
    main()
