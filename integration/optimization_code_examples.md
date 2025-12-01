# Convergence Engine: Optimization Code Examples & Implementation Patterns

**Quick Reference for Implementation**

---

## 1. Batched Organism Inference (COPY-PASTE READY)

```python
# neural_organism_vectorized.py
import torch
import torch.nn as nn
from typing import Tuple
import numpy as np

class VectorizedOrganismNetwork(nn.Module):
    """Single network shared across population, vectorized forward pass"""
    
    def __init__(self, state_dim: int = 18, hidden_dim: int = 64, 
                 action_dim: int = 6, language_dim: int = 128):
        super().__init__()
        
        # Shared backbone (all organisms use same weights)
        self.shared_backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        
        # Action head (maps to 6 actions)
        self.action_head = nn.Linear(hidden_dim, action_dim)
        
        # Language head (semantic token generation)
        self.language_head = nn.Linear(hidden_dim, language_dim)
        
    def forward(self, batch_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for entire organism population
        
        Args:
            batch_states: (batch_size, state_dim) - all organism states
        
        Returns:
            (actions, language_embeddings)
            - actions: (batch_size, action_dim)
            - language_embeddings: (batch_size, language_dim)
        """
        features = self.shared_backbone(batch_states)
        actions = self.action_head(features)
        language = self.language_head(features)
        
        return actions, language


class PopulationManager:
    """Manages vectorized inference for organism population"""
    
    def __init__(self, network: VectorizedOrganismNetwork, 
                 population_size: int = 1400,
                 device: str = 'cuda'):
        self.network = network.to(device)
        self.device = torch.device(device)
        self.population_size = population_size
        
    def get_population_actions(self, organism_states: np.ndarray) -> np.ndarray:
        """
        Get actions for entire population in single forward pass
        
        Args:
            organism_states: (population_size, state_dim) numpy array
        
        Returns:
            actions: (population_size, action_dim) numpy array
        """
        # Convert to tensor and move to GPU
        states_tensor = torch.from_numpy(organism_states).float().to(self.device)
        
        with torch.no_grad():
            actions, _ = self.network(states_tensor)
        
        # Move back to CPU and convert to numpy
        return actions.cpu().numpy()
    
    def get_population_actions_and_language(self, 
                                           organism_states: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Get both actions and language for entire population"""
        states_tensor = torch.from_numpy(organism_states).float().to(self.device)
        
        with torch.no_grad():
            actions, language = self.network(states_tensor)
        
        return actions.cpu().numpy(), language.cpu().numpy()


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

class RealitySimulator:
    """Modified to use vectorized inference"""
    
    def __init__(self, population_size=1400):
        self.population_size = population_size
        self.network = VectorizedOrganismNetwork(
            state_dim=18, hidden_dim=64, action_dim=6, language_dim=128
        )
        self.population_manager = PopulationManager(
            self.network, population_size, device='cuda'
        )
        self.organisms = []
        
    def decision_cycle(self):
        """Execute single decision cycle for all organisms"""
        
        # Collect states from all organisms into single array
        organism_states = np.array([org.get_state() for org in self.organisms])
        # Shape: (population_size, state_dim)
        
        # VECTORIZED: Single GPU operation instead of 1,400 CPU operations
        actions = self.population_manager.get_population_actions(organism_states)
        
        # Apply actions to all organisms simultaneously
        for i, organism in enumerate(self.organisms):
            organism.action = int(np.argmax(actions[i]))
        
        return actions


# Benchmark comparison
def benchmark_inference():
    import time
    
    network = VectorizedOrganismNetwork()
    manager = PopulationManager(network, population_size=2000)
    
    # Create dummy population
    organism_states = np.random.randn(2000, 18).astype(np.float32)
    
    # Warmup
    for _ in range(3):
        manager.get_population_actions(organism_states)
    
    # Benchmark
    start = time.time()
    for _ in range(100):
        manager.get_population_actions(organism_states)
    duration = time.time() - start
    
    print(f"2000 organisms, 100 iterations: {duration:.3f}s")
    print(f"Per-organism cost: {(duration / 100 / 2000) * 1000:.3f} ms")
    # Expected: ~0.5-1.5 ms per organism (vs 2-5 ms serial)
```

---

