from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import shutil
from pathlib import Path
from typing import Optional


REPO_URL = "https://github.com/Yufok1/Convergence_Engine.git"
REPO_DIR = Path(os.environ.get("CONVERGENCE_REPO_DIR", "/data/Convergence_Engine"))
URL_FILE = Path("data/tunnel_url.txt")
LOG_FILE = Path("data/hf_jupyter_unified.log")
PID_FILE = Path("/data/engine.pid")


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
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
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


def stop_engine_from_pidfile(pid_file: Path = PID_FILE) -> None:
    if not pid_file.exists():
        print(f"No pid file found: {pid_file}")
        return
    pid_text = pid_file.read_text(encoding="utf-8", errors="replace").strip()
    if not pid_text:
        print(f"Empty pid file: {pid_file}")
        return
    pid = int(pid_text)
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped engine process {pid}")
    except ProcessLookupError:
        print(f"Engine process {pid} is not running")
    finally:
        pid_file.unlink(missing_ok=True)


def ssh_status(repo_dir: Path = REPO_DIR) -> str:
    rows: list[str] = []
    ssh_path = shutil.which("ssh")
    rows.append("SSH / TUNNEL STATUS")
    rows.append("=" * 80)
    rows.append(f"ssh binary: {ssh_path or 'not found'}")
    rows.append(f"repo dir: {Path(repo_dir)}")
    rows.append(f"tunnel url file: {Path(repo_dir) / URL_FILE}")
    rows.append(f"engine log file: {Path(repo_dir) / LOG_FILE}")
    rows.append(f"pid file: {PID_FILE}")

    if PID_FILE.exists():
        rows.append(f"engine pid: {PID_FILE.read_text(encoding='utf-8', errors='replace').strip()}")
    else:
        rows.append("engine pid: none")

    try:
        proc = subprocess.run(
            ["pgrep", "-af", "ssh|cloudflared|unified_entry.py"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=10,
        )
        rows.append("")
        rows.append("matching processes:")
        rows.append(proc.stdout.strip() or "none")
    except Exception as exc:
        rows.append(f"process check failed: {exc}")

    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convergence Engine cloud CLI helper")
    parser.add_argument("command", choices=["prepare", "run", "url", "tail", "stop", "ssh"])
    parser.add_argument("--tunnel", default="localhostrun", choices=["localhostrun", "cloudflared", "auto"])
    args = parser.parse_args()

    if args.command == "prepare":
        repo = ensure_repo()
        install_requirements(repo)
        print(f"Ready: {repo}")
    elif args.command == "run":
        repo = ensure_repo()
        start_engine(repo, tunnel=args.tunnel)
    elif args.command == "url":
        print(wait_for_tunnel_url(REPO_DIR, timeout=300))
    elif args.command == "tail":
        print(tail_log(REPO_DIR, lines=180))
    elif args.command == "stop":
        stop_engine_from_pidfile()
    elif args.command == "ssh":
        print(ssh_status(REPO_DIR))


if __name__ == "__main__":
    main()
