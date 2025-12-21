#!/usr/bin/env python3
"""
GPU Profiling Script for Convergence Engine
============================================

Uses NVIDIA Nsight Systems and Nsight Compute to identify optimization opportunities.

Usage:
    # Quick profile (Nsight Systems - timeline analysis)
    python profile_gpu.py --mode quick
    
    # Deep kernel analysis (Nsight Compute - per-kernel metrics)
    python profile_gpu.py --mode deep
    
    # Run with PyTorch profiler (no NVIDIA tools needed)
    python profile_gpu.py --mode torch
    
    # Profile specific component
    python profile_gpu.py --mode torch --component brain
    python profile_gpu.py --mode torch --component trainer
    python profile_gpu.py --mode torch --component attention
    
Output:
    data/profiles/nsys_*.nsys-rep     - Open with Nsight Systems GUI
    data/profiles/ncu_*.ncu-rep       - Open with Nsight Compute GUI  
    data/profiles/torch_*.json        - Open with chrome://tracing
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project
sys.path.insert(0, str(Path(__file__).parent))

import torch
import torch.nn.functional as F
from torch.profiler import profile, record_function, ProfilerActivity

# Check CUDA availability
if not torch.cuda.is_available():
    print("ERROR: CUDA not available. GPU profiling requires CUDA.")
    sys.exit(1)

DEVICE = torch.device('cuda')
PROFILE_DIR = Path("data/profiles")
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def profile_brain_forward():
    """Profile the OrganismBrain forward pass."""
    from reality_simulator.neural.brain import OrganismBrain
    
    print("\n🧠 Profiling OrganismBrain forward pass...")
    
    # Create brain with typical config (matches OrganismBrain.__init__ signature)
    brain = OrganismBrain(
        input_dim=30,
        hidden_dim=128,
        output_dim=8,
        use_attention=True,
        num_attention_heads=4,
        attention_dim=128,
        vocab_size=10000,
        use_language_head=True
    ).to(DEVICE)
    
    # Typical batch sizes to profile
    batch_sizes = [1, 4, 8, 16, 32]
    seq_lengths = [8, 16, 32]
    
    results = []
    
    # Warmup
    x = torch.randn(4, 28, device=DEVICE)
    for _ in range(10):
        _ = brain(x)
    torch.cuda.synchronize()
    
    for batch_size in batch_sizes:
        x = torch.randn(batch_size, 28, device=DEVICE)
        
        # Time forward pass
        torch.cuda.synchronize()
        start = time.perf_counter()
        
        for _ in range(100):
            with torch.no_grad():
                output = brain(x, vp_value=0.5)
        
        torch.cuda.synchronize()
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms
        
        results.append({
            'batch_size': batch_size,
            'time_ms': elapsed,
            'throughput': batch_size / elapsed * 1000  # samples/sec
        })
        print(f"  Batch={batch_size:2d}: {elapsed:.3f}ms ({results[-1]['throughput']:.0f} samples/s)")
    
    return results


def profile_attention():
    """Profile MultiHeadAttention in isolation."""
    from reality_simulator.neural.brain import MultiHeadAttention
    
    print("\n👁️ Profiling MultiHeadAttention...")
    
    attn = MultiHeadAttention(
        embed_dim=128,
        num_heads=8,
        dropout=0.0  # No dropout for consistent timing
    ).to(DEVICE)
    
    batch_sizes = [1, 4, 16]
    seq_lengths = [16, 32, 64, 128, 256]
    
    results = []
    
    for batch_size in batch_sizes:
        for seq_len in seq_lengths:
            x = torch.randn(batch_size, seq_len, 128, device=DEVICE)
            
            # Warmup
            for _ in range(5):
                _ = attn(x)
            torch.cuda.synchronize()
            
            # Time
            start = time.perf_counter()
            for _ in range(100):
                with torch.no_grad():
                    _ = attn(x, vp_value=0.5)
            torch.cuda.synchronize()
            elapsed = (time.perf_counter() - start) / 100 * 1000
            
            # Attention is O(seq_len^2)
            ops = batch_size * seq_len * seq_len * 128
            results.append({
                'batch_size': batch_size,
                'seq_len': seq_len,
                'time_ms': elapsed,
                'gflops': ops / elapsed / 1e6
            })
            print(f"  Batch={batch_size:2d}, Seq={seq_len:3d}: {elapsed:.3f}ms ({results[-1]['gflops']:.1f} GFLOP/s)")
    
    return results


def profile_language_loss():
    """Profile language loss calculation."""
    from reality_simulator.neural.trainer import NeuralTrainer
    
    print("\n📝 Profiling language loss calculation...")
    
    vocab_size = 10000
    batch_sizes = [4, 8, 16, 32]
    seq_lengths = [16, 32, 64, 128]
    
    results = []
    
    for batch_size in batch_sizes:
        for seq_len in seq_lengths:
            # Simulate logits and targets
            logits = torch.randn(batch_size, seq_len, vocab_size, device=DEVICE)
            targets = torch.randint(0, vocab_size, (batch_size, seq_len), device=DEVICE)
            
            # Warmup
            for _ in range(5):
                logits_flat = logits.view(-1, vocab_size)
                targets_flat = targets.view(-1)
                _ = F.cross_entropy(logits_flat, targets_flat, ignore_index=0)
            torch.cuda.synchronize()
            
            # Time
            start = time.perf_counter()
            for _ in range(100):
                logits_flat = logits.view(-1, vocab_size)
                targets_flat = targets.view(-1)
                loss = F.cross_entropy(logits_flat, targets_flat, ignore_index=0)
            torch.cuda.synchronize()
            elapsed = (time.perf_counter() - start) / 100 * 1000
            
            results.append({
                'batch_size': batch_size,
                'seq_len': seq_len,
                'vocab_size': vocab_size,
                'time_ms': elapsed
            })
            print(f"  Batch={batch_size:2d}, Seq={seq_len:3d}, Vocab={vocab_size}: {elapsed:.3f}ms")
    
    return results


def profile_with_torch_profiler(component: str = 'all'):
    """Use PyTorch's built-in profiler for detailed analysis."""
    
    print(f"\n🔬 Running PyTorch Profiler (component={component})...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_file = PROFILE_DIR / f"torch_{component}_{timestamp}.json"
    
    activities = [ProfilerActivity.CPU, ProfilerActivity.CUDA]
    
    with profile(
        activities=activities,
        record_shapes=True,
        profile_memory=True,
        with_stack=True,
        with_flops=True
    ) as prof:
        
        if component in ['all', 'brain']:
            with record_function("brain_forward"):
                profile_brain_forward()
        
        if component in ['all', 'attention']:
            with record_function("attention"):
                profile_attention()
        
        if component in ['all', 'loss']:
            with record_function("language_loss"):
                profile_language_loss()
    
    # Export trace
    prof.export_chrome_trace(str(trace_file))
    print(f"\n📊 Trace exported to: {trace_file}")
    print(f"   Open with: chrome://tracing")
    
    # Print summary
    print("\n" + "="*80)
    print("TOP 20 CUDA OPERATIONS BY TIME:")
    print("="*80)
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
    
    print("\n" + "="*80)
    print("TOP 10 BY GPU MEMORY:")
    print("="*80)
    print(prof.key_averages().table(sort_by="self_cuda_memory_usage", row_limit=10))
    
    # Save summary to file
    summary_file = PROFILE_DIR / f"torch_{component}_{timestamp}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("TOP 20 CUDA OPERATIONS BY TIME:\n")
        f.write(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
        f.write("\n\nTOP 10 BY GPU MEMORY:\n")
        f.write(prof.key_averages().table(sort_by="self_cuda_memory_usage", row_limit=10))
    
    print(f"\n📄 Summary saved to: {summary_file}")
    
    return prof


def run_nsight_systems():
    """Run Nsight Systems profiling (requires admin on some systems)."""
    
    print("\n🔍 Running Nsight Systems profiling...")
    
    nsys_path = r"C:\Program Files\NVIDIA Corporation\Nsight Systems 2023.1.2\target-windows-x64\nsys.exe"
    
    if not os.path.exists(nsys_path):
        print("ERROR: Nsight Systems not found at expected path.")
        print("       Install from: https://developer.nvidia.com/nsight-systems")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = PROFILE_DIR / f"nsys_{timestamp}"
    
    # Create a mini profiling script
    mini_script = PROFILE_DIR / "nsys_target.py"
    with open(mini_script, 'w') as f:
        f.write('''
import sys
sys.path.insert(0, '.')
import torch
from reality_simulator.neural.brain import OrganismBrain

device = torch.device('cuda')
brain = OrganismBrain(
    input_dim=32, hidden_dim=128, output_dim=8,
    use_attention=True, language_model=True, vocab_size=10000
).to(device)

# Warmup
x = torch.randn(8, 32, 32, device=device)
for _ in range(10):
    brain(x)
torch.cuda.synchronize()

# Profile this part
for _ in range(1000):
    output, lang = brain(x, vp_value=0.5, return_language=True)
torch.cuda.synchronize()
print("Done")
''')
    
    cmd = f'"{nsys_path}" profile --output="{output_file}" --force-overwrite=true python "{mini_script}"'
    print(f"Running: {cmd}")
    os.system(cmd)
    
    print(f"\n📊 Profile saved to: {output_file}.nsys-rep")
    print(f"   Open with: Nsight Systems GUI")


def run_nsight_compute():
    """Run Nsight Compute for deep kernel analysis."""
    
    print("\n🔬 Running Nsight Compute profiling...")
    
    ncu_path = r"C:\Program Files\NVIDIA Corporation\Nsight Compute 2023.1.1\ncu.bat"
    
    if not os.path.exists(ncu_path):
        print("ERROR: Nsight Compute not found.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = PROFILE_DIR / f"ncu_{timestamp}.ncu-rep"
    
    # Create mini script
    mini_script = PROFILE_DIR / "ncu_target.py"
    with open(mini_script, 'w') as f:
        f.write('''
import sys
sys.path.insert(0, '.')
import torch
from reality_simulator.neural.brain import OrganismBrain

device = torch.device('cuda')
brain = OrganismBrain(
    input_dim=32, hidden_dim=128, output_dim=8,
    use_attention=True
).to(device)

x = torch.randn(16, 32, 32, device=device)
for _ in range(10):
    brain(x)
torch.cuda.synchronize()
print("Done")
''')
    
    # Note: Nsight Compute requires admin privileges on Windows
    cmd = f'"{ncu_path}" --set full --output "{output_file}" python "{mini_script}"'
    print(f"Running: {cmd}")
    print("NOTE: This may require administrator privileges on Windows.")
    os.system(cmd)
    
    print(f"\n📊 Profile saved to: {output_file}")
    print(f"   Open with: Nsight Compute GUI")


def suggest_optimizations():
    """Print optimization suggestions based on architecture."""
    
    print("\n" + "="*80)
    print("💡 OPTIMIZATION SUGGESTIONS FOR CONVERGENCE ENGINE")
    print("="*80)
    
    suggestions = """
1. ATTENTION OPTIMIZATION
   - Current: Manual attention implementation
   - Suggestion: Use torch.nn.functional.scaled_dot_product_attention() (PyTorch 2.0+)
   - Benefit: Flash Attention / Memory-efficient attention automatic dispatch
   - Location: reality_simulator/neural/brain.py, MultiHeadAttention.forward()

2. MIXED PRECISION TRAINING
   - Current: FP32 everywhere
   - Suggestion: Use torch.cuda.amp.autocast() with GradScaler
   - Benefit: 2-3x speedup on Tensor Cores, lower memory
   - Location: reality_simulator/neural/trainer.py

3. TORCH.COMPILE() (PyTorch 2.0+)
   - Suggestion: Wrap brain.forward() with torch.compile()
   - Benefit: Kernel fusion, memory planning, 10-30% speedup
   - Code: brain = torch.compile(brain, mode='reduce-overhead')

4. CUDA GRAPHS
   - Suggestion: Capture forward pass as CUDA graph for static shapes
   - Benefit: Eliminate kernel launch overhead
   - Best for: Inference loops with fixed batch sizes

5. REDUCE PYTHON OVERHEAD
   - Current: Python loops for organism processing
   - Suggestion: Batch organisms together, vectorize operations
   - Benefit: Less CPU-GPU synchronization

6. GRADIENT CHECKPOINTING
   - Suggestion: Use torch.utils.checkpoint for attention layers
   - Benefit: Trade compute for memory, fit larger batches

7. VOCAB SIZE OPTIMIZATION
   - Current: vocab_size=10000
   - Note: Embedding layers scale with vocab size
   - Consider: Smaller embedding dim if vocab is sparse

8. MEMORY POOLING
   - Suggestion: Use CUDA memory pools (torch.cuda.memory.CUDAPluggableAllocator)
   - Benefit: Reduce allocation overhead

RUN THESE COMMANDS TO DIAGNOSE:
    python profile_gpu.py --mode torch              # Full analysis
    python profile_gpu.py --mode torch --component attention  # Attention focus
"""
    print(suggestions)


def main():
    parser = argparse.ArgumentParser(description="GPU Profiling for Convergence Engine")
    parser.add_argument('--mode', choices=['quick', 'deep', 'torch', 'suggest'], 
                       default='torch', help='Profiling mode')
    parser.add_argument('--component', choices=['all', 'brain', 'attention', 'loss'],
                       default='all', help='Component to profile (torch mode only)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🚀 CONVERGENCE ENGINE GPU PROFILER")
    print("="*80)
    print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.version.cuda}")
    
    if args.mode == 'quick':
        run_nsight_systems()
    elif args.mode == 'deep':
        run_nsight_compute()
    elif args.mode == 'torch':
        profile_with_torch_profiler(args.component)
        suggest_optimizations()
    elif args.mode == 'suggest':
        suggest_optimizations()


if __name__ == "__main__":
    main()
