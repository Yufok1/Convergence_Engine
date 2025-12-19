"""
Perception pipeline utilities for the portable agent runtime.

The exported agent needs a consistent 28D feature vector regardless of the
source environment. This module centralizes the transformation logic so the
runtime, Gym adapter, and future integrations can share the same behavior.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # Avoid circular imports at runtime
    from .agent_runtime import AgentState, ExperienceBuffer


class PerceptionPipeline:
    """Converts arbitrary observations into 28D feature vectors."""

    def __init__(self,
                 agent_state: Optional["AgentState"] = None,
                 experience_buffer: Optional["ExperienceBuffer"] = None):
        self.agent_state = agent_state
        self.experience_buffer = experience_buffer

    def update_context(self,
                       agent_state: Optional["AgentState"],
                       experience_buffer: Optional["ExperienceBuffer"] = None) -> None:
        """Attach runtime state so derived features stay in sync."""
        self.agent_state = agent_state
        if experience_buffer is not None:
            self.experience_buffer = experience_buffer

    def __call__(self, observation: Any) -> np.ndarray:
        return self.process(observation)

    def process(self, observation: Any) -> np.ndarray:
        """Return a normalized 28D feature vector (matches config.json input_dim=28)."""
        features = np.zeros(28, dtype=np.float32)
        state = self.agent_state
        buffer = self.experience_buffer

        if isinstance(observation, dict):
            features[0] = float(observation.get('fitness', getattr(state, 'fitness', 0.5)))
            features[1] = float(observation.get('resources', getattr(state, 'resources', 100.0))) / 200.0
            features[2] = float(observation.get('connections', 0)) / 20.0
            features[3] = float(observation.get('neighbor_fitness', 0.5))
            features[4] = float(observation.get('flow_in', 0)) / 10.0
            features[5] = float(observation.get('flow_out', 0)) / 10.0
            features[6] = float(observation.get('clustering', 0.5))
            features[7] = float(observation.get('distance', 1.0))
            features[8] = float(observation.get('age', getattr(state, 'age', 0))) / 1000.0
            features[9] = float(observation.get('parent_fitness', getattr(state, 'fitness', 0.5)))
            features[10] = float(observation.get('breath_phase', 0.5))
            features[11] = float(observation.get('breath_depth', 0.5))
            features[12] = float(observation.get('trait_divergence', 0))
            features[13] = float(observation.get('network_coherence', 0))
            features[14] = float(observation.get('quantum_entropy', 0))
            features[15] = float(observation.get('evolution_pressure', 0))
            features[16] = float(observation.get('phase_mismatch', 0))
            features[17] = float(observation.get('system_health', 0.5))

            if state:
                total_battles = state.battle_wins + state.battle_losses
                features[18] = state.battle_wins / total_battles if total_battles else 0.5
                features[19] = state.alliance_reputation
                features[20] = np.log1p(state.vocabulary_size) / np.log1p(65536)
            else:
                features[18:21] = 0.5

            features[21] = float(observation.get('density', 0.5))
            if buffer:
                features[22] = len(buffer) / buffer.capacity
            else:
                features[22] = 0.0

            if state and state.fitness_history:
                if len(state.fitness_history) >= 3:
                    recent = float(np.mean(state.fitness_history[-3:]))
                    older_hist = state.fitness_history[:-3]
                    older = float(np.mean(older_hist)) if older_hist else state.fitness_history[0]
                    features[23] = 0.5 + (recent - older) / (abs(older) + 0.01)
                else:
                    features[23] = 0.5
            else:
                features[23] = 0.5
            
            # Feature 24: Reserved / VP pressure proxy
            features[24] = float(observation.get('vp_pressure', 0.5))
            
            # Feature 25-26: Self-perception (oscillation_entropy, coherence_frequency)
            # These let the agent sense its own stability and coherence
            features[25] = float(observation.get('oscillation_entropy', 0.0))  # Chaos/stability self-sense
            features[26] = float(observation.get('coherence_frequency', 0.0))  # Trap/freedom self-sense
            
            # Feature 27: Attractor proximity (distance to nearest known stable configuration)
            features[27] = float(observation.get('attractor_proximity', 0.5))  # Collective stability sense

        elif isinstance(observation, (list, np.ndarray)):
            obs = np.array(observation, dtype=np.float32).flatten()
            features[:min(len(obs), 28)] = obs[:28]
        else:
            features[0] = float(observation)

        return np.clip(features, 0.0, 1.0)
