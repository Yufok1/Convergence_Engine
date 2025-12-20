"""
Atomic Language System - Trackable Linguistic Units for Butterfly Engine

This module atomizes language concepts exactly like organism traits are atomized,
enabling full causation tracking and Butterfly Engine integration.

Each LinguisticAtom is a discrete, trackable unit that can:
- Be traced through causation chains
- Have its formation explained by Butterfly Chat
- Show temporal evolution of organism "vocabulary"
- Enable dialect emergence analysis

Architecture mirrors the trait system:
- Traits: organism.phenotype.traits['speed'] = 0.7
- Language: organism.linguistic_atoms['food'].strength = 0.7

This enables questions like:
- "Why did this organism develop the 'share-food' concept?"
- "What caused 'danger' to associate with 'friend'?"
- "How did this community's dialect emerge?"
"""

import time
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter, deque
import numpy as np
import json

logger = logging.getLogger(__name__)

# Try to import torch for tensor conversion
try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


@dataclass
class ConceptAssociation:
    """
    Association between two concepts - a trackable link.
    
    Like a synapse between linguistic neurons.
    
    HEALING PROTOCOL EXTENSION:
    - strength_history: Track strength over time for oscillation detection
    - resonance_frequency(): Measure coherence (high = forbidden bond)
    - is_forbidden(): Bonds with coherence > 0.8 are locked in feedback loops
    """
    target_concept: str
    strength: float = 0.0  # -1.0 to 1.0 (negative = inhibition)
    formation_time: float = 0.0
    formation_reason: str = "unknown"
    update_count: int = 0
    last_update_time: float = 0.0
    
    # Quality tracking
    success_count: int = 0  # Times this association led to good outcome
    failure_count: int = 0  # Times this association led to bad outcome
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALING PROTOCOL - Forbidden Bond Detection
    # 
    # "centimeter daub orchestrate" - measure distance between oscillation peaks
    # High-frequency resonance pairs are FORBIDDEN - locked in feedback loops
    # Low coherence bonds are safe to preserve (just weak, not trapped)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def __post_init__(self):
        # Track strength history for oscillation detection (not a field to avoid dataclass issues)
        object.__setattr__(self, '_strength_history', deque(maxlen=10))
    
    def record_strength(self):
        """Record current strength to history for oscillation tracking."""
        if not hasattr(self, '_strength_history'):
            object.__setattr__(self, '_strength_history', deque(maxlen=10))
        self._strength_history.append(self.strength)
    
    def resonance_frequency(self) -> float:
        """
        Measure coherence frequency of this bond.
        
        "centimeter" = measure the distance between oscillation peaks
        High coherence (>0.8) = forbidden bond (locked in feedback loop)
        Low coherence = safe to preserve
        
        Returns:
            Coherence frequency 0.0-1.0 (higher = more synchronized oscillation)
        """
        if not hasattr(self, '_strength_history') or len(self._strength_history) < 3:
            return 0.0
        
        history = list(self._strength_history)
        
        # Count sign changes (oscillation frequency)
        sign_changes = 0
        deltas = [history[i+1] - history[i] for i in range(len(history)-1)]
        for i in range(len(deltas)-1):
            if deltas[i] * deltas[i+1] < 0:  # Sign changed
                sign_changes += 1
        
        # Normalize: many sign changes = high resonance frequency
        max_changes = len(deltas) - 1
        if max_changes <= 0:
            return 0.0
        
        frequency = sign_changes / max_changes
        
        # Also consider amplitude of oscillation
        amplitude = max(history) - min(history) if history else 0.0
        
        # High frequency + high amplitude = strong resonance (forbidden)
        coherence = frequency * (0.5 + amplitude * 0.5)
        return min(1.0, coherence)
    
    def is_forbidden(self, threshold: float = 0.8) -> bool:
        """
        Check if this bond is forbidden (trapped in feedback loop).
        
        Forbidden bonds have high coherence - they oscillate in sync.
        These need to be weakened for healing.
        
        Args:
            threshold: Coherence above this = forbidden (default 0.8)
        
        Returns:
            True if bond is trapped in high-frequency resonance
        """
        return self.resonance_frequency() > threshold
    
    def to_dict(self) -> Dict[str, Any]:
        history = list(self._strength_history) if hasattr(self, '_strength_history') else []
        return {
            'target': self.target_concept,
            'strength': self.strength,
            'formation_time': self.formation_time,
            'formation_reason': self.formation_reason,
            'update_count': self.update_count,
            'success_rate': self.success_count / max(1, self.success_count + self.failure_count),
            'strength_history': history,
            'resonance_frequency': self.resonance_frequency(),
            'is_forbidden': self.is_forbidden()
        }


