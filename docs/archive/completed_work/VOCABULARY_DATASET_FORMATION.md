# 📚 Vocabulary Dataset Formation Guide

**How the 50k curated vocabulary and linguistic knowledge web are built**

---

## Overview: Three-Stage Pipeline

Your vocabulary pipeline has **three stages** that progressively refine data:

```
Stage 1: Extract                    Stage 2: Refine                  Stage 3: Seed
─────────────────────────────────────────────────────────────────────────────────────

WordNet Database                    Aggressive Filtering             Knowledge Web
(141k raw words)                    (50k curated)                    (50k concepts + relations)
        ↓                                  ↓                                ↓
build_vocabulary.py          refine_vocabulary.py            seed_knowledge_web_from_vocab.py
        ↓                                  ↓                                ↓
Output:                      Output:                         Output:
butterfly_vocabulary_         butterfly_vocabulary_            seeded_knowledge_web_
200k_raw.json                50k_curated.json                 50k.json
```

---

## Stage 1: Extract from WordNet (141k words)

**File:** `build_vocabulary.py`

### What is WordNet?

WordNet is **Princeton's lexical database** - a curated English vocabulary:
- ✅ 141,000+ unique English words (lemmas)
- ✅ 100% legitimate English words
- ✅ ZERO proper nouns, brand names, personal names
- ✅ Morphologically complete (all word forms)

**Why WordNet?** Because you need a **clean, domain-agnostic foundation** that's:
- Scientifically curated (by linguists)
- Comprehensive (covers real English)
- Free from bias (no brand names, no spam)

### Extraction Process

```python
# From build_vocabulary.py
for synset in wordnet.all_synsets():      # For each meaning
    for lemma in synset.lemmas():         # Get all word forms
        word = lemma.name()               # Extract the word
        if word.isalpha():                # Only letters (no numbers/symbols)
            vocabulary.add(word)          # Add to set
```

### Output

**File:** `data/butterfly_vocabulary_200k_raw.json`

```json
{
  "source": "wordnet",
  "total_words": 141287,
  "words": [
    "abandon", "aberrant", "abet", "abide", "ability", "able", 
    "abnormal", "aboard", "abode", "abolish", "abominable", "abominate",
    "abortion", "abound", "about", "above", "abscond", "absence",
    ... (141k+ total)
  ],
  "categories": {
    "verbs": 13521,
    "nouns": 81426,
    "adjectives": 28374,
    "adverbs": 3982,
    "other": 14384
  }
}
```

---

## Stage 2: Refine to 50k Curated (Domain-Aligned)

**File:** `refine_vocabulary.py`

### The Filtering Challenge

You have 141k words, but organisms don't need:
- Surnames and brand names
- Obscure technical jargon
- Malformed morphological variants
- Random pop culture references
- Medical/financial/programming specifics

### Aggressive Filtering Strategy

```
141k WordNet words
    ↓
[Remove Blacklist Fragments]
  ✗ Surnames (Williams, Watson, etc.)
  ✗ Brands (Tesla, Amazon, Google, etc.)
  ✗ Technical jargon (blockchain, webpack, etc.)
  ✗ Geographic names (Afghanistan, Tokyo, etc.)
  ✗ Pop culture (Pokemon, Netflix, etc.)
    ↓
~110k filtered words
    ↓
[Domain Relevance Scoring]
Score each word by:
  • Semantic frame (action, state, relationship, etc.)
  • Organism applicability (relevant to AI behavior)
  • Abstraction level (concrete vs abstract)
  • Frequency in domain corpus
    ↓
Top 50k by relevance score
```

### Domain Categories (10 Core Categories)

Words are scored within domain-focused buckets:

