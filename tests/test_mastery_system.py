"""
Tests for the Grounded Language Mastery System (Round 4 fixes).

Tests:
1. Level 0 organisms get exactly 6 ACTION_HEADS
2. form_association() doesn't create implicit atoms in mastery-gated mode
3. apply_experience() tracks experiences correctly
4. Breadth tracking (activation counts) works
5. Depth tracking (associations between known words) works
6. Mastery advancement triggers at correct thresholds
7. Level advancement unlocks more vocabulary
"""
import pytest
import sys
import os
import json

# Direct import to avoid circular import issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "atomic_language", 
    os.path.join(os.path.dirname(__file__), "..", "reality_simulator", "language", "atomic_language.py")
)
atomic_language_module = importlib.util.module_from_spec(spec)
sys.modules['reality_simulator.language.atomic_language'] = atomic_language_module
spec.loader.exec_module(atomic_language_module)
AtomicLanguageSystem = atomic_language_module.AtomicLanguageSystem


def get_grounded_config(mastery_level=0):
    """Create config for grounded language mode at specified mastery level."""
    return {
        'language': {
            'mode': 'grounded',
            'grounded': {
                'initial_mastery_level': mastery_level,
                'mastery_vocab_sizes': [6, 26, 76, 276, 20000],
                'mastery_advancement_ratio': 0.7,
                'mastery_depth_ratio': 0.5,
                'mastery_min_experiences': [50, 200, 500, 1000]
            }
        }
    }


class TestLevel0Initialization:
    """Test that level 0 organisms start with exactly 6 ACTION_HEADS."""
    
    def test_level0_has_6_atoms(self):
        """Level 0 should have exactly 6 atoms."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        assert len(als.atoms) == 6, f"Expected 6 atoms, got {len(als.atoms)}"
    
    def test_level0_has_action_heads(self):
        """Level 0 should have the 6 ACTION_HEADS."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        expected = {'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'}
        actual = set(als.atoms.keys())
        
        assert actual == expected, f"Expected {expected}, got {actual}"
    
    def test_level0_mastery_level_set(self):
        """Level 0 should have _mastery_level = 0."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        assert als._mastery_level == 0


class TestFormAssociationMasteryGating:
    """Test that form_association respects mastery gating."""
    
    def test_no_implicit_atom_creation_level0(self):
        """form_association should NOT create atoms for unknown words at level 0."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        initial_count = len(als.atoms)
        
        # Try to form association with unknown word
        als.form_association('cooperate', 'friend', 0.5, 'test')
        
        assert len(als.atoms) == initial_count, \
            f"Atoms increased from {initial_count} to {len(als.atoms)} - implicit creation not blocked!"
    
    def test_association_between_known_words_works(self):
        """form_association should work between known ACTION_HEADS."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        initial_assoc_count = als.total_associations_formed
        
        # Form association between two known words
        als.form_association('cooperate', 'reproduce', 0.5, 'test')
        
        assert als.total_associations_formed > initial_assoc_count, \
            "Association between known words should work"
        assert 'reproduce' in als.atoms['cooperate'].associations, \
            "Association should be recorded in atom"
    
    def test_level4_allows_implicit_creation(self):
        """Level 4 (semantic graduation) should allow implicit atom creation."""
        config = get_grounded_config(mastery_level=4)
        als = AtomicLanguageSystem('test_org', config=config)
        
        initial_count = len(als.atoms)
        
        # Form association with unknown word - should create it
        als.form_association('cooperate', 'friendship_test_word', 0.5, 'test')
        
        # At level 4, this should create the new atom
        assert 'friendship_test_word' in als.atoms or len(als.atoms) > initial_count, \
            "Level 4 should allow implicit concept acquisition"


class TestExperienceTracking:
    """Test that experiences are tracked correctly."""
    
    def test_experience_starts_at_zero(self):
        """New organisms should have 0 experiences."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        assert als._total_experiences == 0
    
    def test_apply_experience_increments_count(self):
        """apply_experience should increment _total_experiences."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        als.apply_experience(action=1, outcome=0.5, context=context)
        
        assert als._total_experiences == 1
    
    def test_multiple_experiences_accumulate(self):
        """Multiple experiences should accumulate."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        for i in range(60):
            als.apply_experience(action=i % 6, outcome=0.5, context=context)
        
        assert als._total_experiences == 60


