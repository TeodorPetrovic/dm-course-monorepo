# Dan 6 — Collaborative Recommender (Implicit Feedback)

- lesson_id: 116
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:46.936 updated: 2026-09-05 20:00:29.192
- summary: Item-item CF preporučuje šta izgleda kao ko-interagovano — ne dokazuje da će korisnik to voleti. Postojeća session-co-occurrence heuristika je obavezan baseline; težine događaja (view=1/cart=3/purchase=5) su pretpostavke, ne istine — promena težina menja izlaz, i to je dokaz da su pretpostavke. [subjects-import]


---

<!-- page_id 422 order 0 -->
## [Page] Materijal

# Dan 6 — Collaborative Recommender (Implicit Feedback)

> *Item-item CF preporučuje šta izgleda kao ko-interagovano — ne dokazuje da će
> korisnik to voleti. Postojeća session-co-occurrence heuristika je obavezan
> baseline; težine događaja (view=1/cart=3/purchase=5) su pretpostavke, ne
> istine — promena težina menja izlaz, i to je dokaz da su pretpostavke.*

## Šta gradimo

Collaborative recommender: **implicitna interaction matrica** (sesije ×
proizvodi) iz Day 1 događaja + **item-item kosinusna sličnost** → preporuke
sličnih proizvoda, kao formalna nadogradnja postojeće **session-co-occurrence
heuristike** (`recomendations.py::get_collaborative_recommendations`). Izloženo
kroz `GET /recommendations/collaborative/{product_id}` (sa
`/recommendations/collaborative/{product_id}/comparison` za heuristic-vs-CF) i
integrisano u product page kao „Customers Also Viewed". Cilj dana je da
razdvoji **ko-interakciju** (šta sesije gledaju zajedno) od **preferencije**
(šta korisnik voli) — i da pokaže da su težine interakcija pretpostavke koje
podaci treba da smeju da obore.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `build_interaction_matrix` | **data preprocessing** (događaji → implicitna matrica) |
| `calculate_item_similarity` | **statistical** (item-item kosinusna sličnost — nema naučenih parametara) |
| `recommend_from_item_similarity` | **statistical** (rank + cold-start fallback) |
| `recommend_session_cooccurrence` | **rule / heuristic** (Day 1/seed baseline, bez ML-a) |
| `weight_sensitivity_experiment` | **statistical / experiment** (težine = pretpostavke) |
| `examples/toy_sgd.py` | **machine learning** (MF od nule — SGD) |
| `examples/mf_library.py` | **machine learning** (MF preko `surprise`/`implicit`) |

## Application requirement

Product page u `dm-frontend` već ima „Recommended Products" (Day 5: content).
Day 6 dodaje **„Customers Also Viewed"** sekciju koja poziva
`GET /ml/recommendations/collaborative/{product_id}` — preporuke po tome šta
su *druge sesije* gledale/kupile zajedno, ne po sličnosti teksta. Bez toga,
product page nema nikakav signal iz ponašanja korisnika — samo tekst.

## Ciljevi učenja

Do kraja dana treba da:

* izgradite **implicitnu interaction matricu** iz događaja (sesije × proizvodi,
  težine, sparse) i objasnite šta je *implicit feedback* vs *eksplicitna ocena*;
* izračunate **item-item kosinusnu sličnost** (sa i bez session-length
  normalizacije) i preporučite slične proizvode **bez targeta**;
* objasnite zašto je postojeća **session-co-occurrence heuristika** baseline, a
  ne odgovor (sirov `count × weight`, bez normalizacije);
* testirate **alternativne težine** (weight-sensitivity) i objasnite da su težine
  **pretpostavke** koje podaci treba da smeju da obore;
* rešite **cold start** (nov proizvod / proizvod bez interakcija) eksplicitnim
  fallback-om — nikad tihi `[]`;
* uradite **mali SGD od nule** na toy matrici i proverite da faktori
  reprodukuju matricu;
* koristite **`surprise`/`implicit`** za matrix factorization (ekstenzija).

## Preduslovi

Day 1 događaji (event tracking, sesije), Day 5 katalog (`products_text.csv`),
kosinusna sličnost, sparse matrice (scipy), FastAPI rute (Day 1–4).

## Postojeći sistem (šta nasleđujemo)

* **Day 1/seed heuristika:** `recomendations.py::get_collaborative_recommendations`
  — nađi sesije target proizvoda, skor ostalih = `Σ(count × weight)`. Radeći
  baseline, ali sirov: bez session-length normalizacije, bez item normalizacije.
* **Day 5 sloj:** content recommender (TF-IDF + kosinus) sa baseline-ima i
  cold-start fallback-om — ista filozofija „nikad tiho prazno" se nastavlja.
* **Nedostaje:** bilo kakva preporuka iz *ponašanja* (ko-interakcija). Content
  gleda tekst; Day 6 uvodi pravi implicit-feedback CF sa evaluacijom protiv
  postojeće heuristike.

## Arhitektura

```
Day 1 događaji (events.csv)                Day 5 katalog (products_text.csv)
      │                                               │
      ▼                                               ▼
app/data/generate_interactions.py      interaction matrix (Day 6/data)
      │                                      (sesije × proizvodi, max-težina)
      ▼                                               │
app/recommenders/collaborative.py   build_interaction_matrix
                                    calculate_item_similarity (item-item kosinus)
                                    recommend_from_item_similarity (rank + fallback)
                                    recommend_session_cooccurrence (heuristic baseline)
      │
      ▼
app/services/collaborative.py    CollaborativeRecommenderService
      │                            (lazy matrica + sličnost, comparison, weight-sensitivity)
      ▼
app/api/recommendation_routes.py   GET /recommendations/collaborative/{product_id}
                                   GET /recommendations/collaborative/{product_id}/comparison
      │
      ▼
dm-frontend product page   product/[slug].vue -> /ml/recommendations/collaborative/{id}
```

## Korišćeni podaci

**Implicitna interaction matrica** (seeded, `Day 6/data/interactions.csv`,
jedini izvor: `app/data/generate_interactions.py`) — izvedena tabela iz Day 1
događaja (ne duplira ih):

| Kolona | Značenje |
| --- | --- |
| `session_id` | `user_session` — red matrice |
| `product_id` | proizvod — kolona matrice |
| `value` | agregirana težina interakcije (max: view=1, cart=3, purchase=5) |

Stanje: **15 360 sesija × 252 proizvoda**, **90 761** nenultih ćelija,
**gustina 0.0234** (≈ 97.7 % prazno — sparsity). Svih 252 proizvoda ima
interakcije; 13 763 sesije imaju ≥ 2 različita proizvoda (co-occurrence signal).
Top-5 po vrednosti interakcija: **90, 184, 110, 12, 49**. (Day 1 ima 15 361 sesiju;
jedna sesija nema nijedan proizvodni događaj, pa nema red u matrici.)

