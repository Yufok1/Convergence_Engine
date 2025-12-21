"""
💊 ORGANISM STATE CAPSULE
=========================

Complete serialization of an organism's existence.

When an organism proves itself through the Highlander Protocol,
we capture its ENTIRE state - not just weights, but everything
that makes it uniquely adapted to its environment.

This is the "soul jar" - the complete snapshot of emergent consciousness.

Captures:
- Neural network weights (PyTorch state_dict)
- VP history and current state
- Atomic Language (all concepts, associations, dialect signature)
- Atomic Config (optimized hyperparameters)
- Trait atoms (behavioral phenotype)
- Causation subgraph (relevant event history)
- Environment context (what it adapted to)
- Fitness trajectory (how it evolved)

Restoration:
- Full organism resurrection from capsule
- Partial restoration (e.g., language only)
- Cross-pollination (inject concepts from one into another)
- Lineage tracking (parent capsules)

Author: Convergence Engine Team
Created: 2024
"""

import torch
import numpy as np
import json
import pickle
import gzip
import hashlib
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import io
import base64


class CapsuleVersion(Enum):
    """Capsule format versions for backward compatibility."""
    V1_BASIC = "1.0"
    V2_ATOMIC = "2.0"  # Adds atomic language/config
    V3_HIGHLANDER = "3.0"  # Adds Highlander metadata
    CURRENT = "3.0"


@dataclass
class VPSnapshot:
    """Snapshot of Vitality-Pleasure state."""
    vitality: float
    pleasure: float
    violation_pressure: float
    vitality_history: List[float]
    pleasure_history: List[float]
    vp_trajectory: List[Tuple[float, float]]  # [(v, p), ...]
    critical_events: List[Dict[str, Any]]  # Times VP hit critical
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VPSnapshot':
        return cls(**data)


@dataclass
class NeuralSnapshot:
    """Snapshot of neural network state."""
    state_dict_bytes: bytes  # Compressed state_dict
    architecture_hash: str  # For compatibility checking
    hidden_size: int
    num_layers: int
    input_size: int
    output_size: int
    total_parameters: int
    training_steps: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_dict_b64': base64.b64encode(self.state_dict_bytes).decode('utf-8'),
            'architecture_hash': self.architecture_hash,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'input_size': self.input_size,
            'output_size': self.output_size,
            'total_parameters': self.total_parameters,
            'training_steps': self.training_steps
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuralSnapshot':
        return cls(
            state_dict_bytes=base64.b64decode(data['state_dict_b64']),
            architecture_hash=data['architecture_hash'],
            hidden_size=data['hidden_size'],
            num_layers=data['num_layers'],
            input_size=data['input_size'],
            output_size=data['output_size'],
            total_parameters=data['total_parameters'],
            training_steps=data['training_steps']
        )


@dataclass
class LanguageSnapshot:
    """Snapshot of atomic language state."""
    atoms: Dict[str, Dict[str, Any]]  # concept_id -> atom.to_dict()
    dialect_signature: List[float]
    total_concepts: int
    concept_order: List[str]
    strongest_concepts: List[Tuple[str, float]]  # Top 10
    unique_concepts: List[str]  # Concepts not in default set
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LanguageSnapshot':
        return cls(**data)


@dataclass
class ConfigSnapshot:
    """Snapshot of atomic config state."""
    atoms: Dict[str, Dict[str, Any]]  # param_name -> atom.to_dict()
    domains: Dict[str, List[str]]  # domain -> param names
    best_performing: List[Tuple[str, float]]
    config_signature: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigSnapshot':
        return cls(**data)


@dataclass
class ExperienceSnapshot:
    """
    Snapshot of organism's experiential learning state.
    
    This captures what the organism has LEARNED through interaction,
    not just its static weights. Critical for:
    - Continued learning from where it left off
    - Language model training data
    - Behavioral context
    """
    action_history: List[int]  # Recent action sequence
    state_history: List[List[float]]  # Recent state vectors
    token_sequence: List[int]  # Token IDs for language model
    epsilon: float  # Current exploration rate
    alliance_reputation: float  # Social standing
    alliance_id: Optional[str]  # Current alliance
    confederation_tier: int  # Alliance level
    battle_wins: int
    battle_losses: int
    cross_alliance_connections: int
    experience_samples: List[Dict[str, Any]]  # Sample of experience buffer
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperienceSnapshot':
        return cls(**data)


@dataclass
class TraitSnapshot:
    """Snapshot of trait atoms (behavioral phenotype)."""
    traits: Dict[str, Dict[str, Any]]  # trait_name -> trait data
    phenotype_cluster: Optional[int]  # Which behavioral cluster
    behavioral_signature: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraitSnapshot':
        return cls(**data)


@dataclass
class EnvironmentContext:
    """Context the organism adapted to."""
    resource_distribution: Dict[str, float]
    population_size_at_capture: int
    avg_population_fitness: float
    competition_intensity: float
    predation_pressure: float
    cooperation_level: float
    environment_hash: str  # For matching environments
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentContext':
        return cls(**data)


@dataclass
class HighlanderMetadata:
    """Highlander Protocol survival metadata."""
    battles_won: int
    battles_lost: int
    organisms_absorbed: int
    concepts_absorbed: List[str]
    configs_absorbed: Dict[str, Any]
    survival_streak: int  # Consecutive tournament wins
    peak_fitness: float
    peak_fitness_time: float
    lineage: List[str]  # IDs of ancestors
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HighlanderMetadata':
        return cls(**data)


