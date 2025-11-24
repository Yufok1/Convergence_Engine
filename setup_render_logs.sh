#!/bin/bash
# Clone logs repo and copy to data/logs for Render deployment
# This runs during build to ensure logs are available at runtime

# Don't exit on error - log and continue
set +e

echo "=========================================="
echo "=== Setting up logs for Render ==="
echo "=========================================="
echo "Working directory: $(pwd)"
echo "Script location: $0"

# Determine project root (where this script is)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${SCRIPT_DIR}"
TARGET_DIR="${PROJECT_ROOT}/data/logs"

echo "Project root: $PROJECT_ROOT"
echo "Target logs directory: $TARGET_DIR"

# Clone logs repo
echo "Cloning logs from GitHub..."
TEMP_REPO="/tmp/convergence_engine_logs_$$"
rm -rf "$TEMP_REPO" 2>/dev/null || true

if git clone https://github.com/Yufok1/convergence_engine_logs.git "$TEMP_REPO" 2>&1; then
    echo "✓ Logs repo cloned successfully"
else
    echo "✗ Failed to clone logs repo"
    exit 1
fi

# Find logs directory
if [ -d "$TEMP_REPO/logs" ]; then
    LOGS_SOURCE="$TEMP_REPO/logs"
    echo "✓ Found logs directory: $LOGS_SOURCE"
elif [ -f "$TEMP_REPO/logs" ]; then
    echo "✗ 'logs' is a file, not a directory"
    ls -la "$TEMP_REPO/" || true
    exit 1
else
    echo "✗ 'logs' directory not found in repo"
    echo "Repo contents:"
    ls -la "$TEMP_REPO/" || true
    exit 1
fi

# Create target directory
echo "Creating target directory: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copy all log files
echo "Copying log files..."
if cp "$LOGS_SOURCE"/*.log "$TARGET_DIR/" 2>&1; then
    echo "✓ Log files copied successfully"
else
    echo "✗ Failed to copy log files"
    exit 1
fi

# Verify
echo "Verifying copied logs:"
ls -lh "$TARGET_DIR/" || true
LOG_COUNT=$(ls -1 "$TARGET_DIR"/*.log 2>/dev/null | wc -l || echo "0")
echo "✓ Copied $LOG_COUNT log files"

# Cleanup
rm -rf "$TEMP_REPO"

echo "=== Log setup complete ==="

