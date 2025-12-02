# RCUS Implementation Audit Plan
## For Grok Task Force Assessment

**Date:** December 1, 2025  
**Purpose:** Comprehensive audit of RCUS integration for gaps, inconsistencies, and alignment issues  
**Target:** 4 Grok agents performing parallel analysis

---

## Task Force Assignment

| Grok | Focus Area | Primary Files | Key Questions |
|------|------------|---------------|---------------|
| **Grok 1** | Mathematical Consistency | concept_system.py | Are the composition operators mathematically sound? |
| **Grok 2** | Integration Integrity | brain.py, trainer.py | Does RCUS integrate cleanly with existing systems? |
| **Grok 3** | Grounding Validity | concept_system.py, neural_organism.py | Are axioms properly grounded in state features? |
| **Grok 4** | Language Bridge Coherence | concept_system.py, vocabulary | Does the language bridge correctly map concepts to words? |

---

# GROK 1: Mathematical Consistency Audit

## Objective
Verify that composition operators are mathematically well-defined, consistent, and produce meaningful results.

## Files to Analyze
- `reality_simulator/neural/concept_system.py` (lines 130-230: Composition Operators)

## Audit Checklist

### 1.1 WITH Operator (Symmetric Conjunction)
```python
class WithOperator(CompositionOperator):
    def forward(self, embed_a, embed_b):
        bilinear_out = self.bilinear(embed_a, embed_b)
        concat = torch.cat([embed_a, embed_b], dim=-1)
        gate = torch.sigmoid(self.gate(concat))
        interaction = embed_a * embed_b * gate
        return self.norm(bilinear_out + interaction)
```

**Questions to Answer:**
- [ ] Is WITH truly symmetric? Does `WITH(A, B) ≈ WITH(B, A)`?
- [ ] Does the bilinear layer preserve symmetry or break it?
- [ ] Is the gated interaction meaningful or just noise?
- [ ] Should there be explicit symmetry enforcement?

**Test to Propose:**
```python
# Symmetry test
state = torch.randn(24)
ab = concept_system.compose('SELF', 'WITH', 'OTHER', state)
ba = concept_system.compose('OTHER', 'WITH', 'SELF', state)
symmetry_error = torch.norm(ab[0] - ba[0])
# Should be small if symmetric
```

### 1.2 CAUSE Operator (Asymmetric Causal)
```python
class CauseOperator(CompositionOperator):
    def forward(self, cause, effect):
        cause_repr = F.relu(self.cause_transform(cause))
        effect_repr = F.relu(self.effect_transform(effect))
        combined = torch.cat([cause_repr, effect_repr], dim=-1)
        return self.norm(self.combine(combined))
```

**Questions to Answer:**
- [ ] Is CAUSE properly asymmetric? Is `CAUSE(A, B) ≠ CAUSE(B, A)` guaranteed?
- [ ] Does the ReLU activation lose information for negative embeddings?
- [ ] Is causal directionality preserved through the transformation?
- [ ] Should there be a causal attention mechanism instead?

**Test to Propose:**
```python
# Asymmetry test
ab = concept_system.compose('DO', 'CAUSE', 'GOOD', state)
ba = concept_system.compose('GOOD', 'CAUSE', 'DO', state)
asymmetry = torch.norm(ab[0] - ba[0])
# Should be significantly non-zero
```

### 1.3 MODIFY Operator (Attribute Modification)
```python
class ModifyOperator(CompositionOperator):
    def forward(self, modifier, base):
        scale = torch.sigmoid(self.modifier_scale(modifier))
        shift = torch.tanh(self.modifier_shift(modifier))
        return self.norm(base * scale + shift)
```

**Questions to Answer:**
- [ ] Does MODIFY preserve the "base" concept's identity?
- [ ] Can scale become 0 (destroying the base concept)?
- [ ] Is the shift bounded appropriately by tanh?
- [ ] Should MODIFY be idempotent? `MODIFY(MODIFY(x)) ≈ MODIFY(x)`?

