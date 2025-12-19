"""Quick test: Cocoon flying a drone with realistic physics."""
import sys
sys.path.insert(0, r'D:\cocoons\creative\12-14.300sh')

print("Loading cocoon (this takes a moment)...")
from cocoon_ensemble_20251214085724 import CocoonAgent
cocoon = CocoonAgent()

print("Loading drone physics...")
from reality_simulator.arena.cocoon_drone_bridge import CocoonDronePilot
import numpy as np

print("Creating drone pilot...")
pilot = CocoonDronePilot(cocoon, team='blue')

print("\n" + "="*60)
print("🥚🛸 COCOON DRONE FLIGHT TEST")
print("="*60)

# Fly mission
stats = pilot.fly_mission(
    duration=10.0, 
    visualize=True, 
    wind=np.array([5.0, 2.0, 0])
)

print("\n📊 FLIGHT STATISTICS:")
print(f"   Distance traveled: {stats['distance_traveled']:.1f}m")
print(f"   Final battery: {stats['final_battery']*100:.0f}%")
print(f"   Crashed: {stats['crashed']}")
print(f"   Actions: {stats['actions_histogram']}")
