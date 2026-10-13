# Dan 9 — Session-Aware Recommendations and the Feedback Loop

- lesson_id: 119
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:47.598 updated: 2026-09-05 20:00:30.019
- summary: „Kontekst je kratak, istorija je duga." Do sada smo preporučivali iz duge istorije korisnika (Day 8 hybrid) ili sličnosti proizvoda (Day 5/6). Danas preporučujemo iz tekuće sesije: šta je korisnik upravo gledao, koliko je davno, koje kategorije ga trenutno zanimaju. I — po prvi put — merimo šta preporuke rade: svaku preporuku logujemo kao impresiju, a ako korisnik klikne, i kao klik. Odatle računamo CTR i poredimo algoritme. Day 8 je završio pitanjem: ako su težine pretpostavka, kako da ih podaci obore? Day 9 je odgovor: feedback loop-om. [subjects-import]


---

<!-- page_id 428 order 0 -->
## [Page] Materijal

# Dan 9 — Session-Aware Recommendations and the Feedback Loop

> *„Kontekst je kratak, istorija je duga."* Do sada smo preporučivali iz **duge
> istorije korisnika** (Day 8 hybrid) ili **sličnosti proizvoda** (Day 5/6).
> Danas preporučujemo iz **tekuće sesije**: šta je korisnik upravo gledao,
> koliko je davno, koje kategorije ga trenutno zanimaju. I — po prvi put —
> merimo šta preporuke *rade*: svaku preporuku logujemo kao **impresiju**, a ako
> korisnik klikne, i kao **klik**. Odatle računamo **CTR** i poredimo algoritme.
> Day 8 je završio pitanjem: *ako su težine pretpostavka, kako da ih podaci
> obore?* Day 9 je odgovor: **feedback loop-om**.

## Šta gradimo

**Session-aware preporuke** — preporuke iz konteksta tekuće sesije (recent
category/product interest sa recency weighting-om), izložene kroz
`GET /recommendations/session/{session_id}` — plus **feedback loop**: logovanje
impresija i klikova kroz `POST /recommendations/events`, **CTR dashboard**
(`GET /analytics/recommendations/ctr`) i **popular-vs-personalized poređenje**
(experiment-ready log u `Day 9/data/`).

Dok Day 5/6/8 odgovaraju na „šta da preporučim?", Day 9 postavlja drugo
pitanje: **kako znamo da li preporuke rade?** Bez logovanja impresija/klikova,
svaka preporuka je samo *predlog* — nemaš podatak da li je neko kliknuo. Sa
feedback loop-om, podaci (impresije i klikovi) mogu da obore težine iz Day 8:
algoritam koji skuplja više klikova po impresiji (viši CTR) je bolji — na ovom
skupu, u ovom trenutku.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `get_current_session` | **data preprocessing** (filter sesije + sort po vremenu) |
| `calculate_recent_product_interest` | **statistical / aggregation** (recency-weighted interes) |
| `calculate_recent_category_interest` | **statistical / aggregation** (mapiranje na katalog) |
| `build_session_features` | **data preprocessing / feature engineering** |
| `recommend_for_session` | **rule / heuristic** (kontekst sesije + fallback) |
| `recommendation_ctr` | **statistical / evaluation** (impresije → klikovi → stopa, zero-division) |

## Application requirement

Product stranica već prikazuje preporuke (Day 5 content + Day 6 collaborative).
Day 9 dodaje **session-aware preporuke** (zasnovane na tekućoj sesiji korisnika)
i **CTR dashboard** u admin sekciji: koje preporuke se *prikazuju* (impresije),
koje se *klikću* (klikovi), i kolika je stopa po algoritmu i po poziciji. Bez
toga, ne znaš da li je „Recommended Products" uopšte korisno.

## Ciljevi učenja

Do kraja dana treba da:

* objasnite **kontekst vs istoriju**: session features se računaju iz TEKUĆE
  sesije, ne iz cele istorije korisnika (mešanje session i user podataka je čest
  bag);
* implementirate **`get_current_session`** (filter + sort po vremenu, opcioni
  recency prozor);
* izračunate **recent category/product interest** sa **recency weighting-om**
  (`calculate_recent_category_interest` / `calculate_recent_product_interest`) —
  skoriji događaji nose više težine;
* sagradite **`build_session_features`** (trajanje, brojevi, top kategorije/
  proizvodi, recency);
* preporučite za tekuću sesiju **`recommend_for_session`** (kandidati iz top
  kategorija sesije, bez već viđenih, blend sa popularnošću; fallback za sesiju
  bez signala — nikad tihi `[]`);
* logujete **impresije i klikove** sa `recommendation_source` (algoritam) i
  `recommendation_position` (pozicija) — impresija bez pozicije ne meri
  position-bias;
* izračunate **CTR** (`recommendation_ctr`) sa **zero-division handling-om**
  (0 impresija → `0.0`, bez `None` i bez deljenja kroz nulu);
* objasnite **A/B ideju** (popular vs personalized) bez zahtevanja punog
  značajnosnog testa — Day 9 proizvodi *prikupljanje podataka* za eksperiment,
  ne statistički zaključak.

## Preduslovi

Day 1 događaji (sa `recommendation_impression`/`recommendation_click` — seeded),
Day 5 katalog (`products_text.csv`), Day 8 ranking. **Session-co-occurrence
heuristika iz Day 6 je session baseline** — postojeća heuristika za sesije,
protiv koje merimo session-aware preporuke.

## Postojeći sistem (šta nasleđujemo)

* **Day 1 event sloj već loguje impresije/klikove.** `events.csv` ima
  `recommendation_impression` (61 530) i `recommendation_click` (1 427)
  događaja sa `recommendation_source="category"` i `recommendation_position`
  1..3. Day 9 to koristi kao *stvarni* impression/click log za CTR.
* **Day 6 session-co-occurrence heuristika** (`recommend_session_cooccurrence`)
  je **session baseline** — kao što je `2.0/0.5` merge bio degenerisano seme za
  Day 8. Ne zaboravi ga: session-aware preporuke se mere protiv njega.
* **Day 8 hybrid ranking** (retrieval → merge → rank → pravila) preporučuje za
  KORISNIKA. Day 9 preporučuje za SESIJU — kratak, tekući kontekst.
* **Nedostaje:** preporuka iz tekuće sesije; logovanje impresija/klikova kao
  prvorazredni API; CTR; popular-vs-personalized poređenje. Day 9 to dodaje.

## Arhitektura

```
Day 1 događaji (events.csv, sadrži impression/click)   Day 5 katalog (products_text.csv)
      │                                                           │
      ▼                                                           ▼
app/recommenders/session.py  recommend_for_session(session_id)
  │
  ├── get_current_session        (filter + sort po vremenu, recency prozor)
  ├── calculate_recent_product_interest   (recency-weighted interes proizvoda)
  ├── calculate_recent_category_interest  (mapiranje na katalog)
  ├── build_session_features     (trajanje, brojevi, top kategorije/proizvodi)
  ├── recommend_for_session      (kandidati iz top kategorija + popularity blend,
  │                               exclude_seen, cold-start fallback)
  │
  ▼
GET /recommendations/session/{session_id}   POST /recommendations/events
      │                                              │
      ▼                                              ▼
CTR dashboard  GET /analytics/recommendations/ctr   (impresije + klikovi)
      │
      ▼
GET /analytics/recommendations/session-comparison  (popular vs personalized,
                         Day 9/data/impressions.csv — experiment-ready log)
```

## Korišćeni podaci

**Stvarni impression/click log** je *sam* `Day 1/data/events.csv` — seeded
događaji sa `recommendation_source`/`recommendation_position`. CTR dashboard ga
čita direktno.

**Experiment-ready log** (seeded, `Day 9/data/`, jedini izvor:
`app/data/generate_session.py`) — izvedene tabele iz Day 1 događaja + Day 5
kataloga:

| Fajl | Sadržaj |
| --- | --- |
| `impressions.csv` | SIMULIRANI experiment log: za 200 sesija, oba algoritma (`popular`/`personalized`) loguju po 5 impresija sa pozicijom; klik je simuliran (seed 42, klik-model u `metadata.json`) — 2000 redova |
| `ctr.csv` | CTR po algoritmu i po poziciji |
| `comparison.csv` | popular vs personalized (impresije, klikovi, CTR) |
| `metadata.json` | izvor, parametri, klik-model, counts, sha256 |

**Važno:** klikovi u `impressions.csv` su SIMULIRANI — to je *demonstracija
logging mehanizma*, ne stvarno ponašanje. U `events.csv` klikovi su sintetički
generisani (Day 1), ali njihov CTR (0.0232 ukupno, 0.0373 na poziciji 1) je
„stvaran" u smislu da je proizveden generativnim modelom.

## AI-ML koncept

* **Kontekst ≠ istorija.** Session features se računaju iz događaja tekuće
  sesije (filter na `user_session`). Mešanje session i user podataka (računanje
  interesa iz cele istorije korisnika) uništava poentu: session intencija je
  kratkotrajna („gleda skije sad"), istorija je dugotrajna („kupuje i knjige").
* **Recency weighting.** Skoriji događaji nose više težine. Day 9 koristi
  geometrijski decay po poziciji (najnoviji = 1.0, prethodni = 0.8, ...).
  „Sesija koja je pre 2 min gledala tenis" ≠ „sesija koja je tenis gledala pre
  30 min" — obe su o tenisu, ali prva je verovatnije u teniskom modu.
* **Session intent / online behavior.** Session-aware preporuke hvataju
  *kratkoročnu nameru*: korisnik koji gleda bicikle u ovoj sesiji verovatno
  gleda i kacige — sada, ne „jednom u istoriji".
* **Recommendation position.** Pozicija preporuke (1, 2, 3, ...) je podatak:
  prva pozicija dobija više klikova (position-bias). Logovana pozicija ti
  omogućava da meriš bias i da ga kontrolišeš u evaluaciji.
* **Feedback loop.** Impresija = „preporuka je prikazana"; klik = „korisnik je
  reagovao". CTR = `klikovi / impresije`. To je zatvaranje petlje: preporuka →
  prikaz → reakcija → mera → poboljšanje. Day 8 pitanje („kako podaci obaraju
  težine?") dobija *osnovu* za odgovor: CTR po algoritmu je signal kojim se težine
  mogu menjati (npr. kasnije bandit koji daje više impresija boljem algoritmu) — Day 9
  to NE radi automatski, samo prikuplja podatke.
* **CTR je deskriptivan, ne preskriptivan.** Viši CTR kaže „više klikova po
  prikazu" — ne kaže „ovaj algoritam je bolji" (ne meri zadovoljstvo, konverziju
  u kupovinu, ni dugoročnu vrednost). Zato je comparison deo kursa.
* **Experiment-ready logging.** Da bi uporedio dva algoritma (popular vs
  personalized), loguješ impresije pod OBAMA i brojiš klikove. Day 9 proizvodi
  *infrastrukturu* za to i demonstrira na simuliranom logu; značajnosni test
  (da li je razlika statistički pouzdana) je van dana — DAY-BRIEFS „What the
  result does NOT prove".

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — `get_current_session`

`get_current_session(events, session_id, window_minutes=None)` — filter
događaja na `user_session`, sort po `timestamp`, opcioni recency prozor
(poslednjih N minuta relativno na poslednji događaj). Sesija koja ne postoji →
prazan DataFrame (uslov za cold-start fallback).

### Korak 2 — `calculate_recent_product_interest`

`calculate_recent_product_interest(events, decay=0.8)` (alias za `recent_product_interest`;
`events` je lista dict-ova sa `event_type`/`product_id`, hronološki) — za svaki
proizvodni događaj sesije: težina = `EVENT_WEIGHTS[type] × recency_weight`
(geometrijski decay po poziciji; najnoviji = 1.0). Agregira se po proizvodu
(zbir) → `{product_id: interes}`. Bez proizvodnih događaja → prazan dict.

### Korak 3 — `calculate_recent_category_interest`

`calculate_recent_category_interest(events, product_categories, decay=0.8)` —
mapira proizvodni interes na kategorije preko kataloga (`product_categories` =
`{product_id: category_id}`, source of truth, ne događaj). Proizvodi kojih nema u
katalogu se ignorišu. Prazno → prazan dict.

### Korak 4 — `build_session_features`

`build_session_features(session_events, product_categories, decay=0.8, top_n=2)`
(alias za `session_features`) — `n_events`, `n_product_events`, `n_distinct_products`,
`duration_minutes`, `top_categories` (top `top_n`) / `top_products` (top 3),
`seen_product_ids` (recency-weighted interes). Ovo su
feature-i koje bi dao modelu da nauči „šta dalje".

### Korak 5 — `recommend_for_session`

`recommend_for_session(feats, products, similarity=None, sim_ids=None, limit=5,
w_category=0.5, w_similar=0.5)` (modul) i `SessionRecommenderService.recommend_for_session(session_id, limit)` (servis):

1. `get_current_session` → događaji sesije; `session_features` → recency-weighted
   interes (proizvod + kategorija).
2. **Cold-start fallback** (nikad tihi `[]`, u servisu): sesija bez proizvodnog
   signala → popularity top-N sa `fallback=True`, `fallback_reason="no_session_signal"`.
3. Skor kandidata (već viđeni u sesiji su isključeni — `exclude_seen` je svojstveno
   session kontekstu): `0.5 × norm(interes kategorije × popularnost) +
   0.5 × norm(Σ interes × item-item sličnost)` (Day 6 CF sličnost; težine = heuristika).
4. `sources` kaže koji signal je doprineo (`session_category`, `session_similar`).

### Korak 6 — `recommendation_ctr`

`recommendation_ctr(impressions, clicks)` — `ctr = len(clicks) / len(impressions)`.
**Zero-division:** 0 impresija → `ctr = 0.0`. Grupisanje radi `ctr_by_algorithm(impressions, clicks)`
(po `algorithm`), a servis (`ctr_dashboard`) isto i po poziciji.

### Korak 7 — Servis + API + generator + CMS

`app/services/session.py` (`SessionRecommenderService`, lazy + keširani EventStore
za round-trip), `GET /recommendations/session/{session_id}` +
`POST /recommendations/events` + `GET /analytics/recommendations/ctr` +
`GET /analytics/recommendations/session-comparison`,
`app/data/generate_session.py` (upisuje `Day 9/data/*`), product stranica loguje
session-aware impresije/klikove, admin dobija CTR karticu.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `get_current_session(...)` | događaji tekuće sesije, sort po vremenu (+ recency prozor) | `app/recommenders/session.py` |
| `calculate_recent_product_interest(...)` | recency-weighted interes proizvoda | `app/recommenders/session.py` |
| `calculate_recent_category_interest(...)` | recency-weighted interes kategorija (preko kataloga) | `app/recommenders/session.py` |
| `build_session_features(...)` | trajanje, brojevi, top kategorije/proizvodi, recency | `app/recommenders/session.py` |
| `recommend_for_session(...)` | preporuke iz konteksta sesije + cold-start fallback | `app/recommenders/session.py` |
| `recommendation_ctr(...)` | CTR sa zero-division handling-om (overall/po algoritmu/po poziciji) | `app/recommenders/session.py` |
| `ctr_by_algorithm(...)` | CTR po algoritmu + po poziciji (dashboard pregled) | `app/recommenders/session.py` |
| `SessionRecommenderService.*` | lazy podaci, logovanje, CTR, comparison | `app/services/session.py` |
| `app/data/generate_session.py` | generiše `Day 9/data/*` (byte-for-byte) | `app/data/generate_session.py` |
| `examples/demo_session.py` | pun demo (features + preporuke + CTR + comparison) | `Day 9/examples/demo_session.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /recommendations/session/{session_id}?limit=5` | 200: session-aware envelope (`session_id`, `method`, `fallback`, `session_features`, `excluded_seen`, `recommendations`); **nepoznata sesija → 200 sa fallback-om** (`fallback_reason="no_session_signal"`, popularity top-N); **422** nevalidan `limit`; **503** nema podataka |
| `POST /recommendations/events` | 201: sačuvan impression/click događaj (`event_id`, round-trip); **422** pogrešan `event_type` / bez `product_id` / `recommendation_source` / `recommendation_position` / `user_session` |
| `GET /analytics/recommendations/ctr` | 200: CTR dashboard (overall + po algoritmu + po poziciji); zero-division → `0.0` |
| `GET /analytics/recommendations/session-comparison` | 200: popular vs personalized (iz `Day 9/data/comparison.csv`); **503** nema generisanog loga |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /recommendations/session/session_005246?limit=3`

```
{
  "session_id": "session_005246", "method": "session", "fallback": false,
  "fallback_reason": null, "returned": 3,
  "recommendations": [
    {"product_id": 55, "name": "Guide Everyday 453", "category_id": 3, "score": 1.0,
     "sources": ["session_category", "session_similar"]},
    {"product_id": 59, "name": "Poetry Classic 204", "category_id": 3, "score": 0.887047,
     "sources": ["session_category", "session_similar"]},
    {"product_id": 56, "name": "Guide Eco 397", "category_id": 3, "score": 0.838476,
     "sources": ["session_category", "session_similar"]}
  ],
  "session_features": {
    "n_events": 31, "n_product_events": 15, "n_distinct_products": 12,
    "duration_minutes": 21.0,
    "top_categories": [{"category_id": 3, "interest": 4.4524},
                       {"category_id": 7, "interest": 0.3277}],
    "top_products": [{"product_id": 48, "interest": 1.0},
                     {"product_id": 54, "interest": 0.8},
                     {"product_id": 43, "interest": 0.64}],
    "seen_product_ids": [43, 44, 48, 49, 50, 52, 54, 60, 61, 63, 127, 231]
  },
  "excluded_seen": 12
}
```

`GET /recommendations/session/session_DOESNOTEXIST?limit=3`:

```
{
  "product_id": null, "method": "fallback", "fallback": true,
  "fallback_reason": "no_session_signal", "returned": 3,
  "recommendations": [{"product_id": 90, "name": "Table Lamp Eco 643", "category_id": 5,
                       "price": 23.99, "score": 2115.0, ...}, ...],
  "session_id": "session_DOESNOTEXIST"
}
```

## CMS integracija

* **Product stranica** (`dm-frontend/app/pages/product/[slug].vue`): nova sekcija
  **„Based on your session"** — poziva `GET /ml/recommendations/session/{sessionId}`
  (session ID iz `trackEvent` kompozable), renderuje preporuke, i **loguje
  impresije/klikove** sa `recommendation_source="session"` i pozicijom kroz
  `POST /ml/recommendations/events`. Postojeće content/collaborative sekcije
  nastavljaju da loguju kroz frontend store.
* **Admin** (`dm-frontend/app/pages/admin/recommendations/index.vue`): nova
  **CTR kartica** — `GET /ml/analytics/recommendations/ctr` (overall + po
  algoritmu + po poziciji) i **popular vs personalized** kartica —
  `GET /ml/analytics/recommendations/session-comparison`. Graceful fallback kad
  dm-ml ne radi.

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 9/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno (Day 9): **`recommendation_ctr`** (overall, po algoritmu, po poziciji,
prazan ulaz, nepoznat `group_by` → ValueError, nepoznata kolona → ValueError,
**0 impresija → ctr 0.0** — acceptansi), `get_current_session` (sort, nepoznata
sesija, lookback prozor), `calculate_recent_product_interest` (recency weighting,
event težine, prazan signal), `calculate_recent_category_interest` (mapiranje
preko kataloga), `build_session_features` (counts, trajanje, top kategorije/proizvodi),
`recommend_for_session` (**session-aware: isključi viđeno, prvi kandidat iz
aktivne kategorije; nepoznata sesija → fallback `no_session_signal`; nikad tihi
`[]`**; `available_ids` filter), **seeded manifest sha256**, API
(`/recommendations/session/{id}` 200/fallback/422/503,
`POST /recommendations/events` 201/422, CTR dashboard, session-comparison).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 9/examples/demo_session.py"` —
   session features, session-aware preporuke, cold-start fallback, CTR iz
   seeded loga, popular-vs-personalized comparison.
2. Pusti servis pa pitaj `GET /recommendations/session/session_005246?limit=5` —
   uporedi sa `GET /recommendations/395` (Day 8, user istorija). Kako se
   preporuke razlikuju i zašto?
3. Pitaj `GET /recommendations/session/session_DOESNOTEXIST` — fallback na
   popularity sa `no_session_signal` (nikad tihi `[]`).
4. Pošalji `POST /recommendations/events` (impresija + klik) pa pitaj
   `GET /analytics/recommendations/ctr` — logovani događaj menja CTR odmah
   (round-trip).
5. Pitaj `GET /analytics/recommendations/session-comparison` — popular vs
   personalized. Šta tabela kaže, a šta NE kaže?
6. Pokreni lab (`Day 9/lab/`) — ponovo implementiraj `recency_weights` /
   `recent_product_interest` / `recent_category_interest` / `recommendation_ctr`
   / `ctr_by_algorithm` na malim podacima i proveri `test_lab.py`.
7. Product stranica: otvori proizvod, pogledaj „Based on your session" sekciju,
   klikni preporuku — i vidi klik u CTR dashboardu.

## Comparison (baseline ugao)

**Popular vs personalized** (simulirani experiment log, `Day 9/data/`):

| Algoritam | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| **popular** (baseline) | 1000 | 11 | **0.011** |
| **personalized** (session-aware) | 1000 | 22 | **0.022** |

**CTR iz seeded impression/click loga** (`events.csv`, stvarni sintetički log):

| Grupa | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| ukupno (source=category) | 61 530 | 1 427 | 0.0232 |
| position 1 | 20 510 | 765 | **0.0373** |
| position 2 | 20 510 | 390 | 0.0190 |
| position 3 | 20 510 | 272 | 0.0133 |

Šta tabela kaže:

* **Position-bias je vidljiv u seeded logu**: CTR opada sa pozicijom
  (0.0373 → 0.0190 → 0.0133; pozicija 1 nosi 54 % klikova). To je zašto se pozicija mora logovati —
  bez nje ne bi mogao da vidiš bias.
* **Simulirani comparison**: personalized ima viši CTR (0.022 vs 0.011) jer mu
  je klik-model favorabilniji za proizvode iz kategorija koje sesija upravo
  gleda. To je MODEL, ne stvarno ponašanje.
* **Session-co-occurrence heuristika (Day 6) je session baseline**: pre nego što
  pripišeš zasluge session-aware pipeline-u, uporedi ga sa `recommend_session_cooccurrence`
  — postojećom heuristikom koja gleda „šta su drugi radili u istim sesijama".

## Evaluacija (kako znamo da je dobro)

* **`recommendation_ctr` je definisan za edge case-ove:** 0 impresija → `0.0`
  (ne `None`, ne greška), nepoznat `group_by` → ValueError, prazan ulaz →
  `{0, 0, 0.0}` (testovi).
* **Cold-start sesija je definisan slučaj:** nepoznata sesija → 200 sa
  `method="fallback"`, `fallback_reason="no_session_signal"`, popularity top-N —
  NIKAD tihi `[]` (test).
* **`recommend_for_session` je session-aware:** proizvodi već viđeni u sesiji se
  isključuju (`excluded_seen`), a prvi kandidat dolazi iz AKTIVNE kategorije
  sesije (test).
* **Impresija bez pozicije se odbija:** `POST /recommendations/events` zahteva
  `recommendation_position` i `recommendation_source` (422; test) — logovanje
  impresija bez pozicije je čest bag.
* **Feedback loop radi:** logovani događaj menja CTR odmah (test
  `ctr_reflects_logged_events`: impresija + klik → CTR 1.0).
* **Determinizam:** generator je byte-for-byte (sha256 u `metadata.json`);
  isti podaci + isti parametri → isti izlaz.
* **Modul je importabilan** od Days 10–12 i capstone-a:
  `from app.recommenders.session import recommend_for_session, recommendation_ctr`.

## Česti bugovi

* **Mešanje session i user podataka** — računaš interes iz CELE istorije
  korisnika umesto iz tekuće sesije. Rešenje: filter na `user_session` pre
  računanja interesa (test).
* **Logovanje impresija bez pozicije** — ne možeš meriti position-bias (najviše
  klikova je na poziciji 1). Rešenje: `recommendation_position` je obavezan u
  `POST /recommendations/events` (test).
* **Nema recency weighting-a** — svi događaji sesije tretirani jednako, pa
  interes „zaglavi" na starom. Rešenje: geometrijski decay po poziciji
  (`calculate_recent_product_interest`).
* **CTR preko 0 impresija** — deljenje kroz nulu. Rešenje: `recommendation_ctr`
  vraća `0.0` (zero-division handling, test).
* **Zaboravljanje da je session-co-occurrence heuristika session baseline** —
  pripisuješ session-aware preporukama zasluge bez poređenja sa postojećom
  heuristikom (Day 6 `recommend_session_cooccurrence`). Rešenje: comparison
  sekcija uključuje baseline.
* **Isključivanje samo kupljenog, ne i viđenog** — u sesiji „video sam, ne
  preporučuj ponovo" (session kontekst je kratak; već viđeni proizvodi se
  isključuju).
