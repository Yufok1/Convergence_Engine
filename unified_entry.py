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
    print(f"[UNIFIED] [WARN] Explorer not available: {e}")

try:
    from reality_simulator.main import RealitySimulator
    REALITY_SIM_AVAILABLE = True
except ImportError as e:
    REALITY_SIM_AVAILABLE = False
    print(f"[UNIFIED] [WARN] Reality Simulator not available: {e}")

try:
    # Import directly from kernel directory (not as package)
    from utm_kernel_design import UTMKernel
    from violation_pressure_calculation import ViolationMonitor
    DJINN_KERNEL_AVAILABLE = True
except ImportError as e:
    DJINN_KERNEL_AVAILABLE = False
    print(f"[UNIFIED] [WARN] Djinn Kernel not available: {e}")


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
    
    def check_dependencies(self) -> List[SystemCheck]:
        """Check all Python dependencies"""
        checks = []
        
        # Core dependencies
        deps = {
            'numpy': 'numpy',
            'networkx': 'networkx',
            'matplotlib': 'matplotlib',
            'tkinter': 'tkinter',
        }
        
        for dep_name, import_name in deps.items():
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
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all pre-flight checks"""
        print("\n" + "="*70)
        print("[BUTTERFLY] PRE-FLIGHT SYSTEM CHECKS")
        print("="*70)
        
        all_checks = []
        all_checks.extend(self.check_dependencies())
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
            'system': self._create_logger('system', 'system.log'),
        }
        
        # State tracking
        self.state_history = []
        self.max_history = 10000
        self.last_event_time = 0  # Track last event for live mode
    
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
        
        # Update last event time for live mode
        self.last_event_time = timestamp
        
        # Feed to Causation Explorer in real-time if available
        if self.causation_explorer:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=timestamp,
                    component=component,
                    event_type=state.get('event', 'state_change'),
                    data=state
                )
                self.causation_explorer.add_event(event)
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


# ============================================================================
# UNIFIED VISUALIZATION
# ============================================================================

class UnifiedVisualization:
    """Three-panel visualization: Left=Reality Sim, Middle=Explorer, Right=Djinn Kernel"""
    
    def __init__(self, network_ref=None, renderer_ref=None):
        self.root = None
        self.fig = None
        self.axes = {}
        self.running = False
        self._network_ref = network_ref  # Reference to Reality Simulator network
        self._renderer_ref = renderer_ref  # Reference to Reality Simulator renderer
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
            self.root.geometry("1920x1080")

            # Create figure with 3D network graph - make left panel dominant (60% width)
            from mpl_toolkits.mplot3d import Axes3D
            import matplotlib.gridspec as gridspec
            self.fig = plt.figure(figsize=(19.2, 10.8), facecolor='black')
            
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
            self._update_reality_sim_panel(self.axes['left'], self._last_reality_sim_state)
            if self.canvas:
                self.canvas.draw()


    def update(self, reality_sim_state: Dict, explorer_state: Dict, djinn_kernel_state: Dict):
        """Update all three panels"""
        if not self.running:
            return

        try:
            import matplotlib.pyplot as plt

            # Left panel: Reality Simulator 3D Network
            self._last_reality_sim_state = reality_sim_state  # Store for grid toggle redraw
            self._update_reality_sim_panel(self.axes['left'], reality_sim_state)

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
    
    def _update_reality_sim_panel(self, ax, state: Dict):
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

                # Build network data dict with actual graph edges
                network_data = {
                    'network': {
                        'organisms': state.get('organism_count', 0),
                        'connections': state.get('connection_count', 0),
                        'graph_edges': []
                    }
                }

                # Get actual graph edges if network is available
                if network and hasattr(network, 'network_graph'):
                    G = network.network_graph
                    # Convert node IDs to integers for the viewer (it expects integer nodes)
                    node_map = {node: i for i, node in enumerate(G.nodes())}
                    network_data['network']['graph_edges'] = [(node_map[u], node_map[v]) for u, v in G.edges()]

                # Combine data
                viz_data = {
                    'network': network_data.get('network', {})
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

                # Render using the existing 3D method
                self._viewer.render_network_graph(viz_data, ax)

                # Clear any text overlays from the viewer (we'll add our own organized layout)
                # Remove all text2D elements that the viewer may have added
                for text_obj in ax.texts:
                    if hasattr(text_obj, 'get_position'):
                        text_obj.remove()

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
                # Position stats box bottom-center, clustered around the grid visualization
                ax.text2D(0.5, 0.12, all_stats, ha='center', va='bottom', color='cyan',
                         fontsize=11, family='monospace', fontweight='bold', transform=ax.transAxes,
                         bbox=dict(boxstyle='round,pad=0.8', facecolor='black', alpha=0.9, edgecolor='cyan', linewidth=2.5))
                
                # System label - bottom right (small, unobtrusive)
                ax.text2D(0.98, 0.02, 'Left Wing', ha='right', va='bottom', color='cyan',
                         fontsize=10, family='monospace', style='italic', transform=ax.transAxes, alpha=0.7)

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
    
    def __init__(self, enable_visualization: bool = True):
        # Pre-flight checks
        checker = PreFlightChecker()
        check_results = checker.run_all_checks()
        
        if not check_results['can_start']:
            raise RuntimeError("Pre-flight checks failed. Cannot start system.")
        
        # Initialize logging
        self.logger = StateLogger()
        self.logger.log_state('system', {'event': 'initialization_start'})
        
        # Initialize systems FIRST (before visualization, which needs references)
        print("\n[UNIFIED] Initializing systems...")
        
        # Explorer (body)
        if EXPLORER_AVAILABLE:
            try:
                self.controller = BiphasicController()
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
        
        # Djinn Kernel (right wing) - already initialized in Explorer
        self.vp_monitor = getattr(self.controller, 'vp_monitor', None) if self.controller else None
        self.utm_kernel = getattr(self.controller, 'utm_kernel', None) if self.controller else None
        
        # Initialize Causation Explorer (Phase 2: Live Mode Integration)
        try:
            from causation_explorer import CausationExplorer
            self.causation_explorer = CausationExplorer(
                state_logger=self.logger,
                log_dir=self.logger.log_dir,
                utm_kernel=self.utm_kernel
            )
            # Connect StateLogger to CausationExplorer for live event tracking
            self.logger.causation_explorer = self.causation_explorer
            print("[UNIFIED] [PASS] Causation Explorer initialized (Live Mode Enabled)")
            self.logger.log_state('system', {'event': 'causation_explorer_initialized'})
        except ImportError as e:
            print(f"[UNIFIED] [WARN] Causation Explorer not available: {e}")
            self.causation_explorer = None
        except Exception as e:
            print(f"[UNIFIED] [WARN] Causation Explorer initialization failed: {e}")
            self.causation_explorer = None
        
        # Initialize visualization with references to Reality Simulator components (AFTER systems are initialized)
        network_ref = getattr(self.reality_sim, 'components', {}).get('network') if self.reality_sim else None
        renderer_ref = getattr(self.reality_sim, 'components', {}).get('renderer') if self.reality_sim else None
        self.visualization = UnifiedVisualization(network_ref=network_ref, renderer_ref=renderer_ref) if enable_visualization else None
        if self.visualization:
            self.visualization.initialize()
        
        self.logger.log_state('system', {'event': 'initialization_complete'})
        print("[UNIFIED] [PASS] All systems initialized\n")
    
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
            while True:
                # Get states from all systems
                reality_sim_state = self._get_reality_sim_state()
                explorer_state = self._get_explorer_state()
                djinn_kernel_state = self._get_djinn_kernel_state()
                
                # Log all states
                self.logger.log_reality_sim(reality_sim_state)
                self.logger.log_explorer(explorer_state)
                self.logger.log_djinn_kernel(djinn_kernel_state)
                
                # Update visualization
                if self.visualization and self.visualization.running:
                    self.visualization.update(reality_sim_state, explorer_state, djinn_kernel_state)
                
                # Run one breath cycle (drives everything)
                if hasattr(self.controller, 'run_genesis_phase'):
                    self.controller.run_genesis_phase()
                elif hasattr(self.controller, 'run_sovereign_phase'):
                    self.controller.run_sovereign_phase()
                
                # Small delay
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n[UNIFIED] Shutting down gracefully...")
            self.logger.log_state('system', {'event': 'shutdown'})
        except Exception as e:
            print(f"\n[UNIFIED] [FAIL] Error: {e}")
            traceback.print_exc()
            self.logger.log_state('system', {'event': 'error', 'error': str(e)})
    
    def _get_reality_sim_state(self) -> Dict[str, Any]:
        """Get Reality Simulator state"""
        if not self.reality_sim or not self.reality_sim.components:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        network = self.reality_sim.components.get('network')
        if not network:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        return {
            'organism_count': len(network.organisms),
            'connection_count': len(network.connections),
            'modularity': network.metrics.modularity if hasattr(network.metrics, 'modularity') else 0,
            'clustering_coefficient': network.metrics.clustering_coefficient if hasattr(network.metrics, 'clustering_coefficient') else 0,
            'average_path_length': network.metrics.average_path_length if hasattr(network.metrics, 'average_path_length') else 0,
            'generation': network.generation if hasattr(network, 'generation') else 0,
        }
    
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
                
                return {
                    'violation_pressure': latest_vp,
                    'vp_classification': latest_vp_class,
                    'vp_calculations': ledger_summary.get('total_cells', 0),
                    'trait_count': 0,
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
                vp_class = self.vp_monitor._classify_violation_pressure(total_vp)
                return {
                    'violation_pressure': total_vp,
                    'vp_classification': vp_class.value if hasattr(vp_class, 'value') else str(vp_class),
                    'vp_calculations': len(vp_history),
                }
        
        return {'violation_pressure': 0, 'vp_classification': 'VP0', 'vp_calculations': 0}


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Unified entry point - one command to rule them all"""
    import argparse
    
    parser = argparse.ArgumentParser(description='The Butterfly System - Unified Entry Point')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--check-only', action='store_true', help='Run pre-flight checks only')
    
    args = parser.parse_args()
    
    if args.check_only:
        checker = PreFlightChecker()
        checker.run_all_checks()
        return
    
    # Create and run unified system
    system = UnifiedSystem(enable_visualization=not args.no_viz)
    system.run()


if __name__ == "__main__":
    main()

