# ⚙️ Configuration Exposure Summary

**New Systems Configuration Exposure for CRA Control**

**Status**: ✅ **IMPLEMENTED**  
**Date**: 2025-01-XX

---

## 🎯 Overview

All new systems now have their configuration settings:
1. ✅ **Exposed in config.json** - Settings are accessible and editable
2. ✅ **Documented for CRA** - CRA knows about all settings and can tune them
3. ✅ **Configurable via CONFIG_UPDATE** - CRA can adjust settings in real-time

---

## 📋 New Configuration Sections

### 1. **Neural Relationship Learning** (`/neural/language_model/relationship_learning`)

**Purpose**: Neural system learns from generation quality to strengthen/weaken semantic relationships

#### Quality Evaluation Thresholds

| Path | Range | Default | Description |
|------|-------|---------|-------------|
| `enabled` | true/false | true | Enable/disable relationship learning |
| `quality_evaluation/coherent_threshold` | 0.0-1.0 | 0.5 | Minimum coherence score for success (>50% semantic pairs) |
| `quality_evaluation/garbled_threshold` | 0.0-1.0 | 0.2 | Maximum coherence score for failure (<20% semantic pairs) |
| `quality_evaluation/unk_ratio_threshold` | 0.0-1.0 | 0.3 | Maximum UNK token ratio (>30% = garbled) |
| `quality_evaluation/min_word_count` | 1-10 | 2 | Minimum words for evaluation |
| `quality_evaluation/min_word_count_for_evaluation` | 2-10 | 3 | Minimum words for full evaluation |
| `quality_evaluation/max_word_count` | 10-50 | 20 | Maximum words (beyond = rambling) |
| `quality_evaluation/relationship_strength_threshold` | 0.0-1.0 | 0.5 | Minimum relationship strength for coherence check |

#### Semantic Guidance Parameters

| Path | Range | Default | Description |
|------|-------|---------|-------------|
| `semantic_guidance/enabled` | true/false | true | Enable semantic word boosting during generation |
| `semantic_guidance/min_strength_threshold` | 0.0-1.0 | 0.7 | Minimum relationship strength for semantic guidance |
| `semantic_guidance/semantic_boost` | 0.0-1.0 | 0.2 | Logit boost for semantically related words |
| `semantic_guidance/high_strength_boost` | 0.0-1.0 | 0.1 | Logit boost for high-strength relationships (0.8+) |
| `semantic_guidance/max_similar_words` | 1-10 | 5 | Maximum similar words to consider |

---

## 🔧 CRA Configuration Control

### Example Commands

#### Stricter Coherence Requirements

```json
[[CONFIG_UPDATE: {
  "reason": "Require higher quality generation",
  "correlation_id": "stricter-coherence",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/relationship_learning/quality_evaluation/coherent_threshold",
    "value": 0.6
  }]
}]]
```

#### More Lenient Garbled Detection

```json
[[CONFIG_UPDATE: {
  "reason": "Allow more variation in generation",
  "correlation_id": "lenient-garbled",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/relationship_learning/quality_evaluation/garbled_threshold",
    "value": 0.15
  }]
}]]
```

#### Stronger Semantic Guidance

```json
[[CONFIG_UPDATE: {
  "reason": "Increase semantic influence on generation",
  "correlation_id": "stronger-guidance",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/relationship_learning/semantic_guidance/semantic_boost",
    "value": 0.3
  }]
}]]
```

#### Disable Relationship Learning

```json
[[CONFIG_UPDATE: {
  "reason": "Disable learning from generation quality",
  "correlation_id": "no-learning",
  "patch": [{
    "op": "replace",
    "path": "/neural/language_model/relationship_learning/enabled",
    "value": false
  }]
}]]
```

---

## 📊 Monitoring After Config Changes

### Relationship Learning Metrics

After adjusting relationship learning settings, monitor:

1. **Generation Coherence Scores**
   - Should improve with stricter thresholds
   - Check via language system diagnostics

2. **Relationship Success/Failure Rates**
   - Which relationships are being strengthened?
   - Which relationships are being weakened?
   - Check via knowledge web diagnostics

3. **Semantic Network Evolution**
   - Are relationships strengthening over time?
   - Are useless relationships being pruned?
   - Check via quality control metrics

4. **Language Generation Quality**
   - Ratio of coherent vs garbled generation
   - Should improve as system learns
   - Check via neural language training events

5. **Word Combination Patterns**
   - Which word combinations are being learned?
   - Are patterns emerging?
   - Check via vocabulary growth and word associations

---

## 🔗 Integration Points

### Config File Location

All settings are in `config.json` under:
```json
{
  "neural": {
    "language_model": {
      "relationship_learning": {
        "enabled": true,
        "quality_evaluation": { ... },
        "semantic_guidance": { ... }
      }
    }
  }
}
```

### Code Integration

- **Neural Organism**: `reality_simulator/neural/neural_organism.py`
  - Reads config in `_evaluate_generation_quality()`
  - Reads config in `generate_tokens()` for semantic guidance
  - Checks `enabled` flag before recording success/failure

### CRA Documentation

- **CRA Prompt**: `causation_web_ui.py` (lines ~4157-4180)
  - Documents all relationship learning parameters
  - Provides example CONFIG_UPDATE commands
  - Lists monitoring guidelines

---

## 🎯 Future Enhancements

### Scikit-Learn Configuration (When Implemented)

When scikit-learn enhancements are implemented, they will also be exposed:

- **Text Feature Extraction**: TF-IDF, CountVectorizer parameters
- **Nearest Neighbors**: k-neighbors, metric selection
- **Feature Selection**: SelectKBest, mutual_info parameters
- **Model Selection**: GridSearchCV, cross-validation parameters

These will follow the same pattern:
1. Add to `config.json` under `/scikit/`
2. Update code to read from config
3. Document in CRA prompt
4. Provide example CONFIG_UPDATE commands

---

## ✅ Summary

**All new systems are now fully configurable:**

- ✅ **Neural Relationship Learning**: 13 configurable parameters
- ✅ **Config File**: All settings in `config.json`
- ✅ **CRA Documentation**: Complete parameter documentation
- ✅ **Real-Time Control**: CRA can adjust via CONFIG_UPDATE
- ✅ **Monitoring Guidelines**: What to watch after changes

**The CRA can now:**
- Understand all relationship learning parameters
- Adjust quality thresholds in real-time
- Tune semantic guidance strength
- Enable/disable relationship learning
- Monitor learning effectiveness

---

**Last Updated**: 2025-01-XX  
**Status**: ✅ Complete | Ready for Use

