# RCUS Research Synthesis
## Grok Task Force Findings - December 1, 2025

---

# 🎯 CONVERGENCE SUMMARY

All four agents' research converges on key insights:

## The Core Answer

| Question | Converged Answer |
|----------|------------------|
| **Axiom Set** | **16-18 primitives** (add temporal, spatial, modal to our 12) |
| **Architecture** | **Hybrid Neuro-Symbolic** (unanimous) |
| **Discovery** | **Utility-based, not frequency-based** (predictive coding) |
| **Evaluation** | **Compositional generalization benchmarks** (SCAN, COGS, gSCAN) |

---

# 📚 AGENT 1: THEORETICAL FOUNDATIONS

## Enhanced Axiom Set (16-18 primitives)

### Original (12):
```
exist, more, less, same, self, other, with, without, good, bad, do, cause
```

### Recommended Additions:

**Temporal (3):**
- `before` - temporal precedence
- `after` - temporal succession  
- `now` - present moment

**Spatial (4):**
- `here` - current location
- `there` - distant location
- `near` - proximity
- `far` - distance

**Quantity (2):**
- `one` - singularity
- `many` - plurality

**Modality (2):**
- `can` - possibility
- `must` - necessity

### Final Axiom Set (18 primitives):
```python
AXIOMS = {
    # Existential (1)
    'exist',
    
    # Quantitative (4)
    'more', 'less', 'one', 'many',
    
    # Relational (4)
    'same', 'self', 'other', 'with',
    
    # Evaluative (2)
    'good', 'bad',
    
    # Causal (2)
    'do', 'cause',
    
    # Temporal (3)
    'before', 'after', 'now',
    
    # Spatial (2)
    'here', 'there',
}
```

## Key Theoretical Sources

### Conceptual Spaces (Gärdenfors, 2000)
- **Concepts as vectors** in quality space
- **Composition via tensor products**: `A ⊗ B`
- **Convex regions** for natural concepts
- **Distance = similarity**

### Symbol Grounding Solutions
1. **Perceptual Grounding** (Steels, 2008) - symbols grounded in sensorimotor experience
2. **Embodied Grounding** (Barsalou, 1999) - concepts as bodily simulations
3. **Hierarchical Grounding** - sensory → symbolic layers

### Image Schemas (Lakoff & Johnson)
Add these to axioms:
- **CONTAINER**: in/out boundary
- **PATH**: source → goal
- **FORCE**: push/pull dynamics

---

# 🏗️ AGENT 2: IMPLEMENTATION ARCHITECTURE

## Neuro-Symbolic Concept Learner (NS-CL) - Mao et al.

**Two-Phase Architecture:**
```
Phase 1: Neural Perception → Symbolic Concepts
Phase 2: Symbolic Reasoning → Neural Execution
```

**Key Insight**: Differentiable logic operations allow backpropagation through symbolic reasoning.

## Neural Module Networks (NMNs) - Andreas et al.

**Dynamic Composition:**
```python
class ModuleLibrary:
    modules = {
        'find': FindModule(),
        'describe': DescribeModule(),
        'relate': RelateModule(),
        'combine': CombineModule()
    }
    
    def compose(self, parse_tree):
        return self.build_execution_graph(parse_tree)
```

**Key Insight**: Module composition based on structure, not memorization.

## Recommended Hybrid Architecture

```python
class HybridConceptLearner(nn.Module):
    def __init__(self):
        # Neural perception pipeline
        self.feature_encoder = NeuralEncoder()
        
        # Symbolic concept layer
        self.concept_classifier = ConceptClassifier()
        
        # Compositional reasoning (NMN-style)
        self.composition_network = NeuralModuleNetwork()
        
        # Symbolic interface
        self.symbolic_interface = SymbolicReasoner()
    
    def forward(self, x, composition_spec=None):
        features = self.feature_encoder(x)
        concepts = self.concept_classifier(features)
        
        if composition_spec:
            composed = self.composition_network(concepts, composition_spec)
        
        return self.symbolic_interface(concepts, composed)
```

## Training for Compositional Structure

**Key Techniques:**
1. **Curriculum Learning**: atomic → binary → ternary → recursive
2. **Structure-Preserving Loss**: Penalize shortcuts
3. **Modularity Regularization**: Encourage independent components

```python
class CompositionalLoss(nn.Module):
    def forward(self, pred, target, structure):
        recon = F.mse_loss(pred, target)
        
        # Penalize if composed ≠ original (shortcut detected)
        comp = F.mse_loss(self.recompose(pred, structure), target)
        
        # Structure preservation
        struct = F.l1_loss(self.extract_structure(pred), structure)
        
        return recon + 0.5 * comp + 0.3 * struct
```

---

# 🔍 AGENT 3: CONCEPT DISCOVERY ALGORITHMS

## The Critical Shift

