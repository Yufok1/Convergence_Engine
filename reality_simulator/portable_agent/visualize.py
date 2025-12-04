#!/usr/bin/env python3
"""
🦋 Butterfly Agent Visualizer

Interactive visualization tool for exported Butterfly System agents.
Run this script from within an extracted agent archive to explore:
- Neural activation heatmaps
- Behavioral fingerprints
- Decision-making process
- Scenario testing

Usage:
    cd agent_xxx/
    python portable_agent/visualize.py
    # Or from archive root:
    python -m portable_agent.visualize
"""

import json
import os
import sys
import webbrowser
import threading
import socket
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Try to import numpy and onnxruntime
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️  NumPy not installed. Install with: pip install numpy")

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️  ONNX Runtime not installed. Install with: pip install onnxruntime")

# Action mapping
ACTION_MAP = {
    0: 'move',
    1: 'cooperate',
    2: 'compete',
    3: 'rest',
    4: 'reproduce',
    5: 'isolate'
}

ACTION_COLORS = {
    'move': '#3498db',       # Blue
    'cooperate': '#2ecc71',  # Green
    'compete': '#e74c3c',    # Red
    'rest': '#9b59b6',       # Purple
    'reproduce': '#f39c12',  # Orange
    'isolate': '#7f8c8d'     # Gray
}


