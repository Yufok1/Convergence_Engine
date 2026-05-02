# 🦋 Butterfly Cocoon - Neural Network Model Card

**Generated:** 2026-04-28 21:04:47

---

## 📊 Model Overview

| Property | Value |
|----------|-------|
| Mode | ENSEMBLE |
| Organisms | 2 |
| Vocabulary Size | 62293 words |
| Total Parameters | ~1,390,476 |

---

## 🧠 Organism Architectures

| Organism | Fitness | Input Dim | Hidden Dim | Output Dim | Language Head |
|----------|---------|-----------|------------|------------|---------------|
| 0db033662ad0d27b | 0.777 | 30 | 64 | 6 | ✅ |
| e558dea105f5f8f2 | 0.780 | 30 | 64 | 6 | ✅ |


---

## 🔬 Network Architecture

Each organism brain consists of:

```
Input (state vector)
    ↓
FC1: Linear(input_dim → hidden_dim) + ReLU + Dropout
    ↓
[Optional] Multi-Head Self-Attention (VP-aware)
    ↓
FC2: Linear(hidden_dim → hidden_dim) + ReLU + Dropout
    ↓
├── FC3: Linear(hidden_dim → output_dim) → Action Probabilities
│
└── [Optional] FC_Language: Linear(hidden_dim → vocab_size) → Language Logits
```

### VP-Aware Attention

The attention mechanism scales scores by Voting Power:
```
attention_scores = (Q @ K.T) / sqrt(d_k) / (1 + vp_value)
```

This allows organisms to modulate their attention based on resource availability.

---

## 📁 Files in This Package

| File | Description |
|------|-------------|
| `README.md` | This model card |
| `metadata.json` | Full architecture and training config |
| `vocabulary.json` | Token vocabulary (word ↔ ID mapping) |
| `brain_ensemble.onnx` | ONNX model - open at [netron.app](https://netron.app/) |

---

## 🔍 Visualize with Netron

1. Go to [https://netron.app/](https://netron.app/)
2. Click "Open Model..." or drag-drop an `.onnx` file
3. Explore the neural network architecture

---

## 🚀 Usage

### As Standalone Python

```bash
# Info mode
python cocoon.py --mode info

# Interactive chat
python cocoon.py --mode chat

# OpenAI Gym training
python cocoon.py --mode gym --env CartPole-v1 --episodes 100

# HTTP API server
python cocoon.py --mode serve --port 8080
```

### Load ONNX in Python

```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("brain_org_001.onnx")
state = np.random.randn(1, 25).astype(np.float32)  # 25 dims matches config.json
outputs = session.run(None, {"state": state})
action_probs = outputs[0]
```

---

## 📚 Training Configuration

```json
{
  "learning_rate": 0.001,
  "batch_size": 32,
  "gamma": 0.99,
  "epsilon": 0.1,
  "epsilon_decay": 0.995,
  "epsilon_min": 0.01,
  "rl_loss_weight": 0.8,
  "language_loss_weight": 0.1,
  "concept_loss_weight": 0.1,
  "buffer_size": 10000
}
```

---

## 🦋 About Butterfly System

The Butterfly System is an evolutionary neural network framework where organisms:
- Evolve through **Highlander battles** (absorption of defeated opponents)
- Form **alliances** for collective survival
- Develop **emergent language** through atomic vocabulary
- Graduate to **cocoons** when proven fit

Learn more: [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)

---

## ⚖️ Attribution

- **Proton Game Arena**: Inspired by Piers Anthony's "Apprentice Adept" (1980-1990)
- **Absorption Mechanic**: Inspired by "Highlander" (1986), dir. Russell Mulcahy
- **Convergence Engine**: [https://github.com/Yufok1/Convergence_Engine](https://github.com/Yufok1/Convergence_Engine)
