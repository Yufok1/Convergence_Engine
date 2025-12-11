# Convergence Engine Case Studies
## Language Composure, Understanding & Articulation

**Budget**: ~$1/hour total across 5 GPUs (~$0.20/GPU/hour)
**Duration**: 3-4 hours per experiment
**Focus**: How organisms develop language comprehension and articulate responses

---

## Research Questions

1. **Composure**: How do organisms learn to structure coherent responses?
2. **Understanding**: Can organisms demonstrate comprehension of input context?
3. **Articulation**: What conditions produce expressive, varied language?
4. **Vocabulary Depth**: Quality vs quantity of word usage
5. **Semantic Precision**: Using the RIGHT word, not just A word

---

## Case Study Overview

| GPU | Study | Key Manipulation | Research Question |
|-----|-------|------------------|-------------------|
| 1 | **Slow Learner** | Low LR, high patience, small pop | Does slower learning = deeper understanding? |
| 2 | **Immersion** | Massive vocab exposure, no staged delay | Does vocabulary flood help or hurt composure? |
| 3 | **Survival Pressure** | High competition, fast battles | Does stress produce terse or rich language? |
| 4 | **Social Learning** | Large alliances, low competition | Does cooperation breed shared understanding? |
| 5 | **Creative Specialist** | High temperature, semantic guidance boost | Does creativity improve articulation? |

---

## Study 1: SLOW LEARNER
**Hypothesis**: Slower learning rate with longer training produces deeper semantic understanding

Key settings:
- `learning_rate: 0.001` (5x slower than default)
- `epsilon_decay: 0.995` (slower exploration decay)
- `population_size: 7` (small, stable group)
- `competition_intensity: 0.1` (minimal pressure)
- `teaching_frequency: 1` (constant teaching)

**Measure**: Response coherence over time, vocabulary retention

---

## Study 2: IMMERSION
**Hypothesis**: Immediate exposure to full vocabulary produces faster articulation

Key settings:
- `staged_knowledge.enabled: false` (no delay)
- `vocab_size: 30000` (larger vocabulary)
- `organism_embedding_alpha: 0.2` (faster embedding learning)
- `temperature: 1.0` (neutral generation)

**Measure**: Unique words per response, time to first coherent output

---

## Study 3: SURVIVAL PRESSURE
**Hypothesis**: High evolutionary pressure produces efficient, precise language

Key settings:
- `competition_intensity: 0.5` (high)
- `rounds_per_cycle: 3` (frequent battles)
- `survival_threshold: 0.5` (harsh)
- `population_size: 15` (more competition)
- `germination_rate: 1.0` (fast replacement)

**Measure**: Word economy (meaning per word), response length vs quality

---

## Study 4: SOCIAL LEARNING
**Hypothesis**: Allied organisms develop shared vocabulary and understanding

Key settings:
- `max_alliance_size: 20` (large alliances)
- `competition_intensity: 0.05` (very low)
- `betrayal_chance: 0.0` (stable relationships)
- `population_size: 25` (larger social group)
- `phenotype_to_vocabulary: true` (personality affects words)

**Measure**: Vocabulary overlap between allies, response similarity

---

## Study 5: CREATIVE SPECIALIST
**Hypothesis**: Higher temperature + semantic guidance produces more expressive language

Key settings:
- `temperature: 1.5` (more creative)
- `semantic_boost: 0.4` (strong guidance)
- `high_strength_boost: 0.2` (reward strong associations)
- `concept_system.enabled: true` (active concept formation)
- `knowledge_web_influence_interval: 10` (frequent updates)

**Measure**: Vocabulary diversity, novel word combinations, articulation quality

---

## Machine Setup

```bash
# On each GPU machine:
git clone <repo>
cd Convergence_Engine
pip install -r requirements.txt

# Copy the study config
cp case_studies/config_study_N.json config.json

# Fresh start
python clear_all_data.py

# Run (headless recommended)
python causation_web_ui.py
```

---

## Data Collection

### During Experiment (every 30 min)
1. Screenshot the organism chat panel
2. Note vocabulary counts in debug panel
3. Check Highlander battle count

### After Experiment
1. `data/logs/application.log` - full system log
2. Chat with each surviving organism - save transcripts
3. Export atom formation data from debug panel
4. Note final population and vocabulary sizes

---

## Analysis Metrics

### Composure Score
- % responses without `<UNK>` tokens
- Average sentence length
- Grammar structure (subject-verb patterns)

### Understanding Score  
- Context relevance (does response match input?)
- Follow-up coherence (multi-turn consistency)
- Concept accuracy (uses concepts correctly)

### Articulation Score
- Vocabulary diversity (unique words / total words)
- Semantic precision (word-concept alignment)
- Expression richness (adjectives, modifiers used)

### Overall Language Quality
```
LQ = (Composure × 0.3) + (Understanding × 0.4) + (Articulation × 0.3)
```

---

## Expected Results

| Study | Composure | Understanding | Articulation |
|-------|-----------|---------------|--------------|
| Slow Learner | HIGH | HIGH | MEDIUM |
| Immersion | LOW | MEDIUM | HIGH |
| Survival Pressure | HIGH | MEDIUM | LOW |
| Social Learning | MEDIUM | HIGH | MEDIUM |
| Creative Specialist | MEDIUM | LOW | HIGH |

---

## Post-Experiment Comparison

After all 5 complete:
1. Rank by overall Language Quality score
2. Identify which conditions produced best understanding
3. Check if any organism achieved multi-turn coherent dialogue
4. Compare vocabulary depth vs breadth across studies
5. Document emergent language patterns
