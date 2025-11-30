"""
Language Teacher - Phase 1: Behavior-Based Word Mapping

Automated system that observes organism behavior and state, then associates
words with organisms through ContextMemory. This enables vocabulary growth
and language learning.

Based on semantic grounding research and emergent language patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class LanguageTeacher:
    """
    Phase 1: Simple behavior-based language teacher.
    
    Observes organisms and automatically associates words with them based on:
    - Actions they take (move, cooperate, compete, rest, reproduce, isolate)
    - States they're in (fitness, connections, resources)
    
    This creates the initial vocabulary that organisms can then use for communication.
    """
    
    # Action mapping: action index -> list of associated words
    ACTION_WORD_MAP = {
        0: ['explore', 'travel', 'wander', 'move', 'journey'],  # move
        1: ['connect', 'share', 'help', 'cooperate', 'collaborate'],  # cooperate
        2: ['fight', 'compete', 'challenge', 'compete', 'rival'],  # compete
        3: ['rest', 'pause', 'recover', 'sleep', 'wait'],  # rest
        4: ['grow', 'multiply', 'spread', 'reproduce', 'expand'],  # reproduce
        5: ['withdraw', 'separate', 'isolate', 'retreat', 'alone']  # isolate
    }
    
    # State-based word mappings
    STATE_WORD_MAP = {
        'high_fitness': ['thrive', 'success', 'strong', 'flourish', 'prosper'],
        'low_fitness': ['struggle', 'weak', 'failing', 'decline', 'suffer'],
        'medium_fitness': ['stable', 'survive', 'endure', 'persist'],
        'many_connections': ['social', 'connected', 'networked', 'linked', 'integrated'],
        'few_connections': ['isolated', 'alone', 'separate', 'disconnected', 'lonely'],
        'no_connections': ['solitary', 'independent', 'autonomous'],
        'high_resources': ['rich', 'abundant', 'plentiful', 'wealthy', 'sustained'],
        'low_resources': ['poor', 'scarce', 'depleted', 'starving', 'needy'],
        'medium_resources': ['moderate', 'adequate', 'sufficient']
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize language teacher.
        
        Args:
            config: Configuration dictionary with language_model settings
        """
        self.config = config or {}
        language_config = self.config.get('neural', {}).get('language_model', {})
        
        # Enable/disable flag
        self.enabled = language_config.get('enabled', False)
        
        # Teaching frequency (teach every N generations)
        self.teaching_frequency = language_config.get('teaching_frequency', 1)  # Every generation by default
        
        # Minimum action history length before teaching
        self.min_action_history = language_config.get('min_action_history', 3)
        
        # Track teaching statistics
        self.stats = {
            'organisms_taught': 0,
            'words_assigned': 0,
            'total_teachings': 0,
            'words_by_type': defaultdict(int)
        }
        
        logger.info(f"[LANGUAGE_TEACHER] Initialized (enabled={self.enabled}, frequency={self.teaching_frequency})")
    
    def teach_organism(self, organism, context_memory, generation: int) -> int:
        """
        Teach words to an organism based on its behavior and state.
        
        Args:
            organism: Organism instance (can be Organism or NeuralOrganism)
            context_memory: ContextMemory instance for storing associations
            generation: Current generation number
            
        Returns:
            Number of words assigned to this organism
        """
        if not self.enabled:
            return 0
        
        words_assigned = 0
        
        # Get organism ID (convert to int if needed for compatibility)
        species_id = organism.species_id if hasattr(organism, 'species_id') else str(id(organism))
        # Convert string ID to int (hash-based) for compatibility with link_word_to_node
        organism_id = hash(species_id) if isinstance(species_id, str) else species_id
        
        # Phase 1: Action-based words
        if hasattr(organism, 'get_action_sequence'):
            # Neural organism with action history
            recent_actions = organism.get_action_sequence(length=10)  # Last 10 actions
            if len(recent_actions) >= self.min_action_history:
                for action in recent_actions:
                    if action in self.ACTION_WORD_MAP:
                        words = self.ACTION_WORD_MAP[action]
                        for word in words:
                            try:
                                context_memory.link_word_to_node(word, organism_id, generation)
                                words_assigned += 1
                                self.stats['words_by_type']['action'] += 1
                            except Exception as e:
                                logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        elif hasattr(organism, 'prev_action'):
            # Organism with single previous action
            action = organism.prev_action
            if action is not None and action in self.ACTION_WORD_MAP:
                words = self.ACTION_WORD_MAP[action]
                for word in words[:2]:  # Limit to 2 words for single action
                    try:
                        context_memory.link_word_to_node(word, organism_id, generation)
                        words_assigned += 1
                        self.stats['words_by_type']['action'] += 1
                    except Exception as e:
                        logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        
        # Phase 1: State-based words
        # Fitness-based words
        if hasattr(organism, 'fitness'):
            fitness = organism.fitness
            if fitness > 0.7:
                words = self.STATE_WORD_MAP['high_fitness']
            elif fitness < 0.3:
                words = self.STATE_WORD_MAP['low_fitness']
            else:
                words = self.STATE_WORD_MAP['medium_fitness']
            
            # Assign top 2-3 words based on fitness
            for word in words[:3]:
                try:
                    context_memory.link_word_to_node(word, organism_id, generation)
                    words_assigned += 1
                    self.stats['words_by_type']['fitness'] += 1
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        
        # Connection-based words
        if hasattr(organism, 'connections'):
            num_connections = len(organism.connections) if hasattr(organism.connections, '__len__') else 0
            if num_connections > 5:
                words = self.STATE_WORD_MAP['many_connections']
            elif num_connections == 0:
                words = self.STATE_WORD_MAP['no_connections']
            else:
                words = self.STATE_WORD_MAP['few_connections']
            
            # Assign top 2 words
            for word in words[:2]:
                try:
                    context_memory.link_word_to_node(word, organism_id, generation)
                    words_assigned += 1
                    self.stats['words_by_type']['connections'] += 1
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        elif hasattr(organism, 'get_connections'):
            # Alternative connection access
            try:
                connections = organism.get_connections()
                num_connections = len(connections) if connections else 0
                if num_connections > 5:
                    words = self.STATE_WORD_MAP['many_connections']
                elif num_connections == 0:
                    words = self.STATE_WORD_MAP['no_connections']
                else:
                    words = self.STATE_WORD_MAP['few_connections']
                
                for word in words[:2]:
                    context_memory.link_word_to_node(word, organism_id, generation)
                    words_assigned += 1
                    self.stats['words_by_type']['connections'] += 1
            except Exception:
                pass  # Skip if connections not available
        
        # Resource-based words (if available)
        if hasattr(organism, 'resources'):
            resources = organism.resources
            if resources > 0.7:
                words = self.STATE_WORD_MAP['high_resources']
            elif resources < 0.3:
                words = self.STATE_WORD_MAP['low_resources']
            else:
                words = self.STATE_WORD_MAP['medium_resources']
            
            for word in words[:2]:
                try:
                    context_memory.link_word_to_node(word, organism_id, generation)
                    words_assigned += 1
                    self.stats['words_by_type']['resources'] += 1
                except Exception as e:
                    logger.warning(f"[LANGUAGE_TEACHER] Failed to link word '{word}': {e}")
        
        # Update statistics
        if words_assigned > 0:
            self.stats['organisms_taught'] += 1
            self.stats['words_assigned'] += words_assigned
        
        return words_assigned
    
    def teach_network(self, organisms: Dict[str, Any], context_memory, generation: int) -> Dict[str, Any]:
        """
        Teach all organisms in the network.
        
        Args:
            organisms: Dictionary of organism_id -> organism
            context_memory: ContextMemory instance
            generation: Current generation number
            
        Returns:
            Dictionary with teaching statistics
        """
        if not self.enabled:
            return {'enabled': False, 'organisms_taught': 0, 'words_assigned': 0}
        
        # Check teaching frequency
        if generation % self.teaching_frequency != 0:
            return {'skipped': True, 'reason': 'teaching_frequency'}
        
        self.stats['total_teachings'] += 1
        organisms_taught = 0
        total_words = 0
        
        for organism_id, organism in organisms.items():
            words_assigned = self.teach_organism(organism, context_memory, generation)
            if words_assigned > 0:
                organisms_taught += 1
                total_words += words_assigned
        
        result = {
            'enabled': True,
            'generation': generation,
            'organisms_taught': organisms_taught,
            'total_organisms': len(organisms),
            'words_assigned': total_words,
            'stats': dict(self.stats)
        }
        
        # Log periodically
        if generation % 10 == 0:
            logger.info(
                f"[LANGUAGE_TEACHER] Gen {generation}: Taught {organisms_taught}/{len(organisms)} organisms, "
                f"{total_words} words assigned"
            )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get teaching statistics."""
        return dict(self.stats)
    
    def reset_stats(self):
        """Reset teaching statistics."""
        self.stats = {
            'organisms_taught': 0,
            'words_assigned': 0,
            'total_teachings': 0,
            'words_by_type': defaultdict(int)
        }


# Convenience function for easy import
def create_language_teacher(config: Optional[Dict[str, Any]] = None) -> Optional[LanguageTeacher]:
    """
    Create a LanguageTeacher instance if language model is enabled.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        LanguageTeacher instance or None if disabled
    """
    if config is None:
        return None
    
    language_config = config.get('neural', {}).get('language_model', {})
    if language_config.get('enabled', False):
        return LanguageTeacher(config)
    return None

