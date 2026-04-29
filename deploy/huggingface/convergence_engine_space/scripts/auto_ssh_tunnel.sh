#!/bin/bash
set -uo pipefail

echo "SSH TUNNEL AUTO-RUNNER"
echo "Command: ssh -R 80:localhost:5000 nokey@localhost.run"
echo "Start the engine when ready; this tunnel forwards to localhost:5000."
echo "Look below for the localhost.run public URL."
echo

while true; do
  echo "[$(date -Is)] starting localhost.run reverse tunnel"
  ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/data/known_hosts \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -R 80:localhost:5000 \
    nokey@localhost.run
  code=$?
  echo "[$(date -Is)] ssh tunnel exited with code ${code}; restarting in 5s"
  sleep 5
done
