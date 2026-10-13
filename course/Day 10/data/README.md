# Day 10 podaci — dense embedding store + keyword-vs-TFIDF-vs-embedding comparison

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 5
kataloga (ne dupliraju ga). Kompletna dokumentacija (izvor, embedder, parametri,
counts, summary, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Oblik |
| --- | --- | --- |
| `embeddings.npz` | dense embedding matrica (L2 normalizovana) + `product_ids` + embedder descriptor | `252 x 384` (sentence-transformers MiniLM) |
| `embeddings.json` | sidecar uz `.npz` (descriptor embeddera) | — |
| `comparison.csv` | **keyword vs TFIDF vs embedding** na 6 poznatih upita | 47 redova (neke metode vrate < 3 hita, npr. keyword bez pogodaka) |
| `metadata.json` | izvor, embedder, parametri, counts, summary, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 5/data/products_text.csv` (katalog sa `product_text` kolonom =
  kategorija + naziv + opis).
* Embedder: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, naučen model).
  Fallback (offline): `HashEmbedder` (`--embedder hash`, 64-dim seeded random
  projection nad hashing TF-IDF) — deterministički, bez modela i mreže.
* Za svaki proizvod: `product_text` → dense vektor (L2 normalizovan). Red `i`
  matrice = proizvod `i` (isti redosled kao `products_text.csv`).
* Generator: `app/data/generate_embeddings.py` (upisuje `.npz` + sidecar).

## `comparison.csv` — šta poredi

Poznati upiti se puštaju kroz **tri** metode pretrage:

| Metoda | Skor | Rečni mehanizam |
| --- | --- | --- |
| `keyword` | broj tokena upita u tekstu proizvoda (bez stopworda) | tačno preklapanje reči |
| `tfidf` | kosinus TF-IDF vektora (Day 5 `build_tfidf_matrix`) | težinsko preklapanje reči (ngram 1-2) |
| `embedding` | kosinus dense embedding vektora (istom embedderu kao store) | blizina u naučenom prostoru |

Ključni upiti i prvi pogodak:

| Upit | keyword | tfidf | **embedding** |
| --- | --- | --- | --- |
| `smartphone` | Smartphone ✓ | Smartphone ✓ | Smartphone ✓ |
| `something to listen to music with` | Stand (sadrži „music") | Guitar | **Metronome, Amp, Headphones** |
| `a book to read before bed` | **Bed** ✗ | **Bed** ✗ | **Novel, Textbook** ✓ |
| `fitness and training gear` | — | Smartphone ✗ | **Belt, Backpack, Dumbbell** ✓ |
| `home cooking essentials` | Lamp/Toaster | Table/Lamp | **Spice Set, Cookbook** ✓ |
| `wireless earbuds for travel` | — | Smartphone ✗ | **Headphones** ✓ |

Šta tabela NE dokazuje: pobeda embeddinga na ovih 6 upita nije benchmark; na
upitima sa očiglednim preklapanjem (`smartphone`) sve tri metode rade isto.
Semantički pogodak ≠ model „razume" — to je blizina vektora u naučenom prostoru.

## Ključne kolone (`comparison.csv`)

| Kolona | Značenje |
| --- | --- |
| `query` | upit (poznat, iz `--queries`) |
| `method` | `keyword` | `tfidf` | `embedding` |
| `rank` | 1 = prvi pogodak |
| `product_id` | pogodak (stabilan ID) |
| `name` | naziv proizvoda (katalog) |
| `category_id` | kategorija |
| `score` | skor metode (overlap count / kosinusna sličnost) |

## Reprodukcija

```
cd dm-ml
.venv/bin/python -m app.data.generate_embeddings --embedder auto   # ST (default)
.venv/bin/python -m app.data.generate_embeddings --embedder hash   # offline fallback
```

Isti embedder + isti ulaz → identični fajlovi (sha256 u `metadata.json`).