## 2. RAPIDS cuML HDBSCAN Migration (DROP-IN REPLACEMENT)

```python
# ml_analysis_gpu.py
import numpy as np
import cupy as cp
from typing import Optional, Tuple

class GPUClusterer:
    """Unified interface for CPU/GPU clustering"""
    
    def __init__(self, use_gpu: bool = True, backend: str = 'cuml'):
        self.use_gpu = use_gpu
        self.backend = backend
        
        if use_gpu:
            try:
                from cuml.cluster import HDBSCAN as cuHDBSCAN
                self.clusterer = cuHDBSCAN(
                    min_cluster_size=6,
                    min_samples=3,
                    cluster_selection_epsilon=0.08,
                    prediction_data=True,  # Enable approximate_predict
                    verbose=0,
                )
                print("✓ Using GPU-accelerated HDBSCAN (cuML)")
            except ImportError:
                print("⚠ cuML not found, falling back to CPU HDBSCAN")
                from hdbscan import HDBSCAN
                self.clusterer = HDBSCAN(
                    min_cluster_size=6,
                    min_samples=3,
                    cluster_selection_epsilon=0.08,
                )
                self.use_gpu = False
        else:
            from hdbscan import HDBSCAN
            self.clusterer = HDBSCAN(
                min_cluster_size=6,
                min_samples=3,
                cluster_selection_epsilon=0.08,
            )
    
    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cluster embeddings
        
        Args:
            embeddings: (n_samples, n_features) array
        
        Returns:
            cluster_labels: (n_samples,) with -1 for noise
        """
        
        if self.use_gpu:
            # Transfer to GPU
            gpu_embeddings = cp.asarray(embeddings, dtype=cp.float32)
            
            # Cluster on GPU
            labels_gpu = self.clusterer.fit_predict(gpu_embeddings)
            
            # Transfer back to CPU
            labels = cp.asnumpy(labels_gpu)
        else:
            labels = self.clusterer.fit_predict(embeddings)
        
        return labels
    
    def approximate_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fast prediction for new samples without refitting
        
        Use when population changes (births/deaths) between cycles
        """
        
        if not hasattr(self.clusterer, 'approximate_predict'):
            raise NotImplementedError("CPU HDBSCAN doesn't support approximate_predict")
        
        if self.use_gpu:
            gpu_embeddings = cp.asarray(embeddings, dtype=cp.float32)
            labels_gpu = self.clusterer.approximate_predict(gpu_embeddings)
            return cp.asnumpy(labels_gpu)
        else:
            return self.clusterer.approximate_predict(embeddings)


class AnomalyDetectorGPU:
    """GPU-accelerated Isolation Forest"""
    
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        
        if use_gpu:
            try:
                from cuml.ensemble import IsolationForest as cuIF
                self.detector = cuIF(
                    n_estimators=450,
                    contamination=0.02,
                    max_samples=512,
                    random_state=42,
                )
                print("✓ Using GPU Isolation Forest (cuML)")
            except ImportError:
                print("⚠ cuML not found, using CPU Isolation Forest")
                from sklearn.ensemble import IsolationForest
                self.detector = IsolationForest(
                    n_estimators=450,
                    contamination=0.02,
                    max_samples=512,
                    random_state=42,
                )
                self.use_gpu = False
        else:
            from sklearn.ensemble import IsolationForest
            self.detector = IsolationForest(
                n_estimators=450,
                contamination=0.02,
                max_samples=512,
                random_state=42,
            )
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Detect anomalies
        
        Returns:
            predictions: (n_samples,) with -1 for anomalies, 1 for normal
        """
        
        if self.use_gpu:
            X_gpu = cp.asarray(X, dtype=cp.float32)
            preds_gpu = self.detector.predict(X_gpu)
            return cp.asnumpy(preds_gpu).astype(np.int32)
        else:
            return self.detector.predict(X)


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

class MLAnalysisPipeline:
    """Replace existing ml_analysis.py with this"""
    
    def __init__(self, use_gpu: bool = True):
        self.clusterer = GPUClusterer(use_gpu=use_gpu)
        self.anomaly_detector = AnomalyDetectorGPU(use_gpu=use_gpu)
        self.use_gpu = use_gpu
        
        # Caching to avoid clustering every cycle
        self.last_cluster_cycle = 0
        self.cluster_update_frequency = 10
        self.cached_clusters = None
        
    def analyze_cycle(self, cycle: int, organism_embeddings: np.ndarray) -> dict:
        """
        Run ML analysis on population
        
        Args:
            cycle: simulation cycle number
            organism_embeddings: (population_size, embedding_dim) array
        
        Returns:
            dict with:
            - 'clusters': cluster labels
            - 'anomalies': anomaly predictions
            - 'timing': dict with timing info
        """
        
        import time
        timings = {}
        
        # Cluster every N cycles (amortize cost)
        if (cycle - self.last_cluster_cycle) >= self.cluster_update_frequency:
            start = time.time()
            clusters = self.clusterer.fit_predict(organism_embeddings)
            timings['clustering_ms'] = (time.time() - start) * 1000
            
            self.cached_clusters = clusters
            self.last_cluster_cycle = cycle
        else:
            clusters = self.cached_clusters
            timings['clustering_ms'] = 0  # Cached
        
        # Anomaly detection every cycle
        start = time.time()
        anomalies = self.anomaly_detector.predict(organism_embeddings)
        timings['anomaly_detection_ms'] = (time.time() - start) * 1000
        
        return {
            'clusters': clusters,
            'anomalies': anomalies,
            'timings': timings,
        }


# Benchmark
def benchmark_clustering():
    import time
    
    pipeline = MLAnalysisPipeline(use_gpu=True)
    
    # Create dummy population
    embeddings = np.random.randn(4000, 64).astype(np.float32)
    
    # Benchmark
    times = []
    for i in range(5):
        start = time.time()
        pipeline.analyze_cycle(i, embeddings)
        times.append(time.time() - start)
    
    print(f"GPU clustering average: {np.mean(times[1:]) * 1000:.1f} ms")
    # Expected: 30-100 ms with cuML (vs 500ms-2s with CPU HDBSCAN)
```

