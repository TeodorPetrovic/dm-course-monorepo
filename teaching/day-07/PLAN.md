# Dan 7 — Evaluacija preporuka (2 × 45 min)

Lekcija: `lessons/07-*.md`. Kucanje uživo: **66 linija** (algoritam 60, servis+API 5, frontend 1);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 15.7 s (sa kešom iz `teach.sh prepare`).
Procena: ≈32 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_evaluation` 6.9 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/admin/recommendations → tabela evaluacije`; zatim `scripts/teach.sh start 7` i `scripts/teach.sh diff 7` (šta ćemo napisati).
- **5–17** Teorija:
   - temporalni split (bez curenja)
   - P@K, recall@K, hit rate, NDCG, coverage
   - poređenje metoda na istim test slučajevima
- **17–40** Kucaj algoritam (A, 60 lin., ≈30 min):
   - `apps/api/app/recommenders/evaluation.py` → **precision_at_k** (4 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **recall_at_k** (4 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **hit_rate_at_k** (2 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **ndcg_at_k** (6 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **catalog_coverage** (3 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **temporal_split** (3 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **extract_test_cases** (13 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **make_popularity_predictor** (2 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **make_category_predictor** (4 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **evaluate_recommender** (10 lin.)
   - `apps/api/app/recommenders/evaluation.py` → **build_comparison_report** (9 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 7/examples/demo_evaluation.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 7` za ceo dan.

## Čas 2 (0–45)
- **0–7** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **7–9** Servis + API (B, 5 lin.):
   - `apps/api/app/api/analytics_routes.py` → **rec_eval** (5 lin.)
- **9–12 Checkpoint B** (API sa --reload):
```
curl -s localhost:3001/analytics/recommendations
```
- **12–12** Frontend deo (C, 1 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/recommendations/index.vue` → **offline evaluacija (P@K, recall, NDCG, coverage)** (1 lin.)
- **12–14 Checkpoint C**: otvori `/admin/recommendations → tabela evaluacije`.
- **14–40** Rezultati i diskusija: Kategorija je najbolja po P@5 (0.245), collaborative 0.239, content najslabiji (0.069).
- **40–45** Lab handoff: `course/Day 7/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `make_content_predictor` / `make_collaborative_predictor` — walk-through
   - `visualize_comparison.py`

## Opcioni blokovi (`scripts/teach.sh start 7 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 7` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
