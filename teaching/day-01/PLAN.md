# Dan 1 — Praćenje događaja, analitika, sintetički generator (2 × 45 min)

Lekcija: `lessons/01-*.md`. Kucanje uživo: **76 linija** (algoritam 57, servis+API 9, frontend 10);
opciono još 34 (`--full`). Izvršavanje primera + generatora ≈ 11.5 s (sa kešom iz `teach.sh prepare`).
Procena: ≈37 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_dataset` 7.5 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/product/<slug> pa /admin/event (događaji iz lokalne baze)`; zatim `scripts/teach.sh start 1` i `scripts/teach.sh diff 1` (šta ćemo napisati).
- **5–17** Teorija:
   - 8 tipova događaja i šema (`create_event`)
   - funnel view→cart→purchase, konverzija, AOV po porudžbini
   - sintetički generator: sezonalnost, sesije, seed 42 (samo walk-through `generate_dataset.py`)
- **17–40** Kucaj algoritam (A, 57 lin., ≈28 min):
   - `apps/api/app/data/analytics.py` → **calculate_funnel_counts** (10 lin.)
   - `apps/api/app/data/analytics.py` → **calculate_conversion_rate** (2 lin.)
   - `apps/api/app/data/analytics.py` → **average_order_value** (5 lin.)
   - `apps/api/app/data/events.py` → **create_event** (22 lin.)
   - `apps/api/app/data/events.py` → **EventStore.save_event** (18 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 1/examples/demo_events.py"
   cd course && dm-ml/.venv/bin/python "Day 1/examples/demo_analytics.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 1` za ceo dan.

## Čas 2 (0–45)
- **0–5** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **5–9** Servis + API (B, 9 lin.):
   - `apps/api/app/api/event_routes.py` → **post_event** (6 lin.)
   - `apps/api/app/api/event_routes.py` → **conv_rate** (2 lin.)
   - `apps/api/app/api/event_routes.py` → **aov** (1 lin.)
- **9–12 Checkpoint B** (API sa --reload):
```
curl -s -X POST localhost:3001/events -H 'Content-Type: application/json' -d '{"event_type":"product_view","user_id":395,"user_session":"s1","product_id":1}'
curl -s localhost:3001/analytics/conversion-rate
curl -s localhost:3001/analytics/average-order-value
```
- **12–17** Frontend deo (C, 10 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/composables/trackEvent.ts` → **trackEvent -> POST /api/event/track (nikad ne ruši stranicu)** (10 lin.)
- **17–19 Checkpoint C**: otvori `/product/<slug> pa /admin/event (događaji iz lokalne baze)`.
- **19–40** Rezultati i diskusija: AOV = suma / broj porudžbina (893), ne po stavci (1 045).
- **40–45** Lab handoff: `course/Day 1/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `share_by_category` (opciono, --full)
   - Nitro ruta `server/api/event/track.post.ts` (opciono, --full; inače walk-through)

## Opcioni blokovi (`scripts/teach.sh start 1 --full`)
   - `apps/api/app/data/analytics.py` → **share_by_category** (10 lin.)
   - `apps/frontend/server/api/event/track.post.ts` → **validacija + upis u bazu + prosleđivanje u dm-ml** (24 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 1` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
