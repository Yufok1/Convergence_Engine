"""Test BytesIO TorchScript save/load."""
from io import BytesIO
import torch
import sys
import os

# Add reality_simulator to path
rs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reality_simulator')
print(f"Adding to path: {rs_path}")
sys.path.insert(0, rs_path)

from neural.brain import OrganismBrain

# Create brain
brain = OrganismBrain(input_dim=64, hidden_dim=128, output_dim=10)
brain.eval()

# Test BytesIO export (web UI path)
buffer = BytesIO()
dummy_input = torch.randn(1, 64, dtype=torch.float32)
traced = torch.jit.trace(brain, (dummy_input,))
torch.jit.save(traced, buffer)
buffer.seek(0)
print(f'BytesIO export: SUCCESS ({len(buffer.getvalue())} bytes)')

# Load it back
loaded = torch.jit.load(buffer)
out = loaded(dummy_input)
print(f'Reload + inference: SUCCESS, output shape {out.shape}')

print('\n✅ BytesIO TorchScript working!')
