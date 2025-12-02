# Dynamic Multi-Dimensional Linguistic Awareness System

## Overview

The linguistic system has been redesigned as a **dynamic, context-aware word association framework** that operates like a precise, adaptive system capable of multi-dimensional situational assessment. The system now uses all available data to generate contextually appropriate word associations with high precision and responsiveness.

## Core Concept

The system functions as a **word dynamo** - a dynamic association framework that:
- Assesses organism position, environment, and system dynamics simultaneously
- Uses all 18 state features plus network/breath state for comprehensive awareness
- Generates precise, contextually appropriate word associations
- Adapts in real-time to changing conditions across multiple dimensions

## Key Enhancements

### 1. Multi-Dimensional Context Assessment

The system now evaluates **14 distinct dimensions** simultaneously:

1. **Action-Based** - Immediate behavioral context
2. **Fitness-Based** - Organism vitality
3. **Resource-Based** - Material context
4. **Connection-Based** - Social/network context
5. **Positional Awareness** - Spatial context (center/edge, proximity)
6. **Local Density** - Environmental context (crowded/sparse)
7. **Violation Pressure** - System stability context
8. **Network Coherence** - System integration context
9. **Evolution Pressure** - Adaptation context
10. **Phase Mismatch** - Synchronization context
11. **System Health** - Ecosystem wellness context
12. **Breath Phase** - Temporal/rhythmic context
13. **Action Success** - Behavioral feedback context
14. **Generation Age** - Temporal/evolutionary context

### 2. Dynamic Word Scoring System

Words are scored based on their relevance across multiple dimensions:
- Each dimension contributes a score (0.0-1.0) based on context
- Scores are aggregated to prioritize the most contextually relevant words
- Semantic relationships expand high-scoring words for associative complexity
- Top 15 words (score > 0.3) are selected for assignment

### 3. Expanded Vocabulary

Added **40+ new words** covering:
- Spatial concepts: `center`, `edge`, `crowded`, `dense`, `sparse`
- System dynamics: `pressure`, `crisis`, `stress`, `calm`, `balanced`
- Network states: `connected`, `united`, `coherent`, `fragmented`, `disconnected`
- Evolution: `adapt`, `evolve`, `change`, `persist`
- Synchronization: `mismatch`, `desynchronized`
- Health: `healthy`, `thriving`, `sick`, `declining`
- Breath phases: `expand`, `consolidate`
- System phases: `precise`, `focused`, `discover`
- Action outcomes: `success`, `effective`, `failure`, `ineffective`
- Age: `mature`, `experienced`, `young`, `new`
- Basic existence: `exist`, `be`, `act`

### 4. Full State Vector Integration

The system now uses the complete **18-feature state vector**:
1. Fitness (0-1)
2. Resources (0-1)
3. Connections (normalized)
4. Position X (normalized)
5. Position Y (normalized)
6. Recent action success rate
7. Local density
8. Distance to nearest neighbor
9. Generation age (normalized)
10. Parent fitness average
11-12. Breath features (2 features)
13-17. VP components (5 features)
18. System health (0-1)

### 5. Network & Breath State Integration

The system incorporates:
- **Network State**: VP value, generation, organism count, connections
- **Breath State**: Depth, phase, cycle, system phase (genesis/sovereign)

## Technical Implementation

### Enhanced `get_situational_awareness()` Method

```python
def get_situational_awareness(
    organism_state: np.ndarray,        # Full 18-feature vector
    organism_action: Optional[int],    # Current/recent action
    network_state: Optional[Dict],     # Network-level context
    breath_state: Optional[Dict],      # Breath engine context
    context_memory: Optional[Any]      # Vocabulary access
) -> List[str]
```

### Word Scoring Algorithm

1. **Dimension Assessment**: Each of 14 dimensions evaluates context
2. **Score Accumulation**: Words accumulate scores from relevant dimensions
3. **Semantic Expansion**: Top words expand through semantic relationships
4. **Prioritization**: Words sorted by score, top 15 selected (score > 0.3)

### Integration with Language Teacher

The `LanguageTeacher` now:
- Retrieves full 18-feature state vector via `get_state_features()`
- Passes complete context (state, action, network, breath) to knowledge web
- Falls back gracefully if full state unavailable
- Uses dynamic awareness as primary, hardcoded maps as supplement

## Benefits

1. **Precision**: Context-aware word selection based on comprehensive data
2. **Responsiveness**: Real-time adaptation to changing conditions
3. **Multi-Dimensional**: Simultaneous assessment across 14 dimensions
4. **Associative Complexity**: Semantic relationships create rich word networks
5. **Scalability**: Easy to add new dimensions or words
6. **Robustness**: Graceful fallback when data unavailable

## Example Scenarios

### High VP + Low Coherence + Edge Position
- Words: `pressure`, `unstable`, `crisis`, `edge`, `fragmented`, `disconnected`
- Context: System under stress, organism at periphery, network fragmented

### Low VP + High Coherence + Center Position + Inhale Phase
- Words: `stable`, `calm`, `center`, `expand`, `grow`, `explore`, `coherent`
- Context: Stable system, organism at center, expansion phase

### High Fitness + Many Connections + High Resources + Sovereign Phase
- Words: `thrive`, `flourish`, `social`, `connected`, `precise`, `focused`, `rich`
- Context: Successful organism, well-connected, resource-rich, precision phase

## Future Enhancements

1. **Learned Embeddings**: Semantic embeddings learned from experience
2. **Temporal Patterns**: Word associations based on historical patterns
3. **Causal Relationships**: Words linked to causation chains
4. **Adaptive Scoring**: Scores learned from organism success
5. **Multi-Organism Context**: Words based on neighbor states

## Files Modified

- `reality_simulator/language/linguistic_knowledge_web.py`
  - Enhanced `get_situational_awareness()` with 14-dimensional assessment
  - Added 40+ new system dynamics concepts
  - Implemented dynamic word scoring system
  - Added numpy import for state vector processing

- `reality_simulator/language/language_teacher.py`
  - Updated to pass full context to knowledge web
  - Integrated 18-feature state vector retrieval
  - Fixed indentation errors in hardcoded fallback

## Summary

The linguistic system is now a **dynamic, multi-dimensional word association framework** that provides precise, context-aware word selection based on comprehensive situational assessment. It operates like a responsive, adaptive system capable of evaluating multiple dimensions simultaneously to generate linguistically appropriate associations that reflect the organism's true state and context.

