# Dan 8 — Hybrid Candidate-Generation and Ranking Pipeline

- lesson_id: 118
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:47.362 updated: 2026-09-05 20:00:29.717
- summary: „Preporuči sve što bi moglo da se svidi" nije isto što i „preporuči ono što se zaista svidi". Prvo širiš mrežu (candidate generation — jeftino, puno kandidata), pa sužavaš (scoring + ranking — normalizuj skorove izvora, spoj težinama, primeni biznis pravila, raznovrsnost). Postojeći 2.0/0.5 merge je degenerisano seme: ručne težine nad SIROVIM skorovima. Težine su heuristika, ne naučen odgovor — dok ih ranking model ne nauči, bolja hybrid metrika ne dokazuje da su težine „tačne". [subjects-import]


---

<!-- page_id 426 order 0 -->
## [Page] Materijal

# Dan 8 — Hybrid Candidate-Generation and Ranking Pipeline

> *„Preporuči sve što bi moglo da se svidi" nije isto što i „preporuči ono što
> se zaista svidi". Prvo širiš mrežu (candidate generation — jeftino, puno
> kandidata), pa sužavaš (scoring + ranking — normalizuj skorove izvora, spoj
> težinama, primeni biznis pravila, raznovrsnost). Postojeći `2.0/0.5` merge
> je degenerisano seme: ručne težine nad SIROVIM skorovima. Težine su
> heuristika, ne naučen odgovor — dok ih ranking model ne nauči, bolja hybrid
> metrika ne dokazuje da su težine „tačne".*

## Šta gradimo

**Hybrid pipeline za preporuke korisniku**: popularity/category/content/
collaborative candidate generatori → **merge** (normalizacija skorova +
težinski spoj) → **score** → **rank** → **biznis pravila** (dostupnost,
isključi viđeno/kupljeno) → **raznovrsnost** — izloženo kroz
`GET /recommendations/{user_id}` i integrisano u shop stranicu (default vs
personalized poredak). Do sada smo pravili preporučivače koji odgovaraju na
„šta je slično ovom proizvodu" (Day 5/6). Danas pravimo preporuke **za
korisnika**, spajajući sve izvore u jednu rangiranu listu — i postavljamo
pitanje: **kako da spojimo izvore koji mere različite stvari (tekst, ponašanje,
popularnost)?**

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `generate_candidates` | **data preprocessing / retrieval** (jeftin, recall-orijentisan) |
| `merge_candidates` | **data preprocessing** (normalizacija + težinski spoj) |
| `score_candidate` | **rule / heuristic** (težinski blend — pretpostavka, ne naučen) |
| `rank_candidates` | **statistical / sort** (deterministički) |
| `apply_business_rules` | **rule / business logic** (dostupnost, isključenja, price cap) |
| `diversify_results` | **rule / heuristic** (raznovrsnost uz očuvanje relevantnosti) |
| `recommend_for_user` | **rule / heuristic** (orkestracija + cold-start fallback) |
| `build_user_based_comparison` | **statistical / evaluation protocol** (hybrid vs single-source, Day 7 metrike) |

## Application requirement

Shop stranica već prikazuje proizvode u **default poretku** (iz baze). Day 8
dodaje **personalizovani poredak**: shop poziva `GET /ml/recommendations/{user_id}`
i **rerankira** grid — sa mogućnošću poređenja „default vs personalized"
(koji proizvodi su se pomerili gore/dole i zašto). Bez toga, korisnik vidi
istu listu svima; sa hybrid pipeline-om lista zavisi od istorije korisnika.

## Ciljevi učenja

Do kraja dana treba da:

* objasnite **two-stage arhitekturu**: retrieval (candidate generation —
  recall, jeftin) vs ranking (scoring — precision); zašto se NE rangira svaki
  izvor posebno pa konkateniše (**scoring before merging** je čest bag);
* implementirate **`generate_candidates`** za četiri izvora (popularity,
  category, content, collaborative) i objasnite šta svaki meri;
* **normalizujete skorove izvora pre spajanja** (`merge_candidates`) — ne možeš
  sabrati TF-IDF sličnost 0..1 sa count-om interakcija 0..stotine;
* **score + rank** kandidate (težine su heuristika, ne naučen odgovor);
* primenite **biznis pravila posle rangiranja** (dostupnost = slow movers se
  čiste, isključi viđeno/kupljeno, price cap) — filter, ne generator;
