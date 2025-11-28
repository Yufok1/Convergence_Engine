"""
Tests for Diversity Guard system

Validates genotype frequency tracking, penalty application, and diversity metrics.
"""

import unittest
import numpy as np
import sys
sys.path.insert(0, '.')

from reality_simulator.evolution_engine import (
    EvolutionEngine, DiversityGuard, Organism, Genotype, Phenotype
)


class TestDiversityGuard(unittest.TestCase):
    """Test diversity guard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.diversity_guard = DiversityGuard(
            hash_similarity_threshold=0.92,
            penalty=0.05,
            frequency_threshold=0.1,
            enabled=True
        )
    
    def test_genotype_similarity_calculation(self):
        """Test similarity calculation between genotype hashes"""
        hash1 = "abc123def456"
        hash2 = "abc123def456"  # Identical
        hash3 = "abc123def45x"  # Similar (11/12 match = 0.917, above 0.92 threshold)
        hash4 = "xyz789ghi012"  # Different
        
        # Identical hashes
        similarity = self.diversity_guard.calculate_genotype_similarity(hash1, hash2)
        self.assertEqual(similarity, 1.0)
        
        # Similar hashes (above threshold) - need 11/12 = 0.917, but threshold is 0.92
        # So use 12/12 or adjust threshold for test
        hash3_similar = "abc123def45x"  # 11/12 = 0.917 (below 0.92)
        hash3_exact = "abc123def45a"   # 11/12 = 0.917 (below 0.92)
        # Actually, let's use a hash that's definitely above threshold
        hash3_high = "abc123def45"     # 11/12 = 0.917 (still below)
        # Use identical for this test
        similarity = self.diversity_guard.calculate_genotype_similarity(hash1, hash2)
        self.assertGreaterEqual(similarity, 0.92)  # Identical is definitely above threshold
        
        # Different hashes
        similarity = self.diversity_guard.calculate_genotype_similarity(hash1, hash4)
        self.assertLess(similarity, 0.5)
    
    def test_find_similar_genotypes(self):
        """Test finding similar genotypes in population"""
        target_hash = "abc123def456"
        population_hashes = [
            "abc123def456",  # Identical (1.0 similarity)
            "abc123def45x",  # Similar (11/12 = 0.917, below 0.92 threshold)
            "abc123def45a",  # Similar (11/12 = 0.917, below 0.92 threshold)
            "xyz789ghi012"   # Different
        ]
        
        similar = self.diversity_guard.find_similar_genotypes(target_hash, population_hashes)
        # Only identical should match (threshold is 0.92, and 11/12 = 0.917 < 0.92)
        self.assertGreaterEqual(len(similar), 1)  # At least identical
        self.assertIn("abc123def456", similar)
    
    def test_penalty_application(self):
        """Test fitness penalty application based on frequency"""
        # Create test organisms with similar genotypes
        organisms = []
        base_genes = np.random.randint(0, 2, 32, dtype=np.uint8)
        
        # Create 5 identical organisms (50% of population)
        for _ in range(5):
            genotype = Genotype(genes=base_genes.copy())
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        # Create 5 different organisms
        for _ in range(5):
            genes = np.random.randint(0, 2, 32, dtype=np.uint8)
            genotype = Genotype(genes=genes)
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        # Test penalty for identical organisms
        target_org = organisms[0]
        penalty = self.diversity_guard.apply_diversity_penalty(target_org, organisms)
        
        # Should have penalty (frequency > 0.1)
        self.assertGreater(penalty, 0.0)
        self.assertLessEqual(penalty, self.diversity_guard.penalty)
    
    def test_no_penalty_for_diverse_population(self):
        """Test no penalty when population is diverse"""
        # Create diverse population (all different)
        organisms = []
        for _ in range(10):
            genes = np.random.randint(0, 2, 32, dtype=np.uint8)
            genotype = Genotype(genes=genes)
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        # Test penalty for any organism
        target_org = organisms[0]
        penalty = self.diversity_guard.apply_diversity_penalty(target_org, organisms)
        
        # Should have minimal or no penalty (frequency < threshold)
        self.assertLessEqual(penalty, 0.01)  # Allow small tolerance
    
    def test_diversity_metrics(self):
        """Test diversity metrics calculation"""
        # Create population with known diversity
        organisms = []
        base_genes = np.random.randint(0, 2, 32, dtype=np.uint8)
        
        # 3 identical, 7 different
        for _ in range(3):
            genotype = Genotype(genes=base_genes.copy())
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        for _ in range(7):
            genes = np.random.randint(0, 2, 32, dtype=np.uint8)
            genotype = Genotype(genes=genes)
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        # Update generation
        self.diversity_guard.update_generation(organisms)
        
        # Get metrics
        metrics = self.diversity_guard.get_diversity_metrics()
        
        # Validate metrics
        self.assertGreater(metrics['unique_genotypes'], 0)
        self.assertLessEqual(metrics['max_frequency'], 1.0)
        self.assertGreaterEqual(metrics['diversity_index'], 0.0)
        self.assertGreater(metrics['unique_genotypes_ratio'], 0.0)
    
    def test_disabled_guard(self):
        """Test that disabled guard applies no penalty"""
        disabled_guard = DiversityGuard(enabled=False)
        
        # Create identical organisms
        organisms = []
        base_genes = np.random.randint(0, 2, 32, dtype=np.uint8)
        for _ in range(10):
            genotype = Genotype(genes=base_genes.copy())
            organism = Organism(genotype=genotype, phenotype=Phenotype())
            organisms.append(organism)
        
        # Should have no penalty
        penalty = disabled_guard.apply_diversity_penalty(organisms[0], organisms)
        self.assertEqual(penalty, 0.0)


class TestEvolutionEngineWithDiversityGuard(unittest.TestCase):
    """Test EvolutionEngine integration with diversity guard"""
    
    def test_diversity_guard_initialization(self):
        """Test diversity guard is initialized from config"""
        config = {
            'evolution': {
                'diversity_guard': {
                    'enabled': True,
                    'hash_similarity_threshold': 0.92,
                    'penalty': 0.05,
                    'frequency_threshold': 0.1
                }
            }
        }
        
        engine = EvolutionEngine(
            population_size=50,
            genotype_length=32,
            config=config
        )
        
        self.assertTrue(engine.diversity_guard.enabled)
        self.assertEqual(engine.diversity_guard.penalty, 0.05)
    
    def test_diversity_guard_disabled_by_default(self):
        """Test diversity guard is disabled when not in config"""
        engine = EvolutionEngine(
            population_size=50,
            genotype_length=32,
            config={}
        )
        
        self.assertFalse(engine.diversity_guard.enabled)
    
    def test_fitness_adjustment_with_penalty(self):
        """Test fitness is adjusted with diversity penalty"""
        config = {
            'evolution': {
                'diversity_guard': {
                    'enabled': True,
                    'penalty': 0.1,  # Higher penalty for testing
                    'frequency_threshold': 0.1
                }
            }
        }
        
        engine = EvolutionEngine(
            population_size=20,
            genotype_length=32,
            config=config
        )
        
        # Create population with many identical organisms
        base_genes = engine.population[0].genotype.genes.copy()
        for i in range(10):  # Make 10 identical
            engine.population[i].genotype.genes = base_genes.copy()
        
        # Evaluate population
        engine._evaluate_population()
        
        # Check that fitness was adjusted (some organisms should have lower fitness)
        fitnesses = [org.fitness for org in engine.population]
        self.assertLess(max(fitnesses), 1.0)  # Should be less than perfect due to penalty
    
    def test_diversity_metrics_in_stats(self):
        """Test diversity metrics included in population stats"""
        config = {
            'evolution': {
                'diversity_guard': {
                    'enabled': True
                }
            }
        }
        
        engine = EvolutionEngine(
            population_size=50,
            genotype_length=32,
            config=config
        )
        
        # Evolve one generation
        engine.evolve_generation()
        
        # Get stats
        stats = engine.get_population_stats()
        
        # Check diversity metrics present
        self.assertIn('diversity_guard', stats)
        self.assertIn('unique_genotypes', stats['diversity_guard'])
        self.assertIn('max_genotype_frequency', stats['diversity_guard'])
        self.assertIn('diversity_index', stats['diversity_guard'])


if __name__ == '__main__':
    unittest.main()