@dataclass
class LinguisticAtom:
    """
    Single trackable linguistic unit - like a trait but for language.
    
    Every change to this atom can be traced through the causation system.
    The Butterfly Engine can explain WHY any concept strengthened or weakened.
    
    Attributes:
        concept_id: Unique identifier (e.g., 'food', 'danger', 'share')
        strength: Salience of this concept for the organism (0.0 to 1.0)
        associations: Links to other concepts with strengths
        acquisition_time: When this concept was first acquired
        source: How acquired ('innate', 'observed', 'taught', 'discovered')
        semantic_frame: Category ('action', 'state', 'quality', 'relationship', etc.)
        abstraction_level: 0=concrete, 1=abstract, 2=meta
        usage_count: How often this concept has been "used" by the organism
        last_used_time: Last time this concept was activated
        vp_context: VP state when concept is most relevant
        curiosity_magnetism: PERSONAL magnetism - how much THIS ORGANISM is drawn to this concept
                            Starts from base_magnetism but evolves based on outcomes!
        base_magnetism: Initial/default magnetism (action heads start at 0.9)
        outcome_history: Recent outcomes when this concept was active (-1 to +1)
    """
    concept_id: str
    strength: float = 0.5
    associations: Dict[str, ConceptAssociation] = field(default_factory=dict)
    acquisition_time: float = 0.0
    source: str = "innate"  # 'innate', 'observed', 'taught', 'discovered', 'mutated'
    semantic_frame: str = "unknown"  # 'action', 'state', 'quality', 'relationship', 'temporal', 'spatial'
    abstraction_level: int = 0  # 0=concrete, 1=abstract, 2=meta
    
    # Usage tracking
    usage_count: int = 0
    last_used_time: float = 0.0
    activation_history: List[float] = field(default_factory=list)  # Recent activation timestamps
    
    # VP context (when is this concept most relevant?)
    vp_vitality_affinity: float = 0.5  # Activated at what vitality level?
    vp_pleasure_affinity: float = 0.5  # Activated at what pleasure level?
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PERSONAL MAGNETISM SYSTEM - Coax, Don't Trap!
    # 
    # Each organism develops their OWN relationship with concepts:
    # - base_magnetism: Starting attraction (action heads = 0.9, questions = 0.85)
    # - curiosity_magnetism: CURRENT attraction (evolves based on outcomes!)
    # - outcome_history: Did referencing this concept help or hurt?
    # 
    # If an organism keeps getting BAD outcomes when they think about "compete",
    # their personal magnetism for "compete" DECREASES. They learn to avoid it.
    # If they get GOOD outcomes from "cooperate", magnetism INCREASES.
    # 
    # This is GENUINE LEARNING - not Pied Piper manipulation.
    # ═══════════════════════════════════════════════════════════════════════════
    base_magnetism: float = 0.5  # Starting/default magnetism
    curiosity_magnetism: float = 0.5  # Current PERSONAL magnetism (can diverge from base)
    outcome_history: List[float] = field(default_factory=list)  # Recent outcomes (-1 to +1)
    
    # Satiation/boredom tracking - overused concepts lose appeal
    recent_activation_count: int = 0  # Activations in recent window
    satiation_level: float = 0.0  # 0 = fresh, 1 = completely bored
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALING PROTOCOL - Oscillation Tracking
    # 
    # "sick cleavable edge wait opening" - detect oscillation, find breaking point
    # Track magnetism trajectory over time to detect trapped states
    # Entropy spikes trigger verification tests
    # ═══════════════════════════════════════════════════════════════════════════
    magnetism_history: List[float] = field(default_factory=list)  # Trajectory for oscillation detection (max 20)
    
    # Event emitter callback (set by AtomicLanguageSystem)
    _event_emitter: Optional[Callable] = field(default=None, repr=False)
    _organism_id: Optional[str] = field(default=None, repr=False)
    
    def update_magnetism_from_outcome(self, outcome: float, reason: str = ""):
        """
        Update personal magnetism based on outcome when this concept was active.
        
        This is the ANTI-PIED-PIPER mechanism:
        - Good outcome (+) → magnetism increases (want to explore more)
        - Bad outcome (-) → magnetism decreases (learn to avoid)
        - Neutral (0) → slight decay toward base (regression to mean)
        
        Args:
            outcome: Result of action when this concept was active (-1 to +1)
            reason: Why this outcome happened (for causation tracking)
        """
        # Track outcome history (keep last 10)
        self.outcome_history.append(outcome)
        if len(self.outcome_history) > 10:
            self.outcome_history = self.outcome_history[-10:]
        
        # Calculate magnetism adjustment
        # Good outcomes: +0.05 max, Bad outcomes: -0.08 max (asymmetric - bad is stronger)
        if outcome > 0:
            delta = outcome * 0.05  # Positive reinforcement
        elif outcome < 0:
            delta = outcome * 0.08  # Negative reinforcement (stronger!)
        else:
            # Neutral: regress toward base_magnetism
            delta = (self.base_magnetism - self.curiosity_magnetism) * 0.02
        
        old_magnetism = self.curiosity_magnetism
        self.curiosity_magnetism = np.clip(self.curiosity_magnetism + delta, 0.1, 1.0)
        
        # ═══════════════════════════════════════════════════════════════════════
        # HEALING PROTOCOL - Track magnetism trajectory for oscillation detection
        # ═══════════════════════════════════════════════════════════════════════
        was_oscillating = self.is_oscillating() if len(self.magnetism_history) >= 5 else False
        
        self.magnetism_history.append(self.curiosity_magnetism)
        if len(self.magnetism_history) > 20:
            self.magnetism_history = self.magnetism_history[-20:]
        
        # Detect oscillation onset - emit event when atom becomes trapped
        now_oscillating = self.is_oscillating()
        if not was_oscillating and now_oscillating and self._event_emitter:
            try:
                from causation_explorer import Event
                self._event_emitter(Event(
                    timestamp=time.time(),
                    component='healing_protocol',
                    event_type='oscillation_detected',
                    data={
                        'organism_id': self._organism_id,
                        'concept_id': self.concept_id,
                        'coherence_frequency': self.coherence_frequency(),
                        'oscillation_entropy': self.oscillation_entropy(),
                        'magnetism_trajectory': self.magnetism_history[-10:]
                    }
                ))
            except ImportError:
                pass
        
        # Emit causation event if significant change
        if self._event_emitter and abs(delta) > 0.01:
            self._emit_magnetism_update(old_magnetism, outcome, reason)
    
    def update_satiation(self):
        """
        Update satiation level based on recent usage.
        
        Overused concepts become boring - organisms naturally seek novelty.
        This prevents getting trapped in loops around the same concepts.
        """
        # Increment recent activation count
        self.recent_activation_count += 1
        
        # Satiation increases with use, decays over time
        # High usage = more satiation = less attractive
        self.satiation_level = min(1.0, self.satiation_level + 0.1)
    
    def decay_satiation(self, amount: float = 0.02):
        """
        Decay satiation over time - concepts become fresh again.
        
        Called periodically to let organisms "forget" overuse.
        NOTE: We decay satiation_level but NOT recent_activation_count,
        because activation count is needed for mastery breadth calculation.
        """
        self.satiation_level = max(0.0, self.satiation_level - amount)
        # DO NOT decay recent_activation_count - it tracks lifetime usage for mastery
    
    def get_effective_magnetism(self, organism_skepticism: float = 0.5) -> float:
        """
        Get the EFFECTIVE magnetism considering skepticism and satiation.
        
        This is the key anti-manipulation mechanism:
        - High skepticism REDUCES magnetism bonus (skeptics aren't easily drawn)
        - High satiation REDUCES magnetism (boredom protects against loops)
        - Bad outcome history REDUCES magnetism (learned avoidance)
        
        Args:
            organism_skepticism: The organism's skepticism trait (0-1)
                                High skepticism = resistant to magnetism
        
        Returns:
            Effective magnetism after all modifiers (0.1 to 1.0)
        """
        base = self.curiosity_magnetism
        
        # Skepticism reduces magnetism effect (skeptics aren't easily drawn)
        # At skepticism=1.0, magnetism effect is halved
        skepticism_modifier = 1.0 - (organism_skepticism * 0.5)
        
        # Satiation reduces magnetism (bored with this concept)
        satiation_modifier = 1.0 - (self.satiation_level * 0.4)
        
        # Recent bad outcomes reduce magnetism
        if self.outcome_history:
            avg_outcome = sum(self.outcome_history) / len(self.outcome_history)
            if avg_outcome < 0:
                outcome_modifier = 1.0 + (avg_outcome * 0.3)  # Up to -30% for bad history
            else:
                outcome_modifier = 1.0  # Good history doesn't further boost
        else:
            outcome_modifier = 1.0
        
        effective = base * skepticism_modifier * satiation_modifier * outcome_modifier
        return max(0.1, min(1.0, effective))
    
    # ═════════════════════════════════════════════════════════════════════════════
    # HEALING PROTOCOL - Oscillation Detection Methods
    # 
    # "centimeter daub orchestrate" = measure peak distances, test gently, find resonance
    # "sick cleavable edge" = detect oscillation, find breaking point
    # ═════════════════════════════════════════════════════════════════════════════
    
    def coherence_frequency(self) -> float:
        """
        Measure coherence frequency of this atom's magnetism trajectory.
        
        "centimeter" = measure the distance between oscillation peaks
        High coherence (>0.8) = trapped in oscillation loop
        Low coherence = stable or drifting (not trapped)
        
        Returns:
            Coherence frequency 0.0-1.0 (higher = more trapped in oscillation)
        """
        if len(self.magnetism_history) < 5:
            return 0.0
        
        history = self.magnetism_history
        
        # Count sign changes in deltas (oscillation frequency)
        deltas = [history[i+1] - history[i] for i in range(len(history)-1)]
        sign_changes = 0
        for i in range(len(deltas)-1):
            if deltas[i] * deltas[i+1] < 0:  # Direction reversed
                sign_changes += 1
        
        # Normalize: many sign changes = high oscillation frequency
        max_changes = len(deltas) - 1
        if max_changes <= 0:
            return 0.0
        
        frequency = sign_changes / max_changes
        
        # Also consider amplitude - small wiggles don't count as trapped
        amplitude = max(history) - min(history) if history else 0.0
        
        # High frequency + high amplitude = trapped oscillation
        # Low amplitude oscillation = just noise, not trapped
        coherence = frequency * min(1.0, amplitude * 2.0)  # Amplitude > 0.5 counts full
        return min(1.0, coherence)
    
    def oscillation_entropy(self) -> float:
        """
        Calculate entropy of magnetism oscillation pattern.
        
        "wait opening mediate disconcertingly" - when entropy SPIKES, run verification
        High entropy = chaotic/unpredictable changes (good time to test healing)
        Low entropy = stable or regular pattern (not the right moment)
        
        Returns:
            Oscillation entropy 0.0-1.0 (spike above 0.3 triggers verification)
        """
        if len(self.magnetism_history) < 5:
            return 0.0
        
        history = self.magnetism_history
        
        # Calculate variance of deltas (how unpredictable are the changes?)
        deltas = [abs(history[i+1] - history[i]) for i in range(len(history)-1)]
        if not deltas:
            return 0.0
        
        mean_delta = sum(deltas) / len(deltas)
        if mean_delta < 0.001:
            return 0.0  # No movement = no entropy
        
        # Variance of deltas normalized by mean
        variance = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)
        
        # Also check for sudden large jumps (entropy spikes)
        max_delta = max(deltas)
        spike_factor = max_delta / mean_delta if mean_delta > 0.001 else 0
        
        # Combine variance and spike detection
        # High variance + large spikes = high entropy (the "opening" moment)
        entropy = min(1.0, (variance ** 0.5) * 2 + (spike_factor - 1) * 0.1)
        return max(0.0, entropy)
    
    def is_oscillating(self, threshold: float = 0.5) -> bool:
        """
        Check if this atom is trapped in oscillation.
        
        "trapped" phenotype = coherence_frequency > threshold
        
        Args:
            threshold: Coherence above this = trapped (default 0.5)
        
        Returns:
            True if atom is oscillating/trapped
        """
        return self.coherence_frequency() > threshold
    
    def should_verify_healing(self, entropy_threshold: float = 0.3) -> bool:
        """
        Check if now is the right time to run healing verification.
        
        "wait opening" - only test when entropy spikes (the system offers an opening)
        NOT clock-based, NOT state-change-based. ENTROPY-triggered.
        
        Args:
            entropy_threshold: Entropy above this = run verification (default 0.3)
        
        Returns:
            True if entropy spike detected (good moment to test)
        """
        return self.oscillation_entropy() > entropy_threshold
    
    def get_state_signature(self) -> Dict[str, Any]:
        """
        Get state signature for broadcast.
        
        "rollback specialize compare journey" - share your trajectory, not your conclusion
        Broadcast = state-signature sharing, receivers compare to their own patterns
        
        Returns:
            State signature dict with trajectory, frequencies, current state
        """
        return {
            'concept_id': self.concept_id,
            'oscillation_trajectory': list(self.magnetism_history),
            'coherence_frequency': self.coherence_frequency(),
            'oscillation_entropy': self.oscillation_entropy(),
            'current_magnetism': self.curiosity_magnetism,
            'is_oscillating': self.is_oscillating(),
            'outcome_trend': sum(self.outcome_history) / len(self.outcome_history) if self.outcome_history else 0.0
        }
    
    def _emit_magnetism_update(self, old_magnetism: float, outcome: float, reason: str):
        """Emit causation event for magnetism change."""
        if not self._event_emitter:
            return
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='magnetism_update',
                data={
                    'organism_id': self._organism_id,
                    'concept': self.concept_id,
                    'old_magnetism': old_magnetism,
                    'new_magnetism': self.curiosity_magnetism,
                    'outcome': outcome,
                    'reason': reason,
                    'outcome_history': self.outcome_history[-5:],
                    'satiation': self.satiation_level
                }
            )
            self._event_emitter(event)
        except Exception:
            pass
    
    def update_strength(self, delta: float, reason: str, emit_event: bool = True):
        """
        Update concept strength with full causation tracking.
        
        Args:
            delta: Change in strength (can be negative)
            reason: Why the change happened (for Butterfly Engine)
            emit_event: Whether to emit causation event
        """
        old_strength = self.strength
        self.strength = np.clip(self.strength + delta, 0.0, 1.0)
        self.last_used_time = time.time()
        self.usage_count += 1
        
        # Track activation history (keep last 20)
        self.activation_history.append(time.time())
        if len(self.activation_history) > 20:
            self.activation_history = self.activation_history[-20:]
        
        # Emit causation event for Butterfly Engine
        if emit_event and self._event_emitter and abs(delta) > 0.01:
            self._emit_atom_update(old_strength, reason)
    
    def _emit_atom_update(self, old_strength: float, reason: str):
        """Emit event for causation tracking."""
        if not self._event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='linguistic_atom_update',
                data={
                    'organism_id': self._organism_id,
                    'concept': self.concept_id,
                    'old_strength': old_strength,
                    'new_strength': self.strength,
                    'delta': self.strength - old_strength,
                    'reason': reason,
                    'source': self.source,
                    'semantic_frame': self.semantic_frame,
                    'usage_count': self.usage_count,
                    'association_count': len(self.associations)
                }
            )
            self._event_emitter(event)
        except ImportError:
            pass  # CausationExplorer not available
    
    def form_association(self, target_concept: str, strength: float, reason: str, emit_event: bool = True):
        """
        Form or strengthen association with another concept.
        
        Args:
            target_concept: The concept to associate with
            strength: Association strength (-1.0 to 1.0)
            reason: Why the association formed
            emit_event: Whether to emit causation event
        """
        current_time = time.time()
        
        if target_concept in self.associations:
            # Strengthen existing association
            old_strength = self.associations[target_concept].strength
            self.associations[target_concept].strength = np.clip(
                self.associations[target_concept].strength + strength * 0.3,  # Gradual update
                -1.0, 1.0
            )
            self.associations[target_concept].update_count += 1
            self.associations[target_concept].last_update_time = current_time
            # Track for resonance/forbidden bond detection
            self.associations[target_concept].record_strength()
        else:
            # Create new association
            old_strength = 0.0
            self.associations[target_concept] = ConceptAssociation(
                target_concept=target_concept,
                strength=np.clip(strength, -1.0, 1.0),
                formation_time=current_time,
                formation_reason=reason
            )
            # Initial strength recording
            self.associations[target_concept].record_strength()
        
        # Emit causation event
        if emit_event and self._event_emitter:
            self._emit_association_event(target_concept, old_strength, reason)
    
    def _emit_association_event(self, target_concept: str, old_strength: float, reason: str):
        """Emit event for association formation/update."""
        if not self._event_emitter:
            return
            
        try:
            from causation_explorer import Event
            new_strength = self.associations[target_concept].strength
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='association_formed' if old_strength == 0.0 else 'association_updated',
                data={
                    'organism_id': self._organism_id,
                    'source_concept': self.concept_id,
                    'target_concept': target_concept,
                    'old_strength': old_strength,
                    'new_strength': new_strength,
                    'reason': reason,
                    'is_new': old_strength == 0.0
                }
            )
            self._event_emitter(event)
        except ImportError:
            pass
    
    def get_top_associations(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N associated concepts by strength."""
        sorted_assocs = sorted(
            self.associations.items(),
            key=lambda x: abs(x[1].strength),
            reverse=True
        )
        return [(k, v.strength) for k, v in sorted_assocs[:n]]
    
    def decay(self, amount: float = 0.01):
        """Apply decay to strength (unused concepts fade)."""
        time_since_use = time.time() - self.last_used_time
        if time_since_use > 60:  # More than 60 seconds since use
            decay_factor = min(amount * (time_since_use / 60), 0.1)  # Cap decay
            if self.strength > 0.1:  # Don't decay below 0.1
                self.strength = max(0.1, self.strength - decay_factor)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize atom for storage/debugging."""
        return {
            'concept_id': self.concept_id,
            'strength': self.strength,
            'source': self.source,
            'semantic_frame': self.semantic_frame,
            'abstraction_level': self.abstraction_level,
            'usage_count': self.usage_count,
            'acquisition_time': self.acquisition_time,
            'associations': {k: v.to_dict() for k, v in self.associations.items()},
            'vp_affinity': {
                'vitality': self.vp_vitality_affinity,
                'pleasure': self.vp_pleasure_affinity
            },
            # ═══════════════════════════════════════════════════════════════
            # MAGNETISM INHERITANCE - Bonds that persist across death
            # ═══════════════════════════════════════════════════════════════
            'base_magnetism': self.base_magnetism,
            'curiosity_magnetism': self.curiosity_magnetism,
            'outcome_history': self.outcome_history[-10:],  # Last 10 outcomes
            'satiation_level': self.satiation_level,
            # ═══════════════════════════════════════════════════════════════
            # HEALING PROTOCOL - Oscillation trajectory
            # ═══════════════════════════════════════════════════════════════
            'magnetism_history': self.magnetism_history[-20:],  # Last 20 trajectory points
            'coherence_frequency': self.coherence_frequency(),
            'oscillation_entropy': self.oscillation_entropy(),
            'is_oscillating': self.is_oscillating()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinguisticAtom':
        """Deserialize atom from storage."""
        atom = cls(
            concept_id=data['concept_id'],
            strength=data.get('strength', 0.5),
            source=data.get('source', 'loaded'),
            semantic_frame=data.get('semantic_frame', 'unknown'),
            abstraction_level=data.get('abstraction_level', 0),
            usage_count=data.get('usage_count', 0),
            acquisition_time=data.get('acquisition_time', time.time())
        )
        
        # Restore associations
        for target, assoc_data in data.get('associations', {}).items():
            assoc = ConceptAssociation(
                target_concept=target,
                strength=assoc_data.get('strength', 0.0),
                formation_time=assoc_data.get('formation_time', 0.0),
                formation_reason=assoc_data.get('formation_reason', 'loaded')
            )
            # Restore strength history for resonance detection
            strength_history = assoc_data.get('strength_history', [])
            for s in strength_history:
                assoc.record_strength() if s == assoc.strength else None
            # Re-record current to populate history
            if strength_history:
                for s in strength_history[-10:]:
                    assoc._strength_history.append(s)
            atom.associations[target] = assoc
        
        # Restore VP affinity
        vp_data = data.get('vp_affinity', {})
        atom.vp_vitality_affinity = vp_data.get('vitality', 0.5)
        atom.vp_pleasure_affinity = vp_data.get('pleasure', 0.5)
        
        # ═══════════════════════════════════════════════════════════════
        # RESTORE MAGNETISM - Inherited attractor landscape
        # ═══════════════════════════════════════════════════════════════
        atom.base_magnetism = data.get('base_magnetism', 0.5)
        atom.curiosity_magnetism = data.get('curiosity_magnetism', data.get('base_magnetism', 0.5))
        atom.outcome_history = data.get('outcome_history', [])
        atom.satiation_level = data.get('satiation_level', 0.0)
        
        # ═══════════════════════════════════════════════════════════════
        # RESTORE HEALING PROTOCOL - Oscillation trajectory
        # ═══════════════════════════════════════════════════════════════
        atom.magnetism_history = data.get('magnetism_history', [])
        
        return atom


class AtomicLanguageSystem:
    """
    Per-organism atomic language representation.
    
    Replaces monolithic vocabulary vectors with trackable discrete atoms.
    Each organism has its own AtomicLanguageSystem instance.
    
    Provides:
    - Full causation tracking for Butterfly Engine
    - Dialect emergence through differential atom development
    - VP-modulated concept salience
    - Association graphs between concepts
    - Conversion to dense tensors for neural network compatibility
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # THE 6 ACTION HEADS
    # Core neural network outputs - every organism action maps to one of these
    # Canonical order: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
    # ═══════════════════════════════════════════════════════════════════════════
    
    ACTION_HEADS = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FOUNDATIONAL ORIENTATION SYSTEM
    # Inspired by the Voyager Golden Record (1977) - what humanity chose to
    # represent itself to the cosmos. These are the BASICS every organism
    # considers recursively when taking ANY action.
    #
    # Like teaching a child: alphabet, numbers, colors, then concepts.
    # This is embedded INTO each action frame as orientation context.
    # ═══════════════════════════════════════════════════════════════════════════
    
    ORIENTATION = {
        # NOTE: Alphabet removed - single letters have no semantic weight
        # Organisms operate at WORD level, not character level
        
        # NUMBERS - Foundation of quantity and mathematics
        'numbers': [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 
            'eight', 'nine', 'ten', 'hundred', 'thousand', 'million',
            'first', 'second', 'third', 'last', 'none', 'all', 'some', 'many', 'few'
        ],
        
        # COLORS - Foundation of perception and differentiation
        'colors': [
            'red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink',
            'black', 'white', 'gray', 'brown', 'gold', 'silver',
            'light', 'dark', 'bright', 'dim'
        ],
        
        # DIRECTIONS - Foundation of spatial orientation
        'directions': [
            'up', 'down', 'left', 'right', 'forward', 'backward',
            'north', 'south', 'east', 'west', 'near', 'far',
            'inside', 'outside', 'above', 'below', 'here', 'there'
        ],
        
        # TIME - Foundation of temporal orientation
        'time': [
            'now', 'then', 'before', 'after', 'past', 'present', 'future',
            'begin', 'end', 'start', 'stop', 'continue', 'pause',
            'fast', 'slow', 'always', 'never', 'sometimes', 'soon', 'later'
        ],
        
        # EXISTENCE - Foundation of being (from Golden Record)
        'existence': [
            'yes', 'no', 'true', 'false', 'exist', 'nothing', 'something',
            'life', 'death', 'birth', 'growth', 'change', 'same', 'different',
            'self', 'other', 'we', 'they', 'it'
        ],
        
        # RELATIONSHIPS - Foundation of social orientation (from Golden Record)
        'relationships': [
            'friend', 'enemy', 'family', 'mother', 'father', 'child',
            'together', 'alone', 'group', 'pair', 'one', 'many',
            'love', 'fear', 'trust', 'help', 'harm'
        ],
        
        # NATURE - Sounds of Earth (from Golden Record)
        'nature': [
            'sun', 'moon', 'star', 'earth', 'sky', 'water', 'fire', 'air',
            'wind', 'rain', 'thunder', 'ocean', 'mountain', 'river', 'tree',
            'animal', 'plant', 'food', 'energy'
        ],
        
        # ACTIONS - The 6 heads + basic verbs
        'actions': [
            'move', 'rest', 'reproduce', 'cooperate', 'compete', 'isolate',
            'go', 'come', 'give', 'take', 'make', 'break', 'find', 'lose',
            'see', 'hear', 'feel', 'think', 'know', 'want', 'need',
            'eat', 'drink', 'sleep', 'wake', 'live', 'die'
        ],
        
        # QUALITIES - Basic descriptors
        'qualities': [
            'good', 'bad', 'big', 'small', 'strong', 'weak', 'hot', 'cold',
            'hard', 'soft', 'new', 'old', 'young', 'safe', 'danger',
            'happy', 'sad', 'angry', 'calm', 'hungry', 'full'
        ],
        
        # QUESTIONS - Foundation of curiosity and learning
        'questions': [
            'what', 'who', 'where', 'when', 'why', 'how', 'which',
            'can', 'will', 'should', 'must', 'may', 'might'
        ],
        
        # UNIVERSALS - What humanity most wanted to convey (Golden Record)
        'universals': [
            'hello', 'peace', 'welcome', 'hope', 'curiosity', 'explore',
            'create', 'share', 'learn', 'teach', 'understand', 'remember',
            'music', 'dance', 'play', 'work', 'dream'
        ]
    }
    
    # Flatten for quick lookup
    ORIENTATION_WORDS = set()
    for category, words in ORIENTATION.items():
        ORIENTATION_WORDS.update(words)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VOYAGER GOLDEN RECORD - Detailed concept definitions
    # These get special treatment - higher innate strength, marked as foundational
    # ═══════════════════════════════════════════════════════════════════════════
    
    GOLDEN_RECORD_CONCEPTS = {
        # GREETINGS - First contact, basic communication
        'hello': {'frame': 'greeting', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'peace': {'frame': 'greeting', 'level': 0, 'vp': (0.4, 0.9), 'golden_record': True},
        'friend': {'frame': 'greeting', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'welcome': {'frame': 'greeting', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        
        # SOUNDS OF EARTH - Natural world awareness
        'wind': {'frame': 'nature', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'rain': {'frame': 'nature', 'level': 0, 'vp': (0.5, 0.6), 'golden_record': True},
        'thunder': {'frame': 'nature', 'level': 0, 'vp': (0.6, 0.4), 'golden_record': True},
        'fire': {'frame': 'nature', 'level': 0, 'vp': (0.7, 0.3), 'golden_record': True},
        'ocean': {'frame': 'nature', 'level': 0, 'vp': (0.5, 0.6), 'golden_record': True},
        'bird': {'frame': 'nature', 'level': 0, 'vp': (0.5, 0.6), 'golden_record': True},
        'whale': {'frame': 'nature', 'level': 0, 'vp': (0.4, 0.6), 'golden_record': True},
        'heartbeat': {'frame': 'nature', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        
        # MUSIC - Culture, emotion, expression
        'music': {'frame': 'culture', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'song': {'frame': 'culture', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'dance': {'frame': 'culture', 'level': 0, 'vp': (0.6, 0.8), 'golden_record': True},
        'rhythm': {'frame': 'culture', 'level': 0, 'vp': (0.5, 0.7), 'golden_record': True},
        
        # IMAGES OF LIFE - Biological existence
        'birth': {'frame': 'life', 'level': 0, 'vp': (0.7, 0.9), 'golden_record': True},
        'growth': {'frame': 'life', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        'family': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'child': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'mother': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.9), 'golden_record': True},
        'father': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'eat': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.7), 'golden_record': True},
        'drink': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.7), 'golden_record': True},
        'learn': {'frame': 'life', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        'teach': {'frame': 'life', 'level': 0, 'vp': (0.5, 0.7), 'golden_record': True},
        
        # PIONEER PLAQUE - Scientific understanding
        'hydrogen': {'frame': 'science', 'level': 1, 'vp': (0.5, 0.5), 'golden_record': True},
        'star': {'frame': 'science', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        'planet': {'frame': 'science', 'level': 0, 'vp': (0.5, 0.6), 'golden_record': True},
        'sun': {'frame': 'science', 'level': 0, 'vp': (0.7, 0.6), 'golden_record': True},
        'earth': {'frame': 'science', 'level': 0, 'vp': (0.5, 0.7), 'golden_record': True},
        'time': {'frame': 'science', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'distance': {'frame': 'science', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'number': {'frame': 'science', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        
        # ARECIBO MESSAGE - Mathematics and biology
        'one': {'frame': 'math', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'two': {'frame': 'math', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'three': {'frame': 'math', 'level': 0, 'vp': (0.5, 0.5), 'golden_record': True},
        'life': {'frame': 'biology', 'level': 0, 'vp': (0.7, 0.8), 'golden_record': True},
        'human': {'frame': 'biology', 'level': 0, 'vp': (0.5, 0.6), 'golden_record': True},
        
        # UNIVERSAL CONCEPTS - What we most wanted to convey
        'love': {'frame': 'universal', 'level': 0, 'vp': (0.5, 0.9), 'golden_record': True},
        'hope': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.8), 'golden_record': True},
        'curiosity': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        'explore': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.7), 'golden_record': True},
        'create': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.8), 'golden_record': True},
        'together': {'frame': 'universal', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
        'share': {'frame': 'universal', 'level': 0, 'vp': (0.5, 0.8), 'golden_record': True},
    }
    
    # Innate vocabulary loaded from data/innate_vocab.json
    # Generated by generate_innate_vocab.py from nuclear extraction
    _INNATE_VOCAB_CACHE = None  # Class-level cache
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FALLBACK INNATE CONCEPTS
    # Used if innate_vocab.json not found
    # 
    # CURIOSITY MAGNETISM: The key to coaxing, not forcing!
    # - Action heads have HIGH magnetism (0.9) - organisms are drawn to explore them
    # - Questions have HIGH magnetism (0.85) - curiosity begets curiosity  
    # - Golden Record concepts have MEDIUM-HIGH magnetism (0.7)
    # - Regular concepts have NEUTRAL magnetism (0.5)
    # - Boring/negative concepts have LOW magnetism (0.3)
    # ═══════════════════════════════════════════════════════════════════════════
    FALLBACK_INNATE_CONCEPTS = {
        # THE 6 ACTION HEADS - HIGH MAGNETISM (organisms WANT to explore these)
        'move': {'frame': 'action_head', 'level': 0, 'vp': (0.5, 0.5), 'magnetism': 0.9},
        'rest': {'frame': 'action_head', 'level': 0, 'vp': (0.3, 0.6), 'magnetism': 0.9},
        'reproduce': {'frame': 'action_head', 'level': 0, 'vp': (0.6, 0.8), 'magnetism': 0.9},
        'cooperate': {'frame': 'action_head', 'level': 0, 'vp': (0.5, 0.7), 'magnetism': 0.9},
        'compete': {'frame': 'action_head', 'level': 0, 'vp': (0.6, 0.3), 'magnetism': 0.9},
        'isolate': {'frame': 'action_head', 'level': 0, 'vp': (0.4, 0.4), 'magnetism': 0.9},
        
        # CURIOSITY CONCEPTS - Also high magnetism (self-reinforcing)
        'why': {'frame': 'question', 'level': 0, 'vp': (0.5, 0.6), 'magnetism': 0.85},
        'how': {'frame': 'question', 'level': 0, 'vp': (0.5, 0.6), 'magnetism': 0.85},
        'what': {'frame': 'question', 'level': 0, 'vp': (0.5, 0.5), 'magnetism': 0.8},
        'explore': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.7), 'magnetism': 0.85},
        'learn': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.7), 'magnetism': 0.8},
        'discover': {'frame': 'universal', 'level': 0, 'vp': (0.6, 0.8), 'magnetism': 0.85},
        
        # State concepts - medium magnetism
        'hungry': {'frame': 'state', 'level': 0, 'vp': (0.3, 0.3), 'magnetism': 0.6},
        'safe': {'frame': 'state', 'level': 0, 'vp': (0.6, 0.7), 'magnetism': 0.5},
        'danger': {'frame': 'state', 'level': 0, 'vp': (0.4, 0.2), 'magnetism': 0.4},
        'alive': {'frame': 'state', 'level': 0, 'vp': (0.7, 0.7), 'magnetism': 0.6},
        'strong': {'frame': 'state', 'level': 0, 'vp': (0.7, 0.6), 'magnetism': 0.55},
        'weak': {'frame': 'state', 'level': 0, 'vp': (0.3, 0.4), 'magnetism': 0.35},
        
        # Relationship concepts - medium-high magnetism (social is interesting)
        'friend': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.8), 'magnetism': 0.7},
        'enemy': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.2), 'magnetism': 0.5},
        'alone': {'frame': 'relationship', 'level': 0, 'vp': (0.4, 0.4), 'magnetism': 0.4},
        'together': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.7), 'magnetism': 0.7},
        
        # Resource concepts - medium magnetism  
        'food': {'frame': 'resource', 'level': 0, 'vp': (0.5, 0.7), 'magnetism': 0.6},
        'energy': {'frame': 'resource', 'level': 0, 'vp': (0.6, 0.5), 'magnetism': 0.55},
    }
    
    @classmethod
    def _load_innate_vocab(cls):
        """Load innate vocabulary from JSON file (cached at class level)."""
        if cls._INNATE_VOCAB_CACHE is not None:
            return cls._INNATE_VOCAB_CACHE
        
        from pathlib import Path
        innate_path = Path(__file__).parent.parent.parent / "data" / "innate_vocab.json"
        
        try:
            with open(innate_path, 'r', encoding='utf-8') as f:
                cls._INNATE_VOCAB_CACHE = json.load(f)
                logger.info(f"[ATOMIC_LANG] Loaded innate vocab: {len(cls._INNATE_VOCAB_CACHE.get('concepts', {}))} concepts")
                return cls._INNATE_VOCAB_CACHE
        except FileNotFoundError:
            logger.warning(f"[ATOMIC_LANG] innate_vocab.json not found, using fallback")
            cls._INNATE_VOCAB_CACHE = None
            return None
        except Exception as e:
            logger.error(f"[ATOMIC_LANG] Error loading innate_vocab.json: {e}")
            cls._INNATE_VOCAB_CACHE = None
            return None
    
    def __init__(self, organism_id: str, event_emitter: Optional[Callable] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize atomic language system for an organism.
        
        Args:
            organism_id: Unique identifier for the organism
            event_emitter: Callback to emit causation events
            config: Configuration dictionary
        """
        self.organism_id = organism_id
        self.event_emitter = event_emitter
        self.config = config or {}
        
        # Core storage
        self.atoms: Dict[str, LinguisticAtom] = {}
        
        # Ordered concept list for tensor conversion (deterministic order)
        self._concept_order: List[str] = []
        
        # Statistics
        self.total_concepts_acquired = 0
        self.total_associations_formed = 0
        self.creation_time = time.time()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # GROUNDED LANGUAGE MODE - Mastery Level System
        # 
        # Organisms start with minimal vocabulary (6 action heads) and EARN more
        # through demonstrated competence. This ensures behavioral grounding
        # before semantic abstraction.
        # 
        # Level 0: 6 words   - Action heads only (move, cooperate, compete, rest, reproduce, isolate)
        # Level 1: 26 words  - +20 core state/relationship words
        # Level 2: 76 words  - +50 extended concepts
        # Level 3: 276 words - +200 pool words
        # Level 4: Unlimited - Semantic graduation (knowledge web unlocks)
        # ═══════════════════════════════════════════════════════════════════════════
        lang_config = self.config.get('language', {})
        grounded_config = lang_config.get('grounded', {})
        self._mastery_level: int = grounded_config.get('initial_mastery_level', 4)  # Default: no gating
        self._mastery_vocab_sizes: List[int] = grounded_config.get('mastery_vocab_sizes', [6, 26, 76, 276, 20000])
        self._mastery_advancement_ratio: float = grounded_config.get('mastery_advancement_ratio', 0.5)
        self._mastery_depth_ratio: float = grounded_config.get('mastery_depth_ratio', 0.3)
        self._mastery_min_experiences: List[int] = grounded_config.get('mastery_min_experiences', [25, 100, 300, 600])
        self._total_experiences: int = 0
        
        # ═══════════════════════════════════════════════════════════════════════════
        # HEALING PROTOCOL - Resonance Tracking
        # 
        # "duration trigger eventual caressing" - isolation = no resonant response for N cycles
        # Track when we last received echoing response from network
        # ═══════════════════════════════════════════════════════════════════════════
        self.last_echo_cycle: int = 0  # Last cycle we received resonant response
        self.current_cycle: int = 0    # Current cycle counter
        self.resonance_persistence_window: int = self.config.get('resonance_persistence_window', 5)
        
        # Initialize with innate concepts (respecting mastery level in grounded mode)
        self._initialize_innate_concepts()

        logger.debug(f"[ATOMIC_LANG] Initialized for organism {organism_id} with {len(self.atoms)} innate concepts (mastery level {self._mastery_level})")
    
    def _initialize_innate_concepts(self):
        """
        Initialize organism with innate (inherited) concepts from nuclear vocab.

        GROUNDED MODE BEHAVIOR:
        - Level 0: ONLY action heads (6 words) - no innate loading
        - Level 1: Action heads + minimal core (26 words target)
        - Level 2-3: Progressive innate loading
        - Level 4: Full innate loading (current behavior)

        Loads from data/innate_vocab.json which contains:
        - Tier 1 (core): 50 words all organisms get
        - Tier 2 (extended): 200 words, organisms get random 20-50
        - Tier 3 (pool): 1450 words, organisms get random 0-10

        This creates vocabulary diversity while ensuring core survival concepts.
        """
        current_time = time.time()

        # ═══════════════════════════════════════════════════════════════
        # GROUNDED MODE: Mastery-gated initialization
        # ═══════════════════════════════════════════════════════════════
        if self._mastery_level == 0:
            # Level 0: ONLY action heads - load them explicitly, skip all other innate vocab
            logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Level 0 - loading ACTION_HEADS only")
            self._initialize_action_heads_only(current_time)
            self._seed_action_head_curiosity()  # Make them interesting
            self.total_concepts_acquired = len(self.atoms)
            return

        innate_data = self._load_innate_vocab()

        if innate_data is None:
            # Fallback to minimal hardcoded concepts
            logger.warning(f"[ATOMIC_LANG] Using fallback innate concepts for {self.organism_id}")
            for concept_id, info in self.FALLBACK_INNATE_CONCEPTS.items():
                # Get curiosity_magnetism - action heads and questions get HIGH magnetism
                magnetism = info.get('magnetism', 0.5)
                
                atom = LinguisticAtom(
                    concept_id=concept_id,
                    strength=0.5,  # Fixed starting point - differentiation comes from experience
                    source='innate',
                    semantic_frame=info['frame'],
                    abstraction_level=info['level'],
                    acquisition_time=current_time,
                    vp_vitality_affinity=info['vp'][0],
                    vp_pleasure_affinity=info['vp'][1],
                    curiosity_magnetism=magnetism
                )
                atom._event_emitter = self.event_emitter
                atom._organism_id = self.organism_id
                self.atoms[concept_id] = atom
                self._concept_order.append(concept_id)
            self.total_concepts_acquired = len(self.atoms)
            return
        
        # Load from innate_vocab.json
        concepts = innate_data.get('concepts', {})
        tiers = innate_data.get('tiers', {})
        tier_config = innate_data.get('tier_config', {})
        associations = innate_data.get('associations', [])
        
        # Tier 1: Core concepts (all organisms)
        core_words = tiers.get('core', [])
        for word in core_words:
            if word in concepts:
                self._add_innate_concept(word, concepts[word], current_time, 'innate_core', 0.6)
        
        # Tier 2: Extended concepts (random subset)
        extended_words = tiers.get('extended', [])
        ext_range = tier_config.get('extended_sample_range', [20, 50])
        num_extended = np.random.randint(ext_range[0], ext_range[1] + 1)
        
        if extended_words:
            selected_extended = list(np.random.choice(
                extended_words, 
                size=min(num_extended, len(extended_words)), 
                replace=False
            ))
            for word in selected_extended:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], current_time, 'innate_extended', 0.4)
        
        # Tier 3: Pool concepts (rare random additions)
        pool_words = tiers.get('pool', [])
        pool_range = tier_config.get('pool_sample_range', [0, 10])
        num_pool = np.random.randint(pool_range[0], pool_range[1] + 1)
        
        if pool_words and num_pool > 0:
            selected_pool = list(np.random.choice(
                pool_words,
                size=min(num_pool, len(pool_words)),
                replace=False
            ))
            for word in selected_pool:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], current_time, 'innate_rare', 0.25)
        
        # Initialize associations between innate concepts
        for assoc in associations:
            src = assoc.get('source', '')
            tgt = assoc.get('target', '')
            strength = assoc.get('strength', 0.5)
            
            if src in self.atoms and tgt in self.atoms:
                self.atoms[src].form_association(tgt, strength, 'innate', emit_event=False)
        
        self.total_concepts_acquired = len(self.atoms)
        logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id} initialized with {len(self.atoms)} innate concepts")

        # GROUNDED MODE: Gate Golden Record and Orientation loading by mastery
        if self._mastery_level >= 2:
            # Level 2+: Load Voyager Golden Record concepts
            self._initialize_golden_record_concepts(current_time)
            logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Level {self._mastery_level} - loaded Golden Record concepts")

        if self._mastery_level >= 2:
            # Level 2+: Initialize foundational orientation concepts (numbers, colors)
            self._initialize_foundational_orientation(current_time)
            logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Level {self._mastery_level} - loaded foundational orientation")

        # Make action heads intrinsically interesting (coax, don't force!)
        self._seed_action_head_curiosity()
    
    def _initialize_action_heads_only(self, current_time: float):
        """
        Initialize ONLY the 6 action heads for level 0 organisms.
        
        GROUNDED LANGUAGE PHILOSOPHY:
        Level 0 organisms get ONLY the foundational action vocabulary:
        - move, cooperate, compete, rest, reproduce, isolate
        
        These are the behavioral primitives that ground language in action.
        Organisms must earn more vocabulary through demonstrated mastery.
        """
        # Load innate_vocab.json to get proper concept definitions for action heads
        innate_data = self._load_innate_vocab()
        concepts = innate_data.get('concepts', {}) if innate_data else {}
        
        for action_head in self.ACTION_HEADS:
            if action_head not in self.atoms:
                # Get definition from innate_vocab if available, else use defaults
                info = concepts.get(action_head, {})
                frame = info.get('frame', 'action')
                level = info.get('level', 0)
                vp = info.get('vp', [0.5, 0.5])
                
                atom = LinguisticAtom(
                    concept_id=action_head,
                    strength=0.7,  # Fixed starting point - differentiation comes from experience
                    source='innate_action_head',
                    semantic_frame=frame,
                    abstraction_level=level,
                    acquisition_time=current_time,
                    vp_vitality_affinity=vp[0] if isinstance(vp, (list, tuple)) else 0.5,
                    vp_pleasure_affinity=vp[1] if isinstance(vp, (list, tuple)) else 0.5,
                    base_magnetism=0.9,  # High magnetism - these are CORE concepts
                    curiosity_magnetism=0.9
                )
                atom._event_emitter = self.event_emitter
                atom._organism_id = self.organism_id
                self.atoms[action_head] = atom
                self._concept_order.append(action_head)
        
        logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Initialized {len(self.atoms)} action heads")
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # BEHAVIOR-DRIVEN SPECIALIZATION: Map actions to preferred vocabulary frames
    # Like Elder Scrolls: use sword → level sword skill. Use compete → get combat vocabulary.
    # Each organism develops a UNIQUE dialect based on their actual playstyle.
    # ═══════════════════════════════════════════════════════════════════════════════════════
    ACTION_FRAME_AFFINITIES = {
        # action_index: (primary_frames, secondary_frames)
        # Primary frames get 3x weight, secondary get 2x weight
        0: (['action', 'perception'], ['state', 'causal']),        # MOVE: action verbs, perception
        1: (['relationship', 'communication'], ['state', 'quality']),  # COOPERATE: social, communication
        2: (['action', 'causal'], ['state', 'quality']),           # COMPETE: action, cause-effect
        3: (['state', 'cognitive'], ['perception', 'quality']),    # REST: states, introspection
        4: (['causal', 'relationship'], ['state', 'action']),      # REPRODUCE: causation, relationships
        5: (['perception', 'cognitive'], ['state', 'quality']),    # ISOLATE: perception, cognition
    }
    
    def _get_behavior_profile(self) -> Dict[str, float]:
        """
        Get organism's behavior profile based on action history.
        
        Returns normalized weights for each frame based on which actions
        the organism has used most. This drives vocabulary specialization.
        
        Returns:
            Dict mapping frame names to weights (0.0-1.0)
        """
        # Count activations for each action head
        action_counts = {}
        for i, action_name in enumerate(self.ACTION_HEADS):
            if action_name in self.atoms:
                action_counts[i] = getattr(self.atoms[action_name], 'recent_activation_count', 0)
            else:
                action_counts[i] = 0
        
        total_actions = sum(action_counts.values())
        if total_actions == 0:
            # No action history yet - return uniform weights
            return {frame: 1.0 for frame in ['action', 'causal', 'cognitive', 'communication', 
                                              'perception', 'quality', 'relationship', 'state']}
        
        # Calculate frame weights based on action usage
        frame_weights = {}
        for action_idx, count in action_counts.items():
            if count == 0:
                continue
            
            action_weight = count / total_actions
            primary_frames, secondary_frames = self.ACTION_FRAME_AFFINITIES.get(action_idx, ([], []))
            
            # Primary frames get 3x weight contribution
            for frame in primary_frames:
                frame_weights[frame] = frame_weights.get(frame, 0) + action_weight * 3.0
            
            # Secondary frames get 2x weight contribution  
            for frame in secondary_frames:
                frame_weights[frame] = frame_weights.get(frame, 0) + action_weight * 2.0
        
        # Normalize to 0-1 range with minimum floor
        if frame_weights:
            max_weight = max(frame_weights.values())
            if max_weight > 0:
                for frame in frame_weights:
                    frame_weights[frame] = max(0.1, frame_weights[frame] / max_weight)
        
        # Ensure all frames have at least minimum weight (allows some diversity)
        for frame in ['action', 'causal', 'cognitive', 'communication', 
                      'perception', 'quality', 'relationship', 'state']:
            if frame not in frame_weights:
                frame_weights[frame] = 0.1  # Minimum floor
        
        return frame_weights
    
    def _get_dominant_actions(self, top_n: int = 2) -> List[int]:
        """
        Get the organism's most-used actions.
        
        Returns:
            List of action indices sorted by usage (highest first)
        """
        action_counts = []
        for i, action_name in enumerate(self.ACTION_HEADS):
            if action_name in self.atoms:
                count = getattr(self.atoms[action_name], 'recent_activation_count', 0)
                action_counts.append((i, count))
            else:
                action_counts.append((i, 0))
        
        # Sort by count descending
        action_counts.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, count in action_counts[:top_n] if count > 0]
    
    def _sort_words_by_behavior_affinity(self, words: List[str], concepts: Dict[str, Any]) -> List[str]:
        """
        Sort candidate words by how well they match organism's behavior profile.
        
        Words in frames the organism uses most get prioritized.
        This creates vocabulary specialization based on playstyle.
        
        Args:
            words: List of candidate words
            concepts: Concept info dict from innate_vocab.json
            
        Returns:
            Words sorted by behavior affinity (highest first)
        """
        behavior_profile = self._get_behavior_profile()
        
        # Score each word by its frame's weight in behavior profile
        scored_words = []
        for word in words:
            if word in concepts:
                frame = concepts[word].get('frame', 'universal')
                score = behavior_profile.get(frame, 0.1)
                scored_words.append((word, score))
            else:
                scored_words.append((word, 0.1))
        
        # Sort by score descending, with small random tiebreaker for variety
        import random
        scored_words.sort(key=lambda x: (x[1], random.random()), reverse=True)
        
        return [word for word, score in scored_words]
    
    def _expand_vocabulary_for_level(self, new_level: int):
        """
        Expand vocabulary when organism advances to a new mastery level.
        
        BEHAVIOR-DRIVEN SPECIALIZATION (Elder Scrolls style):
        Words are selected based on organism's action history. An organism
        that competes a lot gets combat/causal vocabulary. One that cooperates
        gets social/communication vocabulary. Each organism develops a unique
        dialect grounded in their actual experience.
        
        Level 1: +20 core state/relationship words (total: 26)
        Level 2: +50 extended concepts (total: 76)  
        Level 3: +200 pool words (total: 276)
        Level 4: Full vocabulary unlocked
        """
        current_time = time.time()
        innate_data = self._load_innate_vocab()
        
        if innate_data is None:
            logger.warning(f"[ATOMIC_LANG] Cannot expand vocab - innate_vocab.json not found")
            return
        
        concepts = innate_data.get('concepts', {})
        tiers = innate_data.get('tiers', {})
        
        # Get behavior profile for specialization logging
        behavior_profile = self._get_behavior_profile()
        dominant_actions = self._get_dominant_actions(top_n=2)
        dominant_names = [self.ACTION_HEADS[i] for i in dominant_actions] if dominant_actions else ['none']
        
        added_count = 0
        added_by_frame = {}  # Track what frames we added for logging
        
        if new_level >= 1:
            # Level 1+: Add core state/relationship words
            # BEHAVIOR-DRIVEN: Sort by affinity to organism's playstyle
            core_words = tiers.get('core', [])
            
            # Filter to words we don't have yet
            candidate_words = [w for w in core_words if w not in self.atoms and w in concepts]
            
            # Sort by behavior affinity - words matching organism's actions come first
            sorted_words = self._sort_words_by_behavior_affinity(candidate_words, concepts)
            
            for word in sorted_words:
                if len(self.atoms) >= 26:
                    break
                info = concepts[word]
                frame = info.get('frame', 'universal')
                self._add_innate_concept(word, info, current_time, 'innate_core', 0.5)
                added_count += 1
                added_by_frame[frame] = added_by_frame.get(frame, 0) + 1
        
        if new_level >= 2:
            # Level 2+: Add extended concepts
            # BEHAVIOR-DRIVEN: Sort by affinity to organism's playstyle
            extended_words = tiers.get('extended', [])
            
            candidate_words = [w for w in extended_words if w not in self.atoms and w in concepts]
            sorted_words = self._sort_words_by_behavior_affinity(candidate_words, concepts)
            
            for word in sorted_words:
                if len(self.atoms) >= 76:
                    break
                info = concepts[word]
                frame = info.get('frame', 'universal')
                self._add_innate_concept(word, info, current_time, 'innate_extended', 0.4)
                added_count += 1
                added_by_frame[frame] = added_by_frame.get(frame, 0) + 1
            
            # Also initialize Golden Record and Orientation at level 2
            self._initialize_golden_record_concepts(current_time)
            self._initialize_foundational_orientation(current_time)
        
        if new_level >= 3:
            # Level 3+: Add pool words  
            # BEHAVIOR-DRIVEN: Sort by affinity to organism's playstyle
            pool_words = tiers.get('pool', [])
            
            candidate_words = [w for w in pool_words if w not in self.atoms and w in concepts]
            sorted_words = self._sort_words_by_behavior_affinity(candidate_words, concepts)
            
            for word in sorted_words:
                if len(self.atoms) >= 276:
                    break
                info = concepts[word]
                frame = info.get('frame', 'universal')
                self._add_innate_concept(word, info, current_time, 'innate_rare', 0.25)
                added_count += 1
                added_by_frame[frame] = added_by_frame.get(frame, 0) + 1
        
        # Log specialization details
        frame_breakdown = ', '.join(f"{f}:{c}" for f, c in sorted(added_by_frame.items(), key=lambda x: -x[1]))
        logger.info(f"[ATOMIC_LANG] Organism {self.organism_id}: Level {new_level} SPECIALIZED expansion - "
                   f"dominant actions: {dominant_names}, added {added_count} words (total: {len(self.atoms)}), "
                   f"by frame: [{frame_breakdown}]")
    
    def _initialize_golden_record_concepts(self, current_time: float):
        """
        Initialize Voyager Golden Record concepts - humanity's message to the cosmos.
        
        These are the concepts humanity chose to represent itself to unknown
        intelligences. We use them as foundational teaching material for organisms.
        """
        golden_count = 0
        for word, info in self.GOLDEN_RECORD_CONCEPTS.items():
            if word not in self.atoms:
                atom = LinguisticAtom(
                    concept_id=word,
                    strength=0.7,  # Fixed starting point - differentiation comes from experience
                    source='golden_record',
                    semantic_frame=info['frame'],
                    abstraction_level=info.get('level', 0),
                    acquisition_time=current_time,
                    vp_vitality_affinity=info['vp'][0],
                    vp_pleasure_affinity=info['vp'][1],
                    curiosity_magnetism=0.7  # Golden Record concepts are interesting!
                )
                atom._event_emitter = self.event_emitter
                atom._organism_id = self.organism_id
                self.atoms[word] = atom
                self._concept_order.append(word)
                golden_count += 1
        
        if golden_count > 0:
            logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Added {golden_count} Golden Record concepts")
    
    def _seed_action_head_curiosity(self):
        """
        Make action heads intrinsically interesting without forcing associations.
        
        Philosophy: COAX, DON'T FORCE!
        
        Instead of hardcoding links, we just ensure action heads have:
        1. High BASE magnetism - they START attractive (but can change!)
        2. Pleasurable VP affinity - they feel good to think about
        3. Low initial usage - the novelty bonus kicks in
        
        CRITICAL: We set BASE magnetism high, but organisms' PERSONAL magnetism
        can and WILL diverge based on their outcomes. An organism that keeps
        getting hurt when they think about "compete" will develop LOW personal
        magnetism for "compete" even though the BASE is high.
        
        This is genuine learning, not manipulation.
        """
        for action_head in self.ACTION_HEADS:
            if action_head in self.atoms:
                atom = self.atoms[action_head]
                # Set high BASE magnetism (starting point)
                atom.base_magnetism = max(atom.base_magnetism, 0.9)
                # Initialize personal magnetism to match base (will evolve!)
                atom.curiosity_magnetism = atom.base_magnetism
                # Ensure they feel slightly pleasurable to consider
                atom.vp_pleasure_affinity = max(atom.vp_pleasure_affinity, 0.6)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GROUNDED LANGUAGE MODE - Mastery System Properties
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def mastery_level(self) -> int:
        """Current mastery level (0-4). Higher = more vocabulary unlocked."""
        return self._mastery_level
    
    @mastery_level.setter
    def mastery_level(self, value: int):
        """Set mastery level with bounds checking and vocabulary expansion."""
        old_level = self._mastery_level
        self._mastery_level = max(0, min(4, value))
        if self._mastery_level != old_level:
            logger.info(f"[ATOMIC_LANG] Organism {self.organism_id}: Mastery level {old_level} → {self._mastery_level}")
            
            # CRITICAL: Initialize vocabulary for new mastery level
            # When advancing from level 0, we need to add the level 1+ atoms
            self._expand_vocabulary_for_level(self._mastery_level)
            
            if self.event_emitter:
                try:
                    from causation_explorer import Event
                    self.event_emitter(Event(
                        timestamp=time.time(),
                        component='language',
                        event_type='mastery_advancement',
                        data={
                            'organism_id': self.organism_id,
                            'old_level': old_level,
                            'new_level': self._mastery_level,
                            'vocab_size': len(self.get_available_vocabulary())
                        }
                    ))
                except ImportError:
                    pass
    
    @property
    def total_experiences(self) -> int:
        """Total chat/game experiences accumulated."""
        return self._total_experiences
    
    def record_experience(self):
        """Record that organism had a learning experience."""
        self._total_experiences += 1
    
    def get_available_vocabulary(self) -> List[str]:
        """
        Get vocabulary available at current mastery level.
        
        Level 0: 6 action heads only
        Level 1: +20 core state/relationship words
        Level 2: +50 extended concepts  
        Level 3: +200 pool words
        Level 4: All atoms (semantic graduation)
        
        Returns:
            List of concept_ids available for generation
        """
        if self._mastery_level >= 4:
            # Level 4: All vocabulary unlocked
            return list(self.atoms.keys())
        
        # Get target vocab size for current level
        target_size = self._mastery_vocab_sizes[self._mastery_level]
        
        # Priority ordering for vocabulary selection:
        # 1. Action heads (always first)
        # 2. Core state/relationship words
        # 3. Extended concepts by strength
        # 4. Pool words by strength
        
        available = []
        
        # Level 0+: Always include action heads
        for head in self.ACTION_HEADS:
            if head in self.atoms:
                available.append(head)
        
        if self._mastery_level == 0:
            return available[:target_size]
        
        # Level 1+: Add core words (expanded frame set to match innate_vocab.json)
        # Core tier includes: relationship, state, action, causal, perception, quality, cognitive, etc.
        core_frames = {'state', 'relationship', 'resource', 'question', 'action', 'causal', 
                       'perception', 'quality', 'cognitive', 'emotion', 'social', 'universal'}
        core_words = [
            c for c in self.atoms.keys() 
            if c not in available 
            and self.atoms[c].semantic_frame in core_frames
        ]
        # Sort by strength (strongest first)
        core_words.sort(key=lambda w: self.atoms[w].strength, reverse=True)
        available.extend(core_words[:20])
        
        if self._mastery_level == 1:
            return available[:target_size]
        
        # Level 2+: Add extended concepts
        extended_frames = {'universal', 'perception', 'spatial', 'temporal', 'nature'}
        extended_words = [
            c for c in self.atoms.keys()
            if c not in available
            and (self.atoms[c].semantic_frame in extended_frames or self.atoms[c].source == 'innate_extended')
        ]
        extended_words.sort(key=lambda w: self.atoms[w].strength, reverse=True)
        available.extend(extended_words[:50])
        
        if self._mastery_level == 2:
            return available[:target_size]
        
        # Level 3+: Add pool words
        remaining = [c for c in self.atoms.keys() if c not in available]
        remaining.sort(key=lambda w: self.atoms[w].strength, reverse=True)
        available.extend(remaining[:200])
        
        return available[:target_size]
    
    def can_use_word(self, word: str) -> bool:
        """
        Check if organism has earned the right to use this word at current mastery level.
        
        In grounded mode, organisms must demonstrate competence before accessing vocabulary.
        This prevents premature word assignment from external systems (concept tracker, etc).
        
        Args:
            word: The word/concept to check
            
        Returns:
            True if word is in organism's earned vocabulary, False otherwise
        """
        # Level 4+: Full vocabulary access (semantic graduation)
        if self._mastery_level >= 4:
            return True
        
        # Check if word is in current available vocabulary
        available = self.get_available_vocabulary()
        return word in available
    
    def can_acquire(self) -> bool:
        """
        Check if organism can acquire new vocabulary.
        
        CALLERS MUST CHECK THIS BEFORE ATTEMPTING acquire_concept().
        Returns False if organism is at vocab cap for current mastery level.
        
        Returns:
            True if organism has room for new words, False if at cap
        """
        max_vocab = self._mastery_vocab_sizes[min(self._mastery_level, len(self._mastery_vocab_sizes) - 1)]
        return len(self.atoms) < max_vocab
    
    def check_mastery_advancement(self) -> bool:
        """
        Check if organism should advance to next mastery level.
        
        Criteria:
        - BREADTH: 70% of available words used (usage_count > 5)
        - DEPTH: 50% of available words have 3+ associations
        - EXPERIENCE: Minimum interactions at current level
        
        Returns:
            True if organism should advance, False otherwise
        """
        if self._mastery_level >= 4:
            return False  # Already at max
        
        vocab = self.get_available_vocabulary()
        if not vocab:
            return False
        
        # BREADTH: At least 50% of words used (lowered from 70%)
        # Count words with usage - threshold of 3 uses (was 5)
        used_words = sum(
            1 for w in vocab 
            if w in self.atoms and getattr(self.atoms[w], 'recent_activation_count', 0) > 2
        )
        breadth_ratio = used_words / len(vocab)
        
        # DEPTH: At least 30% have 2+ associations (lowered from 3)
        deep_words = sum(
            1 for w in vocab
            if w in self.atoms and len(getattr(self.atoms[w], 'associations', {})) >= 2
        )
        depth_ratio = deep_words / len(vocab)
        
        # EXPERIENCE: Minimum interactions at current level
        min_exp = self._mastery_min_experiences[self._mastery_level] if self._mastery_level < len(self._mastery_min_experiences) else 1000
        
        should_advance = (
            breadth_ratio >= self._mastery_advancement_ratio and
            depth_ratio >= self._mastery_depth_ratio and
            self._total_experiences >= min_exp
        )
        
        # Debug logging to help diagnose why organisms aren't advancing
        if self._total_experiences > 10 and not should_advance:
            logger.debug(
                f"[MASTERY_CHECK] {self.organism_id[:8]} Level {self._mastery_level}: "
                f"breadth={breadth_ratio:.2f}/{self._mastery_advancement_ratio} "
                f"depth={depth_ratio:.2f}/{self._mastery_depth_ratio} "
                f"exp={self._total_experiences}/{min_exp} "
                f"vocab={len(vocab)}"
            )
        
        if should_advance:
            logger.info(f"[ATOMIC_LANG] Organism {self.organism_id} ready to advance! breadth={breadth_ratio:.2f}, depth={depth_ratio:.2f}, exp={self._total_experiences}")
        
        return should_advance
    
    def try_advance_mastery(self) -> bool:
        """
        Check and advance mastery level if criteria met.
        
        Note: Vocabulary expansion is handled by the mastery_level setter
        via _expand_vocabulary_for_level() - no need to call it here.
        
        Returns:
            True if advanced, False otherwise
        """
        if self.check_mastery_advancement():
            self.mastery_level = self._mastery_level + 1
            return True
        return False
    
    def _initialize_foundational_orientation(self, current_time: float):
        """
        Initialize foundational orientation concepts from ORIENTATION dict.
        
        These are the basic building blocks of symbolic understanding - not hardcoded
        meanings, but anchors that organisms can build associations around through
        experience. Like teaching a child the alphabet before they learn words.
        
        Uses the ORIENTATION class constant which contains categorized word lists.
        """
        orientation_count = 0
        
        # Frame mappings for each category
        frame_map = {
            'alphabet': ('symbol', -1, (0.5, 0.5)),  # (frame, level, vp)
            'numbers': ('quantity', 0, (0.5, 0.5)),
            'colors': ('perception', 0, (0.5, 0.6)),
            'directions': ('spatial', 0, (0.5, 0.5)),
            'time': ('temporal', 0, (0.5, 0.5)),
            'existence': ('state', 0, (0.5, 0.5)),
            'relationships': ('relationship', 0, (0.5, 0.6)),
            'nature': ('nature', 0, (0.5, 0.6)),
            'actions': ('action', 0, (0.5, 0.5)),
            'qualities': ('quality', 0, (0.5, 0.5)),
            'questions': ('question', 0, (0.6, 0.6)),
            'universals': ('universal', 0, (0.5, 0.7)),
        }
        
        for category, words in self.ORIENTATION.items():
            frame_info = frame_map.get(category, ('unknown', 0, (0.5, 0.5)))
            frame, level, vp = frame_info
            
            for word in words:
                if word not in self.atoms:
                    # Determine magnetism based on category
                    if category == 'questions':
                        base_mag = 0.85  # Questions draw curiosity
                    elif category == 'universals':
                        base_mag = 0.7  # Universal concepts are interesting
                    elif category == 'actions' and word in self.ACTION_HEADS:
                        base_mag = 0.9  # Action heads get high magnetism
                    elif category == 'alphabet':
                        base_mag = 0.3  # Letters are neutral anchors
                    else:
                        base_mag = 0.5  # Default
                    
                    atom = LinguisticAtom(
                        concept_id=word,
                        strength=0.35,  # Fixed starting point - differentiation comes from experience
                        source='foundational_orientation',
                        semantic_frame=frame,
                        abstraction_level=level,
                        acquisition_time=current_time,
                        vp_vitality_affinity=vp[0],
                        vp_pleasure_affinity=vp[1],
                        base_magnetism=base_mag,
                        curiosity_magnetism=base_mag
                    )
                    atom._event_emitter = self.event_emitter
                    atom._organism_id = self.organism_id
                    self.atoms[word] = atom
                    self._concept_order.append(word)
                    orientation_count += 1
        
        if orientation_count > 0:
            logger.debug(f"[ATOMIC_LANG] Organism {self.organism_id}: Added {orientation_count} foundational orientation concepts")
    
    def _add_innate_concept(self, word: str, info: dict, current_time: float, 
                           source: str, base_strength: float):
        """Helper to add an innate concept atom with personal magnetism system."""
        vp = info.get('vp', (0.5, 0.5))
        
        # Determine semantic frame - check if it's an action head
        frame = info.get('frame', 'unknown')
        if word in self.ACTION_HEADS:
            frame = 'action_head'
        
        # ═══════════════════════════════════════════════════════════════
        # PERSONAL MAGNETISM SYSTEM - Coax, Don't Trap!
        #
        # Set BASE magnetism (starting point) - but personal magnetism
        # will EVOLVE based on this organism's outcomes!
        #
        # Action heads start HIGH but can decrease if they hurt the organism.
        # Questions start HIGH because curiosity should beget curiosity.
        # Regular words start NEUTRAL and can go either direction.
        # ═══════════════════════════════════════════════════════════════
        if word in self.ACTION_HEADS:
            base_mag = 0.9  # Action heads START attractive (but can change!)
        elif frame == 'question' or word in ['why', 'how', 'what', 'where', 'when', 'who']:
            base_mag = 0.85  # Questions draw curious minds
        elif word in self.GOLDEN_RECORD_CONCEPTS:
            base_mag = 0.7  # Golden Record concepts are interesting
        elif frame in ['universal', 'relationship']:
            base_mag = 0.65  # Social/universal concepts moderately magnetic
        else:
            base_mag = info.get('magnetism', 0.5)  # Default or explicit magnetism
        
        atom = LinguisticAtom(
            concept_id=word,
            strength=base_strength,  # Fixed starting point - differentiation comes from experience
            source=source,
            semantic_frame=frame,
            abstraction_level=info.get('level', 0),
            acquisition_time=current_time,
            vp_vitality_affinity=vp[0] if isinstance(vp, (list, tuple)) else 0.5,
            vp_pleasure_affinity=vp[1] if isinstance(vp, (list, tuple)) else 0.5,
            base_magnetism=base_mag,  # Starting point
            curiosity_magnetism=base_mag  # Personal magnetism starts at base (will evolve!)
        )
        atom._event_emitter = self.event_emitter
        atom._organism_id = self.organism_id
        self.atoms[word] = atom
        self._concept_order.append(word)
    
    def get_action_head(self, word: str) -> Optional[str]:
        """
        Get the action head for a word (if it's an action head itself).
        
        With the new foundational orientation system, we don't have hardcoded
        synonyms. This now just returns the word if it's an action head, else None.
        Organisms learn action-word associations through experience, not hardcoding.
        
        Returns:
            The action head if word is one, else None
        """
        return word if word in self.ACTION_HEADS else None
    
    def is_action_word(self, word: str) -> bool:
        """Check if a word is an action head."""
        return word in self.ACTION_HEADS
    
    def get_high_magnetism_concepts(self, threshold: float = 0.7) -> List[str]:
        """
        Get concepts with high curiosity magnetism.
        
        These are the concepts that naturally attract curious exploration -
        action heads, questions, Golden Record concepts, etc.
        
        Args:
            threshold: Minimum magnetism level (default 0.7)
            
        Returns:
            List of concept IDs with magnetism >= threshold
        """
        return [
            cid for cid, atom in self.atoms.items()
            if atom.curiosity_magnetism >= threshold
        ]
    
    def update_magnetism_from_action(self, active_concepts: List[str], outcome: float, 
                                     action_type: str = "", reason: str = ""):
        """
        Update personal magnetism for concepts that were active during an action.
        
        THIS IS THE CORE LEARNING MECHANISM!
        
        When an organism takes an action while thinking about certain concepts,
        the outcome of that action shapes their future relationship with those concepts.
        
        Good outcome → increased magnetism (want to think about this more)
        Bad outcome → decreased magnetism (learn to avoid this thought pattern)
        
        Args:
            active_concepts: List of concept IDs that were "active" during action
            outcome: Result of the action (-1 to +1)
            action_type: Type of action taken (for context)
            reason: Why this outcome happened (for causation tracking)
        """
        for concept_id in active_concepts:
            if concept_id in self.atoms:
                self.atoms[concept_id].update_magnetism_from_outcome(
                    outcome, 
                    reason=f"{action_type}: {reason}" if action_type else reason
                )
    
    def decay_all_satiation(self, decay_amount: float = 0.02):
        """
        Decay satiation for all concepts - let them become "fresh" again.
        
        Call this periodically (e.g., each simulation step) to allow
        organisms to rediscover concepts they've become bored with.
        
        Args:
            decay_amount: How much satiation to decay (default 0.02)
        """
        for atom in self.atoms.values():
            atom.decay_satiation(decay_amount)
    
    def get_magnetism_divergence(self) -> Dict[str, float]:
        """
        Get how much each concept's personal magnetism has diverged from base.
        
        Useful for understanding what the organism has LEARNED:
        - Positive divergence = they like this more than default
        - Negative divergence = they've learned to avoid this
        
        Returns:
            Dict mapping concept_id to (personal - base) magnetism
        """
        divergence = {}
        for cid, atom in self.atoms.items():
            div = atom.curiosity_magnetism - atom.base_magnetism
            if abs(div) > 0.05:  # Only report significant divergence
                divergence[cid] = div
        return divergence
    
    def get_learned_preferences(self) -> Dict[str, Dict]:
        """
        Get summary of what this organism has learned to prefer/avoid.
        
        Returns:
            Dict with 'attracted_to' and 'avoiding' lists
        """
        attracted = []
        avoiding = []
        
        for cid, atom in self.atoms.items():
            div = atom.curiosity_magnetism - atom.base_magnetism
            avg_outcome = sum(atom.outcome_history) / len(atom.outcome_history) if atom.outcome_history else 0
            
            if div > 0.1 or (atom.outcome_history and avg_outcome > 0.3):
                attracted.append({
                    'concept': cid,
                    'magnetism': atom.curiosity_magnetism,
                    'divergence': div,
                    'avg_outcome': avg_outcome
                })
            elif div < -0.1 or (atom.outcome_history and avg_outcome < -0.3):
                avoiding.append({
                    'concept': cid,
                    'magnetism': atom.curiosity_magnetism,
                    'divergence': div,
                    'avg_outcome': avg_outcome
                })
        
        # Sort by strength of preference
        attracted.sort(key=lambda x: x['magnetism'], reverse=True)
        avoiding.sort(key=lambda x: x['magnetism'])
        
        return {
            'attracted_to': attracted[:10],  # Top 10 attractions
            'avoiding': avoiding[:10]  # Top 10 avoidances
        }

    
    def acquire_concept(self, concept_id: str, source: str, semantic_frame: str = 'unknown',
                       initial_strength: float = 0.3, reason: str = "acquired") -> Optional[LinguisticAtom]:
        """
        Acquire a new concept (learn a new word).
        
        This is a MAJOR EVENT for causation tracking - the organism
        learned something new!
        
        MASTERY GATING: In grounded mode (levels 0-3), organisms can only
        acquire concepts through mastery advancement - external teaching/
        absorption is blocked. This prevents vocabulary leaking past the cap.
        
        Args:
            concept_id: Unique concept identifier
            source: How acquired ('observed', 'taught', 'discovered')
            semantic_frame: Category of concept
            initial_strength: Starting strength
            reason: Why this concept was acquired
            
        Returns:
            The newly created or existing LinguisticAtom, or None if blocked by mastery
        """
        if concept_id in self.atoms:
            # Already have this concept - strengthen it instead
            self.atoms[concept_id].update_strength(0.1, f"reinforced: {reason}")
            return self.atoms[concept_id]
        
        # ═══════════════════════════════════════════════════════════════
        # MASTERY GATING - Block acquisition if beyond vocab cap
        # ═══════════════════════════════════════════════════════════════
        max_vocab = self._mastery_vocab_sizes[min(self._mastery_level, len(self._mastery_vocab_sizes) - 1)]
        is_mastery_gated = max_vocab < 20000  # True for levels 0-3
        
        if is_mastery_gated:
            # Check if we're at or beyond the vocab cap for current level
            if len(self.atoms) >= max_vocab:
                # Block acquisition - organism must advance mastery to get more words
                logger.debug(
                    f"[MASTERY_GATE] {self.organism_id[:8]}: Blocked acquisition of '{concept_id}' "
                    f"(source={source}) - at vocab cap {len(self.atoms)}/{max_vocab} for level {self._mastery_level}"
                )
                return None
        
        current_time = time.time()
        
        # Create new atom
        atom = LinguisticAtom(
            concept_id=concept_id,
            strength=initial_strength,
            source=source,
            semantic_frame=semantic_frame,
            abstraction_level=0 if semantic_frame in ['action', 'state', 'resource'] else 1,
            acquisition_time=current_time
        )
        atom._event_emitter = self.event_emitter
        atom._organism_id = self.organism_id
        
        self.atoms[concept_id] = atom
        self._concept_order.append(concept_id)
        self.total_concepts_acquired += 1
        
        # Emit concept acquisition event
        self._emit_concept_acquired(concept_id, source, reason)
        
        return atom
    
    def _emit_concept_acquired(self, concept_id: str, source: str, reason: str):
        """Emit event when organism acquires new concept."""
        if not self.event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='concept_acquired',
                data={
                    'organism_id': self.organism_id,
                    'concept': concept_id,
                    'source': source,
                    'reason': reason,
                    'total_concepts': len(self.atoms),
                    'semantic_frame': self.atoms[concept_id].semantic_frame
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    def strengthen_concept(self, concept_id: str, delta: float, reason: str):
        """
        Strengthen (or weaken) a concept.
        
        Args:
            concept_id: Concept to modify
            delta: Change in strength (positive or negative)
            reason: Why the change happened
        """
        if concept_id not in self.atoms:
            logger.debug(f"[ATOMIC_LANG] Cannot strengthen unknown concept: {concept_id}")
            return
            
        self.atoms[concept_id].update_strength(delta, reason)
    
    def form_association(self, source_concept: str, target_concept: str, 
                        strength: float, reason: str):
        """
        Form association between two concepts.
        
        This is how organisms build semantic networks - by linking
        concepts through experience.
        
        GROUNDED LANGUAGE MODE:
        In mastery-gated mode (levels 0-3), associations can only form between
        concepts the organism ALREADY has. New concepts are NOT implicitly created.
        This ensures vocabulary growth is governed by the mastery system, not
        bypassed by association formation.
        
        Args:
            source_concept: The primary concept
            target_concept: The concept to associate with
            strength: Association strength (-1.0 to 1.0)
            reason: Why this association formed
        """
        # GROUNDED MODE CHECK: Don't implicitly acquire concepts in mastery-gated mode
        # Organisms must EARN vocabulary through mastery advancement
        max_vocab = self._mastery_vocab_sizes[min(self._mastery_level, len(self._mastery_vocab_sizes) - 1)]
        is_mastery_gated = max_vocab < 20000  # True for levels 0-3
        
        if is_mastery_gated:
            # In grounded mode, only form associations between EXISTING atoms
            # Don't create new atoms - that bypasses the mastery system!
            if source_concept not in self.atoms:
                return  # Source must already be known
            if target_concept not in self.atoms:
                # Can't form association to unknown word - organism hasn't learned it yet
                # This is intentional: associations are between KNOWN concepts only
                return
        else:
            # Non-grounded mode (level 4+): Allow implicit concept acquisition
            if source_concept not in self.atoms:
                self.acquire_concept(source_concept, 'implicit', reason=f"needed for association with {target_concept}")
            if target_concept not in self.atoms:
                self.acquire_concept(target_concept, 'implicit', reason=f"needed for association with {source_concept}")
        
        # Form the association
        self.atoms[source_concept].form_association(target_concept, strength, reason)
        self.total_associations_formed += 1
    
    def get_activated_concepts(self, vp_state: Tuple[float, float], 
                               context: Optional[str] = None,
                               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Get concepts most activated by current VP state and context.
        
        This is how organisms "think" - VP state activates relevant concepts.
        
        Args:
            vp_state: (vitality, pleasure) tuple
            context: Optional context string
            top_k: Number of top concepts to return
            
        Returns:
            List of (concept_id, activation_score) tuples
        """
        vitality, pleasure = vp_state
        activations = []
        
        for concept_id, atom in self.atoms.items():
            # Base activation from strength
            activation = atom.strength
            
            # VP affinity modulation
            vp_match = 1.0 - 0.5 * (
                abs(vitality - atom.vp_vitality_affinity) +
                abs(pleasure - atom.vp_pleasure_affinity)
            )
            activation *= vp_match
            
            # Recency boost
            if atom.last_used_time > 0:
                recency = 1.0 / (1.0 + (time.time() - atom.last_used_time) / 60)
                activation *= (0.7 + 0.3 * recency)
            
            activations.append((concept_id, activation))
        
        # Sort by activation
        activations.sort(key=lambda x: x[1], reverse=True)
        return activations[:top_k]
    
    def get_associated_concepts(self, concept_id: str, min_strength: float = 0.2) -> List[Tuple[str, float]]:
        """
        Get concepts associated with a given concept.
        
        Args:
            concept_id: The concept to get associations for
            min_strength: Minimum association strength
            
        Returns:
            List of (associated_concept, strength) tuples
        """
        if concept_id not in self.atoms:
            return []
            
        associations = []
        for target, assoc in self.atoms[concept_id].associations.items():
            if abs(assoc.strength) >= min_strength:
                associations.append((target, assoc.strength))
        
        return sorted(associations, key=lambda x: abs(x[1]), reverse=True)
    
    def get_word_vector(self, word: str, embedding_dim: int = 64) -> Optional[np.ndarray]:
        """
        Get a semantic vector for a specific word based on its atomic properties.
        
        This is THE ROOT for vector retrieval — embeddings derived directly from
        the organism's learned atomic structure (strength, associations, VP affinity).
        
        Vector components (64-dim default):
        - [0]: strength (salience)
        - [1]: usage_count normalized
        - [2]: abstraction_level
        - [3]: vp_vitality_affinity
        - [4]: vp_pleasure_affinity
        - [5-14]: semantic frame one-hot (10 frames)
        - [15-64]: association vector (top associations hashed to positions)
        
        Args:
            word: The word/concept to get vector for
            embedding_dim: Desired vector dimension (default 64)
            
        Returns:
            Numpy array of shape (embedding_dim,) or None if word not in atoms
        """
        if word not in self.atoms:
            return None
        
        atom = self.atoms[word]
        vec = np.zeros(embedding_dim, dtype=np.float32)
        
        # Core properties [0-4]
        vec[0] = atom.strength
        vec[1] = min(atom.usage_count / 100.0, 1.0)  # Normalize usage
        vec[2] = atom.abstraction_level / 2.0  # 0, 0.5, or 1.0
        vec[3] = atom.vp_vitality_affinity
        vec[4] = atom.vp_pleasure_affinity
        
        # Semantic frame one-hot [5-14]
        frame_map = {
            'action': 5, 'state': 6, 'quality': 7, 'relationship': 8,
            'temporal': 9, 'spatial': 10, 'resource': 11, 'unknown': 12,
            'innate_core': 13, 'innate_extended': 14
        }
        frame_idx = frame_map.get(atom.semantic_frame, 12)
        if frame_idx < embedding_dim:
            vec[frame_idx] = 1.0
        
        # Association vector [15-64]: hash associations into remaining dimensions
        assoc_start = 15
        assoc_dim = embedding_dim - assoc_start
        if assoc_dim > 0 and atom.associations:
            for target, assoc in atom.associations.items():
                # Hash target word to position in association subspace
                hash_idx = hash(target) % assoc_dim
                vec[assoc_start + hash_idx] += assoc.strength * 0.5
        
        # Normalize association subspace
        assoc_slice = vec[assoc_start:]
        assoc_norm = np.linalg.norm(assoc_slice)
        if assoc_norm > 0:
            vec[assoc_start:] = assoc_slice / assoc_norm
        
        return vec
    
    def find_similar_words(self, query_word: str, top_k: int = 10, 
                          min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """
        Find words most similar to query using atomic-derived vectors.
        
        This is VECTOR RETRIEVAL rooted in the atomic vocabulary itself.
        
        Args:
            query_word: Word to find similar words for
            top_k: Number of results
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of (word, similarity) tuples sorted by similarity descending
        """
        query_vec = self.get_word_vector(query_word)
        if query_vec is None:
            return []
        
        # Normalize query
        query_norm = np.linalg.norm(query_vec)
        if query_norm < 1e-8:
            return []
        query_vec = query_vec / query_norm
        
        results = []
        for word in self.atoms:
            if word == query_word:
                continue
            
            word_vec = self.get_word_vector(word)
            if word_vec is None:
                continue
            
            # Cosine similarity
            word_norm = np.linalg.norm(word_vec)
            if word_norm < 1e-8:
                continue
            
            similarity = np.dot(query_vec, word_vec / word_norm)
            if similarity >= min_similarity:
                results.append((word, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def find_words_for_state(self, organism_state: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find words whose atomic vectors are most similar to organism state.
        
        Enables ASSOCIATIVE REASONING: organism state → relevant words.
        
        Args:
            organism_state: Organism's state vector (any dimension, will be projected)
            top_k: Number of results
            
        Returns:
            List of (word, similarity) tuples
        """
        if organism_state is None or len(organism_state) == 0:
            return []
        
        # Project state to 64-dim (truncate or pad)
        embedding_dim = 64
        state_vec = np.zeros(embedding_dim, dtype=np.float32)
        copy_len = min(len(organism_state), embedding_dim)
        state_vec[:copy_len] = organism_state[:copy_len]
        
        # Normalize
        state_norm = np.linalg.norm(state_vec)
        if state_norm < 1e-8:
            return []
        state_vec = state_vec / state_norm
        
        results = []
        for word in self.atoms:
            word_vec = self.get_word_vector(word, embedding_dim)
            if word_vec is None:
                continue
            
            word_norm = np.linalg.norm(word_vec)
            if word_norm < 1e-8:
                continue
            
            similarity = np.dot(state_vec, word_vec / word_norm)
            results.append((word, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def query_vocabulary(self, 
                        query_word: str = None,
                        organism_state: np.ndarray = None,
                        curiosity: float = 0.5,
                        aggression: float = 0.5,
                        social_affinity: float = 0.5,
                        exploration_rate: float = 0.1,
                        top_k: int = 10) -> List[Tuple[str, float]]:
        """
        TRAIT-DRIVEN SEMANTIC QUERY: Use organism reasoning traits to guide word retrieval.
        
        This is THE QUERY MECHANIC that makes vector search behavioral.
        
        How traits affect the search:
        - curiosity (0-1): Higher = broader search, more associations explored, 
                          more novel/rare words surfaced
        - aggression (0-1): Higher = prefer action words, competitive concepts
                           Lower = prefer state words, passive concepts
        - social_affinity (0-1): Higher = prefer relationship/cooperation words
                                Lower = prefer solitary/individual concepts  
        - exploration_rate (0-1): Random exploration - chance to include random words
                                 for serendipitous discovery
        
        Args:
            query_word: Seed word to expand from (optional)
            organism_state: State vector to match (optional)
            curiosity: Organism's curiosity trait [0-1]
            aggression: Organism's aggression trait [0-1]
            social_affinity: Organism's social trait [0-1]
            exploration_rate: Chance of random exploration [0-1]
            top_k: Number of results to return
            
        Returns:
            List of (word, score) tuples sorted by trait-adjusted relevance
        """
        word_scores: Dict[str, float] = {}
        
        # Step 1: Seed from query word (if provided)
        if query_word and query_word in self.atoms:
            # Base: similar words
            similar = self.find_similar_words(query_word, top_k=int(top_k * (1 + curiosity)))
            for word, sim in similar:
                word_scores[word] = word_scores.get(word, 0.0) + sim
            
            # Curiosity: follow more association chains
            if curiosity > 0.3:
                atom = self.atoms[query_word]
                # More curious = explore more associations
                num_assoc = int(len(atom.associations) * curiosity)
                for target, assoc in list(atom.associations.items())[:num_assoc]:
                    if target in self.atoms:
                        word_scores[target] = word_scores.get(target, 0.0) + abs(assoc.strength) * curiosity
                        # High curiosity: follow second-order associations
                        if curiosity > 0.7 and target in self.atoms:
                            for t2, a2 in list(self.atoms[target].associations.items())[:3]:
                                if t2 in self.atoms and t2 != query_word:
                                    word_scores[t2] = word_scores.get(t2, 0.0) + abs(a2.strength) * curiosity * 0.5
        
        # Step 2: Seed from organism state (if provided)
        if organism_state is not None:
            state_words = self.find_words_for_state(organism_state, top_k=top_k)
            for word, sim in state_words:
                word_scores[word] = word_scores.get(word, 0.0) + sim * 0.8
        
        # Step 3: Apply trait-based filtering/boosting
        # Calculate skepticism from curiosity (they're inversely related)
        skepticism = 1.0 - curiosity
        
        for word in list(word_scores.keys()):
            if word not in self.atoms:
                continue
            atom = self.atoms[word]
            
            # Aggression bias: boost action words, penalize passive
            if atom.semantic_frame == 'action':
                word_scores[word] *= (1.0 + aggression * 0.5)  # Up to 50% boost for aggressive
            elif atom.semantic_frame == 'state':
                word_scores[word] *= (1.0 - aggression * 0.3)  # Up to 30% penalty for aggressive
            
            # Social affinity bias: boost relationship words
            if atom.semantic_frame == 'relationship':
                word_scores[word] *= (1.0 + social_affinity * 0.5)
            
            # Curiosity bonus for rare/novel words (low usage)
            if curiosity > 0.5 and atom.usage_count < 5:
                word_scores[word] *= (1.0 + (curiosity - 0.5) * 0.4)  # Up to 20% bonus
            
            # ═══════════════════════════════════════════════════════════════
            # PERSONAL MAGNETISM - Coax, Don't Trap!
            # 
            # Uses get_effective_magnetism() which considers:
            # 1. Personal magnetism (evolved from outcomes)
            # 2. Skepticism (high skepticism = resistant to magnetism)
            # 3. Satiation (overused concepts lose appeal)
            # 4. Outcome history (bad outcomes = learned avoidance)
            #
            # This is GENUINE learning, not Pied Piper manipulation.
            # Organisms can and WILL diverge from base magnetism!
            # ═══════════════════════════════════════════════════════════════
            if curiosity > 0.2:
                # Get EFFECTIVE magnetism considering skepticism, satiation, outcomes
                effective_magnetism = atom.get_effective_magnetism(skepticism)
                
                # Magnetism bonus scales with curiosity and EFFECTIVE (not raw) magnetism
                # This means skeptical organisms get much smaller bonuses
                # And concepts with bad outcome history get reduced attraction
                magnetism_bonus = effective_magnetism * curiosity * 0.5
                word_scores[word] *= (1.0 + magnetism_bonus)
                
                # Update satiation (this concept was considered)
                atom.update_satiation()
            
            # Skepticism defense: prefer well-established, proven words
            if skepticism > 0.4 and atom.usage_count > 10:
                # Check outcome history - skeptics trust concepts with good track records
                if atom.outcome_history:
                    avg_outcome = sum(atom.outcome_history) / len(atom.outcome_history)
                    if avg_outcome > 0:
                        # Good track record + high skepticism = trust this word
                        word_scores[word] *= (1.0 + skepticism * avg_outcome * 0.4)
                    elif avg_outcome < -0.3:
                        # Bad track record + high skepticism = AVOID this word
                        word_scores[word] *= (1.0 + avg_outcome * skepticism * 0.5)
                else:
                    # No track record, slight boost for familiarity
                    word_scores[word] *= (1.0 + (skepticism - 0.4) * 0.2)
        
        # Step 4: Exploration - EFFECTIVE magnetism-weighted random word injection
        # Concepts organisms have learned to like are more likely to be "stumbled upon"
        if exploration_rate > 0 and len(self.atoms) > 0:
            num_random = max(1, int(top_k * exploration_rate))
            all_words = list(self.atoms.keys())
            
            # Weight by EFFECTIVE magnetism (considers personal history!)
            magnetism_weights = np.array([
                self.atoms[w].get_effective_magnetism(skepticism) for w in all_words
            ])
            # Add small epsilon to avoid division by zero
            magnetism_weights = magnetism_weights + 0.01
            # Normalize to probability distribution
            magnetism_probs = magnetism_weights / magnetism_weights.sum()
            
            for _ in range(num_random):
                if np.random.random() < exploration_rate:
                    # Personal-magnetism-weighted random selection
                    random_word = np.random.choice(all_words, p=magnetism_probs)
                    if random_word not in word_scores:
                        # Score based on effective magnetism
                        eff_mag = self.atoms[random_word].get_effective_magnetism(skepticism)
                        word_scores[random_word] = 0.3 * exploration_rate * (0.5 + eff_mag)
        
        # Step 5: Sort and return
        sorted_results = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def to_embedding(self, embedding_dim: Optional[int] = None) -> np.ndarray:
        """
        Convert atomic representation to dense vector for neural network.
        
        This bridges atomic tracking with neural efficiency.
        
        Args:
            embedding_dim: Desired embedding dimension (default: num_concepts)
            
        Returns:
            Dense numpy array representing linguistic state
        """
        # Extract strengths in deterministic order
        strengths = np.array([self.atoms[c].strength for c in self._concept_order])
        
        if embedding_dim is None or embedding_dim == len(strengths):
            return strengths
        
        # Project to desired dimension (simple linear projection for now)
        if embedding_dim < len(strengths):
            # Downsample by taking top concepts
            indices = np.argsort(strengths)[-embedding_dim:]
            return strengths[indices]
        else:
            # Upsample by padding
            result = np.zeros(embedding_dim)
            result[:len(strengths)] = strengths
            return result
    
    def to_tensor(self, embedding_dim: Optional[int] = None) -> 'torch.Tensor':
        """
        Convert to PyTorch tensor for neural network integration.
        
        Args:
            embedding_dim: Desired embedding dimension
            
        Returns:
            PyTorch tensor
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch required for tensor conversion")
        
        embedding = self.to_embedding(embedding_dim)
        return torch.FloatTensor(embedding)
    
    def get_concept_graph(self) -> Dict[str, Any]:
        """
        Get full concept graph for visualization.
        
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        nodes = []
        edges = []
        
        for concept_id, atom in self.atoms.items():
            nodes.append({
                'id': concept_id,
                'strength': atom.strength,
                'frame': atom.semantic_frame,
                'source': atom.source
            })
            
            for target, assoc in atom.associations.items():
                edges.append({
                    'source': concept_id,
                    'target': target,
                    'strength': assoc.strength,
                    'reason': assoc.formation_reason
                })
        
        return {'nodes': nodes, 'edges': edges}
    
    def compute_dialect_signature(self, fixed_length: int = 32) -> np.ndarray:
        """
        Compute a signature vector representing this organism's "dialect".
        
        Used for clustering organisms by linguistic similarity.
        
        Args:
            fixed_length: Fixed length for the signature vector (default 32)
        
        Returns:
            Normalized signature vector of fixed length
        """
        # Combine concept strengths with association patterns
        signature = []
        
        # Concept strengths (normalized) - use sorted concepts
        sorted_concepts = sorted(self._concept_order)
        for concept_id in sorted_concepts[:fixed_length - 4]:  # Reserve 4 slots for meta-features
            signature.append(self.atoms[concept_id].strength)
        
        # Pad to fixed_length - 4 if fewer concepts
        while len(signature) < fixed_length - 4:
            signature.append(0.0)
        
        # Add association density metrics
        total_associations = sum(len(a.associations) for a in self.atoms.values())
        signature.append(total_associations / max(1, len(self.atoms)))
        
        # Add abstraction level distribution
        level_counts = defaultdict(int)
        for atom in self.atoms.values():
            level_counts[atom.abstraction_level] += 1
        
        for level in range(3):
            signature.append(level_counts[level] / max(1, len(self.atoms)))
        
        return np.array(signature, dtype=np.float32)
    
    def _get_action_related_words(self, action: int, outcome: float) -> List[str]:
        """
        Get words semantically related to an action for breadth tracking.
        
        This maps actions to related concepts that should also be "activated"
        when an organism takes that action. Without this, only 6 action words
        ever get activation counts, making Level 1→2 advancement impossible.
        
        Returns list of related words from available vocabulary.
        """
        # Map actions to semantically related concept categories
        # FIXED: Use ACTUAL Level 1 vocabulary words from innate_vocab.json:
        # abandon, avoid, compete, cooperate, create, curiosity, explore, force, hope, 
        # ignore, isolate, love, miss, move, neglect, overlook, pressure, prevent, 
        # release, reproduce, rest, separate, share, stop, suppress, together
        action_word_map = {
            0: ['move', 'explore', 'release', 'curiosity', 'hope'],  # MOVE - exploration/motion
            1: ['cooperate', 'share', 'together', 'love', 'hope'],   # COOPERATE - social/positive
            2: ['compete', 'force', 'pressure', 'suppress', 'stop'], # COMPETE - aggressive
            3: ['rest', 'stop', 'ignore', 'neglect', 'overlook'],    # REST - inaction
            4: ['reproduce', 'create', 'love', 'hope', 'together'],  # REPRODUCE - creation
            5: ['isolate', 'separate', 'avoid', 'prevent', 'abandon', 'miss', 'ignore'],  # ISOLATE - avoidance
        }
        
        # Get related words for this action
        related = action_word_map.get(action, [])
        
        # Filter to only words in our vocabulary
        available = self.get_available_vocabulary()
        activated = [w for w in related if w in available]
        
        # AGGRESSIVE breadth activation - activate ALL matching words, not just a few
        # Level 1 has 26 words - need 50% breadth (13 words with count > 2)
        # Each action should activate 4-7 words to spread activation broadly
        return activated  # Return ALL matching words, not limited subset
    
    def apply_experience(self, action: int, outcome: float, context: Dict[str, Any]):
        """
        Update language atoms based on organism experience.
        
        This is called after each organism action to update linguistic
        representation based on what happened.
        
        Args:
            action: Action index taken (0-5)
            outcome: Reward/outcome of action (-1 to 1)
            context: Additional context (VP state, nearby organisms, etc.)
        """
        # Canonical action order: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
        action_concepts = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        
        if 0 <= action < len(action_concepts):
            action_concept = action_concepts[action]
            
            # ═══════════════════════════════════════════════════════════════════════════
            # MASTERY TRACKING: Update breadth criterion (activation count)
            # This tracks that the organism USED this action word, not just considered it
            # ═══════════════════════════════════════════════════════════════════════════
            if action_concept in self.atoms:
                self.atoms[action_concept].update_satiation()  # Increments recent_activation_count
            
            # ═══════════════════════════════════════════════════════════════════════════
            # FIX: Also activate semantically related words from vocabulary
            # Without this, only 6 action words ever get activated, making Level 1→2
            # advancement impossible (breadth stuck at 6/26 = 23% < 50% threshold)
            # ═══════════════════════════════════════════════════════════════════════════
            related_words = self._get_action_related_words(action, outcome)
            for word in related_words:
                if word in self.atoms and word != action_concept:
                    self.atoms[word].update_satiation()
            
            # Record this as a learning experience for mastery advancement
            self.record_experience()
            
            # Strengthen action concept based on outcome
            if outcome > 0:
                reason = f"positive_outcome_{outcome:.2f}"
                self.strengthen_concept(action_concept, outcome * 0.1, reason)
            else:
                reason = f"negative_outcome_{outcome:.2f}"
                self.strengthen_concept(action_concept, outcome * 0.05, reason)  # Slower weakening
            
            # 🆕 UPDATE PERSONAL MAGNETISM - organism learns from outcomes
            # This is the key learning signal: actions that worked become more attractive
            # Actions that failed become less attractive (and harder/slower to recover)
            self.update_magnetism_from_action(
                active_concepts=[action_concept],
                outcome=outcome,
                action_type=action_concept,
                reason=f"action_outcome_{outcome:.2f}"
            )
            
            # Form associations based on context
            vp_state = context.get('vp_state', (0.5, 0.5))
            
            # ═══════════════════════════════════════════════════════════════════════════
            # GROUNDED LANGUAGE MODE: Build associations between EXISTING vocabulary only
            # Level 0 organisms know only 6 ACTION_HEADS, so associations form between them
            # This creates a semantic web from limited vocabulary - organisms learn that:
            #   cooperate <-> reproduce (social actions)
            #   compete <-> move (aggressive/active actions)
            #   rest <-> isolate (defensive actions)
            # As organisms advance levels, they can form richer associations with new words
            # ═══════════════════════════════════════════════════════════════════════════
            
            # If cooperated successfully, associate with other social/growth actions
            if action == 1 and outcome > 0:  # COOPERATE
                self.form_association('cooperate', 'reproduce', outcome * 0.3, 'social_synergy')
                self.form_association('cooperate', 'rest', outcome * 0.2, 'cooperation_enables_rest')
                self.form_association('cooperate', 'move', outcome * 0.15, 'group_movement')
            
            # If competed successfully, associate with active/dominant actions
            if action == 2 and outcome > 0:  # COMPETE
                self.form_association('compete', 'move', outcome * 0.25, 'chase_opponent')
                self.form_association('compete', 'isolate', outcome * 0.2, 'territorial')
                self.form_association('compete', 'rest', outcome * 0.1, 'post_battle_rest')
            
            # If reproduced successfully, associate with enabling actions
            if action == 4 and outcome > 0:  # REPRODUCE
                self.form_association('reproduce', 'cooperate', outcome * 0.3, 'needs_partner')
                self.form_association('reproduce', 'rest', outcome * 0.2, 'recovery_after')
                self.form_association('reproduce', 'move', outcome * 0.15, 'find_partner')
            
            # If moved successfully, associate with exploration-related actions
            if action == 0 and outcome > 0:  # MOVE
                self.form_association('move', 'compete', outcome * 0.2, 'approach_rival')
                self.form_association('move', 'cooperate', outcome * 0.2, 'approach_ally')
                self.form_association('move', 'isolate', outcome * 0.15, 'retreat')
            
            # If rested successfully, associate with recovery-related actions
            if action == 3 and outcome > 0:  # REST
                self.form_association('rest', 'compete', outcome * 0.2, 'preparing_for_battle')
                self.form_association('rest', 'reproduce', outcome * 0.2, 'energy_for_life')
                self.form_association('rest', 'isolate', outcome * 0.15, 'safe_rest')
            
            # If isolated successfully, associate with defensive actions
            if action == 5 and outcome > 0:  # ISOLATE
                self.form_association('isolate', 'rest', outcome * 0.25, 'safe_recovery')
                self.form_association('isolate', 'move', outcome * 0.2, 'escape')
                self.form_association('isolate', 'compete', outcome * 0.15, 'prepare_ambush')
            
            # ═══════════════════════════════════════════════════════════════════════════
            # FIX FOR DEPTH: Form associations between action-related words too!
            # Without this, only action heads get associations and depth is stuck at 6/26
            # Level 1→2 requires 30% depth (8/26 words with 2+ associations)
            # ═══════════════════════════════════════════════════════════════════════════
            if outcome > 0:
                related_words = self._get_action_related_words(action, outcome)
                # Form associations between action head and its related words
                for word in related_words:
                    if word != action_concept:
                        self.form_association(action_concept, word, outcome * 0.2, f'{action_concept}_related')
                        self.form_association(word, action_concept, outcome * 0.2, f'related_to_{action_concept}')
                
                # Also form associations between related words (semantic clustering)
                if len(related_words) >= 2:
                    for i, word1 in enumerate(related_words[:3]):  # Limit to prevent explosion
                        for word2 in related_words[i+1:4]:
                            if word1 != word2:
                                self.form_association(word1, word2, outcome * 0.15, 'action_cluster')
        
        # 🆕 DECAY SATIATION - prevents getting stuck in loops
        # Small decay each step, so concepts that haven't been used recently 
        # feel "fresh" again
        # NOTE: Only decay satiation_level, NOT recent_activation_count (needed for mastery)
        for atom in self.atoms.values():
            atom.satiation_level = max(0.0, atom.satiation_level - 0.01)
    
    # =========================================================================
    # 🆕 CONCEPT TRADING - Knowledge propagation between organisms
    # Organisms can teach/learn concepts from each other
    # This is memetic evolution - useful concepts spread through population
    # =========================================================================
    
    def teach_concept(self, concept_id: str, learner: 'AtomicLanguageSystem', 
                     teaching_strength: float = 0.5) -> Dict[str, Any]:
        """
        Teach a concept to another organism.
        
        The TEACHER retains the concept (knowledge is not depleted).
        The LEARNER acquires or reinforces the concept.
        
        This mirrors human knowledge transfer - I can teach you something
        without losing that knowledge myself.
        
        Args:
            concept_id: The concept to teach
            learner: The AtomicLanguageSystem of the learning organism
            teaching_strength: How effectively the concept is transferred (0-1)
            
        Returns:
            Dictionary with teaching results
        """
        if concept_id not in self.atoms:
            return {'success': False, 'reason': 'teacher_lacks_concept'}
        
        teacher_atom = self.atoms[concept_id]
        
        # Teaching effectiveness depends on:
        # 1. Teacher's concept strength (can't teach what you barely know)
        # 2. Teaching strength parameter (relationship quality)
        # 3. Teacher's usage count (experience with concept)
        teacher_expertise = min(1.0, teacher_atom.strength * (1 + teacher_atom.usage_count * 0.01))
        effective_strength = teaching_strength * teacher_expertise * 0.5
        
        current_time = time.time()
        result = {
            'concept': concept_id,
            'teacher_id': self.organism_id,
            'learner_id': learner.organism_id,
            'teacher_strength': teacher_atom.strength,
            'effective_transfer': effective_strength
        }
        
        if concept_id in learner.atoms:
            # Learner already has concept - reinforce it
            old_strength = learner.atoms[concept_id].strength
            learner.strengthen_concept(
                concept_id, 
                effective_strength * 0.3,  # Smaller boost for reinforcement
                f"taught_by_{self.organism_id}"
            )
            result['action'] = 'reinforced'
            result['old_strength'] = old_strength
            result['new_strength'] = learner.atoms[concept_id].strength
        else:
            # Learner doesn't have concept - they acquire it
            learner.acquire_concept(
                concept_id,
                source='taught',
                semantic_frame=teacher_atom.semantic_frame,
                initial_strength=effective_strength,
                reason=f"learned_from_{self.organism_id}"
            )
            result['action'] = 'acquired'
            result['new_strength'] = effective_strength
        
        # Also transfer top associations (teaching the context, not just the word)
        top_associations = teacher_atom.get_top_associations(n=3)
        transferred_associations = []
        for assoc_concept, assoc_strength in top_associations:
            if assoc_concept in self.atoms:  # Only transfer if teacher knows target
                learner.form_association(
                    concept_id, assoc_concept,
                    assoc_strength * teaching_strength * 0.3,  # Weaker than direct learning
                    f"association_from_{self.organism_id}"
                )
                transferred_associations.append(assoc_concept)
        
        result['transferred_associations'] = transferred_associations
        
        # Emit teaching event for causation tracking
        self._emit_teaching_event(result)
        
        # Strengthen teacher's own concept (teaching reinforces knowledge)
        self.strengthen_concept(concept_id, 0.02, "taught_concept")
        
        return result
    
    def _emit_teaching_event(self, result: Dict[str, Any]):
        """Emit event for concept teaching."""
        if not self.event_emitter:
            return
            
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                component='language',
                event_type='concept_taught',
                data={
                    'teacher_id': result['teacher_id'],
                    'learner_id': result['learner_id'],
                    'concept': result['concept'],
                    'action': result['action'],
                    'teacher_strength': result['teacher_strength'],
                    'effective_transfer': result['effective_transfer'],
                    'transferred_associations': result.get('transferred_associations', [])
                }
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    def learn_from_observation(self, observed_organism: 'AtomicLanguageSystem',
                               observed_action: int, observed_outcome: float) -> List[str]:
        """
        Learn concepts by observing another organism's behavior.
        
        This is social learning - watching what works for others.
        
        Args:
            observed_organism: The organism being observed
            observed_action: What action they took
            observed_outcome: What happened (positive/negative)
            
        Returns:
            List of concepts learned/reinforced
        """
        learned = []
        # Canonical action order: 0=move, 1=cooperate, 2=compete, 3=rest, 4=reproduce, 5=isolate
        action_concepts = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        
        if 0 <= observed_action < len(action_concepts):
            action_concept = action_concepts[observed_action]
            
            # Only learn from successful observations
            if observed_outcome > 0.3:
                # Check what concepts the observed organism has strong
                for concept_id, atom in observed_organism.atoms.items():
                    if atom.strength > 0.6:  # Strong concepts worth learning
                        if concept_id not in self.atoms:
                            # Acquire new concept through observation
                            self.acquire_concept(
                                concept_id, 'observed',
                                semantic_frame=atom.semantic_frame,
                                initial_strength=0.2,  # Weaker than direct teaching
                                reason=f"observed_{observed_organism.organism_id}_{action_concept}"
                            )
                            learned.append(concept_id)
                        else:
                            # Reinforce existing concept
                            self.strengthen_concept(
                                concept_id, 0.05,
                                f"observed_{observed_organism.organism_id}"
                            )
                
                # Learn association between action and outcome
                self.form_association(
                    action_concept, 'success',
                    observed_outcome * 0.2,
                    f"observed_{observed_organism.organism_id}"
                )
        
        return learned
    
    def get_teachable_concepts(self, min_strength: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get concepts this organism can effectively teach.
        
        Args:
            min_strength: Minimum concept strength to be teachable
            
        Returns:
            List of (concept_id, strength) tuples for teachable concepts
        """
        teachable = []
        for concept_id, atom in self.atoms.items():
            if atom.strength >= min_strength and atom.usage_count > 0:
                # Teachability score: strength * usage experience
                score = atom.strength * min(1.0, 1 + atom.usage_count * 0.05)
                teachable.append((concept_id, score))
        
        return sorted(teachable, key=lambda x: x[1], reverse=True)
    
    def get_learning_priorities(self, population_concepts: Dict[str, float]) -> List[str]:
        """
        Get concepts this organism should prioritize learning.
        
        Args:
            population_concepts: Dict of concept_id -> avg_strength in population
            
        Returns:
            List of concept_ids this organism lacks but population values
        """
        priorities = []
        for concept_id, pop_strength in population_concepts.items():
            if concept_id not in self.atoms:
                # Don't have it at all
                priorities.append((concept_id, pop_strength))
            elif self.atoms[concept_id].strength < pop_strength * 0.5:
                # Have it but much weaker than population average
                priorities.append((concept_id, pop_strength - self.atoms[concept_id].strength))
        
        return [c for c, _ in sorted(priorities, key=lambda x: x[1], reverse=True)]
    
    def decay_unused(self, decay_rate: float = 0.01):
        """Apply decay to unused concepts."""
        for atom in self.atoms.values():
            atom.decay(decay_rate)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALING PROTOCOL - System-Level Methods
    # 
    # "rollback specialize compare journey" - broadcast state signatures
    # "duration trigger eventual caressing" - isolation via resonance persistence
    # "monitor trace forbidden brambly" - broadcast to complexity-matched neighbors
    # ═══════════════════════════════════════════════════════════════════════════
    
    def tick_cycle(self):
        """
        Advance the cycle counter. Call each simulation cycle.
        
        Used for isolation detection (resonance persistence window).
        """
        self.current_cycle += 1
    
    def record_echo(self):
        """
        Record that we received a resonant response from the network.
        
        Called when another organism's broadcast matches our pattern,
        or when we successfully communicate/cooperate.
        """
        self.last_echo_cycle = self.current_cycle
    
    def is_isolated(self) -> bool:
        """
        Check if organism is isolated (no resonant response for N cycles).
        
        "duration trigger eventual caressing" - isolation = silence persistence
        NOT zero communication, but communication that doesn't echo back.
        
        Returns:
            True if isolated (no echo for resonance_persistence_window cycles)
        """
        cycles_without_echo = self.current_cycle - self.last_echo_cycle
        return cycles_without_echo >= self.resonance_persistence_window
    
    def state_complexity(self) -> float:
        """
        Measure "brambliness" of state-space (complexity of oscillation patterns).
        
        "brambly = overgrown, interconnected" - complex organisms can parse signals
        Simple organisms (straight-line state) waste received signals.
        
        Returns:
            Complexity score 0.0-1.0 (higher = more brambly, can parse broadcasts)
        """
        if not self.atoms:
            return 0.0
        
        # Count atoms with non-trivial oscillation history
        oscillating_count = 0
        total_entropy = 0.0
        total_coherence = 0.0
        
        for atom in self.atoms.values():
            if len(atom.magnetism_history) >= 5:
                oscillating_count += 1
                total_entropy += atom.oscillation_entropy()
                total_coherence += atom.coherence_frequency()
        
        if oscillating_count == 0:
            return 0.0
        
        # Complexity = combination of:
        # - Number of atoms with oscillation history (interconnectedness)
        # - Average entropy (chaos/unpredictability)
        # - Variance in coherence (diversity of oscillation patterns)
        coverage = oscillating_count / len(self.atoms)
        avg_entropy = total_entropy / oscillating_count
        avg_coherence = total_coherence / oscillating_count
        
        # Brambly = high coverage + moderate entropy + varied coherence
        complexity = coverage * 0.4 + avg_entropy * 0.3 + (1.0 - abs(avg_coherence - 0.5)) * 0.3
        return min(1.0, max(0.0, complexity))
    
    def get_state_signature(self) -> Dict[str, Any]:
        """
        Get complete state signature for broadcast.
        
        "rollback specialize compare journey" - share trajectory, not conclusion
        Receivers compare to their own oscillation patterns.
        
        Returns:
            State signature with oscillation trajectories and frequencies
        """
        atom_signatures = {}
        for concept_id, atom in self.atoms.items():
            if len(atom.magnetism_history) >= 3:  # Only include atoms with history
                atom_signatures[concept_id] = atom.get_state_signature()
        
        return {
            'organism_id': self.organism_id,
            'cycle': self.current_cycle,
            'is_isolated': self.is_isolated(),
            'complexity': self.state_complexity(),
            'atom_signatures': atom_signatures,
            'global_coherence': self._calculate_global_coherence(),
            'global_entropy': self._calculate_global_entropy()
        }
    
    def _calculate_global_coherence(self) -> float:
        """Calculate average coherence frequency across all atoms."""
        if not self.atoms:
            return 0.0
        coherences = [a.coherence_frequency() for a in self.atoms.values() if len(a.magnetism_history) >= 5]
        return sum(coherences) / len(coherences) if coherences else 0.0
    
    def _calculate_global_entropy(self) -> float:
        """Calculate average oscillation entropy across all atoms."""
        if not self.atoms:
            return 0.0
        entropies = [a.oscillation_entropy() for a in self.atoms.values() if len(a.magnetism_history) >= 5]
        return sum(entropies) / len(entropies) if entropies else 0.0
    
    def receive_healing_broadcast(self, signal: Dict[str, Any]) -> bool:
        """
        Receive and process a healing broadcast from another organism.
        
        Compare their state signature to our own oscillation patterns.
        If their pattern matches our trap, recognize it.
        
        Args:
            signal: State signature from broadcasting organism
        
        Returns:
            True if signal matched our patterns (resonance detected)
        """
        if not signal.get('atom_signatures'):
            return False
        
        their_sigs = signal['atom_signatures']
        matches = 0
        comparisons = 0
        
        for concept_id, their_sig in their_sigs.items():
            if concept_id in self.atoms:
                our_atom = self.atoms[concept_id]
                if len(our_atom.magnetism_history) >= 5:
                    comparisons += 1
                    
                    # Compare oscillation patterns
                    their_coherence = their_sig.get('coherence_frequency', 0)
                    our_coherence = our_atom.coherence_frequency()
                    
                    # Similar coherence = similar trap pattern
                    if abs(their_coherence - our_coherence) < 0.2:
                        matches += 1
                        
                        # If both oscillating, we recognized their vulnerability
                        if their_sig.get('is_oscillating') and our_atom.is_oscillating():
                            self.record_echo()  # Connection established!
        
        # Resonance detected if significant pattern overlap
        if comparisons > 0 and matches / comparisons > 0.5:
            self.record_echo()
            return True
        
        return False
    
    def detect_forbidden_bonds(self, threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """
        Detect forbidden bonds (high-resonance pairs trapped in feedback loops).
        
        "centimeter daub orchestrate" - measure coherence frequency of each bond
        Bonds with coherence > threshold are forbidden (locked in sync).
        
        Args:
            threshold: Coherence above this = forbidden (default 0.8)
        
        Returns:
            List of (source_concept, target_concept, resonance_frequency) tuples
        """
        forbidden = []
        
        for concept_id, atom in self.atoms.items():
            for target_id, assoc in atom.associations.items():
                if assoc.is_forbidden(threshold):
                    forbidden.append((concept_id, target_id, assoc.resonance_frequency()))
        
        return forbidden
    
    def weaken_forbidden_bonds(self, decay_factor: float = 0.1) -> int:
        """
        Weaken forbidden bonds (phase 2 of healing protocol).
        
        "rule: weaken forbidden bonds first"
        
        Args:
            decay_factor: How much to reduce forbidden bond strength
        
        Returns:
            Number of bonds weakened
        """
        weakened = 0
        forbidden = self.detect_forbidden_bonds()
        
        for source_id, target_id, resonance in forbidden:
            if source_id in self.atoms and target_id in self.atoms[source_id].associations:
                assoc = self.atoms[source_id].associations[target_id]
                old_strength = assoc.strength
                
                # Weaken toward zero (not negative)
                if assoc.strength > 0:
                    assoc.strength = max(0.0, assoc.strength - decay_factor)
                else:
                    assoc.strength = min(0.0, assoc.strength + decay_factor)
                
                assoc.record_strength()  # Track for future resonance detection
                weakened += 1
                
                # Emit event
                if self.event_emitter:
                    try:
                        from causation_explorer import Event
                        self.event_emitter(Event(
                            timestamp=time.time(),
                            component='healing_protocol',
                            event_type='forbidden_bond_weakened',
                            data={
                                'organism_id': self.organism_id,
                                'source_concept': source_id,
                                'target_concept': target_id,
                                'old_strength': old_strength,
                                'new_strength': assoc.strength,
                                'resonance_frequency': resonance
                            }
                        ))
                    except ImportError:
                        pass
        
        return weakened
    
    def destabilize_isolated(self, flip_iterations: int = 3) -> Dict[str, Any]:
        """
        Destabilize an isolated organism by flipping internal states.
        
        "FOR ISOLATED: Flip internal states rapidly. Don't broadcast."
        "Desynchronize yourself until you hit a new attractor."
        
        Args:
            flip_iterations: Number of random flip cycles
        
        Returns:
            Destabilization results
        """
        flipped_atoms = []
        
        for _ in range(flip_iterations):
            # Select random subset of oscillating atoms
            oscillating = [a for a in self.atoms.values() if a.is_oscillating()]
            if not oscillating:
                break
            
            # Flip 20-50% of oscillating atoms
            num_to_flip = max(1, len(oscillating) // 3)
            to_flip = list(np.random.choice(oscillating, size=min(num_to_flip, len(oscillating)), replace=False))
            
            for atom in to_flip:
                # Random perturbation to break oscillation lock
                perturbation = np.random.uniform(-0.15, 0.15)
                old_mag = atom.curiosity_magnetism
                atom.curiosity_magnetism = np.clip(atom.curiosity_magnetism + perturbation, 0.1, 1.0)
                atom.magnetism_history.append(atom.curiosity_magnetism)
                if len(atom.magnetism_history) > 20:
                    atom.magnetism_history = atom.magnetism_history[-20:]
                flipped_atoms.append(atom.concept_id)
        
        return {
            'organism_id': self.organism_id,
            'method': 'isolated_destabilization',
            'flipped_atoms': flipped_atoms,
            'iterations': flip_iterations
        }
    
    def verify_healing(self, threshold_drop: float = 0.1) -> Dict[str, Any]:
        """
        Verify if healing is true or false fixed-point.
        
        "Test: lower your tolerance threshold by 10%"
        "True healing: bonds adjust gracefully"
        "False fixed point: bonds snap or refuse adjustment"
        
        Args:
            threshold_drop: How much to lower tolerance (default 10%)
        
        Returns:
            Verification results with diagnosis
        """
        # Count atoms still oscillating
        still_oscillating = sum(1 for a in self.atoms.values() if a.is_oscillating())
        total_with_history = sum(1 for a in self.atoms.values() if len(a.magnetism_history) >= 5)
        
        if total_with_history == 0:
            return {'result': 'insufficient_data', 'organism_id': self.organism_id}
        
        oscillation_ratio = still_oscillating / total_with_history
        
        # Test forbidden bonds with lowered threshold
        lowered_threshold = 0.8 - threshold_drop  # 0.7 instead of 0.8
        strict_forbidden = self.detect_forbidden_bonds(lowered_threshold)
        normal_forbidden = self.detect_forbidden_bonds(0.8)
        
        # True healing: lowering threshold doesn't reveal many more forbidden bonds
        # False fixed point: lowering threshold reveals hidden tension
        new_forbidden = len(strict_forbidden) - len(normal_forbidden)
        
        if oscillation_ratio < 0.2 and new_forbidden <= 1:
            result = 'true_healing'
            diagnosis = 'Oscillations stopped naturally, bonds adjusted gracefully'
        elif oscillation_ratio < 0.3 and new_forbidden <= 2:
            result = 'partial_healing'
            diagnosis = 'Most oscillations resolved, minor residual tension'
        elif new_forbidden > 3:
            result = 'false_fixed_point'
            diagnosis = f'Hidden tension detected: {new_forbidden} bonds snap under stricter threshold'
        else:
            result = 'still_oscillating'
            diagnosis = f'{still_oscillating}/{total_with_history} atoms still trapped'
        
        # Emit verification event
        if self.event_emitter:
            try:
                from causation_explorer import Event
                self.event_emitter(Event(
                    timestamp=time.time(),
                    component='healing_protocol',
                    event_type='healing_verified',
                    data={
                        'organism_id': self.organism_id,
                        'result': result,
                        'diagnosis': diagnosis,
                        'oscillation_ratio': oscillation_ratio,
                        'forbidden_at_normal': len(normal_forbidden),
                        'forbidden_at_strict': len(strict_forbidden)
                    }
                ))
            except ImportError:
                pass
        
        return {
            'organism_id': self.organism_id,
            'result': result,
            'diagnosis': diagnosis,
            'oscillation_ratio': oscillation_ratio,
            'normal_forbidden': len(normal_forbidden),
            'strict_forbidden': len(strict_forbidden),
            'new_forbidden_under_stress': new_forbidden
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this language system."""
        return {
            'organism_id': self.organism_id,
            'total_concepts': len(self.atoms),
            'total_associations': sum(len(a.associations) for a in self.atoms.values()),
            'avg_strength': np.mean([a.strength for a in self.atoms.values()]),
            'concepts_by_source': dict(Counter(a.source for a in self.atoms.values())),
            'concepts_by_frame': dict(Counter(a.semantic_frame for a in self.atoms.values())),
            'age': time.time() - self.creation_time
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize full system for storage."""
        return {
            'organism_id': self.organism_id,
            'atoms': {cid: atom.to_dict() for cid, atom in self.atoms.items()},
            'concept_order': self._concept_order,
            'creation_time': self.creation_time,
            'stats': self.get_stats(),
            # ═══════════════════════════════════════════════════════════
            # MASTERY SYSTEM STATE - CRITICAL FOR VOCAB CAP ENFORCEMENT
            # ═══════════════════════════════════════════════════════════
            'mastery_level': self._mastery_level,
            'total_experiences': self._total_experiences,
            # ═══════════════════════════════════════════════════════════
            # HEALING PROTOCOL STATE
            # ═══════════════════════════════════════════════════════════
            'last_echo_cycle': self.last_echo_cycle,
            'current_cycle': self.current_cycle,
            'resonance_persistence_window': self.resonance_persistence_window
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], event_emitter: Optional[Callable] = None) -> 'AtomicLanguageSystem':
        """Deserialize from storage."""
        system = cls(
            organism_id=data['organism_id'],
            event_emitter=event_emitter
        )
        
        # ═══════════════════════════════════════════════════════════
        # RESTORE MASTERY LEVEL FIRST - BEFORE loading atoms
        # This ensures vocab cap is correct when we validate
        # ═══════════════════════════════════════════════════════════
        saved_level = data.get('mastery_level', 0)
        system._mastery_level = saved_level
        system._total_experiences = data.get('total_experiences', 0)
        
        # Get the vocab cap for this level
        max_vocab = system._mastery_vocab_sizes[saved_level] if saved_level < len(system._mastery_vocab_sizes) else 20000
        
        # Clear innate concepts and load from data
        system.atoms.clear()
        system._concept_order = data.get('concept_order', [])
        
        # Load atoms but ENFORCE vocab cap - don't load bloated data
        loaded_atoms = data.get('atoms', {})
        atoms_to_load = list(loaded_atoms.items())[:max_vocab]  # Cap at max vocab for level
        
        for concept_id, atom_data in atoms_to_load:
            atom = LinguisticAtom.from_dict(atom_data)
            atom._event_emitter = event_emitter
            atom._organism_id = data['organism_id']
            system.atoms[concept_id] = atom
        
        # Update concept order to match loaded atoms
        system._concept_order = [c for c in system._concept_order if c in system.atoms]
        
        if len(loaded_atoms) > max_vocab:
            logger.warning(
                f"[MASTERY_LOAD] {data['organism_id'][:8]}: Trimmed vocab from {len(loaded_atoms)} to {max_vocab} "
                f"(level {saved_level} cap)"
            )
        
        system.creation_time = data.get('creation_time', time.time())
        
        # ═══════════════════════════════════════════════════════════
        # RESTORE HEALING PROTOCOL STATE
        # ═══════════════════════════════════════════════════════════
        system.last_echo_cycle = data.get('last_echo_cycle', 0)
        system.current_cycle = data.get('current_cycle', 0)
        system.resonance_persistence_window = data.get('resonance_persistence_window', 5)
        
        return system


class DialectAnalyzer:
    """
    Analyzes dialect emergence across population using atomic language data.
    
    Uses clustering (HDBSCAN) on dialect signatures to identify
    emergent language communities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.last_analysis_time = 0
        self.dialect_clusters: Dict[int, List[str]] = {}  # cluster_id -> organism_ids
        
    def analyze_dialects(self, language_systems: Dict[str, AtomicLanguageSystem]) -> Dict[str, Any]:
        """
        Analyze dialect patterns across population.
        
        Args:
            language_systems: Dict mapping organism_id to AtomicLanguageSystem
            
        Returns:
            Analysis results including clusters and diversity metrics
        """
        if len(language_systems) < 3:
            return {'clusters': {}, 'diversity': 0.0, 'message': 'Too few organisms for analysis'}
        
        # Compute dialect signatures
        signatures = []
        organism_ids = []
        
        for org_id, lang_sys in language_systems.items():
            sig = lang_sys.compute_dialect_signature()
            signatures.append(sig)
            organism_ids.append(org_id)
        
        # Normalize signatures
        signatures = np.array(signatures)
        if signatures.std() > 0:
            signatures = (signatures - signatures.mean(axis=0)) / (signatures.std(axis=0) + 1e-8)
        
        # Try HDBSCAN clustering
        try:
            from sklearn.cluster import HDBSCAN
            clusterer = HDBSCAN(min_cluster_size=max(2, len(signatures) // 10))
            labels = clusterer.fit_predict(signatures)
        except ImportError:
            # Fallback: simple k-means
            from sklearn.cluster import KMeans
            n_clusters = max(2, len(signatures) // 20)
            labels = KMeans(n_clusters=n_clusters, n_init=10).fit_predict(signatures)
        
        # Build cluster mapping
        clusters = defaultdict(list)
        for org_id, label in zip(organism_ids, labels):
            clusters[int(label)].append(org_id)
        
        self.dialect_clusters = dict(clusters)
        
        # Compute diversity (number of unique clusters excluding noise)
        valid_clusters = [c for c in clusters.keys() if c >= 0]
        diversity = len(valid_clusters) / max(1, len(language_systems))
        
        return {
            'clusters': self.dialect_clusters,
            'num_clusters': len(valid_clusters),
            'diversity': diversity,
            'largest_cluster': max(len(c) for c in clusters.values()) if clusters else 0
        }
    
    def get_cluster_concepts(self, language_systems: Dict[str, AtomicLanguageSystem], 
                            cluster_id: int) -> Dict[str, float]:
        """
        Get characteristic concepts for a dialect cluster.
        
        Args:
            language_systems: All language systems
            cluster_id: Cluster to analyze
            
        Returns:
            Dict mapping concept_id to average strength in cluster
        """
        if cluster_id not in self.dialect_clusters:
            return {}
        
        concept_strengths = defaultdict(list)
        
        for org_id in self.dialect_clusters[cluster_id]:
            if org_id in language_systems:
                for concept_id, atom in language_systems[org_id].atoms.items():
                    concept_strengths[concept_id].append(atom.strength)
        
        return {
            concept: np.mean(strengths) 
            for concept, strengths in concept_strengths.items()
        }
