"""
AgentRuntime - Self-Contained Living Agent

This is the core of the portable agent system. It encapsulates everything
needed to make an organism "alive":
- Neural brain (decision making)
- Experience buffer (memory)
- Internal state (resources, health, position, social standing)
- Perception pipeline (state feature extraction)
- Learning capability (can adapt to new environments)

Unlike a static snapshot, this agent can:
- Perceive its environment
- Make decisions based on learned behavior
- Remember experiences
- Continue learning
- Maintain internal state across episodes
"""

import numpy as np
import json
import pickle
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
import random

from .perception import PerceptionPipeline


@dataclass
class AgentState:
    """Internal state that makes the agent 'alive'."""
    # Identity
    organism_id: str = "exported_agent"
    generation: int = 0
    age: int = 0
    
    # Survival metrics
    fitness: float = 0.5
    fitness_history: List[float] = field(default_factory=list)
    resources: float = 100.0
    health: float = 1.0
    
    # Position in environment
    position: Tuple[float, float] = (0.0, 0.0)
    
    # Social state
    alliance_reputation: float = 0.5
    battle_wins: int = 0
    battle_losses: int = 0
    
    # Learning state
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    total_steps: int = 0
    total_episodes: int = 0
    total_rewards: float = 0.0
    
    # Language/vocabulary size
    vocabulary_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        d = asdict(self)
        d['position'] = list(self.position)
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'AgentState':
        """Deserialize from dictionary."""
        d = d.copy()
        if 'position' in d:
            d['position'] = tuple(d['position'])
        if 'fitness_history' not in d:
            d['fitness_history'] = []
        return cls(**d)


class ExperienceBuffer:
    """Simple experience replay buffer for learning."""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
    
    def add(self, state: np.ndarray, action: int, reward: float,
            next_state: np.ndarray, done: bool):
        """Add experience to buffer."""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> List[Tuple]:
        """Sample a batch of experiences."""
        batch_size = min(batch_size, len(self.buffer))
        return random.sample(list(self.buffer), batch_size)
    
    def __len__(self) -> int:
        return len(self.buffer)
    
    def to_list(self) -> List[Tuple]:
        """Export buffer contents."""
        return [(s.tolist(), a, r, ns.tolist(), d) for s, a, r, ns, d in self.buffer]
    
    @classmethod
    def from_list(cls, data: List[Tuple], capacity: int = 10000) -> 'ExperienceBuffer':
        """Import buffer from list."""
        buf = cls(capacity)
        for s, a, r, ns, d in data:
            buf.add(np.array(s), a, r, np.array(ns), d)
        return buf


