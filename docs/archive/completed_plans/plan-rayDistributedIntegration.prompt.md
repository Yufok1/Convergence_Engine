# Ray Distributed Computing Integration for Convergence Engine

**TL;DR:** Integrate Ray across 6 key subsystems (Neural, Network, Highlander, ML, Causation, Language) using a phased approach. Phase 1 parallelizes organism decisions (biggest CPU bottleneck), Phase 2 adds distributed training, Phase 3 scales tournament/ML systems. This transforms single-threaded simulation into a multi-core/multi-node distributed system while preserving causation tracking.

---

## 🔍 **PEER REVIEW ANALYSIS (December 2025)**

### **Overall Assessment: 7.5/10 - APPROVED WITH REFINEMENTS**

Four comprehensive analyses identified key strengths and critical gaps. This plan has been updated to incorporate all critical refinements.

### **✅ Validated Bottlenecks:**
- Neural decisions: `symbiotic_network.py:1453-1470` - CONFIRMED
- Training loop: `trainer.py:556-703` - CONFIRMED  
- Battle resolution: `highlander_protocol.py:487-520` - CONFIRMED
- ML features: `ml_utils.py:179-280` - CONFIRMED

### **⚠️ Critical Issues Addressed:**
1. **Method Name Error** - Fixed: `_collect_organism_decisions()` doesn't exist; code is inline in `update_network()`
2. **State Synchronization** - Added: New State Synchronization Strategy section
3. **Actor State Management** - Added: Actor lifecycle management patterns
4. **Causation Event Ordering** - Enhanced: Vector clocks and batch event processing
5. **Memory Management** - Added: Object store cleanup and actor pooling
6. **GPU Strategy** - Resolved: Single GPU with CPU parallelism recommended

### **📊 Revised Performance Expectations:**

| Component | Current | Ray (8 cores) | **Revised Speedup** | Overhead Impact |
|-----------|---------|---------------|---------------------|-----------------|
| 1000 Decisions | ~200ms | ~50-80ms | **3-4x** | High (state serialization) |
| 100 Training Steps | ~500ms | ~150-250ms | **2-3x** | Very High (PyTorch state) |
| 50 Battles | ~100ms | ~20-30ms | **4-5x** | Medium (stateless) |
| ML Features | ~150ms | ~30-50ms | **4-5x** | Low (pure computation) |

*Note: Original 6-7x estimates were optimistic. Revised based on serialization overhead analysis.*

---

## Phase 1: Foundation & Neural Parallelization

### Step 1: Create Ray Infrastructure Layer

Create new `reality_simulator/distributed/` folder with core Ray management:

**`ray_manager.py`** - Central Ray lifecycle management:
- `RayManager` class with `init()`, `shutdown()`, `is_initialized()` 
- Resource monitoring (`ray.available_resources()`)
- Graceful degradation when Ray unavailable
- Config-driven initialization from `/ray/*` settings

**`ray_actors.py`** - Stateful distributed actors:
- `OrganismBrainActor` - Persistent neural network per organism
- `TrainerActor` - Distributed training coordinator
- Actor pool management for organism count scaling

**`ray_tasks.py`** - Stateless parallel tasks:
- `@ray.remote` decorated functions for embarrassingly parallel work
- Battle resolution, feature extraction, connection evaluation

### Step 2: Parallelize Neural Organism Decisions

**Target:** `symbiotic_network.py` → `update_network()` method (lines 1453-1470)

*Note: Decision collection happens inline in `update_network()`, not in a separate method.*

**Current Pattern (Sequential):**
```python
# symbiotic_network.py:1453-1470
organism_actions = {}
for org_id, organism in self.organisms.items():
    if hasattr(organism, 'decide_action') and hasattr(organism, 'brain') and organism.brain is not None:
        local_env = {
            'resources': getattr(organism, 'resources', 0.5),
            'neighbors': len(list(self.network_graph.neighbors(org_id))) if org_id in self.network_graph else 0,
        }
        action = organism.decide_action(local_env=local_env, network_state=network_state, breath_state=None)
        organism_actions[org_id] = action
```

