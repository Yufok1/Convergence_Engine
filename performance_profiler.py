"""
Performance Profiler for Butterfly System
Measures actual cycle times and identifies bottlenecks
"""

import time
import statistics
from collections import deque
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class CycleMetrics:
    """Metrics for a single cycle"""
    cycle_number: int
    total_time: float
    component_times: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PerformanceProfiler:
    """Profiles performance of unified system cycles"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.cycles: deque = deque(maxlen=window_size)
        self.current_cycle_start: Optional[float] = None
        self.component_timers: Dict[str, List[float]] = {}
        self.cycle_count = 0
        
        # Track detailed metrics
        self.total_cycles = 0
        self.total_time = 0.0
        
    def start_cycle(self):
        """Start timing a new cycle"""
        self.current_cycle_start = time.perf_counter()
        self.component_timers.clear()
        
    def time_component(self, component_name: str):
        """Context manager for timing components"""
        return ComponentTimer(component_name, self)
    
    def record_component_time(self, component_name: str, elapsed: float):
        """Record time spent in a component"""
        if component_name not in self.component_timers:
            self.component_timers[component_name] = []
        self.component_timers[component_name].append(elapsed)
    
    def end_cycle(self) -> CycleMetrics:
        """End current cycle and record metrics"""
        if self.current_cycle_start is None:
            return None
        
        total_time = time.perf_counter() - self.current_cycle_start
        self.cycle_count += 1
        self.total_cycles += 1
        self.total_time += total_time
        
        metrics = CycleMetrics(
            cycle_number=self.cycle_count,
            total_time=total_time,
            component_times=self.component_timers.copy()
        )
        
        self.cycles.append(metrics)
        self.current_cycle_start = None
        
        return metrics
    
    def get_statistics(self) -> Dict:
        """Get performance statistics"""
        if not self.cycles:
            return {"error": "No cycles recorded yet"}
        
        cycle_times = [c.total_time for c in self.cycles]
        
        # Component times
        component_stats = {}
        for component in set(
            comp for c in self.cycles 
            for comp in c.component_times.keys()
        ):
            times = [
                c.component_times.get(component, 0.0) 
                for c in self.cycles 
                if component in c.component_times
            ]
            if times:
                component_stats[component] = {
                    "avg_ms": statistics.mean(times) * 1000,
                    "median_ms": statistics.median(times) * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "total_ms": sum(times) * 1000,
                    "percentage": (sum(times) / sum(cycle_times)) * 100
                }
        
        return {
            "cycles_recorded": len(self.cycles),
            "total_cycles": self.total_cycles,
            "total_time_seconds": self.total_time,
            "overall": {
                "avg_cycle_time_ms": statistics.mean(cycle_times) * 1000,
                "median_cycle_time_ms": statistics.median(cycle_times) * 1000,
                "min_cycle_time_ms": min(cycle_times) * 1000,
                "max_cycle_time_ms": max(cycle_times) * 1000,
                "std_dev_ms": statistics.stdev(cycle_times) * 1000 if len(cycle_times) > 1 else 0,
                "cycles_per_second": 1.0 / statistics.mean(cycle_times) if cycle_times else 0,
                "theoretical_max_fps": 1.0 / statistics.mean(cycle_times) if cycle_times else 0
            },
            "components": component_stats,
            "bottlenecks": self._identify_bottlenecks(component_stats)
        }
    
    def _identify_bottlenecks(self, component_stats: Dict) -> List[Dict]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Sort by percentage of time spent
        sorted_components = sorted(
            component_stats.items(),
            key=lambda x: x[1]["percentage"],
            reverse=True
        )
        
        # Top 5 bottlenecks
        for component, stats in sorted_components[:5]:
            if stats["percentage"] > 5.0:  # More than 5% of time
                bottlenecks.append({
                    "component": component,
                    "avg_time_ms": stats["avg_ms"],
                    "percentage": stats["percentage"],
                    "severity": "high" if stats["percentage"] > 20 else "medium" if stats["percentage"] > 10 else "low"
                })
        
        return bottlenecks
    
    def print_report(self):
        """Print a human-readable performance report"""
        stats = self.get_statistics()
        
        if "error" in stats:
            print(f"[Profiler] {stats['error']}")
            return
        
        print("\n" + "="*70)
        print("PERFORMANCE PROFILING REPORT")
        print("="*70)
        print(f"\nCycles Recorded: {stats['cycles_recorded']} (window) / {stats['total_cycles']} (total)")
        print(f"Total Time: {stats['total_time_seconds']:.2f}s")
        
        overall = stats['overall']
        print(f"\n📊 Overall Performance:")
        print(f"  Average Cycle Time: {overall['avg_cycle_time_ms']:.2f}ms")
        print(f"  Median Cycle Time: {overall['median_cycle_time_ms']:.2f}ms")
        print(f"  Min/Max: {overall['min_cycle_time_ms']:.2f}ms / {overall['max_cycle_time_ms']:.2f}ms")
        print(f"  Std Dev: {overall['std_dev_ms']:.2f}ms")
        print(f"  Cycles/Second: {overall['cycles_per_second']:.2f}")
        print(f"  Theoretical Max FPS: {overall['theoretical_max_fps']:.2f}")
        
        # Current sleep time
        current_sleep = 0.1  # From unified_entry.py
        theoretical_speedup = current_sleep / (overall['avg_cycle_time_ms'] / 1000)
        if theoretical_speedup > 1:
            print(f"\n⚡ Speedup Potential:")
            print(f"  Current Sleep: {current_sleep*1000:.0f}ms")
            print(f"  Actual Cycle Time: {overall['avg_cycle_time_ms']:.2f}ms")
            print(f"  Theoretical Speedup: {theoretical_speedup:.1f}x (if sleep removed)")
        
        print(f"\n🔍 Component Breakdown:")
        components = sorted(
            stats['components'].items(),
            key=lambda x: x[1]['percentage'],
            reverse=True
        )
        
        for component, comp_stats in components:
            print(f"\n  {component}:")
            print(f"    Avg: {comp_stats['avg_ms']:.2f}ms ({comp_stats['percentage']:.1f}%)")
            print(f"    Min/Max: {comp_stats['min_ms']:.2f}ms / {comp_stats['max_ms']:.2f}ms")
        
        if stats['bottlenecks']:
            print(f"\n🚨 Bottlenecks Identified:")
            for bottleneck in stats['bottlenecks']:
                severity_emoji = "🔴" if bottleneck['severity'] == 'high' else "🟡" if bottleneck['severity'] == 'medium' else "🟢"
                print(f"  {severity_emoji} {bottleneck['component']}: {bottleneck['avg_time_ms']:.2f}ms ({bottleneck['percentage']:.1f}%)")
        
        print("\n" + "="*70)
    
    def save_report(self, filepath: Optional[str] = None):
        """Save detailed report to JSON file"""
        if filepath is None:
            filepath = Path("data/logs/performance_report.json")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        stats = self.get_statistics()
        
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"[Profiler] Report saved to {filepath}")


class ComponentTimer:
    """Context manager for timing components"""
    
    def __init__(self, component_name: str, profiler: PerformanceProfiler):
        self.component_name = component_name
        self.profiler = profiler
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        self.profiler.record_component_time(self.component_name, elapsed)
        return False


# Example usage:
if __name__ == "__main__":
    profiler = PerformanceProfiler(window_size=100)
    
    # Simulate a few cycles
    for i in range(10):
        profiler.start_cycle()
        
        with profiler.time_component("state_collection"):
            time.sleep(0.001)  # Simulate work
        
        with profiler.time_component("logging"):
            time.sleep(0.002)  # Simulate work
        
        with profiler.time_component("breath_cycle"):
            time.sleep(0.001)  # Simulate work
        
        profiler.end_cycle()
        time.sleep(0.1)  # Simulate the 100ms sleep
    
    profiler.print_report()
    profiler.save_report()
