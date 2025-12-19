# 🔥 MEGA SWARM DEBUG MISSION - ROUND 3
## 8-Agent Deep Dive (4x Grok + 4x Sonnet)
**Generated:** December 19, 2025
**Status:** ACTIVE - We're on a roll! 16 bugs fixed so far!

---

## 📋 ROUNDS 1 & 2 FIXES APPLIED

### Round 1 (10 fixes):
- ✅ Trainer self-perception IndexError guard
- ✅ Fallback defaults 27→25 (concept_system, utils)
- ✅ Population default 100→25 (evolution_engine)
- ✅ Highlander interval 30→600 (unified_entry)
- ✅ GerminationPool vocab bypass (clone/crossover/chimera)
- ✅ Highlander vocab transfer bypass
- ✅ Butterfly chat vocab pollution
- ✅ Knowledge web bulk loading bypass
- ✅ link_word_to_node missing organism parameter

### Round 2 (6 fixes):
- ✅ Nova strategy grounded check added
- ✅ Highlander config path fixed (neural.language → language)
- ✅ CausationEvent → Event import fix
- ✅ Memory leak - cleanup_dead_organism now called
- ✅ SwarmBattle event pattern fixed
- ✅ DroneWarfare event pattern fixed

---

## 🎯 ROUND 3 AGENT ASSIGNMENTS

| Agent # | Model | Mission | Target |
|---------|-------|---------|--------|
| **1** | Grok | Proton Game Audit | Is the language game actually playable? |
| **2** | Grok | Alliance System Deep Dive | Do alliances actually DO anything? |
| **3** | Grok | Breath Engine Audit | Is the breath cycle controlling anything? |
| **4** | Grok | Organism Lifecycle | Birth → Death flow complete? |
| **5** | Sonnet | Language Model Head | Does token generation work? |
| **6** | Sonnet | Checkpoint/Capsule System | Can organisms be saved/restored? |
| **7** | Sonnet | VP (Visceral Priority) System | Is VP affecting decisions? |
| **8** | Sonnet | Dead Code Hunter | Find the zombies! |

---

# GROK 1: PROTON GAME AUDIT

## Mission: Verify the language game is actually functional

Proton Game is supposed to be a language-based battle type. But does it work?

### Files to Audit:
```
reality_simulator/arena/proton_game.py
reality_simulator/arena/battle_arena.py (proton integration)
reality_simulator/evolution/highlander_protocol.py (battle type selection)
```

### Critical Questions:

1. **Game Mechanics**
   - What ARE the Proton Game rules?
   - How do organisms compete linguistically?
   - Is there a scoring system?

2. **Battle Integration**
   - When is PROTON_GAME selected vs FULL_COMBAT?
   - Search for `proton_game_probability` usage
   - Is the game actually instantiated and run?

3. **Language Requirements**
   - Does Proton Game require vocabulary?
   - What happens if organisms have NO words (grounded mode level 0)?
   - Is there a fallback?

4. **Winner Determination**
   - How does Proton Game decide who wins?
   - Is it fair? Can mute organisms win?
   - What's the reward for winning?

5. **Dead Code Check**
   - Is ProtonGame class instantiated anywhere?
   - Search for `ProtonGame(` constructor calls
   - Are there methods defined but never called?

### Output Format:
```
PROTON GAME AUDIT
=================
Game Rules: [describe or "UNCLEAR"]
Battle Integration: [connected/orphaned]
Language Requirement: [required/optional/handled]
Winner Formula: [describe]
Instantiation Sites: [list or "NONE FOUND"]
VERDICT: [WORKING/BROKEN/DEAD CODE]
```

---

# GROK 2: ALLIANCE SYSTEM DEEP DIVE

## Mission: Verify alliances actually affect gameplay

Alliances are formed, but do they DO anything?

### Files to Audit:
```
reality_simulator/evolution/alliance_warfare.py
reality_simulator/evolution/highlander_protocol.py
reality_simulator/evolution/battle_arena.py
unified_entry.py (alliance wiring)
```

### Critical Questions:

1. **Alliance Formation**
   - How are alliances formed?
   - What triggers alliance creation?
   - Can organisms choose their allies?

2. **Alliance Benefits**
   - Do allies help each other in battles?
   - Is there resource sharing?
   - Do allies avoid fighting each other?

3. **Alliance Mechanics in Battle**
   - Search for `alliance` in battle_arena.py
   - Are there 2v1 scenarios?
   - Do alliances affect battle selection?

