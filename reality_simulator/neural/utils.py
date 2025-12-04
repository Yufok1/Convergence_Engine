"""
Neural System Utilities

Device detection, feature normalization, and other neural utilities.
"""

import numpy as np
from typing import Dict, Any, Optional
import platform
import shutil

# Try importing PyTorch
try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None


def get_device(device_preference: str = "cpu"):
    """
    Get PyTorch device, auto-detecting CUDA if available.
    
    Args:
        device_preference: "cpu" or "cuda"
        
    Returns:
        torch.device object, or None if PyTorch not available
    """
    if not PYTORCH_AVAILABLE:
        return None
    
    if device_preference == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def set_seed(seed: Optional[int] = None):
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed (None = no seed)
    """
    if not PYTORCH_AVAILABLE or seed is None:
        return
    
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


def normalize_features(features: np.ndarray, 
                       min_vals: Optional[np.ndarray] = None,
                       max_vals: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Normalize features to [0, 1] range.
    
    Args:
        features: Input features array
        min_vals: Minimum values for normalization (None = use feature min)
        max_vals: Maximum values for normalization (None = use feature max)
        
    Returns:
        Normalized features array
    """
    features = np.asarray(features, dtype=np.float32)
    
    if min_vals is None:
        min_vals = features.min(axis=0, keepdims=True)
    if max_vals is None:
        max_vals = features.max(axis=0, keepdims=True)
    
    # Avoid division by zero
    range_vals = max_vals - min_vals
    range_vals = np.where(range_vals == 0, 1.0, range_vals)
    
    normalized = (features - min_vals) / range_vals
    return np.clip(normalized, 0.0, 1.0)


def get_breath_features(breath_state: Optional[Dict[str, Any]]) -> np.ndarray:
    """
    Extract breath features for neural input.
    
    Args:
        breath_state: Breath state dictionary from BreathEngine
        
    Returns:
        Array of breath features [depth, phase_normalized, intensity]
    """
    if breath_state:
        phase = breath_state.get('phase', 0.0)
        # Normalize phase to [0, 1]
        phase_normalized = (phase % (2 * np.pi)) / (2 * np.pi)
        
        return np.array([
            breath_state.get('depth', 0.5),
            phase_normalized,
            breath_state.get('intensity', 1.0)
        ], dtype=np.float32)
    
    # Default values if breath state not available
    return np.array([0.5, 0.0, 1.0], dtype=np.float32)


# Global counter for brain creation progress tracking
_brain_creation_counter = {'count': 0, 'total': 0, 'logged_config': False}

