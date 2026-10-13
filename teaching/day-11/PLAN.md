# Dan 11 — Strukturisani generativni AI (2 × 45 min)

Lekcija: `lessons/11-*.md`. Kucanje uživo: **75 linija** (algoritam 67, servis+API 4, frontend 4);
opciono još 7 (`--full`). Izvršavanje primera + generatora ≈ 1.5 s (sa kešom iz `teach.sh prepare`).
Procena: ≈38 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: —. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/admin/ai → Generate SEO`; zatim `scripts/teach.sh start 11` i `scripts/teach.sh diff 11` (šta ćemo napisati).
- **5–17** Teorija:
   - strukturisan izlaz (JSON šema), validacija dužine i činjenica
   - bounded retry i template fallback
   - demo vs pravi provider (DeepSeek je PLAĆEN)
- **17–40** Kucaj algoritam (A, 67 lin., ≈34 min):
   - `apps/api/app/services/ai.py` → **parse_json_output** (11 lin.)
   - `apps/api/app/services/ai.py` → **validate_required_fields** (3 lin.)
   - `apps/api/app/services/ai.py` → **validate_length** (1 lin.)
   - `apps/api/app/services/ai.py` → **validate_product_facts** (6 lin.)
   - `apps/api/app/services/ai.py` → **validate_generated_output** (7 lin.)
   - `apps/api/app/services/ai.py` → **generate_with_retry** (17 lin.)
   - `apps/api/app/services/ai.py` → **AIService.generate_seo_metadata** (22 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 11/examples/demo_generative.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 11` za ceo dan.

## Čas 2 (0–45)
- **0–11** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **11–13** Servis + API (B, 4 lin.):
   - `apps/api/app/api/ai_routes.py` → **ai_seo** (4 lin.)
- **13–16 Checkpoint B** (API sa --reload):
```
curl -s -X POST localhost:3001/ai/seo -H 'Content-Type: application/json' -d '{"product_name":"Smartphone Compact 686","description":"5G smartphone with OLED display.","category_name":"Electronics"}'
```
- **16–18** Frontend deo (C, 4 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/admin/ai/index.vue` → **POST /ai/seo (validacija + fallback su u API-ju)** (4 lin.)
- **18–20 Checkpoint C**: otvori `/admin/ai → Generate SEO`.
- **20–40** Rezultati i diskusija: Demo režim je deterministički; pravi LLM ponekad izostavi kategoriju → validacija + retry.
- **40–45** Lab handoff: `course/Day 11/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `ExternalProvider.generate` (opciono, --full)
   - uživo DeepSeek: `AI_PROVIDER=deepseek` (~3 poziva, plaćeno; izlaz varira)

## Opcioni blokovi (`scripts/teach.sh start 11 --full`)
   - `apps/api/app/services/ai.py` → **ExternalProvider.generate** (7 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 11` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
