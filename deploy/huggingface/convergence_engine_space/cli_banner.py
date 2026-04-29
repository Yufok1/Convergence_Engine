from __future__ import annotations


BANNER = r"""
   ____                            ____
  / ___|___  _ ____   _____ _ __  / ___| ___ _ __   ___
 | |   / _ \| '_ \ \ / / _ \ '__| | |  _ / _ \ '_ \ / _ \
 | |__| (_) | | | \ V /  __/ |    | |_| |  __/ | | |  __/
  \____\___/|_| |_|\_/ \___|_|     \____|\___|_| |_|\___|

                  CONVERGENCE ENGINE CLOUD CLI
"""


HELP = """
Main commands:

  ./01_prepare_engine.sh     Clone/update repo and install dependencies
  ./02_run_engine.sh         Start unified_entry.py with tunnel support
  ./03_show_tunnel_url.sh    Print the public Convergence web UI URL
  ./04_tail_engine_log.sh    Watch the engine log
  ./05_stop_engine.sh        Stop the running engine
  ./06_live_dashboard.sh     Watch auto-running live_dashboard.py output
  ./07_ssh_tunnel_status.sh  Watch auto-running localhost.run ssh output

Expected flow:

  1. Open a Terminal in JupyterLab.
  2. Run: cd /data
  3. Run: ./01_prepare_engine.sh
  4. Run: ./02_run_engine.sh
  5. Run: ./03_show_tunnel_url.sh
  6. Open the printed URL.

Files:

  /data/Convergence_Engine         Full cloned GitHub repo
  /data/engine.pid                 Running engine process id
  /data/Convergence_Engine/data/hf_jupyter_unified.log
  /data/Convergence_Engine/data/tunnel_url.txt
  /data/LIVE_DASHBOARD.log         Auto live dashboard output
  /data/SSH_TUNNEL.log             Auto ssh tunnel output with public URL

Open these tabs/files:

  START_HERE.txt              This banner
  README_RUNTIME.md           Short command reference
  SSH_TUNNEL.log              Click/copy the localhost.run link here
  LIVE_DASHBOARD.log          Dashboard output
"""


if __name__ == "__main__":
    print(BANNER)
    print(HELP)