**Ray Pattern (Parallel) - ACTOR-BASED APPROACH:**

⚠️ **Critical Design Decision:** Use Ray Actors, NOT stateless tasks, for organisms with neural brains. This avoids serialization overhead on every call.

```python
@ray.remote
class OrganismActor:
    """Persistent actor holding organism state - avoids repeated serialization"""
    def __init__(self, organism_state, brain_weights):
        self.organism = self._reconstruct_organism(organism_state)
        if brain_weights:
            self.organism.brain.load_state_dict(brain_weights)
        
    def decide_action(self, local_env, network_state, breath_state):
        action = self.organism.decide_action(local_env, network_state, breath_state)
        return action, self.organism.get_state()  # Return updated state for sync
    
    def get_state(self):
        return self.organism.get_state()
    
    def update_state(self, new_state):
        """Sync state from main process"""
        self.organism.set_state(new_state)

# Actor pool management
class OrganismActorPool:
    def __init__(self, organisms):
        self.actors = {
            org_id: OrganismActor.remote(org.get_state(), 
                org.brain.state_dict() if hasattr(org, 'brain') and org.brain else None)
            for org_id, org in organisms.items()
        }
    
    def parallel_decide_all(self, local_envs, network_state, breath_state):
        futures = {
            org_id: actor.decide_action.remote(local_envs[org_id], network_state, breath_state)
            for org_id, actor in self.actors.items()
        }
        results = {org_id: ray.get(future) for org_id, future in futures.items()}
        return {org_id: result[0] for org_id, result in results.items()}  # Just actions
```

**Parallelization Threshold:** Only parallelize when `len(organisms) > 50` (configurable)

---

## Phase 2: Distributed Training

### Step 3: Distribute DQN Training

**Target:** `reality_simulator/neural/trainer.py` → `train_step()` (lines 556-703)

**Current Pattern:**
```python
# trainer.py:556-703
for organism in trainable_organisms:
    states, actions, rewards, next_states, dones = organism.experience_buffer.sample_batch()
    # Triple-loss system: RL + Language + Concept
    loss = self.rl_loss_weight * rl_loss
    if language_loss is not None:
        loss = loss + self.language_loss_weight * language_loss  
    if concept_loss is not None:
        loss = loss + self.concept_loss_weight * concept_loss
    loss.backward()
    self.optimizers[organism_id].step()
```

**Ray Pattern with Actors:**

⚠️ **Critical: Actor State Synchronization Strategy**

```python
@ray.remote(num_gpus=0.1)  # Fractional GPU sharing
class OrganismTrainerActor:
    def __init__(self, brain_config, device='cpu'):
        self.device = device
        self.brain = NeuralOrganismBrain(brain_config).to(device)
        self.optimizer = torch.optim.Adam(self.brain.parameters())
        self.training_stats = {'total_loss': 0, 'steps': 0}
    
    def load_weights(self, state_dict):
        """Load weights from main process"""
        self.brain.load_state_dict(state_dict)
    
    def train_batch(self, experiences_ref, loss_weights):
        """Train on batch, return updated weights"""
        # experiences_ref is an ObjectRef to avoid copying
        experiences = ray.get(experiences_ref)
        states, actions, rewards, next_states, dones = experiences
        
        # Convert to tensors on actor's device
        states = torch.tensor(states, device=self.device)
        # ... other conversions
        
        # Training step
        loss = self._compute_triple_loss(states, actions, rewards, next_states, dones, loss_weights)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.training_stats['total_loss'] += loss.item()
        self.training_stats['steps'] += 1
        
        return {
            'loss': loss.item(),
            'state_dict': self.brain.state_dict(),  # Return for sync
            'stats': self.training_stats
        }
    
    def cleanup(self):
        """Release GPU memory"""
        del self.brain
        del self.optimizer
        torch.cuda.empty_cache()

# State synchronization after training
def sync_training_results(organisms, actor_results):
    """Sync actor weights back to main process organisms"""
    for org, result in zip(organisms, actor_results):
        org.brain.load_state_dict(result['state_dict'])
        org.training_loss = result['loss']  # Track for VP monitoring
```

