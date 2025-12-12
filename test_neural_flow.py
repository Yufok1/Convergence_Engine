"""
Test script to verify neural organism training flow.

Verifies that:
1. Organisms' decide_action is called during simulation
2. Experiences accumulate in the buffer
3. Epsilon decays over time
4. Training produces non-None loss when buffer is sufficient
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_neural_flow():
    """Test the neural training flow."""
    print("=" * 60)
    print("NEURAL TRAINING FLOW TEST")
    print("=" * 60)
    
    # Load config
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Ensure neural is enabled
    if not config.get('neural', {}).get('enabled', False):
        print("ERROR: Neural system not enabled in config.json")
        return False
    
    print(f"Neural config: batch_size={config['neural']['training'].get('batch_size', 32)}")
    print(f"              epsilon_start={config['neural']['training'].get('epsilon_start', 0.8)}")
    print(f"              epsilon_decay={config['neural']['training'].get('epsilon_decay', 0.99)}")
    
    # Import neural components
    try:
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.neural.trainer import NeuralTrainer
        from reality_simulator.evolution_engine import Genotype
        import numpy as np
        print("✓ Neural imports successful")
    except ImportError as e:
        print(f"ERROR: Failed to import neural components: {e}")
        return False
    
    # Create test organisms
    print("\n--- Creating test organisms ---")
    organisms = {}
    for i in range(5):
        genotype = Genotype(genes=np.random.randint(0, 2, 32).astype(np.uint8))
        org = NeuralOrganism(genotype=genotype, config=config)
        org_id = f"org_{i}"
        org.species_id = org_id
        organisms[org_id] = org
        print(f"  Created {org_id}: brain={'present' if org.brain else 'None'}, epsilon={org.epsilon:.4f}")
    
    # Create trainer
    trainer = NeuralTrainer(config.get('neural', {}))
    
    # Simulate several steps
    print("\n--- Simulating decision steps ---")
    batch_size = config['neural']['training'].get('batch_size', 32)
    steps_needed = batch_size + 10  # Need more steps than batch_size
    
    for step in range(steps_needed):
        network_state = {
            'generation': step,
            'organism_count': len(organisms),
            'connection_count': step * 2,
            'modularity': 0.5,
            'clustering_coefficient': 0.3,
            'max_connections_per_organism': 5,
            'resource_pool': 200.0,
        }
        
        for org_id, org in organisms.items():
            if org.brain is not None:
                local_env = {
                    'resources': np.random.random(),
                    'neighbors': np.random.randint(0, 5),
                }
                # This should:
                # 1. Store prev_state/prev_action
                # 2. Decay epsilon
                action = org.decide_action(
                    local_env=local_env,
                    network_state=network_state,
                    breath_state=None
                )
        
        # Train step
        loss = trainer.train_step(
            organisms=organisms,
            network_state=network_state,
            breath_state=None
        )
        
        if step % 20 == 0 or loss is not None:
            sample_org = list(organisms.values())[0]
            buffer_len = len(sample_org.experience_buffer) if sample_org.experience_buffer else 0
            print(f"  Step {step:3d}: epsilon={sample_org.epsilon:.4f}, buffer={buffer_len:3d}, loss={loss}")
    
    # Verify results
    print("\n--- Final State ---")
    sample_org = list(organisms.values())[0]
    initial_epsilon = config['neural']['training'].get('epsilon_start', 0.8)
    
    results = {
        'epsilon_decayed': sample_org.epsilon < initial_epsilon,
        'buffer_accumulated': len(sample_org.experience_buffer) > 0 if sample_org.experience_buffer else False,
        'loss_computed': trainer.total_loss > 0,
    }
    
    print(f"  Initial epsilon: {initial_epsilon}")
    print(f"  Final epsilon: {sample_org.epsilon:.4f}")
    print(f"  Buffer size: {len(sample_org.experience_buffer) if sample_org.experience_buffer else 0}")
    print(f"  Training steps: {trainer.training_step_count}")
    print(f"  Total loss accumulated: {trainer.total_loss:.6f}")
    
    print("\n--- Verification ---")
    all_passed = True
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("NEURAL TRAINING FLOW: ALL CHECKS PASSED ✓")
    else:
        print("NEURAL TRAINING FLOW: SOME CHECKS FAILED ✗")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    success = test_neural_flow()
    sys.exit(0 if success else 1)
