# 🔬 MEGA SWARM DEBUG MISSION - ROUND 2
## 8-Agent Parallel Audit (4x Grok + 4x Sonnet 4.5)
**Generated:** December 19, 2025
**Status:** ACTIVE - Fresh tree required for latest fixes

---

## 📋 ROUND 1 FIXES APPLIED (for context)

The following issues were fixed in Round 1 - verify they're working AND look for similar patterns elsewhere:

1. ✅ Trainer self-perception IndexError guard (`trainer.py`)
2. ✅ Fallback defaults 27→25 (`concept_system.py`, `utils.py`)
3. ✅ Population default 100→25 (`evolution_engine.py`)
4. ✅ Highlander interval 30→600 (`unified_entry.py`)
5. ✅ GerminationPool vocab bypass - clone/crossover/chimera strategies
6. ✅ Highlander vocab transfer bypass
7. ✅ Butterfly chat vocab pollution
8. ✅ Knowledge web bulk loading bypass
9. ✅ `link_word_to_node` missing organism parameter

---

## 🎯 AGENT ASSIGNMENTS

| Agent # | Model | Mission | Focus Area |
|---------|-------|---------|------------|
| **1** | Grok | Mastery Progression | Does mastery_level ever increment? |
| **2** | Grok | Config Path Audit | Are config paths consistent? |
| **3** | Grok | Nova & Edge Cases | Missing grounded checks? |
| **4** | Grok | Training Loop | Is learning actually happening? |
| **5** | Sonnet | Event System | Are causation events firing? |
| **6** | Sonnet | Memory Systems | Context/episodic memory flow |
| **7** | Sonnet | Battle Mechanics | Combat math & fairness |
| **8** | Sonnet | Data Flow & Wiring | Are systems actually connected? |

---

## 🎯 ROUND 2 FOCUS AREAS

We need DEEPER dives into systems that may have subtle bugs, race conditions, or logic errors that aren't immediately obvious from grep searches.

---

# GROK 1: ATOMIC LANGUAGE & MASTERY SYSTEM AUDIT

## Mission: Verify the mastery progression system actually works

The grounded language system gates vocabulary by mastery level (0-4). But does the progression actually happen? Are organisms stuck at level 0 forever?

### Files to Audit:
```
reality_simulator/language/atomic_language.py
reality_simulator/language/language_teacher.py
reality_simulator/neural/concept_tracker.py
```

### Critical Questions:

1. **Mastery Level Progression**
   - Find `mastery_level` - how does it increment?
   - What triggers level-up? Is it automatic or requires specific conditions?
   - Search for `mastery_level += 1` or `mastery_level = ` assignments
   - Is there a cap? What happens at level 4?

2. **can_use_word() Logic**
   - Find `can_use_word` method in atomic_language.py
   - What's the vocabulary limit at each level? (Should be: 0→6, 1→15, 2→50, 3→200, 4→unlimited)
   - Is the limit being enforced correctly?

3. **Concept Mastery Integration**
   - Does concept_tracker.py call atomic_language methods?
   - When a concept is "mastered", does vocabulary unlock?
   - Search for any disconnect between concept mastery and word unlocking

4. **Dead Code Check**
   - Are there mastery progression methods that are DEFINED but never CALLED?
   - Search for methods like `level_up`, `gain_mastery`, `unlock_vocabulary`

### Output Format:
```
MASTERY AUDIT REPORT
====================
Level Progression Trigger: [describe mechanism or "NOT FOUND"]
Methods That Increment Level: [list with line numbers]
Can_use_word Implementation: [correct/broken/missing]
Integration Issues: [list any disconnects]
Dead Code Found: [methods defined but never called]
```

---

# GROK 2: CONFIG PATH CONSISTENCY AUDIT

## Mission: Find all config access patterns and verify consistency

We have config paths like:
- `config.get('language', {}).get('grounded', {}).get('enabled', False)`
- `config.get('neural', {}).get('language', {}).get('grounded', {}).get('enabled', False)`

These are DIFFERENT PATHS. One is correct, one is wrong. Find all instances.

### Files to Audit:
```
**/*.py (all Python files)
config.json (canonical config structure)
```

### Critical Searches:

1. **Find All Grounded Mode Checks**
   ```
   grep for: grounded.*enabled
   grep for: get('grounded'
   grep for: ['grounded']
   ```

2. **Catalog Every Config Access Pattern**
   For each file, document:
   - What config path is used?
   - Does it match config.json structure?
   - Is there a fallback default?

3. **config.json Structure** (canonical source of truth)
   ```json
   {
     "language": {
       "grounded": {
         "enabled": true,
         "mastery_gating": true
       }
     }
   }
   ```
   vs
   ```json
   {
     "neural": {
       "language": {
         "grounded": { ... }
       }
     }
   }
   ```
   WHICH ONE IS ACTUALLY IN config.json?

