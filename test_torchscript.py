#!/usr/bin/env python
"""Test TorchScript compilation of brain."""

from reality_simulator.neural.brain import OrganismBrain
import torch

print("Testing TorchScript compilation...")
brain = OrganismBrain(input_dim=24, output_dim=32)
print(f"✓ Brain created: input_dim=24, output_dim=32")

# Test forward pass
x = torch.randn(4, 24)
out = brain(x)
print(f"✓ Forward pass works: input {x.shape} -> output {out.shape}")

# Test TorchScript compilation
try:
    scripted = torch.jit.script(brain)
    print("✓ TorchScript compilation: SUCCESS")
    
    # Test scripted forward pass
    out_scripted = scripted(x)
    print(f"✓ Scripted forward pass works: output {out_scripted.shape}")
    
except Exception as e:
    print(f"✗ TorchScript compilation FAILED:")
    print(f"  {type(e).__name__}: {str(e)[:500]}")
