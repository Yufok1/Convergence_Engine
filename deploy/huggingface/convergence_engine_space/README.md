---
title: Convergence Engine
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Cloud Jupyter runner for Convergence Engine.
---

# Convergence Engine

This Space runs a cloud JupyterLab control plane for the Convergence Engine.

Open the Space app, enter the `JUPYTER_TOKEN` configured in Space secrets, and run the prepared notebook:

`Convergence_Engine_Cloud_Run.ipynb`

The notebook runs inside this Hugging Face Space. It clones or updates the GitHub repo under `/data/Convergence_Engine`, installs dependencies in the cloud runtime, starts `unified_entry.py`, and prints the public tunnel URL for the real Convergence web UI.

## Required Space Secret

Set this in `Settings -> Variables and secrets`:

`JUPYTER_TOKEN=<strong password>`

If `JUPYTER_TOKEN` is not set, the container refuses to start. This avoids exposing an executable notebook with a weak default password.

## Runtime Shape

1. JupyterLab runs on Space port `7860`.
2. Persistent storage mounts at `/data`.
3. The prepared notebook opens by default.
4. The notebook starts `unified_entry.py --no-viz --tunnel localhostrun`.
5. The notebook prints the tunnel URL for the real web UI.

Source repo: https://github.com/Yufok1/Convergence_Engine
