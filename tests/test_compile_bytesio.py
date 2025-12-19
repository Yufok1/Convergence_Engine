"""Test AgentCompiler BytesIO TorchScript compile flow with real capsule."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reality_simulator'))

from agent_compiler import AgentCompiler
from checkpointing.organism_capsule import OrganismCapsuleManager
import zipfile
from io import BytesIO
from pathlib import Path

print("Loading real capsule from system...")

# Find existing capsules
capsule_dir = Path("reality_simulator/checkpointing/capsules")
if not capsule_dir.exists():
    capsule_dir = Path("capsules")

manager = OrganismCapsuleManager(str(capsule_dir) if capsule_dir.exists() else ".")

# List available capsules
capsules = manager.list_capsules()
print(f"Found {len(capsules)} capsules")

if not capsules:
    print("No capsules found - testing the _export_torchscript method directly...")
    from neural.brain import OrganismBrain
    import torch
    
    brain = OrganismBrain(input_dim=64, hidden_dim=128, output_dim=10)
    brain.eval()
    
    compiler = AgentCompiler()
    buffer = BytesIO()
    
    # Test _export_torchscript with BytesIO
    compiler._export_torchscript(brain, buffer)
    print(f"BytesIO export size: {len(buffer.getvalue())} bytes")
    
    # Verify it loads
    buffer.seek(0)
    loaded = torch.jit.load(buffer)
    out = loaded(torch.randn(1, 64))
    print(f"Reload + inference: output shape {out.shape}")
    print("\n✅ _export_torchscript BytesIO path working!")
else:
    # Use first available capsule
    capsule_id = capsules[0]['capsule_id']
    print(f"Using capsule: {capsule_id}")
    
    capsule = manager.load_capsule(capsule_id)
    
    compiler = AgentCompiler()
    result = compiler.compile_capsule_to_agent(
        capsule=capsule,
        export_format='torchscript',
        include_history=False
    )
    
    print(f"Result type: {type(result)}")
    print(f"Result size: {len(result.getvalue())} bytes")
    
    # Verify it's a valid ZIP
    result.seek(0)
    with zipfile.ZipFile(result, 'r') as zf:
        print(f"ZIP contents: {zf.namelist()}")
    
    print("\n✅ Full compile_capsule_to_agent BytesIO flow working!")
