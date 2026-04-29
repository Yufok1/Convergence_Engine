#!/bin/bash
set -uo pipefail

echo "LIVE DASHBOARD AUTO-RUNNER"
echo "Waiting for /data/Convergence_Engine/live_dashboard.py"
echo "This starts automatically after you prepare the repo."
echo

while true; do
  if [ -f /data/Convergence_Engine/live_dashboard.py ]; then
    cd /data/Convergence_Engine || exit 1
    echo "[$(date -Is)] starting: python live_dashboard.py"
    python live_dashboard.py
    code=$?
    echo "[$(date -Is)] live_dashboard.py exited with code ${code}; restarting in 5s"
  else
    echo "[$(date -Is)] repo not ready yet; waiting for /data/Convergence_Engine/live_dashboard.py"
  fi
  sleep 5
done
