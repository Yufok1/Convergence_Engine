"""
UNIFIED ENTRY POINT - THE BUTTERFLY SYSTEM

Single cohesive unit: Explorer + Reality Simulator + Djinn Kernel
One process. One breath. Three systems unified.

Features:
- Pre-flight system checks (redundant, comprehensive)
- Extensive state logging (granular, terse, information-saturated)
- Unified visualization (Left: Reality Sim, Middle: Explorer, Right: Djinn Kernel)
- All systems wired as one machine
- Neural organism decision-making with Illumination Engine
- Alliance Warfare system with collective wisdom
- Highlander survival tournament protocol
- Memory leak prevention with automatic cleanup

Usage:
    python unified_entry.py                    # Run with visualization
    python unified_entry.py --headless         # Run without visualization (server mode)
    python unified_entry.py --web-only         # Run web UI only (no simulation)
"""

# MUST be set before ANY imports that might touch Ray
import os
os.environ['RAY_METRICS_AGENT_DISABLED'] = '1'
os.environ['RAY_ENABLE_WINDOWS_OR_OSX_CLUSTER'] = '1'

# Suppress PyTorch inductor warnings (spammy but harmless)
# These come from torch.compile's kernel optimization - safe to ignore
import warnings
warnings.filterwarnings('ignore', message='.*Online softmax is disabled.*')
warnings.filterwarnings('ignore', message='.*TensorFloat32 tensor cores.*')
warnings.filterwarnings('ignore', message='.*Not enough SMs to use max_autotune_gemm.*')
warnings.filterwarnings('ignore', module='torch._inductor.*')
warnings.filterwarnings('ignore', category=UserWarning, module='torch')

# Also suppress via logging for inductor
import logging as _logging
_logging.getLogger('torch._inductor').setLevel(_logging.ERROR)
_logging.getLogger('torch._inductor.utils').setLevel(_logging.CRITICAL)
_logging.getLogger('torch._dynamo').setLevel(_logging.ERROR)

# Enable TensorFloat32 for better performance on Ampere+ GPUs
try:
    import torch
    torch.set_float32_matmul_precision('high')
except ImportError:
    pass

import sys
import time
import json
import logging
import threading
import queue
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import datetime as dt_module
import traceback
import webbrowser
import subprocess
import shutil
import re

from runtime_config import ConfigHotReloadWatcher, set_global_config_path


def _is_colab_runtime() -> bool:
    """Best-effort detection for Google Colab runtime."""
    if os.environ.get('COLAB_GPU') or os.environ.get('COLAB_TPU_ADDR'):
        return True
    try:
        import google.colab  # type: ignore
        _ = google.colab
        return True
    except Exception:
        return False


def _try_get_colab_proxy_url(port: int) -> Optional[str]:
    """Return a Colab-proxied URL for a localhost port, or None if unavailable."""
    if not _is_colab_runtime():
        return None
    try:
        from google.colab.output import eval_js  # type: ignore
        url = eval_js(f"google.colab.kernel.proxyPort({int(port)})")
        return str(url) if url else None
    except Exception:
        return None


def _maybe_start_localhostrun_tunnel(local_port: int, remote_port: int = 80) -> Optional[subprocess.Popen]:
    """Optionally start an ssh reverse tunnel to localhost.run.

    Opt-in only: set UNIFIED_TUNNEL=localhostrun.
    This is intentionally conservative to avoid impacting local/dev behavior.
    """
    if os.environ.get('UNIFIED_TUNNEL', '').strip().lower() != 'localhostrun':
        return None
    if shutil.which('ssh') is None:
        print("[UNIFIED] [WEB] [TUNNEL] ssh not found; cannot start localhost.run tunnel")
        return None

    # Avoid interactive host-key prompt.
    # Note: this bypasses host key verification; only enable if you understand the risk.
    ssh_cmd = [
        'ssh',
        '-T',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'LogLevel=ERROR',
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ServerAliveInterval=30',
        '-R', f"{int(remote_port)}:localhost:{int(local_port)}",
        'nokey@localhost.run',
    ]

    try:
        proc = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        print(f"[UNIFIED] [WEB] [TUNNEL] Starting localhost.run tunnel: remote :{remote_port} -> localhost:{local_port}")
        print("[UNIFIED] [WEB] [TUNNEL] Waiting for tunnel URL in logs...")
        return proc
    except Exception as e:
        print(f"[UNIFIED] [WEB] [TUNNEL] Failed to start tunnel: {e}")
        return None


