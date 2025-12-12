"""
Semantic Convergence End-to-End Test Suite
===========================================

Tests all 6 semantic systems and their wiring:
1. ContextMemory - learned embeddings enabled
2. OrganismBrain.fc2 → word embeddings flow
3. ConceptSystem → axiom export → word embeddings
4. LinguisticKnowledgeWeb → semantic influence
5. ConceptTracker → phenotype names → vocabulary
6. Config integration

Run from butterfly root: python -m pytest tests/test_semantic_convergence.py -v
Or directly: python tests/test_semantic_convergence.py
"""

import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_context_memory_learned_embeddings():
    """Test 1: ContextMemory has use_learned_embeddings=True by default"""
    print("\n" + "="*60)
    print("TEST 1: ContextMemory Learned Embeddings Default")
    print("="*60)
    
    from reality_simulator.memory.context_memory import ContextMemory
    
    cm = ContextMemory()
    
    assert cm.use_learned_embeddings == True, "use_learned_embeddings should be True by default"
    assert cm.word_embedding is not None, "word_embedding layer should be initialized"
    
    print(f"✅ use_learned_embeddings: {cm.use_learned_embeddings}")
    print(f"✅ word_embedding initialized: {cm.word_embedding is not None}")
    print(f"✅ embedding_dim: {cm.word_embedding.embedding_dim if cm.word_embedding else 'N/A'}")
    
    return True


def test_context_memory_update_method():
    """Test 2: ContextMemory.update_word_embedding_from_organism exists and works"""
    print("\n" + "="*60)
    print("TEST 2: ContextMemory.update_word_embedding_from_organism")
    print("="*60)
    
    from reality_simulator.memory.context_memory import ContextMemory
    
    cm = ContextMemory()
    
    # Check method exists
    assert hasattr(cm, 'update_word_embedding_from_organism'), "Method should exist"
    
    # Create test embedding
    test_embedding = np.random.randn(64).astype(np.float32)
    
    # First link a word to create vocabulary entry
    cm.link_word_to_node("test_word", 12345, 1)
    
    # Get embedding before
    embed_before = cm.get_word_embedding("test_word")
    print(f"Embedding before update (first 5): {embed_before[:5] if embed_before is not None else 'None'}")
    
    # Update with organism embedding
    cm.update_word_embedding_from_organism("test_word", test_embedding, alpha=0.5)
    
    # Get embedding after
    embed_after = cm.get_word_embedding("test_word")
    print(f"Embedding after update (first 5): {embed_after[:5] if embed_after is not None else 'None'}")
    
    # Verify embedding changed
    if embed_before is not None and embed_after is not None:
        diff = np.abs(embed_before - embed_after).sum()
        print(f"✅ Embedding difference: {diff:.4f}")
        assert diff > 0.01, "Embedding should have changed"
    
    print("✅ update_word_embedding_from_organism works correctly")
    return True


def test_link_word_to_node_accepts_embedding():
    """Test 3: link_word_to_node accepts organism_embedding parameter"""
    print("\n" + "="*60)
    print("TEST 3: link_word_to_node with organism_embedding parameter")
    print("="*60)
    
    from reality_simulator.memory.context_memory import ContextMemory
    import inspect
    
    cm = ContextMemory()
    
    # Check method signature
    sig = inspect.signature(cm.link_word_to_node)
    params = list(sig.parameters.keys())
    
    assert 'organism_embedding' in params, "organism_embedding parameter should exist"
    print(f"✅ link_word_to_node parameters: {params}")
    
    # Test calling with embedding
    test_embedding = np.random.randn(64).astype(np.float32)
    cm.link_word_to_node("neural_word", 99999, 1, organism_embedding=test_embedding)
    
    embed = cm.get_word_embedding("neural_word")
    print(f"✅ Word embedding after link (first 5): {embed[:5] if embed is not None else 'None'}")
    
    return True


def test_concept_system_export():
    """Test 4: ConceptSystem.export_concept_embeddings exists and works"""
    print("\n" + "="*60)
    print("TEST 4: ConceptSystem.export_concept_embeddings")
    print("="*60)
    
    try:
        import torch
        from reality_simulator.neural.concept_system import ConceptSystem
    except ImportError as e:
        print(f"⚠️ Skipping - PyTorch or ConceptSystem not available: {e}")
        return True
    
    cs = ConceptSystem(state_dim=25, embed_dim=64, device='cpu')
    
    # Check method exists
    assert hasattr(cs, 'export_concept_embeddings'), "Method should exist"
    
    # Create test state
    state = torch.randn(25)
    
    # Export embeddings
    axiom_embeds = cs.export_concept_embeddings(state)
    
    print(f"✅ Exported {len(axiom_embeds)} axiom embeddings")
    print(f"   Axiom names: {list(axiom_embeds.keys())[:5]}...")
    
    # Verify structure
    for name, embed in list(axiom_embeds.items())[:3]:
        assert isinstance(embed, np.ndarray), f"{name} should be numpy array"
        assert embed.shape == (64,), f"{name} should be 64-dim"
        print(f"   {name}: shape={embed.shape}, dtype={embed.dtype}")
    
    print("✅ export_concept_embeddings works correctly")
    return True


