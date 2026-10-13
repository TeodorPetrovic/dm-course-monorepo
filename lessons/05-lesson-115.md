# Dan 5 — Content-Based Product Recommender

- lesson_id: 115
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:46.713 updated: 2026-09-05 20:00:28.696
- summary: Sličan tekst nije ista stvar kao dobra preporuka. Popularnost i kategorija su obavezni baseline; TF-IDF + kosinusna sličnost su content preporuke — i kada preporuči „Smartphone Compact 854" za „Smartphone Compact 686", to je sadržajna sličnost, ne dokaz da će je korisnik voleti. [subjects-import]


---

<!-- page_id 420 order 0 -->
## [Page] Materijal

# Dan 5 — Content-Based Product Recommender

> *Sličan tekst nije ista stvar kao dobra preporuka. Popularnost i kategorija su
> obavezni baseline; TF-IDF + kosinusna sličnost su content preporuke — i kada
> preporuči „Smartphone Compact 854" za „Smartphone Compact 686", to je sadržajna sličnost,
> ne dokaz da će je korisnik voleti.*

## Šta gradimo

Content-based recommender: **popularity** i **category** baseline (obavezne
referentne tačke), zatim TF-IDF vektori teksta proizvoda + **kosinusna
sličnost** → preporuke sličnih proizvoda, izloženo kroz
`GET /recommendations/content/{product_id}`, `/recommendations/popular`,
`/recommendations/category/{product_id}` i integrisano u product page. Cilj dana
je da razdvoji **content-sličnost** (šta je tekstualno slično) od **preferencije**
(šta korisnik voli) — i da pokaže da svaka preporuka mora imati baseline za
poređenje.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `recommend_popular` | **statistical** (brojanje događaja; baseline bez ML-a) |
| `recommend_same_category` | **rule / heuristic** (baseline) |
| `prepare_product_text` | **data preprocessing** (tekst → tokeni) |
| `build_tfidf_matrix` | **statistical** (TF-IDF težine reči — nema naučenih parametara) |
| `calculate_product_similarity` | **statistical** (kosinusna sličnost) |
| `recommend_similar_products` | **statistical** (rank + cold-start fallback) |

## Application requirement

