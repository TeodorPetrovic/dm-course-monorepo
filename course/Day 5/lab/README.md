# Lab — Dan 5: baselines, TF-IDF, kosinusna sličnost i cold start

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/content.py` već sadrži (da bi razumeo *šta* ti
moduli rade). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` + `scikit-learn` — `dm-ml/.venv` ih ima.
* Lab radi na malim, ručno napravljenim katalozima — nema seeded CSV-a.

## Zadatak (koraci)

Katalog je DataFrame po proizvodu (`product_id`, `category_id`,
`category_name`, `name`, `slug`, `description`, `img_url`, `price`,
`popularity`). `popularity` je *data* (baseline skor iz događaja) — ne
implementiraš je.

1. **`recommend_popular(products_df, limit=5)`** — popularity baseline: sortiraj
   po `popularity` opadajuće (tie-break po `product_id`), vrati top-`limit` sa
   kolonom `score`. Bez ML-a — ovo je referentna tačka za sve ostalo.
2. **`recommend_same_category(products_df, product_id, limit=5)`** — baseline po
   kategoriji: proizvodi iste kategorije, **bez targeta**, po popularnosti.
   Nepoznat `product_id` -> `ValueError`.
3. **`prepare_product_text(products_df, include_category=True)`** — tekst za
   TF-IDF: `name + description`, opciono + `category_name` ispred (kategorija je
   token — „extend the text with category tokens" iz DAY-BRIEFS-a). Vrati
   `pd.Series` indeksiranu po `product_id`.
4. **`build_tfidf_matrix(products_df, text_column="product_text")`** —
   `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)` →
   `(matrix, vectorizer)`. Ako nema `product_text` kolone, napravi je iz
   `prepare_product_text`. Matrica je poravnata sa `products_df`.
5. **`calculate_product_similarity(tfidf_matrix, index)`** — kosinusna sličnost
   reda `index` sa **svim** redovima. `TfidfVectorizer` normalizuje redove po
   default-u, pa je kosinus = skalarni proizvod normalizovanih vektora — ne
   porediš raw counts (to je čest bag).
6. **`recommend_similar_products(products_df, product_id, tfidf_matrix, limit=5)`**
   — content preporuke: sličnost → **isključi target** → top-N. Cold start
   (nepoznat `product_id` — nov proizvod bez TF-IDF reda) -> **fallback na
   `recommend_popular`** (baseline; nikad prazan rezultat).

## Provera

```
# iz Day 5/lab/ — koristi dm-ml venv (ima sklearn)
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: popularity/category baseline, pripremu teksta, TF-IDF (preko
  `TfidfVectorizer`), kosinusnu sličnost, target exclusion i cold-start fallback.
* Ne radiš: ceo `dm-ml` servis, API, generator `products_text.csv`, popularity
  skor iz događaja (data je), baseline comparison — to koristi tvoje funkcije u
  `app/recommenders/content.py` i servisu.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
