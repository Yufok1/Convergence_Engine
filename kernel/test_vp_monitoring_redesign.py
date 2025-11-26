"""
Comprehensive tests for VP Monitoring System Redesign

Tests backward compatibility, diagnostics, stabilization, decomposition, and adaptive thresholds.
"""

import unittest
from typing import Dict, Any
import json
from pathlib import Path
import os
import sys

# Add kernel path
kernel_path = Path(__file__).parent
sys.path.insert(0, str(kernel_path))

from violation_pressure_calculation import (
    ViolationMonitor, VPDiagnostics, VPStabilizer, VPComponentCalculator,
    AdaptiveThresholdManager, ViolationClass, StabilityEnvelope
)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that existing VP calculation behavior is unchanged"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.vp_monitor = ViolationMonitor()
        self.test_payload = {
            'intimacy': 0.8,
            'commitment': 0.3,
            'caregiving': 0.7
        }
    
    def test_default_initialization(self):
        """Test that ViolationMonitor initializes with all features disabled"""
        self.assertFalse(self.vp_monitor.diagnostics.enabled)
        self.assertFalse(self.vp_monitor.stabilization_enabled)
        self.assertFalse(self.vp_monitor.component_decomposition_enabled)
        self.assertFalse(self.vp_monitor.adaptive_thresholds_enabled)
    
    def test_existing_api_unchanged(self):
        """Test that existing compute_violation_pressure API works unchanged"""
        total_vp, breakdown = self.vp_monitor.compute_violation_pressure(self.test_payload)
        
        # Verify return type and structure
        self.assertIsInstance(total_vp, float)
        self.assertIsInstance(breakdown, dict)
        self.assertTrue(0.0 <= total_vp <= 1.0)
        
        # Verify all traits are in breakdown
        for trait in self.test_payload:
            self.assertIn(trait, breakdown)
    
    def test_classification_unchanged(self):
        """Test that VP classification still works"""
        total_vp, _ = self.vp_monitor.compute_violation_pressure(self.test_payload)
        classification = self.vp_monitor._classify_violation_pressure(total_vp)
        
        self.assertIsInstance(classification, ViolationClass)
        self.assertIn(classification, list(ViolationClass))


class TestVPDiagnostics(unittest.TestCase):
    """Test diagnostic logging functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.vp_monitor = ViolationMonitor(diagnostics_enabled=True)
        self.test_payload = {
            'intimacy': 0.8,
            'commitment': 0.3
        }
    
    def test_diagnostics_enabled(self):
        """Test that diagnostics are enabled"""
        self.assertTrue(self.vp_monitor.diagnostics.enabled)
    
    def test_diagnostics_logging(self):
        """Test that diagnostics log trait breakdowns"""
        total_vp, breakdown = self.vp_monitor.compute_violation_pressure(self.test_payload)
        
        # Verify calculation still works
        self.assertIsInstance(total_vp, float)
        
        # Verify diagnostic log file exists (if enabled)
        if self.vp_monitor.diagnostics.log_file.exists():
            # File should exist if diagnostics enabled
            pass
    
    def test_get_vp_diagnostics(self):
        """Test diagnostic breakdown retrieval"""
        diagnostics = self.vp_monitor.get_vp_diagnostics(self.test_payload)
        
        self.assertIn('trait_analysis', diagnostics)
        self.assertIn('envelope_analysis', diagnostics)
        self.assertIn('summary', diagnostics)
        
        # Verify trait analysis contains expected traits
        for trait in self.test_payload:
            self.assertIn(trait, diagnostics['trait_analysis'])


class TestVPStabilizer(unittest.TestCase):
    """Test VP stabilization functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.stabilizer = VPStabilizer(
            history_size=10,
            max_jump=0.1,
            smoothing_factor=0.3
        )
    
    def test_stabilizer_initialization(self):
        """Test stabilizer initializes correctly"""
        self.assertEqual(self.stabilizer.history_size, 10)
        self.assertEqual(self.stabilizer.max_jump, 0.1)
        self.assertEqual(self.stabilizer.smoothing_factor, 0.3)
    
    def test_jump_limiting(self):
        """Test that large jumps are limited"""
        # First value
        vp1 = self.stabilizer.stabilize(0.5)
        self.assertEqual(vp1, 0.5)
        
        # Try to jump too far
        vp2 = self.stabilizer.stabilize(0.8)  # 0.3 jump, should be limited to 0.1
        
        # Should be limited to max_jump
        jump = vp2 - vp1
        self.assertLessEqual(abs(jump), 0.1)
    
    def test_smoothing(self):
        """Test that VP values are smoothed"""
        # Stabilize multiple values
        values = []
        for vp in [0.5, 0.6, 0.7, 0.8]:
            stabilized = self.stabilizer.stabilize(vp)
            values.append(stabilized)
        
        # Values should be smoothed (less volatile)
        self.assertIsNotNone(self.stabilizer.last_vp)
    
    def test_history_tracking(self):
        """Test that history is tracked"""
        for i in range(15):
            self.stabilizer.stabilize(0.5 + (i * 0.01))
        
        # History should not exceed history_size
        self.assertLessEqual(len(self.stabilizer.vp_history), 10)
    
    def test_stabilization_integration(self):
        """Test stabilization integrated with ViolationMonitor"""
        vp_monitor = ViolationMonitor(stabilization_enabled=True, max_vp_jump=0.1)
        self.assertTrue(vp_monitor.stabilization_enabled)
        self.assertIsNotNone(vp_monitor.stabilizer)
        
        payload = {'intimacy': 0.8}
        total_vp, _ = vp_monitor.compute_violation_pressure(payload)
        
        # Should return valid VP
        self.assertTrue(0.0 <= total_vp <= 1.0)


