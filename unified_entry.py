"""
UNIFIED ENTRY POINT - THE BUTTERFLY SYSTEM

Single cohesive unit: Explorer + Reality Simulator + Djinn Kernel
One process. One breath. Three systems unified.

Features:
- Pre-flight system checks (redundant, comprehensive)
- Extensive state logging (granular, terse, information-saturated)
- Unified visualization (Left: Reality Sim, Middle: Explorer, Right: Djinn Kernel)
- All systems wired as one machine
"""

import sys
import os
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import datetime as dt_module
import traceback
import webbrowser

from runtime_config import ConfigHotReloadWatcher

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Setup paths
parent_path = Path(__file__).parent
explorer_path = parent_path / 'explorer'
reality_sim_path = parent_path / 'reality_simulator'
kernel_path = parent_path / 'kernel'

sys.path.insert(0, str(explorer_path))
sys.path.insert(0, str(reality_sim_path))
sys.path.insert(0, str(kernel_path))

# Import all systems
try:
    from explorer.main import BiphasicController
    from explorer.breath_engine import BreathEngine
    EXPLORER_AVAILABLE = True
except ImportError as e:
    EXPLORER_AVAILABLE = False
    logger.warning(f"Explorer not available: {e}")

try:
    from reality_simulator.main import RealitySimulator
    REALITY_SIM_AVAILABLE = True
except ImportError as e:
    REALITY_SIM_AVAILABLE = False
    logger.warning(f"Reality Simulator not available: {e}")

try:
    # Import directly from kernel directory (not as package)
    from utm_kernel_design import UTMKernel
    from violation_pressure_calculation import ViolationMonitor
    from lawfold_field_architecture import LawfoldFieldOrchestrator
    DJINN_KERNEL_AVAILABLE = True
except ImportError as e:
    DJINN_KERNEL_AVAILABLE = False
    logger.warning(f"Djinn Kernel not available: {e}")

# Import integration facilities
try:
    from reality_simulator.phase_sync_bridge import PhaseSynchronizationBridge
    PHASE_SYNC_AVAILABLE = True
except ImportError as e:
    PHASE_SYNC_AVAILABLE = False
    logger.warning(f"Phase Sync Bridge not available: {e}")


# ============================================================================
# PRE-FLIGHT SYSTEM CHECKS
# ============================================================================

@dataclass
class SystemCheck:
    """Result of a system check"""
    name: str
    status: str  # 'pass', 'warn', 'fail'
    message: str
    details: Dict[str, Any] = None

