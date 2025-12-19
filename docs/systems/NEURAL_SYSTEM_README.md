# 🧠 Neural System - Quick Reference

**PyTorch-based neural networks for organisms in the Reality Simulator**

---

## 🚀 Quick Start

### Enable Neural System

Edit `config.json`:

```json
{
  "neural": {
    "enabled": true,
    "device": "cpu",
    "brain": {
      "input_dim": 12,
      "hidden_dim": 64,
      "output_dim": 6
    },
    "training": {
      "enabled": true,
      "batch_size": 32,
      "learning_rate": 0.001,
      "epsilon_start": 1.0,
      "epsilon_end": 0.01
    }
  }
}
```

### Install PyTorch (Optional)

```bash
# CPU only
pip install torch>=2.0.0

# With CUDA support (if you have GPU)
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu118
```

**Note:** System works without PyTorch (creates standard organisms). Neural features are optional.

---

## 📖 Documentation

- **[NEURAL_LEARNING_SYSTEM_EXPLAINED.md](./NEURAL_LEARNING_SYSTEM_EXPLAINED.md)** - Complete architecture explanation
- **[NEURAL_INTEGRATION_COMPLETE.md](./NEURAL_INTEGRATION_COMPLETE.md)** - Integration details
- **[CRA_NEURAL_UPGRADE_COMPLETE.md](./CRA_NEURAL_UPGRADE_COMPLETE.md)** - CRA awareness

---

## 🏗️ Architecture

### Components

- **OrganismBrain** (`brain.py`): PyTorch neural network (Input → Hidden → Attention → Hopfield → Output)
- **HopfieldLayer** (`brain.py`): Modern continuous Hopfield network for iterative thought refinement ⭐ NEW
- **NeuralOrganism** (`neural_organism.py`): Organism with brain for decision-making
- **NeuralTrainer** (`trainer.py`): DQN training with experience replay
- **ExperienceBuffer** (`experience.py`): Stores (state, action, reward, next_state) experiences

### How It Works

1. **Decision Making**: Organisms use brain to choose actions (move, cooperate, compete, etc.)
2. **Thought Refinement**: Optional Hopfield layer iteratively refines hidden states before output ⭐ NEW
3. **Experience Collection**: Actions and outcomes stored in experience buffer
4. **Training**: DQN learns optimal policies from experiences (synchronized with breath cycles)
5. **Inheritance**: Learned neural weights passed to offspring (Lamarckian evolution)

---

## ⚙️ Configuration

See `config.json` → `neural` section for all parameters:

- **Brain Architecture**: `input_dim`, `hidden_dim`, `output_dim`, `activation`, `dropout`
- **Training**: `batch_size`, `learning_rate`, `gamma`, `epsilon_*`, `update_frequency`
- **Rewards**: `fitness_improvement`, `survival`, `connection_success/failure`, `resource_gain/loss`
- **Inheritance**: `mutation_rate`, `crossover_rate` for brain weights
- **Checkpointing**: `enabled`, `auto_save_interval_*`, `max_checkpoints`, `auto_resume`

---

## 💾 Checkpointing

Training state is automatically saved and can be restored:

```json
{
  "neural": {
    "checkpointing": {
      "enabled": true,
      "auto_save_interval_generations": 100,
      "auto_save_interval_minutes": 10,
      "max_checkpoints": 5,
      "auto_resume": true
    }
  }
}
```

**Features:**
- **Auto-save** by generation count or time interval
- **Rotation** keeps last N checkpoints
- **Auto-resume** loads latest checkpoint on startup
- **Graceful shutdown** saves checkpoint on Ctrl+C

**API Endpoints:**
- `POST /api/checkpoint/save` - Force immediate save
- `POST /api/checkpoint/restore` - Restore from checkpoint
- `GET /api/checkpoint/list` - List all checkpoints

---

## 🧪 Testing

```bash
# Run neural integration tests
python -m pytest tests/test_neural_integration.py -v
```

All 7 tests passing ✅

---

## 📊 Visualization

Neural events appear in Causation Explorer:

- **Electric Blue Diamonds** = Neural decisions (high confidence)
- **Neon Purple Squares** = Training events
- **Dashed, pulsing links** = Neural thought connections

---

## 🤖 CRA Control

The Convergence Research Assistant can:

- Monitor training loss and epsilon
- Adjust all neural parameters via `CONFIG_UPDATE`
- Analyze decision patterns
- Control neural visualization colors

Example: "Enable neural system and set learning rate to 0.002"

---

## 🔧 Troubleshooting

**Q: Training loss is high (>1.0)**
- A: Normal during early training. Should decrease over time.

**Q: Training loss is NaN**
- A: Fixed in 2025-12-09 update. Language logits had extreme values causing overflow. Now uses temperature scaling and NaN guards. Update to latest version.

**Q: Organisms not learning**
- A: Check `epsilon` - if too high, they're exploring too much. Check reward weights.

**Q: PyTorch not found**
- A: System falls back to standard organisms. Install PyTorch to enable neural features.

**Q: CUDA out of memory**
- A: Reduce `batch_size` or `memory_size`, or use `"device": "cpu"`

**Q: Dimension mismatch errors**
- A: Fixed in 2025-12-09 update. Model dimensions now read dynamically from `brain.input_dim`. Observations are padded/truncated automatically.

---

## 📝 Key Concepts

- **DQN**: Deep Q-Network - learns action values (Q-values) from experiences
- **Experience Replay**: Random batch sampling breaks correlation, stabilizes learning
- **Epsilon-Greedy**: Balances exploration (random) vs exploitation (learned policy)
- **Dual Inheritance**: Organisms inherit both genetic code AND learned neural weights
- **Breath Synchronization**: Training happens during breath "inhale" phase

---

**For complete details, see [NEURAL_LEARNING_SYSTEM_EXPLAINED.md](./NEURAL_LEARNING_SYSTEM_EXPLAINED.md)**