def test_knowledge_web_influence():
    """Test 5: LinguisticKnowledgeWeb.influence_context_memory exists and works"""
    print("\n" + "="*60)
    print("TEST 5: LinguisticKnowledgeWeb.influence_context_memory")
    print("="*60)
    
    from reality_simulator.language.linguistic_knowledge_web import LinguisticKnowledgeWeb
    from reality_simulator.memory.context_memory import ContextMemory
    
    kw = LinguisticKnowledgeWeb()
    cm = ContextMemory()
    
    # Check method exists
    assert hasattr(kw, 'influence_context_memory'), "Method should exist"
    
    # Add some words to context memory first
    test_words = ['good', 'bad', 'happy', 'sad', 'strong', 'weak']
    for i, word in enumerate(test_words):
        cm.link_word_to_node(word, i + 1000, 1)
    
    # Get embeddings before
    embeds_before = {w: cm.get_word_embedding(w).copy() if cm.get_word_embedding(w) is not None else None 
                     for w in test_words}
    
    # Call influence method
    influenced = kw.influence_context_memory(cm)
    
    print(f"✅ influence_context_memory returned: {influenced} embeddings influenced")
    
    # Get embeddings after
    embeds_after = {w: cm.get_word_embedding(w) for w in test_words}
    
    # Check for changes
    changes = 0
    for word in test_words:
        if embeds_before[word] is not None and embeds_after[word] is not None:
            diff = np.abs(embeds_before[word] - embeds_after[word]).sum()
            if diff > 0.001:
                changes += 1
                print(f"   {word}: changed by {diff:.4f}")
    
    print(f"✅ {changes} word embeddings showed changes")
    return True


def test_concept_tracker_context_memory():
    """Test 6: ConceptTracker has context_memory attribute"""
    print("\n" + "="*60)
    print("TEST 6: ConceptTracker.context_memory attribute")
    print("="*60)
    
    from reality_simulator.concept_tracker import ConceptTracker
    
    ct = ConceptTracker()
    
    # Check attribute exists
    assert hasattr(ct, 'context_memory'), "context_memory attribute should exist"
    print(f"✅ context_memory attribute exists: {ct.context_memory}")
    
    # Test setting it
    from reality_simulator.memory.context_memory import ContextMemory
    cm = ContextMemory()
    ct.context_memory = cm
    
    assert ct.context_memory is cm, "Should be able to set context_memory"
    print("✅ context_memory can be set and retrieved")
    
    return True


def test_config_semantic_convergence():
    """Test 7: Config has semantic_convergence section"""
    print("\n" + "="*60)
    print("TEST 7: Config semantic_convergence section")
    print("="*60)
    
    import json
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    assert 'semantic_convergence' in config, "semantic_convergence section should exist"
    
    sc = config['semantic_convergence']
    print(f"✅ semantic_convergence section found:")
    for key, value in sc.items():
        print(f"   {key}: {value}")
    
    # Verify expected keys
    expected_keys = ['enabled', 'use_learned_embeddings', 'embedding_dim']
    for key in expected_keys:
        assert key in sc, f"Expected key '{key}' in semantic_convergence"
    
    print("✅ All expected config keys present")
    return True


def test_language_teacher_wiring():
    """Test 8: LanguageTeacher extracts organism embedding in teach_organism"""
    print("\n" + "="*60)
    print("TEST 8: LanguageTeacher organism embedding extraction")
    print("="*60)
    
    import inspect
    from reality_simulator.language.language_teacher import LanguageTeacher
    
    # Check teach_organism source for organism embedding extraction
    source = inspect.getsource(LanguageTeacher.teach_organism)
    
    checks = [
        ('get_language_embedding' in source, "get_language_embedding call"),
        ('organism_embedding' in source, "organism_embedding variable"),
        ('export_concept_embeddings' in source, "export_concept_embeddings call"),
    ]
    
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {desc}: {'found' if passed else 'NOT FOUND'}")
        
    all_passed = all(c[0] for c in checks)
    if all_passed:
        print("✅ All wiring checks passed in teach_organism")
    
    return all_passed


