# 🦋 Butterfly Cocoon

**Organism:** `{ORGANISM_ID}`  
**Fitness:** {FITNESS}  
**Generation:** {GENERATION}  
**Exported:** {EXPORT_DATE}

---

## 🚀 Quick Start

```bash
# View cocoon info
python cocoon.py --mode info

# Start chatting
python cocoon.py --mode chat

# Play games
python cocoon.py --mode gym --env CartPole-v1

# 3D sphere arena
python cocoon.py --mode sphere --train
```

---

## 📚 Complete Command Reference

### Mode Selection

| Mode | Command | Description |
|------|---------|-------------|
| **info** | `python cocoon.py --mode info` | Show organism metadata, vocabulary, architecture (default) |
| **chat** | `python cocoon.py --mode chat` | Interactive conversation with learning |
| **gym** | `python cocoon.py --mode gym` | Train/test in Gymnasium environments |
| **serve** | `python cocoon.py --mode serve` | HTTP API server |
| **sphere** | `python cocoon.py --mode sphere` | 3D Sphere Arena swarm defense |
| **link** | `python cocoon.py --mode link` | P2P networking for cocoon battles |

---

### 💬 Chat Mode

Interactive conversation with the neural organisms. Learns from every interaction.

```bash
python cocoon.py --mode chat
python cocoon.py --mode chat --verbose
```

**In-Chat Commands:**

| Command | Description |
|---------|-------------|
| `quit` | Exit chat mode |
| `export <file.py>` | Save current state to new cocoon file |

**Example Session:**
```
💬 You: Hello, how are you?
🦋 Cocoon: greeting response based on learned patterns
💬 You: export my_trained_cocoon.py
✅ Saved to my_trained_cocoon.py
```

---

### 🌐 Sphere Arena (3D Training)

Swarm defense game where organisms cooperate to catch falling balls.

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode sphere` | Play sphere defense |
| `python cocoon.py --mode sphere --train` | Play + learn from experience |
| `python cocoon.py --mode sphere --demo` | Preview with dummy AI |
| `python cocoon.py --mode sphere --headless` | Train without display |
| `python cocoon.py --mode sphere --balls 3 --train` | Multi-ball training |
| `python cocoon.py --mode sphere --misses 5 --train` | Harder difficulty |
| `python cocoon.py --mode sphere --headless --train` | Background training |
| `python cocoon.py --mode sphere --verbose` | Debug logging |

**Sphere Arena Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--balls N` | 1 | Number of balls (1-5) |
| `--misses N` | 10 | Max collective misses before game over |
| `--train` | off | Enable post-snapshot training |
| `--demo` | off | Run with dummy AI for preview |
| `--headless` | off | No display (training only) |
| `--verbose` | off | Verbose debug logging |

---

### 🎮 Gymnasium Environments

Train and test in OpenAI Gym / Gymnasium environments.

**Built-in Environments (always available):**

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env CartPole-v1` | Classic pole balancing (reflexes) |
| `python cocoon.py --mode gym --env MountainCar-v0` | Drive up hill (persistence) |
| `python cocoon.py --mode gym --env Acrobot-v1` | Double pendulum (coordination) |
| `python cocoon.py --mode gym --env FrozenLake-v1` | Navigate slippery ice (planning) |
| `python cocoon.py --mode gym --env CliffWalking-v1` | Don't fall off! (caution) |
| `python cocoon.py --mode gym --env Taxi-v3` | Pickup & delivery (efficiency) |
| `python cocoon.py --mode gym --env Blackjack-v1` | Beat the dealer (probability) |

**Box2D Environments (pip install gymnasium[box2d]):**

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env Pendulum-v1` | Torque control (precision) |
| `python cocoon.py --mode gym --env LunarLander-v3` | Spacecraft landing (piloting) |
| `python cocoon.py --mode gym --env BipedalWalker-v3` | Two-legged locomotion |
| `python cocoon.py --mode gym --env CarRacing-v3` | Drive the track |

**Atari Environments (pip install ale-py):**

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env ALE/Pong-v5` | Classic paddle game |
| `python cocoon.py --mode gym --env ALE/Breakout-v5` | Break the bricks |
| `python cocoon.py --mode gym --env ALE/SpaceInvaders-v5` | Defend Earth |
| `python cocoon.py --mode gym --env ALE/MsPacman-v5` | Maze chase |
| `python cocoon.py --mode gym --env ALE/Enduro-v5` | Racing endurance |

**MuJoCo Environments (pip install gymnasium[mujoco]):**

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env Ant-v4` | Quadruped locomotion |
| `python cocoon.py --mode gym --env HalfCheetah-v4` | Fast running |

