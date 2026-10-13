#!/usr/bin/env bash
# Regeneriše SVE kursne podatke (Day 1 generator -> izvedene tabele Day 2–12) (monorepo: course/Day N/data).
# Deterministički (seed 42). Bez baze, bez .env. Trajanje ~1 min.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R/course/dm-ml"
PY="$R/apps/api/.venv/bin/python"
export HF_HUB_DISABLE_PROGRESS_BARS=1 TRANSFORMERS_VERBOSITY=error
$PY -m app.data.generate_dataset --seed 42 > /dev/null
for g in features training targeting product_text interactions evaluation hybrid session; do
  $PY -m app.data.generate_$g
done
$PY -m app.data.generate_embeddings --embedder auto
$PY -m app.data.generate_ai_comparison
$PY -m app.data.generate_platform
$PY -m app.data.refresh_metadata
$PY -m app.data.verify_dataset