---

## 3. Prioritized Experience Replay with torchrl

```python
# dqn_agent_prioritized.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchrl.data import ReplayBuffer, PrioritizedSampler, ListStorage
from torch.optim import Adam
from copy import deepcopy
import numpy as np

class DQNAgentPrioritized:
    """DQN with prioritized experience replay"""
    
    def __init__(self, state_dim: int = 18, action_dim: int = 6,
                 buffer_size: int = 40000, batch_size: int = 128,
                 learning_rate: float = 1e-4):
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.batch_size = batch_size
        self.gamma = 0.99
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Q-Network
        self.q_network = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
        ).to(self.device)
        
        self.target_network = deepcopy(self.q_network)
        self.optimizer = Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Prioritized Replay Buffer
        self.replay_buffer = ReplayBuffer(
            storage=ListStorage(max_size=buffer_size),
            sampler=PrioritizedSampler(
                max_capacity=buffer_size,
                alpha=0.6,  # Prioritization exponent
                beta=0.4,   # Importance sampling exponent
            ),
            batch_size=batch_size,
            prefetch=4,  # Pre-fetch batches
        )
        
        self.alpha = 0.6
        self.beta = 0.4
        self.update_steps = 0
        self.max_update_steps = 100000
        
    def store_experience(self, state: np.ndarray, action: int, 
                        reward: float, next_state: np.ndarray, done: bool):
        """Add experience to replay buffer"""
        
        experience = {
            'state': torch.tensor(state, dtype=torch.float32),
            'action': torch.tensor([action], dtype=torch.long),
            'reward': torch.tensor([reward], dtype=torch.float32),
            'next_state': torch.tensor(next_state, dtype=torch.float32),
            'done': torch.tensor([done], dtype=torch.float32),
        }
        
        self.replay_buffer.extend([experience])
    
    def select_action(self, state: np.ndarray, epsilon: float = 0.0) -> int:
        """Select action (e-greedy)"""
        
        if np.random.random() < epsilon:
            return np.random.randint(self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor)
            return q_values.argmax(1).item()
    
    def train_step(self) -> float:
        """Single training iteration with prioritized sampling"""
        
        if len(self.replay_buffer) < self.batch_size:
            return 0.0
        
        # Sample prioritized batch
        batch, info = self.replay_buffer.sample(return_info=True)
        
        # Unpack batch
        states = batch['state'].to(self.device)
        actions = batch['action'].squeeze(1).to(self.device)
        rewards = batch['reward'].squeeze(1).to(self.device)
        next_states = batch['next_state'].to(self.device)
        dones = batch['done'].squeeze(1).to(self.device)
        
        # Importance weights for prioritized sampling
        weights = info['weights'].to(self.device)
        indices = info['index'].to(self.device)
        
        # Compute Q(s, a)
        q_values = self.q_network(states)
        q_selected = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Compute Q_target(s', a)
        with torch.no_grad():
            next_q_values = self.target_network(next_states)
            max_next_q = next_q_values.max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * max_next_q
        
        # TD Error for priority update
        td_error = (target_q - q_selected).detach().abs()
        
        # Weighted MSE Loss (importance sampling correction)
        loss = (weights * (target_q - q_selected) ** 2).mean()
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # Update priorities (important for next sampling)
        priorities = (td_error + 1e-6) ** self.alpha
        self.replay_buffer.update_priority(index=indices, priority=priorities)
        
        # Anneal beta (increase importance sampling correction)
        self.beta = min(1.0, self.beta + 1e-5)
        
        # Soft target update
        tau = 0.005
        for target_param, param in zip(self.target_network.parameters(),
                                       self.q_network.parameters()):
            target_param.data.copy_(tau * param.data + (1.0 - tau) * target_param.data)
        
        self.update_steps += 1
        
        return loss.item()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def train_episode(agent: DQNAgentPrioritized, env, max_steps: int = 500) -> float:
    """Train agent for one episode"""
    
    state, _ = env.reset()
    total_reward = 0.0
    
    for step in range(max_steps):
        # Select action with epsilon-decay
        epsilon = 0.1 * (1 - min(1.0, agent.update_steps / 100000))
        action = agent.select_action(state, epsilon)
        
        # Take step in environment
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        
        # Store experience
        agent.store_experience(state, action, reward, next_state, done)
        
        # Training step
        loss = agent.train_step()
        
        total_reward += reward
        state = next_state
        
        if done:
            break
    
    return total_reward
```

