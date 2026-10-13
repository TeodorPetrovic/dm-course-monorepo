# Lab — Dan 9: session features, recency i CTR (feedback loop)

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/session.py` već sadrži (da razumeš *šta* session-aware
preporuke i CTR rade). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 — `dm-ml/.venv` ga ima.
* Lab radi na malim, ručno napravljenim strukturama (list dict-ova) — nema
  seeded CSV-a, nema pandas-a.

## Zadatak (koraci)

1. **`recency_weights(n, decay)`** — geometrijska recency težina: za `n`
   događaja (najnoviji je POSLEDNJI), težina i-tog je `decay ** (n - 1 - i)`.
   `n == 0` → `[]`. **Zašto:** skoriji događaji nose više informacije o tekućem
   interesu (recency) — ne računamo sve događaje sesije jednako.
2. **`recent_product_interest(events, decay=0.8)`** — `{product_id: interes}` iz
   proizvodnih događaja sesije: težina = `EVENT_WEIGHTS[type] × recency_weight`.
   Bez proizvodnih događaja → `{}`.
3. **`recent_category_interest(events, product_categories, decay=0.8)`** —
   `{category_id: interes}`: mapira proizvodni interes na kategorije preko
   `product_categories` (katalog je source of truth). Proizvodi kojih nema u
   katalogu se ignorišu.
4. **`recommendation_ctr(impressions, clicks)`** — CTR = `len(clicks) / len(impressions)`. **Zero-division:** 0 impresija → `0.0` (bez `None`, bez
   deljenja kroz nulu).
5. **`ctr_by_algorithm(impressions, clicks)`** — CTR po `algorithm`
   (`recommendation_source`): `[{"algorithm", "impressions", "clicks", "ctr"}, ...]` sortirano po `algorithm` rastuće; algoritam sa 0 impresija → `ctr = 0.0`.

## Provera

```
# iz Day 9/lab/ — koristi dm-ml venv
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: recency težine, recency-weighted interes (proizvod + kategorija), CTR
  sa zero-division handling-om, CTR po algoritmu.
* Ne radiš: `get_current_session` (filter + sort), `build_session_features`
  (trajanje/recency u sekundama), `recommend_for_session` (kandidati + fallback),
  API, generator `Day 9/data` — to koristi tvoje funkcije kao deo
  `app/recommenders/session.py` i servisa.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
