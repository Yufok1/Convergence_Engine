# 🔍 GROK SWARM DEBUG MISSION - Convergence Engine Audit

**Date**: December 19, 2025  
**Mission**: Deep codebase analysis to identify bugs, inconsistencies, and integration failures  
**Your Role**: You are a debugger/analyst. Find problems, document them clearly. DO NOT fix code - report findings.

---

## 📋 MISSION BRIEFING

The Convergence Engine is an evolutionary AI simulation where neural organisms compete, cooperate, and develop language through behavioral learning. Recent rapid development has introduced potential instabilities. Your mission is to hunt for bugs.

### Recent Changes That May Have Broken Things:
1. **28D → 25D Rollback**: Self-perception features (oscillation_entropy, coherence_frequency, attractor_proximity) were disabled. Input dimensions changed from 28 to 25 across ~30 files. Some may have been missed or inconsistently applied.

2. **Grounded Language Mode**: New vocabulary gating system where organisms must EARN words through mastery levels (0=6 words, 1=26, 2=76, 3=276, 4=unlimited). Multiple code paths were modified to block "vocabulary pollution."

3. **Boom-Bust Wave System**: Highlander evaluation interval changed from 10 seconds to 600 seconds (10-minute waves). Population dynamics completely altered.

4. **Config Consolidation**: 15+ config files deleted. Fallback defaults throughout codebase may no longer match the surviving config.json.

---

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONVERGENCE ENGINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   ORGANISM   │───▶│    BRAIN     │───▶│   DECISION   │                   │
│  │  (Genotype/  │    │ (OrganismBrain)   │  (Action 0-5) │                   │
│  │  Phenotype)  │    │  input_dim=25│    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   ATOMIC     │    │  EXPERIENCE  │    │  HIGHLANDER  │                   │
│  │  LANGUAGE    │    │   BUFFER     │    │  PROTOCOL    │                   │
│  │ (Vocabulary) │    │ (state_dim=25)    │ (Selection)  │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   CONTEXT    │    │   NEURAL     │    │ GERMINATION  │                   │
│  │   MEMORY     │    │   TRAINER    │    │    POOL      │                   │
│  │(SharedVocab) │    │ (batch train)│    │ (Respawning) │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Data Flow:
1. **Organism** extracts 25D state features → **Brain** processes → outputs 6 action probabilities
2. **Experience** (state, action, reward, next_state) stored in **ExperienceBuffer**
3. **NeuralTrainer** samples batches, trains brain networks
4. **LanguageTeacher** observes behavior, assigns words to **ContextMemory**
5. **AtomicLanguage** tracks per-organism vocabulary with mastery levels
6. **HighlanderProtocol** culls weak organisms, **GerminationPool** respawns new ones

### The 6 Actions (Output Head):
```python
ACTION_MAP = {
    0: 'move',
    1: 'cooperate', 
    2: 'compete',
    3: 'rest',
    4: 'reproduce',
    5: 'isolate'
}
```

### Grounded Language Mastery Levels:
```
Level 0: 6 words   (action heads only: move, cooperate, compete, rest, reproduce, isolate)
Level 1: 26 words  (+ basic concepts)
Level 2: 76 words  (+ expanded vocabulary)
Level 3: 276 words (+ advanced concepts)
Level 4: UNLIMITED (semantic graduation - full vocabulary access)
```

---

## 🎯 YOUR SPECIFIC ASSIGNMENT

**Read your Grok number prefix to find your assignment.**

---

# GROK 1: NEURAL DIMENSION CONSISTENCY AUDIT

**Domain**: Neural network input/output dimensions, state vector sizes, tensor shapes

**The Problem**: We changed input_dim from 28 to 25. This touches EVERY file that creates tensors, neural networks, or state vectors. Some places may still have hardcoded 28, or may have been changed inconsistently.

### Files to Investigate:

