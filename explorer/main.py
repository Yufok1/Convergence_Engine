

import time
import sys
import os
import json
import random
import uuid
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add explorer path to allow relative imports when called from outside
explorer_path = Path(__file__).parent
if str(explorer_path) not in sys.path:
    sys.path.insert(0, str(explorer_path))

from sentinel import Sentinel
from kernel import Kernel
from diagnostics import Diagnostics
from breath_engine import BreathEngine
from mirror_systems import MirrorOfInsight, MirrorOfPortent, BloomSystem
from dynamic_operations import DynamicOperations

# Add paths for Reality Simulator and Djinn Kernel
parent_path = Path(__file__).parent.parent
reality_sim_path = parent_path / 'reality_simulator'
kernel_path = parent_path / 'kernel'

if str(reality_sim_path) not in sys.path:
    sys.path.insert(0, str(reality_sim_path))
if str(kernel_path) not in sys.path:
    sys.path.insert(0, str(kernel_path))

# Import Reality Simulator and Djinn Kernel
try:
    from reality_simulator.main import RealitySimulator
    REALITY_SIM_AVAILABLE = True
except ImportError:
    REALITY_SIM_AVAILABLE = False
    print("[Explorer] Reality Simulator not available")

try:
    from utm_kernel_design import UTMKernel, AgentInstruction, TapeSymbol
    from violation_pressure_calculation import ViolationMonitor, StabilityEnvelope
    from event_driven_coordination import ViolationPressureEvent, EventType
    DJINN_KERNEL_AVAILABLE = True
except ImportError:
    DJINN_KERNEL_AVAILABLE = False
    print("[Explorer] Djinn Kernel not available")

# Import integration facilities
try:
    from trait_hub import TraitHub
    TRAIT_HUB_AVAILABLE = True
except ImportError:
    TRAIT_HUB_AVAILABLE = False
    print("[Explorer] Trait Hub not available")

try:
    from integration_bridge import ExplorerIntegrationBridge
    INTEGRATION_BRIDGE_AVAILABLE = True
except ImportError:
    INTEGRATION_BRIDGE_AVAILABLE = False
    print("[Explorer] Integration Bridge not available")

try:
    from unified_transition_manager import UnifiedTransitionManager
    TRANSITION_MANAGER_AVAILABLE = True
except ImportError:
    TRANSITION_MANAGER_AVAILABLE = False
    print("[Explorer] Unified Transition Manager not available")

try:
    import sys
    import os
    parent_path = Path(__file__).parent.parent
    phase_sync_path = parent_path / 'reality_simulator'
    if str(phase_sync_path) not in sys.path:
        sys.path.insert(0, str(phase_sync_path))
    from phase_sync_bridge import PhaseSynchronizationBridge
    PHASE_SYNC_BRIDGE_AVAILABLE = True
except ImportError:
    PHASE_SYNC_BRIDGE_AVAILABLE = False
    print("[Explorer] Phase Sync Bridge not available")

# ANSI color codes for Windows terminal

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    ORANGE = '\033[38;5;214m'  # Orange/Gold for math
    MAGENTA = '\033[95m'  # Magenta/Purple for transitions
    END = '\033[0m'

TRAIT_TRANSLATIONS = {
    'speed_ms': ('Speed (ms)', 'How fast did it run?'),
    'memory_mb': ('Memory (MB)', 'How much computer memory did it use?'),
    'reliability': ('Reliability', 'Did it finish successfully?'),
}

def explain_traits(traits):
    lines = []
    for k, v in traits.items():
        label, desc = TRAIT_TRANSLATIONS.get(k, (k, 'No description.'))
        lines.append(f"  {label}: {v} — {desc}")
    return '\n'.join(lines)

def math_print(text):
    print(f"{Colors.ORANGE}{text}{Colors.END}")

def color_print(text, color):
    print(f"{color}{text}{Colors.END}")