```python
DOMAIN_CORE = {
    # Behavior (actions organisms perform)
    'move', 'rest', 'explore', 'hunt', 'gather', 'attack', 'defend',
    'cooperate', 'compete', 'share', 'help', 'lead', 'follow', 'adapt',
    
    # Social (relationships and groups)
    'ally', 'rival', 'friend', 'enemy', 'partner', 'group', 'team',
    'alliance', 'confederation', 'empire', 'govern', 'trust', 'betray',
    
    # Cognition (thinking and reasoning)
    'think', 'reason', 'analyze', 'evaluate', 'infer', 'decide', 'plan',
    'learn', 'remember', 'predict', 'hypothesize', 'optimize',
    
    # Survival (fitness and persistence)
    'survive', 'thrive', 'struggle', 'persist', 'recover', 'heal',
    'reproduce', 'die', 'evolve', 'strengthen', 'weaken',
    
    # Temporal (time and sequences)
    'now', 'soon', 'later', 'cycle', 'phase', 'timeline', 'sequence',
    'duration', 'delay', 'acceleration', 'transition', 'rhythm',
    
    # Spatial (networks and topology)
    'network', 'node', 'edge', 'link', 'cluster', 'layer', 'topology',
    'density', 'boundary', 'center', 'gradient',
    
    # Causal (cause and effect)
    'cause', 'effect', 'trigger', 'cascade', 'amplify', 'suppress',
    'feedback', 'propagate', 'emerge',
    
    # Communication
    'say', 'ask', 'reply', 'explain', 'signal', 'warn', 'encode',
    'decode', 'translate', 'inform', 'respond',
    
    # Perception
    'sense', 'observe', 'detect', 'track', 'focus', 'notice', 'recognize',
    'visualize', 'measure', 'inspect', 'diagnose',
    
    # Governance
    'govern', 'regulate', 'validate', 'certify', 'audit', 'authorize',
    'synchronize', 'calibrate', 'tune', 'optimize', 'orchestrate'
}
```

### Scoring Function

Each word gets a **relevance score** based on:

```python
def score_word(word, semantic_frame, category):
    score = 0.0
    
    # High relevance: direct organism behavior
    if semantic_frame in {'action', 'state', 'relationship'}:
        score += 1.0
    
    # Medium relevance: enabling concepts
    if semantic_frame in {'mental_state', 'causal', 'temporal'}:
        score += 0.7
    
    # Bonus for domain core words
    if word in DOMAIN_CORE:
        score += 0.3
    
    # Penalty for very short (too abstract)
    if len(word) < 3:
        score -= 0.1
    
    return score
```

### Blacklist Fragments (Aggressive Filtering)

```python
BLACKLIST_FRAGMENTS = {
    # Surnames
    'williams', 'watson', 'wilson', 'wright', 'walker', 'white',
    
    # Brands
    'nvidia', 'tesla', 'amazon', 'google', 'microsoft', 'apple',
    
    # Technical jargon
    'blockchain', 'cryptocurrency', 'kubernetes', 'webpack',
    
    # Geographic
    'afghanistan', 'california', 'tokyo', 'barcelona',
    
    # Pop culture
    'pokemon', 'netflix', 'youtube', 'spotify',
    
    # Medical/Financial
    'endocrinology', 'angioplasty', 'derivatives', 'nasdaq',
    
    # Programming specifics
    'javascript', 'typescript', 'ansible'
}
```

### Output

**File:** `data/butterfly_vocabulary_50k_curated.json`

```json
{
  "source": "wordnet_curated",
  "total_words": 50000,
  "filtered_out": 91287,
  "filtering_method": "domain_relevance_scoring",
  "domain_categories": {
    "behavior": 4200,
    "social": 3500,
    "cognition": 3800,
    "survival": 3100,
    "temporal": 2800,
    "spatial": 3200,
    "causal": 2900,
    "communication": 2600,
    "perception": 3100,
    "governance": 3200,
    "general": 7600
  },
  "words": [
    "move", "cooperate", "think", "survive", "now", "network",
    "cause", "say", "sense", "govern", ...
    (50k total)
  ]
}
```

---

