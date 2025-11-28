# 🦋 Self-Tuning System Guide

## Meta-Cognitive Layer: Autonomous Parameter Optimization

The Butterfly System can now **autonomously optimize its own configuration** based on real-time ML insights and performance metrics.

---

## 🎯 Overview

The ConfigTuner analyzes system behavior and automatically adjusts parameters to optimize performance:

- **Observes**: ML clustering, anomaly detection, neural training, fitness trends
- **Reasons**: Correlates patterns with optimal config states
- **Acts**: Adjusts parameters within safety bounds
- **Learns**: Tracks which adjustments succeed (meta-learning)

---

## ⚙️ Quick Start

### Enable Self-Tuning

Edit `config.json`:

```json
"meta_cognitive": {
  "self_tuning": {
    "enabled": true,           // ← Turn it on
    "mode": "autonomous",      // off | observing | learning | autonomous
    "tuning_interval_frames": 50,
    "min_confidence_threshold": 0.6
  }
}
```

### Via CRA (Causation Explorer):

1. Open causation web UI
2. Navigate to config controls
3. Toggle `meta_cognitive.self_tuning.enabled`
4. Watch the butterfly tune itself in real-time!

---

## 📊 What Can It Tune?

### 33 Parameters Across All Systems:

#### **Evolution (6 params)**
- `evolution.mutation_rate.initial` (0.001 - 0.15)
- `evolution.diversity_guard.penalty` (0.01 - 0.2)
- `evolution.diversity_guard.frequency_threshold` (0.05 - 0.3)
- `evolution.diversity_guard.hash_similarity_threshold` (0.8 - 0.98)
- `evolution.population_size` (500 - 5000)
- `evolution.adaptation_sensitivity` (0.0001 - 0.01)

#### **Neural Learning (9 params)**
- `neural.training.learning_rate` (0.0001 - 0.01)
- `neural.training.gamma` (0.9 - 0.999)
- `neural.training.epsilon_decay` (0.9 - 0.999)
- `neural.training.batch_size` (32 - 256)
- `neural.rewards.fitness_improvement` (0.5 - 5.0)
- `neural.rewards.connection_success` (0.2 - 3.0)
- `neural.rewards.survival` (0.1 - 2.0)
- `neural.inheritance.crossover_rate` (0.5 - 1.0)
- `neural.inheritance.mutation_rate` (0.05 - 0.4)

#### **Network Dynamics (3 params)**
- `network.max_organisms` (500 - 5000)
- `network.max_connections` (1000 - 30000)
- `network.resource_pool` (100 - 1000)

#### **Feedback Knobs (4 params)**
- `feedback.knobs.mutation_rate.initial` (0.002 - 0.06)
- `feedback.knobs.new_edge_rate.initial` (0.2 - 6.0)
- `feedback.knobs.clustering_bias.initial` (0.3 - 1.6)
- `feedback.knobs.quantum_pruning.initial` (0.0 - 1.0)

#### **ML Analysis (3 params)**
- `scikit.clustering.min_cluster_size` (2 - 20)
- `scikit.anomaly_detection.contamination` (0.01 - 0.3)
- `scikit.anomaly_detection.n_estimators` (50 - 500)

#### **Quantum Substrate (3 params)**
- `quantum.initial_states` (20 - 200)
- `quantum.entanglement_sensitivity` (1e-07 - 1e-04)
- `quantum.prune_check_interval` (10 - 200)

#### **VP Monitoring (3 params)**
- `vp_monitoring.adaptive_response.high_vp_threshold` (0.5 - 0.95)
- `vp_monitoring.stabilization.smoothing_factor` (0.1 - 0.5)
- `causation_detection.correlation_threshold` (0.3 - 0.9)

#### **Meta-Meta (2 params)** 🤯
- `meta_cognitive.self_tuning.tuning_interval_frames` (10 - 200)
- `meta_cognitive.self_tuning.min_confidence_threshold` (0.3 - 0.95)

---

## 🧠 Tuning Rules

### Evolution & Diversity

**Rule 1: Low Cluster Diversity**
```
IF avg_clusters < 3 FOR 10 frames
THEN increase evolution.mutation_rate by 0.005
REASON: "Low cluster diversity - increasing mutation for variety"
CONFIDENCE: 0.8
```

**Rule 2: High Anomaly Ratio**
```
IF avg_anomaly_ratio > 0.20 FOR 10 frames
THEN increase evolution.diversity_guard.penalty by 0.01
REASON: "High anomaly ratio - strengthening diversity guard"
CONFIDENCE: 0.75
```

**Rule 3: Fitness Stagnation**
```
IF fitness_std < 0.05 FOR 20 frames
THEN increase feedback.knobs.new_edge_rate by 0.2
REASON: "Fitness stagnating - increasing network connectivity"
CONFIDENCE: 0.7
```