* dodate **raznovrsnost** bez uništavanja relevantnosti („fill, don't
  truncate");
* rešite **cold-start korisnika** eksplicitnim fallback-om — nikad tihi `[]`;
* uporedite **hybrid vs single-source** na user-based protokolu (Day 7 metrike)
  i protumačite šta razlika znači — i šta NE znači.

## Preduslovi

Day 1 događaji (korisnici + sesije), Day 5 katalog (`products_text.csv`),
Day 5 content (TF-IDF + kosinus), Day 6 collaborative (interaction matrica +
item-item sličnost), Day 7 evaluacija (temporal split + metrike). Kao i Day 7,
sve se gradi iz **train** perioda da budućnost ne procuri.

## Postojeći sistem (šta nasleđujemo)

* **Day 1/seed `2.0/0.5` merge** (`recomendations.py`): za proizvod —
  collaborative skor × 2.0 + 0.5 po proizvodu iz iste kategorije. **Degenerisano
  seme:** ručne težine nad SIROVIM skorovima, bez normalizacije, bez
  biznis pravila, bez raznovrsnosti.
* **Day 5:** popularity/category baseline + content recommender (TF-IDF), sa
  cold-start fallback-om na popularity.
* **Day 6:** collaborative recommender (implicitna matrica + item-item), sa
  fallback-om i weight-sensitivity (težine = pretpostavke).
* **Day 7:** evaluation framework (P@K/R@K/HR@K/NDCG@K, coverage, temporal
  split, comparison report).
* **Nedostaje:** preporuka ZA KORISNIKA koja spaja izvore; filter posle
  rangiranja; raznovrsnost; fallback za nepoznatog korisnika. Day 8 to dodaje.

## Arhitektura

```
Day 1 događaji (events.csv)              Day 5 katalog (products_text.csv)
      │                                             │
      ▼                                             ▼
temporal_split (0.8)  →  TRAIN istorija (anti-leakage, Day 7)
      │
      ▼
app/recommenders/hybrid.py  recommend_for_user(user_id)
  │
  ├── generate_candidates (retrieval — široko)
  │     popularity | category | content (TF-IDF) | collaborative (item-item)
  │
  ├── merge_candidates  (normalizacija po izvoru + težinski spoj 0.2/0.3/0.3/0.2)
  ├── score_candidate   (blended skor)
  ├── rank_candidates   (opadajuće, tie-break product_id)
  │
  ├── apply_business_rules  (dostupnost, isključi kupljeno, min_score)
  ├── diversify_results     (max_per_category=2, fill don't truncate)
  │
  ▼
GET /recommendations/{user_id}     (API, cold-start fallback na popularity;
                                    alias /recommendations/user/{user_id};
                                    statičke rute /popular, /content/…, /session/…
                                    MORAJU biti registrovane PRE ove parametarske)
      │
      ▼
dm-frontend shop page   shop/index.vue → /ml/recommendations/{user_id}
                        (default vs personalized poredak)
```

## Korišćeni podaci

**Hybrid derivati** (seeded, `Day 8/data/`, jedini izvor:
`app/data/generate_hybrid.py`) — izvedene tabele iz Day 1 događaja + Day 5
kataloga:

| Fajl | Sadržaj |
| --- | --- |
| `candidates.csv` | kandidati PO IZVORU za 5 demo korisnika (recall faza): `user_id`, `source`, `product_id`, `score`, `rank_in_source` (600 redova) |
| `ranking.csv` | finalni hybrid ranking posle merge/score/pravila/raznovrsnosti (25 redova) |
| `comparison.csv` | hybrid vs single-source (user-based protokol): P@5/R@5/HR@5/NDCG@5/coverage (5 metoda) |
| `metadata.json` | izvor, parametri, težine, counts, sha256 |

Stanje seed-a: **split\_time = 2026-01-26 11:21:20** (kvantil 0.8), train
**146 774**, test **36 694**, test korisnika **1 293**. Dostupnih proizvoda
(biznis pravilo, kvantil 0.2 popularnosti = slow movers se čiste): **201 / 252**.
Modeli se grade iz train događaja — Day 7 anti-leakage lekcija.

## AI-ML koncept

* **Retrieval ≠ ranking.** Prva faza (candidate generation) je **recall**:
  jeftino, široko — svaki izvor predloži do 30 kandidata. Druga faza
  (scoring + ranking) je **precision**: suzi na top-K posle spajanja. Greška
  „scoring before merging" je rangiranje svakog izvora posebno pa spajanje
  konkatenacijom — poredak postaje artifact redosleda izvora.
* **Zašto normalizacija?** Izvori mere različite stvari na različitim skalama:
  TF-IDF kosinus je 0..1, count interakcija je 0..stotine, popularity kolona
  je 0..hiljade. Zbir sirovih skorova = popularnost uvek pobeđuje. `merge_candidates`
  normalizuje PO IZVORU (max-skaliranje) pa tek onda meša težinama.
* **Težine merge-a su heuristika.** `0.2/0.3/0.3/0.2` je ručno biranje, kao i
  seed-ov `2.0/0.5`. Dok ranking model (Day 12 / capstone) ne nauči težine iz
  podataka, one ostaju pretpostavka. Zato izveštaj mora da kaže koje su težine
  korišćene — DAY-BRIEFS „What the result does NOT prove".
* **Biznis pravila idu POSLE rangiranja.** Dostupnost (slow movers se čiste),
  isključi već viđeno/kupljeno, price cap — to su filteri na rangiranoj listi,
  ne generatori kandidata.
* **Raznovrsnost ne sme da uništi relevantnost.** Greedy re-ranker po kategoriji
  sa `max_per_category=2`; ako ostane mesta do `k`, lista se DOPUNJAVA (ne
  seče) — „fill, don't truncate".
* **Cold-start korisnik nije greška.** Nepoznat korisnik → popularity baseline
  sa `fallback=True`, `fallback_reason="unknown_user"`. Nikad tihi `[]`.
* **User-based protokol.** Za razliku od Day 7 (query = prvi proizvod sesije),
  ovde je query = `user_id`; targets = NOVI proizvodi iz test perioda (van
  train istorije korisnika). Pitanje: „šta korisnik novo radi posle?"

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Candidate generation (`generate_candidates`)

Za korisnika: signal proizvodi = njegovi proizvodi po težinskom interesu
(view=1/cart=3/purchase=5, top 15). Za svaki izvor, kandidati:

* `popularity` — globalni top-N po train popularnosti (isti za svakog, baseline);
* `category` — top-N iz omiljenih kategorija korisnika po train popularnosti;
* `content` — najsličniji (TF-IDF kosinus) signal proizvodima, MAKS po signal
  proizvodu (recall — dovoljan je jedan sličan signal);
* `collaborative` — item-item slični signal proizvodima (Day 6), isti obrazac.

Rangirane liste po proizvodu se **keširaju** (Day 7 pattern) — evaluacija
preko stotina korisnika ne računa istu listu iznova.

### Korak 2 — Merge (`merge_candidates`)

`merge_candidates(candidate_lists, weights)`: svaki izvor se normalizuje
(max-skaliranje), pa blended = `Σ w_source × normalized_score` (težine se
normalizuju da zbirom budu 1.0). Duplikati se spajaju; `sources` i `per_source`
čuvaju trag. Edge-case: prazan ulaz → `[]`, nepoznat izvor → `ValueError`,
zbir težina ≤ 0 → `ValueError`.

### Korak 3 — Score + rank (`score_candidate`, `rank_candidates`)

`score_candidate(normalized_by_source, weights)` — blended skor jednog kandidata (težinski zbir normalizovanih skorova po izvoru);
`rank_candidates(candidates)` — sort opadajuće, tie-break `product_id`
rastuće (determinizam).

### Korak 4 — Biznis pravila (`apply_business_rules`)

`apply_business_rules(ranked, rules)` — filter posle rangiranja; `rules` je dict sa
ključevima `available_ids` (dostupnost), `exclude_ids` (npr. već kupljeno) i
`min_score`. Vraća `{"ranked": kept, "removed": [...]}` gde svaki uklonjeni kandidat
nosi `removed_by` razloge (`unavailable`, `excluded`, `below_min_score`). Podrazumevana
pravila za korisnika (`HybridModels.recommend`): isključi **kupljeno** + dostupnost
(slow movers se čiste). Viđeno se namerno NE isključuje — ponovno prikazivanje
gledanog proizvoda je legitimna e-commerce preporuka (vežba: dodaj `exclude_ids` za viđeno
i izmeri efekat).

### Korak 5 — Raznovrsnost (`diversify_results`)

`diversify_results(ranked, k, max_per_category=2)` — greedy re-ranker po
kategoriji, sa dopunjavanjem do `k` (raznovrsnost ne seče relevantnost).

### Korak 6 — `recommend_for_user` (pipeline + cold-start)

`recommend_for_user(models, user_id, k=5)` (modul) / `HybridRecommenderService.recommend_for_user(user_id, limit)` (servis) — sve zajedno.
Nepoznat korisnik (nema događaja) → **fallback na popularity top-N** sa
`fallback=True`, `fallback_reason="unknown_user"`. Envelope nosi i
`candidate_counts`, `merge_weights`, `rules`, `n_after_rules` — da se vidi
šta se desilo (transparentnost pipeline-a).

### Korak 7 — User-based evaluacija (`build_user_based_comparison`)

`build_user_based_comparison(products, events, k=5, split_ratio=0.8, max_test_users=None)`:
temporal split → test korisnici (istorija u oba perioda) → za svakog:
`recommend_for_user` na train istoriji → P@K/R@K/HR@K/NDCG@K prema NOVIM
proizvodima iz test perioda + coverage. Metode: `hybrid` + svaki pojedinačni
izvor (single-source = pipeline sa jednim generatorom).

### Korak 8 — Servis + API + generator + CMS

`app/services/hybrid.py` (lazy + keširani modeli i report),
`GET /recommendations/{user_id}` + `GET /analytics/recommendations/hybrid`,
`app/data/generate_hybrid.py` (upisuje `Day 8/data/*`), shop stranica
rerankira grid.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `generate_candidates(...)` | kandidati PO IZVORU (recall) za korisnika | `app/recommenders/hybrid.py` |
| `merge_candidates(...)` | normalizacija izvora + težinski spoj + dedup | `app/recommenders/hybrid.py` |
| `score_candidate(...)` | blended skor jednog kandidata | `app/recommenders/hybrid.py` |
| `rank_candidates(...)` | sort opadajuće, tie-break product\_id | `app/recommenders/hybrid.py` |
| `apply_business_rules(...)` | dostupnost + isključenja + price cap (filter) | `app/recommenders/hybrid.py` |
| `diversify_results(...)` | greedy raznovrsnost (fill, ne truncate) | `app/recommenders/hybrid.py` |
| `recommend_for_user(...)` | ceo pipeline + cold-start fallback | `app/recommenders/hybrid.py` |
| `build_user_based_comparison(...)` | hybrid vs single-source (Day 7 metrike) | `app/recommenders/hybrid.py` |
| `HybridRecommenderService.recommend_for_user` | lazy + keširani modeli | `app/services/hybrid.py` |
| `app/data/generate_hybrid.py` | generiše `Day 8/data/*` (byte-for-byte) | `app/data/generate_hybrid.py` |
| `examples/demo_hybrid.py` | pun demo pipeline + comparison | `Day 8/examples/demo_hybrid.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /recommendations/{user_id}?limit=5` | 200: hybrid envelope (`user_id`, `method`, `fallback`, `candidate_counts`, `merge_weights`, `rules`, `recommendations`); **nepoznat korisnik → 200 sa fallback-om** (`fallback_reason="unknown_user"`, popularity top-N); **422** nevalidan `limit`; **503** nema podataka |
| `GET /analytics/recommendations/hybrid?k=5&split_ratio=0.8` | 200: user-based comparison report (split, counts, `comparison` tabela); **422** nevalidan `k`/`split_ratio`; **503** nema podataka |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /recommendations/395?limit=3`

```
{
  "user_id": 395, "method": "hybrid", "fallback": false, "fallback_reason": null,
  "returned": 3,
  "recommendations": [
    {"product_id": 50, "name": "Biography Essential 819", "category_id": 3, "price": 23.99, "score": 0.520322, "sources": ["category", "collaborative", "content"]},
    {"product_id": 52, "name": "Fantasy Pro 681", "category_id": 3, "price": 17.99, "score": 0.509836, "sources": ["category", "collaborative", "popularity"]},
    {"product_id": 127, "name": "Building Blocks Premium 126", "category_id": 7, "price": 37.99, "score": 0.368996, "sources": ["category", "collaborative", "popularity"]}
  ],
  "n_signal_products": 15, "n_user_events": 267,
  "candidate_counts": {"popularity": 30, "category": 30, "content": 30, "collaborative": 30},
  "n_candidates": 120,
  "merge_weights": {"popularity": 0.2, "category": 0.3, "content": 0.3, "collaborative": 0.2},
  "rules": ["exclude_purchased", "availability"], "n_available": 201,
  "n_after_rules": 61, "max_per_category": 2
}
```

`GET /recommendations/999999?limit=3` (nepoznat korisnik):

```
{
  "product_id": null, "method": "fallback", "fallback": true,
  "fallback_reason": "unknown_user", "returned": 3,
  "recommendations": [{"product_id": 90, "name": "Table Lamp Eco 643", "category_id": 5, "price": 23.99, "score": 2115.0, ...}, ...],
  "user_id": 999999, "rules": null, "max_per_category": 2
}
```

## CMS integracija

Shop stranica `dm-frontend/app/pages/shop/index.vue` rerankira product grid:

* Prikazuje **default poredak** (iz `/api/shop`) i **personalizovani poredak**
  za demo korisnika (poziv `GET /ml/recommendations/{user_id}` preko Nitro
  proxy-ja `/ml/**` → `:3001`).
* Toggle **Default / Personalized**: u personalized modu grid se sortira po
  hybrid preporukama (preporučeni prvi, ostali po default redosledu na kraju),
  sa bedžom i naznakom koliko se proizvoda pomerilo.
* **Graceful fallback:** ako dm-ml ne radi, `try/catch` → default poredak —
  stranica se NE ruši.
* Admin: `GET /analytics/recommendations/hybrid` prikazuje se na novoj
  admin stranici pored postojećeg Day 7 report-a (sidebar stavka).

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 8/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno (Day 8): `merge_candidates` (**normalizacija, težinski spoj, dedup,
nepoznat izvor → ValueError, svi-nula skorovi, prazan ulaz**), `score_candidate`,
`rank_candidates` (tie-break), `apply_business_rules` (dostupnost,
`exclude_ids`, prazno), `diversify_results`
(raznovrsnost bez truncate-a, fill, prazno), `recommend_for_user` (**poznat
korisnik → hybrid; nepoznat → fallback `unknown_user`; nikad tihi `[]`**;
single-source; available\_ids filter), `build_user_based_comparison` (sve metode,
nepoznata metoda → ValueError), **seeded manifest sha256**, API
(`/recommendations/{user_id}` 200/fallback/422/503).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 8/examples/demo_hybrid.py"`
   — candidate generation, merge/score/rank, biznis pravila, raznovrsnost,
   cold-start fallback i hybrid-vs-single-source comparison.
2. Pusti servis pa pitaj `GET /recommendations/395?limit=5` — uporedi sa
   `GET /recommendations/popular`, `/content/{product_id}`,
   `/collaborative/{product_id}` i ručnim osećajem „šta izgleda dobro".
3. Pitaj `GET /recommendations/999999` — fallback na popularity sa
   `unknown_user` (nikad tihi `[]`).
4. Pitaj `GET /analytics/recommendations/hybrid` — uporedi sa
   `GET /analytics/recommendations` (Day 7 session-based protokol).
5. Pokreni lab (`Day 8/lab/`) — ponovo implementiraj `merge_candidates` /
   `rank_candidates` / `apply_business_rules` / `diversify_results` na malim
   podacima i proveri `test_lab.py`.
6. Shop stranica: uključi „Personalized" i uporedi redosled sa default-om.

## Comparison (baseline ugao)

**Hybrid vs single-source** (user-based protokol, k=5, seeded, temporal split
0.8):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| **hybrid** | 0.058 | 0.054 | 0.240 | 0.064 | 0.504 |
| popularity (baseline) | **0.071** | 0.053 | **0.289** | **0.079** | **0.032** |
| category (baseline) | 0.044 | 0.040 | 0.180 | 0.049 | 0.294 |
| content (ML) | 0.044 | 0.038 | 0.190 | 0.053 | **0.794** |
| collaborative (ML) | 0.057 | 0.052 | 0.214 | 0.071 | 0.492 |

(1 293 test korisnika; target = proizvodi iz test perioda koje korisnik u train
periodu NIJE video — zato su brojevi niži nego u Day 7 session protokolu.)

Šta tabela kaže — **iskreno: hybrid ovde nije pobedio**:

* **Popularity ima najviši P@5/HR@5** (0.071 / 0.289) — kada tražimo *nove*
  proizvode za korisnika, najprodavaniji artikli su jak baseline. Cena je coverage
  3 % (uvek istih 8 proizvoda): **popularity bias**, isti kao Day 7.
* **Hybrid je drugi po preciznosti** (P@5 0.058, ≈ collaborative 0.057) uz coverage
  0.50 — 16× više kataloga od popularity. Ručne težine (0.2/0.3/0.3/0.2) daju samo
  0.2 popularity signalu; trade-off preciznost ↔ raznolikost je ovde vidljiv.
* **Category je najslabiji** (P@5 0.044) u user protokolu: korisnik je svoje
  omiljene kategorije već uglavnom „prošao" u train periodu.
* **Content ima najviši coverage** (0.794) — preporučuje ceo katalog; sam nije
  precizan. U hybrid-u njegova vrednost je pokrivanje, ne preciznost.
* Zaključak nije „hybrid ne valja", nego: **heuristične težine nisu optimizovane** —
  Day 12 / capstone (ranking model koji uči težine) je pravi sledeći korak.

**Degenerisano seme (`2.0/0.5` merge):** da ponovimo seed-ov pristup na user
nivou (collaborative × 2.0 + category + 0.5, bez normalizacije), collaborative
skorovi bi dominirali jer su na većoj skali — normalizacija je ta koja
omogućava da sadržaj i kategorija uopšte „dođu do reči". To je centralna
tehnička lekcija dana.

## Evaluacija (kako znamo da je dobro)

* **`merge_candidates` je definisan za edge case-ove:** normalizacija po izvoru,
  dedup, nepoznat izvor → ValueError, zbir težina ≤ 0 → ValueError, prazan ulaz
  → `[]` (testovi).
* **Cold-start korisnik je definisan slučaj:** nepoznat korisnik → 200 sa
  `method="fallback"`, `fallback_reason="unknown_user"`, popularity top-N —
  NIKAD tihi `[]` (test).
* **Biznis pravila su primenjena i vidljiva:** envelope nosi `rules`
  (`exclude_purchased`, `availability`), `n_available` i `n_after_rules`; lab test
  (`test_rules_and_diversity`) potvrđuje da isključeno/nedostupno ne ulazi u preporuke.
* **Raznovrsnost ne seče relevantnost:** `diversify_results` dopunjava do `k`
  (test `fill_not_truncate`).
* **Determinizam:** isti podaci + iste težine → isti izlaz (tie-break po
  `product_id`); generator je byte-for-byte (sha256 u `metadata.json`).
* **Anti-leakage:** modeli se grade iz TRAIN događaja (temporal split); test
  korisnici = istorija u oba perioda; targets = NOVI proizvodi iz test perioda.
* **Modul je importabilan** od Days 9–12 i capstone-a:
  `from app.recommenders.hybrid import recommend_for_user, build_user_based_comparison`.

## Česti bugovi

* **Scoring before merging** — rangiraš svaki izvor posebno pa konkatenišeš;
  poredak postaje artifact redosleda izvora. Rešenje: merge na normalizovanim
  skorovima PA rank (test).
* **Nema normalizacije izvora** — popularity (0..hiljade) uvek pobeđuje;
  content/collaborative (0..1) nikad ne dođu do reči. Rešenje: max-skaliranje
  po izvoru pre težinskog spoja (test).
* **Tretiranje težina kao naučenih** — `0.2/0.3/0.3/0.2` je heuristika, kao i
  seed-ov `2.0/0.5`. Rešenje: izveštaj uvek kaže koje težine su korišćene i da
  nisu naučene (DAY-BRIEFS).
* **Nema fallback-a za nepoznatog korisnika** — tihi `[]` bez objašnjenja.
  Rešenje: `fallback=True`, `fallback_reason="unknown_user"`, popularity top-N
  (test).
* **Biznis pravila kao generator** — filter (dostupnost, isključi viđeno) se
  primenjuje PRE rangiranja ili se meša sa kandidatima. Rešenje: pravila idu
  POSLE rangiranja (test).
* **Raznovrsnost koja uništi relevantnost** — isečeš listu na
  `max_per_category` pa ostane manje od `k`. Rešenje: „fill, don't truncate"
  (test).
* **Dostupnost koja ne filtrira** — freshness-prozor na seeded skupu ne bi
  filtrirao ništa (svaki proizvod ima skorašnju aktivnost). Rešenje: dostupnost
  = kvantil popularnosti (slow movers se čiste) — filtrira stvarno (~20 %).

## Šta rezultat NE dokazuje

* **Hybrid nije „najbolji" — ovde čak ni po preciznosti.** Na ovom seed-u
  popularity ima najviši P@5; hybrid je drugi, sa ~16× većim coverage-om. To je
  *svojstvo ovog skupa i ovih ručnih težina*, ne opšta istina.
* **Težine merge-a su ručno birane.** Dok ranking model ne nauči težine iz
  podataka (Day 12 / capstone), ni bolja ni lošija hybrid metrika ne dokazuje
  da su težine „tačne" ili „pogrešne" — samo kako se OVE težine ponašaju na OVOM skupu. Izveštaj kaže koje su.
* **Metrike su dataset-specifične** (sintetički seed 42, ovaj test period). Na
  pravom store-u pipeline ostaje, brojevi se menjaju.
* **Targets su ponašanje korisnika, ne preferencija.** „Korisnik je interagovao
  sa X u test periodu" ≠ „korisnik voli X". Evaluacija meri ko-interakciju u
  budućnosti, ne zadovoljstvo.
* **Isključivanje viđenog bi bio jak filter.** Najaktivniji demo korisnik (395)
  je u train periodu video 90 od 252 proizvoda; da se isključuje i viđeno (vežba),
  kandidata bi bilo znatno manje — power user „troši" katalog. Zato pipeline
  podrazumevano isključuje samo kupljeno.

## Vežbe

1. **Vary K** — pokreni comparison za `k=1`, `k=3`, `k=10` (API ili
   `build_user_based_comparison`) i uporedi redosled metoda. Šta se menja?
2. **Promeni merge težine** — npr. `{"popularity": 0.1, "category": 0.2, "content": 0.4, "collaborative": 0.3}` — kako se menja comparison? To je
   dokaz da su težine pretpostavka (weight-sensitivity na nivou merge-a).
3. **Nauči težine** — pokušaj grid-search po težinama (mali skup) i vidi da li
   postoji kombinacija koja pobeđuje category na P@5. Da li je to „naučen"
   odgovor ili i dalje heuristika? (Traženje po test skupu = overfitting.)
4. **Dodaj biznis pravilo i izmeri efekat na coverage** — npr. `max_price=100`
   — koliko coverage padne? Koji proizvodi ispadnu? Zabeleži u README.
5. **Dodaj freshness pravilo** — proizvode sa skorašnjom aktivnošću
   (window od N dana) — na seeded skupu ne filtrira (svaki proizvod je aktivan),
   ali na pravom store-u jeste. Zašto je važno da pravilo bude testirano i kad
   ne filtrira?
6. **Novi izvor u hybrid** — dodaj session-co-occurrence heuristiku (Day 6)
   kao peti generator u `generate_candidates` i uporedi hybrid pre/posle.
7. **Cold-start degradacija** — korisnik sa 1-2 događaja (tanki signal):
   kako izgledaju preporuke? Da li je to „graceful degradation"?
8. **Razmisli o ground truth** — da su targets samo `purchase` događaji (ne i
   `product_view`), kako bi se comparison promenio? (Day 7 ista vežba, sad na
   user nivou.)

## Sažetak

Napravio si **hybrid candidate-generation and ranking pipeline**: candidate
generators (popularity/category/content/collaborative) → **merge na
normalizovanim skorovima** (težine 0.2/0.3/0.3/0.2 = heuristika, ne naučen
odgovor) → **score + rank** → **biznis pravila** (dostupnost, isključi
viđeno/kupljeno) → **raznovrsnost** (fill, ne truncate) → **top-K** za
korisnika, izloženo kroz `GET /recommendations/{user_id}` i integrisano u shop
stranicu (default vs personalized poredak). Nepoznat korisnik → **fallback na
popularity** (nikad tihi `[]`). Na ovom seed-u popularity ima najviši P@5, a hybrid
je drugi po preciznosti sa ~16× većim coverage-om — iskren rezultat ručnih težina,
ne opšta istina. Centralna lekcija: **retrieval je širok i jeftin,
ranking je uzak i precizan; skorovi izvora se ne sabiraju pre normalizacije;
težine merge-a su pretpostavka dok ih ranking model ne nauči.** Pitanje danas:
**ako su težine pretpostavka, kako da ih podaci (impresije i klikovi) obore?**
— to je Day 9 (session-aware preporuke i feedback loop).

---

<!-- page_id 427 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/candidates.csv

```
user_id,source,product_id,score,rank_in_source
395,popularity,90,1708.0,1
395,popularity,110,1523.0,2
395,popularity,184,1493.0,3
395,popularity,12,1447.0,4
395,popularity,231,1419.0,5
395,popularity,49,1407.0,6
395,popularity,76,1407.0,7
395,popularity,200,1265.0,8
395,popularity,85,1254.0,9
395,popularity,148,1246.0,10
395,popularity,127,1237.0,11
395,popularity,30,1171.0,12
395,popularity,41,1086.0,13
395,popularity,243,1074.0,14
395,popularity,2,978.0,15
395,popularity,37,942.0,16
395,popularity,52,938.0,17
395,popularity,177,930.0,18
395,popularity,80,897.0,19
395,popularity,223,881.0,20
395,popularity,133,867.0,21
395,popularity,160,867.0,22
395,popularity,93,822.0,23
395,popularity,9,816.0,24
395,popularity,198,793.0,25
395,popularity,181,753.0,26
395,popularity,125,736.0,27
395,popularity,74,702.0,28
395,popularity,105,690.0,29
395,popularity,60,680.0,30
395,category,49,133665.0,1
395,category,52,89110.0,2
395,category,60,64600.0,3
395,category,63,48640.0,4
395,category,44,48165.0,5
395,category,127,43295.0,6
395,category,50,35245.0,7
395,category,43,32395.0,8
395,category,200,30360.0,9
395,category,133,30345.0,10
395,category,231,28380.0,11
395,category,55,24035.0,12
395,category,61,23180.0,13
395,category,59,21660.0,14
395,category,137,21350.0,15
395,category,56,20045.0,16
395,category,46,19570.0,17
395,category,198,19032.0,18
395,category,223,17620.0,19
395,category,62,17100.0,20
395,category,51,16245.0,21
395,category,45,15865.0,22
395,category,90,15372.0,23
395,category,132,14525.0,24
395,category,57,14440.0,25
395,category,53,14155.0,26
395,category,58,14155.0,27
395,category,206,13584.0,28
395,category,224,12760.0,29
395,category,48,12445.0,30
395,content,50,31.618385,1
395,content,59,20.610173,2
395,content,138,19.967624,3
395,content,48,19.424403,4
395,content,47,18.804004,5
395,content,192,14.14261,6
395,content,217,14.058999,7
395,content,128,13.987943,8
395,content,206,13.778616,9
395,content,134,12.800147,10
395,content,201,12.353551,11
395,content,51,12.022792,12
395,content,100,11.607937,13
395,content,218,11.189489,14
395,content,207,11.142163,15
395,content,58,10.797688,16
395,content,53,10.418772,17
395,content,44,10.278076,18
395,content,62,10.168264,19
395,content,49,9.69982,20
395,content,135,9.593364,21
395,content,229,9.191767,22
395,content,143,9.129743,23
395,content,5,8.930382,24
395,content,26,8.890798,25
395,content,142,8.409624,26
395,content,104,8.275459,27
395,content,55,8.209682,28
395,content,161,8.066605,29
395,content,54,7.651733,30
395,collaborative,52,30.302155,1
395,collaborative,60,24.368056,2
395,collaborative,44,24.29665,3
395,collaborative,63,21.810143,4
395,collaborative,49,21.407457,5
395,collaborative,50,21.39593,6
395,collaborative,127,19.238205,7
395,collaborative,43,19.098149,8
395,collaborative,133,18.943987,9
395,collaborative,56,17.127174,10
395,collaborative,61,16.174849,11
395,collaborative,55,16.025989,12
395,collaborative,59,15.126224,13
395,collaborative,45,14.606882,14
395,collaborative,62,13.582404,15
395,collaborative,132,13.552061,16
395,collaborative,134,13.298294,17
395,collaborative,46,13.186578,18
395,collaborative,137,12.647138,19
395,collaborative,51,12.517393,20
395,collaborative,141,12.224179,21
395,collaborative,47,11.943126,22
395,collaborative,53,11.893611,23
395,collaborative,57,11.730913,24
395,collaborative,140,11.590489,25
395,collaborative,58,11.437818,26
395,collaborative,223,11.40628,27
395,collaborative,54,11.224593,28
395,collaborative,142,11.009056,29
395,collaborative,224,10.670912,30
1465,popularity,90,1708.0,1
1465,popularity,110,1523.0,2
1465,popularity,184,1493.0,3
1465,popularity,12,1447.0,4
1465,popularity,231,1419.0,5
1465,popularity,49,1407.0,6
1465,popularity,76,1407.0,7
1465,popularity,200,1265.0,8
1465,popularity,85,1254.0,9
1465,popularity,148,1246.0,10
1465,popularity,127,1237.0,11
1465,popularity,30,1171.0,12
1465,popularity,41,1086.0,13
1465,popularity,243,1074.0,14
1465,popularity,2,978.0,15
1465,popularity,37,942.0,16
1465,popularity,52,938.0,17
1465,popularity,177,930.0,18
1465,popularity,80,897.0,19
1465,popularity,223,881.0,20
1465,popularity,133,867.0,21
1465,popularity,160,867.0,22
1465,popularity,93,822.0,23
1465,popularity,9,816.0,24
1465,popularity,198,793.0,25
1465,popularity,181,753.0,26
1465,popularity,125,736.0,27
1465,popularity,74,702.0,28
1465,popularity,105,690.0,29
1465,popularity,60,680.0,30
1465,category,30,108903.0,1
1465,category,41,100998.0,2
1465,category,37,87606.0,3
1465,category,110,50259.0,4
1465,category,31,49290.0,5
1465,category,36,35712.0,6
1465,category,23,35526.0,7
1465,category,39,34689.0,8
1465,category,27,31899.0,9
1465,category,32,29853.0,10
1465,category,38,29760.0,11
1465,category,40,29016.0,12
1465,category,34,27156.0,13
1465,category,76,26733.0,14
1465,category,125,24288.0,15
1465,category,22,23064.0,16
1465,category,29,21855.0,17
1465,category,25,20925.0,18
1465,category,118,20394.0,19
1465,category,26,20367.0,20
1465,category,33,20274.0,21
1465,category,123,18942.0,22
1465,category,35,18414.0,23
1465,category,121,17589.0,24
1465,category,80,17043.0,25
1465,category,24,16554.0,26
1465,category,28,14229.0,27
1465,category,108,13959.0,28
1465,category,74,13338.0,29
1465,category,107,12243.0,30
1465,content,38,16.727519,1
1465,content,34,16.58405,2
1465,content,27,16.349764,3
1465,content,119,15.982324,4
1465,content,40,15.387548,5
1465,content,36,15.386289,6
1465,content,31,14.895518,7
1465,content,30,14.042125,8
1465,content,111,13.989987,9
1465,content,81,13.009581,10
1465,content,42,12.91585,11
1465,content,168,12.584696,12
1465,content,23,12.458416,13
1465,content,126,12.402647,14
1465,content,166,12.366854,15
1465,content,32,12.039983,16
1465,content,115,10.895345,17
1465,content,75,9.755453,18
1465,content,39,9.234394,19
1465,content,86,7.525058,20
1465,content,184,7.450636,21
1465,content,41,7.387548,22
1465,content,63,7.253298,23
1465,content,176,7.210976,24
1465,content,11,7.089519,25
1465,content,157,7.047518,26
1465,content,91,6.958431,27
1465,content,109,6.939017,28
1465,content,67,6.808454,29
1465,content,26,6.777917,30
1465,collaborative,30,21.39151,1
1465,collaborative,31,20.105435,2
1465,collaborative,41,19.921884,3
1465,collaborative,37,19.735609,4
1465,collaborative,32,16.800671,5
1465,collaborative,39,16.432814,6
1465,collaborative,38,15.71529,7
1465,collaborative,110,15.632698,8
1465,collaborative,27,14.683516,9
1465,collaborative,76,14.397138,10
1465,collaborative,23,14.189334,11
1465,collaborative,36,14.14901,12
1465,collaborative,123,13.735382,13
1465,collaborative,40,13.734093,14
1465,collaborative,121,13.502221,15
1465,collaborative,34,13.221342,16
1465,collaborative,125,13.178449,17
1465,collaborative,118,12.39152,18
1465,collaborative,35,12.111554,19
1465,collaborative,29,12.096636,20
1465,collaborative,33,12.075977,21
1465,collaborative,25,11.795938,22
1465,collaborative,114,11.308354,23
1465,collaborative,24,11.282888,24
1465,collaborative,107,10.611157,25
1465,collaborative,111,9.944607,26
1465,collaborative,80,9.843158,27
1465,collaborative,115,9.839374,28
1465,collaborative,108,9.525294,29
1465,collaborative,74,9.393243,30
409,popularity,90,1708.0,1
409,popularity,110,1523.0,2
409,popularity,184,1493.0,3
409,popularity,12,1447.0,4
409,popularity,231,1419.0,5
409,popularity,49,1407.0,6
409,popularity,76,1407.0,7
409,popularity,200,1265.0,8
409,popularity,85,1254.0,9
409,popularity,148,1246.0,10
409,popularity,127,1237.0,11
409,popularity,30,1171.0,12
409,popularity,41,1086.0,13
409,popularity,243,1074.0,14
409,popularity,2,978.0,15
409,popularity,37,942.0,16
409,popularity,52,938.0,17
409,popularity,177,930.0,18
409,popularity,80,897.0,19
409,popularity,223,881.0,20
409,popularity,133,867.0,21
409,popularity,160,867.0,22
409,popularity,93,822.0,23
409,popularity,9,816.0,24
409,popularity,198,793.0,25
409,popularity,181,753.0,26
409,popularity,125,736.0,27
409,popularity,74,702.0,28
409,popularity,105,690.0,29
409,popularity,60,680.0,30
409,category,127,66798.0,1
409,category,133,46818.0,2
409,category,137,32940.0,3
409,category,200,27830.0,4
409,category,132,22410.0,5
409,category,49,21105.0,6
409,category,90,20496.0,7
409,category,198,17446.0,8
409,category,134,16794.0,9
409,category,141,16416.0,10
409,category,142,16308.0,11
409,category,140,15822.0,12
409,category,85,15048.0,13
409,category,243,15036.0,14
409,category,52,14070.0,15
409,category,136,13176.0,16
409,category,206,12452.0,17
409,category,129,12042.0,18
409,category,143,11556.0,19
409,category,60,10200.0,20
409,category,93,9864.0,21
409,category,145,9720.0,22
409,category,193,9570.0,23
409,category,30,9368.0,24
409,category,41,8688.0,25
409,category,138,8532.0,26
409,category,135,8370.0,27
409,category,131,8316.0,28
409,category,105,8280.0,29
409,category,147,7992.0,30
409,content,139,14.928121,1
409,content,233,13.204323,2
409,content,135,12.512457,3
409,content,136,11.929199,4
409,content,128,10.889016,5
409,content,50,10.812137,6
409,content,191,10.44989,7
409,content,143,9.722876,8
409,content,40,9.308473,9
409,content,202,9.297173,10
409,content,89,8.32092,11
409,content,44,7.92819,12
409,content,133,7.638054,13
409,content,207,7.627581,14
409,content,88,7.014349,15
409,content,193,6.553968,16
409,content,131,6.240364,17
409,content,206,6.198994,18
409,content,192,5.955518,19
409,content,23,5.787244,20
409,content,130,5.382637,21
409,content,205,5.09015,22
409,content,25,4.864075,23
409,content,243,4.827789,24
409,content,145,4.824065,25
409,content,138,4.791709,26
409,content,137,4.750353,27
409,content,100,4.713842,28
409,content,129,4.683026,29
409,content,217,4.676335,30
409,collaborative,133,11.370559,1
409,collaborative,127,9.960657,2
409,collaborative,137,9.651999,3
409,collaborative,52,8.317284,4
409,collaborative,134,8.145341,5
409,collaborative,132,7.702349,6
409,collaborative,63,6.791915,7
409,collaborative,60,6.683201,8
409,collaborative,136,6.568457,9
409,collaborative,141,6.40709,10
409,collaborative,140,6.360035,11
409,collaborative,200,6.306966,12
409,collaborative,143,5.93009,13
409,collaborative,142,5.887361,14
409,collaborative,44,5.864144,15
409,collaborative,139,5.854735,16
409,collaborative,50,5.840743,17
409,collaborative,243,5.786142,18
409,collaborative,49,5.705643,19
409,collaborative,138,5.457343,20
409,collaborative,135,5.419911,21
409,collaborative,144,5.286935,22
409,collaborative,61,5.215686,23
409,collaborative,145,5.008501,24
409,collaborative,129,4.946662,25
409,collaborative,128,4.891634,26
409,collaborative,198,4.889098,27
409,collaborative,247,4.85445,28
409,collaborative,55,4.503932,29
409,collaborative,146,4.49332,30
1182,popularity,90,1708.0,1
1182,popularity,110,1523.0,2
1182,popularity,184,1493.0,3
1182,popularity,12,1447.0,4
1182,popularity,231,1419.0,5
1182,popularity,49,1407.0,6
1182,popularity,76,1407.0,7
1182,popularity,200,1265.0,8
1182,popularity,85,1254.0,9
1182,popularity,148,1246.0,10
1182,popularity,127,1237.0,11
1182,popularity,30,1171.0,12
1182,popularity,41,1086.0,13
1182,popularity,243,1074.0,14
1182,popularity,2,978.0,15
1182,popularity,37,942.0,16
1182,popularity,52,938.0,17
1182,popularity,177,930.0,18
1182,popularity,80,897.0,19
1182,popularity,223,881.0,20
1182,popularity,133,867.0,21
1182,popularity,160,867.0,22
1182,popularity,93,822.0,23
1182,popularity,9,816.0,24
1182,popularity,198,793.0,25
1182,popularity,181,753.0,26
1182,popularity,125,736.0,27
1182,popularity,74,702.0,28
1182,popularity,105,690.0,29
1182,popularity,60,680.0,30
1182,category,12,125889.0,1
1182,category,2,85086.0,2
1182,category,9,70992.0,3
1182,category,6,42108.0,4
1182,category,17,40281.0,5
1182,category,200,34155.0,6
1182,category,13,31842.0,7
1182,category,10,29754.0,8
1182,category,7,28710.0,9
1182,category,15,23925.0,10
1182,category,14,23142.0,11
1182,category,198,21411.0,12
1182,category,21,21141.0,13
1182,category,30,21078.0,14
1182,category,1,20271.0,15
1182,category,41,19548.0,16
1182,category,19,18096.0,17
1182,category,20,17487.0,18
1182,category,37,16956.0,19
1182,category,206,15282.0,20
1182,category,8,15138.0,21
1182,category,16,14877.0,22
1182,category,3,14790.0,23
1182,category,5,14268.0,24
1182,category,231,14190.0,25
1182,category,110,13707.0,26
1182,category,184,13437.0,27
1182,category,11,12093.0,28
1182,category,193,11745.0,29
1182,category,4,11397.0,30
1182,content,1,24.163058,1
1182,content,9,18.35731,2
1182,content,18,18.048387,3
1182,content,37,16.875436,4
1182,content,8,15.751739,5
1182,content,10,12.799803,6
1182,content,204,12.44529,7
1182,content,40,11.175743,8
1182,content,213,11.126338,9
1182,content,207,10.81516,10
1182,content,5,10.604076,11
1182,content,182,9.538106,12
1182,content,123,9.181154,13
1182,content,21,8.601918,14
1182,content,17,8.531381,15
1182,content,174,8.501189,16
1182,content,176,8.306015,17
1182,content,19,8.281602,18
1182,content,3,8.158479,19
1182,content,241,7.754607,20
1182,content,7,7.737026,21
1182,content,100,7.65293,22
1182,content,157,7.542367,23
1182,content,22,7.500102,24
1182,content,38,7.489818,25
1182,content,194,7.485225,26
1182,content,63,7.450433,27
1182,content,201,7.037071,28
1182,content,45,7.029085,29
1182,content,114,7.015395,30
1182,collaborative,12,22.128855,1
1182,collaborative,9,16.557784,2
1182,collaborative,2,16.051502,3
1182,collaborative,6,14.656589,4
1182,collaborative,17,13.598075,5
1182,collaborative,7,12.579947,6
1182,collaborative,13,12.35988,7
1182,collaborative,10,11.878427,8
1182,collaborative,15,11.341101,9
1182,collaborative,14,10.978098,10
1182,collaborative,21,10.504885,11
1182,collaborative,16,10.389402,12
1182,collaborative,19,10.336046,13
1182,collaborative,20,10.239971,14
1182,collaborative,4,10.058374,15
1182,collaborative,231,9.986261,16
1182,collaborative,1,9.92439,17
1182,collaborative,200,9.540378,18
1182,collaborative,3,9.535347,19
1182,collaborative,8,9.162976,20
1182,collaborative,198,8.879239,21
1182,collaborative,5,8.681694,22
1182,collaborative,18,8.359801,23
1182,collaborative,223,7.963658,24
1182,collaborative,11,7.945604,25
1182,collaborative,224,7.107187,26
1182,collaborative,230,6.879564,27
1182,collaborative,193,6.696645,28
1182,collaborative,208,6.6824,29
1182,collaborative,196,6.123807,30
2360,popularity,90,1708.0,1
2360,popularity,110,1523.0,2
2360,popularity,184,1493.0,3
2360,popularity,12,1447.0,4
2360,popularity,231,1419.0,5
2360,popularity,49,1407.0,6
2360,popularity,76,1407.0,7
2360,popularity,200,1265.0,8
2360,popularity,85,1254.0,9
2360,popularity,148,1246.0,10
2360,popularity,127,1237.0,11
2360,popularity,30,1171.0,12
2360,popularity,41,1086.0,13
2360,popularity,243,1074.0,14
2360,popularity,2,978.0,15
2360,popularity,37,942.0,16
2360,popularity,52,938.0,17
2360,popularity,177,930.0,18
2360,popularity,80,897.0,19
2360,popularity,223,881.0,20
2360,popularity,133,867.0,21
2360,popularity,160,867.0,22
2360,popularity,93,822.0,23
2360,popularity,9,816.0,24
2360,popularity,198,793.0,25
2360,popularity,181,753.0,26
2360,popularity,125,736.0,27
2360,popularity,74,702.0,28
2360,popularity,105,690.0,29
2360,popularity,60,680.0,30
2360,category,90,49532.0,1
2360,category,76,36582.0,2
2360,category,85,36366.0,3
2360,category,184,32846.0,4
2360,category,93,23838.0,5
2360,category,80,23322.0,6
2360,category,177,20460.0,7
2360,category,105,20010.0,8
2360,category,74,18252.0,9
2360,category,103,18125.0,10
2360,category,181,16566.0,11
2360,category,87,13601.0,12
2360,category,148,12460.0,13
2360,category,68,11830.0,14
2360,category,86,11571.0,15
2360,category,200,11385.0,16
2360,category,88,11049.0,17
2360,category,185,10406.0,18
2360,category,65,10400.0,19
2360,category,182,10076.0,20
2360,category,75,10062.0,21
2360,category,95,9860.0,22
2360,category,94,9657.0,23
2360,category,160,8670.0,24
2360,category,66,8658.0,25
2360,category,175,8558.0,26
2360,category,89,8526.0,27
2360,category,67,8294.0,28
2360,category,73,8112.0,29
2360,category,169,8030.0,30
2360,content,77,13.034211,1
2360,content,99,11.851775,2
2360,content,177,11.172632,3
2360,content,151,9.845525,4
2360,content,210,8.989078,5
2360,content,195,8.405898,6
2360,content,183,7.851005,7
2360,content,70,7.589654,8
2360,content,170,7.229039,9
2360,content,206,6.804508,10
2360,content,73,6.568386,11
2360,content,69,6.503234,12
2360,content,85,6.280966,13
2360,content,207,6.280181,14
2360,content,84,5.779182,15
2360,content,87,5.587025,16
2360,content,89,5.555899,17
2360,content,189,5.156522,18
2360,content,86,5.127329,19
2360,content,174,4.702609,20
2360,content,127,4.607493,21
2360,content,176,4.420703,22
2360,content,134,4.049168,23
2360,content,157,3.719765,24
2360,content,63,3.694071,25
2360,content,188,3.623327,26
2360,content,22,3.610374,27
2360,content,91,3.576709,28
2360,content,180,3.523004,29
2360,content,212,3.436481,30
2360,collaborative,85,7.372164,1
2360,collaborative,80,7.097138,2
2360,collaborative,90,6.783724,3
2360,collaborative,74,6.654121,4
2360,collaborative,105,6.571527,5
2360,collaborative,177,6.518287,6
2360,collaborative,93,6.373787,7
2360,collaborative,148,6.213552,8
2360,collaborative,181,6.123389,9
2360,collaborative,87,5.700024,10
2360,collaborative,88,5.67922,11
2360,collaborative,75,5.624638,12
2360,collaborative,65,5.513441,13
2360,collaborative,86,5.445784,14
2360,collaborative,160,5.35544,15
2360,collaborative,103,5.239712,16
2360,collaborative,68,5.074729,17
2360,collaborative,184,5.050264,18
2360,collaborative,96,5.007086,19
2360,collaborative,77,4.920176,20
2360,collaborative,94,4.892221,21
2360,collaborative,66,4.837711,22
2360,collaborative,185,4.69433,23
2360,collaborative,67,4.675535,24
2360,collaborative,101,4.545281,25
2360,collaborative,95,4.508121,26
2360,collaborative,175,4.434858,27
2360,collaborative,73,4.351658,28
2360,collaborative,64,4.317676,29
2360,collaborative,78,4.310573,30
```

### data/comparison.csv

```
method,precision_at_k,recall_at_k,hit_rate_at_k,ndcg_at_k,catalog_coverage
hybrid,0.058469,0.054208,0.239753,0.064345,0.503968
popularity,0.071307,0.052988,0.28925,0.079087,0.031746
category,0.043619,0.040365,0.180201,0.048559,0.293651
content,0.043929,0.037665,0.190255,0.052932,0.793651
collaborative,0.057077,0.051523,0.21423,0.070652,0.492063
```

### data/metadata.json

```
{
  "dataset": "dm_hybrid_pipeline_v1",
  "description": "Seeded hybrid candidate-generation and ranking artifacts. candidates.csv = per-source candidates (recall phase) for demo users; ranking.csv = final hybrid ranking after merge/score/business-rules/diversity; comparison.csv = hybrid vs single-source recommenders on a USER-BASED protocol (temporal split, Day 7 metrics). Models are built from TRAIN events only (anti-leakage).",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "products": "Day 5/data/products_text.csv",
    "module": "app.data.generate_hybrid",
    "function": "generate_hybrid",
    "pipeline_module": "app.recommenders.hybrid",
    "split_function": "app.recommenders.evaluation.temporal_split",
    "metric_functions": "app.recommenders.evaluation"
  },
  "parameters": {
    "k": 5,
    "split_ratio": 0.8,
    "split_time": "2026-01-26 11:21:20",
    "candidate_limit": 30,
    "signal_limit": 15,
    "merge_weights": {
      "popularity": 0.2,
      "category": 0.3,
      "content": 0.3,
      "collaborative": 0.2
    },
    "availability_quantile": 0.2,
    "available_ids_count": 201,
    "max_test_users": null,
    "demo_user_ids": [
      395,
      1465,
      409,
      1182,
      2360
    ],
    "user_protocol": "test users = users with history in both train and test; targets = distinct products from TEST period NOT in the user's train history; metrics = Day 7 P@K/R@K/HR@K/NDCG@K + catalog coverage"
  },
  "columns": {
    "candidates.csv": {
      "user_id": "int, korisnik (Day 1 kolona) — red evaluacije",
      "source": "str, izvor kandidata (popularity/category/content/collaborative)",
      "product_id": "int, stabilan ID proizvoda",
      "score": "float, SIROV skor izvora (pre normalizacije merge-a)",
      "rank_in_source": "int, pozicija u rangiranoj listi izvora (1=top)"
    },
    "ranking.csv": {
      "user_id": "int, korisnik",
      "position": "int, finalna pozicija (1=prva preporuka)",
      "product_id": "int, preporučeni proizvod",
      "name": "str, naziv proizvoda (katalog)",
      "category_id": "int, kategorija (za raznovrsnost)",
      "score": "float, merged blended skor (Σ w·normalizovani skor)",
      "sources": "str, izvori koji su predložili proizvod (';'-spojeni)"
    },
    "comparison.csv": {
      "method": "str, hybrid ili single izvor (popularity/category/content/collaborative)",
      "precision_at_k": "float, P@K (user-based protokol)",
      "recall_at_k": "float, R@K",
      "hit_rate_at_k": "float, HR@K",
      "ndcg_at_k": "float, NDCG@K",
      "catalog_coverage": "float, distinct preporučenih / katalog"
    }
  },
  "counts": {
    "n_train_events": 146774,
    "n_test_events": 36694,
    "n_test_users": 1293,
    "n_candidate_rows": 600,
    "n_ranking_rows": 25,
    "n_catalog": 252,
    "profiles": {
      "395": {
        "n_train_events": 267,
        "n_train_products": 90,
        "n_purchases": 5
      },
      "1465": {
        "n_train_events": 229,
        "n_train_products": 77,
        "n_purchases": 4
      },
      "409": {
        "n_train_events": 227,
        "n_train_products": 108,
        "n_purchases": 5
      },
      "1182": {
        "n_train_events": 214,
        "n_train_products": 98,
        "n_purchases": 11
      },
      "2360": {
        "n_train_events": 182,
        "n_train_products": 95,
        "n_purchases": 4
      }
    }
  },
  "comparison": [
    {
      "method": "hybrid",
      "precision_at_k": 0.058469,
      "recall_at_k": 0.054208,
      "hit_rate_at_k": 0.239753,
      "ndcg_at_k": 0.064345,
      "catalog_coverage": 0.503968
    },
    {
      "method": "popularity",
      "precision_at_k": 0.071307,
      "recall_at_k": 0.052988,
      "hit_rate_at_k": 0.28925,
      "ndcg_at_k": 0.079087,
      "catalog_coverage": 0.031746
    },
    {
      "method": "category",
      "precision_at_k": 0.043619,
      "recall_at_k": 0.040365,
      "hit_rate_at_k": 0.180201,
      "ndcg_at_k": 0.048559,
      "catalog_coverage": 0.293651
    },
    {
      "method": "content",
      "precision_at_k": 0.043929,
      "recall_at_k": 0.037665,
      "hit_rate_at_k": 0.190255,
      "ndcg_at_k": 0.052932,
      "catalog_coverage": 0.793651
    },
    {
      "method": "collaborative",
      "precision_at_k": 0.057077,
      "recall_at_k": 0.051523,
      "hit_rate_at_k": 0.21423,
      "ndcg_at_k": 0.070652,
      "catalog_coverage": 0.492063
    }
  ],
  "weights_note": "merge weights are hand-picked heuristics (0.2/0.3/0.3/0.2), NOT learned — DAY-BRIEFS 'What the result does NOT prove'.",
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "candidates.csv": "e3109120a610bcc37f3a970c26a42e2843434485077cd56fc21a7790eccd0151",
      "ranking.csv": "71bcf949149d731dbf5c3b5294afda5e9f41a1dc373bbffaa9ebd1fb07b3305d",
      "comparison.csv": "30d5ea6b9601e6d2d134391f579d3e846ccfa571a3da961b742c168d0762ae9e"
    }
  }
}
```

### data/ranking.csv

```
user_id,position,product_id,name,category_id,score,sources
395,1,50,Biography Essential 819,3,0.520321695,category;collaborative;content
395,2,52,Fantasy Pro 681,3,0.509836066,category;collaborative;popularity
395,3,127,Building Blocks Premium 126,7,0.36899563,category;collaborative;popularity
395,4,133,Doll Eco 977,7,0.294663008,category;collaborative;popularity
395,5,90,Table Lamp Eco 643,5,0.234501178,category;popularity
1465,1,30,T-shirt Everyday 987,2,0.888958189,category;collaborative;content;popularity
1465,2,41,Boots Compact 911,2,0.72414186,category;collaborative;content;popularity
1465,3,110,Shampoo Everyday 111,6,0.462945934,category;collaborative;popularity
1465,4,76,Tennis Racket Compact 416,4,0.373002791,category;collaborative;popularity
1465,5,111,Shampoo Classic 190,6,0.343880821,collaborative;content
409,1,133,Doll Eco 977,7,0.665285648,category;collaborative;content;popularity
409,2,127,Building Blocks Premium 126,7,0.620048607,category;collaborative;popularity
409,3,243,Ladder Deluxe 713,12,0.392084888,category;collaborative;content;popularity
409,4,200,Floor Mats Everyday 949,10,0.384050257,category;collaborative;popularity
409,5,49,Biography Deluxe 648,3,0.35989805,category;collaborative;popularity
1182,1,12,Keyboard Classic 505,1,0.669437939,category;collaborative;popularity
1182,2,1,Smartphone Compact 686,1,0.438003213,category;collaborative;content
1182,3,37,Backpack Compact 926,2,0.360230932,category;content;popularity
1182,4,200,Floor Mats Everyday 949,10,0.315745277,category;collaborative;popularity
1182,5,231,Studio Headphones Classic 686,11,0.290230315,category;collaborative;popularity
2360,1,85,Blender Classic 334,5,0.711660949,category;collaborative;content;popularity
2360,2,90,Table Lamp Eco 643,5,0.684036166,category;collaborative;popularity
2360,3,177,Bed Frame Eco 577,9,0.666807534,category;collaborative;content;popularity
2360,4,184,Nightstand Everyday 721,9,0.510771414,category;collaborative;popularity
2360,5,80,Fitness Band Eco 108,4,0.438828066,category;collaborative;popularity
```

### data/README.md

# Day 8 podaci — hybrid candidate/ranking derivati (candidates + ranking + comparison)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, težine, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `candidates.csv` | kandidati PO IZVORU (recall faza) za 5 demo korisnika: `user_id`, `source`, `product_id`, `score`, `rank_in_source` | 600 |
| `ranking.csv` | finalni hybrid ranking (posle merge/score/biznis pravila/raznovrsnosti) za iste korisnike | 25 |
| `comparison.csv` | **hybrid vs single-source** (user-based protokol): P@K / R@K / HR@K / NDCG@K / coverage | 5 |
| `metadata.json` | izvor, parametri, težine, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (istorija) + `Day 5/data/products_text.csv`
  (katalog).
* **Temporal split** (`temporal_split`, `app/recommenders/evaluation.py`):
  granica = kvantil 0.8 (`2026-01-30 15:26:05`); modeli se grade SAMO na train
  događajima (anti-leakage, Day 7 lekcija).
* **Candidates** (`generate_candidates`): popularity/category/content/
  collaborative — svaki izvor predlaže do 30 kandidata (retrieval je
  recall-orijentisan).
* **Ranking** (`recommend_for_user`): merge na normalizovanim skorovima
  (težine `0.2/0.3/0.3/0.2` — **heuristika, ne naučen odgovor**), rank, biznis
  pravila (dostupnost = slow movers se čiste, isključi viđeno/kupljeno),
  raznovrsnost (`max_per_category=2`).
* **Comparison** (`build_user_based_comparison`): test korisnici = sa istorijom
  u train i test periodu; `targets` = NOVI proizvodi iz test perioda (van
  train istorije). Metrike su Day 7 P@K/R@K/HR@K/NDCG@K + coverage.
* Generator: `app/data/generate_hybrid.py` (upisuje CSV + metadata).

## Ključne kolone (`ranking.csv`)

| Kolona | Značenje |
| --- | --- |
| `user_id` | korisnik (Day 1) — red evaluacije |
| `position` | finalna pozicija (1 = prva preporuka) |
| `product_id` | preporučeni proizvod |
| `name` | naziv (katalog) |
| `category_id` | kategorija (ulaz u raznovrsnost) |
| `score` | merged blended skor (Σ težina × normalizovani skor izvora) |
| `sources` | izvori koji su predložili proizvod, `;`-spojeni |

## Stanje u ovom seed-u

* split\_time: **2026-01-26 11:21:20** · train: **146 774** · test: **36 694**
* test korisnika (user-based protokol): **1 293** · demo korisnici:
  **395, 1465, 409, 1182, 2360**
* dostupnih proizvoda (biznis pravilo, kvantil 0.2 popularnosti): **201 / 252**

Comparison (user-based, k=5):

| Metod | P@5 | R@5 | HR@5 | NDCG@5 | coverage |
| --- | --- | --- | --- | --- | --- |
| hybrid | 0.058 | 0.054 | 0.240 | 0.064 | 0.504 |
| popularity | 0.071 | 0.053 | 0.289 | 0.079 | 0.032 |
| category | 0.044 | 0.040 | 0.180 | 0.049 | 0.294 |
| content | 0.044 | 0.038 | 0.190 | 0.053 | 0.794 |
| collaborative | 0.057 | 0.052 | 0.214 | 0.071 | 0.492 |

Iskren rezultat: na ovom seed-u hybrid (heuristične težine) **nije** bolji od
najboljeg pojedinačnog signala po preciznosti — vidi lekciju, „Šta rezultat NE dokazuje".

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_hybrid
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`). `candidates.csv` ne zavisi od biznis
pravila (sirovi kandidati), pa njegov sha256 ostaje isti i kad se pravila
promene — samo `ranking.csv`/`comparison.csv` reaguju.

## Šta ovi podaci NE dokazuju

* **Hybrid nije „najbolji" na svakoj metrici.** Na ovom seed-u category ima
  najviši P@5 (sesije ostaju u kategoriji — isto kao Day 7), a hybrid je
  drugi po preciznosti ali sa višim coverage-om (0.73 vs 0.65). To je
  *svojstvo ovog skupa*, ne opšta istina.
* **Težine merge-a su ručno birane.** `0.2/0.3/0.3/0.2` je heuristika; dok
  ranking model ne nauči težine, bolja hybrid metrika ne dokazuje da su težine
  „tačne".
* **Metrike su dataset-specifične** (sintetički seed 42, ovaj test period). Na
  pravom store-u raspodela je drugačija.

### examples/demo\_hybrid.py

```
"""Demo: hybrid candidate-generation and ranking pipeline (Day 8).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 8/examples/demo_hybrid.py"

Prikazuje:
  1) **candidate generation** — per izvor (popularity/category/content/
     collaborative), recall-orijentisana faza;
  2) **merge -> score -> rank** — normalizacija izvora i blended skor
     (težine = heuristika, ne naučen odgovor);
  3) **biznis pravila** — dostupnost (slow movers) + isključi viđeno/kupljeno;
  4) **raznovrsnost** — finalna lista;
  5) **cold-start fallback** — nepoznat korisnik -> popularity (nikad tihi []);
  6) **hybrid vs single-source comparison** (user-based protokol, Day 7 metrike).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.hybrid import DEMO_USER_IDS, HybridRecommenderService

DEMO_USER = DEMO_USER_IDS[0]  # 395 — najaktivniji korisnik


def _ids(records: list[dict]) -> str:
    return ",".join(str(r["product_id"]) for r in records)


def _scores(records: list[dict]) -> str:
    return ", ".join(f"{r['product_id']}({r['score']:.3f})" for r in records)


def main() -> None:
    print("=== Day 8 — Hybrid Candidate-Generation and Ranking Pipeline ===\n")
    svc = HybridRecommenderService()

    # --- 1) Candidate generation -------------------------------------------- #
    print(f"[1] Candidate generation (recall) za korisnika {DEMO_USER}:")
    res = svc.recommend_for_user(DEMO_USER, limit=5, include_pipeline=True)
    pipe = res["pipeline"]
    print(f"    signal proizvoda: {res['n_signal_products']}  "
          f"događaja u train: {res['n_user_events']}")
    print(f"    kandidata po izvoru: {res['candidate_counts']}")
    print(f"    ukupno pre merge-a: {pipe['n_candidates_before_merge']}  ->  "
          f"merged: {pipe['n_merged']}")
    print()

    # --- 2) Merge + score + rank -------------------------------------------- #
    print("[2] Merge -> score -> rank (normalizovani skorovi, težine "
          f"{svc.merge_weights}):")
    print(f"    težine su HEURISTIKA, ne naučen odgovor (DAY-BRIEFS).")
    for r in res["recommendations"]:
        print(f"      #{res['recommendations'].index(r) + 1}  {r['product_id']:>3}  "
              f"{r['name']:<22} score={r['score']:.4f}  "
              f"sources=[{';'.join(r['sources'])}]")
    print()

    # --- 3) Business rules --------------------------------------------------- #
    print(f"[3] Biznis pravila posle rangiranja: {res['rules']}")
    print(f"    removed: {pipe['n_removed_by_rules']}  preostalo: "
          f"{pipe['n_after_rules']}  (exclude_purchased + availability)")
    print()

    # --- 4) Diversity -------------------------------------------------------- #
    print(f"[4] Raznovrsnost (max_per_category={res['max_per_category']}): "
          f"finalna lista {_ids(res['recommendations'])}")
    print()

    # --- 5) Cold-start fallback ---------------------------------------------- #
    print("[5] Cold-start fallback (nepoznat korisnik 99999):")
    cs = svc.recommend_for_user(99999, limit=5)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-5: "
          f"{_ids(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 6) Hybrid vs single-source ------------------------------------------ #
    print("[6] Hybrid vs single-source (user-based protokol, Day 7 metrike):")
    print(f"    {'method':<14} {'P@5':>7} {'R@5':>7} {'HR@5':>7} "
          f"{'NDCG@5':>8} {'coverage':>9}")
    # brži podskup za demo (pun report je u Day 8/data/comparison.csv i na
    # GET /analytics/recommendations/hybrid)
    rep = svc.user_based_comparison(k=5, max_test_users=200)
    for row in rep["comparison"]:
        print(
            f"    {row['method']:<14} {row['precision_at_k']:>7.4f} "
            f"{row['recall_at_k']:>7.4f} {row['hit_rate_at_k']:>7.4f} "
            f"{row['ndcg_at_k']:>8.4f} {row['catalog_coverage']:>9.4f}"
        )
    print(f"    (test korisnika: {rep['n_test_users']}; pun izveštaj — "
          f"`python -m app.data.generate_hybrid`)")
    print()
    rows = {r["method"]: r for r in rep["comparison"]}
    best = max(rows.values(), key=lambda r: r["precision_at_k"])
    h = rows["hybrid"]
    print(f"Interpretacija (računato, ne napamet): najviši P@5 ima {best['method']} "
          f"({best['precision_at_k']:.4f}); hybrid ima P@5 {h['precision_at_k']:.4f} i coverage "
          f"{h['catalog_coverage']:.2f} (vs {best['catalog_coverage']:.2f}).")
    if best["method"] != "hybrid":
        print("    Hybrid sa ručnim težinama NIJE pobedio — to je pošten rezultat, ne bag; "
              "težine nisu naučene (vidi lekciju).")
    print("API: GET /recommendations/{user_id} · GET /analytics/recommendations/hybrid")


if __name__ == "__main__":
    main()
```

### lab/README.md

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

### lab/starter.py

```
"""Starter za Day 8 lab — hybrid merge/rank/pravila/raznovrsnost.

Implementiraš mali deo onoga što kursni modul ``dm-ml/app/recommenders/hybrid.py``
već sadrži (da razumeš *šta* two-stage pipeline radi). Ne menjaš ``dm-ml`` —
radiš u ovom fajlu i proveravaš svoje rešenje sa ``test_lab.py``.

Kandidat = dict ``{"product_id": int, "score": float}`` (opciono ``category_id``).
"""

# --------------------------------------------------------------------------- #
# 1) normalize_scores — max-skaliranje na [0, 1]
# --------------------------------------------------------------------------- #
def normalize_scores(scores):
    """Max-skaliranje liste skorova na [0, 1].

    ``score / max``. Ako je ``max == 0`` -> svi ``0.0``; ako su svi jednaki
    (``max == min > 0``) -> svi ``1.0``. Prazna lista -> ``[]``.

    Zašto: ne možeš smisleno sabrati TF-IDF sličnost (0..1) sa sirovim
    count-om interakcija (0..stotine) pre nego što ih normalizuješ.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) merge_candidates — normalizacija + težinski spoj + dedup
# --------------------------------------------------------------------------- #
def merge_candidates(candidate_lists, weights):
    """Spaja kandidate izvora u JEDNU listu sa blended skorom.

    ``candidate_lists``: dict ``source`` -> lista kandidata (dict-ova sa
    ``product_id``/``score``). ``weights``: dict ``source`` -> težina.

    Koraci:
      1. Svaki izvor normalizuj sa ``normalize_scores`` (po izvoru).
      2. Za svaki proizvod: blended = ``Σ w_source * normalized_score``
         (normalizuj težine da zbirom budu 1.0).
      3. Duplikati se spajaju; ``sources`` = sortirana lista izvora.

    Vraća listu dict-ova: ``product_id``, ``score`` (blended), ``sources``.
    Prazan ulaz -> ``[]``; zbir težina <= 0 -> ``ValueError``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) rank_candidates — deterministički sort
# --------------------------------------------------------------------------- #
def rank_candidates(candidates):
    """Rangira kandidate: ``score`` opadajuće, tie-break ``product_id`` rastuće.

    Deterministika — isti ulaz uvek daje isti redosled.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) apply_business_rules — filter posle rangiranja
# --------------------------------------------------------------------------- #
def apply_business_rules(ranked, rules):
    """Primeni biznis pravila na RANGIRANU listu (filter, ne generator).

    ``rules`` (dict, opcioni ključevi):
      - ``available_ids`` (set) — ostaju samo proizvodi u skupu (dostupnost).
      - ``exclude_ids`` (set) — izbaci proizvode (npr. već kupljeno/viđeno).
      - ``min_score`` (float) — merged skor >= granice.

    Vraća dict: ``ranked`` (kept), ``removed`` (sa ``removed_by`` razlozima).
    Prazna lista -> ``{"ranked": [], "removed": []}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) diversify_results — raznovrsnost bez uništavanja relevantnosti
# --------------------------------------------------------------------------- #
def diversify_results(ranked, k, max_per_category=2):
    """Greedy re-ranker po kategoriji.

    Prolazi kroz rangiranu listu i zadržava kandidata ako njegova kategorija
    nije prekoračila ``max_per_category``. Ako ostane mesta do ``k``, DOPUNJUJE
    ostatkom liste po redosledu (ne skraćuje ispod onoga što ima — „fill,
    don't truncate"). Kandidat bez ``category_id`` se uvek zadržava.
    """
    # TODO: implementiraj
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


def test_normalize():
    assert lab.normalize_scores([2, 4]) == [0.5, 1.0]
    assert lab.normalize_scores([0, 0]) == [0.0, 0.0]
    assert lab.normalize_scores([3, 3]) == [1.0, 1.0]
    assert lab.normalize_scores([]) == []


def test_merge_and_rank():
    m = lab.merge_candidates({"a": [{"product_id": 1, "score": 10}, {"product_id": 2, "score": 5}],
                              "b": [{"product_id": 2, "score": 0.9}]}, {"a": 1, "b": 1})
    by = {c["product_id"]: c for c in m}
    assert by[2]["sources"] == ["a", "b"] and by[2]["score"] == pytest.approx(0.75)
    assert by[1]["score"] == pytest.approx(0.5)
    assert [c["product_id"] for c in lab.rank_candidates(m)] == [2, 1]
    assert lab.merge_candidates({}, {"a": 1}) == []
    with pytest.raises(ValueError):
        lab.merge_candidates({"a": [{"product_id": 1, "score": 1}]}, {"a": 0})
    tie = lab.rank_candidates([{"product_id": 5, "score": 1}, {"product_id": 3, "score": 1}])
    assert [c["product_id"] for c in tie] == [3, 5]


def test_rules_and_diversity():
    r = [{"product_id": i, "score": 1 - i / 10, "category_id": c} for i, c in enumerate([1, 1, 1, 2, 3], 1)]
    res = lab.apply_business_rules(r, {"available_ids": {1, 2, 3, 4}, "exclude_ids": {2}})
    assert [c["product_id"] for c in res["ranked"]] == [1, 3, 4]
    assert {c["product_id"] for c in res["removed"]} == {2, 5}
    assert lab.apply_business_rules([], {}) == {"ranked": [], "removed": []}
    d = lab.diversify_results(r, 4, max_per_category=2)
    assert [c["product_id"] for c in d] == [1, 2, 4, 5]
    assert len(lab.diversify_results(r[:3], 3, max_per_category=1)) == 3   # fill, don't truncate
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 8 lab-a."""
from __future__ import annotations

from collections import Counter


def normalize_scores(scores):
    s = [float(x) for x in scores]
    if not s:
        return []
    mx, mn = max(s), min(s)
    if mx == 0:
        return [0.0] * len(s)
    if mx == mn:
        return [1.0] * len(s)
    return [x / mx for x in s]


def merge_candidates(candidate_lists, weights):
    if not candidate_lists or not any(candidate_lists.values()):
        return []
    tot = sum(weights.get(k, 0.0) for k in candidate_lists)
    if tot <= 0:
        raise ValueError("zbir težina mora biti > 0")
    out = {}
    for src, cands in candidate_lists.items():
        w = weights.get(src, 0.0) / tot
        for c, n in zip(cands, normalize_scores([c["score"] for c in cands])):
            m = out.setdefault(c["product_id"], {**c, "score": 0.0, "sources": set()})
            m["score"] += w * n; m["sources"].add(src)
    return [{**m, "sources": sorted(m["sources"])} for m in out.values()]


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: (-c["score"], c["product_id"]))


def apply_business_rules(ranked, rules):
    kept, removed = [], []
    rules = rules or {}
    for c in ranked:
        why = []
        if rules.get("available_ids") is not None and c["product_id"] not in rules["available_ids"]:
            why.append("unavailable")
        if c["product_id"] in (rules.get("exclude_ids") or set()):
            why.append("excluded")
        if rules.get("min_score") is not None and c["score"] < rules["min_score"]:
            why.append("below_min_score")
        (removed.append({**c, "removed_by": why}) if why else kept.append(c))
    return {"ranked": kept, "removed": removed}


def diversify_results(ranked, k, max_per_category=2):
    out, rest, cnt = [], [], Counter()
    for c in ranked:
        cat = c.get("category_id")
        if len(out) < k and (cat is None or cnt[cat] < max_per_category):
            out.append(c); cnt[cat] += 1
        else:
            rest.append(c)
    out += rest[: max(0, k - len(out))]
    return out[:k]
```
