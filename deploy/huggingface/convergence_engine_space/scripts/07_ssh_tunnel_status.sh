#!/bin/bash
set -euo pipefail

touch /data/SSH_TUNNEL.log
tail -n 200 -f /data/SSH_TUNNEL.log
