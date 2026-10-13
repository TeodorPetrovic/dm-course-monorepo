# Dan 12 — Integrated AI Marketing Platform Capstone

- lesson_id: 122
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:48.316 updated: 2026-09-05 20:00:30.934
- summary: „Sistem radi end-to-end — ali to ne znači da je 'inteligentan'. Radi zato što je svaka komponenta mala, zamenljiva i ima definisan fallback." Dvanaest dana si gradio komponente: događaje (Day 1), segmente (Day 2), predikciju (Day 3), targeting (Day 4), preporuke (Day 5/6/8/9/10) i generativni sadržaj (Day 11). Danas ih povezuješ u jedan radni sistem: tekući korisnik/sesija dobija personalizovane preporuke i AI-asistiran sadržaj iz dostupne istorije interakcija — i ti moraš da objasniš dizajn: šta je pravilo, heuristika, statistika, ML, a šta generative AI; kako sistem pada; i šta rezultat NE dokazuje. [subjects-import]


---

<!-- page_id 434 order 0 -->
## [Page] Materijal

# Dan 12 — Integrated AI Marketing Platform Capstone

> *„Sistem radi end-to-end — ali to ne znači da je 'inteligentan'. Radi zato što
> je svaka komponenta mala, zamenljiva i ima definisan fallback."*
> Dvanaest dana si gradio komponente: događaje (Day 1), segmente (Day 2),
> predikciju (Day 3), targeting (Day 4), preporuke (Day 5/6/8/9/10) i
> generativni sadržaj (Day 11). Danas ih **povezuješ u jedan radni sistem**:
> tekući korisnik/sesija dobija **personalizovane preporuke** i **AI-asistiran
> sadržaj** iz dostupne istorije interakcija — i ti moraš da **objasniš dizajn**:
> šta je pravilo, heuristika, statistika, ML, a šta generative AI; kako sistem
> pada; i šta rezultat NE dokazuje.

## Šta gradimo

**Integrisanu marketing platformu** — orkestrator (`app/services/platform.py`)
koji spaja sve module kursa u `GET /platform/modules` (diagnostics),
`GET /platform/profile/{user_id}` (marketing flywheel), `GET /platform/homepage`
(preporuke + AI sadržaj za tekućeg korisnika/sesiju) i
`GET /platform/product/{product_id}` (AI sadržaj + taksonomija sekcija), i
konzumira ga CMS: **home page personalizacija**, **product page** i
**admin/marketing dashboard**.

Ovo NIJE novi ML modul — ovo je **ML sistem kao softver**: moduli se pozivaju u
određenom redosledu, sa fallback-ovima, i svaki odgovor nosi **klasu komponente**
(taksonomija) + **fallback** + **fallback\_reason**. Radni sistem već postoji;
tvoj posao u capstone-u je da ga **razumeš, kritički oceniš i objasniš**
(lab + design write-up), i da dokažeš da umeš da označiš svaku komponentu.

Klasa komponenti (standing item — svaka komponenta se mora moći označiti):

| Komponenta | Klasa |
| --- | --- |
| `MODULE_REGISTRY` | **data structure** (manifest arhitekture) |
| `module_status` | **diagnostics** (koji modul je dostupan i zašto) |
| `profile_for_user` | **orchestration** (flywheel: segment → verovatnoća → target) |
| `homepage_payload` | **orchestration** (preporuke + AI sadržaj za tekuću sesiju) |
| Manual RFM bucket (Day 2) | **rule / heuristic** |
| K-Means segment (Day 2) | **ML** (unsupervised — naučeni centroidi) |
| Majority-class baseline (Day 3) | **statistical** (merenje, nema modela) |
| Konverzija model (Day 3) | **ML** (predikcija) |
| Rule-based targeting (Day 4) | **rule / heuristic** |
| Popularity (Day 5) | **statistical** (težinski zbir) |
| TF-IDF content (Day 5) | **statistical** (težine reči + kosinus) |
| Collaborative item-item (Day 6) | **statistical** (sličnost, nema naučenih parametara) |
| Evaluacija (Day 7) | **statistical / evaluation protocol** |
| Hybrid pipeline (Day 8) | **rule / heuristic** (merge težine = ručne!) |
| Session-aware recs (Day 9) | **rule / heuristic** (recency-weighted) |
| CTR (Day 9) | **statistical** (merenje) |
| Embeddings / semantic (Day 10) | **ML** (naučena reprezentacija) |
| LLM generacija (Day 11) | **generative AI** |
| Template SEO (Day 11) | **rule / heuristic** (baseline) |

## Application requirement

**Home page** („Main Page" je bio prazan) sada je **personalizovan**: za demo
korisnika i tekuću sesiju prikazuje AI-asistiran hero sadržaj (Day 11),
profil (segment/verovatnoća/RFM/targeting hint), „Recommended for You"
(Day 8 hybrid) i „Based on Your Session" (Day 9) — i **loguje impresije/klikove**
u dm-ml (CTR dashboard). **Product page** dobija „Platform (Day 12)" sekciju:
AI-asistiran opis (Day 11) + taksonomiju sekcija koje već renderuje
(content/collab/session/semantic). **Admin** dobija **/admin/marketing**
dashboard: module status (označi komponente), profil lookup, product payload i
vezu na evaluaciju.

Svaki odgovor nosi **`module_class`** — student može da vidi *šta je šta* na
samom ekranu. To je acceptance: „the student can explain which component is a
rule/heuristic/statistical/ML/generative-AI system".

## Ciljevi učenja

Do kraja dana treba da:

* **inspect-ujete postojeće komponente** (Day 1–11) i odlučite koje su
  **potrebne** za integrisani sistem (ne moraju sve!);
* **povežete module** kroz orkestrator: profil → preporuke → AI sadržaj →
  evaluacija, sa **definisanim redosledom** (flywheel);
* **izložite endpoint-e** (`/platform/*`) i **konzumirate ih iz CMS-a**
  (home page, product page, admin);
* **logujete recommendation događaje** (impresije/klikovi → CTR dashboard);
* **evaluirate outpute** (CTR summary u homepage-u; pun report na
  `/analytics/recommendations`);
* **obradite failure cases** (nepoznat korisnik, prazna istorija, netreniran
  model, LLM down, bez embeddinga, missing file) — svaki sa fallback-om;
* **objasnite dizajn** u design write-up-u: arhitekturu, odluke, trade-off-ove,
  i **iskreno interpretirate** šta sistem dokazuje a šta ne.

## Preduslovi

* **Svi dani 1–11** — ovo je capstone; svaka komponenta je već izgrađena.
* FastAPI/Pydantic (Day 3–4), recommenderi (Day 5–10), `AIService` (Day 11).
* Seeded dataset (Day 1–11) — `events.csv`, `products_text.csv`,
  `interactions.csv`, `embeddings.npz`; trenirani `app/models/` (segment +
  konverzija) ako želiš ML put (inače `untrained_model` fallback).

## Teorija

### ML sistemi kao softver

Do sada si gradio **komponente**. Capstone je o **sistemu**: komponente u
aplikaciji imaju uloge koje ML „čistije" ne modelira — *retrieval* (jeftino,
recall-orijentisano), *scoring/ranking*, *business rules*, *fallback*,
*logovanje*, *monitoring*. Isti modul može biti najbolji na svom inputu, a
najgori kad je pozvan u pogrešnom trenutku. Zato Day 12 postavlja **sistemska
pitanja**:

* **Koji redosled?** — profil (segment/verovatnoća) pre nego što generišeš
  hero sadržaj, jer mu treba segment. Preporuke posle profila, jer im treba
  istorija. Evaluacija na kraju (meri output).
* **Koje module pozivati?** — home page ne mora da pozove sve; npr.
  **semantic** koristimo samo za top preporuku (featured). Svaki poziv ima
  cenu (latencija) i rizik (pad) — manje je više.
