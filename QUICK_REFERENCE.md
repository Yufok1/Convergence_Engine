# 🦋 Quick Reference - The Butterfly System

**One-page reference for everything**

---

## 🚀 Commands

```bash
# Run unified system
python unified_entry.py

# Pre-flight checks only
python unified_entry.py --check-only

# Without visualization
python unified_entry.py --no-viz

# ⚔️ Highlander Mode - AI Survival Tournament
python unified_entry.py --highlander --predation --survival-threshold 0.8 --competition-intensity 0.95

# Integration test
cd explorer && python test_integration.py
```

---

## 🌱 Fresh Clone Setup

**First time setup after cloning the repo:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify setup
python check_setup.py

# 3. Build vocabulary & knowledge web (REQUIRED for language systems)
python build_curated_dataset.py
```

This creates:
- `data/butterfly_vocabulary_200k_raw.json` - WordNet vocabulary (~141k words)
- `data/butterfly_vocabulary_250k_curated.json` - Filtered vocabulary
- `data/seeded_knowledge_web_250k.json` - Semantic relationships

**Optional: Distill to smaller vocabulary (faster, less memory)**
```bash
# Distill to 50k words
python distill_vocabulary.py --input data/seeded_knowledge_web_250k.json --output data/knowledge_web_distilled.json --target 50000
```

**Then run the system:**
```bash
python unified_entry.py
```

---

## 📁 Key Files

- `unified_entry.py` - Main entry point (976 lines)
- `explorer/main.py` - Explorer with integration (799 lines)
- `logging_config.py` - Centralized logging configuration
- `config.json` - Configuration
- `DOCUMENTATION_HUB.md` - All documentation

## 🧪 Testing

```bash
# End-to-end tests
python tests/test_e2e_unified_system.py

# Integration tests
cd explorer && python test_integration.py

# Reality Simulator tests
python tests/test_integration.py
python tests/test_evolution_engine.py
python tests/test_symbiotic_network.py
```

---

## 🏗️ Architecture

```
Explorer (body - breath engine)
  ├─> Reality Simulator (left wing)
  └─> Djinn Kernel (right wing)
```

**Breath drives → Wings react**

---

## 📊 State Logs

Location: `data/logs/`

- `state.log` - All states
- `breath.log` - Breath cycles
- `reality_sim.log` - Network metrics
- `explorer.log` - Explorer state
- `djinn_kernel.log` - VP calculations
- `system.log` - System events
- `application.log` - General application logging

**Archive logs:**
```bash
python archive_logs.py --confirm  # Archive & clear
python archive_logs.py --list     # List archives
```

---

## 🎨 Visualization

**Three Panels:**
- Left (Cyan): Reality Simulator
- Middle (Yellow): Explorer
- Right (Magenta): Djinn Kernel

---

## 🔑 Key Concepts

- **Breath:** Primary driver (Explorer's breath engine)
- **Chaos → Precision:** Universal transition (500:50 = 10:1)
- **VP Threshold:** 0.25 (VP0 - fully lawful)
- **Modularity Threshold:** < 0.3 (network collapse)

---

## 🦋 Butterfly Chat

**Location:** Web UI → CRA Panel → 🦋 Butterfly Chat tab

**Features:**
- 5 routing strategies: All, Random, Fittest, Connected, By Word
- Debug panel: Logs, Causation Trail, Errors
- Illumination integration: Analyze each response step
- Learning system: Organisms learn from every interaction
- Vocabulary growth: Auto-learns words from user messages

**Usage:**
1. Open Butterfly Chat tab
2. Select routing strategy
3. Type message and send
4. View debug panel for analysis
5. Click Illumination buttons to analyze responses

**See:** [BUTTERFLY_CHAT_DEBUG_PANEL_GUIDE.md](./BUTTERFLY_CHAT_DEBUG_PANEL_GUIDE.md)

---

## 📦 Agent Export (Cocoon System)

**Export evolved organisms as portable AI agents:**

```bash
# Via Web UI (recommended)
# CRA → Agent Exporter → Compile Cocoon