```
❌ OLD: Crystallize if pattern is COMMON (frequency-based)
✅ NEW: Crystallize if pattern PREDICTS REWARDS (utility-based)
```

## Developmental Psychology Insights

### Piaget
- **Assimilation**: Fit new experience into existing concepts
- **Accommodation**: Modify concepts when they don't fit
- **Action-based learning**: Concepts from interaction, not observation

### Vygotsky
- **Scaffolding**: Learn with guidance just beyond current ability
- **Social learning**: Concepts develop through communication

## Predictive Coding Framework (Friston)

**Free Energy Principle:**
- Brain maintains **generative models** of the world
- **Prediction errors** drive learning
- Concepts = **predictive models** that minimize surprise

```python
class PredictiveConcept:
    def __init__(self):
        self.prediction_model = {}  # state → predicted_outcome
        self.prediction_errors = []
        self.utility_score = 0.0
        
    def update(self, state, actual, predicted):
        error = abs(actual - predicted)
        self.prediction_errors.append(error)
        
        # Utility = inverse of prediction error
        recent_errors = self.prediction_errors[-100:]
        self.utility_score = 1.0 / (1.0 + np.mean(recent_errors))
```

## Utility-Driven Discovery Algorithm

```python
class UtilityDrivenConceptDiscovery:
    def __init__(self):
        self.concepts = {}
        self.experience_buffer = []
        self.utility_threshold = 0.7
        
    def discovery_loop(self):
        while True:
            # 1. Collect experiences
            experiences = self.collect_experiences()
            
            # 2. Generate candidates
            candidates = self.generate_candidates(experiences)
            
            # 3. Evaluate UTILITY (not frequency!)
            for candidate in candidates:
                utility = self.evaluate_predictive_utility(candidate)
                
                if utility > self.utility_threshold:
                    self.crystallize_concept(candidate)
            
            # 4. Prune bad concepts
            self.prune_concepts()
    
    def evaluate_predictive_utility(self, abstraction):
        """Does this abstraction predict rewards?"""
        train, test = self.split_experiences()
        
        model = self.train_predictor(abstraction, train)
        predictions = model.predict(test.states)
        actuals = test.rewards
        
        mse = np.mean((predictions - actuals)**2)
        correlation = pearsonr(predictions, actuals)[0]
        
        return (1.0 / (1.0 + mse)) * abs(correlation)
```

## Pruning Criteria

**Dead Concepts (never activate):**
- `time_since_last_use > DEAD_THRESHOLD`
- `activation_frequency < MIN_FREQUENCY`

