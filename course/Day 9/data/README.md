# Day 9 podaci — experiment-ready impression log (popular vs personalized)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, klik-model, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `impressions.csv` | experiment log: impresije oba algoritma (`popular`/`personalized`) po sesiji, sa SIMULIRANIM klikom | 2000 |
| `ctr.csv` | CTR po algoritmu i po poziciji (`level`, `group`, `impressions`, `clicks`, `ctr`) | 7 |
| `comparison.csv` | **popular vs personalized** (`algorithm`, `impressions`, `clicks`, `ctr`) | 2 |
| `metadata.json` | izvor, parametri, klik-model, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (istorija) + `Day 5/data/products_text.csv`
  (katalog).
* Uzorak: **200 sesija** sa ≥ 2 proizvodna događaja (deterministički,
  `numpy.random.default_rng(42)`, bez ponavljanja).
* Za svaku sesiju, oba algoritma loguju `k=5` impresija:
  + `popular` — globalni popularity top-5 (bez proizvoda koje je sesija već
    videla);
  + `personalized` — `recommend_for_session` (session-aware, recency-weighted
    interes, bez već viđenih).
* **Klik je SIMULIRAN** klik-modelom iz `metadata.json → click_model`:
  + personalized: viši `base` (0.06) ako je proizvod u top-2 kategorijama
    sesije, inače 0.02;
  + popular: base 0.02;
  + oba algoritma: position-bias (`position_factors = [1.0, 0.6, 0.4, 0.3, 0.2]`).
* Generator: `app/data/generate_session.py` (upisuje CSV + metadata).

## Ključne kolone (`impressions.csv`)

| Kolona | Značenje |
| --- | --- |
| `session_id` | sesija (Day 1) — jedinica eksperimenta |
| `algorithm` | `popular` ili `personalized` (pod kojim algoritmom je impresija logovana) |
| `position` | pozicija preporuke (1 = prva) — position-bias |
| `product_id` | preporučeni proizvod |
| `name` | naziv (katalog) |
| `category_id` | kategorija proizvoda |
| `session_top_category` | da li je proizvod u top-2 kategorijama sesije (dijagnostika) |
| `clicked` | 0/1 — SIMULIRAN klik (seed 42, klik-model u metadata) |

## Stanje u ovom seed-u

| Algoritam | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| **popular** | 1000 | 11 | **0.011** |
| **personalized** | 1000 | 22 | **0.022** |

CTR po poziciji (position-bias — prva pozicija nosi više klikova):

| Pozicija | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| 1 | 400 | 16 | 0.0400 |
| 2 | 400 | 5 | 0.0125 |
| 3 | 400 | 7 | 0.0175 |
| 4 | 400 | 5 | 0.0125 |
| 5 | 400 | 0 | 0.0000 |

Klikovi su **simulirani** (click\_model u `metadata.json`); na ovako malom uzorku
(2000 impresija) kriva po poziciji je bučna — na pravom store-u treba više impresija.

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_session
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

* **CTR razlika NIJE statistički potvrđen A/B rezultat.** Klikovi su SIMULIRANI
  determinističkim klik-modelom; na pravom store-u treba ti pravi eksperiment
  (logovanje impresija/klikova kroz `POST /recommendations/events` i dovoljno
  saobraćaja). Day 9 proizvodi *prikupljanje podataka* za taj eksperiment
  (experiment-ready), ne značajnosni test.
* **Personalized nije "dokazano bolji".** Na ovom simuliranom logu
  `personalized` ima viši CTR jer mu je klik-model favorabilniji za
  session-relevantne proizvode — to je MODEL, ne stvarno ponašanje korisnika.
* **Position-bias je realan, ali su klikovi simulirani.** Prava raspodela po
  pozicijama zavisi od saobraćaja i UI-ja; logovana pozicija je ono što meriš.