**HIGH PRIORITY - Neural Core:**
```
reality_simulator/neural/brain.py           - OrganismBrain class, input_dim default
reality_simulator/neural/neural_organism.py - get_state_features(), state vector creation
reality_simulator/neural/experience.py      - ExperienceBuffer, normalize_state() functions
reality_simulator/neural/trainer.py         - batch processing, tensor shapes
reality_simulator/neural/utils.py           - create_brain(), ARCHITECTURE_DEFAULTS
reality_simulator/neural/concept_system.py  - ConceptSystem state_dim
```

**MEDIUM PRIORITY - Integration Points:**
```
reality_simulator/language/language_teacher.py    - SemanticEmbeddingTeacher state_dim
reality_simulator/language/language_game_bridge.py - observation vectors
reality_simulator/portable_agent/perception.py    - PerceptionPipeline state_dim
reality_simulator/portable_agent/bridge.py        - AgentConfig state_dim, InputAdapters
reality_simulator/portable_agent/agent_runtime.py - brain loading, dimension inference
```

**LOWER PRIORITY - Arena/Games:**
```
reality_simulator/arena/gym_runner.py             - obs_tensor creation
reality_simulator/arena/proton_game.py            - _generate_game_state()
reality_simulator/arena/drone_adapter.py          - DroneState.to_observation()
reality_simulator/arena/cocoon_drone_bridge.py    - CocoonDroneState.to_observation()
reality_simulator/arena/live_organism_adapter.py  - state tensor creation
```

### What to Look For:

1. **Hardcoded dimension values**: Search for `28`, `25`, `24` in tensor creation
   ```python
   # BAD - hardcoded
   obs_tensor = torch.zeros(28)
   state = np.zeros(28, dtype=np.float32)
   
   # GOOD - configurable
   obs_tensor = torch.zeros(input_dim)
   state = np.zeros(self.state_dim, dtype=np.float32)
   ```

2. **Mismatched defaults**: Function signature says 25, but code uses 28
   ```python
   def __init__(self, state_dim: int = 25):  # Says 25
       self.features = np.zeros(28)           # Creates 28! BUG!
   ```

3. **Comments referencing wrong dimensions**:
   ```python
   # Create 28-dim state vector (matches config)  # Comment is WRONG if config says 25
   state = np.zeros(25)
   ```

4. **Padding/truncation logic**: Look for `[:28]` or `[:25]` slice operations
   ```python
   # This will silently truncate if state is actually 28-dim
   features[:min(len(obs), 25)] = obs[:25]
   ```

5. **Config reads vs hardcoded**: Some places read from config, others don't
   ```python
   # Inconsistent - one reads config, one hardcodes
   input_dim = config.get('neural', {}).get('brain', {}).get('input_dim', 28)  # Wrong default!
   ```

### Specific Patterns to grep:

```bash
# Find all hardcoded 28s that might be dimensions
grep -rn "zeros(28" --include="*.py"
grep -rn "= 28" --include="*.py" | grep -i "dim\|size\|shape"
grep -rn "[:28]" --include="*.py"

# Find dimension-related defaults
grep -rn "input_dim.*=.*2[458]" --include="*.py"
grep -rn "state_dim.*=.*2[458]" --include="*.py"

# Find self-perception references (should be disabled)
grep -rn "oscillation_entropy\|coherence_frequency\|attractor_proximity" --include="*.py"
```

### Report Format:
```
FILE: path/to/file.py
LINE: 123
ISSUE: Hardcoded 28 in tensor creation
CODE: `state = np.zeros(28, dtype=np.float32)`
SHOULD BE: `state = np.zeros(self.state_dim, dtype=np.float32)` or `np.zeros(25, ...)`
SEVERITY: HIGH/MEDIUM/LOW
```

---

# GROK 2: GROUNDED LANGUAGE MODE INTEGRITY AUDIT

**Domain**: Vocabulary gating, mastery level enforcement, word assignment pathways

**The Problem**: We implemented "grounded mode" where organisms must EARN vocabulary. But there may be code paths that bypass this gating, allowing vocabulary to leak through.

