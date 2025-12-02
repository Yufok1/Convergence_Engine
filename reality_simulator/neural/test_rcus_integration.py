"""
RCUS Integration Test
=====================

Tests the complete RCUS (Recursive Conceptual Understanding System) integration
with the existing Convergence Engine neural system.

Tests:
1. ConceptSystem creation and axiom grounding
2. OrganismBrain with concept head
3. NeuralTrainer with concept loss
4. ConceptLanguageBridge for vocabulary connection
5. Full training loop with triple-loss
"""

import sys
import os
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Check PyTorch
try:
    import torch
    PYTORCH_AVAILABLE = True
    print(f"✅ PyTorch available (version {torch.__version__})")
    print(f"   Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
except ImportError:
    PYTORCH_AVAILABLE = False
    print("❌ PyTorch not available")
    sys.exit(1)


def test_concept_system():
    """Test ConceptSystem creation and basic operations."""
    print("\n" + "=" * 60)
    print("TEST 1: ConceptSystem")
    print("=" * 60)
    
    from reality_simulator.neural.concept_system import (
        ConceptSystem, AXIOM_DEFINITIONS, KEY_COMPOSITIONS
    )
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Create system
    concept_system = ConceptSystem(state_dim=24, embed_dim=64, device=device)
    print(f"✅ Created ConceptSystem with {len(AXIOM_DEFINITIONS)} axioms")
    
    # Test axiom embedding
    state = torch.randn(24, device=device)
    self_embed = concept_system.get_axiom_embedding('SELF', state)
    other_embed = concept_system.get_axiom_embedding('OTHER', state)
    print(f"✅ SELF embedding shape: {self_embed.shape}")
    print(f"✅ OTHER embedding shape: {other_embed.shape}")
    
    # Test composition
    composed, name = concept_system.compose('SELF', 'WITH', 'OTHER', state)
    print(f"✅ Composed '{name}' shape: {composed.shape}")
    
    # Test value prediction
    value = concept_system.predict_value(composed)
    print(f"✅ Predicted value: {value.item():.4f}")
    
    # Test all key compositions
    print(f"\nKey compositions ({len(KEY_COMPOSITIONS)}):")
    for axiom_a, op, axiom_b in KEY_COMPOSITIONS:
        comp, name = concept_system.compose(axiom_a, op, axiom_b, state)
        val = concept_system.predict_value(comp)
        print(f"   {name}: value = {val.item():.4f}")
    
    return concept_system


def test_organism_brain():
    """Test OrganismBrain with concept head."""
    print("\n" + "=" * 60)
    print("TEST 2: OrganismBrain with ConceptHead")
    print("=" * 60)
    
    from reality_simulator.neural.brain import OrganismBrain
    
    # Create brain with concept head
    brain = OrganismBrain(
        input_dim=24,
        hidden_dim=64,
        output_dim=6,
        use_language_head=True,
        vocab_size=1000,
        use_concept_head=True,
        num_key_compositions=5
    )
    
    total_params = sum(p.numel() for p in brain.parameters())
    print(f"✅ Created OrganismBrain with {total_params:,} parameters")
    print(f"   use_language_head: {brain.use_language_head}")
    print(f"   use_concept_head: {brain.use_concept_head}")
    
    # Test forward pass with all outputs
    state = torch.randn(4, 24)  # batch of 4
    
    # Standard forward
    action_probs = brain(state)
    print(f"✅ Action probs shape: {action_probs.shape}")
    
    # With language output
    action_probs, lang_logits = brain(state, return_language_logits=True)
    print(f"✅ Language logits shape: {lang_logits.shape}")
    
    # With concept output
    action_probs, concept_out = brain(state, return_concept_outputs=True)
    print(f"✅ Concept output keys: {list(concept_out.keys())}")
    print(f"   axiom_relevance: {concept_out['axiom_relevance'].shape}")
    print(f"   composition_value: {concept_out['composition_value'].shape}")
    
    # With all outputs
    action_probs, lang_logits, concept_out = brain(
        state, return_language_logits=True, return_concept_outputs=True
    )
    print(f"✅ All three outputs returned successfully")
    
    return brain


def test_neural_trainer():
    """Test NeuralTrainer with concept loss."""
    print("\n" + "=" * 60)
    print("TEST 3: NeuralTrainer with Concept Loss")
    print("=" * 60)
    
    from reality_simulator.neural.trainer import NeuralTrainer
    
    # Config with concept system enabled
    config = {
        'device': 'cpu',
        'training': {
            'batch_size': 16,
            'learning_rate': 0.001,
            'gamma': 0.99,
            'update_frequency': 1,
        },
        'brain': {
            'input_dim': 24,
            'hidden_dim': 64,
            'output_dim': 6,
        },
        'language_model': {
            'enabled': True,
            'rl_loss_weight': 0.8,
            'language_loss_weight': 0.1,
        },
        'concept_system': {
            'enabled': True,
            'embed_dim': 64,
            'concept_loss_weight': 0.1,
            'num_key_compositions': 5,
        },
    }
    
    trainer = NeuralTrainer(config)
    
    print(f"✅ Created NeuralTrainer")
    print(f"   concept_system_enabled: {trainer.concept_system_enabled}")
    print(f"   concept_loss_weight: {trainer.concept_loss_weight}")
    
    if trainer.concept_system is not None:
        print(f"   concept_system axioms: {len(trainer.concept_system.axiom_names)}")
    
    # Test training stats
    stats = trainer.get_training_stats()
    print(f"✅ Training stats keys: {list(stats.keys())}")
    print(f"   concept_system_enabled: {stats.get('concept_system_enabled')}")
    
    return trainer


def test_language_bridge():
    """Test ConceptLanguageBridge."""
    print("\n" + "=" * 60)
    print("TEST 4: ConceptLanguageBridge")
    print("=" * 60)
    
    from reality_simulator.neural.concept_system import (
        ConceptSystem, ConceptLanguageBridge
    )
    
    device = 'cpu'
    concept_system = ConceptSystem(state_dim=24, embed_dim=64, device=device)
    bridge = ConceptLanguageBridge(concept_system)
    
    print(f"✅ Created ConceptLanguageBridge")
    print(f"   Axiom vocabulary entries: {len(bridge.AXIOM_VOCABULARY)}")
    print(f"   Word-to-axiom mappings: {len(bridge.word_to_axiom)}")
    
    # Test concept to phrase
    phrase = bridge.concept_to_phrase('SELF_WITH_OTHER')
    print(f"✅ 'SELF_WITH_OTHER' → '{phrase}'")
    
    phrase = bridge.concept_to_phrase('DO_CAUSE_GOOD')
    print(f"✅ 'DO_CAUSE_GOOD' → '{phrase}'")
    
    # Test phrase to concept
    concept = bridge.phrase_to_concept('self with other')
    print(f"✅ 'self with other' → {concept}")
    
    concept = bridge.phrase_to_concept('action causes success')
    print(f"✅ 'action causes success' → {concept}")
    
    # Test explanation
    explanation = bridge.explain_concept('DO_CAUSE_GOOD')
    print(f"✅ Explanation: '{explanation}'")
    
    # Test grounded words
    state = torch.randn(24)
    state[0] = 0.9  # High fitness → SELF, GOOD grounded
    words = bridge.get_grounded_axiom_words(state, threshold=0.3)
    print(f"✅ Grounded words (high fitness state): {words[:10]}...")
    
    return bridge


def test_compute_concept_loss():
    """Test concept loss computation."""
    print("\n" + "=" * 60)
    print("TEST 5: Concept Loss Computation")
    print("=" * 60)
    
    from reality_simulator.neural.concept_system import (
        ConceptSystem, compute_concept_loss, KEY_COMPOSITIONS
    )
    
    device = 'cpu'
    concept_system = ConceptSystem(state_dim=24, embed_dim=64, device=device)
    
    # Batch of states and rewards
    states = torch.randn(8, 24)
    rewards = torch.randn(8)
    
    # Compute loss
    loss = compute_concept_loss(concept_system, states, rewards, KEY_COMPOSITIONS)
    print(f"✅ Concept loss: {loss.item():.6f}")
    
    # Check utility was updated
    useful = concept_system.get_useful_concepts(top_k=5)
    print(f"✅ Useful concepts after training:")
    for name, utility, count in useful:
        print(f"   {name}: utility={utility:.4f}, count={count}")
    
    # Test backward pass
    loss.backward()
    print(f"✅ Backward pass successful")
    
    # Check gradients exist
    grad_exists = any(p.grad is not None for p in concept_system.parameters())
    print(f"✅ Gradients computed: {grad_exists}")
    
    return loss


def test_full_training_loop():
    """Test full training loop with triple-loss."""
    print("\n" + "=" * 60)
    print("TEST 6: Full Training Loop (Triple-Loss)")
    print("=" * 60)
    
    from reality_simulator.neural.brain import OrganismBrain
    from reality_simulator.neural.concept_system import (
        ConceptSystem, compute_concept_loss, KEY_COMPOSITIONS
    )
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Create brain with all heads
    brain = OrganismBrain(
        input_dim=24,
        hidden_dim=64,
        output_dim=6,
        use_language_head=True,
        vocab_size=100,
        use_concept_head=True,
        num_key_compositions=5
    ).to(device)
    
    # Create concept system
    concept_system = ConceptSystem(state_dim=24, embed_dim=64, device=device)
    
    # Optimizer
    optimizer = torch.optim.Adam(
        list(brain.parameters()) + list(concept_system.parameters()),
        lr=0.001
    )
    
    print(f"Training on {device}...")
    
    # Training loop
    losses = []
    for episode in range(50):
        # Generate batch
        states = torch.randn(16, 24, device=device)
        actions = torch.randint(0, 6, (16,), device=device)
        rewards = torch.randn(16, device=device)
        next_states = states + torch.randn(16, 24, device=device) * 0.1
        
        # Forward pass
        brain.train()
        q_values, lang_logits, concept_out = brain(
            states, return_language_logits=True, return_concept_outputs=True
        )
        
        # 1. RL Loss (DQN-style)
        q_value = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = brain(next_states).max(1)[0]
        target_q = rewards + 0.99 * next_q
        rl_loss = torch.nn.functional.mse_loss(q_value, target_q)
        
        # 2. Language Loss (simplified)
        lang_loss = torch.nn.functional.cross_entropy(
            lang_logits, torch.randint(0, 100, (16,), device=device)
        )
        
        # 3. Concept Loss
        concept_loss = compute_concept_loss(concept_system, states, rewards, KEY_COMPOSITIONS)
        
        # Combined loss (alpha=0.8, beta=0.1, gamma=0.1)
        total_loss = 0.8 * rl_loss + 0.1 * lang_loss + 0.1 * concept_loss
        
        # Backward
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()
        
        losses.append(total_loss.item())
        
        if episode % 10 == 0:
            print(f"  Episode {episode}: loss={total_loss.item():.4f} "
                  f"(rl={rl_loss.item():.4f}, lang={lang_loss.item():.4f}, "
                  f"concept={concept_loss.item():.4f})")
    
    print(f"✅ Training complete")
    print(f"   Initial loss: {losses[0]:.4f}")
    print(f"   Final loss: {losses[-1]:.4f}")
    print(f"   Loss reduction: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")
    
    # Check useful concepts
    useful = concept_system.get_useful_concepts(top_k=5)
    print(f"✅ Top useful concepts after training:")
    for name, utility, count in useful:
        print(f"   {name}: utility={utility:.4f}")
    
    return losses


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("RCUS INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("ConceptSystem", test_concept_system),
        ("OrganismBrain with ConceptHead", test_organism_brain),
        ("NeuralTrainer with Concept Loss", test_neural_trainer),
        ("ConceptLanguageBridge", test_language_bridge),
        ("Concept Loss Computation", test_compute_concept_loss),
        ("Full Training Loop", test_full_training_loop),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            test_fn()
            results.append((name, "PASS"))
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"FAIL: {e}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)
    
    for name, result in results:
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {name}: {result}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - RCUS Integration Complete!")
        return 0
    else:
        print("\n⚠️  Some tests failed - review errors above")
        return 1


if __name__ == "__main__":
    exit(main())