4. **HighlanderProtocol Special Case**
   - Highlander receives a subset config (not full config)
   - Check what keys are actually in `self.config` for highlander
   - The fix used `self.config.get('neural', {}).get('language', {})...` - is 'neural' even in highlander's config?

### Output Format:
```
CONFIG PATH AUDIT
=================
Files Using 'language.grounded.enabled': [list]
Files Using 'neural.language.grounded.enabled': [list]
Files Using Other Paths: [list with paths]
config.json Actual Structure: [paste relevant section]
MISMATCHES FOUND: [critical - these are bugs]
```

---

# GROK 3: NOVA STRATEGY & EDGE CASES AUDIT

## Mission: Find the remaining germination strategies and edge cases

Round 1 fixed clone/crossover/chimera vocabulary bypasses. But what about:
- Nova strategy (random generation)?
- Edge cases in the fixed strategies?
- Other vocabulary manipulation we missed?

### Files to Audit:
```
reality_simulator/evolution/germination_pool.py
reality_simulator/evolution/highlander_protocol.py
reality_simulator/evolution/battle_arena.py
reality_simulator/evolution/alliance_warfare.py
```

### Critical Searches:

1. **Nova Strategy**
   - Find `_apply_nova_strategy` method
   - Does it set vocabulary? How?
   - Does it need a grounded mode check?

2. **Other Vocabulary Setters**
   ```
   grep for: vocabulary_words =
   grep for: vocabulary.add
   grep for: vocabulary.extend
   grep for: .vocabulary =
   ```

3. **Alliance Vocabulary Sharing**
   - Do alliances share vocabulary between members?
   - Search alliance_warfare.py for vocabulary manipulation
   - Check if alliance formation triggers word transfers

4. **Battle Rewards**
   - Does winning a battle grant vocabulary?
   - Check battle_arena.py for post-battle rewards
   - Look for any "loot" or "spoils" systems

5. **Resurrection/Respawn**
   - When organisms die and respawn, is vocabulary reset?
   - Check the full respawn flow in germination_pool.py
   - Verify `_inherited_vocabulary` handling

### Output Format:
```
EDGE CASE AUDIT
===============
Nova Strategy Vocabulary: [describe or "NEEDS FIX"]
Alliance Vocabulary Sharing: [found/not found] - [needs fix?]
Battle Rewards: [found/not found] - [needs fix?]
Respawn Vocabulary: [correctly reset/incorrectly inherited]
Other Vocabulary Setters Found: [list with line numbers]
```

---

# GROK 4: TRAINING LOOP & REWARD FLOW AUDIT

## Mission: Verify the neural training actually trains

Organisms have brains that should learn. But is the training loop actually running? Are rewards flowing correctly?

### Files to Audit:
```
reality_simulator/neural/trainer.py
reality_simulator/neural/neural_organism.py
unified_entry.py (training triggers)
reality_simulator/evolution/highlander_protocol.py (battle rewards)
```

### Critical Questions:

1. **Training Trigger**
   - When does `trainer.train()` or `trainer.train_step()` get called?
   - Is it called every tick? Every battle? Never?
   - Search unified_entry.py for training calls

2. **Experience Collection**
   - How do organisms collect experiences?
   - Is there an experience buffer/replay buffer?
   - Search for `experience`, `replay`, `buffer`, `memory`

3. **Reward Signal**
   - What rewards do organisms receive?
   - Battle win/loss rewards?
   - Fitness delta rewards?
   - Language success rewards?
   - Trace the reward flow from source to brain update

4. **Gradient Flow**
   - Is `loss.backward()` being called?
   - Is `optimizer.step()` being called?
   - Are gradients actually flowing? (not zeroed out or NaN)

5. **Learning Rate**
   - What's the learning rate?
   - Is it being scheduled/decayed?
   - Is it too low to see changes?

### Output Format:
```
TRAINING AUDIT
==============
Training Trigger Location: [file:line or "NOT FOUND"]
Training Frequency: [every tick/battle/generation/never]
Experience Buffer: [exists/missing] - [size if exists]
Reward Sources Found:
  - Battle: [yes/no] [value range]
  - Fitness: [yes/no] [value range]
  - Language: [yes/no] [value range]
Gradient Flow: [confirmed/broken/unknown]
Learning Rate: [value] [scheduled: yes/no]
CRITICAL ISSUES: [list any blockers to learning]
```

---

# GENERAL INSTRUCTIONS FOR ALL AGENTS

## Search Strategy
1. Start with the specific files listed
2. Use grep/search to find patterns
3. Trace call chains (who calls what)
4. Look for dead code (defined but never called)
5. Check for silent failures (try/except that swallows errors)