class BiphasicController:
    def improvement_triggers(self):
        triggers = []
        # Resource optimization
        triggers.append({
            'name': 'resource_optimization',
            'func_path': 'test_func1.py',
            'inputs': [1, 2, 3],
            'desc': 'Seeking more efficient primitive recursive function.'
        })
        # Parallelism
        triggers.append({
            'name': 'parallelism',
            'func_path': 'test_func2.py',
            'inputs': [4, 5, 6],
            'desc': 'Seeking parallelizable primitive recursive function.'
        })
        # Feature expansion
        triggers.append({
            'name': 'feature_expansion',
            'func_path': 'test_func3.py',
            'inputs': [7, 8, 9],
            'desc': 'Seeking new operational capability.'
        })
        # Load balancing/fault tolerance
        triggers.append({
            'name': 'load_balancing',
            'func_path': 'test_func4.py',
            'inputs': [10, 11, 12],
            'desc': 'Seeking redundant or alternative function.'
        })
        # Fixed-point/self-replication (Kleene)
        triggers.append({
            'name': 'fixed_point',
            'func_path': 'test_func5.py',
            'inputs': [13, 14, 15],
            'desc': 'Seeking self-referential primitive recursive function.'
        })
        return triggers
    def __init__(self, config_path: str = None):
        # Initialize systems
        # Store config path (can be passed from unified_entry.py)
        self._config_path = config_path or str(parent_path / 'config.json')
        self.kernel = Kernel()
        self.sentinel = Sentinel()
        self.diagnostics = Diagnostics()
        self.breath_engine = BreathEngine()
        self.mirror_of_insight = MirrorOfInsight()
        self.mirror_of_portent = MirrorOfPortent()
        self.bloom_system = BloomSystem()
        self.dynamic_operations = DynamicOperations()
        
        # Initialize Reality Simulator (if available)
        self.current_config = {}
        
        # Initialize optional components to None (may be set later if available)
        self.utm_kernel = None
        self.vp_monitor = None
        self.lawfold_orchestrator = None

        if REALITY_SIM_AVAILABLE:
            try:
                self.reality_sim = RealitySimulator(config_path=self._config_path)
                try:
                    with open(self._config_path, 'r') as cfg_file:
                        self.current_config = json.load(cfg_file)
                except Exception:
                    self.current_config = {}
                
                # Disable RealityRenderer visualizations when used in unified mode
                # UnifiedVisualization in unified_entry.py handles all visualization
                if 'rendering' in self.reality_sim.config:
                    self.reality_sim.config['rendering']['enable_visualizations'] = False
                    print("[Explorer] Disabled RealityRenderer visualizations (using UnifiedVisualization)")
                
                if self.reality_sim.initialize_simulation():
                    print("[Explorer] ✅ Reality Simulator initialized")
                else:
                    print("[Explorer] ⚠️  Reality Simulator failed to initialize")
                    self.reality_sim = None
            except Exception as e:
                print(f"[Explorer] ⚠️  Reality Simulator error: {e}")
                self.reality_sim = None
        else:
            self.reality_sim = None
        
        # Initialize Djinn Kernel (if available)
        if DJINN_KERNEL_AVAILABLE:
            try:
                self.utm_kernel = UTMKernel()
                
                # Load VP monitoring configuration from config
                vp_config = {}
                try:
                    import json
                    with open(self._config_path, 'r') as f:
                        config = json.load(f)
                        self.current_config = config
                        vp_config = config.get('vp_monitoring', {})
                except Exception as e:
                    print(f"[Explorer] ⚠️  Could not load VP config: {e}, using defaults")
                
                self._configure_violation_monitor(vp_config)
            except Exception as e:
                print(f"[Explorer] ⚠️  Djinn Kernel error: {e}")
                self.utm_kernel = None
                self.vp_monitor = None
        else:
            self.utm_kernel = None
            self.vp_monitor = None

        # Initialize Lawfold Field Architecture (if available)
        if DJINN_KERNEL_AVAILABLE and self.utm_kernel:
            try:
                from lawfold_field_architecture import LawfoldFieldOrchestrator
                self.lawfold_orchestrator = LawfoldFieldOrchestrator(self.utm_kernel)
                self.lawfold_orchestrator.activate_all_fields()
                print("[Explorer] ✅ Lawfold Field Architecture initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Lawfold Field Architecture error: {e}")
                self.lawfold_orchestrator = None
        else:
            self.lawfold_orchestrator = None

        # Connect systems for mathematical capability assessment
        self.sentinel.mirror_of_insight = self.mirror_of_insight
        self.sentinel.breath_engine = self.breath_engine
        self.sentinel.bloom_system = self.bloom_system
        self.sentinel.dynamic_operations = self.dynamic_operations
        
        # Initialize integration facilities
        # 1. Trait Hub - for trait translation
        if TRAIT_HUB_AVAILABLE:
            try:
                self.trait_hub = TraitHub()
                print("[Explorer] ✅ Trait Hub initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Trait Hub error: {e}")
                self.trait_hub = None
        else:
            self.trait_hub = None
        
        # 2. Integration Bridge - for unified coordination
        if INTEGRATION_BRIDGE_AVAILABLE:
            try:
                self.integration_bridge = ExplorerIntegrationBridge()
                print("[Explorer] ✅ Integration Bridge initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Integration Bridge error: {e}")
                self.integration_bridge = None
        else:
            self.integration_bridge = None
        
        # 3. Unified Transition Manager - for chaos→precision transitions
        if TRANSITION_MANAGER_AVAILABLE:
            try:
                self.transition_manager = UnifiedTransitionManager()
                # Wire in our systems
                if self.reality_sim:
                    self.transition_manager.reality_sim_connector = getattr(self.transition_manager, 'reality_sim_connector', None)
                if self.utm_kernel:
                    self.transition_manager.djinn_kernel_connector = getattr(self.transition_manager, 'djinn_kernel_connector', None)
                self.transition_manager.breath_engine = self.breath_engine
                self.transition_manager.sentinel = self.sentinel
                self.transition_manager.mirror_insight = self.mirror_of_insight
                print("[Explorer] ✅ Unified Transition Manager initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Unified Transition Manager error: {e}")
                import traceback
                traceback.print_exc()
                self.transition_manager = None
        else:
            self.transition_manager = None
        
        # 4. Phase Synchronization Bridge - for phase sync
        if PHASE_SYNC_BRIDGE_AVAILABLE:
            try:
                self.phase_sync_bridge = PhaseSynchronizationBridge(
                    collapse_threshold=500,
                    max_connections_per_organism=5
                )
                print("[Explorer] ✅ Phase Sync Bridge initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Phase Sync Bridge error: {e}")
                self.phase_sync_bridge = None
        else:
            self.phase_sync_bridge = None
        
        # Dynamic stability system that learns from performance
        self.performance_history = []
        self.stability_center = self._initialize_stability_center()
        self.stability_envelope = self._initialize_stability_envelope()
        
        # Load previous state or start fresh
        self.phase = self._load_previous_state()

        # Adaptive VP response configuration
        adaptive_cfg = self.current_config.get('vp_monitoring', {}).get('adaptive_response', {}) if isinstance(self.current_config, dict) else {}
        self.high_vp_threshold = float(adaptive_cfg.get('high_vp_threshold', 0.75))
        self.streak_threshold = int(adaptive_cfg.get('streak_threshold', 3))
        self.fallback_streak = int(adaptive_cfg.get('fallback_streak', self.streak_threshold + 2))
        self.envelope_widen_factor = float(adaptive_cfg.get('envelope_widen_factor', 1.2))
        self.vp_high_streak = 0
        self.last_adaptive_actions: List[str] = []

    def _initialize_stability_center(self):
        """Initialize stability center with realistic baseline values"""
        return {
            'speed_ms': 100.0,  # Realistic baseline: 100ms execution time
            'memory_mb': 50.0,  # Realistic baseline: 50MB memory usage
            'reliability': 1.0   # Perfect reliability
        }

    def _initialize_stability_envelope(self):
        """Initialize stability envelope with realistic ranges"""
        return {
            'speed_ms': (10.0, 1000.0),    # 10ms to 1 second
            'memory_mb': (1.0, 8000.0),    # 1MB to 8GB - increased for realistic ML workloads
            'reliability': (1.0, 1.0)      # Must be reliable
        }

    def _load_previous_state(self):
        """Load previous system state and determine starting phase"""
        previous_state = self.diagnostics.load_latest_state()
        
        if previous_state is None:
            print("[Controller] No previous state found, starting in Genesis Phase")
            return 'genesis'
        
        # Extract phase from previous state
        previous_phase = previous_state.get('phase', 'genesis')
        
        # Check if we should continue in Sovereign Phase
        if previous_phase == 'sovereign':
            print(f"[Controller] Resuming in Sovereign Phase from previous session")
            return 'sovereign'
        elif previous_phase == 'genesis':
            # Check if we have enough certified functions to transition
            kernel_ids = previous_state.get('kernel_sovereign_ids', [])
            if len(kernel_ids) > 0:
                print(f"[Controller] Previous Genesis Phase had {len(kernel_ids)} certified functions, checking mathematical capability...")
                # We'll let the system check mathematical capability in the first run
                return 'genesis'
            else:
                print("[Controller] Previous Genesis Phase had no certified functions, starting fresh")
                return 'genesis'
        else:
            print(f"[Controller] Unknown previous phase '{previous_phase}', starting in Genesis Phase")
            return 'genesis'

    def apply_runtime_config(self, new_config: Dict[str, Any]) -> List[str]:
        """Apply runtime configuration updates while the system is running."""
        applied_sections: List[str] = []
        if not isinstance(new_config, dict):
            return applied_sections

        self.current_config = new_config

        if getattr(self, 'reality_sim', None) and hasattr(self.reality_sim, 'apply_runtime_config'):
            try:
                applied_sections.extend(self.reality_sim.apply_runtime_config(new_config) or [])
            except Exception as reality_err:
                print(f"[Explorer] ⚠️  Reality Simulator config update failed: {reality_err}")

        vp_config = new_config.get('vp_monitoring')
        if vp_config is not None and self._configure_violation_monitor(vp_config):
            applied_sections.append('vp_monitoring')

        return applied_sections

    def _configure_violation_monitor(self, vp_config: Dict[str, Any]) -> bool:
        """(Re)configure ViolationMonitor based on config dictionary."""
        if not self.utm_kernel:
            return False
        try:
            vp_config = vp_config or {}
            self.vp_monitor = ViolationMonitor(
                event_publisher=self.utm_kernel.event_publisher,
                diagnostics_enabled=vp_config.get('diagnostics_enabled', False),
                stabilization_enabled=vp_config.get('stabilization_enabled', False),
                max_vp_jump=vp_config.get('stabilization', {}).get('max_jump', 0.1),
                smoothing_factor=vp_config.get('stabilization', {}).get('smoothing_factor', 0.3),
                component_decomposition_enabled=vp_config.get('component_decomposition_enabled', False),
                component_weights=vp_config.get('component_weights'),
                adaptive_thresholds_enabled=vp_config.get('adaptive_thresholds_enabled', False)
            )
            self.utm_kernel.violation_monitor = self.vp_monitor

            vp_features = []
            if vp_config.get('diagnostics_enabled'):
                vp_features.append("diagnostics")
            if vp_config.get('stabilization_enabled'):
                vp_features.append("stabilization")
            if vp_config.get('component_decomposition_enabled'):
                vp_features.append("component_decomposition")
            if vp_config.get('adaptive_thresholds_enabled'):
                vp_features.append("adaptive_thresholds")

            feature_str = f" [{', '.join(vp_features)}]" if vp_features else ""
            print(f"[Explorer] ✅ Djinn Kernel configuration applied{feature_str}")

            if self.vp_monitor and hasattr(self.vp_monitor, 'diagnostics'):
                diag_enabled = self.vp_monitor.diagnostics.enabled
                diag_file = str(getattr(self.vp_monitor.diagnostics, 'log_file', 'unknown'))
                print(f"[Explorer] [VP_MONITORING] Diagnostics enabled: {diag_enabled}, Log file: {diag_file}")
            if hasattr(self.utm_kernel, 'violation_monitor') and self.utm_kernel.violation_monitor is self.vp_monitor:
                print(f"[Explorer] [VP_MONITORING] ✅ UTM Kernel using configured ViolationMonitor with diagnostics")
            return True
        except Exception as err:
            print(f"[Explorer] ⚠️  Failed to configure ViolationMonitor: {err}")
            return False

    def _prepare_trait_diagnostics(self, traits: Dict[str, float], vp_breakdown: Optional[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        diagnostics: Dict[str, Dict[str, float]] = {}
        if not traits:
            return diagnostics
        for name, value in traits.items():
            envelope = self.vp_monitor.get_stability_envelope(name) if self.vp_monitor else None
            diagnostics[name] = {
                'value': value,
                'envelope_center': envelope.center if envelope else 0.5,
                'envelope_radius': envelope.radius if envelope else 0.25,
                'vp_contribution': (vp_breakdown or {}).get(name, 0.0)
            }
        return diagnostics

    def _log_trait_diagnostics(self, diagnostics: Dict[str, Dict[str, float]]) -> None:
        if not diagnostics:
            return
        color_print("[Adaptive VP] Trait diagnostics:", Colors.YELLOW)
        for trait, info in diagnostics.items():
            deviation = abs(info['value'] - info['envelope_center'])
            color_print(
                f"  {trait}: value={info['value']:.3f}, center={info['envelope_center']:.3f}, "
                f"radius={info['envelope_radius']:.3f}, deviation={deviation:.3f}, "
                f"vp_contribution={info['vp_contribution']:.3f}",
                Colors.YELLOW
            )

    def _handle_vp_feedback(self, vp_value: Optional[float], traits: Dict[str, float], vp_breakdown: Optional[Dict[str, float]]) -> None:
        if vp_value is None:
            return
        diagnostics = self._prepare_trait_diagnostics(traits, vp_breakdown)
        if vp_value > self.high_vp_threshold:
            self.vp_high_streak += 1
            if self.vp_high_streak == 1:
                self._log_trait_diagnostics(diagnostics)
        else:
            if self.vp_high_streak > 0:
                color_print(f"[Adaptive VP] Streak reset (vp={vp_value:.3f})", Colors.CYAN)
            self.vp_high_streak = 0
            self.last_adaptive_actions = []
            return

        if self.vp_high_streak >= self.streak_threshold:
            actions = self._trigger_adaptive_response(vp_value, diagnostics, traits)
            self.last_adaptive_actions = actions
            if self.vp_high_streak >= self.fallback_streak:
                self._fallback_mutation_reset()

    def _trigger_adaptive_response(self, vp_value: float, diagnostics: Dict[str, Dict[str, float]], traits: Dict[str, float]) -> List[str]:
        actions: List[str] = []
        vp_contributions = {name: info.get('vp_contribution', 0.0) for name, info in diagnostics.items()}
        dominant_trait = None
        if vp_contributions:
            dominant_trait = max(vp_contributions.items(), key=lambda item: item[1])[0]
        target_traits = [dominant_trait] if dominant_trait else list(diagnostics.keys())
        for trait_name in target_traits:
            if trait_name and self._widen_trait_envelope(trait_name):
                actions.append(f"widen_envelope:{trait_name}")
        for base_trait in ['organism_count', 'modularity', 'clustering_coefficient', 'average_path_length']:
            if base_trait not in target_traits and self._widen_trait_envelope(base_trait):
                actions.append(f"widen_envelope:{base_trait}")
        if self._queue_arbitration_instruction(traits, priority=min(1.0, vp_value)):
            actions.append("queue_arbitration")
        self._publish_adaptive_event(vp_value, diagnostics, actions)
        return actions

    def _widen_trait_envelope(self, trait_name: str) -> bool:
        if not self.vp_monitor:
            return False
        envelope = self.vp_monitor.get_stability_envelope(trait_name)
        if not envelope:
            return False
        # Clamp to max 0.5 to respect StabilityEnvelope constraint
        new_radius = min(0.5, envelope.radius * self.envelope_widen_factor)
        widened = StabilityEnvelope(
            center=envelope.center,
            radius=new_radius,
            compression_factor=envelope.compression_factor
        )
        self.vp_monitor.set_stability_envelope(trait_name, widened)
        color_print(f"[Adaptive VP] Widened envelope for {trait_name} → radius {new_radius:.3f}", Colors.ORANGE)
        return True

    def _fallback_mutation_reset(self) -> None:
        if not self.reality_sim:
            return
        color_print("[Adaptive VP] Fallback reset triggered - nudging mutation parameters", Colors.RED)
        try:
            self.reality_sim.config['evolution']['mutation_rate']['initial'] = max(0.002, self.reality_sim.config['evolution']['mutation_rate']['initial'] * 0.9)
        except Exception:
            pass
        self._queue_compute_instruction(
            {
                "type": "trait_convergence",
                "parameters": {"mode": "reset", "breath_cycle": self.breath_engine.get_breath_state().get('cycle_count', 0)}
            },
            priority=0.9
        )

    def _publish_adaptive_event(self, vp_value: float, diagnostics: Dict[str, Dict[str, float]], actions: List[str]) -> None:
        """Publish adaptive VP event to DjinnEventBus for system-wide coordination"""
        if not self.utm_kernel or not hasattr(self.utm_kernel, 'event_bus'):
            return

        try:
            # Extract VP breakdown from diagnostics
            breakdown = {
                trait_name: info.get('vp_contribution', 0.0)
                for trait_name, info in diagnostics.items()
            }

            # Determine classification based on VP value
            if vp_value >= 1.0:
                classification = "VP4"
            elif vp_value >= 0.75:
                classification = "VP3"
            elif vp_value >= 0.5:
                classification = "VP2"
            elif vp_value >= 0.25:
                classification = "VP1"
            else:
                classification = "VP0"

            # Create proper ViolationPressureEvent
            event = ViolationPressureEvent(
                total_vp=vp_value,
                breakdown=breakdown,
                classification=f"{classification}_adaptive",  # Mark as adaptive response
                source_agent="explorer_adaptive_vp",
                metadata={
                    "adaptive_actions": actions,
                    "streak_count": self.vp_high_streak
                }
            )

            # Publish to DjinnEventBus
            self.utm_kernel.event_bus.publish(event)

        except Exception as err:
            color_print(f"[Adaptive VP] Event publish failed: {err}", Colors.YELLOW)

    def _queue_arbitration_instruction(self, traits: Dict[str, float], priority: float = 0.5) -> bool:
        if not self.utm_kernel:
            return False
        parameters = {
            "type": "stability_arbitration",
            "parameters": {"traits": traits, "timestamp": time.time()}
        }
        return self._queue_utm_instruction("ARBITRATE", parameters, priority)

    def _queue_compute_instruction(self, parameters: Dict[str, Any], priority: float = 0.5) -> bool:
        if not self.utm_kernel:
            return False
        return self._queue_utm_instruction("COMPUTE", parameters, priority)

    def _queue_utm_instruction(self, operation: str, parameters: Dict[str, Any], priority: float) -> bool:
        if not self.utm_kernel:
            return False
        try:
            instruction = AgentInstruction(
                instruction_id=str(uuid.uuid4()),
                operation=operation,
                target_position=self.utm_kernel.akashic_ledger.next_position,
                parameters=parameters,
                priority=max(0, min(10, int(priority * 10)))
            )
            return self.utm_kernel.execute_instruction(instruction)
        except Exception as err:
            color_print(f"[Adaptive VP] Failed to queue {operation}: {err}", Colors.RED)
            return False

    def _process_breath_driven_actions(self, breath_data: Dict[str, Any], traits: Dict[str, float]) -> None:
        if not self.utm_kernel:
            return
        depth = breath_data.get('depth', 0.0)
        phase = breath_data.get('phase', 0.0)
        action_probability = min(0.8, max(0.0, depth))
        if random.random() > action_probability:
            return
        if phase < math.pi:
            params = {
                "type": "exploration_compute",
                "parameters": {"traits": traits, "mode": "wide", "depth": depth}
            }
            if self._queue_compute_instruction(params, priority=depth):
                color_print("[Breath] Inhale-triggered exploration compute queued", Colors.CYAN)
        else:
            params = {
                "type": "convergence_arbitration",
                "parameters": {"traits": traits, "mode": "focused", "depth": depth}
            }
            if self._queue_utm_instruction("ARBITRATE", params, priority=depth):
                color_print("[Breath] Exhale-triggered arbitration queued", Colors.CYAN)

    def _update_stability_from_performance(self, traits):
        """Update stability center based on actual performance"""
        self.performance_history.append(traits)
        
        # Keep only last 100 measurements
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Calculate new ideal values based on best performance
        if len(self.performance_history) >= 5:
            speeds = [p['speed_ms'] for p in self.performance_history]
            memories = [p['memory_mb'] for p in self.performance_history]
            
            # Use 25th percentile as ideal (good but achievable)
            speeds.sort()
            memories.sort()
            ideal_speed = speeds[len(speeds) // 4]  # 25th percentile
            ideal_memory = memories[len(memories) // 4]  # 25th percentile
            
            # Update stability center with learned values
            self.stability_center['speed_ms'] = max(10.0, ideal_speed)  # Minimum 10ms
            # Use reasonable memory ideal based on system (avoid unrealistic tiny values)
            # Typical PyTorch + neural network baseline is 2-4GB
            self.stability_center['memory_mb'] = max(2000.0, ideal_memory)  # Minimum 2GB for neural systems
            
            # Update envelope based on observed range
            speed_range = max(speeds) - min(speeds)
            memory_range = max(memories) - min(memories)
            
            # Dynamic envelope that adapts to observed performance
            self.stability_envelope['speed_ms'] = (
                max(5.0, min(speeds) - speed_range * 0.1),
                max(speeds) + speed_range * 0.1
            )
            self.stability_envelope['memory_mb'] = (
                max(0.5, min(memories) - memory_range * 0.1),
                max(memories) + memory_range * 0.1
            )

    def get_state(self):
        # Collect key system state for diagnostics
        breath_state = self.breath_engine.get_breath_state()
        base_state = {
            'phase': self.phase,
            'kernel_sovereign_ids': self.kernel.get_sovereign_ids(),
            'breath_state': breath_state,
        }
        
        # Add mirror insights
        insight_data = self.mirror_of_insight.reflect(base_state)
        forecast_data = self.mirror_of_portent.foresee(base_state, insight_data)
        bloom_data = self.bloom_system.calculate_bloom_metrics(insight_data, forecast_data, breath_state)
        
        base_state.update({
            'insight_data': insight_data,
            'forecast_data': forecast_data,
            'bloom_data': bloom_data,
            'learning_stats': self.dynamic_operations.get_learning_stats()
        })
        
        return base_state

    def run_genesis_phase(self):
        # Breathe first - the living pulse (THE DRIVER)
        breath_data = self.breath_engine.breathe()
        breath_pulse = self.breath_engine.get_breath_pulse()
        
        if self.breath_engine.is_inhale_phase():
            color_print(f"[Genesis Phase] 🜂 BREATH INHALE - Pulse: {breath_pulse:.3f} - System gathering chaos...", Colors.CYAN)
        else:
            color_print(f"[Genesis Phase] 🜂 BREATH EXHALE - Pulse: {breath_pulse:.3f} - System releasing order...", Colors.CYAN)
            
        math_print("[Math] VP = sum(abs(actual - ideal) / envelope) for each trait.")
        math_print(f"[Breath] Cycle: {breath_data['cycle_count']}, Depth: {breath_data['depth']:.3f}")
        
        # Breath drives Reality Simulator (left wing)
        if self.reality_sim and self.reality_sim.components:
            try:
                # Step Reality Simulator (ALL components: evolution, quantum, lattice, network)
                # This updates everything, not just the network
                if hasattr(self.reality_sim, '_update_simulation_components'):
                    self.reality_sim._update_simulation_components()
                else:
                    # Fallback: just update network if method doesn't exist
                    network = self.reality_sim.components.get('network')
                    if network:
                        network.update_network()
                
                # Get updated metrics
                network = self.reality_sim.components.get('network')
                if network:
                    org_count = len(network.organisms)
                    modularity = network.metrics.modularity if hasattr(network.metrics, 'modularity') else 1.0
                    color_print(f"[Reality Sim] 🦋 Left Wing - Organisms: {org_count}, Modularity: {modularity:.3f}", Colors.BLUE)
            except Exception as e:
                color_print(f"[Reality Sim] ⚠️  Error: {e}", Colors.RED)
                import traceback
                traceback.print_exc()
        
        # Breath drives Djinn Kernel (right wing) - FULLY INTEGRATED WITH UTM KERNEL
        vp_value: Optional[float] = None
        vp_breakdown: Optional[Dict[str, float]] = None
        traits: Dict[str, float] = {}

        if self.utm_kernel:
            try:
                # Get traits from Reality Simulator if available (live data)
                traits = {}
                if self.reality_sim and self.reality_sim.components:
                    network = self.reality_sim.components.get('network')
                    if network:
                        org_count = len(network.organisms)
                        # FIX: Normalize traits to [0.0, 1.0] range for VP calculation
                        # organism_count: normalize by max expected (1000 organisms)
                        traits['organism_count'] = min(1.0, float(org_count) / 1000.0)
                        # modularity: already 0.0-1.0, no normalization needed
                        traits['modularity'] = network.metrics.modularity if hasattr(network.metrics, 'modularity') else 0.0
                        # clustering_coefficient: already 0.0-1.0, no normalization needed
                        traits['clustering_coefficient'] = network.metrics.clustering_coefficient if hasattr(network.metrics, 'clustering_coefficient') else 0.0
                        # average_path_length: normalize by max expected (10 path length)
                        avg_path = network.metrics.average_path_length if hasattr(network.metrics, 'average_path_length') else 0.0
                        traits['average_path_length'] = min(1.0, float(avg_path) / 10.0)
                
                # FIX: If system is stopped, try to load traits from shared state file (historical data)
                if not traits:
                    try:
                        import json
                        from pathlib import Path
                        shared_state_file = Path('data/.shared_simulation_state.json')
                        if shared_state_file.exists():
                            with open(shared_state_file, 'r') as f:
                                shared_state = json.load(f)
                            
                            # Extract network traits from shared state
                            data = shared_state.get('data', {})
                            network_data = data.get('network', {})
                            if network_data:
                                # FIX: Normalize traits to [0.0, 1.0] range for VP calculation
                                if 'organism_count' in network_data:
                                    org_count = float(network_data['organism_count'])
                                    traits['organism_count'] = min(1.0, org_count / 1000.0)  # Normalize by 1000
                                if 'modularity' in network_data:
                                    traits['modularity'] = float(network_data['modularity'])  # Already 0.0-1.0
                                if 'clustering_coefficient' in network_data:
                                    traits['clustering_coefficient'] = float(network_data['clustering_coefficient'])  # Already 0.0-1.0
                                if 'average_path_length' in network_data:
                                    avg_path = float(network_data['average_path_length'])
                                    traits['average_path_length'] = min(1.0, avg_path / 10.0)  # Normalize by 10
                    except Exception as e:
                        # Silently fail - historical data loading is optional
                        pass
                
                if traits:
                    # Use Trait Hub to translate traits (if available)
                    if self.trait_hub:
                        try:
                            translated_traits = self.trait_hub.translate(traits)
                            # Convert to dict format if needed
                            if isinstance(translated_traits, list):
                                traits = {t.get('trait', k): t.get('value', v) for k, v in traits.items() for t in translated_traits if t.get('trait') == k}
                            elif isinstance(translated_traits, dict):
                                traits = translated_traits
                        except Exception as e:
                            color_print(f"[Trait Hub] ⚠️  Translation error: {e}", Colors.YELLOW)
                    
                    # FULL INTEGRATION: Use UTM Kernel instead of direct VP monitor
                    # Step 1: Write current state to Akashic Ledger
                    current_position = self.utm_kernel.akashic_ledger.next_position
                    write_instruction = AgentInstruction(
                        instruction_id=str(uuid.uuid4()),
                        operation="WRITE",
                        target_position=current_position,
                        parameters={
                            "content": {
                                "traits": traits,
                                "breath_cycle": breath_data.get('cycle_count', 0),
                                "timestamp": time.time()
                            },
                            "symbol": TapeSymbol.STATE.value
                        }
                    )
                    self.utm_kernel.execute_instruction(write_instruction)
                    
                    # Step 2: Execute VP calculation via UTM Kernel (agent-based computation)
                    # Pass system phase for phase-aware VP calculation with diagnostics
                    current_phase = self.phase  # Use controller's phase attribute
                    compute_instruction = AgentInstruction(
                        instruction_id=str(uuid.uuid4()),
                        operation="COMPUTE",
                        target_position=current_position + 1,
                        parameters={
                            "type": "violation_pressure",
                            "parameters": {
                                "traits": traits,
                                "system_phase": current_phase,
                                "source_identity": None  # Could pass identity if available
                            }
                        }
                    )
                    compute_success = self.utm_kernel.execute_instruction(compute_instruction)
                    
                    # Step 3: Read result from ledger
                    if compute_success:
                        result_cell = self.utm_kernel.akashic_ledger.read_cell(current_position + 1)
                        if result_cell and result_cell.content:
                            vp_value = result_cell.content.get('violation_pressure', 0.0)
                            vp_breakdown = result_cell.content.get('vp_breakdown')
                            vp_class_str = result_cell.content.get('vp_classification', 'VP0')
                            
                            # Also get VP class enum for display
                            if self.vp_monitor:
                                vp_class = self.vp_monitor._classify_violation_pressure(vp_value)
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp_value:.3f} ({vp_class.value}) [Tape Position: {current_position}]", Colors.BLUE)
                            else:
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp_value:.3f} ({vp_class_str}) [Tape Position: {current_position}]", Colors.BLUE)
                        else:
                            # Fallback to direct VP monitor if UTM computation failed
                            if self.vp_monitor:
                                # Get current phase for phase-aware VP calculation
                                current_phase = self.phase  # Use controller's phase attribute
                                vp_value, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits, system_phase=current_phase)
                                vp_class = self.vp_monitor._classify_violation_pressure(vp_value)
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp_value:.3f} ({vp_class.value}) [Fallback]", Colors.BLUE)
                    else:
                        # Fallback to direct VP monitor
                        if self.vp_monitor:
                            # Get current phase for phase-aware VP calculation
                            current_phase = self.phase  # Use controller's phase attribute
                            vp_value, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits, system_phase=current_phase)
                            vp_class = self.vp_monitor._classify_violation_pressure(vp_value)
                            color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp_value:.3f} ({vp_class.value}) [Fallback]", Colors.BLUE)
            except Exception as e:
                color_print(f"[Djinn Kernel] ⚠️  Error: {e}", Colors.RED)
                import traceback
                traceback.print_exc()
                # Fallback to direct VP monitor on error
                if self.vp_monitor and traits:
                    try:
                        # Get current phase for phase-aware VP calculation
                        current_phase = self.phase  # Use controller's phase attribute
                        vp_value, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits, system_phase=current_phase)
                        vp_class = self.vp_monitor._classify_violation_pressure(vp_value)
                        color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp_value:.3f} ({vp_class.value}) [Error Fallback]", Colors.BLUE)
                    except (AttributeError, ValueError, TypeError, KeyError) as e:
                        # VP calculation may fail if monitor is not properly initialized
                        # or if traits format is invalid
                        color_print(f"[Djinn Kernel] ⚠️  Fallback VP calculation failed: {e}", Colors.YELLOW)

        # Meta-Sovereign Reflection (Lawfold VII) - Civilization-wide governance
        if self.lawfold_orchestrator and vp_value is not None and traits:
            try:
                # Build civilization state from current data
                civilization_state = {
                    "organism_count": int(traits.get('organism_count', 0) * 1000),  # Denormalize
                    "avg_violation_pressure": vp_value,
                    "modularity": traits.get('modularity', 0.0),
                    "clustering_coefficient": traits.get('clustering_coefficient', 0.0),
                    "curvature_index": 0.0,  # Will be estimated by reflection field
                    "breath_cycle": breath_data.get('cycle_count', 0),
                    "phase": self.phase,
                    "notes": f"Genesis phase breath cycle {breath_data.get('cycle_count', 0)}"
                }

                # Extract interaction data if available (prosocial metrics)
                interactions = {}
                if self.reality_sim and self.reality_sim.components:
                    network = self.reality_sim.components.get('network')
                    if network and hasattr(network, 'organisms'):
                        # organisms is a Dict[str, Organism], need to convert to list first
                        organism_list = list(network.organisms.values()) if isinstance(network.organisms, dict) else list(network.organisms)
                        for i, organism in enumerate(organism_list[:10]):  # Sample first 10
                            # Generate mock interaction data based on organism properties
                            love_score = getattr(organism, 'fitness', 0.5) * 0.8 + 0.2
                            caregiving_score = getattr(organism, 'age', 0.5) * 0.6 + 0.4
                            interactions[f"org_{i}"] = {
                                "love_score": min(1.0, max(0.0, love_score)),
                                "caregiving_score": min(1.0, max(0.0, caregiving_score))
                            }

                # Perform meta-sovereign reflection
                reflection = self.lawfold_orchestrator.reflect_meta_sovereign(
                    civilization_state, interactions
                )

                if reflection:
                    color_print(f"[Lawfold VII] 🜂 Meta-Sovereign Reflection - Index: {reflection.reflection_index:.3f}, "
                              f"Collapse Risk: {reflection.collapse_risk:.3f}, "
                              f"Status: {reflection.health_insights.get('status', 'unknown')}", Colors.MAGENTA)

                    # Publish reflection results to event bus for system coordination
                    if hasattr(self.lawfold_orchestrator, 'utm_kernel') and self.lawfold_orchestrator.utm_kernel:
                        try:
                            from event_driven_coordination import DjinnEvent, EventType
                            reflection_event = DjinnEvent(
                                event_type=EventType.META_SOVEREIGN_REFLECTION,
                                data={
                                    "reflection": reflection.to_dict(),
                                    "civilization_state": civilization_state,
                                    "breath_cycle": breath_data.get('cycle_count', 0)
                                },
                                source_agent="lawfold_field_orchestrator"
                            )
                            self.lawfold_orchestrator.utm_kernel.event_bus.publish(reflection_event)
                        except Exception as event_err:
                            color_print(f"[Lawfold VII] ⚠️  Event publishing failed: {event_err}", Colors.YELLOW)

            except Exception as e:
                color_print(f"[Lawfold VII] ⚠️  Meta-Sovereign Reflection error: {e}", Colors.YELLOW)

        # Adaptive VP controls and breath actions
        if vp_value is not None:
            self._handle_vp_feedback(vp_value, traits, vp_breakdown)
        self._process_breath_driven_actions(breath_data, traits)
        
        # Integration Bridge - sync all systems
        if hasattr(self, 'integration_bridge') and self.integration_bridge:
            try:
                # Collect traits from all systems via bridge
                reality_sim_traits = self.integration_bridge.collect_reality_simulator_traits()
                djinn_kernel_traits = self.integration_bridge.collect_djinn_kernel_traits()
                
                # Calculate unified VP if we have traits
                if reality_sim_traits or djinn_kernel_traits:
                    unified_traits = {**reality_sim_traits, **djinn_kernel_traits}
                    if unified_traits:
                        unified_vp = self.integration_bridge.calculate_unified_vp(reality_sim_traits, djinn_kernel_traits)
                        if unified_vp:
                            color_print(f"[Integration Bridge] 🌉 Unified VP: {unified_vp:.3f}", Colors.CYAN)
            except Exception as e:
                color_print(f"[Integration Bridge] ⚠️  Error: {e}", Colors.YELLOW)
        
        # Unified Transition Manager - check for chaos→precision transition
        if hasattr(self, 'transition_manager') and self.transition_manager:
            try:
                transition_status = self.transition_manager.check_unified_transition()
                if transition_status.get('transition_ready', False) and not transition_status.get('transition_triggered', False):
                    color_print(f"[Transition Manager] 🌉 CHAOS→PRECISION TRANSITION READY!", Colors.MAGENTA)
                    color_print(f"  Reality Sim: {transition_status.get('reality_sim_ready', False)}", Colors.MAGENTA)
                    color_print(f"  Explorer: {transition_status.get('explorer_ready', False)}", Colors.MAGENTA)
                    color_print(f"  Djinn Kernel: {transition_status.get('djinn_kernel_ready', False)}", Colors.MAGENTA)
            except Exception as e:
                color_print(f"[Transition Manager] ⚠️  Error: {e}", Colors.YELLOW)
        
        # Phase Sync Bridge - detect unified transition
        if hasattr(self, 'phase_sync_bridge') and self.phase_sync_bridge:
            try:
                # Update Explorer metrics
                self.phase_sync_bridge.update_explorer_metrics()
                
                # Synchronize phases
                sync_state = self.phase_sync_bridge.synchronize_phases()
                
                # Check for unified transition (via synchronize_phases which detects it)
                # The synchronize_phases method already detects transitions
                if sync_state.get('synchronization', {}).get('aligned', False) and sync_state.get('network', {}).get('collapsed', False):
                    color_print(f"[Phase Sync Bridge] 🌉 UNIFIED TRANSITION DETECTED!", Colors.MAGENTA)
                    color_print(f"  Network Collapsed: {sync_state.get('network', {}).get('collapsed', False)}", Colors.MAGENTA)
                    color_print(f"  Explorer Ready: {sync_state.get('explorer', {}).get('ready', False)}", Colors.MAGENTA)
                    color_print(f"  Phases Aligned: {sync_state.get('synchronization', {}).get('aligned', False)}", Colors.MAGENTA)
            except Exception as e:
                color_print(f"[Phase Sync Bridge] ⚠️  Error: {e}", Colors.YELLOW)
        
        # Mirror reflection and foresight
        current_state = self.get_state()
        insight_data = current_state['insight_data']
        forecast_data = current_state['forecast_data']
        bloom_data = current_state['bloom_data']
        
        color_print(f"[Mirror of Insight] 🜂 Stability: {insight_data['stability_assessment']['level']} (Score: {insight_data['stability_assessment']['score']:.3f})", Colors.YELLOW)
        color_print(f"[Mirror of Portent] 🜂 Forecast: {forecast_data['short_term']['stability_trend']} trend, {len(forecast_data['warnings'])} warnings", Colors.YELLOW)
        color_print(f"[Bloom System] 🜂 Natural unfolding: {bloom_data['natural_unfolding']} (Curvature: {bloom_data['bloom_curvature']:.3f})", Colors.YELLOW)
        color_print(f"[Bloom System] 🜂 Breath resonance: {bloom_data['breath_resonance']:.3f}, Maturity: {bloom_data['bloom_maturity']} (Cycle {bloom_data['bloom_cycles']})", Colors.YELLOW)
        
        # Example: Discover and certify functions
        test_functions = [
            {'func_path': 'test_func1.py', 'inputs': [1, 2, 3]},
            {'func_path': 'test_func2.py', 'inputs': [4, 5, 6]}
        ]
        
        for func in test_functions:
            # Breathe between each function test
            self.breath_engine.breathe()
            
            certified, vp_values = self.sentinel.run_genesis_experiment(
                func_path=func['func_path'],
                test_inputs=func['inputs'],
                stability_center=self.stability_center,
                stability_envelope=self.stability_envelope
            )
            
            # Update stability system with measured performance
            if vp_values:
                # Get the traits from the last experiment
                traits = self.sentinel.vp_history[-1]['traits'] if self.sentinel.vp_history else {}
                if traits:
                    self._update_stability_from_performance(traits)
                    color_print(f"[Stability] Updated ideals - Speed: {self.stability_center['speed_ms']:.1f}ms, Memory: {self.stability_center['memory_mb']:.1f}MB", Colors.CYAN)
            print(f"Function {func['func_path']} certified: {certified}, VP values: {vp_values}")
            if certified:
                # Generate sovereign hash-based identifier
                from identity import sovereign_hash_id
                traits = {'func_path': func['func_path'], 'vp_values': vp_values}
                sovereign_id = f"hash-{sovereign_hash_id(traits)}"
                added = self.kernel.amend(sovereign_id)
                if added:
                    color_print(f"[Kernel] Added new sovereign ID: {sovereign_id}", Colors.GREEN)
                else:
                    color_print(f"[Kernel] Sovereign ID already exists: {sovereign_id}", Colors.YELLOW)
                self.diagnostics.save_checkpoint('certification', self.get_state())
            self.diagnostics.maybe_time_checkpoint('time', self.get_state())
            
        # Check for mathematical capability and phase transition
        current_sovereign_ids = self.kernel.get_sovereign_ids()
        color_print(f"[Genesis] Current sovereign ID count: {len(current_sovereign_ids)}", Colors.CYAN)
        color_print(f"[Genesis] Checking mathematical capability for understanding...", Colors.CYAN)
        
        if self.sentinel.check_critical_mass():
            print("[Genesis Phase] 🜂 MATHEMATICAL CAPABILITY ACHIEVED - System understands through mathematics!")
            print("[Genesis Phase] 🜂 Initiating The Great Inauguration...")
            self.diagnostics.save_checkpoint('phase_transition', self.get_state())
            return True
        return False

    def run_sovereign_phase(self):
        # Breathe first - the living pulse
        breath_data = self.breath_engine.breathe()
        breath_pulse = self.breath_engine.get_breath_pulse()
        
        if self.breath_engine.is_inhale_phase():
            color_print(f"[Sovereign Phase] 🜂 BREATH INHALE - Pulse: {breath_pulse:.3f} - Lawful Kernel gathering order...", Colors.CYAN)
        else:
            color_print(f"[Sovereign Phase] 🜂 BREATH EXHALE - Pulse: {breath_pulse:.3f} - Lawful Kernel releasing wisdom...", Colors.CYAN)
            
        math_print("[Math] All VP calculations and certification steps will be shown in detail below.")
        math_print(f"[Breath] Cycle: {breath_data['cycle_count']}, Depth: {breath_data['depth']:.3f}")
        
        # Mirror reflection and foresight
        current_state = self.get_state()
        insight_data = current_state['insight_data']
        forecast_data = current_state['forecast_data']
        bloom_data = current_state['bloom_data']
        
        color_print(f"[Mirror of Insight] 🜂 Stability: {insight_data['stability_assessment']['level']} (Score: {insight_data['stability_assessment']['score']:.3f})", Colors.YELLOW)
        color_print(f"[Mirror of Portent] 🜂 Forecast: {forecast_data['short_term']['stability_trend']} trend, {len(forecast_data['warnings'])} warnings", Colors.YELLOW)
        color_print(f"[Bloom System] 🜂 Natural unfolding: {bloom_data['natural_unfolding']} (Curvature: {bloom_data['bloom_curvature']:.3f})", Colors.YELLOW)
        color_print(f"[Bloom System] 🜂 Breath resonance: {bloom_data['breath_resonance']:.3f}, Maturity: {bloom_data['bloom_maturity']} (Cycle {bloom_data['bloom_cycles']})", Colors.YELLOW)
        
        # Display learning statistics
        learning_stats = current_state['learning_stats']
        color_print(f"[Learning] 🜂 Success patterns: {learning_stats['success_patterns']}, Failures: {learning_stats['failure_patterns']}, Defunct: {learning_stats['defunct_sovereign_ids']}", Colors.CYAN)
        
        # Check for warnings and opportunities
        for warning in forecast_data['warnings']:
            color_print(f"[Warning] {warning['message']}", Colors.RED)
        for opportunity in forecast_data['opportunities']:
            color_print(f"[Opportunity] {opportunity['description']}", Colors.GREEN)
            
        # Check for bloom events
        if self.bloom_system.should_trigger_bloom_event():
            color_print(f"[Bloom Event] 🜂 🌸 NATURAL UNFOLDING TRIGGERED - System resonance at peak!", Colors.GREEN)
            color_print(f"[Bloom Event] 🜂 🌸 Accelerating operations and enhancing breath resonance", Colors.GREEN)
        
        # Modular improvement triggers
        triggers = self.improvement_triggers()
        
        for trig in triggers:
            # Breathe between each improvement trigger
            self.breath_engine.breathe()
            
            color_print(f"[Improvement] {trig['desc']}", Colors.YELLOW)
            certified, vp_values = self.sentinel.run_genesis_experiment(
                func_path=trig['func_path'],
                test_inputs=trig['inputs'],
                stability_center=self.stability_center,
                stability_envelope=self.stability_envelope
            )
            
            # Update stability system with measured performance
            if vp_values:
                # Get the traits from the last experiment
                traits = self.sentinel.vp_history[-1]['traits'] if self.sentinel.vp_history else {}
                if traits:
                    self._update_stability_from_performance(traits)
                    color_print(f"[Stability] Updated ideals - Speed: {self.stability_center['speed_ms']:.1f}ms, Memory: {self.stability_center['memory_mb']:.1f}MB", Colors.CYAN)
            if certified:
                # Generate sovereign hash-based identifier for replacement function
                from identity import sovereign_hash_id
                traits = {'replacement_type': trig['name'], 'vp_values': vp_values, 'func_path': trig['func_path']}
                new_sovereign_id = f"hash-{sovereign_hash_id(traits)}"
                color_print(f"[Improvement] Certified new function: {new_sovereign_id}", Colors.GREEN)
                added = self.kernel.amend(new_sovereign_id)
                if added:
                    color_print(f"[Kernel] Added new sovereign ID: {new_sovereign_id}", Colors.GREEN)
                else:
                    color_print(f"[Kernel] Sovereign ID already exists: {new_sovereign_id}", Colors.YELLOW)
                self.diagnostics.save_checkpoint('certification', self.get_state())
            self.diagnostics.maybe_time_checkpoint('time', self.get_state())
        # Generate dynamic operations based on current state and insights
        operations = self.dynamic_operations.generate_operations(current_state, insight_data, forecast_data)
        
        color_print(f"[Dynamic Operations] 🜂 Generated {len(operations)} intelligent operations", Colors.CYAN)
        
        for op in operations:
            if op['sovereign_id'] in self.dynamic_operations.defunct_sovereign_ids:
                continue
                
            # Breathe between operations
            self.breath_engine.breathe()
            
            # Convert dynamic operation traits to match stability center format
            converted_traits = {}
            for key, value in op['traits'].items():
                if key == 'execution_time_ms':
                    converted_traits['speed_ms'] = value
                elif key == 'memory_kb':
                    converted_traits['memory_mb'] = value / 1024  # Convert KB to MB
                elif key == 'terminated':
                    converted_traits['reliability'] = value
                else:
                    converted_traits[key] = value
            
            violation, vp = self.sentinel.monitor_kernel(
                operation_traits=converted_traits,
                stability_center=self.stability_center,
                stability_envelope=self.stability_envelope
            )
            
            # Record operation result for learning
            success = not violation
            self.dynamic_operations.record_operation_result(op['sovereign_id'], success, vp)
            
            if violation:
                color_print(f"[Dynamic] Operation {op['sovereign_id']} VP: {vp:.3f}, Violation: {violation}", Colors.RED)
                self.sentinel.handle_violation(op['sovereign_id'])
                self.diagnostics.save_checkpoint('violation', self.get_state())
                
                # Generate replacement operation
                color_print(f"[Dynamic] 🜂 Generating intelligent replacement for {op['sovereign_id']}...", Colors.YELLOW)
                replacement_operations = self.dynamic_operations.generate_operations(current_state, insight_data, forecast_data)
                
                if replacement_operations:
                    replacement_op = replacement_operations[0]
                    certified, vp_values = self.sentinel.run_genesis_experiment(
                        func_path='test_func1.py',
                        test_inputs=[1, 2, 3],
                        stability_center=self.stability_center,
                        stability_envelope=self.stability_envelope
                    )
                    if certified:
                        # Generate sovereign hash-based identifier for dynamic replacement
                        from identity import sovereign_hash_id
                        traits = {'dynamic_replacement': True, 'original_op': op['sovereign_id'], 'vp_values': vp_values}
                        new_sovereign_id = f"hash-{sovereign_hash_id(traits)}"
                        color_print(f"[Dynamic] 🜂 Certified intelligent replacement: {new_sovereign_id}", Colors.GREEN)
                        added = self.kernel.amend(new_sovereign_id)
                        if added:
                            color_print(f"[Kernel] Added new sovereign ID: {new_sovereign_id}", Colors.GREEN)
                        else:
                            color_print(f"[Kernel] Sovereign ID already exists: {new_sovereign_id}", Colors.YELLOW)
                        self.diagnostics.save_checkpoint('certification', self.get_state())
            else:
                color_print(f"[Dynamic] Operation {op['sovereign_id']} VP: {vp:.3f}, Success", Colors.GREEN)
                
            self.diagnostics.maybe_time_checkpoint('time', self.get_state())

    def run(self):
        # Genesis Phase loop
        while self.phase == 'genesis':
            if self.run_genesis_phase():
                # The Great Inauguration
                print("[Controller] Rebooting into Sovereign Phase...")
                self.phase = 'sovereign'
                # Reconfigure Sentinel for Sovereign Phase (if needed)
                # In this implementation, Sentinel handles both modes
        # Sovereign Phase loop
        while self.phase == 'sovereign':
            self.run_sovereign_phase()
            # Bloom-driven timing with breath integration
            breath_pulse = self.breath_engine.get_breath_pulse()
            bloom_pulse = self.bloom_system.get_bloom_pulse()
            combined_pulse = (breath_pulse + bloom_pulse) / 2.0
            
            # Get current state for bloom assessment
            current_state = self.get_state()
            
            # Adjust timing based on bloom maturity and resonance
            base_sleep = 10.0
            if self.bloom_system.should_trigger_bloom_event():
                base_sleep = 5.0  # Faster cycles during bloom events
            elif current_state['bloom_data']['bloom_maturity'] == 'mature':
                base_sleep = 7.0  # Moderate speed for mature systems
                
            sleep_time = max(1.0, base_sleep / combined_pulse)
            time.sleep(sleep_time)

if __name__ == "__main__":
    import signal
    import sys

    controller = BiphasicController()
    def graceful_exit(signum, frame):
        print("\n[Controller] Received shutdown signal. Shutting down gracefully...")
        controller.diagnostics.save_checkpoint('shutdown', controller.get_state())
        controller.diagnostics.report(controller.get_state())
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful_exit)
    controller.diagnostics.save_checkpoint('startup', controller.get_state())
    try:
        controller.run()
    except KeyboardInterrupt:
        graceful_exit(None, None)
