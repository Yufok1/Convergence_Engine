#!/usr/bin/env python
"""
Debug script to verify experience buffer is working.
Directly tests the neural organism experience collection flow.
"""
import json
import sys
import numpy as np

# Add project to path
sys.path.insert(0, 'D:/end-GAME/butterfly')

def main():
    # Load config
    with open('D:/end-GAME/butterfly/config.json', 'r') as f:
        config = json.load(f)
    
    print("=== CONFIG CHECK ===")
    neural_cfg = config.get('neural', {})
    print(f"neural.enabled: {neural_cfg.get('enabled')}")
    print(f"neural.training.batch_size: {neural_cfg.get('training', {}).get('batch_size')}")
    print(f"neural.training.memory_size: {neural_cfg.get('training', {}).get('memory_size')}")
    
    # Check PyTorch
    print("\n=== PYTORCH CHECK ===")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("PyTorch NOT AVAILABLE!")
        return
    
    # Import neural components
    print("\n=== IMPORT CHECK ===")
    from reality_simulator.neural.neural_organism import NeuralOrganism
    from reality_simulator.neural.experience import ExperienceBuffer
    from reality_simulator.evolution_engine import Genotype
    print("Imports successful")
    
    # Create test organism
    print("\n=== CREATE TEST ORGANISM ===")
    # NeuralOrganism expects Genotype object
    genotype = Genotype(
        color_genes=[0.5, 0.5, 0.5],
        size_gene=0.5,
        speed_gene=0.5,
        cooperation_gene=0.5,
        metabolism_gene=0.5,
        mutation_rate=0.01
    )
    org = NeuralOrganism(
        genotype=genotype,
        config=config
    )
    print(f"Organism created: {org.species_id}")
    print(f"brain is None: {org.brain is None}")
    print(f"experience_buffer is None: {org.experience_buffer is None}")
    
    if org.brain is not None:
        device = next(org.brain.parameters()).device
        print(f"brain device: {device}")
    
    if org.experience_buffer is not None:
        print(f"buffer capacity: {org.experience_buffer.capacity}")
        print(f"buffer size BEFORE: {len(org.experience_buffer)}")
    
    # Test decide_action flow
    print("\n=== TEST DECIDE_ACTION ===")
    network_state = {
        'generation': 1,
        'organism_count': 10,
        'connection_count': 5,
        'modularity': 0.3,
        'clustering_coefficient': 0.4,
        'max_connections_per_organism': 5,
        'resource_pool': 100.0,
        'vp_components': {
            'trait_divergence': 0.1,
            'network_coherence': 0.5,
            'quantum_entropy': 0.2,
            'evolution_pressure': 0.3,
            'phase_mismatch': 0.1,
        }
    }
    local_env = {'resources': 0.5, 'neighbors': 3}
    
    # Make a decision - this should set prev_state and prev_action
    action = org.decide_action(local_env=local_env, network_state=network_state, breath_state=None)
    print(f"Action taken: {action}")
    print(f"prev_state is None: {org.prev_state is None}")
    print(f"prev_action is None: {org.prev_action is None}")
    if org.prev_state is not None:
        print(f"prev_state shape: {org.prev_state.shape}")
        print(f"prev_state dtype: {org.prev_state.dtype}")
    
    # Now test record_experience
    print("\n=== TEST RECORD_EXPERIENCE ===")
    next_state = org.get_state_features(local_env=local_env, network_state=network_state)
    print(f"next_state shape: {next_state.shape}")
    print(f"next_state dtype: {next_state.dtype}")
    
    # Record experience
    org.record_experience(reward=0.5, next_state=next_state, done=False)
    print(f"buffer size AFTER: {len(org.experience_buffer)}")
    
    # Multiple experiences
    print("\n=== TEST MULTIPLE EXPERIENCES ===")
    for i in range(10):
        action = org.decide_action(local_env=local_env, network_state=network_state, breath_state=None)
        next_state = org.get_state_features(local_env=local_env, network_state=network_state)
        org.record_experience(reward=np.random.random(), next_state=next_state, done=False)
    
    print(f"buffer size after 10 more: {len(org.experience_buffer)}")
    print(f"epsilon: {org.epsilon}")
    
    print("\n=== SUCCESS ===")
    print("Experience buffer is working correctly!")

if __name__ == '__main__':
    main()