### Critical Files:

**Gating Implementation:**
```
reality_simulator/memory/context_memory.py      - link_word_to_node(), grounded_mode_enabled
reality_simulator/language/atomic_language.py   - can_use_word(), get_available_vocabulary(), mastery_level
reality_simulator/language/language_teacher.py  - _teach_internal(), grounded mode early return
reality_simulator/concept_tracker.py            - concept emergence, grounded mode skip
reality_simulator/evolution/germination_pool.py - vocabulary inheritance blocking
reality_simulator/symbiotic_network.py          - ContextMemory creation with config
```

**Potential Bypass Points:**
```
reality_simulator/language/butterfly_chat.py       - Response generation
reality_simulator/language/linguistic_knowledge_web.py - Knowledge loading
reality_simulator/evolution/highlander_protocol.py - Winner absorption
reality_simulator/neural/neural_organism.py        - Organism initialization
```

### What to Look For:

1. **Missing grounded mode checks**: Code that assigns words without checking mastery
   ```python
   # BAD - no grounded mode check
   context_memory.link_word_to_node(word, organism_id, generation)
   
   # SHOULD CHECK mastery level first or trust caller validated
   ```

2. **Config not propagated**: ContextMemory created without config parameter
   ```python
   # BAD - no config passed, grounded_mode_enabled will be False
   self.context_memory = ContextMemory()
   
   # GOOD - config passed for grounded mode checking
   self.context_memory = ContextMemory(..., config=config)
   ```

3. **Vocabulary inheritance leaks**: Words transferred during reproduction/respawn
   ```python
   # Look for vocabulary transfer that bypasses grounded mode
   new_organism._inherited_vocabulary = parent._inherited_vocabulary  # Leak?
   ```

4. **Direct atomic_language manipulation**: Code that adds atoms without mastery check
   ```python
   # Direct atom addition bypasses can_use_word()
   organism.atomic_language.atoms[word] = LinguisticAtom(...)
   ```

5. **Knowledge web bootstrap**: Bulk loading vocabulary at startup
   ```python
   # Does this respect grounded mode?
   self.knowledge_web.load_expanded_relations()
   ```

### Config Values to Verify Are Respected:

```json
{
  "language": {
    "mode": "grounded",
    "grounded": {
      "enabled": true,
      "mastery_gating": true,
      "initial_mastery_level": 0,
      "mastery_vocab_sizes": [6, 26, 76, 276, 20000]
    }
  }
}
```

### Mastery Gating Logic to Verify:

```python
# In atomic_language.py - get_available_vocabulary()
MASTERY_VOCAB_SIZES = [6, 26, 76, 276, 20000]  # Level 0-4

def get_available_vocabulary(self) -> List[str]:
    if self._mastery_level >= 4:
        return list(self.vocab_index.keys())  # All words
    
    target_size = MASTERY_VOCAB_SIZES[min(self._mastery_level, 4)]
    # Returns only words organism has earned
```

### Specific Patterns to grep:

```bash
# Find all word assignment points
grep -rn "link_word_to_node" --include="*.py"
grep -rn "\.atoms\[" --include="*.py"

# Find vocabulary inheritance
grep -rn "_inherited_vocabulary\|inherit.*vocab" --include="*.py"

# Find grounded mode checks (or lack thereof)
grep -rn "grounded_mode\|mastery_level\|mastery_gating" --include="*.py"

# Find knowledge web loading
grep -rn "load_expanded\|bootstrap.*vocab\|knowledge_web.*enabled" --include="*.py"
```

### Report Format:
```
FILE: path/to/file.py
LINE: 456
ISSUE: Word assignment without mastery check
CODE: `context_memory.link_word_to_node(concept_name, org_id, gen)`
CONTEXT: This is called when concepts emerge, but grounded mode should block this
SEVERITY: HIGH - Vocabulary pollution pathway
```

---

# GROK 3: CONFIG/FALLBACK CONSISTENCY AUDIT