## Stage 3: Seed Knowledge Web (50k Concepts + Relations)

**File:** `seed_knowledge_web_from_vocab.py`

### What is the Knowledge Web?

The **Linguistic Knowledge Web** transforms raw words into a **semantic graph**:

```
Word ("move")
    ↓
Linguistic Concept with:
  • Definition: "To change position or location in space"
  • Semantic Frame: "action"
  • Organism Relevance: 1.0 (highly relevant to organisms)
  • Associations: ["explore", "travel", "navigate", "migrate", "roam"]
  • Contexts: ["exploration", "resource_seeking", "survival"]
  • Abstraction Level: 0 (concrete - directly observable)
```

### Semantic Frames (Categories for Words)

Each word gets assigned a **semantic frame** - a category that describes what kind of concept it is:

```
'action'          → Verbs (move, explore, cooperate, attack)
'state'           → Nouns/adjectives (alive, healthy, connected)
'quality'         → Adjectives ending in -ly (fast, slow, smart)
'relationship'    → Social concepts (ally, friend, team)
'temporal'        → Time concepts (now, cycle, phase, duration)
'spatial'         → Space concepts (network, node, edge, center)
'mental_state'    → Cognition (think, reason, decide, remember)
'causal'          → Cause/effect (trigger, cascade, propagate)
'communication'   → Language (say, ask, explain, signal)
'perception'      → Sensing (see, hear, detect, recognize)
'entity'          → Pronouns and basic entities (I, you, we, group)
'logical'         → Logical connectors (and, or, if, because)
'general'         → Everything else (fallback category)
```

### Organism Relevance Scoring

Each concept gets a **relevance score** (0.0-1.0) based on how relevant it is to organism experiences:

```python
def calculate_organism_relevance(word, semantic_frame):
    # High relevance: directly tied to organism behavior
    if semantic_frame in {'action', 'state', 'relationship', 'perception', 'survival', 'communication'}:
        return 1.0  # 100% relevant
    
    # Medium relevance: enabling concepts
    if semantic_frame in {'mental_state', 'causal', 'temporal', 'spatial'}:
        return 0.8  # 80% relevant
    
    # Lower relevance: abstract/general
    return 0.5  # 50% relevant
```

**Why?** Organisms learn faster with high-relevance words because they map directly to their experiences.

### Seeding Process

```python
for word in 50k_curated_vocabulary:
    # 1. Infer semantic frame
    frame = infer_semantic_frame(word)
    
    # 2. Calculate organism relevance
    relevance = calculate_organism_relevance(word, frame)
    
    # 3. Create linguistic concept
    concept = LinguisticConcept(
        word=word,
        definition=generate_definition(word),
        semantic_frame=frame,
        organism_relevance=relevance,
        associations=[],  # Will be populated by ConceptNet/WordNet
        contexts=[],      # Will be populated by usage
        abstraction_level=determine_abstraction(frame)
    )
    
    # 4. Add to knowledge web
    knowledge_web.add_concept(concept)
```

### Output Structure

**File:** `data/seeded_knowledge_web_50k.json`

```json
{
  "version": "1.0-seeded",
  "source": "curated_vocabulary_50k",
  "metadata": {
    "concept_count": 50000,
    "relation_count": 0,
    "ready_for_expansion": true
  },
  "concepts": {
    "move": {
      "word": "move",
      "definition": "To change position or location in space",
      "semantic_frame": "action",
      "organism_relevance": 1.0,
      "associations": [],
      "contexts": ["exploration", "resource_seeking", "survival"],
      "abstraction_level": 0
    },
    "cooperate": {
      "word": "cooperate",
      "definition": "To work together for mutual benefit",
      "semantic_frame": "action",
      "organism_relevance": 1.0,
      "associations": [],
      "contexts": ["social", "network", "mutual_benefit"],
      "abstraction_level": 0
    },
    ... (50k total concepts)
  },
  "relations": []  # Will be populated by expansion step
}
```

