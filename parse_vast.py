#!/usr/bin/env python3
"""Quick parser for vast.ai search results"""
import json
import sys

def print_row(r):
    gpu = str(r.get('gpu_name', '?'))[:16]
    vram = r.get('gpu_ram', 0) / 1024
    ram = r.get('cpu_ram', 0) / 1024
    cpus = r.get('cpu_cores', 0)
    price = r.get('dph_total', 0)
    rel = r.get('reliability', 0) or 0
    dlperf = r.get('dlperf', 0) or 0
    print(f"{r['id']:>8} | {gpu:>16} | {vram:>4.0f}GB | {ram:>4.0f}GB | {cpus:>4} | ${price:>8.4f} | {rel:.2f} | {dlperf:>6.1f}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-price', type=float, default=None, help='Max price per hour')
    parser.add_argument('--min-ram', type=float, default=30, help='Min RAM in GB')
    args = parser.parse_args()
    
    try:
        d = json.load(open('vast_results.json'))
    except:
        print("Run: vastai search offers \"rentable=true\" --order dph+ --limit 100 --raw > vast_results.json")
        return
    
    # Filter by price and RAM if specified
    filtered = d
    if args.max_price:
        filtered = [r for r in filtered if r.get('dph_total', 999) <= args.max_price]
    if args.min_ram:
        filtered = [r for r in filtered if r.get('cpu_ram', 0) >= args.min_ram * 1024]
    
    print(f'Found {len(filtered)} offers (max ${args.max_price}/hr, {args.min_ram}GB+ RAM)\n')
    print('ID       | GPU              | VRAM  | RAM   | CPUs | Price/hr  | Rel  | DLPerf')
    print('-' * 95)
    
    # Sort by RAM desc, then price asc
    for r in sorted(filtered, key=lambda x: (-x.get('cpu_ram', 0), x.get('dph_total', 0)))[:20]:
        print_row(r)
    
    if filtered:
        best = min(filtered, key=lambda x: x.get('dph_total', 999))
        print(f"\n💡 Cheapest: python vast.py create {best['id']} --image pytorch/pytorch:latest --disk 50 --ssh --direct")

if __name__ == '__main__':
    main()
