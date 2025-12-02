#!/usr/bin/env python3
"""
Clear All Runtime Data - Fresh Start Script

Clears all logs, checkpoints, shared state, and runtime data
for a completely fresh run of the Butterfly System.

⚠️ WARNING: This will permanently delete all runtime data!

PRESERVED (Not Deleted):
- data/config.json - System configuration
- data/causation_explorer/ollama_config.json - Ollama settings
- data/linguistic_concepts.json - Linguistic knowledge base
- data/semantic_relations.json - Semantic relations knowledge base
- data/ngram_patterns.json - N-gram patterns knowledge base
- Directory structure - All directories maintained

NOTE: Neural-ML Symbiosis, ConfigTuner, and Health Monitor data is stored in-memory only
(no persistent files to clear - history resets on restart)
"""

import shutil
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def safe_delete_file(file_path: Path, max_retries: int = 3) -> tuple[bool, int, str]:
    """
    Safely delete a file, handling locked files on Windows.
    
    Returns:
        tuple: (success, size_cleared, message)
    """
    if not file_path.exists():
        return True, 0, "already gone"
    
    try:
        size = file_path.stat().st_size
    except:
        size = 0
    
    # Try to delete
    for attempt in range(max_retries):
        try:
            file_path.unlink()
            return True, size, "deleted"
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.1)  # Brief wait before retry
                continue
            
            # File is locked - try to truncate it instead
            try:
                with open(file_path, 'w') as f:
                    f.truncate(0)
                return True, size, "truncated (was locked)"
            except PermissionError:
                return False, 0, "locked by another process"
            except Exception as e:
                return False, 0, f"error: {e}"
        except Exception as e:
            return False, 0, f"error: {e}"
    
    return False, 0, "failed after retries"


def safe_delete_dir(dir_path: Path) -> tuple[bool, str]:
    """Safely delete a directory tree."""
    try:
        shutil.rmtree(dir_path)
        return True, "deleted"
    except PermissionError:
        return False, "locked by another process"
    except Exception as e:
        return False, f"error: {e}"

