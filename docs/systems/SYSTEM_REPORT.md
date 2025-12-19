# 📊 SystemReport & LiveReporter

**Real-Time Population Analytics for The Butterfly System**

---

## Overview

The SystemReport provides comprehensive, typed dataclasses for population analytics. The LiveReporter enables thread-safe live reporting with configurable intervals.

---

## SystemReport

### Structure

```python
@dataclass
class SystemReport:
    """Comprehensive system status report."""
    timestamp: float
    cycle: int
    population: PopulationStats
    resources: ResourceStats
    neural: NeuralStats
    alliances: AllianceStats
    events: EventStats
    language: LanguageStats
```

### PopulationStats

```python
@dataclass
class PopulationStats:
    count: int = 0
    avg_fitness: float = 0.0
    max_fitness: float = 0.0
    min_fitness: float = 0.0
    avg_age: float = 0.0
    generation: int = 0
    births_this_cycle: int = 0
    deaths_this_cycle: int = 0
```

### ResourceStats

```python
@dataclass
class ResourceStats:
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
```

### NeuralStats

```python
@dataclass
class NeuralStats:
    training_loss: float = 0.0
    avg_epsilon: float = 0.0
    dqn_enabled: bool = False
    training_steps: int = 0
```

### AllianceStats

```python
@dataclass
class AllianceStats:
    total_alliances: int = 0
    total_members: int = 0
    largest_alliance: int = 0
    confederations: int = 0
    empires: int = 0
    hegemonies: int = 0
    wars_in_progress: int = 0
```

### EventStats

```python
@dataclass
class EventStats:
    total_events: int = 0
    recent_events: int = 0
    event_rate: float = 0.0
    causation_graph_size: int = 0
```

### LanguageStats

```python
@dataclass
class LanguageStats:
    vocabulary_size: int = 0
    avg_vocab_per_organism: float = 0.0
    total_communications: int = 0
```

---

## Usage

### Generate a Report

```python
from system_report import SystemReport

# From a network object
report = SystemReport.from_network(network, causation_graph)

# Access typed fields
print(f"Population: {report.population.count}")
print(f"Avg Fitness: {report.population.avg_fitness:.4f}")
print(f"GPU Memory: {report.resources.gpu_memory_used_mb:.1f} MB")
print(f"Alliances: {report.alliances.total_alliances}")
```

### Convert to Dict

```python
data = report.to_dict()
# All fields serialized to JSON-compatible dict
```

---

## LiveReporter

Thread-safe background reporter with configurable intervals.

### Basic Usage

```python
from system_report import LiveReporter

# Create reporter with 5-second interval
reporter = LiveReporter(interval=5.0)

# Add callback for updates
def on_report(report):
    print(f"[LIVE] Pop: {report.population.count}, Fit: {report.population.avg_fitness:.3f}")

reporter.add_callback(on_report)

# Start reporting
reporter.start()

# ... simulation runs ...

# Clean shutdown
reporter.stop()
reporter.close()
```

### Multiple Callbacks

```python
reporter = LiveReporter(interval=5.0)

# Console logging
reporter.add_callback(lambda r: print(f"Pop: {r.population.count}"))

# File logging
def log_to_file(report):
    with open('metrics.log', 'a') as f:
        f.write(f"{report.timestamp},{report.population.avg_fitness}\n")

reporter.add_callback(log_to_file)

# Custom analytics
def track_trends(report):
    global fitness_history
    fitness_history.append(report.population.avg_fitness)

reporter.add_callback(track_trends)
```

### Update from Network

```python
# In your main loop
reporter.update(network, causation_graph)
# Callbacks will be called on the reporter's schedule
```

---

## Integration with Antennae

The SystemReport works seamlessly with the Antennae system:

```python
# In unified_entry.py main loop
report = SystemReport.from_network(network, causation_graph)

# Antennae uses report for sensing
antennae.sense(network.organisms, report)

# Report fields inform Antennae perception:
# - report.alliances → alliance_cohesion, conflict_intensity
# - report.resources → resource_abundance
# - report.population → population_pressure, diversity_sense
```

---

## Configuration

```json
{
  "reporting": {
    "live_interval": 5.0,
    "log_to_file": false,
    "log_path": "data/logs/system_reports.log"
  }
}
```

---

## Thread Safety

The LiveReporter uses:
- `threading.Lock` for callback list protection
- `threading.Event` for clean shutdown
- Background thread for non-blocking updates

```python
# Safe to call from any thread
reporter.update(network, graph)  # Thread-safe
reporter.add_callback(fn)        # Thread-safe
reporter.stop()                  # Clean shutdown
```

---

## Performance

| Operation | Typical Time |
|-----------|--------------|
| `from_network()` | ~1-5ms |
| `to_dict()` | ~0.1ms |
| Callback dispatch | ~0.1ms per callback |

For large populations (10k+ organisms), consider:
- Increasing `interval` to 10+ seconds
- Using sampling instead of full population scans
- Disabling expensive stats (language analysis)

---

## Files

| File | Purpose |
|------|---------|
| `system_report.py` | Main implementation |
| `unified_entry.py` | Integration point |
| `docs/systems/SYSTEM_REPORT.md` | This documentation |

---

## Example Output

```
[REPORT] Cycle 1000 @ 2025-12-17 14:30:00
┌─────────────────────────────────────────────┐
│ POPULATION                                   │
│   Count: 150 | Gen: 42                       │
│   Fitness: avg=0.6234 max=0.9521 min=0.1234 │
│   Births: 12 | Deaths: 8                     │
├─────────────────────────────────────────────┤
│ RESOURCES                                    │
│   CPU: 45.2% | RAM: 4.2GB/16GB               │
│   GPU: 2.1GB/24GB (H100)                     │
├─────────────────────────────────────────────┤
│ NEURAL                                       │
│   Training Loss: 0.0234 | Epsilon: 0.15     │
│   Steps: 50000 | DQN: enabled               │
├─────────────────────────────────────────────┤
│ ALLIANCES                                    │
│   Alliances: 12 | Members: 89               │
│   Confederations: 2 | Wars: 3               │
├─────────────────────────────────────────────┤
│ EVENTS                                       │
│   Total: 15234 | Rate: 12.5/sec             │
│   Graph Size: 8921 nodes                     │
└─────────────────────────────────────────────┘
```
