# 🦋 ConfigTuner: Meta-Cognitive Self-Tuning System

## Overview

The **ConfigTuner** is the Butterfly System's meta-cognitive layer - it autonomously optimizes its own configuration parameters based on real-time ML insights, neural metrics, and system performance patterns.

**Core Philosophy**: The system learns to tune itself by observing population-level patterns and correlating them with optimal configuration states.

---

## 🧠 How It Works

### Observation Phase
The ConfigTuner observes:
- **ML Clustering**: Behavioral phenotype diversity (are organisms forming distinct groups?)
- **Anomaly Detection**: Population health (are there unusual organisms or system states?)
- **Neural Training**: Learning progress (are organisms learning? Is loss decreasing?)
- **Fitness Trends**: Evolution progress (is fitness improving over time?)
- **Network Health**: Connection density, resource availability
- **VP Stability**: Violation pressure oscillations
- **Language Quality**: Vocabulary size, semantic clustering quality (silhouette scores)

### Analysis Phase
The tuner runs **9 parallel analysis methods**:

1. **Cluster Diversity Analysis** (`_analyze_cluster_diversity`)
   - Low diversity (< 3 clusters) → Increase mutation rate
   - Creates more behavioral variety

2. **Anomaly Detection** (`_analyze_anomalies`)
   - High anomaly ratio (> 20%) → Adjust diversity guard or mutation
   - Identifies unhealthy population states

3. **Fitness Trends** (`_analyze_fitness_trends`)
   - Stagnant fitness → Increase adaptation sensitivity
   - Declining fitness → Adjust mutation/selection pressure

4. **Neural Learning** (`_analyze_neural_learning`)
   - Loss increasing → Decrease learning rate
   - Loss stable but high → Increase batch size or adjust rewards

5. **Network Health** (`_analyze_network_health`)
   - Too dense (> 8 conn/org) → Reduce max organisms
   - Too sparse → Increase connection formation

6. **ML Effectiveness** (`_analyze_ml_effectiveness`)
   - Too many tiny clusters → Increase min_cluster_size
   - **Meta-tuning**: Tunes the ML analyzer itself!

7. **Language Quality** (`_analyze_language_quality`) ⭐ NEW
   - Small vocabulary (< 30 words) → Increase language exploration
   - Fast convergence → Slow down semantic guidance
   - Low quality (silhouette < 0.3) → Relax quality thresholds

8. **VP Health** (`_analyze_vp_health`)
   - High VP variance (> 0.3 std) → Increase smoothing factor
   - Stabilizes system pressure

9. **Meta-Meta Learning** (`_analyze_meta_tuning_performance`) 🌀
   - Low success rate (< 30%) → Increase confidence threshold
   - High success rate (> 70%) → Decrease tuning interval
   - **The tuner tunes itself!**

### Action Selection
- All analysis methods propose `TuningAction` objects
- Each action has: parameter path, current value, proposed value, reason, confidence (0-1)
- **Best action selected**: Highest confidence wins
- **Meta-learning boost**: If parameter has worked before, confidence is boosted
- **Confidence threshold**: Only actions with confidence > 0.6 are applied

### Learning Phase
- Tracks success/failure of each tuning action
- Evaluates after 20 frames: Did fitness improve? Did clusters diversify?
- Updates `action_success_rates` dictionary: `param → (successes, total)`
- Future actions on same parameter get confidence boost based on historical success

---

## 🛡️ Regulation Mechanisms

### 1. **Safety Bounds** (Hard Limits)
Every tunable parameter has min/max bounds enforced:
```python
'evolution.mutation_rate.initial': (0.001, 0.15)  # Can't go below 0.001 or above 0.15
'neural.training.learning_rate': (0.0001, 0.01)   # Bounded for stability
```

**33 parameters** have safety bounds across:
- Evolution (6 params)
- Feedback knobs (4 params)
- Neural learning (9 params)
- Network dynamics (3 params)
- ML analysis (3 params)
- Quantum substrate (3 params)
- VP monitoring (3 params)
- Meta-cognitive (2 params - the tuner tunes itself!)

### 2. **Step Sizes** (Gradual Changes)
Changes are incremental, not drastic:
```python
'evolution.mutation_rate.initial': 0.005  # Only change by ±0.005 per adjustment
'neural.training.learning_rate': 0.0005   # Small steps prevent instability
```

### 3. **Confidence Threshold** (Quality Gate)
- Default: `min_confidence_threshold = 0.6`
- Only actions with confidence > 0.6 are applied
- Prevents low-quality adjustments
- **Self-adjusting**: If success rate is low, threshold increases (meta-meta learning)

### 4. **Tuning Interval** (Frequency Control)
- Default: `tuning_interval_frames = 50`
- Only considers tuning every 50 frames
- Prevents oscillation and gives changes time to take effect
- **Self-adjusting**: If success rate is high, interval decreases (tune more often)

