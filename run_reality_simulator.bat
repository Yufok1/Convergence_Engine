@echo off
REM Reality Simulator Interactive Launcher
REM Dynamic configuration and Ollama model selection for Reality Simulator

echo ========================================
echo [ROCKET] REALITY SIMULATOR LAUNCHER
echo ========================================
echo [CONFIGURABLE] Interactive Parameter Selection
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Change to simulator directory
cd /d "%~dp0"

REM Global variables for configuration (initialize empty - user must set all values)
set AI_MODEL=
set QUANTUM_STATES=
set LATTICE_PARTICLES=
set POPULATION_SIZE=
set MAX_ORGANISMS=
set MAX_CONNECTIONS=
set TARGET_FPS=
set SIMULATION_MODE=
set MAX_FRAMES=
set TEXT_INTERFACE=
set FRAME_DELAY=

REM Check setup first
python check_setup.py
if errorlevel 1 (
    echo.
    echo [ERROR] Setup issues detected. Please fix them first.
    pause
    exit /b 1
)

REM Brief pause to let user see setup results
echo.
echo Press any key to continue to main menu...
pause >nul

REM Main menu (inline)
:main_menu_inline
cls
echo ========================================
echo [ROCKET] REALITY SIMULATOR LAUNCHER
echo ========================================
echo [CONFIGURABLE] Interactive Parameter Selection
echo.
echo Current Configuration:
if "%AI_MODEL%"=="" (echo AI Model: [NOT SET]) else (echo AI Model: %AI_MODEL%)
if "%QUANTUM_STATES%"=="" (echo Quantum States: [NOT SET]) else (echo Quantum States: %QUANTUM_STATES%)
if "%LATTICE_PARTICLES%"=="" (echo Lattice Particles: [NOT SET]) else (echo Lattice Particles: %LATTICE_PARTICLES%)
if "%POPULATION_SIZE%"=="" (echo Population Size: [NOT SET]) else (echo Population Size: %POPULATION_SIZE%)
if "%MAX_ORGANISMS%"=="" (echo Max Organisms: [NOT SET]) else (echo Max Organisms: %MAX_ORGANISMS%)
if "%TARGET_FPS%"=="" (echo FPS Target: [NOT SET]) else (echo FPS Target: %TARGET_FPS%)
if "%SIMULATION_MODE%"=="" (echo Simulation Mode: [NOT SET]) else (echo Simulation Mode: %SIMULATION_MODE%)
echo.
echo Choose an option:
echo.
echo [0] Check System Setup
echo [1] Quick Start (Current Config)
echo [2] Interactive Configuration
echo [3] God Mode (Full Control)
echo [4] Scientist Mode (Experiments)
echo [5] Participant Mode (Immersion)
echo [6] Chat Mode (DISABLED - AI Agents Removed)
echo [7] Run Tests
echo [8] Run Benchmarks
echo [9] Feedback Status
echo [10] Exit
echo.
set /p choice="Enter choice (0-10): "

REM Validate choice input
if "%choice%"=="" (
    echo Invalid choice. Please enter a number between 0-10.
    timeout /t 2 >nul
    goto main_menu_inline_inline_inline
)

if "%choice%"=="0" goto check_setup
if "%choice%"=="1" goto quick_start
if "%choice%"=="2" goto interactive_config
if "%choice%"=="3" goto god_mode
if "%choice%"=="4" goto scientist_mode
if "%choice%"=="5" goto participant_mode
if "%choice%"=="6" goto chat_mode
if "%choice%"=="7" goto run_tests
if "%choice%"=="8" goto run_benchmarks
if "%choice%"=="9" goto feedback_status
if "%choice%"=="10" goto exit_launcher

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto main_menu_inline_inline

REM Function to query available Ollama models
:get_available_models
echo [SEARCH] Querying available Ollama models...
echo.

REM Create a temporary Python script to parse ollama list output
echo import subprocess, json > temp_models.py
echo result = subprocess.run(['ollama', 'list'], capture_output=True, text=True) >> temp_models.py
echo if result.returncode == 0: >> temp_models.py
echo     lines = result.stdout.strip().split('\n') >> temp_models.py
echo     if len(lines) ^> 1: >> temp_models.py
echo         models = [line.split()[0] for line in lines[1:] if line.strip()] >> temp_models.py
echo         print(json.dumps(models)) >> temp_models.py
echo     else: >> temp_models.py
echo         print('[]') >> temp_models.py
echo else: >> temp_models.py
echo     print('[]') >> temp_models.py

