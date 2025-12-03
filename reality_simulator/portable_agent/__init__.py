"""
Portable Agent - Living Agent Export System

This module provides a self-contained agent runtime that can be exported
from the Butterfly System and run independently in any environment.

Components:
- AgentRuntime: Core living agent with brain, memory, state, and learning
- AgentBridge: Universal interface (Gym, HTTP API, CLI, Python integration)
- MiniEnvironment: Embedded survival environment for immediate testing
- GymAdapter: Integration with OpenAI Gym/Gymnasium environments
- Perception: State feature extraction and normalization
- Training: Continued learning capability for adaptation
- Visualize: Neural activation visualization tool (run as `python -m portable_agent.visualize`)

Usage:
    # Method 1: Direct runtime
    from portable_agent import AgentRuntime, MiniEnvironment
    agent = AgentRuntime.load("agent_state.json", "brain.onnx")
    
    # Method 2: Universal bridge (RECOMMENDED)
    from portable_agent import AgentBridge
    bridge = AgentBridge.load("./exported_agent")
    
    # Run in Gym environment
    bridge.run_gym("CartPole-v1", episodes=10)
    
    # Start HTTP API server
    bridge.serve(port=8080)
    
    # Interactive chat mode
    bridge.interactive()
    
    # Direct Python integration
    result = bridge.process(text="Enemy approaching", context={"threat": 0.8})
    print(result.action, result.response, result.confidence)
"""

from .agent_runtime import AgentRuntime
from .mini_environment import MiniEnvironment
from .gym_adapter import GymAdapter
from .perception import PerceptionPipeline
from .training import TrainingLoop
from .bridge import AgentBridge, BridgeResult, AgentConfig

__all__ = [
    'AgentRuntime',
    'AgentBridge',
    'BridgeResult',
    'AgentConfig',
    'MiniEnvironment', 
    'GymAdapter',
    'PerceptionPipeline',
    'TrainingLoop'
]

__version__ = '2.0.0'  # Major update: AgentBridge universal interface