**Shared Experience Replay with Memory Management:**
```python
class DistributedExperienceManager:
    def __init__(self, max_refs=100):
        self.experience_refs = {}
        self.max_refs = max_refs
    
    def put_experiences(self, org_id, experiences):
        """Store in ObjectStore with memory tracking"""
        # Cleanup old refs to prevent memory explosion
        if len(self.experience_refs) >= self.max_refs:
            oldest_ref = next(iter(self.experience_refs))
            del self.experience_refs[oldest_ref]
        
        ref = ray.put(experiences)
        self.experience_refs[org_id] = ref
        return ref
    
    def cleanup_org(self, org_id):
        """Release memory when organism dies"""
        if org_id in self.experience_refs:
            del self.experience_refs[org_id]
```

**GPU Strategy Decision: SINGLE GPU + CPU PARALLELISM**
- Keep all PyTorch training on single GPU (simpler, better memory efficiency)
- Use Ray for CPU parallelization of non-neural work
- Fractional GPU allocation (`num_gpus=0.1`) allows multiple actors to share GPU

---

## Phase 3: Tournament & ML Scaling

### Step 4: Scale Highlander Battles

**Target:** `reality_simulator/evolution/highlander_protocol.py` → `_run_competition()` (lines 487-520)

**Current Pattern:**
```python
# highlander_protocol.py:487-549
for _ in range(num_battles):
    # Select combatants, conduct battle, absorb loser traits
    result = self._conduct_battle(org1_id, organisms[org1_id], org2_id, organisms[org2_id], get_fitness)
    if result:
        battles.append(result.to_dict())
        self._absorb_loser(result.winner_id, organisms[result.winner_id], 
                          result.loser_id, organisms[result.loser_id])
```

**Ray Pattern (Stateless Tasks - Ideal for Battles):**
```python
@ray.remote
def resolve_battle_remote(org_a_state, org_b_state, battle_config):
    """Stateless battle resolution - no state mutation during battle"""
    result = BattleResolver.resolve(org_a_state, org_b_state, battle_config)
    return result

# Collect all battle pairs first, then resolve in parallel
battle_pairs = [(org_a, org_b) for ... if self._should_battle(org_a, org_b)]
futures = [
    resolve_battle_remote.remote(a.get_state(), b.get_state(), self.config)
    for a, b in battle_pairs
]
results = ray.get(futures)

# IMPORTANT: Apply state mutations AFTER parallel resolution
for result in results:
    if result:
        self._absorb_loser(result.winner_id, organisms[result.winner_id],
                          result.loser_id, organisms[result.loser_id])
```

*Note: Battles are ideal for stateless Ray tasks - no shared state during computation, mutations applied sequentially after.*

### Step 5: Integrate Ray Data for ML Analysis

**Target:** `reality_simulator/ml_analyzer.py`

**Current Pattern:**
```python
def extract_features(self, organisms, context_memory):
    features = []
    for org in organisms:
        feat = self._extract_organism_features(org, context_memory)
        features.append(feat)
    return np.array(features)
```

**Ray Data Pattern:**
```python
import ray.data

def extract_features_distributed(self, organisms, context_memory):
    # Create Ray Dataset from organisms
    org_data = ray.data.from_items([org.get_state() for org in organisms])
    
    # Map feature extraction in parallel
    features_ds = org_data.map(
        lambda state: self._extract_organism_features_from_state(state, context_memory)
    )
    
    # Collect results
    return np.array(features_ds.take_all())
```

**Distributed Scikit-learn:**
```python
from ray.util.joblib import register_ray
register_ray()

# Now sklearn uses Ray backend automatically
from sklearn.cluster import HDBSCAN
clusterer = HDBSCAN(n_jobs=-1)  # Uses Ray workers
```

---

## 🆕 Phase 4.5: State Synchronization Strategy

### **Critical Design: State Propagation Across Workers**

**Challenge:** Current system assumes tight coupling - all organisms see identical `network_state` and `breath_state` simultaneously. Ray workers need consistent state snapshots.