### 5. **Meta-Learning** (Historical Success)
- Tracks which parameters have worked before
- Success rate: `successes / total` for each parameter
- Confidence boost: `confidence *= (0.5 + 0.5 * success_rate)`
- Parameters with 100% success get 1.0x confidence boost
- Parameters with 0% success get 0.5x confidence (still considered, but less likely)

### 6. **Mode Control** (Safety Levels)
Four modes in `config.json`:
- `off`: No tuning (disabled)
- `observing`: Analyzes but doesn't apply changes (safe mode for testing)
- `learning`: Applies changes and learns from outcomes
- `autonomous`: Full self-tuning enabled (default)

### 7. **Performance Targets** (Goal-Oriented)
```json
"performance_targets": {
  "max_anomaly_ratio": 0.2,      // Keep anomalies < 20%
  "min_cluster_diversity": 3,     // Maintain at least 3 distinct clusters
  "min_fitness_std": 0.05        // Ensure fitness variance (evolution happening)
}
```

### 8. **Safe Parameters List** (Whitelist)
Only parameters in `safe_parameters` list can be tuned:
- Prevents accidental tuning of critical system parameters
- 33 parameters currently whitelisted
- Can be extended via config

---

## 🔬 Current Implementation: Rule-Based Heuristics

### Strengths
✅ **Interpretable**: Clear if-then logic, easy to understand
✅ **Fast**: No model training, instant decisions
✅ **Safe**: Hard bounds prevent dangerous changes
✅ **Proven**: Works well for common scenarios

### Limitations
❌ **Rigid**: Fixed thresholds (e.g., "if clusters < 3, increase mutation")
❌ **No Context**: Doesn't consider parameter interactions
❌ **Simple Statistics**: Only uses averages and trends
❌ **No Prediction**: Can't predict optimal values, only adjusts incrementally
❌ **Manual Tuning**: Thresholds and step sizes are hand-coded

---

## 🚀 PyTorch & Scikit-Learn Enhancement Opportunities

### **Enhancement 1: Neural Parameter Predictor** (PyTorch)

**Concept**: Train a neural network to predict optimal parameter values based on system state.

**Architecture**:
```python
class ParameterPredictor(nn.Module):
    def __init__(self):
        # Input: System state vector (50+ features)
        # - ML metrics: cluster_count, anomaly_ratio, silhouette_score
        # - Neural metrics: training_loss, avg_epsilon, organisms_tracked
        # - Evolution metrics: best_fitness, fitness_std, population_size
        # - Network metrics: density, modularity, connection_count
        # - VP metrics: current_vp, vp_variance, vp_trend
        # - Language metrics: vocab_size, language_quality, word_fitness_correlation
        
        self.fc1 = nn.Linear(50, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 33)  # Output: 33 parameter adjustments
        
    def forward(self, state):
        # Predict optimal parameter values
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        adjustments = torch.sigmoid(self.fc3(x))  # 0-1 normalized
        return adjustments
```

**Training Data**:
- Collect: `(system_state, parameter_values, outcome_fitness)` tuples
- Outcome: Fitness after 20 frames
- Train: Supervised learning to predict parameters that maximize fitness

**Integration**:
```python
def _predict_optimal_parameters(self, ml_metrics, neural_metrics, ...):
    """Use neural network to predict optimal parameter values"""
    if self.parameter_predictor is None:
        return None  # Fallback to rule-based
    
    # Build state vector
    state = self._build_state_vector(ml_metrics, neural_metrics, ...)
    
    # Predict optimal values
    predicted = self.parameter_predictor(torch.FloatTensor(state))
    
    # Convert to TuningAction
    # Compare predicted vs current, propose changes
```

**Benefits**:
- Learns complex parameter interactions
- Predicts optimal values directly (not just increments)
- Adapts to system-specific patterns
- Can discover non-obvious parameter combinations

---

### **Enhancement 2: ML-Based Action Selector** (Scikit-Learn)

**Concept**: Use RandomForest/GradientBoosting to predict which tuning action will succeed.

**Features**:
```python
features = [
    'current_cluster_count',
    'anomaly_ratio',
    'neural_loss',
    'fitness_trend',
    'vp_variance',
    'vocab_size',
    'language_quality',
    'parameter_name',  # Categorical: which param to tune
    'current_value',
    'proposed_value',
    'confidence',
    'historical_success_rate'
]
```

**Target**: Binary classification - will this action succeed? (fitness improves)

**Integration**:
```python
def _select_best_action_ml(self, actions):
    """Use ML model to predict which action will succeed"""
    if self.action_selector is None:
        return max(actions, key=lambda a: a.confidence)  # Fallback
    
    # Predict success probability for each action
    for action in actions:
        features = self._extract_action_features(action)
        success_prob = self.action_selector.predict_proba([features])[0][1]
        action.confidence = success_prob  # Override with ML prediction
    
    # Select action with highest predicted success
    return max(actions, key=lambda a: a.confidence)
```

