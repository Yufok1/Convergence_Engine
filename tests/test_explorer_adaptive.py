import pytest
pytest.skip("Import collision: kernel package shadows explorer/kernel.py - needs path restructure", allow_module_level=True)

import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
EXPLORER_DIR = PROJECT_ROOT / "explorer"
if str(EXPLORER_DIR) not in sys.path:
    sys.path.insert(0, str(EXPLORER_DIR))

from explorer.main import BiphasicController, StabilityEnvelope


class DummyLedger:
    def __init__(self):
        self.next_position = 1


class DummyKernel:
    def __init__(self):
        self.akashic_ledger = DummyLedger()
        self.executed = []
        self.event_publisher = types.SimpleNamespace(publish=lambda *args, **kwargs: None)

    def execute_instruction(self, instruction):
        self.executed.append(instruction.operation)
        self.akashic_ledger.next_position += 1
        return True


class DummyMonitor:
    def __init__(self):
        self._envelopes = {
            "organism_count": StabilityEnvelope(center=0.4, radius=0.2, compression_factor=1.0)
        }

    def get_stability_envelope(self, trait_name):
        return self._envelopes.get(trait_name)

    def set_stability_envelope(self, trait_name, envelope):
        self._envelopes[trait_name] = envelope


def _build_controller():
    controller = BiphasicController.__new__(BiphasicController)
    controller.vp_monitor = DummyMonitor()
    controller.utm_kernel = DummyKernel()
    controller.reality_sim = None
    controller.breath_engine = types.SimpleNamespace(
        get_breath_state=lambda: {"cycle_count": 0},
        get_breath_pulse=lambda: 0.0
    )
    controller.current_config = {
        "vp_monitoring": {
            "adaptive_response": {"high_vp_threshold": 0.5, "streak_threshold": 2}
        }
    }
    controller.high_vp_threshold = 0.5
    controller.streak_threshold = 2
    controller.fallback_streak = 4
    controller.envelope_widen_factor = 1.1
    controller.vp_high_streak = 0
    controller.last_adaptive_actions = []
    controller.dynamic_operations = None
    controller._publish_adaptive_event = lambda *args, **kwargs: None
    return controller


def test_adaptive_response_widens_envelope_and_queues_arbitration():
    controller = _build_controller()
    traits = {"organism_count": 0.9}
    breakdown = {"organism_count": 0.8}

    controller._handle_vp_feedback(0.8, traits, breakdown)
    assert controller.vp_high_streak == 1

    controller._handle_vp_feedback(0.82, traits, breakdown)

    assert controller.vp_high_streak >= controller.streak_threshold
    assert any(action.startswith("widen_envelope") for action in controller.last_adaptive_actions)
    assert any(op == "ARBITRATE" for op in controller.utm_kernel.executed)

