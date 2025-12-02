# RCUS Integration Summary
## Recursive Conceptual Understanding System - Complete Implementation

**Date:** December 1, 2025  
**Status:** ✅ Complete - All 6/6 integration tests passing

---

## Overview

RCUS (Recursive Conceptual Understanding System) has been fully integrated into the Convergence Engine's neural architecture. This enables organisms to develop **compositional understanding** through lived experience - forming concepts, combining them, and using them to make better decisions.

**Core Principle:** Infinite possibility from finite resources through recursive composition of 18 primitive axioms.

---

## Files Changed

### New Files

| File | Lines | Purpose |
|------|-------|---------|
| `reality_simulator/neural/concept_system.py` | ~800 | Core RCUS implementation |
| `reality_simulator/neural/test_rcus_integration.py` | ~300 | Integration test suite |

### Modified Files

| File | Changes |
|------|---------|
| `reality_simulator/neural/brain.py` | Added ConceptHead, `use_concept_head` param, `return_concept_outputs` in forward() |
| `reality_simulator/neural/trainer.py` | Triple-loss system (RL + Language + Concept), concept system initialization |
| `reality_simulator/neural/utils.py` | Updated `create_brain()` to handle concept config |
| `reality_simulator/neural/__init__.py` | Exported new concept system components |
| `config.json` | Added `concept_system` config section, fixed `input_dim` from 18 to 24 |

---

## Architecture

### OrganismBrain (Extended)
```
OrganismBrain
├── fc1 → fc2 (hidden layers) [existing]
├── Action Head (DQN) [existing]
├── Language Head (next-token prediction) [existing]
└── Concept Head (RCUS) [NEW]
    ├── axiom_relevance: (batch, 18) - which axioms are active
    ├── composition_value: (batch, 5) - predicted value of key compositions
    └── context_embed: (batch, hidden_dim) - context for grounding
```

### NeuralTrainer (Extended)
```
Triple-Loss System:
  total_loss = α * rl_loss + β * language_loss + γ * concept_loss
  
  Default weights:
  - α (rl_loss_weight): 0.8
  - β (language_loss_weight): 0.1  
  - γ (concept_loss_weight): 0.1
```

### ConceptSystem (New)
```
ConceptSystem
├── Axiom Embeddings: nn.Embedding(18, 64)
├── Grounding Network: state → embedding modulation
├── Composition Operators:
│   ├── WITH: Bilinear + gated (symmetric conjunction)
│   ├── CAUSE: Asymmetric causal (A→B ≠ B→A)
│   ├── MODIFY: Scale + shift (adjective-like)
│   └── SEQUENCE: GRU temporal ordering
├── Value Head: concept → predicted reward
└── Concept Memory: stores useful compositions + utility scores
```

### ConceptLanguageBridge (New)
```
ConceptLanguageBridge
├── AXIOM_VOCABULARY: 18 axioms → 107 vocabulary words
├── concept_to_phrase(): "SELF_WITH_OTHER" → "self with other"
├── phrase_to_concept(): "self with other" → ('SELF', 'WITH', 'OTHER')
├── explain_concept(): human-readable explanations
├── get_grounded_axiom_words(): state → relevant vocabulary
└── seed_vocabulary_with_axioms(): initialize vocabulary with axiom words
```

---

## The 18 Axioms

Grounded in the 24-dimensional organism state vector:

| Category | Axiom | Feature Indices | Description |
|----------|-------|-----------------|-------------|
| **Existence** | EXIST | [0, 17] | Being alive (fitness + system_health) |
| | ONE | [2] | Singular (inverse of connections) |
| | MANY | [2, 21] | Plurality (connections + density) |
| **Comparison** | MORE | [0, 3] | Greater than (fitness vs neighbor) |
| | LESS | [3, 0] | Less than (neighbor vs fitness) |
| | SAME | [0, 3] | Equal (inverse of difference) |
| **Agency** | SELF | [0, 18, 19] | Self-identity (fitness + battle + reputation) |
| | OTHER | [3, 21] | Others (neighbor_fitness + density) |
| | WITH | [2, 6] | Togetherness (connections + clustering) |
| **Value** | GOOD | [0, 23, 17] | Positive (fitness + trend + health) |
| | BAD | [12, 15, 16] | Negative (VP components) |
| **Action** | DO | [22, 18] | Agency (learning_progress + battle_ratio) |
| | CAUSE | [4, 5] | Effect (resource flows) |
| **Time** | BEFORE | [8, 9] | Past (age + parent_fitness) |
| | AFTER | [23, 22] | Future (trend + learning) |
| | NOW | [10, 11] | Present (breath phase + amplitude) |
| **Space** | HERE | [6, 7] | Local (clustering, inverse distance) |
| | THERE | [7] | Distant (distance to nearest) |

---

## 24D State Vector (Reference)

```python
# From neural_organism.py get_state_features():
features[0]  = fitness
features[1]  = resource_level
features[2]  = num_connections
features[3]  = avg_neighbor_fitness
features[4]  = flow_in
features[5]  = flow_out
features[6]  = clustering_coefficient
features[7]  = distance_to_nearest
features[8]  = generation_age
features[9]  = parent_fitness
features[10] = breath_phase
features[11] = breath_amplitude
features[12] = trait_divergence (VP)
features[13] = network_coherence (VP)
features[14] = quantum_entropy (VP)
features[15] = evolution_pressure (VP)
features[16] = phase_mismatch (VP)
features[17] = system_health
features[18] = battle_ratio
features[19] = alliance_reputation
features[20] = language_fluency
features[21] = environmental_density
features[22] = learning_progress
features[23] = health_trend
```

