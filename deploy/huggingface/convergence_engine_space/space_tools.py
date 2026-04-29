from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


REPO_URL = "https://github.com/Yufok1/Convergence_Engine.git"
REPO_DIR = Path(os.environ.get("CONVERGENCE_REPO_DIR", "/data/Convergence_Engine"))
URL_FILE = Path("data/tunnel_url.txt")
LOG_FILE = Path("data/hf_jupyter_unified.log")


def _print_header(label: str) -> None:
    print("\n" + "=" * 80)
    print(label)
    print("=" * 80)


def run(args: list[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> None:
    _print_header(" ".join(args))
    proc = subprocess.Popen(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert proc.stdout is not None
    started = time.time()
    for line in proc.stdout:
        print(line, end="")
        if timeout and time.time() - started > timeout:
            proc.kill()
            raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(args)}")
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"Command failed ({code}): {' '.join(args)}")


def ensure_repo(repo_url: str = REPO_URL, repo_dir: Path = REPO_DIR, branch: str = "main") -> Path:
    repo_dir = Path(repo_dir)
    if (repo_dir / ".git").exists():
        run(["git", "fetch", "origin", branch], cwd=repo_dir, timeout=300)
        run(["git", "checkout", branch], cwd=repo_dir, timeout=120)
        run(["git", "pull", "--ff-only", "origin", branch], cwd=repo_dir, timeout=300)
        return repo_dir

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--branch", branch, repo_url, str(repo_dir)], timeout=600)
    return repo_dir


def install_requirements(repo_dir: Path = REPO_DIR) -> None:
    repo_dir = Path(repo_dir)
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], timeout=600)
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=repo_dir, timeout=3600)


def start_engine(
    repo_dir: Path = REPO_DIR,
    tunnel: str = "localhostrun",
    extra_args: Optional[list[str]] = None,
) -> subprocess.Popen:
    repo_dir = Path(repo_dir)
    url_path = repo_dir / URL_FILE
    log_path = repo_dir / LOG_FILE
    url_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if url_path.exists():
        url_path.unlink()

    cmd = [
        sys.executable,
        "-u",
        "unified_entry.py",
        "--config",
        "config.json",
        "--no-viz",
        "--tunnel",
        tunnel,
        "--tunnel-url-file",
        str(url_path),
        "--tunnel-verbose",
    ]
    if extra_args:
        cmd.extend(extra_args)

    log_handle = log_path.open("a", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_dir),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    proc._convergence_log_handle = log_handle  # type: ignore[attr-defined]
    print(f"Started unified_entry.py pid={proc.pid}")
    print(f"Log file: {log_path}")
    print(f"Tunnel URL file: {url_path}")
    return proc


def wait_for_tunnel_url(repo_dir: Path = REPO_DIR, timeout: int = 240) -> str:
    url_path = Path(repo_dir) / URL_FILE
    deadline = time.time() + timeout
    while time.time() < deadline:
        if url_path.exists():
            value = url_path.read_text(encoding="utf-8", errors="replace").strip()
            if value:
                return value
        time.sleep(1)
    raise TimeoutError(f"No tunnel URL appeared in {url_path} within {timeout}s")


def tail_log(repo_dir: Path = REPO_DIR, lines: int = 120) -> str:
    log_path = Path(repo_dir) / LOG_FILE
    if not log_path.exists():
        return f"No log file yet: {log_path}"
    content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


def stop_engine(proc: Optional[subprocess.Popen]) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=20)
