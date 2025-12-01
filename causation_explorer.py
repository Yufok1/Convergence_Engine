"""
🔬 Causation Explorer - Interactive Causation Trail System

Allows curiosity-driven exploration of cause-effect relationships.
Click any event → see what caused it
Click any metric → see what it affected
Trace backwards → "Why did this happen?"
Trace forwards → "What did this cause?"

This is about scientific exploration, not just visualization.
"""

import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)


# Global counter for unique event IDs
_event_counter = 0

def _generate_unique_event_id() -> str:
    """Generate a unique event ID using timestamp and counter"""
    global _event_counter
    _event_counter += 1
    return f"evt_{int(time.time() * 1000000)}_{_event_counter}"

@dataclass
class Event:
    """A system event with causation context"""
    timestamp: float
    component: str
    event_type: str  # 'state_change', 'threshold_crossed', 'transition', etc.
    data: Dict[str, Any]
    event_id: str = field(default_factory=_generate_unique_event_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'component': self.component,
            'event_type': self.event_type,
            'data': self.data
        }


@dataclass
class CausationLink:
    """A link between two events showing causation"""
    from_event: str  # event_id
    to_event: str     # event_id
    causation_type: str  # 'temporal', 'correlation', 'threshold', 'direct'
    strength: float   # 0.0-1.0, how strong the causation
    explanation: str   # Human-readable explanation
    metrics_involved: List[str] = field(default_factory=list)


