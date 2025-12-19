#!/bin/bash
# ============================================
# 🚀 CONVERGENCE ENGINE - Cloud Auto-Setup
# ============================================
# Automatically configures storage for any cloud environment
# Run this ONCE before starting the simulation:
#   chmod +x cloud_setup.sh && ./cloud_setup.sh
# ============================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "🚀 Convergence Engine - Cloud Auto-Setup"
echo "============================================"

# Detect available storage options
detect_storage() {
    echo ""
    echo "📊 Detecting storage options..."
    
    # Check RAM disk (shared memory)
    if [ -d "/dev/shm" ]; then
        SHM_SIZE=$(df -BG /dev/shm 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
        echo "   /dev/shm (RAM disk): ${SHM_SIZE}GB available"
    else
        SHM_SIZE=0
    fi
    
    # Check /tmp
    TMP_SIZE=$(df -BG /tmp 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    echo "   /tmp: ${TMP_SIZE}GB available"
    
    # Check workspace
    WORKSPACE_SIZE=$(df -BG /workspace 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G' || echo "0")
    echo "   /workspace: ${WORKSPACE_SIZE}GB available"
    
    # Check root overlay
    ROOT_SIZE=$(df -BG / 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    echo "   / (overlay): ${ROOT_SIZE}GB available"
    
    # Check for large NVMe mounts (Vast.ai sometimes mounts here)
    if [ -d "/etc/hosts" ]; then
        NVME_SIZE=$(df -BG /etc/hosts 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G' || echo "0")
        if [ "$NVME_SIZE" -gt 100 ]; then
            echo "   NVMe (via /etc/hosts): ${NVME_SIZE}GB available"
        fi
    fi
}

# Select best storage location
select_storage() {
    echo ""
    echo "🎯 Selecting optimal storage..."
    
    # Priority: RAM disk > Large NVMe > /tmp > local
    if [ "$SHM_SIZE" -gt 50 ]; then
        DATA_PATH="/dev/shm/convergence_data"
        STORAGE_TYPE="RAM disk (fastest)"
    elif [ "$NVME_SIZE" -gt 500 ]; then
        DATA_PATH="/mnt/nvme_data/convergence_data"
        STORAGE_TYPE="NVMe"
    elif [ "$TMP_SIZE" -gt 20 ]; then
        DATA_PATH="/tmp/convergence_data"
        STORAGE_TYPE="/tmp"
    else
        DATA_PATH="./data"
        STORAGE_TYPE="local (warning: may fill up)"
    fi
    
    echo "   Selected: $DATA_PATH ($STORAGE_TYPE)"
}

# Setup data directory
setup_data() {
    echo ""
    echo "📁 Setting up data directory..."
    
    # Create target directory
    mkdir -p "$DATA_PATH"/{logs,checkpoints,neural_checkpoints,kernel,profiles,knowledge,decision_logs,causation_explorer}
    
    # Remove existing data dir and symlink
    if [ -L "./data" ]; then
        rm -f ./data
        echo "   Removed existing symlink"
    elif [ -d "./data" ]; then
        # Backup any existing data
        if [ "$(ls -A ./data 2>/dev/null)" ]; then
            echo "   Moving existing data to $DATA_PATH..."
            cp -r ./data/* "$DATA_PATH/" 2>/dev/null || true
        fi
        rm -rf ./data
    fi
    
    # Create symlink
    ln -s "$DATA_PATH" ./data
    echo "   Created symlink: ./data -> $DATA_PATH"
    
    # Verify
    echo "   Verifying..."
    ls -la ./data > /dev/null
    echo "   ✅ Data directory ready"
}

# Detect config to use
detect_config() {
    echo ""
    echo "⚙️ Detecting optimal config..."
    
    # Get total RAM in GB
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    
    # Get CPU threads
    CPU_THREADS=$(nproc)
    
    echo "   RAM: ${TOTAL_RAM}GB"
    echo "   CPU threads: ${CPU_THREADS}"
    
    # Select config based on resources
    if [ "$TOTAL_RAM" -gt 1500 ]; then
        RECOMMENDED_CONFIG="config_vast_epyc_2tb.json"
        echo "   Recommended: $RECOMMENDED_CONFIG (2TB+ RAM detected)"
    elif [ "$TOTAL_RAM" -gt 100 ]; then
        RECOMMENDED_CONFIG="config_vast_epyc_2tb.json"
        echo "   Recommended: $RECOMMENDED_CONFIG (100GB+ RAM)"
    elif [ "$TOTAL_RAM" -gt 40 ]; then
        RECOMMENDED_CONFIG="config_colab_cpu.json"
        echo "   Recommended: $RECOMMENDED_CONFIG (40-100GB RAM)"
    else
        RECOMMENDED_CONFIG="config.json"
        echo "   Recommended: $RECOMMENDED_CONFIG (standard)"
    fi
    
    # Check if GPU available
    if command -v nvidia-smi &> /dev/null; then
        GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || echo "0")
        if [ "$GPU_MEM" -gt 20000 ]; then
            echo "   GPU: ${GPU_MEM}MB VRAM detected"
            echo "   Note: Large populations work better on CPU (RAM > VRAM)"
        fi
    fi
}

# Clear caches to free space
clear_caches() {
    echo ""
    echo "🧹 Clearing caches..."
    
    # Clear pip cache
    rm -rf ~/.cache/pip/* 2>/dev/null && echo "   Cleared pip cache" || true
    
    # Clear old logs
    rm -rf /var/log/*.log 2>/dev/null && echo "   Cleared system logs" || true
    
    # Clear tmp
    rm -rf /tmp/chamber_* /tmp/tmp* 2>/dev/null && echo "   Cleared /tmp" || true
}

# Git pull latest
update_code() {
    echo ""
    echo "📥 Checking for updates..."
    
    if [ -d ".git" ]; then
        git pull --ff-only 2>/dev/null && echo "   ✅ Updated to latest" || echo "   ⚠️ Could not update (may have local changes)"
    else
        echo "   Not a git repo, skipping update"
    fi
}

# Main
main() {
    detect_storage
    select_storage
    setup_data
    detect_config
    clear_caches
    update_code
    
    echo ""
    echo "============================================"
    echo "✅ Setup complete!"
    echo "============================================"
    echo ""
    echo "To run:"
    echo "  python unified_entry.py --config $RECOMMENDED_CONFIG"
    echo ""
    echo "Or use the quick-start:"
    echo "  ./run.sh"
    echo ""
}

main "$@"
