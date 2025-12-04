# 🔧 GROK SWARM - SYSTEM STABILIZATION MISSION

## CONTEXT BRIEFING

Two rounds of fixes have been applied to the Butterfly language system. We need to verify the system is now stable and catch any remaining issues before testing.

## FIXES ALREADY APPLIED

### Round 1 (Initial Fixes):
1. Repetition penalty added to token generation
2. Top-k sampling (k=40) for diversity
3. Stronger reward penalty for repetition
4. Lower minimum reward floor
5. Broadcast protection (unique_ratio > 0.5)
6. Semantic threshold lowered (0.7 → 0.3)
7. Language loss weight increased (beta: 0.1 → 0.4)
8. Vocab sizes synchronized (teacher: 4096 → 50000)

### Round 2 (Review Fixes):
1. **CRITICAL**: Changed division to subtraction for repetition penalty
2. Removed double unique_ratio calculation
3. Separated vocab expansion from broadcast condition
4. Added try-except isolation for broadcast/vocab
5. Fixed config min_strength_threshold (0.7 → 0.3)
6. Fixed vocab max_size (10000 → 50000)
7. Added default unique_ratio = 1.0 initialization
8. Reduced negative reward floor (-0.2 → -0.1)

## CURRENT CODE STATE

### Token Generation (neural_organism.py ~1595-1620):
```python
repetition_penalty = 2.0  # Subtraction value
recent_window = 5
if len(generated) > 0:
    for prev_token in recent_tokens:
        logits[prev_token] = logits[prev_token] - repetition_penalty
    logits[generated[-1]] = logits[generated[-1]] - (repetition_penalty * 1.5)

top_k = 40
if len(logits) > top_k:
    top_k_values, top_k_indices = torch.topk(logits, top_k)
    top_k_mask = torch.full_like(logits, float('-inf'))
    top_k_mask[top_k_indices] = 0
    logits = logits + top_k_mask
```

### Reward Calculation (butterfly_chat.py ~885-955):
```python
unique_ratio = 1.0  # Default for single-word
if len(response_words) > 1:
    unique_ratio = len(response_words_set) / len(response_words)
    coherence_score += unique_ratio * 0.15
    if unique_ratio < 0.5:
        coherence_score -= (1.0 - unique_ratio) * 0.3
    # consecutive repeat detection...

# Later reuses unique_ratio:
if len(response_words) > 1 and unique_ratio < 0.3:
    final_reward = max(-0.1, min(1.0, reward))
else:
    final_reward = max(0.1, min(1.0, reward))
```

### Config (config.json):
```json
"training": { "alpha": 0.5, "beta": 0.4, "gamma": 0.1 }
"vocabulary": { "max_size": 50000 }
"teacher": { "vocab_size": 50000 }
"brain": { "vocab_size": 50000 }
"semantic_guidance": { "min_strength_threshold": 0.3 }
```

---

# YOUR MISSION

You will be told which GROK number you are (1, 2, 3, or 4). Find your section below.

**OUTPUT FORMAT**:
```
ISSUE: [Brief description]
FILE: [Full path]
LINE: [Line number or range]
CODE: [Relevant code]
PROBLEM: [Why this is wrong/risky]
SUGGESTED_FIX: [Specific fix]
SEVERITY: [CRITICAL / HIGH / MEDIUM / LOW]
```

OR if no issues found:
```
AREA CHECKED: [What you verified]
STATUS: ✅ STABLE
NOTES: [Any observations]
```

---

# GROK-1: Training Pipeline Stability

## YOUR TARGETS

### Check 1: Training Still Works
Search `reality_simulator/neural/trainer.py` for:
- Does training still use `token_sequence`? (original issue not fully fixed)
- Are alpha/beta/gamma being read correctly from config?
- Is language loss actually being computed with new weights?

### Check 2: Loss Weight Application
- Verify the new alpha=0.5, beta=0.4, gamma=0.1 are loaded
- Check if there are hardcoded fallbacks that override config
- Trace the loss calculation: `loss = alpha * rl + beta * lang + gamma * concept`

### Check 3: Experience Buffer Integration
- Is `sample_batch_with_language()` implemented?
- Are `input_tokens`/`target_tokens` from experience buffer ever used?
- This was flagged as root cause but may not be fixed yet

### Check 4: Training Triggers
- Is training triggered often enough?
- Check `_trigger_chat_training()` frequency
- Verify experience buffer minimum size checks

### SEARCH COMMANDS
```
grep -n "alpha\|beta\|gamma" trainer.py
grep -n "token_sequence" trainer.py
grep -n "input_tokens\|target_tokens" trainer.py
grep -n "sample_batch" trainer.py
```

Report whether the CORE training issue (using token_sequence instead of proper seq2seq) is still present.

---

# GROK-2: Token Generation Stability

## YOUR TARGETS

