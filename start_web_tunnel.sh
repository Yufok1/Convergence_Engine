#!/bin/bash
# ONE COMMAND TO RULE THEM ALL
# Run this from the HF Space terminal: bash /data/work/Convergence_Engine/start_web_tunnel.sh

set -e

VENV_DIR="/home/user/.venvs/convergence-engine"
WORK_DIR="/data/work/Convergence_Engine"
PORT=5000

echo "═══════════════════════════════════════════════════"
echo "  🚀 Convergence Engine Full Stack Launcher"
echo "═══════════════════════════════════════════════════"

# Step 1: Kill anything on port 5000
echo ""
echo "[1/6] Clearing port $PORT..."
fuser -k $PORT/tcp 2>/dev/null || true
sleep 1

# Step 2: Create venv if it doesn't exist
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[2/6] Creating virtual environment..."
    python -m venv "$VENV_DIR"
else
    echo "[2/6] Virtual environment exists ✓"
fi

# Step 3: Activate and install deps
echo "[3/6] Activating venv and installing dependencies..."
. "$VENV_DIR/bin/activate"
cd "$WORK_DIR"

# Only install if flask isn't importable (skip on repeat runs)
python -c "import flask" 2>/dev/null || pip install -q -r requirements.txt 2>&1 | tail -5

# Make sure data dir and config exist
mkdir -p data
[ -f data/config.json ] || cp config.json data/config.json 2>/dev/null || true

# Step 4: Start unified_entry.py (the world) in background
echo "[4/6] Starting unified_entry.py (the world)..."
python unified_entry.py --config config.json --no-viz --debug > /tmp/unified_entry.log 2>&1 &
UNIFIED_PID=$!
sleep 3
echo "    ✓ World running (PID $UNIFIED_PID)"

# Step 5: Start live_dashboard.py in background
echo "[5/6] Starting live_dashboard.py (TUI dashboard)..."
python live_dashboard.py > /tmp/live_dashboard.log 2>&1 &
DASH_PID=$!
sleep 2
echo "    ✓ Dashboard running (PID $DASH_PID)"

# Step 6: Start web UI in background
echo "[6/6] Starting causation_web_ui.py on port $PORT..."
python causation_web_ui.py > /tmp/web_ui.log 2>&1 &
WEB_PID=$!
sleep 3

# Verify web UI started
BYTES=$(curl -s http://localhost:$PORT | wc -c)
if [ "$BYTES" -lt 100 ]; then
    echo "❌ Web UI failed to start. Check /tmp/web_ui.log"
    echo "--- Last 10 lines of /tmp/web_ui.log ---"
    tail -10 /tmp/web_ui.log
    exit 1
fi
echo "    ✓ Web UI running ($BYTES bytes served)"

# Open tunnel
echo ""
echo "═══════════════════════════════════════════════════"
echo "  📋 COPY THE https://xxxxx.lhr.life LINK BELOW"
echo "  📋 PASTE IT IN YOUR BROWSER"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  To view logs:"
echo "    tail -f /tmp/unified_entry.log"
echo "    tail -f /tmp/live_dashboard.log"
echo "    tail -f /tmp/web_ui.log"
echo ""
echo "  To stop everything:"
echo "    kill $UNIFIED_PID $DASH_PID $WEB_PID"
echo ""
ssh -o StrictHostKeyChecking=accept-new -R 80:localhost:$PORT nokey@localhost.run
