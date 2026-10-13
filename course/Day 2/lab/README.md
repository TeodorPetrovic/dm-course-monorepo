# Lab — Dan 2: RFM feature-i i dodela segmenta

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne menjaš
`dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas`, `numpy`, `scikit-learn` (`dm-ml/.venv` ih ima).
* Seeded dataset: `Day 1/data/events.csv` + `orders.csv` (jedini izvor istine).

## Zadatak (koraci)

1. **`calculate_rfm(events, orders)`** — vrati DataFrame `user_id, recency_days, frequency, monetary` sa eksplicitnim definicijama:

   * **Recency:** `(referenca − poslednja kupovina)` za kupce; za zero-spend
     korisnike `(referenca − poslednja aktivnost)`; bez ijednog događaja →
     najhladniji fallback. Referenca = max(timestamp) iz događaja i porudžbina.
   * **Frequency / Monetary:** iz `orders`; zero-spend → 0 i 0.0 (bez NaN).
2. **`scale_customer_features(features, cols, scaler=None)`** —
   `scaler=None` → fit novi `StandardScaler`; `scaler` dat → **transform only**
   (ne refit-uj — čest bug). Vrati `(scaled_df, scaler)`.
3. **`assign_segment(model, scaled_row, fallback_label="unsegmented")`** —
   `model is None` → `ValueError`; prazan `scaled_row` → `fallback_label`;
   inače → `f"segment_{int(model.predict(row))}"`.

## Provera

```
# iz Day 2/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: RFM (sa zero-spend fallback-om), skaliranje sa transform-only
  disciplinom, dodelu segmenta sa definisanim fallback-om.
* Ne radiš: celokupan `dm-ml` servis, API, perzistenciju modela — to koristi
  tvoje funkcije u `app/ml/` i servisu. Ovaj lab je fokus na *koncept*.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