* **Tretiranje CTR-a kao presude** — viši CTR ≠ „bolji algoritam" (ne meri
  zadovoljstvo ni konverziju). CTR je deskriptivan; A/B značaj je van dana.

## Šta rezultat NE dokazuje

* **CTR razlika NIJE statistički potvrđen A/B rezultat.** Day 9 proizvodi
  *prikupljanje podataka* za eksperiment (experiment-ready logging), ne
  značajnosni test. Za pravi A/B treba ti randomizacija, dovoljan saobraćaj i
  test značajnosti — van dana.
* **Personalized nije „dokazano bolji".** Simulirani log ima viši CTR za
  personalized jer mu je klik-model favorabilan; na pravom store-u brojevi se
  menjaju. (U seeded `events.csv` svi klikovi su na `category` — nema još
  uporedivog `personalized` saobraćaja.)
* **Session-aware preporuke nisu „pametnije" od user istorije.** One hvataju
  *drugu* informaciju (kratkoročna intencija), ne *bolju*. Često najbolje radi
  kombinacija (Day 12 / capstone).
* **CTR ne meri konverziju.** Klik na preporuku ≠ kupovina. Preporuka može da
  ima visok CTR a nizak doprinos prodaji („clickbait").
* **Recency decay i merge težine su heuristike** (0.8, 0.5/0.5) — ne naučen
  odgovor. Feedback loop je ono što ih podacima može oboriti.
* **Simulirani klik-model ne opisuje stvarno ponašanje.** Vrednost je u
  *mehanizmu* (logovanje, CTR matematika, position-bias), ne u brojevima.

## Vežbe

1. **Vary recency decay** — pokreni `recommend_for_session` sa `decay=0.5`,
   `0.9`, `1.0` (nema recency-ja). Kako se top kategorije/proizvodi menjaju?
   Šta `decay=1.0` radi sa „recent" interest-om? (weight-sensitivity na recency.)
2. **Dodaj recency weighting u session features** — već jeste (Day 9); probaj
   *vremenski* decay (poluživot u minutima) umesto po-poziciji i uporedi.
3. **Loguj `recommendation_position` u frontendu** — proveri da svaka
   `recommendation_impression` ima poziciju; vidi position-bias u CTR dashboardu
   (seed već pokazuje: pozicija 1 nosi sve klikove).
4. **CTR po algoritmu** — `GET /analytics/recommendations/ctr` grupiše po
   `recommendation_source`; dodaj više algoritama (npr. `content`,
   `collaborative`) kroz `POST /recommendations/events` i vidi poređenje.
5. **Popular-vs-personalized na dashboard** — već je dodato (admin kartica);
   probaj da promeniš klik-model u `generate_session.py` (npr. simetričan model
   gde popular i personalized imaju isti `base`) i regeneriši — kako se
   comparison menja? To dokazuje da je razlika MODEL, ne „istina".
6. **Session vs user** — uporedi `GET /recommendations/session/{session_id}` sa
   `GET /recommendations/{user_id}` (Day 8) za istu sesiju/korisnika. Koje
   preporuke se razlikuju i zašto? (Session intencija vs duga istorija.)
7. **Uporedi sa session baseline-om** — za isti proizvod pokreni Day 6
   `recommend_session_cooccurrence` i svoj session-aware pipeline; gde se
   preklapaju, gde se razlikuju? (Session-co-occurrence je baseline, ne istina.)
8. **Razmisli o ground truth** — da su klikovi samo na poziciji 1 (kao u seed-u),
   da li je CTR po poziciji poštena mera algoritma? Kako bi logovao/merio
   drugačije?
9. **A/B ideja na papiru** — kako bi dizajnirao pravi A/B test između popular i
   personalized? (Randomizacija sesija, dovoljan sample, unapred definisan
   ishod, test značajnosti.) Koji koraci su van Day 9?

## Sažetak

Napravio si **session-aware preporuke i feedback loop**: session features
(recency-weighted recent category/product interest, trajanje, brojevi) →
`recommend_for_session` (kandidati iz top kategorija sesije, bez već viđenih,
blend sa popularnošću; cold-start fallback — nikad tihi `[]`) → izloženo kroz
`GET /recommendations/session/{session_id}`. Dodao si **logovanje impresija/
klikova** (`POST /recommendations/events`), **CTR dashboard** (`GET /analytics/ recommendations/ctr`) sa **zero-division handling-om**, i **popular-vs-
personalized comparison** (experiment-ready log, `Day 9/data/`). Centralna
lekcija: **kontekst sesije je kratak i tekuć — recency teži, viđeno se
isključuje, pozicija se loguje, CTR meri reakciju.** CTR razlika nije A/B
rezultat — Day 9 pravi *prikupljanje podataka* za taj eksperiment. Pitanje
danas: **ako podaci (impresije i klikovi) mogu da obore težine, kako da ih
naučimo umesto da ih ručno biramo?** — to je Day 10 (semantička pretraga i
embedding preporuke) i Day 12 (full integration).

---

<!-- page_id 429 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/comparison.csv

```
algorithm,impressions,clicks,ctr
popular,1000,11,0.011
personalized,1000,22,0.022
```

### data/ctr.csv

```
level,group,impressions,clicks,ctr
algorithm,personalized,1000,22,0.022
algorithm,popular,1000,11,0.011
position,position_1,400,16,0.04
position,position_2,400,5,0.0125
position,position_3,400,7,0.0175
position,position_4,400,5,0.0125
position,position_5,400,0,0.0
```

### data/impressions.csv

```
session_id,algorithm,position,product_id,name,category_id,session_top_category,clicked
session_005653,popular,1,90,Table Lamp Eco 643,5,False,0
session_005653,popular,2,184,Nightstand Everyday 721,9,False,0
session_005653,popular,3,110,Shampoo Everyday 111,6,False,0
session_005653,popular,4,12,Keyboard Classic 505,1,False,0
session_005653,popular,5,49,Biography Deluxe 648,3,False,0
session_005653,personalized,1,198,Car Charger Everyday 607,10,True,0
session_005653,personalized,2,193,Car Battery Deluxe 488,10,True,0
session_005653,personalized,3,208,Jump Starter Essential 942,10,True,0
session_005653,personalized,4,199,Car Charger Everyday 299,10,True,0
session_005653,personalized,5,205,Ice Scraper Deluxe 739,10,True,0
session_007740,popular,1,90,Table Lamp Eco 643,5,False,0
session_007740,popular,2,184,Nightstand Everyday 721,9,False,0
session_007740,popular,3,12,Keyboard Classic 505,1,False,0
session_007740,popular,4,49,Biography Deluxe 648,3,False,0
session_007740,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007740,personalized,1,37,Backpack Compact 926,2,True,0
session_007740,personalized,2,31,T-shirt Classic 854,2,True,0
session_007740,personalized,3,125,Beard Trimmer Premium 354,6,True,0
session_007740,personalized,4,118,Body Lotion Deluxe 734,6,True,0
session_007740,personalized,5,36,Backpack Classic 759,2,True,0
session_006853,popular,1,90,Table Lamp Eco 643,5,False,0
session_006853,popular,2,184,Nightstand Everyday 721,9,False,0
session_006853,popular,3,12,Keyboard Classic 505,1,False,0
session_006853,popular,4,49,Biography Deluxe 648,3,False,0
session_006853,popular,5,127,Building Blocks Premium 126,7,False,0
session_006853,personalized,1,80,Fitness Band Eco 108,4,True,0
session_006853,personalized,2,75,Football Premium 903,4,True,1
session_006853,personalized,3,68,Dumbbell Set Premium 193,4,True,0
session_006853,personalized,4,65,Running Shoes Deluxe 803,4,True,0
session_006853,personalized,5,77,Tennis Racket Classic 374,4,True,0
session_001406,popular,1,90,Table Lamp Eco 643,5,False,0
session_001406,popular,2,184,Nightstand Everyday 721,9,False,0
session_001406,popular,3,110,Shampoo Everyday 111,6,False,0
session_001406,popular,4,12,Keyboard Classic 505,1,True,0
session_001406,popular,5,49,Biography Deluxe 648,3,False,0
session_001406,personalized,1,12,Keyboard Classic 505,1,True,0
session_001406,personalized,2,2,Smartphone Compact 854,1,True,0
session_001406,personalized,3,9,Monitor Premium 997,1,True,0
session_001406,personalized,4,13,Mouse Deluxe 406,1,True,1
session_001406,personalized,5,6,Headphones Compact 103,1,True,0
session_001410,popular,1,90,Table Lamp Eco 643,5,True,0
session_001410,popular,2,110,Shampoo Everyday 111,6,False,0
session_001410,popular,3,12,Keyboard Classic 505,1,False,0
session_001410,popular,4,49,Biography Deluxe 648,3,False,0
session_001410,popular,5,76,Tennis Racket Compact 416,4,False,0
session_001410,personalized,1,90,Table Lamp Eco 643,5,True,0
session_001410,personalized,2,177,Bed Frame Eco 577,9,True,0
session_001410,personalized,3,181,Coffee Table Eco 857,9,True,0
session_001410,personalized,4,85,Blender Classic 334,5,True,0
session_001410,personalized,5,185,Dining Chair Classic 954,9,True,0
session_005401,popular,1,90,Table Lamp Eco 643,5,False,0
session_005401,popular,2,184,Nightstand Everyday 721,9,False,0
session_005401,popular,3,110,Shampoo Everyday 111,6,False,0
session_005401,popular,4,12,Keyboard Classic 505,1,False,0
session_005401,popular,5,49,Biography Deluxe 648,3,False,0
session_005401,personalized,1,41,Boots Compact 911,2,True,0
session_005401,personalized,2,30,T-shirt Everyday 987,2,True,0
session_005401,personalized,3,37,Backpack Compact 926,2,True,0
session_005401,personalized,4,36,Backpack Classic 759,2,True,0
session_005401,personalized,5,23,Jacket Essential 819,2,True,0
session_007784,popular,1,90,Table Lamp Eco 643,5,False,0
session_007784,popular,2,184,Nightstand Everyday 721,9,False,0
session_007784,popular,3,110,Shampoo Everyday 111,6,False,0
session_007784,popular,4,12,Keyboard Classic 505,1,False,0
session_007784,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007784,personalized,1,52,Fantasy Pro 681,3,True,0
session_007784,personalized,2,132,Puzzle Everyday 336,7,True,0
session_007784,personalized,3,134,Doll Classic 843,7,True,0
session_007784,personalized,4,141,Paint Set Classic 369,7,True,0
session_007784,personalized,5,142,Paint Set Deluxe 295,7,True,0
session_009991,popular,1,90,Table Lamp Eco 643,5,False,0
session_009991,popular,2,184,Nightstand Everyday 721,9,False,0
session_009991,popular,3,110,Shampoo Everyday 111,6,True,0
session_009991,popular,4,12,Keyboard Classic 505,1,False,0
session_009991,popular,5,49,Biography Deluxe 648,3,False,0
session_009991,personalized,1,110,Shampoo Everyday 111,6,True,0
session_009991,personalized,2,125,Beard Trimmer Premium 354,6,True,0
session_009991,personalized,3,118,Body Lotion Deluxe 734,6,True,0
session_009991,personalized,4,123,Makeup Brush Set Pro 675,6,True,0
session_009991,personalized,5,121,Sunscreen Classic 799,6,True,0
session_003601,popular,1,90,Table Lamp Eco 643,5,False,0
session_003601,popular,2,184,Nightstand Everyday 721,9,False,0
session_003601,popular,3,110,Shampoo Everyday 111,6,False,0
session_003601,popular,4,12,Keyboard Classic 505,1,False,0
session_003601,popular,5,49,Biography Deluxe 648,3,True,0
session_003601,personalized,1,49,Biography Deluxe 648,3,True,0
session_003601,personalized,2,60,Poetry Everyday 604,3,True,0
session_003601,personalized,3,63,Cookbook Compact 232,3,True,0
session_003601,personalized,4,50,Biography Essential 819,3,True,0
session_003601,personalized,5,43,Novel Premium 556,3,True,0
session_009211,popular,1,90,Table Lamp Eco 643,5,False,0
session_009211,popular,2,184,Nightstand Everyday 721,9,False,0
session_009211,popular,3,110,Shampoo Everyday 111,6,False,0
session_009211,popular,4,12,Keyboard Classic 505,1,False,0
session_009211,popular,5,49,Biography Deluxe 648,3,False,0
session_009211,personalized,1,37,Backpack Compact 926,2,True,0
session_009211,personalized,2,41,Boots Compact 911,2,True,0
session_009211,personalized,3,39,Cap Everyday 356,2,True,0
session_009211,personalized,4,76,Tennis Racket Compact 416,4,True,0
session_009211,personalized,5,32,Scarf Eco 733,2,True,0
session_008639,popular,1,90,Table Lamp Eco 643,5,False,0
session_008639,popular,2,184,Nightstand Everyday 721,9,False,0
session_008639,popular,3,110,Shampoo Everyday 111,6,False,0
session_008639,popular,4,12,Keyboard Classic 505,1,False,0
session_008639,popular,5,49,Biography Deluxe 648,3,False,0
session_008639,personalized,1,243,Ladder Deluxe 713,12,True,0
session_008639,personalized,2,198,Car Charger Everyday 607,10,True,0
session_008639,personalized,3,249,Work Gloves Compact 227,12,True,0
session_008639,personalized,4,232,Cordless Drill Classic 499,12,True,0
session_008639,personalized,5,234,Screwdriver Set Eco 897,12,True,0
session_014054,popular,1,90,Table Lamp Eco 643,5,False,0
session_014054,popular,2,184,Nightstand Everyday 721,9,True,0
session_014054,popular,3,110,Shampoo Everyday 111,6,False,0
session_014054,popular,4,12,Keyboard Classic 505,1,False,0
session_014054,popular,5,49,Biography Deluxe 648,3,True,0
session_014054,personalized,1,184,Nightstand Everyday 721,9,True,0
session_014054,personalized,2,182,Coffee Table Pro 626,9,True,0
session_014054,personalized,3,175,Bookshelf Eco 371,9,True,0
session_014054,personalized,4,169,Sofa Essential 990,9,True,0
session_014054,personalized,5,171,Office Chair Deluxe 707,9,True,0
session_008482,popular,1,90,Table Lamp Eco 643,5,False,0
session_008482,popular,2,184,Nightstand Everyday 721,9,False,0
session_008482,popular,3,110,Shampoo Everyday 111,6,False,0
session_008482,popular,4,12,Keyboard Classic 505,1,False,0
session_008482,popular,5,49,Biography Deluxe 648,3,False,0
session_008482,personalized,1,76,Tennis Racket Compact 416,4,True,0
session_008482,personalized,2,80,Fitness Band Eco 108,4,True,0
session_008482,personalized,3,68,Dumbbell Set Premium 193,4,True,0
session_008482,personalized,4,65,Running Shoes Deluxe 803,4,True,0
session_008482,personalized,5,75,Football Premium 903,4,True,0
session_011998,popular,1,90,Table Lamp Eco 643,5,False,0
session_011998,popular,2,184,Nightstand Everyday 721,9,False,0
session_011998,popular,3,12,Keyboard Classic 505,1,False,0
session_011998,popular,4,49,Biography Deluxe 648,3,False,0
session_011998,popular,5,231,Studio Headphones Classic 686,11,False,0
session_011998,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_011998,personalized,2,208,Jump Starter Essential 942,10,True,0
session_011998,personalized,3,199,Car Charger Everyday 299,10,True,0
session_011998,personalized,4,210,Dash Cam Premium 877,10,True,0
session_011998,personalized,5,196,Phone Holder Pro 656,10,True,0
session_011708,popular,1,90,Table Lamp Eco 643,5,False,0
session_011708,popular,2,184,Nightstand Everyday 721,9,False,0
session_011708,popular,3,12,Keyboard Classic 505,1,False,0
session_011708,popular,4,49,Biography Deluxe 648,3,False,0
session_011708,popular,5,231,Studio Headphones Classic 686,11,False,0
session_011708,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_011708,personalized,2,123,Makeup Brush Set Pro 675,6,True,0
session_011708,personalized,3,121,Sunscreen Classic 799,6,True,0
session_011708,personalized,4,114,Lipstick Compact 868,6,True,0
session_011708,personalized,5,108,Serum Essential 226,6,True,0
session_005921,popular,1,90,Table Lamp Eco 643,5,False,0
session_005921,popular,2,184,Nightstand Everyday 721,9,False,0
session_005921,popular,3,110,Shampoo Everyday 111,6,False,0
session_005921,popular,4,12,Keyboard Classic 505,1,False,0
session_005921,popular,5,49,Biography Deluxe 648,3,False,0
session_005921,personalized,1,198,Car Charger Everyday 607,10,True,0
session_005921,personalized,2,206,Car Vacuum Deluxe 348,10,True,0
session_005921,personalized,3,193,Car Battery Deluxe 488,10,True,0
session_005921,personalized,4,243,Ladder Deluxe 713,12,True,0
session_005921,personalized,5,205,Ice Scraper Deluxe 739,10,True,0
session_011896,popular,1,90,Table Lamp Eco 643,5,False,0
session_011896,popular,2,184,Nightstand Everyday 721,9,False,0
session_011896,popular,3,110,Shampoo Everyday 111,6,False,0
session_011896,popular,4,12,Keyboard Classic 505,1,False,0
session_011896,popular,5,49,Biography Deluxe 648,3,False,0
session_011896,personalized,1,148,Coffee Beans Pro 813,8,True,0
session_011896,personalized,2,160,Granola Premium 789,8,True,0
session_011896,personalized,3,167,Juice Everyday 509,8,True,0
session_011896,personalized,4,158,Pasta Eco 942,8,True,0
session_011896,personalized,5,152,Dark Chocolate Premium 512,8,True,0
session_010628,popular,1,90,Table Lamp Eco 643,5,False,0
session_010628,popular,2,184,Nightstand Everyday 721,9,True,0
session_010628,popular,3,110,Shampoo Everyday 111,6,False,0
session_010628,popular,4,12,Keyboard Classic 505,1,False,0
session_010628,popular,5,49,Biography Deluxe 648,3,False,0
session_010628,personalized,1,184,Nightstand Everyday 721,9,True,0
session_010628,personalized,2,137,Plush Toy Classic 439,7,True,0
session_010628,personalized,3,90,Table Lamp Eco 643,5,False,0
session_010628,personalized,4,181,Coffee Table Eco 857,9,True,0
session_010628,personalized,5,243,Ladder Deluxe 713,12,False,0
session_012001,popular,1,90,Table Lamp Eco 643,5,False,0
session_012001,popular,2,184,Nightstand Everyday 721,9,False,0
session_012001,popular,3,110,Shampoo Everyday 111,6,False,0
session_012001,popular,4,12,Keyboard Classic 505,1,False,0
session_012001,popular,5,231,Studio Headphones Classic 686,11,False,0
session_012001,personalized,1,63,Cookbook Compact 232,3,True,0
session_012001,personalized,2,44,Novel Premium 964,3,True,0
session_012001,personalized,3,50,Biography Essential 819,3,True,0
session_012001,personalized,4,43,Novel Premium 556,3,True,0
session_012001,personalized,5,61,Dictionary Essential 458,3,True,0
session_003470,popular,1,90,Table Lamp Eco 643,5,False,0
session_003470,popular,2,184,Nightstand Everyday 721,9,False,0
session_003470,popular,3,110,Shampoo Everyday 111,6,False,0
session_003470,popular,4,49,Biography Deluxe 648,3,False,0
session_003470,popular,5,76,Tennis Racket Compact 416,4,False,0
session_003470,personalized,1,10,Monitor Classic 784,1,True,0
session_003470,personalized,2,7,Tablet Compact 853,1,True,0
session_003470,personalized,3,14,Mouse Eco 475,1,True,0
session_003470,personalized,4,21,Keyboard Compact 874,1,True,0
session_003470,personalized,5,1,Smartphone Compact 686,1,True,0
session_013017,popular,1,90,Table Lamp Eco 643,5,False,0
session_013017,popular,2,184,Nightstand Everyday 721,9,False,0
session_013017,popular,3,110,Shampoo Everyday 111,6,False,0
session_013017,popular,4,12,Keyboard Classic 505,1,False,0
session_013017,popular,5,49,Biography Deluxe 648,3,True,0
session_013017,personalized,1,49,Biography Deluxe 648,3,True,0
session_013017,personalized,2,52,Fantasy Pro 681,3,True,0
session_013017,personalized,3,44,Novel Premium 964,3,True,0
session_013017,personalized,4,231,Studio Headphones Classic 686,11,True,0
session_013017,personalized,5,50,Biography Essential 819,3,True,0
session_012572,popular,1,90,Table Lamp Eco 643,5,False,0
session_012572,popular,2,110,Shampoo Everyday 111,6,False,0
session_012572,popular,3,49,Biography Deluxe 648,3,False,0
session_012572,popular,4,231,Studio Headphones Classic 686,11,False,0
session_012572,popular,5,76,Tennis Racket Compact 416,4,False,0
session_012572,personalized,1,9,Monitor Premium 997,1,True,0
session_012572,personalized,2,177,Bed Frame Eco 577,9,True,0
session_012572,personalized,3,185,Dining Chair Classic 954,9,True,0
session_012572,personalized,4,182,Coffee Table Pro 626,9,True,0
session_012572,personalized,5,175,Bookshelf Eco 371,9,True,0
session_001179,popular,1,90,Table Lamp Eco 643,5,False,0
session_001179,popular,2,110,Shampoo Everyday 111,6,False,0
session_001179,popular,3,12,Keyboard Classic 505,1,False,1
session_001179,popular,4,49,Biography Deluxe 648,3,False,0
session_001179,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001179,personalized,1,181,Coffee Table Eco 857,9,True,0
session_001179,personalized,2,182,Coffee Table Pro 626,9,True,0
session_001179,personalized,3,175,Bookshelf Eco 371,9,True,0
session_001179,personalized,4,171,Office Chair Deluxe 707,9,True,0
session_001179,personalized,5,169,Sofa Essential 990,9,True,0
session_011059,popular,1,90,Table Lamp Eco 643,5,True,0
session_011059,popular,2,110,Shampoo Everyday 111,6,False,0
session_011059,popular,3,12,Keyboard Classic 505,1,False,0
session_011059,popular,4,49,Biography Deluxe 648,3,False,0
session_011059,popular,5,231,Studio Headphones Classic 686,11,False,0
session_011059,personalized,1,177,Bed Frame Eco 577,9,True,0
session_011059,personalized,2,185,Dining Chair Classic 954,9,True,0
session_011059,personalized,3,90,Table Lamp Eco 643,5,True,0
session_011059,personalized,4,182,Coffee Table Pro 626,9,True,0
session_011059,personalized,5,175,Bookshelf Eco 371,9,True,0
session_000541,popular,1,90,Table Lamp Eco 643,5,False,0
session_000541,popular,2,184,Nightstand Everyday 721,9,False,0
session_000541,popular,3,110,Shampoo Everyday 111,6,False,0
session_000541,popular,4,12,Keyboard Classic 505,1,False,0
session_000541,popular,5,49,Biography Deluxe 648,3,False,0
session_000541,personalized,1,37,Backpack Compact 926,2,True,0
session_000541,personalized,2,41,Boots Compact 911,2,True,0
session_000541,personalized,3,32,Scarf Eco 733,2,True,0
session_000541,personalized,4,38,Cap Compact 731,2,True,0
session_000541,personalized,5,27,Sneakers Compact 248,2,True,0
session_002525,popular,1,90,Table Lamp Eco 643,5,False,0
session_002525,popular,2,184,Nightstand Everyday 721,9,False,0
session_002525,popular,3,110,Shampoo Everyday 111,6,False,0
session_002525,popular,4,12,Keyboard Classic 505,1,False,0
session_002525,popular,5,49,Biography Deluxe 648,3,False,0
session_002525,personalized,1,148,Coffee Beans Pro 813,8,True,0
session_002525,personalized,2,160,Granola Premium 789,8,True,0
session_002525,personalized,3,167,Juice Everyday 509,8,True,0
session_002525,personalized,4,152,Dark Chocolate Premium 512,8,True,0
session_002525,personalized,5,154,Olive Oil Everyday 426,8,True,0
session_002563,popular,1,90,Table Lamp Eco 643,5,False,0
session_002563,popular,2,184,Nightstand Everyday 721,9,False,0
session_002563,popular,3,110,Shampoo Everyday 111,6,False,0
session_002563,popular,4,12,Keyboard Classic 505,1,True,0
session_002563,popular,5,49,Biography Deluxe 648,3,False,0
session_002563,personalized,1,12,Keyboard Classic 505,1,True,0
session_002563,personalized,2,2,Smartphone Compact 854,1,True,0
session_002563,personalized,3,9,Monitor Premium 997,1,True,0
session_002563,personalized,4,6,Headphones Compact 103,1,True,0
session_002563,personalized,5,10,Monitor Classic 784,1,True,0
session_014795,popular,1,90,Table Lamp Eco 643,5,False,0
session_014795,popular,2,184,Nightstand Everyday 721,9,False,0
session_014795,popular,3,12,Keyboard Classic 505,1,False,0
session_014795,popular,4,49,Biography Deluxe 648,3,False,0
session_014795,popular,5,231,Studio Headphones Classic 686,11,False,0
session_014795,personalized,1,123,Makeup Brush Set Pro 675,6,True,0
session_014795,personalized,2,121,Sunscreen Classic 799,6,True,0
session_014795,personalized,3,108,Serum Essential 226,6,True,0
session_014795,personalized,4,114,Lipstick Compact 868,6,True,0
session_014795,personalized,5,115,Lipstick Eco 829,6,True,0
session_008461,popular,1,90,Table Lamp Eco 643,5,False,0
session_008461,popular,2,184,Nightstand Everyday 721,9,True,0
session_008461,popular,3,110,Shampoo Everyday 111,6,False,0
session_008461,popular,4,12,Keyboard Classic 505,1,False,0
session_008461,popular,5,49,Biography Deluxe 648,3,False,0
session_008461,personalized,1,184,Nightstand Everyday 721,9,True,0
session_008461,personalized,2,181,Coffee Table Eco 857,9,True,0
session_008461,personalized,3,185,Dining Chair Classic 954,9,True,0
session_008461,personalized,4,169,Sofa Essential 990,9,True,0
session_008461,personalized,5,175,Bookshelf Eco 371,9,True,0
session_001423,popular,1,90,Table Lamp Eco 643,5,False,0
session_001423,popular,2,184,Nightstand Everyday 721,9,False,0
session_001423,popular,3,110,Shampoo Everyday 111,6,False,0
session_001423,popular,4,12,Keyboard Classic 505,1,False,0
session_001423,popular,5,49,Biography Deluxe 648,3,False,0
session_001423,personalized,1,80,Fitness Band Eco 108,4,True,0
session_001423,personalized,2,68,Dumbbell Set Premium 193,4,True,0
session_001423,personalized,3,75,Football Premium 903,4,True,0
session_001423,personalized,4,65,Running Shoes Deluxe 803,4,True,0
session_001423,personalized,5,67,Yoga Mat Everyday 759,4,True,0
session_005332,popular,1,90,Table Lamp Eco 643,5,False,0
session_005332,popular,2,184,Nightstand Everyday 721,9,False,0
session_005332,popular,3,110,Shampoo Everyday 111,6,False,0
session_005332,popular,4,12,Keyboard Classic 505,1,True,0
session_005332,popular,5,231,Studio Headphones Classic 686,11,False,0
session_005332,personalized,1,12,Keyboard Classic 505,1,True,0
session_005332,personalized,2,2,Smartphone Compact 854,1,True,0
session_005332,personalized,3,9,Monitor Premium 997,1,True,0
session_005332,personalized,4,17,Camera Compact 359,1,True,0
session_005332,personalized,5,6,Headphones Compact 103,1,True,0
session_015301,popular,1,90,Table Lamp Eco 643,5,False,0
session_015301,popular,2,184,Nightstand Everyday 721,9,False,0
session_015301,popular,3,110,Shampoo Everyday 111,6,False,0
session_015301,popular,4,12,Keyboard Classic 505,1,False,0
session_015301,popular,5,231,Studio Headphones Classic 686,11,False,0
session_015301,personalized,1,44,Novel Premium 964,3,True,0
session_015301,personalized,2,50,Biography Essential 819,3,True,0
session_015301,personalized,3,133,Doll Eco 977,7,True,0
session_015301,personalized,4,55,Guide Everyday 453,3,True,1
session_015301,personalized,5,61,Dictionary Essential 458,3,True,0
session_002909,popular,1,90,Table Lamp Eco 643,5,False,0
session_002909,popular,2,184,Nightstand Everyday 721,9,False,0
session_002909,popular,3,110,Shampoo Everyday 111,6,False,0
session_002909,popular,4,12,Keyboard Classic 505,1,False,0
session_002909,popular,5,49,Biography Deluxe 648,3,False,0
session_002909,personalized,1,41,Boots Compact 911,2,True,0
session_002909,personalized,2,37,Backpack Compact 926,2,True,0
session_002909,personalized,3,31,T-shirt Classic 854,2,True,0
session_002909,personalized,4,32,Scarf Eco 733,2,True,0
session_002909,personalized,5,38,Cap Compact 731,2,True,0
session_011904,popular,1,90,Table Lamp Eco 643,5,False,0
session_011904,popular,2,184,Nightstand Everyday 721,9,False,0
session_011904,popular,3,110,Shampoo Everyday 111,6,False,0
session_011904,popular,4,12,Keyboard Classic 505,1,False,0
session_011904,popular,5,49,Biography Deluxe 648,3,False,0
session_011904,personalized,1,224,Ukulele Essential 759,11,True,0
session_011904,personalized,2,230,Effects Pedal Eco 176,11,True,0
session_011904,personalized,3,229,Effects Pedal Essential 260,11,True,0
session_011904,personalized,4,218,Studio Headphones Pro 770,11,True,0
session_011904,personalized,5,226,Drum Sticks Eco 816,11,True,0
session_007010,popular,1,90,Table Lamp Eco 643,5,True,0
session_007010,popular,2,110,Shampoo Everyday 111,6,False,0
session_007010,popular,3,12,Keyboard Classic 505,1,False,0
session_007010,popular,4,49,Biography Deluxe 648,3,False,0
session_007010,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007010,personalized,1,90,Table Lamp Eco 643,5,True,0
session_007010,personalized,2,85,Blender Classic 334,5,True,0
session_007010,personalized,3,181,Coffee Table Eco 857,9,True,0
session_007010,personalized,4,105,Bedding Set Everyday 147,5,True,0
session_007010,personalized,5,185,Dining Chair Classic 954,9,True,0
session_006562,popular,1,12,Keyboard Classic 505,1,False,0
session_006562,popular,2,49,Biography Deluxe 648,3,False,0
session_006562,popular,3,231,Studio Headphones Classic 686,11,False,0
session_006562,popular,4,76,Tennis Racket Compact 416,4,False,0
session_006562,popular,5,127,Building Blocks Premium 126,7,False,0
session_006562,personalized,1,118,Body Lotion Deluxe 734,6,True,0
session_006562,personalized,2,108,Serum Essential 226,6,True,0
session_006562,personalized,3,114,Lipstick Compact 868,6,True,0
session_006562,personalized,4,109,Serum Everyday 923,6,True,0
session_006562,personalized,5,115,Lipstick Eco 829,6,True,0
session_010127,popular,1,90,Table Lamp Eco 643,5,False,0
session_010127,popular,2,184,Nightstand Everyday 721,9,False,0
session_010127,popular,3,110,Shampoo Everyday 111,6,True,0
session_010127,popular,4,12,Keyboard Classic 505,1,False,0
session_010127,popular,5,49,Biography Deluxe 648,3,False,0
session_010127,personalized,1,30,T-shirt Everyday 987,2,True,0
session_010127,personalized,2,41,Boots Compact 911,2,True,0
session_010127,personalized,3,37,Backpack Compact 926,2,True,0
session_010127,personalized,4,110,Shampoo Everyday 111,6,True,0
session_010127,personalized,5,39,Cap Everyday 356,2,True,0
session_013785,popular,1,90,Table Lamp Eco 643,5,False,0
session_013785,popular,2,184,Nightstand Everyday 721,9,False,0
session_013785,popular,3,110,Shampoo Everyday 111,6,False,0
session_013785,popular,4,49,Biography Deluxe 648,3,False,0
session_013785,popular,5,76,Tennis Racket Compact 416,4,False,0
session_013785,personalized,1,7,Tablet Compact 853,1,True,0
session_013785,personalized,2,15,Speaker Pro 628,1,True,0
session_013785,personalized,3,21,Keyboard Compact 874,1,True,0
session_013785,personalized,4,1,Smartphone Compact 686,1,True,0
session_013785,personalized,5,20,Smartwatch Everyday 615,1,True,0
session_013491,popular,1,90,Table Lamp Eco 643,5,False,0
session_013491,popular,2,184,Nightstand Everyday 721,9,False,0
session_013491,popular,3,110,Shampoo Everyday 111,6,False,0
session_013491,popular,4,12,Keyboard Classic 505,1,False,0
session_013491,popular,5,49,Biography Deluxe 648,3,False,0
session_013491,personalized,1,37,Backpack Compact 926,2,True,0
session_013491,personalized,2,31,T-shirt Classic 854,2,True,0
session_013491,personalized,3,23,Jacket Essential 819,2,True,0
session_013491,personalized,4,36,Backpack Classic 759,2,True,0
session_013491,personalized,5,38,Cap Compact 731,2,True,0
session_004324,popular,1,90,Table Lamp Eco 643,5,False,0
session_004324,popular,2,184,Nightstand Everyday 721,9,False,0
session_004324,popular,3,110,Shampoo Everyday 111,6,False,0
session_004324,popular,4,12,Keyboard Classic 505,1,False,0
session_004324,popular,5,49,Biography Deluxe 648,3,False,0
session_004324,personalized,1,243,Ladder Deluxe 713,12,True,0
session_004324,personalized,2,200,Floor Mats Everyday 949,10,True,0
session_004324,personalized,3,247,Spirit Level Eco 157,12,True,0
session_004324,personalized,4,232,Cordless Drill Classic 499,12,True,0
session_004324,personalized,5,235,Screwdriver Set Pro 103,12,True,0
session_004965,popular,1,90,Table Lamp Eco 643,5,False,0
session_004965,popular,2,184,Nightstand Everyday 721,9,False,0
session_004965,popular,3,110,Shampoo Everyday 111,6,False,0
session_004965,popular,4,12,Keyboard Classic 505,1,False,0
session_004965,popular,5,49,Biography Deluxe 648,3,False,0
session_004965,personalized,1,74,Football Deluxe 883,4,True,0
session_004965,personalized,2,75,Football Premium 903,4,True,0
session_004965,personalized,3,30,T-shirt Everyday 987,2,True,0
session_004965,personalized,4,65,Running Shoes Deluxe 803,4,True,0
session_004965,personalized,5,66,Yoga Mat Premium 817,4,True,0
session_002571,popular,1,90,Table Lamp Eco 643,5,False,0
session_002571,popular,2,184,Nightstand Everyday 721,9,False,0
session_002571,popular,3,12,Keyboard Classic 505,1,False,0
session_002571,popular,4,49,Biography Deluxe 648,3,False,0
session_002571,popular,5,231,Studio Headphones Classic 686,11,False,0
session_002571,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_002571,personalized,2,118,Body Lotion Deluxe 734,6,True,0
session_002571,personalized,3,108,Serum Essential 226,6,True,0
session_002571,personalized,4,107,Face Cream Everyday 865,6,True,0
session_002571,personalized,5,115,Lipstick Eco 829,6,True,0
session_007724,popular,1,90,Table Lamp Eco 643,5,False,0
session_007724,popular,2,184,Nightstand Everyday 721,9,False,0
session_007724,popular,3,110,Shampoo Everyday 111,6,True,0
session_007724,popular,4,12,Keyboard Classic 505,1,False,0
session_007724,popular,5,49,Biography Deluxe 648,3,False,0
session_007724,personalized,1,30,T-shirt Everyday 987,2,True,0
session_007724,personalized,2,37,Backpack Compact 926,2,True,0
session_007724,personalized,3,110,Shampoo Everyday 111,6,True,0
session_007724,personalized,4,76,Tennis Racket Compact 416,4,False,0
session_007724,personalized,5,31,T-shirt Classic 854,2,True,0
session_013110,popular,1,90,Table Lamp Eco 643,5,False,0
session_013110,popular,2,184,Nightstand Everyday 721,9,False,0
session_013110,popular,3,110,Shampoo Everyday 111,6,False,0
session_013110,popular,4,12,Keyboard Classic 505,1,False,0
session_013110,popular,5,231,Studio Headphones Classic 686,11,False,0
session_013110,personalized,1,132,Puzzle Everyday 336,7,True,0
session_013110,personalized,2,134,Doll Classic 843,7,True,0
session_013110,personalized,3,142,Paint Set Deluxe 295,7,True,0
session_013110,personalized,4,141,Paint Set Classic 369,7,True,0
session_013110,personalized,5,140,Robot Kit Essential 218,7,True,0
session_001953,popular,1,90,Table Lamp Eco 643,5,False,0
session_001953,popular,2,184,Nightstand Everyday 721,9,False,0
session_001953,popular,3,110,Shampoo Everyday 111,6,False,0
session_001953,popular,4,12,Keyboard Classic 505,1,False,0
session_001953,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001953,personalized,1,127,Building Blocks Premium 126,7,True,0
session_001953,personalized,2,141,Paint Set Classic 369,7,True,1
session_001953,personalized,3,142,Paint Set Deluxe 295,7,True,0
session_001953,personalized,4,140,Robot Kit Essential 218,7,True,0
session_001953,personalized,5,136,RC Car Essential 980,7,True,0
session_001052,popular,1,90,Table Lamp Eco 643,5,False,0
session_001052,popular,2,184,Nightstand Everyday 721,9,False,0
session_001052,popular,3,110,Shampoo Everyday 111,6,False,0
session_001052,popular,4,12,Keyboard Classic 505,1,False,0
session_001052,popular,5,49,Biography Deluxe 648,3,False,0
session_001052,personalized,1,76,Tennis Racket Compact 416,4,True,0
session_001052,personalized,2,80,Fitness Band Eco 108,4,True,0
session_001052,personalized,3,74,Football Deluxe 883,4,True,0
session_001052,personalized,4,68,Dumbbell Set Premium 193,4,True,0
session_001052,personalized,5,66,Yoga Mat Premium 817,4,True,0
session_010657,popular,1,90,Table Lamp Eco 643,5,False,0
session_010657,popular,2,184,Nightstand Everyday 721,9,False,0
session_010657,popular,3,110,Shampoo Everyday 111,6,False,0
session_010657,popular,4,12,Keyboard Classic 505,1,True,0
session_010657,popular,5,49,Biography Deluxe 648,3,False,0
session_010657,personalized,1,160,Granola Premium 789,8,True,0
session_010657,personalized,2,167,Juice Everyday 509,8,True,0
session_010657,personalized,3,158,Pasta Eco 942,8,True,0
session_010657,personalized,4,150,Green Tea Deluxe 321,8,True,0
session_010657,personalized,5,152,Dark Chocolate Premium 512,8,True,0
session_012155,popular,1,90,Table Lamp Eco 643,5,False,0
session_012155,popular,2,184,Nightstand Everyday 721,9,False,0
session_012155,popular,3,110,Shampoo Everyday 111,6,False,0
session_012155,popular,4,49,Biography Deluxe 648,3,False,0
session_012155,popular,5,76,Tennis Racket Compact 416,4,False,0
session_012155,personalized,1,223,Ukulele Premium 117,11,True,0
session_012155,personalized,2,9,Monitor Premium 997,1,True,0
session_012155,personalized,3,224,Ukulele Essential 759,11,True,0
session_012155,personalized,4,230,Effects Pedal Eco 176,11,True,0
session_012155,personalized,5,6,Headphones Compact 103,1,True,0
session_007050,popular,1,90,Table Lamp Eco 643,5,False,0
session_007050,popular,2,184,Nightstand Everyday 721,9,False,0
session_007050,popular,3,110,Shampoo Everyday 111,6,True,1
session_007050,popular,4,12,Keyboard Classic 505,1,False,0
session_007050,popular,5,49,Biography Deluxe 648,3,False,0
session_007050,personalized,1,30,T-shirt Everyday 987,2,True,0
session_007050,personalized,2,37,Backpack Compact 926,2,True,0
session_007050,personalized,3,36,Backpack Classic 759,2,True,0
session_007050,personalized,4,31,T-shirt Classic 854,2,True,0
session_007050,personalized,5,27,Sneakers Compact 248,2,True,0
session_000910,popular,1,90,Table Lamp Eco 643,5,False,0
session_000910,popular,2,184,Nightstand Everyday 721,9,False,0
session_000910,popular,3,12,Keyboard Classic 505,1,False,0
session_000910,popular,4,49,Biography Deluxe 648,3,False,0
session_000910,popular,5,231,Studio Headphones Classic 686,11,False,0
session_000910,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_000910,personalized,2,118,Body Lotion Deluxe 734,6,True,0
session_000910,personalized,3,123,Makeup Brush Set Pro 675,6,True,0
session_000910,personalized,4,121,Sunscreen Classic 799,6,True,0
session_000910,personalized,5,107,Face Cream Everyday 865,6,True,0
session_003685,popular,1,110,Shampoo Everyday 111,6,False,0
session_003685,popular,2,49,Biography Deluxe 648,3,False,0
session_003685,popular,3,231,Studio Headphones Classic 686,11,False,0
session_003685,popular,4,76,Tennis Racket Compact 416,4,False,0
session_003685,popular,5,127,Building Blocks Premium 126,7,False,0
session_003685,personalized,1,181,Coffee Table Eco 857,9,True,0
session_003685,personalized,2,85,Blender Classic 334,5,True,0
session_003685,personalized,3,185,Dining Chair Classic 954,9,True,0
session_003685,personalized,4,175,Bookshelf Eco 371,9,True,0
session_003685,personalized,5,103,Candle Everyday 732,5,True,0
session_006639,popular,1,90,Table Lamp Eco 643,5,False,0
session_006639,popular,2,184,Nightstand Everyday 721,9,False,0
session_006639,popular,3,110,Shampoo Everyday 111,6,False,0
session_006639,popular,4,12,Keyboard Classic 505,1,False,0
session_006639,popular,5,231,Studio Headphones Classic 686,11,False,0
session_006639,personalized,1,76,Tennis Racket Compact 416,4,True,0
session_006639,personalized,2,63,Cookbook Compact 232,3,True,0
session_006639,personalized,3,44,Novel Premium 964,3,True,0
session_006639,personalized,4,43,Novel Premium 556,3,True,0
session_006639,personalized,5,80,Fitness Band Eco 108,4,True,0
session_004643,popular,1,90,Table Lamp Eco 643,5,False,0
session_004643,popular,2,184,Nightstand Everyday 721,9,False,0
session_004643,popular,3,110,Shampoo Everyday 111,6,False,0
session_004643,popular,4,12,Keyboard Classic 505,1,False,0
session_004643,popular,5,49,Biography Deluxe 648,3,False,0
session_004643,personalized,1,80,Fitness Band Eco 108,4,True,1
session_004643,personalized,2,75,Football Premium 903,4,True,0
session_004643,personalized,3,65,Running Shoes Deluxe 803,4,True,0
session_004643,personalized,4,67,Yoga Mat Everyday 759,4,True,0
session_004643,personalized,5,66,Yoga Mat Premium 817,4,True,0
session_010671,popular,1,90,Table Lamp Eco 643,5,False,0
session_010671,popular,2,184,Nightstand Everyday 721,9,False,0
session_010671,popular,3,110,Shampoo Everyday 111,6,False,0
session_010671,popular,4,49,Biography Deluxe 648,3,False,0
session_010671,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010671,personalized,1,198,Car Charger Everyday 607,10,True,0
session_010671,personalized,2,193,Car Battery Deluxe 488,10,True,0
session_010671,personalized,3,2,Smartphone Compact 854,1,True,0
session_010671,personalized,4,9,Monitor Premium 997,1,True,0
session_010671,personalized,5,205,Ice Scraper Deluxe 739,10,True,0
session_004246,popular,1,184,Nightstand Everyday 721,9,False,1
session_004246,popular,2,110,Shampoo Everyday 111,6,False,0
session_004246,popular,3,12,Keyboard Classic 505,1,False,0
session_004246,popular,4,49,Biography Deluxe 648,3,False,1
session_004246,popular,5,231,Studio Headphones Classic 686,11,False,0
session_004246,personalized,1,85,Blender Classic 334,5,True,0
session_004246,personalized,2,93,Towel Set Eco 365,5,True,0
session_004246,personalized,3,103,Candle Everyday 732,5,True,0
session_004246,personalized,4,105,Bedding Set Everyday 147,5,True,0
session_004246,personalized,5,87,Coffee Maker Pro 639,5,True,0
session_010168,popular,1,90,Table Lamp Eco 643,5,False,0
session_010168,popular,2,184,Nightstand Everyday 721,9,False,0
session_010168,popular,3,110,Shampoo Everyday 111,6,False,0
session_010168,popular,4,12,Keyboard Classic 505,1,False,0
session_010168,popular,5,49,Biography Deluxe 648,3,False,0
session_010168,personalized,1,79,Sports Bottle Premium 411,4,True,0
session_010168,personalized,2,64,Running Shoes Pro 936,4,True,0
session_010168,personalized,3,81,Fitness Band Deluxe 954,4,True,0
session_010168,personalized,4,72,Tent Classic 324,4,True,0
session_010168,personalized,5,69,Dumbbell Set Pro 352,4,True,0
session_012270,popular,1,90,Table Lamp Eco 643,5,False,0
session_012270,popular,2,184,Nightstand Everyday 721,9,False,0
session_012270,popular,3,110,Shampoo Everyday 111,6,False,0
session_012270,popular,4,12,Keyboard Classic 505,1,False,0
session_012270,popular,5,231,Studio Headphones Classic 686,11,False,0
session_012270,personalized,1,133,Doll Eco 977,7,True,1
session_012270,personalized,2,137,Plush Toy Classic 439,7,True,0
session_012270,personalized,3,60,Poetry Everyday 604,3,True,0
session_012270,personalized,4,148,Coffee Beans Pro 813,8,False,0
session_012270,personalized,5,132,Puzzle Everyday 336,7,True,0
session_002151,popular,1,90,Table Lamp Eco 643,5,True,0
session_002151,popular,2,184,Nightstand Everyday 721,9,True,0
session_002151,popular,3,110,Shampoo Everyday 111,6,False,0
session_002151,popular,4,12,Keyboard Classic 505,1,False,0
session_002151,popular,5,49,Biography Deluxe 648,3,False,0
session_002151,personalized,1,184,Nightstand Everyday 721,9,True,0
session_002151,personalized,2,177,Bed Frame Eco 577,9,True,0
session_002151,personalized,3,185,Dining Chair Classic 954,9,True,0
session_002151,personalized,4,90,Table Lamp Eco 643,5,True,0
session_002151,personalized,5,171,Office Chair Deluxe 707,9,True,0
session_009317,popular,1,90,Table Lamp Eco 643,5,False,0
session_009317,popular,2,184,Nightstand Everyday 721,9,False,0
session_009317,popular,3,110,Shampoo Everyday 111,6,False,0
session_009317,popular,4,12,Keyboard Classic 505,1,False,0
session_009317,popular,5,231,Studio Headphones Classic 686,11,True,0
session_009317,personalized,1,52,Fantasy Pro 681,3,True,0
session_009317,personalized,2,60,Poetry Everyday 604,3,True,0
session_009317,personalized,3,44,Novel Premium 964,3,True,0
session_009317,personalized,4,63,Cookbook Compact 232,3,True,0
session_009317,personalized,5,50,Biography Essential 819,3,True,0
session_007146,popular,1,90,Table Lamp Eco 643,5,False,0
session_007146,popular,2,184,Nightstand Everyday 721,9,False,0
session_007146,popular,3,110,Shampoo Everyday 111,6,False,0
session_007146,popular,4,12,Keyboard Classic 505,1,False,0
session_007146,popular,5,49,Biography Deluxe 648,3,False,0
session_007146,personalized,1,249,Work Gloves Compact 227,12,True,0
session_007146,personalized,2,232,Cordless Drill Classic 499,12,True,1
session_007146,personalized,3,247,Spirit Level Eco 157,12,True,0
session_007146,personalized,4,239,Tape Measure Premium 980,12,True,0
session_007146,personalized,5,205,Ice Scraper Deluxe 739,10,True,0
session_011287,popular,1,90,Table Lamp Eco 643,5,False,0
session_011287,popular,2,184,Nightstand Everyday 721,9,False,0
session_011287,popular,3,110,Shampoo Everyday 111,6,True,0
session_011287,popular,4,12,Keyboard Classic 505,1,False,0
session_011287,popular,5,49,Biography Deluxe 648,3,False,0
session_011287,personalized,1,30,T-shirt Everyday 987,2,True,0
session_011287,personalized,2,41,Boots Compact 911,2,True,0
session_011287,personalized,3,37,Backpack Compact 926,2,True,0
session_011287,personalized,4,31,T-shirt Classic 854,2,True,0
session_011287,personalized,5,36,Backpack Classic 759,2,True,0
session_011132,popular,1,90,Table Lamp Eco 643,5,False,1
session_011132,popular,2,184,Nightstand Everyday 721,9,False,0
session_011132,popular,3,110,Shampoo Everyday 111,6,False,0
session_011132,popular,4,49,Biography Deluxe 648,3,False,0
session_011132,popular,5,231,Studio Headphones Classic 686,11,False,0
session_011132,personalized,1,9,Monitor Premium 997,1,True,0
session_011132,personalized,2,6,Headphones Compact 103,1,True,0
session_011132,personalized,3,17,Camera Compact 359,1,True,0
session_011132,personalized,4,13,Mouse Deluxe 406,1,True,0
session_011132,personalized,5,10,Monitor Classic 784,1,True,0
session_007085,popular,1,90,Table Lamp Eco 643,5,False,0
session_007085,popular,2,184,Nightstand Everyday 721,9,False,0
session_007085,popular,3,110,Shampoo Everyday 111,6,False,0
session_007085,popular,4,12,Keyboard Classic 505,1,False,0
session_007085,popular,5,49,Biography Deluxe 648,3,False,0
session_007085,personalized,1,160,Granola Premium 789,8,True,1
session_007085,personalized,2,167,Juice Everyday 509,8,True,0
session_007085,personalized,3,150,Green Tea Deluxe 321,8,True,0
session_007085,personalized,4,154,Olive Oil Everyday 426,8,True,0
session_007085,personalized,5,152,Dark Chocolate Premium 512,8,True,0
session_012696,popular,1,90,Table Lamp Eco 643,5,False,0
session_012696,popular,2,184,Nightstand Everyday 721,9,False,0
session_012696,popular,3,110,Shampoo Everyday 111,6,False,0
session_012696,popular,4,12,Keyboard Classic 505,1,False,0
session_012696,popular,5,49,Biography Deluxe 648,3,False,0
session_012696,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_012696,personalized,2,223,Ukulele Premium 117,11,True,0
session_012696,personalized,3,224,Ukulele Essential 759,11,True,0
session_012696,personalized,4,230,Effects Pedal Eco 176,11,True,0
session_012696,personalized,5,229,Effects Pedal Essential 260,11,True,0
session_004415,popular,1,90,Table Lamp Eco 643,5,False,1
session_004415,popular,2,184,Nightstand Everyday 721,9,False,0
session_004415,popular,3,110,Shampoo Everyday 111,6,False,0
session_004415,popular,4,12,Keyboard Classic 505,1,True,0
session_004415,popular,5,49,Biography Deluxe 648,3,False,0
session_004415,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_004415,personalized,2,224,Ukulele Essential 759,11,True,0
session_004415,personalized,3,12,Keyboard Classic 505,1,True,0
session_004415,personalized,4,229,Effects Pedal Essential 260,11,True,0
session_004415,personalized,5,218,Studio Headphones Pro 770,11,True,0
session_001651,popular,1,184,Nightstand Everyday 721,9,False,0
session_001651,popular,2,110,Shampoo Everyday 111,6,False,0
session_001651,popular,3,12,Keyboard Classic 505,1,False,0
session_001651,popular,4,49,Biography Deluxe 648,3,False,0
session_001651,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001651,personalized,1,103,Candle Everyday 732,5,True,0
session_001651,personalized,2,87,Coffee Maker Pro 639,5,True,0
session_001651,personalized,3,88,Coffee Maker Compact 260,5,True,0
session_001651,personalized,4,95,Cookware Set Premium 431,5,True,0
session_001651,personalized,5,97,Rug Pro 262,5,True,0
session_000680,popular,1,90,Table Lamp Eco 643,5,False,0
session_000680,popular,2,184,Nightstand Everyday 721,9,False,0
session_000680,popular,3,110,Shampoo Everyday 111,6,False,0
session_000680,popular,4,49,Biography Deluxe 648,3,False,0
session_000680,popular,5,231,Studio Headphones Classic 686,11,False,0
session_000680,personalized,1,9,Monitor Premium 997,1,True,0
session_000680,personalized,2,6,Headphones Compact 103,1,True,0
session_000680,personalized,3,17,Camera Compact 359,1,True,0
session_000680,personalized,4,13,Mouse Deluxe 406,1,True,0
session_000680,personalized,5,10,Monitor Classic 784,1,True,0
session_005638,popular,1,90,Table Lamp Eco 643,5,True,0
session_005638,popular,2,184,Nightstand Everyday 721,9,False,0
session_005638,popular,3,110,Shampoo Everyday 111,6,False,0
session_005638,popular,4,49,Biography Deluxe 648,3,False,0
session_005638,popular,5,231,Studio Headphones Classic 686,11,False,0
session_005638,personalized,1,17,Camera Compact 359,1,True,0
session_005638,personalized,2,13,Mouse Deluxe 406,1,True,0
session_005638,personalized,3,10,Monitor Classic 784,1,True,0
session_005638,personalized,4,7,Tablet Compact 853,1,True,0
session_005638,personalized,5,21,Keyboard Compact 874,1,True,0
session_002154,popular,1,90,Table Lamp Eco 643,5,False,0
session_002154,popular,2,184,Nightstand Everyday 721,9,False,0
session_002154,popular,3,110,Shampoo Everyday 111,6,False,0
session_002154,popular,4,12,Keyboard Classic 505,1,False,0
session_002154,popular,5,49,Biography Deluxe 648,3,False,0
session_002154,personalized,1,41,Boots Compact 911,2,True,0
session_002154,personalized,2,37,Backpack Compact 926,2,True,0
session_002154,personalized,3,31,T-shirt Classic 854,2,True,0
session_002154,personalized,4,90,Table Lamp Eco 643,5,False,0
session_002154,personalized,5,23,Jacket Essential 819,2,True,0
session_009696,popular,1,90,Table Lamp Eco 643,5,False,0
session_009696,popular,2,184,Nightstand Everyday 721,9,False,0
session_009696,popular,3,110,Shampoo Everyday 111,6,False,0
session_009696,popular,4,49,Biography Deluxe 648,3,False,0
session_009696,popular,5,231,Studio Headphones Classic 686,11,False,0
session_009696,personalized,1,2,Smartphone Compact 854,1,True,0
session_009696,personalized,2,9,Monitor Premium 997,1,True,0
session_009696,personalized,3,13,Mouse Deluxe 406,1,True,0
session_009696,personalized,4,6,Headphones Compact 103,1,True,0
session_009696,personalized,5,21,Keyboard Compact 874,1,True,0
session_009583,popular,1,90,Table Lamp Eco 643,5,False,0
session_009583,popular,2,184,Nightstand Everyday 721,9,False,0
session_009583,popular,3,110,Shampoo Everyday 111,6,False,0
session_009583,popular,4,12,Keyboard Classic 505,1,False,0
session_009583,popular,5,231,Studio Headphones Classic 686,11,False,0
session_009583,personalized,1,60,Poetry Everyday 604,3,True,0
session_009583,personalized,2,50,Biography Essential 819,3,True,0
session_009583,personalized,3,43,Novel Premium 556,3,True,0
session_009583,personalized,4,61,Dictionary Essential 458,3,True,0
session_009583,personalized,5,55,Guide Everyday 453,3,True,0
session_004775,popular,1,90,Table Lamp Eco 643,5,False,0
session_004775,popular,2,184,Nightstand Everyday 721,9,True,0
session_004775,popular,3,12,Keyboard Classic 505,1,False,0
session_004775,popular,4,49,Biography Deluxe 648,3,False,0
session_004775,popular,5,231,Studio Headphones Classic 686,11,False,0
session_004775,personalized,1,184,Nightstand Everyday 721,9,True,0
session_004775,personalized,2,181,Coffee Table Eco 857,9,True,0
session_004775,personalized,3,185,Dining Chair Classic 954,9,True,0
session_004775,personalized,4,182,Coffee Table Pro 626,9,True,0
session_004775,personalized,5,175,Bookshelf Eco 371,9,True,0
session_015263,popular,1,90,Table Lamp Eco 643,5,False,0
session_015263,popular,2,184,Nightstand Everyday 721,9,False,0
session_015263,popular,3,110,Shampoo Everyday 111,6,False,0
session_015263,popular,4,12,Keyboard Classic 505,1,False,0
session_015263,popular,5,231,Studio Headphones Classic 686,11,False,0
session_015263,personalized,1,60,Poetry Everyday 604,3,True,0
session_015263,personalized,2,44,Novel Premium 964,3,True,0
session_015263,personalized,3,132,Puzzle Everyday 336,7,True,0
session_015263,personalized,4,50,Biography Essential 819,3,True,0
session_015263,personalized,5,134,Doll Classic 843,7,True,0
session_007241,popular,1,90,Table Lamp Eco 643,5,False,0
session_007241,popular,2,184,Nightstand Everyday 721,9,False,0
session_007241,popular,3,110,Shampoo Everyday 111,6,False,0
session_007241,popular,4,12,Keyboard Classic 505,1,False,0
session_007241,popular,5,49,Biography Deluxe 648,3,False,0
session_007241,personalized,1,160,Granola Premium 789,8,True,0
session_007241,personalized,2,158,Pasta Eco 942,8,True,0
session_007241,personalized,3,152,Dark Chocolate Premium 512,8,True,0
session_007241,personalized,4,150,Green Tea Deluxe 321,8,True,0
session_007241,personalized,5,154,Olive Oil Everyday 426,8,True,0
session_007628,popular,1,90,Table Lamp Eco 643,5,False,0
session_007628,popular,2,184,Nightstand Everyday 721,9,False,0
session_007628,popular,3,110,Shampoo Everyday 111,6,False,0
session_007628,popular,4,12,Keyboard Classic 505,1,False,0
session_007628,popular,5,49,Biography Deluxe 648,3,False,0
session_007628,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_007628,personalized,2,206,Car Vacuum Deluxe 348,10,True,0
session_007628,personalized,3,208,Jump Starter Essential 942,10,True,0
session_007628,personalized,4,205,Ice Scraper Deluxe 739,10,True,0
session_007628,personalized,5,199,Car Charger Everyday 299,10,True,0
session_010443,popular,1,90,Table Lamp Eco 643,5,False,0
session_010443,popular,2,184,Nightstand Everyday 721,9,False,0
session_010443,popular,3,110,Shampoo Everyday 111,6,False,0
session_010443,popular,4,49,Biography Deluxe 648,3,False,0
session_010443,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010443,personalized,1,9,Monitor Premium 997,1,True,0
session_010443,personalized,2,6,Headphones Compact 103,1,True,0
session_010443,personalized,3,17,Camera Compact 359,1,True,0
session_010443,personalized,4,10,Monitor Classic 784,1,True,0
session_010443,personalized,5,7,Tablet Compact 853,1,True,0
session_006275,popular,1,90,Table Lamp Eco 643,5,False,0
session_006275,popular,2,184,Nightstand Everyday 721,9,False,0
session_006275,popular,3,110,Shampoo Everyday 111,6,False,0
session_006275,popular,4,12,Keyboard Classic 505,1,False,0
session_006275,popular,5,49,Biography Deluxe 648,3,False,0
session_006275,personalized,1,133,Doll Eco 977,7,True,0
session_006275,personalized,2,137,Plush Toy Classic 439,7,True,0
session_006275,personalized,3,132,Puzzle Everyday 336,7,True,0
session_006275,personalized,4,134,Doll Classic 843,7,True,0
session_006275,personalized,5,141,Paint Set Classic 369,7,True,0
session_013581,popular,1,90,Table Lamp Eco 643,5,False,0
session_013581,popular,2,184,Nightstand Everyday 721,9,False,0
session_013581,popular,3,110,Shampoo Everyday 111,6,False,0
session_013581,popular,4,12,Keyboard Classic 505,1,False,0
session_013581,popular,5,231,Studio Headphones Classic 686,11,False,0
session_013581,personalized,1,52,Fantasy Pro 681,3,True,0
session_013581,personalized,2,63,Cookbook Compact 232,3,True,0
session_013581,personalized,3,44,Novel Premium 964,3,True,0
session_013581,personalized,4,50,Biography Essential 819,3,True,0
session_013581,personalized,5,43,Novel Premium 556,3,True,0
session_003078,popular,1,90,Table Lamp Eco 643,5,False,0
session_003078,popular,2,184,Nightstand Everyday 721,9,False,0
session_003078,popular,3,110,Shampoo Everyday 111,6,False,0
session_003078,popular,4,12,Keyboard Classic 505,1,False,0
session_003078,popular,5,49,Biography Deluxe 648,3,False,0
session_003078,personalized,1,68,Dumbbell Set Premium 193,4,True,0
session_003078,personalized,2,75,Football Premium 903,4,True,0
session_003078,personalized,3,65,Running Shoes Deluxe 803,4,True,0
session_003078,personalized,4,67,Yoga Mat Everyday 759,4,True,0
session_003078,personalized,5,66,Yoga Mat Premium 817,4,True,0
session_009765,popular,1,90,Table Lamp Eco 643,5,False,0
session_009765,popular,2,184,Nightstand Everyday 721,9,False,0
session_009765,popular,3,110,Shampoo Everyday 111,6,False,0
session_009765,popular,4,12,Keyboard Classic 505,1,False,0
session_009765,popular,5,49,Biography Deluxe 648,3,False,0
session_009765,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_009765,personalized,2,243,Ladder Deluxe 713,12,True,0
session_009765,personalized,3,198,Car Charger Everyday 607,10,True,1
session_009765,personalized,4,234,Screwdriver Set Eco 897,12,True,0
session_009765,personalized,5,232,Cordless Drill Classic 499,12,True,0
session_005593,popular,1,90,Table Lamp Eco 643,5,False,0
session_005593,popular,2,184,Nightstand Everyday 721,9,False,0
session_005593,popular,3,110,Shampoo Everyday 111,6,False,0
session_005593,popular,4,12,Keyboard Classic 505,1,False,0
session_005593,popular,5,49,Biography Deluxe 648,3,False,0
session_005593,personalized,1,167,Juice Everyday 509,8,True,0
session_005593,personalized,2,158,Pasta Eco 942,8,True,0
session_005593,personalized,3,152,Dark Chocolate Premium 512,8,True,0
session_005593,personalized,4,150,Green Tea Deluxe 321,8,True,0
session_005593,personalized,5,154,Olive Oil Everyday 426,8,True,0
session_005032,popular,1,90,Table Lamp Eco 643,5,False,0
session_005032,popular,2,184,Nightstand Everyday 721,9,False,0
session_005032,popular,3,110,Shampoo Everyday 111,6,False,0
session_005032,popular,4,12,Keyboard Classic 505,1,False,0
session_005032,popular,5,49,Biography Deluxe 648,3,False,0
session_005032,personalized,1,243,Ladder Deluxe 713,12,True,0
session_005032,personalized,2,198,Car Charger Everyday 607,10,True,0
session_005032,personalized,3,206,Car Vacuum Deluxe 348,10,True,0
session_005032,personalized,4,234,Screwdriver Set Eco 897,12,True,0
session_005032,personalized,5,193,Car Battery Deluxe 488,10,True,0
session_006687,popular,1,12,Keyboard Classic 505,1,False,0
session_006687,popular,2,49,Biography Deluxe 648,3,False,0
session_006687,popular,3,231,Studio Headphones Classic 686,11,False,0
session_006687,popular,4,76,Tennis Racket Compact 416,4,False,0
session_006687,popular,5,127,Building Blocks Premium 126,7,False,0
session_006687,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_006687,personalized,2,247,Spirit Level Eco 157,12,True,0
session_006687,personalized,3,118,Body Lotion Deluxe 734,6,True,0
session_006687,personalized,4,123,Makeup Brush Set Pro 675,6,True,0
session_006687,personalized,5,121,Sunscreen Classic 799,6,True,0
session_011312,popular,1,90,Table Lamp Eco 643,5,False,0
session_011312,popular,2,184,Nightstand Everyday 721,9,False,0
session_011312,popular,3,110,Shampoo Everyday 111,6,False,0
session_011312,popular,4,12,Keyboard Classic 505,1,False,0
session_011312,popular,5,49,Biography Deluxe 648,3,False,0
session_011312,personalized,1,243,Ladder Deluxe 713,12,True,0
session_011312,personalized,2,249,Work Gloves Compact 227,12,True,0
session_011312,personalized,3,234,Screwdriver Set Eco 897,12,True,0
session_011312,personalized,4,232,Cordless Drill Classic 499,12,True,0
session_011312,personalized,5,247,Spirit Level Eco 157,12,True,0
session_008303,popular,1,90,Table Lamp Eco 643,5,False,0
session_008303,popular,2,184,Nightstand Everyday 721,9,False,0
session_008303,popular,3,110,Shampoo Everyday 111,6,False,0
session_008303,popular,4,12,Keyboard Classic 505,1,False,0
session_008303,popular,5,49,Biography Deluxe 648,3,False,0
session_008303,personalized,1,80,Fitness Band Eco 108,4,True,0
session_008303,personalized,2,75,Football Premium 903,4,True,0
session_008303,personalized,3,66,Yoga Mat Premium 817,4,True,0
session_008303,personalized,4,67,Yoga Mat Everyday 759,4,True,0
session_008303,personalized,5,73,Tent Classic 332,4,True,0
session_005131,popular,1,90,Table Lamp Eco 643,5,False,0
session_005131,popular,2,184,Nightstand Everyday 721,9,False,0
session_005131,popular,3,12,Keyboard Classic 505,1,False,0
session_005131,popular,4,49,Biography Deluxe 648,3,False,0
session_005131,popular,5,231,Studio Headphones Classic 686,11,False,0
session_005131,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_005131,personalized,2,123,Makeup Brush Set Pro 675,6,True,0
session_005131,personalized,3,30,T-shirt Everyday 987,2,True,0
session_005131,personalized,4,37,Backpack Compact 926,2,True,0
session_005131,personalized,5,114,Lipstick Compact 868,6,True,0
session_003305,popular,1,90,Table Lamp Eco 643,5,False,0
session_003305,popular,2,184,Nightstand Everyday 721,9,False,0
session_003305,popular,3,110,Shampoo Everyday 111,6,False,0
session_003305,popular,4,12,Keyboard Classic 505,1,False,0
session_003305,popular,5,49,Biography Deluxe 648,3,True,0
session_003305,personalized,1,49,Biography Deluxe 648,3,True,0
session_003305,personalized,2,137,Plush Toy Classic 439,7,True,0
session_003305,personalized,3,60,Poetry Everyday 604,3,True,0
session_003305,personalized,4,132,Puzzle Everyday 336,7,True,0
session_003305,personalized,5,44,Novel Premium 964,3,True,0
session_006720,popular,1,90,Table Lamp Eco 643,5,True,0
session_006720,popular,2,110,Shampoo Everyday 111,6,False,0
session_006720,popular,3,12,Keyboard Classic 505,1,False,0
session_006720,popular,4,49,Biography Deluxe 648,3,False,0
session_006720,popular,5,231,Studio Headphones Classic 686,11,False,0
session_006720,personalized,1,90,Table Lamp Eco 643,5,True,0
session_006720,personalized,2,105,Bedding Set Everyday 147,5,True,0
session_006720,personalized,3,103,Candle Everyday 732,5,True,0
session_006720,personalized,4,86,Blender Everyday 283,5,True,0
session_006720,personalized,5,87,Coffee Maker Pro 639,5,True,0
session_001369,popular,1,90,Table Lamp Eco 643,5,False,0
session_001369,popular,2,184,Nightstand Everyday 721,9,False,0
session_001369,popular,3,110,Shampoo Everyday 111,6,False,0
session_001369,popular,4,12,Keyboard Classic 505,1,False,0
session_001369,popular,5,49,Biography Deluxe 648,3,False,0
session_001369,personalized,1,132,Puzzle Everyday 336,7,True,0
session_001369,personalized,2,134,Doll Classic 843,7,True,0
session_001369,personalized,3,129,Board Game Deluxe 308,7,True,0
session_001369,personalized,4,136,RC Car Essential 980,7,True,0
session_001369,personalized,5,143,Toy Train Deluxe 965,7,True,0
session_008547,popular,1,184,Nightstand Everyday 721,9,False,0
session_008547,popular,2,110,Shampoo Everyday 111,6,False,0
session_008547,popular,3,12,Keyboard Classic 505,1,False,0
session_008547,popular,4,49,Biography Deluxe 648,3,False,0
session_008547,popular,5,231,Studio Headphones Classic 686,11,False,0
session_008547,personalized,1,93,Towel Set Eco 365,5,True,0
session_008547,personalized,2,160,Granola Premium 789,8,True,0
session_008547,personalized,3,105,Bedding Set Everyday 147,5,True,0
session_008547,personalized,4,103,Candle Everyday 732,5,True,0
session_008547,personalized,5,167,Juice Everyday 509,8,True,0
session_001452,popular,1,90,Table Lamp Eco 643,5,False,1
session_001452,popular,2,184,Nightstand Everyday 721,9,False,0
session_001452,popular,3,110,Shampoo Everyday 111,6,False,0
session_001452,popular,4,12,Keyboard Classic 505,1,False,0
session_001452,popular,5,49,Biography Deluxe 648,3,False,0
session_001452,personalized,1,30,T-shirt Everyday 987,2,True,0
session_001452,personalized,2,37,Backpack Compact 926,2,True,0
session_001452,personalized,3,36,Backpack Classic 759,2,True,0
session_001452,personalized,4,31,T-shirt Classic 854,2,True,0
session_001452,personalized,5,23,Jacket Essential 819,2,True,0
session_003075,popular,1,90,Table Lamp Eco 643,5,True,0
session_003075,popular,2,184,Nightstand Everyday 721,9,False,0
session_003075,popular,3,110,Shampoo Everyday 111,6,False,0
session_003075,popular,4,12,Keyboard Classic 505,1,False,0
session_003075,popular,5,49,Biography Deluxe 648,3,False,0
session_003075,personalized,1,90,Table Lamp Eco 643,5,True,0
session_003075,personalized,2,105,Bedding Set Everyday 147,5,True,0
session_003075,personalized,3,94,Towel Set Pro 801,5,True,0
session_003075,personalized,4,89,Table Lamp Deluxe 218,5,True,0
session_003075,personalized,5,87,Coffee Maker Pro 639,5,True,0
session_008677,popular,1,90,Table Lamp Eco 643,5,False,0
session_008677,popular,2,184,Nightstand Everyday 721,9,False,0
session_008677,popular,3,12,Keyboard Classic 505,1,False,0
session_008677,popular,4,49,Biography Deluxe 648,3,False,0
session_008677,popular,5,231,Studio Headphones Classic 686,11,False,0
session_008677,personalized,1,123,Makeup Brush Set Pro 675,6,True,0
session_008677,personalized,2,108,Serum Essential 226,6,True,0
session_008677,personalized,3,107,Face Cream Everyday 865,6,True,0
session_008677,personalized,4,114,Lipstick Compact 868,6,True,0
session_008677,personalized,5,109,Serum Everyday 923,6,True,0
session_008269,popular,1,90,Table Lamp Eco 643,5,False,0
session_008269,popular,2,184,Nightstand Everyday 721,9,False,0
session_008269,popular,3,110,Shampoo Everyday 111,6,False,0
session_008269,popular,4,12,Keyboard Classic 505,1,False,0
session_008269,popular,5,49,Biography Deluxe 648,3,False,0
session_008269,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_008269,personalized,2,198,Car Charger Everyday 607,10,True,0
session_008269,personalized,3,208,Jump Starter Essential 942,10,True,0
session_008269,personalized,4,205,Ice Scraper Deluxe 739,10,True,0
session_008269,personalized,5,199,Car Charger Everyday 299,10,True,0
session_006655,popular,1,90,Table Lamp Eco 643,5,False,0
session_006655,popular,2,184,Nightstand Everyday 721,9,False,0
session_006655,popular,3,110,Shampoo Everyday 111,6,False,0
session_006655,popular,4,12,Keyboard Classic 505,1,False,0
session_006655,popular,5,49,Biography Deluxe 648,3,False,0
session_006655,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_006655,personalized,2,232,Cordless Drill Classic 499,12,True,0
session_006655,personalized,3,249,Work Gloves Compact 227,12,True,0
session_006655,personalized,4,234,Screwdriver Set Eco 897,12,True,0
session_006655,personalized,5,198,Car Charger Everyday 607,10,True,0
session_004245,popular,1,90,Table Lamp Eco 643,5,False,0
session_004245,popular,2,184,Nightstand Everyday 721,9,False,0
session_004245,popular,3,110,Shampoo Everyday 111,6,False,0
session_004245,popular,4,49,Biography Deluxe 648,3,False,0
session_004245,popular,5,231,Studio Headphones Classic 686,11,False,0
session_004245,personalized,1,6,Headphones Compact 103,1,True,0
session_004245,personalized,2,17,Camera Compact 359,1,True,0
session_004245,personalized,3,13,Mouse Deluxe 406,1,True,1
session_004245,personalized,4,7,Tablet Compact 853,1,True,0
session_004245,personalized,5,200,Floor Mats Everyday 949,10,True,0
session_001506,popular,1,90,Table Lamp Eco 643,5,False,0
session_001506,popular,2,184,Nightstand Everyday 721,9,False,0
session_001506,popular,3,110,Shampoo Everyday 111,6,False,0
session_001506,popular,4,12,Keyboard Classic 505,1,False,0
session_001506,popular,5,49,Biography Deluxe 648,3,False,0
session_001506,personalized,1,127,Building Blocks Premium 126,7,True,0
session_001506,personalized,2,132,Puzzle Everyday 336,7,True,0
session_001506,personalized,3,141,Paint Set Classic 369,7,True,0
session_001506,personalized,4,134,Doll Classic 843,7,True,0
session_001506,personalized,5,140,Robot Kit Essential 218,7,True,0
session_001377,popular,1,90,Table Lamp Eco 643,5,False,0
session_001377,popular,2,184,Nightstand Everyday 721,9,False,0
session_001377,popular,3,12,Keyboard Classic 505,1,False,0
session_001377,popular,4,49,Biography Deluxe 648,3,False,0
session_001377,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001377,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_001377,personalized,2,118,Body Lotion Deluxe 734,6,True,0
session_001377,personalized,3,125,Beard Trimmer Premium 354,6,True,0
session_001377,personalized,4,123,Makeup Brush Set Pro 675,6,True,0
session_001377,personalized,5,121,Sunscreen Classic 799,6,True,0
session_012484,popular,1,184,Nightstand Everyday 721,9,True,0
session_012484,popular,2,110,Shampoo Everyday 111,6,False,0
session_012484,popular,3,12,Keyboard Classic 505,1,False,0
session_012484,popular,4,49,Biography Deluxe 648,3,False,0
session_012484,popular,5,231,Studio Headphones Classic 686,11,False,0
session_012484,personalized,1,184,Nightstand Everyday 721,9,True,0
session_012484,personalized,2,181,Coffee Table Eco 857,9,True,0
session_012484,personalized,3,185,Dining Chair Classic 954,9,True,0
session_012484,personalized,4,85,Blender Classic 334,5,True,0
session_012484,personalized,5,182,Coffee Table Pro 626,9,True,0
session_013042,popular,1,90,Table Lamp Eco 643,5,False,0
session_013042,popular,2,184,Nightstand Everyday 721,9,False,0
session_013042,popular,3,110,Shampoo Everyday 111,6,False,0
session_013042,popular,4,12,Keyboard Classic 505,1,False,0
session_013042,popular,5,49,Biography Deluxe 648,3,False,0
session_013042,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_013042,personalized,2,198,Car Charger Everyday 607,10,True,0
session_013042,personalized,3,243,Ladder Deluxe 713,12,True,0
session_013042,personalized,4,249,Work Gloves Compact 227,12,True,0
session_013042,personalized,5,247,Spirit Level Eco 157,12,True,0
session_008772,popular,1,90,Table Lamp Eco 643,5,False,0
session_008772,popular,2,184,Nightstand Everyday 721,9,False,0
session_008772,popular,3,110,Shampoo Everyday 111,6,False,0
session_008772,popular,4,12,Keyboard Classic 505,1,False,0
session_008772,popular,5,49,Biography Deluxe 648,3,False,0
session_008772,personalized,1,76,Tennis Racket Compact 416,4,True,1
session_008772,personalized,2,80,Fitness Band Eco 108,4,True,0
session_008772,personalized,3,75,Football Premium 903,4,True,0
session_008772,personalized,4,68,Dumbbell Set Premium 193,4,True,0
session_008772,personalized,5,65,Running Shoes Deluxe 803,4,True,0
session_005222,popular,1,90,Table Lamp Eco 643,5,False,0
session_005222,popular,2,184,Nightstand Everyday 721,9,False,0
session_005222,popular,3,110,Shampoo Everyday 111,6,False,0
session_005222,popular,4,12,Keyboard Classic 505,1,False,0
session_005222,popular,5,49,Biography Deluxe 648,3,False,0
session_005222,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_005222,personalized,2,224,Ukulele Essential 759,11,True,0
session_005222,personalized,3,230,Effects Pedal Eco 176,11,True,0
session_005222,personalized,4,225,Drum Sticks Pro 333,11,True,0
session_005222,personalized,5,218,Studio Headphones Pro 770,11,True,0
session_014756,popular,1,184,Nightstand Everyday 721,9,False,1
session_014756,popular,2,110,Shampoo Everyday 111,6,False,0
session_014756,popular,3,12,Keyboard Classic 505,1,False,0
session_014756,popular,4,49,Biography Deluxe 648,3,False,0
session_014756,popular,5,231,Studio Headphones Classic 686,11,False,0
session_014756,personalized,1,167,Juice Everyday 509,8,True,0
session_014756,personalized,2,156,Honey Everyday 491,8,True,0
session_014756,personalized,3,168,Juice Everyday 512,8,True,0
session_014756,personalized,4,161,Granola Deluxe 683,8,True,0
session_014756,personalized,5,155,Olive Oil Deluxe 890,8,True,0
session_010747,popular,1,90,Table Lamp Eco 643,5,False,0
session_010747,popular,2,184,Nightstand Everyday 721,9,False,0
session_010747,popular,3,110,Shampoo Everyday 111,6,False,0
session_010747,popular,4,49,Biography Deluxe 648,3,False,0
session_010747,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010747,personalized,1,206,Car Vacuum Deluxe 348,10,True,0
session_010747,personalized,2,205,Ice Scraper Deluxe 739,10,True,0
session_010747,personalized,3,193,Car Battery Deluxe 488,10,True,0
session_010747,personalized,4,199,Car Charger Everyday 299,10,True,0
session_010747,personalized,5,208,Jump Starter Essential 942,10,True,0
session_007566,popular,1,90,Table Lamp Eco 643,5,False,0
session_007566,popular,2,184,Nightstand Everyday 721,9,False,0
session_007566,popular,3,110,Shampoo Everyday 111,6,False,0
session_007566,popular,4,12,Keyboard Classic 505,1,True,0
session_007566,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007566,personalized,1,12,Keyboard Classic 505,1,True,0
session_007566,personalized,2,6,Headphones Compact 103,1,True,0
session_007566,personalized,3,13,Mouse Deluxe 406,1,True,0
session_007566,personalized,4,17,Camera Compact 359,1,True,0
session_007566,personalized,5,10,Monitor Classic 784,1,True,0
session_004514,popular,1,90,Table Lamp Eco 643,5,True,0
session_004514,popular,2,184,Nightstand Everyday 721,9,False,0
session_004514,popular,3,12,Keyboard Classic 505,1,False,0
session_004514,popular,4,49,Biography Deluxe 648,3,False,0
session_004514,popular,5,231,Studio Headphones Classic 686,11,False,0
session_004514,personalized,1,132,Puzzle Everyday 336,7,True,0
session_004514,personalized,2,90,Table Lamp Eco 643,5,True,0
session_004514,personalized,3,85,Blender Classic 334,5,True,0
session_004514,personalized,4,142,Paint Set Deluxe 295,7,True,0
session_004514,personalized,5,129,Board Game Deluxe 308,7,True,0
session_010978,popular,1,90,Table Lamp Eco 643,5,False,0
session_010978,popular,2,184,Nightstand Everyday 721,9,False,0
session_010978,popular,3,110,Shampoo Everyday 111,6,False,0
session_010978,popular,4,12,Keyboard Classic 505,1,False,0
session_010978,popular,5,49,Biography Deluxe 648,3,False,0
session_010978,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_010978,personalized,2,198,Car Charger Everyday 607,10,True,0
session_010978,personalized,3,206,Car Vacuum Deluxe 348,10,True,0
session_010978,personalized,4,193,Car Battery Deluxe 488,10,True,0
session_010978,personalized,5,196,Phone Holder Pro 656,10,True,0
session_000122,popular,1,90,Table Lamp Eco 643,5,False,0
session_000122,popular,2,184,Nightstand Everyday 721,9,False,0
session_000122,popular,3,110,Shampoo Everyday 111,6,False,0
session_000122,popular,4,12,Keyboard Classic 505,1,False,0
session_000122,popular,5,49,Biography Deluxe 648,3,False,0
session_000122,personalized,1,41,Boots Compact 911,2,True,0
session_000122,personalized,2,31,T-shirt Classic 854,2,True,0
session_000122,personalized,3,23,Jacket Essential 819,2,True,0
session_000122,personalized,4,39,Cap Everyday 356,2,True,0
session_000122,personalized,5,27,Sneakers Compact 248,2,True,0
session_006733,popular,1,90,Table Lamp Eco 643,5,False,0
session_006733,popular,2,184,Nightstand Everyday 721,9,False,0
session_006733,popular,3,110,Shampoo Everyday 111,6,False,0
session_006733,popular,4,12,Keyboard Classic 505,1,False,0
session_006733,popular,5,49,Biography Deluxe 648,3,False,0
session_006733,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_006733,personalized,2,198,Car Charger Everyday 607,10,True,0
session_006733,personalized,3,206,Car Vacuum Deluxe 348,10,True,0
session_006733,personalized,4,199,Car Charger Everyday 299,10,True,0
session_006733,personalized,5,205,Ice Scraper Deluxe 739,10,True,0
session_011688,popular,1,90,Table Lamp Eco 643,5,False,0
session_011688,popular,2,184,Nightstand Everyday 721,9,False,0
session_011688,popular,3,110,Shampoo Everyday 111,6,False,0
session_011688,popular,4,12,Keyboard Classic 505,1,False,0
session_011688,popular,5,49,Biography Deluxe 648,3,False,0
session_011688,personalized,1,37,Backpack Compact 926,2,True,0
session_011688,personalized,2,41,Boots Compact 911,2,True,0
session_011688,personalized,3,31,T-shirt Classic 854,2,True,0
session_011688,personalized,4,39,Cap Everyday 356,2,True,0
session_011688,personalized,5,23,Jacket Essential 819,2,True,0
session_002490,popular,1,90,Table Lamp Eco 643,5,False,0
session_002490,popular,2,184,Nightstand Everyday 721,9,False,0
session_002490,popular,3,110,Shampoo Everyday 111,6,False,0
session_002490,popular,4,12,Keyboard Classic 505,1,False,0
session_002490,popular,5,49,Biography Deluxe 648,3,False,0
session_002490,personalized,1,158,Pasta Eco 942,8,True,0
session_002490,personalized,2,152,Dark Chocolate Premium 512,8,True,0
session_002490,personalized,3,150,Green Tea Deluxe 321,8,True,0
session_002490,personalized,4,154,Olive Oil Everyday 426,8,True,0
session_002490,personalized,5,156,Honey Everyday 491,8,True,0
session_013075,popular,1,90,Table Lamp Eco 643,5,False,0
session_013075,popular,2,184,Nightstand Everyday 721,9,False,0
session_013075,popular,3,110,Shampoo Everyday 111,6,False,0
session_013075,popular,4,12,Keyboard Classic 505,1,False,1
session_013075,popular,5,49,Biography Deluxe 648,3,False,0
session_013075,personalized,1,243,Ladder Deluxe 713,12,True,0
session_013075,personalized,2,249,Work Gloves Compact 227,12,True,0
session_013075,personalized,3,232,Cordless Drill Classic 499,12,True,0
session_013075,personalized,4,247,Spirit Level Eco 157,12,True,0
session_013075,personalized,5,239,Tape Measure Premium 980,12,True,0
session_006257,popular,1,90,Table Lamp Eco 643,5,False,0
session_006257,popular,2,184,Nightstand Everyday 721,9,False,0
session_006257,popular,3,110,Shampoo Everyday 111,6,False,1
session_006257,popular,4,12,Keyboard Classic 505,1,False,0
session_006257,popular,5,49,Biography Deluxe 648,3,False,0
session_006257,personalized,1,234,Screwdriver Set Eco 897,12,True,0
session_006257,personalized,2,249,Work Gloves Compact 227,12,True,0
session_006257,personalized,3,247,Spirit Level Eco 157,12,True,0
session_006257,personalized,4,200,Floor Mats Everyday 949,10,True,0
session_006257,personalized,5,236,Hammer Essential 301,12,True,0
session_012744,popular,1,184,Nightstand Everyday 721,9,False,0
session_012744,popular,2,110,Shampoo Everyday 111,6,False,0
session_012744,popular,3,12,Keyboard Classic 505,1,False,0
session_012744,popular,4,49,Biography Deluxe 648,3,False,0
session_012744,popular,5,231,Studio Headphones Classic 686,11,False,0
session_012744,personalized,1,85,Blender Classic 334,5,True,0
session_012744,personalized,2,93,Towel Set Eco 365,5,True,0
session_012744,personalized,3,103,Candle Everyday 732,5,True,0
session_012744,personalized,4,87,Coffee Maker Pro 639,5,True,0
session_012744,personalized,5,86,Blender Everyday 283,5,True,0
session_010136,popular,1,184,Nightstand Everyday 721,9,False,0
session_010136,popular,2,110,Shampoo Everyday 111,6,False,0
session_010136,popular,3,12,Keyboard Classic 505,1,False,0
session_010136,popular,4,49,Biography Deluxe 648,3,False,0
session_010136,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010136,personalized,1,93,Towel Set Eco 365,5,True,0
session_010136,personalized,2,103,Candle Everyday 732,5,True,0
session_010136,personalized,3,87,Coffee Maker Pro 639,5,True,0
session_010136,personalized,4,86,Blender Everyday 283,5,True,0
session_010136,personalized,5,94,Towel Set Pro 801,5,True,0
session_014747,popular,1,90,Table Lamp Eco 643,5,False,0
session_014747,popular,2,184,Nightstand Everyday 721,9,False,0
session_014747,popular,3,110,Shampoo Everyday 111,6,False,0
session_014747,popular,4,12,Keyboard Classic 505,1,False,0
session_014747,popular,5,49,Biography Deluxe 648,3,True,0
session_014747,personalized,1,49,Biography Deluxe 648,3,True,1
session_014747,personalized,2,52,Fantasy Pro 681,3,True,0
session_014747,personalized,3,127,Building Blocks Premium 126,7,True,0
session_014747,personalized,4,60,Poetry Everyday 604,3,True,0
session_014747,personalized,5,133,Doll Eco 977,7,True,0
session_006410,popular,1,184,Nightstand Everyday 721,9,False,0
session_006410,popular,2,110,Shampoo Everyday 111,6,False,0
session_006410,popular,3,12,Keyboard Classic 505,1,False,0
session_006410,popular,4,49,Biography Deluxe 648,3,False,0
session_006410,popular,5,231,Studio Headphones Classic 686,11,False,0
session_006410,personalized,1,85,Blender Classic 334,5,True,0
session_006410,personalized,2,93,Towel Set Eco 365,5,True,0
session_006410,personalized,3,105,Bedding Set Everyday 147,5,True,0
session_006410,personalized,4,87,Coffee Maker Pro 639,5,True,0
session_006410,personalized,5,86,Blender Everyday 283,5,True,0
session_010192,popular,1,90,Table Lamp Eco 643,5,False,0
session_010192,popular,2,184,Nightstand Everyday 721,9,False,0
session_010192,popular,3,110,Shampoo Everyday 111,6,False,0
session_010192,popular,4,49,Biography Deluxe 648,3,False,0
session_010192,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010192,personalized,1,6,Headphones Compact 103,1,True,0
session_010192,personalized,2,17,Camera Compact 359,1,True,0
session_010192,personalized,3,13,Mouse Deluxe 406,1,True,0
session_010192,personalized,4,10,Monitor Classic 784,1,True,0
session_010192,personalized,5,7,Tablet Compact 853,1,True,0
session_007197,popular,1,90,Table Lamp Eco 643,5,False,0
session_007197,popular,2,184,Nightstand Everyday 721,9,False,0
session_007197,popular,3,110,Shampoo Everyday 111,6,False,0
session_007197,popular,4,49,Biography Deluxe 648,3,False,0
session_007197,popular,5,76,Tennis Racket Compact 416,4,False,0
session_007197,personalized,1,2,Smartphone Compact 854,1,True,1
session_007197,personalized,2,13,Mouse Deluxe 406,1,True,0
session_007197,personalized,3,17,Camera Compact 359,1,True,0
session_007197,personalized,4,10,Monitor Classic 784,1,True,0
session_007197,personalized,5,14,Mouse Eco 475,1,True,0
session_008414,popular,1,90,Table Lamp Eco 643,5,True,0
session_008414,popular,2,184,Nightstand Everyday 721,9,False,0
session_008414,popular,3,110,Shampoo Everyday 111,6,True,0
session_008414,popular,4,12,Keyboard Classic 505,1,False,0
session_008414,popular,5,231,Studio Headphones Classic 686,11,False,0
session_008414,personalized,1,90,Table Lamp Eco 643,5,True,0
session_008414,personalized,2,93,Towel Set Eco 365,5,True,0
session_008414,personalized,3,103,Candle Everyday 732,5,True,0
session_008414,personalized,4,87,Coffee Maker Pro 639,5,True,0
session_008414,personalized,5,110,Shampoo Everyday 111,6,True,0
session_007977,popular,1,90,Table Lamp Eco 643,5,False,0
session_007977,popular,2,184,Nightstand Everyday 721,9,False,0
session_007977,popular,3,12,Keyboard Classic 505,1,False,0
session_007977,popular,4,49,Biography Deluxe 648,3,False,0
session_007977,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007977,personalized,1,123,Makeup Brush Set Pro 675,6,True,0
session_007977,personalized,2,121,Sunscreen Classic 799,6,True,0
session_007977,personalized,3,109,Serum Everyday 923,6,True,0
session_007977,personalized,4,114,Lipstick Compact 868,6,True,0
session_007977,personalized,5,115,Lipstick Eco 829,6,True,0
session_010557,popular,1,90,Table Lamp Eco 643,5,False,0
session_010557,popular,2,184,Nightstand Everyday 721,9,False,0
session_010557,popular,3,110,Shampoo Everyday 111,6,False,0
session_010557,popular,4,12,Keyboard Classic 505,1,False,0
session_010557,popular,5,49,Biography Deluxe 648,3,False,0
session_010557,personalized,1,198,Car Charger Everyday 607,10,True,0
session_010557,personalized,2,206,Car Vacuum Deluxe 348,10,True,0
session_010557,personalized,3,193,Car Battery Deluxe 488,10,True,0
session_010557,personalized,4,205,Ice Scraper Deluxe 739,10,True,0
session_010557,personalized,5,208,Jump Starter Essential 942,10,True,0
session_013070,popular,1,90,Table Lamp Eco 643,5,False,0
session_013070,popular,2,184,Nightstand Everyday 721,9,False,0
session_013070,popular,3,110,Shampoo Everyday 111,6,False,0
session_013070,popular,4,12,Keyboard Classic 505,1,False,0
session_013070,popular,5,49,Biography Deluxe 648,3,True,0
session_013070,personalized,1,132,Puzzle Everyday 336,7,True,0
session_013070,personalized,2,140,Robot Kit Essential 218,7,True,0
session_013070,personalized,3,142,Paint Set Deluxe 295,7,True,0
session_013070,personalized,4,129,Board Game Deluxe 308,7,True,0
session_013070,personalized,5,135,RC Car Deluxe 276,7,True,0
session_002362,popular,1,90,Table Lamp Eco 643,5,True,0
session_002362,popular,2,184,Nightstand Everyday 721,9,True,0
session_002362,popular,3,110,Shampoo Everyday 111,6,False,0
session_002362,popular,4,12,Keyboard Classic 505,1,False,0
session_002362,popular,5,49,Biography Deluxe 648,3,False,0
session_002362,personalized,1,90,Table Lamp Eco 643,5,True,0
session_002362,personalized,2,184,Nightstand Everyday 721,9,True,0
session_002362,personalized,3,103,Candle Everyday 732,5,True,0
session_002362,personalized,4,105,Bedding Set Everyday 147,5,True,0
session_002362,personalized,5,177,Bed Frame Eco 577,9,True,0
session_014034,popular,1,90,Table Lamp Eco 643,5,False,0
session_014034,popular,2,184,Nightstand Everyday 721,9,False,0
session_014034,popular,3,110,Shampoo Everyday 111,6,False,0
session_014034,popular,4,12,Keyboard Classic 505,1,False,0
session_014034,popular,5,49,Biography Deluxe 648,3,False,0
session_014034,personalized,1,158,Pasta Eco 942,8,True,0
session_014034,personalized,2,152,Dark Chocolate Premium 512,8,True,0
session_014034,personalized,3,76,Tennis Racket Compact 416,4,True,0
session_014034,personalized,4,154,Olive Oil Everyday 426,8,True,0
session_014034,personalized,5,156,Honey Everyday 491,8,True,0
session_005547,popular,1,90,Table Lamp Eco 643,5,False,0
session_005547,popular,2,184,Nightstand Everyday 721,9,False,0
session_005547,popular,3,12,Keyboard Classic 505,1,False,0
session_005547,popular,4,49,Biography Deluxe 648,3,False,0
session_005547,popular,5,231,Studio Headphones Classic 686,11,False,0
session_005547,personalized,1,118,Body Lotion Deluxe 734,6,True,0
session_005547,personalized,2,123,Makeup Brush Set Pro 675,6,True,0
session_005547,personalized,3,108,Serum Essential 226,6,True,0
session_005547,personalized,4,107,Face Cream Everyday 865,6,True,0
session_005547,personalized,5,114,Lipstick Compact 868,6,True,0
session_010200,popular,1,90,Table Lamp Eco 643,5,False,0
session_010200,popular,2,184,Nightstand Everyday 721,9,False,0
session_010200,popular,3,110,Shampoo Everyday 111,6,False,0
session_010200,popular,4,12,Keyboard Classic 505,1,False,0
session_010200,popular,5,231,Studio Headphones Classic 686,11,True,0
session_010200,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_010200,personalized,2,200,Floor Mats Everyday 949,10,True,0
session_010200,personalized,3,52,Fantasy Pro 681,3,False,0
session_010200,personalized,4,224,Ukulele Essential 759,11,True,0
session_010200,personalized,5,60,Poetry Everyday 604,3,False,0
session_006832,popular,1,90,Table Lamp Eco 643,5,False,0
session_006832,popular,2,184,Nightstand Everyday 721,9,False,0
session_006832,popular,3,110,Shampoo Everyday 111,6,False,0
session_006832,popular,4,12,Keyboard Classic 505,1,False,0
session_006832,popular,5,49,Biography Deluxe 648,3,False,0
session_006832,personalized,1,127,Building Blocks Premium 126,7,True,0
session_006832,personalized,2,133,Doll Eco 977,7,True,0
session_006832,personalized,3,137,Plush Toy Classic 439,7,True,0
session_006832,personalized,4,145,Card Game Essential 324,7,True,0
session_006832,personalized,5,141,Paint Set Classic 369,7,True,0
session_009906,popular,1,90,Table Lamp Eco 643,5,False,0
session_009906,popular,2,184,Nightstand Everyday 721,9,False,0
session_009906,popular,3,110,Shampoo Everyday 111,6,False,0
session_009906,popular,4,12,Keyboard Classic 505,1,False,0
session_009906,popular,5,49,Biography Deluxe 648,3,False,0
session_009906,personalized,1,76,Tennis Racket Compact 416,4,True,1
session_009906,personalized,2,74,Football Deluxe 883,4,True,0
session_009906,personalized,3,160,Granola Premium 789,8,True,0
session_009906,personalized,4,68,Dumbbell Set Premium 193,4,True,0
session_009906,personalized,5,67,Yoga Mat Everyday 759,4,True,0
session_004218,popular,1,90,Table Lamp Eco 643,5,False,0
session_004218,popular,2,184,Nightstand Everyday 721,9,False,0
session_004218,popular,3,110,Shampoo Everyday 111,6,False,0
session_004218,popular,4,12,Keyboard Classic 505,1,False,0
session_004218,popular,5,49,Biography Deluxe 648,3,False,0
session_004218,personalized,1,206,Car Vacuum Deluxe 348,10,True,0
session_004218,personalized,2,208,Jump Starter Essential 942,10,True,0
session_004218,personalized,3,205,Ice Scraper Deluxe 739,10,True,0
session_004218,personalized,4,199,Car Charger Everyday 299,10,True,0
session_004218,personalized,5,196,Phone Holder Pro 656,10,True,0
session_003476,popular,1,90,Table Lamp Eco 643,5,False,0
session_003476,popular,2,110,Shampoo Everyday 111,6,False,0
session_003476,popular,3,12,Keyboard Classic 505,1,False,0
session_003476,popular,4,49,Biography Deluxe 648,3,False,0
session_003476,popular,5,231,Studio Headphones Classic 686,11,False,0
session_003476,personalized,1,249,Work Gloves Compact 227,12,True,0
session_003476,personalized,2,247,Spirit Level Eco 157,12,True,0
session_003476,personalized,3,235,Screwdriver Set Pro 103,12,True,0
session_003476,personalized,4,238,Tape Measure Pro 133,12,True,0
session_003476,personalized,5,252,Spirit Level Classic 425,12,True,0
session_014324,popular,1,90,Table Lamp Eco 643,5,False,0
session_014324,popular,2,184,Nightstand Everyday 721,9,False,0
session_014324,popular,3,12,Keyboard Classic 505,1,False,0
session_014324,popular,4,49,Biography Deluxe 648,3,False,0
session_014324,popular,5,127,Building Blocks Premium 126,7,False,0
session_014324,personalized,1,198,Car Charger Everyday 607,10,True,0
session_014324,personalized,2,208,Jump Starter Essential 942,10,True,0
session_014324,personalized,3,199,Car Charger Everyday 299,10,True,0
session_014324,personalized,4,210,Dash Cam Premium 877,10,True,0
session_014324,personalized,5,80,Fitness Band Eco 108,4,True,0
session_006776,popular,1,90,Table Lamp Eco 643,5,True,0
session_006776,popular,2,184,Nightstand Everyday 721,9,False,0
session_006776,popular,3,110,Shampoo Everyday 111,6,False,0
session_006776,popular,4,12,Keyboard Classic 505,1,False,0
session_006776,popular,5,49,Biography Deluxe 648,3,False,0
session_006776,personalized,1,80,Fitness Band Eco 108,4,True,0
session_006776,personalized,2,74,Football Deluxe 883,4,True,0
session_006776,personalized,3,75,Football Premium 903,4,True,0
session_006776,personalized,4,65,Running Shoes Deluxe 803,4,True,0
session_006776,personalized,5,66,Yoga Mat Premium 817,4,True,0
session_010380,popular,1,184,Nightstand Everyday 721,9,False,0
session_010380,popular,2,110,Shampoo Everyday 111,6,False,0
session_010380,popular,3,12,Keyboard Classic 505,1,False,0
session_010380,popular,4,49,Biography Deluxe 648,3,False,0
session_010380,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010380,personalized,1,85,Blender Classic 334,5,True,0
session_010380,personalized,2,105,Bedding Set Everyday 147,5,True,0
session_010380,personalized,3,87,Coffee Maker Pro 639,5,True,0
session_010380,personalized,4,94,Towel Set Pro 801,5,True,0
session_010380,personalized,5,86,Blender Everyday 283,5,True,0
session_000353,popular,1,90,Table Lamp Eco 643,5,False,0
session_000353,popular,2,184,Nightstand Everyday 721,9,False,0
session_000353,popular,3,110,Shampoo Everyday 111,6,False,0
session_000353,popular,4,12,Keyboard Classic 505,1,False,0
session_000353,popular,5,49,Biography Deluxe 648,3,True,0
session_000353,personalized,1,49,Biography Deluxe 648,3,True,0
session_000353,personalized,2,52,Fantasy Pro 681,3,True,0
session_000353,personalized,3,60,Poetry Everyday 604,3,True,0
session_000353,personalized,4,63,Cookbook Compact 232,3,True,0
session_000353,personalized,5,59,Poetry Classic 204,3,True,0
session_012152,popular,1,90,Table Lamp Eco 643,5,False,0
session_012152,popular,2,184,Nightstand Everyday 721,9,False,0
session_012152,popular,3,110,Shampoo Everyday 111,6,False,0
session_012152,popular,4,12,Keyboard Classic 505,1,False,0
session_012152,popular,5,49,Biography Deluxe 648,3,False,0
session_012152,personalized,1,167,Juice Everyday 509,8,True,0
session_012152,personalized,2,158,Pasta Eco 942,8,True,0
session_012152,personalized,3,152,Dark Chocolate Premium 512,8,True,0
session_012152,personalized,4,150,Green Tea Deluxe 321,8,True,0
session_012152,personalized,5,156,Honey Everyday 491,8,True,0
session_004933,popular,1,90,Table Lamp Eco 643,5,True,0
session_004933,popular,2,184,Nightstand Everyday 721,9,False,0
session_004933,popular,3,110,Shampoo Everyday 111,6,False,0
session_004933,popular,4,12,Keyboard Classic 505,1,False,0
session_004933,popular,5,49,Biography Deluxe 648,3,False,0
session_004933,personalized,1,160,Granola Premium 789,8,True,0
session_004933,personalized,2,167,Juice Everyday 509,8,True,0
session_004933,personalized,3,158,Pasta Eco 942,8,True,1
session_004933,personalized,4,150,Green Tea Deluxe 321,8,True,0
session_004933,personalized,5,152,Dark Chocolate Premium 512,8,True,0
session_011500,popular,1,90,Table Lamp Eco 643,5,False,0
session_011500,popular,2,184,Nightstand Everyday 721,9,False,0
session_011500,popular,3,110,Shampoo Everyday 111,6,False,0
session_011500,popular,4,12,Keyboard Classic 505,1,False,0
session_011500,popular,5,49,Biography Deluxe 648,3,False,0
session_011500,personalized,1,158,Pasta Eco 942,8,True,0
session_011500,personalized,2,152,Dark Chocolate Premium 512,8,True,0
session_011500,personalized,3,150,Green Tea Deluxe 321,8,True,0
session_011500,personalized,4,154,Olive Oil Everyday 426,8,True,0
session_011500,personalized,5,156,Honey Everyday 491,8,True,0
session_014061,popular,1,90,Table Lamp Eco 643,5,False,0
session_014061,popular,2,184,Nightstand Everyday 721,9,False,0
session_014061,popular,3,110,Shampoo Everyday 111,6,False,0
session_014061,popular,4,12,Keyboard Classic 505,1,False,0
session_014061,popular,5,49,Biography Deluxe 648,3,False,0
session_014061,personalized,1,160,Granola Premium 789,8,True,0
session_014061,personalized,2,167,Juice Everyday 509,8,True,0
session_014061,personalized,3,158,Pasta Eco 942,8,True,0
session_014061,personalized,4,152,Dark Chocolate Premium 512,8,True,0
session_014061,personalized,5,154,Olive Oil Everyday 426,8,True,0
session_011906,popular,1,184,Nightstand Everyday 721,9,False,0
session_011906,popular,2,110,Shampoo Everyday 111,6,False,0
session_011906,popular,3,49,Biography Deluxe 648,3,False,0
session_011906,popular,4,231,Studio Headphones Classic 686,11,False,0
session_011906,popular,5,76,Tennis Racket Compact 416,4,False,0
session_011906,personalized,1,2,Smartphone Compact 854,1,True,0
session_011906,personalized,2,9,Monitor Premium 997,1,True,0
session_011906,personalized,3,85,Blender Classic 334,5,True,0
session_011906,personalized,4,93,Towel Set Eco 365,5,True,0
session_011906,personalized,5,6,Headphones Compact 103,1,True,0
session_002462,popular,1,90,Table Lamp Eco 643,5,False,0
session_002462,popular,2,184,Nightstand Everyday 721,9,False,0
session_002462,popular,3,12,Keyboard Classic 505,1,False,0
session_002462,popular,4,49,Biography Deluxe 648,3,False,0
session_002462,popular,5,231,Studio Headphones Classic 686,11,False,0
session_002462,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_002462,personalized,2,123,Makeup Brush Set Pro 675,6,True,0
session_002462,personalized,3,30,T-shirt Everyday 987,2,True,0
session_002462,personalized,4,121,Sunscreen Classic 799,6,True,0
session_002462,personalized,5,37,Backpack Compact 926,2,True,0
session_011843,popular,1,90,Table Lamp Eco 643,5,False,0
session_011843,popular,2,184,Nightstand Everyday 721,9,False,0
session_011843,popular,3,110,Shampoo Everyday 111,6,False,0
session_011843,popular,4,12,Keyboard Classic 505,1,False,0
session_011843,popular,5,49,Biography Deluxe 648,3,False,0
session_011843,personalized,1,80,Fitness Band Eco 108,4,True,0
session_011843,personalized,2,41,Boots Compact 911,2,True,1
session_011843,personalized,3,30,T-shirt Everyday 987,2,True,0
session_011843,personalized,4,37,Backpack Compact 926,2,True,0
session_011843,personalized,5,68,Dumbbell Set Premium 193,4,True,0
session_008530,popular,1,90,Table Lamp Eco 643,5,False,0
session_008530,popular,2,184,Nightstand Everyday 721,9,False,0
session_008530,popular,3,110,Shampoo Everyday 111,6,False,0
session_008530,popular,4,12,Keyboard Classic 505,1,False,0
session_008530,popular,5,231,Studio Headphones Classic 686,11,False,0
session_008530,personalized,1,52,Fantasy Pro 681,3,True,0
session_008530,personalized,2,63,Cookbook Compact 232,3,True,0
session_008530,personalized,3,44,Novel Premium 964,3,True,0
session_008530,personalized,4,50,Biography Essential 819,3,True,0
session_008530,personalized,5,43,Novel Premium 556,3,True,0
session_010399,popular,1,90,Table Lamp Eco 643,5,True,0
session_010399,popular,2,184,Nightstand Everyday 721,9,False,0
session_010399,popular,3,12,Keyboard Classic 505,1,False,0
session_010399,popular,4,49,Biography Deluxe 648,3,False,0
session_010399,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010399,personalized,1,118,Body Lotion Deluxe 734,6,True,0
session_010399,personalized,2,121,Sunscreen Classic 799,6,True,0
session_010399,personalized,3,108,Serum Essential 226,6,True,0
session_010399,personalized,4,107,Face Cream Everyday 865,6,True,0
session_010399,personalized,5,114,Lipstick Compact 868,6,True,0
session_007586,popular,1,90,Table Lamp Eco 643,5,False,0
session_007586,popular,2,184,Nightstand Everyday 721,9,False,0
session_007586,popular,3,110,Shampoo Everyday 111,6,False,0
session_007586,popular,4,12,Keyboard Classic 505,1,False,0
session_007586,popular,5,49,Biography Deluxe 648,3,False,0
session_007586,personalized,1,232,Cordless Drill Classic 499,12,True,0
session_007586,personalized,2,249,Work Gloves Compact 227,12,True,0
session_007586,personalized,3,234,Screwdriver Set Eco 897,12,True,0
session_007586,personalized,4,247,Spirit Level Eco 157,12,True,0
session_007586,personalized,5,236,Hammer Essential 301,12,True,0
session_003674,popular,1,90,Table Lamp Eco 643,5,False,0
session_003674,popular,2,184,Nightstand Everyday 721,9,False,0
session_003674,popular,3,110,Shampoo Everyday 111,6,False,0
session_003674,popular,4,12,Keyboard Classic 505,1,False,0
session_003674,popular,5,49,Biography Deluxe 648,3,False,0
session_003674,personalized,1,41,Boots Compact 911,2,True,0
session_003674,personalized,2,31,T-shirt Classic 854,2,True,0
session_003674,personalized,3,39,Cap Everyday 356,2,True,0
session_003674,personalized,4,32,Scarf Eco 733,2,True,0
session_003674,personalized,5,27,Sneakers Compact 248,2,True,0
session_010290,popular,1,90,Table Lamp Eco 643,5,False,0
session_010290,popular,2,184,Nightstand Everyday 721,9,False,0
session_010290,popular,3,110,Shampoo Everyday 111,6,False,0
session_010290,popular,4,12,Keyboard Classic 505,1,False,0
session_010290,popular,5,49,Biography Deluxe 648,3,True,0
session_010290,personalized,1,49,Biography Deluxe 648,3,True,0
session_010290,personalized,2,52,Fantasy Pro 681,3,True,0
session_010290,personalized,3,50,Biography Essential 819,3,True,0
session_010290,personalized,4,43,Novel Premium 556,3,True,0
session_010290,personalized,5,45,Thriller Compact 230,3,True,0
session_012491,popular,1,90,Table Lamp Eco 643,5,False,0
session_012491,popular,2,184,Nightstand Everyday 721,9,False,0
session_012491,popular,3,12,Keyboard Classic 505,1,False,0
session_012491,popular,4,49,Biography Deluxe 648,3,False,0
session_012491,popular,5,231,Studio Headphones Classic 686,11,False,0
session_012491,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_012491,personalized,2,118,Body Lotion Deluxe 734,6,True,0
session_012491,personalized,3,121,Sunscreen Classic 799,6,True,0
session_012491,personalized,4,108,Serum Essential 226,6,True,0
session_012491,personalized,5,107,Face Cream Everyday 865,6,True,0
session_014785,popular,1,90,Table Lamp Eco 643,5,False,0
session_014785,popular,2,184,Nightstand Everyday 721,9,True,0
session_014785,popular,3,110,Shampoo Everyday 111,6,False,0
session_014785,popular,4,12,Keyboard Classic 505,1,False,0
session_014785,popular,5,49,Biography Deluxe 648,3,False,0
session_014785,personalized,1,184,Nightstand Everyday 721,9,True,0
session_014785,personalized,2,200,Floor Mats Everyday 949,10,False,0
session_014785,personalized,3,249,Work Gloves Compact 227,12,True,0
session_014785,personalized,4,234,Screwdriver Set Eco 897,12,True,0
session_014785,personalized,5,181,Coffee Table Eco 857,9,True,0
session_006115,popular,1,90,Table Lamp Eco 643,5,False,0
session_006115,popular,2,184,Nightstand Everyday 721,9,False,0
session_006115,popular,3,110,Shampoo Everyday 111,6,False,0
session_006115,popular,4,12,Keyboard Classic 505,1,False,0
session_006115,popular,5,49,Biography Deluxe 648,3,True,0
session_006115,personalized,1,224,Ukulele Essential 759,11,True,0
session_006115,personalized,2,230,Effects Pedal Eco 176,11,True,0
session_006115,personalized,3,49,Biography Deluxe 648,3,True,0
session_006115,personalized,4,229,Effects Pedal Essential 260,11,True,0
session_006115,personalized,5,225,Drum Sticks Pro 333,11,True,0
session_001324,popular,1,90,Table Lamp Eco 643,5,True,0
session_001324,popular,2,184,Nightstand Everyday 721,9,False,0
session_001324,popular,3,12,Keyboard Classic 505,1,False,0
session_001324,popular,4,49,Biography Deluxe 648,3,False,0
session_001324,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001324,personalized,1,90,Table Lamp Eco 643,5,True,0
session_001324,personalized,2,85,Blender Classic 334,5,True,0
session_001324,personalized,3,93,Towel Set Eco 365,5,True,0
session_001324,personalized,4,125,Beard Trimmer Premium 354,6,True,0
session_001324,personalized,5,118,Body Lotion Deluxe 734,6,True,0
session_001772,popular,1,184,Nightstand Everyday 721,9,False,0
session_001772,popular,2,110,Shampoo Everyday 111,6,False,0
session_001772,popular,3,12,Keyboard Classic 505,1,False,0
session_001772,popular,4,49,Biography Deluxe 648,3,False,0
session_001772,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001772,personalized,1,103,Candle Everyday 732,5,True,0
session_001772,personalized,2,232,Cordless Drill Classic 499,12,True,0
session_001772,personalized,3,87,Coffee Maker Pro 639,5,True,0
session_001772,personalized,4,86,Blender Everyday 283,5,True,0
session_001772,personalized,5,94,Towel Set Pro 801,5,True,0
session_014726,popular,1,90,Table Lamp Eco 643,5,False,0
session_014726,popular,2,184,Nightstand Everyday 721,9,False,0
session_014726,popular,3,110,Shampoo Everyday 111,6,False,0
session_014726,popular,4,12,Keyboard Classic 505,1,False,0
session_014726,popular,5,231,Studio Headphones Classic 686,11,False,0
session_014726,personalized,1,60,Poetry Everyday 604,3,True,1
session_014726,personalized,2,63,Cookbook Compact 232,3,True,0
session_014726,personalized,3,44,Novel Premium 964,3,True,0
session_014726,personalized,4,50,Biography Essential 819,3,True,0
session_014726,personalized,5,43,Novel Premium 556,3,True,0
session_000582,popular,1,110,Shampoo Everyday 111,6,False,0
session_000582,popular,2,12,Keyboard Classic 505,1,False,0
session_000582,popular,3,49,Biography Deluxe 648,3,False,0
session_000582,popular,4,231,Studio Headphones Classic 686,11,False,0
session_000582,popular,5,76,Tennis Racket Compact 416,4,False,0
session_000582,personalized,1,177,Bed Frame Eco 577,9,True,0
session_000582,personalized,2,193,Car Battery Deluxe 488,10,True,0
session_000582,personalized,3,181,Coffee Table Eco 857,9,True,0
session_000582,personalized,4,205,Ice Scraper Deluxe 739,10,True,0
session_000582,personalized,5,208,Jump Starter Essential 942,10,True,0
session_011522,popular,1,90,Table Lamp Eco 643,5,False,0
session_011522,popular,2,184,Nightstand Everyday 721,9,False,0
session_011522,popular,3,110,Shampoo Everyday 111,6,False,0
session_011522,popular,4,12,Keyboard Classic 505,1,False,0
session_011522,popular,5,49,Biography Deluxe 648,3,False,0
session_011522,personalized,1,249,Work Gloves Compact 227,12,True,0
session_011522,personalized,2,232,Cordless Drill Classic 499,12,True,0
session_011522,personalized,3,247,Spirit Level Eco 157,12,True,0
session_011522,personalized,4,239,Tape Measure Premium 980,12,True,0
session_011522,personalized,5,236,Hammer Essential 301,12,True,0
session_001834,popular,1,184,Nightstand Everyday 721,9,False,0
session_001834,popular,2,110,Shampoo Everyday 111,6,True,0
session_001834,popular,3,12,Keyboard Classic 505,1,False,0
session_001834,popular,4,49,Biography Deluxe 648,3,False,0
session_001834,popular,5,231,Studio Headphones Classic 686,11,False,0
session_001834,personalized,1,85,Blender Classic 334,5,True,0
session_001834,personalized,2,103,Candle Everyday 732,5,True,0
session_001834,personalized,3,87,Coffee Maker Pro 639,5,True,0
session_001834,personalized,4,89,Table Lamp Deluxe 218,5,True,0
session_001834,personalized,5,86,Blender Everyday 283,5,True,0
session_012283,popular,1,90,Table Lamp Eco 643,5,False,0
session_012283,popular,2,184,Nightstand Everyday 721,9,False,0
session_012283,popular,3,110,Shampoo Everyday 111,6,False,0
session_012283,popular,4,12,Keyboard Classic 505,1,False,0
session_012283,popular,5,49,Biography Deluxe 648,3,False,0
session_012283,personalized,1,148,Coffee Beans Pro 813,8,True,0
session_012283,personalized,2,160,Granola Premium 789,8,True,0
session_012283,personalized,3,158,Pasta Eco 942,8,True,0
session_012283,personalized,4,167,Juice Everyday 509,8,True,0
session_012283,personalized,5,152,Dark Chocolate Premium 512,8,True,0
session_015343,popular,1,184,Nightstand Everyday 721,9,False,0
session_015343,popular,2,110,Shampoo Everyday 111,6,False,0
session_015343,popular,3,12,Keyboard Classic 505,1,False,0
session_015343,popular,4,49,Biography Deluxe 648,3,False,0
session_015343,popular,5,231,Studio Headphones Classic 686,11,False,0
session_015343,personalized,1,85,Blender Classic 334,5,True,0
session_015343,personalized,2,243,Ladder Deluxe 713,12,True,0
session_015343,personalized,3,93,Towel Set Eco 365,5,True,0
session_015343,personalized,4,103,Candle Everyday 732,5,True,0
session_015343,personalized,5,105,Bedding Set Everyday 147,5,True,0
session_012844,popular,1,90,Table Lamp Eco 643,5,False,0
session_012844,popular,2,184,Nightstand Everyday 721,9,True,0
session_012844,popular,3,110,Shampoo Everyday 111,6,False,0
session_012844,popular,4,12,Keyboard Classic 505,1,False,0
session_012844,popular,5,49,Biography Deluxe 648,3,False,0
session_012844,personalized,1,184,Nightstand Everyday 721,9,True,0
session_012844,personalized,2,181,Coffee Table Eco 857,9,True,0
session_012844,personalized,3,175,Bookshelf Eco 371,9,True,0
session_012844,personalized,4,169,Sofa Essential 990,9,True,0
session_012844,personalized,5,171,Office Chair Deluxe 707,9,True,0
session_007686,popular,1,110,Shampoo Everyday 111,6,False,0
session_007686,popular,2,12,Keyboard Classic 505,1,False,0
session_007686,popular,3,49,Biography Deluxe 648,3,False,0
session_007686,popular,4,231,Studio Headphones Classic 686,11,False,0
session_007686,popular,5,76,Tennis Racket Compact 416,4,False,0
session_007686,personalized,1,185,Dining Chair Classic 954,9,True,0
session_007686,personalized,2,182,Coffee Table Pro 626,9,True,0
session_007686,personalized,3,105,Bedding Set Everyday 147,5,True,0
session_007686,personalized,4,103,Candle Everyday 732,5,True,0
session_007686,personalized,5,169,Sofa Essential 990,9,True,0
session_011821,popular,1,90,Table Lamp Eco 643,5,False,0
session_011821,popular,2,184,Nightstand Everyday 721,9,False,0
session_011821,popular,3,110,Shampoo Everyday 111,6,False,0
session_011821,popular,4,231,Studio Headphones Classic 686,11,False,0
session_011821,popular,5,76,Tennis Racket Compact 416,4,False,0
session_011821,personalized,1,37,Backpack Compact 926,2,True,0
session_011821,personalized,2,41,Boots Compact 911,2,True,0
session_011821,personalized,3,31,T-shirt Classic 854,2,True,0
session_011821,personalized,4,32,Scarf Eco 733,2,True,0
session_011821,personalized,5,36,Backpack Classic 759,2,True,0
session_007605,popular,1,90,Table Lamp Eco 643,5,False,0
session_007605,popular,2,184,Nightstand Everyday 721,9,False,0
session_007605,popular,3,110,Shampoo Everyday 111,6,False,0
session_007605,popular,4,12,Keyboard Classic 505,1,False,0
session_007605,popular,5,231,Studio Headphones Classic 686,11,False,0
session_007605,personalized,1,127,Building Blocks Premium 126,7,True,0
session_007605,personalized,2,133,Doll Eco 977,7,True,0
session_007605,personalized,3,52,Fantasy Pro 681,3,True,0
session_007605,personalized,4,137,Plush Toy Classic 439,7,True,0
session_007605,personalized,5,60,Poetry Everyday 604,3,True,0
session_012106,popular,1,90,Table Lamp Eco 643,5,False,0
session_012106,popular,2,184,Nightstand Everyday 721,9,False,0
session_012106,popular,3,110,Shampoo Everyday 111,6,False,0
session_012106,popular,4,12,Keyboard Classic 505,1,False,0
session_012106,popular,5,49,Biography Deluxe 648,3,False,0
session_012106,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_012106,personalized,2,49,Biography Deluxe 648,3,False,0
session_012106,personalized,3,223,Ukulele Premium 117,11,True,0
session_012106,personalized,4,137,Plush Toy Classic 439,7,True,0
session_012106,personalized,5,52,Fantasy Pro 681,3,False,0
session_007196,popular,1,90,Table Lamp Eco 643,5,True,0
session_007196,popular,2,184,Nightstand Everyday 721,9,True,0
session_007196,popular,3,110,Shampoo Everyday 111,6,False,0
session_007196,popular,4,12,Keyboard Classic 505,1,False,0
session_007196,popular,5,49,Biography Deluxe 648,3,False,0
session_007196,personalized,1,90,Table Lamp Eco 643,5,True,0
session_007196,personalized,2,85,Blender Classic 334,5,True,1
session_007196,personalized,3,103,Candle Everyday 732,5,True,0
session_007196,personalized,4,105,Bedding Set Everyday 147,5,True,0
session_007196,personalized,5,184,Nightstand Everyday 721,9,True,0
session_003767,popular,1,90,Table Lamp Eco 643,5,False,0
session_003767,popular,2,184,Nightstand Everyday 721,9,False,0
session_003767,popular,3,110,Shampoo Everyday 111,6,False,0
session_003767,popular,4,12,Keyboard Classic 505,1,False,0
session_003767,popular,5,49,Biography Deluxe 648,3,True,0
session_003767,personalized,1,49,Biography Deluxe 648,3,True,0
session_003767,personalized,2,60,Poetry Everyday 604,3,True,0
session_003767,personalized,3,44,Novel Premium 964,3,True,0
session_003767,personalized,4,50,Biography Essential 819,3,True,0
session_003767,personalized,5,43,Novel Premium 556,3,True,0
session_013821,popular,1,184,Nightstand Everyday 721,9,True,0
session_013821,popular,2,110,Shampoo Everyday 111,6,False,0
session_013821,popular,3,12,Keyboard Classic 505,1,False,0
session_013821,popular,4,49,Biography Deluxe 648,3,False,0
session_013821,popular,5,231,Studio Headphones Classic 686,11,False,0
session_013821,personalized,1,184,Nightstand Everyday 721,9,True,0
session_013821,personalized,2,85,Blender Classic 334,5,True,0
session_013821,personalized,3,93,Towel Set Eco 365,5,True,0
session_013821,personalized,4,105,Bedding Set Everyday 147,5,True,0
session_013821,personalized,5,103,Candle Everyday 732,5,True,0
session_001230,popular,1,90,Table Lamp Eco 643,5,False,0
session_001230,popular,2,184,Nightstand Everyday 721,9,False,0
session_001230,popular,3,110,Shampoo Everyday 111,6,False,0
session_001230,popular,4,12,Keyboard Classic 505,1,False,0
session_001230,popular,5,49,Biography Deluxe 648,3,False,0
session_001230,personalized,1,160,Granola Premium 789,8,True,0
session_001230,personalized,2,68,Dumbbell Set Premium 193,4,True,0
session_001230,personalized,3,167,Juice Everyday 509,8,True,0
session_001230,personalized,4,158,Pasta Eco 942,8,True,0
session_001230,personalized,5,73,Tent Classic 332,4,True,0
session_006651,popular,1,90,Table Lamp Eco 643,5,False,0
session_006651,popular,2,184,Nightstand Everyday 721,9,False,0
session_006651,popular,3,110,Shampoo Everyday 111,6,True,0
session_006651,popular,4,12,Keyboard Classic 505,1,False,0
session_006651,popular,5,49,Biography Deluxe 648,3,False,0
session_006651,personalized,1,232,Cordless Drill Classic 499,12,True,0
session_006651,personalized,2,249,Work Gloves Compact 227,12,True,0
session_006651,personalized,3,234,Screwdriver Set Eco 897,12,True,0
session_006651,personalized,4,247,Spirit Level Eco 157,12,True,0
session_006651,personalized,5,236,Hammer Essential 301,12,True,0
session_015195,popular,1,90,Table Lamp Eco 643,5,False,0
session_015195,popular,2,184,Nightstand Everyday 721,9,False,0
session_015195,popular,3,110,Shampoo Everyday 111,6,True,0
session_015195,popular,4,12,Keyboard Classic 505,1,False,0
session_015195,popular,5,49,Biography Deluxe 648,3,False,0
session_015195,personalized,1,30,T-shirt Everyday 987,2,True,0
session_015195,personalized,2,110,Shampoo Everyday 111,6,True,0
session_015195,personalized,3,31,T-shirt Classic 854,2,True,0
session_015195,personalized,4,36,Backpack Classic 759,2,True,0
session_015195,personalized,5,23,Jacket Essential 819,2,True,0
session_008593,popular,1,90,Table Lamp Eco 643,5,False,0
session_008593,popular,2,184,Nightstand Everyday 721,9,False,0
session_008593,popular,3,110,Shampoo Everyday 111,6,False,0
session_008593,popular,4,49,Biography Deluxe 648,3,False,0
session_008593,popular,5,76,Tennis Racket Compact 416,4,False,0
session_008593,personalized,1,223,Ukulele Premium 117,11,True,0
session_008593,personalized,2,9,Monitor Premium 997,1,True,0
session_008593,personalized,3,2,Smartphone Compact 854,1,True,0
session_008593,personalized,4,224,Ukulele Essential 759,11,True,0
session_008593,personalized,5,230,Effects Pedal Eco 176,11,True,0
session_006839,popular,1,90,Table Lamp Eco 643,5,False,0
session_006839,popular,2,184,Nightstand Everyday 721,9,False,0
session_006839,popular,3,110,Shampoo Everyday 111,6,False,0
session_006839,popular,4,12,Keyboard Classic 505,1,False,0
session_006839,popular,5,49,Biography Deluxe 648,3,False,0
session_006839,personalized,1,148,Coffee Beans Pro 813,8,True,0
session_006839,personalized,2,160,Granola Premium 789,8,True,0
session_006839,personalized,3,65,Running Shoes Deluxe 803,4,True,0
session_006839,personalized,4,66,Yoga Mat Premium 817,4,True,0
session_006839,personalized,5,77,Tennis Racket Classic 374,4,True,0
session_013699,popular,1,90,Table Lamp Eco 643,5,False,1
session_013699,popular,2,184,Nightstand Everyday 721,9,False,0
session_013699,popular,3,110,Shampoo Everyday 111,6,False,0
session_013699,popular,4,12,Keyboard Classic 505,1,False,0
session_013699,popular,5,231,Studio Headphones Classic 686,11,False,0
session_013699,personalized,1,243,Ladder Deluxe 713,12,True,0
session_013699,personalized,2,234,Screwdriver Set Eco 897,12,True,0
session_013699,personalized,3,247,Spirit Level Eco 157,12,True,0
session_013699,personalized,4,249,Work Gloves Compact 227,12,True,0
session_013699,personalized,5,232,Cordless Drill Classic 499,12,True,0
session_012714,popular,1,90,Table Lamp Eco 643,5,False,0
session_012714,popular,2,184,Nightstand Everyday 721,9,False,0
session_012714,popular,3,110,Shampoo Everyday 111,6,False,0
session_012714,popular,4,12,Keyboard Classic 505,1,False,0
session_012714,popular,5,49,Biography Deluxe 648,3,False,0
session_012714,personalized,1,76,Tennis Racket Compact 416,4,True,1
session_012714,personalized,2,80,Fitness Band Eco 108,4,True,0
session_012714,personalized,3,74,Football Deluxe 883,4,True,0
session_012714,personalized,4,156,Honey Everyday 491,8,True,0
session_012714,personalized,5,68,Dumbbell Set Premium 193,4,True,0
session_015038,popular,1,90,Table Lamp Eco 643,5,True,0
session_015038,popular,2,110,Shampoo Everyday 111,6,False,0
session_015038,popular,3,12,Keyboard Classic 505,1,False,0
session_015038,popular,4,49,Biography Deluxe 648,3,False,0
session_015038,popular,5,231,Studio Headphones Classic 686,11,False,0
session_015038,personalized,1,177,Bed Frame Eco 577,9,True,0
session_015038,personalized,2,169,Sofa Essential 990,9,True,0
session_015038,personalized,3,171,Office Chair Deluxe 707,9,True,0
session_015038,personalized,4,172,Office Chair Classic 995,9,True,0
session_015038,personalized,5,187,Armchair Eco 684,9,True,0
session_007096,popular,1,90,Table Lamp Eco 643,5,False,0
session_007096,popular,2,184,Nightstand Everyday 721,9,False,0
session_007096,popular,3,110,Shampoo Everyday 111,6,False,0
session_007096,popular,4,12,Keyboard Classic 505,1,True,0
session_007096,popular,5,49,Biography Deluxe 648,3,False,0
session_007096,personalized,1,12,Keyboard Classic 505,1,True,0
session_007096,personalized,2,9,Monitor Premium 997,1,True,0
session_007096,personalized,3,200,Floor Mats Everyday 949,10,True,0
session_007096,personalized,4,17,Camera Compact 359,1,True,1
session_007096,personalized,5,6,Headphones Compact 103,1,True,0
session_011678,popular,1,90,Table Lamp Eco 643,5,False,0
session_011678,popular,2,184,Nightstand Everyday 721,9,False,0
session_011678,popular,3,110,Shampoo Everyday 111,6,False,0
session_011678,popular,4,12,Keyboard Classic 505,1,True,0
session_011678,popular,5,49,Biography Deluxe 648,3,False,0
session_011678,personalized,1,12,Keyboard Classic 505,1,True,0
session_011678,personalized,2,2,Smartphone Compact 854,1,True,0
session_011678,personalized,3,9,Monitor Premium 997,1,True,0
session_011678,personalized,4,6,Headphones Compact 103,1,True,0
session_011678,personalized,5,13,Mouse Deluxe 406,1,True,0
session_000987,popular,1,90,Table Lamp Eco 643,5,False,0
session_000987,popular,2,184,Nightstand Everyday 721,9,False,0
session_000987,popular,3,110,Shampoo Everyday 111,6,False,0
session_000987,popular,4,12,Keyboard Classic 505,1,False,0
session_000987,popular,5,49,Biography Deluxe 648,3,True,0
session_000987,personalized,1,49,Biography Deluxe 648,3,True,0
session_000987,personalized,2,198,Car Charger Everyday 607,10,True,0
session_000987,personalized,3,60,Poetry Everyday 604,3,True,0
session_000987,personalized,4,63,Cookbook Compact 232,3,True,0
session_000987,personalized,5,44,Novel Premium 964,3,True,0
session_008633,popular,1,90,Table Lamp Eco 643,5,False,0
session_008633,popular,2,184,Nightstand Everyday 721,9,False,0
session_008633,popular,3,110,Shampoo Everyday 111,6,False,0
session_008633,popular,4,12,Keyboard Classic 505,1,True,0
session_008633,popular,5,49,Biography Deluxe 648,3,False,0
session_008633,personalized,1,12,Keyboard Classic 505,1,True,0
session_008633,personalized,2,224,Ukulele Essential 759,11,True,0
session_008633,personalized,3,230,Effects Pedal Eco 176,11,True,0
session_008633,personalized,4,2,Smartphone Compact 854,1,True,0
session_008633,personalized,5,229,Effects Pedal Essential 260,11,True,0
session_002353,popular,1,90,Table Lamp Eco 643,5,False,0
session_002353,popular,2,184,Nightstand Everyday 721,9,False,0
session_002353,popular,3,110,Shampoo Everyday 111,6,False,0
session_002353,popular,4,12,Keyboard Classic 505,1,False,0
session_002353,popular,5,49,Biography Deluxe 648,3,False,0
session_002353,personalized,1,239,Tape Measure Premium 980,12,True,0
session_002353,personalized,2,246,Spirit Level Pro 357,12,True,0
session_002353,personalized,3,250,Glue Gun Deluxe 657,12,True,0
session_002353,personalized,4,237,Hammer Essential 102,12,True,0
session_002353,personalized,5,252,Spirit Level Classic 425,12,True,0
session_002787,popular,1,90,Table Lamp Eco 643,5,False,0
session_002787,popular,2,184,Nightstand Everyday 721,9,False,0
session_002787,popular,3,12,Keyboard Classic 505,1,False,0
session_002787,popular,4,49,Biography Deluxe 648,3,False,0
session_002787,popular,5,231,Studio Headphones Classic 686,11,False,0
session_002787,personalized,1,118,Body Lotion Deluxe 734,6,True,0
session_002787,personalized,2,121,Sunscreen Classic 799,6,True,0
session_002787,personalized,3,108,Serum Essential 226,6,True,0
session_002787,personalized,4,107,Face Cream Everyday 865,6,True,0
session_002787,personalized,5,114,Lipstick Compact 868,6,True,0
session_006234,popular,1,90,Table Lamp Eco 643,5,False,0
session_006234,popular,2,184,Nightstand Everyday 721,9,False,0
session_006234,popular,3,12,Keyboard Classic 505,1,False,0
session_006234,popular,4,49,Biography Deluxe 648,3,False,0
session_006234,popular,5,231,Studio Headphones Classic 686,11,False,0
session_006234,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_006234,personalized,2,121,Sunscreen Classic 799,6,True,0
session_006234,personalized,3,108,Serum Essential 226,6,True,0
session_006234,personalized,4,107,Face Cream Everyday 865,6,True,0
session_006234,personalized,5,115,Lipstick Eco 829,6,True,0
session_006663,popular,1,90,Table Lamp Eco 643,5,False,0
session_006663,popular,2,184,Nightstand Everyday 721,9,False,0
session_006663,popular,3,12,Keyboard Classic 505,1,False,0
session_006663,popular,4,49,Biography Deluxe 648,3,False,0
session_006663,popular,5,231,Studio Headphones Classic 686,11,False,0
session_006663,personalized,1,125,Beard Trimmer Premium 354,6,True,0
session_006663,personalized,2,118,Body Lotion Deluxe 734,6,True,0
session_006663,personalized,3,123,Makeup Brush Set Pro 675,6,True,0
session_006663,personalized,4,108,Serum Essential 226,6,True,0
session_006663,personalized,5,114,Lipstick Compact 868,6,True,0
session_001962,popular,1,90,Table Lamp Eco 643,5,False,0
session_001962,popular,2,184,Nightstand Everyday 721,9,False,0
session_001962,popular,3,110,Shampoo Everyday 111,6,False,0
session_001962,popular,4,49,Biography Deluxe 648,3,False,0
session_001962,popular,5,231,Studio Headphones Classic 686,11,True,0
session_001962,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_001962,personalized,2,223,Ukulele Premium 117,11,True,0
session_001962,personalized,3,224,Ukulele Essential 759,11,True,0
session_001962,personalized,4,230,Effects Pedal Eco 176,11,True,0
session_001962,personalized,5,9,Monitor Premium 997,1,True,0
session_010860,popular,1,90,Table Lamp Eco 643,5,False,0
session_010860,popular,2,184,Nightstand Everyday 721,9,False,0
session_010860,popular,3,110,Shampoo Everyday 111,6,False,0
session_010860,popular,4,12,Keyboard Classic 505,1,False,0
session_010860,popular,5,231,Studio Headphones Classic 686,11,False,0
session_010860,personalized,1,41,Boots Compact 911,2,True,0
session_010860,personalized,2,37,Backpack Compact 926,2,True,0
session_010860,personalized,3,39,Cap Everyday 356,2,True,1
session_010860,personalized,4,36,Backpack Classic 759,2,True,0
session_010860,personalized,5,32,Scarf Eco 733,2,True,0
session_009670,popular,1,90,Table Lamp Eco 643,5,False,0
session_009670,popular,2,184,Nightstand Everyday 721,9,False,0
session_009670,popular,3,110,Shampoo Everyday 111,6,False,0
session_009670,popular,4,12,Keyboard Classic 505,1,False,0
session_009670,popular,5,49,Biography Deluxe 648,3,False,0
session_009670,personalized,1,30,T-shirt Everyday 987,2,True,1
session_009670,personalized,2,37,Backpack Compact 926,2,True,0
session_009670,personalized,3,41,Boots Compact 911,2,True,0
session_009670,personalized,4,76,Tennis Racket Compact 416,4,True,0
session_009670,personalized,5,80,Fitness Band Eco 108,4,True,0
session_005279,popular,1,110,Shampoo Everyday 111,6,False,0
session_005279,popular,2,12,Keyboard Classic 505,1,False,0
session_005279,popular,3,49,Biography Deluxe 648,3,False,0
session_005279,popular,4,231,Studio Headphones Classic 686,11,False,0
session_005279,popular,5,76,Tennis Racket Compact 416,4,False,0
session_005279,personalized,1,103,Candle Everyday 732,5,True,0
session_005279,personalized,2,87,Coffee Maker Pro 639,5,True,0
session_005279,personalized,3,86,Blender Everyday 283,5,True,0
session_005279,personalized,4,177,Bed Frame Eco 577,9,True,0
session_005279,personalized,5,181,Coffee Table Eco 857,9,True,0
session_009585,popular,1,90,Table Lamp Eco 643,5,False,0
session_009585,popular,2,110,Shampoo Everyday 111,6,False,0
session_009585,popular,3,49,Biography Deluxe 648,3,False,0
session_009585,popular,4,231,Studio Headphones Classic 686,11,False,0
session_009585,popular,5,76,Tennis Racket Compact 416,4,False,0
session_009585,personalized,1,177,Bed Frame Eco 577,9,True,0
session_009585,personalized,2,9,Monitor Premium 997,1,True,0
session_009585,personalized,3,2,Smartphone Compact 854,1,True,0
session_009585,personalized,4,181,Coffee Table Eco 857,9,True,0
session_009585,personalized,5,185,Dining Chair Classic 954,9,True,0
session_010491,popular,1,90,Table Lamp Eco 643,5,False,0
session_010491,popular,2,184,Nightstand Everyday 721,9,True,0
session_010491,popular,3,110,Shampoo Everyday 111,6,False,0
session_010491,popular,4,12,Keyboard Classic 505,1,False,0
session_010491,popular,5,49,Biography Deluxe 648,3,False,0
session_010491,personalized,1,198,Car Charger Everyday 607,10,True,0
session_010491,personalized,2,184,Nightstand Everyday 721,9,True,0
session_010491,personalized,3,206,Car Vacuum Deluxe 348,10,True,0
session_010491,personalized,4,243,Ladder Deluxe 713,12,False,0
session_010491,personalized,5,208,Jump Starter Essential 942,10,True,0
session_004664,popular,1,90,Table Lamp Eco 643,5,False,0
session_004664,popular,2,184,Nightstand Everyday 721,9,True,0
session_004664,popular,3,12,Keyboard Classic 505,1,False,0
session_004664,popular,4,49,Biography Deluxe 648,3,False,0
session_004664,popular,5,231,Studio Headphones Classic 686,11,False,0
session_004664,personalized,1,184,Nightstand Everyday 721,9,True,0
session_004664,personalized,2,181,Coffee Table Eco 857,9,True,0
session_004664,personalized,3,185,Dining Chair Classic 954,9,True,0
session_004664,personalized,4,175,Bookshelf Eco 371,9,True,0
session_004664,personalized,5,182,Coffee Table Pro 626,9,True,0
session_011819,popular,1,110,Shampoo Everyday 111,6,False,0
session_011819,popular,2,12,Keyboard Classic 505,1,False,0
session_011819,popular,3,49,Biography Deluxe 648,3,False,0
session_011819,popular,4,231,Studio Headphones Classic 686,11,False,0
session_011819,popular,5,76,Tennis Racket Compact 416,4,False,0
session_011819,personalized,1,198,Car Charger Everyday 607,10,True,0
session_011819,personalized,2,208,Jump Starter Essential 942,10,True,0
session_011819,personalized,3,205,Ice Scraper Deluxe 739,10,True,0
session_011819,personalized,4,196,Phone Holder Pro 656,10,True,0
session_011819,personalized,5,210,Dash Cam Premium 877,10,True,0
session_005569,popular,1,90,Table Lamp Eco 643,5,False,0
session_005569,popular,2,184,Nightstand Everyday 721,9,False,0
session_005569,popular,3,110,Shampoo Everyday 111,6,False,0
session_005569,popular,4,12,Keyboard Classic 505,1,False,0
session_005569,popular,5,49,Biography Deluxe 648,3,False,0
session_005569,personalized,1,41,Boots Compact 911,2,True,0
session_005569,personalized,2,30,T-shirt Everyday 987,2,True,0
session_005569,personalized,3,37,Backpack Compact 926,2,True,0
session_005569,personalized,4,31,T-shirt Classic 854,2,True,0
session_005569,personalized,5,40,Boots Compact 582,2,True,0
session_011534,popular,1,90,Table Lamp Eco 643,5,False,0
session_011534,popular,2,184,Nightstand Everyday 721,9,False,0
session_011534,popular,3,110,Shampoo Everyday 111,6,False,0
session_011534,popular,4,12,Keyboard Classic 505,1,True,0
session_011534,popular,5,49,Biography Deluxe 648,3,False,0
session_011534,personalized,1,12,Keyboard Classic 505,1,True,0
session_011534,personalized,2,6,Headphones Compact 103,1,True,0
session_011534,personalized,3,17,Camera Compact 359,1,True,0
session_011534,personalized,4,10,Monitor Classic 784,1,True,0
session_011534,personalized,5,13,Mouse Deluxe 406,1,True,0
session_005865,popular,1,90,Table Lamp Eco 643,5,False,0
session_005865,popular,2,184,Nightstand Everyday 721,9,False,0
session_005865,popular,3,110,Shampoo Everyday 111,6,False,0
session_005865,popular,4,12,Keyboard Classic 505,1,False,0
session_005865,popular,5,49,Biography Deluxe 648,3,False,0
session_005865,personalized,1,127,Building Blocks Premium 126,7,True,0
session_005865,personalized,2,137,Plush Toy Classic 439,7,True,0
session_005865,personalized,3,142,Paint Set Deluxe 295,7,True,0
session_005865,personalized,4,141,Paint Set Classic 369,7,True,0
session_005865,personalized,5,129,Board Game Deluxe 308,7,True,0
session_012583,popular,1,90,Table Lamp Eco 643,5,False,0
session_012583,popular,2,184,Nightstand Everyday 721,9,False,0
session_012583,popular,3,110,Shampoo Everyday 111,6,False,0
session_012583,popular,4,12,Keyboard Classic 505,1,False,0
session_012583,popular,5,49,Biography Deluxe 648,3,True,0
session_012583,personalized,1,49,Biography Deluxe 648,3,True,0
session_012583,personalized,2,127,Building Blocks Premium 126,7,True,0
session_012583,personalized,3,52,Fantasy Pro 681,3,True,0
session_012583,personalized,4,60,Poetry Everyday 604,3,True,0
session_012583,personalized,5,44,Novel Premium 964,3,True,0
session_002981,popular,1,90,Table Lamp Eco 643,5,False,0
session_002981,popular,2,184,Nightstand Everyday 721,9,False,0
session_002981,popular,3,110,Shampoo Everyday 111,6,False,0
session_002981,popular,4,12,Keyboard Classic 505,1,False,0
session_002981,popular,5,49,Biography Deluxe 648,3,False,0
session_002981,personalized,1,133,Doll Eco 977,7,True,0
session_002981,personalized,2,137,Plush Toy Classic 439,7,True,0
session_002981,personalized,3,134,Doll Classic 843,7,True,0
session_002981,personalized,4,132,Puzzle Everyday 336,7,True,0
session_002981,personalized,5,140,Robot Kit Essential 218,7,True,0
session_012694,popular,1,90,Table Lamp Eco 643,5,False,0
session_012694,popular,2,184,Nightstand Everyday 721,9,False,0
session_012694,popular,3,110,Shampoo Everyday 111,6,False,0
session_012694,popular,4,49,Biography Deluxe 648,3,False,0
session_012694,popular,5,231,Studio Headphones Classic 686,11,True,0
session_012694,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_012694,personalized,2,223,Ukulele Premium 117,11,True,0
session_012694,personalized,3,6,Headphones Compact 103,1,True,0
session_012694,personalized,4,17,Camera Compact 359,1,True,0
session_012694,personalized,5,13,Mouse Deluxe 406,1,True,0
session_000480,popular,1,90,Table Lamp Eco 643,5,False,0
session_000480,popular,2,184,Nightstand Everyday 721,9,False,0
session_000480,popular,3,110,Shampoo Everyday 111,6,False,0
session_000480,popular,4,12,Keyboard Classic 505,1,False,0
session_000480,popular,5,49,Biography Deluxe 648,3,True,0
session_000480,personalized,1,49,Biography Deluxe 648,3,True,0
session_000480,personalized,2,60,Poetry Everyday 604,3,True,0
session_000480,personalized,3,63,Cookbook Compact 232,3,True,0
session_000480,personalized,4,50,Biography Essential 819,3,True,0
session_000480,personalized,5,43,Novel Premium 556,3,True,0
session_009705,popular,1,90,Table Lamp Eco 643,5,False,0
session_009705,popular,2,184,Nightstand Everyday 721,9,False,0
session_009705,popular,3,110,Shampoo Everyday 111,6,False,0
session_009705,popular,4,12,Keyboard Classic 505,1,False,0
session_009705,popular,5,49,Biography Deluxe 648,3,False,0
session_009705,personalized,1,200,Floor Mats Everyday 949,10,True,0
session_009705,personalized,2,198,Car Charger Everyday 607,10,True,0
session_009705,personalized,3,193,Car Battery Deluxe 488,10,True,0
session_009705,personalized,4,208,Jump Starter Essential 942,10,True,0
session_009705,personalized,5,210,Dash Cam Premium 877,10,True,0
session_014395,popular,1,90,Table Lamp Eco 643,5,False,0
session_014395,popular,2,184,Nightstand Everyday 721,9,False,0
session_014395,popular,3,110,Shampoo Everyday 111,6,False,0
session_014395,popular,4,12,Keyboard Classic 505,1,False,0
session_014395,popular,5,49,Biography Deluxe 648,3,False,0
session_014395,personalized,1,76,Tennis Racket Compact 416,4,True,0
session_014395,personalized,2,80,Fitness Band Eco 108,4,True,0
session_014395,personalized,3,68,Dumbbell Set Premium 193,4,True,0
session_014395,personalized,4,67,Yoga Mat Everyday 759,4,True,0
session_014395,personalized,5,65,Running Shoes Deluxe 803,4,True,0
session_001996,popular,1,90,Table Lamp Eco 643,5,False,0
session_001996,popular,2,184,Nightstand Everyday 721,9,False,0
session_001996,popular,3,110,Shampoo Everyday 111,6,False,0
session_001996,popular,4,49,Biography Deluxe 648,3,False,0
session_001996,popular,5,231,Studio Headphones Classic 686,11,True,0
session_001996,personalized,1,231,Studio Headphones Classic 686,11,True,0
session_001996,personalized,2,230,Effects Pedal Eco 176,11,True,0
session_001996,personalized,3,229,Effects Pedal Essential 260,11,True,0
session_001996,personalized,4,225,Drum Sticks Pro 333,11,True,0
session_001996,personalized,5,2,Smartphone Compact 854,1,True,0
```

### data/metadata.json

```
{
  "dataset": "dm_session_feedback_v1",
  "description": "Simulated experiment-ready log for the popular-vs-personalized CTR comparison. impressions.csv logs k impressions per algorithm per sampled session with a DETERMINISTIC simulated click (seed 42). The SAME click model is used for both algorithms (relevant_base if the product is in the session's top-2 categories, else base, times a position factor), so the CTR difference comes only from which products each algorithm ranks where. Data collection for an A/B experiment, not a significance test.",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "products": "Day 5/data/products_text.csv",
    "module": "app.data.generate_session",
    "function": "generate_session",
    "recommender_module": "app.recommenders.session",
    "recommend_function": "recommend_for_session",
    "ctr_function": "app.recommenders.session.recommendation_ctr"
  },
  "parameters": {
    "seed": 42,
    "n_sessions": 200,
    "k": 5,
    "min_session_product_events": 2,
    "recency_decay": 0.8,
    "session_top_n": 2,
    "click_model": {
      "relevant_base": 0.06,
      "base": 0.02,
      "position_factors": [
        1.0,
        0.6,
        0.4,
        0.3,
        0.2
      ]
    },
    "sampling": "deterministic rng.choice over sessions with >= min_session_product_events product events (no replacement)"
  },
  "click_model_note": "Clicks are SIMULATED with the documented click_model — this is not real user behavior. The point is the LOGGING MECHANISM (algorithm, position, clicked) and the CTR math, not a true A/B outcome.",
  "columns": {
    "impressions.csv": {
      "session_id": "str, sesija (Day 1 kolona) — jedinica eksperimenta",
      "algorithm": "str, popular ili personalized (impression se loguje pod algoritmom)",
      "position": "int, pozicija preporuke (1=prva) — position-bias",
      "product_id": "int, stabilan ID proizvoda",
      "name": "str, naziv proizvoda (katalog)",
      "category_id": "int, kategorija proizvoda",
      "session_top_category": "bool, da li je proizvod u top-2 kategorijama sesije",
      "clicked": "int, 0/1 — SIMULIRAN klik (seed 42, klik-model u metadata.click_model)"
    },
    "ctr.csv": {
      "level": "str, algorithm ili position (nivo agregacije)",
      "group": "str, vrednost (npr. popular / personalized / position_1)",
      "impressions": "int, broj impresija",
      "clicks": "int, broj klikova",
      "ctr": "float, clicks/impressions (0 ako nema impresija)"
    },
    "comparison.csv": {
      "algorithm": "str, popular ili personalized",
      "impressions": "int, broj impresija",
      "clicks": "int, broj klikova",
      "ctr": "float, click-through rate"
    }
  },
  "counts": {
    "n_sessions": 200,
    "n_impressions": 2000,
    "n_popular_impressions": 1000,
    "n_personalized_impressions": 1000,
    "n_clicks": 33,
    "n_catalog": 252
  },
  "comparison": [
    {
      "algorithm": "popular",
      "impressions": 1000,
      "clicks": 11,
      "ctr": 0.011
    },
    {
      "algorithm": "personalized",
      "impressions": 1000,
      "clicks": 22,
      "ctr": 0.022
    }
  ],
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "impressions.csv": "07c40173f17f77ecb692471763ef26a1e0d9f94c52a8c7f9130708cd6ec59c47",
      "ctr.csv": "387101ad0982becfe3fd827508e2438993b400815aa46bd9edc28fb9a9200a38",
      "comparison.csv": "3a0eccceb666d808e43da0ecdab18f611d6bc1ea8e040af27cc13dcb66bbfe22"
    }
  }
}
```

### data/README.md

# Day 9 podaci — experiment-ready impression log (popular vs personalized)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja + Day 5 kataloga (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, klik-model, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `impressions.csv` | experiment log: impresije oba algoritma (`popular`/`personalized`) po sesiji, sa SIMULIRANIM klikom | 2000 |
| `ctr.csv` | CTR po algoritmu i po poziciji (`level`, `group`, `impressions`, `clicks`, `ctr`) | 7 |
| `comparison.csv` | **popular vs personalized** (`algorithm`, `impressions`, `clicks`, `ctr`) | 2 |
| `metadata.json` | izvor, parametri, klik-model, counts, comparison, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` (istorija) + `Day 5/data/products_text.csv`
  (katalog).
* Uzorak: **200 sesija** sa ≥ 2 proizvodna događaja (deterministički,
  `numpy.random.default_rng(42)`, bez ponavljanja).
* Za svaku sesiju, oba algoritma loguju `k=5` impresija:
  + `popular` — globalni popularity top-5 (bez proizvoda koje je sesija već
    videla);
  + `personalized` — `recommend_for_session` (session-aware, recency-weighted
    interes, bez već viđenih).
* **Klik je SIMULIRAN** klik-modelom iz `metadata.json → click_model`:
  + personalized: viši `base` (0.06) ako je proizvod u top-2 kategorijama
    sesije, inače 0.02;
  + popular: base 0.02;
  + oba algoritma: position-bias (`position_factors = [1.0, 0.6, 0.4, 0.3, 0.2]`).
* Generator: `app/data/generate_session.py` (upisuje CSV + metadata).

## Ključne kolone (`impressions.csv`)

| Kolona | Značenje |
| --- | --- |
| `session_id` | sesija (Day 1) — jedinica eksperimenta |
| `algorithm` | `popular` ili `personalized` (pod kojim algoritmom je impresija logovana) |
| `position` | pozicija preporuke (1 = prva) — position-bias |
| `product_id` | preporučeni proizvod |
| `name` | naziv (katalog) |
| `category_id` | kategorija proizvoda |
| `session_top_category` | da li je proizvod u top-2 kategorijama sesije (dijagnostika) |
| `clicked` | 0/1 — SIMULIRAN klik (seed 42, klik-model u metadata) |

## Stanje u ovom seed-u

| Algoritam | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| **popular** | 1000 | 11 | **0.011** |
| **personalized** | 1000 | 22 | **0.022** |

CTR po poziciji (position-bias — prva pozicija nosi više klikova):

| Pozicija | Impresija | Klikova | CTR |
| --- | --- | --- | --- |
| 1 | 400 | 16 | 0.0400 |
| 2 | 400 | 5 | 0.0125 |
| 3 | 400 | 7 | 0.0175 |
| 4 | 400 | 5 | 0.0125 |
| 5 | 400 | 0 | 0.0000 |

Klikovi su **simulirani** (click\_model u `metadata.json`); na ovako malom uzorku
(2000 impresija) kriva po poziciji je bučna — na pravom store-u treba više impresija.

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_session
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

* **CTR razlika NIJE statistički potvrđen A/B rezultat.** Klikovi su SIMULIRANI
  determinističkim klik-modelom; na pravom store-u treba ti pravi eksperiment
  (logovanje impresija/klikova kroz `POST /recommendations/events` i dovoljno
  saobraćaja). Day 9 proizvodi *prikupljanje podataka* za taj eksperiment
  (experiment-ready), ne značajnosni test.
* **Personalized nije "dokazano bolji".** Na ovom simuliranom logu
  `personalized` ima viši CTR jer mu je klik-model favorabilniji za
  session-relevantne proizvode — to je MODEL, ne stvarno ponašanje korisnika.
* **Position-bias je realan, ali su klikovi simulirani.** Prava raspodela po
  pozicijama zavisi od saobraćaja i UI-ja; logovana pozicija je ono što meriš.

### examples/demo\_session.py

```
"""Demo: session-aware preporuke i feedback loop (Day 9).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 9/examples/demo_session.py"

Prikazuje:
  1) **session features** — recency-weighted interes iz tekuće sesije
     (trajanje, top kategorije/proizvodi, recency);
  2) **session-aware preporuke** — ``recommend_for_session`` (kandidati iz top
     kategorija sesije, bez već viđenih, blend sa popularnošću);
  3) **cold-start fallback** — nepoznata sesija -> popularity (nikad tihi []);
  4) **CTR** — overall + po algoritmu + po poziciji iz seeded impression/click
     loga (zero-division -> 0.0);
  5) **popular vs personalized** — experiment-ready poređenje iz
     ``Day 9/data/impressions.csv`` (simulirani klik-model, NIJE A/B rezultat).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.session import SessionRecommenderService

DEMO_SESSION = "session_005246"   # bogata sesija (korisnik 395: 15 pregleda, 3 kategorije)


def _ids(records: list[dict]) -> str:
    return ",".join(str(r["product_id"]) for r in records)


def main() -> None:
    print("=== Day 9 — Session-Aware Recommendations and the Feedback Loop ===\n")
    svc = SessionRecommenderService()

    # --- 1) Session features ------------------------------------------------- #
    res = svc.recommend_for_session(DEMO_SESSION, limit=5)
    feats = res["session_features"]
    print(f"[1] Session features za sesiju {DEMO_SESSION}:")
    print(f"    n_events={feats['n_events']}  product_events="
          f"{feats['n_product_events']}  distinct_products="
          f"{feats['n_distinct_products']}  duration={feats['duration_minutes']}min")
    print(f"    top_categories: "
          f"{[(c['category_id'], c['interest']) for c in feats['top_categories']]}")
    print(f"    top_products:   "
          f"{[(p['product_id'], p['interest']) for p in feats['top_products']]}")
    print()

    # --- 2) Session-aware preporuke ------------------------------------------ #
    print(f"[2] Session-aware preporuke (k={res['returned']}, "
          f"isključeno viđenih: {res['excluded_seen']}):")
    for r in res["recommendations"]:
        print(f"      #{res['recommendations'].index(r) + 1}  {r['product_id']:>3}  "
              f"{r['name']:<22} score={r['score']:.4f}  "
              f"sources=[{';'.join(r['sources'])}]")
    print()

    # --- 3) Cold-start fallback ---------------------------------------------- #
    print("[3] Cold-start fallback (nepoznata sesija 'session_NOPE'):")
    cs = svc.recommend_for_session("session_NOPE", limit=5)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-5: "
          f"{_ids(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 4) CTR iz seeded impression/click loga ------------------------------- #
    ctr = svc.ctr_dashboard()
    print("[4] CTR iz seeded impression/click loga (zero-division -> 0.0):")
    print(f"    overall: impressions={ctr['overall']['impressions']} "
          f"clicks={ctr['overall']['clicks']} ctr={ctr['overall']['ctr']:.4f}")
    for g in ctr["by_algorithm"]["groups"]:
        print(f"      {g['group']:10s} impressions={g['impressions']:>6} "
              f"clicks={g['clicks']:>4}  ctr={g['ctr']:.4f}")
    print("    po poziciji (position-bias):")
    for g in ctr["by_position"]["groups"]:
        print(f"      position {g['group']}: impressions={g['impressions']:>6} "
              f"clicks={g['clicks']:>4}  ctr={g['ctr']:.4f}")
    print()

    # --- 5) Popular vs personalized ------------------------------------------ #
    print("[5] Popular vs personalized (experiment-ready log, Day 9/data):")
    comp = svc.popular_vs_personalized_comparison()
    print(f"    sessions={comp['n_sessions']}  impressions={comp['n_impressions']}")
    for row in comp["comparison"]:
        print(f"      {row['algorithm']:14s} impressions={row['impressions']:>5} "
              f"clicks={row['clicks']:>4}  ctr={row['ctr']:.4f}")
    print("    klikovi su SIMULIRANI (seed 42, klik-model u metadata.json) —")
    print("    CTR razlika NIJE statistički potvrđen A/B rezultat; Day 9 pravi")
    print("    *prikupljanje podataka* za eksperiment (experiment-ready).")
    print()
    print("API: GET /recommendations/session/{session_id} · "
          "POST /recommendations/events · GET /analytics/recommendations/ctr")
    print("     GET /analytics/recommendations/session-comparison")


if __name__ == "__main__":
    main()
```

### lab/README.md

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

### lab/starter.py

```
"""Starter za Day 9 lab — session features, recency i CTR (feedback loop).

Implementiraš mali deo onoga što kursni modul ``dm-ml/app/recommenders/session.py``
već sadrži (da razumeš *šta* session-aware preporuke i CTR rade). Ne menjaš
``dm-ml`` — radiš u ovom fajlu i proveravaš svoje rešenje sa ``test_lab.py``.

Lab radi na malim, ručno napravljenim strukturama (list dict-ova) — bez pandas-a.
"""

# Težine događaja unutar sesije (Day 9 / Day 5-8 kontinuitet).
EVENT_WEIGHTS = {"product_view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}


# --------------------------------------------------------------------------- #
# 1) recency_weights — geometrijska recency težina
# --------------------------------------------------------------------------- #
def recency_weights(n, decay):
    """Težina po događaju, od najnovijeg (1.0) ka najstarijem (``decay**i``).

    Za ``n`` događaja (najnoviji je POSLEDNJI): težina i-tog je
    ``decay ** (n - 1 - i)``. ``n == 0`` -> ``[]``.

    Zašto: skoriji događaji nose više informacije o tekućem interesu — sesija
    koja je pre 2 min gledala 'tenis' je verovatnije o tenisu nego ona koja je
    tenis gledala pre 30 min (recency).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) recent_product_interest — recency-weighted interes proizvoda