### 1.4 SEQUENCE Operator (Temporal Ordering)
```python
class SequenceOperator(CompositionOperator):
    def forward(self, first, second):
        sequence = torch.stack([first, second], dim=1)
        _, final = self.temporal(sequence)
        return self.norm(final.squeeze(0))
```

**Questions to Answer:**
- [ ] Does GRU properly encode temporal ordering?
- [ ] Is the final hidden state the right output (vs. full sequence)?
- [ ] Can SEQUENCE handle more than 2 elements for chaining?
- [ ] Is there vanishing gradient risk for deeper compositions?

### 1.5 Value Prediction Consistency
**Questions to Answer:**
- [ ] Does `predict_value()` produce consistent outputs for similar concepts?
- [ ] Is the value head properly calibrated (outputs in reasonable range)?
- [ ] Should value prediction be relative or absolute?

### 1.6 Composition Algebra
**Questions to Answer:**
- [ ] Is there associativity? `(A WITH B) WITH C ≈ A WITH (B WITH C)`?
- [ ] Are there identity elements? `A WITH EXIST ≈ A`?
- [ ] Are there inverse operations?
- [ ] Do compositions form a proper algebraic structure?

---

# GROK 2: Integration Integrity Audit

## Objective
Verify that RCUS integrates correctly with OrganismBrain, NeuralTrainer, and the existing training loop.

## Files to Analyze
- `reality_simulator/neural/brain.py` (ConceptHead integration)
- `reality_simulator/neural/trainer.py` (triple-loss system)
- `reality_simulator/neural/utils.py` (create_brain function)
- `config.json` (configuration)

## Audit Checklist

### 2.1 OrganismBrain Integration
```python
# In brain.py forward()
if return_concept_outputs and self.use_concept_head:
    concept_outputs = self.concept_head(x_for_action)
```

**Questions to Answer:**
- [ ] Is `x_for_action` the right input for concept head? (hidden state after fc2)
- [ ] Are gradients flowing correctly through concept head?
- [ ] Does concept head receive the same hidden state as action/language heads?
- [ ] Is there proper weight initialization for concept head?

**Potential Issues to Check:**
- [ ] Does `return_concept_outputs=True` work correctly in all forward() code paths?
- [ ] Is the crossover() method properly copying concept head weights?
- [ ] Does mutate() affect concept head parameters?

### 2.2 NeuralTrainer Triple-Loss
```python
# In trainer.py train_step()
loss = self.rl_loss_weight * rl_loss
if language_loss is not None:
    loss = loss + self.language_loss_weight * language_loss
if concept_loss is not None:
    loss = loss + self.concept_loss_weight * concept_loss
```

**Questions to Answer:**
- [ ] Are loss weights correctly summing to ~1.0 (0.8 + 0.1 + 0.1)?
- [ ] Is concept_loss computed on the same batch as rl_loss?
- [ ] Does the concept system share optimizer with brain, or is it separate?
- [ ] Is gradient clipping applied to concept system parameters?

**Potential Issues to Check:**
- [ ] Is `compute_concept_loss()` called with correct tensor shapes?
- [ ] Are concept utilities being updated during training?
- [ ] Is concept loss magnitude comparable to rl_loss and language_loss?

### 2.3 Configuration Flow
```python
# In utils.py create_brain()
use_concept_head = concept_config.get('enabled', False)
num_key_compositions = concept_config.get('num_key_compositions', 5)
```

**Questions to Answer:**
- [ ] Does config flow correctly from config.json → main.py → trainer.py → brain?
- [ ] Is `concept_system` config nested under `neural` or at root level?
- [ ] Are defaults sensible if config is missing?

**Config Validation:**
```json
// Check these paths exist and are correct:
neural.concept_system.enabled
neural.concept_system.embed_dim
neural.concept_system.concept_loss_weight
neural.concept_system.num_key_compositions
neural.brain.input_dim  // Should be 24, not 18
```

