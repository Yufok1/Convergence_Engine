#!/bin/bash
# ============================================
# 🚀 Quick Start - Runs auto-setup then simulation
# ============================================
# Usage: ./run.sh [config_file]
# ============================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run cloud setup (handles storage, git pull, etc)
if [ -f "cloud_setup.sh" ]; then
    chmod +x cloud_setup.sh
    ./cloud_setup.sh
fi

# Determine config
if [ -n "$1" ]; then
    CONFIG="$1"
elif [ -f "config_vast_epyc_2tb.json" ]; then
    # Auto-detect based on RAM
    TOTAL_RAM=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "16")
    if [ "$TOTAL_RAM" -gt 100 ]; then
        CONFIG="config_vast_epyc_2tb.json"
    elif [ "$TOTAL_RAM" -gt 40 ]; then
        CONFIG="config_colab_cpu.json"
    else
        CONFIG="config.json"
    fi
else
    CONFIG="config.json"
fi

echo ""
echo "🎮 Starting with config: $CONFIG"
echo "============================================"
echo ""

# Run simulation
python unified_entry.py --config "$CONFIG"
