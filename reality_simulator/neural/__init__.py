"""
🧠 Neural System for Reality Simulator

Provides PyTorch-based neural networks for organisms, enabling learning
through reinforcement learning synchronized with the Breath Engine.

The neural system extends organisms with decision-making capabilities
while maintaining full backward compatibility.
"""

# Check for PyTorch availability
try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    # Create stub for type checking
    class nn:
        class Module:
            pass

__all__ = [
    'PYTORCH_AVAILABLE',
    'OrganismBrain',
    'NeuralOrganism',
    'NeuralTrainer',
    'ExperienceBuffer',
    'get_device',
]

# Lazy imports to avoid errors if PyTorch not available
if PYTORCH_AVAILABLE:
    from .brain import OrganismBrain
    from .neural_organism import NeuralOrganism
    from .trainer import NeuralTrainer
    from .experience import ExperienceBuffer
    from .utils import get_device
else:
    # Stub classes for when PyTorch is not available
    OrganismBrain = None
    NeuralOrganism = None
    NeuralTrainer = None
    ExperienceBuffer = None
    
    def get_device(device_preference: str = "cpu"):
        """Stub function when PyTorch not available"""
        return None

