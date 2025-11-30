"""
Tests for Language Teacher (Phase 1: Behavior-based mapping)
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reality_simulator.language.language_teacher import LanguageTeacher
from reality_simulator.memory.context_memory import ContextMemory
from reality_simulator.evolution_engine import Organism, Genotype, Phenotype


class MockOrganism:
    """Mock organism for testing"""
    def __init__(self, species_id, fitness=0.5, connections=None, prev_action=None):
        self.species_id = species_id
        self.fitness = fitness
        self.connections = connections or []
        self.prev_action = prev_action
    
    def get_action_sequence(self, length=None):
        """Mock action sequence"""
        if self.prev_action is not None:
            return [self.prev_action] * (length or 3)
        return []


class TestLanguageTeacher(unittest.TestCase):
    """Test Language Teacher functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'neural': {
                'language_model': {
                    'enabled': True,
                    'teaching_frequency': 1,
                    'min_action_history': 3
                }
            }
        }
        self.teacher = LanguageTeacher(self.config)
        self.context_memory = ContextMemory()
    
    def test_initialization(self):
        """Test teacher initialization"""
        self.assertTrue(self.teacher.enabled)
        self.assertEqual(self.teacher.teaching_frequency, 1)
        self.assertEqual(self.teacher.min_action_history, 3)
    
    def test_teach_organism_with_actions(self):
        """Test teaching organism based on actions"""
        organism = MockOrganism('org_1', fitness=0.8, prev_action=0)  # move action
        
        words_assigned = self.teacher.teach_organism(
            organism, self.context_memory, generation=1
        )
        
        # Should assign words for action (move) and state (high fitness)
        self.assertGreater(words_assigned, 0)
        
        # Check that words were linked
        self.assertGreater(len(self.context_memory.language_anchors), 0)
        
        # Check specific words were assigned (language_anchors is defaultdict, check if sets are non-empty)
        self.assertGreater(len(self.context_memory.language_anchors.get('explore', set())), 0)
        self.assertGreater(len(self.context_memory.language_anchors.get('thrive', set())), 0)
    
    def test_teach_organism_with_fitness(self):
        """Test teaching organism based on fitness"""
        # High fitness organism
        organism = MockOrganism('org_2', fitness=0.9)
        words_assigned = self.teacher.teach_organism(
            organism, self.context_memory, generation=1
        )
        
        self.assertGreater(words_assigned, 0)
        self.assertGreater(len(self.context_memory.language_anchors.get('thrive', set())), 0)
        
        # Low fitness organism
        organism_low = MockOrganism('org_3', fitness=0.2)
        self.teacher.teach_organism(organism_low, self.context_memory, generation=1)
        self.assertGreater(len(self.context_memory.language_anchors.get('struggle', set())), 0)
    
    def test_teach_organism_with_connections(self):
        """Test teaching organism based on connections"""
        # Many connections
        organism = MockOrganism('org_4', fitness=0.5, connections=[1, 2, 3, 4, 5, 6])
        words_assigned = self.teacher.teach_organism(
            organism, self.context_memory, generation=1
        )
        
        self.assertGreater(words_assigned, 0)
        self.assertGreater(len(self.context_memory.language_anchors.get('social', set())), 0)
        
        # No connections
        organism_isolated = MockOrganism('org_5', fitness=0.5, connections=[])
        self.teacher.teach_organism(organism_isolated, self.context_memory, generation=1)
        self.assertGreater(len(self.context_memory.language_anchors.get('solitary', set())), 0)
    
    def test_teach_network(self):
        """Test teaching entire network"""
        organisms = {
            'org_1': MockOrganism('org_1', fitness=0.8, prev_action=0),
            'org_2': MockOrganism('org_2', fitness=0.3, prev_action=1),
            'org_3': MockOrganism('org_3', fitness=0.5, connections=[1, 2, 3])
        }
        
        result = self.teacher.teach_network(organisms, self.context_memory, generation=1)
        
        self.assertTrue(result['enabled'])
        self.assertGreater(result['organisms_taught'], 0)
        self.assertGreater(result['words_assigned'], 0)
        self.assertEqual(result['total_organisms'], 3)
    
    def test_teaching_frequency(self):
        """Test teaching frequency filtering"""
        teacher = LanguageTeacher({
            'neural': {
                'language_model': {
                    'enabled': True,
                    'teaching_frequency': 5  # Teach every 5 generations
                }
            }
        })
        
        organisms = {'org_1': MockOrganism('org_1')}
        
        # Generation 1 - should skip
        result = teacher.teach_network(organisms, self.context_memory, generation=1)
        self.assertTrue(result.get('skipped'))
        
        # Generation 5 - should teach
        result = teacher.teach_network(organisms, self.context_memory, generation=5)
        self.assertFalse(result.get('skipped'))
        self.assertTrue(result['enabled'])
    
    def test_disabled_teacher(self):
        """Test disabled teacher"""
        teacher = LanguageTeacher({
            'neural': {
                'language_model': {
                    'enabled': False
                }
            }
        })
        
        self.assertFalse(teacher.enabled)
        
        organism = MockOrganism('org_1')
        words_assigned = teacher.teach_organism(organism, self.context_memory, generation=1)
        self.assertEqual(words_assigned, 0)
        
        result = teacher.teach_network({'org_1': organism}, self.context_memory, generation=1)
        self.assertFalse(result['enabled'])
    
    def test_action_word_mapping(self):
        """Test all action mappings"""
        action_map = {
            0: 'explore',  # move
            1: 'connect',  # cooperate
            2: 'fight',    # compete
            3: 'rest',     # rest
            4: 'grow',     # reproduce
            5: 'withdraw'  # isolate
        }
        
        for action, expected_word in action_map.items():
            organism = MockOrganism(f'org_{action}', prev_action=action)
            self.teacher.teach_organism(organism, self.context_memory, generation=1)
            self.assertGreater(len(self.context_memory.language_anchors.get(expected_word, set())), 0)
    
    def test_stats_tracking(self):
        """Test statistics tracking"""
        organisms = {
            'org_1': MockOrganism('org_1', fitness=0.8),
            'org_2': MockOrganism('org_2', fitness=0.3)
        }
        
        self.teacher.teach_network(organisms, self.context_memory, generation=1)
        
        stats = self.teacher.get_stats()
        self.assertGreater(stats['organisms_taught'], 0)
        self.assertGreater(stats['words_assigned'], 0)
        self.assertGreater(stats['total_teachings'], 0)
        self.assertIn('words_by_type', stats)


if __name__ == '__main__':
    unittest.main()

