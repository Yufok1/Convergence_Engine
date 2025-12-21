"""Debug the Cocoon/Export system by testing real operations."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print('=== REAL-WORLD COCOON SYSTEM TEST ===')
print()

# Step 1: Try to import everything
print('[1] Testing imports...')
try:
    from reality_simulator.agent_compiler import AgentCompiler
    print('  OK: AgentCompiler')
except Exception as e:
    print(f'  FAIL: AgentCompiler - {e}')

try:
    from reality_simulator.checkpointing.organism_capsule import OrganismCapsule, NeuralSnapshot
    print('  OK: OrganismCapsule, NeuralSnapshot')
except Exception as e:
    print(f'  FAIL: Capsule imports - {e}')

try:
    from reality_simulator.portable_agent.bridge import AgentBridge
    print('  OK: AgentBridge')
except Exception as e:
    print(f'  FAIL: AgentBridge - {e}')

# Step 2: Create a real organism and try to export it
print()
print('[2] Creating test organism with brain...')
brain = None
try:
    from reality_simulator.neural.brain import OrganismBrain
    import torch
    
    brain = OrganismBrain(
        input_dim=30,  # Matches config.json
        hidden_dim=128, 
        output_dim=6,
        vocab_size=1000,
        use_language_head=True
    )
    print(f'  OK: Brain created (params={sum(p.numel() for p in brain.parameters())})')
except Exception as e:
    print(f'  FAIL: Brain creation - {e}')

# Step 3: Try to compile to different formats
print()
print('[3] Testing AgentCompiler.compile_organism...')
if brain:
    try:
        compiler = AgentCompiler()
        
        # Create a mock organism-like object
        class MockOrganism:
            def __init__(self, brain):
                self.brain = brain
                self.organism_id = 'test_org_001'
                self.id = 'test_org_001'
                self.fitness = 0.75
        
        mock_org = MockOrganism(brain)
        
        # Try ONNX export
        print('  Trying ONNX export...')
        result = compiler.compile_organism(mock_org, format='onnx')
        result_info = result.keys() if isinstance(result, dict) else 'not a dict'
        print(f'    Result type: {type(result)}')
        print(f'    Result keys: {result_info}')
    except Exception as e:
        import traceback
        print(f'  FAIL: {type(e).__name__}: {e}')
        traceback.print_exc()

# Step 4: Check if there are any existing capsule files we can try to load
print()
print('[4] Looking for existing capsule files...')
import os
from pathlib import Path

capsule_dirs = [
    'data/capsules',
    'data/highlander',
    'checkpoints',
]

found_capsules = []
for d in capsule_dirs:
    p = Path(d)
    if p.exists():
        files = list(p.glob('*.json')) + list(p.glob('*.capsule'))
        print(f'  {d}: {len(files)} files')
        for f in files[:3]:
            print(f'    - {f.name}')
            found_capsules.append(f)
    else:
        print(f'  {d}: (not found)')

# Step 5: Try to load a capsule if we found any
print()
print('[5] Testing capsule loading...')
if found_capsules:
    capsule_file = found_capsules[0]
    print(f'  Trying to load: {capsule_file}')
    try:
        import json
        with open(capsule_file, 'r') as f:
            data = json.load(f)
        print(f'    Loaded JSON, keys: {list(data.keys())[:10]}')
        
        # Try to create OrganismCapsule from it
        try:
            capsule = OrganismCapsule.from_dict(data)
            print(f'    OK: Created OrganismCapsule')
            print(f'    organism_id: {capsule.organism_id}')
        except Exception as e:
            print(f'    FAIL creating capsule: {type(e).__name__}: {e}')
    except Exception as e:
        print(f'  FAIL loading file: {e}')
else:
    print('  No capsule files found to test')

# Step 6: Try to create a capsule from scratch with CORRECT API
print()
print('[6] Testing capsule creation with correct API...')
try:
    import base64
    import torch
    from io import BytesIO
    
    # Create brain state bytes
    state_buffer = BytesIO()
    torch.save(brain.state_dict(), state_buffer, _use_new_zipfile_serialization=True)
    state_bytes = state_buffer.getvalue()
    
    # Create NeuralSnapshot with ACTUAL required fields
    print('  Creating NeuralSnapshot...')
    print(f'    Required fields: {NeuralSnapshot.__dataclass_fields__.keys()}')
    
    neural_snap = NeuralSnapshot(
        state_dict_bytes=state_bytes,
        architecture_hash='test_hash_001',
        hidden_size=128,
        num_layers=2,
        input_size=28,  # Matches config.json input_dim=28
        output_size=6,
        total_parameters=sum(p.numel() for p in brain.parameters()),
        training_steps=0
    )
    print(f'  OK: NeuralSnapshot created')
    
    # Create OrganismCapsule with ACTUAL required fields
    print('  Creating OrganismCapsule...')
    print(f'    Required fields: {[f for f in OrganismCapsule.__dataclass_fields__.keys()][:10]}...')
    
    capsule = OrganismCapsule(
        organism_id='test_org_001',
        capsule_id='cap_test_001',
        neural=neural_snap
    )
    print(f'  OK: OrganismCapsule created')
    print(f'    organism_id: {capsule.organism_id}')
    print(f'    has neural: {capsule.neural is not None}')
    
except Exception as e:
    import traceback
    print(f'  FAIL: {type(e).__name__}: {e}')
    traceback.print_exc()

# Step 7: Try the full compile->export->load cycle
print()
print('[7] Testing full export cycle...')
if brain:
    try:
        compiler = AgentCompiler()
        
        # Check what methods are available
        methods = [m for m in dir(compiler) if not m.startswith('_')]
        print(f'  Compiler methods: {methods[:10]}...')
        
        # Try compile_to_archive if it exists
        if hasattr(compiler, 'compile_to_archive'):
            print('  Found compile_to_archive, trying...')
            # This needs a proper organism or capsule
        elif hasattr(compiler, 'compile_organism'):
            print('  Found compile_organism, trying...')
        elif hasattr(compiler, 'compile'):
            print('  Found compile, trying...')
            
    except Exception as e:
        import traceback
        print(f'  FAIL: {type(e).__name__}: {e}')
        traceback.print_exc()

print()
print('=== TEST COMPLETE ===')
