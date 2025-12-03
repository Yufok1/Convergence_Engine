"""
Portable Agent - Living Agent Export System

This module provides a self-contained agent runtime that can be exported
from the Butterfly System and run independently in any environment.

Components:
- AgentRuntime: Core living agent with brain, memory, state, and learning
- MiniEnvironment: Embedded survival environment for immediate testing
- GymAdapter: Integration with OpenAI Gym/Gymnasium environments
- Perception: State feature extraction and normalization
- Training: Continued learning capability for adaptation
- Visualize: Neural activation visualization tool (run as `python -m portable_agent.visualize`)

Usage:
    from portable_agent import AgentRuntime, MiniEnvironment
    
    agent = AgentRuntime.load("agent_state.json", "brain.onnx")
    env = MiniEnvironment()
    
    for episode in range(100):
        state = env.reset()
        while not done:
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
    
    # Visualize the agent's neural activations
    # Run: python portable_agent/visualize.py
"""

from .agent_runtime import AgentRuntime
from .mini_environment import MiniEnvironment
from .gym_adapter import GymAdapter
from .perception import PerceptionPipeline
from .training import TrainingLoop

__all__ = [
    'AgentRuntime',
    'MiniEnvironment', 
    'GymAdapter',
    'PerceptionPipeline',
    'TrainingLoop'
]

__version__ = '1.1.0'  # Added neural activation visualizer
