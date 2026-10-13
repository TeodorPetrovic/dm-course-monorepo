# Day 4 podaci — targeting profili i kampanje (izvedene tabele)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja i porudžbina (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `customer_profiles.csv` | 2579 korisnika (čista istorija): K-Means segment + RFM bucket + verovatnoća kupovine + vrednost + RFM komponente | 2579 |
| `campaigns.csv` | 4 seeded kampanje sa pravilima (ciljani segmenti, bucket-i, pragovi, cene, limita) | 4 |
| `metadata.json` | izvor, cutoff/reference, counts, značenja polja, sha256 | — |

## Kako nastaju (izvedene tabele)

* Ulaz: `Day 1/data/events.csv` + `Day 1/data/orders.csv` (jedini izvor istine).
* Graditelj profila: `app.data.generate_targeting.build_targeting_profile` —
  iste funkcije kao Day 2/3 (isti seed **42**, `k=4`, `logistic_regression`):
  + **Verovatnoća** — clean training dataset (labela iz 7-dnevnog window-a) →
    split → skaliranje (fit na trening) → logistic regression → verovatnoće na
    **čistoj** istoriji (feature-i pre cut-off-a).
  + **Segment** — K-Means (k=4) nad skaliranim feature-ima cele istorije.
  + **RFM bucket** — `manual_rfm_buckets` (pravilo, bez ML-a).
* Generator: `app/data/generate_targeting.py` (upisuje CSV + metadata).
* Kampanje: `app/data/campaigns.py` (jedini izvor definicija kampanja).
* `reference_date = 2026-01-31 23:24:05`, `cutoff_date = 2026-01-24 23:24:05`.

## Ključne kolone (`customer_profiles.csv`)

| Kolona | Značenje |
| --- | --- |
| `user_id` | FK -> `customers.user_id` |
| `segment` | K-Means labela (segment\_0..3; Day 2, k=4, seed 42) |
| `rfm_bucket` | ručni RFM bucket (champions/loyal/at\_risk/dormant; pravilo) |
| `probability` | P(kupovina u window-u) iz Day 3 modela (logistic, seed 42) |
| `monetary` | ukupna vrednost porudžbina (istorijska vrednost korisnika) |
| `frequency` / `recency_days` | broj porudžbina / dani od reference do poslednje kupovine |
| `aov` / `conversion` | prosečna porudžbina / sesije sa kupovinom |
| `favorite_category` | modus kategorije po pregledima (NaN ako ih nema) |

## Stanje u ovom seed-u

* korisnika sa istorijom pre cut-off-a: **2579** (od 3000)
* kupaca (monetary > 0): **571**
* po RFM bucket-u: `dormant` 1623 · `at_risk` 716 · `loyal` 159 · `champions` 81
* po K-Means segmentu: `segment_1` 1468 · `segment_0` 720 · `segment_3` 344 · `segment_2` 47
* prosek verovatnoće po bucket-u: champions **0.290** · loyal **0.168** · at\_risk **0.072** · dormant **0.037**
  (Day 2/3 README imaju modele i metrike).

## Kampanje (`campaigns.csv`)

| ID | Naziv | Ciljani segmenti | Dozvoljeni bucketi | Prag P | Cena | Max kontakti |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | VIP reaktivacija | segment\_2, segment\_3 | champions, loyal | 0.20 | 0.5 | 200 |
| 2 | At-risk win-back | segment\_0 | at\_risk | 0.15 | 0.3 | 300 |
| 3 | Široka visoko-vrednosna | — (svi) | champions, loyal, at\_risk | 0.10 | 0.2 | 500 |
| 4 | Dormant re-engage (pravila) | — (svi) | dormant | 0.00 | 0.1 | 150 |

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_targeting --seed 42
```

Dva pokretanja sa istim seed-om daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Profil je *ulaz* za targeting, ne rezultat. Visoka prosečna verovatnoća u
champions bucket-u ne znači „pošalji svima" — to je predikcija, a odluka zavisi
od pravila (cena, kapacitet, budžet) i vrednosti korisnika (vidi Day 4 README,
„What the result does NOT prove"). Segmenti i verovatnoće su računati na
sintetičkom seed-u (42); na pravom store-u raspodela je drugačija.