echo Running model query...
python temp_models.py > available_models.json 2>nul
if exist temp_models.py del temp_models.py

REM Read the models from JSON
set MODELS_JSON=[]
if exist available_models.json (
    for /f "delims=" %%i in (available_models.json) do set MODELS_JSON=%%i
    del available_models.json
) else (
    echo [WARNING] Could not query Ollama models. Using defaults.
    set MODELS_JSON=["gemma3:4b","gemma3:12b","granite4:350m"]
)
goto :eof

:check_setup
echo.
echo [SEARCH] Running system setup check...
echo.
python check_setup.py
echo.
echo Press any key to return to main menu...
pause >nul
goto main_menu_inline

:interactive_config
cls
echo ========================================
echo [SETTINGS] INTERACTIVE CONFIGURATION
echo ========================================
echo.

echo Select what to configure:
echo.
echo [1] Ollama AI Model (Agents Disabled)
echo [2] Simulation Parameters
echo [3] Performance Settings
echo [4] View Current Configuration
echo [5] Reset to Defaults
echo [6] Back to Main Menu
echo.
set /p config_choice="Enter choice (1-6): "

if "%config_choice%"=="1" goto configure_models
if "%config_choice%"=="2" goto configure_simulation
if "%config_choice%"=="3" goto configure_performance
if "%config_choice%"=="4" goto view_config
if "%config_choice%"=="5" goto reset_defaults
if "%config_choice%"=="6" goto main_menu_inline

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto interactive_config

:configure_models
cls
echo ========================================
echo [MODEL] OLLAMA MODEL SELECTION
echo ========================================
echo.
echo [AI MODEL] Set for config compatibility (agents are currently disabled).
echo The simulation runs without active agent/chat/vision features.
echo This setting is stored but not actively used in the current build.
echo.

call :get_available_models

echo Available Ollama models:
echo.

REM Parse and display models with numbers
echo import json > display_models.py
echo models = json.loads('%MODELS_JSON%') >> display_models.py
echo if models: >> display_models.py
echo     vision_capable = ['gemma3', 'granite3.2-vision', 'qwen3-vl'] >> display_models.py
echo     for i, model in enumerate(models, 1): >> display_models.py
echo         vision_indicator = ' [VISION]' if any(vc in model for vc in vision_capable) else '' >> display_models.py
echo         print(f'[{i}] {model}{vision_indicator}') >> display_models.py
echo else: >> display_models.py
echo     print('No models found. Please install Ollama models first.') >> display_models.py

python display_models.py > models_list.txt
type models_list.txt
del display_models.py
del models_list.txt

echo.
echo [0] Keep current (%AI_MODEL%)
echo.

set /p ai_choice="Select AI model number: "
if "%ai_choice%"=="0" (
    echo Keeping current AI model: %AI_MODEL%
) else (
    REM Get the selected model name using embedded Python with environment variables
    set MODELS_JSON=%MODELS_JSON%
    set AI_CHOICE=%ai_choice%
    set AI_MODEL_CURRENT=%AI_MODEL%

    python -c "import ast, os; models_json = os.environ.get('MODELS_JSON', '[]'); ai_choice = os.environ.get('AI_CHOICE', '0'); ai_model = os.environ.get('AI_MODEL_CURRENT', 'gemma3:4b'); models = ast.literal_eval(models_json); choice = int(ai_choice); print(models[choice - 1] if 1 <= choice <= len(models) else ai_model)" > model_output.txt 2>nul

    if exist model_output.txt (
        set /p AI_MODEL=<model_output.txt
        del model_output.txt 2>nul
    )

    REM Clean up environment variables
    set MODELS_JSON=
    set AI_CHOICE=
    set AI_MODEL_CURRENT=
)

echo.
echo [SUCCESS] AI model configured: %AI_MODEL% (stored for compatibility only)
echo.
pause
goto interactive_config

