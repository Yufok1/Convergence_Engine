"""
🔍 Causation Explorer Web UI - Setup Diagnostic Tool

Run this script on your other PC to check if everything is set up correctly.
It will verify all dependencies, files, and paths needed for the web UI.
"""

import sys
from pathlib import Path
import importlib

print("=" * 70)
print("🔍 Causation Explorer Web UI - Setup Diagnostic")
print("=" * 70)
print()

errors = []
warnings = []

# 1. Check Python version
print("1️⃣  Python Version")
print(f"   Python {sys.version}")
if sys.version_info < (3, 7):
    errors.append("Python 3.7+ required")
else:
    print("   ✅ Python version OK")
print()

# 2. Check Flask
print("2️⃣  Flask Dependency")
try:
    import flask
    print(f"   ✅ Flask {flask.__version__} installed")
except ImportError:
    errors.append("Flask not installed - run: pip install flask")
    print("   ❌ Flask NOT INSTALLED")
print()

# 3. Check other dependencies
print("3️⃣  Other Dependencies")
deps = ['networkx', 'numpy']
for dep in deps:
    try:
        mod = importlib.import_module(dep)
        version = getattr(mod, '__version__', 'unknown')
        print(f"   ✅ {dep} ({version})")
    except ImportError:
        warnings.append(f"{dep} not installed (may cause issues)")
        print(f"   ⚠️  {dep} NOT INSTALLED")
print()

# 4. Check project structure
print("4️⃣  Project Structure")
base_dir = Path(__file__).parent
required_files = [
    'causation_web_ui.py',
    'causation_explorer.py',
    'templates/causation_explorer.html',
]

for file_path in required_files:
    full_path = base_dir / file_path
    if full_path.exists():
        print(f"   ✅ {file_path}")
    else:
        errors.append(f"Missing file: {file_path}")
        print(f"   ❌ {file_path} NOT FOUND")
print()

# 5. Check data directories
print("5️⃣  Data Directories")
data_dirs = [
    'data/logs',
    'data',
    'templates',
]

for dir_path in data_dirs:
    full_path = base_dir / dir_path
    if full_path.exists():
        print(f"   ✅ {dir_path}/")
    else:
        # Create if it doesn't exist (non-critical)
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {dir_path}/ (created)")
        except Exception as e:
            warnings.append(f"Could not create {dir_path}: {e}")
            print(f"   ⚠️  {dir_path}/ (cannot create)")
print()

# 6. Check template file specifically
print("6️⃣  Template File")
template_path = base_dir / 'templates' / 'causation_explorer.html'
if template_path.exists():
    size = template_path.stat().st_size
    print(f"   ✅ causation_explorer.html ({size:,} bytes)")
    
    # Check if it looks like valid HTML
    try:
        content = template_path.read_text(encoding='utf-8')
        if '<html' in content.lower() and '<script' in content.lower():
            print("   ✅ Contains HTML and JavaScript")
        else:
            warnings.append("Template file may be corrupted")
            print("   ⚠️  Template content looks incomplete")
    except Exception as e:
        errors.append(f"Cannot read template file: {e}")
        print(f"   ❌ Cannot read template: {e}")
else:
    errors.append("Template file missing")
    print("   ❌ Template file NOT FOUND")
print()

# 7. Test Causation Explorer import
print("7️⃣  Causation Explorer Module")
try:
    from causation_explorer import CausationExplorer
    print("   ✅ Module imports successfully")
    
    # Try to initialize (may fail if data dirs missing, but that's OK)
    try:
        explorer = CausationExplorer()
        print("   ✅ Initializes successfully")
    except Exception as e:
        warnings.append(f"CausationExplorer init warning: {e}")
        print(f"   ⚠️  Initialization warning: {e}")
except ImportError as e:
    errors.append(f"Cannot import CausationExplorer: {e}")
    print(f"   ❌ Import failed: {e}")
except Exception as e:
    errors.append(f"Unexpected error: {e}")
    print(f"   ❌ Error: {e}")
print()

# 8. Test Flask app creation
print("8️⃣  Flask App Creation")
try:
    from flask import Flask
    template_dir = Path(__file__).parent / 'templates'
    app = Flask(__name__, template_folder=str(template_dir))
    print("   ✅ Flask app created successfully")
    print(f"   ✅ Template folder: {template_dir}")
except Exception as e:
    errors.append(f"Cannot create Flask app: {e}")
    print(f"   ❌ Failed: {e}")
print()

# 9. Check port availability (informational)
print("9️⃣  Port 5000 Status")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()
    if result == 0:
        warnings.append("Port 5000 is already in use")
        print("   ⚠️  Port 5000 is IN USE (you may need to use a different port)")
    else:
        print("   ✅ Port 5000 is available")
except Exception as e:
    print(f"   ⚠️  Cannot check port: {e}")
print()

# 10. Summary
print("=" * 70)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 70)

if errors:
    print("\n❌ ERRORS (must fix):")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
    print("\n   ⚠️  The web UI will NOT work until these are fixed!")
else:
    print("\n✅ No critical errors found!")

if warnings:
    print("\n⚠️  WARNINGS (may cause issues):")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")
else:
    print("\n✅ No warnings!")

print("\n" + "=" * 70)

if errors:
    print("\n🔧 QUICK FIX COMMANDS:")
    print()
    if any("Flask" in e for e in errors):
        print("   pip install flask")
    if any("Missing file" in e for e in errors):
        print("   # Make sure all files are copied from the main PC")
    print()
    sys.exit(1)
else:
    print("\n✅ Everything looks good! You can run:")
    print("   python causation_web_ui.py")
    print()
    sys.exit(0)

