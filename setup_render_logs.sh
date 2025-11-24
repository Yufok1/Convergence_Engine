#!/bin/bash
# Clone logs repo and copy to data/logs for Render deployment

echo "Cloning logs from GitHub..."
git clone https://github.com/Yufok1/convergence_engine_logs.git /tmp/logs_repo 2>/dev/null || true

if [ -d "/tmp/logs_repo/logs" ]; then
    echo "Copying logs to data/logs..."
    mkdir -p data/logs
    cp -r /tmp/logs_repo/logs/* data/logs/ 2>/dev/null || true
    echo "Logs copied successfully"
    ls -la data/logs/
else
    echo "Warning: Logs directory not found in repo"
fi

