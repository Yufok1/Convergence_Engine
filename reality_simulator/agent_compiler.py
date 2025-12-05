import torch
import json
import zipfile
import zlib
from io import BytesIO
import numpy as np
import datetime
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import base64
from string import Template
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

    class LanguageHeadWrapper(torch.nn.Module):
        """Wrapper that exports both action and language heads together."""
        
        def __init__(self, brain: 'OrganismBrain'):
            super().__init__()
            self.brain = brain
            self.has_language_head = brain.use_language_head
            self.input_dim = brain.input_dim
            self.output_dim = brain.output_dim
            self.vocab_size = brain.vocab_size if hasattr(brain, 'vocab_size') else 1000
            
        def forward(self, x: torch.Tensor):
            """Forward pass returning (action_probs, language_logits) if language head exists."""
            if self.has_language_head:
                # Call forward with return_language_logits=True
                action_probs, language_logits = self.brain(x, return_language_logits=True)
                return action_probs, language_logits
            else:
                # Just return action probs
                action_probs = self.brain(x)
                return action_probs

    class MultiOrganismWrapper(torch.nn.Module):
        def __init__(self, brains: List['OrganismBrain'], names: List[str]):
            super().__init__()
            self.brains = torch.nn.ModuleList(brains)
            self.names = names
            self.input_dims = [b.input_dim for b in brains]
            self.output_dims = [b.output_dim for b in brains]
            self.max_input_dim = max(self.input_dims) if self.input_dims else 0
            # Check if any brain has language head
            self.has_language_heads = [getattr(b, 'use_language_head', False) for b in brains]
            self.any_language_head = any(self.has_language_heads)

        def forward(self, x: torch.Tensor):
            # x shape: [B, max_input_dim] (we will slice/pad per brain)
            # Returns FLAT tuple: (action1, action2, ..., lang1, lang2, ...) for ONNX compatibility
            action_outputs = []
            language_outputs = []
            
            for brain, in_dim, has_lang in zip(self.brains, self.input_dims, self.has_language_heads):
                if x.shape[1] < in_dim:
                    pad = torch.zeros(x.shape[0], in_dim - x.shape[1], dtype=x.dtype, device=x.device)
                    x_i = torch.cat([x, pad], dim=1)
                else:
                    x_i = x[:, :in_dim]
                
                if has_lang:
                    action_probs, lang_logits = brain(x_i, return_language_logits=True)
                    action_outputs.append(action_probs)
                    language_outputs.append(lang_logits)
                else:
                    action_probs = brain(x_i)
                    action_outputs.append(action_probs)
            
            # Return flat tuple: all actions first, then all language outputs
            # This is compatible with ONNX which expects flat output tuple
            if language_outputs:
                return tuple(action_outputs + language_outputs)
            return tuple(action_outputs)
    
    def _get_brain_from_entity(self, entity) -> OrganismBrain:
        """
        Extract or reconstruct brain from either a live NeuralOrganism or an OrganismCapsule.
        
        Args:
            entity: Either a NeuralOrganism (live) or OrganismCapsule (saved)
            
        Returns:
            OrganismBrain instance
        """
        # Check if it's a live organism with a brain attribute
        if hasattr(entity, 'brain') and entity.brain is not None:
            return entity.brain
        
        # Otherwise, treat as capsule and reconstruct from neural snapshot
        return self._reconstruct_brain_from_capsule(entity)
    
    def _get_organism_id(self, entity) -> str:
        """Get organism ID from either a live organism or capsule."""
        if hasattr(entity, 'organism_id'):
            return str(entity.organism_id)
        if hasattr(entity, 'id'):
            return str(entity.id)
        if hasattr(entity, 'species_id'):
            return str(entity.species_id)
        return "unknown"
        
    def _reconstruct_brain_from_capsule(self, capsule: OrganismCapsule) -> OrganismBrain:
        """
        Reconstructs the OrganismBrain model from the capsule data.
        Uses capsule.neural (NeuralSnapshot) for reconstruction.
        """
        if not hasattr(capsule, 'neural') or not capsule.neural:
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

        # Load the state_dict FIRST to detect architecture
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

        # Use .size() instead of .shape[] for robustness
        vocab_size = state_dict['fc_language.weight'].size(0) if use_language_head else 1000

        # Infer num_attention_heads if attention is used
        if use_attention:
            # Infer from hidden_dim and common head counts
            # attention uses hidden_dim as embed_dim, which must be divisible by num_heads
            # Try to match common patterns: 8, 16, 4, 2
            for candidate_heads in [8, 16, 4, 2, 1]:
                if inferred_hidden % candidate_heads == 0:
                    num_attention_heads = candidate_heads
                    break
            else:
                num_attention_heads = 4  # Fallback
        else:
            num_attention_heads = 4

        # Use reasonable dropout matching current config (can't infer from state_dict)
        dropout = 0.15

        # Infer num_key_compositions from concept_head if present
        num_key_compositions = 20  # Default
        if use_concept_head and 'concept_head.composition_value.weight' in state_dict:
            # composition_value.weight shape is (num_key_compositions, hidden_dim)
            num_key_compositions = state_dict['concept_head.composition_value.weight'].size(0)
            logger.debug(f"Inferred num_key_compositions={num_key_compositions} from state_dict")

        # Create a new instance of OrganismBrain matching the checkpoint
        reconstructed_brain = OrganismBrain(
            input_dim=int(inferred_input),
            hidden_dim=int(inferred_hidden),
            output_dim=int(inferred_output),
            activation='relu',
            dropout=dropout,
            use_attention=bool(use_attention),
            num_attention_heads=int(num_attention_heads),
            attention_dim=int(inferred_hidden),
            vocab_size=int(vocab_size),
            use_language_head=bool(use_language_head),
            use_concept_head=bool(use_concept_head),
            num_key_compositions=int(num_key_compositions)
        )

        # Load state dict allowing extra/missing keys (robust to optional heads)
        missing, unexpected = reconstructed_brain.load_state_dict(state_dict, strict=False)
        if unexpected:
            logger.debug(f"AgentCompiler: Ignored unexpected keys during load: {sorted(list(unexpected))[:5]}...")
        reconstructed_brain.eval() # Set to evaluation mode
        
        return reconstructed_brain

    def _export_onnx(self, brain: OrganismBrain, dummy_input: torch.Tensor, model_path: str) -> None: 
        """Exports the PyTorch brain to ONNX format, including language head if present."""
        try:
            # Wrap brain to export both action and language heads
            wrapper = self.LanguageHeadWrapper(brain)
            wrapper.eval()
            
            # Log brain architecture for debugging
            logger.debug(f"ONNX export: input_dim={brain.input_dim}, hidden_dim={brain.hidden_dim}, "
                        f"output_dim={brain.output_dim}, use_attention={brain.use_attention}, "
                        f"use_language_head={brain.use_language_head}, use_concept_head={brain.use_concept_head}, "
                        f"num_key_compositions={getattr(brain, 'num_key_compositions', 'N/A')}")
            
            # Test forward pass before export to catch errors early
            logger.debug("Testing forward pass before ONNX export...")
            with torch.no_grad():
                test_output = wrapper(dummy_input)
                if isinstance(test_output, tuple):
                    logger.debug(f"Forward pass OK: {len(test_output)} outputs")
                else:
                    logger.debug(f"Forward pass OK: single output shape {test_output.shape}")
            
            # Configure output names based on whether language head exists
            if wrapper.has_language_head:
                output_names = ['action_probs', 'language_logits']
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'},
                    'language_logits': {0: 'batch_size'}
                }
            else:
                output_names = ['action_probs']
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'}
                }
            
            logger.debug("Starting torch.onnx.export...")
            torch.onnx.export(
                wrapper,
                dummy_input,
                model_path,
                input_names=['input'],
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                opset_version=11 # A commonly supported opset version
            )
            head_info = " (with language head)" if wrapper.has_language_head else ""
            logger.info(f"Successfully exported brain to ONNX{head_info}: {model_path}")
        except Exception as e:
            # Provide clearer guidance when onnx/onnxscript is missing (PyTorch 2.6+)
            import traceback
            msg = str(e)
            hint = ""
            if 'onnxscript' in msg.lower():
                hint = " (install with: pip install onnx onnxscript)"
            logger.error(f"Failed to export brain to ONNX at {model_path}: {e}{hint}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def _export_torchscript(self, brain: OrganismBrain, model_path) -> None: 
        """Exports the PyTorch brain to TorchScript format, including language head if present.
        
        Args:
            brain: The OrganismBrain to export
            model_path: Either a file path string or a BytesIO buffer
        """
        try:
            # Wrap brain to export both action and language heads
            wrapper = self.LanguageHeadWrapper(brain)
            wrapper.eval()
            
            # Log brain architecture for debugging
            logger.debug(f"TorchScript export: input_dim={brain.input_dim}, hidden_dim={brain.hidden_dim}, "
                        f"output_dim={brain.output_dim}, use_attention={brain.use_attention}, "
                        f"use_language_head={brain.use_language_head}, use_concept_head={brain.use_concept_head}, "
                        f"num_key_compositions={getattr(brain, 'num_key_compositions', 'N/A')}")
            
            # Use torch.jit.trace instead of torch.jit.script
            # trace captures the execution path dynamically, which works with
            # OrganismBrain's complex control flow (conditional attention, etc.)
            # script analyzes code statically and fails on Python 3.12 + PyTorch 2.5
            dummy_input = torch.randn(1, brain.input_dim, dtype=torch.float32)
            
            # Test forward pass before tracing to catch errors early
            logger.debug("Testing forward pass before trace...")
            with torch.no_grad():
                test_output = wrapper(dummy_input)
                if isinstance(test_output, tuple):
                    logger.debug(f"Forward pass OK: {len(test_output)} outputs")
                else:
                    logger.debug(f"Forward pass OK: single output shape {test_output.shape}")
            
            logger.debug("Starting torch.jit.trace...")
            traced_brain = torch.jit.trace(wrapper, (dummy_input,))
            
            head_info = " (with language head)" if wrapper.has_language_head else ""
            
            # Handle both file path (str) and BytesIO buffer
            if isinstance(model_path, BytesIO):
                torch.jit.save(traced_brain, model_path)
                model_path.seek(0)  # Reset buffer position for reading
                logger.info(f"Successfully exported brain to TorchScript (traced){head_info} in memory buffer")
            else:
                traced_brain.save(model_path)
                logger.info(f"Successfully exported brain to TorchScript (traced){head_info}: {model_path}")
        except Exception as e:
            import traceback
            logger.error(f"Failed to export brain to TorchScript: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def _export_statedict(self, brain: OrganismBrain, model_path: str) -> None: 
        """Exports the PyTorch brain's state_dict."""
        try:
            torch.save(brain.state_dict(), model_path)
            logger.info(f"Successfully exported brain state_dict: {model_path}")
        except Exception as e:
            logger.error(f"Failed to export brain state_dict at {model_path}: {e}")
            raise

    def _extract_fitness_value(self, entity) -> Optional[float]:
        """Safely extract fitness value from capsule or organism, handling various data formats."""
        # Handle direct numeric fitness (live organisms)
        if hasattr(entity, 'fitness'):
            fitness_attr = entity.fitness
            # If it's already a number, return it directly
            if isinstance(fitness_attr, (int, float)):
                return float(fitness_attr)
            # numpy scalar
            if hasattr(fitness_attr, 'item'):
                return float(fitness_attr.item())
            # If it's a fitness object with history
            if hasattr(fitness_attr, 'fitness_history') and fitness_attr.fitness_history:
                history = fitness_attr.fitness_history
                try:
                    # Handle list of tuples: [(time, fitness), ...]
                    if isinstance(history, list) and len(history) > 0:
                        last_entry = history[-1]
                        if isinstance(last_entry, (list, tuple)) and len(last_entry) >= 2:
                            return float(last_entry[1])
                        else:
                            return float(last_entry)
                    # Handle numpy array
                    elif hasattr(history, 'shape'):
                        if len(history.shape) == 2:
                            return float(history[-1, 1])
                        elif len(history.shape) == 1:
                            return float(history[-1])
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"Could not extract fitness from history: {e}")
        
        # Try get_fitness() method
        if hasattr(entity, 'get_fitness'):
            try:
                return float(entity.get_fitness())
            except:
                pass
        
        return None

    def _create_rich_metadata(self, capsule: OrganismCapsule, brain: Optional[OrganismBrain] = None) -> Dict[str, Any]:
        """
        Creates comprehensive metadata for the compiled agent, leveraging the rich capsule data.
        
        Args:
            capsule: The OrganismCapsule containing agent state
            brain: Optional reconstructed brain for extracting additional architecture info
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
                'fitness': self._extract_fitness_value(capsule),
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
                    'total_parameters': capsule.neural.total_parameters,
                    'has_language_head': hasattr(brain, 'use_language_head') and brain.use_language_head if brain else False,
                    'has_attention': hasattr(brain, 'use_attention') and brain.use_attention if brain else False,
                    'has_concept_head': hasattr(brain, 'use_concept_head') and brain.use_concept_head if brain else False,
                    'vocab_size': brain.vocab_size if brain and hasattr(brain, 'vocab_size') and hasattr(brain, 'use_language_head') and brain.use_language_head else None
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
            
            # VP (Vitality-Pleasure) State - CRITICAL for runtime behavior
            'vp_state': {
                'enabled': bool(capsule.vp),
                'vitality': capsule.vp.vitality if capsule.vp else None,
                'pleasure': capsule.vp.pleasure if capsule.vp else None,
                'violation_pressure': capsule.vp.violation_pressure if capsule.vp else None,
                'trajectory_length': len(capsule.vp.vp_trajectory) if capsule.vp else 0,
                'critical_events_count': len(capsule.vp.critical_events) if capsule.vp else 0,
            },
            
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

    def _compute_behavioral_fingerprint(self, brain: OrganismBrain, num_samples: int = 100) -> Dict[str, Any]:
        """
        Compute a behavioral fingerprint by sampling the brain's decision tendencies.
        
        This runs multiple random states through the network and analyzes:
        - Action distribution (which actions does it prefer?)
        - Decision confidence (how certain is it?)
        - Response patterns (how does it react to different input ranges?)
        
        Returns a dictionary with behavioral metrics that can be used for:
        - Clustering organisms by behavior
        - Filtering populations for specific traits
        - Visualizing behavioral space
        """
        brain.eval()
        
        action_counts = {i: 0 for i in range(brain.output_dim)}
        q_value_sums = {i: 0.0 for i in range(brain.output_dim)}
        confidence_scores = []
        
        # Response patterns for different input scenarios
        low_energy_actions = []    # When energy-related inputs are low
        high_threat_actions = []   # When threat signals are high
        social_actions = []        # When social signals are present
        
        with torch.no_grad():
            for i in range(num_samples):
                # Generate random state vector
                state = torch.rand(1, brain.input_dim)
                
                # Get Q-values
                q_values = brain(state)
                if isinstance(q_values, tuple):
                    q_values = q_values[0]  # Handle multi-head output
                
                q_np = q_values.squeeze().numpy()
                
                # Track action selection
                action = int(np.argmax(q_np))
                action_counts[action] += 1
                
                # Track Q-value magnitudes per action
                for j, qv in enumerate(q_np):
                    q_value_sums[j] += float(qv)
                
                # Track confidence (max Q minus mean Q)
                confidence = float(np.max(q_np) - np.mean(q_np))
                confidence_scores.append(confidence)
                
                # Scenario-specific responses
                # Low energy scenario (dims 6-8 low)
                low_energy_state = state.clone()
                low_energy_state[0, 6:9] = 0.1
                le_q = brain(low_energy_state)
                if isinstance(le_q, tuple):
                    le_q = le_q[0]
                low_energy_actions.append(int(torch.argmax(le_q).item()))
                
                # High threat scenario (dims 9-11 high)
                high_threat_state = state.clone()
                high_threat_state[0, 9:12] = 0.9
                ht_q = brain(high_threat_state)
                if isinstance(ht_q, tuple):
                    ht_q = ht_q[0]
                high_threat_actions.append(int(torch.argmax(ht_q).item()))
                
                # Social scenario (cooperative signals)
                social_state = state.clone()
                social_state[0, 15:18] = 0.8
                soc_q = brain(social_state)
                if isinstance(soc_q, tuple):
                    soc_q = soc_q[0]
                social_actions.append(int(torch.argmax(soc_q).item()))
        
        # Compute action distribution (normalized)
        total_actions = sum(action_counts.values())
        action_distribution = {
            ACTION_MAP.get(k, f'action_{k}'): round(v / total_actions, 4)
            for k, v in action_counts.items()
        }
        
        # Compute average Q-values per action
        avg_q_values = {
            ACTION_MAP.get(k, f'action_{k}'): round(v / num_samples, 4)
            for k, v in q_value_sums.items()
        }
        
        # Dominant action (most frequently chosen)
        dominant_action_idx = max(action_counts, key=action_counts.get)
        dominant_action = ACTION_MAP.get(dominant_action_idx, f'action_{dominant_action_idx}')
        
        # Behavioral tendencies (simplified categories)
        cooperative_score = action_distribution.get('cooperate', 0) + action_distribution.get('reproduce', 0) * 0.5
        competitive_score = action_distribution.get('compete', 0) + action_distribution.get('move', 0) * 0.3
        passive_score = action_distribution.get('rest', 0) + action_distribution.get('isolate', 0)
        
        # Scenario response analysis
        def mode_action(actions):
            if not actions:
                return 'unknown'
            counts = {}
            for a in actions:
                counts[a] = counts.get(a, 0) + 1
            mode_idx = max(counts, key=counts.get)
            return ACTION_MAP.get(mode_idx, f'action_{mode_idx}')
        
        return {
            'action_distribution': action_distribution,
            'avg_q_values': avg_q_values,
            'dominant_action': dominant_action,
            'dominant_action_percentage': round(action_counts[dominant_action_idx] / total_actions * 100, 1),
            'decision_confidence': {
                'mean': round(float(np.mean(confidence_scores)), 4),
                'std': round(float(np.std(confidence_scores)), 4),
                'min': round(float(np.min(confidence_scores)), 4),
                'max': round(float(np.max(confidence_scores)), 4)
            },
            'behavioral_tendencies': {
                'cooperative': round(cooperative_score, 4),
                'competitive': round(competitive_score, 4),
                'passive': round(passive_score, 4)
            },
            'scenario_responses': {
                'low_energy': mode_action(low_energy_actions),
                'high_threat': mode_action(high_threat_actions),
                'social_opportunity': mode_action(social_actions)
            },
            'behavioral_vector': [
                round(cooperative_score, 4),
                round(competitive_score, 4),
                round(passive_score, 4),
                round(float(np.mean(confidence_scores)), 4)
            ],
            'personality_label': self._classify_personality(cooperative_score, competitive_score, passive_score)
        }
    
    def _classify_personality(self, coop: float, comp: float, passive: float) -> str:
        """Classify organism into a personality archetype based on behavioral tendencies."""
        max_trait = max(coop, comp, passive)
        
        if max_trait < 0.2:
            return "balanced"
        elif coop == max_trait:
            if comp > 0.2:
                return "diplomatic"  # Cooperative but will compete if needed
            else:
                return "altruist"    # Strongly cooperative
        elif comp == max_trait:
            if coop > 0.2:
                return "opportunist" # Competitive but can cooperate
            else:
                return "aggressor"   # Strongly competitive
        elif passive == max_trait:
            if coop > comp:
                return "pacifist"    # Passive and cooperative
            else:
                return "hermit"      # Passive and isolated
        return "complex"

    def _merge_capsule_language_data(self, capsules: List['OrganismCapsule']) -> Optional[Dict[str, Any]]:
        """
        Merge language data from multiple capsules into a unified vocabulary.
        
        This creates a combined vocabulary that includes:
        - All unique concepts from all capsules
        - Merged word frequencies (summed)
        - Aggregated dialect signatures (averaged)
        - Union of all semantic associations
        
        Args:
            capsules: List of OrganismCapsule objects
            
        Returns:
            Merged language dictionary, or None if no capsules have language data
        """
        merged = {
            'vocabulary': [],
            'word_frequencies': {},
            'concepts': {},
            'semantic_associations': {},
            'dialect_signatures': [],
            'total_concepts': 0,
            'source_organisms': [],
            'ensemble_merged': True
        }
        
        has_language = False
        
        for cap in capsules:
            if not cap.language:
                continue
                
            has_language = True
            lang_data = cap.language.to_dict() if hasattr(cap.language, 'to_dict') else cap.language
            
            # Track source organism
            merged['source_organisms'].append(str(cap.organism_id))
            
            # Handle LanguageSnapshot format (atoms, concept_order, etc.)
            # OR legacy format (vocabulary, word_frequencies, etc.)
            
            # Extract vocabulary from atoms or concept_order
            if 'atoms' in lang_data:
                # LanguageSnapshot format - extract concept names as vocabulary
                for concept_id in lang_data['atoms'].keys():
                    if concept_id not in merged['vocabulary']:
                        merged['vocabulary'].append(concept_id)
                # Also merge atom data as concepts
                for concept_id, atom_data in lang_data['atoms'].items():
                    if concept_id not in merged['concepts']:
                        merged['concepts'][concept_id] = atom_data
                    else:
                        # Merge strengths by taking max
                        existing = merged['concepts'][concept_id]
                        if isinstance(atom_data, dict) and isinstance(existing, dict):
                            if atom_data.get('strength', 0) > existing.get('strength', 0):
                                merged['concepts'][concept_id] = atom_data
            
            # Also check concept_order for vocabulary
            if 'concept_order' in lang_data:
                for concept in lang_data['concept_order']:
                    if concept not in merged['vocabulary']:
                        merged['vocabulary'].append(concept)
            
            # Legacy format support
            if 'vocabulary' in lang_data:
                for word in lang_data['vocabulary']:
                    if word not in merged['vocabulary']:
                        merged['vocabulary'].append(word)
            
            # Merge word frequencies (sum them)
            if 'word_frequencies' in lang_data:
                for word, freq in lang_data['word_frequencies'].items():
                    merged['word_frequencies'][word] = merged['word_frequencies'].get(word, 0) + freq
            
            # Legacy concepts format
            if 'concepts' in lang_data:
                for concept_id, concept_data in lang_data['concepts'].items():
                    if concept_id not in merged['concepts']:
                        merged['concepts'][concept_id] = concept_data
            
            # Merge semantic associations
            if 'semantic_associations' in lang_data:
                for word, associations in lang_data['semantic_associations'].items():
                    if word not in merged['semantic_associations']:
                        merged['semantic_associations'][word] = associations
                    else:
                        # Merge association lists
                        existing = set(merged['semantic_associations'][word])
                        existing.update(associations)
                        merged['semantic_associations'][word] = list(existing)
            
            # Collect dialect signatures for averaging
            if 'dialect_signature' in lang_data:
                merged['dialect_signatures'].append(lang_data['dialect_signature'])
        
        if not has_language:
            return None
        
        # Finalize merged data
        merged['total_concepts'] = len(merged['concepts']) + len(merged['vocabulary'])
        
        # Average dialect signatures if we have multiple
        if merged['dialect_signatures']:
            import numpy as np
            try:
                avg_dialect = np.mean(merged['dialect_signatures'], axis=0).tolist()
                merged['dialect_signature'] = avg_dialect
            except Exception:
                merged['dialect_signature'] = merged['dialect_signatures'][0] if merged['dialect_signatures'] else []
        
        # Remove the list now that we've computed average
        del merged['dialect_signatures']
        
        logger.info(f"Merged language data from {len(merged['source_organisms'])} organisms: "
                   f"{merged['total_concepts']} concepts, {len(merged['vocabulary'])} words")
        
        return merged

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
            
            # 5. Bridge Config (JSON) - Critical for AgentBridge to know state dimensions
            input_dim = metadata.get('neural_network', {}).get('architecture', {}).get('input_size', 24)
            arch_info = metadata.get('neural_network', {}).get('architecture', {})
            bridge_config = {
                'state_dim': input_dim,
                'num_actions': 6,
                'action_names': ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'],
                'epsilon': 0.1,
                'epsilon_decay': 0.995,
                'epsilon_min': 0.01,
                'learning_rate': 0.001,
                'gamma': 0.99,
                'batch_size': 32,
                'max_response_length': 32,
                'temperature': 1.0,
                'default_port': 8080,
                'has_language_head': arch_info.get('has_language_head', False),
                'has_attention': arch_info.get('has_attention', False),
                'has_concept_head': arch_info.get('has_concept_head', False),
                'vocab_size': arch_info.get('vocab_size', 1000)
            }
            zf.writestr("bridge_config.json", json.dumps(bridge_config, indent=2))
            
            # 6. Atomic Language (JSON)
            if capsule.language:
                zf.writestr("atomic_language.json", json.dumps(capsule.language.to_dict(), indent=2))
            else:
                # Write empty language file - bridge.py will use default vocabulary
                empty_language = {
                    'vocabulary': [],
                    'word_frequencies': {},
                    'concepts': {},
                    'semantic_associations': {},
                    'dialect_signature': None,
                    'total_concepts': 0,
                    'source_note': 'No language training data available'
                }
                zf.writestr("atomic_language.json", json.dumps(empty_language, indent=2))

            # 7. VP State (JSON) - Vitality-Pleasure for runtime behavior
            if capsule.vp:
                zf.writestr("vp_state.json", json.dumps(capsule.vp.to_dict(), indent=2))
            else:
                # Default VP state for agents without VP history
                default_vp = {
                    'vitality': 0.5,
                    'pleasure': 0.5,
                    'violation_pressure': 0.0,
                    'vitality_history': [],
                    'pleasure_history': [],
                    'vp_trajectory': [],
                    'critical_events': [],
                    'source_note': 'Default VP state - no simulation history'
                }
                zf.writestr("vp_state.json", json.dumps(default_vp, indent=2))

            # 8. Runner Script
            zf.writestr("run_agent.py", runner_script)

            # 7. Requirements.txt
            requirements = "# Butterfly Agent - Dependencies\n"
            requirements += "# Install with: pip install -r requirements.txt\n\n"
            
            # Core dependencies based on export format
            if metadata['export_format'] == 'onnx':
                requirements += "# Neural network inference (ONNX)\n"
                requirements += "onnxruntime>=1.15.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements += "# Neural network inference (PyTorch)\n"
                requirements += "torch>=2.0.0\n"
            elif metadata['export_format'] == 'statedict':
                requirements += "# Neural network inference (PyTorch state dict)\n"
                requirements += "torch>=2.0.0\n"
            
            requirements += "numpy>=1.21.0\n\n"
            
            # Bridge/visualizer dependencies
            requirements += "# AgentBridge HTTP server & Visualizer\n"
            requirements += "flask>=2.0.0\n\n"
            
            # Gymnasium environments (NEW - comprehensive)
            requirements += "# ========================================\n"
            requirements += "# GYMNASIUM ENVIRONMENTS - Learning Playground!\n"
            requirements += "# ========================================\n"
            requirements += "# 400+ environments to train/test your agent\n\n"
            requirements += "# Core gymnasium (63 built-in environments)\n"
            requirements += "gymnasium>=0.29.0\n\n"
            requirements += "# Classic Control (CartPole, MountainCar, Pendulum, etc)\n"
            requirements += "# Already included in gymnasium core!\n\n"
            requirements += "# Visual rendering (required for --render flag)\n"
            requirements += "pygame>=2.5.0\n\n"
            requirements += "# Atari Arcade Games (100+ classic games!)\n"
            requirements += "# Pac-Man, Breakout, Space Invaders, Pong, etc.\n"
            requirements += "ale-py>=0.8.0\n\n"
            requirements += "# Box2D Physics (LunarLander, BipedalWalker, CarRacing)\n"
            requirements += "# gymnasium[box2d]\n"
            requirements += "box2d-py>=2.3.5\n\n"
            requirements += "# MuJoCo Robotics (Humanoid, Ant, HalfCheetah, etc)\n"
            requirements += "# pip install gymnasium[mujoco]\n"
            requirements += "# mujoco>=2.3.0\n\n"
            requirements += "# ========================================\n"
            requirements += "# USAGE EXAMPLES:\n"
            requirements += "# ========================================\n"
            requirements += "# python bridge.py . --mode gym --gym-env CartPole-v1 --render\n"
            requirements += "# python bridge.py . --mode gym --gym-env LunarLander-v3 --episodes 50\n"
            requirements += "# python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --online-learn\n"
            requirements += "# python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render --online-learn\n\n"
            requirements += "# ========================================\n"
            requirements += "# OPTIONAL GPU ACCELERATION\n"
            requirements += "# ========================================\n"
            requirements += "# onnxruntime-gpu>=1.15.0  # NVIDIA CUDA\n"

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
├── 🧩 portable_agent/         # Runtime code
│   ├── bridge.py             # 🌉 Universal interface (Gym, HTTP, CLI)
│   ├── agent_runtime.py      # Core AgentRuntime class
│   ├── mini_environment.py   # Built-in test environment
│   ├── gym_adapter.py        # Gymnasium/Gym bridge
│   ├── training.py           # TrainingLoop helper
│   └── visualize.py          # 🔬 Neural activation visualizer
├── 🚀 start.bat / start.sh    # Quick launch: Interactive chat mode
├── 🌐 serve.bat / serve.sh    # Quick launch: HTTP API server
├── 🐍 run_agent.py            # Legacy CLI runner script
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Double-Click Launch (Easiest!)
```
Windows: Double-click start.bat     → Interactive chat mode
         Double-click serve.bat     → HTTP API server on port 8080

Linux/Mac: chmod +x start.sh && ./start.sh    → Interactive chat
           chmod +x serve.sh && ./serve.sh    → HTTP server
```

### Option 2: AgentBridge Commands
```bash
# Extract and install
unzip agent_*.zip && cd agent_*/
pip install -r requirements.txt

# Interactive chat mode
python -m portable_agent.bridge --mode interactive

# HTTP API server (for external applications)
python -m portable_agent.bridge --mode serve --port 8080

# Run in Gym environment
python -m portable_agent.bridge --mode gym --gym-env CartPole-v1
```

### Option 3: Legacy Runner
```bash
python run_agent.py --episodes 5
python run_agent.py --gym-env CartPole-v1 --episodes 10
```

### Option 4: 🔬 Neural Activation Visualizer
```bash
python portable_agent/visualize.py
```

### Option 5: Python Integration (Direct)
```python
from portable_agent import AgentRuntime, MiniEnvironment

# Load the agent
agent = AgentRuntime.load("agent_state", brain_path="brain.{metadata['export_format']}")
env = MiniEnvironment()

state = env.reset()
while not done:
    action = agent.act(state)
    next_state, reward, done, info = env.step(action)
    agent.learn(state, action, reward, next_state, done)
    state = next_state
```

---

## 🌉 AgentBridge - Universal Interface

The **AgentBridge** is the recommended way to deploy and interact with this agent.
It provides a unified interface for all interaction modes:

### HTTP API Server
Deploy the agent as a REST API that any application can call:

```bash
python -m portable_agent.bridge --mode serve --port 8080
```

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/act` | Get action for observation/text/context |
| POST | `/chat` | Chat with agent (text in, text out) |
| POST | `/reward` | Provide reward for learning |
| GET | `/state` | Get current agent state |
| GET | `/config` | Get configuration |
| GET | `/health` | Health check |

**Example API Call:**
```python
import requests

# Chat with agent
response = requests.post('http://localhost:8080/chat', json={{
    'text': 'Enemy approaching from the north!',
    'context': {{'threat_level': 0.8}}
}})
print(response.json())
# {{'response': 'Isolating for safety.', 'action': 'isolate', 'confidence': 0.73}}

# Get action for structured input
response = requests.post('http://localhost:8080/act', json={{
    'context': {{'energy': 0.3, 'threat': 0.8, 'food_available': 0.2}}
}})
print(response.json()['action_name'])  # 'rest' or 'isolate'
```

### Interactive CLI
Chat with your agent directly:

```bash
python -m portable_agent.bridge --mode interactive
```

```
🦋 AgentBridge Interactive Mode
   Type messages to chat with the agent
   Commands: /act, /gym, /state, /config, /quit

You: I'm feeling threatened and low on energy
Agent [REST]: Resting to conserve energy.
       (confidence: 67.3%)

You: Now there's food nearby!
Agent [MOVE]: Moving to explore the environment.
       (confidence: 81.2%)
```

### Python Library Integration
Use the bridge directly in your code:

```python
from portable_agent import AgentBridge

# Load agent
bridge = AgentBridge.load("./")

# Text input (semantic parsing)
result = bridge.process(text="Enemy approaching, low on energy")
print(f"Action: {{result.action_name}}, Response: {{result.response}}")

# Structured context input
result = bridge.process(context={{
    'energy': 0.2,
    'threat': 0.9,
    'friend_nearby': 0.1
}})
print(f"Decision: {{result.action_name}} ({{result.confidence:.1%}} confident)")

# Gym observation input
result = bridge.process(obs=gym_env.reset())
action = result.action

# Provide reward for learning
bridge.reward(reward_value=1.0, done=False)

# Run full Gym episodes
stats = bridge.run_gym("CartPole-v1", episodes=100)
print(f"Mean reward: {{stats['mean_reward']:.2f}}")
```

---

## 🎮 GYMNASIUM PLAYGROUND - 400+ Learning Environments!

Your agent can learn and play in **400+ environments** across multiple categories!

### 🕹️ Classic Control (Built-in)
Simple physics environments perfect for testing:
```bash
python bridge.py . --mode gym --gym-env CartPole-v1 --render        # Balance a pole
python bridge.py . --mode gym --gym-env MountainCar-v0 --render     # Drive up a hill
python bridge.py . --mode gym --gym-env Pendulum-v1 --render        # Swing a pendulum
python bridge.py . --mode gym --gym-env Acrobot-v1 --render         # Double pendulum
python bridge.py . --mode gym --gym-env LunarLander-v3 --render     # Land on the moon!
```

### 👾 Atari Arcade (100+ Classic Games!)
Install: `pip install ale-py`
```bash
python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --render    # Break bricks!
python bridge.py . --mode gym --gym-env ALE/Pong-v5 --render        # Classic Pong
python bridge.py . --mode gym --gym-env ALE/SpaceInvaders-v5        # Shoot aliens
python bridge.py . --mode gym --gym-env ALE/Pacman-v5 --render      # Pac-Man!
python bridge.py . --mode gym --gym-env ALE/Asteroids-v5            # Space shooter
python bridge.py . --mode gym --gym-env ALE/Frogger-v5 --render     # Cross the road
python bridge.py . --mode gym --gym-env ALE/DonkeyKong-v5           # Rescue the princess
```

### 🚀 Box2D Physics
Install: `pip install gymnasium[box2d]` or `pip install box2d-py`
```bash
python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render   # Walk on 2 legs!
python bridge.py . --mode gym --gym-env CarRacing-v3 --render       # Race a car
python bridge.py . --mode gym --gym-env LunarLanderContinuous-v3    # Smooth landing
```

### 🤖 MuJoCo Robotics (Advanced)
Install: `pip install gymnasium[mujoco]`
```bash
python bridge.py . --mode gym --gym-env Humanoid-v4 --render        # Walk like a human
python bridge.py . --mode gym --gym-env Ant-v4 --render             # 4-legged ant
python bridge.py . --mode gym --gym-env HalfCheetah-v4 --render     # Run fast!
python bridge.py . --mode gym --gym-env Hopper-v4 --render          # One-legged hopper
python bridge.py . --mode gym --gym-env Swimmer-v4 --render         # Swim through fluid
python bridge.py . --mode gym --gym-env Walker2d-v4 --render        # 2D walking
```

### 🧠 Online Learning (Train While Playing!)
Enable real-time weight updates with `--online-learn`:
```bash
# Agent learns from experiences AS IT PLAYS
python bridge.py . --mode gym --gym-env CartPole-v1 --episodes 100 --online-learn

# With custom learning rate
python bridge.py . --mode gym --gym-env LunarLander-v3 --online-learn --learning-rate 0.0005

# Watch it learn!
python bridge.py . --mode gym --gym-env CartPole-v1 --render --online-learn --episodes 50
```

### 📊 Full Command Reference
```bash
python bridge.py <agent_dir> --mode gym [options]

Options:
  --gym-env, -e    Environment name (default: CartPole-v1)
  --episodes, -n   Number of episodes (default: 10)
  --render, -r     Show visual window
  --online-learn   Update weights during play
  --learning-rate  Learning rate for online learning (default: 0.001)
```

### 🔬 Interactive Gym Commands
In interactive mode (`python bridge.py . --mode interactive`):
```
/gym CartPole-v1          # Run 3 episodes
/gym CartPole-v1 render   # With visuals
/gym CartPole-v1 learn    # With online learning
/gym CartPole-v1 render learn  # Both!
/train                    # Show training stats
```

---

## ⚔️ PROTON GAME ARENA - Apprentice Adept Style Battles!

> **🙏 ATTRIBUTION**:  
> 
> 🎮 **Game Selection**: Inspired by "The Game" from **Piers Anthony's "Apprentice Adept"**  
> series (1980-1990). The 4x4 grid (PHYSICAL/MENTAL/CHANCE/ARTS × NAKED/TOOL/MACHINE/ANIMAL)  
> is the creative work of Piers Anthony. Read: *Split Infinity*, *Blue Adept*, *Juxtaposition*.  
> 
> ⚔️ **Absorption Battles**: Inspired by **"Highlander" (1986)**, directed by Russell Mulcahy.  
> The "Quickening" - where winners absorb the defeated's power, knowledge, and skills -  
> directly influenced our neural/concept/trait transfer system. *"There can be only one."*

The Proton Game Arena provides a gamified competition system using the 4x4 game 
selection grid from the novels:

```
           NAKED        TOOL         MACHINE      ANIMAL
         ─────────────────────────────────────────────────
PHYSICAL   Balance      Lunar        Racing       Bipedal
           CartPole     LunarLander  CarRacing    Walker
           
MENTAL     Frozen       Blackjack    Breakout     Custom
           Lake         Cards        SpaceInvaders Games
           
CHANCE     Pure         Luck+        Machine      Genetic
           Luck         Skill        Gambling     Lottery
           
ARTS       Language     Vocabulary   Dialogue     Cross-
           Coherence    Duel         Quality      Species
```

### Arena Commands (Interactive Mode)
```
/arena                    # Show game selection grid
/arena games              # List all arena games
/arena games physical     # Games by category
/arena play 'Balance Beam'  # Play specific game
```

### Game Categories
- **PHYSICAL**: Speed, reflexes, coordination challenges
- **MENTAL**: Strategy, planning, puzzle-solving  
- **CHANCE**: Luck-based games with probabilistic elements
- **ARTS**: Language, creativity, expression challenges

### Resource Types
- **NAKED**: Pure ability, no augmentation
- **TOOL**: Simple tools to extend capabilities
- **MACHINE**: Complex automation and machinery
- **ANIMAL**: Living partners and symbiosis

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

## 🎭 Behavioral Fingerprint

This organism's decision-making patterns were analyzed by sampling 100 random states:

### Personality Profile
| Metric | Value |
|--------|-------|
| **Personality Type** | `{metadata.get('behavioral_fingerprint', {}).get('personality_label', 'unknown')}` |
| **Dominant Action** | `{metadata.get('behavioral_fingerprint', {}).get('dominant_action', 'unknown')}` ({metadata.get('behavioral_fingerprint', {}).get('dominant_action_percentage', 0)}% of decisions) |
| **Cooperative Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('cooperative', 0):.2%} |
| **Competitive Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('competitive', 0):.2%} |
| **Passive Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('passive', 0):.2%} |

### Action Distribution
```
{chr(10).join([f"{k:12}: {'█' * int(v * 50):50} {v:.1%}" for k, v in metadata.get('behavioral_fingerprint', {}).get('action_distribution', {}).items()])}
```

### Scenario Responses
How this organism typically responds to specific situations:

| Scenario | Typical Response |
|----------|-----------------|
| **Low Energy** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('low_energy', 'unknown')}` |
| **High Threat** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('high_threat', 'unknown')}` |
| **Social Opportunity** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('social_opportunity', 'unknown')}` |

### Decision Confidence
- **Mean**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('mean', 0):.4f}
- **Std Dev**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('std', 0):.4f}
- **Range**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('min', 0):.4f} - {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('max', 0):.4f}

### Behavioral Vector (for clustering/visualization)
```python
behavioral_vector = {metadata.get('behavioral_fingerprint', {}).get('behavioral_vector', [0, 0, 0, 0])}
# [cooperative, competitive, passive, confidence]
```

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
  year = {{2025}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{Organism ID: {capsule.organism_id}, Exported: {metadata['export_timestamp']}}}
}}
```

---

*This organism lived, learned, and evolved. Now it continues in your hands.* 🦋
"""
            zf.writestr("README.md", readme_content)

            # 9. Launcher scripts for easy startup
            # Windows batch file - COMPLETE MENU with all capabilities
            start_bat = """@echo off
cd /d "%~dp0"
title Butterfly Agent - Evolved Intelligence

:menu
cls
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║         🦋 BUTTERFLY AGENT - EVOLVED INTELLIGENCE 🦋       ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║                                                            ║
echo  ║  This agent evolved in The Butterfly System simulation.    ║
echo  ║  It has learned behaviors through neural reinforcement.    ║
echo  ║                                                            ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║  CHOOSE A MODE:                                            ║
echo  ║                                                            ║
echo  ║  [1] 💬 CHAT MODE     - Talk to your agent interactively   ║
echo  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║
echo  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║
echo  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║
echo  ║  [5] 📊 AGENT INFO    - View agent stats and history       ║
echo  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║
echo  ║                                                            ║
echo  ║  [0] ❌ EXIT                                                ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.
set /p choice="Enter choice [0-6]: "

if "%choice%"=="1" goto chat
if "%choice%"=="2" goto server
if "%choice%"=="3" goto gym
if "%choice%"=="4" goto visualize
if "%choice%"=="5" goto info
if "%choice%"=="6" goto python
if "%choice%"=="0" goto end
goto menu

:setup
REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    goto menu
)
REM Install deps if needed
if not exist ".deps_installed" (
    echo.
    echo First run - installing dependencies...
    pip install torch numpy flask onnxruntime gymnasium pygame ale-py 2>nul
    echo. > .deps_installed
)
goto :eof

:chat
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   💬 CHAT MODE - Talk to your evolved agent
echo  ════════════════════════════════════════════════════════════
echo.
echo   Commands while chatting:
echo     /state  - See agent's internal state vector
echo     /config - View agent configuration  
echo     /reward [+/-] - Give positive/negative feedback
echo     /quit   - Return to menu
echo.
echo   The agent responds based on its evolved neural network.
echo   Try describing situations: "I see danger" or "Resources ahead"
echo.
echo  ════════════════════════════════════════════════════════════
echo.
python portable_agent/bridge.py . --mode interactive
pause
goto menu

:server
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🌐 HTTP SERVER MODE - REST API
echo  ════════════════════════════════════════════════════════════
echo.
echo   Starting server on http://localhost:8080
echo.
echo   ENDPOINTS:
echo     POST /act   {"text": "..."} or {"obs": [...]}
echo                 → Returns action decision
echo.
echo     POST /chat  {"message": "hello"}  
echo                 → Chat and get response
echo.
echo     POST /reward {"reward": 1.0, "done": false}
echo                 → Provide learning feedback
echo.
echo     GET /state  → Current agent state
echo     GET /config → Agent configuration
echo     GET /health → Health check
echo.
echo   Press Ctrl+C to stop server and return to menu.
echo.
echo  ════════════════════════════════════════════════════════════
echo.
python portable_agent/bridge.py . --mode serve --port 8080
pause
goto menu

:gym
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🎮 GYM MODE - 400+ Learning Environments!
echo  ════════════════════════════════════════════════════════════
echo.
echo   ENVIRONMENT CATEGORIES:
echo     Classic: CartPole-v1, MountainCar-v0, LunarLander-v3, Pendulum-v1
echo     Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5
echo     Box2D:   BipedalWalker-v3, CarRacing-v3
echo     MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4
echo.
set /p gymenv="Enter Gym environment (default: CartPole-v1): "
if "%gymenv%"=="" set gymenv=CartPole-v1
set /p episodes="Number of episodes (default: 10): "
if "%episodes%"=="" set episodes=10
set /p render="Enable visual rendering? (y/n, default: n): "
set /p online="Enable online learning? (y/n, default: n): "
echo.
set renderarg=
set onlinearg=
if /i "%render%"=="y" set renderarg=--render
if /i "%online%"=="y" set onlinearg=--online-learn
echo   Running %episodes% episodes in %gymenv%...
echo.
python portable_agent/bridge.py . --mode gym --gym-env %gymenv% --episodes %episodes% %renderarg% %onlinearg%
pause
goto menu

:visualize
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🔬 NEURAL VISUALIZER - See the brain in action
echo  ════════════════════════════════════════════════════════════
echo.
echo   This opens an interactive visualization of the neural network.
echo   Watch activations flow through the network as it processes inputs.
echo.
python portable_agent/visualize.py
pause
goto menu

:info
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   📊 AGENT INFORMATION
echo  ════════════════════════════════════════════════════════════
echo.
echo   Reading metadata.json...
echo.
type metadata.json
echo.
echo.
echo  ════════════════════════════════════════════════════════════
echo.
if exist "atomic_language.json" (
    echo   Language/Vocabulary loaded: YES
) else (
    echo   Language/Vocabulary loaded: NO
)
if exist "agent_state\\state.json" (
    echo   Saved state: YES
) else (
    echo   Saved state: NO
)
echo.
pause
goto menu

:python
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🐍 PYTHON INTEGRATION - Use programmatically
echo  ════════════════════════════════════════════════════════════
echo.
echo   Example code to use this agent in your Python projects:
echo.
echo   ─────────────────────────────────────────────────────────
echo   from portable_agent.bridge import AgentBridge
echo.
echo   # Load the agent
echo   agent = AgentBridge.load(".")
echo.
echo   # Chat with it
echo   result = agent.process(text="I see an enemy")
echo   print(result.action_name, result.confidence)
echo.
echo   # Or use with observations
echo   result = agent.process(obs=[0.5, 0.3, 0.8, ...])
echo.
echo   # Give feedback for learning  
echo   agent.reward(1.0)  # positive
echo   agent.reward(-1.0) # negative
echo.
echo   # Save learned experiences
echo   agent.save(".")
echo   ─────────────────────────────────────────────────────────
echo.
echo   Opening Python shell with agent pre-loaded...
echo.
python -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Agent loaded! Use: agent.process(text=\"...\") or agent.process(obs=[...])')"
pause
goto menu

:end
echo.
echo  Goodbye! 🦋
echo.
exit /b 0
"""
            zf.writestr("start.bat", start_bat)
            
            # Unix shell script - Same complete menu
            start_sh = """#!/bin/bash
cd "$(dirname "$0")"

show_menu() {
    clear
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════╗"
    echo "  ║         🦋 BUTTERFLY AGENT - EVOLVED INTELLIGENCE 🦋       ║"
    echo "  ╠════════════════════════════════════════════════════════════╣"
    echo "  ║                                                            ║"
    echo "  ║  This agent evolved in The Butterfly System simulation.    ║"
    echo "  ║  It has learned behaviors through neural reinforcement.    ║"
    echo "  ║                                                            ║"
    echo "  ╠════════════════════════════════════════════════════════════╣"
    echo "  ║  CHOOSE A MODE:                                            ║"
    echo "  ║                                                            ║"
    echo "  ║  [1] 💬 CHAT MODE     - Talk to your agent interactively   ║"
    echo "  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║"
    echo "  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║"
    echo "  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║"
    echo "  ║  [5] 📊 AGENT INFO    - View agent stats and history       ║"
    echo "  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║"
    echo "  ║                                                            ║"
    echo "  ║  [0] ❌ EXIT                                                ║"
    echo "  ║                                                            ║"
    echo "  ╚════════════════════════════════════════════════════════════╝"
    echo ""
}

setup() {
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python3 not found!"
        read -p "Press Enter to continue..."
        return 1
    fi
    if [ ! -f ".deps_installed" ]; then
        echo "First run - installing dependencies..."
        pip3 install torch numpy flask onnxruntime gymnasium pygame ale-py 2>/dev/null
        touch .deps_installed
    fi
    return 0
}

while true; do
    show_menu
    read -p "Enter choice [0-6]: " choice
    
    case $choice in
        1)
            setup || continue
            clear
            echo ""
            echo "  💬 CHAT MODE - Talk to your evolved agent"
            echo "  Commands: /state, /config, /reward, /quit"
            echo ""
            python3 portable_agent/bridge.py . --mode interactive
            read -p "Press Enter to continue..."
            ;;
        2)
            setup || continue
            clear
            echo ""
            echo "  🌐 HTTP SERVER - http://localhost:8080"
            echo "  POST /act, /chat, /reward | GET /state, /config"
            echo "  Press Ctrl+C to stop"
            echo ""
            python3 portable_agent/bridge.py . --mode serve --port 8080
            read -p "Press Enter to continue..."
            ;;
        3)
            setup || continue
            clear
            echo ""
            echo "  🎮 GYM MODE - 400+ Learning Environments!"
            echo ""
            echo "  ENVIRONMENT CATEGORIES:"
            echo "    Classic: CartPole-v1, MountainCar-v0, LunarLander-v3"
            echo "    Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5"
            echo "    Box2D:   BipedalWalker-v3, CarRacing-v3"
            echo "    MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4"
            echo ""
            read -p "Gym environment (default: CartPole-v1): " gymenv
            gymenv=${gymenv:-CartPole-v1}
            read -p "Episodes (default: 10): " episodes
            episodes=${episodes:-10}
            read -p "Enable visual rendering? (y/n, default: n): " render
            read -p "Enable online learning? (y/n, default: n): " online
            renderarg=""
            onlinearg=""
            [[ "$render" == "y" || "$render" == "Y" ]] && renderarg="--render"
            [[ "$online" == "y" || "$online" == "Y" ]] && onlinearg="--online-learn"
            python3 portable_agent/bridge.py . --mode gym --gym-env "$gymenv" --episodes "$episodes" $renderarg $onlinearg
            read -p "Press Enter to continue..."
            ;;
        4)
            setup || continue
            python3 portable_agent/visualize.py
            read -p "Press Enter to continue..."
            ;;
        5)
            clear
            echo ""
            echo "  📊 AGENT INFORMATION"
            echo ""
            cat metadata.json
            echo ""
            read -p "Press Enter to continue..."
            ;;
        6)
            setup || continue
            python3 -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Agent loaded! Use: agent.process(text=\"...\")') "
            ;;
        0)
            echo "Goodbye! 🦋"
            exit 0
            ;;
    esac
done
"""
            zf.writestr("start.sh", start_sh)

            # 10. Living agent runtime bundle
            self._write_agent_state_bundle(zf, agent_state_payload)
            self._write_portable_agent_sources(zf)

        archive_buffer.seek(0)
        return archive_buffer

    def _create_ensemble_archive(self,
                                 model_buffer: BytesIO,
                                 metadata: Dict[str, Any],
                                 runner_script: str,
                                 capsules: Optional[List['OrganismCapsule']] = None,
                                 vocabulary: Any = None,
                                 conversation_history: List[Dict] = None) -> BytesIO:
        """Package ensemble components into a ZIP archive.
        
        Args:
            model_buffer: The compiled neural network model
            metadata: Export metadata
            runner_script: Python runner script
            capsules: Optional list of capsules for language/config extraction
            vocabulary: LanguageVocabulary object for chat system tokenization
            conversation_history: List of conversation history entries for training data
        """
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Neural model
            model_buffer.seek(0)
            zf.writestr(f"brain.{metadata['export_format']}", model_buffer.read())

            # Metadata
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Bridge Config (JSON) - Critical for AgentBridge to know state dimensions
            max_input_dim = metadata.get('ensemble', {}).get('max_input_dim', 24)
            # Check if any brain in ensemble has language head from metadata
            members = metadata.get('ensemble', {}).get('members', [])
            any_language_head = any(m.get('has_language_head', False) for m in members)
            member_count = len(members)
            bridge_config = {
                'state_dim': max_input_dim,
                'num_actions': 6,
                'action_names': ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'],
                'epsilon': 0.1,
                'epsilon_decay': 0.995,
                'epsilon_min': 0.01,
                'learning_rate': 0.001,
                'gamma': 0.99,
                'batch_size': 32,
                'max_response_length': 32,
                'temperature': 1.0,
                'default_port': 8080,
                'has_language_head': any_language_head,
                'is_ensemble': True,
                'member_count': member_count,
                # Ensemble voting configuration
                'voting_strategy': 'fitness_weighted',  # Default: weight by organism fitness
                'top_k_voters': 5  # For fittest_top_k strategy
            }
            zf.writestr("bridge_config.json", json.dumps(bridge_config, indent=2))
            
            # Merge language data from all capsules
            if capsules:
                merged_language = self._merge_capsule_language_data(capsules)
                if merged_language:
                    zf.writestr("atomic_language.json", json.dumps(merged_language, indent=2))
                else:
                    # Write empty language file - bridge.py will use default vocabulary
                    empty_language = {
                        'vocabulary': [],
                        'word_frequencies': {},
                        'concepts': {},
                        'semantic_associations': {},
                        'dialect_signature': None,
                        'total_concepts': 0,
                        'source_note': 'No language training data available in ensemble',
                        'ensemble_merged': True
                    }
                    zf.writestr("atomic_language.json", json.dumps(empty_language, indent=2))

            # ═══════════════════════════════════════════════════════════════
            # CHAT VOCABULARY (LanguageVocabulary from butterfly_chat)
            # ═══════════════════════════════════════════════════════════════
            # This is SEPARATE from atomic_language - it's the tokenization vocab
            # used by the chat system for word<->token mapping
            if vocabulary is not None:
                chat_vocab_data = {
                    'word_to_id': dict(getattr(vocabulary, 'word_to_id', {})),
                    'id_to_word': {str(k): v for k, v in getattr(vocabulary, 'id_to_word', {}).items()},
                    'vocab_size': getattr(vocabulary, 'vocab_size', 0),
                    'word_frequencies': dict(getattr(vocabulary, 'word_frequencies', {})),
                    'word_last_used': dict(getattr(vocabulary, 'word_last_used', {})),
                    'source_note': 'Chat vocabulary for tokenization - learned words from conversations'
                }
                zf.writestr("chat_vocabulary.json", json.dumps(chat_vocab_data, indent=2))
                logger.info(f"📚 Exported chat vocabulary: {chat_vocab_data['vocab_size']} words")

            # ═══════════════════════════════════════════════════════════════
            # CONVERSATION HISTORY (Training Data)
            # ═══════════════════════════════════════════════════════════════
            # The actual chat exchanges that trained the organisms
            if conversation_history:
                history_data = {
                    'conversations': conversation_history,
                    'total_entries': len(conversation_history),
                    'source_note': 'Training conversation history - prompts and organism responses'
                }
                zf.writestr("conversation_history.json", json.dumps(history_data, indent=2))
                logger.info(f"💬 Exported conversation history: {len(conversation_history)} entries")

            # Runner
            zf.writestr("run_agent.py", runner_script)

            # Requirements
            requirements = "# Butterfly Ensemble Agent - Dependencies\n"
            requirements += "# Install with: pip install -r requirements.txt\n\n"
            
            if metadata['export_format'] == 'onnx':
                requirements += "# Neural network inference (ONNX)\n"
                requirements += "onnxruntime>=1.15.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements += "# Neural network inference (PyTorch)\n"
                requirements += "torch>=2.0.0\n"
            
            requirements += "numpy>=1.21.0\n\n"
            
            requirements += "# AgentBridge HTTP server & Visualizer\n"
            requirements += "flask>=2.0.0\n\n"
            
            # Gymnasium environments (NEW - comprehensive)
            requirements += "# ========================================\n"
            requirements += "# GYMNASIUM ENVIRONMENTS - Learning Playground!\n"
            requirements += "# ========================================\n"
            requirements += "# 400+ environments to train/test your ensemble\n\n"
            requirements += "# Core gymnasium (63 built-in environments)\n"
            requirements += "gymnasium>=0.29.0\n\n"
            requirements += "# Classic Control (CartPole, MountainCar, Pendulum, etc)\n"
            requirements += "# Already included in gymnasium core!\n\n"
            requirements += "# Visual rendering (required for --render flag)\n"
            requirements += "pygame>=2.5.0\n\n"
            requirements += "# Atari Arcade Games (100+ classic games!)\n"
            requirements += "# Pac-Man, Breakout, Space Invaders, Pong, etc.\n"
            requirements += "ale-py>=0.8.0\n\n"
            requirements += "# Box2D Physics (LunarLander, BipedalWalker, CarRacing)\n"
            requirements += "# gymnasium[box2d]\n"
            requirements += "box2d-py>=2.3.5\n\n"
            requirements += "# MuJoCo Robotics (Humanoid, Ant, HalfCheetah, etc)\n"
            requirements += "# pip install gymnasium[mujoco]\n"
            requirements += "# mujoco>=2.3.0\n\n"
            requirements += "# ========================================\n"
            requirements += "# ENSEMBLE USAGE EXAMPLES:\n"
            requirements += "# ========================================\n"
            requirements += "# python bridge.py . --mode gym --gym-env CartPole-v1 --render\n"
            requirements += "# python bridge.py . --mode gym --gym-env LunarLander-v3 --episodes 100 --online-learn\n"
            requirements += "# python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --online-learn --learning-rate 0.0001\n"
            requirements += "# python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render --online-learn\n\n"
            requirements += "# ========================================\n"
            requirements += "# OPTIONAL GPU ACCELERATION\n"
            requirements += "# ========================================\n"
            requirements += "# onnxruntime-gpu>=1.15.0  # NVIDIA CUDA\n"
            
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
├── 🗣️  atomic_language.json    # Merged vocabulary from all organisms
├── 🧩 portable_agent/         # Runtime code
│   ├── bridge.py             # 🌉 Universal interface (Gym, HTTP, CLI)
│   ├── agent_runtime.py      # Core runtime class
│   ├── mini_environment.py   # Built-in test environment
│   ├── gym_adapter.py        # Gymnasium/Gym bridge
│   ├── training.py           # TrainingLoop helper
│   └── visualize.py          # 🔬 Neural activation visualizer
├── 🚀 start.bat / start.sh    # Quick launch: Interactive chat mode
├── 🌐 serve.bat / serve.sh    # Quick launch: HTTP API server
├── 🐍 run_agent.py            # Legacy CLI runner
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Double-Click Launch (Easiest!)
```
Windows: Double-click start.bat     → Interactive chat mode
         Double-click serve.bat     → HTTP API server on port 8080

Linux/Mac: chmod +x start.sh && ./start.sh    → Interactive chat
           chmod +x serve.sh && ./serve.sh    → HTTP server
```

### Option 2: AgentBridge Commands
```bash
unzip ensemble_*.zip && cd ensemble_*/
pip install -r requirements.txt

# Interactive chat
python -m portable_agent.bridge --mode interactive

# HTTP API server
python -m portable_agent.bridge --mode serve --port 8080

# Run in Gym environment
python -m portable_agent.bridge --mode gym --gym-env CartPole-v1
```

### Option 2: Run Classic Demo
```bash
python run_agent.py
```

### Option 3: 🔬 Neural Activation Visualizer
```bash
python portable_agent/visualize.py
```

### Option 4: Python Integration
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

## 🎮 GYMNASIUM PLAYGROUND - 400+ Learning Environments!

Your ensemble can learn and play in **400+ environments** across multiple categories!
The collective intelligence votes on actions while learning from shared experiences.

### 🕹️ Classic Control (Built-in)
Simple physics environments perfect for testing ensemble coordination:
```bash
python bridge.py . --mode gym --gym-env CartPole-v1 --render        # Balance a pole
python bridge.py . --mode gym --gym-env MountainCar-v0 --render     # Drive up a hill
python bridge.py . --mode gym --gym-env Pendulum-v1 --render        # Swing a pendulum
python bridge.py . --mode gym --gym-env Acrobot-v1 --render         # Double pendulum
python bridge.py . --mode gym --gym-env LunarLander-v3 --render     # Land on the moon!
```

### 👾 Atari Arcade (100+ Classic Games!)
Install: `pip install ale-py`
```bash
python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --render    # Break bricks!
python bridge.py . --mode gym --gym-env ALE/Pong-v5 --render        # Classic Pong
python bridge.py . --mode gym --gym-env ALE/SpaceInvaders-v5        # Shoot aliens
python bridge.py . --mode gym --gym-env ALE/Pacman-v5 --render      # Pac-Man!
python bridge.py . --mode gym --gym-env ALE/Asteroids-v5            # Space shooter
python bridge.py . --mode gym --gym-env ALE/Frogger-v5 --render     # Cross the road
python bridge.py . --mode gym --gym-env ALE/DonkeyKong-v5           # Rescue the princess
```

### 🚀 Box2D Physics
Install: `pip install gymnasium[box2d]` or `pip install box2d-py`
```bash
python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render   # Walk on 2 legs!
python bridge.py . --mode gym --gym-env CarRacing-v3 --render       # Race a car
python bridge.py . --mode gym --gym-env LunarLanderContinuous-v3    # Smooth landing
```

### 🤖 MuJoCo Robotics (Advanced)
Install: `pip install gymnasium[mujoco]`
```bash
python bridge.py . --mode gym --gym-env Humanoid-v4 --render        # Walk like a human
python bridge.py . --mode gym --gym-env Ant-v4 --render             # 4-legged ant
python bridge.py . --mode gym --gym-env HalfCheetah-v4 --render     # Run fast!
python bridge.py . --mode gym --gym-env Hopper-v4 --render          # One-legged hopper
python bridge.py . --mode gym --gym-env Swimmer-v4 --render         # Swim through fluid
python bridge.py . --mode gym --gym-env Walker2d-v4 --render        # 2D walking
```

### 🧠 Online Learning (Ensemble Learns While Playing!)
Enable real-time weight updates with `--online-learn`:
```bash
# Ensemble learns from experiences AS IT PLAYS
python bridge.py . --mode gym --gym-env CartPole-v1 --episodes 100 --online-learn

# With custom learning rate
python bridge.py . --mode gym --gym-env LunarLander-v3 --online-learn --learning-rate 0.0005

# Watch the ensemble learn together!
python bridge.py . --mode gym --gym-env CartPole-v1 --render --online-learn --episodes 50
```

### 📊 Full Command Reference
```bash
python bridge.py <agent_dir> --mode gym [options]

Options:
  --gym-env, -e    Environment name (default: CartPole-v1)
  --episodes, -n   Number of episodes (default: 10)
  --render, -r     Show visual window
  --online-learn   Update weights during play (ensemble learns!)
  --learning-rate  Learning rate for online learning (default: 0.001)
```

### 🔬 Interactive Gym Commands
In interactive mode (`python bridge.py . --mode interactive`):
```
/gym CartPole-v1          # Run 3 episodes
/gym CartPole-v1 render   # With visuals
/gym CartPole-v1 learn    # With online learning
/gym CartPole-v1 render learn  # Both!
/train                    # Show training stats
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

## 🎭 Ensemble Behavioral Profile

### Personality Distribution
{chr(10).join([f"- **{personality}**: {count} organism(s)" for personality, count in metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('personality_distribution', {}).items()])}

### Aggregate Action Tendencies
```
{chr(10).join([f"{k:12}: {'█' * int(v * 50):50} {v:.1%}" for k, v in metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('action_distribution', {}).items()])}
```

### Collective Behavioral Tendencies
| Tendency | Score |
|----------|-------|
| **Cooperative** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('cooperative', 0):.2%} |
| **Competitive** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('competitive', 0):.2%} |
| **Passive** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('passive', 0):.2%} |

### Member Personality Breakdown

| # | Organism | Personality | Dominant Action |
|---|----------|-------------|-----------------|
{chr(10).join([f"| {i+1} | `{m['organism_id'][:16]}...` | {m.get('behavioral_fingerprint', {}).get('personality_label', 'unknown')} | {m.get('behavioral_fingerprint', {}).get('dominant_action', 'unknown')} |" for i, m in enumerate(metadata.get('ensemble', {}).get('members', []))])}

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
  year = {{2025}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{{member_count} organisms, Exported: {metadata['export_timestamp']}}}
}}
```

---

*{member_count} minds evolved together. Now they think as one.* 🦋🦋
"""
            zf.writestr("README.md", readme)
            
            # Launcher scripts - Full menu (same as single agent)
            # Windows batch file
            start_bat = """@echo off
cd /d "%~dp0"
title Butterfly Ensemble - Collective Intelligence

:menu
cls
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║      🦋🦋 BUTTERFLY ENSEMBLE - COLLECTIVE INTELLIGENCE 🦋🦋  ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║                                                            ║
echo  ║  This ensemble contains multiple evolved organisms         ║
echo  ║  working together as a collective intelligence.            ║
echo  ║                                                            ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║  CHOOSE A MODE:                                            ║
echo  ║                                                            ║
echo  ║  [1] 💬 CHAT MODE     - Talk to the collective             ║
echo  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║
echo  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║
echo  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║
echo  ║  [5] 📊 ENSEMBLE INFO - View member stats and profiles     ║
echo  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║
echo  ║                                                            ║
echo  ║  [0] ❌ EXIT                                                ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.
set /p choice="Enter choice [0-6]: "

if "%choice%"=="1" goto chat
if "%choice%"=="2" goto server
if "%choice%"=="3" goto gym
if "%choice%"=="4" goto visualize
if "%choice%"=="5" goto info
if "%choice%"=="6" goto python
if "%choice%"=="0" goto end
goto menu

:setup
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    goto menu
)
if not exist ".deps_installed" (
    echo First run - installing dependencies...
    pip install torch numpy flask onnxruntime gymnasium pygame ale-py 2>nul
    echo. > .deps_installed
)
goto :eof

