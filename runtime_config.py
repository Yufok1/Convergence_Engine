"""
Runtime configuration hot-reload utilities.

Shared between the unified entry process and subsystem controllers so they can
detect changes to ``config.json`` without restarting the Butterfly System.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigHotReloadWatcher:
    """Lightweight file watcher that reloads JSON when the file changes."""

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._last_mtime = 0.0
        self._config: Dict[str, Any] = {}
        self._load_initial_config()

    def _load_initial_config(self):
        config = self._read_config_file()
        mtime = self._get_mtime()
        with self._lock:
            self._config = config
            self._last_mtime = mtime

    def _get_mtime(self) -> float:
        try:
            return self.config_path.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    def _read_config_file(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            # Fall back to last-known config if parse fails
            return {}

    def get_current_config(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._config))  # Deep copy via JSON

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        current_mtime = self._get_mtime()
        with self._lock:
            if current_mtime <= self._last_mtime:
                return None
        # Load outside lock to avoid blocking accessors
        config = self._read_config_file()
        with self._lock:
            self._config = config
            self._last_mtime = current_mtime
            return json.loads(json.dumps(self._config))


