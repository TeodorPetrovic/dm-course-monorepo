# Dan 12 — Integrisana platforma (capstone) (2 × 45 min)

Lekcija: `lessons/12-*.md`. Kucanje uživo: **78 linija** (algoritam 66, servis+API 5, frontend 7);
opciono još 15 (`--full`). Izvršavanje primera + generatora ≈ 21.1 s (sa kešom iz `teach.sh prepare`).
Procena: ≈39 min kucanja od 90 → **staje: da**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: `generate_platform` 10.1 s. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `/ (početna: hero + profil + preporuke) i /product/<slug> (Platform sekcija)`; zatim `scripts/teach.sh start 12` i `scripts/teach.sh diff 12` (šta ćemo napisati).
- **5–17** Teorija:
   - orkestracija modula sa fallback-om po modulu
   - profil korisnika iz Day 2–4 modela
   - homepage/product payload za CMS
- **17–40** Kucaj algoritam (A, 66 lin., ≈33 min):
   - `apps/api/app/services/platform.py` → **IntegratedPlatformService.profile_for_user** (26 lin.)
   - `apps/api/app/services/platform.py` → **IntegratedPlatformService.homepage_payload** (28 lin.)
   - `apps/api/app/services/platform.py` → **IntegratedPlatformService.product_page_payload** (12 lin.)
- **40–45 Rezime + pitanja (Checkpoint A pomeren na početak časa 2)**:
```
   cd course && dm-ml/.venv/bin/python "Day 12/examples/demo_platform.py"
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution 12` za ceo dan.

## Čas 2 (0–45)
- **0–10** Završi algoritam (ostatak A), pa odmah Checkpoint A.
- **10–12** Servis + API (B, 5 lin.):
   - `apps/api/app/api/platform_routes.py` → **p_home** (1 lin.)
   - `apps/api/app/api/platform_routes.py` → **p_product** (4 lin.)
- **12–15 Checkpoint B** (API sa --reload):
```
curl -s 'localhost:3001/platform/homepage?user_id=395&session_id=session_005246&limit=5'
curl -s localhost:3001/platform/modules
```
- **15–19** Frontend deo (C, 7 lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
   - `apps/frontend/app/pages/index.vue` → **personalizovana početna (GET /platform/homepage)** (6 lin.)
   - `apps/frontend/app/pages/product/[slug].vue` → **platform payload (AI opis + module_class)** (1 lin.)
- **19–21 Checkpoint C**: otvori `/ (početna: hero + profil + preporuke) i /product/<slug> (Platform sekcija)`.
- **21–40** Rezultati i diskusija: Modul status pokazuje koji moduli rade; trening Day 2/3 modela je preduslov za pun profil.
- **40–45** Lab handoff: `course/Day 12/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
   - `_available` (opciono, --full)
   - završna diskusija: šta je ML, šta heuristika

## Opcioni blokovi (`scripts/teach.sh start 12 --full`)
   - `apps/api/app/services/platform.py` → **IntegratedPlatformService._available** (15 lin.)

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution 12` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