### 2.4 Concept System Ownership
**Questions to Answer:**
- [ ] Who owns the ConceptSystem instance? (Trainer creates it)
- [ ] Is it shared across all organisms or per-organism?
- [ ] Is there a risk of race conditions in multi-threaded training?
- [ ] Is the concept system on the correct device (CPU/CUDA)?

### 2.5 Persistence Integration
**Questions to Answer:**
- [ ] Is concept system saved when simulation state is saved?
- [ ] Is concept system loaded when simulation state is loaded?
- [ ] Are concept utilities and use counts persisted?
- [ ] Is there a migration path for old saves without concept data?

---

# GROK 3: Grounding Validity Audit

## Objective
Verify that axioms are properly grounded in organism state features and that the grounding is semantically meaningful.

## Files to Analyze
- `reality_simulator/neural/concept_system.py` (AXIOM_DEFINITIONS, grounding)
- `reality_simulator/neural/neural_organism.py` (get_state_features)

## Audit Checklist

### 3.1 Feature Index Validity
**Cross-reference this mapping:**

| Axiom | Feature Indices | Claimed Feature | Actual Feature (verify) |
|-------|-----------------|-----------------|-------------------------|
| EXIST | [0, 17] | fitness, system_health | ? |
| ONE | [2] | inverse of connections | ? |
| MANY | [2, 21] | connections, density | ? |
| MORE | [0, 3] | fitness, neighbor_fitness | ? |
| LESS | [3, 0] | neighbor_fitness, fitness | ? |
| SAME | [0, 3] | fitness, neighbor_fitness | ? |
| SELF | [0, 18, 19] | fitness, battle, reputation | ? |
| OTHER | [3, 21] | neighbor_fitness, density | ? |
| WITH | [2, 6] | connections, clustering | ? |
| GOOD | [0, 23, 17] | fitness, trend, health | ? |
| BAD | [12, 15, 16] | VP components | ? |
| DO | [22, 18] | learning, battle | ? |
| CAUSE | [4, 5] | flow_in, flow_out | ? |
| BEFORE | [8, 9] | age, parent_fitness | ? |
| AFTER | [23, 22] | trend, learning | ? |
| NOW | [10, 11] | breath_phase, breath_amp | ? |
| HERE | [6, 7] | clustering, distance | ? |
| THERE | [7] | distance | ? |

**Verify in neural_organism.py get_state_features():**
```python
# Line ~235-400 in neural_organism.py
# Check that feature indices match actual feature order
```

**Questions to Answer:**
- [ ] Do all feature indices fall within 0-23 range?
- [ ] Are feature semantics correctly matched to axioms?
- [ ] Are any features used by multiple axioms appropriately?
- [ ] Are any important features unused?

### 3.2 Grounding Function Validity
```python
def _compute_grounding_signal(self, state, axiom_def):
    features = state[:, valid_indices]
    
    if axiom_def.grounding_fn == 'direct':
        return features.mean(dim=-1, keepdim=True)
    elif axiom_def.grounding_fn == 'inverse':
        return 1.0 - features.mean(dim=-1, keepdim=True)
    elif axiom_def.grounding_fn == 'diff':
        return (features[:, 0:1] - features[:, 1:2]) * 0.5 + 0.5
    elif axiom_def.grounding_fn == 'inverse_diff':
        diff = torch.abs(features[:, 0:1] - features[:, 1:2])
        return 1.0 - diff
```

**Questions to Answer:**
- [ ] Is 'direct' grounding appropriate for all axioms using it?
- [ ] Does 'inverse' correctly flip the semantics?
- [ ] Is 'diff' correctly computing comparisons (MORE/LESS)?
- [ ] Does 'inverse_diff' correctly compute SAME (similarity)?
- [ ] Are outputs properly bounded in [0, 1]?

### 3.3 Semantic Coherence
**Test scenarios:**

