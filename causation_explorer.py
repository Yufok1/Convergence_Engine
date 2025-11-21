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
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import networkx as nx
from datetime import datetime


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
    
    def __init__(self, state_logger=None, log_dir: Path = None, utm_kernel=None):
        self.logger = state_logger
        self.log_dir = log_dir or (Path(__file__).parent / 'data' / 'logs')
        self.utm_kernel = utm_kernel  # UTM Kernel for Akashic Ledger access
        
        # Causation graph (NetworkX directed graph)
        self.causation_graph = nx.DiGraph()
        
        # Event storage
        self.events: Dict[str, Event] = {}
        self.events_by_component: Dict[str, List[str]] = defaultdict(list)
        self.events_by_type: Dict[str, List[str]] = defaultdict(list)
        
        # Metric tracking (for correlation detection)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Threshold definitions
        self.thresholds = {
            'modularity': {'collapse': 0.3, 'direction': 'below'},
            'organism_count': {'collapse': 500, 'direction': 'above'},
            'clustering_coefficient': {'collapse': 0.5, 'direction': 'above'},
            'violation_pressure': {'vp0': 0.25, 'vp1': 0.50, 'vp2': 0.75, 'vp3': 0.99},
            'vp_calculations': {'transition': 50, 'direction': 'above'},
        }
        
        # Load existing state history if available
        self._load_state_history()
    
    def _load_state_history(self):
        """Load state history from log files AND Akashic Ledger"""
        # First, try to load from Akashic Ledger (tape-based)
        if hasattr(self, 'utm_kernel') and self.utm_kernel:
            try:
                self._load_from_akashic_ledger()
            except Exception as e:
                print(f"[CausationExplorer] Warning: Could not load from Akashic Ledger: {e}")
        
        # Also load from log files (fallback/complementary)
        if not self.log_dir.exists():
            return
        
        # Load from all log files
        for log_file in self.log_dir.glob('*.log'):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
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
    
    def add_event(self, event: Event):
        """Add an event and detect causations"""
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
        
        # Detect causations with recent events
        self._detect_causations(event)
    
    def _detect_causations(self, new_event: Event):
        """Detect causation relationships for a new event"""
        # Look at recent events (last 100)
        recent_events = sorted(
            self.events.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )[:100]
        
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
                
                # Check if threshold was crossed
                crossed = False
                if direction == 'above':
                    crossed = prev_value < threshold_value <= new_value
                elif direction == 'below':
                    crossed = prev_value > threshold_value >= new_value
                
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
                if change_pct > 0.1:  # 10% change
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
            ('breath', 'reality_sim'): 'Breath cycle drives network update',
            ('breath', 'djinn_kernel'): 'Breath cycle drives VP calculation',
            ('reality_sim', 'djinn_kernel'): 'Network metrics feed into VP calculation',
            ('explorer', 'reality_sim'): 'Explorer phase affects network behavior',
        }
        
        key = (prev_event.component, new_event.component)
        if key in direct_causations and time_diff < 1.0:  # Within 1 second
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

