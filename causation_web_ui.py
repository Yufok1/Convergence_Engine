"""
🌐 Causation Explorer Web UI

Simple web interface for interactive causation exploration
Uses Flask + D3.js for interactive graph visualization
"""

from flask import Flask, render_template, jsonify, request, abort
from causation_explorer import CausationExplorer
import json
from pathlib import Path
import logging
import traceback
import time
import requests
from typing import Dict, List, Optional, Any
from collections import defaultdict
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure Flask knows where templates are
template_dir = Path(__file__).parent / 'templates'
app = Flask(__name__, template_folder=str(template_dir))

# Initialize Causation Explorer with error handling
try:
    explorer = CausationExplorer()
    logger.info("Causation Explorer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Causation Explorer: {e}", exc_info=True)
    explorer = None


# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - BACKEND CLASSES
# ============================================================================

class OllamaBridge:
    """HTTP client for Ollama API at localhost:11434"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            models = data.get('models', [])
            # Ensure we return a list of model dicts with 'name' key
            result = []
            for model in models:
                if isinstance(model, dict):
                    if 'name' in model:
                        result.append(model)
                    elif 'model' in model:
                        result.append({'name': model['model'], **model})
                elif isinstance(model, str):
                    result.append({'name': model, 'model': model})
            return result
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}", exc_info=True)
            return []
    
    def chat(self, model: str, messages: List[Dict[str, str]], context: Dict[str, Any] = None) -> Optional[str]:
        """Send chat message with context to Ollama"""
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Combine system prompt with messages
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            payload = {
                "model": model,
                "messages": full_messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get('message', {}).get('content', '')
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}", exc_info=True)
            return None
    
    def vision(self, model: str, image_base64: str, prompt: str) -> Optional[str]:
        """Send image and prompt to vision model"""
        try:
            # Remove data URL prefix if present
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
            
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout * 2  # Vision takes longer
            )
            response.raise_for_status()
            data = response.json()
            return data.get('response', '')
        except Exception as e:
            logger.error(f"Error in Ollama vision: {e}", exc_info=True)
            return None
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt from context"""
        if not context:
            return ""
        
        parts = []
        
        if context.get('system_knowledge'):
            parts.append(f"# System Knowledge\n{context['system_knowledge']}\n")
        
        if context.get('current_state'):
            parts.append(f"# Current System State\n{context['current_state']}\n")
        
        if context.get('recent_logs'):
            parts.append(f"# Recent Log Activity\n{context['recent_logs']}\n")
        
        if context.get('graph_context'):
            parts.append(f"# Graph Context\n{context['graph_context']}\n")
        
        if context.get('view_state'):
            parts.append(f"# Current View State\n{context['view_state']}\n")
        
        if context.get('visual_description'):
            parts.append(f"# Visual Description\n{context['visual_description']}\n")
        
        prompt = "\n".join(parts)
        prompt += "\n\nYou are the Convergence Research Assistant (CRA) for the Butterfly System. "
        prompt += "Your purpose is to help discover, understand, and explain the system. "
        prompt += "Provide clear, informative, discovery-oriented responses based on the context above."
        
        return prompt


