# 🌐 Cross-Platform Setup Guide

This guide helps you set up The Butterfly System on **Windows**, **Mac**, or **Linux**.

## Quick Start

### Windows
```cmd
run_reality_simulator.bat
```
or
```cmd
python unified_entry.py
```

### Mac / Linux
```bash
chmod +x run_unified_entry.sh run_reality_simulator.sh setup_ollama_cloud.sh
./run_unified_entry.sh
```
or
```bash
python3 unified_entry.py
```

## Scripts Available

### Windows (.bat files)
- `run_reality_simulator.bat` - Interactive launcher with full menu
- `run_quantum_tests.bat` - Run quantum subsystem tests
- `run_quantum_demo.bat` - Run quantum demo

### Mac/Linux (.sh files)
- `run_unified_entry.sh` - Simple launcher for unified_entry.py
- `run_reality_simulator.sh` - Interactive launcher (basic version)
- `setup_ollama_cloud.sh` - Setup Ollama Cloud environment variables

## Platform-Specific Notes

### Windows
- Uses `pywin32` for Explorer process isolation (optional)
- Uses `.bat` batch files
- PowerShell scripts available (`.ps1`)

### Mac/Linux
- `pywin32` is skipped automatically (not needed)
- Uses `.sh` shell scripts
- Explorer runs in degraded mode (no Windows job objects)
- File paths handled via `pathlib.Path` (cross-platform)

## Installation

### Prerequisites

**All Platforms:**
```bash
pip install -r requirements.txt
```

**Windows Only (Optional):**
```bash
pip install pywin32
```

**Mac/Linux:**
- Python 3.8+ (usually `python3`)
- Shell: bash or zsh
- No Windows-specific dependencies needed

## Running the System

### Causation Explorer Web UI

**Windows:**
```cmd
python causation_web_ui.py
```

**Mac/Linux:**
```bash
python3 causation_web_ui.py
```

Then open http://localhost:5000 in your browser.

### Unified Entry Point

**Windows:**
```cmd
python unified_entry.py
```

**Mac/Linux:**
```bash
python3 unified_entry.py
```

or use the launcher:
```bash
./run_unified_entry.sh
```

## Ollama Cloud Setup

### Windows (PowerShell)
```powershell
.\SETUP_OLLAMA_CLOUD.ps1
```

### Mac/Linux
```bash
./setup_ollama_cloud.sh
```

Or manually:
```bash
export OLLAMA_BASE_URL="https://ollama.com"
export OLLAMA_API_KEY="your-api-key"
export OLLAMA_TIMEOUT="60"
```

## Platform Compatibility

✅ **Fully Compatible:**
- Python code (uses `pathlib.Path` for cross-platform paths)
- Web UI (Flask)
- Core simulation systems
- Causation Explorer

⚠️ **Platform-Specific Features:**
- Explorer process isolation (Windows only via `pywin32`)
- Sandbox resource limits (Windows: strict, Mac/Linux: monitored via psutil)

## Troubleshooting

### Mac/Linux: "Permission denied" on scripts
```bash
chmod +x script_name.sh
```

### Mac/Linux: Python not found
Use `python3` instead of `python`:
```bash
python3 unified_entry.py
```

### Windows: pywin32 not installed
Explorer will run in degraded mode. To enable full features:
```cmd
pip install pywin32
```

### Import errors
Make sure you're in the project root directory:
```bash
cd Reality_Sim-main
```

## Differences Summary

| Feature | Windows | Mac/Linux |
|---------|---------|-----------|
| Python command | `python` | `python3` |
| Script extension | `.bat`, `.ps1` | `.sh` |
| Process isolation | `pywin32` (optional) | `psutil` (always) |
| File paths | Handled automatically via `pathlib` | Handled automatically via `pathlib` |
| Console encoding | Auto-fixed in code | Native UTF-8 |

## Need Help?

- See `MAC_SETUP.md` for Mac-specific details
- See `README.md` for general documentation
- Check `TROUBLESHOOTING.md` for common issues

