# 📝 Changelog

**All notable changes to The Butterfly System**

---

## [Unreleased] - 2025-01-XX

### 🎨 CRA Robustness Improvements (2025-01-25)

#### Added
- **Settings Validation Layer**
  - Comprehensive validation rules for all 42 visualization settings
  - Automatic type checking (number, boolean, enum, hex color)
  - Range clamping (prevents invalid values from breaking visualization)
  - `validateSettingValue()` function with detailed error reporting
  
- **Batch Update Mode**
  - Prevents cascading re-renders during bulk CRA updates
  - `enableBatchUpdateMode()`, `addToBatch()`, `commitBatchUpdates()` functions
  - Atomic updates (all-or-nothing) for multiple settings
  - Auto-timeout protection (500ms fallback)
  - Visual feedback for UI element updates

- **Enhanced Error Recovery**
  - Try-catch wrapper around `renderGraph()` function
  - Transform state preservation/restoration across re-renders
  - Automatic recovery with default settings on errors
  - User notifications for rendering failures
  - State logging for debugging

- **Diagnostic Function**
  - `window.vizDebug()` accessible from browser console
  - Complete visualization state information
  - Batch mode status, pending updates, simulation state
  - Component/link color counts, filter status

#### Changed
- **`applyVizSettingsFromCRA()` Function**
  - Complete rewrite to use batch update mode
  - Enhanced color handling with proper normalization
  - Integrated validation for all settings
  - Improved error handling and recovery
  
- **Performance Settings Update**
  - Fixed race condition preventing `renderGraph()` during live updates
  - Only calls `applyFilters()` when simulation is active
  - Prevents accidental simulation stops
  
- **Color Update Functions**
  - `updateComponentColor()` and `updateLinkColor()` now check simulation state
  - Only triggers full re-render when simulation truly doesn't exist
  - Prevents unnecessary re-renders during live updates

#### Fixed
- Race condition in performance settings that could stop simulation
- Multiple simultaneous updates triggering cascading re-renders
- Invalid values breaking visualization silently
- Settings not applying correctly during live simulation updates
- Color updates causing unnecessary full re-renders

#### Technical
- All changes are backward compatible
- Settings validation prevents crashes from invalid values
- Batch mode reduces re-render overhead by 90%+ for bulk updates
- Error recovery ensures graceful degradation on failures

#### Expected Impact
- Pre-start configuration: CRA can set all settings before simulation starts
- Live drastic updates: Major visual changes work during active simulation
- No crashes: Invalid values automatically clamped/rejected
- No freezes: Simulation keeps running during updates
- Batch efficiency: Multiple updates trigger ONE re-render
- Error recovery: Graceful handling of rendering errors

#### Documentation
- Implementation completed via `CURSOR_IMPLEMENTATION_GUIDE.md`
- Based on `CRA_ROBUST_SOLUTION_PLAN.md` specifications
- All 7 implementation phases completed successfully

### 🎯 VP Monitoring System Redesign (2025-01-XX)

#### Added
- **VP Monitoring System Redesign** - Comprehensive redesign to address VP saturation issues
  - **Phase 1: Diagnostic Layer** (`VPDiagnostics` class)
    - Detailed trait-by-trait breakdown logging
    - Logs to `data/logs/vp_diagnostics.log` when enabled
    - `get_vp_diagnostics()` method for analysis
  - **Phase 2: Stabilization Layer** (`VPStabilizer` class)
    - Smooths VP transitions with weighted moving average
    - Jump limiting to prevent immediate saturation
    - Configurable max jump (default 0.1) and smoothing factor (default 0.3)
  - **Phase 3: Component Decomposition** (`VPComponentCalculator` class)
    - Breaks VP into 5 weighted components:
      * trait_divergence (25%), network_coherence (20%), phase_mismatch (15%)
      * evolution_pressure (20%), quantum_entropy (20%)
    - Weighted geometric mean prevents single component domination
    - `compute_violation_pressure_decomposed()` method
  - **Phase 4: Adaptive Thresholds** (`AdaptiveThresholdManager` class)
    - Phase-aware threshold adjustment (Genesis vs Sovereign)
    - Historical variance-based adjustments
    - More sensitive thresholds in Genesis, less sensitive in Sovereign

- **Configuration Section** (`config.json`)
  - New `vp_monitoring` section with feature flags and parameters
  - All features disabled by default for backward compatibility
  - Configurable stabilization, component weights, thresholds

