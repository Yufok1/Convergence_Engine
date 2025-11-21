"""
[ROCKET] REALITY SIMULATOR - MAIN INTEGRATION

The complete Reality Simulator bringing together:
🌌 REALITY SIMULATOR MAIN

Entry point for the quantum-genetic consciousness simulation.
Orchestrates all components and provides various interaction modes.
"""

import sys
import os
import time
import signal
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

# Setup logging - try to use centralized config, fallback to basic setup
try:
    # Try importing centralized logging config
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from logging_config import setup_logging, get_logger
    
    # Setup logging if not already configured
    if not logging.getLogger().handlers:
        setup_logging(level=logging.INFO, debug=False, console=False)
    
    logger = get_logger(__name__)
except ImportError:
    # Fallback: basic logging setup if centralized config not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)

# Handle imports for both module and script execution
try:
    from .colors import ColorScheme
except ImportError:
    # If running as script, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from reality_simulator.colors import ColorScheme

# Import other components with fallback
try:
    from .quantum_substrate import QuantumStateManager
    from .subatomic_lattice import create_subatomic_lattice, ResourceMonitor
    from .evolution_engine import EvolutionEngine, create_evolution_engine
    from .symbiotic_network import SymbioticNetwork, create_symbiotic_network
    from .agency import create_agency_router, AgencyMode
    from .reality_renderer import (
        RealityRenderer, InteractionMode, VisualizationConfig,
        create_reality_renderer, render_text_interface
    )
except ImportError as e:
    # Fallback for script execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from reality_simulator.quantum_substrate import QuantumStateManager
        from reality_simulator.subatomic_lattice import create_subatomic_lattice, ResourceMonitor
        from reality_simulator.evolution_engine import EvolutionEngine, create_evolution_engine
        from reality_simulator.symbiotic_network import SymbioticNetwork, create_symbiotic_network
        from reality_simulator.agency import create_agency_router, AgencyMode
        from reality_simulator.reality_renderer import (
            RealityRenderer, InteractionMode, VisualizationConfig,
            create_reality_renderer, render_text_interface
        )
    except ImportError:
        print(f"[ERROR] Import error: {e}")
        print("Make sure all Reality Simulator components are properly installed.")
        sys.exit(1)


def get_project_root() -> str:
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
    # For reality_simulator/main.py, the project root is reality_sim_dir (parent of reality_simulator/)
    # But we check multiple levels to be robust
    
    marker_files = ['config.json', '.git', 'README.md', 'requirements.txt', 'LICENSE']
    
    # Method 1: Check reality_sim_dir's parent (most common case)
    # If script is at reality_simulator/main.py, project root is parent of reality_simulator/
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