:configure_simulation
cls
echo ========================================
echo [PARAMS] SIMULATION PARAMETERS
echo ========================================
echo.
echo Current values:
echo Quantum States: %QUANTUM_STATES%
echo Lattice Particles: %LATTICE_PARTICLES%
echo Population Size: %POPULATION_SIZE%
echo Max Organisms: %MAX_ORGANISMS%
echo Max Connections: %MAX_CONNECTIONS%
echo.
echo Choose parameter to modify:
echo.
echo [1] Quantum States (%QUANTUM_STATES%)
echo    Higher values = more complex quantum behavior
echo    Lower values = simpler/faster simulation
echo.
echo [2] Lattice Particles (%LATTICE_PARTICLES%)
echo    Higher values = more detailed particle interactions
echo    Lower values = faster performance
echo.
echo [3] Population Size (%POPULATION_SIZE%)
echo    Higher values = more genetic diversity
echo    Lower values = faster evolution cycles
echo.
echo [4] Max Organisms (%MAX_ORGANISMS%)
echo    Higher values = larger ecosystems possible
echo    Lower values = more focused evolution
echo.
echo [5] Max Connections (%MAX_CONNECTIONS%)
echo    Higher values = more complex network topologies
echo    Lower values = simpler topologies
echo.
echo [6] Back to Configuration Menu
echo.
set /p sim_choice="Enter parameter to change (1-6): "

if "%sim_choice%"=="1" (
    echo.
    echo [QUANTUM STATES] Controls the initial number of quantum superposition states.
    echo Higher values create more complex quantum behavior and richer particle interactions.
    echo Lower values result in simpler, faster simulations.
    echo Recommended: 20-200
    echo.
    set /p QUANTUM_STATES="Enter quantum states [20-200]: "
) else if "%sim_choice%"=="2" (
    echo.
    echo [LATTICE PARTICLES] Total number of particles in the quantum lattice substrate.
    echo Higher values create more detailed particle physics and interactions.
    echo Lower values improve performance but reduce simulation fidelity.
    echo Recommended: 1000-10000
    echo.
    set /p LATTICE_PARTICLES="Enter lattice particles [1000-10000]: "
) else if "%sim_choice%"=="3" (
    echo.
    echo [POPULATION SIZE] Initial number of organisms in the evolutionary pool.
    echo Higher values increase genetic diversity and evolutionary possibilities.
    echo Lower values speed up evolution cycles but may limit adaptation.
    echo Recommended: 100-2000
    echo.
    set /p POPULATION_SIZE="Enter population size [100-2000]: "
) else if "%sim_choice%"=="4" (
    echo.
    echo [MAX ORGANISMS] Maximum number of organisms the symbiotic network can sustain.
    echo Higher values allow larger, more complex ecosystems to emerge.
    echo Lower values create more focused, manageable evolutionary pressures.
    echo Recommended: 500-5000
    echo.
    set /p MAX_ORGANISMS="Enter max organisms [500-5000]: "
) else if "%sim_choice%"=="5" (
    echo.
    echo [MAX CONNECTIONS] Maximum neural connections in the consciousness network.
    echo Higher values enable more complex consciousness topologies and behaviors.
    echo Lower values create simpler network structures with faster processing.
    echo Recommended: 2000-20000
    echo.
    set /p MAX_CONNECTIONS="Enter max connections [2000-20000]: "
) else if "%sim_choice%"=="6" (
    goto interactive_config
) else (
    echo Invalid choice.
    timeout /t 2 >nul
)

goto configure_simulation

:configure_performance
cls
echo ========================================
echo [PERF] PERFORMANCE SETTINGS
echo ========================================
echo.
echo Current values:
echo Target FPS: %TARGET_FPS%
echo Frame Delay: %FRAME_DELAY%
echo Text Interface: %TEXT_INTERFACE%
echo Simulation Mode: %SIMULATION_MODE%
echo.
echo Choose performance setting to modify:
echo.
echo [1] Target FPS (%TARGET_FPS%)
echo    Higher = faster evolution, Lower = more stable/detailed analysis
echo.
echo [2] Frame Delay (%FRAME_DELAY%)
echo    Higher = slower simulation for observation, Lower = full speed
echo.
echo [3] Text Interface (%TEXT_INTERFACE%)
echo    Enabled = detailed logging, Disabled = faster/cleaner performance
echo.
echo [4] Simulation Mode (%SIMULATION_MODE%)
echo    observer=passive viewing, god=full control
echo.
echo [5] Max Frames (%MAX_FRAMES%)
echo    Blank = unlimited, Number = auto-stop after X frames
echo.
echo [6] Back to Configuration Menu
echo.
set /p perf_choice="Enter setting to change (1-6): "

