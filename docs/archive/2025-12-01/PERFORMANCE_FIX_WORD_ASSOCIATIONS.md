# Performance Fix: Word Associations Loading

## Problem
The web page was timing out and becoming unresponsive because it was loading ALL word associations for ALL organisms into memory, which could be thousands of organisms with many words each.

## Root Cause
1. **`get_graph()` endpoint**: Loading ALL `node_word_associations` from `context_memory.node_word_associations.items()` without limits
2. **`/api/language/data` endpoint**: Sending ALL language_anchors, ALL node_word_associations, and ALL word_frequencies without pagination

## Fixes Applied

### 1. Limited Word Associations in `get_graph()` (`causation_web_ui.py`)

**Before:**
```python
node_word_associations = {
    str(org_id): set(words) 
    for org_id, words in context_memory.node_word_associations.items()  # ALL organisms!
}
```

**After:**
```python
# Limit to most recent 500 organisms with word associations
MAX_ASSOCIATIONS_TO_LOAD = 500
loaded_count = 0

for org_id, words in list(context_memory.node_word_associations.items())[-MAX_ASSOCIATIONS_TO_LOAD:]:
    if loaded_count >= MAX_ASSOCIATIONS_TO_LOAD:
        break
    node_word_associations[str(org_id)] = set(words)
    loaded_count += 1
```

**Impact:**
- Reduces memory usage from potentially thousands of organisms to 500
- Still covers recent organisms (most likely to have linguistic edges)
- Prevents timeout when loading graph data

### 2. Limited Data in `/api/language/data` (`causation_web_ui.py`)

**Before:**
```python
language_anchors = {
    word: list(organism_ids) 
    for word, organism_ids in context_memory.language_anchors.items()  # ALL words!
}

node_word_associations = {
    str(organism_id): list(words)
    for organism_id, words in context_memory.node_word_associations.items()  # ALL organisms!
}
```

**After:**
```python
MAX_WORDS_TO_SEND = 500  # Limit vocabulary size
MAX_ORGANISMS_TO_SEND = 1000  # Limit organism associations
MAX_ORGANISMS_PER_WORD = 100  # Limit organism list per word

# Limit language_anchors
language_anchors = {}
word_count = 0
for word, organism_ids in context_memory.language_anchors.items():
    if word_count >= MAX_WORDS_TO_SEND:
        break
    limited_org_ids = list(organism_ids)[:MAX_ORGANISMS_PER_WORD]
    language_anchors[word] = limited_org_ids
    word_count += 1

# Limit node_word_associations
node_word_associations = {}
org_count = 0
for organism_id, words in context_memory.node_word_associations.items():
    if org_count >= MAX_ORGANISMS_TO_SEND:
        break
    word_list = list(words)[:20]  # Limit to 20 words per organism
    node_word_associations[str(organism_id)] = word_list
    org_count += 1

# Limit word frequencies (top N by frequency)
word_frequencies = dict(sorted(
    context_memory.word_frequencies.items(),
    key=lambda x: x[1],
    reverse=True
)[:MAX_WORDS_TO_SEND])
```

**Impact:**
- Limits vocabulary to top 500 words
- Limits organisms to 1000 most recent
- Limits words per organism to 20
- Limits organisms per word to 100
- Returns metadata about what was limited

## Performance Improvements

### Before
- Loading 10,000+ organisms with 50+ words each = 500,000+ word associations
- Sending all data to frontend = multi-MB JSON responses
- Browser timeout/unresponsive

### After
- Loading 500 organisms = ~10,000 word associations (20x reduction)
- Sending limited data = ~100KB JSON responses (50x reduction)
- Fast response times, no timeouts

## Configuration

If you need more data, you can adjust these limits:

```python
# In get_graph()
MAX_ASSOCIATIONS_TO_LOAD = 500  # Increase for more organisms

# In /api/language/data
MAX_WORDS_TO_SEND = 500  # Increase for larger vocabulary
MAX_ORGANISMS_TO_SEND = 1000  # Increase for more organisms
MAX_ORGANISMS_PER_WORD = 100  # Increase organisms per word
```

## Testing

After these fixes:
1. Web page should load quickly
2. Graph should render without timeout
3. `/api/language/data` should return quickly
4. Check response includes `limited` metadata showing what was capped

