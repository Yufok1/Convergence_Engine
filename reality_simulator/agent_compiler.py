import torch
import json
import zipfile
from io import BytesIO
import numpy as np
import datetime
import os
import sys
from typing import Dict, Any, List
import base64
import uuid

# Optional ONNX runtime - graceful degradation if not installed
try:
    import onnxruntime
    ONNX_AVAILABLE = True
except ImportError:
    onnxruntime = None
    ONNX_AVAILABLE = False

# Assuming Organism and OrganismBrain are importable from their respective paths
# Using relative imports suitable for agent_compiler.py in reality_simulator/
try:
    from .evolution_engine import Organism, Genotype, Phenotype
    from .neural.brain import OrganismBrain
    from .checkpointing.organism_capsule import OrganismCapsule
except ImportError:
    # Fallback for direct execution or different import contexts
    import sys
    from pathlib import Path
    
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir)) # Add reality_simulator to path
    
    from evolution_engine import Organism, Genotype, Phenotype
    from neural.brain import OrganismBrain
    from checkpointing.organism_capsule import OrganismCapsule

import logging
logger = logging.getLogger(__name__)

# Constants for action mapping
ACTION_MAP = {
    0: 'move',
    1: 'cooperate',
    2: 'compete',
    3: 'rest',
    4: 'reproduce',
    5: 'isolate'
}