**Solution: Breath-Cycle State Snapshots**

```python
class DistributedStateManager:
    """Manages state consistency across Ray workers"""
    
    def __init__(self):
        self.current_snapshot_ref = None
        self.snapshot_version = 0
        
    def create_snapshot(self, network_state, breath_state, organisms):
        """Create immutable state snapshot at breath cycle boundary"""
        snapshot = {
            'version': self.snapshot_version,
            'timestamp': time.time(),
            'network_state': network_state.copy(),  # Deep copy
            'breath_state': breath_state.copy() if breath_state else None,
            'organism_states': {
                org_id: org.get_state() 
                for org_id, org in organisms.items()
            }
        }
        
        # Store in ObjectStore - returns immutable reference
        self.current_snapshot_ref = ray.put(snapshot)
        self.snapshot_version += 1
        
        return self.current_snapshot_ref
    
    def get_snapshot_ref(self):
        """Workers use this ref for consistent reads"""
        return self.current_snapshot_ref

# Integration with breath cycle
def breath_cycle(self):
    """Main breath loop with state synchronization"""
    # 1. Create immutable snapshot BEFORE parallel work
    snapshot_ref = self.state_manager.create_snapshot(
        self.network_state, self.breath_state, self.organisms
    )
    
    # 2. Parallel decisions with consistent snapshot
    if self.ray_manager.is_initialized():
        decisions = self.ray_manager.parallel_decide_all(
            self.actor_pool, snapshot_ref
        )
    else:
        decisions = self._sequential_decide_all()
    
    # 3. Sequential state mutations (maintains consistency)
    for org_id, action in decisions.items():
        self.organisms[org_id].apply_action(action)
    
    # 4. Update network state for next cycle
    self.network_state = self._compute_network_state()
```

**Config Integration:**
```json
{
  "ray": {
    "state_synchronization": {
      "snapshot_strategy": "breath_cycle",
      "consistency_model": "sequential",
      "max_state_age_ms": 100
    }
  }
}
```

---

## Phase 5: Configuration & CRA Integration

### Step 6: Add Config Controls

**New `/ray/*` config paths in `config.json`:**

```json
{
  "ray": {
    "enabled": true,
    "num_cpus": null,
    "num_gpus": null,
    "object_store_memory": null,
    "parallelization_threshold": 50,
    "actor_pool_size": 4,
    "batch_inference_size": 32,
    "fallback_on_error": true,
    "logging_level": "warning",
    "state_synchronization": {
      "snapshot_strategy": "breath_cycle",
      "consistency_model": "sequential",
      "max_state_age_ms": 100
    },
    "memory_management": {
      "max_object_refs": 100,
      "cleanup_on_organism_death": true,
      "actor_pool_lru_eviction": true
    }
  }
}
```

**CRA CONFIG_UPDATE Support:**
```
[[CONFIG_UPDATE: {"reason": "Scale up parallelization", "patch": [
  {"op": "replace", "path": "/ray/parallelization_threshold", "value": 25},
  {"op": "replace", "path": "/ray/actor_pool_size", "value": 8}
]}]]
```

