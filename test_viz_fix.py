"""Quick test to identify visualization issue"""
import sys
sys.path.insert(0, '.')

from unified_entry import UnifiedVisualization

# Create visualization
viz = UnifiedVisualization()
viz.initialize()

# Test with sample data
reality_sim_state = {
    'organism_count': 10,
    'connection_count': 15,
    'modularity': 0.7,
    'clustering_coefficient': 0.5
}

explorer_state = {
    'phase': 'emergence',
    'vp_calculations': 5,
    'breath_cycle': 10,
    'breath_depth': 0.8
}

djinn_kernel_state = {
    'violation_pressure': 0.42,
    'vp_classification': 'stable',
    'vp_calculations': 3
}

print("Testing visualization update...")
try:
    viz.update(reality_sim_state, explorer_state, djinn_kernel_state)
    print("UPDATE SUCCESSFUL!")
except Exception as e:
    print(f"UPDATE FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nVisualization test complete. Close the window to exit.")
input("Press Enter to close...")