**Domain**: Hardcoded defaults vs config.json values, missing config reads

**The Problem**: Config values were changed, but fallback defaults throughout the codebase may not have been updated. When config lookup fails, wrong defaults are used.

### The Canonical Config (config.json excerpts):

```json
{
  "neural": {
    "brain": {
      "input_dim": 25,
      "hidden_dim": 64,
      "output_dim": 6,
      "vocab_size": 20000,
      "attention_dim": 32
    },
    "training": {
      "learning_rate": 0.003,
      "gamma": 0.995,
      "epsilon": 0.95,
      "epsilon_decay": 0.995,
      "epsilon_end": 0.01,
      "batch_size": 32,
      "memory_size": 20000
    }
  },
  "evolution": {
    "population_size": 25
  },
  "highlander": {
    "eval_interval_seconds": 600,
    "survival_threshold": 0.5,
    "competition_intensity": 0.4,
    "max_population": 50,
    "min_population": 10,
    "germination_rate": 0.15
  },
  "network": {
    "resource_pool": 600,
    "max_organisms": 200
  }
}
```

### Files to Audit:

**Neural System:**
```
reality_simulator/neural/brain.py
reality_simulator/neural/trainer.py
reality_simulator/neural/neural_organism.py
reality_simulator/neural/utils.py
reality_simulator/neural/experience.py
```

**Evolution System:**
```
reality_simulator/evolution/highlander_protocol.py
reality_simulator/evolution/germination_pool.py
reality_simulator/evolution_engine.py
```

**Network/Simulation:**
```
reality_simulator/symbiotic_network.py
reality_simulator/main.py (if exists)
unified_entry.py
```

### What to Look For:

1. **Wrong default values**: Fallback doesn't match config.json
   ```python
   # BAD - config says 0.995, fallback says 0.99
   gamma = config.get('neural', {}).get('training', {}).get('gamma', 0.99)
   
   # GOOD - matches config.json
   gamma = config.get('neural', {}).get('training', {}).get('gamma', 0.995)
   ```

2. **Outdated comments**: Comment says one thing, code does another
   ```python
   # Default: 1000 (from legacy config)  # WRONG - config says 20000
   memory_size = config.get('memory_size', 1000)
   ```

3. **Inconsistent config paths**: Different files use different paths for same value
   ```python
   # File A:
   lr = config.get('neural', {}).get('training', {}).get('learning_rate', 0.003)
   
   # File B (DIFFERENT PATH!):
   lr = config.get('training', {}).get('lr', 0.001)  # BUG - wrong path AND wrong default
   ```

4. **Missing config reads**: Value is always hardcoded, never reads config
   ```python
   # Always uses 0.1, ignores config
   self.mutation_rate = 0.1  # Should read from config!
   ```

5. **Deleted config references**: References config files that no longer exist
   ```python
   # These configs were DELETED:
   # config_a100.json, config_genesis.json, config_h100_genesis.json
   # config_shadow_cloud_epyc.json, config_shadow_epyc.json
   # Any references to these are bugs
   ```

### Known Problematic Defaults (Historical Bugs):

These have been fixed before but may have regressed:
```python
# CORRECT VALUES (from config.json):
input_dim = 25          # NOT 24, NOT 28
gamma = 0.995           # NOT 0.99
vocab_size = 20000      # NOT 1000
memory_size = 20000     # NOT 1000, NOT 10000
resource_pool = 600     # NOT 200
survival_threshold = 0.5 # NOT 0.3, NOT 0.4
competition_intensity = 0.4  # NOT 0.2, NOT 0.5
```

### Specific Patterns to grep:

```bash
# Find all .get() calls with defaults
grep -rn "\.get\(.*,.*\)" --include="*.py" | grep -E "0\.(99|9|3|4|5)|1000|24|28"

# Find hardcoded training params
grep -rn "learning_rate\s*=\s*0\." --include="*.py"
grep -rn "gamma\s*=\s*0\." --include="*.py"
grep -rn "epsilon.*=\s*0\." --include="*.py"

# Find population/resource defaults
grep -rn "resource_pool\|max_organisms\|population_size" --include="*.py"

# Find references to deleted configs
grep -rn "config_a100\|config_genesis\|config_h100\|config_shadow" --include="*.py"
```

