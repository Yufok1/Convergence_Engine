#!/usr/bin/env python3
"""
Clear All Runtime Data - Fresh Start Script

Clears all logs, checkpoints, shared state, and runtime data
for a completely fresh run of the Butterfly System.

⚠️ WARNING: This will permanently delete all runtime data!
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def clear_all_data():
    """Clear all runtime data for fresh start"""
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    
    if not data_dir.exists():
        print("✅ No data directory found - already clean!")
        return
    
    print("🧹 Clearing all runtime data for fresh start...\n")
    
    cleared_items = []
    total_size = 0
    
    # 1. Clear all log files
    logs_dir = data_dir / 'logs'
    if logs_dir.exists():
        for log_file in logs_dir.glob('*.log'):
            if log_file.exists():
                size = log_file.stat().st_size
                total_size += size
                log_file.unlink()
                cleared_items.append(f"  ✅ Log: {log_file.name} ({size / 1024:.1f} KB)")
        print(f"📋 Cleared {len([f for f in logs_dir.glob('*.log')])} log files")
    
    # 2. Clear all checkpoints
    checkpoints_dir = data_dir / 'checkpoints'
    if checkpoints_dir.exists():
        checkpoint_count = 0
        for checkpoint in checkpoints_dir.glob('*.json'):
            if checkpoint.exists():
                size = checkpoint.stat().st_size
                total_size += size
                checkpoint.unlink()
                checkpoint_count += 1
        if checkpoint_count > 0:
            cleared_items.append(f"  ✅ Checkpoints: {checkpoint_count} files")
            print(f"💾 Cleared {checkpoint_count} checkpoint files")
    
    # 3. Clear shared state
    shared_state = data_dir / '.shared_simulation_state.json'
    if shared_state.exists():
        size = shared_state.stat().st_size
        total_size += size
        shared_state.unlink()
        cleared_items.append(f"  ✅ Shared state: {size / 1024:.1f} KB")
        print("📊 Cleared shared simulation state")
    
    # 4. Clear context memory
    context_memory = data_dir / 'context_memory.json'
    if context_memory.exists():
        size = context_memory.stat().st_size
        total_size += size
        context_memory.unlink()
        cleared_items.append(f"  ✅ Context memory: {size / 1024:.1f} KB")
        print("🧠 Cleared context memory")
    
    # 5. Clear simulation control
    sim_control = data_dir / '.simulation_control.json'
    if sim_control.exists():
        size = sim_control.stat().st_size
        total_size += size
        sim_control.unlink()
        cleared_items.append(f"  ✅ Simulation control: {size / 1024:.1f} KB")
        print("🎮 Cleared simulation control")
    
    # 6. Clear simulation paused flag
    sim_paused = data_dir / '.simulation_paused'
    if sim_paused.exists():
        sim_paused.unlink()
        cleared_items.append("  ✅ Simulation paused flag")
        print("⏸️  Cleared pause flag")
    
    # 7. Clear causation explorer snapshots
    snapshots_dir = data_dir / 'causation_explorer' / 'snapshots'
    if snapshots_dir.exists():
        snapshot_count = 0
        for snapshot in snapshots_dir.glob('*'):
            if snapshot.is_file():
                size = snapshot.stat().st_size
                total_size += size
                snapshot.unlink()
                snapshot_count += 1
            elif snapshot.is_dir():
                shutil.rmtree(snapshot)
                snapshot_count += 1
        if snapshot_count > 0:
            cleared_items.append(f"  ✅ Snapshots: {snapshot_count} items")
            print(f"📸 Cleared {snapshot_count} causation explorer snapshots")
    
    # 8. Clear chat history (but keep ollama_config.json)
    chat_history = data_dir / 'causation_explorer' / 'chat_history.json'
    if chat_history.exists():
        size = chat_history.stat().st_size
        total_size += size
        chat_history.unlink()
        cleared_items.append(f"  ✅ Chat history: {size / 1024:.1f} KB")
        print("💬 Cleared chat history")
    
    # 9. Clear kernel versions
    kernel_versions_dir = data_dir / 'kernel' / 'versions'
    if kernel_versions_dir.exists():
        version_count = 0
        for version_file in kernel_versions_dir.glob('*.json'):
            if version_file.exists():
                size = version_file.stat().st_size
                total_size += size
                version_file.unlink()
                version_count += 1
        if version_count > 0:
            cleared_items.append(f"  ✅ Kernel versions: {version_count} files")
            print(f"⚙️  Cleared {version_count} kernel version files")
    
    # 10. Clear kernel latest link
    kernel_latest = data_dir / 'kernel' / 'latest.link'
    if kernel_latest.exists():
        kernel_latest.unlink()
        cleared_items.append("  ✅ Kernel latest link")
        print("🔗 Cleared kernel latest link")
    
    # 11. Clear decision logs
    decision_logs_dir = data_dir / 'decision_logs'
    if decision_logs_dir.exists():
        log_count = 0
        for log_file in decision_logs_dir.glob('*'):
            if log_file.is_file():
                size = log_file.stat().st_size
                total_size += size
                log_file.unlink()
                log_count += 1
        if log_count > 0:
            cleared_items.append(f"  ✅ Decision logs: {log_count} files")
            print(f"📝 Cleared {log_count} decision log files")
    
    # Summary
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE!")
    print("="*60)
    print(f"📊 Total data cleared: {total_size / (1024*1024):.2f} MB")
    print(f"📁 Items cleared: {len(cleared_items)}")
    print("\n✨ Your system is now ready for a fresh run!")
    print("   Start with: python unified_entry.py")
    print("="*60)

if __name__ == '__main__':
    try:
        clear_all_data()
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

