# 🔬 GROK SWARM - FINAL VERIFICATION MISSION

## CONTEXT BRIEFING

Three rounds of fixes have been applied. This is the FINAL verification pass before testing the live system.

## ALL FIXES APPLIED SO FAR

### Round 1 - Initial Fixes:
- Repetition penalty (subtraction, not division)
- Top-k sampling (k=40)
- Stronger reward penalties for repetition
- Broadcast protection
- Config syncs (beta=0.4, vocab sizes)

### Round 2 - Review Fixes:
- Division→subtraction for repetition penalty (CRITICAL)
- Double penalty bug removed
- Vocab expansion separated from broadcast
- Try-except isolation
- unique_ratio initialization

### Round 3 - Stabilization Fixes:
- `sample_batch_with_seq2seq()` method added to ExperienceBuffer
- `has_seq2seq_data()` method added
- Trainer now uses seq2seq data from experience buffer
- `_train_from_token_sequence()` fallback method added
- Brain default vocab_size: 12288→50000
- Teacher default vocab_size: 1000→50000
- Utils validation: 4096→50000
- Reward clamping: 3-tier system (-0.3/0.0/0.05 floors)

## CURRENT VERIFIED STATE

✅ All files compile without syntax errors
✅ Data files present (50k vocab, knowledge web)
✅ New experience buffer methods tested
✅ Config values synchronized

---

# YOUR MISSION

You are doing FINAL VERIFICATION. Look for:
1. Integration bugs between the new code
2. Edge cases we missed
3. Logic errors in the fix implementations
4. Any remaining inconsistencies

**OUTPUT FORMAT**:
```
ISSUE: [Brief description]
FILE: [Full path]
LINE: [Line number]
SEVERITY: [CRITICAL / HIGH / MEDIUM / LOW]
DETAILS: [Full explanation]
```

OR:
```
AREA: [What you checked]
STATUS: ✅ VERIFIED
```

---

# GROK-1: Seq2Seq Training Integration

## VERIFY THESE

### Check 1: Seq2Seq Data Flow
Trace the FULL path:
1. `butterfly_chat.py` stores experience with `input_tokens`/`target_tokens`
2. Experience buffer receives and stores them
3. Trainer samples with `sample_batch_with_seq2seq()`
4. Training uses separated input→target

**QUESTION**: Is there any place where `input_tokens` gets corrupted, truncated, or lost?

### Check 2: Fallback Logic
When `has_seq2seq_data()` returns False, trainer falls back to `_train_from_token_sequence()`.
- Does the fallback work correctly?
- Is there a case where NEITHER path executes?

### Check 3: Tensor Shape Compatibility
New code uses `target_tokens.size(1)` for sequence length.
- What if `target_tokens` is 1D instead of 2D?
- What if batch size > 1?

### SEARCH COMMANDS
```
grep -n "input_tokens" butterfly_chat.py trainer.py experience.py
grep -n "target_tokens" butterfly_chat.py trainer.py experience.py
grep -n "sample_batch_with_seq2seq" trainer.py experience.py
grep -n "_train_from_token_sequence" trainer.py
```

---

# GROK-2: Experience Buffer Integrity

## VERIFY THESE

### Check 1: Experience Class Fields
In `experience.py`, Experience class now has:
- `input_tokens` (default: [])
- `target_tokens` (default: [])
- `token_sequence` (backward compat)

**QUESTION**: When `add()` is called, are ALL these fields properly populated?

### Check 2: Sample Method Returns
`sample_batch_with_seq2seq()` returns 9 values:
```python
(states, actions, rewards, next_states, dones, 
 input_tokens_list, target_tokens_list, rewards_list, vp_values)
```

**QUESTION**: Does the caller unpack all 9 correctly? Any mismatch?

### Check 3: Filter Logic
```python
seq2seq_experiences = [e for e in self.buffer if e.has_seq2seq_data()]
```