* **Kako padati?** — svaki modul ima fallback, a platforma **nikad ne padne u
  celini**: ako jedan modul pukne, ostali rade.

### Marketing flywheel (data → segment → predict → target → recommend → generate → measure)

```
Day 1 events ──► Day 2 segment ──► Day 3 p(buy) ──► Day 4 targeting ──► Day 8/9 preporuke ──► Day 11 sadržaj ──► Day 7/9 evaluacija
     ▲                                                                                                             │
     └────────────────────────────────── feedback loop (impresije/klikovi) ────────────────────────────────────────┘
```

Flywheel je **povratna petlja**: događaji grade profil, profil vodi do
preporuka/sadržaja, a preporuke generišu nove događaje (impresije/klikovi) koji
vraćaju u početak. Day 9 feedback loop (logovanje + CTR) je ono što petlju
zatvara — bez njega sistem ne zna da li radi.

### Orchestration i fallback na sistemskom nivou

`homepage_payload` poziva module **oprezno** — svaki poziv je u `try/except` i
vraća labeled fallback:

```
GET /platform/homepage?user_id=395&session_id=session_005246
  ├─ profile_for_user
  │    ├─ segment (Day 2 ML)   ── pad/bez istorije ──► unsegmented (no_history / untrained_model)
  │    ├─ conversion (Day 3 ML) ── pad/bez istorije ──► base_rate (no_history / untrained_model)
  │    └─ RFM (Day 2 rule)      ── bez istorije ──► bucket=None (no_history)
  ├─ hero (Day 11 genAI)        ── LLM down ──► template (source=template, model_unavailable)
  ├─ recs (Day 8 hybrid)        ── nepoznat korisnik ──► popularity (unknown_user)
  ├─ session (Day 9)            ── bez signala ──► popularity (no_session_signal)
  ├─ semantic (Day 10)          ── bez embeddinga ──► popularity (no_embedding)
  └─ evaluation_summary (Day 9 CTR) ── 0 impresija ──► ctr=0.0
```

Svaki blok u odgovoru nosi `module_class` + `fallback` + `fallback_reason` —
to je *jedini* način da sistem bude predvidljiv i da se objasni.

## API

### `GET /platform/modules`

Manifest arhitekture + live status. Primer (`curl` kroz Nitro proxy
`/ml/platform/modules`):

```
curl -s http://127.0.0.1:3001/platform/modules
```

```
{
  "modules": [
    {"id": "hybrid", "class": "rule / heuristic",
     "day": 8, "endpoint": "GET /recommendations/{user_id}",
     "fallback": "nepoznat korisnik -> popularity (unknown_user); merge težine su heuristika",
     "available": true}
  ],
  "summary": {"total": 18, "available": 17, "unavailable": 1},
  "note": "available=False znači da modul pada na svoj fallback — ne da platforma ne radi."
}
```

`generative_ai` je obično `available=false` (nema LLM providera u default
okruženju) — i to je OK: fail-safe vraća template.

### `GET /platform/profile/{user_id}`

Marketing flywheel profil: segment (Day 2), p(buy) (Day 3), RFM (Day 2 rule),
istorija (Day 1) i targeting hint (Day 4 rule). **Nepoznat korisnik → 200 sa
fallback-om** (NIKAD 404):

```
{
  "user_id": 999999,
  "segment": {"label": "unsegmented", "fallback": true, "fallback_reason": "no_history", "module_class": "ML (prediction / learned representation)"},
  "conversion": {"probability": 0.0632, "base_rate": 0.0632, "fallback": true, "fallback_reason": "no_history", "module_class": "ML (prediction / learned representation)"},
  "rfm": {"bucket": null, "fallback": true, "fallback_reason": "no_history", "module_class": "rule / heuristic"},
  "history": {"n_events": 0, "n_purchases": 0, "top_categories": [], "module_class": "statistical"},
  "targeting_hint": {"reason": "nema istorije -> popularity onboarding", "module_class": "rule / heuristic"}
}
```

### `GET /platform/homepage?user_id=…&session_id=…&limit=…`

Integrisana početna strana. Svaki blok nosi `module_class` + `fallback`:

```
{
  "user_id": 395, "session_id": "session_005246",
  "profile": { "...": "vidi /platform/profile" },
  "hero": {"content": "Welcome back. Cilj: Recommend products for segment segment_2. …",
           "kind": "campaign_copy", "source": "template", "fallback": true,
           "fallback_reason": "model_unavailable", "module_class": "generative AI"},
  "recommendations": {"user_id": 395, "method": "hybrid", "fallback": false, "returned": 5,
      "recommendations": [{"product_id": 50, "name": "Biography Essential 819", "category_id": 3,
                           "price": 23.99, "score": 0.520322, "sources": ["category", "collaborative", "content"]}, "..."],
      "merge_weights": {"popularity": 0.2, "category": 0.3, "content": 0.3, "collaborative": 0.2},
      "module_class": "rule / heuristic", "...": "..."},
  "session_recommendations": {"session_id": "session_005246", "method": "session", "fallback": false,
                              "returned": 5, "excluded_seen": 12, "module_class": "rule / heuristic", "...": "..."},
  "semantic": {"product_id": 50, "method": "semantic", "fallback": false, "returned": 5, "recommendations": ["..."], "...": "..."},
  "featured_content": {"kind": "product_description", "source": "template", "fallback": true,
                       "content": "Biography Essential 819 iz kategorije Books. …", "...": "..."},
  "evaluation_summary": {"available": true, "overall": {"impressions": 61530, "clicks": 1427, "ctr": 0.0232}, "module_class": "statistical"},
  "modules_used": [{"id": "events", "name": "Event tracking & analytics (Day 1)", "class": "data pipeline"}, "..."]
}
```

(Primer posle `POST /segments/train` i `POST /models/conversion/train`; `"..."` = skraćeno.)

### `GET /platform/product/{product_id}`

AI-asistiran opis/SEO (Day 11) + taksonomija sekcija koje CMS renderuje
(content/collab/session/semantic). Nepoznat proizvod → `product: null`,
AI polja `null` (fallback).

## Failure handling (deo kursa)

| Scenario | Modul | Odgovor |
| --- | --- | --- |
| Nepoznat korisnik | segment, konverzija | `unsegmented` + `base_rate` (NIKAD 404) |
| Sesija bez signala | session | popularity (`no_session_signal`) |
| Netreniran model | segment/konverzija | `untrained_model` fallback |
| LLM nedostupan | generative\_ai | template (`source="template"`) |
| LLM output nevalidan | generative\_ai | template (`invalid_llm_output`) |
| Proizvod bez embeddinga | semantic | popularity (`no_embedding`) |
| Nema events.csv | svi zavisni | `available=false` u `/platform/modules` |
| 0 impresija | ctr | `ctr=0.0` (zero-division) |

Ključna stvar: **`available=false` ≠ platforma ne radi**. To je ulaz u fallback
lanac. NIJEDAN `/platform/*` endpoint ne vraća `404` za nepoznatog korisnika i
NIJEDAN ne ruši ceo zahtev kad jedan modul padne.

## Evaluacija (kako znamo da je dobro)

* **Sistem radi end-to-end** — `GET /platform/homepage` vraća preporuke + AI
  sadržaj za tekućeg korisnika/sesiju; `curl` i demo (`examples/demo_platform.py`)
  dokazuju; snapshot je u `Day 12/data/`.
* **Student može da označi svaku komponentu** — `module_class` u svakom bloku;
  `GET /platform/modules` = manifest; lab testira `classify` (taksonomija).
* **Evaluacija preporuka prisutna** — `evaluation_summary` (CTR) u homepage-u;
  pun report (P@K/R@K/NDCG, hybrid vs single-source) na `/analytics/*`.
