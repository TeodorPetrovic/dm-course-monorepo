# Dan 9 — Session-aware preporuke i feedback loop (2 × 45 min)

Lekcija: `lessons/09-*.md`. Kucanje uživo: **74 linija** (algoritam 55, servis+API 15, frontend 4);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 3.7 s (sa kešom iz `teach.sh prepare`).
Procena: ≈38 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_session` 2.3 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/product/<slug> → „Based on your session“ i /admin/recommendations (CTR kartica)`; zatim `scripts/teach.sh start 9` i `scripts/teach.sh diff 9` (šta ćemo napisati).
- **5–17** Teorija:
   - signali tekuće sesije sa recency težinama
   - CTR po algoritmu i poziciji
   - simulacija popular vs personalized
- **17–40** Kucaj algoritam (A, 55 lin., ≈28 min):
   - `apps/api/app/recommenders/session.py` → **recency_weights** (1 lin.)
   - `apps/api/app/recommenders/session.py` → **recent_product_interest** (5 lin.)
   - `apps/api/app/recommenders/session.py` → **recent_category_interest** (5 lin.)
   - `apps/api/app/recommenders/session.py` → **recommendation_ctr** (1 lin.)
   - `apps/api/app/recommenders/session.py` → **_group_ctr** (7 lin.)
   - `apps/api/app/recommenders/session.py` → **session_features** (13 lin.)
   - `apps/api/app/recommenders/session.py` → **recommend_for_session** (23 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 9/examples/demo_session.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 9` za ceo dan.

## Čas 2 (0–45)
- **0–5** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **5–13** Servis + API (B, 15 lin.):
   - `apps/api/app/api/analytics_routes.py` → **rec_ctr** (1 lin.)
   - `apps/api/app/api/recommendation_routes.py` → **session_recs** (1 lin.)
   - `apps/api/app/services/session.py` → **SessionRecommenderService.recommend_for_session** (13 lin.)
- **13–16 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/recommendations/session/session_005246?limit=5'
curl -s localhost:3001/analytics/recommendations/ctr
```
- **16–18** Frontend deo (C, 4 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/recommendations/index.vue` → **CTR dashboard + popular vs personalized** (2 lin.)
   - `apps/frontend/app/pages/product/[slug].vue` → **preporuke na osnovu tekuće sesije** (2 lin.)
- **18–20 Checkpoint C**: otvori `/product/<slug> → „Based on your session“ i /admin/recommendations (CTR kartica)`.
- **20–40** Rezultati i diskusija: Impression log je simuliran — CTR razlike su ilustracija, ne A/B test.
- **40–45** Lab handoff: `course/Day 9/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - vežba: drugačiji half-life

## Opcioni blokovi (`scripts/teach.sh start 9 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 9` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