**QUESTION**: What if buffer is a deque and iteration fails? Thread safety?

### SEARCH COMMANDS
```
grep -n "def add" experience.py
grep -n "sample_batch_with_seq2seq" experience.py
grep -n "has_seq2seq_data" experience.py
```

---

# GROK-3: Reward System Consistency

## VERIFY THESE

### Check 1: Reward Calculation Variables
The reward calculation uses:
- `response_words` 
- `response_words_set`
- `unique_ratio`
- `coherence_score`

**QUESTION**: Are ALL these defined before use? Any scope issues?

### Check 2: Three-Tier Clamping Logic
```python
if unique_ratio < 0.3:
    final_reward = max(-0.3, ...)  # Severe
elif unique_ratio < 0.5:
    final_reward = max(0.0, ...)   # Moderate
else:
    final_reward = max(0.05, ...)  # Normal
```

**QUESTION**: What if `len(response_words) == 1`? The `elif` and `else` won't trigger because they're inside `if len(response_words) > 1`.

### Check 3: Reward Storage
After `final_reward` is calculated, is it properly stored in experience buffer?

### SEARCH COMMANDS
```
grep -n "unique_ratio" butterfly_chat.py
grep -n "final_reward" butterfly_chat.py
grep -n "coherence_score" butterfly_chat.py
```

---

# GROK-4: Config & Default Consistency

## VERIFY THESE

### Check 1: All Default Values
Search ALL Python files for hardcoded vocab sizes:
- 12288 (old brain default)
- 4096 (old teacher config)
- 1000 (old teacher default)
- 10000 (old vocab max_size)

**QUESTION**: Did we miss any?

### Check 2: Config Reading Paths
Verify these config paths are read correctly:
- `config.neural.brain.vocab_size` → 50000
- `config.neural.language_model.teacher.vocab_size` → 50000
- `config.neural.language_model.vocabulary.max_size` → 50000
- `config.neural.language_model.training.alpha` → 0.5
- `config.neural.language_model.training.beta` → 0.4

### Check 3: Runtime vs Init
Some values are read at init, some at runtime.
**QUESTION**: If config changes at runtime, which values update and which don't?

### SEARCH COMMANDS
```
grep -rn "12288\|4096\|1000\b" --include="*.py" | grep -i vocab
grep -rn "vocab_size" --include="*.py" | head -30
grep -n "training_config.get" trainer.py
```

---

# GROK-5: Token Generation Edge Cases

## VERIFY THESE

### Check 1: Repetition Penalty Bounds
```python
repetition_penalty = 2.0
logits[prev_token] = logits[prev_token] - repetition_penalty
logits[generated[-1]] = logits[generated[-1]] - (repetition_penalty * 1.5)
```

**QUESTION**: 
- If a token gets penalized multiple times (in `recent_tokens` AND as `generated[-1]`), total penalty is -2.0 + -3.0 = -5.0. Too harsh?
- What's the minimum logit value that causes numerical issues?

### Check 2: Top-k with Small Vocabulary
```python
top_k = 40
if len(logits) > top_k:
    # apply top-k mask
```

**QUESTION**: If actual vocabulary is 35 words, top-k is skipped. Is that correct behavior?

### Check 3: Empty Generation
What happens if:
- `generated` list is empty (first token)?
- All tokens are masked to -inf?
- Softmax produces NaN?

### SEARCH COMMANDS
```
grep -n "repetition_penalty" neural_organism.py
grep -n "top_k" neural_organism.py
grep -n "generated\[-1\]" neural_organism.py
grep -n "softmax" neural_organism.py
```

---

# AFTER ALL GROKS REPORT

This is the FINAL pass. Report:
1. Any remaining bugs (CRITICAL/HIGH priority)
2. Edge cases that need defensive code
3. Areas verified as stable

Claude will either:
- Fix remaining issues, OR
- Declare system ready for testing
