#!/usr/bin/env bash
# Nastava uživo: starter/rešenje po danu. Vidi teaching/README.md.
#   teach.sh prepare            # pre časa: venv, podaci, HF model, baza, frontend build (sve sporo unapred)
#   teach.sh start NN           # starter stanje dana NN
#   teach.sh solution [NN]      # rešenje (fallback kad kasniš)
#   teach.sh status | lines [NN] | diff NN | verify
#   teach.sh check [--frontend] # rešenje prolazi run_all + check_commands (+ smoke_frontend)
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
case "${1:-}" in
  prepare) exec "$R/scripts/teach_prepare.sh" ;;
  check)
    "$R/scripts/teach.py" solution
    "$R/scripts/run_all.sh" && "$R/scripts/check_commands.sh"
    if [ "${2:-}" = "--frontend" ]; then (cd "$R/apps/frontend" && bun run build >/dev/null) && "$R/apps/api/.venv/bin/python" "$R/scripts/smoke_frontend.py"; fi ;;
  *) exec "$R/apps/api/.venv/bin/python" "$R/scripts/teach.py" "$@" ;;
esac
