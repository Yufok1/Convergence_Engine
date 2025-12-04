# 🦋 BUTTERFLY SYSTEM - LANGUAGE DIAGNOSTIC MISSION

## CONTEXT BRIEFING (READ THIS FIRST)

You are part of a 4-agent diagnostic swarm analyzing the Butterfly System's language generation problem. The system produces repetitive outputs like "was was was" or "shared shared shared" instead of coherent responses.

## SYSTEM ARCHITECTURE (Quick Reference)

The language system has these key components:
1. **LanguageVocabulary** (`reality_simulator/language_system.py`) - Token management
2. **OrganismBrain** (`reality_simulator/neural/brain.py`) - Neural network with language head
3. **NeuralOrganism** (`reality_simulator/neural/neural_organism.py`) - Has `generate_tokens()` method
4. **NeuralTrainer** (`reality_simulator/neural/trainer.py`) - Training loop with language loss
5. **ButterflyChatRouter** (`reality_simulator/language/butterfly_chat.py`) - Routes messages, stores experiences
6. **AtomicLanguageSystem** (`reality_simulator/language/atomic_language.py`) - Concept associations
7. **LinguisticKnowledgeWeb** (`reality_simulator/language/linguistic_knowledge_web.py`) - Semantic relationships

## KNOWN PROBLEM AREAS (Investigate These)

1. **Training Target Mismatch**: Trainer may use `organism.token_sequence` (concatenated history) instead of proper `input_tokens`/`target_tokens` pairs from experience buffer
2. **Logit-Vocabulary Mismatch**: Brain outputs 12,288 logits but actual vocabulary may be 50-500 words
3. **No Repetition Penalty**: Nothing prevents sampling the same token repeatedly
4. **Sampling Method**: Uses pure `torch.multinomial()` without top-k or nucleus sampling
5. **Reward Shaping**: May not adequately penalize repetitive outputs

## YOUR MISSION

You will be told which GROK number you are (1, 2, 3, or 4). Find your section below.

**OUTPUT FORMAT**: For each issue found, report:
```
ISSUE: [Brief description]
FILE: [Full path]
LINE: [Line number or range]
CODE: [Relevant code snippet]
PROBLEM: [Why this causes repetition]
SUGGESTED_FIX: [Specific code change needed]
```

Do NOT implement fixes. Just find and report. Claude will implement.

---

# GROK-1: Training Pipeline Investigator

## YOUR SEARCH TARGETS

### Target 1: Training Target Source
Search `reality_simulator/neural/trainer.py` for:
- How `token_sequence` is used in training
- Whether `input_tokens` and `target_tokens` from Experience are ever used
- The actual tensors fed to language loss calculation
- Look for any mismatch between what chat stores vs what trainer uses

Key methods to examine:
- `train_step()` 
- `calculate_language_loss()`
- Any method that samples from experience buffer

### Target 2: Experience Buffer Usage
Search `reality_simulator/neural/experience.py` for:
- `sample_batch()` - does it return language tokens?
- `sample_batch_with_language()` - does this exist?
- Whether `input_tokens`/`target_tokens` fields are ever accessed after storage

### Target 3: Training Frequency & Triggers
Search for:
- When training is actually triggered
- `_trigger_chat_training()` in butterfly_chat.py
- Whether training happens often enough
- Minimum experience buffer size before training starts

### Target 4: Loss Weighting
Search `trainer.py` for:
- `rl_loss_weight`, `language_loss_weight` values
- Whether language loss is actually being computed (check for None guards)
- The actual alpha/beta/gamma weights in triple-loss system

## SEARCH COMMANDS (grep patterns)
```
token_sequence
sample_batch
input_tokens
target_tokens
language_loss
rl_loss_weight
train_step
_trigger
```

Report ALL mismatches between stored experience format and training consumption format.

---

# GROK-2: Token Generation Pipeline Investigator

## YOUR SEARCH TARGETS