* **Failure cases obrađeni** — svaki scenario iz tabele ima `fallback` +
  `fallback_reason` + `module_class`; test u `app/tests/test_platform.py`
  (registry = 18 modula, profil, homepage sa hero fallback-om, product page, 404 za
  nepoznat proizvod) + Day 12 lab testovi.
* **Design write-up** — `Day 12/lab/design-writeup-template.md` + rubric
  (25/25/20/15/15).
* **Full dm-ml suite prođe** — `.venv/bin/pytest app/tests` (9 testova, uključujući `app/tests/test_platform.py`); `scripts/run_all.sh` pokreće sve (47 provera).

## Česti bugovi

* **Pozivanje svih modula bez pitanja „da li mi treba"** — home page ne treba
  da pozove svaki modul; svaki poziv ima cenu (latencija) i rizik (pad).
  Rešenje: orkestrator bira; npr. semantic samo za top preporuku.
* **Redosled koji stvara cirkularnu zavisnost** — hero pre nego što profil
  postoji ne može da se personalizuje. Rešenje: profil → sadržaj.
* **Tihi pad modula** — modul pukne, a korisnik vidi prazan blok. Rešenje:
  svaki poziv je u `try/except` i vraća `fallback` + `fallback_reason` +
  `module_class` (nikad tiho `[]`).
* **Fallback koji je i sam pad** — npr. „ne znam, vrati mi ništa". Rešenje:
  fallback je UVEK definisan baseline (popularity, template, base\_rate) —
  ne prazan odgovor.
* **`available=false` shvaćen kao „sistem je pokvaren"** — to je diagnostics:
  modul pada na svoj fallback, platforma radi.
* **Tretiranje evaluacije kao presude** — CTR/P@K na sintetičkom datasetu su
  *sočivo*, ne *presuda*; težine hybrida su ručne (heuristika), ne naučene.
* **„Inteligencija" bez dekompozicije** — opisivati sistem kao „AI" a ne znati
  koja je komponenta pravilo, statistika, ML ili generative AI. Day 12 je
  upravo o ovoj dekompoziciji.

## Šta rezultat NE dokazuje

* **Radni sistem nije dokaz poslovne vrednosti.** Sve metrike (CTR, P@K) su
  računate na **sintetičkom datasetu** — sistem koji radi end-to-end u kursu
  ne garantuje iste odluke na realnom saobraćaju.
* **„Inteligencija" je kompozicija, ne jedan model.** Sistem je lanac
  pravila, heuristika, statistike, ML-a i generative AI-ja. Hybrid „pobeda" nad
  pojedinačnim izvorima (Day 8) nije dokaz da su **merge težine naučene** —
  one su ručno birane (0.2/0.3/0.3/0.2).
* **AI sadržaj može biti fluentan i netačan.** `hero` sa `source="template"`
  je fail-safe, ne dokaz da je LLM „najbolji". Validacija (Day 11) proverava
  strukturu i ograničenja, **ne istinitost**.
* **CTR razlika nije A/B rezultat.** Day 9 pravi *prikupljanje podataka* za
  eksperiment, ne statistički potvrđen zaključak.
* **`module_class` je klasifikacija, ne ocena kvaliteta.** „ML" znači da je
  komponenta naučila iz podataka — ne da je nužno bolja od pravilom baziranog
  baseline-a (često je obrnuto na malom datasetu).

## Vežbe

1. **Uradi lab** — `Day 12/lab/`: `starter.py` (`classify`, `fallback_for`,
   `select_module`) + `test_lab.py`, pa napiši design write-up po
   `design-writeup-template.md` (rubric: 25/25/20/15/15).
2. **Pokreni sistem i generiši snapshot** — `python -m app.data.generate_platform`
   pa uporedi `Day 12/data/homepage-snapshot.json` sa svojim `curl` pozivom.
3. **Promeni redosled orkestracije** — u `homepage_payload` pozovi session pre
   hybrid-a; šta se promeni u hero/profilu? (Dokumentuj u write-up-u.)
4. **Obriši `app/models/`** pa pozovi `/platform/profile/395` — snimi
   `untrained_model` fallback. (Posle toga ponovo treniraj ako želiš ML put.)
5. **Dodaj evaluacioni blok u homepage** — posluži keširani P@K report (Day 7)
   u `evaluation_summary` ako je generisan; kako se to ponaša kad nije?
