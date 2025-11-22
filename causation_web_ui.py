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
from typing import Dict, List, Optional, Any, Tuple
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
    """HTTP client for Ollama API (supports both local and cloud)"""
    
    def __init__(self, base_url: str = None, timeout: float = None, api_key: str = None):
        # Support environment variables for configuration
        # OLLAMA_BASE_URL defaults to localhost, or use https://ollama.com for cloud
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT", "30.0"))
        # OLLAMA_API_KEY required for cloud API access
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        
        # Determine if we're using cloud (https://ollama.com)
        self.is_cloud = self.base_url.startswith("https://ollama.com")
        
        # Build headers (include auth for cloud)
        self.headers = {}
        if self.is_cloud and self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
            self.headers['Content-Type'] = 'application/json'  # Explicit content type for cloud
        
        if self.is_cloud:
            if self.api_key:
                logger.info(f"✅ OllamaBridge configured for cloud: {self.base_url}")
            else:
                logger.warning("⚠️ Ollama Cloud URL detected but OLLAMA_API_KEY not set. Cloud API calls will fail.")
                logger.info("   Set OLLAMA_API_KEY environment variable or get key from: https://ollama.com/settings/keys")
        else:
            logger.info(f"✅ OllamaBridge configured for local: {self.base_url}")
    
    def update_config(self, base_url: str = None, api_key: str = None, timeout: float = None):
        """Update configuration dynamically"""
        if base_url is not None:
            self.base_url = base_url
            self.is_cloud = self.base_url.startswith("https://ollama.com")
        
        if api_key is not None:
            self.api_key = api_key
        
        if timeout is not None:
            self.timeout = timeout
        
        # Rebuild headers
        self.headers = {}
        if self.is_cloud and self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        logger.info(f"OllamaBridge configuration updated: {self.base_url} (cloud: {self.is_cloud})")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                headers=self.headers,
                timeout=self.timeout
            )
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
            if self.is_cloud and not self.api_key:
                logger.warning("OLLAMA_API_KEY not set - required for cloud access")
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
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get('message', {}).get('content', '')
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}", exc_info=True)
            return None
    
    def vision(self, model: str, images: List[str], prompt: str) -> Optional[str]:
        """Send one or more images with prompt to vision model
        
        Args:
            model: Vision model name
            images: List of base64-encoded images (or single image as string for backwards compat)
            prompt: Minimal prompt for vision model
        """
        try:
            # Handle both single image (backwards compat) and list of images
            if isinstance(images, str):
                images = [images]
            
            # Clean images (remove data URL prefix if present)
            cleaned_images = []
            total_image_size = 0
            for img in images:
                if img.startswith('data:image'):
                    img = img.split(',')[1]
                cleaned_images.append(img)
                total_image_size += len(img.encode('utf-8'))
            
            # Check total payload size (all images + prompt + JSON overhead)
            prompt_bytes = len(prompt.encode('utf-8'))
            estimated_json_overhead = 1000  # Model name, structure, array overhead
            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
            
            # Log payload size for debugging
            logger.debug(f"Vision payload: {len(cleaned_images)} image(s)={total_image_size/1024:.1f}KB, Prompt={prompt_bytes/1024:.1f}KB, Total≈{total_payload_estimate/1024:.1f}KB")
            
            # Optimistic payload limits: allow larger batches for better analysis
            # Target: 200KB max total payload (allows multiple images + prompt)
            # More generous limits for comprehensive vision analysis
            max_total_payload = 200 * 1024  # 200KB - optimistic limit for batch processing
            if total_payload_estimate > max_total_payload:
                # Calculate how many images we can fit
                avg_image_size = total_image_size / len(cleaned_images) if cleaned_images else 0
                if avg_image_size > 0:
                    # Leave room for prompt + overhead (estimate ~1KB)
                    max_images = max(1, int((max_total_payload - prompt_bytes - estimated_json_overhead) / avg_image_size))
                    
                    if len(cleaned_images) > max_images:
                        # Keep most recent images (they're most informative for evolution)
                        original_count = len(cleaned_images)
                        cleaned_images = cleaned_images[-max_images:]
                        total_image_size = sum(len(img.encode('utf-8')) for img in cleaned_images)
                        total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                        logger.warning(f"Reduced images from {original_count} to {len(cleaned_images)} (avg {avg_image_size/1024:.1f}KB/image, total payload {total_payload_estimate/1024:.1f}KB)")
                
                # If still too large even with reduced images, truncate prompt
                if total_payload_estimate > max_total_payload:
                    max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead
                    if max_prompt_size > 50:  # Need at least 50 bytes for prompt
                        prompt = prompt[:max_prompt_size] + "...[truncated]"
                        logger.warning(f"Truncated prompt to {max_prompt_size} bytes")
                    else:
                        # Images alone are too large - try to reduce to just 1 (current state)
                        if len(cleaned_images) > 1:
                            logger.warning(f"Images too large ({total_image_size/1024:.1f}KB), keeping only most recent image")
                            cleaned_images = cleaned_images[-1:]
                            total_image_size = len(cleaned_images[0].encode('utf-8'))
                            total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                            
                            if total_payload_estimate > max_total_payload:
                                # Try aggressive prompt truncation first (leave 5KB headroom for safety)
                                max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead - 5000
                                if max_prompt_size > 50:
                                    prompt = prompt[:max_prompt_size] + "...[truncated]"
                                    prompt_bytes = len(prompt.encode('utf-8'))
                                    total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                    logger.warning(f"Aggressively truncated prompt to fit image ({max_prompt_size} bytes, new total: {total_payload_estimate/1024:.1f}KB)")
                                
                                # Only fail if still too large after aggressive truncation
                                if total_payload_estimate > max_total_payload:
                                    # If even single image is too large, skip vision analysis gracefully
                                    logger.warning(f"Image too large for Ollama Cloud ({total_image_size/1024:.1f}KB, max ~{max_total_payload/1024:.0f}KB). Skipping vision analysis.")
                                    if self.is_cloud:
                                        raise Exception(f"Image too large for Ollama Cloud preview ({total_image_size/1024:.1f}KB). Vision models may have limited support in cloud. Try reducing graph complexity or use local Ollama.")
                                    else:
                                        raise Exception(f"Image too large ({total_image_size/1024:.1f}KB) for vision API")
                        else:
                            # Single image but still too large - try aggressive prompt truncation
                            max_prompt_size = max_total_payload - total_image_size - estimated_json_overhead - 5000
                            if max_prompt_size > 50:
                                prompt = prompt[:max_prompt_size] + "...[truncated]"
                                prompt_bytes = len(prompt.encode('utf-8'))
                                total_payload_estimate = total_image_size + prompt_bytes + estimated_json_overhead
                                logger.warning(f"Aggressively truncated prompt to fit image ({max_prompt_size} bytes, new total: {total_payload_estimate/1024:.1f}KB)")
                            
                            # Only fail if still too large after truncation
                            if total_payload_estimate > max_total_payload:
                                if self.is_cloud:
                                    raise Exception(f"Image too large for Ollama Cloud preview ({total_image_size/1024:.1f}KB). Vision models may have limited support. Try reducing graph complexity or use local Ollama.")
                                else:
                                    raise Exception(f"Image too large ({total_image_size/1024:.1f}KB) for vision API")
            
            # Ollama Cloud and newer local versions use /api/chat for vision models
            # Use chat endpoint format for both local and cloud
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "images": cleaned_images  # Send all images
                }
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Use /api/chat endpoint (works for both local and cloud)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=self.headers,
                timeout=self.timeout * 2  # Vision takes longer
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract response from chat format
            if 'message' in data:
                return data['message'].get('content', '')
            elif 'response' in data:
                return data.get('response', '')
            else:
                logger.warning(f"Unexpected vision response format: {data}")
                return str(data)
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error in Ollama vision: {e}", exc_info=True)
            # Extract detailed error message from response
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if isinstance(error_data, dict) and 'error' in error_data:
                        error_message = f"Ollama API error: {error_data['error']}"
                    else:
                        error_detail = e.response.text[:500]
                        error_message = f"Ollama API error ({e.response.status_code}): {error_detail}"
                    logger.error(f"API response: {error_message}")
                except:
                    error_message = f"HTTP {e.response.status_code} error from Ollama Cloud"
            # Return error string instead of None for better error display
            raise Exception(error_message)
        except Exception as e:
            logger.error(f"Error in Ollama vision: {e}", exc_info=True)
            raise
    
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
        
        # Add time-series trends if available
        if context.get('time_series_trends'):
            parts.append(f"# Time-Series Trends (Recent Changes)")
            trends = context['time_series_trends']
            significant_trends = []
            for metric_name, trend_info in trends.items():
                if trend_info.get('trend') != 'insufficient_data':
                    trend = trend_info.get('trend', 'unknown')
                    change = trend_info.get('change_percent', 0)
                    current = trend_info.get('current_value', 0)
                    if abs(change) > 1.0:  # Only show significant changes
                        significant_trends.append((metric_name, trend, change, current))
            
            if significant_trends:
                for metric_name, trend, change, current in significant_trends[:10]:  # Top 10
                    parts.append(f"  {metric_name}: {trend} ({change:+.2f}%), current={current:.3f}")
            else:
                parts.append("  All metrics stable")
        
        # Add anomaly detection if available
        if context.get('anomalies'):
            parts.append(f"\n# Detected Anomalies (Statistical Spikes)")
            anomalies = context['anomalies']
            for metric_name, spikes in anomalies.items():
                if spikes:
                    latest = spikes[-1]
                    parts.append(f"  {metric_name}: Spike detected (value={latest['value']:.3f}, "
                               f"deviation={latest['deviation']:.2f}σ above average)")
        
        # Add predictive insights if available
        if context.get('predictive_insights'):
            parts.append(f"\n# Predictive Insights (Future Projections)")
            insights = context['predictive_insights']
            for metric_name, insight in insights.items():
                prediction = insight.get('prediction', 'No prediction available')
                predicted_value = insight.get('predicted_value')
                if predicted_value is not None:
                    parts.append(f"  {metric_name}: {prediction} (predicted: {predicted_value:.3f})")
                else:
                    parts.append(f"  {metric_name}: {prediction}")
        
        # Add alerts if available
        if context.get('alerts'):
            parts.append(f"\n# ⚠️ Active Alerts (Requires Attention)")
            alerts = context['alerts']
            for alert in alerts[:5]:  # Top 5 alerts
                severity = alert.get('severity', 'info')
                parts.append(f"  [{severity.upper()}] {alert.get('message', 'Unknown alert')}")
        
        prompt = "\n".join(parts)
        prompt += "\n\nYou are the Convergence Research Assistant (CRA) for the Butterfly System. "
        prompt += "Your purpose is to help discover, understand, and explain the system. "
        prompt += "Analyze the time-series trends to identify patterns, predict future behavior, and explain anomalies. "
        prompt += "Use the predictive insights to suggest what might happen next and what adjustments might be needed. "
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


