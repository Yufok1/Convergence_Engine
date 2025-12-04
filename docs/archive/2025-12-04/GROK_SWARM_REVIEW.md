# 🔍 GROK SWARM - CODE REVIEW MISSION

## CONTEXT BRIEFING

Claude just implemented 8 fixes to address the language system's repetitive output problem ("was was was"). Your job is to **review these changes** for bugs, inconsistencies, edge cases, and integration issues.

## THE FIXES THAT WERE APPLIED

### Fix 1: Repetition Penalty (neural_organism.py ~line 1590)
```python
# Added repetition penalty
repetition_penalty = 1.2
recent_window = 5
if len(generated) > 0:
    recent_tokens = generated[-recent_window:] if len(generated) >= recent_window else generated
    for prev_token in recent_tokens:
        if prev_token < len(logits):
            logits[prev_token] = logits[prev_token] / repetition_penalty
    # Extra penalty for immediately previous token
    if generated[-1] < len(logits):
        logits[generated[-1]] = logits[generated[-1]] / (repetition_penalty * 1.5)
```

### Fix 2: Top-k Sampling (neural_organism.py ~line 1605)
```python
top_k = 40
if len(logits) > top_k:
    top_k_values, top_k_indices = torch.topk(logits, top_k)
    top_k_mask = torch.full_like(logits, float('-inf'))
    top_k_mask[top_k_indices] = 0
    logits = logits + top_k_mask
```

### Fix 3: Stronger Reward Penalty (butterfly_chat.py ~line 874)
```python
if len(response_words) > 1:
    unique_ratio = len(response_words_set) / len(response_words)
    coherence_score += unique_ratio * 0.15
    if unique_ratio < 0.5:
        coherence_score -= (1.0 - unique_ratio) * 0.3
    # Consecutive repeat detection
    consecutive_repeats = 0
    for i in range(1, len(response_words)):
        if response_words[i] == response_words[i-1]:
            consecutive_repeats += 1
    if consecutive_repeats > 0:
        coherence_score -= consecutive_repeats * 0.15
```

### Fix 4: Lower Minimum Reward (butterfly_chat.py ~line 927)
```python
if len(response_words) > 1:
    unique_ratio = len(response_words_set) / len(response_words)
    if unique_ratio < 0.3:
        final_reward = max(-0.2, min(1.0, reward))  # Allow negative
    else:
        final_reward = max(0.1, min(1.0, reward))
else:
    final_reward = max(0.1, min(1.0, reward))
```

### Fix 5: Broadcast Protection (butterfly_chat.py ~line 780)
```python
response_words_for_broadcast = organism_response.lower().split() if organism_response else []
broadcast_unique_ratio = len(set(response_words_for_broadcast)) / max(1, len(response_words_for_broadcast))
if reward > 0.6 and network_state and broadcast_unique_ratio > 0.5:
    self._broadcast_successful_response(...)
```

### Fix 6: Semantic Threshold Lowered (neural_organism.py ~line 1516)
```python
min_strength = semantic_config.get('min_strength_threshold', 0.3)  # Was 0.7
```

### Fix 7: Config - Language Loss Weight (config.json)
```json
"training": {
    "alpha": 0.5,  // Was 0.8
    "beta": 0.4,   // Was 0.1
    "gamma": 0.1
}
```

### Fix 8: Config - Vocab Size Sync (config.json)
```json
"teacher": {
    "vocab_size": 50000  // Was 4096
}
```

---

# YOUR MISSION

You will be told which GROK number you are (1, 2, 3, or 4). Find your section below.

**OUTPUT FORMAT**: For each issue found, report:
```
ISSUE: [Brief description]
FILE: [Full path]
LINE: [Line number or range]
CODE: [Relevant code showing the problem]
PROBLEM: [Why this is wrong/risky]
SUGGESTED_FIX: [Specific code change needed]
SEVERITY: [CRITICAL / HIGH / MEDIUM / LOW]
```

---

# GROK-1: Repetition Penalty & Sampling Review

## YOUR TARGETS

### Check 1: Repetition Penalty Logic
In `reality_simulator/neural/neural_organism.py` around line 1590:
- Is division the right operation? (logits can be negative!)
- What happens if `generated` is empty at start?
- Is the penalty applied BEFORE or AFTER the vocabulary mask?
- Does the penalty interact badly with semantic boost?

### Check 2: Top-k Sampling Order
- Is top-k applied AFTER repetition penalty? (correct order?)
- What if vocab_size < 40? Does top-k break?
- Are we applying top-k AFTER the vocab mask? (could unmask invalid tokens)

### Check 3: Edge Cases
- What if `logits` tensor is on GPU but `generated` list indices are CPU?
- Is there a race condition in the generation loop?
- What happens with 1-token responses?

