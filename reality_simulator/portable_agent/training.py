"""
High-level training utilities for the exported agent.

The goal is to let users fine-tune or continue training the organism inside
MiniEnvironment, Gym, or any custom environment with minimal setup.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class TrainingLoop:
    """Simple episodic training harness."""

    def __init__(self,
                 agent,
                 environment,
                 episodes: int = 10,
                 max_steps: Optional[int] = None,
                 explore: bool = True,
                 learn: bool = True,
                 callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None):
        self.agent = agent
        self.env = environment
        self.episodes = episodes
        self.max_steps = max_steps
        self.explore = explore
        self.learn = learn
        self.callbacks = callbacks or []

    def _reset_env(self) -> Any:
        result = self.env.reset()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0]
        return result

    def _step_env(self, action: int):
        result = self.env.step(action)
        if isinstance(result, tuple) and len(result) == 4:
            return result
        if isinstance(result, tuple) and len(result) == 5:
            obs, reward, terminated, truncated, info = result
            return obs, reward, bool(terminated or truncated), info
        raise ValueError("Environment step must return 4 or 5 values.")

    def run(self) -> List[Dict[str, Any]]:
        history: List[Dict[str, Any]] = []
        for episode in range(self.episodes):
            observation = self._reset_env()
            done = False
            total_reward = 0.0
            steps = 0
            episode_info: Dict[str, Any] = {
                'episode': episode,
                'steps': 0,
                'total_reward': 0.0,
            }

            while not done:
                if self.max_steps is not None and steps >= self.max_steps:
                    break

                action = self.agent.act(observation, explore=self.explore)
                next_obs, reward, done, info = self._step_env(action)
                if self.learn:
                    self.agent.learn(observation, action, reward, next_obs, done)
                observation = next_obs
                total_reward += reward
                steps += 1
                if isinstance(info, dict):
                    episode_info.update(info)

            episode_info['steps'] = steps
            episode_info['total_reward'] = total_reward
            history.append(episode_info)

            for cb in self.callbacks:
                cb(episode_info)

        return history