:chat
call :setup
cls
echo.
echo  💬 CHAT MODE - Talk to the collective intelligence
echo  Commands: /state, /config, /reward, /gym, /train, /quit
echo.
python portable_agent/bridge.py . --mode interactive
pause
goto menu

:server
call :setup
cls
echo  🌐 HTTP SERVER on http://localhost:8080
echo  Endpoints: POST /act, /chat, /reward ^| GET /state, /config
echo  Press Ctrl+C to stop
echo.
python portable_agent/bridge.py . --mode serve --port 8080
pause
goto menu

:gym
call :setup
cls
echo.
echo  🎮 GYM MODE - 400+ Learning Environments!
echo.
echo  ENVIRONMENT CATEGORIES:
echo    Classic: CartPole-v1, MountainCar-v0, LunarLander-v3
echo    Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5
echo    Box2D:   BipedalWalker-v3, CarRacing-v3
echo    MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4
echo.
set /p gymenv="Gym environment (default: CartPole-v1): "
if "%gymenv%"=="" set gymenv=CartPole-v1
set /p episodes="Episodes (default: 10): "
if "%episodes%"=="" set episodes=10
set /p render="Enable visual rendering? (y/n, default: n): "
set /p online="Enable online learning? (y/n, default: n): "
set renderarg=
set onlinearg=
if /i "%render%"=="y" set renderarg=--render
if /i "%online%"=="y" set onlinearg=--online-learn
python portable_agent/bridge.py . --mode gym --gym-env %gymenv% --episodes %episodes% %renderarg% %onlinearg%
pause
goto menu

