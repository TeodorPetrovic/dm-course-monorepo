# Day 7 podaci — evaluacioni derivati (test cases + comparison report)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `test_cases.csv` | evaluacioni slučajevi iz **test perioda** temporalnog splita: `session_id`, `query_product_id`, `target_product_ids`, `n_targets`, `query_time` | 2 803 |
| `comparison.csv` | P@K / R@K / HR@K / NDCG@K / coverage za popularity/category/content/collaborative | 4 |
| `metadata.json` | izvor, parametri splita, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (jedini izvor istine) + `Day 5/data/products_text.csv`
  (katalog).
* **Temporal split** (`temporal_split`, `app/recommenders/evaluation.py`): granica
  = kvantil 0.8 po broju događaja (`2026-01-26 11:21:20`); događaji pre granice
  = train (146 774), posle = test (36 694). **Nije random split** — random
  procuruje budućnost i lažno povećava metrike.
* **Test cases** (`extract_test_cases`): po sesiji iz test perioda,
  `query` = prvi *različiti* proizvod, `targets` = različiti proizvodi viđeni
  kasnije u istoj sesiji. Sesije sa < 2 različita proizvoda se izuzimaju (nemaju
  signal „šta sledeće").
* **Comparison** (`build_comparison_report`): svaki preporučivač se trenira
  SAMO na train događajima (npr. popularity iz train-a, ne iz `popularity`
  kolone kataloga koja je računata iz cele istorije — temporalni leakage).
* Generator: `app/data/generate_evaluation.py` (upisuje CSV + metadata).

## Ključne kolone (`test_cases.csv`)

| Kolona | Značenje |
| --- | --- |
| `session_id` | `user_session` (Day 1) — red evaluacionog slučaja |
| `query_product_id` | prvi proizvod koji sesija vidi u test periodu — ulaz u preporučivača |
| `target_product_ids` | proizvodi viđeni KASNIJE u istoj sesiji, `;`-spojeni — ground truth |
| `n_targets` | broj target proizvoda |
| `query_time` | timestamp prvog proizvoda (test period) |

## Stanje u ovom seed-u

* split\_time: **2026-01-26 11:21:20** (kvantil 0.8 događaja)
* train: **146 774** događaja · test: **36 694** događaja · test sesija: **3 121**
* evaluacionih slučajeva: **2 803**

Comparison (k=5):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| popularity | 0.082 | 0.079 | 0.335 | 0.097 | 0.024 |
| category | 0.245 | 0.298 | 0.675 | 0.345 | 0.286 |
| content | 0.069 | 0.073 | 0.279 | 0.094 | 1.000 |
| collaborative | 0.239 | 0.290 | 0.669 | 0.335 | 0.722 |

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_evaluation
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Metrike važe **za ovaj sintetički seed (42)** i **ovaj test period**; na pravom
store-u raspodela sesija/događaja je drugačija. `target_product_ids` je
*ponašanje sesije* (šta je gledala posle), ne dokaz preferencije. Bolji P@5
kategorije na ovom skupu ne znači da je category preporučivač „najbolji" —
coverage pokazuje da popularnost servira samo 2 % kataloga (popularity bias), a
content 100 % (preporučuje sve). Metrika je sočivo, ne presuda.
