import os
import json
import time
from datetime import datetime

class Diagnostics:
    def __init__(self, checkpoint_dir='data/checkpoints', interval_minutes=10):
        self.checkpoint_dir = checkpoint_dir
        self.interval = interval_minutes * 60
        self.last_time_checkpoint = time.time()
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save_checkpoint(self, label, state):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f'{label}_checkpoint_{ts}.json'
        path = os.path.join(self.checkpoint_dir, fname)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        print(f'[Diagnostics] Checkpoint saved: {path}')

    def maybe_time_checkpoint(self, label, state):
        now = time.time()
        if now - self.last_time_checkpoint >= self.interval:
            self.save_checkpoint(label, state)
            self.last_time_checkpoint = now

    def load_latest_state(self):
        """Load the most recent system state from checkpoints"""
        try:
            # Find the most recent checkpoint
            checkpoints = []
            for filename in os.listdir(self.checkpoint_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.checkpoint_dir, filename)
                    checkpoints.append((filepath, os.path.getmtime(filepath)))
            
            if not checkpoints:
                print('[Diagnostics] No previous state found, starting fresh')
                return None
            
            # Sort by modification time (newest first)
            checkpoints.sort(key=lambda x: x[1], reverse=True)
            latest_checkpoint = checkpoints[0][0]
            
            with open(latest_checkpoint, 'r') as f:
                state = json.load(f)
            
            print(f'[Diagnostics] Loaded previous state from: {latest_checkpoint}')
            return state
            
        except Exception as e:
            print(f'[Diagnostics] Error loading previous state: {e}')
            return None

    def report(self, state):
        print('[Diagnostics] Comprehensive System Report:')
        print(json.dumps(state, indent=2))