class PreFlightChecker:
    """Comprehensive pre-flight system checks"""
    
    def __init__(self):
        self.checks: List[SystemCheck] = []
        self.critical_failures = []
        self.warnings = []
    
    def check_dependencies(self, require_visualization: bool = True) -> List[SystemCheck]:
        """Check all Python dependencies
        
        Args:
            require_visualization: If False, tkinter is optional (for headless runs)
        """
        checks = []
        
        # Core dependencies (always required)
        core_deps = {
            'numpy': 'numpy',
            'networkx': 'networkx',
            'matplotlib': 'matplotlib',
        }
        
        for dep_name, import_name in core_deps.items():
            try:
                __import__(import_name)
                checks.append(SystemCheck(
                    name=f"dep_{dep_name}",
                    status='pass',
                    message=f"{dep_name} available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name=f"dep_{dep_name}",
                    status='fail',
                    message=f"{dep_name} missing"
                ))
                self.critical_failures.append(f"Missing dependency: {dep_name}")
        
        # Visualization dependencies (optional for headless runs)
        if require_visualization:
            try:
                __import__('tkinter')
                checks.append(SystemCheck(
                    name="dep_tkinter",
                    status='pass',
                    message="tkinter available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name="dep_tkinter",
                    status='fail',
                    message="tkinter missing (required for visualization)"
                ))
                self.critical_failures.append("Missing dependency: tkinter (required for visualization)")
        else:
            # Optional for headless runs
            try:
                __import__('tkinter')
                checks.append(SystemCheck(
                    name="opt_tkinter",
                    status='pass',
                    message="tkinter available (optional, not required for headless)"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name="opt_tkinter",
                    status='warn',
                    message="tkinter missing (optional for headless runs)"
                ))
                self.warnings.append("Optional dependency missing: tkinter (only needed for visualization)")
        
        # Optional dependencies
        optional_deps = {
            'win32job': 'pywin32 (optional, for Explorer)',
        }
        
        for dep_name, description in optional_deps.items():
            try:
                __import__(dep_name)
                checks.append(SystemCheck(
                    name=f"opt_{dep_name}",
                    status='pass',
                    message=f"{description} available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name=f"opt_{dep_name}",
                    status='warn',
                    message=f"{description} missing (optional)"
                ))
                self.warnings.append(f"Optional dependency missing: {description}")
        
        return checks
    
    def check_systems(self) -> List[SystemCheck]:
        """Check system availability"""
        checks = []
        
        checks.append(SystemCheck(
            name="explorer",
            status='pass' if EXPLORER_AVAILABLE else 'fail',
            message="Explorer available" if EXPLORER_AVAILABLE else "Explorer not available"
        ))
        
        checks.append(SystemCheck(
            name="reality_sim",
            status='pass' if REALITY_SIM_AVAILABLE else 'fail',
            message="Reality Simulator available" if REALITY_SIM_AVAILABLE else "Reality Simulator not available"
        ))
        
        checks.append(SystemCheck(
            name="djinn_kernel",
            status='pass' if DJINN_KERNEL_AVAILABLE else 'fail',
            message="Djinn Kernel available" if DJINN_KERNEL_AVAILABLE else "Djinn Kernel not available"
        ))
        
        if not EXPLORER_AVAILABLE:
            self.critical_failures.append("Explorer is required")
        if not REALITY_SIM_AVAILABLE:
            self.critical_failures.append("Reality Simulator is required")
        if not DJINN_KERNEL_AVAILABLE:
            self.warnings.append("Djinn Kernel not available (will run without it)")
        
        return checks
    
    def check_files(self) -> List[SystemCheck]:
        """Check required files exist"""
        checks = []
        
        required_files = {
            'config.json': parent_path / 'config.json',
            'explorer/main.py': explorer_path / 'main.py',
            'reality_simulator/main.py': reality_sim_path / 'main.py',
        }
        
        for name, path in required_files.items():
            if path.exists():
                checks.append(SystemCheck(
                    name=f"file_{name}",
                    status='pass',
                    message=f"{name} exists"
                ))
            else:
                checks.append(SystemCheck(
                    name=f"file_{name}",
                    status='fail',
                    message=f"{name} missing"
                ))
                self.critical_failures.append(f"Required file missing: {name}")
        
        return checks
    
    def check_directories(self) -> List[SystemCheck]:
        """Check required directories exist"""
        checks = []
        
        required_dirs = {
            'explorer': explorer_path,
            'reality_simulator': reality_sim_path,
            'kernel': kernel_path,
            'data': parent_path / 'data',
        }
        
        for name, path in required_dirs.items():
            if path.exists() and path.is_dir():
                checks.append(SystemCheck(
                    name=f"dir_{name}",
                    status='pass',
                    message=f"{name}/ exists"
                ))
            else:
                checks.append(SystemCheck(
                    name=f"dir_{name}",
                    status='warn',
                    message=f"{name}/ missing (will be created)"
                ))
                self.warnings.append(f"Directory missing: {name}/")
        
        return checks
    
    def check_memory(self) -> List[SystemCheck]:
        """Check system memory"""
        checks = []
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            mem_gb = mem.total / (1024**3)
            
            if mem_gb >= 4.0:
                checks.append(SystemCheck(
                    name="memory",
                    status='pass',
                    message=f"Memory: {mem_gb:.1f}GB available",
                    details={'total_gb': mem_gb, 'available_gb': mem.available / (1024**3)}
                ))
            elif mem_gb >= 2.0:
                checks.append(SystemCheck(
                    name="memory",
                    status='warn',
                    message=f"Memory: {mem_gb:.1f}GB (low)",
                    details={'total_gb': mem_gb}
                ))
                self.warnings.append("Low system memory")
            else:
                checks.append(SystemCheck(
                    name="memory",
                    status='fail',
                    message=f"Memory: {mem_gb:.1f}GB (insufficient)"
                ))
                self.critical_failures.append("Insufficient system memory")
        except ImportError:
            checks.append(SystemCheck(
                name="memory",
                status='warn',
                message="Memory check unavailable (psutil not installed)"
            ))
        
        return checks
    
    def run_all_checks(self, require_visualization: bool = True) -> Dict[str, Any]:
        """Run all pre-flight checks
        
        Args:
            require_visualization: If False, tkinter is optional (for headless runs)
        """
        print("\n" + "="*70)
        print("[BUTTERFLY] PRE-FLIGHT SYSTEM CHECKS")
        print("="*70)
        
        all_checks = []
        all_checks.extend(self.check_dependencies(require_visualization=require_visualization))
        all_checks.extend(self.check_systems())
        all_checks.extend(self.check_files())
        all_checks.extend(self.check_directories())
        all_checks.extend(self.check_memory())
        
        self.checks = all_checks
        
        # Print results
        for check in all_checks:
            if check.status == 'pass':
                print(f"[PASS] {check.name}: {check.message}")
            elif check.status == 'warn':
                print(f"[WARN] {check.name}: {check.message}")
            else:
                print(f"[FAIL] {check.name}: {check.message}")
        
        print("\n" + "="*70)
        
        if self.critical_failures:
            print("[FAIL] CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   - {failure}")
            print("\n[WARN] System cannot start with critical failures.")
            return {'can_start': False, 'checks': all_checks, 'failures': self.critical_failures}
        
        if self.warnings:
            print("[WARN] WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
            print("\n[WARN] System will start with warnings.")
        
        print("[PASS] All critical checks passed. System ready to start.")
        print("="*70 + "\n")
        
        return {
            'can_start': True,
            'checks': all_checks,
            'warnings': self.warnings,
            'failures': self.critical_failures
        }


# ============================================================================
# STATE LOGGING SYSTEM
# ============================================================================

class StateLogger:
    """Extensive, granular, terse, information-saturated state logging"""
    
    def __init__(self, log_dir: Path = None, causation_explorer=None):
        self.log_dir = log_dir or (parent_path / 'data' / 'logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.causation_explorer = causation_explorer  # For live event tracking
        
        # Create loggers
        self.loggers = {
            'state': self._create_logger('state', 'state.log'),
            'breath': self._create_logger('breath', 'breath.log'),
            'reality_sim': self._create_logger('reality_sim', 'reality_sim.log'),
            'explorer': self._create_logger('explorer', 'explorer.log'),
            'djinn_kernel': self._create_logger('djinn_kernel', 'djinn_kernel.log'),
            'neural': self._create_logger('neural', 'neural.log'),
            'system': self._create_logger('system', 'system.log'),
        }
        
        # State tracking
        self.state_history = []
        self.max_history = 10000
        self.last_event_time = 0  # Track last event timestamp
    
    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """Create a logger with terse, information-saturated format"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_dir / filename)
        file_handler.setLevel(logging.DEBUG)
        
        # Terse format: timestamp|level|component|metric:value|metric:value|...
        # Use custom formatter for microseconds support
        class MicrosecondFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                dt = dt_module.datetime.fromtimestamp(record.created)
                return dt.strftime('%H:%M:%S.%f')[:-3]  # Truncate to milliseconds
        
        formatter = MicrosecondFormatter(
            '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_state(self, component: str, state: Dict[str, Any], causation_explorer=None):
        """Log state in terse, information-saturated format"""
        # Format: metric:value|metric:value|...
        state_str = '|'.join([f"{k}:{v}" for k, v in state.items()])
        
        logger = self.loggers.get(component, self.loggers['system'])
        logger.debug(state_str)
        
        # Store in history
        timestamp = time.time()
        history_entry = {
            'timestamp': timestamp,
            'component': component,
            'state': state
        }
        self.state_history.append(history_entry)
        
        # Trim history
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
        
        # Update last event timestamp
        self.last_event_time = timestamp
        
        # Feed to Causation Explorer in real-time if available
        # These are TRULY new real-time events (not historical)
        if self.causation_explorer:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=timestamp,
                    component=component,
                    event_type=state.get('event', 'state_change'),
                    data=state
                )
                # is_historical=False because these are new real-time events from the backend
                self.causation_explorer.add_event(event, is_historical=False)
            except Exception as e:
                # Don't let causation tracking break logging
                pass
    
    def log_breath(self, breath_data: Dict[str, Any]):
        """Log breath state"""
        self.log_state('breath', {
            'cycle': breath_data.get('cycle_count', 0),
            'depth': f"{breath_data.get('depth', 0):.3f}",
            'phase': f"{breath_data.get('phase', 0):.3f}",
            'pulse': f"{breath_data.get('intensity', 0):.3f}",
        })
    
    def log_reality_sim(self, network_data: Dict[str, Any]):
        """Log Reality Simulator state"""
        self.log_state('reality_sim', {
            'orgs': network_data.get('organism_count', 0),
            'conns': network_data.get('connection_count', 0),
            'mod': f"{network_data.get('modularity', 0):.3f}",
            'clust': f"{network_data.get('clustering_coefficient', 0):.3f}",
            'path': f"{network_data.get('average_path_length', 0):.2f}",
            'gen': network_data.get('generation', 0),
        })
    
    def log_explorer(self, explorer_data: Dict[str, Any]):
        """Log Explorer state"""
        self.log_state('explorer', {
            'phase': explorer_data.get('phase', 'unknown'),
            'vp_calcs': explorer_data.get('vp_calculations', 0),
            'sovereign_ids': explorer_data.get('sovereign_ids_count', 0),
            'math_cap': explorer_data.get('mathematical_capability', False),
        })
    
    def log_djinn_kernel(self, kernel_data: Dict[str, Any]):
        """Log Djinn Kernel state"""
        self.log_state('djinn_kernel', {
            'vp': f"{kernel_data.get('violation_pressure', 0):.3f}",
            'vp_class': kernel_data.get('vp_classification', 'unknown'),
            'vp_calcs': kernel_data.get('vp_calculations', 0),
            'traits': kernel_data.get('trait_count', 0),
        })
    
    def log_neural(self, neural_data: Dict[str, Any]):
        """Log Neural System state"""
        self.log_state('neural', {
            'enabled': neural_data.get('enabled', False),
            'training_loss': f"{neural_data.get('training_loss', 0):.6f}" if neural_data.get('training_loss') is not None else 'N/A',
            'avg_epsilon': f"{neural_data.get('avg_epsilon', 0):.3f}",
            'organisms_tracked': neural_data.get('organisms_tracked', 0),
            'training_steps': neural_data.get('training_steps', 0),
            'avg_loss': f"{neural_data.get('avg_loss', 0):.6f}" if neural_data.get('avg_loss') is not None else 'N/A',
        })


# ============================================================================
# UNIFIED VISUALIZATION
# ============================================================================

class UnifiedVisualization:
    """Three-panel visualization: Left=Reality Sim, Middle=Explorer, Right=Djinn Kernel"""

    def __init__(self, network_ref=None, renderer_ref=None, reality_sim_ref=None):
        self.root = None
        self.fig = None
        self.axes = {}
        self.running = False
        self._network_ref = network_ref  # Reference to Reality Simulator network
        self._renderer_ref = renderer_ref  # Reference to Reality Simulator renderer
        self.reality_sim = reality_sim_ref  # Reference to Reality Simulator itself for metrics
        self.grid_enabled = True  # Grid toggle state
        self.canvas = None  # Store canvas reference for redraw
        self._last_reality_sim_state = {}  # Store last state for redraw
        
    def initialize(self):
        """Initialize matplotlib GUI with 3D network visualization"""
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import tkinter as tk

            self.root = tk.Tk()
            self.root.title("The Convergence Engine - 3D Network Visualization")
            self.root.geometry("1280x720")

            # Create figure with 3D network graph - make left panel dominant (60% width)
            from mpl_toolkits.mplot3d import Axes3D
            import matplotlib.gridspec as gridspec
            self.fig = plt.figure(figsize=(12.8, 7.2), facecolor='black')
            
            # Create GridSpec with 60/20/20 width ratios
            gs = gridspec.GridSpec(1, 5, figure=self.fig, width_ratios=[3, 0.2, 1, 0.2, 1], wspace=0.05)
            
            self.axes = {
                'left': self.fig.add_subplot(gs[0, 0], projection='3d'),   # Reality Simulator - 60% width, 3D
                'middle': self.fig.add_subplot(gs[0, 2]),                 # Explorer - 20% width
                'right': self.fig.add_subplot(gs[0, 4])                  # Djinn Kernel - 20% width
            }
            
            # Tight layout for cleaner appearance
            self.fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.04, wspace=0.05)

            # Setup axes
            for name, ax in self.axes.items():
                ax.set_facecolor('black')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')

            # Left axis is already 3D from GridSpec setup above

            # Embed in tkinter
            self.canvas = FigureCanvasTkAgg(self.fig, self.root)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Add grid toggle button
            self._create_grid_toggle_button()

            self.running = True
            print("[VISUALIZATION] [PASS] 3D network visualization initialized")

        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Error initializing: {e}")
            self.running = False
    
    def show(self):
        """Show the visualization window - called from main thread"""
        if self.root and self.running:
            try:
                # Make sure window is visible
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                print("[VISUALIZATION] [PASS] Visualization window displayed")
            except Exception as e:
                print(f"[VISUALIZATION] [WARN] Error showing window: {e}")
    
    def _create_grid_toggle_button(self):
        """Create toggle button for grid visibility"""
        try:
            import tkinter as tk
            button = tk.Button(
                self.root,
                text="Grid: ON",
                command=self._toggle_grid,
                bg="#050505",
                fg="#00ffff",
                activebackground="#1a1a1a",
                activeforeground="#00ffff",
                relief=tk.FLAT,
                padx=12,
                pady=6,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                borderwidth=1,
                highlightthickness=1,
                highlightbackground="#00ffff"
            )
            button.place(relx=0.99, rely=0.02, anchor='ne')
            self.grid_toggle_button = button
        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Error creating grid toggle: {e}")
    
    def _toggle_grid(self):
        """Toggle grid visibility and redraw"""
        self.grid_enabled = not self.grid_enabled
        if hasattr(self, 'grid_toggle_button'):
            self.grid_toggle_button.config(text=f"Grid: {'ON' if self.grid_enabled else 'OFF'}")
        # Redraw the reality sim panel with new grid state
        if self._last_reality_sim_state:
            djinn_state = getattr(self, '_last_djinn_kernel_state', {})
            self._update_reality_sim_panel(self.axes['left'], self._last_reality_sim_state, djinn_state)
            if self.canvas:
                self.canvas.draw()


    def update(self, reality_sim_state: Dict, explorer_state: Dict, djinn_kernel_state: Dict):
        """Update all three panels"""
        if not self.running:
            return

        try:
            import matplotlib.pyplot as plt
            # Prefer a Windows font that supports emojis
            # Suppress font warnings for missing emoji glyphs (expected behavior)
            import warnings
            warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')
            try:
                import matplotlib as mpl
                mpl.rcParams['font.family'] = ['Segoe UI Emoji', 'Segoe UI Symbol', 'DejaVu Sans']
            except Exception:
                pass

            # Left panel: Reality Simulator 3D Network
            self._last_reality_sim_state = reality_sim_state  # Store for grid toggle redraw
            self._last_djinn_kernel_state = djinn_kernel_state  # Store for grid toggle redraw
            self._update_reality_sim_panel(self.axes['left'], reality_sim_state, djinn_kernel_state)

            # Middle panel: Explorer
            self._update_explorer_panel(self.axes['middle'], explorer_state)

            # Right panel: Djinn Kernel
            self._update_djinn_kernel_panel(self.axes['right'], djinn_kernel_state)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
            # Process tkinter events so window updates properly (this is why the first window doesn't populate)
            if self.root:
                try:
                    self.root.update_idletasks()  # Process pending idle events
                    self.root.update()            # Process all pending events
                except:
                    pass  # Window might be closed

        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Update error: {e}")
    
    def _update_reality_sim_panel(self, ax, state: Dict, djinn_kernel_state: Dict = None):
        """Update Reality Simulator panel using 3D network visualization"""
        try:
            import sys
            import os
            from pathlib import Path
            import importlib.util

            # Import the visualization viewer
            viewer_path = Path(__file__).parent / 'reality_simulator' / 'visualization_viewer.py'
            if viewer_path.exists():
                spec = importlib.util.spec_from_file_location("visualization_viewer", viewer_path)
                viz_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(viz_module)

                # Create a viewer instance (or reuse if exists)
                if not hasattr(self, '_viewer'):
                    self._viewer = viz_module.LightweightVisualizationViewer()

                # Prepare data in the format expected by the viewer
                network = getattr(self, '_network_ref', None)

                # Build network data dict with actual graph edges and metrics
                network_data = {
                    'network': {
                        'organisms': state.get('organism_count', 0),
                        'connections': state.get('connection_count', 0),
                        'graph_edges': []
                    },
                    'stability': 0.0,
                    'connectivity': 0.0
                }

                # Get actual graph edges and metrics if network is available
                if network and hasattr(network, 'network_graph'):
                    G = network.network_graph
                    # Convert node IDs to integers for the viewer (it expects integer nodes)
                    node_map = {node: i for i, node in enumerate(G.nodes())}
                    network_data['network']['graph_edges'] = [(node_map[u], node_map[v]) for u, v in G.edges()]

                    # Add network metrics for diagnostic panels
                    if hasattr(network, 'metrics'):
                        stability = getattr(network.metrics, 'stability_index', 0.0)
                        connectivity = getattr(network.metrics, 'connectivity', 0.0)
                        network_data['stability'] = stability
                        network_data['connectivity'] = connectivity

                # Combine data from ALL systems for comprehensive diagnostic panels
                # Get neural data
                neural_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, '_neural_metrics'):
                    neural_data = self.reality_sim._neural_metrics

                # Get ML data
                ml_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, '_ml_metrics'):
                    ml_data = self.reality_sim._ml_metrics

                # Get evolution data - organisms live in network component
                evolution_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'components'):
                    network = self.reality_sim.components.get('network')
                    evolution = self.reality_sim.components.get('evolution')

                    # Get organisms from network component
                    if network and hasattr(network, 'organisms'):
                        organisms = network.organisms
                        # Handle organisms as dict or list
                        org_values = organisms.values() if isinstance(organisms, dict) else organisms
                        org_count = len(organisms) if organisms else 0

                        if org_count > 0:
                            fitnesses = [org.fitness for org in org_values if hasattr(org, 'fitness')]
                            generation = evolution.generation if evolution and hasattr(evolution, 'generation') else 0

                            evolution_data = {
                                'generation': generation,
                                'population_size': org_count,
                                'best_fitness': max(fitnesses) if fitnesses else 0.0,
                                'avg_fitness': sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
                            }
                        else:
                            evolution_data = {
                                'generation': 0,
                                'population_size': 0,
                                'best_fitness': 0.0,
                                'avg_fitness': 0.0
                            }

                # Get config_tuner data
                config_tuner_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
                    tuner_stats = self.reality_sim.config_tuner.get_stats()
                    config_tuner_data = {
                        'enabled': True,
                        'mode': self.reality_sim.config.get('meta_cognitive', {}).get('self_tuning', {}).get('mode', 'unknown'),
                        'stats': tuner_stats
                    }

                # Get djinn_kernel data (VP info) - passed as parameter
                djinn_kernel_data = djinn_kernel_state if djinn_kernel_state else {}

                # Get quantum data
                quantum_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'components'):
                    quantum = self.reality_sim.components.get('quantum')
                    if quantum:
                        quantum_data = {
                            'states': len(quantum.states) if hasattr(quantum, 'states') else 0
                        }

                viz_data = {
                    'network': network_data,
                    'neural': neural_data,
                    'ml': ml_data,
                    'evolution': evolution_data,
                    'config_tuner': config_tuner_data,
                    'djinn_kernel': djinn_kernel_data,
                    'quantum': quantum_data
                }

                # Ensure 3D axes
                from mpl_toolkits.mplot3d import Axes3D
                if not hasattr(ax, 'name') or getattr(ax, 'name', '') != '3d':
                    fig = ax.figure
                    try:
                        fig.delaxes(ax)
                    except:
                        pass
                    ax = fig.add_subplot(131, projection='3d')
                    self.axes['left'] = ax

                # Render using the existing 3D method (includes enhanced diagnostic panels!)
                self._viewer.render_network_graph(viz_data, ax)

                # NOTE: Do NOT remove text overlays - render_network_graph now includes
                # comprehensive 5-panel diagnostic dashboard utilizing empty space!
                # Panels: Network Topology, Neural/ML, Evolution/VP, Meta-Cognitive, Events

                # Make network dominant - set equal aspect and proper limits
                ax.set_box_aspect([1, 1, 1])
                
                # Add highly contrastive 3D grid background (only if enabled)
                if self.grid_enabled:
                    import numpy as np
                    # Use fewer grid lines for better performance and clarity
                    grid_range = np.linspace(-1, 1, 6)  # 6 lines per axis = clearer grid
                    grid_color = '#00ffff'  # Bright cyan for high contrast
                    grid_alpha = 0.5  # More visible
                    grid_linewidth = 0.8  # Thicker lines
                    
                    # Draw grid lines on key planes only (reduces clutter)
                    # XY plane at z = -1, 0, 1
                    for z_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([i, i], [-1, 1], [z_val, z_val], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([-1, 1], [i, i], [z_val, z_val], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                    
                    # XZ plane at y = -1, 0, 1
                    for y_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([i, i], [y_val, y_val], [-1, 1], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([-1, 1], [y_val, y_val], [i, i], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                    
                    # YZ plane at x = -1, 0, 1
                    for x_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([x_val, x_val], [i, i], [-1, 1], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([x_val, x_val], [-1, 1], [i, i], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)

                # Remove the hard-to-see box frame completely
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_zticks([])
                ax.xaxis.pane.fill = False
                ax.yaxis.pane.fill = False
                ax.zaxis.pane.fill = False
                # Make pane edges invisible
                ax.xaxis.pane.set_edgecolor('black')
                ax.yaxis.pane.set_edgecolor('black')
                ax.zaxis.pane.set_edgecolor('black')
                ax.xaxis.pane.set_alpha(0)
                ax.yaxis.pane.set_alpha(0)
                ax.zaxis.pane.set_alpha(0)
                
                # Remove axis lines for cleaner look
                ax.xaxis.line.set_color('black')
                ax.yaxis.line.set_color('black')
                ax.zaxis.line.set_color('black')

                # Title at top (centered, clear and prominent)
                ax.set_title('Reality Simulator Network', color='cyan', fontsize=18, fontweight='bold', pad=20)
                
                # All stats clustered around the grid area (bottom-center, integrated with grid visualization)
                orgs = state.get('organism_count', 0)
                conns = state.get('connection_count', 0)
                mod = state.get('modularity', 0)
                clust = state.get('clustering_coefficient', 0)
                path_len = state.get('average_path_length', 0)
                
                # Clustered stats box - all metrics together, positioned around grid center
                all_stats = (
                    f"ORGANISMS: {orgs}\n"
                    f"CONNECTIONS: {conns}\n"
                    f"MODULARITY: {mod:.3f}\n"
                    f"CLUSTERING: {clust:.3f}\n"
                    f"PATH LENGTH: {path_len:.2f}"
                )
                # Position stats box on left side, between Network Topology and Evolution panels
                ax.text2D(0.10, 0.50, all_stats, ha='left', va='center', color='cyan',
                         fontsize=10, family='monospace', fontweight='bold', transform=ax.transAxes,
                         bbox=dict(boxstyle='round,pad=0.7', facecolor='black', alpha=0.9, edgecolor='cyan', linewidth=2.5))

                # System label - top left corner near title (small, unobtrusive)
                ax.text2D(0.10, 0.95, 'Left Wing', ha='left', va='top', color='cyan',
                         fontsize=9, family='monospace', style='italic', transform=ax.transAxes, alpha=0.6)

                return
        except Exception as e:
            import traceback
            print(f"[VISUALIZATION] Error in 3D network render: {e}")
            traceback.print_exc()

        # Fallback: Simple text display
        try:
            ax.clear()
            ax.set_facecolor('black')
            orgs = state.get('organism_count', 0)
            conns = state.get('connection_count', 0)
            mod = state.get('modularity', 0)
            clust = state.get('clustering_coefficient', 0)
            info = f"Organisms: {orgs}\nConnections: {conns}\nModularity: {mod:.3f}\nClustering: {clust:.3f}"
            ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=12,
                    family='monospace', transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        except:
            pass

    def _update_explorer_panel(self, ax, state: Dict):
        """Update Explorer panel"""
        ax.clear()
        ax.set_facecolor('black')
        ax.set_title('Explorer (Body)', color='yellow', fontsize=14, fontweight='bold')

        # Explorer metrics
        phase = state.get('phase', 'unknown')
        vp_calcs = state.get('vp_calculations', 0)
        breath_cycle = state.get('breath_cycle', 0)
        breath_depth = state.get('breath_depth', 0)

        # Clean, informative display
        info = f"""EXPLORER SYSTEM

Phase: {phase.upper()}
VP Calculations: {vp_calcs}
Breath Cycle: {breath_cycle}
Breath Depth: {breath_depth:.3f}

Status: ACTIVE"""
        ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=11,
                family='monospace', transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    def _update_djinn_kernel_panel(self, ax, state: Dict):
        """Update Djinn Kernel panel"""
        ax.clear()
        ax.set_facecolor('black')
        ax.set_title('Djinn Kernel (Right Wing)', color='magenta', fontsize=14, fontweight='bold')

        # Djinn Kernel metrics
        vp = state.get('violation_pressure', 0)
        vp_class = state.get('vp_classification', 'unknown')
        vp_calcs = state.get('vp_calculations', 0)

        # Clean, informative display
        info = f"""DJINN KERNEL

Violation Pressure: {vp:.3f}
VP Classification: {vp_class.upper()}
VP Calculations: {vp_calcs}

Status: ACTIVE"""
        ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=11,
                family='monospace', transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')


# ============================================================================
# UNIFIED SYSTEM
# ============================================================================

class UnifiedSystem:
    """The unified butterfly system - one cohesive unit"""
    
    def __init__(self, enable_visualization: bool = True, max_cycles: int = 0,
                 highlander_config: Optional[Dict] = None):
        # Pre-flight checks (tkinter optional for headless runs)
        checker = PreFlightChecker()
        check_results = checker.run_all_checks(require_visualization=enable_visualization)
        
        if not check_results['can_start']:
            raise RuntimeError("Pre-flight checks failed. Cannot start system.")
        
        # Store Highlander config
        self.highlander_config = highlander_config
        self.highlander_protocol = None
        self.battle_arena = None
        self.capsule_manager = None
        self.germination_pool = None
        
        # Initialize logging
        self.logger = StateLogger()
        self.logger.log_state('system', {'event': 'initialization_start'})
        self.config_watcher = ConfigHotReloadWatcher(parent_path / 'config.json')
        self.active_config = self.config_watcher.get_current_config()
        
        # Initialize systems FIRST (before visualization, which needs references)
        print("\n[UNIFIED] Initializing systems...")
        
        # Explorer (body)
        if EXPLORER_AVAILABLE:
            try:
                self.controller = BiphasicController()
                if hasattr(self.controller, 'apply_runtime_config'):
                    try:
                        applied = self.controller.apply_runtime_config(self.active_config)
                        if applied:
                            print(f"[UNIFIED] [CONFIG] Applied startup config overrides: {applied}")
                    except Exception as config_err:
                        print(f"[UNIFIED] [WARN] Failed to apply startup config overrides: {config_err}")
                print("[UNIFIED] [PASS] Explorer initialized")
                self.logger.log_state('system', {'event': 'explorer_initialized'})
            except Exception as e:
                print(f"[UNIFIED] [FAIL] Explorer initialization failed: {e}")
                traceback.print_exc()
                self.controller = None
        else:
            self.controller = None
        
        # Reality Simulator (left wing) - already initialized in Explorer
        self.reality_sim = getattr(self.controller, 'reality_sim', None) if self.controller else None
        
        # Wire breath engine reference to Reality Simulator for neural training
        if self.reality_sim and self.controller and hasattr(self.controller, 'breath_engine'):
            self.reality_sim.breath_engine_ref = self.controller.breath_engine
        
        # Djinn Kernel (right wing) - already initialized in Explorer
        self.vp_monitor = getattr(self.controller, 'vp_monitor', None) if self.controller else None
        self.utm_kernel = getattr(self.controller, 'utm_kernel', None) if self.controller else None

        # Lawfold Field Architecture (civilization governance)
        if self.utm_kernel and DJINN_KERNEL_AVAILABLE:
            try:
                self.lawfold_orchestrator = LawfoldFieldOrchestrator(self.utm_kernel)
                self.lawfold_orchestrator.activate_all_fields()
                print("[UNIFIED] [PASS] Lawfold Field Architecture initialized")
                self.logger.log_state('system', {'event': 'lawfold_fields_initialized'})
            except Exception as e:
                print(f"[UNIFIED] [FAIL] Lawfold Field Architecture initialization failed: {e}")
                traceback.print_exc()
                self.lawfold_orchestrator = None
        else:
            self.lawfold_orchestrator = None

        # Initialize Causation Explorer
        try:
            from causation_explorer import CausationExplorer
            # Load config for causation detection
            config_path = Path('config.json')
            causation_config = {}
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        full_config = json.load(f)
                        causation_config = full_config
                except Exception:
                    pass
            self.causation_explorer = CausationExplorer(
                state_logger=self.logger,
                log_dir=self.logger.log_dir,
                utm_kernel=self.utm_kernel,
                config=causation_config
            )
            # Connect StateLogger to CausationExplorer
            self.logger.causation_explorer = self.causation_explorer
            print("[UNIFIED] [PASS] Causation Explorer initialized")
            self.logger.log_state('system', {'event': 'causation_explorer_initialized'})
        except ImportError as e:
            print(f"[UNIFIED] [WARN] Causation Explorer not available: {e}")
            self.causation_explorer = None
        except Exception as e:
            print(f"[UNIFIED] [WARN] Causation Explorer initialization failed: {e}")
            self.causation_explorer = None

        # Wire event emitter for neural/ML visualization (AFTER causation_explorer is initialized)
        if self.reality_sim and self.causation_explorer:
            from causation_explorer import Event
            def neural_event_emitter(event_input):
                """Emit neural/ML events to causation explorer - handles both dicts and Event objects"""
                try:
                    # Handle both Event objects and dicts
                    if isinstance(event_input, Event):
                        # Already an Event object, use it directly
                        event = event_input
                    elif isinstance(event_input, dict):
                        # Convert dict to Event object
                        event = Event(
                            timestamp=event_input.get('timestamp', time.time()),
                            component=event_input.get('component', 'unknown'),
                            event_type=event_input.get('event_type', 'unknown'),
                            data=event_input.get('data', {})
                        )
                    else:
                        # Unknown type, skip
                        return
                    
                    self.causation_explorer.add_event(event, is_historical=False)
                except Exception as e:
                    # Don't break if event emission fails, but log for debugging
                    if not hasattr(self, '_event_emitter_error_logged'):
                        print(f"[UNIFIED] [WARN] Event emission failed: {e}")
                        self._event_emitter_error_logged = True
                    pass
            
            self.reality_sim.event_emitter = neural_event_emitter

            # CRITICAL: Wire context_memory and vocabulary event emitters for language events
            # This MUST happen BEFORE any word assignments occur
            # Do this immediately after network is created, not later
            if hasattr(self.reality_sim, 'components') and 'network' in self.reality_sim.components:
                network = self.reality_sim.components['network']
                if hasattr(network, 'context_memory') and network.context_memory:
                    # Wire event_emitter immediately - this ensures word_assignment events are emitted
                    network.context_memory.event_emitter = neural_event_emitter
                    # Also wire vocabulary if it exists
                    if hasattr(network.context_memory, 'vocabulary') and network.context_memory.vocabulary:
                        network.context_memory.vocabulary.event_emitter = neural_event_emitter
                    print(f"[UNIFIED] [LANGUAGE] Wired event_emitter to context_memory (event_emitter is {'set' if neural_event_emitter else 'None'})")

            # Also wire ML event emitter on the network (clustering, anomaly, phenotype events)
            try:
                network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                if network and hasattr(network, 'ml_event_emitter'):
                    network.ml_event_emitter = neural_event_emitter  # Reuse same emitter for ML events

                    # Configure ML analyzer from config if available and enabled
                    if hasattr(network, 'configure_ml_analyzer'):
                        try:
                            config_path = Path('config.json')
                            if config_path.exists():
                                with open(config_path, 'r') as f:
                                    full_config = json.load(f)
                                    scikit_config = full_config.get('scikit', {})
                                    if scikit_config.get('enabled', False):
                                        network.configure_ml_analyzer(scikit_config)
                                        print("[UNIFIED] [PASS] 🧠 ML Analyzer configured (Scikit-learn)")
                        except Exception as e:
                            print(f"[UNIFIED] [WARN] ML Analyzer configuration failed: {e}")
                    
                    # Configure Health Monitor (Quick Win #5)
                    if hasattr(network, 'configure_health_monitor'):
                        try:
                            config_path = Path('config.json')
                            if config_path.exists():
                                with open(config_path, 'r') as f:
                                    full_config = json.load(f)
                                    health_config = full_config.get('health_monitor', {})
                                    if health_config.get('enabled', True):
                                        network.configure_health_monitor(health_config, event_emitter=neural_event_emitter)
                                        print("[UNIFIED] [PASS] ❤️ Health Monitor configured")
                        except Exception as e:
                            print(f"[UNIFIED] [WARN] Health Monitor configuration failed: {e}")
            except Exception:
                # Don't let ML wiring break initialization
                pass
        else:
            print(f"[UNIFIED] [WARN] Cannot wire event emitter - reality_sim: {bool(self.reality_sim)}, causation_explorer: {bool(self.causation_explorer)}")
            
            # Wire ML event emitter for SymbioticNetwork (clustering, anomaly, phenotype events)
            network = self.reality_sim.components.get('network')
            if network and hasattr(network, 'ml_event_emitter'):
                network.ml_event_emitter = neural_event_emitter  # Reuse same emitter
                
                # Configure ML analyzer from config if available
                if hasattr(network, 'configure_ml_analyzer'):
                    try:
                        config_path = Path('config.json')
                        if config_path.exists():
                            with open(config_path, 'r') as f:
                                full_config = json.load(f)
                                scikit_config = full_config.get('scikit', {})
                                if scikit_config.get('enabled', False):
                                    network.configure_ml_analyzer(scikit_config)
                                    print("[UNIFIED] [PASS] 🧠 ML Analyzer configured (Scikit-learn)")
                    except Exception as e:
                        print(f"[UNIFIED] [WARN] ML Analyzer configuration failed: {e}")
                
                # Configure Health Monitor (Quick Win #5)
                if hasattr(network, 'configure_health_monitor'):
                    try:
                        config_path = Path('config.json')
                        if config_path.exists():
                            with open(config_path, 'r') as f:
                                full_config = json.load(f)
                                health_config = full_config.get('health_monitor', {})
                                if health_config.get('enabled', True):
                                    network.configure_health_monitor(health_config, event_emitter=neural_event_emitter)
                                    print("[UNIFIED] [PASS] ❤️ Health Monitor configured")
                    except Exception as e:
                        print(f"[UNIFIED] [WARN] Health Monitor configuration failed: {e}")

        # Initialize Phase Sync Bridge (CRITICAL INTEGRATION!)
        if PHASE_SYNC_AVAILABLE:
            try:
                self.phase_sync_bridge = PhaseSynchronizationBridge(
                    collapse_threshold=500,
                    max_connections_per_organism=5
                )
                print("[UNIFIED] [PASS] ✨ Phase Sync Bridge initialized - COLLAPSE PREDICTION ACTIVE")
                self.logger.log_state('system', {'event': 'phase_sync_bridge_initialized', 'status': 'active'})
            except Exception as e:
                print(f"[UNIFIED] [WARN] Phase Sync Bridge initialization failed: {e}")
                self.phase_sync_bridge = None
        else:
            self.phase_sync_bridge = None
            print("[UNIFIED] [WARN] Phase Sync Bridge not available")
        
        # Initialize visualization with references to Reality Simulator components (AFTER systems are initialized)
        network_ref = getattr(self.reality_sim, 'components', {}).get('network') if self.reality_sim else None
        renderer_ref = getattr(self.reality_sim, 'components', {}).get('renderer') if self.reality_sim else None
        self.visualization = UnifiedVisualization(network_ref=network_ref, renderer_ref=renderer_ref, reality_sim_ref=self.reality_sim) if enable_visualization else None
        if self.visualization:
            self.visualization.initialize()
            self.visualization.show()
        
        # Initialize Web UI integration
        self.web_ui = None
        self._initialize_web_ui()
        
        # Initialize Highlander Protocol (if enabled)
        if self.highlander_config:
            self._initialize_highlander_protocol()
        
        self.logger.log_state('system', {'event': 'initialization_complete'})
        print("[UNIFIED] [PASS] All systems initialized\n")
        # Max cycles (0 means run indefinitely)
        self.max_cycles = int(max_cycles or 0)
    
    def _initialize_web_ui(self):
        """Initialize web UI integration with access to organism networks"""
        try:
            print("[UNIFIED] [WEB] Initializing web UI integration...")
            
            # Import web UI app directly
            import causation_web_ui
            from reality_simulator.language_system import LanguageVocabulary
            
            # Get the Flask app from the module
            self.web_ui = causation_web_ui.app

            # Share unified system with web UI for capsule management
            self.web_ui.unified_system = self

            # CRITICAL: Share CausationExplorer instance with web UI
            # This ensures events from unified_entry.py appear in the web UI
            if self.causation_explorer:
                self.web_ui.config['explorer'] = self.causation_explorer
                # Also update the web UI's explorer variable directly
                causation_web_ui.explorer = self.causation_explorer
                print("[UNIFIED] [WEB] Shared CausationExplorer instance with web UI")
            
            # Store references for butterfly chat access
            if self.reality_sim:
                # Get organism networks from the symbiotic network
                network = self.reality_sim.components.get('network')
                if network:
                    organism_networks = list(network.organisms.values()) if hasattr(network, 'organisms') else []
                    self.web_ui.config['organisms'] = organism_networks
                    # Store network reference for language data access
                    self.web_ui.config['network'] = network
                else:
                    self.web_ui.config['organisms'] = []
                    self.web_ui.config['network'] = None
                
                # Get vocabulary from context_memory (if available)
                vocabulary = None
                if network and hasattr(network, 'context_memory'):
                    context_memory = network.context_memory
                    # Use existing vocabulary if it exists and has words
                    if hasattr(context_memory, 'vocabulary') and context_memory.vocabulary:
                        # Check if vocabulary has words beyond special tokens
                        special_token_count = len(context_memory.vocabulary.word_to_id) - len([k for k in context_memory.vocabulary.word_to_id.keys() if k.startswith('<') and k.endswith('>')])
                        if context_memory.vocabulary.vocab_size > 5:  # More than just special tokens
                            vocabulary = context_memory.vocabulary
                            print(f"[UNIFIED] [WEB] Using vocabulary from context_memory ({vocabulary.vocab_size} words)")
                        else:
                            # Build vocabulary from language_anchors
                            if context_memory.language_anchors:
                                vocabulary = LanguageVocabulary()
                                words_added = vocabulary.build_from_language_anchors(
                                    language_anchors=dict(context_memory.language_anchors),
                                    node_word_associations={k: v for k, v in context_memory.node_word_associations.items()}
                                )
                                print(f"[UNIFIED] [WEB] Built vocabulary from language_anchors ({words_added} words added)")
                    else:
                        # Create new vocabulary and build from anchors
                        vocabulary = LanguageVocabulary()
                        if context_memory.language_anchors:
                            words_added = vocabulary.build_from_language_anchors(
                                language_anchors=dict(context_memory.language_anchors),
                                node_word_associations={k: v for k, v in context_memory.node_word_associations.items()}
                            )
                            print(f"[UNIFIED] [WEB] Created vocabulary from language_anchors ({words_added} words added)")
                
                # Fallback: Create empty vocabulary if no context_memory
                if vocabulary is None:
                    vocabulary = LanguageVocabulary()
                    # FIXED: Seed vocabulary with basic words to prevent empty vocabulary on first use
                    seed_words = [
                        'hello', 'hi', 'yes', 'no', 'thrive', 'struggle',
                        'connect', 'move', 'rest', 'grow', 'alone', 'together',
                        'help', 'share', 'compete', 'cooperate', 'survive', 'live',
                        'good', 'bad', 'more', 'less', 'fast', 'slow', 'strong', 'weak'
                    ]
                    for word in seed_words:
                        vocabulary.add_word(word)
                    print(f"[UNIFIED] [WEB] Created vocabulary with {len(seed_words)} seed words (will expand as organisms learn)")
                
                self.web_ui.config['vocabulary'] = vocabulary
                
                # Store event emitter for causation events
                if self.causation_explorer:
                    def event_emitter(event_data):
                        from causation_explorer import Event
                        if isinstance(event_data, dict):
                            event = Event(
                                timestamp=event_data.get('timestamp', time.time()),
                                component=event_data.get('component', 'butterfly_chat'),
                                event_type=event_data.get('event_type', 'butterfly_chat_message'),
                                data=event_data.get('data', {})
                            )
                            self.causation_explorer.add_event(event, is_historical=False)
                    
                    self.web_ui.config['event_emitter'] = event_emitter
                else:
                    self.web_ui.config['event_emitter'] = None
            
            # Start web UI in background thread (same process for app.config sharing)
            # CRITICAL: Running in same process allows Butterfly Chat to access live organisms
            import threading
            self._web_ui_proc = None
            
            # Run Flask in background thread
            web_thread = threading.Thread(
                target=lambda: self.web_ui.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True),
                daemon=True
            )
            web_thread.start()
            print("[UNIFIED] [WEB] ✅ Web UI started in background thread (same process for live organism access)")
            
            print("[UNIFIED] [WEB] 🌐 Web interface available at http://localhost:5000")
            
            # Auto-launch browser in a separate thread to avoid GIL issues
            def launch_browser():
                import requests
                # Wait for server to be ready
                for _ in range(20):
                    try:
                        r = requests.get('http://127.0.0.1:5000/health', timeout=1)
                        if r.status_code == 200:
                            break
                    except Exception:
                        pass
                    time.sleep(0.25)
                try:
                    webbrowser.open('http://localhost:5000')
                    print("[UNIFIED] [WEB] 🌐 Browser launched automatically")
                except Exception as e:
                    print(f"[UNIFIED] [WEB] Could not auto-launch browser: {e}")
            
            import threading as threading_module
            browser_thread = threading_module.Thread(target=launch_browser, daemon=True)
            browser_thread.start()
            
        except Exception as e:
            print(f"[UNIFIED] [WEB] ❌ Web UI integration failed: {e}")
            import traceback
            traceback.print_exc()
            self.web_ui = None

    def get_current_organisms(self) -> Dict[str, Any]:
        """Get current organisms from the active simulation.

        Returns:
            Dict mapping organism IDs to organism objects
        """
        organisms = {}

        # Get organisms from Reality Simulator
        if self.reality_sim and hasattr(self.reality_sim, 'organisms'):
            organisms.update(self.reality_sim.organisms)

        # If using Highlander protocol, get from there instead
        if hasattr(self, 'highlander_protocol') and self.highlander_protocol:
            # Get organisms from highlander protocol (which has active_organisms)
            if hasattr(self.highlander_protocol, 'active_organisms'):
                active_ids = set(self.highlander_protocol.active_organisms)
                # Filter to only active organisms
                organisms = {oid: org for oid, org in organisms.items() if oid in active_ids}

        return organisms

    def _update_web_ui_organisms(self):
        """Update web UI with current organism networks for Butterfly Chat.
        
        This is called every cycle to ensure Butterfly Chat always has access
        to the latest organism population, even as organisms are created/destroyed.
        """
        if not self.web_ui or not self.reality_sim:
            return
        
        try:
            network = self.reality_sim.components.get('network')
            if network and hasattr(network, 'organisms'):
                organism_networks = list(network.organisms.values())
                # Only update if organisms exist or if we had organisms before
                current_count = len(organism_networks)
                previous_count = len(self.web_ui.config.get('organisms', []))
                
                if current_count > 0 or previous_count > 0:
                    self.web_ui.config['organisms'] = organism_networks
                    # Also update network reference
                    self.web_ui.config['network'] = network
                    
                    # Log significant changes
                    if current_count != previous_count and current_count > 0:
                        if previous_count == 0:
                            print(f"[UNIFIED] [WEB] 🦋 Butterfly Chat now has {current_count} organisms available")
        except Exception:
            pass  # Silent fail - don't break main loop for web UI updates
    
    def _initialize_highlander_protocol(self):
        """Initialize the Highlander Protocol tournament system.
        
        There can be only one. Organisms compete for survival,
        absorbing the traits, knowledge, and very essence of the fallen.
        The last butterfly standing becomes the template for immortality.
        """
        try:
            print("\n[UNIFIED] [HIGHLANDER] ⚔️ Initializing Highlander Protocol...")
            print("[UNIFIED] [HIGHLANDER] 'There can be only one.'")
            
            # Import Highlander systems
            from reality_simulator.evolution.highlander_protocol import HighlanderProtocol
            from reality_simulator.evolution.battle_arena import BattleArena
            from reality_simulator.checkpointing.organism_capsule import OrganismCapsuleManager
            from reality_simulator.evolution.germination_pool import GerminationPool, integrate_germination_with_highlander
            from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem, integrate_alliance_warfare_with_highlander
            
            # Parse config
            config = self.highlander_config or {}
            population_size = config.get('population_size', 10)
            survival_threshold = config.get('survival_threshold', 0.3)
            competition_intensity = config.get('competition_intensity', 0.5)
            rounds_per_cycle = config.get('rounds_per_cycle', 1)
            
            # Create event emitter for Highlander events
            def highlander_event_emitter(event_data):
                """Emit Highlander events to causation explorer"""
                if self.causation_explorer:
                    try:
                        from causation_explorer import Event
                        event = Event(
                            timestamp=event_data.get('timestamp', time.time()),
                            component=event_data.get('component', 'highlander'),
                            event_type=event_data.get('event_type', 'highlander_event'),
                            data=event_data.get('data', {})
                        )
                        self.causation_explorer.add_event(event, is_historical=False)
                    except Exception:
                        pass
            
            # Initialize Battle Arena (combat resolution)
            arena_config = {
                'max_rounds': config.get('max_battle_rounds', 10),
                'chaos_factor': config.get('chaos_factor', 0.15)
            }
            self.battle_arena = BattleArena(
                config=arena_config,
                event_emitter=highlander_event_emitter
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] Battle Arena initialized")
            
            # Initialize Organism Capsule Manager (checkpointing)
            capsule_dir = Path('highlander_capsules')
            self.capsule_manager = OrganismCapsuleManager(
                storage_dir=capsule_dir
            )
            print(f"[UNIFIED] [HIGHLANDER] [PASS] Capsule Manager initialized (dir: {capsule_dir})")
            
            # Initialize Germination Pool (new life from the fallen)
            self.germination_pool = GerminationPool(
                causation_explorer=self.causation_explorer,
                max_genetic_samples=config.get('max_genetic_samples', 100),
                min_population=config.get('min_population', 5),
                max_population=config.get('max_population', 50),
                germination_rate=config.get('germination_rate', 0.1),
                mutation_base_rate=config.get('mutation_rate', 0.05)
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🌱 Germination Pool initialized")
            
            # Initialize Highlander Protocol (tournament orchestration)
            highlander_config = {
                'survival_threshold': survival_threshold,
                'competition_intensity': competition_intensity,
                'predation_enabled': config.get('predation_enabled', False),
                'germination_rate': config.get('germination_rate', 0.1),
                'max_population': config.get('max_population', 100),
                'min_population': config.get('min_population', 10),
                'battle_randomness': config.get('chaos_factor', 0.15)
            }
            self.highlander_protocol = HighlanderProtocol(
                config=highlander_config,
                event_emitter=highlander_event_emitter,
                capsule_manager=self.capsule_manager,
                battle_arena=self.battle_arena
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] Tournament Protocol initialized")
            
            # Register existing organisms
            network = self.reality_sim.components.get('network') if self.reality_sim else None
            if network and hasattr(network, 'organisms'):
                for org_id, organism in network.organisms.items():
                    try:
                        # Get fitness from organism
                        fitness = 0.5  # Default
                        if hasattr(organism, 'fitness'):
                            fitness = organism.fitness
                        elif hasattr(organism, 'get_fitness'):
                            fitness = organism.get_fitness()
                        
                        self.highlander_protocol.register_organism(org_id, initial_fitness=fitness)
                        print(f"[UNIFIED] [HIGHLANDER] Registered organism: {org_id}")
                    except Exception as e:
                        print(f"[UNIFIED] [HIGHLANDER] Failed to register {org_id}: {e}")
            
            # Wire Germination Pool to Highlander Protocol
            # This creates organism_factory callback for spawning new warriors
            def organism_factory(organism_id, initial_traits=None, initial_config=None):
                """Factory function to create new organisms for the tournament"""
                if network and hasattr(network, 'create_organism'):
                    return network.create_organism(
                        organism_id=organism_id,
                        traits=initial_traits,
                        config=initial_config
                    )
                return None
                
            self._germination_callback = integrate_germination_with_highlander(
                self.highlander_protocol,
                self.germination_pool,
                organism_factory
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🔗 Germination Pool wired to tournament")
            
            # ⚔️🪐 INITIALIZE ALLIANCE WARFARE SYSTEM
            # Beyond individual battles - collective warfare for existential dominance
            alliance_config = {
                'min_alliance_size': config.get('min_alliance_size', 3),
                'max_alliances': config.get('max_alliances', 10),
                'war_frequency': config.get('war_frequency', 0.3),
                'war_chaos_factor': config.get('chaos_factor', 0.15),
                'existential_war_threshold': config.get('existential_war_threshold', 0.8)
            }
            self.alliance_warfare = AllianceWarfareSystem(
                highlander_protocol=self.highlander_protocol,
                config=alliance_config,
                event_emitter=highlander_event_emitter
            )
            integrate_alliance_warfare_with_highlander(
                self.highlander_protocol,
                self.alliance_warfare,
                alliance_config
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🪐⚔️ Alliance Warfare System initialized")
            print("[UNIFIED] [HIGHLANDER] 'Beyond individual battles - collective warfare for existential dominance'")
            
            # Store config for runtime access
            self._highlander_rounds_per_cycle = rounds_per_cycle
            self._highlander_enabled = True
            
            # Store reference to network for organism access
            self._highlander_network = network
            
            print(f"[UNIFIED] [HIGHLANDER] ✅ Protocol active with {self.highlander_protocol.get_population_count()} organisms")
            print(f"[UNIFIED] [HIGHLANDER] 📊 Config: survival={survival_threshold}, intensity={competition_intensity}")
            self.logger.log_state('system', {
                'event': 'highlander_initialized',
                'population': self.highlander_protocol.get_population_count(),
                'config': config
            })
            
        except ImportError as e:
            print(f"[UNIFIED] [HIGHLANDER] ❌ Import failed: {e}")
            print("[UNIFIED] [HIGHLANDER] Highlander Protocol not available")
            self._highlander_enabled = False
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[UNIFIED] [HIGHLANDER] ❌ Initialization failed: {e}")
            self._highlander_enabled = False
            import traceback
            traceback.print_exc()
    
    def _run_highlander_round(self, cycle_count: int):
        """Run a Highlander Protocol tournament round.
        
        Each round may involve:
        - Battles between organisms (winner absorbs loser)
        - Alliance formation and betrayal
        - Predation of weak by strong
        - Champion checkpointing
        """
        try:
            # Only run tournament every N cycles
            rounds_per_cycle = getattr(self, '_highlander_rounds_per_cycle', 1)
            if cycle_count % max(1, rounds_per_cycle) != 0:
                return
            
            # Get organisms from network component
            network = getattr(self, '_highlander_network', None)
            if not network or not hasattr(network, 'organisms'):
                # Try to get network from reality_sim
                if self.reality_sim and hasattr(self.reality_sim, 'components'):
                    network = self.reality_sim.components.get('network')
                    self._highlander_network = network
            
            if not network or not hasattr(network, 'organisms'):
                return  # No organisms to battle
            
            organisms = network.organisms
            if not organisms:
                return  # Empty population
            
            # Convert to dict if needed
            if not isinstance(organisms, dict):
                organisms = {getattr(o, 'id', str(id(o))): o for o in organisms}
            
            # Define fitness getter
            def get_fitness(organism) -> float:
                if hasattr(organism, 'fitness'):
                    return organism.fitness
                if hasattr(organism, 'get_fitness'):
                    return organism.get_fitness()
                return 0.5  # Default fitness
            
            # Run one tournament round with proper arguments
            results = self.highlander_protocol.run_round(organisms, get_fitness)
            
            # Check for champion emergence
            champion = self.highlander_protocol.get_current_champion()
            if champion and self.highlander_protocol.phase.name == 'CHAMPION':
                champion_id = champion.get('id', 'unknown')
                print(f"\n⚔️ [HIGHLANDER] THE CHAMPION EMERGES: {champion_id}")
                print(f"   Stats: {champion.get('stats', {})}")
                
                # Checkpoint the champion organism
                if self.capsule_manager and champion_id in organisms:
                    champion_org = organisms[champion_id]
                    capsule = self.capsule_manager.capture_organism(
                        champion_org, 
                        reason='HIGHLANDER_CHAMPION'
                    )
                    if capsule:
                        print(f"   📦 Champion capsule saved: {capsule.capsule_id}")
            
            # Log round results
            if results:
                population = self.highlander_protocol.get_population_count()
                self.logger.log_state('highlander', {
                    'event': 'round_complete',
                    'cycle': cycle_count,
                    'phase': self.highlander_protocol.phase.name,
                    'population': population,
                    'battles': len(results.get('battles', [])),
                    'eliminations': len(results.get('eliminations', [])),
                    'alliances': len(results.get('alliances_formed', []))
                })
                
                # Print status update
                battles_count = len(results.get('battles', []))
                eliminations_count = len(results.get('eliminations', []))
                alliances_count = len(results.get('alliances_formed', []))
                
                if battles_count > 0 or eliminations_count > 0:
                    print(f"[HIGHLANDER] Round {cycle_count}: "
                          f"⚔️ {battles_count} battles, "
                          f"💀 {eliminations_count} eliminated, "
                          f"🤝 {alliances_count} alliances, "
                          f"👥 {population} remaining")
            
            # 🌱 GERMINATION - Spawn new organisms if population too low
            if hasattr(self, '_germination_callback') and self._germination_callback:
                new_organisms = self._germination_callback()
                if new_organisms:
                    print(f"[HIGHLANDER] 🌱 Germinated {len(new_organisms)} new warriors from the genetic pool")
                    
                    # Log germination
                    self.logger.log_state('highlander', {
                        'event': 'germination',
                        'cycle': cycle_count,
                        'count': len(new_organisms),
                        'ids': [getattr(o, 'id', str(id(o))) for o in new_organisms],
                        'pool_stats': self.germination_pool.get_pool_stats() if self.germination_pool else {}
                    })
            
            # ⚔️🪐 ALLIANCE WARFARE - Collective battles for existential dominance
            if hasattr(self, 'alliance_warfare') and self.alliance_warfare:
                # Define concept getter for knowledge sharing
                def get_concepts(organism):
                    if hasattr(organism, 'concepts'):
                        return list(organism.concepts)
                    if hasattr(organism, 'knowledge'):
                        return list(organism.knowledge.keys()) if isinstance(organism.knowledge, dict) else []
                    return []
                
                # Run alliance warfare round
                war_results = self.alliance_warfare.run_warfare_round(
                    organisms, get_fitness, get_concepts
                )
                
                # Log alliance warfare activity
                if war_results:
                    formations = war_results.get('formations', [])
                    wars = war_results.get('wars', [])
                    alliance_count = war_results.get('alliance_count', 0)
                    
                    if formations:
                        print(f"[ALLIANCE WAR] 🪐 {len(formations)} new planetary alliances formed!")
                    
                    if wars:
                        for war in wars:
                            print(f"[ALLIANCE WAR] ⚔️ {war.get('winner_name', 'Unknown')} defeats "
                                  f"{war.get('loser_name', 'Unknown')}! "
                                  f"Margin: {war.get('margin', 0)*100:.1f}%")
                    
                    # Check for galactic dominance
                    dominant = war_results.get('dominant_alliance')
                    if dominant:
                        print(f"[ALLIANCE WAR] 🌟🌟🌟 GALACTIC DOMINANCE ACHIEVED! 🌟🌟🌟")
                    
                    # Log to state
                    self.logger.log_state('highlander', {
                        'event': 'alliance_warfare_round',
                        'cycle': cycle_count,
                        'alliance_count': alliance_count,
                        'formations': len(formations),
                        'wars': len(wars),
                        'dominant_alliance': dominant
                    })
                          
        except Exception as e:
            print(f"[HIGHLANDER] Round error: {e}")
            import traceback
            traceback.print_exc()
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run the unified system"""
        print("="*70)
        print("[BUTTERFLY] THE BUTTERFLY SYSTEM - FLYING")
        print("="*70)
        print("Press Ctrl+C to stop\n")
        
        try:
            if not self.controller:
                print("[UNIFIED] [FAIL] Explorer not available. Cannot run.")
                return
            
            # Main loop
            cycle_count = 0
            while True:
                updated_config = self.config_watcher.check_for_updates()
                if updated_config is not None:
                    self._apply_runtime_config(updated_config)

                # Update reality sim (includes neural training and config tuner)
                if self.reality_sim:
                    try:
                        # Inject VP data from Explorer into network (Quick Win #1)
                        network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                        if network and self.controller and hasattr(self.controller, 'sentinel'):
                            try:
                                if hasattr(self.controller.sentinel, 'vp_history') and self.controller.sentinel.vp_history:
                                    latest_vp = self.controller.sentinel.vp_history[-1]
                                    if isinstance(latest_vp, dict):
                                        vp_total = latest_vp.get('total_vp')
                                        vp_components = latest_vp.get('component_breakdown', {})
                                        if hasattr(network, 'inject_vp_data'):
                                            network.inject_vp_data(vp_total=vp_total, vp_components=vp_components)
                            except Exception:
                                pass  # Don't break if VP injection fails
                        
                        self.reality_sim._update_simulation_components()
                    except Exception as e:
                        print(f"[ERROR] Reality sim update failed: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 🦋 UPDATE WEB UI ORGANISMS - Keep Butterfly Chat in sync with live organisms
                self._update_web_ui_organisms()

                # Get states from all systems
                reality_sim_state = self._get_reality_sim_state()
                explorer_state = self._get_explorer_state()
                djinn_kernel_state = self._get_djinn_kernel_state()

                # 🌉 PHASE SYNC INTEGRATION - Update network metrics and get predictions
                phase_sync_state = {}
                if self.phase_sync_bridge:
                    try:
                        # Update network metrics in phase sync bridge
                        network_data = {
                            'organism_count': reality_sim_state.get('organism_count', 0),
                            'connection_count': reality_sim_state.get('connection_count', 0),
                            'clustering_coefficient': reality_sim_state.get('clustering_coefficient', 0.0),
                            'modularity': reality_sim_state.get('modularity', 0.0),
                            'average_path_length': reality_sim_state.get('average_path_length', 0.0),
                            'connectivity': reality_sim_state.get('connection_count', 0) / max(1, reality_sim_state.get('organism_count', 1)),
                            'stability_index': 1.0 - reality_sim_state.get('modularity', 0.0)  # Rough estimate
                        }
                        collapsed = self.phase_sync_bridge.update_network_metrics(network_data)

                        # Get synchronization state
                        sync_data = self.phase_sync_bridge.synchronize_phases()
                        phase_sync_state = sync_data

                        # 🔮 COLLAPSE PREDICTION - Warn if imminent
                        will_collapse, estimated_gens = self.phase_sync_bridge.get_collapse_prediction()
                        if will_collapse and estimated_gens < 20 and estimated_gens > 0:
                            collapse_proximity = sync_data['network']['collapse_proximity']
                            warning_level = 'red' if collapse_proximity > 0.9 else ('orange' if collapse_proximity > 0.7 else 'yellow')
                            print(f"\n🔮 [{warning_level.upper()}] COLLAPSE PREDICTED IN ~{estimated_gens:.1f} GENERATIONS (proximity: {collapse_proximity:.1%})")

                        # 🌉 TRANSITION DETECTION
                        if collapsed and not getattr(self, '_collapse_announced', False):
                            print(f"\n🌉 ✨ CHAOS→PRECISION TRANSITION DETECTED ✨")
                            print(f"   Reality Sim: {sync_data['network']['organism_count']} organisms explored")
                            print(f"   Explorer: {sync_data['explorer']['vp_calculations']} VP calculations")
                            print(f"   Conversion factor: {self.phase_sync_bridge.exploration_to_precision_ratio}:1")
                            print(f"   The butterfly spreads its wings. 🦋\n")
                            self._collapse_announced = True

                    except Exception as e:
                        print(f"[UNIFIED] [WARN] Phase sync error: {e}")
                        phase_sync_state = {}

                # Get breath state for logging
                if self.controller and hasattr(self.controller, 'breath_engine'):
                    breath_state = self.controller.breath_engine.get_breath_state()
                    self.logger.log_breath(breath_state)

                # Log all states
                self.logger.log_reality_sim(reality_sim_state)
                self.logger.log_explorer(explorer_state)
                self.logger.log_djinn_kernel(djinn_kernel_state)
                
                # Log unified state snapshot (flatten nested dicts)
                unified_state = {
                    'timestamp': time.time()
                }
                # Flatten nested states with prefixes
                for key, value in reality_sim_state.items():
                    unified_state[f'reality_sim_{key}'] = value
                for key, value in explorer_state.items():
                    unified_state[f'explorer_{key}'] = value
                for key, value in djinn_kernel_state.items():
                    unified_state[f'djinn_{key}'] = value
                
                # Add neural metrics to unified state if available
                if self.reality_sim and hasattr(self.reality_sim, '_neural_metrics'):
                    neural_metrics = self.reality_sim._neural_metrics
                    for key, value in neural_metrics.items():
                        unified_state[f'neural_{key}'] = value
                    
                    # Log neural metrics to neural.log file
                    if neural_metrics.get('enabled', False):
                        self.logger.log_neural(neural_metrics)
                
                # Log ML analysis results if available
                if self.reality_sim and hasattr(self.reality_sim, '_ml_metrics'):
                    ml_metrics = self.reality_sim._ml_metrics
                    if ml_metrics and ml_metrics.get('enabled', False):
                        # Log ML metrics to neural.log (or create ml.log if needed)
                        ml_log_data = {
                            'enabled': True,
                            'organism_count': ml_metrics.get('organism_count', 0),
                            'n_clusters': ml_metrics.get('clustering', {}).get('n_clusters', 0),
                            'anomaly_count': ml_metrics.get('anomalies', {}).get('anomaly_count', 0),
                            'anomaly_ratio': f"{ml_metrics.get('anomalies', {}).get('anomaly_ratio', 0):.4f}",
                            'algorithm': ml_metrics.get('clustering', {}).get('algorithm', 'unknown')
                        }
                        self.logger.log_state('neural', ml_log_data)  # Use neural.log for now
                
                self.logger.log_state('state', unified_state)
                
                # Write unified shared state file (includes all three systems + phase sync!)
                # This is the primary source of truth for the Causation Explorer
                self._write_unified_shared_state(reality_sim_state, explorer_state, djinn_kernel_state, phase_sync_state)
                
                # Phase 2: Feed events to Causation Explorer in real-time
                if self.causation_explorer:
                    try:
                        # Load latest state from shared state file (incremental)
                        self.causation_explorer._load_from_shared_state(force_reload=False)
                    except Exception as e:
                        pass  # Don't break if event feeding fails
                
                # Update visualization
                if self.visualization and self.visualization.running:
                    self.visualization.update(reality_sim_state, explorer_state, djinn_kernel_state)
                
                # Run one breath cycle (drives everything)
                if hasattr(self.controller, 'run_genesis_phase'):
                    self.controller.run_genesis_phase()
                elif hasattr(self.controller, 'run_sovereign_phase'):
                    self.controller.run_sovereign_phase()
                
                # 🗡️ HIGHLANDER PROTOCOL - Run tournament round
                if getattr(self, '_highlander_enabled', False) and self.highlander_protocol:
                    self._run_highlander_round(cycle_count)
                
                # Small delay
                time.sleep(0.1)
                # Increment cycle counter and break if requested
                cycle_count += 1
                if self.max_cycles > 0 and cycle_count >= self.max_cycles:
                    print(f"[UNIFIED] Reached max cycles ({self.max_cycles}). Exiting loop.")
                    break
                
        except KeyboardInterrupt:
            print("\n[UNIFIED] Shutting down gracefully...")
            self.logger.log_state('system', {'event': 'shutdown'})
        except Exception as e:
            print(f"\n[UNIFIED] [FAIL] Error: {e}")
            traceback.print_exc()
            self.logger.log_state('system', {'event': 'error', 'error': str(e)})
    
    def _apply_runtime_config(self, new_config: Dict[str, Any]):
        """Apply runtime configuration updates to live subsystems."""
        if not isinstance(new_config, dict):
            return

        applied_sections = []
        try:
            if self.controller and hasattr(self.controller, 'apply_runtime_config'):
                applied = self.controller.apply_runtime_config(new_config) or []
                applied_sections.extend(applied)
            self.active_config = new_config
            summary = ', '.join(applied_sections) if applied_sections else 'no-op'
            print(f"[UNIFIED] [CONFIG] Runtime config applied ({summary})")
            self.logger.log_state('system', {
                'event': 'config_runtime_update',
                'applied': summary,
                'timestamp': time.time()
            })
        except Exception as err:
            print(f"[UNIFIED] [WARN] Runtime config update failed: {err}")
            self.logger.log_state('system', {
                'event': 'config_runtime_update_failed',
                'error': str(err)
            })
    
    def _get_reality_sim_state(self) -> Dict[str, Any]:
        """Get Reality Simulator state"""
        if not self.reality_sim or not self.reality_sim.components:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        network = self.reality_sim.components.get('network')
        if not network:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        state = {
            'organism_count': len(network.organisms),
            'connection_count': len(network.connections),
            'modularity': network.metrics.modularity if hasattr(network.metrics, 'modularity') else 0,
            'clustering_coefficient': network.metrics.clustering_coefficient if hasattr(network.metrics, 'clustering_coefficient') else 0,
            'average_path_length': network.metrics.average_path_length if hasattr(network.metrics, 'average_path_length') else 0,
            'generation': network.generation if hasattr(network, 'generation') else 0,
        }
        
        # Quick Win #5: Add Health Monitor data to shared state
        if hasattr(network, 'health_monitor') and network.health_monitor is not None:
            try:
                # Get neural stats if available
                neural_stats = None
                if hasattr(self.reality_sim, '_neural_metrics') and self.reality_sim._neural_metrics:
                    neural_stats = {
                        'training_loss': self.reality_sim._neural_metrics.get('training_loss'),
                        'avg_epsilon': self.reality_sim._neural_metrics.get('avg_epsilon', 0.0),
                        'organisms_tracked': self.reality_sim._neural_metrics.get('organisms_tracked', 0),
                        'training_steps': self.reality_sim._neural_metrics.get('training_steps', 0),
                    }
                
                # Get VP components from Explorer if available
                vp_components = None
                if self.controller and hasattr(self.controller, 'sentinel'):
                    try:
                        if hasattr(self.controller.sentinel, 'vp_history') and self.controller.sentinel.vp_history:
                            latest_vp = self.controller.sentinel.vp_history[-1]
                            if isinstance(latest_vp, dict) and 'component_breakdown' in latest_vp:
                                vp_components = latest_vp['component_breakdown']
                    except Exception:
                        pass
                
                # Compute health
                health_result = network.compute_ecosystem_health(
                    neural_stats=neural_stats,
                    vp_components=vp_components
                )
                
                # Add health data to state
                if health_result and health_result.get('enabled', False):
                    state['health'] = {
                        'health_score': health_result.get('health_score', 0.5),
                        'state': health_result.get('state', 'unknown'),
                        'components': {
                            'coherence': health_result.get('components', {}).get('coherence', 0.0),
                            'diversity': health_result.get('components', {}).get('diversity', 0.0),
                            'adaptability': health_result.get('components', {}).get('adaptability', 0.0),
                            'lawfulness': health_result.get('components', {}).get('lawfulness', 0.0),
                            'sustainability': health_result.get('components', {}).get('sustainability', 0.0),
                        }
                    }
                else:
                    # Health monitor disabled or unavailable
                    state['health'] = {
                        'health_score': 0.5,
                        'state': 'unknown',
                        'enabled': False
                    }
            except Exception as e:
                # Don't break if health calculation fails
                state['health'] = {
                    'health_score': 0.5,
                    'state': 'error',
                    'error': str(e)
                }
        else:
            # Health monitor not initialized
            state['health'] = {
                'health_score': 0.5,
                'state': 'not_initialized',
                'enabled': False
            }
        
        # Add meta-cognitive tuner status if available
        if hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
            try:
                tuner_stats = self.reality_sim.config_tuner.get_stats()
                state['meta_cognitive'] = {
                    'enabled': tuner_stats.get('enabled', False),
                    'mode': tuner_stats.get('mode', 'unknown'),
                    'total_actions': tuner_stats.get('total_actions', 0),
                    'successful_actions': tuner_stats.get('successful_actions', 0),
                    'success_rate': tuner_stats.get('success_rate', 0.0),
                }
            except Exception:
                state['meta_cognitive'] = {'enabled': False, 'mode': 'unknown'}
        else:
            state['meta_cognitive'] = {'enabled': False, 'mode': 'not_initialized'}
        
        return state
    
    def _get_explorer_state(self) -> Dict[str, Any]:
        """Get Explorer state"""
        if not self.controller:
            return {'phase': 'unknown', 'vp_calculations': 0}
        
        breath_state = self.controller.breath_engine.get_breath_state()
        
        return {
            'phase': self.controller.phase if hasattr(self.controller, 'phase') else 'unknown',
            'vp_calculations': len(self.controller.sentinel.vp_history) if hasattr(self.controller, 'sentinel') else 0,
            'sovereign_ids_count': len(self.controller.kernel.get_sovereign_ids()) if hasattr(self.controller, 'kernel') else 0,
            'breath_cycle': breath_state.get('cycle_count', 0),
            'breath_depth': breath_state.get('depth', 0),
        }
    
    def _get_djinn_kernel_state(self) -> Dict[str, Any]:
        """Get Djinn Kernel state from UTM Kernel and Akashic Ledger (tape-based)"""
        # Try UTM Kernel first (tape-based)
        if hasattr(self, 'utm_kernel') and self.utm_kernel:
            try:
                ledger = self.utm_kernel.akashic_ledger
                ledger_summary = ledger.get_ledger_summary()
                
                # Read latest VP calculation from ledger
                latest_vp = 0.0
                latest_vp_class = 'VP0'
                if ledger_summary.get('total_cells', 0) > 0:
                    # Read last few cells to find VP calculation
                    for pos in range(ledger_summary.get('next_position', 1) - 1, max(0, ledger_summary.get('next_position', 1) - 10), -1):
                        cell = ledger.read_cell(pos)
                        if cell and cell.content:
                            if 'violation_pressure' in cell.content:
                                latest_vp = cell.content.get('violation_pressure', 0.0)
                                latest_vp_class = cell.content.get('vp_classification', 'VP0')
                                break
                
                # FIX: Count actual traits from latest VP calculation in ledger
                trait_count = 0
                if ledger_summary.get('total_cells', 0) > 0:
                    for pos in range(ledger_summary.get('next_position', 1) - 1, max(0, ledger_summary.get('next_position', 1) - 10), -1):
                        cell = ledger.read_cell(pos)
                        if cell and cell.content:
                            if 'trait_payload' in cell.content:
                                trait_payload = cell.content.get('trait_payload', {})
                                trait_count = len(trait_payload) if isinstance(trait_payload, dict) else 0
                                break
                            elif 'traits' in cell.content:
                                traits = cell.content.get('traits', {})
                                trait_count = len(traits) if isinstance(traits, dict) else 0
                                break
                
                return {
                    'violation_pressure': latest_vp,
                    'vp_classification': latest_vp_class,
                    'vp_calculations': ledger_summary.get('total_cells', 0),
                    'trait_count': trait_count,  # FIX: Use actual count, not hardcoded 0
                    'tape_cells': ledger_summary.get('total_cells', 0),
                    'tape_position': ledger_summary.get('next_position', 0)
                }
            except Exception as e:
                # Fallback to VP monitor if UTM Kernel fails
                pass
        
        # Fallback to VP monitor
        if self.vp_monitor:
            vp_history = self.vp_monitor.vp_history if hasattr(self.vp_monitor, 'vp_history') else []
            if vp_history:
                recent = vp_history[-1]
                total_vp = recent.get('total_vp', 0) if isinstance(recent, dict) else (recent.vp if hasattr(recent, 'vp') else 0)
                
                # FIX: Count traits from VP history entry
                trait_count = 0
                if isinstance(recent, dict):
                    breakdown = recent.get('breakdown', {})
                    trait_count = len(breakdown) if isinstance(breakdown, dict) else 0
                
                vp_class = self.vp_monitor._classify_violation_pressure(total_vp)
                
                # Include VP diagnostic data if available
                result = {
                    'violation_pressure': total_vp,
                    'vp_classification': vp_class.value if hasattr(vp_class, 'value') else str(vp_class),
                    'vp_calculations': len(vp_history),
                    'trait_count': trait_count,  # FIX: Include trait count
                    'tape_cells': len(vp_history),
                    'tape_position': len(vp_history),
                    'vp_history': vp_history[-100:] if len(vp_history) > 100 else vp_history  # Last 100 entries
                }
                
                # Add VP diagnostics if enabled
                if self.vp_monitor.diagnostics.enabled:
                    result['vp_diagnostics'] = {'available': True, 'log_file': 'data/logs/vp_diagnostics.log'}
                
                # Add component breakdown if decomposition enabled
                if isinstance(recent, dict) and 'component_breakdown' in recent:
                    result['component_breakdown'] = recent.get('component_breakdown', {})
                
                return result
        
        # FIX: Return default with trait_count=0 explicitly (no traits = no VP calculation)
        return {'violation_pressure': 0, 'vp_classification': 'VP0', 'vp_calculations': 0, 'trait_count': 0, 'tape_cells': 0, 'tape_position': 0}
    
    def _write_unified_shared_state(self, reality_sim_state: Dict[str, Any], explorer_state: Dict[str, Any],
                                     djinn_kernel_state: Dict[str, Any], phase_sync_state: Dict[str, Any] = None):
        """
        Write unified shared state file that includes all three systems + PHASE SYNC DATA.
        This is the primary source of truth for the Causation Explorer and other viewers.

        NOW INCLUDES:
        - phase_sync: collapse prediction, phase proximity, exploration ratio, transition status
        - exploration_tracking: 10:1 ratio tracking, progress monitoring
        - unified_health: multi-system health metrics
        - transition_status: readiness of all three systems

        Uses snapshot-based approach: writes discrete state snapshots that the HTML can handle efficiently.
        Throttled to write at most once per second to reduce I/O overhead.
        """
        try:
            # Throttle writes to at most once per second (snapshots, not constant stream)
            current_time = time.time()
            if not hasattr(self, '_last_shared_state_write'):
                self._last_shared_state_write = 0
            
            # Only write if at least 1 second has passed since last write
            if current_time - self._last_shared_state_write < 1.0:
                return  # Skip this write, too soon
            
            self._last_shared_state_write = current_time
            
            shared_state_file = Path('data/.shared_simulation_state.json')
            shared_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Get frame count from Reality Simulator if available
            frame_count = 0
            if self.reality_sim and hasattr(self.reality_sim, 'frame_count'):
                frame_count = self.reality_sim.frame_count
            
            # Collect Reality Simulator data (if available from the actual simulator)
            reality_sim_data = {}
            if self.reality_sim and hasattr(self.reality_sim, '_collect_simulation_data'):
                try:
                    reality_sim_data = self.reality_sim._collect_simulation_data()
                    # Neural metrics are already included in _collect_simulation_data
                except Exception as e:
                    # Fallback to state we collected
                    reality_sim_data = {
                        'network': reality_sim_state,
                        'evolution': {},
                        'quantum': {},
                        'lattice': {},
                        'consciousness': {},
                        'neural': {}
                    }
                    # Add neural metrics if available
                    if self.reality_sim and hasattr(self.reality_sim, '_neural_metrics'):
                        reality_sim_data['neural'] = self.reality_sim._neural_metrics
            else:
                # Use state we collected
                reality_sim_data = {
                    'network': reality_sim_state,
                    'evolution': {},
                    'quantum': {},
                    'lattice': {},
                    'consciousness': {}
                }
            
            # 🌉 BUILD ENHANCED STATE DATA - Now with phase sync intelligence!
            # Create unified shared state with ALL three systems + PHASE SYNC
            unified_data = {
                **reality_sim_data,  # Reality Simulator data (quantum, lattice, evolution, network, consciousness)
                'explorer': explorer_state,  # Explorer data (phase, vp_calculations, breath_state, etc.)
                'djinn_kernel': djinn_kernel_state  # Djinn Kernel data (VP, tape cells, etc.)
            }

            # 🗣️ ADD LANGUAGE DATA for CRA/Illumination Engine
            try:
                network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                if network and hasattr(network, 'context_memory') and network.context_memory:
                    cm = network.context_memory
                    vocab = cm.vocabulary if hasattr(cm, 'vocabulary') else None
                    language_data = {
                        'vocab_size': vocab.vocab_size if vocab else 0,
                        'word_count': len(vocab.word_to_id) if vocab and hasattr(vocab, 'word_to_id') else 0,
                        'organism_word_assignments': len(cm.organism_words) if hasattr(cm, 'organism_words') else 0,
                        'language_anchors': len(cm.language_anchors) if hasattr(cm, 'language_anchors') else 0,
                        'total_associations': sum(len(v) for v in cm.language_anchors.values()) if hasattr(cm, 'language_anchors') else 0
                    }
                    unified_data['language'] = language_data
            except Exception:
                pass  # Don't break if language data extraction fails

            # ✨ ADD PHASE SYNC DATA (collapse prediction, phase proximity, exploration ratio)
            if phase_sync_state:
                unified_data['phase_sync'] = phase_sync_state

                # Build exploration tracking data for CRA
                exploration_tracking = {
                    'exploration_to_precision_ratio': 10.0,  # The fundamental 500:50 = 10:1 ratio
                    'reality_sim_explorations': phase_sync_state.get('network', {}).get('organism_count', 0),
                    'explorer_explorations': phase_sync_state.get('explorer', {}).get('vp_calculations', 0),
                    'target_ratio': '500:50',
                    'current_ratio': f"{phase_sync_state.get('network', {}).get('organism_count', 0)}:{phase_sync_state.get('explorer', {}).get('vp_calculations', 0)}",
                    'ratio_maintained': abs(phase_sync_state.get('synchronization', {}).get('proximity_difference', 1.0)) < 0.1,
                    'progress_to_transition': phase_sync_state.get('network', {}).get('collapse_proximity', 0.0)
                }
                unified_data['exploration_tracking'] = exploration_tracking

                # Build unified health metrics for CRA
                network_health = 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                
                # FIXED: Include actual Health Monitor data if available (Quick Win #5)
                health_monitor_data = reality_sim_state.get('health', {})
                if health_monitor_data and health_monitor_data.get('health_score') is not None:
                    # Use actual health monitor score
                    actual_health_score = health_monitor_data.get('health_score', 0.5)
                    unified_health = {
                        'overall_health': actual_health_score,  # Use actual health monitor score
                        'reality_sim_health': actual_health_score,  # Health Monitor score
                        'health_score': actual_health_score,  # For /api/diagnostic/unified_health compatibility
                        'state': health_monitor_data.get('state', 'unknown'),
                        'components': health_monitor_data.get('components', {}),
                        'explorer_health': min(1.0, phase_sync_state.get('explorer', {}).get('genesis_proximity', 0.0) + 0.2),
                        'djinn_kernel_health': 0.82,  # Default, could calculate from VP if available
                        'integration_health': network_health,
                        'phase_alignment_health': 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                    }
                else:
                    # Fallback to phase sync-based health
                    unified_health = {
                        'overall_health': network_health * 0.9,  # Slight penalty if not fully aligned
                        'reality_sim_health': min(1.0, phase_sync_state.get('network', {}).get('collapse_proximity', 0.0) + 0.2),
                        'health_score': min(1.0, phase_sync_state.get('network', {}).get('collapse_proximity', 0.0) + 0.2),  # For compatibility
                        'explorer_health': min(1.0, phase_sync_state.get('explorer', {}).get('genesis_proximity', 0.0) + 0.2),
                        'djinn_kernel_health': 0.82,  # Default, could calculate from VP if available
                        'integration_health': network_health,
                        'phase_alignment_health': 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                    }
                unified_data['unified_health'] = unified_health

                # Build transition status for CRA
                transition_status = {
                    'reality_sim_ready': phase_sync_state.get('network', {}).get('is_collapsed', False),
                    'explorer_ready': phase_sync_state.get('explorer', {}).get('is_ready', False),
                    'djinn_kernel_ready': djinn_kernel_state.get('violation_pressure', 1.0) < 0.25,  # VP0
                    'unified_transition_triggered': phase_sync_state.get('network', {}).get('is_collapsed', False),
                    'estimated_time_to_transition': f"~{phase_sync_state.get('network', {}).get('estimated_generations_to_collapse', float('inf')):.0f} cycles"
                }
                unified_data['transition_status'] = transition_status
            
            # Add VP monitoring configuration to shared state for CRA
            try:
                import json as json_module
                config_path = parent_path / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json_module.load(f)
                        unified_data['config'] = config  # Include full config for CRA
            except Exception as e:
                # Don't break if config read fails
                pass
            
            # Make JSON serializable
            def make_json_serializable(obj):
                """Recursively make object JSON serializable"""
                if isinstance(obj, dict):
                    return {k: make_json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                elif isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                else:
                    return str(obj)  # Convert everything else to string
            
            shared_state = {
                "frame_count": frame_count,
                "simulation_fps": 0.0,  # Could calculate if needed
                "simulation_time": round(time.time(), 6),
                "data": make_json_serializable(unified_data),
                "visualization_data": make_json_serializable(unified_data),
                "timestamp": round(time.time(), 6),
                "measurement_precision": 6
            }
            
            # Atomic write
            temp_file = shared_state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(shared_state, f, indent=2)
            
            # Atomic replace
            if os.name == 'nt':  # Windows
                if shared_state_file.exists():
                    shared_state_file.unlink()
                temp_file.rename(shared_state_file)
            else:  # Unix
                temp_file.replace(shared_state_file)
                
        except Exception as e:
            # Don't break the main loop if shared state write fails
            if not hasattr(self, '_shared_state_error_logged') or not self._shared_state_error_logged:
                print(f"[UNIFIED] [WARN] Could not write unified shared state: {e}")
                self._shared_state_error_logged = True


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Unified entry point - one command to rule them all"""
    import argparse
    
    parser = argparse.ArgumentParser(description='The Butterfly System - Unified Entry Point')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--check-only', action='store_true', help='Run pre-flight checks only')
    parser.add_argument('--max-cycles', type=int, default=0, help='Number of breath cycles to run (0 = unlimited)')
    
    # 🆕 Highlander Mode - Survival of the fittest
    parser.add_argument('--highlander', action='store_true', 
                       help='Enable Highlander Protocol - perpetual survival tournament')
    parser.add_argument('--predation', action='store_true',
                       help='Enable predator/prey mechanics in Highlander mode')
    parser.add_argument('--survival-threshold', type=float, default=0.3,
                       help='Fitness threshold for survival (default: 0.3)')
    parser.add_argument('--competition-intensity', type=float, default=0.5,
                       help='How many organisms battle per round (default: 0.5)')
    
    args = parser.parse_args()
    
    if args.check_only:
        checker = PreFlightChecker()
        # For check-only, assume visualization is required (can be overridden with --no-viz)
        checker.run_all_checks(require_visualization=not args.no_viz)
        return
    
    # Build Highlander config if enabled
    highlander_config = None
    if args.highlander:
        # Load config from config.json if available
        config_highlander = {}
        try:
            import json
            config_path = Path('config.json')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    full_config = json.load(f)
                    config_highlander = full_config.get('highlander', {})
        except Exception:
            pass  # Use defaults if config loading fails
        
        # Command line args override config file settings
        highlander_config = {
            'enabled': True,
            'survival_threshold': args.survival_threshold,
            'competition_intensity': args.competition_intensity,
            'predation_enabled': args.predation,
            # Use config file values as defaults, override with command line if specified
            'germination_rate': config_highlander.get('germination_rate', 0.1),
            'min_population': config_highlander.get('min_population', 10),
            'max_population': config_highlander.get('max_population', 100),
            'population_size': config_highlander.get('population_size', 10),
            'max_battle_rounds': config_highlander.get('max_battle_rounds', 10),
            'chaos_factor': config_highlander.get('chaos_factor', 0.15),
            'max_capsules': config_highlander.get('max_capsules', 5),
            'max_genetic_samples': config_highlander.get('max_genetic_samples', 100),
            'mutation_rate': config_highlander.get('mutation_rate', 0.05),
            'rounds_per_cycle': config_highlander.get('rounds_per_cycle', 1)
        }
        print("⚔️  HIGHLANDER MODE ACTIVATED - There can be only one!")
        if args.predation or config_highlander.get('predation_enabled', False):
            print("🦁 Predation enabled - the strong will hunt the weak")
    
    # Create and run unified system
    system = UnifiedSystem(
        enable_visualization=not args.no_viz, 
        max_cycles=args.max_cycles,
        highlander_config=highlander_config
    )
    system.run()


if __name__ == "__main__":
    main()

