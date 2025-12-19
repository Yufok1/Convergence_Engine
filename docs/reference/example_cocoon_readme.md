# 🦋 Butterfly Cocoon - Example README

**Organism:** `abc123def456`  
**Fitness:** 0.847  
**Generation:** 42  
**Exported:** 2025-12-11

---

## 🚀 Quick Start

### 🖱️ VS Code Click-to-Run (if viewing in VS Code)

> **Tip**: Click these links to run commands directly in your terminal!

| Action | Click to Run |
|--------|--------------|
| 💬 Chat Mode | [Start Chat](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--mode%20chat%5Cn%22%7D) |
| 🌐 Sphere Arena | [Play Sphere](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--mode%20sphere%5Cn%22%7D) |
| 🎓 Train in Sphere | [Train Mode](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--mode%20sphere%20--train%5Cn%22%7D) |
| 🎮 CartPole | [Play CartPole](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--mode%20gym%20--env%20CartPole-v1%20--episodes%20100%5Cn%22%7D) |
| 🌐 HTTP Server | [Start Server](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--mode%20serve%20--port%208080%5Cn%22%7D) |
| 🔬 Export ONNX | [Export Model](command:workbench.action.terminal.sendSequence?%7B%22text%22%3A%22python%20cocoon.py%20--export-onnx%20brain.onnx%5Cn%22%7D) |

---

## 📚 Command Compendium

<details>
<summary><b>💬 Chat & Interaction</b></summary>

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode chat` | Interactive conversation mode |
| `python cocoon.py --mode chat --verbose` | Chat with debug output |
| `python cocoon.py --mode infer --state "[1,2,3]"` | Single inference on state vector |

**Chat Commands (inside chat mode):**
| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/state` | Display agent internal state |
| `/vocab` | Show vocabulary statistics |
| `/quit` | Exit chat mode |

</details>

<details>
<summary><b>🌐 Sphere Arena (3D Training)</b></summary>

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode sphere` | Play sphere defense game |
| `python cocoon.py --mode sphere --train` | Play + learn from experience |
| `python cocoon.py --mode sphere --demo` | Preview with dummy AI |
| `python cocoon.py --mode sphere --headless` | Train without display |

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--balls N` | 1 | Number of balls (1-5) |
| `--misses N` | 10 | Max misses before game over |
| `--train` | off | Enable learning during play |
| `--demo` | off | Use dummy AI for preview |
| `--headless` | off | No display (training only) |
| `--verbose` | off | Debug logging |

**Example Combinations:**
```bash
python cocoon.py --mode sphere --balls 3 --train      # Multi-ball training
python cocoon.py --mode sphere --misses 5 --train     # Harder difficulty
python cocoon.py --mode sphere --headless --train     # Background training
```

</details>

<details>
<summary><b>🎮 Gymnasium Environments</b></summary>

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env CartPole-v1` | Classic pole balancing |
| `python cocoon.py --mode gym --env LunarLander-v3` | Moon landing |
| `python cocoon.py --mode gym --env MountainCar-v0` | Drive up hill |
| `python cocoon.py --mode gym --env Acrobot-v1` | Double pendulum |

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--env NAME` | CartPole-v1 | Gymnasium environment name |
| `--episodes N` | 10 | Number of episodes to run |
| `--render` | off | Show visual window |
| `--learn` | off | Online learning during play |

**Advanced Environments (require extra packages):**
```bash
# Atari (pip install ale-py)
python cocoon.py --mode gym --env ALE/Breakout-v5
python cocoon.py --mode gym --env ALE/Pong-v5

# Box2D (pip install gymnasium[box2d])
python cocoon.py --mode gym --env BipedalWalker-v3
python cocoon.py --mode gym --env CarRacing-v3

# MuJoCo (pip install gymnasium[mujoco])
python cocoon.py --mode gym --env Humanoid-v4
python cocoon.py --mode gym --env Ant-v4
```

</details>

<details>
<summary><b>🌐 HTTP API Server</b></summary>

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode serve` | Start on default port 8080 |
| `python cocoon.py --mode serve --port 3000` | Custom port |

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/act` | Get action for state/text |
| `POST` | `/chat` | Chat endpoint |
| `POST` | `/reward` | Provide learning reward |
| `GET` | `/state` | Get agent state |
| `GET` | `/health` | Health check |

**Example Usage:**
```bash
# Start server
python cocoon.py --mode serve --port 8080

# Query from another terminal
curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"text": "Hello!"}'
curl -X POST http://localhost:8080/act -H "Content-Type: application/json" -d '{"state": [1,2,3,4]}'
```

</details>

<details>
<summary><b>🔬 Export & Conversion</b></summary>

| Command | Description |
|---------|-------------|
| `python cocoon.py --export-onnx brain.onnx` | Export to ONNX format |
| `python cocoon.py --export-torchscript brain.pt` | Export to TorchScript |

**ONNX Benefits:**
- 10-100x faster inference
- Works with ONNX Runtime (CPU/GPU)
- Compatible with many deployment targets

**TorchScript Benefits:**
- Native PyTorch format
- Preserves training capability
- C++ deployment ready

**View Models:**
- Open `.onnx` files at [netron.app](https://netron.app/)

</details>

<details>
<summary><b>⚙️ Global Options</b></summary>

These flags work with any mode:

| Flag | Description |
|------|-------------|
| `--verbose` | Enable debug logging |
| `--help` | Show all available options |

</details>

---

## 🧠 About This Agent

This organism emerged from **The Butterfly System** - evolved through:
- 🧬 Genetic algorithms
- 🧠 Reinforcement learning  
- 🌐 Social evolution

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

*This organism lived, learned, and evolved. Now it continues in your hands.* 🦋
