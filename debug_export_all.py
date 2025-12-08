"""
🦋 COCOON EXPORT DEBUGGER - Automated Test Suite for All Export Pathways

This tool systematically tests EVERY export format and combination:
1. Single organism exports (ONNX, TorchScript, StateDict, Cocoon)
2. Ensemble exports (multi-organism packages)
3. Full package exports (ZIP with all formats)
4. Load-back verification (can we actually USE what we exported?)

When something breaks, it tells you EXACTLY where and why.

Usage:
    python debug_export_all.py              # Run all tests
    python debug_export_all.py --format onnx  # Test specific format
    python debug_export_all.py --verbose    # Show detailed output
"""

import sys
import os
import tempfile
import shutil
import json
import base64
import traceback
from pathlib import Path
from io import BytesIO
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# TEST RESULT TRACKING
# =============================================================================

@dataclass
class TestResult:
    name: str
    category: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    duration_ms: float = 0.0
    error: Optional[str] = None
    traceback: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ExportDebugger:
    """Comprehensive export system debugger."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.temp_dir = None
        
        # Track what's available
        self.torch_available = False
        self.onnx_available = False
        self.compiler_available = False
        self.bridge_available = False
        
    def log(self, msg: str, level: str = 'INFO'):
        """Print with optional verbosity filter."""
        if level == 'DEBUG' and not self.verbose:
            return
        prefix = {'INFO': '  ', 'DEBUG': '    ', 'ERROR': '❌', 'OK': '✓'}
        print(f"{prefix.get(level, '  ')} {msg}")
    
    def add_result(self, name: str, category: str, status: str, **kwargs):
        """Record a test result."""
        result = TestResult(name=name, category=category, status=status, **kwargs)
        self.results.append(result)
        
        icon = {'PASS': '✓', 'FAIL': '✗', 'SKIP': '⊘'}.get(status, '?')
        print(f"  [{icon}] {name}: {status}")
        if status == 'FAIL' and result.error:
            print(f"      Error: {result.error}")
    
    # =========================================================================
    # SETUP & IMPORTS
    # =========================================================================
    
    def test_imports(self) -> bool:
        """Test all required imports."""
        print("\n" + "="*70)
        print("PHASE 1: IMPORT VERIFICATION")
        print("="*70)
        
        # PyTorch
        try:
            import torch
            self.torch_available = True
            self.add_result("PyTorch import", "imports", "PASS", 
                          details={'version': torch.__version__})
        except ImportError as e:
            self.add_result("PyTorch import", "imports", "FAIL", error=str(e))
            return False  # Can't continue without PyTorch
        
        # ONNX Runtime
        try:
            import onnxruntime as ort
            self.onnx_available = True
            self.add_result("ONNX Runtime import", "imports", "PASS",
                          details={'version': ort.__version__})
        except ImportError as e:
            self.add_result("ONNX Runtime import", "imports", "SKIP", 
                          error="Not installed (optional)")
        
        # AgentCompiler
        try:
            from reality_simulator.agent_compiler import AgentCompiler
            self.compiler_available = True
            self.add_result("AgentCompiler import", "imports", "PASS")
        except ImportError as e:
            self.add_result("AgentCompiler import", "imports", "FAIL", 
                          error=str(e), traceback=traceback.format_exc())
            return False
        
        # OrganismCapsule
        try:
            from reality_simulator.checkpointing.organism_capsule import (
                OrganismCapsule, NeuralSnapshot
            )
            self.add_result("OrganismCapsule import", "imports", "PASS")
        except ImportError as e:
            self.add_result("OrganismCapsule import", "imports", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
            return False
        
        # AgentBridge
        try:
            from reality_simulator.portable_agent.bridge import AgentBridge
            self.bridge_available = True
            self.add_result("AgentBridge import", "imports", "PASS")
        except ImportError as e:
            self.add_result("AgentBridge import", "imports", "SKIP",
                          error="Not available (optional)")
        
        # OrganismBrain
        try:
            from reality_simulator.neural.brain import OrganismBrain
            self.add_result("OrganismBrain import", "imports", "PASS")
        except ImportError as e:
            self.add_result("OrganismBrain import", "imports", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
            return False
        
        return True
    
    # =========================================================================
    # TEST FIXTURES - Create test organisms/capsules
    # =========================================================================
    
    def create_test_brain(self, with_language_head: bool = False) -> Any:
        """Create a test OrganismBrain."""
        from reality_simulator.neural.brain import OrganismBrain
        
        brain = OrganismBrain(
            input_dim=24,
            hidden_dim=128,
            output_dim=6,
            vocab_size=1000,
            use_language_head=with_language_head
        )
        return brain
    
    def create_test_capsule(self, organism_id: str = "test_org", 
                           with_language_head: bool = False) -> Any:
        """Create a properly-formed OrganismCapsule."""
        import torch
        from reality_simulator.checkpointing.organism_capsule import (
            OrganismCapsule, NeuralSnapshot
        )
        
        brain = self.create_test_brain(with_language_head=with_language_head)
        
        # Serialize brain state
        state_buffer = BytesIO()
        torch.save(brain.state_dict(), state_buffer, _use_new_zipfile_serialization=True)
        state_bytes = state_buffer.getvalue()
        
        # Create NeuralSnapshot with CORRECT fields
        neural_snap = NeuralSnapshot(
            state_dict_bytes=state_bytes,
            architecture_hash=f"arch_{organism_id}",
            hidden_size=128,
            num_layers=2,
            input_size=24,
            output_size=6,
            total_parameters=sum(p.numel() for p in brain.parameters()),
            training_steps=100
        )
        
        # Create capsule with CORRECT fields
        capsule = OrganismCapsule(
            organism_id=organism_id,
            capsule_id=f"cap_{organism_id}",
            neural=neural_snap
        )
        
        return capsule, brain
    
    # =========================================================================
    # SINGLE ORGANISM EXPORT TESTS
    # =========================================================================
    
    def test_single_exports(self):
        """Test all single-organism export formats."""
        print("\n" + "="*70)
        print("PHASE 2: SINGLE ORGANISM EXPORTS")
        print("="*70)
        
        from reality_simulator.agent_compiler import AgentCompiler
        import inspect
        
        compiler = AgentCompiler()
        capsule, brain = self.create_test_capsule("single_test")
        
        # First, discover what methods actually exist
        print("\n  Available compiler methods:")
        methods = {}
        for name in dir(compiler):
            if not name.startswith('_') and callable(getattr(compiler, name)):
                method = getattr(compiler, name)
                try:
                    sig = inspect.signature(method)
                    methods[name] = sig
                    print(f"    {name}{sig}")
                except (ValueError, TypeError):
                    print(f"    {name}(...)")
        
        # Test compile_capsule_to_agent
        print("\n  Testing compile_capsule_to_agent...")
        if 'compile_capsule_to_agent' in methods:
            sig = methods['compile_capsule_to_agent']
            params = list(sig.parameters.keys())
            print(f"    Signature: {sig}")
            print(f"    Parameters: {params}")
            
            try:
                # Try calling with just the capsule
                result = compiler.compile_capsule_to_agent(capsule)
                self.add_result("compile_capsule_to_agent (default)", "single_export", "PASS",
                              details={'result_type': type(result).__name__})
            except Exception as e:
                self.add_result("compile_capsule_to_agent (default)", "single_export", "FAIL",
                              error=str(e), traceback=traceback.format_exc())
        
        # Test compile_cocoon
        print("\n  Testing compile_cocoon...")
        if 'compile_cocoon' in methods:
            sig = methods['compile_cocoon']
            print(f"    Signature: {sig}")
            
            try:
                # compile_cocoon expects a LIST of capsules
                result = compiler.compile_cocoon([capsule])
                self.add_result("compile_cocoon (single capsule)", "single_export", "PASS",
                              details={'result_length': len(result) if isinstance(result, (str, bytes)) else 'N/A'})
            except Exception as e:
                self.add_result("compile_cocoon (single capsule)", "single_export", "FAIL",
                              error=str(e), traceback=traceback.format_exc())
        
        # Test direct ONNX export if available
        print("\n  Testing direct ONNX export...")
        if self.onnx_available:
            try:
                import torch
                import torch.onnx
                
                # Export brain directly to ONNX
                dummy_input = torch.randn(1, 24)
                onnx_path = Path(self.temp_dir) / "test_brain.onnx"
                
                torch.onnx.export(
                    brain,
                    dummy_input,
                    str(onnx_path),
                    input_names=['state'],
                    output_names=['action_probs'],
                    dynamic_axes={'state': {0: 'batch'}, 'action_probs': {0: 'batch'}}
                )
                
                # Verify it loads
                import onnxruntime as ort
                session = ort.InferenceSession(str(onnx_path))
                
                self.add_result("Direct ONNX export", "single_export", "PASS",
                              details={'file_size': onnx_path.stat().st_size})
            except Exception as e:
                self.add_result("Direct ONNX export", "single_export", "FAIL",
                              error=str(e), traceback=traceback.format_exc())
        else:
            self.add_result("Direct ONNX export", "single_export", "SKIP",
                          error="ONNX Runtime not available")
        
        # Test TorchScript export
        print("\n  Testing TorchScript export...")
        try:
            import torch
            
            ts_path = Path(self.temp_dir) / "test_brain.pt"
            dummy_input = torch.randn(1, 24)
            
            # Script the model
            scripted = torch.jit.trace(brain, dummy_input)
            scripted.save(str(ts_path))
            
            # Verify it loads
            loaded = torch.jit.load(str(ts_path))
            output = loaded(dummy_input)
            
            self.add_result("TorchScript export", "single_export", "PASS",
                          details={'file_size': ts_path.stat().st_size, 
                                   'output_shape': list(output.shape)})
        except Exception as e:
            self.add_result("TorchScript export", "single_export", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
        
        # Test StateDict export
        print("\n  Testing StateDict export...")
        try:
            import torch
            
            sd_path = Path(self.temp_dir) / "test_brain_state.pth"
            torch.save(brain.state_dict(), sd_path)
            
            # Verify it loads
            loaded_state = torch.load(sd_path)
            
            self.add_result("StateDict export", "single_export", "PASS",
                          details={'file_size': sd_path.stat().st_size,
                                   'num_keys': len(loaded_state)})
        except Exception as e:
            self.add_result("StateDict export", "single_export", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
    
    # =========================================================================
    # ENSEMBLE EXPORT TESTS
    # =========================================================================
    
    def test_ensemble_exports(self):
        """Test multi-organism ensemble exports."""
        print("\n" + "="*70)
        print("PHASE 3: ENSEMBLE EXPORTS")
        print("="*70)
        
        from reality_simulator.agent_compiler import AgentCompiler
        import inspect
        
        compiler = AgentCompiler()
        
        # Create multiple capsules
        capsules = []
        brains = []
        for i in range(3):
            cap, brain = self.create_test_capsule(f"ensemble_org_{i}")
            capsules.append(cap)
            brains.append(brain)
        
        print(f"\n  Created {len(capsules)} test capsules")
        
        # Test compile_capsules_to_ensemble
        print("\n  Testing compile_capsules_to_ensemble...")
        if hasattr(compiler, 'compile_capsules_to_ensemble'):
            sig = inspect.signature(compiler.compile_capsules_to_ensemble)
            print(f"    Signature: {sig}")
            
            try:
                result = compiler.compile_capsules_to_ensemble(capsules)
                self.add_result("compile_capsules_to_ensemble", "ensemble_export", "PASS",
                              details={'result_type': type(result).__name__})
            except Exception as e:
                self.add_result("compile_capsules_to_ensemble", "ensemble_export", "FAIL",
                              error=str(e), traceback=traceback.format_exc())
        
        # Test compile_cocoon with multiple capsules
        print("\n  Testing compile_cocoon (multi-capsule)...")
        if hasattr(compiler, 'compile_cocoon'):
            try:
                result = compiler.compile_cocoon(capsules)
                self.add_result("compile_cocoon (ensemble)", "ensemble_export", "PASS",
                              details={'result_length': len(result) if isinstance(result, (str, bytes)) else 'N/A'})
            except Exception as e:
                self.add_result("compile_cocoon (ensemble)", "ensemble_export", "FAIL",
                              error=str(e), traceback=traceback.format_exc())
    
    # =========================================================================
    # PACKAGE EXPORT TESTS  
    # =========================================================================
    
    def test_package_exports(self):
        """Test full package exports (ZIP with multiple formats)."""
        print("\n" + "="*70)
        print("PHASE 4: PACKAGE EXPORTS")
        print("="*70)
        
        # TODO: Test ZIP package creation with all formats
        # This would include: ONNX + TorchScript + StateDict + metadata + README
        
        self.add_result("Package export (ZIP)", "package_export", "SKIP",
                      error="Not yet implemented in test suite")
    
    # =========================================================================
    # LOAD-BACK VERIFICATION
    # =========================================================================
    
    def test_load_back(self):
        """Test that exported models can be loaded and used."""
        print("\n" + "="*70)
        print("PHASE 5: LOAD-BACK VERIFICATION")
        print("="*70)
        
        if not self.bridge_available:
            self.add_result("AgentBridge load-back", "load_back", "SKIP",
                          error="AgentBridge not available")
            return
        
        # TODO: Test loading exported models through AgentBridge
        self.add_result("AgentBridge load-back", "load_back", "SKIP",
                      error="Not yet implemented in test suite")
    
    # =========================================================================
    # LANGUAGE HEAD EXPORT TESTS
    # =========================================================================
    
    def test_language_head_exports(self):
        """Test exports with language heads enabled."""
        print("\n" + "="*70)
        print("PHASE 6: LANGUAGE HEAD EXPORTS")
        print("="*70)
        
        from reality_simulator.agent_compiler import AgentCompiler
        
        compiler = AgentCompiler()
        capsule, brain = self.create_test_capsule("lang_test", with_language_head=True)
        
        print(f"  Brain has language head: {brain.use_language_head}")
        print(f"  Vocab size: {brain.vocab_size}")
        
        # Test TorchScript with language head
        print("\n  Testing TorchScript export (with language head)...")
        try:
            import torch
            
            ts_path = Path(self.temp_dir) / "test_brain_lang.pt"
            dummy_input = torch.randn(1, 24)
            
            # This is trickier - language head changes output signature
            scripted = torch.jit.trace(brain, dummy_input)
            scripted.save(str(ts_path))
            
            # Verify
            loaded = torch.jit.load(str(ts_path))
            output = loaded(dummy_input)
            
            self.add_result("TorchScript export (language head)", "language_export", "PASS",
                          details={'output_type': type(output).__name__})
        except Exception as e:
            self.add_result("TorchScript export (language head)", "language_export", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
        
        # Test cocoon with language head
        print("\n  Testing compile_cocoon (with language head)...")
        try:
            result = compiler.compile_cocoon([capsule])
            self.add_result("compile_cocoon (language head)", "language_export", "PASS")
        except Exception as e:
            self.add_result("compile_cocoon (language head)", "language_export", "FAIL",
                          error=str(e), traceback=traceback.format_exc())
    
    # =========================================================================
    # MAIN RUNNER
    # =========================================================================
    
    def run_all(self) -> bool:
        """Run all export tests."""
        print("="*70)
        print("🦋 COCOON EXPORT DEBUGGER")
        print("="*70)
        print(f"Started: {datetime.now().isoformat()}")
        
        # Create temp directory for exports
        self.temp_dir = tempfile.mkdtemp(prefix="cocoon_debug_")
        print(f"Temp directory: {self.temp_dir}")
        
        try:
            # Phase 1: Imports
            if not self.test_imports():
                print("\n❌ CRITICAL: Import failures prevent further testing")
                return False
            
            # Phase 2: Single exports
            self.test_single_exports()
            
            # Phase 3: Ensemble exports
            self.test_ensemble_exports()
            
            # Phase 4: Package exports
            self.test_package_exports()
            
            # Phase 5: Load-back
            self.test_load_back()
            
            # Phase 6: Language head
            self.test_language_head_exports()
            
        finally:
            # Cleanup
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
        
        # Summary
        self.print_summary()
        
        return all(r.status != 'FAIL' for r in self.results)
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        # Count by status
        passed = sum(1 for r in self.results if r.status == 'PASS')
        failed = sum(1 for r in self.results if r.status == 'FAIL')
        skipped = sum(1 for r in self.results if r.status == 'SKIP')
        
        print(f"\n  Total: {len(self.results)} tests")
        print(f"  ✓ Passed:  {passed}")
        print(f"  ✗ Failed:  {failed}")
        print(f"  ⊘ Skipped: {skipped}")
        
        # List failures
        if failed > 0:
            print("\n  FAILURES:")
            for r in self.results:
                if r.status == 'FAIL':
                    print(f"    - {r.name}")
                    print(f"      Error: {r.error}")
                    if self.verbose and r.traceback:
                        for line in r.traceback.split('\n')[:5]:
                            print(f"        {line}")
        
        # Categories breakdown
        print("\n  BY CATEGORY:")
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'pass': 0, 'fail': 0, 'skip': 0}
            categories[r.category][r.status.lower()] += 1
        
        for cat, counts in categories.items():
            status = "✓" if counts['fail'] == 0 else "✗"
            print(f"    {status} {cat}: {counts['pass']}P / {counts['fail']}F / {counts['skip']}S")
        
        print("\n" + "="*70)


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Cocoon Export Debugger")
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--format', '-f', type=str, help='Test specific format only')
    
    args = parser.parse_args()
    
    debugger = ExportDebugger(verbose=args.verbose)
    success = debugger.run_all()
    
    sys.exit(0 if success else 1)
