# SWARM DEBUG ROUND 4: Mastery Advancement System

## Problem Statement
Organisms in GROUNDED LANGUAGE MODE never advance past level 0. The mastery advancement system exists but is completely disconnected from the main simulation loop.

### What Should Happen:
- Level 0: 6 words (ACTION_HEADS: move, cooperate, compete, rest, reproduce, isolate)
- Level 1: 26 words (+20 core state/relationship)
- Level 2: 76 words (+50 extended concepts)
- Level 3: 276 words (+200 pool words)
- Level 4: 20000 (semantic graduation)

### What Actually Happens:
- All organisms stay at level 0 forever
- `atomic_language.record_experience()` is NEVER called during simulation
- `atomic_language.try_advance_mastery()` is NEVER called during simulation
- These functions ONLY get called in butterfly_chat.py (chat interface)

---

# AGENT ASSIGNMENTS

---

## GROK 1: Simulation Loop Integration Points

**Your Mission**: Find WHERE in the simulation loop mastery advancement should be hooked in.

**Files to Investigate**:
- `reality_simulator/symbiotic_network.py` - Main simulation orchestrator
- `unified_entry.py` - Entry point and cycle runner

**Specific Tasks**:
1. Find the `step()` method in symbiotic_network.py - trace the full tick lifecycle
2. Find `_run_behavior_step()` - when organisms take actions
3. Find `_process_token_exchanges()` - when organisms interact
4. Find where Language Teacher is called (around line 1592-1603)
5. Identify the BEST insertion point for calling `try_advance_mastery()` on all organisms

**Questions to Answer**:
- How often does `step()` get called? Every tick? Every generation?
- Is there already a per-organism loop we can hook into?
- Where is the generation counter incremented?

**Report Format**:
```
INTEGRATION POINT FOUND:
- File: [path]
- Method: [name]
- Line: [number]
- Recommended insertion: [description]
- Frequency: [how often this runs]
```

---

## GROK 2: Experience Recording - What Counts?

**Your Mission**: Determine what events should trigger `atomic_language.record_experience()`.

**Files to Investigate**:
- `reality_simulator/language/atomic_language.py` - lines 1308-1310, 1403-1450
- `reality_simulator/neural/neural_organism.py` - line 1408+ (different record_experience!)
- `reality_simulator/symbiotic_network.py` - organism interaction events

**Specific Tasks**:
1. Read `check_mastery_advancement()` (line 1403) - understand the criteria
2. Find what `_total_experiences` is supposed to track
3. Find `_mastery_min_experiences` config: `[50, 200, 500, 1000]` - what do these numbers mean?
4. Identify all organism interaction types that should count as "experience"
5. Check if `neural_organism.record_experience()` and `atomic_language.record_experience()` are related or independent

**Questions to Answer**:
- Should experience be recorded on: action taken? cooperation? competition? teaching received? generation survived?
- Are the min_experiences thresholds reasonable? (50 for level 0→1)
- Is there already an event system we could hook into?

**Report Format**:
```
EXPERIENCE DEFINITION:
- Events that should trigger record_experience():
  1. [event type] - [where it happens] - [why it counts]
  2. ...
- Recommended implementation location: [file:line]
- Min experiences analysis: [are thresholds reasonable?]
```

---

## GROK 3: Mastery Criteria - Breadth & Depth Tracking

**Your Mission**: Verify the breadth/depth criteria are actually being tracked.

**Files to Investigate**:
- `reality_simulator/language/atomic_language.py` - `check_mastery_advancement()` at line 1403
- `reality_simulator/language/atomic_language.py` - LinguisticAtom class (look for `recent_activation_count`, `associations`)

**Specific Tasks**:
1. Find `recent_activation_count` - where is it defined? Where is it incremented?
2. Find where `associations` dict on atoms is populated
3. Check if these counters are actually being updated during simulation
4. Trace: when an organism uses a word, does `recent_activation_count` increase?
5. Trace: when concepts are taught, do associations form?