def clear_all_data():
    """Clear all runtime data for fresh start"""
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    
    if not data_dir.exists():
        print("✅ No data directory found - already clean!")
        return
    
    print("🧹 Clearing all runtime data for fresh start...\n")
    
    cleared_items = []
    skipped_items = []
    total_size = 0
    
    # 1. Clear all log files
    logs_dir = data_dir / 'logs'
    if logs_dir.exists():
        log_files = list(logs_dir.glob('*.log'))
        log_count = 0
        for log_file in log_files:
            success, size, msg = safe_delete_file(log_file)
            if success:
                total_size += size
                cleared_items.append(f"  ✅ Log: {log_file.name} ({size / 1024:.1f} KB) - {msg}")
                log_count += 1
            else:
                skipped_items.append(f"  ⚠️  Log: {log_file.name} - {msg}")
        if log_count > 0:
            print(f"📋 Cleared {log_count} log files")
    
    # 2. Clear all checkpoints
    checkpoints_dir = data_dir / 'checkpoints'
    if checkpoints_dir.exists():
        checkpoint_count = 0
        for checkpoint in checkpoints_dir.glob('*.json'):
            success, size, msg = safe_delete_file(checkpoint)
            if success:
                total_size += size
                checkpoint_count += 1
            else:
                skipped_items.append(f"  ⚠️  Checkpoint: {checkpoint.name} - {msg}")
        if checkpoint_count > 0:
            cleared_items.append(f"  ✅ Checkpoints: {checkpoint_count} files")
            print(f"💾 Cleared {checkpoint_count} checkpoint files")
    
    # 3. Clear shared state
    shared_state = data_dir / '.shared_simulation_state.json'
    if shared_state.exists():
        success, size, msg = safe_delete_file(shared_state)
        if success:
            total_size += size
            cleared_items.append(f"  ✅ Shared state: {size / 1024:.1f} KB")
            print("📊 Cleared shared simulation state")
        else:
            skipped_items.append(f"  ⚠️  Shared state - {msg}")
    
    # 4. Clear context memory
    context_memory = data_dir / 'context_memory.json'
    if context_memory.exists():
        success, size, msg = safe_delete_file(context_memory)
        if success:
            total_size += size
            cleared_items.append(f"  ✅ Context memory: {size / 1024:.1f} KB")
            print("🧠 Cleared context memory")
        else:
            skipped_items.append(f"  ⚠️  Context memory - {msg}")
    
    # 5. Clear simulation control
    sim_control = data_dir / '.simulation_control.json'
    if sim_control.exists():
        success, size, msg = safe_delete_file(sim_control)
        if success:
            total_size += size
            cleared_items.append(f"  ✅ Simulation control: {size / 1024:.1f} KB")
            print("🎮 Cleared simulation control")
        else:
            skipped_items.append(f"  ⚠️  Simulation control - {msg}")
    
    # 6. Clear simulation paused flag
    sim_paused = data_dir / '.simulation_paused'
    if sim_paused.exists():
        success, size, msg = safe_delete_file(sim_paused)
        if success:
            cleared_items.append("  ✅ Simulation paused flag")
            print("⏸️  Cleared pause flag")
        else:
            skipped_items.append(f"  ⚠️  Simulation paused flag - {msg}")
    
    # 7. Clear causation explorer snapshots
    snapshots_dir = data_dir / 'causation_explorer' / 'snapshots'
    if snapshots_dir.exists():
        snapshot_count = 0
        for snapshot in snapshots_dir.glob('*'):
            if snapshot.is_file():
                success, size, msg = safe_delete_file(snapshot)
                if success:
                    total_size += size
                    snapshot_count += 1
                else:
                    skipped_items.append(f"  ⚠️  Snapshot: {snapshot.name} - {msg}")
            elif snapshot.is_dir():
                success, msg = safe_delete_dir(snapshot)
                if success:
                    snapshot_count += 1
                else:
                    skipped_items.append(f"  ⚠️  Snapshot dir: {snapshot.name} - {msg}")
        if snapshot_count > 0:
            cleared_items.append(f"  ✅ Snapshots: {snapshot_count} items")
            print(f"📸 Cleared {snapshot_count} causation explorer snapshots")
    
    # 8. Clear chat history (but keep ollama_config.json)
    chat_history = data_dir / 'causation_explorer' / 'chat_history.json'
    if chat_history.exists():
        success, size, msg = safe_delete_file(chat_history)
        if success:
            total_size += size
            cleared_items.append(f"  ✅ Chat history: {size / 1024:.1f} KB")
            print("💬 Cleared chat history")
        else:
            skipped_items.append(f"  ⚠️  Chat history - {msg}")
    
    # 9. Clear kernel versions
    kernel_versions_dir = data_dir / 'kernel' / 'versions'
    if kernel_versions_dir.exists():
        version_count = 0
        for version_file in kernel_versions_dir.glob('*.json'):
            success, size, msg = safe_delete_file(version_file)
            if success:
                total_size += size
                version_count += 1
            else:
                skipped_items.append(f"  ⚠️  Kernel version: {version_file.name} - {msg}")
        if version_count > 0:
            cleared_items.append(f"  ✅ Kernel versions: {version_count} files")
            print(f"⚙️  Cleared {version_count} kernel version files")
    
    # 10. Clear kernel latest link
    kernel_latest = data_dir / 'kernel' / 'latest.link'
    if kernel_latest.exists():
        success, size, msg = safe_delete_file(kernel_latest)
        if success:
            cleared_items.append("  ✅ Kernel latest link")
            print("🔗 Cleared kernel latest link")
        else:
            skipped_items.append(f"  ⚠️  Kernel latest link - {msg}")
    
    # 11. Clear decision logs
    decision_logs_dir = data_dir / 'decision_logs'
    if decision_logs_dir.exists():
        log_count = 0
        for log_file in decision_logs_dir.glob('*'):
            if log_file.is_file():
                success, size, msg = safe_delete_file(log_file)
                if success:
                    total_size += size
                    log_count += 1
                else:
                    skipped_items.append(f"  ⚠️  Decision log: {log_file.name} - {msg}")
        if log_count > 0:
            cleared_items.append(f"  ✅ Decision logs: {log_count} files")
            print(f"📝 Cleared {log_count} decision log files")
    
    # 12. Clear neural model checkpoints (PyTorch .pt/.pth files)
    neural_models_dir = data_dir / 'neural_models'
    if neural_models_dir.exists():
        model_count = 0
        for model_file in neural_models_dir.glob('*.pt'):
            success, size, msg = safe_delete_file(model_file)
            if success:
                total_size += size
                model_count += 1
            else:
                skipped_items.append(f"  ⚠️  Neural model: {model_file.name} - {msg}")
        for model_file in neural_models_dir.glob('*.pth'):
            success, size, msg = safe_delete_file(model_file)
            if success:
                total_size += size
                model_count += 1
            else:
                skipped_items.append(f"  ⚠️  Neural model: {model_file.name} - {msg}")
        if model_count > 0:
            cleared_items.append(f"  ✅ Neural models: {model_count} files")
            print(f"🧠 Cleared {model_count} neural model checkpoint files")
    
    # Also check checkpoints directory for neural models
    if checkpoints_dir.exists():
        neural_checkpoint_count = 0
        for checkpoint in checkpoints_dir.glob('*.pt'):
            success, size, msg = safe_delete_file(checkpoint)
            if success:
                total_size += size
                neural_checkpoint_count += 1
            else:
                skipped_items.append(f"  ⚠️  Neural checkpoint: {checkpoint.name} - {msg}")
        for checkpoint in checkpoints_dir.glob('*.pth'):
            success, size, msg = safe_delete_file(checkpoint)
            if success:
                total_size += size
                neural_checkpoint_count += 1
            else:
                skipped_items.append(f"  ⚠️  Neural checkpoint: {checkpoint.name} - {msg}")
        if neural_checkpoint_count > 0:
            cleared_items.append(f"  ✅ Neural checkpoints: {neural_checkpoint_count} files")
            print(f"🧠 Cleared {neural_checkpoint_count} neural model files from checkpoints")
    
    # Note: Knowledge base files are PRESERVED (not runtime data):
    # - linguistic_concepts.json
    # - semantic_relations.json
    # - ngram_patterns.json
    # - config.json
    # - causation_explorer/ollama_config.json
    
    # Summary
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE!")
    print("="*60)
    print(f"📊 Total data cleared: {total_size / (1024*1024):.2f} MB")
    print(f"📁 Items cleared: {len(cleared_items)}")
    
    if skipped_items:
        print(f"\n⚠️  Skipped {len(skipped_items)} items (files in use):")
        for item in skipped_items:
            print(item)
        print("\n💡 Tip: Close any running simulations/servers and try again")
        print("   to fully clear locked files.")
    
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

