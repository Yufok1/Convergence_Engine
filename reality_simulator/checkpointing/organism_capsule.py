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
    
    # Context
    environment: Optional[EnvironmentContext] = None
    fitness: Optional[FitnessTrajectory] = None
    highlander: Optional[HighlanderMetadata] = None
    causation: Optional[CausationDigest] = None
    
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
            'environment': self.environment.to_dict() if self.environment else None,
            'fitness': self.fitness.to_dict() if self.fitness else None,
            'highlander': self.highlander.to_dict() if self.highlander else None,
            'causation': self.causation.to_dict() if self.causation else None,
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
            environment=EnvironmentContext.from_dict(data['environment']) if data.get('environment') else None,
            fitness=FitnessTrajectory.from_dict(data['fitness']) if data.get('fitness') else None,
            highlander=HighlanderMetadata.from_dict(data['highlander']) if data.get('highlander') else None,
            causation=CausationDigest.from_dict(data['causation']) if data.get('causation') else None,
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
                        causation_explorer: Optional[Any] = None) -> OrganismCapsule:
        """
        Capture complete organism state into a capsule.
        
        Args:
            organism: The NeuralOrganism to capture
            reason: Why this capture is happening
            notes: Additional notes
            tags: Tags for categorization
            include_causation: Whether to include causation history
            causation_explorer: CausationExplorer for event history
            
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
        input_size = getattr(brain, 'input_dim', None) or getattr(brain, 'input_size', 10)
        output_size = getattr(brain, 'output_dim', None) or getattr(brain, 'output_size', 5)
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
        default_concepts = {
            'move', 'rest', 'eat', 'reproduce', 'attack', 'flee', 'explore',
            'cooperate', 'share', 'hoard', 'signal', 'hide', 'seek',
            'danger', 'safety', 'food', 'mate', 'threat', 'friend', 'enemy',
            'existence'
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
            
            for concept_id, atom_dict in capsule.language.atoms.items():
                atom = LinguisticAtom(
                    concept_id=concept_id,
                    strength=atom_dict.get('strength', 0.5),
                    source=atom_dict.get('source', 'restored'),
                    semantic_frame=atom_dict.get('semantic_frame', 'unknown'),
                    abstraction_level=atom_dict.get('abstraction_level', 0)
                )
                target_language_system.atoms[concept_id] = atom
                target_language_system._concept_order.append(concept_id)
            
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
