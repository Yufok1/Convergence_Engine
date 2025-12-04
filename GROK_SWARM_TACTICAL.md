# 🎯 GROK SWARM - TACTICAL REDUNDANCY VALIDATION

## MISSION BRIEFING

This is a **redundant validation sweep** - two Groks assigned to each task to compare findings and catch anything the other misses. After 4 rounds of fixes, we need absolute confidence before testing.

## ASSIGNMENT STRUCTURE

| Task | Primary | Secondary |
|------|---------|-----------|
| **Task A: Code Path Validation** | GROK-1 | GROK-2 |
| **Task B: Config & Data Validation** | GROK-3 | GROK-4 |

Compare your findings with your partner. Discrepancies = potential bugs.

---

# TASK A: CODE PATH VALIDATION

## Assigned to: GROK-1 and GROK-2

Both of you independently verify these code paths work correctly.

### A1: Seq2Seq Training Path (CRITICAL)
Trace this EXACT execution path:

```
1. User sends message to butterfly_chat.py
2. _store_chat_experience() called with input_tokens, target_tokens
3. ExperienceBuffer.add() stores them
4. Later: trainer.train_from_chat_experiences() called
5. has_seq2seq_data() returns True
6. sample_batch_with_seq2seq() returns data
7. Tensors created: input_tokens, target_tokens
8. target_tokens.size(1) gets sequence length
9. Language loss calculated
10. Backprop + optimizer step
11. Event emitted with correct sequence_length
```

**VERIFY**: Does EVERY step work? What happens if ANY step fails?

### A2: Fallback Training Path
Trace this path when seq2seq data is NOT available:

```
1. has_seq2seq_data() returns False
2. _train_from_token_sequence() called
3. organism.token_sequence used
4. Tensors created from token_seq
5. Loss calculated
6. Optimizer created (inline pattern)
7. Backprop + step
```

**VERIFY**: Does fallback work independently of seq2seq path?

### A3: Token Generation Path
Trace token generation in neural_organism.py:

```
1. generate_tokens() called
2. Brain forward pass → language_logits
3. Vocabulary mask applied
4. Repetition penalty subtracted (2.0 base, 3.0 for last)
5. Top-k mask applied (if vocab > 40)
6. Softmax → probs
7. Multinomial sample
8. Token clamped to vocab range
9. Word decoded
```

**VERIFY**: Any path where this produces invalid tokens or NaN?

### A4: Reward Calculation Path
Trace reward in butterfly_chat.py:

```
1. _calculate_semantic_reward() called
2. response_words, response_words_set created
3. unique_ratio initialized to 1.0
4. If len > 1: unique_ratio calculated
5. coherence_score penalties applied
6. Three-tier clamping:
   - unique_ratio < 0.3 → max(-0.3, reward)
   - unique_ratio < 0.5 → max(0.0, reward)
   - else → max(0.05, reward)
7. final_reward stored in experience
```

**VERIFY**: All variables in scope? Clamping logic correct?

### OUTPUT FORMAT
```
PATH: [A1/A2/A3/A4]
STATUS: ✅ VERIFIED / ⚠️ ISSUE FOUND / ❌ BROKEN
STEPS_VERIFIED: [List each step you confirmed]
ISSUES: [Any problems found]
EDGE_CASES: [Edge cases that could fail]
```

---

# TASK B: CONFIG & DATA VALIDATION

## Assigned to: GROK-3 and GROK-4

Both of you independently verify config consistency and data availability.

### B1: Vocab Size Consistency (CRITICAL)
Find EVERY reference to vocab_size and verify they all match 50000:

**Files to check:**
- `config.json` - all vocab_size entries
- `brain.py` - default parameter
- `language_teacher.py` - default parameter (line 62 AND line 251)
- `utils.py` - ARCHITECTURE_DEFAULTS dict
- `neural_organism.py` - any hardcoded values
- `trainer.py` - any hardcoded values

**Search commands:**
```bash
grep -rn "vocab_size" --include="*.py" --include="*.json"
grep -rn "12288\|4096\|1000\b" --include="*.py" | grep -i vocab
```

**VERIFY**: Every vocab_size reference is 50000 or reads from config.

### B2: Loss Weight Consistency
Verify alpha/beta/gamma are correctly configured:

**Expected values:**
- alpha (RL loss) = 0.5
- beta (language loss) = 0.4
- gamma (concept loss) = 0.1
- Sum = 1.0

**Check:**
- `config.json` - training section
- `trainer.py` - how they're loaded
- Any hardcoded fallbacks

### B3: Data File Availability
Verify these files exist and have content:

```bash
ls -la data/butterfly_vocabulary_50k_curated.json
ls -la data/seeded_knowledge_web_50k.json
ls -la data/context_memory.json
```

**Check file contents:**
- Vocab file has ~50000 words
- Knowledge web has relationships
- Context memory has valid structure

### B4: Semantic Guidance Config
Verify semantic guidance settings:

**Expected:**
- `min_strength_threshold` = 0.3 (was 0.7)
- `semantic_boost` = 0.2
- `enabled` = true

**Check:**
- `config.json` - semantic_guidance section
- `neural_organism.py` - default value in code

### OUTPUT FORMAT
```
CHECK: [B1/B2/B3/B4]
STATUS: ✅ CONSISTENT / ⚠️ MISMATCH FOUND / ❌ MISSING
VALUES_FOUND: [List each value and location]
MISMATCHES: [Any inconsistencies]
```

---

# COMPARISON PROTOCOL

After both Groks in each task report:

## Task A Comparison (GROK-1 vs GROK-2)
- Compare step-by-step verification
- Flag any discrepancies
- If one found an issue the other missed, investigate

## Task B Comparison (GROK-3 vs GROK-4)
- Compare all values found
- Flag any different values reported
- If one found a mismatch the other missed, investigate

---

# FINAL REPORT FORMAT

Each Grok should end with:

```
GROK-[N] FINAL ASSESSMENT
========================
TASK: [A or B]
PATHS/CHECKS VERIFIED: [count]
ISSUES FOUND: [count]
CONFIDENCE: [HIGH/MEDIUM/LOW]

CRITICAL FINDINGS:
[List any showstoppers]

READY FOR TESTING: [YES/NO]
```

---

# AFTER ALL 4 GROKS REPORT

Paste all 4 reports. Claude will:
1. Compare GROK-1 vs GROK-2 findings
2. Compare GROK-3 vs GROK-4 findings
3. Resolve any discrepancies
4. Make final go/no-go decision