| Scenario | Expected Axiom Activation |
|----------|---------------------------|
| High fitness organism | SELF strong, GOOD strong, MORE strong |
| Isolated organism (no connections) | ONE strong, WITH weak, MANY weak |
| High VP (system stress) | BAD strong, GOOD weak |
| Near neighbors | HERE strong, THERE weak |
| Old organism (high age) | BEFORE strong |
| Rapidly improving | AFTER strong (health_trend high) |

**Questions to Answer:**
- [ ] Do axioms activate as expected in these scenarios?
- [ ] Are there degenerate cases where all axioms are equally active?
- [ ] Is there sufficient discrimination between axiom activations?

### 3.4 Grounding Network Behavior
```python
self.grounding_net = nn.Sequential(
    nn.Linear(state_dim, embed_dim),
    nn.ReLU(),
    nn.Linear(embed_dim, embed_dim),
    nn.Tanh()
)
```

**Questions to Answer:**
- [ ] Does the grounding network learn meaningful representations?
- [ ] Is Tanh output appropriate for modulating embeddings?
- [ ] Is there risk of vanishing gradients through this path?
- [ ] Should grounding be per-axiom or shared?

---

# GROK 4: Language Bridge Coherence Audit

## Objective
Verify that the language bridge correctly maps between concepts and vocabulary, and integrates with existing language systems.

## Files to Analyze
- `reality_simulator/neural/concept_system.py` (ConceptLanguageBridge)
- `reality_simulator/language/` (existing language system)
- `reality_simulator/memory/context_memory.py` (vocabulary)

## Audit Checklist

### 4.1 Vocabulary Mapping Completeness
```python
AXIOM_VOCABULARY = {
    'EXIST': ['exist', 'be', 'presence', 'alive', 'real', 'is'],
    'ONE': ['one', 'single', 'alone', 'individual', 'only', 'sole'],
    # ... 18 axioms total
}
```

**Questions to Answer:**
- [ ] Are all 18 axioms covered in AXIOM_VOCABULARY?
- [ ] Are the word choices semantically appropriate?
- [ ] Are there overlapping words that map to multiple axioms? (conflicts)
- [ ] Are common words missing that should be included?
- [ ] Are the words likely to appear in organism vocabulary?

**Word Coverage Analysis:**
```python
# Count words per axiom
for axiom, words in AXIOM_VOCABULARY.items():
    print(f"{axiom}: {len(words)} words")
# Should be roughly balanced
```

### 4.2 Phrase Parsing Robustness
```python
def phrase_to_concept(self, phrase):
    words = phrase.lower().split()
    # ... matching logic
```

**Test Cases to Verify:**
- [ ] "self with other" → ('SELF', 'WITH', 'OTHER') ✓
- [ ] "SELF WITH OTHER" → ('SELF', 'WITH', 'OTHER') (case handling)
- [ ] "me together them" → ('SELF', 'WITH', 'OTHER') (synonyms)
- [ ] "self other" → None (missing operator)
- [ ] "with self other" → None (wrong order)
- [ ] "self with with other" → ? (duplicate operator)
- [ ] "the self is with the other" → ? (noise words)

**Questions to Answer:**
- [ ] Is phrase parsing robust to word order variations?
- [ ] Does it handle synonyms for operators?
- [ ] Are noise words (the, a, is) filtered?
- [ ] What happens with malformed phrases?

### 4.3 Integration with Existing Vocabulary
**Questions to Answer:**
- [ ] Does `seed_vocabulary_with_axioms()` work with actual Vocabulary class?
- [ ] Are axiom words already in the base vocabulary?
- [ ] Is there a conflict between axiom words and existing words?
- [ ] Does the language teacher know about axiom words?

**Check compatibility:**
```python
# Find the actual vocabulary class used
from reality_simulator.memory.context_memory import Vocabulary
# or
from reality_simulator.language.vocabulary import Vocabulary

# Verify methods exist
assert hasattr(vocab, 'add_word') or hasattr(vocab, 'add')
assert hasattr(vocab, 'encode')
assert hasattr(vocab, 'decode')
```

