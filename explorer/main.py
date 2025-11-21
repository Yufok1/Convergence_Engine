

import time
import sys
import os
from pathlib import Path
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
    from main import RealitySimulator
    REALITY_SIM_AVAILABLE = True
except ImportError:
    REALITY_SIM_AVAILABLE = False
    print("[Explorer] Reality Simulator not available")

try:
    from utm_kernel_design import UTMKernel
    from violation_pressure_calculation import ViolationMonitor
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
    def __init__(self):
        # Initialize systems
        self.kernel = Kernel()
        self.sentinel = Sentinel()
        self.diagnostics = Diagnostics()
        self.breath_engine = BreathEngine()
        self.mirror_of_insight = MirrorOfInsight()
        self.mirror_of_portent = MirrorOfPortent()
        self.bloom_system = BloomSystem()
        self.dynamic_operations = DynamicOperations()
        
        # Initialize Reality Simulator (if available)
        if REALITY_SIM_AVAILABLE:
            try:
                config_path = str(parent_path / 'config.json')
                self.reality_sim = RealitySimulator(config_path=config_path)
                
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
                self.vp_monitor = ViolationMonitor()
                print("[Explorer] ✅ Djinn Kernel initialized")
            except Exception as e:
                print(f"[Explorer] ⚠️  Djinn Kernel error: {e}")
                self.utm_kernel = None
                self.vp_monitor = None
        else:
            self.utm_kernel = None
            self.vp_monitor = None
        
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
            'memory_mb': (1.0, 500.0),     # 1MB to 500MB
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
            self.stability_center['memory_mb'] = max(1.0, ideal_memory)  # Minimum 1MB
            
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
        if self.utm_kernel:
            try:
                # Get traits from Reality Simulator if available
                traits = {}
                if self.reality_sim and self.reality_sim.components:
                    network = self.reality_sim.components.get('network')
                    if network:
                        org_count = len(network.organisms)
                        traits['organism_count'] = float(org_count)
                        traits['modularity'] = network.metrics.modularity if hasattr(network.metrics, 'modularity') else 1.0
                        traits['clustering_coefficient'] = network.metrics.clustering_coefficient if hasattr(network.metrics, 'clustering_coefficient') else 0.0
                        traits['average_path_length'] = network.metrics.average_path_length if hasattr(network.metrics, 'average_path_length') else 0.0
                
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
                    from utm_kernel_design import AgentInstruction, TapeSymbol
                    import uuid
                    import time
                    
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
                    compute_instruction = AgentInstruction(
                        instruction_id=str(uuid.uuid4()),
                        operation="COMPUTE",
                        target_position=current_position + 1,
                        parameters={
                            "type": "violation_pressure",
                            "parameters": {
                                "traits": traits
                            }
                        }
                    )
                    compute_success = self.utm_kernel.execute_instruction(compute_instruction)
                    
                    # Step 3: Read result from ledger
                    if compute_success:
                        result_cell = self.utm_kernel.akashic_ledger.read_cell(current_position + 1)
                        if result_cell and result_cell.content:
                            vp = result_cell.content.get('violation_pressure', 0.0)
                            vp_class_str = result_cell.content.get('vp_classification', 'VP0')
                            
                            # Also get VP class enum for display
                            if self.vp_monitor:
                                vp_class = self.vp_monitor._classify_violation_pressure(vp)
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp:.3f} ({vp_class.value}) [Tape Position: {current_position}]", Colors.BLUE)
                            else:
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp:.3f} ({vp_class_str}) [Tape Position: {current_position}]", Colors.BLUE)
                        else:
                            # Fallback to direct VP monitor if UTM computation failed
                            if self.vp_monitor:
                                vp, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits)
                                vp_class = self.vp_monitor._classify_violation_pressure(vp)
                                color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp:.3f} ({vp_class.value}) [Fallback]", Colors.BLUE)
                    else:
                        # Fallback to direct VP monitor
                        if self.vp_monitor:
                            vp, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits)
                            vp_class = self.vp_monitor._classify_violation_pressure(vp)
                            color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp:.3f} ({vp_class.value}) [Fallback]", Colors.BLUE)
            except Exception as e:
                color_print(f"[Djinn Kernel] ⚠️  Error: {e}", Colors.RED)
                import traceback
                traceback.print_exc()
                # Fallback to direct VP monitor on error
                if self.vp_monitor and traits:
                    try:
                        vp, vp_breakdown = self.vp_monitor.compute_violation_pressure(traits)
                        vp_class = self.vp_monitor._classify_violation_pressure(vp)
                        color_print(f"[Djinn Kernel] 🦋 Right Wing - VP: {vp:.3f} ({vp_class.value}) [Error Fallback]", Colors.BLUE)
                    except (AttributeError, ValueError, TypeError, KeyError) as e:
                        # VP calculation may fail if monitor is not properly initialized
                        # or if traits format is invalid
                        color_print(f"[Djinn Kernel] ⚠️  Fallback VP calculation failed: {e}", Colors.YELLOW)
        
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
