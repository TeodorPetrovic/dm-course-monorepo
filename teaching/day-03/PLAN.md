# Dan 3 — Predikcija konverzije (2 × 45 min)

Lekcija: `lessons/03-*.md`. Kucanje uživo: **74 linija** (algoritam 49, servis+API 18, frontend 7);
opciono još 23 (`--full`). Izvršavanje primera + generatora ≈ 4.5 s (sa kešom iz `teach.sh prepare`).
Procena: ≈37 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_training` 2.1 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/admin/conversion → Treniraj, GET probability`; zatim `scripts/teach.sh start 3` i `scripts/teach.sh diff 3` (šta ćemo napisati).
- **5–17** Teorija:
   - vremenski cutoff i prozor (bez curenja budućnosti)
   - logistička regresija vs majority baseline
   - precision/recall/F1 kad je klasa retka (~6%)
- **17–40** Kucaj algoritam (A, 49 lin., ≈24 min):
   - `apps/api/app/ml/conversion.py` → **build_training_dataset** (16 lin.)
   - `apps/api/app/ml/conversion.py` → **split_dataset** (5 lin.)
   - `apps/api/app/ml/conversion.py` → **train_conversion_model** (7 lin.)
   - `apps/api/app/ml/conversion.py` → **_metrics** (10 lin.)
   - `apps/api/app/ml/conversion.py` → **majority_class_baseline** (5 lin.)
   - `apps/api/app/ml/conversion.py` → **predict_conversion_probability** (6 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 3/examples/demo_conversion.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 3` za ceo dan.

## Čas 2 (0–45)
- **0–1** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **1–10** Servis + API (B, 18 lin.):
   - `apps/api/app/api/conversion_routes.py` → **conv_train** (5 lin.)
   - `apps/api/app/api/conversion_routes.py` → **conv_prob** (1 lin.)
   - `apps/api/app/services/conversion.py` → **ConversionService.get_customer_probability** (12 lin.)
- **10–13 Checkpoint B** (API sa --reload):
```
curl -s -X POST localhost:3001/models/conversion/train -H 'Content-Type: application/json' -d '{}'
curl -s localhost:3001/customers/395/conversion-probability
```
- **13–17** Frontend deo (C, 7 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/conversion/index.vue` → **POST /models/conversion/train** (4 lin.)
   - `apps/frontend/app/pages/admin/conversion/index.vue` → **verovatnoća kupovine za korisnika** (3 lin.)
- **17–19 Checkpoint C**: otvori `/admin/conversion → Treniraj, GET probability`.
- **19–40** Rezultati i diskusija: Accuracy baseline-a je visok zbog retke klase — gledamo recall/F1.
- **40–45** Lab handoff: `course/Day 3/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `ConversionService.train` (opciono, --full; inače walk-through)
   - leakage vežba (`run_leakage_exercise`) — domaći
   - `visualize_confusion.py`

## Opcioni blokovi (`scripts/teach.sh start 3 --full`)
   - `apps/api/app/services/conversion.py` → **ConversionService.train** (23 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 3` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
