#!/usr/bin/env bash
# Pre časa (jednom, ~5–10 min prvi put; posle ~1 min): sve sporo se radi UNAPRED, da na času ništa ne čeka > ~2 min.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; PY="$R/apps/api/.venv/bin/python"
"$R/scripts/teach.sh" status | grep -q nijedan || { echo "Kod je u starter stanju — prvo: scripts/teach.sh solution"; exit 1; }
t() { local s=$(date +%s); "$@"; echo "   ($(( $(date +%s) - s )) s) $*"; }
echo "1) Python venv + Day 1 podaci";            t "$R/scripts/setup.sh" >/dev/null
echo "2) embedding model u HF keš (Day 10)";     t "$PY" -c "import sys; sys.path.insert(0,'$R/apps/api'); from app.recommenders.embeddings import ST_MODEL; from sentence_transformers import SentenceTransformer; SentenceTransformer(ST_MODEL)" >/dev/null 2>&1 || echo "   (nema mreže/ST: Day 10 koristi hash embedder)"
echo "3) svi izvedeni podaci (Day 2–12)";        t "$R/scripts/regenerate_all.sh" >/dev/null
echo "4) lokalna baza";                          t bash -c "'$R/db/start_local_db.sh' >/dev/null && '$R/db/load.sh' >/dev/null"
echo "5) frontend zavisnosti + build";           t bash -c "cd '$R/apps/frontend' && bun install >/dev/null 2>&1 && bun run build >/dev/null 2>&1"
echo "6) zagrevanje API-ja (import + prvi pozivi)"
t "$PY" - 2>/dev/null <<PY
import os, sys, tempfile; sys.path.insert(0, "$R/apps/api"); os.environ.setdefault("DM_LIVE_EVENTS", tempfile.mktemp())
from fastapi.testclient import TestClient; from app.main import app; c = TestClient(app)
for path in ["/analytics/summary", "/recommendations/popular", "/recommendations/content/1", "/recommendations/collaborative/1",
             "/recommendations/395", "/analytics/recommendations", "/search/semantic?q=shoes"]:
    c.get(path)
PY
echo "Spremno. Na času: scripts/teach.sh start NN  (fallback: scripts/teach.sh solution NN)"
