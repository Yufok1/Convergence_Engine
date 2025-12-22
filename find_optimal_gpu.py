#!/usr/bin/env python3
"""
find_optimal_gpu.py - Smart GPU Finder for Convergence Engine

Searches Vast.ai for optimal GPU rental based on your training needs.
Considers VRAM, performance, cost, and reliability.

Usage:
    python find_optimal_gpu.py                    # Find best overall
    python find_optimal_gpu.py --budget 0.30      # Under $0.30/hr
    python find_optimal_gpu.py --cocoon-training  # Optimal for cocoon production
    python find_optimal_gpu.py --testing          # Cheap testing GPU
"""

import subprocess
import json
import sys
import argparse
from typing import List, Dict, Any

# GPU tier rankings (performance per dollar)
GPU_TIERS = {
    # Tier S: Best for cocoon production (24GB+, latest arch)
    'S': ['RTX 4090', 'L40', 'RTX 4080'],
    
    # Tier A: Production-ready (24GB, good perf)
    'A': ['RTX 3090', 'RTX 3090 Ti', 'A40', 'A6000'],
    
    # Tier B: Good value (16-24GB)
    'B': ['RTX 3080 Ti', 'RTX 3080', 'A5000', 'RTX A4500'],
    
    # Tier C: Budget testing (8-12GB)
    'C': ['RTX 3070', 'RTX 3060 Ti', 'RTX 3060', 'RTX 2080 Ti'],
    
    # Tier D: Minimal (avoid unless desperate)
    'D': ['T4', 'RTX 2070', 'RTX 2060', 'GTX 1080 Ti'],
}

def get_gpu_tier(gpu_name: str) -> str:
    """Determine GPU tier from name."""
    for tier, gpus in GPU_TIERS.items():
        for gpu in gpus:
            if gpu.lower() in gpu_name.lower():
                return tier
    return 'E'  # Unknown/unranked


