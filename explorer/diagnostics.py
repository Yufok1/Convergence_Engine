import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class Diagnostics:
    def __init__(self, checkpoint_dir='data/checkpoints', interval_minutes=10):
        self.checkpoint_dir = checkpoint_dir
        self.interval = interval_minutes * 60
        self.last_time_checkpoint = time.time()
        self.certification_checkpoint_counter = 0  # Counter for sparse certification checkpoints
        self.certification_checkpoint_interval = 100  # Save every 100th certification
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        # Clean up old checkpoints on initialization
        self._cleanup_old_checkpoints()

    def _cleanup_old_checkpoints(self):
        """Remove checkpoints older than 7 days and enforce retention limits"""
        try:
            checkpoint_path = Path(self.checkpoint_dir)
            if not checkpoint_path.exists():
                return

            # Calculate cutoff date (7 days ago)
            cutoff_date = datetime.now() - timedelta(days=7)
            cutoff_timestamp = cutoff_date.timestamp()

            # Track checkpoints by type for rotation
            cert_checkpoints = []
            time_checkpoints = []
            other_checkpoints = []

            removed_count = 0

            for filepath in checkpoint_path.glob('*.json'):
                # Remove files older than 7 days
                if filepath.stat().st_mtime < cutoff_timestamp:
                    filepath.unlink()
                    removed_count += 1
                    continue

                # Categorize remaining checkpoints
                filename = filepath.name
                if filename.startswith('certification_'):
                    cert_checkpoints.append((filepath, filepath.stat().st_mtime))
                elif filename.startswith('time_'):
                    time_checkpoints.append((filepath, filepath.stat().st_mtime))
                else:
                    other_checkpoints.append((filepath, filepath.stat().st_mtime))

            # Keep only last 50 certification checkpoints
            if len(cert_checkpoints) > 50:
                cert_checkpoints.sort(key=lambda x: x[1], reverse=True)
                for filepath, _ in cert_checkpoints[50:]:
                    filepath.unlink()
                    removed_count += 1

            # Keep only last 10 time checkpoints
            if len(time_checkpoints) > 10:
                time_checkpoints.sort(key=lambda x: x[1], reverse=True)
                for filepath, _ in time_checkpoints[10:]:
                    filepath.unlink()
                    removed_count += 1

            if removed_count > 0:
                print(f'[Diagnostics] Cleaned up {removed_count} old checkpoints')
                print(f'[Diagnostics] Remaining: {len(cert_checkpoints)} cert, {len(time_checkpoints)} time, {len(other_checkpoints)} other')

        except Exception as e:
            print(f'[Diagnostics] Error cleaning up checkpoints: {e}')

    def save_checkpoint(self, label, state):
        """Save a checkpoint with the given label and state"""
        # For certification checkpoints, only save every Nth one
        if label == 'certification':
            self.certification_checkpoint_counter += 1
            if self.certification_checkpoint_counter % self.certification_checkpoint_interval != 0:
                # Skip this checkpoint (sparse saving)
                return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f'{label}_checkpoint_{ts}.json'
        path = os.path.join(self.checkpoint_dir, fname)

        try:
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
            print(f'[Diagnostics] Checkpoint saved: {fname}')
        except Exception as e:
            print(f'[Diagnostics] Error saving checkpoint: {e}')

    def maybe_time_checkpoint(self, label, state):
        """Save a time-based checkpoint if interval has elapsed"""
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
        """Print a comprehensive system report"""
        print('[Diagnostics] Comprehensive System Report:')
        print(json.dumps(state, indent=2))
