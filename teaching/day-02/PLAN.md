# Dan 2 — Segmentacija kupaca (RFM + K-Means) (2 × 45 min)

Lekcija: `lessons/02-*.md`. Kucanje uživo: **75 linija** (algoritam 47, servis+API 22, frontend 6);
opciono još 14 (`--full`). Izvršavanje primera + generatora ≈ 3.5 s (sa kešom iz `teach.sh prepare`).
Procena: ≈38 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_features` 1.6 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/admin/segments → Treniraj`; zatim `scripts/teach.sh start 2` i `scripts/teach.sh diff 2` (šta ćemo napisati).
- **5–17** Teorija:
   - RFM i skaliranje (zašto StandardScaler)
   - K-Means, izbor k (silhouette)
   - profil segmenta = čitljiv opis, ne ID
- **17–40** Kucaj algoritam (A, 47 lin., ≈24 min):
   - `apps/api/app/ml/features.py` → **calculate_rfm** (33 lin.)
   - `apps/api/app/ml/segmentation.py` → **train_segmentation_model** (8 lin.)
   - `apps/api/app/ml/segmentation.py` → **assign_segment** (6 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 2/examples/demo_segmentation.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 2` za ceo dan.

## Čas 2 (0–45)
- **0–1** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **1–12** Servis + API (B, 22 lin.):
   - `apps/api/app/api/segment_routes.py` → **seg_train** (2 lin.)
   - `apps/api/app/api/segment_routes.py` → **segments** (1 lin.)
   - `apps/api/app/api/segment_routes.py` → **cust_segment** (1 lin.)
   - `apps/api/app/services/segmentation.py` → **SegmentationService.train** (18 lin.)
- **12–15 Checkpoint B** (API sa --reload):
```
curl -s -X POST localhost:3001/segments/train -H 'Content-Type: application/json' -d '{"k":4}'
curl -s localhost:3001/customers/395/segment
```
- **15–18** Frontend deo (C, 6 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/segments/index.vue` → **učitaj segmente (503 = model nije treniran)** (2 lin.)
   - `apps/frontend/app/pages/admin/segments/index.vue` → **POST /segments/train** (4 lin.)
- **18–20 Checkpoint C**: otvori `/admin/segments → Treniraj`.
- **20–40** Rezultati i diskusija: Većina kupaca nema kupovinu → jedan veliki „dormant“ segment je očekivan.
- **40–45** Lab handoff: `course/Day 2/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `profile_segments` (opciono, --full)
   - `visualize_clusters.py` (PCA slika)
   - manual RFM vs K-Means (ARI)

## Opcioni blokovi (`scripts/teach.sh start 2 --full`)
   - `apps/api/app/ml/segmentation.py` → **profile_segments** (14 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 2` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