:visualize
call :setup
python portable_agent/visualize.py
pause
goto menu

:info
cls
echo  📊 ENSEMBLE INFORMATION
echo.
type metadata.json
echo.
pause
goto menu

:python
call :setup
echo.
echo  Example: agent.process(text="hello")
echo.
python -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Ensemble loaded!')"
pause
goto menu

:end
exit /b 0
"""
            zf.writestr("start.bat", start_bat)
            
            # Unix shell script
            start_sh = """#!/bin/bash
cd "$(dirname "$0")"

setup() {
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python3 not found!"
        return 1
    fi
    if [ ! -f ".deps_installed" ]; then
        pip3 install torch numpy flask onnxruntime gymnasium pygame ale-py 2>/dev/null
        touch .deps_installed
    fi
}

while true; do
    clear
    echo "  🦋🦋 BUTTERFLY ENSEMBLE - COLLECTIVE INTELLIGENCE 🦋🦋"
    echo ""
    echo "  [1] 💬 Chat   [2] 🌐 Server   [3] 🎮 Gym (400+ envs!)"
    echo "  [4] 🔬 Viz    [5] 📊 Info     [6] 🐍 Python"
    echo "  [0] Exit"
    echo ""
    read -p "Choice: " c
    case $c in
        1) setup && python3 portable_agent/bridge.py . --mode interactive; read -p "Enter..." ;;
        2) setup && python3 portable_agent/bridge.py . --mode serve --port 8080; read -p "Enter..." ;;
        3) 
            setup || continue
            echo ""
            echo "  ENVIRONMENTS: CartPole-v1, LunarLander-v3, ALE/Breakout-v5, BipedalWalker-v3..."
            read -p "Env (CartPole-v1): " e
            read -p "Episodes (10): " ep
            read -p "Render? (y/n): " r
            read -p "Online learn? (y/n): " l
            renderarg=""
            onlinearg=""
            [[ "$r" == "y" ]] && renderarg="--render"
            [[ "$l" == "y" ]] && onlinearg="--online-learn"
            python3 portable_agent/bridge.py . --mode gym --gym-env ${e:-CartPole-v1} --episodes ${ep:-10} $renderarg $onlinearg
            read -p "Enter..."
            ;;
        4) setup && python3 portable_agent/visualize.py; read -p "Enter..." ;;
        5) cat metadata.json; read -p "Enter..." ;;
        6) setup && python3 -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.')" ;;
        0) exit 0 ;;
    esac