## AI-ML koncept

* **Implicit feedback vs eksplicitne ocene.** Ovo NIJE MovieLens (ocene 1–5).
  Naši signali su događaji: pogledao, dodao u korpu, kupio. Svaki događaj nosi
  *težinu* — ali težina je *prisustvo*, ne ocena. Proizvod gledan 5 puta u
  sesiji nije „5× voljeniji" — u matrici je i dalje jedna interakcija
  (`max` agregacija). Brojanje interakcija kao ocenu (zbir 1+3+5=9) je čest bag.
* **Sparsity.** Većina (sesija, proizvod) ćelija je prazna — zato matrica mora
  biti sparse (`csr_matrix`). Dense matrica 15 360 × 252 bi bila ~31 MB u
  float64 (~15.5 MB u float32), dok sparse CSR sa 90 761 nenultih ćelija zauzima ~1.2 MB;
  dense verzija raste sa *proizvodom* broja sesija i proizvoda.
* **Item-item CF.** Item vektor = kolona matrice (koliko je svaka sesija
  interagovala sa proizvodom). Kosinus između kolona = koliko slično sesije
  „vide" dva proizvoda. Preporuka = najsličniji proizvodi po tom vektoru.
  Item-item (ne user-user) zato što se katalog sporije menja od korisnika.
* **Session-length normalization.** Dugačka sesija (20 pregleda) „spaja" svih
  20 proizvoda jako; bez normalizacije to dominira. L2-normalizacija svake
  sesije pre računanja sličnosti smanjuje taj efekat (vežba: uporedi sa i bez).
* **Težine su pretpostavke.** view=1/cart=3/purchase=5 su *izbor*, ne istina.
  Weight-sensitivity eksperiment menja težine i gleda kako se menja izlaz —
  kada se izlaz menja, to je dokaz da su težine hipoteza, ne odgovor.
* **Heuristika kao baseline.** Postojeća heuristika (`Σ count × weight`) je
  obavezna referentna tačka: „CF pomaže" mora da stoji pored nje. Ona nema
  normalizaciju — zato je baseline, ne rešenje.
* **Matrix factorization (MF).** SGD uči faktore `R ≈ P·Qᵀ` (latentni domeni).
  Toy SGD (`examples/toy_sgd.py`) je mehanizam od nule; `surprise`/`implicit`
  su bibliotečke ekstenzije (`examples/mf_library.py`) — ista ideja, gotove
  optimizacije.

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Interaction matrica (`app/recommenders/collaborative.py`)

`build_interaction_matrix(events_df, weights, aggregation="max", level="session", products=None)` — filtrira događaje po težinama, grupisanje (sesija, proizvod),
agregacija **max** (ili `sum`/`binary`), sparse `csr_matrix` + `InteractionMatrix`
(redovi = sesije, kolone = proizvodi). `products` poravnava kolone na katalog
(proizvodi bez interakcija → nula kolone, da se `no_interactions` razlikuje od
`unknown_product`).

### Korak 2 — Item-item sličnost (`calculate_item_similarity`)

`cosine_similarity(matrix.T)` → `n_proizvoda × n_proizvoda` (sparse). Sa
`row_normalize=True` (default) svaka sesija se prvo L2-normalizuje
(session-length normalization) — bez toga duge sesije dominiraju.

### Korak 3 — Preporuke (`recommend_from_item_similarity`)

Sličnosti → **isključi target** → top-N po `score` (tie-break `product_id`).
Cold start: nepoznat proizvod → `fallback="unknown_product"` na popularity;
proizvod sa nula interakcija → `fallback="no_interactions"`. Vraća envelope
`{product_id, method, fallback, fallback_reason, recommendations}` — nikad tihi
`[]`.

### Korak 4 — Heuristic baseline (`recommend_session_cooccurrence`)

Veran port seed heuristike: sesije targeta → `Σ(count × weight)` za ostale
proizvode. `method="heuristic"`, isti fallback envelope. Ovo je **baseline za
poređenje**, ne „tačan odgovor".

### Korak 5 — Poređenja

`compare_heuristic_vs_cf(...)` — heuristic vs CF za jedan proizvod (overlap);
`weight_sensitivity_experiment(...)` — top-N po šemi težina +
`overlap_with_default` (težine su pretpostavke).

### Korak 6 — Servis + API (`app/services/collaborative.py`, `app/api/recommendation_routes.py`)

`CollaborativeRecommenderService` učitava Day 5 katalog + `Day 6/data/ interactions.csv`, gradi matricu i sličnost **lazy** (kešira), nudi
`collaborative_recommendations` / `heuristic_recommendations` /
`collaborative_comparison` / `weight_sensitivity`. API rute registrovane u
`app/api/recommendation_routes.py` (uključene preko `app/api/routes.py` u `app/main.py`).

### Korak 7 — Toy SGD + MF ekstenzija (`Day 6/examples/`)

