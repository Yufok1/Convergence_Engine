# 🌐 CRA Guide: Monitoring Self-Tuning System

**For the Causation Relationship Analyzer (CRA)**

This guide explains how the CRA can monitor and interact with the Butterfly System's meta-cognitive self-tuning capabilities.

---

## 🎯 What is Self-Tuning?

The Butterfly System can **autonomously optimize its own configuration parameters** in real-time based on ML insights, neural performance, and evolutionary metrics.

**Key Points**:
- **33 tunable parameters** across Evolution, Neural, Network, ML, Quantum, VP, and Meta-Cognitive systems
- **9 intelligent tuning rules** analyze system behavior and propose parameter changes
- **Meta-meta learning**: The tuner tracks which adjustments work and improves over time
- **Meta-meta-meta**: The tuner can tune ITSELF (its own interval and confidence threshold)

---

## 📊 CRA Monitoring Capabilities

### 1. Real-Time Event Stream

The CRA receives **`config_tuning` events** whenever a parameter is adjusted:

```json
{
  "event_type": "config_tuning",
  "component": "config_tuner",
  "timestamp": 1732765432.123,
  "data": {
    "parameter": "neural.training.learning_rate",
    "old_value": 0.002,
    "new_value": 0.0018,
    "reason": "Neural loss increasing (0.0456) - reducing learning rate",
    "confidence": 0.75
  }
}
```

**How to use**:
- Watch the causation graph for `config_tuning` nodes appearing
- These nodes connect to related events (e.g., neural_training → config_tuning → neural_training)
- Trace causation chains: "What caused this tuning action?" and "What did this tuning action cause?"

---

### 2. Diagnostic Endpoint

**GET** `/api/cra/diagnostics/config_tuner`

Returns comprehensive self-tuning statistics:

```json
{
  "success": true,
  "config_tuner": {
    "enabled": true,
    "mode": "autonomous",
    "total_actions": 47,
    "successful_actions": 34,
    "success_rate": 0.723,
    "param_success_rates": {
      "evolution.mutation_rate.initial": 0.85,
      "neural.training.learning_rate": 0.67,
      "network.max_organisms": 0.71,
      "scikit.clustering.min_cluster_size": 0.60
    },
    "recent_actions": [
      {
        "param": "evolution.mutation_rate.initial",
        "change": "0.0400 → 0.0450",
        "reason": "Low cluster diversity - increasing mutation for variety",
        "success": true
      },
      {
        "param": "neural.training.learning_rate",
        "change": "0.0020 → 0.0018",
        "reason": "Neural loss increasing - reducing learning rate",
        "success": true
      }
    ],
    "tuning_interval_frames": 50,
    "min_confidence_threshold": 0.6,
    "source": "shared_state"
  }
}
```

**When to call**:
- Preflight diagnostics: Check if tuning is enabled and working
- Performance analysis: Evaluate tuning success rate
- Troubleshooting: Identify which parameters are struggling
- Post-mortem: Review what the tuner did during a run

---

### 3. Shared State Access

ConfigTuner status is available in `/api/cra/data` under `reality_sim.config_tuner`:

```json
{
  "reality_sim": {
    "config_tuner": {
      "enabled": true,
      "mode": "autonomous",
      "stats": { /* full stats object */ },
      "tuning_interval_frames": 50,
      "min_confidence_threshold": 0.6
    }
  }
}
```

---

## 🔍 What to Monitor

### Critical Metrics

1. **Success Rate** (`success_rate`)
   - **Healthy**: > 60%
   - **Warning**: 40-60% (tuner struggling, consider increasing confidence threshold)
   - **Critical**: < 40% (tuner not effective, manual intervention needed)

2. **Parameter Success Rates** (`param_success_rates`)
   - Identifies which parameters tune well vs. poorly
   - If a parameter has < 30% success rate, it may need manual tuning or different bounds

3. **Recent Actions** (`recent_actions`)
   - Shows last 10 tuning actions with success/failure
   - Look for patterns: repeated failures on same parameter = problem
   - High-frequency changes = tuner oscillating (increase interval or confidence)

4. **Mode** (`mode`)
   - `off`: No tuning happening
   - `observing`: Tuner analyzes but doesn't apply changes (safe mode)
   - `learning`: Tuner applies changes and learns from outcomes
   - `autonomous`: Full self-tuning enabled

---

## 🎮 CRA Control Capabilities

### Toggle Self-Tuning On/Off

**CONFIG_UPDATE** to enable/disable:

```
[[CONFIG_UPDATE: {
  "reason": "Disable autonomous tuning for testing",
  "correlation_id": "tuning-disable",
  "patch": [{
    "op": "replace",
    "path": "/meta_cognitive/self_tuning/enabled",
    "value": false
  }]
}]]
```

### Change Tuning Mode

```
[[CONFIG_UPDATE: {
  "reason": "Switch to observing mode",
  "correlation_id": "tuning-observe",
  "patch": [{
    "op": "replace",
    "path": "/meta_cognitive/self_tuning/mode",
    "value": "observing"
  }]
}]]
```