done
"""
            zf.writestr("start.sh", start_sh)
            
            # Include portable_agent sources (for visualizer, etc.)
            self._write_portable_agent_sources(zf)

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
                                     example_state: Any = None,
                                     vocabulary: Any = None,
                                     conversation_history: List[Dict] = None) -> BytesIO:
        """Compile multiple capsules into a single ensemble model archive.
        
        Args:
            capsules: List of OrganismCapsule objects
            export_format: 'onnx' or 'torchscript'
            example_state: Example state for tracing
            vocabulary: LanguageVocabulary object for chat system
            conversation_history: List of conversation history entries

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
                'output_dim': b.output_dim,
                'has_language_head': getattr(b, 'use_language_head', False),
                'has_attention': getattr(b, 'use_attention', False)
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
                # Build output names based on whether language heads exist
                if wrapper.any_language_head:
                    # Action outputs + language outputs for members with language heads
                    output_names = [f"action_{n}" for n in names]
                    for i, (name, has_lang) in enumerate(zip(names, wrapper.has_language_heads)):
                        if has_lang:
                            output_names.append(f"language_{name}")
                else:
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
                logger.info(f"✓ Successfully exported ensemble to ONNX format ({model_buffer.tell()} bytes)")
            except Exception as e:
                logger.warning(f"✗ ONNX export failed: {type(e).__name__}: {e}")
                logger.warning("Falling back to TorchScript export.")
                model_buffer = BytesIO()
                traced = torch.jit.trace(wrapper, (dummy_input,))
                torch.jit.save(traced, model_buffer)
                model_buffer.seek(0)
                chosen_format = 'torchscript'
        else:
            # Use trace instead of script - script fails on OrganismBrain's complex control flow
            traced = torch.jit.trace(wrapper, (dummy_input,))
            torch.jit.save(traced, model_buffer)
            model_buffer.seek(0)

        # Compute behavioral fingerprints for each member
        logger.info("Computing behavioral fingerprints for ensemble members...")
        for i, (brain, cap, member_meta) in enumerate(zip(brains, capsules, members_meta)):
            try:
                fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=50)
                member_meta['behavioral_fingerprint'] = fingerprint
                member_meta['fitness'] = self._extract_fitness_value(cap)
                member_meta['generation'] = getattr(cap, 'generation', None)
                logger.info(f"  Member {i+1}/{len(brains)}: {fingerprint['personality_label']} "
                           f"(dominant: {fingerprint['dominant_action']})")
            except Exception as e:
                logger.warning(f"Could not compute fingerprint for member {i}: {e}")
                member_meta['behavioral_fingerprint'] = {'error': str(e)}

        # Compute aggregate ensemble behavioral profile
        ensemble_action_dist = {}
        ensemble_tendencies = {'cooperative': 0, 'competitive': 0, 'passive': 0}
        personality_counts = {}
        
        for member_meta in members_meta:
            fp = member_meta.get('behavioral_fingerprint', {})
            if 'error' in fp:
                continue
            # Aggregate action distributions
            for action, prob in fp.get('action_distribution', {}).items():
                ensemble_action_dist[action] = ensemble_action_dist.get(action, 0) + prob
            # Aggregate tendencies
            for tendency, score in fp.get('behavioral_tendencies', {}).items():
                ensemble_tendencies[tendency] = ensemble_tendencies.get(tendency, 0) + score
            # Count personalities
            personality = fp.get('personality_label', 'unknown')
            personality_counts[personality] = personality_counts.get(personality, 0) + 1
        
        # Normalize aggregates
        n_members = len([m for m in members_meta if 'error' not in m.get('behavioral_fingerprint', {})])
        if n_members > 0:
            ensemble_action_dist = {k: round(v / n_members, 4) for k, v in ensemble_action_dist.items()}
            ensemble_tendencies = {k: round(v / n_members, 4) for k, v in ensemble_tendencies.items()}

        # Metadata
        metadata = {
            'export_timestamp': datetime.datetime.now().isoformat(),
            'export_format': chosen_format,
            'ensemble': {
                'members': members_meta,
                'member_count': len(members_meta),
                'max_input_dim': wrapper.max_input_dim,
                'aggregate_behavioral_profile': {
                    'action_distribution': ensemble_action_dist,
                    'behavioral_tendencies': ensemble_tendencies,
                    'personality_distribution': personality_counts,
                    'dominant_personalities': sorted(personality_counts.keys(), 
                                                     key=lambda x: personality_counts[x], 
                                                     reverse=True)[:3] if personality_counts else []
                }
            },
            'runtime_dependencies': {
                'onnxruntime': onnxruntime.__version__ if ONNX_AVAILABLE else 'not installed',
                'numpy': np.__version__,
                'python': sys.version.split(' ')[0]
            }
        }

        # Runner
        runner_script = self._generate_ensemble_runner_script(chosen_format, metadata)

        # Package (pass capsules for language data extraction, plus chat vocabulary)
        return self._create_ensemble_archive(model_buffer, metadata, runner_script, capsules, vocabulary, conversation_history)

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
                logger.info(f"✓ Successfully exported to ONNX format ({model_buffer.tell()} bytes)")
            except Exception as e:
                # Graceful fallback: if ONNX dependencies missing, fallback to TorchScript
                logger.warning(f"✗ ONNX export failed: {type(e).__name__}: {e}")
                logger.warning("Falling back to TorchScript export.")
                model_buffer = BytesIO()
                self._export_torchscript(brain, model_buffer)
                chosen_format = 'torchscript'
        elif export_format == 'torchscript':
            self._export_torchscript(brain, model_buffer)
        elif export_format == 'statedict':
            self._export_statedict(brain, model_buffer)
        
        # 4. Create rich metadata
        metadata = self._create_rich_metadata(capsule, brain)
        metadata['export_format'] = chosen_format # Add (possibly updated) export format to metadata
        
        # 4b. Compute behavioral fingerprint by sampling the brain
        try:
            logger.info(f"Computing behavioral fingerprint for {capsule.organism_id}...")
            behavioral_fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=100)
            metadata['behavioral_fingerprint'] = behavioral_fingerprint
            logger.info(f"Behavioral profile: {behavioral_fingerprint['personality_label']} "
                       f"(cooperative={behavioral_fingerprint['behavioral_tendencies']['cooperative']:.2f}, "
                       f"competitive={behavioral_fingerprint['behavioral_tendencies']['competitive']:.2f})")
        except Exception as e:
            logger.warning(f"Could not compute behavioral fingerprint: {e}")
            metadata['behavioral_fingerprint'] = {'error': str(e)}
        
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

    def compile_cocoon(self,
                       capsules: List['OrganismCapsule'],
                       vocabulary: Any = None,
                       knowledge_web: Any = None,
                       training_config: Dict[str, Any] = None,
                       include_gym: bool = True,
                       include_http: bool = True,
                       compress_data: bool = True,
                       export_format: str = 'cocoon') -> Tuple[str, Optional[bytes]]:
        """
        🦋 COCOON COMPILER - Single-file deployable agent
        Compiles organism(s) into a SINGLE self-contained Python file that can run solo or ensemble.
        
        export_format options:
            - 'cocoon': Python single-file (default)
            - 'onnx': ONNX model file (Netron-viewable)
            - 'torchscript': TorchScript model file (Netron-viewable)
            - 'package': Full package (cocoon.py + ONNX + README + metadata)
        
        Returns:
            (cocoon_source, model_bytes) - model_bytes is None for 'cocoon' format
        """
        logger.info(f"[COCOON] Compiling {len(capsules)} organism(s) into single-file cocoon...")

        is_ensemble = len(capsules) > 1
        mode_str = "ENSEMBLE" if is_ensemble else "SOLO"
        logger.info(f"[COCOON] Mode: {mode_str}")

        # 1) Serialize brains
        brain_data_list = []
        brain_configs = []
        organism_names = []

        for entity in capsules:
            brain = self._get_brain_from_entity(entity)
            name = self._get_organism_id(entity)
            organism_names.append(name)

            state_buffer = BytesIO()
            torch.save(brain.state_dict(), state_buffer)
            state_bytes = state_buffer.getvalue()
            if compress_data:
                state_bytes = zlib.compress(state_bytes, level=9)
            state_b64 = base64.b64encode(state_bytes).decode('ascii')
            brain_data_list.append(state_b64)

            # Extract fitness from capsule if available
            fitness = 1.0
            if hasattr(entity, 'fitness') and entity.fitness:
                extracted = self._extract_fitness_value(entity)
                if extracted is not None:
                    fitness = extracted

            config = {
                'organism_id': name,
                'input_dim': brain.input_dim,
                'hidden_dim': brain.hidden_dim,
                'output_dim': brain.output_dim,
                'vocab_size': getattr(brain, 'vocab_size', 1000),
                'use_attention': getattr(brain, 'use_attention', False),
                'use_language_head': getattr(brain, 'use_language_head', False),
                'use_concept_head': getattr(brain, 'use_concept_head', False),
                'num_attention_heads': getattr(brain, 'num_attention_heads', 4),
                'num_key_compositions': getattr(brain, 'num_key_compositions', 15),
                'dropout': getattr(brain, 'dropout_rate', 0.1),
                'fitness': fitness,  # Include organism fitness for decision matrix
            }
            brain_configs.append(config)

        # 2) Vocabulary
        vocab_data = {}
        if vocabulary is not None:
            vocab_data = {
                'word_to_id': dict(getattr(vocabulary, 'word_to_id', {})),
                'id_to_word': {str(k): v for k, v in getattr(vocabulary, 'id_to_word', {}).items()},
                'vocab_size': getattr(vocabulary, 'vocab_size', 0),
            }
        vocab_json = json.dumps(vocab_data)
        vocab_bytes = zlib.compress(vocab_json.encode('utf-8'), level=9) if compress_data else vocab_json.encode('utf-8')
        vocab_b64 = base64.b64encode(vocab_bytes).decode('ascii')

        # 3) Knowledge web (condensed)
        kw_data = {}
        if knowledge_web is not None:
            try:
                concepts = getattr(knowledge_web, 'concepts', {})
                relations = getattr(knowledge_web, 'relations', [])
                sorted_concepts = sorted(concepts.values(), key=lambda c: getattr(c, 'discovery_count', 0), reverse=True)[:5000]
                kw_data = {
                    'concepts': {c.word: {'category': c.category, 'confidence': c.confidence} for c in sorted_concepts},
                    'relation_count': len(relations),
                }
            except Exception as e:
                logger.warning(f"[COCOON] Could not serialize knowledge web: {e}")
        kw_json = json.dumps(kw_data)
        kw_bytes = zlib.compress(kw_json.encode('utf-8'), level=9) if compress_data else kw_json.encode('utf-8')
        kw_b64 = base64.b64encode(kw_bytes).decode('ascii')

        # 4) Training config
        default_training = {
            'learning_rate': 0.001,
            'batch_size': 32,
            'gamma': 0.99,
            'epsilon': 0.1,
            'epsilon_decay': 0.995,
            'epsilon_min': 0.01,
            'rl_loss_weight': 0.8,
            'language_loss_weight': 0.1,
            'concept_loss_weight': 0.1,
            'buffer_size': 10000,
        }
        if training_config:
            default_training.update(training_config)
        config_json = json.dumps(default_training)
        config_bytes = zlib.compress(config_json.encode('utf-8'), level=9) if compress_data else config_json.encode('utf-8')
        config_b64 = base64.b64encode(config_bytes).decode('ascii')

        # 5) Architecture
        arch_data = {
            'brain_configs': brain_configs,
            'organism_names': organism_names,
            'ensemble_size': len(capsules),
            'is_ensemble': is_ensemble,
        }
        arch_json = json.dumps(arch_data)
        arch_bytes = zlib.compress(arch_json.encode('utf-8'), level=9) if compress_data else arch_json.encode('utf-8')
        arch_b64 = base64.b64encode(arch_bytes).decode('ascii')

        # Generate cocoon source (always needed for 'cocoon' and 'package' formats)
        cocoon_source = self._generate_cocoon_source(
            brain_data_list=brain_data_list,
            arch_b64=arch_b64,
            vocab_b64=vocab_b64,
            kw_b64=kw_b64,
            config_b64=config_b64,
            compressed=compress_data,
            include_gym=include_gym,
            include_http=include_http,
            is_ensemble=is_ensemble,
            organism_names=organism_names,
        )

        # Handle different export formats
        if export_format == 'cocoon':
            logger.info(f"[COCOON] ✅ Generated cocoon: {len(cocoon_source):,} characters")
            return cocoon_source, None
        
        elif export_format == 'onnx':
            # Export first brain as ONNX
            brain = self._get_brain_from_entity(capsules[0])
            onnx_buffer = BytesIO()
            dummy_input = torch.randn(1, brain.input_dim)
            try:
                torch.onnx.export(
                    brain, dummy_input, onnx_buffer,
                    export_params=True, opset_version=14,
                    do_constant_folding=True,
                    input_names=['state'],
                    output_names=['action_probs', 'language_logits'] if brain.use_language_head else ['action_probs'],
                )
                logger.info(f"[COCOON] ✅ Generated ONNX: {onnx_buffer.tell():,} bytes")
                return cocoon_source, onnx_buffer.getvalue()
            except Exception as e:
                logger.error(f"[COCOON] ONNX export failed: {e}")
                return cocoon_source, None
        
        elif export_format == 'torchscript':
            # Export first brain as TorchScript using trace (more compatible than script)
            brain = self._get_brain_from_entity(capsules[0])
            ts_buffer = BytesIO()
            try:
                brain.eval()
                # Use trace instead of script - script fails with "Can't redefine method: forward"
                input_dim = getattr(brain, 'input_dim', 24)
                dummy_input = torch.randn(1, input_dim)
                traced = torch.jit.trace(brain, (dummy_input,))
                torch.jit.save(traced, ts_buffer)
                logger.info(f"[COCOON] ✅ Generated TorchScript: {ts_buffer.tell():,} bytes")
                return cocoon_source, ts_buffer.getvalue()
            except Exception as e:
                logger.error(f"[COCOON] TorchScript export failed: {e}")
                return cocoon_source, None
        
        elif export_format == 'statedict':
            # Export first brain state dict
            brain = self._get_brain_from_entity(capsules[0])
            sd_buffer = BytesIO()
            torch.save(brain.state_dict(), sd_buffer)
            logger.info(f"[COCOON] ✅ Generated StateDict: {sd_buffer.tell():,} bytes")
            return cocoon_source, sd_buffer.getvalue()
        
        elif export_format == 'package':
            # ═══════════════════════════════════════════════════════════════════════
            # ULTIMATE PACKAGE - Everything you need to deploy the ensemble
            # ═══════════════════════════════════════════════════════════════════════
            # Contains:
            #   - brain_ensemble.onnx (ALL organisms wrapped in MultiOrganismWrapper)
            #   - brain_ensemble.pt (TorchScript version of same)
            #   - cocoon.py (self-contained Python with embedded weights)
            #   - bridge.py (universal runner for Gym/HTTP/CLI)
            #   - metadata.json (ensemble config, member profiles, behavioral fingerprints)
            #   - vocabulary.json (tokenization vocab)
            #   - requirements.txt
            #   - README.md
            # ═══════════════════════════════════════════════════════════════════════
            import zipfile
            zip_buffer = BytesIO()
            
            # Build the MultiOrganismWrapper for unified ensemble export
            brains = []
            names = []
            for entity in capsules:
                brain = self._get_brain_from_entity(entity)
                name = self._get_organism_id(entity)
                brains.append(brain)
                names.append(name)
            
            wrapper = self.MultiOrganismWrapper(brains, names)
            wrapper.eval()
            
            # Prepare dummy input for tracing
            dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32)
            
            export_results = {
                'onnx': {'success': False, 'size': 0, 'error': None},
                'torchscript': {'success': False, 'size': 0, 'error': None},
            }
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # ─────────────────────────────────────────────────────────────
                # 1. ONNX ENSEMBLE MODEL
                # ─────────────────────────────────────────────────────────────
                onnx_buffer = BytesIO()
                try:
                    output_names = [f"action_{n}" for n in names]
                    if wrapper.any_language_head:
                        for i, (name, has_lang) in enumerate(zip(names, wrapper.has_language_heads)):
                            if has_lang:
                                output_names.append(f"language_{name}")
                    
                    torch.onnx.export(
                        wrapper,
                        dummy_input,
                        onnx_buffer,
                        input_names=['state'],
                        output_names=output_names,
                        dynamic_axes={'state': {0: 'batch_size'}},
                        opset_version=14,
                        do_constant_folding=True
                    )
                    onnx_buffer.seek(0)
                    onnx_bytes = onnx_buffer.read()
                    zf.writestr('brain_ensemble.onnx', onnx_bytes)
                    export_results['onnx'] = {'success': True, 'size': len(onnx_bytes), 'error': None}
                    logger.info(f"[PACKAGE] ✅ ONNX ensemble: {len(onnx_bytes):,} bytes")
                except Exception as e:
                    export_results['onnx'] = {'success': False, 'size': 0, 'error': str(e)}
                    logger.warning(f"[PACKAGE] ⚠️ ONNX export failed: {e}")
                
                # ─────────────────────────────────────────────────────────────
                # 2. TORCHSCRIPT ENSEMBLE MODEL
                # ─────────────────────────────────────────────────────────────
                ts_buffer = BytesIO()
                try:
                    traced = torch.jit.trace(wrapper, (dummy_input,))
                    torch.jit.save(traced, ts_buffer)
                    ts_buffer.seek(0)
                    ts_bytes = ts_buffer.read()
                    zf.writestr('brain_ensemble.pt', ts_bytes)
                    export_results['torchscript'] = {'success': True, 'size': len(ts_bytes), 'error': None}
                    logger.info(f"[PACKAGE] ✅ TorchScript ensemble: {len(ts_bytes):,} bytes")
                except Exception as e:
                    export_results['torchscript'] = {'success': False, 'size': 0, 'error': str(e)}
                    logger.warning(f"[PACKAGE] ⚠️ TorchScript export failed: {e}")
                
                # ─────────────────────────────────────────────────────────────
                # 3. COCOON.PY (self-contained Python)
                # ─────────────────────────────────────────────────────────────
                zf.writestr('cocoon.py', cocoon_source)
                logger.info(f"[PACKAGE] ✅ Cocoon source: {len(cocoon_source):,} chars")
                
                # ─────────────────────────────────────────────────────────────
                # 4. BRIDGE.PY (universal runner)
                # ─────────────────────────────────────────────────────────────
                bridge_script = self._generate_bridge_script(brain_configs, is_ensemble)
                zf.writestr('bridge.py', bridge_script)
                
                # ─────────────────────────────────────────────────────────────
                # 5. METADATA.JSON (comprehensive)
                # ─────────────────────────────────────────────────────────────
                # Compute behavioral fingerprints
                member_profiles = []
                for i, (brain, cfg) in enumerate(zip(brains, brain_configs)):
                    profile = dict(cfg)  # Copy config
                    try:
                        fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=50)
                        profile['behavioral_fingerprint'] = fingerprint
                        logger.info(f"[PACKAGE] Member {i+1}: {fingerprint.get('personality_label', '?')}")
                    except Exception as e:
                        profile['behavioral_fingerprint'] = {'error': str(e)}
                    member_profiles.append(profile)
                
                metadata = {
                    'mode': 'ENSEMBLE' if is_ensemble else 'SOLO',
                    'num_organisms': len(capsules),
                    'organism_names': organism_names,
                    'max_input_dim': wrapper.max_input_dim,
                    'brain_configs': brain_configs,
                    'member_profiles': member_profiles,
                    'training_config': default_training,
                    'export_results': export_results,
                    'generated': datetime.datetime.now().isoformat(),
                    'package_contents': [
                        'brain_ensemble.onnx' if export_results['onnx']['success'] else None,
                        'brain_ensemble.pt' if export_results['torchscript']['success'] else None,
                        'cocoon.py',
                        'bridge.py',
                        'metadata.json',
                        'vocabulary.json',
                        'requirements.txt',
                        'README.md',
                    ],
                }
                # Filter out None entries
                metadata['package_contents'] = [x for x in metadata['package_contents'] if x]
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # ─────────────────────────────────────────────────────────────
                # 6. VOCABULARY.JSON
                # ─────────────────────────────────────────────────────────────
                zf.writestr('vocabulary.json', vocab_json)
                
                # ─────────────────────────────────────────────────────────────
                # 7. REQUIREMENTS.TXT
                # ─────────────────────────────────────────────────────────────
                requirements = """# Butterfly Ensemble - Complete Package Dependencies
# Install with: pip install -r requirements.txt

# ═══════════════════════════════════════════════════════════════
# CORE DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

# Neural network inference
torch>=2.0.0           # For TorchScript (.pt) models
onnxruntime>=1.15.0    # For ONNX models (CPU)
# onnxruntime-gpu>=1.15.0  # Uncomment for NVIDIA GPU acceleration

numpy>=1.21.0

# HTTP server & web interface
flask>=2.0.0

# ═══════════════════════════════════════════════════════════════
# GYMNASIUM ENVIRONMENTS (Optional but recommended!)
# ═══════════════════════════════════════════════════════════════

gymnasium>=0.29.0      # 63 built-in environments
pygame>=2.5.0          # Visual rendering

# Classic Control (CartPole, MountainCar, Pendulum, Acrobot)
# -> Included in gymnasium core!

# Atari Arcade (100+ classic games)
# ale-py>=0.8.0

# Box2D Physics (LunarLander, BipedalWalker, CarRacing)
# box2d-py>=2.3.5

# MuJoCo Robotics (Humanoid, Ant, HalfCheetah, Hopper)
# mujoco>=2.3.0

# ═══════════════════════════════════════════════════════════════
# QUICK START COMMANDS
# ═══════════════════════════════════════════════════════════════
# 
# Run with TorchScript model:
#   python bridge.py --model brain_ensemble.pt --mode interactive
#
# Run with ONNX model:
#   python bridge.py --model brain_ensemble.onnx --mode interactive
#
# Run in Gymnasium:
#   python bridge.py --model brain_ensemble.onnx --mode gym --env CartPole-v1
#
# Start HTTP server:
#   python bridge.py --model brain_ensemble.onnx --mode http --port 8080
"""
                zf.writestr('requirements.txt', requirements)
                
                # ─────────────────────────────────────────────────────────────
                # 8. README.MD
                # ─────────────────────────────────────────────────────────────
                readme = self._generate_ultimate_readme(
                    organism_names, brain_configs, metadata, export_results, is_ensemble
                )
                zf.writestr('README.md', readme)
                
                # ─────────────────────────────────────────────────────────────
                # 9. QUICK-START SCRIPTS
                # ─────────────────────────────────────────────────────────────
                # Windows batch
                start_bat = """@echo off
echo ═══════════════════════════════════════════════════════════════
echo  🦋 Butterfly Ensemble - Quick Start
echo ═══════════════════════════════════════════════════════════════
echo.
echo 1. Interactive Chat (TorchScript)
echo 2. Interactive Chat (ONNX)
echo 3. Gymnasium - CartPole
echo 4. HTTP Server
echo 5. View Metadata
echo 0. Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" python bridge.py --model brain_ensemble.pt --mode interactive
if "%choice%"=="2" python bridge.py --model brain_ensemble.onnx --mode interactive
if "%choice%"=="3" python bridge.py --model brain_ensemble.onnx --mode gym --env CartPole-v1 --render
if "%choice%"=="4" python bridge.py --model brain_ensemble.onnx --mode http --port 8080
if "%choice%"=="5" type metadata.json
if "%choice%"=="0" exit /b

pause
"""
                zf.writestr('start.bat', start_bat)
                
                # Unix shell
                start_sh = """#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo " 🦋 Butterfly Ensemble - Quick Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Interactive Chat (TorchScript)"
echo "2. Interactive Chat (ONNX)"
echo "3. Gymnasium - CartPole"
echo "4. HTTP Server"
echo "5. View Metadata"
echo "0. Exit"
echo ""
read -p "Select option: " choice

case $choice in
    1) python bridge.py --model brain_ensemble.pt --mode interactive ;;
    2) python bridge.py --model brain_ensemble.onnx --mode interactive ;;
    3) python bridge.py --model brain_ensemble.onnx --mode gym --env CartPole-v1 --render ;;
    4) python bridge.py --model brain_ensemble.onnx --mode http --port 8080 ;;
    5) cat metadata.json ;;
    0) exit 0 ;;
esac
"""
                zf.writestr('start.sh', start_sh)
            
            # Verify we got at least one model format
            if not export_results['onnx']['success'] and not export_results['torchscript']['success']:
                logger.error("[PACKAGE] ❌ FAILED: Neither ONNX nor TorchScript export succeeded!")
                # Still return the package but log the error
            
            zip_buffer.seek(0)
            total_size = len(zip_buffer.getvalue())
            logger.info(f"[COCOON] ✅ Generated ULTIMATE package: {total_size:,} bytes")
            logger.info(f"[COCOON]    ONNX: {'✅' if export_results['onnx']['success'] else '❌'} "
                       f"TorchScript: {'✅' if export_results['torchscript']['success'] else '❌'}")
            return cocoon_source, zip_buffer.getvalue()
        
        else:
            logger.warning(f"[COCOON] Unknown format '{export_format}', defaulting to cocoon")
            return cocoon_source, None

    def _generate_package_readme(self, organism_names: List[str], brain_configs: List[Dict], metadata: Dict) -> str:
        """Generate README for package export."""
        org_table = "| Organism | Input | Hidden | Output | Language Head |\n|----------|-------|--------|--------|---------------|\n"
        for cfg in brain_configs:
            org_table += f"| {cfg.get('organism_id', '?')} | {cfg.get('input_dim', 24)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {'✅' if cfg.get('use_language_head') else '❌'} |\n"
        
        return f"""# 🦋 Butterfly Cocoon Package

**Generated:** {metadata.get('generated', 'Unknown')}
**Mode:** {metadata.get('mode', 'SOLO')}
**Organisms:** {metadata.get('num_organisms', 1)}

## 📁 Contents

| File | Description |
|------|-------------|
| `cocoon.py` | Standalone Python agent (run with `python cocoon.py --mode chat`) |
| `brain_*.onnx` | ONNX models - view at [netron.app](https://netron.app/) |
| `vocabulary.json` | Token vocabulary |
| `metadata.json` | Full configuration |
| `README.md` | This file |

## 🧠 Organisms

{org_table}

## 🚀 Quick Start

```bash
# View model architecture
# Open any .onnx file at https://netron.app/

# Interactive chat
python cocoon.py --mode chat

# Export ONNX from cocoon
python cocoon.py --export-onnx brain.onnx

# Run in Gym environment  
python cocoon.py --mode gym --env CartPole-v1

# HTTP API server
python cocoon.py --mode serve --port 8080
```

## 🔗 Links

- [Netron Model Viewer](https://netron.app/)
- [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
"""

    def _generate_bridge_script(self, brain_configs: List[Dict], is_ensemble: bool) -> str:
        """Generate the universal bridge.py runner script."""
        return '''#!/usr/bin/env python3
"""
🌉 BUTTERFLY BRIDGE - Universal Agent Runner
Supports: ONNX, TorchScript, Interactive, HTTP, Gymnasium
"""
import argparse
import json
import sys
from pathlib import Path

def load_model(model_path: str):
    """Load either ONNX or TorchScript model."""
    model_path = Path(model_path)
    
    if model_path.suffix == '.onnx':
        import onnxruntime as ort
        return ort.InferenceSession(str(model_path)), 'onnx'
    elif model_path.suffix == '.pt':
        import torch
        return torch.jit.load(str(model_path)), 'torchscript'
    else:
        raise ValueError(f"Unknown model format: {model_path.suffix}")

def run_inference(model, model_type: str, state):
    """Run inference on model."""
    import numpy as np
    state = np.array(state, dtype=np.float32).reshape(1, -1)
    
    if model_type == 'onnx':
        input_name = model.get_inputs()[0].name
        outputs = model.run(None, {input_name: state})
        return outputs
    else:  # torchscript
        import torch
        with torch.no_grad():
            state_t = torch.from_numpy(state)
            outputs = model(state_t)
            if isinstance(outputs, torch.Tensor):
                return [outputs.numpy()]
            return [o.numpy() for o in outputs]

def interactive_mode(model, model_type: str, metadata: dict):
    """Interactive chat/command mode."""
    print("\\n🦋 Butterfly Ensemble Interactive Mode")
    print("=" * 50)
    print(f"Model: {model_type.upper()}")
    print(f"Organisms: {metadata.get('num_organisms', '?')}")
    print("\\nCommands: /state <values>, /quit")
    print("=" * 50)
    
    import numpy as np
    max_dim = metadata.get('max_input_dim', 24)
    
    while True:
        try:
            cmd = input("\\n> ").strip()
            if cmd.lower() in ('/quit', '/exit', 'quit', 'exit'):
                break
            elif cmd.startswith('/state '):
                values = [float(x) for x in cmd[7:].split()]
                # Pad to max_dim
                if len(values) < max_dim:
                    values.extend([0.0] * (max_dim - len(values)))
                outputs = run_inference(model, model_type, values[:max_dim])
                print(f"Outputs: {len(outputs)} tensors")
                for i, out in enumerate(outputs):
                    print(f"  [{i}] shape={out.shape}, argmax={np.argmax(out)}")
            else:
                # Generate random state for demo
                state = np.random.randn(max_dim).astype(np.float32)
                outputs = run_inference(model, model_type, state)
                actions = [np.argmax(out) for out in outputs]
                print(f"Random state -> Actions: {actions}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\\nGoodbye! 🦋")

def http_mode(model, model_type: str, metadata: dict, port: int):
    """Start HTTP API server."""
    from flask import Flask, request, jsonify
    import numpy as np
    
    app = Flask(__name__)
    
    @app.route('/predict', methods=['POST'])
    def predict():
        data = request.get_json()
        state = data.get('state', [0.0] * metadata.get('max_input_dim', 24))
        outputs = run_inference(model, model_type, state)
        return jsonify({
            'outputs': [out.tolist() for out in outputs],
            'actions': [int(np.argmax(out)) for out in outputs]
        })
    
    @app.route('/metadata')
    def get_metadata():
        return jsonify(metadata)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'model_type': model_type})
    
    print(f"\\n🌐 Starting HTTP server on port {port}")
    print(f"   POST /predict - Run inference")
    print(f"   GET /metadata - Get model info")
    app.run(host='0.0.0.0', port=port)

def gym_mode(model, model_type: str, metadata: dict, env_name: str, episodes: int, render: bool):
    """Run in Gymnasium environment."""
    import gymnasium as gym
    import numpy as np
    
    env = gym.make(env_name, render_mode='human' if render else None)
    max_dim = metadata.get('max_input_dim', 24)
    
    print(f"\\n🎮 Running {env_name} for {episodes} episodes")
    
    for ep in range(episodes):
        state, _ = env.reset()
        # Pad/truncate state
        state = np.array(state, dtype=np.float32)
        if len(state) < max_dim:
            state = np.concatenate([state, np.zeros(max_dim - len(state))])
        elif len(state) > max_dim:
            state = state[:max_dim]
        
        total_reward = 0
        done = False
        steps = 0
        
        while not done:
            outputs = run_inference(model, model_type, state)
            # Use first output (or majority vote could be implemented)
            action = int(np.argmax(outputs[0]))
            # Clamp to valid action space
            action = min(action, env.action_space.n - 1)
            
            state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            steps += 1
            
            # Pad state for next iteration
            state = np.array(state, dtype=np.float32)
            if len(state) < max_dim:
                state = np.concatenate([state, np.zeros(max_dim - len(state))])
            elif len(state) > max_dim:
                state = state[:max_dim]
        
        print(f"  Episode {ep+1}: {steps} steps, reward={total_reward:.2f}")
    
    env.close()
    print("\\nDone! 🦋")

def main():
    parser = argparse.ArgumentParser(description='🦋 Butterfly Bridge - Universal Agent Runner')
    parser.add_argument('--model', '-m', default='brain_ensemble.onnx', help='Model file (.onnx or .pt)')
    parser.add_argument('--mode', choices=['interactive', 'http', 'gym'], default='interactive')
    parser.add_argument('--port', type=int, default=8080, help='HTTP server port')
    parser.add_argument('--env', '-e', default='CartPole-v1', help='Gymnasium environment')
    parser.add_argument('--episodes', '-n', type=int, default=5, help='Number of episodes')
    parser.add_argument('--render', '-r', action='store_true', help='Render environment')
    args = parser.parse_args()
    
    # Load metadata
    metadata = {}
    if Path('metadata.json').exists():
        with open('metadata.json') as f:
            metadata = json.load(f)
    
    # Load model
    print(f"Loading {args.model}...")
    model, model_type = load_model(args.model)
    print(f"✅ Loaded {model_type.upper()} model")
    
    if args.mode == 'interactive':
        interactive_mode(model, model_type, metadata)
    elif args.mode == 'http':
        http_mode(model, model_type, metadata, args.port)
    elif args.mode == 'gym':
        gym_mode(model, model_type, metadata, args.env, args.episodes, args.render)

if __name__ == '__main__':
    main()
'''

    def _generate_ultimate_readme(self, organism_names: List[str], brain_configs: List[Dict], 
                                   metadata: Dict, export_results: Dict, is_ensemble: bool) -> str:
        """Generate comprehensive README for ultimate package."""
        mode = "ENSEMBLE" if is_ensemble else "SOLO"
        num_orgs = len(organism_names)
        
        # Build organism table
        org_table = "| # | Organism ID | Input | Hidden | Output | Language | Fitness |\n"
        org_table += "|---|-------------|-------|--------|--------|----------|--------|\n"
        for i, cfg in enumerate(brain_configs):
            org_id = cfg.get('organism_id', '?')[:16]
            has_lang = '✅' if cfg.get('use_language_head') else '❌'
            fitness = cfg.get('fitness', 0)
            fitness_str = f"{fitness:.4f}" if isinstance(fitness, float) else str(fitness)
            org_table += f"| {i+1} | `{org_id}` | {cfg.get('input_dim', 24)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {has_lang} | {fitness_str} |\n"
        
        # Export status
        onnx_status = "✅ Included" if export_results.get('onnx', {}).get('success') else "❌ Failed"
        ts_status = "✅ Included" if export_results.get('torchscript', {}).get('success') else "❌ Failed"
        onnx_size = export_results.get('onnx', {}).get('size', 0)
        ts_size = export_results.get('torchscript', {}).get('size', 0)
        
        return f'''# 🦋🦋 Butterfly Ensemble - Ultimate Package

> **{num_orgs} evolved AI organisms** unified into a single deployable intelligence

## 📦 Package Contents

| File | Description | Size |
|------|-------------|------|
| `brain_ensemble.onnx` | ONNX model (all organisms) | {onnx_size:,} bytes {onnx_status} |
| `brain_ensemble.pt` | TorchScript model (all organisms) | {ts_size:,} bytes {ts_status} |
| `cocoon.py` | Self-contained Python (embedded weights) | - |
| `bridge.py` | Universal runner (Gym/HTTP/CLI) | - |
| `metadata.json` | Complete configuration | - |
| `vocabulary.json` | Token vocabulary | - |
| `requirements.txt` | Python dependencies | - |
| `start.bat` / `start.sh` | Quick-start launcher | - |

## 🚀 Quick Start

### Option 1: Double-Click Launch
- **Windows:** Run `start.bat`
- **Linux/Mac:** Run `./start.sh`

### Option 2: Command Line

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive mode (TorchScript)
python bridge.py --model brain_ensemble.pt --mode interactive

# Interactive mode (ONNX - faster)
python bridge.py --model brain_ensemble.onnx --mode interactive

# Gymnasium environment
python bridge.py --model brain_ensemble.onnx --mode gym --env CartPole-v1 --render

# HTTP API server
python bridge.py --model brain_ensemble.onnx --mode http --port 8080
```

### Option 3: Pure Python (No Dependencies)

```bash
# The cocoon.py has embedded weights - runs standalone!
python cocoon.py --mode chat
python cocoon.py --mode gym --env CartPole-v1
```

## 🧠 Ensemble Members

{org_table}

## 🔬 Architecture

```
                    Input State Vector ({metadata.get('max_input_dim', 24)} dims)
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │ Brain 1 │     │ Brain 2 │ ... │ Brain N │
      │  (DQN)  │     │  (DQN)  │     │  (DQN)  │
      └────┬────┘     └────┬────┘     └────┬────┘
           │               │               │
           ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │Action Q │     │Action Q │     │Action Q │
      │ values  │     │ values  │     │ values  │
      └─────────┘     └─────────┘     └─────────┘
```

The `MultiOrganismWrapper` feeds the same input to all brains and returns
all their Q-value outputs. You can then:
- **Majority vote** - Most common action
- **Weighted vote** - Weight by fitness scores
- **Ensemble average** - Average Q-values, then argmax

## 🌐 HTTP API

Start server: `python bridge.py --model brain_ensemble.onnx --mode http --port 8080`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Run inference on state |
| `/metadata` | GET | Get ensemble info |
| `/health` | GET | Health check |

### Example

```bash
curl -X POST http://localhost:8080/predict \\
  -H "Content-Type: application/json" \\
  -d '{{"state": [0.1, 0.2, 0.3, 0.4]}}'
```

## 🎮 Gymnasium Environments

```bash
# Classic Control
python bridge.py -m brain_ensemble.onnx --mode gym --env CartPole-v1 --render
python bridge.py -m brain_ensemble.onnx --mode gym --env MountainCar-v0 --render
python bridge.py -m brain_ensemble.onnx --mode gym --env LunarLander-v3 --render

# With training
python bridge.py -m brain_ensemble.onnx --mode gym --env CartPole-v1 --episodes 100
```

## 🔗 Links

- 📊 [View Model in Netron](https://netron.app/) - Drag & drop any `.onnx` or `.pt` file
- 🦋 [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
- 📚 [Gymnasium Docs](https://gymnasium.farama.org/)

---

*Generated: {metadata.get('generated', 'Unknown')}*
'''

    def _generate_cocoon_source(self,
                                brain_data_list: List[str],
                                arch_b64: str,
                                vocab_b64: str,
                                kw_b64: str,
                                config_b64: str,
                                compressed: bool,
                                include_gym: bool,
                                include_http: bool,
                                is_ensemble: bool,
                                organism_names: List[str]) -> str:
        """Generate the complete cocoon Python source code."""

        brain_data_py = "[\n" + ",\n".join(f'    "{b}"' for b in brain_data_list) + "\n]"
        mode_comment = "ENSEMBLE MODE - Multiple organisms with voting" if is_ensemble else "SOLO MODE - Single organism"
        generated_timestamp = datetime.datetime.now().isoformat()

        template = Template(r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦋 BUTTERFLY COCOON - Self-Contained Learning Agent
════════════════════════════════════════════════════════════════════════════════

$MODE_COMMENT
Organisms: $ORGANISMS
Generated: $GENERATED_TS

Faithful behavioral clone of Butterfly System (as prescribed):
    • VP-aware attention: scores / (1.0 + vp_value)
    • Experience buffer stores input_tokens, target_tokens, vp_value
    • Triple-loss pipeline (RL + Language + Concept placeholder)
    • Curriculum-ready sequence handling
    • Solo + Ensemble voting

USAGE:
    python cocoon.py --mode chat
    python cocoon.py --mode gym --env CartPole-v1
    python cocoon.py --mode serve --port 8080
    python cocoon.py --export new_cocoon.py

ATTRIBUTION:
    Proton Game Arena inspired by Piers Anthony's "Apprentice Adept" (1980-1990)
    Absorption battle mechanic inspired by "Highlander" (1986), dir. Russell Mulcahy
    Butterfly System / Convergence Engine: https://github.com/Yufok1/Convergence_Engine
"""

import json
import base64
import random
import sys
import os
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import numpy as np

# Embedded payloads (base64, optional zlib)
_BRAIN_DATA = $BRAIN_DATA
_ARCHITECTURE_B64 = "$ARCH_B64"
_VOCABULARY_B64 = "$VOCAB_B64"
_KNOWLEDGE_WEB_B64 = "$KW_B64"
_TRAINING_CONFIG_B64 = "$CONFIG_B64"
_DATA_COMPRESSED = $DATA_COMPRESSED


def _decode_data(b64_str: str, is_json: bool = True) -> Any:
    raw = base64.b64decode(b64_str)
    if _DATA_COMPRESSED:
        import zlib
        raw = zlib.decompress(raw)
    if is_json:
        return json.loads(raw.decode('utf-8'))
    return raw


def _decode_brain(b64_str: str) -> bytes:
    raw = base64.b64decode(b64_str)
    if _DATA_COMPRESSED:
        import zlib
        raw = zlib.decompress(raw)
    return raw


# Torch imports
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not found. Install with: pip install torch")
    print("    Learning disabled; info mode still works.")


# Experience buffer with token + VP support
@dataclass
class Experience:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    input_tokens: List[int]
    target_tokens: List[int]
    vp_value: Optional[float]


class ExperienceBuffer:
    def __init__(self, capacity: int = 0):
        self.capacity = capacity if capacity and capacity > 0 else None
        self.buffer: deque = deque(maxlen=self.capacity)

    def add(self, state, action, reward, next_state, done,
            input_tokens: Optional[List[int]] = None,
            target_tokens: Optional[List[int]] = None,
            vp_value: Optional[float] = None):
        exp = Experience(
            np.asarray(state, dtype=np.float32),
            int(action),
            float(reward),
            np.asarray(next_state, dtype=np.float32),
            bool(done),
            input_tokens or [],
            target_tokens or [],
            vp_value
        )
        self.buffer.append(exp)

    def __len__(self):
        return len(self.buffer)

    def sample(self, batch_size: int) -> List[Experience]:
        batch_size = min(batch_size, len(self.buffer))
        return random.sample(list(self.buffer), batch_size)

    def sample_batch(self, batch_size: int):
        exps = self.sample(batch_size)
        return (
            np.array([e.state for e in exps]),
            np.array([e.action for e in exps]),
            np.array([e.reward for e in exps]),
            np.array([e.next_state for e in exps]),
            np.array([e.done for e in exps]),
            [e.input_tokens for e in exps],
            [e.target_tokens for e in exps],
            [e.vp_value for e in exps],
        )


# Multi-head attention with VP scaling
if TORCH_AVAILABLE:
    class MultiHeadAttention(nn.Module):
        def __init__(self, embed_dim: int, num_heads: int = 4, dropout: float = 0.1):
            super().__init__()
            if embed_dim % num_heads != 0:
                raise ValueError("embed_dim must be divisible by num_heads")
            self.embed_dim = embed_dim
            self.num_heads = num_heads
            self.head_dim = embed_dim // num_heads
            self.scale = float(self.head_dim) ** 0.5
            self.q_proj = nn.Linear(embed_dim, embed_dim)
            self.k_proj = nn.Linear(embed_dim, embed_dim)
            self.v_proj = nn.Linear(embed_dim, embed_dim)
            self.out_proj = nn.Linear(embed_dim, embed_dim)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x: torch.Tensor, vp_value: Optional[float] = None) -> torch.Tensor:
            bsz, seq_len, _ = x.size()
            q = self.q_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            k = self.k_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            v = self.v_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

            scores = torch.matmul(q, k.transpose(-2, -1)) / self.scale
            if vp_value is not None and vp_value > 0:
                scores = scores / (1.0 + vp_value)

            attn = F.softmax(scores, dim=-1)
            attn = self.dropout(attn)
            out = torch.matmul(attn, v)
            out = out.transpose(1, 2).contiguous().view(bsz, seq_len, self.embed_dim)
            return self.out_proj(out)


    class ConceptHead(nn.Module):
        """Concept prediction head for compositional understanding (RCUS)."""
        def __init__(self, hidden_dim: int = 64, num_axioms: int = 18, num_compositions: int = 15):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.num_axioms = num_axioms
            self.num_compositions = num_compositions
            self.axiom_relevance = nn.Linear(hidden_dim, num_axioms)
            self.composition_value = nn.Linear(hidden_dim, num_compositions)
            self.context_embed = nn.Linear(hidden_dim, hidden_dim)

        def forward(self, hidden: torch.Tensor) -> Dict[str, torch.Tensor]:
            return {
                'axiom_relevance': torch.sigmoid(self.axiom_relevance(hidden)),
                'composition_value': self.composition_value(hidden),
                'context': self.context_embed(hidden),
            }


    class OrganismBrain(nn.Module):
        def __init__(self, config: Dict[str, Any]):
            super().__init__()
            self.input_dim = config['input_dim']
            self.hidden_dim = config['hidden_dim']
            self.output_dim = config['output_dim']
            self.vocab_size = config.get('vocab_size', 1000)
            self.use_language_head = config.get('use_language_head', False)
            self.use_concept_head = config.get('use_concept_head', False)
            self.use_attention = config.get('use_attention', False)
            self.dropout_rate = config.get('dropout', 0.1)
            self.num_attention_heads = config.get('num_attention_heads', 4)
            self.num_key_compositions = config.get('num_key_compositions', 15)
            self.fc1 = nn.Linear(self.input_dim, self.hidden_dim)
            if self.use_attention:
                self.attention = MultiHeadAttention(self.hidden_dim, self.num_attention_heads, self.dropout_rate)
                self.attention_norm = nn.LayerNorm(self.hidden_dim)
            self.fc2 = nn.Linear(self.hidden_dim, self.hidden_dim)
            self.fc3 = nn.Linear(self.hidden_dim, self.output_dim)
            if self.use_language_head:
                self.fc_language = nn.Linear(self.hidden_dim, self.vocab_size)
            if self.use_concept_head:
                self.concept_head = ConceptHead(self.hidden_dim, num_axioms=18, num_compositions=self.num_key_compositions)
            self.dropout = nn.Dropout(self.dropout_rate)

        def forward(self, x: torch.Tensor, vp_value: Optional[float] = None,
                    return_language_logits: bool = True) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
            if x.shape[-1] < self.input_dim:
                pad = torch.zeros(*x.shape[:-1], self.input_dim - x.shape[-1], device=x.device)
                x = torch.cat([x, pad], dim=-1)
            elif x.shape[-1] > self.input_dim:
                x = x[..., :self.input_dim]

            h = F.relu(self.fc1(x))
            h = self.dropout(h)

            if self.use_attention:
                if h.dim() == 2:
                    h = h.unsqueeze(1)
                attn_out = self.attention(h, vp_value=vp_value)
                h = self.attention_norm(h + attn_out)
                h = h.squeeze(1)

            h = F.relu(self.fc2(h))
            h = self.dropout(h)

            action_logits = self.fc3(h)
            action_probs = F.softmax(action_logits, dim=-1)

            language_logits = None
            if self.use_language_head and return_language_logits:
                language_logits = self.fc_language(h)
            return action_probs, language_logits


class EnsembleVoting:
    @staticmethod
    def majority(actions: List[int]) -> int:
        from collections import Counter
        return Counter(actions).most_common(1)[0][0]

    @staticmethod
    def confidence(action_probs_list: List[np.ndarray]) -> int:
        weights = [float(np.max(p)) for p in action_probs_list]
        weighted = np.zeros_like(action_probs_list[0])
        for p, w in zip(action_probs_list, weights):
            weighted += p * w
        return int(np.argmax(weighted / max(1e-9, sum(weights))))


class CocoonAgent:
    def __init__(self, voting: str = 'confidence'):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.architecture = _decode_data(_ARCHITECTURE_B64)
        self.is_ensemble = self.architecture.get('is_ensemble', False)
        self.organism_names = self.architecture.get('organism_names', [])
        self.config = _decode_data(_TRAINING_CONFIG_B64)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.batch_size = self.config.get('batch_size', 32)
        self.gamma = self.config.get('gamma', 0.99)
        self.epsilon = self.config.get('epsilon', 0.1)
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)
        self.epsilon_min = self.config.get('epsilon_min', 0.01)
        self.rl_weight = self.config.get('rl_loss_weight', 0.8)
        self.lang_weight = self.config.get('language_loss_weight', 0.1)
        self.concept_weight = self.config.get('concept_loss_weight', 0.1)
        self.vocabulary = _decode_data(_VOCABULARY_B64)
        self.knowledge_web = _decode_data(_KNOWLEDGE_WEB_B64)
        self.brains: List[OrganismBrain] = []
        self.optimizers: List[optim.Adam] = []
        self.experience_buffers: List[ExperienceBuffer] = []
        self.organism_fitness: List[float] = []  # Track per-organism fitness
        self._load_brains()
        self.voting = voting
        self.training_step = 0
        mode = "ENSEMBLE" if self.is_ensemble else "SOLO"
        print(f"[OK] CocoonAgent loaded: {mode}, {len(self.brains)} organism(s), device={self.device}")

    def _load_brains(self):
        brain_configs = self.architecture.get('brain_configs', [])
        for idx, (cfg, brain_b64) in enumerate(zip(brain_configs, _BRAIN_DATA)):
            brain = OrganismBrain(cfg)
            state_bytes = _decode_brain(brain_b64)
            state_dict = torch.load(BytesIO(state_bytes), map_location=self.device, weights_only=False)
            brain.load_state_dict(state_dict)
            brain.to(self.device)
            brain.eval()
            self.brains.append(brain)
            self.optimizers.append(optim.Adam(brain.parameters(), lr=self.learning_rate))
            self.experience_buffers.append(ExperienceBuffer(self.config.get('buffer_size', 0)))
            # Initialize fitness from config or default
            fitness = cfg.get('fitness', 1.0 + idx * 0.05)
            self.organism_fitness.append(fitness)

    def tokenize(self, text: str) -> List[int]:
        word_to_id = self.vocabulary.get('word_to_id', {})
        unk_id = word_to_id.get('<UNK>', 1)
        return [word_to_id.get(w, unk_id) for w in text.lower().split()]

    def detokenize(self, tokens: List[int]) -> str:
        id_to_word = {int(k): v for k, v in self.vocabulary.get('id_to_word', {}).items()}
        words = []
        for t in tokens:
            w = id_to_word.get(int(t), '<UNK>')
            if w in ['<END>', '<PAD>']:
                break
            words.append(w)
        return ' '.join(words)

    def add_word(self, word: str) -> int:
        """Add a new word to vocabulary dynamically. Returns token ID."""
        word = word.lower().strip()
        if not word:
            return self.vocabulary.get('word_to_id', {}).get('<UNK>', 1)
        
        word_to_id = self.vocabulary.get('word_to_id', {})
        id_to_word = self.vocabulary.get('id_to_word', {})
        
        if word in word_to_id:
            return word_to_id[word]
        
        # Add new word
        new_id = len(word_to_id)
        word_to_id[word] = new_id
        id_to_word[str(new_id)] = word
        self.vocabulary['word_to_id'] = word_to_id
        self.vocabulary['id_to_word'] = id_to_word
        self.vocabulary['vocab_size'] = len(word_to_id)
        print(f"[VOCAB] Learned new word: '{word}' (ID={new_id})")
        return new_id

    def learn_from_text(self, text: str, context_state: Optional[np.ndarray] = None,
                        reward: float = 0.0, vp_value: Optional[float] = None):
        """Learn from text input - adds new words and creates training experience."""
        words = text.lower().split()
        tokens = []
        for word in words:
            # Add word if new
            token_id = self.add_word(word)
            tokens.append(token_id)
        
        # Create experience with language targets
        if context_state is None:
            context_state = np.zeros(self.brains[0].input_dim, dtype=np.float32)
        
        # Add as experience for language learning
        if len(tokens) > 1:
            for i in range(len(tokens) - 1):
                self.add_experience(
                    state=context_state,
                    action=0,  # Placeholder
                    reward=reward,
                    next_state=context_state,
                    done=False,
                    input_tokens=tokens[:i+1],
                    target_tokens=[tokens[i+1]],
                    vp_value=vp_value
                )
        return tokens

    def add_concept(self, word: str, category: str = 'learned', confidence: float = 0.5):
        """Add a new concept to knowledge web."""
        if 'concepts' not in self.knowledge_web:
            self.knowledge_web['concepts'] = {}
        
        self.knowledge_web['concepts'][word] = {
            'category': category,
            'confidence': confidence
        }
        # Also add to vocabulary
        self.add_word(word)

    def get_action(self, state: np.ndarray, explore: bool = True, vp_value: Optional[float] = None,
                   action_space_size: Optional[int] = None) -> int:
        """Get action from ensemble or single brain, optionally limited to action_space_size."""
        effective_size = action_space_size if action_space_size else self.brains[0].output_dim
        if explore and random.random() < self.epsilon:
            return random.randint(0, effective_size - 1)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        if self.is_ensemble:
            probs_list = []
            for brain in self.brains:
                brain.eval()
                with torch.no_grad():
                    probs, _ = brain(state_t, vp_value=vp_value, return_language_logits=False)
                # Slice to action_space_size if needed
                p = probs.cpu().numpy().squeeze(0)
                if action_space_size and len(p) > action_space_size:
                    p = p[:action_space_size]
                    p = p / (p.sum() + 1e-9)  # Re-normalize
                probs_list.append(p)
            return EnsembleVoting.confidence(probs_list)
        brain = self.brains[0]
        brain.eval()
        with torch.no_grad():
            probs, _ = brain(state_t, vp_value=vp_value, return_language_logits=False)
        if action_space_size and probs.shape[-1] > action_space_size:
            probs = probs[..., :action_space_size]
        return int(torch.argmax(probs, dim=-1).item())

    def add_experience(self, state, action, reward, next_state, done,
                        input_tokens=None, target_tokens=None, vp_value=None, organism_idx: Optional[int] = None):
        targets = range(len(self.experience_buffers)) if organism_idx is None else [organism_idx]
        for idx in targets:
            if idx < len(self.experience_buffers):
                self.experience_buffers[idx].add(state, action, reward, next_state, done,
                                                  input_tokens=input_tokens, target_tokens=target_tokens, vp_value=vp_value)

    def _language_loss(self, logits: torch.Tensor, target_tokens: List[List[int]], vp_value: Optional[float]):
        if logits is None or len(target_tokens) == 0:
            return None
        targets = torch.LongTensor([t[0] if t else 0 for t in target_tokens]).to(self.device)
        if vp_value is not None and vp_value > 0:
            logits = logits / (1.0 + vp_value)
        return F.cross_entropy(logits, targets, ignore_index=0)

    def train_step(self) -> float:
        total = 0.0
        trained = 0
        for brain, opt, buf in zip(self.brains, self.optimizers, self.experience_buffers):
            if len(buf) < self.batch_size:
                continue
            states, actions, rewards, next_states, dones, in_tok, tgt_tok, vp_vals = buf.sample_batch(self.batch_size)
            vp_val = None
            for v in vp_vals:
                if v is not None:
                    vp_val = v
                    break
            states_t = torch.FloatTensor(states).to(self.device)
            actions_t = torch.LongTensor(actions).to(self.device)
            rewards_t = torch.FloatTensor(rewards).to(self.device)
            next_states_t = torch.FloatTensor(next_states).to(self.device)
            dones_t = torch.BoolTensor(dones).to(self.device)

            brain.train()
            q_values, lang_logits = brain(states_t, vp_value=vp_val, return_language_logits=True)
            q_sel = q_values.gather(1, actions_t.unsqueeze(1)).squeeze(1)

            brain.eval()
            with torch.no_grad():
                next_q, _ = brain(next_states_t, vp_value=vp_val, return_language_logits=False)
                next_max = next_q.max(1)[0]
            target_q = rewards_t + self.gamma * next_max * (~dones_t)

            rl_loss = F.mse_loss(q_sel, target_q)
            lang_loss = self._language_loss(lang_logits, tgt_tok, vp_val)
            
            # Concept loss: ConceptHead predicts composition values that should correlate with rewards
            concept_loss = None
            if hasattr(brain, 'use_concept_head') and brain.use_concept_head and hasattr(brain, 'concept_head'):
                brain.train()
                # Get hidden state for concept head (recompute forward to get hidden)
                h = F.relu(brain.fc1(states_t))
                h = brain.dropout(h)
                if brain.use_attention:
                    if h.dim() == 2:
                        h = h.unsqueeze(1)
                    attn_out = brain.attention(h, vp_value=vp_val)
                    h = brain.attention_norm(h + attn_out)
                    h = h.squeeze(1)
                h = F.relu(brain.fc2(h))
                h = brain.dropout(h)
                
                # Get concept predictions
                concept_out = brain.concept_head(h)
                composition_values = concept_out['composition_value']  # (batch, num_compositions)
                
                # Loss: predicted composition values should predict rewards
                # Average composition value should approximate reward signal
                predicted_reward = composition_values.mean(dim=-1)
                concept_loss = F.mse_loss(predicted_reward, rewards_t)

            loss = self.rl_weight * rl_loss
            if lang_loss is not None:
                loss = loss + self.lang_weight * lang_loss
            if concept_loss is not None:
                loss = loss + self.concept_weight * concept_loss

            opt.zero_grad()
            loss.backward()
            opt.step()

            total += loss.item()
            trained += 1

        if trained > 0:
            self.training_step += 1
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            return total / trained
        return 0.0

    def _get_semantic_related(self, word: str, min_strength: float = 0.3) -> List[str]:
        """Get semantically related words from knowledge web."""
        if not self.knowledge_web:
            return []
        concepts = self.knowledge_web.get('concepts', {})
        # Simple word association: return words in same category
        word_info = concepts.get(word.lower(), {})
        category = word_info.get('category', '')
        related = []
        if category:
            for w, info in concepts.items():
                if info.get('category') == category and w != word.lower():
                    related.append((w, info.get('confidence', 0.5)))
        related.sort(key=lambda x: x[1], reverse=True)
        return [w for w, s in related[:10] if s >= min_strength]

    def generate_response(self, prompt: str, organism_idx: int = 0, max_tokens: int = 128,
                          vp_value: Optional[float] = None, temperature: float = 1.0) -> Tuple[str, float]:
        """Generate response with semantic boosting and confidence. Returns (response, confidence).
        
        NEURAL SYNAPSE MODE: max_tokens=128 allows rich causation chains!"""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        if not brain.use_language_head:
            return "[No language head available]", 0.1
        
        tokens = self.tokenize(prompt)
        id_to_word = {int(k): v for k, v in self.vocabulary.get('id_to_word', {}).items()}
        word_to_id = self.vocabulary.get('word_to_id', {})
        
        actual_vocab_size = len(id_to_word)
        if actual_vocab_size == 0:
            return "[Empty vocabulary]", 0.1
        
        valid_ids = [i for i in range(5, actual_vocab_size) if i in id_to_word and id_to_word[i] not in ['<PAD>', '<UNK>', '<START>', '<END>', '<VP_GATE>']]
        if not valid_ids:
            return "[No valid words in vocabulary]", 0.1
        
        # Build semantic primes from input
        input_semantic_primes = set()
        input_words = prompt.lower().split()
        for word in input_words:
            if word in word_to_id:
                input_semantic_primes.add(word)
            related = self._get_semantic_related(word, min_strength=0.5)
            input_semantic_primes.update(related[:3])
        
        brain.eval()
        generated: List[int] = []
        recent_tokens: List[int] = []
        confidence_scores: List[float] = []
        
        state = np.zeros(brain.input_dim, dtype=np.float32)
        for i, tok in enumerate(tokens[-brain.input_dim:]):
            state[i] = tok / 1000.0
        
        # Get base logits once
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            _, base_lang_logits = brain(state_t, vp_value=vp_value, return_language_logits=True)
        if base_lang_logits is None:
            return "[No language output]", 0.1
        
        base_logits = base_lang_logits.squeeze(0).cpu().numpy()
        
        # Initial semantic priming
        if input_semantic_primes:
            initial_boost = 0.8
            for prime_word in input_semantic_primes:
                prime_token = word_to_id.get(prime_word.lower())
                if prime_token is not None and prime_token < len(base_logits):
                    base_logits[prime_token] += initial_boost
        
        # Generation loop with semantic boosting
        for step in range(max_tokens):
            logits = base_logits.copy()
            logits = logits / max(0.1, temperature)
            
            # Tiered repetition penalty
            strong_penalty = 3.0
            moderate_penalty = 1.5
            if recent_tokens:
                for i, prev_token in enumerate(recent_tokens):
                    recency = len(recent_tokens) - i
                    if prev_token < len(logits):
                        if recency <= 2:
                            logits[prev_token] -= strong_penalty
                        else:
                            logits[prev_token] -= moderate_penalty
            
            # Semantic boosting from last generated word
            if self.knowledge_web and generated:
                last_token = generated[-1]
                last_word = id_to_word.get(last_token, '')
                if last_word:
                    related = self._get_semantic_related(last_word, min_strength=0.3)
                    semantic_boost = 0.5
                    for related_word in related[:5]:
                        related_token = word_to_id.get(related_word.lower())
                        if related_token and related_token < len(logits):
                            if related_token not in recent_tokens:
                                logits[related_token] += semantic_boost
            
            # Mask special tokens
            logits[:5] = -1e9
            if actual_vocab_size < len(logits):
                logits[actual_vocab_size:] = -1e9
            
            # Top-k sampling
            top_k = 50
            valid_logits = np.array([logits[i] if i < len(logits) else -1e9 for i in valid_ids])
            top_k_indices = np.argsort(valid_logits)[-top_k:]
            mask = np.full(len(valid_ids), -1e9)
            mask[top_k_indices] = valid_logits[top_k_indices]
            
            # Softmax and sample
            probs = np.exp(mask - np.max(mask))
            probs = probs / (probs.sum() + 1e-9)
            chosen_idx = np.random.choice(len(valid_ids), p=probs)
            next_token = valid_ids[chosen_idx]
            
            confidence_scores.append(float(probs[chosen_idx]))
            
            word = id_to_word.get(next_token, '<UNK>')
            if word in ['<END>', '<PAD>']:
                break
            
            generated.append(next_token)
            recent_tokens.append(next_token)
            if len(recent_tokens) > 8:
                recent_tokens.pop(0)
            
            if len(generated) >= max_tokens:
                break
        
        # Calculate overall confidence
        if confidence_scores:
            avg_conf = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_conf = 0.1
        
        # Diversity bonus
        unique_tokens = len(set(generated))
        diversity = unique_tokens / max(len(generated), 1)
        confidence = (avg_conf * 0.4 + diversity * 0.6)
        
        words = [id_to_word.get(t, '<UNK>') for t in generated]
        return ' '.join(words) if words else "[Empty response]", confidence

    def export_cocoon(self, output_path: str):
        import zlib
        new_brain_data = []
        for brain in self.brains:
            buf = BytesIO()
            torch.save(brain.state_dict(), buf)
            compressed = zlib.compress(buf.getvalue(), level=9)
            new_brain_data.append(base64.b64encode(compressed).decode('ascii'))
        with open(__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        import re
        brain_data_py = "[\n" + ",\n".join(f'    "{b}"' for b in new_brain_data) + "\n]"
        source = re.sub(r'_BRAIN_DATA = \[.*?\]', f'_BRAIN_DATA = {brain_data_py}', source, flags=re.DOTALL)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(source)
        print(f"[OK] Exported updated cocoon to: {output_path}")

    def export_onnx(self, output_path: str, organism_idx: int = 0):
        """Export a brain as ONNX file for Netron visualization."""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        brain.eval()
        
        dummy_input = torch.randn(1, brain.input_dim).to(self.device)
        
        try:
            torch.onnx.export(
                brain,
                dummy_input,
                output_path,
                export_params=True,
                opset_version=14,
                do_constant_folding=True,
                input_names=['state'],
                output_names=['action_probs', 'language_logits'] if brain.use_language_head else ['action_probs'],
                dynamic_axes={
                    'state': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'},
                }
            )
            print(f"[OK] Exported ONNX model to: {output_path}")
            print(f"     View at: https://netron.app/")
            return True
        except Exception as e:
            print(f"[!] ONNX export failed: {e}")
            return False

    def export_torchscript(self, output_path: str, organism_idx: int = 0):
        """Export a brain as TorchScript file for Netron visualization."""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        brain.eval()
        
        try:
            # Use trace instead of script - more compatible with complex models
            input_dim = getattr(brain, 'input_dim', 24)
            dummy_input = torch.randn(1, input_dim)
            traced = torch.jit.trace(brain, (dummy_input,))
            traced.save(output_path)
            print(f"[OK] Exported TorchScript model to: {output_path}")
            print(f"     View at: https://netron.app/")
            return True
        except Exception as e:
            print(f"[!] TorchScript export failed: {e}")
            return False

    def export_package(self, output_dir: str):
        """
        Export a complete Netron-viewable package:
        - brain_ensemble.onnx (or brain_0.onnx, brain_1.onnx, ...)
        - README.md with model card
        - vocabulary.json
        - metadata.json
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export each brain as ONNX
        onnx_files = []
        for i, (brain, name) in enumerate(zip(self.brains, self.organism_names)):
            onnx_path = os.path.join(output_dir, f"brain_{name}.onnx")
            if self.export_onnx(onnx_path, organism_idx=i):
                onnx_files.append(f"brain_{name}.onnx")
        
        # Export vocabulary
        vocab_path = os.path.join(output_dir, "vocabulary.json")
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, indent=2)
        print(f"[OK] Exported vocabulary to: {vocab_path}")
        
        # Export metadata
        metadata = {
            'mode': 'ENSEMBLE' if self.is_ensemble else 'SOLO',
            'num_organisms': len(self.brains),
            'organism_names': self.organism_names,
            'organism_fitness': self.organism_fitness,
            'vocab_size': len(self.vocabulary.get('word_to_id', {})),
            'architecture': self.architecture,
            'training_config': self.config,
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"[OK] Exported metadata to: {meta_path}")
        
        # Generate README
        readme = self._generate_readme(onnx_files, metadata)
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        print(f"[OK] Generated README to: {readme_path}")
        
        print(f"\n✅ Package exported to: {output_dir}")
        print(f"   Open .onnx files at https://netron.app/ to visualize")

    def _generate_readme(self, onnx_files: List[str], metadata: Dict[str, Any]) -> str:
        """Generate a model card README for the cocoon package."""
        import datetime
        
        organism_table = "| Organism | Fitness | Input Dim | Hidden Dim | Output Dim | Language Head |\n"
        organism_table += "|----------|---------|-----------|------------|------------|---------------|\n"
        
        for i, cfg in enumerate(metadata['architecture'].get('brain_configs', [])):
            name = cfg.get('organism_id', f'org_{i}')
            fitness = metadata['organism_fitness'][i] if i < len(metadata['organism_fitness']) else 1.0
            organism_table += f"| {name} | {fitness:.3f} | {cfg.get('input_dim', 24)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {'✅' if cfg.get('use_language_head') else '❌'} |\n"
        
        readme = f"""# 🦋 Butterfly Cocoon - Neural Network Model Card

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Model Overview

| Property | Value |
|----------|-------|
| Mode | {metadata['mode']} |
| Organisms | {metadata['num_organisms']} |
| Vocabulary Size | {metadata['vocab_size']} words |
| Total Parameters | ~{sum(sum(p.numel() for p in brain.parameters()) for brain in self.brains):,} |

---

## 🧠 Organism Architectures

{organism_table}

---

## 🔬 Network Architecture

Each organism brain consists of:

```
Input (state vector)
    ↓
FC1: Linear(input_dim → hidden_dim) + ReLU + Dropout
    ↓
[Optional] Multi-Head Self-Attention (VP-aware)
    ↓
FC2: Linear(hidden_dim → hidden_dim) + ReLU + Dropout
    ↓
├── FC3: Linear(hidden_dim → output_dim) → Action Probabilities
│
└── [Optional] FC_Language: Linear(hidden_dim → vocab_size) → Language Logits
```

### VP-Aware Attention

The attention mechanism scales scores by Voting Power:
```
attention_scores = (Q @ K.T) / sqrt(d_k) / (1 + vp_value)
```

This allows organisms to modulate their attention based on resource availability.

---

## 📁 Files in This Package

| File | Description |
|------|-------------|
| `README.md` | This model card |
| `metadata.json` | Full architecture and training config |
| `vocabulary.json` | Token vocabulary (word ↔ ID mapping) |
"""
        
        for onnx_file in onnx_files:
            readme += f"| `{onnx_file}` | ONNX model - open at [netron.app](https://netron.app/) |\n"
        
        readme += f"""
---

## 🔍 Visualize with Netron

1. Go to [https://netron.app/](https://netron.app/)
2. Click "Open Model..." or drag-drop an `.onnx` file
3. Explore the neural network architecture

---

## 🚀 Usage

### As Standalone Python

```bash
# Info mode
python cocoon.py --mode info

# Interactive chat
python cocoon.py --mode chat

# OpenAI Gym training
python cocoon.py --mode gym --env CartPole-v1 --episodes 100

# HTTP API server
python cocoon.py --mode serve --port 8080
```

### Load ONNX in Python

```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("brain_org_001.onnx")
state = np.random.randn(1, 24).astype(np.float32)
outputs = session.run(None, {{"state": state}})
action_probs = outputs[0]
```

---

## 📚 Training Configuration

```json
{json.dumps(metadata['training_config'], indent=2)}
```

---

## 🦋 About Butterfly System

The Butterfly System is an evolutionary neural network framework where organisms:
- Evolve through **Highlander battles** (absorption of defeated opponents)
- Form **alliances** for collective survival
- Develop **emergent language** through atomic vocabulary
- Graduate to **cocoons** when proven fit

Learn more: [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)

---

## ⚖️ Attribution

- **Proton Game Arena**: Inspired by Piers Anthony's "Apprentice Adept" (1980-1990)
- **Absorption Mechanic**: Inspired by "Highlander" (1986), dir. Russell Mulcahy
- **Convergence Engine**: [https://github.com/Yufok1/Convergence_Engine](https://github.com/Yufok1/Convergence_Engine)
"""
        
        return readme