`toy_sgd.py` — SGD faktorizacija od nule na toy matrici (RMSE pada, faktori
reprodukuju matricu). `mf_library.py` — `implicit` ALS na Day 6 matrici
(slični proizvodi iz faktora) + `surprise` SVD na toy ocenama (predikcija
nepoznate ćelije). Biblioteke su opcione (dodate u `requirements.txt`).

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `build_interaction_matrix(...)` | događaji → implicitna matrica (max-težina, sparse) | `app/recommenders/collaborative.py` |
| `calculate_item_similarity(...)` | item-item kosinusna sličnost (+ session-length normalizacija) | `app/recommenders/collaborative.py` |
| `recommend_from_item_similarity(...)` | rank + target exclusion + cold-start fallback | `app/recommenders/collaborative.py` |
| `recommend_session_cooccurrence(...)` | postojeća heuristika (baseline) | `app/recommenders/collaborative.py` |
| `compare_heuristic_vs_cf(...)` | heuristic vs CF (overlap) | `app/recommenders/collaborative.py` |
| `weight_sensitivity_experiment(...)` | težine = pretpostavke (top-N po šemi) | `app/recommenders/collaborative.py` |
| `CollaborativeRecommenderService.*` | CF/heuristic/comparison/weight-sensitivity | `app/services/collaborative.py` |
| `app/data/generate_interactions.py` | generiše `Day 6/data/*` (byte-for-byte) | `app/data/generate_interactions.py` |
| `examples/toy_sgd.py` | SGD MF od nule (toy matrica) | `Day 6/examples/toy_sgd.py` |
| `examples/mf_library.py` | MF preko `implicit` ALS + `surprise` SVD | `Day 6/examples/mf_library.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /recommendations/collaborative/{product_id}?limit=` | 200: CF (item-item) bez targeta; cold start -> **fallback envelope** (`method:"fallback"`, `fallback_reason`, popularity recs); **422** nevalidan limit |
| `GET /recommendations/collaborative/{product_id}/comparison?limit=` | 200: `{heuristic, collaborative, overlap}` — postojeća heuristika vs CF |
| `GET /recommendations/popular` | 200: popularity baseline (Day 5) — radi uvek |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /recommendations/collaborative/1?limit=2`

```
{
  "product_id": 1,
  "method": "collaborative",
  "fallback": false,
  "fallback_reason": null,
  "returned": 2,
  "recommendations": [
    { "product_id": 12, "name": "Keyboard Classic 505", "slug": "keyboard-classic-505",
      "description": "Mechanical keyboard with backlight, quiet switches. Classic line, red.",
      "img_url": "/images/products/keyboard-classic-505.jpg", "category_id": 1, "price": 24.99, "score": 0.1362 },
    { "product_id": 2, "name": "Smartphone Compact 854", "slug": "smartphone-compact-854",
      "description": "5G smartphone with OLED display, dual camera and fast charging. Compact line, red.",
      "img_url": "/images/products/smartphone-compact-854.jpg", "category_id": 1, "price": 263.99, "score": 0.1256 }
  ]
}
```

**Cold start:** `GET /recommendations/collaborative/99999` vraća
`method="fallback"`, `fallback=true`, `fallback_reason="unknown_product"` i
top-N po popularnosti — NIKAD tihi `[]`.

## CMS integracija

Product page `dm-frontend/app/pages/product/[slug].vue` (vidi taj fajl):

* Nova sekcija **„Customers Also Viewed"** — poziva
  `GET /ml/recommendations/collaborative/{product_id}` (Nitro proxy `/ml/**` →
  `:3001`), badge `collaborative`.
* Renderuje **top-5 CF preporuke** (slika, naziv, opis, cena iz `rec.price`).
* Ako je `fallback=true` (cold start) prikazuje poruku „showing popularity
  fallback".
* **Graceful fallback:** ako dm-ml ne radi, `try/catch` → prazna lista — stranica
  se NE ruši.
* Klik na preporuku šalje `recommendation_click` sa
  `recommendation_source="collaborative"` (Day 1 šema — feedback za Day 9).

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 6/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno: `build_interaction_matrix` (oblik, **max/sum/binary agregacija**,
težine, catalog alignment, sparsity, prazni događaji), round-trip
(`to_long_frame`/`from_long_csv`), `calculate_item_similarity` (simetrija,
dijagonala 1, session-length normalizacija), `recommend_from_item_similarity`
(**target exclusion**, sortiranje, **unknown\_product fallback**,
**no\_interactions fallback**, lazy sličnost), `recommend_session_cooccurrence`
(heuristika, fallback), `compare_heuristic_vs_cf`, `weight_sensitivity_experiment`
(različite težine → različit izlaz), API (collaborative 200/422, cold-start
fallback 200, comparison).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 6/examples/demo_collaborative.py"`
   — matrica, CF preporuke, cold-start fallback, heuristic-vs-CF i
   weight-sensitivity tabela.
2. Pokreni toy SGD: `dm-ml/.venv/bin/python "Day 6/examples/toy_sgd.py"`
   — RMSE kroz epohe; zameni `TOY_MATRIX` svojom matricom.
3. Pokreni MF ekstenziju: `dm-ml/.venv/bin/python "Day 6/examples/mf_library.py"`
   — `implicit` ALS (slični proizvodi iz faktora) + `surprise` SVD (predikcija
   ocene). Uporedi ALS top-5 sa item-item kosinus top-5.
4. Pokreni vizualizaciju: `dm-ml/.venv/bin/python "Day 6/examples/visualize_weights.py"`
   — `weight_sensitivity.png` + `item_similarity_heatmap.png`.
5. Pusti servis pa pitaj `GET /recommendations/collaborative/1?limit=5` —
   uporedi sa `/recommendations/content/1` i `/recommendations/popular`.
6. Pokreni lab (`Day 6/lab/`) — ponovo implementiraj `build_interaction_matrix`
   / `calculate_item_similarity` / `recommend_similar` na malim podacima i
   proveri `test_lab.py`.

## Comparison (baseline ugao)

**Existing heuristic vs CF** (top-5, seeded):

| Target | Heuristic top-5 | CF top-5 | overlap |
| --- | --- | --- | --- |
| 1 (Smartphone Compact 686) | 12, 2, 9, 6, 17 | 12, 2, 9, 6, 20 | `[12, 2, 9, 6]` |
| 2 (Smartphone Compact 854) | 12, 9, 231, 6, 17 | 12, 9, 17, 6, 7 | `[12, 9, 17, 6]` |
| 23 (Jacket Essential 819) | 41, 30, 37, 110, 36 | 41, 30, 36, 40, 37 | `[41, 30, 36, 37]` |
| 144 (Toy Train Pro 565) | 127, 133, 137, 140, 49 | 127, 140, 137, 136, 132 | `[127, 140, 137]` |
| 232 (Cordless Drill Classic 499) | 243, 234, 249, 247, 200 | 243, 247, 236, 249, 234 | `[243, 247, 249, 234]` |

**Distribucija preko svih 252 proizvoda** (top-5):

* **heuristic ∩ CF:** mean **3.73** / 5, median **4**; **nijedan proizvod nema nula
  poklapanja**. Na ovom seed-u (jaka kategorijska afinitetnost sesija) heuristika i CF
  se slažu u ~4 od top-5 — razlika je uglavnom u repu liste (npr. 231/110/200 u
  heuristici su popularni proizvodi iz drugih kategorija koje sirov count „vuče" gore).
* Šta se vidi: **normalizacija menja izlaz.** Heuristika daje sirov
  `count × weight` (duge sesije i popularni proizvodi dominiraju); CF
  normalizuje sesije i item vektore. Razlika nije „bag" — to je razlika između
  sirovog co-occurrence-a i normalizovane sličnosti.

**Weight sensitivity** (težine = pretpostavke) — `top-5` po šemi težina:

| Target | view=1 cart=3 buy=5 | all equal (co-occurrence) | purchase dominates | purchases only |
| --- | --- | --- | --- | --- |
| 1 | `12, 2, 9, 6, 20` | `12, 2, 9, 6, 17` | `12, 2, 9, 6, 20` | `199, 7, 20, 17, 127` |
| 23 | `41, 30, 36, 40, 37` | `41, 30, 36, 37, 40` | `41, 30, 36, 37, 40` | `1, 2, 3, 4, 5` |
| 232 | `243, 247, 236, 249, 234` | `243, 247, 236, 249, 234` | `243, 247, 236, 234, 249` | `240, 203, 234, 1, 2` |

Kod **„purchases only"** (0/0/1) signal skoro nestaje: samo **131** sesija ima ≥ 2
kupljena proizvoda (korpe), pa proizvod 23 nema nijednu ko-kupovinu (svih 5 skorova je 0
→ redosled `1..5` je tie-break po `product_id`, NIJE popularnost), a 232 ima samo 3
nenulta skora (`1, 2` na kraju su opet tie-break). To je dokaz: **težine su hipoteza**,
ne istina. „all equal" i „purchase dominates" često daju isti skup (samo drugi
redosled) — jer na ovom seed-u pregledi i korpe prate kupovine; na pravom
store-u to ne mora da važi.

## Evaluacija (kako znamo da je dobro)

* **Target exclusion je ugovor:** CF ne vraća sam proizvod (test).
* **Cold-start fallback je definisan:** nepoznat proizvod -> 200 sa
  `method="fallback"`, `fallback_reason="unknown_product"`; proizvod sa nula
  interakcija -> `no_interactions`; nema tihog `[]` (test).
* **Sparsity je stvarna:** matrica je `csr_matrix` (nnz ≪ red×kolona); nema
  dense blowup-a (test `sparse_not_dense` / `density < 1`).
* **Agregacija nije „count as rating":** max-težina (purchase dominira), ne
  zbir; `sum` je dokumentovan kao varijanta-vežba (test).
* **Determinizam:** isti događaji + iste težine -> ista matrica i sličnost
  (tie-break po `product_id`); `interactions.csv` byte-for-byte (sha256 u
  `metadata.json`).
* **Baseline comparison je dokumentovan:** README tabela + distribucija
  overlap-a preko svih proizvoda (heuristic ∩ CF mean 3.73/5, 0 nula).
* **Toy SGD reprodukuje matricu:** finalni RMSE < 1.0 (assert u `toy_sgd.py`).

## Česti bugovi

* **Brojanje interakcija kao ocene** — proizvod gledan 5 puta ≠ 5. Rešenje:
  max-agregacija (prisustvo), ne zbir (test).
* **Nema session-length normalizacije** — dugačke sesije lažno „spajaju" sve
  proizvode. Rešenje: L2-normalizacija redova pre sličnosti (vežba).
* **Dense matrica na sparse podacima** — 15 360 × 252 gusta matrica je ~31 MB (float64).
  Rešenje: uvek `csr_matrix`.
* **Hardkodovanje težina kao odgovora** — view=1/cart=3/purchase=5 su baseline
  pretpostavke, ne istina. Rešenje: weight-sensitivity eksperiment.
* **Tihi `[]` na grešku** — nov proizvod / proizvod bez interakcija mora da
  vrati *nešto* objašnjeno (popularity fallback sa `fallback_reason`).
* **Mešanje heuristike i CF-a** — heuristika (sirov co-occurrence) je baseline;
  CF (normalizovana sličnost) je metoda. Poređenje je obavezno, ne zamena.

## Šta rezultat NE dokazuje

* **Ko-interakcija nije preferencija.** Item-item CF kaže „ovi proizvodi se
  pojavljuju zajedno u sesijama" — ne kaže „korisnik će ga voleti". Da bi se to
  znalo, treba Day 7 (evaluacija).
* **Sličnost nije kvalitet.** Visok skor znači „sesije ih vide slično", ne „ovaj
  proizvod je dobar".
* **Težine nisu istina.** Promena težina menja izlaz — težine su pretpostavke
  koje podaci treba da smeju da obore. „Purchases only" za mnoge proizvode daje
  nula-sličnosti (tie-break po ID-u) — signal je nestao, nije „drugačiji“.
* **CF ne rešava cold start.** Proizvod bez interakcija nema vektor — fallback
  je popularity, ne „prava" preporuka. (Day 8/10 hibridi to adresiraju.)
* **Heuristic vs CF nije takmičenje „ko je bolji"** — to je evaluacija da li
  normalizacija menja izlaz. Na sintetičkom seed-u (42) oba imaju iste
  slabosti; na pravom store-u podaci odlučuju.
* **Brojevi važe za sintetički seed (42).** Na pravom store-u raspodela sesija i
  događaja je drugačija — pipeline ostaje, brojevi se menjaju.
* **MF nije čarolija.** Toy SGD i `implicit` ALS uče faktore koji minimizuju
  rekonstrukciju — to su još uvek pretpostavke o tome šta „slično" znači.

## Vežbe

1. **Target exclusion** — ukloni isključivanje u `recommend_from_item_similarity`
   i pokreni test (`test_collaborative.py::TestRecommendFromItemSimilarity`):
   proizvod se vraća sam sebi. Vrati i potvrdi da test prolazi.
2. **Cold-start fallback** — pitaj `GET /recommendations/collaborative/99999` i
   potvrdi `method="fallback"`, `fallback_reason="unknown_product"`; proveri da
   NIJE prazan rezultat.
3. **Promeni težine interakcija** — napravi sopstvenu šemu (npr. view=1,
   cart=2, purchase=8) i uporedi top-5 za proizvod 1 preko
   `svc.weight_sensitivity(1)` (ili API-ja). Šta se menja? Zašto?
4. **Session-length normalization** — pokreni `calculate_item_similarity` sa
   `row_normalize=False` i uporedi top-5. Koji proizvodi uđu/ispadnu? (Duge
   sesije dominiraju bez normalizacije.)
5. **Fallback za proizvod bez interakcija** — napravi matricu sa proizvodom koji
   ima nula interakcija (catalog alignment) i potvrdi
   `fallback_reason="no_interactions"` (različito od `unknown_product`).
6. **Toy SGD** — promeni `TOY_MATRIX` u `toy_sgd.py` (dodaj red/kolonu), povećaj
   `k` ili `n_epochs` i gledaj kako RMSE i rekonstrukcija reaguju.
7. **MF ekstenzija** — instaliraj `scikit-surprise` + `implicit`, pokreni
   `mf_library.py` i uporedi ALS top-5 sa item-item kosinus top-5 za isti
   proizvod.

## Sažetak

Od sirove session-co-occurrence heuristike napravio si **implicit-feedback
collaborative recommender**: interaction matrica (sesije × proizvodi, max-težina,
sparse), item-item kosinusna sličnost (sa session-length normalizacijom), target
exclusion kao ugovor, i **cold-start fallback** na popularity (nikad tihi `[]`).
Postojeća heuristika je ostala kao **baseline** za poređenje (heuristic ∩ CF
mean 3.73/5 — normalizacija menja rep liste), a **weight-sensitivity** pokazuje da su
težine događaja **pretpostavke**, ne istine. Centralna lekcija: **ko-interakcija
≠ preferencija** — CF kaže šta izgleda kao ko-interagovano, ne šta će korisnik
voleti; zato Day 7 (evaluacija) meri da li preporuke zaista pomažu. Pitanje
danas: **kada je co-occurrence signal dovoljan, a kada treba i stvarna evaluacija
da bi se znalo da li preporuke rade?**

---

<!-- page_id 423 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/metadata.json

```
{
  "dataset": "dm_interaction_matrix_v1",
  "description": "Seeded implicit-feedback interaction matrix (sessions x products) built from Day 1 events. Value = aggregated event weight per (session, product) using aggregation='max' and weights view=1 / add_to_cart=3 / purchase=5. These weights are ASSUMPTIONS, not truths — weight-sensitivity experiment tests them (DAY-BRIEFS Day 6).",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "products": "Day 1/data/products.csv",
    "module": "app.data.generate_interactions",
    "function": "generate_interactions",
    "matrix_builder": "app.recommenders.collaborative.build_interaction_matrix"
  },
  "parameters": {
    "aggregation": "max",
    "level": "session",
    "weights": {
      "product_view": 1.0,
      "add_to_cart": 3.0,
      "purchase": 5.0
    }
  },
  "columns": [
    "session_id",
    "product_id",
    "value"
  ],
  "counts": {
    "sessions": 15360,
    "products_total": 252,
    "products_with_interactions": 252,
    "nnz": 90761,
    "density": 0.023448,
    "total_value": 99163.0,
    "top_by_value": [
      90,
      184,
      110,
      12,
      49
    ],
    "sessions_with_2_plus_products": 13763
  },
  "fields": {
    "session_id": "str, user_session (Day 1 kolona) — red interaction matrice",
    "product_id": "int, stabilan ID proizvoda (kolona matrice)",
    "value": "float, agregirana težina interakcije za (sesija, proizvod) — aggregation=max nad težinama događaja {'product_view': 1.0, 'add_to_cart': 3.0, 'purchase': 5.0}"
  },
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "interactions.csv": "f48740190a325fbfeda071fa2ef6b5f60324e7a164031816edd31aefc5c3297e"
    }
  }
}
```

### data/README.md

# Day 6 podaci — implicitna interaction matrica (izvedena tabela)

Deterministička, **byte-for-byte reproduktivna** tabela **izvedena** iz Day 1
seeded događaja (ne duplira ih). Kompletna dokumentacija (izvor, parametri,
značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `interactions.csv` | long format: `session_id`, `product_id`, `value` (nenulte interakcije, sortirano) | 90 761 |
| `metadata.json` | izvor, težine, agregacija, counts, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (jedini izvor istine) + `Day 1/data/products.csv`
  (katalog za poravnanje kolona).
* Matrica: `build_interaction_matrix` (`app/recommenders/collaborative.py`) —
  sesije × proizvodi, agregacija **max** nad težinama događaja
  (`product_view`=1, `add_to_cart`=3, `purchase`=5). Težine su **pretpostavke,
  ne istine** (weight-sensitivity ih testira).
* Generator: `app/data/generate_interactions.py` (upisuje CSV + metadata).

## Ključne kolone (`interactions.csv`)

| Kolona | Značenje |
| --- | --- |
| `session_id` | `user_session` (Day 1) — red interaction matrice |
| `product_id` | FK -> `products.product_id` — kolona matrice |
| `value` | agregirana težina interakcije za (sesija, proizvod) — `max` |

## Stanje u ovom seed-u

* sesija: **15 360** · proizvoda (kolone): **252** · sa interakcijama: **252**
* nenultih ćelija: **90 761** · gustina: **0.0234** (≈ 97.7 % prazno — sparsity)
* sesija sa ≥ 2 različita proizvoda: **13 763** (co-occurrence signal)
* top-5 po vrednosti interakcija: **90, 184, 110, 12, 49**

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_interactions
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

`value` je **agregirana težina prisustva**, ne ocena niti „koliko korisnik voli".
Ista `value` može da znači „gledao 1 put" ili „kupio 1 put" — težine su izbor
(pretpostavka). Matrica pokazuje *ko-interakcije*, ne preferencije; da li će ih
korisnik voleti je pitanje za Day 7 (evaluacija).

### examples/demo\_collaborative.py

```
"""Demo: collaborative recommender (implicit feedback, Day 6).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/demo_collaborative.py"

Prikazuje:
  1) interaction matricu (sesije × proizvodi, sparsity) iz ``Day 6/data``;
  2) **collaborative preporuke** (item-item kosinusna sličnost) za nekoliko
     proizvoda;
  3) **cold-start fallback** — nov proizvod (bez interakcija) -> popularity
     baseline sa ``fallback=true``, ne tihi ``[]``;
  4) **existing-heuristic-vs-CF poređenje** (session co-occurrence vs item-item)
     — overlap tabela koju README citira;
  5) **weight-sensitivity** — iste težine su pretpostavke: promena šeme težina
     menja izlaz.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.collaborative import CollaborativeRecommenderService

EXAMPLES = [1, 2, 23, 144, 232]


def _ids(envelope: dict) -> str:
    return ",".join(str(r["product_id"]) for r in envelope["recommendations"])


def main() -> None:
    print("=== Day 6 — Collaborative Recommender (implicit feedback) ===\n")
    svc = CollaborativeRecommenderService()

    stats = svc.matrix_stats
    print(f"[0] Interaction matrica: {stats['sessions']} sesija × "
          f"{stats['products']} proizvoda, nnz={stats['nnz']}, "
          f"density={stats['density']:.5f} (sparse — nema dense blowup-a)")
    print()

    # --- 1) Collaborative preporuke ---------------------------------------- #
    print("[1] Collaborative preporuke (item-item kosinusna sličnost):")
    pid = 1
    res = svc.collaborative_recommendations(pid, 5)
    print(f"    /recommendations/collaborative/{pid}: method={res['method']} "
          f"fallback={res['fallback']}")
    for r in res["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} score={r['score']:.4f}")
    ids = [r["product_id"] for r in res["recommendations"]]
    print(f"    target {pid} isključen: {pid not in ids}")
    print()

    # --- 2) Cold-start fallback -------------------------------------------- #
    print("[2] Cold-start fallback (nov proizvod bez interakcija):")
    cs = svc.collaborative_recommendations(99999, 5)
    print(f"    /recommendations/collaborative/99999: method={cs['method']} "
          f"fallback={cs['fallback']} reason={cs['fallback_reason']}")
    print(f"    -> popularity baseline, {cs['returned']} preporuka (NIKAD tihi [])")
    print()

    # --- 3) Existing heuristic vs CF ---------------------------------------- #
    print("[3] Existing heuristic vs CF (top-5, overlap):")
    print(f"    {'target':>6} {'heuristic top-5':<30} {'CF top-5':<30} {'overlap':<12}")
    for pid in EXAMPLES:
        comp = svc.collaborative_comparison(pid, 5)
        h = _ids(comp["heuristic"])
        c = _ids(comp["collaborative"])
        ov = ",".join(str(x) for x in comp["overlap"]) or "—"
        print(f"    {pid:>6} {h:<30} {c:<30} {ov:<12}")
    print()

    # --- 4) Weight sensitivity ---------------------------------------------- #
    print("[4] Weight sensitivity (težine = pretpostavke, ne istine):")
    ws = svc.weight_sensitivity(1, limit=5)
    print(f"    target 1, limit={ws['limit']}:")
    print(f"    {'weight set':<32} {'top-5':<24} {'overlap w/ default':>18}")
    for row in ws["rows"]:
        top = ",".join(str(x) for x in row["top_ids"])
        ov = row["overlap_with_default"]
        print(f"    {row['name']:<32} {top:<24} {ov!s:>18}")
    print()
    print("Promena težina menja izlaz -> težine nisu istina o kvalitetu, "
          "nego hipoteza.")
    print("Vizualizacija: python3 \"Day 6/examples/visualize_weights.py\"")


if __name__ == "__main__":
    main()
```

### examples/mf\_library.py

```
"""MF extension: matrix factorization preko biblioteka (Day 6).

Toy SGD (``toy_sgd.py``) pokazuje mehanizam iz osnova; ovo je **library-level
ekstenzija** — isti koncept kroz dve biblioteke:

  1. ``implicit`` — **Alternating Least Squares (ALS)** za implicitni feedback
     (naš slučaj: interaction matrica sesije × proizvodi). Faktorizuje matricu i
     nudi ``similar_items`` iz naučenih faktora proizvoda.
  2. ``surprise`` — **SVD** za eksplicitne ocene (toy primer 1–5) i predikcija
     nepoznate ocene.

Obe biblioteke su **opcione** (Day 6 ekstenzija): instaliraj ih sa
``pip install scikit-surprise implicit`` (dodate su u ``dm-ml/requirements.txt``).
Ako nisu instalirane, skripta prijavljuje jasnu poruku i izlazi — ne pada.

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/mf_library.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import numpy as np

from app.recommenders.collaborative import InteractionMatrix

DEFAULT_INTERACTIONS = (
    Path(__file__).resolve().parents[2] / "Day 6" / "data" / "interactions.csv"
)
TARGET_PRODUCT = 1


def load_user_item_matrix(path: Path = DEFAULT_INTERACTIONS):
    """Long-format interaction matrica -> ``(user_item_matrix, products)``.

    ALS iz ``implicit`` očekuje **users × items** CSR matricu (red = korisnik/
    sesija, kolona = proizvod) — to je tačno ``inter.matrix``. Vraća i
    ``products`` listu za mapiranje indeksa kolona.
    """
    inter = InteractionMatrix.from_long_csv(path)
    return inter.matrix, inter.products


def implicit_als_similar_items(n_similar: int = 5) -> None:
    """ALS (implicit feedback) -> top-N sličnih proizvoda za target."""
    try:
        import implicit
    except ImportError:
        print("implicit nije instaliran — pokreni: "
              "dm-ml/.venv/bin/pip install implicit")
        return

    print("[1] implicit ALS (implicit feedback) — na Day 6 interaction matrici")
    user_item, products = load_user_item_matrix()
    print(f"    matrica: {user_item.shape[0]} sesija × {user_item.shape[1]} proizvoda")

    model = implicit.als.AlternatingLeastSquares(
        factors=20, iterations=15, regularization=0.1, random_state=42
    )
    model.fit(user_item, show_progress=False)

    if TARGET_PRODUCT not in products:
        print(f"    target {TARGET_PRODUCT} nije u matrici")
        return
    item_idx = products.index(TARGET_PRODUCT)
    ids, scores = model.similar_items(item_idx, N=n_similar + 1)
    print(f"    top-{n_similar} sličnih proizvoda za {TARGET_PRODUCT} "
          f"(iz naučenih faktora):")
    for idx, score in zip(ids[1:], scores[1:]):  # ids[0] je sam proizvod
        print(f"      {products[idx]:>3}  similarity={score:.4f}")
    print()


def surprise_svd_explicit_toy() -> None:
    """SVD (explicit ratings) na toy primeru -> predikcija nepoznate ocene."""
    try:
        from surprise import Dataset, Reader, SVD
    except ImportError:
        print("scikit-surprise nije instaliran — pokreni: "
              "dm-ml/.venv/bin/pip install scikit-surprise")
        return

    print("[2] surprise SVD (explicit ratings) — toy primer")
    # 3 korisnika × 4 proizvoda, ocene 1–5; zadnja ćelija je „nepoznata" (0).
    rows = [
        ("u1", "p1", 5), ("u1", "p2", 4), ("u1", "p3", 2),
        ("u2", "p1", 4), ("u2", "p2", 5), ("u2", "p4", 1),
        ("u3", "p1", 1), ("u3", "p3", 5), ("u3", "p4", 4),
    ]
    import pandas as pd

    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(pd.DataFrame(rows, columns=["user", "item", "rating"]), reader)
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=3, random_state=42)
    algo.fit(trainset)

    # Nepoznata ćelija: korisnik u1, proizvod p4 — koliko bi ocenio?
    pred = algo.predict("u1", "p4").est
    print(f"    predikcija ocene u1->p4 (nepoznata ćelija): {pred:.2f} (skala 1–5)")
    print()


def main() -> None:
    print("=== Day 6 — MF extension (surprise / implicit) ===\n")
    implicit_als_similar_items()
    surprise_svd_explicit_toy()
    print("Gotovo.")


if __name__ == "__main__":
    main()
```

### examples/toy\_sgd.py

```
"""Toy SGD: matrix factorization iz osnova (Day 6 vežba).

SGD (stohastički gradijentni spust) na **toy matrici** — mala implicitna
matrica interakcija (5 korisnika × 4 proizvoda). Cilj: naučiti faktorizaciju
``R ≈ P @ Q.T`` (P = korisnički faktori, Q = proizvod faktori, ``k`` latentnih
domena) minimizovanjem greške rekonstrukcije na **posmatranim** ćelijama uz L2
regularizaciju.

Ovo je *prvi korak* ka matrix factorization (MF): isti SGD mehanizam koriste
``surprise``/``implicit`` biblioteke (vidi ``mf_library.py``). Poenta vežbe:

  - razumeš gradijentni korak ``P[u] += lr * (err * Q[i] - reg * P[u])``;
  - vidiš da se RMSE smanjuje kroz epohe;
  - proveriš da naučeni faktori **reprodukuju toy matricu** (rekonstrukcija ≈
    original) — to je acceptance za ovaj fajl.

Pokretanje (koristi dm-ml venv — treba samo numpy):

    dm-ml/.venv/bin/python "Day 6/examples/toy_sgd.py"

Zameni ``TOY_MATRIX`` svojom malom matricom i ponovo pokreni.
"""

from __future__ import annotations

import numpy as np

# Toy implicitna matrica: red = korisnik, kolona = proizvod, 0 = nema interakcije.
TOY_MATRIX = np.array(
    [
        [5, 3, 0, 1],
        [4, 0, 0, 1],
        [1, 1, 0, 5],
        [1, 0, 0, 4],
        [0, 1, 5, 4],
    ],
    dtype=float,
)

N_LATENT = 2  # broj latentnih faktora (k)
LR = 0.02     # stopa učenja
REG = 0.1     # L2 regularizacija
N_EPOCHS = 200
SEED = 42


def sgd_matrix_factorization(
    R: np.ndarray,
    k: int = N_LATENT,
    lr: float = LR,
    reg: float = REG,
    n_epochs: int = N_EPOCHS,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """SGD faktorizacija ``R ≈ P @ Q.T`` na posmatranim ćelijama.

    Vraća ``(P, Q, rmse_history)`` — P (n_users×k), Q (n_items×k) i RMSE po
    epohi nad posmatranim ćelijama. Svaka iteracija uzima jednu posmatranu
    ćeliju, računa grešku i koriguje odgovarajuće redove P i Q (gradijentni
    spust + regularizacija).
    """
    rng = np.random.default_rng(seed)
    n_users, n_items = R.shape
    P = rng.normal(scale=0.1, size=(n_users, k))
    Q = rng.normal(scale=0.1, size=(n_items, k))
    rows, cols = np.nonzero(R)
    history: list[float] = []

    for _ in range(n_epochs):
        for u, i in zip(rows, cols):
            r_ui = R[u, i]
            err = r_ui - float(P[u] @ Q[i])
            # Gradijentni koraci: učiš i korisnički i proizvod vektor.
            P[u] += lr * (err * Q[i] - reg * P[u])
            Q[i] += lr * (err * P[u] - reg * Q[i])
        history.append(rmse(R, P, Q))

    return P, Q, history


def rmse(R: np.ndarray, P: np.ndarray, Q: np.ndarray) -> float:
    """RMSE nad posmatranim ćelijama (``R > 0``)."""
    mask = R > 0
    recon = P @ Q.T
    return float(np.sqrt(((R[mask] - recon[mask]) ** 2).mean()))


def main() -> None:
    print("=== Day 6 — Toy SGD matrix factorization ===")
    print(f"Toy matrica ({TOY_MATRIX.shape[0]} korisnika × {TOY_MATRIX.shape[1]} proizvoda):")
    print(TOY_MATRIX)
    print(f"k={N_LATENT}, lr={LR}, reg={REG}, epochs={N_EPOCHS}, seed={SEED}")
    print()

    P, Q, history = sgd_matrix_factorization(TOY_MATRIX)

    print("RMSE kroz epohe (svakih 50):")
    for epoch in range(0, N_EPOCHS, 50):
        print(f"  epoch {epoch:>3}: rmse={history[epoch]:.4f}")
    print(f"  final: rmse={history[-1]:.4f}")
    print()

    recon = P @ Q.T
    print("Rekonstrukcija (P @ Q.T):")
    print(np.round(recon, 2))
    print()

    # Acceptance: naučeni faktori reprodukuju toy matricu (mala finalna greška).
    assert history[-1] < 1.0, (
        f"toy SGD nije konvergirao: finalni RMSE {history[-1]:.4f} — "
        "povećaj n_epochs ili podesi lr/reg"
    )
    print(f"OK: finalni RMSE {history[-1]:.4f} < 1.0 — faktori reprodukuju toy matricu.")

    print("\nNaučeni faktori:")
    print("P (korisnici):")
    print(np.round(P, 3))
    print("Q (proizvodi):")
    print(np.round(Q, 3))
    print("\nGotovo.")


if __name__ == "__main__":
    main()
```

### examples/visualize\_weights.py

```
"""Vizualizacija collaborative preporuka (Day 6, supporting material).

Dve slike u ``Day 6/examples/``:

    - ``weight_sensitivity.png`` — za target proizvod, koliko se top-5 preporuka
      poklapa sa default šemom težina po različitim šemama. Mali overlap =
      težine menjaju izlaz = težine su pretpostavke, ne istine.
    - ``item_similarity_heatmap.png`` — item-item kosinusna sličnost za uzorak
      proizvoda (24 iz više kategorija): blokovi po kategoriji (proizvodi koje
      iste sesije gledaju zajedno) + dijagonalni parovi.

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/visualize_weights.py"

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

from app.recommenders.collaborative import calculate_item_similarity
from app.services.collaborative import CollaborativeRecommenderService

OUT_DIR = Path(__file__).resolve().parent
TARGET = 1
SAMPLE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
              22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]


def weight_sensitivity_plot(svc: CollaborativeRecommenderService) -> None:
    """Bars: overlap sa default šemom po šemi težina za target."""
    ws = svc.weight_sensitivity(TARGET, limit=5)
    rows = ws["rows"]
    names = [r["name"] for r in rows]
    overlaps = [r["overlap_with_default"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(range(len(names)), overlaps, color="#3b82f6")
    for i, (bar, r) in enumerate(zip(bars, rows)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"top: {r['top_ids'][0]}", ha="center", fontsize=8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=7, rotation=18, ha="right")
    ax.set_ylabel("overlap sa default težinama (od top-5)")
    ax.set_ylim(0, 5.5)
    ax.set_title(f"Weight sensitivity — target {TARGET} (težine su pretpostavke)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "weight_sensitivity.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'weight_sensitivity.png'}")


def item_similarity_heatmap(svc: CollaborativeRecommenderService) -> None:
    """Heatmap item-item kosinusne sličnosti za uzorak proizvoda."""
    inter = svc._interaction()
    products = svc.products
    sample = products[products["product_id"].isin(SAMPLE_IDS)].sort_values("product_id")
    sample_ids = sorted(int(x) for x in sample["product_id"])
    idx = [inter.products.index(p) for p in sample_ids]
    sim = calculate_item_similarity(inter)
    sub = sim[np.ix_(idx, idx)].toarray()

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(sub, cmap="viridis", vmin=0, vmax=1)
    labels = [f"{p}:{products.loc[products['product_id']==p, 'name'].iloc[0].split()[0][:8]}" for p in sample_ids]
    ax.set_xticks(range(len(sample_ids)))
    ax.set_yticks(range(len(sample_ids)))
    ax.set_xticklabels(labels, fontsize=5.5, rotation=90)
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_title("Item-item kosinusna sličnost (implicit feedback)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "item_similarity_heatmap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'item_similarity_heatmap.png'}")


def main() -> None:
    print("=== Day 6 — collaborative recommender vizualizacija ===")
    svc = CollaborativeRecommenderService()
    weight_sensitivity_plot(svc)
    item_similarity_heatmap(svc)
    print("Gotovo.")


if __name__ == "__main__":
    main()
```

### lab/README.md

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

### lab/starter.py

```
"""Starter za Day 6 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 6/lab/``, koristi dm-ml venv — ima sklearn):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

# Kolone koje sve preporuke vraćaju (product_info + score).
RECOMMENDATION_COLUMNS = [
    "product_id", "name", "slug", "description", "img_url",
    "category_id", "price", "score",
]

# Težine događaja (pretpostavke, ne istine — vidi Day 6 README).
EVENT_WEIGHTS = {
    "product_view": 1.0,
    "add_to_cart": 3.0,
    "purchase": 5.0,
}


def build_interaction_matrix(events_df: pd.DataFrame) -> tuple:
    """Implicitna interaction matrica (sesije × proizvodi). TODO: implementirati.

    Zahtevi:
    - Uzmi samo događaje čiji je ``event_type`` u ``EVENT_WEIGHTS`` i koji imaju
      ``user_session`` i ``product_id``.
    - Vrednost ćelije (sesija, proizvod) = **najveća** težina događaja u toj
      sesiji za taj proizvod (max-agregacija — NE zbir; brojanje interakcija kao
      ocenu je čest bag).
    - Redovi = sortirane sesije, kolone = sortirani proizvodi.
    - Vrati ``(matrix, sessions, products)`` gde je ``matrix`` ``csr_matrix``
      (sparse), ``sessions`` lista stringova, ``products`` lista int-ova.
    """
    raise NotImplementedError("implementiraj build_interaction_matrix")


def calculate_item_similarity(matrix) -> np.ndarray:
    """Item-item kosinusna sličnost. TODO: implementirati.

    Zahtevi: item vektori su **kolone** matrice (sesije × proizvodi), pa je
    ``cosine_similarity(matrix.T)`` matrica ``n_proizvoda × n_proizvoda``.
    Vrati je kao **gusti** ``np.ndarray``.
    """
    raise NotImplementedError("implementiraj calculate_item_similarity")


def recommend_similar(
    products_df: pd.DataFrame,
    product_id: int,
    matrix,
    products: list,
    limit: int = 5,
) -> pd.DataFrame:
    """Collaborative preporuke po item-item sličnosti, BEZ targeta. TODO: implementirati.

    Zahtevi:
    - Ako ``product_id`` NIJE u ``products`` (cold start / nov proizvod) ->
      fallback: vrati ``recommend_popular(products_df, limit)`` (baseline —
      nikad prazan rezultat bez objašnjenja).
    - Inače: izračunaj sličnosti (``calculate_item_similarity``), uzmi red
      targeta, ISKLJUČI target iz kandidata, sortiraj opadajuće po ``score``
      (tie-break ``product_id``) i vrati top-``limit`` sa
      ``RECOMMENDATION_COLUMNS`` (``score`` = kosinusna sličnost).
    """
    raise NotImplementedError("implementiraj recommend_similar")


def recommend_popular(products_df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Popularity baseline (za fallback). TODO: implementirati.

    Zahtevi: ``products_df`` ima kolonu ``popularity``; sortiraj opadajuće
    (tie-break po ``product_id`` rastuće), uzmi prvih ``limit``, vrati
    ``RECOMMENDATION_COLUMNS`` gde je ``score`` = ``popularity``.
    """
    raise NotImplementedError("implementiraj recommend_popular")
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
import pandas as pd

EV = pd.DataFrame({"user_session": ["s1", "s1", "s1", "s2", "s2", "s3"],
                   "product_id": [1, 1, 2, 1, 3, 2],
                   "event_type": ["product_view", "add_to_cart", "product_view", "purchase", "product_view", "search"]})
PR = pd.DataFrame({"product_id": [1, 2, 3, 4], "name": list("abcd"), "category_id": [1, 1, 2, 2],
                   "popularity": [5.0, 9.0, 1.0, 9.0]})


def test_matrix_max_aggregation():
    m, s, p = lab.build_interaction_matrix(EV)
    assert s == ["s1", "s2"] and p == [1, 2, 3]          # search bez težine je izbačen
    d = m.toarray()
    assert d[0, 0] == 3.0                                 # max(1, 3), ne 4
    assert d[1, 0] == 5.0 and d[1, 2] == 1.0
    assert hasattr(m, "tocsr")


def test_similarity_dense_square():
    m, _, p = lab.build_interaction_matrix(EV)
    sim = lab.calculate_item_similarity(m)
    assert isinstance(sim, np.ndarray) and sim.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)


def test_recommend_similar_and_cold_start():
    m, _, p = lab.build_interaction_matrix(EV)
    r = lab.recommend_similar(PR, 1, m, p, 5)
    assert 1 not in set(r["product_id"]) and list(r.columns) == lab.RECOMMENDATION_COLUMNS
    cold = lab.recommend_similar(PR, 99, m, p, 2)
    assert list(cold["product_id"]) == [2, 4]            # popularity, tie-break po product_id
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 6 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from starter import EVENT_WEIGHTS, RECOMMENDATION_COLUMNS  # noqa: F401


def build_interaction_matrix(events_df):
    ev = events_df[events_df["event_type"].isin(EVENT_WEIGHTS)].dropna(subset=["user_session", "product_id"])
    ev = ev.assign(_w=ev["event_type"].map(EVENT_WEIGHTS).astype(float), product_id=ev["product_id"].astype(int))
    agg = ev.groupby(["user_session", "product_id"])["_w"].max().reset_index()  # MAX, ne zbir
    sessions = sorted(agg["user_session"].astype(str).unique()); products = sorted(int(p) for p in agg["product_id"].unique())
    si = {s: i for i, s in enumerate(sessions)}; pi = {p: i for i, p in enumerate(products)}
    m = csr_matrix((agg["_w"], (agg["user_session"].astype(str).map(si), agg["product_id"].map(pi))),
                   shape=(len(sessions), len(products)))
    return m, sessions, products


def calculate_item_similarity(matrix):
    return np.asarray(cosine_similarity(matrix.T))


def _out(df, score):
    df = df.copy(); df["score"] = list(score)
    for c in RECOMMENDATION_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[RECOMMENDATION_COLUMNS].reset_index(drop=True)


def recommend_popular(products_df, limit=5):
    d = products_df.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def recommend_similar(products_df, product_id, matrix, products, limit=5):
    if product_id not in products:
        return recommend_popular(products_df, limit)
    row = calculate_item_similarity(matrix)[products.index(product_id)]
    s = pd.Series(row, index=products).drop(product_id)
    d = products_df.assign(_s=products_df["product_id"].map(s)).dropna(subset=["_s"])
    d = d.sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["_s"])
```
