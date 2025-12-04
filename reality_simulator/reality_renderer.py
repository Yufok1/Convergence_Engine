"""
[RENDER] REALITY RENDERER (Layer 5)

The interface between simulated reality and human perception.
Multiple visualization modes and interaction paradigms.

Features:
- God Mode: Omniscient overview of entire simulation
- Observer Mode: Scientific analysis and data visualization
- Participant Mode: Immersive experience within the simulation
- Scientist Mode: Experimental controls and hypothesis testing
- Real-time rendering with performance optimization
- Multi-modal output (text, graphics, audio)
"""

import time
import json
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

try:
    from quantum_substrate import QuantumStateManager
    from subatomic_lattice import create_subatomic_lattice
    from evolution_engine import EvolutionEngine
    from symbiotic_network import SymbioticNetwork
    from agency import AgencyRouter
except ImportError:
    # Forward declarations for testing
    class QuantumStateManager: pass
    class EvolutionEngine: pass
    class SymbioticNetwork: pass
    class AgencyRouter: pass


class InteractionMode(Enum):
    """Different ways users can interact with the simulation"""
    GOD = "god"              # Omniscient control and overview
    OBSERVER = "observer"    # Scientific observation and analysis
    PARTICIPANT = "participant"  # Immersive participation
    SCIENTIST = "scientist"  # Experimental manipulation
    HEADLESS = "headless"    # No rendering, pure computation (server/cloud mode)


@dataclass
class RenderState:
    """
    Current state of the reality renderer
    """
    mode: InteractionMode = InteractionMode.OBSERVER
    active_visualizations: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    user_position: Optional[np.ndarray] = None
    selected_entities: List[str] = field(default_factory=list)
    time_dilation: float = 1.0  # Simulation speed relative to real time
    last_render_time: float = 0.0


@dataclass
class VisualizationConfig:
    """
    Configuration for visualization rendering
    """
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: float = 30.0
    quality: str = "high"  # low, medium, high
    show_debug_info: bool = False
    enable_visualizations: bool = False  # Enable matplotlib plot windows
    color_scheme: str = "scientific"
    audio_enabled: bool = True


