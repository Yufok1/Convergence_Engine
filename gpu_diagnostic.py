"""
GPU Diagnostic Script
Identifies GPU utilization issues and provides optimization recommendations
"""

import sys
import json
from pathlib import Path

def check_pytorch_cuda():
    """Check PyTorch CUDA availability and configuration"""
    try:
        import torch
        print("\n=== PyTorch GPU Diagnostics ===")
        print(f"PyTorch Version: {torch.__version__}")
        print(f"CUDA Available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA Version: {torch.version.cuda}")
            print(f"cuDNN Enabled: {torch.backends.cudnn.enabled}")
            print(f"Device Count: {torch.cuda.device_count()}")
            print(f"Current Device: {torch.cuda.current_device()}")
            print(f"Device Name: {torch.cuda.get_device_name(0)}")
            print(f"Device Capability: {torch.cuda.get_device_capability(0)}")

            # Memory info
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**2
            memory_reserved = torch.cuda.memory_reserved(0) / 1024**2
            print(f"Memory Allocated: {memory_allocated:.2f} MiB")
            print(f"Memory Reserved: {memory_reserved:.2f} MiB")

            return True
        else:
            print("❌ CUDA not available - PyTorch will use CPU")
            print("Reasons could be:")
            print("  - No GPU present")
            print("  - Wrong PyTorch version (CPU-only)")
            print("  - CUDA drivers not installed")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def check_config():
    """Check config.json GPU settings"""
    print("\n=== Config.json GPU Settings ===")
    config_path = Path(__file__).parent / 'config.json'

    if not config_path.exists():
        print("❌ config.json not found")
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)

    neural_config = config.get('neural', {})
    device = neural_config.get('device', 'cpu')
    enabled = neural_config.get('enabled', False)
    training_enabled = neural_config.get('training', {}).get('enabled', False)

    print(f"Neural System Enabled: {enabled}")
    print(f"Neural Training Enabled: {training_enabled}")
    print(f"Device Setting: {device}")

    if device == 'cpu':
        print("⚠️  WARNING: Device set to 'cpu' - change to 'cuda' for GPU acceleration")

    # Optimization settings
    opt_config = neural_config.get('optimization', {})
    use_compile = opt_config.get('use_compile', False)
    compile_mode = opt_config.get('compile_mode', 'default')

    print(f"torch.compile Enabled: {use_compile}")
    print(f"Compile Mode: {compile_mode}")

    return neural_config

def check_neural_system():
    """Check if neural organisms are being created and trained"""
    print("\n=== Neural System Status ===")

    shared_state_path = Path(__file__).parent / 'data' / 'shared_state.json'

    if not shared_state_path.exists():
        print("⚠️  shared_state.json not found - simulation may not be running")
        return None

    with open(shared_state_path, 'r') as f:
        state = json.load(f)

    neural_data = state.get('neural', {})
    neural_organisms = neural_data.get('neural_organisms', 0)
    training_active = neural_data.get('training_active', False)
    experiences_collected = neural_data.get('experiences_collected', 0)
    training_steps = neural_data.get('training_steps', 0)

    print(f"Neural Organisms: {neural_organisms}")
    print(f"Training Active: {training_active}")
    print(f"Experiences Collected: {experiences_collected}")
    print(f"Training Steps: {training_steps}")

    if neural_organisms == 0:
        print("❌ No neural organisms created")
        print("   - Check if neural.enabled = true in config")
        print("   - Verify PyTorch is installed")
    elif not training_active:
        print("⚠️  Neural organisms exist but training not active")
        print(f"   - Need {128} experiences to start training")
        print(f"   - Currently have {experiences_collected}")
    elif training_steps == 0:
        print("⚠️  Training marked active but no steps completed")
        print("   - Check for errors in console output")
    else:
        print(f"✅ Training is active with {training_steps} steps completed")

    return neural_data

def diagnose_low_gpu_usage():
    """Provide recommendations for low GPU utilization"""
    print("\n=== GPU Utilization Diagnosis ===")
    print("\nCommon causes of low GPU usage (0.59%):")
    print("\n1. ❌ Small Batch Size")
    print("   - Current batch_size: 128")
    print("   - Recommendation: Increase to 256-512 for A100")
    print("   - GPUs are optimized for large parallel workloads")

    print("\n2. ❌ CPU-Bound Preprocessing")
    print("   - Experience collection happens on CPU")
    print("   - Only training uses GPU")
    print("   - Solution: Batch experiences and send to GPU in bulk")

    print("\n3. ❌ Training Frequency Too Low")
    print("   - Training only happens every 'update_frequency' frames")
    print("   - Most time spent on CPU (organism logic, networks)")
    print("   - GPU sits idle between training batches")

    print("\n4. ❌ Data Transfer Overhead")
    print("   - Moving small batches CPU→GPU→CPU is inefficient")
    print("   - Solution: Keep experience buffer on GPU")

    print("\n5. ❌ torch.compile() May Not Be Active")
    print("   - Requires PyTorch 2.0+")
    print("   - Check if compilation actually succeeded")

    print("\n=== Optimization Recommendations ===")
    print("\n1. Increase Batch Size:")
    print('   "neural.training.batch_size": 256  # or 512 for A100')

    print("\n2. Increase Training Frequency:")
    print('   "neural.training.update_frequency": 1  # Train every frame when enough experiences')

    print("\n3. Pin Experience Buffer to GPU:")
    print("   - Modify ExperienceBuffer to store tensors on GPU")
    print("   - Avoid CPU→GPU transfer on every training step")

    print("\n4. Profile GPU Kernels:")
    print("   - Use PyTorch Profiler to identify bottlenecks")
    print("   - Check if time is spent in tensor operations vs data transfer")

    print("\n5. Increase Population Size:")
    print("   - More organisms = more parallel experiences")
    print('   "evolution.population_size": 4000  # Double it')

    print("\n6. Verify torch.compile():")
    print("   - Add logging to confirm compilation succeeded")
    print("   - Check PyTorch version >= 2.0.0")

def main():
    """Run all diagnostics"""
    print("=" * 60)
    print("CONVERGENCE ENGINE - GPU DIAGNOSTIC TOOL")
    print("=" * 60)

    # Check PyTorch
    cuda_available = check_pytorch_cuda()

    # Check config
    config = check_config()

    # Check neural system status
    neural_status = check_neural_system()

    # Provide optimization recommendations
    diagnose_low_gpu_usage()

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