**The Criteria** (from check_mastery_advancement):
- BREADTH: 70% of available words must have `recent_activation_count > 5`
- DEPTH: 50% of available words must have `len(associations) >= 3`

**Questions to Answer**:
- Is `recent_activation_count` being incremented anywhere? Or is it always 0?
- Are associations being formed? Or are atoms isolated?
- If these aren't being tracked, organisms can NEVER advance!

**Report Format**:
```
BREADTH TRACKING:
- recent_activation_count defined at: [file:line]
- Incremented at: [file:line] OR [NOT FOUND - BUG!]
- Current behavior: [description]

DEPTH TRACKING:
- associations populated at: [file:line]
- Association formation calls: [list locations]
- Current behavior: [description]

VERDICT: [Criteria trackable? / Broken?]
```

---

## GROK 4: acquire_concept() Mastery Bypass

**Your Mission**: Analyze whether `acquire_concept()` should respect mastery gating.

**Files to Investigate**:
- `reality_simulator/language/atomic_language.py` - `acquire_concept()` at line 1709
- `reality_simulator/language/atomic_language.py` - `get_available_vocabulary()` at line 1312
- `reality_simulator/language/language_teacher.py` - where acquire_concept is called

**Specific Tasks**:
1. Read `acquire_concept()` - does it check mastery level? (spoiler: no)
2. Read `get_available_vocabulary()` - this DOES respect mastery for output
3. Find all callers of `acquire_concept()` - who's adding words?
4. Understand the current design: atoms can exist but be filtered for use
5. Decide: should acquisition be gated, or is filtering-on-use sufficient?

**Design Question**:
Current flow: `acquire_concept()` adds to atoms → `get_available_vocabulary()` filters for use