class AgentRuntime:
    """
    Self-contained living agent runtime.
    
    This class provides everything needed to run an organism independently:
    - Decision making (via neural brain or ONNX model)
    - Memory (experience buffer)
    - Internal state (fitness, resources, position, etc.)
    - Perception (convert raw observations to 24D feature vector)
    - Learning (experience replay, epsilon-greedy exploration)
    
    The agent can run in any environment that provides:
    - observations (dict or array)
    - step(action) -> (next_obs, reward, done, info)
    - reset() -> obs
    """
    
    # Action mapping (same as Butterfly System)
    ACTIONS = {
        0: 'move',
        1: 'cooperate', 
        2: 'compete',
        3: 'rest',
        4: 'reproduce',
        5: 'isolate'
    }
    
    def __init__(self,
                 brain_path: Optional[str] = None,
                 state: Optional[AgentState] = None,
                 config: Optional[Dict[str, Any]] = None,
                 perception: Optional[PerceptionPipeline] = None):
        """
        Initialize agent runtime.
        
        Args:
            brain_path: Path to brain model (ONNX, TorchScript, or state_dict)
            state: Initial agent state (or create default)
            config: Configuration overrides
        """
        self.config = config or {}
        self.state = state or AgentState()
        self.brain = None
        self.brain_type = None
        
        # Experience buffer for learning
        buffer_size = self.config.get('buffer_size', 10000)
        self.experience_buffer = ExperienceBuffer(capacity=buffer_size)
        
        # Action/state history (short-term memory)
        self.action_history: deque = deque(maxlen=100)
        self.state_history: deque = deque(maxlen=100)

        # Perception pipeline attaches to state/buffer
        self.perception = perception or PerceptionPipeline(self.state, self.experience_buffer)
        self._sync_perception_context()
        
        # Load brain if provided
        if brain_path:
            self.load_brain(brain_path)

    def _sync_perception_context(self):
        if self.perception:
            self.perception.update_context(self.state, self.experience_buffer)
    
    def load_brain(self, path: str):
        """
        Load neural brain from file.
        
        Supports:
        - .onnx (ONNX Runtime)
        - .pt (TorchScript)
        - .pth (PyTorch state_dict - requires OrganismBrain class)
        """
        path = Path(path)
        
        if path.suffix == '.onnx':
            self._load_onnx(path)
        elif path.suffix == '.pt':
            self._load_torchscript(path)
        elif path.suffix == '.pth':
            self._load_statedict(path)
        else:
            # Try to infer from content
            try:
                self._load_onnx(path)
            except:
                try:
                    self._load_torchscript(path)
                except:
                    raise ValueError(f"Unknown brain format: {path}")
    
    def _load_onnx(self, path: Path):
        """Load ONNX model."""
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if 'CUDAExecutionProvider' in providers:
                self.brain = ort.InferenceSession(str(path), providers=['CUDAExecutionProvider'])
            else:
                self.brain = ort.InferenceSession(str(path), providers=['CPUExecutionProvider'])
            self.brain_type = 'onnx'
            print(f"✓ Loaded ONNX brain from {path}")
        except ImportError:
            raise ImportError("onnxruntime required for ONNX models: pip install onnxruntime")
    
    def _load_torchscript(self, path: Path):
        """Load TorchScript model."""
        try:
            import torch
            self.brain = torch.jit.load(str(path))
            self.brain.eval()
            self.brain_type = 'torchscript'
            print(f"✓ Loaded TorchScript brain from {path}")
        except ImportError:
            raise ImportError("PyTorch required for TorchScript models: pip install torch")
    
    def _load_statedict(self, path: Path):
        """Load PyTorch state_dict (requires OrganismBrain class)."""
        try:
            import torch
            # Try to import OrganismBrain
            try:
                from reality_simulator.neural.brain import OrganismBrain
            except ImportError:
                raise ImportError(
                    "state_dict format requires OrganismBrain class from Butterfly System. "
                    "Use ONNX or TorchScript format for standalone deployment."
                )
            
            # Load state dict and infer architecture
            sd = torch.load(str(path), map_location='cpu', weights_only=False)
            
            def _shape(name, dim):
                return sd[name].shape[dim] if name in sd else None
            
            in_dim = _shape('fc1.weight', 1) or 24
            hid_dim = _shape('fc1.weight', 0) or 64
            out_dim = _shape('fc3.weight', 0) or 6
            
            self.brain = OrganismBrain(
                input_dim=int(in_dim),
                hidden_dim=int(hid_dim),
                output_dim=int(out_dim)
            )
            self.brain.load_state_dict(sd, strict=False)
            self.brain.eval()
            self.brain_type = 'pytorch'
            print(f"✓ Loaded PyTorch brain from {path}")
        except ImportError as e:
            raise ImportError(f"PyTorch required: {e}")
    
    def perceive(self, observation: Any) -> np.ndarray:
        """
        Convert raw observation to 24D feature vector.
        
        This is the perception pipeline that maps any environment's
        observations to the format the brain expects.
        
        Args:
            observation: Raw observation (dict, array, or scalar)
            
        Returns:
            24D normalized feature vector
        """
        if not self.perception:
            self.perception = PerceptionPipeline(self.state, self.experience_buffer)
        return self.perception.process(observation)
    
    def act(self, observation: Any, explore: bool = True) -> int:
        """
        Choose an action given an observation.
        
        Args:
            observation: Raw observation from environment
            explore: Whether to use epsilon-greedy exploration
            
        Returns:
            Action index (0-5)
        """
        # Epsilon-greedy exploration
        if explore and random.random() < self.state.epsilon:
            return random.randint(0, 5)
        
        # Perceive environment
        state = self.perceive(observation)
        
        # Get action from brain
        if self.brain is None:
            # No brain - random action
            return random.randint(0, 5)
        
        if self.brain_type == 'onnx':
            inputs = {self.brain.get_inputs()[0].name: state.reshape(1, -1)}
            outputs = self.brain.run(None, inputs)
            action_probs = outputs[0]
            action = int(np.argmax(action_probs))
            
        elif self.brain_type == 'torchscript':
            import torch
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                output = self.brain(state_tensor)
                # Handle tuple output (action_probs, language_logits) from language-head models
                action_probs = output[0] if isinstance(output, tuple) else output
                action = int(torch.argmax(action_probs).item())
                
        elif self.brain_type == 'pytorch':
            import torch
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                output = self.brain(state_tensor)
                # Handle tuple output (action_probs, language_logits) from language-head models
                action_probs = output[0] if isinstance(output, tuple) else output
                action = int(torch.argmax(action_probs).item())
        else:
            action = random.randint(0, 5)
        
        # Update history
        self.action_history.append(action)
        self.state_history.append(state)
        
        return action
    
    def learn(self, state: Any, action: int, reward: float, 
              next_state: Any, done: bool):
        """
        Learn from experience.
        
        Args:
            state: State before action
            action: Action taken
            reward: Reward received
            next_state: State after action
            done: Whether episode ended
        """
        # Convert to feature vectors
        s = self.perceive(state)
        ns = self.perceive(next_state)
        
        # Store experience
        self.experience_buffer.add(s, action, reward, ns, done)
        
        # Update state
        self.state.total_steps += 1
        self.state.total_rewards += reward
        
        # Update fitness based on reward
        self.state.fitness = np.clip(self.state.fitness + reward * 0.01, 0.0, 1.0)
        self.state.fitness_history.append(self.state.fitness)
        if len(self.state.fitness_history) > 1000:
            self.state.fitness_history = self.state.fitness_history[-1000:]
        
        # Decay epsilon
        if done:
            self.state.total_episodes += 1
            self.state.epsilon = max(
                self.state.epsilon_min,
                self.state.epsilon * self.state.epsilon_decay
            )
    
    def get_action_name(self, action: int) -> str:
        """Get human-readable action name."""
        return self.ACTIONS.get(action, 'unknown')
    
    def save(self, directory: str):
        """
        Save complete agent state to directory.
        
        Creates:
        - state.json: Agent internal state
        - experience_buffer.pkl: Replay memory
        - config.json: Configuration
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        # Save state
        with open(directory / 'state.json', 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
        
        # Save experience buffer
        with open(directory / 'experience_buffer.pkl', 'wb') as f:
            pickle.dump(self.experience_buffer.to_list(), f)
        
        # Save config
        with open(directory / 'config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"✓ Saved agent state to {directory}")
    
    @classmethod
    def load(cls, directory: str, brain_path: Optional[str] = None) -> 'AgentRuntime':
        """
        Load agent from directory.
        
        Args:
            directory: Directory containing saved state
            brain_path: Path to brain model (optional, can be in directory)
            
        Returns:
            Loaded AgentRuntime
        """
        directory = Path(directory)
        
        # Load state
        state = None
        state_path = directory / 'state.json'
        if state_path.exists():
            with open(state_path, 'r') as f:
                state = AgentState.from_dict(json.load(f))
        
        # Load config
        config = {}
        config_path = directory / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Find brain if not specified
        if brain_path is None:
            for ext in ['.onnx', '.pt', '.pth']:
                candidate = directory / f'brain{ext}'
                if candidate.exists():
                    brain_path = str(candidate)
                    break
        
        # Create agent
        agent = cls(brain_path=brain_path, state=state, config=config)
        
        # Load experience buffer
        buffer_path = directory / 'experience_buffer.pkl'
        if buffer_path.exists():
            with open(buffer_path, 'rb') as f:
                buffer_data = pickle.load(f)
                agent.experience_buffer = ExperienceBuffer.from_list(
                    buffer_data, 
                    config.get('buffer_size', 10000)
                )
        
        agent._sync_perception_context()
        print(f"✓ Loaded agent from {directory}")
        return agent
    
    def __repr__(self) -> str:
        return (
            f"AgentRuntime("
            f"id={self.state.organism_id}, "
            f"fitness={self.state.fitness:.3f}, "
            f"steps={self.state.total_steps}, "
            f"episodes={self.state.total_episodes}, "
            f"ε={self.state.epsilon:.3f})"
        )