# --------------------------------------------------------------------------- #
def recent_product_interest(events, decay=0.8):
    """``{product_id: interes}`` iz proizvodnih događaja sesije.

    ``events`` = lista dict-ova ``{"event_type": str, "product_id": int}``
    (hronološki poredak — najnoviji POSLEDNJI). Za svaki proizvodni događaj
    (``event_type`` u ``EVENT_WEIGHTS``): težina = ``EVENT_WEIGHTS[type] *
    recency_weights[i]``; agregira se (zbir) po proizvodu.

    Vraća dict ``product_id -> interes``. Bez proizvodnih događaja -> ``{}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) recent_category_interest — interes kategorija iz sesije
# --------------------------------------------------------------------------- #
def recent_category_interest(events, product_categories, decay=0.8):
    """``{category_id: interes}`` — mapira proizvodni interes na kategorije.

    ``product_categories`` = dict ``product_id -> category_id`` (katalog je
    source of truth). Interes proizvoda (iz ``recent_product_interest``) se
    sabira po kategoriji. Proizvodi kojih nema u katalogu se ignorišu.

    Vraća dict ``category_id -> interes``. Prazno -> ``{}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) recommendation_ctr — CTR sa zero-division handling-om
# --------------------------------------------------------------------------- #
def recommendation_ctr(impressions, clicks):
    """Click-through rate: ``len(clicks) / len(impressions)``.

    ``impressions`` = lista (npr. impression događaja); ``clicks`` = lista
    (npr. click događaja). **Zero-division:** ``len(impressions) == 0`` ->
    vraća ``0.0`` (bez ``None``, bez deljenja kroz nulu).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) ctr_by_algorithm — CTR po algoritmu
# --------------------------------------------------------------------------- #
def ctr_by_algorithm(impressions, clicks):
    """CTR po ``algorithm`` (``recommendation_source``).

    ``impressions``/``clicks`` = liste dict-ova sa ključem ``algorithm`` (npr.
    ``"popular"``/``"personalized"``). Vraća listu dict-ova sortiranu po
    ``algorithm`` rastuće:

        [{"algorithm": "popular", "impressions": N, "clicks": C, "ctr": float},
         {"algorithm": "personalized", ...}, ...]

    Algoritam sa 0 impresija -> ``ctr = 0.0`` (zero-division).
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


