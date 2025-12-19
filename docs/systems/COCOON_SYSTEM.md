# 🦋 COCOON SYSTEM - Single-File Deployable Agent

**Last Updated:** 2025-12-08

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

# Limit organisms to reduce VRAM usage (useful for large cocoons)
python cocoon.py --mode gym --max-organisms 10 --episodes 50
```
Train/test in OpenAI Gym environments with visual rendering.

**CLI Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--env` | CartPole-v1 | Gym environment name |
| `--episodes` | 10 | Number of episodes to run |
| `--max-organisms` | all | Limit organisms loaded (reduces VRAM) |
| `--render` | False | Show visual rendering |
| `--learn` | True | Enable online learning |

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
| STEP 1-7 Pipeline | ✅ | ✅ | Aligned |
| Decision Matrix | ✅ | ✅ | Aligned |
| Semantic Boosting | ✅ | ✅ | Aligned |
| Fitness Weighting | ✅ | ✅ | Aligned |
| Knowledge Web Usage | ✅ | ✅ | Aligned |
| Response Aggregation | ✅ | ✅ | Aligned |
| **Semantic Convergence** | ✅ | ✅ | **NEW** - Word embeddings exported |
| **Language Anchors** | ✅ | ✅ | **NEW** - Word-organism mappings |
| **Axiom Embeddings** | ✅ | ✅ | **NEW** - ConceptSystem grounding |
| Gym integration | ✅ | ✅ | Aligned |
| HTTP server | N/A | ✅ | Cocoon-specific |
| Self-export | N/A | ✅ | Cocoon-specific |
| Highlander battles | ✅ | ❌ | Post-selection |
| Alliance warfare | ✅ | ✅ | **NEW** - Exported state |
| Causation events | ✅ | ✅ | **NEW** - Full event history |
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

### Archive Contents (Package/Ensemble Export)

When exporting as `.zip` package, the archive contains:

| File | Description | NEW |
|------|-------------|-----|
| `brain.onnx` / `brain.pt` | Neural network model | |
| `metadata.json` | Export metadata, behavioral fingerprints | |
| `bridge_config.json` | Runtime configuration | |
| `atomic_language.json` | Merged language concepts from organisms | |
| `chat_vocabulary.json` | Tokenization vocabulary | |
| `conversation_history.json` | Training conversation data | |
| `semantic_convergence.json` | **Word embeddings, language anchors** | ✅ |
| `knowledge_web_full.json` | **Full semantic relationships (10k concepts)** | ✅ |
| `causation_system.json` | **Event history for exported organisms** | ✅ |
| `alliance_system.json` | **Social structures and reputation** | ✅ |
| `run_agent.py` | Runner script | |
| `requirements.txt` | Dependencies | |
| `README.md` | Documentation | |

### Semantic Convergence Export (NEW)

The `semantic_convergence.json` file contains:

```json
{
  "version": "1.0",
  "total_words": 500,
  "total_anchors": 1200,
  "embedding_dim": 64,
  "organism_embedding_alpha": 0.1,
  "language_anchors": {"word": ["org_id_1", "org_id_2"]},
  "node_word_associations": {"org_id": ["word1", "word2"]},
  "word_frequencies": {"word": 42},
  "word_embeddings_compressed": "<base64 compressed>"
}
```

This enables exported agents to maintain their **unique linguistic identity** - the same organism that learned specific words will respond with those words in the cocoon.

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

## 🎮 Tournament & Arena System (NEW)

Exported cocoons can battle each other for self-improvement:

### Proton Tournament
```python
from cocoon import CocoonAgent
from standalone_proton_tournament import ProtonTournament

agent = CocoonAgent()
tournament = ProtonTournament(agent)

# Different tournament formats
tournament.round_robin()              # All vs All
tournament.elimination()              # Single elimination bracket
tournament.ladder(total_battles=50)   # Continuous random pairings
```

### Swarm Pong Arena
```python
# Multi-agent elimination battle (polygon Pong)
tournament.swarm_pong_arena(lives=3, headless=True)

# Best-of-5 series
tournament.swarm_pong_series(rounds=5)
```

Features:
- **13 games** - CartPole, LunarLander, Taxi, Blackjack, Pong, Swarm Pong, etc.
- **Fitness transfer** - Winners absorb loser's fitness (Highlander-style)
- **Headless mode** - Training without display
- **Deterministic** - Seedable for reproducibility

---

## 🔗 Link Mode - P2P Networking (NEW)

Cocoons can connect to each other over the internet for battles, trades, and chat!

### Architecture

```
┌─────────────────┐         WebSocket         ┌─────────────────┐
│   COCOON A      │◄───────────────────────►│   COCOON B      │
│  (User Alice)   │                          │  (User Bob)     │
└────────┬────────┘                          └────────┬────────┘
         │         ┌──────────────────┐               │
         └────────►│  COCOON HATCH    │◄──────────────┘
                   │  (Relay Server)  │
                   │  ws://host:9000  │
                   └──────────────────┘
```

### Starting a Hatch Server

Anyone can host a hatch - it's a simple relay server:

```bash
# Start on default port 9000
python cocoon_hatch.py

# Custom port
python cocoon_hatch.py --port 8080

# Public (accessible from internet)
python cocoon_hatch.py --public
```

### Connecting Your Cocoon

```bash
# Connect to a hatch
python cocoon.py --mode link --hatch ws://server-ip:9000

# With custom display name
python cocoon.py --mode link --hatch ws://localhost:9000 --name "Champion Swarm"
```

### Link Mode Commands

Once connected:
| Command | Description |
|---------|-------------|
| `/users` | List online cocoons |
| `/challenge <name>` | Challenge a user to battle |
| `/accept <id>` | Accept a challenge |
| `/decline <id>` | Decline a challenge |
| `/chat <message>` | Send message to lobby |
| `/quit` | Disconnect |

### Battle Protocol

When two cocoons battle:
1. **10 rounds** of simultaneous action selection
2. Each organism picks: `move`, `cooperate`, `compete`, `rest`, `reproduce`, `isolate`
3. **Circular dominance** determines round winner
4. Final score determines overall winner
5. Stats tracked on both cocoons

### Requirements

```bash
pip install websockets
```

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
