#!/usr/bin/env python3
"""
Log Archiving and Clearing Script

Archives all system logs to a timestamped archive directory,
then clears them for a fresh start.

Usage:
    python archive_logs.py [--archive-dir ARCHIVE_DIR] [--no-archive] [--confirm]

Options:
    --archive-dir DIR    Directory to store archives (default: data/logs_archive)
    --no-archive         Skip archiving, just clear logs (not recommended)
    --confirm            Skip confirmation prompt (use with caution)
"""

import shutil
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Log files to archive/clear (in data/logs/)
LOG_FILES = [
    'application.log',
    'breath.log',
    'djinn_kernel.log',
    'explorer.log',
    'reality_sim.log',
    'state.log',
    'system.log',
]

# Shared state file (in data/)
SHARED_STATE_FILE = '.shared_simulation_state.json'


def get_log_directory() -> Path:
    """Get the log directory path"""
    return Path(__file__).parent / 'data' / 'logs'


def get_archive_directory(base_dir: Optional[Path] = None) -> Path:
    """Get the archive directory path"""
    if base_dir is None:
        base_dir = Path(__file__).parent / 'data' / 'logs_archive'
    return base_dir


def archive_logs(log_dir: Path, archive_dir: Path) -> bool:
    """
    Archive all log files and shared state file to a timestamped directory.
    
    Args:
        log_dir: Directory containing current log files
        archive_dir: Base directory for archives
        
    Returns:
        True if archiving was successful, False otherwise
    """
    # Create timestamped archive directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_path = archive_dir / f'logs_{timestamp}'
    
    try:
        archive_path.mkdir(parents=True, exist_ok=True)
        print(f"📦 Creating archive: {archive_path}")
        
        archived_count = 0
        total_size = 0
        
        # Archive each log file
        for log_file in LOG_FILES:
            source_file = log_dir / log_file
            
            if source_file.exists():
                # Get file size before copying
                file_size = source_file.stat().st_size
                total_size += file_size
                
                # Copy to archive
                dest_file = archive_path / log_file
                shutil.copy2(source_file, dest_file)
                
                archived_count += 1
                size_mb = file_size / (1024 * 1024)
                print(f"  ✅ Archived: {log_file} ({size_mb:.2f} MB)")
            else:
                print(f"  ⚠️  Missing: {log_file} (skipped)")
        
        # Archive shared state file (in data/ directory, not data/logs/)
        data_dir = log_dir.parent
        shared_state_path = data_dir / SHARED_STATE_FILE
        if shared_state_path.exists():
            file_size = shared_state_path.stat().st_size
            total_size += file_size
            
            dest_file = archive_path / SHARED_STATE_FILE
            shutil.copy2(shared_state_path, dest_file)
            
            archived_count += 1
            size_mb = file_size / (1024 * 1024)
            print(f"  ✅ Archived: {SHARED_STATE_FILE} ({size_mb:.2f} MB)")
        
        # Create archive info file
        info_file = archive_path / '_archive_info.txt'
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Archive created: {datetime.now().isoformat()}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Files archived: {archived_count}\n")
            f.write(f"Total size: {total_size / (1024 * 1024):.2f} MB\n")
            f.write(f"\nFiles:\n")
            for log_file in LOG_FILES:
                source_file = log_dir / log_file
                if source_file.exists():
                    size = source_file.stat().st_size
                    f.write(f"  {log_file}: {size / (1024 * 1024):.2f} MB\n")
            if shared_state_path.exists():
                size = shared_state_path.stat().st_size
                f.write(f"  {SHARED_STATE_FILE}: {size / (1024 * 1024):.2f} MB\n")
        
        print(f"\n✅ Successfully archived {archived_count} file(s) ({total_size / (1024 * 1024):.2f} MB)")
        print(f"📁 Archive location: {archive_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error archiving logs: {e}", file=sys.stderr)
        return False


def clear_logs(log_dir: Path) -> bool:
    """
    Clear all log files and shared state file.
    
    Args:
        log_dir: Directory containing log files to clear
        
    Returns:
        True if clearing was successful, False otherwise
    """
    try:
        cleared_count = 0
        
        # Clear log files
        for log_file in LOG_FILES:
            log_path = log_dir / log_file
            
            if log_path.exists():
                # Truncate file to zero size (keeps file but clears content)
                log_path.open('w').close()
                cleared_count += 1
                print(f"  ✅ Cleared: {log_file}")
        
        # Clear shared state file (in data/ directory, not data/logs/)
        data_dir = log_dir.parent
        shared_state_path = data_dir / SHARED_STATE_FILE
        if shared_state_path.exists():
            # Create minimal valid JSON structure
            minimal_state = {
                "frame_count": 0,
                "simulation_fps": 0.0,
                "simulation_time": 0.0,
                "data": {},
                "visualization_data": {},
                "timestamp": 0.0,
                "measurement_precision": 6
            }
            import json
            with open(shared_state_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_state, f, indent=2)
            cleared_count += 1
            print(f"  ✅ Cleared: {SHARED_STATE_FILE}")
        
        print(f"\n✅ Successfully cleared {cleared_count} file(s)")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing logs: {e}", file=sys.stderr)
        return False