@dataclass
class FitnessTrajectory:
    """How fitness evolved over time."""
    fitness_history: List[Tuple[float, float]]  # [(time, fitness), ...]
    milestone_events: List[Dict[str, Any]]  # Significant fitness jumps
    fitness_components: Dict[str, float]  # Breakdown of current fitness
    relative_rank_history: List[float]  # Percentile rank over time
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FitnessTrajectory':
        return cls(**data)


@dataclass
class CausationDigest:
    """Compressed causation history - key events that shaped this organism."""
    key_events: List[Dict[str, Any]]  # Most influential events
    event_count_by_type: Dict[str, int]
    causal_chains: List[List[str]]  # Important causal sequences
    turning_points: List[Dict[str, Any]]  # Events that changed trajectory
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CausationDigest':
        return cls(**data)


@dataclass
class SemanticConvergenceSnapshot:
    """
    🔗 SEMANTIC CONVERGENCE SNAPSHOT
    
    Captures the organism's contribution to unified word embeddings.
    This is CRITICAL for portable agents to maintain their unique "voice".
    
    The Semantic Convergence system unifies 6 systems:
    - ContextMemory (word embeddings)
    - LanguageTeacher (word assignment)
    - ConceptSystem (axiom embeddings)
    - LinguisticKnowledgeWeb (semantic relations)
    - ConceptTracker (emergent concepts)
    - AtomicLanguage (organism-local concepts)
    """
    # Words this organism has influenced
    organism_words: List[str]  # Words assigned to this organism
    word_frequencies: Dict[str, int]  # How often each word was used
    
    # Word embedding contributions (base64-encoded for JSON compatibility)
    word_embeddings_b64: Optional[str] = None  # Compressed word embeddings for org's words
    embedding_dim: int = 64
    
    # Axiom embeddings from ConceptSystem (grounded concepts)
    axiom_embeddings: Dict[str, List[float]] = field(default_factory=dict)  # good/bad/self/other
    
    # Language anchor info
    language_anchor_count: int = 0  # How many words anchored to this organism
    
    # Teaching history
    words_taught_count: int = 0
    teaching_generations: List[int] = field(default_factory=list)  # Generations when taught
    
    # Semantic config at capture time
    semantic_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'organism_words': self.organism_words,
            'word_frequencies': self.word_frequencies,
            'word_embeddings_b64': self.word_embeddings_b64,
            'embedding_dim': self.embedding_dim,
            'axiom_embeddings': self.axiom_embeddings,
            'language_anchor_count': self.language_anchor_count,
            'words_taught_count': self.words_taught_count,
            'teaching_generations': self.teaching_generations,
            'semantic_config': self.semantic_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticConvergenceSnapshot':
        return cls(
            organism_words=data.get('organism_words', []),
            word_frequencies=data.get('word_frequencies', {}),
            word_embeddings_b64=data.get('word_embeddings_b64'),
            embedding_dim=data.get('embedding_dim', 64),
            axiom_embeddings=data.get('axiom_embeddings', {}),
            language_anchor_count=data.get('language_anchor_count', 0),
            words_taught_count=data.get('words_taught_count', 0),
            teaching_generations=data.get('teaching_generations', []),
            semantic_config=data.get('semantic_config', {})
        )


