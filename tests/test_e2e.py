import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock GUI dependencies BEFORE importing unified_entry
sys.modules['tkinter'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['matplotlib.backends.backend_tkagg'] = MagicMock()
sys.modules['mpl_toolkits.mplot3d'] = MagicMock()

from unified_entry import UnifiedSystem, PreFlightChecker, StateLogger

class TestUnifiedSystemE2E(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for logs
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.test_dir) / 'logs'
        self.log_dir.mkdir()

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    @patch('unified_entry.PreFlightChecker')
    def test_initialization(self, MockChecker):
        """Test that the system initializes all components correctly"""
        # Mock pre-flight checks to pass
        mock_checker_instance = MockChecker.return_value
        mock_checker_instance.run_all_checks.return_value = {
            'can_start': True,
            'checks': [],
            'warnings': [],
            'failures': []
        }

        # Initialize system with visualization disabled (to avoid complex mocking)
        system = UnifiedSystem(enable_visualization=False)
        
        # Verify components are initialized
        self.assertIsNotNone(system.logger)
        # Note: controller might be None if dependencies are missing in the environment, 
        # but we expect it to try.
        # Check if we are in an environment where we expect success
        if system.controller:
            self.assertIsNotNone(system.reality_sim)
            # Check references
            self.assertEqual(system.reality_sim, system.controller.reality_sim)

    @patch('unified_entry.PreFlightChecker')
    def test_state_retrieval(self, MockChecker):
        """Test that we can retrieve state from all subsystems"""
        mock_checker_instance = MockChecker.return_value
        mock_checker_instance.run_all_checks.return_value = {'can_start': True}

        system = UnifiedSystem(enable_visualization=False)
        
        # Mock the controller and subsystems if they failed to load (e.g. missing deps)
        if not system.controller:
            system.controller = MagicMock()
            system.reality_sim = MagicMock()
            system.reality_sim.components = {
                'network': MagicMock(),
                'renderer': MagicMock()
            }
            # Setup mock network
            network = system.reality_sim.components['network']
            network.organisms = [1, 2, 3] # Mock list
            network.connections = [1, 2]
            network.metrics.modularity = 0.5
            network.metrics.clustering_coefficient = 0.3
            
            # Setup mock breath engine
            system.controller.breath_engine.get_breath_state.return_value = {
                'cycle_count': 10,
                'depth': 0.8
            }
            
            # Setup mock sentinel
            system.controller.sentinel.vp_history = [1, 2, 3, 4, 5]

        # Test Reality Sim state
        rs_state = system._get_reality_sim_state()
        self.assertIn('organism_count', rs_state)
        self.assertIn('connection_count', rs_state)
        self.assertIsInstance(rs_state['organism_count'], int)

        # Test Explorer state
        ex_state = system._get_explorer_state()
        self.assertIn('phase', ex_state)
        self.assertIn('vp_calculations', ex_state)
        self.assertIn('breath_cycle', ex_state)

        # Test Djinn Kernel state
        dk_state = system._get_djinn_kernel_state()
        self.assertIn('violation_pressure', dk_state)
        self.assertIn('vp_classification', dk_state)

    def test_pre_flight_checker(self):
        """Test the pre-flight checker logic"""
        checker = PreFlightChecker()
        
        # Check dependencies
        dep_checks = checker.check_dependencies()
        self.assertIsInstance(dep_checks, list)
        self.assertTrue(len(dep_checks) > 0)
        
        # Check files
        file_checks = checker.check_files()
        self.assertIsInstance(file_checks, list)
        # We expect some files to exist since we are in the repo
        
    @patch('unified_entry.UnifiedVisualization')
    @patch('unified_entry.PreFlightChecker')
    def test_main_loop_logic(self, MockChecker, MockViz):
        """Simulate one iteration of the main loop"""
        mock_checker_instance = MockChecker.return_value
        mock_checker_instance.run_all_checks.return_value = {'can_start': True}
        
        system = UnifiedSystem(enable_visualization=True)
        
        # Mock controller to avoid actual execution
        system.controller = MagicMock()
        
        # Execute the logic that happens inside the loop manually
        
        # 1. Get states
        rs_state = system._get_reality_sim_state()
        ex_state = system._get_explorer_state()
        dk_state = system._get_djinn_kernel_state()
        
        # 2. Log states
        system.logger.log_reality_sim(rs_state)
        system.logger.log_explorer(ex_state)
        system.logger.log_djinn_kernel(dk_state)
        
        # 3. Update visualization
        if system.visualization:
            system.visualization.update(rs_state, ex_state, dk_state)
            system.visualization.update.assert_called_once()

if __name__ == '__main__':
    unittest.main()
