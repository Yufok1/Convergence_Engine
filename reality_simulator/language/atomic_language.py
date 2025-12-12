"""
Atomic Language System - Trackable Linguistic Units for Butterfly Engine

This module atomizes language concepts exactly like organism traits are atomized,
enabling full causation tracking and Butterfly Engine integration.

Each LinguisticAtom is a discrete, trackable unit that can:
- Be traced through causation chains
- Have its formation explained by Butterfly Chat
- Show temporal evolution of organism "vocabulary"
- Enable dialect emergence analysis

Architecture mirrors the trait system:
- Traits: organism.phenotype.traits['speed'] = 0.7
- Language: organism.linguistic_atoms['food'].strength = 0.7

This enables questions like:
- "Why did this organism develop the 'share-food' concept?"
- "What caused 'danger' to associate with 'friend'?"
- "How did this community's dialect emerge?"
"""

import time
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np
import json

logger = logging.getLogger(__name__)

# Try to import torch for tensor conversion
try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


@dataclass
class ConceptAssociation:
    """
    Association between two concepts - a trackable link.
    
    Like a synapse between linguistic neurons.
    """
    target_concept: str
    strength: float = 0.0  # -1.0 to 1.0 (negative = inhibition)
    formation_time: float = 0.0
    formation_reason: str = "unknown"
    update_count: int = 0
    last_update_time: float = 0.0
    
    # Quality tracking
    success_count: int = 0  # Times this association led to good outcome
    failure_count: int = 0  # Times this association led to bad outcome
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target': self.target_concept,
            'strength': self.strength,
            'formation_time': self.formation_time,
            'formation_reason': self.formation_reason,
            'update_count': self.update_count,
            'success_rate': self.success_count / max(1, self.success_count + self.failure_count)
        }


