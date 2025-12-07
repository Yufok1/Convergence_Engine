# 🏗️ Linguistic Cognition Architecture Implementation Guide
## From Theory to Code: Building the Semantic Layer

---

## QUICK START: Core Data Structures

### 1. SemanticWeb Foundation

```python
# Add to your unified_entry.py or create linguistic_engine.py

import torch
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import json

@dataclass
class ConceptEmbedding:
    """Single concept's representation"""
    word: str
    embedding: np.ndarray  # 64-dim vector
    confidence: float      # 0.0-1.0
    usage_count: int
    success_count: int
    organism_ids: Set[int]
    first_learned_generation: int
    last_used_generation: int

@dataclass
class ConceptRelationship:
    """Two-concept relationship"""
    concept_a: str
    concept_b: str
    relationship_type: str  # "cause", "compare", "temporal", "context"
    confidence: float
    embedding: np.ndarray
    organism_counts: int
    total_applications: int
    success_applications: int

@dataclass
class ConceptTriangle:
    """Three-concept semantic triangle"""
    atom_1: str
    atom_2: str
    atom_3: str
    composite_word: str
    composite_embedding: np.ndarray
    confidence: float
    derived_concepts: List[str]
    experience_examples: List[Dict]

class SemanticWeb:
    def __init__(self, embedding_dim=64, vocab_size=1000):
        self.embedding_dim = embedding_dim
        self.vocab_size = vocab_size
        
        # Stage 0: Atomic concepts
        self.concepts: Dict[str, ConceptEmbedding] = {}
        self.atomic_state_mappings: Dict[Tuple, str] = {}
        
        # Stage 1: Binary relationships
        self.relationships: Dict[Tuple, ConceptRelationship] = {}
        self.causation_graph: Dict[str, List[Tuple]] = defaultdict(list)
        
        # Stage 2: Triangular concepts
        self.triangles: Dict[Tuple, ConceptTriangle] = {}
        self.semantic_network: Dict[str, List[Tuple]] = defaultdict(list)
        
        # Stage 3: Articulation rules
        self.articulation_rules: List[Dict] = []
        self.synonym_matrices: Dict[str, Dict[str, float]] = {}
        self.metaphor_bridges: Dict[Tuple, Tuple] = {}
        
        # Tracking
        self.concept_confidence_history: Dict[str, List[float]] = defaultdict(list)
        self.precision_scores: List[float] = []
        self.current_stage = 0
        self.generation = 0
    
    # ===== STAGE 0: ATOMIC CONCEPTS =====
    
    def discretize_state_to_concept(self, state_value, dimension_name):
        """
        Convert continuous state value to discrete concept
        
        Example:
          discretize_state_to_concept(0.85, "fitness") → "thriving"
        """
        # Define discretization bins
        bins = {
            "fitness": [
                (0.9, "thriving"),
                (0.7, "healthy"),
                (0.5, "managed"),
                (0.3, "struggling"),
                (0.0, "critical")
            ],
            "resources": [
                (0.9, "abundant"),
                (0.7, "sufficient"),
                (0.5, "moderate"),
                (0.3, "scarce"),
                (0.0, "depleted")
            ],
            "energy": [
                (0.9, "vigorous"),
                (0.7, "active"),
                (0.5, "balanced"),
                (0.3, "weary"),
                (0.0, "exhausted")
            ],
            "connections": [
                (0.9, "highly_connected"),
                (0.7, "well_connected"),
                (0.5, "moderately_connected"),
                (0.3, "isolated"),
                (0.0, "alone")
            ],
            # Add more dimensions...
        }
        
        if dimension_name not in bins:
            return f"unknown_{dimension_name}"
        
        for threshold, concept in bins[dimension_name]:
            if state_value >= threshold:
                return concept
        
        return "critical"  # Fallback
    
    def create_atomic_concept(self, word, organism_id, generation):
        """Create new atomic concept or strengthen existing"""
        
        if word not in self.concepts:
            # Create new
            embedding = np.random.randn(self.embedding_dim) * 0.1
            self.concepts[word] = ConceptEmbedding(
                word=word,
                embedding=embedding / np.linalg.norm(embedding),
                confidence=0.3,
                usage_count=1,
                success_count=1,
                organism_ids={organism_id},
                first_learned_generation=generation,
                last_used_generation=generation
            )
        else:
            # Strengthen existing
            concept = self.concepts[word]
            concept.usage_count += 1
            concept.success_count += 1
            concept.last_used_generation = generation
            concept.organism_ids.add(organism_id)
            
            # Increase confidence (with saturation at 0.95)
            concept.confidence = min(
                concept.confidence + 0.02,
                0.95
            )
        
        # Track history
        self.concept_confidence_history[word].append(
            self.concepts[word].confidence
        )
    
    def teach_atomic_concept(self, organism_state, dimension, organism_id):
        """
        Main teaching function for Stage 0
        
        Usage:
          semantic_web.teach_atomic_concept(org.state, "fitness", org.id)
        """
        # Discretize state to concept
        concept_word = self.discretize_state_to_concept(
            organism_state[dimension],
            dimension
        )
        
        # Create/strengthen concept
        self.create_atomic_concept(concept_word, organism_id, self.generation)
        
        # Return for use in chat/emission
        return concept_word
    
    # ===== STAGE 1: BINARY RELATIONSHIPS =====
    
    def learn_relationship(self, concept_a, concept_b, concept_c, 
                          relationship_type, organism_id):
        """
        Learn a binary relationship from three consecutive concepts
        
        relationship_type: "cause", "compare", "temporal", "context"
        """
        
        rel_key = (concept_a, concept_b, concept_c)
        
        if rel_key not in self.relationships:
            # Create new relationship
            embedding = np.random.randn(self.embedding_dim) * 0.1
            
            self.relationships[rel_key] = ConceptRelationship(
                concept_a=concept_a,
                concept_b=concept_b,
                confidence=0.25,
                embedding=embedding / np.linalg.norm(embedding),
                relationship_type=relationship_type,
                organism_counts=1,
                total_applications=1,
                success_applications=1
            )
        else:
            # Update existing
            rel = self.relationships[rel_key]
            rel.total_applications += 1
            rel.success_applications += 1
            rel.confidence = min(rel.confidence + 0.03, 0.90)
            rel.organism_counts = len(set([organism_id] + 
                                         [rel.organism_counts]))
        
        # Link in causation graph
        self.causation_graph[concept_b].append(
            (concept_c, self.relationships[rel_key].confidence)
        )
        
        return self.relationships[rel_key]
    
    def get_causal_chain(self, starting_concept, depth=3):
        """
        Retrieve causal chain from concept
        
        Returns sequence of concepts that typically follow
        """
        chain = [starting_concept]
        current = starting_concept
        
        for _ in range(depth - 1):
            if current not in self.causation_graph:
                break
            
            # Get most likely next concept
            next_concepts = self.causation_graph[current]
            if not next_concepts:
                break
            
            # Sort by confidence
            next_concepts.sort(key=lambda x: x[1], reverse=True)
            next_concept = next_concepts[0][0]
            
            chain.append(next_concept)
            current = next_concept
        
        return chain
    
    # ===== STAGE 2: SEMANTIC TRIANGULATION =====
    
    def create_triangular_concept(self, atom_1, atom_2, atom_3, 
                                  composite_word, organism_id):
        """
        Create or strengthen a triangular semantic concept
        
        This combines three atomic concepts into composite understanding
        """
        
        tri_key = tuple(sorted([atom_1, atom_2, atom_3]))
        
        if tri_key not in self.triangles:
            # Blend embeddings from three atoms
            embeddings = [
                self.concepts[atom_1].embedding if atom_1 in self.concepts 
                    else np.random.randn(self.embedding_dim),
                self.concepts[atom_2].embedding if atom_2 in self.concepts 
                    else np.random.randn(self.embedding_dim),
                self.concepts[atom_3].embedding if atom_3 in self.concepts 
                    else np.random.randn(self.embedding_dim)
            ]
            
            # Composite: mean of three embeddings
            composite_embedding = np.mean(embeddings, axis=0)
            composite_embedding = composite_embedding / np.linalg.norm(
                composite_embedding
            )
            
            self.triangles[tri_key] = ConceptTriangle(
                atom_1=atom_1,
                atom_2=atom_2,
                atom_3=atom_3,
                composite_word=composite_word,
                composite_embedding=composite_embedding,
                confidence=0.30,
                derived_concepts=[],
                experience_examples=[]
            )
        else:
            # Strengthen existing triangle
            tri = self.triangles[tri_key]
            tri.confidence = min(tri.confidence + 0.04, 0.85)
        
        # Create triangular link
        self.semantic_network[atom_1].append((atom_2, atom_3))
        self.semantic_network[atom_2].append((atom_1, atom_3))
        self.semantic_network[atom_3].append((atom_1, atom_2))
        
        return self.triangles[tri_key]
    
    # ===== STAGE 3: ARTICULATION =====
    
    def add_articulation_rule(self, rule_dict):
        """
        Add a contextual articulation rule
        
        Example:
          rule = {
            'condition': lambda state: state['fitness'] > 0.7 and 
                                      state['cooperation'] > 0.6,
            'base_word': 'thriving',
            'preferred_word': 'flourishing',
            'confidence_boost': 0.15,
            'description': 'When high fitness AND cooperation'
          }
        """
        self.articulation_rules.append(rule_dict)
    
    def score_word_choice(self, word, organism_state, target_concept):
        """
        Score how well a word choice fits the organism's state
        
        Returns: precision_score (0.0-1.0)
        """
        
        if word not in self.concepts:
            return 0.0
        
        # Component 1: Embedding distance (40%)
        target_embedding = self.concepts[target_concept].embedding \
            if target_concept in self.concepts \
            else np.random.randn(self.embedding_dim)
        
        word_embedding = self.concepts[word].embedding
        
        embedding_distance = np.linalg.norm(
            word_embedding - target_embedding
        )
        embedding_score = 1.0 / (1.0 + embedding_distance)  # Sigmoid-like
        
        # Component 2: Contextual appropriateness (30%)
        context_matches = 0
        for rule in self.articulation_rules:
            try:
                if rule['condition'](organism_state):
                    if rule['base_word'] == word or \
                       rule['preferred_word'] == word:
                        context_matches += 1
            except:
                pass  # Condition failed
        
        contextual_score = min(context_matches / max(len(self.articulation_rules), 1), 1.0)
        
        # Component 3: Connotation consistency (20%)
        # Track if word is used consistently in similar contexts
        word_context_history = []
        for rule in self.articulation_rules:
            try:
                if (rule['base_word'] == word or rule['preferred_word'] == word) \
                   and rule['condition'](organism_state):
                    word_context_history.append(True)
            except:
                word_context_history.append(False)
        
        connotation_score = 1.0 if word_context_history else 0.6
        
        # Component 4: Usage history (10%)
        if word in self.concepts:
            usage_ratio = self.concepts[word].success_count / \
                         max(self.concepts[word].usage_count, 1)
        else:
            usage_ratio = 0.5
        
        consistency_score = usage_ratio
        
        # Final precision
        precision = (
            embedding_score * 0.4 +
            contextual_score * 0.3 +
            connotation_score * 0.2 +
            consistency_score * 0.1
        )
        
        # Track
        self.precision_scores.append(precision)
        
        return precision
    
    def select_best_word(self, target_concept, organism_state):
        """
        Select the best word to express a concept given current state
        
        Returns: (best_word, precision_score)
        """
        
        if target_concept not in self.concepts:
            return target_concept, 0.5
        
        # Get base word
        base_word = target_concept
        
        # Get synonyms from synonym matrix
        candidates = [base_word]
        if base_word in self.synonym_matrices:
            for synonym, similarity in \
                sorted(self.synonym_matrices[base_word].items(),
                      key=lambda x: x[1], reverse=True)[:5]:
                candidates.append(synonym)
        
        # Score each candidate
        scores = {}
        for candidate in candidates:
            scores[candidate] = self.score_word_choice(
                candidate, 
                organism_state, 
                target_concept
            )
        
        # Select best
        best_word = max(scores, key=scores.get)
        
        return best_word, scores[best_word]

# ===== CURRICULUM MANAGEMENT =====

class CurriculumManager:
    """Manages progression through learning stages"""
    
    STAGE_GATES = {
        0: {
            'min_concepts': 30,
            'min_avg_confidence': 0.65,
            'min_organisms_participating': 0.7  # 70% of swarm
        },
        1: {
            'min_relationships': 200,
            'min_avg_confidence': 0.55,
            'max_contradictions': 0.05
        },
        2: {
            'min_triangles': 800,
            'min_avg_confidence': 0.48,
            'min_semantic_diversity': 100
        },
        3: {
            'min_avg_precision': 0.68,
            'min_avg_articulation': 0.72,
            'min_active_rules': 200
        }
    }
    
    def __init__(self, semantic_web, organisms):
        self.semantic_web = semantic_web
        self.organisms = organisms
        self.current_stage = 0
        self.stage_start_generation = 0
        self.metrics_history = defaultdict(list)
    
    def evaluate_stage_readiness(self):
        """Check if organisms can advance to next stage"""
        
        gate = self.STAGE_GATES.get(self.current_stage, {})
        
        if not gate:
            return False, "No gate defined"
        
        # Gather metrics
        metrics = self.calculate_metrics()
        
        # Check each gate
        for key, threshold in gate.items():
            if metrics.get(key, 0) < threshold:
                return False, f"Failed: {key} = {metrics.get(key)}"
        
        return True, metrics
    
    def calculate_metrics(self):
        """Calculate current system metrics"""
        
        metrics = {}
        
        if self.current_stage == 0:
            # Count unique concepts
            all_concepts = set(self.semantic_web.concepts.keys())
            metrics['min_concepts'] = len(all_concepts)
            
            # Average confidence
            confidences = [c.confidence for c in 
                          self.semantic_web.concepts.values()]
            metrics['min_avg_confidence'] = np.mean(confidences) \
                if confidences else 0.0
            
            # Participation ratio
            organisms_with_concepts = set()
            for concept in self.semantic_web.concepts.values():
                organisms_with_concepts.update(concept.organism_ids)
            
            metrics['min_organisms_participating'] = \
                len(organisms_with_concepts) / max(len(self.organisms), 1)
        
        elif self.current_stage == 1:
            metrics['min_relationships'] = len(self.semantic_web.relationships)
            
            if self.semantic_web.relationships:
                confidences = [r.confidence for r in 
                              self.semantic_web.relationships.values()]
                metrics['min_avg_confidence'] = np.mean(confidences)
            else:
                metrics['min_avg_confidence'] = 0.0
            
            metrics['max_contradictions'] = 0.0  # Placeholder
        
        elif self.current_stage == 2:
            metrics['min_triangles'] = len(self.semantic_web.triangles)
            
            if self.semantic_web.triangles:
                confidences = [t.confidence for t in 
                              self.semantic_web.triangles.values()]
                metrics['min_avg_confidence'] = np.mean(confidences)
            else:
                metrics['min_avg_confidence'] = 0.0
            
            metrics['min_semantic_diversity'] = len(
                set(t.composite_word for t in 
                    self.semantic_web.triangles.values())
            )
        
        elif self.current_stage == 3:
            if self.semantic_web.precision_scores:
                metrics['min_avg_precision'] = np.mean(
                    self.semantic_web.precision_scores[-100:]  # Last 100
                )
            else:
                metrics['min_avg_precision'] = 0.0
            
            metrics['min_avg_articulation'] = metrics['min_avg_precision']
            metrics['min_active_rules'] = len(
                self.semantic_web.articulation_rules
            )
        
        # Store history
        for key, value in metrics.items():
            self.metrics_history[key].append(value)
        
        return metrics
    
    def advance_stage(self):
        """Move to next curriculum stage"""
        
        if self.current_stage < 3:
            self.current_stage += 1
            self.stage_start_generation = self.semantic_web.generation
            
            # Adjust organism learning rates slightly
            for organism in self.organisms:
                if hasattr(organism, 'learning_rate'):
                    organism.learning_rate *= 1.05  # 5% faster
```

