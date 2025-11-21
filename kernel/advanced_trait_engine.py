"""
Advanced Trait Engine v2.0 - Phase 2.1 Implementation

This module implements the advanced trait processing capabilities that operate
within the Lawfold architecture, providing dynamic stability envelopes,
adaptive mutation rates, and comprehensive prosocial governance metrics.

Key Features:
- Dynamic Stability Envelopes: Adapt based on system state and VP levels
- Adaptive Mutation Rates: Adjust based on system health and convergence pressure
- Prosocial Governance Metrics: Full love measurement integration
- Advanced Convergence Operations: Multi-dimensional trait synthesis
- Real-time Stability Monitoring: Continuous VP and health assessment
"""

import time
import math
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime

from core_trait_framework import CoreTraitFramework, TraitDefinition, StabilityEnvelope, TraitCategory
from violation_pressure_calculation import ViolationMonitor
from trait_convergence_engine import TraitConvergenceEngine, ConvergenceMethod
from event_driven_coordination import DjinnEventBus, EventType


class MutationStrategy(Enum):
    """Strategies for adaptive mutation in trait evolution"""
    CONSERVATIVE = "conservative"      # Low mutation, high stability
    BALANCED = "balanced"             # Moderate mutation, balanced approach
    EXPLORATORY = "exploratory"       # High mutation, exploration focus
    RADICAL = "radical"               # Maximum mutation, radical change


class StabilityMode(Enum):
    """Modes for dynamic stability envelope operation"""
    STRICT = "strict"                 # Tight stability bounds
    NORMAL = "normal"                 # Standard stability bounds
    FLEXIBLE = "flexible"             # Relaxed stability bounds
    ADAPTIVE = "adaptive"             # Context-aware bounds


@dataclass
class DynamicStabilityEnvelope:
    """Dynamic stability envelope that adapts based on system state"""
    base_center: float = 0.5
    base_radius: float = 0.25
    base_compression: float = 1.0
    
    # Dynamic adjustment parameters
    vp_sensitivity: float = 0.3       # How much VP affects stability
    health_sensitivity: float = 0.2   # How much system health affects stability
    time_decay: float = 0.95          # Stability decay over time
    
    # Current dynamic state
    current_center: float = 0.5
    current_radius: float = 0.25
    current_compression: float = 1.0
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    def update_stability(self, violation_pressure: float, system_health: float, 
                        time_factor: float = 1.0) -> None:
        """Update stability envelope based on current system state"""
        
        # Calculate VP-based adjustments
        vp_adjustment = violation_pressure * self.vp_sensitivity
        center_vp_shift = vp_adjustment * 0.1  # VP pushes center slightly
        radius_vp_expansion = vp_adjustment * 0.2  # VP expands radius
        
        # Calculate health-based adjustments
        health_adjustment = (1.0 - system_health) * self.health_sensitivity
        compression_health_factor = 1.0 + health_adjustment  # Poor health increases compression
        
        # Apply time decay
        time_factor = time_factor * self.time_decay
        
        # Update current values
        self.current_center = max(0.0, min(1.0, 
            self.base_center + center_vp_shift))
        self.current_radius = max(0.1, min(0.5, 
            self.base_radius + radius_vp_expansion))
        self.current_compression = max(0.5, min(2.0, 
            self.base_compression * compression_health_factor * time_factor))
        
        self.last_update = datetime.utcnow()
    
    def get_current_envelope(self) -> StabilityEnvelope:
        """Get current stability envelope for VP calculations"""
        return StabilityEnvelope(
            center=self.current_center,
            radius=self.current_radius,
            compression_factor=self.current_compression
        )


@dataclass
class AdaptiveMutationRate:
    """Adaptive mutation rate that adjusts based on system conditions"""
    base_rate: float = 0.1
    min_rate: float = 0.01
    max_rate: float = 0.5
    
    # Adaptation factors
    vp_factor: float = 0.3            # VP influence on mutation
    health_factor: float = 0.2        # System health influence
    convergence_factor: float = 0.2   # Convergence success influence
    time_factor: float = 0.1          # Time-based adaptation
    
    # Current state
    current_rate: float = 0.1
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_mutation_rate(self, violation_pressure: float, 
                               system_health: float, convergence_success: float,
                               time_elapsed: float = 1.0) -> float:
        """Calculate adaptive mutation rate based on system conditions"""
        
        # VP-based adaptation (higher VP = higher mutation for exploration)
        vp_adaptation = violation_pressure * self.vp_factor
        
        # Health-based adaptation (poor health = higher mutation for recovery)
        health_adaptation = (1.0 - system_health) * self.health_factor
        
        # Convergence-based adaptation (poor convergence = higher mutation)
        convergence_adaptation = (1.0 - convergence_success) * self.convergence_factor
        
        # Time-based adaptation (gradual increase over time)
        time_adaptation = min(0.1, time_elapsed * self.time_factor)
        
        # Combine all factors
        total_adaptation = (vp_adaptation + health_adaptation + 
                           convergence_adaptation + time_adaptation)
        
        # Calculate new rate
        new_rate = self.base_rate + total_adaptation
        
        # Clamp to valid range
        self.current_rate = max(self.min_rate, min(self.max_rate, new_rate))
        self.last_update = datetime.utcnow()
        
        return self.current_rate