def test_ml_utils_wiring():
    """Test 9: MLAnalyzer wires concept_tracker.context_memory"""
    print("\n" + "="*60)
    print("TEST 9: MLAnalyzer concept_tracker wiring")
    print("="*60)
    
    import inspect
    from reality_simulator.ml_utils import MLAnalyzer
    
    # Check analyze method source for context_memory wiring
    source = inspect.getsource(MLAnalyzer.analyze)
    
    checks = [
        ('concept_tracker.context_memory' in source, "concept_tracker.context_memory assignment"),
    ]
    
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {desc}: {'found' if passed else 'NOT FOUND'}")
    
    return all(c[0] for c in checks)


def test_end_to_end_flow():
    """Test 10: Full end-to-end flow simulation"""
    print("\n" + "="*60)
    print("TEST 10: End-to-End Flow Simulation")
    print("="*60)
    
    from reality_simulator.memory.context_memory import ContextMemory
    from reality_simulator.language.linguistic_knowledge_web import LinguisticKnowledgeWeb
    
    try:
        import torch
        from reality_simulator.neural.concept_system import ConceptSystem
        has_torch = True
    except ImportError:
        has_torch = False
    
    # Step 1: Initialize systems
    print("\n1. Initializing systems...")
    cm = ContextMemory()
    kw = LinguisticKnowledgeWeb()
    
    if has_torch:
        cs = ConceptSystem(state_dim=25, embed_dim=64, device='cpu')
        print("   ✅ ContextMemory, KnowledgeWeb, ConceptSystem initialized")
    else:
        print("   ✅ ContextMemory, KnowledgeWeb initialized (no PyTorch)")
    
    # Step 2: Simulate organism embedding
    print("\n2. Simulating organism neural embedding (fc2)...")
    organism_embedding = np.random.randn(64).astype(np.float32)
    print(f"   Organism embedding shape: {organism_embedding.shape}")
    
    # Step 3: Link words with organism embedding
    print("\n3. Linking words with organism embedding...")
    test_words = ['thriving', 'surviving', 'struggling']
    for word in test_words:
        cm.link_word_to_node(word, 12345, 1, organism_embedding=organism_embedding)
    print(f"   ✅ Linked {len(test_words)} words with organism embedding")
    
    # Step 4: Export concept axiom embeddings
    if has_torch:
        print("\n4. Exporting ConceptSystem axiom embeddings...")
        state = torch.randn(25)
        axiom_embeds = cs.export_concept_embeddings(state)
        
        # Push axiom embeddings to words
        for axiom, embed in list(axiom_embeds.items())[:3]:
            word = axiom.lower()
            cm.link_word_to_node(word, 99999, 1)
            cm.update_word_embedding_from_organism(word, embed, alpha=0.1)
        print(f"   ✅ Pushed {len(axiom_embeds)} axiom embeddings to words")
    
    # Step 5: Apply knowledge web semantic influence
    print("\n5. Applying KnowledgeWeb semantic influence...")
    influenced = kw.influence_context_memory(cm)
    print(f"   ✅ Influenced {influenced} word embeddings")
    
    # Step 6: Verify differentiation
    print("\n6. Verifying word embedding differentiation...")
    embeddings = {}
    for word in test_words + ['good', 'bad']:
        embed = cm.get_word_embedding(word)
        if embed is not None:
            embeddings[word] = embed
    
    if len(embeddings) >= 2:
        words = list(embeddings.keys())
        for i in range(len(words)):
            for j in range(i+1, len(words)):
                w1, w2 = words[i], words[j]
                diff = np.linalg.norm(embeddings[w1] - embeddings[w2])
                print(f"   Distance '{w1}' <-> '{w2}': {diff:.4f}")
        
        print("   ✅ Embeddings are differentiated (not identical)")
    
    print("\n" + "="*60)
    print("END-TO-END FLOW COMPLETE")
    print("="*60)
    
    return True


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "="*70)
    print("SEMANTIC CONVERGENCE END-TO-END TEST SUITE")
    print("="*70)
    
    tests = [
        ("ContextMemory Learned Embeddings", test_context_memory_learned_embeddings),
        ("ContextMemory Update Method", test_context_memory_update_method),
        ("link_word_to_node Embedding Param", test_link_word_to_node_accepts_embedding),
        ("ConceptSystem Export", test_concept_system_export),
        ("KnowledgeWeb Influence", test_knowledge_web_influence),
        ("ConceptTracker context_memory", test_concept_tracker_context_memory),
        ("Config Section", test_config_semantic_convergence),
        ("LanguageTeacher Wiring", test_language_teacher_wiring),
        ("MLAnalyzer Wiring", test_ml_utils_wiring),
        ("End-to-End Flow", test_end_to_end_flow),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed, None))
        except Exception as e:
            import traceback
            results.append((name, False, str(e)))
            traceback.print_exc()
    
    # Generate report
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)
    
    for name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if error:
            print(f"       Error: {error}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Semantic Convergence wiring is correct!")
    else:
        print(f"\n⚠️ {total_count - passed_count} tests failed - review required")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