---

## Integration with Chat Teaching

```python
class ChatTeachingBridge:
    """
    Routes organism chat interactions through semantic web
    """
    
    def __init__(self, semantic_web, curriculum_manager):
        self.semantic_web = semantic_web
        self.curriculum_manager = curriculum_manager
    
    async def handle_organism_chat(self, organism, prompt, 
                                  response_text):
        """
        Process organism's chat response through semantic system
        """
        
        stage = self.curriculum_manager.current_stage
        
        if stage == 0:
            # Extract single concept
            concept = self.extract_concept_from_text(response_text)
            if concept:
                self.semantic_web.create_atomic_concept(
                    concept, organism.id, 
                    self.semantic_web.generation
                )
                return concept, 0.5
        
        elif stage == 1:
            # Extract relationship
            concepts = self.extract_multiple_concepts(response_text)
            if len(concepts) >= 2:
                self.semantic_web.learn_relationship(
                    concepts[0], concepts[1], 
                    concepts[2] if len(concepts) > 2 else concepts[1],
                    "context", organism.id
                )
                return concepts, 0.6
        
        elif stage == 2:
            # Extract triangle
            concepts = self.extract_multiple_concepts(response_text)
            if len(concepts) == 3:
                composite = self.generate_composite_name(concepts)
                self.semantic_web.create_triangular_concept(
                    concepts[0], concepts[1], concepts[2],
                    composite, organism.id
                )
                return composite, 0.7
        
        elif stage == 3:
            # Evaluate articulation precision
            best_word, precision = \
                self.semantic_web.select_best_word(
                    self.extract_main_concept(response_text),
                    organism.state
                )
            return best_word, precision
    
    def extract_concept_from_text(self, text):
        """Extract single concept from organism response"""
        # Simple NLP: match against known concepts
        text_lower = text.lower()
        for concept in self.semantic_web.concepts.keys():
            if concept.lower() in text_lower:
                return concept
        return None
    
    def extract_multiple_concepts(self, text):
        """Extract multiple concepts from text"""
        concepts = []
        text_lower = text.lower()
        for concept in self.semantic_web.concepts.keys():
            if concept.lower() in text_lower:
                concepts.append(concept)
        return concepts[:5]  # Limit to 5
    
    def generate_composite_name(self, concepts):
        """Generate composite concept name from three concepts"""
        # Simple approach: combine with underscores
        return "_".join(concepts)
```

