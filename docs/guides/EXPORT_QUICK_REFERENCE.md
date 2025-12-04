# 🚀 Agent Export & Deployment - Quick Reference

**Status:** Production-ready export infrastructure
**Version:** 2.0 (AgentBridge Universal Interface)

---

## 📦 Export Formats

### Solo Organism Export

```python
from reality_simulator.agent_compiler import AgentCompiler
from reality_simulator.checkpointing.organism_capsule import OrganismCapsule

compiler = AgentCompiler()

# Export single organism
archive = compiler.compile_capsule_to_agent(
    capsule=my_organism_capsule,
    export_format='onnx',  # 'onnx', 'torchscript', 'statedict'
    include_history=True
)

# Save to file
with open('my_agent.zip', 'wb') as f:
    f.write(archive.getvalue())
```

**Output Structure:**
```
my_agent.zip/
├── brain.onnx              # Neural network (or brain.pt for TorchScript)
├── metadata.json           # Rich metadata + behavioral fingerprint
├── agent_state.json        # Agent state for AgentRuntime
├── runner.py               # Standalone Python runner script
└── portable_agent/         # Self-contained runtime library
    ├── agent_runtime.py
    ├── bridge.py
    ├── mini_environment.py
    └── ...
```

---

### Ensemble Export (Multi-Organism)

```python
# Export multiple organisms as voting ensemble
archive = compiler.compile_capsules_to_ensemble(
    capsules=[capsule1, capsule2, capsule3],
    export_format='onnx'
)
```

**Ensemble includes:**
- All organism brains in single model
- Fitness weights for voting
- Organism IDs and metadata
- Automatic voting strategy selection

---

## 🌉 AgentBridge - Universal Deployment Interface

### Load Exported Agent

```python
from reality_simulator.portable_agent.bridge import AgentBridge

# Load from exported directory
bridge = AgentBridge.load("./path/to/exported_agent")
```

---

### Mode 1: Gym Environment Runner

```python
# Run in OpenAI Gym/Gymnasium environment
bridge.run_gym(
    env_name="CartPole-v1",
    episodes=100,
    render=True,
    save_video=True
)
```

**Use case:** RL benchmarking, competition submission, testing

---

### Mode 2: HTTP/REST API Server

```python
# Start HTTP server for external applications
bridge.serve(
    port=8080,
    host='0.0.0.0',
    debug=False
)
```

**API Endpoints:**
- `POST /predict` - Get action from state
- `POST /process` - Process text + context
- `GET /status` - Agent health check
- `GET /metadata` - Agent metadata

**Example request:**
```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Enemy approaching from north",
    "context": {"threat_level": 0.8, "energy": 0.3}
  }'
```

**Response:**
```json
{
  "action": 5,
  "action_name": "isolate",
  "response": "Taking defensive position",
  "confidence": 0.87,
  "q_values": [0.2, 0.3, 0.1, 0.4, 0.2, 0.9],
  "state_vector": [...]
}
```

---

### Mode 3: Interactive CLI

```python
# Interactive chat + environment hybrid
bridge.interactive()
```

**Use case:** Manual testing, debugging, demos

---

### Mode 4: Direct Python Integration

```python
# Programmatic access for custom applications
result = bridge.process(
    text="Threat detected",
    context={
        'threat_level': 0.8,
        'energy': 0.5,
        'allies_nearby': 2
    }
)

print(f"Action: {result.action_name}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Q-values: {result.q_values}")

# Access internal state
print(f"Agent memory: {bridge.get_memory_summary()}")
print(f"Learning stats: {bridge.get_learning_stats()}")
```

**Use case:** Custom workflows, scientific experiments, production systems

---

## 🗳️ Ensemble Voting Strategies

When using ensemble exports, configure voting behavior:

```python
from reality_simulator.portable_agent.bridge import AgentConfig, EnsembleVotingStrategy

config = AgentConfig(
    is_ensemble=True,
    member_count=5,
    voting_strategy='fitness_weighted',  # See options below
    top_k_voters=3,  # For fittest_top_k strategy
    adaptive_strategy=True  # Auto-select best strategy
)

bridge = AgentBridge.load("./ensemble_export", config=config)
```

### Available Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `single` | Use first organism only | Debugging |
| `majority` | Democratic vote (1 organism = 1 vote) | Balanced collectives |
| `fitness_weighted` ⭐ | Weight votes by fitness | Production (default) |
| `softmax_ensemble` | Softmax aggregate Q-values | Maximum confidence |
| `confidence_weighted` | Weight by decision confidence | Uncertain environments |
| `fittest_top_k` | Only top K fittest vote | Elitism |
| `adaptive` | Auto-select per situation | Dynamic environments |

---

## 📊 Behavioral Fingerprinting

Every export includes automatic behavioral analysis:

```python
# Access from metadata.json after export
import json

with open('my_agent/metadata.json') as f:
    metadata = json.load(f)

fingerprint = metadata['behavioral_fingerprint']

print(f"Personality: {fingerprint['personality_label']}")
# Output: "diplomat" or "altruist" or "aggressor" etc.

print(f"Dominant action: {fingerprint['dominant_action']}")
# Output: "cooperate" (45.3% of decisions)

print(f"Tendencies:")
print(f"  Cooperative: {fingerprint['behavioral_tendencies']['cooperative']}")
print(f"  Competitive: {fingerprint['behavioral_tendencies']['competitive']}")
print(f"  Passive: {fingerprint['behavioral_tendencies']['passive']}")

print(f"Scenario responses:")
print(f"  Low energy: {fingerprint['scenario_responses']['low_energy']}")
print(f"  High threat: {fingerprint['scenario_responses']['high_threat']}")
print(f"  Social opportunity: {fingerprint['scenario_responses']['social_opportunity']}")
```

