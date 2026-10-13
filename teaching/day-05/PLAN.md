# Dan 5 — Content-based preporuke (TF-IDF) (2 × 45 min)

Lekcija: `lessons/05-*.md`. Kucanje uživo: **59 linija** (algoritam 47, servis+API 10, frontend 2);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 2.5 s (sa kešom iz `teach.sh prepare`).
Procena: ≈30 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_product_text` 1.4 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/product/<slug> → sekcija „Recommended Products“`; zatim `scripts/teach.sh start 5` i `scripts/teach.sh diff 5` (šta ćemo napisati).
- **5–17** Teorija:
   - popularity i same-category baseline
   - TF-IDF + kosinusna sličnost
   - envelope odgovora (fallback, reason)
- **17–40** Kucaj algoritam (A, 47 lin., ≈24 min):
   - `apps/api/app/recommenders/content.py` → **popularity_from_events** (5 lin.)
   - `apps/api/app/recommenders/content.py` → **recommend_popular** (5 lin.)
   - `apps/api/app/recommenders/content.py` → **recommend_same_category** (8 lin.)
   - `apps/api/app/recommenders/content.py` → **prepare_product_text** (8 lin.)
   - `apps/api/app/recommenders/content.py` → **build_tfidf_matrix** (4 lin.)
   - `apps/api/app/recommenders/content.py` → **calculate_product_similarity** (3 lin.)
   - `apps/api/app/recommenders/content.py` → **recommend_similar_products** (14 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 5/examples/demo_content_recommender.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 5` za ceo dan.

## Čas 2 (0–45)
- **0–1** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **1–6** Servis + API (B, 10 lin.):
   - `apps/api/app/api/recommendation_routes.py` → **content** (1 lin.)
   - `apps/api/app/services/recommender.py` → **RecommenderService.content_recommendations** (1 lin.)
   - `apps/api/app/services/recommender.py` → **RecommenderService.baseline_comparison** (8 lin.)
- **6–9 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/recommendations/content/1?limit=5'
curl -s localhost:3001/recommendations/content/1/comparison
```
- **9–10** Frontend deo (C, 2 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/product/[slug].vue` → **content-based preporuke (TF-IDF)** (2 lin.)
- **10–12 Checkpoint C**: otvori `/product/<slug> → sekcija „Recommended Products“`.
- **12–40** Rezultati i diskusija: Dan je lakši (≈60 linija) — ostatak vremena za lab u učionici.
- **40–45** Lab handoff: `course/Day 5/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `visualize_content.py` (heatmap)
   - vežba: min_df / bigrami

## Opcioni blokovi (`scripts/teach.sh start 5 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 5` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