---

## Quick Integration Points

### 1. In Your Breath Cycle

```python
# In unified_entry.py or where you run the breath cycle:

def run_breath_cycle_with_semantics(self):
    # Normal breath cycle
    breath_data = self.breath_engine.breathe()
    
    # NEW: Teach semantic concepts
    for organism in self.organisms:
        # Teach appropriate stage concept
        if self.curriculum_manager.current_stage == 0:
            concept = self.semantic_web.teach_atomic_concept(
                organism.state, "fitness", organism.id
            )
            organism.emit_chat(f"I am currently {concept}")
        
        # ... similar for other stages
    
    # Check if ready to advance
    ready, metrics = self.curriculum_manager.evaluate_stage_readiness()
    if ready:
        self.curriculum_manager.advance_stage()
        print(f"ADVANCED TO STAGE {self.curriculum_manager.current_stage}")
```

### 2. In Neural Training

```python
# Blend semantic loss with action loss:

def compute_total_reward(self, base_action_reward, 
                        organism_state, chat_response):
    # Action reward (existing)
    action_component = base_action_reward * 0.7
    
    # Semantic reward (NEW)
    if chat_response:
        _, precision = self.semantic_web.select_best_word(
            extract_target_concept(chat_response),
            organism_state
        )
        semantic_component = precision * 0.3
    else:
        semantic_component = 0.0
    
    total = action_component + semantic_component
    return total
```

---

## File Structure

```
your_project/
├── linguistic_cognition/
│   ├── __init__.py
│   ├── semantic_web.py        # SemanticWeb class
│   ├── curriculum.py          # CurriculumManager class
│   ├── chat_bridge.py         # ChatTeachingBridge class
│   ├── concepts.py            # Concept definitions
│   └── articulation.py        # Articulation rules
│
└── unified_entry.py           # Integrate above classes
```

---

**Start with `SemanticWeb` class, run it for ~50 generations with Stage 0, then progressively add stages.**
