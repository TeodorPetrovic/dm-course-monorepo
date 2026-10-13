# Day 3 podaci — labeled training dataset za predikciju kupovine

Deterministički, **byte-for-byte reproduktivni** labeled training dataset,
**izveden** iz Day 1 seeded događaja i porudžbina (ne duplira ih). Kompletna
dokumentacija (izvor, parametri, značenje polja, sha256) je u
`metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `training_dataset.csv` | **clean** verzija: feature-i po korisniku **pre** cut-off-a + labela `will_purchase` (kupovina u 7-dnevnom window-u) | 2579 |
| `leaky_training_dataset.csv` | **leaky** verzija: feature-i iz CELE istorije (uključujući window — namerni bug) + ista labela | 3000 |
| `leakage_metrics.json` | before/after metrike: isti model, isti split, clean vs leaky | — |
| `metadata.json` | izvor, cutoff/reference, značenja polja, counts, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` + `Day 1/data/orders.csv` (jedini izvor istine).
* Graditelj: `app.ml.conversion.build_training_dataset` (ista funkcija koju koristi
  `POST /models/conversion/train`).
* Generator: `app/data/generate_training.py` (upisuje CSV + leakage + metadata).
* `reference_date = 2026-01-31 23:24:05`, `cutoff_date = 2026-01-24 23:24:05`
  (window = poslednjih 7 dana dataset-a).

## Labela i window (definicije)

* **cutoff** = `reference − window_days` = `2026-01-24 23:24:05`.
* **Labela** `will_purchase`: 1 ako je korisnik kupio u `[cutoff, reference]`,
  inače 0.
* **Clean feature-i** se računaju SAMO na događajima/porudžbinama **pre**
  cut-off-a (recency u odnosu na cutoff) — model ne vidi period koji predviđa.
* **Leaky feature-i** se računaju na celoj istoriji: `recency_days` direktno
  kodira labelu (kupac u window-u ima recency 0–6), `frequency`/`monetary`/
  `conversion` uključuju window kupovine. Ovo je namerni bug za vežbu.

## Stanje u ovom seed-u (window = 7 dana)

* clean: **2579** korisnika (aktivni pre cut-off-a), **163** kupaca u window-u (pozitivna stopa **0.063**)
* leaky: **3000** korisnika, **175** kupaca u window-u

## Leakage (before/after) — logistic\_regression, test\_size 0.3

| Verzija | Accuracy | Precision | Recall | F1 | Confusion matrix |
| --- | --- | --- | --- | --- | --- |
| **clean** (feature-i pre cut-off-a) | 0.9393 | 0.6250 | 0.1020 | 0.1754 | [[722, 3], [44, 5]] |
| **leaky** (feature-i iz cele istorije) | 0.9742 | 0.9143 | 0.6531 | 0.7619 | [[722, 3], [17, 32]] |

Leaky model izgleda daleko bolje (`ΔF1 = +0.587`) jer **vara** — feature-i vide
kupovine iz samog window-a koji predviđa. Clean model ima nizak recall: pozitivna
klasa je retka (≈ 6.3 %), pa je ovo realan, težak problem — ne bug.
Test skup: **774** korisnika (`test_size` 0.3, `random_state` 42).

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_training --seed 42
```

Dva pokretanja sa istim seed-om daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Labela i feature-i su *ulaz* za model, ne rezultat. Visoke metrike leaky
verzije ne znače da je model „dobar" — znače da je pokvaren (vidi
`leakage_metrics.json`). Ni clean metrike (F1 ≈ 0.05–0.16) ne znače da je
predikcija „nemoguća" — znače da je na ovom sintetičkom skupu signal slab
(vidi Day 3 README, „What the result does NOT prove").