---

## 4. torch.compile() Integration (EXPERIMENTAL)

```python
# neural_organism_compiled.py
import torch
import torch.nn as nn
from typing import Tuple

class CompiledOrganismNetwork(nn.Module):
    """Network optimized with torch.compile()"""
    
    def __init__(self, state_dim: int = 18, hidden_dim: int = 64,
                 action_dim: int = 6, language_dim: int = 128,
                 use_compile: bool = True):
        super().__init__()
        
        self.state_dim = state_dim
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        self.action_head = nn.Linear(hidden_dim, action_dim)
        self.language_head = nn.Linear(hidden_dim, language_dim)
        
        if use_compile:
            # Compile with careful settings
            self.forward_compiled = torch.compile(
                self._forward_impl,
                mode='default',  # 'default', 'reduce-overhead', 'max-autotune'
                dynamic=False,   # False if batch size is fixed
            )
        else:
            self.forward_compiled = None
    
    def _forward_impl(self, batch_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Core forward logic"""
        features = self.backbone(batch_states)
        actions = self.action_head(features)
        language = self.language_head(features)
        return actions, language
    
    def forward(self, batch_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.forward_compiled is not None:
            return self.forward_compiled(batch_states)
        else:
            return self._forward_impl(batch_states)


# Debugging torch.compile issues
class CompileDebugger:
    """Help diagnose torch.compile problems"""
    
    @staticmethod
    def check_compilation(model: nn.Module, test_input: torch.Tensor):
        """Test model compilation and report issues"""
        
        import os
        import logging
        
        # Enable detailed logging
        os.environ['TORCH_LOGS'] = 'dynamo,bytecode'
        os.environ['TORCH_LOGS_OUT'] = 'compile_debug.log'
        
        logging.basicConfig(level=logging.DEBUG)
        
        # Compile and test
        try:
            compiled_model = torch.compile(model, mode='default')
            output = compiled_model(test_input)
            print("✓ Compilation successful")
            return output
        except Exception as e:
            print(f"✗ Compilation failed: {e}")
            print("Check compile_debug.log for details")
            return None
    
    @staticmethod
    def compare_performance(model: nn.Module, test_input: torch.Tensor, 
                           num_runs: int = 100):
        """Compare eager vs compiled performance"""
        
        import time
        
        # Warm up
        model(test_input)
        
        # Eager mode
        start = time.time()
        for _ in range(num_runs):
            model(test_input)
        eager_time = (time.time() - start) / num_runs
        
        # Compiled mode
        compiled_model = torch.compile(model, mode='default')
        
        # Warmup (compilation happens here)
        compiled_model(test_input)
        
        start = time.time()
        for _ in range(num_runs):
            compiled_model(test_input)
        compiled_time = (time.time() - start) / num_runs
        
        speedup = eager_time / compiled_time
        
        print(f"Eager mode: {eager_time * 1000:.3f} ms")
        print(f"Compiled mode: {compiled_time * 1000:.3f} ms")
        print(f"Speedup: {speedup:.2f}×")
        
        return speedup
```