if "%perf_choice%"=="1" goto perf_fps
if "%perf_choice%"=="2" goto perf_delay
if "%perf_choice%"=="3" goto perf_text
if "%perf_choice%"=="4" goto perf_mode
if "%perf_choice%"=="5" goto perf_frames
if "%perf_choice%"=="6" goto interactive_config

echo Invalid choice.
timeout /t 2 >nul
goto configure_performance

:perf_fps
echo.
echo [TARGET FPS] Controls how fast the simulation runs in frames per second.
echo Higher FPS means faster evolution cycles and quicker results.
echo Lower FPS allows more stable analysis and detailed observation.
echo Recommended: 1-60
echo.
set /p TARGET_FPS="Enter target FPS [1-60]: "
goto configure_performance

:perf_delay
echo.
echo [FRAME DELAY] Adds artificial delay between simulation frames.
echo Useful for slowing down fast simulations for better observation.
echo Set to 0.0 for full speed, higher values for slower viewing.
echo Recommended: 0.0-1.0 seconds
echo.
set /p FRAME_DELAY="Enter frame delay in seconds [0.0-1.0]: "
goto configure_performance

:perf_text
echo.
echo [TEXT INTERFACE] Controls whether detailed console output is shown.
echo Enabled: Shows all simulation details, metrics, and status updates.
echo Disabled: Runs faster with minimal output, better for performance testing.
echo Recommended: Enabled for development, Disabled for benchmarks
echo.
set /p TEXT_INTERFACE="Enable text interface? (y/n): "
goto configure_performance

:perf_mode
echo.
echo [SIMULATION MODE] Determines your interaction level with the simulation:
echo - observer: Passive viewing, AI controls everything
echo - god: Full manual control over all simulation aspects
echo - participant: Immersive experience within the simulation
echo - scientist: Experimental controls and data collection
echo Recommended: observer for first-time
echo.
echo Available modes: observer, god, participant, scientist
set /p SIMULATION_MODE="Enter simulation mode: "
goto configure_performance

:perf_frames
echo.
echo [MAX FRAMES] Limits how long the simulation runs before auto-stopping.
echo Leave blank for unlimited runtime (manual stop required).
echo Set a number to auto-stop after that many simulation frames.
echo Recommended: Leave blank for unlimited
echo.
set /p MAX_FRAMES="Enter max frames (blank for unlimited): "
goto configure_performance

:view_config
cls
echo ========================================
echo [VIEW] CURRENT CONFIGURATION
echo ========================================
echo.
echo OLLAMA MODELS:
if "%AI_MODEL%"=="" (echo AI Model: [NOT SET]) else (echo AI Model: %AI_MODEL% (agents disabled))
echo.
echo SIMULATION PARAMETERS:
if "%QUANTUM_STATES%"=="" (echo Quantum States: [NOT SET]) else (echo Quantum States: %QUANTUM_STATES%)
if "%LATTICE_PARTICLES%"=="" (echo Lattice Particles: [NOT SET]) else (echo Lattice Particles: %LATTICE_PARTICLES%)
if "%POPULATION_SIZE%"=="" (echo Population Size: [NOT SET]) else (echo Population Size: %POPULATION_SIZE%)
if "%MAX_ORGANISMS%"=="" (echo Max Organisms: [NOT SET]) else (echo Max Organisms: %MAX_ORGANISMS%)
if "%MAX_CONNECTIONS%"=="" (echo Max Connections: [NOT SET]) else (echo Max Connections: %MAX_CONNECTIONS%)
echo.
echo PERFORMANCE SETTINGS:
if "%TARGET_FPS%"=="" (echo Target FPS: [NOT SET]) else (echo Target FPS: %TARGET_FPS%)
if "%FRAME_DELAY%"=="" (echo Frame Delay: [NOT SET]) else (echo Frame Delay: %FRAME_DELAY% seconds)
if "%TEXT_INTERFACE%"=="" (echo Text Interface: [NOT SET]) else (echo Text Interface: %TEXT_INTERFACE%)
if "%SIMULATION_MODE%"=="" (echo Simulation Mode: [NOT SET]) else (echo Simulation Mode: %SIMULATION_MODE%)
if "%MAX_FRAMES%"=="" (
    echo Max Frames: Unlimited
) else (
    echo Max Frames: %MAX_FRAMES%
)
echo.
pause
goto interactive_config

