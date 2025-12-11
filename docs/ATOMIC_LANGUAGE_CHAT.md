# Atomic Language Chat System

## Overview

The Atomic Language Chat system enables direct communication with individual organisms using their **personally learned vocabulary**. Each organism speaks only words it has acquired through experience, with full causation tracking.

## Key Concepts

### Atomic Language System
Each organism has an `atomic_language` attribute containing:
- **atoms**: Dictionary of `LinguisticAtom` objects - trackable linguistic units
- Each atom tracks:
  - `concept_id`: The word/concept
  - `strength`: Salience (0.0-1.0)
  - `source`: How acquired ('innate', 'observed', 'taught', 'discovered')
  - `semantic_frame`: Category ('action', 'state', 'quality', etc.)
  - `associations`: Links to other concepts
  - `usage_count`: How often used
  - Full causation event emission

### How It Works

1. **User sends message** via organism card chat button
2. **Endpoint** `/api/organism/<id>/chat` receives the message
3. **Vocabulary population**: 
   - `context_memory.vocabulary` starts with only 5 special tokens
   - We populate it from `organism.atomic_language.atoms`
   - Each word the organism has learned becomes available for generation
4. **Token generation**: 
   - `organism.generate_tokens()` uses the brain's `fc_language` layer
   - Generates tokens from the organism's personal vocabulary only
5. **Response**: Organism speaks using words it actually learned

## Architecture

```
User Message
    ↓
/api/organism/<id>/chat (causation_web_ui.py)
    ↓
Get organism.atomic_language.atoms → populate vocabulary
    ↓
ButterflyChatRouter.process_message_through_organism()
    ↓
organism.generate_tokens(context_memory, max_length, vp_value)
    ↓
Brain fc_language layer → token IDs → decode to words
    ↓
Response (only learned words)
```

## Required Systems

For chat to work, organism must have:

| System | Purpose |
|--------|---------|
| `organism.brain` | Neural network for generation |
| `organism.brain.fc_language` | Language output layer (50k capacity) |
| `organism.brain.use_language_head` | Must be `True` |
| `organism.atomic_language` | THE vocabulary source |
| `organism.atomic_language.atoms` | Dictionary of learned concepts |
| `organism.experience_buffer` | Stores chat as learning experience |
| `context_memory.vocabulary` | LanguageVocabulary for encoding/decoding |
| `context_memory.knowledge_web` | Semantic reference (optional) |

## Debug Panel

The chat debug panel shows:

| Field | Description |
|-------|-------------|
| `ctx_mem` | Context memory source (network/fallback/none) |
| `org_vocab` | Organism's learned word count |
| `lang_head` | Has language head (yes/no) |
| `exp_count` | Experience buffer size |
| `vp_value` | Violation pressure |
| `has_atomic_language` | Atomic language system present |
| `atomic_language_atom_count` | Number of learned concepts |
| `vocab_before_population` | Vocab size before adding atoms (5) |
| `vocab_after_population` | Vocab size after adding atoms |
| `vocab_source` | Where words came from ('atomic_language') |

## No Fallbacks Policy

The system has **no fallbacks**:
- If `atomic_language` is missing → error, no response
- Organisms must learn words to speak
- This ensures responses are genuine emergent language

## Example Response

```
User: hello
Organism: ignore fight start maintain contend deride perceive
Confidence: 58%
Reward: 0.82

[VOCAB_CHECK] vocab_size_attr:137.00 word_to_id_len:137.00
[DIRECT_CHAT] token_count:8.00 tokens:2,5,136,66,34,112,106,61
```

The organism generated 8 tokens from its 137-word vocabulary (5 special + 132 learned).

## Causation Tracking

Every word an organism learns is tracked:
- **Acquisition source**: How the word was learned
- **Formation time**: When it was acquired
- **Strength**: Salience/importance
- **Associations**: Links to other concepts
- **Events**: Emitted to causation system

This enables questions like:
- "Why did this organism develop the 'fight' concept?"
- "What caused 'danger' to associate with 'friend'?"
- "How did this community's dialect emerge?"

## Files Modified

- `causation_web_ui.py`: Chat endpoint populates vocab from atomic_language
- `butterfly_chat.py`: Diagnostic logging for vocab check
- `neural_organism.py`: Debug logging for token generation
- `templates/causation_explorer.html`: Debug panel displays 10 logs
- `config.json`: vocab_size set to 50000

## Date Implemented
December 11, 2025
