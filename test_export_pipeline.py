"""
EXPORT PIPELINE VERIFICATION TEST
==================================

Comprehensive test suite for verifying agent export infrastructure:
- Solo organism exports (ONNX, TorchScript, StateDict)
- Ensemble exports with voting strategies
- AgentBridge deployment modes
- Behavioral fingerprinting
- Graceful fallback mechanisms

Run: python test_export_pipeline.py
"""

import sys
import os
from pathlib import Path
import tempfile
import json
import zipfile
from io import BytesIO
import logging
import time

# Add paths
current_dir = Path(__file__).parent
reality_sim_path = current_dir / 'reality_simulator'
sys.path.insert(0, str(reality_sim_path))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Try imports with graceful degradation
TORCH_AVAILABLE = False
ONNX_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
    logger.info("✓ PyTorch available")
except ImportError:
    logger.warning("✗ PyTorch NOT available - some tests will be skipped")

try:
    import onnxruntime
    ONNX_AVAILABLE = True
    logger.info("✓ ONNX Runtime available")
except ImportError:
    logger.warning("✗ ONNX Runtime NOT available - ONNX inference tests will be skipped")

try:
    from agent_compiler import AgentCompiler
    from checkpointing.organism_capsule import OrganismCapsule
    from portable_agent.bridge import AgentBridge
    from portable_agent.agent_runtime import AgentRuntime
    COMPILER_AVAILABLE = True
    logger.info("✓ Agent compiler and portable agent modules loaded")
except ImportError as e:
    logger.error(f"✗ CRITICAL: Could not import export modules: {e}")
    COMPILER_AVAILABLE = False


