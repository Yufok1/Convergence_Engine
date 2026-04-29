from reality_simulator.agent_compiler import AgentCompiler
import base64
import json
import pytest
import re
import zlib


class DummyCapsule:
    def __init__(self, organism_id, alliance_id=None, alliance_reputation=0.5):
        self.organism_id = organism_id
        self.alliance_id = alliance_id
        self.alliance_reputation = alliance_reputation
        self.tournament_wins = 0
        self.tournament_losses = 0


class DummyAlliance:
    def __init__(self, name, members):
        self.name = name
        self.members = members
        self.wars_won = 0
        self.wars_lost = 0


class DummyAllianceSystem:
    def __init__(self):
        self.alliances = {
            "a1": DummyAlliance("Alpha", ["o1", "o2"]),
            "a2": DummyAlliance("Beta", ["o3"]),
        }


def test_selected_alliance_export_derives_trust_and_social_graph():
    compiler = AgentCompiler.__new__(AgentCompiler)
    capsules = [
        DummyCapsule("o1", "a1", 0.9),
        DummyCapsule("o2", "a1", 0.8),
        DummyCapsule("o3", "a2", 0.3),
        DummyCapsule("o4", None, 0.5),
    ]
    alliance_system = DummyAllianceSystem()

    filtered, receipt = compiler._filter_capsules_by_selected_alliances(
        capsules,
        alliance_system,
        ["Alpha"],
        include_unallied=False,
    )

    organism_ids = [compiler._get_organism_id(cap) for cap in filtered]
    assert organism_ids == ["o1", "o2"]
    assert receipt["excluded_organisms"] == ["o3", "o4"]
    assert receipt["unallied_organisms"] == ["o4"]

    alliance_data = compiler._extract_alliance_data_for_cocoon(
        filtered,
        alliance_system,
        organism_ids,
        selection_metadata=receipt,
    )

    assert alliance_data["organism_trust"] == {"o1": 0.9, "o2": 0.8}
    assert alliance_data["trust_source"] == "organism_stats.alliance_reputation"
    assert alliance_data["social_graph_present"] is True
    assert alliance_data["social_graph"]["o1"] == ["o2"]
    assert alliance_data["selected_alliances"][0]["alliance_id"] == "a1"
    assert alliance_data["runtime_endpoint_contract_version"] == "cocoon-runtime-v2.1"


def test_selected_alliance_can_include_unallied_by_opt_in():
    compiler = AgentCompiler.__new__(AgentCompiler)
    capsules = [
        DummyCapsule("o1", "a1", 0.9),
        DummyCapsule("o2", "a1", 0.8),
        DummyCapsule("o4", None, 0.5),
    ]

    filtered, receipt = compiler._filter_capsules_by_selected_alliances(
        capsules,
        DummyAllianceSystem(),
        ["a1"],
        include_unallied=True,
    )

    assert [compiler._get_organism_id(cap) for cap in filtered] == ["o1", "o2", "o4"]
    assert receipt["include_unallied"] is True
    assert receipt["unallied_organisms"] == ["o4"]


def test_cocoon_compiler_preserves_non_default_hopfield_config():
    pytest.importorskip("torch")

    from reality_simulator.neural.brain import OrganismBrain

    class DummyOrganism:
        organism_id = "hopfield_probe"
        fitness = 0.7

        def __init__(self):
            self.brain = OrganismBrain(
                input_dim=30,
                hidden_dim=64,
                output_dim=6,
                use_attention=True,
                use_language_head=False,
                use_world_model=False,
                use_hopfield=True,
                hopfield_patterns=8,
                hopfield_iterations=3,
                hopfield_beta=1.5,
            )

    compiler = AgentCompiler()
    source, _readme, _topology = compiler.compile_cocoon(
        [DummyOrganism()],
        export_format="cocoon",
        include_gym=False,
        include_http=False,
    )

    match = re.search(r'_ARCHITECTURE_B64 = "([^"]+)"', source)
    assert match, "generated cocoon source should embed architecture payload"
    architecture = json.loads(zlib.decompress(base64.b64decode(match.group(1))).decode("utf-8"))
    config = architecture["brain_configs"][0]

    assert config["use_hopfield"] is True
    assert config["hopfield_patterns"] == 8
    assert config["hopfield_iterations"] == 3
    assert config["hopfield_beta"] == 1.5