class LogParser:
    """Parse log files in pipe-delimited format"""
    
    LOG_FILES = [
        'state.log',
        'breath.log',
        'reality_sim.log',
        'explorer.log',
        'djinn_kernel.log',
        'system.log',
        'application.log'
    ]
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
    
    def parse_log_file(self, filename: str, max_lines: int = 500) -> List[Dict[str, Any]]:
        """Parse a single log file and return recent entries"""
        log_path = self.log_dir / filename
        if not log_path.exists():
            return []
        
        try:
            entries = []
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last N lines
                recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parsed = self._parse_log_line(line, filename)
                    if parsed:
                        entries.append(parsed)
            
            return entries
        except Exception as e:
            logger.error(f"Error parsing log file {filename}: {e}", exc_info=True)
            return []
    
    def _parse_log_line(self, line: str, source: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line: timestamp|level|component|metric:value|..."""
        try:
            parts = line.split('|')
            if len(parts) < 3:
                return None
            
            timestamp_str = parts[0]
            level = parts[1]
            component = parts[2]
            
            # Parse metrics
            metrics = {}
            for part in parts[3:]:
                if ':' in part:
                    key, value = part.split(':', 1)
                    # Try to parse value as number
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            return {
                'timestamp': timestamp_str,
                'level': level,
                'component': component,
                'source': source,
                'metrics': metrics,
                'raw': line
            }
        except Exception as e:
            logger.debug(f"Error parsing log line: {line[:50]}... - {e}")
            return None
    
    def parse_all_logs(self, max_lines_per_file: int = 500) -> Dict[str, List[Dict[str, Any]]]:
        """Parse all log files"""
        result = {}
        for log_file in self.LOG_FILES:
            entries = self.parse_log_file(log_file, max_lines_per_file)
            result[log_file] = entries
        return result
    
    def summarize_logs(self, log_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Summarize log data into text for context"""
        parts = []
        for log_file, entries in log_data.items():
            if not entries:
                continue
            
            parts.append(f"\n## {log_file}")
            parts.append(f"Recent entries: {len(entries)}")
            
            # Extract key metrics from recent entries
            if entries:
                latest = entries[-1]
                parts.append(f"Latest: {latest.get('timestamp', '')} - {latest.get('component', '')}")
                if latest.get('metrics'):
                    metrics_str = ", ".join([f"{k}: {v}" for k, v in list(latest['metrics'].items())[:5]])
                    parts.append(f"Metrics: {metrics_str}")
            
            # Show trends if available
            if len(entries) >= 2:
                first = entries[0]
                last = entries[-1]
                parts.append(f"First entry: {first.get('timestamp', '')}")
                parts.append(f"Last entry: {last.get('timestamp', '')}")
        
        return "\n".join(parts)


class SystemContextBuilder:
    """Build comprehensive context for research assistant"""
    
    def __init__(self, log_dir: Path, shared_state_path: Path, explorer: Optional[CausationExplorer] = None):
        self.log_dir = log_dir
        self.shared_state_path = shared_state_path
        self.explorer = explorer
        self.log_parser = LogParser(log_dir)
    
    def build_context(self, view_state: Dict[str, Any] = None, selected_event: str = None) -> Dict[str, Any]:
        """Build complete context for research assistant"""
        context = {}
        
        # Load shared state
        context['current_state'] = self._load_shared_state()
        
        # Load all logs
        context['recent_logs'] = self._load_recent_logs()
        
        # Get graph context
        context['graph_context'] = self._get_graph_context(selected_event)
        
        # Add view state
        context['view_state'] = view_state or {}
        
        return context
    
    def _load_shared_state(self) -> str:
        """Load and summarize shared state file"""
        if not self.shared_state_path.exists():
            return "No shared state file found."
        
        try:
            # Force reload if modified <10s
            file_mtime = os.path.getmtime(self.shared_state_path)
            current_time = time.time()
            force_reload = (current_time - file_mtime) < 10
            
            with open(self.shared_state_path, 'r') as f:
                state = json.load(f)
            
            parts = []
            parts.append(f"Frame: {state.get('frame_count', 0)}")
            parts.append(f"FPS: {state.get('simulation_fps', 0.0)}")
            parts.append(f"Simulation Time: {state.get('simulation_time', 0)}")
            
            data = state.get('data', {})
            
            if 'quantum' in data:
                q = data['quantum']
                parts.append(f"\nQuantum: {q.get('states', 0)} states")
            
            if 'lattice' in data:
                l = data['lattice']
                parts.append(f"Lattice: {l.get('particles', 0)} particles, CPU: {l.get('cpu_usage', 0)}%, RAM: {l.get('ram_usage', 0)}MB")
            
            if 'evolution' in data:
                e = data['evolution']
                parts.append(f"Evolution: Gen {e.get('generation', 0)}, Population: {e.get('population_size', 0)}, Best Fitness: {e.get('best_fitness', 0)}")
            
            if 'network' in data:
                n = data['network']
                parts.append(f"Network: {n.get('organisms', 0)} organisms, {n.get('connections', 0)} connections, Modularity: {n.get('modularity', 0)}, Clustering: {n.get('clustering_coefficient', 0)}")
            
            if 'explorer' in data:
                ex = data['explorer']
                parts.append(f"Explorer: Phase {ex.get('phase', 'unknown')}, VP Calculations: {ex.get('vp_calculations', 0)}, Breath Cycle: {ex.get('breath_cycle', 0)}")
            
            if 'djinn_kernel' in data:
                dk = data['djinn_kernel']
                parts.append(f"Djinn Kernel: VP {dk.get('violation_pressure', 0)}, Classification: {dk.get('vp_classification', 'unknown')}, Tape Cells: {dk.get('tape_cells', 0)}")
            
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Error loading shared state: {e}", exc_info=True)
            return f"Error loading shared state: {e}"
    
    def _load_recent_logs(self) -> str:
        """Load and summarize recent log entries"""
        log_data = self.log_parser.parse_all_logs(max_lines_per_file=200)
        return self.log_parser.summarize_logs(log_data)
    
    def _get_graph_context(self, selected_event: str = None) -> str:
        """Get causation graph context"""
        if not self.explorer:
            return "Causation Explorer not available."
        
        try:
            parts = []
            parts.append(f"Total Events: {len(self.explorer.events)}")
            parts.append(f"Total Causation Links: {self.explorer.causation_graph.number_of_edges()}")
            
            # Get selected event details
            if selected_event and selected_event in self.explorer.events:
                event = self.explorer.events[selected_event]
                parts.append(f"\nSelected Event: {selected_event}")
                parts.append(f"  Component: {event.component}")
                parts.append(f"  Type: {event.event_type}")
                parts.append(f"  Timestamp: {event.timestamp}")
            
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Error getting graph context: {e}", exc_info=True)
            return f"Error getting graph context: {e}"


class SystemKnowledgeBase:
    """Load and provide system knowledge from documentation"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._knowledge = None
    
    def load_knowledge(self) -> str:
        """Load system knowledge from documentation"""
        if self._knowledge:
            return self._knowledge
        
        parts = []
        
        # Load ARCHITECTURE.md if available
        arch_path = self.project_root / 'ARCHITECTURE.md'
        if arch_path.exists():
            try:
                with open(arch_path, 'r', encoding='utf-8') as f:
                    arch_content = f.read()
                    # Take first 3000 chars (summary)
                    parts.append(f"# System Architecture\n{arch_content[:3000]}...\n")
            except Exception as e:
                logger.warning(f"Could not load ARCHITECTURE.md: {e}")
        
        # Load README.md if available
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    # Take first 3000 chars (summary)
                    parts.append(f"# System Overview\n{readme_content[:3000]}...\n")
            except Exception as e:
                logger.warning(f"Could not load README.md: {e}")
        
        # Add system component descriptions
        parts.append(self._get_component_descriptions())
        
        self._knowledge = "\n".join(parts)
        return self._knowledge
    
    def _get_component_descriptions(self) -> str:
        """Get descriptions of system components"""
        return """
# Butterfly System Components

## Reality Simulator (Left Wing)
- Simulates quantum field, particle lattice, evolution, and network dynamics
- Network: Organisms (nodes) with connections (edges)
- Evolution: Generational selection and fitness
- Quantum: State field representation
- Lattice: Particle positions and interactions

## Explorer (Central Body / Breath Engine)
- Primary driver for all three systems
- Breath-driven execution cycles
- Causation graph exploration
- Phase tracking (Genesis/Sovereign)
- VP (Violation Pressure) calculations

## Djinn Kernel (Right Wing)
- UTM (Universal Turing Machine) kernel
- Akashic Ledger (immutable tape-based history)
- VP classification and calculations
- Trait convergence tracking
- Tape cell management

## Settings and Parameters
- Modularity: Network clustering metric (0.0-1.0)
- Clustering Coefficient: Node connectivity (0.0-1.0)
- Violation Pressure: System state indicator (0.0-1.0)
- VP Classifications: VP0 (<0.25), VP1 (0.25-0.50), VP2 (0.50-0.75), VP3 (0.75-0.99), VP4 (>=0.99)
- Breath Cycle: Explorer execution cycle
- Breath Depth: Depth of exploration phase
"""


# Initialize Ollama Bridge and Context Builder
project_root = Path(__file__).parent
log_dir = project_root / 'data' / 'logs'
shared_state_path = project_root / 'data' / '.shared_simulation_state.json'
ollama_bridge = OllamaBridge()
context_builder = SystemContextBuilder(log_dir, shared_state_path, explorer)
knowledge_base = SystemKnowledgeBase(project_root)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'explorer_initialized': explorer is not None,
        'template_path': str(Path(__file__).parent / 'templates' / 'causation_explorer.html'),
        'template_exists': (Path(__file__).parent / 'templates' / 'causation_explorer.html').exists()
    })


@app.route('/favicon.ico')
def favicon():
    """Serve favicon (blank to prevent 404)"""
    return '', 204  # No content


@app.route('/')
def index():
    """Main interface"""
    try:
        # Verify template exists
        template_path = Path(__file__).parent / 'templates' / 'causation_explorer.html'
        if not template_path.exists():
            error_msg = f"Error: Template not found at {template_path}. Please ensure templates/causation_explorer.html exists."
            logger.error(error_msg)
            return f"<html><body><h1>{error_msg}</h1></body></html>", 500
        
        logger.info(f"Rendering template from: {template_path}")
        return render_template('causation_explorer.html')
    except Exception as e:
        error_msg = f"Error rendering template: {e}"
        logger.error(error_msg, exc_info=True)
        return f"<html><body><h1>{error_msg}</h1><pre>{traceback.format_exc()}</pre></body></html>", 500


@app.route('/api/events/search')
def search_events():
    """Search events"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        query = request.args.get('q', '')
        results = explorer.search_events(query)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching events: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>')
def get_event(event_id):
    """Get event details"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        summary = explorer.get_event_summary(event_id)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>/backwards')
def explore_backwards(event_id):
    """Explore what caused this event"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        max_depth = int(request.args.get('depth', 10))
        trail = explorer.explore_backwards(event_id, max_depth)
        return jsonify(trail)
    except Exception as e:
        logger.error(f"Error exploring backwards for {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/events/<event_id>/forwards')
def explore_forwards(event_id):
    """Explore what this event caused"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized'}), 500
    try:
        max_depth = int(request.args.get('depth', 10))
        trail = explorer.explore_forwards(event_id, max_depth)
        return jsonify(trail)
    except Exception as e:
        logger.error(f"Error exploring forwards for {event_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/path/<from_id>/<to_id>')
def find_path(from_id, to_id):
    """Find path between two events"""
    if explorer is None:
        return jsonify({'path': None, 'events': [], 'error': 'Causation Explorer not initialized'}), 200
    try:
        path = explorer.find_path(from_id, to_id)
        if path:
            events = [explorer.events[eid].to_dict() for eid in path]
            return jsonify({'path': path, 'events': events})
        return jsonify({'path': None, 'events': []})
    except Exception as e:
        logger.error(f"Error finding path from {from_id} to {to_id}: {e}", exc_info=True)
        return jsonify({'path': None, 'events': [], 'error': str(e)}), 200


@app.route('/api/stats')
def get_stats():
    """Get causation graph statistics"""
    if explorer is None:
        return jsonify({'error': 'Causation Explorer not initialized', 'total_events': 0, 'total_links': 0}), 200
    try:
        stats = explorer.get_causation_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({'error': str(e), 'total_events': 0, 'total_links': 0}), 200


@app.route('/api/live/status')
def get_live_status():
    """
    Check if system is in live mode (receiving events from unified_entry.py)
    
    ⚠️ CURRENT BEHAVIOR (NOT ACTUALLY LIVE):
    - Accesses: explorer.events{} (loaded from log files on startup)
    - Checks: If any events have recent timestamps (within 10 seconds)
    - Returns: {"live": true/false} based on timestamp check
    - Problem: Only checks already-loaded events, doesn't connect to running backend
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    💡 TO MAKE IT ACTUALLY LIVE:
    - Add event feeding from unified_entry.py (Phase 2)
    - Add shared state file loading
    - Poll for updates from running backend
    """
    # Check if CausationExplorer has recent events (within last 5 seconds)
    if explorer is None or not explorer.events:
        return jsonify({'live': False, 'last_event_time': None, 'event_count': 0})
    
    try:
        # DATA ACCESS: Get most recent event timestamp from explorer.events{}
        # This is loaded from log files on startup, NOT from running backend
        recent_events = sorted(explorer.events.values(), key=lambda e: e.timestamp, reverse=True)
        if recent_events:
            last_event_time = recent_events[0].timestamp
            current_time = time.time()
            # Consider live if last event was within last 10 seconds
            # ⚠️ This just checks timestamps of already-loaded events, not actual backend connection
            is_live = (current_time - last_event_time) < 10
            return jsonify({
                'live': is_live,
                'last_event_time': last_event_time,
                'event_count': len(explorer.events),  # Total events loaded from logs/Akashic
                'events_since_start': len(recent_events)
            })
        return jsonify({'live': False, 'last_event_time': None, 'event_count': 0})
    except Exception as e:
        logger.error(f"Error checking live status: {e}", exc_info=True)
        return jsonify({'live': False, 'error': str(e)})


@app.route('/api/live/events')
def get_new_events():
    """
    Get events since a given timestamp (for live updates)
    
    ⚠️ CURRENT BEHAVIOR (NOT ACTUALLY LIVE):
    - Accesses: explorer.events{} (loaded from log files on startup)
    - Filters: Events where event.timestamp > since_timestamp
    - Returns: Filtered subset of already-loaded events
    - Problem: Only returns events that were loaded on startup, not new events from backend
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    💡 TO MAKE IT ACTUALLY LIVE:
    - Add event feeding from unified_entry.py (Phase 2)
    - Add shared state file polling
    - Stream new events from running backend
    """
    if explorer is None:
        return jsonify({'events': [], 'event_count': 0})
    
    try:
        since_timestamp = float(request.args.get('since', 0))
        # DATA ACCESS: Filter explorer.events{} for events after timestamp
        # ⚠️ This only filters already-loaded events from log files, not new events from backend
        new_events = [
            e.to_dict() for e in explorer.events.values()
            if e.timestamp > since_timestamp
        ]
        # Sort by timestamp
        new_events.sort(key=lambda e: e['timestamp'])
        
        return jsonify({
            'events': new_events,
            'event_count': len(new_events),
            'latest_timestamp': max([e['timestamp'] for e in new_events]) if new_events else since_timestamp
        })
    except Exception as e:
        logger.error(f"Error getting new events: {e}", exc_info=True)
        return jsonify({'events': [], 'error': str(e)})


@app.route('/api/graph')
def get_graph():
    """
    Get full causation graph for visualization
    
    🔍 DATA SOURCES ACCESSED:
    - explorer.events{} - Dictionary of all events loaded from:
      1. Akashic Ledger (if available) - data/kernel/akashic_ledger/
      2. Log files (fallback) - data/logs/*.log
      ❌ NOT: Shared state file (data/.shared_simulation_state.json)
      ❌ NOT: Real-time events from unified_entry.py
    
    - explorer.causation_graph - NetworkX DiGraph containing:
      - Nodes: Event IDs (from explorer.events{})
      - Edges: Causation links (threshold, correlation, direct, temporal)
      - Created when events are added via add_event()
      - Causations detected automatically when events are loaded
    
    📊 WHAT GETS VISUALIZED:
    - Nodes: All events from explorer.events{}
      - id, component, type, data, timestamp
    - Links: All causation links from explorer.causation_graph
      - source, target, type, strength, explanation
    
    ✅ Phase 2: REAL-TIME UPDATES (IMPLEMENTED):
    - Loads latest state from shared state file on each graph request (incremental)
    - Shows new events from running unified_entry.py in real-time
    - Thread-safe access to event graph (snapshots prevent iteration errors)
    """
    if explorer is None:
        return jsonify({'nodes': [], 'links': [], 'error': 'Causation Explorer not initialized'}), 200
    try:
        # Phase 2: Load latest state from shared state file (force reload on each request to get latest data)
        # This ensures that even if the simulation started before the web UI, we still load the latest data
        try:
            shared_state_path = Path('data/.shared_simulation_state.json')
            if shared_state_path.exists():
                # Check file modification time to see if it's been updated recently
                import os
                file_mtime = os.path.getmtime(shared_state_path)
                current_time = time.time()
                
                # If file was modified in the last 10 seconds, definitely reload
                if (current_time - file_mtime) < 10:
                    logger.info(f"Shared state file recently updated ({current_time - file_mtime:.1f}s ago), loading...")
                    explorer._load_from_shared_state(force_reload=True)  # Force reload recent data
                else:
                    # File exists but might be old, still try incremental load
                    explorer._load_from_shared_state(force_reload=False)
            else:
                logger.debug("Shared state file does not exist yet")
        except Exception as e:
            logger.warning(f"Could not load from shared state: {e}", exc_info=True)
        
        nodes = []
        links = []
        
        # DATA ACCESS: Read all events from explorer.events{}
        # This includes:
        # - Log files loaded on startup
        # - Akashic Ledger loaded on startup
        # - Shared state file (just loaded above for live updates)
        # Add nodes (use lock for thread safety)
        with explorer.graph_lock:
            events_snapshot = dict(explorer.events)  # Create snapshot inside lock
            edges_snapshot = list(explorer.causation_graph.edges(data=True))  # Create snapshot inside lock
        
        # Process snapshots outside lock
        if events_snapshot:
            for event_id, event in events_snapshot.items():
                nodes.append({
                    'id': event_id,
                    'component': event.component,
                    'type': event.event_type,
                    'data': event.data,
                    'timestamp': event.timestamp
                })
        
        # DATA ACCESS: Read all causation links from explorer.causation_graph (snapshot)
        # This is a NetworkX DiGraph built when events are added
        # Causation links are detected automatically (threshold, correlation, direct, temporal)
        # Add links
        if edges_snapshot:
            for u, v, data in edges_snapshot:
                links.append({
                    'source': u,
                    'target': v,
                    'type': data.get('causation_type', 'unknown'),
                    'strength': data.get('strength', 0.0),
                    'explanation': data.get('explanation', '')
                })
        
        # Add diagnostic info if no data
        diagnostic_info = {}
        if len(nodes) == 0:
            shared_state_path = Path('data/.shared_simulation_state.json')
            diagnostic_info['no_data'] = True
            diagnostic_info['data_sources_checked'] = {
                'shared_state_exists': shared_state_path.exists(),
                'log_dir_exists': explorer.log_dir.exists() if explorer else False,
                'log_files_count': len(list(explorer.log_dir.glob('*.log'))) if explorer and explorer.log_dir.exists() else 0,
                'events_in_memory': len(explorer.events) if explorer else 0,
            }
            if shared_state_path.exists():
                import os
                file_mtime = os.path.getmtime(shared_state_path)
                file_age = time.time() - file_mtime
                diagnostic_info['data_sources_checked']['shared_state_age_seconds'] = file_age
            diagnostic_info['message'] = 'No events found. Make sure the simulation is running and generating data.'
            logger.warning(f"Graph request returned 0 nodes. Diagnostics: {diagnostic_info}")
        else:
            logger.info(f"Graph request returned {len(nodes)} nodes and {len(links)} links")
        
        return jsonify({
            'nodes': nodes,
            'links': links,
            'diagnostic': diagnostic_info if diagnostic_info else None
        })
    except Exception as e:
        logger.error(f"Error getting graph: {e}", exc_info=True)
        return jsonify({'nodes': [], 'links': [], 'error': str(e)}), 200


# ============================================================================
# CONVERGENCE RESEARCH ASSISTANT - FLASK ENDPOINTS
# ============================================================================

@app.route('/api/ollama/models')
def list_ollama_models():
    """List available Ollama models"""
    try:
        models_data = ollama_bridge.list_models()
        # models_data is a list of model objects from Ollama API
        # Each model has: {'name': 'model-name', 'modified_at': '...', 'size': ...}
        
        # Separate vision models from text models (heuristic)
        vision_models = []
        text_models = []
        all_models = []
        
        for model in models_data:
            # Handle both dict format and string format
            if isinstance(model, dict):
                model_name = model.get('name', '')
            else:
                model_name = str(model)
            
            if not model_name:
                continue
            
            # Normalize model name (remove tags like :latest, :7b, etc for comparison)
            name_lower = model_name.lower()
            
            # Common vision model patterns
            if any(keyword in name_lower for keyword in ['vision', 'llava', 'clip', 'minicpm-v', 'bakllava', 'moondream']):
                vision_models.append({'name': model_name, 'model': model_name})
            else:
                text_models.append({'name': model_name, 'model': model_name})
            
            all_models.append({'name': model_name, 'model': model_name})
        
        # If no vision models found but we have models, add all as potential vision models (fallback)
        if not vision_models and all_models:
            vision_models = all_models.copy()
        
        return jsonify({
            'models': all_models,
            'text_models': text_models,
            'vision_models': vision_models
        })
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}", exc_info=True)
        return jsonify({'error': str(e), 'models': [], 'text_models': [], 'vision_models': []}), 500


@app.route('/api/ollama/chat', methods=['POST'])
def ollama_chat():
    """Send message to research assistant with complete context"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        model = data.get('model', 'llama2')
        view_state = data.get('view_state', {})
        selected_event = data.get('selected_event')
        graph_image = data.get('graph_image')  # base64 image if provided
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Build context
        context = context_builder.build_context(view_state=view_state, selected_event=selected_event)
        
        # Add system knowledge
        context['system_knowledge'] = knowledge_base.load_knowledge()
        
        # If graph image provided, analyze it first with vision model
        visual_description = None
        if graph_image and data.get('vision_model'):
            vision_model = data.get('vision_model')
            vision_prompt = "Describe what you see in this causation graph visualization. Identify visible nodes, clusters, connections, and patterns."
            visual_description = ollama_bridge.vision(vision_model, graph_image, vision_prompt)
            if visual_description:
                context['visual_description'] = visual_description
        
        # Build messages for chat
        messages = [{"role": "user", "content": message}]
        
        # Send to research assistant
        response = ollama_bridge.chat(model, messages, context)
        
        if response is None:
            return jsonify({'error': 'Failed to get response from Ollama'}), 500
        
        return jsonify({
            'response': response,
            'visual_description': visual_description,
            'context_sources': {
                'shared_state': shared_state_path.exists(),
                'log_files': len(list(log_dir.glob('*.log'))) if log_dir.exists() else 0,
                'graph_events': len(explorer.events) if explorer else 0
            }
        })
    except Exception as e:
        logger.error(f"Error in Ollama chat: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/vision', methods=['POST'])
def ollama_vision():
    """Analyze graph view with vision model"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        model = data.get('model', 'llava')
        prompt = data.get('prompt', 'Describe what you see in this causation graph visualization.')
        
        if not image_base64:
            return jsonify({'error': 'Image is required'}), 400
        
        response = ollama_bridge.vision(model, image_base64, prompt)
        
        if response is None:
            return jsonify({'error': 'Failed to get response from vision model'}), 500
        
        return jsonify({'description': response})
    except Exception as e:
        logger.error(f"Error in Ollama vision: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/system/context')
def get_system_context():
    """Get current system context (for debugging)"""
    try:
        view_state = request.args.get('view_state')
        selected_event = request.args.get('selected_event')
        
        view_state_dict = json.loads(view_state) if view_state else {}
        context = context_builder.build_context(view_state=view_state_dict, selected_event=selected_event)
        context['system_knowledge'] = knowledge_base.load_knowledge()[:1000] + "..."  # Truncated for display
        
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error getting system context: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if needed
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print("🔬 Causation Explorer Web UI")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)

