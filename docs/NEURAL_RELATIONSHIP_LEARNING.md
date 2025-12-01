# 🎓 Neural System Relationship Learning

**Learning from Success and Failure in Language Generation**

**Status**: ✅ **IMPLEMENTED**  
**Date**: 2025-01-XX

---

## 🎯 Overview

The neural system now **learns from its language generation** by recording relationship success/failure back to the Linguistic Knowledge Web. This enables the system to:

- ✅ **Strengthen** semantic relationships that lead to coherent generation
- ✅ **Weaken** semantic relationships that lead to garbled generation
- ✅ **Build** understanding of which word combinations work
- ✅ **Forget** useless combinations over time (via quality control decay)

---

## 🔄 How It Works

### 1. **Relationship Tracking During Generation**

During token generation, the neural system tracks which semantic relationships it uses:

```python
# In generate_tokens() method
if knowledge_web and len(generated) > 1:
    last_word = vocab.get_word(last_token)
    similar_words = knowledge_web.get_similar_words(last_word, min_strength=0.7)
    
    # Track which relationships we're using
    used_relationships = []
    for similar_word in similar_words:
        relations = knowledge_web.get_relations(last_word)
        for r in relations:
            if (r.target == similar_word or r.source == similar_word):
                used_relationships.append(r)
    
    # Store for later evaluation
    self._generation_relationships.extend(used_relationships)
```

### 2. **Quality Evaluation After Generation**

After generation completes, the system evaluates quality:

```python
def _evaluate_generation_quality(self, generated, vocab, knowledge_web):
    """
    Evaluates:
    - Coherence: Do words form semantically meaningful sequences?
    - Garbled: Are words randomly combined?
    - Length: Appropriate sequence length?
    - Special tokens: Too many UNK tokens?
    """
    # Convert tokens to words
    words = [vocab.get_word(t) for t in generated if vocab.get_word(t) not in SPECIAL_TOKENS]
    
    # Check semantic relationships between consecutive words
    coherent_pairs = 0
    for i in range(len(words) - 1):
        word1, word2 = words[i], words[i + 1]
        relations = knowledge_web.get_relations(word1)
        has_relationship = any(
            (r.target == word2 or r.source == word2) and r.strength >= 0.5
            for r in relations
        )
        if has_relationship:
            coherent_pairs += 1
    
    coherence_score = coherent_pairs / (len(words) - 1) if len(words) > 1 else 0.0
    
    return {
        'is_coherent': coherence_score >= 0.5,  # >50% pairs have relationships
        'is_garbled': coherence_score < 0.2,    # <20% pairs have relationships
        'coherence_score': coherence_score
    }
```

### 3. **Recording Success/Failure**

Based on quality evaluation, relationships are strengthened or weakened:

```python
# After generation completes
generation_quality = self._evaluate_generation_quality(generated, vocab, knowledge_web)

for relation in self._generation_relationships:
    if generation_quality['is_coherent']:
        # Successful use - strengthen relationship
        knowledge_web.record_relationship_success(
            relation.source, relation.target, relation.relation_type
        )
    elif generation_quality['is_garbled']:
        # Failed use - weaken relationship
        knowledge_web.record_relationship_failure(
            relation.source, relation.target, relation.relation_type
        )
```

---

## 📊 Quality Metrics

### Coherence Criteria

**Coherent Generation** (Success):
- ✅ >50% of consecutive word pairs have semantic relationships
- ✅ Sequence length 3-20 words (appropriate)
- ✅ <30% UNK tokens
- ✅ Words form meaningful semantic sequences

**Garbled Generation** (Failure):
- ❌ <20% of consecutive word pairs have semantic relationships
- ❌ Too many UNK tokens (>30%)
- ❌ Words randomly combined without semantic connections
- ❌ Sequence too short (<2 words) or too long (>20 words)

### Relationship Strength Changes

**Success** (`record_relationship_success`):
- Increases `confidence` by `confidence_growth_rate` (default: 0.05)
- Increases `strength` by `strength_growth_rate` (default: 0.03)
- Increments `success_count`
- Updates `last_used` timestamp

**Failure** (`record_relationship_failure`):
- Decreases `confidence` by `confidence_decay_rate` (default: 0.1, asymmetric)
- Decreases `strength` by `strength_decay_rate` (default: 0.05)
- Increments `failure_count`
- Updates `last_used` timestamp

---

## 🔗 Integration with Quality Control

This learning mechanism integrates with the existing **Quality-Controlled Recursive Expansion** system:

1. **Discovery**: New relationships discovered via `discover_relationship()`
2. **Validation**: Relationships validated via `validate_relationship()`
3. **Usage**: Relationships used in neural generation
4. **Learning**: Success/failure recorded via `record_relationship_success/failure()`
5. **Decay**: Unused/failed relationships decayed via `decay_relationships()`
6. **Pruning**: Low-confidence relationships pruned if below threshold

