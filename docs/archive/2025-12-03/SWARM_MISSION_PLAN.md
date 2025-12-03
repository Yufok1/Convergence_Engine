# 🐝 AGENT SWARM MISSION PLAN
## Full System Integration & Optimization

**Date:** December 1, 2025  
**Objective:** Achieve full system integration across AutoTune, Neural (PyTorch), Scikit-learn, Language, CRA, Highlander, and Graph systems  
**Swarm Size:** 5 Agents (1 Claude + 4 Grok)

---

## 📋 MISSION OVERVIEW

The Convergence Engine has multiple sophisticated subsystems that need tighter integration:

| System | Current State | Integration Gap |
|--------|---------------|-----------------|
| **AutoTune (AtomicConfig)** | Domain-aware tuning | Not receiving neural/scikit/language metrics |
| **Neural Trainer (PyTorch)** | DQN + Language Learning | Metrics not flowing to config atoms |
| **Scikit-learn (MLAnalyzer)** | HDBSCAN + IsolationForest + PCA | Clustering/anomaly insights not fed back |
| **Language Learning** | Semantic rewards + knowledge transfer | Quality not informing AutoTune |
| **CRA** | 11 diagnostic endpoints | Missing new agent swarm + ML systems |
| **Highlander** | Tournament + Germination | No language inheritance |
| **Network Graph** | Centralized nx.Graph | Some null references in knowledge transfer |

---

## 🌟 MISSION 1: Claude - CRA Enhancement & Monitoring
**Role:** Research Lead & System Visibility  
**Priority:** HIGH  
**Estimated Complexity:** Medium

### Objective
Extend CRA diagnostics to expose the new agent swarm language learning systems AND scikit-learn ML analysis for monitoring and debugging.

### Deliverables

#### 1.1 New Endpoint: `/api/cra/diagnostics/agent_swarm`
```python
# Returns comprehensive agent swarm stats:
{
    "semantic_reward": {
        "total_calculations": int,
        "avg_reward": float,
        "components": {"word_overlap": float, "coherence": float, "length": float}
    },
    "knowledge_transfer": {
        "total_broadcasts": int,
        "total_recipients": int,
        "total_reward_transferred": float
    },
    "creative_vocabulary": {
        "expansions": int,
        "phrases_generated": int,
        "compounds_created": int
    }
}
```

#### 1.2 New Endpoint: `/api/cra/diagnostics/ml_analysis`
```python
# Returns scikit-learn ML analysis stats:
{
    "ml_available": bool,
    "clustering": {
        "enabled": bool,
        "algorithm": str,  # "hdbscan", "kmeans", "dbscan"
        "n_clusters": int,
        "cluster_sizes": dict,
        "noise_count": int,
        "concept_tags": dict  # Semantic names for clusters
    },
    "anomaly_detection": {
        "enabled": bool,
        "algorithm": str,  # "isolation_forest"
        "anomaly_count": int,
        "anomaly_ratio": float
    },
    "dimensionality_reduction": {
        "enabled": bool,
        "algorithm": str,  # "pca", "tsne"
        "explained_variance": float
    }
}
```

#### 1.3 Update CRA System Prompt
Add documentation for new endpoints so CRA knows how to use them.

### Files to Modify
1. `causation_web_ui.py` - Add new endpoints after `/api/cra/diagnostics/config_tuner`
2. `causation_web_ui.py` - Update CRA system prompt with new endpoint docs

### Data Sources
- `butterfly_chat.py`: `get_agent_swarm_stats()` method (already added)
- `ml_utils.py`: `MLAnalyzer` class with clustering/anomaly results

---

## 🔧 MISSION 2: Grok-1 - Neural (PyTorch) → AutoTune Bridge
**Role:** Neural Integration Specialist  
**Priority:** CRITICAL  
**Estimated Complexity:** High

### Objective
Create bidirectional metrics flow between PyTorch neural training and AtomicConfigSystem so AutoTune can learn from neural performance.

### Deliverables

#### 2.1 Neural Metrics Emission
Add to `trainer.py`:

```python
def _emit_training_metrics_for_autotune(self, metrics: Dict):
    """Emit training metrics for AtomicConfigSystem consumption."""
    if not hasattr(self, 'autotune_metrics_buffer'):
        self.autotune_metrics_buffer = []
    
    self.autotune_metrics_buffer.append({
        'timestamp': time.time(),
        'neural_loss': metrics.get('loss', 1.0),
        'language_loss': metrics.get('language_loss', 1.0),
        'learning_progress': 1.0 - min(metrics.get('loss', 1.0), 1.0),
        'neural_improving': metrics.get('loss', 1.0) < self._prev_loss if hasattr(self, '_prev_loss') else False,
        'batch_efficiency': metrics.get('samples_trained', 0) / max(metrics.get('time_ms', 1), 1)
    })
    
    self.autotune_metrics_buffer = self.autotune_metrics_buffer[-100:]
    self._prev_loss = metrics.get('loss', 1.0)
```

#### 2.2 AtomicConfigSystem Neural Integration
Enhance `_evaluate_domain_success()` in `atomic_config.py`:

```python
def _evaluate_domain_success(self, domain: ConfigDomain, metrics: Dict[str, Any]) -> bool:
    if domain == ConfigDomain.NEURAL:
        # Enhanced with direct trainer access
        if 'neural_trainer' in metrics and hasattr(metrics['neural_trainer'], 'autotune_metrics_buffer'):
            trainer_metrics = metrics['neural_trainer'].autotune_metrics_buffer
            if trainer_metrics:
                recent = trainer_metrics[-10:]
                avg_loss = np.mean([m['neural_loss'] for m in recent])
                improving = sum(1 for m in recent if m['neural_improving']) > len(recent) // 2
                return avg_loss < 0.5 or improving
        
        # Fallback to passed metrics
        loss = metrics.get('neural_loss', metrics.get('loss', 1.0))
        return loss < 0.5 or metrics.get('neural_improving', False)
```

#### 2.3 Wiring in unified_entry.py
```python
# In UnifiedEntry._run_step() - pass trainer to config system
if hasattr(self, 'config_tuner') and hasattr(self, 'neural_trainer'):
    tune_metrics = {
        'neural_trainer': self.neural_trainer,
        'avg_fitness': avg_fitness,
        # ... other metrics
    }
    self.config_tuner.tune(tune_metrics, frame_count)
```

### Files to Modify
1. `reality_simulator/neural/trainer.py` - Add `_emit_training_metrics_for_autotune()`
2. `reality_simulator/tuning/atomic_config.py` - Enhance NEURAL domain evaluation
3. `unified_entry.py` - Wire trainer to config system

---

## 🧪 MISSION 3: Grok-2 - Scikit-learn → AutoTune Bridge
**Role:** ML Analytics Integration Specialist  
**Priority:** CRITICAL  
**Estimated Complexity:** High

### Objective
Connect scikit-learn MLAnalyzer insights (clustering, anomaly detection) to AtomicConfigSystem and create feedback loops to Neural system.

### Deliverables

#### 3.1 ML Metrics Aggregator
Add to `ml_utils.py`:

```python
class MLMetricsAggregator:
    """Aggregate ML analysis metrics for AutoTune consumption."""
    
    def __init__(self):
        self.clustering_history = []
        self.anomaly_history = []
        
    def update_clustering(self, result: ClusteringResult):
        self.clustering_history.append({
            'timestamp': result.timestamp,
            'n_clusters': result.n_clusters,
            'noise_ratio': np.sum(result.labels == -1) / len(result.labels) if len(result.labels) > 0 else 0,
            'algorithm': result.algorithm
        })
        self.clustering_history = self.clustering_history[-100:]
    
    def update_anomaly(self, result: AnomalyResult):
        self.anomaly_history.append({
            'timestamp': result.timestamp,
            'anomaly_ratio': result.anomaly_ratio,
            'anomaly_count': len(result.anomaly_indices)
        })
        self.anomaly_history = self.anomaly_history[-100:]
    
    def get_autotune_metrics(self) -> Dict[str, Any]:
        """Get metrics formatted for AtomicConfigSystem."""
        cluster_stability = 0.0
        if self.clustering_history:
            recent = self.clustering_history[-10:]
            cluster_stability = 1.0 - np.std([c['n_clusters'] for c in recent]) / max(np.mean([c['n_clusters'] for c in recent]), 1)
        
        return {
            'ml_enabled': True,
            'cluster_count': self.clustering_history[-1]['n_clusters'] if self.clustering_history else 0,
            'cluster_stability': cluster_stability,
            'anomaly_ratio': self.anomaly_history[-1]['anomaly_ratio'] if self.anomaly_history else 0.0
        }
```

