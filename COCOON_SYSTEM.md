# 🦋 COCOON SYSTEM - Single-File Deployable Agent

**Last Updated:** 2025-12-05

The Cocoon System compiles trained Butterfly organisms into a single, self-contained Python file that can run independently without the full Butterfly infrastructure.

---

## 🎯 Purpose

A **Cocoon** is a "graduation package" - when organisms have evolved through Highlander battles and proven their fitness, they can be exported as standalone agents that:

1. **Run anywhere** - Single Python file, minimal dependencies (just PyTorch + optionally Gym)
2. **Continue learning** - Full triple-loss training system preserved
3. **Match Butterfly behavior** - VP-aware attention, concept reasoning, vocabulary expansion
4. **Deploy in multiple modes** - Chat, Gym environments, HTTP API, or embed in other code

---

## 🏗️ Architecture

### Core Components (Embedded in Cocoon)

| Component | Purpose | Alignment with Butterfly |
|-----------|---------|-------------------------|
| `MultiHeadAttention` | Self-attention with VP gating | ✅ `scores / (1 + vp_value)` |
| `ConceptHead` | Axiom relevance, composition value | ✅ 18 axioms, configurable compositions |
| `OrganismBrain` | Neural network with action + language heads | ✅ Same architecture as `OrganismBrain` |
| `ExperienceBuffer` | Store experiences for training | ✅ `input_tokens`, `target_tokens`, `vp_value` |
| `CocoonAgent` | Manages brains, training, vocabulary | ✅ Mirrors `NeuralOrganism` behavior |

### Training System

The cocoon implements the **full triple-loss** training:

```python
loss = α * rl_loss + β * language_loss + γ * concept_loss
#      0.8            0.1                   0.1
```

- **RL Loss**: TD-error on Q-values (reward prediction)
- **Language Loss**: Cross-entropy on token prediction
- **Concept Loss**: MSE on composition value prediction (NEW!)

### Vocabulary Expansion

Cocoons can learn new words dynamically:

```python
# Add individual word
cocoon.add_word("synchronize", frequency=1)

# Learn from text
cocoon.learn_from_text("The organisms cooperate to achieve convergence")

# Add concept (category + associations)
cocoon.add_concept("emergence", category="dynamics", associations=["growth", "pattern"])
```

---

## 📦 Export Formats

The cocoon compiler supports multiple export formats:

| Format | Extension | Netron Viewable | Trainable | Description |
|--------|-----------|-----------------|-----------|-------------|
| **🦋 Cocoon** | `.py` | ❌ | ✅ | Single Python file with embedded weights |
| **ONNX** | `.onnx` | ✅ | ❌ | Open Neural Network Exchange format |
| **TorchScript** | `.pt` | ✅ | ❌ | PyTorch JIT compiled model |
| **StateDict** | `.pth` | ❌ | ✅* | Raw PyTorch weights |
| **📦 Package** | `.zip` | ✅ | ✅ | All formats + README + metadata |

*StateDict requires rebuilding the model architecture to use.

### View in Netron

