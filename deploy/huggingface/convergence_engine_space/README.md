---
title: Convergence Engine
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Cloud Jupyter runner for Convergence Engine.
---

# Convergence Engine

This Space runs a cloud CLI/JupyterLab control plane for the Convergence Engine.

Open the Space app, enter the `JUPYTER_TOKEN` configured in Space secrets, then open a Terminal and run:

```bash
cd /data
./01_prepare_engine.sh
./02_run_engine.sh
./03_show_tunnel_url.sh
```

The commands run inside this Hugging Face Space. They clone or update the GitHub repo under `/data/Convergence_Engine`, install dependencies in the cloud runtime, start `unified_entry.py`, and print the public tunnel URL for the real Convergence web UI.

## Required Space Secret

Set this in `Settings -> Variables and secrets`:

`JUPYTER_TOKEN=<strong password>`

If `JUPYTER_TOKEN` is not set, the container refuses to start. This avoids exposing an executable notebook with a weak default password.

## Runtime Shape

1. JupyterLab runs on Space port `7860`.
2. Persistent storage mounts at `/data`.
3. `/data` contains simple numbered CLI scripts.
4. `02_run_engine.sh` starts `unified_entry.py --no-viz --tunnel localhostrun`.
5. `03_show_tunnel_url.sh` prints the tunnel URL for the real web UI.
6. `python live_dashboard.py` auto-runs when the repo exists; output goes to `/data/LIVE_DASHBOARD.log`.
7. `ssh -R 80:localhost:5000 nokey@localhost.run` auto-runs on startup; output goes to `/data/SSH_TUNNEL.log`.

Source repo: https://github.com/Yufok1/Convergence_Engine
