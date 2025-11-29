"""
🎨 LIGHTWEIGHT VISUALIZATION VIEWER

This is a separate lightweight process that ONLY displays visualizations.
All computation happens in the backend - this just reads snapshots and displays them.

This dramatically reduces CPU usage because:
- No simulation computation
- No data processing
- Only matplotlib display updates
- Updates at a lower rate (e.g., every 2-5 frames)
"""

import time
import json
import os
import sys
from typing import Dict, Any, Optional, List
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.gridspec as gridspec
from matplotlib import colors as mcolors
import numpy as np
import tkinter as tk
from tkinter import ttk

# Import visualization modules (but they'll only render, not compute)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_project_root():
    """
    Get the project root directory robustly.
    
    Uses multiple detection methods in order of reliability:
    1. Looks for marker files (config.json, .git, README.md) starting from script location
    2. Falls back to corrected path calculation (1 level up from reality_simulator/)
    3. Caches result for performance
    
    Returns:
        str: Absolute path to project root directory
    """
    # Check cache first (performance optimization)
    if hasattr(get_project_root, '_cached_root'):
        return get_project_root._cached_root
    
    # Get current script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # reality_sim_dir = reality_simulator/ directory
    reality_sim_dir = os.path.dirname(script_dir)
    # For reality_simulator/visualization_viewer.py, the project root is reality_sim_dir's parent
    # But we check multiple levels to be robust
    
    marker_files = ['config.json', '.git', 'README.md', 'requirements.txt', 'LICENSE']
    
    # Method 1: Check reality_sim_dir's parent (most common case)
    # If script is at reality_simulator/visualization_viewer.py, project root is parent of reality_simulator/
    potential_root = os.path.dirname(reality_sim_dir)
    for marker in marker_files:
        marker_path = os.path.join(potential_root, marker)
        if os.path.exists(marker_path):
            # Found marker file - this is the project root
            get_project_root._cached_root = potential_root
            return potential_root
    
    # Method 2: Check reality_sim_dir itself (if config.json is in reality_simulator/)
    for marker in marker_files:
        marker_path = os.path.join(reality_sim_dir, marker)
        if os.path.exists(marker_path):
            get_project_root._cached_root = reality_sim_dir
            return reality_sim_dir
    
    # Method 3: Check potential_root's parent (if nested deeper)
    parent_of_potential = os.path.dirname(potential_root)
    for marker in marker_files:
        marker_path = os.path.join(parent_of_potential, marker)
        if os.path.exists(marker_path):
            get_project_root._cached_root = parent_of_potential
            return parent_of_potential
    
    # Method 4: Last resort - use potential_root (corrected: only 1 level up, not 2)
    # This matches the corrected calculation
    if os.path.exists(potential_root):
        get_project_root._cached_root = potential_root
        return potential_root
    
    # Method 5: Ultimate fallback
    get_project_root._cached_root = reality_sim_dir
    return reality_sim_dir


def read_visualization_data() -> Optional[Dict[str, Any]]:
    """Read visualization data from shared state file"""
    try:
        project_root = get_project_root()
        shared_state_file = os.path.join(project_root, "data", ".shared_simulation_state.json")

        print(f"[Viewer] Checking for file at: {shared_state_file}")

        if os.path.exists(shared_state_file):
            print(f"[Viewer] File exists, reading...")
            with open(shared_state_file, 'r') as f:
                shared_state = json.load(f)

            timestamp = shared_state.get('timestamp', 0)
            age = time.time() - timestamp
            print(f"[Viewer] File timestamp: {timestamp}, age: {age:.1f}s")

            has_viz_data = 'visualization_data' in shared_state
            has_data = 'data' in shared_state
            print(f"[Viewer] Has visualization_data: {has_viz_data}, has data: {has_data}")

            # Check if data is recent (within last 60 seconds)
            if age < 60.0:  # Accept data up to 60 seconds old
                result = shared_state.get('visualization_data', shared_state.get('data', {}))
                print(f"[Viewer] Returning data with {len(result)} keys: {list(result.keys())}")
                return result
            else:
                print(f"[Viewer] Data too old (age: {age:.1f}s > 60s)")
        else:
            print(f"[Viewer] File does not exist")

        return None
    except Exception as e:
        print(f"[Viewer] Error reading visualization data: {e}")
        import traceback
        traceback.print_exc()
        return None


