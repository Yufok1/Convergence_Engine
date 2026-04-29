"""Notebook helpers for running Convergence Engine behind a public tunnel.

This module is intentionally small and side-effect free on import. It is meant
to be imported from a Hugging Face/Jupyter notebook, then used to start
``unified_entry.py`` with the repo's built-in tunnel support.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_REPO_URL = "https://github.com/Yufok1/Convergence_Engine.git"
DEFAULT_REPO_DIR = Path(os.environ.get("CONVERGENCE_REPO_DIR", "/tmp/Convergence_Engine"))
DEFAULT_URL_FILE = Path("data/tunnel_url.txt")
DEFAULT_LOG_FILE = Path("data/hf_jupyter_unified.log")


def run_command(args: Iterable[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> str:
    """Run a command and return combined output, raising on failure."""
    proc = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout}")
    return proc.stdout


def ensure_repo(
    repo_url: str = DEFAULT_REPO_URL,
    repo_dir: Path | str = DEFAULT_REPO_DIR,
    branch: str = "main",
) -> Path:
    """Clone or update the Convergence Engine repo for notebook use."""
    repo_dir = Path(repo_dir).expanduser().resolve()

    if (repo_dir / ".git").exists():
        run_command(["git", "fetch", "origin", branch], cwd=repo_dir, timeout=180)
        run_command(["git", "checkout", branch], cwd=repo_dir, timeout=60)
        run_command(["git", "pull", "--ff-only", "origin", branch], cwd=repo_dir, timeout=180)
        return repo_dir

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    run_command(["git", "clone", "--branch", branch, repo_url, str(repo_dir)], timeout=300)
    return repo_dir


def find_repo_root(start: Optional[Path | str] = None) -> Path:
    """Find a repo root containing unified_entry.py."""
    current = Path(start or os.getcwd()).expanduser().resolve()
    for path in [current, *current.parents]:
        if (path / "unified_entry.py").exists():
            return path
    raise FileNotFoundError("Could not find unified_entry.py; call ensure_repo() first.")


def start_unified_entry(
    repo_dir: Optional[Path | str] = None,
    config: str = "config.json",
    tunnel: str = "localhostrun",
    url_file: Path | str = DEFAULT_URL_FILE,
    log_file: Path | str = DEFAULT_LOG_FILE,
    extra_args: Optional[list[str]] = None,
) -> subprocess.Popen:
    """Start unified_entry.py in the background and stream output to a log file."""
    repo = find_repo_root(repo_dir)
    url_path = Path(url_file)
    log_path = Path(log_file)

    if not url_path.is_absolute():
        url_path = repo / url_path
    if not log_path.is_absolute():
        log_path = repo / log_path

    url_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if url_path.exists():
        url_path.unlink()

    cmd = [
        sys.executable,
        "-u",
        "unified_entry.py",
        "--config",
        config,
        "--no-viz",
        "--tunnel",
        tunnel,
        "--tunnel-url-file",
        str(url_path),
    ]
    if extra_args:
        cmd.extend(extra_args)

    log_handle = log_path.open("a", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Keep the handle reachable so it is not garbage-collected while the process runs.
    proc._convergence_log_handle = log_handle  # type: ignore[attr-defined]
    print(f"Started unified_entry.py pid={proc.pid}")
    print(f"Log: {log_path}")
    print(f"Tunnel URL file: {url_path}")
    return proc


def wait_for_tunnel_url(
    url_file: Path | str = DEFAULT_URL_FILE,
    repo_dir: Optional[Path | str] = None,
    timeout: int = 120,
) -> str:
    """Wait for unified_entry.py to write a public tunnel URL."""
    repo = find_repo_root(repo_dir)
    url_path = Path(url_file)
    if not url_path.is_absolute():
        url_path = repo / url_path

    deadline = time.time() + timeout
    last_value = ""
    while time.time() < deadline:
        if url_path.exists():
            value = url_path.read_text(encoding="utf-8", errors="replace").strip()
            if value and value != last_value:
                return value
            last_value = value
        time.sleep(1)
    raise TimeoutError(f"No tunnel URL appeared in {url_path} within {timeout}s")


def tail_log(log_file: Path | str = DEFAULT_LOG_FILE, repo_dir: Optional[Path | str] = None, lines: int = 80) -> str:
    """Return the last N lines of the unified_entry log."""
    repo = find_repo_root(repo_dir)
    log_path = Path(log_file)
    if not log_path.is_absolute():
        log_path = repo / log_path
    if not log_path.exists():
        return f"No log file yet: {log_path}"
    content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


def stop_process(proc: Optional[subprocess.Popen], timeout: int = 15) -> None:
    """Terminate a process started by start_unified_entry."""
    if proc is None:
        return
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=timeout)