class CausationExplorer:
    """
    Interactive causation trail explorer
    
    Builds a graph of cause-effect relationships from state history
    and allows exploration of "why did this happen?" and "what did this cause?"
    
    Now integrates with Akashic Ledger for tape-based causation tracking.
    """
    
    def __init__(self, state_logger=None, log_dir: Path = None, utm_kernel=None, config: Optional[Dict[str, Any]] = None):
        self.logger = state_logger
        self.log_dir = log_dir or (Path(__file__).parent / 'data' / 'logs')
        self.utm_kernel = utm_kernel  # UTM Kernel for Akashic Ledger access
        
        # Load configuration (with defaults)
        self.config = config or {}
        causation_config = self.config.get('causation_detection', {})
        
        # Causation graph (NetworkX directed graph)
        self.causation_graph = nx.DiGraph()
        
        # Event storage
        self.events: Dict[str, Event] = {}
        self.events_by_component: Dict[str, List[str]] = defaultdict(list)
        self.events_by_type: Dict[str, List[str]] = defaultdict(list)
        
        # Metric tracking (for correlation detection)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Threshold definitions (configurable)
        default_thresholds = {
            'modularity': {'collapse': 0.3, 'direction': 'below'},
            'organism_count': {'collapse': 500, 'direction': 'above'},
            'clustering_coefficient': {'collapse': 0.5, 'direction': 'above'},
            'violation_pressure': {'vp0': 0.25, 'vp1': 0.50, 'vp2': 0.75, 'vp3': 0.99},
            'vp_calculations': {'transition': 50, 'direction': 'above'},
        }
        self.thresholds = causation_config.get('thresholds', default_thresholds)
        # Merge any custom thresholds with defaults
        if 'thresholds' in causation_config:
            for metric, thresholds in causation_config['thresholds'].items():
                if metric in default_thresholds:
                    default_thresholds[metric].update(thresholds)
                else:
                    default_thresholds[metric] = thresholds
            self.thresholds = default_thresholds
        
        # Causation detection parameters (configurable)
        self.direct_causation_time_window = causation_config.get('direct_causation_time_window', 5.0)  # seconds (increased for better detection)
        self.phase_transition_time_window = causation_config.get('phase_transition_time_window', 10.0)  # seconds
        self.recent_events_window = causation_config.get('recent_events_window', 200)  # number of events (increased)
        self.correlation_threshold = causation_config.get('correlation_threshold', 0.7)  # 0.0-1.0
        self.enable_neural_causations = causation_config.get('enable_neural_causations', True)  # Master toggle
        self.enable_neural_decision_causations = causation_config.get('enable_neural_decision_causations', True)
        self.enable_neural_training_causations = causation_config.get('enable_neural_training_causations', True)
        self.enable_ml_causations = causation_config.get('enable_ml_causations', True)  # ML Analysis causation toggle
        self.enable_language_causations = causation_config.get('enable_language_causations', True)  # Language model causations
        self.enable_phase_transition_causations = causation_config.get('enable_phase_transition_causations', True)
        self.enable_bidirectional_causations = causation_config.get('enable_bidirectional_causations', True)
        
        # Phase 2: Real-time event tracking state
        self._last_explorer_phase = None
        self._last_vp = None
        self._last_loaded_frame = -1  # Track last frame loaded from shared state
        
        # Thread safety for concurrent access (Phase 2: Real-time event feeding)
        import threading
        self.graph_lock = threading.Lock()
        
        # Load existing state history if available
        self._load_state_history()
    
    def _load_state_history(self):
        """
        Load state history from log files AND Akashic Ledger
        
        🔍 DATA SOURCES ACCESSED (in priority order):
        
        1. Akashic Ledger (Primary - if available)
           - Location: data/kernel/akashic_ledger/ (via UTM Kernel)
           - Format: Tape cells (immutable history)
           - What: Agent actions, tape states, symbol writes/reads
           - Component: djinn_kernel
           - Event type: tape_cell
           - Method: _load_from_akashic_ledger()
        
        2. Log Files (Secondary - always loaded)
           - Location: data/logs/*.log
           - Files: state.log, reality_sim.log, explorer.log, breath.log, djinn_kernel.log, system.log, application.log
           - Format: Pipe-delimited (timestamp|level|component|metric:value|...)
           - Example: "23:37:11.608|DEBUG|reality_sim|orgs:10|conns:0|mod:0.000|..."
           - Component: Log file name (e.g., reality_sim, explorer)
           - Event type: state_change
           - Method: _parse_log_line()
        
        ✅ Phase 2: REAL-TIME DATA SOURCES (IMPLEMENTED):
        - Shared State File: data/.shared_simulation_state.json (NOW LOADED - incremental updates)
        - Real-time Events: Feeds from unified_entry.py every loop iteration (Phase 2 COMPLETE)
        
        📊 RESULT:
        - Stores events in self.events{}
        - Builds causation graph in self.causation_graph
        - Detects causations automatically (threshold, correlation, direct, temporal)
        """
        # First, try to load from Akashic Ledger (tape-based)
        # DATA SOURCE 1: Akashic Ledger - data/kernel/akashic_ledger/
        if hasattr(self, 'utm_kernel') and self.utm_kernel:
            try:
                self._load_from_akashic_ledger()
            except Exception as e:
                print(f"[CausationExplorer] Warning: Could not load from Akashic Ledger: {e}")
        
        # DATA SOURCE 2: Shared State File - data/.shared_simulation_state.json (Phase 2)
        # Load current state from shared state file (contains all three systems)
        try:
            self._load_from_shared_state()
        except Exception as e:
            print(f"[CausationExplorer] Warning: Could not load from shared state: {e}")
        
        # DATA SOURCE 3: Log Files - data/logs/*.log (fallback/complementary)
        if not self.log_dir.exists():
            return
        
        # Load from all log files
        for log_file in self.log_dir.glob('*.log'):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Parse each log line and create Event
                        # Format: timestamp|level|component|metric:value|metric:value|...
                        self._parse_log_line(line, log_file.stem)
            except Exception as e:
                print(f"[CausationExplorer] Warning: Could not parse {log_file}: {e}")
    
    def _load_from_akashic_ledger(self):
        """Load events from Akashic Ledger (tape-based causation)"""
        if not hasattr(self, 'utm_kernel') or not self.utm_kernel:
            return
        
        ledger = self.utm_kernel.akashic_ledger
        summary = ledger.get_ledger_summary()
        total_cells = summary.get('total_cells', 0)
        
        # Read all cells from ledger
        for position in range(total_cells):
            cell = ledger.read_cell(position)
            if cell:
                # Convert tape cell to event
                event = Event(
                    timestamp=cell.timestamp.timestamp() if hasattr(cell.timestamp, 'timestamp') else time.time(),
                    component='djinn_kernel',
                    event_type='tape_cell',
                    data={
                        **cell.content,
                        'tape_position': cell.position,
                        'symbol': cell.symbol.value,
                        'agent_id': cell.agent_id
                    }
                )
                self.add_event(event)
    
    def _load_from_shared_state(self, force_reload: bool = False):
        """
        Load events from shared state file (data/.shared_simulation_state.json)
        
        Phase 2: Real-time data source - contains current state of all three systems
        - Reality Simulator: network, evolution, quantum, lattice, consciousness
        - Explorer: phase, vp_calculations, breath_state
        - Djinn Kernel: violation_pressure, vp_classification, tape_cells
        
        Args:
            force_reload: If True, reload all data. If False, only load new frames (incremental)
        """
        import time
        load_start = time.time()
        MAX_LOAD_TIME = 3.0  # Don't spend more than 3 seconds loading
        
        shared_state_file = Path('data/.shared_simulation_state.json')
        if not shared_state_file.exists():
            return
        
        # Check if file is empty or too small to be valid JSON
        try:
            file_size = shared_state_file.stat().st_size
            if file_size < 10:
                return  # File is empty or corrupted
            # 🚀 TIMEOUT PROTECTION: Skip very large files that would take too long
            if file_size > 10 * 1024 * 1024:  # >10MB
                logger.warning(f"Shared state file is very large ({file_size/1024/1024:.1f}MB), skipping load to prevent timeout")
                return
        except Exception as e:
            logger.warning(f"Could not check shared state file size: {e}")
            return
        
        try:
            # Retry logic for file locking/race conditions (with timeout)
            max_retries = 3  # Reduced from 5 to speed up
            shared_state = None
            for attempt in range(max_retries):
                # Check timeout
                if time.time() - load_start > MAX_LOAD_TIME:
                    logger.warning(f"Shared state load timeout after {time.time() - load_start:.1f}s, aborting")
                    return
                    
                try:
                    with open(shared_state_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # Skip empty or null-byte-filled files
                        if not content or content.startswith('\x00'):
                            return
                        shared_state = json.loads(content)
                        break  # Success
                except (json.JSONDecodeError, ValueError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.05)  # Reduced delay
                        continue
                    else:
                        # Last attempt failed, log and return (don't raise)
                        logger.warning(f"Could not parse shared state file after {max_retries} attempts: {e}")
                        return
            
            if not shared_state or 'data' not in shared_state:
                return
            
            data = shared_state['data']
            timestamp = shared_state.get('simulation_time', shared_state.get('timestamp', time.time()))
            frame_count = shared_state.get('frame_count', 0)
            
            # Ensure frame_count is an integer (JSON might load it as string)
            try:
                frame_count = int(frame_count) if frame_count is not None else 0
            except (ValueError, TypeError):
                frame_count = 0
            
            # Ensure _last_loaded_frame is also an integer (defensive)
            try:
                if isinstance(self._last_loaded_frame, str):
                    self._last_loaded_frame = int(self._last_loaded_frame)
                elif self._last_loaded_frame is None:
                    self._last_loaded_frame = -1
                else:
                    self._last_loaded_frame = int(self._last_loaded_frame)
            except (ValueError, TypeError):
                self._last_loaded_frame = -1
            
            # Incremental loading: only process if frame_count is newer
            # Ensure both are ints before comparison
            try:
                frame_count_int = int(frame_count)
                last_frame_int = int(self._last_loaded_frame)
                if not force_reload and frame_count_int <= last_frame_int:
                    return  # Already loaded this frame or older
            except (ValueError, TypeError) as e:
                # If comparison fails, force reload to be safe
                pass
            
            self._last_loaded_frame = int(frame_count)  # Ensure it stays an int
            
            # Helper to normalize numeric values
            def normalize_value(v):
                """Convert string numbers to actual numbers, keep other types"""
                if isinstance(v, (int, float)):
                    return v
                if isinstance(v, str):
                    try:
                        # Try int first, then float
                        if '.' in v:
                            return float(v)
                        return int(v)
                    except ValueError:
                        return v
                return v
            
            # 🚀 TIMEOUT PROTECTION: Check timeout before processing
            if time.time() - load_start > MAX_LOAD_TIME:
                logger.warning(f"Shared state processing timeout, aborting")
                return
            
            # Extract Reality Simulator events
            if 'network' in data:
                network_data = data['network']
                if network_data:
                    # Normalize all values in network_data
                    normalized_network = {k: normalize_value(v) for k, v in network_data.items()}
                    event = Event(
                        timestamp=timestamp,
                        component='reality_sim',
                        event_type='state_change',
                        data={
                            'organism_count': normalized_network.get('organism_count', 0),
                            'connection_count': normalized_network.get('connection_count', 0),
                            'modularity': normalized_network.get('modularity', 0),
                            'clustering_coefficient': normalized_network.get('clustering_coefficient', 0),
                            'frame_count': frame_count,
                            **normalized_network  # Include all network data (normalized)
                        }
                    )
                    self.add_event(event)
                    
                    # 🚀 TIMEOUT PROTECTION: Check after each major operation
                    if time.time() - load_start > MAX_LOAD_TIME:
                        logger.warning(f"Shared state processing timeout after network events, aborting")
                        return
            
            # Extract Explorer events
            if 'explorer' in data:
                explorer_data = data['explorer']
                if explorer_data:
                    # Normalize all values in explorer_data
                    normalized_explorer = {k: normalize_value(v) for k, v in explorer_data.items()}
                    event = Event(
                        timestamp=timestamp,
                        component='explorer',
                        event_type='state_change',
                        data={
                            'phase': normalized_explorer.get('phase', 'unknown'),
                            'vp_calculations': normalized_explorer.get('vp_calculations', 0),
                            'breath_cycle': normalized_explorer.get('breath_cycle', 0),
                            'breath_depth': normalized_explorer.get('breath_depth', 0),
                            'frame_count': frame_count,
                            **normalized_explorer  # Include all explorer data (normalized)
                        }
                    )
                    self.add_event(event)
                    
                    # Detect phase transitions
                    if self._last_explorer_phase is not None:
                        if self._last_explorer_phase != explorer_data.get('phase'):
                            phase_event = Event(
                                timestamp=timestamp,
                                component='explorer',
                                event_type='phase_transition',
                                data={
                                    'from_phase': self._last_explorer_phase,
                                    'to_phase': explorer_data.get('phase'),
                                    'frame_count': frame_count
                                }
                            )
                            self.add_event(phase_event)
                    self._last_explorer_phase = explorer_data.get('phase')
                    
                    # 🚀 TIMEOUT PROTECTION: Check after explorer processing
                    if time.time() - load_start > MAX_LOAD_TIME:
                        logger.warning(f"Shared state processing timeout after explorer events, aborting")
                        return
            
            # Extract Djinn Kernel events
            if 'djinn_kernel' in data:
                djinn_data = data['djinn_kernel']
                if djinn_data:
                    # Normalize all values in djinn_data
                    normalized_djinn = {k: normalize_value(v) for k, v in djinn_data.items()}
                    event = Event(
                        timestamp=timestamp,
                        component='djinn_kernel',
                        event_type='state_change',
                        data={
                            'violation_pressure': normalized_djinn.get('violation_pressure', 0),
                            'vp_classification': normalized_djinn.get('vp_classification', 'VP0'),
                            'vp_calculations': normalized_djinn.get('vp_calculations', 0),
                            'tape_cells': normalized_djinn.get('tape_cells', 0),
                            'frame_count': frame_count,
                            **normalized_djinn  # Include all djinn_kernel data (normalized)
                        }
                    )
                    self.add_event(event)
                    
                    # Detect VP threshold crossings
                    vp = normalized_djinn.get('violation_pressure', 0)
                    if self._last_vp is not None:
                        # Check each VP threshold (vp0, vp1, vp2, vp3 in thresholds dict)
                        for vp_key in ['vp0', 'vp1', 'vp2', 'vp3']:
                            vp_level = vp_key.upper()  # Convert to VP0, VP1, etc.
                            threshold = self.thresholds['violation_pressure'].get(vp_key, 0)
                            # Check if we crossed the threshold (going up or down)
                            if self._last_vp < threshold <= vp or self._last_vp > threshold >= vp:
                                vp_event = Event(
                                    timestamp=timestamp,
                                    component='djinn_kernel',
                                    event_type='threshold_crossed',
                                    data={
                                        'metric': 'violation_pressure',
                                        'threshold': vp_level,
                                        'value': vp,
                                        'frame_count': frame_count
                                    }
                                )
                                self.add_event(vp_event)
                    self._last_vp = vp
                    
                    # 🚀 TIMEOUT PROTECTION: Check after djinn processing
                    if time.time() - load_start > MAX_LOAD_TIME:
                        logger.warning(f"Shared state processing timeout after djinn events, aborting")
                        return
            
            # Extract Neural System events
            if 'neural' in data:
                neural_data = data['neural']
                if neural_data and neural_data.get('enabled', False):
                    # Normalize all values in neural_data
                    normalized_neural = {k: normalize_value(v) for k, v in neural_data.items()}
                    
                    # Create neural training event if training occurred
                    if normalized_neural.get('training_steps', 0) > 0:
                        training_event = Event(
                            timestamp=timestamp,
                            component='neural',
                            event_type='neural_training',
                            data={
                                'training_steps': normalized_neural.get('training_steps', 0),
                                'organisms_tracked': normalized_neural.get('organisms_tracked', 0),
                                'avg_loss': normalized_neural.get('avg_loss', 0),
                                'avg_epsilon': normalized_neural.get('avg_epsilon', 0),
                                'frame_count': frame_count,
                                **normalized_neural
                            }
                        )
                        self.add_event(training_event)
                    
                    # Create general neural state event
                    neural_event = Event(
                        timestamp=timestamp,
                        component='neural',
                        event_type='state_change',
                        data={
                            'enabled': True,
                            'organisms_tracked': normalized_neural.get('organisms_tracked', 0),
                            'training_steps': normalized_neural.get('training_steps', 0),
                            'avg_epsilon': normalized_neural.get('avg_epsilon', 0),
                            'frame_count': frame_count,
                            **normalized_neural
                        }
                    )
                    self.add_event(neural_event)
                    
                    # 🚀 TIMEOUT PROTECTION: Check after neural processing
                    if time.time() - load_start > MAX_LOAD_TIME:
                        logger.warning(f"Shared state processing timeout after neural events, aborting")
                        return
            
            # Extract ML Analysis events
            if 'ml' in data:
                ml_data = data['ml']
                if ml_data and ml_data.get('enabled', False):
                    # Normalize all values in ml_data
                    normalized_ml = {k: normalize_value(v) for k, v in ml_data.items()}
                    
                    # Create phenotype emergence event if clusters detected
                    clustering = normalized_ml.get('clustering', {})
                    if clustering.get('n_clusters', 0) > 0:
                        phenotype_event = Event(
                            timestamp=timestamp,
                            component='ml_analysis',
                            event_type='phenotype_emergence',
                            data={
                                'n_clusters': clustering.get('n_clusters', 0),
                                'cluster_sizes': clustering.get('cluster_sizes', {}),
                                'algorithm': clustering.get('algorithm', 'unknown'),
                                'frame_count': frame_count,
                                **normalized_ml
                            }
                        )
                        self.add_event(phenotype_event)
                    
                    # Create anomaly spike event if significant anomalies
                    anomalies = normalized_ml.get('anomalies', {})
                    if anomalies.get('anomaly_ratio', 0) > 0.15:
                        anomaly_event = Event(
                            timestamp=timestamp,
                            component='ml_analysis',
                            event_type='anomaly_spike',
                            data={
                                'anomaly_count': anomalies.get('anomaly_count', 0),
                                'anomaly_ratio': anomalies.get('anomaly_ratio', 0),
                                'algorithm': anomalies.get('algorithm', 'unknown'),
                                'frame_count': frame_count,
                                **normalized_ml
                            }
                        )
                        self.add_event(anomaly_event)
                    
                    # Create general ML state event
                    ml_event = Event(
                        timestamp=timestamp,
                        component='ml_analysis',
                        event_type='state_change',
                        data={
                            'enabled': True,
                            'organism_count': normalized_ml.get('organism_count', 0),
                            'n_clusters': clustering.get('n_clusters', 0),
                            'anomaly_count': anomalies.get('anomaly_count', 0),
                            'frame_count': frame_count,
                            **normalized_ml
                        }
                    )
                    self.add_event(ml_event)
                    
                    # 🚀 TIMEOUT PROTECTION: Final check
                    if time.time() - load_start > MAX_LOAD_TIME:
                        logger.warning(f"Shared state processing timeout after ML events, aborting")
                        return
            
            # 🗣️ Extract Language System events
            if 'language' in data:
                language_data = data['language']
                if language_data:
                    # Normalize all values in language_data
                    normalized_lang = {k: normalize_value(v) for k, v in language_data.items()}
                    vocab_size = normalized_lang.get('vocab_size', 0) or normalized_lang.get('word_count', 0)
                    
                    # Create vocabulary growth event if vocab has grown
                    if vocab_size > 0:
                        # Track if vocabulary has grown since last check
                        if not hasattr(self, '_last_vocab_size'):
                            self._last_vocab_size = 0
                        
                        if vocab_size > self._last_vocab_size:
                            growth_event = Event(
                                timestamp=timestamp,
                                component='language',
                                event_type='vocabulary_growth',
                                data={
                                    'vocab_size': vocab_size,
                                    'prev_vocab_size': self._last_vocab_size,
                                    'growth': vocab_size - self._last_vocab_size,
                                    'organism_assignments': normalized_lang.get('organism_word_assignments', 0),
                                    'language_anchors': normalized_lang.get('language_anchors', 0),
                                    'total_associations': normalized_lang.get('total_associations', 0),
                                    'frame_count': frame_count
                                }
                            )
                            self.add_event(growth_event)
                            self._last_vocab_size = vocab_size
                    
                    # Create general language state event
                    lang_event = Event(
                        timestamp=timestamp,
                        component='language',
                        event_type='state_change',
                        data={
                            'vocab_size': vocab_size,
                            'organism_assignments': normalized_lang.get('organism_word_assignments', 0),
                            'language_anchors': normalized_lang.get('language_anchors', 0),
                            'total_associations': normalized_lang.get('total_associations', 0),
                            'frame_count': frame_count,
                            **normalized_lang
                        }
                    )
                    self.add_event(lang_event)
            
        except Exception as e:
            logger.warning(f"[CausationExplorer] Could not load from shared state: {e}")
            # Don't raise - just log and return (prevents hanging)
    
    def _parse_log_line(self, line: str, component: str):
        """Parse a log line and extract events"""
        # Valid simulation components - filter out noise from imports/libraries
        VALID_COMPONENTS = {
            'reality_sim', 'explorer', 'djinn_kernel', 'neural', 'ml_analysis',
            'language', 'butterfly_chat', 'config_tuner', 'health_monitor',
            'breath', 'state', 'system', 'application', 'causation_explorer',
            'network', 'quantum', 'lattice', 'consciousness', 'evolution'
        }
        
        try:
            # Format: timestamp|level|component|metric:value|metric:value|...
            parts = line.strip().split('|')
            if len(parts) < 4:
                return
            
            timestamp_str = parts[0]
            level = parts[1]
            log_component = parts[2]
            metrics_str = '|'.join(parts[3:])
            
            # Filter out non-simulation components (matplotlib, PIL, etc.)
            component_base = log_component.split('.')[0] if '.' in log_component else log_component
            if component_base.lower() not in VALID_COMPONENTS and log_component.lower() not in VALID_COMPONENTS:
                return  # Skip non-simulation log entries
            
            # Parse timestamp (format: HH:MM:SS.microseconds)
            # For now, use current time offset
            timestamp = time.time()  # Simplified
            
            # Parse metrics
            metrics = {}
            for metric_pair in metrics_str.split('|'):
                if ':' in metric_pair:
                    key, value = metric_pair.split(':', 1)
                    try:
                        # Try to convert to number
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            # Skip events with no meaningful metrics
            if not metrics:
                return
            
            # Use the base component name for cleaner matching
            clean_component = component_base.lower() if component_base.lower() in VALID_COMPONENTS else component
            
            # Create event
            event = Event(
                timestamp=timestamp,
                component=clean_component,
                event_type='state_change',
                data=metrics
            )
            
            self.add_event(event)
            
        except Exception as e:
            pass  # Skip malformed lines
    
    def add_event(self, event: Event, is_historical: bool = False):
        """
        Add an event and detect causations
        
        Phase 2: Thread-safe for real-time event feeding from unified_entry.py
        
        Args:
            event: Event to add
            is_historical: If True, event is from historical logs (for optimization)
        """
        with self.graph_lock:
            event_id = event.event_id
            # Store event in main dictionary
            self.events[event_id] = event
            
            # CRITICAL VERIFICATION: Check immediately after assignment
            if event_id not in self.events:
                logger.error(f"[ADD_EVENT] CRITICAL: Event {event_id} missing immediately after assignment! This should never happen.")
                import traceback
                logger.error(f"[ADD_EVENT] Traceback: {traceback.format_exc()}")
            
            # Index by component
            self.events_by_component[event.component].append(event_id)
            
            # Index by type
            self.events_by_type[event.event_type].append(event_id)
            
            # Add event as node to causation graph
            if event_id not in self.causation_graph:
                self.causation_graph.add_node(event_id, **event.to_dict())
            
            # Verify storage (debug logging for language events)
            if event.event_type in ['butterfly_chat_message', 'butterfly_chat_response', 'vocabulary_growth', 'organism_communication', 'word_assignment']:
                logger.info(f"[EVENT_STORAGE] ✅ Stored language event: {event_id} (type={event.event_type}, component={event.component}) in events dict (total: {len(self.events)})")
                # Verify it's actually in the dict
                if event_id not in self.events:
                    logger.error(f"[EVENT_STORAGE] ❌ CRITICAL: Event {event_id} was not found in self.events immediately after storage!")
                else:
                    logger.info(f"[EVENT_STORAGE] ✅ Verified: Event {event_id} is present in self.events (can be looked up)")
            
            # Update metric history
            for metric, value in event.data.items():
                if isinstance(value, (int, float)):
                    self.metric_history[metric].append({
                        'timestamp': event.timestamp,
                        'value': value,
                        'event_id': event.event_id
                    })
            
            # Detect causations with recent events (inside lock)
            self._detect_causations(event)
    
    def _detect_causations(self, new_event: Event):
        """
        Detect causation relationships for a new event
        
        Phase 2: Thread-safe - assumes called from within graph_lock
        """
        # Look at recent events (configurable window)
        # Create snapshot to avoid iteration issues if events are modified concurrently
        events_snapshot = list(self.events.values())
        recent_events = sorted(
            events_snapshot,
            key=lambda e: e.timestamp,
            reverse=True
        )[: max(1, int(getattr(self, 'recent_events_window', 100)))]
        
        for prev_event in recent_events:
            if prev_event.event_id == new_event.event_id:
                continue
            
            # Temporal causation (happened before)
            if prev_event.timestamp < new_event.timestamp:
                time_diff = new_event.timestamp - prev_event.timestamp
                
                # Check for threshold crossings
                causation = self._check_threshold_causation(prev_event, new_event)
                if causation:
                    self._add_causation_link(causation)
                    continue
                
                # Check for correlation (metrics changed together)
                causation = self._check_correlation_causation(prev_event, new_event)
                if causation:
                    self._add_causation_link(causation)
                    continue
                
                # Check for direct metric relationships
                causation = self._check_direct_causation(prev_event, new_event, time_diff)
                if causation:
                    self._add_causation_link(causation)
    
    def _check_threshold_causation(self, prev_event: Event, new_event: Event) -> Optional[CausationLink]:
        """Check if threshold crossing caused an event"""
        for metric, thresholds in self.thresholds.items():
            prev_value = prev_event.data.get(metric)
            new_value = new_event.data.get(metric)
            
            if prev_value is None or new_value is None:
                continue
            
            # Convert to numbers for comparison (handle string numbers from JSON)
            try:
                prev_value = float(prev_value) if not isinstance(prev_value, (int, float)) else prev_value
                new_value = float(new_value) if not isinstance(new_value, (int, float)) else new_value
            except (ValueError, TypeError):
                continue  # Skip if can't convert to number
            
            # Check each threshold
            for threshold_name, threshold_config in thresholds.items():
                if isinstance(threshold_config, dict):
                    threshold_value = threshold_config.get('collapse') or threshold_config.get('transition')
                    direction = threshold_config.get('direction', 'above')
                else:
                    threshold_value = threshold_config
                    direction = 'above'
                
                if threshold_value is None:
                    continue
                
                # Ensure threshold is numeric
                try:
                    threshold_value = float(threshold_value) if not isinstance(threshold_value, (int, float)) else threshold_value
                except (ValueError, TypeError):
                    continue
                
                # Check if threshold was crossed
                crossed = False
                try:
                    if direction == 'above':
                        crossed = prev_value < threshold_value <= new_value
                    elif direction == 'below':
                        crossed = prev_value > threshold_value >= new_value
                except TypeError:
                    continue  # Skip if types still don't match
                
                if crossed:
                    # This threshold crossing might have caused the new event
                    # Check if new event is a known consequence
                    if self._is_known_consequence(new_event, metric, threshold_name):
                        return CausationLink(
                            from_event=prev_event.event_id,
                            to_event=new_event.event_id,
                            causation_type='threshold',
                            strength=0.9,
                            explanation=f"{metric} crossed {threshold_name} threshold ({threshold_value})",
                            metrics_involved=[metric]
                        )
        
        return None
    
    def _is_known_consequence(self, event: Event, metric: str, threshold_name: str) -> bool:
        """Check if event is a known consequence of threshold crossing"""
        # Known consequences
        consequences = {
            ('modularity', 'collapse'): ['is_collapsed', 'collapse', 'transition'],
            ('organism_count', 'collapse'): ['is_collapsed', 'collapse', 'transition'],
            ('violation_pressure', 'vp0'): ['vp_classification', 'transition', 'convergence'],
            ('vp_calculations', 'transition'): ['phase', 'transition', 'mathematical_capability'],
        }
        
        key = (metric, threshold_name)
        if key in consequences:
            for consequence_type in consequences[key]:
                if consequence_type in event.event_type.lower() or any(
                    consequence_type in str(v).lower() for v in event.data.values()
                ):
                    return True
        
        return False
    
    def _check_correlation_causation(self, prev_event: Event, new_event: Event) -> Optional[CausationLink]:
        """Check if events are correlated (metrics changed together)"""
        # Find metrics that changed in both events
        common_metrics = set(prev_event.data.keys()) & set(new_event.data.keys())
        
        if not common_metrics:
            return None
        
        # Check for significant changes
        significant_changes = []
        for metric in common_metrics:
            prev_val = prev_event.data.get(metric)
            new_val = new_event.data.get(metric)
            
            if not isinstance(prev_val, (int, float)) or not isinstance(new_val, (int, float)):
                continue
            
            # Calculate change percentage
            if prev_val != 0:
                change_pct = abs((new_val - prev_val) / prev_val)
                min_change = (1.0 - self.correlation_threshold)  # Use configurable threshold
                if change_pct > min_change:
                    significant_changes.append((metric, change_pct))
        
        if len(significant_changes) >= 2:
            # Strong correlation
            metrics_str = ', '.join([m for m, _ in significant_changes[:3]])
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='correlation',
                strength=0.7,
                explanation=f"Correlated changes in {metrics_str}",
                metrics_involved=[m for m, _ in significant_changes]
            )
        
        return None
    
    def _check_direct_causation(self, prev_event: Event, new_event: Event, time_diff: float) -> Optional[CausationLink]:
        """Check for direct causation relationships"""
        # Known direct causations
        direct_causations = {
            # Bidirectional system causations
            ('reality_sim', 'djinn_kernel'): 'Network metrics feed into VP calculation',
            ('djinn_kernel', 'reality_sim'): 'VP changes affect network behavior',
            ('explorer', 'reality_sim'): 'Explorer phase affects network behavior',
            ('reality_sim', 'explorer'): 'Network state influences Explorer phase',
            ('explorer', 'djinn_kernel'): 'Explorer state influences VP calculation',
            ('djinn_kernel', 'explorer'): 'VP changes influence Explorer phase',
            # Neural causations
            ('neural', 'reality_sim'): 'Neural decision affects network state',
            ('reality_sim', 'neural'): 'Network state influences neural decisions',
            ('neural', 'neural'): 'Neural training influences future decisions',
            ('neural', 'explorer'): 'Neural decisions influence Explorer state',
            ('explorer', 'neural'): 'Explorer phase affects neural behavior',
            # ML Analysis causations
            ('ml_analysis', 'reality_sim'): 'ML analysis detects patterns affecting network state',
            ('reality_sim', 'ml_analysis'): 'Network state provides data for ML analysis',
            ('ml_analysis', 'ml_analysis'): 'ML clustering/anomaly detection influences future analysis',
            ('ml_analysis', 'neural'): 'ML patterns influence neural decisions',
            ('neural', 'ml_analysis'): 'Neural decisions affect population patterns analyzed by ML',
            ('ml_analysis', 'explorer'): 'ML analysis influences Explorer state',
            ('explorer', 'ml_analysis'): 'Explorer phase affects ML analysis context',
            # ML ↔ Language causations (Neural-ML Symbiosis Integration)
            ('ml_analysis', 'language'): 'ML feature importance guides language rewards',
            ('language', 'ml_analysis'): 'Language patterns provide data for ML clustering',
            # Language model causations (Phase 1)
            ('language', 'language'): 'Vocabulary growth enables organism communication',
            ('language', 'neural'): 'Language learning influences neural training',
            ('neural', 'language'): 'Neural training improves language generation',
            ('language', 'reality_sim'): 'Language associations affect organism behavior',
            ('reality_sim', 'language'): 'Organism behavior creates language associations',
            ('butterfly_chat', 'language'): 'User chat interactions trigger language events',
            ('language', 'butterfly_chat'): 'Language events enable chat responses',
            # ConfigTuner causations (Autonomous Configuration Tuning)
            ('config_tuner', 'neural'): 'Config tuning adjusts neural parameters',
            ('neural', 'config_tuner'): 'Neural metrics trigger config tuning',
            ('config_tuner', 'ml_analysis'): 'Config tuning adjusts ML parameters',
            ('ml_analysis', 'config_tuner'): 'ML metrics trigger config tuning',
            ('config_tuner', 'language'): 'Config tuning adjusts language parameters',
            ('language', 'config_tuner'): 'Language metrics trigger config tuning',
            ('config_tuner', 'reality_sim'): 'Config tuning adjusts network parameters',
            ('reality_sim', 'config_tuner'): 'Network metrics trigger config tuning',
            ('config_tuner', 'explorer'): 'Config tuning adjusts explorer parameters',
            ('explorer', 'config_tuner'): 'Explorer metrics trigger config tuning',
            ('config_tuner', 'djinn_kernel'): 'Config tuning adjusts VP calculation parameters',
            ('djinn_kernel', 'config_tuner'): 'VP metrics trigger config tuning',
            ('config_tuner', 'config_tuner'): 'Config tuning influences future tuning decisions',
            # Health Monitor causations (System Health Tracking)
            ('health_monitor', 'neural'): 'Health issues affect neural training',
            ('neural', 'health_monitor'): 'Neural training impacts system health',
            ('health_monitor', 'ml_analysis'): 'Health patterns affect ML clustering',
            ('ml_analysis', 'health_monitor'): 'ML analysis detects health issues',
            ('health_monitor', 'language'): 'Health issues affect language learning',
            ('language', 'health_monitor'): 'Language patterns indicate system health',
            ('health_monitor', 'reality_sim'): 'Health issues affect network behavior',
            ('reality_sim', 'health_monitor'): 'Network state impacts system health',
            ('health_monitor', 'explorer'): 'Health issues affect explorer phase',
            ('explorer', 'health_monitor'): 'Explorer phase impacts system health',
            ('health_monitor', 'config_tuner'): 'Health issues trigger config tuning',
            ('config_tuner', 'health_monitor'): 'Config tuning affects system health',
            ('health_monitor', 'djinn_kernel'): 'Health issues affect VP calculation',
            ('djinn_kernel', 'health_monitor'): 'VP changes impact system health',
            ('health_monitor', 'health_monitor'): 'Health state changes influence future health',
        }
        
        # Special handling for phase transitions - they should link to what caused them
        if self.enable_phase_transition_causations and new_event.event_type == 'phase_transition':
            # Phase transitions are caused by threshold crossings or state changes
            if prev_event.component == 'explorer' and 'vp_calculations' in prev_event.data:
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='direct',
                    strength=0.9,
                    explanation=f'VP calculations triggered phase transition ({new_event.data.get("from_phase", "?")} → {new_event.data.get("to_phase", "?")})',
                    metrics_involved=['vp_calculations', 'phase']
                )
            # Also link phase transitions to what they affect
            if time_diff < self.phase_transition_time_window:  # Configurable window for phase effects
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='direct',
                    strength=0.85,
                    explanation=f'State change triggered phase transition ({new_event.data.get("from_phase", "?")} → {new_event.data.get("to_phase", "?")})',
                    metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
                )
        
        # Special handling for breath-driven events (breath_state in explorer data)
        if prev_event.component == 'explorer' and 'breath_cycle' in prev_event.data:
            if new_event.component == 'reality_sim' and time_diff < self.direct_causation_time_window:
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='direct',
                    strength=0.8,
                    explanation='Breath cycle drives network update',
                    metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
                )
            if new_event.component == 'djinn_kernel' and time_diff < self.direct_causation_time_window:
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='direct',
                    strength=0.8,
                    explanation='Breath cycle drives VP calculation',
                    metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
                )
        
        key = (prev_event.component, new_event.component)
        
        # Special handling for ConfigTuner events - use longer time window (tuning happens periodically)
        if (prev_event.component == 'config_tuner' or new_event.component == 'config_tuner') and key in direct_causations:
            # ConfigTuner events can have longer time windows since tuning happens periodically
            # Use a more lenient time window (4x normal) for ConfigTuner causations
            tuner_time_window = self.direct_causation_time_window * 4.0
            if time_diff > tuner_time_window:
                return None
            
            # ConfigTuner links get specific explanations based on event type and parameter
            explanation = direct_causations[key]
            if prev_event.event_type == 'tuning_action':
                param_path = prev_event.data.get('parameter_path', 'unknown')
                current_val = prev_event.data.get('current_value', '?')
                proposed_val = prev_event.data.get('proposed_value', '?')
                reason = prev_event.data.get('reason', 'optimization')
                explanation = f'Config tuning: {param_path} ({current_val} → {proposed_val}) - {reason}'
            elif new_event.event_type == 'tuning_action':
                param_path = new_event.data.get('parameter_path', 'unknown')
                current_val = new_event.data.get('current_value', '?')
                proposed_val = new_event.data.get('proposed_value', '?')
                reason = new_event.data.get('reason', 'optimization')
                explanation = f'System state triggers config tuning: {param_path} ({current_val} → {proposed_val}) - {reason}'
            
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='direct',
                strength=0.9,  # High strength for tuning links (meta-management is important)
                explanation=explanation,
                metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
            )
        
        # Special handling for Health Monitor events - use longer time window (health changes gradually)
        if (prev_event.component == 'health_monitor' or new_event.component == 'health_monitor') and key in direct_causations:
            # Health Monitor events can have longer time windows since health changes gradually
            # Use a more lenient time window (3x normal) for Health Monitor causations
            health_time_window = self.direct_causation_time_window * 3.0
            if time_diff > health_time_window:
                return None
            
            # Health Monitor links get specific explanations based on event type and health state
            explanation = direct_causations[key]
            if prev_event.event_type == 'health_state_change':
                prev_state = prev_event.data.get('previous_state', 'unknown')
                new_state = prev_event.data.get('new_state', 'unknown')
                health_score = prev_event.data.get('health_score', 0.0)
                explanation = f'Health state change: {prev_state} → {new_state} (score: {health_score:.2f})'
            elif new_event.event_type == 'health_state_change':
                prev_state = new_event.data.get('previous_state', 'unknown')
                new_state = new_event.data.get('new_state', 'unknown')
                health_score = new_event.data.get('health_score', 0.0)
                explanation = f'System changes trigger health state change: {prev_state} → {new_state} (score: {health_score:.2f})'
            
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='direct',
                strength=0.88,  # High strength for health links (system monitoring is important)
                explanation=explanation,
                metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
            )
        
        # Special handling for ML Analysis events - use longer time window
        if (prev_event.component == 'ml_analysis' or new_event.component == 'ml_analysis') and key in direct_causations:
            # Check master toggle first
            if not self.enable_ml_causations:
                return None
            
            # ML events can have longer time windows since they're analysis results
            # Use a more lenient time window (3x normal) for ML causations
            ml_time_window = self.direct_causation_time_window * 3.0
            if time_diff > ml_time_window:
                return None
            
            # ML links get specific explanations based on event type
            explanation = direct_causations[key]
            if prev_event.event_type == 'phenotype_emergence':
                n_clusters = prev_event.data.get('n_clusters', 0)
                explanation = f'Phenotype emergence ({n_clusters} clusters) affects system'
            elif new_event.event_type == 'phenotype_emergence':
                n_clusters = new_event.data.get('n_clusters', 0)
                explanation = f'System state triggers phenotype emergence ({n_clusters} clusters)'
            elif prev_event.event_type == 'cluster_collapse':
                explanation = 'Cluster collapse affects network structure'
            elif new_event.event_type == 'cluster_collapse':
                explanation = 'Network changes trigger cluster collapse'
            elif prev_event.event_type == 'anomaly_spike':
                anomaly_count = prev_event.data.get('anomaly_count', 0)
                explanation = f'Anomaly spike ({anomaly_count} anomalies) detected'
            elif new_event.event_type == 'anomaly_spike':
                anomaly_count = new_event.data.get('anomaly_count', 0)
                explanation = f'System changes trigger anomaly spike ({anomaly_count} anomalies)'
            
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='direct',
                strength=0.85,  # Slightly higher strength for ML links
                explanation=explanation,
                metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
            )
        
        if key in direct_causations and time_diff < self.direct_causation_time_window:
            # Check if neural causations are enabled
            if not self.enable_neural_causations and (prev_event.component == 'neural' or new_event.component == 'neural'):
                return None
            
            # Check if ML causations are enabled (already handled above, but keep for consistency)
            if not self.enable_ml_causations and (prev_event.component == 'ml_analysis' or new_event.component == 'ml_analysis'):
                return None
            
            # Check if language causations are enabled
            if not self.enable_language_causations and (prev_event.component in ['language', 'butterfly_chat'] or new_event.component in ['language', 'butterfly_chat']):
                return None
            
            # Check if ConfigTuner causations are enabled (if component involved)
            if (prev_event.component == 'config_tuner' or new_event.component == 'config_tuner'):
                # ConfigTuner causations are always enabled (no toggle needed - it's meta-management)
                pass
            
            # Check if Health Monitor causations are enabled (if component involved)
            if (prev_event.component == 'health_monitor' or new_event.component == 'health_monitor'):
                # Health Monitor causations are always enabled (no toggle needed - it's system monitoring)
                pass
            
            # Check if bidirectional causations are enabled
            if not self.enable_bidirectional_causations:
                # Only allow forward causations (reality_sim -> djinn_kernel, not reverse)
                bidirectional_pairs = [
                    ('djinn_kernel', 'reality_sim'),
                    ('reality_sim', 'explorer'),
                    ('djinn_kernel', 'explorer'),
                ]
                if key in bidirectional_pairs:
                    return None
            
            # Special handling for neural events
            if prev_event.component == 'neural' or new_event.component == 'neural':
                # Check master toggle first
                if not self.enable_neural_causations:
                    return None
                
                # Check specific neural event type toggles
                # If either event is a decision, decision causations must be enabled
                # If either event is training, training causations must be enabled
                # If both types are involved, both must be enabled
                prev_is_decision = prev_event.event_type == 'neural_decision'
                prev_is_training = prev_event.event_type == 'neural_training'
                new_is_decision = new_event.event_type == 'neural_decision'
                new_is_training = new_event.event_type == 'neural_training'
                
                has_decision = prev_is_decision or new_is_decision
                has_training = prev_is_training or new_is_training
                
                # Require appropriate toggle for each event type involved
                if has_decision and not self.enable_neural_decision_causations:
                    return None
                if has_training and not self.enable_neural_training_causations:
                    return None
                
                # Neural links get slightly higher strength and specific explanation
                explanation = direct_causations[key]
                if prev_event.event_type == 'neural_decision':
                    action = prev_event.data.get('action', 'unknown')
                    explanation = f'Neural decision ({action}) affects network'
                elif new_event.event_type == 'neural_decision':
                    action = new_event.data.get('action', 'unknown')
                    explanation = f'Network state triggers neural decision ({action})'
                elif prev_event.event_type == 'neural_training':
                    explanation = 'Neural training improves future decisions'
                elif new_event.event_type == 'neural_training':
                    explanation = 'Network state triggers neural training'
                
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='direct',
                    strength=0.85,  # Slightly higher strength for neural links
                    explanation=explanation,
                    metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
                )
            
            # Special handling for word_assignment events - create linguistic connections
            if prev_event.event_type == 'word_assignment' and new_event.event_type == 'word_assignment':
                prev_word = prev_event.data.get('word')
                new_word = new_event.data.get('word')
                prev_org = prev_event.data.get('organism_id')
                new_org = new_event.data.get('organism_id')
                
                # Same word assigned to different organisms = linguistic connection
                if prev_word == new_word and prev_org != new_org:
                    return CausationLink(
                        from_event=prev_event.event_id,
                        to_event=new_event.event_id,
                        causation_type='language',
                        strength=0.95,  # Very strong - shared vocabulary
                        explanation=f"Organisms share word '{prev_word}' (linguistic connection)",
                        metrics_involved=['word', 'organism_id']
                    )
                # Word assignments to same organism = vocabulary building
                elif prev_org == new_org:
                    return CausationLink(
                        from_event=prev_event.event_id,
                        to_event=new_event.event_id,
                        causation_type='language',
                        strength=0.8,
                        explanation=f"Organism {prev_org} learns multiple words",
                        metrics_involved=['word', 'organism_id']
                    )
            
            # Vocabulary growth → word assignment connections
            if prev_event.event_type == 'vocabulary_growth' and new_event.event_type == 'word_assignment':
                prev_word = prev_event.data.get('word')
                new_word = new_event.data.get('word')
                if prev_word == new_word:
                    return CausationLink(
                        from_event=prev_event.event_id,
                        to_event=new_event.event_id,
                        causation_type='language',
                        strength=0.9,
                        explanation=f"Word '{prev_word}' added to vocabulary, then assigned to organism",
                        metrics_involved=['word', 'vocab_size']
                    )
            
            # Word assignment → vocabulary growth (if word is new)
            if prev_event.event_type == 'word_assignment' and new_event.event_type == 'vocabulary_growth':
                prev_word = prev_event.data.get('word')
                new_word = new_event.data.get('word')
                if prev_word == new_word:
                    return CausationLink(
                        from_event=prev_event.event_id,
                        to_event=new_event.event_id,
                        causation_type='language',
                        strength=0.85,
                        explanation=f"Word assignment triggers vocabulary growth",
                        metrics_involved=['word', 'vocab_size']
                    )
            
            # Word assignment → organism communication (organisms with shared words communicate)
            if prev_event.event_type == 'word_assignment' and new_event.event_type == 'organism_communication':
                prev_word = prev_event.data.get('word')
                prev_org = prev_event.data.get('organism_id')
                comm_orgs = {new_event.data.get('organism_a_id'), new_event.data.get('organism_b_id')}
                if prev_org in comm_orgs:
                    return CausationLink(
                        from_event=prev_event.event_id,
                        to_event=new_event.event_id,
                        causation_type='language',
                        strength=0.8,
                        explanation=f"Word assignment enables organism communication",
                        metrics_involved=['word', 'tokens_exchanged']
                    )
            
            # Special handling for language events
            if prev_event.component in ['language', 'butterfly_chat'] or new_event.component in ['language', 'butterfly_chat']:
                # Check master toggle first
                if not self.enable_language_causations:
                    return None
                
                # Language events can have longer time windows since they're communication-based
                language_time_window = self.direct_causation_time_window * 2.0
                if time_diff > language_time_window:
                    return None
                
                # Language links get specific explanations based on event type
                explanation = direct_causations.get(key, 'Language event affects system')
                
                # Language ↔ Neural: Neural-ML Symbiosis Integration 2 & 3
                if (prev_event.component == 'language' and new_event.component == 'neural') or \
                   (prev_event.component == 'neural' and new_event.component == 'language'):
                    if new_event.event_type == 'neural_language_reward':
                        explanation = 'Language patterns trigger neural language rewards'
                    elif new_event.event_type == 'neural_curriculum_adjustment':
                        explanation = 'Language quality metrics adjust neural curriculum'
                    elif prev_event.event_type == 'neural_language_reward':
                        explanation = 'Neural language rewards improve language generation'
                    elif prev_event.event_type == 'neural_curriculum_adjustment':
                        explanation = 'Neural curriculum adjustments optimize language learning'
                    elif prev_event.event_type == 'vocabulary_growth':
                        vocab_size = prev_event.data.get('vocab_size', 0)
                        explanation = f'Vocabulary growth ({vocab_size} words) influences neural training'
                    elif new_event.event_type == 'vocabulary_growth':
                        vocab_size = new_event.data.get('vocab_size', 0)
                        explanation = f'Neural training enables vocabulary growth ({vocab_size} words)'
                
                # Language ↔ ML: Neural-ML Symbiosis Integration 1 & 2
                elif (prev_event.component == 'language' and new_event.component == 'ml_analysis') or \
                     (prev_event.component == 'ml_analysis' and new_event.component == 'language'):
                    if prev_event.component == 'ml_analysis' and new_event.event_type == 'neural_language_reward':
                        explanation = 'ML feature importance guides language rewards'
                    elif prev_event.component == 'language' and new_event.component == 'ml_analysis':
                        if prev_event.event_type == 'vocabulary_growth':
                            vocab_size = prev_event.data.get('vocab_size', 0)
                            explanation = f'Vocabulary growth ({vocab_size} words) provides embeddings for ML clustering'
                        elif prev_event.event_type == 'organism_communication':
                            tokens = prev_event.data.get('tokens_exchanged', 0)
                            explanation = f'Organism communication ({tokens} tokens) provides patterns for ML analysis'
                
                # Language → Language (pure language links)
                elif prev_event.component in ['language', 'butterfly_chat'] and new_event.component in ['language', 'butterfly_chat']:
                    if prev_event.event_type == 'word_assignment':
                        word = prev_event.data.get('word', 'unknown')
                        org_id = prev_event.data.get('organism_id', 'unknown')
                        explanation = f"Word '{word}' assigned to organism {org_id}"
                    elif new_event.event_type == 'word_assignment':
                        word = new_event.data.get('word', 'unknown')
                        org_id = new_event.data.get('organism_id', 'unknown')
                        explanation = f"System state triggers word assignment: '{word}' to organism {org_id}"
                    elif prev_event.event_type == 'vocabulary_growth':
                        vocab_size = prev_event.data.get('vocab_size', 0)
                        word = prev_event.data.get('word', 'unknown')
                        explanation = f"Vocabulary growth: word '{word}' added (vocab size: {vocab_size})"
                    elif new_event.event_type == 'vocabulary_growth':
                        vocab_size = new_event.data.get('vocab_size', 0)
                        word = new_event.data.get('word', 'unknown')
                        explanation = f"System state triggers vocabulary growth: '{word}' added (vocab size: {vocab_size})"
                    elif prev_event.event_type == 'organism_communication':
                        num_organisms = prev_event.data.get('num_organisms', 0)
                        explanation = f'Organism communication ({num_organisms} organisms) affects network'
                    elif new_event.event_type == 'organism_communication':
                        num_organisms = new_event.data.get('num_organisms', 0)
                        explanation = f'Network state triggers organism communication ({num_organisms} organisms)'
                    elif prev_event.event_type == 'neural_language_training':
                        explanation = 'Language training improves communication'
                    elif new_event.event_type == 'neural_language_training':
                        explanation = 'Communication patterns trigger language training'
                    elif prev_event.event_type == 'butterfly_chat_message':
                        explanation = 'User chat message triggers organism responses'
                    elif new_event.event_type == 'butterfly_chat_response':
                        explanation = 'Organism responds to user message'
                
                # Determine causation type: 'language' for pure language links, 'direct' for cross-component links
                causation_type = 'language' if (prev_event.component in ['language', 'butterfly_chat'] and 
                                                new_event.component in ['language', 'butterfly_chat']) else 'direct'
                
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type=causation_type,
                    strength=0.8,  # Language links strength
                    explanation=explanation,
                    metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
                )
            
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='direct',
                strength=0.8,
                explanation=direct_causations[key],
                metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
            )
        
        # FALLBACK: Same-component temporal causation
        # If events are from the same component and close in time, they're likely causally related
        if prev_event.component == new_event.component and time_diff < self.direct_causation_time_window * 2.0:
            # Calculate how many metrics changed
            shared_metrics = set(prev_event.data.keys()) & set(new_event.data.keys())
            changed_metrics = []
            for metric in shared_metrics:
                prev_val = prev_event.data.get(metric)
                new_val = new_event.data.get(metric)
                if isinstance(prev_val, (int, float)) and isinstance(new_val, (int, float)):
                    if abs(new_val - prev_val) > 0.001:
                        changed_metrics.append(metric)
            
            if changed_metrics:
                metrics_str = ', '.join(changed_metrics[:3])
                return CausationLink(
                    from_event=prev_event.event_id,
                    to_event=new_event.event_id,
                    causation_type='temporal',
                    strength=0.6,  # Lower strength for inferred temporal links
                    explanation=f"Sequential {prev_event.component} state changes ({metrics_str})",
                    metrics_involved=changed_metrics
                )
        
        return None
    
    def _add_causation_link(self, link: CausationLink):
        """Add a causation link to the graph"""
        # Ensure both nodes exist in the graph
        if link.from_event not in self.causation_graph:
            from_event = self.events.get(link.from_event)
            if from_event:
                self.causation_graph.add_node(link.from_event, **from_event.to_dict())
        if link.to_event not in self.causation_graph:
            to_event = self.events.get(link.to_event)
            if to_event:
                self.causation_graph.add_node(link.to_event, **to_event.to_dict())
        
        if not self.causation_graph.has_edge(link.from_event, link.to_event):
            self.causation_graph.add_edge(
                link.from_event,
                link.to_event,
                causation_type=link.causation_type,
                strength=link.strength,
                explanation=link.explanation,
                metrics_involved=link.metrics_involved
            )
    
    def explore_backwards(self, event_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        What caused this event?
        Returns chain of events leading to this event
        """
        if event_id not in self.events:
            return []
        
        # Find all events that led to this one
        trail = []
        visited = set()
        
        def traverse_backwards(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            event = self.events[current_id]
            
            # Find predecessors
            predecessors = list(self.causation_graph.predecessors(current_id))
            
            if not predecessors:
                # Root cause
                trail.append({
                    'event': event.to_dict(),
                    'depth': depth,
                    'is_root': True
                })
                return
            
            # Add current event
            trail.append({
                'event': event.to_dict(),
                'depth': depth,
                'caused_by': [self.events[p].to_dict() for p in predecessors]
            })
            
            # Recurse
            for pred_id in predecessors:
                traverse_backwards(pred_id, depth + 1)
        
        traverse_backwards(event_id, 0)
        
        # Sort by depth (deepest first = root causes)
        trail.sort(key=lambda x: x['depth'], reverse=True)
        
        return trail
    
    def explore_forwards(self, event_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        What did this event cause?
        Returns chain of events caused by this event
        """
        if event_id not in self.events:
            return []
        
        trail = []
        visited = set()
        
        def traverse_forwards(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            event = self.events[current_id]
            
            # Find successors
            successors = list(self.causation_graph.successors(current_id))
            
            if not successors:
                # Final effect
                trail.append({
                    'event': event.to_dict(),
                    'depth': depth,
                    'is_final': True
                })
                return
            
            # Add current event
            trail.append({
                'event': event.to_dict(),
                'depth': depth,
                'caused': [self.events[s].to_dict() for s in successors]
            })
            
            # Recurse
            for succ_id in successors:
                traverse_forwards(succ_id, depth + 1)
        
        traverse_forwards(event_id, 0)
        
        # Sort by depth (shallowest first = immediate effects)
        trail.sort(key=lambda x: x['depth'])
        
        return trail
    
    def find_path(self, from_event_id: str, to_event_id: str) -> Optional[List[str]]:
        """
        Find shortest causation path between two events
        """
        try:
            path = nx.shortest_path(self.causation_graph, from_event_id, to_event_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_event_summary(self, event_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of an event"""
        # CRITICAL: Use lock to ensure thread-safe access
        with self.graph_lock:
            # Try exact match first
            if event_id not in self.events:
                # Try normalizing event ID (handle variations like evt_xxx vs evt-xxx)
                normalized_id = event_id
                if event_id.startswith('evt') and not event_id.startswith('evt_'):
                    normalized_id = 'evt_' + event_id[3:] if len(event_id) > 3 else event_id
                
                if normalized_id not in self.events:
                    # Log available event IDs for debugging (check for similar IDs)
                    available_ids = list(self.events.keys())
                    similar_ids = [eid for eid in available_ids if event_id in eid or eid in event_id][:10]
                    recent_ids = available_ids[-20:] if len(available_ids) > 20 else available_ids
                    
                    logger.warning(f"[EVENT_LOOKUP] ❌ Event not found in get_event_summary: {event_id} (normalized: {normalized_id})")
                    logger.warning(f"[EVENT_LOOKUP] Total events in dict: {len(self.events)}")
                    logger.warning(f"[EVENT_LOOKUP] Recent event IDs (last 20): {recent_ids}")
                    if similar_ids:
                        logger.warning(f"[EVENT_LOOKUP] Similar IDs found: {similar_ids}")
                    
                    return {
                        'error': f'Event not found: {event_id}',
                        'normalized_id': normalized_id,
                        'available_event_count': len(self.events),
                        'recent_event_ids': recent_ids,
                        'similar_event_ids': similar_ids
                    }
                
                event_id = normalized_id
                logger.debug(f"[EVENT_LOOKUP] Event ID normalized: {normalized_id} -> {event_id}")
            
            event = self.events[event_id]
            logger.debug(f"[EVENT_LOOKUP] ✅ Found event: {event_id} (type={event.event_type}, component={event.component})")
            
            # Get causation info (must be inside lock for thread safety)
            predecessors = list(self.causation_graph.predecessors(event_id))
            successors = list(self.causation_graph.successors(event_id))
            
            return {
                'event': event.to_dict(),
                'caused_by': len(predecessors),
                'caused': len(successors),
                'predecessor_events': [self.events[p].to_dict() for p in predecessors[:5] if p in self.events],
                'successor_events': [self.events[s].to_dict() for s in successors[:5] if s in self.events],
                'causation_links': [
                    {
                        'from': self.causation_graph.nodes[p]['event'] if p in self.causation_graph.nodes and 'event' in self.causation_graph.nodes[p] else {},
                        'to': event.to_dict(),
                        'type': self.causation_graph[p][event_id].get('causation_type', 'unknown') if self.causation_graph.has_edge(p, event_id) else 'unknown',
                        'strength': self.causation_graph[p][event_id].get('strength', 0.0) if self.causation_graph.has_edge(p, event_id) else 0.0,
                        'explanation': self.causation_graph[p][event_id].get('explanation', '') if self.causation_graph.has_edge(p, event_id) else ''
                    }
                    for p in predecessors[:5] if p in self.events
                ]
            }
    
    def search_events(self, query: str) -> List[Dict[str, Any]]:
        """Search events by component, type, or metric"""
        results = []
        query_lower = query.lower()
        
        for event_id, event in self.events.items():
            # Search in component
            if query_lower in event.component.lower():
                results.append(event.to_dict())
                continue
            
            # Search in event type
            if query_lower in event.event_type.lower():
                results.append(event.to_dict())
                continue
            
            # Search in data
            for key, value in event.data.items():
                if query_lower in key.lower() or query_lower in str(value).lower():
                    results.append(event.to_dict())
                    break
        
        return results
    
    def get_causation_stats(self) -> Dict[str, Any]:
        """Get statistics about the causation graph"""
        return {
            'total_events': len(self.events),
            'total_links': self.causation_graph.number_of_edges(),
            'components': list(self.events_by_component.keys()),
            'event_types': list(self.events_by_type.keys()),
            'metrics_tracked': list(self.metric_history.keys()),
            'graph_density': nx.density(self.causation_graph),
            'strongest_links': sorted(
                [
                    {
                        'from': self.events[u].to_dict() if u in self.events else {},
                        'to': self.events[v].to_dict() if v in self.events else {},
                        'strength': data.get('strength', 0.0),
                        'explanation': data.get('explanation', '')
                    }
                    for u, v, data in self.causation_graph.edges(data=True)
                ],
                key=lambda x: x['strength'],
                reverse=True
            )[:10]
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 🔬 ILLUMINATION ENGINE - Deep Causal Intelligence
    # ═══════════════════════════════════════════════════════════════════════════

    def find_root_causes(self, event_id: str, max_depth: int = 20) -> Dict[str, Any]:
        """
        🔍 DEEP ROOT CAUSE ANALYSIS
        
        Trace ALL the way back to find the ultimate origins.
        Returns a ranked list of root causes with their causal chains.
        
        This is the "why did this REALLY happen?" query.
        """
        if event_id not in self.events:
            return {'error': 'Event not found', 'root_causes': []}
        
        root_causes = []
        visited = set()
        paths_to_roots = {}  # root_id -> list of paths to it
        
        def trace_to_roots(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            path = path + [current_id]
            
            predecessors = list(self.causation_graph.predecessors(current_id))
            
            if not predecessors:
                # Found a root cause!
                if current_id not in paths_to_roots:
                    paths_to_roots[current_id] = []
                paths_to_roots[current_id].append(path)
            else:
                for pred_id in predecessors:
                    trace_to_roots(pred_id, path, depth + 1)
        
        trace_to_roots(event_id, [], 0)
        
        # Build rich root cause analysis
        for root_id, paths in paths_to_roots.items():
            if root_id not in self.events:
                continue
            
            root_event = self.events[root_id]
            shortest_path = min(paths, key=len)
            
            # Calculate total causal strength along path
            total_strength = 0.0
            chain_explanations = []
            for i in range(len(shortest_path) - 1):
                from_id, to_id = shortest_path[i], shortest_path[i + 1]
                if self.causation_graph.has_edge(from_id, to_id):
                    edge_data = self.causation_graph[from_id][to_id]
                    total_strength += edge_data.get('strength', 0.5)
                    chain_explanations.append(edge_data.get('explanation', 'Unknown causation'))
            
            avg_strength = total_strength / max(1, len(shortest_path) - 1)
            
            root_causes.append({
                'root_event': root_event.to_dict(),
                'depth': len(shortest_path) - 1,
                'causal_chain': [self.events[eid].to_dict() for eid in shortest_path if eid in self.events],
                'chain_explanations': chain_explanations,
                'avg_strength': round(avg_strength, 3),
                'num_paths': len(paths),
                'narrative': self._build_causation_narrative(shortest_path, chain_explanations)
            })
        
        # Sort by relevance: higher strength and shorter depth = more relevant
        root_causes.sort(key=lambda x: (x['avg_strength'] * 2 - x['depth'] * 0.1), reverse=True)
        
        return {
            'event': self.events[event_id].to_dict(),
            'root_causes': root_causes[:10],  # Top 10 root causes
            'total_roots_found': len(root_causes),
            'analysis_depth': max_depth
        }

    def analyze_impact(self, event_id: str, max_depth: int = 20) -> Dict[str, Any]:
        """
        💥 IMPACT ANALYSIS
        
        What were ALL the downstream effects of this event?
        Returns a ranked list of consequences with impact metrics.
        
        This is the "what did this set in motion?" query.
        """
        if event_id not in self.events:
            return {'error': 'Event not found', 'impacts': []}
        
        impacts = []
        visited = set()
        leaf_effects = {}  # leaf_id -> list of paths to it
        
        def trace_effects(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            path = path + [current_id]
            
            successors = list(self.causation_graph.successors(current_id))
            
            if not successors and current_id != event_id:
                # Found a leaf effect!
                if current_id not in leaf_effects:
                    leaf_effects[current_id] = []
                leaf_effects[current_id].append(path)
            else:
                for succ_id in successors:
                    trace_effects(succ_id, path, depth + 1)
        
        trace_effects(event_id, [], 0)
        
        # Also count total affected events
        all_affected = set()
        def count_all_effects(current_id: str, depth: int):
            if depth > max_depth or current_id in all_affected:
                return
            all_affected.add(current_id)
            for succ_id in self.causation_graph.successors(current_id):
                count_all_effects(succ_id, depth + 1)
        
        count_all_effects(event_id, 0)
        all_affected.discard(event_id)  # Don't count the source event
        
        # Build impact analysis
        for leaf_id, paths in leaf_effects.items():
            if leaf_id not in self.events:
                continue
            
            leaf_event = self.events[leaf_id]
            shortest_path = min(paths, key=len)
            
            # Calculate propagation strength
            total_strength = 0.0
            chain_explanations = []
            for i in range(len(shortest_path) - 1):
                from_id, to_id = shortest_path[i], shortest_path[i + 1]
                if self.causation_graph.has_edge(from_id, to_id):
                    edge_data = self.causation_graph[from_id][to_id]
                    total_strength += edge_data.get('strength', 0.5)
                    chain_explanations.append(edge_data.get('explanation', 'Unknown effect'))
            
            avg_strength = total_strength / max(1, len(shortest_path) - 1)
            
            impacts.append({
                'effect_event': leaf_event.to_dict(),
                'propagation_depth': len(shortest_path) - 1,
                'effect_chain': [self.events[eid].to_dict() for eid in shortest_path if eid in self.events],
                'chain_explanations': chain_explanations,
                'propagation_strength': round(avg_strength, 3),
                'num_paths': len(paths),
                'severity': self._calculate_severity(leaf_event)
            })
        
        # Sort by severity and propagation strength
        impacts.sort(key=lambda x: (x['severity'] * 2 + x['propagation_strength']), reverse=True)
        
        # Categorize affected events by component
        affected_by_component = defaultdict(int)
        for eid in all_affected:
            if eid in self.events:
                affected_by_component[self.events[eid].component] += 1
        
        return {
            'source_event': self.events[event_id].to_dict(),
            'total_affected_events': len(all_affected),
            'affected_by_component': dict(affected_by_component),
            'leaf_effects': impacts[:15],  # Top 15 most significant effects
            'total_leaf_effects': len(impacts),
            'analysis_depth': max_depth
        }

    def _calculate_severity(self, event: Event) -> float:
        """Calculate severity score for an event (0.0-1.0)"""
        severity = 0.5  # baseline
        
        # High severity event types
        high_severity_types = ['collapse', 'threshold_crossed', 'phase_transition', 'anomaly_spike', 'cluster_collapse']
        if any(t in event.event_type.lower() for t in high_severity_types):
            severity += 0.3
        
        # Check data for concerning metrics
        data = event.data
        if data.get('is_collapsed', False):
            severity += 0.2
        if 'violation_pressure' in data:
            vp = data['violation_pressure']
            if isinstance(vp, (int, float)) and vp > 0.75:
                severity += 0.2
        if 'modularity' in data:
            mod = data['modularity']
            if isinstance(mod, (int, float)) and mod < 0.3:
                severity += 0.1
        
        return min(1.0, severity)

    def _build_causation_narrative(self, path: List[str], explanations: List[str]) -> str:
        """Build a human-readable narrative of a causation chain"""
        if not path or len(path) < 2:
            return "Direct event (no causal chain)"
        
        narrative_parts = []
        for i, event_id in enumerate(path):
            if event_id not in self.events:
                continue
            event = self.events[event_id]
            
            if i == 0:
                # Starting event
                narrative_parts.append(f"It started with {event.component.upper()}: {event.event_type}")
            elif i == len(path) - 1:
                # Final event
                narrative_parts.append(f"Finally causing {event.component.upper()}: {event.event_type}")
            else:
                # Intermediate events
                if i - 1 < len(explanations):
                    narrative_parts.append(f"which {explanations[i-1].lower()}")
        
        return " → ".join(narrative_parts) if narrative_parts else "Unknown chain"
    
    def _build_propagation_narrative(self, path: List[str], explanations: List[str]) -> str:
        """Build a human-readable narrative of a propagation chain (for impact analysis)"""
        if not path or len(path) < 2:
            return "Direct effect (no propagation chain)"
        
        narrative_parts = []
        for i, event_id in enumerate(path):
            if event_id not in self.events:
                continue
            event = self.events[event_id]
            
            if i == 0:
                # Source event
                narrative_parts.append(f"Started from {event.component.upper()}: {event.event_type}")
            elif i == len(path) - 1:
                # Final effect
                narrative_parts.append(f"resulted in {event.component.upper()}: {event.event_type}")
            else:
                # Intermediate propagation
                if i - 1 < len(explanations):
                    narrative_parts.append(f"which {explanations[i-1].lower()}")
        
        return " → ".join(narrative_parts) if narrative_parts else "Unknown propagation"

    def explain_event(self, event_id: str) -> Dict[str, Any]:
        """
        📖 COMPLETE EVENT EXPLANATION
        
        Answer: "Why did this happen and what did it cause?"
        Returns a comprehensive narrative with all context.
        """
        if event_id not in self.events:
            return {'error': 'Event not found'}
        
        event = self.events[event_id]
        
        # Get root causes
        root_analysis = self.find_root_causes(event_id, max_depth=10)
        
        # Get impacts
        impact_analysis = self.analyze_impact(event_id, max_depth=10)
        
        # Get direct predecessors and successors
        predecessors = list(self.causation_graph.predecessors(event_id))
        successors = list(self.causation_graph.successors(event_id))
        
        # Build rich explanation
        pred_details = []
        for pred_id in predecessors[:5]:
            if pred_id in self.events and self.causation_graph.has_edge(pred_id, event_id):
                edge = self.causation_graph[pred_id][event_id]
                pred_event = self.events[pred_id]
                pred_details.append({
                    'event': pred_event.to_dict(),
                    'causation_type': edge.get('causation_type', 'unknown'),
                    'strength': edge.get('strength', 0.0),
                    'explanation': edge.get('explanation', ''),
                    'metric_deltas': self._calculate_metric_deltas(pred_event, event)
                })
        
        succ_details = []
        for succ_id in successors[:5]:
            if succ_id in self.events and self.causation_graph.has_edge(event_id, succ_id):
                edge = self.causation_graph[event_id][succ_id]
                succ_event = self.events[succ_id]
                succ_details.append({
                    'event': succ_event.to_dict(),
                    'causation_type': edge.get('causation_type', 'unknown'),
                    'strength': edge.get('strength', 0.0),
                    'explanation': edge.get('explanation', ''),
                    'metric_deltas': self._calculate_metric_deltas(event, succ_event)
                })
        
        return {
            'event': event.to_dict(),
            'summary': self._generate_event_summary(event, root_analysis, impact_analysis),
            'immediate_causes': pred_details,
            'immediate_effects': succ_details,
            'root_causes': root_analysis.get('root_causes', [])[:3],
            'major_impacts': impact_analysis.get('leaf_effects', [])[:3],
            'total_upstream_events': len(root_analysis.get('root_causes', [])),
            'total_downstream_events': impact_analysis.get('total_affected_events', 0),
            'severity': self._calculate_severity(event)
        }

    def _calculate_metric_deltas(self, from_event: Event, to_event: Event) -> Dict[str, Any]:
        """Calculate metric changes between two events"""
        deltas = {}
        common_metrics = set(from_event.data.keys()) & set(to_event.data.keys())
        
        for metric in common_metrics:
            from_val = from_event.data.get(metric)
            to_val = to_event.data.get(metric)
            
            if isinstance(from_val, (int, float)) and isinstance(to_val, (int, float)):
                delta = to_val - from_val
                if from_val != 0:
                    pct_change = round((delta / from_val) * 100, 2)
                else:
                    pct_change = 100.0 if delta > 0 else (-100.0 if delta < 0 else 0.0)
                
                if abs(delta) > 0.001:  # Only include meaningful changes
                    deltas[metric] = {
                        'from': round(from_val, 4) if isinstance(from_val, float) else from_val,
                        'to': round(to_val, 4) if isinstance(to_val, float) else to_val,
                        'delta': round(delta, 4) if isinstance(delta, float) else delta,
                        'pct_change': pct_change,
                        'direction': '↑' if delta > 0 else ('↓' if delta < 0 else '→')
                    }
        
        return deltas
    
    def _generate_event_summary(self, event: Event, root_analysis: Dict, impact_analysis: Dict,
                                context_memory: Optional[Any] = None) -> str:
        """Generate a human-readable summary of an event with AI-powered reasoning"""
        parts = []
        
        # Language event types (including atomic language events)
        language_event_types = {'vocabulary_growth', 'organism_communication', 
                               'neural_language_training', 'butterfly_chat_message', 
                               'butterfly_chat_response',
                               # 🆕 Atomic language events
                               'linguistic_atom_update', 'association_formed', 
                               'association_updated', 'concept_acquired',
                               # 🆕 Concept trading events
                               'concept_taught'}
        language_components = {'language', 'butterfly_chat', 'vocabulary', 'communication', 'chat'}
        is_language_event = (event.component.lower() in language_components or 
                           event.event_type in language_event_types)
        
        # Atomic language event detection
        is_atomic_language = event.event_type in {'linguistic_atom_update', 'association_formed', 
                                                   'association_updated', 'concept_acquired',
                                                   'concept_taught'}
        
        # Neural decision event with reasoning
        is_neural_decision = event.event_type == 'neural_decision'
        
        # What happened - with enhanced context
        if is_neural_decision:
            action = event.data.get('action', 'unknown')
            confidence = event.data.get('confidence', 0)
            parts.append(f"🧠 NEURAL decided to {action.upper()} (confidence: {confidence:.1%})")
        elif is_language_event:
            parts.append(f"🦋 {event.component.upper()} generated a {event.event_type} event.")
        else:
            parts.append(f"📍 {event.component.upper()} generated a {event.event_type} event.")
        
        # 🧠 NEW: Include neural reasoning if available
        if is_neural_decision and 'reasoning' in event.data:
            reasoning = event.data['reasoning']
            parts.append(f"🧠 Reasoning: {reasoning}")
        
        # VP adjustments for neural decisions
        if is_neural_decision and event.data.get('vp_adjustments'):
            vp_adj = event.data['vp_adjustments'][:2]  # First 2 adjustments
            if vp_adj:
                parts.append(f"⚖️ VP factors: {', '.join(vp_adj)}")
        
        # Language-specific data with semantic context
        if is_language_event:
            if event.event_type == 'vocabulary_growth':
                vocab_size = event.data.get('vocab_size', event.data.get('new_words', 0))
                growth = event.data.get('growth', 0)
                parts.append(f"📚 Vocabulary: {vocab_size} words (+{growth})")
                # Add semantic context if context_memory has knowledge_web
                if context_memory and hasattr(context_memory, 'knowledge_web'):
                    word = event.data.get('word')
                    if word:
                        relations = context_memory.knowledge_web.get_relations(word)
                        if relations:
                            related = [f"{r.target}" for r in relations[:3]]
                            parts.append(f"📖 Related: {', '.join(related)}")
            
            # 🆕 Atomic language events - fully trackable linguistic changes
            elif event.event_type == 'linguistic_atom_update':
                concept = event.data.get('concept', 'unknown')
                old_str = event.data.get('old_strength', 0)
                new_str = event.data.get('new_strength', 0)
                reason = event.data.get('reason', 'unknown')
                delta = new_str - old_str
                direction = "↑" if delta > 0 else "↓"
                parts.append(f"🧬 Concept '{concept}' {direction} {abs(delta):.2f} ({reason})")
                org_id = event.data.get('organism_id', '')
                if org_id:
                    parts.append(f"🦠 Organism: {org_id[:8]}...")
            
            elif event.event_type == 'association_formed':
                source = event.data.get('source_concept', 'unknown')
                target = event.data.get('target_concept', 'unknown')
                strength = event.data.get('new_strength', 0)
                reason = event.data.get('reason', 'unknown')
                parts.append(f"🔗 NEW association: '{source}' → '{target}' (strength: {strength:.2f})")
                parts.append(f"💡 Reason: {reason}")
            
            elif event.event_type == 'association_updated':
                source = event.data.get('source_concept', 'unknown')
                target = event.data.get('target_concept', 'unknown')
                old_str = event.data.get('old_strength', 0)
                new_str = event.data.get('new_strength', 0)
                delta = new_str - old_str
                direction = "strengthened" if delta > 0 else "weakened"
                parts.append(f"🔗 Association '{source}' → '{target}' {direction} ({delta:+.2f})")
            
            elif event.event_type == 'concept_acquired':
                concept = event.data.get('concept', 'unknown')
                source = event.data.get('source', 'unknown')
                reason = event.data.get('reason', 'unknown')
                total = event.data.get('total_concepts', 0)
                parts.append(f"🌱 NEW concept learned: '{concept}' (via {source})")
                parts.append(f"📚 Total concepts: {total} | Reason: {reason}")
            
            # 🆕 Concept trading events
            elif event.event_type == 'concept_taught':
                concept = event.data.get('concept', 'unknown')
                teacher_id = event.data.get('teacher_id', 'unknown')
                learner_id = event.data.get('learner_id', 'unknown')
                success = event.data.get('success', False)
                teaching_strength = event.data.get('teaching_strength', 0)
                learned_strength = event.data.get('learned_strength', 0)
                
                if success:
                    parts.append(f"📤 Concept TRADED: '{concept}'")
                    parts.append(f"👨‍🏫 Teacher: {teacher_id} (str={teaching_strength:.2f}) → Learner: {learner_id} (str={learned_strength:.2f})")
                    
                    # Track association transfer if present
                    associations_transferred = event.data.get('associations_transferred', 0)
                    if associations_transferred > 0:
                        parts.append(f"🔗 {associations_transferred} associations also transferred")
                else:
                    reason = event.data.get('reason', 'unknown')
                    parts.append(f"❌ Concept teaching FAILED: '{concept}'")
                    parts.append(f"📝 Reason: {reason}")
            
            elif event.event_type == 'organism_communication':
                num_orgs = event.data.get('num_organisms', event.data.get('organism_count', 0))
                tokens = event.data.get('tokens_exchanged', event.data.get('token_count', 0))
                parts.append(f"💬 Communication: {num_orgs} organisms, {tokens} tokens")
            elif event.event_type in {'butterfly_chat_message', 'butterfly_chat_response'}:
                message = event.data.get('message', event.data.get('response', ''))
                if message:
                    parts.append(f"💭 Message: {message[:50]}...")
        
        # ═══════════════════════════════════════════════════════════════
        # CONFIG EVENTS (Atomic Config System)
        # ═══════════════════════════════════════════════════════════════
        if event.component == 'config':
            if event.event_type == 'config_atom_update':
                param = event.data.get('param_name', 'unknown')
                domain = event.data.get('domain', 'unknown')
                old_val = event.data.get('old_value', '?')
                new_val = event.data.get('new_value', '?')
                reason = event.data.get('reason', 'unknown')
                strength = event.data.get('strength', 0)
                parts.append(f"⚙️ Config [{domain}] {param}: {old_val} → {new_val}")
                parts.append(f"📊 Confidence: {strength:.1%} | Reason: {reason}")
            
            elif event.event_type == 'config_outcome':
                success = event.data.get('success', False)
                domain = event.data.get('domain', 'all')
                context = event.data.get('context', '')
                emoji = "✅" if success else "❌"
                parts.append(f"{emoji} Config outcome [{domain}]: {'SUCCESS' if success else 'FAILURE'}")
                if context:
                    parts.append(f"📝 Context: {context}")
            
            elif event.event_type == 'pytorch_training_update':
                epoch = event.data.get('epoch', 0)
                metrics = event.data.get('metrics', {})
                improved = event.data.get('is_improvement', False)
                loss = metrics.get('loss', 0)
                emoji = "📈" if improved else "📉"
                parts.append(f"{emoji} PyTorch Epoch {epoch}: loss={loss:.4f}")
                parts.append(f"🔧 LR={event.data.get('current_lr', '?')}, Batch={event.data.get('current_batch', '?')}")
            
            elif event.event_type == 'highlander_config_absorption':
                winner = event.data.get('winner_id', 'unknown')
                loser = event.data.get('loser_id', 'unknown')
                absorbed = event.data.get('absorbed_params', {})
                parts.append(f"⚔️ HIGHLANDER: {winner} absorbed configs from {loser}")
                parts.append(f"🏆 Absorbed {len(absorbed)} parameters: {list(absorbed.keys())[:3]}")
        
        # ═══════════════════════════════════════════════════════════════
        # HIGHLANDER PROTOCOL EVENTS
        # ═══════════════════════════════════════════════════════════════
        if event.component == 'highlander':
            round_num = event.data.get('round', 0)
            phase = event.data.get('phase', 'unknown')
            
            if event.event_type == 'highlander_battle_concluded':
                winner = event.data.get('winner', 'unknown')
                loser = event.data.get('loser', 'unknown')
                margin = event.data.get('margin', 0)
                concepts = event.data.get('concepts_transferred', [])
                parts.append(f"⚔️ BATTLE: {winner} defeated {loser} (margin: {margin:.1%})")
                if concepts:
                    parts.append(f"📚 Absorbed concepts: {concepts[:3]}")
            
            elif event.event_type == 'highlander_organism_fallen':
                org_id = event.data.get('organism_id', 'unknown')
                reason = event.data.get('reason', 'unknown')
                remaining = event.data.get('remaining', 0)
                parts.append(f"💀 FALLEN: {org_id} ({reason})")
                parts.append(f"🏟️ {remaining} organisms remain")
            
            elif event.event_type == 'highlander_alliance_formed':
                members = event.data.get('members', [])
                parts.append(f"🤝 ALLIANCE FORMED: {' + '.join(members)}")
            
            elif event.event_type == 'highlander_predation_success':
                predator = event.data.get('predator', 'unknown')
                prey = event.data.get('prey', 'unknown')
                parts.append(f"🦁 HUNT: {predator} consumed {prey}")
            
            elif event.event_type == 'highlander_champion_crowned':
                champion = event.data.get('champion_id', 'unknown')
                lineage = event.data.get('lineage_length', 0)
                concepts = event.data.get('concepts_accumulated', 0)
                parts.append(f"👑 CHAMPION: {champion}")
                parts.append(f"⚔️ Lineage: {lineage} absorbed | 📚 Concepts: {concepts}")
            
            elif event.event_type == 'highlander_arena_reset':
                prev_champions = event.data.get('previous_champions', 0)
                parts.append(f"🏟️ ARENA RESET - Previous champions: {prev_champions}")
            
            elif event.event_type == 'highlander_germination_needed':
                needed = event.data.get('needed', 0)
                current = event.data.get('current_population', 0)
                parts.append(f"🌱 GERMINATION: {needed} new challengers needed (pop: {current})")
        
        # ═══════════════════════════════════════════════════════════════
        # GERMINATION POOL EVENTS
        # ═══════════════════════════════════════════════════════════════
        if event.component == 'germination_pool':
            if event.event_type == 'essence_collected':
                donor = event.data.get('donor_id', 'unknown')
                reason = event.data.get('death_reason', 'unknown')
                killer = event.data.get('killer_id', None)
                fitness = event.data.get('fitness_score', 0)
                pool_size = event.data.get('pool_size', 0)
                killer_str = f" by {killer}" if killer else ""
                parts.append(f"💀→🧬 Collected essence from {donor} ({reason}{killer_str})")
                parts.append(f"📊 Fitness: {fitness:.2f} | Pool: {pool_size} samples")
            
            elif event.event_type == 'organism_germinated':
                org_id = event.data.get('organism_id', 'unknown')
                strategy = event.data.get('strategy', 'unknown')
                parents = event.data.get('parent_ids', [])
                generation = event.data.get('generation', 0)
                vigor = event.data.get('vigor', 1.0)
                parts.append(f"🌱 BORN: {org_id} (Strategy: {strategy.upper()})")
                if parents:
                    parts.append(f"👨‍👩‍👧 Parents: {', '.join(parents[:3])}")
                parts.append(f"🧬 Gen {generation} | Vigor: {vigor:.1f}")
            
            elif event.event_type == 'germination_failed':
                candidate_id = event.data.get('candidate_id', 'unknown')
                strategy = event.data.get('strategy', 'unknown')
                error = event.data.get('error', 'unknown')
                parts.append(f"❌ Germination failed: {candidate_id} ({strategy})")
                parts.append(f"⚠️ Error: {error}")
        
        # ML events with cluster/anomaly context
        if event.component == 'ml_analysis':
            if event.event_type == 'phenotype_emergence':
                n_clusters = event.data.get('n_clusters', 0)
                concept_tags = event.data.get('concept_tags', {})
                parts.append(f"🔬 {n_clusters} behavioral phenotypes detected")
                if concept_tags:
                    concepts = list(concept_tags.values())[:3]
                    parts.append(f"📊 Phenotypes: {', '.join(concepts)}")
            elif event.event_type == 'anomaly_spike':
                count = event.data.get('anomaly_count', 0)
                ratio = event.data.get('anomaly_ratio', 0)
                parts.append(f"⚠️ {count} anomalies ({ratio:.1%} of population)")
        
        # Key metrics (excluding already shown data)
        important_keys = ['modularity', 'organism_count', 'violation_pressure', 'phase', 'is_collapsed', 'fitness']
        shown_keys = {'action', 'reasoning', 'vp_adjustments', 'vocab_size', 'word', 'n_clusters', 'anomaly_count'}
        key_data = {k: v for k, v in event.data.items() if k in important_keys and k not in shown_keys}
        if key_data:
            data_str = ', '.join([f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in key_data.items()])
            parts.append(f"📈 Metrics: {data_str}")
        
        # Causes with depth
        num_roots = len(root_analysis.get('root_causes', []))
        if num_roots > 0:
            top_root = root_analysis['root_causes'][0]
            depth = top_root['depth']
            parts.append(f"🔍 Root: {top_root['root_event']['component']}.{top_root['root_event']['event_type']} ({depth} steps)")
        
        # Effects with impact count
        num_affected = impact_analysis.get('total_affected_events', 0)
        if num_affected > 0:
            by_component = impact_analysis.get('affected_by_component', {})
            if by_component:
                top_affected = max(by_component.items(), key=lambda x: x[1], default=('', 0))
                parts.append(f"💥 Impact: {num_affected} events (mostly {top_affected[0]})")
            else:
                parts.append(f"💥 Impact: {num_affected} downstream event(s)")
        
        return " | ".join(parts)
    
    def search_advanced(self, 
                       query: str = None,
                       component: str = None,
                       event_type: str = None,
                       time_start: float = None,
                       time_end: float = None,
                       min_severity: float = None,
                       has_caused: bool = None,
                       has_been_caused: bool = None,
                       word: str = None,
                       limit: int = 50,
                       context_memory: Optional[Any] = None) -> Dict[str, Any]:
        """
        🔎 ADVANCED SEARCH with filters and aggregation
        
        Find events matching complex criteria.
        Returns events with metadata about the search.
        
        NEW: Language support:
        - component='language' or component='butterfly_chat' for language events
        - word='<word>' to find events related to specific words
        - concept='<concept>' to find events related to specific linguistic atoms
        """
        results = []
        
        # Language event types (including atomic language events)
        language_event_types = {'vocabulary_growth', 'organism_communication', 
                               'neural_language_training', 'butterfly_chat_message', 
                               'butterfly_chat_response',
                               # 🆕 Atomic language events
                               'linguistic_atom_update', 'association_formed',
                               'association_updated', 'concept_acquired',
                               # 🆕 Concept trading events
                               'concept_taught'}
        language_components = {'language', 'butterfly_chat', 'vocabulary', 'communication', 'chat'}
        
        for event_id, event in self.events.items():
            # Text query filter
            if query:
                query_lower = query.lower()
                match = False
                if query_lower in event.component.lower():
                    match = True
                elif query_lower in event.event_type.lower():
                    match = True
                else:
                    for key, value in event.data.items():
                        if query_lower in str(key).lower() or query_lower in str(value).lower():
                            match = True
                            break
                if not match:
                    continue
            
            # Component filter (with language normalization)
            if component:
                comp_normalized = component.lower()
                # Normalize language component variations
                if comp_normalized in language_components:
                    comp_normalized = 'language' if comp_normalized in {'language', 'vocabulary', 'communication'} else 'butterfly_chat'
                
                event_comp_normalized = event.component.lower()
                if event_comp_normalized in language_components:
                    event_comp_normalized = 'language' if event_comp_normalized in {'language', 'vocabulary', 'communication'} else 'butterfly_chat'
                
                if event_comp_normalized != comp_normalized:
                    continue
            
            # Word filter (NEW: language-specific)
            if word:
                word_lower = word.lower()
                # Check if event is language-related
                is_language_event = (event.component.lower() in language_components or 
                                   event.event_type in language_event_types)
                
                if is_language_event:
                    # Check event data for word mentions
                    word_found = False
                    for key, value in event.data.items():
                        if word_lower in str(key).lower() or word_lower in str(value).lower():
                            word_found = True
                            break
                    
                    # Check context_memory for word associations
                    if not word_found and context_memory and hasattr(context_memory, 'language_anchors'):
                        # Get organism IDs from event
                        org_ids = event.data.get('organism_ids', [])
                        if not org_ids:
                            org_id = event.data.get('organism_id')
                            if org_id:
                                org_ids = [org_id]
                        
                        # Check if any organism uses this word
                        for org_id in org_ids:
                            org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
                            if org_id_int in context_memory.node_word_associations:
                                if word_lower in {w.lower() for w in context_memory.node_word_associations[org_id_int]}:
                                    word_found = True
                                    break
                    
                    if not word_found:
                        continue
            
            # Event type filter
            if event_type and event_type.lower() not in event.event_type.lower():
                continue
            
            # Time range filter
            if time_start and event.timestamp < time_start:
                continue
            if time_end and event.timestamp > time_end:
                continue
            
            # Severity filter
            if min_severity:
                severity = self._calculate_severity(event)
                if severity < min_severity:
                    continue
            
            # Causation filters - check if node exists in graph first
            node_in_graph = self.causation_graph.has_node(event_id)
            
            if has_caused is not None:
                has_successors = node_in_graph and len(list(self.causation_graph.successors(event_id))) > 0
                if has_caused and not has_successors:
                    continue
                if not has_caused and has_successors:
                    continue
            
            if has_been_caused is not None:
                has_predecessors = node_in_graph and len(list(self.causation_graph.predecessors(event_id))) > 0
                if has_been_caused and not has_predecessors:
                    continue
                if not has_been_caused and has_predecessors:
                    continue
            
            # Include the event
            num_causes = len(list(self.causation_graph.predecessors(event_id))) if node_in_graph else 0
            num_effects = len(list(self.causation_graph.successors(event_id))) if node_in_graph else 0
            
            results.append({
                'event': event.to_dict(),
                'severity': self._calculate_severity(event),
                'num_causes': num_causes,
                'num_effects': num_effects
            })
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x['event']['timestamp'], reverse=True)
        
        # Aggregations
        component_counts = defaultdict(int)
        type_counts = defaultdict(int)
        for r in results:
            component_counts[r['event']['component']] += 1
            type_counts[r['event']['event_type']] += 1
        
        return {
            'results': results[:limit],
            'total_matches': len(results),
            'returned': min(len(results), limit),
            'aggregations': {
                'by_component': dict(component_counts),
                'by_type': dict(type_counts)
            },
            'filters_applied': {
                'query': query,
                'component': component,
                'event_type': event_type,
                'time_range': [time_start, time_end] if time_start or time_end else None,
                'min_severity': min_severity,
                'has_caused': has_caused,
                'has_been_caused': has_been_caused
            }
        }
    
    def get_most_consequential(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        🏆 MOST CONSEQUENTIAL EVENTS
        
        Find events that caused the most downstream effects.
        These are the "big bang" moments in your system.
        """
        event_impact_scores = []
        
        for event_id in self.events:
            # Skip events not in the graph
            if not self.causation_graph.has_node(event_id):
                continue
                
            # Count downstream effects
            visited = set()
            def count_effects(current_id: str, depth: int):
                if depth > 50 or current_id in visited:
                    return 0
                if not self.causation_graph.has_node(current_id):
                    return 0
                visited.add(current_id)
                count = 1
                for succ_id in self.causation_graph.successors(current_id):
                    count += count_effects(succ_id, depth + 1)
                return count
            
            effect_count = count_effects(event_id, 0) - 1  # Exclude self
            
            if effect_count > 0:
                event = self.events[event_id]
                severity = self._calculate_severity(event)
                
                event_impact_scores.append({
                    'event': event.to_dict(),
                    'downstream_effects': effect_count,
                    'severity': severity,
                    'impact_score': round(effect_count * (1 + severity), 2)
                })
        
        # Sort by impact score
        event_impact_scores.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return event_impact_scores[:limit]
    
    def get_timeline(self, 
                    start_time: float = None, 
                    end_time: float = None,
                    components: List[str] = None,
                    include_causation_links: bool = True) -> Dict[str, Any]:
        """
        📅 TIMELINE VIEW
        
        Get events and their causation links over a time period.
        Optimized for visualization.
        """
        # Filter events
        filtered_events = []
        for event_id, event in self.events.items():
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if components and event.component not in components:
                continue
            
            filtered_events.append({
                'id': event_id,
                'timestamp': event.timestamp,
                'component': event.component,
                'event_type': event.event_type,
                'data_preview': {k: v for k, v in list(event.data.items())[:5]},
                'severity': self._calculate_severity(event)
            })
        
        # Sort by timestamp
        filtered_events.sort(key=lambda x: x['timestamp'])
        
        # Get causation links between these events
        links = []
        if include_causation_links:
            event_ids = {e['id'] for e in filtered_events}
            for u, v, data in self.causation_graph.edges(data=True):
                if u in event_ids and v in event_ids:
                    links.append({
                        'from': u,
                        'to': v,
                        'type': data.get('causation_type', 'unknown'),
                        'strength': data.get('strength', 0.5),
                        'explanation': data.get('explanation', '')
                    })
        
        return {
            'events': filtered_events,
            'links': links,
            'time_range': {
                'start': filtered_events[0]['timestamp'] if filtered_events else None,
                'end': filtered_events[-1]['timestamp'] if filtered_events else None
            },
            'total_events': len(filtered_events),
            'total_links': len(links)
        }


# Example usage
if __name__ == "__main__":
    explorer = CausationExplorer()
    
    # Example: Explore what caused network collapse
    collapse_events = explorer.search_events("collapse")
    if collapse_events:
        event_id = collapse_events[0]['event_id']
        print(f"\n🔬 Exploring what caused: {collapse_events[0]}")
        backwards = explorer.explore_backwards(event_id)
        print(f"\n📊 Causation trail (backwards):")
        for item in backwards[:5]:
            print(f"  Depth {item['depth']}: {item['event']}")
        
        forwards = explorer.explore_forwards(event_id)
        print(f"\n📊 Effects (forwards):")
        for item in forwards[:5]:
            print(f"  Depth {item['depth']}: {item['event']}")