**Add to CONFIG_GUARDRAILS:**
```python
"/ray/parallelization_threshold": (10, 500),
"/ray/actor_pool_size": (1, 32),
"/ray/batch_inference_size": (8, 128),
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED ENTRY POINT                                  │
│                         (unified_entry.py)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAY MANAGER                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ ray.init()  │  │  Resource   │  │  Fallback   │  │   Config    │        │
│  │ ray.shutdown│  │  Monitor    │  │   Handler   │  │   Loader    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│    RAY ACTORS       │ │    RAY TASKS        │ │    RAY DATA         │
│  (Stateful)         │ │  (Stateless)        │ │  (Pipelines)        │
├─────────────────────┤ ├─────────────────────┤ ├─────────────────────┤
│ OrganismBrainActor  │ │ parallel_decide()   │ │ feature_extraction  │
│ TrainerActor        │ │ resolve_battle()    │ │ clustering_pipeline │
│ CausationActor      │ │ evaluate_connection │ │ anomaly_pipeline    │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RAY OBJECT STORE                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  network_state  │  │ experience_data │  │  battle_results │              │
│  │  (shared read)  │  │  (shared read)  │  │  (write-back)   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🆕 Causation Tracking Preservation (ENHANCED)

**Challenge:** Ray tasks are async - need event ordering strategy. Current system expects immediate ordering via simple timestamps.

⚠️ **Critical Complexity:** The analyses identified this as the highest-risk area. Out-of-order event arrival can break causation trails.

**Solution: Vector Clocks + Batch Event Processing**

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import threading

@dataclass
class DistributedEvent:
    event_id: str
    timestamp: float           # Wall clock time
    logical_clock: int         # Lamport timestamp  
    worker_id: str             # Ray worker identifier
    batch_sequence: int        # Position within batch (guaranteed ordering)
    causation_context: dict    # Parent event IDs carried through
    vector_clock: Dict[str, int] = field(default_factory=dict)  # Full vector clock

class DistributedCausationManager:
    """Thread-safe causation tracking for distributed events"""
    
    def __init__(self, causation_explorer):
        self.explorer = causation_explorer
        self.vector_clock = {}  # worker_id -> logical_clock
        self.event_buffer = []
        self.buffer_lock = threading.Lock()
        self.flush_threshold = 100  # Flush buffer when this many events
        
    def increment_clock(self, worker_id: str) -> int:
        """Thread-safe Lamport clock increment"""
        with self.buffer_lock:
            current = self.vector_clock.get(worker_id, 0)
            self.vector_clock[worker_id] = current + 1
            return current + 1
    
    def merge_vector_clock(self, incoming_clock: Dict[str, int]):
        """Merge incoming vector clock (for happens-before ordering)"""
        with self.buffer_lock:
            for worker_id, clock in incoming_clock.items():
                self.vector_clock[worker_id] = max(
                    self.vector_clock.get(worker_id, 0), clock
                )

# Event emission from Ray task with batch sequencing
@ray.remote
def parallel_task_batch(input_batch, batch_start_seq, causation_context):
    """Process batch with guaranteed event ordering via sequence numbers"""
    results = []
    events = []
    worker_id = ray.get_runtime_context().get_worker_id()
    
    for i, input_data in enumerate(input_batch):
        result = do_work(input_data)
        
        event = DistributedEvent(
            event_id=generate_id(),
            timestamp=time.time(),
            logical_clock=causation_context['clock'] + i,
            worker_id=worker_id,
            batch_sequence=batch_start_seq + i,  # GUARANTEED ORDERING
            causation_context={'parent': causation_context['event_id']},
            vector_clock=causation_context.get('vector_clock', {}).copy()
        )
        
        results.append(result)
        events.append(event)
    
    return results, events
```

**Event Ordering in CausationExplorer (ENHANCED):**
```python
def add_distributed_events(self, events: List[DistributedEvent]):
    """Add events with proper causal ordering"""
    
    # PRIMARY: Sort by batch_sequence (guaranteed ordering within batches)
    # SECONDARY: Sort by logical clock (ordering across batches)
    # TERTIARY: Sort by timestamp (tiebreaker for concurrent events)
    sorted_events = sorted(
        events, 
        key=lambda e: (e.batch_sequence, e.logical_clock, e.timestamp)
    )
    
    for event in sorted_events:
        # Convert to standard Event format
        std_event = Event(
            timestamp=event.timestamp,
            component='ray_distributed',
            event_type='parallel_execution',
            data={
                'worker_id': event.worker_id,
                'logical_clock': event.logical_clock,
                'batch_sequence': event.batch_sequence,
                **event.causation_context
            }
        )
        
        self.add_event(std_event)
        
        # Reconstruct causation links from context
        if event.causation_context.get('parent'):
            self.add_link(event.causation_context['parent'], event.event_id)
```