@dataclass
class LinguisticAtom:
    """
    Single trackable linguistic unit - like a trait but for language.
    
    Every change to this atom can be traced through the causation system.
    The Butterfly Engine can explain WHY any concept strengthened or weakened.
    
    Attributes:
        concept_id: Unique identifier (e.g., 'food', 'danger', 'share')
        strength: Salience of this concept for the organism (0.0 to 1.0)
        associations: Links to other concepts with strengths
        acquisition_time: When this concept was first acquired
        source: How acquired ('innate', 'observed', 'taught', 'discovered')
        semantic_frame: Category ('action', 'state', 'quality', 'relationship', etc.)
        abstraction_level: 0=concrete, 1=abstract, 2=meta
        usage_count: How often this concept has been "used" by the organism
        last_used_time: Last time this concept was activated
        vp_context: VP state when concept is most relevant
    """
    concept_id: str
    strength: float = 0.5
    associations: Dict[str, ConceptAssociation] = field(default_factory=dict)
    acquisition_time: float = 0.0
    source: str = "innate"  # 'innate', 'observed', 'taught', 'discovered', 'mutated'
    semantic_frame: str = "unknown"  # 'action', 'state', 'quality', 'relationship', 'temporal', 'spatial'
    abstraction_level: int = 0  # 0=concrete, 1=abstract, 2=meta
    
    # Usage tracking
    usage_count: int = 0
    last_used_time: float = 0.0
    activation_history: List[float] = field(default_factory=list)  # Recent activation timestamps
    
    # VP context (when is this concept most relevant?)
    vp_vitality_affinity: float = 0.5  # Activated at what vitality level?
    vp_pleasure_affinity: float = 0.5  # Activated at what pleasure level?
    
    # Event emitter callback (set by AtomicLanguageSystem)
    _event_emitter: Optional[Callable] = field(default=None, repr=False)
    _organism_id: Optional[str] = field(default=None, repr=False)
    
    def update_strength(self, delta: float, reason: str, emit_event: bool = True):
        """
        Update concept strength with full causation tracking.
        
        Args:
            delta: Change in strength (can be negative)
            reason: Why the change happened (for Butterfly Engine)
            emit_event: Whether to emit causation event
        """
        old_strength = self.strength
        self.strength = np.clip(self.strength + delta, 0.0, 1.0)
        self.last_used_time = time.time()
        self.usage_count += 1
        
        # Track activation history (keep last 20)
        self.activation_history.append(time.time())
        if len(self.activation_history) > 20:
            self.activation_history = self.activation_history[-20:]
        
        # Emit causation event for Butterfly Engine
        if emit_event and self._event_emitter and abs(delta) > 0.01:
            self._emit_atom_update(old_strength, reason)
    
    def _emit_atom_update(self, old_strength: float, reason: str):
        """Emit event for causation tracking."""
        if not self._event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='linguistic_atom_update',
                data={
                    'organism_id': self._organism_id,
                    'concept': self.concept_id,
                    'old_strength': old_strength,
                    'new_strength': self.strength,
                    'delta': self.strength - old_strength,
                    'reason': reason,
                    'source': self.source,
                    'semantic_frame': self.semantic_frame,
                    'usage_count': self.usage_count,
                    'association_count': len(self.associations)
                }
            )
            self._event_emitter(event)
        except ImportError:
            pass  # CausationExplorer not available
    
    def form_association(self, target_concept: str, strength: float, reason: str, emit_event: bool = True):
        """
        Form or strengthen association with another concept.
        
        Args:
            target_concept: The concept to associate with
            strength: Association strength (-1.0 to 1.0)
            reason: Why the association formed
            emit_event: Whether to emit causation event
        """
        current_time = time.time()
        
        if target_concept in self.associations:
            # Strengthen existing association
            old_strength = self.associations[target_concept].strength
            self.associations[target_concept].strength = np.clip(
                self.associations[target_concept].strength + strength * 0.3,  # Gradual update
                -1.0, 1.0
            )
            self.associations[target_concept].update_count += 1
            self.associations[target_concept].last_update_time = current_time
        else:
            # Create new association
            old_strength = 0.0
            self.associations[target_concept] = ConceptAssociation(
                target_concept=target_concept,
                strength=np.clip(strength, -1.0, 1.0),
                formation_time=current_time,
                formation_reason=reason
            )
        
        # Emit causation event
        if emit_event and self._event_emitter:
            self._emit_association_event(target_concept, old_strength, reason)
    
    def _emit_association_event(self, target_concept: str, old_strength: float, reason: str):
        """Emit event for association formation/update."""
        if not self._event_emitter:
            return
            
        try:
            from causation_explorer import Event
            new_strength = self.associations[target_concept].strength
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='association_formed' if old_strength == 0.0 else 'association_updated',
                data={
                    'organism_id': self._organism_id,
                    'source_concept': self.concept_id,
                    'target_concept': target_concept,
                    'old_strength': old_strength,
                    'new_strength': new_strength,
                    'reason': reason,
                    'is_new': old_strength == 0.0
                }
            )
            self._event_emitter(event)
        except ImportError:
            pass
    
    def get_top_associations(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N associated concepts by strength."""
        sorted_assocs = sorted(
            self.associations.items(),
            key=lambda x: abs(x[1].strength),
            reverse=True
        )
        return [(k, v.strength) for k, v in sorted_assocs[:n]]
    
    def decay(self, amount: float = 0.01):
        """Apply decay to strength (unused concepts fade)."""
        time_since_use = time.time() - self.last_used_time
        if time_since_use > 60:  # More than 60 seconds since use
            decay_factor = min(amount * (time_since_use / 60), 0.1)  # Cap decay
            if self.strength > 0.1:  # Don't decay below 0.1
                self.strength = max(0.1, self.strength - decay_factor)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize atom for storage/debugging."""
        return {
            'concept_id': self.concept_id,
            'strength': self.strength,
            'source': self.source,
            'semantic_frame': self.semantic_frame,
            'abstraction_level': self.abstraction_level,
            'usage_count': self.usage_count,
            'acquisition_time': self.acquisition_time,
            'associations': {k: v.to_dict() for k, v in self.associations.items()},
            'vp_affinity': {
                'vitality': self.vp_vitality_affinity,
                'pleasure': self.vp_pleasure_affinity
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinguisticAtom':
        """Deserialize atom from storage."""
        atom = cls(
            concept_id=data['concept_id'],
            strength=data.get('strength', 0.5),
            source=data.get('source', 'loaded'),
            semantic_frame=data.get('semantic_frame', 'unknown'),
            abstraction_level=data.get('abstraction_level', 0),
            usage_count=data.get('usage_count', 0),
            acquisition_time=data.get('acquisition_time', time.time())
        )
        
        # Restore associations
        for target, assoc_data in data.get('associations', {}).items():
            atom.associations[target] = ConceptAssociation(
                target_concept=target,
                strength=assoc_data.get('strength', 0.0),
                formation_time=assoc_data.get('formation_time', 0.0),
                formation_reason=assoc_data.get('formation_reason', 'loaded')
            )
        
        # Restore VP affinity
        vp_data = data.get('vp_affinity', {})
        atom.vp_vitality_affinity = vp_data.get('vitality', 0.5)
        atom.vp_pleasure_affinity = vp_data.get('pleasure', 0.5)
        
        return atom


class AtomicLanguageSystem:
    """
    Per-organism atomic language representation.
    
    Replaces monolithic vocabulary vectors with trackable discrete atoms.
    Each organism has its own AtomicLanguageSystem instance.
    
    Provides:
    - Full causation tracking for Butterfly Engine
    - Dialect emergence through differential atom development
    - VP-modulated concept salience
    - Association graphs between concepts
    - Conversion to dense tensors for neural network compatibility
    """
    
    # Innate vocabulary loaded from data/innate_vocab.json
    # Generated by generate_innate_vocab.py from nuclear extraction
    _INNATE_VOCAB_CACHE = None  # Class-level cache
    
    # Fallback core concepts if innate_vocab.json not found
    # CRITICAL: Must include all 6 action heads + key synonyms
    FALLBACK_INNATE_CONCEPTS = {
        # THE 6 ACTION HEADS (required for neural network action outputs)
        'move': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.5)},
        'rest': {'frame': 'action', 'level': 0, 'vp': (0.3, 0.6)},
        'reproduce': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.8)},
        'cooperate': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.7)},
        'compete': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.3)},
        'isolate': {'frame': 'action', 'level': 0, 'vp': (0.4, 0.4)},
        # Key synonyms for each action head
        'walk': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.5)},
        'run': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.5)},
        'sleep': {'frame': 'action', 'level': 0, 'vp': (0.2, 0.7)},
        'wait': {'frame': 'action', 'level': 0, 'vp': (0.3, 0.5)},
        'breed': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.8)},
        'spawn': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.8)},
        'help': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.7)},
        'ally': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.7)},
        'fight': {'frame': 'action', 'level': 0, 'vp': (0.7, 0.3)},
        'attack': {'frame': 'action', 'level': 0, 'vp': (0.7, 0.2)},
        'hide': {'frame': 'action', 'level': 0, 'vp': (0.4, 0.4)},
        'escape': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.4)},
        # State concepts
        'hungry': {'frame': 'state', 'level': 0, 'vp': (0.3, 0.3)},
        'safe': {'frame': 'state', 'level': 0, 'vp': (0.6, 0.7)},
        'danger': {'frame': 'state', 'level': 0, 'vp': (0.4, 0.2)},
        'alive': {'frame': 'state', 'level': 0, 'vp': (0.7, 0.7)},
        'strong': {'frame': 'state', 'level': 0, 'vp': (0.7, 0.6)},
        'weak': {'frame': 'state', 'level': 0, 'vp': (0.3, 0.4)},
        # Relationship concepts
        'friend': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.8)},
        'enemy': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.2)},
        'alone': {'frame': 'relationship', 'level': 0, 'vp': (0.4, 0.4)},
        'together': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.7)},
        # Resource concepts
        'food': {'frame': 'resource', 'level': 0, 'vp': (0.5, 0.7)},
        'energy': {'frame': 'resource', 'level': 0, 'vp': (0.6, 0.5)},
    }
    
    @classmethod
    def _load_innate_vocab(cls):
        """Load innate vocabulary from JSON file (cached at class level)."""
        if cls._INNATE_VOCAB_CACHE is not None:
            return cls._INNATE_VOCAB_CACHE
        
        from pathlib import Path
        innate_path = Path(__file__).parent.parent.parent / "data" / "innate_vocab.json"
        
        try:
            with open(innate_path, 'r', encoding='utf-8') as f:
                cls._INNATE_VOCAB_CACHE = json.load(f)
                logger.info(f"[ATOMIC_LANG] Loaded innate vocab: {len(cls._INNATE_VOCAB_CACHE.get('concepts', {}))} concepts")
                return cls._INNATE_VOCAB_CACHE
        except FileNotFoundError:
            logger.warning(f"[ATOMIC_LANG] innate_vocab.json not found, using fallback")
            cls._INNATE_VOCAB_CACHE = None
            return None
        except Exception as e:
            logger.error(f"[ATOMIC_LANG] Error loading innate_vocab.json: {e}")
            cls._INNATE_VOCAB_CACHE = None
            return None
    
    def __init__(self, organism_id: str, event_emitter: Optional[Callable] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize atomic language system for an organism.
        
        Args:
            organism_id: Unique identifier for the organism
            event_emitter: Callback to emit causation events
            config: Configuration dictionary
        """
        self.organism_id = organism_id
        self.event_emitter = event_emitter
        self.config = config or {}
        
        # Core storage
        self.atoms: Dict[str, LinguisticAtom] = {}
        
        # Ordered concept list for tensor conversion (deterministic order)
        self._concept_order: List[str] = []
        
        # Statistics
        self.total_concepts_acquired = 0
        self.total_associations_formed = 0
        self.creation_time = time.time()
        
        # Initialize with innate concepts
        self._initialize_innate_concepts()
        
        logger.debug(f"[ATOMIC_LANG] Initialized for organism {organism_id} with {len(self.atoms)} innate concepts")
    
    def _initialize_innate_concepts(self):
        """
        Initialize organism with innate (inherited) concepts from nuclear vocab.
        
        Loads from data/innate_vocab.json which contains:
        - Tier 1 (core): 50 words all organisms get
        - Tier 2 (extended): 200 words, organisms get random 20-50
        - Tier 3 (pool): 1450 words, organisms get random 0-10
        
        This creates vocabulary diversity while ensuring core survival concepts.
        """
        current_time = time.time()
        innate_data = self._load_innate_vocab()
        
        if innate_data is None:
            # Fallback to minimal hardcoded concepts
            logger.warning(f"[ATOMIC_LANG] Using fallback innate concepts for {self.organism_id}")
            for concept_id, info in self.FALLBACK_INNATE_CONCEPTS.items():
                atom = LinguisticAtom(
                    concept_id=concept_id,
                    strength=0.5 + np.random.uniform(-0.1, 0.1),
                    source='innate',
                    semantic_frame=info['frame'],
                    abstraction_level=info['level'],
                    acquisition_time=current_time,
                    vp_vitality_affinity=info['vp'][0],
                    vp_pleasure_affinity=info['vp'][1]
                )
                atom._event_emitter = self.event_emitter
                atom._organism_id = self.organism_id
                self.atoms[concept_id] = atom
                self._concept_order.append(concept_id)
            self.total_concepts_acquired = len(self.atoms)
            return
        
        # Load from innate_vocab.json
        concepts = innate_data.get('concepts', {})
        tiers = innate_data.get('tiers', {})
        tier_config = innate_data.get('tier_config', {})
        associations = innate_data.get('associations', [])
        
        # Tier 1: Core concepts (all organisms)
        core_words = tiers.get('core', [])
        for word in core_words:
            if word in concepts:
                self._add_innate_concept(word, concepts[word], current_time, 'innate_core', 0.6)
        
        # Tier 2: Extended concepts (random subset)
        extended_words = tiers.get('extended', [])
        ext_range = tier_config.get('extended_sample_range', [20, 50])
        num_extended = np.random.randint(ext_range[0], ext_range[1] + 1)
        
        if extended_words:
            selected_extended = list(np.random.choice(
                extended_words, 
                size=min(num_extended, len(extended_words)), 
                replace=False
            ))
            for word in selected_extended:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], current_time, 'innate_extended', 0.4)
        
        # Tier 3: Pool concepts (rare random additions)
        pool_words = tiers.get('pool', [])
        pool_range = tier_config.get('pool_sample_range', [0, 10])
        num_pool = np.random.randint(pool_range[0], pool_range[1] + 1)
        
        if pool_words and num_pool > 0:
            selected_pool = list(np.random.choice(
                pool_words,
                size=min(num_pool, len(pool_words)),
                replace=False
            ))
            for word in selected_pool:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], current_time, 'innate_rare', 0.25)
        
        # Initialize associations between innate concepts
        for assoc in associations:
            src = assoc.get('source', '')
            tgt = assoc.get('target', '')
            strength = assoc.get('strength', 0.5)
            
            if src in self.atoms and tgt in self.atoms:
                self.atoms[src].form_association(tgt, strength, 'innate', emit_event=False)
        
        self.total_concepts_acquired = len(self.atoms)
        logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id} initialized with {len(self.atoms)} innate concepts")
    
    def _add_innate_concept(self, word: str, info: dict, current_time: float, 
                           source: str, base_strength: float):
        """Helper to add an innate concept atom."""
        vp = info.get('vp', (0.5, 0.5))
        atom = LinguisticAtom(
            concept_id=word,
            strength=base_strength + np.random.uniform(-0.1, 0.1),
            source=source,
            semantic_frame=info.get('frame', 'unknown'),
            abstraction_level=info.get('level', 0),
            acquisition_time=current_time,
            vp_vitality_affinity=vp[0] if isinstance(vp, (list, tuple)) else 0.5,
            vp_pleasure_affinity=vp[1] if isinstance(vp, (list, tuple)) else 0.5
        )
        atom._event_emitter = self.event_emitter
        atom._organism_id = self.organism_id
        self.atoms[word] = atom
        self._concept_order.append(word)

    
    def acquire_concept(self, concept_id: str, source: str, semantic_frame: str = 'unknown',
                       initial_strength: float = 0.3, reason: str = "acquired") -> LinguisticAtom:
        """
        Acquire a new concept (learn a new word).
        
        This is a MAJOR EVENT for causation tracking - the organism
        learned something new!
        
        Args:
            concept_id: Unique concept identifier
            source: How acquired ('observed', 'taught', 'discovered')
            semantic_frame: Category of concept
            initial_strength: Starting strength
            reason: Why this concept was acquired
            
        Returns:
            The newly created or existing LinguisticAtom
        """
        if concept_id in self.atoms:
            # Already have this concept - strengthen it instead
            self.atoms[concept_id].update_strength(0.1, f"reinforced: {reason}")
            return self.atoms[concept_id]
        
        current_time = time.time()
        
        # Create new atom
        atom = LinguisticAtom(
            concept_id=concept_id,
            strength=initial_strength,
            source=source,
            semantic_frame=semantic_frame,
            abstraction_level=0 if semantic_frame in ['action', 'state', 'resource'] else 1,
            acquisition_time=current_time
        )
        atom._event_emitter = self.event_emitter
        atom._organism_id = self.organism_id
        
        self.atoms[concept_id] = atom
        self._concept_order.append(concept_id)
        self.total_concepts_acquired += 1
        
        # Emit concept acquisition event
        self._emit_concept_acquired(concept_id, source, reason)
        
        return atom
    
    def _emit_concept_acquired(self, concept_id: str, source: str, reason: str):
        """Emit event when organism acquires new concept."""
        if not self.event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='concept_acquired',
                data={
                    'organism_id': self.organism_id,
                    'concept': concept_id,
                    'source': source,
                    'reason': reason,
                    'total_concepts': len(self.atoms),
                    'semantic_frame': self.atoms[concept_id].semantic_frame
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    def strengthen_concept(self, concept_id: str, delta: float, reason: str):
        """
        Strengthen (or weaken) a concept.
        
        Args:
            concept_id: Concept to modify
            delta: Change in strength (positive or negative)
            reason: Why the change happened
        """
        if concept_id not in self.atoms:
            logger.debug(f"[ATOMIC_LANG] Cannot strengthen unknown concept: {concept_id}")
            return
            
        self.atoms[concept_id].update_strength(delta, reason)
    
    def form_association(self, source_concept: str, target_concept: str, 
                        strength: float, reason: str):
        """
        Form association between two concepts.
        
        This is how organisms build semantic networks - by linking
        concepts through experience.
        
        Args:
            source_concept: The primary concept
            target_concept: The concept to associate with
            strength: Association strength (-1.0 to 1.0)
            reason: Why this association formed
        """
        # Ensure both concepts exist
        if source_concept not in self.atoms:
            self.acquire_concept(source_concept, 'implicit', reason=f"needed for association with {target_concept}")
        if target_concept not in self.atoms:
            self.acquire_concept(target_concept, 'implicit', reason=f"needed for association with {source_concept}")
        
        # Form the association
        self.atoms[source_concept].form_association(target_concept, strength, reason)
        self.total_associations_formed += 1
    
    def get_activated_concepts(self, vp_state: Tuple[float, float], 
                               context: Optional[str] = None,
                               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Get concepts most activated by current VP state and context.
        
        This is how organisms "think" - VP state activates relevant concepts.
        
        Args:
            vp_state: (vitality, pleasure) tuple
            context: Optional context string
            top_k: Number of top concepts to return
            
        Returns:
            List of (concept_id, activation_score) tuples
        """
        vitality, pleasure = vp_state
        activations = []
        
        for concept_id, atom in self.atoms.items():
            # Base activation from strength
            activation = atom.strength
            
            # VP affinity modulation
            vp_match = 1.0 - 0.5 * (
                abs(vitality - atom.vp_vitality_affinity) +
                abs(pleasure - atom.vp_pleasure_affinity)
            )
            activation *= vp_match
            
            # Recency boost
            if atom.last_used_time > 0:
                recency = 1.0 / (1.0 + (time.time() - atom.last_used_time) / 60)
                activation *= (0.7 + 0.3 * recency)
            
            activations.append((concept_id, activation))
        
        # Sort by activation
        activations.sort(key=lambda x: x[1], reverse=True)
        return activations[:top_k]
    
    def get_associated_concepts(self, concept_id: str, min_strength: float = 0.2) -> List[Tuple[str, float]]:
        """
        Get concepts associated with a given concept.
        
        Args:
            concept_id: The concept to get associations for
            min_strength: Minimum association strength
            
        Returns:
            List of (associated_concept, strength) tuples
        """
        if concept_id not in self.atoms:
            return []
            
        associations = []
        for target, assoc in self.atoms[concept_id].associations.items():
            if abs(assoc.strength) >= min_strength:
                associations.append((target, assoc.strength))
        
        return sorted(associations, key=lambda x: abs(x[1]), reverse=True)
    
    def get_word_vector(self, word: str, embedding_dim: int = 64) -> Optional[np.ndarray]:
        """
        Get a semantic vector for a specific word based on its atomic properties.
        
        This is THE ROOT for vector retrieval — embeddings derived directly from
        the organism's learned atomic structure (strength, associations, VP affinity).
        
        Vector components (64-dim default):
        - [0]: strength (salience)
        - [1]: usage_count normalized
        - [2]: abstraction_level
        - [3]: vp_vitality_affinity
        - [4]: vp_pleasure_affinity
        - [5-14]: semantic frame one-hot (10 frames)
        - [15-64]: association vector (top associations hashed to positions)
        
        Args:
            word: The word/concept to get vector for
            embedding_dim: Desired vector dimension (default 64)
            
        Returns:
            Numpy array of shape (embedding_dim,) or None if word not in atoms
        """
        if word not in self.atoms:
            return None
        
        atom = self.atoms[word]
        vec = np.zeros(embedding_dim, dtype=np.float32)
        
        # Core properties [0-4]
        vec[0] = atom.strength
        vec[1] = min(atom.usage_count / 100.0, 1.0)  # Normalize usage
        vec[2] = atom.abstraction_level / 2.0  # 0, 0.5, or 1.0
        vec[3] = atom.vp_vitality_affinity
        vec[4] = atom.vp_pleasure_affinity
        
        # Semantic frame one-hot [5-14]
        frame_map = {
            'action': 5, 'state': 6, 'quality': 7, 'relationship': 8,
            'temporal': 9, 'spatial': 10, 'resource': 11, 'unknown': 12,
            'innate_core': 13, 'innate_extended': 14
        }
        frame_idx = frame_map.get(atom.semantic_frame, 12)
        if frame_idx < embedding_dim:
            vec[frame_idx] = 1.0
        
        # Association vector [15-64]: hash associations into remaining dimensions
        assoc_start = 15
        assoc_dim = embedding_dim - assoc_start
        if assoc_dim > 0 and atom.associations:
            for target, assoc in atom.associations.items():
                # Hash target word to position in association subspace
                hash_idx = hash(target) % assoc_dim
                vec[assoc_start + hash_idx] += assoc.strength * 0.5
        
        # Normalize association subspace
        assoc_slice = vec[assoc_start:]
        assoc_norm = np.linalg.norm(assoc_slice)
        if assoc_norm > 0:
            vec[assoc_start:] = assoc_slice / assoc_norm
        
        return vec
    
    def find_similar_words(self, query_word: str, top_k: int = 10, 
                          min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """
        Find words most similar to query using atomic-derived vectors.
        
        This is VECTOR RETRIEVAL rooted in the atomic vocabulary itself.
        
        Args:
            query_word: Word to find similar words for
            top_k: Number of results
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of (word, similarity) tuples sorted by similarity descending
        """
        query_vec = self.get_word_vector(query_word)
        if query_vec is None:
            return []
        
        # Normalize query
        query_norm = np.linalg.norm(query_vec)
        if query_norm < 1e-8:
            return []
        query_vec = query_vec / query_norm
        
        results = []
        for word in self.atoms:
            if word == query_word:
                continue
            
            word_vec = self.get_word_vector(word)
            if word_vec is None:
                continue
            
            # Cosine similarity
            word_norm = np.linalg.norm(word_vec)
            if word_norm < 1e-8:
                continue
            
            similarity = np.dot(query_vec, word_vec / word_norm)
            if similarity >= min_similarity:
                results.append((word, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def find_words_for_state(self, organism_state: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find words whose atomic vectors are most similar to organism state.
        
        Enables ASSOCIATIVE REASONING: organism state → relevant words.
        
        Args:
            organism_state: Organism's state vector (any dimension, will be projected)
            top_k: Number of results
            
        Returns:
            List of (word, similarity) tuples
        """
        if organism_state is None or len(organism_state) == 0:
            return []
        
        # Project state to 64-dim (truncate or pad)
        embedding_dim = 64
        state_vec = np.zeros(embedding_dim, dtype=np.float32)
        copy_len = min(len(organism_state), embedding_dim)
        state_vec[:copy_len] = organism_state[:copy_len]
        
        # Normalize
        state_norm = np.linalg.norm(state_vec)
        if state_norm < 1e-8:
            return []
        state_vec = state_vec / state_norm
        
        results = []
        for word in self.atoms:
            word_vec = self.get_word_vector(word, embedding_dim)
            if word_vec is None:
                continue
            
            word_norm = np.linalg.norm(word_vec)
            if word_norm < 1e-8:
                continue
            
            similarity = np.dot(state_vec, word_vec / word_norm)
            results.append((word, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def query_vocabulary(self, 
                        query_word: str = None,
                        organism_state: np.ndarray = None,
                        curiosity: float = 0.5,
                        aggression: float = 0.5,
                        social_affinity: float = 0.5,
                        exploration_rate: float = 0.1,
                        top_k: int = 10) -> List[Tuple[str, float]]:
        """
        TRAIT-DRIVEN SEMANTIC QUERY: Use organism reasoning traits to guide word retrieval.
        
        This is THE QUERY MECHANIC that makes vector search behavioral.
        
        How traits affect the search:
        - curiosity (0-1): Higher = broader search, more associations explored, 
                          more novel/rare words surfaced
        - aggression (0-1): Higher = prefer action words, competitive concepts
                           Lower = prefer state words, passive concepts
        - social_affinity (0-1): Higher = prefer relationship/cooperation words
                                Lower = prefer solitary/individual concepts  
        - exploration_rate (0-1): Random exploration - chance to include random words
                                 for serendipitous discovery
        
        Args:
            query_word: Seed word to expand from (optional)
            organism_state: State vector to match (optional)
            curiosity: Organism's curiosity trait [0-1]
            aggression: Organism's aggression trait [0-1]
            social_affinity: Organism's social trait [0-1]
            exploration_rate: Chance of random exploration [0-1]
            top_k: Number of results to return
            
        Returns:
            List of (word, score) tuples sorted by trait-adjusted relevance
        """
        word_scores: Dict[str, float] = {}
        
        # Step 1: Seed from query word (if provided)
        if query_word and query_word in self.atoms:
            # Base: similar words
            similar = self.find_similar_words(query_word, top_k=int(top_k * (1 + curiosity)))
            for word, sim in similar:
                word_scores[word] = word_scores.get(word, 0.0) + sim
            
            # Curiosity: follow more association chains
            if curiosity > 0.3:
                atom = self.atoms[query_word]
                # More curious = explore more associations
                num_assoc = int(len(atom.associations) * curiosity)
                for target, assoc in list(atom.associations.items())[:num_assoc]:
                    if target in self.atoms:
                        word_scores[target] = word_scores.get(target, 0.0) + abs(assoc.strength) * curiosity
                        # High curiosity: follow second-order associations
                        if curiosity > 0.7 and target in self.atoms:
                            for t2, a2 in list(self.atoms[target].associations.items())[:3]:
                                if t2 in self.atoms and t2 != query_word:
                                    word_scores[t2] = word_scores.get(t2, 0.0) + abs(a2.strength) * curiosity * 0.5
        
        # Step 2: Seed from organism state (if provided)
        if organism_state is not None:
            state_words = self.find_words_for_state(organism_state, top_k=top_k)
            for word, sim in state_words:
                word_scores[word] = word_scores.get(word, 0.0) + sim * 0.8
        
        # Step 3: Apply trait-based filtering/boosting
        for word in list(word_scores.keys()):
            if word not in self.atoms:
                continue
            atom = self.atoms[word]
            
            # Aggression bias: boost action words, penalize passive
            if atom.semantic_frame == 'action':
                word_scores[word] *= (1.0 + aggression * 0.5)  # Up to 50% boost for aggressive
            elif atom.semantic_frame == 'state':
                word_scores[word] *= (1.0 - aggression * 0.3)  # Up to 30% penalty for aggressive
            
            # Social affinity bias: boost relationship words
            if atom.semantic_frame == 'relationship':
                word_scores[word] *= (1.0 + social_affinity * 0.5)
            
            # Curiosity bonus for rare/novel words (low usage)
            if curiosity > 0.5 and atom.usage_count < 5:
                word_scores[word] *= (1.0 + (curiosity - 0.5) * 0.4)  # Up to 20% bonus
            
            # Skepticism (inverse curiosity): prefer well-established words
            skepticism = 1.0 - curiosity
            if skepticism > 0.5 and atom.usage_count > 10:
                word_scores[word] *= (1.0 + (skepticism - 0.5) * 0.3)
        
        # Step 4: Exploration - random word injection
        if exploration_rate > 0 and len(self.atoms) > 0:
            num_random = max(1, int(top_k * exploration_rate))
            all_words = list(self.atoms.keys())
            for _ in range(num_random):
                if np.random.random() < exploration_rate:
                    random_word = np.random.choice(all_words)
                    if random_word not in word_scores:
                        # Random words get base score scaled by exploration
                        word_scores[random_word] = 0.3 * exploration_rate
        
        # Step 5: Sort and return
        sorted_results = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def to_embedding(self, embedding_dim: Optional[int] = None) -> np.ndarray:
        """
        Convert atomic representation to dense vector for neural network.
        
        This bridges atomic tracking with neural efficiency.
        
        Args:
            embedding_dim: Desired embedding dimension (default: num_concepts)
            
        Returns:
            Dense numpy array representing linguistic state
        """
        # Extract strengths in deterministic order
        strengths = np.array([self.atoms[c].strength for c in self._concept_order])
        
        if embedding_dim is None or embedding_dim == len(strengths):
            return strengths
        
        # Project to desired dimension (simple linear projection for now)
        if embedding_dim < len(strengths):
            # Downsample by taking top concepts
            indices = np.argsort(strengths)[-embedding_dim:]
            return strengths[indices]
        else:
            # Upsample by padding
            result = np.zeros(embedding_dim)
            result[:len(strengths)] = strengths
            return result
    
    def to_tensor(self, embedding_dim: Optional[int] = None) -> 'torch.Tensor':
        """
        Convert to PyTorch tensor for neural network integration.
        
        Args:
            embedding_dim: Desired embedding dimension
            
        Returns:
            PyTorch tensor
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch required for tensor conversion")
        
        embedding = self.to_embedding(embedding_dim)
        return torch.FloatTensor(embedding)
    
    def get_concept_graph(self) -> Dict[str, Any]:
        """
        Get full concept graph for visualization.
        
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        nodes = []
        edges = []
        
        for concept_id, atom in self.atoms.items():
            nodes.append({
                'id': concept_id,
                'strength': atom.strength,
                'frame': atom.semantic_frame,
                'source': atom.source
            })
            
            for target, assoc in atom.associations.items():
                edges.append({
                    'source': concept_id,
                    'target': target,
                    'strength': assoc.strength,
                    'reason': assoc.formation_reason
                })
        
        return {'nodes': nodes, 'edges': edges}
    
    def compute_dialect_signature(self, fixed_length: int = 32) -> np.ndarray:
        """
        Compute a signature vector representing this organism's "dialect".
        
        Used for clustering organisms by linguistic similarity.
        
        Args:
            fixed_length: Fixed length for the signature vector (default 32)
        
        Returns:
            Normalized signature vector of fixed length
        """
        # Combine concept strengths with association patterns
        signature = []
        
        # Concept strengths (normalized) - use sorted concepts
        sorted_concepts = sorted(self._concept_order)
        for concept_id in sorted_concepts[:fixed_length - 4]:  # Reserve 4 slots for meta-features
            signature.append(self.atoms[concept_id].strength)
        
        # Pad to fixed_length - 4 if fewer concepts
        while len(signature) < fixed_length - 4:
            signature.append(0.0)
        
        # Add association density metrics
        total_associations = sum(len(a.associations) for a in self.atoms.values())
        signature.append(total_associations / max(1, len(self.atoms)))
        
        # Add abstraction level distribution
        level_counts = defaultdict(int)
        for atom in self.atoms.values():
            level_counts[atom.abstraction_level] += 1
        
        for level in range(3):
            signature.append(level_counts[level] / max(1, len(self.atoms)))
        
        return np.array(signature, dtype=np.float32)
    
    def apply_experience(self, action: int, outcome: float, context: Dict[str, Any]):
        """
        Update language atoms based on organism experience.
        
        This is called after each organism action to update linguistic
        representation based on what happened.
        
        Args:
            action: Action index taken (0-5)
            outcome: Reward/outcome of action (-1 to 1)
            context: Additional context (VP state, nearby organisms, etc.)
        """
        action_concepts = ['rest', 'move', 'eat', 'reproduce', 'attack', 'cooperate']
        
        if 0 <= action < len(action_concepts):
            action_concept = action_concepts[action]
            
            # Strengthen action concept based on outcome
            if outcome > 0:
                reason = f"positive_outcome_{outcome:.2f}"
                self.strengthen_concept(action_concept, outcome * 0.1, reason)
            else:
                reason = f"negative_outcome_{outcome:.2f}"
                self.strengthen_concept(action_concept, outcome * 0.05, reason)  # Slower weakening
            
            # Form associations based on context
            vp_state = context.get('vp_state', (0.5, 0.5))
            
            # If hungry and ate successfully, strengthen food-eat association
            if action == 2 and outcome > 0:  # EAT
                self.form_association('hungry', 'eat', outcome * 0.3, 'successful_eating')
                self.form_association('food', 'eat', outcome * 0.2, 'successful_eating')
            
            # If cooperated successfully, strengthen social associations
            if action == 5 and outcome > 0:  # COOPERATE
                self.form_association('friend', 'cooperate', outcome * 0.3, 'successful_cooperation')
                self.form_association('together', 'cooperate', outcome * 0.2, 'successful_cooperation')
            
            # If attacked and outcome was positive, strengthen attack associations
            if action == 4 and outcome > 0:  # ATTACK
                self.form_association('strong', 'attack', outcome * 0.2, 'successful_attack')
    
    # =========================================================================
    # 🆕 CONCEPT TRADING - Knowledge propagation between organisms
    # Organisms can teach/learn concepts from each other
    # This is memetic evolution - useful concepts spread through population
    # =========================================================================
    
    def teach_concept(self, concept_id: str, learner: 'AtomicLanguageSystem', 
                     teaching_strength: float = 0.5) -> Dict[str, Any]:
        """
        Teach a concept to another organism.
        
        The TEACHER retains the concept (knowledge is not depleted).
        The LEARNER acquires or reinforces the concept.
        
        This mirrors human knowledge transfer - I can teach you something
        without losing that knowledge myself.
        
        Args:
            concept_id: The concept to teach
            learner: The AtomicLanguageSystem of the learning organism
            teaching_strength: How effectively the concept is transferred (0-1)
            
        Returns:
            Dictionary with teaching results
        """
        if concept_id not in self.atoms:
            return {'success': False, 'reason': 'teacher_lacks_concept'}
        
        teacher_atom = self.atoms[concept_id]
        
        # Teaching effectiveness depends on:
        # 1. Teacher's concept strength (can't teach what you barely know)
        # 2. Teaching strength parameter (relationship quality)
        # 3. Teacher's usage count (experience with concept)
        teacher_expertise = min(1.0, teacher_atom.strength * (1 + teacher_atom.usage_count * 0.01))
        effective_strength = teaching_strength * teacher_expertise * 0.5
        
        current_time = time.time()
        result = {
            'concept': concept_id,
            'teacher_id': self.organism_id,
            'learner_id': learner.organism_id,
            'teacher_strength': teacher_atom.strength,
            'effective_transfer': effective_strength
        }
        
        if concept_id in learner.atoms:
            # Learner already has concept - reinforce it
            old_strength = learner.atoms[concept_id].strength
            learner.strengthen_concept(
                concept_id, 
                effective_strength * 0.3,  # Smaller boost for reinforcement
                f"taught_by_{self.organism_id}"
            )
            result['action'] = 'reinforced'
            result['old_strength'] = old_strength
            result['new_strength'] = learner.atoms[concept_id].strength
        else:
            # Learner doesn't have concept - they acquire it
            learner.acquire_concept(
                concept_id,
                source='taught',
                semantic_frame=teacher_atom.semantic_frame,
                initial_strength=effective_strength,
                reason=f"learned_from_{self.organism_id}"
            )
            result['action'] = 'acquired'
            result['new_strength'] = effective_strength
        
        # Also transfer top associations (teaching the context, not just the word)
        top_associations = teacher_atom.get_top_associations(n=3)
        transferred_associations = []
        for assoc_concept, assoc_strength in top_associations:
            if assoc_concept in self.atoms:  # Only transfer if teacher knows target
                learner.form_association(
                    concept_id, assoc_concept,
                    assoc_strength * teaching_strength * 0.3,  # Weaker than direct learning
                    f"association_from_{self.organism_id}"
                )
                transferred_associations.append(assoc_concept)
        
        result['transferred_associations'] = transferred_associations
        
        # Emit teaching event for causation tracking
        self._emit_teaching_event(result)
        
        # Strengthen teacher's own concept (teaching reinforces knowledge)
        self.strengthen_concept(concept_id, 0.02, "taught_concept")
        
        return result
    
    def _emit_teaching_event(self, result: Dict[str, Any]):
        """Emit event for concept teaching."""
        if not self.event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='concept_taught',
                data={
                    'teacher_id': result['teacher_id'],
                    'learner_id': result['learner_id'],
                    'concept': result['concept'],
                    'action': result['action'],
                    'teacher_strength': result['teacher_strength'],
                    'effective_transfer': result['effective_transfer'],
                    'transferred_associations': result.get('transferred_associations', [])
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    def learn_from_observation(self, observed_organism: 'AtomicLanguageSystem',
                               observed_action: int, observed_outcome: float) -> List[str]:
        """
        Learn concepts by observing another organism's behavior.
        
        This is social learning - watching what works for others.
        
        Args:
            observed_organism: The organism being observed
            observed_action: What action they took
            observed_outcome: What happened (positive/negative)
            
        Returns:
            List of concepts learned/reinforced
        """
        learned = []
        action_concepts = ['rest', 'move', 'eat', 'reproduce', 'attack', 'cooperate']
        
        if 0 <= observed_action < len(action_concepts):
            action_concept = action_concepts[observed_action]
            
            # Only learn from successful observations
            if observed_outcome > 0.3:
                # Check what concepts the observed organism has strong
                for concept_id, atom in observed_organism.atoms.items():
                    if atom.strength > 0.6:  # Strong concepts worth learning
                        if concept_id not in self.atoms:
                            # Acquire new concept through observation
                            self.acquire_concept(
                                concept_id, 'observed',
                                semantic_frame=atom.semantic_frame,
                                initial_strength=0.2,  # Weaker than direct teaching
                                reason=f"observed_{observed_organism.organism_id}_{action_concept}"
                            )
                            learned.append(concept_id)
                        else:
                            # Reinforce existing concept
                            self.strengthen_concept(
                                concept_id, 0.05,
                                f"observed_{observed_organism.organism_id}"
                            )
                
                # Learn association between action and outcome
                self.form_association(
                    action_concept, 'success',
                    observed_outcome * 0.2,
                    f"observed_{observed_organism.organism_id}"
                )
        
        return learned
    
    def get_teachable_concepts(self, min_strength: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get concepts this organism can effectively teach.
        
        Args:
            min_strength: Minimum concept strength to be teachable
            
        Returns:
            List of (concept_id, strength) tuples for teachable concepts
        """
        teachable = []
        for concept_id, atom in self.atoms.items():
            if atom.strength >= min_strength and atom.usage_count > 0:
                # Teachability score: strength * usage experience
                score = atom.strength * min(1.0, 1 + atom.usage_count * 0.05)
                teachable.append((concept_id, score))
        
        return sorted(teachable, key=lambda x: x[1], reverse=True)
    
    def get_learning_priorities(self, population_concepts: Dict[str, float]) -> List[str]:
        """
        Get concepts this organism should prioritize learning.
        
        Args:
            population_concepts: Dict of concept_id -> avg_strength in population
            
        Returns:
            List of concept_ids this organism lacks but population values
        """
        priorities = []
        for concept_id, pop_strength in population_concepts.items():
            if concept_id not in self.atoms:
                # Don't have it at all
                priorities.append((concept_id, pop_strength))
            elif self.atoms[concept_id].strength < pop_strength * 0.5:
                # Have it but much weaker than population average
                priorities.append((concept_id, pop_strength - self.atoms[concept_id].strength))
        
        return [c for c, _ in sorted(priorities, key=lambda x: x[1], reverse=True)]
    
    def decay_unused(self, decay_rate: float = 0.01):
        """Apply decay to unused concepts."""
        for atom in self.atoms.values():
            atom.decay(decay_rate)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this language system."""
        return {
            'organism_id': self.organism_id,
            'total_concepts': len(self.atoms),
            'total_associations': sum(len(a.associations) for a in self.atoms.values()),
            'avg_strength': np.mean([a.strength for a in self.atoms.values()]),
            'concepts_by_source': dict(Counter(a.source for a in self.atoms.values())),
            'concepts_by_frame': dict(Counter(a.semantic_frame for a in self.atoms.values())),
            'age': time.time() - self.creation_time
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize full system for storage."""
        return {
            'organism_id': self.organism_id,
            'atoms': {cid: atom.to_dict() for cid, atom in self.atoms.items()},
            'concept_order': self._concept_order,
            'creation_time': self.creation_time,
            'stats': self.get_stats()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], event_emitter: Optional[Callable] = None) -> 'AtomicLanguageSystem':
        """Deserialize from storage."""
        system = cls(
            organism_id=data['organism_id'],
            event_emitter=event_emitter
        )
        
        # Clear innate concepts and load from data
        system.atoms.clear()
        system._concept_order = data.get('concept_order', [])
        
        for concept_id, atom_data in data.get('atoms', {}).items():
            atom = LinguisticAtom.from_dict(atom_data)
            atom._event_emitter = event_emitter
            atom._organism_id = data['organism_id']
            system.atoms[concept_id] = atom
        
        system.creation_time = data.get('creation_time', time.time())
        
        return system


class DialectAnalyzer:
    """
    Analyzes dialect emergence across population using atomic language data.
    
    Uses clustering (HDBSCAN) on dialect signatures to identify
    emergent language communities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.last_analysis_time = 0
        self.dialect_clusters: Dict[int, List[str]] = {}  # cluster_id -> organism_ids
        
    def analyze_dialects(self, language_systems: Dict[str, AtomicLanguageSystem]) -> Dict[str, Any]:
        """
        Analyze dialect patterns across population.
        
        Args:
            language_systems: Dict mapping organism_id to AtomicLanguageSystem
            
        Returns:
            Analysis results including clusters and diversity metrics
        """
        if len(language_systems) < 3:
            return {'clusters': {}, 'diversity': 0.0, 'message': 'Too few organisms for analysis'}
        
        # Compute dialect signatures
        signatures = []
        organism_ids = []
        
        for org_id, lang_sys in language_systems.items():
            sig = lang_sys.compute_dialect_signature()
            signatures.append(sig)
            organism_ids.append(org_id)
        
        # Normalize signatures
        signatures = np.array(signatures)
        if signatures.std() > 0:
            signatures = (signatures - signatures.mean(axis=0)) / (signatures.std(axis=0) + 1e-8)
        
        # Try HDBSCAN clustering
        try:
            from sklearn.cluster import HDBSCAN
            clusterer = HDBSCAN(min_cluster_size=max(2, len(signatures) // 10))
            labels = clusterer.fit_predict(signatures)
        except ImportError:
            # Fallback: simple k-means
            from sklearn.cluster import KMeans
            n_clusters = max(2, len(signatures) // 20)
            labels = KMeans(n_clusters=n_clusters, n_init=10).fit_predict(signatures)
        
        # Build cluster mapping
        clusters = defaultdict(list)
        for org_id, label in zip(organism_ids, labels):
            clusters[int(label)].append(org_id)
        
        self.dialect_clusters = dict(clusters)
        
        # Compute diversity (number of unique clusters excluding noise)
        valid_clusters = [c for c in clusters.keys() if c >= 0]
        diversity = len(valid_clusters) / max(1, len(language_systems))
        
        return {
            'clusters': self.dialect_clusters,
            'num_clusters': len(valid_clusters),
            'diversity': diversity,
            'largest_cluster': max(len(c) for c in clusters.values()) if clusters else 0
        }
    
    def get_cluster_concepts(self, language_systems: Dict[str, AtomicLanguageSystem], 
                            cluster_id: int) -> Dict[str, float]:
        """
        Get characteristic concepts for a dialect cluster.
        
        Args:
            language_systems: All language systems
            cluster_id: Cluster to analyze
            
        Returns:
            Dict mapping concept_id to average strength in cluster
        """
        if cluster_id not in self.dialect_clusters:
            return {}
        
        concept_strengths = defaultdict(list)
        
        for org_id in self.dialect_clusters[cluster_id]:
            if org_id in language_systems:
                for concept_id, atom in language_systems[org_id].atoms.items():
                    concept_strengths[concept_id].append(atom.strength)
        
        return {
            concept: np.mean(strengths) 
            for concept, strengths in concept_strengths.items()
        }
