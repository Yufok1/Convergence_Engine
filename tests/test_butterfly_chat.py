"""
Tests for ButterflyChatRouter
"""
import pytest
from reality_simulator.language.butterfly_chat import ButterflyChatRouter
from reality_simulator.language_system import LanguageVocabulary


class MockOrganism:
    """Mock organism aligned with NeuralOrganism.generate_tokens() signature."""
    def __init__(self, oid, tokens=None, fitness=1.0):
        self.species_id = oid
        self.fitness = fitness
        self._tokens = tokens or [2, 3, 4]
        self.experience_buffer = []  # Required for adaptive max_length calculation

    def generate_tokens(self, context_memory=None, max_length=50, vp_value=None, temperature=1.0, input_tokens=None):
        """
        Generate tokens - aligned with NeuralOrganism signature.

        Args:
            context_memory: Optional context memory (ignored in mock)
            max_length: Maximum tokens to generate
            vp_value: Violation pressure value (ignored in mock)
            temperature: Sampling temperature (ignored in mock)
            input_tokens: Optional input token IDs for conditioning (ignored in mock)
        """
        return self._tokens[:max_length]


def make_vocab():
    v = LanguageVocabulary()
    # add a few words for decoding
    for w in ['hello', 'world', 'test', 'butterfly', 'chat']:
        v.add_word(w)
    return v


def test_route_all():
    vocab = make_vocab()
    orgs = {
        'o1': MockOrganism('o1', tokens=[5, 6, 7], fitness=0.8),
        'o2': MockOrganism('o2', tokens=[6, 7, 8], fitness=0.9),
        'o3': MockOrganism('o3', tokens=[7, 8, 9], fitness=0.5)
    }

    router = ButterflyChatRouter(orgs, vocabulary=vocab)
    out = router.route_message('hello butterfly', routing_strategy='all')

    assert 'response' in out
    assert isinstance(out['organism_responses'], list)
    assert out['routing_info']['organisms_queried'] == 3


def test_route_fittest():
    vocab = make_vocab()
    orgs = {
        'a': MockOrganism('a', tokens=[5], fitness=0.1),
        'b': MockOrganism('b', tokens=[6], fitness=0.9),
        'c': MockOrganism('c', tokens=[7], fitness=0.2)
    }
    router = ButterflyChatRouter(orgs, vocabulary=vocab)
    out = router.route_message('test', routing_strategy='fittest', max_organisms=1)
    assert out['routing_info']['organisms_queried'] == 1
    assert len(out['organism_responses']) == 1


def test_route_by_word_with_anchors():
    vocab = make_vocab()
    orgs = {
        '1': MockOrganism('1', tokens=[5], fitness=0.5),
        '2': MockOrganism('2', tokens=[6], fitness=0.5)
    }
    # network_state provides language_anchors mapping
    network_state = {'language_anchors': {'hello': {'1'}, 'butterfly': {'2'}}}
    router = ButterflyChatRouter(orgs, vocabulary=vocab)
    out = router.route_message('hello', routing_strategy='by_word', network_state=network_state)
    assert out['routing_info']['organisms_queried'] >= 1

if __name__ == '__main__':
    pytest.main([__file__, '-q'])