:reset_defaults
echo.
echo [RESET] Clearing all parameters (you must set them manually)...
set AI_MODEL=
set QUANTUM_STATES=
set LATTICE_PARTICLES=
set POPULATION_SIZE=
set MAX_ORGANISMS=
set MAX_CONNECTIONS=
set TARGET_FPS=
set SIMULATION_MODE=
set MAX_FRAMES=
set TEXT_INTERFACE=
set FRAME_DELAY=
echo [SUCCESS] All parameters cleared. Configure them manually.
echo.
pause
goto interactive_config

:generate_temp_config
echo [CONFIG] Generating configuration...

REM Check if this is called from model selection (caller sets ASK_SAVE)
if "%ASK_SAVE%"=="true" (
    REM Ask user if they want to save changes permanently
    echo.
    echo [SAVE] Do you want to save these model selections permanently?
    echo This will update config.json and codebase defaults.
    echo.
    set /p save_permanently="Save permanently? (y/N): "
    if /i "%save_permanently%"=="y" (
        call :update_permanent_config
    ) else (
        echo Using temporary configuration for this session only.
    )
)

REM Create temporary config with current settings (even if some are empty)
(
echo {
echo   "simulation": {
echo     "target_fps": %TARGET_FPS%,
echo     "time_resolution_ms": 1.0
echo   },
echo   "quantum": {
echo     "initial_states": %QUANTUM_STATES%
echo   },
echo   "lattice": {
echo     "particles": %LATTICE_PARTICLES%
echo   },
echo   "evolution": {
echo     "population_size": %POPULATION_SIZE%
echo   },
echo   "network": {
echo     "max_organisms": %MAX_ORGANISMS%,
echo     "max_connections": %MAX_CONNECTIONS%
echo   },
echo   "agency": {
echo     "ai_model": "%AI_MODEL%"
echo   },
echo   "rendering": {
echo     "enable_visualizations": true
echo   },
echo   "feedback": {
echo     "enabled": true,
echo     "interval_frames": 10,
echo     "hysteresis_checks": 3,
echo     "rate_limit_frames": 30,
echo     "knobs": {
echo       "mutation_rate": {
echo         "min": 0.001,
echo         "max": 0.05,
echo         "step": 0.001,
echo         "initial": 0.02
echo       },
echo       "new_edge_rate": {
echo         "min": 0.2,
echo         "max": 2.0,
echo         "step": 0.1,
echo         "initial": 1.8
echo       },
echo       "clustering_bias": {
echo         "min": 0.3,
echo         "max": 1.5,
echo         "step": 0.05,
echo         "initial": 0.65
echo       },
echo       "quantum_pruning": {
echo         "min": 0.0,
echo         "max": 1.0,
echo         "step": 0.05,
echo         "initial": 0.7
echo       }
echo     }
echo   }
echo }
) > temp_config.json

echo [SUCCESS] Configuration ready.
goto :eof

:update_permanent_config
echo.
echo [UPDATE] Updating permanent configuration...
echo.

REM Ask if they want to update hardcoded defaults in Python files
echo [CODEBASE] Update hardcoded model references in Python files?
echo This will change default values in the source code permanently.
echo.
set /p update_codebase="Update Python defaults? (y/N): "

REM Run the Python update script
if /i "%update_codebase%"=="y" (
    python update_models.py "%AI_MODEL%" "%VISION_MODEL%"
) else (
    REM Just update config.json without Python defaults
    python -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
config['agency']['ai_model'] = '%AI_MODEL%'
config['agency']['vision_model'] = '%VISION_MODEL%'
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ Updated config.json with AI: %AI_MODEL%, Vision: %VISION_MODEL%')
print('ℹ️ Python defaults unchanged (user choice)')
"
)

echo.
echo [SUCCESS] Permanent configuration updated!
goto :eof

