"""
Quick Readiness Check for The Convergence Engine
"""
import sys
import os
from pathlib import Path

# Setup paths
parent_path = Path(__file__).parent
explorer_path = parent_path / 'explorer'
reality_sim_path = parent_path / 'reality_simulator'
kernel_path = parent_path / 'kernel'

sys.path.insert(0, str(explorer_path))
sys.path.insert(0, str(reality_sim_path))
sys.path.insert(0, str(kernel_path))

print("=" * 60)
print("SYSTEM READINESS CHECK")
print("=" * 60)
print()

# Check core dependencies
print("Core Dependencies:")
try:
    import numpy
    print(f"  ✅ NumPy {numpy.__version__}")
except ImportError:
    print("  ❌ NumPy missing")

try:
    import networkx
    print(f"  ✅ NetworkX {networkx.__version__}")
except ImportError:
    print("  ❌ NetworkX missing")

try:
    import matplotlib
    print(f"  ✅ Matplotlib {matplotlib.__version__}")
except ImportError:
    print("  ⚠️  Matplotlib missing (optional for visualization)")

print()

# Check system imports
print("System Imports:")

# Reality Simulator
try:
    from reality_simulator.main import RealitySimulator
    print("  ✅ Reality Simulator")
except Exception as e:
    print(f"  ❌ Reality Simulator: {str(e)[:60]}")

# Djinn Kernel (direct import after adding kernel to path)
try:
    from utm_kernel_design import UTMKernel
    from violation_pressure_calculation import ViolationMonitor
    print("  ✅ Djinn Kernel")
except Exception as e:
    print(f"  ❌ Djinn Kernel: {str(e)[:60]}")

# Event Bus (direct import after adding kernel to path)
try:
    from event_driven_coordination import DjinnEventBus
    print("  ✅ Event Bus")
except Exception as e:
    print(f"  ❌ Event Bus: {str(e)[:60]}")

# Explorer
try:
    from explorer.main import BiphasicController
    print("  ✅ Explorer")
except Exception as e:
    error_msg = str(e)[:60]
    if 'win32job' in error_msg:
        print("  ⚠️  Explorer: Missing pywin32 (install: pip install pywin32)")
    else:
        print(f"  ❌ Explorer: {error_msg}")

print()

# Check files
print("Required Files:")
files = ['config.json', 'unified_entry.py']
for f in files:
    if Path(f).exists():
        print(f"  ✅ {f}")
    else:
        print(f"  ❌ {f} missing")

print()

# Check directories
print("Required Directories:")
dirs = ['explorer', 'reality_simulator', 'kernel', 'data']
for d in dirs:
    if Path(d).exists():
        print(f"  ✅ {d}/")
    else:
        print(f"  ❌ {d}/ missing")

print()
print("=" * 60)

# Final verdict
print("VERDICT:")
print("  System is READY if:")
print("    ✅ All core dependencies installed")
print("    ✅ All system imports work")
print("    ✅ All files/directories present")
print()
print("  If Explorer shows warning:")
print("    → Install: pip install pywin32")
print()
print("  Then run: python unified_entry.py --check-only")
print("=" * 60)

