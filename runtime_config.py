"""
Runtime configuration hot-reload utilities.

Shared between the unified entry process and subsystem controllers so they can
detect changes to ``config.json`` without restarting the Butterfly System.
"""

from __future__ import annotations

import json
import os
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


# =============================================================================
# GLOBAL CONFIG ACCESSOR - Single source of truth for hardcoded values
# =============================================================================

_GLOBAL_CONFIG: Dict[str, Any] = {}
_CONFIG_LOADED = False
_GLOBAL_CONFIG_PATH: Optional[Path] = None
_GLOBAL_CONFIG_ENV_VAR = 'BUTTERFLY_CONFIG_PATH'


def _resolve_global_config_path() -> Path:
    """Resolve the active runtime config path."""
    env_path = os.environ.get(_GLOBAL_CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).parent / 'config.json'


def set_global_config_path(config_path: Optional[Path | str]) -> None:
    """Override the global config path used by runtime helpers."""
    global _GLOBAL_CONFIG, _CONFIG_LOADED, _GLOBAL_CONFIG_PATH

    if config_path is None:
        os.environ.pop(_GLOBAL_CONFIG_ENV_VAR, None)
        _GLOBAL_CONFIG_PATH = None
    else:
        resolved_path = Path(config_path).expanduser()
        os.environ[_GLOBAL_CONFIG_ENV_VAR] = str(resolved_path)
        _GLOBAL_CONFIG_PATH = resolved_path

    _GLOBAL_CONFIG = {}
    _CONFIG_LOADED = False


def get_global_config() -> Dict[str, Any]:
    """
    Load and cache the active config once.
    Call this instead of hardcoding values like input_dim=30.
    
    Usage:
        from runtime_config import get_global_config
        cfg = get_global_config()
        input_dim = cfg.get('neural', {}).get('brain', {}).get('input_dim', 30)
    """
    global _GLOBAL_CONFIG, _CONFIG_LOADED, _GLOBAL_CONFIG_PATH
    config_path = _resolve_global_config_path()
    if (not _CONFIG_LOADED) or (_GLOBAL_CONFIG_PATH != config_path):
        _GLOBAL_CONFIG_PATH = config_path
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    _GLOBAL_CONFIG = json.load(f)
            except Exception:
                _GLOBAL_CONFIG = {}
        else:
            _GLOBAL_CONFIG = {}
        _CONFIG_LOADED = True
    return _GLOBAL_CONFIG


def get_input_dim() -> int:
    """
    Get neural.brain.input_dim from config.
    Replaces all hardcoded 25/28/30 values throughout codebase.
    """
    cfg = get_global_config()
    return cfg.get('neural', {}).get('brain', {}).get('input_dim', 30)


def get_hidden_dim() -> int:
    """Get neural.brain.hidden_dim from config."""
    cfg = get_global_config()
    return cfg.get('neural', {}).get('brain', {}).get('hidden_dim', 64)


def get_output_dim() -> int:
    """Get neural.brain.output_dim from config."""
    cfg = get_global_config()
    return cfg.get('neural', {}).get('brain', {}).get('output_dim', 6)