### Report Format:
```
FILE: path/to/file.py
LINE: 789
ISSUE: Fallback default doesn't match config.json
CONFIG PATH: neural.training.gamma
CONFIG VALUE: 0.995
CODE DEFAULT: 0.99
CODE: `gamma = config.get('neural', {}).get('training', {}).get('gamma', 0.99)`
SEVERITY: MEDIUM - Training will use wrong discount factor if config lookup fails
```

---

# GROK 4: INTEGRATION/DATA FLOW AUDIT

**Domain**: Cross-system communication, event emission, data passing between modules

**The Problem**: Systems that worked in isolation may fail when integrated. Data flows through multiple modules and type mismatches, missing parameters, or broken event chains can cause silent failures.

### Critical Integration Points:

**1. Organism → Brain → Decision Flow:**
```
neural_organism.py:get_state_features() 
    → brain.py:forward() 
    → Returns (q_values, language_logits, concept_output)
    → neural_organism.py:decide()
```

**2. Language Teaching Flow:**
```
language_teacher.py:teach_network()
    → For each organism: _teach_internal()
    → context_memory.py:link_word_to_node()
    → atomic_language.py updates
```

**3. Experience Recording Flow:**
```
neural_organism.py:record_experience()
    → experience.py:ExperienceBuffer.add()
    → trainer.py:train_step() samples from buffer
```

**4. Highlander → Germination Flow:**
```
highlander_protocol.py:evaluate()
    → Culls organisms
    → germination_pool.py:spawn_from_pool()
    → Creates new NeuralOrganisms with inherited brains
```

**5. Event Emission Flow:**
```
Various modules emit events → event_emitter
    → causation_explorer.py receives
    → Web UI displays
```

### Files to Investigate:

```
reality_simulator/neural/neural_organism.py    - Organism lifecycle
reality_simulator/neural/trainer.py            - Training integration
reality_simulator/language/language_teacher.py - Teaching flow
reality_simulator/memory/context_memory.py     - Shared state
reality_simulator/evolution/highlander_protocol.py - Selection
reality_simulator/evolution/germination_pool.py    - Respawning
reality_simulator/symbiotic_network.py         - Network management
reality_simulator/causation_explorer.py        - Event handling
unified_entry.py                               - Main orchestration
```

### What to Look For:

1. **Function signature mismatches**: Caller passes wrong args
   ```python
   # In context_memory.py:
   def link_word_to_node(self, word, organism_id, generation=None, 
                         organism_embedding=None, organism=None):
   
   # In some_caller.py - MISSING organism parameter:
   cm.link_word_to_node(word, org_id, gen, embedding)  # No organism!
   ```

2. **Return value changes**: Function returns different type than expected
   ```python
   # brain.forward() returns tuple: (q_values, lang_logits, concept_out)
   # But caller expects just q_values:
   q_values = brain(state)  # BUG - this is actually a tuple!
   action = q_values.argmax()  # Will fail!
   ```

3. **None checks missing**: Object might be None but code assumes it exists
   ```python
   # Organism might not have atomic_language
   words = organism.atomic_language.get_available_vocabulary()  # AttributeError if None!
   
   # Should be:
   if organism.atomic_language:
       words = organism.atomic_language.get_available_vocabulary()
   ```

4. **Event emitter not wired**: Events emitted but no listener
   ```python
   # Emitting event
   if self.event_emitter:
       self.event_emitter.emit('word_assignment', {...})
   
   # But event_emitter might be None if not wired in unified_entry.py
   ```

5. **Type mismatches**: String vs int, numpy vs torch
   ```python
   # organism_id might be string in some places, int in others
   # This causes dict key mismatches
   organisms[organism_id]  # KeyError if types don't match
   ```

