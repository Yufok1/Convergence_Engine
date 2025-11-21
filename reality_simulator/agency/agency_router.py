"""
🚦 AGENCY ROUTER

Coordinates between manual and AI decision-making modes.
Routes decisions based on context, user preference, and AI confidence.

Features:
- Automatic mode switching based on AI performance
- User preference override
- Decision quality monitoring
- Seamless fallback between modes
- Performance analytics across modes
"""

import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .manual_mode import ManualAgency
from .network_decision_agent import NetworkDecisionAgent
from .system_decision_makers import (
    SystemAgencyMode, SystemDecisionContext,
    ExplorerDecisionMaker, DjinnKernelDecisionMaker, RealitySimDecisionMaker,
    UnifiedConsensusDecisionMaker, BreathDrivenDecisionMaker, ChaosModeDecisionMaker
)

# Event Bus integration
try:
    import sys
    import os
    kernel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kernel')
    if kernel_path not in sys.path:
        sys.path.insert(0, kernel_path)
    from event_driven_coordination import (
        DjinnEventBus, DjinnEvent, EventType
    )
    from decision_events import create_decision_event
    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False
    DjinnEventBus = None
    DjinnEvent = None
    EventType = None
    create_decision_event = None


class AgencyMode(Enum):
    """Decision-making modes - REPURPOSED FOR SYSTEM-DRIVEN DECISIONS"""
    # Legacy modes (kept for compatibility)
    MANUAL_ONLY = "manual_only"      # Human makes all decisions (fallback)
    AI_ASSISTED = "ai_assisted"      # AI suggests (deprecated - agents removed)
    AI_AUTONOMOUS = "ai_autonomous"  # AI makes decisions (deprecated - agents removed)
    HYBRID = "hybrid"               # Mix of manual and AI (deprecated)
    
    # NEW: System-driven modes
    EXPLORER_DRIVEN = "explorer_driven"          # Explorer makes decision (VP-based)
    DJINN_KERNEL_DRIVEN = "djinn_kernel_driven"  # Djinn Kernel makes decision (trait-based)
    REALITY_SIM_DRIVEN = "reality_sim_driven"    # Reality Sim makes decision (network-based)
    UNIFIED_CONSENSUS = "unified_consensus"       # All three systems vote
    BREATH_DRIVEN = "breath_driven"              # Breath engine decides (rhythm-based)
    CHAOS_MODE = "chaos_mode"                    # Random/exploratory decisions


@dataclass
class DecisionRouting:
    """
    Routing configuration for different decision types
    """
    decision_type: str
    preferred_mode: AgencyMode
    ai_confidence_threshold: float = 0.6
    allow_override: bool = True
    batch_capable: bool = False

    def should_use_ai(self, ai_performance: float) -> bool:
        """Determine if AI should be used for this decision type"""
        if self.preferred_mode == AgencyMode.MANUAL_ONLY:
            return False
        elif self.preferred_mode == AgencyMode.AI_AUTONOMOUS:
            return True
        elif self.preferred_mode == AgencyMode.AI_ASSISTED:
            return ai_performance >= self.ai_confidence_threshold
        else:  # HYBRID
            return ai_performance >= 0.5  # Lower threshold for hybrid


@dataclass
class AgencyPerformance:
    """
    Performance metrics for agency system
    """
    total_decisions: int = 0
    manual_decisions: int = 0
    ai_decisions: int = 0
    deferred_decisions: int = 0
    accuracy_vs_manual: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction: float = 0.0  # Based on override frequency

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "total_decisions": self.total_decisions,
            "ai_adoption_rate": self.ai_decisions / max(1, self.total_decisions),
            "deferred_rate": self.deferred_decisions / max(1, self.total_decisions),
            "manual_rate": self.manual_decisions / max(1, self.total_decisions),
            "avg_response_time": self.avg_response_time,
            "user_satisfaction": self.user_satisfaction
        }


