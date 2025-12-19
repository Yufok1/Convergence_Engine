"""
🧠 LANGUAGE-GAME BRIDGE

The Missing Link: Connects the linguistic/semantic systems with game/ML systems.

CURRENT STATE (The Gap):
    - Organisms have 400+ atomic concepts with learned magnetism
    - Organisms have 62,000+ knowledge web concepts with relations
    - Organisms play gym games (CartPole, drones, etc.)
    - BUT: These systems are DISCONNECTED!
    
THE INSIGHT:
    When an organism plays a game, it should:
    1. Use its vocabulary to interpret observations ("enemy close" → "threat" concept)
    2. Let concept strengths bias action selection ("aggressive" strong → favor COMPETE)
    3. Update concept magnetism based on game outcomes (win → strengthen "victory")
    4. Build new associations from game experience ("evade + enemy + survive" → new link)

THIS MODULE BRIDGES THE GAP:
    1. ObservationInterpreter: Maps game obs → activated concepts
    2. ConceptActionBias: Biases neural action selection using language
    3. OutcomeLearner: Updates language from game results  
    4. GameExperienceEncoder: Converts game episodes to linguistic memory

The result: Language and games MUTUALLY REINFORCE each other.
    - Better vocabulary → better game performance (strategy, planning)
    - Game experience → richer vocabulary (learned concepts, associations)
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONCEPT ACTIVATION FROM GAME STATE
# =============================================================================

@dataclass
class ActivatedConcepts:
    """Concepts activated by interpreting game state."""
    primary: List[str] = field(default_factory=list)      # Main concepts (high confidence)
    secondary: List[str] = field(default_factory=list)    # Related concepts (lower confidence)
    action_hints: Dict[int, float] = field(default_factory=dict)  # Action → weight boost
    urgency: float = 0.5  # How urgent the situation (affects action bias strength)


class ObservationInterpreter:
    """
    Interprets game observations through the lens of vocabulary.
    
    Maps raw numerical observations to activated linguistic concepts.
    This is how an organism "thinks about" what it's observing.
    """
    
    # Semantic patterns for drone/game observations
    # These map observation features to concept activations
    DRONE_PATTERNS = {
        # Position/movement
        'high_altitude': (['height', 'fly', 'above', 'sky'], lambda obs: obs[2] > 0.7 if len(obs) > 2 else False),
        'low_altitude': (['ground', 'danger', 'crash', 'low'], lambda obs: obs[2] < 0.2 if len(obs) > 2 else False),
        'fast_movement': (['speed', 'fast', 'rush', 'velocity'], lambda obs: np.linalg.norm(obs[3:6]) > 0.5 if len(obs) > 5 else False),
        
        # Tactical
        'enemy_close': (['enemy', 'threat', 'attack', 'danger', 'target'], lambda obs: obs[13] < 0.2 if len(obs) > 13 else False),
        'enemy_far': (['safe', 'distant', 'pursue', 'hunt'], lambda obs: obs[13] > 0.7 if len(obs) > 13 else False),
        'ally_close': (['friend', 'ally', 'team', 'cooperate', 'formation'], lambda obs: obs[12] < 0.3 if len(obs) > 12 else False),
        'outnumbered': (['outnumber', 'retreat', 'evade', 'escape'], lambda obs: obs[15] > obs[14] + 0.2 if len(obs) > 15 else False),
        'advantage': (['advantage', 'attack', 'push', 'dominate'], lambda obs: obs[14] > obs[15] + 0.2 if len(obs) > 15 else False),
        
        # Health
        'low_health': (['damage', 'hurt', 'heal', 'careful', 'retreat'], lambda obs: obs[16] < 0.3 if len(obs) > 16 else False),
        'healthy': (['strong', 'power', 'attack', 'confident'], lambda obs: obs[16] > 0.7 if len(obs) > 16 else False),
        'just_tagged': (['tagged', 'hit', 'evade', 'escape', 'retreat'], lambda obs: obs[17] > 0.5 if len(obs) > 17 else False),
    }
    
    # Patterns for gym games (CartPole, etc.)
    GYM_PATTERNS = {
        'falling_left': (['fall', 'left', 'push', 'balance'], lambda obs: obs[2] < -0.1 if len(obs) > 2 else False),
        'falling_right': (['fall', 'right', 'push', 'balance'], lambda obs: obs[2] > 0.1 if len(obs) > 2 else False),
        'stable': (['stable', 'balance', 'steady', 'maintain'], lambda obs: abs(obs[2]) < 0.05 if len(obs) > 2 else False),
        'edge_left': (['edge', 'danger', 'center', 'move'], lambda obs: obs[0] < -0.5 if len(obs) > 0 else False),
        'edge_right': (['edge', 'danger', 'center', 'move'], lambda obs: obs[0] > 0.5 if len(obs) > 0 else False),
    }
    
    def __init__(self, atomic_language=None, knowledge_web=None, context: str = "drone"):
        """
        Args:
            atomic_language: The organism's AtomicLanguageSystem
            knowledge_web: The organism's SemanticKnowledgeWeb
            context: Game context ("drone", "gym", "sphere")
        """
        self.atomic_language = atomic_language
        self.knowledge_web = knowledge_web
        self.context = context
        self.patterns = self.DRONE_PATTERNS if context == "drone" else self.GYM_PATTERNS
        
    def interpret(self, observation: np.ndarray) -> ActivatedConcepts:
        """
        Interpret observation through vocabulary.
        
        Returns activated concepts based on what patterns match.
        """
        activated = ActivatedConcepts()
        
        # Check each pattern
        matched_patterns = []
        for pattern_name, (concepts, condition) in self.patterns.items():
            try:
                if condition(observation):
                    matched_patterns.append(pattern_name)
                    activated.primary.extend(concepts[:2])  # Top 2 concepts
                    activated.secondary.extend(concepts[2:])  # Rest
            except (IndexError, TypeError):
                pass
        
        # Calculate urgency based on patterns
        urgent_patterns = ['enemy_close', 'low_health', 'just_tagged', 'falling_left', 'falling_right', 'edge_left', 'edge_right']
        activated.urgency = min(1.0, sum(0.2 for p in matched_patterns if p in urgent_patterns))
        
        # If we have atomic_language, filter to concepts that exist and are strong
        if self.atomic_language and hasattr(self.atomic_language, 'atoms'):
            strong_concepts = []
            for concept in activated.primary + activated.secondary:
                if concept in self.atomic_language.atoms:
                    atom = self.atomic_language.atoms[concept]
                    if atom.strength > 0.3 or atom.curiosity_magnetism > 0.5:
                        strong_concepts.append(concept)
            activated.primary = strong_concepts[:5]
        
        # Calculate action hints based on activated concepts
        activated.action_hints = self._concepts_to_action_hints(activated.primary)
        
        logger.debug(f"Interpreted obs → {len(activated.primary)} concepts, urgency={activated.urgency:.2f}")
        
        return activated
    
    def _concepts_to_action_hints(self, concepts: List[str]) -> Dict[int, float]:
        """
        Map activated concepts to action biases.
        
        Returns dict of action_index → weight_boost
        """
        # Action semantics:
        # 0: MOVE - forward, pursue, advance
        # 1: COOPERATE - team, ally, formation, protect
        # 2: COMPETE - attack, fight, aggressive, target
        # 3: REST - wait, hover, conserve, heal
        # 4: REPRODUCE - decoy, distract, spawn (contextual)
        # 5: ISOLATE - evade, escape, retreat, hide
        
        action_keywords = {
            0: {'move', 'forward', 'pursue', 'advance', 'push', 'hunt', 'speed', 'fast', 'rush'},
            1: {'cooperate', 'team', 'ally', 'formation', 'friend', 'protect', 'help', 'support'},
            2: {'attack', 'fight', 'aggressive', 'target', 'compete', 'strike', 'dominate', 'enemy'},
            3: {'rest', 'wait', 'hover', 'conserve', 'heal', 'stable', 'maintain', 'balance', 'careful'},
            4: {'decoy', 'distract', 'spawn', 'reproduce', 'confuse'},
            5: {'evade', 'escape', 'retreat', 'hide', 'isolate', 'flee', 'avoid', 'danger', 'safe'},
        }
        
        hints = {i: 0.0 for i in range(6)}
        
        for concept in concepts:
            concept_lower = concept.lower()
            for action, keywords in action_keywords.items():
                if concept_lower in keywords:
                    hints[action] += 0.2
        
        return hints


# =============================================================================
# ACTION SELECTION WITH LANGUAGE BIAS
# =============================================================================

class ConceptActionBias:
    """
    Biases neural action selection using language understanding.
    
    The neural network produces action probabilities.
    This class modifies them based on:
    1. Activated concepts from current observation
    2. Long-term concept magnetism (what the organism has learned to prefer)
    3. Current VP state (risk tolerance)
    """
    
    # Base action preferences for different concept patterns
    CONCEPT_ACTION_MAP = {
        # Tactical concepts
        'aggressive': {2: 0.3, 0: 0.1},      # Bias toward COMPETE and MOVE
        'defensive': {3: 0.2, 5: 0.2},       # Bias toward REST and ISOLATE
        'cautious': {3: 0.3, 5: 0.1},        # Bias toward REST
        'social': {1: 0.4},                  # Strong bias toward COOPERATE
        'cooperative': {1: 0.3, 0: 0.1},     # COOPERATE and MOVE
        'solitary': {5: 0.3},                # Bias toward ISOLATE
        'fast': {0: 0.3, 2: 0.1},            # MOVE and COMPETE
        'patient': {3: 0.4},                 # REST
        
        # Combat concepts
        'attack': {2: 0.4},
        'defend': {3: 0.2, 5: 0.2},
        'evade': {5: 0.4},
        'pursue': {0: 0.3, 2: 0.2},
        'retreat': {5: 0.3, 3: 0.1},
        'coordinate': {1: 0.3},
        
        # State concepts
        'danger': {5: 0.3, 3: 0.1},
        'safe': {2: 0.1, 0: 0.1},
        'threat': {5: 0.2, 2: 0.2},
        'opportunity': {2: 0.3, 0: 0.2},
    }
    
    def __init__(self, atomic_language=None, bias_strength: float = 0.3):
        """
        Args:
            atomic_language: AtomicLanguageSystem for concept strengths
            bias_strength: How strongly to bias (0.0 = no bias, 1.0 = strong bias)
        """
        self.atomic_language = atomic_language
        self.bias_strength = bias_strength
    
    def compute_bias(self, 
                     activated: ActivatedConcepts,
                     vp_value: Optional[float] = None) -> np.ndarray:
        """
        Compute action bias vector from activated concepts.
        
        Args:
            activated: Concepts activated by observation
            vp_value: Current VP (0-1), affects risk tolerance
            
        Returns:
            Bias vector of shape (6,) to ADD to log-probabilities
        """
        bias = np.zeros(6)
        
        # Add hints from observation interpretation
        for action, hint in activated.action_hints.items():
            bias[action] += hint
        
        # Add bias from concept preferences
        all_concepts = set(activated.primary + activated.secondary)
        for concept in all_concepts:
            concept_lower = concept.lower()
            if concept_lower in self.CONCEPT_ACTION_MAP:
                for action, weight in self.CONCEPT_ACTION_MAP[concept_lower].items():
                    bias[action] += weight
        
        # If we have atomic_language, use learned magnetism
        if self.atomic_language and hasattr(self.atomic_language, 'atoms'):
            for concept in all_concepts:
                if concept in self.atomic_language.atoms:
                    atom = self.atomic_language.atoms[concept]
                    # High magnetism = this concept is important to the organism
                    magnetism_factor = atom.curiosity_magnetism
                    
                    # Apply magnetism to strengthen concept-driven bias
                    if concept.lower() in self.CONCEPT_ACTION_MAP:
                        for action, weight in self.CONCEPT_ACTION_MAP[concept.lower()].items():
                            bias[action] += weight * magnetism_factor
        
        # VP modulation: low VP = more conservative, high VP = more aggressive
        if vp_value is not None:
            if vp_value < 0.3:
                # Low VP: favor safe actions
                bias[3] += 0.2  # REST
                bias[5] += 0.2  # ISOLATE
                bias[2] -= 0.1  # Less COMPETE
            elif vp_value > 0.7:
                # High VP: favor aggressive actions
                bias[2] += 0.2  # COMPETE
                bias[0] += 0.1  # MOVE
                bias[3] -= 0.1  # Less REST
        
        # Urgency modulation
        if activated.urgency > 0.5:
            # Urgent: sharpen the bias (make differences more extreme)
            bias = bias * (1.0 + activated.urgency)
        
        # Scale by bias strength
        bias = bias * self.bias_strength
        
        return bias
    
    def apply_to_logits(self, 
                        logits: np.ndarray,
                        bias: np.ndarray) -> np.ndarray:
        """
        Apply bias to action logits (before softmax).
        
        Args:
            logits: Raw action logits from neural network
            bias: Bias vector from compute_bias()
            
        Returns:
            Modified logits
        """
        return logits + bias


# =============================================================================
# LEARNING FROM GAME OUTCOMES
# =============================================================================

class OutcomeLearner:
    """
    Updates linguistic concepts based on game outcomes.
    
    When an organism wins/loses/scores/dies, we update the magnetism
    of concepts that were active during the experience.
    """
    
    # Outcome categories and their concept associations
    OUTCOME_CONCEPTS = {
        'win': ['victory', 'success', 'win', 'triumph', 'dominance', 'power'],
        'lose': ['defeat', 'loss', 'fail', 'retreat'],
        'tag_enemy': ['attack', 'hit', 'strike', 'target', 'precision'],
        'got_tagged': ['evade', 'dodge', 'escape', 'defense', 'retreat'],
        'survived': ['survive', 'endure', 'persist', 'strong', 'resilient'],
        'crashed': ['crash', 'fall', 'mistake', 'careful', 'avoid'],
        'cooperated': ['cooperate', 'team', 'ally', 'formation', 'coordinate'],
        'zone_captured': ['control', 'territory', 'capture', 'dominate'],
    }
    
    def __init__(self, atomic_language=None, learning_rate: float = 0.1):
        """
        Args:
            atomic_language: AtomicLanguageSystem to update
            learning_rate: How fast to update magnetism (0.01-0.5)
        """
        self.atomic_language = atomic_language
        self.learning_rate = learning_rate
    
    def learn_from_outcome(self,
                           outcome_type: str,
                           outcome_value: float,
                           active_concepts: List[str],
                           context: str = "") -> Dict[str, float]:
        """
        DISABLED: Games no longer modify language.
        
        ═══════════════════════════════════════════════════════════════════════════
        THE PRINCIPLE: Language → Games, NOT Games → Language
        
        Language is the FOUNDATION that games USE, not something games CORRUPT.
        Organisms should leverage their vocabulary to play games better,
        but game outcomes should NOT warp vocabulary distributions.
        
        When this was enabled, it caused language collapse:
        - Battle outcomes updated magnetism for combat concepts
        - Over 1000+ battles, magnetism for "attack", "victory" etc. went to 1.0
        - Skewed magnetism → token generation favored those words → loops
        - Result: "right demand right one oppose strike right demand..."
        
        The fix: Language is READ-ONLY during games.
        ═══════════════════════════════════════════════════════════════════════════
        """
        # NO-OP: Language is immutable during gameplay
        return {}
    
    def learn_from_episode(self,
                           total_reward: float,
                           won: bool,
                           stats: Dict[str, Any],
                           episode_concepts: List[str]) -> Dict[str, float]:
        """
        DISABLED: Games no longer modify language.
        
        Language → Games, NOT Games → Language.
        See learn_from_outcome for explanation.
        """
        # NO-OP: Language is immutable during gameplay
        return {}


# =============================================================================
# UNIFIED BRIDGE
# =============================================================================

class LanguageGameBridge:
    """
    The unified bridge connecting language and game systems.
    
    Use this class to:
    1. Interpret observations linguistically
    2. Bias actions using vocabulary
    3. Learn from game outcomes
    4. Export learned concepts
    
    Example:
        bridge = LanguageGameBridge(organism)
        
        # During game step:
        concepts = bridge.interpret_observation(obs)
        action_bias = bridge.get_action_bias(concepts)
        action = neural_action + action_bias  # Combine
        
        # After game:
        bridge.learn_from_game_result(won=True, stats={...})
    """
    
    def __init__(self, 
                 organism=None,
                 atomic_language=None,
                 knowledge_web=None,
                 context: str = "drone",
                 bias_strength: float = 0.3,
                 learning_rate: float = 0.1,
                 # Additional parameters used by arenas:
                 organism_names: Optional[List[str]] = None,
                 game_type: Optional[str] = None):
        """
        Args:
            organism: Full organism object (will extract language from it)
            atomic_language: Or provide atomic_language directly
            knowledge_web: Or provide knowledge_web directly
            context: Game context ("drone", "gym", "sphere")
            bias_strength: How strongly to bias actions (0.0-1.0)
            learning_rate: How fast to learn from outcomes (0.01-0.5)
            organism_names: List of organism names (for multi-organism arenas)
            game_type: Alternative to context (e.g., "sphere_defense")
        """
        # Handle game_type as alias for context
        if game_type is not None:
            context = game_type
        
        # Extract language systems from organism if provided
        if organism is not None:
            atomic_language = atomic_language or getattr(organism, 'atomic_language', None)
            knowledge_web = knowledge_web or getattr(organism, 'knowledge_web', None)
        
        self.atomic_language = atomic_language
        self.knowledge_web = knowledge_web
        self.context = context
        
        # Initialize components
        self.interpreter = ObservationInterpreter(
            atomic_language=atomic_language,
            knowledge_web=knowledge_web,
            context=context
        )
        self.bias_computer = ConceptActionBias(
            atomic_language=atomic_language,
            bias_strength=bias_strength
        )
        self.learner = OutcomeLearner(
            atomic_language=atomic_language,
            learning_rate=learning_rate
        )
        
        # Track episode concepts
        self.episode_concepts: Set[str] = set()
        
        logger.info(f"🧠 LanguageGameBridge initialized (context={context}, "
                   f"bias={bias_strength}, lr={learning_rate})")
    
    def interpret_observation(self, observation: np.ndarray) -> ActivatedConcepts:
        """Interpret observation and track concepts for episode."""
        activated = self.interpreter.interpret(observation)
        self.episode_concepts.update(activated.primary)
        self.episode_concepts.update(activated.secondary)
        return activated
    
    def get_action_bias(self, 
                        activated: ActivatedConcepts,
                        vp_value: Optional[float] = None) -> np.ndarray:
        """Get action bias vector."""
        return self.bias_computer.compute_bias(activated, vp_value)
    
    def apply_bias_to_action(self,
                             action_probs: np.ndarray,
                             observation: np.ndarray,
                             vp_value: Optional[float] = None) -> np.ndarray:
        """
        Full pipeline: interpret observation, compute bias, apply to action probs.
        
        Args:
            action_probs: Action probabilities from neural network
            observation: Game observation
            vp_value: Current VP value
            
        Returns:
            Modified action probabilities
        """
        # Interpret observation
        activated = self.interpret_observation(observation)
        
        # Compute bias
        bias = self.get_action_bias(activated, vp_value)
        
        # Apply to log probs
        log_probs = np.log(np.clip(action_probs, 1e-8, 1.0))
        biased_log_probs = log_probs + bias
        
        # Softmax back to probs
        exp_probs = np.exp(biased_log_probs - np.max(biased_log_probs))
        biased_probs = exp_probs / exp_probs.sum()
        
        return biased_probs
    
    def learn_from_step(self,
                        outcome_type: Optional[str] = None,
                        outcome_value: Optional[float] = None,
                        observation: Optional[np.ndarray] = None,
                        # Multi-organism API used by sphere_arena:
                        organism_name: Optional[str] = None,
                        action: Optional[int] = None,
                        reward: Optional[float] = None,
                        done: Optional[bool] = None,
                        info: Optional[Dict[str, Any]] = None):
        """
        Learn from a single step outcome (e.g., tag, collision).
        
        Supports two call patterns:
        1. Simple: learn_from_step('tag_enemy', 0.5)
        2. Multi-organism: learn_from_step(organism_name=..., action=..., reward=..., done=..., info=...)
        """
        # Handle multi-organism API (used by sphere_arena)
        if organism_name is not None:
            outcome_type = info.get('event', 'step') if info else 'step'
            outcome_value = reward if reward is not None else 0.0
        else:
            # Simple API (used by cocoon_drone_arena)
            outcome_type = outcome_type or 'unknown'
            outcome_value = outcome_value if outcome_value is not None else 0.0
        
        active = list(self.episode_concepts)
        if observation is not None:
            activated = self.interpreter.interpret(observation)
            active = activated.primary + activated.secondary
        
        self.learner.learn_from_outcome(outcome_type, outcome_value, active)
    
    def learn_from_episode_end(self,
                               total_reward: Optional[float] = None,
                               won: Optional[bool] = None,
                               stats: Optional[Dict[str, Any]] = None,
                               # New multi-organism API used by arenas:
                               organism_name: Optional[str] = None,
                               final_score: Optional[float] = None,
                               episode_length: Optional[int] = None,
                               additional_info: Optional[Dict[str, Any]] = None):
        """
        Learn from episode end.
        
        Supports two call patterns:
        1. Legacy: learn_from_episode_end(total_reward, won, stats)
        2. Multi-organism: learn_from_episode_end(organism_name=..., won=..., final_score=..., episode_length=..., additional_info=...)
        """
        # Handle multi-organism API (used by all arenas)
        if organism_name is not None:
            # Convert new API to internal format
            total_reward = final_score if final_score is not None else 0.0
            won = won if won is not None else False
            stats = additional_info or {}
            stats['organism_name'] = organism_name
            stats['episode_length'] = episode_length or 0
        else:
            # Legacy API
            total_reward = total_reward if total_reward is not None else 0.0
            won = won if won is not None else False
            stats = stats or {}
        
        self.learner.learn_from_episode(
            total_reward,
            won,
            stats,
            list(self.episode_concepts)
        )
        
        # Track for correlation metrics
        self._record_correlation_data(total_reward, won, stats)
        
        # Reset episode tracking
        self.episode_concepts.clear()
    
    def _record_correlation_data(self,
                                  total_reward: float,
                                  won: bool,
                                  stats: Dict[str, Any]):
        """Record data for correlation analysis with ML/scikit systems."""
        # Initialize tracking if needed
        if not hasattr(self, '_correlation_history'):
            self._correlation_history = []
            self._bias_influence_history = []
            self._concept_outcome_map = {}  # concept -> list of (reward, won)
        
        # Track episode data
        episode_data = {
            'concepts_activated': len(self.episode_concepts),
            'unique_concepts': list(self.episode_concepts)[:20],  # Top 20
            'total_reward': total_reward,
            'won': won,
            'bias_applications': getattr(self, '_bias_count', 0),
            'avg_urgency': getattr(self, '_avg_urgency', 0.5),
            **{k: v for k, v in stats.items() if isinstance(v, (int, float, bool))}
        }
        self._correlation_history.append(episode_data)
        
        # Track concept->outcome correlations
        for concept in self.episode_concepts:
            if concept not in self._concept_outcome_map:
                self._concept_outcome_map[concept] = []
            self._concept_outcome_map[concept].append({
                'reward': total_reward,
                'won': won,
                'count': 1
            })
        
        # Limit history
        if len(self._correlation_history) > 1000:
            self._correlation_history = self._correlation_history[-500:]
        
        # Reset per-episode counters
        self._bias_count = 0
        self._avg_urgency = 0.5
    
    def get_correlation_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for correlation analysis with ML/scikit systems.
        
        Returns data suitable for ConfigTuner cross-system correlation analyzers.
        """
        if not hasattr(self, '_correlation_history') or not self._correlation_history:
            return {'episodes_tracked': 0}
        
        history = self._correlation_history
        n = len(history)
        
        # Calculate core metrics
        wins = sum(1 for h in history if h.get('won', False))
        win_rate = wins / n if n > 0 else 0.0
        
        avg_reward = sum(h.get('total_reward', 0) for h in history) / n if n > 0 else 0.0
        avg_concepts = sum(h.get('concepts_activated', 0) for h in history) / n if n > 0 else 0.0
        
        # Calculate concept-to-win correlation (simplified)
        concept_win_correlation = 0.0
        if n > 10:
            high_concept_wins = sum(1 for h in history 
                                    if h.get('concepts_activated', 0) > avg_concepts and h.get('won', False))
            low_concept_wins = sum(1 for h in history 
                                   if h.get('concepts_activated', 0) <= avg_concepts and h.get('won', False))
            high_count = sum(1 for h in history if h.get('concepts_activated', 0) > avg_concepts)
            low_count = n - high_count
            
            if high_count > 0 and low_count > 0:
                high_rate = high_concept_wins / high_count
                low_rate = low_concept_wins / low_count
                concept_win_correlation = high_rate - low_rate  # -1 to 1
        
        # Bias influence tracking
        avg_bias_applications = sum(h.get('bias_applications', 0) for h in history) / n if n > 0 else 0.0
        
        # Get most influential concepts
        top_concepts = []
        if hasattr(self, '_concept_outcome_map'):
            concept_scores = []
            for concept, outcomes in self._concept_outcome_map.items():
                if len(outcomes) >= 3:
                    avg_r = sum(o['reward'] for o in outcomes) / len(outcomes)
                    win_r = sum(1 for o in outcomes if o['won']) / len(outcomes)
                    concept_scores.append({
                        'concept': concept,
                        'avg_reward': avg_r,
                        'win_rate': win_r,
                        'count': len(outcomes)
                    })
            concept_scores.sort(key=lambda x: x['win_rate'] * x['avg_reward'], reverse=True)
            top_concepts = concept_scores[:10]
        
        return {
            'episodes_tracked': n,
            'win_rate': win_rate,
            'avg_reward': avg_reward,
            'avg_concepts_activated': avg_concepts,
            'concept_win_correlation': concept_win_correlation,
            'avg_bias_applications': avg_bias_applications,
            'unique_concepts_total': len(getattr(self, '_concept_outcome_map', {})),
            'top_performing_concepts': top_concepts,
            # For ML integration
            'vocabulary_game_alignment': concept_win_correlation,  # Key metric for tuner
            'language_decision_influence': avg_bias_applications / 100.0,  # Normalized
            'concept_diversity': avg_concepts / max(1, len(getattr(self, '_concept_outcome_map', {}))),
        }
    
    def get_sklearn_features(self) -> Dict[str, float]:
        """
        Get features formatted for scikit-learn analysis.
        
        Returns a flat dict of numeric features suitable for clustering/analysis.
        """
        metrics = self.get_correlation_metrics()
        
        return {
            'lang_game_win_rate': metrics.get('win_rate', 0.0),
            'lang_game_avg_reward': metrics.get('avg_reward', 0.0),
            'lang_game_concept_correlation': metrics.get('concept_win_correlation', 0.0),
            'lang_game_vocab_alignment': metrics.get('vocabulary_game_alignment', 0.0),
            'lang_game_bias_influence': metrics.get('language_decision_influence', 0.0),
            'lang_game_concept_diversity': metrics.get('concept_diversity', 0.0),
            'lang_game_concepts_used': float(metrics.get('unique_concepts_total', 0)),
        }
    
    def get_learned_preferences(self) -> Dict[str, Any]:
        """Get summary of what the organism has learned."""
        if self.atomic_language and hasattr(self.atomic_language, 'get_learned_preferences'):
            return self.atomic_language.get_learned_preferences()
        return {}

    def update_parameters(self, bias_strength: Optional[float] = None, 
                          learning_rate: Optional[float] = None) -> Dict[str, float]:
        """
        Dynamically update bridge parameters at runtime.
        
        Called by ConfigTuner to propagate tuning changes to running bridges.
        
        Args:
            bias_strength: New bias strength (0.0-1.0), or None to keep current
            learning_rate: New learning rate (0.01-0.5), or None to keep current
            
        Returns:
            Dict with old and new values for logging
        """
        changes = {}
        
        if bias_strength is not None:
            old_bias = getattr(self.bias_computer, 'bias_strength', 0.3)
            self.bias_computer.bias_strength = bias_strength
            changes['bias_strength_old'] = old_bias
            changes['bias_strength_new'] = bias_strength
            logger.debug(f"🧠 Bridge bias_strength updated: {old_bias:.3f} → {bias_strength:.3f}")
        
        if learning_rate is not None:
            old_lr = getattr(self.learner, 'learning_rate', 0.1)
            self.learner.learning_rate = learning_rate
            changes['learning_rate_old'] = old_lr
            changes['learning_rate_new'] = learning_rate
            logger.debug(f"🧠 Bridge learning_rate updated: {old_lr:.3f} → {learning_rate:.3f}")
        
        return changes

    def get_current_parameters(self) -> Dict[str, float]:
        """Get current bridge parameters for inspection."""
        return {
            'bias_strength': getattr(self.bias_computer, 'bias_strength', 0.3),
            'learning_rate': getattr(self.learner, 'learning_rate', 0.1)
        }


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def create_bridge_for_organism(organism, context: str = "drone", 
                               global_config: Optional[Dict[str, Any]] = None) -> 'LanguageGameBridge':
    """
    Create a LanguageGameBridge for an organism.
    
    Works with both live organisms and exported cocoons.
    
    Args:
        organism: Organism with atomic_language/knowledge_web
        context: Game context (drone, sphere, etc.)
        global_config: Optional config dict to read bias_strength/learning_rate from
    """
    # Read from config if provided, otherwise use defaults
    bridge_config = {}
    if global_config:
        bridge_config = global_config.get('neural', {}).get('language_game_bridge', {})
    
    bias_strength = bridge_config.get('bias_strength', 0.3)
    learning_rate = bridge_config.get('learning_rate', 0.1)
    
    return LanguageGameBridge(
        organism=organism,
        context=context,
        bias_strength=bias_strength,
        learning_rate=learning_rate
    )