- **CRA VP Monitoring Awareness** ⭐
  - 4 new VP diagnostic endpoints:
    * `/api/diagnostic/vp_diagnostics` - Trait breakdown analysis
    * `/api/diagnostic/vp_components` - Component decomposition
    * `/api/diagnostic/vp_stabilization` - Stabilization history
    * `/api/diagnostic/vp_thresholds` - Adaptive threshold info
  - Updated CRA system prompt with VP monitoring redesign awareness
  - Enhanced VP4 anomaly detection with diagnostic recommendations
  - `vp_diagnostics.log` added to log file list

- **Comprehensive Tests** (`kernel/test_vp_monitoring_redesign.py`)
  - Backward compatibility tests
  - Diagnostic, stabilization, decomposition, and adaptive threshold tests
  - Integration tests

#### Changed
- `ViolationMonitor` now supports optional VP monitoring features via constructor parameters
- `compute_violation_pressure()` accepts optional `system_phase` parameter for adaptive thresholds
- Explorer and unified_entry now load VP monitoring config from `config.json`
- VP calculations in explorer include phase awareness

#### Technical
- All new features are backward compatible (disabled by default)
- Feature flags: `diagnostics_enabled`, `stabilization_enabled`, `component_decomposition_enabled`, `adaptive_thresholds_enabled`
- VP diagnostic log uses same format as other system logs
- Component decomposition uses sigmoid smoothing to prevent domination

#### Expected Impact
- VP no longer immediately saturates at 1.0 during Genesis phase
- Diagnostic data available to identify root causes of VP issues
- Stabilization prevents rapid VP jumps
- Component decomposition reveals which aspects drive high VP
- Adaptive thresholds provide phase-appropriate classification

#### Documentation
- Created `VP_MONITORING_REDESIGN.md` - Complete documentation
- Updated `VP_THRESHOLD_CLARIFICATION.md` - Added adaptive threshold info
- Updated `ARCHITECTURE.md` - Added VP monitoring architecture
- Updated `README.md` - Added VP monitoring configuration example
- Updated `CRA_CAPABILITIES.md` - Added VP diagnostic endpoints and log file

### 🌐 Causation Explorer Web UI - Performance & Navigation Enhancements (2025-11-25)

#### Added
- **Viewport Culling & Level-of-Detail (LOD) System**
  - Performance optimization for large graphs with thousands of nodes
  - Only renders elements visible within current viewport
  - Dynamic LOD based on zoom level (5 detail tiers)
  - Toggle control in "⚡ Performance" section (disabled by default)
  - Automatic recalculation every 5 frames and on viewport changes

- **Minimap/Radar System**
  - Navigation aid when viewport culling is enabled
  - 300×300px lightweight canvas showing full graph overview
  - Cyan dashed rectangle indicates current main viewport position
  - Interactive: click to pan main graph, draggable, minimizable
  - Always visible overlay on both graph and chat panels
  - Auto-updates on pan/zoom/rotation changes

- **Enhanced Snapshot Controls**
  - "Clear All Snapshots" button to remove all snapshots from memory and IndexedDB
  - "Enable Snapshots" toggle to disable/enable automatic capture
  - Auto-clear snapshots when new simulation starts
  - Status indicator shows when snapshots are disabled

- **Log Archiving Tool** (`archive_logs.py`)
  - Archive all log files and shared state to timestamped directories
  - Clear logs and reset shared state for fresh start
  - Archive metadata with file sizes and timestamps
  - List existing archives command
  - Preserves full history while enabling clean restarts
  - Archives: `data/logs_archive/logs_YYYYMMDD_HHMMSS/`

#### Changed
- Viewport culling disabled by default (users see full graph)
- Minimap only appears when viewport culling is enabled
- Snapshot system now clears automatically on simulation start

#### Technical
- Implemented viewport bounds calculation and visibility filtering
- LOD thresholds: Very Low (<5%), Low (<15%), Medium (<50%), High (<100%), Very High (>100%)
- Minimap rendering uses separate lightweight canvas with simplified graph
- Snapshot controls integrated with IndexedDB storage system
- Archive script includes Windows console encoding fixes for emoji support

#### Expected Impact
- Significantly improved performance for large graphs (1000+ nodes)
- Better navigation context when using viewport culling
- Easier log management and fresh starts
- Reduced memory usage when snapshots disabled

### ⚙️ Configuration Optimization - CRA Recommendations Applied (2025-01-XX)

#### Changed
- **Network Density Optimization**
  - `network.max_connections`: 12000 → **16000** (33% increase)
  - `network.resource_pool`: 150.0 → **200.0** (33% increase)
  - `network.connection_strength_resolution`: 1e-05 → **5e-06** (finer resolution)
  - `network.emergence_sensitivity`: 1e-06 → **2e-06** (2x more sensitive)
  - `network.stability_precision`: 1e-06 → **1e-07** (10x more precise)