# Optional Gym adapter
class GymRunner:
    def __init__(self, agent: CocoonAgent):
        self.agent = agent

    def run(self, env_name: str, episodes: int = 100, render: bool = False, learn: bool = True):
        try:
            import gymnasium as gym
        except ImportError:
            try:
                import gym
            except ImportError:
                print("[!] Gymnasium not found. Install with: pip install gymnasium")
                return

        env = gym.make(env_name, render_mode='human' if render else None)
        
        # Get environment's action space size
        action_space_size = None
        if hasattr(env.action_space, 'n'):
            action_space_size = env.action_space.n
            print(f"[INFO] Environment action space: {action_space_size} (brain has {self.agent.brains[0].output_dim})")
        
        all_rewards = []
        for ep in range(episodes):
            obs, _ = env.reset()
            if isinstance(obs, dict):
                obs = np.array(list(obs.values())).flatten()
            obs = np.asarray(obs, dtype=np.float32).flatten()
            done = False
            ep_reward = 0.0
            while not done:
                action = self.agent.get_action(obs, explore=learn, action_space_size=action_space_size)
                result = env.step(action)
                if len(result) == 5:
                    next_obs, reward, terminated, truncated, info = result
                    done = terminated or truncated
                else:
                    next_obs, reward, done, info = result
                if isinstance(next_obs, dict):
                    next_obs = np.array(list(next_obs.values())).flatten()
                next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
                if learn:
                    self.agent.add_experience(obs, action, reward, next_obs, done)
                    if len(self.agent.experience_buffers[0]) >= self.agent.batch_size:
                        self.agent.train_step()
                obs = next_obs
                ep_reward += reward
            all_rewards.append(ep_reward)
            if (ep + 1) % 10 == 0:
                avg = np.mean(all_rewards[-10:])
                print(f"  Episode {ep+1:4d}: reward={ep_reward:7.1f}, avg10={avg:7.1f}, ε={self.agent.epsilon:.3f}")
        env.close()
        print(f"\n✅ Completed {episodes} episodes")
        print(f"   Mean reward: {np.mean(all_rewards):.2f}")
        print(f"   Best reward: {np.max(all_rewards):.2f}")