@dataclass
class OrganismCapsule:
    """
    Complete state capsule for an organism.
    
    This is the "soul jar" - everything needed to resurrect
    or study an organism's complete existence.
    """
    # Identity
    organism_id: str
    capsule_id: str  # Unique capsule identifier
    version: str = CapsuleVersion.CURRENT.value
    
    # Timestamps
    creation_time: float = 0.0
    organism_birth_time: float = 0.0
    organism_age: float = 0.0  # Time steps lived
    
    # Core state
    neural: Optional[NeuralSnapshot] = None
    vp: Optional[VPSnapshot] = None
    language: Optional[LanguageSnapshot] = None
    config: Optional[ConfigSnapshot] = None
    traits: Optional[TraitSnapshot] = None
    
    # Experiential state (what the organism has LEARNED)
    experience: Optional[ExperienceSnapshot] = None
    
    # Context
    environment: Optional[EnvironmentContext] = None
    fitness: Optional[FitnessTrajectory] = None
    highlander: Optional[HighlanderMetadata] = None
    causation: Optional[CausationDigest] = None
    
    # Semantic Convergence state (word embeddings, language anchors)
    semantic_convergence: Optional[SemanticConvergenceSnapshot] = None
    
    # Metadata
    capture_reason: str = "manual"  # 'highlander_champion', 'fitness_milestone', 'manual', etc.
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Integrity
    checksum: str = ""
    
    def __post_init__(self):
        if self.creation_time == 0.0:
            self.creation_time = time.time()
        if not self.capsule_id:
            self.capsule_id = self._generate_capsule_id()
    
    def _generate_capsule_id(self) -> str:
        """Generate unique capsule ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{self.organism_id}_{timestamp}_{time.time()}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"capsule_{self.organism_id}_{timestamp}_{short_hash}"
    
    def compute_checksum(self) -> str:
        """Compute integrity checksum."""
        # Serialize without checksum field
        data = self.to_dict()
        data.pop('checksum', None)
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify capsule hasn't been corrupted."""
        return self.checksum == self.compute_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'organism_id': self.organism_id,
            'capsule_id': self.capsule_id,
            'version': self.version,
            'creation_time': self.creation_time,
            'organism_birth_time': self.organism_birth_time,
            'organism_age': self.organism_age,
            'neural': self.neural.to_dict() if self.neural else None,
            'vp': self.vp.to_dict() if self.vp else None,
            'language': self.language.to_dict() if self.language else None,
            'config': self.config.to_dict() if self.config else None,
            'traits': self.traits.to_dict() if self.traits else None,
            'experience': self.experience.to_dict() if self.experience else None,
            'environment': self.environment.to_dict() if self.environment else None,
            'fitness': self.fitness.to_dict() if self.fitness else None,
            'highlander': self.highlander.to_dict() if self.highlander else None,
            'causation': self.causation.to_dict() if self.causation else None,
            'semantic_convergence': self.semantic_convergence.to_dict() if self.semantic_convergence else None,
            'capture_reason': self.capture_reason,
            'notes': self.notes,
            'tags': self.tags,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrganismCapsule':
        """Deserialize from dictionary."""
        return cls(
            organism_id=data['organism_id'],
            capsule_id=data['capsule_id'],
            version=data.get('version', CapsuleVersion.V1_BASIC.value),
            creation_time=data.get('creation_time', 0.0),
            organism_birth_time=data.get('organism_birth_time', 0.0),
            organism_age=data.get('organism_age', 0.0),
            neural=NeuralSnapshot.from_dict(data['neural']) if data.get('neural') else None,
            vp=VPSnapshot.from_dict(data['vp']) if data.get('vp') else None,
            language=LanguageSnapshot.from_dict(data['language']) if data.get('language') else None,
            config=ConfigSnapshot.from_dict(data['config']) if data.get('config') else None,
            traits=TraitSnapshot.from_dict(data['traits']) if data.get('traits') else None,
            experience=ExperienceSnapshot.from_dict(data['experience']) if data.get('experience') else None,
            environment=EnvironmentContext.from_dict(data['environment']) if data.get('environment') else None,
            fitness=FitnessTrajectory.from_dict(data['fitness']) if data.get('fitness') else None,
            highlander=HighlanderMetadata.from_dict(data['highlander']) if data.get('highlander') else None,
            causation=CausationDigest.from_dict(data['causation']) if data.get('causation') else None,
            semantic_convergence=SemanticConvergenceSnapshot.from_dict(data['semantic_convergence']) if data.get('semantic_convergence') else None,
            capture_reason=data.get('capture_reason', 'loaded'),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
            checksum=data.get('checksum', '')
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get human-readable summary of capsule contents."""
        summary = {
            'id': self.capsule_id,
            'organism': self.organism_id,
            'captured': datetime.fromtimestamp(self.creation_time).isoformat(),
            'age': self.organism_age,
            'reason': self.capture_reason,
            'components': []
        }
        
        if self.neural:
            summary['components'].append(f"🧠 Neural ({self.neural.total_parameters:,} params)")
        if self.vp:
            summary['components'].append(f"💓 VP (v={self.vp.vitality:.2f}, p={self.vp.pleasure:.2f})")
        if self.language:
            summary['components'].append(f"💬 Language ({self.language.total_concepts} concepts)")
        if self.config:
            summary['components'].append(f"⚙️ Config ({len(self.config.atoms)} atoms)")
        if self.traits:
            summary['components'].append(f"🧬 Traits ({len(self.traits.traits)} traits)")
        if self.highlander:
            summary['components'].append(f"⚔️ Highlander ({self.highlander.battles_won}W-{self.highlander.battles_lost}L)")
        if self.fitness:
            peak = self.fitness.fitness_history[-1][1] if self.fitness.fitness_history else 0
            summary['components'].append(f"📈 Fitness (peak={peak:.3f})")
        if self.semantic_convergence:
            summary['components'].append(f"🔗 Semantic ({len(self.semantic_convergence.organism_words)} words, {self.semantic_convergence.language_anchor_count} anchors)")
        
        summary['tags'] = self.tags
        summary['integrity'] = '✅' if self.verify_integrity() else '❌'
        
        return summary


class OrganismCapsuleManager:
    """
    Manages creation, storage, and restoration of organism capsules.
    
    The vault for consciousness snapshots.
    """
    
    def __init__(self, storage_dir: str = "./capsules"):
        """
        Initialize capsule manager.
        
        Args:
            storage_dir: Directory to store capsule files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Index of known capsules
        self.capsule_index: Dict[str, Dict[str, Any]] = {}
        self._load_index()
    
    def _load_index(self):
        """Load capsule index from storage."""
        index_file = self.storage_dir / "capsule_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.capsule_index = json.load(f)
    
    def _save_index(self):
        """Save capsule index to storage."""
        index_file = self.storage_dir / "capsule_index.json"
        with open(index_file, 'w') as f:
            json.dump(self.capsule_index, f, indent=2)
    
    def capture_organism(self, organism: Any, 
                        reason: str = "manual",
                        notes: str = "",
                        tags: Optional[List[str]] = None,
                        include_causation: bool = True,
                        causation_explorer: Optional[Any] = None,
                        context_memory: Optional[Any] = None,
                        concept_system: Optional[Any] = None) -> OrganismCapsule:
        """
        Capture complete organism state into a capsule.
        
        Args:
            organism: The NeuralOrganism to capture
            reason: Why this capture is happening
            notes: Additional notes
            tags: Tags for categorization
            include_causation: Whether to include causation history
            causation_explorer: CausationExplorer for event history
            context_memory: ContextMemory for semantic convergence data
            concept_system: ConceptSystem for axiom embeddings
            
        Returns:
            OrganismCapsule with complete state
        """
        current_time = time.time()
        
        capsule = OrganismCapsule(
            organism_id=organism.species_id,
            capsule_id="",  # Will be generated
            organism_birth_time=getattr(organism, 'birth_time', current_time),
            organism_age=getattr(organism, 'age', 0),
            capture_reason=reason,
            notes=notes,
            tags=tags or []
        )
        
        # ═══════════════════════════════════════════════════════════════
        # NEURAL STATE
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'brain') and organism.brain is not None:
            capsule.neural = self._capture_neural(organism.brain)
        
        # ═══════════════════════════════════════════════════════════════
        # VP STATE
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'vitality') and hasattr(organism, 'pleasure'):
            capsule.vp = self._capture_vp(organism)
        
        # ═══════════════════════════════════════════════════════════════
        # ATOMIC LANGUAGE
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'atomic_language') and organism.atomic_language is not None:
            capsule.language = self._capture_language(organism.atomic_language)
        
        # ═══════════════════════════════════════════════════════════════
        # ATOMIC CONFIG
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'config_system') and organism.config_system is not None:
            capsule.config = self._capture_config(organism.config_system)
        
        # ═══════════════════════════════════════════════════════════════
        # TRAITS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'traits') and organism.traits is not None:
            capsule.traits = self._capture_traits(organism)
        
        # ═══════════════════════════════════════════════════════════════
        # EXPERIENCE (What the organism has LEARNED through interaction)
        # ═══════════════════════════════════════════════════════════════
        capsule.experience = self._capture_experience(organism)
        
        # ═══════════════════════════════════════════════════════════════
        # FITNESS
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'fitness') and organism.fitness is not None:
            capsule.fitness = self._capture_fitness(organism)
        
        # ═══════════════════════════════════════════════════════════════
        # HIGHLANDER METADATA
        # ═══════════════════════════════════════════════════════════════
        if hasattr(organism, 'highlander_stats') and organism.highlander_stats is not None:
            capsule.highlander = self._capture_highlander(organism)
        
        # ═══════════════════════════════════════════════════════════════
        # CAUSATION DIGEST
        # ═══════════════════════════════════════════════════════════════
        if include_causation and causation_explorer:
            capsule.causation = self._capture_causation(organism.species_id, causation_explorer)
        
        # ═══════════════════════════════════════════════════════════════
        # SEMANTIC CONVERGENCE (word embeddings, language anchors)
        # ═══════════════════════════════════════════════════════════════
        if context_memory is not None:
            capsule.semantic_convergence = self._capture_semantic_convergence(
                organism, context_memory, concept_system
            )
        
        # Compute checksum
        capsule.checksum = capsule.compute_checksum()
        
        return capsule
    
    def _capture_neural(self, brain: torch.nn.Module) -> NeuralSnapshot:
        """Capture neural network state."""
        # Serialize state dict to bytes
        buffer = io.BytesIO()
        torch.save(brain.state_dict(), buffer)
        state_bytes = gzip.compress(buffer.getvalue())
        
        # Compute architecture hash
        arch_str = str(brain)
        arch_hash = hashlib.md5(arch_str.encode()).hexdigest()
        
        # Count parameters
        total_params = sum(p.numel() for p in brain.parameters())
        
        # Get architecture details - OrganismBrain uses _dim suffix not _size
        hidden_size = getattr(brain, 'hidden_dim', None) or getattr(brain, 'hidden_size', 64)
        num_layers = getattr(brain, 'num_layers', 2)
        input_size = getattr(brain, 'input_dim', None) or getattr(brain, 'input_size', 30)
        output_size = getattr(brain, 'output_dim', None) or getattr(brain, 'output_size', 6)
        training_steps = getattr(brain, 'training_steps', 0)
        
        return NeuralSnapshot(
            state_dict_bytes=state_bytes,
            architecture_hash=arch_hash,
            hidden_size=hidden_size,
            num_layers=num_layers,
            input_size=input_size,
            output_size=output_size,
            total_parameters=total_params,
            training_steps=training_steps
        )
    
    def _capture_vp(self, organism: Any) -> VPSnapshot:
        """Capture VP state."""
        # Get history if available
        v_history = getattr(organism, 'vitality_history', [organism.vitality])[-100:]
        p_history = getattr(organism, 'pleasure_history', [organism.pleasure])[-100:]
        
        # Build trajectory
        trajectory = list(zip(v_history, p_history))
        
        # Find critical events (VP below threshold)
        critical = getattr(organism, 'critical_events', [])
        
        return VPSnapshot(
            vitality=organism.vitality,
            pleasure=organism.pleasure,
            violation_pressure=getattr(organism, 'violation_pressure', 0.0),
            vitality_history=list(v_history),
            pleasure_history=list(p_history),
            vp_trajectory=trajectory,
            critical_events=critical
        )
    
    def _capture_language(self, lang_system: Any) -> LanguageSnapshot:
        """Capture atomic language state."""
        # Serialize all atoms
        atoms_dict = {}
        for concept_id, atom in lang_system.atoms.items():
            atoms_dict[concept_id] = atom.to_dict()
        
        # Get dialect signature
        dialect_sig = lang_system.compute_dialect_signature()
        
        # Find strongest concepts
        sorted_atoms = sorted(
            lang_system.atoms.items(),
            key=lambda x: x[1].strength,
            reverse=True
        )
        strongest = [(c, a.strength) for c, a in sorted_atoms[:10]]
        
        # Find unique concepts (not in default innate set)
        # Includes canonical actions: move, cooperate, compete, rest, reproduce, isolate
        # Plus common concepts from innate vocabulary
        default_concepts = {
            'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate',  # canonical 6 actions
            'explore', 'share', 'hoard', 'signal', 'hide', 'seek', 'flee',  # common behaviors
            'danger', 'safety', 'food', 'mate', 'threat', 'friend', 'enemy',  # survival concepts
            'existence', 'life', 'energy', 'strong', 'weak'  # core states
        }
        unique = [c for c in lang_system.atoms.keys() if c not in default_concepts]
        
        return LanguageSnapshot(
            atoms=atoms_dict,
            dialect_signature=list(dialect_sig) if isinstance(dialect_sig, np.ndarray) else dialect_sig,
            total_concepts=len(lang_system.atoms),
            concept_order=lang_system._concept_order.copy(),
            strongest_concepts=strongest,
            unique_concepts=unique
        )
    
    def _capture_config(self, config_system: Any) -> ConfigSnapshot:
        """Capture atomic config state."""
        atoms_dict = {}
        for param_name, atom in config_system.atoms.items():
            atoms_dict[param_name] = atom.to_dict()
        
        # Get domain groupings
        domains = {}
        for domain, params in config_system.domains.items():
            domains[domain.value] = list(params)
        
        # Best performing params
        sorted_atoms = sorted(
            config_system.atoms.items(),
            key=lambda x: x[1].get_value_performance(),
            reverse=True
        )
        best = [(p, a.get_value_performance()) for p, a in sorted_atoms[:5]]
        
        # Config signature
        signature = config_system.get_config_signature()
        
        return ConfigSnapshot(
            atoms=atoms_dict,
            domains=domains,
            best_performing=best,
            config_signature=list(signature)
        )
    
    def _capture_traits(self, organism: Any) -> TraitSnapshot:
        """Capture trait state."""
        traits_dict = {}
        if hasattr(organism, 'traits') and organism.traits:
            for trait_name, trait in organism.traits.items():
                if hasattr(trait, 'to_dict'):
                    traits_dict[trait_name] = trait.to_dict()
                else:
                    traits_dict[trait_name] = {'value': trait}
        
        # Behavioral signature if available
        if hasattr(organism, 'get_behavioral_signature'):
            sig = organism.get_behavioral_signature()
            behavioral_sig = list(sig) if isinstance(sig, np.ndarray) else sig
        else:
            behavioral_sig = []
        
        return TraitSnapshot(
            traits=traits_dict,
            phenotype_cluster=getattr(organism, 'phenotype_cluster', None),
            behavioral_signature=behavioral_sig
        )
    
    def _capture_experience(self, organism: Any) -> ExperienceSnapshot:
        """
        Capture experiential learning state.
        
        This is what makes the organism SMART - its learned behaviors,
        not just static weights.
        """
        # Action history
        action_history = list(getattr(organism, 'action_history', []))
        
        # State history (convert numpy arrays to lists)
        state_history_raw = list(getattr(organism, 'state_history', []))
        state_history = []
        for state in state_history_raw[-50:]:  # Keep last 50
            if hasattr(state, 'tolist'):
                state_history.append(state.tolist())
            elif isinstance(state, (list, tuple)):
                state_history.append(list(state))
        
        # Token sequence for language model
        token_sequence = list(getattr(organism, 'token_sequence', []))
        
        # Exploration rate
        epsilon = float(getattr(organism, 'epsilon', 0.0))
        
        # Alliance/social state
        alliance_reputation = float(getattr(organism, 'alliance_reputation', 0.5))
        alliance_id = getattr(organism, 'alliance_id', None)
        if alliance_id is not None:
            alliance_id = str(alliance_id)
        confederation_tier = int(getattr(organism, 'confederation_tier', 0))
        
        # Battle record
        battle_wins = int(getattr(organism, 'battle_wins', 0))
        battle_losses = int(getattr(organism, 'battle_losses', 0))
        cross_alliance = int(getattr(organism, 'cross_alliance_connections', 0))
        
        # Sample from experience buffer (don't export entire buffer - too big)
        experience_samples = []
        exp_buffer = getattr(organism, 'experience_buffer', None)
        if exp_buffer and hasattr(exp_buffer, 'buffer'):
            buffer_list = list(exp_buffer.buffer)
            # Sample up to 100 recent experiences
            sample_size = min(100, len(buffer_list))
            if sample_size > 0:
                for exp in buffer_list[-sample_size:]:
                    try:
                        sample = {
                            'state': exp.state.tolist() if hasattr(exp.state, 'tolist') else list(exp.state),
                            'action': int(exp.action),
                            'reward': float(exp.reward),
                            'next_state': exp.next_state.tolist() if hasattr(exp.next_state, 'tolist') else list(exp.next_state),
                            'done': bool(exp.done)
                        }
                        experience_samples.append(sample)
                    except Exception:
                        pass  # Skip malformed experiences
        
        return ExperienceSnapshot(
            action_history=action_history[-100:],  # Last 100 actions
            state_history=state_history,
            token_sequence=token_sequence[-200:],  # Last 200 tokens
            epsilon=epsilon,
            alliance_reputation=alliance_reputation,
            alliance_id=alliance_id,
            confederation_tier=confederation_tier,
            battle_wins=battle_wins,
            battle_losses=battle_losses,
            cross_alliance_connections=cross_alliance,
            experience_samples=experience_samples
        )
    
    def _capture_fitness(self, organism: Any) -> FitnessTrajectory:
        """Capture fitness history."""
        # Get fitness history
        history = getattr(organism, 'fitness_history', [])
        if not history and hasattr(organism, 'fitness'):
            history = [(time.time(), organism.fitness)]
        
        # Find milestone events
        milestones = getattr(organism, 'fitness_milestones', [])
        
        # Fitness component breakdown
        components = {}
        if hasattr(organism, 'get_fitness_components'):
            components = organism.get_fitness_components()
        
        # Relative rank history
        rank_history = getattr(organism, 'rank_history', [])
        
        return FitnessTrajectory(
            fitness_history=history,
            milestone_events=milestones,
            fitness_components=components,
            relative_rank_history=rank_history
        )
    
    def _capture_highlander(self, organism: Any) -> HighlanderMetadata:
        """Capture Highlander Protocol metadata."""
        stats = organism.highlander_stats
        return HighlanderMetadata(
            battles_won=stats.get('battles_won', 0),
            battles_lost=stats.get('battles_lost', 0),
            organisms_absorbed=stats.get('organisms_absorbed', 0),
            concepts_absorbed=stats.get('concepts_absorbed', []),
            configs_absorbed=stats.get('configs_absorbed', {}),
            survival_streak=stats.get('survival_streak', 0),
            peak_fitness=stats.get('peak_fitness', 0.0),
            peak_fitness_time=stats.get('peak_fitness_time', 0.0),
            lineage=stats.get('lineage', [])
        )
    
    def _capture_causation(self, organism_id: str, explorer: Any) -> CausationDigest:
        """Capture causation history digest."""
        # Get events for this organism
        events = []
        event_counts = {}
        
        if hasattr(explorer, 'events'):
            for event_id, event in explorer.events.items():
                if event.data.get('organism_id') == organism_id:
                    events.append({
                        'id': event_id,
                        'type': event.event_type,
                        'time': event.timestamp,
                        'component': event.component
                    })
                    event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Keep only most recent/important events
        events = sorted(events, key=lambda x: x['time'], reverse=True)[:100]
        
        # Find turning points (large fitness changes, etc.)
        turning_points = []  # Would need more context to identify these
        
        return CausationDigest(
            key_events=events,
            event_count_by_type=event_counts,
            causal_chains=[],  # Would need graph analysis
            turning_points=turning_points
        )
    
    def _capture_semantic_convergence(self, organism: Any, context_memory: Any, 
                                      concept_system: Optional[Any] = None) -> SemanticConvergenceSnapshot:
        """
        🔗 Capture semantic convergence state for this organism.
        
        This captures:
        - Words assigned to this organism (language anchors)
        - Word embeddings for those words
        - Axiom embeddings from ConceptSystem
        - Teaching history
        
        Args:
            organism: The organism being captured
            context_memory: ContextMemory instance with word embeddings and anchors
            concept_system: Optional ConceptSystem for axiom embeddings
            
        Returns:
            SemanticConvergenceSnapshot with all semantic data
        """
        organism_id = organism.species_id if hasattr(organism, 'species_id') else str(id(organism))
        # Convert to int hash if string for lookup
        org_id_hash = hash(organism_id) if isinstance(organism_id, str) else organism_id
        
        # Get words assigned to this organism
        organism_words = []
        word_frequencies = {}
        
        if hasattr(context_memory, 'node_word_associations'):
            words_set = context_memory.node_word_associations.get(org_id_hash, set())
            organism_words = list(words_set)
        
        # Get word frequencies
        if hasattr(context_memory, 'word_frequencies') and organism_words:
            for word in organism_words:
                freq = context_memory.word_frequencies.get(word, 0)
                if freq > 0:
                    word_frequencies[word] = freq
        
        # Capture word embeddings for this organism's words
        word_embeddings_b64 = None
        embedding_dim = 64
        
        if (hasattr(context_memory, 'word_embedding') and 
            context_memory.word_embedding is not None and
            hasattr(context_memory, 'vocabulary') and 
            context_memory.vocabulary is not None and
            organism_words):
            try:
                import torch
                import zlib
                embedding_dim = context_memory.embedding_dim
                
                # Extract embeddings for organism's words
                embeddings_dict = {}
                for word in organism_words[:200]:  # Limit to top 200 words
                    token_id = context_memory.vocabulary.get_id(word)
                    if token_id is not None and token_id < context_memory.word_embedding.weight.shape[0]:
                        embed = context_memory.word_embedding.weight[token_id].detach().cpu().numpy().tolist()
                        embeddings_dict[word] = embed
                
                if embeddings_dict:
                    # Serialize and compress
                    embed_json = json.dumps(embeddings_dict)
                    embed_bytes = zlib.compress(embed_json.encode('utf-8'), level=9)
                    word_embeddings_b64 = base64.b64encode(embed_bytes).decode('ascii')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not capture word embeddings: {e}")
        
        # Capture axiom embeddings from ConceptSystem
        axiom_embeddings = {}
        if concept_system is not None and hasattr(concept_system, 'export_concept_embeddings'):
            try:
                import torch
                # Get organism state for grounding
                if hasattr(organism, 'get_state_features'):
                    state_np = organism.get_state_features(None, None, None)
                    if state_np is not None and len(state_np) >= 18:
                        state_tensor = torch.from_numpy(state_np).float()
                        axiom_embeds = concept_system.export_concept_embeddings(state_tensor)
                        for axiom_name, embed in axiom_embeds.items():
                            if isinstance(embed, (torch.Tensor, np.ndarray)):
                                axiom_embeddings[axiom_name] = embed.tolist() if hasattr(embed, 'tolist') else list(embed)
                            else:
                                axiom_embeddings[axiom_name] = list(embed)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not capture axiom embeddings: {e}")
        
        # Count language anchors
        language_anchor_count = 0
        if hasattr(context_memory, 'language_anchors'):
            for word, org_ids in context_memory.language_anchors.items():
                if org_id_hash in org_ids:
                    language_anchor_count += 1
        
        # Get teaching history from LanguageTeacher stats if available
        words_taught_count = len(organism_words)
        teaching_generations = []
        
        # Get semantic config
        semantic_config = {}
        if hasattr(context_memory, 'organism_embedding_alpha'):
            semantic_config['organism_embedding_alpha'] = context_memory.organism_embedding_alpha
        if hasattr(context_memory, 'use_learned_embeddings'):
            semantic_config['use_learned_embeddings'] = context_memory.use_learned_embeddings
        if hasattr(context_memory, 'embedding_dim'):
            semantic_config['embedding_dim'] = context_memory.embedding_dim
        if hasattr(context_memory, 'max_vocab_size'):
            semantic_config['max_vocab_size'] = context_memory.max_vocab_size
        
        return SemanticConvergenceSnapshot(
            organism_words=organism_words,
            word_frequencies=word_frequencies,
            word_embeddings_b64=word_embeddings_b64,
            embedding_dim=embedding_dim,
            axiom_embeddings=axiom_embeddings,
            language_anchor_count=language_anchor_count,
            words_taught_count=words_taught_count,
            teaching_generations=teaching_generations,
            semantic_config=semantic_config
        )

    def save_capsule(self, capsule: OrganismCapsule, 
                    compress: bool = True) -> str:
        """
        Save capsule to storage.
        
        Args:
            capsule: The capsule to save
            compress: Whether to gzip the file
            
        Returns:
            Path to saved file
        """
        filename = f"{capsule.capsule_id}.capsule"
        if compress:
            filename += ".gz"
        
        filepath = self.storage_dir / filename
        
        data = capsule.to_dict()
        json_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')
        
        if compress:
            with gzip.open(filepath, 'wb') as f:
                f.write(json_bytes)
        else:
            with open(filepath, 'wb') as f:
                f.write(json_bytes)
        
        # Update index
        self.capsule_index[capsule.capsule_id] = {
            'organism_id': capsule.organism_id,
            'filepath': str(filepath),
            'creation_time': capsule.creation_time,
            'reason': capsule.capture_reason,
            'tags': capsule.tags,
            'summary': capsule.get_summary()
        }
        self._save_index()
        
        return str(filepath)
    
    def load_capsule(self, capsule_id: str) -> Optional[OrganismCapsule]:
        """
        Load capsule from storage.
        
        Args:
            capsule_id: ID of capsule to load
            
        Returns:
            Loaded OrganismCapsule or None if not found
        """
        if capsule_id not in self.capsule_index:
            return None
        
        filepath = Path(self.capsule_index[capsule_id]['filepath'])
        if not filepath.exists():
            return None
        
        if filepath.suffix == '.gz':
            with gzip.open(filepath, 'rb') as f:
                data = json.loads(f.read().decode('utf-8'))
        else:
            with open(filepath, 'rb') as f:
                data = json.loads(f.read().decode('utf-8'))
        
        capsule = OrganismCapsule.from_dict(data)
        
        # Verify integrity
        if not capsule.verify_integrity():
            print(f"⚠️ Warning: Capsule {capsule_id} failed integrity check!")
        
        return capsule
    
    def restore_neural(self, capsule: OrganismCapsule, 
                      target_brain: torch.nn.Module) -> bool:
        """
        Restore neural network weights from capsule.
        
        Args:
            capsule: Capsule containing neural state
            target_brain: Neural network to restore into
            
        Returns:
            True if successful
        """
        if not capsule.neural:
            return False
        
        # Check architecture compatibility
        target_hash = hashlib.md5(str(target_brain).encode()).hexdigest()
        if target_hash != capsule.neural.architecture_hash:
            print("⚠️ Warning: Architecture mismatch, restoration may fail")
        
        # Decompress and load state dict
        state_bytes = gzip.decompress(capsule.neural.state_dict_bytes)
        buffer = io.BytesIO(state_bytes)
        state_dict = torch.load(buffer, weights_only=True)
        
        try:
            # Use strict=False to handle architecture changes (e.g., num_key_compositions)
            target_brain.load_state_dict(state_dict, strict=False)
            return True
        except Exception as e:
            print(f"❌ Failed to restore neural state: {e}")
            return False
    
    def restore_language(self, capsule: OrganismCapsule,
                        target_language_system: Any) -> bool:
        """
        Restore atomic language from capsule.
        
        MASTERY-GATED: Respects vocabulary caps when restoring.
        
        Args:
            capsule: Capsule containing language state
            target_language_system: AtomicLanguageSystem to restore into
            
        Returns:
            True if successful
        """
        if not capsule.language:
            return False
        
        try:
            # Clear existing atoms
            target_language_system.atoms.clear()
            target_language_system._concept_order.clear()
            
            # Restore from snapshot
            from reality_simulator.language.atomic_language import LinguisticAtom
            
            # MASTERY CHECK: Get vocab cap for organism's level
            mastery_level = getattr(target_language_system, '_mastery_level', 0)
            vocab_caps = getattr(target_language_system, '_mastery_vocab_sizes', [6, 26, 76, 276, 10000])
            max_vocab = vocab_caps[mastery_level] if mastery_level < len(vocab_caps) else 10000
            
            # Sort atoms by strength so we keep strongest if we hit cap
            sorted_atoms = sorted(
                capsule.language.atoms.items(),
                key=lambda x: x[1].get('strength', 0.5),
                reverse=True
            )[:max_vocab]  # Cap at max vocab for level
            
            for concept_id, atom_dict in sorted_atoms:
                atom = LinguisticAtom(
                    concept_id=concept_id,
                    strength=atom_dict.get('strength', 0.5),
                    source=atom_dict.get('source', 'restored'),
                    semantic_frame=atom_dict.get('semantic_frame', 'unknown'),
                    abstraction_level=atom_dict.get('abstraction_level', 0)
                )
                target_language_system.atoms[concept_id] = atom
                target_language_system._concept_order.append(concept_id)
            
            if len(capsule.language.atoms) > max_vocab:
                print(f"⚠️ Trimmed language restore from {len(capsule.language.atoms)} to {max_vocab} (mastery level {mastery_level})")
            
            return True
        except Exception as e:
            print(f"❌ Failed to restore language: {e}")
            return False
    
    def inject_concepts(self, capsule: OrganismCapsule,
                       target_language_system: Any,
                       concepts: Optional[List[str]] = None) -> int:
        """
        Inject specific concepts from capsule into target organism.
        
        Like a "mind meld" - selective knowledge transfer.
        
        Args:
            capsule: Capsule containing language state
            target_language_system: AtomicLanguageSystem to inject into
            concepts: Specific concepts to inject (None = inject unique concepts)
            
        Returns:
            Number of concepts injected
        """
        if not capsule.language:
            return 0
        
        if concepts is None:
            concepts = capsule.language.unique_concepts
        
        injected = 0
        for concept_id in concepts:
            if concept_id not in capsule.language.atoms:
                continue
            
            atom_dict = capsule.language.atoms[concept_id]
            
            # Use acquire_concept or direct add
            if hasattr(target_language_system, 'acquire_concept'):
                target_language_system.acquire_concept(
                    concept_id,
                    source='capsule_injection',
                    semantic_frame=atom_dict.get('semantic_frame', 'unknown'),
                    initial_strength=atom_dict.get('strength', 0.3),
                    reason=f"injected_from_{capsule.organism_id}"
                )
                injected += 1
        
        return injected
    
    def list_capsules(self, 
                     organism_id: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     reason: Optional[str] = None) -> List[Dict[str, Any]]:
        """List capsules matching criteria."""
        results = []
        
        for capsule_id, info in self.capsule_index.items():
            if organism_id and info['organism_id'] != organism_id:
                continue
            if reason and info['reason'] != reason:
                continue
            if tags:
                if not any(t in info.get('tags', []) for t in tags):
                    continue
            
            results.append({
                'capsule_id': capsule_id,
                **info
            })
        
        return sorted(results, key=lambda x: x['creation_time'], reverse=True)
    
    def get_champion_capsule(self) -> Optional[OrganismCapsule]:
        """Get the most recent Highlander champion capsule."""
        champions = self.list_capsules(reason='highlander_champion')
        if champions:
            return self.load_capsule(champions[0]['capsule_id'])
        return None


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def quick_capture(organism: Any, 
                 reason: str = "manual",
                 storage_dir: str = "./capsules") -> str:
    """Quick capture and save organism."""
    manager = OrganismCapsuleManager(storage_dir)
    capsule = manager.capture_organism(organism, reason=reason)
    return manager.save_capsule(capsule)


def quick_restore_brain(filepath: str, 
                       target_brain: torch.nn.Module,
                       storage_dir: str = "./capsules") -> bool:
    """Quick restore neural network from capsule file."""
    manager = OrganismCapsuleManager(storage_dir)
    capsule_id = Path(filepath).stem.replace('.capsule', '')
    capsule = manager.load_capsule(capsule_id)
    if capsule:
        return manager.restore_neural(capsule, target_brain)
    return False