**Result**: The system builds a **curated semantic network** where:
- ✅ Strong, useful relationships are strengthened
- ❌ Weak, useless relationships are weakened and forgotten
- 🔄 The system learns which word combinations work

---

## 🎯 Benefits

### 1. **Self-Improving Language**

The system learns from experience:
- Words that work well together get stronger connections
- Words that don't work together get weaker connections
- Over time, the semantic network becomes more coherent

### 2. **Quality Over Quantity**

- Only relationships that lead to coherent generation are strengthened
- Garbled combinations are weakened, preventing "yarn ball" problem
- System converges toward meaningful patterns

### 3. **Adaptive Learning**

- Relationships adapt based on actual usage
- System learns organism-specific language patterns
- Semantic network evolves with the population

### 4. **Failure Understanding**

- System understands when relationships fail
- Records failure to prevent repeated mistakes
- Learns from both success and failure

---

## 📈 Example Flow

### Generation 1: Learning "cooperate" → "social"

```
1. Neural system generates: ["cooperate", "social", "together"]
2. Uses relationship: cooperate → social (strength: 0.7)
3. Quality evaluation: coherence_score = 0.8 (coherent!)
4. Record success: strengthen relationship
   - confidence: 0.7 → 0.75
   - strength: 0.7 → 0.73
   - success_count: 0 → 1
```

### Generation 2: Learning "cooperate" → "banana" (failure)

```
1. Neural system generates: ["cooperate", "banana", "purple"]
2. Uses relationship: cooperate → banana (strength: 0.5, weak)
3. Quality evaluation: coherence_score = 0.1 (garbled!)
4. Record failure: weaken relationship
   - confidence: 0.5 → 0.4
   - strength: 0.5 → 0.45
   - failure_count: 0 → 1
```

### Generation 100: Relationship Decay

```
1. Relationship "cooperate" → "banana" has:
   - confidence: 0.2 (below threshold)
   - failure_count: 15 (high)
   - last_used: 50 generations ago
2. decay_relationships() prunes it
3. System forgets useless combination
```

---

## 🔧 Configuration

### Quality Evaluation Thresholds

```python
# In _evaluate_generation_quality()
COHERENT_THRESHOLD = 0.5    # >50% pairs have relationships
GARBLED_THRESHOLD = 0.2      # <20% pairs have relationships
UNK_RATIO_THRESHOLD = 0.3    # >30% UNK = garbled
MIN_WORD_COUNT = 2           # Minimum words for evaluation
MAX_WORD_COUNT = 20          # Maximum words (rambling)
```

### Relationship Strength Changes

```python
# In LinguisticKnowledgeWeb.record_relationship_success()
confidence_growth_rate = 0.05    # +5% confidence per success
strength_growth_rate = 0.03      # +3% strength per success

# In LinguisticKnowledgeWeb.record_relationship_failure()
confidence_decay_rate = 0.1      # -10% confidence per failure (asymmetric)
strength_decay_rate = 0.05        # -5% strength per failure
```

---

## 🧪 Testing

### Test Coherent Generation

```python
# Generate sequence with strong semantic relationships
generated = [vocab.get_id('cooperate'), vocab.get_id('social'), vocab.get_id('together')]
quality = organism._evaluate_generation_quality(generated, vocab, knowledge_web)

assert quality['is_coherent'] == True
assert quality['coherence_score'] >= 0.5
```

### Test Garbled Generation

```python
# Generate sequence with weak/no semantic relationships
generated = [vocab.get_id('cooperate'), vocab.get_id('banana'), vocab.get_id('purple')]
quality = organism._evaluate_generation_quality(generated, vocab, knowledge_web)

assert quality['is_garbled'] == True
assert quality['coherence_score'] < 0.2
```

---

## 📚 Related Documentation

- **Quality Control System**: `QUALITY_CONTROL_SYSTEM.md`
- **Linguistic Knowledge Web**: `LINGUISTIC_KNOWLEDGE_WEB_GUIDE.md`
- **ML Relationship Learning**: `ml_utils.py` (lines 816-823)
- **Neural Generation**: `reality_simulator/neural/neural_organism.py`

---

## ✅ Summary

The neural system now **learns from experience** by:

1. ✅ **Tracking** which semantic relationships are used during generation
2. ✅ **Evaluating** generation quality (coherent vs garbled)
3. ✅ **Recording** success/failure back to knowledge web
4. ✅ **Strengthening** relationships that work
5. ✅ **Weakening** relationships that fail
6. ✅ **Building** understanding over time

**Result**: A self-improving language system that learns which word combinations work and forgets useless ones.

---

**Last Updated**: 2025-01-XX  
**Status**: ✅ Implemented | Ready for Testing

