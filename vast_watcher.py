#!/usr/bin/env python3
"""
Vast.ai Deal Snatcher - Auto-rents cheap high-RAM instances and stops them immediately.
"""

import subprocess
import json
import time
import winsound
import sys
import os
from datetime import datetime

# === CONFIG ===
MIN_RAM_GB = 1000        # 1TB+
MAX_PRICE = 0.25         # $0.25/hr max (your target)
POLL_INTERVAL = 60       # Check every 1 minute (faster to catch deals)
AUTO_RENT = True         # Auto-rent when found
AUTO_STOP = True         # Stop immediately after rent (hibernate)
DISK_GB = 100            # Disk to request
IMAGE = "pytorch/pytorch:latest"
MAX_AUTO_RENTS = 1       # Stop after renting this many

# Change to script directory for vast.py access
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def beep_alert(times=5):
    """Make noise to get attention"""
    for _ in range(times):
        winsound.Beep(1000, 300)
        time.sleep(0.2)

def search_vast():
    """Run vast.py search and parse results"""
    try:
        result = subprocess.run(
            ['python', 'vast.py', 'raw', 'search', 'offers', 
             f'cpu_ram>={MIN_RAM_GB}', f'dph<={MAX_PRICE}', 
             '--order', 'dph+', '--raw'],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode != 0:
            return []
        
        try:
            offers = json.loads(result.stdout)
            return offers if isinstance(offers, list) else []
        except json.JSONDecodeError:
            return []
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

def rent_instance(offer_id):
    """Rent an instance and return the instance ID"""
    print(f"   🛒 Renting offer {offer_id}...")
    result = subprocess.run(
        ['python', 'vast.py', 'raw', 'create', 'instance', str(offer_id),
         '--image', IMAGE, '--disk', str(DISK_GB), '--ssh', '--direct', '--raw'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            instance_id = data.get('new_contract') or data.get('instance_id')
            print(f"   ✅ Rented! Instance ID: {instance_id}")
            return instance_id
        except:
            # Try to get instance ID from instances list
            time.sleep(3)
            return get_latest_instance_id()
    else:
        print(f"   ❌ Rent failed: {result.stderr}")
        return None

def get_latest_instance_id():
    """Get the most recent instance ID"""
    result = subprocess.run(
        ['python', 'vast.py', 'raw', 'show', 'instances', '--raw'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        try:
            instances = json.loads(result.stdout)
            if instances:
                return instances[0].get('id')
        except:
            pass
    return None

def stop_instance(instance_id):
    """Stop/hibernate an instance"""
    print(f"   💤 Stopping instance {instance_id} (hibernate)...")
    result = subprocess.run(
        ['python', 'vast.py', 'raw', 'stop', 'instance', str(instance_id)],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        print(f"   ✅ Instance {instance_id} stopped (not charging full rate)")
    else:
        print(f"   ⚠️ Stop might have failed - check manually: python vast.py instances")

def format_offer(o):
    """Format offer for display"""
    return (
        f"  ID: {o.get('id', '?')} | "
        f"{o.get('gpu_name', '?')} x{o.get('num_gpus', 1)} | "
        f"CPU: {o.get('cpu_cores_effective', '?')} | "
        f"RAM: {o.get('cpu_ram', 0)/1024:.1f}TB | "
        f"${o.get('dph_total', 0):.4f}/hr"
    )

def main():
    print("=" * 60)
    print("🎯 VAST.AI DEAL SNATCHER")
    print(f"   Target: {MIN_RAM_GB}GB+ RAM @ ${MAX_PRICE}/hr or less")
    print(f"   Auto-rent: {AUTO_RENT} | Auto-stop: {AUTO_STOP}")
    print(f"   Polling every {POLL_INTERVAL}s")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    
    seen_ids = set()
    rented_count = 0
    
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        offers = search_vast()
        
        if offers:
            new_offers = [o for o in offers if o.get('id') not in seen_ids]
            
            if new_offers:
                print(f"\n[{now}] 🎯 FOUND {len(new_offers)} NEW DEAL(S)!")
                beep_alert(3)
                
                for o in new_offers:
                    offer_id = o.get('id')
                    print(format_offer(o))
                    seen_ids.add(offer_id)
                    
                    if AUTO_RENT and rented_count < MAX_AUTO_RENTS:
                        instance_id = rent_instance(offer_id)
                        if instance_id:
                            rented_count += 1
                            if AUTO_STOP:
                                time.sleep(5)  # Wait for instance to initialize
                                stop_instance(instance_id)
                            
                            beep_alert(5)
                            print(f"\n   🎉 DEAL SNAGGED! Instance {instance_id} is STOPPED.")
                            print(f"   To start: python vast.py start {instance_id}")
                            print(f"   To SSH:   python vast.py ssh {instance_id} --connect")
                            
                            if rented_count >= MAX_AUTO_RENTS:
                                print(f"\n   Reached max auto-rents ({MAX_AUTO_RENTS}). Still watching but won't auto-rent more.")
                else:
                    if not AUTO_RENT:
                        print("\n   Run: python vast.py create <ID> --image pytorch/pytorch:latest --disk 100 --ssh --direct")
            else:
                print(f"[{now}] ✓ {len(offers)} match(es), already seen")
        else:
            print(f"[{now}] - No matches @ ${MAX_PRICE}/hr...")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped watching.")
        sys.exit(0)