def create_bridge_for_cocoon(cocoon_path: str, context: str = "drone") -> LanguageGameBridge:
    """
    Create a LanguageGameBridge for an exported cocoon.
    """
    import sys
    import os
    
    # Load cocoon
    if os.path.isdir(cocoon_path):
        py_files = [f for f in os.listdir(cocoon_path) 
                    if f.endswith('.py') and 'cocoon' in f.lower()]
        if py_files:
            module_name = py_files[0].replace('.py', '')
            sys.path.insert(0, cocoon_path)
            module = __import__(module_name)
            cocoon = module.CocoonAgent()
            
            return LanguageGameBridge(
                atomic_language=getattr(cocoon, 'atomic_language', None),
                knowledge_web=getattr(cocoon, 'knowledge_web', None),
                context=context
            )
    
    raise ValueError(f"Could not load cocoon from {cocoon_path}")


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("🧠 Language-Game Bridge Test")
    print("=" * 50)
    
    # Test without language (raw patterns)
    bridge = LanguageGameBridge(context="drone")
    
    # Simulate drone observation
    obs = np.zeros(28)
    obs[13] = 0.1   # Enemy very close
    obs[16] = 0.8   # High health
    obs[2] = 0.5    # Medium altitude
    
    activated = bridge.interpret_observation(obs)
    print(f"Activated concepts: {activated.primary}")
    print(f"Urgency: {activated.urgency}")
    print(f"Action hints: {activated.action_hints}")
    
    bias = bridge.get_action_bias(activated, vp_value=0.7)
    print(f"Action bias: {bias}")
    
    # Test learning
    bridge.learn_from_step('tag_enemy', 1.0)
    bridge.learn_from_episode_end(total_reward=50.0, won=True, stats={'tags_given': 3})
    
    print("\n✅ Bridge test complete")
