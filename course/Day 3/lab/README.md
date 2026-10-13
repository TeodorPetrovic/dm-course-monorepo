# Lab — Dan 3: labeled training dataset, split, evaluacija i fallback

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne menjaš
`dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas`, `numpy`, `scikit-learn` (`dm-ml/.venv` ih ima).
* Seeded dataset: `Day 1/data/events.csv` + `orders.csv` (jedini izvor istine).

## Zadatak (koraci)

1. **`build_training_dataset(events, orders, window_days=7, leaky=False)`** —
   labeled dataset po korisniku:

   * **cutoff** = `reference − window_days` (reference = najskoriji događaj/
     porudžbina).
   * **Labela** `will_purchase`: 1 ako je korisnik kupio u `[cutoff, reference]`, inače 0.
   * **Clean** (`leaky=False`): feature-i se računaju SAMO na istoriji *pre*
     cutoff-a (sa `reference=cutoff` za recency) — model ne sme da vidi window.
   * **Leaky** (`leaky=True`): feature-i iz CELE istorije (uključujući window)
     — namerni bug za vežbu.
   * Vrati DataFrame: `user_id`, feature kolone (`FEATURE_COLUMNS`),
     `will_purchase`.
2. **`split_dataset(df, test_size=0.3, random_state=42)`** — stratifikovan
   train/test split po `will_purchase` (isti udeo pozitivnih u oba skupa);
   resetuj indekse.
3. **`evaluate_model(model, X, y)`** — vrati dict: `accuracy`, `precision`,
   `recall`, `f1`, `confusion_matrix` ([[tn, fp], [fn, tp]]), `n`. Koristi
   `sklearn.metrics` sa `zero_division=0`.
4. **`predict_conversion_probability(model, scaled_row)`** — vrati
   verovatnoću `will_purchase=1` (zaokruži na 4 decimale):

   * `model is None` -> `ValueError` („model not trained").
   * prazan `scaled_row` -> `ValueError` („prazna feature vrsta").

## Provera

```
# iz Day 3/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: definiciju labele + temporalni window + leaky flag, stratifikovan
  split, evaluaciju (confusion/P/R/F1) i untrained fallback.
* Ne radiš: celokupan `dm-ml` servis, API, perzistenciju modela, skaliranje —
  to koristi tvoje funkcije u `app/ml/` i servisu. Feature builder
  (`build_features`) je dat u `starter.py` (to je Day 2 materijal).

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
