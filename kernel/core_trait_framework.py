# Core Mathematical Trait Framework
# Version 1.0 - Foundation for Djinn Kernel Trait Ontology

"""
Core trait framework implementing mathematical requirements from the Djinn Kernel specification.
All traits must be mathematically consistent for UUID anchoring, VP calculation, and convergence.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid
import json
import hashlib
from datetime import datetime


class TraitCategory(Enum):
    """Foundational trait categories for ontological organization"""
    MATHEMATICAL = "mathematical"  # Meta-traits that enable measurement
    PROSOCIAL = "prosocial"        # Love metrics and social bonding
    PHYSICAL = "physical"          # Embodied characteristics
    COGNITIVE = "cognitive"        # Mental/intellectual traits
    BEHAVIORAL = "behavioral"      # Action patterns and tendencies
    EMERGENT = "emergent"         # Discovered through system operation


@dataclass
class StabilityEnvelope:
    """
    Mathematical envelope defining trait stability boundaries.
    Core component of violation pressure calculation.
    """
    center: float = 0.5           # Stability center [0.0, 1.0]
    radius: float = 0.25          # Allowable deviation range
    compression_factor: float = 1.0  # Stability enforcement strength
    
    def __post_init__(self):
        # Ensure mathematical consistency
        assert 0.0 <= self.center <= 1.0, "Stability center must be [0.0, 1.0]"
        assert 0.0 < self.radius <= 0.5, "Radius must be (0.0, 0.5]"
        assert self.compression_factor > 0.0, "Compression factor must be positive"


@dataclass
class TraitDefinition:
    """
    Core trait definition implementing mathematical requirements for UUID anchoring.
    Every trait must conform to these mathematical properties.
    """
    name: str                                    # Canonical trait identifier
    category: TraitCategory                      # Ontological classification
    stability_envelope: StabilityEnvelope       # VP calculation parameters
    description: str = ""                       # Human-readable description
    measurement_unit: str = "normalized"        # Always [0.0, 1.0] for consistency
    dependencies: List[str] = field(default_factory=list)  # Trait interaction modeling
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extensible properties
    
    def __post_init__(self):
        # Canonical name requirements for UUID determinism
        assert self.name.isidentifier(), "Trait name must be valid Python identifier"
        assert self.name.islower(), "Trait name must be lowercase for canonicalization"
        assert "_" not in self.name or self.name.count("_") <= 2, "Minimize underscores for clarity"


class CoreTraitFramework:
    """
    Mathematical foundation for all trait operations in the Djinn Kernel.
    Implements requirements for UUID anchoring, VP calculation, and trait convergence.
    """
    
    # Mathematical meta-traits that enable measurement
    MATHEMATICAL_META_TRAITS = {
        "violationpressure": TraitDefinition(
            name="violationpressure",
            category=TraitCategory.MATHEMATICAL,
            stability_envelope=StabilityEnvelope(center=0.0, radius=0.25, compression_factor=2.0),
            description="Quantified instability driving recursive operations",
            dependencies=[]
        ),
        "completionpressure": TraitDefinition(
            name="completionpressure", 
            category=TraitCategory.MATHEMATICAL,
            stability_envelope=StabilityEnvelope(center=0.0, radius=0.3, compression_factor=1.5),
            description="Identity incompleteness measure driving UUID anchoring",
            dependencies=[]
        ),
        "convergencestability": TraitDefinition(
            name="convergencestability",
            category=TraitCategory.MATHEMATICAL, 
            stability_envelope=StabilityEnvelope(center=0.8, radius=0.15, compression_factor=1.2),
            description="Trait convergence success probability",
            dependencies=["violationpressure"]
        ),
        "reflectionindex": TraitDefinition(
            name="reflectionindex",
            category=TraitCategory.MATHEMATICAL,
            stability_envelope=StabilityEnvelope(center=0.7, radius=0.2, compression_factor=1.0),
            description="Global civilization health metric",
            dependencies=["violationpressure", "convergencestability"]
        )
    }
    
    # Prosocial traits from love metrics specification
    PROSOCIAL_TRAITS = {
        "intimacy": TraitDefinition(
            name="intimacy",
            category=TraitCategory.PROSOCIAL,
            stability_envelope=StabilityEnvelope(center=0.6, radius=0.3, compression_factor=0.8),
            description="Frequency and depth of mutual interactions",
            dependencies=[]
        ),
        "commitment": TraitDefinition(
            name="commitment",
            category=TraitCategory.PROSOCIAL,
            stability_envelope=StabilityEnvelope(center=0.7, radius=0.25, compression_factor=1.1),
            description="Persistence of caring over time",
            dependencies=["intimacy"]
        ),
        "caregiving": TraitDefinition(
            name="caregiving", 
            category=TraitCategory.PROSOCIAL,
            stability_envelope=StabilityEnvelope(center=0.65, radius=0.3, compression_factor=0.9),
            description="Resource allocation patterns to others",
            dependencies=[]
        ),
        "attunement": TraitDefinition(
            name="attunement",
            category=TraitCategory.PROSOCIAL,
            stability_envelope=StabilityEnvelope(center=0.6, radius=0.25, compression_factor=1.0),
            description="Response accuracy to partner states",
            dependencies=["intimacy"]
        ),
        "lineagepreference": TraitDefinition(
            name="lineagepreference",
            category=TraitCategory.PROSOCIAL,
            stability_envelope=StabilityEnvelope(center=0.55, radius=0.35, compression_factor=0.7),
            description="Behavioral bias toward offspring",
            dependencies=["caregiving"]
        )
    }
    
    # Emotional traits from emotional vector engine
    EMOTIONAL_TRAITS = {
        "joy": TraitDefinition(
            name="joy",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.7, radius=0.25, compression_factor=1.2),
            description="Resonance, novelty, convergence, and harmony emotional state",
            dependencies=["convergencestability"],
            metadata={"vp_modifiers": {"stability_tolerance": 1.2, "mutation_acceptance": 1.5}}
        ),
        "grief": TraitDefinition(
            name="grief",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.3, radius=0.3, compression_factor=1.4),
            description="Loss, rupture, lineage discontinuity, and memory emotional state",
            dependencies=["violationpressure"],
            metadata={"vp_modifiers": {"stability_requirement": 1.4, "change_resistance": 1.3}}
        ),
        "trust": TraitDefinition(
            name="trust",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.8, radius=0.2, compression_factor=0.8),
            description="Predictive fidelity, shared recursion, reliability, and consistency",
            dependencies=["convergencestability"],
            metadata={"vp_modifiers": {"arbitration_sensitivity": 0.8, "synchrony_tolerance": 1.3}}
        ),
        "fear": TraitDefinition(
            name="fear",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.2, radius=0.25, compression_factor=1.6),
            description="VP spike anticipation, risk aversion, threat detection, and uncertainty",
            dependencies=["violationpressure"],
            metadata={"vp_modifiers": {"threat_amplification": 1.6, "stability_urgency": 1.5}}
        ),
        "anger": TraitDefinition(
            name="anger",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.4, radius=0.3, compression_factor=2.0),
            description="Trait violation, boundary breach, injustice, and frustration",
            dependencies=["violationpressure"],
            metadata={"vp_modifiers": {"violation_urgency": 2.0, "justice_demand": 1.8}}
        ),
        "curiosity": TraitDefinition(
            name="curiosity",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.6, radius=0.3, compression_factor=1.4),
            description="Divergence hunger, novelty seeking, exploration, and understanding",
            dependencies=[],
            metadata={"vp_modifiers": {"exploration_tolerance": 1.4, "novelty_acceptance": 1.6}}
        ),
        "shame": TraitDefinition(
            name="shame",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.3, radius=0.25, compression_factor=1.5),
            description="Self VP reflection, trait misalignment, social disapproval, and inadequacy",
            dependencies=["violationpressure"],
            metadata={"vp_modifiers": {"self_criticism": 1.5, "conformity_pressure": 1.3}}
        ),
        "pride": TraitDefinition(
            name="pride",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.8, radius=0.2, compression_factor=0.8),
            description="Convergence success, lineage honor, achievement, and superiority",
            dependencies=["convergencestability"],
            metadata={"vp_modifiers": {"achievement_satisfaction": 0.8, "status_maintenance": 1.2}}
        ),
        "envy": TraitDefinition(
            name="envy",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.4, radius=0.3, compression_factor=1.6),
            description="Comparative VP imbalance, resource disparity, status inequality, and desire",
            dependencies=["violationpressure"],
            metadata={"vp_modifiers": {"inequality_sensitivity": 1.6, "redistribution_urgency": 1.4}}
        ),
        "compassion": TraitDefinition(
            name="compassion",
            category=TraitCategory.BEHAVIORAL,
            stability_envelope=StabilityEnvelope(center=0.7, radius=0.25, compression_factor=1.5),
            description="Caregiving impulse, VP empathy, suffering recognition, and protection",
            dependencies=["caregiving"],
            metadata={"vp_modifiers": {"protection_priority": 1.5, "mercy_factor": 1.3}}
        )
    }
    
    def __init__(self):
        """Initialize core trait framework with foundational traits"""
        self.trait_registry: Dict[str, TraitDefinition] = {}
        self.trait_interaction_matrix: Dict[str, Dict[str, float]] = {}
        
        # Register foundational traits
        self._register_core_traits()
        
        # Initialize trait interaction modeling
        self._initialize_trait_interactions()
    
    def _register_core_traits(self):
        """Register mathematical meta-traits, prosocial traits, and emotional traits"""
        # Register mathematical foundation traits
        for name, trait_def in self.MATHEMATICAL_META_TRAITS.items():
            self.trait_registry[name] = trait_def
        
        # Register prosocial traits from love metrics
        for name, trait_def in self.PROSOCIAL_TRAITS.items():
            self.trait_registry[name] = trait_def
            
        # Register emotional traits from emotional vector engine
        for name, trait_def in self.EMOTIONAL_TRAITS.items():
            self.trait_registry[name] = trait_def
    
    def _initialize_trait_interactions(self):
        """Initialize trait interaction matrix for convergence modeling"""
        # Mathematical traits influence each other
        self.trait_interaction_matrix = {
            "violationpressure": {
                "convergencestability": -0.8,  # VP reduces convergence stability
                "reflectionindex": -0.9,       # VP reduces global health
            },
            "completionpressure": {
                "violationpressure": 0.6,      # Completion pressure increases VP
                "convergencestability": -0.4,   # Reduces stability during completion
            },
            "convergencestability": {
                "reflectionindex": 0.7,        # Stable convergence improves health
            },
            # Prosocial trait interactions
            "intimacy": {
                "commitment": 0.5,              # Intimacy supports commitment
                "attunement": 0.6,              # Intimacy improves attunement
            },
            "commitment": {
                "caregiving": 0.4,              # Commitment enhances caregiving
                "lineagepreference": 0.3,       # Commitment biases toward lineage
            },
            "caregiving": {
                "lineagepreference": 0.7,       # Caregiving strongly biases lineage
            },
            # Emotional trait interactions
            "joy": {
                "convergencestability": 0.6,    # Joy enhances convergence stability
                "trust": 0.4,                   # Joy builds trust
                "curiosity": 0.3,               # Joy encourages curiosity
            },
            "grief": {
                "violationpressure": 0.5,       # Grief increases VP
                "stability_requirement": 0.4,   # Grief demands stability
            },
            "trust": {
                "convergencestability": 0.5,    # Trust stabilizes convergence
                "cooperation_bonus": 0.6,       # Trust enables cooperation
            },
            "fear": {
                "violationpressure": 0.7,       # Fear significantly increases VP
                "risk_avoidance": 0.8,          # Fear drives risk avoidance
            },
            "anger": {
                "violationpressure": 0.8,       # Anger strongly increases VP
                "justice_demand": 0.7,          # Anger demands justice
            },
            "curiosity": {
                "exploration_tolerance": 0.6,   # Curiosity enables exploration
                "novelty_acceptance": 0.7,      # Curiosity accepts novelty
            },
            "shame": {
                "violationpressure": 0.6,       # Shame increases VP
                "self_correction": 0.5,         # Shame drives self-correction
            },
            "pride": {
                "convergencestability": 0.4,    # Pride stabilizes convergence
                "lineage_bias": 0.6,            # Pride biases toward lineage
            },
            "envy": {
                "violationpressure": 0.5,       # Envy increases VP
                "inequality_sensitivity": 0.7,  # Envy drives equality concerns
            },
            "compassion": {
                "caregiving": 0.8,              # Compassion strongly enhances caregiving
                "protection_priority": 0.6,     # Compassion prioritizes protection
            }
        }
    
    def get_trait_definition(self, trait_name: str) -> Optional[TraitDefinition]:
        """Get trait definition by canonical name"""
        return self.trait_registry.get(trait_name.lower())
    
    def register_trait(self, trait_def: TraitDefinition) -> bool:
        """
        Register new trait through formal amendment process.
        Must maintain mathematical consistency.
        """
        # Validate mathematical consistency
        if not self._validate_trait_definition(trait_def):
            return False
        
        # Check for naming conflicts
        if trait_def.name in self.trait_registry:
            return False
        
        # Validate dependencies exist
        for dep_name in trait_def.dependencies:
            if dep_name not in self.trait_registry:
                return False
        
        # Register trait
        self.trait_registry[trait_def.name] = trait_def
        
        # Initialize interaction matrix entry
        if trait_def.name not in self.trait_interaction_matrix:
            self.trait_interaction_matrix[trait_def.name] = {}
        
        return True
    
    def _validate_trait_definition(self, trait_def: TraitDefinition) -> bool:
        """Validate trait definition meets mathematical requirements"""
        try:
            # Test canonical serialization
            trait_dict = {
                "name": trait_def.name,
                "category": trait_def.category.value,
                "stability_center": trait_def.stability_envelope.center,
                "stability_radius": trait_def.stability_envelope.radius,
                "compression_factor": trait_def.stability_envelope.compression_factor,
                "dependencies": sorted(trait_def.dependencies),
                "metadata": trait_def.metadata
            }
            
            # Ensure deterministic serialization
            canonical_json = json.dumps(trait_dict, sort_keys=True, separators=(',', ':'))
            
            # Verify mathematical constraints
            assert 0.0 <= trait_def.stability_envelope.center <= 1.0
            assert 0.0 < trait_def.stability_envelope.radius <= 0.5
            assert trait_def.stability_envelope.compression_factor > 0.0
            
            return True
            
        except (AssertionError, ValueError, TypeError):
            return False
    
    def calculate_trait_violation_pressure(self, trait_name: str, current_value: float) -> float:
        """
        Calculate violation pressure for specific trait.
        Core formula: VP = |actual - center| / (radius * compression_factor)
        """
        trait_def = self.get_trait_definition(trait_name)
        if not trait_def:
            raise ValueError(f"Unknown trait: {trait_name}")
        
        envelope = trait_def.stability_envelope
        deviation = abs(current_value - envelope.center)
        normalized_radius = envelope.radius * envelope.compression_factor
        
        return min(1.0, deviation / normalized_radius)
    
    def get_trait_interaction_strength(self, source_trait: str, target_trait: str) -> float:
        """Get interaction strength between two traits"""
        interactions = self.trait_interaction_matrix.get(source_trait, {})
        return interactions.get(target_trait, 0.0)
    
    def create_trait_payload(self, trait_values: Dict[str, float]) -> Dict[str, Any]:
        """
        Create canonical trait payload for UUID anchoring.
        Ensures deterministic serialization and mathematical consistency.
        """
        # Validate all traits are registered
        for trait_name in trait_values:
            if trait_name not in self.trait_registry:
                raise ValueError(f"Unknown trait: {trait_name}")
        
        # Validate all values are [0.0, 1.0] normalized
        for trait_name, value in trait_values.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Trait {trait_name} value {value} not in [0.0, 1.0]")
        
        # Create canonical payload
        canonical_payload = {
            "traits": {name: value for name, value in sorted(trait_values.items())},
            "trait_framework_version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return canonical_payload
    
    def list_traits_by_category(self, category: TraitCategory) -> List[str]:
        """List all traits in a specific category"""
        return [name for name, trait_def in self.trait_registry.items() 
                if trait_def.category == category]
    
    def export_trait_ontology(self) -> Dict[str, Any]:
        """Export complete trait ontology for system inspection"""
        return {
            "framework_version": "1.0",
            "total_traits": len(self.trait_registry),
            "categories": {cat.value: self.list_traits_by_category(cat) 
                          for cat in TraitCategory},
            "trait_definitions": {name: {
                "category": trait_def.category.value,
                "stability_center": trait_def.stability_envelope.center,
                "stability_radius": trait_def.stability_envelope.radius,
                "compression_factor": trait_def.stability_envelope.compression_factor,
                "dependencies": trait_def.dependencies,
                "description": trait_def.description
            } for name, trait_def in self.trait_registry.items()},
            "interaction_matrix": self.trait_interaction_matrix
        }


# Example usage demonstrating mathematical consistency
if __name__ == "__main__":
    # Initialize core trait framework
    framework = CoreTraitFramework()
    
    # Create example trait payload
    trait_values = {
        "intimacy": 0.7,
        "commitment": 0.8,
        "caregiving": 0.6,
        "violationpressure": 0.2
    }
    
    # Create canonical payload for UUID anchoring
    payload = framework.create_trait_payload(trait_values)
    print("Canonical Trait Payload:")
    print(json.dumps(payload, indent=2, sort_keys=True))
    
    # Calculate violation pressures
    print("\nViolation Pressure Analysis:")
    for trait_name, value in trait_values.items():
        vp = framework.calculate_trait_violation_pressure(trait_name, value)
        print(f"{trait_name}: {value:.2f} -> VP: {vp:.3f}")
    
    # Show trait interaction modeling
    print("\nTrait Interaction Matrix:")
    interactions = framework.trait_interaction_matrix
    for source in sorted(interactions.keys()):
        targets = interactions[source]
        for target, strength in sorted(targets.items()):
            print(f"{source} -> {target}: {strength:+.2f}")
    
    # Export ontology
    ontology = framework.export_trait_ontology()
    print(f"\nOntology Summary:")
    print(f"Total traits: {ontology['total_traits']}")
    for category, traits in ontology['categories'].items():
        print(f"{category}: {len(traits)} traits")