# Optional HTTP server
def run_http_server(agent: CocoonAgent, port: int = 8080):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("[!] Flask not found. Install with: pip install flask")
        return

    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'organisms': len(agent.brains)})

    @app.route('/act', methods=['POST'])
    def act():
        data = request.json
        state = np.array(data.get('state', []), dtype=np.float32)
        explore = data.get('explore', False)
        action = agent.get_action(state, explore=explore)
        return jsonify({'action': action})

    @app.route('/learn', methods=['POST'])
    def learn():
        data = request.json
        agent.add_experience(
            np.array(data['state'], dtype=np.float32),
            data['action'],
            data['reward'],
            np.array(data['next_state'], dtype=np.float32),
            data['done']
        )
        loss = agent.train_step()
        return jsonify({'loss': loss, 'step': agent.training_step})

    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.json
        prompt = data.get('prompt', '')
        learn = data.get('learn', True)
        
        # Learn from input if enabled
        if learn and prompt:
            agent.learn_from_text(prompt, reward=0.1)
            if len(agent.experience_buffers[0]) >= agent.batch_size:
                agent.train_step()
        
        # Get responses from all organisms with confidence
        responses = []
        for i, name in enumerate(agent.organism_names):
            response, confidence = agent.generate_response(prompt, organism_idx=i)
            fitness = agent.organism_fitness[i] if i < len(agent.organism_fitness) else 1.0
            weight = fitness * confidence
            responses.append({
                'organism': name,
                'response': response,
                'confidence': confidence,
                'fitness': fitness,
                'weight': weight
            })
        
        # Select best response using decision matrix
        valid = [r for r in responses if r['response'].strip() and not r['response'].startswith('[')]
        if valid:
            best = max(valid, key=lambda r: r['weight'])
            final_response = best['response']
        else:
            final_response = responses[0]['response'] if responses else ''
        
        return jsonify({
            'response': final_response,
            'all_responses': responses,
            'vocab_size': len(agent.vocabulary.get('word_to_id', {}))
        })

    @app.route('/teach', methods=['POST'])
    def teach():
        """Teach the cocoon new words or concepts."""
        data = request.json
        text = data.get('text', '')
        reward = data.get('reward', 0.5)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        tokens = agent.learn_from_text(text, reward=reward)
        
        # Train if we have enough experiences
        loss = 0.0
        if len(agent.experience_buffers[0]) >= agent.batch_size:
            loss = agent.train_step()
        
        return jsonify({
            'tokens': tokens,
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
            'loss': loss
        })

    @app.route('/vocab', methods=['GET'])
    def get_vocab():
        """Get current vocabulary."""
        return jsonify({
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
            'words': list(agent.vocabulary.get('word_to_id', {}).keys())
        })

    print(f"\n🌐 HTTP API Server starting on port {port}")
    print(f"   Endpoints: /health, /act, /learn, /chat, /teach, /vocab")
    app.run(host='0.0.0.0', port=port)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🦋 Butterfly Cocoon - Self-Contained Learning Agent",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  python cocoon.py --mode chat
  python cocoon.py --mode gym --env CartPole-v1 --episodes 100
  python cocoon.py --mode serve --port 8080
  python cocoon.py --export updated_cocoon.py
  python cocoon.py --export-onnx brain.onnx
  python cocoon.py --export-package ./my_model
        """)
    parser.add_argument('--mode', choices=['chat', 'gym', 'serve', 'info'], default='info')
    parser.add_argument('--env', type=str, default='CartPole-v1')
    parser.add_argument('--episodes', type=int, default=100)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--no-learn', action='store_true')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--export', type=str, help='Export cocoon Python file')
    parser.add_argument('--export-onnx', type=str, help='Export ONNX model for Netron visualization')
    parser.add_argument('--export-package', type=str, help='Export full package (ONNX + README + metadata)')
    parser.add_argument('--organism', type=int, default=0, help='Organism index for ONNX export')
    parser.add_argument('--voting', choices=['majority', 'weighted', 'confidence'], default='confidence')
    args = parser.parse_args()

    arch = _decode_data(_ARCHITECTURE_B64)
    config = _decode_data(_TRAINING_CONFIG_B64)
    vocab = _decode_data(_VOCABULARY_B64)

    if args.mode == 'info':
        print("\n🦋 BUTTERFLY COCOON")
        print("=" * 50)
        print(f"Mode:       {'ENSEMBLE' if arch.get('is_ensemble') else 'SOLO'}")
        print(f"Organisms:  {arch.get('ensemble_size', 1)}")
        print(f"Names:      {', '.join(arch.get('organism_names', []))}")
        print(f"Vocabulary: {len(vocab.get('word_to_id', {}))} words")
        print("\nTraining Config:")
        for k, v in config.items():
            print(f"  {k}: {v}")
        print("\nExport Options:")
        print("  --export <file.py>      Export updated cocoon")
        print("  --export-onnx <file>    Export ONNX for Netron")
        print("  --export-package <dir>  Export full package")
        print("\nUse --mode chat/gym/serve to run the agent")
        return

    if not TORCH_AVAILABLE:
        print("[!] PyTorch required for agent modes")
        return

    agent = CocoonAgent(voting=args.voting)

    if args.export:
        agent.export_cocoon(args.export)
        return

    if args.export_onnx:
        agent.export_onnx(args.export_onnx, organism_idx=args.organism)
        return

    if args.export_package:
        agent.export_package(args.export_package)
        return

    if args.mode == 'chat':
        print("\n🦋 Butterfly Cocoon - Interactive Chat")
        print("=" * 60)
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║ BUTTERFLY PIPELINE: Tokenomic Decision Matrix Active      ║")
        print("║ Commands: 'quit' to exit, 'export <file>' to save         ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print()
        initial_vocab = len(agent.vocabulary.get('word_to_id', {}))
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input.lower() == 'quit':
                break
            if user_input.lower().startswith('export '):
                agent.export_cocoon(user_input[7:].strip())
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: MESSAGE RECEIVED
            # ═══════════════════════════════════════════════════════════════
            print()
            print("┌─── STEP 1: MESSAGE ───────────────────────────────────────┐")
            print(f"│ Input: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 2: TOKENIZATION
            # ═══════════════════════════════════════════════════════════════
            input_tokens = agent.tokenize(user_input)
            print("┌─── STEP 2: TOKENIZATION ────────────────────────────────────┐")
            print(f"│ Tokens: {len(input_tokens)} │ IDs: {input_tokens[:8]}{'...' if len(input_tokens) > 8 else ''}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # Learn from user input
            agent.learn_from_text(user_input, reward=0.1)
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 3: ORGANISM SELECTION
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 3: SELECTION ───────────────────────────────────────┐")
            num_orgs = len(agent.brains)
            print(f"│ Strategy: FITNESS_WEIGHTED │ Organisms: {num_orgs}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 4: GENERATION (per-organism with detailed decision matrix)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 4: GENERATION ──────────────────────────────────────┐")
            print("│ Decision Matrix: weight = fitness × confidence × gene_mod")
            print("├────────────────────────────────────────────────────────────┤")
            
            responses = []
            
            for i, name in enumerate(agent.organism_names):
                response, confidence = agent.generate_response(user_input, organism_idx=i)
                fitness = agent.organism_fitness[i] if i < len(agent.organism_fitness) else 1.0
                
                # Granular decision matrix (matching main Butterfly Chat)
                # 1. Base weight from fitness × confidence
                base_weight = fitness * confidence
                
                # 2. Genetic diversity modifier (if available)
                gene_modifier = 1.0
                if hasattr(agent, 'organism_metadata') and i < len(agent.organism_metadata):
                    meta = agent.organism_metadata[i]
                    if 'gene_variance' in meta:
                        # More genetic diversity = slight weight bonus (max 20%)
                        gene_modifier = 1.0 + min(meta['gene_variance'] / 50000.0, 0.2)
                
                # 3. Response quality modifier
                response_modifier = 1.0
                if response.strip():
                    # Non-empty response bonus
                    word_count = len(response.split())
                    if word_count >= 1:
                        response_modifier = 1.0 + min(word_count * 0.05, 0.15)  # Max 15% bonus
                
                # Final weight with all modifiers
                weight = base_weight * gene_modifier * response_modifier
                
                responses.append({
                    'name': name,
                    'response': response,
                    'confidence': confidence,
                    'fitness': fitness,
                    'gene_mod': gene_modifier,
                    'resp_mod': response_modifier,
                    'weight': weight
                })
                
                # Show individual organism response with granular breakdown
                print(f"│ [{name}]")
                print(f"│   conf={confidence:.3f} × fit={fitness:.2f} × gene={gene_modifier:.2f} × resp={response_modifier:.2f}")
                print(f"│   = weight {weight:.4f}")
                print(f"│   → {response[:40]}{'...' if len(response) > 40 else ''}")
            
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 5: AGGREGATION (Granular Decision Matrix Summary)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 5: AGGREGATION ─────────────────────────────────────┐")
            
            # Filter empty responses
            valid_responses = [r for r in responses if r['response'].strip() and not r['response'].startswith('[')]
            total_weight = sum(r['weight'] for r in valid_responses)
            
            if valid_responses:
                # Sort by weight descending
                sorted_responses = sorted(valid_responses, key=lambda r: r['weight'], reverse=True)
                best = sorted_responses[0]
                final_response = best['response']
                
                # Show granular decision matrix summary
                print(f"│ Aggregation: WEIGHTED_SELECTION")
                print(f"│ Total Weight Pool: {total_weight:.4f}")
                print(f"├────────────────────────────────────────────────────────────┤")
                print(f"│ 🏆 WINNER: [{best['name']}]")
                print(f"│    Weight: {best['weight']:.4f} ({best['weight']/total_weight*100:.1f}% of pool)")
                print(f"│    Breakdown: conf={best['confidence']:.3f} × fit={best['fitness']:.2f}")
                if 'gene_mod' in best:
                    print(f"│               × gene={best['gene_mod']:.2f} × resp={best['resp_mod']:.2f}")
                print(f"├────────────────────────────────────────────────────────────┤")
                print(f"│ Runners-up:")
                for i, r in enumerate(sorted_responses[1:4], 2):  # Show top 3 runners-up
                    pct = r['weight']/total_weight*100 if total_weight > 0 else 0
                    print(f"│   #{i} [{r['name']}] weight={r['weight']:.4f} ({pct:.1f}%)")
            else:
                final_response = "[No valid response from organisms]"
                best = None
                print(f"│ No valid responses to aggregate")
            
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 6: CAUSATION (Event Tracking)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 6: CAUSATION ───────────────────────────────────────┐")
            print(f"│ Event: CHAT_RESPONSE")
            print(f"│ Organisms Queried: {num_orgs}")
            print(f"│ Valid Responses: {len(valid_responses)}")
            print(f"│ Winner: {best['name'] if best else 'none'}")
            if best:
                print(f"│ Winner Weight: {best['weight']:.4f}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 7: COMPLETE
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 7: COMPLETE ────────────────────────────────────────┐")
            print(f"│ Final Response:")
            print(f"└────────────────────────────────────────────────────────────┘")
            print()
            print(f"🦋 Cocoon: {final_response}")
            
            # Train on accumulated experiences
            if len(agent.experience_buffers[0]) >= agent.batch_size:
                loss = agent.train_step()
                if loss > 0:
                    print(f"\n  [📈 Training: loss={loss:.4f}, step={agent.training_step}]")
        
        # Show vocabulary growth
        final_vocab = len(agent.vocabulary.get('word_to_id', {}))
        if final_vocab > initial_vocab:
            print(f"\n📚 Vocabulary grew: {initial_vocab} → {final_vocab} words (+{final_vocab - initial_vocab})")
            print("   Export the cocoon to save learned words!")

    elif args.mode == 'gym':
        runner = GymRunner(agent)
        runner.run(args.env, episodes=args.episodes, render=args.render, learn=not args.no_learn)
        if not args.no_learn:
            save = input("\nSave updated cocoon? (y/N): ").strip().lower()
            if save == 'y':
                agent.export_cocoon('cocoon_trained.py')

    elif args.mode == 'serve':
        run_http_server(agent, port=args.port)


if __name__ == "__main__":
    main()
''')

        source = template.substitute(
            MODE_COMMENT=mode_comment,
            ORGANISMS=", ".join(organism_names),
            GENERATED_TS=generated_timestamp,
            BRAIN_DATA=brain_data_py,
            ARCH_B64=arch_b64,
            VOCAB_B64=vocab_b64,
            KW_B64=kw_b64,
            CONFIG_B64=config_b64,
            DATA_COMPRESSED=str(compressed)
        )
        return source

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
        'vocab_size': 1000,
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
