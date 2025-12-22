#!/usr/bin/env python3
"""
VRAM Monitor - Debug GPU Memory Usage

Monitors VRAM usage during training to prevent OOM.
Shows where memory is allocated (models, batches, gradients).

Usage:
    # Monitor during training
    python monitor_vram.py

    # Check current VRAM usage
    python monitor_vram.py --check

    # Estimate VRAM needs for config
    python monitor_vram.py --estimate --organisms 1000 --batch-size 64
"""

import argparse
import sys
import os
from pathlib import Path

# Check if PyTorch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    print("❌ PyTorch not installed. Install with: pip install torch")
    sys.exit(1)

# Check if CUDA is available
if not torch.cuda.is_available():
    print("⚠️  CUDA not available. This script is for GPU monitoring only.")
    print("   Running on CPU - no VRAM to monitor.")
    sys.exit(0)


def format_bytes(bytes_val):
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def get_gpu_info():
    """Get GPU information and VRAM usage."""
    if not torch.cuda.is_available():
        return None
    
    device = torch.device('cuda')
    props = torch.cuda.get_device_properties(device)
    
    total_memory = props.total_memory
    allocated = torch.cuda.memory_allocated(device)
    reserved = torch.cuda.memory_reserved(device)
    free = total_memory - reserved
    
    return {
        'name': props.name,
        'compute_capability': f"{props.major}.{props.minor}",
        'total_memory': total_memory,
        'allocated': allocated,
        'reserved': reserved,
        'free': free,
        'utilization': (reserved / total_memory) * 100
    }


def print_vram_status():
    """Print current VRAM status."""
    info = get_gpu_info()
    if not info:
        print("No GPU available.")
        return
    
    print(f"\n{'='*60}")
    print(f"🖥️  GPU: {info['name']}")
    print(f"   Compute: {info['compute_capability']}")
    print(f"{'='*60}\n")
    
    print(f"💾 VRAM STATUS:")
    print(f"   Total:     {format_bytes(info['total_memory']):>12}")
    print(f"   Allocated: {format_bytes(info['allocated']):>12} ({info['allocated'] / info['total_memory'] * 100:.1f}%)")
    print(f"   Reserved:  {format_bytes(info['reserved']):>12} ({info['utilization']:.1f}%)")
    print(f"   Free:      {format_bytes(info['free']):>12} ({info['free'] / info['total_memory'] * 100:.1f}%)")
    print()
    
    # Warnings
    if info['utilization'] > 90:
        print("⚠️  WARNING: VRAM usage > 90% - OOM risk!")
        print("   Consider reducing batch_size or population")
    elif info['utilization'] > 75:
        print("⚠️  VRAM usage > 75% - approaching limits")
    else:
        print("✅ VRAM usage healthy")
    print()