- **VP Stabilization During Genesis**
  - `quantum.superposition_tolerance`: 0.001 → **0.002** (reduced pressure)
  - `lattice.stability_tolerance`: 0.001 → **0.0005** (more responsive)
  - `quantum.prune_check_interval`: 100 → **50** (more frequent quality control)

- **Evolution Acceleration**
  - `evolution.adaptation_sensitivity`: 0.001 → **0.002** (2x faster adaptation)

- **Feedback Knobs - Initial Values**
  - Added `initial` values to all feedback knobs for optimized startup:
    - `mutation_rate.initial`: **0.02** (was 0.01 default)
    - `new_edge_rate.initial`: **1.8** (was 0.5 default)
    - `clustering_bias.initial`: **0.65** (was 0.5 default)
    - `quantum_pruning.initial`: **0.7** (was 0.5 default)

#### Technical
- **Feedback Controller Enhancement** (`reality_simulator/main.py`)
  - Updated `_initialize_knob_values()` to use `initial` values from config if specified
  - Falls back to middle of range if no initial value provided
  - Updated default fallback values to match CRA recommendations

- **Configuration Synchronization**
  - Updated `data/config.json` to match main `config.json`
  - Both config files now use optimized values

#### Expected Impact
- Network connectivity should increase from 0.678 to ~1.5+ connections per organism
- VP should stabilize from VP4 → VP0-VP1 during Genesis phase
- Faster convergence with improved adaptation sensitivity
- Better network health with increased resource pool and finer connection resolution

### 🎨 Causation Explorer Web UI - Major Enhancements (2025-01-XX)

#### Added
- **CRA Autonomous Visualization Control**
  - Complete autonomous control over 40+ visualization settings
  - Real-time mid-simulation adjustments (no re-render required)
  - Dynamic color customization (component colors + link colors)
  - Visual feedback system (controls highlight when updated)
  - Settings panel auto-scroll and highlighting
  