6. **Config not passed through**: Child objects don't receive config
   ```python
   # Parent has config
   self.teacher = LanguageTeacher(config=self.config)
   
   # But teacher creates child without passing config
   self.embedding_teacher = SemanticEmbeddingTeacher()  # No config!
   ```

### Specific Integration Bugs to Hunt:

**A. Brain Forward Return Handling:**
```python
# OrganismBrain.forward() can return:
# - Just q_values (old code)
# - (q_values, language_logits) (with language head)
# - (q_values, language_logits, concept_output) (with concept system)

# Find places that don't handle tuple return:
grep -rn "brain\(.*\)\.argmax\|brain\(.*\)\[0\]" --include="*.py"
```

**B. Organism ID Type Consistency:**
```python
# Some use string species_id, some use int hash
# Find inconsistencies:
grep -rn "organism_id\|species_id\|org_id" --include="*.py"
```

**C. Context Memory Wiring:**
```python
# context_memory should be shared across:
# - SymbioticNetwork
# - LanguageTeacher  
# - ConceptTracker
# - All organisms

# Find places it might not be wired:
grep -rn "context_memory\s*=\s*None\|context_memory is None" --include="*.py"
```

**D. Event Emitter Wiring:**
```python
# event_emitter should be wired to:
# - context_memory
# - highlander_protocol
# - germination_pool
# - language_teacher

grep -rn "event_emitter\s*=\s*None\|\.event_emitter\s*=" --include="*.py"
```

### Specific Patterns to grep:

```bash
# Find function calls that might have wrong args
grep -rn "link_word_to_node\|teach_network\|record_experience" --include="*.py"

# Find potential None dereferences
grep -rn "\.atomic_language\.\|\.brain\.\|\.context_memory\." --include="*.py"

# Find event emissions
grep -rn "emit\(.*\)\|event_emitter" --include="*.py"

# Find config passing (or not)
grep -rn "config=config\|config=self\.config\|config=None" --include="*.py"
```

### Report Format:
```
FILE: path/to/file.py
LINE: 234
ISSUE: Function call missing required parameter
CALLER: `context_memory.link_word_to_node(word, org_id, gen, emb)`
EXPECTED: `link_word_to_node(word, org_id, gen, emb, organism=organism)`
IMPACT: Mastery gating check will be skipped, vocabulary pollution possible
SEVERITY: HIGH
```

---

## 📝 REPORTING INSTRUCTIONS

### For ALL Groks:

1. **Be thorough** - Check every file in your domain
2. **Be specific** - Include exact line numbers and code snippets
3. **Prioritize** - Mark severity (HIGH/MEDIUM/LOW)
4. **Explain impact** - Why does this bug matter?
5. **Don't fix** - Just report. The human + Claude will fix.

### Report Structure:

```markdown
# GROK [NUMBER] FINDINGS REPORT

## Summary
- Total files examined: X
- Total issues found: Y
- High severity: A
- Medium severity: B  
- Low severity: C

## High Severity Issues

### Issue 1: [Brief Title]
- **File**: path/to/file.py
- **Line**: 123
- **Code**: `problematic code here`
- **Problem**: Explanation
- **Impact**: What breaks
- **Suggested Fix Direction**: (optional) General approach

### Issue 2: ...

## Medium Severity Issues
...

## Low Severity Issues
...

## Suspicious But Unconfirmed
(Things that look wrong but you're not 100% sure)

## Files Examined
- file1.py ✓
- file2.py ✓
- ...
```

---

## 🚀 START YOUR INVESTIGATION

You have your assignment. Go deep. Question everything. The codebase has been through rapid iteration and things are likely broken in subtle ways.

**Remember**: 
- You are debugging, not refactoring
- Find problems, don't solve them
- Be paranoid - assume nothing works correctly
- Cross-reference with config.json values
- Check that recent changes (25D, grounded mode) are consistently applied

Good hunting! 🔍
