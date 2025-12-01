# Knowledge Web with Quality Control - Wiring Verification

## ✅ Complete System Wiring Check

### 1. Configuration Flow ✅

**Path:** `config.json` → `LinguisticKnowledgeWeb.__init__()` → `LanguageTeacher.__init__()`

**Config Location:**
```json
{
  "neural": {
    "language_model": {
      "knowledge_web": {
        "quality_control": {
          "enabled": true,
          "min_discovery_count": 3,
          "min_confidence_threshold": 0.3,
          "confidence_growth_rate": 0.0005,
          "exploration_start": 0.2,
          "exploration_end": 0.05,
          "exploration_decay_generations": 1000,
          "validation_required": true,
          "max_discoveries_per_generation": 10,
          "vp_boost_exploration": true,
          "vp_boost_threshold": 0.7,
          "review_frequency": 100,
          "pruning_confidence_threshold": 0.2,
          "pruning_unused_generations": 100,
          "pruning_failure_rate": 0.7
        }
      }
    }
  }
}
```

**Initialization:**
- ✅ `LinguisticKnowledgeWeb.__init__()` reads `quality_control` from config
- ✅ All 14 quality control parameters are loaded
- ✅ Defaults are provided if config values missing

### 2. Knowledge Base Import ✅

**Path:** `LanguageTeacher.__init__()` → `KnowledgeBaseImporter.import_all()`

**Flow:**
1. `LanguageTeacher.__init__()` creates `LinguisticKnowledgeWeb(config)`
2. Imports `KnowledgeBaseImporter` from `.import_knowledge_base`
3. Calls `importer.import_all(self.knowledge_web, grammar_learner=None)`
4. Loads:
   - `data/linguistic_concepts.json` (326 concepts)
   - `data/semantic_relations.json` (1,395 relations)
   - `data/ngram_patterns.json` (106 patterns)

**Seeded Relationships:**
- ✅ Relations from `semantic_relations.json` are marked `is_seeded=True`
- ✅ Seeded relations have `confidence=0.9`
- ✅ Seeded relations have `generation_discovered=0`
- ✅ Seeded relations are **protected from pruning** (never deleted)

**Code Location:**
- `import_knowledge_base.py:load_relations()` - Marks relations as seeded
- `linguistic_knowledge_web.py:_add_relation()` - Handles seeded flag

### 3. Runtime Flow ✅

**Path:** `SymbioticNetwork.update()` → `LanguageTeacher.teach_network()` → `LinguisticKnowledgeWeb.update_generation()`

**Generation Updates:**
- ✅ `teach_network()` calls `self.knowledge_web.update_generation(generation)` every generation
- ✅ `update_generation()` adjusts:
  - `exploration_rate` (decays from 0.2 → 0.05 over 1000 generations)
  - `confidence_threshold` (grows from 0.3 → 0.8 over 2000 generations)

**Discovery Flow:**
- ✅ `teach_organism()` calls `discover_relationship()` with:
  - `generation` (current generation)
  - `vp_value` (from network_state)
  - Context data (organism_id, organism_state, etc.)
- ✅ `discover_relationship()`:
  - Checks `exploration_rate` (VP-boosted if VP > threshold)
  - Checks `max_discoveries_per_generation` cap
  - Calls `validate_relationship()` before adding
  - Initializes discovered relations with `confidence=0.5`, `is_seeded=False`

**Validation:**
- ✅ `validate_relationship()` checks:
  - `min_discovery_count` (must see pattern N times)
  - `_check_semantic_coherence()` (semantic frame compatibility)
  - `_check_context_coherence()` (context co-occurrence)
- ✅ Only validated relationships are added

### 4. Quality Review & Decay ✅

**Quality Review (Every N Generations):**
- ✅ `_perform_quality_review()` called every `review_frequency` generations (default: 100)
- ✅ Iterates through discovered relationships
- ✅ Strengthens high-quality ones (`record_relationship_success()`)
- ✅ Weakens low-quality ones (`record_relationship_failure()`)
- ✅ Prunes very weak ones

