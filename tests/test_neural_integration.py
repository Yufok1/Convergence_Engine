"""
Test suite for Neural System Integration

Tests neural organism creation, training, and breath synchronization.
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add paths for imports
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))
sys.path.insert(0, str(parent_path / 'reality_simulator'))
sys.path.insert(0, str(parent_path / 'reality_simulator' / 'neural'))

try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


class TestNeuralIntegration(unittest.TestCase):
    """Test neural system integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_neural_enabled = {
            'neural': {
                'enabled': True,
                'device': 'cpu',
                'brain': {
                    'input_dim': 12,
                    'hidden_dim': 64,
                    'output_dim': 6,
                    'activation': 'relu',
                    'dropout': 0.1
                },
                'training': {
                    'enabled': True,
                    'batch_size': 32,
                    'memory_size': 1000,
                    'learning_rate': 0.001,
                    'gamma': 0.99,
                    'epsilon_start': 1.0,
                    'epsilon_end': 0.01,
                    'epsilon_decay': 0.995,
                    'update_frequency': 1
                },
                'rewards': {
                    'fitness_improvement': 1.0,
                    'survival': 0.1,
                    'connection_success': 0.5,
                    'connection_failure': -0.2,
                    'resource_gain': 0.3,
                    'resource_loss': -0.1
                },
                'inheritance': {
                    'enabled': True,
                    'mutation_rate': 0.1,
                    'crossover_rate': 0.5
                }
            }
        }
        
        self.config_neural_disabled = {
            'neural': {
                'enabled': False
            }
        }
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_neural_organism_spawn(self):
        """Test that factory creates correct organism type based on config"""
        from reality_simulator.evolution_engine import EvolutionEngine, Genotype
        
        # Test with neural enabled
        evolution_neural = EvolutionEngine(
            population_size=10,
            genotype_length=32,
            config=self.config_neural_enabled
        )
        
        # Check that organisms are NeuralOrganisms
        from reality_simulator.neural.neural_organism import NeuralOrganism
        self.assertTrue(len(evolution_neural.population) > 0)
        self.assertIsInstance(evolution_neural.population[0], NeuralOrganism)
        self.assertIsNotNone(evolution_neural.population[0].brain)
        
        # Test with neural disabled
        evolution_standard = EvolutionEngine(
            population_size=10,
            genotype_length=32,
            config=self.config_neural_disabled
        )
        
        # Check that organisms are standard Organisms
        from reality_simulator.evolution_engine import Organism
        self.assertTrue(len(evolution_standard.population) > 0)
        self.assertIsInstance(evolution_standard.population[0], Organism)
        self.assertFalse(hasattr(evolution_standard.population[0], 'brain'))
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_brain_forward(self):
        """Test that brain forward pass works correctly"""
        from reality_simulator.neural.brain import OrganismBrain
        
        brain = OrganismBrain(
            input_dim=12,
            hidden_dim=64,
            output_dim=6
        )
        
        # Test forward pass
        state = np.random.rand(12).astype(np.float32)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        brain.eval()
        with torch.no_grad():
            output = brain(state_tensor)
        
        # Check output shape
        self.assertEqual(output.shape, (1, 6))
        
        # Check output is probability distribution (sums to ~1)
        self.assertAlmostEqual(output.sum().item(), 1.0, places=5)
        
        # Check all values are non-negative
        self.assertTrue((output >= 0).all().item())
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_training_step(self):
        """Test that trainer runs without error and calculates loss"""
        from reality_simulator.neural.trainer import NeuralTrainer
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        trainer = NeuralTrainer(
            config=self.config_neural_enabled['neural'],
            device=torch.device('cpu')
        )
        
        # Create a few neural organisms
        organisms = {}
        for i in range(5):
            genes = np.random.randint(0, 2, 32, dtype=np.uint8)
            genotype = Genotype(genes=genes, generation=0)
            org = NeuralOrganism(genotype=genotype, config=self.config_neural_enabled)
            organisms[org.species_id] = org
        
        # Add some experiences
        for org in organisms.values():
            state = np.random.rand(12).astype(np.float32)
            action = np.random.randint(0, 6)
            reward = np.random.randn()
            next_state = np.random.rand(12).astype(np.float32)
            
            org.experience_buffer.add(state, action, reward, next_state, False)
        
        # Add more experiences to meet batch size (need 32 total, already have 1, so add 31 more)
        for _ in range(31):
            for org in organisms.values():
                state = np.random.rand(12).astype(np.float32)
                action = np.random.randint(0, 6)
                reward = np.random.randn()
                next_state = np.random.rand(12).astype(np.float32)
                org.experience_buffer.add(state, action, reward, next_state, False)
        
        # Network state
        network_state = {
            'generation': 1,
            'organism_count': len(organisms),
            'connection_count': 0,
            'modularity': 0.5,
            'clustering_coefficient': 0.5,
            'max_connections_per_organism': 15,
            'resource_pool': 200.0
        }
        
        # Perform training step
        loss = trainer.train_step(
            organisms=organisms,
            network_state=network_state,
            breath_state=None
        )
        
        # Check that loss was calculated
        self.assertIsNotNone(loss)
        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0.0)
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_breath_sync(self):
        """Test that training respects update frequency"""
        from reality_simulator.neural.trainer import NeuralTrainer
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        # Config with update_frequency = 3 (train every 3 steps)
        config = self.config_neural_enabled.copy()
        config['neural']['training']['update_frequency'] = 3
        
        trainer = NeuralTrainer(
            config=config['neural'],
            device=torch.device('cpu')
        )
        
        # Create organisms with experiences
        organisms = {}
        for i in range(3):
            genes = np.random.randint(0, 2, 32, dtype=np.uint8)
            genotype = Genotype(genes=genes, generation=0)
            org = NeuralOrganism(genotype=genotype, config=config)
            organisms[org.species_id] = org
            
            # Add enough experiences
            for _ in range(35):
                state = np.random.rand(12).astype(np.float32)
                action = np.random.randint(0, 6)
                reward = np.random.randn()
                next_state = np.random.rand(12).astype(np.float32)
                org.experience_buffer.add(state, action, reward, next_state, False)
        
        network_state = {
            'generation': 1,
            'organism_count': len(organisms),
            'connection_count': 0,
            'modularity': 0.5,
            'clustering_coefficient': 0.5,
            'max_connections_per_organism': 15,
            'resource_pool': 200.0
        }
        
        # Step 1: Should not train (step_count % 3 != 0)
        loss1 = trainer.train_step(organisms, network_state, None)
        self.assertIsNone(loss1)  # Should return None (no training)
        
        # Step 2: Should not train
        loss2 = trainer.train_step(organisms, network_state, None)
        self.assertIsNone(loss2)
        
        # Step 3: Should train (step_count % 3 == 0)
        loss3 = trainer.train_step(organisms, network_state, None)
        self.assertIsNotNone(loss3)  # Should return loss
    
    def test_graceful_degradation(self):
        """Test that system works without PyTorch"""
        from reality_simulator.evolution_engine import EvolutionEngine
        
        # Should work even without PyTorch (creates standard Organisms)
        evolution = EvolutionEngine(
            population_size=10,
            genotype_length=32,
            config=self.config_neural_disabled
        )
        
        self.assertTrue(len(evolution.population) > 0)
        from reality_simulator.evolution_engine import Organism
        self.assertIsInstance(evolution.population[0], Organism)
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_experience_buffer(self):
        """Test experience buffer functionality"""
        from reality_simulator.neural.experience import ExperienceBuffer
        
        buffer = ExperienceBuffer(capacity=100)
        
        # Add experiences
        for i in range(50):
            state = np.random.rand(12).astype(np.float32)
            action = i % 6
            reward = float(i)
            next_state = np.random.rand(12).astype(np.float32)
            buffer.add(state, action, reward, next_state, False)
        
        self.assertEqual(len(buffer), 50)
        
        # Sample batch
        batch = buffer.sample(10)
        self.assertEqual(len(batch), 10)
        
        # Sample as arrays
        states, actions, rewards, next_states, dones = buffer.sample_batch(10)
        self.assertEqual(states.shape[0], 10)
        self.assertEqual(actions.shape[0], 10)
        self.assertEqual(rewards.shape[0], 10)
    
    @unittest.skipUnless(PYTORCH_AVAILABLE, "PyTorch not available")
    def test_brain_inheritance(self):
        """Test brain mutation and crossover"""
        from reality_simulator.neural.brain import OrganismBrain
        
        parent1 = OrganismBrain(input_dim=12, hidden_dim=64, output_dim=6)
        parent2 = OrganismBrain(input_dim=12, hidden_dim=64, output_dim=6)
        
        # Test mutation
        parent1_copy = OrganismBrain(input_dim=12, hidden_dim=64, output_dim=6)
        parent1_copy.load_state_dict(parent1.state_dict())
        parent1.mutate(mutation_rate=0.1)
        
        # Check that weights changed
        weights_different = False
        for p1_param, p1_copy_param in zip(parent1.parameters(), parent1_copy.parameters()):
            if not torch.equal(p1_param, p1_copy_param):
                weights_different = True
                break
        self.assertTrue(weights_different)
        
        # Test crossover
        child = parent1.crossover(parent2, crossover_rate=0.5)
        self.assertIsNotNone(child)
        self.assertEqual(child.input_dim, 12)
        self.assertEqual(child.hidden_dim, 64)
        self.assertEqual(child.output_dim, 6)


if __name__ == '__main__':
    unittest.main()

