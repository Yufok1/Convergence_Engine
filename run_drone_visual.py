"""
Live Drone Visualization Runner
Run from: F:\Amoeba\Convergence_Engine\
Usage: python run_drone_visual.py [cocoon_path]
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reality_simulator.arena.live_drone_view import LiveCocoonFlight, demo_flight

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cocoon_path = sys.argv[1]
        print(f"Loading cocoon: {cocoon_path}")
        flight = LiveCocoonFlight(cocoon_path)
        flight.run(max_steps=2000, wind_speed=5.0)
    else:
        print("No cocoon specified, running demo...")
        demo_flight()
