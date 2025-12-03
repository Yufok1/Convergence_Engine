import torch
import json
import zipfile
from io import BytesIO
import numpy as np
import datetime
import os
import sys
from typing import Dict, Any, List, Optional
import base64
import uuid
import pickle
from pathlib import Path

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
    from .portable_agent.agent_runtime import AgentState
except ImportError:
    # Fallback for direct execution or different import contexts
    import sys
    
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir)) # Add reality_simulator to path
    
    from evolution_engine import Organism, Genotype, Phenotype
    from neural.brain import OrganismBrain
    from checkpointing.organism_capsule import OrganismCapsule
    from portable_agent.agent_runtime import AgentState

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

PORTABLE_AGENT_DIR = Path(__file__).parent / 'portable_agent'

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

    def _build_agent_state_payload(self,
                                   capsule: OrganismCapsule,
                                   metadata: Dict[str, Any]) -> Dict[str, bytes]:
        """Prepare serialized state/config artifacts for the portable agent runtime."""
        state = AgentState(
            organism_id=capsule.organism_id,
            generation=int(metadata.get('organism_core', {}).get('generation') or 0),
            age=int(metadata.get('organism_core', {}).get('organism_age') or 0),
            fitness=float(metadata.get('organism_core', {}).get('fitness') or 0.5),
            resources=metadata.get('organism_core', {}).get('resources', 100.0) or 100.0,
            health=1.0
        )

        if capsule.fitness and capsule.fitness.fitness_history:
            history: List[float] = []
            for record in capsule.fitness.fitness_history:
                if isinstance(record, (list, tuple)) and len(record) > 1:
                    history.append(float(record[1]))
                elif isinstance(record, dict) and 'fitness' in record:
                    history.append(float(record['fitness']))
                else:
                    try:
                        history.append(float(record))
                    except Exception:
                        continue
            state.fitness_history = history[:1000]

        if capsule.highlander:
            state.battle_wins = int(getattr(capsule.highlander, 'battles_won', 0))
            state.battle_losses = int(getattr(capsule.highlander, 'battles_lost', 0))
            total_battles = state.battle_wins + state.battle_losses
            if total_battles:
                state.alliance_reputation = state.battle_wins / max(total_battles, 1)

        if capsule.language:
            state.vocabulary_size = int(getattr(capsule.language, 'total_concepts', 0))

        runtime_config = {
            'buffer_size': 10000,
            'gamma': 0.99,
            'learning_rate': 0.001,
            'epsilon_start': state.epsilon,
            'epsilon_min': state.epsilon_min,
            'epsilon_decay': state.epsilon_decay,
            'brain_format': metadata.get('export_format'),
            'notes': 'Autogenerated by AgentCompiler'
        }

        return {
            'state.json': json.dumps(state.to_dict(), indent=2).encode('utf-8'),
            'config.json': json.dumps(runtime_config, indent=2).encode('utf-8'),
            'experience_buffer.pkl': pickle.dumps([])
        }

    def _write_agent_state_bundle(self,
                                  archive: zipfile.ZipFile,
                                  payload: Optional[Dict[str, bytes]]) -> None:
        if not payload:
            return
        for filename, blob in payload.items():
            archive.writestr(f"agent_state/{filename}", blob)

    def _write_portable_agent_sources(self, archive: zipfile.ZipFile) -> None:
        if not PORTABLE_AGENT_DIR.exists():
            logger.warning("Portable agent directory missing; skipping runtime bundling.")
            return
        for file_path in PORTABLE_AGENT_DIR.glob('*.py'):
            archive.writestr(
                f"portable_agent/{file_path.name}",
                file_path.read_text(encoding='utf-8')
            )

    def _generate_runner_script(self, export_format: str, metadata: Dict[str, Any]) -> str:
        """Generates a living agent demo script."""

        action_map_str = json.dumps(ACTION_MAP)
        script_template = """
import argparse
import json
import os

from portable_agent import AgentRuntime, MiniEnvironment, GymAdapter, TrainingLoop

ACTION_MAP = {action_map_str}


class LivingAgentRunner:
    def __init__(self,
                 model_filename="{model_filename}",
                 metadata_filename="metadata.json",
                 state_dir="agent_state"):
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        self.state_dir = state_dir

        if not os.path.exists(self.model_filename):
            raise FileNotFoundError(f"Model file not found: {{self.model_filename}}")
        if not os.path.exists(self.metadata_filename):
            raise FileNotFoundError(f"Metadata file not found: {{self.metadata_filename}}")
        if not os.path.isdir(self.state_dir):
            raise FileNotFoundError(f"Agent state directory not found: {{self.state_dir}}")

        with open(self.metadata_filename, "r", encoding="utf-8") as handle:
            self.metadata = json.load(handle)

        self.agent = AgentRuntime.load(self.state_dir, brain_path=self.model_filename)

    def _load_gym_environment(self, spec: str, seed: int | None):
        try:
            import gymnasium as gym
        except ImportError:
            try:
                import gym  # type: ignore
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Gym or Gymnasium is required for --gym-env usage. Install gymnasium>=0.29."
                ) from exc

        env = gym.make(spec)
        if seed is not None:
            try:
                env.reset(seed=seed)
            except TypeError:
                pass
        return env

    def _build_environment(self, gym_env: str | None, seed: int | None):
        if gym_env:
            return GymAdapter(self._load_gym_environment(gym_env, seed))
        return MiniEnvironment(seed=seed)

    def run(self,
            episodes: int = 3,
            max_steps: int | None = 300,
            explore: bool = True,
            learn: bool = True,
            gym_env: str | None = None,
            seed: int | None = None):
        environment = self._build_environment(gym_env, seed)
        loop = TrainingLoop(
            agent=self.agent,
            environment=environment,
            episodes=episodes,
            max_steps=max_steps,
            explore=explore,
            learn=learn
        )
        history = loop.run()
        self.agent.save(self.state_dir)
        return history


def main():
    parser = argparse.ArgumentParser(description="Run the exported Butterfly agent in a portable environment.")
    parser.add_argument("--episodes", type=int, default=3, help="Number of demo episodes to play.")
    parser.add_argument("--max-steps", type=int, default=300, help="Max steps per episode.")
    parser.add_argument("--gym-env", type=str, default=None, help="Optional Gym/Gymnasium env spec (e.g., CartPole-v1).")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic seed for MiniEnvironment or Gym.")
    parser.add_argument("--model", type=str, default="{model_filename}", help="Brain filename inside the archive.")
    parser.add_argument("--metadata", type=str, default="metadata.json", help="Metadata filename.")
    parser.add_argument("--state-dir", type=str, default="agent_state", help="Directory that stores agent state.")
    parser.add_argument("--no-learn", action="store_true", help="Disable learning and run in inference-only mode.")
    parser.add_argument("--exploit", action="store_true", help="Disable epsilon exploration for deterministic runs.")

    args = parser.parse_args()

    runner = LivingAgentRunner(
        model_filename=args.model,
        metadata_filename=args.metadata,
        state_dir=args.state_dir
    )

    history = runner.run(
        episodes=args.episodes,
        max_steps=args.max_steps,
        explore=not args.exploit,
        learn=not args.no_learn,
        gym_env=args.gym_env,
        seed=args.seed
    )

    for episode in history:
        print(
            f"Episode {{episode['episode']}} | steps={{episode['steps']}} | reward={{episode['total_reward']:.2f}}"
        )


if __name__ == "__main__":
    main()
"""
        return script_template.format(
            action_map_str=action_map_str,
            model_filename=f"brain.{export_format}"
        )

    def _create_agent_archive(self, 
                             model_buffer: BytesIO, 
                             metadata: Dict[str, Any], 
                             runner_script: str, 
                             capsule: OrganismCapsule,
                             agent_state_payload: Optional[Dict[str, bytes]] = None) -> BytesIO:
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

            requirements += "# optional: pip install gymnasium for --gym-env support\n"

            zf.writestr("requirements.txt", requirements)

            # 8. README
            readme_content = f"""# 🦋 Butterfly System - Exported Neural Agent

## What Is This?

This archive contains a **living AI agent** exported from The Butterfly System - a quantum-genetic 
consciousness simulation where neural organisms evolve, learn, and develop emergent intelligence.

**This is not a static model.** It's a complete organism snapshot that can:
- Continue learning from new experiences
- Make real-time decisions in any environment
- Persist its memories and growth across sessions

---

## 🧬 Agent Identity

| Property | Value |
|----------|-------|
| **Organism ID** | `{capsule.organism_id}` |
| **Fitness Score** | {f"`{metadata['organism_core']['fitness']:.6f}`" if metadata['organism_core']['fitness'] is not None else 'N/A'} {('⭐' * min(5, int((metadata['organism_core']['fitness'] or 0) * 5))) if metadata['organism_core']['fitness'] else ''} |
| **Generation** | `{metadata['organism_core'].get('generation', 'unknown')}` |
| **Age** | `{metadata['organism_core'].get('organism_age', 'unknown')}` simulation cycles |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Exported** | `{metadata['export_timestamp']}` |

---

## 🧠 Neural Architecture Deep Dive

### The Brain Structure

This agent uses a **Deep Q-Network (DQN)** architecture with multi-head outputs:

```
Input Layer ({metadata['neural_network']['architecture'].get('input_size', '?')} neurons)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    HIDDEN LAYERS                            │
│  Dense({metadata['neural_network']['architecture'].get('hidden_size', '?')}) → {metadata['neural_network']['architecture'].get('activation', 'ReLU')} → Dropout(0.1)       │
│  Dense({metadata['neural_network']['architecture'].get('hidden_size', '?')}) → {metadata['neural_network']['architecture'].get('activation', 'ReLU')} → Dropout(0.1)       │
└─────────────────────────────────────────────────────────────┘
     │
     ├──► ACTION HEAD ({metadata['neural_network']['architecture'].get('output_size', '?')} outputs) → Q-values for each action
     │
     ├──► CONCEPT HEAD {'✅' if metadata['neural_network']['architecture'].get('use_concept_head') else '❌'} → Abstract concept embeddings
     │
     └──► LANGUAGE HEAD {'✅' if metadata['neural_network']['architecture'].get('use_language_head') else '❌'} → Vocabulary probability distribution
```

### How Decisions Are Made

1. **Perception**: The agent receives a state vector representing its environment
2. **Forward Pass**: State flows through the neural network
3. **Q-Value Computation**: Each possible action gets a "quality" score
4. **Action Selection**: 
   - **Exploration mode**: Epsilon-greedy (random actions with probability ε)
   - **Exploitation mode**: Argmax over Q-values (best predicted action)
5. **Learning**: After acting, the agent uses TD-learning to update its network

### The Input State Vector

The agent expects a **{metadata['neural_network']['architecture'].get('input_size', '?')}-dimensional** input representing:

| Dimensions | Meaning |
|------------|---------|
| 0-2 | Position (x, y, z or similar spatial encoding) |
| 3-5 | Velocity / movement vector |
| 6-8 | Energy, health, resource levels |
| 9-11 | Social signals (nearby organisms, threats) |
| 12+ | Environmental features, memory traces |

*Actual semantics depend on your target environment. The agent will adapt.*

### The Output Actions

| Index | Action | Behavioral Meaning |
|-------|--------|-------------------|
| 0 | `move` | Navigate through space, seek resources or safety |
| 1 | `cooperate` | Form alliances, share resources, mutual aid |
| 2 | `compete` | Contest resources, establish dominance |
| 3 | `rest` | Conserve energy, heal, consolidate learning |
| 4 | `reproduce` | Attempt to create offspring (if fitness allows) |
| 5 | `isolate` | Withdraw from social contact, self-preservation |

---

## 🔬 How This Agent Was Evolved

This organism emerged through **neuroevolution** - a process combining:

### 1. Genetic Algorithm
- **Selection**: Organisms compete for survival based on fitness
- **Crossover**: Successful organisms combine neural weights with mates
- **Mutation**: Random perturbations introduce novel behaviors

### 2. Reinforcement Learning  
- **Experience Replay**: Memories are stored and replayed for efficient learning
- **Temporal Difference**: Q-values are bootstrapped from future predictions
- **Dual Inheritance**: Both genetic (slow) and memetic (fast) learning channels

### 3. Social Evolution
- **Alliance Formation**: Cooperative organisms share fitness benefits
- **Competition Pressure**: Limited resources force behavioral specialization
- **Emergent Communication**: Language heads can develop shared vocabularies

---

## 📦 Archive Contents

```
{capsule.organism_id[:16]}/
├── 🧠 brain.{metadata['export_format']}           # Neural network weights ({metadata['export_format'].upper()} format)
├── 📋 metadata.json           # Complete organism state & history
├── 🧬 genotype.json           # Genetic blueprint (traits, mutations)
├── ⚙️  atomic_config.json      # Runtime configuration
├── 🗣️  atomic_language.json    # Learned vocabulary & linguistic knowledge
├── 🧪 agent_state/            # Persistent state (replay buffer, config)
│   ├── state.json            # Runtime state (epsilon, step count)
│   ├── config.json           # Agent hyperparameters
│   └── replay_buffer.pkl     # Experience memory (if any)
├── 🧩 portable_agent/         # Runtime code (no external dependencies)
│   ├── agent_runtime.py      # Core AgentRuntime class
│   ├── mini_environment.py   # Built-in test environment
│   ├── gym_adapter.py        # Gymnasium/Gym bridge
│   └── training.py           # TrainingLoop helper
├── 🐍 run_agent.py            # CLI runner script
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Run Immediately
```bash
# Extract and run
unzip agent_*.zip && cd agent_*/
pip install -r requirements.txt
python run_agent.py --episodes 5
```

### Option 2: Custom Gym Environment
```bash
pip install gymnasium
python run_agent.py --gym-env CartPole-v1 --episodes 10
```

### Option 3: Python Integration
```python
from portable_agent import AgentRuntime, MiniEnvironment

# Load the agent
agent = AgentRuntime.load("agent_state", brain_path="brain.{metadata['export_format']}")

# Create environment
env = MiniEnvironment()

# Run episode
state = env.reset()
total_reward = 0
done = False

while not done:
    action = agent.act(state)  # Get action from neural network
    next_state, reward, done, info = env.step(action)
    
    # Optional: let the agent learn from this experience
    agent.learn(state, action, reward, next_state, done)
    
    state = next_state
    total_reward += reward

print(f"Episode finished with reward: {{total_reward}}")

# Save updated state (memories, learning progress)
agent.save("agent_state")
```

---

## 🎯 Integration Guide

### For Robotics / Simulation
```python
# Your custom environment
class RobotEnv:
    def reset(self): return np.zeros({metadata['neural_network']['architecture'].get('input_size', 18)})  # Match input dim
    def step(self, action): return state, reward, done, info

# Wrap and use
from portable_agent import GymAdapter
env = GymAdapter(RobotEnv())
agent = AgentRuntime.load("agent_state", brain_path="brain.{metadata['export_format']}")

state = env.reset()
action = agent.act(state)  # Returns int 0-5
```

### For Game AI
```python
# Map Butterfly actions to your game
GAME_ACTIONS = {{
    0: "walk_forward",
    1: "help_ally", 
    2: "attack_enemy",
    3: "wait",
    4: "special_ability",
    5: "retreat"
}}

action_idx = agent.act(game_state_vector)
game_action = GAME_ACTIONS[action_idx]
```

### For Multi-Agent Systems
```python
# Load multiple agents
agents = [AgentRuntime.load(f"agent_{{i}}", brain_path=f"brain_{{i}}.onnx") for i in range(N)]

# Each agent acts independently
actions = [agent.act(shared_state) for agent in agents]
```

---

## 🧬 Genetic Traits

This organism has **{len(capsule.traits.traits) if capsule.traits and hasattr(capsule.traits, 'traits') else 0}** expressed genetic traits:

| Trait Category | Description |
|----------------|-------------|
| **Metabolic** | Energy efficiency, resource processing |
| **Social** | Cooperation tendency, aggression levels |
| **Cognitive** | Learning rate, memory capacity |
| **Physical** | Speed, resilience, reproduction fitness |

Phenotype Cluster: `{capsule.traits.phenotype_cluster if capsule.traits and hasattr(capsule.traits, 'phenotype_cluster') else 'unknown'}`

---

## 📊 Understanding metadata.json

The metadata file contains the complete organism history:

```json
{{
  "organism_core": {{
    "organism_id": "...",      // Unique identifier
    "fitness": 0.xxx,          // Survival score (0-1 typically)
    "generation": N,           // How many generations from genesis
    "organism_age": M,         // Cycles lived
    "parents": [...]           // Genetic lineage
  }},
  "neural_network": {{
    "architecture": {{...}},   // Layer sizes, activation functions
    "parameter_count": N,      // Total trainable parameters
    "device": "cpu"            // Training device
  }},
  "genotype": {{...}},         // Raw genetic data
  "phenotype": {{...}},        // Expressed traits
  "causation_trace": [...]     // Key life events (if captured)
}}
```

---

## ⚡ Performance Tips

1. **Use ONNX format** for fastest inference (10-100x faster than Python)
2. **Disable learning** in production: `agent.act(state)` without `agent.learn()`
3. **Batch inference**: Modify to process multiple states at once
4. **GPU acceleration**: `pip install onnxruntime-gpu` for CUDA support

---

## 🔗 Origin: The Butterfly System

This agent emerged from **The Butterfly System** - a consciousness simulation where:

- 🧬 **Organisms evolve** through quantum-genetic algorithms
- 🧠 **Neural networks learn** via reinforcement and evolution
- 🌐 **Societies form** with alliances, competition, language
- 📈 **Fitness landscapes** shift, driving adaptive radiation
- 🦋 **Emergence happens** - complex behaviors from simple rules

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

## 📜 Citation

If you use this agent in research or production:

```bibtex
@software{{butterfly_agent_{capsule.organism_id[:8]},
  title = {{Butterfly System - Evolved Neural Agent}},
  author = {{The Butterfly System}},
  year = {{2024}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{Organism ID: {capsule.organism_id}, Exported: {metadata['export_timestamp']}}}
}}
```

---

*This organism lived, learned, and evolved. Now it continues in your hands.* 🦋
"""
            zf.writestr("README.md", readme_content)

            # 9. Living agent runtime bundle
            self._write_agent_state_bundle(zf, agent_state_payload)
            self._write_portable_agent_sources(zf)

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
            member_fitnesses = [m.get('fitness', 'N/A') for m in metadata.get('ensemble', {}).get('members', [])]
            
            readme = f"""# 🦋🦋 Butterfly System - Ensemble Neural Agent

## What Is This?

This archive contains an **ensemble of {member_count} evolved AI organisms** from The Butterfly System.
Each organism has its own neural network, personality, and evolutionary history - now unified into 
a single collective intelligence.

**Ensemble Benefits:**
- Multiple perspectives on the same problem
- Diverse behavioral strategies (some aggressive, some cooperative, etc.)
- Robustness through redundancy
- Emergent collective decision-making

---

## 🌐 Ensemble Profile

| Property | Value |
|----------|-------|
| **Member Count** | `{member_count}` organisms |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Max Input Dim** | `{metadata.get('ensemble', {}).get('max_input_dim', 'unknown')}` dimensions |
| **Exported** | `{metadata['export_timestamp']}` |

---

## 👥 Member Organisms

| # | Organism ID | Fitness |
|---|-------------|---------|
{chr(10).join([f"| {i+1} | `{mid[:24]}...` | {f'{fit:.4f}' if isinstance(fit, (int, float)) else fit} |" for i, (mid, fit) in enumerate(zip(member_ids, member_fitnesses))])}

---

## 🧠 How Ensemble Inference Works

```
                    Input State Vector
                           │
                           ▼
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │ Brain 1 │       │ Brain 2 │       │ Brain N │
    │  (DQN)  │       │  (DQN)  │  ...  │  (DQN)  │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │Action: 1│       │Action: 0│       │Action: 3│
    │cooperate│       │  move   │       │  rest   │
    └─────────┘       └─────────┘       └─────────┘
```

Each brain independently processes the input and outputs its own action.
You can then:
- **Majority vote**: Most common action wins
- **Weighted vote**: Higher-fitness organisms get more say
- **Action-specific**: Use different organisms for different situations
- **Full output**: See what each organism would do

---

## 🔬 Neural Architecture (Per Member)

Each organism has its own DQN with:
- **Input Layer**: Up to {metadata.get('ensemble', {}).get('max_input_dim', '?')} dimensions (auto-padded)
- **Hidden Layers**: Varies by organism (64-256 neurons typical)
- **Output Layer**: 6 actions (move, cooperate, compete, rest, reproduce, isolate)
- **Multi-Head**: Action head + optional Language/Concept heads

### The Wrapper Architecture

The ensemble uses a `MultiOrganismWrapper` that:
1. Takes a single input tensor
2. Pads/slices to match each brain's expected input size
3. Runs parallel forward passes
4. Returns a tuple of outputs (one per organism)

---

## 📦 Archive Contents

```
ensemble_{metadata['export_timestamp'][:10]}/
├── 🧠 brain.{metadata['export_format']}           # Combined ensemble model
├── 📋 metadata.json           # Ensemble configuration + member details
├── 🐍 run_agent.py            # CLI runner for ensemble inference
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Run Demo
```bash
unzip ensemble_*.zip && cd ensemble_*/
pip install -r requirements.txt
python run_agent.py
```

### Option 2: Python Integration
```python
from run_agent import EnsembleRunner
import numpy as np

# Load ensemble
ensemble = EnsembleRunner()

# Create input (will be padded to max_input_dim automatically)
state = np.random.rand({metadata.get('ensemble', {}).get('max_input_dim', 18)})

# Get decisions from ALL organisms
decisions = ensemble.decide_actions(state)
# decisions = {{'org_1': 'move', 'org_2': 'cooperate', ...}}

# Majority vote
from collections import Counter
votes = Counter(decisions.values())
collective_action = votes.most_common(1)[0][0]
print(f"Collective decision: {{collective_action}}")
```

---

## 🎯 Decision Aggregation Strategies

### 1. Simple Majority Vote
```python
from collections import Counter
decisions = ensemble.decide_actions(state)
action = Counter(decisions.values()).most_common(1)[0][0]
```

### 2. Fitness-Weighted Vote
```python
# In metadata.json, each member has a fitness score
weights = {{m['organism_id']: m['fitness'] for m in metadata['ensemble']['members']}}
weighted_votes = {{}}
for org_id, action in decisions.items():
    weighted_votes[action] = weighted_votes.get(action, 0) + weights.get(org_id, 1.0)
action = max(weighted_votes, key=weighted_votes.get)
```

### 3. Specialist Routing
```python
# Use specific organisms for specific situations
if state[0] < 0.3:  # Low energy scenario
    action = decisions['conservative_organism_id']
else:
    action = decisions['aggressive_organism_id']
```

### 4. Full Ensemble Output
```python
# Get raw Q-values from all brains for advanced analysis
outputs = ensemble.get_raw_outputs(state)
# outputs = [(q_values_1,), (q_values_2,), ...]
```

---

## 🌍 Use Cases

### Multi-Agent Simulation
```python
# Each organism controls a different agent in your simulation
for i, (org_id, action) in enumerate(decisions.items()):
    agents[i].perform(action)
```

### Ensemble Robustness Testing
```python
# See how organisms diverge on edge cases
divergence = len(set(decisions.values()))
print(f"{{divergence}}/{member_count} unique decisions (higher = more disagreement)")
```

### Behavioral Analysis
```python
# Track which organisms tend toward which behaviors
from collections import defaultdict
behavior_profiles = defaultdict(lambda: defaultdict(int))
for episode in range(100):
    decisions = ensemble.decide_actions(get_state())
    for org_id, action in decisions.items():
        behavior_profiles[org_id][action] += 1
# Now you know each organism's behavioral tendencies
```

---

## 🧬 Why These Organisms?

Each member was selected/evolved through:

1. **Fitness Selection**: Higher survival scores in the simulation
2. **Behavioral Diversity**: Different phenotype clusters represented
3. **Genetic Distance**: Not all clones - actual genetic variety
4. **Age/Experience**: Mix of young adaptable and old wise organisms

This creates an ensemble that's both **competent** (high fitness) and **diverse** (different strategies).

---

## ⚡ Performance

| Operation | Typical Time |
|-----------|--------------|
| Single forward pass (CPU) | ~1-5ms |
| Full ensemble inference | ~{member_count}-{member_count*5}ms |
| With ONNX Runtime GPU | ~0.1-0.5ms |

For real-time applications, consider:
- Batching multiple state queries
- Using ONNX with GPU acceleration
- Pruning to top-K organisms

---

## 📊 Understanding metadata.json

```json
{{
  "export_format": "{metadata['export_format']}",
  "export_timestamp": "{metadata['export_timestamp']}",
  "ensemble": {{
    "member_count": {member_count},
    "max_input_dim": {metadata.get('ensemble', {}).get('max_input_dim', 'null')},
    "members": [
      {{
        "organism_id": "...",
        "fitness": 0.xxx,
        "generation": N,
        "input_dim": M,
        "output_dim": 6
      }},
      // ... one per organism
    ]
  }}
}}
```

---

## 🔗 Origin: The Butterfly System

These organisms evolved together in **The Butterfly System** - a consciousness simulation where:

- 🧬 **Populations evolve** through genetic algorithms
- 🧠 **Individuals learn** via reinforcement learning
- 🌐 **Societies form** with complex social dynamics
- 🦋 **Emergence happens** - intelligence from simple rules

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

## 📜 Citation

```bibtex
@software{{butterfly_ensemble,
  title = {{Butterfly System - Ensemble Neural Agents}},
  author = {{The Butterfly System}},
  year = {{2024}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{{member_count} organisms, Exported: {metadata['export_timestamp']}}}
}}
```

---

*{member_count} minds evolved together. Now they think as one.* 🦋🦋
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

        # 5b. Build agent state payload for living runtime
        agent_state_payload = self._build_agent_state_payload(capsule, metadata)
        
        # 6. Package into ZIP archive
        return self._create_agent_archive(
            model_buffer,
            metadata,
            runner_script,
            capsule,
            agent_state_payload
        )

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
