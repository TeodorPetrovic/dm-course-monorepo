# Dan 7 — Recommendation Evaluation Framework

- lesson_id: 117
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:47.136 updated: 2026-09-05 20:00:29.474
- summary: „Ova preporuka izgleda dobro" nije evaluacija. P@K, R@K, HR@K, NDCG@K i coverage porede što je preporučeno sa šta je sesija stvarno radila kasnije — a temporalni split (ne random) sprečava budućnost da procuri u treniranje. Bolji P@5 na ovom skupu ne dokazuje da je preporučivač bolji u pravom store-u: metrika je sočivo, ne presuda. Preporučivač može da ima dobar P@5 a da bude beskoristan (npr. uvek najpopularniji — coverage to hvata). [subjects-import]


---

<!-- page_id 424 order 0 -->
## [Page] Materijal

# Dan 7 — Recommendation Evaluation Framework

> *„Ova preporuka izgleda dobro" nije evaluacija. P@K, R@K, HR@K, NDCG@K i
> coverage porede što je preporučeno sa šta je sesija stvarno radila kasnije —
> a temporalni split (ne random) sprečava budućnost da procuri u treniranje.
> Bolji P@5 na ovom skupu ne dokazuje da je preporučivač bolji u pravom
> store-u: metrika je sočivo, ne presuda. Preporučivač može da ima dobar P@5 a
> da bude beskoristan (npr. uvek najpopularniji — coverage to hvata).*

## Šta gradimo

Reusable **evaluation modul** (`app/recommenders/evaluation.py`): ranking
metrike (**P@K, R@K, HR@K, NDCG@K**), **catalog coverage**, **temporal
train/test split** (podela po vremenu — NE random), session-based evaluacioni
protokol i **comparison report** preko svih preporučivača izgrađenih do sada —
popularity/category **baseline-i** (Day 5) i content/collaborative **ML**
(Day 5/6). Izloženo kroz `GET /analytics/recommendations` i integrisano u CMS
kao analytics report stranica.

Do sada smo *gradili* preporučivače i govorili „ovo izgleda razumno". Danas
postavljamo pitanje: **kako da znamo da su preporuke zaista dobre?** Odgovor je
evaluacija — objektivne, reproducibilne mere koje ne zavise od utiska.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `precision_at_k` / `recall_at_k` / `hit_rate_at_k` / `ndcg_at_k` / `catalog_coverage` | **statistical / metric** (matematika, bez ML-a) |
| `temporal_split` | **data preprocessing** (podela po vremenu — anti-leakage) |
| `extract_test_cases` | **data preprocessing** (sesija → query/targets) |
| `evaluate_recommender` | **statistical / evaluation protocol** |
| `make_popularity_predictor` | **rule / heuristic** (baseline, bez ML-a) |
| `make_category_predictor` | **rule / heuristic** (baseline, bez ML-a) |
| `make_content_predictor` | **machine learning** (TF-IDF + kosinus, Day 5) |
| `make_collaborative_predictor` | **machine learning** (item-item CF, Day 6) |
| `build_comparison_report` | **statistical / report** |

## Application requirement

Admin panel treba da odgovori na pitanje „koji preporučivač da uključimo?".
Day 7 dodaje **analytics report stranicu** (`/admin/recommendations`) koja
poziva `GET /analytics/recommendations` i prikazuje uporednu tabelu
popularity/category/content/collaborative po P@5/R@5/HR@5/NDCG@5/coverage. Bez
toga, odluka o tome koji preporučivač koristiti je *mišljenje*; sa evaluacijom
je (bar delom) *mera*.

## Ciljevi učenja

Do kraja dana treba da:

* implementirate **P@K, R@K, HR@K, NDCG@K** sa edge-case handlingom
  (imenilac, prazne liste, nula relevantnih, `k > |ranked|`) i objasnite šta
  svaka metrika kaže;
* izračunate **catalog coverage** i povežete nizak coverage sa **popularity
  bias-om**;
* napravite **temporal train/test split** (podela po vremenu) i objasnite zašto
  random split procuruje budućnost i lažno povećava metrike;
* izgradite **session-based evaluacioni protokol** (query = prvi proizvod u
  test periodu, targets = kasniji proizvodi iste sesije);
* pokrenete **`evaluate_recommender`** i **`build_comparison_report`** preko
  popularity/category/content/collaborative i protumačite tabelu;
