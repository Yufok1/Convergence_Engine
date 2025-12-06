import unittest
from unittest.mock import MagicMock
import time
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reality_simulator.evolution.highlander_protocol import HighlanderProtocol, Alliance
from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem

class TestAllianceIllumination(unittest.TestCase):
    def setUp(self):
        # Mocks
        self.mock_config = {
            'min_alliance_size': 2,
            'max_alliances': 5,
            'war_frequency': 0,
            'illumination_stability_threshold': 3,  # Reduced for testing
            'enabled': True
        }
        self.mock_emitter = MagicMock()
        self.mock_explorer = MagicMock()

        # Components
        # Use mock battle arena to avoid imports
        self.highlander = HighlanderProtocol(event_emitter=self.mock_emitter, battle_arena=MagicMock())
        self.aws = AllianceWarfareSystem(
            highlander_protocol=self.highlander,
            config=self.mock_config,
            event_emitter=self.mock_emitter
        )
        self.highlander.set_alliance_warfare_system(self.aws)

        # Create Mock organisms
        self.org1 = MagicMock()
        self.org1.id = "org1"
        self.org1._illumination_level = 'none'
        
        self.org2 = MagicMock()
        self.org2.id = "org2"
        self.org2._illumination_level = 'none'

        self.organisms = {"org1": self.org1, "org2": self.org2}

    def test_illumination_unlocking(self):
        print("\nTesting Illumination Unlocking...")
        
        # 1. Register organisms in Highlander
        # We need to manually populate organism_stats because register_organism might try to emit event
        self.highlander.register_organism("org1")
        self.highlander.register_organism("org2")

        # 2. Create Alliance in Highlander (Simulate formation)
        h_alliance = Alliance(
            members={"org1", "org2"},
            formation_time=time.time(),
            formation_round=0 # Start at round 0
        )
        a_id = "alliance_1"
        self.highlander.alliances[a_id] = h_alliance
        self.highlander.organism_stats["org1"].alliance_id = a_id
        self.highlander.organism_stats["org2"].alliance_id = a_id
        
        # 3. Run Rounds
        # We simulate 5 rounds. Threshold is 3.
        # Illumination should be granted at round 3 or 4.
        
        for i in range(1, 6):
            self.highlander.round_number = i
            print(f"--- Round {i} ---")
            
            # Set current round organisms so AWS can find them via get_organism
            self.highlander._current_round_organisms = self.organisms
            
            # Calculate stability (current round - formation round)
            stability = i - h_alliance.formation_round
            
            # Sync to AWS (checked against real signature)
            self.aws.sync_alliance_state(
                a_id,
                {
                    'members': list(h_alliance.members),
                    'formation_round': h_alliance.formation_round,
                    'stability_rounds': stability
                }
            )
            
            # Check logic:
            # AWS.sync calls internal update
            # Internal update calculates stability = current_round - formation_round
            # round 1: 1-0 = 1 (<3)
            # round 2: 2-0 = 2 (<3)
            # round 3: 3-0 = 3 (>=3) -> GRANT
            
            if i >= 3:
                # Assert that org1 was updated
                # Note: MagicMock attributes are not automatically updated if we don't mock the property setter?
                # No, standard python objects or Mocks allow attribute setting.
                pass

        print(f"Org1 Illumination Level: {self.org1._illumination_level}")
        
        # Verify call to set level
        # Since _illumination_level is an attribute, we check if it holds the value
        self.assertEqual(self.org1._illumination_level, 'basic')
        self.assertEqual(self.org2._illumination_level, 'basic')
        print("✅ Illumination 'basic' verified for both organisms.")

if __name__ == '__main__':
    unittest.main()