class AgentCompiler:
    """
    Compiles a NeuralOrganism's state, particularly its neural network brain,
    into a portable, deployable agent archive.
    """

    def __init__(self):
        self.supported_formats = ['onnx', 'torchscript', 'statedict']

    class MultiOrganismWrapper(torch.nn.Module):
        def __init__(self, brains: List['OrganismBrain'], names: List[str]):
            super().__init__()
            self.brains = torch.nn.ModuleList(brains)
            self.names = names
            self.input_dims = [b.input_dim for b in brains]
            self.output_dims = [b.output_dim for b in brains]
            self.max_input_dim = max(self.input_dims) if self.input_dims else 0

        def forward(self, x: torch.Tensor):
            # x shape: [B, max_input_dim] (we will slice/pad per brain)
            outputs = []
            for brain, in_dim in zip(self.brains, self.input_dims):
                if x.shape[1] < in_dim:
                    pad = torch.zeros(x.shape[0], in_dim - x.shape[1], dtype=x.dtype, device=x.device)
                    x_i = torch.cat([x, pad], dim=1)
                else:
                    x_i = x[:, :in_dim]
                out = brain(x_i)
                outputs.append(out)
            return tuple(outputs)
        
    def _reconstruct_brain_from_capsule(self, capsule: OrganismCapsule) -> OrganismBrain:
        """
        Reconstructs the OrganismBrain model from the capsule data.
        Uses capsule.neural (NeuralSnapshot) for reconstruction.
        """
        if not capsule.neural:
            raise ValueError("Capsule does not contain neural network state.")
        
        # Extract from NeuralSnapshot
        neural_snap = capsule.neural
        brain_state_dict_b64 = neural_snap.to_dict().get('state_dict_b64')
        
        if not brain_state_dict_b64:
            raise ValueError("Neural network state in capsule is incomplete.")
            
        # Extract parameters from NeuralSnapshot
        input_dim = neural_snap.input_size
        hidden_dim = neural_snap.hidden_size
        output_dim = neural_snap.output_size
        # NeuralSnapshot doesn't store these, use defaults
        activation = 'relu'
        dropout = 0.0
        use_attention = False
        num_attention_heads = 4
        attention_dim = 64
        vocab_size = 50000  # Default
        use_language_head = False  # Will be detected from state_dict

        # Create a new instance of OrganismBrain with the same architecture
        reconstructed_brain = OrganismBrain(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            activation=activation,
            dropout=dropout,
            use_attention=use_attention,
            num_attention_heads=num_attention_heads,
            attention_dim=attention_dim,
            vocab_size=vocab_size,
            use_language_head=use_language_head
        )
        
        # Load the state_dict (handle possible compression)
        state_dict_bytes = base64.b64decode(brain_state_dict_b64)
        # Some snapshots may be gzip or zip compressed before base64 encoding
        try:
            if len(state_dict_bytes) >= 2 and state_dict_bytes[:2] == b"\x1f\x8b":
                import gzip
                state_dict_bytes = gzip.decompress(state_dict_bytes)
            elif len(state_dict_bytes) >= 2 and state_dict_bytes[:2] == b"PK":
                # ZIP archive; read first plausible tensor file
                with zipfile.ZipFile(BytesIO(state_dict_bytes)) as zf:
                    names = zf.namelist()
                    candidate = None
                    for ext in ('.pt', '.pth', '.pkl', '.bin', '.tensors'):
                        for n in names:
                            if n.lower().endswith(ext):
                                candidate = n
                                break
                        if candidate:
                            break
                    if not candidate and names:
                        candidate = names[0]
                    state_dict_bytes = zf.read(candidate)
        except Exception:
            # If decompression fails, fall back to raw bytes
            pass

        # PyTorch 2.6 defaults weights_only=True; allow full, trusted load
        state_dict = torch.load(BytesIO(state_dict_bytes), map_location='cpu', weights_only=False)

        # Infer architecture from state_dict to avoid shape/key mismatches
        sd_keys = set(state_dict.keys())
        def _shape(name, dim):
            return state_dict[name].shape[dim] if name in state_dict else None

        inferred_input = _shape('fc1.weight', 1) or getattr(capsule.neural, 'input_size', None) or 18
        inferred_hidden = _shape('fc1.weight', 0) or getattr(capsule.neural, 'hidden_size', None) or 64
        inferred_output = _shape('fc3.weight', 0) or getattr(capsule.neural, 'output_size', None) or 6

        use_attention = any(k.startswith('attention.') for k in sd_keys) or 'attention_norm.weight' in sd_keys
        use_language_head = 'fc_language.weight' in sd_keys
        use_concept_head = any(k.startswith('concept_head.') for k in sd_keys)

        vocab_size = state_dict['fc_language.weight'].shape[0] if use_language_head else 50000

        # Create a new instance of OrganismBrain matching the checkpoint
        reconstructed_brain = OrganismBrain(
            input_dim=int(inferred_input),
            hidden_dim=int(inferred_hidden),
            output_dim=int(inferred_output),
            activation='relu',
            dropout=0.0,
            use_attention=bool(use_attention),
            num_attention_heads=4,
            attention_dim=int(inferred_hidden),
            vocab_size=int(vocab_size),
            use_language_head=bool(use_language_head),
            use_concept_head=bool(use_concept_head)
        )

        # Load state dict allowing extra/missing keys (robust to optional heads)
        missing, unexpected = reconstructed_brain.load_state_dict(state_dict, strict=False)
        if unexpected:
            logger.debug(f"AgentCompiler: Ignored unexpected keys during load: {sorted(list(unexpected))[:5]}...")
        reconstructed_brain.eval() # Set to evaluation mode
        
        return reconstructed_brain

    def _export_onnx(self, brain: OrganismBrain, dummy_input: torch.Tensor, model_path: str) -> None: 
        """Exports the PyTorch brain to ONNX format."""
        try:
            torch.onnx.export(
                brain,
                dummy_input,
                model_path,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
                opset_version=11 # A commonly supported opset version
            )
            logger.info(f"Successfully exported brain to ONNX: {model_path}")
        except Exception as e:
            # Provide clearer guidance when onnx/onnxscript is missing (PyTorch 2.6+)
            msg = str(e)
            hint = ""
            if 'onnxscript' in msg.lower():
                hint = " (install with: pip install onnx onnxscript)"
            logger.error(f"Failed to export brain to ONNX at {model_path}: {e}{hint}")
            raise

    def _export_torchscript(self, brain: OrganismBrain, model_path) -> None: 
        """Exports the PyTorch brain to TorchScript format.
        
        Args:
            brain: The OrganismBrain to export
            model_path: Either a file path string or a BytesIO buffer
        """
        try:
            # Use torch.jit.trace instead of torch.jit.script
            # trace captures the execution path dynamically, which works with
            # OrganismBrain's complex control flow (conditional attention, etc.)
            # script analyzes code statically and fails on Python 3.12 + PyTorch 2.5
            brain.eval()  # Disable dropout for deterministic tracing
            dummy_input = torch.randn(1, brain.input_dim, dtype=torch.float32)
            traced_brain = torch.jit.trace(brain, (dummy_input,))
            
            # Handle both file path (str) and BytesIO buffer
            if isinstance(model_path, BytesIO):
                torch.jit.save(traced_brain, model_path)
                model_path.seek(0)  # Reset buffer position for reading
                logger.info("Successfully exported brain to TorchScript (traced) in memory buffer")
            else:
                traced_brain.save(model_path)
                logger.info(f"Successfully exported brain to TorchScript (traced): {model_path}")
        except Exception as e:
            logger.error(f"Failed to export brain to TorchScript: {e}")
            raise

    def _export_statedict(self, brain: OrganismBrain, model_path: str) -> None: 
        """Exports the PyTorch brain's state_dict."""
        try:
            torch.save(brain.state_dict(), model_path)
            logger.info(f"Successfully exported brain state_dict: {model_path}")
        except Exception as e:
            logger.error(f"Failed to export brain state_dict at {model_path}: {e}")
            raise

    def _create_rich_metadata(self, capsule: OrganismCapsule) -> Dict[str, Any]:
        """
        Creates comprehensive metadata for the compiled agent, leveraging the rich capsule data.
        """
        metadata = {
            'agent_id': capsule.organism_id,
            'capsule_id': capsule.capsule_id,
            'export_timestamp': datetime.datetime.now().isoformat(),
            'capsule_version': capsule.version,
            'capture_reason': capsule.capture_reason,

            # Organism Core Data
            'organism_core': {
                'species_id': capsule.organism_id,
                'capsule_id': capsule.capsule_id,
                'fitness': capsule.fitness.fitness_history[-1][1] if capsule.fitness and capsule.fitness.fitness_history else None,
                'organism_age': capsule.organism_age,
                'birth_time': capsule.organism_birth_time,
            },
            
            # Neural Network Details
            'neural_network': {
                'architecture': {
                    'input_size': capsule.neural.input_size,
                    'hidden_size': capsule.neural.hidden_size,
                    'output_size': capsule.neural.output_size,
                    'num_layers': capsule.neural.num_layers,
                    'total_parameters': capsule.neural.total_parameters
                } if capsule.neural else {},
                'training_steps': capsule.neural.training_steps if capsule.neural else 0,
                'avg_loss': None,
                'device_trained_on': 'cpu',
            },
            
            # Language System Details
            'atomic_language': {
                'enabled': bool(capsule.language),
                'concept_count': capsule.language.total_concepts if capsule.language else 0,
                'dialect_signature': str(capsule.language.dialect_signature) if capsule.language else 'N/A',
            },

            # Configuration & Environment
            'atomic_config': {
                'enabled': bool(capsule.config),
                'atom_count': len(capsule.config.atoms) if capsule.config else 0,
            },
            'environment_context': capsule.environment.to_dict() if capsule.environment else {},
            
            # Highlander & Social Data
            'highlander_data': capsule.highlander.to_dict() if capsule.highlander else {},
            'social_connections': {},  # Not stored in capsule directly
            
            # Causation Trace
            'causation_trace': {
                'enabled': bool(capsule.causation),
                'key_event_count': len(capsule.causation.key_events) if capsule.causation else 0,
                'turning_point_count': len(capsule.causation.turning_points) if capsule.causation else 0,
                'causal_chain_count': len(capsule.causation.causal_chains) if capsule.causation else 0,
            },
            
            # Export Options (to be added by the compiler)
            'export_format': None, 
            'runtime_dependencies': {
                'onnxruntime': onnxruntime.__version__ if ONNX_AVAILABLE else 'not installed',
                'numpy': np.__version__,
                'python': sys.version.split(' ')[0]
            },
            'compatibility': {
                'python_versions': ['3.8+', '3.9+', '3.10+', '3.11+', '3.12+'],
                'platforms': ['windows', 'linux', 'macos'],
                'architectures': ['x64', 'arm64']
            }
        }
        return metadata

    def _generate_runner_script(self, export_format: str, metadata: Dict[str, Any]) -> str:
        """Generates a standalone Python script to load and run the agent."""
        
        # Action map directly from metadata
        action_map_str = json.dumps(ACTION_MAP)

        script_template = """
import onnxruntime
import numpy as np
import json
import os
import time

ACTION_MAP = {action_map_str}

class AgentRunner:
    def __init__(self, model_filename="{model_filename}", metadata_filename="metadata.json"):
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        
        if not os.path.exists(self.model_filename):
            raise FileNotFoundError(f"Model file not found: {{self.model_filename}}")
        if not os.path.exists(self.metadata_filename):
            raise FileNotFoundError(f"Metadata file not found: {{self.metadata_filename}}")
            
        with open(self.metadata_filename, "r") as f:
            self.metadata = json.load(f)
            
        print("\\n--- Agent Loaded ---")
        print(f"Organism ID: {{self.metadata['organism_core']['species_id']}}")
        print(f"Fitness: {{self.metadata['organism_core']['fitness']:.3f}}")
        print(f"Age: {{self.metadata['organism_core']['organism_age']}} generations")
        print(f"Exported: {{self.metadata['export_timestamp']}}")
        
        self.input_dim = self.metadata['neural_network']['architecture']['input_size']
        self.output_actions = [ACTION_MAP[i] for i in range(self.metadata['neural_network']['architecture']['output_size'])]
        
        print(f"NN Input Dim: {{self.input_dim}}")
        print(f"NN Output Actions: {{self.output_actions}}")
        print("--------------------\\n")

        self.session = None
        if "{export_format}" == "onnx":
            # Try to use CUDA provider first if available
            providers = onnxruntime.get_available_providers()
            if 'CUDAExecutionProvider' in providers:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CUDAExecutionProvider'])
                print("Using CUDAExecutionProvider for ONNX inference.")
            else:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CPUExecutionProvider'])
                print("Using CPUExecutionProvider for ONNX inference.")
        elif "{export_format}" == "torchscript":
            import torch
            self.model = torch.jit.load(self.model_filename)
            self.model.eval()
            print("TorchScript model loaded.")
        elif "{export_format}" == "statedict":
            import torch
            from reality_simulator.neural.brain import OrganismBrain # Requires brain definition
            
            # Load state_dict first and infer architecture
            sd = torch.load(self.model_filename, map_location='cpu', weights_only=False)
            keys = set(sd.keys())
            def _shape(name, dim):
                return sd[name].shape[dim] if name in sd else None
            in_dim = _shape('fc1.weight', 1) or 18
            hid_dim = _shape('fc1.weight', 0) or 64
            out_dim = _shape('fc3.weight', 0) or 6
            use_attn = any(k.startswith('attention.') for k in keys) or 'attention_norm.weight' in keys
            use_lang = 'fc_language.weight' in keys
            use_concept = any(k.startswith('concept_head.') for k in keys)
            vocab = sd['fc_language.weight'].shape[0] if use_lang and 'fc_language.weight' in sd else 50000

            self.model = OrganismBrain(
                input_dim=int(in_dim), hidden_dim=int(hid_dim),
                output_dim=int(out_dim), activation='relu',
                dropout=0.0, use_attention=bool(use_attn),
                num_attention_heads=4, attention_dim=int(hid_dim),
                vocab_size=int(vocab), use_language_head=bool(use_lang),
                use_concept_head=bool(use_concept)
            )
            self.model.load_state_dict(sd, strict=False)
            self.model.eval()
            print("PyTorch state_dict model loaded (requires OrganismBrain class).")

    def decide_action(self, state_vector):
        if len(state_vector) != self.input_dim:
            raise ValueError(f"State vector must have {{self.input_dim}} dimensions, got {{len(state_vector)}}")
        
        if "{export_format}" == "onnx":
            state_array = np.array(state_vector, dtype=np.float32).reshape(1, -1)
            inputs = {{self.session.get_inputs()[0].name: state_array}}
            outputs = self.session.run(None, inputs)
            action_index = np.argmax(outputs[0])
        elif "{export_format}" == "torchscript":
            import torch
            state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                action_probs = self.model(state_tensor)
            action_index = torch.argmax(action_probs).item()
        elif "{export_format}" == "statedict":
            import torch
            state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                action_probs = self.model(state_tensor)
            action_index = torch.argmax(action_probs).item()
        else:
            raise ValueError(f"Unsupported export format: {{self.metadata['export_format']}}")
        
        return ACTION_MAP.get(action_index, "unknown")

if __name__ == '__main__':
    print("--- Running Agent Example ---")
    
    # Example usage:
    # 1. Initialize runner
    runner = AgentRunner()
    
    # 2. Provide a dummy state vector (replace with actual sensor data)
    # The agent expects a state vector of input_dim size
    dummy_state = np.random.rand(runner.input_dim) 
    
    # 3. Get agent's decision
    action = runner.decide_action(dummy_state)
    
    print(f"Agent decision for dummy state: {{action}}")
    
    print("\\n--- Simulating 5 decisions ---")
    for i in range(5):
        # Simulate a slightly changing state
        simulated_state = np.random.rand(runner.input_dim) + (np.random.randn(runner.input_dim) * 0.1)
        decision = runner.decide_action(simulated_state)
        print(f"Step {{i+1}}: State={{simulated_state[:3]}}..., Decision={{decision}}")
        time.sleep(0.5)

    print("\\n--- Agent Example Complete ---")
"""
        return script_template.format(
            action_map_str=action_map_str,
            model_filename=f"brain.{export_format}",
            export_format=export_format
        )

    def _create_agent_archive(self, 
                             model_buffer: BytesIO, 
                             metadata: Dict[str, Any], 
                             runner_script: str, 
                             capsule: OrganismCapsule) -> BytesIO:
        """Packages all components into a ZIP archive."""
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Neural Model
            model_buffer.seek(0) # Ensure buffer is at the beginning
            zf.writestr(f"brain.{metadata['export_format']}", model_buffer.read())
            
            # 2. Metadata (JSON)
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # 3. Genotype (JSON)
            if capsule.traits:
                zf.writestr("genotype.json", json.dumps(capsule.traits.to_dict(), indent=2))
            
            # 4. Atomic Config (JSON)
            if capsule.config:
                zf.writestr("atomic_config.json", json.dumps(capsule.config.to_dict(), indent=2))
            
            # 5. Atomic Language (JSON)
            if capsule.language:
                zf.writestr("atomic_language.json", json.dumps(capsule.language.to_dict(), indent=2))

            # 6. Runner Script
            zf.writestr("run_agent.py", runner_script)

            # 7. Requirements.txt
            requirements = ""
            if metadata['export_format'] == 'onnx':
                requirements = "onnxruntime>=1.15.0\nnumpy>=1.21.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements = "torch\nnumpy>=1.21.0\n"
            elif metadata['export_format'] == 'statedict':
                requirements = "torch\nnumpy>=1.21.0\n" # Will also require organism_brain class definition

            zf.writestr("requirements.txt", requirements)

            # 8. README
            readme_content = f"""```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        🦋  THE BUTTERFLY SYSTEM - COMPILED AGENT  🦋          ║
    ║                                                               ║
    ║           Quantum-Genetic Consciousness Snapshot              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

# Agent Archive: `{capsule.organism_id[:16]}...`

> **Exported from The Butterfly System**  
> A living AI organism, crystallized into portable intelligence.

---

## 🧬 Agent Profile

| Property | Value |
|----------|-------|
| **Organism ID** | `{capsule.organism_id}` |
| **Fitness Score** | `{metadata['organism_core']['fitness']:.6f}` {('⭐' * min(5, int(metadata['organism_core']['fitness'] * 5))) if metadata['organism_core']['fitness'] else 'N/A'} |
| **Generation** | `{metadata['organism_core'].get('generation', 'unknown')}` |
| **Age** | `{metadata['organism_core'].get('organism_age', 'unknown')}` cycles |
| **Neural Input** | `{metadata['neural_network']['architecture'].get('input_size', 'unknown')}` dimensions |
| **Action Space** | `{metadata['neural_network']['architecture'].get('output_size', 'unknown')}` actions |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Exported** | `{metadata['export_timestamp']}` |

---

## 📦 Archive Contents

```
agent_{capsule.organism_id[:8]}.zip/
├── 🧠 brain.{metadata['export_format']}              # Neural network weights
├── 📋 metadata.json                # Complete organism state
├── 🧬 genotype.json                # Genetic blueprint
├── ⚙️  atomic_config.json          # Optimized configuration
├── 🗣️  atomic_language.json        # Linguistic knowledge
├── 🐍 run_agent.py                 # Standalone inference script
├── 📦 requirements.txt             # Python dependencies
└── 📖 README.md                    # This file
```

---

## 🚀 Quick Start

### 1. Extract Archive
```bash
unzip agent_{capsule.organism_id[:8]}.zip
cd agent_{capsule.organism_id[:8]}
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Agent
```bash
python run_agent.py
```

The agent will load its neural network and demonstrate decision-making using dummy sensory input.

---

## 🔬 Technical Specifications

### Neural Architecture
- **Model Type**: Deep Q-Network (DQN) with multi-head architecture
- **Brain Dimensions**: `{metadata['neural_network']['architecture'].get('input_size', 'unknown')}` → `{metadata['neural_network']['architecture'].get('hidden_size', 'unknown')}` → `{metadata['neural_network']['architecture'].get('output_size', 'unknown')}`
- **Activation**: `{metadata['neural_network']['architecture'].get('activation', 'ReLU')}`
- **Language Head**: {'✅ Enabled' if metadata['neural_network']['architecture'].get('use_language_head') else '❌ Disabled'}
- **Concept Head**: {'✅ Enabled' if metadata['neural_network']['architecture'].get('use_concept_head') else '❌ Disabled'}
- **Attention Mechanism**: {'✅ Enabled' if metadata['neural_network']['architecture'].get('use_attention') else '❌ Disabled'}

### Genetic Traits
- **Gene Length**: `{len(capsule.traits.genotype.genes) if capsule.traits else 'unknown'}` bits
- **Development Stage**: `{capsule.traits.phenotype.development_stage if capsule.traits else 'unknown'}`
- **Trait Count**: `{len(capsule.traits.phenotype.traits) if capsule.traits else 0}` expressed traits

---

## 🎯 Action Space

The agent can produce the following actions:

| Index | Action | Description |
|-------|--------|-------------|
| 0 | `move` | Locomotion through environment |
| 1 | `cooperate` | Collaborative behavior with other agents |
| 2 | `compete` | Competitive resource acquisition |
| 3 | `rest` | Energy conservation mode |
| 4 | `reproduce` | Genetic propagation |
| 5 | `isolate` | Social withdrawal |

---

## 💻 Integration Example

```python
import numpy as np
from run_agent import AgentRunner

# Initialize agent
agent = AgentRunner()

# Prepare sensory input (replace with real sensor data)
state = np.array([
    0.5,   # fitness
    0.3,   # resources
    0.7,   # social connections
    # ... (input_dim={metadata['neural_network']['architecture'].get('input_size', 'unknown')} total)
])

# Get agent decision
action = agent.decide_action(state)
print(f"Agent decision: {{action}}")  # e.g., "cooperate"
```

---

## 🧪 Deployment Options

### Option 1: Standalone Script
Run `run_agent.py` directly for quick testing and demos.

### Option 2: Import as Module
```python
from run_agent import AgentRunner
agent = AgentRunner("brain.{metadata['export_format']}", "metadata.json")
```

### Option 3: Production Integration
- Load `brain.{metadata['export_format']}` with ONNX Runtime or PyTorch
- Parse `metadata.json` for architecture details
- Integrate into your inference pipeline

---

## 📊 Metadata Schema

The `metadata.json` contains:
- **organism_core**: ID, fitness, age, generation, parent lineage
- **neural_network**: Architecture specs, parameter counts, device info
- **genotype**: Raw genetic data, mutation history
- **phenotype**: Expressed traits, development stage
- **environment_context**: Environmental factors during capture
- **causation_trace**: Key events that shaped this organism
- **export_options**: Format, timestamp, compatibility

---

## 🛠️ Troubleshooting

### Import Errors
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt --upgrade
```

### ONNX Runtime Issues
```bash
# For GPU acceleration (optional)
pip install onnxruntime-gpu
```

### State Dict Loading (if using state_dict format)
You'll need the `OrganismBrain` class definition from the Butterfly System source code.

---

## 🔗 About The Butterfly System

This agent was born in **The Butterfly System**, a quantum-genetic consciousness simulation where AI organisms evolve, learn, and develop emergent intelligence through:

- **Quantum-Genetic Evolution**: Probabilistic gene expression and trait inheritance
- **Neural Learning**: Deep Q-Network with experience replay and dual inheritance
- **Social Dynamics**: Alliances, competition, and emergent cooperation
- **Language Acquisition**: Multi-dimensional linguistic awareness and vocabulary learning
- **Causation Tracking**: Full lineage and event history for explainability

**Learn More**: https://github.com/Yufok1/Convergence_Engine

---

## 📜 License & Attribution

This agent and its neural weights are exported from **The Butterfly System**.

**Attribution**: If you use this agent in research or production, please cite:
```
Butterfly System - Quantum-Genetic Consciousness Simulation
Agent ID: {capsule.organism_id}
Export Date: {metadata['export_timestamp']}
```

---

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║             Ready for deployment. Let it thrive.              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```
"""
            zf.writestr("README.md", readme_content)

        archive_buffer.seek(0)
        return archive_buffer

    def _create_ensemble_archive(self,
                                 model_buffer: BytesIO,
                                 metadata: Dict[str, Any],
                                 runner_script: str) -> BytesIO:
        """Package ensemble components into a ZIP archive (no single capsule).
        """
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Neural model
            model_buffer.seek(0)
            zf.writestr(f"brain.{metadata['export_format']}", model_buffer.read())

            # Metadata
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Runner
            zf.writestr("run_agent.py", runner_script)

            # Requirements
            requirements = ""
            if metadata['export_format'] == 'onnx':
                requirements = "onnxruntime>=1.15.0\nnumpy>=1.21.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements = "torch\nnumpy>=1.21.0\n"
            zf.writestr("requirements.txt", requirements)

            member_count = len(metadata.get('ensemble', {}).get('members', []))
            member_ids = [m['organism_id'] for m in metadata.get('ensemble', {}).get('members', [])]
            
            readme = f"""```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     🦋🦋  THE BUTTERFLY SYSTEM - ENSEMBLE AGENT  🦋🦋        ║
    ║                                                               ║
    ║              Multi-Organism Collective Intelligence           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

# Ensemble Agent Archive: `{member_count} Organisms`

> **Exported from The Butterfly System**  
> A collective of evolved AI organisms, unified into a single decision-making ensemble.

---

## 🌐 Ensemble Profile

| Property | Value |
|----------|-------|
| **Member Count** | `{member_count}` organisms |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Max Input Dim** | `{metadata.get('ensemble', {}).get('max_input_dim', 'unknown')}` dimensions |
| **Exported** | `{metadata['export_timestamp']}` |
| **Architecture** | Multi-organism wrapper with parallel inference |

---

## 👥 Ensemble Members

{chr(10).join([f"- `{mid[:16]}...` (Organism {i+1}/{member_count})" for i, mid in enumerate(member_ids)])}

---

## 📦 Archive Contents

```
ensemble_{metadata['export_timestamp'][:10]}.zip/
├── 🧠 brain.{metadata['export_format']}              # Ensemble neural network
├── 📋 metadata.json                # Ensemble configuration
├── 🐍 run_agent.py                 # Multi-organism runner
├── 📦 requirements.txt             # Python dependencies
└── 📖 README.md                    # This file
```

---

## 🚀 Quick Start

### 1. Extract Archive
```bash
unzip ensemble_*.zip
cd ensemble_*/
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Ensemble
```bash
python run_agent.py
```

The ensemble will load all member networks and produce collective decisions.

---

## 💻 Usage Example

```python
from run_agent import EnsembleRunner
import numpy as np

# Initialize ensemble
ensemble = EnsembleRunner()

# Prepare input (max_input_dim={metadata.get('ensemble', {}).get('max_input_dim', 'unknown')})
state = np.random.rand(ensemble.input_dim)

# Get collective decisions from all members
decisions = ensemble.decide_actions(state)

# decisions = {{'organism_1': 'cooperate', 'organism_2': 'move', ...}}
print(decisions)
```

---

## 🎯 Ensemble Decision Making

The ensemble returns a **dictionary of decisions**, one per member organism:

```python
{{
    'organism_id_1': 'move',
    'organism_id_2': 'cooperate',
    'organism_id_3': 'rest',
    # ... (one per member)
}}
```

Each organism independently processes the input and produces its own action.

---

## 🔬 Technical Details

### Architecture
- **Type**: Multi-organism wrapper
- **Inference**: Parallel forward passes through all member brains
- **Aggregation**: Individual decisions (no voting/averaging)
- **Format**: {metadata['export_format'].upper()}

### Action Space (per organism)
- `move` - Locomotion
- `cooperate` - Collaborative behavior
- `compete` - Resource competition
- `rest` - Energy conservation
- `reproduce` - Genetic propagation
- `isolate` - Social withdrawal

---

## 🛠️ Deployment

### Standalone Testing
```bash
python run_agent.py
```

### Import as Module
```python
from run_agent import EnsembleRunner
ensemble = EnsembleRunner()
```

### Production Integration
Load the ensemble model directly with ONNX Runtime or PyTorch for high-performance inference.

---

## 🧪 Advanced Usage

### Custom Input
```python
# Prepare real sensor data
state_vector = np.array([...])  # Match max_input_dim

# Get decisions
decisions = ensemble.decide_actions(state_vector)

# Process collective output
for organism_id, action in decisions.items():
    print(f"{{organism_id[:8]}}... decided: {{action}}")
```

---

## 🔗 About The Butterfly System

This ensemble was cultivated in **The Butterfly System**, where AI organisms evolve through:

- **Quantum-Genetic Evolution**: Probabilistic inheritance and trait expression
- **Neural Learning**: DQN with experience replay
- **Social Dynamics**: Alliances, warfare, and cooperation
- **Language Acquisition**: Vocabulary learning and semantic understanding
- **Collective Intelligence**: Emergent group behaviors

**Learn More**: https://github.com/Yufok1/Convergence_Engine

---

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         {member_count} minds, one purpose. Deploy the swarm.              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```
"""
            zf.writestr("README.md", readme)

        archive_buffer.seek(0)
        return archive_buffer

    def _generate_ensemble_runner_script(self, export_format: str, metadata: Dict[str, Any]) -> str:
        action_map_str = json.dumps(ACTION_MAP)
        script = """
import onnxruntime
import numpy as np
import json
import os
import time

ACTION_MAP = {action_map_str}

class EnsembleRunner:
    def __init__(self, model_filename="{model_filename}", metadata_filename="metadata.json"):
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        if not os.path.exists(self.model_filename):
            raise FileNotFoundError(f"Model file not found: {{self.model_filename}}")
        if not os.path.exists(self.metadata_filename):
            raise FileNotFoundError(f"Metadata file not found: {{self.metadata_filename}}")

        with open(self.metadata_filename, "r") as f:
            self.metadata = json.load(f)

        ensemble = self.metadata.get('ensemble', {{}})
        members = ensemble.get('members', [])
        self.member_names = [m['name'] for m in members]
        self.input_dim = ensemble.get('max_input_dim', 0)

        print("\\n--- Ensemble Loaded ---")
        print(f"Members: {{', '.join(self.member_names)}}")
        print(f"Input Dim: {{self.input_dim}}")
        print(f"Exported: {{self.metadata['export_timestamp']}}")
        print("-----------------------\\n")

        self.session = None
        if "{export_format}" == "onnx":
            providers = onnxruntime.get_available_providers()
            if 'CUDAExecutionProvider' in providers:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CUDAExecutionProvider'])
                print("Using CUDAExecutionProvider for ONNX inference.")
            else:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CPUExecutionProvider'])
                print("Using CPUExecutionProvider for ONNX inference.")
        elif "{export_format}" == "torchscript":
            import torch
            self.model = torch.jit.load(self.model_filename)
            self.model.eval()
            print("TorchScript ensemble loaded.")

    def decide_actions(self, state_vector):
        if len(state_vector) != self.input_dim:
            raise ValueError(f"State vector must have {{self.input_dim}} dimensions, got {{len(state_vector)}}")

        if "{export_format}" == "onnx":
            state_array = np.array(state_vector, dtype=np.float32).reshape(1, -1)
            inputs = {{self.session.get_inputs()[0].name: state_array}}
            outputs = self.session.run(None, inputs)
            # outputs is a list; align to member order
            decisions = {{}}
            for name, out in zip(self.member_names, outputs):
                idx = int(np.argmax(out))
                decisions[name] = ACTION_MAP.get(idx, str(idx))
            return decisions
        elif "{export_format}" == "torchscript":
            import torch
            state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                outs = self.model(state_tensor)
            decisions = {{}}
            for name, out in zip(self.member_names, outs):
                idx = int(torch.argmax(out).item())
                decisions[name] = ACTION_MAP.get(idx, str(idx))
            return decisions
        else:
            raise ValueError(f"Unsupported export format: {{self.metadata['export_format']}}")

if __name__ == '__main__':
    runner = EnsembleRunner()
    dummy_state = np.random.rand(runner.input_dim)
    decisions = runner.decide_actions(dummy_state)
    print("Decisions:", decisions)
"""
        return script.format(action_map_str=action_map_str,
                             model_filename=f"brain.{export_format}",
                             export_format=export_format)

    def compile_capsules_to_ensemble(self,
                                     capsules: List['OrganismCapsule'],
                                     export_format: str = 'onnx',
                                     example_state: Any = None) -> BytesIO:
        """Compile multiple capsules into a single ensemble model archive.

        All brains receive the same state vector (max input dim); per-brain
        slicing/padding is handled inside the wrapper for compatibility.
        """
        if export_format not in ['onnx', 'torchscript']:
            raise ValueError("Ensemble export supports 'onnx' and 'torchscript' only.")

        # Reconstruct brains
        brains = []
        names = []
        members_meta = []
        for cap in capsules:
            b = self._reconstruct_brain_from_capsule(cap)
            brains.append(b)
            name = str(cap.organism_id)
            names.append(name)
            members_meta.append({
                'organism_id': name,
                'name': name,
                'input_dim': b.input_dim,
                'output_dim': b.output_dim
            })

        if not brains:
            raise ValueError("No capsules provided for ensemble export.")

        wrapper = self.MultiOrganismWrapper(brains, names)
        wrapper.eval()  # Disable dropout for deterministic tracing

        # Prepare deterministic input
        if example_state is not None:
            try:
                arr = np.asarray(example_state, dtype=np.float32).reshape(1, -1)
                if arr.shape[1] < wrapper.max_input_dim:
                    pad = np.zeros((1, wrapper.max_input_dim - arr.shape[1]), dtype=np.float32)
                    arr = np.concatenate([arr, pad], axis=1)
                elif arr.shape[1] > wrapper.max_input_dim:
                    arr = arr[:, :wrapper.max_input_dim]
                dummy_input = torch.from_numpy(arr)
            except Exception:
                dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32)
        else:
            dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32)

        # Export
        model_buffer = BytesIO()
        chosen_format = export_format
        if export_format == 'onnx':
            try:
                # Multiple outputs with names per member
                output_names = [f"out_{n}" for n in names]
                torch.onnx.export(
                    wrapper,
                    dummy_input,
                    model_buffer,
                    input_names=['input'],
                    output_names=output_names,
                    dynamic_axes={'input': {0: 'batch_size'}},
                    opset_version=11
                )
            except Exception as e:
                msg = str(e)
                if 'onnxscript' in msg.lower() or 'onnx' in msg.lower():
                    # Fallback to TorchScript trace (not script - script fails on OrganismBrain)
                    model_buffer = BytesIO()
                    traced = torch.jit.trace(wrapper, (dummy_input,))
                    torch.jit.save(traced, model_buffer)
                    model_buffer.seek(0)
                    chosen_format = 'torchscript'
                else:
                    raise
        else:
            # Use trace instead of script - script fails on OrganismBrain's complex control flow
            traced = torch.jit.trace(wrapper, (dummy_input,))
            torch.jit.save(traced, model_buffer)
            model_buffer.seek(0)

        # Metadata
        metadata = {
            'export_timestamp': datetime.datetime.now().isoformat(),
            'export_format': chosen_format,
            'ensemble': {
                'members': members_meta,
                'max_input_dim': wrapper.max_input_dim
            },
            'runtime_dependencies': {
                'onnxruntime': onnxruntime.__version__ if ONNX_AVAILABLE else 'not installed',
                'numpy': np.__version__,
                'python': sys.version.split(' ')[0]
            }
        }

        # Runner
        runner_script = self._generate_ensemble_runner_script(chosen_format, metadata)

        # Package
        return self._create_ensemble_archive(model_buffer, metadata, runner_script)

    def compile_capsule_to_agent(self, 
                                 capsule: OrganismCapsule, 
                                 export_format: str = 'onnx',
                                 include_history: bool = True,
                                 example_state: Any = None) -> BytesIO:
        """
        Compiles an OrganismCapsule into a deployable agent archive (ZIP file).
        
        Args:
            capsule: The OrganismCapsule object containing the agent's state.
            export_format: The format for the neural network model ('onnx', 'torchscript', 'statedict').
            include_history: If True, includes more detailed history/causation data.
            
        Returns:
            BytesIO: A memory buffer containing the ZIP archive.
        """
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}. Supported: {self.supported_formats}")

        logger.info(f"Compiling organism {capsule.organism_id} to {export_format.upper()} format.")
        
        # 1. Reconstruct the neural brain
        brain = self._reconstruct_brain_from_capsule(capsule)
        
        # 2. Prepare deterministic input for ONNX export (and TorchScript tracing if used)
        if example_state is not None:
            try:
                arr = np.asarray(example_state, dtype=np.float32)
                arr = arr.reshape(1, -1)
                # Pad or truncate to match expected input_dim
                if arr.shape[1] < brain.input_dim:
                    pad = np.zeros((1, brain.input_dim - arr.shape[1]), dtype=np.float32)
                    arr = np.concatenate([arr, pad], axis=1)
                elif arr.shape[1] > brain.input_dim:
                    arr = arr[:, :brain.input_dim]
                dummy_input = torch.from_numpy(arr)
            except Exception:
                dummy_input = torch.zeros(1, brain.input_dim, dtype=torch.float32)
        else:
            dummy_input = torch.zeros(1, brain.input_dim, dtype=torch.float32)
        
        # 3. Export the brain to the specified format
        model_buffer = BytesIO()
        chosen_format = export_format
        if export_format == 'onnx':
            try:
                self._export_onnx(brain, dummy_input, model_buffer)
            except Exception as e:
                # Graceful fallback: if ONNX dependencies missing, fallback to TorchScript
                if 'onnxscript' in str(e).lower() or 'onnx' in str(e).lower():
                    logger.warning("ONNX export failed due to missing dependencies; falling back to TorchScript export.")
                    model_buffer = BytesIO()
                    self._export_torchscript(brain, model_buffer)
                    chosen_format = 'torchscript'
                else:
                    raise
        elif export_format == 'torchscript':
            self._export_torchscript(brain, model_buffer)
        elif export_format == 'statedict':
            self._export_statedict(brain, model_buffer)
        
        # 4. Create rich metadata
        metadata = self._create_rich_metadata(capsule)
        metadata['export_format'] = chosen_format # Add (possibly updated) export format to metadata
        
        # 5. Generate runner script
        runner_script = self._generate_runner_script(chosen_format, metadata)
        
        # 6. Package into ZIP archive
        return self._create_agent_archive(model_buffer, metadata, runner_script, capsule)

