"""
Adapters that let the portable agent interact with Gym / Gymnasium
environments without the user having to write boilerplate.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


class GymAdapter:
    """Normalizes Gym style APIs and provides a simple training helper."""

    def __init__(self, env: Any, max_steps: Optional[int] = None):
        self.env = env
        self.max_steps = max_steps

    def reset(self) -> Tuple[Any, Dict[str, Any]]:
        """Supports both Gymnasium (obs, info) and legacy Gym (obs)."""
        result = self.env.reset()
        if isinstance(result, tuple) and len(result) == 2:
            observation, info = result
        else:  # Legacy API
            observation, info = result, {}
        return observation, info

    def step(self, action: int) -> Tuple[Any, float, bool, Dict[str, Any]]:
        """Normalize step outputs to (obs, reward, done, info)."""
        result = self.env.step(action)
        if isinstance(result, tuple) and len(result) == 5:
            obs, reward, terminated, truncated, info = result
            done = bool(terminated or truncated)
        else:  # Legacy API returns 4 values
            obs, reward, done, info = result
        return obs, float(reward), bool(done), info

    def run_episode(self,
                    agent,
                    explore: bool = True,
                    learn: bool = True,
                    render: bool = False) -> Dict[str, Any]:
        """Convenience loop for quick experiments inside Gym environments."""
        observation, info = self.reset()
        done = False
        total_reward = 0.0
        steps = 0
        max_steps = self.max_steps or getattr(self.env, "max_episode_steps", None)

        while not done:
            if max_steps is not None and steps >= max_steps:
                break

            action = agent.act(observation, explore=explore)
            next_obs, reward, done, info = self.step(action)
            if learn:
                agent.learn(observation, action, reward, next_obs, done)
            observation = next_obs
            total_reward += reward
            steps += 1

            if render and hasattr(self.env, "render"):
                self.env.render()

        return {
            'steps': steps,
            'total_reward': total_reward,
            'terminated': done,
            'info': info
        }