#### 3.2 AtomicConfigSystem ML Domain
Add to `atomic_config.py`:

```python
# In ConfigDomain enum:
ML = 'ml'  # Scikit-learn ML analysis

# In _evaluate_domain_success():
elif domain == ConfigDomain.ML:
    if 'ml_metrics' in metrics:
        ml = metrics['ml_metrics']
        cluster_stable = ml.get('cluster_stability', 0) > 0.5
        anomaly_healthy = 0.05 < ml.get('anomaly_ratio', 0) < 0.20
        return cluster_stable and anomaly_healthy
    return True

# New ML Config Atoms:
'scikit.clustering.min_cluster_size': ConfigAtom(..., domain=ConfigDomain.ML),
'scikit.anomaly_detection.contamination': ConfigAtom(..., domain=ConfigDomain.ML),
```

#### 3.3 ML → Neural Feedback Loop
Add to `trainer.py`:

```python
def adjust_exploration_from_ml(self, ml_metrics: Dict[str, Any]):
    """Adjust neural exploration based on ML insights."""
    cluster_count = ml_metrics.get('cluster_count', 5)
    anomaly_ratio = ml_metrics.get('anomaly_ratio', 0.1)
    
    # Few clusters = population converging, need more exploration
    if cluster_count < 3:
        for org_id, tracker in self.organism_trackers.items():
            if hasattr(tracker, 'dqn') and tracker.dqn:
                tracker.dqn.epsilon = min(1.0, tracker.dqn.epsilon + 0.1)
    
    # High anomaly ratio = too much diversity, exploit good solutions
    elif anomaly_ratio > 0.25:
        for org_id, tracker in self.organism_trackers.items():
            if hasattr(tracker, 'dqn') and tracker.dqn:
                tracker.dqn.epsilon = max(0.05, tracker.dqn.epsilon * 0.9)
```

### Files to Modify
1. `reality_simulator/ml_utils.py` - Add `MLMetricsAggregator` class
2. `reality_simulator/tuning/atomic_config.py` - Add ML domain + atoms
3. `reality_simulator/neural/trainer.py` - Add `adjust_exploration_from_ml()`
4. `unified_entry.py` - Wire ML metrics to AutoTune and Neural

---

## 🔗 MISSION 4: Grok-3 - Language → AutoTune Bridge
**Role:** Language Integration Architect  
**Priority:** HIGH  
**Estimated Complexity:** Medium

### Objective
Connect language learning quality metrics to AtomicConfigSystem for automatic language parameter optimization.

### Deliverables

#### 4.1 Language Metrics Aggregator
Add to `butterfly_chat.py`:

```python
class LanguageMetricsAggregator:
    """Aggregate language learning metrics for AutoTune consumption."""
    
    def __init__(self):
        self.semantic_reward_history = []
        self.knowledge_transfer_stats = {'total_broadcasts': 0, 'successful_transfers': 0}
        self.vocabulary_stats = {'creative_generations': 0, 'compounds_created': 0}
    
    def get_autotune_metrics(self) -> Dict[str, Any]:
        return {
            'language_learning': len(self.semantic_reward_history) > 0,
            'avg_semantic_reward': np.mean(self.semantic_reward_history[-100:]) if self.semantic_reward_history else 0.0,
            'knowledge_transfer_rate': self.knowledge_transfer_stats['successful_transfers'] / max(self.knowledge_transfer_stats['total_broadcasts'], 1),
            'vocabulary_growth': self.vocabulary_stats['compounds_created']
        }
```

