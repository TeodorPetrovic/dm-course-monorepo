# Lab — Dan 8: merge, rank, biznis pravila i raznovrsnost

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/hybrid.py` već sadrži (da bi razumeo *šta* two-stage
pipeline radi). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 — `dm-ml/.venv` ga ima.
* Lab radi na malim, ručno napravljenim listama kandidata — nema seeded CSV-a.

## Zadatak (koraci)

Kandidat = dict `{"product_id": int, "score": float}` (opciono `category_id`).
Implementiraj čiste funkcije:

1. **`normalize_scores(scores)`** — max-skaliranje na `[0, 1]`:
   `score / max`. `max == 0` → svi `0.0`; svi jednaki (>0) → svi `1.0`;
   prazna lista → `[]`. **Zašto:** ne sabiraš sirov TF-IDF skor (0..1) sa
   sirovim count-om interakcija (0..stotine) pre normalizacije.
2. **`merge_candidates(candidate_lists, weights)`** — za svaki izvor
   normalizuj skorove, pa blended = `Σ w_source * normalized_score`
   (normalizuj težine da zbirom budu 1.0). Duplikati se spajaju;
   `sources` = sortirani izvori. Zbir težina ≤ 0 → `ValueError`.
3. **`rank_candidates(candidates)`** — sortiraj opadajuće po `score`,
   tie-break po `product_id` rastuće (determinizam).
4. **`apply_business_rules(ranked, rules)`** — filter posle rangiranja:
   `available_ids` (dostupnost), `exclude_ids` (već kupljeno/viđeno),
   `min_score`. Vrati `{"ranked": [...], "removed": [...]}` — removed sa
   `removed_by` razlozima.
5. **`diversify_results(ranked, k, max_per_category=2)`** — greedy re-ranker:
   zadrži kandidata ako njegova kategorija nije prekoračila
   `max_per_category`; popuni do `k` ostatkom liste („fill, don't truncate" —
   raznovrsnost ne sme da uništi relevantnost).

## Provera

```
# iz Day 8/lab/ — koristi dm-ml venv
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: normalizaciju, težinski merge, deterministički rank, biznis pravila,
  greedy raznovrsnost.
* Ne radiš: candidate generation (content/CF/TF-IDF), cold-start fallback,
  user-based evaluaciju, API, generator `Day 8/data` — to koristi tvoje
  funkcije kao deo `app/recommenders/hybrid.py` i servisa.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