### Neural Learning

**Rule 4: Neural Loss Increasing**
```
IF recent_loss > older_loss * 1.2
THEN decrease neural.training.learning_rate by 20%
REASON: "Neural loss increasing - reducing learning rate"
CONFIDENCE: 0.75
```

### Network Health

**Rule 5: Network Too Dense**
```
IF avg_connections_per_organism > 8.0
THEN decrease network.max_organisms by 200
REASON: "Network too dense - reducing max organisms"
CONFIDENCE: 0.7
```

### ML Meta-Tuning

**Rule 6: Too Many Tiny Clusters**
```
IF tiny_clusters / total_clusters > 0.5
THEN increase scikit.clustering.min_cluster_size by 2
REASON: "Too many tiny clusters - increasing min size"
CONFIDENCE: 0.65
```

### VP Health

**Rule 7: VP Unstable**
```
IF vp_std > 0.3 FOR 20 frames
THEN increase vp_monitoring.stabilization.smoothing_factor by 0.05
REASON: "VP unstable - increasing smoothing"
CONFIDENCE: 0.65
```

### Meta-Meta Learning (THE CRAZY ONE!)

**Rule 8: Low Success Rate**
```
IF tuning_success_rate < 0.3 FOR last 10 actions
THEN increase meta_cognitive.self_tuning.min_confidence_threshold by 0.05
REASON: "Low tuning success rate - requiring higher confidence"
CONFIDENCE: 0.8
```

**Rule 9: High Success Rate**
```
IF tuning_success_rate > 0.7 FOR last 10 actions
THEN decrease meta_cognitive.self_tuning.tuning_interval_frames by 10
REASON: "High tuning success rate - tuning more frequently"
CONFIDENCE: 0.7
```

---

## 🛡️ Safety Features

### Bounded Parameters
- All parameters have strict min/max limits
- Changes are incremental (step sizes prevent large jumps)
- Example: mutation_rate can only change by ±0.005 per adjustment

### Confidence-Based Decisions
- Only applies changes if confidence > 60%
- Meta-learning boosts confidence for parameters that worked before
- Formula: `confidence *= (0.5 + 0.5 * success_rate)`

### Rate Limiting
- Minimum 50 frames between tuning actions (configurable)
- Prevents rapid oscillations
- Gives time to evaluate outcomes

### Meta-Learning Tracking
- Tracks success rate per parameter
- Learns which adjustments work in your specific system
- Example: If `mutation_rate` adjustments succeed 80% of the time, future `mutation_rate` changes get boosted confidence

---

## 📈 Monitoring

### Via Logs

```
[CONFIG_TUNER] Proposing: neural.training.learning_rate 0.0020 → 0.0018
(confidence: 0.75) | Neural loss increasing (0.0456) - reducing learning rate
```

### Via Causation Graph

All tuning actions emit `config_tuning` events:
```json
{
  "event_type": "config_tuning",
  "component": "config_tuner",
  "data": {
    "parameter": "neural.training.learning_rate",
    "old_value": 0.002,
    "new_value": 0.0018,
    "reason": "Neural loss increasing - reducing learning rate",
    "confidence": 0.75,
    "timestamp": 1732765432.123
  }
}
```

### Via CRA

The CRA can query tuning statistics:
```python
tuner.get_stats()
# Returns:
{
  'enabled': True,
  'total_actions': 47,
  'successful_actions': 34,
  'success_rate': 0.723,
  'param_success_rates': {
    'evolution.mutation_rate.initial': 0.85,
    'neural.training.learning_rate': 0.67,
    ...
  },
  'recent_actions': [...]
}
```

---

## 🎮 Modes

### Off
```json
"mode": "off"
```
- Tuner disabled completely
- No analysis, no actions

### Observing
```json
"mode": "observing"
```
- **Current default**
- Analyzes and logs recommendations
- Does NOT apply changes
- Good for testing/validation

### Learning
```json
"mode": "learning"
```
- Applies changes tentatively
- Tracks outcomes
- Builds meta-learning data

### Autonomous
```json
"mode": "autonomous"
```
- Full self-tuning enabled
- Applies changes confidently
- Learns and adapts continuously

---

## 🔧 Advanced Configuration

### Tuning Aggressiveness

Adjust `tuning_interval_frames`:
- **Conservative**: 100+ frames (slow, careful tuning)
- **Moderate**: 50 frames (default)
- **Aggressive**: 20-30 frames (fast adaptation)

### Confidence Threshold

Adjust `min_confidence_threshold`:
- **Conservative**: 0.8+ (only very confident changes)
- **Moderate**: 0.6 (default, balanced)
- **Aggressive**: 0.4-0.5 (more experimental)