class RealityRenderer:
    """
    Main reality renderer coordinating all visualization and interaction
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.state = RenderState()
        self.visualization_modules: Dict[str, Any] = {}

        # Core simulation components (to be injected)
        self.quantum_manager: Optional[QuantumStateManager] = None
        self.lattice: Optional[Any] = None  # Subatomic lattice
        self.evolution_engine: Optional[EvolutionEngine] = None
        self.network: Optional[SymbioticNetwork] = None
        self.agency_router: Optional[AgencyRouter] = None

        # Rendering state
        self.frame_count = 0
        self.start_time = time.time()
        self.fitness_history = []  # Track fitness over time for evolution visualization

        # Initialize visualization modules
        self._initialize_visualizations()

    def _initialize_visualizations(self):
        """Initialize available visualization modules"""
        # Import QuantumVisualizer for real visualizations
        try:
            from visualization import QuantumVisualizer
            self.quantum_visualizer = QuantumVisualizer()
        except ImportError:
            self.quantum_visualizer = None
        
        # Setup matplotlib for interactive mode if visualizations enabled
        self.visualizations_enabled = self.config.enable_visualizations if self.config else False
        
        print(f"[Visualization] Initializing with enable_visualizations={self.visualizations_enabled}")
        
        if self.visualizations_enabled:
            try:
                import matplotlib
                matplotlib.use('TkAgg')  # Use TkAgg backend for interactive windows
                import matplotlib.pyplot as plt
                plt.ion()  # Turn on interactive mode
                print("[Visualization] [SUCCESS] Matplotlib interactive mode enabled - unified visualization window will be created")
                # Create unified figure on first render
            except Exception as e:
                print(f"[Visualization] [ERROR] Warning: Could not enable interactive mode: {e}")
                self.visualizations_enabled = False
        else:
            print("[Visualization] [WARN] Visualizations disabled (set config.enable_visualizations=True to enable)")
        
        # Real visualization modules that create actual plots
        self.visualization_modules = {
            "quantum_field": QuantumFieldVisualizer(self),
            "particle_cloud": ParticleCloudVisualizer(self),
            "evolution_tree": EvolutionTreeVisualizer(self),
            "network_graph": NetworkGraphVisualizer(self),
            "agency_flow": AgencyFlowVisualizer(self),
            "performance_monitor": PerformanceMonitorVisualizer(self),
            "god_overview": GodOverviewVisualizer(self)
        }
        
        # Track active figure windows
        self.active_figures = {}
        
        # Unified visualization window (single figure with grid layout)
        self.unified_figure = None
        self.unified_axes = {}  # Map visualization names to their axes in the unified figure

    def set_interaction_mode(self, mode: InteractionMode, reason: str = ""):
        """Switch interaction mode"""
        old_mode = self.state.mode
        self.state.mode = mode

        print(f"[RENDER] Switched to {mode.value} mode")
        if reason:
            print(f"Reason: {reason}")

        # Configure visualizations for new mode
        self._configure_mode_visualizations(mode)

        # Reset user position for participant mode
        if mode == InteractionMode.PARTICIPANT:
            self.state.user_position = np.array([0.0, 0.0, 0.0])

    def _configure_mode_visualizations(self, mode: InteractionMode):
        """Configure which visualizations are active for each mode"""
        if mode == InteractionMode.GOD:
            self.state.active_visualizations = [
                "god_overview", "performance_monitor", "quantum_field"
            ]
        elif mode == InteractionMode.OBSERVER:
            self.state.active_visualizations = [
                "network_graph", "evolution_tree",
                "performance_monitor", "particle_cloud"
            ]
        elif mode == InteractionMode.PARTICIPANT:
            self.state.active_visualizations = [
                "particle_cloud", "network_graph", "agency_flow"
            ]
        elif mode == InteractionMode.SCIENTIST:
            self.state.active_visualizations = [
                "quantum_field", "evolution_tree",
                "performance_monitor", "agency_flow"
            ]
        elif mode == InteractionMode.HEADLESS:
            # No visualizations in headless mode - pure computation
            self.state.active_visualizations = []
            self.visualizations_enabled = False
        
        # Reset unified figure when mode changes (will be recreated on next render)
        if self.unified_figure is not None:
            try:
                import matplotlib.pyplot as plt
                plt.close(self.unified_figure)
            except:
                pass
            self.unified_figure = None
            self.unified_axes = {}

    def inject_simulation_components(self, **components):
        """Inject simulation components for rendering"""
        for name, component in components.items():
            setattr(self, name, component)
    
    def _create_unified_visualization_window(self):
        """Create a single unified figure window with grid layout for all visualizations"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec
            
            num_viz = len(self.state.active_visualizations)
            if num_viz == 0:
                return
            
            # Create a reasonably sized figure for the unified window
            self.unified_figure = plt.figure(figsize=(16, 10))
            self.unified_figure.suptitle(f'Reality Simulator - {self.state.mode.value.upper()} Mode', 
                                        fontsize=16, fontweight='bold', y=0.97)
            
            # Determine grid layout based on number of visualizations
            if num_viz <= 2:
                rows, cols = 1, num_viz
            elif num_viz <= 4:
                rows, cols = 2, 2
            elif num_viz <= 6:
                rows, cols = 2, 3
            elif num_viz <= 9:
                rows, cols = 3, 3
            else:
                rows, cols = 3, 4
            
            # Use GridSpec for flexible layout with better spacing to prevent overlap
            gs = gridspec.GridSpec(rows, cols, figure=self.unified_figure, 
                                 hspace=0.4, wspace=0.4, 
                                 left=0.06, right=0.96, top=0.94, bottom=0.06)
            
            # Assign axes to each visualization
            for idx, viz_name in enumerate(self.state.active_visualizations):
                row = idx // cols
                col = idx % cols
                
                # Some visualizations need multiple subplots (like evolution_tree)
                if viz_name in ["evolution_tree", "performance_monitor"]:
                    # These need 2 subplots side by side
                    if col + 1 < cols:
                        # Can fit 2 columns
                        ax = self.unified_figure.add_subplot(gs[row, col:col+2])
                    else:
                        # Wrap to next row if needed
                        ax = self.unified_figure.add_subplot(gs[row, col])
                else:
                    ax = self.unified_figure.add_subplot(gs[row, col])
                
                self.unified_axes[viz_name] = ax
            
            # Show the unified window
            self.unified_figure.show()
            plt.draw()
            plt.pause(0.1)
            
            print(f"[Visualization] [SUCCESS] Created unified visualization window with {num_viz} panels")
            
        except Exception as e:
            print(f"[Visualization] [ERROR] Error creating unified window: {e}")
            import traceback
            traceback.print_exc()
            self.unified_figure = None
            self.unified_axes = {}

    def render_frame(self) -> Dict[str, Any]:
        """
        Render a single frame of the simulation

        Returns render data for different output modalities
        """
        current_time = time.time()
        delta_time = current_time - self.state.last_render_time
        self.state.last_render_time = current_time

        # Apply time dilation
        sim_delta = delta_time * self.state.time_dilation

        # Collect data from all simulation components
        simulation_data = self._collect_simulation_data()

        # Render active visualizations
        render_output = {
            "frame_number": self.frame_count,
            "timestamp": current_time,
            "mode": self.state.mode.value,
            "time_dilation": self.state.time_dilation,
            "visualizations": {},
            "performance": self.state.performance_metrics
        }

        # HEADLESS mode: skip all visualization, just return metrics
        if self.state.mode == InteractionMode.HEADLESS:
            self.frame_count += 1
            render_output["headless_data"] = {
                "simulation_data": simulation_data,
                "frame_count": self.frame_count
            }
            return render_output

        # Create unified visualization window on first frame
        if self.visualizations_enabled and self.unified_figure is None:
            self._create_unified_visualization_window()
        
        if self.frame_count == 1 and self.visualizations_enabled:
            print(f"[Visualization] Rendering {len(self.state.active_visualizations)} visualizations in unified window: {self.state.active_visualizations}")
        
        for viz_name in self.state.active_visualizations:
            if viz_name in self.visualization_modules:
                viz_module = self.visualization_modules[viz_name]
                
                # Pass unified axis if available
                unified_ax = self.unified_axes.get(viz_name) if self.unified_figure else None
                viz_data = viz_module.render(simulation_data, self.state, self.config, unified_ax=unified_ax)
                render_output["visualizations"][viz_name] = viz_data
        
        # Update unified window if it exists
        if self.visualizations_enabled and self.unified_figure is not None:
            try:
                import matplotlib.pyplot as plt
                self.unified_figure.canvas.draw()
                self.unified_figure.canvas.flush_events()
                plt.pause(0.001)  # Allow GUI to update
            except Exception as e:
                if self.frame_count % 100 == 0:  # Only log occasionally
                    print(f"[Visualization] ⚠️  Error updating unified window: {e}")

        # Mode-specific rendering
        if self.state.mode == InteractionMode.GOD:
            render_output["god_data"] = self._render_god_mode(simulation_data)
        elif self.state.mode == InteractionMode.OBSERVER:
            render_output["observer_data"] = self._render_observer_mode(simulation_data)
        elif self.state.mode == InteractionMode.PARTICIPANT:
            render_output["participant_data"] = self._render_participant_mode(simulation_data)
        elif self.state.mode == InteractionMode.SCIENTIST:
            render_output["scientist_data"] = self._render_scientist_mode(simulation_data)

        self.frame_count += 1
        return render_output

    def _collect_simulation_data(self) -> Dict[str, Any]:
        """Collect current state from all simulation components"""
        data = {}

        if self.quantum_manager:
            data["quantum"] = {
                "states": len(self.quantum_manager.states) if hasattr(self.quantum_manager, 'states') else 0,
                "entanglements": 0,  # Would collect actual entanglement data
                "superpositions": 0
            }

        if self.lattice:
            particles, approximator, monitor = self.lattice
            data["lattice"] = {
                "particles": len(particles),
                "pruned_states": approximator.pruned_states if hasattr(approximator, 'pruned_states') else 0,
                "cpu_usage": monitor.get_current_usage().get("cpu_percent", 0),
                "ram_usage": monitor.get_current_usage().get("ram_gb", 0)
            }

        if self.evolution_engine:
            best_fitness = self.evolution_engine.get_best_organism().fitness if self.evolution_engine.population else 0
            # Track fitness history for visualization
            self.fitness_history.append(best_fitness)
            if len(self.fitness_history) > 100:  # Keep last 100 generations
                self.fitness_history = self.fitness_history[-100:]
            
            data["evolution"] = {
                "generation": self.evolution_engine.generation,
                "population_size": len(self.evolution_engine.population),
                "best_fitness": best_fitness,
                "avg_fitness": np.mean([org.fitness for org in self.evolution_engine.population]) if self.evolution_engine.population else 0
            }

        if self.network:
            data["network"] = {
                "organisms": len(self.network.organisms),
                "connections": len(self.network.connections),
                "stability": self.network.metrics.stability_index,
                "connectivity": self.network.metrics.connectivity
            }

        if self.agency_router:
            data["agency"] = {
                "mode": self.agency_router.current_mode.value,
                "performance": self.agency_router.performance.get_summary()
            }

        return data

    def _render_god_mode(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render god mode: Omniscient overview"""
        return {
            "universe_overview": {
                "total_entities": sum(len(v) if isinstance(v, (list, dict)) and not isinstance(v, str)
                                    else (v if isinstance(v, (int, float)) else 0)
                                    for k, v in simulation_data.items() if k != "consciousness")
            },
            "control_panels": {
                "time_control": {"current_dilation": self.state.time_dilation},
                "entity_selection": {"selected": self.state.selected_entities},
                "intervention_tools": ["create_particle", "modify_fitness", "force_connection"]
            },
            "system_health": {
                "overall_stability": simulation_data.get("network", {}).get("stability", 0.5),
                "resource_usage": simulation_data.get("lattice", {})
            }
        }

    def _render_observer_mode(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render observer mode: Scientific analysis"""
        return {
            "scientific_metrics": {
                "evolutionary_progress": simulation_data.get("evolution", {}),
                "network_topology": simulation_data.get("network", {}),
                "quantum_coherence": simulation_data.get("quantum", {})
            },
            "data_visualizations": {
                "fitness_over_time": [],  # Would contain historical data
                "network_evolution": [],  # Network structure changes
                "consciousness_emergence": []  # Consciousness detection events
            },
            "analysis_tools": {
                "correlation_analysis": "available",
                "trend_detection": "available",
                "hypothesis_testing": "available"
            }
        }

    def _render_participant_mode(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render participant mode: Immersive experience"""
        # Simulate user's position in the simulation
        if self.state.user_position is None:
            self.state.user_position = np.array([0.0, 0.0, 0.0])

        # Find nearby entities
        nearby_entities = self._find_nearby_entities(self.state.user_position)

        return {
            "user_position": self.state.user_position.tolist(),
            "nearby_entities": nearby_entities,
            "sensory_input": {
                "visual": f"Rendering {len(nearby_entities)} nearby entities",
                "auditory": "Simulation ambient sounds",
                "tactile": "Subtle vibration feedback"
            },
            "interaction_options": {
                "move": "WASD or arrow keys",
                "interact": "E key or mouse click",
                "communicate": "Text chat with entities"
            },
            "immersion_metrics": {
                "presence_level": 0.8,  # Would be calculated from user engagement
                "agency_feeling": 0.7
            }
        }

    def _render_scientist_mode(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render scientist mode: Experimental controls"""
        return {
            "experimental_tools": {
                "parameter_controls": {
                    "mutation_rate": "adjustable",
                    "connection_probability": "adjustable",
                    "resource_distribution": "adjustable"
                },
                "intervention_capabilities": {
                    "introduce_species": "available",
                    "modify_environment": "available",
                    "reset_simulation": "available"
                },
                "measurement_tools": {
                    "real_time_monitoring": "active",
                    "data_export": "available",
                    "hypothesis_tracker": "available"
                }
            },
            "current_experiments": [],  # Would track active experiments
            "data_collection": {
                "metrics_being_recorded": ["consciousness", "fitness", "network_stability"],
                "sample_rate": f"{self.config.frame_rate} Hz",
                "data_points_collected": self.frame_count
            }
        }

    def _find_nearby_entities(self, position: np.ndarray, radius: float = 10.0) -> List[Dict[str, Any]]:
        """Find entities near a given position (for participant mode)"""
        nearby = []

        # This is a simplified version - in reality would do spatial queries
        if self.lattice and len(self.lattice) >= 3:
            particles = self.lattice[0]  # First element is particles list
            for i, particle in enumerate(particles[:10]):  # Limit for performance
                distance = np.linalg.norm(particle.position - position)
                if distance <= radius:
                    nearby.append({
                        "id": f"particle_{i}",
                        "type": "particle",
                        "position": particle.position.tolist(),
                        "distance": distance,
                        "properties": {
                            "charge": particle.charge,
                            "fitness": getattr(particle, 'fitness', 0.5)
                        }
                    })

        return nearby

    def handle_user_input(self, input_type: str, input_data: Any) -> Dict[str, Any]:
        """
        Handle user input based on current interaction mode

        Returns response data for the user interface
        """
        response = {"input_processed": True, "mode": self.state.mode.value}

        if self.state.mode == InteractionMode.GOD:
            response.update(self._handle_god_input(input_type, input_data))
        elif self.state.mode == InteractionMode.OBSERVER:
            response.update(self._handle_observer_input(input_type, input_data))
        elif self.state.mode == InteractionMode.PARTICIPANT:
            response.update(self._handle_participant_input(input_type, input_data))
        elif self.state.mode == InteractionMode.SCIENTIST:
            response.update(self._handle_scientist_input(input_type, input_data))

        return response

    def _handle_god_input(self, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle god mode input (omniscient control)"""
        if input_type == "time_control":
            self.state.time_dilation = float(input_data.get("dilation", 1.0))
            return {"time_dilation_set": self.state.time_dilation}

        elif input_type == "entity_select":
            self.state.selected_entities = input_data.get("entities", [])
            return {"entities_selected": len(self.state.selected_entities)}

        elif input_type == "create_entity":
            # Would create new entity in simulation
            return {"entity_created": "placeholder"}

        return {"action": "unhandled"}

    def _handle_observer_input(self, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle observer mode input (analysis controls)"""
        if input_type == "analysis_request":
            analysis_type = input_data.get("type", "general")
            return {"analysis": f"Performing {analysis_type} analysis"}

        elif input_type == "data_export":
            format_type = input_data.get("format", "json")
            return {"export_started": f"Exporting in {format_type} format"}

        return {"action": "unhandled"}

    def _handle_participant_input(self, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle participant mode input (movement and interaction)"""
        if input_type == "movement":
            direction = np.array(input_data.get("direction", [0, 0, 0]))
            speed = input_data.get("speed", 1.0)

            if self.state.user_position is not None:
                self.state.user_position += direction * speed

            return {"position_updated": self.state.user_position.tolist() if self.state.user_position is not None else None}

        elif input_type == "interaction":
            target_id = input_data.get("target_id")
            interaction_type = input_data.get("type", "examine")

            return {"interaction_result": f"{interaction_type} with {target_id}"}

        return {"action": "unhandled"}

    def _handle_scientist_input(self, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle scientist mode input (experimental controls)"""
        if input_type == "parameter_change":
            param_name = input_data.get("parameter")
            new_value = input_data.get("value")

            # Would modify simulation parameters
            return {"parameter_changed": f"{param_name} = {new_value}"}

        elif input_type == "experiment_start":
            experiment_name = input_data.get("name")
            return {"experiment_started": experiment_name}

        return {"action": "unhandled"}

    def get_performance_stats(self) -> Dict[str, float]:
        """Get rendering performance statistics"""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0

        # Try to get simulation FPS from shared state if available
        simulation_fps = 0
        try:
            import os
            import json
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            shared_state_file = os.path.join(project_root, "data", ".shared_simulation_state.json")
            if os.path.exists(shared_state_file):
                with open(shared_state_file, 'r') as f:
                    shared_state = json.load(f)
                    simulation_fps = shared_state.get('simulation_fps', 0)
        except:
            pass  # Fall back to render FPS

        return {
            "frames_rendered": self.frame_count,
            "elapsed_time": elapsed,
            "average_fps": fps,
            "simulation_fps": simulation_fps,
            "target_fps": self.config.frame_rate,
            "performance_ratio": fps / self.config.frame_rate if self.config.frame_rate > 0 else 0
        }


# Visualization Module Classes
class QuantumFieldVisualizer:
    """Visualizes quantum field states"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config):
        """Render quantum field visualization"""
        if not self.renderer.visualizations_enabled:
            return {"quantum_states": data.get("quantum", {}), "field_intensity": 0.7}
        
        if not self.renderer.quantum_visualizer or not self.renderer.quantum_manager:
            return {"quantum_states": data.get("quantum", {}), "field_intensity": 0.7}
        
        try:
            import matplotlib.pyplot as plt
            
            # Get quantum states
            quantum_data = data.get("quantum", {})
            num_states = quantum_data.get("states", 0)
            
            if num_states > 0 and len(self.renderer.quantum_manager.states) > 0:
                # Reuse existing figure or create new one
                fig = self.renderer.active_figures.get("quantum_field")
                if fig is None or not plt.fignum_exists(fig.number):
                    # Visualize first available state
                    first_state_id = list(self.renderer.quantum_manager.states.keys())[0]
                    first_state = self.renderer.quantum_manager.states[first_state_id]
                    
                    fig = self.renderer.quantum_visualizer.visualize_superposition(
                        first_state, 
                        f"Quantum Field - {num_states} States"
                    )
                else:
                    # Update existing figure (simplified - could update data here)
                    fig.suptitle(f"Quantum Field - {num_states} States", fontsize=16, fontweight='bold')
                
                plt.draw()
                plt.pause(0.001)  # Allow GUI to update
                
                return {
                    "quantum_states": quantum_data,
                    "field_intensity": 0.7,
                    "figure": fig
                }
        except Exception as e:
            print(f"[Visualization] Error rendering quantum field: {e}")
        
        quantum_data = data.get("quantum", {})
        return {"quantum_states": quantum_data, "field_intensity": 0.7}

class ParticleCloudVisualizer:
    """Visualizes particle distributions"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config, unified_ax=None):
        """Render particle cloud visualization"""
        if not self.renderer.visualizations_enabled:
            return {"particle_count": data.get("lattice", {}).get("particles", 0), "cloud_density": 0.5}
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            lattice_data = data.get("lattice", {})
            particle_count = lattice_data.get("particles", 0)
            
            if particle_count > 0 and self.renderer.lattice:
                particles, _, _ = self.renderer.lattice
                
                if particles and len(particles) > 0:
                    # Extract positions
                    positions = np.array([p.position for p in particles[:min(50, len(particles))]])
                    
                    # Use unified axis if provided, otherwise create own figure
                    if unified_ax is not None:
                        ax = unified_ax
                        ax.clear()
                        fig = ax.figure
                    else:
                        # Legacy: create separate figure
                        fig = self.renderer.active_figures.get("particle_cloud")
                        if fig is None or not plt.fignum_exists(fig.number):
                            fig, ax = plt.subplots(figsize=(10, 8))
                        else:
                            ax = fig.gca()
                            ax.clear()
                    
                    if positions.shape[1] >= 2:
                        # 2D projection
                        ax.scatter(positions[:, 0], positions[:, 1], 
                                  c=range(len(positions)), cmap='plasma',
                                  s=100, alpha=0.7, edgecolors='white', linewidth=1)
                        ax.set_xlabel('X Position', fontsize=10)
                        ax.set_ylabel('Y Position', fontsize=10)
                    elif positions.shape[1] == 1:
                        # 1D
                        ax.scatter(positions[:, 0], np.zeros(len(positions)),
                                  c=range(len(positions)), cmap='plasma',
                                  s=100, alpha=0.7, edgecolors='white', linewidth=1)
                        ax.set_xlabel('Position', fontsize=10)
                    
                    ax.set_title(f'Particle Cloud - {particle_count} Particles', 
                               fontsize=12, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    
                    if unified_ax is None:
                        plt.tight_layout()
                        plt.draw()
                        plt.pause(0.001)
                    
                    return {
                        "particle_count": particle_count,
                        "cloud_density": 0.5,
                        "figure": fig if unified_ax is None else None
                    }
        except Exception as e:
            print(f"[Visualization] Error rendering particle cloud: {e}")
        
        return {"particle_count": data.get("lattice", {}).get("particles", 0), "cloud_density": 0.5}

class EvolutionTreeVisualizer:
    """Visualizes evolutionary relationships"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config, unified_ax=None):
        """Render evolution tree visualization"""
        if not self.renderer.visualizations_enabled:
            return {"generations": data.get("evolution", {}).get("generation", 0), "tree_depth": 5}
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec
            import numpy as np
            
            evolution_data = data.get("evolution", {})
            generation = evolution_data.get("generation", 0)
            population_size = evolution_data.get("population_size", 0)
            best_fitness = evolution_data.get("best_fitness", 0)
            avg_fitness = evolution_data.get("avg_fitness", 0)
            
            # Use unified axis if provided, otherwise create own figure
            if unified_ax is not None:
                # Split unified axis into two sub-axes
                ax = unified_ax
                ax.clear()
                # Create sub-grid within this axis
                gs_sub = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=ax.get_subplotspec(), wspace=0.3)
                ax1 = ax.figure.add_subplot(gs_sub[0])
                ax2 = ax.figure.add_subplot(gs_sub[1])
                fig = ax.figure
            else:
                # Legacy: create separate figure
                fig = self.renderer.active_figures.get("evolution_tree")
                if fig is None or not plt.fignum_exists(fig.number):
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
                else:
                    ax1, ax2 = fig.axes
                    ax1.clear()
                    ax2.clear()
            
            # Left: Fitness over generations (if we have history)
            if hasattr(self.renderer, 'fitness_history') and len(self.renderer.fitness_history) > 0:
                gens = list(range(len(self.renderer.fitness_history)))
                ax1.plot(gens, self.renderer.fitness_history, 'cyan', 
                       linewidth=2, marker='o', markersize=3)
                ax1.set_xlabel('Generation', fontsize=9)
                ax1.set_ylabel('Best Fitness', fontsize=9)
                ax1.set_title('Fitness Evolution', fontsize=11)
                ax1.grid(True, alpha=0.3)
            else:
                # Just show current state
                ax1.bar(['Best', 'Avg'], [best_fitness, avg_fitness],
                      color=['cyan', 'magenta'], alpha=0.7, edgecolor='white', linewidth=1)
                ax1.set_ylabel('Fitness', fontsize=9)
                ax1.set_title('Current Fitness', fontsize=11)
                ax1.set_ylim(0, 1)
                ax1.grid(True, alpha=0.3, axis='y')
            
            # Right: Population info
            ax2.barh(['Gen', 'Pop'], 
                    [generation, population_size],
                    color=['yellow', 'green'], alpha=0.7, edgecolor='white', linewidth=1)
            ax2.set_xlabel('Value', fontsize=9)
            ax2.set_title('Evolution Status', fontsize=11)
            ax2.grid(True, alpha=0.3, axis='x')
            
            if unified_ax is None:
                fig.suptitle(f'Evolution Tree - Gen {generation}', 
                           fontsize=16, fontweight='bold')
                plt.tight_layout()
                plt.draw()
                plt.pause(0.001)
            else:
                unified_ax.set_title(f'Evolution Tree - Gen {generation}', fontsize=12, fontweight='bold')
            
            return {
                "generations": generation,
                "tree_depth": 5,
                "figure": fig if unified_ax is None else None
            }
        except Exception as e:
            print(f"[Visualization] Error rendering evolution tree: {e}")
            import traceback
            traceback.print_exc()
        
        return {"generations": data.get("evolution", {}).get("generation", 0), "tree_depth": 5}

class NetworkGraphVisualizer:
    """Visualizes symbiotic network structure"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config, unified_ax=None):
        """Render network graph visualization"""
        if not self.renderer.visualizations_enabled:
            network_data = data.get("network", {})
            return {
                "nodes": network_data.get("organisms", 0),
                "edges": network_data.get("connections", 0),
                "stability": network_data.get("stability", 0.5)
            }
        
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            
            network_data = data.get("network", {})
            num_orgs = network_data.get("organisms", 0)
            num_conns = network_data.get("connections", 0)
            
            if num_orgs > 0 and self.renderer.network:
                G = self.renderer.network.network_graph
                
                if len(G.nodes()) > 0:
                    # Use unified axis if provided, otherwise create own figure
                    if unified_ax is not None:
                        ax = unified_ax
                        ax.clear()
                        fig = ax.figure
                    else:
                        # Legacy: create separate figure
                        fig = self.renderer.active_figures.get("network_graph")
                        if fig is None or not plt.fignum_exists(fig.number):
                            fig, ax = plt.subplots(figsize=(12, 8))
                        else:
                            ax = fig.gca()
                            ax.clear()
                    
                    # Layout
                    pos = nx.spring_layout(G, k=1, iterations=50)
                    
                    # Color nodes by fitness if available
                    node_colors = []
                    for node_id in G.nodes():
                        if node_id in self.renderer.network.organisms:
                            org = self.renderer.network.organisms[node_id]
                            fitness = getattr(org, 'fitness', 0.5)
                            node_colors.append(fitness)
                        else:
                            node_colors.append(0.5)
                    
                    # Draw network with differentiated edge types
                    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                                         node_size=300, cmap='plasma',
                                         alpha=0.8, edgecolors='white',
                                         linewidths=1, ax=ax)

                    # Separate edges by type for differentiation
                    regular_edges = []
                    language_edges = []
                    edge_weights = []
                    edge_alphas = []

                    # Check if network has language subgraph
                    has_language_subgraph = hasattr(self.renderer.network, 'language_subgraph') and self.renderer.network.language_subgraph is not None
                    print(f"[NETWORK VISUALIZATION] Language subgraph available: {has_language_subgraph}")

                    language_edge_count = 0
                    for u, v, data in G.edges(data=True):
                        # Check if this is a language-tagged connection
                        is_language_edge = False
                        if has_language_subgraph:
                            # Check if edge exists in linguistic_edges dictionary (check both directions)
                            is_language_edge = ((u, v) in self.renderer.network.language_subgraph.linguistic_edges or
                                              (v, u) in self.renderer.network.language_subgraph.linguistic_edges)
                            if is_language_edge:
                                language_edge_count += 1

                        if is_language_edge:
                            language_edges.append((u, v))
                        else:
                            regular_edges.append((u, v))

                        # Get edge weight (default to 1.0)
                        weight = data.get('weight', 1.0)
                        edge_weights.append(weight)

                        # Calculate edge age/opacity (newer edges more opaque)
                        # Use a simple heuristic: recent connections are more opaque
                        age_alpha = 0.3 + (weight / max(edge_weights + [1.0])) * 0.7  # 0.3 to 1.0 range
                        edge_alphas.append(min(1.0, age_alpha))

                    print(f"[NETWORK VISUALIZATION] Total edges: {len(G.edges())}, Regular: {len(regular_edges)}, Language: {len(language_edges)}")

                    # Draw regular network edges (cyan)
                    if regular_edges:
                        nx.draw_networkx_edges(G, pos, edgelist=regular_edges,
                                             edge_color='cyan', width=1.5,
                                             alpha=0.5, ax=ax)

                    # Draw language-tagged edges (bright red, thicker, with arrows)
                    if language_edges:
                        nx.draw_networkx_edges(G, pos, edgelist=language_edges,
                                             edge_color='red', width=3.0,
                                             alpha=0.9, ax=ax,
                                             style='solid', arrows=True, arrowsize=12)

                    # Add legend for edge types
                    legend_elements = [
                        plt.Line2D([0], [0], color='cyan', linewidth=1.5, alpha=0.5, label='Network Connections'),
                        plt.Line2D([0], [0], color='red', linewidth=3.0, alpha=0.9, label='Language Connections')
                    ]
                    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.7)

                    nx.draw_networkx_labels(G, pos, font_size=6,
                                          font_color='white', ax=ax)
                    
                    ax.set_title(f'Network - {num_orgs} Org, {num_conns} Conn',
                             fontsize=11, fontweight='bold')
                    ax.axis('off')
                    
                    if unified_ax is None:
                        plt.tight_layout()
                        plt.draw()
                        plt.pause(0.001)
                    
                    return {
                        "nodes": num_orgs,
                        "edges": num_conns,
                        "stability": network_data.get("stability", 0.5),
                        "figure": fig if unified_ax is None else None
                    }
        except Exception as e:
            print(f"[Visualization] Error rendering network graph: {e}")
        
        network_data = data.get("network", {})
        return {
            "nodes": network_data.get("organisms", 0),
            "edges": network_data.get("connections", 0),
            "stability": network_data.get("stability", 0.5)
        }



class AgencyFlowVisualizer:
    """Visualizes decision-making agency flow"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config, unified_ax=None):
        """Render agency flow visualization"""
        if not self.renderer.visualizations_enabled:
            agency_data = data.get("agency", {})
            return {"decision_mode": agency_data.get("mode", "unknown"), "agency_balance": 0.6}
        
        try:
            import matplotlib.pyplot as plt
            
            agency_data = data.get("agency", {})
            mode = agency_data.get("mode", "unknown")
            performance = agency_data.get("performance", {})
            
            # Use unified axis if provided, otherwise create own figure
            if unified_ax is not None:
                ax = unified_ax
                ax.clear()
                fig = ax.figure
            else:
                # Legacy: create separate figure
                fig, ax = plt.subplots(figsize=(10, 6))
            
            # Pie chart of decision modes
            labels = ['AI Assisted', 'Manual', 'Deferred']
            sizes = [
                performance.get('ai_adoption_rate', 0) * 100,
                performance.get('manual_rate', 0) * 100,
                performance.get('deferred_rate', 0) * 100
            ]
            
            if sum(sizes) == 0:
                sizes = [33, 33, 34]  # Default
            
            colors = ['cyan', 'magenta', 'yellow']
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                  startangle=90, textprops={'color': 'white', 'fontsize': 12})
            ax.set_title(f'Agency Flow - {mode}', fontsize=11, fontweight='bold')
            
            if unified_ax is None:
                plt.tight_layout()
                plt.draw()
                plt.pause(0.001)
            
            return {"decision_mode": mode, "agency_balance": 0.6, "figure": fig if unified_ax is None else None}
        except Exception as e:
            print(f"[Visualization] Error rendering agency flow: {e}")
        
        agency_data = data.get("agency", {})
        return {"decision_mode": agency_data.get("mode", "unknown"), "agency_balance": 0.6}

class PerformanceMonitorVisualizer:
    """Visualizes system performance metrics"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config, unified_ax=None):
        """Render performance monitor visualization"""
        if not self.renderer.visualizations_enabled:
            return {"cpu_usage": data.get("lattice", {}).get("cpu_usage", 0), "memory_usage": 0.5}
        
        try:
            import matplotlib.pyplot as plt
            
            lattice_data = data.get("lattice", {})
            cpu_usage = lattice_data.get("cpu_usage", 0)
            ram_usage = lattice_data.get("ram_usage", 0)
            
            perf_stats = self.renderer.get_performance_stats()
            fps = perf_stats.get('average_fps', 0)
            
            # Use unified axis if provided, otherwise create own figure
            if unified_ax is not None:
                # Split unified axis into two sub-axes
                import matplotlib.gridspec as gridspec
                ax = unified_ax
                ax.clear()
                gs_sub = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=ax.get_subplotspec(), wspace=0.3)
                ax1 = ax.figure.add_subplot(gs_sub[0])
                ax2 = ax.figure.add_subplot(gs_sub[1])
                fig = ax.figure
            else:
                # Legacy: create separate figure
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Left: Resource usage
            resources = ['CPU %', 'RAM (GB)']
            values = [cpu_usage, ram_usage]
            bars = ax1.bar(resources, values, color=['red', 'blue'], 
                         alpha=0.7, edgecolor='white', linewidth=1)
            ax1.set_ylabel('Usage', fontsize=9)
            ax1.set_title('Resource Usage', fontsize=11)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # Right: Performance
            ax2.barh(['FPS'], [fps], color='green', alpha=0.7, 
                    edgecolor='white', linewidth=1)
            ax2.set_xlabel('Frames Per Second', fontsize=9)
            ax2.set_title('Performance', fontsize=11)
            ax2.set_xlim(0, max(20, fps * 1.2))
            ax2.grid(True, alpha=0.3, axis='x')
            
            if unified_ax is None:
                fig.suptitle('Performance Monitor', fontsize=16, fontweight='bold')
                plt.tight_layout()
                plt.draw()
                plt.pause(0.001)
            else:
                unified_ax.set_title('Performance Monitor', fontsize=12, fontweight='bold')
            
            return {"cpu_usage": cpu_usage, "memory_usage": ram_usage, "figure": fig if unified_ax is None else None}
        except Exception as e:
            print(f"[Visualization] Error rendering performance monitor: {e}")
        
        return {"cpu_usage": data.get("lattice", {}).get("cpu_usage", 0), "memory_usage": 0.5}

class GodOverviewVisualizer:
    """God mode omniscient overview"""
    def __init__(self, renderer):
        self.renderer = renderer
    
    def render(self, data, state, config):
        """Render god overview visualization"""
        if not self.renderer.visualizations_enabled:
            return {"universe_entropy": 0.3, "total_complexity": sum(len(str(v)) for v in data.values())}
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Collect all metrics
            quantum_states = data.get("quantum", {}).get("states", 0)
            particles = data.get("lattice", {}).get("particles", 0)
            generation = data.get("evolution", {}).get("generation", 0)
            organisms = data.get("network", {}).get("organisms", 0)
            fig, axes = plt.subplots(2, 2, figsize=(16, 10))
            axes = axes.flatten()
            
            # 1. Quantum states
            axes[0].bar(['States'], [quantum_states], color='cyan', alpha=0.7)
            axes[0].set_title('Quantum States', fontsize=12)
            axes[0].grid(True, alpha=0.3, axis='y')
            
            # 2. Particles
            axes[1].bar(['Particles'], [particles], color='magenta', alpha=0.7)
            axes[1].set_title('Particles', fontsize=12)
            axes[1].grid(True, alpha=0.3, axis='y')
            
            # 3. Evolution
            axes[2].bar(['Generation'], [generation], color='yellow', alpha=0.7)
            axes[2].set_title('Evolution', fontsize=12)
            axes[2].grid(True, alpha=0.3, axis='y')
            
            # 4. Network
            axes[3].bar(['Organisms'], [organisms], color='green', alpha=0.7)
            axes[3].set_title('Network', fontsize=12)
            axes[3].grid(True, alpha=0.3, axis='y')
            
            fig.suptitle('God Mode - Omniscient Overview', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.draw()
            plt.pause(0.001)
            
            return {"universe_entropy": 0.3, "total_complexity": complexity, "figure": fig}
        except Exception as e:
            print(f"[Visualization] Error rendering god overview: {e}")
        
        return {"universe_entropy": 0.3, "total_complexity": sum(len(str(v)) for v in data.values())}


# Utility functions
def create_reality_renderer(mode: InteractionMode = InteractionMode.OBSERVER,
                          config: Optional[VisualizationConfig] = None) -> RealityRenderer:
    """Create a configured reality renderer"""
    renderer = RealityRenderer(config)
    renderer.set_interaction_mode(mode, "Initial setup")
    return renderer


def render_text_interface(renderer: RealityRenderer, simulation_data: Dict[str, Any]) -> str:
    """
    Render a text-based interface for the simulation

    Useful for console-based interaction
    """
    output = []

    # Header
    output.append("=" * 60)
    output.append(f"[RENDER] REALITY SIMULATOR - {renderer.state.mode.value.upper()} MODE")
    output.append("=" * 60)

    # Simulation status
    quantum = simulation_data.get("quantum", {})
    lattice = simulation_data.get("lattice", {})
    evolution = simulation_data.get("evolution", {})
    network = simulation_data.get("network", {})
    consciousness = simulation_data.get("consciousness", {})

    # Safe formatting function for display values that might be strings
    def safe_display_format(value, format_spec, default=0):
        """Safely format a value for display, using default if not numeric"""
        try:
            if isinstance(value, (int, float)):
                return f"{value:{format_spec}}"
            else:
                return f"{default:{format_spec}}"
        except (ValueError, TypeError):
            return f"{default:{format_spec}}"

    output.append(f"Quantum States: {quantum.get('states', 0)}")
    output.append(f"Particles: {lattice.get('particles', 0)} | CPU: {safe_display_format(lattice.get('cpu_usage', 0), '.1f')}% | RAM: {safe_display_format(lattice.get('ram_usage', 0), '.1f')}GB")
    output.append(f"Evolution: Gen {evolution.get('generation', 0)} | Pop {evolution.get('population_size', 0)} | Best Fitness: {safe_display_format(evolution.get('best_fitness', 0), '.3f')}")
    output.append(f"Network: {network.get('organisms', 0)} orgs | {network.get('connections', 0)} connections | Stability: {safe_display_format(network.get('stability', 0), '.2f')}")

    # Mode-specific information
    if renderer.state.mode == InteractionMode.GOD:
        output.append("\n[GOD MODE] Omniscient Control Available")
        output.append("- Time dilation: {:.1f}x".format(renderer.state.time_dilation))
        output.append("- Use commands: time <factor>, select <entities>, create <type>")

    elif renderer.state.mode == InteractionMode.OBSERVER:
        output.append("\n[OBSERVER MODE] Scientific Analysis")
        output.append("- Data collection active")
        output.append("- Use: analyze <type>, export <format>")

    elif renderer.state.mode == InteractionMode.PARTICIPANT:
        if renderer.state.user_position is not None:
            pos = renderer.state.user_position
            output.append(f"\n[PARTICIPANT MODE] Position: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
        output.append("- Movement: move <x> <y> <z>")
        output.append("- Interaction: interact <target>")

    elif renderer.state.mode == InteractionMode.SCIENTIST:
        output.append("\n[SCIENTIST MODE] Experimental Control")
        output.append("- Parameters adjustable")
        output.append("- Use: set <param> <value>, experiment <name>")

    # Performance
    perf = renderer.get_performance_stats()
    sim_fps = perf.get('simulation_fps', 0)
    fps_display = f"{sim_fps:.1f} FPS" if sim_fps > 0 else f"{perf['average_fps']:.1f} FPS"
    output.append(f"\nPerformance: {fps_display} | Frames: {perf['frames_rendered']}")

    return "\n".join(output)


# Module-level docstring
"""
[RENDER] REALITY RENDERER = SEEING THE UNSEEN

This module makes the invisible visible:
- God Mode: Control reality like a deity
- Observer Mode: Scientific analysis and data
- Participant Mode: Live within the simulation
- Scientist Mode: Experiment and discover

Multiple visualization modalities adapt to user needs.
The bridge between quantum computation and human experience.
"""