* objasnite zašto **bolja metrika ≠ bolji preporučivač** u pravom store-u
  („What the result does NOT prove").

## Preduslovi

Day 1 događaji (`events.csv` — timestamp kolona), Day 5 katalog
(`products_text.csv`), Day 5 content recommender (TF-IDF + kosinus), Day 6
collaborative recommender (interaction matrica + item-item sličnost),
baseline-i (popularity/category).

## Postojeći sistem (šta nasleđujemo)

* **Day 5:** popularity/category baseline-i, content recommender (TF-IDF +
  kosinus), cold-start fallback na popularity.
* **Day 6:** collaborative recommender (implicit interaction matrica +
  item-item sličnost), session-co-occurrence heuristika kao baseline,
  weight-sensitivity (težine = pretpostavke).
* **Nedostaje:** bilo kakva *objektivna* mera da li preporuke pomažu. Day 5/6
  su donosile „izgleda dobro" zaključke; Day 7 ih zamenjuje merom.
* **Nasleđeni rizik:** `products_text.csv` ima `popularity` kolonu računatu iz
  **cele** istorije — koristiti je u temporalnoj evaluaciji = **leakage**.
  Zato evaluacija uvek računa popularnost iz **train** događaja.

## Arhitektura

```
Day 1 događaji (events.csv)              Day 5 katalog (products_text.csv)
      │                                             │
      ▼                                             ▼
temporal_split (kvantil 0.8, po VREMENU)            │
      │  train (146 774)  test (36 694)            │
      ▼                                             │
make_*_predictor(products, train)                   │
  popularity | category | content | collaborative  │
      │                                             │
      ▼                                             │
extract_test_cases(test)  — sesija → (query, targets)
      │                                             │
      ▼                                             ▼
evaluate_recommender  — za svaki slučaj: recommend(query,k) → P@K,R@K,HR@K,NDCG@K
      │
      ▼
build_comparison_report  — tabela popularity/category/content/collaborative
      │
      ▼
app/services/evaluation.py  →  GET /analytics/recommendations
      │
      ▼
dm-frontend /admin/recommendations  (analytics report stranica)
```

## Korišćeni podaci

**Evaluacioni derivati** (seeded, `Day 7/data/`, jedini izvor:
`app/data/generate_evaluation.py`) — izvedene tabele iz Day 1 događaja:

| Fajl | Sadržaj |
| --- | --- |
| `test_cases.csv` | evaluacioni slučajevi iz test perioda: `session_id`, `query_product_id`, `target_product_ids`, `n_targets`, `query_time` (2 803 reda) |
| `comparison.csv` | uporedna tabela P@5/R@5/HR@5/NDCG@5/coverage (4 metode) |
| `metadata.json` | izvor, parametri splita, counts, sha256 |

Stanje seed-a: **split\_time = 2026-01-26 11:21:20** (kvantil 0.8 događaja),
train **146 774**, test **36 694** događaja, test sesija **3 121**,
evaluacionih slučajeva **2 803**. Sami događaji ostaju u `Day 1/data/events.csv`
— evaluacija ih referencira, ne duplira.

## AI-ML koncept

* **Top-N evaluacija ≠ predikcija ocene.** Ne merimo „koliko se preporuka svidi"
  (to bi bila ocena). Merimo **da li je među prvih K preporuka bilo nešto što
  je sesija stvarno uradila** (pogledala/dodala/kupila) kasnije. Ground truth
  je *ponašanje*, ne mišljenje.
* **P@K** = udeo relevantnih u prvih K preporuka. Imenilac je `min(K, |ranked|)`
  — broj stvarno vraćenih, NIKAD broj relevantnih (čest bag). P@K kaže „koliki deo
  onoga što sam servirao je bio relevantan". Napomena: standardna definicija deli sa
  `K`; `min(K, |ranked|)` je namerna odluka kursa da preporučivač koji vrati manje od K
  ne bude kažnjen za prazna mesta (navedite to kad poredite sa literaturom).
* **R@K** = udeo SVIH relevantnih koji je uhvaćen. Imenilac je `|relevant|`.
  R@K kaže „koliko od svega što je bilo relevantno sam pokrio u prvih K".
* **HR@K** = 1 ako je bar jedan relevantan u prvih K, inače 0. Najgrublja
  metrika: „da li korisnik uopšte vidi nešto korisno".
* **NDCG@K** = DCG/IDCG. DCG kažnjava poziciju: relevantan na poziciji 1
  vredi više nego na poziciji 3 (log discount). NDCG = 1 kad je poredak
  idealan. Jedina metrika koja *nagradi redosled* unutar top-K.
* **Coverage** = `|distinct preporučenih| / |katalog|`. Nizak coverage =
  **popularity bias**: preporučivač servira samo nekoliko „blockbustera".
  Klasika: visok P@K + nizak coverage = „dobra" metrika, beskoristan
  preporučivač.
* **Temporal split (anti-leakage).** Random split meša prošlost i budućnost:
  treniranje „vidi" test period i metrike lažno rastu. Podela po vremenu
  (train = događaji pre granice) sprečava to. Ovde se i `popularity` kolona iz
  kataloga ignoriše — popularnost se računa iz train događaja, jer je kolona
  računata iz cele istorije (= leaky).
* **Session-based protokol.** Za svaku test sesiju: `query` = prvi različiti
  proizvod, `targets` = proizvodi viđeni kasnije. Pitanje koje evaluacija
  postavlja je „šta sesija radi sledeće?" — ne „šta korisnik trajno voli".

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Metrike (`app/recommenders/evaluation.py`)

Čiste funkcije, edge-case handling:

* `precision_at_k(ranked_ids, relevant_ids, k)` — `|relevant ∩ top-K| / min(K, |ranked|)`.
* `recall_at_k(ranked_ids, relevant_ids, k)` — `|relevant ∩ top-K| / |relevant|`; nula
  relevantnih → 0.0 (definisano `0/0`).
* `hit_rate_at_k(ranked_ids, relevant_ids, k)` — 1.0 ako je bar jedan relevantan.
* `ndcg_at_k(ranked_ids, relevant_ids, k)` — DCG/IDCG, log discount po poziciji.
* `catalog_coverage(recommended_ids, catalog_size)` — distinct / katalog.

Zajednički edge-case: `k <= 0` → `ValueError`; prazna lista preporuka → 0.0;
`k > |ranked|` → imenilac se ograniči na `min(k, |ranked|)`; duplikati se broje
jednom; IDCG se ograniči brojem mesta. `metrics_at_k` vraća sve četiri odjednom.

### Korak 2 — Temporal split (`temporal_split`)

`temporal_split(events, split_ratio=0.8, split_time=None)` → `(train, test, split_time)`. Ako granica nije data, bira se kvantil po **broju događaja**
(deterministički). Događaji `timestamp < split_time` → train, `>=` → test.
Prazni događaji / `split_ratio` van (0,1) → `ValueError`.

### Korak 3 — Test cases (`extract_test_cases`)

Iz test događaja: po sesiji, `query` = prvi *različiti* proizvod po vremenu,
`targets` = različiti proizvodi viđeni kasnije. Sesije sa < `min_session_items`
različitih proizvoda se izuzimaju (nemaju signal „šta sledeće").

### Korak 4 — Prediktori (`make_*_predictor`)

Svaki prediktor se gradi **samo iz train događaja**:

* `make_popularity_predictor` — top-N po train popularnosti (isti za svaki query).
* `make_category_predictor` — top-N iz iste kategorije po train popularnosti.
* `make_content_predictor` — TF-IDF (ne zavisi od vremena) + train popularnost
  za cold-start fallback.
* `make_collaborative_predictor` — interaction matrica + item-item sličnost iz
  **train** događaja (test interakcije NE smeju u matricu).

Rangirane liste se prekompjutuju/keširaju po proizvodu (ceo comparison report ~7 s na box-u); deterministički isti rezultat kao i poziv po slučaju.

### Korak 5 — `evaluate_recommender` (protokol + report builder)

`evaluate_recommender(predict, cases, k, catalog_size)` — za svaki slučaj
`predict(query_product_id, k)` → rangirana lista, pa metrike prema targets; vraća
mean P@K/R@K/HR@K/NDCG@K + `catalog_coverage`.

`build_comparison_report(events, products, k=5, split_ratio=0.8, min_session_items=2)` je
ceo protokol:

1. `temporal_split` → train/test.
2. `extract_test_cases(test_events, min_session_items)` → slučajevi.
3. Za svaki metod iz `PREDICTOR_FACTORIES`: `make_*_predictor(products, train)` → prediktor.
4. `evaluate_recommender(...)` po metodu → red `comparison` tabele.

Vraća report dict (split, counts, `metrics`, opciono `per_case`). Prazan test →
definisan izveštaj sa nulama, **nikad tihi `None`**.

### Korak 6 — Comparison report + generator podataka

`build_comparison_report(...)` koristi **istu granicu** za sve metode (fer
poređenje) i vraća uporednu tabelu. `app/data/generate_evaluation.py` upisuje
`Day 7/data/{test_cases.csv, comparison.csv, metadata.json}` (byte-for-byte).

### Korak 7 — Servis + API + CMS

`app/services/evaluation.py` (lazy + keširan report), `app/api/analytics_routes.py`
(`GET /analytics/recommendations`), CMS analytics stranica.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `precision_at_k(...)` | P@K: udeo relevantnih u top-K (imenilac `min(K, | ranked |
| `recall_at_k(...)` | R@K: udeo relevantnih uhvaćen | `app/recommenders/evaluation.py` |
| `hit_rate_at_k(...)` | HR@K: bar jedan relevantan u top-K | `app/recommenders/evaluation.py` |
| `ndcg_at_k(...)` | NDCG@K: DCG/IDCG (log discount) | `app/recommenders/evaluation.py` |
| `catalog_coverage(...)` | distinct preporučenih / katalog | `app/recommenders/evaluation.py` |
| `temporal_split(...)` | train/test po vremenu (anti-leakage) | `app/recommenders/evaluation.py` |
| `extract_test_cases(...)` | sesija → (query, targets) | `app/recommenders/evaluation.py` |
| `evaluate_recommender(...)` | temporal split + protokol + report | `app/recommenders/evaluation.py` |
| `build_comparison_report(...)` | tabela svih metoda | `app/recommenders/evaluation.py` |
| `make_*_predictor(...)` | popularity/category/content/collaborative prediktori | `app/recommenders/evaluation.py` |
| `RecommendationEvaluationService.comparison_report` | lazy + keširan report | `app/services/evaluation.py` |
| `app/data/generate_evaluation.py` | generiše `Day 7/data/*` (byte-for-byte) | `app/data/generate_evaluation.py` |
| `examples/demo_evaluation.py` | pun comparison report + tumačenje | `Day 7/examples/demo_evaluation.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /analytics/recommendations?k=5&split_ratio=0.8` | 200: comparison report (split, counts, `comparison` tabela); **422** nevalidan `k`/`split_ratio`; **503** nema podataka |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /analytics/recommendations`

```
{
  "k": 5,
  "split_time": "2026-01-26 11:21:20",
  "split_ratio": 0.8,
  "n_train_events": 146774,
  "n_test_events": 36694,
  "n_test_sessions": 3121,
  "n_test_cases": 2803,
  "methods": ["popularity", "category", "content", "collaborative"],
  "comparison": [
    {"method": "popularity", "precision_at_k": 0.081841, "recall_at_k": 0.078593, "hit_rate_at_k": 0.335355, "ndcg_at_k": 0.096795, "catalog_coverage": 0.02381},
    {"method": "category", "precision_at_k": 0.244595, "recall_at_k": 0.297802, "hit_rate_at_k": 0.674634, "ndcg_at_k": 0.345375, "catalog_coverage": 0.285714},
    {"method": "content", "precision_at_k": 0.068641, "recall_at_k": 0.073318, "hit_rate_at_k": 0.278987, "ndcg_at_k": 0.093596, "catalog_coverage": 1.0},
    {"method": "collaborative", "precision_at_k": 0.239386, "recall_at_k": 0.289999, "hit_rate_at_k": 0.668926, "ndcg_at_k": 0.335239, "catalog_coverage": 0.722222}
  ]
}
```

## CMS integracija

Analytics report stranica `dm-frontend/app/pages/admin/recommendations/index.vue`:

* Poziva `GET /ml/analytics/recommendations` (Nitro proxy `/ml/**` → `:3001`).
* Prikazuje **header** (split\_time, broj test slučajeva, sesija, train/test
  događaja) i **uporednu tabelu** (metod × P@5/R@5/HR@5/NDCG@5/coverage).
* **Graceful fallback:** ako dm-ml ne radi, `try/catch` → poruka — stranica se
  NE ruši.
* Veza u admin sidebar-u (`app/layouts/admin.vue`) — stavka „Recommendations".

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 7/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno (Day 7): `precision_at_k` edge case-ovi (**imenilac `min(K,|ranked|)`,
prazne preporuke, nula relevantnih, `k<=0`, duplikati**), `recall_at_k`
(0/0 → 0), `hit_rate_at_k`, `ndcg_at_k` edge case-ovi (**prazna lista, nula
relevantnih, IDCG ograničen mestima, log discount, savršen poredak → 1.0**),
`catalog_coverage` (`catalog_size<=0`), `temporal_split` (eksplicitna granica,
kvantil, determinizam, validacija), `extract_test_cases` (query/targets, filter),
`evaluate_recommender` (savršen/prazan prediktor, prazan test → definisane nule,
**popularity prediktor koristi samo train događaje**), `build_comparison_report`
(sve metode, nepoznata metoda), API (`/analytics/recommendations` 200/422/503).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 7/examples/demo_evaluation.py"`
   — temporal split, test cases, pun comparison report i tumačenje.
2. Pokreni vizualizaciju: `dm-ml/.venv/bin/python "Day 7/examples/visualize_comparison.py"`
   — `comparison.png` (P@5/R@5/HR@5/NDCG@5/coverage po metodi).
3. Pusti servis pa pitaj `GET /analytics/recommendations` — uporedi sa
   `GET /recommendations/popular` i ručnim osećajem „šta izgleda dobro".
4. Pokreni lab (`Day 7/lab/`) — ponovo implementiraj `precision_at_k` /
   `recall_at_k` / `hit_rate_at_k` / `ndcg_at_k` / `catalog_coverage` /
   `temporal_split` na malim podacima i proveri `test_lab.py`.

## Comparison (baseline ugao)

**P@5 / R@5 / HR@5 / NDCG@5 / coverage** (temporal split 0.8, k=5, seeded):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| popularity (baseline) | 0.082 | 0.079 | 0.335 | 0.097 | **0.024** |
| category (baseline) | **0.245** | **0.298** | **0.675** | **0.345** | 0.286 |
| content (ML) | 0.069 | 0.073 | 0.279 | 0.094 | **1.000** |
| collaborative (ML) | 0.239 | 0.290 | 0.669 | 0.335 | 0.722 |

Šta tabela kaže:

* **Category je najprecizniji** na ovom seed-u: sesije ostaju u kategoriji
  (pogledaju slične proizvode), pa ista-kategorija pogađa češće. To nije
  „category je najbolji preporučivač" — to je *svojstvo ovog skupa*.
* **Popularity ima najniži coverage** (2.4 % kataloga = 6 proizvoda) — servira samo
  „blockbustere". Ovo je **popularity bias** uhvaćen merom: HR@5 0.335 izgleda
  pristojno, ali coverage otkriva da su to uvek isti proizvodi.
* **Content ima coverage 1.0, ali najniži P@5 (0.069)** — preporučuje ceo katalog
  (svaki proizvod je „sličan" nekome), a tekstualna sličnost (zajednička linija
  „Compact"/„Pro", broj modela) slabo prati šta sesije stvarno gledaju dalje.
* **Collaborative ≈ category po preciznosti** (0.239 vs 0.245) uz viši coverage
  (0.72 vs 0.29) — ko-interakcije u sesijama nose kategorijsku afinitetnost, ali i
  prelaze između srodnih kategorija.

**Temporal leakage je merljiv:** da smo koristili leaky `popularity` kolonu iz
kataloga (računatu iz cele istorije), popularity metrike bi bile malo više
(P@5 0.085 umesto 0.082, HR@5 0.359 umesto 0.335). Razlika je mala na ovom seed-u, ali
princip je centralan: **budućnost u treningu = lažno bolje metrike**.

## Evaluacija (kako znamo da je dobro)

* **Metrike su definisane i za edge case-ove:** prazna lista → 0.0, nula
  relevantnih → 0.0, `k > |ranked|` → imenilac `min(K, |ranked|)`, `k<=0` →
  ValueError (testovi).
* **Temporal split, ne random:** granica po vremenu; `popularity` iz train
  događaja, ne iz leaky kolone (test `test_popularity_predictor_uses_train_only`).
* **Coverage je obavezan deo report-a** — nijedan izveštaj ne sme da prijavi
  samo jednu metriku (DAY-BRIEFS „Common bugs").
* **Determinizam:** isti podaci + ista granica → isti report; generator je
  byte-for-byte (sha256 u `metadata.json`).
* **Prazan test skup je definisan slučaj:** report sa nulama, ne `None`.
* **Modul je importabilan** od Days 8–10 i capstone-a:
  `from app.recommenders.evaluation import evaluate_recommender, build_comparison_report`.

## Česti bugovi

* **Random split koji procuruje budućnost** — treniranje „vidi" test period,
  metrike lažno rastu. Rešenje: `temporal_split` po vremenu (i popularnost iz
  train događaja, ne iz leaky kolone kataloga).
* **P@K sa imeniocem = broj relevantnih** umesto `min(K, |ranked|)` —
  sa 2 relevantna i K=5 max P@5 postaje 1.0. Rešenje: imenilac je uvek broj
  stvarno serviranih preporuka (test).
* **Izveštavanje samo jedne metrike** — P@K bez coverage-a krije popularity
  bias. Rešenje: report uvek sadrži svih pet mera (test u report builder-u).
* **Ignorisanje coverage-a** — preporučivač sa coverage 2 % može da ima „dobar"
  P@K i da bude beskoristan (uvek najpopularniji). Rešenje: coverage je obavezan.
* **Tihi `[]` / `None` na prazan test skup** — prazan test mora da vrati
  *definisan* izveštaj sa nulama (test).
* **IDCG preko cele liste umesto top-K** — NDCG mora da se normalizuje idealnim
  poretkom OGRANIČENIM na K mesta, inače dugi relevantni skupovi neopravdano
  obaraju skor (test `test_idcg_limited_by_slots`).

## Šta rezultat NE dokazuje

* **Bolji P@5 na ovom skupu ≠ bolji preporučivač u pravom store-u.** Metrika je
  sočivo, ne presuda. Category „pobeđuje" ovde jer sesije ostaju u kategoriji —
  na drugom store-u raspodela je drugačija i poredak može da se obrne.
* **Preporučivač može da ima dobar skor i bude beskoristan.** Popularity ima
  HR@5 0.34 (svaka treća sesija dobije bar jedan hit) ali coverage 2 % — uvek
  servira iste proizvode. Dobre metrike ne znače korisnu raznolikost.
* **Targeti su ponašanje sesije, ne preferencija.** „Sesija je pogledala X
  kasnije" ≠ „korisnik voli X". Evaluacija meri ko-interakciju u budućnosti, ne
  zadovoljstvo.
* **Brojevi važe za sintetički seed (42) i ovaj test period.** Na pravom
  store-u pipeline ostaje, brojevi se menjaju.
* **Coverage 1.0 nije automatski dobar.** Content preporučuje ceo katalog —
  to znači raznolikost, ali ne i relevantnost (P@5 mu je najniži od svih metoda).
* **Evaluacija ne rešava težine interakcija** (Day 6): P@K/NDCG@K mere rezultat
  sa težinama kakve jesu; koje su težine „tačne" ostaje pretpostavka.

## Vežbe

1. **Vary K** — pokreni report za `k=1`, `k=3`, `k=10` (API ili
   `build_comparison_report`) i uporedi redosled algoritama. Šta se menja?
   Zašto popularity HR@K raste sa K brže od P@K?
2. **Objasni NDCG discount** — za `ranked=[3,1,2]`, `relevant=[1]`, `k=3`
   izračunaj DCG, IDCG i NDCG ručno; zameni pozicije i pokaži da se NDCG menja
   iako su P@K i HR@K isti.
3. **Coverage i popularity bias** — dodaj u report treću kolonu za
   „distinct preporučenih / katalog" i diskutuj: koji preporučivač ima najviši
   coverage i da li je to nužno dobro.
4. **Temporal leakage eksperiment** — napravi prediktor koji koristi
   `products_df["popularity"]` (leaky kolonu) umesto train popularnosti i
   uporedi metrike. Razlika je mera leakage-a na ovom seed-u.
5. **Novi kandidat u report** — dodaj `make_heuristic_predictor` (Day 6
   session-co-occurrence heuristika) u `PREDICTOR_FACTORIES` i pusti report.
6. **Metrika od nule** — u lab-u (ili na papiru) implementiraj `ndcg_at_k` bez
   gledanja rešenja i testiraj na `[1,2,3]` vs `[3,1,2]`.
7. **Razmisli o ground truth** — šta bi se promenilo da su targets samo
   `purchase` događaji (ne i `product_view`)? Zašto je izbor ground truth-a
   deo evaluacije, ne tehnički detalj?

## Sažetak

Napravio si **evaluation framework**: ranking metrike (P@K, R@K, HR@K, NDCG@K)
sa edge-case handlingom, **catalog coverage** (hvata popularity bias), **temporal
train/test split** (anti-leakage), session-based protokol (query = prvi proizvod,
targets = kasniji) i **comparison report** preko popularity/category/content/
collaborative. Na ovom seed-u category je najprecizniji (sesije ostaju u
kategoriji), collaborative je skoro jednako precizan uz viši coverage, popularity ima najniži
coverage (2 % — blockbusteri), a content pokriva ceo katalog uz najniži P@5. Centralna lekcija: **„izgleda
dobro" nije evaluacija** — metrika je sočivo, ne presuda; bolji P@5 na ovom
skupu ne dokazuje bolji preporučivač u pravom store-u. Pitanje danas: **kada
metrika prestaje da bude sočivo i postaje presuda — šta još treba da znamo o
tome kako korisnici stvarno koriste preporuke?**

---

<!-- page_id 425 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/comparison.csv

```
method,precision_at_k,recall_at_k,hit_rate_at_k,ndcg_at_k,catalog_coverage
popularity,0.081841,0.078593,0.335355,0.096795,0.02381
category,0.244595,0.297802,0.674634,0.345375,0.285714
content,0.068641,0.073318,0.278987,0.093596,1.0
collaborative,0.239386,0.289999,0.668926,0.335239,0.722222
```

### data/metadata.json

```
{
  "dataset": "dm_recommendation_evaluation_v1",
  "description": "Seeded recommendation-evaluation artifacts. test_cases.csv = session-based evaluation cases from the TEST period of a temporal split (query = first product a session sees, targets = later products in the same session). comparison.csv = P@K / R@K / HR@K / NDCG@K / catalog coverage for the popularity/category/content/collaborative recommenders. Temporal split is used so the FUTURE does not leak into training (DAY-BRIEFS Day 7).",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "products": "Day 5/data/products_text.csv",
    "module": "app.data.generate_evaluation",
    "function": "generate_evaluation",
    "split_function": "app.recommenders.evaluation.temporal_split",
    "metric_functions": "app.recommenders.evaluation"
  },
  "parameters": {
    "k": 5,
    "split_ratio": 0.8,
    "split_time": "2026-01-26 11:21:20",
    "min_session_items": 2,
    "session_protocol": "query = first distinct product by timestamp in test window; targets = distinct products seen later in the same session"
  },
  "columns": {
    "test_cases.csv": [
      "session_id",
      "query_product_id",
      "target_product_ids",
      "n_targets",
      "query_time"
    ],
    "comparison.csv": [
      "method",
      "precision_at_k",
      "recall_at_k",
      "hit_rate_at_k",
      "ndcg_at_k",
      "catalog_coverage"
    ]
  },
  "counts": {
    "n_train_events": 146774,
    "n_test_events": 36694,
    "n_test_sessions": 3121,
    "n_test_cases": 2803,
    "methods": [
      "popularity",
      "category",
      "content",
      "collaborative"
    ]
  },
  "comparison": [
    {
      "method": "popularity",
      "precision_at_k": 0.081841,
      "recall_at_k": 0.078593,
      "hit_rate_at_k": 0.335355,
      "ndcg_at_k": 0.096795,
      "catalog_coverage": 0.02381
    },
    {
      "method": "category",
      "precision_at_k": 0.244595,
      "recall_at_k": 0.297802,
      "hit_rate_at_k": 0.674634,
      "ndcg_at_k": 0.345375,
      "catalog_coverage": 0.285714
    },
    {
      "method": "content",
      "precision_at_k": 0.068641,
      "recall_at_k": 0.073318,
      "hit_rate_at_k": 0.278987,
      "ndcg_at_k": 0.093596,
      "catalog_coverage": 1.0
    },
    {
      "method": "collaborative",
      "precision_at_k": 0.239386,
      "recall_at_k": 0.289999,
      "hit_rate_at_k": 0.668926,
      "ndcg_at_k": 0.335239,
      "catalog_coverage": 0.722222
    }
  ],
  "fields": {
    "session_id": "str, user_session (Day 1 kolona) — red evaluacionog slučaja",
    "query_product_id": "int, PRVI različiti proizvod koji sesija vidi u test periodu — ulaz u preporučivača (query)",
    "target_product_ids": "str, različiti proizvodi viđeni KASNIJE u istoj sesiji, ';'-spojeni — ground truth (šta je sesija stvarno radila posle query-ja)",
    "n_targets": "int, broj target proizvoda",
    "query_time": "str, timestamp prvog proizvoda u sesiji (test period)"
  },
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "test_cases.csv": "c5ee998c96efaff8b0533095864254de634adad5bd96c0b00bb286e0e84f2022",
      "comparison.csv": "e88d3ef65d5090a4b509bb26606b0fb455203d7137c47fb4d3476794fe939359"
    }
  }
}
```

### data/README.md

# Day 7 podaci — evaluacioni derivati (test cases + comparison report)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `test_cases.csv` | evaluacioni slučajevi iz **test perioda** temporalnog splita: `session_id`, `query_product_id`, `target_product_ids`, `n_targets`, `query_time` | 2 803 |
| `comparison.csv` | P@K / R@K / HR@K / NDCG@K / coverage za popularity/category/content/collaborative | 4 |
| `metadata.json` | izvor, parametri splita, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (jedini izvor istine) + `Day 5/data/products_text.csv`
  (katalog).
* **Temporal split** (`temporal_split`, `app/recommenders/evaluation.py`): granica
  = kvantil 0.8 po broju događaja (`2026-01-26 11:21:20`); događaji pre granice
  = train (146 774), posle = test (36 694). **Nije random split** — random
  procuruje budućnost i lažno povećava metrike.
* **Test cases** (`extract_test_cases`): po sesiji iz test perioda,
  `query` = prvi *različiti* proizvod, `targets` = različiti proizvodi viđeni
  kasnije u istoj sesiji. Sesije sa < 2 različita proizvoda se izuzimaju (nemaju
  signal „šta sledeće").
* **Comparison** (`build_comparison_report`): svaki preporučivač se trenira
  SAMO na train događajima (npr. popularity iz train-a, ne iz `popularity`
  kolone kataloga koja je računata iz cele istorije — temporalni leakage).
* Generator: `app/data/generate_evaluation.py` (upisuje CSV + metadata).

## Ključne kolone (`test_cases.csv`)

| Kolona | Značenje |
| --- | --- |
| `session_id` | `user_session` (Day 1) — red evaluacionog slučaja |
| `query_product_id` | prvi proizvod koji sesija vidi u test periodu — ulaz u preporučivača |
| `target_product_ids` | proizvodi viđeni KASNIJE u istoj sesiji, `;`-spojeni — ground truth |
| `n_targets` | broj target proizvoda |
| `query_time` | timestamp prvog proizvoda (test period) |

## Stanje u ovom seed-u

* split\_time: **2026-01-26 11:21:20** (kvantil 0.8 događaja)
* train: **146 774** događaja · test: **36 694** događaja · test sesija: **3 121**
* evaluacionih slučajeva: **2 803**

Comparison (k=5):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| popularity | 0.082 | 0.079 | 0.335 | 0.097 | 0.024 |
| category | 0.245 | 0.298 | 0.675 | 0.345 | 0.286 |
| content | 0.069 | 0.073 | 0.279 | 0.094 | 1.000 |
| collaborative | 0.239 | 0.290 | 0.669 | 0.335 | 0.722 |

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_evaluation
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Metrike važe **za ovaj sintetički seed (42)** i **ovaj test period**; na pravom
store-u raspodela sesija/događaja je drugačija. `target_product_ids` je
*ponašanje sesije* (šta je gledala posle), ne dokaz preferencije. Bolji P@5
kategorije na ovom skupu ne znači da je category preporučivač „najbolji" —
coverage pokazuje da popularnost servira samo 2 % kataloga (popularity bias), a
content 100 % (preporučuje sve). Metrika je sočivo, ne presuda.

### examples/demo\_evaluation.py

```
"""Demo: recommendation evaluation framework (Day 7).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 7/examples/demo_evaluation.py"

Prikazuje:
  1) temporal split — train/test po VREMENU (anti-leakage), sa brojevima;
  2) test cases — sesija → (query, targets) iz test perioda;
  3) ručno izračunate metrike na jednom primeru (P@K, R@K, HR@K, NDCG@K);
  4) **comparison report** — popularity/category/content/collaborative
     (P@5/R@5/HR@5/NDCG@5/coverage);
  5) tumačenje: category najprecizniji, popularity najniži coverage
     (popularity bias), content coverage 1.0.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.paths import course_root, dataset_path
from app.recommenders.evaluation import (
    build_comparison_report,
    extract_test_cases,
    metrics_at_k,
    temporal_split,
)

K = 5
SPLIT_RATIO = 0.8


def main() -> None:
    print("=== Day 7 — Recommendation Evaluation Framework ===\n")

    events = pd.read_csv(dataset_path("events.csv"))
    products = pd.read_csv(course_root() / "Day 5" / "data" / "products_text.csv")

    # --- 1) Temporal split --------------------------------------------------- #
    train, test, split = temporal_split(events, split_ratio=SPLIT_RATIO)
    print(f"[1] Temporal split (NE random): granica = {split}")
    print(f"    train={len(train)} događaja · test={len(test)} događaja · "
          f"test sesija={test['user_session'].nunique()}")
    print("    Random split bi promešao prošlost i budućnost (leakage); ovako se")
    print("    preporučivači treniraju SAMO na prošlosti.\n")

    # --- 2) Test cases ------------------------------------------------------- #
    cases = extract_test_cases(test, min_session_items=2)
    print(f"[2] Test cases (sesija → query → targets): {len(cases)}")
    for c in cases[:3]:
        print(f"    {c['session_id']}: query={c['query_product_id']} "
              f"targets={c['target_product_ids']}")
    print("    query = prvi proizvod koji sesija vidi u test periodu;")
    print("    targets = proizvodi viđeni KASNIJE u istoj sesiji.\n")

    # --- 3) Ručno izračunate metrike na jednom primeru ----------------------- #
    case = cases[0]
    ranked = [case["target_product_ids"][0], 999, 998, 997, 996]  # hipotetički top-5
    m = metrics_at_k(ranked, case["target_product_ids"], K)
    print("[3] Metrike na jednom primeru:")
    print(f"    query={case['query_product_id']} targets={case['target_product_ids']}")
    print(f"    hipotetički top-5 = {ranked}")
    for name, val in m.items():
        print(f"      {name}: {val:.4f}")
    print("    P@K udeo relevantnih u top-K · R@K udeo relevantnih uhvaćen ·")
    print("    HR@K bar jedan pogodak · NDCG@K kažnjava duboke pozicije.\n")

    # --- 4) Comparison report ------------------------------------------------ #
    print(f"[4] Comparison report (k={K}, split_ratio={SPLIT_RATIO}):")
    report = build_comparison_report(events, products, k=K, split_ratio=SPLIT_RATIO)
    header = f"{'metod':14s} {'P@5':>6s} {'R@5':>6s} {'HR@5':>6s} {'NDCG@5':>8s} {'coverage':>9s}"
    print("    " + header)
    for row in report["comparison"]:
        print(
            f"    {row['method']:14s} {row['precision_at_k']:6.3f} "
            f"{row['recall_at_k']:6.3f} {row['hit_rate_at_k']:6.3f} "
            f"{row['ndcg_at_k']:8.3f} {row['catalog_coverage']:9.3f}"
        )
    print(f"\n    n_test_cases = {report['n_test_cases']}")

    # --- 5) Tumačenje -------------------------------------------------------- #
    print("\n[5] Tumačenje:")
    print("    - category ima najviši P@5/HR@5: sesije ostaju u kategoriji.")
    print("    - popularity ima najniži coverage (2%): popularity bias — uvek isti")
    print("      'blockbusteri'; dobra metrika ne znači korisnu raznolikost.")
    print("    - content coverage 1.0: preporučuje ceo katalog (raznolikost, ne i")
    print("      nužno relevantnost).")
    print("    - Metrike su sočivo, ne presuda: bolji P@5 ovde ≠ bolji preporučivač")
    print("      u pravom store-u.")


if __name__ == "__main__":
    main()
```

### examples/visualize\_comparison.py

```
"""Vizualizacija comparison report-a (Day 7, supporting material).

Jedna slika u ``Day 7/examples/``:

    - ``comparison.png`` — grupisani bar chart: P@5 / R@5 / HR@5 / NDCG@5 /
      coverage po metodi (popularity/category/content/collaborative). Vizuelno
      pokazuje: category najviše metrike, popularity najniži coverage
      (popularity bias), content coverage 1.0.

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 7/examples/visualize_comparison.py"

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
import pandas as pd

from app.data.paths import course_root, dataset_path
from app.recommenders.evaluation import build_comparison_report

OUT_DIR = Path(__file__).resolve().parent
METRIC_LABELS = {
    "precision_at_k": "P@5",
    "recall_at_k": "R@5",
    "hit_rate_at_k": "HR@5",
    "ndcg_at_k": "NDCG@5",
    "catalog_coverage": "coverage",
}


def main() -> None:
    events = pd.read_csv(dataset_path("events.csv"))
    products = pd.read_csv(course_root() / "Day 5" / "data" / "products_text.csv")
    report = build_comparison_report(events, products, k=5, split_ratio=0.8)

    comparison = pd.DataFrame(report["comparison"]).set_index("method")
    metrics = [m for m in METRIC_LABELS if m in comparison.columns]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(comparison))
    width = 0.15
    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"]
    for i, metric in enumerate(metrics):
        vals = comparison[metric].astype(float)
        ax.bar(x + (i - len(metrics) / 2) * width, vals, width * 0.92,
               label=METRIC_LABELS[metric], color=colors[i % len(colors)])
        for xi, v in zip(x, vals):
            ax.text(xi + (i - len(metrics) / 2) * width, v + 0.01, f"{v:.2f}",
                    ha="center", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(comparison.index)
    ax.set_ylabel("vrednost (0–1)")
    ax.set_ylim(0, 1.12)
    ax.set_title(f"Comparison report (k=5, temporal split 0.8, "
                 f"n={report['n_test_cases']} test cases)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    out = OUT_DIR / "comparison.png"
    fig.savefig(out, dpi=140)
    print(f"Sačuvano: {out}")

    # Ispis tumačenja koje slika ne pokazuje sama.
    print("\nKratko tumačenje:")
    print("  - category: najviši P@5/HR@5 — sesije ostaju u kategoriji.")
    print("  - popularity: najniži coverage (~0.02) — popularity bias (blockbusteri).")
    print("  - content: coverage 1.0 — preporučuje ceo katalog (raznolikost ≠ relevantnost).")


if __name__ == "__main__":
    main()
```

### lab/README.md

# Lab — Dan 7: ranking metrike i temporal split

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/recommenders/evaluation.py` već sadrži (da bi razumeo *šta* te
metrike rade). Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje
rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` — `dm-ml/.venv` ih ima.
* Lab radi na malim, ručno napravljenim listama — nema seeded CSV-a.

## Zadatak (koraci)

Implementiraj čiste funkcije nad listama ID-jeva (`ranked_ids` = redosled
preporuka, `relevant_ids` = ground truth — šta je sesija stvarno radila kasnije).

1. **`precision_at_k(ranked_ids, relevant_ids, k)`** — P@K = `|relevant ∩ top-K| / min(K, |ranked|)`. Imenilac je **broj stvarno serviranih** preporuka, NIKAD
   broj relevantnih (čest bag). Prazna lista → `0.0`; `k <= 0` → `ValueError`.
2. **`recall_at_k(ranked_ids, relevant_ids, k)`** — R@K = `|relevant ∩ top-K| / |relevant|`. Nula relevantnih (`0/0`) → `0.0` (definisano).
3. **`hit_rate_at_k(ranked_ids, relevant_ids, k)`** — HR@K = `1.0` ako je bar
   jedan relevantan u top-K, inače `0.0`.
4. **`ndcg_at_k(ranked_ids, relevant_ids, k)`** — DCG@K = Σ `rel_i / log2(i+2)`
   (rel\_i = 1 ako je pozicija `i` relevantna), IDCG@K = DCG idealnog poretka
   (svi relevantni prvo, ograničeno na `min(|relevant|, |top|)` mesta).
   NDCG = DCG/IDCG; nula relevantnih ili prazna lista → `0.0`.
5. **`catalog_coverage(recommended_ids, catalog_size)`** — `|set(ids)| / catalog_size`. `catalog_size <= 0` → `ValueError`.
6. **`temporal_split(events_df, split_time)`** — događaji sa
   `timestamp < split_time` → train, `>=` → test. Vrati `(train_df, test_df)`.

## Provera

```
# iz Day 7/lab/ — koristi dm-ml venv
dm-ml/.venv/bin/python -m pytest test_lab.py                       # tvoj starter
LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
```

## Šta radiš, a šta ne

* Radiš: pet metrika (edge case-ovi uključeni), temporal split.
* Ne radiš: ceo `evaluate_recommender` protokol, prediktore, comparison report,
  API, generator `Day 7/data` — to koristi tvoje funkcije u
  `app/recommenders/evaluation.py` i servisu.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.

### lab/starter.py

```
"""Starter za Day 7 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 7/lab/``, koristi dm-ml venv):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

import math

import pandas as pd


def precision_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """P@K — udeo relevantnih u prvih K preporuka. TODO: implementirati.

    Zahtevi:
    - ``top = ranked_ids[:k]``; imenilac je ``min(k, len(top))`` (broj stvarno
      serviranih), NIKAD broj relevantnih.
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    - duplikati se broje jednom (``set``).
    """
    raise NotImplementedError("implementiraj precision_at_k")


def recall_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """R@K — udeo relevantnih uhvaćen. TODO: implementirati.

    Zahtevi:
    - ``hits / len(relevant_ids)`` (imenilac je broj relevantnih, ne k).
    - nula relevantnih (``0/0``) -> ``0.0`` (definisano).
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    """
    raise NotImplementedError("implementiraj recall_at_k")


def hit_rate_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """HR@K — 1.0 ako je bar jedan relevantan u top-K, inače 0.0. TODO: implementirati.

    Zahtevi:
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    """
    raise NotImplementedError("implementiraj hit_rate_at_k")


def ndcg_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """NDCG@K — DCG/IDCG (log discount po poziciji). TODO: implementirati.

    Zahtevi:
    - DCG@K = sum(rel_i / log2(i + 2)) za i u 0..len(top)-1, rel_i = 1 ako je
      ``top[i]`` relevantan.
    - IDCG@K = DCG idealnog poretka: svi relevantni prvo, ograničeno na
      ``min(len(relevant), len(top))`` mesta.
    - prazna lista preporuka ili nula relevantnih -> ``0.0``; ``k <= 0`` ->
      ``ValueError``.
    """
    raise NotImplementedError("implementiraj ndcg_at_k")


def catalog_coverage(recommended_ids: list, catalog_size: int) -> float:
    """Udeo kataloga koji se UOPŠTE preporuči. TODO: implementirati.

    Zahtevi:
    - ``len(set(recommended_ids)) / catalog_size``.
    - ``catalog_size <= 0`` -> ``ValueError``; prazne preporuke -> ``0.0``.
    """
    raise NotImplementedError("implementiraj catalog_coverage")


def temporal_split(
    events_df: pd.DataFrame,
    split_time: str,
    timestamp_column: str = "timestamp",
) -> tuple:
    """Podeli događaje na train/test po vremenu. TODO: implementirati.

    Zahtevi:
    - događaji sa ``timestamp < split_time`` idu u train, ``>= split_time`` u test.
    - vrati ``(train_df, test_df)`` (DataFrame-ovi, redosled redova očuvan).
    """
    raise NotImplementedError("implementiraj temporal_split")
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
import math

import pandas as pd


def test_precision_recall_hr():
    assert lab.precision_at_k([1, 2, 3, 4, 5], [1, 3], 5) == pytest.approx(0.4)
    assert lab.precision_at_k([1, 2], [1], 5) == pytest.approx(0.5)    # imenilac min(k, len(top))
    assert lab.precision_at_k([1, 1, 2], [1], 3) == pytest.approx(0.5)  # duplikati jednom
    assert lab.recall_at_k([1, 2, 3], [1, 9], 3) == pytest.approx(0.5)
    assert lab.recall_at_k([1], [], 3) == 0.0 and lab.precision_at_k([], [1], 3) == 0.0
    assert lab.hit_rate_at_k([5, 6, 1], [1], 3) == 1.0 and lab.hit_rate_at_k([5, 6, 1], [1], 2) == 0.0
    for f in (lab.precision_at_k, lab.recall_at_k, lab.hit_rate_at_k, lab.ndcg_at_k):
        with pytest.raises(ValueError):
            f([1], [1], 0)


def test_ndcg():
    assert lab.ndcg_at_k([1, 2], [1], 2) == pytest.approx(1.0)
    assert lab.ndcg_at_k([2, 1], [1], 2) == pytest.approx(1 / math.log2(3))
    assert lab.ndcg_at_k([], [1], 3) == 0.0


def test_coverage_and_split():
    assert lab.catalog_coverage([1, 1, 2], 4) == 0.5
    with pytest.raises(ValueError):
        lab.catalog_coverage([1], 0)
    df = pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-03", "2026-01-02"], "x": [1, 2, 3]})
    tr, te = lab.temporal_split(df, "2026-01-02")
    assert list(tr["x"]) == [1] and list(te["x"]) == [2, 3]
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 7 lab-a."""
from __future__ import annotations

import math

import pandas as pd


def _chk(k):
    if k <= 0:
        raise ValueError("k mora biti > 0")


def precision_at_k(ranked_ids, relevant_ids, k):
    _chk(k); top = list(dict.fromkeys(ranked_ids[:k]))
    return len(set(top) & set(relevant_ids)) / min(k, len(top)) if top else 0.0


def recall_at_k(ranked_ids, relevant_ids, k):
    _chk(k); rel = set(relevant_ids)
    return len(set(ranked_ids[:k]) & rel) / len(rel) if ranked_ids and rel else 0.0


def hit_rate_at_k(ranked_ids, relevant_ids, k):
    _chk(k)
    return 1.0 if set(ranked_ids[:k]) & set(relevant_ids) else 0.0


def ndcg_at_k(ranked_ids, relevant_ids, k):
    _chk(k); rel = set(relevant_ids); top = list(ranked_ids[:k])
    if not top or not rel:
        return 0.0
    dcg = sum(1 / math.log2(i + 2) for i, p in enumerate(top) if p in rel)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(rel), len(top))))
    return dcg / idcg


def catalog_coverage(recommended_ids, catalog_size):
    if catalog_size <= 0:
        raise ValueError("catalog_size mora biti > 0")
    return len(set(recommended_ids)) / catalog_size if len(recommended_ids) else 0.0


def temporal_split(events_df, split_time, timestamp_column="timestamp"):
    ts = pd.to_datetime(events_df[timestamp_column]); t = pd.Timestamp(split_time)
    return events_df[ts < t], events_df[ts >= t]
```
