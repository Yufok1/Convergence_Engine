from reality_simulator.main import RealitySimulator
import time

# Create simulator
rs = RealitySimulator()

# Set up event capture
events_captured = []
def capture_event(event):
    events_captured.append(event)
    print(f"EVENT: {event.event_type}")

rs.event_emitter = capture_event

# Initialize
rs.initialize_simulation()

# Run a few simulation steps to generate events
print("Running simulation steps...")
for step in range(5):
    print(f"Step {step + 1}/5")
    rs.run_simulation()
    time.sleep(0.1)  # Small delay

print(f"\nCaptured {len(events_captured)} events:")
neural_events = [e for e in events_captured if 'neural' in e.event_type]
ml_events = [e for e in events_captured if e.event_type in ['phenotype_emergence', 'cluster_collapse', 'anomaly_spike']]

print(f"Neural events: {len(neural_events)}")
for event in neural_events:
    print(f"  - {event.event_type}")

print(f"ML events: {len(ml_events)}")
for event in ml_events:
    print(f"  - {event.event_type}")

# Run CRA diagnostic
print("\nRunning CRA diagnostic...")
try:
    from causation_web_ui import run_causation_analysis
    result = run_causation_analysis(rs, events_captured)
    print("CRA Result:", result)
except Exception as e:
    print(f"CRA diagnostic failed: {e}")
    import traceback
    traceback.print_exc()