def test_recency():
    assert lab.recency_weights(3, 0.5) == [0.25, 0.5, 1.0]
    assert lab.recency_weights(0, 0.8) == []


def test_interest():
    ev = [{"event_type": "product_view", "product_id": 1}, {"event_type": "search", "product_id": None},
          {"event_type": "add_to_cart", "product_id": 2}]
    pi = lab.recent_product_interest(ev, decay=0.5)
    assert pi == {1: pytest.approx(0.5), 2: pytest.approx(3.0)}
    ci = lab.recent_category_interest(ev, {1: 10, 2: 10}, decay=0.5)
    assert ci == {10: pytest.approx(3.5)}
    assert lab.recent_product_interest([{"event_type": "search", "product_id": None}]) == {}


def test_ctr():
    assert lab.recommendation_ctr([1, 2, 3, 4], [1]) == 0.25
    assert lab.recommendation_ctr([], []) == 0.0
    imps = [{"algorithm": "popular"}] * 4 + [{"algorithm": "personalized"}] * 2
    rows = lab.ctr_by_algorithm(imps, [{"algorithm": "personalized"}])
    assert [r["algorithm"] for r in rows] == ["personalized", "popular"]   # rastuće po imenu
    assert rows[0]["ctr"] == 0.5 and rows[1]["ctr"] == 0.0
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 9 lab-a."""
from __future__ import annotations

from collections import defaultdict

from starter import EVENT_WEIGHTS  # noqa: F401


def recency_weights(n, decay):
    return [decay ** (n - 1 - i) for i in range(n)]


def recent_product_interest(events, decay=0.8):
    pe = [e for e in events if e.get("event_type") in EVENT_WEIGHTS]
    out = defaultdict(float)
    for e, w in zip(pe, recency_weights(len(pe), decay)):
        out[e["product_id"]] += EVENT_WEIGHTS[e["event_type"]] * w
    return dict(out)


def recent_category_interest(events, product_categories, decay=0.8):
    out = defaultdict(float)
    for p, v in recent_product_interest(events, decay).items():
        if p in product_categories:
            out[product_categories[p]] += v
    return dict(out)


def recommendation_ctr(impressions, clicks):
    return len(clicks) / len(impressions) if len(impressions) else 0.0


def ctr_by_algorithm(impressions, clicks):
    imp, clk = defaultdict(int), defaultdict(int)
    for r in impressions:
        imp[r["algorithm"]] += 1
    for r in clicks:
        clk[r["algorithm"]] += 1
    return [{"algorithm": a, "impressions": imp[a], "clicks": clk[a],
             "ctr": clk[a] / imp[a] if imp[a] else 0.0} for a in sorted(set(imp) | set(clk))]
```