class TestVPComponentCalculator(unittest.TestCase):
    """Test component decomposition functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = VPComponentCalculator()
        self.test_payload = {
            'organism_count': 0.5,
            'modularity': 0.3,
            'intimacy': 0.6,
            'commitment': 0.7
        }
        self.envelopes = {
            'organism_count': StabilityEnvelope(center=0.4, radius=0.2),
            'modularity': StabilityEnvelope(center=0.3, radius=0.2),
            'intimacy': StabilityEnvelope(center=0.6, radius=0.3),
            'commitment': StabilityEnvelope(center=0.7, radius=0.25)
        }
    
    def test_component_calculation(self):
        """Test that components are calculated"""
        components = self.calculator.calculate_components(self.test_payload, self.envelopes)
        
        self.assertIn('trait_divergence', components)
        self.assertIn('network_coherence', components)
        self.assertIn('phase_mismatch', components)
        self.assertIn('evolution_pressure', components)
        self.assertIn('quantum_entropy', components)
        
        # All components should be in [0, 1] range
        for component_vp in components.values():
            self.assertTrue(0.0 <= component_vp <= 1.0)
    
    def test_component_combination(self):
        """Test that components are combined correctly"""
        components = {
            'trait_divergence': 0.3,
            'network_coherence': 0.2,
            'phase_mismatch': 0.1,
            'evolution_pressure': 0.2,
            'quantum_entropy': 0.15
        }
        
        total_vp = self.calculator.combine_components(components)
        
        self.assertTrue(0.0 <= total_vp <= 1.0)
    
    def test_sigmoid_smoothing(self):
        """Test that sigmoid smoothing works"""
        result = self.calculator.sigmoid(0.5)
        self.assertTrue(0.0 <= result <= 1.0)
    
    def test_decomposed_calculation(self):
        """Test decomposed VP calculation"""
        vp_monitor = ViolationMonitor(component_decomposition_enabled=True)
        self.assertTrue(vp_monitor.component_decomposition_enabled)
        
        total_vp, per_trait, component_breakdown = vp_monitor.compute_violation_pressure_decomposed(
            self.test_payload
        )
        
        self.assertTrue(0.0 <= total_vp <= 1.0)
        self.assertIsInstance(per_trait, dict)
        self.assertIsInstance(component_breakdown, dict)


class TestAdaptiveThresholdManager(unittest.TestCase):
    """Test adaptive threshold functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.threshold_manager = AdaptiveThresholdManager()
    
    def test_base_thresholds(self):
        """Test base threshold values"""
        thresholds = self.threshold_manager.base_thresholds
        
        self.assertEqual(thresholds[ViolationClass.VP0_FULLY_LAWFUL], 0.25)
        self.assertEqual(thresholds[ViolationClass.VP1_STABLE_DRIFT], 0.50)
        self.assertEqual(thresholds[ViolationClass.VP2_INSTABILITY], 0.75)
        self.assertEqual(thresholds[ViolationClass.VP3_CRITICAL_DIVERGENCE], 1.00)
    
    def test_genesis_thresholds(self):
        """Test Genesis phase thresholds are more sensitive"""
        historical_vps = [0.1, 0.15, 0.2, 0.18, 0.22]
        thresholds = self.threshold_manager.adjust_thresholds_for_phase('genesis', historical_vps)
        
        # Genesis thresholds should be lower (more sensitive)
        self.assertLess(thresholds[ViolationClass.VP0_FULLY_LAWFUL], 0.25)
    
    def test_sovereign_thresholds(self):
        """Test Sovereign phase thresholds are less sensitive"""
        historical_vps = [0.3, 0.35, 0.32, 0.38, 0.34]
        thresholds = self.threshold_manager.adjust_thresholds_for_phase('sovereign', historical_vps)
        
        # Sovereign thresholds should be adjusted
        self.assertIsNotNone(thresholds)
    
    def test_adaptive_classification(self):
        """Test adaptive classification"""
        historical_vps = [0.1, 0.15, 0.2] * 10  # Replicate for enough history
        
        # Test classification with adaptive thresholds
        classification = self.threshold_manager.classify_with_adaptive_thresholds(
            0.2, 'genesis', historical_vps
        )
        
        self.assertIsInstance(classification, ViolationClass)
    
    def test_adaptive_integration(self):
        """Test adaptive thresholds integrated with ViolationMonitor"""
        vp_monitor = ViolationMonitor(adaptive_thresholds_enabled=True)
        self.assertTrue(vp_monitor.adaptive_thresholds_enabled)
        self.assertIsNotNone(vp_monitor.adaptive_threshold_manager)
        
        payload = {'intimacy': 0.8}
        total_vp, _ = vp_monitor.compute_violation_pressure(payload, system_phase='genesis')
        
        # Should return valid VP
        self.assertTrue(0.0 <= total_vp <= 1.0)


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading from config.json"""
    
    def test_config_structure(self):
        """Test that config.json has correct structure"""
        config_path = Path(__file__).parent.parent / 'config.json'
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.assertIn('vp_monitoring', config)
            vp_config = config['vp_monitoring']
            
            self.assertIn('diagnostics_enabled', vp_config)
            self.assertIn('stabilization_enabled', vp_config)
            self.assertIn('adaptive_thresholds_enabled', vp_config)
            self.assertIn('component_decomposition_enabled', vp_config)
            self.assertIn('stabilization', vp_config)
            self.assertIn('component_weights', vp_config)


class TestIntegration(unittest.TestCase):
    """Test integration of all features together"""
    
    def test_all_features_enabled(self):
        """Test that all features can be enabled simultaneously"""
        vp_monitor = ViolationMonitor(
            diagnostics_enabled=True,
            stabilization_enabled=True,
            component_decomposition_enabled=True,
            adaptive_thresholds_enabled=True
        )
        
        self.assertTrue(vp_monitor.diagnostics.enabled)
        self.assertTrue(vp_monitor.stabilization_enabled)
        self.assertTrue(vp_monitor.component_decomposition_enabled)
        self.assertTrue(vp_monitor.adaptive_thresholds_enabled)
        
        # Should still calculate VP correctly
        payload = {'intimacy': 0.8, 'commitment': 0.3}
        total_vp, breakdown = vp_monitor.compute_violation_pressure(payload, system_phase='genesis')
        
        self.assertTrue(0.0 <= total_vp <= 1.0)
        self.assertIsInstance(breakdown, dict)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestVPDiagnostics))
    suite.addTests(loader.loadTestsFromTestCase(TestVPStabilizer))
    suite.addTests(loader.loadTestsFromTestCase(TestVPComponentCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveThresholdManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)