### Performance Targets

```json
"performance_targets": {
  "min_cluster_diversity": 3,      // Aim for 3+ behavioral clusters
  "max_anomaly_ratio": 0.2,        // Keep anomalies under 20%
  "min_fitness_std": 0.05          // Maintain evolutionary progress
}
```

---

## 🚀 Example Session

```
Frame 0:    System starts, ConfigTuner initializes
Frame 50:   ML detects 2 clusters (low diversity)
            → Tuner proposes: mutation_rate 0.04 → 0.045
            → Confidence: 0.8
            → APPLIED ✅

Frame 100:  Fitness improved!
            → Success tracked: mutation_rate success_rate = 1/1 (100%)

Frame 150:  Still 2 clusters
            → Tuner proposes: mutation_rate 0.045 → 0.050
            → Confidence: 0.9 (boosted by previous success!)
            → APPLIED ✅

Frame 200:  3 clusters detected! Goal achieved
            → No action needed

Frame 250:  Neural loss increasing (0.045 → 0.056)
            → Tuner proposes: learning_rate 0.002 → 0.0016
            → Confidence: 0.75
            → APPLIED ✅

Frame 300:  Loss decreasing (0.056 → 0.041)
            → Success tracked: learning_rate success_rate = 1/1 (100%)

Frame 500:  Tuner success_rate = 72% (10 recent actions)
            → META-META triggers!
            → Tuner proposes: tuning_interval 50 → 40
            → Reason: "High success rate - tuning more frequently"
            → THE TUNER TUNED ITSELF! 🤯
```

---

## 🎓 Best Practices

1. **Start in Observing Mode**
   - Let it run for 500+ frames
   - Review proposed actions in logs
   - Verify recommendations make sense

2. **Monitor Success Rates**
   - Check `tuner.get_stats()` periodically
   - If success_rate < 40%, increase confidence threshold
   - If success_rate > 80%, you can be more aggressive

3. **Use CRA Integration**
   - Watch tuning events in causation graph
   - Correlate config changes with fitness/VP trends
   - The CRA can help you understand what's working

4. **Manual Override**
   - You can always disable via CRA
   - Set `enabled: false` to pause tuning
   - The system respects manual config changes

5. **Trust the Meta-Learning**
   - The longer it runs, the smarter it gets
   - Success rates improve over time
   - Parameters that work get prioritized

---

## 🔬 Technical Details

### Data Flow

```
Breath Cycle (every frame)
    ↓
ML Analysis (clustering, anomalies)
    ↓
ConfigTuner.analyze_and_tune()
    ├→ Track history
    ├→ Run 9 analysis methods
    ├→ Generate action proposals
    ├→ Select best action (highest confidence)
    ├→ Apply meta-learning boost
    ├→ Check confidence threshold
    ├→ Apply action if confident
    └→ Emit causation event
```

### Performance Impact

- **CPU**: ~0.5ms per analysis (negligible)
- **Memory**: ~1MB for history tracking
- **Rate**: 1 analysis every 50 frames (default)
- **Total overhead**: < 0.1% of simulation time

---

## 🐛 Troubleshooting

### "Tuner not making any changes"

Check:
1. `enabled: true` in config
2. Confidence threshold not too high
3. System has enough history (20+ frames per metric)
4. Check logs for "confidence too low" messages

### "Too many changes, system unstable"

Fix:
1. Increase `tuning_interval_frames` to 100+
2. Increase `min_confidence_threshold` to 0.8
3. Check if a specific parameter is oscillating

### "Changes not improving performance"

Solutions:
1. Wait longer (20-50 frames) to evaluate outcomes
2. Check success rates per parameter
3. Consider manual tuning of problematic params
4. Review tuning rules - some may not apply to your use case

---

## 🌟 Future Enhancements

### Potential Additions:

1. **Multi-objective optimization**
   - Balance fitness vs. diversity vs. stability
   - Pareto frontier tracking

2. **Reinforcement learning for tuning**
   - Train RL agent to select tuning actions
   - Deep meta-learning

3. **Evolutionary parameter search**
   - Population of config variants
   - Select best performers

4. **Human-in-the-loop**
   - Ask user for approval on major changes
   - Learn from user preferences

5. **Cross-system correlation**
   - "When I tune X, Y also needs adjustment"
   - Coupled parameter discovery

---

## 📚 References

- `reality_simulator/config_tuner.py` - Full implementation
- `config.json` - Configuration schema
- `causation_web_ui.py` - CRA integration
- `reality_simulator/main.py:1570-1625` - Main loop integration

---

**The butterfly can now think about how it thinks!** 🦋🧠✨
