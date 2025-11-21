import os
import time
import sys
from pathlib import Path
from sandbox import IsolatedChamber
from metrics import calculate_vp
from kernel import Kernel

# Helper function to import from explorer/main.py
def _import_explorer_main():
    """Import color_print, Colors, etc. from explorer/main.py"""
    # Get the explorer directory (where this file is located)
    explorer_dir = Path(__file__).parent
    
    # Temporarily modify sys.path to prioritize explorer directory
    original_path = sys.path[:]
    if str(explorer_dir) not in sys.path:
        sys.path.insert(0, str(explorer_dir))
    
    # Import using importlib to be explicit about the file
    import importlib.util
    main_path = explorer_dir / 'main.py'
    
    if not main_path.exists():
        raise ImportError(f"explorer/main.py not found at {main_path}")
    
    spec = importlib.util.spec_from_file_location("explorer_main", main_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {main_path}")
    
    explorer_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(explorer_main)
    
    # Restore original sys.path
    sys.path[:] = original_path
    
    return explorer_main

class Sentinel:
    def __init__(self, config_path='data/config.json'):
        self.kernel = Kernel()
        self.config = self._load_config(config_path)
        self.vp_threshold = self.config.get('vp_threshold', 1.0)
        self.critical_mass_sample_size = self.config.get('critical_mass_sample_size', 5)
        self.vp_history = []  # Track all VP calculations
        self.stability_history = []  # Track stability calculations

    def _load_config(self, path):
        import json
        with open(path, 'r') as f:
            return json.load(f)

    # --- Genesis Phase Logic ---
    def run_genesis_experiment(self, func_path, test_inputs, stability_center, stability_envelope):
        # Import from explorer/main.py (not reality_simulator/main.py)
        explorer_main = _import_explorer_main()
        color_print = explorer_main.color_print
        Colors = explorer_main.Colors
        explain_traits = explorer_main.explain_traits
        math_print = explorer_main.math_print
        color_print(f"[Sentinel] Genesis experiment: func_path={func_path}, inputs={test_inputs}", Colors.CYAN)
        color_print(f"[Info] Stability center and envelope:", Colors.GRAY)
        math_print(explain_traits(stability_center))
        math_print(explain_traits(stability_envelope))
        """
        Orchestrate experiments in IsolatedChamber, collect telemetry, compute VP, and certify stability.
        func_path: path to untrusted function (e.g., Python script)
        test_inputs: list of input arguments for the function
        stability_center: dict of ideal trait values
        stability_envelope: dict of allowed deviation for each trait
        Returns: (certified: bool, vp_values: list)
        """
        chamber = IsolatedChamber()
        vp_values = []
        all_terminated = True
        import psutil
        for inp in test_inputs:
            # Prepare input file for the experiment
            input_file = os.path.join(chamber.chamber_dir, 'input.txt')
            with open(input_file, 'w') as f:
                f.write(str(inp))
            # Run the function in the chamber
            start = time.time()
            try:
                out, err, timed_out, resource_exceeded = chamber.run(f'python {func_path}')
                exec_time = time.time() - start
                
                # Get the process that was actually run by the chamber
                import psutil
                current_process = psutil.Process()
                mem_usage_mb = current_process.memory_info().rss / (1024 * 1024)
                
                # If chamber has memory tracking, use that instead
                if hasattr(chamber, 'peak_memory_mb'):
                    mem_usage_mb = chamber.peak_memory_mb
                    
            except Exception as e:
                exec_time = time.time() - start
                mem_usage_mb = 0.0
                resource_exceeded = False
                timed_out = False
                print(f"[Warning] Exception during execution: {e}")
            finally:
                # Chamber handles process cleanup
                pass
            if resource_exceeded:
                mem_usage_mb = chamber.mem_limit_mb
            traits = {
                'speed_ms': exec_time * 1000,
                'memory_mb': mem_usage_mb,
                'reliability': 0 if timed_out else 1
            }
            color_print(f"[Info] Traits measured:", Colors.GRAY)
            math_print(explain_traits(traits))
            vp = calculate_vp(traits, stability_center, stability_envelope)
        vp_values.append(vp)
        # Track VP calculation for mathematical understanding
        self.vp_history.append({
            'vp': vp,
            'traits': traits,
            'timestamp': time.time(),
            'context': 'genesis_experiment'
        })
        if timed_out or resource_exceeded:
            all_terminated = False
        chamber.cleanup()
        # Certification: must terminate and have low VP for all inputs
        certified = all_terminated and all(vp < self.vp_threshold for vp in vp_values)
        math_print(f"[VP Calculation] VP values for all inputs: {vp_values}")
        if certified:
            color_print(f"[Result] Certified: {certified} (all_terminated={all_terminated}, threshold={self.vp_threshold}) ✅ This function is stable and lawful.", Colors.GREEN)
        else:
            color_print(f"[Result] Certified: {certified} (all_terminated={all_terminated}, threshold={self.vp_threshold}) ❌ This function is unstable or unlawful.", Colors.RED)
        return certified, vp_values

    def check_critical_mass(self):
        """
        Check if the system has mathematical capability for understanding.
        Returns: bool
        """
        return self.check_mathematical_capability()
    
    def check_mathematical_capability(self):
        """
        Check if system has mathematical capability for understanding.
        Returns: bool
        """
        # 1. VP Calculation Mastery
        vp_calculations = len(self.vp_history)
        understands_vp = vp_calculations >= 50
        
        # 2. VP Pattern Recognition
        if len(self.vp_history) >= 10:
            recent_vps = [entry['vp'] for entry in self.vp_history[-10:]]
            vp_variance = self._calculate_variance(recent_vps)
            vp_stability = vp_variance < 0.1  # Low variance indicates understanding
        else:
            vp_stability = False
        
        # 3. Stability Mathematics (if mirror systems available)
        understands_stability = True  # Default if no mirror systems
        stability_variance = float('inf')
        if hasattr(self, 'mirror_of_insight') and self.mirror_of_insight:
            stability_score = self.mirror_of_insight.get_stability_score()
            stability_variance = self.mirror_of_insight.get_stability_variance()
            understands_stability = stability_score > 0.5 and stability_variance < 0.2
        
        # 4. Breath Mathematics (if breath engine available)
        understands_breath = True  # Default if no breath engine
        breath_cycles = 0
        if hasattr(self, 'breath_engine') and self.breath_engine:
            breath_cycles = self.breath_engine.breath_cycle_count
            understands_breath = breath_cycles >= 25
        
        # 5. Bloom Mathematics (if bloom system available)
        understands_bloom = True  # Default if no bloom system
        bloom_curvature = 0.0
        if hasattr(self, 'bloom_system') and self.bloom_system:
            bloom_curvature = self.bloom_system.bloom_curvature
            understands_bloom = bloom_curvature > 0.2
        
        # 6. Learning Mathematics (if dynamic operations available)
        understands_learning = True  # Default if no dynamic operations
        if hasattr(self, 'dynamic_operations') and self.dynamic_operations:
            total_patterns = len(self.dynamic_operations.success_patterns) + len(self.dynamic_operations.failure_patterns)
            if total_patterns > 0:
                success_rate = len(self.dynamic_operations.success_patterns) / total_patterns
                understands_learning = success_rate > 0.6
        
        # 7. Overall Mathematical Maturity
        mathematical_maturity = (understands_vp and vp_stability and 
                               understands_stability and understands_breath and 
                               understands_bloom and understands_learning)
        
        # Log comprehensive mathematical capability assessment
        explorer_main = _import_explorer_main()
        color_print = explorer_main.color_print
        Colors = explorer_main.Colors
        color_print(f"[Mathematical Capability] VP: {vp_calculations}/50 (stable: {vp_stability})", Colors.CYAN)
        color_print(f"[Mathematical Capability] Stability: {understands_stability} (variance: {stability_variance:.3f})", Colors.CYAN)
        color_print(f"[Mathematical Capability] Breath: {understands_breath} (cycles: {breath_cycles})", Colors.CYAN)
        color_print(f"[Mathematical Capability] Bloom: {understands_bloom} (curvature: {bloom_curvature:.3f})", Colors.CYAN)
        color_print(f"[Mathematical Capability] Learning: {understands_learning}", Colors.CYAN)
        color_print(f"[Mathematical Capability] Overall Maturity: {mathematical_maturity}", Colors.CYAN)
        
        return mathematical_maturity
    
    def _calculate_variance(self, values):
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return float('inf')
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    # --- Sovereign Phase Logic ---
    def monitor_kernel(self, operation_traits, stability_center, stability_envelope):
        # Import from explorer/main.py (not reality_simulator/main.py)
        explorer_main = _import_explorer_main()
        color_print = explorer_main.color_print
        Colors = explorer_main.Colors
        explain_traits = explorer_main.explain_traits
        math_print = explorer_main.math_print
        color_print(f"[Sentinel] Monitoring kernel operation: traits={operation_traits}", Colors.CYAN)
        color_print(f"[Info] Stability center and envelope:", Colors.GRAY)
        math_print(explain_traits(stability_center))
        math_print(explain_traits(stability_envelope))
        """
        Monitor kernel operations, compute VP, and detect violations.
        operation_traits: dict of measured trait values for the operation
        Returns: (violation_detected: bool, vp)
        """
        # Calculate VP with detailed output
        vp = calculate_vp(operation_traits, stability_center, stability_envelope)
        violation_detected = vp > self.vp_threshold
        
        # Track VP calculation for mathematical understanding
        self.vp_history.append({
            'vp': vp,
            'traits': operation_traits,
            'timestamp': time.time(),
            'context': 'sovereign_monitoring'
        })
        if violation_detected:
            color_print(f"[Result] VP={vp}, Violation detected={violation_detected} (threshold={self.vp_threshold}) ❌ Unstable or unlawful operation.", Colors.RED)
        else:
            color_print(f"[Result] VP={vp}, Violation detected={violation_detected} (threshold={self.vp_threshold}) ✅ Stable and lawful operation.", Colors.GREEN)
        return violation_detected, vp

    def handle_violation(self, offending_sovereign_id):
        """
        Eject offending function sovereign ID and trigger kernel rollback.
        """
        sovereign_ids = self.kernel.get_sovereign_ids()
        if offending_sovereign_id in sovereign_ids:
            sovereign_ids.remove(offending_sovereign_id)
            # Amend kernel without offending sovereign ID
            self.kernel.sovereign_ids = sovereign_ids
            self.kernel.amend('')  # Empty string to force new version
        self.kernel.rollback()

# Example usage:
if __name__ == "__main__":
    sentinel = Sentinel()
    # Genesis Phase: run experiment
    certified, vp_values = sentinel.run_genesis_experiment(
        func_path='test_func.py',
        test_inputs=[1, 2, 3],
        stability_center={'execution_time_ms': 0.0, 'memory_kb': 0, 'terminated': 1},
        stability_envelope={'execution_time_ms': 100.0, 'memory_kb': 2048, 'terminated': 1}
    )
    print("Certified:", certified, "VPs:", vp_values)
    # Sovereign Phase: monitor operation
    violation, vp = sentinel.monitor_kernel(
        operation_traits={'execution_time_ms': 120.0, 'memory_kb': 3000, 'terminated': 1},
        stability_center={'execution_time_ms': 0.0, 'memory_kb': 0, 'terminated': 1},
        stability_envelope={'execution_time_ms': 100.0, 'memory_kb': 2048, 'terminated': 1}
    )
    print("Violation detected:", violation, "VP:", vp)
    if violation:
        sentinel.handle_violation('123e4567-e89b-12d3-a456-426614174000')