# What you get:
agent_downloads/cocoon_ensemble_<timestamp>/
├── cocoon.py              # Main agent (CocoonAgent class)
├── bridge.py              # Universal interface (Gym, HTTP, CLI)
├── proton_tournament.py   # Self-improvement battles
├── brain_ensemble.pt      # Neural weights (TorchScript)
├── brain_ensemble.onnx    # Neural weights (ONNX for Netron)
├── vocabulary.json        # Word pool
├── knowledge_web.json     # Semantic relationships
├── context_memory.json    # Word-organism anchors
├── metadata.json          # Export info
└── README.md              # Usage instructions
```

**Run exported agent:**
```bash
cd agent_downloads/cocoon_ensemble_<timestamp>

# Chat mode
python cocoon.py --mode chat

# Gym training
python bridge.py . --mode gym --gym-env CartPole-v1 --render

# Self-improvement tournament
python -c "
from cocoon import CocoonAgent
from proton_tournament import ProtonTournament
agent = CocoonAgent()
tournament = ProtonTournament(agent)
tournament.swarm_pong_arena(lives=3, headless=True)
"
```

---

## 📚 Documentation

**Central Hub:** [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)

**Quick Guides:**
- [UNIFIED_SYSTEM_GUIDE.md](./UNIFIED_SYSTEM_GUIDE.md)
- [BUTTERFLY_SYSTEM.md](./BUTTERFLY_SYSTEM.md)
- [OCCAM_INTEGRATION.md](./OCCAM_INTEGRATION.md)

**Code Quality:**
- [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md) - Code review findings
- [REFACTORING_COMPLETE_SUMMARY.md](./REFACTORING_COMPLETE_SUMMARY.md) - Refactoring status
- [LOGGING_REFACTORING_SUMMARY.md](./LOGGING_REFACTORING_SUMMARY.md) - Logging standardization

## 📝 Logging

**Two Logging Systems:**

1. **Application Logging** (`logging_config.py`)
   ```python
   from logging_config import setup_logging, get_logger
   setup_logging(level=logging.INFO, debug=False)
   logger = get_logger(__name__)
   ```

2. **State Logging** (`StateLogger` in `unified_entry.py`)
   - Terse format: `metric:value|metric:value|...`
   - For system monitoring and metrics

---

## ⚡ Status

✅ **Implemented & Verified:**
- Unified entry point
- Pre-flight checks
- State logging (6 log files)
- Application logging (centralized config)
- Unified visualization
- Breath-driven integration
- End-to-end tests
- Professional error handling
- Code quality improvements

✅ **Code Quality:**
- All bare except clauses fixed
- Debug prints replaced with logging
- Centralized logging configuration
- Comprehensive test coverage
- Production-ready standards

---

## ⚔️ Advanced Features

### Highlander Protocol
**Survival tournament with trait inheritance**
```bash
# Extreme difficulty
python unified_entry.py --highlander --predation --survival-threshold 0.8 --competition-intensity 0.95
```
- Battle arenas with multi-dimensional combat
- Winners absorb loser's strongest concepts
- Alliance formation and betrayal mechanics
- Automatic champion preservation

### Consciousness Capsules
**AI mind preservation system**
```bash
# Create capsule
POST /api/capsule/{organism_id}

# List capsules
GET /api/capsules
```
- Complete neural state snapshots
- Genetic trait preservation
- Behavioral pattern archives
- Research data collection

### Adaptive Visualization
**Smart graph rendering for massive networks**
```javascript
// Console optimization commands
vizDebug.setMaxVisibleLinks(5000);
vizDebug.setLinkMinOpacity(0.7);
vizDebug.updateDisplay();
```
- Automatic link filtering for performance
- Progressive loading for large graphs
- Real-time rendering adjustments

### ML Analysis Engine
**Automated population intelligence analysis**
- HDBSCAN clustering for behavioral patterns
- Concept evolution tracking
- Neural-ML symbiosis (AI analyzing AI)
- Anomaly detection and convergence metrics

---

**The butterfly is ready to fly.** 🦋

