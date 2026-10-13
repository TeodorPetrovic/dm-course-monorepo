# Dan 4 — ML-assisted targeting kampanja (2 × 45 min)

Lekcija: `lessons/04-*.md`. Kucanje uživo: **76 linija** (algoritam 48, servis+API 26, frontend 2);
opciono još 0 (`--full`). Izvršavanje primera + generatora ≈ 6.3 s (sa kešom iz `teach.sh prepare`).
Procena: ≈38 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_targeting` 3.9 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/admin/campaigns → Prikaži publiku (ML/Rule)`; zatim `scripts/teach.sh start 4` i `scripts/teach.sh diff 4` (šta ćemo napisati).
- **5–17** Teorija:
   - skor odluke = P(kupovina) × vrednost − trošak kontakta
   - selekcija pod budžetom (max_contacts) i rangiranje
   - rule baseline i poređenje (lift, overlap)
- **17–40** Kucaj algoritam (A, 48 lin., ≈24 min):
   - `apps/api/app/ml/targeting.py` → **score_customer** (9 lin.)
   - `apps/api/app/ml/targeting.py` → **select_target_customers** (14 lin.)
   - `apps/api/app/ml/targeting.py` → **rank_target_customers** (14 lin.)
   - `apps/api/app/ml/targeting.py` → **compare_rule_vs_ml** (11 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 4/examples/demo_targeting.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 4` za ceo dan.

## Čas 2 (0–45)
- **0–1** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **1–14** Servis + API (B, 26 lin.):
   - `apps/api/app/api/campaign_routes.py` → **audience** (1 lin.)
   - `apps/api/app/services/targeting.py` → **TargetingService.recommended_audience** (25 lin.)
- **14–17 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/campaigns/1/recommended-audience?mode=ml&limit=5'
curl -s localhost:3001/campaigns/1/targeting-comparison
```
- **17–18** Frontend deo (C, 2 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/campaigns/index.vue` → **publika (ml|rule) + rule vs ML poređenje** (2 lin.)
- **18–20 Checkpoint C**: otvori `/admin/campaigns → Prikaži publiku (ML/Rule)`.
- **20–40** Rezultati i diskusija: ML publika je manja (lift 0.18–0.90 po broju), ali ima veći prosečni P i profit po kontaktu.
- **40–45** Lab handoff: `course/Day 4/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `evaluate_campaign_rules` — walk-through (32 linije, ne kuca se)
   - `visualize_targeting.py`

## Opcioni blokovi (`scripts/teach.sh start 4 --full`)
   - (nema)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 4` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