@dataclass
class ProsocialGovernanceMetrics:
    """Comprehensive prosocial governance metrics for love measurement"""
    
    # Love vector components (from love_measurement_spec.md)
    intimacy: float = 0.0
    commitment: float = 0.0
    caregiving: float = 0.0
    attunement: float = 0.0
    lineage_preference: float = 0.0
    
    # Default weights (auditable, modifiable via governance)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "intimacy": 0.25,
        "commitment": 0.20,
        "caregiving": 0.30,
        "attunement": 0.15,
        "lineage_preference": 0.10
    })
    
    # Calculated metrics
    love_score: float = 0.0
    governance_priority: float = 0.0
    protection_level: float = 0.0
    
    def calculate_love_score(self) -> float:
        """Calculate scalar love score from vector components"""
        score = sum(self.weights[component] * getattr(self, component) 
                   for component in self.weights.keys())
        self.love_score = max(0.0, min(1.0, score))
        return self.love_score
    
    def calculate_governance_priority(self, violation_pressure: float) -> float:
        """Calculate governance priority based on love score and VP"""
        # High love score increases governance priority
        # High VP amplifies the priority
        base_priority = self.love_score * 0.7
        vp_amplification = violation_pressure * 0.3
        self.governance_priority = min(1.0, base_priority + vp_amplification)
        return self.governance_priority
    
    def calculate_protection_level(self) -> float:
        """Calculate protection level based on love metrics"""
        # Caregiving and lineage preference heavily influence protection
        protection_factors = [
            self.caregiving * 0.4,
            self.lineage_preference * 0.3,
            self.commitment * 0.2,
            self.intimacy * 0.1
        ]
        self.protection_level = min(1.0, sum(protection_factors))
        return self.protection_level
    
    def update_from_traits(self, trait_values: Dict[str, float]) -> None:
        """Update metrics from trait values"""
        # Map trait values to love vector components
        love_components = {
            "intimacy": trait_values.get("intimacy", 0.0),
            "commitment": trait_values.get("commitment", 0.0),
            "caregiving": trait_values.get("caregiving", 0.0),
            "attunement": trait_values.get("attunement", 0.0),
            "lineagepreference": trait_values.get("lineagepreference", 0.0)
        }
        
        # Update component values
        for component, value in love_components.items():
            if hasattr(self, component):
                setattr(self, component, value)
        
        # Recalculate metrics
        self.calculate_love_score()
        self.calculate_protection_level()