class AgencyRouter:
    """
    Routes decisions between manual and AI modes
    """

    def __init__(self,
                 manual_agency: ManualAgency,
                 ai_agent: Optional[NetworkDecisionAgent] = None,
                 initial_mode: AgencyMode = AgencyMode.MANUAL_ONLY,
                 # NEW: System integration
                 explorer_controller=None,
                 utm_kernel=None,
                 vp_monitor=None,
                 network=None,
                 breath_engine=None,
                 # NEW: Event Bus integration
                 event_bus=None):
        self.manual_agency = manual_agency
        self.ai_agent = ai_agent  # Always None - agents removed
        self.current_mode = AgencyMode.MANUAL_ONLY  # Default to manual (fallback)

        # NEW: Event Bus integration
        if event_bus is None and EVENT_BUS_AVAILABLE:
            # Try to get event bus from UTM Kernel if available
            if utm_kernel and hasattr(utm_kernel, 'event_bus'):
                self.event_bus = utm_kernel.event_bus
            else:
                # Create new event bus if none provided
                self.event_bus = DjinnEventBus()
                # Start async processing
                if hasattr(self.event_bus.event_processor, 'start_processing'):
                    self.event_bus.event_processor.start_processing()
        elif event_bus:
            self.event_bus = event_bus
        else:
            self.event_bus = None

        # NEW: System decision makers
        self.explorer_maker = ExplorerDecisionMaker(explorer_controller) if explorer_controller else None
        self.djinn_maker = DjinnKernelDecisionMaker(utm_kernel, vp_monitor) if (utm_kernel or vp_monitor) else None
        self.reality_maker = RealitySimDecisionMaker(network) if network else None
        self.breath_maker = BreathDrivenDecisionMaker(breath_engine) if breath_engine else None
        self.chaos_maker = ChaosModeDecisionMaker()
        
        # Unified consensus maker (if all three available)
        if self.explorer_maker and self.djinn_maker and self.reality_maker:
            self.unified_maker = UnifiedConsensusDecisionMaker(
                self.explorer_maker, self.djinn_maker, self.reality_maker
            )
        else:
            self.unified_maker = None

        # Decision routing configuration
        self.routing_config: Dict[str, DecisionRouting] = self._create_default_routing()

        # Performance tracking
        self.performance = AgencyPerformance()

        # Mode transition history
        self.mode_history: List[Tuple[float, AgencyMode, str]] = []

        # Override tracking
        self.pending_overrides: Dict[str, Any] = {}
        
        # System references (for context building)
        self.explorer_controller = explorer_controller
        self.utm_kernel = utm_kernel
        self.vp_monitor = vp_monitor
        self.network = network
        self.breath_engine = breath_engine

    def _create_default_routing(self) -> Dict[str, DecisionRouting]:
        """Create default routing configuration for different decision types"""
        return {
            "network_connection": DecisionRouting(
                decision_type="network_connection",
                preferred_mode=AgencyMode.UNIFIED_CONSENSUS,  # All systems vote
                ai_confidence_threshold=0.6,
                allow_override=True,
                batch_capable=True
            ),
            "evolution_mutation": DecisionRouting(
                decision_type="evolution_mutation",
                preferred_mode=AgencyMode.DJINN_KERNEL_DRIVEN,  # Lawful decisions
                ai_confidence_threshold=0.8,
                allow_override=False,
                batch_capable=False
            ),
            "resource_allocation": DecisionRouting(
                decision_type="resource_allocation",
                preferred_mode=AgencyMode.REALITY_SIM_DRIVEN,  # Network-aware
                ai_confidence_threshold=0.7,
                allow_override=True,
                batch_capable=True
            ),
            "organism_selection": DecisionRouting(
                decision_type="organism_selection",
                preferred_mode=AgencyMode.BREATH_DRIVEN,  # Rhythm-based
                ai_confidence_threshold=0.5,
                allow_override=True,
                batch_capable=True
            ),
            "phase_transition": DecisionRouting(
                decision_type="phase_transition",
                preferred_mode=AgencyMode.UNIFIED_CONSENSUS,  # All systems must agree
                ai_confidence_threshold=0.9,
                allow_override=False,
                batch_capable=False
            ),
            "trait_translation": DecisionRouting(
                decision_type="trait_translation",
                preferred_mode=AgencyMode.DJINN_KERNEL_DRIVEN,  # Trait-based
                ai_confidence_threshold=0.6,
                allow_override=True,
                batch_capable=True
            )
        }

    def make_decision(self, decision_type: str,
                     context: Dict[str, Any],
                     options: List[str],
                     force_mode: Optional[AgencyMode] = None) -> str:
        """
        Route decision to appropriate system-driven agency mode

        Args:
            decision_type: Type of decision
            context: Decision context (can be Dict or SystemDecisionContext)
            options: Available options
            force_mode: Override automatic routing

        Returns:
            Chosen option
        """
        start_time = time.time()
        routing = self.routing_config.get(decision_type)

        if not routing:
            # Default to unified consensus for unknown decision types
            routing = DecisionRouting(decision_type, AgencyMode.UNIFIED_CONSENSUS)

        # Determine which mode to use
        effective_mode = force_mode or routing.preferred_mode

        # Convert context to SystemDecisionContext if needed
        system_context = self._build_system_context(context, decision_type)

        # Route to appropriate system-driven decision maker
        result = self._route_to_system(effective_mode, decision_type, system_context, options, routing)

        response_time = time.time() - start_time

        # Update performance metrics
        self._update_performance_metrics(decision_type, result, response_time, routing)

        # NEW: Publish decision event to Event Bus
        self._publish_decision_event(decision_type, result, options, system_context, effective_mode, response_time)

        return result
    
    def _publish_decision_event(self, decision_type: str, decision: str, options: List[str],
                               context: SystemDecisionContext, routing_mode: AgencyMode, response_time: float):
        """Publish decision event to Event Bus"""
        if not self.event_bus or not EVENT_BUS_AVAILABLE:
            return
        
        try:
            from event_driven_coordination import AgencyDecisionEvent
            
            # Convert context to dict for event
            context_dict = {}
            if isinstance(context, SystemDecisionContext):
                context_dict = {
                    'explorer_vp': context.explorer_vp,
                    'explorer_phase': context.explorer_phase,
                    'djinn_kernel_vp': context.djinn_kernel_vp,
                    'djinn_kernel_vp_class': context.djinn_kernel_vp_class,
                    'organism_count': context.organism_count,
                    'modularity': context.modularity,
                    'clustering_coefficient': context.clustering_coefficient,
                    'compatibility_score': context.compatibility_score,
                    'breath_phase': context.breath_phase,
                    'breath_cycle': context.breath_cycle
                }
                # Add additional context if available
                if context.additional_context:
                    context_dict.update(context.additional_context)
            elif isinstance(context, dict):
                context_dict = context
            
            # Create and publish event
            decision_event = AgencyDecisionEvent(
                decision_type=decision_type,
                decision=decision,
                options=options,
                context=context_dict,
                routing_mode=routing_mode.value if isinstance(routing_mode, AgencyMode) else str(routing_mode),
                response_time=response_time,
                source_agent="agency_router"
            )
            
            self.event_bus.publish(decision_event)
        except Exception as e:
            # Don't fail if event publishing fails
            print(f"[Agency Router] Warning: Could not publish decision event: {e}")
    
    def _build_system_context(self, context: Any, decision_type: str) -> SystemDecisionContext:
        """Build SystemDecisionContext from various input formats"""
        if isinstance(context, SystemDecisionContext):
            return context
        
        # Convert Dict to SystemDecisionContext
        if isinstance(context, dict):
            return SystemDecisionContext(
                # Explorer state
                explorer_vp=context.get('explorer_vp', 0.0),
                explorer_phase=context.get('explorer_phase', 'genesis'),
                explorer_vp_calculations=context.get('explorer_vp_calculations', 0),
                breath_cycle=context.get('breath_cycle', 0),
                breath_phase=context.get('breath_phase', 'inhale'),
                breath_depth=context.get('breath_depth', 0.0),
                
                # Djinn Kernel state
                djinn_kernel_vp=context.get('djinn_kernel_vp', 0.0),
                djinn_kernel_vp_class=context.get('djinn_kernel_vp_class', 'VP0'),
                trait_convergence=context.get('trait_convergence', 0.0),
                tape_position=context.get('tape_position', 0),
                
                # Reality Simulator state
                organism_count=context.get('organism_count', 0),
                connection_count=context.get('connection_count', 0),
                modularity=context.get('modularity', 1.0),
                clustering_coefficient=context.get('clustering_coefficient', 0.0),
                average_path_length=context.get('average_path_length', 0.0),
                network_stability=context.get('network_stability', 0.0),
                
                # Decision-specific
                org_a_id=context.get('org_a_id'),
                org_b_id=context.get('org_b_id'),
                org_a_fitness=context.get('org_a_fitness', 0.0),
                org_b_fitness=context.get('org_b_fitness', 0.0),
                org_a_connections=context.get('org_a_connections', 0),
                org_b_connections=context.get('org_b_connections', 0),
                compatibility_score=context.get('compatibility_score', 0.0),
                distance=context.get('distance', 0.0),
                
                # Additional context
                additional_context=context
            )
        
        # Fallback: Try to get state from system references
        return self._build_context_from_systems(decision_type)
    
    def _build_context_from_systems(self, decision_type: str) -> SystemDecisionContext:
        """Build context by querying actual systems"""
        context = SystemDecisionContext()
        
        # Get Explorer state
        if self.explorer_controller:
            try:
                state = self.explorer_controller.get_state()
                context.explorer_phase = state.get('phase', 'genesis')
                if hasattr(self.explorer_controller, 'sentinel'):
                    vp_history = self.explorer_controller.sentinel.vp_history if hasattr(self.explorer_controller.sentinel, 'vp_history') else []
                    context.explorer_vp_calculations = len(vp_history)
                    if vp_history:
                        context.explorer_vp = vp_history[-1].get('vp', 0.0) if isinstance(vp_history[-1], dict) else 0.0
            except (AttributeError, KeyError, IndexError) as e:
                # Explorer controller may not have sentinel or vp_history may be empty
                # Silently use default values (0.0) for context
                pass
        
        # Get Breath Engine state
        if self.breath_engine:
            try:
                breath_state = self.breath_engine.get_breath_state()
                context.breath_cycle = breath_state.get('cycle_count', 0)
                context.breath_depth = breath_state.get('depth', 0.0)
                context.breath_phase = 'inhale' if breath_state.get('phase', 0) < 3.14159 else 'exhale'
            except (AttributeError, KeyError, TypeError) as e:
                # Breath engine may not have get_breath_state method or may return unexpected format
                # Silently use default values
                pass
        
        # Get Djinn Kernel state
        if self.vp_monitor:
            try:
                vp_history = self.vp_monitor.vp_history if hasattr(self.vp_monitor, 'vp_history') else []
                if vp_history:
                    recent = vp_history[-1]
                    context.djinn_kernel_vp = recent.get('total_vp', 0.0) if isinstance(recent, dict) else 0.0
                    context.djinn_kernel_vp_class = self.vp_monitor._classify_violation_pressure(context.djinn_kernel_vp).value
            except (AttributeError, KeyError, IndexError, ValueError) as e:
                # VP monitor may not have vp_history or classification may fail
                # Silently use default values
                pass
        
        if self.utm_kernel:
            try:
                ledger = self.utm_kernel.akashic_ledger
                context.tape_position = ledger.next_position
            except (AttributeError, TypeError) as e:
                # UTM kernel may not have akashic_ledger or ledger may not have next_position
                # Silently use default value
                pass
        
        # Get Reality Simulator state
        if self.network:
            try:
                context.organism_count = len(self.network.organisms)
                context.connection_count = len(self.network.network_graph.edges())
                if hasattr(self.network, 'metrics'):
                    context.modularity = self.network.metrics.modularity if hasattr(self.network.metrics, 'modularity') else 1.0
                    context.clustering_coefficient = self.network.metrics.clustering_coefficient if hasattr(self.network.metrics, 'clustering_coefficient') else 0.0
                    context.average_path_length = self.network.metrics.average_path_length if hasattr(self.network.metrics, 'average_path_length') else 0.0
                    context.network_stability = self.network.metrics.ecosystem_stability if hasattr(self.network.metrics, 'ecosystem_stability') else 0.0
            except (AttributeError, KeyError, TypeError) as e:
                # Network may not have expected attributes or metrics may be incomplete
                # Silently use default values
                pass
        
        return context
    
    def _route_to_system(self, mode: AgencyMode, decision_type: str,
                        context: SystemDecisionContext, options: List[str],
                        routing: DecisionRouting) -> str:
        """Route to system-driven decision maker"""
        
        # System-driven modes
        if mode == AgencyMode.EXPLORER_DRIVEN:
            if self.explorer_maker:
                result = self.explorer_maker.make_decision(decision_type, context, options)
                if result:
                    return result
        elif mode == AgencyMode.DJINN_KERNEL_DRIVEN:
            if self.djinn_maker:
                result = self.djinn_maker.make_decision(decision_type, context, options)
                if result:
                    return result
        elif mode == AgencyMode.REALITY_SIM_DRIVEN:
            if self.reality_maker:
                result = self.reality_maker.make_decision(decision_type, context, options)
                if result:
                    return result
        elif mode == AgencyMode.UNIFIED_CONSENSUS:
            if self.unified_maker:
                result = self.unified_maker.make_decision(decision_type, context, options)
                if result:
                    return result
        elif mode == AgencyMode.BREATH_DRIVEN:
            if self.breath_maker:
                result = self.breath_maker.make_decision(decision_type, context, options)
                if result:
                    return result
        elif mode == AgencyMode.CHAOS_MODE:
            result = self.chaos_maker.make_decision(decision_type, context, options)
            if result:
                return result
        
        # Fallback to automated decision (non-interactive) instead of manual
        # Use chaos mode as safe fallback (random but deterministic)
        import random
        if options:
            return random.choice(options)
        return "default_automated_decision"

    def _route_to_manual(self, decision_type: str, context: Dict[str, Any],
                        options: List[str], routing: DecisionRouting) -> str:
        """Route to manual agency"""
        batch_mode = routing.batch_capable and len(options) > 2

        result = self.manual_agency.make_decision(
            decision_type, context, options, batch_mode=batch_mode
        )

        if result == "queued":
            # Handle batch processing
            batch_results = self.manual_agency.process_batch_decisions()
            result = batch_results[0] if batch_results else options[0]

        self.performance.manual_decisions += 1
        return result

    def _route_to_ai(self, decision_type: str, context: Dict[str, Any],
                    options: List[str], routing: DecisionRouting) -> str:
        """Route to AI agent - disabled, always use manual"""
        return self._route_to_manual(decision_type, context, options, routing)

    def _route_to_assisted(self, decision_type: str, context: Dict[str, Any],
                          options: List[str], routing: DecisionRouting) -> str:
        """AI-assisted mode - disabled, always use manual"""
        return self._route_to_manual(decision_type, context, options, routing)

    def _route_to_hybrid(self, decision_type: str, context: Dict[str, Any],
                        options: List[str], routing: DecisionRouting) -> str:
        """Hybrid mode - disabled, always use manual"""
        return self._route_to_manual(decision_type, context, options, routing)

    def _handle_override(self, decision_type: str, context: Dict[str, Any],
                        options: List[str]) -> str:
        """Handle user override for AI decision"""
        print(f"\n⚠️  AI deferred decision: {decision_type}")
        print("AI was uncertain, please decide:")

        override_decision = self.manual_agency.make_decision(
            f"{decision_type}_override", context, options
        )

        return override_decision

    def _update_performance_metrics(self, decision_type: str, result: str,
                                  response_time: float, routing: DecisionRouting):
        """Update performance tracking"""
        self.performance.total_decisions += 1
        self.performance.avg_response_time = (
            self.performance.avg_response_time * (self.performance.total_decisions - 1) +
            response_time
        ) / self.performance.total_decisions
    
    def _publish_decision_event(self, decision_type: str, chosen_option: str,
                               options: List[str], context: 'SystemDecisionContext',
                               mode: AgencyMode, response_time: float):
        """
        Publish decision event to Event Bus.
        
        This enables asynchronous notification of all decision outcomes,
        creating a clean separation between decision-making and notification.
        """
        if not self.event_bus or not EVENT_BUS_AVAILABLE or not create_decision_event:
            return
        
        try:
            # Convert response time to milliseconds
            response_time_ms = response_time * 1000
            
            # Build context snapshot for event
            context_snapshot = {
                "explorer_vp": context.explorer_vp,
                "explorer_phase": context.explorer_phase,
                "breath_cycle": context.breath_cycle,
                "breath_phase": context.breath_phase,
                "djinn_kernel_vp": context.djinn_kernel_vp,
                "djinn_kernel_vp_class": context.djinn_kernel_vp_class,
                "organism_count": context.organism_count,
                "connection_count": context.connection_count,
                "modularity": context.modularity,
                "network_stability": context.network_stability
            }
            
            # Build event-specific kwargs
            event_kwargs = {
                "source_agent": "agency_router"
            }
            
            # Add network-specific details for network decisions
            if decision_type in ["network_connection", "resource_allocation", "organism_selection"]:
                event_kwargs["org_a_id"] = context.org_a_id
                event_kwargs["org_b_id"] = context.org_b_id
                event_kwargs["network_metrics"] = {
                    "modularity": context.modularity,
                    "clustering_coefficient": context.clustering_coefficient,
                    "average_path_length": context.average_path_length,
                    "network_stability": context.network_stability
                }
                event_kwargs["connection_details"] = {
                    "org_a_fitness": context.org_a_fitness,
                    "org_b_fitness": context.org_b_fitness,
                    "org_a_connections": context.org_a_connections,
                    "org_b_connections": context.org_b_connections,
                    "compatibility_score": context.compatibility_score,
                    "distance": context.distance
                }
            
            # Add evolution-specific details for evolution decisions
            elif decision_type in ["evolution_mutation", "trait_translation"]:
                event_kwargs["organism_id"] = context.org_a_id  # Reuse org_a_id for organism
                event_kwargs["mutation_type"] = decision_type
                event_kwargs["trait_changes"] = context.additional_context.get("trait_changes", {}) if context.additional_context else {}
                event_kwargs["fitness_before"] = context.org_a_fitness
                event_kwargs["fitness_after"] = context.additional_context.get("fitness_after", 0.0) if context.additional_context else 0.0
            
            # Add phase transition details
            elif decision_type == "phase_transition":
                event_kwargs["current_phase"] = context.explorer_phase
                event_kwargs["target_phase"] = chosen_option
                event_kwargs["transition_criteria"] = context.additional_context.get("transition_criteria", {}) if context.additional_context else {}
                event_kwargs["system_state"] = context_snapshot
            
            # Create and publish event
            event = create_decision_event(
                decision_type=decision_type,
                chosen_option=chosen_option,
                available_options=options,
                decision_mode=mode.value,
                context=context_snapshot,
                response_time_ms=response_time_ms,
                **event_kwargs
            )
            
            self.event_bus.publish(event)
            
        except Exception as e:
            # Don't let event publishing errors break decision-making
            print(f"[AgencyRouter] Warning: Failed to publish decision event: {e}")

    def switch_mode(self, new_mode: AgencyMode, reason: str = ""):
        """Switch agency mode"""
        old_mode = self.current_mode
        self.current_mode = new_mode

        self.mode_history.append((time.time(), new_mode, reason))

        print(f"🚦 Agency mode switched: {old_mode.value} → {new_mode.value}")
        if reason:
            print(f"Reason: {reason}")

    def adaptive_mode_switching(self):
        """Automatically switch modes based on performance"""
        # AI agents removed - no performance tracking
        ai_performance = 0.0
        deferred_rate = 0.0

        # Switch logic disabled - always manual only (agents removed)

    def get_status(self) -> Dict[str, Any]:
        """Get current agency status"""
        return {
            "current_mode": self.current_mode.value,
            "manual_agency_stats": self.manual_agency.get_decision_stats(),
            "ai_agent_stats": {},
            "performance_summary": self.performance.get_summary(),
            "routing_config": {k: v.preferred_mode.value for k, v in self.routing_config.items()},
            "mode_history": [(t, m.value, r) for t, m, r in self.mode_history[-5:]]  # Last 5
        }

    def process_deferred_decisions(self):
        """Process deferred decisions - disabled, no agents"""
        pass

    def export_decision_data(self) -> Tuple[str, str]:
        """Export decision data from manual agency only"""
        manual_path = self.manual_agency.export_training_data()
        return manual_path, ""