def _maybe_start_cloudflared_tunnel(local_port: int) -> Optional[subprocess.Popen]:
    """Optionally start a Cloudflare quick tunnel via cloudflared.

    Opt-in only: set UNIFIED_TUNNEL=cloudflared.
    """
    if os.environ.get('UNIFIED_TUNNEL', '').strip().lower() != 'cloudflared':
        return None
    if shutil.which('cloudflared') is None:
        print("[UNIFIED] [WEB] [TUNNEL] cloudflared not found; cannot start Cloudflare tunnel")
        return None

    # cloudflared prints the public URL to stdout; no interactive prompts.
    cmd = ['cloudflared', 'tunnel', '--url', f"http://localhost:{int(local_port)}"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        print(f"[UNIFIED] [WEB] [TUNNEL] Starting cloudflared tunnel -> localhost:{local_port}")
        print("[UNIFIED] [WEB] [TUNNEL] Waiting for tunnel URL in logs...")
        return proc
    except Exception as e:
        print(f"[UNIFIED] [WEB] [TUNNEL] Failed to start cloudflared tunnel: {e}")
        return None


def _select_auto_tunnel_mode() -> str:
    """Select a tunnel mode when UNIFIED_TUNNEL=auto.

    Preference order:
      1) Colab proxy (handled separately)
      2) cloudflared (if installed)
      3) localhostrun (if ssh installed)
    """
    if shutil.which('cloudflared') is not None:
        return 'cloudflared'
    if shutil.which('ssh') is not None:
        return 'localhostrun'
    return 'none'


def _extract_first_url(text_line: str) -> Optional[str]:
    m = re.search(r"https?://\S+", text_line)
    if not m:
        return None
    # Trim common trailing punctuation
    url = m.group(0).rstrip(').,;\"\'')
    # localhost.run prints docs/help URLs that are not the actual public tunnel.
    # Ignore those so we keep scanning for the real session URL.
    if url.startswith('https://localhost.run/docs') or url.startswith('http://localhost.run/docs'):
        return None
    return url


def _write_tunnel_url(url: str) -> None:
    """Optionally write the current public URL to a file for easy retrieval."""
    out_path = os.environ.get('UNIFIED_TUNNEL_URL_FILE', '').strip()
    if not out_path:
        return
    try:
        # If relative, anchor to project directory
        if not os.path.isabs(out_path):
            out_path = str(Path(__file__).parent / out_path)
        Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(url + "\n")
    except Exception as e:
        print(f"[UNIFIED] [WEB] [TUNNEL] Could not write URL file: {e}")

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logging early (before imports that may fail)
try:
    from logging_config import setup_logging, get_logger
    setup_logging(level=logging.INFO, debug=False, console=True)
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging_config not available
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(__name__)

# Setup paths
parent_path = Path(__file__).parent
explorer_path = parent_path / 'explorer'
reality_sim_path = parent_path / 'reality_simulator'
kernel_path = parent_path / 'kernel'

sys.path.insert(0, str(explorer_path))
sys.path.insert(0, str(reality_sim_path))
sys.path.insert(0, str(kernel_path))

# Import all systems
try:
    from explorer.main import BiphasicController
    from explorer.breath_engine import BreathEngine
    EXPLORER_AVAILABLE = True
except ImportError as e:
    EXPLORER_AVAILABLE = False
    logger.warning(f"Explorer not available: {e}")

try:
    from reality_simulator.main import RealitySimulator
    REALITY_SIM_AVAILABLE = True
except ImportError as e:
    REALITY_SIM_AVAILABLE = False
    logger.warning(f"Reality Simulator not available: {e}")

try:
    # Import from kernel (now has proper __init__.py for package recognition)
    from utm_kernel_design import UTMKernel
    from violation_pressure_calculation import ViolationMonitor
    from lawfold_field_architecture import LawfoldFieldOrchestrator
    DJINN_KERNEL_AVAILABLE = True
except ImportError as e:
    DJINN_KERNEL_AVAILABLE = False
    logger.warning(f"Djinn Kernel not available: {e}")

# Import integration facilities
try:
    from reality_simulator.phase_sync_bridge import PhaseSynchronizationBridge
    PHASE_SYNC_AVAILABLE = True
except ImportError as e:
    PHASE_SYNC_AVAILABLE = False
    logger.warning(f"Phase Sync Bridge not available: {e}")


# ============================================================================
# PRE-FLIGHT SYSTEM CHECKS
# ============================================================================

@dataclass
class SystemCheck:
    """Result of a system check"""
    name: str
    status: str  # 'pass', 'warn', 'fail'
    message: str
    details: Dict[str, Any] = None

class PreFlightChecker:
    """Comprehensive pre-flight system checks"""
    
    def __init__(self):
        self.checks: List[SystemCheck] = []
        self.critical_failures = []
        self.warnings = []
    
    def check_dependencies(self, require_visualization: bool = True) -> List[SystemCheck]:
        """Check all Python dependencies
        
        Args:
            require_visualization: If False, matplotlib/tkinter are optional (for headless runs)
        """
        checks = []
        
        # Core dependencies (always required)
        core_deps = {
            'numpy': 'numpy',
            'networkx': 'networkx',
        }
        
        for dep_name, import_name in core_deps.items():
            try:
                __import__(import_name)
                checks.append(SystemCheck(
                    name=f"dep_{dep_name}",
                    status='pass',
                    message=f"{dep_name} available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name=f"dep_{dep_name}",
                    status='fail',
                    message=f"{dep_name} missing"
                ))
                self.critical_failures.append(f"Missing dependency: {dep_name}")
        
        # Visualization dependencies - optional for headless runs
        try:
            __import__('matplotlib')
            checks.append(SystemCheck(
                name="dep_matplotlib",
                status='pass',
                message="matplotlib available"
            ))
        except ImportError:
            if require_visualization:
                checks.append(SystemCheck(
                    name="dep_matplotlib",
                    status='fail',
                    message="matplotlib missing (required for visualization)"
                ))
                self.critical_failures.append("Missing dependency: matplotlib (required for visualization)")
            else:
                checks.append(SystemCheck(
                    name="opt_matplotlib",
                    status='warn',
                    message="matplotlib missing (optional for headless runs)"
                ))
                self.warnings.append("Optional dependency missing: matplotlib (only needed for visualization)")
        
        # Visualization dependencies (optional for headless runs)
        if require_visualization:
            try:
                __import__('tkinter')
                checks.append(SystemCheck(
                    name="dep_tkinter",
                    status='pass',
                    message="tkinter available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name="dep_tkinter",
                    status='fail',
                    message="tkinter missing (required for visualization)"
                ))
                self.critical_failures.append("Missing dependency: tkinter (required for visualization)")
        else:
            # Optional for headless runs
            try:
                __import__('tkinter')
                checks.append(SystemCheck(
                    name="opt_tkinter",
                    status='pass',
                    message="tkinter available (optional, not required for headless)"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name="opt_tkinter",
                    status='warn',
                    message="tkinter missing (optional for headless runs)"
                ))
                self.warnings.append("Optional dependency missing: tkinter (only needed for visualization)")
        
        # Optional dependencies
        optional_deps = {
            'win32job': 'pywin32 (optional, for Explorer)',
        }
        
        for dep_name, description in optional_deps.items():
            try:
                __import__(dep_name)
                checks.append(SystemCheck(
                    name=f"opt_{dep_name}",
                    status='pass',
                    message=f"{description} available"
                ))
            except ImportError:
                checks.append(SystemCheck(
                    name=f"opt_{dep_name}",
                    status='warn',
                    message=f"{description} missing (optional)"
                ))
                self.warnings.append(f"Optional dependency missing: {description}")
        
        return checks
    
    def check_systems(self) -> List[SystemCheck]:
        """Check system availability"""
        checks = []
        
        checks.append(SystemCheck(
            name="explorer",
            status='pass' if EXPLORER_AVAILABLE else 'fail',
            message="Explorer available" if EXPLORER_AVAILABLE else "Explorer not available"
        ))
        
        checks.append(SystemCheck(
            name="reality_sim",
            status='pass' if REALITY_SIM_AVAILABLE else 'fail',
            message="Reality Simulator available" if REALITY_SIM_AVAILABLE else "Reality Simulator not available"
        ))
        
        checks.append(SystemCheck(
            name="djinn_kernel",
            status='pass' if DJINN_KERNEL_AVAILABLE else 'fail',
            message="Djinn Kernel available" if DJINN_KERNEL_AVAILABLE else "Djinn Kernel not available"
        ))
        
        if not EXPLORER_AVAILABLE:
            self.critical_failures.append("Explorer is required")
        if not REALITY_SIM_AVAILABLE:
            self.critical_failures.append("Reality Simulator is required")
        if not DJINN_KERNEL_AVAILABLE:
            self.warnings.append("Djinn Kernel not available (will run without it)")
        
        return checks
    
    def check_files(self) -> List[SystemCheck]:
        """Check required files exist"""
        checks = []
        
        required_files = {
            'config.json': parent_path / 'config.json',
            'explorer/main.py': explorer_path / 'main.py',
            'reality_simulator/main.py': reality_sim_path / 'main.py',
        }
        
        for name, path in required_files.items():
            if path.exists():
                checks.append(SystemCheck(
                    name=f"file_{name}",
                    status='pass',
                    message=f"{name} exists"
                ))
            else:
                checks.append(SystemCheck(
                    name=f"file_{name}",
                    status='fail',
                    message=f"{name} missing"
                ))
                self.critical_failures.append(f"Required file missing: {name}")
        
        return checks
    
    def check_directories(self) -> List[SystemCheck]:
        """Check required directories exist"""
        checks = []
        
        required_dirs = {
            'explorer': explorer_path,
            'reality_simulator': reality_sim_path,
            'kernel': kernel_path,
            'data': parent_path / 'data',
        }
        
        for name, path in required_dirs.items():
            if path.exists() and path.is_dir():
                checks.append(SystemCheck(
                    name=f"dir_{name}",
                    status='pass',
                    message=f"{name}/ exists"
                ))
            else:
                checks.append(SystemCheck(
                    name=f"dir_{name}",
                    status='warn',
                    message=f"{name}/ missing (will be created)"
                ))
                self.warnings.append(f"Directory missing: {name}/")
        
        return checks
    
    def check_memory(self) -> List[SystemCheck]:
        """Check system memory"""
        checks = []
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            mem_gb = mem.total / (1024**3)
            
            if mem_gb >= 4.0:
                checks.append(SystemCheck(
                    name="memory",
                    status='pass',
                    message=f"Memory: {mem_gb:.1f}GB available",
                    details={'total_gb': mem_gb, 'available_gb': mem.available / (1024**3)}
                ))
            elif mem_gb >= 2.0:
                checks.append(SystemCheck(
                    name="memory",
                    status='warn',
                    message=f"Memory: {mem_gb:.1f}GB (low)",
                    details={'total_gb': mem_gb}
                ))
                self.warnings.append("Low system memory")
            else:
                checks.append(SystemCheck(
                    name="memory",
                    status='fail',
                    message=f"Memory: {mem_gb:.1f}GB (insufficient)"
                ))
                self.critical_failures.append("Insufficient system memory")
        except ImportError:
            checks.append(SystemCheck(
                name="memory",
                status='warn',
                message="Memory check unavailable (psutil not installed)"
            ))
        
        return checks
    
    def run_all_checks(self, require_visualization: bool = True) -> Dict[str, Any]:
        """Run all pre-flight checks
        
        Args:
            require_visualization: If False, tkinter is optional (for headless runs)
        """
        print("\n" + "="*70)
        print("[BUTTERFLY] PRE-FLIGHT SYSTEM CHECKS")
        print("="*70)
        
        all_checks = []
        all_checks.extend(self.check_dependencies(require_visualization=require_visualization))
        all_checks.extend(self.check_systems())
        all_checks.extend(self.check_files())
        all_checks.extend(self.check_directories())
        all_checks.extend(self.check_memory())
        
        self.checks = all_checks
        
        # Print results
        for check in all_checks:
            if check.status == 'pass':
                print(f"[PASS] {check.name}: {check.message}")
            elif check.status == 'warn':
                print(f"[WARN] {check.name}: {check.message}")
            else:
                print(f"[FAIL] {check.name}: {check.message}")
        
        print("\n" + "="*70)
        
        if self.critical_failures:
            print("[FAIL] CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   - {failure}")
            print("\n[WARN] System cannot start with critical failures.")
            return {
                'can_start': False, 
                'checks': all_checks, 
                'warnings': self.warnings,
                'failures': self.critical_failures
            }
        
        if self.warnings:
            print("[WARN] WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
            print("\n[WARN] System will start with warnings.")
        
        print("[PASS] All critical checks passed. System ready to start.")
        print("="*70 + "\n")
        
        return {
            'can_start': True,
            'checks': all_checks,
            'warnings': self.warnings,
            'failures': self.critical_failures
        }


# ============================================================================
# STATE LOGGING SYSTEM
# ============================================================================

class StateLogger:
    """Extensive, granular, terse, information-saturated state logging
    
    Uses async queue for non-blocking disk I/O - main thread never waits on file writes.
    Queue is bounded (fail-open): if full, drops log entries rather than blocking.
    """
    
    def __init__(self, log_dir: Path = None, causation_explorer=None, config: Dict = None):
        self.log_dir = log_dir or (parent_path / 'data' / 'logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.causation_explorer = causation_explorer  # For live event tracking
        
        # Configuration
        config = config or {}
        logging_config = config.get('logging', {})
        self.sample_rate = logging_config.get('sample_rate', 1)  # 1 = log all, 10 = log 1/10
        self._sample_counter = 0
        
        # Async logging queue (bounded, fail-open)
        self._log_queue = queue.Queue(maxsize=10000)
        self._drop_count = 0
        self._shutdown = False
        
        # Create loggers
        self.loggers = {
            'state': self._create_logger('state', 'state.log'),
            'breath': self._create_logger('breath', 'breath.log'),
            'reality_sim': self._create_logger('reality_sim', 'reality_sim.log'),
            'explorer': self._create_logger('explorer', 'explorer.log'),
            'djinn_kernel': self._create_logger('djinn_kernel', 'djinn_kernel.log'),
            'neural': self._create_logger('neural', 'neural.log'),
            'system': self._create_logger('system', 'system.log'),
        }
        
        # State tracking (always full rate - memory is fast)
        self.state_history = []
        self.max_history = 10000
        self.last_event_time = 0  # Track last event timestamp
        
        # Start background writer thread
        self._writer_thread = threading.Thread(target=self._async_writer, daemon=True, name="StateLogger-Writer")
        self._writer_thread.start()
    
    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """Create a logger with terse, information-saturated format"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_dir / filename)
        file_handler.setLevel(logging.DEBUG)
        
        # Terse format: timestamp|level|component|metric:value|metric:value|...
        # Use custom formatter for microseconds support
        class MicrosecondFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                dt = dt_module.datetime.fromtimestamp(record.created)
                return dt.strftime('%H:%M:%S.%f')[:-3]  # Truncate to milliseconds
        
        formatter = MicrosecondFormatter(
            '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _async_writer(self):
        """Background thread that writes log entries to disk."""
        while True:
            try:
                entry = self._log_queue.get(timeout=1.0)
                if entry is None:  # Sentinel for shutdown
                    break
                
                component, state_str = entry
                logger = self.loggers.get(component, self.loggers['system'])
                logger.debug(state_str)
                
            except queue.Empty:
                if self._shutdown:
                    break
            except Exception:
                pass  # Never crash the writer thread
    
    def shutdown(self):
        """Graceful shutdown - drain queue and stop writer thread."""
        self._shutdown = True
        try:
            self._log_queue.put_nowait(None)  # Sentinel
        except queue.Full:
            pass
        self._writer_thread.join(timeout=5.0)
        
        if self._drop_count > 0:
            print(f"[StateLogger] Dropped {self._drop_count} log entries during session")
    
    def log_state(self, component: str, state: Dict[str, Any], causation_explorer=None):
        """Log state in terse, information-saturated format (non-blocking)"""
        timestamp = time.time()
        
        # Always update in-memory state (fast path - never sampled)
        history_entry = {
            'timestamp': timestamp,
            'component': component,
            'state': state
        }
        self.state_history.append(history_entry)
        
        # Trim history
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
        
        # Update last event timestamp
        self.last_event_time = timestamp
        
        # Feed to Causation Explorer in real-time if available
        if self.causation_explorer:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=timestamp,
                    component=component,
                    event_type=state.get('event', 'state_change'),
                    data=state
                )
                self.causation_explorer.add_event(event, is_historical=False)
            except Exception:
                pass
        
        # Sample-based disk logging (async, non-blocking)
        self._sample_counter += 1
        if self._sample_counter >= self.sample_rate:
            self._sample_counter = 0
            state_str = '|'.join([f"{k}:{v}" for k, v in state.items()])
            
            try:
                self._log_queue.put_nowait((component, state_str))
            except queue.Full:
                # Fail-open: drop log entry rather than block
                self._drop_count += 1
                if self._drop_count % 1000 == 0:
                    print(f"[StateLogger] Warning: dropped {self._drop_count} log entries (queue full)")
    
    def log_breath(self, breath_data: Dict[str, Any]):
        """Log breath state"""
        self.log_state('breath', {
            'cycle': breath_data.get('cycle_count', 0),
            'depth': f"{breath_data.get('depth', 0):.3f}",
            'phase': f"{breath_data.get('phase', 0):.3f}",
            'pulse': f"{breath_data.get('intensity', 0):.3f}",
        })
    
    def log_reality_sim(self, network_data: Dict[str, Any]):
        """Log Reality Simulator state"""
        self.log_state('reality_sim', {
            'orgs': network_data.get('organism_count', 0),
            'conns': network_data.get('connection_count', 0),
            'mod': f"{network_data.get('modularity', 0):.3f}",
            'clust': f"{network_data.get('clustering_coefficient', 0):.3f}",
            'path': f"{network_data.get('average_path_length', 0):.2f}",
            'gen': network_data.get('generation', 0),
        })
    
    def log_explorer(self, explorer_data: Dict[str, Any]):
        """Log Explorer state"""
        self.log_state('explorer', {
            'phase': explorer_data.get('phase', 'unknown'),
            'vp_calcs': explorer_data.get('vp_calculations', 0),
            'sovereign_ids': explorer_data.get('sovereign_ids_count', 0),
            'math_cap': explorer_data.get('mathematical_capability', False),
        })
    
    def log_djinn_kernel(self, kernel_data: Dict[str, Any]):
        """Log Djinn Kernel state"""
        self.log_state('djinn_kernel', {
            'vp': f"{kernel_data.get('violation_pressure', 0):.3f}",
            'vp_class': kernel_data.get('vp_classification', 'unknown'),
            'vp_calcs': kernel_data.get('vp_calculations', 0),
            'traits': kernel_data.get('trait_count', 0),
        })
    
    def log_neural(self, neural_data: Dict[str, Any]):
        """Log Neural System state"""
        # Use same fallback chain as visualization: ema_loss > training_loss > avg_loss
        ema_loss = neural_data.get('ema_loss')
        training_loss = neural_data.get('training_loss')
        avg_loss = neural_data.get('avg_loss')
        
        # Determine display loss (matching visualization_viewer.py logic)
        if ema_loss is not None:
            display_loss = f"{ema_loss:.6f}"
        elif training_loss is not None:
            display_loss = f"{training_loss:.6f}"
        elif avg_loss is not None and avg_loss != 0.0:
            display_loss = f"{avg_loss:.6f}"
        else:
            display_loss = 'N/A'
        
        self.log_state('neural', {
            'enabled': neural_data.get('enabled', False),
            'training_loss': display_loss,
            'avg_epsilon': f"{neural_data.get('avg_epsilon', 0):.3f}",
            'organisms_tracked': neural_data.get('organisms_tracked', 0),
            'training_steps': neural_data.get('training_steps', 0),
            'avg_loss': f"{avg_loss:.6f}" if avg_loss is not None else 'N/A',
        })


# ============================================================================
# UNIFIED VISUALIZATION
# ============================================================================

class UnifiedVisualization:
    """Three-panel visualization: Left=Reality Sim, Middle=Explorer, Right=Djinn Kernel"""

    def __init__(self, network_ref=None, renderer_ref=None, reality_sim_ref=None):
        self.root = None
        self.fig = None
        self.axes = {}
        self.running = False
        self._network_ref = network_ref  # Reference to Reality Simulator network
        self._renderer_ref = renderer_ref  # Reference to Reality Simulator renderer
        self.reality_sim = reality_sim_ref  # Reference to Reality Simulator itself for metrics
        self.grid_enabled = True  # Grid toggle state
        self.canvas = None  # Store canvas reference for redraw
        self._last_reality_sim_state = {}  # Store last state for redraw
        
    def initialize(self):
        """Initialize matplotlib GUI with 3D network visualization"""
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import tkinter as tk

            self.root = tk.Tk()
            self.root.title("The Convergence Engine - 3D Network Visualization")
            self.root.geometry("1280x720")

            # Create figure with 3D network graph - make left panel dominant (60% width)
            from mpl_toolkits.mplot3d import Axes3D
            import matplotlib.gridspec as gridspec
            self.fig = plt.figure(figsize=(12.8, 7.2), facecolor='black')
            
            # Create GridSpec with 60/20/20 width ratios
            gs = gridspec.GridSpec(1, 5, figure=self.fig, width_ratios=[3, 0.2, 1, 0.2, 1], wspace=0.05)
            
            self.axes = {
                'left': self.fig.add_subplot(gs[0, 0], projection='3d'),   # Reality Simulator - 60% width, 3D
                'middle': self.fig.add_subplot(gs[0, 2]),                 # Explorer - 20% width
                'right': self.fig.add_subplot(gs[0, 4])                  # Djinn Kernel - 20% width
            }
            
            # Tight layout for cleaner appearance
            self.fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.04, wspace=0.05)

            # Setup axes
            for name, ax in self.axes.items():
                ax.set_facecolor('black')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')

            # Left axis is already 3D from GridSpec setup above

            # Embed in tkinter
            self.canvas = FigureCanvasTkAgg(self.fig, self.root)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Add grid toggle button
            self._create_grid_toggle_button()

            self.running = True
            print("[VISUALIZATION] [PASS] 3D network visualization initialized")

        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Error initializing: {e}")
            self.running = False
    
    def show(self):
        """Show the visualization window - called from main thread"""
        if self.root and self.running:
            try:
                # Make sure window is visible
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                print("[VISUALIZATION] [PASS] Visualization window displayed")
            except Exception as e:
                print(f"[VISUALIZATION] [WARN] Error showing window: {e}")
    
    def _create_grid_toggle_button(self):
        """Create toggle button for grid visibility"""
        try:
            import tkinter as tk
            button = tk.Button(
                self.root,
                text="Grid: ON",
                command=self._toggle_grid,
                bg="#050505",
                fg="#00ffff",
                activebackground="#1a1a1a",
                activeforeground="#00ffff",
                relief=tk.FLAT,
                padx=12,
                pady=6,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                borderwidth=1,
                highlightthickness=1,
                highlightbackground="#00ffff"
            )
            button.place(relx=0.99, rely=0.02, anchor='ne')
            self.grid_toggle_button = button
        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Error creating grid toggle: {e}")
    
    def _toggle_grid(self):
        """Toggle grid visibility and redraw"""
        self.grid_enabled = not self.grid_enabled
        if hasattr(self, 'grid_toggle_button'):
            self.grid_toggle_button.config(text=f"Grid: {'ON' if self.grid_enabled else 'OFF'}")
        # Redraw the reality sim panel with new grid state
        if self._last_reality_sim_state:
            djinn_state = getattr(self, '_last_djinn_kernel_state', {})
            explorer_state = getattr(self, '_last_explorer_state', {})
            self._update_reality_sim_panel(self.axes['left'], self._last_reality_sim_state, djinn_state, explorer_state)
            if self.canvas:
                self.canvas.draw()


    def update(self, reality_sim_state: Dict, explorer_state: Dict, djinn_kernel_state: Dict):
        """Update all three panels"""
        if not self.running:
            return

        try:
            import matplotlib.pyplot as plt
            # Prefer a Windows font that supports emojis
            # Suppress font warnings for missing emoji glyphs (expected behavior)
            import warnings
            warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')
            try:
                import matplotlib as mpl
                mpl.rcParams['font.family'] = ['Segoe UI Emoji', 'Segoe UI Symbol', 'DejaVu Sans']
            except Exception:
                pass

            # Left panel: Reality Simulator 3D Network
            self._last_reality_sim_state = reality_sim_state  # Store for grid toggle redraw
            self._last_djinn_kernel_state = djinn_kernel_state  # Store for grid toggle redraw
            self._last_explorer_state = explorer_state  # Store for grid toggle redraw
            self._update_reality_sim_panel(self.axes['left'], reality_sim_state, djinn_kernel_state, explorer_state)

            # Middle panel: Explorer
            self._update_explorer_panel(self.axes['middle'], explorer_state)

            # Right panel: Djinn Kernel
            self._update_djinn_kernel_panel(self.axes['right'], djinn_kernel_state)

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
            # Process tkinter events so window updates properly (this is why the first window doesn't populate)
            if self.root:
                try:
                    self.root.update_idletasks()  # Process pending idle events
                    self.root.update()            # Process all pending events
                except (tk.TclError, RuntimeError):
                    pass  # Window might be closed or destroyed

        except Exception as e:
            print(f"[VISUALIZATION] [WARN] Update error: {e}")
    
    def _update_reality_sim_panel(self, ax, state: Dict, djinn_kernel_state: Dict = None, explorer_state: Dict = None):
        """Update Reality Simulator panel using 3D network visualization"""
        try:
            import sys
            import os
            from pathlib import Path
            import importlib.util

            # Import the visualization viewer
            viewer_path = Path(__file__).parent / 'reality_simulator' / 'visualization_viewer.py'
            if viewer_path.exists():
                spec = importlib.util.spec_from_file_location("visualization_viewer", viewer_path)
                viz_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(viz_module)

                # Create a viewer instance (or reuse if exists)
                if not hasattr(self, '_viewer'):
                    self._viewer = viz_module.LightweightVisualizationViewer()

                # Prepare data in the format expected by the viewer
                network = getattr(self, '_network_ref', None)

                # Build network data dict with actual graph edges and metrics
                network_data = {
                    'network': {
                        'organisms': state.get('organism_count', 0),
                        'connections': state.get('connection_count', 0),
                        'graph_edges': []
                    },
                    'stability': 0.0,
                    'connectivity': 0.0
                }

                # Get actual graph edges and metrics if network is available
                if network and hasattr(network, 'network_graph'):
                    G = network.network_graph
                    # Convert node IDs to integers for the viewer (it expects integer nodes)
                    node_map = {node: i for i, node in enumerate(G.nodes())}
                    network_data['network']['graph_edges'] = [(node_map[u], node_map[v]) for u, v in G.edges()]

                    # Add network metrics for diagnostic panels
                    if hasattr(network, 'metrics'):
                        stability = getattr(network.metrics, 'stability_index', 0.0)
                        connectivity = getattr(network.metrics, 'connectivity', 0.0)
                        network_data['stability'] = stability
                        network_data['connectivity'] = connectivity

                # Combine data from ALL systems for comprehensive diagnostic panels
                # Get neural data
                neural_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, '_neural_metrics'):
                    neural_data = self.reality_sim._neural_metrics

                # Get ML data
                ml_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, '_ml_metrics'):
                    ml_data = self.reality_sim._ml_metrics

                # Get evolution data - organisms live in network component
                evolution_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'components'):
                    network = self.reality_sim.components.get('network')
                    evolution = self.reality_sim.components.get('evolution')

                    # Get organisms from network component
                    if network and hasattr(network, 'organisms'):
                        organisms = network.organisms
                        # Handle organisms as dict or list
                        org_values = organisms.values() if isinstance(organisms, dict) else organisms
                        org_count = len(organisms) if organisms else 0

                        if org_count > 0:
                            fitnesses = [org.fitness for org in org_values if hasattr(org, 'fitness')]
                            generation = evolution.generation if evolution and hasattr(evolution, 'generation') else 0

                            evolution_data = {
                                'generation': generation,
                                'population_size': org_count,
                                'best_fitness': max(fitnesses) if fitnesses else 0.0,
                                'avg_fitness': sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
                            }
                        else:
                            evolution_data = {
                                'generation': 0,
                                'population_size': 0,
                                'best_fitness': 0.0,
                                'avg_fitness': 0.0
                            }

                # Get config_tuner data
                config_tuner_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
                    tuner_stats = self.reality_sim.config_tuner.get_stats()
                    config_tuner_data = {
                        'enabled': True,
                        'mode': self.reality_sim.config.get('meta_cognitive', {}).get('self_tuning', {}).get('mode', 'unknown'),
                        'stats': tuner_stats
                    }

                # Get djinn_kernel data (VP info) - passed as parameter
                djinn_kernel_data = djinn_kernel_state if djinn_kernel_state else {}

                # Get quantum data
                quantum_data = {}
                if hasattr(self, 'reality_sim') and hasattr(self.reality_sim, 'components'):
                    quantum = self.reality_sim.components.get('quantum')
                    if quantum:
                        quantum_data = {
                            'states': len(quantum.states) if hasattr(quantum, 'states') else 0
                        }

                # Get explorer data from parameter (for Panel 6: EXPLORER Body)
                explorer_data = explorer_state if explorer_state else {}

                viz_data = {
                    'network': network_data,
                    'neural': neural_data,
                    'ml': ml_data,
                    'evolution': evolution_data,
                    'config_tuner': config_tuner_data,
                    'djinn_kernel': djinn_kernel_data,
                    'quantum': quantum_data,
                    'explorer': explorer_data  # Add explorer data for Panel 6
                }

                # Ensure 3D axes
                from mpl_toolkits.mplot3d import Axes3D
                if not hasattr(ax, 'name') or getattr(ax, 'name', '') != '3d':
                    fig = ax.figure
                    try:
                        fig.delaxes(ax)
                    except (AttributeError, ValueError):
                        pass  # Axes already removed or invalid
                    ax = fig.add_subplot(131, projection='3d')
                    self.axes['left'] = ax

                # Render using the existing 3D method (includes enhanced diagnostic panels!)
                self._viewer.render_network_graph(viz_data, ax)

                # NOTE: Do NOT remove text overlays - render_network_graph now includes
                # comprehensive 5-panel diagnostic dashboard utilizing empty space!
                # Panels: Network Topology, Neural/ML, Evolution/VP, Meta-Cognitive, Events

                # Make network dominant - set equal aspect and proper limits
                ax.set_box_aspect([1, 1, 1])
                
                # Add highly contrastive 3D grid background (only if enabled)
                if self.grid_enabled:
                    import numpy as np
                    # Use fewer grid lines for better performance and clarity
                    grid_range = np.linspace(-1, 1, 6)  # 6 lines per axis = clearer grid
                    grid_color = '#00ffff'  # Bright cyan for high contrast
                    grid_alpha = 0.5  # More visible
                    grid_linewidth = 0.8  # Thicker lines
                    
                    # Draw grid lines on key planes only (reduces clutter)
                    # XY plane at z = -1, 0, 1
                    for z_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([i, i], [-1, 1], [z_val, z_val], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([-1, 1], [i, i], [z_val, z_val], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                    
                    # XZ plane at y = -1, 0, 1
                    for y_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([i, i], [y_val, y_val], [-1, 1], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([-1, 1], [y_val, y_val], [i, i], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                    
                    # YZ plane at x = -1, 0, 1
                    for x_val in [-1, 0, 1]:
                        for i in grid_range:
                            ax.plot([x_val, x_val], [i, i], [-1, 1], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)
                            ax.plot([x_val, x_val], [-1, 1], [i, i], color=grid_color, alpha=grid_alpha, linewidth=grid_linewidth)

                # Remove the hard-to-see box frame completely
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_zticks([])
                ax.xaxis.pane.fill = False
                ax.yaxis.pane.fill = False
                ax.zaxis.pane.fill = False
                # Make pane edges invisible
                ax.xaxis.pane.set_edgecolor('black')
                ax.yaxis.pane.set_edgecolor('black')
                ax.zaxis.pane.set_edgecolor('black')
                ax.xaxis.pane.set_alpha(0)
                ax.yaxis.pane.set_alpha(0)
                ax.zaxis.pane.set_alpha(0)
                
                # Remove axis lines for cleaner look
                ax.xaxis.line.set_color('black')
                ax.yaxis.line.set_color('black')
                ax.zaxis.line.set_color('black')

                # Title at top (centered, clear and prominent)
                ax.set_title('Reality Simulator Network', color='cyan', fontsize=18, fontweight='bold', pad=20)
                
                # All stats clustered around the grid area (bottom-center, integrated with grid visualization)
                orgs = state.get('organism_count', 0)
                conns = state.get('connection_count', 0)
                mod = state.get('modularity', 0)
                clust = state.get('clustering_coefficient', 0)
                path_len = state.get('average_path_length', 0)
                
                # NOTE: Stats box removed from visual display (2025-12-03)
                # Data still available via state dict for other panels/APIs
                # Original stats box was overlapping Explorer menu and showing redundant info
                # Metrics accessible via: Panel 1 (Network Topology), /api/state, causation graph
                
                # all_stats = (
                #     f"ORGANISMS: {orgs}\n"
                #     f"CONNECTIONS: {conns}\n"
                #     f"MODULARITY: {mod:.3f}\n"
                #     f"CLUSTERING: {clust:.3f}\n"
                #     f"PATH LENGTH: {path_len:.2f}"
                # )
                # Position stats box on left side, between Network Topology and Evolution panels
                # ax.text2D(0.10, 0.50, all_stats, ha='left', va='center', color='cyan',
                #          fontsize=10, family='monospace', fontweight='bold', transform=ax.transAxes,
                #          bbox=dict(boxstyle='round,pad=0.7', facecolor='black', alpha=0.9, edgecolor='cyan', linewidth=2.5))

                # System label - top left corner near title (small, unobtrusive)
                ax.text2D(0.10, 0.95, 'Left Wing', ha='left', va='top', color='cyan',
                         fontsize=9, family='monospace', style='italic', transform=ax.transAxes, alpha=0.6)

                return
        except Exception as e:
            import traceback
            print(f"[VISUALIZATION] Error in 3D network render: {e}")
            traceback.print_exc()

        # Fallback: Simple text display
        try:
            ax.clear()
            ax.set_facecolor('black')
            orgs = state.get('organism_count', 0)
            conns = state.get('connection_count', 0)
            mod = state.get('modularity', 0)
            clust = state.get('clustering_coefficient', 0)
            info = f"Organisms: {orgs}\nConnections: {conns}\nModularity: {mod:.3f}\nClustering: {clust:.3f}"
            ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=12,
                    family='monospace', transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        except (AttributeError, ValueError, TypeError):
            pass  # Visualization update failed - non-critical

    def _update_explorer_panel(self, ax, state: Dict):
        """Update Explorer panel"""
        ax.clear()
        ax.set_facecolor('black')
        ax.set_title('Explorer (Body)', color='yellow', fontsize=14, fontweight='bold')

        # Explorer metrics
        phase = state.get('phase', 'unknown')
        vp_calcs = state.get('vp_calculations', 0)
        breath_cycle = state.get('breath_cycle', 0)
        breath_depth = state.get('breath_depth', 0)

        # Clean, informative display
        info = f"""EXPLORER SYSTEM

Phase: {phase.upper()}
VP Calculations: {vp_calcs}
Breath Cycle: {breath_cycle}
Breath Depth: {breath_depth:.3f}

Status: ACTIVE"""
        ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=11,
                family='monospace', transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    def _update_djinn_kernel_panel(self, ax, state: Dict):
        """Update Djinn Kernel panel"""
        ax.clear()
        ax.set_facecolor('black')
        ax.set_title('Djinn Kernel (Right Wing)', color='magenta', fontsize=14, fontweight='bold')

        # Djinn Kernel metrics
        vp = state.get('violation_pressure', 0)
        vp_class = state.get('vp_classification', 'unknown')
        vp_calcs = state.get('vp_calculations', 0)

        # Clean, informative display
        info = f"""DJINN KERNEL

Violation Pressure: {vp:.3f}
VP Classification: {vp_class.upper()}
VP Calculations: {vp_calcs}

Status: ACTIVE"""
        ax.text(0.5, 0.5, info, ha='center', va='center', color='white', fontsize=11,
                family='monospace', transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')


# ============================================================================
# UNIFIED SYSTEM
# ============================================================================

class UnifiedSystem:
    """The unified butterfly system - one cohesive unit"""
    
    def __init__(self, enable_visualization: bool = True, max_cycles: int = 0,
                 highlander_config: Optional[Dict] = None, config_path: str = 'config.json'):
        # Pre-flight checks (tkinter optional for headless runs)
        checker = PreFlightChecker()
        check_results = checker.run_all_checks(require_visualization=enable_visualization)
        
        if not check_results['can_start']:
            raise RuntimeError("Pre-flight checks failed. Cannot start system.")
        
        # Store Highlander config
        self.highlander_config = highlander_config
        self.highlander_protocol = None
        self.battle_arena = None
        self.capsule_manager = None
        self.germination_pool = None
        
        # Store config path for use throughout the system
        self.config_path = Path(config_path)
        
        # Load config first so we can pass it to StateLogger
        self.config_watcher = ConfigHotReloadWatcher(self.config_path)
        self.active_config = self.config_watcher.get_current_config()
        
        # Initialize logging with config (for sample_rate etc)
        self.logger = StateLogger(config=self.active_config)
        self.logger.log_state('system', {'event': 'initialization_start'})
        
        # Apply Hardware Governor - MUST happen before any other system uses config
        # Hardware envelope supersedes CRA self-tuning for hardware-critical params
        try:
            from reality_simulator.hardware_governor import apply_hardware_envelope, get_hardware_governor
            force_profile = self.active_config.get('hardware_profile', None)  # Allow manual override
            self.active_config = apply_hardware_envelope(self.active_config, force_profile)
            self.hardware_governor = get_hardware_governor()
            print(f"[UNIFIED] [PASS] Hardware Governor: {self.hardware_governor.capabilities.profile.value.upper()} mode")
        except Exception as hw_err:
            print(f"[UNIFIED] [WARN] Hardware Governor not applied: {hw_err}")
            self.hardware_governor = None
        
        # Initialize systems FIRST (before visualization, which needs references)
        print("\n[UNIFIED] Initializing systems...")
        
        # Explorer (body)
        if EXPLORER_AVAILABLE:
            try:
                self.controller = BiphasicController(config_path=str(self.config_path))
                if hasattr(self.controller, 'apply_runtime_config'):
                    try:
                        applied = self.controller.apply_runtime_config(self.active_config)
                        if applied:
                            print(f"[UNIFIED] [CONFIG] Applied startup config overrides: {applied}")
                    except Exception as config_err:
                        print(f"[UNIFIED] [WARN] Failed to apply startup config overrides: {config_err}")
                print("[UNIFIED] [PASS] Explorer initialized")
                self.logger.log_state('system', {'event': 'explorer_initialized'})
            except Exception as e:
                print(f"[UNIFIED] [FAIL] Explorer initialization failed: {e}")
                traceback.print_exc()
                self.controller = None
        else:
            self.controller = None
        
        # Reality Simulator (left wing) - already initialized in Explorer
        self.reality_sim = getattr(self.controller, 'reality_sim', None) if self.controller else None
        
        # Wire breath engine reference to Reality Simulator for neural training
        if self.reality_sim and self.controller and hasattr(self.controller, 'breath_engine'):
            self.reality_sim.breath_engine_ref = self.controller.breath_engine
        
        # Djinn Kernel (right wing) - already initialized in Explorer
        self.vp_monitor = getattr(self.controller, 'vp_monitor', None) if self.controller else None
        self.utm_kernel = getattr(self.controller, 'utm_kernel', None) if self.controller else None

        # Lawfold Field Architecture (civilization governance)
        if self.utm_kernel and DJINN_KERNEL_AVAILABLE:
            try:
                self.lawfold_orchestrator = LawfoldFieldOrchestrator(self.utm_kernel)
                self.lawfold_orchestrator.activate_all_fields()
                print("[UNIFIED] [PASS] Lawfold Field Architecture initialized")
                self.logger.log_state('system', {'event': 'lawfold_fields_initialized'})
            except Exception as e:
                print(f"[UNIFIED] [FAIL] Lawfold Field Architecture initialization failed: {e}")
                traceback.print_exc()
                self.lawfold_orchestrator = None
        else:
            self.lawfold_orchestrator = None

        # Initialize Causation Explorer
        try:
            from causation_explorer import CausationExplorer
            # Load config for causation detection (use self.config_path from CLI)
            causation_config = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r') as f:
                        full_config = json.load(f)
                        causation_config = full_config
                except Exception:
                    pass
            self.causation_explorer = CausationExplorer(
                state_logger=self.logger,
                log_dir=self.logger.log_dir,
                utm_kernel=self.utm_kernel,
                config=causation_config
            )
            # Connect StateLogger to CausationExplorer
            self.logger.causation_explorer = self.causation_explorer
            print("[UNIFIED] [PASS] Causation Explorer initialized")
            self.logger.log_state('system', {'event': 'causation_explorer_initialized'})
        except ImportError as e:
            print(f"[UNIFIED] [WARN] Causation Explorer not available: {e}")
            self.causation_explorer = None
        except Exception as e:
            print(f"[UNIFIED] [WARN] Causation Explorer initialization failed: {e}")
            self.causation_explorer = None

        # ═══════════════════════════════════════════════════════════════════════════
        # INTEGRATION FIX: Wire event handlers to make system reactive, not just observant
        # This closes the loop: events → handlers → config tuning → behavior changes
        # ═══════════════════════════════════════════════════════════════════════════
        if self.causation_explorer and self.reality_sim:
            self._wire_reactive_event_handlers()

        # Wire event emitter for neural/ML visualization (AFTER causation_explorer is initialized)
        if self.reality_sim and self.causation_explorer:
            from causation_explorer import Event
            
            # ═══════════════════════════════════════════════════════════════════════════
            # UNIFIED EVENT EMITTER - Routes events to ALL consumers:
            # 1. CausationExplorer - for visualization and root cause analysis
            # 2. ConfigTuner (legacy) - for cross-system correlation analysis
            # 3. AtomicConfigSystem - for atomic config tracking
            # ═══════════════════════════════════════════════════════════════════════════
            
            # Get reference to legacy ConfigTuner for track_event (cross-system correlation)
            legacy_config_tuner = None
            try:
                from reality_simulator.config_tuner_legacy import ConfigTuner
                # Initialize legacy config tuner if it exists
                if hasattr(self.reality_sim, 'config') and self.reality_sim.config:
                    legacy_config_tuner = ConfigTuner(self.reality_sim.config, enabled=True)
                    self.reality_sim.legacy_config_tuner = legacy_config_tuner  # Store reference
                    print("[UNIFIED] [INTEGRATION] ✅ Initialized legacy ConfigTuner for cross-system correlation")
            except ImportError:
                pass  # Legacy tuner not available
            
            def neural_event_emitter(event_input):
                """Emit neural/ML events to ALL consumers - handles both dicts and Event objects"""
                try:
                    # Handle both Event objects and dicts
                    if isinstance(event_input, Event):
                        # Already an Event object, use it directly
                        event = event_input
                        event_dict = {
                            'timestamp': event.timestamp,
                            'component': event.component,
                            'event_type': event.event_type,
                            'data': event.data,
                            'event_id': getattr(event, 'event_id', None)
                        }
                    elif isinstance(event_input, dict):
                        # Convert dict to Event object
                        event = Event(
                            timestamp=event_input.get('timestamp', time.time()),
                            component=event_input.get('component', 'unknown'),
                            event_type=event_input.get('event_type', 'unknown'),
                            data=event_input.get('data', {})
                        )
                        event_dict = event_input
                    else:
                        # Unknown type, skip
                        return
                    
                    # 1. Send to CausationExplorer (visualization)
                    self.causation_explorer.add_event(event, is_historical=False)
                    
                    # 2. Send to legacy ConfigTuner track_event (cross-system correlation)
                    # This populates recent_events for _find_recent_event() calls
                    if legacy_config_tuner is not None:
                        legacy_config_tuner.track_event(event_dict)
                        
                except Exception as e:
                    # Don't break if event emission fails, but log for debugging
                    if not hasattr(self, '_event_emitter_error_logged'):
                        print(f"[UNIFIED] [WARN] Event emission failed: {e}")
                        self._event_emitter_error_logged = True
                    pass
            
            self.reality_sim.event_emitter = neural_event_emitter

            # ═══════════════════════════════════════════════════════════════════════════
            # INTEGRATION FIX: Wire event emitter to AtomicConfigSystem (config_tuner)
            # This fixes the race condition where config_tuner was created with None
            # because event_emitter wasn't set on reality_sim yet during __init__
            # ═══════════════════════════════════════════════════════════════════════════
            if hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
                self.reality_sim.config_tuner.set_event_emitter(neural_event_emitter)
                print("[UNIFIED] [INTEGRATION] ✅ Wired event_emitter to AtomicConfigSystem (config_tuner)")

            # CRITICAL: Wire context_memory and vocabulary event emitters for language events
            # This MUST happen BEFORE any word assignments occur
            # Do this immediately after network is created, not later
            if hasattr(self.reality_sim, 'components') and 'network' in self.reality_sim.components:
                network = self.reality_sim.components['network']
                if hasattr(network, 'context_memory') and network.context_memory:
                    # Wire event_emitter immediately - this ensures word_assignment events are emitted
                    network.context_memory.event_emitter = neural_event_emitter
                    # Also wire vocabulary if it exists
                    if hasattr(network.context_memory, 'vocabulary') and network.context_memory.vocabulary:
                        network.context_memory.vocabulary.event_emitter = neural_event_emitter
                    print(f"[UNIFIED] [LANGUAGE] Wired event_emitter to context_memory (event_emitter is {'set' if neural_event_emitter else 'None'})")
                
                # SEMANTIC CONVERGENCE: Wire neural_trainer to network for ConceptSystem access
                if hasattr(self.reality_sim, 'neural_trainer') and self.reality_sim.neural_trainer:
                    if hasattr(network, 'set_neural_trainer'):
                        network.set_neural_trainer(self.reality_sim.neural_trainer)
                        print("[UNIFIED] [SEMANTIC] ✅ Wired neural_trainer to network for ConceptSystem access")

            # Also wire ML event emitter on the network (clustering, anomaly, phenotype events)
            try:
                network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                if network and hasattr(network, 'ml_event_emitter'):
                    network.ml_event_emitter = neural_event_emitter  # Reuse same emitter for ML events

                    # Configure ML analyzer from config if available and enabled
                    if hasattr(network, 'configure_ml_analyzer'):
                        try:
                            if self.config_path.exists():
                                with open(self.config_path, 'r') as f:
                                    full_config = json.load(f)
                                    scikit_config = full_config.get('scikit', {})
                                    if scikit_config.get('enabled', False):
                                        network.configure_ml_analyzer(scikit_config)
                                        print("[UNIFIED] [PASS] 🧠 ML Analyzer configured (Scikit-learn)")
                        except Exception as e:
                            print(f"[UNIFIED] [WARN] ML Analyzer configuration failed: {e}")
                    
                    # Configure Health Monitor (Quick Win #5)
                    if hasattr(network, 'configure_health_monitor'):
                        try:
                            if self.config_path.exists():
                                with open(self.config_path, 'r') as f:
                                    full_config = json.load(f)
                                    health_config = full_config.get('health_monitor', {})
                                    if health_config.get('enabled', True):
                                        network.configure_health_monitor(health_config, event_emitter=neural_event_emitter)
                                        print("[UNIFIED] [PASS] ❤️ Health Monitor configured")
                        except Exception as e:
                            print(f"[UNIFIED] [WARN] Health Monitor configuration failed: {e}")
            except Exception:
                # Don't let ML wiring break initialization
                pass
        else:
            print(f"[UNIFIED] [WARN] Cannot wire event emitter - reality_sim: {bool(self.reality_sim)}, causation_explorer: {bool(self.causation_explorer)}")
            # NOTE: ML wiring skipped when reality_sim is not available

        # Initialize Phase Sync Bridge (CRITICAL INTEGRATION!)
        if PHASE_SYNC_AVAILABLE:
            try:
                self.phase_sync_bridge = PhaseSynchronizationBridge(
                    collapse_threshold=500,
                    max_connections_per_organism=5
                )
                # Wire up the ACTUAL Explorer components from the controller (not fresh instances!)
                if self.controller:
                    self.phase_sync_bridge.explorer_sentinel = self.controller.sentinel if hasattr(self.controller, 'sentinel') else self.phase_sync_bridge.explorer_sentinel
                    self.phase_sync_bridge.explorer_kernel = self.controller.kernel if hasattr(self.controller, 'kernel') else self.phase_sync_bridge.explorer_kernel
                    self.phase_sync_bridge.explorer_breath = self.controller.breath_engine if hasattr(self.controller, 'breath_engine') else self.phase_sync_bridge.explorer_breath
                    # MirrorOfInsight may be in mirror_systems
                    if hasattr(self.controller, 'mirror_of_insight'):
                        self.phase_sync_bridge.explorer_insight = self.controller.mirror_of_insight
                    # BloomSystem may be in bloom_curvature or similar
                    if hasattr(self.controller, 'bloom_system'):
                        self.phase_sync_bridge.explorer_bloom = self.controller.bloom_system
                print("[UNIFIED] [PASS] ✨ Phase Sync Bridge initialized - COLLAPSE PREDICTION ACTIVE")
                self.logger.log_state('system', {'event': 'phase_sync_bridge_initialized', 'status': 'active'})
            except Exception as e:
                print(f"[UNIFIED] [WARN] Phase Sync Bridge initialization failed: {e}")
                self.phase_sync_bridge = None
        else:
            self.phase_sync_bridge = None
            print("[UNIFIED] [WARN] Phase Sync Bridge not available")
        
        # Initialize visualization with references to Reality Simulator components (AFTER systems are initialized)
        network_ref = getattr(self.reality_sim, 'components', {}).get('network') if self.reality_sim else None
        renderer_ref = getattr(self.reality_sim, 'components', {}).get('renderer') if self.reality_sim else None
        self.visualization = UnifiedVisualization(network_ref=network_ref, renderer_ref=renderer_ref, reality_sim_ref=self.reality_sim) if enable_visualization else None
        if self.visualization:
            self.visualization.initialize()
            self.visualization.show()
        
        # Initialize Web UI integration
        self.web_ui = None
        self._initialize_web_ui()
        
        # Initialize Highlander Protocol (if enabled)
        if self.highlander_config:
            self._initialize_highlander_protocol()
        
        self.logger.log_state('system', {'event': 'initialization_complete'})
        print("[UNIFIED] [PASS] All systems initialized\n")
        
        # Initialize Live Reporter - your informational wealth dashboard
        try:
            from system_report import LiveReporter
            self.live_reporter = LiveReporter(unified_system=self, update_interval=10.0)
            
            # Wire live_report → ConfigTuner for meta-brain analysis
            # This completes the feedback loop: config.json → runtime → live_report → tuning → config.json
            if hasattr(self, 'reality_sim') and self.reality_sim:
                legacy_tuner = getattr(self.reality_sim, 'legacy_config_tuner', None)
                if legacy_tuner is not None:
                    self.live_reporter.add_report_callback(legacy_tuner.ingest_live_report)
                    print("[UNIFIED] [META] 🧠 Live report → ConfigTuner feedback loop connected!")
                else:
                    # ConfigTuner not found on reality_sim - try to initialize it here
                    try:
                        from reality_simulator.config_tuner_legacy import ConfigTuner
                        if hasattr(self.reality_sim, 'config') and self.reality_sim.config:
                            legacy_tuner = ConfigTuner(self.reality_sim.config, enabled=True)
                            self.reality_sim.legacy_config_tuner = legacy_tuner
                            self.live_reporter.add_report_callback(legacy_tuner.ingest_live_report)
                            print("[UNIFIED] [META] 🧠 Live report → ConfigTuner feedback loop connected (late init)!")
                    except Exception as ct_err:
                        print(f"[UNIFIED] [WARN] ConfigTuner late init failed: {ct_err}")
            
            self.live_reporter.start()
            print("[UNIFIED] [REPORT] 📊 Live system reporter started → data/live_report.json")
        except Exception as e:
            print(f"[UNIFIED] [WARN] Live reporter not available: {e}")
            self.live_reporter = None
        
        # Initialize Antennae - collective sensing apparatus
        try:
            from reality_simulator.antennae import Antennae
            self.antennae = Antennae(history_size=100)
            self.antennae.sensitivity = 1.0
            self.antennae.signal_cooldown = 10.0  # Don't tune too frequently
            print("[UNIFIED] [ANTENNAE] 🦋 Collective sensing apparatus initialized")
        except Exception as e:
            print(f"[UNIFIED] [WARN] Antennae not available: {e}")
            self.antennae = None
        
        # Max cycles (0 means run indefinitely)
        self.max_cycles = int(max_cycles or 0)
    
    def _initialize_web_ui(self):
        """Initialize web UI integration with access to organism networks"""
        try:
            print("[UNIFIED] [WEB] Initializing web UI integration...")
            
            # Import web UI app directly
            import causation_web_ui
            from reality_simulator.language_system import LanguageVocabulary
            
            # Get the Flask app from the module
            self.web_ui = causation_web_ui.app

            # Share unified system with web UI for capsule management
            self.web_ui.unified_system = self

            # CRITICAL: Share CausationExplorer instance with web UI
            # This ensures events from unified_entry.py appear in the web UI
            if self.causation_explorer:
                self.web_ui.config['explorer'] = self.causation_explorer
                # Also update the web UI's explorer variable directly
                causation_web_ui.explorer = self.causation_explorer
                print("[UNIFIED] [WEB] Shared CausationExplorer instance with web UI")
            
            # Store references for butterfly chat access
            if self.reality_sim:
                # Get organism networks from the symbiotic network
                network = self.reality_sim.components.get('network')
                if network:
                    organism_networks = list(network.organisms.values()) if hasattr(network, 'organisms') else []
                    self.web_ui.config['organisms'] = organism_networks
                    # Store network reference for language data access
                    self.web_ui.config['network'] = network
                else:
                    self.web_ui.config['organisms'] = []
                    self.web_ui.config['network'] = None
                
                # Get vocabulary from context_memory (if available)
                vocabulary = None
                if network and hasattr(network, 'context_memory'):
                    context_memory = network.context_memory
                    # Use existing vocabulary if it exists and has words
                    if hasattr(context_memory, 'vocabulary') and context_memory.vocabulary:
                        # Check if vocabulary has words beyond special tokens
                        special_token_count = len(context_memory.vocabulary.word_to_id) - len([k for k in context_memory.vocabulary.word_to_id.keys() if k.startswith('<') and k.endswith('>')])
                        if context_memory.vocabulary.vocab_size > 5:  # More than just special tokens
                            vocabulary = context_memory.vocabulary
                            print(f"[UNIFIED] [WEB] Using vocabulary from context_memory ({vocabulary.vocab_size} words)")
                        else:
                            # Vocabulary has only special tokens - this is CORRECT initial state!
                            # Vocab grows ORGANICALLY through organism behavior, NOT bulk-loaded
                            vocabulary = context_memory.vocabulary
                            print(f"[UNIFIED] [WEB] Using vocabulary with {vocabulary.vocab_size} words (will grow through organism behavior)")
                            
                            # Only build from existing language_anchors if organisms have already learned
                            if context_memory.language_anchors:
                                words_added = vocabulary.build_from_language_anchors(
                                    language_anchors=dict(context_memory.language_anchors),
                                    node_word_associations={k: v for k, v in context_memory.node_word_associations.items()}
                                )
                                print(f"[UNIFIED] [WEB] Built vocabulary from language_anchors ({words_added} words added)")
                    else:
                        # Create new vocabulary and build from anchors
                        # Get max_vocab_size from config
                        max_vocab = self.config.get('neural', {}).get('language_model', {}).get('vocabulary', {}).get('max_size')
                        if not max_vocab:
                            max_vocab = self.config.get('neural', {}).get('brain', {}).get('vocab_size', 10000)
                        vocabulary = LanguageVocabulary(max_vocab_size=max_vocab)
                        if context_memory.language_anchors:
                            words_added = vocabulary.build_from_language_anchors(
                                language_anchors=dict(context_memory.language_anchors),
                                node_word_associations={k: v for k, v in context_memory.node_word_associations.items()}
                            )
                            print(f"[UNIFIED] [WEB] Created vocabulary from language_anchors ({words_added} words added, max={max_vocab})")
                
                # Fallback: Create empty vocabulary if no context_memory
                if vocabulary is None:
                    # Get max_vocab_size from config
                    max_vocab = self.config.get('neural', {}).get('language_model', {}).get('vocabulary', {}).get('max_size')
                    if not max_vocab:
                        max_vocab = self.config.get('neural', {}).get('brain', {}).get('vocab_size', 10000)
                    vocabulary = LanguageVocabulary(max_vocab_size=max_vocab)
                    seed_words = [
                        'hello', 'hi', 'yes', 'no', 'thrive', 'struggle',
                        'connect', 'move', 'rest', 'grow', 'alone', 'together',
                        'help', 'share', 'compete', 'cooperate', 'survive', 'live',
                        'good', 'bad', 'more', 'less', 'fast', 'slow', 'strong', 'weak'
                    ]
                    for word in seed_words:
                        vocabulary.add_word(word)
                    print(f"[UNIFIED] [WEB] Created vocabulary with {len(seed_words)} seed words (will expand as organisms learn)")
                
                self.web_ui.config['vocabulary'] = vocabulary
                
                # Store event emitter for causation events
                if self.causation_explorer:
                    def event_emitter(event_data):
                        from causation_explorer import Event
                        if isinstance(event_data, dict):
                            event = Event(
                                timestamp=event_data.get('timestamp', time.time()),
                                component=event_data.get('component', 'butterfly_chat'),
                                event_type=event_data.get('event_type', 'butterfly_chat_message'),
                                data=event_data.get('data', {})
                            )
                            self.causation_explorer.add_event(event, is_historical=False)
                    
                    self.web_ui.config['event_emitter'] = event_emitter
                else:
                    self.web_ui.config['event_emitter'] = None
            
            # Start web UI in background thread (same process for app.config sharing)
            # CRITICAL: Running in same process allows Butterfly Chat to access live organisms
            import threading
            self._web_ui_proc = None
            
            # Run Flask in background thread with error logging
            def run_web_ui():
                try:
                    # Enable Flask/Werkzeug logging to console
                    import logging
                    log = logging.getLogger('werkzeug')
                    log.setLevel(logging.INFO)
                    handler = logging.StreamHandler()
                    handler.setFormatter(logging.Formatter('[WEB] %(message)s'))
                    log.addHandler(handler)
                    
                    self.web_ui.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
                except Exception as e:
                    print(f"[UNIFIED] [WEB] ❌ Web UI thread crashed: {e}")
                    import traceback
                    traceback.print_exc()
            
            web_thread = threading.Thread(
                target=run_web_ui,
                daemon=True
            )
            web_thread.start()
            print("[UNIFIED] [WEB] ✅ Web UI started in background thread (same process for live organism access)")
            
            print("[UNIFIED] [WEB] 🌐 Web interface available at http://localhost:5000")

            # If we're in Colab, localhost isn't directly reachable.
            # Colab provides a built-in port proxy that yields a clickable public-ish URL.
            colab_url = _try_get_colab_proxy_url(5000)
            if colab_url:
                print(f"[UNIFIED] [WEB] 🌐 Colab proxied URL: {colab_url}")
                print("[UNIFIED] [WEB] (Colab) Open that URL to view the dashboard.")
                # If a URL file is configured, persist the proxy URL so it isn't lost in fast logs.
                _write_tunnel_url(colab_url)
                out_path = os.environ.get('UNIFIED_TUNNEL_URL_FILE', '').strip()
                if out_path:
                    print(f"[UNIFIED] [WEB] (Colab) Saved URL to: {out_path}")

            # Optional: start a localhost.run reverse tunnel (opt-in via env var).
            # Example:
            #   UNIFIED_TUNNEL=localhostrun
            #   UNIFIED_TUNNEL_REMOTE_PORT=80
            #   UNIFIED_TUNNEL_URL_FILE=tunnel_url.txt
            # Note: localhost.run URLs can rotate/expire; this supervisor auto-reconnects and reprints.
            try:
                remote_port = int(os.environ.get('UNIFIED_TUNNEL_REMOTE_PORT', '80'))
            except Exception:
                remote_port = 80

            def _supervise_localhostrun():
                # Run on any platform including Colab (Colab proxy doesn't work from subprocess).
                last_url = None
                while os.environ.get('UNIFIED_TUNNEL', '').strip().lower() == 'localhostrun':
                    proc = _maybe_start_localhostrun_tunnel(local_port=5000, remote_port=remote_port)
                    if not proc:
                        time.sleep(5)
                        continue

                    # Tail output until process exits; extract and surface URL.
                    try:
                        if proc.stdout:
                            for raw in proc.stdout:
                                line = (raw or '').strip()
                                if not line:
                                    continue
                                url = _extract_first_url(line)
                                if url and url != last_url:
                                    last_url = url
                                    print(f"[UNIFIED] [WEB] [TUNNEL] ✅ Public URL: {url}")
                                    _write_tunnel_url(url)
                                else:
                                    # Keep some logs for debugging, but don’t spam.
                                    if os.environ.get('UNIFIED_TUNNEL_VERBOSE', '').strip() == '1':
                                        print(f"[UNIFIED] [WEB] [TUNNEL] {line}")
                    except Exception as e:
                        print(f"[UNIFIED] [WEB] [TUNNEL] Tunnel log reader error: {e}")

                    # If we got here, ssh exited or stdout ended. Restart after short backoff.
                    time.sleep(2)


            def _supervise_cloudflared():
                # Run on any platform including Colab (Colab proxy doesn't work from subprocess).
                last_url = None
                while os.environ.get('UNIFIED_TUNNEL', '').strip().lower() == 'cloudflared':
                    proc = _maybe_start_cloudflared_tunnel(local_port=5000)
                    if not proc:
                        time.sleep(5)
                        continue
                    try:
                        if proc.stdout:
                            for raw in proc.stdout:
                                line = (raw or '').strip()
                                if not line:
                                    continue
                                url = _extract_first_url(line)
                                if url and url != last_url:
                                    last_url = url
                                    print(f"[UNIFIED] [WEB] [TUNNEL] ✅ Public URL: {url}")
                                    _write_tunnel_url(url)
                                else:
                                    if os.environ.get('UNIFIED_TUNNEL_VERBOSE', '').strip() == '1':
                                        print(f"[UNIFIED] [WEB] [TUNNEL] {line}")
                    except Exception as e:
                        print(f"[UNIFIED] [WEB] [TUNNEL] Tunnel log reader error: {e}")
                    time.sleep(2)

            tunnel_mode = os.environ.get('UNIFIED_TUNNEL', '').strip().lower()
            if tunnel_mode == 'auto':
                chosen = _select_auto_tunnel_mode()
                if chosen == 'none':
                    print("[UNIFIED] [WEB] [TUNNEL] UNIFIED_TUNNEL=auto but no tunnel backend found (install cloudflared or ensure ssh exists)")
                else:
                    os.environ['UNIFIED_TUNNEL'] = chosen
                    tunnel_mode = chosen
                    print(f"[UNIFIED] [WEB] [TUNNEL] Auto-selected tunnel backend: {chosen}")

            if tunnel_mode == 'localhostrun':
                threading.Thread(target=_supervise_localhostrun, daemon=True).start()
            elif tunnel_mode == 'cloudflared':
                threading.Thread(target=_supervise_cloudflared, daemon=True).start()
            
            # Auto-launch browser in a separate thread to avoid GIL issues
            def launch_browser():
                # Skip browser auto-launch in Colab (no local browser to open).
                if _is_colab_runtime():
                    return
                import requests
                # Wait for server to be ready
                for _ in range(20):
                    try:
                        r = requests.get('http://127.0.0.1:5000/health', timeout=1)
                        if r.status_code == 200:
                            break
                    except Exception:
                        pass
                    time.sleep(0.25)
                try:
                    webbrowser.open('http://localhost:5000')
                    print("[UNIFIED] [WEB] 🌐 Browser launched automatically")
                except Exception as e:
                    print(f"[UNIFIED] [WEB] Could not auto-launch browser: {e}")
            
            import threading as threading_module
            browser_thread = threading_module.Thread(target=launch_browser, daemon=True)
            browser_thread.start()
            
        except Exception as e:
            print(f"[UNIFIED] [WEB] ❌ Web UI integration failed: {e}")
            import traceback
            traceback.print_exc()
            self.web_ui = None

    def get_current_organisms(self) -> Dict[str, Any]:
        """Get current organisms from the active simulation.

        Returns:
            Dict mapping organism IDs to organism objects
        """
        organisms = {}

        # Get organisms from Reality Simulator's network component
        if self.reality_sim and hasattr(self.reality_sim, 'components'):
            network = self.reality_sim.components.get('network')
            if network and hasattr(network, 'organisms'):
                organisms.update(network.organisms)
        
        # Fallback: Check if reality_sim has organisms directly
        elif self.reality_sim and hasattr(self.reality_sim, 'organisms'):
            organisms.update(self.reality_sim.organisms)

        # If using Highlander protocol, filter to only active organisms
        if hasattr(self, 'highlander_protocol') and self.highlander_protocol:
            # Get organisms from highlander protocol (which has active_organisms)
            if hasattr(self.highlander_protocol, 'active_organisms'):
                active_ids = set(self.highlander_protocol.active_organisms)
                # Filter to only active organisms
                organisms = {oid: org for oid, org in organisms.items() if oid in active_ids}

        return organisms

    def _update_web_ui_organisms(self):
        """Update web UI with current organism networks for Butterfly Chat.
        
        This is called every cycle to ensure Butterfly Chat always has access
        to the latest organism population, even as organisms are created/destroyed.
        """
        if not self.web_ui or not self.reality_sim:
            return
        
        try:
            network = self.reality_sim.components.get('network')
            if network and hasattr(network, 'organisms'):
                organism_networks = list(network.organisms.values())
                # Only update if organisms exist or if we had organisms before
                current_count = len(organism_networks)
                previous_count = len(self.web_ui.config.get('organisms', []))
                
                if current_count > 0 or previous_count > 0:
                    self.web_ui.config['organisms'] = organism_networks
                    # Also update network reference
                    self.web_ui.config['network'] = network
                    
                    # Also update trainer reference for chat-triggered learning
                    if self.reality_sim.neural_trainer:
                        self.web_ui.config['neural_trainer'] = self.reality_sim.neural_trainer
                    
                    # Log significant changes
                    if current_count != previous_count and current_count > 0:
                        if previous_count == 0:
                            print(f"[UNIFIED] [WEB] 🦋 Butterfly Chat now has {current_count} organisms available")
        except Exception:
            pass  # Silent fail - don't break main loop for web UI updates
    
    def _wire_reactive_event_handlers(self):
        """
        INTEGRATION FIX: Wire event handlers to make the system reactive.
        
        This is the key fix for the "events as museum" problem. Events are no longer
        just logged - they trigger actual responses that affect system behavior.
        
        The flow becomes:
        1. Neural training completes → emits event
        2. Causation explorer receives event → calls handler
        3. Handler adjusts config tuner parameters
        4. Config tuner syncs to components (trainer, evolution)
        5. Components use updated parameters
        """
        if not self.causation_explorer or not self.reality_sim:
            return
        
        config_tuner = getattr(self.reality_sim, 'config_tuner', None)
        neural_trainer = getattr(self.reality_sim, 'neural_trainer', None)
        
        # ═══════════════════════════════════════════════════════════════
        # LIGHTWEIGHT EVENT TRACKER - for rate-based decisions
        # Tracks rolling windows without accumulating unbounded memory
        # ═══════════════════════════════════════════════════════════════
        import time
        from collections import deque
        
        class EventTracker:
            """Minimal rolling window tracker for event-based decisions."""
            __slots__ = ['battles', 'low_conf_decisions', 'vocab_adoptions', 'last_action_time']
            
            def __init__(self):
                # Rolling windows: (timestamp, data) tuples, max 100 entries each
                self.battles = deque(maxlen=100)
                self.low_conf_decisions = deque(maxlen=50)
                self.vocab_adoptions = deque(maxlen=50)
                self.last_action_time = {}  # cooldowns per action type
            
            def count_recent(self, window: deque, seconds: float = 60.0) -> int:
                """Count events in last N seconds."""
                cutoff = time.time() - seconds
                return sum(1 for ts, _ in window if ts > cutoff)
            
            def can_act(self, action_type: str, cooldown: float = 30.0) -> bool:
                """Check if enough time passed since last action of this type."""
                last = self.last_action_time.get(action_type, 0)
                if time.time() - last > cooldown:
                    self.last_action_time[action_type] = time.time()
                    return True
                return False
        
        tracker = EventTracker()
        
        # Handler: Adjust learning rate when training loss is high
        def on_training_complete(event):
            """React to neural training completion events."""
            if not config_tuner:
                return
            
            try:
                avg_loss = event.data.get('avg_loss', 0.0)
                step = event.data.get('training_step', 0)
                
                # Only react every 100 steps to avoid thrashing
                if step % 100 != 0:
                    return
                
                # If loss is too high (>2.0), reduce learning rate
                if avg_loss > 2.0:
                    current_lr = config_tuner.get('learning_rate')
                    if current_lr and current_lr > 1e-5:
                        new_lr = current_lr * 0.9
                        config_tuner.set('learning_rate', new_lr, 
                                        reason=f'loss_high_{avg_loss:.3f}')
                
                # If loss is very low and stable, slightly increase for faster learning
                elif avg_loss < 0.1 and step > 500:
                    current_lr = config_tuner.get('learning_rate')
                    if current_lr and current_lr < 0.01:
                        new_lr = current_lr * 1.05
                        config_tuner.set('learning_rate', new_lr,
                                        reason=f'loss_stable_{avg_loss:.3f}')
            except Exception as e:
                pass  # Don't break on handler errors
        
        # Handler: Adjust mutation rate based on ML clustering diversity
        def on_ml_analysis_complete(event):
            """React to ML analysis events - adjust evolution parameters."""
            if not config_tuner:
                return
            
            try:
                # ml_autotune_metrics event uses 'cluster_count', not 'n_clusters'
                cluster_count = event.data.get('cluster_count', event.data.get('n_clusters', 0))
                anomaly_ratio = event.data.get('anomaly_ratio', 0.0)
                
                # If too many anomalies (>30%), increase mutation to explore more
                if anomaly_ratio > 0.3:
                    current_rate = config_tuner.get('mutation_rate')
                    if current_rate and current_rate < 0.1:
                        config_tuner.set('mutation_rate', current_rate * 1.1,
                                        reason=f'high_anomaly_{anomaly_ratio:.2f}')
                
                # If clusters are too few (<3), system is converging - increase exploration
                elif cluster_count < 3 and cluster_count > 0:
                    current_rate = config_tuner.get('mutation_rate')
                    if current_rate:
                        config_tuner.set('mutation_rate', current_rate * 1.2,
                                        reason=f'low_diversity_{cluster_count}_clusters')
            except Exception:
                pass
        
        # Handler: Record config outcomes based on phase transitions
        def on_phase_transition(event):
            """Track config success/failure based on phase changes."""
            if not config_tuner:
                return
            
            try:
                # Handle both 'to_phase' (from causation_explorer) and 'new_phase' (from other sources)
                new_phase = event.data.get('to_phase', event.data.get('new_phase', ''))
                success = 'emergence' in new_phase or 'convergence' in new_phase
                config_tuner.record_outcome(
                    success=success,
                    context=f"phase_transition_to_{new_phase}"
                )
            except Exception:
                pass
        
        # Handler: React to config atom updates (close the feedback loop)
        def on_config_atom_update(event):
            """Log and potentially react to config parameter changes."""
            try:
                param_name = event.data.get('param_name', 'unknown')
                old_val = event.data.get('old_value')
                new_val = event.data.get('new_value')
                reason = event.data.get('reason', '')
                
                # Log significant changes for observability
                logger.debug(f"[CONFIG] Atom updated: {param_name} {old_val} → {new_val} ({reason})")
                
                # If learning_rate changed, invalidate cached optimizers in trainer
                if param_name == 'learning_rate' and self.reality_sim:
                    trainer = getattr(self.reality_sim, 'neural_trainer', None)
                    if trainer and hasattr(trainer, 'optimizers'):
                        trainer.optimizers.clear()
                        trainer.schedulers.clear()
            except Exception:
                pass
        
        # Handler: React to config outcomes (track what works)
        def on_config_outcome(event):
            """Track config success/failure for meta-learning."""
            try:
                success = event.data.get('success', False)
                context = event.data.get('context', '')
                domain = event.data.get('domain', 'all')
                
                # Log for observability - this closes the loop visibility
                status = "✓" if success else "✗"
                logger.debug(f"[CONFIG] Outcome {status}: {domain} ({context})")
            except Exception:
                pass
        
        # Handler: React to battle results (feed back to evolution)
        def on_battle_resolved(event):
            """React to battle outcomes - adjust selection pressure if needed."""
            if not config_tuner:
                return
            try:
                winner_id = event.data.get('winner', event.data.get('winner_id'))
                loser_id = event.data.get('loser', event.data.get('loser_id'))
                battle_type = event.data.get('battle_type', 'unknown')
                
                # Track battle in rolling window
                tracker.battles.append((time.time(), battle_type))
                
                # Check battle rate (battles per minute)
                battles_per_min = tracker.count_recent(tracker.battles, 60.0)
                
                # REACTIVE: If too many battles (>20/min), reduce selection pressure
                if battles_per_min > 20 and tracker.can_act('reduce_selection', cooldown=60.0):
                    current = config_tuner.get('selection_pressure')
                    if current and current > 0.3:
                        new_val = max(0.3, current * 0.85)
                        config_tuner.set('selection_pressure', new_val,
                                        reason=f'high_battle_rate_{battles_per_min}/min')
                        logger.info(f"[BATTLE] High battle rate ({battles_per_min}/min) → selection_pressure {current:.2f}→{new_val:.2f}")
                
                # REACTIVE: If too few battles (<3/min), increase selection pressure
                elif battles_per_min < 3 and tracker.can_act('increase_selection', cooldown=60.0):
                    current = config_tuner.get('selection_pressure')
                    if current and current < 0.9:
                        new_val = min(0.9, current * 1.15)
                        config_tuner.set('selection_pressure', new_val,
                                        reason=f'low_battle_rate_{battles_per_min}/min')
                        logger.info(f"[BATTLE] Low battle rate ({battles_per_min}/min) → selection_pressure {current:.2f}→{new_val:.2f}")
                
            except Exception:
                pass
        
        # Handler: React to alliance decisions
        def on_alliance_decision(event):
            """React to alliance patterns - adjust cooperation incentives."""
            if not config_tuner:
                return
            try:
                decision_type = event.data.get('decision_type', '')
                decision = event.data.get('decision', '')
                confidence = event.data.get('confidence', 0.0)
                
                # REACTIVE: If organisms consistently reject alliances (low cooperation)
                # boost cooperation_bonus to incentivize teamwork
                if decision in ['reject', 'defect', 'refuse']:
                    if tracker.can_act('boost_cooperation', cooldown=120.0):
                        current = config_tuner.get('cooperation_bonus')
                        if current is not None and current < 2.0:
                            new_val = min(2.0, current * 1.2)
                            config_tuner.set('cooperation_bonus', new_val,
                                            reason='low_alliance_acceptance')
                            logger.info(f"[ALLIANCE] Low cooperation → cooperation_bonus {current:.2f}→{new_val:.2f}")
                
                # REACTIVE: If alliances form easily, can reduce bonus
                elif decision in ['accept', 'cooperate', 'form'] and confidence > 0.7:
                    if tracker.can_act('reduce_cooperation', cooldown=120.0):
                        current = config_tuner.get('cooperation_bonus')
                        if current is not None and current > 0.5:
                            new_val = max(0.5, current * 0.95)
                            config_tuner.set('cooperation_bonus', new_val,
                                            reason='healthy_alliance_rate')
                
            except Exception:
                pass
        
        # Handler: React to neural decisions (track decision quality)
        def on_neural_decision(event):
            """React to decision confidence patterns - adjust exploration/exploitation."""
            if not config_tuner or not neural_trainer:
                return
            try:
                action = event.data.get('action', '')
                confidence = event.data.get('confidence', 0.0)
                organism_id = event.data.get('organism_id', '')
                
                # Track low-confidence decisions
                if confidence < 0.3:
                    tracker.low_conf_decisions.append((time.time(), confidence))
                
                # Check rate of low-confidence decisions
                low_conf_rate = tracker.count_recent(tracker.low_conf_decisions, 60.0)
                
                # REACTIVE: Many low-confidence decisions (>15/min) = organisms uncertain
                # Increase epsilon for more exploration, they need to learn more
                if low_conf_rate > 15 and tracker.can_act('increase_epsilon', cooldown=90.0):
                    # Boost epsilon on all organisms slightly
                    network = self.reality_sim.components.get('network')
                    if network:
                        boosted = 0
                        for org in network.organisms.values():
                            if hasattr(org, 'epsilon') and org.epsilon is not None:
                                org.epsilon = min(0.5, org.epsilon + 0.05)
                                boosted += 1
                        if boosted > 0:
                            logger.info(f"[NEURAL] High uncertainty ({low_conf_rate} low-conf/min) → epsilon boosted on {boosted} organisms")
                
                # REACTIVE: Very few low-confidence decisions = organisms confident
                # Can slightly decay epsilon for more exploitation
                elif low_conf_rate < 3 and tracker.can_act('decay_epsilon', cooldown=90.0):
                    network = self.reality_sim.components.get('network')
                    if network:
                        decayed = 0
                        for org in network.organisms.values():
                            if hasattr(org, 'epsilon') and org.epsilon is not None and org.epsilon > 0.05:
                                org.epsilon = max(0.05, org.epsilon * 0.95)
                                decayed += 1
                        # Silent - this is normal healthy behavior
                
            except Exception:
                pass
        
        # Handler: React to vocabulary growth
        def on_vocabulary_growth(event):
            """React to language evolution - reward linguistic organisms."""
            try:
                new_word = event.data.get('word', '')
                
                # Handle vocabulary_growth events
                if event.event_type == 'vocabulary_growth':
                    vocab_size = event.data.get('vocab_size', 0)
                    
                    # REACTIVE: Milestone rewards - boost language fitness weight at thresholds
                    if vocab_size in [25, 50, 100, 200] and config_tuner:
                        if tracker.can_act(f'vocab_milestone_{vocab_size}', cooldown=300.0):
                            current = config_tuner.get('language_fitness_weight')
                            if current is not None:
                                # Boost language importance as vocab grows
                                new_val = min(0.4, current + 0.02)
                                config_tuner.set('language_fitness_weight', new_val,
                                                reason=f'vocab_milestone_{vocab_size}')
                                logger.info(f"[LANGUAGE] Vocabulary milestone {vocab_size} → language_fitness_weight {current:.2f}→{new_val:.2f}")
                
                # Handle word_assignment events (word spreading through population)
                elif event.event_type == 'word_assignment':
                    num_orgs = event.data.get('total_organisms_with_word', 0)
                    tracker.vocab_adoptions.append((time.time(), num_orgs))
                    
                    # REACTIVE: If a word spreads to 10+ organisms, it's "viral"
                    # This is emergent communication - record as positive outcome
                    if num_orgs >= 10 and config_tuner:
                        if tracker.can_act(f'viral_word_{new_word[:10]}', cooldown=60.0):
                            config_tuner.record_outcome(success=True, context=f'viral_word_{new_word}')
                            logger.info(f"[LANGUAGE] Viral word '{new_word}' adopted by {num_orgs} organisms")
                
            except Exception:
                pass
        
        # Handler: React to early stopping
        def on_early_stopping(event):
            """React when training stops early."""
            try:
                best_loss = event.data.get('best_loss', 0)
                patience_exhausted = event.data.get('patience_exhausted', 0)
                
                logger.info(f"[NEURAL] Early stopping triggered: best_loss={best_loss:.4f}, patience={patience_exhausted}")
                
                # Record as successful outcome - training converged
                if config_tuner:
                    config_tuner.record_outcome(success=True, context="early_stopping_convergence")
            except Exception:
                pass
        
        # Handler: React to learning rate adjustments
        def on_lr_adjusted(event):
            """React to LR changes - track scheduler effectiveness."""
            try:
                old_lr = event.data.get('old_lr', 0)
                new_lr = event.data.get('new_lr', 0)
                reason = event.data.get('reason', event.data.get('scheduler_type', ''))
                
                # REACTIVE: If LR dropped significantly (>50% reduction), record outcome
                # This helps the config tuner learn which LR schedules work
                if config_tuner and old_lr > 0 and new_lr > 0:
                    reduction_ratio = new_lr / old_lr
                    
                    # Large reduction = scheduler detected plateau, record for learning
                    if reduction_ratio < 0.5:
                        config_tuner.record_outcome(
                            success=False,  # Plateau = current config wasn't optimal
                            context=f'lr_plateau_reduction_{reduction_ratio:.2f}'
                        )
                        logger.debug(f"[NEURAL] LR plateau: {old_lr:.6f}→{new_lr:.6f} ({reason})")
                    
                    # Small reduction = healthy decay, record as neutral/positive
                    elif reduction_ratio > 0.8:
                        # Normal scheduled decay - don't record, this is expected
                        pass
                
            except Exception:
                pass
        
        # Subscribe handlers to ACTUAL event types that are emitted
        # (Audit found mismatches - these are the real event_type values)
        self.causation_explorer.subscribe('neural_training', on_training_complete)  # trainer.py:1276
        self.causation_explorer.subscribe('neural_autotune_metrics', on_training_complete)  # trainer.py:1414
        self.causation_explorer.subscribe('ml_autotune_metrics', on_ml_analysis_complete)  # ml_utils.py:1146
        self.causation_explorer.subscribe('phase_transition', on_phase_transition)
        self.causation_explorer.subscribe('explorer_phase_change', on_phase_transition)
        self.causation_explorer.subscribe('config_atom_update', on_config_atom_update)  # atomic_config.py:328
        self.causation_explorer.subscribe('config_outcome', on_config_outcome)  # atomic_config.py:850
        self.causation_explorer.subscribe('battle_resolved', on_battle_resolved)  # battle_arena.py:787
        self.causation_explorer.subscribe('absorption_complete', on_battle_resolved)  # battle_arena.py:917 (reuse handler)
        self.causation_explorer.subscribe('alliance_decision', on_alliance_decision)  # neural_organism.py:2260
        self.causation_explorer.subscribe('neural_decision', on_neural_decision)  # neural_organism.py:802
        self.causation_explorer.subscribe('vocabulary_growth', on_vocabulary_growth)  # language_system.py:184
        self.causation_explorer.subscribe('word_assignment', on_vocabulary_growth)  # context_memory.py:401
        self.causation_explorer.subscribe('early_stopping_triggered', on_early_stopping)  # trainer.py:366
        self.causation_explorer.subscribe('lr_adjusted', on_lr_adjusted)  # trainer.py:1221
        
        print("[UNIFIED] [INTEGRATION] ✅ Reactive event handlers wired (14 event types)")
        print("[UNIFIED] [INTEGRATION]    - Training/LR → Config tuner (adjust LR on loss)")
        print("[UNIFIED] [INTEGRATION]    - ML Analysis → Evolution (adjust mutation on diversity)")
        print("[UNIFIED] [INTEGRATION]    - Battles → Selection pressure (rate-based tuning)")
        print("[UNIFIED] [INTEGRATION]    - Alliances → Cooperation bonus (acceptance-based)")
        print("[UNIFIED] [INTEGRATION]    - Neural decisions → Epsilon (confidence-based)")
        print("[UNIFIED] [INTEGRATION]    - Language → Fitness weight (milestone rewards)")
        print("[UNIFIED] [INTEGRATION]    - Config updates → Immediate effect")
        
        # Wire WIKAI Observer - passive listener for pattern capture
        self._wire_wikai_observer()
    
    def _wire_wikai_observer(self):
        """
        Wire WIKAI Observer to auto-capture butterflies when they converge.
        
        The Observer watches silently. When a butterfly discovers something true
        (stability_score > 0.85, fitness_delta > 0.15), the pattern is captured
        and added to the Commons for all future AI systems to learn from.

        "The butterflies don't know they're being studied. They just fly.
         And WIKAI quietly records every time they discover something true."
        """
        print("[UNIFIED] [WIKAI] 📚 Attempting to wire WIKAI Observer...")
        
        if not self.causation_explorer:
            print("[UNIFIED] [WIKAI] ⚠️ No causation_explorer - skipping WIKAI")
            return
        
        try:
            from wikai.observer import create_observer_for_convergence
            
            self.wikai_observer = create_observer_for_convergence(
                causation_explorer=self.causation_explorer,
                fitness_delta_threshold=0.15,  # Minimum improvement to capture
                stability_threshold=0.85,       # Must be stable
                cycle_threshold=20              # Must have run for a while
            )
            
            print("[UNIFIED] [WIKAI] ✅ WIKAI Observer wired to event stream")
            print("[UNIFIED] [WIKAI]    - Watching for convergent butterflies")
            print("[UNIFIED] [WIKAI]    - Auto-capture: stability>0.85 AND fitness_delta>0.15")
            print("[UNIFIED] [WIKAI]    - Patterns saved to wikai/patterns/")
            
        except ImportError as e:
            print(f"[UNIFIED] [WIKAI] ⚠️ WIKAI import failed: {e}")
            self.wikai_observer = None
        except Exception as e:
            print(f"[UNIFIED] [WIKAI] ❌ WIKAI Observer error: {e}")
            import traceback
            traceback.print_exc()
            self.wikai_observer = None
        except Exception as e:
            print(f"[UNIFIED] [WIKAI] ❌ WIKAI Observer failed to initialize: {e}")
            self.wikai_observer = None
    
    def _initialize_highlander_protocol(self):
        """Initialize the Highlander Protocol tournament system.
        
        There can be only one. Organisms compete for survival,
        absorbing the traits, knowledge, and very essence of the fallen.
        The last butterfly standing becomes the template for immortality.
        """
        try:
            print("\n[UNIFIED] [HIGHLANDER] ⚔️ Initializing Highlander Protocol...")
            print("[UNIFIED] [HIGHLANDER] 'There can be only one.'")
            
            # Import Highlander systems
            from reality_simulator.evolution.highlander_protocol import HighlanderProtocol
            from reality_simulator.evolution.battle_arena import BattleArena
            from reality_simulator.checkpointing.organism_capsule import OrganismCapsuleManager
            from reality_simulator.evolution.germination_pool import GerminationPool, integrate_germination_with_highlander
            from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem, integrate_alliance_warfare_with_highlander
            
            # Parse config
            config = self.highlander_config or {}
            population_size = config.get('population_size', 9)  # Default matches config.json
            survival_threshold = config.get('survival_threshold', 0.4)  # Default matches config.json
            competition_intensity = config.get('competition_intensity', 0.2)  # Default matches config.json
            rounds_per_cycle = config.get('rounds_per_cycle', 1)
            
            # Create event emitter for Highlander events
            def highlander_event_emitter(event_data):
                """Emit Highlander events to causation explorer"""
                if self.causation_explorer:
                    try:
                        from causation_explorer import Event
                        # Handle both Event objects and dicts
                        if isinstance(event_data, Event):
                            # Already an Event object, add directly
                            self.causation_explorer.add_event(event_data, is_historical=False)
                            print(f"[HIGHLANDER] ⚔️ Event emitted: {event_data.event_type} (total: {len(self.causation_explorer.events)})")
                        else:
                            # Dict format - create Event
                            event = Event(
                                timestamp=event_data.get('timestamp', time.time()),
                                component=event_data.get('component', 'highlander'),
                                event_type=event_data.get('event_type', 'highlander_event'),
                                data=event_data.get('data', {})
                            )
                            self.causation_explorer.add_event(event, is_historical=False)
                            print(f"[HIGHLANDER] ⚔️ Event emitted: {event.event_type} (total: {len(self.causation_explorer.events)})")
                    except Exception as e:
                        print(f"[HIGHLANDER] ❌ Event emission failed: {e}")
            
            # Initialize Battle Arena (combat resolution)
            arena_config = {
                'max_rounds': config.get('max_battle_rounds', 50),  # Default matches config.json
                'chaos_factor': config.get('chaos_factor', 0.0)  # Default matches config.json (disabled)
            }
            self.battle_arena = BattleArena(
                config=arena_config,
                event_emitter=highlander_event_emitter
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] Battle Arena initialized")
            
            # Initialize Organism Capsule Manager (checkpointing)
            capsule_dir = Path('highlander_capsules')
            self.capsule_manager = OrganismCapsuleManager(
                storage_dir=capsule_dir
            )
            print(f"[UNIFIED] [HIGHLANDER] [PASS] Capsule Manager initialized (dir: {capsule_dir})")
            
            # Get network reference for context_memory and organism access
            network = None
            if self.reality_sim and hasattr(self.reality_sim, 'components'):
                network = self.reality_sim.components.get('network')
            
            # Initialize Germination Pool (new life from the fallen)
            # Pass context_memory for vocabulary extraction from dying organisms
            # Pass config for grounded mode checking during vocabulary inheritance
            network_context_memory = network.context_memory if network and hasattr(network, 'context_memory') else None
            self.germination_pool = GerminationPool(
                causation_explorer=self.causation_explorer,
                max_genetic_samples=config.get('max_genetic_samples', 100),
                min_population=config.get('min_population', 5),  # Default matches config.json
                max_population=config.get('max_population', 100),  # Default matches config.json
                germination_rate=config.get('germination_rate', 0.1),
                mutation_base_rate=config.get('mutation_rate', 0.0),  # Default matches config.json
                context_memory=network_context_memory,  # For full vocabulary inheritance
                config=self.active_config  # For grounded mode checking
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🌱 Germination Pool initialized")
            
            # Get arena config for battle type selection
            arena_settings = self.active_config.get('arena', {})
            
            # Initialize Highlander Protocol (tournament orchestration)
            # IMPORTANT: Include 'neural' section for LanguageGameBridge config (meta-tunable)
            highlander_config = {
                'survival_threshold': survival_threshold,
                'competition_intensity': competition_intensity,
                'predation_enabled': config.get('predation_enabled', False),
                'germination_rate': config.get('germination_rate', 0.1),
                'max_population': config.get('max_population', 100),
                'min_population': config.get('min_population', 5),  # Default matches config.json
                'battle_randomness': config.get('chaos_factor', 0.0),  # Default matches config.json (disabled)
                # Include arena battle type and probability settings
                'default_battle_type': arena_settings.get('default_battle_type', 'FULL_COMBAT'),
                'proton_game_probability': arena_settings.get('proton_game_probability', 1.0),  # Default matches config.json
                'prefer_native_games': arena_settings.get('prefer_native_games', True),
                # Include neural config for LanguageGameBridge parameters (bias_strength, learning_rate)
                # This allows ConfigTuner to propagate tuning changes to the bridge
                'neural': self.active_config.get('neural', {})
            }
            
            # Log battle type selection
            battle_type = highlander_config['default_battle_type']
            proton_prob = highlander_config['proton_game_probability']
            print(f"[UNIFIED] [HIGHLANDER] ⚔️ Battle type: {battle_type}")
            print(f"[UNIFIED] [HIGHLANDER] 🎮 Proton Game probability: {proton_prob:.0%}")
            if battle_type == 'PROTON_GAME' or proton_prob > 0:
                print("[UNIFIED] [HIGHLANDER] 🎮 Proton Game Arena battles enabled!")
                if highlander_config['prefer_native_games']:
                    print("[UNIFIED] [HIGHLANDER]    (Prioritizing language/concept games - no Gym dependency)")
            
            self.highlander_protocol = HighlanderProtocol(
                config=highlander_config,
                event_emitter=highlander_event_emitter,
                capsule_manager=self.capsule_manager,
                battle_arena=self.battle_arena
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] Tournament Protocol initialized")
            
            # WIRE INTO REALITY_SIM.COMPONENTS for system_report.py discovery
            # This enables live_report.json to find the language_game_bridge
            if self.reality_sim and hasattr(self.reality_sim, 'components'):
                self.reality_sim.components['highlander'] = self.highlander_protocol
                print("[UNIFIED] [HIGHLANDER] [PASS] Registered into reality_sim.components['highlander']")
            
            # Register existing organisms
            network = self.reality_sim.components.get('network') if self.reality_sim else None
            if network and hasattr(network, 'organisms'):
                for org_id, organism in network.organisms.items():
                    try:
                        # Get fitness from organism
                        fitness = 0.5  # Default
                        if hasattr(organism, 'fitness'):
                            fitness = organism.fitness
                        elif hasattr(organism, 'get_fitness'):
                            fitness = organism.get_fitness()
                        
                        self.highlander_protocol.register_organism(org_id, initial_fitness=fitness)
                        print(f"[UNIFIED] [HIGHLANDER] Registered organism: {org_id}")
                    except Exception as e:
                        print(f"[UNIFIED] [HIGHLANDER] Failed to register {org_id}: {e}")
            
            # Wire Germination Pool to Highlander Protocol
            # This creates organism_factory callback for spawning new warriors
            def organism_factory(organism_id, initial_traits=None, initial_config=None):
                """Factory function to create new organisms for the tournament"""
                if network and hasattr(network, 'create_organism'):
                    org = network.create_organism(
                        organism_id=organism_id,
                        traits=initial_traits,
                        config=initial_config
                    )
                    # Wire Illumination Engine references
                    if org and hasattr(org, 'set_system_references'):
                        aws = getattr(self, 'alliance_warfare', None)
                        causation_explorer = getattr(self, 'causation_explorer', None)
                        org.set_system_references(aws, causation_explorer, None)
                    return org
                return None
                
            self._germination_callback = integrate_germination_with_highlander(
                self.highlander_protocol,
                self.germination_pool,
                organism_factory,
                alliance_warfare=None  # Will be set after alliance_warfare is created
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🔗 Germination Pool wired to tournament")
            
            # ⚔️🪐 INITIALIZE ALLIANCE WARFARE SYSTEM
            # Beyond individual battles - collective warfare for existential dominance
            # Read alliance_warfare directly from config (which IS the highlander config)
            aw_config = config.get('alliance_warfare', {})
            alliance_config = {
                'min_alliance_size': aw_config.get('min_alliance_size', 3),
                'max_alliances': aw_config.get('max_alliances', 10),
                'max_alliance_size': aw_config.get('max_alliance_size', 50),
                'max_confederations': aw_config.get('max_confederations', 10),
                'war_frequency': aw_config.get('war_frequency', 0.3),
                'war_chaos_factor': aw_config.get('chaos_factor', 0.15),
                'existential_war_threshold': aw_config.get('existential_war_threshold', 0.8),
                'illumination_stability_threshold': aw_config.get('illumination_stability_threshold', 5)
            }
            print(f"[UNIFIED] [ALLIANCE] Config loaded: max_alliances={alliance_config['max_alliances']}, max_confederations={alliance_config['max_confederations']}")
            self.alliance_warfare = AllianceWarfareSystem(
                highlander_protocol=self.highlander_protocol,
                config=alliance_config,
                event_emitter=highlander_event_emitter
            )
            integrate_alliance_warfare_with_highlander(
                self.highlander_protocol,
                self.alliance_warfare,
                alliance_config
            )
            print("[UNIFIED] [HIGHLANDER] [PASS] 🪐⚔️ Alliance Warfare System initialized")
            print("[UNIFIED] [HIGHLANDER] 'Beyond individual battles - collective warfare for existential dominance'")
            
            # Explicitly wire AWS to Highlander (bidirectional)
            self.highlander_protocol.set_alliance_warfare_system(self.alliance_warfare)
            
            # 🏛️ WIRE GERMINATION WAVE ALLIANCES
            # Now that alliance_warfare exists, tell germination pool about it
            # This enables pre-allied germination waves - the fallen rise TOGETHER!
            if hasattr(self, '_germination_callback') and hasattr(self._germination_callback, 'set_alliance_warfare'):
                self._germination_callback.set_alliance_warfare(self.alliance_warfare)
                print("[UNIFIED] [GERMINATION] 🏛️ Wave Alliances enabled - newcomers will be born allied!")
            
            # 📚 WIRE CONTEXT MEMORY FOR VOCABULARY INHERITANCE
            # This enables resurrected organisms to inherit their full vocabulary
            if hasattr(self, '_germination_callback') and hasattr(self._germination_callback, 'set_context_memory'):
                if network and hasattr(network, 'context_memory'):
                    self._germination_callback.set_context_memory(network.context_memory)
                    print("[UNIFIED] [GERMINATION] 📚 Vocabulary inheritance enabled - the fallen keep their words!")
            
            # 📚 WIRE CONTEXT MEMORY TO HIGHLANDER FOR VOCABULARY TRANSFER ON DEATH
            # CRITICAL: Without this, vocabulary is LOST when organisms die in battle!
            # The winner needs access to loser's word associations.
            if network and hasattr(network, 'context_memory'):
                self.highlander_protocol.set_context_memory(network.context_memory)
                print("[UNIFIED] [HIGHLANDER] 📚 Vocabulary transfer enabled - winners absorb loser's words!")
            
            # ═══════════════════════════════════════════════════════════════════
            # 🧠 LANGUAGE-GAME BRIDGE: Connect vocabulary to battle decisions
            # This is THE MISSING LINK - 62,000+ concepts now influence games!
            # ═══════════════════════════════════════════════════════════════════
            if network and hasattr(network, 'organisms'):
                try:
                    organism_names = list(network.organisms.keys())
                    
                    # Get atomic language and knowledge web if available
                    atomic_language = None
                    knowledge_web = None
                    first_org = next(iter(network.organisms.values()), None)
                    if first_org:
                        atomic_language = getattr(first_org, 'atomic_language', None)
                        knowledge_web = getattr(network, 'knowledge_web', 
                                               getattr(first_org, 'knowledge_web', None))
                    
                    # Wire the language bridge
                    self.highlander_protocol.set_language_bridge(
                        organism_names=organism_names,
                        atomic_language=atomic_language,
                        knowledge_web=knowledge_web
                    )
                    print("[UNIFIED] [HIGHLANDER] 🧠 Language-Game Bridge: VOCABULARY NOW AFFECTS BATTLES!")
                except Exception as e:
                    print(f"[UNIFIED] [HIGHLANDER] ⚠️ Language Bridge wiring failed: {e}")
            
            # 🔌 SYSTEM WIRING: Connect NeuralOrganisms to Illumination Engine
            # This enables organisms to query "Why?" and access the Causation Explorer
            if network and hasattr(network, 'organisms'):
                wired_count = 0
                for org_id, organism in network.organisms.items():
                    if hasattr(organism, 'set_system_references'):
                        organism.set_system_references(self.alliance_warfare, self.causation_explorer, None)
                        wired_count += 1
                if wired_count > 0:
                    print(f"[UNIFIED] [ILLUMINATION] 👁️ Wired {wired_count} organisms to Causation Engine")
            
            # 🏛️ CONFEDERATION (Super-Alliance) logging
            print("[UNIFIED] [HIGHLANDER] [PASS] 🏛️ Confederation System enabled (CONFEDERATION → EMPIRE → HEGEMONY)")
            
            # Store config for runtime access
            self._highlander_rounds_per_cycle = rounds_per_cycle
            self._highlander_enabled = True
            
            # Store reference to network for organism access
            self._highlander_network = network
            
            # 🧠 NEURAL FEEDBACK LOOP: Inject organisms into alliance warfare
            # This allows alliance outcomes to feed back into neural learning
            if network and hasattr(network, 'organisms') and self.alliance_warfare:
                self.alliance_warfare.set_neural_organisms(network.organisms)
                print("[UNIFIED] [HIGHLANDER] 🧠 Neural feedback loop connected (alliance → neural)")
            
            # 🔗 WIRE ConfigTuner to HighlanderProtocol for parameter propagation
            # This enables tuning changes (bias_strength, learning_rate) to reach the bridge
            if hasattr(self.reality_sim, 'legacy_config_tuner') and self.reality_sim.legacy_config_tuner:
                self.reality_sim.legacy_config_tuner.set_highlander_protocol(self.highlander_protocol)
                print("[UNIFIED] [HIGHLANDER] 🔗 ConfigTuner wired to HighlanderProtocol for bridge propagation")
            
            print(f"[UNIFIED] [HIGHLANDER] ✅ Protocol active with {self.highlander_protocol.get_population_count()} organisms")
            print(f"[UNIFIED] [HIGHLANDER] 📊 Config: survival={survival_threshold}, intensity={competition_intensity}")
            self.logger.log_state('system', {
                'event': 'highlander_initialized',
                'population': self.highlander_protocol.get_population_count(),
                'config': config
            })
            
        except ImportError as e:
            print(f"[UNIFIED] [HIGHLANDER] ❌ Import failed: {e}")
            print("[UNIFIED] [HIGHLANDER] Highlander Protocol not available")
            self._highlander_enabled = False
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[UNIFIED] [HIGHLANDER] ❌ Initialization failed: {e}")
            self._highlander_enabled = False
            import traceback
            traceback.print_exc()
    
    def _run_highlander_round(self, cycle_count: int):
        """Run a Highlander Protocol tournament round.
        
        Each round may involve:
        - Battles between organisms (winner absorbs loser)
        - Alliance formation and betrayal
        - Predation of weak by strong
        - Champion checkpointing
        
        NOTE: Time-based gating is handled by the caller (eval_interval_seconds).
        The rounds_per_cycle config is IGNORED here to avoid double-gating.
        """
        try:
            # Get organisms from network component
            network = getattr(self, '_highlander_network', None)
            if not network or not hasattr(network, 'organisms'):
                # Try to get network from reality_sim
                if self.reality_sim and hasattr(self.reality_sim, 'components'):
                    network = self.reality_sim.components.get('network')
                    self._highlander_network = network
            
            if not network or not hasattr(network, 'organisms'):
                return  # No organisms to battle
            
            organisms = network.organisms
            if not organisms:
                return  # Empty population
            
            # Convert to dict if needed
            if not isinstance(organisms, dict):
                organisms = {getattr(o, 'id', str(id(o))): o for o in organisms}
            
            # Define fitness getter
            def get_fitness(organism) -> float:
                if hasattr(organism, 'fitness'):
                    return organism.fitness
                if hasattr(organism, 'get_fitness'):
                    return organism.get_fitness()
                return 0.5  # Default fitness
            
            # Run one tournament round with proper arguments
            results = self.highlander_protocol.run_round(organisms, get_fitness)
            
            # Check for champion emergence
            champion = self.highlander_protocol.get_current_champion()
            if champion and self.highlander_protocol.phase.name == 'CHAMPION':
                champion_id = champion.get('id', 'unknown')
                print(f"\n⚔️ [HIGHLANDER] THE CHAMPION EMERGES: {champion_id}")
                print(f"   Stats: {champion.get('stats', {})}")
                # NOTE: Capsule saving handled by highlander_protocol._crown_champion()
            
            # Log round results
            if results:
                population = self.highlander_protocol.get_population_count()
                self.logger.log_state('highlander', {
                    'event': 'round_complete',
                    'cycle': cycle_count,
                    'phase': self.highlander_protocol.phase.name,
                    'population': population,
                    'battles': len(results.get('battles', [])),
                    'eliminations': results.get('total_eliminations', len(results.get('battles', []))),
                    'alliances': len(results.get('alliances_formed', []))
                })
                
                # Print status update
                battles_count = len(results.get('battles', []))
                # Total eliminations = battles (1 death each) + culling + predation
                eliminations_count = results.get('total_eliminations', battles_count)
                alliances_count = len(results.get('alliances_formed', []))
                
                if battles_count > 0 or eliminations_count > 0:
                    print(f"[HIGHLANDER] Round {cycle_count}: "
                          f"⚔️ {battles_count} battles, "
                          f"💀 {eliminations_count} eliminated, "
                          f"🤝 {alliances_count} alliances, "
                          f"👥 {population} remaining")
                
                # 💀 ACTUALLY REMOVE ELIMINATED ORGANISMS FROM NETWORK
                fallen = self.highlander_protocol.fallen
                if fallen and network and hasattr(network, 'organisms'):
                    removed_count = 0
                    for fallen_id in fallen:
                        if fallen_id in network.organisms:
                            del network.organisms[fallen_id]
                            removed_count += 1
                            
                            # 🧹 MEMORY LEAK FIX: Clean up context memory for dead organisms
                            if hasattr(network, 'context_memory') and network.context_memory:
                                try:
                                    # Convert fallen_id to int if needed (context_memory uses int keys)
                                    if isinstance(fallen_id, str) and '_' in fallen_id:
                                        try:
                                            org_id_int = int(fallen_id.split('_')[-1])
                                        except (ValueError, IndexError):
                                            org_id_int = abs(hash(fallen_id)) % (2**31)
                                    else:
                                        org_id_int = abs(hash(fallen_id)) % (2**31)
                                    network.context_memory.cleanup_dead_organism(org_id_int)
                                except (ValueError, AttributeError):
                                    pass  # Graceful degradation
                    if removed_count > 0:
                        print(f"[HIGHLANDER] 🪦 {removed_count} organisms permanently removed from network")
            
            # 🌱 GERMINATION - Spawn new organisms if population too low
            if hasattr(self, '_germination_callback') and self._germination_callback:
                new_organisms = self._germination_callback()
                if new_organisms:
                    print(f"[HIGHLANDER] 🌱 Germinated {len(new_organisms)} new warriors from the genetic pool")
                    
                    # Log germination
                    self.logger.log_state('highlander', {
                        'event': 'germination',
                        'cycle': cycle_count,
                        'count': len(new_organisms),
                        'ids': [getattr(o, 'id', str(id(o))) for o in new_organisms],
                        'pool_stats': self.germination_pool.get_pool_stats() if self.germination_pool else {}
                    })
            
            # ⚔️🪐 ALLIANCE WARFARE - Collective battles for existential dominance
            if hasattr(self, 'alliance_warfare') and self.alliance_warfare:
                # Process alliance round (cleanup, proposal timeouts, alliance dissolution)
                # Also wires Illumination Engine system references to organisms
                causation_ref = getattr(self, 'causation_explorer', None)
                war_results = self.alliance_warfare.process_round(
                    organisms, get_fitness, causation_explorer=causation_ref
                )
                
                # 🤝 PROCESS ORGANISM COOPERATION DECISIONS → ALLIANCE ACTIONS
                # When organisms choose "cooperate" action, they may form/join alliances
                alliance_actions = self._process_organism_alliance_decisions(organisms, get_fitness)
                if alliance_actions:
                    war_results.update(alliance_actions)
                
                # Log alliance warfare activity
                if war_results:
                    alliance_count = war_results.get('alliances', 0)
                    proposals_timed_out = war_results.get('proposals_timed_out', 0)
                    alliances_dissolved = war_results.get('alliances_dissolved', 0)
                    
                    if alliances_dissolved > 0:
                        print(f"[ALLIANCE WAR] 💀 {alliances_dissolved} alliance(s) dissolved (insufficient members)")
                    
                    if proposals_timed_out > 0:
                        print(f"[ALLIANCE WAR] ⏰ {proposals_timed_out} proposal(s) timed out")
                    
                    # Log to state
                    self.logger.log_state('highlander', {
                        'event': 'alliance_round',
                        'cycle': cycle_count,
                        'alliance_count': alliance_count,
                        'proposals_timed_out': proposals_timed_out,
                        'alliances_dissolved': alliances_dissolved
                    })
                          
        except Exception as e:
            print(f"[HIGHLANDER] Round error: {e}")
            import traceback
            traceback.print_exc()
            import traceback
            traceback.print_exc()
    
    def _process_organism_alliance_decisions(self, organisms: Dict[str, Any], 
                                              get_fitness: callable) -> Dict[str, Any]:
        """
        Process organism "cooperate" decisions and convert them to alliance actions.
        
        When organisms choose action 1 (cooperate), this checks if they should:
        1. Form a new alliance (if not in one and high fitness)
        2. Invite nearby organisms (if alliance founder)
        3. Accept pending invites (if invited)
        
        This bridges the neural decision system with the Alliance Warfare system.
        """
        results = {
            'alliances_formed': 0,
            'invites_sent': 0,
            'invites_accepted': 0
        }
        
        if not hasattr(self, 'alliance_warfare') or not self.alliance_warfare:
            return results
        
        aws = self.alliance_warfare
        
        # Get organisms by action type
        cooperative_orgs = []  # action 1 = cooperate
        competitive_orgs = []  # action 2 = compete
        moving_orgs = []       # action 0 = move
        resting_orgs = []      # action 3 = rest
        reproducing_orgs = []  # action 4 = reproduce
        isolating_orgs = []    # action 5 = isolate
        
        for org_id, org in organisms.items():
            action = None
            if hasattr(org, 'last_action'):
                action = org.last_action
            elif hasattr(org, 'brain') and hasattr(org.brain, 'last_action'):
                action = org.brain.last_action
            
            if action == 0:  # move
                moving_orgs.append((org_id, org))
            elif action == 1:  # cooperate
                cooperative_orgs.append((org_id, org))
            elif action == 2:  # compete
                competitive_orgs.append((org_id, org))
            elif action == 3:  # rest
                resting_orgs.append((org_id, org))
            elif action == 4:  # reproduce
                reproducing_orgs.append((org_id, org))
            elif action == 5:  # isolate
                isolating_orgs.append((org_id, org))
        
        if not cooperative_orgs:
            return results
        
        # Process each cooperative organism
        for org_id, org in cooperative_orgs:
            fitness = get_fitness(org)
            current_alliance = aws.get_organism_alliance(org_id)
            
            # High fitness + no alliance = FOUND one!
            if not current_alliance and fitness > 0.6:
                # Generate a name based on organism's concepts
                name_parts = ["United", "Alliance", "Pact", "Legion", "Order"]
                if hasattr(org, 'atomic_language') and hasattr(org.atomic_language, 'atoms'):
                    concepts = list(org.atomic_language.atoms.keys())[:3]
                    if concepts:
                        name_parts = concepts + ["Alliance"]
                
                alliance_name = f"{random.choice(name_parts)}_{org_id[:6]}"
                
                alliance_id = aws.organism_create_alliance(org_id, alliance_name)
                if alliance_id:
                    results['alliances_formed'] += 1
                    print(f"[ALLIANCE] 🪐 {org_id[:8]} founded '{alliance_name}' (fitness: {fitness:.2f})")
                    # FEEDBACK: Organism learns founding worked
                    if hasattr(org, 'record_alliance_event'):
                        org.record_alliance_event('founded', True)
            
            # In alliance + cooperating = invite others
            elif current_alliance:
                alliance = aws.alliances.get(current_alliance)
                if alliance and org_id in alliance.members:
                    # Any member can invite - organic growth (matches alliance_warfare.py)
                    # Find nearby cooperative organisms not in an alliance
                    for other_id, other_org in organisms.items():
                        if other_id == org_id:
                            continue
                        if aws.get_organism_alliance(other_id):
                            continue  # Already in alliance
                        
                        # Check if other is also cooperative
                        other_cooperative = False
                        if hasattr(other_org, 'last_action') and other_org.last_action == 1:
                            other_cooperative = True
                        elif hasattr(other_org, 'brain') and hasattr(other_org.brain, 'last_action'):
                            if other_org.brain.last_action == 1:
                                other_cooperative = True
                        
                        if other_cooperative and len(alliance.members) < 10:
                            # 🗣️ PRE-INVITE COMMUNICATION - Organisms talk before joining!
                            # Language is the medium for coordination
                            exchange_quality = 0.0
                            if hasattr(org, 'speak_to'):
                                try:
                                    exchange = org.speak_to(other_org, context='alliance')
                                    exchange_quality = exchange.get('exchange_quality', 0)
                                except Exception:
                                    pass  # Communication failure doesn't block invite
                            
                            proposal_id = aws.organism_propose_invite(org_id, other_id)
                            if proposal_id:
                                results['invites_sent'] += 1
                                
                                # Accept based on communication quality + cooperation
                                # Better communication = higher acceptance chance
                                accept_threshold = 0.3 if exchange_quality > 0.5 else 0.7
                                accept = other_cooperative and (exchange_quality > 0.2 or random.random() > accept_threshold)
                                
                                if aws.organism_respond_to_invite(other_id, proposal_id, accept=accept):
                                    results['invites_accepted'] += 1
                                    print(f"[ALLIANCE] 🤝 {other_id[:8]} joined '{alliance.name}' (comm: {exchange_quality:.2f})")
                                    # FEEDBACK: Both organisms learn cooperation worked
                                    if hasattr(org, 'record_alliance_event'):
                                        org.record_alliance_event('recruited', True)
                                    if hasattr(other_org, 'record_alliance_event'):
                                        other_org.record_alliance_event('joined', True)
                            
                            # Only invite one per round to prevent spam
                            break
                
                # ═══════════════════════════════════════════════════════════════════════
                # 🏛️ WARCHIEF COOPERATING → CONFEDERATION PROPOSAL
                # ═══════════════════════════════════════════════════════════════════════
                # If warchief cooperates, evaluate confederation with similar alliances
                if alliance.warchief_id == org_id and not alliance.at_war_with:
                    # Check if already in confederation
                    if alliance.alliance_id in aws.alliance_to_confederation:
                        # Invite similar alliances to our confederation
                        confederation_id = aws.alliance_to_confederation[alliance.alliance_id]
                        for other_id, other in aws.alliances.items():
                            if other_id == alliance.alliance_id:
                                continue
                            if other_id in aws.alliance_to_confederation:
                                continue
                            if other.at_war_with:
                                continue
                            
                            similarity = 1.0 - aws.calculate_behavioral_divergence(alliance.alliance_id, other_id)
                            if similarity > 0.6:
                                # 🗣️ CONFEDERATION DIPLOMACY - Warchiefs negotiate!
                                # Communication affects whether they join
                                comm_quality = 0.0
                                if other.warchief_id:
                                    other_warchief = organisms.get(other.warchief_id)
                                    if org and other_warchief and hasattr(org, 'speak_to'):
                                        try:
                                            exchange = org.speak_to(other_warchief, context='alliance')
                                            comm_quality = exchange.get('exchange_quality', 0)
                                        except:
                                            pass
                                
                                # Better communication = more likely to accept
                                adjusted_similarity = similarity + (comm_quality * 0.2)
                                if adjusted_similarity > 0.6:
                                    proposal_id = aws.alliance_propose_confederation_invite(alliance.alliance_id, other_id)
                                    if proposal_id:
                                        target_name = other.name
                                        confederation = aws.confederations.get(confederation_id)
                                        confed_name = confederation.name if confederation else confederation_id[:8]
                                        print(f"[ALLIANCE] 🏛️ Warchief {org_id[:8]} invites '{target_name}' to '{confed_name}' (similarity: {similarity:.2f}, comm: {comm_quality:.2f})")
                                        results['confederation_invites'] = results.get('confederation_invites', 0) + 1
                                break  # One invite per round
                    else:
                        # Consider creating confederation with similar alliance
                        if alliance.wars_won >= 1:  # Proven themselves
                            for other_id, other in aws.alliances.items():
                                if other_id == alliance.alliance_id:
                                    continue
                                if other_id in aws.alliance_to_confederation:
                                    continue
                                if other.at_war_with:
                                    continue
                                
                                similarity = 1.0 - aws.calculate_behavioral_divergence(alliance.alliance_id, other_id)
                                if similarity > 0.7:  # Higher bar to CREATE
                                    # 🗣️ Warchiefs discuss forming confederation
                                    comm_quality = 0.0
                                    if other.warchief_id:
                                        other_warchief = organisms.get(other.warchief_id)
                                        if org and other_warchief and hasattr(org, 'speak_to'):
                                            try:
                                                exchange = org.speak_to(other_warchief, context='alliance')
                                                comm_quality = exchange.get('exchange_quality', 0)
                                            except:
                                                pass
                                    
                                    confed_name = f"United_{alliance.name[:10]}"
                                    confed_id = aws.alliance_create_confederation(alliance.alliance_id, confed_name)
                                    if confed_id:
                                        print(f"[ALLIANCE] 🏛️ '{alliance.name}' FOUNDED confederation '{confed_name}' (comm: {comm_quality:.2f})")
                                        results['confederations_formed'] = results.get('confederations_formed', 0) + 1
                                        # Invite the similar alliance
                                        proposal_id = aws.alliance_propose_confederation_invite(alliance.alliance_id, other_id)
                                        if proposal_id:
                                            print(f"[ALLIANCE] 🏛️ Inviting '{other.name}' to join")
                                            results['confederation_invites'] = results.get('confederation_invites', 0) + 1
                                    break
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ⚔️ COMPETITIVE ORGANISMS → WAR PROPOSALS OR ULTIMATUMS
        # ═══════════════════════════════════════════════════════════════════════════
        # When warchief competes, evaluate war against divergent alliances
        # Powerful alliances can issue "Join or Die" ultimatums first!
        for org_id, org in competitive_orgs:
            current_alliance = aws.get_organism_alliance(org_id)
            if not current_alliance:
                continue
            
            alliance = aws.alliances.get(current_alliance)
            if not alliance:
                continue
            
            # Only warchief can propose war/ultimatum
            if alliance.warchief_id != org_id:
                continue
            
            # Can't propose if already at war
            if alliance.at_war_with:
                continue
            
            # Find most divergent alliance
            target_id, divergence = aws.get_most_divergent_alliance(alliance.alliance_id)
            if not target_id or divergence < 0.4:
                continue
            
            target_alliance = aws.alliances.get(target_id)
            if not target_alliance:
                continue
            
            # Check power differential for ultimatum
            our_power = len(alliance.members) + alliance.wars_won * 2 + alliance.territory_count
            their_power = len(target_alliance.members) + target_alliance.wars_won * 2 + target_alliance.territory_count
            
            # 🗣️ ULTIMATUM PATH: If we're significantly stronger, try "Join or Die" first!
            if our_power > their_power * 1.5:
                ultimatum_result = aws.organism_issue_ultimatum(org_id, target_id, organisms)
                
                if ultimatum_result['outcome'] == 'submitted':
                    target_name = target_alliance.name
                    print(f"[ALLIANCE] 🏳️ '{target_name}' SUBMITS to ultimatum from '{alliance.name}'!")
                    print(f"   Communication quality: {ultimatum_result.get('communication_quality', 0):.2f}")
                    print(f"   Members absorbed: {ultimatum_result.get('members_absorbed', 0)}")
                    results['ultimatums_accepted'] = results.get('ultimatums_accepted', 0) + 1
                    continue  # No war needed
                    
                elif ultimatum_result['outcome'] == 'refused':
                    target_name = target_alliance.name
                    print(f"[ALLIANCE] ☠️ '{target_name}' REFUSES ultimatum - WAR DECLARED!")
                    print(f"   Communication quality: {ultimatum_result.get('communication_quality', 0):.2f}")
                    results['ultimatums_refused'] = results.get('ultimatums_refused', 0) + 1
                    results['wars_declared'] = results.get('wars_declared', 0) + 1
                    # War already declared by ultimatum function
                    continue
            
            # Standard war proposal path (for equal-power alliances)
            proposal_id = aws.organism_propose_war(org_id, target_id)
            if proposal_id:
                target_name = target_alliance.name
                print(f"[ALLIANCE] ⚔️ Warchief {org_id[:8]} PROPOSES WAR on '{target_name}' (divergence: {divergence:.2f})")
                results['wars_proposed'] = results.get('wars_proposed', 0) + 1
                # FEEDBACK: Organism learns war proposal (outcome feedback comes later when war resolves)
                if hasattr(org, 'record_alliance_event'):
                    org.record_alliance_event('war_proposed', True)
                
                # Alliance members vote based on their own action
                # Competitive members vote YES, cooperative vote NO
                for proposal in alliance.pending_proposals:
                    if proposal.proposal_id == proposal_id:
                        for member_id in alliance.members:
                            if member_id == org_id:
                                continue  # Warchief already voted
                            # Check member's action
                            member_org = organisms.get(member_id)
                            if member_org:
                                member_action = None
                                if hasattr(member_org, 'last_action'):
                                    member_action = member_org.last_action
                                elif hasattr(member_org, 'brain') and hasattr(member_org.brain, 'last_action'):
                                    member_action = member_org.brain.last_action
                                
                                if member_action == 2:  # compete = vote YES
                                    proposal.votes_for.add(member_id)
                                elif member_action == 1:  # cooperate = vote NO
                                    proposal.votes_against.add(member_id)
                                # Other actions = abstain
                        
                        # Check if vote resolves
                        aws._check_proposal_resolution(alliance, proposal)
                        break
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ⚔️ ACTIVE WAR RESOLUTION - Competitive organisms FIGHT in active wars
        # ═══════════════════════════════════════════════════════════════════════════
        # Wars were declared but never fought! Now competitive organisms participate
        alliances_at_war = [(aid, a) for aid, a in aws.alliances.items() if a.at_war_with]
        wars_processed = set()  # Track war pairs to avoid double processing
        
        for alliance_id, alliance in alliances_at_war:
            for enemy_id in list(alliance.at_war_with):
                # Create unique war key to avoid processing twice
                war_key = tuple(sorted([alliance_id, enemy_id]))
                if war_key in wars_processed:
                    continue
                wars_processed.add(war_key)
                
                enemy = aws.alliances.get(enemy_id)
                if not enemy:
                    continue
                
                # 🗣️ PRE-WAR ROUND COMMUNICATION - Warchiefs exchange words!
                # Taunts, threats, or last-chance negotiations
                war_comm_quality = 0.0
                if alliance.warchief_id and enemy.warchief_id:
                    our_chief = organisms.get(alliance.warchief_id)
                    their_chief = organisms.get(enemy.warchief_id)
                    if our_chief and their_chief and hasattr(our_chief, 'speak_to'):
                        try:
                            exchange = our_chief.speak_to(their_chief, context='battle')
                            war_comm_quality = exchange.get('exchange_quality', 0)
                            if war_comm_quality > 0:
                                print(f"[ALLIANCE] 🗣️ War talk: {alliance.name} ↔ {enemy.name} (quality: {war_comm_quality:.2f})")
                        except:
                            pass
                
                # Build participating organisms dict - competitive organisms FIGHT
                participating = {}
                for org_id, org in competitive_orgs:
                    org_alliance = aws.get_organism_alliance(org_id)
                    if org_alliance in [alliance_id, enemy_id]:
                        participating[org_id] = True  # Fighting!
                
                # Also check all alliance members - anyone can choose to fight
                for member_id in alliance.members:
                    if member_id not in participating:
                        member_org = organisms.get(member_id)
                        if member_org:
                            action = getattr(member_org, 'last_action', None)
                            if action is None and hasattr(member_org, 'brain'):
                                action = getattr(member_org.brain, 'last_action', None)
                            # Competitive = fighting, others = not participating
                            participating[member_id] = (action == 2)
                
                for member_id in enemy.members:
                    if member_id not in participating:
                        member_org = organisms.get(member_id)
                        if member_org:
                            action = getattr(member_org, 'last_action', None)
                            if action is None and hasattr(member_org, 'brain'):
                                action = getattr(member_org.brain, 'last_action', None)
                            participating[member_id] = (action == 2)
                
                # Resolve war round!
                war_result = aws.resolve_war_round(
                    alliance_id=alliance_id,
                    enemy_id=enemy_id,
                    get_organism_fitness=get_fitness,
                    participating_organisms=participating
                )
                
                if war_result:
                    results['war_rounds'] = results.get('war_rounds', 0) + 1
                    if war_result.get('war_ended'):
                        results['wars_ended'] = results.get('wars_ended', 0) + 1
                        print(f"[ALLIANCE] 🏆 WAR ENDED: {war_result['winner']} defeats {war_result['loser']}!")
                    else:
                        print(f"[ALLIANCE] ⚔️ War round: {alliance.name} vs {enemy.name} (margin: {war_result.get('margin', 0):.1%})")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 🌍 MOVING ORGANISMS → TERRITORY CLAIMS
        # ═══════════════════════════════════════════════════════════════════════════
        # When organism moves + in alliance, they're exploring FOR the alliance
        for org_id, org in moving_orgs:
            current_alliance = aws.get_organism_alliance(org_id)
            if not current_alliance:
                continue
            
            alliance = aws.alliances.get(current_alliance)
            if not alliance:
                continue
            
            # Any member can propose territory claims (exploring for the group)
            if aws.uncontrolled_territories:
                # Pick a random unclaimed territory
                territory = random.choice(list(aws.uncontrolled_territories))
                
                # 🗣️ TERRITORY COMMUNICATION - Explorer announces to alliance!
                # The explorer tells their alliance about the new territory
                if alliance.warchief_id and alliance.warchief_id != org_id:
                    warchief = organisms.get(alliance.warchief_id)
                    if warchief and hasattr(org, 'speak_to'):
                        try:
                            exchange = org.speak_to(warchief, context='general')
                            if exchange.get('exchange_quality', 0) > 0:
                                print(f"[ALLIANCE] 🗣️ {org_id[:8]} reports {territory.value} discovery to warchief")
                        except:
                            pass
                
                proposal_id = aws.organism_claim_territory(org_id, territory)
                if proposal_id:
                    print(f"[ALLIANCE] 🌍 {org_id[:8]} proposes claiming {territory.value} for '{alliance.name}'")
                    results['territory_claims'] = results.get('territory_claims', 0) + 1
                    # FEEDBACK: Organism learns exploration led to claim
                    if hasattr(org, 'record_alliance_event'):
                        org.record_alliance_event('territory_claimed', True)
                    
                    # Other moving members vote YES (explorers agree)
                    for proposal in alliance.pending_proposals:
                        if proposal.proposal_id == proposal_id:
                            for member_id in alliance.members:
                                if member_id == org_id:
                                    continue
                                member_org = organisms.get(member_id)
                                if member_org:
                                    member_action = getattr(member_org, 'last_action', None)
                                    if member_action is None and hasattr(member_org, 'brain'):
                                        member_action = getattr(member_org.brain, 'last_action', None)
                                    if member_action == 0:  # move = vote YES
                                        proposal.votes_for.add(member_id)
                            aws._check_proposal_resolution(alliance, proposal)
                            break
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 🥋 RESTING ORGANISMS → DOJO TRAINING
        # ═══════════════════════════════════════════════════════════════════════════
        # When organism rests + in alliance, they train together at the dojo
        resting_alliance_members = {}  # alliance_id -> list of (org_id, org) tuples
        for org_id, org in resting_orgs:
            current_alliance = aws.get_organism_alliance(org_id)
            if current_alliance:
                if current_alliance not in resting_alliance_members:
                    resting_alliance_members[current_alliance] = []
                resting_alliance_members[current_alliance].append((org_id, org))
        
        # Run dojo sessions for alliances with 2+ resting members
        for alliance_id, resting_members in resting_alliance_members.items():
            if len(resting_members) >= 2:
                alliance = aws.alliances.get(alliance_id)
                if alliance:
                    member_ids = [m[0] for m in resting_members]
                    
                    # 🗣️ PRE-TRAINING COMMUNICATION - Teammates coordinate!
                    # Alliance members talk before training to share strategy
                    training_comm_quality = 0.0
                    if len(resting_members) >= 2:
                        org1 = resting_members[0][1]
                        org2 = resting_members[1][1]
                        if org1 and org2 and hasattr(org1, 'speak_to'):
                            try:
                                exchange = org1.speak_to(org2, context='alliance')
                                training_comm_quality = exchange.get('exchange_quality', 0)
                                if training_comm_quality > 0.3:
                                    print(f"[ALLIANCE] 🗣️ Dojo coordination: {training_comm_quality:.2f} quality")
                            except:
                                pass
                    
                    print(f"[ALLIANCE] 🥋 {len(member_ids)} members training at '{alliance.name}' dojo")
                    results['dojo_sessions'] = results.get('dojo_sessions', 0) + 1
                    
                    # Try to run actual dojo training if DojoManager available
                    try:
                        from reality_simulator.evolution.alliance_dojo import DojoManager
                        
                        # Get or create dojo manager (cached on aws for reuse)
                        if not hasattr(aws, '_dojo_manager'):
                            aws._dojo_manager = DojoManager()
                        
                        # Create organism getter function (gym_runner needs full organism for experience recording)
                        def get_brain(org_id):
                            org = organisms.get(org_id)
                            return org  # Return full organism, not just brain
                        
                        # Run actual sparring session!
                        session = aws._dojo_manager.run_alliance_training(
                            alliance_id=alliance_id,
                            members=member_ids,
                            get_organism_brain=get_brain,
                            training_type='sparring',
                            rounds=2  # Keep short per round
                        )
                        
                        if session:
                            results['dojo_matches'] = results.get('dojo_matches', 0) + session.total_matches
                            results['dojo_experiences'] = results.get('dojo_experiences', 0) + session.total_experiences
                            print(f"[ALLIANCE] 🥋 Session complete: {session.total_matches} matches, {session.total_experiences} experiences")
                    except Exception as e:
                        # Fallback: just track sessions if dojo unavailable
                        pass
                    
                    # Mark organisms as having trained + FEEDBACK
                    for org_id, org in resting_members:
                        if org:
                            if hasattr(org, 'dojo_sessions'):
                                org.dojo_sessions = getattr(org, 'dojo_sessions', 0) + 1
                            # FEEDBACK: Organism learns resting with allies = training
                            if hasattr(org, 'record_alliance_event'):
                                org.record_alliance_event('trained', True)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 👶 REPRODUCING ORGANISMS → ALLIANCE SPAWN (Daughter Alliance)
        # ═══════════════════════════════════════════════════════════════════════════
        # When organism reproduces + large alliance, can spawn a daughter alliance
        for org_id, org in reproducing_orgs:
            current_alliance = aws.get_organism_alliance(org_id)
            if not current_alliance:
                continue
            
            alliance = aws.alliances.get(current_alliance)
            if not alliance:
                continue
            
            # Only spawn if alliance is large enough (6+ members)
            if len(alliance.members) < 6:
                continue
            
            # Only warchief or founder can spawn daughter
            if org_id not in [alliance.warchief_id, alliance.founder_id]:
                continue
            
            # Find other reproducing members to form the new alliance
            reproducing_in_alliance = [
                m_id for m_id, m_org in reproducing_orgs 
                if aws.get_organism_alliance(m_id) == current_alliance and m_id != org_id
            ]
            
            if len(reproducing_in_alliance) >= 2:  # Need 2+ others
                # 🗣️ SPAWN COMMUNICATION - Leader speaks to those about to leave
                # Share wisdom before they branch off
                for other_id in reproducing_in_alliance[:2]:
                    other_org = organisms.get(other_id)
                    if other_org and hasattr(org, 'speak_to'):
                        try:
                            exchange = org.speak_to(other_org, context='general')
                            if exchange.get('exchange_quality', 0) > 0:
                                print(f"[ALLIANCE] 🗣️ {org_id[:8]} shares wisdom with spawn member {other_id[:8]}")
                        except:
                            pass
                
                # Create daughter alliance
                daughter_name = f"{alliance.name}_Spawn_{int(time.time()) % 10000}"
                
                # The reproducing organism leaves and founds new alliance
                aws.alliances[current_alliance].remove_member(org_id, is_betrayal=False)
                daughter_id = aws.organism_create_alliance(org_id, daughter_name)
                
                if daughter_id:
                    # Other reproducers join the daughter
                    for other_id in reproducing_in_alliance[:2]:  # Take 2
                        aws.alliances[current_alliance].remove_member(other_id, is_betrayal=False)
                        aws.alliances[daughter_id].add_member(other_id)
                    
                    print(f"[ALLIANCE] 👶 '{alliance.name}' spawned daughter '{daughter_name}' (3 members)")
                    results['alliances_spawned'] = results.get('alliances_spawned', 0) + 1
                    # FEEDBACK: Organisms learn spawning succeeded
                    if hasattr(org, 'record_alliance_event'):
                        org.record_alliance_event('spawned_alliance', True)
                    for other_id in reproducing_in_alliance[:2]:
                        other_org = organisms.get(other_id)
                        if other_org and hasattr(other_org, 'record_alliance_event'):
                            other_org.record_alliance_event('joined_spawn', True)
                break  # One spawn per round
        
        # ═══════════════════════════════════════════════════════════════════════════
        # 🚪 ISOLATING ORGANISMS → LEAVE/BETRAY ALLIANCE
        # ═══════════════════════════════════════════════════════════════════════════
        # When organism isolates + in alliance, they want out
        for org_id, org in isolating_orgs:
            current_alliance = aws.get_organism_alliance(org_id)
            if not current_alliance:
                continue
            
            alliance = aws.alliances.get(current_alliance)
            if not alliance:
                continue
            
            # Isolating = leaving (betrayal if at war)
            is_at_war = len(alliance.at_war_with) > 0
            if aws.organism_betray_alliance(org_id, sabotage=False):
                if is_at_war:
                    print(f"[ALLIANCE] 🗡️ {org_id[:8]} BETRAYED '{alliance.name}' (left during war!)")
                    results['betrayals'] = results.get('betrayals', 0) + 1
                    # FEEDBACK: Organism learns betrayal has consequences (negative)
                    if hasattr(org, 'record_alliance_event'):
                        org.record_alliance_event('betrayed', True)  # 'betrayed' has -0.8 reward
                else:
                    print(f"[ALLIANCE] 🚪 {org_id[:8]} left '{alliance.name}'")
                    results['departures'] = results.get('departures', 0) + 1
                    # FEEDBACK: Leaving peacefully is neutral
                    if hasattr(org, 'record_alliance_event'):
                        org.record_alliance_event('left', True)
        
        return results
    
    def run(self):
        """Run the unified system"""
        print("="*70)
        print("[BUTTERFLY] THE BUTTERFLY SYSTEM - FLYING")
        print("="*70)
        print("Press Ctrl+C to stop\n")
        
        try:
            if not self.controller:
                print("[UNIFIED] [FAIL] Explorer not available. Cannot run.")
                return
            
            # Get simulation timing config
            simulation_config = self.active_config.get('simulation', {})
            
            # Highlander evaluation interval (time-based)
            highlander_config = self.active_config.get('highlander', {})
            highlander_eval_interval_seconds = highlander_config.get('eval_interval_seconds', 600)  # Default: 600 seconds (10 min boom-bust waves)
            last_highlander_time = time.time()
            print(f"[UNIFIED] Highlander eval interval: every {highlander_eval_interval_seconds} seconds")
            
            # Optional rate limiting (set target_fps > 0 to enable)
            # When 0 or not set, system runs as fast as hardware allows
            target_fps = simulation_config.get('target_fps', 0)  # Default 0 = unlimited
            if target_fps > 0:
                target_cycle_time = 1.0 / target_fps
                print(f"[UNIFIED] Rate limit: {target_fps} FPS (cycle time: {target_cycle_time:.3f}s)")
            else:
                target_cycle_time = 0
                print(f"[UNIFIED] Rate limit: UNLIMITED (full hardware speed)")
            
            # Main loop
            cycle_count = 0
            cycle_start_time = time.time()
            while True:
                loop_start = time.time()
                
                updated_config = self.config_watcher.check_for_updates()
                if updated_config is not None:
                    self._apply_runtime_config(updated_config)
                    # Update timing config if changed
                    simulation_config = self.active_config.get('simulation', {})
                    highlander_config = self.active_config.get('highlander', {})
                    highlander_eval_interval_seconds = highlander_config.get('eval_interval_seconds', 600)
                    target_fps = simulation_config.get('target_fps', 0)
                    target_cycle_time = 1.0 / target_fps if target_fps > 0 else 0

                # Update reality sim (includes neural training and config tuner)
                if self.reality_sim:
                    try:
                        # Inject VP data from Explorer into network (Quick Win #1)
                        network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                        if network and self.controller and hasattr(self.controller, 'sentinel'):
                            try:
                                if hasattr(self.controller.sentinel, 'vp_history') and self.controller.sentinel.vp_history:
                                    latest_vp = self.controller.sentinel.vp_history[-1]
                                    if isinstance(latest_vp, dict):
                                        vp_total = latest_vp.get('total_vp')
                                        vp_components = latest_vp.get('component_breakdown', {})
                                        if hasattr(network, 'inject_vp_data'):
                                            network.inject_vp_data(vp_total=vp_total, vp_components=vp_components)
                            except Exception:
                                pass  # Don't break if VP injection fails
                        
                        self.reality_sim._update_simulation_components()
                        
                        # 📊 ORGANISM STATS UPDATE - Track age and fitness history for viewer
                        network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                        if network and hasattr(network, 'organisms'):
                            for org in network.organisms.values():
                                # Increment organism age
                                if hasattr(org, 'age'):
                                    org.age += 1
                                # Track fitness history (limit to last 30 values for memory)
                                if hasattr(org, 'fitness_history') and hasattr(org, 'fitness'):
                                    org.fitness_history.append(org.fitness)
                                    if len(org.fitness_history) > 30:
                                        org.fitness_history = org.fitness_history[-30:]
                    except Exception as e:
                        print(f"[ERROR] Reality sim update failed: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 🦋 ANTENNAE - Collective sensing and governance
                if hasattr(self, 'antennae') and self.antennae:
                    try:
                        network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                        if network and hasattr(network, 'organisms'):
                            # Generate report for context (if reporter available)
                            report = None
                            if hasattr(self, 'live_reporter') and self.live_reporter:
                                try:
                                    report = self.live_reporter.reporter.generate()
                                except Exception:
                                    pass
                            
                            # Sense the collective state
                            self.antennae.sense(network.organisms, report)
                            
                            # Let perception influence tuning
                            config_tuner = getattr(self.reality_sim, 'config_tuner', None)
                            if config_tuner:
                                changes = self.antennae.influence(config_tuner)
                    except Exception:
                        pass  # Don't break main loop if antennae fails
                
                # 🦋 UPDATE WEB UI ORGANISMS - Keep Butterfly Chat in sync with live organisms
                self._update_web_ui_organisms()

                # Get states from all systems
                reality_sim_state = self._get_reality_sim_state()
                explorer_state = self._get_explorer_state()
                djinn_kernel_state = self._get_djinn_kernel_state()

                # 🌉 PHASE SYNC INTEGRATION - Update network metrics and get predictions
                phase_sync_state = {}
                if self.phase_sync_bridge:
                    try:
                        # Update network metrics in phase sync bridge
                        network_data = {
                            'organism_count': reality_sim_state.get('organism_count', 0),
                            'connection_count': reality_sim_state.get('connection_count', 0),
                            'clustering_coefficient': reality_sim_state.get('clustering_coefficient', 0.0),
                            'modularity': reality_sim_state.get('modularity', 0.0),
                            'average_path_length': reality_sim_state.get('average_path_length', 0.0),
                            'connectivity': reality_sim_state.get('connection_count', 0) / max(1, reality_sim_state.get('organism_count', 1)),
                            'stability_index': 1.0 - reality_sim_state.get('modularity', 0.0)  # Rough estimate
                        }
                        collapsed = self.phase_sync_bridge.update_network_metrics(network_data)

                        # Get synchronization state
                        sync_data = self.phase_sync_bridge.synchronize_phases()
                        phase_sync_state = sync_data

                        # 🔮 COLLAPSE PREDICTION - Warn if imminent
                        will_collapse, estimated_gens = self.phase_sync_bridge.get_collapse_prediction()
                        if will_collapse and estimated_gens < 20 and estimated_gens > 0:
                            collapse_proximity = sync_data['network']['collapse_proximity']
                            warning_level = 'red' if collapse_proximity > 0.9 else ('orange' if collapse_proximity > 0.7 else 'yellow')
                            print(f"\n🔮 [{warning_level.upper()}] COLLAPSE PREDICTED IN ~{estimated_gens:.1f} GENERATIONS (proximity: {collapse_proximity:.1%})")

                        # 🌉 TRANSITION DETECTION
                        if collapsed and not getattr(self, '_collapse_announced', False):
                            print(f"\n🌉 ✨ CHAOS→PRECISION TRANSITION DETECTED ✨")
                            print(f"   Reality Sim: {sync_data['network']['organism_count']} organisms explored")
                            print(f"   Explorer: {sync_data['explorer']['vp_calculations']} VP calculations")
                            print(f"   Conversion factor: {self.phase_sync_bridge.exploration_to_precision_ratio}:1")
                            print(f"   The butterfly spreads its wings. 🦋\n")
                            self._collapse_announced = True

                    except Exception as e:
                        print(f"[UNIFIED] [WARN] Phase sync error: {e}")
                        phase_sync_state = {}

                # Get breath state for logging
                if self.controller and hasattr(self.controller, 'breath_engine'):
                    breath_state = self.controller.breath_engine.get_breath_state()
                    self.logger.log_breath(breath_state)

                # Log all states
                self.logger.log_reality_sim(reality_sim_state)
                self.logger.log_explorer(explorer_state)
                self.logger.log_djinn_kernel(djinn_kernel_state)
                
                # Log unified state snapshot (flatten nested dicts)
                unified_state = {
                    'timestamp': time.time()
                }
                # Flatten nested states with prefixes
                for key, value in reality_sim_state.items():
                    unified_state[f'reality_sim_{key}'] = value
                for key, value in explorer_state.items():
                    unified_state[f'explorer_{key}'] = value
                for key, value in djinn_kernel_state.items():
                    unified_state[f'djinn_{key}'] = value
                
                # Add neural metrics to unified state if available
                if self.reality_sim and hasattr(self.reality_sim, '_neural_metrics'):
                    neural_metrics = self.reality_sim._neural_metrics
                    for key, value in neural_metrics.items():
                        unified_state[f'neural_{key}'] = value
                    
                    # Log neural metrics to neural.log file
                    if neural_metrics.get('enabled', False):
                        self.logger.log_neural(neural_metrics)
                
                # Log ML analysis results if available
                if self.reality_sim and hasattr(self.reality_sim, '_ml_metrics'):
                    ml_metrics = self.reality_sim._ml_metrics
                    if ml_metrics and ml_metrics.get('enabled', False):
                        # Log ML metrics to neural.log (or create ml.log if needed)
                        ml_log_data = {
                            'enabled': True,
                            'organism_count': ml_metrics.get('organism_count', 0),
                            'n_clusters': ml_metrics.get('clustering', {}).get('n_clusters', 0),
                            'anomaly_count': ml_metrics.get('anomalies', {}).get('anomaly_count', 0),
                            'anomaly_ratio': f"{ml_metrics.get('anomalies', {}).get('anomaly_ratio', 0):.4f}",
                            'algorithm': ml_metrics.get('clustering', {}).get('algorithm', 'unknown')
                        }
                        self.logger.log_state('neural', ml_log_data)  # Use neural.log for now
                
                self.logger.log_state('state', unified_state)
                
                # Write unified shared state file (includes all three systems + phase sync)
                # This is the primary source of truth for the Causation Explorer
                self._write_unified_shared_state(reality_sim_state, explorer_state, djinn_kernel_state, phase_sync_state)
                
                # Phase 2: Feed events to Causation Explorer in real-time
                if self.causation_explorer:
                    try:
                        # Load latest state from shared state file (incremental)
                        self.causation_explorer._load_from_shared_state(force_reload=False)
                    except Exception as e:
                        pass  # Don't break if event feeding fails
                
                # Update visualization
                if self.visualization and self.visualization.running:
                    self.visualization.update(reality_sim_state, explorer_state, djinn_kernel_state)
                
                # Run one breath cycle (drives everything)
                if hasattr(self.controller, 'run_genesis_phase'):
                    self.controller.run_genesis_phase()
                elif hasattr(self.controller, 'run_sovereign_phase'):
                    self.controller.run_sovereign_phase()
                
                # 🗡️ HIGHLANDER PROTOCOL - Run tournament round (time-based)
                if getattr(self, '_highlander_enabled', False) and self.highlander_protocol:
                    current_time = time.time()
                    if current_time - last_highlander_time >= highlander_eval_interval_seconds:
                        self._run_highlander_round(cycle_count)
                        last_highlander_time = current_time
                
                # Optional rate limiting (only if target_fps > 0)
                # When disabled, system runs at full hardware speed
                elapsed = time.time() - loop_start
                if target_cycle_time > 0:
                    sleep_time = target_cycle_time - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                # else: running at full speed, no rate limiting
                
                # Increment cycle counter and break if requested
                # Use BREATH cycles, not loop iterations
                actual_breath_cycle = 0
                if self.controller and hasattr(self.controller, 'breath_engine'):
                    breath_state = self.controller.breath_engine.get_breath_state()
                    actual_breath_cycle = breath_state.get('cycle_count', cycle_count)
                else:
                    actual_breath_cycle = cycle_count
                    
                cycle_count += 1
                if self.max_cycles > 0 and actual_breath_cycle >= self.max_cycles:
                    print(f"[UNIFIED] Reached max breath cycles ({self.max_cycles}). Exiting loop.")
                    break
                
        except KeyboardInterrupt:
            print("\n[UNIFIED] Shutting down gracefully...")
            # Stop live reporter
            if hasattr(self, 'live_reporter') and self.live_reporter:
                self.live_reporter.stop()
            # Save neural checkpoint before exit
            self._save_shutdown_checkpoint("user_interrupt")
            self.logger.log_state('system', {'event': 'shutdown'})
            self.logger.shutdown()  # Drain async queue
        except Exception as e:
            print(f"\n[UNIFIED] [FAIL] Error: {e}")
            traceback.print_exc()
            # Stop live reporter
            if hasattr(self, 'live_reporter') and self.live_reporter:
                self.live_reporter.stop()
            # Try to save checkpoint even on error
            self._save_shutdown_checkpoint("error_recovery")
            self.logger.log_state('system', {'event': 'error', 'error': str(e)})
            self.logger.shutdown()  # Drain async queue
    
    def _save_shutdown_checkpoint(self, reason: str = "shutdown"):
        """
        Save a neural checkpoint during graceful shutdown.
        
        Called when:
        - User interrupts with Ctrl+C
        - An error occurs
        - Simulation terminates normally
        
        Args:
            reason: Why the checkpoint is being saved (for metadata)
        """
        if not self.reality_sim:
            return
        
        neural_trainer = getattr(self.reality_sim, 'neural_trainer', None)
        if not neural_trainer:
            return
        
        if not getattr(neural_trainer, 'checkpoint_enabled', False):
            print("[UNIFIED CHECKPOINT] Checkpointing disabled, skipping shutdown save")
            return
        
        network = self.reality_sim.components.get('network')
        if not network:
            print("[UNIFIED CHECKPOINT] No network available for shutdown checkpoint")
            return
        
        try:
            from datetime import datetime
            import os
            
            # Get current generation
            generation = getattr(network, 'generation', 0)
            
            # Create checkpoint directory
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}_shutdown"
            checkpoint_path = os.path.join(neural_trainer.checkpoint_dir, checkpoint_name)
            
            print(f"\n[UNIFIED CHECKPOINT] Saving shutdown checkpoint...")
            print(f"  Reason: {reason}")
            print(f"  Generation: {generation}")
            
            success = neural_trainer.save_checkpoint(
                checkpoint_dir=checkpoint_path,
                organisms=list(network.organisms.values()),
                generation=generation,
                metadata={
                    'trigger': 'shutdown',
                    'reason': reason,
                    'entry_point': 'unified_entry',
                    'training_step_count': neural_trainer.training_step_count
                }
            )
            
            if success:
                print("[UNIFIED CHECKPOINT] ✓ Shutdown checkpoint saved successfully!")
                # Rotate old checkpoints
                neural_trainer.rotate_checkpoints(
                    neural_trainer.checkpoint_dir,
                    neural_trainer.checkpoint_max_count
                )
            else:
                print("[UNIFIED CHECKPOINT] ⚠ Shutdown checkpoint save returned False")
                
        except Exception as e:
            print(f"[UNIFIED CHECKPOINT] ⚠ Failed to save shutdown checkpoint: {e}")
            import traceback
            traceback.print_exc()

    def _apply_runtime_config(self, new_config: Dict[str, Any]):
        """Apply runtime configuration updates to live subsystems."""
        if not isinstance(new_config, dict):
            return

        applied_sections = []
        try:
            if self.controller and hasattr(self.controller, 'apply_runtime_config'):
                applied = self.controller.apply_runtime_config(new_config) or []
                applied_sections.extend(applied)
            
            # GAP 6 FIX: Sync hot reload config to AtomicConfigSystem
            # This ensures runtime config changes propagate to the meta-cognitive tuner
            if self.reality_sim and hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
                try:
                    atomic_config = self.reality_sim.config_tuner
                    synced_params = 0
                    
                    # Flatten and sync key config sections
                    config_mappings = {
                        'neural': ['neural.learning_rate', 'neural.batch_size', 'neural.epsilon'],
                        'language': ['language.vocab_size', 'language.embedding_dim'],
                        'simulation': ['simulation.max_organisms', 'simulation.mutation_rate'],
                        'evolution': ['evolution.selection_pressure', 'evolution.crossover_rate']
                    }
                    
                    for section, param_paths in config_mappings.items():
                        if section in new_config:
                            section_config = new_config[section]
                            for param_path in param_paths:
                                # Extract param name from path (e.g., 'neural.learning_rate' -> 'learning_rate')
                                param_name = param_path.split('.')[-1]
                                if param_name in section_config:
                                    value = section_config[param_name]
                                    # Check if atom exists and update
                                    if hasattr(atomic_config, 'atoms') and param_name in atomic_config.atoms:
                                        if atomic_config.atoms[param_name].value != value:
                                            atomic_config.atoms[param_name].update_value(value, 'hot_reload_sync')
                                            synced_params += 1
                    
                    if synced_params > 0:
                        applied_sections.append(f'atomic_config({synced_params})')
                        logger.debug(f"[UNIFIED→ATOMIC] Synced {synced_params} params from hot reload")
                except Exception as atomic_err:
                    logger.debug(f"[UNIFIED] AtomicConfigSystem sync failed: {atomic_err}")
            
            # 🌉 Propagate language_game_bridge parameter changes to running bridge
            # This enables ConfigTuner changes to reach the active bridge without direct wiring
            if self.highlander_protocol and hasattr(self.highlander_protocol, 'language_bridge'):
                bridge = self.highlander_protocol.language_bridge
                if bridge and hasattr(bridge, 'update_parameters'):
                    try:
                        neural_config = new_config.get('neural', {})
                        lgb_config = neural_config.get('language_game_bridge', {})
                        if lgb_config:
                            changes = bridge.update_parameters(
                                bias_strength=lgb_config.get('bias_strength'),
                                learning_rate=lgb_config.get('learning_rate')
                            )
                            if changes:
                                applied_sections.append('language_game_bridge')
                                print(f"[UNIFIED] [BRIDGE] 🌉 Parameters updated: {changes}")
                    except Exception as bridge_err:
                        logger.debug(f"[UNIFIED] Bridge parameter sync failed: {bridge_err}")
            
            self.active_config = new_config
            summary = ', '.join(applied_sections) if applied_sections else 'no-op'
            print(f"[UNIFIED] [CONFIG] Runtime config applied ({summary})")
            self.logger.log_state('system', {
                'event': 'config_runtime_update',
                'applied': summary,
                'timestamp': time.time()
            })
        except Exception as err:
            print(f"[UNIFIED] [WARN] Runtime config update failed: {err}")
            self.logger.log_state('system', {
                'event': 'config_runtime_update_failed',
                'error': str(err)
            })
    
    def _get_reality_sim_state(self) -> Dict[str, Any]:
        """Get Reality Simulator state"""
        if not self.reality_sim or not self.reality_sim.components:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        network = self.reality_sim.components.get('network')
        if not network:
            return {'organism_count': 0, 'connection_count': 0, 'modularity': 0, 'clustering_coefficient': 0}
        
        state = {
            'organism_count': len(network.organisms),
            'connection_count': len(network.connections),
            'modularity': network.metrics.modularity if hasattr(network.metrics, 'modularity') else 0,
            'clustering_coefficient': network.metrics.clustering_coefficient if hasattr(network.metrics, 'clustering_coefficient') else 0,
            'average_path_length': network.metrics.average_path_length if hasattr(network.metrics, 'average_path_length') else 0,
            'generation': network.generation if hasattr(network, 'generation') else 0,
        }
        
        # Quick Win #5: Add Health Monitor data to shared state
        if hasattr(network, 'health_monitor') and network.health_monitor is not None:
            try:
                # Get neural stats if available
                neural_stats = None
                if hasattr(self.reality_sim, '_neural_metrics') and self.reality_sim._neural_metrics:
                    neural_stats = {
                        'training_loss': self.reality_sim._neural_metrics.get('training_loss'),
                        'avg_epsilon': self.reality_sim._neural_metrics.get('avg_epsilon', 0.0),
                        'organisms_tracked': self.reality_sim._neural_metrics.get('organisms_tracked', 0),
                        'training_steps': self.reality_sim._neural_metrics.get('training_steps', 0),
                    }
                
                # Get VP components from Explorer if available
                vp_components = None
                if self.controller and hasattr(self.controller, 'sentinel'):
                    try:
                        if hasattr(self.controller.sentinel, 'vp_history') and self.controller.sentinel.vp_history:
                            latest_vp = self.controller.sentinel.vp_history[-1]
                            if isinstance(latest_vp, dict) and 'component_breakdown' in latest_vp:
                                vp_components = latest_vp['component_breakdown']
                    except Exception:
                        pass
                
                # Compute health
                health_result = network.compute_ecosystem_health(
                    neural_stats=neural_stats,
                    vp_components=vp_components
                )
                
                # Add health data to state
                if health_result and health_result.get('enabled', False):
                    state['health'] = {
                        'health_score': health_result.get('health_score', 0.5),
                        'state': health_result.get('state', 'unknown'),
                        'components': {
                            'coherence': health_result.get('components', {}).get('coherence', 0.0),
                            'diversity': health_result.get('components', {}).get('diversity', 0.0),
                            'adaptability': health_result.get('components', {}).get('adaptability', 0.0),
                            'lawfulness': health_result.get('components', {}).get('lawfulness', 0.0),
                            'sustainability': health_result.get('components', {}).get('sustainability', 0.0),
                        }
                    }
                else:
                    # Health monitor disabled or unavailable
                    state['health'] = {
                        'health_score': 0.5,
                        'state': 'unknown',
                        'enabled': False
                    }
            except Exception as e:
                # Don't break if health calculation fails
                state['health'] = {
                    'health_score': 0.5,
                    'state': 'error',
                    'error': str(e)
                }
        else:
            # Health monitor not initialized
            state['health'] = {
                'health_score': 0.5,
                'state': 'not_initialized',
                'enabled': False
            }
        
        # Add meta-cognitive tuner status if available
        if hasattr(self.reality_sim, 'config_tuner') and self.reality_sim.config_tuner:
            try:
                tuner_stats = self.reality_sim.config_tuner.get_stats()
                state['meta_cognitive'] = {
                    'enabled': tuner_stats.get('enabled', False),
                    'mode': tuner_stats.get('mode', 'unknown'),
                    'total_actions': tuner_stats.get('total_actions', 0),
                    'successful_actions': tuner_stats.get('successful_actions', 0),
                    'success_rate': tuner_stats.get('success_rate', 0.0),
                }
            except Exception:
                state['meta_cognitive'] = {'enabled': False, 'mode': 'unknown'}
        else:
            state['meta_cognitive'] = {'enabled': False, 'mode': 'not_initialized'}
        
        return state
    
    def _get_explorer_state(self) -> Dict[str, Any]:
        """Get Explorer state"""
        if not self.controller:
            return {'phase': 'unknown', 'vp_calculations': 0}
        
        breath_state = self.controller.breath_engine.get_breath_state()
        
        return {
            'phase': self.controller.phase if hasattr(self.controller, 'phase') else 'unknown',
            'vp_calculations': len(self.controller.sentinel.vp_history) if hasattr(self.controller, 'sentinel') else 0,
            'sovereign_ids_count': len(self.controller.kernel.get_sovereign_ids()) if hasattr(self.controller, 'kernel') else 0,
            'breath_cycle': breath_state.get('cycle_count', 0),
            'breath_depth': breath_state.get('depth', 0),
        }
    
    def _get_djinn_kernel_state(self) -> Dict[str, Any]:
        """Get Djinn Kernel state from UTM Kernel and Akashic Ledger (tape-based)"""
        # Try UTM Kernel first (tape-based)
        if hasattr(self, 'utm_kernel') and self.utm_kernel:
            try:
                ledger = self.utm_kernel.akashic_ledger
                ledger_summary = ledger.get_ledger_summary()
                
                # Read latest VP calculation from ledger
                latest_vp = 0.0
                latest_vp_class = 'VP0'
                if ledger_summary.get('total_cells', 0) > 0:
                    # Read last few cells to find VP calculation
                    for pos in range(ledger_summary.get('next_position', 1) - 1, max(0, ledger_summary.get('next_position', 1) - 10), -1):
                        cell = ledger.read_cell(pos)
                        if cell and cell.content:
                            if 'violation_pressure' in cell.content:
                                latest_vp = cell.content.get('violation_pressure', 0.0)
                                latest_vp_class = cell.content.get('vp_classification', 'VP0')
                                break
                
                # FIX: Count actual traits from latest VP calculation in ledger
                trait_count = 0
                if ledger_summary.get('total_cells', 0) > 0:
                    for pos in range(ledger_summary.get('next_position', 1) - 1, max(0, ledger_summary.get('next_position', 1) - 10), -1):
                        cell = ledger.read_cell(pos)
                        if cell and cell.content:
                            if 'trait_payload' in cell.content:
                                trait_payload = cell.content.get('trait_payload', {})
                                trait_count = len(trait_payload) if isinstance(trait_payload, dict) else 0
                                break
                            elif 'traits' in cell.content:
                                traits = cell.content.get('traits', {})
                                trait_count = len(traits) if isinstance(traits, dict) else 0
                                break
                
                return {
                    'violation_pressure': latest_vp,
                    'vp_classification': latest_vp_class,
                    'vp_calculations': ledger_summary.get('total_cells', 0),
                    'trait_count': trait_count,  # FIX: Use actual count, not hardcoded 0
                    'tape_cells': ledger_summary.get('total_cells', 0),
                    'tape_position': ledger_summary.get('next_position', 0)
                }
            except Exception as e:
                # Fallback to VP monitor if UTM Kernel fails
                pass
        
        # Fallback to VP monitor
        if self.vp_monitor:
            vp_history = self.vp_monitor.vp_history if hasattr(self.vp_monitor, 'vp_history') else []
            if vp_history:
                recent = vp_history[-1]
                total_vp = recent.get('total_vp', 0) if isinstance(recent, dict) else (recent.vp if hasattr(recent, 'vp') else 0)
                
                # FIX: Count traits from VP history entry
                trait_count = 0
                if isinstance(recent, dict):
                    breakdown = recent.get('breakdown', {})
                    trait_count = len(breakdown) if isinstance(breakdown, dict) else 0
                
                vp_class = self.vp_monitor._classify_violation_pressure(total_vp)
                
                # Include VP diagnostic data if available
                result = {
                    'violation_pressure': total_vp,
                    'vp_classification': vp_class.value if hasattr(vp_class, 'value') else str(vp_class),
                    'vp_calculations': len(vp_history),
                    'trait_count': trait_count,  # FIX: Include trait count
                    'tape_cells': len(vp_history),
                    'tape_position': len(vp_history),
                    'vp_history': vp_history[-100:] if len(vp_history) > 100 else vp_history  # Last 100 entries
                }
                
                # Add VP diagnostics if enabled
                if self.vp_monitor.diagnostics.enabled:
                    result['vp_diagnostics'] = {'available': True, 'log_file': 'data/logs/vp_diagnostics.log'}
                
                # Add component breakdown if decomposition enabled
                if isinstance(recent, dict) and 'component_breakdown' in recent:
                    result['component_breakdown'] = recent.get('component_breakdown', {})
                
                return result
        
        # FIX: Return default with trait_count=0 explicitly (no traits = no VP calculation)
        return {'violation_pressure': 0, 'vp_classification': 'VP0', 'vp_calculations': 0, 'trait_count': 0, 'tape_cells': 0, 'tape_position': 0}
    
    def _write_unified_shared_state(self, reality_sim_state: Dict[str, Any], explorer_state: Dict[str, Any],
                                     djinn_kernel_state: Dict[str, Any], phase_sync_state: Dict[str, Any] = None,
                                     landscape_state: Dict[str, Any] = None):
        """
        Write unified shared state file that includes all three systems + PHASE SYNC DATA.
        This is the primary source of truth for the Causation Explorer and other viewers.

        NOW INCLUDES:
        - phase_sync: collapse prediction, phase proximity, exploration ratio, transition status
        - exploration_tracking: 10:1 ratio tracking, progress monitoring
        - unified_health: multi-system health metrics
        - transition_status: readiness of all three systems

        Uses snapshot-based approach: writes discrete state snapshots that the HTML can handle efficiently.
        Throttled to write at most once per second to reduce I/O overhead.
        """
        try:
            # Throttle writes to at most once per second (snapshots, not constant stream)
            current_time = time.time()
            if not hasattr(self, '_last_shared_state_write'):
                self._last_shared_state_write = 0
            
            # Only write if at least 1 second has passed since last write
            if current_time - self._last_shared_state_write < 1.0:
                return  # Skip this write, too soon
            
            self._last_shared_state_write = current_time
            
            shared_state_file = Path('data/.shared_simulation_state.json')
            shared_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Get frame count from Reality Simulator if available
            frame_count = 0
            if self.reality_sim and hasattr(self.reality_sim, 'frame_count'):
                frame_count = self.reality_sim.frame_count
            
            # Collect Reality Simulator data (if available from the actual simulator)
            reality_sim_data = {}
            if self.reality_sim and hasattr(self.reality_sim, '_collect_simulation_data'):
                try:
                    reality_sim_data = self.reality_sim._collect_simulation_data()
                    # Neural metrics are already included in _collect_simulation_data
                except Exception as e:
                    # Fallback to state we collected
                    reality_sim_data = {
                        'network': reality_sim_state,
                        'evolution': {},
                        'quantum': {},
                        'lattice': {},
                        'consciousness': {},
                        'neural': {}
                    }
                    # Add neural metrics if available
                    if self.reality_sim and hasattr(self.reality_sim, '_neural_metrics'):
                        reality_sim_data['neural'] = self.reality_sim._neural_metrics
            else:
                # Use state we collected
                reality_sim_data = {
                    'network': reality_sim_state,
                    'evolution': {},
                    'quantum': {},
                    'lattice': {},
                    'consciousness': {}
                }
            
            # 🌉 BUILD ENHANCED STATE DATA - Now with phase sync intelligence!
            # Create unified shared state with ALL three systems + PHASE SYNC
            unified_data = {
                **reality_sim_data,  # Reality Simulator data (quantum, lattice, evolution, network, consciousness)
                'explorer': explorer_state,  # Explorer data (phase, vp_calculations, breath_state, etc.)
                'djinn_kernel': djinn_kernel_state  # Djinn Kernel data (VP, tape cells, etc.)
            }

            # 🗣️ ADD LANGUAGE DATA for CRA/Illumination Engine
            try:
                network = self.reality_sim.components.get('network') if hasattr(self.reality_sim, 'components') else None
                if network and hasattr(network, 'context_memory') and network.context_memory:
                    cm = network.context_memory
                    vocab = cm.vocabulary if hasattr(cm, 'vocabulary') else None
                    # node_word_associations: Dict[organism_id, Set[words]] - organism -> words they know
                    # language_anchors: Dict[word, Set[organism_ids]] - word -> organisms using it
                    node_assocs = cm.node_word_associations if hasattr(cm, 'node_word_associations') else {}
                    language_data = {
                        'vocab_size': vocab.vocab_size if vocab else 0,
                        'word_count': len(vocab.word_to_id) if vocab and hasattr(vocab, 'word_to_id') else 0,
                        'organism_word_assignments': sum(len(words) for words in node_assocs.values()),  # Total word-organism links
                        'organisms_with_words': len(node_assocs),  # How many organisms have ANY words
                        'language_anchors': len(cm.language_anchors) if hasattr(cm, 'language_anchors') else 0,
                        'total_associations': sum(len(v) for v in cm.language_anchors.values()) if hasattr(cm, 'language_anchors') else 0
                    }
                    unified_data['language'] = language_data
            except Exception:
                pass  # Don't break if language data extraction fails

            # ✨ ADD PHASE SYNC DATA (collapse prediction, phase proximity, exploration ratio)
            if phase_sync_state:
                unified_data['phase_sync'] = phase_sync_state

                # Build exploration tracking data for CRA
                exploration_tracking = {
                    'exploration_to_precision_ratio': 10.0,  # The fundamental 500:50 = 10:1 ratio
                    'reality_sim_explorations': phase_sync_state.get('network', {}).get('organism_count', 0),
                    'explorer_explorations': phase_sync_state.get('explorer', {}).get('vp_calculations', 0),
                    'target_ratio': '500:50',
                    'current_ratio': f"{phase_sync_state.get('network', {}).get('organism_count', 0)}:{phase_sync_state.get('explorer', {}).get('vp_calculations', 0)}",
                    'ratio_maintained': abs(phase_sync_state.get('synchronization', {}).get('proximity_difference', 1.0)) < 0.1,
                    'progress_to_transition': phase_sync_state.get('network', {}).get('collapse_proximity', 0.0)
                }
                unified_data['exploration_tracking'] = exploration_tracking

                # Build unified health metrics for CRA
                network_health = 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                
                # FIXED: Include actual Health Monitor data if available (Quick Win #5)
                health_monitor_data = reality_sim_state.get('health', {})
                if health_monitor_data and health_monitor_data.get('health_score') is not None:
                    # Use actual health monitor score
                    actual_health_score = health_monitor_data.get('health_score', 0.5)
                    unified_health = {
                        'overall_health': actual_health_score,  # Use actual health monitor score
                        'reality_sim_health': actual_health_score,  # Health Monitor score
                        'health_score': actual_health_score,  # For /api/diagnostic/unified_health compatibility
                        'state': health_monitor_data.get('state', 'unknown'),
                        'components': health_monitor_data.get('components', {}),
                        'explorer_health': min(1.0, phase_sync_state.get('explorer', {}).get('genesis_proximity', 0.0) + 0.2),
                        'djinn_kernel_health': 0.82,  # Default, could calculate from VP if available
                        'integration_health': network_health,
                        'phase_alignment_health': 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                    }
                else:
                    # Fallback to phase sync-based health
                    unified_health = {
                        'overall_health': network_health * 0.9,  # Slight penalty if not fully aligned
                        'reality_sim_health': min(1.0, phase_sync_state.get('network', {}).get('collapse_proximity', 0.0) + 0.2),
                        'health_score': min(1.0, phase_sync_state.get('network', {}).get('collapse_proximity', 0.0) + 0.2),  # For compatibility
                        'explorer_health': min(1.0, phase_sync_state.get('explorer', {}).get('genesis_proximity', 0.0) + 0.2),
                        'djinn_kernel_health': 0.82,  # Default, could calculate from VP if available
                        'integration_health': network_health,
                        'phase_alignment_health': 1.0 - phase_sync_state.get('synchronization', {}).get('proximity_difference', 0.0)
                    }
                unified_data['unified_health'] = unified_health

                # Build transition status for CRA
                transition_status = {
                    'reality_sim_ready': phase_sync_state.get('network', {}).get('is_collapsed', False),
                    'explorer_ready': phase_sync_state.get('explorer', {}).get('is_ready', False),
                    'djinn_kernel_ready': djinn_kernel_state.get('violation_pressure', 1.0) < 0.25,  # VP0
                    'unified_transition_triggered': phase_sync_state.get('network', {}).get('is_collapsed', False),
                    'estimated_time_to_transition': f"~{phase_sync_state.get('network', {}).get('estimated_generations_to_collapse', float('inf')):.0f} cycles"
                }
                unified_data['transition_status'] = transition_status
            
            # Add VP monitoring configuration to shared state for CRA
            try:
                import json as json_module
                if self.config_path.exists():
                    with open(self.config_path, 'r') as f:
                        config = json_module.load(f)
                        unified_data['config'] = config  # Include full config for CRA
            except Exception as e:
                # Don't break if config read fails
                pass
            
            # Make JSON serializable
            def make_json_serializable(obj):
                """Recursively make object JSON serializable"""
                if isinstance(obj, dict):
                    # Convert tuple keys to strings (e.g., (1, 2) -> "1,2")
                    result = {}
                    for k, v in obj.items():
                        if isinstance(k, tuple):
                            key = ",".join(str(x) for x in k)
                        elif isinstance(k, (str, int, float, bool, type(None))):
                            key = k
                        else:
                            key = str(k)
                        result[key] = make_json_serializable(v)
                    return result
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                elif isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                else:
                    return str(obj)  # Convert everything else to string
            
            shared_state = {
                "frame_count": frame_count,
                "simulation_fps": 0.0,  # Could calculate if needed
                "simulation_time": round(time.time(), 6),
                "data": make_json_serializable(unified_data),
                "visualization_data": make_json_serializable(unified_data),
                "timestamp": round(time.time(), 6),
                "measurement_precision": 6
            }
            
            # Atomic write
            temp_file = shared_state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(shared_state, f, indent=2)
            
            # Atomic replace
            if os.name == 'nt':  # Windows
                if shared_state_file.exists():
                    shared_state_file.unlink()
                temp_file.rename(shared_state_file)
            else:  # Unix
                temp_file.replace(shared_state_file)
                
        except Exception as e:
            # Don't break the main loop if shared state write fails
            if not hasattr(self, '_shared_state_error_logged') or not self._shared_state_error_logged:
                print(f"[UNIFIED] [WARN] Could not write unified shared state: {e}")
                self._shared_state_error_logged = True


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Unified entry point - one command to rule them all"""
    import argparse
    
    parser = argparse.ArgumentParser(description='The Butterfly System - Unified Entry Point')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--check-only', action='store_true', help='Run pre-flight checks only')
    parser.add_argument('--max-cycles', type=int, default=0, help='Number of breath cycles to run (0 = unlimited)')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to config file (default: config.json)')

    # 🌐 Optional public URL support for cloud notebooks / rented GPUs
    # Default is OFF so local behavior never changes.
    parser.add_argument(
        '--tunnel',
        type=str,
        default='none',
        choices=['none', 'auto', 'cloudflared', 'localhostrun'],
        help=(
            'Expose the Web UI (port 5000) via a public URL. '
            "Choices: none|auto|cloudflared|localhostrun. "
            "Colab uses its built-in proxy automatically."
        )
    )
    parser.add_argument(
        '--tunnel-url-file',
        type=str,
        default='',
        help='Optional: write the current public tunnel URL to a file (e.g. tunnel_url.txt)'
    )
    parser.add_argument(
        '--tunnel-remote-port',
        type=int,
        default=80,
        help='localhost.run only: remote port to bind on localhost.run (default: 80)'
    )
    parser.add_argument(
        '--tunnel-verbose',
        action='store_true',
        help='Print full tunnel logs (useful for debugging)'
    )
    
    # 🆕 Highlander Mode - Survival of the fittest
    parser.add_argument('--highlander', action='store_true', 
                       help='Enable Highlander Protocol - perpetual survival tournament')
    parser.add_argument('--predation', action='store_true',
                       help='Enable predator/prey mechanics in Highlander mode')
    parser.add_argument('--survival-threshold', type=float, default=None,
                       help='Fitness threshold for survival (default: from config.json, typically 0.4)')
    parser.add_argument('--competition-intensity', type=float, default=None,
                       help='How many organisms battle per round (default: from config.json, typically 0.2)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable DEBUG level logging for maximum scrutiny')
    parser.add_argument('--no-cloud-setup', action='store_true',
                       help='Skip automatic cloud environment setup')
    parser.add_argument('--auto-config', action='store_true',
                       help='Automatically select best config based on detected hardware')
    
    args = parser.parse_args()

    # ========================================
    # 🌩️ AUTO CLOUD SETUP
    # ========================================
    # Automatically configures storage paths for cloud environments
    # (Vast.ai, Colab, Lambda Labs, etc.)
    if not args.no_cloud_setup:
        try:
            from cloud_setup import setup_cloud_environment, is_cloud_environment
            if is_cloud_environment():
                cloud_info = setup_cloud_environment(Path(__file__).parent, verbose=True)
                
                # Auto-select config if requested or using default
                if args.auto_config or args.config == 'config.json':
                    recommended = cloud_info.get('recommended_config', 'config.json')
                    if recommended != 'config.json' and Path(recommended).exists():
                        print(f"🎯 Auto-selected config: {recommended}")
                        args.config = recommended
        except Exception as e:
            print(f"⚠️ Cloud setup skipped: {e}")

    # Apply tunnel settings (env-var bridge) BEFORE system init.
    # Keep the tunnel implementation centralized in the web-ui startup.
    if args.tunnel and args.tunnel != 'none':
        # Start a real tunnel on ALL platforms (including Colab).
        # Colab's built-in proxy doesn't work from subprocess, so we use localhost.run/cloudflared.
        os.environ['UNIFIED_TUNNEL'] = args.tunnel
        os.environ['UNIFIED_TUNNEL_REMOTE_PORT'] = str(int(args.tunnel_remote_port))
        # If user didn't specify a URL file, pick a sane default.
        # This avoids needing to hunt the URL in scrollback after a tunnel refresh.
        url_file = (args.tunnel_url_file or '').strip()
        if not url_file:
            url_file = 'data/tunnel_url.txt'
        os.environ['UNIFIED_TUNNEL_URL_FILE'] = url_file
        if args.tunnel_verbose:
            os.environ['UNIFIED_TUNNEL_VERBOSE'] = '1'
    
    # Enable debug logging if requested
    if args.debug:
        try:
            from logging_config import setup_logging
            setup_logging(level=logging.DEBUG, debug=True, console=True)
            print("🔬 DEBUG LOGGING ENABLED - Maximum scrutiny mode!")
        except ImportError:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%H:%M:%S.%f'
            )
            print("🔬 DEBUG LOGGING ENABLED (fallback mode)")
    
    # Use specified config file
    config_file = Path(args.config)
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print(f"   Available configs: {list(Path('.').glob('config*.json'))}")
        return
    set_global_config_path(config_file.resolve())
    print(f"📋 Using config: {config_file}")
    
    if args.check_only:
        checker = PreFlightChecker()
        # For check-only, assume visualization is required (can be overridden with --no-viz)
        checker.run_all_checks(require_visualization=not args.no_viz)
        return
    
    # Build Highlander config if enabled (via command line OR config.json)
    highlander_config = None
    
    # Load config from specified config file
    config_highlander = {}
    full_config = {}
    try:
        import json
        if config_file.exists():
            with open(config_file, 'r') as f:
                full_config = json.load(f)
                config_highlander = full_config.get('highlander', {})
                print(f"🔍 [DEBUG] Loaded highlander config: enabled={config_highlander.get('enabled', 'NOT SET')}")
    except Exception as e:
        print(f"❌ [DEBUG] Config load failed: {e}")
    
    # Enable Highlander if command line flag OR config.json has enabled=True
    highlander_enabled = args.highlander or config_highlander.get('enabled', False)
    print(f"🔍 [DEBUG] args.highlander={args.highlander}, config enabled={config_highlander.get('enabled')}, highlander_enabled={highlander_enabled}")
    
    if highlander_enabled:
        # Config file values, command line can override if explicitly passed
        # Check if args were explicitly set (not just default values)
        survival_thresh = config_highlander.get('survival_threshold', 0.4)  # Default matches config.json
        competition_int = config_highlander.get('competition_intensity', 0.2)  # Default matches config.json
        
        # Only override with command line if user explicitly set them (not None)
        if args.survival_threshold is not None:
            survival_thresh = args.survival_threshold
        if args.competition_intensity is not None:
            competition_int = args.competition_intensity
            
        highlander_config = {
            'enabled': True,
            'survival_threshold': survival_thresh,
            'competition_intensity': competition_int,
            'predation_enabled': args.predation or config_highlander.get('predation_enabled', False),
            # Use config file values as defaults, override with command line if specified
            'germination_rate': config_highlander.get('germination_rate', 0.1),
            'min_population': config_highlander.get('min_population', 5),  # Default matches config.json
            'max_population': config_highlander.get('max_population', 100),
            'population_size': config_highlander.get('population_size', 9),  # Default matches config.json
            'max_battle_rounds': config_highlander.get('max_battle_rounds', 50),  # Default matches config.json
            'chaos_factor': config_highlander.get('chaos_factor', 0.0),  # Default matches config.json (disabled)
            'max_capsules': config_highlander.get('max_capsules', 100),  # Default matches config.json
            'max_genetic_samples': config_highlander.get('max_genetic_samples', 100),
            'mutation_rate': config_highlander.get('mutation_rate', 0.0),  # Default matches config.json
            'rounds_per_cycle': config_highlander.get('rounds_per_cycle', 2),  # Default matches config.json
            # CRITICAL: Pass the alliance_warfare nested config!
            'alliance_warfare': config_highlander.get('alliance_warfare', {})
        }
        print("⚔️  HIGHLANDER MODE ACTIVATED - There can be only one!")
        if highlander_config.get('predation_enabled', False):
            print("🦁 Predation enabled - the strong will hunt the weak")
    
    # Create and run unified system
    system = UnifiedSystem(
        enable_visualization=not args.no_viz, 
        max_cycles=args.max_cycles,
        highlander_config=highlander_config,
        config_path=str(config_file)
    )
    system.run()


if __name__ == "__main__":
    main()