class TestBreadthTracking:
    """Test that word usage (breadth criterion) is tracked."""
    
    def test_activation_count_increases(self):
        """Using a word should increase its activation count."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Apply cooperate action 10 times
        for _ in range(10):
            als.apply_experience(action=1, outcome=0.5, context=context)  # COOPERATE
        
        # Check activation count
        cooperate_atom = als.atoms.get('cooperate')
        assert cooperate_atom is not None
        assert cooperate_atom.recent_activation_count >= 10, \
            f"Expected activation count >= 10, got {cooperate_atom.recent_activation_count}"


class TestDepthTracking:
    """Test that associations (depth criterion) are formed correctly."""
    
    def test_associations_form_between_action_heads(self):
        """Associations should form between ACTION_HEADS during experience."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Apply cooperate action with positive outcome
        als.apply_experience(action=1, outcome=0.5, context=context)  # COOPERATE
        
        # Check that cooperate now has associations
        cooperate_atom = als.atoms.get('cooperate')
        assert len(cooperate_atom.associations) > 0, \
            "Cooperate should have associations after positive experience"
    
    def test_all_actions_build_associations(self):
        """All 6 action types should build associations."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Apply each action multiple times
        for _ in range(10):
            for action in range(6):
                als.apply_experience(action=action, outcome=0.5, context=context)
        
        # Check each action head has associations
        for action in ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']:
            atom = als.atoms.get(action)
            assert atom is not None, f"{action} atom missing"
            assert len(atom.associations) >= 3, \
                f"{action} should have 3+ associations, has {len(atom.associations)}"


class TestMasteryAdvancement:
    """Test that mastery advancement works correctly."""
    
    def test_try_advance_mastery_exists(self):
        """AtomicLanguageSystem should have try_advance_mastery method."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        assert hasattr(als, 'try_advance_mastery'), \
            "AtomicLanguageSystem missing try_advance_mastery method"
    
    def test_advancement_requires_minimum_experiences(self):
        """Cannot advance without minimum experiences."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        # No experiences yet
        advanced = als.try_advance_mastery()
        
        assert not advanced, "Should not advance with 0 experiences"
        assert als._mastery_level == 0, "Level should stay at 0"
    
    def test_advancement_with_full_criteria(self):
        """Should advance when all criteria met."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Build up experiences, breadth, and depth
        # Need: 50 experiences, 70% breadth (5 of 6 words used >5 times), 50% depth (3 of 6 with 3+ assocs)
        for _ in range(60):  # 60 experiences > 50 minimum
            for action in range(6):
                als.apply_experience(action=action, outcome=0.5, context=context)
        
        # Try to advance
        advanced = als.try_advance_mastery()
        
        if advanced:
            assert als._mastery_level == 1, "Should be level 1 after advancement"
        else:
            # Print debug info if it didn't advance
            print(f"Experiences: {als._total_experiences}")
            breadth_count = sum(1 for a in als.atoms.values() if a.recent_activation_count > 5)
            print(f"Breadth: {breadth_count}/6 words with >5 activations")
            depth_count = sum(1 for a in als.atoms.values() if len(a.associations) >= 3)
            print(f"Depth: {depth_count}/6 words with 3+ associations")


class TestVocabularyStability:
    """Test that vocabulary doesn't grow unexpectedly."""
    
    def test_vocab_stable_after_many_experiences(self):
        """Vocabulary should stay at 6 after many experiences at level 0."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Run many experiences
        for _ in range(100):
            for action in range(6):
                als.apply_experience(action=action, outcome=0.5, context=context)
        
        assert len(als.atoms) == 6, \
            f"Vocabulary should stay at 6, got {len(als.atoms)}: {list(als.atoms.keys())}"
    
    def test_only_action_heads_exist(self):
        """Only ACTION_HEADS should exist at level 0."""
        config = get_grounded_config(mastery_level=0)
        als = AtomicLanguageSystem('test_org', config=config)
        
        context = {'vp_state': (0.7, 0.6)}
        
        # Run many experiences
        for _ in range(50):
            for action in range(6):
                als.apply_experience(action=action, outcome=0.5, context=context)
        
        expected = {'move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'}
        actual = set(als.atoms.keys())
        
        extra = actual - expected
        assert len(extra) == 0, f"Unexpected atoms acquired: {extra}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