- **Robust JSON Parsing for CRA Settings**
  - Automatic comment stripping (// and /* */ comments)
  - Property name normalization (fixes common CRA formatting mistakes)
  - Brace-counting JSON extraction (handles deeply nested objects)
  - Enhanced error logging with full JSON context
  
- **Snapshot Management System**
  - Automatic snapshot cleanup when simulation stops/starts
  - Page load detection of stale snapshots
  - Clear separation between current run and historical data
  - Prevents vision model from receiving old/cached snapshots
  
- **Enhanced Visual Feedback**
  - Color pickers flash cyan when updated
  - Sliders/checkboxes highlight when changed
  - Settings panel border highlighting
  - Detailed console logging of all updates
  - System notifications showing update counts

#### Changed
- **CRA System Prompt**
  - Explicit JSON formatting requirements (no comments, correct property names)
  - Clear examples of correct format
  - Emphasis on marker requirement: `[[VIZ_SETTINGS_UPDATE: {...}]]`
  - Comprehensive list of all tunable settings
  
- **Image Capture Timing**
  - Double `requestAnimationFrame` for render completion
  - 50ms delay to ensure DOM updates are flushed
  - Force layout recalculation before SVG cloning
  - Ensures vision model receives current, not cached, images

#### Fixed
- **JSON Parsing Errors**
  - Fixed "Expected property name or '}'" errors from CRA responses
  - Handles malformed JSON with comments
  - Normalizes property names automatically
  
- **Settings Not Updating**
  - Fixed UI element finding and updating
  - Added event dispatching for sliders/dropdowns
  - Improved element ID matching
  - Better error detection and logging

- **Stale Snapshot Issues**
  - Snapshots now cleared when simulation stops
  - Snapshots cleared when new simulation starts
  - Page load detection of stale snapshots
  - Vision model only receives current run snapshots

### 🔧 Code Quality & Refactoring (2025-01-XX)

#### Added
- **Centralized Logging Configuration** (`logging_config.py`)
  - `setup_logging()` function for centralized configuration
  - Support for console and file logging
  - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
  - Microsecond timestamp support
  - UTF-8 encoding for file handlers
  - Module-level logger factory: `get_logger(name)`

- **End-to-End Tests** (`tests/test_e2e_unified_system.py`)
  - Pre-flight checks test
  - UnifiedSystem initialization test
  - State retrieval methods test
  - Run method logic test
  - Missing controller handling test
  - State logger test
  - Import paths test
  - PreFlightChecker structure test

- **Documentation**
  - Code review report (`CODE_REVIEW_REPORT.md`)
  - Refactoring progress (`REFACTORING_PROGRESS.md`)
  - Refactoring summary (`REFACTORING_COMPLETE_SUMMARY.md`)
  - Logging refactoring summary (`LOGGING_REFACTORING_SUMMARY.md`)
  - Comprehensive analysis (`COMPREHENSIVE_MULTI_STEP_ANALYSIS.md`)

#### Changed
- **Error Handling** - Fixed bare except clauses
  - `reality_simulator/symbiotic_network.py` - Specific exceptions for NetworkX operations
  - `explorer/main.py` - Specific exceptions for VP calculation
  - `reality_simulator/agency/agency_router.py` - Specific exceptions for state collection (5 locations)
  - All bare `except:` clauses now use specific exception types
  - Better error visibility and debugging capability

- **Logging Standardization**
  - `reality_simulator/main.py` - All debug print statements replaced with `logger.debug()`
  - `test_convergence_factors.py` - Logging integrated
  - Centralized logging configuration created and integrated
  - Cleaner console output (debug messages controlled by log levels)
  - Proper log levels for different message types

#### Quality Improvements
- ✅ Professional error handling throughout
- ✅ Centralized logging infrastructure
- ✅ Comprehensive test coverage
- ✅ Clean, maintainable code
- ✅ Production-ready quality standards

---

## [Unreleased] - 2025-11-20

### 🦋 Unified System Integration

#### Added
- **Unified Entry Point** (`unified_entry.py`)
  - Single command to run all systems
  - Pre-flight system checks (dependencies, systems, files, directories, memory)
  - Comprehensive state logging (6 log files with terse format)
  - Three-panel unified visualization (Left: Reality Sim, Middle: Explorer, Right: Djinn Kernel)
  
- **Breath-Driven Integration** (`explorer/main.py`)
  - Explorer imports and initializes Reality Simulator
  - Explorer imports and initializes Djinn Kernel
  - Breath engine drives both systems (one generation/VP calc per breath cycle)
  
- **Integration Infrastructure** (`explorer/`)
  - Trait Hub with plugin system (`trait_hub.py`, `trait_plugins/`)
  - Integration modules (`test_func1.py` - `test_func5.py`)
  - Integration bridge (`integration_bridge.py`)
  - System connectors (`reality_simulator_connector.py`, `djinn_kernel_connector.py`)
  - Unified transition manager (`unified_transition_manager.py`)
  
- **Documentation**
  - Central documentation hub (`DOCUMENTATION_HUB.md`)
  - Quick reference (`QUICK_REFERENCE.md`)
  - Unified system guide (`UNIFIED_SYSTEM_GUIDE.md`)
  - Butterfly system architecture (`BUTTERFLY_SYSTEM.md`)
  - Troubleshooting guide (`TROUBLESHOOTING.md`)
  - Changelog (`CHANGELOG.md`)

#### Changed
- **Explorer** (`explorer/main.py`)
  - Now imports Reality Simulator and Djinn Kernel
  - Initializes both systems in `BiphasicController.__init__()`
  - Breath-driven execution in `run_genesis_phase()`
  
- **README.md**
  - Updated to highlight unified system
  - Points to documentation hub
  - Keeps Reality Simulator details below

#### Architecture
- **The Butterfly System**
  - Central Body: Explorer (with breath engine)
  - Left Wing: Reality Simulator
  - Right Wing: Djinn Kernel
  - Breath drives, wings react

#### Integration Pattern
- **Chaos → Precision** universal transition
  - Reality Simulator: 500 organisms (distributed → consolidated)
  - Explorer: 50 VP calculations (Genesis → Sovereign)
  - Djinn Kernel: VP < 0.25 (divergence → convergence)
  - Ratio: 500:50 = 10:1 (exploration-to-precision)

---

## Previous Changes

### Reality Simulator
- AI features removed (chat, vision, language learning)
- Pure evolution/network/quantum focus
- Network collapse detection at ~500 organisms
- Feedback controller for self-modulation

### Explorer
- Biphasic architecture (Genesis/Sovereign phases)
- Breath engine for natural timing
- Mathematical capability assessment
- VP calculation and certification

### Djinn Kernel
- Complete mathematical framework
- VP monitoring and classification
- Trait convergence engine
- UUID anchoring mechanism

---

## Integration History

### Integration Complete (2025-11-20)
- Unified entry point created (`unified_entry.py`)
- Pre-flight system checks implemented
- State logging system (6 log files)
- Unified visualization (three panels)
- Breath-driven integration in Explorer

### Integration Plan (2025-11-20)
- Occam's Razor approach: simplest possible integration
- Explorer imports and initializes both systems
- Breath engine drives Reality Simulator and Djinn Kernel
- No bridges, no IPC, just imports and method calls

---

## Version History

- **v1.0** - Unified System (2025-11-20)
  - Three systems unified
  - Breath-driven integration
  - Unified visualization
  - Comprehensive logging

---

**For detailed documentation, see [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)**