class ChangeDetector:
    """Detect changes between graph snapshots"""
    
    def compare_snapshots(self, snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two snapshots and return detected changes"""
        changes = {
            'node_changes': {
                'added': [],
                'removed': [],
                'modified': []
            },
            'link_changes': {
                'added': [],
                'removed': []
            },
            'metric_changes': {}
        }
        
        nodes1 = {n['id']: n for n in snapshot1.get('nodes', [])}
        nodes2 = {n['id']: n for n in snapshot2.get('nodes', [])}
        
        # Detect node changes
        node_ids1 = set(nodes1.keys())
        node_ids2 = set(nodes2.keys())
        
        added_nodes = node_ids2 - node_ids1
        removed_nodes = node_ids1 - node_ids2
        
        for node_id in added_nodes:
            changes['node_changes']['added'].append({
                'id': node_id,
                'component': nodes2[node_id].get('component'),
                'type': nodes2[node_id].get('type')
            })
        
        for node_id in removed_nodes:
            changes['node_changes']['removed'].append({
                'id': node_id,
                'component': nodes1[node_id].get('component'),
                'type': nodes1[node_id].get('type')
            })
        
        # Detect link changes
        links1 = {(l.get('source', {}).get('id', l.get('source')), 
                   l.get('target', {}).get('id', l.get('target'))) 
                  for l in snapshot1.get('links', [])}
        links2 = {(l.get('source', {}).get('id', l.get('source')), 
                   l.get('target', {}).get('id', l.get('target'))) 
                  for l in snapshot2.get('links', [])}
        
        added_links = links2 - links1
        removed_links = links1 - links2
        
        for source, target in added_links:
            changes['link_changes']['added'].append({
                'source': source,
                'target': target
            })
        
        for source, target in removed_links:
            changes['link_changes']['removed'].append({
                'source': source,
                'target': target
            })
        
        # Detect metric changes
        metrics1 = snapshot1.get('metrics', {})
        metrics2 = snapshot2.get('metrics', {})
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            val1 = metrics1.get(metric, 0)
            val2 = metrics2.get(metric, 0)
            if val1 != val2:
                changes['metric_changes'][metric] = {
                    'before': val1,
                    'after': val2,
                    'change': val2 - val1,
                    'change_percent': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
        
        return changes


class ComparativeAnalyzer:
    """Compare different runs or sessions to identify differences"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.runs_dir = storage_dir / 'runs'
        self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def save_run_summary(self, run_id: str, summary: Dict[str, Any]):
        """Save a run summary for later comparison"""
        run_file = self.runs_dir / f"{run_id}.json"
        try:
            with open(run_file, 'w') as f:
                json.dump(summary, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Could not save run summary: {e}")
            return False
    
    def load_run_summaries(self, max_runs: int = 10) -> List[Dict[str, Any]]:
        """Load recent run summaries"""
        run_files = sorted(self.runs_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        runs = []
        
        for run_file in run_files[:max_runs]:
            try:
                with open(run_file, 'r') as f:
                    runs.append(json.load(f))
            except Exception as e:
                logger.debug(f"Could not load run {run_file}: {e}")
        
        return runs
    
    def compare_runs(self, run1: Dict[str, Any], run2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two runs and return differences"""
        comparison = {
            'metrics_differences': {},
            'graph_differences': {},
            'event_differences': {}
        }
        
        # Compare metrics
        metrics1 = run1.get('metrics', {})
        metrics2 = run2.get('metrics', {})
        
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        for metric in all_metrics:
            val1 = metrics1.get(metric, 0)
            val2 = metrics2.get(metric, 0)
            if val1 != val2:
                comparison['metrics_differences'][metric] = {
                    'run1_value': val1,
                    'run2_value': val2,
                    'difference': val2 - val1,
                    'percent_change': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
        
        # Compare graph stats
        graph1 = run1.get('graph_stats', {})
        graph2 = run2.get('graph_stats', {})
        
        comparison['graph_differences'] = {
            'nodes': {
                'run1': graph1.get('nodes', 0),
                'run2': graph2.get('nodes', 0),
                'difference': graph2.get('nodes', 0) - graph1.get('nodes', 0)
            },
            'links': {
                'run1': graph1.get('links', 0),
                'run2': graph2.get('links', 0),
                'difference': graph2.get('links', 0) - graph1.get('links', 0)
            }
        }
        
        # Compare event counts
        events1 = run1.get('event_count', 0)
        events2 = run2.get('event_count', 0)
        
        comparison['event_differences'] = {
            'run1_count': events1,
            'run2_count': events2,
            'difference': events2 - events1
        }
        
        return comparison
    
    def generate_comparison_report(self, run1_id: str, run2_id: str) -> str:
        """Generate a formatted comparison report"""
        runs = self.load_run_summaries(max_runs=20)
        run1 = next((r for r in runs if r.get('run_id') == run1_id), None)
        run2 = next((r for r in runs if r.get('run_id') == run2_id), None)
        
        if not run1 or not run2:
            return "Could not find one or both runs for comparison."
        
        comparison = self.compare_runs(run1, run2)
        
        parts = []
        parts.append(f"# Run Comparison Report")
        parts.append(f"Run 1: {run1_id} (from {run1.get('timestamp', 'unknown')})")
        parts.append(f"Run 2: {run2_id} (from {run2.get('timestamp', 'unknown')})")
        parts.append("\n## Metrics Differences")
        
        for metric, diff in comparison['metrics_differences'].items():
            parts.append(f"  {metric}: {diff['run1_value']:.3f} → {diff['run2_value']:.3f} "
                        f"({diff['percent_change']:+.2f}%)")
        
        parts.append("\n## Graph Differences")
        parts.append(f"  Nodes: {comparison['graph_differences']['nodes']['run1']} → "
                    f"{comparison['graph_differences']['nodes']['run2']} "
                    f"({comparison['graph_differences']['nodes']['difference']:+d})")
        parts.append(f"  Links: {comparison['graph_differences']['links']['run1']} → "
                    f"{comparison['graph_differences']['links']['run2']} "
                    f"({comparison['graph_differences']['links']['difference']:+d})")
        
        return "\n".join(parts)


class AlertSystem:
    """Monitor metrics and trigger alerts when thresholds are exceeded"""
    
    def __init__(self):
        self.thresholds = {
            'djinn_vp': {'min': 0.0, 'max': 0.99, 'alert_on_exceed': True},
            'explorer_vp': {'min': 0.0, 'max': 0.99, 'alert_on_exceed': True},
            'network_modularity': {'min': 0.0, 'max': 1.0, 'alert_on_exceed': False},
            'evolution_best_fitness': {'min': 0.0, 'max': float('inf'), 'alert_on_exceed': False},
            'event_frequency': {'min': 0, 'max': 10000, 'alert_on_exceed': True}
        }
        self.active_alerts = []
        self.alert_history = []
    
    def check_thresholds(self, metrics: Dict[str, float], time_series_tracker: 'TimeSeriesTracker') -> List[Dict[str, Any]]:
        """Check if any metrics exceed thresholds and return alerts"""
        alerts = []
        
        for metric_name, value in metrics.items():
            if metric_name not in self.thresholds:
                continue
            
            threshold = self.thresholds[metric_name]
            
            # Check min threshold
            if value < threshold['min']:
                alert = {
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold['min'],
                    'type': 'below_minimum',
                    'severity': 'warning',
                    'message': f"{metric_name} ({value:.3f}) below minimum threshold ({threshold['min']:.3f})",
                    'timestamp': time.time()
                }
                alerts.append(alert)
            
            # Check max threshold
            if threshold['alert_on_exceed'] and value > threshold['max']:
                alert = {
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold['max'],
                    'type': 'above_maximum',
                    'severity': 'critical' if value > threshold['max'] * 1.5 else 'warning',
                    'message': f"{metric_name} ({value:.3f}) exceeded maximum threshold ({threshold['max']:.3f})",
                    'timestamp': time.time()
                }
                alerts.append(alert)
        
        # Check for spikes using time-series tracker
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity']
        for metric in key_metrics:
            if metric in metrics:
                spikes = time_series_tracker.detect_spikes(metric, threshold_multiplier=3.0)  # Higher threshold for alerts
                if spikes:
                    latest_spike = spikes[-1]
                    alert = {
                        'metric': metric,
                        'value': latest_spike['value'],
                        'threshold': latest_spike['threshold'],
                        'type': 'spike_detected',
                        'severity': 'critical',
                        'message': f"{metric} spike detected: {latest_spike['value']:.3f} ({latest_spike['deviation']:.2f}σ above average)",
                        'timestamp': latest_spike['timestamp']
                    }
                    alerts.append(alert)
        
        # Update alert history
        self.alert_history.extend(alerts)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        self.active_alerts = alerts
        return alerts


class PersistentContext:
    """Save and load chat history and snapshots across sessions"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.chat_history_file = storage_dir / 'chat_history.json'
        self.snapshots_dir = storage_dir / 'snapshots'
        self.snapshots_dir.mkdir(exist_ok=True)
    
    def save_chat_message(self, role: str, message: str, timestamp: float = None):
        """Save a chat message to history"""
        if timestamp is None:
            timestamp = time.time()
        
        # Load existing history
        history = self.load_chat_history()
        
        # Add new message
        history.append({
            'timestamp': timestamp,
            'role': role,
            'message': message
        })
        
        # Save back
        try:
            with open(self.chat_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save chat history: {e}")
    
    def load_chat_history(self) -> List[Dict[str, Any]]:
        """Load chat history from disk"""
        if not self.chat_history_file.exists():
            return []
        
        try:
            with open(self.chat_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load chat history: {e}")
            return []
    
    def save_snapshot(self, snapshot_data: Dict[str, Any], snapshot_id: str = None):
        """Save a graph snapshot"""
        if snapshot_id is None:
            snapshot_id = f"snapshot_{int(time.time())}"
        
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        try:
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
            return snapshot_id
        except Exception as e:
            logger.warning(f"Could not save snapshot: {e}")
            return None
    
    def load_snapshots(self, max_snapshots: int = 10) -> List[Dict[str, Any]]:
        """Load recent snapshots"""
        snapshot_files = sorted(self.snapshots_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        snapshots = []
        
        for snapshot_file in snapshot_files[:max_snapshots]:
            try:
                with open(snapshot_file, 'r') as f:
                    snapshots.append(json.load(f))
            except Exception as e:
                logger.debug(f"Could not load snapshot {snapshot_file}: {e}")
        
        return snapshots


class PredictiveAnalyzer:
    """Generate predictive insights based on time-series trends"""
    
    def __init__(self, time_series_tracker: 'TimeSeriesTracker'):
        self.tracker = time_series_tracker
    
    def predict_future_value(self, metric_name: str, steps_ahead: int = 10) -> Optional[float]:
        """Predict future value based on linear trend"""
        trend = self.tracker.get_trend(metric_name, window_size=20)
        if trend.get('trend') == 'insufficient_data':
            return None
        
        history = self.tracker.metrics_history.get(metric_name, [])
        if len(history) < 2:
            return None
        
        # Simple linear extrapolation using change percentage
        current_value = trend.get('current_value', 0)
        change_percent = trend.get('change_percent', 0)
        
        # Calculate predicted value based on percentage change
        # Assume change_percent is per window, so scale by steps_ahead
        if change_percent != 0:
            predicted_value = current_value * (1 + (change_percent / 100) * (steps_ahead / 10))
            return predicted_value
        else:
            # If no change, return current value
            return current_value
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate predictive insights for key metrics"""
        insights = {}
        
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity', 'evolution_best_fitness']
        
        for metric in key_metrics:
            trend = self.tracker.get_trend(metric, window_size=20)
            if trend.get('trend') == 'insufficient_data':
                continue
            
            prediction = self.predict_future_value(metric, steps_ahead=10)
            
            insight = {
                'current_trend': trend.get('trend'),
                'change_percent': trend.get('change_percent', 0),
                'current_value': trend.get('current_value'),
                'predicted_value': prediction,
                'confidence': 'low'  # Simple model, low confidence
            }
            
            # Add qualitative prediction
            if trend.get('trend') == 'increasing':
                if trend.get('change_percent', 0) > 5:
                    insight['prediction'] = f"{metric} is rapidly increasing - expect continued growth"
                else:
                    insight['prediction'] = f"{metric} is gradually increasing - slow positive trend"
            elif trend.get('trend') == 'decreasing':
                if trend.get('change_percent', 0) < -5:
                    insight['prediction'] = f"{metric} is rapidly decreasing - monitor closely"
                else:
                    insight['prediction'] = f"{metric} is gradually decreasing - slow negative trend"
            else:
                insight['prediction'] = f"{metric} is stable - no significant change expected"
            
            insights[metric] = insight
        
        return insights


class TimeSeriesTracker:
    """Track metrics over time for trend analysis and anomaly detection"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = defaultdict(list)  # metric_name -> [(timestamp, value), ...]
        self.last_update_time = None
    
    def record_metric(self, metric_name: str, value: float, timestamp: float = None):
        """Record a metric value at a given timestamp"""
        if timestamp is None:
            timestamp = time.time()
        
        history = self.metrics_history[metric_name]
        history.append((timestamp, value))
        
        # Keep only last max_history entries
        if len(history) > self.max_history:
            history.pop(0)
    
    def extract_metrics_from_state(self, state: Dict[str, Any], timestamp: float = None):
        """Extract all metrics from shared state and record them"""
        if timestamp is None:
            timestamp = time.time()
        
        data = state.get('data', {})
        
        # Frame-level metrics
        self.record_metric('frame_count', state.get('frame_count', 0), timestamp)
        self.record_metric('simulation_fps', state.get('simulation_fps', 0.0), timestamp)
        self.record_metric('simulation_time', state.get('simulation_time', 0.0), timestamp)
        
        # Quantum metrics
        if 'quantum' in data:
            q = data['quantum']
            self.record_metric('quantum_states', q.get('states', 0), timestamp)
            self.record_metric('quantum_energy', q.get('energy', 0.0), timestamp)
            self.record_metric('quantum_entropy', q.get('entropy', 0.0), timestamp)
        
        # Lattice metrics
        if 'lattice' in data:
            l = data['lattice']
            self.record_metric('lattice_particles', l.get('particles', 0), timestamp)
            self.record_metric('lattice_cpu_usage', l.get('cpu_usage', 0.0), timestamp)
            self.record_metric('lattice_temperature', l.get('temperature', 0.0), timestamp)
        
        # Evolution metrics
        if 'evolution' in data:
            e = data['evolution']
            self.record_metric('evolution_generation', e.get('generation', 0), timestamp)
            self.record_metric('evolution_population', e.get('population_size', 0), timestamp)
            self.record_metric('evolution_best_fitness', e.get('best_fitness', 0.0), timestamp)
            self.record_metric('evolution_avg_fitness', e.get('avg_fitness', 0.0), timestamp)
        
        # Network metrics
        if 'network' in data:
            n = data['network']
            self.record_metric('network_organisms', n.get('organisms', 0), timestamp)
            self.record_metric('network_connections', n.get('connections', 0), timestamp)
            self.record_metric('network_modularity', n.get('modularity', 0.0), timestamp)
            self.record_metric('network_clustering', n.get('clustering_coefficient', 0.0), timestamp)
        
        # Explorer metrics
        if 'explorer' in data:
            ex = data['explorer']
            self.record_metric('explorer_vp', ex.get('current_vp', 0.0), timestamp)
            self.record_metric('explorer_phase', self._phase_to_number(ex.get('phase', 'unknown')), timestamp)
            self.record_metric('explorer_breath_cycle', ex.get('breath_cycle', 0), timestamp)
        
        # Djinn Kernel metrics
        if 'djinn_kernel' in data:
            dk = data['djinn_kernel']
            self.record_metric('djinn_vp', dk.get('violation_pressure', 0.0), timestamp)
            self.record_metric('djinn_tape_cells', dk.get('tape_cells', 0), timestamp)
        
        self.last_update_time = timestamp
    
    def _phase_to_number(self, phase: str) -> float:
        """Convert phase name to number for tracking"""
        phase_map = {'unknown': 0, 'exploration': 1, 'analysis': 2, 'synthesis': 3}
        return phase_map.get(phase.lower(), 0)
    
    def get_trend(self, metric_name: str, window_size: int = 10) -> Dict[str, Any]:
        """Calculate trend statistics for a metric"""
        history = self.metrics_history.get(metric_name, [])
        if len(history) < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'change_percent': 0}
        
        # Get recent window
        recent = history[-window_size:] if len(history) >= window_size else history
        
        values = [v for _, v in recent]
        timestamps = [t for t, _ in recent]
        
        # Calculate slope (simple linear regression)
        n = len(values)
        if n < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'change_percent': 0}
        
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(t * v for t, v in zip(timestamps, values))
        sum_x2 = sum(t * t for t in timestamps)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        # Calculate percentage change
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 1e-6:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'trend': trend,
            'slope': slope,
            'change_percent': change_percent,
            'current_value': last_value,
            'previous_value': values[-2] if len(values) >= 2 else first_value,
            'min_value': min(values),
            'max_value': max(values),
            'avg_value': sum(values) / len(values),
            'data_points': len(recent)
        }
    
    def get_all_trends(self, window_size: int = 10) -> Dict[str, Dict[str, Any]]:
        """Get trend statistics for all tracked metrics"""
        return {metric: self.get_trend(metric, window_size) for metric in self.metrics_history.keys()}
    
    def detect_spikes(self, metric_name: str, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Detect spikes in a metric (values > threshold_multiplier * average)"""
        history = self.metrics_history.get(metric_name, [])
        if len(history) < 10:
            return []
        
        values = [v for _, v in history]
        avg = sum(values) / len(values)
        std_dev = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
        threshold = avg + (threshold_multiplier * std_dev)
        
        spikes = []
        for timestamp, value in history:
            if value > threshold:
                spikes.append({
                    'timestamp': timestamp,
                    'value': value,
                    'threshold': threshold,
                    'deviation': (value - avg) / std_dev if std_dev > 0 else 0
                })
        
        return spikes


# Initialize Ollama Bridge and Context Builder
project_root = Path(__file__).parent
log_dir = project_root / 'data' / 'logs'
shared_state_path = project_root / 'data' / '.shared_simulation_state.json'
# Load Ollama config from file if available
config_dir = project_root / 'data' / 'causation_explorer'
config_dir.mkdir(parents=True, exist_ok=True)
config_file = config_dir / 'ollama_config.json'

ollama_config = {}
if config_file.exists():
    try:
        with open(config_file, 'r') as f:
            ollama_config = json.load(f)
        logger.info(f"Loaded Ollama config from {config_file}")
    except Exception as e:
        logger.warning(f"Could not load Ollama config: {e}")

# Initialize OllamaBridge with config file settings (env vars take precedence)
ollama_bridge = OllamaBridge(
    base_url=os.getenv("OLLAMA_BASE_URL") or ollama_config.get("base_url"),
    timeout=float(os.getenv("OLLAMA_TIMEOUT", str(ollama_config.get("timeout", 30.0)))),
    api_key=os.getenv("OLLAMA_API_KEY") or ollama_config.get("api_key")
)

context_builder = SystemContextBuilder(log_dir, shared_state_path, explorer)
knowledge_base = SystemKnowledgeBase(project_root)
time_series_tracker = TimeSeriesTracker(max_history=1000)

# Initialize persistent context and predictive analyzer
storage_dir = project_root / 'data' / 'causation_explorer'
persistent_context = PersistentContext(storage_dir)
predictive_analyzer = PredictiveAnalyzer(time_series_tracker)


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
            component_counts = {}  # Debug: track component distribution
            for event_id, event in events_snapshot.items():
                # Normalize component names to match color mapping in HTML
                component = (event.component or 'unknown').lower().strip()
                # Map variations to standard names
                if 'reality' in component or 'sim' in component:
                    component = 'reality_sim'
                elif 'explorer' in component:
                    component = 'explorer'
                elif 'djinn' in component or 'kernel' in component or 'utm' in component:
                    component = 'djinn_kernel'
                elif 'breath' in component:
                    component = 'breath'
                elif 'system' in component:
                    component = 'system'
                else:
                    component = component  # Keep as-is (will default to orange)
                
                component_counts[component] = component_counts.get(component, 0) + 1
                nodes.append({
                    'id': event_id,
                    'component': component,  # Normalized component name
                    'type': event.event_type,
                    'data': event.data,
                    'timestamp': event.timestamp
                })
            # Log component distribution for debugging
            if component_counts:
                logger.info(f"Graph nodes by component: {component_counts}")
                logger.info(f"Total nodes: {len(nodes)}, Total links: {len(links)}")
        
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

@app.route('/api/ollama/config', methods=['GET'])
def get_ollama_config():
    """Get current Ollama configuration"""
    try:
        return jsonify({
            'base_url': ollama_bridge.base_url,
            'is_cloud': ollama_bridge.is_cloud,
            'has_api_key': bool(ollama_bridge.api_key),
            'timeout': ollama_bridge.timeout
        })
    except Exception as e:
        logger.error(f"Error getting Ollama config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/config', methods=['POST'])
def set_ollama_config():
    """Update Ollama configuration"""
    try:
        data = request.get_json()
        base_url = data.get('base_url')
        api_key = data.get('api_key')
        timeout = data.get('timeout')
        
        # Validate base_url
        if base_url:
            if base_url.startswith("https://ollama.com"):
                if not api_key:
                    return jsonify({'error': 'API key required for cloud mode'}), 400
            elif not base_url.startswith("http://"):
                return jsonify({'error': 'Invalid base URL. Use http://localhost:11434 or https://ollama.com'}), 400
        
        # Update OllamaBridge (only update provided values)
        update_kwargs = {}
        if base_url is not None:
            update_kwargs['base_url'] = base_url
        if api_key is not None:
            update_kwargs['api_key'] = api_key
        if timeout is not None:
            update_kwargs['timeout'] = float(timeout)
        
        if update_kwargs:
            ollama_bridge.update_config(**update_kwargs)
        
        # Save to config file
        config_data = {
            'base_url': ollama_bridge.base_url,
            'api_key': ollama_bridge.api_key,
            'timeout': ollama_bridge.timeout
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved Ollama config to {config_file}")
        except Exception as e:
            logger.warning(f"Could not save Ollama config: {e}")
        
        return jsonify({
            'success': True,
            'config': {
                'base_url': ollama_bridge.base_url,
                'is_cloud': ollama_bridge.is_cloud,
                'has_api_key': bool(ollama_bridge.api_key),
                'timeout': ollama_bridge.timeout
            }
        })
    except Exception as e:
        logger.error(f"Error setting Ollama config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama/test', methods=['POST'])
def test_ollama_connection():
    """Test Ollama connection"""
    try:
        models = ollama_bridge.list_models()
        if models or ollama_bridge.is_cloud:
            return jsonify({
                'success': True,
                'connected': True,
                'model_count': len(models),
                'mode': 'cloud' if ollama_bridge.is_cloud else 'local'
            })
        else:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'Could not connect to Ollama'
            }), 503
    except Exception as e:
        logger.error(f"Error testing Ollama connection: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 503


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
            # Ollama Cloud only supports Qwen3-VL for vision (in preview)
            # Local Ollama supports: llava, bakllava, moondream, minicpm-v, etc.
            if any(keyword in name_lower for keyword in ['vision', 'llava', 'clip', 'minicpm-v', 'bakllava', 'moondream', 'qwen3-vl', 'qwen-vl', 'qwen3vl']):
                vision_models.append({'name': model_name, 'model': model_name})
            else:
                text_models.append({'name': model_name, 'model': model_name})
            
            all_models.append({'name': model_name, 'model': model_name})
        
        # If no vision models found but we have models, add all as potential vision models (fallback)
        if not vision_models and all_models:
            vision_models = all_models.copy()
        
        # For Ollama Cloud, prioritize Qwen3-VL for vision (it's the only supported vision model)
        if ollama_bridge.is_cloud:
            # Find Qwen3-VL models and move them to front
            qwen_models = [m for m in vision_models if 'qwen3-vl' in m.get('name', '').lower() or 'qwen-vl' in m.get('name', '').lower()]
            if qwen_models:
                # Remove Qwen models from their current position
                vision_models = [m for m in vision_models if 'qwen3-vl' not in m.get('name', '').lower() and 'qwen-vl' not in m.get('name', '').lower()]
                # Add Qwen models to front
                vision_models = qwen_models + vision_models
        
        return jsonify({
            'models': all_models,
            'text_models': text_models,
            'vision_models': vision_models,
            'is_cloud': ollama_bridge.is_cloud,
            'cloud_vision_hint': 'Qwen3-VL' if ollama_bridge.is_cloud else None
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
        evolutionary_snapshots = data.get('evolutionary_snapshots', [])  # List of historical snapshots
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Update time-series tracker with current state
        try:
            if shared_state_path.exists():
                with open(shared_state_path, 'r') as f:
                    current_state = json.load(f)
                time_series_tracker.extract_metrics_from_state(current_state)
        except Exception as e:
            logger.debug(f"Could not update time-series tracker: {e}")
        
        # Build context
        context = context_builder.build_context(view_state=view_state, selected_event=selected_event)
        
        # Add system knowledge
        context['system_knowledge'] = knowledge_base.load_knowledge()
        
        # Add time-series trends and anomaly detection
        context['time_series_trends'] = time_series_tracker.get_all_trends(window_size=20)
        
        # Detect anomalies/spikes in key metrics
        anomalies = {}
        key_metrics = ['djinn_vp', 'explorer_vp', 'network_modularity', 'evolution_best_fitness']
        for metric in key_metrics:
            spikes = time_series_tracker.detect_spikes(metric, threshold_multiplier=2.0)
            if spikes:
                anomalies[metric] = spikes[-5:]  # Last 5 spikes
        
        if anomalies:
            context['anomalies'] = anomalies
        
        # If graph image provided, analyze it with vision model (images only, no context)
        # Vision model gets ONLY images. CRA gets vision analysis + all context.
        visual_description = None
        vision_error = None
        if graph_image and data.get('vision_model'):
            vision_model = data.get('vision_model')
            
            # Collect all images: current + evolutionary snapshots
            # Strategy: Send 2-3 most recent snapshots for evolution analysis
            # Reason: Multiple images = better evolution tracking, but payload limits constrain us
            MAX_VISION_IMAGES = 5  # Max snapshots to send (current + 4 previous) - more optimistic
            
            all_images = []
            
            # Add evolutionary snapshots first (they're older)
            if evolutionary_snapshots:
                # Extract images from snapshots (already sorted oldest to newest)
                snapshot_images = []
                for snapshot in evolutionary_snapshots:
                    if isinstance(snapshot, dict) and 'image' in snapshot:
                        img = snapshot['image']
                        if img:  # Only add non-empty images
                            snapshot_images.append(img)
                    elif isinstance(snapshot, str):
                        snapshot_images.append(snapshot)
                
                # Keep only the most recent evolutionary snapshots (keep last N-1, since we'll add current)
                if len(snapshot_images) > (MAX_VISION_IMAGES - 1):
                    snapshot_images = snapshot_images[-(MAX_VISION_IMAGES - 1):]
                    logger.debug(f"Limited evolutionary snapshots from {len(evolutionary_snapshots)} to {len(snapshot_images)}")
                
                all_images.extend(snapshot_images)
            
            # Add current image last (it's the newest)
            if graph_image:
                all_images.append(graph_image)
            
            # Final limit check - never send more than MAX
            if len(all_images) > MAX_VISION_IMAGES:
                all_images = all_images[-MAX_VISION_IMAGES:]
                logger.debug(f"Final limit: keeping {MAX_VISION_IMAGES} most recent images")
            
            if not all_images:
                vision_error = "No images available for vision analysis."
            else:
                # Log what we're sending
                logger.info(f"Vision model: Analyzing {len(all_images)} snapshot(s) - {'current + ' + str(len(all_images)-1) + ' evolutionary' if len(all_images) > 1 else 'current state only (no history yet)'}")
                
                # Minimal prompt for vision model - ONLY asks it to describe what it sees
                # NO system context - that goes to CRA instead
                if len(all_images) > 1:
                    vision_prompt = f"These {len(all_images)} images show the evolution of a causation graph over time (oldest to newest). Compare them and describe: What changes do you see? How does the graph structure, node positions, connections, and patterns evolve? Describe the evolution timeline from oldest to newest."
                else:
                    # Single image - describe current state, note that this is the first snapshot
                    vision_prompt = "This is a single snapshot of a causation graph visualization (no previous snapshots available for comparison yet). Describe what you see: What are the node colors and what do they represent? What is the graph structure? Are there clusters, isolated nodes, or branching patterns? What do the connections show? Note: This is the first snapshot, so no evolutionary analysis is possible yet."
                
                # Vision model ONLY gets images + minimal prompt
                # All context will go to CRA after vision analysis
                try:
                    visual_description = ollama_bridge.vision(vision_model, all_images, vision_prompt)
                    
                    if visual_description:
                        # Add metadata about snapshots for CRA context
                        if len(all_images) > 1:
                            visual_description = f"[Visual Evolution Analysis - {len(all_images)} snapshots]\n{visual_description}"
                        else:
                            visual_description = f"[Visual Analysis - Single Snapshot (no evolution data available yet)]\n{visual_description}"
                        
                        # Pass vision analysis to CRA context (CRA has all the data points)
                        context['visual_description'] = visual_description
                except Exception as e:
                    vision_error = f"Vision model error: {str(e)}"
                    logger.error(f"Vision model call failed: {e}", exc_info=True)
                    visual_description = None
        elif data.get('vision_model') and not graph_image:
            vision_error = "Vision model selected but no graph image captured. Try adjusting graph view or filters."
        
        # Build messages for chat
        messages = [{"role": "user", "content": message}]
        
        # Send to research assistant
        response = ollama_bridge.chat(model, messages, context)
        
        if response is None:
            return jsonify({'error': 'Failed to get response from Ollama'}), 500
        
        # Save chat messages to persistent context
        try:
            persistent_context.save_chat_message('user', message)
            persistent_context.save_chat_message('assistant', response)
            if visual_description:
                persistent_context.save_chat_message('vision', visual_description)
            
            # Save run summary periodically (every 10 messages or so)
            history = persistent_context.load_chat_history()
            if len(history) % 10 == 0:
                run_summary = {
                    'run_id': f"run_{int(time.time())}",
                    'timestamp': time.time(),
                    'metrics': current_metrics if current_metrics else {},
                    'graph_stats': {
                        'nodes': len(explorer.events) if explorer else 0,
                        'links': explorer.causation_graph.number_of_edges() if explorer else 0
                    },
                    'event_count': len(explorer.events) if explorer else 0
                }
                comparative_analyzer.save_run_summary(run_summary['run_id'], run_summary)
        except Exception as e:
            logger.debug(f"Could not save chat history: {e}")
        
        return jsonify({
            'response': response,
            'visual_description': visual_description,
            'vision_error': vision_error,  # Include vision errors for frontend display
            'context_sources': {
                'shared_state': shared_state_path.exists(),
                'log_files': len(list(log_dir.glob('*.log'))) if log_dir.exists() else 0,
                'graph_events': len(explorer.events) if explorer else 0
            },
            'trends': context.get('time_series_trends', {}),
            'anomalies': len(context.get('anomalies', {})),
            'alerts': len(context.get('alerts', [])),
            'predictions': len(context.get('predictive_insights', {}))
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
        
        try:
            response = ollama_bridge.vision(model, image_base64, prompt)
            if response is None:
                return jsonify({'error': 'Failed to get response from vision model'}), 500
            return jsonify({'description': response})
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Ollama vision: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 500
    except Exception as e:
        logger.error(f"Error in Ollama vision endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/compare', methods=['POST'])
def compare_runs_endpoint():
    """Compare two runs"""
    try:
        data = request.get_json()
        run1_id = data.get('run1_id')
        run2_id = data.get('run2_id')
        
        if not run1_id or not run2_id:
            return jsonify({'error': 'Both run1_id and run2_id are required'}), 400
        
        report = comparative_analyzer.generate_comparison_report(run1_id, run2_id)
        return jsonify({'report': report})
    except Exception as e:
        logger.error(f"Error comparing runs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/list')
def list_runs_endpoint():
    """List all saved runs"""
    try:
        runs = comparative_analyzer.load_run_summaries(max_runs=20)
        return jsonify({'runs': runs, 'count': len(runs)})
    except Exception as e:
        logger.error(f"Error listing runs: {e}", exc_info=True)
        return jsonify({'error': str(e), 'runs': []}), 500


@app.route('/api/chat/history')
def get_chat_history_endpoint():
    """Get chat history from persistent storage"""
    try:
        history = persistent_context.load_chat_history()
        return jsonify({'history': history, 'count': len(history)})
    except Exception as e:
        logger.error(f"Error loading chat history: {e}", exc_info=True)
        return jsonify({'error': str(e), 'history': []}), 500


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