---

## Key Compositions

Default compositions used for decision-making:

```python
KEY_COMPOSITIONS = [
    ('SELF', 'WITH', 'OTHER'),     # Social situation
    ('DO', 'CAUSE', 'GOOD'),        # Purposeful action → reward
    ('DO', 'CAUSE', 'BAD'),         # Action → harm (to avoid)
    ('MORE', 'MODIFY', 'GOOD'),     # Better outcomes
    ('SELF', 'WITH', 'GOOD'),       # Self-benefit
]
```

---

## Config.json Changes

Added to `neural` section:

```json
"concept_system": {
  "enabled": true,
  "embed_dim": 64,
  "concept_loss_weight": 0.1,
  "num_key_compositions": 5,
  "utility_update_alpha": 0.1
}
```

Also changed:
- `neural.brain.input_dim`: 18 → 24 (to match actual state vector size)

---

## API Usage

### Creating Brain with Concept Head
```python
from reality_simulator.neural.brain import OrganismBrain

brain = OrganismBrain(
    input_dim=24,
    hidden_dim=64,
    output_dim=6,
    use_language_head=True,
    vocab_size=10000,
    use_concept_head=True,        # Enable RCUS
    num_key_compositions=5
)
```

### Forward Pass with All Outputs
```python
# Get all three outputs
action_probs, lang_logits, concept_outputs = brain(
    state_tensor,
    return_language_logits=True,
    return_concept_outputs=True
)

# concept_outputs is a dict:
# - 'axiom_relevance': (batch, 18)
# - 'composition_value': (batch, 5)
# - 'context': (batch, hidden_dim)
```

### Using ConceptSystem Directly
```python
from reality_simulator.neural.concept_system import (
    ConceptSystem, 
    compute_concept_loss,
    KEY_COMPOSITIONS
)

# Create system
concept_system = ConceptSystem(state_dim=24, embed_dim=64, device='cuda')

# Get grounded axiom embedding
self_embed = concept_system.get_axiom_embedding('SELF', state_tensor)

# Compose concepts
composed, name = concept_system.compose('SELF', 'WITH', 'OTHER', state_tensor)

# Predict value
value = concept_system.predict_value(composed)

# Compute loss for training
loss = compute_concept_loss(concept_system, states, rewards, KEY_COMPOSITIONS)
```

### Using Language Bridge
```python
from reality_simulator.neural.concept_system import ConceptLanguageBridge

bridge = ConceptLanguageBridge(concept_system)

# Convert concept to phrase
phrase = bridge.concept_to_phrase('SELF_WITH_OTHER')  # → "self with other"

# Parse phrase to concept
concept = bridge.phrase_to_concept('self with other')  # → ('SELF', 'WITH', 'OTHER')

# Get explanation
explanation = bridge.explain_concept('DO_CAUSE_GOOD')

# Get vocabulary words grounded in current state
words = bridge.get_grounded_axiom_words(state_tensor, threshold=0.5)
```

### Trainer Concept System Methods
```python
# Save/load concept system state
trainer.save_concept_system('saves/concept_system.pt')
trainer.load_concept_system('saves/concept_system.pt')

# Get concept stats
stats = trainer.get_training_stats()
# Now includes: concept_system_enabled, average_concept_loss, 
#               concept_compositions_evaluated, top_useful_concepts
```

---

## Test Results

```
============================================================
RCUS INTEGRATION TEST SUITE
============================================================
✅ ConceptSystem: PASS
✅ OrganismBrain with ConceptHead: PASS
✅ NeuralTrainer with Concept Loss: PASS
✅ ConceptLanguageBridge: PASS
✅ Concept Loss Computation: PASS
✅ Full Training Loop: PASS

Result: 6/6 tests passed

🎉 ALL TESTS PASSED - RCUS Integration Complete!
```

Training metrics from full loop test:
- Initial loss: 1.58
- Final loss: 0.92
- Loss reduction: 41.9%

---

## Integration Points for Capsule System

If the capsule system needs to interact with RCUS:

1. **Get concept embeddings for capsule routing:**
   ```python
   axiom_embeds = concept_system.get_all_axiom_embeddings(state)
   ```

2. **Use concept values for attention:**
   ```python
   _, concept_out = brain(state, return_concept_outputs=True)
   axiom_weights = concept_out['axiom_relevance']  # (batch, 18)
   ```

3. **Ground capsules in axiom space:**
   - Each capsule could correspond to an axiom category
   - Existence capsules, Agency capsules, Value capsules, etc.

4. **Compose capsule outputs:**
   ```python
   composed = concept_system.operators['WITH'](capsule_a, capsule_b)
   ```

---

## Files to Review

1. `reality_simulator/neural/concept_system.py` - Full RCUS implementation
2. `reality_simulator/neural/brain.py` - ConceptHead integration
3. `reality_simulator/neural/trainer.py` - Triple-loss training
4. `config.json` - Configuration options

---

## Contact

For questions about the RCUS integration, the key classes are:
- `ConceptSystem` - Core axiom embeddings and composition
- `ConceptHead` - Brain output head
- `ConceptLanguageBridge` - Vocabulary connection
- `compute_concept_loss` - Training loss function
