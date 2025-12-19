"""
Cloud Environment Auto-Setup Module

Automatically configures storage paths for cloud environments like:
- Vast.ai (has RAM disk at /dev/shm, limited overlay)
- Colab (has /content drive)
- Lambda Labs, RunPod, etc.

Call setup_cloud_environment() at startup before any disk I/O.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

_logger = logging.getLogger(__name__)

# Storage priority (higher = better)
STORAGE_PRIORITIES = {
    'ram_disk': 100,      # /dev/shm - fastest, survives container restarts
    'nvme_mount': 80,     # /workspace, /mnt/*, etc
    'tmp': 60,            # /tmp - may be tmpfs (RAM) or disk
    'local': 20,          # Current directory - may be tiny overlay
}


def get_disk_space_gb(path: str) -> float:
    """Get available disk space in GB for a path."""
    try:
        stat = os.statvfs(path)
        return (stat.f_bavail * stat.f_frsize) / (1024**3)
    except (OSError, AttributeError):
        # Windows or path doesn't exist
        try:
            total, used, free = shutil.disk_usage(path)
            return free / (1024**3)
        except Exception:
            return 0.0


def detect_storage_options() -> Dict[str, Dict[str, Any]]:
    """Detect available storage locations and their capacities."""
    options = {}
    
    # Check RAM disk
    if os.path.isdir('/dev/shm'):
        space = get_disk_space_gb('/dev/shm')
        if space > 1:  # At least 1GB
            options['ram_disk'] = {
                'path': '/dev/shm/convergence_data',
                'space_gb': space,
                'type': 'RAM disk',
                'priority': STORAGE_PRIORITIES['ram_disk'],
            }
    
    # Check common cloud mounts
    for mount in ['/workspace', '/mnt/data', '/content', '/home/user']:
        if os.path.isdir(mount):
            space = get_disk_space_gb(mount)
            if space > 10:  # At least 10GB
                options[f'mount_{mount}'] = {
                    'path': f'{mount}/convergence_data',
                    'space_gb': space,
                    'type': f'mount ({mount})',
                    'priority': STORAGE_PRIORITIES['nvme_mount'],
                }
    
    # Check /tmp
    if os.path.isdir('/tmp'):
        space = get_disk_space_gb('/tmp')
        if space > 5:  # At least 5GB
            options['tmp'] = {
                'path': '/tmp/convergence_data',
                'space_gb': space,
                'type': '/tmp',
                'priority': STORAGE_PRIORITIES['tmp'],
            }
    
    # Local directory (fallback)
    options['local'] = {
        'path': './data',
        'space_gb': get_disk_space_gb('.'),
        'type': 'local',
        'priority': STORAGE_PRIORITIES['local'],
    }
    
    return options


def select_best_storage(options: Dict[str, Dict[str, Any]], min_space_gb: float = 20.0) -> Tuple[str, Dict[str, Any]]:
    """Select the best storage location from available options."""
    
    # Filter by minimum space requirement
    viable = {k: v for k, v in options.items() if v['space_gb'] >= min_space_gb}
    
    if not viable:
        # Fall back to largest available
        viable = options
    
    # Sort by priority (descending), then space (descending)
    best_key = max(viable.keys(), key=lambda k: (viable[k]['priority'], viable[k]['space_gb']))
    
    return best_key, viable[best_key]


def setup_data_directory(target_path: str, project_root: Path) -> bool:
    """Set up the data directory with symlink to target storage."""
    
    data_path = project_root / 'data'
    target = Path(target_path)
    
    # Create target directories
    subdirs = ['logs', 'checkpoints', 'neural_checkpoints', 'kernel', 
               'profiles', 'knowledge', 'decision_logs', 'causation_explorer']
    
    try:
        target.mkdir(parents=True, exist_ok=True)
        for subdir in subdirs:
            (target / subdir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        _logger.error(f"Failed to create target directories: {e}")
        return False
    
    # Handle existing data directory
    try:
        if data_path.is_symlink():
            data_path.unlink()
        elif data_path.is_dir():
            # Move existing data to target
            for item in data_path.iterdir():
                dest = target / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
            shutil.rmtree(data_path)
    except Exception as e:
        _logger.warning(f"Could not clean up existing data dir: {e}")
    
    # Create symlink (Unix only)
    if sys.platform != 'win32':
        try:
            data_path.symlink_to(target)
            return True
        except Exception as e:
            _logger.error(f"Failed to create symlink: {e}")
            return False
    else:
        # Windows - just use local path
        return False


def get_system_info() -> Dict[str, Any]:
    """Get system information for config selection."""
    info = {
        'ram_gb': 0,
        'cpu_threads': os.cpu_count() or 1,
        'gpu_vram_mb': 0,
        'platform': sys.platform,
    }
    
    # Get RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    kb = int(line.split()[1])
                    info['ram_gb'] = kb // (1024 * 1024)
                    break
    except Exception:
        try:
            import psutil
            info['ram_gb'] = psutil.virtual_memory().total // (1024**3)
        except Exception:
            pass
    
    # Get GPU VRAM
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            info['gpu_vram_mb'] = int(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    
    return info


def recommend_config(system_info: Dict[str, Any], project_root: Path) -> str:
    """Recommend the best config file based on system resources."""
    
    ram_gb = system_info.get('ram_gb', 0)
    
    # Priority order: largest RAM requirement first
    # Each tuple: (config_name, min_ram_gb)
    configs = [
        ('config_vast_epyc_2tb.json', 1800),        # 1.8TB+ RAM (EPYC 2TB monster)
        ('config_vast_xeon_1.5tb_genesis.json', 1000),  # 1TB+ RAM (Xeon 1.5TB genesis)
        ('config_vast_epyc_2tb.json', 100),         # 100GB+ RAM (fallback to EPYC config)
        ('config_colab_cpu.json', 40),              # 40GB+ RAM  
        ('config.json', 0),                          # Default
    ]
    
    for config_name, min_ram in configs:
        config_path = project_root / config_name
        if config_path.exists() and ram_gb >= min_ram:
            return config_name
    
    return 'config.json'


def clear_caches() -> None:
    """Clear various caches to free up disk space."""
    
    cache_dirs = [
        os.path.expanduser('~/.cache/pip'),
        '/tmp/chamber_*',
        '/var/log/*.log',
    ]
    
    import glob
    for pattern in cache_dirs:
        for path in glob.glob(pattern):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
            except Exception:
                pass


def setup_cloud_environment(project_root: Optional[Path] = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Main entry point - auto-configure environment for cloud deployment.
    
    Returns dict with:
        - storage_path: Path where data will be stored
        - storage_type: Type of storage (RAM disk, NVMe, etc.)
        - storage_space_gb: Available space
        - recommended_config: Best config file to use
        - system_info: CPU/RAM/GPU details
    """
    
    if project_root is None:
        project_root = Path(__file__).parent
    
    if sys.platform == 'win32':
        # Skip cloud setup on Windows
        return {
            'storage_path': str(project_root / 'data'),
            'storage_type': 'local',
            'storage_space_gb': get_disk_space_gb(str(project_root)),
            'recommended_config': 'config.json',
            'system_info': get_system_info(),
            'setup_performed': False,
        }
    
    if verbose:
        print("=" * 50)
        print("🚀 Convergence Engine - Auto Setup")
        print("=" * 50)
    
    # Detect storage options
    options = detect_storage_options()
    
    if verbose:
        print("\n📊 Detected storage options:")
        for name, opt in sorted(options.items(), key=lambda x: -x[1]['priority']):
            print(f"   {opt['type']}: {opt['space_gb']:.1f}GB available")
    
    # Select best storage
    storage_key, storage_info = select_best_storage(options)
    
    if verbose:
        print(f"\n🎯 Selected: {storage_info['type']} ({storage_info['space_gb']:.1f}GB)")
    
    # Set up data directory
    if storage_info['path'] != './data':
        success = setup_data_directory(storage_info['path'], project_root)
        if success and verbose:
            print(f"   ✅ Symlinked ./data -> {storage_info['path']}")
    else:
        # Ensure local data dir exists
        (project_root / 'data').mkdir(parents=True, exist_ok=True)
    
    # Get system info
    sys_info = get_system_info()
    
    if verbose:
        print(f"\n💻 System: {sys_info['ram_gb']}GB RAM, {sys_info['cpu_threads']} threads", end='')
        if sys_info['gpu_vram_mb'] > 0:
            print(f", {sys_info['gpu_vram_mb']}MB VRAM")
        else:
            print()
    
    # Recommend config
    recommended = recommend_config(sys_info, project_root)
    
    if verbose:
        print(f"⚙️  Recommended config: {recommended}")
    
    # Clear caches if space is tight
    root_space = get_disk_space_gb('/')
    if root_space < 2.0:
        if verbose:
            print("\n🧹 Clearing caches (low disk space)...")
        clear_caches()
    
    if verbose:
        print("\n" + "=" * 50)
        print("✅ Setup complete!")
        print("=" * 50 + "\n")
    
    return {
        'storage_path': storage_info['path'],
        'storage_type': storage_info['type'],
        'storage_space_gb': storage_info['space_gb'],
        'recommended_config': recommended,
        'system_info': sys_info,
        'setup_performed': True,
    }


# Auto-run on import if in cloud environment
_CLOUD_INDICATORS = [
    '/dev/shm',           # Unix shared memory
    '/workspace',         # Vast.ai, Lambda Labs
    '/content',           # Colab
]

def is_cloud_environment() -> bool:
    """Check if we're running in a cloud environment."""
    if sys.platform == 'win32':
        return False
    return any(os.path.isdir(path) for path in _CLOUD_INDICATORS)


if __name__ == '__main__':
    # Run setup when called directly
    result = setup_cloud_environment()
    print(f"\nRun with:")
    print(f"  python unified_entry.py --config {result['recommended_config']}")