Option A: Gate acquisition (can't learn words above your tier)
Option B: Keep current (learn anything, only use what you've earned)
Option C: Add "pending" state for concepts above tier

**Report Format**:
```
ACQUIRE_CONCEPT ANALYSIS:
- Mastery check present: [YES/NO]
- Callers: [list all places that call acquire_concept]
- Current behavior: [description]

RECOMMENDATION: [Option A/B/C]
- Reasoning: [why this approach]
- If gating needed, insertion point: [file:line]
```

---

## SONNET 5: Germination & Inheritance

**Your Mission**: Determine how mastery level and experience should be handled on organism death/rebirth.

**Files to Investigate**:
- `reality_simulator/evolution/germination_pool.py` - GerminationCandidate class, spawn methods
- `reality_simulator/language/atomic_language.py` - initialization

**Specific Tasks**:
1. Find GerminationCandidate dataclass - what's inherited currently?
2. Check if `mastery_level` is in the candidate fields
3. Check if `_total_experiences` is inherited
4. Find how atomic_language is initialized on new organisms
5. Look for vocabulary inheritance patterns (vocabulary_words field)

**Questions to Answer**:
- Should a child inherit parent's mastery level? Or start fresh?
- Should experience count transfer? Partially?
- Current grounded mode sets `vocabulary_words = []` - is mastery_level handled similarly?

**Report Format**:
```
INHERITANCE ANALYSIS:
- mastery_level inherited: [YES/NO/PARTIALLY]
- experiences inherited: [YES/NO/PARTIALLY]
- Current germination fields: [list relevant ones]

RECOMMENDATION:
- Mastery inheritance: [approach]
- Experience inheritance: [approach]
- Implementation location: [file:line]
```

---

## SONNET 6: butterfly_chat.py - Reference Implementation

**Your Mission**: Study how mastery advancement works in butterfly_chat (the only place it's called) and extract patterns for simulation integration.

**Files to Investigate**:
- `reality_simulator/language/butterfly_chat.py` - around line 1313-1315

**Specific Tasks**:
1. Find exactly where `record_experience()` and `try_advance_mastery()` are called
2. Understand WHEN they're called - what triggers it?
3. What context/event makes this the right moment?
4. Is there logging when advancement happens?
5. Extract the pattern that should be replicated in simulation loop

**Report Format**:
```
BUTTERFLY_CHAT PATTERN:
- record_experience() called at: [line]
- try_advance_mastery() called at: [line]
- Trigger condition: [what event causes this]
- Context available: [what data is present]

PATTERN TO REPLICATE:
```python
[code snippet showing the pattern]
```

SIMULATION EQUIVALENT:
- This pattern should be applied in: [file:method]
- Equivalent trigger: [what simulation event]
```

---

## SONNET 7: Config Validation & Thresholds

**Your Mission**: Validate that config settings are reasonable and being loaded correctly.

**Files to Investigate**:
- `config.json` - language.grounded section
- `reality_simulator/language/atomic_language.py` - __init__ config loading

**Specific Tasks**:
1. Verify config structure:
```json
"language": {
  "grounded": {
    "enabled": true,
    "initial_mastery_level": 0,
    "mastery_vocab_sizes": [6, 26, 76, 276, 20000],
    "mastery_advancement_ratio": 0.7,
    "mastery_depth_ratio": 0.5,
    "mastery_min_experiences": [50, 200, 500, 1000]
  }
}
```
2. Trace config loading in atomic_language.__init__
3. Check if grounded.enabled is actually checked anywhere
4. Verify mastery_advancement_ratio (0.7 = 70%) is reasonable
5. Verify mastery_min_experiences [50, 200, 500, 1000] are achievable

**Questions to Answer**:
- Is 50 experiences achievable at level 0 in reasonable time?
- Is 70% breadth achievable with 6 words? (need 4-5 words used >5 times each)
- Is 50% depth achievable? (need 3+ associations on 3 words)

**Report Format**:
```
CONFIG VALIDATION:
- grounded.enabled checked at: [file:line] OR [NOT CHECKED - BUG!]
- Config loading correct: [YES/NO]
- Threshold analysis:
  - Level 0→1: [achievable in X generations because...]
  - Level 1→2: [analysis]
  
RECOMMENDATIONS:
- Config changes needed: [if any]
- Code changes needed: [if any]
```

---

## SONNET 8: Web UI Display Fix

**Your Mission**: Fix the Population Browser to show mastery-relevant info.

**Files to Investigate**:
- `causation_web_ui.py` - around line 7254-7257 (vocab counting)
- `causation_web_ui.py` - /api/organisms endpoint

**Specific Tasks**:
1. Find current vocab display logic:
```python
words_learned = len(organism.atomic_language.atoms)
```
2. This shows RAW atoms count, not mastery-available vocabulary
3. Find where mastery_level could be displayed
4. Determine what info would help debug mastery advancement

**Recommended Display**:
- Current: "Words: 9"
- Better: "Words: 6/9 (Level 0)" showing available/total

**Report Format**:
```
CURRENT DISPLAY:
- Location: [file:line]
- Shows: [what]
- Problem: [why misleading]

RECOMMENDED FIX:
```python
[code showing improved display]
```

ADDITIONAL INFO TO ADD:
- mastery_level: [where to add]
- experiences: [where to add]
- advancement progress: [where to add]
```

---

# COORDINATION NOTES

## Dependencies
- GROK 3's findings about breadth/depth tracking affect everyone's recommendations
- GROK 1's integration point affects SONNET 6's pattern application
- GROK 2's experience definition affects thresholds (SONNET 7)

## If You Find Something Critical
Flag it clearly:
```
🚨 CRITICAL BUG: [description]
Location: [file:line]
Impact: [what breaks]
```

## Report Due
Include line numbers. Be specific. Code snippets welcome.

---

**Priority**: HIGH - Organisms are stuck at 6 words forever, breaking the entire grounded language philosophy.
