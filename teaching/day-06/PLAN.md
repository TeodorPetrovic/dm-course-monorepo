# Dan 6 — Collaborative preporuke (implicit feedback) (2 × 45 min)

Lekcija: `lessons/06-*.md`. Kucanje uživo: **72 linija** (algoritam 58, servis+API 12, frontend 2);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 3.4 s (sa kešom iz `teach.sh prepare`).
Procena: ≈36 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_interactions` 1.5 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/product/<slug> → „Customers Also Viewed“`; zatim `scripts/teach.sh start 6` i `scripts/teach.sh diff 6` (šta ćemo napisati).
- **5–17** Teorija:
   - interakciona matrica i težine (view/cart/purchase)
   - item-item kosinus
   - heuristika co-occurrence vs CF
- **17–40** Kucaj algoritam (A, 58 lin., ≈29 min):
   - `apps/api/app/recommenders/collaborative.py` → **build_interaction_matrix** (15 lin.)
   - `apps/api/app/recommenders/collaborative.py` → **calculate_item_similarity** (4 lin.)
   - `apps/api/app/recommenders/collaborative.py` → **recommend_from_item_similarity** (10 lin.)
   - `apps/api/app/recommenders/collaborative.py` → **recommend_session_cooccurrence** (12 lin.)
   - `apps/api/app/recommenders/collaborative.py` → **compare_heuristic_vs_cf** (4 lin.)
   - `apps/api/app/recommenders/collaborative.py` → **weight_sensitivity_experiment** (13 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 6/examples/demo_collaborative.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 6` za ceo dan.

## Čas 2 (0–45)
- **0–6** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **6–12** Servis + API (B, 12 lin.):
   - `apps/api/app/api/recommendation_routes.py` → **collab** (1 lin.)
   - `apps/api/app/services/collaborative.py` → **CollaborativeRecommenderService._interaction** (9 lin.)
   - `apps/api/app/services/collaborative.py` → **CollaborativeRecommenderService.collaborative_recommendations** (2 lin.)
- **12–15 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/recommendations/collaborative/1?limit=5'
```
- **15–16** Frontend deo (C, 2 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/product/[slug].vue` → **collaborative preporuke (item-item)** (2 lin.)
- **16–18 Checkpoint C**: otvori `/product/<slug> → „Customers Also Viewed“`.
- **18–40** Rezultati i diskusija: Težine događaja su ručne — weight_sensitivity pokazuje koliko menjaju rezultat.
- **40–45** Lab handoff: `course/Day 6/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `toy_sgd.py` (matrix factorization od nule, 0.2 s) — opciono
   - `mf_library.py` (implicit ALS)
   - `visualize_weights.py`

## Opcioni blokovi (`scripts/teach.sh start 6 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 6` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