6. **Dodaj novi modul u `MODULE_REGISTRY`** (npr. „email campaign") sa
   fallback-om — i testiraj da `module_status` broji 19.
7. **Zabeleži CTR pre i posle** kliktanja na home page — da li impresije/klikovi
   menjaju `evaluation_summary.overall.ctr`? (feedback loop, Day 9.)
8. **Regeneriši snapshot sa LLM-om** — `AI_PROVIDER=external` (ili local sa
   keširanim modelom) + `generate_platform`; uporedi `hero.source` u
   `metadata.json` summary sa default uzorkom.

## Sažetak

Povezao si sve module kursa u **integrisanu marketing platformu**: orkestrator
(`app/services/platform.py`) koji za tekućeg korisnika/sesiju vraća
personalizovane preporuke (Day 8/9) i AI-asistiran sadržaj (Day 11), izlaže
`/platform/modules`, `/platform/profile/{user_id}`, `/platform/homepage` i
`/platform/product/{product_id}`, a CMS ih konzumira (home page personalizacija,
product page, admin/marketing dashboard). Svaki blok nosi **`module_class`**
(taksonomija: pravilo/heuristika/statistika/ML/generative AI) i **fallback**
(failure handling: nepoznat korisnik, netreniran model, LLM down, bez
embeddinga, missing file). Evaluacija je prisutna (CTR summary + pun report), a
snapshot (`Day 12/data/`) i demo dokazuju da sistem radi end-to-end. Centralna
lekcija: *radni sistem je kompozicija malih, zamenljivih komponenti sa
definisanim fallback-ovima — „inteligencija" mora da se dekomponuje i iskreno
interpretira, jer metrike su dataset-specific a težine heuristike*.

---

<!-- page_id 435 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/homepage-snapshot.json

```
{
  "snapshots": [
    {
      "user_id": 395,
      "session_id": "session_005246",
      "hero": {
        "content": "Welcome back. Cilj: Recommend products for segment segment_2. Stvoreno za publiku: segment_2. Iskoristite priliku dok traje ponuda!",
        "kind": "campaign_copy",
        "source": "template",
        "fallback": true,
        "fallback_reason": "model_unavailable",
        "module_class": "generative AI"
      },
      "recommendations": [
        50,
        52,
        127,
        133,
        90
      ],
      "evaluation_summary": {
        "available": true,
        "overall": {
          "impressions": 61530,
          "clicks": 1427,
          "ctr": 0.0232
        },
        "module_class": "statistical"
      }
    },
    {
      "user_id": 1465,
      "session_id": "session_001403",
      "hero": {
        "content": "Welcome back. Cilj: Recommend products for segment segment_3. Stvoreno za publiku: segment_3. Iskoristite priliku dok traje ponuda!",
        "kind": "campaign_copy",
        "source": "template",
        "fallback": true,
        "fallback_reason": "model_unavailable",
        "module_class": "generative AI"
      },
      "recommendations": [
        30,
        41,
        110,
        76,
        111
      ],
      "evaluation_summary": {
        "available": true,
        "overall": {
          "impressions": 61530,
          "clicks": 1427,
          "ctr": 0.0232
        },
        "module_class": "statistical"
      }
    }
  ]
}
```

### data/metadata.json

```
{
  "dataset": "dm_platform_v1",
  "description": "Integrated Marketing Platform capstone snapshot (Day 12). module-registry.json = manifest arhitekture (klasa + fallback + available status svakog modula). homepage-snapshot.json = stvarni integrisani payload (profil + preporuke + AI sadržaj + evaluacija summary) za demo korisnike/sesije. Reference, ne duplira: izvori su Day 1–11 seeded podaci.",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "products": "Day 5/data/products_text.csv",
    "interactions": "Day 6/data/interactions.csv",
    "embeddings": "Day 10/data/embeddings.npz",
    "models": "app/models/ (segment + conversion, runtime)",
    "service": "app.services.platform.IntegratedPlatformService"
  },
  "parameters": {
    "users": [
      395,
      1465
    ],
    "sessions": [
      "session_005246",
      "session_001403"
    ],
    "limit": 5
  },
  "counts": {
    "n_modules": 18,
    "n_available": 17,
    "n_unavailable": 1,
    "n_snapshots": 2
  },
  "hero_source_note": "hero['source'] == 'template' znači da LLM nije bio dostupan na ovom okruženju (fail-safe) — ne da je template 'pravi' odgovor. Uzorak ovog pokretanja: ['template', 'template'].",
  "summary": {
    "modules": [
      {
        "id": "events",
        "class": "data pipeline",
        "available": true,
        "fallback": "— (sve kasnije zavisi od ovoga)"
      },
      {
        "id": "rfm",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "korisnik bez istorije -> bucket izostavljen (no_history)"
      },
      {
        "id": "kmeans_segmentation",
        "class": "ML (prediction / learned representation)",
        "available": true,
        "fallback": "netreniran model -> unsegmented (untrained_model); bez istorije -> unsegmented (no_history)"
      },
      {
        "id": "majority_baseline",
        "class": "statistical",
        "available": true,
        "fallback": "— (baseline uvek postoji)"
      },
      {
        "id": "conversion_model",
        "class": "ML (prediction / learned representation)",
        "available": true,
        "fallback": "netreniran model -> base_rate (untrained_model); bez istorije -> base_rate (no_history)"
      },
      {
        "id": "rule_targeting",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "— (pravila uvek rade)"
      },
      {
        "id": "ml_targeting",
        "class": "ML (prediction / learned representation)",
        "available": true,
        "fallback": "netrenirani modeli -> rule-based publika (untrained_model)"
      },
      {
        "id": "popularity",
        "class": "statistical",
        "available": true,
        "fallback": "— (baseline uvek radi)"
      },
      {
        "id": "content_tfidf",
        "class": "statistical",
        "available": true,
        "fallback": "cold-start -> popularity (no_signal)"
      },
      {
        "id": "template_text",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "— (deterministički baseline)"
      },
      {
        "id": "collaborative",
        "class": "statistical",
        "available": true,
        "fallback": "cold-start -> popularity (unknown_product / no_interactions)"
      },
      {
        "id": "evaluation",
        "class": "statistical / evaluation protocol",
        "available": true,
        "fallback": "nema fajlova -> 503 (koji generator da pokrene)"
      },
      {
        "id": "hybrid",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "nepoznat korisnik -> popularity (unknown_user); merge težine su heuristika, ne naučen odgovor"
      },
      {
        "id": "session",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "sesija bez signala -> popularity (no_session_signal)"
      },
      {
        "id": "ctr",
        "class": "statistical",
        "available": true,
        "fallback": "0 impresija -> ctr=0.0 (zero-division)"
      },
      {
        "id": "embeddings",
        "class": "ML (prediction / learned representation)",
        "available": true,
        "fallback": "embedder nedostupan -> keyword; proizvod bez embeddinga -> popularity (no_embedding)"
      },
      {
        "id": "generative_ai",
        "class": "generative AI",
        "available": false,
        "fallback": "provider nedostupan / nevalidan output -> template (model_unavailable / invalid_llm_output)"
      },
      {
        "id": "seo_template",
        "class": "rule / heuristic",
        "available": true,
        "fallback": "— (struktura garantovana kodom)"
      }
    ]
  },
  "created": "2026-08-19",
  "reproducibility_note": "Deterministički za dati environment: isti seeded podaci + isti demo korisnici + isti AI_PROVIDER -> isti fajlovi. Hero source zavisi od toga da li je LLM konfigurisan (local/external).",
  "manifest": {
    "sha256": {
      "module-registry.json": "b85a2d5f67d603b23811a74ba5aa8ed72c04fc590c0c9f8008b267bd85bd9745",
      "homepage-snapshot.json": "050eee77e2c6fb8ef307b154cea8a550320179c15097d899108983f815186f0b"
    }
  }
}
```

### data/module-registry.json

```
{
  "description": "Integrated Marketing Platform — manifest arhitekture (Day 12).",
  "modules": [
    {
      "id": "events",
      "name": "Event tracking & analytics (Day 1)",
      "class": "data pipeline",
      "day": 1,
      "endpoint": "POST /events, GET /analytics/summary",
      "data": "Day 1/data/events.csv",
      "fallback": "— (sve kasnije zavisi od ovoga)",
      "available": true
    },
    {
      "id": "rfm",
      "name": "Manual RFM buckets (Day 2)",
      "class": "rule / heuristic",
      "day": 2,
      "endpoint": "GET /segments",
      "data": "Day 1/data/events.csv + orders.csv",
      "fallback": "korisnik bez istorije -> bucket izostavljen (no_history)",
      "available": true
    },
    {
      "id": "kmeans_segmentation",
      "name": "K-Means customer segmentation (Day 2)",
      "class": "ML (prediction / learned representation)",
      "day": 2,
      "endpoint": "GET /customers/{user_id}/segment",
      "data": "app/models/segment_kmeans.joblib + meta",
      "fallback": "netreniran model -> unsegmented (untrained_model); bez istorije -> unsegmented (no_history)",
      "available": true
    },
    {
      "id": "majority_baseline",
      "name": "Majority-class conversion baseline (Day 3)",
      "class": "statistical",
      "day": 3,
      "endpoint": "GET /models/conversion/status",
      "data": "Day 3/data/training_dataset.csv",
      "fallback": "— (baseline uvek postoji)",
      "available": true
    },
    {
      "id": "conversion_model",
      "name": "Purchase probability model (Day 3)",
      "class": "ML (prediction / learned representation)",
      "day": 3,
      "endpoint": "GET /customers/{user_id}/conversion-probability",
      "data": "app/models/conversion_model.joblib + meta",
      "fallback": "netreniran model -> base_rate (untrained_model); bez istorije -> base_rate (no_history)",
      "available": true
    },
    {
      "id": "rule_targeting",
      "name": "Rule-based campaign targeting (Day 4)",
      "class": "rule / heuristic",
      "day": 4,
      "endpoint": "GET /campaigns/{campaign_id}/recommended-audience?mode=rule",
      "data": "Day 4/data/campaigns.csv",
      "fallback": "— (pravila uvek rade)",
      "available": true
    },
    {
      "id": "ml_targeting",
      "name": "ML-assisted campaign targeting (Day 4)",
      "class": "ML (prediction / learned representation)",
      "day": 4,
      "endpoint": "GET /campaigns/{campaign_id}/recommended-audience?mode=ml",
      "data": "Day 4/data/campaigns.csv + trenirani Day 2/3 modeli",
      "fallback": "netrenirani modeli -> rule-based publika (untrained_model)",
      "available": true
    },
    {
      "id": "popularity",
      "name": "Popularity baseline (Day 5)",
      "class": "statistical",
      "day": 5,
      "endpoint": "GET /recommendations/popular",
      "data": "Day 1/data/events.csv",
      "fallback": "— (baseline uvek radi)",
      "available": true
    },
    {
      "id": "content_tfidf",
      "name": "Content-based recommender (TF-IDF + cosine) (Day 5)",
      "class": "statistical",
      "day": 5,
      "endpoint": "GET /recommendations/content/{product_id}",
      "data": "Day 5/data/products_text.csv",
      "fallback": "cold-start -> popularity (no_signal)",
      "available": true
    },
    {
      "id": "template_text",
      "name": "Template product text (Day 5/11)",
      "class": "rule / heuristic",
      "day": 5,
      "endpoint": "app.services.templates",
      "data": "Day 5/data/products_text.csv",
      "fallback": "— (deterministički baseline)",
      "available": true
    },
    {
      "id": "collaborative",
      "name": "Collaborative item-item (implicit feedback) (Day 6)",
      "class": "statistical",
      "day": 6,
      "endpoint": "GET /recommendations/collaborative/{product_id}",
      "data": "Day 6/data/interactions.csv",
      "fallback": "cold-start -> popularity (unknown_product / no_interactions)",
      "available": true
    },
    {
      "id": "evaluation",
      "name": "Recommendation evaluation framework (Day 7)",
      "class": "statistical / evaluation protocol",
      "day": 7,
      "endpoint": "GET /analytics/recommendations",
      "data": "Day 1/data/events.csv + Day 5 katalog",
      "fallback": "nema fajlova -> 503 (koji generator da pokrene)",
      "available": true
    },
    {
      "id": "hybrid",
      "name": "Hybrid candidate-generation + ranking (Day 8)",
      "class": "rule / heuristic",
      "day": 8,
      "endpoint": "GET /recommendations/{user_id}",
      "data": "Day 1/data/events.csv + Day 5 katalog",
      "fallback": "nepoznat korisnik -> popularity (unknown_user); merge težine su heuristika, ne naučen odgovor",
      "available": true
    },
    {
      "id": "session",
      "name": "Session-aware recommendations (Day 9)",
      "class": "rule / heuristic",
      "day": 9,
      "endpoint": "GET /recommendations/session/{session_id}",
      "data": "Day 1/data/events.csv",
      "fallback": "sesija bez signala -> popularity (no_session_signal)",
      "available": true
    },
    {
      "id": "ctr",
      "name": "Recommendation CTR / feedback loop (Day 9)",
      "class": "statistical",
      "day": 9,
      "endpoint": "GET /analytics/recommendations/ctr",
      "data": "live event store (POST /recommendations/events)",
      "fallback": "0 impresija -> ctr=0.0 (zero-division)",
      "available": true
    },
    {
      "id": "embeddings",
      "name": "Product embeddings + semantic search (Day 10)",
      "class": "ML (prediction / learned representation)",
      "day": 10,
      "endpoint": "GET /search/semantic, GET /recommendations/semantic/{product_id}",
      "data": "Day 10/data/embeddings.npz",
      "fallback": "embedder nedostupan -> keyword; proizvod bez embeddinga -> popularity (no_embedding)",
      "available": true
    },
    {
      "id": "generative_ai",
      "name": "Structured generative-AI content (Day 11)",
      "class": "generative AI",
      "day": 11,
      "endpoint": "POST /ai/seo, POST /ai/content",
      "data": "AI_PROVIDER (local/external/auto) + template baseline",
      "fallback": "provider nedostupan / nevalidan output -> template (model_unavailable / invalid_llm_output)",
      "available": false
    },
    {
      "id": "seo_template",
      "name": "Template SEO baseline (Day 11)",
      "class": "rule / heuristic",
      "day": 11,
      "endpoint": "app.services.templates.template_seo_metadata",
      "data": "Day 5/data/products_text.csv",
      "fallback": "— (struktura garantovana kodom)",
      "available": true
    }
  ],
  "summary": {
    "total": 18,
    "available": 17,
    "unavailable": 1
  }
}
```

### data/README.md

# Day 12 podaci — Integrated Marketing Platform snapshot

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz celog
seeda (Day 1–11) — ne dupliraju ga. Kompletna dokumentacija (izvor, parametri,
counts, summary, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Oblik |
| --- | --- | --- |
| `module-registry.json` | manifest arhitekture: svaki modul sa **klasom** (rule/heuristic, statistical, ML, generative AI), endpoint-om, izvorom, fallback-om i **`available`** statusom (live diagnostics) | 18 modula |
| `homepage-snapshot.json` | stvarni `GET /platform/homepage` payload za demo korisnike/sesije (profil + preporuke + AI sadržaj + evaluacija summary) | 2–3 snapshota (limit=5) |
| `metadata.json` | izvor, parametri, counts, summary, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: celi seed Day 1–11 (`events.csv`, `products_text.csv`,
  `interactions.csv`, `embeddings.npz`, trenirani `app/models/` segment +
  konverzija) — kroz **`IntegratedPlatformService`**.
* Istu putanju koju CMS konzumira (`/platform/homepage`) — snapshot je *dokaz
  da sistem radi end-to-end*.
* Generator: `app/data/generate_platform.py`.

```
cd dm-ml
.venv/bin/python -m app.data.generate_platform   # demo korisnici 395 i 1465, sesije session_005246 i session_001403
```

Deterministički za dati environment: isti seeded podaci + isti demo korisnici +
isti `AI_PROVIDER` → isti fajlovi (sha256 u `metadata.json`).

## Šta snapshot pokazuje

**`module-registry.json`** — označi svaku komponentu (acceptance):

```
{"id": "hybrid", "class": "rule / heuristic pipeline",
 "endpoint": "GET /recommendations/{user_id}",
 "fallback": "nepoznat korisnik -> popularity (unknown_user); merge težine su heuristika",
 "available": true}
```

**`homepage-snapshot.json`** — integrisani payload: `profile` (segment +
verovatnoća + RFM + istorija), `hero` (AI sadržaj, `source` kaže put),
`recommendations` (hybrid), `session_recommendations`, `featured_content`,
`evaluation_summary` (CTR). Svaki blok nosi `module_class`.

## Šta snapshot NE dokazuje

* `hero.source == "template"` znači da LLM nije bio dostupan na okruženju gde
  je snapshot generisan (fail-safe) — ne da je template „pravi" odgovor. Sa
  konfigurisanim LLM-om (`AI_PROVIDER=external`) snapshot može da se razlikuje.
* `available: true` u registry-ju znači da su *fajlovi/modeli* prisutni, ne da
  je komponenta „dobra". Netrenirani modeli su `available: false` — i to je deo
  dizajna (fallback lanac).
* Radni sistem ≠ dokaz poslovne vrednosti: metrike su dataset-specific, a
  „inteligencija" je kompozicija pravila/heuristika/statistike/ML/generative AI
  koju moraš da označiš (to je poenta capstone-a).

### examples/demo\_platform.py

```
"""Demo: Integrated Marketing Platform (Day 12 capstone).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 12/examples/demo_platform.py"

Prikazuje:
  1) **module status** — manifest arhitekture: koji modul je dostupan, koje
     je klase (rule/heuristic/statistical/ML/generative-AI) i koji mu je
     fallback (diagnostics);
  2) **marketing flywheel profil** — segment (Day 2) + verovatnoća kupovine
     (Day 3) + RFM + istorija + targeting hint (Day 4), sa fallback-ovima za
     nepoznatog korisnika;
  3) **homepage payload** — integrisana početna strana: hero AI sadržaj
     (Day 11, template fallback ako LLM nije dostupan) + hybrid preporuke
     (Day 8) + session preporuke (Day 9) + semantic (Day 10) + CTR summary;
  4) **failure cases** — nepoznat korisnik (fallback), netreniran model
     (fallback), LLM down (template) — svaki nosi ``fallback`` +
     ``fallback_reason`` + ``module_class``;
  5) **product page** — AI-asistiran opis/SEO (Day 11) + taksonomija sekcija
     koje CMS renderuje.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.platform import IntegratedPlatformService

DEMO_USER = 395
DEMO_SESSION = "session_005246"
DEMO_PRODUCT = 22
UNKNOWN_USER = 999999


def _rec_brief(recs: dict) -> str:
    if not recs or not recs.get("recommendations"):
        return f"{recs.get('method')} (fallback={recs.get('fallback')}, {recs.get('fallback_reason')})"
    names = [r.get("name") for r in recs["recommendations"][:3]]
    return f"{recs.get('method')} n={len(recs['recommendations'])}: {', '.join(names)}"


def main() -> None:
    print("=== Day 12 — Integrated AI Marketing Platform Capstone ===\n")
    svc = IntegratedPlatformService()

    # --- 1) Module status --------------------------------------------------- #
    status = svc.module_status()
    print("[1] Module status (manifest arhitekture):")
    for m in status["modules"]:
        ok = "✓" if m["available"] else "✗ fallback"
        print(f"    {m['id']:22s} {m['class']:38s} {ok}")
    print(f"    summary: {status['summary']['available']}/{status['summary']['total']} "
          f"dostupno (generative_ai obično ✗ bez LLM providera — fail-safe)")
    print()

    # --- 2) Marketing flywheel profil --------------------------------------- #
    print("[2] Marketing flywheel profil (Day 2/3/4):")
    p = svc.profile_for_user(DEMO_USER)
    print(f"    segment : {p['segment']['label']}  (class={p['segment']['module_class']})")
    print(f"    p(buy)  : {p['conversion']['probability']:.4f}  "
          f"(class={p['conversion']['module_class']}, base_rate={p['conversion']['base_rate']:.4f})")
    print(f"    rfm     : {p['rfm']['bucket']}  (class={p['rfm']['module_class']})")
    print(f"    history : {p['history']['n_events']} događaja, "
          f"{p['history']['n_purchases']} kupovina")
    print(f"    targeting: {p['targeting_hint']['reason']}")
    print()

    # --- 3) Homepage payload (integrisani put) ------------------------------ #
    print("[3] Homepage payload (integrisana platforma):")
    hp = svc.homepage_payload(DEMO_USER, session_id=DEMO_SESSION, limit=5)
    hero = hp["hero"]
    print(f"    hero     : [{hero['source']}] fallback={hero['fallback']} "
          f"class={hero['module_class']}")
    print(f"               {hero['content'][:90]}…")
    print(f"    recs     : {_rec_brief(hp['recommendations'])}")
    print(f"    session  : {_rec_brief(hp['session_recommendations'])}")
    if hp["semantic"]:
        print(f"    semantic : n={len(hp['semantic']['recommendations'])} "
              f"class={hp['semantic']['module_class']}")
    print(f"    featured : {hp['featured_content']['kind']} "
          f"[{hp['featured_content']['source']}]")
    print(f"    ctr      : overall={hp['evaluation_summary']['overall']} "
          f"class={hp['evaluation_summary']['module_class']}")
    print(f"    modules  : {', '.join(m['id'] for m in hp['modules_used'])}")
    print()

    # --- 4) Failure cases --------------------------------------------------- #
    print("[4] Failure handling (svaki nosi fallback + reason + class):")
    unk = svc.profile_for_user(UNKNOWN_USER)
    print(f"    unknown user segment : {unk['segment']['label']} "
          f"fallback={unk['segment']['fallback']} ({unk['segment']['fallback_reason']})")
    print(f"    unknown user p(buy)  : {unk['conversion']['probability']:.4f} "
          f"(= base_rate, fallback={unk['conversion']['fallback']})")
    print(f"    hero source          : {hero['source']} "
          f"(fallback={hero['fallback']} — LLM nije dostupan -> template)")
    print()

    # --- 5) Product page ---------------------------------------------------- #
    print("[5] Product page (AI sadržaj + taksonomija sekcija):")
    pp = svc.product_page_payload(DEMO_PRODUCT)
    print(f"    product  : {pp['product']['name']}")
    print(f"    ai_desc  : [{pp['ai_description']['source']}] fallback="
          f"{pp['ai_description']['fallback']}: {pp['ai_description']['content'][:80]}…")
    print(f"    ai_seo   : {pp['ai_seo']['seo_title']}")
    for s in pp["sections"]:
        print(f"    {s['section']:26s} -> {s['module_id']:16s} ({s['class']})")
    print()

    print("API: GET /platform/modules · GET /platform/profile/{user_id} · "
          "GET /platform/homepage · GET /platform/product/{product_id}")
    print("Data: Day 12/data/module-registry.json + homepage-snapshot.json "
          "(pokreni app.data.generate_platform)")
    print("Lab: Day 12/lab — capstone brief + rubric + design write-up template")


if __name__ == "__main__":
    main()
```

### lab/design-writeup-template.md

# Design write-up — Integrated AI Marketing Platform (Day 12)

> Popuni sve sekcije. Ovo je glavni predati dokument za rubric (posebno
> **Design quality** i **Honest interpretation**). Drži se činjenica — piši o
> *svom* sistemu, ne o idealnom.

## 1. Arhitektura (dijagram + moduli)

Nacrtaj dijagram toka podataka: `events → profile → preporuke → AI sadržaj → evaluacija`, sa svakim modulom i njegovim **inputom/outputom**.

```
[npr.]
Day 1 events ──► Day 2 segment ──┐
            └──► Day 3 p(buy) ───┼──► Day 4 targeting hint ──► profile
Day 1+5 ─────► Day 8 hybrid ─────┼──► preporuke
Day 1 ───────► Day 9 session ────┤
Day 10 ──────► embeddings ───────┘
Day 11 ──────► AI content ───────► hero / featured
Day 7/8/9 ───► evaluation ───────► CTR / P@K
```

## 2. Označi svaku komponentu (taksonomija)

Za svaki modul koji tvoj sistem koristi: **klasa + baseline**.

| Modul (id) | Klasa (rule/heuristika/statistika/ML/genAI) | Baseline (s čime se poredi) | Zadatak u sistemu |
| --- | --- | --- | --- |
| `rfm` | rule / heuristic | — | profil bucket |
| `kmeans_segmentation` | ML | manual RFM (pravilo) | segment korisnika |
| `conversion_model` | ML | majority-class (statistika) | p(buy) |
| `popularity` | statistical / heuristic | — | fallback baseline |
| `content_tfidf` | statistical | keyword (Day 10) | preporuke po tekstu |
| `collaborative` | statistical / heuristic | session co-occurrence | item-item |
| `hybrid` | rule / heuristic pipeline | svaki pojedinačni izvor (Day 8) | user preporuke |
| `session` | rule / heuristic | popularity | session preporuke |
| `embeddings` | ML | TF-IDF (Day 10) | semantic |
| `generative_ai` | generative AI | template tekst (Day 11) | AI sadržaj |

## 3. Odluke i trade-off-ovi

Za svaku veliku odluku: šta si izabrao, koje alternative si odbacio i zašto.

| Odluka | Izbor | Alternative | Zašto |
| --- | --- | --- | --- |
| Redosled orkestracije (profil pre preporuka?) | … | … | … |
| Koje module poziva home page (a koje product page) | … | … | … |
| Evaluacija: CTR summary na home page-u, pun report u admin-u | … | … | … |
| Gde živi fallback (servis? CMS?) | … | … | … |
| … | … | … | … |

## 4. Failure handling

Za svaki scenario iz brief-a: koji modul puca, kako sistem reaguje, koji je
fallback, i gde si to *dokazao* (endpoint/poziv).

| Scenario | Modul koji puca | Fallback + razlog | Dokaz |
| --- | --- | --- | --- |
| Nepoznat korisnik | segment, konverzija | `unsegmented`, `base_rate` | `curl /platform/profile/999999` |
| Sesija bez signala | session | popularity `no_session_signal` | nova sesija na home page-u |
| Netreniran model | segment/konverzija | `untrained_model` | obriši `app/models/`, pa pozovi |
| LLM down | generative\_ai | template `model_unavailable` | hero `source=template` |
| Proizvod bez embeddinga | embeddings | popularity `no_embedding` | `/recommendations/semantic/{nov}` |
| Nema events.csv | svi zavisni | `available=false` | `/platform/modules` |

## 5. Evaluacija (šta meriš i zašto)

* **Šta** meriš: CTR (Day 9), P@K/R@K/NDCG (Day 7), hybrid vs single-source
  (Day 8) — ili nešto svoje.
* **Na kom pitanju**: npr. „da li je session-aware bolji od popularity za
  početnu stranu?"
* **Ograničenja**: metrike su dataset-specific; težine merge-a su ručne; CTR
  razlika nije statistički potvrđen A/B rezultat.

## 6. Šta rezultat NE dokazuje (iskrena interpretacija — obavezno)

1. **Radni sistem ≠ poslovna vrednost.** Sistem radi end-to-end, ali metrike
   (CTR, P@K) su računate na sintetičkom datasetu — ne znači da bi iste odluke
   bile dobre na realnom saobraćaju.
2. **„Inteligencija" je kompozicija, ne model.** Svaka komponenta je
   pravilo/heuristika/statistika/ML/generative AI — i mora da se označi.
   Hybrid „pobeda" nad pojedinačnim izvorima nije dokaz da je težinski blend
   naučen; težine su ručne.
3. **AI sadržaj može biti fluentAN i netačan.** Template fallback nije dokaz
   da je LLM „najbolji" — on je fail-safe. Validacija proverava strukturu, ne
   istinitost.
4. **CTR razlika nije A/B rezultat.** Day 9 pravi *prikupljanje podataka* za
   eksperiment, ne značajnosni test.
5. *(dodaj svoju)* …

## 7. Šta bi sledeće unapredio

* Naučene merge težine (ranking model, npr. LambdaMART) umesto heuristike.
* Pravi A/B test sa statističkim zaključkom.
* Online evaluacija (CTR iz live događaja) umesto offline report-a.
* Personalizacija generativnog sadržaja sa više konteksta (ne samo segment).

### lab/README.md

# Day 12 capstone — Integrated AI Marketing Platform (brief za studenta)

Ovo je **poslednji dan** i **capstone**: ne pišeš jedan novi modul, nego
**povezuješ sve module** kursa (Day 1–11) u jedan radni sistem. Rezultat je
e-commerce aplikacija u kojoj **tekući korisnik/sesija dobija personalizovane
preporuke i AI-asistiran sadržaj iz dostupne istorije interakcija**.

Radni sistem već postoji u `dm-ml/app/services/platform.py` (`/platform/*`
endpoint-i) i u CMS-u (home page personalizacija, product page, admin/marketing
dashboard). Tvoj posao u capstone-u je da **razumeš, kritički oceniš i objasniš
taj dizajn** — i da dokažeš da razumeš *šta je šta* (koja komponenta je pravilo,
heuristika, statistika, ML, generative AI) i *kako sistem pada* (failure
handling). Lab ispod je taj dokaz.

## Šta moraš da uradiš

### 1. Pokreni sistem end-to-end (acceptance: „the system runs end-to-end")

```
cd dm-ml
.venv/bin/python -m uvicorn app.main:app --port 3001        # servis
# u drugom terminalu:
.venv/bin/python -m app.data.generate_platform               # snapshot (Day 12/data)
(cd .. && dm-ml/.venv/bin/python "Day 12/examples/demo_platform.py")   # demo (iz root-a kursa)
curl -s "http://127.0.0.1:3001/platform/homepage?user_id=395&session_id=session_005246&limit=5"
```

Proveri i CMS (frontend, `dm-frontend/`): home page personalizacija,
product page (Platform sekcija), admin/marketing dashboard.

### 2. Označi svaku komponentu (acceptance: „student can label each component")

Za svaki modul u `GET /platform/modules` (i `Day 12/data/module-registry.json`)
odgovori: **pravilo/heuristika, statistika, ML, ili generative AI?** Primeri:

| Komponenta | Klasa | Zašto |
| --- | --- | --- |
| Manual RFM bucket | **rule / heuristic** | eksplicitno pravilo (bins), nema modela |
| K-Means segment | **ML** | naučeni centroidi iz podataka (unsupervised) |
| Majority-class baseline | **statistical** | merenje učestalosti klase, nema modela |
| Verovatnoća kupovine | **ML** | model (logistic regression / RF) treniran na podacima |
| Popularity | **statistical / heuristic** | težinski zbroj događaja, deterministički |
| TF-IDF content | **statistical** | težine reči iz korpusa + kosinus |
| Collaborative item-item | **statistical / heuristic** | sličnost na osnovu interakcija, nema naučenih parametara |
| Hybrid merge težine | **rule / heuristic** | ručno birane (0.2/0.3/0.3/0.2), NISU naučene |
| Session-aware recs | **rule / heuristic** | recency-weighted interes, pravila |
| CTR | **statistical** | klikovi / impresije (merenje) |
| Embeddings / semantic | **ML** | naučena reprezentacija (sentence-transformers) |
| LLM generacija | **generative AI** | model *stvara nov tekst* |
| Template SEO | **rule / heuristic** | baseline bez modela |

### 3. Pokaži evaluaciju (acceptance: „recommendation evaluation present")

* `GET /platform/homepage` vraća **CTR summary** (Day 9) u `evaluation_summary`.
* Pun report je na `GET /analytics/recommendations` (Day 7: P@K/R@K/HR@K/NDCG,
  coverage) i `GET /analytics/recommendations/hybrid` (Day 8: hybrid vs
  single-source) — admin dashboard `/admin/recommendations`.
* U design write-up-u objasni: *koju* evaluaciju si koristio, *za šta* je
  valjana i *šta ne dokazuje* (dataset-specific, heurističke težine).

### 4. Obrađi failure cases (acceptance: „failure cases are handled")

Za svaki slučaj: koji modul pada, kako, i koji je fallback? (Svaki odgovor u
`/platform/*` nosi `fallback` + `fallback_reason` + `module_class`.)

| Scenario | Šta puca | Fallback | Vidi u |
| --- | --- | --- | --- |
| Nepoznat korisnik | segment (Day 2) + konverzija (Day 3) | `unsegmented` + `base_rate` | `/platform/profile/999999` |
| Sesija bez signala | session recs (Day 9) | popularity top-N | `/platform/homepage` (nova sesija) |
| Netreniran model | segment / konverzija | `untrained_model` fallback | obriši `app/models/` pa pozovi profil |
| LLM nedostupan | generacija (Day 11) | template (source=template) | hero u homepage payload-u |
| Proizvod bez embeddinga | semantic (Day 10) | popularity (`no_embedding`) | `/recommendations/semantic/{nov}` |
| Nema events.csv | sve (Day 1 zavisnici) | modul `available=false` | `/platform/modules` |

### 5. Napiši design write-up (acceptance: „design write-up explains architecture")

Koristi `design-writeup-template.md`. Rubric: `rubric.md`.

## Dnevne vežbe (uz capstone)

1. **Uradi lab** — `starter.py` + `test_lab.py` (taksonomija + fallback +
   izbor modula za zadatak).
2. **Proširi platformu**: dodaj jedan modul u `module_status` (npr. „email
   campaign") i njegov fallback.
3. **Promeni redosled orkestracije**: šta se desi ako u `homepage_payload`
   prvo pozoveš session pa hybrid? (Različit redosled = različiti podaci za
   hero/profil.)
4. **Obriši `app/models/`** pa pozovi `/platform/profile/395` — dokumentuj
   `untrained_model` fallback u write-up-u.
5. **Dodaj evaluacioni blok** u homepage: npr. posluži `P@K` iz keširanog
   report-a (Day 7) ako je generisan, pa `evaluation_summary` nosi i njega.
6. **Zabeleži CTR pre i posle** kliktanja na home page — da li impresije/
   klikovi menjaju `evaluation_summary`? (feedback loop, Day 9.)

## Pokretanje lab-a

```
cd "Day 12/lab"
python3 -m pytest test_lab.py                          # tvoje rešenje
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # referentno
```

## Predaja (za ocenjivača)

1. `design-writeup.md` (iz `design-writeup-template.md`) — arhitektura,
   odluke, trade-off-ovi, iskrena interpretacija.
2. Snimljeni dokazi da sistem radi: `Day 12/data/` (regeneriši ako treba) +
   screenshot CMS-a (home / product / admin marketing).
3. Rubric checklist (označi gde si zadovoljio kriterijum).

### lab/starter.py

```
"""Starter za Day 12 lab — taksonomija, fallback i izbor modula (student piše).

Capstone (``dm-ml/app/services/platform.py``) već sadrži pravi integrisani
sistem. U ovom lab-u **ti pišeš čistu logiku** koja dokazuje da razumeš tri
capstone veštine, pre nego što ocenjuješ dizajn:

  1. **``classify``** — označi svaku komponentu: pravilo/heuristika,
     statistika, ML, generative AI, data pipeline, evaluacija;
  2. **``fallback_for``** — za svaki failure scenario vrati definisani fallback
     (acceptance: „failure cases are handled");
  3. **``select_module``** — za svaki marketing zadatak izaberi primarni modul
     (flywheel: data → segment → predict → target → recommend → generate).

Ne menjaš ``dm-ml`` — radiš u ovom fajlu i proveravaš rešenje sa ``test_lab.py``:

    cd "Day 12/lab"
    python3 -m pytest test_lab.py                          # tvoje rešenje
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # referentno

Fajl je samostalan (bez importa iz ``dm-ml``).
"""


# --------------------------------------------------------------------------- #
# Taksonomija komponenti (day-agnostic, ista kao u systemu)
# --------------------------------------------------------------------------- #
RULE = "rule / heuristic"
STATISTICAL = "statistical"
ML = "ML (prediction / learned representation)"
GENAI = "generative AI"
DATA_PIPELINE = "data pipeline"
EVAL = "statistical / evaluation protocol"

# Komponenta (id) -> klasa. Ovo je odgovor na „označi svaku komponentu".
TAXONOMY: dict[str, str] = {
    "events": DATA_PIPELINE,
    "rfm": RULE,
    "kmeans_segmentation": ML,
    "majority_baseline": STATISTICAL,
    "conversion_model": ML,
    "rule_targeting": RULE,
    "popularity": STATISTICAL,
    "content_tfidf": STATISTICAL,
    "template_text": RULE,
    "collaborative": STATISTICAL,
    "evaluation": EVAL,
    "hybrid": RULE,  # merge težine + pipeline su heuristika, ne naučen model
    "session": RULE,
    "ctr": STATISTICAL,
    "embeddings": ML,
    "generative_ai": GENAI,
    "seo_template": RULE,
}


# --------------------------------------------------------------------------- #
# Fallback-i (failure handling) — scenario -> fallback
# --------------------------------------------------------------------------- #
FALLBACKS: dict[str, str] = {
    # nepoznat korisnik bez istorije
    "unknown_user": "unsegmented (no_history) + base_rate p(buy)",
    # sesija bez ijednog proizvodnog događaja
    "no_session_signal": "popularity top-N (no_session_signal)",
    # segment / konverzija model nije treniran
    "untrained_model": "unsegmented (untrained_model) / base_rate (untrained_model)",
    # LLM provider nije dostupan (nema API-ja, model nije keširan)
    "model_unavailable": "template (source=template, model_unavailable)",
    # LLM output ne prođe validaciju (bounded retry iscrpljen)
    "invalid_llm_output": "template (source=template, invalid_llm_output)",
    # proizvod nema red u embedding store-u
    "no_embedding": "popularity (no_embedding)",
    # embedding model (query embedder) se ne može učitati
    "embedder_unavailable": "keyword fallback (embedder_unavailable)",
    # nov proizvod bez TF-IDF reda / bez interakcija (content/collaborative)
    "cold_start": "popularity (unknown_product / no_interactions)",
    # nema events.csv -> svi zavisni moduli su nedostupni
    "events_file_missing": "module available=false (fallback lanac)",
    # CTR nad 0 impresija
    "zero_impressions": "ctr=0.0 (zero-division handling)",
}


# --------------------------------------------------------------------------- #
# Marketing zadaci -> primarni modul (flywheel)
# --------------------------------------------------------------------------- #
TASKS: dict[str, str] = {
    "segment_user": "kmeans_segmentation",
    "predict_purchase": "conversion_model",
    "target_campaign": "rule_targeting",
    "recommend_for_user": "hybrid",
    "recommend_for_session": "session",
    "semantic_search": "embeddings",
    "generate_content": "generative_ai",
    "evaluate_recommendations": "evaluation",
}


# --------------------------------------------------------------------------- #
# 1) classify — označi komponentu
# --------------------------------------------------------------------------- #
def classify(component_id: str) -> str:
    """Vraća klasu komponente (``TAXONOMY``), npr. ``classify("rfm") -> RULE``.

    Nepoznata komponenta -> ``ValueError`` (ne vraćaj ``None`` tiho).
    Ovo je „student can label each component" iz acceptance-a.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) fallback_for — koji fallback za koji scenario
# --------------------------------------------------------------------------- #
def fallback_for(failure_code: str) -> str:
    """Vraća definisani fallback za scenario (``FALLBACKS``).

    Nepoznat scenario -> ``ValueError``. Failure handling je deo dizajna:
    svaki pad mora da ima imenovan fallback — NIKAD tiho prazno.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) select_module — izaberi modul za zadatak
# --------------------------------------------------------------------------- #
def select_module(task: str) -> str:
    """Vraća primarni modul za marketing zadatak (``TASKS``).

    Nepoznat zadatak -> ``ValueError``. Ovo je flywheel iz Day 12 teorije:
    data -> segment -> predict -> target -> recommend -> generate -> evaluate.
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
import json

REG = json.loads((Path(__file__).resolve().parents[1] / "data" / "module-registry.json").read_text())


def test_classify_matches_registry():
    for m in REG["modules"]:
        if m["id"] in lab.TAXONOMY:
            assert lab.classify(m["id"]) == m["class"], m["id"]
    assert lab.classify("rfm") == lab.RULE and lab.classify("embeddings") == lab.ML
    with pytest.raises(ValueError):
        lab.classify("nope")


def test_fallbacks_named():
    assert "popularity" in lab.fallback_for("no_session_signal")
    assert lab.fallback_for("zero_impressions").startswith("ctr=0.0")
    with pytest.raises(ValueError):
        lab.fallback_for("nope")


def test_select_module_flywheel():
    assert lab.select_module("recommend_for_user") == "hybrid"
    for t, mid in lab.TASKS.items():
        assert lab.select_module(t) in lab.TAXONOMY
    with pytest.raises(ValueError):
        lab.select_module("nope")
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 12 lab-a."""
from __future__ import annotations

from starter import (DATA_PIPELINE, EVAL, FALLBACKS, GENAI, ML, RULE, STATISTICAL, TASKS,  # noqa: F401
                     TAXONOMY)


def _lookup(table, key, what):
    if key not in table:
        raise ValueError(f"nepoznat {what}: {key!r}")
    return table[key]


def classify(component_id):
    return _lookup(TAXONOMY, component_id, "komponenta")


def fallback_for(failure_code):
    return _lookup(FALLBACKS, failure_code, "scenario")


def select_module(task):
    return _lookup(TASKS, task, "zadatak")
```
