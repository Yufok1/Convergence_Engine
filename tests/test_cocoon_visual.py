"""Cocoon drone flight with visualization."""
import sys
sys.path.insert(0, r'D:\cocoons\creative\12-14.300sh')

print("Loading cocoon...")
from cocoon_ensemble_20251214085724 import CocoonAgent
cocoon = CocoonAgent()

print("Loading physics and visualization...")
from reality_simulator.arena.cocoon_drone_bridge import CocoonDronePilot
from reality_simulator.arena.drone_visualizer import plot_trajectory_3d, plot_actions_over_time, plot_flight_stats
import numpy as np
import matplotlib.pyplot as plt

# Create pilot
pilot = CocoonDronePilot(cocoon, team='blue')

# Configure flight
wind = np.array([4.0, 1.0, 0])
duration = 15.0

print(f"\n🛸 Flying for {duration}s with wind: {wind}")
print("="*50)

# Initialize
pilot.fdm.reset(position=np.array([0, 0, 5.0]))
pilot.fdm.set_wind(wind, turbulence=0.3)
pilot.position = np.array([0, 0, 5.0])

dt = 0.02
steps = int(duration / dt)
trajectory = []
actions = []

for step in range(steps):
    result = pilot.step(dt=dt)
    
    if not result.get('alive', True):
        print(f"  CRASHED at t={step*dt:.1f}s")
        break
    
    trajectory.append(result['position'].copy())
    actions.append(result['action'])
    
    if step % 100 == 0:
        pos = result['position']
        action_names = ['MOVE', 'COOP', 'COMP', 'REST', 'REPR', 'ISOL']
        print(f"t={step*dt:4.1f}s | pos=[{pos[0]:5.1f}, {pos[1]:5.1f}, {pos[2]:5.1f}] | action={action_names[result['action']]}")

trajectory = np.array(trajectory)

# Compile stats
stats = {
    'distance_traveled': pilot.distance_traveled,
    'final_battery': pilot.fdm.state.battery_remaining,
    'max_altitude': float(trajectory[:, 2].max()) if len(trajectory) > 0 else 0,
    'min_altitude': float(trajectory[:, 2].min()) if len(trajectory) > 0 else 0,
    'flight_time': pilot.flight_time,
    'crashed': not pilot.alive,
    'actions_histogram': {
        'MOVE': actions.count(0),
        'COOPERATE': actions.count(1),
        'COMPETE': actions.count(2),
        'REST': actions.count(3),
        'REPRODUCE': actions.count(4),
        'ISOLATE': actions.count(5),
    }
}

print("="*50)
print(f"Distance: {stats['distance_traveled']:.1f}m")
print(f"Battery: {stats['final_battery']*100:.0f}%")

# VISUALIZATIONS
print("\n📊 Generating visualizations...")

# 1. 3D Trajectory
fig1, ax1 = plot_trajectory_3d(
    trajectory, 
    title=f"🥚🛸 Cocoon Drone Flight Path\nWind: {wind[0]:.0f} m/s",
    wind_vector=wind
)

# 2. Action timeline
fig2 = plot_actions_over_time(
    actions, 
    dt=dt,
    title="Cocoon's Decision Making Over Time"
)

# 3. Stats dashboard
fig3 = plot_flight_stats(stats, "Cocoon Flight Statistics")

plt.show()
print("✅ Done! Close the plot windows to exit.")