def create_brain(config: Dict[str, Any], silent: bool = False):
    """
    Factory function for brain creation.
    
    Args:
        config: Neural configuration dictionary
        silent: If True, suppress per-brain logging (for batch creation)
        
    Returns:
        OrganismBrain instance, or None if PyTorch not available
    """
    global _brain_creation_counter
    
    if not PYTORCH_AVAILABLE:
        return None
    
    # Use absolute import to avoid relative import issues
    try:
        from .brain import OrganismBrain
    except (ImportError, ValueError):
        try:
            from reality_simulator.neural.brain import OrganismBrain
        except ImportError:
            # Last resort: direct import
            import sys
            import os
            neural_path = os.path.dirname(__file__)
            if neural_path not in sys.path:
                sys.path.insert(0, neural_path)
            from brain import OrganismBrain
    
    # Handle both full config and neural-only config being passed
    # Full config has: {'neural': {'brain': {...}, 'language_model': {...}}}
    # Neural-only config has: {'brain': {...}, 'language_model': {...}}
    if 'neural' in config:
        # Full config passed - extract neural section which contains both brain and language_model
        neural_section = config.get('neural', {})
        brain_config = neural_section.get('brain', {})
        language_config = neural_section.get('language_model', {})  # language_model is INSIDE neural
    else:
        # Neural-only config passed (neural section already extracted)
        brain_config = config.get('brain', {})
        language_config = config.get('language_model', {})
    
    # Extract language head settings
    use_language_head = language_config.get('enabled', False)
    vocab_size = language_config.get('vocabulary', {}).get('max_size', 50000)
    use_attention = language_config.get('attention', {}).get('enabled', False)
    num_attention_heads = language_config.get('attention', {}).get('num_heads', 4)
    attention_dim = language_config.get('attention', {}).get('attention_dim', 64)
    max_sequence_length = language_config.get('sequence', {}).get('max_length', 128)
    
    # Extract concept head settings (RCUS)
    if 'neural' in config:
        concept_config = config.get('neural', {}).get('concept_system', {})
    else:
        concept_config = config.get('concept_system', {})
    use_concept_head = concept_config.get('enabled', False)
    num_key_compositions = concept_config.get('num_key_compositions', 20)
    
    # Debug log for language/concept head creation (only once per batch, or if not silent)
    if not silent and not _brain_creation_counter['logged_config']:
        if use_language_head:
            print(f"[CREATE_BRAIN] ✅ Language head ENABLED (vocab_size={vocab_size}, attention={use_attention})")
        else:
            print(f"[CREATE_BRAIN] ⚠️ Language head DISABLED (language_model.enabled={language_config.get('enabled', 'not set')})")
        if use_concept_head:
            print(f"[CREATE_BRAIN] ✅ Concept head ENABLED (RCUS - {num_key_compositions} key compositions)")
        _brain_creation_counter['logged_config'] = True
    
    brain = OrganismBrain(
        input_dim=brain_config.get('input_dim', 24),
        hidden_dim=brain_config.get('hidden_dim', 64),
        output_dim=brain_config.get('output_dim', 6),
        activation=brain_config.get('activation', 'relu'),
        dropout=brain_config.get('dropout', 0.1),
        use_language_head=use_language_head,
        vocab_size=vocab_size,
        use_attention=use_attention,
        num_attention_heads=num_attention_heads,
        attention_dim=attention_dim,
        max_sequence_length=max_sequence_length,
        use_concept_head=use_concept_head,
        num_key_compositions=num_key_compositions
    )
    
    # Get device from config (default to cpu for larger vocab support)
    if 'neural' in config:
        device_preference = config.get('neural', {}).get('device', 'cpu')
    else:
        device_preference = config.get('device', 'cpu')
    device = get_device(device_preference)
    brain = brain.to(device)
    
    # Optimization: Compile brain for faster training/inference (PyTorch 2.0+)
    optimization_config = config.get('optimization', {})
    optimizations_applied = []
    
    # Only attempt to compile if PyTorch supports it and the platform/compiler is available.
    # On Windows, torch.inductor requires MSVC 'cl' to be installed; avoid compile when missing.
    can_compile = (
        PYTORCH_AVAILABLE and
        optimization_config.get('use_compile', True) and
        torch is not None and
        hasattr(torch, 'compile')
    )
    if can_compile:
        # Additional Windows compiler check
        if platform.system().lower().startswith('windows'):
            if shutil.which('cl') is None:
                # MSVC cl compiler not available, skip compile to avoid inductor errors
                can_compile = False

    if can_compile:
        compile_mode = optimization_config.get('compile_mode', 'reduce-overhead')
        try:
            brain = torch.compile(brain, mode=compile_mode)
            optimizations_applied.append(f"torch.compile({compile_mode})")
        except Exception:
            # Fallback if compilation fails (e.g., older PyTorch, unsupported ops)
            pass
    
    # Optimization: Enable scripted inference for faster action selection
    if optimization_config.get('use_scripted_inference', True):
        try:
            brain.enable_scripted_inference()
            optimizations_applied.append("scripted_inference")
        except Exception:
            # Fallback if scripting fails
            pass
    
    # Log optimizations if any were applied
    if optimizations_applied:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[NEURAL] Brain optimizations: {', '.join(optimizations_applied)}")
    
    return brain