1. Select **ONNX**, **TorchScript**, or **📦 Package** format
2. Download the file
3. Go to [https://netron.app/](https://netron.app/)
4. Drag & drop the `.onnx` or `.pt` file
5. Explore the neural network architecture!

---

## 🚀 Usage Modes

### 1. Info Mode (Default)
```bash
python cocoon.py --mode info
```
Shows organism metadata, vocabulary size, architecture info.

### 2. Chat Mode
```bash
python cocoon.py --mode chat
```
Interactive chat with the neural organisms. Learns from every interaction.

### 3. Gym Mode
```bash
python cocoon.py --mode gym --env CartPole-v1 --episodes 100 --render
```
Train/test in OpenAI Gym environments with visual rendering.

### 4. HTTP Server Mode
```bash
python cocoon.py --mode serve --port 8080
```

Endpoints:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/act` | POST | Get action from state vector |
| `/learn` | POST | Train on experience batch |
| `/chat` | POST | Send message, get response |
| `/teach` | POST | Explicitly teach new words |
| `/vocab` | GET | View current vocabulary |

### 5. Export Modes
```bash
# Export updated cocoon with learned state
python cocoon.py --export evolved_cocoon.py

# Export ONNX for Netron visualization
python cocoon.py --export-onnx brain.onnx

# Export full package (ONNX + README + metadata)
python cocoon.py --export-package ./my_model/
```
Export current state (with learned words) to new cocoon file.

---

## 🔧 CRA Control

The CRA can compile cocoons through the web UI or API:

### Web UI
1. Open Causation Explorer
2. Go to "Agent Exporter" tab
3. Select organisms (or leave blank for top N by fitness)
4. Click **🦋 Compile Cocoon (single-file)**
5. Download the `.py` file

### API Endpoint
```
POST /api/capsules/compile-cocoon
{
  "organism_ids": ["org_001", "org_002"],  // optional, uses live if blank
  "include_gym": true,
  "include_http": true,
  "compress": true
}
```

### CRA Command (Future)
```json
[[COCOON_COMPILE: {"organisms": "top_5", "output": "champion_swarm.py"}]]
```

---

## ⚙️ Configuration

Cocoons embed their configuration at compile time:

```python
# Architecture
hidden_dim = 64
num_heads = 4
num_axioms = 18
num_key_compositions = 32

# Training weights
rl_weight = 0.8
language_weight = 0.1
concept_weight = 0.1

# Vocabulary
vocab_size = 1000  # expandable
special_tokens = ['<PAD>', '<UNK>', '<START>', '<END>', '<VP_GATE>']
```

---

## 🧬 Capability Alignment with Butterfly

| Feature | Butterfly | Cocoon | Status |
|---------|-----------|--------|--------|
| VP-aware attention | ✅ | ✅ | Aligned |
| Multi-head self-attention | ✅ | ✅ | Aligned |
| Experience buffer | ✅ | ✅ | Aligned |
| RL loss (TD-error) | ✅ | ✅ | Aligned |
| Language loss (CE) | ✅ | ✅ | Aligned |
| Concept loss (MSE) | ✅ | ✅ | Aligned |
| ConceptHead | ✅ | ✅ | Aligned |
| Vocabulary expansion | ✅ | ✅ | Aligned |
| STEP 1-7 Pipeline | ✅ | ✅ | **NEW** - Aligned |
| Decision Matrix | ✅ | ✅ | **NEW** - Aligned |
| Semantic Boosting | ✅ | ✅ | **NEW** - Aligned |
| Fitness Weighting | ✅ | ✅ | **NEW** - Aligned |
| Knowledge Web Usage | ✅ | ✅ | **NEW** - Aligned |
| Response Aggregation | ✅ | ✅ | **NEW** - Aligned |
| Gym integration | ✅ | ✅ | Aligned |
| HTTP server | N/A | ✅ | Cocoon-specific |
| Self-export | N/A | ✅ | Cocoon-specific |
| Highlander battles | ✅ | ❌ | Post-selection |
| Alliance warfare | ✅ | ❌ | Post-selection |
| Causation events | ✅ | ✅ | **NEW** - Display only |
| Population dynamics | ✅ | ❌ | Post-selection |

### NEW: Full Intelligence Pipeline (2025-12-05)

The cocoon now implements Butterfly's complete STEP 1-7 tokenomic pipeline:

```
┌─── STEP 1: MESSAGE ───────────────────────────────────────┐
│ Input: hello world                                        │
└────────────────────────────────────────────────────────────┘
┌─── STEP 2: TOKENIZATION ────────────────────────────────────┐
│ Tokens: 2 │ IDs: [27, 45]                                   │
└────────────────────────────────────────────────────────────┘
┌─── STEP 3: SELECTION ───────────────────────────────────────┐
│ Strategy: FITNESS_WEIGHTED │ Organisms: 10                  │
└────────────────────────────────────────────────────────────┘
┌─── STEP 4: GENERATION ──────────────────────────────────────┐
│ [org_001] conf=0.650 fit=1.25 weight=0.812                  │
│   → greeting response from organism...                      │
│ [org_002] conf=0.540 fit=1.10 weight=0.594                  │
│   → another response...                                     │
└────────────────────────────────────────────────────────────┘
┌─── STEP 5: AGGREGATION ─────────────────────────────────────┐
│ Decision Matrix: weight = fitness × confidence              │
│ Winner: [org_001] weight=0.8125                             │
│ Runners-up:                                                 │
│   [org_003] weight=0.7890                                   │
│   [org_002] weight=0.5940                                   │
└────────────────────────────────────────────────────────────┘
┌─── STEP 6: CAUSATION ───────────────────────────────────────┐
│ Event: CHAT_RESPONSE │ Organisms: 10 │ Winner: org_001      │
└────────────────────────────────────────────────────────────┘
┌─── STEP 7: COMPLETE ────────────────────────────────────────┐
│ Final Response:                                             │
└────────────────────────────────────────────────────────────┘

🦋 Cocoon: <aggregated response>
```

### Decision Matrix Formula

The winner is selected by maximizing:

```python
weight = fitness × confidence
```

Where:
- **fitness** - Organism's proven fitness from Highlander/evolution
- **confidence** - Response confidence (diversity × token probability)

**Note:** Alliance warfare and Highlander battles are *selection mechanisms* - they determine WHICH organisms graduate to cocoons. Once exported, cocoons are champions that have already proven themselves.

---

## 🔬 Technical Implementation

### Compile Process (`AgentCompiler.compile_cocoon`)

1. **Extract organisms** from live session or capsules
2. **Serialize brain weights** to compressed base64
3. **Serialize vocabulary** and knowledge web
4. **Generate Python source** using `string.Template`
5. **Embed compressed data** as string constants
6. **Return single `.py` file**

### Key Files

- `reality_simulator/agent_compiler.py` - Compiler implementation
- `causation_web_ui.py` - API endpoint `/api/capsules/compile-cocoon`
- `templates/causation_explorer.html` - UI button

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `zlib.error: incorrect header check` | Compression mismatch | Regenerate cocoon |
| `Unexpected key in state_dict` | Architecture mismatch | Check ConceptHead inclusion |
| `action X invalid` | Action space size | Use `--env` to set environment |
| UNK spam in chat | Vocab filter missing | Regenerate (fixed 2025-12-05) |

---

## 📚 Related Documentation

- [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md) - Central documentation
- [CRA_CAPABILITIES.md](./CRA_CAPABILITIES.md) - CRA control reference
- [NEURAL_LEARNING_SYSTEM_EXPLAINED.md](./NEURAL_LEARNING_SYSTEM_EXPLAINED.md) - DQN architecture
- [CONFIG_REFERENCE.md](./CONFIG_REFERENCE.md) - Configuration options

---

## 🚀 Quick Start

```bash
# 1. Compile from web UI (recommended)
# Go to Causation Explorer → Agent Exporter → Compile Cocoon

# 2. Or via API
curl -X POST http://localhost:5001/api/capsules/compile-cocoon \
  -H "Content-Type: application/json" \
  -d '{"include_gym": true, "include_http": true}'

# 3. Run the cocoon
python cocoon_20251205_123456.py --mode chat
```
