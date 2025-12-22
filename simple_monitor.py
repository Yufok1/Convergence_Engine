#!/usr/bin/env python3
"""
SIMPLE CONVERGENCE ENGINE MONITOR
=================================

A clean, emoji-free monitoring utility for the Convergence Engine.
"""

import json
import sys
from pathlib import Path

class SimpleMonitor:
    def __init__(self):
        self.live_data = {}

    def load_data(self):
        """Load live simulation data"""
        try:
            with open("data/live_report.json", "r") as f:
                self.live_data = json.load(f)
            return True
        except FileNotFoundError:
            print("No live_report.json found. Run the simulation first.")
            return False

    def show_quick_stats(self):
        """Show essential statistics"""
        if not self.live_data:
            return

        pop = self.live_data.get("population", {})
        hl = self.live_data.get("highlander", {})
        al = self.live_data.get("alliances", {})
        nn = self.live_data.get("neural", {})
        lang = self.live_data.get("language", {})
        res = self.live_data.get("resources", {})
        events = self.live_data.get("events", {})

        print("CONVERGENCE ENGINE STATUS")
        print("="*50)
        print(f"Timestamp: {self.live_data.get('timestamp')}")
        print()
        print("POPULATION")
        print(f"  Total: {pop.get('total_organisms', 0)}")
        print(f"  Active: {pop.get('active_organisms', 0)}")
        print(f"  Fitness: {pop.get('fitness_mean', 0):.4f}")
        print()
        print("HIGHLANDER")
        print(f"  Round: {hl.get('round_number', 0)}")
        print(f"  Eliminations: {hl.get('eliminations_total', 0)}")
        print(f"  Phase: {hl.get('phase', 'unknown')}")
        print()
        print("ALLIANCES")
        print(f"  Active: {al.get('active_alliances', 0)}")
        print(f"  Members: {al.get('total_members', 0)}")
        print(f"  Warchiefs: {al.get('warchief_count', 0)}")
        print()
        print("NEURAL")
        print(f"  Brains: {nn.get('organisms_with_brains', 0)}")
        print(f"  Epsilon: {nn.get('avg_epsilon', 0):.4f}")
        print(f"  Experience: {nn.get('experience_buffer_total', 0)}")
        print()
        print("LANGUAGE")
        print(f"  Vocabulary: {lang.get('total_vocabulary_words', 0)}")
        print(f"  Mastery Level: {lang.get('highest_mastery_achieved', 0)}")
        print()
        print("SYSTEM")
        print(f"  Breath Cycle: {res.get('breath_cycle', 0)}")
        print(f"  CPU: {res.get('cpu_percent', 0):.1f}%")
        print(f"  Memory: {res.get('memory_used_gb', 0):.1f}GB")
        print(f"  Events/Hour: {events.get('events_last_hour', 0)}")

def main():
    monitor = SimpleMonitor()
    if monitor.load_data():
        monitor.show_quick_stats()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
