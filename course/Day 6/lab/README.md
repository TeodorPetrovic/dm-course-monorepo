# Lab — Dan 6: implicitna interaction matrica, item-item sličnost i preporuke

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/collaborative.py` već sadrži (da bi razumeo *šta*
ti moduli rade). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` + `scipy` + `scikit-learn` — `dm-ml/.venv` ih ima.
* Lab radi na malim, ručno napravljenim događajima i proizvodima — nema seeded
  CSV-a.

## Zadatak (koraci)

Događaji su DataFrame (`user_session`, `product_id`, `event_type`); težine su
date u `EVENT_WEIGHTS` (`product_view`=1, `add_to_cart`=3, `purchase`=5 —
pretpostavke, ne istine).

1. **`build_interaction_matrix(events_df)`** — implicitna interaction matrica
   (red = sesija, kolona = proizvod). Vrednost ćelije = **najveća** težina
   događaja u (sesija, proizvod) — *ne zbir* (brojanje interakcija kao ocenu je
   čest bag). Vrati `(csr_matrix, sessions, products)`, sortirano.
2. **`calculate_item_similarity(matrix)`** — item-item kosinusna sličnost:
   item vektori su **kolone** matrice, pa je `cosine_similarity(matrix.T)` →
   gusti `np.ndarray` (`n_proizvoda × n_proizvoda`).
3. **`recommend_similar(products_df, product_id, matrix, products, limit=5)`**
   — preporuke po sličnosti, **isključi target**, top-N sa `score` =
   kosinusna sličnost. Nepoznat `product_id` (cold start / nov proizvod) ->
   **fallback na `recommend_popular`** (baseline; nikad prazan rezultat).
4. **`recommend_popular(products_df, limit=5)`** — popularity baseline (za
   fallback): sortiraj po `popularity` opadajuće (tie-break po `product_id`),
   `score` = `popularity`.

## Provera

```
# iz Day 6/lab/ — koristi dm-ml venv (ima sklearn)
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: max-agregaciju interakcija, sparse matricu, item-item kosinusnu
  sličnost, target exclusion i cold-start fallback, popularity baseline.
* Ne radiš: ceo `dm-ml` servis, API, generator `interactions.csv`,
  session-length normalizaciju (vežba), heuristic baseline i poređenja,
  weight-sensitivity eksperiment — to koristi tvoje funkcije u
  `app/recommenders/collaborative.py` i servisu.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