class LightweightVisualizationViewer:
    """Lightweight viewer that only displays pre-computed data"""
    
    def __init__(self, update_interval: float = 0.5, precision_config: Dict[str, float] = None):
        """
        Args:
            update_interval: How often to update visualizations (seconds)
            precision_config: Dictionary of precision values for different metrics
        """
        self.update_interval = update_interval
        self.last_update = 0
        self.root = None
        self.notebook = None
        self.tab_figures = {}  # Store figures for each tab
        self.tab_axes = {}     # Store axes for each tab
        self.tab_canvases = {} # Store canvas widgets for each tab
        self.tab_frames = {}
        self.active_visualizations = [
            "network_graph", "evolution_tree", "consciousness_gauge",
            "performance_monitor", "particle_cloud"
        ]
        self.network_layout_cache = {}  # Cache network layouts to prevent jumping
        self.grid_profiles = self._build_grid_profiles()
        self.current_grid_profile_index = 0
        self.grid_profile_button = None
        self.last_visualization_data: Optional[Dict[str, Any]] = None
        self.max_edges_to_plot = 2500
        self.max_particles_to_plot = 1200

        # Load precision configuration
        self.precision_config = precision_config or {
            'fitness': 0.000001,
            'consciousness': 0.000001,
            'performance_cpu': 0.0001,
            'performance_fps': 10
        }

        plt.ion()  # Interactive mode
    
    def _build_grid_profiles(self) -> List[Dict[str, Any]]:
        """Define grid styling/metric profiles for the network graph."""
        return [
            {
                "name": "Topology Matrix",
                "description": "Connectivity & clustering emphasis",
                "axis_color": "#00d1ff",
                "grid_color": "#0094cc",
                "pane_color": "#00141d",
                "pane_alpha": 0.7,
                "grid_alpha": 0.25,
                "plane_color": "#004466",
                "plane_alpha": 0.18,
                "grid_lines": 6,
                "metrics": [
                    {"label": "Connectivity", "path": "network.connectivity", "format": ".2f"},
                    {"label": "Avg Degree", "path": "derived.avg_degree", "format": ".2f"},
                    {"label": "Clustering", "path": "derived.clustering", "format": ".2f"}
                ]
            },
            {
                "name": "Stability Field",
                "description": "Network stability & Phi alignment",
                "axis_color": "#56f39a",
                "grid_color": "#50c878",
                "pane_color": "#0b1a12",
                "pane_alpha": 0.75,
                "grid_alpha": 0.3,
                "plane_color": "#1f4d2f",
                "plane_alpha": 0.22,
                "grid_lines": 5,
                "metrics": [
                    {"label": "Stability", "path": "network.stability", "format": ".2f"},
                    {"label": "Phi Score", "path": "consciousness.last_analysis.overall_score", "format": ".2f"},
                    {"label": "Emergence", "path": "consciousness.last_analysis.metrics.emergence_confidence", "format": ".2f"}
                ]
            },
            {
                "name": "Agency Flow",
                "description": "Language integration & feedback",
                "axis_color": "#ff5fd1",
                "grid_color": "#c441ff",
                "pane_color": "#190018",
                "pane_alpha": 0.65,
                "grid_alpha": 0.35,
                "plane_color": "#3b003a",
                "plane_alpha": 0.2,
                "grid_lines": 5,
                "metrics": [
                    {"label": "Language %", "path": "derived.language_ratio", "format": ".1%"},
                    {"label": "Connections", "path": "derived.connections", "format": ".0f"},
                    {"label": "Organisms", "path": "derived.organisms", "format": ".0f"}
                ]
            }
        ]
        
    def create_unified_window(self):
        """Create tabbed visualization window"""
        try:
            if len(self.active_visualizations) == 0:
                return
            
            # Create main tkinter window
            self.root = tk.Tk()
            self.root.title("Reality Simulator - Live Metrics")
            self.root.geometry("600x600")  # Square window, 50% smaller than original
            
            # Create notebook for tabs
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create a tab and figure for each visualization
            for viz_name in self.active_visualizations:
                # Create tab frame
                tab_frame = ttk.Frame(self.notebook)
                
                # Create matplotlib figure for this tab (reduced size, square format)
                fig = plt.Figure(figsize=(6, 6), facecolor='black')
                ax = fig.add_subplot(111)
                
                # Store figure and axes
                self.tab_figures[viz_name] = fig
                self.tab_axes[viz_name] = ax
                self.tab_frames[viz_name] = tab_frame
                
                # Embed figure in tkinter frame
                canvas = FigureCanvasTkAgg(fig, tab_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add toolbar for navigation (zoom, pan, etc.)
                toolbar = NavigationToolbar2Tk(canvas, tab_frame)
                toolbar.update()
                
                # Store canvas
                self.tab_canvases[viz_name] = canvas
                
                # Add tab with friendly name
                tab_label = viz_name.replace('_', ' ').title()
                self.notebook.add(tab_frame, text=tab_label)

                if viz_name == "network_graph":
                    self._create_grid_profile_button(tab_frame)
            
            print("[Viewer] ✅ Created tabbed visualization window")
            
        except Exception as e:
            print(f"[Viewer] ❌ Error creating window: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_grid_profile_button(self, tab_frame):
        """Place the grid profile cycle button on the network tab."""
        if not self.grid_profiles:
            return
        button = tk.Button(
            tab_frame,
            text=self._grid_button_text(),
            command=self.cycle_grid_profile,
            bg="#050505",
            fg="white",
            activebackground="#1a1a1a",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )
        button.place(relx=0.02, rely=0.98, anchor='sw')
        self.grid_profile_button = button
    
    def _grid_button_text(self) -> str:
        if not self.grid_profiles:
            return "Grid Profiles"
        profile = self.grid_profiles[self.current_grid_profile_index]
        return f"Grid: {profile['name']}"
    
    def cycle_grid_profile(self):
        """Cycle through available grid profiles and refresh the network view."""
        if not self.grid_profiles:
            return
        self.current_grid_profile_index = (self.current_grid_profile_index + 1) % len(self.grid_profiles)
        if self.grid_profile_button:
            self.grid_profile_button.config(text=self._grid_button_text())
        if self.last_visualization_data and "network_graph" in self.tab_axes:
            self.render_network_graph(self.last_visualization_data, self.tab_axes["network_graph"])
            if "network_graph" in self.tab_canvases:
                self.tab_canvases["network_graph"].draw()
    
    def _apply_grid_profile(self, ax, profile: Dict[str, Any]):
        """Apply axis/grid styling based on the active profile."""
        if not profile or getattr(ax, 'name', '') != '3d':
            return
        pane_color = profile.get("pane_color", "#000000")
        pane_alpha = profile.get("pane_alpha", 0.6)
        grid_color = profile.get("grid_color", "#444444")
        axis_color = profile.get("axis_color", "#ffffff")
        grid_alpha = profile.get("grid_alpha", 0.2)

        pane_rgba = mcolors.to_rgba(pane_color, pane_alpha)
        # Matplotlib changed attributes from w_xaxis→xaxis; support both.
        axes = []
        for attr in ("w_xaxis", "xaxis"):
            axis = getattr(ax, attr, None)
            if axis:
                axes.append(axis)
                break
        for attr in ("w_yaxis", "yaxis"):
            axis = getattr(ax, attr, None)
            if axis:
                axes.append(axis)
                break
        for attr in ("w_zaxis", "zaxis"):
            axis = getattr(ax, attr, None)
            if axis:
                axes.append(axis)
                break

        for axis in axes:
            setter = getattr(axis, "set_pane_color", None)
            if callable(setter):
                setter(pane_rgba)
            if hasattr(axis, "line"):
                axis.line.set_color(axis_color)
            axinfo = getattr(axis, "_axinfo", None)
            if axinfo and "grid" in axinfo:
                axinfo["grid"]["color"] = grid_color
                axinfo["grid"]["alpha"] = grid_alpha

    def _draw_profile_label(self, ax, profile: Dict[str, Any], data: Dict[str, Any], derived: Dict[str, Any]):
        """Render profile-specific metric labels."""
        if not profile:
            return
        lines = [f"{profile['name']} Grid"]
        description = profile.get("description")
        if description:
            lines.append(description)
        for metric in profile.get("metrics", []):
            label = metric.get("label", "Metric")
            path = metric.get("path", "")
            fmt = metric.get("format", ".2f")
            value = self._get_metric_value(data, path, derived, default=0.0)
            formatted = self._format_metric(value, fmt)
            lines.append(f"{label}: {formatted}")

        ax.text2D(
            0.02,
            0.02,
            "\n".join(lines),
            transform=ax.transAxes,
            ha='left',
            va='bottom',
            fontsize=8,
            color='white',
            bbox=dict(facecolor='black', alpha=0.45, edgecolor='white', linewidth=0.5)
        )

    def _get_metric_value(self, data: Dict[str, Any], path: str, derived: Dict[str, Any], default: float = 0.0):
        """Fetch nested metric using dotted path with derived overrides."""
        if not path:
            return default
        if path.startswith("derived."):
            key = path.split(".", 1)[1]
            return derived.get(key, default)
        value = data
        for part in path.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default
        if isinstance(value, (int, float, np.number)):
            return float(value)
        try:
            return float(value)
        except Exception:
            return default

    def _format_metric(self, value, fmt: str):
        """Format metric values with graceful fallback."""
        try:
            return format(value, fmt)
        except Exception:
            return str(value)

    def _draw_profile_planes(self, ax, profile: Dict[str, Any], xs: list, ys: list, zs: list):
        """Render subtle grid planes for depth/contrast."""
        if not profile or not xs:
            return
        plane_color = profile.get("plane_color", "#333333")
        plane_alpha = profile.get("plane_alpha", 0.15)
        grid_lines = max(3, int(profile.get("grid_lines", 5)))

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        z_min, z_max = min(zs), max(zs)

        x_vals = np.linspace(x_min, x_max, grid_lines)
        y_vals = np.linspace(y_min, y_max, grid_lines)
        z_vals = np.linspace(z_min, z_max, grid_lines)

        # XY plane at lowest Z
        z_level = z_min - (z_max - z_min) * 0.05
        for x in x_vals:
            ax.plot([x, x], [y_min, y_max], [z_level, z_level], color=plane_color, alpha=plane_alpha, linewidth=0.8)
        for y in y_vals:
            ax.plot([x_min, x_max], [y, y], [z_level, z_level], color=plane_color, alpha=plane_alpha, linewidth=0.8)

        # YZ plane at min X
        x_level = x_min - (x_max - x_min) * 0.05
        for y in y_vals:
            ax.plot([x_level, x_level], [y, y], [z_min, z_max], color=plane_color, alpha=plane_alpha * 0.9, linewidth=0.8)
        for z in z_vals:
            ax.plot([x_level, x_level], [y_min, y_max], [z, z], color=plane_color, alpha=plane_alpha * 0.9, linewidth=0.8)

        # XZ plane at max Y
        y_level = y_max + (y_max - y_min) * 0.05
        for x in x_vals:
            ax.plot([x, x], [y_level, y_level], [z_min, z_max], color=plane_color, alpha=plane_alpha * 0.8, linewidth=0.8)
        for z in z_vals:
            ax.plot([x_min, x_max], [y_level, y_level], [z, z], color=plane_color, alpha=plane_alpha * 0.8, linewidth=0.8)
    
    def render_network_graph(self, data: Dict[str, Any], ax):
        """Render network graph in interactive 3D with cached layout"""
        try:
            import networkx as nx
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - ensures 3D support

            # Ensure 3D axes for interactive rotation
            if getattr(ax, 'name', '') != '3d':
                fig = ax.figure
                try:
                    fig.delaxes(ax)
                except Exception:
                    pass
                ax = fig.add_subplot(111, projection='3d')
                self.tab_axes["network_graph"] = ax

            ax.cla()
            ax.set_facecolor('black')

            network_data = data.get("network", {})
            network_info = network_data.get("network", {})
            num_orgs = network_info.get("organisms", 0)
            num_conns = network_info.get("connections", 0)

            if num_orgs > 0 and num_conns > 0:
                # Reconstruct graph
                G = nx.Graph()
                for i in range(num_orgs):
                    G.add_node(i)

                graph_edges = network_info.get('graph_edges', [])
                if graph_edges and len(graph_edges) > self.max_edges_to_plot:
                    graph_edges = graph_edges[:self.max_edges_to_plot]
                if graph_edges:
                    for edge in graph_edges:
                        if len(edge) >= 2:
                            G.add_edge(edge[0], edge[1])
                else:
                    if num_conns > 0:
                        # Ring + a few random edges
                        for i in range(num_orgs):
                            G.add_edge(i, (i + 1) % num_orgs)
                        import random
                        random.seed(42)
                        added = num_orgs
                        while added < num_conns and added < num_orgs * 2:
                            n1, n2 = random.sample(range(num_orgs), 2)
                            if not G.has_edge(n1, n2):
                                G.add_edge(n1, n2)
                                added += 1

                if len(G.nodes()) > 0:
                    # Cache 3D layout (prevents recompute & lag)
                    graph_key = ("3d", num_orgs, num_conns, tuple(sorted(G.edges())))
                    if graph_key not in self.network_layout_cache:
                        pos = nx.spring_layout(G, dim=3, k=1.2, iterations=50, seed=42)
                        self.network_layout_cache[graph_key] = pos
                    else:
                        pos = self.network_layout_cache[graph_key]

                    # Extract coordinates
                    xs = []
                    ys = []
                    zs = []
                    for n in G.nodes():
                        p = pos[n]
                        xs.append(p[0])
                        ys.append(p[1])
                        zs.append(p[2])

                    # Node colors (placeholder)
                    node_colors = [0.5 + 0.3 * (i % 3) / 3.0 for i in G.nodes()]

                    # Draw network (3D, interactive)
                    ax.scatter(xs, ys, zs, c=node_colors, cmap='plasma', s=20, alpha=0.9, edgecolors='white', linewidths=0.2)

                    # Draw edges
                    for i, j in G.edges():
                        p1, p2 = pos[i], pos[j]
                        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color='cyan', alpha=0.5, linewidth=0.7)

                    ax.set_title(f'Network Graph (3D) - {num_orgs} Organisms, {num_conns} Connections',
                                 fontsize=12, fontweight='bold', color='white', pad=10)
                    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
                    ax.set_box_aspect((1, 1, 1))  # Equal aspect

                    # Overlay key indicators (quantifies the plot)
                    try:
                        avg_deg = (2 * len(G.edges())) / max(1, len(G.nodes()))
                        clustering = nx.average_clustering(G)
                    except Exception:
                        avg_deg, clustering = 0.0, 0.0
                    language_connections = network_info.get('language_connections', 0)
                    language_ratio = (language_connections / max(1, len(G.edges()))) if len(G.edges()) else 0.0

                    # ==================================================================
                    # COMPREHENSIVE DIAGNOSTIC PANELS (utilizing empty space)
                    # ==================================================================

                    # Panel 1: TOP-LEFT - Network Topology Metrics
                    stability = network_data.get('stability', 0.0)
                    connectivity = network_data.get('connectivity', 0.0)
                    panel1_text = (
                        f"━━━ NETWORK TOPOLOGY ━━━\n"
                        f"Nodes: {len(G.nodes())}\n"
                        f"Edges: {len(G.edges())}\n"
                        f"Avg Degree: {avg_deg:.2f}\n"
                        f"Clustering: {clustering:.3f}\n"
                        f"Stability: {stability:.3f}\n"
                        f"Connectivity: {connectivity:.3f}"
                    )
                    ax.text2D(0.10, 0.90, panel1_text, transform=ax.transAxes,
                              ha='left', va='top', fontsize=8, color='cyan',
                              bbox=dict(facecolor='black', alpha=0.7, edgecolor='cyan', linewidth=1),
                              family='monospace')

                    # Panel 2: TOP-RIGHT - Neural & ML Insights
                    neural_data = data.get('neural', {})
                    ml_data = data.get('ml', {})
                    neural_enabled = neural_data.get('enabled', False)
                    ml_enabled = ml_data.get('enabled', False)

                    panel2_lines = ["━━━ NEURAL & ML ━━━"]
                    if neural_enabled:
                        # Check for error state first
                        if 'error' in neural_data:
                            error_msg = neural_data['error']
                            # Truncate long error messages
                            if len(error_msg) > 40:
                                error_msg = error_msg[:37] + "..."
                            panel2_lines.extend([
                                f"🧠 Neural: ERROR",
                                f"{error_msg}"
                            ])
                        else:
                            training_loss = neural_data.get('training_loss', 0.0)
                            epsilon = neural_data.get('avg_epsilon', neural_data.get('epsilon', 0.0))
                            organisms_tracked = neural_data.get('organisms_tracked', 0)
                            training_steps = neural_data.get('training_steps', 0)

                            # Handle None values properly
                            loss_str = f"{training_loss:.4f}" if training_loss is not None else "N/A"
                            epsilon_val = epsilon if epsilon is not None else 0.0

                            panel2_lines.extend([
                                f"🧠 Neural: ACTIVE",
                                f"Loss: {loss_str}",
                                f"Epsilon: {epsilon_val:.3f}",
                                f"Tracked: {organisms_tracked}",
                                f"Steps: {training_steps}"
                            ])
                    else:
                        panel2_lines.append("🧠 Neural: OFF")

                    if ml_enabled:
                        clustering = ml_data.get('clustering', {})
                        anomalies = ml_data.get('anomalies', {})
                        n_clusters = clustering.get('n_clusters', 0)
                        anomaly_ratio = anomalies.get('anomaly_ratio', 0.0)
                        panel2_lines.extend([
                            f"🔬 ML: ACTIVE",
                            f"Clusters: {n_clusters}",
                            f"Anomalies: {anomaly_ratio:.1%}"
                        ])
                    else:
                        panel2_lines.append("🔬 ML: OFF")

                    panel2_text = "\n".join(panel2_lines)
                    ax.text2D(0.90, 0.90, panel2_text, transform=ax.transAxes,
                              ha='right', va='top', fontsize=8, color='magenta',
                              bbox=dict(facecolor='black', alpha=0.7, edgecolor='magenta', linewidth=1),
                              family='monospace')

                    # Panel 3: BOTTOM-LEFT - Evolution & VP Metrics
                    evolution_data = data.get('evolution', {})
                    generation = evolution_data.get('generation', 0)
                    best_fitness = evolution_data.get('best_fitness', 0.0)
                    avg_fitness = evolution_data.get('avg_fitness', 0.0)
                    population_size = evolution_data.get('population_size', 0)

                    # Get VP data from djinn_kernel (correct location in unified_entry structure)
                    djinn_kernel_data = data.get('djinn_kernel', {})
                    vp_value = djinn_kernel_data.get('violation_pressure', 0.0)
                    vp_classification = djinn_kernel_data.get('vp_classification', 'VP0')

                    panel3_text = (
                        f"━━━ EVOLUTION & VP ━━━\n"
                        f"Generation: {generation}\n"
                        f"Population: {population_size}\n"
                        f"Best Fitness: {best_fitness:.4f}\n"
                        f"Avg Fitness: {avg_fitness:.4f}\n"
                        f"VP: {vp_value:.4f}\n"
                        f"Class: {vp_classification}"
                    )
                    ax.text2D(0.10, 0.10, panel3_text, transform=ax.transAxes,
                              ha='left', va='bottom', fontsize=8, color='lime',
                              bbox=dict(facecolor='black', alpha=0.7, edgecolor='lime', linewidth=1),
                              family='monospace')

                    # Panel 4: BOTTOM-RIGHT - ConfigTuner & Meta-Cognitive
                    config_tuner_data = data.get('config_tuner', {})
                    tuner_enabled = config_tuner_data.get('enabled', False)

                    panel4_lines = ["━━━ META-COGNITIVE ━━━"]
                    if tuner_enabled:
                        tuner_mode = config_tuner_data.get('mode', 'unknown')
                        tuner_stats = config_tuner_data.get('stats', {})
                        total_actions = tuner_stats.get('total_actions', 0)
                        success_rate = tuner_stats.get('success_rate', 0.0)
                        recent_actions = tuner_stats.get('recent_actions', [])

                        # Get last action if available
                        last_action = ""
                        if recent_actions and len(recent_actions) > 0:
                            last = recent_actions[-1]
                            param_short = last.get('param', '').split('.')[-1][:10]
                            last_action = f"Last: {param_short}"

                        panel4_lines.extend([
                            f"🧠🔧 Tuner: {tuner_mode.upper()}",
                            f"Actions: {total_actions}",
                            f"Success: {success_rate:.1%}",
                            f"{last_action}"
                        ])
                    else:
                        panel4_lines.append("🧠🔧 Tuner: OFF")

                    # Add quantum info if available
                    quantum_data = data.get('quantum', {})
                    if quantum_data:
                        quantum_states = quantum_data.get('states', 0)
                        panel4_lines.extend([
                            f"⚛️ Quantum: {quantum_states} states"
                        ])

                    panel4_text = "\n".join(panel4_lines)
                    ax.text2D(0.90, 0.10, panel4_text, transform=ax.transAxes,
                              ha='right', va='bottom', fontsize=8, color='yellow',
                              bbox=dict(facecolor='black', alpha=0.7, edgecolor='yellow', linewidth=1),
                              family='monospace')

                    # Panel 5: CENTER-BOTTOM - Real-Time Event Stream
                    # Show last significant event from causation graph
                    events_text = "━━━ RECENT EVENTS ━━━"

                    # Try to get recent tuning action
                    if tuner_enabled and recent_actions and len(recent_actions) > 0:
                        last = recent_actions[-1]
                        param = last.get('param', 'unknown')
                        change = last.get('change', '')
                        success_icon = "✅" if last.get('success', False) else "❌"
                        events_text += f"\n{success_icon} {param}: {change}"
                    elif tuner_enabled:
                        events_text += "\nMonitoring..."
                    else:
                        events_text += "\nNo tuner active"

                    ax.text2D(0.50, 0.10, events_text, transform=ax.transAxes,
                              ha='center', va='bottom', fontsize=7, color='orange',
                              bbox=dict(facecolor='black', alpha=0.7, edgecolor='orange', linewidth=1),
                              family='monospace')

                    profile = self.grid_profiles[self.current_grid_profile_index] if self.grid_profiles else {}
                    derived = {
                        "avg_degree": avg_deg,
                        "clustering": clustering,
                        "language_ratio": language_ratio,
                        "connections": len(G.edges()),
                        "organisms": len(G.nodes())
                    }
                    self._apply_grid_profile(ax, profile)
                    # Bottom menu removed per user request - was showing cluster_sizes and running off window
                    # self._draw_profile_label(ax, profile, data, derived)
                    self._draw_profile_planes(ax, profile, xs, ys, zs)
                else:
                    ax.text2D(0.5, 0.5, f'{num_orgs} Organisms\n{num_conns} Connections',
                              transform=ax.transAxes, ha='center', va='center', fontsize=12, color='white')
            else:
                ax.text2D(0.5, 0.5, 'No Network Data Available',
                          transform=ax.transAxes, ha='center', va='center', fontsize=12, color='white')
        except Exception as e:
            print(f"[Viewer] Error rendering network: {e}")
            import traceback
            traceback.print_exc()
    
    def render_evolution_tree(self, data: Dict[str, Any], ax):
        """Render evolution tree from pre-computed data"""
        try:
            ax.clear()
            ax.set_facecolor('black')
            
            evolution_data = data.get("evolution", {})
            generation = evolution_data.get("generation", 0)
            best_fitness = evolution_data.get("best_fitness", 0)
            avg_fitness = evolution_data.get("avg_fitness", 0)
            population_size = evolution_data.get("population_size", 0)
            
            # Split into two subplots for larger display
            gs = gridspec.GridSpec(1, 2, figure=ax.figure, width_ratios=[1, 1], wspace=0.3)
            ax1 = ax.figure.add_subplot(gs[0])
            ax2 = ax.figure.add_subplot(gs[1])
            
            # Left: Fitness (with larger labels)
            bars1 = ax1.bar(['Best', 'Avg'], [best_fitness, avg_fitness],
                  color=['cyan', 'magenta'], alpha=0.8, edgecolor='white', linewidth=2)
            ax1.set_ylabel('Fitness (0-1)', fontsize=14, color='white')
            ax1.set_title('Fitness Scores', fontsize=16, fontweight='bold', color='white', pad=15)
            ax1.set_ylim(0, 1)
            ax1.tick_params(labelsize=12, colors='white')
            ax1.grid(True, alpha=0.3, axis='y', color='gray')
            ax1.set_facecolor('black')
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                        f'{height:.4f}', ha='center', va='bottom', 
                        fontsize=12, color='white', fontweight='bold')
            
            # Right: Population info (with larger labels)
            bars2 = ax2.barh(['Gen', 'Pop'], [generation, population_size],
                    color=['yellow', 'green'], alpha=0.8, edgecolor='white', linewidth=2)
            ax2.set_xlabel('Value', fontsize=14, color='white')
            ax2.set_title('Status', fontsize=16, fontweight='bold', color='white', pad=15)
            ax2.tick_params(labelsize=12, colors='white')
            ax2.grid(True, alpha=0.3, axis='x', color='gray')
            ax2.set_facecolor('black')
            
            # Add value labels on bars
            for bar in bars2:
                width = bar.get_width()
                ax2.text(width + max(generation, population_size) * 0.02, bar.get_y() + bar.get_height()/2.,
                        f'{int(width)}', ha='left', va='center',
                        fontsize=12, color='white', fontweight='bold')
            
            # Set figure title
            ax.figure.suptitle(f'Evolution - Generation {generation}', 
                             fontsize=18, fontweight='bold', color='white', y=0.98)

            # Add precision indicators
            precision = self.precision_config.get('fitness', 0.000001)
            ax1.text(0.02, 0.98, f'±{precision:.1e}', transform=ax1.transAxes,
                    fontsize=10, alpha=0.7, verticalalignment='top', color='white')
            ax2.text(0.02, 0.98, f'±{precision:.1e}', transform=ax2.transAxes,
                    fontsize=10, alpha=0.7, verticalalignment='top', color='white')
            
            # Remove original ax
            ax.axis('off')
        except Exception as e:
            print(f"[Viewer] Error rendering evolution: {e}")
    
    def render_consciousness_gauge(self, data: Dict[str, Any], ax):
        """Render consciousness gauge from pre-computed data"""
        try:
            ax.cla()
            ax.set_facecolor('black')

            consciousness_data = data.get("consciousness", {})
            score = 0
            if consciousness_data and isinstance(consciousness_data, dict):
                last_analysis = consciousness_data.get("last_analysis", {})
                if isinstance(last_analysis, dict):
                    score = last_analysis.get("overall_score", 0) or 0

            # Title
            ax.set_title('Consciousness Gauge', fontsize=16, fontweight='bold', color='white', pad=10)

            # Large numeric
            ax.text(0.5, 0.7, f'{score:.6f}', ha='center', va='center',
                    fontsize=30, fontweight='bold', color='cyan', transform=ax.transAxes)
            ax.text(0.5, 0.58, '0.0 → 1.0', ha='center', va='center',
                    fontsize=10, color='gray', transform=ax.transAxes)

            # Horizontal bar
            ax.barh([0], [score], color='cyan', alpha=0.9, edgecolor='white', linewidth=2, height=0.18)
            ax.set_xlim(0, 1)
            ax.set_yticks([])
            ax.tick_params(colors='white')
            ax.grid(True, axis='x', alpha=0.2, color='gray')

            # Precision
            precision = self.precision_config.get('consciousness', 0.000001)
            ax.text(0.02, 0.95, f'±{precision:.1e}', transform=ax.transAxes,
                    fontsize=9, alpha=0.7, color='white', va='top')
        except Exception as e:
            print(f"[Viewer] Error rendering consciousness: {e}")
    
    def render_performance_monitor(self, data: Dict[str, Any], ax):
        """Render performance monitor from pre-computed data"""
        try:
            ax.cla()
            ax.set_facecolor('black')

            lattice_data = data.get("lattice", {})
            cpu_usage = float(lattice_data.get("cpu_usage", 0) or 0)
            ram_usage = float(lattice_data.get("ram_usage", 0) or 0)

            simulation_data = data.get("simulation", {})
            fps = float(simulation_data.get("fps", 10) or 10)

            ax.set_title('Performance Monitor', fontsize=16, fontweight='bold', color='white', pad=10)

            # Draw bars in-place to avoid subplot overdraw
            labels = ['CPU %', 'RAM GB', 'FPS']
            values = [cpu_usage, ram_usage, fps]
            colors = ['red', 'blue', 'green']

            bars = ax.bar(labels, values, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
            ax.tick_params(colors='white', labelsize=11)
            ax.grid(True, axis='y', alpha=0.25, color='gray')
            
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2., val + max(values) * 0.03,
                        f'{val:.2f}', ha='center', va='bottom', fontsize=10, color='white', fontweight='bold')

            cpu_prec = self.precision_config.get('performance_cpu', 0.0001)
            fps_prec = self.precision_config.get('performance_fps', 10)
            ax.text(0.02, 0.95, f'±CPU {cpu_prec:.1e} | ±FPS {fps_prec}', transform=ax.transAxes,
                    fontsize=9, alpha=0.7, color='white', va='top')
        except Exception as e:
            print(f"[Viewer] Error rendering performance: {e}")
    
    def render_particle_cloud(self, data: Dict[str, Any], ax):
        """Render particle cloud in 3D with interactive rotation"""
        try:
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

            # Ensure 3D axes
            if getattr(ax, 'name', '') != '3d':
                fig = ax.figure
                try:
                    fig.delaxes(ax)
                except Exception:
                    pass
                ax = fig.add_subplot(111, projection='3d')
                self.tab_axes["particle_cloud"] = ax

            ax.cla()
            ax.set_facecolor('black')

            lattice_data = data.get("lattice", {})
            particle_count = int(lattice_data.get("particles", 0) or 0)

            if particle_count > 0:
                positions = None
                particle_positions = lattice_data.get('particle_positions', [])

                if particle_positions:
                    positions = np.array(particle_positions[:self.max_particles_to_plot])
                    # If positions are 2D, lift into 3D with small z jitter
                    if positions.ndim == 2 and positions.shape[1] == 2:
                        zs = np.random.default_rng(42).normal(0.0, 0.02, size=positions.shape[0])
                        positions = np.column_stack((positions, zs))
                else:
                    # Synthetic 3D cloud fallback
                    rng = np.random.default_rng(42)
                    theta = rng.uniform(0, 2*np.pi, size=min(particle_count, 100))
                    phi = rng.uniform(0, np.pi, size=min(particle_count, 100))
                    r = 0.4 + 0.1 * rng.random(size=min(particle_count, 100))
                    xs = r * np.sin(phi) * np.cos(theta)
                    ys = r * np.sin(phi) * np.sin(theta)
                    zs = r * np.cos(phi)
                    positions = np.column_stack((xs, ys, zs))

                # Normalize for nice cube display
                pos_min = positions.min(axis=0)
                pos_max = positions.max(axis=0)
                ranges = np.maximum(pos_max - pos_min, 1e-9)
                positions = (positions - pos_min) / ranges

                ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                           c=np.arange(len(positions)), cmap='plasma', s=15,
                           alpha=0.85, edgecolors='white', linewidths=0.2)
                ax.set_title(f'Particle Cloud (3D) - {particle_count} Particles',
                             fontsize=12, fontweight='bold', color='white', pad=10)
                ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
                ax.set_box_aspect((1, 1, 1))
            else:
                ax.text2D(0.5, 0.5, 'No Particle Data Available',
                          transform=ax.transAxes, ha='center', va='center', fontsize=12, color='white')
        except Exception as e:
            print(f"[Viewer] Error rendering particles: {e}")
            import traceback
            traceback.print_exc()
    
    def update_visualizations(self, data: Dict[str, Any]):
        """Update all visualizations with new data"""
        if self.root is None:
            self.create_unified_window()

        if self.root is None or len(self.tab_axes) == 0:
            return

        try:
            print(f"[Viewer] Updating visualizations with data keys: {list(data.keys()) if data else 'None'}")
            self.last_visualization_data = data

            # Update each visualization in its respective tab
            if "network_graph" in self.tab_axes:
                print("[Viewer] Rendering network graph...")
                self.render_network_graph(data, self.tab_axes["network_graph"])
                if "network_graph" in self.tab_canvases:
                    self.tab_canvases["network_graph"].draw()
                    print("[Viewer] Network graph canvas drawn")
                else:
                    print("[Viewer] ERROR: Network graph canvas not found")

            if "evolution_tree" in self.tab_axes:
                print("[Viewer] Rendering evolution tree...")
                self.render_evolution_tree(data, self.tab_axes["evolution_tree"])
                if "evolution_tree" in self.tab_canvases:
                    self.tab_canvases["evolution_tree"].draw()
                    print("[Viewer] Evolution tree canvas drawn")
                else:
                    print("[Viewer] ERROR: Evolution tree canvas not found")

            if "consciousness_gauge" in self.tab_axes:
                print("[Viewer] Rendering consciousness gauge...")
                self.render_consciousness_gauge(data, self.tab_axes["consciousness_gauge"])
                if "consciousness_gauge" in self.tab_canvases:
                    self.tab_canvases["consciousness_gauge"].draw()
                    print("[Viewer] Consciousness gauge canvas drawn")
                else:
                    print("[Viewer] ERROR: Consciousness gauge canvas not found")

            if "performance_monitor" in self.tab_axes:
                print("[Viewer] Rendering performance monitor...")
                self.render_performance_monitor(data, self.tab_axes["performance_monitor"])
                if "performance_monitor" in self.tab_canvases:
                    self.tab_canvases["performance_monitor"].draw()
                    print("[Viewer] Performance monitor canvas drawn")
                else:
                    print("[Viewer] ERROR: Performance monitor canvas not found")

            if "particle_cloud" in self.tab_axes:
                print("[Viewer] Rendering particle cloud...")
                self.render_particle_cloud(data, self.tab_axes["particle_cloud"])
                if "particle_cloud" in self.tab_canvases:
                    self.tab_canvases["particle_cloud"].draw()
                    print("[Viewer] Particle cloud canvas drawn")
                else:
                    print("[Viewer] ERROR: Particle cloud canvas not found")

            # Process tkinter events
            self.root.update_idletasks()
            print("[Viewer] Visualization update complete")

        except Exception as e:
            print(f"[Viewer] Error updating visualizations: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main loop - reads data and updates display"""
        print("[Viewer] 🎨 Starting lightweight visualization viewer...")
        print("[Viewer] This process only displays data - all computation happens in backend")
        
        if self.root is None:
            self.create_unified_window()
        
        if self.root is None:
            print("[Viewer] ❌ Failed to create window")
            return
        
        def update_loop():
            """Update visualizations periodically"""
            try:
                current_time = time.time()

                # Only update at specified interval (reduces CPU usage)
                if current_time - self.last_update >= self.update_interval:
                    print(f"[Viewer] Reading visualization data...")
                    data = read_visualization_data()
                    if data:
                        print(f"[Viewer] Data read successfully, updating visualizations...")
                        self.update_visualizations(data)
                        self.last_update = current_time
                    else:
                        print(f"[Viewer] No data available from shared state")

                # Schedule next update
                if self.root.winfo_exists():
                    self.root.after(int(self.update_interval * 1000), update_loop)
            except Exception as e:
                print(f"[Viewer] Error in update loop: {e}")
                import traceback
                traceback.print_exc()
        
        # Start update loop
        self.root.after(100, update_loop)
        
        # Run tkinter main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n[Viewer] Shutting down...")
            if self.root:
                self.root.quit()


if __name__ == "__main__":
    viewer = LightweightVisualizationViewer(update_interval=0.5)  # Update every 0.5 seconds
    viewer.run()

