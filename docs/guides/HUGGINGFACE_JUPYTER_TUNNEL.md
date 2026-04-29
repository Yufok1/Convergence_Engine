# Hugging Face Jupyter Tunnel Workflow

This is the near-term public demo lane: use Hugging Face/Jupyter as the control plane, run `unified_entry.py` there, and expose the Convergence web UI through the built-in tunnel support.

## Current Status

- GitHub source of truth: `https://github.com/Yufok1/Convergence_Engine`
- Runtime entry point: `unified_entry.py`
- Web UI port: `5000`
- Preferred tunnel: `localhostrun`
- Tunnel URL file: `data/tunnel_url.txt`

## Notebook Cells

### 1. Clone or update the repo

```python
from pathlib import Path

REPO_DIR = Path("/tmp/Convergence_Engine")

if not REPO_DIR.exists():
    !git clone https://github.com/Yufok1/Convergence_Engine.git {REPO_DIR}
else:
    %cd {REPO_DIR}
    !git pull --ff-only origin main

%cd {REPO_DIR}
```

### 2. Install dependencies

Use the CPU path for the public demo/control plane. Rent Vast only for heavy training.

```python
!python -m pip install --upgrade pip
!python -m pip install -r requirements.txt
```

### 3. Start the system and tunnel

```python
%cd /tmp/Convergence_Engine

from scripts.hf_jupyter_unified_tunnel import start_unified_entry, wait_for_tunnel_url

convergence_proc = start_unified_entry(
    repo_dir="/tmp/Convergence_Engine",
    config="config.json",
    tunnel="localhostrun",
)

public_url = wait_for_tunnel_url(repo_dir="/tmp/Convergence_Engine", timeout=180)
print(public_url)
```

Open the printed URL. It should route to the same Convergence web UI that is available locally at `http://localhost:5000` inside the notebook runtime.

### 4. Inspect logs

```python
from scripts.hf_jupyter_unified_tunnel import tail_log

print(tail_log(repo_dir="/tmp/Convergence_Engine", lines=120))
```

### 5. Stop cleanly

```python
from scripts.hf_jupyter_unified_tunnel import stop_process

stop_process(convergence_proc)
```

## Direct CLI Equivalent

If you are already inside the repo in a terminal/notebook shell:

```bash
python -u unified_entry.py --config config.json --no-viz --tunnel localhostrun --tunnel-url-file data/tunnel_url.txt --tunnel-verbose
```

Then read:

```bash
cat data/tunnel_url.txt
```

## Operational Notes

- Use `--no-viz`; `--headless` appears in the file header, but the actual argparse flag is `--no-viz`.
- `--tunnel auto` is acceptable if the runtime may have `cloudflared`; otherwise use `localhostrun` for the old `*.lhr.life` style workflow.
- Keep Hugging Face tokens out of notebooks and git. Use Space/Notebook secrets if auth is needed.
- Do not expose a raw Jupyter server publicly unless it is private and authenticated. The public browser surface should be the Convergence web UI tunnel, not the notebook kernel.
- If the tunnel URL rotates, rerun the `wait_for_tunnel_url` cell or inspect `data/tunnel_url.txt`.