def vast_search(query: str, order: str = "dph_total", limit: int = 50) -> List[Dict[str, Any]]:
    """Run vast.ai search and return results."""
    try:
        cmd = ["python", "vast.py", "search", query, "--order", order, "--limit", str(limit)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the output (vast.py outputs JSON)
        # Note: vast.py prints header text, so we need to extract JSON
        output = result.stdout.strip()
        
        # Try running vastai directly for JSON
        cmd_direct = ["vastai", "search", "offers", query, "-o", order, "--raw"]
        result_direct = subprocess.run(cmd_direct, capture_output=True, text=True)
        
        if result_direct.returncode == 0 and result_direct.stdout.strip():
            return json.loads(result_direct.stdout)
        
        return []
    except Exception as e:
        print(f"Error searching Vast.ai: {e}", file=sys.stderr)
        return []


def score_offer(offer: Dict[str, Any], mode: str = 'balanced') -> float:
    """
    Score an offer based on multiple factors.
    
    Modes:
        - 'balanced': Best overall value
        - 'performance': Maximum speed (ignore cost)
        - 'budget': Minimum cost
        - 'cocoon': Optimized for cocoon training (24GB+, good perf, reasonable cost)
    """
    gpu_name = offer.get('gpu_name', '')
    vram = offer.get('gpu_ram', 0) / 1024  # Convert MB to GB
    num_gpus = offer.get('num_gpus', 1)
    dph = offer.get('dph_total', 999)
    reliability = offer.get('reliability', 0)
    dlperf = offer.get('dlperf', 0)
    
    # Base score components
    tier = get_gpu_tier(gpu_name)
    tier_score = {'S': 100, 'A': 80, 'B': 60, 'C': 40, 'D': 20, 'E': 10}.get(tier, 10)
    
    vram_score = min(vram / 24.0, 1.0) * 50  # 24GB = full score
    reliability_score = reliability * 30
    perf_score = min(dlperf / 200.0, 1.0) * 40  # 200 = good performance
    
    # Cost efficiency (inverse, higher is better)
    if dph > 0:
        cost_efficiency = (dlperf / dph) / 200.0 * 50  # Normalize
    else:
        cost_efficiency = 0
    
    # Mode-specific weighting
    if mode == 'performance':
        score = tier_score * 1.5 + perf_score * 2.0 + vram_score * 1.0
    elif mode == 'budget':
        score = cost_efficiency * 2.0 + reliability_score * 1.0
    elif mode == 'cocoon':
        # Cocoon training: need 24GB, good tier, reliable, reasonable cost
        if vram < 20:
            score = 0  # Insufficient VRAM
        else:
            score = tier_score * 1.2 + vram_score * 1.5 + reliability_score * 1.0 + cost_efficiency * 0.8
    else:  # balanced
        score = tier_score * 0.8 + vram_score * 0.8 + reliability_score * 0.8 + perf_score * 0.6 + cost_efficiency * 1.0
    
    # Penalties
    if reliability < 0.9:
        score *= 0.8
    if dph > 1.0:
        score *= 0.7  # Expensive
    if num_gpus > 1:
        score *= 0.9  # Multi-GPU not needed
    
    return score


def print_offers(offers: List[Dict[str, Any]], mode: str, top_n: int = 10):
    """Print top offers in a nice table."""
    if not offers:
        print("No offers found.")
        return
    
    # Score and sort
    scored = [(score_offer(o, mode), o) for o in offers]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    print(f"\n{'='*100}")
    print(f"🎯 TOP {top_n} GPUs FOR {mode.upper()} MODE")
    print(f"{'='*100}\n")
    
    # Header
    print(f"{'Rank':<5} {'ID':<8} {'GPU':<18} {'VRAM':<7} {'$/hr':<10} {'Rel':<6} {'Tier':<5} {'Score':<7} {'DLPerf':<8}")
    print(f"{'-'*100}")
    
    # Rows
    for rank, (score, offer) in enumerate(scored[:top_n], 1):
        gpu_name = offer.get('gpu_name', 'Unknown')[:18]
        vram = offer.get('gpu_ram', 0) / 1024
        dph = offer.get('dph_total', 0)
        reliability = offer.get('reliability', 0)
        tier = get_gpu_tier(offer.get('gpu_name', ''))
        dlperf = offer.get('dlperf', 0)
        
        print(f"{rank:<5} {offer.get('id'):<8} {gpu_name:<18} {vram:>5.0f}GB {dph:>8.4f} {reliability:>5.2f} {tier:^5} {score:>6.1f} {dlperf:>7.1f}")
    
    print(f"\n{'='*100}\n")
    
    # Show best pick
    if scored:
        best_score, best = scored[0]
        vram_gb = best.get('gpu_ram', 0) / 1024
        
        print(f"🏆 RECOMMENDED: #{best.get('id')} - {best.get('gpu_name')} ({vram_gb:.0f}GB) at ${best.get('dph_total', 0):.4f}/hr")
        print(f"\n💾 VRAM CAPACITY ESTIMATE:")
        print(f"   With {vram_gb:.0f}GB VRAM:")
        print(f"   - Max organisms: ~{int(vram_gb * 50)}-{int(vram_gb * 80)} (depends on batch size)")
        print(f"   - Recommended batch size: {32 if vram_gb < 12 else 64 if vram_gb < 20 else 128}")
        print(f"   - Safe population: {200 if vram_gb < 12 else 500 if vram_gb < 20 else '1000+'} organisms")
        print(f"\n   ✅ Experience buffers stored in CPU RAM (unlimited!)")
        print(f"   ✅ Only active training batches use GPU VRAM")
        
        print(f"\n📋 TO RENT THIS GPU:")
        print(f"   python vast.py create {best.get('id')} --image pytorch/pytorch:2.5.0-cuda12.1-cudnn9-runtime --disk 50 --ssh --direct")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Find optimal GPU rental for Convergence Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python find_optimal_gpu.py                       # Balanced search
    python find_optimal_gpu.py --cocoon-training     # Best for cocoon production
    python find_optimal_gpu.py --budget 0.30         # Under $0.30/hr
    python find_optimal_gpu.py --testing             # Cheap testing GPU
    python find_optimal_gpu.py --performance         # Maximum speed
        """
    )
    
    parser.add_argument('--cocoon-training', action='store_true',
                        help='Optimize for cocoon production (24GB+, reliable)')
    parser.add_argument('--testing', action='store_true',
                        help='Find cheap GPU for testing (8GB+)')
    parser.add_argument('--performance', action='store_true',
                        help='Maximum performance (ignore cost)')
    parser.add_argument('--budget', type=float,
                        help='Maximum price per hour (e.g., 0.30)')
    parser.add_argument('--min-vram', type=int, default=8,
                        help='Minimum VRAM in GB (default: 8)')
    parser.add_argument('--top-n', type=int, default=10,
                        help='Number of results to show (default: 10)')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.cocoon_training:
        mode = 'cocoon'
        query_parts = [
            "gpu_ram>=20480",  # 20GB+
            "reliability>=0.95",
            "verified=true",
            "rentable=true"
        ]
        if args.budget:
            query_parts.append(f"dph_total<={args.budget}")
        else:
            query_parts.append("dph_total<=0.80")  # Max $0.80/hr
    elif args.testing:
        mode = 'budget'
        query_parts = [
            f"gpu_ram>={args.min_vram * 1024}",
            "verified=true",
            "rentable=true",
            "dph_total<=0.30"
        ]
    elif args.performance:
        mode = 'performance'
        query_parts = [
            "gpu_ram>=16384",  # 16GB+
            "dlperf>=150",
            "verified=true",
            "rentable=true"
        ]
        if args.budget:
            query_parts.append(f"dph_total<={args.budget}")
    else:  # balanced
        mode = 'balanced'
        query_parts = [
            f"gpu_ram>={args.min_vram * 1024}",
            "reliability>=0.90",
            "verified=true",
            "rentable=true"
        ]
        if args.budget:
            query_parts.append(f"dph_total<={args.budget}")
        else:
            query_parts.append("dph_total<=0.60")  # Max $0.60/hr
    
    query = " ".join(query_parts)
    
    print(f"\n🔍 Searching Vast.ai...")
    print(f"   Query: {query}")
    print(f"   Mode: {mode}")
    
    offers = vast_search(query, order="dph_total", limit=100)
    
    if not offers:
        print("\n❌ No offers found. Try relaxing your filters.")
        print("\nTroubleshooting:")
        print("  1. Check that vast.ai CLI is installed: vastai --version")
        print("  2. Try a broader search: python vast.py search \"rentable=true verified=true\"")
        print("  3. Increase budget: --budget 1.0")
        sys.exit(1)
    
    print(f"   Found {len(offers)} offers\n")
    
    print_offers(offers, mode, args.top_n)


if __name__ == '__main__':
    main()