:quick_start
echo.
echo [TARGET] Starting Reality Simulator with Custom Configuration...
echo.
REM No validation - user can enter whatever values they want

echo Configuration Summary:
echo AI Model: %AI_MODEL% (agents disabled)
echo Quantum States: %QUANTUM_STATES% / Particles: %LATTICE_PARTICLES%
echo Population: %POPULATION_SIZE% / Organisms: %MAX_ORGANISMS%
echo FPS Target: %TARGET_FPS% / Mode: %SIMULATION_MODE%
echo.

echo [DEBUG] Generating temp config...
call :generate_temp_config

if not exist temp_config.json (
    echo [ERROR] Failed to generate temp config file!
    pause
    goto main_menu_inline
)

echo [DEBUG] Temp config generated successfully.

REM Build command line arguments
set CMD_ARGS=--mode %SIMULATION_MODE% --config "%~dp0temp_config.json"
if "%FRAME_DELAY%" NEQ "0.0" set CMD_ARGS=%CMD_ARGS% --delay %FRAME_DELAY%
if "%MAX_FRAMES%" NEQ "" set CMD_ARGS=%CMD_ARGS% --frames %MAX_FRAMES%
if "%TEXT_INTERFACE%"=="disabled" set CMD_ARGS=%CMD_ARGS% --no-text

echo [LAUNCH] Command: python -m reality_simulator.main %CMD_ARGS%
echo.

REM Check if Python exists before launching
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Cannot launch simulator.
    pause
    goto main_menu_inline
)

REM Launch with error checking
echo [DEBUG] Launching Python script...
python -m reality_simulator.main %CMD_ARGS%
set LAUNCH_EXIT_CODE=%errorlevel%

echo.
echo [DEBUG] Python script exited with code: %LAUNCH_EXIT_CODE%

REM Clean up temp config
if exist temp_config.json (
    del temp_config.json
    echo [DEBUG] Temp config cleaned up.
) else (
    echo [WARNING] Temp config file was not found for cleanup.
)

if %LAUNCH_EXIT_CODE% NEQ 0 (
    echo [ERROR] Python script exited with error code %LAUNCH_EXIT_CODE%
    echo Press any key to return to main menu...
    pause >nul
    goto main_menu_inline
)

goto end

:god_mode
echo.
echo [GOD] Starting Reality Simulator in God Mode...
echo Full control over the simulation universe.
echo.
echo Using current configuration:
echo AI Model: %AI_MODEL% (agents disabled)
echo.

call :generate_temp_config
python -m reality_simulator.main --mode god --config temp_config.json
if exist temp_config.json del temp_config.json
goto end

:scientist_mode
echo.
echo [SCIENCE] Starting Reality Simulator in Scientist Mode...
echo Experimental controls for hypothesis testing.
echo.
echo Using current configuration:
echo AI Model: %AI_MODEL% | Vision: %VISION_MODEL%
echo.

call :generate_temp_config
python -m reality_simulator.main --mode scientist --config temp_config.json
if exist temp_config.json del temp_config.json
goto end

:participant_mode
echo.
echo [STAR] Starting Reality Simulator in Participant Mode...
echo Immersive experience within the simulated reality.
echo.
echo Using current configuration:
echo AI Model: %AI_MODEL% | Vision: %VISION_MODEL%
echo.

call :generate_temp_config
python -m reality_simulator.main --mode participant --config temp_config.json
if exist temp_config.json del temp_config.json
goto end

:chat_mode
echo.
echo [CHAT] Chat Mode has been DISABLED
echo.
echo AI agents (Ollama) have been completely removed from this system.
echo Chat mode is no longer available.
echo.
echo Available modes:
echo   - observer: Scientific observation and analysis
echo   - god: Omniscient control over the simulation
echo   - participant: Immersive experience within the simulation
echo   - scientist: Experimental controls and hypothesis testing
echo.
pause
goto main_menu_inline

:custom_config
echo.
echo [SETTINGS] Legacy Custom Configuration (Use Interactive Config Instead)
echo.
echo NOTE: This legacy menu is deprecated. Use option [2] Interactive Configuration
echo for a much better experience with explanations and model selection.
echo.
echo Press any key to go to Interactive Configuration...
pause >nul
goto interactive_config