**Integration with Existing Event Emission:**
```python
# Use existing pattern from unified_entry.py:1098-1116
def emit_distributed_event_to_causation(event, is_historical=False):
    """Emit distributed events using existing emission pattern"""
    if self.causation_explorer:
        try:
            self.causation_explorer.add_event(event, is_historical=False)
        except Exception as e:
            logger.warning(f"Failed to emit distributed event: {e}")
```
```

---

## Fallback Mode (Graceful Degradation)

**Pattern: Optional Dependency like onnxruntime**

```python
# reality_simulator/distributed/__init__.py
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    ray = None

def get_ray_manager():
    if RAY_AVAILABLE:
        from .ray_manager import RayManager
        return RayManager()
    else:
        from .fallback_manager import SequentialFallback
        return SequentialFallback()
```

**Fallback Manager (Sequential Execution):**
```python
class SequentialFallback:
    """Drop-in replacement when Ray unavailable - matches existing patterns"""
    
    def __init__(self):
        self._initialized = False
    
    def is_initialized(self):
        return False
    
    def map_parallel(self, func, items, **kwargs):
        # Just run sequentially - same interface as RayManager
        return [func(item, **kwargs) for item in items]
    
    def get_results(self, futures):
        # Futures are already results in fallback mode
        return futures
    
    def parallel_decide_all(self, organisms, network_state, breath_state):
        # Sequential fallback for organism decisions
        return {
            org_id: org.decide_action(
                local_env={'resources': org.resources, 'neighbors': 0},
                network_state=network_state,
                breath_state=breath_state
            )
            for org_id, org in organisms.items()
            if hasattr(org, 'decide_action') and hasattr(org, 'brain') and org.brain
        }
```

**Import Path Setup (matching existing patterns):**
```python
def _setup_ray_imports():
    """Mirror the import path setup from unified_entry.py"""
    from pathlib import Path
    import sys
    parent_path = Path(__file__).parent.parent
    reality_sim_path = parent_path / 'reality_simulator'
    if str(reality_sim_path) not in sys.path:
        sys.path.insert(0, str(reality_sim_path))