4. **Germination Wave Alliances**
   - New organisms are supposed to be allied as a "generation cohort"
   - Is this actually happening?
   - Does it help them survive?

5. **Alliance Dissolution**
   - When do alliances end?
   - What happens when an ally dies?
   - Can organisms betray allies?

### Output Format:
```
ALLIANCE AUDIT
==============
Formation Trigger: [describe mechanism]
Benefits Found:
  - Battle help: [yes/no]
  - Resource sharing: [yes/no]
  - Fight avoidance: [yes/no]
Alliance in Battle: [affects outcome/ignored]
Wave Alliances: [working/broken]
VERDICT: [MEANINGFUL/COSMETIC/BROKEN]
```

---

# GROK 3: BREATH ENGINE AUDIT

## Mission: Verify the breath cycle is actually controlling behavior

The system has a "breath engine" that's supposed to pace everything. Is it real?

### Files to Audit:
```
reality_simulator/breath_engine.py (if exists)
unified_entry.py (breath integration)
reality_simulator/neural/trainer.py (breath-aware training)
reality_simulator/symbiotic_network.py (breath state)
```

### Critical Questions:

1. **Breath Engine Location**
   - Does `breath_engine.py` exist?
   - Or is breath integrated into something else?
   - Find where breath state is calculated

2. **Breath State Components**
   - What IS breath state? (phase, depth, rhythm?)
   - How is it calculated?
   - What's the cycle period?

3. **Breath Affects Training**
   - Round 2 found training is breath-aware
   - HOW does breath affect training?
   - Is it meaningful or cosmetic?

4. **Breath Affects Decisions**
   - Do organisms breathe?
   - Does breath_state influence organism actions?
   - Search for `breath` in neural_organism.py

5. **Djinn Kernel Integration**
   - What's the relationship between breath and Djinn?
   - Does Djinn Kernel control breath?
   - Search for `djinn` + `breath` connections

### Output Format:
```
BREATH ENGINE AUDIT
===================
Engine Location: [file:line or "INTEGRATED INTO X"]
Breath Components: [list: phase, depth, etc.]
Cycle Period: [X seconds or "UNKNOWN"]
Training Effect: [describe or "COSMETIC"]
Decision Effect: [describe or "NONE"]
Djinn Connection: [yes/no - describe]
VERDICT: [FUNCTIONAL/COSMETIC/BROKEN]
```

---

# GROK 4: ORGANISM LIFECYCLE AUDIT

## Mission: Trace the complete birth-to-death flow

An organism is born, lives, fights, maybe reproduces, and dies. Is this flow complete?

### Files to Audit:
```
reality_simulator/neural/neural_organism.py
reality_simulator/evolution/germination_pool.py
reality_simulator/evolution/highlander_protocol.py
reality_simulator/symbiotic_network.py
unified_entry.py
```

### Critical Questions:

1. **Birth Flow**
   - Germination creates candidate → ??? → Living organism
   - What's the missing step?
   - Where does `organism_factory` come from?
   - Search for `organism_factory` definition

2. **Life Flow**
   - What does an organism DO each tick?
   - Is there a main `update()` or `step()` method?
   - Trace one tick of organism behavior

3. **Battle Flow**
   - How is an organism selected for battle?
   - What happens during battle?
   - What's passed to the organism?

4. **Death Flow**
   - What triggers death?
   - Is cleanup complete? (memory, connections, events)
   - Are there zombie organisms?

5. **Reproduction Flow**
   - Can organisms reproduce directly?
   - Or only through germination on death?
   - Search for `reproduce`, `offspring`, `spawn`

### Output Format:
```
LIFECYCLE AUDIT
===============
Birth Chain: [germination → ??? → organism]
Per-Tick Actions: [list what happens each tick]
Battle Selection: [random/fitness/other]
Death Triggers: [list]
Cleanup Complete: [yes/no - what's missing]
Reproduction: [direct/germination-only/broken]
GAPS FOUND: [missing lifecycle steps]
```

---

# SONNET 5: LANGUAGE MODEL HEAD AUDIT

## Mission: Verify token generation actually works

Organisms have a language head for generating tokens. Does it produce anything?

### Files to Audit:
```
reality_simulator/neural/brain.py (language head)
reality_simulator/neural/neural_organism.py (generate_tokens)
reality_simulator/language/butterfly_chat.py (response generation)
reality_simulator/language/language_vocabulary.py
```