**Decay & Pruning (Every N Generations):**
- ✅ `decay_relationships()` called every `decay_frequency` generations (default: 50)
- ✅ Never prunes `is_seeded=True` relationships
- ✅ Prunes discovered relationships if:
  - `confidence < pruning_confidence_threshold` (default: 0.2)
  - Unused for `pruning_unused_generations` (default: 100)
  - `failure_rate > pruning_failure_rate` (default: 0.7)
- ✅ Gradually decays `strength` and `confidence` for unused relationships

### 5. Event Emission ✅

**Language Events:**
- ✅ `vocabulary_growth` - Emitted when words added
- ✅ `organism_communication` - Emitted when organisms communicate
- ✅ `word_assignment` - Emitted when words linked to organisms
- ✅ `butterfly_chat_message` - Emitted when user sends message
- ✅ `butterfly_chat_response` - Emitted when organism responds

**Causation Links:**
- ✅ Language → Language (vocabulary_growth → organism_communication)
- ✅ Language → Neural (vocabulary_growth → neural_language_training)
- ✅ Butterfly Chat → Language (butterfly_chat_message → organism_communication)
- ✅ Language → Reality Sim (organism_communication → network state changes)

### 6. Butterfly Chat Integration ✅

**Path:** Web UI → `ButterflyChatRouter` → Organisms → Knowledge Web

**Flow:**
1. User sends message via `/api/butterfly/chat`
2. `ButterflyChatRouter.route_message()` tokenizes message
3. Organisms generate responses using `knowledge_web.get_situational_awareness()`
4. Responses use quality-controlled vocabulary
5. Events emitted for causation tracking

**Knowledge Web Usage:**
- ✅ `get_situational_awareness()` uses 14-dimensional assessment
- ✅ Uses validated relationships (quality-controlled)
- ✅ Respects `exploration_rate` for diversity
- ✅ Uses `confidence_threshold` for word selection

### 7. CRA Integration ✅

**Quality Control Parameters:**
- ✅ All 14 parameters in `CONFIG_GUARDRAILS` in `causation_web_ui.py`
- ✅ CRA can tune all quality control settings
- ✅ CRA system prompt includes quality control documentation
- ✅ Example `CONFIG_UPDATE` commands provided

**Illumination Engine:**
- ✅ Language component in dropdown (`language`, `butterfly_chat`)
- ✅ Language event types searchable (`vocabulary_growth`, `organism_communication`, etc.)
- ✅ Causation links visible when filtering by language components

## 🔍 Verification Checklist

### Initialization ✅
- [x] Config loaded correctly
- [x] Quality control parameters initialized
- [x] Knowledge base imported
- [x] Seeded relationships marked correctly
- [x] Exploration/confidence rates set to start values

### Runtime ✅
- [x] `update_generation()` called every generation
- [x] Exploration rate decays over time
- [x] Confidence threshold grows over time
- [x] Discovery respects caps and cooldowns
- [x] Validation gates work correctly
- [x] VP-aware exploration boosting works

### Quality Control ✅
- [x] Quality review runs periodically
- [x] Relationship strengthening/weakening works
- [x] Decay runs periodically
- [x] Pruning respects seeded protection
- [x] Low-quality relationships removed

### Integration ✅
- [x] Events emitted correctly
- [x] Causation links created
- [x] Butterfly Chat uses knowledge web
- [x] CRA can control parameters
- [x] Illumination Engine filters work

## 🎯 System Status: **FULLY WIRED** ✅

All components are properly connected:
1. ✅ Config → Initialization
2. ✅ Knowledge Base → Seeded Relationships
3. ✅ Runtime → Generation Updates
4. ✅ Discovery → Validation → Quality Control
5. ✅ Events → Causation Links
6. ✅ Butterfly Chat → Knowledge Web
7. ✅ CRA → Quality Control Tuning

The recursive expansion system with quality control is **fully operational**.

