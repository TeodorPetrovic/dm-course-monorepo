# Day 8 podaci — hybrid candidate/ranking derivati (candidates + ranking + comparison)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, težine, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `candidates.csv` | kandidati PO IZVORU (recall faza) za 5 demo korisnika: `user_id`, `source`, `product_id`, `score`, `rank_in_source` | 600 |
| `ranking.csv` | finalni hybrid ranking (posle merge/score/biznis pravila/raznovrsnosti) za iste korisnike | 25 |
| `comparison.csv` | **hybrid vs single-source** (user-based protokol): P@K / R@K / HR@K / NDCG@K / coverage | 5 |
| `metadata.json` | izvor, parametri, težine, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (istorija) + `Day 5/data/products_text.csv`
  (katalog).
* **Temporal split** (`temporal_split`, `app/recommenders/evaluation.py`):
  granica = kvantil 0.8 (`2026-01-30 15:26:05`); modeli se grade SAMO na train
  događajima (anti-leakage, Day 7 lekcija).
* **Candidates** (`generate_candidates`): popularity/category/content/
  collaborative — svaki izvor predlaže do 30 kandidata (retrieval je
  recall-orijentisan).
* **Ranking** (`recommend_for_user`): merge na normalizovanim skorovima
  (težine `0.2/0.3/0.3/0.2` — **heuristika, ne naučen odgovor**), rank, biznis
  pravila (dostupnost = slow movers se čiste, isključi viđeno/kupljeno),
  raznovrsnost (`max_per_category=2`).
* **Comparison** (`build_user_based_comparison`): test korisnici = sa istorijom
  u train i test periodu; `targets` = NOVI proizvodi iz test perioda (van
  train istorije). Metrike su Day 7 P@K/R@K/HR@K/NDCG@K + coverage.
* Generator: `app/data/generate_hybrid.py` (upisuje CSV + metadata).

## Ključne kolone (`ranking.csv`)

| Kolona | Značenje |
| --- | --- |
| `user_id` | korisnik (Day 1) — red evaluacije |
| `position` | finalna pozicija (1 = prva preporuka) |
| `product_id` | preporučeni proizvod |
| `name` | naziv (katalog) |
| `category_id` | kategorija (ulaz u raznovrsnost) |
| `score` | merged blended skor (Σ težina × normalizovani skor izvora) |
| `sources` | izvori koji su predložili proizvod, `;`-spojeni |

## Stanje u ovom seed-u

* split\_time: **2026-01-26 11:21:20** · train: **146 774** · test: **36 694**
* test korisnika (user-based protokol): **1 293** · demo korisnici:
  **395, 1465, 409, 1182, 2360**
* dostupnih proizvoda (biznis pravilo, kvantil 0.2 popularnosti): **201 / 252**

Comparison (user-based, k=5):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| hybrid | 0.058 | 0.054 | 0.240 | 0.064 | 0.504 |
| popularity | 0.071 | 0.053 | 0.289 | 0.079 | 0.032 |
| category | 0.044 | 0.040 | 0.180 | 0.049 | 0.294 |
| content | 0.044 | 0.038 | 0.190 | 0.053 | 0.794 |
| collaborative | 0.057 | 0.052 | 0.214 | 0.071 | 0.492 |

Iskren rezultat: na ovom seed-u hybrid (heuristične težine) **nije** bolji od
najboljeg pojedinačnog signala po preciznosti — vidi lekciju, „Šta rezultat NE dokazuje".

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_hybrid
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`). `candidates.csv` ne zavisi od biznis
pravila (sirovi kandidati), pa njegov sha256 ostaje isti i kad se pravila
promene — samo `ranking.csv`/`comparison.csv` reaguju.

## Šta ovi podaci NE dokazuju

* **Hybrid nije „najbolji" na svakoj metrici.** Na ovom seed-u category ima
  najviši P@5 (sesije ostaju u kategoriji — isto kao Day 7), a hybrid je
  drugi po preciznosti ali sa višim coverage-om (0.73 vs 0.65). To je
  *svojstvo ovog skupa*, ne opšta istina.
* **Težine merge-a su ručno birane.** `0.2/0.3/0.3/0.2` je heuristika; dok
  ranking model ne nauči težine, bolja hybrid metrika ne dokazuje da su težine
  „tačne".
* **Metrike su dataset-specifične** (sintetički seed 42, ovaj test period). Na
  pravom store-u raspodela je drugačija.
