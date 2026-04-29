# Convergence Engine Cloud Runtime

This directory is the persistent `/data` workspace for the Hugging Face Space.

Open `Convergence_Engine_Cloud_Run.ipynb` and run the cells in order:

1. Clone or update `Yufok1/Convergence_Engine` into `/data/Convergence_Engine`.
2. Install the repo dependencies in this cloud runtime.
3. Start `unified_entry.py` with `--no-viz --tunnel localhostrun`.
4. Open the printed tunnel URL to use the real Convergence web UI.

The Space itself is JupyterLab. The Convergence web page is served by the running engine process and exposed through the tunnel URL printed by the notebook.