## Report Format
- Be SPECIFIC with file names and line numbers
- Include code snippets for bugs found
- Rate severity: CRITICAL / HIGH / MEDIUM / LOW
- Suggest fixes where possible

## What NOT to Report
- Style issues (formatting, naming conventions)
- Performance optimizations (unless critical)
- Feature requests
- Things that "could be better" but aren't bugs

## What TO Report
- Logic errors
- Dead code that should be alive
- Missing integrations
- Incorrect defaults
- Silent failures
- Race conditions
- Off-by-one errors

---

# ═══════════════════════════════════════════════════════════════════════════
# SONNET MISSIONS (Agents 5-8)
# ═══════════════════════════════════════════════════════════════════════════

---

# SONNET 5: EVENT SYSTEM & CAUSATION TRAIL AUDIT

## Mission: Verify events are actually being emitted and processed

The system has an event_emitter for causation tracking. But are events actually firing? Is anyone listening?

### Files to Audit:
```
causation_explorer.py
causation_web_ui.py
unified_entry.py (event wiring)
reality_simulator/neural/neural_organism.py (event emission)
reality_simulator/evolution/highlander_protocol.py (battle events)
```

### Critical Questions:

1. **Event Emitter Wiring**
   - Search for `event_emitter` parameter in constructors
   - Is it passed down the chain? Or does it stop at some level?
   - Find places where `event_emitter` is None when it shouldn't be

2. **Event Emission Points**
   - Search for `self.event_emitter(` calls
   - Are they guarded with `if self.event_emitter:`?
   - What events are defined but never emitted?

3. **Causation Explorer Integration**
   - Does CausationExplorer receive events?
   - Is it connected to the visualization?
   - Search for `causation_explorer` usage in unified_entry.py

4. **Silent Event Failures**
   - Are there try/except blocks around event emission that swallow errors?
   - Could events be failing silently?

5. **Event Types**
   - What event types exist? (`neural_decision`, `battle_result`, `vocabulary_learned`, etc.)
   - Are they documented?
   - Are any defined but never used?

### Output Format:
```
EVENT SYSTEM AUDIT
==================
Event Emitter Wired: [yes/partial/no]
Components Missing Emitter: [list]
Events Defined: [list event types]
Events Actually Emitted: [list with file:line]
Events Never Emitted: [list - dead code]
Causation Explorer Connected: [yes/no]
Silent Failures Found: [list]
```

---

# SONNET 6: MEMORY SYSTEMS AUDIT

## Mission: Verify context_memory and episodic memory are functioning

The system has multiple memory types. Are they being written to AND read from?

### Files to Audit:
```
reality_simulator/memory/context_memory.py
reality_simulator/memory/episodic_memory.py (if exists)
reality_simulator/neural/neural_organism.py (memory access)
reality_simulator/language/language_teacher.py (memory writes)
```

### Critical Questions:

1. **Context Memory Population**
   - When are word embeddings created?
   - Search for `update_word_embedding`, `link_word_to_node`
   - Is the memory actually being populated or staying empty?

2. **Memory Retrieval**
   - Who reads from context_memory?
   - Search for `get_word_embedding`, `get_context`
   - Are reads happening? Or is data written but never read?

3. **Episodic Memory**
   - Does episodic_memory.py exist? Is it used?
   - Search for `episodic` across codebase
   - Is episodic memory connected to anything?

4. **Memory Persistence**
   - Is memory saved to disk?
   - Search for `save`, `load`, `persist`, `checkpoint`
   - Does memory survive restarts?

5. **Memory Size/Limits**
   - Are there memory limits?
   - What happens when limits are exceeded?
   - Search for `max_size`, `capacity`, `prune`, `cleanup`

### Output Format:
```
MEMORY AUDIT
============
Context Memory:
  - Write Locations: [file:line list]
  - Read Locations: [file:line list]
  - Write:Read Ratio: [X:Y]
  - Persistence: [yes/no]
Episodic Memory:
  - Exists: [yes/no]
  - Connected: [yes/no]
  - Used By: [list or "nothing"]
Memory Limits:
  - Defined: [yes/no]
  - Enforced: [yes/no]
ISSUES: [data written but never read, etc.]
```

---

# SONNET 7: BATTLE MECHANICS AUDIT

## Mission: Verify battle math is fair and correct

Battles determine organism survival. Is the math right? Are there exploits?

### Files to Audit:
```
reality_simulator/evolution/battle_arena.py
reality_simulator/evolution/highlander_protocol.py
reality_simulator/evolution/alliance_warfare.py
```

### Critical Questions:

1. **Battle Outcome Calculation**
   - How is winner determined?
   - What factors contribute? (fitness, neural output, randomness)
   - Is there a formula? Find it.

2. **Fairness Check**
   - Can a weak organism ever beat a strong one?
   - Is there too much randomness? Too little?
   - Search for `random`, `chaos`, `luck`