class AgentVisualizer:
    """Interactive visualizer for exported Butterfly agents."""
    
    def __init__(self, archive_dir: str = '.'):
        self.archive_dir = Path(archive_dir)
        self.metadata = self._load_metadata()
        self.session = self._load_model() if ONNX_AVAILABLE else None
        self.input_dim = self._get_input_dim()
        
    def _load_metadata(self) -> dict:
        """Load metadata.json from the archive."""
        metadata_path = self.archive_dir / 'metadata.json'
        if not metadata_path.exists():
            print(f"❌ metadata.json not found in {self.archive_dir}")
            return {}
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_model(self):
        """Load the ONNX or TorchScript model."""
        # Try ONNX first
        onnx_path = self.archive_dir / 'brain.onnx'
        if onnx_path.exists():
            try:
                session = ort.InferenceSession(str(onnx_path))
                print(f"✅ Loaded ONNX model: {onnx_path}")
                return session
            except Exception as e:
                print(f"⚠️  Failed to load ONNX model: {e}")
        
        # Try TorchScript
        ts_path = self.archive_dir / 'brain.torchscript'
        if ts_path.exists():
            try:
                import torch
                model = torch.jit.load(str(ts_path))
                model.eval()
                print(f"✅ Loaded TorchScript model: {ts_path}")
                return model
            except Exception as e:
                print(f"⚠️  Failed to load TorchScript model: {e}")
        
        print("❌ No compatible model found (brain.onnx or brain.torchscript)")
        return None
    
    def _get_input_dim(self) -> int:
        """Get the input dimension from metadata or model."""
        # Check neural_network architecture first
        if self.metadata:
            arch = self.metadata.get('neural_network', {}).get('architecture', {})
            if 'input_size' in arch:
                return arch['input_size']
            
            # Check ensemble members
            ensemble = self.metadata.get('ensemble', {})
            members = ensemble.get('members', [])
            if members and 'input_dim' in members[0]:
                return members[0]['input_dim']
            
            # Check max_input_dim from ensemble
            if 'max_input_dim' in ensemble:
                return ensemble['max_input_dim']
        
        # Check bridge_config.json
        config_path = self.archive_dir / 'bridge_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                if 'state_dim' in config:
                    return config['state_dim']
            except Exception:
                pass
        
        # Default fallback
        return 24  # Updated default to match current system
    
    def predict(self, state: list) -> dict:
        """Run inference and return Q-values and action."""
        if not NUMPY_AVAILABLE:
            return {'error': 'NumPy not available'}
        
        if self.session is None:
            return {'error': 'Model not loaded'}
        
        state_np = np.array(state, dtype=np.float32).reshape(1, -1)
        
        # Pad or truncate to match input dimension
        if state_np.shape[1] < self.input_dim:
            pad = np.zeros((1, self.input_dim - state_np.shape[1]), dtype=np.float32)
            state_np = np.concatenate([state_np, pad], axis=1)
        elif state_np.shape[1] > self.input_dim:
            state_np = state_np[:, :self.input_dim]
        
        try:
            if isinstance(self.session, ort.InferenceSession):
                # ONNX inference
                input_name = self.session.get_inputs()[0].name
                outputs = self.session.run(None, {input_name: state_np})
                q_values = outputs[0].flatten().tolist()
            else:
                # TorchScript inference
                import torch
                with torch.no_grad():
                    state_tensor = torch.from_numpy(state_np)
                    output = self.session(state_tensor)
                    if isinstance(output, tuple):
                        output = output[0]
                    q_values = output.flatten().tolist()
            
            # Get action with highest Q-value
            action_idx = int(np.argmax(q_values))
            action_name = ACTION_MAP.get(action_idx, f'action_{action_idx}')
            
            return {
                'q_values': q_values,
                'action_index': action_idx,
                'action_name': action_name,
                'confidence': float(max(q_values) - np.mean(q_values))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_fingerprint(self) -> dict:
        """Get behavioral fingerprint from metadata."""
        return self.metadata.get('behavioral_fingerprint', {})
    
    def generate_html(self) -> str:
        """Generate the visualization HTML page."""
        fingerprint = self.get_fingerprint()
        arch = self.metadata.get('neural_network', {}).get('architecture', {})
        organism_id = self.metadata.get('agent_id', 'Unknown')[:16]
        
        # Action distribution bars
        action_dist = fingerprint.get('action_distribution', {})
        action_bars_html = ""
        for action, prob in action_dist.items():
            color = ACTION_COLORS.get(action, '#666')
            width = int(prob * 100)
            action_bars_html += f'''
                <div class="action-bar">
                    <span class="action-label">{action}</span>
                    <div class="bar-container">
                        <div class="bar" style="width: {width}%; background: {color};"></div>
                    </div>
                    <span class="action-value">{prob:.1%}</span>
                </div>
            '''
        
        # Scenario responses
        scenarios = fingerprint.get('scenario_responses', {})
        scenario_html = ""
        for scenario, response in scenarios.items():
            color = ACTION_COLORS.get(response, '#666')
            scenario_html += f'<div class="scenario"><strong>{scenario.replace("_", " ").title()}:</strong> <span style="color: {color}; font-weight: bold;">{response}</span></div>'
        
        # Input sliders (24 dimensions to match current neural system)
        input_labels = [
            'pos_x', 'pos_y', 'pos_z',                        # 0-2: position
            'vel_x', 'vel_y', 'vel_z',                        # 3-5: velocity
            'energy', 'health', 'age',                        # 6-8: vitality
            'threat_1', 'threat_2', 'threat_3',               # 9-11: threats
            'resource_1', 'resource_2', 'resource_3',         # 12-14: resources
            'social_1', 'social_2', 'social_3',               # 15-17: social
            'alliance', 'battle',                             # 18-19: combat
            'vocab_size', 'comm_activity',                    # 20-21: language
            'vp', 'coherence'                                 # 22-23: stability
        ]
        # Extend labels if input_dim > 24
        while len(input_labels) < self.input_dim:
            input_labels.append(f'input_{len(input_labels)}')
        
        sliders_html = ""
        for i, label in enumerate(input_labels[:self.input_dim]):
            sliders_html += f'''
                <div class="slider-row">
                    <label for="input_{i}">{label}</label>
                    <input type="range" id="input_{i}" min="0" max="1" step="0.01" value="0.5" 
                           oninput="updateInput({i}, this.value)">
                    <span id="value_{i}">0.50</span>
                </div>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦋 Agent Visualizer - {organism_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 900px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
        .panel {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .panel h2 {{
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.2em;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 10px;
        }}
        .action-bar {{
            display: flex;
            align-items: center;
            margin: 8px 0;
        }}
        .action-label {{
            width: 100px;
            font-size: 0.9em;
        }}
        .bar-container {{
            flex: 1;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin: 0 10px;
        }}
        .bar {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        .action-value {{
            width: 50px;
            text-align: right;
            font-size: 0.9em;
        }}
        .personality {{
            text-align: center;
            padding: 20px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .personality-label {{
            font-size: 2em;
            font-weight: bold;
            color: #00d4ff;
            text-transform: uppercase;
        }}
        .scenario {{
            padding: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            margin: 5px 0;
        }}
        .slider-row {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 0.85em;
        }}
        .slider-row label {{
            width: 80px;
            color: #888;
        }}
        .slider-row input[type="range"] {{
            flex: 1;
            margin: 0 10px;
            accent-color: #00d4ff;
        }}
        .slider-row span {{
            width: 40px;
            text-align: right;
        }}
        .decision-display {{
            text-align: center;
            padding: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            margin-top: 15px;
        }}
        .decision-action {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .q-values {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin-top: 15px;
        }}
        .q-value {{
            text-align: center;
            padding: 10px;
            min-width: 80px;
        }}
        .q-value-label {{
            font-size: 0.8em;
            color: #888;
        }}
        .q-value-num {{
            font-size: 1.2em;
            font-weight: bold;
        }}
        .preset-btn {{
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.1s, box-shadow 0.1s;
        }}
        .preset-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}
        .presets {{
            text-align: center;
            margin: 15px 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        .stat-item {{
            background: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .stat-label {{
            font-size: 0.8em;
            color: #888;
        }}
        #heatmap {{
            width: 100%;
            height: 200px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 15px;
        }}
        .heatmap-row {{
            display: flex;
            margin: 2px 0;
        }}
        .heatmap-cell {{
            width: 20px;
            height: 20px;
            margin: 1px;
            border-radius: 2px;
            transition: background-color 0.2s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🦋 Butterfly Agent Visualizer</h1>
        <p class="subtitle">Organism: {organism_id} | Format: {self.metadata.get('export_format', 'unknown').upper()}</p>
        
        <div class="grid">
            <!-- Left Column: Fingerprint -->
            <div class="panel">
                <h2>🎭 Behavioral Fingerprint</h2>
                
                <div class="personality">
                    <div class="personality-label">{fingerprint.get('personality_label', 'Unknown')}</div>
                    <div>Dominant: {fingerprint.get('dominant_action', 'N/A')} ({fingerprint.get('dominant_action_percentage', 0)}%)</div>
                </div>
                
                <h3 style="margin: 15px 0 10px; color: #888;">Action Distribution</h3>
                {action_bars_html}
                
                <h3 style="margin: 15px 0 10px; color: #888;">Scenario Responses</h3>
                {scenario_html}
                
                <div class="stats-grid" style="margin-top: 15px;">
                    <div class="stat-item">
                        <div class="stat-value">{fingerprint.get('behavioral_tendencies', {}).get('cooperative', 0):.0%}</div>
                        <div class="stat-label">Cooperative</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{fingerprint.get('behavioral_tendencies', {}).get('competitive', 0):.0%}</div>
                        <div class="stat-label">Competitive</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{fingerprint.get('behavioral_tendencies', {}).get('passive', 0):.0%}</div>
                        <div class="stat-label">Passive</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{fingerprint.get('decision_confidence', {}).get('mean', 0):.2f}</div>
                        <div class="stat-label">Confidence</div>
                    </div>
                </div>
            </div>
            
            <!-- Right Column: Interactive Testing -->
            <div class="panel">
                <h2>🧪 Interactive Testing</h2>
                
                <div class="presets">
                    <button class="preset-btn" style="background: #e74c3c; color: white;" onclick="setPreset('threat')">⚠️ High Threat</button>
                    <button class="preset-btn" style="background: #f39c12; color: white;" onclick="setPreset('low_energy')">🔋 Low Energy</button>
                    <button class="preset-btn" style="background: #2ecc71; color: white;" onclick="setPreset('social')">🤝 Social</button>
                    <button class="preset-btn" style="background: #3498db; color: white;" onclick="setPreset('explore')">🔍 Explore</button>
                    <button class="preset-btn" style="background: #9b59b6; color: white;" onclick="setPreset('random')">🎲 Random</button>
                </div>
                
                <div style="max-height: 300px; overflow-y: auto; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                    {sliders_html}
                </div>
                
                <div class="decision-display">
                    <div class="decision-action" id="current-action">-</div>
                    <div id="confidence-display">Adjust inputs above</div>
                    
                    <div class="q-values" id="q-values-display">
                        <!-- Q-values will be populated by JavaScript -->
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Neural Architecture Info -->
        <div class="panel" style="margin-top: 20px;">
            <h2>🧠 Neural Architecture</h2>
            <div class="stats-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="stat-item">
                    <div class="stat-value">{arch.get('input_size', '?')}</div>
                    <div class="stat-label">Input Dim</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{arch.get('hidden_size', '?')}</div>
                    <div class="stat-label">Hidden Size</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{arch.get('output_size', '?')}</div>
                    <div class="stat-label">Output (Actions)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{arch.get('total_parameters', '?')}</div>
                    <div class="stat-label">Parameters</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const inputDim = {self.input_dim};
        let inputValues = new Array(inputDim).fill(0.5);
        
        const actionColors = {{
            'move': '#3498db',
            'cooperate': '#2ecc71',
            'compete': '#e74c3c',
            'rest': '#9b59b6',
            'reproduce': '#f39c12',
            'isolate': '#7f8c8d'
        }};
        
        function updateInput(idx, value) {{
            inputValues[idx] = parseFloat(value);
            document.getElementById('value_' + idx).textContent = parseFloat(value).toFixed(2);
            runInference();
        }}
        
        function setPreset(preset) {{
            // Reset all to 0.5
            inputValues = new Array(inputDim).fill(0.5);
            
            switch(preset) {{
                case 'threat':
                    // High threat signals (dims 9-11)
                    if (inputDim > 9) inputValues[9] = 0.9;
                    if (inputDim > 10) inputValues[10] = 0.8;
                    if (inputDim > 11) inputValues[11] = 0.7;
                    break;
                case 'low_energy':
                    // Low energy (dims 6-8)
                    if (inputDim > 6) inputValues[6] = 0.1;
                    if (inputDim > 7) inputValues[7] = 0.2;
                    if (inputDim > 8) inputValues[8] = 0.3;
                    break;
                case 'social':
                    // High social signals (dims 15-17)
                    if (inputDim > 15) inputValues[15] = 0.9;
                    if (inputDim > 16) inputValues[16] = 0.8;
                    if (inputDim > 17) inputValues[17] = 0.7;
                    break;
                case 'explore':
                    // High movement, medium everything else
                    if (inputDim > 3) inputValues[3] = 0.8;
                    if (inputDim > 4) inputValues[4] = 0.8;
                    if (inputDim > 5) inputValues[5] = 0.6;
                    break;
                case 'random':
                    inputValues = inputValues.map(() => Math.random());
                    break;
            }}
            
            // Update sliders
            for (let i = 0; i < inputDim; i++) {{
                const slider = document.getElementById('input_' + i);
                const valueSpan = document.getElementById('value_' + i);
                if (slider && valueSpan) {{
                    slider.value = inputValues[i];
                    valueSpan.textContent = inputValues[i].toFixed(2);
                }}
            }}
            
            runInference();
        }}
        
        async function runInference() {{
            try {{
                const response = await fetch('/predict', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ state: inputValues }})
                }});
                
                const result = await response.json();
                
                if (result.error) {{
                    document.getElementById('current-action').textContent = '❌ Error';
                    document.getElementById('confidence-display').textContent = result.error;
                    return;
                }}
                
                // Update action display
                const actionEl = document.getElementById('current-action');
                actionEl.textContent = result.action_name.toUpperCase();
                actionEl.style.color = actionColors[result.action_name] || '#fff';
                
                document.getElementById('confidence-display').textContent = 
                    `Confidence: ${{result.confidence.toFixed(3)}}`;
                
                // Update Q-values display
                const qDisplay = document.getElementById('q-values-display');
                qDisplay.innerHTML = result.q_values.map((q, i) => {{
                    const actionName = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'][i] || 'action_' + i;
                    const color = actionColors[actionName] || '#666';
                    const isMax = i === result.action_index;
                    return `
                        <div class="q-value" style="${{isMax ? 'background: rgba(0,212,255,0.2); border-radius: 4px;' : ''}}">
                            <div class="q-value-num" style="color: ${{color}}">${{q.toFixed(3)}}</div>
                            <div class="q-value-label">${{actionName}}</div>
                        </div>
                    `;
                }}).join('');
                
            }} catch (e) {{
                document.getElementById('current-action').textContent = '❌ Error';
                document.getElementById('confidence-display').textContent = e.message;
            }}
        }}
        
        // Initial inference
        runInference();
    </script>
</body>
</html>
'''
        return html


class VisualizerHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the visualizer server."""
    
    visualizer = None
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = self.visualizer.generate_html()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/predict':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            result = self.visualizer.predict(data.get('state', []))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


def find_free_port(start=5001, end=5100):
    """Find an available port."""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start


def main():
    """Main entry point for the visualizer."""
    # Determine archive directory
    if len(sys.argv) > 1:
        archive_dir = sys.argv[1]
    else:
        # Try current directory, then parent (if run from portable_agent/)
        if Path('metadata.json').exists():
            archive_dir = '.'
        elif Path('../metadata.json').exists():
            archive_dir = '..'
        else:
            print("❌ Could not find metadata.json")
            print("   Run this script from an extracted agent archive directory")
            print("   Usage: python visualize.py [archive_directory]")
            sys.exit(1)
    
    print(f"🦋 Butterfly Agent Visualizer")
    print(f"   Archive: {Path(archive_dir).absolute()}")
    
    # Create visualizer
    viz = AgentVisualizer(archive_dir)
    
    if not viz.metadata:
        print("❌ Failed to load agent metadata")
        sys.exit(1)
    
    # Print agent info
    agent_id = viz.metadata.get('agent_id', 'Unknown')[:16]
    personality = viz.get_fingerprint().get('personality_label', 'Unknown')
    print(f"   Agent ID: {agent_id}...")
    print(f"   Personality: {personality}")
    
    # Find port and start server
    port = find_free_port()
    VisualizerHandler.visualizer = viz
    
    server = HTTPServer(('localhost', port), VisualizerHandler)
    url = f'http://localhost:{port}'
    
    print(f"\n✅ Server running at {url}")
    print("   Press Ctrl+C to stop\n")
    
    # Open browser
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
