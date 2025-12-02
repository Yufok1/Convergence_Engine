#!/usr/bin/env python
"""Test TorchScript export with fallback to tracing."""

from reality_simulator.neural.brain import OrganismBrain
import torch

print("Testing TorchScript export (script -> trace fallback)...")
brain = OrganismBrain(input_dim=24, output_dim=32)
print(f"✓ Brain created")

# Test forward pass
x = torch.randn(4, 24)
out = brain(x)
print(f"✓ Forward pass works: {out.shape}")

# Test torch.jit.script
print("\n--- Trying torch.jit.script ---")
try:
    scripted = torch.jit.script(brain)
    out_scripted = scripted(x)
    print(f"✓ torch.jit.script SUCCESS: {out_scripted.shape}")
except Exception as e:
    print(f"✗ torch.jit.script failed: {type(e).__name__}")
    
    # Try tracing
    print("\n--- Falling back to torch.jit.trace ---")
    try:
        traced = torch.jit.trace(brain, (x,))
        out_traced = traced(x)
        print(f"✓ torch.jit.trace SUCCESS: {out_traced.shape}")
    except Exception as trace_error:
        print(f"✗ torch.jit.trace also failed: {trace_error}")
