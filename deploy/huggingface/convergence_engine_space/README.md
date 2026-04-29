---
title: Convergence Engine
sdk: gradio
sdk_version: 5.33.1
app_file: app.py
pinned: false
license: mit
short_description: Public launch page for the Convergence Engine notebook tunnel demo.
---

# Convergence Engine

This Space is the public launch page for the Convergence Engine demo.

The full Convergence Engine runtime is launched from a notebook or rented runtime, then exposed through the built-in tunnel workflow. This keeps the public surface lightweight while preserving the real engine, compiler, and web UI in the GitHub source tree.

## Source

GitHub: https://github.com/Yufok1/Convergence_Engine

## Launch Model

1. Open a Hugging Face/Jupyter or rented runtime.
2. Clone the GitHub repo.
3. Install dependencies.
4. Start `unified_entry.py` with `--no-viz --tunnel localhostrun`.
5. Open the tunnel URL written to `data/tunnel_url.txt`.

See `docs/guides/HUGGINGFACE_JUPYTER_TUNNEL.md` in the GitHub repo for the canonical notebook cells.