if __name__ == '__main__':
    # This block is for testing the AgentCompiler in isolation.
    # It requires a dummy OrganismCapsule and OrganismBrain setup.
    
    
    # Setup dummy brain and organism for testing
    dummy_brain_arch = {
        'input_dim': 24,
        'hidden_dim': 64,
        'output_dim': 6,
        'activation': 'relu',
        'dropout': 0.1,
        'use_attention': False,
        'num_attention_heads': 4,
        'attention_dim': 64,
        'vocab_size': 50000,
        'use_language_head': False
    }
    dummy_brain = OrganismBrain(**dummy_brain_arch)
    
    # Save dummy brain state_dict to BytesIO
    dummy_state_dict_buffer = BytesIO()
    torch.save(dummy_brain.state_dict(), dummy_state_dict_buffer)
    dummy_state_dict_buffer.seek(0)
    dummy_state_dict_b64 = base64.b64encode(dummy_state_dict_buffer.read()).decode('utf-8')
    
    dummy_capsule = OrganismCapsule(
        organism_id="test_org_001",
        capsule_id=f"cap_{uuid.uuid4()}",
        version="1.0",
        timestamp=datetime.datetime.now().isoformat(),
        neural_network_state={
            'architecture': dummy_brain_arch,
            'state_dict_b64': dummy_state_dict_b64,
            'device': 'cpu',
            'training_steps': 100,
            'avg_loss': 0.05
        },
        genotype_hash_state={'dna': 'ATGC...'}, 
        phenotype_summary={'size': 10, 'color': 'red'},
        fitness_trajectory=[{'fitness': 0.5, 'generation': 0}, {'fitness': 0.6, 'generation': 10}],
        age=10,
        atomic_language_state={'concept_count': 50, 'dialect_signature': [0.1, 0.2]},
        atomic_config_state={'neural': {'lr': 0.001}},
        highlander_metadata={'wins': 5, 'losses': 2},
        social_connections={'neighbors': 3},
        environment_context={'resource_density': 0.7},
        causation_digest={'events': [{'id': 'evt_1', 'type': 'born'}]},
        file_path="dummy_path.json"
    )
    
    compiler = AgentCompiler()
    
    # Test ONNX export
    try:
        onnx_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='onnx')
        with open("test_agent_onnx.zip", "wb") as f:
            f.write(onnx_archive.read())
        print("Generated test_agent_onnx.zip")
    except Exception as e:
        print(f"ONNX compilation failed: {e}")
        
    # Test TorchScript export
    try:
        ts_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='torchscript')
        with open("test_agent_torchscript.zip", "wb") as f:
            f.write(ts_archive.read())
        print("Generated test_agent_torchscript.zip")
    except Exception as e:
        print(f"TorchScript compilation failed: {e}")
        
    # Test StateDict export
    try:
        sd_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='statedict')
        with open("test_agent_statedict.zip", "wb") as f:
            f.write(sd_archive.read())
        print("Generated test_agent_statedict.zip")
    except Exception as e:
        print(f"StateDict compilation failed: {e}")
