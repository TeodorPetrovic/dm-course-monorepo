# Dan 8 — Hibridni candidate-generation + ranking (2 × 45 min)

Lekcija: `lessons/08-*.md`. Kucanje uživo: **73 linija** (algoritam 39, servis+API 24, frontend 10);
opciono još 22 (`--full`). Izvršavanje primera + generatora ≈ 13.8 s (sa kešom iz `teach.sh prepare`).
Procena: ≈37 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_hybrid` 9.8 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/shop → Personalized (bedž „For you“) i /admin/recommendations/hybrid`; zatim `scripts/teach.sh start 8` i `scripts/teach.sh diff 8` (šta ćemo napisati).
- **5–17** Teorija:
   - kandidati iz više izvora, normalizacija skorova
   - spajanje sa težinama (heuristika, ne učenje)
   - poslovna pravila (kupljeno, dostupnost) i diverzifikacija
- **17–37** Kucaj algoritam (A, 39 lin., ≈20 min):
   - `apps/api/app/recommenders/hybrid.py` → **merge_candidates** (16 lin.)
   - `apps/api/app/recommenders/hybrid.py` → **apply_business_rules** (13 lin.)
   - `apps/api/app/recommenders/hybrid.py` → **HybridModels.recommend** (10 lin.)
- **37–45 Checkpoint A (+ pitanja)**:
```
   cd course && dm-ml/.venv/bin/python "Day 8/examples/demo_hybrid.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 8` za ceo dan.

## Čas 2 (0–45)
- **0–12** Servis + API (B, 24 lin.):
   - `apps/api/app/api/recommendation_routes.py` → **hybrid** (1 lin.)
   - `apps/api/app/services/hybrid.py` → **HybridRecommenderService.recommend_for_user** (23 lin.)
- **12–15 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/recommendations/395?limit=5'
curl -s localhost:3001/analytics/recommendations/hybrid
```
- **15–20** Frontend deo (C, 10 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/recommendations/hybrid.vue` → **user-based evaluacija hybrid vs izvori** (1 lin.)
   - `apps/frontend/app/pages/shop/index.vue` → **hybrid preporuke za korisnika -> lista ID-jeva + impresije** (6 lin.)
   - `apps/frontend/app/pages/shop/index.vue` → **personalizovan poredak (preporučeni prvi, ostali zadržavaju redosled)** (3 lin.)
- **20–22 Checkpoint C**: otvori `/shop → Personalized (bedž „For you“) i /admin/recommendations/hybrid`.
- **22–40** Rezultati i diskusija: Popularity pobeđuje hybrid po P@5 (0.071 vs 0.058), hybrid ima mnogo veći coverage (0.504 vs 0.032).
- **40–45** Lab handoff: `course/Day 8/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `normalize_scores`, `diversify_results` (opciono, --full)

## Opcioni blokovi (`scripts/teach.sh start 8 --full`)
   - `apps/api/app/recommenders/hybrid.py` → **normalize_scores** (9 lin.)
   - `apps/api/app/recommenders/hybrid.py` → **diversify_results** (13 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 8` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
