# 🦋 Swarm Recon Messages for System Diagnostics

These messages are designed to probe specific subsystems when sent through Butterfly Chat (`/api/butterfly/chat`).
The organism responses (or lack thereof) will reveal the health of each subsystem.

---

## Recon Message 1: Token Generation & Vocabulary Health

**Purpose:** Diagnose empty token decoding, vocabulary size, and word availability.

```
🔬 VOCAB PROBE: What words do you know? Tell me about move, rest, eat, cooperate. How many words exist in your vocabulary? Can you count from one to five using only words you've learned?
```

**What to observe:**
- Empty response = vocabulary empty or token generation broken
- Gibberish/UNK = tokens generated but out of vocabulary range
- Coherent words = vocabulary properly populated
- Check console for: `vocab_size`, `token_count`, `decode` results

**Expected healthy output:** Should return at least some action-related words (move, rest, eat, cooperate, attack, danger, safe, food, energy)

---

## Recon Message 2: Experience Buffer & Learning Status

**Purpose:** Diagnose if experiences are being stored and if organisms are learning from chat.

```
🧠 LEARNING PROBE: Have you learned anything from our conversations? What was the last thing you remembered? How many experiences do you have stored? Tell me something you learned recently.
```

**What to observe:**
- Check `experience_count` in debug logs
- Check if `token_sequence` is being stored
- Watch for `bootstrap_learning` triggers
- Console should show: `experience_buffer.add()` calls with `token_sequence`

**Expected healthy output:** Organisms should reference recent interactions. Debug logs should show `experience_count > 0` after a few messages.

---

## Recon Message 3: Knowledge Web & Semantic Relationships

**Purpose:** Diagnose if organisms can access the Knowledge Web for semantic guidance.

```
🌐 SEMANTIC PROBE: What is the opposite of danger? What causes hunger? What enables cooperation? Tell me words that are similar to "strong" or "move".
```

**What to observe:**
- Empty response = knowledge_web not accessible from context_memory
- Correct antonyms/synonyms = semantic guidance working
- Check console for: `knowledge_web` access, `get_similar_words()` calls
- Watch for: `context_memory.knowledge_web` or `context_memory.language_teacher.knowledge_web`

**Expected healthy output:** Should return semantic relationships (danger↔safe, hunger→eat, cooperate→friend, strong→weak)

---

## Recon Message 4: Neural Language Head & Training Pipeline

**Purpose:** Diagnose if the language head is enabled and receiving training signals.

```
🔥 NEURAL PROBE: Generate a sequence of thoughts. What action would you take if you were hungry and saw food nearby? Describe your decision process step by step.
```

**What to observe:**
- Check if `fc_language` exists on brain (language head enabled)
- Check if `use_language_head=True` in brain config
- Watch for: logits shape, temperature sampling, token clamping
- Console should show: `language_loss` values during training

**Expected healthy output:** Multi-word coherent response showing logical reasoning. Debug logs should show `generate_tokens()` using actual language head, not fallback pseudo-tokens.

---

## How to Use These Messages

### Via Web UI (Butterfly Chat Panel):
1. Open the Causation Explorer web UI
2. Find the 🦋 Butterfly Chat panel (right sidebar)
3. Paste each recon message and click Send
4. Observe both the response AND the browser console (F12)

### Via API (curl/Postman):
```bash
curl -X POST http://localhost:5000/api/butterfly/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "🔬 VOCAB PROBE: What words do you know?", "routing_strategy": "all", "max_organisms": 10}'
```

### Via Python:
```python
import requests
response = requests.post('http://localhost:5000/api/butterfly/chat', json={
    'message': '🔬 VOCAB PROBE: What words do you know?',
    'routing_strategy': 'all',
    'max_organisms': 10
})
print(response.json())
```

---

## Interpreting Results

| Symptom | Likely Issue | Fix Location |
|---------|--------------|--------------|
| All probes return empty | Vocabulary not initialized | `context_memory.py` - add seed vocabulary |
| Probe 1 empty, others work | Token generation broken | `neural_organism.py` - check `generate_tokens()` |
| Probe 2 shows 0 experiences | Token sequences not stored | `butterfly_chat.py` - check `.add()` calls |
| Probe 3 shows no relationships | Knowledge web not attached | `symbiotic_network.py` - attach to context_memory |
| Probe 4 shows pseudo-tokens | Language head disabled | `utils.py` - enable `use_language_head=True` |

---

## Debug Log Keys to Watch

When running these probes, look for these keys in the response `debug_logs`:

```json
{
  "vocab_size": 33,           // Should be > 5 (special tokens only = broken)
  "experience_count": 0,      // Should grow over time
  "token_count": 5,           // Tokens generated per response
  "has_language_head": true,  // Should be true
  "knowledge_web_used": true, // Should be true for semantic guidance
  "bootstrap_triggered": true // True if empty response triggered learning
}
```

---

## Quick Health Check Script

Run this after sending all 4 probes:

```javascript
// In browser console after Butterfly Chat responses
const lastResponses = window._butterflyDebugResponses || [];
console.log('=== SWARM HEALTH CHECK ===');
console.log('Total probes:', lastResponses.length);
console.log('Empty responses:', lastResponses.filter(r => !r.response || r.response === '<no response>').length);
console.log('Avg confidence:', lastResponses.reduce((a,b) => a + (b.confidence || 0), 0) / lastResponses.length);
console.log('Organisms responding:', new Set(lastResponses.flatMap(r => r.organism_responses?.map(o => o.organism_id) || [])).size);
```
