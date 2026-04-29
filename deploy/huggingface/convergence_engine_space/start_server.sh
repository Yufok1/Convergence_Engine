#!/bin/bash
set -euo pipefail

JUPYTER_TOKEN="${JUPYTER_TOKEN:=huggingface}"
NOTEBOOK_DIR="/data"

mkdir -p "$NOTEBOOK_DIR"
cp -n /app/notebooks/Convergence_Engine_Cloud_Run.ipynb "$NOTEBOOK_DIR/Convergence_Engine_Cloud_Run.ipynb"
cp -n /app/space_tools.py "$NOTEBOOK_DIR/space_tools.py"
cp -n /app/README_RUNTIME.md "$NOTEBOOK_DIR/README_RUNTIME.md"

mkdir -p /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension
cp /app/jupyter-settings/themes.jupyterlab-settings \
  /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/themes.jupyterlab-settings

echo "Starting Convergence Engine JupyterLab on /data"
echo "Set JUPYTER_TOKEN in Space secrets before exposing this Space."

exec jupyter-lab \
  --ip 0.0.0.0 \
  --port 7860 \
  --no-browser \
  --allow-root \
  --ServerApp.token="$JUPYTER_TOKEN" \
  --ServerApp.tornado_settings="{'headers': {'Content-Security-Policy': 'frame-ancestors *'}}" \
  --ServerApp.cookie_options="{'SameSite': 'None', 'Secure': True}" \
  --ServerApp.disable_check_xsrf=True \
  --LabApp.default_url="/lab/tree/Convergence_Engine_Cloud_Run.ipynb" \
  --LabApp.news_url=None \
  --LabApp.check_for_updates_class="jupyterlab.NeverCheckForUpdate" \
  --notebook-dir="$NOTEBOOK_DIR"
