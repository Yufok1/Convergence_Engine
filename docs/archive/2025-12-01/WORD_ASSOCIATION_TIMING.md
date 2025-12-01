# Word Association Timing Guide

## When Word Association Happens

Word association occurs **every generation** during `SymbioticNetwork.update_network()` (called from the main simulation loop).

### Process Flow

```
Every Generation:
  ↓
SymbioticNetwork.update_network()
  ↓
language_teacher.teach_network(organisms, context_memory, generation)
  ↓
For each organism:
  ↓
1. Get organism state (18-feature vector or fallback)
2. Get current/recent action
3. Get network_state and breath_state from context_memory
4. Call knowledge_web.get_situational_awareness() → returns words
5. Link words to organism via context_memory.link_word_to_node()
```

### Configuration

**Required:**
- `neural.language_model.enabled: true` ✅ (already set)

**Optional (with defaults):**
- `neural.language_model.teaching_frequency: 1` (teach every generation)
- `neural.language_model.min_action_history: 3` (organisms need 3+ actions)

**New Teacher Config (add to config.json):**
```json
"neural": {
  "language_model": {
    "enabled": true,
    "teaching_frequency": 1,
    "min_action_history": 3,
    "teacher": {
      "use_knowledge_web": true,
      "use_semantic_embeddings": true,
      "vocab_size": 1000,
      "embedding_dim": 64,
      "min_experiences": 100,
      "training_frequency": 10,
      "min_confidence": 0.3
    }
  }
}
```

### Why Words Might Not Be Associated

1. **Organisms don't have enough action history yet**
   - Need at least `min_action_history` (default: 3) actions
   - Check: Are organisms taking actions?

2. **Teaching frequency is skipping generations**
   - Default is 1 (every generation), but check config

3. **State vector issues**
   - Fixed: Now properly converts to numpy array if `get_state_features()` fails

4. **Knowledge web not initialized**
   - Should raise ImportError if unavailable
   - Check logs for: `[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled`

5. **Silent errors**
   - Errors are caught in `update_network()` (line 1336-1338)
   - Check logs for: `[SYMBIOTIC_NETWORK] Language teaching error`

### Debugging

Add logging to see what's happening:

```python
# In language_teacher.py, teach_network():
logger.info(f"[LANGUAGE_TEACHER] Gen {generation}: Starting teaching...")
logger.info(f"[LANGUAGE_TEACHER] Organisms: {len(organisms)}, Enabled: {self.enabled}")
logger.info(f"[LANGUAGE_TEACHER] Knowledge web: {self.knowledge_web is not None}")
```

### Expected Log Output

When working correctly, you should see:
```
[LANGUAGE_TEACHER] Initialized (enabled=True, knowledge_web=True, ...)
[LANGUAGE_TEACHER] Gen 10: Taught 45/90 organisms, 234 words assigned
```

If you see `[Context Memory] No anchors yet`, it means:
- Either teaching hasn't run yet (early generations)
- Or teaching is being skipped (check teaching_frequency)
- Or organisms don't meet min_action_history requirement

