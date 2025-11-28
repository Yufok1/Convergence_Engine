from reality_simulator.main import RealitySimulator
import numpy as np

rs=RealitySimulator()
rs.initialize_simulation()
rs.event_emitter=lambda e: print('EVENT:', getattr(e,'event_type','unknown'), getattr(e,'data',{}))
rs.neural_trainer.event_emitter = rs.event_emitter
net = rs.components['network']
# Fill experience buffer for each neural organism
for org in net.organisms.values():
    if hasattr(org,'experience_buffer') and org.experience_buffer is not None:
        for _ in range(150):
            state = np.random.rand(12).astype(np.float32)
            action = np.random.randint(0,6)
            reward = np.random.randn()
            next_state = np.random.rand(12).astype(np.float32)
            org.experience_buffer.add(state, action, reward, next_state, False)

# Trigger a training step
loss = rs.neural_trainer.train_step(organisms=net.organisms, network_state={'generation':1,'organism_count':len(net.organisms),'connection_count':len(net.connections),'modularity':0.5,'clustering_coefficient':0.5,'max_connections_per_organism':10,'resource_pool':200.0}, breath_state=None)
print('Loss:', loss)
