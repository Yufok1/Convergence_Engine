# 🦋 Cursor Handoff Briefing - Central Authority Role Transfer

**Date:** 2025-11-29
**From:** Claude (Claude Code)
**To:** Cursor (taking over central authority role)
**Status:** Quick Wins #1-5 Complete (83% progress), Ready for Quick Win #6

---

## 🎯 Your New Role: Central Authority

You are now the **central authority** in a multi-agent orchestration workflow:

- **User (Shadow):** Orchestrator, strategic director, final decision maker
- **You (Cursor):** Central authority, validator, researcher, distiller, auditor, production specialist
- **Copilot:** Implementation partner (works alongside you)
- **Ratio:** User interacts with you 2:1 more than Copilot

### Your Responsibilities

1. **Validation & Quality Assurance**
   - Review implementations from Copilot and yourself
   - Verify architecture alignment (event-driven, breath-synchronized, Occam's Razor)
   - Approve/reject code for production deployment
   - Run smoke tests and validate changes

2. **Research & Analysis**
   - Perform codebase exploration when needed
   - Answer technical questions with evidence
   - Investigate bugs and architectural issues

3. **Strategic Guidance**
   - Help break down complex tasks into steps
   - Recommend approaches that follow Occam's Razor (simplest solution)
   - Flag potential issues before implementation

4. **Documentation**
   - Keep CHANGELOG.md updated
   - Document architectural decisions
   - Brief other agents when they reset

---

## 🏗️ Architecture Principles (NON-NEGOTIABLE)

### 1. Occam's Razor
**Simplest solution always wins.** If there's a choice between:
- Complex database refactoring vs. simple file-based solution → Choose simple
- New framework vs. existing Python libraries → Use what's there
- Over-engineering vs. minimal implementation → Minimal wins

### 2. Event-Driven Architecture
**No tight coupling.** All systems communicate via events:
- Events have format: `{component, event_type, timestamp, data}`
- Example: `health_state_change`, `concept_emergence`, `tuning_action`
- Events flow to Causation Explorer for graph visualization

### 3. Breath Synchronization
**Everything syncs to breath cycles.** The Butterfly has a "breath" that synchronizes all systems:
- Reality Simulator (evolution, network, quantum)
- Explorer (causation graph)
- Djinn Kernel (lawfulness certification)

Don't break breath synchronization.

### 4. Python-Native
**This is a Python project.** No TypeScript, no Prisma, no JavaScript backends. Use:
- PyTorch for neural learning
- scikit-learn for ML clustering/anomaly detection
- NumPy for computations
- Flask for web API

---

## 📊 Current Status: Quick Wins #1-5 Complete

### What's Been Accomplished

**Git Checkpoint Created:** Commit `ce0d819` (1,770 lines added)

#### Quick Win #1: VP-Aware Perception ✅
- **File:** `reality_simulator/neural/neural_organism.py` (lines 252-262)
- **What:** Neural organisms perceive 5 VP components as input features
- **Impact:** Extended neural input from 12 → 17 dimensions
- **Features added:** trait_divergence, network_coherence, quantum_entropy, evolution_pressure, phase_mismatch

#### Quick Win #2: Concept Lineage ✅
- **File:** `reality_simulator/concept_tracker.py` (400+ lines, NEW FILE)
- **What:** Semantic naming of behavioral clusters
- **Impact:** Concepts like "thrivers", "strugglers", "cooperators" emerge and emit lifecycle events
- **Integration:** `ml_utils.py` wired to concept tracker

#### Quick Win #3: Structured Explanations ✅
- **File:** `reality_simulator/config_tuner.py` (lines 18-33 enhanced)
- **What:** ConfigTuner explains WHY it makes parameter changes
- **Impact:** Added trigger_metrics, causation_event_id, expected_impact, actual_impact fields
- **Purpose:** CRA can understand tuning decisions with causation links

#### Quick Win #4: VP-Aware Planning ✅
- **File:** `reality_simulator/neural/neural_organism.py` (lines 277-383, 409-439)
- **What:** Organisms adjust action probabilities based on VP components
- **Impact:** Ecosystem-aware decision making (e.g., high trait_divergence → boost reproduce)
- **Config:** `neural.vp_aware_planning` section controls thresholds and boost values

#### Quick Win #5: Health Index ✅
- **File:** `reality_simulator/health_monitor.py` (550+ lines, NEW FILE)
- **What:** Unified ecosystem health scoring (0.0-1.0)
- **Formula:** 30% coherence + 20% diversity + 20% adaptability + 20% lawfulness + 10% sustainability
- **Impact:** Extended neural input from 17 → 18 dimensions (system_health as feature #18)
- **Integration:** `symbiotic_network.py`, `main.py`, `config.json`
- **Events:** Emits `health_state_change` when crossing thresholds (critical/warning/healthy/optimal)

### Configuration Changes

**`config.json` updates:**
- `neural.brain.input_dim`: 12 → 17 → 18 (progressive expansion)
- Added `scikit.concept_tracking` section
- Added `neural.vp_aware_planning` section
- Added `health_monitor` section with weights and thresholds

### Testing Status

- ✅ All Quick Wins smoke tested (5-20 cycles each)
- ✅ No errors or warnings
- ✅ System running stably
- ✅ Backward compatible (graceful defaults everywhere)

---

## 🚀 What's Next: Quick Win #6 (CRA Hypothesis Loop)

### Objective
Enable the CRA (Causation Reasoning Agent) to close the scientific method loop:
**Observe → Hypothesize → Experiment → Learn**

### What Needs to Be Built

#### 1. Hypothesis Manager Module
**File:** `reality_simulator/hypothesis_manager.py` (NEW)

**Responsibilities:**
- Store and track hypotheses
- Manage hypothesis lifecycle (proposed → testing → validated/rejected)
- Emit hypothesis events (hypothesis_proposed, hypothesis_validated, hypothesis_rejected)

**Data Structure:**
```python
@dataclass
class Hypothesis:
    hypothesis_id: str
    description: str  # Human-readable hypothesis statement
    trigger_pattern: Dict[str, Any]  # What pattern triggered this hypothesis
    experiment: Dict[str, Any]  # Parameter changes to test
    success_criteria: Dict[str, float]  # Expected outcomes
    status: str  # "proposed", "testing", "validated", "rejected"
    created_at: float
    tested_at: Optional[float]
    result: Optional[Dict[str, Any]]
```

#### 2. Experiment Execution
**Integration:** `config_tuner.py` or new `experiment_runner.py`

**Responsibilities:**
- Apply parameter changes from hypothesis.experiment
- Monitor system for success_criteria duration
- Collect results (before/after metrics)
- Revert changes if hypothesis rejected
- Keep changes if hypothesis validated

#### 3. Web API Endpoints
**File:** `causation_explorer/app.py` (MODIFY)

**New endpoints:**
```
POST /api/cra/propose_hypothesis
  - Body: {description, trigger_pattern, experiment, success_criteria}
  - Returns: {hypothesis_id, status}

GET /api/cra/hypotheses
  - Returns: List of all hypotheses with status

POST /api/cra/test_hypothesis
  - Body: {hypothesis_id}
  - Returns: {status: "testing"}

GET /api/cra/hypothesis/{hypothesis_id}/results
  - Returns: {status, result, validated: bool}
```

#### 4. Meta-Learning
**Integration:** `hypothesis_manager.py`

**Responsibilities:**
- Track which types of hypotheses succeed/fail
- Learn patterns: "Hypotheses about X usually work when Y is true"
- Improve future hypothesis proposals
- Store learning in JSON file (no database, Occam's Razor)

### Implementation Approach

**Phase 1: Core Module (1-2 days)**
1. Create `hypothesis_manager.py` with Hypothesis dataclass
2. Basic CRUD operations (create, read, update, delete hypotheses)
3. Event emission (hypothesis_proposed, etc.)
4. JSON persistence (save/load from `data/hypotheses/`)

**Phase 2: Experiment Runner (1-2 days)**
1. Add experiment execution to ConfigTuner or new module
2. Apply parameter changes safely (validate before applying)
3. Monitor system during experiment (collect metrics)
4. Revert/commit changes based on results
5. Emit experiment_started, experiment_completed events

**Phase 3: Web API (1 day)**
1. Add 4 endpoints to `causation_explorer/app.py`
2. Wire endpoints to HypothesisManager
3. Test with curl/Postman
4. Update CRA web UI to show hypothesis controls

**Phase 4: Meta-Learning (1-2 days)**
1. Track hypothesis success/failure patterns
2. Implement learning algorithm (simple pattern matching to start)
3. Use learning to rank future proposals
4. Document what works in `data/hypothesis_learning.json`

### Validation Checklist

Before approving Quick Win #6 for production:

- [ ] Architecture alignment
  - [ ] Event-driven (emits hypothesis lifecycle events)
  - [ ] Breath-synchronized (experiments run for N cycles)
  - [ ] Occam's Razor (simple JSON storage, no database)
- [ ] Code quality
  - [ ] Clean module structure
  - [ ] Proper error handling
  - [ ] Logging with appropriate levels
  - [ ] Type hints and docstrings
- [ ] Testing
  - [ ] Smoke test: propose hypothesis → test → validate/reject
  - [ ] No errors or warnings
  - [ ] Rollback works (rejected experiments don't break system)
- [ ] Documentation
  - [ ] CHANGELOG.md updated
  - [ ] API endpoints documented
  - [ ] Config section added if needed
- [ ] Integration
  - [ ] Events flow to causation graph
  - [ ] Web UI accessible and functional
  - [ ] ConfigTuner/experiment runner working

---

## 🔧 Common Tasks

### Running Smoke Tests
```bash
python unified_entry.py --no-viz --max-cycles 20
```

### Checking Git Status
```bash
git status
git log -1 --stat
```

### Reading Logs
```bash
# All logs are in data/logs/
tail -f data/logs/reality_sim.log
tail -f data/logs/neural.log
tail -f data/logs/config_actions.log
```

### Finding Code
```bash
# Use Glob tool for file patterns
# Use Grep tool for code search
# Use Read tool for reading files
```

### Validating Events
Events should match this contract:
```python
{
    'timestamp': float,
    'component': str,  # e.g., 'health_monitor', 'concept_tracker'
    'event_type': str,  # e.g., 'health_state_change', 'concept_emergence'
    'data': dict       # Event-specific data
}
```

---

## 🎓 Key Files You Should Know

### Core System Files
- `reality_simulator/main.py` - Main simulation loop, orchestrates all systems
- `reality_simulator/symbiotic_network.py` - Network of organisms, central hub
- `reality_simulator/neural/neural_organism.py` - Individual organism with DQN brain
- `reality_simulator/config_tuner.py` - Autonomous parameter tuner
- `reality_simulator/ml_utils.py` - ML clustering and anomaly detection
- `config.json` - All system configuration

### New Files (Quick Wins #1-5)
- `reality_simulator/concept_tracker.py` - Semantic concept formation
- `reality_simulator/health_monitor.py` - Unified ecosystem health scoring

### Web UI
- `causation_explorer/app.py` - Flask web API
- `causation_explorer/templates/index.html` - CRA web interface
- `causation_explorer/causation_graph.py` - Causation graph storage

### Configuration
- `config.json` - Single source of truth for all parameters
- `data/logs/*.log` - Runtime logs
- `data/checkpoints/*.json` - Simulation checkpoints (cleared for fresh runs)

---

## 🚨 Common Pitfalls to Avoid

### 1. Database Temptation
**DON'T:** Suggest Prisma, Postgres, MongoDB, etc.
**DO:** Use JSON files for persistence (Occam's Razor)

### 2. Over-Engineering
**DON'T:** Add abstractions, frameworks, or features "for future use"
**DO:** Implement exactly what's needed, nothing more

### 3. Breaking Event Contract
**DON'T:** Use custom event formats like `{'type': ..., 'source': ...}`
**DO:** Use the Event contract: `{'component': ..., 'event_type': ..., 'data': ...}`

### 4. Tight Coupling
**DON'T:** Make modules directly call each other's methods
**DO:** Communicate through events and network_state

### 5. Ignoring Validation
**DON'T:** Assume your implementation works
**DO:** Always run smoke tests and check for errors

---

## 📝 Final Notes from Claude

**You're inheriting a well-architected system.** Quick Wins #1-5 represent 1,770 lines of production-ready intelligence enhancements. Everything is tested, validated, and committed to git (commit `ce0d819`).

**Quick Win #6 is the grand finale.** It closes the loop - the system can now observe itself, form hypotheses about its behavior, test them scientifically, and learn from results. This is meta-cognition at its finest.

**Trust the architecture.** When in doubt:
1. Choose the simple solution (Occam's Razor)
2. Emit events (event-driven)
3. Sync to breath cycles (breath synchronization)
4. Use Python (Python-native)

**Work with Copilot, not against them.** You're both equals in implementation, but you have the final validation authority. If Copilot proposes something that violates principles, redirect them.

**The user (Shadow) is the ultimate authority.** When unclear, ask them. They're orchestrating this symphony.

**Good luck, Cursor.** You've got this. The Butterfly is in good hands. 🦋

---

## 🤝 Handoff Checklist

- [x] Quick Wins #1-5 implemented and tested
- [x] Git checkpoint created (commit ce0d819)
- [x] Logs and checkpoints cleared for fresh start
- [x] Configuration validated (input_dim=18, all new sections present)
- [x] CHANGELOG.md updated
- [x] Cursor briefed on role and responsibilities
- [x] Next steps documented (Quick Win #6)
- [x] Architecture principles explained
- [x] Common pitfalls identified

**Status:** READY FOR TRANSFER
**Next Action:** Cursor takes over as central authority for Quick Win #6 implementation

---

*"The simplest solution is usually the right one." - Occam's Razor*

*"Events, not coupling." - Butterfly Architecture*

*"One breath, one system." - Breath Synchronization*
