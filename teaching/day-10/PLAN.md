# Dan 10 — Semantička pretraga i embedding preporuke (2 × 45 min)

Lekcija: `lessons/10-*.md`. Kucanje uživo: **71 linija** (algoritam 29, servis+API 35, frontend 7);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 14.0 s (sa kešom iz `teach.sh prepare`).
Procena: ≈36 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_embeddings` 7.5 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/search?q=wireless earbuds`; zatim `scripts/teach.sh start 10` i `scripts/teach.sh diff 10` (šta ćemo napisati).
- **5–17** Teorija:
   - embedding = vektor značenja; normalizacija
   - brute-force najbliži susedi (kosinus)
   - keyword vs TF-IDF vs embedding
- **17–31** Kucaj algoritam (A, 29 lin., ≈14 min):
   - `apps/api/app/recommenders/embeddings.py` → **normalize** (6 lin.)
   - `apps/api/app/recommenders/embeddings.py` → **brute_force_nearest** (3 lin.)
   - `apps/api/app/recommenders/embeddings.py` → **HashEmbedder.encode** (1 lin.)
   - `apps/api/app/recommenders/embeddings.py` → **make_embedder** (9 lin.)
   - `apps/api/app/recommenders/embeddings.py` → **keyword_search** (10 lin.)
- **31–45 Checkpoint A (+ pitanja)**:
```
   cd course && dm-ml/.venv/bin/python "Day 10/examples/demo_semantic.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 10` za ceo dan.

## Čas 2 (0–45)
- **0–18** Servis + API (B, 35 lin.):
   - `apps/api/app/api/recommendation_routes.py` → **semantic_recs** (1 lin.)
   - `apps/api/app/api/recommendation_routes.py` → **semantic_search** (1 lin.)
   - `apps/api/app/services/semantic.py` → **SemanticService.semantic_search** (9 lin.)
   - `apps/api/app/services/semantic.py` → **SemanticService.recommendations_for_product** (6 lin.)
   - `apps/api/app/services/semantic.py` → **SemanticService.build_comparison** (18 lin.)
- **18–21 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/search/semantic?q=wireless%20earbuds%20for%20travel&limit=3'
curl -s 'localhost:3001/recommendations/semantic/1?limit=5'
```
- **21–25** Frontend deo (C, 7 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/product/[slug].vue` → **semantički slični proizvodi (embeddings)** (2 lin.)
   - `apps/frontend/app/pages/search.vue` → **semantička pretraga (GET /search/semantic)** (5 lin.)
- **25–27 Checkpoint C**: otvori `/search?q=wireless earbuds`.
- **27–40** Rezultati i diskusija: Embedding gubi na „fitness and training gear“ (vraća bicikle) — pokaži to.
- **40–45** Lab handoff: `course/Day 10/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - vežba: kategorija u embedding ulazu

## Opcioni blokovi (`scripts/teach.sh start 10 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 10` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