def list_archives(archive_dir: Path) -> None:
    """List all existing archives"""
    if not archive_dir.exists():
        print(f"📁 Archive directory doesn't exist yet: {archive_dir}")
        return
    
    archives = sorted([d for d in archive_dir.iterdir() if d.is_dir() and d.name.startswith('logs_')])
    
    if not archives:
        print(f"📁 No archives found in: {archive_dir}")
        return
    
    print(f"\n📚 Existing archives ({len(archives)}):")
    print("=" * 70)
    
    for archive in archives:
        # Read archive info if available
        info_file = archive / '_archive_info.txt'
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                info_lines = f.readlines()
                if info_lines:
                    created = info_lines[0].split(': ', 1)[-1].strip()
                    print(f"  📦 {archive.name}")
                    print(f"     Created: {created}")
                    
                    # Get total size
                    total_size = sum(f.stat().st_size for f in archive.rglob('*.log') if f.is_file())
                    print(f"     Size: {total_size / (1024 * 1024):.2f} MB")
                    print()
        else:
            print(f"  📦 {archive.name}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Archive and clear system logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python archive_logs.py
    # Interactive: archive and clear logs with confirmation
    
  python archive_logs.py --confirm
    # Archive and clear without confirmation prompt
    
  python archive_logs.py --archive-dir data/my_archives
    # Use custom archive directory
    
  python archive_logs.py --list
    # List existing archives without clearing
        """
    )
    
    parser.add_argument(
        '--archive-dir',
        type=Path,
        default=None,
        help='Directory to store archives (default: data/logs_archive)'
    )
    
    parser.add_argument(
        '--no-archive',
        action='store_true',
        help='Skip archiving, just clear logs (not recommended)'
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing archives and exit'
    )
    
    args = parser.parse_args()
    
    log_dir = get_log_directory()
    archive_dir = get_archive_directory(args.archive_dir)
    
    # List archives mode
    if args.list:
        list_archives(archive_dir)
        return 0
    
    # Check if log directory exists
    if not log_dir.exists():
        print(f"❌ Log directory doesn't exist: {log_dir}")
        print("   This is normal if you haven't run the system yet.")
        return 1
    
    # Check if any log files exist
    existing_logs = [f for f in LOG_FILES if (log_dir / f).exists()]
    
    # Check for shared state file
    data_dir = log_dir.parent
    has_shared_state = (data_dir / SHARED_STATE_FILE).exists()
    
    if not existing_logs and not has_shared_state:
        print(f"📁 No log files or shared state found.")
        print("   Everything is already clear!")
        return 0
    
    print("=" * 70)
    print("📦 LOG ARCHIVING AND CLEARING")
    print("=" * 70)
    print(f"\n📁 Log directory: {log_dir}")
    print(f"📦 Archive directory: {archive_dir}")
    print(f"\n📄 Log files found: {len(existing_logs)}/{len(LOG_FILES)}")
    if has_shared_state:
        shared_state_size = (data_dir / SHARED_STATE_FILE).stat().st_size / (1024 * 1024)
        print(f"📄 Shared state file: {SHARED_STATE_FILE} ({shared_state_size:.2f} MB)")
    
    # Show existing archives
    if archive_dir.exists():
        archives = sorted([d for d in archive_dir.iterdir() if d.is_dir() and d.name.startswith('logs_')])
        if archives:
            print(f"📚 Existing archives: {len(archives)}")
    
    print()
    
    # Confirmation
    if not args.confirm:
        print("⚠️  This will:")
        if not args.no_archive:
            print("   1. Archive all current log files and shared state to a timestamped directory")
        print("   2. Clear all log files and reset shared state (clean start)")
        print()
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ('yes', 'y'):
            print("❌ Cancelled.")
            return 1
    
    # Archive logs
    if not args.no_archive:
        print("\n" + "=" * 70)
        print("📦 ARCHIVING LOGS...")
        print("=" * 70)
        if not archive_logs(log_dir, archive_dir):
            print("\n❌ Archiving failed. Aborting to preserve logs.")
            return 1
    
    # Clear logs
    print("\n" + "=" * 70)
    print("🗑️  CLEARING LOGS...")
    print("=" * 70)
    if not clear_logs(log_dir):
        print("\n❌ Clearing failed.")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ DONE!")
    print("=" * 70)
    print("\n🔄 Next steps:")
    print("   1. Run: python unified_entry.py")
    print("   2. Logs will start fresh from zero")
    print()
    
    if not args.no_archive:
        print("💡 To view archived logs:")
        print(f"   python archive_logs.py --list")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