**Meaningless Concepts (don't predict):**
- `prediction_accuracy < MIN_ACCURACY`
- `reward_correlation < MIN_CORRELATION`

```python
def should_prune(concept, current_time):
    # Dead?
    if current_time - concept.last_activated > DEAD_THRESHOLD:
        return True
    if concept.use_count / concept.age < MIN_FREQUENCY:
        return True
    
    # Meaningless?
    if concept.prediction_accuracy < 0.3:
        return True
    if abs(concept.reward_correlation) < 0.2:
        return True
    
    return False
```

## DisCoCat (Coecke) - Category Theory

**Verdict**: Theoretically elegant but **not practical yet** for implementation.
- Quantum implementations still experimental
- Scale issues with current hardware
- Hard to integrate with neural architectures

**Recommendation**: Keep as theoretical reference, don't implement directly.

---

# 📊 AGENT 4: EVALUATION FRAMEWORK

## Testing "Understanding" vs "Memorization"

### Key Distinction Tests:

1. **Transfer Tests**: Apply concept to novel situations
2. **Counterfactual Reasoning**: "What if X instead of Y?"
3. **Explanatory Depth**: Can explain WHY, not just WHAT
4. **Metacognition**: Knows when it doesn't know

## Compositional Generalization Benchmarks

| Benchmark | Task | What It Tests |
|-----------|------|---------------|
| **SCAN** | Command → Action sequences | Systematic composition |
| **COGS** | Sentence → Logical form | Novel verb-argument combos |
| **gSCAN** | Grounded language navigation | Color-shape generalization |

## Systematic Compositionality Criteria

A system is **systematically compositional** if:
1. **Productivity**: Infinite expressions from finite rules
2. **Systematicity**: "A relates to B" ⟹ understands "B relates to A"
3. **Substitutivity**: Can replace components preserving meaning
4. **Recursion**: Embed structures within structures

## Failure Modes to Detect

| Failure Mode | Description | Detection Method |
|--------------|-------------|------------------|
| **Shortcut Learning** | Exploits surface patterns | Adversarial examples |
| **Isolated Component** | Learns parts, can't combine | Novel combination tests |
| **Statistical Memorization** | Treats sequences as atomic | Exponential combination tests |
| **Distribution Overfitting** | Fails on shifted distributions | OOD evaluation |

## Evaluation Test Suite

### Test Categories:

**1. Zero-Shot Generalization (25%)**
- Novel concept combinations
- Out-of-distribution transfer

**2. Instruction Following (25%)**
- Complex composed commands
- Recursive command embedding

**3. Conceptual Decomposition (20%)**
- Axiom tracing (trace concept → primitives)
- Counterfactual reasoning

**4. Anti-Shortcut Tests (15%)**
- Adversarial compositions
- Minimal pair distinctions

**5. Counterfactual Reasoning (15%)**
- "What if?" scenarios
- Causal chain generation

### Pass Thresholds:

| Test | Minimum | Target |
|------|---------|--------|
| Zero-shot | 70% | 85%+ |
| Commands | 80% | 95%+ |
| Axiom tracing | 60% | 80%+ |
| Counterfactual | 50% | 75%+ |
| Anti-shortcut | 90% | 95%+ |

### Overall Score Formula:
```
Score = 0.25×ZeroShot + 0.25×Commands + 0.20×Decomposition + 0.15×Counterfactual + 0.15×AntiShortcut
```

**Genuine Recursive Understanding: ≥75%**

## Implementation

```python
class RecursiveUnderstandingEvaluator:
    def evaluate(self) -> Dict[str, float]:
        return {
            'zero_shot': self._test_zero_shot(),
            'commands': self._test_commands(),
            'decomposition': self._test_decomposition(),
            'counterfactual': self._test_counterfactual(),
            'anti_shortcut': self._test_anti_shortcut(),
            'overall': self._compute_overall()
        }
```

---

# 🎯 CONVERGED IMPLEMENTATION PLAN

## Phase 1: Foundation (Weeks 1-2)

### 1.1 Axiom Layer
```python
AXIOMS = {
    'exist', 'more', 'less', 'one', 'many',
    'same', 'self', 'other', 'with',
    'good', 'bad', 'do', 'cause',
    'before', 'after', 'now', 'here', 'there'
}  # 18 primitives
```

### 1.2 Grounding Functions
```python
GROUNDING = {
    'exist': lambda o: o.is_alive,
    'more': lambda o, attr: getattr(o, attr).derivative > 0,
    'good': lambda o: o.fitness.derivative > 0,
    'with': lambda o1, o2: distance(o1, o2) < threshold,
    # ... etc
}
```

### 1.3 Composition Operators
```python
OPERATORS = {
    'AND': lambda a, b: min(a, b),
    'OR': lambda a, b: max(a, b),
    'NOT': lambda a: 1 - a,
    'CAUSE': lambda a, b: correlation(a, b),
    'THEN': lambda a, b: temporal_sequence(a, b),
}
```

## Phase 2: Discovery (Weeks 3-4)

### 2.1 Predictive Utility Evaluation
- Train predictor on candidate abstraction
- Test prediction accuracy on held-out data
- Crystallize if utility > 0.7

### 2.2 Pruning System
- Dead: not activated in N generations
- Meaningless: prediction accuracy < 0.3

### 2.3 Integration with Organism Loop
- Process experiences each generation
- Evaluate candidate concepts
- Emit emergence events

## Phase 3: Evaluation (Weeks 5-6)

### 3.1 Implement Test Suite
- Zero-shot tests
- Command following
- Axiom tracing
- Counterfactual reasoning
- Anti-shortcut detection

### 3.2 Benchmarking
- Compare to baseline (current lookup system)
- Track emergence of novel concepts
- Measure abstraction depth

## Success Criteria

**Minimum Viable (Week 6):**
- [ ] ONE novel concept emerges from experience (not predefined)
- [ ] That concept is used in language generation
- [ ] Concept can be traced to axioms

**Target (Week 10):**
- [ ] 3+ levels of abstraction
- [ ] Concepts combine to form new concepts
- [ ] Overall evaluation score ≥75%

---

# 📚 PRIORITY READING LIST

## Must Read (Before Implementation):
1. **NS-CL** - Mao et al. - Neuro-symbolic concept learning
2. **NMNs** - Andreas et al. - Neural module networks
3. **Gärdenfors (2000)** - Conceptual Spaces book

## Should Read (During Implementation):
4. **Friston** - Free Energy Principle / Predictive Coding
5. **Spelke (1994)** - Core Knowledge Systems
6. **SCAN/COGS papers** - Compositional benchmarks

## Nice to Have (Reference):
7. **Harnad (1990)** - Symbol Grounding Problem
8. **Lakoff & Johnson (1980)** - Metaphors We Live By
9. **Coecke - DisCoCat** - Category theory (theoretical reference)

---

# 🚀 NEXT STEPS

1. **Update main spec** with converged findings
2. **Begin Phase 1 implementation** (axioms + grounding)
3. **Set up evaluation framework** early (TDD approach)
4. **Track concept emergence** from first generation

The Grok task force has given us a solid theoretical and practical foundation. Time to build! 🦋
