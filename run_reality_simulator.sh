#!/bin/bash
# Reality Simulator Interactive Launcher for Mac/Linux
# Cross-platform version of run_reality_simulator.bat

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "[ROCKET] REALITY SIMULATOR LAUNCHER"
echo "========================================"
echo "[CONFIGURABLE] Interactive Parameter Selection"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "[INFO] Using Python $PYTHON_VERSION"
echo ""

# Check setup first
if [ -f "check_setup.py" ]; then
    $PYTHON_CMD check_setup.py
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Setup issues detected. Please fix them first."
        read -p "Press Enter to continue anyway..."
    fi
fi

echo ""
echo "Press Enter to continue to main menu..."
read

# Global variables for configuration
export AI_MODEL=""
export QUANTUM_STATES=""
export LATTICE_PARTICLES=""
export POPULATION_SIZE=""
export MAX_ORGANISMS=""
export MAX_CONNECTIONS=""
export TARGET_FPS=""
export SIMULATION_MODE=""
export MAX_FRAMES=""
export TEXT_INTERFACE=""
export FRAME_DELAY=""

# Function to get available Ollama models
get_available_models() {
    echo "[SEARCH] Querying available Ollama models..."
    echo ""
    
    if command -v ollama &> /dev/null; then
        # Query Ollama for available models
        MODELS_JSON=$($PYTHON_CMD -c "
import subprocess
import json
try:
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            models = [line.split()[0] for line in lines[1:] if line.strip()]
            print(json.dumps(models))
        else:
            print('[]')
    else:
        print('[]')
except:
    print('[]')
" 2>/dev/null || echo '[]')
    else
        MODELS_JSON='[]'
    fi
    
    if [ "$MODELS_JSON" = "[]" ] || [ -z "$MODELS_JSON" ]; then
        echo "[WARNING] Could not query Ollama models. Using defaults."
        MODELS_JSON='["gemma3:4b","gemma3:12b","granite4:350m"]'
    fi
    
    export MODELS_JSON
}

# Main menu function
show_main_menu() {
    clear
    echo "========================================"
    echo "[ROCKET] REALITY SIMULATOR LAUNCHER"
    echo "========================================"
    echo "[CONFIGURABLE] Interactive Parameter Selection"
    echo ""
    echo "Current Configuration:"
    [ -z "$AI_MODEL" ] && echo "AI Model: [NOT SET]" || echo "AI Model: $AI_MODEL"
    [ -z "$QUANTUM_STATES" ] && echo "Quantum States: [NOT SET]" || echo "Quantum States: $QUANTUM_STATES"
    [ -z "$LATTICE_PARTICLES" ] && echo "Lattice Particles: [NOT SET]" || echo "Lattice Particles: $LATTICE_PARTICLES"
    [ -z "$POPULATION_SIZE" ] && echo "Population Size: [NOT SET]" || echo "Population Size: $POPULATION_SIZE"
    [ -z "$MAX_ORGANISMS" ] && echo "Max Organisms: [NOT SET]" || echo "Max Organisms: $MAX_ORGANISMS"
    [ -z "$TARGET_FPS" ] && echo "FPS Target: [NOT SET]" || echo "FPS Target: $TARGET_FPS"
    [ -z "$SIMULATION_MODE" ] && echo "Simulation Mode: [NOT SET]" || echo "Simulation Mode: $SIMULATION_MODE"
    echo ""
    echo "Choose an option:"
    echo ""
    echo "[0] Check System Setup"
    echo "[1] Quick Start (Current Config)"
    echo "[2] Interactive Configuration"
    echo "[3] God Mode (Full Control)"
    echo "[4] Scientist Mode (Experiments)"
    echo "[5] Participant Mode (Immersion)"
    echo "[6] Chat Mode (DISABLED - AI Agents Removed)"
    echo "[7] Run Tests"
    echo "[8] Run Benchmarks"
    echo "[9] Feedback Status"
    echo "[10] Exit"
    echo ""
}

# Generate temp config
generate_temp_config() {
    cat > temp_config.json <<EOF
{
  "simulation": {
    "target_fps": ${TARGET_FPS:-30},
    "time_resolution_ms": 1.0
  },
  "quantum": {
    "initial_states": ${QUANTUM_STATES:-50}
  },
  "lattice": {
    "particles": ${LATTICE_PARTICLES:-5000}
  },
  "evolution": {
    "population_size": ${POPULATION_SIZE:-500}
  },
  "network": {
    "max_organisms": ${MAX_ORGANISMS:-2000},
    "max_connections": ${MAX_CONNECTIONS:-10000}
  },
  "agency": {
    "ai_model": "${AI_MODEL:-gemma3:4b}"
  },
  "rendering": {
    "enable_visualizations": true
  },
  "feedback": {
    "enabled": true,
    "interval_frames": 10,
    "hysteresis_checks": 3,
    "rate_limit_frames": 30,
    "knobs": {
      "mutation_rate": {"min": 0.001, "max": 0.05, "step": 0.001},
      "new_edge_rate": {"min": 0.0, "max": 1.5, "step": 0.05},
      "clustering_bias": {"min": 0.0, "max": 1.2, "step": 0.05},
      "quantum_pruning": {"min": 0.0, "max": 1.0, "step": 0.05}
    }
  }
}
EOF
    echo "[SUCCESS] Configuration ready."
}

# Main menu loop
while true; do
    show_main_menu
    read -p "Enter choice (0-10): " choice
    
    case "$choice" in
        0)
            echo ""
            echo "[SEARCH] Running system setup check..."
            echo ""
            if [ -f "check_setup.py" ]; then
                $PYTHON_CMD check_setup.py
            else
                echo "[INFO] check_setup.py not found, skipping..."
            fi
            echo ""
            read -p "Press Enter to return to main menu..."
            ;;
        1)
            echo ""
            echo "[TARGET] Starting Reality Simulator with Custom Configuration..."
            echo ""
            echo "Configuration Summary:"
            echo "AI Model: ${AI_MODEL:-[DEFAULT]} (agents disabled)"
            echo "Quantum States: ${QUANTUM_STATES:-[DEFAULT]} / Particles: ${LATTICE_PARTICLES:-[DEFAULT]}"
            echo "Population: ${POPULATION_SIZE:-[DEFAULT]} / Organisms: ${MAX_ORGANISMS:-[DEFAULT]}"
            echo "FPS Target: ${TARGET_FPS:-[DEFAULT]} / Mode: ${SIMULATION_MODE:-[DEFAULT]}"
            echo ""
            
            generate_temp_config
            
            CMD_ARGS="--mode ${SIMULATION_MODE:-observer} --config $SCRIPT_DIR/temp_config.json"
            [ -n "$FRAME_DELAY" ] && [ "$FRAME_DELAY" != "0.0" ] && CMD_ARGS="$CMD_ARGS --delay $FRAME_DELAY"
            [ -n "$MAX_FRAMES" ] && CMD_ARGS="$CMD_ARGS --frames $MAX_FRAMES"
            [ "$TEXT_INTERFACE" = "disabled" ] && CMD_ARGS="$CMD_ARGS --no-text"
            
            echo "[LAUNCH] Command: $PYTHON_CMD -m reality_simulator.main $CMD_ARGS"
            echo ""
            
            $PYTHON_CMD -m reality_simulator.main $CMD_ARGS || true
            
            [ -f "temp_config.json" ] && rm -f temp_config.json
            echo ""
            read -p "Press Enter to return to main menu..."
            ;;
        3)
            echo ""
            echo "[GOD] Starting Reality Simulator in God Mode..."
            echo "Full control over the simulation universe."
            echo ""
            generate_temp_config
            $PYTHON_CMD -m reality_simulator.main --mode god --config "$SCRIPT_DIR/temp_config.json" || true
            [ -f "temp_config.json" ] && rm -f temp_config.json
            echo ""
            read -p "Press Enter to return to main menu..."
            ;;
        10)
            echo ""
            echo "[WAVE] Goodbye! Thanks for exploring simulated reality."
            echo ""
            exit 0
            ;;
        *)
            echo "[INFO] Feature $choice not yet fully implemented in shell script."
            echo "For full interactive configuration, use the Python script directly:"
            echo "  $PYTHON_CMD unified_entry.py"
            echo ""
            read -p "Press Enter to continue..."
            ;;
    esac
done

