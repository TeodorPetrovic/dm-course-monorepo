# Lab — Dan 7: ranking metrike i temporal split

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/evaluation.py` već sadrži (da bi razumeo *šta* te
metrike rade). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` — `dm-ml/.venv` ih ima.
* Lab radi na malim, ručno napravljenim listama — nema seeded CSV-a.

## Zadatak (koraci)

Implementiraj čiste funkcije nad listama ID-jeva (`ranked_ids` = redosled
preporuka, `relevant_ids` = ground truth — šta je sesija stvarno radila kasnije).

1. **`precision_at_k(ranked_ids, relevant_ids, k)`** — P@K = `|relevant ∩ top-K| / min(K, |ranked|)`. Imenilac je **broj stvarno serviranih** preporuka, NIKAD
   broj relevantnih (čest bag). Prazna lista → `0.0`; `k <= 0` → `ValueError`.
2. **`recall_at_k(ranked_ids, relevant_ids, k)`** — R@K = `|relevant ∩ top-K| / |relevant|`. Nula relevantnih (`0/0`) → `0.0` (definisano).
3. **`hit_rate_at_k(ranked_ids, relevant_ids, k)`** — HR@K = `1.0` ako je bar
   jedan relevantan u top-K, inače `0.0`.
4. **`ndcg_at_k(ranked_ids, relevant_ids, k)`** — DCG@K = Σ `rel_i / log2(i+2)`
   (rel\_i = 1 ako je pozicija `i` relevantna), IDCG@K = DCG idealnog poretka
   (svi relevantni prvo, ograničeno na `min(|relevant|, |top|)` mesta).
   NDCG = DCG/IDCG; nula relevantnih ili prazna lista → `0.0`.
5. **`catalog_coverage(recommended_ids, catalog_size)`** — `|set(ids)| / catalog_size`. `catalog_size <= 0` → `ValueError`.
6. **`temporal_split(events_df, split_time)`** — događaji sa
   `timestamp < split_time` → train, `>=` → test. Vrati `(train_df, test_df)`.

## Provera

```
# iz Day 7/lab/ — koristi dm-ml venv
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: pet metrika (edge case-ovi uključeni), temporal split.
* Ne radiš: ceo `evaluate_recommender` protokol, prediktore, comparison report,
  API, generator `Day 7/data` — to koristi tvoje funkcije u
  `app/recommenders/evaluation.py` i servisu.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
