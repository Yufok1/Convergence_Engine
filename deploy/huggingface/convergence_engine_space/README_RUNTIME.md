# Convergence Engine Cloud CLI

This is the persistent `/data` workspace for the Hugging Face Space.

Open a Terminal in JupyterLab and run:

```bash
cd /data
./01_prepare_engine.sh
./02_run_engine.sh
./03_show_tunnel_url.sh
```

Then open the printed tunnel URL.

Useful commands:

```bash
./04_tail_engine_log.sh
./05_stop_engine.sh
./06_live_dashboard.sh
./07_ssh_tunnel_status.sh
```

The full repo is cloned to `/data/Convergence_Engine`. The notebook is optional.

## Always-On Tabs

These start automatically when the Space starts:

- `python live_dashboard.py`
- `ssh -R 80:localhost:5000 nokey@localhost.run`

Open these files from the left file browser:

- `SSH_TUNNEL.log` - copy/click the localhost.run URL here
- `LIVE_DASHBOARD.log` - dashboard output

To watch from a terminal:

```bash
cd /data
./06_live_dashboard.sh
./07_ssh_tunnel_status.sh
```