Product page u `dm-frontend` već ima „Recommended Products" sekciju, ali je
pozivala legacy `GET /recommendations/{product_id}` placeholder (Day 1: biznis
pravilo „ista kategorija"). Day 5 zamenjuje taj poziv pravim content
recommender-om (sa popularity/category baseline-om i fallback-om). Bez toga,
product page nema ništa smisleno da pokaže — ili padne na tiho prazno stanje.

## Ciljevi učenja

Do kraja dana treba da:

* implementirate **popularity** i **category** baseline (i objasnite zašto su
  obavezni kao referentne tačke);
* preprocessujete tekst proizvoda (naziv + opis + kategorija) za TF-IDF;
* izgradite **TF-IDF matricu** i izračunate **kosinusnu sličnost**;
* preporučite slične proizvode **bez targeta** (target exclusion je ugovor);
* rešite **cold start** (nov proizvod bez TF-IDF reda) eksplicitnim fallback-om
  — nikad tihi `[]`;
* objasnite **overspecialization** (226/252 proizvoda ima blizanca sa kosinusom ≥ 0.8 —
  preporuka će rado predložiti skoro-duplikat);
* dokumentujete **baseline comparison** (popularity/category vs content).

## Preduslovi

Day 1 katalog proizvoda (tekst), sklearn `TfidfVectorizer`, kosinusna sličnost,
FastAPI rute (Day 1–4).

## Postojeći sistem (šta nasleđujemo)

* **Day 1 sloj:** seeded katalog (252 proizvoda, 12 kategorija) + događaji
  (183.468) + legacy `GET /recommendations/{product_id}` (biznis pravilo).
* **Day 4 sloj:** targeting servis (predikcija → odluka) sa pravilima i
  fallback-om — ista filozofija „nikad tiho prazno" se nastavlja i ovde.
* **Nedostaje:** bilo kakva *sadržajna* preporuka. Product page poziva
  placeholder koji nije ni ML ni merljiv; Day 5 uvodi prave baseline-ove i
  content recommender sa evaluacijom.

## Arhitektura

```
Day 1 katalog (products.csv + categories.csv)   Day 1 događaji (events.csv)
      │                                                    │
      ▼                                                    ▼
app/data/generate_product_text.py  product_text korpus   popularity (view=1, cart=3, buy=5)
      │                                                    │
      ▼                                                    ▼
app/recommenders/content.py    recommend_popular / recommend_same_category (baseline)
                               prepare_product_text -> build_tfidf_matrix
                               -> calculate_product_similarity
                               -> recommend_similar_products (rank + cold-start fallback)
      │
      ▼
app/services/recommender.py    RecommenderService (content/popular/category + comparison)
      │
      ▼
app/api/recommendation_routes.py   GET /recommendations/popular
                                   GET /recommendations/category/{product_id}
                                   GET /recommendations/content/{product_id}
      │
      ▼
dm-frontend product page   product/[slug].vue -> /ml/recommendations/content/{id}
```

## Korišćeni podaci

**Product text korpus** (seeded, `Day 5/data/products_text.csv`, jedini izvor:
`app/data/generate_product_text.py`) — 252 proizvoda, izvedena tabela (ne
duplira Day 1):

| Kolona | Značenje |
| --- | --- |
| `product_id` / `category_id` / `category_name` | katalog + kategorija (name je token) |
| `name` / `slug` / `description` / `img_url` / `price` | za prikaz i tekst |
| `product_text` | `category_name + name + description` — ulaz u TF-IDF |
| `popularity` | težinski zbir događaja (`view`=1, `add_to_cart`=3, `purchase`=5) |

Stanje: 252 proizvoda, svi imaju događaje; popularnost min **70** · med **288** ·
max **2115**; top-5 po popularnosti: **90, 184, 110, 12, 49**.

## AI-ML koncept

* **Baseline-i su obavezni.** „Preporuke izgledaju dobro" nije evaluacija.
  `recommend_popular` (šta svi gledaju) i `recommend_same_category` (ista
  kategorija) su najjednostavniji mogući modeli — svaka tvrdnja „content
  pomaže" mora da stoji pored njih.
* **TF-IDF.** Tekst proizvoda (`category + name + description`) se vektorizuje:
  term frequency × inverse document frequency. Retki termini (koji razlikuju
  proizvode) dobijaju veću težinu; „synthetic catalog item" (u svim opisima)
  dobija nisku težinu — ali ne nestaje. Redovi su **L2-normalizovani**, pa je
  kosinusna sličnost = skalarni proizvod vektora (ne porediš raw counts).
* **Kosinusna sličnost.** kosinus reda `i` sa matricom (`calculate_product_similarity(tfidf_matrix, index)`) — koliko je tekst
  proizvoda `i` usmeren isto kao tekstovi ostalih. Sličnost 1.0 = isti rečnik
  (u našem seed-u: isti naziv + ista kategorija + isti boilerplate).
* **Target exclusion.** Proizvod se NIKAD ne preporučuje sam sebi — to je
  ugovor sa testom (DAY-BRIEFS „Common bugs": „including the target product in
  its own recommendations").
* **Cold start.** Nov proizvod (nema TF-IDF red) nema sličnosti — umesto
  tihog `[]`, vraća se **popularity fallback** sa `fallback=true` i razlogom.
* **Overspecialization.** Sličan tekst ≠ dobra preporuka. Pošto 226/252
  proizvoda ima blizanca sa kosinusom ≥ 0.8 (isti tip proizvoda + ista kategorija +
  skoro isti opis), recommender će rado predložiti skoro-duplikat — to je
  *očekivano* ponašanje content modela, ne bag.

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Baselines (`app/recommenders/content.py`)

`recommend_popular(products_df, events_df, limit)` — popularnost iz kolone
`popularity` (ili iz događaja, ili 1.0 za sve — deterministički) → top-N.
`recommend_same_category(products_df, product_id, limit)` — ista kategorija,
**bez targeta**, po popularnosti; nepoznat proizvod -> `ValueError`. Oba vraćaju
iste kolone (`RECOMMENDATION_COLUMNS` sa `score`) — baseline i content su
uporedivi.

### Korak 2 — Tekst i TF-IDF (`prepare_product_text`, `build_tfidf_matrix`)

`prepare_product_text` gradi `category_name + name + description` (kategorija je
token; `category_tokens` mapa omogućava proširivanje teksta — vežba).
`build_tfidf_matrix` radi `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)` (servis; modul ima `min_df=1` default) →
`(matrix, vectorizer)`, poravnato sa `products_df`.

### Korak 3 — Sličnost i preporuke (`calculate_product_similarity`, `recommend_similar_products`)

`calculate_product_similarity(tfidf_matrix, index)` — kosinusna sličnost reda `index`
sa svim redovima. `recommend_similar_products` — sličnosti → **isključi target**
→ top-N po `score` (tie-break `product_id`). Cold start: nepoznat proizvod →
`fallback="unknown_product"` na popularity; prazan red → `fallback="no_text"`.
Vraća envelope `{product_id, method, fallback, fallback_reason, recommendations}` — servis ga pretvara u JSON.

### Korak 4 — Servis + API (`app/services/recommender.py`, `app/api/recommendation_routes.py`)

`RecommenderService` učitava `Day 5/data/products_text.csv`, gradi TF-IDF
**lazy** (jednom, kešira), i nudi `popular_recommendations` /
`category_recommendations` / `content_recommendations` /
`baseline_comparison`. API rute su u `app/api/recommendation_routes.py` (uključene preko `app/api/routes.py`).

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `recommend_popular(...)` | popularity baseline (top-N, bez ML-a) | `app/recommenders/content.py` |
| `recommend_same_category(...)` | category baseline (ista kategorija, bez targeta) | `app/recommenders/content.py` |
| `prepare_product_text(...)` | tekst za TF-IDF (category + name + description) | `app/recommenders/content.py` |
| `build_tfidf_matrix(...)` | TF-IDF matrica + vectorizer | `app/recommenders/content.py` |
| `calculate_product_similarity(...)` | kosinusna sličnost reda sa svima | `app/recommenders/content.py` |
| `recommend_similar_products(...)` | rank + target exclusion + cold-start fallback | `app/recommenders/content.py` |
| `RecommenderService.*` | content/popular/category + comparison | `app/services/recommender.py` |
| `app/data/generate_product_text.py` | generiše `Day 5/data/*` (byte-for-byte) | `app/data/generate_product_text.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /recommendations/popular?limit=` | 200: `{method:"popular", fallback:false, recommendations[]}` — top-N po popularnosti |
| `GET /recommendations/category/{product_id}?limit=` | 200: ista kategorija bez targeta; **404** nepoznat proizvod |
| `GET /recommendations/content/{product_id}?limit=` | 200: content (TF-IDF + kosinus); cold start -> **fallback envelope** (`method:"fallback"`, `fallback_reason`, popularity recs); **422** nevalidan limit |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /recommendations/content/1?limit=2`

```
{
  "product_id": 1,
  "method": "content",
  "fallback": false,
  "fallback_reason": null,
  "returned": 2,
  "recommendations": [
    { "product_id": 2, "name": "Smartphone Compact 854", "slug": "smartphone-compact-854",
      "description": "5G smartphone with OLED display, dual camera and fast charging. Compact line, red.",
      "img_url": "/images/products/smartphone-compact-854.jpg", "category_id": 1, "price": 263.99, "score": 0.9145 },
    { "product_id": 17, "name": "Camera Compact 359", "slug": "camera-compact-359",
      "description": "Mirrorless camera with 4K video and interchangeable lens. Compact line, black.",
      "img_url": "/images/products/camera-compact-359.jpg", "category_id": 1, "price": 478.99, "score": 0.2147 }
  ]
}
```

**Cold start:** `GET /recommendations/content/99999` vraća `method="fallback"`,
`fallback=true`, `fallback_reason="unknown_product"` i top-N po popularnosti —
NIKAD tihi `[]`.

## CMS integracija

Product page `dm-frontend/app/pages/product/[slug].vue` (vidi taj fajl):

* Poziva `GET /ml/recommendations/content/{product_id}` (Nitro proxy
  `/ml/**` → `:3001`).
* Renderuje **top-5 content preporuke** (slika, naziv, opis, cena iz `rec.price`
  — umesto hardkodovanog `15$`).
* Ako je `fallback=true` (cold start) prikazuje poruku „showing popularity
  fallback".
* **Graceful fallback:** ako dm-ml ne radi, `try/catch` → prazna lista — stranica
  se NE ruši.
* Klik na preporuku šalje `recommendation_click` sa `recommendation_source="content"`
  (Day 1 šema — feedback podatak za Day 9).

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 5/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno: `recommend_popular` (popularity kolona, iz događaja, default 1.0,
exclude, kolone, limit), `recommend_same_category` (ista kategorija, bez targeta,
po popularnosti, nepoznat proizvod), `prepare_product_text` (naziv+opis+kategorija,
index po product\_id, bez kategorije, category\_tokens), `build_tfidf_matrix`
(oblik, L2 normalizacija, ngram/min\_df opcije), `calculate_product_similarity`
(samo-sličnost 1.0, isti rečnik najbliži, van opsega), `recommend_similar_products`
(**target exclusion**, isti rečnik prvi, sortiranje, **unknown\_product fallback**,
**no\_text fallback**, limit, kolone), API (popular 200/422, category 200/404,
content 200 bez targeta, **cold-start fallback 200 + fallback=true**).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 5/examples/demo_content_recommender.py"`
   — baselines, content preporuke, cold-start fallback i baseline comparison.
2. Pokreni vizualizaciju: `dm-ml/.venv/bin/python "Day 5/examples/visualize_content.py"`
   — `cosine_heatmap.png` (sličnost 24 proizvoda iz 2 kategorije; blokovi +
   dijagonalni parovi) i `baseline_overlap.png` (content ∩ category/popular).
3. Pusti servis pa pitaj `GET /recommendations/content/1?limit=5` — uporedi sa
   `/recommendations/category/1` i `/recommendations/popular`.
4. Pokreni lab (`Day 5/lab/`) — ponovo implementiraj funkcije na malom katalogu
   i proveri `test_lab.py`.
5. Promeni `min_df`/`ngram_range` u `TFIDF_KWARGS` (servis) i ponovo pitaj —
   kako se menja redosled? (min\_df=2 skida model brojeve; ngram (1,1) skida
   fraze.)

## Comparison (baseline ugao)

**Content vs category vs popular** (top-5, seeded korpus):

| Target | Content top-5 | Category top-5 | content∩category |
| --- | --- | --- | --- |
| 1 (Smartphone Compact 686) | 2, 17, 45, 21, 40 | 12, 2, 9, 6, 17 | `[2, 17]` |
| 2 (Smartphone Compact 854) | 1, 17, 241, 18, 7 | 12, 9, 6, 17, 13 | `[17]` |
| 23 (Jacket Essential 819) | 22, 42, 50, 190, 217 | 30, 41, 37, 31, 36 | — |
| 144 (Toy Train Pro 565) | 143, 235, 94, 162, 69 | 127, 133, 137, 132, 134 | — |
| 232 (Cordless Drill Classic 499) | 233, 183, 111, 31, 134 | 243, 234, 249, 247, 236 | — |

(Category baseline rangira po popularnosti unutar kategorije, pa mu se top-5 retko
poklapa sa tekstualno najsličnijim proizvodima.)

**Distribucija preko svih 252 proizvoda** (top-5):

* **content ∩ category:** mean **0.60** / 5, median **1.0**; **125 proizvoda ima
  NULA poklapanja** — content nalazi tekstualnu sličnost i VAN kategorije (top-1 je
  ipak uvek iz iste kategorije: 252/252).
* **content ∩ popular:** mean **0.16** / 5, median **0.0** — content skoro
  nikad nije popularnost. (Sadržajno slično ≠ popularno.)

Šta se vidi:

* **Content ≠ category.** Proizvod 144 (Toy Train Pro 565, „Wooden toy train set. Pro
  line") dobija content preporuke `[143, 235, 94, 162, 69]` — 235/94/162/69 su
  *Screwdriver Set Pro*, *Towel Set Pro*, *Spice Set Pro*, *Dumbbell Set Pro*: dele tokene
  **"set"** i **"pro"**! Isto tako 23 (Jacket Essential 819) dobija 50 (Biography
  Essential 819) samo zbog zajedničkog broja modela „819". To je tekstualna sličnost
  koja preskače kategoriju. Category baseline to ne vidi (ostaje u svojoj kategoriji).
* **Content ≠ popular.** Najpopularniji proizvod (90, Table Lamp Eco 643) nije najsličniji
  po tekstu — semantički različiti pojmovi dele tekst ne zato što su popularni.
* **Overspecialization.** 226/252 proizvoda ima blizanca sa kosinusom ≥ 0.8
  (medijana najboljeg skora 0.857) — content će predložiti skoro-duplikat
  (Smartphone Compact 686 → Smartphone Compact 854, 0.9145). To je
  *dokaz* da je rezultat content-sličnost, ne preferencija.
* **Gde baseline-i pomažu.** Category je koristan kad je tekst siromašan
  (nema dovoljno signala); popularity je koristan za cold start (nov proizvod
  nema tekst ni kategoriju-signal).

## Evaluacija (kako znamo da je dobro)

* **Target exclusion je ugovor:** ni `content` ni `category` ne vraćaju sam
  proizvod (test).
* **Cold-start fallback je definisan:** nepoznat proizvod -> 200 sa
  `method="fallback"`, `fallback_reason`, popularity preporuke; nema tihog
  `[]` (test).
* **Determinizam:** isti korpus + ista pitanja -> isti redosled (tie-break po
  `product_id`; test). `products_text.csv` byte-for-byte (sha256 u
  `metadata.json`).
* **Normalizovani vektori:** TfidfVectorizer L2-normalizuje redove; kosinusna
  sličnost poredi *ugaone* razlike, ne raw counts (test `rows_normalized`).
* **Baseline comparison je dokumentovan:** README tabela + distribucija
  overlap-a preko svih proizvoda.

## Česti bugovi

* **Uključivanje targeta u sopstvene preporuke** — najsličniji proizvod je sam
  target (score 1.0). Rešenje: isključi target iz kandidata, ne samo „iz
  prikaza" (test).
* **Nema fallback-a za nov proizvod** — endpoint pada (404/500) ili vraća
  prazno. Fallback = popularity baseline sa `fallback=true` (test).
* **Poređenje raw counts umesto normalizovanih vektora** — sirovi TF-IDF
  brojevi favorizuju duge tekstove; kosinus mora ići preko L2-normalizovanih
  redova.
* **Tihi `[]` na grešku** — ako nema sličnosti, mora da se vrati *nešto*
  objašnjeno (fallback), ne prazna lista bez reči.
* **Verovanje da je content preporuka „dobra"** — content nalazi sličan tekst,
  ne preferenciju; bez baseline poređenja ne znaš da li pomaže.
* **min\_df premali/prevelik** — min\_df=1 zadržava model brojeve (npr. `819`, šum);
  min\_df=2 ih skida ali i baca token-e koji se pojave jednom (retke ali
  informativne reči).

## Šta rezultat NE dokazuje

* **Sličan tekst nije dobra preporuka.** Content kaže „ovaj proizvod ima isti
  rečnik" — ne kaže „korisnik će ga voleti". Da bi se to znalo, treba Day 6
  (interakcije) i Day 7 (evaluacija).
* **Score 1.0 nije kvalitet.** Savršeni blizanci (isti naziv + kategorija +
  boilerplate) dobijaju 1.0 — to je overspecialization, ne odobravanje.
* **Cross-category sličnost nije greška modela.** „Paint Set" ~ „Spice Set" je
  stvarna tekstualna sličnost (token „set") — ali kupci ih možda ne doživljavaju
  isto. Content ne zna za namere.
* **Popularnost nije kvalitet.** Najpopularniji proizvod je samo najgledaniji;
  baseline, ne cilj.
* **Brojevi važe za sintetički seed (42).** Na pravom store-u tekst, raspodela i
  popularnost su drugačiji — pipeline ostaje, brojevi se menjaju.
* **Content ne objašnjava zašto.** Kosinusna sličnost je broj; „zašto je ovaj
  sličan" (koji tokeni) je eksploracija, ne ugrađena osobina (Day 10 dodaje
  objašnjivost/embeddinge).

## Vežbe

1. **Target exclusion** — ukloni isključivanje u `recommend_similar_products` i
   pokreni test (`test_content.py::TestRecommendSimilarProducts`): proizvod se
   vraća sam sebi. Zatim vrati i potvrdi da test prolazi.
2. **Cold-start fallback** — pitaj `GET /recommendations/content/99999` i potvrdi
   `method="fallback"`, `fallback_reason="unknown_product"`; proveri da NIJE
   prazan rezultat.
3. **Proširi tekst kategorije** — dodaj `category_tokens` mapu u
   `prepare_product_text` (npr. `{1: "gadgets electronics"}` ) i posmatraj kako
   se menja redosled content preporuka.
4. **Variraj `limit`** — pitaj `/recommendations/content/1?limit=3` vs `limit=10`:
   koja mesta se menjaju? (Score opada; granica je proizvoljna.)
5. **Promeni vektorske opcije** — `min_df=1` vs `min_df=2`, `ngram_range=(1,1)`
   vs `(1,3)` u `TFIDF_KWARGS` — uporedi top-5 za proizvod 1.
6. **Document overspecialization** — nađi primer gde je `score == 1.0` i objasni
   zašto je to content-sličnost, ne preferencija.

## Sažetak

Od praznog „Recommended Products" placeholder-a napravio si **merljiv content
recommender**: popularity i category baseline (obavezne referentne tačke),
TF-IDF tekst proizvoda + kosinusna sličnost, target exclusion kao ugovor, i
**cold-start fallback** na popularity (nikad tihi `[]`). Centralna lekcija:
**sličan tekst ≠ dobra preporuka** — content preporuke su sadržajna sličnost, a
ne preferencija korisnika; zato su baseline-i obavezni, a Day 6 (interakcije) i
Day 7 (evaluacija) su sledeći korak. Pitanje danas: **kada je content-sličnost
dovoljna, a kada treba i podatke o tome šta korisnici zaista rade?**

---

<!-- page_id 421 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/metadata.json

```
{
  "dataset": "dm_product_text_v1",
  "description": "Seeded product-text corpus derived from the Day 1 catalog: one text representation per product (category + name + description) for TF-IDF content recommendations, plus a popularity score computed from Day 1 events (view=1, add_to_cart=3, purchase=5) as the baseline.",
  "source": "derived",
  "derived_from": {
    "products": "Day 1/data/products.csv",
    "categories": "Day 1/data/categories.csv",
    "events": "Day 1/data/events.csv",
    "module": "app.data.generate_product_text",
    "function": "generate_product_text",
    "text_builder": "app.recommenders.content.prepare_product_text",
    "popularity_builder": "app.recommenders.content._popularity_from_events"
  },
  "weights": {
    "product_view": 1.0,
    "add_to_cart": 3.0,
    "purchase": 5.0
  },
  "columns": [
    "product_id",
    "category_id",
    "category_name",
    "name",
    "slug",
    "description",
    "img_url",
    "price",
    "product_text",
    "popularity"
  ],
  "counts": {
    "products": 252,
    "categories": 12,
    "by_category": {
      "1": 21,
      "2": 21,
      "3": 21,
      "4": 21,
      "5": 21,
      "6": 21,
      "7": 21,
      "8": 21,
      "9": 21,
      "10": 21,
      "11": 21,
      "12": 21
    },
    "products_with_events": 252,
    "total_popularity": 108922.0,
    "top_popular": [
      90,
      184,
      110,
      12,
      49
    ]
  },
  "fields": {
    "product_id": "int, stabilan ID proizvoda (FK -> products.product_id)",
    "category_id": "int, FK -> categories.category_id",
    "category_name": "str, naziv kategorije (za tekst — kategorija je token)",
    "name": "str, naziv proizvoda (iz Day 1 kataloga)",
    "slug": "str, URL slug",
    "description": "str, opis proizvoda (iz Day 1 kataloga)",
    "img_url": "str, putanja do slike",
    "price": "float, cena",
    "product_text": "str, tekst za TF-IDF: kategorija + naziv + opis (pripremljen kroz prepare_product_text)",
    "popularity": "float, težinski zbir događaja (view=1, add_to_cart=3, purchase=5) — popularity baseline skor"
  },
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "products_text.csv": "ad00b379283fed0b4e81a53f5a1c847b9d3006cf7d43c4f096ac1fa2153bc3de"
    }
  }
}
```

### data/products\_text.csv

```
product_id,category_id,category_name,name,slug,description,img_url,price,product_text,popularity
1,1,Electronics,Smartphone Compact 686,smartphone-compact-686,"5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",/images/products/smartphone-compact-686.jpg,185.99,"Electronics Smartphone Compact 686 5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",291.0
2,1,Electronics,Smartphone Compact 854,smartphone-compact-854,"5G smartphone with OLED display, dual camera and fast charging. Compact line, red.",/images/products/smartphone-compact-854.jpg,263.99,"Electronics Smartphone Compact 854 5G smartphone with OLED display, dual camera and fast charging. Compact line, red.",1227.0
3,1,Electronics,Laptop Compact 775,laptop-compact-775,"Lightweight laptop for work and study, SSD storage, long battery life. Compact line, grey.",/images/products/laptop-compact-775.jpg,765.99,"Electronics Laptop Compact 775 Lightweight laptop for work and study, SSD storage, long battery life. Compact line, grey.",209.0
4,1,Electronics,Laptop Classic 505,laptop-classic-505,"Lightweight laptop for work and study, SSD storage, long battery life. Classic line, silver.",/images/products/laptop-classic-505.jpg,1393.99,"Electronics Laptop Classic 505 Lightweight laptop for work and study, SSD storage, long battery life. Classic line, silver.",176.0
5,1,Electronics,Headphones Deluxe 350,headphones-deluxe-350,"Wireless over-ear headphones with noise cancelling and 30h battery. Deluxe line, grey.",/images/products/headphones-deluxe-350.jpg,71.99,"Electronics Headphones Deluxe 350 Wireless over-ear headphones with noise cancelling and 30h battery. Deluxe line, grey.",192.0
6,1,Electronics,Headphones Compact 103,headphones-compact-103,"Wireless over-ear headphones with noise cancelling and 30h battery. Compact line, grey.",/images/products/headphones-compact-103.jpg,265.99,"Electronics Headphones Compact 103 Wireless over-ear headphones with noise cancelling and 30h battery. Compact line, grey.",603.0
7,1,Electronics,Tablet Compact 853,tablet-compact-853,"10-inch tablet for streaming, reading and video calls. Compact line, red.",/images/products/tablet-compact-853.jpg,336.99,"Electronics Tablet Compact 853 10-inch tablet for streaming, reading and video calls. Compact line, red.",416.0
8,1,Electronics,Tablet Essential 949,tablet-essential-949,"10-inch tablet for streaming, reading and video calls. Essential line, red.",/images/products/tablet-essential-949.jpg,725.99,"Electronics Tablet Essential 949 10-inch tablet for streaming, reading and video calls. Essential line, red.",211.0
9,1,Electronics,Monitor Premium 997,monitor-premium-997,"27-inch IPS monitor, full HD, slim bezel, for office and gaming. Premium line, black.",/images/products/monitor-premium-997.jpg,142.99,"Electronics Monitor Premium 997 27-inch IPS monitor, full HD, slim bezel, for office and gaming. Premium line, black.",1028.0
10,1,Electronics,Monitor Classic 784,monitor-classic-784,"27-inch IPS monitor, full HD, slim bezel, for office and gaming. Classic line, white.",/images/products/monitor-classic-784.jpg,200.99,"Electronics Monitor Classic 784 27-inch IPS monitor, full HD, slim bezel, for office and gaming. Classic line, white.",422.0
11,1,Electronics,Keyboard Everyday 369,keyboard-everyday-369,"Mechanical keyboard with backlight, quiet switches. Everyday line, red.",/images/products/keyboard-everyday-369.jpg,21.99,"Electronics Keyboard Everyday 369 Mechanical keyboard with backlight, quiet switches. Everyday line, red.",172.0
12,1,Electronics,Keyboard Classic 505,keyboard-classic-505,"Mechanical keyboard with backlight, quiet switches. Classic line, red.",/images/products/keyboard-classic-505.jpg,24.99,"Electronics Keyboard Classic 505 Mechanical keyboard with backlight, quiet switches. Classic line, red.",1812.0
13,1,Electronics,Mouse Deluxe 406,mouse-deluxe-406,"Ergonomic wireless mouse with silent clicks. Deluxe line, red.",/images/products/mouse-deluxe-406.jpg,17.99,"Electronics Mouse Deluxe 406 Ergonomic wireless mouse with silent clicks. Deluxe line, red.",464.0
14,1,Electronics,Mouse Eco 475,mouse-eco-475,"Ergonomic wireless mouse with silent clicks. Eco line, blue.",/images/products/mouse-eco-475.jpg,11.99,"Electronics Mouse Eco 475 Ergonomic wireless mouse with silent clicks. Eco line, blue.",321.0
15,1,Electronics,Speaker Pro 628,speaker-pro-628,"Portable bluetooth speaker, waterproof, deep bass. Pro line, black.",/images/products/speaker-pro-628.jpg,101.99,"Electronics Speaker Pro 628 Portable bluetooth speaker, waterproof, deep bass. Pro line, black.",346.0
16,1,Electronics,Speaker Eco 174,speaker-eco-174,"Portable bluetooth speaker, waterproof, deep bass. Eco line, red.",/images/products/speaker-eco-174.jpg,180.99,"Electronics Speaker Eco 174 Portable bluetooth speaker, waterproof, deep bass. Eco line, red.",235.0
17,1,Electronics,Camera Compact 359,camera-compact-359,"Mirrorless camera with 4K video and interchangeable lens. Compact line, black.",/images/products/camera-compact-359.jpg,478.99,"Electronics Camera Compact 359 Mirrorless camera with 4K video and interchangeable lens. Compact line, black.",554.0
18,1,Electronics,Camera Everyday 481,camera-everyday-481,"Mirrorless camera with 4K video and interchangeable lens. Everyday line, red.",/images/products/camera-everyday-481.jpg,373.99,"Electronics Camera Everyday 481 Mirrorless camera with 4K video and interchangeable lens. Everyday line, red.",158.0
19,1,Electronics,Smartwatch Premium 103,smartwatch-premium-103,"Fitness smartwatch with heart rate, GPS and sleep tracking. Premium line, beige.",/images/products/smartwatch-premium-103.jpg,140.99,"Electronics Smartwatch Premium 103 Fitness smartwatch with heart rate, GPS and sleep tracking. Premium line, beige.",273.0
20,1,Electronics,Smartwatch Everyday 615,smartwatch-everyday-615,"Fitness smartwatch with heart rate, GPS and sleep tracking. Everyday line, beige.",/images/products/smartwatch-everyday-615.jpg,253.99,"Electronics Smartwatch Everyday 615 Fitness smartwatch with heart rate, GPS and sleep tracking. Everyday line, beige.",267.0
21,1,Electronics,Keyboard Compact 874,keyboard-compact-874,"Mechanical keyboard with backlight, quiet switches. Compact line, grey.",/images/products/keyboard-compact-874.jpg,28.99,"Electronics Keyboard Compact 874 Mechanical keyboard with backlight, quiet switches. Compact line, grey.",317.0
22,2,Fashion,Jacket Compact 350,jacket-compact-350,"Warm winter jacket, water-repellent, hooded. Compact line, silver.",/images/products/jacket-compact-350.jpg,123.99,"Fashion Jacket Compact 350 Warm winter jacket, water-repellent, hooded. Compact line, silver.",314.0
23,2,Fashion,Jacket Essential 819,jacket-essential-819,"Warm winter jacket, water-repellent, hooded. Essential line, silver.",/images/products/jacket-essential-819.jpg,109.99,"Fashion Jacket Essential 819 Warm winter jacket, water-repellent, hooded. Essential line, silver.",469.0
24,2,Fashion,Jeans Premium 253,jeans-premium-253,"Slim fit denim jeans, stretch cotton. Premium line, silver.",/images/products/jeans-premium-253.jpg,106.99,"Fashion Jeans Premium 253 Slim fit denim jeans, stretch cotton. Premium line, silver.",222.0
25,2,Fashion,Jeans Essential 168,jeans-essential-168,"Slim fit denim jeans, stretch cotton. Essential line, grey.",/images/products/jeans-essential-168.jpg,73.99,"Fashion Jeans Essential 168 Slim fit denim jeans, stretch cotton. Essential line, grey.",287.0
26,2,Fashion,Sneakers Deluxe 539,sneakers-deluxe-539,"Everyday sneakers, breathable mesh, cushioned sole. Deluxe line, silver.",/images/products/sneakers-deluxe-539.jpg,100.99,"Fashion Sneakers Deluxe 539 Everyday sneakers, breathable mesh, cushioned sole. Deluxe line, silver.",283.0
27,2,Fashion,Sneakers Compact 248,sneakers-compact-248,"Everyday sneakers, breathable mesh, cushioned sole. Compact line, green.",/images/products/sneakers-compact-248.jpg,81.99,"Fashion Sneakers Compact 248 Everyday sneakers, breathable mesh, cushioned sole. Compact line, green.",431.0
28,2,Fashion,Dress Essential 892,dress-essential-892,"Midi dress for office and evening, soft fabric. Essential line, white.",/images/products/dress-essential-892.jpg,109.99,"Fashion Dress Essential 892 Midi dress for office and evening, soft fabric. Essential line, white.",196.0
29,2,Fashion,Dress Pro 538,dress-pro-538,"Midi dress for office and evening, soft fabric. Pro line, beige.",/images/products/dress-pro-538.jpg,87.99,"Fashion Dress Pro 538 Midi dress for office and evening, soft fabric. Pro line, beige.",297.0
30,2,Fashion,T-shirt Everyday 987,t-shirt-everyday-987,"Basic cotton t-shirt, regular fit. Everyday line, red.",/images/products/t-shirt-everyday-987.jpg,34.99,"Fashion T-shirt Everyday 987 Basic cotton t-shirt, regular fit. Everyday line, red.",1440.0
31,2,Fashion,T-shirt Classic 854,t-shirt-classic-854,"Basic cotton t-shirt, regular fit. Classic line, grey.",/images/products/t-shirt-classic-854.jpg,14.99,"Fashion T-shirt Classic 854 Basic cotton t-shirt, regular fit. Classic line, grey.",648.0
32,2,Fashion,Scarf Eco 733,scarf-eco-733,"Knitted wool scarf for winter. Eco line, silver.",/images/products/scarf-eco-733.jpg,32.99,"Fashion Scarf Eco 733 Knitted wool scarf for winter. Eco line, silver.",399.0
33,2,Fashion,Scarf Eco 599,scarf-eco-599,"Knitted wool scarf for winter. Eco line, green.",/images/products/scarf-eco-599.jpg,37.99,"Fashion Scarf Eco 599 Knitted wool scarf for winter. Eco line, green.",284.0
34,2,Fashion,Belt Eco 953,belt-eco-953,"Genuine leather belt with metal buckle. Eco line, grey.",/images/products/belt-eco-953.jpg,65.99,"Fashion Belt Eco 953 Genuine leather belt with metal buckle. Eco line, grey.",348.0
35,2,Fashion,Belt Eco 785,belt-eco-785,"Genuine leather belt with metal buckle. Eco line, red.",/images/products/belt-eco-785.jpg,17.99,"Fashion Belt Eco 785 Genuine leather belt with metal buckle. Eco line, red.",238.0
36,2,Fashion,Backpack Classic 759,backpack-classic-759,"City backpack with laptop sleeve, water-resistant. Classic line, silver.",/images/products/backpack-classic-759.jpg,117.99,"Fashion Backpack Classic 759 City backpack with laptop sleeve, water-resistant. Classic line, silver.",501.0
37,2,Fashion,Backpack Compact 926,backpack-compact-926,"City backpack with laptop sleeve, water-resistant. Compact line, grey.",/images/products/backpack-compact-926.jpg,39.99,"Fashion Backpack Compact 926 City backpack with laptop sleeve, water-resistant. Compact line, grey.",1206.0
38,2,Fashion,Cap Compact 731,cap-compact-731,"Cotton baseball cap, adjustable. Compact line, white.",/images/products/cap-compact-731.jpg,31.99,"Fashion Cap Compact 731 Cotton baseball cap, adjustable. Compact line, white.",392.0
39,2,Fashion,Cap Everyday 356,cap-everyday-356,"Cotton baseball cap, adjustable. Everyday line, red.",/images/products/cap-everyday-356.jpg,25.99,"Fashion Cap Everyday 356 Cotton baseball cap, adjustable. Everyday line, red.",438.0
40,2,Fashion,Boots Compact 582,boots-compact-582,"Leather winter boots, non-slip sole. Compact line, black.",/images/products/boots-compact-582.jpg,130.99,"Fashion Boots Compact 582 Leather winter boots, non-slip sole. Compact line, black.",386.0
41,2,Fashion,Boots Compact 911,boots-compact-911,"Leather winter boots, non-slip sole. Compact line, black.",/images/products/boots-compact-911.jpg,158.99,"Fashion Boots Compact 911 Leather winter boots, non-slip sole. Compact line, black.",1346.0
42,2,Fashion,Jacket Pro 710,jacket-pro-710,"Warm winter jacket, water-repellent, hooded. Pro line, blue.",/images/products/jacket-pro-710.jpg,216.99,"Fashion Jacket Pro 710 Warm winter jacket, water-repellent, hooded. Pro line, blue.",129.0
43,3,Books,Novel Premium 556,novel-premium-556,"Bestselling contemporary novel, paperback. Premium line, red.",/images/products/novel-premium-556.jpg,23.99,"Books Novel Premium 556 Bestselling contemporary novel, paperback. Premium line, red.",416.0
44,3,Books,Novel Premium 964,novel-premium-964,"Bestselling contemporary novel, paperback. Premium line, green.",/images/products/novel-premium-964.jpg,13.99,"Books Novel Premium 964 Bestselling contemporary novel, paperback. Premium line, green.",616.0
45,3,Books,Thriller Compact 230,thriller-compact-230,"Crime thriller, gripping page-turner. Compact line, black.",/images/products/thriller-compact-230.jpg,11.99,"Books Thriller Compact 230 Crime thriller, gripping page-turner. Compact line, black.",207.0
46,3,Books,Thriller Premium 108,thriller-premium-108,"Crime thriller, gripping page-turner. Premium line, beige.",/images/products/thriller-premium-108.jpg,10.99,"Books Thriller Premium 108 Crime thriller, gripping page-turner. Premium line, beige.",253.0
47,3,Books,Cookbook Premium 243,cookbook-premium-243,"Cookbook with healthy everyday recipes. Premium line, blue.",/images/products/cookbook-premium-243.jpg,30.99,"Books Cookbook Premium 243 Cookbook with healthy everyday recipes. Premium line, blue.",157.0
48,3,Books,Cookbook Essential 136,cookbook-essential-136,"Cookbook with healthy everyday recipes. Essential line, white.",/images/products/cookbook-essential-136.jpg,43.99,"Books Cookbook Essential 136 Cookbook with healthy everyday recipes. Essential line, white.",157.0
49,3,Books,Biography Deluxe 648,biography-deluxe-648,"Biography of a famous entrepreneur. Deluxe line, silver.",/images/products/biography-deluxe-648.jpg,15.99,"Books Biography Deluxe 648 Biography of a famous entrepreneur. Deluxe line, silver.",1774.0
50,3,Books,Biography Essential 819,biography-essential-819,"Biography of a famous entrepreneur. Essential line, white.",/images/products/biography-essential-819.jpg,23.99,"Books Biography Essential 819 Biography of a famous entrepreneur. Essential line, white.",461.0
51,3,Books,Fantasy Premium 823,fantasy-premium-823,"Epic fantasy saga, first book in the series. Premium line, white.",/images/products/fantasy-premium-823.jpg,11.99,"Books Fantasy Premium 823 Epic fantasy saga, first book in the series. Premium line, white.",203.0
52,3,Books,Fantasy Pro 681,fantasy-pro-681,"Epic fantasy saga, first book in the series. Pro line, blue.",/images/products/fantasy-pro-681.jpg,17.99,"Books Fantasy Pro 681 Epic fantasy saga, first book in the series. Pro line, blue.",1207.0
53,3,Books,Textbook Deluxe 723,textbook-deluxe-723,"University textbook on marketing and statistics. Deluxe line, beige.",/images/products/textbook-deluxe-723.jpg,56.99,"Books Textbook Deluxe 723 University textbook on marketing and statistics. Deluxe line, beige.",185.0
54,3,Books,Textbook Eco 847,textbook-eco-847,"University textbook on marketing and statistics. Eco line, silver.",/images/products/textbook-eco-847.jpg,87.99,"Books Textbook Eco 847 University textbook on marketing and statistics. Eco line, silver.",147.0
55,3,Books,Guide Everyday 453,guide-everyday-453,"Travel guide with maps and itineraries. Everyday line, white.",/images/products/guide-everyday-453.jpg,26.99,"Books Guide Everyday 453 Travel guide with maps and itineraries. Everyday line, white.",322.0
56,3,Books,Guide Eco 397,guide-eco-397,"Travel guide with maps and itineraries. Eco line, beige.",/images/products/guide-eco-397.jpg,14.99,"Books Guide Eco 397 Travel guide with maps and itineraries. Eco line, beige.",265.0
57,3,Books,Children's Book Premium 257,childrens-book-premium-257,"Illustrated picture book for children. Premium line, blue.",/images/products/childrens-book-premium-257.jpg,9.49,"Books Children's Book Premium 257 Illustrated picture book for children. Premium line, blue.",180.0
58,3,Books,Children's Book Deluxe 173,childrens-book-deluxe-173,"Illustrated picture book for children. Deluxe line, silver.",/images/products/childrens-book-deluxe-173.jpg,8.49,"Books Children's Book Deluxe 173 Illustrated picture book for children. Deluxe line, silver.",185.0
59,3,Books,Poetry Classic 204,poetry-classic-204,"Collection of modern poetry. Classic line, white.",/images/products/poetry-classic-204.jpg,8.49,"Books Poetry Classic 204 Collection of modern poetry. Classic line, white.",283.0
60,3,Books,Poetry Everyday 604,poetry-everyday-604,"Collection of modern poetry. Everyday line, beige.",/images/products/poetry-everyday-604.jpg,14.99,"Books Poetry Everyday 604 Collection of modern poetry. Everyday line, beige.",857.0
61,3,Books,Dictionary Essential 458,dictionary-essential-458,"English-Serbian dictionary, updated edition. Essential line, beige.",/images/products/dictionary-essential-458.jpg,24.99,"Books Dictionary Essential 458 English-Serbian dictionary, updated edition. Essential line, beige.",297.0
62,3,Books,Dictionary Compact 106,dictionary-compact-106,"English-Serbian dictionary, updated edition. Compact line, blue.",/images/products/dictionary-compact-106.jpg,17.99,"Books Dictionary Compact 106 English-Serbian dictionary, updated edition. Compact line, blue.",227.0
63,3,Books,Cookbook Compact 232,cookbook-compact-232,"Cookbook with healthy everyday recipes. Compact line, white.",/images/products/cookbook-compact-232.jpg,20.99,"Books Cookbook Compact 232 Cookbook with healthy everyday recipes. Compact line, white.",675.0
64,4,Sports,Running Shoes Pro 936,running-shoes-pro-936,"Running shoes with responsive cushioning. Pro line, blue.",/images/products/running-shoes-pro-936.jpg,104.99,"Sports Running Shoes Pro 936 Running shoes with responsive cushioning. Pro line, blue.",208.0
65,4,Sports,Running Shoes Deluxe 803,running-shoes-deluxe-803,"Running shoes with responsive cushioning. Deluxe line, beige.",/images/products/running-shoes-deluxe-803.jpg,96.99,"Sports Running Shoes Deluxe 803 Running shoes with responsive cushioning. Deluxe line, beige.",499.0
66,4,Sports,Yoga Mat Premium 817,yoga-mat-premium-817,"Non-slip yoga mat, eco-friendly material. Premium line, green.",/images/products/yoga-mat-premium-817.jpg,54.99,"Sports Yoga Mat Premium 817 Non-slip yoga mat, eco-friendly material. Premium line, green.",418.0
67,4,Sports,Yoga Mat Everyday 759,yoga-mat-everyday-759,"Non-slip yoga mat, eco-friendly material. Everyday line, grey.",/images/products/yoga-mat-everyday-759.jpg,45.99,"Sports Yoga Mat Everyday 759 Non-slip yoga mat, eco-friendly material. Everyday line, grey.",374.0
68,4,Sports,Dumbbell Set Premium 193,dumbbell-set-premium-193,"Adjustable dumbbell set for home workouts. Premium line, silver.",/images/products/dumbbell-set-premium-193.jpg,116.99,"Sports Dumbbell Set Premium 193 Adjustable dumbbell set for home workouts. Premium line, silver.",546.0
69,4,Sports,Dumbbell Set Pro 352,dumbbell-set-pro-352,"Adjustable dumbbell set for home workouts. Pro line, blue.",/images/products/dumbbell-set-pro-352.jpg,90.99,"Sports Dumbbell Set Pro 352 Adjustable dumbbell set for home workouts. Pro line, blue.",155.0
70,4,Sports,Bicycle Compact 781,bicycle-compact-781,"City and trekking bicycle, aluminium frame, 21 gears. Compact line, black.",/images/products/bicycle-compact-781.jpg,251.99,"Sports Bicycle Compact 781 City and trekking bicycle, aluminium frame, 21 gears. Compact line, black.",149.0
71,4,Sports,Bicycle Everyday 242,bicycle-everyday-242,"City and trekking bicycle, aluminium frame, 21 gears. Everyday line, green.",/images/products/bicycle-everyday-242.jpg,493.99,"Sports Bicycle Everyday 242 City and trekking bicycle, aluminium frame, 21 gears. Everyday line, green.",104.0
72,4,Sports,Tent Classic 324,tent-classic-324,"Lightweight camping tent for two, waterproof. Classic line, black.",/images/products/tent-classic-324.jpg,129.99,"Sports Tent Classic 324 Lightweight camping tent for two, waterproof. Classic line, black.",185.0
73,4,Sports,Tent Classic 332,tent-classic-332,"Lightweight camping tent for two, waterproof. Classic line, beige.",/images/products/tent-classic-332.jpg,76.99,"Sports Tent Classic 332 Lightweight camping tent for two, waterproof. Classic line, beige.",378.0
74,4,Sports,Football Deluxe 883,football-deluxe-883,"Official size football, durable. Deluxe line, black.",/images/products/football-deluxe-883.jpg,36.99,"Sports Football Deluxe 883 Official size football, durable. Deluxe line, black.",864.0
75,4,Sports,Football Premium 903,football-premium-903,"Official size football, durable. Premium line, black.",/images/products/football-premium-903.jpg,41.99,"Sports Football Premium 903 Official size football, durable. Premium line, black.",475.0
76,4,Sports,Tennis Racket Compact 416,tennis-racket-compact-416,"Graphite tennis racket for intermediate players. Compact line, grey.",/images/products/tennis-racket-compact-416.jpg,46.99,"Sports Tennis Racket Compact 416 Graphite tennis racket for intermediate players. Compact line, grey.",1735.0
77,4,Sports,Tennis Racket Classic 374,tennis-racket-classic-374,"Graphite tennis racket for intermediate players. Classic line, grey.",/images/products/tennis-racket-classic-374.jpg,47.99,"Sports Tennis Racket Classic 374 Graphite tennis racket for intermediate players. Classic line, grey.",314.0
78,4,Sports,Sports Bottle Pro 464,sports-bottle-pro-464,"Insulated sports water bottle, leak-proof. Pro line, grey.",/images/products/sports-bottle-pro-464.jpg,9.49,"Sports Sports Bottle Pro 464 Insulated sports water bottle, leak-proof. Pro line, grey.",235.0
79,4,Sports,Sports Bottle Premium 411,sports-bottle-premium-411,"Insulated sports water bottle, leak-proof. Premium line, silver.",/images/products/sports-bottle-premium-411.jpg,6.49,"Sports Sports Bottle Premium 411 Insulated sports water bottle, leak-proof. Premium line, silver.",221.0
80,4,Sports,Fitness Band Eco 108,fitness-band-eco-108,"Resistance bands set for strength training. Eco line, blue.",/images/products/fitness-band-eco-108.jpg,37.99,"Sports Fitness Band Eco 108 Resistance bands set for strength training. Eco line, blue.",1127.0
81,4,Sports,Fitness Band Deluxe 954,fitness-band-deluxe-954,"Resistance bands set for strength training. Deluxe line, red.",/images/products/fitness-band-deluxe-954.jpg,29.99,"Sports Fitness Band Deluxe 954 Resistance bands set for strength training. Deluxe line, red.",180.0
82,4,Sports,Ski Gloves Eco 904,ski-gloves-eco-904,"Insulated ski gloves, waterproof. Eco line, beige.",/images/products/ski-gloves-eco-904.jpg,25.99,"Sports Ski Gloves Eco 904 Insulated ski gloves, waterproof. Eco line, beige.",217.0
83,4,Sports,Ski Gloves Premium 117,ski-gloves-premium-117,"Insulated ski gloves, waterproof. Premium line, black.",/images/products/ski-gloves-premium-117.jpg,40.99,"Sports Ski Gloves Premium 117 Insulated ski gloves, waterproof. Premium line, black.",178.0
84,4,Sports,Bicycle Eco 162,bicycle-eco-162,"City and trekking bicycle, aluminium frame, 21 gears. Eco line, grey.",/images/products/bicycle-eco-162.jpg,552.99,"Sports Bicycle Eco 162 City and trekking bicycle, aluminium frame, 21 gears. Eco line, grey.",110.0
85,5,Home,Blender Classic 334,blender-classic-334,"Kitchen blender for smoothies and soups. Classic line, beige.",/images/products/blender-classic-334.jpg,61.99,"Home Blender Classic 334 Kitchen blender for smoothies and soups. Classic line, beige.",1579.0
86,5,Home,Blender Everyday 283,blender-everyday-283,"Kitchen blender for smoothies and soups. Everyday line, red.",/images/products/blender-everyday-283.jpg,84.99,"Home Blender Everyday 283 Kitchen blender for smoothies and soups. Everyday line, red.",524.0
87,5,Home,Coffee Maker Pro 639,coffee-maker-pro-639,"Espresso coffee maker with milk frother. Pro line, green.",/images/products/coffee-maker-pro-639.jpg,103.99,"Home Coffee Maker Pro 639 Espresso coffee maker with milk frother. Pro line, green.",581.0
88,5,Home,Coffee Maker Compact 260,coffee-maker-compact-260,"Espresso coffee maker with milk frother. Compact line, silver.",/images/products/coffee-maker-compact-260.jpg,176.99,"Home Coffee Maker Compact 260 Espresso coffee maker with milk frother. Compact line, silver.",458.0
89,5,Home,Table Lamp Deluxe 218,table-lamp-deluxe-218,"LED table lamp with dimmer, warm light. Deluxe line, white.",/images/products/table-lamp-deluxe-218.jpg,32.99,"Home Table Lamp Deluxe 218 LED table lamp with dimmer, warm light. Deluxe line, white.",394.0
90,5,Home,Table Lamp Eco 643,table-lamp-eco-643,"LED table lamp with dimmer, warm light. Eco line, silver.",/images/products/table-lamp-eco-643.jpg,23.99,"Home Table Lamp Eco 643 LED table lamp with dimmer, warm light. Eco line, silver.",2115.0
91,5,Home,Bedding Set Everyday 737,bedding-set-everyday-737,"Cotton bedding set, soft and breathable. Everyday line, silver.",/images/products/bedding-set-everyday-737.jpg,45.99,"Home Bedding Set Everyday 737 Cotton bedding set, soft and breathable. Everyday line, silver.",259.0
92,5,Home,Bedding Set Everyday 735,bedding-set-everyday-735,"Cotton bedding set, soft and breathable. Everyday line, white.",/images/products/bedding-set-everyday-735.jpg,48.99,"Home Bedding Set Everyday 735 Cotton bedding set, soft and breathable. Everyday line, white.",266.0
93,5,Home,Towel Set Eco 365,towel-set-eco-365,"Absorbent bath towel set. Eco line, blue.",/images/products/towel-set-eco-365.jpg,23.99,"Home Towel Set Eco 365 Absorbent bath towel set. Eco line, blue.",1007.0
94,5,Home,Towel Set Pro 801,towel-set-pro-801,"Absorbent bath towel set. Pro line, red.",/images/products/towel-set-pro-801.jpg,50.99,"Home Towel Set Pro 801 Absorbent bath towel set. Pro line, red.",443.0
95,5,Home,Cookware Set Premium 431,cookware-set-premium-431,"Non-stick cookware set, induction compatible. Premium line, grey.",/images/products/cookware-set-premium-431.jpg,88.99,"Home Cookware Set Premium 431 Non-stick cookware set, induction compatible. Premium line, grey.",432.0
96,5,Home,Cookware Set Premium 319,cookware-set-premium-319,"Non-stick cookware set, induction compatible. Premium line, green.",/images/products/cookware-set-premium-319.jpg,243.99,"Home Cookware Set Premium 319 Non-stick cookware set, induction compatible. Premium line, green.",333.0
97,5,Home,Rug Pro 262,rug-pro-262,"Soft living room rug, easy to clean. Pro line, black.",/images/products/rug-pro-262.jpg,32.99,"Home Rug Pro 262 Soft living room rug, easy to clean. Pro line, black.",322.0
98,5,Home,Rug Everyday 138,rug-everyday-138,"Soft living room rug, easy to clean. Everyday line, blue.",/images/products/rug-everyday-138.jpg,151.99,"Home Rug Everyday 138 Soft living room rug, easy to clean. Everyday line, blue.",199.0
99,5,Home,Vacuum Cleaner Eco 407,vacuum-cleaner-eco-407,"Bagless vacuum cleaner with HEPA filter. Eco line, blue.",/images/products/vacuum-cleaner-eco-407.jpg,372.99,"Home Vacuum Cleaner Eco 407 Bagless vacuum cleaner with HEPA filter. Eco line, blue.",178.0
100,5,Home,Vacuum Cleaner Classic 924,vacuum-cleaner-classic-924,"Bagless vacuum cleaner with HEPA filter. Classic line, black.",/images/products/vacuum-cleaner-classic-924.jpg,122.99,"Home Vacuum Cleaner Classic 924 Bagless vacuum cleaner with HEPA filter. Classic line, black.",288.0
101,5,Home,Kettle Deluxe 984,kettle-deluxe-984,"Electric kettle, 1.7 litre, auto shut-off. Deluxe line, beige.",/images/products/kettle-deluxe-984.jpg,67.99,"Home Kettle Deluxe 984 Electric kettle, 1.7 litre, auto shut-off. Deluxe line, beige.",324.0
102,5,Home,Kettle Pro 822,kettle-pro-822,"Electric kettle, 1.7 litre, auto shut-off. Pro line, blue.",/images/products/kettle-pro-822.jpg,35.99,"Home Kettle Pro 822 Electric kettle, 1.7 litre, auto shut-off. Pro line, blue.",267.0
103,5,Home,Candle Everyday 732,candle-everyday-732,"Scented candle, vanilla and amber. Everyday line, green.",/images/products/candle-everyday-732.jpg,13.99,"Home Candle Everyday 732 Scented candle, vanilla and amber. Everyday line, green.",781.0
104,5,Home,Candle Deluxe 106,candle-deluxe-106,"Scented candle, vanilla and amber. Deluxe line, silver.",/images/products/candle-deluxe-106.jpg,9.49,"Home Candle Deluxe 106 Scented candle, vanilla and amber. Deluxe line, silver.",252.0
105,5,Home,Bedding Set Everyday 147,bedding-set-everyday-147,"Cotton bedding set, soft and breathable. Everyday line, green.",/images/products/bedding-set-everyday-147.jpg,59.99,"Home Bedding Set Everyday 147 Cotton bedding set, soft and breathable. Everyday line, green.",845.0
106,6,Beauty,Face Cream Deluxe 613,face-cream-deluxe-613,"Hydrating face cream for daily use. Deluxe line, white.",/images/products/face-cream-deluxe-613.jpg,65.99,"Beauty Face Cream Deluxe 613 Hydrating face cream for daily use. Deluxe line, white.",184.0
107,6,Beauty,Face Cream Everyday 865,face-cream-everyday-865,"Hydrating face cream for daily use. Everyday line, white.",/images/products/face-cream-everyday-865.jpg,31.99,"Beauty Face Cream Everyday 865 Hydrating face cream for daily use. Everyday line, white.",458.0
108,6,Beauty,Serum Essential 226,serum-essential-226,"Vitamin C serum for radiant skin. Essential line, blue.",/images/products/serum-essential-226.jpg,48.99,"Beauty Serum Essential 226 Vitamin C serum for radiant skin. Essential line, blue.",516.0
109,6,Beauty,Serum Everyday 923,serum-everyday-923,"Vitamin C serum for radiant skin. Everyday line, black.",/images/products/serum-everyday-923.jpg,31.99,"Beauty Serum Everyday 923 Vitamin C serum for radiant skin. Everyday line, black.",376.0
110,6,Beauty,Shampoo Everyday 111,shampoo-everyday-111,"Nourishing shampoo for dry hair. Everyday line, red.",/images/products/shampoo-everyday-111.jpg,9.49,"Beauty Shampoo Everyday 111 Nourishing shampoo for dry hair. Everyday line, red.",1852.0
111,6,Beauty,Shampoo Classic 190,shampoo-classic-190,"Nourishing shampoo for dry hair. Classic line, grey.",/images/products/shampoo-classic-190.jpg,8.49,"Beauty Shampoo Classic 190 Nourishing shampoo for dry hair. Classic line, grey.",247.0
112,6,Beauty,Perfume Classic 324,perfume-classic-324,"Eau de parfum, floral and woody notes. Classic line, black.",/images/products/perfume-classic-324.jpg,65.99,"Beauty Perfume Classic 324 Eau de parfum, floral and woody notes. Classic line, black.",221.0
113,6,Beauty,Perfume Pro 986,perfume-pro-986,"Eau de parfum, floral and woody notes. Pro line, red.",/images/products/perfume-pro-986.jpg,72.99,"Beauty Perfume Pro 986 Eau de parfum, floral and woody notes. Pro line, red.",208.0
114,6,Beauty,Lipstick Compact 868,lipstick-compact-868,"Long-lasting matte lipstick. Compact line, grey.",/images/products/lipstick-compact-868.jpg,8.49,"Beauty Lipstick Compact 868 Long-lasting matte lipstick. Compact line, grey.",388.0
115,6,Beauty,Lipstick Eco 829,lipstick-eco-829,"Long-lasting matte lipstick. Eco line, beige.",/images/products/lipstick-eco-829.jpg,9.49,"Beauty Lipstick Eco 829 Long-lasting matte lipstick. Eco line, beige.",379.0
116,6,Beauty,Hair Dryer Deluxe 707,hair-dryer-deluxe-707,"Ionic hair dryer, fast drying. Deluxe line, silver.",/images/products/hair-dryer-deluxe-707.jpg,85.99,"Beauty Hair Dryer Deluxe 707 Ionic hair dryer, fast drying. Deluxe line, silver.",156.0
117,6,Beauty,Hair Dryer Everyday 502,hair-dryer-everyday-502,"Ionic hair dryer, fast drying. Everyday line, blue.",/images/products/hair-dryer-everyday-502.jpg,80.99,"Beauty Hair Dryer Everyday 502 Ionic hair dryer, fast drying. Everyday line, blue.",229.0
118,6,Beauty,Body Lotion Deluxe 734,body-lotion-deluxe-734,"Body lotion with shea butter. Deluxe line, beige.",/images/products/body-lotion-deluxe-734.jpg,6.49,"Beauty Body Lotion Deluxe 734 Body lotion with shea butter. Deluxe line, beige.",728.0
119,6,Beauty,Body Lotion Everyday 438,body-lotion-everyday-438,"Body lotion with shea butter. Everyday line, blue.",/images/products/body-lotion-everyday-438.jpg,5.49,"Beauty Body Lotion Everyday 438 Body lotion with shea butter. Everyday line, blue.",148.0
120,6,Beauty,Sunscreen Eco 737,sunscreen-eco-737,"Sunscreen SPF 50, water-resistant. Eco line, green.",/images/products/sunscreen-eco-737.jpg,11.99,"Beauty Sunscreen Eco 737 Sunscreen SPF 50, water-resistant. Eco line, green.",256.0
121,6,Beauty,Sunscreen Classic 799,sunscreen-classic-799,"Sunscreen SPF 50, water-resistant. Classic line, silver.",/images/products/sunscreen-classic-799.jpg,22.99,"Beauty Sunscreen Classic 799 Sunscreen SPF 50, water-resistant. Classic line, silver.",640.0
122,6,Beauty,Makeup Brush Set Eco 513,makeup-brush-set-eco-513,"Makeup brush set, soft synthetic bristles. Eco line, black.",/images/products/makeup-brush-set-eco-513.jpg,37.99,"Beauty Makeup Brush Set Eco 513 Makeup brush set, soft synthetic bristles. Eco line, black.",220.0
123,6,Beauty,Makeup Brush Set Pro 675,makeup-brush-set-pro-675,"Makeup brush set, soft synthetic bristles. Pro line, beige.",/images/products/makeup-brush-set-pro-675.jpg,24.99,"Beauty Makeup Brush Set Pro 675 Makeup brush set, soft synthetic bristles. Pro line, beige.",705.0
124,6,Beauty,Beard Trimmer Pro 366,beard-trimmer-pro-366,"Rechargeable beard trimmer with combs. Pro line, black.",/images/products/beard-trimmer-pro-366.jpg,51.99,"Beauty Beard Trimmer Pro 366 Rechargeable beard trimmer with combs. Pro line, black.",207.0
125,6,Beauty,Beard Trimmer Premium 354,beard-trimmer-premium-354,"Rechargeable beard trimmer with combs. Premium line, grey.",/images/products/beard-trimmer-premium-354.jpg,71.99,"Beauty Beard Trimmer Premium 354 Rechargeable beard trimmer with combs. Premium line, grey.",927.0
126,6,Beauty,Body Lotion Classic 808,body-lotion-classic-808,"Body lotion with shea butter. Classic line, green.",/images/products/body-lotion-classic-808.jpg,7.49,"Beauty Body Lotion Classic 808 Body lotion with shea butter. Classic line, green.",164.0
127,7,Toys,Building Blocks Premium 126,building-blocks-premium-126,"Building blocks set, creative construction toy. Premium line, grey.",/images/products/building-blocks-premium-126.jpg,37.99,"Toys Building Blocks Premium 126 Building blocks set, creative construction toy. Premium line, grey.",1584.0
128,7,Toys,Building Blocks Deluxe 813,building-blocks-deluxe-813,"Building blocks set, creative construction toy. Deluxe line, beige.",/images/products/building-blocks-deluxe-813.jpg,51.99,"Toys Building Blocks Deluxe 813 Building blocks set, creative construction toy. Deluxe line, beige.",177.0
129,7,Toys,Board Game Deluxe 308,board-game-deluxe-308,"Family board game for 2-6 players. Deluxe line, green.",/images/products/board-game-deluxe-308.jpg,16.99,"Toys Board Game Deluxe 308 Family board game for 2-6 players. Deluxe line, green.",287.0
130,7,Toys,Board Game Essential 786,board-game-essential-786,"Family board game for 2-6 players. Essential line, grey.",/images/products/board-game-essential-786.jpg,57.99,"Toys Board Game Essential 786 Family board game for 2-6 players. Essential line, grey.",115.0
131,7,Toys,Puzzle Essential 352,puzzle-essential-352,"1000-piece jigsaw puzzle. Essential line, grey.",/images/products/puzzle-essential-352.jpg,29.99,"Toys Puzzle Essential 352 1000-piece jigsaw puzzle. Essential line, grey.",189.0
132,7,Toys,Puzzle Everyday 336,puzzle-everyday-336,"1000-piece jigsaw puzzle. Everyday line, silver.",/images/products/puzzle-everyday-336.jpg,8.49,"Toys Puzzle Everyday 336 1000-piece jigsaw puzzle. Everyday line, silver.",531.0
133,7,Toys,Doll Eco 977,doll-eco-977,"Fashion doll with accessories. Eco line, beige.",/images/products/doll-eco-977.jpg,23.99,"Toys Doll Eco 977 Fashion doll with accessories. Eco line, beige.",1146.0
134,7,Toys,Doll Classic 843,doll-classic-843,"Fashion doll with accessories. Classic line, silver.",/images/products/doll-classic-843.jpg,47.99,"Toys Doll Classic 843 Fashion doll with accessories. Classic line, silver.",414.0
135,7,Toys,RC Car Deluxe 276,rc-car-deluxe-276,"Remote control car, rechargeable. Deluxe line, black.",/images/products/rc-car-deluxe-276.jpg,55.99,"Toys RC Car Deluxe 276 Remote control car, rechargeable. Deluxe line, black.",180.0
136,7,Toys,RC Car Essential 980,rc-car-essential-980,"Remote control car, rechargeable. Essential line, blue.",/images/products/rc-car-essential-980.jpg,52.99,"Toys RC Car Essential 980 Remote control car, rechargeable. Essential line, blue.",311.0
137,7,Toys,Plush Toy Classic 439,plush-toy-classic-439,"Soft plush teddy bear. Classic line, red.",/images/products/plush-toy-classic-439.jpg,32.99,"Toys Plush Toy Classic 439 Soft plush teddy bear. Classic line, red.",787.0
138,7,Toys,Plush Toy Premium 855,plush-toy-premium-855,"Soft plush teddy bear. Premium line, black.",/images/products/plush-toy-premium-855.jpg,14.99,"Toys Plush Toy Premium 855 Soft plush teddy bear. Premium line, black.",183.0
139,7,Toys,Robot Kit Premium 136,robot-kit-premium-136,"Programmable robot kit, STEM learning. Premium line, grey.",/images/products/robot-kit-premium-136.jpg,47.99,"Toys Robot Kit Premium 136 Programmable robot kit, STEM learning. Premium line, grey.",182.0
140,7,Toys,Robot Kit Essential 218,robot-kit-essential-218,"Programmable robot kit, STEM learning. Essential line, green.",/images/products/robot-kit-essential-218.jpg,63.99,"Toys Robot Kit Essential 218 Programmable robot kit, STEM learning. Essential line, green.",366.0
141,7,Toys,Paint Set Classic 369,paint-set-classic-369,"Kids paint set with brushes. Classic line, red.",/images/products/paint-set-classic-369.jpg,17.99,"Toys Paint Set Classic 369 Kids paint set with brushes. Classic line, red.",389.0
142,7,Toys,Paint Set Deluxe 295,paint-set-deluxe-295,"Kids paint set with brushes. Deluxe line, white.",/images/products/paint-set-deluxe-295.jpg,9.49,"Toys Paint Set Deluxe 295 Kids paint set with brushes. Deluxe line, white.",372.0
143,7,Toys,Toy Train Deluxe 965,toy-train-deluxe-965,"Wooden toy train set. Deluxe line, blue.",/images/products/toy-train-deluxe-965.jpg,43.99,"Toys Toy Train Deluxe 965 Wooden toy train set. Deluxe line, blue.",266.0
144,7,Toys,Toy Train Pro 565,toy-train-pro-565,"Wooden toy train set. Pro line, green.",/images/products/toy-train-pro-565.jpg,93.99,"Toys Toy Train Pro 565 Wooden toy train set. Pro line, green.",147.0
145,7,Toys,Card Game Essential 324,card-game-essential-324,"Fast card game for kids and adults. Essential line, black.",/images/products/card-game-essential-324.jpg,10.99,"Toys Card Game Essential 324 Fast card game for kids and adults. Essential line, black.",223.0
146,7,Toys,Card Game Eco 736,card-game-eco-736,"Fast card game for kids and adults. Eco line, blue.",/images/products/card-game-eco-736.jpg,7.49,"Toys Card Game Eco 736 Fast card game for kids and adults. Eco line, blue.",151.0
147,7,Toys,Paint Set Everyday 573,paint-set-everyday-573,"Kids paint set with brushes. Everyday line, green.",/images/products/paint-set-everyday-573.jpg,17.99,"Toys Paint Set Everyday 573 Kids paint set with brushes. Everyday line, green.",186.0
148,8,Food,Coffee Beans Pro 813,coffee-beans-pro-813,"Arabica coffee beans, medium roast. Pro line, white.",/images/products/coffee-beans-pro-813.jpg,8.49,"Food Coffee Beans Pro 813 Arabica coffee beans, medium roast. Pro line, white.",1529.0
149,8,Food,Coffee Beans Pro 200,coffee-beans-pro-200,"Arabica coffee beans, medium roast. Pro line, silver.",/images/products/coffee-beans-pro-200.jpg,8.49,"Food Coffee Beans Pro 200 Arabica coffee beans, medium roast. Pro line, silver.",138.0
150,8,Food,Green Tea Deluxe 321,green-tea-deluxe-321,"Organic green tea, loose leaf. Deluxe line, blue.",/images/products/green-tea-deluxe-321.jpg,7.49,"Food Green Tea Deluxe 321 Organic green tea, loose leaf. Deluxe line, blue.",453.0
151,8,Food,Green Tea Eco 344,green-tea-eco-344,"Organic green tea, loose leaf. Eco line, white.",/images/products/green-tea-eco-344.jpg,10.99,"Food Green Tea Eco 344 Organic green tea, loose leaf. Eco line, white.",120.0
152,8,Food,Dark Chocolate Premium 512,dark-chocolate-premium-512,"Dark chocolate 70% cocoa. Premium line, green.",/images/products/dark-chocolate-premium-512.jpg,3.49,"Food Dark Chocolate Premium 512 Dark chocolate 70% cocoa. Premium line, green.",488.0
153,8,Food,Dark Chocolate Essential 370,dark-chocolate-essential-370,"Dark chocolate 70% cocoa. Essential line, silver.",/images/products/dark-chocolate-essential-370.jpg,3.49,"Food Dark Chocolate Essential 370 Dark chocolate 70% cocoa. Essential line, silver.",199.0
154,8,Food,Olive Oil Everyday 426,olive-oil-everyday-426,"Extra virgin olive oil, cold pressed. Everyday line, white.",/images/products/olive-oil-everyday-426.jpg,7.49,"Food Olive Oil Everyday 426 Extra virgin olive oil, cold pressed. Everyday line, white.",409.0
155,8,Food,Olive Oil Deluxe 890,olive-oil-deluxe-890,"Extra virgin olive oil, cold pressed. Deluxe line, grey.",/images/products/olive-oil-deluxe-890.jpg,10.99,"Food Olive Oil Deluxe 890 Extra virgin olive oil, cold pressed. Deluxe line, grey.",220.0
156,8,Food,Honey Everyday 491,honey-everyday-491,"Natural forest honey. Everyday line, white.",/images/products/honey-everyday-491.jpg,7.49,"Food Honey Everyday 491 Natural forest honey. Everyday line, white.",388.0
157,8,Food,Honey Compact 112,honey-compact-112,"Natural forest honey. Compact line, grey.",/images/products/honey-compact-112.jpg,8.49,"Food Honey Compact 112 Natural forest honey. Compact line, grey.",186.0
158,8,Food,Pasta Eco 942,pasta-eco-942,"Durum wheat pasta. Eco line, black.",/images/products/pasta-eco-942.jpg,5.49,"Food Pasta Eco 942 Durum wheat pasta. Eco line, black.",674.0
159,8,Food,Pasta Premium 123,pasta-premium-123,"Durum wheat pasta. Premium line, blue.",/images/products/pasta-premium-123.jpg,2.49,"Food Pasta Premium 123 Durum wheat pasta. Premium line, blue.",176.0
160,8,Food,Granola Premium 789,granola-premium-789,"Crunchy granola with nuts and honey. Premium line, blue.",/images/products/granola-premium-789.jpg,5.49,"Food Granola Premium 789 Crunchy granola with nuts and honey. Premium line, blue.",1089.0
161,8,Food,Granola Deluxe 683,granola-deluxe-683,"Crunchy granola with nuts and honey. Deluxe line, red.",/images/products/granola-deluxe-683.jpg,5.49,"Food Granola Deluxe 683 Crunchy granola with nuts and honey. Deluxe line, red.",320.0
162,8,Food,Spice Set Pro 698,spice-set-pro-698,"Gourmet spice set for grilling and cooking. Pro line, white.",/images/products/spice-set-pro-698.jpg,26.99,"Food Spice Set Pro 698 Gourmet spice set for grilling and cooking. Pro line, white.",176.0
163,8,Food,Spice Set Premium 106,spice-set-premium-106,"Gourmet spice set for grilling and cooking. Premium line, green.",/images/products/spice-set-premium-106.jpg,9.49,"Food Spice Set Premium 106 Gourmet spice set for grilling and cooking. Premium line, green.",202.0
164,8,Food,Protein Bar Box Compact 478,protein-bar-box-compact-478,"Protein bars box, 12 pieces. Compact line, red.",/images/products/protein-bar-box-compact-478.jpg,13.99,"Food Protein Bar Box Compact 478 Protein bars box, 12 pieces. Compact line, red.",159.0
165,8,Food,Protein Bar Box Deluxe 678,protein-bar-box-deluxe-678,"Protein bars box, 12 pieces. Deluxe line, white.",/images/products/protein-bar-box-deluxe-678.jpg,27.99,"Food Protein Bar Box Deluxe 678 Protein bars box, 12 pieces. Deluxe line, white.",134.0
166,8,Food,Juice Eco 447,juice-eco-447,"Fresh orange juice, no added sugar. Eco line, red.",/images/products/juice-eco-447.jpg,2.49,"Food Juice Eco 447 Fresh orange juice, no added sugar. Eco line, red.",143.0
167,8,Food,Juice Everyday 509,juice-everyday-509,"Fresh orange juice, no added sugar. Everyday line, white.",/images/products/juice-everyday-509.jpg,3.49,"Food Juice Everyday 509 Fresh orange juice, no added sugar. Everyday line, white.",710.0
168,8,Food,Juice Everyday 512,juice-everyday-512,"Fresh orange juice, no added sugar. Everyday line, white.",/images/products/juice-everyday-512.jpg,4.49,"Food Juice Everyday 512 Fresh orange juice, no added sugar. Everyday line, white.",293.0
169,9,Furniture,Sofa Essential 990,sofa-essential-990,"Three-seat sofa, fabric upholstery. Essential line, beige.",/images/products/sofa-essential-990.jpg,440.99,"Furniture Sofa Essential 990 Three-seat sofa, fabric upholstery. Essential line, beige.",474.0
170,9,Furniture,Sofa Everyday 232,sofa-everyday-232,"Three-seat sofa, fabric upholstery. Everyday line, white.",/images/products/sofa-everyday-232.jpg,591.99,"Furniture Sofa Everyday 232 Three-seat sofa, fabric upholstery. Everyday line, white.",184.0
171,9,Furniture,Office Chair Deluxe 707,office-chair-deluxe-707,"Ergonomic office chair with lumbar support. Deluxe line, silver.",/images/products/office-chair-deluxe-707.jpg,235.99,"Furniture Office Chair Deluxe 707 Ergonomic office chair with lumbar support. Deluxe line, silver.",436.0
172,9,Furniture,Office Chair Classic 995,office-chair-classic-995,"Ergonomic office chair with lumbar support. Classic line, beige.",/images/products/office-chair-classic-995.jpg,165.99,"Furniture Office Chair Classic 995 Ergonomic office chair with lumbar support. Classic line, beige.",290.0
173,9,Furniture,Desk Eco 120,desk-eco-120,"Home office desk, wooden top. Eco line, silver.",/images/products/desk-eco-120.jpg,321.99,"Furniture Desk Eco 120 Home office desk, wooden top. Eco line, silver.",144.0
174,9,Furniture,Desk Compact 268,desk-compact-268,"Home office desk, wooden top. Compact line, white.",/images/products/desk-compact-268.jpg,190.99,"Furniture Desk Compact 268 Home office desk, wooden top. Compact line, white.",225.0
175,9,Furniture,Bookshelf Eco 371,bookshelf-eco-371,"Five-tier bookshelf. Eco line, blue.",/images/products/bookshelf-eco-371.jpg,167.99,"Furniture Bookshelf Eco 371 Five-tier bookshelf. Eco line, blue.",488.0
176,9,Furniture,Bookshelf Compact 435,bookshelf-compact-435,"Five-tier bookshelf. Compact line, grey.",/images/products/bookshelf-compact-435.jpg,60.99,"Furniture Bookshelf Compact 435 Five-tier bookshelf. Compact line, grey.",239.0
177,9,Furniture,Bed Frame Eco 577,bed-frame-eco-577,"Double bed frame with storage. Eco line, grey.",/images/products/bed-frame-eco-577.jpg,241.99,"Furniture Bed Frame Eco 577 Double bed frame with storage. Eco line, grey.",1148.0
178,9,Furniture,Bed Frame Essential 340,bed-frame-essential-340,"Double bed frame with storage. Essential line, white.",/images/products/bed-frame-essential-340.jpg,561.99,"Furniture Bed Frame Essential 340 Double bed frame with storage. Essential line, white.",237.0
179,9,Furniture,Wardrobe Eco 520,wardrobe-eco-520,"Two-door wardrobe with mirror. Eco line, white.",/images/products/wardrobe-eco-520.jpg,763.99,"Furniture Wardrobe Eco 520 Two-door wardrobe with mirror. Eco line, white.",221.0
180,9,Furniture,Wardrobe Classic 848,wardrobe-classic-848,"Two-door wardrobe with mirror. Classic line, red.",/images/products/wardrobe-classic-848.jpg,591.99,"Furniture Wardrobe Classic 848 Two-door wardrobe with mirror. Classic line, red.",103.0
181,9,Furniture,Coffee Table Eco 857,coffee-table-eco-857,"Coffee table, oak finish. Eco line, white.",/images/products/coffee-table-eco-857.jpg,204.99,"Furniture Coffee Table Eco 857 Coffee table, oak finish. Eco line, white.",954.0
182,9,Furniture,Coffee Table Pro 626,coffee-table-pro-626,"Coffee table, oak finish. Pro line, black.",/images/products/coffee-table-pro-626.jpg,56.99,"Furniture Coffee Table Pro 626 Coffee table, oak finish. Pro line, black.",558.0
183,9,Furniture,Nightstand Classic 778,nightstand-classic-778,"Nightstand with drawer. Classic line, grey.",/images/products/nightstand-classic-778.jpg,144.99,"Furniture Nightstand Classic 778 Nightstand with drawer. Classic line, grey.",364.0
184,9,Furniture,Nightstand Everyday 721,nightstand-everyday-721,"Nightstand with drawer. Everyday line, silver.",/images/products/nightstand-everyday-721.jpg,89.99,"Furniture Nightstand Everyday 721 Nightstand with drawer. Everyday line, silver.",1878.0
185,9,Furniture,Dining Chair Classic 954,dining-chair-classic-954,"Upholstered dining chair. Classic line, black.",/images/products/dining-chair-classic-954.jpg,98.99,"Furniture Dining Chair Classic 954 Upholstered dining chair. Classic line, black.",589.0
186,9,Furniture,Dining Chair Essential 421,dining-chair-essential-421,"Upholstered dining chair. Essential line, blue.",/images/products/dining-chair-essential-421.jpg,81.99,"Furniture Dining Chair Essential 421 Upholstered dining chair. Essential line, blue.",245.0
187,9,Furniture,Armchair Eco 684,armchair-eco-684,"Reading armchair, velvet. Eco line, white.",/images/products/armchair-eco-684.jpg,277.99,"Furniture Armchair Eco 684 Reading armchair, velvet. Eco line, white.",318.0
188,9,Furniture,Armchair Classic 733,armchair-classic-733,"Reading armchair, velvet. Classic line, white.",/images/products/armchair-classic-733.jpg,141.99,"Furniture Armchair Classic 733 Reading armchair, velvet. Classic line, white.",230.0
189,9,Furniture,Nightstand Pro 841,nightstand-pro-841,"Nightstand with drawer. Pro line, grey.",/images/products/nightstand-pro-841.jpg,56.99,"Furniture Nightstand Pro 841 Nightstand with drawer. Pro line, grey.",206.0
190,10,Automotive,Winter Tires Essential 210,winter-tires-essential-210,"Winter tire, excellent grip on snow and ice. Essential line, grey.",/images/products/winter-tires-essential-210.jpg,183.99,"Automotive Winter Tires Essential 210 Winter tire, excellent grip on snow and ice. Essential line, grey.",169.0
191,10,Automotive,Winter Tires Deluxe 474,winter-tires-deluxe-474,"Winter tire, excellent grip on snow and ice. Deluxe line, white.",/images/products/winter-tires-deluxe-474.jpg,65.99,"Automotive Winter Tires Deluxe 474 Winter tire, excellent grip on snow and ice. Deluxe line, white.",144.0
192,10,Automotive,Car Battery Premium 115,car-battery-premium-115,"12V car battery, long life. Premium line, blue.",/images/products/car-battery-premium-115.jpg,147.99,"Automotive Car Battery Premium 115 12V car battery, long life. Premium line, blue.",70.0
193,10,Automotive,Car Battery Deluxe 488,car-battery-deluxe-488,"12V car battery, long life. Deluxe line, white.",/images/products/car-battery-deluxe-488.jpg,92.99,"Automotive Car Battery Deluxe 488 12V car battery, long life. Deluxe line, white.",558.0
194,10,Automotive,Dash Cam Compact 583,dash-cam-compact-583,"Full HD dash cam with night vision. Compact line, silver.",/images/products/dash-cam-compact-583.jpg,154.99,"Automotive Dash Cam Compact 583 Full HD dash cam with night vision. Compact line, silver.",105.0
195,10,Automotive,Dash Cam Eco 784,dash-cam-eco-784,"Full HD dash cam with night vision. Eco line, red.",/images/products/dash-cam-eco-784.jpg,108.99,"Automotive Dash Cam Eco 784 Full HD dash cam with night vision. Eco line, red.",147.0
196,10,Automotive,Phone Holder Pro 656,phone-holder-pro-656,"Magnetic car phone holder. Pro line, black.",/images/products/phone-holder-pro-656.jpg,19.99,"Automotive Phone Holder Pro 656 Magnetic car phone holder. Pro line, black.",313.0
197,10,Automotive,Phone Holder Pro 706,phone-holder-pro-706,"Magnetic car phone holder. Pro line, green.",/images/products/phone-holder-pro-706.jpg,10.99,"Automotive Phone Holder Pro 706 Magnetic car phone holder. Pro line, green.",139.0
198,10,Automotive,Car Charger Everyday 607,car-charger-everyday-607,"Fast USB-C car charger. Everyday line, blue.",/images/products/car-charger-everyday-607.jpg,11.99,"Automotive Car Charger Everyday 607 Fast USB-C car charger. Everyday line, blue.",992.0
199,10,Automotive,Car Charger Everyday 299,car-charger-everyday-299,"Fast USB-C car charger. Everyday line, beige.",/images/products/car-charger-everyday-299.jpg,16.99,"Automotive Car Charger Everyday 299 Fast USB-C car charger. Everyday line, beige.",396.0
200,10,Automotive,Floor Mats Everyday 949,floor-mats-everyday-949,"Rubber car floor mats, all-weather. Everyday line, silver.",/images/products/floor-mats-everyday-949.jpg,30.99,"Automotive Floor Mats Everyday 949 Rubber car floor mats, all-weather. Everyday line, silver.",1572.0
201,10,Automotive,Floor Mats Pro 348,floor-mats-pro-348,"Rubber car floor mats, all-weather. Pro line, beige.",/images/products/floor-mats-pro-348.jpg,28.99,"Automotive Floor Mats Pro 348 Rubber car floor mats, all-weather. Pro line, beige.",212.0
202,10,Automotive,Engine Oil Compact 508,engine-oil-compact-508,"Synthetic engine oil 5W-30. Compact line, beige.",/images/products/engine-oil-compact-508.jpg,27.99,"Automotive Engine Oil Compact 508 Synthetic engine oil 5W-30. Compact line, beige.",214.0
203,10,Automotive,Engine Oil Eco 775,engine-oil-eco-775,"Synthetic engine oil 5W-30. Eco line, beige.",/images/products/engine-oil-eco-775.jpg,19.99,"Automotive Engine Oil Eco 775 Synthetic engine oil 5W-30. Eco line, beige.",207.0
204,10,Automotive,Ice Scraper Eco 750,ice-scraper-eco-750,"Ice scraper with snow brush. Eco line, beige.",/images/products/ice-scraper-eco-750.jpg,6.49,"Automotive Ice Scraper Eco 750 Ice scraper with snow brush. Eco line, beige.",230.0
205,10,Automotive,Ice Scraper Deluxe 739,ice-scraper-deluxe-739,"Ice scraper with snow brush. Deluxe line, grey.",/images/products/ice-scraper-deluxe-739.jpg,10.99,"Automotive Ice Scraper Deluxe 739 Ice scraper with snow brush. Deluxe line, grey.",438.0
206,10,Automotive,Car Vacuum Deluxe 348,car-vacuum-deluxe-348,"Handheld car vacuum cleaner. Deluxe line, silver.",/images/products/car-vacuum-deluxe-348.jpg,85.99,"Automotive Car Vacuum Deluxe 348 Handheld car vacuum cleaner. Deluxe line, silver.",703.0
207,10,Automotive,Car Vacuum Everyday 954,car-vacuum-everyday-954,"Handheld car vacuum cleaner. Everyday line, white.",/images/products/car-vacuum-everyday-954.jpg,32.99,"Automotive Car Vacuum Everyday 954 Handheld car vacuum cleaner. Everyday line, white.",260.0
208,10,Automotive,Jump Starter Essential 942,jump-starter-essential-942,"Portable jump starter with power bank. Essential line, green.",/images/products/jump-starter-essential-942.jpg,57.99,"Automotive Jump Starter Essential 942 Portable jump starter with power bank. Essential line, green.",433.0
209,10,Automotive,Jump Starter Compact 635,jump-starter-compact-635,"Portable jump starter with power bank. Compact line, white.",/images/products/jump-starter-compact-635.jpg,106.99,"Automotive Jump Starter Compact 635 Portable jump starter with power bank. Compact line, white.",161.0
210,10,Automotive,Dash Cam Premium 877,dash-cam-premium-877,"Full HD dash cam with night vision. Premium line, white.",/images/products/dash-cam-premium-877.jpg,76.99,"Automotive Dash Cam Premium 877 Full HD dash cam with night vision. Premium line, white.",321.0
211,11,Music,Acoustic Guitar Everyday 144,acoustic-guitar-everyday-144,"Acoustic guitar, spruce top. Everyday line, blue.",/images/products/acoustic-guitar-everyday-144.jpg,407.99,"Music Acoustic Guitar Everyday 144 Acoustic guitar, spruce top. Everyday line, blue.",249.0
212,11,Music,Acoustic Guitar Compact 849,acoustic-guitar-compact-849,"Acoustic guitar, spruce top. Compact line, silver.",/images/products/acoustic-guitar-compact-849.jpg,172.99,"Music Acoustic Guitar Compact 849 Acoustic guitar, spruce top. Compact line, silver.",236.0
213,11,Music,Digital Piano Deluxe 132,digital-piano-deluxe-132,"88-key digital piano with weighted keys. Deluxe line, green.",/images/products/digital-piano-deluxe-132.jpg,623.99,"Music Digital Piano Deluxe 132 88-key digital piano with weighted keys. Deluxe line, green.",74.0
214,11,Music,Digital Piano Premium 233,digital-piano-premium-233,"88-key digital piano with weighted keys. Premium line, green.",/images/products/digital-piano-premium-233.jpg,582.99,"Music Digital Piano Premium 233 88-key digital piano with weighted keys. Premium line, green.",200.0
215,11,Music,Guitar Strings Compact 500,guitar-strings-compact-500,"Steel guitar strings, light gauge. Compact line, grey.",/images/products/guitar-strings-compact-500.jpg,14.99,"Music Guitar Strings Compact 500 Steel guitar strings, light gauge. Compact line, grey.",223.0
216,11,Music,Guitar Strings Essential 403,guitar-strings-essential-403,"Steel guitar strings, light gauge. Essential line, black.",/images/products/guitar-strings-essential-403.jpg,19.99,"Music Guitar Strings Essential 403 Steel guitar strings, light gauge. Essential line, black.",224.0
217,11,Music,Studio Headphones Essential 159,studio-headphones-essential-159,"Closed-back studio monitoring headphones. Essential line, silver.",/images/products/studio-headphones-essential-159.jpg,90.99,"Music Studio Headphones Essential 159 Closed-back studio monitoring headphones. Essential line, silver.",186.0
218,11,Music,Studio Headphones Pro 770,studio-headphones-pro-770,"Closed-back studio monitoring headphones. Pro line, green.",/images/products/studio-headphones-pro-770.jpg,64.99,"Music Studio Headphones Pro 770 Closed-back studio monitoring headphones. Pro line, green.",369.0
219,11,Music,Microphone Essential 454,microphone-essential-454,"USB condenser microphone for podcasts and vocals. Essential line, red.",/images/products/microphone-essential-454.jpg,181.99,"Music Microphone Essential 454 USB condenser microphone for podcasts and vocals. Essential line, red.",233.0
220,11,Music,Microphone Eco 278,microphone-eco-278,"USB condenser microphone for podcasts and vocals. Eco line, silver.",/images/products/microphone-eco-278.jpg,76.99,"Music Microphone Eco 278 USB condenser microphone for podcasts and vocals. Eco line, silver.",168.0
221,11,Music,Guitar Amp Classic 781,guitar-amp-classic-781,"Practice guitar amplifier, 20W. Classic line, black.",/images/products/guitar-amp-classic-781.jpg,149.99,"Music Guitar Amp Classic 781 Practice guitar amplifier, 20W. Classic line, black.",154.0
222,11,Music,Guitar Amp Eco 862,guitar-amp-eco-862,"Practice guitar amplifier, 20W. Eco line, red.",/images/products/guitar-amp-eco-862.jpg,272.99,"Music Guitar Amp Eco 862 Practice guitar amplifier, 20W. Eco line, red.",167.0
223,11,Music,Ukulele Premium 117,ukulele-premium-117,"Soprano ukulele for beginners. Premium line, black.",/images/products/ukulele-premium-117.jpg,34.99,"Music Ukulele Premium 117 Soprano ukulele for beginners. Premium line, black.",1119.0
224,11,Music,Ukulele Essential 759,ukulele-essential-759,"Soprano ukulele for beginners. Essential line, beige.",/images/products/ukulele-essential-759.jpg,76.99,"Music Ukulele Essential 759 Soprano ukulele for beginners. Essential line, beige.",819.0
225,11,Music,Drum Sticks Pro 333,drum-sticks-pro-333,"Hickory drum sticks. Pro line, blue.",/images/products/drum-sticks-pro-333.jpg,9.49,"Music Drum Sticks Pro 333 Hickory drum sticks. Pro line, blue.",408.0
226,11,Music,Drum Sticks Eco 816,drum-sticks-eco-816,"Hickory drum sticks. Eco line, blue.",/images/products/drum-sticks-eco-816.jpg,24.99,"Music Drum Sticks Eco 816 Hickory drum sticks. Eco line, blue.",285.0
227,11,Music,Music Stand Everyday 471,music-stand-everyday-471,"Foldable music stand. Everyday line, blue.",/images/products/music-stand-everyday-471.jpg,46.99,"Music Music Stand Everyday 471 Foldable music stand. Everyday line, blue.",257.0
228,11,Music,Music Stand Pro 759,music-stand-pro-759,"Foldable music stand. Pro line, white.",/images/products/music-stand-pro-759.jpg,29.99,"Music Music Stand Pro 759 Foldable music stand. Pro line, white.",209.0
229,11,Music,Effects Pedal Essential 260,effects-pedal-essential-260,"Distortion effects pedal. Essential line, grey.",/images/products/effects-pedal-essential-260.jpg,64.99,"Music Effects Pedal Essential 260 Distortion effects pedal. Essential line, grey.",487.0
230,11,Music,Effects Pedal Eco 176,effects-pedal-eco-176,"Distortion effects pedal. Eco line, white.",/images/products/effects-pedal-eco-176.jpg,110.99,"Music Effects Pedal Eco 176 Distortion effects pedal. Eco line, white.",701.0
231,11,Music,Studio Headphones Classic 686,studio-headphones-classic-686,"Closed-back studio monitoring headphones. Classic line, red.",/images/products/studio-headphones-classic-686.jpg,76.99,"Music Studio Headphones Classic 686 Closed-back studio monitoring headphones. Classic line, red.",1762.0
232,12,Tools,Cordless Drill Classic 499,cordless-drill-classic-499,"Cordless drill driver with two batteries. Classic line, grey.",/images/products/cordless-drill-classic-499.jpg,162.99,"Tools Cordless Drill Classic 499 Cordless drill driver with two batteries. Classic line, grey.",686.0
233,12,Tools,Cordless Drill Everyday 416,cordless-drill-everyday-416,"Cordless drill driver with two batteries. Everyday line, green.",/images/products/cordless-drill-everyday-416.jpg,150.99,"Tools Cordless Drill Everyday 416 Cordless drill driver with two batteries. Everyday line, green.",253.0
234,12,Tools,Screwdriver Set Eco 897,screwdriver-set-eco-897,"Precision screwdriver set. Eco line, beige.",/images/products/screwdriver-set-eco-897.jpg,13.99,"Tools Screwdriver Set Eco 897 Precision screwdriver set. Eco line, beige.",669.0
235,12,Tools,Screwdriver Set Pro 103,screwdriver-set-pro-103,"Precision screwdriver set. Pro line, black.",/images/products/screwdriver-set-pro-103.jpg,25.99,"Tools Screwdriver Set Pro 103 Precision screwdriver set. Pro line, black.",370.0
236,12,Tools,Hammer Essential 301,hammer-essential-301,"Claw hammer with fiberglass handle. Essential line, red.",/images/products/hammer-essential-301.jpg,36.99,"Tools Hammer Essential 301 Claw hammer with fiberglass handle. Essential line, red.",403.0
237,12,Tools,Hammer Essential 102,hammer-essential-102,"Claw hammer with fiberglass handle. Essential line, blue.",/images/products/hammer-essential-102.jpg,34.99,"Tools Hammer Essential 102 Claw hammer with fiberglass handle. Essential line, blue.",218.0
238,12,Tools,Tape Measure Pro 133,tape-measure-pro-133,"5 metre tape measure. Pro line, blue.",/images/products/tape-measure-pro-133.jpg,15.99,"Tools Tape Measure Pro 133 5 metre tape measure. Pro line, blue.",275.0
239,12,Tools,Tape Measure Premium 980,tape-measure-premium-980,"5 metre tape measure. Premium line, blue.",/images/products/tape-measure-premium-980.jpg,8.49,"Tools Tape Measure Premium 980 5 metre tape measure. Premium line, blue.",402.0
240,12,Tools,Toolbox Premium 215,toolbox-premium-215,"Toolbox with 100 hand tools. Premium line, black.",/images/products/toolbox-premium-215.jpg,26.99,"Tools Toolbox Premium 215 Toolbox with 100 hand tools. Premium line, black.",186.0
241,12,Tools,Toolbox Compact 854,toolbox-compact-854,"Toolbox with 100 hand tools. Compact line, green.",/images/products/toolbox-compact-854.jpg,119.99,"Tools Toolbox Compact 854 Toolbox with 100 hand tools. Compact line, green.",288.0
242,12,Tools,Ladder Everyday 810,ladder-everyday-810,"Aluminium step ladder. Everyday line, beige.",/images/products/ladder-everyday-810.jpg,194.99,"Tools Ladder Everyday 810 Aluminium step ladder. Everyday line, beige.",85.0
243,12,Tools,Ladder Deluxe 713,ladder-deluxe-713,"Aluminium step ladder. Deluxe line, green.",/images/products/ladder-deluxe-713.jpg,53.99,"Tools Ladder Deluxe 713 Aluminium step ladder. Deluxe line, green.",1346.0
244,12,Tools,Circular Saw Deluxe 150,circular-saw-deluxe-150,"Circular saw, 1200W. Deluxe line, beige.",/images/products/circular-saw-deluxe-150.jpg,168.99,"Tools Circular Saw Deluxe 150 Circular saw, 1200W. Deluxe line, beige.",157.0
245,12,Tools,Circular Saw Pro 650,circular-saw-pro-650,"Circular saw, 1200W. Pro line, red.",/images/products/circular-saw-pro-650.jpg,120.99,"Tools Circular Saw Pro 650 Circular saw, 1200W. Pro line, red.",129.0
246,12,Tools,Spirit Level Pro 357,spirit-level-pro-357,"Spirit level, 60 cm. Pro line, blue.",/images/products/spirit-level-pro-357.jpg,21.99,"Tools Spirit Level Pro 357 Spirit level, 60 cm. Pro line, blue.",294.0
247,12,Tools,Spirit Level Eco 157,spirit-level-eco-157,"Spirit level, 60 cm. Eco line, silver.",/images/products/spirit-level-eco-157.jpg,15.99,"Tools Spirit Level Eco 157 Spirit level, 60 cm. Eco line, silver.",581.0
248,12,Tools,Work Gloves Pro 810,work-gloves-pro-810,"Protective work gloves. Pro line, silver.",/images/products/work-gloves-pro-810.jpg,9.49,"Tools Work Gloves Pro 810 Protective work gloves. Pro line, silver.",170.0
249,12,Tools,Work Gloves Compact 227,work-gloves-compact-227,"Protective work gloves. Compact line, white.",/images/products/work-gloves-compact-227.jpg,7.49,"Tools Work Gloves Compact 227 Protective work gloves. Compact line, white.",666.0
250,12,Tools,Glue Gun Deluxe 657,glue-gun-deluxe-657,"Hot glue gun with glue sticks. Deluxe line, silver.",/images/products/glue-gun-deluxe-657.jpg,19.99,"Tools Glue Gun Deluxe 657 Hot glue gun with glue sticks. Deluxe line, silver.",243.0
251,12,Tools,Glue Gun Eco 799,glue-gun-eco-799,"Hot glue gun with glue sticks. Eco line, silver.",/images/products/glue-gun-eco-799.jpg,32.99,"Tools Glue Gun Eco 799 Hot glue gun with glue sticks. Eco line, silver.",276.0
252,12,Tools,Spirit Level Classic 425,spirit-level-classic-425,"Spirit level, 60 cm. Classic line, beige.",/images/products/spirit-level-classic-425.jpg,15.99,"Tools Spirit Level Classic 425 Spirit level, 60 cm. Classic line, beige.",238.0
```

### data/README.md

# Day 5 podaci — product text korpus (izvedena tabela)

Deterministička, **byte-for-byte reproduktivna** tabela **izvedena** iz Day 1
seeded kataloga (ne duplira ga). Kompletna dokumentacija (izvor, parametri,
značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `products_text.csv` | 252 proizvoda: katalog + `product_text` (za TF-IDF) + `popularity` (baseline skor) | 252 |
| `metadata.json` | izvor, counts, značenja polja, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/products.csv` + `Day 1/data/categories.csv` +
  `Day 1/data/events.csv` (jedini izvor istine).
* Tekst: `prepare_product_text` (`app/recommenders/content.py`) —
  `category_name + name + description` (kategorija je token).
* Popularnost: `_popularity_from_events` — težinski zbir događaja po proizvodu
  (`product_view`=1, `add_to_cart`=3, `purchase`=5).
* Generator: `app/data/generate_product_text.py` (upisuje CSV + metadata).

## Ključne kolone (`products_text.csv`)

| Kolona | Značenje |
| --- | --- |
| `product_id` | FK -> `products.product_id` |
| `category_id` / `category_name` | kategorija (name je i token u tekstu) |
| `name` / `slug` / `description` | katalog (iz Day 1) |
| `img_url` / `price` | slika / cena (za product page) |
| `product_text` | tekst za TF-IDF: `category + name + description` |
| `popularity` | težinski zbir događaja — popularity baseline skor |

## Stanje u ovom seed-u

* proizvoda: **252** (12 kategorija × 21)
* proizvoda sa događajima: **252**
* popularnost: min **70** · med **288** · max **2115**
* top-5 po popularnosti: **90, 184, 110, 12, 49**

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_product_text
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

`product_text` je *ulaz* za content preporuke, ne rezultat. Sličan tekst nije
isto što i dobra preporuka (vidi Day 5 README, „What the result does NOT
prove"). Popularnost je baseline za poređenje, ne istina o kvalitetu proizvoda.

### examples/demo\_content\_recommender.py

```
"""Demo: content-based product recommender (Day 5).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 5/examples/demo_content_recommender.py"

Prikazuje:
  1) product text korpus (broj proizvoda, kategorije, popularnost);
  2) **baseline-ove** — popularity top-5 i category top-5 za proizvod;
  3) **content preporuke** (TF-IDF + kosinusna sličnost) — najsličniji bez
     targeta, sa skorom;
  4) **cold-start fallback** — nov proizvod (bez TF-IDF reda) -> popularity
     baseline sa ``fallback=true``, ne tihi ``[]``;
  5) **baseline comparison** — content vs category vs popular za nekoliko
     proizvoda (overlap) — tabela koju README citira.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.recommender import RecommenderService

EXAMPLES = [1, 2, 23, 144, 232]  # pokrivaju različite kategorije i rečnike


def main() -> None:
    print("=== Day 5 — Content-Based Product Recommender (demo) ===\n")
    svc = RecommenderService()

    products = svc.products
    print(f"[0] Product text korpus: {len(products)} proizvoda, "
          f"{products['category_id'].nunique()} kategorija")
    print(f"    popularnost (baseline skor iz događaja): "
          f"min {products['popularity'].min():.0f} · med {products['popularity'].median():.0f} · "
          f"max {products['popularity'].max():.0f}")
    print()

    # --- 1) Baselines ------------------------------------------------------ #
    print("[1] Baselines (obavezne referentne tačke):")
    pop = svc.popular_recommendations(5)
    print("    /recommendations/popular (top-5):")
    for r in pop["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} pop={r['score']:.0f}")
    pid = 1
    cat = svc.category_recommendations(pid, 5)
    print(f"    /recommendations/category/{pid} (top-5, bez targeta):")
    for r in cat["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} pop={r['score']:.0f}")
    print()

    # --- 2) Content preporuke --------------------------------------------- #
    print("[2] Content preporuke (TF-IDF + kosinusna sličnost):")
    content = svc.content_recommendations(pid, 5)
    print(f"    /recommendations/content/{pid}: method={content['method']} "
          f"fallback={content['fallback']}")
    for r in content["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} score={r['score']:.4f}")
    ids = [r["product_id"] for r in content["recommendations"]]
    print(f"    target {pid} isključen: {pid not in ids}")
    print()

    # --- 3) Cold-start fallback ------------------------------------------- #
    print("[3] Cold-start fallback (nov proizvod bez TF-IDF reda):")
    cs = svc.content_recommendations(99999, 5)
    print(f"    /recommendations/content/99999: method={cs['method']} "
          f"fallback={cs['fallback']} reason={cs['fallback_reason']}")
    print(f"    -> popularity baseline, {cs['returned']} preporuka (NIKAD tihi [])")
    print()

    # --- 4) Baseline comparison ------------------------------------------- #
    print("[4] Baseline comparison (content vs category vs popular):")
    print(f"    {'target':>6} {'content top-5':<34} {'category top-5':<34} {'overlap c∩cat':<14}")
    for pid in EXAMPLES:
        comp = svc.baseline_comparison(pid, 5)
        c = ",".join(str(r["product_id"]) for r in comp["content"]["recommendations"])
        cat_ids = ",".join(str(r["product_id"]) for r in comp["category"]["recommendations"])
        ov = ",".join(str(x) for x in comp["overlap"]["content_vs_category"]) or "—"
        print(f"    {pid:>6} {c:<34} {cat_ids:<34} {ov:<14}")
    print()

    print("Gotovo. Vizualizacija: python3 \"Day 5/examples/visualize_content.py\"")


if __name__ == "__main__":
    main()
```

### examples/visualize\_content.py

```
"""Vizualizacija content preporuka (Day 5, supporting material).

Dve slike u ``Day 5/examples/``:

    - ``cosine_heatmap.png`` — kosinusna sličnost između uzorka proizvoda
      (24 proizvoda iz 2 kategorije): blokovska struktura po kategoriji +
      „hot" dijagonalni parovi (proizvodi sa istim rečnikom su skoro duplikati —
      overspecialization).
    - ``baseline_overlap.png`` — za nekoliko targeta, koliko od top-5 content
      preporuka se poklapa sa category top-5 i popularity top-5 (baseline
      comparison).

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 5/examples/visualize_content.py"

Zahteva ``matplotlib`` (u ``dm-ml/requirements.txt``).
"""

import sys
from pathlib import Path

# dm-ml na sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import matplotlib

matplotlib.use("Agg")  # bez GUI — čuvamo PNG fajlove
import matplotlib.pyplot as plt
import numpy as np

from app.recommenders.content import build_tfidf_matrix, calculate_product_similarity
from app.services.recommender import RecommenderService, TFIDF_KWARGS

OUT_DIR = Path(__file__).resolve().parent
SAMPLE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
              22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]  # Electronics + Fashion


def cosine_heatmap(svc: RecommenderService) -> None:
    """Heatmap kosinusne sličnosti za uzorak proizvoda (2 kategorije)."""
    products = svc.products
    sample = products[products["product_id"].isin(SAMPLE_IDS)].sort_values("product_id")
    matrix, _ = build_tfidf_matrix(sample, **TFIDF_KWARGS)
    full = np.zeros((len(sample), len(sample)))
    for i in range(len(sample)):
        full[i] = calculate_product_similarity(matrix, i)

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(full, cmap="viridis", vmin=0, vmax=1)
    labels = [f"{int(r['product_id'])}:{r['name'].split()[0][:8]}" for _, r in sample.iterrows()]
    ax.set_xticks(range(len(sample)))
    ax.set_yticks(range(len(sample)))
    ax.set_xticklabels(labels, fontsize=5.5, rotation=90)
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_title("Kosinusna sličnost teksta proizvoda (Electronics + Fashion)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "cosine_heatmap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'cosine_heatmap.png'}")


def baseline_overlap(svc: RecommenderService) -> None:
    """Trakice: overlap content∩category i content∩popular po targetu."""
    targets = [1, 2, 23, 144, 232]
    cat_overlap, pop_overlap = [], []
    for pid in targets:
        comp = svc.baseline_comparison(pid, 5)
        cat_overlap.append(len(comp["overlap"]["content_vs_category"]))
        pop_overlap.append(len(comp["overlap"]["content_vs_popular"]))

    x = range(len(targets))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar([i - w / 2 for i in x], cat_overlap, w, label="content ∩ category", color="#3b82f6")
    b2 = ax.bar([i + w / 2 for i in x], pop_overlap, w, label="content ∩ popular", color="#94a3b8")
    for i, (c, p) in enumerate(zip(cat_overlap, pop_overlap)):
        ax.text(i - w / 2, c + 0.05, str(c), ha="center", fontsize=9)
        ax.text(i + w / 2, p + 0.05, str(p), ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"p{pid}" for pid in targets])
    ax.set_ylabel("overlap (od top-5)")
    ax.set_title("Content vs baselines — poklapanje top-5 preporuka")
    ax.set_ylim(0, 5)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "baseline_overlap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'baseline_overlap.png'}")


def main() -> None:
    print("=== Day 5 — content recommender vizualizacija ===")
    svc = RecommenderService()
    cosine_heatmap(svc)
    baseline_overlap(svc)
    print("Gotovo.")


if __name__ == "__main__":
    main()
```

### lab/README.md

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

### lab/starter.py

```
"""Starter za Day 5 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 5/lab/``, koristi dm-ml venv — ima sklearn):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Kolone koje sve preporuke vraćaju (product_info + score).
RECOMMENDATION_COLUMNS = [
    "product_id", "name", "slug", "description", "img_url",
    "category_id", "price", "score",
]


def recommend_popular(products_df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Top-N proizvoda po popularnosti (baseline bez ML-a). TODO: implementirati.

    Zahtevi:
    - ``products_df`` ima kolonu ``popularity`` (skor po proizvodu).
    - Sortiraj opadajuće po ``popularity`` (tie-break po ``product_id`` rastuće),
      uzmi prvih ``limit``, i vrati kolone ``RECOMMENDATION_COLUMNS`` gde je
      ``score`` = ``popularity``.
    """
    raise NotImplementedError("implementiraj recommend_popular")


def recommend_same_category(
    products_df: pd.DataFrame,
    product_id: int,
    limit: int = 5,
) -> pd.DataFrame:
    """Top-N iz ISTE kategorije kao ``product_id`` (baseline). TODO: implementirati.

    Zahtevi:
    - ``product_id`` mora postojati u ``products_df`` (inače ``ValueError``).
    - Zadrži samo proizvode iste kategorije, ISKLJUČI sam target, sortiraj po
      ``popularity`` opadajuće (tie-break po ``product_id``) i vrati top-``limit``
      sa ``RECOMMENDATION_COLUMNS`` (``score`` = ``popularity``).
    """
    raise NotImplementedError("implementiraj recommend_same_category")


def prepare_product_text(
    products_df: pd.DataFrame,
    include_category: bool = True,
) -> pd.Series:
    """Tekstualna reprezentacija proizvoda za TF-IDF. TODO: implementirati.

    Zahtevi:
    - Tekst = ``name`` + razmak + ``description``.
    - Ako je ``include_category``, dodaj ispred i ``category_name`` (npr.
      ``"Electronics Smartphone 5102 Smartphone for electronics"``).
    - Vrati ``pd.Series`` indeksiranu po ``product_id`` (kolona ``product_id``).
    """
    raise NotImplementedError("implementiraj prepare_product_text")


def build_tfidf_matrix(
    products_df: pd.DataFrame,
    text_column: str = "product_text",
) -> tuple:
    """TF-IDF matrica nad kolonom teksta. TODO: implementirati.

    Zahtevi:
    - Ako ``products_df`` nema ``text_column``, napravi je pozivom
      ``prepare_product_text``.
    - ``TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)``
      fit_transform nad tekstovima -> ``(matrix, vectorizer)``. Matrica je
      poravnata sa ``products_df`` (red i = proizvod i).
    """
    raise NotImplementedError("implementiraj build_tfidf_matrix")


def calculate_product_similarity(tfidf_matrix, index: int) -> np.ndarray:
    """Kosinusne sličnosti reda ``index`` sa svim redovima. TODO: implementirati.

    Zahtevi: ``cosine_similarity(tfidf_matrix[index:index+1], tfidf_matrix)``
    vrati ``.flatten()``. Red ``index`` (uključujući sebe) -> niz dužine
    ``tfidf_matrix.shape[0]``. TfidfVectorizer normalizuje redove, pa je kosinus
    = skalarni proizvod normalizovanih vektora (ne poredi raw counts!).
    """
    raise NotImplementedError("implementiraj calculate_product_similarity")


def recommend_similar_products(
    products_df: pd.DataFrame,
    product_id: int,
    tfidf_matrix,
    limit: int = 5,
) -> pd.DataFrame:
    """Content preporuke po kosinusnoj sličnosti, BEZ targeta. TODO: implementirati.

    Zahtevi:
    - Ako ``product_id`` NIJE u ``products_df`` (cold start / nov proizvod) ->
      fallback: vrati ``recommend_popular(products_df, limit)`` (baseline —
      nikad prazan rezultat bez objašnjenja).
    - Inače: izračunaj sličnosti (``calculate_product_similarity``), ISKLJUČI
      target iz kandidata (najsličniji ne sme biti sam target), sortiraj
      opadajuće po ``score`` (tie-break ``product_id``) i vrati top-``limit``
      sa ``RECOMMENDATION_COLUMNS`` (``score`` = kosinusna sličnost).
    """
    raise NotImplementedError("implementiraj recommend_similar_products")
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
import pandas as pd

P = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "products_text.csv")


def test_popular_and_category():
    assert list(lab.recommend_popular(P, 5)["product_id"]) == [90, 184, 110, 12, 49]
    assert list(lab.recommend_popular(P, 3).columns) == lab.RECOMMENDATION_COLUMNS
    c = lab.recommend_same_category(P, 1, 5)
    assert 1 not in set(c["product_id"]) and set(P.set_index("product_id").loc[c["product_id"], "category_id"]) == {1}
    with pytest.raises(ValueError):
        lab.recommend_same_category(P, 99999)


def test_text_and_tfidf():
    t = lab.prepare_product_text(P.drop(columns=["product_text"]))
    assert t.loc[1] == "Electronics Smartphone Compact 686 5G smartphone with OLED display, dual camera and fast charging. Compact line, black."
    m, vec = lab.build_tfidf_matrix(P)
    assert m.shape[0] == len(P)
    sims = lab.calculate_product_similarity(m, 0)
    assert len(sims) == len(P) and sims[0] == pytest.approx(1.0)


def test_similar_excludes_target_and_cold_start():
    m, _ = lab.build_tfidf_matrix(P)
    r = lab.recommend_similar_products(P, 1, m, 5)
    assert 1 not in set(r["product_id"]) and r["score"].is_monotonic_decreasing
    cold = lab.recommend_similar_products(P, 99999, m, 5)
    assert list(cold["product_id"]) == [90, 184, 110, 12, 49]
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 5 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from starter import RECOMMENDATION_COLUMNS  # noqa: F401


def _out(df, score):
    df = df.copy(); df["score"] = list(score)
    for c in RECOMMENDATION_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[RECOMMENDATION_COLUMNS].reset_index(drop=True)


def recommend_popular(products_df, limit=5):
    d = products_df.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def recommend_same_category(products_df, product_id, limit=5):
    hit = products_df[products_df["product_id"] == product_id]
    if hit.empty:
        raise ValueError(f"nepoznat proizvod {product_id}")
    d = products_df[(products_df["category_id"] == hit.iloc[0]["category_id"]) & (products_df["product_id"] != product_id)]
    d = d.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def prepare_product_text(products_df, include_category=True):
    t = products_df["name"].fillna("") + " " + products_df["description"].fillna("")
    if include_category:
        t = products_df["category_name"].fillna("") + " " + t
    return pd.Series(t.str.strip().values, index=products_df["product_id"].values)


def build_tfidf_matrix(products_df, text_column="product_text"):
    texts = products_df[text_column] if text_column in products_df.columns else prepare_product_text(products_df)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    return vec.fit_transform(list(texts.fillna(""))), vec


def calculate_product_similarity(tfidf_matrix, index):
    return cosine_similarity(tfidf_matrix[index:index + 1], tfidf_matrix).flatten()


def recommend_similar_products(products_df, product_id, tfidf_matrix, limit=5):
    pos = np.where(products_df["product_id"].to_numpy() == product_id)[0]
    if len(pos) == 0:
        return recommend_popular(products_df, limit)
    d = products_df.assign(_s=calculate_product_similarity(tfidf_matrix, int(pos[0])))
    d = d[d["product_id"] != product_id].sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["_s"])
```
