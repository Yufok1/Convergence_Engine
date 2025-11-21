"""
🎯 SYSTEM DECISION MAKERS

Granular, system-driven decision making for the unified system.

Instead of human input, decisions are made based on:
- Explorer state (VP, phase, breath)
- Djinn Kernel state (VP, traits, UTM)
- Reality Simulator state (network metrics, organisms)
- Strategy presets (conservative, balanced, innovative, chaos)
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SystemAgencyMode(Enum):
    """Decision-making modes based on system state"""
    EXPLORER_DRIVEN = "explorer_driven"          # Explorer makes decision (VP-based)
    DJINN_KERNEL_DRIVEN = "djinn_kernel_driven"  # Djinn Kernel makes decision (trait-based)
    REALITY_SIM_DRIVEN = "reality_sim_driven"    # Reality Sim makes decision (network-based)
    UNIFIED_CONSENSUS = "unified_consensus"       # All three systems vote
    BREATH_DRIVEN = "breath_driven"              # Breath engine decides (rhythm-based)
    CHAOS_MODE = "chaos_mode"                    # Random/exploratory decisions


@dataclass
class SystemDecisionContext:
    """Context for system-driven decisions"""
    # Explorer state
    explorer_vp: float = 0.0
    explorer_phase: str = "genesis"
    explorer_vp_calculations: int = 0
    breath_cycle: int = 0
    breath_phase: str = "inhale"  # inhale or exhale
    breath_depth: float = 0.0
    
    # Djinn Kernel state
    djinn_kernel_vp: float = 0.0
    djinn_kernel_vp_class: str = "VP0"
    trait_convergence: float = 0.0
    tape_position: int = 0
    
    # Reality Simulator state
    organism_count: int = 0
    connection_count: int = 0
    modularity: float = 1.0
    clustering_coefficient: float = 0.0
    average_path_length: float = 0.0
    network_stability: float = 0.0
    
    # Decision-specific context
    org_a_id: Optional[str] = None
    org_b_id: Optional[str] = None
    org_a_fitness: float = 0.0
    org_b_fitness: float = 0.0
    org_a_connections: int = 0
    org_b_connections: int = 0
    compatibility_score: float = 0.0
    distance: float = 0.0  # Network distance
    
    # Additional context
    additional_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}


class ExplorerDecisionMaker:
    """Makes decisions based on Explorer state"""
    
    def __init__(self, explorer_controller=None):
        self.explorer = explorer_controller
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext, 
                     options: List[str]) -> str:
        """Make decision based on Explorer state"""
        
        if decision_type == "network_connection":
            return self._decide_connection_explorer(context, options)
        elif decision_type == "resource_allocation":
            return self._decide_resource_allocation_explorer(context, options)
        elif decision_type == "organism_selection":
            return self._decide_organism_selection_explorer(context, options)
        else:
            # Default: Use Explorer's VP to weight options
            return self._weighted_decision(context, options, weight_key='explorer_vp')
    
    def _decide_connection_explorer(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Explorer-driven connection decision"""
        # Explorer in Genesis phase: More exploratory
        if context.explorer_phase == "genesis":
            # High VP = more exploration needed
            if context.explorer_vp > 0.5:
                # High VP, need exploration: Connect more
                if "connect_immediate" in options:
                    return "connect_immediate"
                elif "connect" in options:
                    return "connect"
            else:
                # Low VP, stable: Be selective
                if context.compatibility_score > 0.6:
                    return "connect_immediate" if "connect_immediate" in options else "connect"
                else:
                    return "reject" if "reject" in options else options[0]
        else:
            # Sovereign phase: More precise
            if context.compatibility_score > 0.8:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "reject" if "reject" in options else options[0]
    
    def _decide_resource_allocation_explorer(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Explorer-driven resource allocation"""
        # Use VP to determine allocation strategy
        if context.explorer_vp < 0.3:
            # Low VP: Balanced allocation
            return "equal" if "equal" in options else options[0]
        elif context.explorer_vp > 0.7:
            # High VP: Focus on fittest
            return "fitness_based" if "fitness_based" in options else options[0]
        else:
            # Medium VP: Connection-based
            return "connection_based" if "connection_based" in options else options[0]
    
    def _decide_organism_selection_explorer(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Explorer-driven organism selection"""
        # Breath phase influences selection
        if context.breath_phase == "inhale":
            # Inhale: Gather (select less connected)
            return "least_connected" if "least_connected" in options else options[0]
        else:
            # Exhale: Release (select most connected)
            return "most_connected" if "most_connected" in options else options[0]
    
    def _weighted_decision(self, context: SystemDecisionContext, options: List[str], 
                          weight_key: str = 'explorer_vp') -> str:
        """Make weighted decision based on context"""
        weight = getattr(context, weight_key, 0.5)
        # Higher weight = more exploratory options
        if weight > 0.7:
            # Prefer exploratory options
            for opt in ["connect_immediate", "random", "innovative"]:
                if opt in options:
                    return opt
        elif weight < 0.3:
            # Prefer conservative options
            for opt in ["reject", "defer", "conservative"]:
                if opt in options:
                    return opt
        # Default: balanced
        return options[len(options) // 2] if options else options[0]


class DjinnKernelDecisionMaker:
    """Makes decisions based on Djinn Kernel state"""
    
    def __init__(self, utm_kernel=None, vp_monitor=None):
        self.utm_kernel = utm_kernel
        self.vp_monitor = vp_monitor
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext,
                     options: List[str]) -> str:
        """Make decision based on Djinn Kernel state"""
        
        if decision_type == "network_connection":
            return self._decide_connection_djinn(context, options)
        elif decision_type == "trait_translation":
            return self._decide_trait_translation(context, options)
        elif decision_type == "phase_transition":
            return self._decide_phase_transition(context, options)
        else:
            return self._lawful_decision(context, options)
    
    def _decide_connection_djinn(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Djinn Kernel-driven connection decision"""
        # VP0 (fully lawful): Very precise
        if context.djinn_kernel_vp_class == "VP0":
            # Only connect if highly compatible
            if context.compatibility_score > 0.85:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "reject" if "reject" in options else options[0]
        # VP1-VP2: Moderate precision
        elif context.djinn_kernel_vp < 0.5:
            if context.compatibility_score > 0.7:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "reject" if "reject" in options else options[0]
        # VP3+: High divergence, more exploratory
        else:
            if context.compatibility_score > 0.5:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "connect_delayed" if "connect_delayed" in options else options[0]
    
    def _decide_trait_translation(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Djinn Kernel-driven trait translation"""
        # Use trait convergence to determine translation method
        if context.trait_convergence > 0.8:
            # High convergence: Direct translation
            return "direct" if "direct" in options else options[0]
        elif context.trait_convergence > 0.5:
            # Medium convergence: Normalized
            return "normalized" if "normalized" in options else options[0]
        else:
            # Low convergence: Weighted
            return "weighted" if "weighted" in options else options[0]
    
    def _decide_phase_transition(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Djinn Kernel-driven phase transition"""
        # VP0 = ready for precision
        if context.djinn_kernel_vp_class == "VP0":
            return "now" if "now" in options else options[0]
        elif context.djinn_kernel_vp < 0.3:
            return "accelerate" if "accelerate" in options else options[0]
        else:
            return "wait" if "wait" in options else options[0]
    
    def _lawful_decision(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Make lawful decision based on VP"""
        # Lower VP = more lawful = more precise
        if context.djinn_kernel_vp < 0.25:
            # Most lawful: First option (usually most conservative)
            return options[0]
        elif context.djinn_kernel_vp < 0.5:
            # Lawful: Middle option
            return options[len(options) // 2] if len(options) > 1 else options[0]
        else:
            # Less lawful: More exploratory
            return options[-1] if len(options) > 1 else options[0]


class RealitySimDecisionMaker:
    """Makes decisions based on Reality Simulator state"""
    
    def __init__(self, network=None):
        self.network = network
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext,
                     options: List[str]) -> str:
        """Make decision based on Reality Simulator state"""
        
        if decision_type == "network_connection":
            return self._decide_connection_reality_sim(context, options)
        elif decision_type == "resource_allocation":
            return self._decide_resource_allocation_reality_sim(context, options)
        elif decision_type == "organism_selection":
            return self._decide_organism_selection_reality_sim(context, options)
        else:
            return self._network_aware_decision(context, options)
    
    def _decide_connection_reality_sim(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Reality Sim-driven connection decision"""
        # Pre-collapse: More connections needed
        if context.organism_count < 500:
            # Growing phase: Connect if compatible
            if context.compatibility_score > 0.4:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "connect_delayed" if "connect_delayed" in options else options[0]
        # Post-collapse: Selective connections
        else:
            # Collapsed: Only high-quality connections
            if context.compatibility_score > 0.7 and context.distance < 2.0:
                return "connect_immediate" if "connect_immediate" in options else "connect"
            else:
                return "reject" if "reject" in options else options[0]
    
    def _decide_resource_allocation_reality_sim(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Reality Sim-driven resource allocation"""
        # Use network topology
        if context.modularity < 0.3:
            # Unified network: Equal allocation
            return "equal" if "equal" in options else options[0]
        elif context.clustering_coefficient > 0.5:
            # High clustering: Connection-based
            return "connection_based" if "connection_based" in options else options[0]
        else:
            # Balanced: Fitness-based
            return "fitness_based" if "fitness_based" in options else options[0]
    
    def _decide_organism_selection_reality_sim(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Reality Sim-driven organism selection"""
        # Use network metrics
        if context.average_path_length < 3.0:
            # Short paths: Select most connected (hubs)
            return "most_connected" if "most_connected" in options else options[0]
        else:
            # Long paths: Select least connected (explore)
            return "least_connected" if "least_connected" in options else options[0]
    
    def _network_aware_decision(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Make network-aware decision"""
        # Use network stability
        if context.network_stability > 0.7:
            # Stable: Conservative
            return options[0]
        elif context.network_stability < 0.3:
            # Unstable: Exploratory
            return options[-1] if len(options) > 1 else options[0]
        else:
            # Balanced
            return options[len(options) // 2] if len(options) > 1 else options[0]


class UnifiedConsensusDecisionMaker:
    """Makes decisions based on consensus of all three systems"""
    
    def __init__(self, explorer_maker, djinn_maker, reality_maker):
        self.explorer_maker = explorer_maker
        self.djinn_maker = djinn_maker
        self.reality_maker = reality_maker
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext,
                     options: List[str]) -> str:
        """Make decision based on consensus"""
        # Get votes from all three systems
        explorer_vote = self.explorer_maker.make_decision(decision_type, context, options)
        djinn_vote = self.djinn_maker.make_decision(decision_type, context, options)
        reality_vote = self.reality_maker.make_decision(decision_type, context, options)
        
        # Count votes
        votes = [explorer_vote, djinn_vote, reality_vote]
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # Return majority vote, or first if tie
        if vote_counts:
            majority_vote = max(vote_counts.items(), key=lambda x: x[1])[0]
            return majority_vote
        
        return options[0] if options else ""


class BreathDrivenDecisionMaker:
    """Makes decisions based on breath engine state"""
    
    def __init__(self, breath_engine=None):
        self.breath_engine = breath_engine
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext,
                     options: List[str]) -> str:
        """Make decision based on breath phase"""
        # Inhale: Gather, explore, connect
        if context.breath_phase == "inhale":
            if decision_type == "network_connection":
                return "connect_immediate" if "connect_immediate" in options else "connect"
            elif decision_type == "resource_allocation":
                return "equal" if "equal" in options else options[0]
            else:
                # Inhale: First option (gathering)
                return options[0]
        # Exhale: Release, consolidate, refine
        else:
            if decision_type == "network_connection":
                return "reject" if "reject" in options else options[-1]
            elif decision_type == "resource_allocation":
                return "fitness_based" if "fitness_based" in options else options[-1]
            else:
                # Exhale: Last option (releasing)
                return options[-1] if len(options) > 1 else options[0]


class ChaosModeDecisionMaker:
    """Makes random/exploratory decisions"""
    
    def make_decision(self, decision_type: str, context: SystemDecisionContext,
                     options: List[str]) -> str:
        """Make random decision"""
        if not options:
            return ""
        return np.random.choice(options)


# Strategy presets (repurposed from manual agency)
class SystemStrategyPreset:
    """System-driven strategy preset"""
    
    def __init__(self, name: str, description: str, rules: Dict[str, Any]):
        self.name = name
        self.description = description
        self.rules = rules
    
    def apply(self, context: SystemDecisionContext, options: List[str]) -> str:
        """Apply strategy to context"""
        risk_tolerance = self.rules.get('risk_tolerance', 0.5)
        innovation_factor = self.rules.get('innovation_factor', 0.5)
        random_factor = self.rules.get('random_factor', 0.0)
        
        # Random strategy
        if random_factor > 0.5:
            return np.random.choice(options) if options else ""
        
        # Risk-based strategy
        if risk_tolerance < 0.3:
            # Conservative: First option (safest)
            return options[0]
        elif risk_tolerance > 0.7:
            # Innovative: Last option (most exploratory)
            return options[-1] if len(options) > 1 else options[0]
        else:
            # Balanced: Middle option
            return options[len(options) // 2] if len(options) > 1 else options[0]


# Default strategy presets
DEFAULT_STRATEGY_PRESETS = {
    'conservative': SystemStrategyPreset(
        name='conservative',
        description='Prefer safe, established options. Avoid risk.',
        rules={'risk_tolerance': 0.2, 'innovation_factor': 0.1}
    ),
    'balanced': SystemStrategyPreset(
        name='balanced',
        description='Balance risk and reward. Moderate approach.',
        rules={'risk_tolerance': 0.5, 'innovation_factor': 0.5}
    ),
    'innovative': SystemStrategyPreset(
        name='innovative',
        description='Embrace novelty and risk. Favor new possibilities.',
        rules={'risk_tolerance': 0.8, 'innovation_factor': 0.9}
    ),
    'chaos': SystemStrategyPreset(
        name='chaos',
        description='Maximum unpredictability. Random decisions.',
        rules={'random_factor': 1.0}
    )
}