3. **Battle Type Selection**
   - What battle types exist? (FULL_COMBAT, PROTON_GAME, etc.)
   - How is type selected?
   - Are all types actually implemented?

4. **Alliance Effects**
   - Do alliances affect battle outcomes?
   - Search for alliance bonuses/penalties
   - Is 2v1 possible? How is it handled?

5. **Death & Elimination**
   - What triggers organism death?
   - Is there a minimum population check?
   - Can the last organism die? (extinction bug)

6. **Reward Distribution**
   - What does the winner get?
   - What does the loser lose?
   - Are rewards balanced?

### Output Format:
```
BATTLE AUDIT
============
Winner Formula: [describe or paste code]
Factors: [fitness: X%, neural: Y%, random: Z%]
Battle Types: [list with implementation status]
Alliance Effects: [describe or "none"]
Extinction Protection: [yes/no]
Fairness Assessment: [fair/unfair - why]
EXPLOITS FOUND: [any ways to game the system]
```

---

# SONNET 8: DATA FLOW & WIRING AUDIT

## Mission: Verify all systems are actually connected

The codebase has many systems. Are they wired together? Or are there orphaned components?

### Files to Audit:
```
unified_entry.py (main wiring hub)
reality_simulator/symbiotic_network.py
reality_simulator/evolution/evolution_engine.py
```

### Critical Questions:

1. **Component Initialization Order**
   - What order are components created in unified_entry.py?
   - Are there dependencies that might not be ready?
   - Search for "None" checks that indicate missing wiring

2. **Reference Passing**
   - How do components get references to each other?
   - Search for `set_`, `register_`, `connect_`
   - Are there circular dependencies?

3. **Orphaned Systems**
   - Find classes that are defined but never instantiated
   - Find methods that are defined but never called
   - These are dead code or missing integrations

4. **The Main Loop**
   - What does one "tick" of the simulation do?
   - Find the main loop in unified_entry.py
   - Trace what gets called each tick

5. **Initialization vs Runtime**
   - Are there things set up at init that never run?
   - Are there runtime methods never triggered?
   - Search for `# TODO`, `# FIXME`, `pass` statements

6. **System References**
   - Do organisms have access to the systems they need?
   - Check `_alliance_warfare_ref`, `_causation_explorer_ref`
   - Are these None when they shouldn't be?

### Output Format:
```
WIRING AUDIT
============
Component Init Order: [list in order]
Dependency Issues: [components initialized before dependencies]
Orphaned Classes: [defined but never used]
Orphaned Methods: [defined but never called]
Main Loop Actions: [what happens each tick]
Missing Connections:
  - [component A] needs [component B] but doesn't have it
Reference Issues:
  - [list of None refs that should be set]
```

---

## 📊 SUBMISSION TEMPLATE (ALL AGENTS)

```
AGENT [N] - [MISSION NAME]
==========================

SUMMARY: [1-2 sentence overview]

FINDINGS:

Issue 1: [Title]
Severity: [CRITICAL/HIGH/MEDIUM/LOW]
File: [path]
Line: [number]
Description: [what's wrong]
Code: [snippet]
Fix: [suggested fix]

Issue 2: ...

VERIFIED WORKING:
- [thing that was checked and is correct]
- [another thing]

NEEDS FURTHER INVESTIGATION:
- [thing that's suspicious but uncertain]
```

---

## 🚨 PRIORITY TARGETS BY AGENT

| Agent | Priority Question | If Answer is Bad... |
|-------|-------------------|---------------------|
| **Grok 1** | Does mastery_level ever increment? | Grounded mode is useless |
| **Grok 2** | Is highlander using right config path? | Grounded checks silently fail |
| **Grok 3** | Does nova strategy bypass grounded mode? | Free vocabulary exploit |
| **Grok 4** | Is training actually happening? | Brains never learn |
| **Sonnet 5** | Are events being emitted? | Causation tracking is dead |
| **Sonnet 6** | Is memory being read? | All memory writes are wasted |
| **Sonnet 7** | Is battle math fair? | Evolution is broken |
| **Sonnet 8** | Are systems connected? | Components work in isolation |

---

## 🎯 QUICK REFERENCE

**Config.json location:** `config.json` (root)
**Main entry:** `unified_entry.py`
**Neural core:** `reality_simulator/neural/`
**Evolution:** `reality_simulator/evolution/`
**Language:** `reality_simulator/language/`
**Memory:** `reality_simulator/memory/`

**Key Config Values:**
- `language.grounded.enabled: true` - Grounded mode ON
- `neural.input_dim: 25` - State vector size (NOT 28)
- `population.default_size: 25` - Starting organisms
- `highlander.eval_interval_seconds: 600` - 10 min between culls

---

Good hunting, swarm! 🎯🐝