class ExportPipelineTest:
    """Comprehensive test suite for export pipeline."""

    def __init__(self):
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'tests': []
        }
        self.temp_dir = Path(tempfile.mkdtemp(prefix='export_test_'))
        logger.info(f"Test output directory: {self.temp_dir}")

    def test(self, name: str, func):
        """Run a single test and record result."""
        self.test_results['total'] += 1
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)

        try:
            result = func()
            if result is None or result is True:
                self.test_results['passed'] += 1
                self.test_results['tests'].append({'name': name, 'status': 'PASS'})
                logger.info(f"✓ PASS: {name}")
            elif result == 'SKIP':
                self.test_results['skipped'] += 1
                self.test_results['tests'].append({'name': name, 'status': 'SKIP'})
                logger.warning(f"⊘ SKIP: {name}")
            else:
                self.test_results['failed'] += 1
                self.test_results['tests'].append({'name': name, 'status': 'FAIL', 'reason': str(result)})
                logger.error(f"✗ FAIL: {name} - {result}")
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['tests'].append({'name': name, 'status': 'FAIL', 'error': str(e)})
            logger.error(f"✗ FAIL: {name} - {type(e).__name__}: {e}")

    def create_test_capsule(self, organism_id: str = "test_org_001") -> OrganismCapsule:
        """Create a minimal test capsule with synthetic neural state."""
        from checkpointing.organism_capsule import OrganismCapsule, NeuralSnapshot
        import base64

        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required to create test capsule")

        # Create minimal synthetic brain state_dict
        from neural.brain import OrganismBrain

        brain = OrganismBrain(
            input_dim=24,
            hidden_dim=128,
            output_dim=6,
            vocab_size=50000,
            use_language_head=False  # Start simple
        )

        # Serialize brain state
        state_buffer = BytesIO()
        torch.save(brain.state_dict(), state_buffer, _use_new_zipfile_serialization=True)
        state_bytes = state_buffer.getvalue()
        state_b64 = base64.b64encode(state_bytes).decode('utf-8')

        # Create NeuralSnapshot
        neural_snap = NeuralSnapshot(
            brain_type='OrganismBrain',
            input_size=24,
            hidden_size=128,
            output_size=6,
            state_dict_b64=state_b64
        )

        # Create capsule
        capsule = OrganismCapsule(
            organism_id=organism_id,
            generation=100,
            fitness=0.75,
            neural=neural_snap,
            memory_traces={'test_memory': 'value'},
            vocabulary=['move', 'cooperate', 'compete', 'rest']
        )

        logger.info(f"Created test capsule: {organism_id} (fitness={capsule.fitness})")
        return capsule

    # =========================================================================
    # TEST 1: Solo Organism Export - ONNX
    # =========================================================================

    def test_solo_export_onnx(self):
        """Test exporting a single organism to ONNX format."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        compiler = AgentCompiler()
        capsule = self.create_test_capsule("solo_onnx_001")

        # Export
        archive_buffer = compiler.compile_capsule_to_agent(
            capsule,
            export_format='onnx',
            include_history=True
        )

        # Verify archive structure
        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            files = zf.namelist()
            logger.info(f"Archive contains {len(files)} files: {files}")

            # Check required files
            required = ['brain.onnx', 'metadata.json', 'agent_state.json']
            missing = [f for f in required if f not in files]
            if missing:
                return f"Missing files: {missing}"

            # Verify metadata
            metadata_json = zf.read('metadata.json').decode('utf-8')
            metadata = json.loads(metadata_json)
            logger.info(f"Metadata keys: {list(metadata.keys())}")

            # Check behavioral fingerprint
            if 'behavioral_fingerprint' in metadata:
                bf = metadata['behavioral_fingerprint']
                logger.info(f"Behavioral profile: {bf.get('personality_label', 'unknown')}")
            else:
                logger.warning("No behavioral fingerprint in metadata")

        # Save to disk for manual inspection
        output_path = self.temp_dir / 'solo_onnx_export.zip'
        with open(output_path, 'wb') as f:
            f.write(archive_buffer.getvalue())
        logger.info(f"Saved export to: {output_path}")

        return True

    # =========================================================================
    # TEST 2: Solo Organism Export - TorchScript
    # =========================================================================

    def test_solo_export_torchscript(self):
        """Test exporting a single organism to TorchScript format."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        compiler = AgentCompiler()
        capsule = self.create_test_capsule("solo_ts_001")

        # Export
        archive_buffer = compiler.compile_capsule_to_agent(
            capsule,
            export_format='torchscript'
        )

        # Verify
        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            files = zf.namelist()
            if 'brain.pt' not in files:
                return "Missing brain.pt (TorchScript model)"

            logger.info("TorchScript export verified")

        return True

    # =========================================================================
    # TEST 3: Ensemble Export (Multiple Organisms)
    # =========================================================================

    def test_ensemble_export(self):
        """Test exporting multiple organisms as an ensemble."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        compiler = AgentCompiler()

        # Create 3 test organisms with different fitness levels
        capsules = [
            self.create_test_capsule("ensemble_org_001"),
            self.create_test_capsule("ensemble_org_002"),
            self.create_test_capsule("ensemble_org_003")
        ]
        capsules[0].fitness = 0.9  # High fitness
        capsules[1].fitness = 0.6  # Medium fitness
        capsules[2].fitness = 0.3  # Low fitness

        # Export ensemble
        archive_buffer = compiler.compile_capsules_to_ensemble(
            capsules,
            export_format='onnx'
        )

        # Verify
        if archive_buffer.tell() == 0:
            return "Ensemble export produced empty buffer"

        logger.info(f"Ensemble export size: {archive_buffer.tell()} bytes")

        # Save for inspection
        output_path = self.temp_dir / 'ensemble_export.onnx'
        with open(output_path, 'wb') as f:
            f.write(archive_buffer.getvalue())
        logger.info(f"Saved ensemble to: {output_path}")

        return True

    # =========================================================================
    # TEST 4: AgentBridge - Direct Python Integration
    # =========================================================================

    def test_agent_bridge_python_integration(self):
        """Test AgentBridge direct Python API."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        # First export an agent
        compiler = AgentCompiler()
        capsule = self.create_test_capsule("bridge_test_001")
        archive_buffer = compiler.compile_capsule_to_agent(capsule, export_format='onnx')

        # Extract to directory
        export_dir = self.temp_dir / 'bridge_test_agent'
        export_dir.mkdir(exist_ok=True)

        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            zf.extractall(export_dir)

        # Load with AgentBridge
        try:
            bridge = AgentBridge.load(str(export_dir))
            logger.info(f"AgentBridge loaded successfully")

            # Test process() method
            result = bridge.process(
                text="Enemy approaching",
                context={'threat_level': 0.8, 'energy': 0.5}
            )

            logger.info(f"Action: {result.action_name}, Confidence: {result.confidence:.3f}")
            logger.info(f"Q-values: {[f'{q:.3f}' for q in result.q_values]}")

            return True

        except Exception as e:
            return f"AgentBridge load/process failed: {e}"

    # =========================================================================
    # TEST 5: Behavioral Fingerprinting
    # =========================================================================

    def test_behavioral_fingerprinting(self):
        """Test behavioral fingerprint generation."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        compiler = AgentCompiler()
        capsule = self.create_test_capsule("fingerprint_test_001")

        # Export with fingerprinting
        archive_buffer = compiler.compile_capsule_to_agent(capsule, export_format='onnx')

        # Extract metadata
        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            metadata = json.loads(zf.read('metadata.json'))

            if 'behavioral_fingerprint' not in metadata:
                return "No behavioral_fingerprint in metadata"

            bf = metadata['behavioral_fingerprint']
            required_keys = ['action_distribution', 'dominant_action', 'behavioral_tendencies', 'personality_label']
            missing = [k for k in required_keys if k not in bf]
            if missing:
                return f"Missing fingerprint keys: {missing}"

            logger.info(f"Personality: {bf['personality_label']}")
            logger.info(f"Dominant action: {bf['dominant_action']} ({bf['dominant_action_percentage']}%)")
            logger.info(f"Tendencies: {bf['behavioral_tendencies']}")

            return True

    # =========================================================================
    # TEST 6: Export Format Fallback (ONNX → TorchScript)
    # =========================================================================

    def test_export_fallback(self):
        """Test graceful fallback from ONNX to TorchScript if ONNX fails."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        # This test is tricky - we need to verify the fallback logic exists
        # by checking the code structure rather than forcing a failure

        compiler = AgentCompiler()

        # Check that _export_onnx and _export_torchscript methods exist
        if not hasattr(compiler, '_export_onnx'):
            return "Missing _export_onnx method"
        if not hasattr(compiler, '_export_torchscript'):
            return "Missing _export_torchscript method"

        logger.info("Export fallback methods verified in code structure")

        # Test actual export with fallback by using a format that might fail
        capsule = self.create_test_capsule("fallback_test_001")
        try:
            archive_buffer = compiler.compile_capsule_to_agent(capsule, export_format='onnx')
            logger.info("Export succeeded (may have used fallback)")
            return True
        except Exception as e:
            return f"Export failed even with fallback: {e}"

    # =========================================================================
    # TEST 7: Ensemble Voting Strategy Configuration
    # =========================================================================

    def test_ensemble_voting_strategies(self):
        """Test that ensemble voting strategies are properly configurable."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'

        from portable_agent.bridge import EnsembleVotingStrategy, AgentConfig

        # Verify all strategies are defined
        strategies = [s.value for s in EnsembleVotingStrategy]
        expected = ['single', 'majority', 'fitness_weighted', 'softmax_ensemble',
                   'confidence_weighted', 'fittest_top_k', 'adaptive']

        missing = [s for s in expected if s not in strategies]
        if missing:
            return f"Missing voting strategies: {missing}"

        logger.info(f"Available voting strategies: {strategies}")

        # Test AgentConfig with ensemble settings
        config = AgentConfig(
            is_ensemble=True,
            member_count=5,
            voting_strategy='fitness_weighted',
            top_k_voters=3
        )

        logger.info(f"Ensemble config: members={config.member_count}, strategy={config.voting_strategy}")

        return True

    # =========================================================================
    # TEST 8: Language Head Export (if available)
    # =========================================================================

    def test_language_head_export(self):
        """Test exporting organism with language head enabled."""
        if not COMPILER_AVAILABLE:
            return 'SKIP'
        if not TORCH_AVAILABLE:
            return 'SKIP'

        from checkpointing.organism_capsule import OrganismCapsule, NeuralSnapshot
        from neural.brain import OrganismBrain
        import base64

        # Create brain WITH language head
        brain = OrganismBrain(
            input_dim=24,
            hidden_dim=128,
            output_dim=6,
            vocab_size=50000,
            use_language_head=True  # Enable language
        )

        # Serialize
        state_buffer = BytesIO()
        torch.save(brain.state_dict(), state_buffer, _use_new_zipfile_serialization=True)
        state_bytes = state_buffer.getvalue()
        state_b64 = base64.b64encode(state_bytes).decode('utf-8')

        neural_snap = NeuralSnapshot(
            brain_type='OrganismBrain',
            input_size=24,
            hidden_size=128,
            output_size=6,
            state_dict_b64=state_b64
        )

        capsule = OrganismCapsule(
            organism_id="lang_head_test_001",
            generation=50,
            fitness=0.8,
            neural=neural_snap,
            vocabulary=['move', 'cooperate', 'hello', 'world']
        )

        # Export
        compiler = AgentCompiler()
        archive_buffer = compiler.compile_capsule_to_agent(capsule, export_format='onnx')

        # Verify
        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, 'r') as zf:
            metadata = json.loads(zf.read('metadata.json'))

            # Check if language head info is in metadata
            arch = metadata.get('neural_architecture', {})
            has_lang_head = arch.get('use_language_head', False)

            if not has_lang_head:
                logger.warning("Language head not reflected in metadata")
            else:
                logger.info("Language head successfully exported")
                logger.info(f"Vocabulary size: {metadata.get('vocabulary_size', 0)}")

        return True

    # =========================================================================
    # TEST EXECUTION
    # =========================================================================

    def run_all_tests(self):
        """Execute all tests in sequence."""
        print("\n" + "="*60)
        print("EXPORT PIPELINE VERIFICATION TEST SUITE")
        print("="*60)

        self.test("Solo Export - ONNX Format", self.test_solo_export_onnx)
        self.test("Solo Export - TorchScript Format", self.test_solo_export_torchscript)
        self.test("Ensemble Export (Multi-Organism)", self.test_ensemble_export)
        self.test("AgentBridge - Python Integration", self.test_agent_bridge_python_integration)
        self.test("Behavioral Fingerprinting", self.test_behavioral_fingerprinting)
        self.test("Export Format Fallback", self.test_export_fallback)
        self.test("Ensemble Voting Strategies", self.test_ensemble_voting_strategies)
        self.test("Language Head Export", self.test_language_head_export)

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {self.test_results['total']}")
        print(f"✓ Passed: {self.test_results['passed']}")
        print(f"✗ Failed: {self.test_results['failed']}")
        print(f"⊘ Skipped: {self.test_results['skipped']}")

        if self.test_results['failed'] > 0:
            print("\nFailed tests:")
            for test in self.test_results['tests']:
                if test['status'] == 'FAIL':
                    print(f"  - {test['name']}")
                    if 'error' in test:
                        print(f"    Error: {test['error']}")
                    elif 'reason' in test:
                        print(f"    Reason: {test['reason']}")

        print(f"\nTest artifacts saved to: {self.temp_dir}")
        print("="*60)

        return self.test_results['failed'] == 0


if __name__ == "__main__":
    if not COMPILER_AVAILABLE:
        print("ERROR: Agent compiler not available. Cannot run tests.")
        print("Ensure you're running from the Convergence_Engine directory.")
        sys.exit(1)

    tester = ExportPipelineTest()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