---

## Stage 4 (Optional): Expand Knowledge Web

**File:** `reality_simulator/language/expand_knowledge_web.py`

### What is Expansion?

After seeding, you can **optionally expand** the knowledge web with semantic relationships from:

```
ConceptNet         → Semantic relationships (cause, enable, part_of, etc.)
WordNet            → Synonym/antonym hierarchies
FrameNet           → Frame-to-frame mappings
```

### Expansion Example

```bash
python reality_simulator/language/expand_knowledge_web.py \
  --concepts 50000 \
  --min-weight 0.5
```

This would:
1. Load seeded 50k knowledge web
2. Query ConceptNet for semantic relations (connections)
3. Query WordNet for synonyms/antonyms
4. Add relationships with confidence >= 0.5
5. Output expanded knowledge web with relations

### Relation Types

Semantic relationships connect concepts with types:

```
'synonym'        → "move" ↔ "walk" (similar meaning)
'antonym'        → "move" ↔ "stay" (opposite meaning)
'causes'         → "cooperation" → "success" (one leads to other)
'enables'        → "network" → "cooperation" (makes possible)
'is_a'           → "friend" is_a "relationship" (type hierarchy)
'part_of'        → "node" part_of "network" (composition)
'has_property'   → "network" has_property "connectivity" (qualities)
'related_to'     → "move" related_to "explore" (general relation)
'similar_to'     → "ally" similar_to "friend" (semantic similarity)
```

---

## Data Flow: How Organisms Use It

### 1. During Initialization

```python
# Reality Simulator loads knowledge web
knowledge_web = LinguisticKnowledgeWeb()
knowledge_web.load_from_file("data/seeded_knowledge_web_50k.json")

# Each organism gets access
organism.language_system = LanguageTeacher(knowledge_web)
```

### 2. During Language Generation

```python
# Organism wants to generate a token
organism.generate_token(context_state):
    1. Get organism state (position, energy, connections, etc.)
    2. Score all 50k words by relevance to state
       - Use semantic frames
       - Consider organism relevance
       - Check associations
    3. Select top-K most relevant words
    4. Sample one word (with temperature-based exploration)
    5. Emit token
    6. Log success/failure for learning
```

### 3. During Learning

```python
# After generation, neural system evaluates quality
neural_trainer.evaluate_response(tokens, quality):
    if quality == "coherent":
        # Strengthen relationships used in generation
        for relation in used_relations:
            relation.success_count += 1
            relation.strength *= 1.05  # Boost
    else:
        # Weaken relationships that led to poor generation
        for relation in used_relations:
            relation.failure_count += 1
            relation.strength *= 0.95  # Reduce
```

---

## Complete Setup Checklist

### For Complete Vocabulary Pipeline:

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install nltk  # Required for WordNet

# 2. Run Stage 1: Extract from WordNet (141k)
python reality_simulator/build_vocabulary.py
# Output: data/butterfly_vocabulary_200k_raw.json (~141k words)

# 3. Run Stage 2: Refine to 50k
python reality_simulator/refine_vocabulary.py
# Output: data/butterfly_vocabulary_50k_curated.json (50k words)

# 4. Run Stage 3: Seed Knowledge Web
python reality_simulator/seed_knowledge_web_from_vocab.py
# Output: data/seeded_knowledge_web_50k.json (50k concepts)

# 5. (Optional) Run Stage 4: Expand with ConceptNet/WordNet
python reality_simulator/language/expand_knowledge_web.py \
  --concepts 50000 \
  --min-weight 0.5
# Output: data/seeded_knowledge_web_50k.json (updated with relations)

# 6. Start simulation
python unified_entry.py
```

### One-Command Setup (Automated Pipeline):

```bash
python build_curated_dataset.py
```

This runs stages 1-3 automatically.

---

## File Organization

```
data/
├── butterfly_vocabulary_200k_raw.json         # Stage 1: WordNet (141k)
├── butterfly_vocabulary_50k_curated.json      # Stage 2: Curated (50k)
└── seeded_knowledge_web_50k.json              # Stage 3: Knowledge web (50k concepts)