---

## 5. Automatic Mixed Precision (AMP) for Inference

```python
# neural_organism_amp.py
import torch
import torch.nn as nn
from torch.cuda.amp import autocast

class AMPOrganismNetwork(nn.Module):
    """Network optimized with Automatic Mixed Precision"""
    
    def __init__(self, state_dim: int = 18, hidden_dim: int = 64,
                 action_dim: int = 6, use_amp: bool = True):
        super().__init__()
        
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        self.action_head = nn.Linear(hidden_dim, action_dim)
        self.language_head = nn.Linear(hidden_dim, 128)
        self.use_amp = use_amp and torch.cuda.is_available()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)
    
    def forward_inference(self, batch_states: torch.Tensor):
        """Inference with automatic mixed precision"""
        
        batch_states = batch_states.to(self.device)
        
        if self.use_amp:
            with torch.no_grad():
                with autocast(device_type='cuda', dtype=torch.float16):
                    features = self.backbone(batch_states)
                    actions = self.action_head(features)
                    language = self.language_head(features)
        else:
            with torch.no_grad():
                features = self.backbone(batch_states)
                actions = self.action_head(features)
                language = self.language_head(features)
        
        return actions, language
    
    def forward_training(self, batch_states: torch.Tensor, 
                        target_actions: torch.Tensor):
        """Training with mixed precision"""
        
        batch_states = batch_states.to(self.device)
        target_actions = target_actions.to(self.device)
        
        if self.use_amp:
            with autocast(device_type='cuda', dtype=torch.float16):
                features = self.backbone(batch_states)
                pred_actions = self.action_head(features)
                loss = nn.functional.mse_loss(pred_actions, target_actions)
        else:
            features = self.backbone(batch_states)
            pred_actions = self.action_head(features)
            loss = nn.functional.mse_loss(pred_actions, target_actions)
        
        return loss
```

---

## 6. Combined Optimization: Batching + AMP + torch.compile()

```python
# neural_organism_full_optimization.py
import torch
import torch.nn as nn
from torch.cuda.amp import autocast

class FullyOptimizedOrganismNetwork(nn.Module):
    """All optimizations combined"""
    
    def __init__(self, state_dim: int = 18, hidden_dim: int = 64,
                 action_dim: int = 6,
                 use_amp: bool = True,
                 use_compile: bool = False):
        super().__init__()
        
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        self.action_head = nn.Linear(hidden_dim, action_dim)
        self.language_head = nn.Linear(hidden_dim, 128)
        
        self.use_amp = use_amp and torch.cuda.is_available()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)
        
        if use_compile:
            self._forward_impl = torch.compile(
                self._forward_impl,
                mode='default',
                dynamic=False,
            )
    
    def _forward_impl(self, batch_states: torch.Tensor):
        """Core forward logic (gets compiled if use_compile=True)"""
        features = self.backbone(batch_states)
        actions = self.action_head(features)
        language = self.language_head(features)
        return actions, language
    
    def forward(self, batch_states: torch.Tensor):
        """Forward with automatic mixed precision wrapper"""
        batch_states = batch_states.to(self.device)
        
        if self.use_amp:
            with autocast(device_type='cuda', dtype=torch.float16):
                return self._forward_impl(batch_states)
        else:
            return self._forward_impl(batch_states)


# Benchmark all optimizations
def benchmark_all_optimizations():
    import time
    import numpy as np
    
    batch_size = 2000
    state_dim = 18
    num_runs = 100
    
    test_input = torch.randn(batch_size, state_dim, device='cuda')
    
    configs = [
        ('Baseline (eager)', {'use_amp': False, 'use_compile': False}),
        ('+ AMP', {'use_amp': True, 'use_compile': False}),
        ('+ compile', {'use_amp': False, 'use_compile': True}),
        ('+ AMP + compile', {'use_amp': True, 'use_compile': True}),
    ]
    
    results = []
    
    for name, config in configs:
        model = FullyOptimizedOrganismNetwork(**config)
        model.eval()
        
        # Warmup
        for _ in range(5):
            model(test_input)
        
        # Benchmark
        torch.cuda.synchronize()
        start = time.time()
        for _ in range(num_runs):
            model(test_input)
        torch.cuda.synchronize()
        duration = (time.time() - start) / num_runs
        
        results.append((name, duration * 1000))
        print(f"{name}: {duration * 1000:.3f} ms")
    
    # Calculate speedups relative to baseline
    baseline = results[0][1]
    for name, duration in results:
        speedup = baseline / duration
        print(f"{name}: {speedup:.2f}× speedup")
```

