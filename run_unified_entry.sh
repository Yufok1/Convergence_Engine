#!/bin/bash
# Unified Entry Point Launcher for Mac/Linux
# Simple launcher for unified_entry.py

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🦋 The Butterfly System - Unified Entry Point"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ [ERROR] Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "[INFO] Using Python $PYTHON_VERSION"
echo ""

# Check if unified_entry.py exists
if [ ! -f "unified_entry.py" ]; then
    echo "❌ [ERROR] unified_entry.py not found in current directory"
    echo "Current directory: $SCRIPT_DIR"
    exit 1
fi

# Parse command line arguments
ARGS="$@"

# Run unified_entry.py with all arguments
echo "[LAUNCH] Starting unified system..."
echo ""
$PYTHON_CMD unified_entry.py $ARGS

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  System exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi

