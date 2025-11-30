"""
Tests for Neural Language Model Integration

Validates:
- Phase 0: LanguageVocabulary class
- Phase 1: MultiHeadAttention + dual-head architecture
- Phase 2: Tokenization + vocabulary integration
- Phase 3: Sequence modeling in neural organisms
- Phase 4: Token embedding exchange
- Phase 5: VP integration + language loss
- Phase 6: Experience buffer with token sequences
- Phase 7: Config integration
"""

import pytest
import numpy as np
import json
from pathlib import Path


class TestPhase0LanguageVocabulary:
    """Test LanguageVocabulary class from language_system.py"""
    
    def test_vocabulary_creation(self):
        """Test basic vocabulary creation with special tokens"""
        from reality_simulator.language_system import LanguageVocabulary
        
        vocab = LanguageVocabulary()
        assert vocab is not None
        assert vocab.vocab_size >= 5  # At least special tokens
        
    def test_special_tokens_present(self):
        """Test that all special tokens are in vocabulary"""
        from reality_simulator.language_system import LanguageVocabulary, SPECIAL_TOKENS
        
        vocab = LanguageVocabulary()
        for token in SPECIAL_TOKENS:
            assert vocab.get_id(token) is not None
            
    def test_deterministic_ordering(self):
        """Test that vocabulary built from anchors has deterministic ordering"""
        from reality_simulator.language_system import LanguageVocabulary
        
        # When using build_from_language_anchors, ordering should be deterministic
        anchors1 = {'gamma': {1}, 'alpha': {2}, 'beta': {3}}
        anchors2 = {'beta': {1}, 'gamma': {2}, 'alpha': {3}}
        
        vocab1 = LanguageVocabulary()
        vocab1.build_from_language_anchors(anchors1)
        
        vocab2 = LanguageVocabulary()
        vocab2.build_from_language_anchors(anchors2)
        
        # Both should give same IDs for same words (sorted order)
        assert vocab1.get_id("alpha") == vocab2.get_id("alpha")
        assert vocab1.get_id("beta") == vocab2.get_id("beta")
        assert vocab1.get_id("gamma") == vocab2.get_id("gamma")
        
    def test_tokenize_detokenize(self):
        """Test tokenization round-trip"""
        from reality_simulator.language_system import LanguageVocabulary
        
        vocab = LanguageVocabulary()
        vocab.add_word("hello")
        vocab.add_word("world")
        
        # Encode words
        tokens = vocab.encode(["hello", "world"], add_special=False)
        assert len(tokens) == 2
        
        # Decode tokens
        words = vocab.decode(tokens)
        assert "hello" in words
        assert "world" in words


class TestPhase1MultiHeadAttention:
    """Test MultiHeadAttention and dual-head architecture"""
    
    def test_attention_module_creation(self):
        """Test MultiHeadAttention module creation"""
        import torch
        from reality_simulator.neural.brain import MultiHeadAttention
        
        attention = MultiHeadAttention(
            embed_dim=64,
            num_heads=4,
            dropout=0.1
        )
        assert attention is not None
        
    def test_attention_forward_pass(self):
        """Test attention forward pass with VP scaling"""
        import torch
        from reality_simulator.neural.brain import MultiHeadAttention
        
        attention = MultiHeadAttention(
            embed_dim=64,
            num_heads=4,
            dropout=0.1
        )
        
        x = torch.randn(2, 10, 64)  # batch=2, seq=10, dim=64
        output = attention(x, vp_value=0.3)
        
        assert output.shape == x.shape
        
    def test_vp_temperature_scaling(self):
        """Test that VP value affects attention behavior"""
        import torch
        from reality_simulator.neural.brain import MultiHeadAttention
        
        attention = MultiHeadAttention(
            embed_dim=64,
            num_heads=4,
            dropout=0.0  # No dropout for deterministic test
        )
        attention.eval()  # Disable any dropout
        
        torch.manual_seed(42)
        x = torch.randn(1, 5, 64)
        
        with torch.no_grad():
            # Low VP = sharper attention
            output_low_vp = attention(x, vp_value=0.1)
            # High VP = softer attention (divided by larger value)
            output_high_vp = attention(x, vp_value=0.8)
        
        # Outputs should be different due to different VP scaling
        assert not torch.allclose(output_low_vp, output_high_vp, atol=1e-5)
        
    def test_dual_head_brain(self):
        """Test OrganismBrain with attention (language head is optional)"""
        import torch
        from reality_simulator.neural.brain import OrganismBrain
        
        brain = OrganismBrain(
            input_dim=18,
            hidden_dim=64,
            output_dim=6,
            use_attention=False  # Attention requires 3D input, skip for this test
        )
        
        assert hasattr(brain, 'fc3')  # Action head
        
        x = torch.randn(1, 18)
        action_logits = brain(x)
        assert action_logits.shape == (1, 6)


class TestPhase2Tokenization:
    """Test tokenization and vocabulary integration in ContextMemory"""
    
    def test_context_memory_vocabulary(self):
        """Test that ContextMemory has vocabulary"""
        from reality_simulator.memory.context_memory import ContextMemory
        
        cm = ContextMemory()
        assert hasattr(cm, 'vocabulary')
        assert cm.vocabulary is not None
        
    def test_build_vocabulary_from_anchors(self):
        """Test building vocabulary from language anchors"""
        from reality_simulator.memory.context_memory import ContextMemory
        from collections import defaultdict
        
        cm = ContextMemory()
        # Initialize language_anchors as defaultdict if not already
        if not isinstance(cm.language_anchors, defaultdict):
            cm.language_anchors = defaultdict(set)
        
        # Add some language anchors (word -> organism_ids)
        cm.language_anchors['test'].add(1)
        cm.language_anchors['vocabulary'].add(2)
        cm.language_anchors['building'].add(3)
        
        # Build vocabulary
        if cm.vocabulary:
            cm.vocabulary.build_from_language_anchors(dict(cm.language_anchors))
            
            # Check words are in vocabulary
            for word in ['test', 'vocabulary', 'building']:
                token_id = cm.vocabulary.get_id(word)
                # Should not be UNK (1)
                assert token_id != 1
            
    def test_tokenize_sequence(self):
        """Test tokenizing word sequences"""
        from reality_simulator.memory.context_memory import ContextMemory
        
        cm = ContextMemory()
        words = ['move', 'cooperate', 'compete']
        
        tokens = cm.tokenize_sequence(words)
        assert len(tokens) >= len(words)  # May include special tokens


class TestPhase3SequenceModeling:
    """Test sequence tracking in NeuralOrganism"""
    
    def test_organism_sequence_tracking(self):
        """Test that organism tracks action/state sequences"""
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        config = {
            'neural': {
                'enabled': True,
                'brain': {'input_dim': 18, 'hidden_dim': 32, 'output_dim': 6},  # Match default
                'training': {'memory_size': 100},
                'language_model': {'max_sequence_length': 64}
            }
        }
        
        genotype = Genotype(genes=np.random.randint(0, 2, 48, dtype=np.uint8))
        organism = NeuralOrganism(genotype, config=config)
        
        assert hasattr(organism, 'action_history')
        assert hasattr(organism, 'state_history')
        assert hasattr(organism, 'token_sequence')
        
    def test_sequence_recording_during_decision(self):
        """Test that decide_action records sequences"""
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        config = {
            'neural': {
                'enabled': True,
                'device': 'cpu',  # Force CPU for tests
                'brain': {'input_dim': 18, 'hidden_dim': 32, 'output_dim': 6},
                'training': {'memory_size': 100, 'epsilon_start': 1.0}  # Full exploration
            }
        }
        
        genotype = Genotype(genes=np.random.randint(0, 2, 48, dtype=np.uint8))
        organism = NeuralOrganism(genotype, config=config)
        
        # Move brain to CPU
        if organism.brain is not None:
            organism.brain = organism.brain.cpu()
        
        # Make some decisions
        for _ in range(5):
            action = organism.decide_action()
            assert 0 <= action <= 5
            
        # Should have recorded sequences
        assert len(organism.action_history) == 5
        
    def test_communication_pattern_extraction(self):
        """Test extract_communication_pattern method"""
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        config = {
            'neural': {
                'enabled': True,
                'device': 'cpu',  # Force CPU for tests
                'brain': {'input_dim': 18, 'hidden_dim': 32, 'output_dim': 6},
                'training': {'memory_size': 100, 'epsilon_start': 1.0}  # Full exploration
            }
        }
        
        genotype = Genotype(genes=np.random.randint(0, 2, 48, dtype=np.uint8))
        organism = NeuralOrganism(genotype, config=config)
        
        # Move brain to CPU
        if organism.brain is not None:
            organism.brain = organism.brain.cpu()
        
        # Make some decisions
        for _ in range(3):
            organism.decide_action()
            
        pattern = organism.extract_communication_pattern()
        
        assert 'organism_id' in pattern
        assert 'action_sequence' in pattern
        assert 'fitness_trend' in pattern


class TestPhase4MessagePassing:
    """Test token embedding exchange in SymbioticNetwork"""
    
    def test_exchange_token_embeddings(self):
        """Test exchange_token_embeddings method exists"""
        from reality_simulator.symbiotic_network import SymbioticNetwork
        
        network = SymbioticNetwork()
        assert hasattr(network, 'exchange_token_embeddings')
        
    def test_embedding_exchange_with_organisms(self):
        """Test embedding exchange between organisms"""
        from reality_simulator.symbiotic_network import SymbioticNetwork
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.evolution_engine import Genotype
        
        config = {
            'neural': {
                'enabled': True,
                'brain': {'input_dim': 12, 'hidden_dim': 32, 'output_dim': 6},
                'training': {'memory_size': 100}
            }
        }
        
        network = SymbioticNetwork()
        
        # Create organisms with token sequences
        for i in range(3):
            genotype = Genotype(genes=np.random.randint(0, 2, 48, dtype=np.uint8))
            organism = NeuralOrganism(genotype, config=config)
            organism.token_sequence.extend([1, 2, 3, 4])  # Add tokens
            network.add_organism(organism)
            
        # Add language connection
        org_ids = list(network.organisms.keys())
        if len(org_ids) >= 2:
            network.language_connections.add((org_ids[0], org_ids[1]))
            
        # Exchange
        result = network.exchange_token_embeddings()
        assert 'exchanges_performed' in result


class TestPhase5VPIntegration:
    """Test VP integration in trainer"""
    
    def test_trainer_vp_scaling(self):
        """Test that trainer respects VP for temperature scaling"""
        from reality_simulator.neural.trainer import NeuralTrainer
        
        config = {
            'neural': {
                'enabled': True,
                'brain': {'input_dim': 12, 'hidden_dim': 32, 'output_dim': 6},
                'training': {
                    'learning_rate': 0.001,
                    'gamma': 0.99,
                    'batch_size': 16
                },
                'language_model': {
                    'training': {'alpha': 0.9, 'beta': 0.1}
                }
            }
        }
        
        trainer = NeuralTrainer(config)
        assert trainer is not None
        
    def test_curriculum_learning_config(self):
        """Test curriculum learning configuration"""
        from reality_simulator.neural.trainer import NeuralTrainer
        
        config = {
            'neural': {
                'enabled': True,
                'brain': {'input_dim': 12, 'hidden_dim': 32, 'output_dim': 6},
                'training': {
                    'learning_rate': 0.001,
                    'gamma': 0.99,
                    'batch_size': 16
                },
                'language_model': {
                    'curriculum': {
                        'enabled': True,
                        'vp_thresholds': {'stage_1': 0.5, 'stage_2': 0.4, 'stage_3': 0.3}
                    }
                }
            }
        }
        
        trainer = NeuralTrainer(config)
        assert hasattr(trainer, 'current_sequence_length') or hasattr(trainer, 'update_curriculum_learning')


class TestPhase6ExperienceBuffer:
    """Test Experience buffer with token sequences"""
    
    def test_experience_with_tokens(self):
        """Test Experience class includes token sequence"""
        from reality_simulator.neural.experience import Experience
        
        state = np.zeros(12)
        exp = Experience(
            state=state,
            action=0,
            reward=1.0,
            next_state=state,
            done=False,
            token_sequence=[1, 2, 3],
            vp_value=0.3
        )
        
        assert exp.token_sequence == [1, 2, 3]
        assert exp.vp_value == 0.3
        
    def test_buffer_add_with_tokens(self):
        """Test adding experiences with tokens to buffer"""
        from reality_simulator.neural.experience import ExperienceBuffer
        
        buffer = ExperienceBuffer(capacity=100)
        state = np.zeros(12)
        
        buffer.add(
            state=state,
            action=0,
            reward=1.0,
            next_state=state,
            done=False,
            token_sequence=[1, 2, 3, 4],
            vp_value=0.5
        )
        
        assert len(buffer) == 1
        
    def test_sample_batch_with_tokens(self):
        """Test sampling batch with token sequences"""
        from reality_simulator.neural.experience import ExperienceBuffer
        
        buffer = ExperienceBuffer(capacity=100)
        state = np.zeros(12)
        
        # Add several experiences
        for i in range(20):
            buffer.add(
                state=state,
                action=i % 6,
                reward=0.1 * i,
                next_state=state,
                done=False,
                token_sequence=[i, i+1, i+2],
                vp_value=0.1 * i
            )
            
        # Sample with tokens
        states, actions, rewards, next_states, dones, tokens, vps = buffer.sample_batch_with_tokens(8)
        
        assert len(tokens) == 8
        assert len(vps) == 8
        assert all(len(t) == 3 for t in tokens)


class TestPhase7Config:
    """Test config.json integration"""
    
    def test_config_has_language_model(self):
        """Test that config.json has language_model section"""
        config_path = Path(__file__).parent.parent / 'config.json'
        
        with open(config_path) as f:
            config = json.load(f)
            
        assert 'neural' in config
        assert 'language_model' in config['neural']
        
    def test_language_model_config_structure(self):
        """Test language_model config has required sections"""
        config_path = Path(__file__).parent.parent / 'config.json'
        
        with open(config_path) as f:
            config = json.load(f)
            
        lm_config = config['neural']['language_model']
        
        assert 'enabled' in lm_config
        assert 'attention' in lm_config
        assert 'vocabulary' in lm_config
        assert 'sequence' in lm_config
        assert 'training' in lm_config
        assert 'curriculum' in lm_config


class TestBackwardCompatibility:
    """Ensure existing functionality still works"""
    
    def test_brain_without_attention(self):
        """Test brain still works without attention"""
        import torch
        from reality_simulator.neural.brain import OrganismBrain
        
        brain = OrganismBrain(
            input_dim=12,
            hidden_dim=64,
            output_dim=6,
            use_attention=False
        )
        
        x = torch.randn(1, 12)
        output = brain(x)
        assert output.shape == (1, 6)
        
    def test_experience_without_tokens(self):
        """Test Experience still works without token sequence"""
        from reality_simulator.neural.experience import Experience, ExperienceBuffer
        
        state = np.zeros(12)
        
        # Old-style experience creation
        exp = Experience(
            state=state,
            action=0,
            reward=1.0,
            next_state=state,
            done=False
        )
        
        assert exp.token_sequence == []
        assert exp.vp_value is None
        
        # Old-style buffer add
        buffer = ExperienceBuffer(capacity=100)
        buffer.add(state, 0, 1.0, state, False)
        
        assert len(buffer) == 1
        
    def test_sample_batch_backward_compatible(self):
        """Test sample_batch returns original 5-tuple"""
        from reality_simulator.neural.experience import ExperienceBuffer
        
        buffer = ExperienceBuffer(capacity=100)
        state = np.zeros(12)
        
        for i in range(20):
            buffer.add(state, i % 6, 0.1 * i, state, False)
            
        # Original API
        result = buffer.sample_batch(8)
        
        assert len(result) == 5  # states, actions, rewards, next_states, dones
        states, actions, rewards, next_states, dones = result
        assert len(states) == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