---

## 7. Configuration Helper

```python
# optimization_config.py
from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class OptimizationConfig:
    """Central configuration for all optimizations"""
    
    # Batching
    use_batched_inference: bool = True
    batch_size_organism_inference: int = 1400
    
    # Neural network
    use_mixed_precision: bool = True
    use_torch_compile: bool = False
    torch_compile_mode: str = 'default'
    
    # Clustering
    use_gpu_clustering: bool = True
    clustering_update_frequency: int = 10
    
    # Replay buffer
    use_prioritized_replay: bool = True
    replay_buffer_size: int = 40000
    prioritization_alpha: float = 0.6
    importance_sampling_beta: float = 0.4
    
    def to_dict(self) -> dict:
        return self.__dict__
    
    def to_json(self, filename: str):
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_json(cls, filename: str):
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.batch_size_organism_inference <= 0:
            raise ValueError("batch_size_organism_inference must be positive")
        if not 0 <= self.prioritization_alpha <= 1:
            raise ValueError("prioritization_alpha must be in [0, 1]")
        if not 0 <= self.importance_sampling_beta <= 1:
            raise ValueError("importance_sampling_beta must be in [0, 1]")
        return True


# Usage
config = OptimizationConfig(
    use_batched_inference=True,
    use_mixed_precision=True,
    use_torch_compile=False,  # Set to True after validation
    use_gpu_clustering=True,
)

config.to_json('optimization_config.json')
```

---

## Performance Profiling Utilities

```python
# performance_profiler.py
import torch
import time
import numpy as np
from contextlib import contextmanager

class PerformanceProfiler:
    """Track performance metrics across simulation"""
    
    def __init__(self):
        self.metrics = {}
    
    @contextmanager
    def profile(self, name: str):
        """Context manager for timing"""
        start = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start) * 1000
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(duration)
    
    def report(self, window_size: int = 100):
        """Print performance report"""
        print("\n" + "=" * 60)
        print("Performance Report")
        print("=" * 60)
        
        for name, times in self.metrics.items():
            if len(times) >= window_size:
                recent = times[-window_size:]
            else:
                recent = times
            
            mean = np.mean(recent)
            std = np.std(recent)
            min_t = np.min(recent)
            max_t = np.max(recent)
            
            print(f"{name:30s}: {mean:8.3f} ms "
                  f"(σ={std:6.3f}, min={min_t:6.3f}, max={max_t:6.3f})")
        
        print("=" * 60 + "\n")
    
    def reset(self):
        """Clear metrics"""
        self.metrics = {}


# Usage in simulation
profiler = PerformanceProfiler()

# In main loop
with profiler.profile('organism_inference'):
    actions = population_manager.get_population_actions(organism_states)

with profiler.profile('clustering'):
    clusters = ml_analyzer.cluster_organisms(embeddings)

with profiler.profile('training_step'):
    loss = dqn_agent.train_step()

profiler.report(window_size=100)
```

---

**End of Code Examples**

Use these patterns to incrementally optimize your Convergence Engine. Start with batched inference, then add GPU clustering, then prioritized replay.