**Gym Mode Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--env NAME` | CartPole-v1 | Gymnasium environment name |
| `--episodes N` | 100 | Number of episodes to run |
| `--render` | off | Show visual window |
| `--no-learn` | off | Disable online learning (inference only) |

**Example with all flags:**
```bash
python cocoon.py --mode gym --env LunarLander-v3 --episodes 50 --render
```

---

### 🌐 HTTP API Server

Run cocoon as a REST API server for external integration.

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode serve` | Start on default port 8080 |
| `python cocoon.py --mode serve --port 3000` | Custom port |

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/act` | Get action for state vector |
| `POST` | `/chat` | Chat endpoint |
| `POST` | `/reward` | Provide learning reward |
| `GET` | `/state` | Get agent internal state |
| `GET` | `/health` | Health check |

**Example Usage:**
```bash
# Start server
python cocoon.py --mode serve --port 8080

# Chat request
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!"}'

# Action request
curl -X POST http://localhost:8080/act \
  -H "Content-Type: application/json" \
  -d '{"state": [1,2,3,4]}'
```

---

### 🔗 Link Mode (P2P Networking)

Connect to other cocoons over the internet for battles and chat.

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode link` | Connect to default hatch (ws://localhost:9000) |
| `python cocoon.py --mode link --hatch ws://server:9000` | Connect to specific hatch server |
| `python cocoon.py --mode link --name "Champion"` | Connect with custom display name |

**Link Mode Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--hatch URL` | ws://localhost:9000 | CocoonHatch relay server URL |
| `--name NAME` | auto | Display name (defaults to first organism name) |

**In-Link Commands:**

| Command | Description |
|---------|-------------|
| `/users` | List online cocoons |
| `/challenge <name>` | Challenge a user to battle |
| `/accept <id>` | Accept a challenge |
| `/decline <id>` | Decline a challenge |
| `/chat <message>` | Send message to lobby |
| `/quit` | Disconnect |

**Requirements:** `pip install websockets`

---

### 🔬 Export & Conversion

Save evolved state or convert to different formats.

| Command | Description |
|---------|-------------|
| `python cocoon.py --export evolved.py` | Export updated cocoon with learned state |
| `python cocoon.py --export-onnx brain.onnx` | Export to ONNX format (all brains as ensemble) |
| `python cocoon.py --export-onnx brain.onnx --organism 0` | Export single organism to ONNX |
| `python cocoon.py --export-package ./my_model` | Export full package (ONNX + README + metadata) |
| `python cocoon.py --unpack ./output_dir` | Unpack ultimate package assets |
| `python cocoon.py --readme` | Print embedded README and exit |

**Export Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--export FILE` | - | Export cocoon Python file |
| `--export-onnx FILE` | - | Export ONNX model |
| `--export-package DIR` | - | Export full package (ONNX + README + metadata) |
| `--unpack DIR` | - | Unpack ultimate package assets |
| `--organism N` | 0 (all) | Organism index for single-brain ONNX export |
| `--readme` | - | Print embedded README and exit |

**ONNX Benefits:**
- 10-100x faster inference
- Works with ONNX Runtime (CPU/GPU)
- View architecture at [netron.app](https://netron.app/)

---

### ⚙️ Global Options

These flags work with any mode:

| Flag | Default | Description |
|------|---------|-------------|
| `--voting MODE` | confidence | Ensemble voting strategy: `majority`, `weighted`, `confidence` |
| `--max-organisms N` | all | Limit organisms loaded (saves VRAM) |
| `--verbose` / `-v` | off | Enable verbose debug logging |
| `--help` | - | Show all available options |

**Examples:**
```bash
# Load only 5 organisms to save VRAM
python cocoon.py --mode chat --max-organisms 5

# Use majority voting instead of confidence
python cocoon.py --mode gym --voting majority

# Verbose output for debugging
python cocoon.py --mode chat --verbose
```

---

### 🏟️ Tournament Mode (Gym Interactive Menu)

When running gym mode without specifying `--env`, an interactive menu appears:

```bash
python cocoon.py --mode gym
```

**Tournament Formats (for multi-organism cocoons):**

| Format | Description |
|--------|-------------|
| Round Robin | All organisms battle each other |
| Elimination | Single elimination bracket |
| Ladder | Continuous ranked matches |

---

## 🧠 About This Agent

This organism emerged from **The Butterfly System** - evolved through:
- 🧬 Genetic algorithms
- 🧠 Reinforcement learning (triple-loss: RL + Language + Concept)
- 🌐 Social evolution (Highlander battles, alliance warfare)
- 🎯 VP-aware attention (Violation Pressure self-governance)

**Architecture:**
- 28-dimensional self-perception state space
- Multi-head attention with VP gating
- Concept head with 18 axioms
- Atomic language per organism

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

*This organism lived, learned, and evolved. Now it continues in your hands.* 🦋
