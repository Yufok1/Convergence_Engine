# 🦋 Unified System Guide - One Cohesive Unit

## Overview

**Single entry point. One process. Three systems unified.**

The unified system provides:
- ✅ Pre-flight system checks (redundant, comprehensive)
- ✅ Extensive state logging (granular, terse, information-saturated)
- ✅ Unified visualization (Left: Reality Sim, Middle: Explorer, Right: Djinn Kernel)
- ✅ All systems wired as one machine

---

## Quick Start

### Run Everything

```bash
python unified_entry.py
```

### Pre-flight Checks Only

```bash
python unified_entry.py --check-only
```

### Without Visualization

```bash
python unified_entry.py --no-viz
```

---

## Architecture

```
unified_entry.py (Main Entry Point)
  │
  ├─> PreFlightChecker
  │   ├─> Check dependencies
  │   ├─> Check systems
  │   ├─> Check files
  │   ├─> Check directories
  │   └─> Check memory
  │
  ├─> StateLogger
  │   ├─> state.log (all states)
  │   ├─> breath.log (breath cycles)
  │   ├─> reality_sim.log (network metrics)
  │   ├─> explorer.log (Explorer state)
  │   ├─> djinn_kernel.log (VP calculations)
  │   └─> system.log (system events)
  │
  ├─> UnifiedVisualization
  │   ├─> Left Panel: Reality Simulator
  │   ├─> Middle Panel: Explorer
  │   └─> Right Panel: Djinn Kernel
  │
  └─> UnifiedSystem
      ├─> Explorer (body - breath engine)
      ├─> Reality Simulator (left wing)
      └─> Djinn Kernel (right wing)
```

---

## Pre-Flight Checks

The system performs comprehensive checks before starting:

1. **Dependencies**: numpy, networkx, matplotlib, tkinter, pywin32 (optional)
2. **Systems**: Explorer, Reality Simulator, Djinn Kernel availability
3. **Files**: config.json, main.py files
4. **Directories**: explorer/, reality_simulator/, kernel/, data/
5. **Memory**: System memory check (warns if < 4GB)

**All checks must pass (or be warnings) before system starts.**

---

## Logging System

### Two Complementary Logging Systems

1. **Application Logging** (`logging_config.py`)
   - For: Debug messages, info, warnings, errors
   - Format: Human-readable messages
   - Usage: `from logging_config import get_logger; logger = get_logger(__name__)`
   - Location: `data/logs/application.log`

2. **State Logging** (`StateLogger` in `unified_entry.py`)
   - For: State metrics, breath cycles, system state
   - Format: Terse, information-saturated (metric:value|metric:value|...)
   - Purpose: System monitoring and metrics collection

### State Log Format

**Terse, information-saturated format:**
```
HH:MM:SS.microseconds|LEVEL|COMPONENT|metric:value|metric:value|...
```

### Example Logs

**Breath Log:**
```
14:23:45.123456|DEBUG|breath|cycle:42|depth:0.750|phase:1.234|pulse:1.000
```

**Reality Sim Log:**
```
14:23:45.123456|DEBUG|reality_sim|orgs:500|conns:2500|mod:0.250|clust:0.600|path:2.50|gen:100
```

**Explorer Log:**
```
14:23:45.123456|DEBUG|explorer|phase:genesis|vp_calcs:25|sovereign_ids:5|math_cap:False
```

**Djinn Kernel Log:**
```
14:23:45.123456|DEBUG|djinn_kernel|vp:0.200|vp_class:VP0|vp_calcs:25|traits:6
```

### Log Location

All logs are in `data/logs/`:
- `state.log` - All state changes
- `breath.log` - Breath cycles
- `reality_sim.log` - Network metrics
- `explorer.log` - Explorer state
- `djinn_kernel.log` - VP calculations
- `system.log` - System events

---

## Visualization

### Three-Panel Layout

**Left Panel (Cyan)**: Reality Simulator
- Organism count
- Connection count
- Modularity
- Clustering coefficient

**Middle Panel (Yellow)**: Explorer
- Phase (Genesis/Sovereign)
- VP calculations
- Breath cycle
- Breath depth

**Right Panel (Magenta)**: Djinn Kernel
- Violation Pressure
- VP Classification
- VP Calculations

### Visualization Features

- **Real-time updates**: All panels update every breath cycle
- **Full screen**: 1920x1080 window
- **Dark theme**: Black background, colored text
- **Monospace font**: Easy to read metrics

---

## System Operation

### The Breath Cycle

1. **Breath drives** → `breath_engine.breathe()`
2. **Reality Simulator reacts** → `network.update_network()` (one generation)
3. **Djinn Kernel reacts** → `vp_monitor.compute_violation_pressure()` (one VP calc)
4. **Explorer continues** → Normal Genesis/Sovereign operation
5. **States logged** → All states logged to files
6. **Visualization updates** → All panels refresh

### State Flow

```
Breath Cycle
  ↓
Reality Simulator State → Logger → Visualization (Left)
  ↓
Explorer State → Logger → Visualization (Middle)
  ↓
Djinn Kernel State → Logger → Visualization (Right)
  ↓
Next Breath Cycle
```

---

## Troubleshooting

### Pre-flight Checks Fail

**Missing dependencies:**
```bash
pip install numpy networkx matplotlib
```

**Missing optional dependency (Windows):**
```bash
pip install pywin32
```

### Visualization Not Working

**Check matplotlib backend:**
```bash
python -c "import matplotlib; print(matplotlib.get_backend())"
```

**Run without visualization:**
```bash
python unified_entry.py --no-viz
```

### Logs Not Writing

**Check directory permissions:**
```bash
mkdir -p data/logs
```

---

## The Result

**One cohesive unit. One command. Three systems unified.**

- ✅ Single entry point
- ✅ Pre-flight validation
- ✅ Comprehensive logging
- ✅ Unified visualization
- ✅ All systems wired together

**The butterfly flies as one organism.** 🦋

---

## 🔧 Code Quality

### Error Handling
- ✅ All bare except clauses use specific exception types
- ✅ Proper exception handling throughout
- ✅ Better error visibility and debugging

### Logging
- ✅ Centralized logging configuration (`logging_config.py`)
- ✅ Consistent logging approach across all modules
- ✅ Debug output controlled by log levels
- ✅ Professional logging infrastructure

### Testing
- ✅ End-to-end tests for unified system (`tests/test_e2e_unified_system.py`)
- ✅ Comprehensive test coverage (~85+ test functions)
- ✅ Component tests for all major systems

### Production Readiness
- ✅ Code quality standards met
- ✅ Best practices followed
- ✅ Comprehensive documentation
- ✅ All systems verified and tested