```

---

## Performance Expectations (REVISED)

⚠️ **Original estimates were optimistic. Revised based on serialization overhead analysis.**

| Component | Current (Sequential) | With Ray (8 cores) | **Revised Speedup** | Notes |
|-----------|---------------------|-------------------|---------------------|-------|
| 1000 organism decisions | ~200ms | ~50-80ms | **3-4x** | High state serialization overhead |
| 100 organism training | ~500ms | ~150-250ms | **2-3x** | PyTorch state sync is expensive |
| 50 Highlander battles | ~100ms | ~20-30ms | **4-5x** | Stateless - ideal for Ray tasks |
| ML feature extraction (1000 orgs) | ~150ms | ~30-50ms | **4-5x** | Embarrassingly parallel |
| Causation trace (depth=20) | ~50ms | ~30ms | **2x** | Vector clock overhead |

**Key Insight:** Neural decisions show lower speedup due to PyTorch state serialization costs. ML features and battles show highest speedup as they're stateless.

**Overhead Considerations:**
- Ray task scheduling: ~1ms per task
- Object serialization: ~0.5ms per MB
- PyTorch state_dict serialization: ~2-5ms per brain
- Only parallelize when `organism_count > parallelization_threshold`

**When NOT to Parallelize:**
- Small organism counts (< 50) - overhead exceeds benefit
- Memory pressure situations - ObjectStore at capacity
- Single-core systems - no parallelism benefit

---

## Implementation Order (REVISED PRIORITY)

⚠️ **Critical Insight from Analyses:** Start with lowest-risk, highest-impact areas first.

### Week 1: Foundation + ML Features (LOWEST RISK)
**Priority: Start with pure computation - no state management complexity**

1. Create `reality_simulator/distributed/` module structure
2. Implement `RayManager` with init/shutdown/fallback
3. Add `/ray/*` config paths and CRA integration
4. **Implement ML feature extraction parallelization FIRST** (pure computation, easiest win)
5. Write unit tests for Ray infrastructure
6. Benchmark ML feature extraction speedup

### Week 2: Battle Resolution (MEDIUM RISK)
**Priority: Stateless tasks - ideal Ray pattern**

1. Implement `resolve_battle_remote()` task
2. Integrate into `highlander_protocol.py`
3. Add causation tracking for battle events
4. Benchmark battle resolution speedup
5. Test tournament integrity preserved

### Week 3: Neural Decisions (HIGH COMPLEXITY)
**Priority: Actor-based approach for state management**

1. Implement `OrganismActor` with persistent state
2. Implement `OrganismActorPool` for lifecycle management
3. Add `DistributedStateManager` for state synchronization
4. Integrate into `symbiotic_network.py:update_network()`
5. Benchmark decision speedup (expect 3-4x, not 6-7x)

### Week 4: Distributed Training (HIGHEST COMPLEXITY)
**Priority: Most complex - actor state sync + PyTorch + GPU**

1. Implement `OrganismTrainerActor` with GPU fractional allocation
2. Implement `DistributedExperienceManager` for memory management
3. Modify `trainer.py` to use actor pool
4. Implement state synchronization back to main process
5. Test training convergence matches sequential
6. Benchmark training speedup (expect 2-3x)

### Week 5: Causation & Polish
**Priority: Integration testing and documentation**

1. Implement `DistributedCausationManager` with vector clocks
2. Add comprehensive causation integrity tests
3. Performance profiling and optimization
4. Add Ray dashboard integration
5. Update `system_diagnostics.txt` with Ray section
6. Update `CRA_CAPABILITIES.md` with Ray controls
7. Add Quick Win #13: Ray Distributed Computing

---

## Open Questions (UPDATED)

### ✅ RESOLVED:

1. **GPU distribution strategy?** 
   - **RESOLVED:** Single GPU with CPU parallelization
   - Keep all PyTorch on single GPU, use fractional allocation (`num_gpus=0.1`)
   - Simpler implementation, better memory efficiency, still gets 3-4x speedup

2. **State synchronization?**
   - **RESOLVED:** Breath-cycle state snapshots
   - Create immutable snapshot before parallel work
   - Apply mutations sequentially after parallel results return

3. **Causation event ordering?**
   - **RESOLVED:** Vector clocks + batch sequence numbers
   - Batch events within tasks, use sequence numbers for guaranteed ordering
   - Vector clocks for cross-worker happens-before relationships

4. **Memory management?**
   - **RESOLVED:** Actor pooling with LRU eviction + cleanup on organism death
   - Max object refs limit in config
   - Explicit cleanup when organisms die

### 🔄 STILL OPEN:

1. **Granularity threshold auto-tuning?** 
   - Should `parallelization_threshold` (default 50) be auto-tuned by meta-cognitive system?
   - Could learn optimal threshold based on observed overhead vs benefit
   - **Recommendation:** Start with fixed threshold, add auto-tuning in v2

2. **Multi-node scaling?**
   - Initial implementation: single-node multi-core
   - Future: Ray cluster across machines?
   - Need to consider network latency for shared state
   - **Recommendation:** Design for multi-node but implement single-node first

3. **Checkpointing integration?**
   - OrganismCapsuleManager already checkpoints champions
   - Should Ray actors checkpoint their state independently?
   - Integration with GerminationPool for actor recovery?
   - **Recommendation:** Use existing checkpointing, actors sync back to main process

4. **Monitoring & observability?**
   - Ray Dashboard provides built-in monitoring
   - Should we integrate Ray metrics with existing health monitoring?
   - Add Ray worker stats to diagnostic panels?
   - **Recommendation:** Start with Ray Dashboard, add integration in Week 5

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [ ] ML feature extraction shows 4-5x speedup
- [ ] Battle resolution shows 4-5x speedup
- [ ] Fallback mode works when Ray unavailable
- [ ] No regressions in causation tracking

### Phase 2 Complete When:
- [ ] Neural decisions show 3-4x speedup
- [ ] Training shows 2-3x speedup
- [ ] Actor state synchronization is reliable
- [ ] Memory usage is bounded

### Production Ready When:
- [ ] All speedup targets met
- [ ] Causation integrity tests pass
- [ ] 48-hour stability test passes
- [ ] Documentation complete
- [ ] CRA controls functional