### 4.4 Grounded Word Selection
```python
def get_grounded_axiom_words(self, state, threshold=0.5):
    for axiom_name, axiom_def in AXIOM_DEFINITIONS.items():
        grounding = self.concept_system._compute_grounding_signal(state, axiom_def)
        strength = grounding.mean().item()
        if strength > threshold:
            words = self.AXIOM_VOCABULARY.get(axiom_name, [])
            relevant_words.extend(words[:int(1 + strength * 2)])
```

**Questions to Answer:**
- [ ] Is threshold=0.5 appropriate? (may exclude valid axioms)
- [ ] Is the word count formula `1 + strength * 2` sensible?
- [ ] Are returned words ordered by relevance?
- [ ] Can this be used for language generation guidance?

### 4.5 Explanation Quality
```python
def explain_concept(self, concept_name):
    # Returns human-readable explanation
```

**Test explanations:**
- [ ] Are explanations grammatically correct?
- [ ] Do they accurately describe the concept?
- [ ] Are they useful for debugging/logging?
- [ ] Should explanations be dynamic (based on state)?

---

# Cross-Cutting Concerns

## For All Groks to Consider

### A. Error Handling
- [ ] What happens if an invalid axiom name is passed?
- [ ] What happens if state tensor is wrong shape?
- [ ] Are there proper try/except blocks?
- [ ] Are errors logged appropriately?

### B. Performance
- [ ] Is concept composition called too frequently?
- [ ] Should compositions be cached?
- [ ] Is there memory growth from concept_memory dict?
- [ ] Is CUDA memory properly managed?

### C. Testing Coverage
- [ ] Are there unit tests for each operator?
- [ ] Are there integration tests for training loop?
- [ ] Are there edge case tests (empty state, zero values)?
- [ ] Is there test coverage reporting?

### D. Documentation
- [ ] Are all public methods documented?
- [ ] Are the axiom definitions explained?
- [ ] Is there a usage guide?
- [ ] Are error messages helpful?

---

# Deliverables

Each Grok should provide:

1. **Gap Report** - List of missing functionality or incomplete implementations
2. **Inconsistency Report** - Conflicts between components or with existing systems
3. **Risk Assessment** - Potential failure modes and their severity
4. **Recommendations** - Specific fixes or improvements with code examples
5. **Test Cases** - Proposed tests to verify fixes

---

# Coordination

After individual audits, convene to cross-reference findings:

1. **Grok 1 ↔ Grok 3:** Mathematical validity of grounding
2. **Grok 2 ↔ Grok 4:** Integration of brain concepts with language
3. **Grok 1 ↔ Grok 2:** Composition algebra in training loop
4. **Grok 3 ↔ Grok 4:** State features to vocabulary mapping

---

# Priority Issues to Watch

Based on implementation review, these are highest-risk areas:

1. **input_dim mismatch** - Was 18, changed to 24. Verify all paths use 24.
2. **Concept system ownership** - Single shared instance in trainer. Thread safety?
3. **Feature index accuracy** - Axiom definitions assume specific feature order.
4. **Loss scale balance** - concept_loss may be different magnitude than rl_loss.
5. **Vocabulary integration** - Bridge assumes vocabulary API that may not exist.

---

# Timeline

| Phase | Duration | Activity |
|-------|----------|----------|
| 1 | 30 min | Individual audits (parallel) |
| 2 | 15 min | Cross-reference findings |
| 3 | 15 min | Prioritize issues |
| 4 | 30 min | Draft fixes |
| 5 | 15 min | Final review |

**Total:** ~2 hours for comprehensive audit

---

# Contact

Implementation questions can be directed to the RCUS integration summary document:
`RCUS_INTEGRATION_SUMMARY.md`

Key source files:
- `reality_simulator/neural/concept_system.py` - Main implementation
- `reality_simulator/neural/test_rcus_integration.py` - Existing tests
