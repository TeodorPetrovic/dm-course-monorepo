#!/usr/bin/env bash
# Pokreće SVE: verify dataset, pytest (API smoke), sve primere po danu, sve labove (reference rešenje).
# Bez .env, bez prave baze: modeli i live događaji idu u privremeni direktorijum.
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R/course"
PY="$R/apps/api/.venv/bin/python"
mkdir -p "$R/outputs"
export MPLBACKEND=Agg
TMP="$(mktemp -d)"; export DM_MODELS_DIR="$TMP/models"; mkdir -p "$DM_MODELS_DIR"
export DM_LIVE_EVENTS="$TMP/live_events.csv"
unset AI_PROVIDER AI_EXTERNAL_API_KEY AI_EXTERNAL_BASE_URL
pass=0; fail=0; FAILED=()
run() { local name="$1"; shift
  if "$@" > "$TMP/log.txt" 2>&1; then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name"; tail -5 "$TMP/log.txt" | sed 's/^/      /'; fail=$((fail+1)); FAILED+=("$name"); fi; }
run "verify_dataset" bash -c "cd dm-ml && $PY -m app.data.verify_dataset"
run "pytest dm-ml/app/tests" bash -c "cd dm-ml && $PY -m pytest -q -p no:warnings app/tests"
for d in 1 2 3 4 5 6 7 8 9 10 11 12; do
  for f in "Day $d"/examples/*.py; do
    case "$f" in */toy_sgd.py|*/demo_*.py|*/visualize_*.py|*/mf_library.py) ;; *) continue;; esac
    run "Day $d: $(basename "$f")" bash -c "$PY \"$f\""
    cp "$TMP/log.txt" "$R/outputs/day$d-$(basename "$f" .py).txt"   # izvor brojeva u lekcijama
  done
  run "Day $d: lab (reference_solutions)" bash -c "cd \"Day $d/lab\" && LAB_MODULE=reference_solutions $PY -m pytest -q -p no:warnings test_lab.py"
  # starter mora da PADNE (NotImplementedError) — inače test ne testira ništa
  run "Day $d: lab starter fails as expected" bash -c "cd \"Day $d/lab\" && ! $PY -m pytest -q -p no:warnings test_lab.py"
done
echo; echo "passed=$pass failed=$fail"; for x in "${FAILED[@]:-}"; do [ -n "$x" ] && echo "  failed: $x"; done
rm -rf "$TMP"; [ "$fail" -eq 0 ]
