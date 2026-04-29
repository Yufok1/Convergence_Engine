#!/bin/bash
set -euo pipefail

touch /data/LIVE_DASHBOARD.log
tail -n 200 -f /data/LIVE_DASHBOARD.log
