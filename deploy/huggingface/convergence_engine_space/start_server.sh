#!/bin/bash
set -euo pipefail

if [ -z "${JUPYTER_TOKEN:-}" ]; then
  echo "ERROR: JUPYTER_TOKEN is required. Add it in Space Settings -> Variables and secrets."
  exit 1
fi

NOTEBOOK_DIR="/data"

mkdir -p "$NOTEBOOK_DIR"
cp -n /app/notebooks/Convergence_Engine_Cloud_Run.ipynb "$NOTEBOOK_DIR/Convergence_Engine_Cloud_Run.ipynb"
cp -n /app/space_tools.py "$NOTEBOOK_DIR/space_tools.py"
cp -n /app/README_RUNTIME.md "$NOTEBOOK_DIR/README_RUNTIME.md"
cp -n /app/cli_banner.py "$NOTEBOOK_DIR/cli_banner.py"
cp -n /app/scripts/*.sh "$NOTEBOOK_DIR/"
chmod +x "$NOTEBOOK_DIR"/*.sh
python /app/cli_banner.py > "$NOTEBOOK_DIR/START_HERE.txt"
python /app/space_tools.py ssh > "$NOTEBOOK_DIR/SSH_TUNNEL_STATUS.txt" || true
touch "$NOTEBOOK_DIR/LIVE_DASHBOARD.log" "$NOTEBOOK_DIR/SSH_TUNNEL.log"

nohup /bin/bash /app/scripts/auto_live_dashboard.sh >> "$NOTEBOOK_DIR/LIVE_DASHBOARD.log" 2>&1 &
echo $! > "$NOTEBOOK_DIR/live_dashboard_watcher.pid"

nohup /bin/bash /app/scripts/auto_ssh_tunnel.sh >> "$NOTEBOOK_DIR/SSH_TUNNEL.log" 2>&1 &
echo $! > "$NOTEBOOK_DIR/ssh_tunnel_watcher.pid"

mkdir -p /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension
cp /app/jupyter-settings/themes.jupyterlab-settings \
  /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/themes.jupyterlab-settings

echo "Starting Convergence Engine JupyterLab on /data"
echo "Set JUPYTER_TOKEN in Space secrets before exposing this Space."
python /app/cli_banner.py

exec jupyter-lab \
  --ip 0.0.0.0 \
  --port 7860 \
  --no-browser \
  --allow-root \
  --ServerApp.token="$JUPYTER_TOKEN" \
  --ServerApp.tornado_settings="{'headers': {'Content-Security-Policy': 'frame-ancestors *'}}" \
  --ServerApp.cookie_options="{'SameSite': 'None', 'Secure': True}" \
  --ServerApp.disable_check_xsrf=True \
  --LabApp.default_url="/lab/tree/START_HERE.txt" \
  --LabApp.news_url=None \
  --LabApp.check_for_updates_class="jupyterlab.NeverCheckForUpdate" \
  --notebook-dir="$NOTEBOOK_DIR"