**Personality Archetypes:**
- `altruist` - Strongly cooperative
- `diplomat` - Cooperative but will compete if needed
- `opportunist` - Competitive but will cooperate strategically
- `aggressor` - Strongly competitive
- `cautious` - Prefers passive/defensive actions
- `balanced` - No dominant tendency

---

## 🔧 Advanced Configuration

### Language Head (if enabled)

```python
# When organism has language capabilities
result = bridge.process(
    text="What should we do?",
    context={'energy': 0.7}
)

# Access language output
print(result.response)  # Generated text response
print(result.metadata['language_tokens'])  # Token-level output
```

### Continued Learning

```python
# Enable online learning after deployment
bridge.enable_learning(
    learning_rate=0.0001,
    target_update_freq=100
)

# After interaction
reward = compute_reward(result, outcome)
bridge.learn_from_experience(
    state=state_vector,
    action=result.action,
    reward=reward,
    next_state=next_state_vector,
    done=is_terminal
)
```

### Memory Management

```python
# Access episodic memory
memory = bridge.get_memory_summary()
print(f"Memory entries: {memory['entry_count']}")
print(f"Recent experiences: {memory['recent_traces']}")

# Clear memory
bridge.reset_memory()
```

---

## 🧪 Testing & Verification

### Run Complete Test Suite

```bash
cd Convergence_Engine
python test_export_pipeline.py
```

**Tests:**
1. ✅ Solo export (ONNX)
2. ✅ Solo export (TorchScript)
3. ✅ Ensemble export
4. ✅ AgentBridge Python integration
5. ✅ Behavioral fingerprinting
6. ✅ Export format fallback
7. ✅ Ensemble voting strategies
8. ✅ Language head export

---

## 📁 File Locations

```
Convergence_Engine/
├── reality_simulator/
│   ├── agent_compiler.py           # Main export compiler
│   ├── portable_agent/             # Deployable runtime
│   │   ├── __init__.py
│   │   ├── agent_runtime.py        # Core agent logic
│   │   ├── bridge.py               # Universal interface
│   │   ├── mini_environment.py     # Test environment
│   │   ├── gym_adapter.py          # Gym integration
│   │   ├── perception.py           # State processing
│   │   ├── training.py             # Online learning
│   │   └── visualize.py            # Visualization tool
│   └── checkpointing/
│       └── organism_capsule.py     # Capsule serialization
├── test_export_pipeline.py         # Comprehensive test suite
└── EXPORT_QUICK_REFERENCE.md       # This guide
```

---

## 🚨 Troubleshooting

### Issue: ONNX export fails

**Solution:** Automatic fallback to TorchScript
- The compiler gracefully falls back if ONNX export fails
- Check logs for "Falling back to TorchScript" message
- Ensure `onnx` and `onnxruntime` packages installed:
  ```bash
  pip install onnx onnxruntime
  ```

### Issue: AgentBridge can't load exported agent

**Solution:** Verify export structure
```python
import zipfile

with zipfile.ZipFile('my_agent.zip') as zf:
    print(zf.namelist())  # Should contain brain.onnx, metadata.json, etc.
```

### Issue: Ensemble voting not working as expected

**Solution:** Check member fitness weights
```python
# Verify fitness values are set
for capsule in capsules:
    print(f"{capsule.organism_id}: fitness={capsule.fitness}")

# If all fitness values are similar, consider different strategy
config.voting_strategy = 'majority'  # Equal weight voting
```

### Issue: Language head not exporting

**Solution:** Verify language head is enabled in organism brain
```python
# Check organism brain configuration
print(f"Language head enabled: {organism.brain.use_language_head}")
print(f"Vocab size: {organism.brain.vocab_size}")
```

---

## 📚 See Also

- [DEEP_DIVE_ANALYSIS.md](DEEP_DIVE_ANALYSIS.md) - Complete system architecture
- [NEURAL_LEARNING_SYSTEM_EXPLAINED.md](NEURAL_LEARNING_SYSTEM_EXPLAINED.md) - Neural system details
- [README.md](README.md) - Project overview

---

## 🎯 Real-World Deployment Examples

### Example 1: Deploy to Web Service

```python
# Export agent
compiler = AgentCompiler()
archive = compiler.compile_capsule_to_agent(capsule, export_format='onnx')

# Extract to deployment directory
import zipfile
with zipfile.ZipFile(BytesIO(archive.getvalue())) as zf:
    zf.extractall('/opt/my_service/agent')

# Start HTTP server (in production script)
from portable_agent import AgentBridge
bridge = AgentBridge.load('/opt/my_service/agent')
bridge.serve(port=8080, host='0.0.0.0')
```

### Example 2: Gym Competition Submission

```python
# Export for RL competition
bridge = AgentBridge.load('./my_champion_agent')

# Test on target environment
results = bridge.run_gym(
    env_name='LunarLander-v2',
    episodes=100,
    save_video=True,
    video_dir='./submission_videos'
)

print(f"Average reward: {results['avg_reward']:.2f}")
```

### Example 3: Multi-Agent System with Ensemble

```python
# Deploy ensemble as coordination layer
ensemble_bridge = AgentBridge.load('./my_ensemble')

# Use in multi-agent loop
for step in range(1000):
    # Aggregate observations from multiple agents
    state = aggregate_agent_states(agents)

    # Ensemble decides
    decision = ensemble_bridge.process(context=state)

    # Broadcast action to all agents
    broadcast_action(agents, decision.action_name)
```

---

**Last Updated:** December 2024
**Maintainer:** Convergence Engine Team