### Critical Questions:

1. **Language Head Architecture**
   - Find `fc_language` or `language_head` in brain.py
   - What's the architecture? (input → hidden → vocab_size?)
   - Is it actually instantiated?

2. **Token Generation**
   - Find `generate_tokens` method
   - How does it work? (argmax? sampling? beam search?)
   - What's the max sequence length?

3. **Vocabulary Integration**
   - How does brain output map to words?
   - Is vocabulary connected to language head?
   - What if vocab size doesn't match head output?

4. **Response Quality**
   - In butterfly_chat, what do organisms actually say?
   - Are responses coherent or random?
   - Is there temperature/sampling control?

5. **Grounded Mode Impact**
   - In grounded mode, organisms have limited vocab
   - How does this affect token generation?
   - Can they generate tokens for words they don't "know"?

### Output Format:
```
LANGUAGE HEAD AUDIT
===================
Architecture: [describe or "NOT FOUND"]
Generation Method: [argmax/sampling/other]
Vocab Connection: [connected/broken]
Response Quality: [coherent/random/empty]
Grounded Impact: [properly limited/bypassed]
VERDICT: [GENERATES LANGUAGE/BROKEN/COSMETIC]
```

---

# SONNET 6: CHECKPOINT/CAPSULE SYSTEM AUDIT

## Mission: Verify organisms can be saved and restored

OrganismCapsuleManager is supposed to checkpoint champions. Does it work?

### Files to Audit:
```
reality_simulator/evolution/organism_capsule.py (if exists)
reality_simulator/evolution/germination_pool.py (phoenix strategy)
reality_simulator/evolution/highlander_protocol.py (champion saving)
unified_entry.py (capsule manager init)
```

### Critical Questions:

1. **Capsule Creation**
   - Where is OrganismCapsuleManager defined?
   - When are capsules created?
   - What's saved in a capsule?

2. **Capsule Contents**
   - Neural weights saved?
   - Vocabulary saved?
   - Concepts/atoms saved?
   - Traits saved?

3. **Phoenix Restoration**
   - Phoenix strategy resurrects from capsules
   - Does it restore EVERYTHING?
   - Or just partial state?

4. **Persistence**
   - Are capsules saved to disk?
   - Can you restart and restore champions?
   - Search for capsule file I/O

5. **Champion Selection**
   - Who gets capsule'd?
   - Is it the winner of each round?
   - Or some other criteria?

### Output Format:
```
CAPSULE AUDIT
=============
Capsule Manager Location: [file:line or "NOT FOUND"]
Creation Trigger: [describe]
Contents Saved:
  - Neural: [yes/no]
  - Vocabulary: [yes/no]
  - Concepts: [yes/no]
  - Traits: [yes/no]
Phoenix Restoration: [complete/partial/broken]
Disk Persistence: [yes/no]
VERDICT: [CHECKPOINTING WORKS/PARTIAL/BROKEN]
```

---

# SONNET 7: VP (VISCERAL PRIORITY) SYSTEM AUDIT

## Mission: Verify VP actually affects organism behavior

VP is supposed to be a key differentiator. But does it DO anything?

### Files to Audit:
```
reality_simulator/djinn_kernel.py (VP calculation)
reality_simulator/neural/neural_organism.py (VP usage)
reality_simulator/neural/trainer.py (VP in rewards)
reality_simulator/neural/brain.py (VP in attention)
unified_entry.py (VP wiring)
```

### Critical Questions:

1. **VP Calculation**
   - How is VP calculated?
   - What inputs affect VP?
   - Is it per-organism or global?

2. **VP Range**
   - What's the VP value range? (0-1? -1 to 1?)
   - What's typical VP during runtime?
   - Are there VP extremes?

3. **VP Affects Attention**
   - Brain.py has VP-aware attention
   - HOW does VP change attention?
   - High VP = more focused? More random?

4. **VP Affects Rewards**
   - Does VP modify reward shaping?
   - Search for `vp` in trainer.py reward calculation
   - Is VP bonus/penalty meaningful?

5. **VP Affects Decisions**
   - Does organism.decide_action use VP?
   - Is VP passed through the decision chain?
   - Or is it calculated but ignored?

### Output Format:
```
VP AUDIT
========
Calculation Location: [file:line]
Calculation Formula: [describe or "UNKNOWN"]
Value Range: [min-max]
Attention Effect: [describe or "NONE"]
Reward Effect: [describe or "NONE"]
Decision Effect: [describe or "NONE"]
VERDICT: [VP IS MEANINGFUL/COSMETIC/BROKEN]
```