### SEARCH COMMANDS
```
grep -n "repetition_penalty" neural_organism.py
grep -n "top_k" neural_organism.py
grep -n "generated\[" neural_organism.py
```

Look for order-of-operations bugs and tensor device mismatches.

---

# GROK-2: Reward Calculation Review

## YOUR TARGETS

### Check 1: Variable Scope
In `reality_simulator/language/butterfly_chat.py`:
- Where is `response_words_set` defined? Is it in scope at line 874?
- Where is `response_words` defined? Same scope?
- Is `coherence_score` initialized before these additions?

### Check 2: Double Penalty Bug
- Fix 3 adds penalty based on `unique_ratio`
- Fix 4 uses `unique_ratio` again for reward floor
- Are we penalizing TWICE for the same problem?

### Check 3: Math Consistency
- If `unique_ratio = 0.2` (bad), Fix 3 gives: `+0.03 - 0.24 = -0.21`
- Then Fix 4 allows `final_reward` to go to `-0.2`
- Is the total penalty reasonable or too harsh?

### Check 4: Empty Response Handling
- What if `response_words` is empty?
- Division by zero in `unique_ratio` calculation?
- What if `organism_response` is None?

### SEARCH COMMANDS
```
grep -n "response_words" butterfly_chat.py
grep -n "unique_ratio" butterfly_chat.py
grep -n "coherence_score" butterfly_chat.py
```

Find variable scope issues and division by zero risks.

---

# GROK-3: Config & Integration Review

## YOUR TARGETS

### Check 1: Alpha + Beta + Gamma
In `config.json`:
- alpha=0.5, beta=0.4, gamma=0.1 → Sum = 1.0 ✓
- But does the code actually REQUIRE sum=1.0?
- What happens if they don't sum to 1.0?

### Check 2: Vocab Size Propagation
- Brain uses `config.neural.brain.vocab_size` = 50000
- Teacher now uses `config.neural.language_model.teacher.vocab_size` = 50000
- But what about `config.neural.language_model.vocabulary.max_size` = 10000?
- Is there a THIRD vocab_size that's still wrong?

### Check 3: Runtime Config Reading
In `reality_simulator/neural/trainer.py`:
- Does trainer read alpha/beta from `config.neural.language_model.training`?
- Or does it have hardcoded fallbacks that override the config?
- Check line ~139 for the actual config path used

### Check 4: Semantic Threshold Config
- Code changed default from 0.7 to 0.3
- But is there a config.json setting that overrides this?
- Search for `min_strength_threshold` in config.json

### SEARCH COMMANDS
```
grep -n "vocab_size" config.json
grep -n "alpha\|beta\|gamma" trainer.py
grep -n "min_strength" config.json
grep -n "max_size" config.json
```

Find config mismatches and override issues.

---

# GROK-4: Broadcast & Side Effects Review

## YOUR TARGETS

### Check 1: Broadcast Variable Scope
In `reality_simulator/language/butterfly_chat.py` around line 780:
- `response_words_for_broadcast` is newly calculated
- But there's already `response_words` used earlier
- Why calculate again? Are they the same?
- Is this inside a try block that might skip the calculation?

### Check 2: Broadcast Condition Regression
Original code:
```python
if reward > 0.6 and network_state:
```
New code:
```python
if reward > 0.6 and network_state and broadcast_unique_ratio > 0.5:
```
- What if `organism_response` is None? `broadcast_unique_ratio` calculation fails?
- Is this before or after the None check for `organism_response`?

### Check 3: Vocabulary Expansion Still Happening?
After broadcast protection, there's vocabulary expansion:
```python
if self.vocabulary and hasattr(self.vocabulary, 'expand_vocabulary_from_pattern'):
    self.vocabulary.expand_vocabulary_from_pattern(organism_tokens, reward)
```
- Is this INSIDE the new if-block or outside?
- Should vocabulary expansion also be protected?

### Check 4: Experience Storage Affected?
- Does `_store_chat_experience()` get called before or after these checks?
- Are we accidentally not storing experiences for repetitive outputs?
- That might break training!

### SEARCH COMMANDS
```
grep -n "broadcast" butterfly_chat.py
grep -n "expand_vocabulary" butterfly_chat.py  
grep -n "_store_chat_experience" butterfly_chat.py
grep -n "organism_response" butterfly_chat.py
```

Find side effect bugs and None-handling issues.

---

# AFTER ALL GROKS REPORT

Paste all findings back to Claude. He will:
1. Triage by severity
2. Fix any CRITICAL/HIGH issues immediately
3. Evaluate MEDIUM/LOW for next iteration
