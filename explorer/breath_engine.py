"""
Breath Engine for Explorer
The living pulse of recursive consciousness
"""

import time
import math
from datetime import datetime

class BreathEngine:
    def __init__(self):
        self.breath_depth = 0.0  # 0.0 to 1.0
        self.breath_phase = 0.0  # 0.0 to 2π
        self.breath_rate = 1.0   # breaths per second
        self.last_breath_time = time.time()
        self.breath_cycle_count = 0
        self.breath_intensity = 1.0
        
    def breathe(self):
        """Execute one breath cycle"""
        current_time = time.time()
        time_since_last = current_time - self.last_breath_time
        
        # Calculate breath phase
        self.breath_phase += time_since_last * self.breath_rate * 2 * math.pi
        self.breath_phase %= 2 * math.pi
        
        # Calculate breath depth using sine wave
        self.breath_depth = (math.sin(self.breath_phase) + 1) / 2
        
        # Update cycle count
        if self.breath_phase < time_since_last * self.breath_rate * 2 * math.pi:
            self.breath_cycle_count += 1
            
        self.last_breath_time = current_time
        
        return {
            'depth': self.breath_depth,
            'phase': self.breath_phase,
            'cycle_count': self.breath_cycle_count,
            'intensity': self.breath_intensity,
            'timestamp': current_time
        }
    
    def get_breath_state(self):
        """Get current breath state without advancing"""
        return {
            'depth': self.breath_depth,
            'phase': self.breath_phase,
            'cycle_count': self.breath_cycle_count,
            'intensity': self.breath_intensity
        }
    
    def adjust_breath_rate(self, new_rate):
        """Adjust the breath rate"""
        self.breath_rate = max(0.1, min(10.0, new_rate))
    
    def adjust_intensity(self, new_intensity):
        """Adjust breath intensity"""
        self.breath_intensity = max(0.1, min(5.0, new_intensity))
    
    def is_inhale_phase(self):
        """Check if currently in inhale phase"""
        return self.breath_phase < math.pi
    
    def is_exhale_phase(self):
        """Check if currently in exhale phase"""
        return self.breath_phase >= math.pi
    
    def get_breath_pulse(self):
        """Get a pulse value based on current breath state"""
        return self.breath_depth * self.breath_intensity