# Utility functions
def create_agency_router(manual_log_dir: str = "data/decision_logs",
                        ai_model: str = "none",
                        initial_mode: AgencyMode = AgencyMode.MANUAL_ONLY,
                        # NEW: System integration parameters
                        explorer_controller=None,
                        utm_kernel=None,
                        vp_monitor=None,
                        network=None,
                        breath_engine=None,
                        # NEW: Event Bus integration
                        event_bus=None) -> AgencyRouter:
    """Create a complete agency router system with system-driven decision makers"""
    from .manual_mode import create_manual_agency

    manual_agency = create_manual_agency(manual_log_dir)
    # ai_agent removed - agents completely removed

    return AgencyRouter(
        manual_agency, 
        ai_agent=None, 
        initial_mode=initial_mode,
        # NEW: System integration
        explorer_controller=explorer_controller,
        utm_kernel=utm_kernel,
        vp_monitor=vp_monitor,
        network=network,
        breath_engine=breath_engine,
        # NEW: Event Bus integration
        event_bus=event_bus
    )


def get_agency_recommendation(performance_data: Dict[str, Any]) -> AgencyMode:
    """
    Recommend agency mode based on performance data
    """
    ai_confidence = performance_data.get("ai_confidence", 0.0)
    deferred_rate = performance_data.get("deferred_rate", 1.0)
    total_decisions = performance_data.get("total_decisions", 0)

    if total_decisions < 10:
        return AgencyMode.MANUAL_ONLY  # Not enough data

    if ai_confidence > 0.8 and deferred_rate < 0.1:
        return AgencyMode.AI_AUTONOMOUS
    elif ai_confidence > 0.6 and deferred_rate < 0.3:
        return AgencyMode.AI_ASSISTED
    else:
        return AgencyMode.MANUAL_ONLY


# Module-level docstring
"""
🚦 AGENCY ROUTER

The traffic cop of human-AI decision making:

- Routes decisions based on type, confidence, and user preference
- Automatic mode switching when AI performance changes
- Seamless fallback between manual and AI modes
- Performance monitoring across all decision pathways
- Override handling for critical decisions

Manual mode creates training data for AI improvement.
"""

