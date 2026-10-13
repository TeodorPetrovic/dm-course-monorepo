# Digitalni marketing + ML — kurs (12 dana) — monorepo

Praktičan kurs: od praćenja događaja u e-prodavnici do integrisane AI marketing platforme.
Sve radi lokalno, nad **sintetičkim, determinističkim** podacima (seed 42) — bez prave baze i bez ličnih podataka.

| Dan | Tema | Klasa metode |
|---|---|---|
| 1 | Praćenje događaja, analitika, sintetički generator | data pipeline |
| 2 | Segmentacija kupaca (RFM + KMeans) | ML |
| 3 | Predikcija kupovine / konverzije | ML |
| 4 | ML-assisted targeting kampanja | ML + pravila |
| 5 | Content-based preporuke (TF-IDF) | statistička |
| 6 | Collaborative preporuke (implicit feedback, MF) | ML |
| 7 | Evaluacija preporuka (P@k, coverage) | evaluacija |
| 8 | Hibridni candidate-generation + ranking | heuristika |
| 9 | Session-aware preporuke i feedback loop (CTR) | statistička |
| 10 | Semantička pretraga i embedding preporuke | ML |
| 11 | Strukturisani generativni AI (SEO/sadržaj, validacija, retry, fail-safe) | generativni AI |
| 12 | Integrisana platforma (capstone) | integracija |

Lekcije su na srpskom (latinica), u `lessons/`.

## Struktura

```
apps/api/        dm-ml: FastAPI servis, ML servisi, recommenderi, generatori podataka (app/data), testovi (app/tests)
apps/frontend/   Nuxt 4 prodavnica/CMS (Bun/Nitro); /ml/** proxy -> API :3001; MySQL preko drizzle
course/Day N/    po danu: data/ (generisani CSV/JSON + README), examples/ (demo skripte), lab/ (starter, rešenje, testovi)
course/dm-ml ->  symlink na ../apps/api, da komande iz lekcija (`cd dm-ml`, `dm-ml/.venv/bin/python ...`) rade doslovno
lessons/         12 lekcija (Markdown)
db/              lokalna MariaDB (port 3307): šema, seed iz Day 1 CSV-ova, start/load skripte
scripts/         setup, regenerisanje podataka, provere (run_all, check_commands), frontend smoke, DeepSeek live check
```

Arhitektura: `generator (seed 42) -> course/Day N/data -> dm-ml servisi (trening na snapshot-u) -> FastAPI :3001 <- Nuxt :3000 (+ MariaDB :3307 za katalog/događaje)`.

## Pokretanje

Preduslovi: Python 3.11+ (testirano 3.13), Bun 1.x (ili Node 20+), MariaDB/MySQL server binarni fajlovi (za frontend), Linux/macOS
(symlink `course/dm-ml`; na Windows-u koristi WSL ili `git config core.symlinks true`).

```bash
scripts/setup.sh                 # venv u apps/api/.venv, zavisnosti, regeneriše Day 1 events.csv i proverava sha256
scripts/run_all.sh               # verify + pytest + svi primeri + svi labovi        (očekivano: 47/47 PASS)
scripts/check_commands.sh        # svaka komanda iz lekcija + bajt-identični podaci + curl ka API-ju (očekivano: 64/64)
scripts/regenerate_all.sh        # (opciono) ponovo generiše SVE podatke Day 1–12

# backend
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001

# lokalna baza + frontend (drugi terminal)
db/start_local_db.sh && db/load.sh                      # MariaDB 127.0.0.1:3307, baza dm_local
cd apps/frontend && bun install && bun run build
PORT=3000 bun .output/server/index.mjs                  # http://127.0.0.1:3000  (dev: bun run dev)

# end-to-end smoke (DB + API + Nuxt build + headless Chromium)
apps/api/.venv/bin/playwright install chromium          # jednom
apps/api/.venv/bin/python scripts/smoke_frontend.py     # očekivano: 42/42 PASS
```

Labovi (iz `course/`): `cd "Day 3/lab" && ../../dm-ml/.venv/bin/pytest -q test_lab.py` (tvoj `starter.py`),
`LAB_MODULE=reference_solutions ...` za referentno rešenje.

## AI režimi (Day 11): demo vs DeepSeek

* **demo / auto (podrazumevano, besplatno):** template ili scripted demo provider — deterministički, offline.
  Svi testovi, provere i izlazi u lekcijama koriste ovaj režim.
* **DeepSeek (pravi LLM):** `export AI_PROVIDER=deepseek DEEPSEEK_API_KEY=...` (model `deepseek-chat`, `https://api.deepseek.com`).
  > ⚠️ **Ovo je PLAĆENI API** — svaki poziv troši kredit na tvom DeepSeek nalogu. Izlazi se razlikuju od poziva do poziva.
  > Ključ drži samo u env-u ili u lokalnom `.env` (u `.gitignore`); nikad ga ne commit-uj.
  Validacija (JSON, polja, dužina, činjenice) i bounded retry važe i za pravi model; neuspeh -> template fallback.
  Live provera (~6 poziva): `cd apps/api && .venv/bin/python ../../scripts/deepseek_live_check.py`.

Vidi `.env.example` za sve promenljive. Kredencijali baze u primeru (`dm_local`/`dm_local`) su lažni, lokalni demo nalozi
koje pravi `db/start_local_db.sh` i važe samo na 127.0.0.1.

## Podaci

Sintetička prodavnica (3 000 kupaca, 183 468 događaja, 15 361 sesija, 893 porudžbine, konverzija 5.8%, AOV 106.81).
Emailovi su `@example.test`. `course/Day 1/data/events.csv` (17 MB) nije u repou — `scripts/setup.sh` ga regeneriše bajt-identično.

## Licenca

* **Lekcije i podaci** — `lessons/` i `course/*/data/`: [CC BY 4.0](LICENSE-CONTENT) (slobodno deljenje i prerada uz navođenje autora).
* **Sve ostalo** (kod: `apps/`, `db/`, `scripts/`, `course/*/examples/`, `course/*/lab/`): [MIT](LICENSE).

© 2026 Teodor Petrović
