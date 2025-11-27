"""
Neural System Utilities

Device detection, feature normalization, and other neural utilities.
"""

import numpy as np
from typing import Dict, Any, Optional

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


def create_brain(config: Dict[str, Any]):
    """
    Factory function for brain creation.
    
    Args:
        config: Neural configuration dictionary
        
    Returns:
        OrganismBrain instance, or None if PyTorch not available
    """
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
    
    brain_config = config.get('brain', {})
    brain = OrganismBrain(
        input_dim=brain_config.get('input_dim', 12),
        hidden_dim=brain_config.get('hidden_dim', 64),
        output_dim=brain_config.get('output_dim', 6),
        activation=brain_config.get('activation', 'relu'),
        dropout=brain_config.get('dropout', 0.1)
    )
    
    # Optimization: Compile brain for faster training/inference (PyTorch 2.0+)
    optimization_config = config.get('optimization', {})
    optimizations_applied = []
    
    if (PYTORCH_AVAILABLE and 
        optimization_config.get('use_compile', True) and 
        torch is not None and 
        hasattr(torch, 'compile')):
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

