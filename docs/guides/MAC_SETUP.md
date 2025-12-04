# 🍎 Mac Setup Guide

This guide will help you set up The Butterfly System on macOS.

## Prerequisites

1. **Python 3.8+**
   ```bash
   python3 --version
   ```
   If not installed, install via Homebrew:
   ```bash
   brew install python3
   ```

2. **Ollama** (optional, for AI agents)
   ```bash
   brew install ollama
   ```

## Installation

1. **Clone or download the repository**
   ```bash
   cd ~/Documents
   git clone <repository-url>
   cd Reality_Sim-main
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

   Note: `pywin32` is Windows-only and will be skipped automatically on Mac.

3. **Make scripts executable**
   ```bash
   chmod +x run_unified_entry.sh
   chmod +x run_reality_simulator.sh
   chmod +x setup_ollama_cloud.sh
   ```

## Running the System

### Quick Start - Unified Entry Point
```bash
./run_unified_entry.sh
```

Or directly:
```bash
python3 unified_entry.py
```

### Interactive Launcher
```bash
./run_reality_simulator.sh
```

### Causation Explorer Web UI
```bash
python3 causation_web_ui.py
```
Then open http://localhost:5000 in your browser.

## Ollama Cloud Setup (Optional)

If you want to use Ollama Cloud instead of local Ollama:

```bash
./setup_ollama_cloud.sh
```

Or manually set environment variables:
```bash
export OLLAMA_BASE_URL="https://ollama.com"
export OLLAMA_API_KEY="your-api-key-here"
export OLLAMA_TIMEOUT="60"
```

To make it permanent, add to your `~/.zshrc` (or `~/.bash_profile` if using bash):
```bash
echo 'export OLLAMA_BASE_URL="https://ollama.com"' >> ~/.zshrc
echo 'export OLLAMA_API_KEY="your-api-key-here"' >> ~/.zshrc
echo 'export OLLAMA_TIMEOUT="60"' >> ~/.zshrc
source ~/.zshrc
```

## Platform Differences

### Windows vs Mac/Linux

- **Windows**: Uses `.bat` files and `pywin32` for some Explorer features
- **Mac/Linux**: Uses `.sh` scripts, `pywin32` is skipped automatically

### File Paths

The system uses `pathlib.Path` for cross-platform path handling, so file paths should work correctly on all platforms.

### Console Encoding

The code automatically handles Windows console encoding issues. Mac/Linux terminals typically handle UTF-8 natively.

## Troubleshooting

### "Permission denied" when running scripts
```bash
chmod +x script_name.sh
```

### Python not found
Make sure `python3` is in your PATH:
```bash
which python3
```

If not found:
```bash
brew install python3
```

### Module not found errors
```bash
pip3 install -r requirements.txt
```

### Explorer won't initialize (expected on Mac)
The Explorer component uses Windows-specific features (`win32job`). On Mac/Linux, it will skip these features and run in a degraded mode. This is normal and expected.

## Need Help?

Check the main `README.md` for more detailed information about the system.

