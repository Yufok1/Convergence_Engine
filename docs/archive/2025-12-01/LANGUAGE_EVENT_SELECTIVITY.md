# Language Event Selectivity - Quality Over Quantity

## Problem
Language events were overpopulating the causation graph, making it hard to see relationships between neural, ML, and other systems. Too many routine language events were being emitted compared to the selective nature of neural/ML events.

## Solution
Made language events more selective - only emit when something **significant** happens, matching the importance level of neural/ML events.

## Changes Applied

### 1. Word Assignment Events (`context_memory.py`)
**Before:** Emitted for every new word assignment to an organism
**After:** Only emit when word is adopted by 3+ organisms (significant language emergence)

**Rationale:** Matches ML event selectivity - only emit when language pattern becomes meaningful across multiple organisms.

### 2. Butterfly Chat Response Events (`butterfly_chat.py`)
**Before:** Emitted for every organism response
**After:** Only emit for high-quality responses (confidence > 0.5 OR fitness > 0.5)

**Rationale:** Matches `neural_decision` event selectivity - only meaningful decisions/responses are tracked.

### 3. Organism Communication Events (`symbiotic_network.py`)
**Before:** Emitted for every token exchange
**After:** Only emit for significant exchanges:
- Strong connections (strength > 0.6)
- Linguistic edges (lifetime >= 10 generations)
- Large exchanges (tokens >= 5)

**Rationale:** Matches ML event selectivity - only meaningful communications that indicate language emergence.

### 4. Vocabulary Growth Events (`language_system.py`)
**Before:** Emitted for every new word added
**After:** Only emit at vocabulary milestones (every 10 words)

**Rationale:** Matches neural training event frequency - one event per training step, not per operation.

## Event Frequency Comparison

### Neural Events
- `neural_training`: Once per training step (per generation)
- `neural_decision`: Only when confidence > 0.5 or epsilon > 0.5
- `neural_language_training`: Only when language loss calculated

### ML Events
- `phenotype_emergence`: Only on cluster count changes
- `cluster_collapse`: Only on significant cluster changes
- `anomaly_detection`: Only on significant anomalies

### Language Events (Now)
- `word_assignment`: Only when 3+ organisms adopt word
- `butterfly_chat_response`: Only when confidence/fitness > 0.5
- `organism_communication`: Only for strong/linguistic/large exchanges
- `vocabulary_growth`: Only at 10-word milestones

## Result
Language events now match the selectivity and importance level of neural/ML events, preventing overpopulation of the causation graph while still tracking significant language emergence patterns.

