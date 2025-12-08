"""
Linguistic Knowledge Web - Comprehensive Semantic Network

A custom-tailored linguistic knowledge base designed for organism language learning.
Provides semantic relationships, associative complexities, and situational awareness
to enable true linguistic understanding and reflexive comprehensive thought.

Based on:
- ConceptNet (semantic relationships)
- WordNet (synonym/antonym hierarchies)
- FrameNet (semantic frames)
- Custom organism-behavior mappings
- 50K CURATED VOCABULARY with semantic seeding for diverse organism lexicons
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, field
import json
import numpy as np
import random
import os
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SemanticRelation:
    """A semantic relationship between words/concepts."""
    source: str
    target: str
    relation_type: str  # 'synonym', 'antonym', 'causes', 'enables', 'prevents', 'similar_to', 'part_of', 'related_to', 'discovered'
    strength: float = 1.0  # 0.0-1.0, semantic connection strength of relationship
    context: Optional[str] = None  # Optional context for relationship
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Quality control fields
    confidence: float = 0.9  # 0.0-1.0, validation level (separate from strength)
    is_seeded: bool = True  # True for base 326 concepts, false for discovered
    discovery_count: int = 0  # How many times relationship was discovered
    generation_discovered: int = 0  # When first discovered (generation number)
    last_used: int = 0  # Last generation used
    success_count: int = 0  # Times relationship led to good responses
    failure_count: int = 0  # Times relationship led to poor responses


@dataclass
class LinguisticConcept:
    """A linguistic concept with rich semantic information."""
    word: str
    definition: str
    semantic_frame: str  # 'action', 'state', 'quality', 'relationship', 'temporal', 'spatial'
    organism_relevance: float = 1.0  # How relevant to organism experiences (0.0-1.0)
    associations: List[str] = field(default_factory=list)  # Associated words
    contexts: List[str] = field(default_factory=list)  # Situational contexts
    abstraction_level: int = 0  # 0=concrete, 1=abstract, 2=meta
    metadata: Dict[str, Any] = field(default_factory=dict)


class LinguisticKnowledgeWeb:
    """
    Comprehensive linguistic knowledge web for organism language learning.
    
    Provides:
    - Semantic relationships (synonym, antonym, causes, enables, etc.)
    - Situational awareness (context-dependent word selection)
    - Associative complexities (word-word relationships)
    - Reflexive thought (meta-linguistic reasoning)
    - Organism-behavior grounding (words linked to organism experiences)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize linguistic knowledge web.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Core data structures
        self.concepts: Dict[str, LinguisticConcept] = {}
        self.relations: List[SemanticRelation] = []
        self.relation_index: Dict[str, List[SemanticRelation]] = defaultdict(list)
        self.word_to_concept: Dict[str, str] = {}  # word -> concept_id
        
        # Organism-behavior mappings
        self.state_word_map: Dict[str, List[str]] = {}
        self.action_word_map: Dict[int, List[str]] = {}
        self.situational_contexts: Dict[str, List[str]] = {}
        
        # Semantic clusters (for associative reasoning)
        self.semantic_clusters: Dict[str, Set[str]] = defaultdict(set)
        
        # ============================================================
        # SEMANTIC SEEDING: 50k vocabulary with category-based diversity
        # ============================================================
        self.curated_vocabulary: List[str] = []
        self.vocabulary_categories: Dict[str, List[str]] = {}  # category -> words
        self.word_to_category: Dict[str, str] = {}  # word -> category
        self.organism_word_seeds: Dict[str, Set[str]] = {}  # organism_id -> seeded words (diverse per org)
        self._load_curated_vocabulary()
        
        # Recursive expansion mechanisms (prevent yarn ball, enable growth)
        self.word_usage_counts: Dict[str, int] = defaultdict(int)  # Track word usage for diversity
        self.relation_usage_counts: Dict[Tuple[str, str, str], int] = defaultdict(int)  # Track relation usage
        self.discovered_relations: List[SemanticRelation] = []  # Organism-discovered relationships
        self.diversity_boost: float = self.config.get('diversity_boost', 0.2)  # Boost for less-used words
        self.decay_rate: float = self.config.get('decay_rate', 0.01)  # Relationship decay rate
        
        # Quality control configuration
        quality_config = self.config.get('neural', {}).get('language_model', {}).get('knowledge_web', {}).get('quality_control', {})
        self.exploration_start: float = quality_config.get('exploration_start', 0.2)  # Start at 20%
        self.exploration_end: float = quality_config.get('exploration_end', 0.05)  # End at 5%
        self.exploration_rate: float = self.exploration_start  # Current exploration rate (starts at start value)
        self.exploration_decay_generations: int = quality_config.get('exploration_decay_generations', 1000)
        self.confidence_threshold: float = quality_config.get('min_confidence_threshold', 0.3)  # Start at 0.3
        self.confidence_growth_rate: float = quality_config.get('confidence_growth_rate', 0.0005)
        self.min_discovery_count: int = quality_config.get('min_discovery_count', 3)
        self.max_discoveries_per_generation: int = quality_config.get('max_discoveries_per_generation', 10)
        self.vp_boost_exploration: bool = quality_config.get('vp_boost_exploration', True)
        self.vp_boost_threshold: float = quality_config.get('vp_boost_threshold', 0.7)
        self.current_generation: int = 0  # Track current generation for time-based learning
        
        # Discovery tracking
        self.discovery_attempts: Dict[Tuple[str, str], int] = defaultdict(int)  # Track discovery attempts per word pair
        self.successful_validations: Dict[Tuple[str, str], int] = defaultdict(int)  # Track successful validations
        
        # Context tracking for coherence validation
        self.word_context_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # Track contexts where words appear
        
        # Load base knowledge
        self._initialize_base_knowledge()
        
        logger.info(f"[LINGUISTIC_WEB] Initialized with {len(self.concepts)} concepts, {len(self.relations)} relations, {len(self.curated_vocabulary)} curated words")
    
    def _load_curated_vocabulary(self):
        """
        Load the 50k curated vocabulary with semantic categories.
        
        This enables DIVERSE word seeding per organism instead of the same
        hardcoded ~60 words for everyone.
        """
        vocab_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'butterfly_vocabulary_50k_curated.json'),
            'data/butterfly_vocabulary_50k_curated.json',
            'd:/end-GAME/butterfly/data/butterfly_vocabulary_50k_curated.json'
        ]
        
        vocab_data = None
        for path in vocab_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    vocab_data = json.load(f)
                logger.info(f"[SEMANTIC_SEED] Loaded vocabulary from {path}")
                break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        if vocab_data is None:
            logger.warning("[SEMANTIC_SEED] Could not load curated vocabulary - using fallback")
            return
        
        # Load all words
        self.curated_vocabulary = vocab_data.get('words', [])
        
        # Load category samples (these are the categorized words)
        category_samples = vocab_data.get('category_samples', {})
        for category, words in category_samples.items():
            self.vocabulary_categories[category] = words
            for word in words:
                self.word_to_category[word] = category
        
        # Build reverse index for uncategorized words -> 'other'
        categorized = set(self.word_to_category.keys())
        for word in self.curated_vocabulary:
            if word not in categorized:
                self.word_to_category[word] = 'other'
        
        logger.info(f"[SEMANTIC_SEED] Loaded {len(self.curated_vocabulary)} words in {len(self.vocabulary_categories)} categories")
    
    def _initialize_base_knowledge(self):
        """Initialize comprehensive linguistic knowledge base."""
        
        # ============================================================
        # CORE ORGANISM BEHAVIOR CONCEPTS
        # ============================================================
        
        # Action Concepts (6 organism actions)
        action_concepts = {
            'move': {
                'definition': 'To change position or location in space',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['explore', 'travel', 'wander', 'journey', 'navigate', 'migrate', 'roam'],
                'contexts': ['exploration', 'search', 'discovery', 'survival', 'resource_seeking'],
                'abstraction_level': 0
            },
            'cooperate': {
                'definition': 'To work together for mutual benefit',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['collaborate', 'help', 'assist', 'share', 'unite', 'team', 'alliance'],
                'contexts': ['social', 'network', 'mutual_benefit', 'resource_sharing', 'survival'],
                'abstraction_level': 0
            },
            'compete': {
                'definition': 'To strive against others for resources or advantage',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['fight', 'challenge', 'rival', 'contest', 'struggle', 'conflict', 'oppose'],
                'contexts': ['competition', 'resource_scarcity', 'survival', 'dominance', 'hierarchy'],
                'abstraction_level': 0
            },
            'rest': {
                'definition': 'To cease activity and recover energy',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['pause', 'recover', 'sleep', 'wait', 'recharge', 'rejuvenate', 'calm'],
                'contexts': ['recovery', 'energy_conservation', 'safety', 'stability', 'preparation'],
                'abstraction_level': 0
            },
            'reproduce': {
                'definition': 'To create offspring and propagate',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['grow', 'multiply', 'spread', 'expand', 'generate', 'create', 'propagate'],
                'contexts': ['growth', 'expansion', 'survival', 'evolution', 'continuity', 'legacy'],
                'abstraction_level': 0
            },
            'isolate': {
                'definition': 'To separate from others and become independent',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['withdraw', 'separate', 'retreat', 'alone', 'independent', 'solitary', 'detach'],
                'contexts': ['protection', 'independence', 'resource_hoarding', 'safety', 'autonomy'],
                'abstraction_level': 0
            }
        }
        
        # State Concepts (organism states)
        state_concepts = {
            'thrive': {
                'definition': 'To prosper and flourish with high fitness',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['success', 'flourish', 'prosper', 'excel', 'dominate', 'thriving', 'optimal'],
                'contexts': ['high_fitness', 'abundant_resources', 'many_connections', 'stability'],
                'abstraction_level': 0
            },
            'struggle': {
                'definition': 'To face difficulty and low fitness',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['suffer', 'decline', 'failing', 'weak', 'endure', 'persist', 'survive'],
                'contexts': ['low_fitness', 'scarce_resources', 'few_connections', 'instability'],
                'abstraction_level': 0
            },
            'stable': {
                'definition': 'To maintain consistent state without major change',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['steady', 'consistent', 'balanced', 'endure', 'persist', 'maintain', 'sustain'],
                'contexts': ['medium_fitness', 'adequate_resources', 'moderate_connections', 'equilibrium'],
                'abstraction_level': 0
            },
            'social': {
                'definition': 'To be connected and integrated with others',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['connected', 'networked', 'linked', 'integrated', 'cooperative', 'united', 'together'],
                'contexts': ['many_connections', 'cooperation', 'resource_sharing', 'mutual_support'],
                'abstraction_level': 0
            },
            'isolated': {
                'definition': 'To be separated and disconnected from others',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['alone', 'separate', 'disconnected', 'lonely', 'solitary', 'independent', 'autonomous'],
                'contexts': ['no_connections', 'independence', 'resource_hoarding', 'self_reliance'],
                'abstraction_level': 0
            },
            'rich': {
                'definition': 'To have abundant resources and wealth',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['abundant', 'plentiful', 'wealthy', 'sustained', 'prosperous', 'ample', 'sufficient'],
                'contexts': ['high_resources', 'security', 'growth_potential', 'stability'],
                'abstraction_level': 0
            },
            'poor': {
                'definition': 'To have scarce resources and deprivation',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['scarce', 'depleted', 'starving', 'needy', 'lacking', 'insufficient', 'deprived'],
                'contexts': ['low_resources', 'vulnerability', 'survival_challenge', 'instability'],
                'abstraction_level': 0
            }
        }
        
        # Quality Concepts (abstract qualities)
        quality_concepts = {
            'strong': {
                'definition': 'Having high fitness and capability',
                'frame': 'quality',
                'organism_relevance': 1.0,
                'associations': ['powerful', 'capable', 'robust', 'resilient', 'dominant', 'superior', 'excellent'],
                'contexts': ['high_fitness', 'success', 'advantage', 'survival'],
                'abstraction_level': 1
            },
            'weak': {
                'definition': 'Having low fitness and limited capability',
                'frame': 'quality',
                'organism_relevance': 1.0,
                'associations': ['vulnerable', 'fragile', 'limited', 'inferior', 'struggling', 'failing', 'declining'],
                'contexts': ['low_fitness', 'struggle', 'disadvantage', 'survival_risk'],
                'abstraction_level': 1
            },
            'fast': {
                'definition': 'Moving or acting with high speed',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['quick', 'rapid', 'swift', 'agile', 'nimble', 'efficient', 'responsive'],
                'contexts': ['exploration', 'competition', 'response', 'adaptation'],
                'abstraction_level': 1
            },
            'slow': {
                'definition': 'Moving or acting with low speed',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['gradual', 'deliberate', 'careful', 'methodical', 'patient', 'steady', 'cautious'],
                'contexts': ['conservation', 'stability', 'planning', 'safety'],
                'abstraction_level': 1
            }
        }
        
        # Relationship Concepts (between organisms/entities)
        relationship_concepts = {
            'together': {
                'definition': 'In association or cooperation with others',
                'frame': 'relationship',
                'organism_relevance': 1.0,
                'associations': ['united', 'cooperative', 'collaborative', 'allied', 'connected', 'joint', 'shared'],
                'contexts': ['cooperation', 'mutual_benefit', 'resource_sharing', 'survival'],
                'abstraction_level': 1
            },
            'alone': {
                'definition': 'Separated from others, independent',
                'frame': 'relationship',
                'organism_relevance': 1.0,
                'associations': ['isolated', 'independent', 'solitary', 'autonomous', 'separate', 'detached', 'self_reliant'],
                'contexts': ['independence', 'resource_hoarding', 'safety', 'autonomy'],
                'abstraction_level': 1
            },
            'help': {
                'definition': 'To assist or support others',
                'frame': 'relationship',
                'organism_relevance': 1.0,
                'associations': ['assist', 'support', 'aid', 'cooperate', 'collaborate', 'benefit', 'serve'],
                'contexts': ['cooperation', 'mutual_benefit', 'social', 'network'],
                'abstraction_level': 1
            },
            'share': {
                'definition': 'To distribute resources or information with others',
                'frame': 'relationship',
                'organism_relevance': 1.0,
                'associations': ['distribute', 'exchange', 'cooperate', 'collaborate', 'give', 'provide', 'contribute'],
                'contexts': ['cooperation', 'resource_flow', 'mutual_benefit', 'network'],
                'abstraction_level': 1
            }
        }
        
        # Temporal Concepts (time-related)
        temporal_concepts = {
            'now': {
                'definition': 'The present moment in time',
                'frame': 'temporal',
                'organism_relevance': 0.9,
                'associations': ['present', 'current', 'immediate', 'moment', 'instant', 'today', 'here'],
                'contexts': ['decision_making', 'action', 'response', 'awareness'],
                'abstraction_level': 1
            },
            'before': {
                'definition': 'Earlier in time, in the past',
                'frame': 'temporal',
                'organism_relevance': 0.9,
                'associations': ['past', 'previous', 'earlier', 'prior', 'ago', 'then', 'history'],
                'contexts': ['memory', 'learning', 'experience', 'causation'],
                'abstraction_level': 1
            },
            'after': {
                'definition': 'Later in time, in the future',
                'frame': 'temporal',
                'organism_relevance': 0.9,
                'associations': ['future', 'later', 'next', 'subsequent', 'then', 'ahead', 'coming'],
                'contexts': ['planning', 'prediction', 'consequence', 'causation'],
                'abstraction_level': 1
            },
            'always': {
                'definition': 'At all times, continuously',
                'frame': 'temporal',
                'organism_relevance': 0.8,
                'associations': ['forever', 'continuously', 'constantly', 'perpetually', 'eternally', 'endlessly'],
                'contexts': ['stability', 'persistence', 'law', 'pattern'],
                'abstraction_level': 2
            },
            'never': {
                'definition': 'At no time, not ever',
                'frame': 'temporal',
                'organism_relevance': 0.8,
                'associations': ['not', 'none', 'zero', 'absence', 'lack', 'void', 'empty'],
                'contexts': ['impossibility', 'constraint', 'law', 'pattern'],
                'abstraction_level': 2
            }
        }
        
        # Spatial Concepts (location-related)
        spatial_concepts = {
            'here': {
                'definition': 'At this location or position',
                'frame': 'spatial',
                'organism_relevance': 0.9,
                'associations': ['present', 'location', 'place', 'position', 'spot', 'site', 'where', 'center'],
                'contexts': ['awareness', 'navigation', 'action', 'context'],
                'abstraction_level': 0
            },
            'there': {
                'definition': 'At that location or position',
                'frame': 'spatial',
                'organism_relevance': 0.9,
                'associations': ['distant', 'away', 'other', 'elsewhere', 'remote', 'far', 'beyond', 'edge'],
                'contexts': ['navigation', 'exploration', 'target', 'goal'],
                'abstraction_level': 0
            },
            'near': {
                'definition': 'Close in distance or proximity',
                'frame': 'spatial',
                'organism_relevance': 0.9,
                'associations': ['close', 'adjacent', 'proximate', 'local', 'immediate', 'surrounding', 'neighboring'],
                'contexts': ['connection', 'interaction', 'awareness', 'safety'],
                'abstraction_level': 0
            },
            'far': {
                'definition': 'Distant in space or time',
                'frame': 'spatial',
                'organism_relevance': 0.9,
                'associations': ['distant', 'remote', 'away', 'distant', 'separated', 'isolated', 'beyond'],
                'contexts': ['exploration', 'isolation', 'safety', 'target'],
                'abstraction_level': 0
            },
            'center': {
                'definition': 'At the central position or core',
                'frame': 'spatial',
                'organism_relevance': 0.8,
                'associations': ['core', 'middle', 'heart', 'focal', 'central', 'hub'],
                'contexts': ['position', 'awareness', 'stability'],
                'abstraction_level': 0
            },
            'edge': {
                'definition': 'At the boundary or periphery',
                'frame': 'spatial',
                'organism_relevance': 0.8,
                'associations': ['boundary', 'periphery', 'margin', 'border', 'limit'],
                'contexts': ['position', 'exploration', 'risk'],
                'abstraction_level': 0
            },
            'crowded': {
                'definition': 'High density of organisms or entities',
                'frame': 'spatial',
                'organism_relevance': 0.9,
                'associations': ['dense', 'packed', 'populated', 'concentrated', 'thick'],
                'contexts': ['density', 'competition', 'social'],
                'abstraction_level': 0
            },
            'dense': {
                'definition': 'High concentration or density',
                'frame': 'spatial',
                'organism_relevance': 0.8,
                'associations': ['crowded', 'packed', 'concentrated', 'thick', 'compact'],
                'contexts': ['density', 'environment'],
                'abstraction_level': 0
            },
            'sparse': {
                'definition': 'Low density or concentration',
                'frame': 'spatial',
                'organism_relevance': 0.8,
                'associations': ['thin', 'scattered', 'dispersed', 'isolated', 'rare'],
                'contexts': ['density', 'isolation', 'exploration'],
                'abstraction_level': 0
            }
        }
        
        # Meta-Cognitive Concepts (thinking about thinking)
        metacognitive_concepts = {
            'know': {
                'definition': 'To have understanding or awareness',
                'frame': 'meta',
                'organism_relevance': 0.9,
                'associations': ['understand', 'aware', 'recognize', 'comprehend', 'perceive', 'realize', 'grasp'],
                'contexts': ['learning', 'memory', 'awareness', 'comprehension'],
                'abstraction_level': 2
            },
            'think': {
                'definition': 'To use mental processes and reasoning',
                'frame': 'meta',
                'organism_relevance': 0.9,
                'associations': ['reason', 'consider', 'contemplate', 'reflect', 'ponder', 'analyze', 'process'],
                'contexts': ['decision_making', 'planning', 'reasoning', 'comprehension'],
                'abstraction_level': 2
            },
            'learn': {
                'definition': 'To acquire knowledge or skill through experience',
                'frame': 'meta',
                'organism_relevance': 1.0,
                'associations': ['acquire', 'gain', 'develop', 'adapt', 'evolve', 'improve', 'grow'],
                'contexts': ['experience', 'training', 'adaptation', 'evolution'],
                'abstraction_level': 2
            },
            'remember': {
                'definition': 'To recall or retain information from the past',
                'frame': 'meta',
                'organism_relevance': 0.9,
                'associations': ['recall', 'retain', 'memorize', 'store', 'keep', 'preserve', 'maintain'],
                'contexts': ['memory', 'experience', 'learning', 'causation'],
                'abstraction_level': 2
            },
            'understand': {
                'definition': 'To comprehend meaning and significance',
                'frame': 'meta',
                'organism_relevance': 1.0,
                'associations': ['comprehend', 'grasp', 'realize', 'perceive', 'recognize', 'know', 'appreciate'],
                'contexts': ['comprehension', 'awareness', 'insight', 'reasoning'],
                'abstraction_level': 2
            }
        }
        
        # System Dynamics Concepts (VP, health, stability)
        system_concepts = {
            'pressure': {
                'definition': 'System stress or violation pressure',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['stress', 'tension', 'crisis', 'unstable', 'violation'],
                'contexts': ['vp_high', 'instability', 'crisis'],
                'abstraction_level': 1
            },
            'crisis': {
                'definition': 'Critical system instability or danger',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['emergency', 'danger', 'unstable', 'pressure', 'collapse'],
                'contexts': ['vp_high', 'instability', 'survival'],
                'abstraction_level': 1
            },
            'stress': {
                'definition': 'System tension or pressure',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['pressure', 'tension', 'strain', 'unstable'],
                'contexts': ['vp_high', 'instability'],
                'abstraction_level': 1
            },
            'calm': {
                'definition': 'Peaceful and stable state',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['peaceful', 'stable', 'balanced', 'serene'],
                'contexts': ['vp_low', 'stability', 'equilibrium'],
                'abstraction_level': 1
            },
            'balanced': {
                'definition': 'In equilibrium or harmony',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['equilibrium', 'stable', 'harmonious', 'calm'],
                'contexts': ['vp_low', 'stability', 'coherence'],
                'abstraction_level': 1
            },
            'connected': {
                'definition': 'Linked or integrated with network',
                'frame': 'relationship',
                'organism_relevance': 1.0,
                'associations': ['linked', 'integrated', 'united', 'networked'],
                'contexts': ['coherence', 'social', 'network'],
                'abstraction_level': 1
            },
            'united': {
                'definition': 'Joined together as one',
                'frame': 'relationship',
                'organism_relevance': 0.9,
                'associations': ['together', 'connected', 'coherent', 'integrated'],
                'contexts': ['coherence', 'cooperation'],
                'abstraction_level': 1
            },
            'coherent': {
                'definition': 'Logically consistent and integrated',
                'frame': 'quality',
                'organism_relevance': 0.9,
                'associations': ['consistent', 'integrated', 'unified', 'connected'],
                'contexts': ['coherence', 'stability'],
                'abstraction_level': 1
            },
            'fragmented': {
                'definition': 'Broken into disconnected parts',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['broken', 'disconnected', 'separated', 'isolated'],
                'contexts': ['low_coherence', 'instability'],
                'abstraction_level': 1
            },
            'disconnected': {
                'definition': 'Not linked or separated',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['separated', 'isolated', 'fragmented', 'broken'],
                'contexts': ['low_coherence', 'isolation'],
                'abstraction_level': 1
            },
            'adapt': {
                'definition': 'To adjust to changing conditions',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['adjust', 'change', 'evolve', 'modify', 'learn'],
                'contexts': ['evolution_pressure', 'change', 'survival'],
                'abstraction_level': 1
            },
            'evolve': {
                'definition': 'To develop and change over time',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['develop', 'adapt', 'change', 'grow', 'improve'],
                'contexts': ['evolution_pressure', 'growth', 'development'],
                'abstraction_level': 1
            },
            'change': {
                'definition': 'To become different',
                'frame': 'action',
                'organism_relevance': 0.9,
                'associations': ['modify', 'adapt', 'transform', 'evolve'],
                'contexts': ['evolution_pressure', 'adaptation'],
                'abstraction_level': 1
            },
            'persist': {
                'definition': 'To continue despite difficulty',
                'frame': 'action',
                'organism_relevance': 0.9,
                'associations': ['endure', 'continue', 'maintain', 'survive'],
                'contexts': ['stability', 'survival', 'resilience'],
                'abstraction_level': 1
            },
            'mismatch': {
                'definition': 'Lack of alignment or synchronization',
                'frame': 'state',
                'organism_relevance': 0.8,
                'associations': ['misaligned', 'desynchronized', 'conflict', 'discord'],
                'contexts': ['phase_mismatch', 'instability'],
                'abstraction_level': 1
            },
            'desynchronized': {
                'definition': 'Not synchronized or aligned',
                'frame': 'state',
                'organism_relevance': 0.8,
                'associations': ['mismatch', 'misaligned', 'conflict', 'discord'],
                'contexts': ['phase_mismatch', 'instability'],
                'abstraction_level': 1
            },
            'healthy': {
                'definition': 'In good condition or wellness',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['well', 'thriving', 'flourish', 'strong', 'vital'],
                'contexts': ['system_health', 'wellness', 'survival'],
                'abstraction_level': 1
            },
            'thriving': {
                'definition': 'Prospering and flourishing',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['flourish', 'prosper', 'healthy', 'success', 'grow'],
                'contexts': ['system_health', 'success', 'growth'],
                'abstraction_level': 1
            },
            'sick': {
                'definition': 'In poor condition or unwell',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['unwell', 'declining', 'weak', 'failing', 'struggle'],
                'contexts': ['system_health', 'decline', 'struggle'],
                'abstraction_level': 1
            },
            'declining': {
                'definition': 'Deteriorating or decreasing',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['deteriorating', 'decreasing', 'failing', 'struggle', 'sick'],
                'contexts': ['system_health', 'decline', 'struggle'],
                'abstraction_level': 1
            },
            'expand': {
                'definition': 'To grow or increase in size',
                'frame': 'action',
                'organism_relevance': 0.9,
                'associations': ['grow', 'increase', 'spread', 'extend', 'multiply'],
                'contexts': ['breath_inhale', 'growth', 'exploration'],
                'abstraction_level': 1
            },
            'consolidate': {
                'definition': 'To strengthen or stabilize',
                'frame': 'action',
                'organism_relevance': 0.9,
                'associations': ['strengthen', 'stabilize', 'solidify', 'unify'],
                'contexts': ['breath_exhale', 'stability', 'rest'],
                'abstraction_level': 1
            },
            'precise': {
                'definition': 'Exact and accurate',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['exact', 'accurate', 'focused', 'targeted'],
                'contexts': ['sovereign_phase', 'precision'],
                'abstraction_level': 1
            },
            'focused': {
                'definition': 'Concentrated and directed',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['concentrated', 'directed', 'precise', 'targeted'],
                'contexts': ['sovereign_phase', 'precision'],
                'abstraction_level': 1
            },
            'discover': {
                'definition': 'To find or learn something new',
                'frame': 'action',
                'organism_relevance': 0.9,
                'associations': ['find', 'explore', 'learn', 'uncover', 'reveal'],
                'contexts': ['genesis_phase', 'exploration', 'learning'],
                'abstraction_level': 1
            },
            'success': {
                'definition': 'Achievement of desired outcome',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['achievement', 'victory', 'triumph', 'effective'],
                'contexts': ['action_success', 'achievement'],
                'abstraction_level': 1
            },
            'effective': {
                'definition': 'Producing desired result',
                'frame': 'quality',
                'organism_relevance': 0.9,
                'associations': ['successful', 'efficient', 'productive', 'success'],
                'contexts': ['action_success', 'efficiency'],
                'abstraction_level': 1
            },
            'failure': {
                'definition': 'Lack of success or effectiveness',
                'frame': 'state',
                'organism_relevance': 0.9,
                'associations': ['unsuccessful', 'ineffective', 'defeat', 'loss'],
                'contexts': ['action_failure', 'struggle'],
                'abstraction_level': 1
            },
            'ineffective': {
                'definition': 'Not producing desired result',
                'frame': 'quality',
                'organism_relevance': 0.9,
                'associations': ['unsuccessful', 'inefficient', 'failure', 'weak'],
                'contexts': ['action_failure', 'inefficiency'],
                'abstraction_level': 1
            },
            'mature': {
                'definition': 'Fully developed or experienced',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['developed', 'experienced', 'grown', 'aged'],
                'contexts': ['generation_age', 'development'],
                'abstraction_level': 1
            },
            'experienced': {
                'definition': 'Having knowledge from experience',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['knowledgeable', 'skilled', 'mature', 'wise'],
                'contexts': ['generation_age', 'learning'],
                'abstraction_level': 1
            },
            'young': {
                'definition': 'Early in development or age',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['new', 'fresh', 'early', 'beginning'],
                'contexts': ['generation_age', 'development'],
                'abstraction_level': 1
            },
            'new': {
                'definition': 'Recently created or beginning',
                'frame': 'quality',
                'organism_relevance': 0.8,
                'associations': ['fresh', 'young', 'recent', 'beginning'],
                'contexts': ['generation_age', 'creation'],
                'abstraction_level': 1
            },
            'exist': {
                'definition': 'To be or have being',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['be', 'live', 'persist', 'endure'],
                'contexts': ['basic', 'fundamental'],
                'abstraction_level': 0
            },
            'be': {
                'definition': 'To exist or have identity',
                'frame': 'state',
                'organism_relevance': 1.0,
                'associations': ['exist', 'live', 'persist', 'endure'],
                'contexts': ['basic', 'fundamental'],
                'abstraction_level': 0
            },
            'act': {
                'definition': 'To take action or behave',
                'frame': 'action',
                'organism_relevance': 1.0,
                'associations': ['behave', 'perform', 'do', 'execute'],
                'contexts': ['basic', 'fundamental'],
                'abstraction_level': 0
            }
        }
        
        # Combine all concepts
        all_concepts = {
            **action_concepts,
            **state_concepts,
            **quality_concepts,
            **relationship_concepts,
            **temporal_concepts,
            **spatial_concepts,
            **metacognitive_concepts,
            **system_concepts
        }
        
        # Create concept objects
        for word, data in all_concepts.items():
            concept = LinguisticConcept(
                word=word,
                definition=data['definition'],
                semantic_frame=data['frame'],
                organism_relevance=data['organism_relevance'],
                associations=data['associations'],
                contexts=data['contexts'],
                abstraction_level=data['abstraction_level']
            )
            self.concepts[word] = concept
            self.word_to_concept[word] = word
        
        # Add associations as separate concepts if not already present
        # Convert to list to avoid "dictionary changed size during iteration" error
        for word, concept in list(self.concepts.items()):
            for assoc in concept.associations:
                if assoc not in self.concepts:
                    # Create lightweight concept for association
                    self.concepts[assoc] = LinguisticConcept(
                        word=assoc,
                        definition=f'Related to {word}',
                        semantic_frame=concept.semantic_frame,
                        organism_relevance=concept.organism_relevance * 0.8,  # Slightly less relevant
                        associations=[word],  # Bidirectional
                        contexts=concept.contexts,
                        abstraction_level=concept.abstraction_level
                    )
                    self.word_to_concept[assoc] = assoc
        
        # ============================================================
        # SEMANTIC RELATIONSHIPS
        # ============================================================
        
        # Synonym relationships (similar meaning)
        synonym_pairs = [
            ('move', 'explore'), ('move', 'travel'), ('move', 'wander'),
            ('cooperate', 'collaborate'), ('cooperate', 'help'), ('cooperate', 'share'),
            ('compete', 'fight'), ('compete', 'challenge'), ('compete', 'rival'),
            ('rest', 'pause'), ('rest', 'recover'), ('rest', 'sleep'),
            ('reproduce', 'grow'), ('reproduce', 'multiply'), ('reproduce', 'expand'),
            ('isolate', 'withdraw'), ('isolate', 'separate'), ('isolate', 'retreat'),
            ('thrive', 'flourish'), ('thrive', 'prosper'), ('thrive', 'succeed'),
            ('struggle', 'suffer'), ('struggle', 'decline'), ('struggle', 'endure'),
            ('social', 'connected'), ('social', 'networked'), ('social', 'linked'),
            ('isolated', 'alone'), ('isolated', 'solitary'), ('isolated', 'independent'),
            ('rich', 'abundant'), ('rich', 'wealthy'), ('rich', 'plentiful'),
            ('poor', 'scarce'), ('poor', 'depleted'), ('poor', 'needy'),
            ('strong', 'powerful'), ('strong', 'capable'), ('strong', 'robust'),
            ('weak', 'vulnerable'), ('weak', 'fragile'), ('weak', 'limited'),
            ('together', 'united'), ('together', 'cooperative'), ('together', 'allied'),
            ('alone', 'isolated'), ('alone', 'solitary'), ('alone', 'independent'),
            ('help', 'assist'), ('help', 'support'), ('help', 'aid'),
            ('share', 'distribute'), ('share', 'exchange'), ('share', 'give'),
            ('know', 'understand'), ('know', 'recognize'), ('know', 'comprehend'),
            ('think', 'reason'), ('think', 'consider'), ('think', 'contemplate'),
            ('learn', 'acquire'), ('learn', 'develop'), ('learn', 'adapt'),
            ('remember', 'recall'), ('remember', 'retain'), ('remember', 'memorize'),
            ('understand', 'comprehend'), ('understand', 'grasp'), ('understand', 'realize')
        ]
        
        for source, target in synonym_pairs:
            self._add_relation(source, target, 'synonym', strength=0.9)
            self._add_relation(target, source, 'synonym', strength=0.9)  # Bidirectional
        
        # Antonym relationships (opposite meaning)
        antonym_pairs = [
            ('thrive', 'struggle'), ('strong', 'weak'), ('rich', 'poor'),
            ('social', 'isolated'), ('together', 'alone'), ('help', 'harm'),
            ('fast', 'slow'), ('near', 'far'), ('here', 'there'),
            ('now', 'before'), ('now', 'after'), ('always', 'never'),
            ('move', 'rest'), ('cooperate', 'compete'), ('reproduce', 'isolate')
        ]
        
        for source, target in antonym_pairs:
            self._add_relation(source, target, 'antonym', strength=0.8)
            self._add_relation(target, source, 'antonym', strength=0.8)  # Bidirectional
        
        # Causal relationships (causes/enables/prevents)
        causal_relations = [
            ('cooperate', 'social', 'causes'),
            ('cooperate', 'together', 'causes'),
            ('cooperate', 'help', 'enables'),
            ('cooperate', 'share', 'enables'),
            ('compete', 'struggle', 'causes'),
            ('compete', 'conflict', 'causes'),
            ('rest', 'recover', 'enables'),
            ('rest', 'stability', 'enables'),
            ('reproduce', 'grow', 'causes'),
            ('reproduce', 'expand', 'causes'),
            ('isolate', 'alone', 'causes'),
            ('isolate', 'independent', 'enables'),
            ('thrive', 'strong', 'causes'),
            ('thrive', 'success', 'causes'),
            ('struggle', 'weak', 'causes'),
            ('struggle', 'decline', 'causes'),
            ('social', 'cooperate', 'enables'),
            ('social', 'together', 'enables'),
            ('isolated', 'alone', 'causes'),
            ('isolated', 'independent', 'enables'),
            ('rich', 'thrive', 'enables'),
            ('rich', 'security', 'causes'),
            ('poor', 'struggle', 'causes'),
            ('poor', 'vulnerability', 'causes'),
            ('learn', 'know', 'causes'),
            ('learn', 'understand', 'causes'),
            ('think', 'know', 'enables'),
            ('think', 'understand', 'enables'),
            ('remember', 'know', 'enables'),
            ('remember', 'learn', 'enables')
        ]
        
        for source, target, rel_type in causal_relations:
            self._add_relation(source, target, rel_type, strength=0.7)
        
        # Similarity relationships (related concepts)
        similarity_groups = [
            ['move', 'explore', 'travel', 'wander', 'journey'],
            ['cooperate', 'collaborate', 'help', 'share', 'assist'],
            ['compete', 'fight', 'challenge', 'rival', 'conflict'],
            ['thrive', 'flourish', 'prosper', 'succeed', 'excel'],
            ['struggle', 'suffer', 'decline', 'endure', 'persist'],
            ['social', 'connected', 'networked', 'linked', 'integrated'],
            ['isolated', 'alone', 'solitary', 'independent', 'autonomous'],
            ['know', 'understand', 'comprehend', 'grasp', 'realize'],
            ['think', 'reason', 'consider', 'contemplate', 'reflect'],
            ['learn', 'acquire', 'develop', 'adapt', 'evolve']
        ]
        
        for group in similarity_groups:
            for i, word1 in enumerate(group):
                for word2 in group[i+1:]:
                    self._add_relation(word1, word2, 'similar_to', strength=0.8)
                    self._add_relation(word2, word1, 'similar_to', strength=0.8)
        
        # Part-of relationships (hierarchical)
        part_of_relations = [
            ('help', 'cooperate', 'part_of'),
            ('share', 'cooperate', 'part_of'),
            ('collaborate', 'cooperate', 'part_of'),
            ('fight', 'compete', 'part_of'),
            ('challenge', 'compete', 'part_of'),
            ('explore', 'move', 'part_of'),
            ('travel', 'move', 'part_of'),
            ('recover', 'rest', 'part_of'),
            ('pause', 'rest', 'part_of'),
            ('grow', 'reproduce', 'part_of'),
            ('multiply', 'reproduce', 'part_of')
        ]
        
        for source, target, rel_type in part_of_relations:
            self._add_relation(source, target, rel_type, strength=0.6)
        
        # Build semantic clusters
        self._build_semantic_clusters()
        
        # Build organism-behavior mappings
        self._build_organism_mappings()
        
        logger.info(f"[LINGUISTIC_WEB] Initialized: {len(self.concepts)} concepts, {len(self.relations)} relations, {len(self.semantic_clusters)} clusters")
    
    def _add_relation(self, source: str, target: str, relation_type: str, 
                     strength: float = 1.0, context: Optional[str] = None,
                     confidence: float = 0.9, is_seeded: bool = True,
                     generation: int = 0):
        """Add a semantic relation."""
        relation = SemanticRelation(
            source=source,
            target=target,
            relation_type=relation_type,
            strength=strength,
            context=context,
            confidence=confidence,
            is_seeded=is_seeded,
            generation_discovered=generation,
            last_used=generation
        )
        self.relations.append(relation)
        self.relation_index[source].append(relation)
        self.relation_index[target].append(relation)
    
    def discover_relationship(self, 
                            word1: str, 
                            word2: str, 
                            context: Optional[Dict[str, Any]] = None,
                            strength: float = 0.5,
                            generation: int = 0,
                            vp_value: float = 0.0) -> bool:
        """
        Discover new relationship from organism behavior (recursive expansion).
        
        Called when organisms use words together in similar contexts.
        Enables infinite possibility from finite structure.
        
        Args:
            word1: First word
            word2: Second word
            context: Contextual information about the discovery
            strength: Initial strength of discovered relationship
            generation: Current generation number
            vp_value: Current violation pressure value
            
        Returns:
            True if relationship was discovered/strengthened, False otherwise
        """
        # Check discovery cap
        discovered_this_gen = sum(1 for r in self.discovered_relations 
                                 if r.generation_discovered == generation)
        if discovered_this_gen >= self.max_discoveries_per_generation:
            return False  # Cap reached
        
        # VP-aware exploration boost
        effective_exploration = self.exploration_rate
        if self.vp_boost_exploration and vp_value > self.vp_boost_threshold:
            effective_exploration = min(1.0, self.exploration_rate * 1.5)  # Boost by 50%
        
        # Check if relationship already exists
        existing = [r for r in self.get_relations(word1)
                   if r.target == word2 or (r.source == word2 and r.target == word1)]
        
        if existing:
            # Strengthen existing relationship (recursive reinforcement)
            for rel in existing:
                rel.strength = min(1.0, rel.strength + 0.05)  # Small increment
                rel.discovery_count += 1
                rel.last_used = generation
            return True
        
        # Track discovery attempt
        word_pair = (min(word1, word2), max(word1, word2))  # Normalize order
        self.discovery_attempts[word_pair] += 1
        
        # Validate relationship before accepting
        if context is None:
            context = {}
        is_valid, confidence_score = self.validate_relationship(word1, word2, context)
        
        # Frequency-based validation: require minimum co-occurrence count
        if self.discovery_attempts[word_pair] < self.min_discovery_count:
            return False  # Not enough co-occurrences yet
        
        # Check confidence threshold (adaptive based on generation)
        if confidence_score < self.confidence_threshold:
            return False  # Doesn't meet quality bar
        
        # Accept discovery
        self.successful_validations[word_pair] += 1
        
        # Create new discovered relationship (recursive expansion)
        self._add_relation(
            source=word1,
            target=word2,
            relation_type='discovered',  # New type for organism-discovered relationships
            strength=strength,
            context=str(context) if context else None,
            confidence=confidence_score,  # Initial confidence from validation
            is_seeded=False,  # Mark as discovered, not seeded
            generation=generation
        )
        # Mark as discovered
        relation = self.relations[-1]
        relation.metadata['discovered'] = True
        relation.metadata['discovery_context'] = context
        self.discovered_relations.append(relation)
        
        # Track context for coherence validation
        if context and 'organism_state' in context:
            self.word_context_history[word1].append(context)
            self.word_context_history[word2].append(context)
            # Keep only last 50 contexts per word
            if len(self.word_context_history[word1]) > 50:
                self.word_context_history[word1] = self.word_context_history[word1][-50:]
            if len(self.word_context_history[word2]) > 50:
                self.word_context_history[word2] = self.word_context_history[word2][-50:]
        
        logger.info(f"[LINGUISTIC_WEB] Discovered relationship: {word1} → {word2} "
                   f"(strength={strength:.2f}, confidence={confidence_score:.2f}, gen={generation})")
        return True
    
    def decay_relationships(self, generation: int, pruning_confidence_threshold: float = 0.2,
                           pruning_unused_generations: int = 100, pruning_failure_rate: float = 0.7):
        """
        Weaken unused relationships to prevent yarn ball (recursive pruning).
        
        Prevents over-stimulation by allowing weak connections to fade.
        Enables system to forget and rediscover.
        
        NEVER prunes seeded relationships (is_seeded=True).
        Only prunes discovered relationships that fail quality checks.
        
        Args:
            generation: Current generation number
            pruning_confidence_threshold: Minimum confidence to keep (default: 0.2)
            pruning_unused_generations: Remove if unused for N generations (default: 100)
            pruning_failure_rate: Remove if failure rate > threshold (default: 0.7)
        """
        relations_to_remove = []
        
        for relation in self.relations:
            # NEVER prune seeded relationships
            if relation.is_seeded:
                continue
            
            # Only process discovered relationships
            if relation.relation_type != 'discovered':
                continue
            
            # Get usage count
            usage = self.relation_usage_counts.get(
                (relation.source, relation.target, relation.relation_type), 0
            )
            
            # Calculate failure rate
            total_uses = relation.success_count + relation.failure_count
            failure_rate = relation.failure_count / total_uses if total_uses > 0 else 0.0
            
            # Check pruning criteria
            should_prune = False
            prune_reason = ""
            
            # 1. Very low confidence
            if relation.confidence < pruning_confidence_threshold:
                should_prune = True
                prune_reason = f"low_confidence({relation.confidence:.2f})"
            
            # 2. Unused for many generations
            generations_unused = generation - relation.last_used
            if generations_unused > pruning_unused_generations:
                should_prune = True
                prune_reason = f"unused({generations_unused}gens)"
            
            # 3. High failure rate
            if failure_rate > pruning_failure_rate:
                should_prune = True
                prune_reason = f"high_failure_rate({failure_rate:.2f})"
            
            if should_prune:
                relations_to_remove.append((relation, prune_reason))
            elif usage == 0:
                # Decay unused discovered relationships gradually
                relation.strength *= (1.0 - self.decay_rate)
                relation.confidence = max(0.0, relation.confidence - 0.01)  # Gradual confidence decay
        
        # Remove weak relationships
        for relation, reason in relations_to_remove:
            self.relations.remove(relation)
            if relation in self.relation_index[relation.source]:
                self.relation_index[relation.source].remove(relation)
            if relation in self.relation_index[relation.target]:
                self.relation_index[relation.target].remove(relation)
            if relation in self.discovered_relations:
                self.discovered_relations.remove(relation)
        
        if relations_to_remove:
            logger.info(f"[LINGUISTIC_WEB] Pruned {len(relations_to_remove)} low-quality relationships "
                       f"(reasons: {', '.join(set(r[1] for r in relations_to_remove))})")
    
    def record_relationship_usage(self, word1: str, word2: str, relation_type: str, generation: int):
        """Record that a relationship was used."""
        relation_key = (word1, word2, relation_type)
        self.relation_usage_counts[relation_key] += 1
        
        # Update last_used for matching relations
        for relation in self.get_relations(word1):
            if (relation.target == word2 or relation.source == word2) and relation.relation_type == relation_type:
                relation.last_used = generation
    
    def record_relationship_success(self, word1: str, word2: str, relation_type: str):
        """
        Record that a relationship led to a successful/good response.
        
        Updates confidence and strength positively.
        """
        for relation in self.get_relations(word1):
            if (relation.target == word2 or relation.source == word2) and relation.relation_type == relation_type:
                relation.success_count += 1
                # Asymmetric: success increases confidence more than strength
                relation.confidence = min(1.0, relation.confidence + 0.1)
                relation.strength = min(1.0, relation.strength + 0.05)
                break
    
    def record_relationship_failure(self, word1: str, word2: str, relation_type: str):
        """
        Record that a relationship led to a poor/failed response.
        
        Updates confidence and strength negatively (asymmetric - failure costs more).
        """
        for relation in self.get_relations(word1):
            if (relation.target == word2 or relation.source == word2) and relation.relation_type == relation_type:
                relation.failure_count += 1
                # Asymmetric: failure decreases confidence more than strength
                relation.confidence = max(0.0, relation.confidence - 0.15)
                relation.strength = max(0.1, relation.strength - 0.1)
                break
    
    def _build_semantic_clusters(self):
        """Build semantic clusters for associative reasoning."""
        # Cluster by semantic frame
        for word, concept in self.concepts.items():
            self.semantic_clusters[concept.semantic_frame].add(word)
        
        # Cluster by organism relevance
        high_relevance = {w for w, c in self.concepts.items() if c.organism_relevance >= 0.9}
        medium_relevance = {w for w, c in self.concepts.items() if 0.7 <= c.organism_relevance < 0.9}
        low_relevance = {w for w, c in self.concepts.items() if c.organism_relevance < 0.7}
        
        self.semantic_clusters['high_relevance'] = high_relevance
        self.semantic_clusters['medium_relevance'] = medium_relevance
        self.semantic_clusters['low_relevance'] = low_relevance
    
    def _build_organism_mappings(self):
        """
        Build organism-behavior mappings.
        
        UPDATED: Now uses semantic seeding from 50k vocabulary instead of
        hardcoded word lists. Each organism gets DIFFERENT words based on
        their unique seed, with category biasing for causal coordination.
        """
        # Core action words (these are the "anchor" words - organisms can earn more)
        self.action_word_map = {
            0: ['move', 'explore', 'travel', 'wander', 'journey'],
            1: ['cooperate', 'collaborate', 'help', 'share', 'assist'],
            2: ['compete', 'fight', 'challenge', 'rival', 'conflict'],
            3: ['rest', 'pause', 'recover', 'sleep', 'wait'],
            4: ['reproduce', 'grow', 'multiply', 'spread', 'expand'],
            5: ['isolate', 'withdraw', 'separate', 'retreat', 'alone']
        }
        
        # Core state words (anchor words)
        self.state_word_map = {
            'high_fitness': ['thrive', 'flourish', 'prosper', 'succeed', 'strong'],
            'low_fitness': ['struggle', 'suffer', 'decline', 'weak', 'failing'],
            'medium_fitness': ['stable', 'survive', 'endure', 'persist', 'balanced'],
            'many_connections': ['social', 'connected', 'networked', 'linked', 'together'],
            'few_connections': ['isolated', 'alone', 'separate', 'disconnected', 'lonely'],
            'no_connections': ['solitary', 'independent', 'autonomous', 'alone', 'isolated'],
            'high_resources': ['rich', 'abundant', 'plentiful', 'wealthy', 'sustained'],
            'low_resources': ['poor', 'scarce', 'depleted', 'starving', 'needy'],
            'medium_resources': ['moderate', 'adequate', 'sufficient', 'stable', 'balanced']
        }
        
        # Situational contexts (anchor contexts)
        self.situational_contexts = {
            'exploration': ['move', 'explore', 'travel', 'wander', 'discover', 'search'],
            'cooperation': ['cooperate', 'help', 'share', 'collaborate', 'assist', 'together'],
            'competition': ['compete', 'fight', 'challenge', 'rival', 'conflict', 'struggle'],
            'recovery': ['rest', 'pause', 'recover', 'sleep', 'recharge', 'calm'],
            'growth': ['reproduce', 'grow', 'multiply', 'expand', 'spread', 'thrive'],
            'isolation': ['isolate', 'withdraw', 'separate', 'retreat', 'alone', 'independent'],
            'success': ['thrive', 'succeed', 'flourish', 'prosper', 'excel', 'strong'],
            'struggle': ['struggle', 'suffer', 'decline', 'endure', 'persist', 'weak'],
            'social': ['social', 'connected', 'networked', 'together', 'cooperative', 'united'],
            'learning': ['learn', 'acquire', 'develop', 'adapt', 'evolve', 'understand']
        }
        
        # Category affinities for semantic seeding
        # Maps action types and states to vocabulary categories they should pull from
        self._action_category_affinities = {
            0: ['behavior', 'spatial', 'perception'],  # move -> behavior, spatial awareness
            1: ['social', 'communication', 'governance'],  # cooperate -> social, communication
            2: ['behavior', 'survival', 'causal'],  # compete -> survival, aggression
            3: ['temporal', 'cognition', 'perception'],  # rest -> temporal, recovery
            4: ['survival', 'temporal', 'causal'],  # reproduce -> survival, growth
            5: ['spatial', 'perception', 'cognition']  # isolate -> spatial, introspection
        }
        
        self._state_category_affinities = {
            'high_fitness': ['survival', 'behavior', 'social'],
            'low_fitness': ['survival', 'causal', 'temporal'],
            'medium_fitness': ['cognition', 'temporal', 'perception'],
            'many_connections': ['social', 'communication', 'governance'],
            'few_connections': ['cognition', 'spatial', 'perception'],
            'no_connections': ['spatial', 'cognition', 'survival'],
            'high_resources': ['survival', 'social', 'behavior'],
            'low_resources': ['survival', 'causal', 'behavior'],
            'medium_resources': ['cognition', 'temporal', 'behavior']
        }

    def seed_organism_vocabulary(self, organism_id: str, 
                                  initial_action: Optional[int] = None,
                                  initial_state: Optional[str] = None,
                                  num_words: int = 500) -> Set[str]:
        """
        Seed an organism with a UNIQUE vocabulary based on its identity.
        
        This is SEMANTIC SEEDING: random yet causally coordinated inseminations
        meant to connect organisms and agitate convergence on ideation.
        
        Organisms can KNOW up to 1000 words (vocab storage) but only PROCESS
        ~64-128 tokens at a time (context window). Like humans knowing 20k words
        but only using 100-200 in a conversation. Rich vocabulary = more choices.
        
        Args:
            organism_id: Unique organism identifier (used as seed)
            initial_action: Starting action type (0-5)
            initial_state: Starting state type
            num_words: How many words to seed (default 500 = 50% of capacity)
            
        Returns:
            Set of seeded words unique to this organism
        """
        if not self.curated_vocabulary:
            # Fallback to hardcoded words if vocabulary not loaded
            return set()
        
        # Use organism ID as deterministic seed for reproducible but diverse vocabulary
        seed_hash = int(hashlib.md5(organism_id.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed_hash)
        
        seeded_words = set()
        
        # ============================================================
        # PHASE 1: Category-biased seeding (causally coordinated)
        # ============================================================
        category_pool = []
        
        # Add words from action-related categories
        if initial_action is not None and initial_action in self._action_category_affinities:
            for category in self._action_category_affinities[initial_action]:
                if category in self.vocabulary_categories:
                    category_pool.extend(self.vocabulary_categories[category])
        
        # Add words from state-related categories
        if initial_state and initial_state in self._state_category_affinities:
            for category in self._state_category_affinities[initial_state]:
                if category in self.vocabulary_categories:
                    category_pool.extend(self.vocabulary_categories[category])
        
        # Sample from category pool (40% of words)
        category_words_count = int(num_words * 0.4)
        if category_pool:
            category_pool = list(set(category_pool))  # Dedupe
            rng.shuffle(category_pool)
            seeded_words.update(category_pool[:category_words_count])
        
        # ============================================================
        # PHASE 2: Bridging words (for cross-organism convergence)
        # ============================================================
        # Sample from ALL categories to create semantic bridges
        all_categorized = []
        for category, words in self.vocabulary_categories.items():
            if category != 'other':  # Skip the massive 'other' category
                all_categorized.extend(words)
        
        bridge_words_count = int(num_words * 0.3)
        if all_categorized:
            all_categorized = list(set(all_categorized) - seeded_words)  # Exclude already seeded
            rng.shuffle(all_categorized)
            seeded_words.update(all_categorized[:bridge_words_count])
        
        # ============================================================
        # PHASE 3: Random exploration (agitation for ideation)
        # ============================================================
        # Sample from entire 50k vocabulary for wild card words
        exploration_count = num_words - len(seeded_words)
        if exploration_count > 0:
            available = [w for w in self.curated_vocabulary if w not in seeded_words]
            rng.shuffle(available)
            seeded_words.update(available[:exploration_count])
        
        # Store organism's seed vocabulary
        self.organism_word_seeds[organism_id] = seeded_words
        
        logger.debug(f"[SEMANTIC_SEED] Organism {organism_id[:8]} seeded with {len(seeded_words)} unique words")
        
        return seeded_words

    def get_words_for_action_dynamic(self, action_idx: int, organism_id: Optional[str] = None) -> List[str]:
        """
        Get words for an action with organism-specific semantic seeding.
        
        Unlike the static `get_words_for_action`, this returns DIFFERENT words
        for different organisms based on their seed vocabulary.
        
        Args:
            action_idx: Action type (0-5)
            organism_id: Organism identifier for personalized words
            
        Returns:
            List of words relevant to the action (different per organism)
        """
        # Always include anchor words
        base_words = list(self.action_word_map.get(action_idx, []))
        
        if not organism_id or not self.curated_vocabulary:
            return base_words
        
        # Get or create organism's seed vocabulary
        if organism_id not in self.organism_word_seeds:
            self.seed_organism_vocabulary(organism_id, initial_action=action_idx)
        
        # Add words from organism's seed that are in relevant categories
        organism_words = self.organism_word_seeds.get(organism_id, set())
        
        if action_idx in self._action_category_affinities:
            relevant_categories = self._action_category_affinities[action_idx]
            for word in organism_words:
                word_category = self.word_to_category.get(word, 'other')
                if word_category in relevant_categories:
                    base_words.append(word)
        
        # Also add a few random seeded words for exploration
        remaining = list(organism_words - set(base_words))
        if remaining:
            random.shuffle(remaining)
            base_words.extend(remaining[:3])  # Add 3 random seeded words
        
        return base_words

    def get_words_for_state_dynamic(self, state_type: str, organism_id: Optional[str] = None) -> List[str]:
        """
        Get words for a state with organism-specific semantic seeding.
        
        Unlike the static `get_words_for_state`, this returns DIFFERENT words
        for different organisms based on their seed vocabulary.
        
        Args:
            state_type: State type string
            organism_id: Organism identifier for personalized words
            
        Returns:
            List of words relevant to the state (different per organism)
        """
        # Always include anchor words
        base_words = list(self.state_word_map.get(state_type, []))
        
        if not organism_id or not self.curated_vocabulary:
            return base_words
        
        # Get or create organism's seed vocabulary
        if organism_id not in self.organism_word_seeds:
            self.seed_organism_vocabulary(organism_id, initial_state=state_type)
        
        # Add words from organism's seed that are in relevant categories
        organism_words = self.organism_word_seeds.get(organism_id, set())
        
        if state_type in self._state_category_affinities:
            relevant_categories = self._state_category_affinities[state_type]
            for word in organism_words:
                word_category = self.word_to_category.get(word, 'other')
                if word_category in relevant_categories:
                    base_words.append(word)
        
        # Also add a few random seeded words for exploration
        remaining = list(organism_words - set(base_words))
        if remaining:
            random.shuffle(remaining)
            base_words.extend(remaining[:3])  # Add 3 random seeded words
        
        return base_words
    
    def get_concept(self, word: str) -> Optional[LinguisticConcept]:
        """Get concept for a word."""
        return self.concepts.get(word)
    
    def get_relations(self, word: str, relation_type: Optional[str] = None) -> List[SemanticRelation]:
        """Get relations for a word, optionally filtered by type."""
        relations = self.relation_index.get(word, [])
        if relation_type:
            relations = [r for r in relations if r.relation_type == relation_type]
        return relations
    
    def get_synonyms(self, word: str, min_strength: float = 0.7) -> List[str]:
        """Get synonyms for a word."""
        relations = self.get_relations(word, 'synonym')
        return [r.target for r in relations if r.strength >= min_strength and r.source == word]
    
    def get_antonyms(self, word: str, min_strength: float = 0.7) -> List[str]:
        """Get antonyms for a word."""
        relations = self.get_relations(word, 'antonym')
        return [r.target for r in relations if r.strength >= min_strength and r.source == word]
    
    def get_causes(self, word: str) -> List[str]:
        """Get words that this word causes."""
        relations = self.get_relations(word, 'causes')
        return [r.target for r in relations if r.source == word]
    
    def get_enables(self, word: str) -> List[str]:
        """Get words that this word enables."""
        relations = self.get_relations(word, 'enables')
        return [r.target for r in relations if r.source == word]
    
    def get_similar_words(self, word: str, min_strength: float = 0.6) -> List[str]:
        """Get similar words (synonyms + similar_to)."""
        similar = set()
        similar.update(self.get_synonyms(word, min_strength))
        similar_relations = self.get_relations(word, 'similar_to')
        similar.update([r.target for r in similar_relations if r.strength >= min_strength and r.source == word])
        return list(similar)
    
    def get_contextual_words(self, context: str) -> List[str]:
        """Get words relevant to a situational context."""
        return self.situational_contexts.get(context, [])
    
    def get_words_for_state(self, state_type: str) -> List[str]:
        """Get words for an organism state type."""
        return self.state_word_map.get(state_type, [])
    
    def get_words_for_action(self, action_idx: int) -> List[str]:
        """Get words for an organism action."""
        return self.action_word_map.get(action_idx, [])
    
    def find_semantic_path(self, source: str, target: str, max_depth: int = 3) -> Optional[List[str]]:
        """
        Find semantic path between two words (for reflexive reasoning).
        
        Returns path like: ['source', 'intermediate1', 'intermediate2', 'target']
        """
        if source == target:
            return [source]
        
        if source not in self.concepts or target not in self.concepts:
            return None
        
        # BFS search for semantic path
        queue = [(source, [source])]
        visited = {source}
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Get all related words
            relations = self.get_relations(current)
            for relation in relations:
                next_word = relation.target if relation.source == current else relation.source
                
                if next_word == target:
                    return path + [target]
                
                if next_word not in visited and next_word in self.concepts:
                    visited.add(next_word)
                    queue.append((next_word, path + [next_word]))
        
        return None
    
    def get_situational_awareness(self, 
                                 organism_state: np.ndarray,
                                 organism_action: Optional[int] = None,
                                 network_state: Optional[Dict[str, Any]] = None,
                                 breath_state: Optional[Dict[str, Any]] = None,
                                 context_memory: Optional[Any] = None) -> List[str]:
        """
        Dynamic multi-dimensional situational awareness for word association.
        
        Assesses organism position, environment, system dynamics, and contextual
        variables to generate precise, contextually appropriate word associations.
        
        Uses all 18 state features plus network/breath state for comprehensive
        awareness across multiple dimensions simultaneously.
        
        Args:
            organism_state: Full 18-feature state vector (numpy array)
            organism_action: Current or recent action index (0-5)
            network_state: Network-level state (generation, VP, connections, etc.)
            breath_state: Breath engine state (depth, phase, cycle, pulse)
            context_memory: ContextMemory instance for vocabulary access
            
        Returns:
            List of contextually relevant words, prioritized by situational fit
        """
        if organism_state is None or len(organism_state) < 18:
            # Fallback to basic awareness
            return self._get_basic_awareness(organism_state, organism_action)
        
        # ============================================================
        # MULTI-DIMENSIONAL CONTEXT ASSESSMENT
        # ============================================================
        
        # Extract all 18 state features
        fitness = float(organism_state[0]) if len(organism_state) > 0 else 0.5
        resources = float(organism_state[1]) if len(organism_state) > 1 else 0.5
        connections = float(organism_state[2]) if len(organism_state) > 2 else 0.0
        pos_x = float(organism_state[3]) if len(organism_state) > 3 else 0.5
        pos_y = float(organism_state[4]) if len(organism_state) > 4 else 0.5
        action_success = float(organism_state[5]) if len(organism_state) > 5 else 0.5
        local_density = float(organism_state[6]) if len(organism_state) > 6 else 0.5
        nearest_distance = float(organism_state[7]) if len(organism_state) > 7 else 0.5
        generation_age = float(organism_state[8]) if len(organism_state) > 8 else 0.0
        parent_fitness = float(organism_state[9]) if len(organism_state) > 9 else 0.5
        breath_feat1 = float(organism_state[10]) if len(organism_state) > 10 else 0.5
        breath_feat2 = float(organism_state[11]) if len(organism_state) > 11 else 0.5
        trait_divergence = float(organism_state[12]) if len(organism_state) > 12 else 0.0
        network_coherence = float(organism_state[13]) if len(organism_state) > 13 else 0.5
        quantum_entropy = float(organism_state[14]) if len(organism_state) > 14 else 0.5
        evolution_pressure = float(organism_state[15]) if len(organism_state) > 15 else 0.0
        phase_mismatch = float(organism_state[16]) if len(organism_state) > 16 else 0.0
        system_health = float(organism_state[17]) if len(organism_state) > 17 else 0.5
        
        # Extract network-level context
        vp_value = 0.0
        generation = 0
        num_organisms = 0
        if network_state:
            vp_value = float(network_state.get('vp_value', 0.0))
            generation = int(network_state.get('generation', 0))
            num_organisms = int(network_state.get('num_organisms', 0))
        
        # Extract breath-level context
        breath_depth = 0.5
        breath_phase = 0.0
        breath_cycle = 0
        system_phase = 'genesis'
        if breath_state:
            breath_depth = float(breath_state.get('depth', 0.5))
            breath_phase = float(breath_state.get('phase', 0.0))
            breath_cycle = int(breath_state.get('cycle', 0))
            system_phase = breath_state.get('system_phase', 'genesis')
        
        # ============================================================
        # DYNAMIC WORD ASSOCIATION FRAMEWORK
        # ============================================================
        
        word_scores: Dict[str, float] = {}
        
        # 1. ACTION-BASED ASSOCIATIONS (immediate behavioral context)
        if organism_action is not None:
            action_words = self.get_words_for_action(organism_action)
            for word in action_words:
                word_scores[word] = word_scores.get(word, 0.0) + 1.0
        
        # 2. FITNESS-BASED ASSOCIATIONS (organism vitality)
        if fitness > 0.75:
            for word in self.get_words_for_state('high_fitness'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.9
        elif fitness < 0.25:
            for word in self.get_words_for_state('low_fitness'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.9
        else:
            for word in self.get_words_for_state('medium_fitness'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.7
        
        # 3. RESOURCE-BASED ASSOCIATIONS (material context)
        if resources > 0.75:
            for word in self.get_words_for_state('high_resources'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.8
        elif resources < 0.25:
            for word in self.get_words_for_state('low_resources'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.8
        
        # 4. CONNECTION-BASED ASSOCIATIONS (social/network context)
        if connections > 0.7:
            for word in self.get_words_for_state('many_connections'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.85
        elif connections < 0.1:
            for word in self.get_words_for_state('no_connections'):
                word_scores[word] = word_scores.get(word, 0.0) + 0.85
        
        # 5. POSITIONAL AWARENESS (spatial context)
        # Center vs. edge awareness
        center_distance = np.sqrt((pos_x - 0.5)**2 + (pos_y - 0.5)**2)
        if center_distance < 0.2:
            word_scores['here'] = word_scores.get('here', 0.0) + 0.6
            word_scores['center'] = word_scores.get('center', 0.0) + 0.5
        elif center_distance > 0.7:
            word_scores['there'] = word_scores.get('there', 0.0) + 0.6
            word_scores['edge'] = word_scores.get('edge', 0.0) + 0.5
        
        # Proximity awareness
        if nearest_distance < 0.2:
            word_scores['near'] = word_scores.get('near', 0.0) + 0.7
            word_scores['together'] = word_scores.get('together', 0.0) + 0.6
        elif nearest_distance > 0.8:
            word_scores['far'] = word_scores.get('far', 0.0) + 0.7
            word_scores['alone'] = word_scores.get('alone', 0.0) + 0.6
        
        # 6. LOCAL DENSITY AWARENESS (environmental context)
        if local_density > 0.7:
            word_scores['crowded'] = word_scores.get('crowded', 0.0) + 0.6
            word_scores['dense'] = word_scores.get('dense', 0.0) + 0.5
        elif local_density < 0.3:
            word_scores['sparse'] = word_scores.get('sparse', 0.0) + 0.6
            word_scores['isolated'] = word_scores.get('isolated', 0.0) + 0.5
        
        # 7. VIOLATION PRESSURE AWARENESS (system stability context)
        if vp_value > 0.7 or trait_divergence > 0.7:
            word_scores['pressure'] = word_scores.get('pressure', 0.0) + 0.9
            word_scores['unstable'] = word_scores.get('unstable', 0.0) + 0.8
            word_scores['crisis'] = word_scores.get('crisis', 0.0) + 0.7
            word_scores['stress'] = word_scores.get('stress', 0.0) + 0.7
        elif vp_value < 0.3 and trait_divergence < 0.3:
            word_scores['stable'] = word_scores.get('stable', 0.0) + 0.8
            word_scores['calm'] = word_scores.get('calm', 0.0) + 0.7
            word_scores['balanced'] = word_scores.get('balanced', 0.0) + 0.7
        
        # 8. NETWORK COHERENCE AWARENESS (system integration context)
        if network_coherence > 0.7:
            word_scores['connected'] = word_scores.get('connected', 0.0) + 0.7
            word_scores['united'] = word_scores.get('united', 0.0) + 0.6
            word_scores['coherent'] = word_scores.get('coherent', 0.0) + 0.6
        elif network_coherence < 0.3:
            word_scores['fragmented'] = word_scores.get('fragmented', 0.0) + 0.7
            word_scores['disconnected'] = word_scores.get('disconnected', 0.0) + 0.6
        
        # 9. EVOLUTION PRESSURE AWARENESS (adaptation context)
        if evolution_pressure > 0.7:
            word_scores['adapt'] = word_scores.get('adapt', 0.0) + 0.8
            word_scores['evolve'] = word_scores.get('evolve', 0.0) + 0.7
            word_scores['change'] = word_scores.get('change', 0.0) + 0.6
        elif evolution_pressure < 0.3:
            word_scores['stable'] = word_scores.get('stable', 0.0) + 0.6
            word_scores['persist'] = word_scores.get('persist', 0.0) + 0.5
        
        # 10. PHASE MISMATCH AWARENESS (synchronization context)
        if phase_mismatch > 0.7:
            word_scores['mismatch'] = word_scores.get('mismatch', 0.0) + 0.7
            word_scores['desynchronized'] = word_scores.get('desynchronized', 0.0) + 0.6
        
        # 11. SYSTEM HEALTH AWARENESS (ecosystem wellness context)
        if system_health > 0.7:
            word_scores['healthy'] = word_scores.get('healthy', 0.0) + 0.8
            word_scores['thriving'] = word_scores.get('thriving', 0.0) + 0.7
            word_scores['flourish'] = word_scores.get('flourish', 0.0) + 0.7
        elif system_health < 0.3:
            word_scores['sick'] = word_scores.get('sick', 0.0) + 0.8
            word_scores['declining'] = word_scores.get('declining', 0.0) + 0.7
            word_scores['struggle'] = word_scores.get('struggle', 0.0) + 0.7
        
        # 12. BREATH PHASE AWARENESS (temporal/rhythmic context)
        if breath_depth > 0.7:
            # Inhale phase - expansion, growth, exploration
            word_scores['expand'] = word_scores.get('expand', 0.0) + 0.6
            word_scores['grow'] = word_scores.get('grow', 0.0) + 0.5
            word_scores['explore'] = word_scores.get('explore', 0.0) + 0.5
        elif breath_depth < 0.3:
            # Exhale phase - consolidation, rest, stability
            word_scores['rest'] = word_scores.get('rest', 0.0) + 0.6
            word_scores['consolidate'] = word_scores.get('consolidate', 0.0) + 0.5
            word_scores['stable'] = word_scores.get('stable', 0.0) + 0.5
        
        if system_phase == 'sovereign':
            word_scores['precise'] = word_scores.get('precise', 0.0) + 0.6
            word_scores['focused'] = word_scores.get('focused', 0.0) + 0.5
        elif system_phase == 'genesis':
            word_scores['explore'] = word_scores.get('explore', 0.0) + 0.6
            word_scores['discover'] = word_scores.get('discover', 0.0) + 0.5
        
        # 13. ACTION SUCCESS AWARENESS (behavioral feedback context)
        if action_success > 0.7:
            word_scores['success'] = word_scores.get('success', 0.0) + 0.7
            word_scores['effective'] = word_scores.get('effective', 0.0) + 0.6
        elif action_success < 0.3:
            word_scores['failure'] = word_scores.get('failure', 0.0) + 0.7
            word_scores['ineffective'] = word_scores.get('ineffective', 0.0) + 0.6
        
        # 14. GENERATION AGE AWARENESS (temporal/evolutionary context)
        if generation_age > 0.7:
            word_scores['mature'] = word_scores.get('mature', 0.0) + 0.6
            word_scores['experienced'] = word_scores.get('experienced', 0.0) + 0.5
        elif generation_age < 0.3:
            word_scores['young'] = word_scores.get('young', 0.0) + 0.6
            word_scores['new'] = word_scores.get('new', 0.0) + 0.5
        
        # ============================================================
        # ASSOCIATIVE COMPLEXITY EXPANSION
        # ============================================================
        
        # Expand top-scoring words through semantic relationships
        top_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)[:8]
        expanded_words = set([w for w, _ in top_words])
        
        for word, score in top_words:
            if score > 0.5:  # Only expand high-confidence words
                # Get semantically similar words
                similar = self.get_similar_words(word, min_strength=0.6)
                for sim_word in similar[:2]:  # Top 2 similar
                    if sim_word not in expanded_words:
                        expanded_words.add(sim_word)
                        # Inherit partial score from parent word
                        word_scores[sim_word] = word_scores.get(sim_word, 0.0) + score * 0.5
        
        # ============================================================
        # DIVERSITY MECHANISM (Prevent Over-Stimulation)
        # ============================================================
        
        # Boost less-used words to prevent yarn ball
        for word in word_scores.keys():
            usage = self.word_usage_counts[word]
            # Less-used words get diversity boost (inverse usage weighting)
            diversity_factor = 1.0 / (1.0 + usage * 0.1)
            word_scores[word] = word_scores[word] * (1.0 + self.diversity_boost * diversity_factor)
        
        # ============================================================
        # EXPLORATION MECHANISM (Enable Discovery)
        # ============================================================
        
        # Random exploration of less-used words
        import random
        if random.random() < self.exploration_rate:
            all_words = list(self.concepts.keys())
            if all_words:
                # Weight by inverse usage (explore less-used words)
                word_weights = [1.0 / (1.0 + self.word_usage_counts.get(w, 0)) for w in all_words]
                try:
                    exploration_word = random.choices(all_words, weights=word_weights, k=1)[0]
                    word_scores[exploration_word] = word_scores.get(exploration_word, 0.0) + 0.5
                except (ValueError, IndexError):
                    pass  # Fallback if weights are invalid
        
        # ============================================================
        # PRIORITIZED WORD SELECTION
        # ============================================================
        
        # Sort by score and return top words
        final_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return words with score > 0.3, up to 15 words
        relevant_words = [word for word, score in final_words if score > 0.3][:15]
        
        # Track usage for diversity mechanism
        for word in relevant_words[:10]:  # Track top 10
            self.word_usage_counts[word] += 1
        
        # Ensure we have at least some words (fallback)
        if not relevant_words:
            relevant_words = self._get_basic_awareness(organism_state, organism_action)
        
        return relevant_words
    
    def _get_basic_awareness(self, organism_state: Optional[np.ndarray], 
                            organism_action: Optional[int]) -> List[str]:
        """Fallback basic awareness when full state is unavailable."""
        relevant_words = []
        
        if organism_action is not None:
            relevant_words.extend(self.get_words_for_action(organism_action))
        
        if organism_state is not None and len(organism_state) >= 3:
            fitness = float(organism_state[0])
            resources = float(organism_state[1])
            connections = float(organism_state[2])
            
            if fitness > 0.7:
                relevant_words.extend(self.get_words_for_state('high_fitness'))
            elif fitness < 0.3:
                relevant_words.extend(self.get_words_for_state('low_fitness'))
            
            if resources > 0.7:
                relevant_words.extend(self.get_words_for_state('high_resources'))
            elif resources < 0.3:
                relevant_words.extend(self.get_words_for_state('low_resources'))
            
            if connections > 0.7:
                relevant_words.extend(self.get_words_for_state('many_connections'))
            elif connections < 0.1:
                relevant_words.extend(self.get_words_for_state('no_connections'))
        
        return relevant_words[:10] if relevant_words else ['exist', 'be', 'act']
    
    def validate_relationship(self, word1: str, word2: str, context: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Validate if discovered relationship makes semantic sense.
        
        Returns:
            (is_valid, confidence_score)
        """
        # Check if words exist
        concept1 = self.get_concept(word1)
        concept2 = self.get_concept(word2)
        if not concept1 or not concept2:
            return False, 0.0
        
        # Check if already related (strengthen existing)
        existing = self.get_relations(word1, word2)
        if existing:
            return True, 0.9  # Strengthen existing
        
        # Semantic frame compatibility (40% weight)
        frame_match = concept1.semantic_frame == concept2.semantic_frame
        frame_score = 0.8 if frame_match else 0.5
        
        # Context coherence (60% weight - more important)
        context_score = self._check_context_coherence(word1, word2, context)
        
        # Combined validation score
        confidence = (frame_score * 0.4 + context_score * 0.6)
        
        return confidence > 0.5, confidence
    
    def _check_context_coherence(self, word1: str, word2: str, context: Dict[str, Any]) -> float:
        """
        Check if words appear together in similar organism states/contexts.
        
        Returns coherence score (0.0-1.0).
        """
        # Extract organism state from context
        organism_state = context.get('organism_state')
        if organism_state is None:
            return 0.5  # Neutral if no state available
        
        # Check if words have been used in similar contexts
        word1_contexts = self.word_context_history.get(word1, [])
        word2_contexts = self.word_context_history.get(word2, [])
        
        if not word1_contexts or not word2_contexts:
            return 0.4  # Low coherence if no history
        
        # Compare context vectors (simplified: compare organism state features)
        if isinstance(organism_state, list):
            organism_state = np.array(organism_state)
        
        coherence_scores = []
        for ctx1 in word1_contexts[-10:]:  # Last 10 contexts
            state1 = ctx1.get('organism_state')
            if state1 is not None:
                if isinstance(state1, list):
                    state1 = np.array(state1)
                # Calculate similarity (cosine similarity or euclidean distance)
                try:
                    if len(state1) == len(organism_state):
                        # Cosine similarity
                        dot_product = np.dot(state1, organism_state)
                        norm1 = np.linalg.norm(state1)
                        norm2 = np.linalg.norm(organism_state)
                        if norm1 > 0 and norm2 > 0:
                            similarity = dot_product / (norm1 * norm2)
                            coherence_scores.append(similarity)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Coherence calculation skipped for concept: {e}")
        
        if coherence_scores:
            avg_coherence = np.mean(coherence_scores)
            return float(np.clip(avg_coherence, 0.0, 1.0))
        
        return 0.5  # Default neutral coherence
    
    def update_generation(self, generation: int):
        """Update current generation for time-based learning curve."""
        self.current_generation = generation
        
        # Update exploration rate (decay over time)
        if generation < self.exploration_decay_generations:
            decay_factor = generation / self.exploration_decay_generations
            self.exploration_rate = max(
                self.exploration_end,
                self.exploration_start - (self.exploration_start - self.exploration_end) * decay_factor
            )
        else:
            self.exploration_rate = self.exploration_end
        
        # Update confidence threshold (grow over time)
        self.confidence_threshold = min(
            0.8,
            self.confidence_threshold + self.confidence_growth_rate
        )
    
    def get_reflexive_thought(self, word: str) -> Dict[str, Any]:
        """
        Get reflexive comprehensive thought about a word.
        
        Returns rich semantic information for meta-linguistic reasoning.
        """
        concept = self.get_concept(word)
        if not concept:
            return {}
        
        return {
            'word': word,
            'definition': concept.definition,
            'semantic_frame': concept.semantic_frame,
            'abstraction_level': concept.abstraction_level,
            'synonyms': self.get_synonyms(word),
            'antonyms': self.get_antonyms(word),
            'causes': self.get_causes(word),
            'enables': self.get_enables(word),
            'similar_words': self.get_similar_words(word),
            'contexts': concept.contexts,
            'associations': concept.associations,
            'organism_relevance': concept.organism_relevance
        }
    
    def expand_vocabulary_from_web(self, vocabulary) -> int:
        """
        Add all words from knowledge web to vocabulary.
        
        Args:
            vocabulary: LanguageVocabulary instance
            
        Returns:
            Number of new words added
        """
        words_added = 0
        for word in self.concepts.keys():
            if word not in vocabulary.word_to_id:
                vocabulary.add_word(word)
                words_added += 1
        
        logger.info(f"[LINGUISTIC_WEB] Added {words_added} words from knowledge web to vocabulary")
        return words_added
    
    def influence_context_memory(self, context_memory) -> int:
        """
        SEMANTIC CONVERGENCE: Push semantic relations into word embeddings.
        
        - Synonyms: Pull word embeddings closer together
        - Antonyms: Push word embeddings apart
        
        This ensures that the context_memory word embeddings reflect
        semantic relationships from the knowledge web.
        
        Args:
            context_memory: ContextMemory instance with word embeddings
            
        Returns:
            Number of word embeddings influenced
        """
        if not hasattr(context_memory, 'update_word_embedding_from_organism'):
            logger.debug("[LINGUISTIC_WEB] ContextMemory lacks update_word_embedding_from_organism")
            return 0
        
        influenced = 0
        
        # Process synonym relations
        for relation in self.relations[:1000]:  # Limit to avoid overly long processing
            if relation.strength < 0.5:
                continue
            
            source_embed = context_memory.get_word_embedding(relation.source)
            target_embed = context_memory.get_word_embedding(relation.target)
            
            if source_embed is None or target_embed is None:
                continue
            
            if relation.relation_type == 'synonym':
                # Pull synonyms closer: blend embeddings
                blended = (source_embed + target_embed) / 2
                context_memory.update_word_embedding_from_organism(relation.source, blended, alpha=0.02)
                context_memory.update_word_embedding_from_organism(relation.target, blended, alpha=0.02)
                influenced += 2
            
            elif relation.relation_type == 'antonym':
                # Push antonyms apart: add negative of the other
                # (Moving in opposite direction)
                context_memory.update_word_embedding_from_organism(
                    relation.source, source_embed - 0.1 * target_embed, alpha=0.02
                )
                context_memory.update_word_embedding_from_organism(
                    relation.target, target_embed - 0.1 * source_embed, alpha=0.02
                )
                influenced += 2
            
            elif relation.relation_type == 'similar_to':
                # Similar words: slight pull together
                blended = 0.7 * source_embed + 0.3 * target_embed
                context_memory.update_word_embedding_from_organism(relation.source, blended, alpha=0.01)
                influenced += 1
        
        if influenced > 0:
            logger.info(f"[LINGUISTIC_WEB] Influenced {influenced} word embeddings from semantic relations")
        
        return influenced
    
    def save_to_file(self, filepath: str):
        """Save knowledge web to JSON file."""
        data = {
            'concepts': {
                word: {
                    'definition': c.definition,
                    'semantic_frame': c.semantic_frame,
                    'organism_relevance': c.organism_relevance,
                    'associations': c.associations,
                    'contexts': c.contexts,
                    'abstraction_level': c.abstraction_level
                }
                for word, c in self.concepts.items()
            },
            'relations': [
                {
                    'source': r.source,
                    'target': r.target,
                    'relation_type': r.relation_type,
                    'strength': r.strength,
                    'context': r.context
                }
                for r in self.relations
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"[LINGUISTIC_WEB] Saved to {filepath}")
    
    def load_from_file(self, filepath: str):
        """Load knowledge web from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Load concepts
        for word, concept_data in data['concepts'].items():
            concept = LinguisticConcept(
                word=word,
                definition=concept_data['definition'],
                semantic_frame=concept_data['semantic_frame'],
                organism_relevance=concept_data['organism_relevance'],
                associations=concept_data['associations'],
                contexts=concept_data['contexts'],
                abstraction_level=concept_data['abstraction_level']
            )
            self.concepts[word] = concept
            self.word_to_concept[word] = word
        
        # Load relations
        for rel_data in data['relations']:
            self._add_relation(
                source=rel_data['source'],
                target=rel_data['target'],
                relation_type=rel_data['relation_type'],
                strength=rel_data['strength'],
                context=rel_data.get('context'),
                confidence=0.9,  # High confidence for seeded relationships
                is_seeded=True,  # Mark as seeded (from file)
                generation=0  # Loaded at initialization
            )
        
        # Rebuild indices
        self._build_semantic_clusters()
        self._build_organism_mappings()
        
        logger.info(f"[LINGUISTIC_WEB] Loaded from {filepath}: {len(self.concepts)} concepts, {len(self.relations)} relations")