#### 4.2 AtomicConfigSystem Language Domain Enhancement
```python
# In _evaluate_domain_success():
elif domain == ConfigDomain.LANGUAGE:
    if 'language_metrics' in metrics:
        lang = metrics['language_metrics']
        reward_quality = lang.get('avg_semantic_reward', 0) > 0.4
        transfer_working = lang.get('knowledge_transfer_rate', 0) > 0.3
        return reward_quality or transfer_working
    return True

# New Language Config Atoms:
'language.semantic_reward.word_overlap_weight': ConfigAtom(...),
'language.knowledge_transfer.reward_discount': ConfigAtom(...),
```

### Files to Modify
1. `reality_simulator/language/butterfly_chat.py` - Add `LanguageMetricsAggregator`
2. `reality_simulator/tuning/atomic_config.py` - Enhance LANGUAGE domain + add atoms
3. `unified_entry.py` - Wire language metrics to config system

---

## ⚔️ MISSION 5: Grok-4 - Highlander Language Inheritance + Graph Safety
**Role:** Evolution & Reliability Specialist  
**Priority:** MEDIUM-HIGH  
**Estimated Complexity:** High

### Objective
1. When a Highlander battle concludes, winner inherits linguistic capabilities from defeated
2. Ensure all systems using network_graph have null-safe access

### Deliverables

#### Part A: Highlander Language Inheritance

#### 5.1 Linguistic Trait Extraction
Add to `highlander_protocol.py`:

```python
def extract_linguistic_traits(self, organism) -> Dict[str, Any]:
    """Extract linguistic traits for inheritance."""
    traits = {
        'vocabulary_exposure': [],
        'successful_patterns': []
    }
    
    if hasattr(organism, 'token_sequence'):
        traits['vocabulary_exposure'] = list(organism.token_sequence)[-100:]
    
    if hasattr(organism, 'experience_buffer') and organism.experience_buffer:
        for exp in organism.experience_buffer.buffer[-50:]:
            if hasattr(exp, 'reward') and exp.reward > 0.6:
                if hasattr(exp, 'target_tokens') and exp.target_tokens:
                    traits['successful_patterns'].append({
                        'input': getattr(exp, 'input_tokens', []),
                        'output': exp.target_tokens,
                        'reward': exp.reward
                    })
    return traits

def absorb_linguistic_traits(self, winner, loser_traits: Dict, absorption_rate: float = 0.5):
    """Winner absorbs linguistic traits from defeated opponent."""
    # Vocabulary transfer
    if loser_traits['vocabulary_exposure'] and hasattr(winner, 'token_sequence'):
        num_to_transfer = int(len(loser_traits['vocabulary_exposure']) * absorption_rate)
        tokens_to_add = random.sample(loser_traits['vocabulary_exposure'], 
                                      min(num_to_transfer, len(loser_traits['vocabulary_exposure'])))
        for token in tokens_to_add:
            winner.token_sequence.append(token)
    
    # Emit inheritance event
    if self.event_emitter:
        self.event_emitter({
            'event_type': 'linguistic_inheritance',
            'component': 'highlander',
            'data': {'winner_id': str(id(winner)), 'absorption_rate': absorption_rate}
        })
```

#### 5.2 Integration with Battle Resolution
```python
# In resolve_combat() - after victory determination:
if winner and loser:
    loser_traits = self.extract_linguistic_traits(loser)
    if loser_traits['vocabulary_exposure'] or loser_traits['successful_patterns']:
        self.absorb_linguistic_traits(winner, loser_traits, absorption_rate=0.5)
```

#### Part B: Graph Null Safety

#### 5.3 NetworkGraph Access Helper
Add to `symbiotic_network.py`:

```python
class NetworkGraphAccessor:
    """Safe, centralized access to network graph with null handling."""
    
    def __init__(self, network):
        self._network = network
    
    @property
    def graph(self) -> Optional[nx.Graph]:
        if self._network is None:
            return None
        return getattr(self._network, 'network_graph', None)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        g = self.graph
        if g is None or node_id not in g:
            return []
        return list(g.neighbors(node_id))
    
    def get_edge_data(self, source: str, target: str) -> Dict[str, Any]:
        g = self.graph
        if g is None or not g.has_edge(source, target):
            return {'strength': 0.5, 'type': 'unknown'}
        return g.get_edge_data(source, target, {'strength': 0.5})
```

