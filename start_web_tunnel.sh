#!/bin/bash
# ONE COMMAND TO RULE THEM ALL
# Run this from the HF Space terminal: bash /data/work/Convergence_Engine/start_web_tunnel.sh

set -e

VENV_DIR="/home/user/.venvs/convergence-engine"
WORK_DIR="/data/work/Convergence_Engine"
PORT=5000

echo "═══════════════════════════════════════════════════"
echo "  🚀 Convergence Engine Web UI + Tunnel Launcher"
echo "═══════════════════════════════════════════════════"

# Step 1: Kill anything on port 5000
echo ""
echo "[1/5] Clearing port $PORT..."
fuser -k $PORT/tcp 2>/dev/null || true
sleep 1

# Step 2: Create venv if it doesn't exist
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[2/5] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[2/5] Virtual environment exists ✓"
fi

# Step 3: Activate and install deps
echo "[3/5] Activating venv and installing dependencies..."
. "$VENV_DIR/bin/activate"
cd "$WORK_DIR"
pip install -q -r requirements.txt 2>&1 | tail -5

# Step 4: Start web UI in background
echo "[4/5] Starting web UI on port $PORT..."
python causation_web_ui.py &
WEB_PID=$!
sleep 3

# Verify it started
BYTES=$(curl -s http://localhost:$PORT | wc -c)
if [ "$BYTES" -lt 100 ]; then
    echo "❌ Web UI failed to start. Check errors above."
    kill $WEB_PID 2>/dev/null
    exit 1
fi
echo "    ✓ Web UI running ($BYTES bytes served)"

# Step 5: Open tunnel
echo "[5/5] Opening tunnel..."
echo ""
echo "═══════════════════════════════════════════════════"
echo "  📋 COPY THE https://xxxxx.lhr.life LINK BELOW"
echo "  📋 PASTE IT IN YOUR BROWSER"
echo "═══════════════════════════════════════════════════"
echo ""
ssh -o StrictHostKeyChecking=accept-new -R 80:localhost:$PORT nokey@localhost.run
