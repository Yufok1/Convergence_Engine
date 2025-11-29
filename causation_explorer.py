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


@dataclass
class Event:
    """A system event with causation context"""
    timestamp: float
    component: str
    event_type: str  # 'state_change', 'threshold_crossed', 'transition', etc.
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{int(time.time() * 1000000)}")
    
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
        self.direct_causation_time_window = causation_config.get('direct_causation_time_window', 1.0)  # seconds
        self.phase_transition_time_window = causation_config.get('phase_transition_time_window', 2.0)  # seconds
        self.recent_events_window = causation_config.get('recent_events_window', 100)  # number of events
        self.correlation_threshold = causation_config.get('correlation_threshold', 0.7)  # 0.0-1.0
        self.enable_neural_causations = causation_config.get('enable_neural_causations', True)  # Master toggle
        self.enable_neural_decision_causations = causation_config.get('enable_neural_decision_causations', True)
        self.enable_neural_training_causations = causation_config.get('enable_neural_training_causations', True)
        self.enable_ml_causations = causation_config.get('enable_ml_causations', True)  # ML Analysis causation toggle
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
            
        except Exception as e:
            logger.warning(f"[CausationExplorer] Could not load from shared state: {e}")
            # Don't raise - just log and return (prevents hanging)
    
    def _parse_log_line(self, line: str, component: str):
        """Parse a log line and extract events"""
        try:
            # Format: timestamp|level|component|metric:value|metric:value|...
            parts = line.strip().split('|')
            if len(parts) < 4:
                return
            
            timestamp_str = parts[0]
            level = parts[1]
            log_component = parts[2]
            metrics_str = '|'.join(parts[3:])
            
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
            
            # Create event
            event = Event(
                timestamp=timestamp,
                component=log_component or component,
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
            self.events[event.event_id] = event
            self.events_by_component[event.component].append(event.event_id)
            self.events_by_type[event.event_type].append(event.event_id)
            
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
            
            return CausationLink(
                from_event=prev_event.event_id,
                to_event=new_event.event_id,
                causation_type='direct',
                strength=0.8,
                explanation=direct_causations[key],
                metrics_involved=list(set(prev_event.data.keys()) | set(new_event.data.keys()))
            )
        
        return None
    
    def _add_causation_link(self, link: CausationLink):
        """Add a causation link to the graph"""
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
        if event_id not in self.events:
            return {}
        
        event = self.events[event_id]
        
        # Get causation info
        predecessors = list(self.causation_graph.predecessors(event_id))
        successors = list(self.causation_graph.successors(event_id))
        
        return {
            'event': event.to_dict(),
            'caused_by': len(predecessors),
            'caused': len(successors),
            'predecessor_events': [self.events[p].to_dict() for p in predecessors[:5]],
            'successor_events': [self.events[s].to_dict() for s in successors[:5]],
            'causation_links': [
                {
                    'from': self.causation_graph.nodes[p]['event'] if 'event' in self.causation_graph.nodes[p] else {},
                    'to': event.to_dict(),
                    'type': self.causation_graph[p][event_id].get('causation_type', 'unknown'),
                    'strength': self.causation_graph[p][event_id].get('strength', 0.0),
                    'explanation': self.causation_graph[p][event_id].get('explanation', '')
                }
                for p in predecessors[:5]
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