### Check 1: Penalty Magnitude
- `repetition_penalty = 2.0` is subtracted from logits
- Is 2.0 too aggressive? Too weak?
- What's the typical logit range? (usually -10 to +10)
- Will subtracting 2.0 make a meaningful difference?

### Check 2: Order of Operations
In neural_organism.py generate_tokens():
1. Vocabulary mask applied
2. Repetition penalty applied
3. Top-k mask applied
4. Softmax
5. Multinomial sample

Is this order correct? Any issues?

### Check 3: Edge Cases
- What if vocabulary size < 40? Top-k breaks?
- What if all top-k tokens are penalized? Could get stuck?
- What if `generated` list grows very long?

### Check 4: GPU/CPU Consistency
- Are logits on GPU?
- Is `generated` list on CPU?
- Any device mismatch when indexing?

### SEARCH COMMANDS
```
grep -n "repetition_penalty" neural_organism.py
grep -n "top_k" neural_organism.py
grep -n "\.to\(.*device" neural_organism.py
grep -n "cuda\|cpu" neural_organism.py
```

Verify token generation is numerically stable.

---

# GROK-3: Reward & Experience Flow

## YOUR TARGETS

### Check 1: Reward Range Sanity
With all penalties applied, what's the realistic reward range?
- Base: 0.3
- Overlap: +0.0 to +0.3
- Coherence: -0.5 to +0.2 (with all penalties)
- Length: +0.0 to +0.2
- Confidence: +0.0 to +0.2
- VP adjustment: -0.05 to +0.1
- **Final clamp**: max(-0.1, min(1.0, reward))

Can rewards realistically go negative? Is the floor reachable?

### Check 2: Experience Storage
In butterfly_chat.py `_store_chat_experience()`:
- Is experience stored BEFORE or AFTER reward calculation?
- Does stored experience include the correct reward value?
- Are `input_tokens` and `target_tokens` stored correctly?

### Check 3: Reward → Training Connection
- Does trainer actually USE the stored rewards?
- Or does it recalculate rewards during training?
- Is there a disconnect between chat rewards and training rewards?

### Check 4: Broadcast → Training Loop
- After broadcast, does it trigger training?
- Is there a feedback loop where broadcast triggers training on broadcast data?
- Could this amplify certain patterns?

### SEARCH COMMANDS
```
grep -n "final_reward" butterfly_chat.py
grep -n "_store_chat_experience" butterfly_chat.py
grep -n "reward" trainer.py | head -50
grep -n "experience_buffer" trainer.py
```

Verify rewards flow correctly from chat to training.

---

# GROK-4: Config Consistency & Data Dependencies

## YOUR TARGETS

### Check 1: All Vocab Sizes Match
Search everywhere for vocab_size references:
- config.json: brain.vocab_size, teacher.vocab_size, vocabulary.max_size
- brain.py: default vocab_size parameter
- neural_organism.py: any hardcoded vocab sizes
- trainer.py: any vocab_size references

Are they ALL 50000 now?

### Check 2: Data Files Required
The system needs:
- `data/butterfly_vocabulary_50k_curated.json`
- `data/seeded_knowledge_web_50k.json`
- `data/context_memory.json`

Do these exist? Are they populated?

### Check 3: Initialization Order
When system starts:
1. Config loaded
2. Vocabulary initialized
3. Brain created
4. Knowledge web loaded

Is vocabulary populated BEFORE brain uses vocab_size?

### Check 4: Runtime Config Reload
- Can config be changed at runtime?
- If config.json changes, do running components pick up new values?
- Are there cached config values that won't update?

### SEARCH COMMANDS
```
grep -rn "vocab_size" --include="*.py" | grep -v __pycache__
grep -rn "50000\|12288\|4096\|10000" --include="*.py" | grep vocab
ls data/*.json
cat data/butterfly_vocabulary_50k_curated.json | head -5
```

Find any remaining config/data inconsistencies.

---

# GROK-5: Integration & Startup Stability (BONUS)

If you have capacity, also check:

## YOUR TARGETS

### Check 1: Import Chain
- Does `unified_entry.py` import everything correctly?
- Are there circular import issues?
- Any import-time errors?

### Check 2: Startup Sequence
- What happens if vocabulary files are missing?
- Does system fail gracefully or crash?
- Are there fallback behaviors?

### Check 3: Error Handling
- Are new try-except blocks logging errors?
- Is `logger` properly configured?
- Will silent failures hide problems?

### SEARCH COMMANDS
```
python -c "from reality_simulator.neural.neural_organism import NeuralOrganism; print('Import OK')"
python -c "from reality_simulator.language.butterfly_chat import ButterflyChatRouter; print('Import OK')"
python check_setup.py
```

Verify system can start without crashing.

---

# AFTER ALL GROKS REPORT

Paste all findings back to Claude. He will:
1. Fix any remaining CRITICAL/HIGH issues
2. Verify system is ready for testing
3. Create a test plan if needed