**Benefits**:
- Learns from historical tuning outcomes
- Considers parameter interactions
- More accurate than rule-based confidence
- Can identify patterns humans miss

---

### **Enhancement 3: Hybrid Approach** (Best of Both)

**Phase 1: Rule-Based** (Current)
- Use existing heuristics for initial tuning
- Collect training data: `(state, action, outcome)`

**Phase 2: ML Enhancement** (Scikit-Learn)
- Train RandomForest on collected data
- Use ML to predict action success
- Gradually replace rule-based confidence with ML predictions

**Phase 3: Neural Prediction** (PyTorch)
- Once enough data collected, train neural network
- Predict optimal parameter values directly
- Use neural predictions as primary, ML as fallback, rules as last resort

**Progressive Enhancement**:
```python
def analyze_and_tune(self, ...):
    actions = []
    
    # 1. Rule-based analysis (always runs)
    actions.extend(self._rule_based_analysis(...))
    
    # 2. ML-based action selection (if model trained)
    if self.action_selector and self.action_selector.is_trained():
        actions = self._ml_filter_actions(actions)
    
    # 3. Neural parameter prediction (if model trained)
    if self.parameter_predictor and self.parameter_predictor.is_trained():
        neural_actions = self._neural_predict_actions(...)
        actions.extend(neural_actions)
    
    # 4. Select best (hybrid confidence)
    best = self._select_best_hybrid(actions)
```

---

## 📊 Integration with Neural-ML Symbiosis

The three Neural-ML Symbiosis integrations can enhance autotune:

### **Integration 1: Neural Embeddings → Autotune State**
- Use neural semantic embeddings as features in state vector
- Clusters organisms by understanding, not just behavior
- Better state representation → better parameter predictions

### **Integration 2: ML Feature Importance → Autotune Priorities**
- ML identifies which system metrics predict success
- Autotune can prioritize tuning parameters that affect important metrics
- Example: If "vocabulary_size" is highly predictive, tune language params more aggressively

### **Integration 3: ML Quality Metrics → Autotune Curriculum**
- Use language quality (silhouette) to adjust autotune aggressiveness
- High quality → more aggressive tuning (system is stable)
- Low quality → conservative tuning (system needs stability)

---

## 🎯 Recommended Implementation Plan

### **Phase 1: Data Collection** (Week 1)
- Add logging: `(state, action, outcome)` tuples
- Store in `data/tuning_history.jsonl`
- Collect 1000+ examples before training

### **Phase 2: Scikit-Learn Action Selector** (Week 2)
- Train RandomForest on historical data
- Replace rule-based confidence with ML predictions
- A/B test: rule-based vs ML-based action selection

### **Phase 3: PyTorch Parameter Predictor** (Week 3)
- Train neural network to predict optimal parameters
- Use as primary method, ML as fallback
- Fine-tune on system-specific patterns

### **Phase 4: Hybrid System** (Week 4)
- Integrate all three: rules, ML, neural
- Progressive enhancement based on data availability
- Continuous learning: retrain models as more data accumulates

---

## 🔧 Configuration

Add to `config.json`:
```json
"meta_cognitive": {
  "self_tuning": {
    "enabled": true,
    "mode": "autonomous",
    "tuning_interval_frames": 50,
    "min_confidence_threshold": 0.6,
    
    "ml_enhancement": {
      "enabled": false,  // Enable ML-based action selection
      "model_path": "data/models/action_selector.pkl",
      "min_training_samples": 1000,
      "retrain_interval": 5000
    },
    
    "neural_enhancement": {
      "enabled": false,  // Enable neural parameter prediction
      "model_path": "data/models/parameter_predictor.pt",
      "min_training_samples": 5000,
      "retrain_interval": 10000
    },
    
    "hybrid_mode": "progressive"  // progressive | ml_primary | neural_primary | rules_only
  }
}
```

---

## 🎓 Research Potential

This would be the **first meta-learning system** that:
1. Uses neural networks to predict optimal hyperparameters
2. Uses ML to predict tuning action success
3. Learns from its own tuning history
4. Integrates with bidirectional neural-ML language learning

**Publication Venues**:
- NeurIPS (Meta-Learning track)
- ICML (AutoML track)
- AutoML Conference

---

## 💡 Summary

**Current State**: Rule-based heuristics with meta-learning (success rate tracking)

**Regulation**: 8 layers of safety (bounds, step sizes, confidence, intervals, meta-learning, modes, targets, whitelist)

**Enhancement Opportunity**: PyTorch + Scikit-Learn can make it:
- **Smarter**: Predict optimal values, not just adjust incrementally
- **More Accurate**: Learn from historical outcomes
- **More Adaptive**: Discover parameter interactions automatically
- **Self-Improving**: Continuously learns and gets better

**Integration**: Works seamlessly with Neural-ML Symbiosis - bidirectional learning enhances autotune, autotune optimizes the learning systems.