---

# SONNET 8: DEAD CODE HUNTER

## Mission: Find zombies - code that exists but never runs

Every codebase has dead code. Find it and report it.

### Strategy:

1. **Orphaned Classes**
   - Find classes that are DEFINED but never INSTANTIATED
   - Search for `class FooBar` then search for `FooBar(`
   - If constructor never called = dead

2. **Orphaned Methods**
   - Find public methods never called
   - Especially in key files:
     - unified_entry.py
     - neural_organism.py
     - symbiotic_network.py
     - trainer.py

3. **TODO/FIXME/HACK Comments**
   - Search for `# TODO`, `# FIXME`, `# HACK`, `# XXX`
   - These indicate incomplete features
   - List them with context

4. **Empty Implementations**
   - Search for `pass` as sole method body
   - Search for `raise NotImplementedError`
   - Search for `return None  # TODO`

5. **Commented Out Code**
   - Large blocks of `# ` commented code
   - Especially if it looks like it was important

6. **Unused Imports**
   - Imports at top of file never used
   - (Don't list every one, just patterns)

### Output Format:
```
DEAD CODE AUDIT
===============
Orphaned Classes:
  - [ClassName] in [file] - never instantiated

Orphaned Methods:
  - [method_name] in [file:line] - never called

TODO/FIXME Comments (top 10):
  - [file:line] - "[comment text]"

Empty Implementations:
  - [file:line] - [method_name] - just `pass`

Large Commented Blocks:
  - [file:line-range] - "[description of what it was]"

ESTIMATED DEAD CODE: [X lines / Y%]
```

---

# GENERAL INSTRUCTIONS FOR ALL AGENTS

## Search Strategy
1. Start with the specific files listed
2. Use grep/search to find patterns
3. TRACE CALL CHAINS - who calls what
4. Follow the data - where does X come from?
5. Check for silent failures (try/except that swallows)

## Report Format
- Be SPECIFIC with file names and line numbers
- Include code snippets for bugs found
- Rate severity: CRITICAL / HIGH / MEDIUM / LOW
- Suggest fixes where possible

## What TO Report
- Logic errors
- Dead code that should be alive
- Missing integrations
- Features that are cosmetic (look good but do nothing)
- Race conditions
- Silent failures

## What NOT to Report
- Style issues
- Performance (unless critical)
- Feature requests

---

## 📊 SUBMISSION TEMPLATE

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

NEEDS FURTHER INVESTIGATION:
- [thing that's suspicious but uncertain]
```

---

## 🚨 ROUND 3 PRIORITY QUESTIONS

| Agent | Key Question | Implication |
|-------|-------------|-------------|
| **Grok 1** | Is Proton Game playable? | Language battles may be fake |
| **Grok 2** | Do alliances affect anything? | Social system may be cosmetic |
| **Grok 3** | Does breath control timing? | Pacing system may be fake |
| **Grok 4** | Is lifecycle complete? | Organisms may be stuck/leaked |
| **Sonnet 5** | Does language head generate? | Organisms may be mute |
| **Sonnet 6** | Do capsules restore fully? | Champions may lose state |
| **Sonnet 7** | Does VP affect behavior? | Core mechanic may be fake |
| **Sonnet 8** | How much dead code? | Maintenance burden |

---

## 🎯 QUICK REFERENCE

**Key Files:**
- `unified_entry.py` - Main orchestration
- `reality_simulator/neural/neural_organism.py` - Organism brain
- `reality_simulator/evolution/highlander_protocol.py` - Tournament
- `reality_simulator/symbiotic_network.py` - Network topology
- `reality_simulator/neural/trainer.py` - Learning
- `reality_simulator/language/butterfly_chat.py` - Chat interface

**Key Config:**
- `language.grounded.enabled: true` - Grounded mode ON
- `neural.input_dim: 25` - State vector size
- `population.default_size: 25` - Starting organisms
- `highlander.eval_interval_seconds: 600` - 10 min culling

---

## 🔥 LET'S GOOOOO!

16 bugs fixed so far. Let's find more!

The goal: Make sure EVERY system is either:
1. **WORKING** - and we verified it
2. **BROKEN** - and we know how to fix it
3. **DEAD** - and we can delete it

No more mystery code. No more "I think this works." CERTAINTY.

Good hunting, swarm! 🐝🔥