def estimate_vram_usage(num_organisms, batch_size, input_dim=30, hidden_dim=64, vocab_size=10000):
    """Estimate VRAM usage for given config."""
    print(f"\n{'='*60}")
    print(f"📊 VRAM USAGE ESTIMATE")
    print(f"{'='*60}\n")
    
    print(f"Configuration:")
    print(f"   Organisms: {num_organisms}")
    print(f"   Batch size: {batch_size}")
    print(f"   Input dim: {input_dim}")
    print(f"   Hidden dim: {hidden_dim}")
    print(f"   Vocab size: {vocab_size}")
    print()
    
    # Model size per organism (rough estimate)
    # Parameters: input->hidden, hidden->hidden, hidden->output, hidden->vocab
    params_per_brain = (
        input_dim * hidden_dim +  # Input layer
        hidden_dim * hidden_dim * 2 +  # Hidden layers (2 layers)
        hidden_dim * 6 +  # Action head (6 actions)
        hidden_dim * vocab_size  # Language head (optional)
    )
    bytes_per_param = 4  # FP32
    bytes_per_brain = params_per_brain * bytes_per_param
    
    # Experience batch size
    bytes_per_state = input_dim * 4  # FP32
    bytes_per_batch = bytes_per_state * batch_size * 2  # states + next_states
    
    # Token batch (if language model enabled)
    bytes_per_token_batch = batch_size * 128 * 8  # batch × seq_len × int64
    
    # Gradients (same size as model)
    bytes_gradients = bytes_per_brain
    
    # Estimate concurrent training organisms (not all train at once)
    concurrent_training = min(num_organisms, 100)  # Typically ~100 active
    
    # Total VRAM estimate
    total_models = bytes_per_brain * concurrent_training
    total_batches = bytes_per_batch * concurrent_training
    total_tokens = bytes_per_token_batch * concurrent_training
    total_gradients = bytes_gradients * concurrent_training
    overhead = (total_models + total_batches + total_tokens + total_gradients) * 0.2  # 20% overhead
    
    total_vram = total_models + total_batches + total_tokens + total_gradients + overhead
    
    print(f"VRAM Breakdown:")
    print(f"   Per organism brain: {format_bytes(bytes_per_brain):>12}")
    print(f"   Per training batch: {format_bytes(bytes_per_batch):>12}")
    print(f"   Per token batch:    {format_bytes(bytes_per_token_batch):>12}")
    print()
    print(f"   {concurrent_training} concurrent training organisms:")
    print(f"   - Models:           {format_bytes(total_models):>12}")
    print(f"   - Experience batch: {format_bytes(total_batches):>12}")
    print(f"   - Token batches:    {format_bytes(total_tokens):>12}")
    print(f"   - Gradients:        {format_bytes(total_gradients):>12}")
    print(f"   - Overhead (20%):   {format_bytes(overhead):>12}")
    print(f"   {'─'*40}")
    print(f"   TOTAL ESTIMATED:    {format_bytes(total_vram):>12}")
    print()
    
    # Recommendations
    total_vram_gb = total_vram / (1024**3)
    
    print(f"💡 GPU RECOMMENDATIONS:")
    if total_vram_gb < 6:
        print(f"   ✅ RTX 3060 (8GB) or better")
    elif total_vram_gb < 10:
        print(f"   ✅ RTX 3060 Ti (12GB) or RTX 3080 (10-12GB)")
    elif total_vram_gb < 18:
        print(f"   ✅ RTX 3080 Ti (12GB) or RTX 4070 Ti (16GB)")
    elif total_vram_gb < 22:
        print(f"   ⚠️  Need 24GB GPU: RTX 3090/4090, A40, A6000")
    else:
        print(f"   ⚠️  Need 40GB+ GPU: A100, A6000 (48GB), or reduce population")
    
    print()
    print(f"✅ IMPORTANT: Experience buffers are stored in CPU RAM, not GPU VRAM!")
    print(f"   This estimate is for active training only.")
    print()
    
    # Current GPU check
    if torch.cuda.is_available():
        info = get_gpu_info()
        available_vram_gb = info['total_memory'] / (1024**3)
        print(f"🖥️  Your GPU: {info['name']} ({available_vram_gb:.1f}GB)")
        if total_vram_gb > available_vram_gb * 0.9:
            print(f"   ⚠️  WARNING: Estimated usage ({total_vram_gb:.1f}GB) exceeds 90% of available VRAM!")
            print(f"   Reduce batch_size or concurrent training limit.")
        elif total_vram_gb > available_vram_gb * 0.75:
            print(f"   ⚠️  Estimated usage ({total_vram_gb:.1f}GB) is close to capacity.")
            print(f"   Monitor VRAM during training.")
        else:
            print(f"   ✅ Should fit comfortably ({total_vram_gb:.1f}GB / {available_vram_gb:.1f}GB)")
        print()


def monitor_training():
    """Monitor VRAM during training (real-time)."""
    print(f"\n{'='*60}")
    print(f"📈 VRAM MONITOR (Press Ctrl+C to stop)")
    print(f"{'='*60}\n")
    
    import time
    
    try:
        peak_allocated = 0
        peak_reserved = 0
        
        while True:
            info = get_gpu_info()
            if not info:
                print("GPU not available")
                break
            
            peak_allocated = max(peak_allocated, info['allocated'])
            peak_reserved = max(peak_reserved, info['reserved'])
            
            # Clear line and print status
            print(f"\r💾 Allocated: {format_bytes(info['allocated']):>10} | "
                  f"Reserved: {format_bytes(info['reserved']):>10} | "
                  f"Utilization: {info['utilization']:>5.1f}% | "
                  f"Peak: {format_bytes(peak_allocated):>10}   ", end='', flush=True)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print(f"Peak VRAM Usage:")
        print(f"   Allocated: {format_bytes(peak_allocated)}")
        print(f"   Reserved:  {format_bytes(peak_reserved)}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor GPU VRAM usage for Convergence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--check', action='store_true',
                        help='Check current VRAM status')
    parser.add_argument('--estimate', action='store_true',
                        help='Estimate VRAM needs for config')
    parser.add_argument('--monitor', action='store_true',
                        help='Real-time VRAM monitoring')
    
    # Estimation params
    parser.add_argument('--organisms', type=int, default=1000,
                        help='Number of organisms (default: 1000)')
    parser.add_argument('--batch-size', type=int, default=64,
                        help='Training batch size (default: 64)')
    parser.add_argument('--input-dim', type=int, default=30,
                        help='Input dimension (default: 30)')
    parser.add_argument('--hidden-dim', type=int, default=64,
                        help='Hidden dimension (default: 64)')
    parser.add_argument('--vocab-size', type=int, default=10000,
                        help='Vocabulary size (default: 10000)')
    
    args = parser.parse_args()
    
    # Default to check if no args
    if not (args.check or args.estimate or args.monitor):
        args.check = True
    
    if args.check:
        print_vram_status()
    
    if args.estimate:
        estimate_vram_usage(
            args.organisms,
            args.batch_size,
            args.input_dim,
            args.hidden_dim,
            args.vocab_size
        )
    
    if args.monitor:
        monitor_training()


if __name__ == '__main__':
    main()