### Target 1: The generate_tokens() Method
Search `reality_simulator/neural/neural_organism.py` for the full `generate_tokens()` method:
- How tokens are sampled (multinomial? argmax? top-k?)
- Whether there's ANY repetition penalty
- How the vocabulary mask is applied
- The early stopping conditions

### Target 2: Logit Processing
In the same file, find:
- Where logits come from brain
- How logits are masked to vocabulary size
- The temperature scaling logic
- Any semantic boost/guidance code

### Target 3: Brain Language Head
Search `reality_simulator/neural/brain.py` for:
- `fc_language` layer definition
- `vocab_size` parameter and where it comes from
- The `forward()` path when `return_language_logits=True`
- Whether language logits match actual vocabulary

### Target 4: Token-to-Word Decoding
Search `reality_simulator/language_system.py` for:
- `decode()` method
- `get_word()` method  
- How `<UNK>` tokens are handled
- Whether decoded words can be empty

## SEARCH COMMANDS
```
generate_tokens
multinomial
temperature
vocab_size
fc_language
logits
decode
get_word
<UNK>
```

Find ANY place where token sampling could produce repeated or invalid tokens.

---

# GROK-3: Reward & Feedback Loop Investigator

## YOUR SEARCH TARGETS

### Target 1: Semantic Reward Calculation
Search `reality_simulator/language/butterfly_chat.py` for:
- `_calculate_semantic_reward()` method - full implementation
- What gets rewarded vs penalized
- Whether repetition is explicitly penalized
- The base reward value and how it's modified

### Target 2: Reward Storage Path
In same file, find:
- `_store_chat_experience()` method
- What reward value actually gets stored
- Whether reward can be 0 or negative
- How reward flows to experience buffer

### Target 3: Reward Consumption in Training
Search `trainer.py` for:
- How `rewards_tensor` is used
- Whether rewards actually influence language learning
- The Q-value update formula
- Any reward clipping or normalization

### Target 4: Feedback Loops
Search for:
- Knowledge broadcast (`_broadcast_successful_response`)
- Whether high rewards propagate to other organisms
- Any amplification of repetitive patterns
- Vocabulary expansion triggers

## SEARCH COMMANDS
```
reward
_calculate_semantic_reward
_store_chat_experience
unique_ratio
overlap_score
coherence
penalty
broadcast
```

Find ANY way that repetitive outputs could be positively reinforced or not penalized.

---

# GROK-4: Vocabulary & Knowledge Web Investigator

## YOUR SEARCH TARGETS

### Target 1: Vocabulary Initialization
Search `reality_simulator/language_system.py` for:
- `__post_init__` or initialization
- `build_from_language_anchors()`
- Where vocabulary words actually come from
- The `max_vocab_size` vs actual words added

### Target 2: Vocabulary-Brain Sync
Search for:
- Where brain's `vocab_size` parameter is set
- Config values for vocabulary size
- Whether brain and vocabulary use same size
- Any place these could get out of sync

### Target 3: Knowledge Web State
Search `reality_simulator/language/linguistic_knowledge_web.py` for:
- How relationships are stored
- `get_similar_words()` method
- `get_relations()` method
- Whether the web is empty on startup

### Target 4: Semantic Guidance Activation
Search `neural_organism.py` for:
- Where `knowledge_web` is accessed
- The `semantic_config` usage
- `min_strength_threshold` checks
- Whether semantic boost actually fires

### Target 5: Data Files
Check these data files exist and have content:
- `data/butterfly_vocabulary_50k_curated.json`
- `data/seeded_knowledge_web_50k.json`
- `data/context_memory.json`

## SEARCH COMMANDS
```
vocab_size
max_vocab_size
knowledge_web
get_similar_words
semantic_guidance
min_strength
language_anchors
build_from
seeded
curated
```

Find ANY place where vocabulary or semantic knowledge is empty, uninitialized, or mismatched.

---

# AFTER ALL GROKS REPORT

Paste all findings back to Claude. He will:
1. Synthesize all reports into unified bug list
2. Prioritize by impact
3. Implement surgical fixes
4. Verify fixes don't break other functionality
