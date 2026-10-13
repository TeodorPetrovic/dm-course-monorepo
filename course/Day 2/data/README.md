# Day 2 podaci — customer feature tabela (izvedena)

Deterministička, **byte-for-byte reproduktivna** feature tabela po korisniku,
**izvedena** iz Day 1 seeded događaja i porudžbina (ne duplira ih). Kompletna
dokumentacija (izvor, parametri, značenje polja, sha256) je u
`metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `customer_features.csv` | 3000 korisnika: RFM + brojači + AOV + konverzija + omiljena kategorija | 3000 |
| `metadata.json` | izvor, reference\_date, značenje polja, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` + `Day 1/data/orders.csv` (jedini izvor istine).
* Graditelj: `app/ml/features.build_customer_features` (ista funkcija koju koristi
  `POST /segments/train`).
* Generator: `app/data/generate_features.py` (samo upisuje CSV + metadata).
* `reference_date = 2026-01-31 23:24:05` — najskoriji događaj/porudžbina; recency
  se računa u odnosu na njega.

## Ključne kolone (značenje)

| Kolona | Značenje |
| --- | --- |
| `user_id` | FK -> `customers.user_id` |
| `recency_days` | dani od reference do poslednje kupovine (ili aktivnosti za ne-kupce) |
| `frequency` | broj porudžbina (0 za ne-kupce) |
| `monetary` | ukupna vrednost porudžbina (0.0 za ne-kupce) |
| `product_views` / `cart_adds` / `sessions` | brojači iz događaja |
| `aov` | prosečna porudžbina (0.0 za ne-kupce — bez deljenja sa nulom) |
| `conversion` | sesije sa kupovinom / sve sesije (0..1) |
| `favorite_category` | modus kategorije po pregledima (NaN ako ih nema) |

## Stanje u ovom seed-u

* korisnika: **3000**
* kupaca (frequency > 0): **583**
* zero-spend (monetary = 0): **2417**
* sa omiljenom kategorijom: **3000**

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_features --seed 42
```

Dva pokretanja sa istim seed-om daju identičan fajl (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Feature tabela je *ulaz* za segmentaciju, ne rezultat. Postojanje feature-a
ne znači da su segmenti „stvarni" — K-Means ih uči iz ovih brojeva (Day 2
README, „What the result does NOT prove").
