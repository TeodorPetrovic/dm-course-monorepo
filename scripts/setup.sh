#!/usr/bin/env bash
# Jednokratna priprema: Python venv za API + Day 1 events.csv (regenerisan, seed 42) + verifikacija sha256.
# Frontend: cd apps/frontend && bun install (ili npm install).
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R/apps/api"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q --index-url https://download.pytorch.org/whl/cpu torch   # CPU torch (manji)
  .venv/bin/pip install -q -r requirements-dev.txt
fi
cd "$R/course/dm-ml"
[ -f "../Day 1/data/events.csv" ] || .venv/bin/python -m app.data.generate_dataset --seed 42 > /dev/null
.venv/bin/python -m app.data.verify_dataset
echo "OK. Dalje: scripts/run_all.sh, scripts/check_commands.sh (vidi README)."
