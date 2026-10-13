# Dan 10 — Semantic Search and Embedding-Based Recommendations

- lesson_id: 120
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:47.845 updated: 2026-09-05 20:00:30.274
- summary: „Reči su iste, značenje nije." Do sada je svaka pretraga i preporuka (Day 5 content TF-IDF, Day 6 collaborative, Day 8 hybrid, Day 9 session) radila na eksplicitnom preklapanju: reči koje se poklapaju, kategorije koje se poklapaju, istorija koja se poklapa. Danas uvodimo dense embedding: tekst proizvoda postaje tačka u naučenom prostoru, a „sličnost" je blizina u tom prostoru — ne preklapanje reči. To je osnova semantičke pretrage (GET /search/semantic) i embedding preporuka (GET /recommendations/ semantic/{productid}), gde upit koji deli nula reči sa proizvodom i dalje može da ga pronađe („something to listen to music with" → Headphones). [subjects-import]


---

<!-- page_id 430 order 0 -->
## [Page] Materijal

# Dan 10 — Semantic Search and Embedding-Based Recommendations

> *„Reči su iste, značenje nije."* Do sada je svaka pretraga i preporuka
> (Day 5 content TF-IDF, Day 6 collaborative, Day 8 hybrid, Day 9 session)
> radila na **eksplicitnom preklapanju**: reči koje se poklapaju, kategorije
> koje se poklapaju, istorija koja se poklapa. Danas uvodimo **dense embedding**:
> tekst proizvoda postaje tačka u naučenom prostoru, a „sličnost" je *blizina u
> tom prostoru* — ne preklapanje reči. To je osnova semantičke pretrage
> (`GET /search/semantic`) i **embedding preporuka** (`GET /recommendations/ semantic/{product_id}`), gde upit koji deli *nula* reči sa proizvodom i dalje
> može da ga pronađe („something to listen to music with" → Headphones).

## Šta gradimo

**Dense embedding store** — svaki proizvod postaje vektor (npr. 384-dim iz
`sentence-transformers/all-MiniLM-L6-v2`), sačuvan i reloadable
(`save_embeddings`/`load_embeddings`) — plus **brute-force najbliži susedi**
(bez ANN biblioteke — to je svesno, vidi „AI-ML koncept"), **semantička
pretraga** (`semantic_search`) i **embedding preporuke** (`find_nearest_products`),
izložene kroz dva endpoint-a i integrisane u CMS (search stranica + product
stranica).

Day 5 je napravio *sparse* TF-IDF vektore; Day 10 je njihov *dense* kontrast.
Uz današnji store imamo i **keyword-vs-TFIDF-vs-embedding comparison**
(`Day 10/data/comparison.csv`) — da vidiš *gde* i *zašto* se pristupi razlikuju.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `STEmbedder` | **machine learning** (naučeni semantički embedding model, sentence-transformers) |
| `HashEmbedder` | **machine learning** (fallback embedder: hashing TF-IDF + seeded random projection, bez modela) |
| `l2_normalize` | **data preprocessing** (vektori → jedinični, pre kosinusa) |
| `generate_product_embedding` / `generate_all_embeddings` | **data preprocessing / feature engineering** (tekst → dense vektor) |
| `save_embeddings` / `load_embeddings` | **data persistence** (`.npz` store + descriptor + sidecar) |
| `cosine_similarity_bruteforce` | **machine learning** (kosinusna sličnost, brute-force) |
| `find_nearest_products` | **machine learning / retrieval** (brute-force NN za proizvod) |
| `semantic_search` | **machine learning / retrieval** (upit → top-N) |
| `keyword_search` | **rule / heuristic** (token-overlap fallback bez ML-a) |

## Application requirement

Shop/CMS do sada nije imao pretragu. Dan 10 dodaje **search stranicu** koja
koristi *semantičku* pretragu (`GET /search/semantic?q=…`) umesto ručnog
token-matching-a, i **product stranica** dobija **embedding preporuke**
(`GET /recommendations/semantic/{product_id}`) kao još jedan red
„Recommended Products". Kad embedding model nije dostupan (offline), oba
endpoint-a vraćaju definisan fallback — nikad tihi `[]`.

## Ciljevi učenja

Do kraja dana treba da:

* objasnite **sparse vs dense**: TF-IDF vektor je *sparse* (veličina = rečnik)
  i meri preklapanje reči; dense embedding je npr. 384-dim i meri *semantičku
  blizinu* — tekstovi bez zajedničkih reči mogu da budu blizu;
* generišete **`generate_product_embedding`** (tekst → normalizovan dense
  vektor) i **`generate_all_embeddings`** (ceo katalog → matrica);
* sačuvate i učitate **embedding store** (`save_embeddings`/`load_embeddings`)
  — perzistencija + determinizam;
* implementirate **brute-force najbliže susede** (`find_nearest_products`,
  `semantic_search`) — **ručno, pre nego što dotakneš ANN biblioteku**;
* uporedite **keyword vs TFIDF vs embedding** na poznatim upitima i objasnite
  gde koji pristup „vara";
* dodate **fallback za missing embeddings** (proizvod bez reda u store-u →
  popularity; embedding model nedostupan → keyword pretraga) — nikad tihi `[]`;
* objasnite šta semantički pogodak **NE dokazuje** (model ne „razume" —
  vektori su blizu u naučenom prostoru).

## Preduslovi

Day 5 katalog (`products_text.csv` — `product_text` kolona = kategorija +
naziv + opis), Day 5 TF-IDF (sparse kontrast), sentence-transformers osnove.
Embedding store je *izveden* iz Day 5 kataloga; Day 1–9 podaci nisu potrebni za
retrieval (semantičke preporuke ne gledaju istoriju).

## Postojeći sistem (šta nasleđujemo)

* **Day 5 `build_tfidf_matrix` / `calculate_product_similarity`** — sparse
  content preporuke; danas ih poredimo sa dense embeddingom (`comparison.csv`).
* **Day 5 `prepare_product_text`** — tekstualna reprezentacija proizvoda
  (kategorija + naziv + opis); embedding koristi istu kolonu `product_text`.
* **CMS search page ne postoji** — `trackSearchEvent` u `trackEvent.ts` već
  postoji (komentar: „Day 10 dodaje pravu pretragu"); danas je konektujemo.
* **Day 9 feedback loop** — nove embedding preporuke na product stranici mogu
  da loguju impresije/klikove kroz isti `POST /recommendations/events`
  (source=`semantic`) i da uđu u CTR dashboard.

## Arhitektura

```
product_text (Day 5) ──> STEmbedder | HashEmbedder ──> matrix (n x dim)
        │                                                 │
        │        generate_all_embeddings                  │
        ▼                                                 ▼
  Day 10/data/embeddings.npz ──load──> store dict (matrix + product_ids + embedder descriptor)
        │                                                 │
        │  semantic_search / find_nearest_products        │  brute-force NN
        ▼                                                 ▼
   GET /search/semantic?q=…        GET /recommendations/semantic/{product_id}
        │                                                 │
        ▼                                                 ▼
   search stranica (CMS)           product stranica „Semantically similar" (CMS)
```

Ključni ugao: **upit kodiramo u ISTOM prostoru kao store**. Store čuva
descriptor embeddera (`embeddings.npz`); servis ga čita, rekonstruiše isti
embedder i tek onda kodiramo upit. Mešanje prostora (query drugim embedderom)
je čest bag.

## Korišćeni podaci

**Embedding store** (seeded, `Day 10/data/`, jedini izvor:
`app/data/generate_embeddings.py`) — izveden iz Day 5 kataloga:

| Fajl | Sadržaj |
| --- | --- |
| `embeddings.npz` | dense matrica `252 x 384` (sentence-transformers MiniLM), L2 normalizovana, poravnata sa `products_text.csv`; + `product_ids` + embedder descriptor |
| `embeddings.json` | sidecar uz `.npz` (descriptor embeddera) |
| `comparison.csv` | **keyword vs TFIDF vs embedding** na 6 poznatih upita (`query, method, rank, product_id, name, category_id, score`) |
| `metadata.json` | izvor, embedder, parametri, counts, summary, sha256 |

`embeddings.npz` se **ne regeneriše pri pokretanju** — servis ga učitava
(`load_embeddings`); ako fajl ne postoji, servis ga gradi on-the-fly i čuva
(default embedder). Determinizam: isti embedder + isti ulaz → isti store
(sha256 u `metadata.json`).

## AI-ML koncept

* **Sparse vs dense.** TF-IDF (Day 5) predstavlja tekst kao vektor dužine
  rečnika sa težinama po reči — *sparse*, interpretabilan po rečima. Embedding
  predstavlja tekst kao kratak *dense* vektor (384-dim) naučen da bliski
  vektori = slično značenje. Kosinusna sličnost radi nad oba; razlika je šta
  vektor *znači*.
* **Semantička blizina ≠ preklapanje reči.** „Something to listen to music
  with" i „Headphones for music" dele **samo jednu** reč („music"), a suština je
  *slušanje* — opet su blizu u embedding prostoru. Zato embedding pronalazi
  Metronome/Amp/Headphones gde keyword/tfidf daju Stand/Guitar (samo zbog reči „music");
  na upitima bez zajedničkih reči keyword/tfidf daju Bed ili ništa (vidi Comparison).
* **Normalizacija pre kosinusa.** Kosinus sličnost normalizovanih vektora =
  skalarni proizvod. Bez L2 normalizacije dužine vektora kvare rang. Čest bag.
* **Brute-force pre ANN.** Za `n=252` proizvoda, brute-force petlja
  (`matrix @ query`) je najbolji odgovor. ANN biblioteke (faiss, annoy) su
  priča za *skaliranje* na milione, ne za kurs — zato studenti prvo napišu
  petlju (Day 10/lab), pa tek onda pričaju o ANN kao „šta bi bilo kad bi bilo
  veliko".
* **Query i produkti u istom prostoru.** Embedding upita mora da dolazi iz
  istog modela (iste parametre) kao embedding proizvoda. Zato store čuva
  descriptor, a servis rekonstruiše **isti** embedder.
* **Fallback je deo sistema.** Nov proizvod nema red u store-u → popularity
  (nikad tihi `[]`). Embedding model nedostupan → keyword pretraga — **ali ne
  kodiraš upit drugim embedderom nego store-om** (to bi pomešalo prostore);
  vraćaš se na token-overlap.
* **Semantički hit ≠ razumevanje.** Blizina u naučenom prostoru ne znači da
  model zna šta reči znače. Može da izvuče plausibilno-ali-nebitno (DAY-BRIEFS).

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — embedderi: `STEmbedder` i `HashEmbedder`

`STEmbedder` (sentence-transformers, naučen model) i `HashEmbedder`
(deterministički fallback: hashing TF-IDF + seeded sparse random projection +
L2, bez modela i mreže). Oba imaju `encode_texts(texts) -> (n, dim)` i
`descriptor()` (`{"name", "params"}`); `build_embedder(descriptor)` rekonstruiše iz descriptor-a.
Default je ST ako je dostupan, inače hash.

### Korak 2 — `l2_normalize` + `cosine_similarity_bruteforce`

`l2_normalize(v)` — svaki red postaje jedinični (nula-vektor ostaje nula,
bez `NaN`). `cosine_similarity_bruteforce(query_vec, matrix)` — normalizuje oba
ulaza pa skalarni proizvod → kosinusne sličnosti. **Ovo je funkcija koju
studenti prepisuju u lab-u.**

### Korak 3 — `generate_product_embedding` / `generate_all_embeddings`

`generate_product_embedding(embedder, text)` — jedan tekst → 1-D normalizovan
vektor. `generate_all_embeddings(embedder, products, text_column="product_text")` — ceo
katalog → matrica poravnata sa `products` (red `i` = proizvod `i`).

### Korak 4 — `save_embeddings` / `load_embeddings`

`save_embeddings(path, matrix, product_ids, embedder)` piše `.npz`
(`matrix`, `product_ids`, `embedder_name`, `embedder_params`); `metadata.json` je sidecar
koji piše generator. `load_embeddings(path)` vraća dict (`matrix`, `product_ids`,
`embedder_name`, `embedder_params`).
Round-trip je deo testova (perzistencija + determinizam).

### Korak 5 — `find_nearest_products` / `semantic_search`

`find_nearest_products(matrix, query_vec, k=3, exclude_index=None)` — brute-force NN
(`exclude_index` = red targeta) → lista `(index, score)`; nepoznat proizvod rešava servis
(fallback). `semantic_search(matrix, product_ids, query_vec, k=5)` — upit kodiran istim
embedderom kao store → lista `(product_id, score)`.

### Korak 6 — `keyword_search` (fallback)

`keyword_search(products, query, k=3)` — token-overlap bez stopworda,
tie-break po popularnosti. Služi kao **keyword baseline** u comparison-u i kao
**fallback kad store-ov embedder nije dostupan**.

### Korak 7 — Servis + API + generator + CMS

`app/services/semantic.py` (`SemanticService` — store se učitava/gradi,
query embedder iz descriptor-a, fallback logika), `GET /search/semantic` +
`GET /recommendations/semantic/{product_id}`, `app/data/generate_embeddings.py`
(upisuje `Day 10/data/*`), search stranica + product stranica (CMS), demo.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `generate_product_embedding(embedder, text)` | tekst → 1-D normalizovan dense vektor | `app/recommenders/embeddings.py` |
| `generate_all_embeddings(embedder, products, ...)` | ceo katalog → matrica `n x dim` + ID-evi | `app/recommenders/embeddings.py` |
| `save_embeddings(path, matrix, product_ids, embedder)` | piše `.npz` | `app/recommenders/embeddings.py` |
| `load_embeddings(path)` | `.npz` → dict (matrica + ID-evi + descriptor) | `app/recommenders/embeddings.py` |
| `l2_normalize(v)` | L2 normalizacija redova (pre kosinusa) | `app/recommenders/embeddings.py` |
| `cosine_similarity_bruteforce(query_vec, matrix)` | kosinusna sličnost, brute-force (normalizuje oba ulaza) | `app/recommenders/embeddings.py` |
| `find_nearest_products(matrix, query_vec, k, exclude_index)` | brute-force NN (bez targeta) | `app/recommenders/embeddings.py` |
| `semantic_search(matrix, product_ids, query_vec, k)` | upit → top-N (isti prostor kao store) | `app/recommenders/embeddings.py` |
| `keyword_search(products, query, k)` | token-overlap fallback (keyword baseline) | `app/recommenders/embeddings.py` |
| `STEmbedder` / `HashEmbedder` / `build_embedder` | modeli + fabrika rekonstrukcije | `app/recommenders/embeddings.py` |
| `SemanticService.*` | učitavanje/gradnja store-a, search, preporuke, comparison | `app/services/semantic.py` |
| `app/data/generate_embeddings.py` | generiše `Day 10/data/*` (byte-for-byte) | `app/data/generate_embeddings.py` |
| `examples/demo_semantic.py` | pun demo (store + search + preporuke + comparison) | `Day 10/examples/demo_semantic.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /search/semantic?q=…&limit=5` | 200: semantic envelope (`query`, `method`, `fallback`, `embedder`, `store`, `results`); **422** prazan/missing `q` ili nevalidan `limit`; **503** nema kataloga; **embedding model nedostupan → 200 sa keyword fallback-om** (`fallback_reason="embedder_unavailable"`) |
| `GET /recommendations/semantic/{product_id}?limit=5` | 200: semantic envelope (`product_id`, `method`, `fallback`, `recommendations`); **422** nevalidan `limit`; **503** nema kataloga; **proizvod bez embeddinga → 200 sa popularity fallback-om** (`fallback_reason="no_embedding"`) |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /search/semantic?q=wireless earbuds for travel&limit=3`

```
{
  "product_id": null, "method": "semantic", "fallback": false, "fallback_reason": null,
  "returned": 3,
  "results": [
    {"product_id": 6,  "name": "Headphones Compact 103", "category_id": 1, "price": 265.99, "score": 0.5089},
    {"product_id": 5,  "name": "Headphones Deluxe 350",  "category_id": 1, "price": 71.99,  "score": 0.4548},
    {"product_id": 16, "name": "Speaker Eco 174",        "category_id": 1, "price": 180.99, "score": 0.3169}
  ],
  "query": "wireless earbuds for travel",
  "embedder": "sentence-transformers:sentence-transformers/all-MiniLM-L6-v2",
  "store": {"n_products": 252, "dim": 384, "embedder": "sentence-transformers:sentence-transformers/all-MiniLM-L6-v2"}
}
```

Reč „earbuds" se ne pojavljuje nigde u katalogu — embedding ipak nalazi slušalice i
zvučnik. Keyword pretraga za isti upit „vara": pogađa i *Mouse Deluxe 406* (ima
„wireless") i *Guide Everyday 453* (putni vodič, ima „travel"). To je razlika koju
`comparison.csv` dokumentuje.

### Primer — `GET /recommendations/semantic/22?limit=3`

```
{
  "product_id": 22,
  "method": "semantic",
  "fallback": false,
  "recommendations": [
    {"product_id": 42, "name": "Jacket Pro 710",       "category_id": 2, "price": 216.99, "score": 0.841},
    {"product_id": 23, "name": "Jacket Essential 819", "category_id": 2, "price": 109.99, "score": 0.8176},
    {"product_id": 37, "name": "Backpack Compact 926", "category_id": 2, "price": 39.99,  "score": 0.6474}
  ]
}
```

`GET /recommendations/semantic/99999?limit=3` (proizvod bez embeddinga):

```
{
  "product_id": 99999, "method": "fallback", "fallback": true,
  "fallback_reason": "no_embedding", "returned": 3,
  "recommendations": [{"product_id": 90, "name": "Table Lamp Eco 643", "category_id": 5, "price": 23.99, "score": 2115.0}, ...]
}
```

## CMS integracija

* **Search stranica** (`dm-frontend/app/pages/search.vue`): polje za upit +
  rezultati iz `GET /ml/search/semantic?q=…`; badge prikazuje embedder i
  fallback status; `trackSearchEvent` se šalje pri pretrazi.
* **Product stranica** (`dm-frontend/app/pages/product/[slug].vue`): nova
  sekcija **„Semantically similar"** — `GET /ml/recommendations/semantic/ {product_id}`, pored Day 5 content i Day 6 collaborative preporuka. Graceful
  fallback kad dm-ml ne radi (sekcija se ne prikazuje).

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 10/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno (Day 10): `l2_normalize` (jedinična norma, nula-vektor bez `NaN`),
`HashEmbedder` (determinizam, različit seed → različito, normalizacija),
`build_embedder` rekonstrukcija, `generate_product_embedding` /
`generate_all_embeddings` (oblik + poravnanje), **`save_embeddings` /
`load_embeddings` round-trip** (acceptance: store je perzistiran i reloadable),
`find_nearest_products` (isključi target, top-N, nepoznat → `[]`),
`semantic_search` (top hit na poznatom upitu), `keyword_search` (token-overlap,
stopwordi, bez pogodaka → prazno), **fallback** (`no_embedding` → popularity,
`embedder_unavailable` → keyword; nikad tihi `[]`), **seeded manifest sha256**,
API (`/search/semantic` 200/422/503, `/recommendations/semantic/{id}`
200/fallback/422/503).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 10/examples/demo_semantic.py"` —
   učitava store, radi semantičku pretragu na poznatim upitima, prikazuje
   embedding preporuke, i keyword-vs-TFIDF-vs-embedding summary.
2. Pusti servis pa pitaj `GET /search/semantic?q=wireless earbuds for travel` —
   zašto su rezultati Headphones iako nema zajedničkih reči?
3. Pitaj `GET /search/semantic?q=a book to read before bed` — pa uporedi sa
   `GET /search/semantic?q=novel`. Šta embedding radi na prvom, a keyword/tfidf?
4. Pitaj `GET /recommendations/semantic/22` (Jacket) i uporedi sa Day 5
   `GET /recommendations/content/22`. Koje preporuke se poklapaju, koje se
   razlikuju i zašto?
5. Pitaj `GET /recommendations/semantic/99999` — popularity fallback sa
   `no_embedding` (nikad tihi `[]`).
6. Pokreni lab (`Day 10/lab/`) — napiši **brute-force NN petlju** sam:
   `normalize`, `cosine_similarity`, `brute_force_nearest`, `semantic_search_lite`
   na malim numpy strukturama i proveri `test_lab.py`.
7. Otvori search stranicu u CMS-u, ukucaj „wireless earbuds", klikni rezultat —
   i vidi `search` događaj + klik u podacima.

## Comparison (keyword vs TFIDF vs embedding)

Iz `Day 10/data/comparison.csv` (6 poznatih upita, top-3 po metodi):

| Upit | keyword (token-overlap) | tfidf (Day 5) | **embedding** |
| --- | --- | --- | --- |
| `smartphone` | Smartphone ×2 ✓ | Smartphone ×2 ✓ | Smartphone ×2, Tablet ✓ |
| `something to listen to music with` | Studio Headphones, Ukulele ×2 | Music Stand ×2, Ukulele | Music Stand, **Studio Headphones ×2** |
| `a book to read before bed` | Fantasy, **Bed Frame ×2** ✗ (fooled!) | **Bed Frame ×2** ✗, Children's Book | **Poetry, Thriller, Fantasy** ✓ |
| `fitness and training gear` | Fitness Band ×2, Smartwatch ✓ | Fitness Band ×2, Smartwatch ✓ | Bicycle ×3 (sport, ali drugi tip) |
| `home cooking essentials` | Table Lamp, Blender, Towel Set (sadrže „home") | Spice Set ×2, Desk | **Cookbook, Dark Chocolate, Spice Set** ✓ (kuvanje) |
| `wireless earbuds for travel` | Headphones, **Mouse** ✗, **Travel Guide** ✗ | **Travel Guide ×2** ✗, Mouse ✗ | **Headphones ×2, Speaker** ✓ |

Šta tabela kaže:

* **Keyword radi samo na tačnom preklapanju** i „vara" na rečima koje nose
  pogrešno značenje („bed" → kreveti, „wireless" → miš, „travel" → putni vodič).
* **TF-IDF je keyword sa težinama** — bolji za retke termine („fitness" → Fitness
  Band), ali i dalje vezan za reči (zato i on vidi krevete i putne vodiče).
* **Embedding razume parafrazu**: „read before bed" → knjige, „earbuds for travel"
  → slušalice (reč „earbuds" ne postoji u katalogu), „cooking essentials" → kuvar.
* **Embedding nije uvek bolji**: za „fitness and training gear" keyword/TF-IDF
  pogađaju fitness narukvice, a embedding vraća bicikle — semantički blizu, ali ne
  ono što je korisnik verovatno tražio. Zato se ne preskače keyword baseline.
* **Sve tri nađu `smartphone`** — kad je preklapanje očigledno, razlike nema.

## Evaluacija (kako znamo da je dobro)

* **Embedding store je perzistiran i reloadable:** `save_embeddings` →
  `load_embeddings` round-trip (matrica, ID-evi, descriptor) je acceptance test.
* **Brute-force NN je student-written:** `cosine_similarity_bruteforce` je
  izložena u modulu, a `Day 10/lab` traži da je *sam* napišeš na malim
  strukturama (nema `encode`/`similarity_search` sakrivanja koncepta).
* **Upit i produkti su u istom prostoru:** store čuva descriptor embeddera,
  servis rekonstruiše **isti** embedder; test pokriva top hit na poznatom upitu.
* **Normalizacija pre kosinusa:** `l2_normalize` se zove na oba ulaza u
  `cosine_similarity_bruteforce` (test: jedinična norma, nula-vektor bez `NaN`).
* **Fallback je definisan:** proizvod bez embeddinga → popularity
  (`no_embedding`, nikad tihi `[]`); embedding model nedostupan → keyword
  pretraga (`embedder_unavailable`, test).
* **Determinizam:** generator je byte-for-byte (sha256 u `metadata.json`);
  isti embedder + isti ulaz → isti store.
* **Comparison je dokumentovan:** `comparison.csv` (keyword vs TFIDF vs
  embedding) + tabela u README — vidi se *gde* embedding pobeđuje.

## Česti bugovi

* **Skrivanje koncepta iza `encode`/`similarity_search`** — pozoveš gotovu
  biblioteku a ne znaš šta radi. Rešenje: napiši `cosine_similarity_bruteforce`
  i `find_nearest_products` sam (lab); ANN biblioteke su priča za skaliranje,
  ne za razumevanje.
* **Bez L2 normalizacije pre kosinusa** — skalarni proizvod nenormalizovanih
  vektora meša dužine; rang je pogrešan. Rešenje: `l2_normalize` u
  `cosine_similarity_bruteforce` (test).
* **Upit i produkti u različitim prostorima** — query kodiraš drugim embedderom
  nego store (npr. hash umesto ST koji je napravio store). Rešenje: store čuva
  descriptor; `build_embedder(descriptor)` rekonstruiše isti.
* **Bez fallback-a za proizvod bez embeddinga** — nov proizvod nema red u
  store-u, a ti vratiš prazno. Rešenje: popularity fallback sa
  `fallback_reason="no_embedding"` (nikad tihi `[]`).
* **Keyword fallback koji poklapa sve** — bez stopworda token „with" („... with OLED
  display") poklapa veliki deo kataloga i pretraga se izrodi u popularity.
  Rešenje: `STOPWORDS` (`app/recommenders/embeddings.py`) u `keyword_search`.
* **Tretiranje embedding skora kao „istina"** — kosinus 0.51 je *relativan*
  (najbliži je najbolji), ne apsolutna mera relevantnosti.

## Šta rezultat NE dokazuje

* **Semantički pogodak nije dokaz da model „razume".** „Headphones" za
  „something to listen to music with" znači da su vektori blizu u *naučenom
  prostoru* — ne da model zna šta su slušalice, ni da je tekst „istinit".
* **Embedding pretraga može da izvuče plausibilno-ali-nebitno.** Visok skor ne
  znači relevantno; to je blizina u prostoru, ne procena korisnika.
* **Comparison pokazuje pobedu na odabranim upitima** — nije benchmark.
  Drugačiji upiti/katalog mogu da promene redosled (keyword je najbolji kad je
  preklapanje očigledno — vidi `smartphone`).
* **Embedding preporuke nisu personalizovane.** One mere *sličnost proizvoda*
  (semantičku), ne preferencije korisnika — kao Day 5 content, samo u drugom
  prostoru. Personalizacija je Day 8/9/12.
* **Hash fallback NIJE semantic.** Kad store koristi `HashEmbedder`, blizina je
  bag-of-words + random projection, ne naučeno značenje — to je *degradirani*
  režim (offline), dokumentovan u metadata.json.

## Vežbe

1. **Napiši brute-force NN sam** — u `Day 10/lab/` implementiraj `normalize`,
   `cosine_similarity`, `brute_force_nearest`, `semantic_search_lite` na malim
   numpy strukturama i proveri `test_lab.py`. (Acceptance: brute-force NN petlja
   je student-written.)
2. **Dodaj category token u embedding input** — `generate_all_embeddings`
   koristi `product_text` (koji već sadrži kategoriju). Probaj da *izbaciš*
   kategoriju (tekst = name + description) i regeneriši store — kako se
   preporuke menjaju? (Category u embedding input je vežba iz DAY-BRIEFS-a.)
3. **Save/load determinizam** — pokreni `generate_embeddings` dva puta i uporedi
   sha256; promeni `--seed` (hash embedder) i vidi kako se store menja.
4. **Fallback kad model nije dostupan** — obriši `embeddings.npz`, namesti
   `--embedder hash`, regeneriši; pitaj `GET /search/semantic` — zašto je
   `embedder=hash` i zašto su rezultati drugačiji? (Fallback test.)
5. **Keyword bez stopworda** — privremeno izbaci `STOPWORDS` (`app/recommenders/embeddings.py`) iz
   `keyword_search` i pitaj „wireless earbuds for travel" — zašto sad vraća
   sve proizvode? (Bug demo.)
6. **Uporedi sa Day 5 content** — za isti proizvod pokreni
   `GET /recommendations/semantic/{id}` i `GET /recommendations/content/{id}`.
   Gde se poklapaju, gde se razlikuju? (Embedding vs TF-IDF prostor.)
7. **Dodaj `recommendations/semantic` u feedback loop** — na product stranici
   loguj impresije/klikove semantic preporuka kroz
   `POST /recommendations/events` (source=`semantic`) i vidi ih u CTR dashboardu.
8. **Vreme brute-force-a** — izmeri `find_nearest_products` na `252` proizvoda
   (npr. `timeit`); koliko traje? Koliko bi trajalo na 1M proizvoda? (Uvod u
   ANN.)
9. **Promeni embedder** — regeneriši store sa `--embedder st:sentence-transformers/all-mpnet-base-v2` (veći i u benchmark-ovima jači model, 768-dim) i uporedi `comparison.csv`. Koji upiti menjaju rezultat? (`paraphrase-MiniLM-L6-v2` je iste veličine kao `all-MiniLM-L6-v2`, nije „jači“.)

## Sažetak

Napravio si **semantic search i embedding preporuke**: dense embedding store
(`STEmbedder`/`HashEmbedder`, `generate_all_embeddings`,
`save_embeddings`/`load_embeddings`), **brute-force najbliže susede**
(`cosine_similarity_bruteforce`, `find_nearest_products`, `semantic_search` —
bez ANN biblioteke), izložene kroz `GET /search/semantic` i `GET /recommendations/ semantic/{product_id}` i integrisane u CMS (search stranica + product stranica).
Dodao si **keyword-vs-TFIDF-vs-embedding comparison** (`Day 10/data/ comparison.csv`) i **fallback za missing embeddings** (nikad tihi `[]`).
Centralna lekcija: *semantički pogodak je blizina vektora u naučenom prostoru,
ne dokaz da model razume* — a upit i produkti moraju da budu u istom prostoru.
Sledeći korak (Day 11) generiše tekst sa LLM-om; Day 12 povezuje sve u capstone.

---

<!-- page_id 431 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/comparison.csv

```
query,method,rank,product_id,name,category_id,score
smartphone,keyword,1,2,Smartphone Compact 854,1,1.0
smartphone,keyword,2,1,Smartphone Compact 686,1,1.0
smartphone,tfidf,1,1,Smartphone Compact 686,1,0.4071
smartphone,tfidf,2,2,Smartphone Compact 854,1,0.3996
smartphone,embedding,1,2,Smartphone Compact 854,1,0.6093
smartphone,embedding,2,1,Smartphone Compact 686,1,0.5925
smartphone,embedding,3,7,Tablet Compact 853,1,0.4498
something to listen to music with,keyword,1,231,Studio Headphones Classic 686,11,1.0
something to listen to music with,keyword,2,223,Ukulele Premium 117,11,1.0
something to listen to music with,keyword,3,224,Ukulele Essential 759,11,1.0
something to listen to music with,tfidf,1,227,Music Stand Everyday 471,11,0.4665
something to listen to music with,tfidf,2,228,Music Stand Pro 759,11,0.4526
something to listen to music with,tfidf,3,224,Ukulele Essential 759,11,0.1779
something to listen to music with,embedding,1,227,Music Stand Everyday 471,11,0.4427
something to listen to music with,embedding,2,217,Studio Headphones Essential 159,11,0.3885
something to listen to music with,embedding,3,231,Studio Headphones Classic 686,11,0.3824
a book to read before bed,keyword,1,52,Fantasy Pro 681,3,1.0
a book to read before bed,keyword,2,177,Bed Frame Eco 577,9,1.0
a book to read before bed,keyword,3,178,Bed Frame Essential 340,9,1.0
a book to read before bed,tfidf,1,177,Bed Frame Eco 577,9,0.3467
a book to read before bed,tfidf,2,178,Bed Frame Essential 340,9,0.3433
a book to read before bed,tfidf,3,58,Children's Book Deluxe 173,3,0.2965
a book to read before bed,embedding,1,60,Poetry Everyday 604,3,0.3908
a book to read before bed,embedding,2,46,Thriller Premium 108,3,0.3854
a book to read before bed,embedding,3,51,Fantasy Premium 823,3,0.3843
fitness and training gear,keyword,1,80,Fitness Band Eco 108,4,2.0
fitness and training gear,keyword,2,81,Fitness Band Deluxe 954,4,2.0
fitness and training gear,keyword,3,19,Smartwatch Premium 103,1,1.0
fitness and training gear,tfidf,1,80,Fitness Band Eco 108,4,0.3418
fitness and training gear,tfidf,2,81,Fitness Band Deluxe 954,4,0.3403
fitness and training gear,tfidf,3,20,Smartwatch Everyday 615,1,0.1386
fitness and training gear,embedding,1,71,Bicycle Everyday 242,4,0.477
fitness and training gear,embedding,2,84,Bicycle Eco 162,4,0.429
fitness and training gear,embedding,3,70,Bicycle Compact 781,4,0.4074
home cooking essentials,keyword,1,90,Table Lamp Eco 643,5,1.0
home cooking essentials,keyword,2,85,Blender Classic 334,5,1.0
home cooking essentials,keyword,3,93,Towel Set Eco 365,5,1.0
home cooking essentials,tfidf,1,162,Spice Set Pro 698,8,0.1925
home cooking essentials,tfidf,2,163,Spice Set Premium 106,8,0.187
home cooking essentials,tfidf,3,173,Desk Eco 120,9,0.0891
home cooking essentials,embedding,1,48,Cookbook Essential 136,3,0.5446
home cooking essentials,embedding,2,153,Dark Chocolate Essential 370,8,0.4586
home cooking essentials,embedding,3,163,Spice Set Premium 106,8,0.4216
wireless earbuds for travel,keyword,1,6,Headphones Compact 103,1,1.0
wireless earbuds for travel,keyword,2,13,Mouse Deluxe 406,1,1.0
wireless earbuds for travel,keyword,3,55,Guide Everyday 453,3,1.0
wireless earbuds for travel,tfidf,1,55,Guide Everyday 453,3,0.2028
wireless earbuds for travel,tfidf,2,56,Guide Eco 397,3,0.2021
wireless earbuds for travel,tfidf,3,14,Mouse Eco 475,1,0.1569
wireless earbuds for travel,embedding,1,6,Headphones Compact 103,1,0.5089
wireless earbuds for travel,embedding,2,5,Headphones Deluxe 350,1,0.4548
wireless earbuds for travel,embedding,3,16,Speaker Eco 174,1,0.3169
```

### data/embeddings.json

```
{
  "dataset": "dm_semantic_v1",
  "embedder": {
    "name": "sentence-transformers:sentence-transformers/all-MiniLM-L6-v2",
    "params": {}
  }
}
```

### data/metadata.json

```
{
  "dataset": "dm_semantic_v1",
  "description": "Dense product embedding store (Day 10) + keyword-vs-TFIDF-vs-embedding comparison. embeddings.npz holds the n_products x dim matrix aligned with products_text.csv, plus the embedder descriptor. comparison.csv runs known queries through keyword_search (token overlap), TF-IDF (Day 5 build_tfidf_matrix) and semantic_search (embedding, brute-force NN) and records top-k hits per method.",
  "source": "derived",
  "derived_from": {
    "products": "Day 5/data/products_text.csv",
    "module": "app.data.generate_embeddings",
    "function": "generate_embeddings",
    "embedding_module": "app.recommenders.embeddings"
  },
  "embedder": {
    "name": "sentence-transformers:sentence-transformers/all-MiniLM-L6-v2",
    "params": {}
  },
  "embedder_note": "ST = sentence-transformers (naučen, semantički); hash = deterministički fallback (bag-of-words + seeded random projection, bez modela). Query i produkti moraju da budu u ISTOM prostoru — servis čita descriptor iz store-a i kodiramo upit istim embedderom.",
  "parameters": {
    "top_k": 3,
    "queries": [
      "smartphone",
      "something to listen to music with",
      "a book to read before bed",
      "fitness and training gear",
      "home cooking essentials",
      "wireless earbuds for travel"
    ],
    "hash_dim": 64,
    "hash_seed": 42
  },
  "columns": {
    "embeddings.npz": {
      "matrix": "float, (252 x 384) — L2 normalizovani dense embedding reda po products_text.csv",
      "product_ids": "int, stabilni ID-evi proizvoda (isti redosled kao matrix)",
      "embedder_name": "str, naziv embeddera (npr. sentence-transformers:... ili hash)",
      "embedder_params": "str, JSON parametri embeddera (npr. embedding_dim, seed)"
    },
    "comparison.csv": {
      "query": "str, upit (poznat, iz --queries)",
      "method": "str, keyword | tfidf | embedding",
      "rank": "int, 1=prvi pogodak",
      "product_id": "int, pogodak",
      "name": "str, naziv proizvoda",
      "category_id": "int, kategorija",
      "score": "float, skor metode (overlap count / kosinusna sličnost)"
    }
  },
  "counts": {
    "n_products": 252,
    "dim": 384,
    "n_queries": 6,
    "n_comparison_rows": 52
  },
  "summary": [
    {
      "query": "smartphone",
      "top": {
        "keyword": [
          "Smartphone Compact 854",
          "Smartphone Compact 686"
        ],
        "tfidf": [
          "Smartphone Compact 686",
          "Smartphone Compact 854"
        ],
        "embedding": [
          "Smartphone Compact 854",
          "Smartphone Compact 686",
          "Tablet Compact 853"
        ]
      }
    },
    {
      "query": "something to listen to music with",
      "top": {
        "keyword": [
          "Studio Headphones Classic 686",
          "Ukulele Premium 117",
          "Ukulele Essential 759"
        ],
        "tfidf": [
          "Music Stand Everyday 471",
          "Music Stand Pro 759",
          "Ukulele Essential 759"
        ],
        "embedding": [
          "Music Stand Everyday 471",
          "Studio Headphones Essential 159",
          "Studio Headphones Classic 686"
        ]
      }
    },
    {
      "query": "a book to read before bed",
      "top": {
        "keyword": [
          "Fantasy Pro 681",
          "Bed Frame Eco 577",
          "Bed Frame Essential 340"
        ],
        "tfidf": [
          "Bed Frame Eco 577",
          "Bed Frame Essential 340",
          "Children's Book Deluxe 173"
        ],
        "embedding": [
          "Poetry Everyday 604",
          "Thriller Premium 108",
          "Fantasy Premium 823"
        ]
      }
    },
    {
      "query": "fitness and training gear",
      "top": {
        "keyword": [
          "Fitness Band Eco 108",
          "Fitness Band Deluxe 954",
          "Smartwatch Premium 103"
        ],
        "tfidf": [
          "Fitness Band Eco 108",
          "Fitness Band Deluxe 954",
          "Smartwatch Everyday 615"
        ],
        "embedding": [
          "Bicycle Everyday 242",
          "Bicycle Eco 162",
          "Bicycle Compact 781"
        ]
      }
    },
    {
      "query": "home cooking essentials",
      "top": {
        "keyword": [
          "Table Lamp Eco 643",
          "Blender Classic 334",
          "Towel Set Eco 365"
        ],
        "tfidf": [
          "Spice Set Pro 698",
          "Spice Set Premium 106",
          "Desk Eco 120"
        ],
        "embedding": [
          "Cookbook Essential 136",
          "Dark Chocolate Essential 370",
          "Spice Set Premium 106"
        ]
      }
    },
    {
      "query": "wireless earbuds for travel",
      "top": {
        "keyword": [
          "Headphones Compact 103",
          "Mouse Deluxe 406",
          "Guide Everyday 453"
        ],
        "tfidf": [
          "Guide Everyday 453",
          "Guide Eco 397",
          "Mouse Eco 475"
        ],
        "embedding": [
          "Headphones Compact 103",
          "Headphones Deluxe 350",
          "Speaker Eco 174"
        ]
      }
    }
  ],
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded: regeneration with the same embedder and inputs reproduces the store byte-for-byte. ST values are deterministic for a given model; hash values are seeded.",
  "manifest": {
    "sha256": {
      "embeddings.npz": "b2cd3275aaf7442fb566405788b41ec23416028776d4772fa368e25f112e6fef",
      "embeddings.json": "e4a9d9b66d03a5966bef05dd4be38b92bf0556096ee59f3aa0c94b156b4af607",
      "comparison.csv": "9f26d1c886ff7462b5538cdbe070e0a0c912ad5e9d147201ef03e50df8edafcb"
    }
  }
}
```

### data/README.md

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

### examples/demo\_semantic.py

```
"""Demo: semantic search i embedding preporuke (Day 10).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 10/examples/demo_semantic.py"

Prikazuje:
  1) **embedding store** — učitavanje iz ``Day 10/data/embeddings.npz``
     (n_products, dim, embedder);
  2) **semantičku pretragu** — ``semantic_search`` na poznatim upitima
     (npr. „wireless earbuds for travel" -> Headphones iako nema zajedničkih reči);
  3) **embedding preporuke** — ``recommendations_for_product`` (najbliži susedi,
     bez targeta);
  4) **cold-start fallback** — proizvod bez embeddinga -> popularity
     (``fallback_reason="no_embedding"``, NIKAD tihi []);
  5) **embedding vs content preporuke** — poređenje sa Day 5 TF-IDF content
     recs-ima (preklapanje i razlika);
  6) **keyword vs TFIDF vs embedding** — summary iz ``Day 10/data/comparison.csv``
     (gde koji pristup „vara").
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.recommenders.content import build_tfidf_matrix, recommend_similar_products
from app.services.semantic import SemanticService

DEMO_QUERIES = [
    "wireless earbuds for travel",
    "a book to read before bed",
    "home cooking essentials",
]
DEMO_PRODUCT = 22  # Jacket (fashion)


def _names(results) -> str:
    if hasattr(results, "to_dict"):
        results = results.to_dict("records")
    return ", ".join(r["name"] for r in list(results)[:3])


def main() -> None:
    print("=== Day 10 — Semantic Search and Embedding-Based Recommendations ===\n")
    svc = SemanticService()

    # --- 1) Embedding store ------------------------------------------------ #
    res = svc.semantic_search("smartphone", limit=1)
    store = res["store"]
    print(f"[1] Embedding store: n_products={store['n_products']}  "
          f"dim={store['dim']}  embedder={res['embedder']}")
    print()

    # --- 2) Semantička pretraga -------------------------------------------- #
    print("[2] Semantička pretraga (upit bez zajedničkih reči -> semantički hit):")
    for q in DEMO_QUERIES:
        r = svc.semantic_search(q, limit=3)
        status = "SEMANTIC" if r["method"] == "semantic" else "FALLBACK"
        print(f"    {q!r:38s} [{status}] {_names(r['results'])}")
    print()

    # --- 3) Embedding preporuke -------------------------------------------- #
    print(f"[3] Embedding preporuke za proizvod {DEMO_PRODUCT} "
          f"({svc.products.loc[svc.products['product_id'] == DEMO_PRODUCT, 'name'].iloc[0]}):")
    recs = svc.recommendations_for_product(DEMO_PRODUCT, limit=3)
    for r in recs["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<18} score={r['score']:.4f}")
    print()

    # --- 4) Cold-start fallback -------------------------------------------- #
    print("[4] Cold-start fallback (proizvod bez embeddinga '99999'):")
    cs = svc.recommendations_for_product(99999, limit=3)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-3: "
          f"{_names(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 5) Embedding vs content preporuke ----------------------------------- #
    print(f"[5] Embedding recs vs Day 5 content recs za proizvod {DEMO_PRODUCT}:")
    products: pd.DataFrame = svc.products
    tfidf, _vectorizer = build_tfidf_matrix(products, min_df=2)  # iste postavke kao Day 5 servis
    content = recommend_similar_products(products, DEMO_PRODUCT, tfidf, limit=5)
    content_recs = content["recommendations"]  # lista dict-ova (envelope)
    sem_ids = {r["product_id"] for r in recs["recommendations"]}
    cont_ids = {r["product_id"] for r in content_recs}
    print(f"    semantic: {_names(recs['recommendations'])}")
    print(f"    content : {_names(content_recs)}")
    print(f"    overlap : {len(sem_ids & cont_ids)} od {len(sem_ids | cont_ids)} "
          f"(slično u drugom prostoru, ne identično)")
    print()

    # --- 6) Keyword vs TFIDF vs embedding ----------------------------------- #
    print("[6] Keyword vs TFIDF vs embedding (Day 10/data/comparison.csv):")
    try:
        comp = svc.comparison()
        seen = set()
        for row in comp["comparison"]:
            if row["query"] in seen:
                continue
            seen.add(row["query"])
            kw = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "keyword"), None)
            tf = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "tfidf"), None)
            em = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "embedding"), None)
            print(f"    {row['query']!r}")
            print(f"        keyword  = {kw['name'] if kw else '—'}")
            print(f"        tfidf    = {tf['name'] if tf else '—'}")
            print(f"        embedding= {em['name'] if em else '—'}")
        print("    (vidi gde embedding pobeđuje, a gde keyword 'vara' — npr. 'bed'.)")
    except FileNotFoundError as exc:
        print(f"    {exc}")
    print()

    print("API: GET /search/semantic?q=… · GET /recommendations/semantic/{product_id}")
    print("Lab: Day 10/lab — brute-force NN petlja pišeš SAM.")


if __name__ == "__main__":
    main()
```

### lab/README.md

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

### lab/starter.py

```
"""Starter za Day 10 lab — brute-force nearest neighbors (student-written).

Implementiraš mali deo onoga što kursni modul
``dm-ml/app/recommenders/embeddings.py`` već sadrži (da razumeš *šta* semantička
pretraga i kosinusna sličnost rade). Ne menjaš ``dm-ml`` — radiš u ovom fajlu i
proveravaš svoje rešenje sa ``test_lab.py``.

Lab radi na malim, ručno napravljenim numpy strukturama — nema pandas-a, nema
embedding modela, nema ANN biblioteke.
"""

import numpy as np


# --------------------------------------------------------------------------- #
# 1) normalize — L2 normalizacija redova
# --------------------------------------------------------------------------- #
def normalize(vectors):
    """L2-normalizuje svaki red (vektor -> jedinični vektor).

    ``vectors`` je ``np.ndarray`` oblika ``(n, dim)`` (ili ``(dim,)``).
    Nula-red (norma 0) ostaje nula-red — kosinus sa njim je 0, ne ``NaN``.

    Zašto: kosinus sličnost nenormalizovanih vektora meša dužine (čest bag).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) cosine_similarity — kosinusna sličnost upita sa svakim redom
# --------------------------------------------------------------------------- #
def cosine_similarity(query_vec, matrix):
    """Kosinusne sličnosti ``query_vec`` (1-D) sa svakim redom ``matrix``.

    Vraća 1-D ``np.ndarray`` dužine ``matrix.shape[0]``, redom kao ``matrix``.
    NORMALIZUJ OBA ULAGA (preko ``normalize``) — to je lekcija dana.

    Za ``n`` normalizovanih vektora, kosinus = skalarni proizvod:
    ``matrix @ query``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) brute_force_nearest — top-k najbližih suseda (brute-force petlja)
# --------------------------------------------------------------------------- #
def brute_force_nearest(matrix, query_vec, k=3, exclude_index=None):
    """Top-``k`` ``(index, score)`` po kosinusnoj sličnosti, opadajuće.

    ``matrix`` je ``(n, dim)``; ``query_vec`` je ``(dim,)``. Redni brojevi
    rezultata se odnose na ``matrix`` (ne na product_id — to je posao
    pozivaoca). ``exclude_index`` (opciono) se izbacuje iz rezultata („ne
    preporučuj sam sebe").

    Vraća listu ``[(index, score), ...]`` — **ovo je brute-force petlja** koju
    ANN biblioteke (faiss/annoy) rade pametnije na velikim skupovima.
    """
    # TODO: implementiraj (koristi cosine_similarity, pa sortiraj opadajuće)
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) semantic_search_lite — top-k proizvoda za embedding upita
# --------------------------------------------------------------------------- #
def semantic_search_lite(products, embeddings, query_embedding, k=3):
    """Top-``k`` proizvoda za dati embedding upita (brute-force).

    ``products`` = lista dict-ova ``{"product_id": int, "name": str}``;
    ``embeddings`` = ``np.ndarray`` ``(len(products), dim)`` — red ``i`` je
    embedding proizvoda ``i`` (ISTI redosled kao ``products``).

    Vraća listu dict-ova ``{"product_id": int, "name": str, "score": float}``,
    opadajuće po skoru. (Ne menja ``products``.)
    """
    # TODO: implementiraj (brute_force_nearest, pa mapiraj na products)
    raise NotImplementedError
```

### lab/test_lab.py

```
import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import numpy as np


def test_normalize_zero_row():
    n = lab.normalize(np.array([[3.0, 4.0], [0.0, 0.0]]))
    assert np.allclose(n[0], [0.6, 0.8]) and np.allclose(n[1], [0, 0]) and not np.isnan(n).any()


def test_cosine_normalizes_both():
    m = np.array([[10.0, 0.0], [0.0, 0.1], [1.0, 1.0]])
    s = lab.cosine_similarity(np.array([5.0, 0.0]), m)
    assert np.allclose(s, [1.0, 0.0, 1 / np.sqrt(2)])


def test_nearest_and_search():
    m = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]])
    r = lab.brute_force_nearest(m, m[0], k=2, exclude_index=0)
    assert [i for i, _ in r] == [1, 2]
    prods = [{"product_id": 10, "name": "a"}, {"product_id": 11, "name": "b"}, {"product_id": 12, "name": "c"}]
    hits = lab.semantic_search_lite(prods, m, np.array([0.0, 1.0]), k=1)
    assert hits[0]["product_id"] == 12 and hits[0]["score"] == pytest.approx(1.0)
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 10 lab-a (brute-force NN, bez ANN biblioteka)."""
from __future__ import annotations

import time

import numpy as np


def normalize(vectors):
    v = np.asarray(vectors, dtype=float)
    if v.ndim == 1:
        n = np.linalg.norm(v)
        return v / n if n > 0 else v.copy()
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return np.divide(v, n, out=np.zeros_like(v), where=n > 0)


def cosine_similarity(query_vec, matrix):
    return normalize(matrix) @ normalize(query_vec)


def brute_force_nearest(matrix, query_vec, k=3, exclude_index=None):
    s = cosine_similarity(query_vec, matrix)
    order = sorted(range(len(s)), key=lambda i: (-s[i], i))
    return [(i, float(s[i])) for i in order if i != exclude_index][:k]


def semantic_search_lite(products, embeddings, query_embedding, k=3):
    return [{"product_id": products[i]["product_id"], "name": products[i]["name"], "score": s}
            for i, s in brute_force_nearest(embeddings, query_embedding, k)]


def time_brute_force(n=252, dim=384, repeats=20, seed=42):
    """Vežba: izmeri brute-force na n proizvoda i linearno ekstrapoliraj na 1_000_000."""
    rng = np.random.default_rng(seed)
    m, q = rng.normal(size=(n, dim)), rng.normal(size=dim)
    t0 = time.perf_counter()
    for _ in range(repeats):
        brute_force_nearest(m, q, 3)
    per = (time.perf_counter() - t0) / repeats
    return {"n": n, "seconds_per_query": per, "extrapolated_1m_seconds": per * 1_000_000 / n}


if __name__ == "__main__":
    print(time_brute_force())
```
