# Critical Papers Report for RCUS Implementation

## Executive Summary

This report analyzes five foundational works that inform our Recursive Conceptual Understanding System (RCUS). Each paper offers unique insights for achieving "infinite from finite"—the compositional generation of novel concepts from a primitive axiomatic base.

---

## 1. The Neuro-Symbolic Concept Learner (NS-CL)
**Mao, Gan, Kohli, Tenenbaum, Wu (ICLR 2019)**

### Core Innovation
NS-CL learns visual concepts, words, and semantic parsing **without explicit supervision**—learning by simply looking at images and reading paired questions/answers.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    NS-CL Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Image ──► Perception Module ──► Object-Based Scene Rep     │
│                                         │                   │
│  Question ──► Semantic Parser ──► Symbolic Program          │
│                                         │                   │
│                    ┌────────────────────┘                   │
│                    ▼                                        │
│           Neuro-Symbolic Reasoning Module                   │
│           (Executes programs on scene representation)       │
│                    │                                        │
│                    ▼                                        │
│               Answer/Grounding                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Mechanisms

1. **Object-Based Scene Representation**: Rather than raw pixels, builds structured representations of objects with learned attributes
2. **Executable Symbolic Programs**: Sentences become programs that can be executed (e.g., `filter(scene, color=red) → count()`)
3. **Curriculum Learning**: Guides search over the large compositional space—starts simple, increases complexity

### Generalization Properties
- **Novel compositions**: Generalizes to attribute combinations never seen during training
- **New domains**: Transfers to entirely new visual domains
- **Bidirectional retrieval**: Enables image-text matching without explicit training

### Key Insight for RCUS
> *"The perception module learns visual concepts based on the language description of the object being referred to. Meanwhile, the learned visual concepts facilitate learning new words and parsing new sentences."*

**Translation for RCUS**: Our axioms should **bootstrap each other**. Learning "MORE" from comparing quantities should help ground "GOOD" (more is often good), which helps ground "DO" (do what is good), creating a virtuous cycle.

### Implementation Implications
1. **Differentiable execution**: Programs must be differentiable to enable gradient flow
2. **Joint training**: Perception and language modules train together
3. **Curriculum**: Start with single-axiom groundings, build to multi-axiom compositions

---

## 2. Neural Module Networks (NMNs)
**Andreas, Rohrbach, Darrell, Klein (CVPR 2016)**

### Core Innovation
Exploits the **compositional structure of language** to dynamically compose neural modules into question-specific networks.

### Key Insight
> *"Visual question answering is fundamentally compositional in nature—a question like 'where is the dog?' shares substructure with questions like 'what color is the dog?' and 'where is the cat?'"*

### Architecture

```
Question: "What color is the dog on the left?"
                    │
                    ▼
           Linguistic Parse
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
[find-dog]     [find-left]    [classify-color]
    │               │               │
    └───────┬───────┘               │
            ▼                       │
         [and]                      │
            └───────────┬───────────┘
                        ▼
                   [compose]
                        │
                        ▼
                    Answer
```

### Module Types (Reusable Components)
| Module | Input | Output | Example |
|--------|-------|--------|---------|
| `find[x]` | Image | Attention | find[dog] → dog locations |
| `relate[r]` | Attention | Attention | relate[left] → filter to left |
| `describe[a]` | Attention | Label | describe[color] → "brown" |
| `count` | Attention | Number | count → "3" |
| `and` | Attention × 2 | Attention | intersection |
| `or` | Attention × 2 | Attention | union |

### Training Protocol
- **Joint training**: All modules train together on full task
- **Weight sharing**: Same `find` module for all objects
- **Structure from language**: Parse tree dictates network architecture

### Key Insight for RCUS
> *"We describe a procedure for constructing and learning neural module networks, which compose collections of jointly-trained neural 'modules' into deep networks"*

**Translation for RCUS**: Our composition operators (`WITH`, `MORE`, `DO`) should be **neural modules** that can be combined based on the structural relationships between axioms.

