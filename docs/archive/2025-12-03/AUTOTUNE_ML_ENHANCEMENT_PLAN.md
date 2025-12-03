# Autotune ML Enhancement - Refined Implementation Plan

## Core Principle: Occam's Razor
**Keep it simple, but maintain necessary complexity for interactions.**

The system already tracks tuning outcomes. We just need to:
1. **Persist** the data (already collecting)
2. **Learn** from it (scikit-learn, simple)
3. **Use** it to improve decisions (boost confidence scores)

---

## Strategic Focus: Action Selection Niche

**Why Action Selection (not Parameter Prediction)?**
- ✅ Simpler: Binary classification (will this action succeed?) vs regression (what's optimal value?)
- ✅ Works with less data: 100+ samples vs 5000+ for neural predictor
- ✅ Immediate value: Better action selection = higher success rate
- ✅ Lower risk: Falls back to rules if ML fails
- ✅ Validates easily: Compare ML-boosted vs rule-based success rates

**Deferred: Neural Parameter Predictor**
- Needs 5000+ samples (collect over time)
- More complex (neural network training)
- Can add later once we have data

---

## Implementation: 3 Phases

### Phase 1: Data Persistence (Week 1)
**Goal**: Persist tuning history so we can train on it

**Changes to `reality_simulator/config_tuner.py`:**

1. Add imports (top of file):
```python
import json
import os
from pathlib import Path

# Optional scikit-learn
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None
```

2. Add data directory path (in `__init__`):
```python
# Data persistence for ML training
self.data_dir = Path("data")
self.tuning_history_file = self.data_dir / "tuning_history.jsonl"
self.models_dir = self.data_dir / "models"
self.models_dir.mkdir(parents=True, exist_ok=True)
```

3. Add `_save_tuning_history()` method:
```python
def _save_tuning_history(self, history: TuningHistory):
    """Persist tuning history to disk for ML training"""
    if not self.tuning_history_file.parent.exists():
        self.tuning_history_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Only save after outcome is known
    if history.fitness_after is None or history.success is None:
        return
    
    # Build record
    record = {
        'timestamp': history.action.timestamp,
        'state_vector': self._get_current_state_vector(),  # Will implement in Phase 2
        'action': {
            'parameter_path': history.action.parameter_path,
            'current_value': history.action.current_value,
            'proposed_value': history.action.proposed_value,
            'change_magnitude': abs(history.action.proposed_value - history.action.current_value),
            'rule_confidence': history.action.confidence  # Before ML boost
        },
        'outcome': {
            'success': history.success,
            'fitness_before': history.fitness_before,
            'fitness_after': history.fitness_after,
            'fitness_change': history.fitness_after - history.fitness_before
        }
    }
    
    # Append to JSONL file
    try:
        with open(self.tuning_history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
    except Exception as e:
        logger.warning(f"[CONFIG_TUNER] Failed to save tuning history: {e}")
```

4. Call from `_update_history()`:
```python
# After setting history.success (around line 388)
if history.success is not None:
    self._save_tuning_history(history)
```

**Why This First**: No ML needed, just persistence. System already evaluates outcomes.

---

### Phase 2: State Vector Builder (Week 1)
**Goal**: Extract features from existing metrics for ML model

**Changes to `reality_simulator/config_tuner.py`:**

Add `_build_state_vector()` method:
```python
def _build_state_vector(self, 
                       ml_metrics: Dict[str, Any],
                       neural_metrics: Dict[str, Any],
                       evolution_metrics: Dict[str, Any],
                       network_metrics: Dict[str, Any]) -> List[float]:
    """
    Build feature vector from system metrics.
    
    Returns: List of 20-30 normalized features for ML model.
    """
    features = []
    
    # ML Metrics (5 features)
    if ml_metrics and ml_metrics.get('enabled'):
        clustering = ml_metrics.get('clustering', {})
        anomalies = ml_metrics.get('anomalies', {})
        semantic = ml_metrics.get('semantic_analysis', {})
        
        features.append(float(clustering.get('n_clusters', 0)) / 20.0)  # Normalize to 0-1
        features.append(float(anomalies.get('anomaly_ratio', 0.0)))
        features.append(float(semantic.get('quality_metrics', {}).get('silhouette_score', 0.0)))
        features.append(float(semantic.get('tfidf_analysis', {}).get('vocabulary_size', 0)) / 100.0)
        features.append(float(len(semantic.get('feature_importance', {}).get('top_predictive_words', []))) / 20.0)
    else:
        features.extend([0.0] * 5)
    
    # Neural Metrics (4 features)
    if neural_metrics and neural_metrics.get('enabled'):
        loss = neural_metrics.get('training_loss', 1.0)
        features.append(min(1.0, float(loss) if loss else 1.0))  # Clamp to 0-1
        features.append(float(neural_metrics.get('avg_epsilon', 0.5)))
        features.append(float(neural_metrics.get('organisms_tracked', 0)) / 100.0)
        features.append(float(neural_metrics.get('training_steps', 0)) / 1000.0)
    else:
        features.extend([0.0] * 4)
    
    # Evolution Metrics (4 features)
    if evolution_metrics:
        best_fitness = evolution_metrics.get('best_fitness', 0.0)
        features.append(min(1.0, float(best_fitness)))  # Clamp to 0-1
        
        # Fitness std (last 10)
        if len(self.fitness_history) >= 10:
            recent_fitness = self.fitness_history[-10:]
            fitness_std = np.std(recent_fitness) if len(recent_fitness) > 1 else 0.0
            features.append(min(1.0, float(fitness_std)))
        else:
            features.append(0.0)
        
        features.append(float(evolution_metrics.get('population_size', 0)) / 5000.0)
        features.append(float(evolution_metrics.get('generation', 0)) / 1000.0)
    else:
        features.extend([0.0] * 4)
    
    # Network Metrics (4 features)
    if network_metrics:
        org_count = network_metrics.get('organism_count', 0)
        conn_count = network_metrics.get('connection_count', 0)
        density = conn_count / max(org_count, 1)
        
        features.append(min(1.0, density / 10.0))  # Normalize density
        features.append(float(network_metrics.get('modularity', 0.0)))
        features.append(float(network_metrics.get('clustering_coefficient', 0.0)))
        
        # VP variance (last 10)
        if len(self.vp_history) >= 10:
            recent_vp = self.vp_history[-10:]
            vp_variance = np.var(recent_vp) if len(recent_vp) > 1 else 0.0
            features.append(min(1.0, float(vp_variance)))
        else:
            features.append(0.0)
    else:
        features.extend([0.0] * 4)
    
    # Historical Trends (3 features)
    # Cluster diversity trend
    if len(self.cluster_count_history) >= 10:
        recent_clusters = self.cluster_count_history[-10:]
        older_clusters = self.cluster_count_history[-20:-10] if len(self.cluster_count_history) >= 20 else recent_clusters
        cluster_trend = (np.mean(recent_clusters) - np.mean(older_clusters)) / max(np.mean(older_clusters), 1)
        features.append(min(1.0, max(-1.0, float(cluster_trend)) + 1.0) / 2.0)  # Normalize -1 to 1 → 0 to 1
    else:
        features.append(0.5)  # Neutral
    
    # Anomaly trend
    if len(self.anomaly_ratio_history) >= 10:
        recent_anomaly = self.anomaly_ratio_history[-10:]
        older_anomaly = self.anomaly_ratio_history[-20:-10] if len(self.anomaly_ratio_history) >= 20 else recent_anomaly
        anomaly_trend = np.mean(recent_anomaly) - np.mean(older_anomaly)
        features.append(min(1.0, max(0.0, float(anomaly_trend) + 0.5)))  # Normalize
    else:
        features.append(0.5)
    
    # Neural loss trend
    if len(self.neural_loss_history) >= 10:
        recent_loss = self.neural_loss_history[-10:]
        older_loss = self.neural_loss_history[-20:-10] if len(self.neural_loss_history) >= 20 else recent_loss
        loss_trend = (np.mean(older_loss) - np.mean(recent_loss)) / max(np.mean(older_loss), 0.001)  # Negative = improving
        features.append(min(1.0, max(0.0, float(loss_trend) + 0.5)))  # Normalize
    else:
        features.append(0.5)
    
    return features
```

Add numpy import:
```python
import numpy as np
```

Add `_get_current_state_vector()` helper:
```python
def _get_current_state_vector(self) -> List[float]:
    """Get current state vector using cached metrics"""
    # Use last known metrics (stored during analyze_and_tune)
    return getattr(self, '_last_state_vector', [0.0] * 25)
```

**Why This**: Simple feature extraction from existing metrics. No new data collection needed.

---

### Phase 3: ML Action Selector (Week 2)
**Goal**: Train model to predict action success, boost confidence scores

**Changes to `reality_simulator/config_tuner.py`:**

1. Add ML components to `__init__`:
```python
# ML Enhancement (optional)
ml_config = config.get('meta_cognitive', {}).get('self_tuning', {}).get('ml_enhancement', {})
self.ml_enabled = ml_config.get('enabled', False) and SKLEARN_AVAILABLE
self.ml_min_samples = ml_config.get('min_training_samples', 100)
self.ml_retrain_interval = ml_config.get('retrain_interval_actions', 50)
self.ml_model_path = Path(ml_config.get('model_path', 'data/models/action_selector.pkl'))

self.action_selector = None  # RandomForestClassifier
self.parameter_encoder = LabelEncoder() if SKLEARN_AVAILABLE else None
self.actions_since_retrain = 0

# Try to load existing model
if self.ml_enabled:
    self._load_or_train_model()
```

2. Add `_load_or_train_model()`:
```python
def _load_or_train_model(self):
    """Load existing model or train new one if enough data"""
    if not SKLEARN_AVAILABLE:
        return
    
    # Try to load existing model
    if self.ml_model_path.exists():
        try:
            self.action_selector = joblib.load(self.ml_model_path)
            logger.info(f"[CONFIG_TUNER] Loaded ML model from {self.ml_model_path}")
            return
        except Exception as e:
            logger.warning(f"[CONFIG_TUNER] Failed to load ML model: {e}")
    
    # Try to train new model
    if self.tuning_history_file.exists():
        self._train_action_selector()
```

3. Add `_train_action_selector()`:
```python
def _train_action_selector(self):
    """Train RandomForest to predict action success"""
    if not SKLEARN_AVAILABLE or not self.tuning_history_file.exists():
        return
    
    # Load training data
    records = []
    try:
        with open(self.tuning_history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except Exception as e:
        logger.warning(f"[CONFIG_TUNER] Failed to load training data: {e}")
        return
    
    if len(records) < self.ml_min_samples:
        logger.info(f"[CONFIG_TUNER] Not enough training data ({len(records)} < {self.ml_min_samples})")
        return
    
    # Extract features and targets
    X = []
    y = []
    param_names = []
    
    for record in records:
        state = record.get('state_vector', [])
        action = record.get('action', {})
        outcome = record.get('outcome', {})
        
        if not state or not action or 'success' not in outcome:
            continue
        
        # Combine state + action features
        features = state.copy()
        param_names.append(action.get('parameter_path', 'unknown'))
        features.append(action.get('current_value', 0.0))
        features.append(action.get('proposed_value', 0.0))
        features.append(action.get('change_magnitude', 0.0))
        
        X.append(features)
        y.append(1 if outcome['success'] else 0)
    
    if len(X) < self.ml_min_samples:
        return
    
    # Encode parameter names
    self.parameter_encoder.fit(param_names)
    param_encoded = self.parameter_encoder.transform(param_names)
    
    # Add encoded parameter as feature
    for i, features in enumerate(X):
        # One-hot encode parameter (simpler than categorical)
        param_onehot = [0.0] * len(self.parameter_encoder.classes_)
        param_idx = param_encoded[i]
        if param_idx < len(param_onehot):
            param_onehot[param_idx] = 1.0
        features.extend(param_onehot)
    
    # Train model
    try:
        self.action_selector = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=1  # Avoid threading issues
        )
        self.action_selector.fit(X, y)
        
        # Save model
        self.ml_model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.action_selector, self.ml_model_path)
        
        accuracy = self.action_selector.score(X, y)
        logger.info(f"[CONFIG_TUNER] Trained ML model on {len(X)} samples (accuracy: {accuracy:.2%})")
        
    except Exception as e:
        logger.warning(f"[CONFIG_TUNER] Failed to train ML model: {e}")
        self.action_selector = None
```

4. Add `_boost_confidence_with_ml()`:
```python
def _boost_confidence_with_ml(self, action: TuningAction, state_vector: List[float]) -> float:
    """
    Use ML model to predict action success and boost confidence.
    
    Returns: Adjusted confidence score (0-1)
    """
    if not self.ml_enabled or self.action_selector is None:
        return action.confidence  # Fallback to rule-based
    
    try:
        # Build feature vector
        features = state_vector.copy()
        features.append(action.current_value)
        features.append(action.proposed_value)
        features.append(abs(action.proposed_value - action.current_value))
        
        # Encode parameter name
        if self.parameter_encoder:
            try:
                param_encoded = self.parameter_encoder.transform([action.parameter_path])[0]
                param_onehot = [0.0] * len(self.parameter_encoder.classes_)
                if param_encoded < len(param_onehot):
                    param_onehot[param_encoded] = 1.0
                features.extend(param_onehot)
            except (ValueError, IndexError):
                # Unknown parameter, use zeros
                features.extend([0.0] * len(self.parameter_encoder.classes_))
        
        # Predict success probability
        success_prob = self.action_selector.predict_proba([features])[0][1]  # Probability of success
        
        # Blend rule-based and ML confidence
        # Weight ML more (0.7) since it's learned from data
        blended_confidence = 0.3 * action.confidence + 0.7 * success_prob
        
        return min(1.0, max(0.0, blended_confidence))
        
    except Exception as e:
        logger.warning(f"[CONFIG_TUNER] ML prediction failed: {e}")
        return action.confidence  # Fallback
```

5. Modify `analyze_and_tune()` to use ML:
```python
# After generating all actions (around line 265)
# Build state vector for ML
state_vector = self._build_state_vector(ml_metrics, neural_metrics, evolution_metrics, network_metrics)
self._last_state_vector = state_vector  # Cache for persistence

# Boost each action's confidence with ML
if self.ml_enabled and actions:
    for action in actions:
        ml_confidence = self._boost_confidence_with_ml(action, state_vector)
        action.confidence = ml_confidence  # Replace with ML-boosted confidence

# Select best action (highest confidence) - existing code
if actions:
    best_action = max(actions, key=lambda a: a.confidence)
    # ... rest of existing code
```

6. Add auto-retrain logic:
```python
# In analyze_and_tune(), after returning best_action:
if self.ml_enabled and best_action:
    self.actions_since_retrain += 1
    if self.actions_since_retrain >= self.ml_retrain_interval:
        self._train_action_selector()  # Retrain with new data
        self.actions_since_retrain = 0
```

**Why This**: Simple scikit-learn integration. Works with existing action structure. Just makes confidence smarter.

---

## Configuration

**File**: `config.json`

Add to `meta_cognitive.self_tuning`:
```json
"ml_enhancement": {
  "enabled": false,
  "min_training_samples": 100,
  "retrain_interval_actions": 50,
  "model_path": "data/models/action_selector.pkl"
}
```

---

## Integration with Neural-ML Symbiosis

**Future Enhancement** (not in initial implementation):
- Use neural embeddings as additional features in state vector
- Use ML feature importance to prioritize which parameters to tune
- Use language quality metrics to adjust tuning aggressiveness

**Why Deferred**: Keep initial implementation simple. Can add these once base system works.

---

## Success Metrics

1. **Data Collection**: Tuning history persists to disk automatically
2. **Model Training**: After 100+ actions, model trains automatically
3. **Performance**: ML prediction adds <5ms overhead
4. **Accuracy**: ML-boosted actions have higher success rate than rule-based
5. **Robustness**: Graceful degradation if scikit-learn unavailable

---

## Why This Approach (Occam's Razor)

✅ **Leverages existing**: System already tracks outcomes, just need to save them
✅ **Minimal code**: ~300 lines added, mostly self-contained methods
✅ **Simple ML**: RandomForest (no neural network complexity)
✅ **Progressive**: Works without ML, gets smarter with data
✅ **Low risk**: Falls back to rules if ML fails
✅ **Validatable**: Easy to compare ML vs rule-based success rates
✅ **Focused niche**: Action selection (not parameter prediction)

---

## Timeline

- **Week 1**: Phase 1 (Data Persistence) + Phase 2 (State Vector)
- **Week 2**: Phase 3 (ML Action Selector)
- **Week 3**: Testing, validation, tuning
- **Future**: Neural predictor (once we have 5000+ samples)

---

## Files Modified

1. `reality_simulator/config_tuner.py` - Add ~300 lines (persistence + ML)
2. `config.json` - Add ml_enhancement config section
3. `data/models/` - Created automatically, stores trained model
4. `data/tuning_history.jsonl` - Created automatically, stores training data

---

## Dependencies

- `scikit-learn>=1.5.0` (already in requirements.txt as optional)
- `joblib` (for model persistence, usually comes with scikit-learn)

No new dependencies needed!

