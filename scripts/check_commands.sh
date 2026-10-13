#!/usr/bin/env bash
# Pokreće komande koje lekcije navode (revised/) i proverava da rade i da daju ono što piše.
# Generatori pišu u privremeni dir i porede se bajt-po-bajt sa commit-ovanim Day N/data fajlovima.
# metadata.json za Day 2-9 nije u poređenju: refresh_metadata ga obogaćuje (brojevi redova, sha) posle generisanja.
set -u
B="$(cd "$(dirname "$0")/.." && pwd)"; C="$B/course"; PY="$C/dm-ml/.venv/bin/python"
TMP="$(mktemp -d)"; export DM_MODELS_DIR="$TMP/models" DM_LIVE_EVENTS="$TMP/live.csv" MPLBACKEND=Agg; mkdir -p "$DM_MODELS_DIR"
unset AI_PROVIDER AI_EXTERNAL_API_KEY AI_EXTERNAL_BASE_URL
pass=0; fail=0
ok(){ echo "PASS  $1"; pass=$((pass+1)); }; ko(){ echo "FAIL  $1"; fail=$((fail+1)); }
run(){ local n="$1"; shift; if "$@" >"$TMP/o.txt" 2>&1; then ok "$n"; else ko "$n"; tail -5 "$TMP/o.txt"|sed 's/^/      /'; fi; }
same(){ # $1 ime, $2 generisani dir, $3 commit-ovani dir, ostalo = fajlovi
  local n="$1" g="$2" r="$3"; shift 3; local bad=0
  for f in "$@"; do cmp -s "$g/$f" "$r/$f" || { echo "      razlika: $f"; bad=1; }; done
  [ $bad -eq 0 ] && ok "$n (byte-for-byte)" || ko "$n (byte-for-byte)"; }
cd "$C/dm-ml"
run "verify_dataset" .venv/bin/python -m app.data.verify_dataset
run "pytest app/tests" .venv/bin/pytest -q -p no:warnings app/tests
run "generate_dataset --seed 42" .venv/bin/python -m app.data.generate_dataset --seed 42 --out "$TMP/d1"
same "Day 1 data" "$TMP/d1" "$C/Day 1/data" events.csv customers.csv orders.csv products.csv categories.csv metadata.json
for spec in "features:2:customer_features.csv" "training:3:training_dataset.csv leaky_training_dataset.csv" \
            "targeting:4:customer_profiles.csv campaigns.csv" "product_text:5:products_text.csv" \
            "interactions:6:interactions.csv" "evaluation:7:test_cases.csv comparison.csv" \
            "hybrid:8:candidates.csv ranking.csv comparison.csv" "session:9:impressions.csv ctr.csv comparison.csv" \
            "ai_comparison:11:comparison.csv"; do
  IFS=: read g d files <<< "$spec"; out="$TMP/d$d"
  extra=""; [ "$g" = ai_comparison ] && extra="--provider demo"
  run "generate_$g" .venv/bin/python -m app.data.generate_$g --out-dir "$out" $extra
  same "Day $d data" "$out" "$C/Day $d/data" $files
done
run "generate_embeddings --embedder auto" .venv/bin/python -m app.data.generate_embeddings --embedder auto --out-dir "$TMP/d10"
same "Day 10 data" "$TMP/d10" "$C/Day 10/data" embeddings.npz
for d in 1 2 3 4 5 6 7 8 9 10 11 12; do
  ( cd "../Day $d/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q -p no:warnings test_lab.py >"$TMP/o.txt" 2>&1 ) && ok "Day $d lab komanda" || ko "Day $d lab komanda"
done
cd "$C"
for f in Day\ */examples/*.py; do case "$f" in */demo_*|*/visualize_*|*/toy_sgd.py|*/mf_library.py) run "$f" dm-ml/.venv/bin/python "$f";; esac; done
# API: uvicorn + curl primeri iz lekcija
cd "$C/dm-ml"; .venv/bin/uvicorn app.main:app --port 3901 >"$TMP/uv.log" 2>&1 & UV=$!
for i in $(seq 60); do curl -sf http://127.0.0.1:3901/platform/modules >/dev/null && break; sleep 1; done
run "curl /platform/modules" bash -c "curl -sf http://127.0.0.1:3901/platform/modules | grep -q '\"total\":18'"
run "curl POST /ai/seo" bash -c "curl -sf -X POST http://127.0.0.1:3901/ai/seo -H 'Content-Type: application/json' -d '{\"product_name\": \"Smartphone Compact 686\", \"description\": \"5G smartphone with OLED display, dual camera and fast charging.\", \"category_name\": \"Electronics\"}' | grep -q 'Smartphone Compact 686 | Electronics'"
run "curl /recommendations/395" bash -c "curl -sf 'http://127.0.0.1:3901/recommendations/395?limit=3' | grep -q '\"product_id\":50'"
run "curl /recommendations/session/session_005246" bash -c "curl -sf 'http://127.0.0.1:3901/recommendations/session/session_005246?limit=3' | grep -q '\"product_id\":55'"
run "curl /search/semantic" bash -c "curl -sf 'http://127.0.0.1:3901/search/semantic?q=wireless%20earbuds%20for%20travel&limit=3' | grep -q 'Headphones Compact 103'"
run "curl /recommendations/content/1" bash -c "curl -sf 'http://127.0.0.1:3901/recommendations/content/1?limit=2' | grep -q '0.9145'"
run "curl /recommendations/collaborative/1" bash -c "curl -sf 'http://127.0.0.1:3901/recommendations/collaborative/1?limit=2' | grep -q '0.1362'"
kill $UV 2>/dev/null; wait $UV 2>/dev/null
echo; echo "passed=$pass failed=$fail"; rm -rf "$TMP"; [ $fail -eq 0 ]