:run_tests
echo.
echo [TEST] Running Reality Simulator Tests...
echo.
echo Select test suite:
echo [1] All Tests
echo [2] Quantum Substrate Only
echo [3] Evolution Engine Only
echo [4] Symbiotic Network Only
echo [5] Agency Layer Only
echo [6] Reality Renderer Only
echo [7] Integration Tests Only
echo [8] Back to Main Menu
echo.
set /p test_choice="Enter choice (1-8): "

if "%test_choice%"=="1" (
    echo Running all tests...
    python tests/test_quantum_substrate.py
    python tests/test_subatomic_lattice.py
    python tests/test_evolution_engine.py
    python tests/test_symbiotic_network.py
    python tests/test_agency.py
    python tests/test_reality_renderer.py
    python tests/test_integration.py
) else if "%test_choice%"=="2" (
    python tests/test_quantum_substrate.py
) else if "%test_choice%"=="3" (
    python tests/test_evolution_engine.py
) else if "%test_choice%"=="4" (
    python tests/test_symbiotic_network.py
) else if "%test_choice%"=="5" (
    python tests/test_agency.py
) else if "%test_choice%"=="6" (
    python tests/test_reality_renderer.py
) else if "%test_choice%"=="7" (
    python tests/test_integration.py
) else if "%test_choice%"=="8" (
    goto main_menu_inline_inline
) else (
    echo Invalid choice.
    goto run_tests
)

echo.
echo Tests completed. Press any key to continue...
pause >nul
goto main_menu_inline

:run_benchmarks
echo.
echo [CHART] Running Performance Benchmarks...
echo.
echo [1] Quick Benchmark (10 frames)
echo [2] Standard Benchmark (100 frames)
echo [3] Extended Benchmark (1000 frames)
echo [4] Back to Main Menu
echo.
set /p bench_choice="Enter choice (1-4): "

if "%bench_choice%"=="1" (
    echo Running quick benchmark...
    python reality_simulator/main.py --frames 10 --no-text
) else if "%bench_choice%"=="2" (
    echo Running standard benchmark...
    python reality_simulator/main.py --frames 100 --no-text
) else if "%bench_choice%"=="3" (
    echo Running extended benchmark...
    echo [WARNING]  This may take several minutes...
    python reality_simulator/main.py --frames 1000 --no-text
) else if "%bench_choice%"=="4" (
    goto main_menu_inline_inline
) else (
    echo Invalid choice.
    goto run_benchmarks
)

echo.
echo Benchmark completed. Press any key to continue...
pause >nul
goto main_menu_inline


:end
echo.
echo ========================================
echo Simulation ended. Press any key to exit...
pause >nul
exit /b 0

:feedback_status
cls
echo ========================================
echo [FEEDBACK] SYSTEM STATUS
echo ========================================
echo.
echo [INFO] Checking feedback controller status...
echo.
echo This will run a quick simulation initialization to check feedback status.
echo.
set /p run_check="Run feedback status check? (y/n): "
if /i not "%run_check%"=="y" goto main_menu_inline_inline

echo.
echo [CHECK] Initializing simulation components...
echo.

REM Create a temporary Python script to check feedback status
echo import sys, os > check_feedback.py
echo sys.path.append(os.path.join(os.path.dirname(__file__), 'reality_simulator')) >> check_feedback.py
echo from main import RealitySimulator >> check_feedback.py
echo. >> check_feedback.py
echo # Initialize simulator to check feedback status >> check_feedback.py
echo sim = RealitySimulator() >> check_feedback.py
echo if hasattr(sim, 'feedback_controller') and sim.feedback_controller: >> check_feedback.py
echo     sim.feedback_controller.print_status() >> check_feedback.py
echo else: >> check_feedback.py
echo     print("[ERROR] Feedback controller not initialized") >> check_feedback.py

python check_feedback.py
if errorlevel 1 (
    echo [ERROR] Failed to check feedback status
) else (
    echo.
    echo [SUCCESS] Feedback status check completed
)

REM Clean up
del check_feedback.py 2>nul

echo.
pause
goto main_menu_inline_inline

:exit_launcher
echo.
echo [WAVE] Goodbye! Thanks for exploring simulated reality.
echo.
exit /b 0