### Implementation Implications
1. **Module inventory**: Define neural modules for each composition operator
2. **Dynamic composition**: Structure from conceptual relationships, not language parse
3. **Shared weights**: Same `MORE` operator regardless of what's being compared

---

## 3. Gärdenfors' Conceptual Spaces
**Peter Gärdenfors (MIT Press, 2000)**

### Core Innovation
A **geometric framework** for representing concepts that bridges symbolic AI and connectionism.

### Fundamental Structure

```
                 Quality Dimensions
                        │
                        ▼
    ┌─────────────────────────────────────┐
    │           Conceptual Space          │
    │                                     │
    │    Point = Object instance          │
    │    Region = Concept                 │
    │    Convex Region = Natural Category │
    │                                     │
    │         ┌─────────────┐             │
    │         │   "RED"     │ ← Convex    │
    │         │   ●  ●      │   region    │
    │         │      ●      │             │
    │         └─────────────┘             │
    │                                     │
    │    ● = instance of red thing        │
    └─────────────────────────────────────┘
```

### Key Theoretical Claims

1. **Quality Dimensions**: Fundamental representational axes
   - Can be **integral** (inseparable, like hue-saturation) or **separable** (independent, like pitch-loudness)
   - Correspond to phenomenal qualities of experience

2. **Convexity Constraint**: Natural categories form **convex regions**
   - If A and B are in category C, everything between A and B is also in C
   - This is why humans find "green or blue" natural but "green or red" odd (non-convex in color space)

3. **Similarity = Geometric Distance**
   - Similarity is inverse distance in conceptual space
   - Explains psychological similarity judgments

4. **Prototype Theory**: Category center is prototype
   - Membership = proximity to prototype
   - Graded membership naturally emerges

### Key Insight for RCUS
> *"A conceptual space is built up from geometrical structures based on a number of quality dimensions... natural categories are convex regions."*

**Translation for RCUS**: Our 18 axioms define the **quality dimensions** of a conceptual space. New concepts emerge as **regions** in this space, and the convexity constraint ensures coherent categories.

### Implementation Implications

1. **Axiom Embeddings**: Each axiom defines a dimension (or small set of dimensions)
2. **Concept Regions**: Composed concepts are regions, not points
3. **Betweenness Operator**: Crucial for testing concept coherence
4. **Prototype Learning**: Center of region = canonical exemplar

### Dimensional Structure for 18 Axioms

| Axiom Domain | Dimensions | Structure |
|--------------|------------|-----------|
| **Existence** (EXIST, ONE, MANY) | Quantity axis | Linear, [0, ∞) |
| **Comparison** (MORE, LESS, SAME) | Magnitude differences | Relative, signed |
| **Agency** (SELF, OTHER, WITH) | Social topology | Graph-structured |
| **Value** (GOOD, BAD) | Valence axis | Bipolar, [-1, +1] |
| **Action** (DO, CAUSE) | Causal structure | Directed relations |
| **Time** (BEFORE, AFTER, NOW) | Temporal axis | Linear, ordered |
| **Space** (HERE, THERE) | Spatial axes | Egocentric, 3D |

---

## 4. DisCoCat (Distributional Compositional Categorical)
**Coecke, Sadrzadeh, Clark (2010)**

### Core Innovation
Uses **category theory** to unify distributional semantics (words as vectors) with compositional semantics (meaning from structure).

### Mathematical Framework

```
                Grammar Category (G)
                (Pregroup derivations)
                        │
                        │ F (Functor)
                        ▼
               Semantics Category (FVect)
               (Finite vector spaces)
               
Word → Vector
Grammatical Derivation → Linear Map
Sentence Meaning = Apply maps to compose word vectors
```

### Key Mechanism: Tensor Contraction

For a simple sentence "dogs chase cats":
- `dogs` → vector in **N** space (nouns)
- `chase` → tensor in **N ⊗ S ⊗ N** space (verb takes two nouns, produces sentence)
- `cats` → vector in **N** space