#### 5.4 Graph Validation at Startup
```python
# In unified_entry.py initialize()
def _validate_graph_dependencies(self):
    issues = []
    network = self.reality_sim.components.get('network') if self.reality_sim else None
    
    if hasattr(self, 'butterfly_chat') and not network:
        issues.append("Butterfly Chat knowledge transfer may fail - no network")
    if hasattr(self, 'highlander_protocol') and not network:
        issues.append("Highlander Protocol may have issues - no network")
    
    for issue in issues:
        print(f"[UNIFIED] [WARN] {issue}")
    return len(issues) == 0
```

### Files to Modify
1. `reality_simulator/evolution/highlander_protocol.py` - Add trait extraction/absorption
2. `reality_simulator/evolution/battle_arena.py` - Trigger inheritance post-battle
3. `reality_simulator/symbiotic_network.py` - Add `NetworkGraphAccessor`
4. `reality_simulator/language/butterfly_chat.py` - Use accessor for graph operations
5. `unified_entry.py` - Add graph validation at startup
6. `config.json` - Add `highlander.linguistic_absorption_rate` parameter

---

## 📅 EXECUTION TIMELINE

### Phase 1: Foundation (Missions 2 + 5B)
**Duration:** 2-3 hours  
**Rationale:** Establish neural metrics flow and fix graph safety as foundation

1. Grok-1 implements neural metrics emission
2. Grok-4 implements NetworkGraphAccessor
3. Both integrate and test

### Phase 2: ML + Language Integration (Missions 3 + 4 + 1)
**Duration:** 4-5 hours  
**Rationale:** Build scikit-learn feedback loop, language metrics aggregator, then expose via CRA

1. Grok-2 implements MLMetricsAggregator and AutoTune ML domain
2. Grok-3 implements LanguageMetricsAggregator
3. Claude implements CRA diagnostic endpoints (including ML)
4. Wire all metrics to AutoTune

### Phase 3: Highlander Enhancement (Mission 5A)
**Duration:** 2-3 hours  
**Rationale:** Add linguistic inheritance to complete the evolution loop

1. Grok-4 implements trait extraction/absorption
2. Integrate with battle resolution
3. Test inheritance flow

### Phase 4: Validation & Polish
**Duration:** 1-2 hours
1. Run full system test
2. Verify all CRA endpoints return data
3. Verify AutoTune receiving all domain metrics (Neural, ML, Language)
4. Verify Highlander linguistic inheritance
5. Verify ML → Neural exploration feedback loop

---

## 🎯 SUCCESS CRITERIA

| Metric | Target |
|--------|--------|
| CRA Diagnostic Endpoints | 2 new endpoints returning valid data (agent_swarm + ml_analysis) |
| Neural (PyTorch) → AutoTune Flow | `_evaluate_domain_success(NEURAL)` uses live trainer metrics |
| Scikit-learn → AutoTune Flow | `_evaluate_domain_success(ML)` uses clustering/anomaly metrics |
| Scikit-learn → Neural Flow | Cluster count affects DQN exploration rates |
| Language → AutoTune Flow | `_evaluate_domain_success(LANGUAGE)` uses aggregated metrics |
| Graph Null Errors | Zero null reference errors in knowledge transfer |
| Highlander Language Inheritance | Winners gain vocabulary/patterns from defeated |
| Event Illumination | All new systems emit causation events |

---

## 🚀 READY FOR EXECUTION

| Agent | Mission | Focus Area |
|-------|---------|------------|
| **Claude** | Mission 1 | CRA Enhancement - expose agent swarm + ML via diagnostics |
| **Grok-1** | Mission 2 | Neural (PyTorch) → AutoTune metrics bridge |
| **Grok-2** | Mission 3 | Scikit-learn → AutoTune + Neural feedback loop |
| **Grok-3** | Mission 4 | Language → AutoTune metrics bridge |
| **Grok-4** | Mission 5 | Highlander language inheritance + Graph null safety |

*All 5 agents assigned. Awaiting execution authorization.*