class FeedbackController:
    """
    Self-modulation controller that adjusts simulation parameters based on live metrics.

    Provides bounded, hysteresis-controlled feedback loops for:
    - Mutation rate based on fitness trends
    - Network growth rate based on stability/clustering
    - Quantum pruning aggressiveness based on performance
    - Agency bias based on conversation intent
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('feedback', {})
        self.enabled = self.config.get('enabled', False)
        self.interval_frames = self.config.get('interval_frames', 10)
        self.hysteresis_checks = self.config.get('hysteresis_checks', 3)
        self.rate_limit_frames = self.config.get('rate_limit_frames', 30)

        # Knob configurations
        self.knob_configs = self.config.get('knobs', {})

        # Current knob values (initialized to defaults)
        self.current_values = {}
        self._initialize_knob_values()

        # Hysteresis tracking
        self.hysteresis_counters = {knob: 0 for knob in self.knob_configs}
        self.last_change_frames = {knob: 0 for knob in self.knob_configs}

        # Metric history for trend analysis
        self.metric_history = []
        self.max_history_size = 50

        # Conversation intent bias tracking
        self.conversation_biases = {
            'clustering_bias': 0.0,
            'connectivity_growth': 0.0
        }
        self.bias_decay_rate = 0.95  # Bias decays by 5% each message

        status = "DISABLED" if not self.enabled else "ENABLED"
        print(ColorScheme.colorize(f"[FEEDBACK] Controller initialized ({status})", ColorScheme.FEEDBACK))

    def _initialize_knob_values(self):
        """Initialize current knob values to reasonable defaults"""
        defaults = {
            'mutation_rate': 0.01,
            'new_edge_rate': 0.5,
            'clustering_bias': 0.5,
            'quantum_pruning': 0.5
        }

        for knob_name, config in self.knob_configs.items():
            if knob_name in defaults:
                # Start at middle of range
                min_val = config.get('min', defaults[knob_name])
                max_val = config.get('max', defaults[knob_name])
                self.current_values[knob_name] = (min_val + max_val) / 2.0
            else:
                self.current_values[knob_name] = 0.0

    def update(self, frame_count: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update feedback controls based on current metrics.

        Args:
            frame_count: Current simulation frame
            metrics: Current simulation metrics

        Returns:
            Dict of knob changes made
        """
        if not self.enabled:
            return {}

        # Only update at specified intervals
        if frame_count % self.interval_frames != 0:
            return {}

        # Add metrics to history for trend analysis
        self.metric_history.append(metrics.copy())
        if len(self.metric_history) > self.max_history_size:
            self.metric_history.pop(0)

        # Decay conversation biases over time
        self.decay_conversation_biases()

        changes_made = {}

        # Update each knob
        for knob_name in self.knob_configs:
            change = self._update_knob(knob_name, frame_count, metrics)
            if change is not None:
                changes_made[knob_name] = change

        return changes_made

    def _update_knob(self, knob_name: str, frame_count: int, metrics: Dict[str, Any]) -> Optional[float]:
        """
        Update a specific knob with hysteresis and rate limiting.

        Returns the new value if changed, None otherwise.
        """
        # Rate limiting check
        if frame_count - self.last_change_frames[knob_name] < self.rate_limit_frames:
            return None

        # Get knob configuration
        config = self.knob_configs[knob_name]
        step = config.get('step', 0.01)
        min_val = config.get('min', 0.0)
        max_val = config.get('max', 1.0)
        current_val = self.current_values[knob_name]

        # Calculate desired change (to be implemented per knob)
        desired_delta = self._calculate_desired_change(knob_name, metrics)

        if desired_delta == 0:
            self.hysteresis_counters[knob_name] = 0  # Reset hysteresis
            return None

        # Apply hysteresis
        if desired_delta > 0 and self.hysteresis_counters[knob_name] >= 0:
            self.hysteresis_counters[knob_name] += 1
        elif desired_delta < 0 and self.hysteresis_counters[knob_name] <= 0:
            self.hysteresis_counters[knob_name] -= 1
        else:
            self.hysteresis_counters[knob_name] = desired_delta > 0 and 1 or -1

        # Check if hysteresis threshold met
        if abs(self.hysteresis_counters[knob_name]) < self.hysteresis_checks:
            return None

        # Calculate new value with bounds
        new_val = current_val + (desired_delta * step)
        new_val = max(min_val, min(max_val, new_val))

        # Only update if actually changed
        if abs(new_val - current_val) < 1e-10:
            self.hysteresis_counters[knob_name] = 0  # Reset
            return None

        # Update
        self.current_values[knob_name] = new_val
        self.last_change_frames[knob_name] = frame_count
        self.hysteresis_counters[knob_name] = 0  # Reset after change

        return new_val

    def _calculate_desired_change(self, knob_name: str, metrics: Dict[str, Any]) -> float:
        """
        Calculate desired change direction for a knob (+1, 0, -1).

        Implements feedback logic based on simulation metrics.
        """
        if knob_name == 'mutation_rate':
            return self._calculate_mutation_rate_change(metrics)
        elif knob_name == 'new_edge_rate':
            return self._calculate_new_edge_rate_change(metrics)
        elif knob_name == 'clustering_bias':
            return self._calculate_clustering_bias_change(metrics)
        elif knob_name == 'quantum_pruning':
            return self._calculate_quantum_pruning_change(metrics)

        return 0.0

    def _calculate_mutation_rate_change(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate desired mutation rate change.

        Logic:
        - If best-fitness 5-gen slope < -ε or stagnates AND diversity low → +Δ (increase mutation)
        - If fitness rising and stability low → -Δ (decrease mutation to consolidate)
        """
        if len(self.metric_history) < 5:
            return 0.0  # Need history for trend analysis

        # Get recent fitness values
        recent_fitness = [h.get('best_fitness', 0) for h in self.metric_history[-5:]]
        if len(recent_fitness) < 5:
            return 0.0

        # Calculate 5-generation slope
        slope = 0
        if len(recent_fitness) >= 2:
            slope = (recent_fitness[-1] - recent_fitness[0]) / (len(recent_fitness) - 1)

        # Check for stagnation (very small slope)
        epsilon = 0.001
        is_stagnating = abs(slope) < epsilon

        # Calculate fitness diversity (std dev of recent fitness values)
        avg_fitness_values = [h.get('avg_fitness', 0) for h in self.metric_history[-5:]]
        fitness_std = np.std(avg_fitness_values) if avg_fitness_values else 0
        diversity_low = fitness_std < 0.1  # Low diversity threshold

        # Current stability
        stability = metrics.get('stability', 0.0)

        # Decision logic
        if (slope < -epsilon or (is_stagnating and diversity_low)):
            # Fitness declining or stagnating with low diversity - increase mutation
            return 1.0
        elif slope > epsilon and stability < 0.3:
            # Fitness rising but stability low - decrease mutation to consolidate gains
            return -1.0

        return 0.0

    def _calculate_new_edge_rate_change(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate desired new-edge rate change.

        Logic:
        - If stability < Smin or clustering < Cmin → reduce new-edge rate (-Δ)
        - If avg degree > Dmax → reduce new-edge rate (-Δ)
        - If stability > Sgood and clustering > Cgood → increase new-edge rate (+Δ)
        """
        stability = metrics.get('stability', 0.0)
        clustering = metrics.get('avg_clustering', 0.0)
        avg_degree = metrics.get('avg_degree', 0)

        # Thresholds
        stability_min = 0.2
        clustering_min = 0.1
        stability_good = 0.5
        clustering_good = 0.3
        degree_max = 8  # Maximum average degree

        # Base decision logic
        base_change = 0.0
        if stability < stability_min or clustering < clustering_min or avg_degree > degree_max:
            # Network unstable or over-connected - reduce new edge formation
            base_change = -1.0
        elif stability > stability_good and clustering > clustering_good:
            # Network stable and well-clustered - can increase edge formation
            base_change = 1.0

        # Conversation intent influence for connectivity growth
        conversation_connectivity_bias = self.conversation_biases.get('connectivity_growth', 0.0)

        # Combine performance and conversation signals
        total_change = base_change
        if conversation_connectivity_bias > 0.1:  # Only if significant conversation bias
            conversation_influence = 0.3 * conversation_connectivity_bias
            total_change = base_change + conversation_influence

        # Clamp to valid range
        return max(-1.0, min(1.0, total_change))

    def _calculate_clustering_bias_change(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate desired clustering bias change.

        Higher bias means more preference for clustering-increasing connections.
        Incorporates both performance metrics and conversation intent.
        """
        stability = metrics.get('stability', 0.0)
        clustering = metrics.get('avg_clustering', 0.0)

        # Base decision from performance metrics
        base_change = 0.0
        if stability < 0.3 and clustering < 0.2:
            base_change = 1.0  # Increase clustering bias
        elif stability > 0.6 and clustering > 0.4:
            base_change = -1.0  # Reduce clustering bias

        # Conversation intent influence
        conversation_clustering_bias = self.conversation_biases.get('clustering_bias', 0.0)

        # Combine performance and conversation signals
        # Conversation bias acts as a nudge (up to 0.5 weight)
        total_change = base_change
        if conversation_clustering_bias > 0.1:  # Only if significant conversation bias
            conversation_influence = 0.3 * conversation_clustering_bias
            total_change = base_change + conversation_influence

        # Clamp to valid range
        return max(-1.0, min(1.0, total_change))

    def _calculate_quantum_pruning_change(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate desired quantum pruning aggressiveness change.

        Higher value means more aggressive pruning.
        """
        iteration_time = metrics.get('iteration_time_ms', 100.0)
        memory_mb = metrics.get('memory_mb', 0)
        quantum_states = metrics.get('quantum_states', 0)

        # Thresholds from config
        time_threshold = self.config.get('quantum', {}).get('performance_thresholds', {}).get('iteration_time_ms', 10.0)
        memory_threshold = self.config.get('quantum', {}).get('performance_thresholds', {}).get('memory_percentage', 5.0)

        # If performance suffering, increase pruning aggressiveness
        if iteration_time > time_threshold * 1.5 or memory_mb > 1000:  # Rough memory check in MB
            return 1.0
        elif iteration_time < time_threshold * 0.8 and quantum_states < 100:
            # Performance good and not too many states, can relax pruning
            return -1.0

        return 0.0

    def collect_feedback_metrics(self, simulator) -> Dict[str, Any]:
        """
        Collect metrics needed for feedback control decisions.

        Args:
            simulator: RealitySimulator instance

        Returns:
            Dict of metrics for feedback decisions
        """
        metrics = {}

        # Get base simulation data
        sim_data = simulator._collect_simulation_data()

        # Extract basic metrics
        if 'evolution' in sim_data:
            evo = sim_data['evolution']
            metrics['generation'] = evo.get('generation', 0)
            metrics['population_size'] = evo.get('population_size', 0)
            metrics['best_fitness'] = evo.get('best_fitness', 0.0)
            metrics['avg_fitness'] = evo.get('avg_fitness', 0.0)

        if 'network' in sim_data:
            net = sim_data['network']
            metrics['num_organisms'] = net.get('organisms', 0)
            metrics['num_connections'] = net.get('connections', 0)
            metrics['stability'] = net.get('stability', 0.0)
            metrics['connectivity'] = net.get('connectivity', 0.0)

        # Performance metrics
        import time
        import psutil
        current_time = time.time()
        frame_count = getattr(simulator, 'frame_count', 0)

        # Calculate FPS (frames per second)
        if hasattr(simulator, 'start_time') and frame_count > 0:
            elapsed = current_time - simulator.start_time
            metrics['fps'] = frame_count / elapsed if elapsed > 0 else 0
        else:
            metrics['fps'] = 0

        # Iteration time (rough estimate based on target FPS)
        target_fps = simulator.config.get('simulation', {}).get('target_fps', 10.0)
        metrics['target_fps'] = target_fps
        metrics['iteration_time_ms'] = 1000.0 / target_fps if target_fps > 0 else 100.0

        # Memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        metrics['memory_mb'] = memory_info.rss / (1024 * 1024)  # RSS in MB

        # CPU usage (rough estimate)
        metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)

        # Network-specific metrics for clustering analysis
        network = simulator.components.get('network')
        if network and hasattr(network, 'network_graph'):
            import networkx as nx
            G = network.network_graph

            if len(G) > 0:
                # Average degree
                degrees = [d for n, d in G.degree()]
                metrics['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0

                # Clustering coefficient
                try:
                    metrics['avg_clustering'] = nx.average_clustering(G)
                except:
                    metrics['avg_clustering'] = 0.0

                # Network density
                metrics['network_density'] = nx.density(G)
            else:
                metrics['avg_degree'] = 0
                metrics['avg_clustering'] = 0.0
                metrics['network_density'] = 0.0

        # Quantum state count for performance monitoring
        quantum = simulator.components.get('quantum')
        if quantum:
            metrics['quantum_states'] = len(quantum.states)

        # Frame count for timing
        metrics['frame_count'] = frame_count

        return metrics

    def detect_conversation_intent(self, user_message: str):
        """
        Detect conversation intent from user message and update biases.

        Keywords map to bias weights:
        - "integration", "connect", "unite" → increase clustering bias
        - "explore", "grow", "expand", "diverse" → increase connectivity growth
        """
        if not user_message:
            return

        message_lower = user_message.lower()

        # Keyword mappings
        clustering_keywords = ['integration', 'connect', 'unite', 'cluster', 'cooperate', 'together']
        connectivity_keywords = ['explore', 'grow', 'expand', 'diverse', 'network', 'connections']

        # Count keyword matches
        clustering_matches = sum(1 for keyword in clustering_keywords if keyword in message_lower)
        connectivity_matches = sum(1 for keyword in connectivity_keywords if keyword in message_lower)

        # Apply bias updates (scale by number of matches)
        if clustering_matches > 0:
            bias_boost = min(0.2, clustering_matches * 0.05)  # Max 0.2 boost per message
            self.conversation_biases['clustering_bias'] = min(1.0, self.conversation_biases['clustering_bias'] + bias_boost)

        if connectivity_matches > 0:
            bias_boost = min(0.2, connectivity_matches * 0.05)  # Max 0.2 boost per message
            self.conversation_biases['connectivity_growth'] = min(1.0, self.conversation_biases['connectivity_growth'] + bias_boost)

    def decay_conversation_biases(self):
        """Decay conversation biases over time"""
        for bias_type in self.conversation_biases:
            self.conversation_biases[bias_type] *= self.bias_decay_rate
            # Clamp to prevent very small values from accumulating
            if abs(self.conversation_biases[bias_type]) < 0.001:
                self.conversation_biases[bias_type] = 0.0

    def get_conversation_biases(self) -> Dict[str, float]:
        """Get current conversation bias values"""
        return self.conversation_biases.copy()

    def print_status(self):
        """Print current feedback controller status"""
        if not self.enabled:
            print(ColorScheme.colorize("[FEEDBACK] Controller: DISABLED", ColorScheme.WARNING))
            return

        print(ColorScheme.colorize("[FEEDBACK] Controller Status:", ColorScheme.FEEDBACK))
        print(ColorScheme.colorize(f"  Enabled: {self.enabled}", ColorScheme.SUCCESS))
        print(ColorScheme.colorize(f"  Update Interval: Every {self.interval_frames} frames", ColorScheme.INFO))
        print(ColorScheme.colorize(f"  Hysteresis Checks: {self.hysteresis_checks}", ColorScheme.INFO))
        print(ColorScheme.colorize(f"  Rate Limit: {self.rate_limit_frames} frames", ColorScheme.INFO))
        print(ColorScheme.colorize("  Current Knob Values:", ColorScheme.INFO))
        for knob_name, value in self.current_values.items():
            config = self.knob_configs.get(knob_name, {})
            min_val = config.get('min', 'N/A')
            max_val = config.get('max', 'N/A')
            step = config.get('step', 'N/A')
            print(ColorScheme.colorize(f"    {knob_name}: {value:.4f} (range: {min_val}-{max_val}, step: {step})", ColorScheme.CYAN))
        print(ColorScheme.colorize("  Conversation Biases:", ColorScheme.INFO))
        for bias_name, value in self.conversation_biases.items():
            print(ColorScheme.colorize(f"    {bias_name}: {value:.4f}", ColorScheme.MAGENTA))
        print(ColorScheme.colorize(f"  Hysteresis Counters: {self.hysteresis_counters}", ColorScheme.YELLOW))
        print(ColorScheme.colorize(f"  Last Changes: {self.last_change_frames}", ColorScheme.YELLOW))
        print(ColorScheme.colorize(f"  Metric History Size: {len(self.metric_history)}/{self.max_history_size}", ColorScheme.INFO))

    def get_current_values(self) -> Dict[str, float]:
        """Get current knob values"""
        return self.current_values.copy()


class RealitySimulator:
    """
    Complete Reality Simulator integration
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.components = {}
        self.renderer = None
        self.feedback_controller = None
        self.running = False
        self.paused = False
        self.simulation_time = 0.0

        # Performance tracking
        self.start_time = time.time()
        self.frame_count = 0
    
    def pause_simulation(self):
        """Pause the simulation"""
        self.paused = True
    
    def resume_simulation(self):
        """Resume the simulation"""
        self.paused = False

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load simulation configuration"""
        default_config = {
            "simulation": {
                "max_runtime": 3600,  # 1 hour
                "target_fps": 10,     # Slower for potato mode
                "save_interval": 60,  # Save every minute
                "log_level": "INFO"
            },
            "quantum": {
                "initial_states": 10
            },
            "lattice": {
                "particles": 50,
                "prune_threshold": 0.3
            },
            "evolution": {
                "population_size": 100,
                "genotype_length": 32,
                "max_generations": 1000
            },
            "network": {
                "max_connections": 5,
                "max_organisms": 100,
                "resource_pool": 100.0
            },
            "consciousness": {
                "analysis_interval": 10,  # Every 10 frames
                "circuit_breaker_threshold": 0.1
            },
            "agency": {
                "initial_mode": "ai_assisted",
                "confidence_threshold": 0.6
            },
            "rendering": {
                "mode": "observer",
                "resolution": [1920, 1080],
                "frame_rate": 30,
                "text_interface": True,
                "performance_monitoring": True
            }
        }

        # Auto-detect config.json in root if no path provided
        if not config_path:
            # Try current directory first
            if os.path.exists("config.json"):
                config_path = os.path.abspath("config.json")
                print(f"[CONFIG] Auto-detected config.json at {config_path}")
            else:
                # Try project root using robust detection
                project_root = get_project_root()
                project_config = os.path.join(project_root, "config.json")
                if os.path.exists(project_config):
                    config_path = project_config
                    print(f"[CONFIG] Auto-detected config.json at {config_path}")
        
        if config_path:
            # Resolve to absolute path
            if not os.path.isabs(config_path):
                config_path = os.path.abspath(config_path)
            logger.debug(f"Attempting to load config from: {config_path}")
            logger.debug(f"Config file exists: {os.path.exists(config_path)}")
            try:
                if not os.path.exists(config_path):
                    logger.warning(f"Config file {config_path} not found, using defaults")
                else:
                    with open(config_path, 'r') as f:
                        user_config = json.load(f)
                    logger.debug(f"Loaded config with keys: {list(user_config.keys())}")
                    if 'lattice' in user_config:
                        logger.debug(f"Lattice config: {user_config['lattice']}")
                    # Merge with defaults
                    self._merge_configs(default_config, user_config)
                    logger.info(f"Loaded configuration from {config_path}")
                    logger.debug(f"Final lattice particles: {default_config.get('lattice', {}).get('particles', 'NOT SET')}")
            except FileNotFoundError:
                logger.warning(f"Config file {config_path} not found, using defaults")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {config_path}: {e}, using defaults", exc_info=True)

        return default_config

    def _merge_configs(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    def initialize_simulation(self) -> bool:
        """
        Initialize all simulation components

        Returns True if successful, False otherwise
        """
        try:
            print(ColorScheme.colorize("[INIT] Initializing Reality Simulator...", ColorScheme.SUCCESS))

            # 1. Quantum Foundation
            print(ColorScheme.log_component("quantum", "Initializing quantum substrate..."))
            # Get fitness weights and performance thresholds from config
            fitness_weights = self.config.get('quantum', {}).get('fitness_weights')
            performance_thresholds = self.config.get('quantum', {}).get('performance_thresholds')
            quantum_manager = QuantumStateManager(
                fitness_weights=fitness_weights,
                performance_thresholds=performance_thresholds
            )
            self.components['quantum'] = quantum_manager

            # 2. Subatomic Lattice
            print(ColorScheme.colorize("  [LATTICE] Creating subatomic lattice...", ColorScheme.BRIGHT_BLUE))
            lattice = create_subatomic_lattice(
                num_particles=self.config['lattice']['particles'],
                max_states=self.config['lattice']['particles']
            )
            self.components['lattice'] = lattice

            # 3. Genetic Evolution Engine
            print(ColorScheme.log_component("evolution", "Initializing evolution engine..."))
            fitness_targets = {
                'trait_0': 0.8,  # Target high dominance traits
                'trait_1': 0.2,  # Target low interaction traits
                'trait_2': 0.5,  # Target balanced traits
            }
            evolution_engine = create_evolution_engine(
                population_size=self.config['evolution']['population_size'],
                genotype_length=self.config['evolution']['genotype_length'],
                fitness_targets=fitness_targets
            )
            self.components['evolution'] = evolution_engine

            # 4. Symbiotic Network
            print(ColorScheme.log_component("network", "Creating symbiotic network..."))
            # Initialize with some organisms from evolution
            initial_organisms = evolution_engine.population[:10] if evolution_engine.population else []
            network = create_symbiotic_network(
                organisms=initial_organisms,
                max_connections=self.config['network']['max_connections'],
                new_edge_rate=1.0  # Default, will be modified by feedback controller
            )
            # Allow much denser connection topology for high-capacity runs
            try:
                network.max_connections_per_organism = max(
                    getattr(network, "max_connections_per_organism", 5),
                    12
                )
            except Exception:
                pass
            if hasattr(network, "set_new_edge_rate"):
                network.set_new_edge_rate(2.0)  # Increased for faster connection growth
            self.components['network'] = network

            # 6. Agency Router (now system-driven with Event Bus integration)
            print(ColorScheme.log_component("agency", "Setting up agency system..."))
            # Get system references for agency router
            explorer_ref = None  # Will be set if Explorer is integrated
            utm_kernel_ref = None  # Will be set if Djinn Kernel is integrated
            vp_monitor_ref = None  # Will be set if Djinn Kernel is integrated
            network_ref = self.components.get('network')
            breath_engine_ref = None  # Will be set if Explorer is integrated
            
            # Get Event Bus (from UTM Kernel if available, or create new)
            event_bus_ref = None
            if utm_kernel_ref and hasattr(utm_kernel_ref, 'event_bus'):
                event_bus_ref = utm_kernel_ref.event_bus
            elif utm_kernel_ref and hasattr(utm_kernel_ref, 'akashic_ledger'):
                # UTM Kernel might have event bus in its initialization
                try:
                    from kernel.event_driven_coordination import DjinnEventBus
                    event_bus_ref = DjinnEventBus()
                    # Start async processing
                    if hasattr(event_bus_ref.event_processor, 'start_processing'):
                        event_bus_ref.event_processor.start_processing()
                except ImportError:
                    event_bus_ref = None
            
            agency_router = create_agency_router(
                initial_mode=AgencyMode[self.config['agency']['initial_mode'].upper()],
                ai_model="none",
                explorer_controller=explorer_ref,
                utm_kernel=utm_kernel_ref,
                vp_monitor=vp_monitor_ref,
                network=network_ref,
                breath_engine=breath_engine_ref,
                event_bus=event_bus_ref  # NEW: Wire Event Bus
            )
            self.components['agency'] = agency_router
            
            # Wire agency router into network (for connection decisions)
            if network_ref:
                network_ref.agency_router = agency_router

            # 7. Reality Renderer
            print(ColorScheme.log_component("renderer", "Initializing reality renderer..."))
            render_config = VisualizationConfig(
                resolution=tuple(self.config['rendering']['resolution']),
                frame_rate=self.config['rendering']['frame_rate'],
                enable_visualizations=self.config['rendering'].get('enable_visualizations', False)
            )
            renderer = create_reality_renderer(
                mode=InteractionMode[self.config['rendering']['mode'].upper()],
                config=render_config
            )

            # Inject simulation components into renderer
            renderer.inject_simulation_components(
                quantum_manager=quantum_manager,
                lattice=lattice,
                evolution_engine=evolution_engine,
                network=network,
                agency_router=agency_router
            )
            self.components['renderer'] = renderer

            # 8. Feedback Controller
            print(ColorScheme.log_component("feedback", "Initializing feedback controller..."))
            self.feedback_controller = FeedbackController(self.config)

            print(ColorScheme.colorize("[SUCCESS] All components initialized successfully!", ColorScheme.SUCCESS))
            return True

        except Exception as e:
            print(ColorScheme.colorize(f"[ERROR] Initialization failed: {e}", ColorScheme.ERROR))
            import traceback
            traceback.print_exc()
            return False

    def run_simulation(self, max_frames: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the complete simulation loop

        Args:
            max_frames: Maximum frames to run (None = until stopped)

        Returns simulation results
        """
        if not self.components:
            print("[ERROR] Simulation not initialized. Call initialize_simulation() first.")
            return {"error": "not_initialized"}

        print("[TARGET] Starting Reality Simulator...")
        self.running = True
        self.start_time = time.time()

        renderer = self.components['renderer']
        frame_count = 0
        self.frame_count = 0  # Initialize for performance monitoring
        consciousness_checks = 0

        try:
            while self.running:
                if max_frames and frame_count >= max_frames:
                    break
                
                # Check if paused
                pause_signal_file = "data/.simulation_paused"
                if os.path.exists(pause_signal_file):
                    self.paused = True
                
                while self.paused or os.path.exists(pause_signal_file):
                    time.sleep(0.1)  # Sleep while paused
                    if not self.running:
                        break

                # Update simulation components
                self._update_simulation_components()

                # Agency interpretation removed (consciousness feature eliminated)

                # Feedback control (periodic self-modulation)
                if self.feedback_controller:
                    # Collect current metrics for feedback decisions
                    metrics = self.feedback_controller.collect_feedback_metrics(self)
                    # Update controller and get any knob changes
                    knob_changes = self.feedback_controller.update(frame_count, metrics)
                    # Apply knob changes to components
                    self._apply_feedback_changes(knob_changes)

                # Consciousness analysis (periodic)
                if frame_count % self.config['consciousness']['analysis_interval'] == 0:
                    logger.debug(f"Consciousness analysis triggered at frame {frame_count} (every {self.config['consciousness']['analysis_interval']} frames)")
                    self._perform_consciousness_analysis()
                    consciousness_checks += 1

                # Render frame (but skip expensive visualization updates if visualizations enabled)
                # Visualizations will be handled by a separate lightweight viewer process
                if self.config['rendering'].get('enable_visualizations', False):
                    # Only collect data, don't render plots (saves CPU)
                    simulation_data = self._collect_simulation_data()
                    frame_data = {
                        "frame_number": frame_count,
                        "timestamp": time.time(),
                        "mode": self.config['rendering']['mode'],
                        "data": simulation_data
                    }
                else:
                    # Normal rendering when visualizations disabled
                    frame_data = renderer.render_frame()
                
                # Write shared state file for visualization viewer to read
                # This allows both to read from the SAME simulation instance
                # Use absolute path based on project root so both windows can find it
                try:
                    shared_state_file = _get_shared_state_file_path()
                    os.makedirs(os.path.dirname(shared_state_file), exist_ok=True)

                    simulation_data = self._collect_simulation_data()

                    # COMPREHENSIVE DEBUG: Log FULL simulation data being written
                    log_interval = self.config.get('logging', {}).get('shared_state_dump_interval', 0)
                    if log_interval and (frame_count == 1 or frame_count % log_interval == 0):
                        print(f"\n[SHARED STATE WRITE] Frame {frame_count}:")
                        print(f"  Evolution: {simulation_data.get('evolution', {})}")
                        print(f"  Network: {simulation_data.get('network', {})}")
                        print(f"  Consciousness: {simulation_data.get('consciousness', {})}")
                        print(f"  Quantum: {simulation_data.get('quantum', {})}")
                        print(f"  Lattice: {simulation_data.get('lattice', {})}")
                        print(f"  Full keys: {list(simulation_data.keys())}")
                        print(f"  Writing to: {shared_state_file}")

                    # Read existing shared state to preserve conversation data (merge, don't overwrite)
                    existing_state = _read_full_shared_state()
                    conversation_data = None
                    if existing_state and 'conversation' in existing_state:
                        conversation_data = existing_state['conversation']
                    
                    linguistic_data = {}

                    # Create new shared state with merged conversation data
                    # Calculate actual FPS from simulation timing
                    fps = self.frame_count / (time.time() - self.start_time) if self.start_time and self.frame_count > 0 else 0

                    shared_state = {
                        "frame_count": frame_count,
                        "simulation_fps": round(fps, 2),
                        "simulation_time": round(self.simulation_time, 6),  # High precision timing
                        "data": self._make_json_serializable(simulation_data),
                        "visualization_data": self._make_json_serializable(simulation_data),  # Pre-computed for viewer
                        "linguistic_data": linguistic_data,  # Language subgraph stats for visualization
                        "timestamp": round(time.time(), 6),  # Microsecond precision
                        "measurement_precision": 6  # Track precision level
                    }
                    
                    # Only preserve conversation if it's unread (session-based, not persistent)
                    # If conversation was already read, don't persist it
                    if conversation_data and conversation_data.get('unread_by_backend', False):
                        shared_state['conversation'] = conversation_data
                    
                    # Atomic write (read-modify-write pattern)
                    temp_file = shared_state_file + ".tmp"
                    with open(temp_file, 'w') as f:
                        json.dump(shared_state, f, indent=2)
                    
                    # Atomic replace
                    if os.name == 'nt':  # Windows
                        if os.path.exists(shared_state_file):
                            os.remove(shared_state_file)
                        os.rename(temp_file, shared_state_file)
                    else:  # Unix
                        os.replace(temp_file, shared_state_file)
                    
                except Exception as e:
                    # Don't crash if file write fails
                    if frame_count % 100 == 0:  # Only log occasionally
                        print(f"[Warning] Could not write shared state: {e}")

                # Output based on configuration
                if self.config['rendering']['text_interface']:
                    simulation_data = self._collect_simulation_data()
                    text_output = render_text_interface(renderer, simulation_data)

                    # Consciousness interpretation removed

                    # Clear screen and print (for benchmark mode, show updates every 10 frames)
                    if frame_count % 10 == 0 or frame_count == 1:
                        # Use ANSI escape codes to clear and move cursor to top
                        print("\033[2J\033[H", end="")  # Clear screen, move to top
                        print(text_output, flush=True)

                frame_count += 1
                self.frame_count = frame_count  # Update for performance monitoring

                # Performance monitoring (only check every 10 frames to reduce spam)
                if self.config['rendering']['performance_monitoring'] and frame_count % 10 == 0:
                    self._monitor_performance()

                # Frame rate limiting
                target_frame_time = 1.0 / self.config['simulation']['target_fps']
                elapsed = time.time() - self.start_time
                if elapsed < frame_count * target_frame_time:
                    sleep_time = (frame_count * target_frame_time) - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                # Additional delay if specified (for CPU sharing with other processes)
                if hasattr(self, 'frame_delay') and self.frame_delay > 0:
                    time.sleep(self.frame_delay)

        except KeyboardInterrupt:
            print("\n[STOP]  Simulation interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Simulation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False

        # Final results
        total_time = time.time() - self.start_time
        final_state = self._collect_simulation_data()
        
        # Ensure all values are JSON serializable
        results = {
            "frames_simulated": frame_count,
            "total_time": float(total_time),
            "avg_fps": float(frame_count / total_time if total_time > 0 else 0),
            "consciousness_checks": consciousness_checks,
            "final_state": self._make_json_serializable(final_state)
        }

        print(f"\n[FINISH] Simulation complete! {frame_count} frames in {total_time:.1f}s")
        return results

    def _update_simulation_components(self):
        """Update all simulation components for one time step"""
        # Update quantum substrate (create new quantum states)
        if 'quantum' in self.components:
            quantum_manager = self.components['quantum']
            # Create a new quantum state occasionally
            import random
            if random.random() < 0.1:  # 10% chance each frame
                state_id = f"quantum_{len(quantum_manager.states)}"
                quantum_manager.create_state(state_id, num_basis_states=4,
                                           basis_labels=['up', 'down', 'strange', 'charm'])
            
            # Adaptive pruning: Check performance and prune if needed
            prune_check_interval = self.config.get('quantum', {}).get('prune_check_interval', 50)
            # Use frame_count if available (tracked in run_simulation), otherwise use call counter
            # Note: frame_count is incremented AFTER _update_simulation_components, so we check previous frame
            if hasattr(self, 'frame_count'):
                # Check if we should prune based on previous frame count (will increment after this update)
                frame_count_for_check = self.frame_count + 1
            else:
                # Fallback: track internally
                if not hasattr(quantum_manager, '_prune_check_counter'):
                    quantum_manager._prune_check_counter = 0
                quantum_manager._prune_check_counter += 1
                frame_count_for_check = quantum_manager._prune_check_counter
            
            if frame_count_for_check % prune_check_interval == 0:
                should_prune, optimal_count, reason = quantum_manager.should_prune()
                if should_prune:
                    removed = quantum_manager.prune_low_fitness_states(target_count=optimal_count)
                    if removed > 0:
                        # Log pruning activity (occasionally, not every prune)
                        if frame_count_for_check % (prune_check_interval * 5) == 0:
                            print(ColorScheme.colorize(f"[QUANTUM PRUNING] Removed {removed} low-fitness states. Reason: {reason}", ColorScheme.QUANTUM))
                            print(f"  Optimal count: {optimal_count}, Current: {len(quantum_manager.states)}")

        # Update lattice (particles, pruning)
        if 'lattice' in self.components:
            particles, approximator, monitor = self.components['lattice']
            # Quantum state approximation (ResourceMonitor runs in background thread)
            particles = approximator.approximate_superposition(particles)
            self.components['lattice'] = (particles, approximator, monitor)

        # Update evolution
        if 'evolution' in self.components:
            evolution = self.components['evolution']
            gen_before = evolution.generation
            logger.debug(f"About to call evolve_generation() on generation {gen_before}")
            evolution.evolve_generation()
            gen_after = evolution.generation
            logger.debug(f"After evolve_generation(): {gen_before} -> {gen_after}")
            # Debug: Log generation progression
            if gen_after != gen_before + 1:
                logger.debug(f"Generation jump: {gen_before} -> {gen_after} (expected {gen_before + 1})")

        # Update network
        if 'network' in self.components:
            network = self.components['network']
            network.update_network()

            # Add new organisms from evolution
            evolution = self.components.get('evolution')
            if evolution and evolution.population:
                # Add some evolved organisms to network periodically
                max_organisms = self.config['network'].get('max_organisms', 100)  # Default 100, configurable
                if len(network.organisms) < max_organisms:  # Keep network growing up to configured limit
                    new_orgs = evolution.population[-5:]  # Most recent
                    for org in new_orgs:
                        if org.species_id not in network.organisms:
                            network.add_organism(org)


    def _perform_consciousness_analysis(self):
        """Perform consciousness emergence analysis"""
        consciousness = self.components.get('consciousness')
        network = self.components.get('network')
        agency = self.components.get('agency')

        if consciousness and network:
            try:
                result = consciousness.analyze_consciousness(network)
                score = result.get('overall_score', 0)
                print(f"[CONSCIOUSNESS] Analysis completed - Score: {score:.3f}, Reason: {result.get('reason', 'Unknown')}")


                # Consciousness emergence messages disabled - too robotic
                # if score > 0.5:
                #     print(f"\n[CONSCIOUSNESS] CONSCIOUSNESS EMERGENCE DETECTED: {score:.3f}")
                #     print(f"   Reason: {result.get('reason', 'Unknown')}")

            except Exception as e:
                import traceback
                print(f"Consciousness analysis error: {e}")
                traceback.print_exc()

    def _apply_feedback_changes(self, knob_changes: Dict[str, float]):
        """Apply feedback controller knob changes to simulation components"""
        if not knob_changes:
            return

        # Fetch components once for use across knobs
        evolution = self.components.get('evolution')
        network = self.components.get('network')
        quantum = self.components.get('quantum')

        # Apply mutation rate changes to evolution engine
        if 'mutation_rate' in knob_changes:
            if evolution and hasattr(evolution, 'set_mutation_rate'):
                new_rate = knob_changes['mutation_rate']
                evolution.set_mutation_rate(new_rate)
                print(ColorScheme.log_component("feedback", f"Mutation rate adjusted to {new_rate:.4f}"))

        # Apply new edge rate changes to symbiotic network
        if 'new_edge_rate' in knob_changes:
            if network and hasattr(network, 'set_new_edge_rate'):
                new_rate = knob_changes['new_edge_rate']
                network.set_new_edge_rate(new_rate)
                print(ColorScheme.log_component("feedback", f"New edge rate adjusted to {new_rate:.2f}"))

        # Apply quantum pruning aggressiveness changes
        if 'quantum_pruning' in knob_changes:
            if quantum and hasattr(quantum, 'set_pruning_aggressiveness'):
                aggressiveness = knob_changes['quantum_pruning']
                quantum.set_pruning_aggressiveness(aggressiveness)
                print(ColorScheme.log_component("feedback", f"Quantum pruning aggressiveness set to {aggressiveness:.2f}"))

        # TODO: Implement clustering bias adjustments
        if 'clustering_bias' in knob_changes:
            # Apply clustering bias to network (triangle closure preference)
            if network and hasattr(network, 'set_clustering_bias'):
                clustering_bias = knob_changes['clustering_bias']
                network.set_clustering_bias(clustering_bias)
                print(ColorScheme.log_component("feedback", f"Clustering bias adjusted to {clustering_bias:.2f}"))

    def _collect_simulation_data(self) -> Dict[str, Any]:
        """Collect current state from all components"""
        data = {}

        # Quantum
        quantum = self.components.get('quantum')
        if quantum:
            # quantum is a QuantumStateManager with a states dict
            data['quantum'] = {
                'states': len(quantum.states)
            }

        # Lattice
        lattice = self.components.get('lattice')
        if lattice:
            particles, approximator, monitor = lattice
            usage = monitor.get_current_usage()


            # Serialize particle positions for visualization
            particle_positions = []
            if particles and len(particles) > 0:
                for p in particles:
                    if hasattr(p, 'position'):
                        pos = p.position
                        if isinstance(pos, np.ndarray):
                            # Convert to list and take first 2-3 dimensions
                            pos_list = pos.tolist()
                            if len(pos_list) >= 2:
                                particle_positions.append(pos_list[:2])  # 2D projection
                            elif len(pos_list) == 1:
                                particle_positions.append([pos_list[0], 0.0])  # 1D -> 2D
            
            data['lattice'] = {
                'particles': len(particles) if particles else 0,
                'cpu_usage': usage.get('cpu_percent', 0),
                'ram_usage': usage.get('ram_gb', 0),
                'particle_positions': particle_positions  # For visualization
            }

        # Evolution
        evolution = self.components.get('evolution')
        if evolution:
            # Read generation directly from evolution component (not hardcoded)
            # This MUST read the actual current generation, not a default value
            gen = evolution.generation if hasattr(evolution, 'generation') else 0
            
            # Debug: log what we're actually reading (only first time and every 100 frames)
            if not hasattr(self, '_gen_debug_count'):
                self._gen_debug_count = 0
            self._gen_debug_count += 1
            if self._gen_debug_count == 1 or self._gen_debug_count % 100 == 0:
                logger.debug(f"Reading evolution generation: {gen} (type: {type(gen)}, hasattr: {hasattr(evolution, 'generation')})")
            
            data['evolution'] = {
                'generation': int(gen),  # Ensure it's an integer, read dynamically from component
                'population_size': len(evolution.population) if evolution.population else 0,
                'best_fitness': evolution.get_best_organism().fitness if evolution.population else 0,
                'avg_fitness': np.mean([org.fitness for org in evolution.population]) if evolution.population else 0
            }

        # Network
        network = self.components.get('network')
        if network:
            # Serialize network graph structure for visualization
            graph_edges = []
            node_id_map = {}  # Map string/node IDs to integer indices
            next_index = 0
            
            if hasattr(network, 'network_graph'):
                for edge in network.network_graph.edges():
                    # Handle both string and integer node IDs
                    node1, node2 = edge[0], edge[1]
                    
                    # Map to integer indices for visualization
                    if node1 not in node_id_map:
                        node_id_map[node1] = next_index
                        next_index += 1
                    if node2 not in node_id_map:
                        node_id_map[node2] = next_index
                        next_index += 1
                    
                    graph_edges.append([node_id_map[node1], node_id_map[node2]])
            
            # Count language connections
            language_connections = 0
            persistent_edges = 0
            if hasattr(network, 'language_subgraph') and network.language_subgraph:
                language_connections = len(network.language_subgraph.linguistic_edges)
                persistent_edges = len(network.language_subgraph.get_persistent_edges())

            data['network'] = {
                'organisms': len(network.organisms),
                'connections': len(network.connections),
                'stability': network.metrics.stability_index,
                'connectivity': network.metrics.connectivity,
                'graph_edges': graph_edges,  # For visualization (integer indices)
                'language_connections': language_connections,  # Language-tagged connections
                'persistent_edges': persistent_edges  # Persistent language edges
            }

        # Consciousness
        consciousness = self.components.get('consciousness')
        if consciousness:
            logger.debug(f"Consciousness metrics_history length: {len(consciousness.metrics_history)}")
            last_analysis = consciousness.metrics_history[-1] if consciousness.metrics_history else {}
            logger.debug(f"Last analysis keys: {list(last_analysis.keys()) if last_analysis else 'None'}")
            if last_analysis and 'overall_score' in last_analysis:
                logger.debug(f"Last consciousness score: {last_analysis['overall_score']:.3f}")
            # Convert ConsciousnessMetrics object to dict if present
            if 'metrics' in last_analysis and hasattr(last_analysis['metrics'], '__dict__'):
                metrics_obj = last_analysis['metrics']
                last_analysis = last_analysis.copy()  # Don't modify original
                last_analysis['metrics'] = {
                    'integrated_information': metrics_obj.integrated_information,
                    'self_reference_strength': metrics_obj.self_reference_strength,
                    'qualia_complexity': metrics_obj.qualia_complexity,
                    'information_integration': metrics_obj.information_integration,
                    'causal_density': metrics_obj.causal_density,
                    'emergence_confidence': metrics_obj.emergence_confidence,
                    'overall_score': metrics_obj.get_overall_consciousness_score()
                }
            data['consciousness'] = {
                'last_analysis': last_analysis,
                'trend': consciousness.get_consciousness_trend()
            }

        # Agency
        agency = self.components.get('agency')
        if agency:
            agency_data = {
                'mode': agency.current_mode.value,
                'performance': agency.performance.get_summary()
            }


            data['agency'] = agency_data

        return data

    def _make_json_serializable(self, obj):
        """Recursively convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif hasattr(obj, '__dict__'):
            # Convert objects with __dict__ to dict
            return self._make_json_serializable(obj.__dict__)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            # Fallback: convert to string
            return str(obj)

    def _monitor_performance(self):
        """Monitor and report performance"""
        current_time = time.time()
        elapsed = current_time - self.start_time

        if elapsed > 0:
            fps = self.frame_count / elapsed
            if fps < self.config['simulation']['target_fps'] * 0.8:  # Below 80% of target
                print(f"\n[WARNING]  Performance warning: {fps:.1f} FPS (target: {self.config['simulation']['target_fps']})")

    def handle_user_command(self, command: str, args: Dict[str, Any]) -> str:
        """
        Handle user commands during simulation

        Returns response message
        """
        renderer = self.components.get('renderer')

        if not renderer:
            return "Renderer not available"

        # Parse command
        if command == "mode":
            mode_name = args.get('mode', '').upper()
            if hasattr(InteractionMode, mode_name):
                mode = InteractionMode[mode_name]
                renderer.set_interaction_mode(mode, "User command")
                return f"Switched to {mode.value} mode"
            else:
                return f"Unknown mode: {mode_name}"

        elif command == "time":
            dilation = args.get('dilation', 1.0)
            renderer.state.time_dilation = float(dilation)
            return f"Time dilation set to {dilation}x"

        elif command == "status":
            data = self._collect_simulation_data()
            return json.dumps(data, indent=2)

        elif command == "stop":
            self.running = False
            return "Stopping simulation..."

        else:
            # Pass to renderer input handling
            response = renderer.handle_user_input(command, args)
            return json.dumps(response, indent=2)

    def save_state(self, filepath: str = "reality_simulator_save.json"):
        """Save current simulation state"""
        state = {
            "config": self.config,
            "simulation_time": self.simulation_time,
            "frame_count": self.frame_count,
            "components_state": self._collect_simulation_data()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"[SAVE] Simulation state saved to {filepath}")

    def load_state(self, filepath: str = "reality_simulator_save.json"):
        """Load simulation state"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            self.config = state.get('config', self.config)
            self.simulation_time = state.get('simulation_time', 0)
            self.frame_count = state.get('frame_count', 0)

            print(f"[FOLDER] Simulation state loaded from {filepath}")
            return True

        except FileNotFoundError:
            print(f"Save file {filepath} not found")
            return False
        except json.JSONDecodeError:
            print(f"Invalid save file {filepath}")
            return False

def _read_shared_simulation_state() -> Optional[Dict[str, Any]]:
    """Read simulation state from shared file (written by backend simulation)"""
    try:
        # Use absolute path based on project root so both windows can find it
        # Get project root using robust detection
        project_root = get_project_root()
        shared_state_file = os.path.join(project_root, "data", ".shared_simulation_state.json")
        
        if os.path.exists(shared_state_file):
            with open(shared_state_file, 'r') as f:
                shared_state = json.load(f)
                # Check if data is recent (within last 60 seconds - increased for very slow systems)
                timestamp = shared_state.get('timestamp', 0)
                age = time.time() - timestamp
                if age < 60.0:  # Increased from 10s to 60s for slow systems
                    data = shared_state.get('data', {})
                    frame_count = shared_state.get('frame_count', 0)

                    # COMPREHENSIVE DEBUG: Log what we're reading
                    print(ColorScheme.colorize(f"\n[SHARED STATE READ] File: {shared_state_file}", ColorScheme.SHARED_STATE))
                    print(f"  Timestamp age: {age:.2f}s, frame: {frame_count}")
                    print(f"  Evolution read: {data.get('evolution', {})}")
                    print(f"  Network read: {data.get('network', {})}")
                    print(f"  Consciousness read: {data.get('consciousness', {})}")
                    print(f"  Data keys: {list(data.keys()) if data else 'NO DATA'}")

                    return data
                else:
                    logger.debug(f"Shared state is stale (age: {age:.1f}s, threshold: 60.0s)")
                    return None
        else:
            logger.debug(f"Shared state file not found at: {shared_state_file}")
            # List what's in the data directory for debugging
            data_dir = os.path.join(project_root, "data")
            if os.path.exists(data_dir):
                files = os.listdir(data_dir)
                logger.debug(f"Files in data directory: {files}")
            else:
                logger.debug(f"Data directory does not exist: {data_dir}")
        return None
    except Exception as e:
        logger.debug(f"Error reading shared state: {e}", exc_info=True)
        return None


def _get_shared_state_file_path() -> str:
    """Get the path to the shared state file"""
    project_root = get_project_root()
    shared_state_dir = os.path.join(project_root, "data")
    return os.path.join(shared_state_dir, ".shared_simulation_state.json")


def _read_full_shared_state() -> Optional[Dict[str, Any]]:
    """Read the full shared state file including conversation data"""
    try:
        shared_state_file = _get_shared_state_file_path()
        if os.path.exists(shared_state_file):
            # Use file locking to prevent conflicts
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with open(shared_state_file, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.1)  # Brief delay before retry
                        continue
                    else:
                        logger.debug(f"Error reading shared state after {max_retries} attempts: {e}", exc_info=True)
                        return None
        return None
    except Exception as e:
        logger.debug(f"Error reading full shared state: {e}", exc_info=True)
        return None




def create_argument_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(description="Reality Simulator")

    parser.add_argument("--config", "-c", type=str,
                       help="Configuration file path")

    parser.add_argument("--frames", "-f", type=int,
                       help="Maximum frames to simulate")

    parser.add_argument("--num_runs", "-n", type=int, default=10,
                       help="Number of runs for statistical testing (consciousness_test mode)")

    parser.add_argument("--mode", "-m", type=str, default="observer",
                       choices=["god", "observer", "participant", "scientist", "consciousness_test"],
                       help="Initial interaction mode")

    parser.add_argument("--no-text", action="store_true",
                       help="Disable text interface output")

    parser.add_argument("--no-color", action="store_true",
                       help="Disable ANSI color output")

    parser.add_argument("--save", "-s", type=str,
                       help="Save simulation state to file")

    parser.add_argument("--load", "-l", type=str,
                       help="Load simulation state from file")

    parser.add_argument("--delay", "-d", type=float, default=0.0,
                       help="Delay in seconds between simulation frames (reduces CPU usage)")

    return parser




def _write_simulation_data_to_shared_state(simulation_data: Dict[str, Any], frame_count: int) -> bool:
    """
    Write current simulation data to shared state file for visualization viewer.

    This is a simplified version for the consciousness test that doesn't handle conversation data.
    """
    try:
        shared_state_file = _get_shared_state_file_path()
        os.makedirs(os.path.dirname(shared_state_file), exist_ok=True)

        # Create shared state structure similar to run_simulation
        # Use a simple JSON-compatible version since we don't have access to simulator._make_json_serializable
        def make_json_serializable(obj):
            """Simple JSON serialization for consciousness test"""
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
            "simulation_time": round(time.time(), 6),  # Use current time as simulation time
            "data": make_json_serializable(simulation_data),
            "visualization_data": make_json_serializable(simulation_data),
            "timestamp": round(time.time(), 6),
            "measurement_precision": 6
        }

        # Write to file atomically
        temp_file = shared_state_file + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(shared_state, f, indent=2)

        # Atomic move
        import shutil
        shutil.move(temp_file, shared_state_file)

        return True

    except Exception as e:
        if frame_count % 10 == 0:  # Only log occasionally
            print(f"[WARNING] Could not write shared state for consciousness test: {e}")
        return False


def run_consciousness_test(simulator: RealitySimulator, generations: int = 15, num_runs: int = 10, language_enabled: bool = True) -> Dict[str, float]:
    """
    Run single consciousness test and return final metrics

    Returns final values for statistical analysis across multiple independent runs.
    """
    # Disable language learning if requested (language learning removed)
    if not language_enabled:
        pass  # Language learning feature removed

    try:
        # Reset simulator
        simulator.initialize_simulation()

        phi_scores = []
        connections_list = []
        metrics_list = []

        for gen in range(generations):
            # Run one generation
            simulator._update_simulation_components()

            # Collect simulation data for agency interpretation
            sim_data = simulator._collect_simulation_data()

            # Agency interpretation removed (consciousness feature eliminated)
            network_obj = simulator.components.get('network')
            
            # Extract metrics from simulation data
            consciousness = sim_data.get('consciousness', {})
            phi_score = consciousness.get('phi', 0.0)
            connections = len(network_obj.graph.edges()) if hasattr(network_obj, 'graph') else 0
            metrics = sim_data.get('network_metrics', {})

            phi_scores.append(phi_score)
            connections_list.append(connections)
            metrics_list.append(metrics)

            # Write to shared state for visualization viewer
            print(f"[CONSCIOUSNESS TEST] Writing shared state for generation {gen}")
            success = _write_simulation_data_to_shared_state(sim_data, gen)
            print(f"[CONSCIOUSNESS TEST] Shared state write {'successful' if success else 'failed'}")

        # Return final values (from last generation)
        final_metrics = metrics_list[-1] if metrics_list else {}
        return {
            'phi': phi_scores[-1] if phi_scores else 0.0,
            'connections': connections_list[-1] if connections_list else 0,
            'clustering_coeff': final_metrics.get('clustering_coeff', 0.0),
            'avg_path_length': final_metrics.get('avg_path_length', float('inf')),
            'connection_growth': final_metrics.get('connection_growth', 0.0),
            'linguistic_integration': final_metrics.get('linguistic_integration', 0.0)
        }

    except Exception as e:
        print(f"[ERROR] Consciousness test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'phi': 0.0,
            'connections': 0,
            'clustering_coeff': 0.0,
            'avg_path_length': float('inf'),
            'connection_growth': 0.0,
            'linguistic_integration': 0.0
        }


def run_consciousness_test_continuous(simulator: RealitySimulator, max_generations: int = 100):
    """
    Run consciousness test continuously until interrupted, updating visualizations
    """
    print(f"[CONSCIOUSNESS TEST] Starting continuous consciousness test mode...")
    print(f"[CONSCIOUSNESS TEST] Will run up to {max_generations} generations or until interrupted")
    print(f"[CONSCIOUSNESS TEST] Language learning: ENABLED")
    print(f"[CONSCIOUSNESS TEST] Visualizations: ENABLED")
    print(f"[CONSCIOUSNESS TEST] Press Ctrl+C to stop and view results")

    # Initialize simulation
    simulator.initialize_simulation()

    phi_history = []
    connections_history = []

    try:
        for gen in range(max_generations):
            start_time = time.time()

            # Run one generation
            simulator._update_simulation_components()

            # Collect simulation data for agency interpretation
            sim_data = simulator._collect_simulation_data()

            # Agency interpretation removed (consciousness feature eliminated)
            network_obj = simulator.components.get('network')



            # Re-collect data after agency interpretation
            sim_data = simulator._collect_simulation_data()
            consciousness = sim_data.get('consciousness', {})

            # Force Phi calculation
            network_obj = simulator.components.get('network')
            agency_obj = simulator.components.get('agency')
            
            # Simplified metric collection without consciousness detector
            phi_score = 0.0
            connections = len(network_obj.graph.edges()) if hasattr(network_obj, 'graph') else 0

            # Store metrics
            phi_history.append(phi_score)
            connections_history.append(connections)

            # Debug: Show language connections
            language_connections = len(getattr(network_obj, 'language_connections', set()))
            if gen % 5 == 0 or gen == 0:  # Every 5 generations
                logger.debug(f"Gen {gen}: Total connections = {connections}, Language connections = {language_connections}")

            # Write to shared state for visualizations
            _write_simulation_data_to_shared_state(sim_data, gen)

            generation_time = time.time() - start_time

            # Progress update every 5 generations or on first/last
            if gen == 0 or gen == max_generations - 1 or gen % 5 == 0:
                print(f"[CONSCIOUSNESS TEST] Generation {gen+1}/{max_generations}: "
                      f"Phi = {phi_score:.4f}, Connections = {connections}, "
                      f"Time = {generation_time:.2f}s")

            # Small delay to prevent overwhelming
            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n[CONSCIOUSNESS TEST] Interrupted after {len(phi_history)} generations")

    # Final statistics
    if phi_history:
        avg_phi = sum(phi_history) / len(phi_history)
        avg_connections = sum(connections_history) / len(connections_history)
        max_phi = max(phi_history)
        final_phi = phi_history[-1]

        print(f"\n[CONSCIOUSNESS TEST] Results after {len(phi_history)} generations:")
        print(f"[CONSCIOUSNESS TEST] Average Phi: {avg_phi:.4f}")
        print(f"[CONSCIOUSNESS TEST] Final Phi: {final_phi:.4f}")
        print(f"[CONSCIOUSNESS TEST] Max Phi: {max_phi:.4f}")
        print(f"[CONSCIOUSNESS TEST] Average Connections: {avg_connections:.1f}")
        print(f"[CONSCIOUSNESS TEST] Final Connections: {connections_history[-1]}")

        # Language effectiveness assessment
        phi_improvement = final_phi - phi_history[0] if len(phi_history) > 1 else 0
        connection_growth = connections_history[-1] - connections_history[0] if len(connections_history) > 1 else 0

        print(f"[CONSCIOUSNESS TEST] Phi improvement: {phi_improvement:+.4f}")
        print(f"[CONSCIOUSNESS TEST] Connection growth: {connection_growth:+d}")

        if phi_improvement > 0.01:
            print(f"[CONSCIOUSNESS TEST] SUCCESS: Language learning appears effective")
        elif phi_improvement > 0:
            print(f"[CONSCIOUSNESS TEST] WEAK: Small effect detected, may need more generations")
        else:
            print(f"[CONSCIOUSNESS TEST] NONE: No significant consciousness increase detected")

    print("[CONSCIOUSNESS TEST] Test complete. Visualizations should show the evolution.")


def run_statistical_consciousness_test(simulator: RealitySimulator, num_runs: int = 20, generations: int = 15) -> None:
    """
    Run proper statistical test: Compare language learning effects across many independent runs
    """
    import scipy.stats as stats
    import numpy as np

    print(f"[STATISTICAL TEST] Running {num_runs} independent tests for each condition...")
    print(f"   Each test: {generations} generations")
    print()

    # Collect results from all runs
    results_with_language = []
    results_without_language = []

    # Run tests WITH language learning
    print(f"Running {num_runs} tests WITH language learning...")
    for run in range(num_runs):
        print(f"  Run {run + 1}/{num_runs} with language...")
        result = run_consciousness_test(simulator, generations, language_enabled=True)
        results_with_language.append(result)

    # Run tests WITHOUT language learning
    print(f"\nRunning {num_runs} tests WITHOUT language learning...")
    for run in range(num_runs):
        print(f"  Run {run + 1}/{num_runs} without language...")
        result = run_consciousness_test(simulator, generations, language_enabled=False)
        results_without_language.append(result)

    print(f"\n[SUCCESS] Completed {num_runs} runs for each condition")
    print()

    # Calculate statistics for each metric
    print("[STATISTICAL RESULTS]:")
    print("   Metric              | With Language   | Without Language | P-value | Significant?")
    print("   --------------------|-----------------|------------------|---------|-------------")

    metrics = ['connections', 'clustering_coeff', 'avg_path_length', 'connection_growth', 'linguistic_integration']

    for metric in metrics:
        with_vals = [r[metric] for r in results_with_language]
        without_vals = [r[metric] for r in results_without_language]

        # Filter out infinite path lengths
        if metric == 'avg_path_length':
            with_vals = [x for x in with_vals if x != float('inf')]
            without_vals = [x for x in without_vals if x != float('inf')]

        if not with_vals or not without_vals:
            print(f"   {metric:<18} | N/A             | N/A              | N/A     | NO DATA")
            continue

        mean_with = np.mean(with_vals)
        mean_without = np.mean(without_vals)
        std_with = np.std(with_vals, ddof=1) if len(with_vals) > 1 else 0
        std_without = np.std(without_vals, ddof=1) if len(without_vals) > 1 else 0

        # Perform t-test
        try:
            t_stat, p_value = stats.ttest_ind(with_vals, without_vals, equal_var=False)
        except:
            p_value = 1.0

        significant = "YES" if p_value < 0.05 else "NO"

        # Format based on metric type
        if metric in ['connections', 'linguistic_integration']:
            print(f"   {metric:<18} | {mean_with:>7.1f}±{std_with:>4.1f}   | {mean_without:>7.1f}±{std_without:>4.1f}   | {p_value:>6.4f} | {significant}")
        elif metric == 'avg_path_length':
            print(f"   {metric:<18} | {mean_with:>7.2f}±{std_with:>4.2f}   | {mean_without:>7.2f}±{std_without:>4.2f}   | {p_value:>6.4f} | {significant}")
        else:
            print(f"   {metric:<18} | {mean_with:>7.3f}±{std_with:>4.3f}   | {mean_without:>7.3f}±{std_without:>4.3f}   | {p_value:>6.4f} | {significant}")

    print()

    # Overall conclusion
    significant_metrics = sum([
        1 for metric in metrics
        if stats.ttest_ind(
            [r[metric] for r in results_with_language],
            [r[metric] for r in results_without_language],
            equal_var=False
        )[1] < 0.05
    ])

    print("[CONCLUSION]:")
    if significant_metrics >= 2:
        print(f"   LANGUAGE LEARNING WORKS: {significant_metrics}/{len(metrics)} metrics show statistically significant effects")
        print("   Effects are reproducible across independent runs")
        print("   Language genuinely affects network structure and efficiency")
    elif significant_metrics == 1:
        print(f"   MIXED RESULTS: Only {significant_metrics}/{len(metrics)} metric shows significant effects")
        print("   Some evidence of language impact, but weak")
        print("   May need more runs or different metrics")
    else:
        print(f"   NO SIGNIFICANT EFFECTS: {significant_metrics}/{len(metrics)} metrics show statistical significance")
        print("   Language learning effects appear to be noise/random variation")
        print("   Hypothesis not supported by statistical evidence")

    print()
    print("[NEXT STEPS]:")
    if significant_metrics >= 2:
        print("   1. Language learning confirmed to affect network structure")
        print("   2. Focus on why Phi doesn't capture these effects")
        print("   3. Investigate scaling effects (longer runs, larger networks)")
    else:
        print("   1. Investigate why language learning doesn't create measurable effects")
        print("   2. Debug word-to-organism mapping and connection creation")
        print("   3. Consider alternative approaches to linguistic consciousness")


def log_multidom_metrics(network, generation):
    """
    Calculate and log multi-domain consciousness metrics.
    Call this right after consciousness analysis.
    """

    # Metric 1: Vocabulary Coherence
    # Measure how much organisms share vocabulary
    try:
        vocab_sets = []
        for org in network.organisms:
            if hasattr(org, 'vocabulary'):
                vocab_sets.append(set(org.vocabulary))

        if len(vocab_sets) > 1:
            intersections = 0
            unions = 0
            for i in range(len(vocab_sets)):
                for j in range(i+1, len(vocab_sets)):
                    intersect = len(vocab_sets[i] & vocab_sets[j])
                    union = len(vocab_sets[i] | vocab_sets[j])
                    intersections += intersect
                    unions += union

            coherence = intersections / unions if unions > 0 else 0
            print(f"[MULTIDOM_METRICS] Gen {generation} - Vocabulary_Coherence: {coherence:.4f}")
    except Exception as e:
        print(f"[MULTIDOM_METRICS] Warning: Vocabulary coherence calc failed: {e}")

    # Metric 2: Cross-Domain Integration
    # Percentage of connections that bridge different semantic domains
    try:
        cross_domain_edges = 0
        total_edges = 0

        for connection in network.connections:
            total_edges += 1
            org_a = connection.source
            org_b = connection.target

            # Check if organisms have domain tags
            domain_a = getattr(org_a, 'primary_domain', 'unknown')
            domain_b = getattr(org_b, 'primary_domain', 'unknown')

            if domain_a != domain_b:
                cross_domain_edges += 1

        cross_pct = (cross_domain_edges / total_edges * 100) if total_edges > 0 else 0
        print(f"[MULTIDOM_METRICS] Gen {generation} - Cross_Domain_Integration: {cross_pct:.2f}%")
    except Exception as e:
        print(f"[MULTIDOM_METRICS] Warning: Cross-domain integration calc failed: {e}")

    # Metric 3: Consciousness Diversity
    # Component Phi per domain
    try:
        domains = ['quantum', 'temporal', 'social', 'epistemic', 'mathematical']
        for domain in domains:
            # Calculate Phi component for this domain only
            domain_organisms = [o for o in network.organisms
                              if getattr(o, 'primary_domain', None) == domain]

            if domain_organisms:
                # Simplified per-domain Phi
                domain_phi = len(domain_organisms) * 0.01  # Placeholder calculation
                print(f"[MULTIDOM_METRICS] Gen {generation} - Consciousness_Diversity_{domain}: {domain_phi:.4f}")
    except Exception as e:
        print(f"[MULTIDOM_METRICS] Warning: Consciousness diversity calc failed: {e}")


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup colors
    if args.no_color:
        ColorScheme.disable_colors()

    print(ColorScheme.colorize("REALITY SIMULATOR v1.0", ColorScheme.SUCCESS))
    print("=" * 50)

    # Create simulator
    simulator = RealitySimulator(args.config)
    
    # Set frame delay if specified (for CPU sharing)
    if args.delay:
        simulator.frame_delay = args.delay


    # Override config from args
    if args.mode:
        simulator.config['rendering']['mode'] = args.mode

    if args.no_text:
        simulator.config['rendering']['text_interface'] = False

    # Load state if requested
    if args.load:
        if not simulator.load_state(args.load):
            return 1

    # Initialize
    if not simulator.initialize_simulation():
        print("[ERROR] Failed to initialize simulation")
        return 1

    # Launch visualization viewer for all modes (if enabled)
    if simulator.config['rendering'].get('enable_visualizations', False):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        viewer_script = os.path.join(script_dir, "visualization_viewer.py")
        # Pass precision config to viewer
        precision_config = {
            'fitness': simulator.config['evolution'].get('fitness_precision', 0.000001),
            'consciousness': simulator.config['consciousness'].get('phi_precision', 0.000001),
            'performance_cpu': simulator.config['agency'].get('performance_tracking_precision', 0.0001),
            'performance_fps': 10  # FPS is whole number precision
        }
        import json
        precision_json = json.dumps(precision_config)
        viewer_cmd = f'python "{viewer_script}" --precision-config "{precision_json}"'
        print("[ART] Launching visualization viewer...")
        try:
            os.system(f'start "Reality Simulator - Visualizations" cmd /k "{viewer_cmd}"')
            print("[SUCCESS] Visualization viewer launched!")
            time.sleep(2)  # Give viewer time to start
        except Exception as e:
            print(f"[WARNING]  Could not launch visualization viewer: {e}")

    # Handle consciousness test mode
    if args.mode.lower() == "consciousness_test":
        run_statistical_consciousness_test(simulator, args.num_runs or 20, args.frames or 20)
        return 0

    # Run simulation
    try:
        results = simulator.run_simulation(max_frames=args.frames)

        if args.save:
            simulator.save_state(args.save)

        print("\n[CHART] FINAL RESULTS:")
        print(json.dumps(results, indent=2))

        return 0

    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


# Module-level docstring
"""
[ROCKET] REALITY SIMULATOR - THE COMPLETE SYSTEM

This module brings together all layers of the Reality Simulator:

1. [LATTICE] Quantum Substrate - Fundamental reality building blocks
2. [DNA] Genetic Evolution - Darwinian natural selection
3. [NETWORK] Symbiotic Networks - Cooperative ecosystems
4. [CONSCIOUSNESS] Consciousness Emergence - Detecting self-awareness
5. [AGENCY] Human Agency - Decision-making
6. [ART] Reality Rendering - Multi-modal visualization

The bridge between computational simulation and human experience.
Where quantum particles become conscious, evolving beings in a simulated reality.
"""