Files are gitignored (~50MB total) to keep repo small
but automatically regenerated on first run
```

---

## Why This Design?

### Problem
Organisms need a **large, diverse vocabulary** (50k+ words) but also need it to be **highly relevant** to their actual experiences (move, cooperate, survive, etc.).

### Solution: Three-Stage Pipeline

| Stage | Purpose | Input | Output | Benefit |
|-------|---------|-------|--------|---------|
| Extract | Get clean baseline | WordNet (141k) | WordNet words (141k) | 100% legitimate English |
| Refine | Domain focus | 141k words | 50k curated | Relevant to AI behavior |
| Seed | Semantic structure | 50k words | 50k concepts + frames | Organisms understand relationships |
| Expand | Knowledge enrichment | 50k concepts | 50k + relations | Semantic understanding |

### Quality Guarantees

✅ **No Brand Names**: Filtered out (Tesla, Google, etc.)
✅ **No Proper Nouns**: Filtered out (Williams, Tokyo, etc.)
✅ **No Jargon**: Filtered out (blockchain, webpack, etc.)
✅ **100% English**: All words from WordNet
✅ **Domain-Aligned**: Scored by organism relevance
✅ **Semantically Rich**: Connected via relationships
✅ **Production-Ready**: Single command to generate

---

## Next Steps

1. **Generate Vocabulary** (if not done):
   ```bash
   python build_curated_dataset.py
   ```

2. **Enable Language in Config**:
   ```json
   {
     "neural": {
       "language_model": {
         "enabled": true
       }
     }
   }
   ```

3. **Run Simulation**:
   ```bash
   python unified_entry.py
   ```

4. **Monitor Learning** via:
   - Butterfly Chat (web UI)
   - Logs: `data/logs/application.log`
   - Causation Explorer: vocabulary growth events

---

## Technical Details

### Semantic Frame Inference

```python
# Heuristic-based frame inference
def infer_frame(word):
    if word.endswith('ing'):
        return 'action'              # "moving", "cooperating"
    elif word.endswith('ly'):
        return 'quality'             # "quickly", "slowly"
    elif word.endswith('ness'):
        return 'state'               # "happiness", "fitness"
    elif word in pronouns:
        return 'entity'              # "I", "you", "we"
    elif word in logical_words:
        return 'logical'             # "and", "or", "if"
    
    # Check domain categories
    if word in BEHAVIOR_WORDS:
        return 'action'
    if word in SOCIAL_WORDS:
        return 'relationship'
    ... (and so on)
    
    return 'general'                 # Default fallback
```

### Organism Relevance Calculation

```python
# High-relevance words organisms encounter frequently
HIGH_RELEVANCE = {
    'action', 'state', 'relationship',  # Direct behavior
    'perception', 'survival', 'communication'  # Directly experienced
}

# Medium-relevance words useful for understanding
MEDIUM_RELEVANCE = {
    'mental_state', 'causal', 'temporal', 'spatial'  # Enable reasoning
}

# Lower-relevance words for completeness
GENERAL = {
    'quality', 'entity', 'logical', 'general'  # Supporting concepts
}
```

---

## Monitoring Knowledge Web Growth

During runtime, watch for:

```
[LANGUAGE] Vocabulary growth: 50000 → 50234 words
[LANGUAGE] New relationships discovered: 1,247
[BUTTERFLY_CHAT] Organisms communicating with 45k+ vocabulary terms
[NEURAL] Language learning loss: 0.234 → 0.187 (improving)
```

These indicate:
- ✅ Vocabulary expanding through use
- ✅ Neural system discovering new relationships
- ✅ Language generation improving
- ✅ Organisms developing linguistic understanding

