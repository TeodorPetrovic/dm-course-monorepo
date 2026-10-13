# Day 10 lab — brute-force nearest neighbors (student-written)

U modulu `dm-ml/app/recommenders/embeddings.py` postoji
`cosine_similarity_bruteforce` i `find_nearest_products`. U ovom lab-u **ti ih
pišeš sam** — na malim, ručno napravljenim numpy strukturama — da razumeš *šta*
semantička pretraga radi pre nego što ikad dotakneš ANN biblioteku
(DAY-BRIEFS: „hiding the whole concept behind encode/similarity\_search" je čest
bag).

Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš rešenje sa `test_lab.py`.

## Zadaci (`starter.py`)

1. `normalize(matrix)` — L2 normalizacija svakog reda; **nula-red ostaje nula**
   (bez `NaN`).
2. `cosine_similarity(query_vec, matrix)` — kosinusna sličnost upita sa svakim
   redom matrice; **normalizuje oba ulaza** (ne zaboravi — to je čest bag).
3. `brute_force_nearest(matrix, query_vec, k=3, exclude_index=None)` — top-`k`
   indeksa + skorova po kosinusnoj sličnosti, opadajuće; `exclude_index` se
   izbacuje (za „ne preporučuj sam sebe"). **Ovo je brute-force petlja.**
4. `semantic_search_lite(products, embeddings, query_embedding, k=3)` — top-`k`
   proizvoda (dict-ova) sa skorom za dati embedding upita.

## Pokretanje

```
cd "Day 10/lab"
# svoje rešenje:
python3 -m pytest test_lab.py
# referentno rešenje:
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Vežba (vreme brute-force-a)

U `reference_solutions.py` nađi `time_brute_force` primer: izmeri vreme
`brute_force_nearest` na `n=252` (veličina Day 10 store-a) i zabeleži. Koliko
bi trajalo na `1_000_000` proizvoda? To je *uvod* u ANN biblioteke — brute-force
je tačan, ali linearno skenira sve; ANN (faiss/annoy) je priča za skaliranje.
