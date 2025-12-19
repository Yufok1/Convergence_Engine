#!/usr/bin/env python3
"""
Test script to simulate what the web UI compile endpoint does.
This helps debug the "Failed to fetch" error.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

import time
from pathlib import Path
from io import BytesIO
from datetime import datetime

def test_web_compile_simulation():
    """Simulate the web compile endpoint flow."""
    
    print("=" * 60)
    print("Testing Web Compile Endpoint Simulation")
    print("=" * 60)
    
    # Step 1: Import the modules (lazy import like the web endpoint)
    print("\n[1] Importing modules...")
    try:
        from reality_simulator.agent_compiler import AgentCompiler
        from reality_simulator.checkpointing.organism_capsule import OrganismCapsuleManager
        print("    ✓ AgentCompiler imported")
        print("    ✓ OrganismCapsuleManager imported")
    except ImportError as e:
        print(f"    ✗ Import error: {e}")
        return False
    
    # Step 2: Create a mock organism (simulating what unified_system would return)
    print("\n[2] Creating mock organism...")
    try:
        from reality_simulator.neural.brain import OrganismBrain
        
        # Create a minimal mock organism
        class MockOrganism:
            def __init__(self):
                self.species_id = f"test_org_{int(time.time())}"
                self.birth_time = time.time()
                self.age = 42
                self.brain = OrganismBrain(
                    input_dim=28,
                    hidden_dim=64,
                    output_dim=6,
                    use_attention=True,
                    vocab_size=1000,
                    use_language_head=True
                )
                self.vitality = 75.0
                self.pleasure = 50.0
                self.fitness = 0.85
                self.traits = None
                self.atomic_language = None
                self.config_system = None
                self.highlander_stats = None
        
        mock_org = MockOrganism()
        print(f"    ✓ Mock organism created: {mock_org.species_id}")
        print(f"    ✓ Brain: {mock_org.brain}")
    except Exception as e:
        print(f"    ✗ Error creating mock organism: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Create capsule from organism (like the web endpoint does)
    print("\n[3] Creating capsule from organism...")
    try:
        capsule_manager = OrganismCapsuleManager(storage_dir=Path('test_capsules_temp'))
        capsule = capsule_manager.capture_organism(
            organism=mock_org,
            reason=f'compile_request_{datetime.now().isoformat()}',
            notes=f'Test capsule for web compile simulation',
            include_causation=False,  # No causation explorer in this test
            causation_explorer=None
        )
        if capsule:
            print(f"    ✓ Capsule created: {capsule.capsule_id}")
            print(f"    ✓ Organism ID: {capsule.organism_id}")
            print(f"    ✓ Neural snapshot: {capsule.neural is not None}")
        else:
            print("    ✗ Capsule creation returned None!")
            return False
    except Exception as e:
        print(f"    ✗ Error creating capsule: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Compile the capsule to agent archive (like the web endpoint does)
    print("\n[4] Compiling capsule to agent...")
    export_format = 'torchscript'  # Use torchscript since we know it works
    try:
        compiler = AgentCompiler()
        archive_buffer = compiler.compile_capsule_to_agent(capsule, export_format=export_format)
        print(f"    ✓ Compilation successful!")
        print(f"    ✓ Archive buffer type: {type(archive_buffer)}")
        print(f"    ✓ Archive buffer position: {archive_buffer.tell()}")
        archive_buffer.seek(0, 2)  # Go to end
        size = archive_buffer.tell()
        archive_buffer.seek(0)  # Go back to start
        print(f"    ✓ Archive size: {size / 1024:.1f} KB")
    except Exception as e:
        print(f"    ✗ Error compiling capsule: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Simulate send_file behavior
    print("\n[5] Simulating Flask send_file behavior...")
    try:
        # Flask's send_file reads from the buffer
        archive_buffer.seek(0)
        data = archive_buffer.read()
        print(f"    ✓ Read {len(data)} bytes from buffer")
        
        # Verify it's a valid ZIP
        import zipfile
        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            names = zf.namelist()
            print(f"    ✓ Valid ZIP with {len(names)} files:")
            for name in names:
                info = zf.getinfo(name)
                print(f"        - {name} ({info.file_size} bytes)")
    except Exception as e:
        print(f"    ✗ Error reading archive: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Save to file for verification
    print("\n[6] Saving archive to file...")
    try:
        archive_buffer.seek(0)
        output_path = Path('test_web_compile_output.zip')
        with open(output_path, 'wb') as f:
            f.write(archive_buffer.read())
        print(f"    ✓ Saved to: {output_path}")
        print(f"    ✓ File size: {output_path.stat().st_size / 1024:.1f} KB")
    except Exception as e:
        print(f"    ✗ Error saving file: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✓ All steps completed successfully!")
    print("  The web compile endpoint logic appears to work correctly.")
    print("  The issue may be with:")
    print("    - Organism retrieval from unified_system")
    print("    - CORS or browser security settings")
    print("    - Network timeout")
    print("    - Frontend JavaScript error handling")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = test_web_compile_simulation()
    sys.exit(0 if success else 1)