class AdvancedTraitEngine:
    """
    Advanced trait engine implementing dynamic stability, adaptive mutation,
    and comprehensive prosocial governance metrics.
    """
    
    def __init__(self, core_framework: CoreTraitFramework, 
                 event_bus: Optional[DjinnEventBus] = None):
        """Initialize the advanced trait engine"""
        self.core_framework = core_framework
        self.event_bus = event_bus or DjinnEventBus()
        
        # Core components
        self.violation_monitor = ViolationMonitor(self.event_bus)
        self.convergence_engine = TraitConvergenceEngine(
            self.violation_monitor, self.event_bus
        )
        
        # Advanced components
        self.dynamic_envelopes: Dict[str, DynamicStabilityEnvelope] = {}
        self.mutation_rates: Dict[str, AdaptiveMutationRate] = {}
        self.prosocial_metrics: Dict[str, ProsocialGovernanceMetrics] = {}
        
        # System state tracking
        self.system_health = 1.0
        self.global_violation_pressure = 0.0
        self.convergence_success_rate = 0.8
        self.last_health_update = datetime.utcnow()
        
        # Initialize dynamic components for all traits
        self._initialize_dynamic_components()
    
    def _initialize_dynamic_components(self) -> None:
        """Initialize dynamic components for all registered traits"""
        for trait_name, trait_def in self.core_framework.trait_registry.items():
            # Create dynamic stability envelope
            self.dynamic_envelopes[trait_name] = DynamicStabilityEnvelope(
                base_center=trait_def.stability_envelope.center,
                base_radius=trait_def.stability_envelope.radius,
                base_compression=trait_def.stability_envelope.compression_factor
            )
            
            # Create adaptive mutation rate
            self.mutation_rates[trait_name] = AdaptiveMutationRate(
                base_rate=0.1,
                min_rate=0.01,
                max_rate=0.5
            )
            
            # Create prosocial metrics for prosocial traits
            if trait_def.category == TraitCategory.PROSOCIAL:
                self.prosocial_metrics[trait_name] = ProsocialGovernanceMetrics()
    
    def update_system_state(self, violation_pressure: float, 
                           convergence_success: float) -> None:
        """Update global system state for dynamic adaptations"""
        self.global_violation_pressure = violation_pressure
        self.convergence_success_rate = convergence_success
        
        # Update system health (inverse relationship with VP)
        self.system_health = max(0.0, min(1.0, 1.0 - violation_pressure * 0.8))
        
        # Update all dynamic components
        self._update_dynamic_components()
        
        self.last_health_update = datetime.utcnow()
    
    def _update_dynamic_components(self) -> None:
        """Update all dynamic stability envelopes and mutation rates"""
        time_factor = 1.0  # Could be calculated from last update
        
        for trait_name in self.core_framework.trait_registry:
            # Update dynamic stability envelope
            if trait_name in self.dynamic_envelopes:
                envelope = self.dynamic_envelopes[trait_name]
                envelope.update_stability(
                    self.global_violation_pressure,
                    self.system_health,
                    time_factor
                )
            
            # Update adaptive mutation rate
            if trait_name in self.mutation_rates:
                mutation_rate = self.mutation_rates[trait_name]
                mutation_rate.calculate_mutation_rate(
                    self.global_violation_pressure,
                    self.system_health,
                    self.convergence_success_rate,
                    time_factor
                )
    
    def calculate_dynamic_violation_pressure(self, trait_values: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """Calculate violation pressure using dynamic stability envelopes"""
        total_vp = 0.0
        trait_vp_breakdown = {}
        
        for trait_name, trait_value in trait_values.items():
            if trait_name in self.dynamic_envelopes:
                # Use dynamic envelope for VP calculation
                dynamic_envelope = self.dynamic_envelopes[trait_name].get_current_envelope()
                
                # Calculate VP using dynamic envelope
                deviation = abs(trait_value - dynamic_envelope.center)
                normalized_radius = dynamic_envelope.radius * dynamic_envelope.compression_factor
                trait_vp = min(1.0, deviation / normalized_radius) if normalized_radius > 0 else 1.0
                
                trait_vp_breakdown[trait_name] = trait_vp
                total_vp += trait_vp
        
        # Normalize total VP
        if trait_values:
            total_vp = min(1.0, total_vp / len(trait_values))
        
        return total_vp, trait_vp_breakdown
    
    def converge_traits_with_adaptation(self, parent_traits: List[Dict[str, float]], 
                                      convergence_method: ConvergenceMethod = ConvergenceMethod.WEIGHTED_AVERAGE) -> Dict[str, float]:
        """Converge traits using adaptive mutation rates and dynamic stability"""
        
        if len(parent_traits) < 2:
            raise ValueError("Need at least 2 parent trait sets for convergence")
        
        # Get current mutation rates for all traits
        mutation_rates = {}
        for trait_name in self.core_framework.trait_registry:
            if trait_name in self.mutation_rates:
                mutation_rates[trait_name] = self.mutation_rates[trait_name].current_rate
        
        # Perform convergence with the first two parents
        parent1_traits = parent_traits[0]
        parent2_traits = parent_traits[1]
        
        convergence_result = self.convergence_engine.converge_traits(
            parent1_traits, parent2_traits, convergence_method
        )
        
        # Extract child traits from result
        child_traits = convergence_result.child_traits
        
        # Apply adaptive mutations
        mutated_traits = {}
        for trait_name, trait_value in child_traits.items():
            if trait_name in mutation_rates:
                mutation_rate = mutation_rates[trait_name]
                mutation = (random.random() - 0.5) * mutation_rate * 2.0
                mutated_value = max(0.0, min(1.0, trait_value + mutation))
                mutated_traits[trait_name] = mutated_value
            else:
                mutated_traits[trait_name] = trait_value
        
        return mutated_traits
    
    def calculate_prosocial_governance(self, trait_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate comprehensive prosocial governance metrics"""
        governance_metrics = {}
        
        # Calculate love score and related metrics
        love_metrics = ProsocialGovernanceMetrics()
        love_metrics.update_from_traits(trait_values)
        
        governance_metrics["love_score"] = love_metrics.love_score
        governance_metrics["governance_priority"] = love_metrics.calculate_governance_priority(
            self.global_violation_pressure
        )
        governance_metrics["protection_level"] = love_metrics.protection_level
        
        # Calculate VP with prosocial considerations
        total_vp, vp_breakdown = self.calculate_dynamic_violation_pressure(trait_values)
        
        # Adjust VP based on love score (higher love = lower effective VP)
        love_vp_modifier = 1.0 - (love_metrics.love_score * 0.3)
        adjusted_vp = total_vp * love_vp_modifier
        
        governance_metrics["violation_pressure"] = adjusted_vp
        governance_metrics["vp_breakdown"] = vp_breakdown
        
        return governance_metrics
    
    def get_trait_evolution_strategy(self, trait_name: str) -> MutationStrategy:
        """Determine evolution strategy for a trait based on current conditions"""
        if trait_name not in self.mutation_rates:
            return MutationStrategy.BALANCED
        
        mutation_rate = self.mutation_rates[trait_name].current_rate
        
        if mutation_rate < 0.05:
            return MutationStrategy.CONSERVATIVE
        elif mutation_rate < 0.15:
            return MutationStrategy.BALANCED
        elif mutation_rate < 0.3:
            return MutationStrategy.EXPLORATORY
        else:
            return MutationStrategy.RADICAL
    
    def get_stability_mode(self, trait_name: str) -> StabilityMode:
        """Determine stability mode for a trait based on current conditions"""
        if trait_name not in self.dynamic_envelopes:
            return StabilityMode.NORMAL
        
        envelope = self.dynamic_envelopes[trait_name]
        compression_ratio = envelope.current_compression / envelope.base_compression
        
        if compression_ratio > 1.5:
            return StabilityMode.STRICT
        elif compression_ratio > 1.2:
            return StabilityMode.NORMAL
        elif compression_ratio > 0.8:
            return StabilityMode.FLEXIBLE
        else:
            return StabilityMode.ADAPTIVE
    
    def export_engine_state(self) -> Dict[str, Any]:
        """Export complete engine state for monitoring and debugging"""
        return {
            "system_health": self.system_health,
            "global_violation_pressure": self.global_violation_pressure,
            "convergence_success_rate": self.convergence_success_rate,
            "last_health_update": self.last_health_update.isoformat() + "Z",
            "dynamic_envelopes": {
                name: {
                    "current_center": env.current_center,
                    "current_radius": env.current_radius,
                    "current_compression": env.current_compression,
                    "last_update": env.last_update.isoformat() + "Z"
                } for name, env in self.dynamic_envelopes.items()
            },
            "mutation_rates": {
                name: {
                    "current_rate": rate.current_rate,
                    "last_update": rate.last_update.isoformat() + "Z"
                } for name, rate in self.mutation_rates.items()
            },
            "prosocial_metrics_count": len(self.prosocial_metrics)
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize core framework
    core_framework = CoreTraitFramework()
    
    # Initialize advanced trait engine
    engine = AdvancedTraitEngine(core_framework)
    
    # Test trait values
    test_traits = {
        "intimacy": 0.7,
        "commitment": 0.8,
        "caregiving": 0.6,
        "joy": 0.5,
        "trust": 0.9
    }
    
    # Update system state
    engine.update_system_state(violation_pressure=0.3, convergence_success=0.7)
    
    # Calculate dynamic VP
    total_vp, vp_breakdown = engine.calculate_dynamic_violation_pressure(test_traits)
    print(f"Dynamic VP: {total_vp:.3f}")
    print(f"VP Breakdown: {vp_breakdown}")
    
    # Calculate prosocial governance
    governance = engine.calculate_prosocial_governance(test_traits)
    print(f"Love Score: {governance['love_score']:.3f}")
    print(f"Governance Priority: {governance['governance_priority']:.3f}")
    print(f"Protection Level: {governance['protection_level']:.3f}")
    
    # Export engine state
    state = engine.export_engine_state()
    print(f"System Health: {state['system_health']:.3f}")
    print(f"Convergence Success Rate: {state['convergence_success_rate']:.3f}")
    
    print("Advanced Trait Engine operational!")