Meaning = Contract the tensors:
```
meaning(dogs chase cats) = dogs ⊗ chase ⊗ cats
                        = Σ_i,j,k dogs_i × chase_ijk × cats_k
```

### String Diagrams
DisCoCat uses **string diagrams** to visualize information flow:

```
    dogs        chase        cats
      │           │            │
      │     ┌─────┼─────┐      │
      └─────┤     │     ├──────┘
            │     │     │
            └─────┼─────┘
                  │
                  ▼
           sentence meaning
```

### Key Insight for RCUS
> *"The type reductions of Pregroups are 'lifted' to morphisms in a category, a procedure that transforms meanings of constituents into a meaning of the (well-typed) whole."*

**Translation for RCUS**: Axiom compositions have **types** (like grammatical types). The composition operators define how to combine axiom-vectors into concept-vectors.

### Implementation Implications

1. **Axiom Vectors**: Each axiom gets a learned vector embedding
2. **Composition Tensors**: `WITH`, `MORE`, etc. are tensors that combine axiom vectors
3. **Type System**: Compositions are well-typed (can't apply `MORE` to a boolean)
4. **Single Meaning Space**: All concepts (primitive and composed) live in same space, enabling comparison

---

## 5. SCAN Benchmark & Compositional Generalization
**Lake & Baroni (ICML 2018)**

### Core Innovation
Demonstrated that standard RNNs **fail at systematic compositional generalization**, creating a crucial benchmark for compositional systems.

### The SCAN Task

```
Input: "jump twice and walk left"
Output: JUMP JUMP WALK TURN_LEFT WALK

Training: Individual primitives + some compositions
Testing: Novel compositions of seen primitives
```

### Failure Modes

| Test Split | Description | RNN Accuracy |
|------------|-------------|--------------|
| **Random** | Random train/test split | 99.8% |
| **Length** | Longer sequences than training | 20.8% |
| **Add Jump** | "jump" only seen in simple contexts | 1.2% |
| **Template** | Novel templates around primitives | 63.0% |

### Key Insight
> *"Humans can understand and produce new utterances effortlessly, thanks to their compositional skills... However, when generalization requires systematic compositional skills, RNNs fail spectacularly."*

### GECA Solution (Andreas, 2019)
**Good-Enough Compositional Data Augmentation** offers a practical fix:
- Synthetic training examples by **swapping fragments** that appear in similar contexts
- Reduces error by up to **87%** on SCAN
- Model-agnostic—works with any seq2seq

### Key Insight for RCUS
**SCAN is our litmus test.** If RCUS truly achieves compositional understanding:
1. Training on axioms + some 2-axiom compositions
2. Should generalize to arbitrary n-axiom compositions
3. Without exponentially growing training data

### Implementation Implications

1. **Benchmark**: Use SCAN-like evaluation for RCUS
2. **Anti-shortcuts**: Test for composition splits (like "add jump")
3. **Length generalization**: Test 3-axiom compositions after training on 2-axiom
4. **GECA augmentation**: Consider compositional data augmentation during training

---

## Synthesis: Unified Architecture for RCUS

Based on these papers, here's the recommended architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                    RCUS Unified Architecture                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Conceptual Space Layer                        │  │
│  │                      (Gärdenfors)                                │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │  │
│  │  │ EXIST   │ │ MORE    │ │ GOOD    │ │ DO      │ │ BEFORE  │   │  │
│  │  │ dim 0-2 │ │ dim 3-5 │ │ dim 6-8 │ │ dim 9-11│ │dim 12-14│   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │  │
│  │           18 Axioms = Quality Dimensions (54D total)            │  │
│  └──────────────────────────────┬──────────────────────────────────┘  │
│                                 │                                      │
│  ┌──────────────────────────────┼──────────────────────────────────┐  │
│  │              Composition Module Layer (NMN-style)               │  │
│  │                                                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │ WITH        │  │ MODIFY      │  │ SEQUENCE    │              │  │
│  │  │ (Tensor:    │  │ (Tensor:    │  │ (Tensor:    │              │  │
│  │  │  A×B→C)     │  │  A×M→A')    │  │  A×B→AB)    │              │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │  │
│  │                                                                  │  │
│  │  Compositions are well-typed (DisCoCat) & differentiable (NS-CL)│  │
│  └──────────────────────────────┬──────────────────────────────────┘  │
│                                 │                                      │
│  ┌──────────────────────────────┼──────────────────────────────────┐  │
│  │               Neuro-Symbolic Execution Layer                     │  │
│  │                                                                  │  │
│  │  ConceptProgram = axiom₁ ∘ operator ∘ axiom₂ ∘ operator ∘ ...   │  │
│  │                                                                  │  │
│  │  Execution: Apply operators to axiom embeddings                  │  │
│  │  Result: Concept vector in unified meaning space                 │  │
│  └──────────────────────────────┬──────────────────────────────────┘  │
│                                 │                                      │
│  ┌──────────────────────────────┼──────────────────────────────────┐  │
│  │                  Utility-Guided Discovery                        │  │
│  │                                                                  │  │
│  │  For each candidate concept C:                                   │  │
│  │    utility(C) = predictive_power(C) - complexity(C)              │  │
│  │                                                                  │  │
│  │  Promote concepts that help predict rewards                      │  │
│  │  Prune concepts that don't improve predictions                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Evaluation Layer (SCAN)                       │  │
│  │                                                                  │  │
│  │  Test: Can system compose axioms it has never seen together?     │  │
│  │  Metric: Accuracy on held-out composition splits                 │  │
│  │  Threshold: ≥75% on novel 3+ axiom compositions                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways by Paper

| Paper | Core Lesson | RCUS Application |
|-------|-------------|------------------|
| **NS-CL** | Learn concepts from grounded experience, not labels | Ground axioms through RL environment interaction |
| **NMNs** | Composition structure from problem structure | Use axiom relationships to structure neural composition |
| **Conceptual Spaces** | Concepts are geometric regions, not symbols | Axioms define dimensions; concepts are convex regions |
| **DisCoCat** | Category theory unifies distribution + composition | Type system for well-formed axiom compositions |
| **SCAN** | Neural nets fail compositional generalization | Use SCAN-like benchmarks; consider GECA augmentation |

---

## Recommended Implementation Order

### Phase 1: Axiomatic Foundation (Weeks 1-2)
1. Define 18 axiom embeddings in conceptual space
2. Implement grounding functions for each axiom
3. Build environment that provides grounding signal

### Phase 2: Composition Operators (Weeks 3-4)
1. Implement `WITH` tensor (conjunction)
2. Implement `MODIFY` tensor (e.g., MORE + GOOD → BETTER)
3. Implement `SEQUENCE` tensor (temporal composition)
4. Define type system for well-formed compositions

### Phase 3: Discovery & Learning (Weeks 5-7)
1. Implement utility function: `predictive_power - complexity`
2. Build candidate generation (random axiom combinations)
3. Add pruning (remove low-utility concepts)
4. Curriculum: 2-axiom → 3-axiom → n-axiom

### Phase 4: Evaluation & Iteration (Weeks 8-10)
1. Create SCAN-like benchmark for axiom compositions
2. Test on held-out composition splits
3. Implement GECA-style augmentation if needed
4. Iterate until ≥75% on novel compositions

---

## Conclusion

These five papers converge on a unified vision:

> **Infinite from finite emerges when:**
> 1. **Primitives are grounded** (NS-CL: learn from experience)
> 2. **Composition is structural** (NMNs: structure from relationships)
> 3. **Representation is geometric** (Gärdenfors: concepts as regions)
> 4. **Composition is typed** (DisCoCat: category-theoretic composition)
> 5. **Generalization is tested** (SCAN: systematic evaluation)

The RCUS architecture synthesizes all five approaches. Implementation should proceed systematically, validating compositional generalization at each stage before adding complexity.

---

*Report generated for Convergence Engine RCUS implementation*
*Last updated: December 2024*