### Adjust Tuning Aggressiveness

**Increase interval** (tune less frequently):
```
[[CONFIG_UPDATE: {
  "reason": "Slow down tuning",
  "correlation_id": "tuning-slower",
  "patch": [{
    "op": "replace",
    "path": "/meta_cognitive/self_tuning/tuning_interval_frames",
    "value": 100
  }]
}]]
```

**Increase confidence threshold** (be more conservative):
```
[[CONFIG_UPDATE: {
  "reason": "Only tune with high confidence",
  "correlation_id": "tuning-conservative",
  "patch": [{
    "op": "replace",
    "path": "/meta_cognitive/self_tuning/min_confidence_threshold",
    "value": 0.8
  }]
}]]
```

---

## 📈 Analysis Workflows

### Preflight Diagnostics

**Before a simulation run**:

1. Call `/api/cra/diagnostics/config_tuner`
2. Check if `enabled: true` and `mode: autonomous`
3. Review `param_success_rates` from previous runs
4. Recommend parameter bounds adjustments if success rates < 40%

**Example CRA Output**:
```
ConfigTuner Status:
✅ Enabled: Yes (autonomous mode)
📊 Historical Success Rate: 72.3%
🎯 Top Performing Parameters:
   - evolution.mutation_rate.initial: 85% success
   - network.max_organisms: 71% success
⚠️ Struggling Parameters:
   - neural.training.learning_rate: 35% success (consider manual tuning)
```

---

### Real-Time Monitoring

**During a simulation run**:

1. Watch for `config_tuning` events in causation graph
2. Correlate tuning actions with metric changes:
   - Did `mutation_rate` increase lead to more clusters?
   - Did `learning_rate` decrease reduce neural loss?
3. Alert if tuner makes > 5 failed actions in a row
4. Alert if tuner starts oscillating (same parameter +/- rapidly)

**Example CRA Alert**:
```
⚠️ TUNING OSCILLATION DETECTED:
   - Parameter: neural.training.learning_rate
   - Actions: 0.002 → 0.0018 → 0.0022 → 0.0019 → 0.0021
   - Recommendation: Increase tuning_interval_frames to 100
```

---

### Post-Mortem Analysis

**After a simulation run**:

1. Call `/api/cra/diagnostics/config_tuner`
2. Review `recent_actions` to see what the tuner did
3. Correlate tuning actions with major events:
   - Did tuning prevent a collapse?
   - Did tuning accelerate fitness improvement?
4. Identify which parameters drove the most improvement
5. Generate recommendations for next run

**Example CRA Analysis**:
```
Post-Mortem: ConfigTuner Performance

Total Tuning Actions: 47
Success Rate: 72.3% (34/47 successful)

Key Interventions:
1. Frame 50: Increased mutation_rate → 3 clusters emerged ✅
2. Frame 100: Increased new_edge_rate → network connectivity improved ✅
3. Frame 200: Decreased learning_rate → neural loss stabilized ✅
4. Frame 350: Increased cluster_bias → no effect ❌

Recommendations for Next Run:
- cluster_bias adjustments not effective, consider excluding from tuning
- mutation_rate and new_edge_rate are high-value parameters
- Success rate is healthy, continue autonomous mode
```

---

## 🛠️ Troubleshooting Scenarios

### Scenario 1: Low Success Rate (< 40%)

**Symptoms**:
- `success_rate` < 0.4
- Many failed recent_actions

**CRA Diagnosis**:
1. Check if specific parameters are failing repeatedly
2. Call `/api/ml/analysis` to see if system is in unusual state
3. Check `/api/cra/diagnostics/vp_history` for volatility

**CRA Recommendation**:
```
Tuner success rate is low (35%). Recommend:
1. Increase min_confidence_threshold to 0.8 (be more conservative)
2. Increase tuning_interval_frames to 100 (give time to evaluate)
3. Consider disabling autonomous mode and switching to observing
```

---

### Scenario 2: Tuner Disabled But Should Be On

**Symptoms**:
- `enabled: false` but config shows `enabled: true`
- No config_tuning events appearing

**CRA Diagnosis**:
1. Check if ConfigTuner initialized properly (look for `[TUNER]` logs)
2. Check if there's an initialization error

**CRA Recommendation**:
```
ConfigTuner is configured to be enabled but is not active.
Check system.log for initialization errors.
Possible causes:
- config_tuner.py import failed
- Initialization exception during startup
```

---

### Scenario 3: Excessive Tuning (Oscillation)

**Symptoms**:
- Same parameter changing every 50 frames
- Values oscillating up/down

**CRA Diagnosis**:
1. Review recent_actions for oscillation pattern
2. Check if tuning_interval_frames is too low
3. Check if confidence_threshold is too low (accepting marginal changes)

