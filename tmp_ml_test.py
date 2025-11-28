from reality_simulator.main import RealitySimulator
from reality_simulator.evolution_engine import Genotype
from reality_simulator.neural.neural_organism import NeuralOrganism
import numpy as np

rs = RealitySimulator()
rs.initialize_simulation()
rs.event_emitter = lambda e: print('EVENT:', getattr(e, 'event_type', 'unknown'), getattr(e, 'data', {}))
net = rs.components['network']

# Wire the ML event emitter
net.ml_event_emitter = rs.event_emitter

# Clear existing organisms and add diverse ones to trigger clustering
net.organisms.clear()
net.network_graph.clear()

# Create diverse organisms with different trait patterns
for i in range(20):
    genes = np.random.randint(0, 2, 32, dtype=np.uint8)
    genotype = Genotype(genes=genes, generation=0)
    
    # Create organism with varied traits
    org = NeuralOrganism(genotype=genotype, config=rs.config['neural'])
    
    # Manually set diverse traits to trigger clustering
    if i < 5:
        # Group 1: High trait_0, low trait_1
        org.phenotype.traits = {f'trait_{j}': (0.8 if j == 0 else 0.2) for j in range(10)}
    elif i < 10:
        # Group 2: Low trait_0, high trait_1
        org.phenotype.traits = {f'trait_{j}': (0.2 if j == 0 else 0.8) for j in range(10)}
    else:
        # Group 3: Medium traits
        org.phenotype.traits = {f'trait_{j}': 0.5 for j in range(10)}
    
    org.fitness = np.random.uniform(0.5, 0.95)
    net.add_organism(org)

print(f"Added {len(net.organisms)} diverse organisms")

# Configure ML analyzer
ml_config = {
    "enabled": True,
    "clustering": {"enabled": True, "algorithm": "hdbscan", "min_cluster_size": 3},
    "anomaly_detection": {"enabled": True, "algorithm": "isolation_forest", "contamination": 0.1},
    "dimensionality_reduction": {"enabled": True, "algorithm": "pca", "n_components": 2}
}
net.configure_ml_analyzer(ml_config)

# Run ML analysis
print("Running ML analysis...")
analysis = net.run_ml_analysis(force=True)
print("Analysis result:", analysis)

# Run again to see if events are emitted on changes
print("Running ML analysis again...")
analysis2 = net.run_ml_analysis(force=True)
print("Analysis result 2:", analysis2)