**CRA Recommendation**:
```
Detected oscillation on parameter: neural.training.learning_rate
Actions: 0.002 → 0.0018 → 0.0022 → 0.0019 (4 changes in 200 frames)

Recommend:
1. Increase tuning_interval_frames from 50 to 150
2. Increase min_confidence_threshold from 0.6 to 0.75
3. This will force tuner to be more patient and confident
```

---

## 🧠 Understanding the 9 Tuning Rules

The CRA should understand what triggers each tuning rule to provide better diagnostics:

1. **Low Cluster Diversity** (avg_clusters < 3 for 10 frames)
   - **Action**: Increase `evolution.mutation_rate`
   - **Reason**: More mutation creates behavioral variety
   - **Confidence**: 0.8

2. **High Anomaly Ratio** (avg_anomaly_ratio > 0.20 for 10 frames)
   - **Action**: Increase `evolution.diversity_guard.penalty`
   - **Reason**: Strengthen diversity enforcement
   - **Confidence**: 0.75

3. **Fitness Stagnation** (fitness_std < 0.05 for 20 frames)
   - **Action**: Increase `feedback.knobs.new_edge_rate`
   - **Reason**: More connections = more evolutionary opportunity
   - **Confidence**: 0.7

4. **Neural Loss Increasing** (recent_loss > older_loss * 1.2)
   - **Action**: Decrease `neural.training.learning_rate` by 20%
   - **Reason**: Learning too fast, reduce step size
   - **Confidence**: 0.75

5. **Network Too Dense** (avg_connections_per_organism > 8.0)
   - **Action**: Decrease `network.max_organisms` by 200
   - **Reason**: Reduce network size to improve manageability
   - **Confidence**: 0.7

6. **Too Many Tiny Clusters** (tiny_clusters / total > 0.5)
   - **Action**: Increase `scikit.clustering.min_cluster_size` by 2
   - **Reason**: Force larger, more meaningful clusters
   - **Confidence**: 0.65

7. **VP Unstable** (vp_std > 0.3 for 20 frames)
   - **Action**: Increase `vp_monitoring.stabilization.smoothing_factor`
   - **Reason**: Smooth VP volatility
   - **Confidence**: 0.65

8. **Low Tuning Success Rate** (success_rate < 0.3 for last 10 actions)
   - **Action**: Increase `meta_cognitive.self_tuning.min_confidence_threshold`
   - **Reason**: Be more selective about tuning
   - **Confidence**: 0.8
   - **Meta-Meta**: The tuner tuning itself!

9. **High Tuning Success Rate** (success_rate > 0.7 for last 10 actions)
   - **Action**: Decrease `meta_cognitive.self_tuning.tuning_interval_frames`
   - **Reason**: Tune more frequently since it's working
   - **Confidence**: 0.7
   - **Meta-Meta**: The tuner tuning itself!

---

## 📋 CRA Checklist

When analyzing self-tuning:

- [ ] Check `/api/cra/diagnostics/config_tuner` for status
- [ ] Verify `enabled` matches config.json setting
- [ ] Review `success_rate` (healthy > 60%)
- [ ] Identify struggling parameters (`param_success_rates` < 40%)
- [ ] Check `recent_actions` for patterns (oscillation, repeated failures)
- [ ] Correlate `config_tuning` events with metric changes in graph
- [ ] Verify tuning actions improved metrics (fitness, clusters, loss)
- [ ] Alert user if success_rate < 40% or oscillation detected
- [ ] Recommend parameter bound adjustments based on failure patterns
- [ ] Suggest mode changes (autonomous → observing) if tuning unstable

---

## 🎓 Best Practices for CRA

1. **Proactive Monitoring**
   - Call config_tuner diagnostic during preflight checks
   - Alert user if tuning is misconfigured before simulation starts

2. **Pattern Recognition**
   - Detect oscillations (same param changing repeatedly)
   - Detect cascading failures (tuning causing more problems)
   - Detect meta-meta events (tuner tuning itself)

3. **Context-Aware Recommendations**
   - If VP is high and tuner struggling → recommend manual intervention
   - If fitness improving and tuner succeeding → encourage autonomous mode
   - If oscillation detected → increase interval and confidence

4. **Causation Analysis**
   - Link config_tuning events to outcome events
   - Show user: "This tuning action led to 3 new clusters emerging"
   - Identify which tuning rules are most effective in this system

5. **Educational**
   - Explain what each tuning action means
   - Reference SELF_TUNING_GUIDE.md for details
   - Help user understand meta-cognitive capabilities

---

## 🔗 Related Resources

- **Full Self-Tuning Guide**: [SELF_TUNING_GUIDE.md](./SELF_TUNING_GUIDE.md)
- **Config Schema**: [config.json](./config.json) - See `meta_cognitive.self_tuning` section
- **Implementation**: [reality_simulator/config_tuner.py](./reality_simulator/config_tuner.py)
- **Integration**: [reality_simulator/main.py](./reality_simulator/main.py) lines 1021-1625

---

**The CRA is now fully aware of the Butterfly's meta-cognitive self-tuning capabilities!** 🌐🦋🧠
