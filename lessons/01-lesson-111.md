# Dan 1 — Praćenje događaja, analitika i sintetički generator podataka

- lesson_id: 111
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:45.785 updated: 2026-09-05 20:00:27.722
- summary: Zašto AI zahteva istorijske podatke o ponašanju — i kako da ih prikupimo, analiziramo i reprodukujemo pre nego što uopšte govorimo o modelima? [subjects-import]


---

<!-- page_id 412 order 0 -->
## [Page] Materijal

# Dan 1 — Praćenje događaja, analitika i sintetički generator podataka

> *Zašto AI zahteva istorijske podatke o ponašanju — i kako da ih prikupimo,
> analiziramo i reprodukujemo pre nego što uopšte govorimo o modelima?*

## Šta gradimo

Strukturirani sloj podataka o ponašanju posetilaca: proširena šema događaja,
`POST /events` endpoint, ponovo upotrebljive analitičke funkcije (brojevi
pregleda/korpi/kupovina, stopa konverzije, udeo po kategoriji) i
**deterministički sintetički generator** koji proizvodi korisnike, proizvode,
događaje, porudžbine i kategorije sa pet preklapajućih persona.

Sve što ovaj dan pravi, svaki naredni dan **konzumira**: feature-i (Day 2),
predikcija (Day 3), preporuke (Day 5+), evaluacija (Day 7). Ako danas nema
dobrog podatka, kasnije nema AI-ja.

## Application requirement

Kursna aplikacija je postojeći e-commerce sistem (Nuxt CMS `dm-frontend` +
FastAPI servis `dm-ml`). Da bi aplikacija postala **AI-podržana**, prvo mora
da zna šta se dešava: ko gleda šta, dodaje u korpu, kupuje, u kojoj sesiji i
kada. Bez tog zapisa ne postoje ni feature-i, ni modeli, ni preporuke.

## Ciljevi učenja

Do kraja dana treba da:

* objasnite **zašto AI traži istorijske podatke o ponašanju** (bez podataka
  nema ničega da se nauči);
* definišete **događaj, sesiju, korisnika, proizvod, vremenski žig** i kako
  se oni povezuju u jednu tabelu događaja;
* opišete **marketing funnel** (view → cart → purchase) i **stopu konverzije**
  svojim rečima;
* implementirate funkcije za kreiranje, čuvanje i upite nad događajima
  (`create_event`, `save_event`, `get_session_events`, `get_product_events`,
  `get_customer_events`);
* napišete analitičke upite (broj pregleda/korpi/kupovina po proizvodu, stopa
  konverzije, tržišni udeo po kategoriji);
* pokrenete **sintetički generator podataka** i objasnite zašto je fiksni seed
  + preklapajuće persone bitan za reproduktivnost i naredne dane;
* razlikujete **podatak → analitiku → ML** i znate šta ovaj dan *ne* dokazuje.

## Preduslovi

Osnovni Python (funkcije, moduli, DataFrame-i), HTTP/JSON, postojeći oblik
događaja u `dm-frontend` (`trackEvent.ts`, `server/api/event/track.post.ts`)
i FastAPI aplikacija u `dm-ml`.

## Postojeći sistem (šta nasleđujemo)

Audit nalazi da je trenutno praćenje **minimalno** — `{event_type, product_id, user_session}` [A §C.1]: nema identiteta korisnika, nema cene/količine/izvora,
nema search događaja, nema događaja preporuka, timestamp se ne normalizuje.
Baza je udaljena i nepopunjena, pa kurs ne može da računa na žive podatke
[A §B.5]. Današnji zadatak: **proširiti** (ne brisati) šemu, popuniti je
reproduktivnim sintetičkim podacima i napisati analitiku.

## Arhitektura

```
dm-frontend (Nuxt, :3000)                dm-ml (FastAPI, :3001)
  pages (product/category/shop)            app/data/events.py      (čuvanje + upiti)
    └─ trackEvent(payload) ───────────►    app/data/analytics.py   (brojevi, konverzija, udeo)
        POST /api/event/track               app/data/generate_dataset.py (jedini izvor istine)
                                            app/api/event_routes.py (POST /events, GET /analytics/...)
    Nitro proxy /ml/** ───────────────►     app/main.py
```

Podaci žive u `Day 1/data/` (`customers.csv`, `products.csv`, `events.csv`,
`orders.csv`, `categories.csv` + `metadata.json`). Kursni moduli u `dm-ml/`
čitaju taj direktorijum (path se podešava preko `DM_DATA_DIR`).

## Korišćeni podaci

Sintetički dataset (seed `42`): 3000 korisnika, 252 proizvoda u 12 kategorija,
januar 2026, 183.468 događaja, 15.361 sesija, 893 porudžbine (1.045 stavki). Pet persona sa preklapanjem — vidi
`data/README.md` i `metadata.json`.

## AI-ML koncept

Danas **nema ML-a**. Ovo je namerno i ključno za celu godinu:

* **Događaj** je sirovi zapis (ko, šta, kada, gde). To je *podatak*.
* **Analitika** je agregacija podataka (levak, konverzija, udeo). To je
  *deskriptivna statistika*.
* **ML** (Day 2+) uči parametre iz istorije (segmentacija, predikcija,
  preporuke). *Ne može bez prva dva.*

Terminologija levka (Kaushik, Web Analytics 2.0): posetilac dolazi → pregleda
proizvod → dodaje u korpu → kupuje. Svaki korak gubi deo korisnika. **Stopa
konverzije** = sesije sa kupovinom / sve sesije — jedan broj koji opisuje
*dataset*, ne pojedinačnog korisnika.

## Implementacija (koraci)

Moduli su u `dm-ml/app/data/`; radni tok ispod.

### Korak 1 — Šema događaja

`events.py → create_event` i `EventStore`. Svako polje ima **dokumentovan
razlog** (data minimization — ne skupljamo bez razloga):

| Polje | Zašto postoji |
| --- | --- |
| `user_id` | identitet za RFM/segmentaciju (Day 2) |
| `user_session` | sesija za funnel i feature-e po sesiji |
| `product_id` | vezani proizvod (`NA` za search/category\_view) |
| `category_id` | vezana kategorija |
| `price` | AOV i osetljivost na cenu |
| `quantity` | količina u korpi/kupovini |
| `source` | koja stranica je emitovala događaj |
| `timestamp` | normalizovan `YYYY-MM-DD HH:MM:SS` |
| `recommendation_source` / `recommendation_position` | CTR i evaluacija preporuka (Day 9/12) |

`create_event` validira: poznat `event_type`, proizvodni tip zahteva
`product_id`, `quantity >= 1`.

### Korak 2 — Čuvanje i upiti

`EventStore.save_event` dodeljuje `event_id` i (opciono) dopisuje u CSV fajl
(`live_path`) — **round-trip ugovor**: ono što sačuvaš moraš da nađeš kroz
upit. Upiti: `get_session_events`, `get_product_events`, `get_customer_events`.

### Korak 3 — Analitika

`analytics.py`: `get_product_view_count`, `get_cart_count`,
`get_purchase_count`, `calculate_funnel_counts`, `calculate_conversion_rate`,
`share_by_category`. Konverzija je definisana na nivou **sesije** (ne
proizvoda) i eksplicitno vraća `0.0` na praznom skupu — bez tihog `None`.

### Korak 4 — Sintetički generator

`generate_dataset.py` je **jedini izvor istine** za podatke kursa. Pokretanje:

```
cd dm-ml
.venv/bin/python -m app.data.generate_dataset --seed 42
```

Determinizam: `numpy.random.default_rng(seed)` po podskupovima (seed+0/1/2),
fiksan redosled kolona, nullable `Int64` tipovi. Dva pokretanja sa istim
seed-om → identični bajtovi (dokazano `metadata.json → manifest.sha256`).

Persone: `high_value` (česti kupci), `price_sensitive` (jeftino, puno
pregleda), `category_focused` (1–2 kategorije), `occasional` (retke sesije),
`new_user` (tek došao). Preklapanje: 15% „aspirativnih" pregleda van cene,
sekundarna persona (p=0.35) koja se koristi u sesijama (p=0.25), per-korisnički
jitter.

### Korak 5 — API

`app/api/event_routes.py` + `app/main.py` izlažu endpoint-e ispod. Failure
handling je sadržaj: nepoznat proizvod → `404`, nevalidan događaj → `422`,
prazan store → `503`, greška store-a → `500`. Nikad tihi `[]`/`None`.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `create_event(...)` | kreira i validira događaj (dict) | `app/data/events.py` |
| `EventStore.save_event(event)` | dodeljuje `event_id`, čuva, vraća | `app/data/events.py` |
| `get_session_events / get_product_events / get_customer_events` | upiti | `app/data/events.py` |
| `get_product_view_count / get_cart_count / get_purchase_count` | brojevi po proizvodu | `app/data/analytics.py` |
| `calculate_funnel_counts` | levak: views/carts/purchases/sessions | `app/data/analytics.py` |
| `calculate_conversion_rate` | sesije sa kupovinom / sve sesije | `app/data/analytics.py` |
| `share_by_category(events, products, metric)` | tržišni udeo kategorija | `app/data/analytics.py` |
| `average_order_value(orders)` | prosečna porudžbina (vežba) | `app/data/analytics.py` |
| `generate_dataset(seed=42, ...)` | celokupan dataset + metadata sidecar | `app/data/generate_dataset.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `POST /events` | 201 + sačuvan događaj (sa `event_id`) |
| `GET /analytics/products/{id}/views` | `{product_id, views}` |
| `GET /analytics/products/{id}/carts` | `{product_id, carts}` |
| `GET /analytics/products/{id}/purchases` | `{product_id, purchases}` |
| `GET /analytics/products/{id}` | sva tri broja |
| `GET /analytics/conversion-rate` | levak + `conversion_rate` |
| `GET /analytics/share-by-category?metric=view|cart|purchase` | udeo po kategoriji |
| `GET /recommendations/{id}` | **rule-based placeholder** (business rule, ne ML) — čuva CMS product page. Od Day 8 ova putanja postaje *user-based* hibrid; placeholder se seli na `GET /recommendations/legacy/{product_id}` |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

## CMS integracija

U radnom `dm-frontend/` kopiraju se (ne prepravljaju) samo integracione tačke:

* `server/database/schemas/event.schema.ts` — proširena tabela (nova polja).
* `server/api/event/track.post.ts` — prihvata ceo event set, validira, vraća
  sačuvan događaj, eksplicitne greške.
* `app/composables/trackEvent.ts` — `trackEvent(payload)` + pomagači za svih
  8 tipova događaja.
* `app/pages/product/[slug].vue` — `product_view`, `add_to_cart`, `purchase`,
  `recommendation_impression`/`click`; otporan na nedostupne preporuke.
* `app/pages/category/[slug].vue` — `category_view` + `product_view`
  (source=`category_page`).
* `app/pages/shop/index.vue` — `product_view` (source=`shop`) + `add_to_cart`.

Frontend (`apps/frontend`) radi nad lokalnom MariaDB šemom (`db/schema.sql`) u kojoj
`product` ima kolonu `price`, pa se cena šalje uz događaj. Preostala rupa: nema cart stranice
(`remove_from_cart` ostaje u šemi/generatoru). Search stranica dolazi na Day 10.

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
.venv/bin/python -m app.data.verify_dataset
cd "../Day 1/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno: `calculate_conversion_rate` na poznatim vrednostima (fixture 3
sesije → 1/3), **round-trip** (`save_event` → `get_customer_events`), upiti po
sesiji/proizvodu/korisniku, perzistencija u `live_path`, API sloj (`POST /events` 201/422, analitika, 404 nepoznat proizvod, 503 prazan store),
lab harness (Day 1/lab).

## Experiment (šta vi radite)

1. Regeneriši dataset: `python -m app.data.generate_dataset --seed 42`.
2. Proveri byte-for-byte: pokreni opet i uporedi sha256.
3. Pokreni demo: `python "Day 1/examples/demo_events.py"` i
   `python "Day 1/examples/demo_analytics.py"`.
4. Pošalji nekoliko događaja na `POST /events` i vidi kako se menjaju
   `views`/`sessions` u analitici.
5. Promeni seed (npr. `--seed 7`) i primeti: isti kod radi, ali raspored događaja je
   drugačiji — i zato **svi kasniji dani koriste seed 42**. Agregati (levak, broj
   porudžbina, prihod) se pomeraju u okviru realnih opsega (konverzija ≈ 5–6 %, napuštene
   korpe ≈ 65–70 %); `verify_dataset` proverava sha256 samo za seed 42.

## Comparison (baseline ugao)

Danas nema „AI vs baseline" — ali postavljamo pravilo koje važi cele godine:
**svaki kasniji AI modul se poredi sa prostijim baseline-om.** Ono što danas
gradimo je *tlo* za te poređenja. Jedino poređenje danas: rule-based
`/recommendations` (business rule) koje Day 5 zamenjuje baseline-ima
(popularity/category) pa tek onda ML-om. Klasa svake komponente je eksplicitna:
danas je sve **rule / statistical method**, nijedna nije ML.

## Evaluacija (kako znamo da je dobro)

* Generator: dva pokretanja → identični sha256 (`manifest` u `metadata.json`).
* Analitika: proverena protiv poznatih vrednosti u testovima (fixture) i protiv
  unutrašnje konzistentnosti dataseta (`verify_dataset.py`: levak monotono
  opada, suma udela = 1, orders == purchases, konverzija u realnom opsegu).
* Round-trip: sačuvan događaj se nalazi kroz `get_customer_events`.
* API: `POST /events` 201 + vraća događaj; greške 404/422/503.

## Česti bugovi

* **Nenormalizovan timestamp** (miks `T` i razmaka, vremenske zone) → sortiranje
  i sesije pucaju. Koristi `YYYY-MM-DD HH:MM:SS` svuda.
* **Polja bez dokumentovanog razloga** — krši data minimization i zbunjuje
  kasnije dane. Svako polje mora da ima „zašto".
* **Tihi `None`/`[]` na grešci** (audit anti-pattern) — zameni eksplicitnim
  404/422/500 sa porukom.
* **Generator sa previše oštrim klasama** — persone se ne preklapaju, pa Day 2
  K-Means savršeno razdvoji „očigledne" grupe i nema šta da se nauči. Preklapanje
  i šum su deo zadatka.
* **Nedeterminizam** — zaboravljen seed, globalni RNG, `date.today()` u
  generatoru → dataset se menja između pokretanja.

## Privatnost i saglasnost (GDPR / ZZPL)

Praćenje ponašanja je obrada ličnih podataka (`user_id`, sesija, istorija kupovine).
U Srbiji važi Zakon o zaštiti podataka o ličnosti (ZZPL, usklađen sa GDPR-om):

* **pravni osnov** — za analitiku i personalizaciju najčešće je to *saglasnost*
  (cookie/consent banner), a ne „legitimni interes“ po automatizmu;
* **minimizacija** — svako polje u šemi ima dokumentovan razlog (vidi Korak 1);
* **pravo na brisanje i prigovor** — mora postojati način da se događaji korisnika
  obrišu ili da se personalizacija isključi (Day 12 fallback „no_history“);
* **sintetički podaci** u kursu nisu lični podaci — ali isti kod u produkciji jeste
  obrada, pa `trackEvent` treba da poštuje odluku iz consent banera.

## Šta rezultat NE dokazuje

* **Popunjena tabela događaja nije analitika, nije segmentacija i nije AI** —
  to je preduslov.
* **Stopa konverzije (≈0.058) opisuje ovaj sintetički dataset**, ne nameru
  stvarnih korisnika; ona ne kaže *zašto* ljudi ne kupuju.
* **Udeo po kategoriji je deskripcija stanja**, ne uzrok uspeha te kategorije.
* **Preporuke koje vidimo na product stranici su biznis pravilo**, ne model —
  ne dokazuju personalizaciju.

## Vežbe

1. **`average_order_value`** — dodaj funkciju (prihod / broj različitih `order_id`;
   `orders.csv` ima jedan red po stavci), testiraj na seed-u, izloži na `GET /analytics/average-order-value`.
2. **`search` upit** — dodaj `get_search_events(store)` i `GET /analytics/searches`
   (broj pretraga po danu).
3. **Generator: price-sensitive persona sa preklapanjem** — napravi da
   price-sensitive korisnik *povremeno* kupi i skuplji proizvod (npr. smanji
   `PRICE_NOISE_PROB` korak ili dodaj sesiju „poklon"). Proveri da raspodela
   cena kupovina i dalje preklapa ostale persone.
4. **Udeo po proizvodu** — implementiraj `share_by_product` (ista logika kao
   `share_by_category`, ali grupiše po `product_id`).

## Sažetak

Danas si izgradio sloj podataka bez kojeg nijedan naredni dan ne može: šemu
događaja, čuvanje + upite (round-trip), analitiku (funnel, konverzija, udeo) i
deterministički generator sa preklapajućim personama. Sledeći korak: Day 2
iz tih događaja gradi feature-e i segmentaciju (RFM → K-Means). Pitanje koje
danas postavljaš je najvažnije u kursu: **šta zapisujemo, zašto i kako da to
bude reproduktivno?**

---

<!-- page_id 413 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/categories.csv

```
category_id,name,slug
1,Electronics,electronics
2,Fashion,fashion
3,Books,books
4,Sports,sports
5,Home,home
6,Beauty,beauty
7,Toys,toys
8,Food,food
9,Furniture,furniture
10,Automotive,automotive
11,Music,music
12,Tools,tools
```

### data/metadata.json

```
{
  "dataset": "dm_events_v2",
  "description": "Seeded synthetic e-commerce month (January 2026): catalog, customers, behavioral events and orders for the Digital Marketing & Recommender Systems course (Day 1).",
  "source": "synthetic",
  "generator": {
    "module": "app.data.generate_dataset",
    "function": "generate_dataset",
    "version": 2,
    "params": {
      "n_customers": 3000,
      "products_per_category": 21,
      "n_products": 252,
      "window_start": "2026-01-01",
      "window_days": 31
    }
  },
  "seed": {
    "rng": "numpy.default_rng",
    "seed_base": 42,
    "sub_seeds": {
      "customers": 42,
      "products": 43,
      "events": 44
    },
    "derivation": "seed_base + per-part integer offset; each part gets its own default_rng"
  },
  "personas": {
    "primary_counts": {
      "occasional": 957,
      "price_sensitive": 600,
      "category_focused": 588,
      "new_user": 523,
      "high_value": 332
    },
    "secondary_counts": {
      "high_value": 222,
      "new_user": 209,
      "price_sensitive": 203,
      "category_focused": 195,
      "occasional": 174
    },
    "secondary_probability": 0.35,
    "blend_prob": 0.25,
    "price_noise_prob": 0.15,
    "definitions": {
      "high_value": "high-value frequent buyers",
      "price_sensitive": "price-sensitive bargain hunters",
      "category_focused": "category-focused enthusiasts",
      "occasional": "occasional visitors",
      "new_user": "new users"
    },
    "behavior": {
      "high_value": {
        "sessions": 11.0,
        "views": 5.5,
        "cart": 0.048,
        "checkout": 0.45,
        "price": [
          4.0,
          2.0
        ],
        "alpha": 0.45
      },
      "category_focused": {
        "sessions": 7.0,
        "views": 7.0,
        "cart": 0.034,
        "checkout": 0.32,
        "price": [
          2.5,
          2.5
        ],
        "alpha": 0.12
      },
      "price_sensitive": {
        "sessions": 6.5,
        "views": 8.0,
        "cart": 0.019,
        "checkout": 0.2,
        "price": [
          1.3,
          4.5
        ],
        "alpha": 0.6
      },
      "occasional": {
        "sessions": 2.6,
        "views": 3.5,
        "cart": 0.026,
        "checkout": 0.22,
        "price": [
          2.0,
          2.5
        ],
        "alpha": 0.6
      },
      "new_user": {
        "sessions": 2.8,
        "views": 4.5,
        "cart": 0.027,
        "checkout": 0.2,
        "price": [
          2.0,
          2.5
        ],
        "alpha": 0.6
      }
    }
  },
  "realism": {
    "seasonality": "Jan 1 low (0.55x), winter sale Jan 2-6 (1.45x traffic, 30% of catalog 15-35% off, 1.2x cart/checkout), Orthodox Christmas Jan 7 (0.65x), weekends +18%, after payday Jan 25+ (+12%); hourly profile peaks 12-13h and 19-21h",
    "session_timing": "log-normal gaps between events (median ~35 s for views), capped at 25 min",
    "category_affinity": {
      "1": [
        [
          11,
          3
        ],
        [
          9,
          1
        ],
        [
          10,
          1
        ]
      ],
      "2": [
        [
          6,
          3
        ],
        [
          4,
          2
        ]
      ],
      "3": [
        [
          7,
          3
        ],
        [
          11,
          1
        ]
      ],
      "4": [
        [
          2,
          3
        ],
        [
          8,
          2
        ]
      ],
      "5": [
        [
          9,
          3
        ],
        [
          8,
          2
        ],
        [
          6,
          1
        ]
      ],
      "6": [
        [
          2,
          3
        ],
        [
          5,
          1
        ]
      ],
      "7": [
        [
          3,
          3
        ],
        [
          1,
          1
        ]
      ],
      "8": [
        [
          5,
          3
        ],
        [
          4,
          1
        ]
      ],
      "9": [
        [
          5,
          3
        ],
        [
          12,
          1
        ]
      ],
      "10": [
        [
          12,
          3
        ],
        [
          1,
          1
        ]
      ],
      "11": [
        [
          1,
          3
        ],
        [
          3,
          1
        ]
      ],
      "12": [
        [
          10,
          2
        ],
        [
          9,
          2
        ],
        [
          5,
          1
        ]
      ]
    },
    "co_purchase": "after add_to_cart, 45% chance to view a complementary product type (e.g. Laptop -> Mouse)",
    "recommendations": {
      "slate_prob": 0.22,
      "k": 3,
      "ctr_by_position": [
        0.035,
        0.02,
        0.012
      ],
      "rule": "top-popular in the viewed product's category"
    },
    "funnel": "cart probability depends on persona and price fit; 12% of cart items removed; checkout probability by persona (0.20-0.45)",
    "products_on_sale": 70
  },
  "counts": {
    "categories": 12,
    "products": 252,
    "customers": 3000,
    "events": 183468,
    "orders": 893,
    "order_lines": 1045
  },
  "funnel": {
    "product_views": 94220,
    "add_to_cart": 3159,
    "purchases": 1045,
    "sessions": 15361,
    "sessions_with_cart": 2713,
    "sessions_with_purchase": 893,
    "session_conversion_rate": 0.0581,
    "cart_abandonment_rate": 0.6708,
    "recommendation_impressions": 61530,
    "recommendation_clicks": 1427
  },
  "revenue": {
    "total": 95378.18,
    "aov": 106.81,
    "items_per_order": 1.17
  },
  "fields": {
    "categories": {
      "category_id": "int, stabilan ID kategorije",
      "name": "str, naziv kategorije",
      "slug": "str, URL slug"
    },
    "products": {
      "product_id": "int, stabilan ID proizvoda",
      "name": "str, tip + linija + model",
      "slug": "str, URL slug",
      "description": "str, opis sa atributima (namena, linija, boja)",
      "img_url": "str, placeholder putanja slike",
      "category_id": "int, FK -> categories.category_id",
      "price": "float, redovna cena u EUR (log-uniformno u opsegu tipa proizvoda), .99/.49",
      "created_at": "str, datum dodavanja u katalog (2025)"
    },
    "customers": {
      "user_id": "int, stabilan ID korisnika",
      "name": "str, generisano (veštački, nije PII)",
      "email": "str, generisani email (example.test)",
      "join_date": "str (YYYY-MM-DD)",
      "persona": "str, primarna persona",
      "secondary_persona": "str ili prazno, sekundarna persona",
      "blend_prob": "float, verovatnoća da sesija koristi sekundarnu personu"
    },
    "events": {
      "event_id": "int, rastući po vremenu",
      "event_type": "product_view|category_view|search|add_to_cart|remove_from_cart|purchase|recommendation_impression|recommendation_click",
      "user_id": "int, FK -> customers",
      "user_session": "str, session_NNNNNN (redosled početka sesije)",
      "product_id": "int ili prazno (category_view/search)",
      "category_id": "int ili prazno (search)",
      "price": "float ili prazno, cena u trenutku događaja (sa popustom tokom sniženja)",
      "quantity": "int >= 1",
      "source": "product_page|category_page|shop|search_page|cart|recommendation",
      "timestamp": "str YYYY-MM-DD HH:MM:SS, bez zone",
      "recommendation_source": "str ili prazno (category = Day 1 rule-based)",
      "recommendation_position": "int ili prazno, 1-based"
    },
    "orders": {
      "order_id": "int, ID porudžbine (stavke iste porudžbine dele ID)",
      "user_id": "int",
      "user_session": "str",
      "product_id": "int",
      "quantity": "int",
      "unit_price": "float, plaćena cena",
      "total_price": "float, unit_price * quantity (stavka)",
      "status": "str (completed)",
      "timestamp": "str, isto kao purchase događaj",
      "event_id": "int, FK -> purchase događaj"
    }
  },
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs.",
  "manifest": {
    "sha256": {
      "categories.csv": "e879d218899fee5d837b9d9c00260ce5abf6ff1781457db1bb9c0ac0c787b276",
      "products.csv": "44fd94efd58cc025eb1e7ca1dc4502942eefd1ac47d0ea01af787a7a309e17c2",
      "customers.csv": "57d1fc8c34129a0819b4f4b4b1589c4f5ef3ff4c3a16f0e98afe82fa92dc4074",
      "events.csv": "abd0360d39134f601804ef58102d6465c15760ad287cfa8e507f5f5923cce195",
      "orders.csv": "2d213925473fd9f3430f8743083a835d909da62f059e5403667ed2d97bc7aa63"
    }
  }
}
```

### data/orders.csv

```
order_id,user_id,user_session,product_id,quantity,unit_price,total_price,status,timestamp,event_id
1,515,session_000019,169,1,440.99,440.99,completed,2026-01-01 08:38:05,238
1,515,session_000019,105,1,59.99,59.99,completed,2026-01-01 08:38:07,239
2,120,session_000034,6,1,265.99,265.99,completed,2026-01-01 11:16:29,439
3,1677,session_000052,36,1,117.99,117.99,completed,2026-01-01 12:34:14,656
4,2995,session_000078,86,1,84.99,84.99,completed,2026-01-01 15:01:16,984
4,2995,session_000078,74,1,36.99,36.99,completed,2026-01-01 15:01:18,985
5,1063,session_000081,135,1,55.99,55.99,completed,2026-01-01 15:05:23,988
5,1063,session_000081,52,1,17.99,17.99,completed,2026-01-01 15:05:25,989
6,234,session_000125,76,1,46.99,46.99,completed,2026-01-01 19:06:52,1547
7,1033,session_000135,52,1,17.99,17.99,completed,2026-01-01 19:31:08,1608
8,870,session_000155,231,1,76.99,76.99,completed,2026-01-01 20:44:47,1924
9,1463,session_000183,184,1,89.99,89.99,completed,2026-01-01 22:00:42,2245
10,2922,session_000188,53,1,56.99,56.99,completed,2026-01-01 22:25:57,2328
11,1267,session_000194,49,1,15.99,15.99,completed,2026-01-01 22:53:51,2405
12,1030,session_000198,88,1,176.99,176.99,completed,2026-01-01 23:18:35,2485
13,2995,session_000216,117,1,56.48,56.48,completed,2026-01-02 02:26:13,2709
14,2852,session_000223,144,1,93.99,93.99,completed,2026-01-02 05:14:36,2807
14,2852,session_000223,140,1,63.99,63.99,completed,2026-01-02 05:14:38,2808
15,256,session_000225,134,1,47.99,47.99,completed,2026-01-02 05:31:39,2838
15,256,session_000225,53,1,44.55,44.55,completed,2026-01-02 05:31:41,2839
16,6,session_000241,153,1,3.49,3.49,completed,2026-01-02 07:17:57,3012
17,2260,session_000240,44,1,13.99,13.99,completed,2026-01-02 07:20:59,3016
18,152,session_000244,68,1,78.09,78.09,completed,2026-01-02 07:30:34,3064
18,152,session_000244,110,2,7.76,15.52,completed,2026-01-02 07:30:36,3065
18,152,session_000244,2,1,263.99,263.99,completed,2026-01-02 07:30:38,3066
19,1595,session_000247,241,1,89.12,89.12,completed,2026-01-02 07:40:20,3107
20,1161,session_000246,41,1,158.99,158.99,completed,2026-01-02 07:56:00,3200
20,1161,session_000246,110,3,7.76,23.28,completed,2026-01-02 07:56:02,3202
21,772,session_000258,242,2,194.99,389.98,completed,2026-01-02 08:12:33,3308
22,821,session_000264,40,1,130.99,130.99,completed,2026-01-02 08:26:05,3383
23,1443,session_000265,183,1,144.99,144.99,completed,2026-01-02 08:28:29,3403
24,2382,session_000274,85,1,61.99,61.99,completed,2026-01-02 08:42:22,3481
25,2895,session_000292,153,1,3.49,3.49,completed,2026-01-02 09:35:54,3689
26,515,session_000291,106,2,65.99,131.98,completed,2026-01-02 09:37:48,3716
27,64,session_000304,49,1,15.99,15.99,completed,2026-01-02 10:09:37,3824
28,2902,session_000308,2,2,263.99,527.98,completed,2026-01-02 10:14:39,3846
29,477,session_000310,10,1,200.99,200.99,completed,2026-01-02 10:18:12,3882
30,390,session_000311,171,1,235.99,235.99,completed,2026-01-02 10:23:16,3935
31,947,session_000313,65,1,96.99,96.99,completed,2026-01-02 10:24:29,3948
32,2917,session_000344,68,1,78.09,78.09,completed,2026-01-02 11:36:57,4229
33,758,session_000357,222,1,272.99,272.99,completed,2026-01-02 12:09:38,4405
34,1044,session_000356,200,1,30.99,30.99,completed,2026-01-02 12:15:07,4472
34,1044,session_000356,208,1,47.96,47.96,completed,2026-01-02 12:15:09,4473
35,1953,session_000366,152,1,2.3,2.3,completed,2026-01-02 12:28:36,4552
36,375,session_000369,6,1,265.99,265.99,completed,2026-01-02 12:31:56,4582
37,2828,session_000377,109,2,25.2,50.4,completed,2026-01-02 12:42:31,4706
38,1380,session_000380,7,1,336.99,336.99,completed,2026-01-02 12:51:05,4752
39,962,session_000379,130,1,57.99,57.99,completed,2026-01-02 12:52:47,4757
40,486,session_000393,74,1,36.99,36.99,completed,2026-01-02 13:09:45,4833
41,1162,session_000396,212,1,172.99,172.99,completed,2026-01-02 13:33:09,5003
42,2910,session_000426,193,1,92.99,92.99,completed,2026-01-02 14:13:29,5424
42,2910,session_000426,206,1,85.99,85.99,completed,2026-01-02 14:13:31,5425
42,2910,session_000426,207,1,22.78,22.78,completed,2026-01-02 14:13:33,5426
43,1182,session_000428,36,1,117.99,117.99,completed,2026-01-02 14:17:23,5453
43,1182,session_000428,122,1,27.51,27.51,completed,2026-01-02 14:17:25,5454
44,601,session_000429,231,1,76.99,76.99,completed,2026-01-02 14:20:45,5472
44,601,session_000429,224,1,76.99,76.99,completed,2026-01-02 14:20:47,5473
45,1703,session_000433,56,1,14.99,14.99,completed,2026-01-02 14:24:01,5488
46,2017,session_000434,183,1,144.99,144.99,completed,2026-01-02 14:24:06,5490
47,692,session_000440,148,2,8.49,16.98,completed,2026-01-02 14:34:01,5529
48,447,session_000443,30,1,34.99,34.99,completed,2026-01-02 14:43:09,5563
49,1708,session_000455,30,1,34.99,34.99,completed,2026-01-02 15:31:49,5734
50,2044,session_000461,181,1,204.99,204.99,completed,2026-01-02 15:41:13,5801
51,1063,session_000470,86,1,64.83,64.83,completed,2026-01-02 15:59:41,5919
52,1793,session_000501,228,1,29.99,29.99,completed,2026-01-02 16:58:47,6228
53,755,session_000503,85,1,61.99,61.99,completed,2026-01-02 17:03:14,6246
54,180,session_000518,85,1,61.99,61.99,completed,2026-01-02 17:32:17,6533
55,1235,session_000519,97,1,22.75,22.75,completed,2026-01-02 17:47:13,6678
55,1235,session_000519,85,1,61.99,61.99,completed,2026-01-02 17:47:15,6680
56,1709,session_000530,110,1,7.76,7.76,completed,2026-01-02 17:48:42,6689
57,1346,session_000524,223,1,34.99,34.99,completed,2026-01-02 17:49:05,6694
57,1346,session_000524,2,1,263.99,263.99,completed,2026-01-02 17:49:07,6695
58,1465,session_000554,26,1,100.99,100.99,completed,2026-01-02 18:19:38,6903
59,2953,session_000555,88,1,176.99,176.99,completed,2026-01-02 18:25:41,6924
60,2080,session_000579,127,1,37.99,37.99,completed,2026-01-02 18:54:25,7210
61,1917,session_000577,38,1,23.03,23.03,completed,2026-01-02 19:01:52,7323
61,1917,session_000577,39,1,25.99,25.99,completed,2026-01-02 19:01:54,7325
62,89,session_000620,148,1,8.49,8.49,completed,2026-01-02 19:38:37,7743
63,2132,session_000623,229,1,54.44,54.44,completed,2026-01-02 19:50:18,7918
64,395,session_000639,99,1,281.26,281.26,completed,2026-01-02 20:07:02,8164
65,2534,session_000667,76,1,46.99,46.99,completed,2026-01-02 20:38:38,8448
65,2534,session_000667,41,1,158.99,158.99,completed,2026-01-02 20:38:40,8449
66,2774,session_000675,1,1,185.99,185.99,completed,2026-01-02 20:41:30,8479
67,893,session_000684,101,1,67.99,67.99,completed,2026-01-02 20:54:51,8643
68,758,session_000696,136,1,36.04,36.04,completed,2026-01-02 21:06:03,8787
69,2633,session_000709,17,2,478.99,957.98,completed,2026-01-02 21:24:47,8930
69,2633,session_000709,193,1,92.99,92.99,completed,2026-01-02 21:24:49,8931
70,758,session_000731,204,1,5.32,5.32,completed,2026-01-02 21:37:24,9108
71,2313,session_000729,224,1,76.99,76.99,completed,2026-01-02 21:41:39,9187
71,2313,session_000729,229,2,54.44,108.88,completed,2026-01-02 21:41:41,9189
72,1419,session_000725,15,1,101.99,101.99,completed,2026-01-02 21:45:36,9251
73,66,session_000722,120,1,11.99,11.99,completed,2026-01-02 21:48:57,9334
74,1422,session_000775,135,1,41.92,41.92,completed,2026-01-02 22:40:25,9682
75,89,session_000821,70,1,206.7,206.7,completed,2026-01-03 01:23:29,10161
76,2630,session_000839,94,1,50.99,50.99,completed,2026-01-03 06:08:57,10370
76,2630,session_000839,2,1,263.99,263.99,completed,2026-01-03 06:08:59,10371
77,1586,session_000847,105,1,59.99,59.99,completed,2026-01-03 07:20:58,10473
78,1112,session_000855,85,1,61.99,61.99,completed,2026-01-03 07:54:07,10579
79,745,session_000865,127,1,37.99,37.99,completed,2026-01-03 08:23:34,10686
80,164,session_000874,121,1,19.17,19.17,completed,2026-01-03 08:40:10,10815
81,1972,session_000887,241,1,89.12,89.12,completed,2026-01-03 09:01:53,10926
82,2095,session_000902,181,1,204.99,204.99,completed,2026-01-03 09:29:59,11068
83,2324,session_000928,80,1,29.53,29.53,completed,2026-01-03 10:24:28,11347
83,2324,session_000928,76,1,46.99,46.99,completed,2026-01-03 10:24:30,11348
84,169,session_000949,6,1,265.99,265.99,completed,2026-01-03 11:05:10,11605
85,1886,session_000967,134,1,47.99,47.99,completed,2026-01-03 11:36:40,11740
86,2637,session_000969,90,1,23.99,23.99,completed,2026-01-03 11:41:47,11770
87,1503,session_000997,132,1,8.49,8.49,completed,2026-01-03 12:17:53,12069
88,2620,session_001014,225,2,9.49,18.98,completed,2026-01-03 12:39:10,12247
89,625,session_001026,60,1,14.99,14.99,completed,2026-01-03 13:06:29,12466
90,2375,session_001029,106,1,65.99,65.99,completed,2026-01-03 13:13:21,12546
91,390,session_001033,161,1,5.49,5.49,completed,2026-01-03 13:22:30,12641
92,1121,session_001039,206,1,85.99,85.99,completed,2026-01-03 13:23:03,12646
93,1780,session_001042,90,1,23.99,23.99,completed,2026-01-03 13:41:58,12811
94,486,session_001056,80,1,29.53,29.53,completed,2026-01-03 13:42:10,12813
95,806,session_001052,72,1,129.99,129.99,completed,2026-01-03 13:43:57,12824
96,1790,session_001065,148,2,8.49,16.98,completed,2026-01-03 14:07:52,12991
96,1790,session_001065,224,1,76.99,76.99,completed,2026-01-03 14:07:54,12992
97,962,session_001066,17,2,478.99,957.98,completed,2026-01-03 14:11:48,13051
98,658,session_001070,41,2,158.99,317.98,completed,2026-01-03 14:17:45,13136
99,2083,session_001079,63,1,20.99,20.99,completed,2026-01-03 14:20:51,13161
100,298,session_001084,30,1,34.99,34.99,completed,2026-01-03 14:31:27,13268
100,298,session_001084,42,1,170.13,170.13,completed,2026-01-03 14:31:29,13269
101,2969,session_001103,125,1,71.99,71.99,completed,2026-01-03 14:51:48,13466
102,1838,session_001104,165,1,21.36,21.36,completed,2026-01-03 15:00:06,13571
103,461,session_001131,15,1,101.99,101.99,completed,2026-01-03 15:40:07,13855
104,2418,session_001127,193,1,92.99,92.99,completed,2026-01-03 15:42:28,13868
105,716,session_001141,90,1,23.99,23.99,completed,2026-01-03 16:01:24,14066
106,2676,session_001159,66,1,54.99,54.99,completed,2026-01-03 16:20:49,14172
107,1009,session_001178,231,1,76.99,76.99,completed,2026-01-03 16:43:29,14435
107,1009,session_001178,226,1,24.99,24.99,completed,2026-01-03 16:43:31,14436
108,1341,session_001185,246,1,21.99,21.99,completed,2026-01-03 16:48:33,14488
109,190,session_001188,184,1,89.99,89.99,completed,2026-01-03 16:48:57,14493
110,2386,session_001189,141,1,17.99,17.99,completed,2026-01-03 17:01:56,14593
111,1018,session_001195,37,1,39.99,39.99,completed,2026-01-03 17:08:07,14632
112,1415,session_001221,141,1,17.99,17.99,completed,2026-01-03 17:28:29,14811
113,762,session_001238,206,1,85.99,85.99,completed,2026-01-03 17:57:09,15027
114,2360,session_001248,100,1,88.67,88.67,completed,2026-01-03 18:08:00,15192
114,2360,session_001248,150,1,7.49,7.49,completed,2026-01-03 18:08:02,15193
115,394,session_001251,61,1,24.99,24.99,completed,2026-01-03 18:08:23,15198
115,394,session_001251,43,1,23.99,23.99,completed,2026-01-03 18:08:25,15200
116,152,session_001243,185,1,98.99,98.99,completed,2026-01-03 18:08:46,15208
117,915,session_001236,99,1,281.26,281.26,completed,2026-01-03 18:11:48,15239
118,2572,session_001255,232,1,112.17,112.17,completed,2026-01-03 18:16:11,15268
119,637,session_001267,223,1,34.99,34.99,completed,2026-01-03 18:41:40,15489
119,637,session_001267,9,1,116.55,116.55,completed,2026-01-03 18:41:42,15491
120,61,session_001293,177,1,241.99,241.99,completed,2026-01-03 19:19:54,15928
121,2519,session_001318,85,1,61.99,61.99,completed,2026-01-03 19:31:51,16055
122,1768,session_001415,110,2,7.76,15.52,completed,2026-01-03 20:56:14,17007
123,1125,session_001429,1,1,185.99,185.99,completed,2026-01-03 21:06:17,17181
123,1125,session_001429,17,1,478.99,478.99,completed,2026-01-03 21:06:19,17182
124,10,session_001442,150,2,7.49,14.98,completed,2026-01-03 21:20:34,17321
125,1961,session_001456,210,1,76.99,76.99,completed,2026-01-03 21:30:58,17437
125,1961,session_001456,201,1,28.99,28.99,completed,2026-01-03 21:31:00,17439
126,624,session_001464,43,1,23.99,23.99,completed,2026-01-03 21:37:30,17522
127,2022,session_001482,76,1,46.99,46.99,completed,2026-01-03 21:45:14,17674
128,326,session_001476,110,1,7.76,7.76,completed,2026-01-03 21:46:20,17699
129,2255,session_001495,231,1,76.99,76.99,completed,2026-01-03 21:51:40,17802
130,600,session_001499,230,1,110.99,110.99,completed,2026-01-03 22:06:16,17956
131,1755,session_001523,178,1,561.99,561.99,completed,2026-01-03 22:31:41,18276
132,2543,session_001519,110,1,7.76,7.76,completed,2026-01-03 22:38:19,18351
133,1671,session_001528,76,2,46.99,93.98,completed,2026-01-03 22:45:47,18435
133,1671,session_001528,67,1,45.99,45.99,completed,2026-01-03 22:45:49,18436
134,967,session_001570,34,1,65.99,65.99,completed,2026-01-03 23:47:34,18739
135,1271,session_001573,230,1,110.99,110.99,completed,2026-01-03 23:48:16,18749
136,1626,session_001579,89,1,23.32,23.32,completed,2026-01-03 23:55:17,18785
137,699,session_001580,43,1,23.99,23.99,completed,2026-01-04 00:03:39,18844
138,1175,session_001581,73,1,76.99,76.99,completed,2026-01-04 00:10:56,18870
138,1175,session_001581,37,1,39.99,39.99,completed,2026-01-04 00:10:58,18871
139,2324,session_001594,80,1,29.53,29.53,completed,2026-01-04 00:54:27,18973
140,1165,session_001610,161,1,5.49,5.49,completed,2026-01-04 02:47:44,19190
141,2660,session_001619,14,1,11.99,11.99,completed,2026-01-04 06:22:58,19268
142,925,session_001638,158,2,4.46,8.92,completed,2026-01-04 07:52:41,19446
143,2614,session_001643,110,2,7.76,15.52,completed,2026-01-04 08:19:47,19529
144,620,session_001656,1,1,185.99,185.99,completed,2026-01-04 08:54:47,19720
144,620,session_001656,199,1,16.99,16.99,completed,2026-01-04 08:54:49,19721
145,2603,session_001666,43,1,23.99,23.99,completed,2026-01-04 09:10:55,19838
146,1463,session_001677,88,1,176.99,176.99,completed,2026-01-04 09:26:36,19906
147,152,session_001689,90,1,23.99,23.99,completed,2026-01-04 09:56:49,20111
148,1465,session_001711,118,1,6.49,6.49,completed,2026-01-04 10:30:53,20375
149,1506,session_001704,128,1,37.02,37.02,completed,2026-01-04 10:39:56,20517
149,1506,session_001704,133,1,23.99,23.99,completed,2026-01-04 10:39:58,20518
149,1506,session_001704,49,1,15.99,15.99,completed,2026-01-04 10:40:00,20519
150,682,session_001729,9,1,116.55,116.55,completed,2026-01-04 10:56:29,20641
151,1477,session_001733,105,1,59.99,59.99,completed,2026-01-04 11:03:01,20680
152,269,session_001731,198,1,8.65,8.65,completed,2026-01-04 11:08:37,20737
153,2872,session_001759,215,1,14.99,14.99,completed,2026-01-04 11:51:35,21029
154,891,session_001769,41,1,158.99,158.99,completed,2026-01-04 11:55:19,21052
155,2636,session_001783,169,1,440.99,440.99,completed,2026-01-04 12:28:53,21251
156,2198,session_001822,184,1,89.99,89.99,completed,2026-01-04 13:02:06,21707
157,1156,session_001841,46,1,10.99,10.99,completed,2026-01-04 13:27:31,21996
158,784,session_001874,127,1,37.99,37.99,completed,2026-01-04 14:12:44,22369
159,2799,session_001877,161,2,5.49,10.98,completed,2026-01-04 14:19:19,22393
160,2577,session_001881,140,1,63.99,63.99,completed,2026-01-04 14:35:54,22437
161,222,session_001912,112,1,65.99,65.99,completed,2026-01-04 15:15:22,22784
162,1880,session_001914,75,1,41.99,41.99,completed,2026-01-04 15:16:36,22787
163,2299,session_001930,76,1,46.99,46.99,completed,2026-01-04 16:02:52,22894
164,1595,session_001948,236,1,29.52,29.52,completed,2026-01-04 16:40:13,23144
165,190,session_001972,236,1,29.52,29.52,completed,2026-01-04 17:25:18,23470
166,956,session_001989,154,1,4.89,4.89,completed,2026-01-04 17:41:06,23677
166,956,session_001989,12,1,24.99,24.99,completed,2026-01-04 17:41:08,23678
167,2745,session_001996,224,1,76.99,76.99,completed,2026-01-04 17:46:20,23730
168,409,session_002003,135,1,41.92,41.92,completed,2026-01-04 17:50:56,23798
169,901,session_002005,53,1,44.55,44.55,completed,2026-01-04 17:59:20,23929
170,1809,session_002029,61,1,24.99,24.99,completed,2026-01-04 18:30:00,24214
170,1809,session_002029,51,1,11.99,11.99,completed,2026-01-04 18:30:02,24215
171,972,session_002040,179,1,763.99,763.99,completed,2026-01-04 18:47:50,24404
172,131,session_002046,177,1,241.99,241.99,completed,2026-01-04 18:53:03,24465
172,131,session_002046,10,1,200.99,200.99,completed,2026-01-04 18:53:05,24466
173,368,session_002058,243,1,53.99,53.99,completed,2026-01-04 19:09:01,24632
174,2852,session_002062,232,1,112.17,112.17,completed,2026-01-04 19:15:41,24735
175,1291,session_002066,178,1,561.99,561.99,completed,2026-01-04 19:25:59,24853
176,344,session_002080,200,1,30.99,30.99,completed,2026-01-04 19:27:35,24873
176,344,session_002080,199,1,16.99,16.99,completed,2026-01-04 19:27:37,24875
176,344,session_002080,234,1,13.99,13.99,completed,2026-01-04 19:27:39,24876
177,409,session_002081,136,1,36.04,36.04,completed,2026-01-04 19:28:08,24882
177,409,session_002081,140,1,63.99,63.99,completed,2026-01-04 19:28:10,24883
178,1484,session_002078,93,1,16.95,16.95,completed,2026-01-04 19:31:31,24914
179,2024,session_002093,181,1,204.99,204.99,completed,2026-01-04 19:40:43,25029
180,2580,session_002123,223,2,34.99,69.98,completed,2026-01-04 20:07:21,25369
181,2969,session_002127,7,1,336.99,336.99,completed,2026-01-04 20:16:02,25468
182,1771,session_002128,231,1,76.99,76.99,completed,2026-01-04 20:16:23,25476
183,1018,session_002146,141,1,17.99,17.99,completed,2026-01-04 20:41:40,25740
183,1018,session_002146,48,2,43.99,87.98,completed,2026-01-04 20:41:42,25741
183,1018,session_002146,61,1,24.99,24.99,completed,2026-01-04 20:41:44,25742
184,2917,session_002188,140,1,63.99,63.99,completed,2026-01-04 21:19:56,26222
185,150,session_002193,3,1,519.85,519.85,completed,2026-01-04 21:20:28,26237
186,395,session_002186,193,1,92.99,92.99,completed,2026-01-04 21:21:53,26251
187,760,session_002198,45,1,9.15,9.15,completed,2026-01-04 21:24:19,26292
188,1306,session_002233,88,1,176.99,176.99,completed,2026-01-04 22:02:20,26699
189,394,session_002242,74,1,36.99,36.99,completed,2026-01-04 22:25:42,26831
190,2903,session_002311,52,1,17.99,17.99,completed,2026-01-05 00:44:35,27628
191,169,session_002313,2,1,263.99,263.99,completed,2026-01-05 00:46:52,27642
191,169,session_002313,32,1,32.99,32.99,completed,2026-01-05 00:46:54,27644
192,2465,session_002393,218,1,64.99,64.99,completed,2026-01-05 09:25:07,28639
193,215,session_002395,93,1,16.95,16.95,completed,2026-01-05 09:35:10,28702
194,1301,session_002416,158,2,4.46,8.92,completed,2026-01-05 10:10:19,28965
195,697,session_002429,136,2,36.04,72.08,completed,2026-01-05 10:22:24,29071
196,2487,session_002431,223,1,34.99,34.99,completed,2026-01-05 10:42:47,29214
197,169,session_002447,125,1,71.99,71.99,completed,2026-01-05 11:25:43,29369
198,2500,session_002492,37,1,39.99,39.99,completed,2026-01-05 12:28:17,29971
199,2708,session_002501,78,1,9.49,9.49,completed,2026-01-05 12:45:34,30113
200,275,session_002542,206,1,85.99,85.99,completed,2026-01-05 13:44:30,30621
201,820,session_002547,52,1,17.99,17.99,completed,2026-01-05 14:10:50,30757
201,820,session_002547,136,1,36.04,36.04,completed,2026-01-05 14:10:52,30758
201,820,session_002547,132,1,8.49,8.49,completed,2026-01-05 14:10:54,30760
201,820,session_002547,95,1,63.75,63.75,completed,2026-01-05 14:10:56,30762
202,543,session_002554,223,2,34.99,69.98,completed,2026-01-05 14:16:42,30824
203,531,session_002562,98,1,120.57,120.57,completed,2026-01-05 14:32:39,30937
203,531,session_002562,80,1,29.53,29.53,completed,2026-01-05 14:32:41,30938
204,2075,session_002574,65,1,96.99,96.99,completed,2026-01-05 14:50:13,31096
204,2075,session_002574,76,1,46.99,46.99,completed,2026-01-05 14:50:15,31098
205,1002,session_002586,231,1,76.99,76.99,completed,2026-01-05 15:08:20,31230
206,2936,session_002598,37,1,39.99,39.99,completed,2026-01-05 15:41:45,31383
207,2286,session_002606,13,1,17.99,17.99,completed,2026-01-05 15:53:10,31474
208,924,session_002627,66,1,54.99,54.99,completed,2026-01-05 16:24:37,31743
209,1245,session_002646,39,1,25.99,25.99,completed,2026-01-05 17:16:07,32173
210,2104,session_002663,49,1,15.99,15.99,completed,2026-01-05 17:32:19,32233
210,2104,session_002663,230,1,110.99,110.99,completed,2026-01-05 17:32:21,32234
211,1939,session_002668,177,2,241.99,483.98,completed,2026-01-05 17:36:46,32268
212,152,session_002676,231,1,76.99,76.99,completed,2026-01-05 17:48:56,32366
213,732,session_002672,19,1,99.1,99.1,completed,2026-01-05 18:01:39,32478
213,732,session_002672,20,1,253.99,253.99,completed,2026-01-05 18:01:41,32479
213,732,session_002672,231,1,76.99,76.99,completed,2026-01-05 18:01:43,32480
214,337,session_002690,123,1,24.99,24.99,completed,2026-01-05 18:11:27,32573
215,1718,session_002706,37,1,39.99,39.99,completed,2026-01-05 18:28:10,32742
216,1388,session_002717,52,1,17.99,17.99,completed,2026-01-05 18:44:13,32847
217,702,session_002736,115,1,9.49,9.49,completed,2026-01-05 19:17:53,33138
218,1263,session_002786,231,1,76.99,76.99,completed,2026-01-05 19:57:14,33572
219,1184,session_002788,12,1,24.99,24.99,completed,2026-01-05 20:14:15,33810
220,63,session_002812,246,1,21.99,21.99,completed,2026-01-05 20:25:03,33941
221,1554,session_002813,229,1,54.44,54.44,completed,2026-01-05 20:44:59,34122
222,2700,session_002818,158,2,4.46,8.92,completed,2026-01-05 20:47:37,34159
223,146,session_002846,87,1,103.99,103.99,completed,2026-01-05 21:08:33,34416
224,1332,session_002844,50,1,23.99,23.99,completed,2026-01-05 21:13:11,34491
224,1332,session_002844,49,1,15.99,15.99,completed,2026-01-05 21:13:13,34493
225,220,session_002853,76,1,46.99,46.99,completed,2026-01-05 21:13:42,34500
226,2110,session_002859,230,1,110.99,110.99,completed,2026-01-05 21:17:36,34548
227,631,session_002880,148,1,8.49,8.49,completed,2026-01-05 21:39:26,34868
228,637,session_002883,202,1,27.99,27.99,completed,2026-01-05 21:43:33,34907
229,1593,session_002882,21,1,28.99,28.99,completed,2026-01-05 21:57:37,35047
230,2519,session_002918,30,1,34.99,34.99,completed,2026-01-05 22:25:43,35244
231,2216,session_002931,92,1,48.99,48.99,completed,2026-01-05 22:40:03,35365
231,2216,session_002931,162,1,26.99,26.99,completed,2026-01-05 22:40:05,35366
232,2447,session_002939,110,2,7.76,15.52,completed,2026-01-05 22:51:02,35461
233,486,session_002957,147,1,14.56,14.56,completed,2026-01-05 23:40:27,35643
234,2445,session_002979,74,1,36.99,36.99,completed,2026-01-06 01:21:37,36009
235,697,session_002992,52,2,17.99,35.98,completed,2026-01-06 06:01:00,36135
236,1301,session_003025,76,1,46.99,46.99,completed,2026-01-06 08:00:13,36446
237,1984,session_003037,140,1,63.99,63.99,completed,2026-01-06 08:19:42,36534
237,1984,session_003037,144,1,93.99,93.99,completed,2026-01-06 08:19:44,36536
238,395,session_003047,49,2,15.99,31.98,completed,2026-01-06 08:38:28,36648
238,395,session_003047,63,1,20.99,20.99,completed,2026-01-06 08:38:30,36650
239,762,session_003049,6,1,265.99,265.99,completed,2026-01-06 08:45:17,36689
239,762,session_003049,17,1,478.99,478.99,completed,2026-01-06 08:45:19,36690
240,2866,session_003063,6,1,265.99,265.99,completed,2026-01-06 09:22:53,36873
241,2224,session_003060,85,1,61.99,61.99,completed,2026-01-06 09:23:42,36879
242,1859,session_003075,93,1,16.95,16.95,completed,2026-01-06 09:46:26,37049
243,564,session_003069,218,1,64.99,64.99,completed,2026-01-06 09:46:54,37052
244,230,session_003084,33,1,37.99,37.99,completed,2026-01-06 10:16:57,37194
245,2890,session_003091,110,1,7.76,7.76,completed,2026-01-06 10:45:10,37393
246,476,session_003107,26,1,100.99,100.99,completed,2026-01-06 11:04:22,37472
247,970,session_003108,230,1,110.99,110.99,completed,2026-01-06 11:06:22,37491
247,970,session_003108,69,1,90.99,90.99,completed,2026-01-06 11:06:24,37492
248,1033,session_003146,142,1,7.83,7.83,completed,2026-01-06 12:22:42,38044
248,1033,session_003146,133,1,23.99,23.99,completed,2026-01-06 12:22:44,38046
248,1033,session_003146,44,1,13.99,13.99,completed,2026-01-06 12:22:46,38047
249,539,session_003158,107,1,25.36,25.36,completed,2026-01-06 12:35:02,38113
250,1868,session_003165,107,1,25.36,25.36,completed,2026-01-06 12:42:14,38170
251,2046,session_003164,127,1,37.99,37.99,completed,2026-01-06 12:45:38,38179
252,910,session_003196,191,1,65.99,65.99,completed,2026-01-06 13:45:06,38629
253,2205,session_003190,118,2,6.49,12.98,completed,2026-01-06 13:55:33,38711
253,2205,session_003190,87,1,103.99,103.99,completed,2026-01-06 13:55:35,38712
253,2205,session_003190,96,1,188.67,188.67,completed,2026-01-06 13:55:37,38713
254,1430,session_003216,76,2,46.99,93.98,completed,2026-01-06 14:16:03,38778
255,1182,session_003215,10,1,200.99,200.99,completed,2026-01-06 14:21:19,38820
256,516,session_003221,57,1,9.49,9.49,completed,2026-01-06 14:30:30,38861
257,620,session_003233,193,1,92.99,92.99,completed,2026-01-06 14:52:55,39012
257,620,session_003233,200,1,30.99,30.99,completed,2026-01-06 14:52:57,39013
258,519,session_003245,148,2,8.49,16.98,completed,2026-01-06 15:17:59,39178
258,519,session_003245,65,1,96.99,96.99,completed,2026-01-06 15:18:01,39180
259,2799,session_003266,49,1,15.99,15.99,completed,2026-01-06 15:46:29,39450
260,6,session_003262,164,1,13.99,13.99,completed,2026-01-06 15:48:28,39457
261,396,session_003298,66,1,54.99,54.99,completed,2026-01-06 16:43:21,39830
262,1576,session_003320,151,1,10.99,10.99,completed,2026-01-06 17:47:20,40197
263,2439,session_003321,27,1,69.38,69.38,completed,2026-01-06 17:54:13,40251
263,2439,session_003321,29,1,87.99,87.99,completed,2026-01-06 17:54:15,40253
264,2392,session_003374,232,1,112.17,112.17,completed,2026-01-06 18:59:54,40838
264,2392,session_003374,240,1,19.09,19.09,completed,2026-01-06 18:59:56,40839
265,2957,session_003406,127,1,37.99,37.99,completed,2026-01-06 19:35:18,41202
266,2799,session_003415,80,1,29.53,29.53,completed,2026-01-06 20:00:06,41500
267,143,session_003430,200,1,30.99,30.99,completed,2026-01-06 20:06:03,41568
268,217,session_003426,123,2,24.99,49.98,completed,2026-01-06 20:06:47,41574
269,1852,session_003431,90,1,23.99,23.99,completed,2026-01-06 20:10:59,41603
270,2146,session_003444,87,1,103.99,103.99,completed,2026-01-06 20:19:18,41681
271,1141,session_003450,237,1,34.99,34.99,completed,2026-01-06 20:24:51,41766
272,2082,session_003446,69,1,90.99,90.99,completed,2026-01-06 20:34:57,41871
273,205,session_003467,49,1,15.99,15.99,completed,2026-01-06 20:42:14,41959
274,2740,session_003474,247,1,15.99,15.99,completed,2026-01-06 21:04:35,42348
274,2740,session_003474,251,2,32.99,65.98,completed,2026-01-06 21:04:37,42350
275,365,session_003476,233,1,150.99,150.99,completed,2026-01-06 21:04:49,42352
276,1798,session_003469,131,1,20.78,20.78,completed,2026-01-06 21:14:25,42522
277,2318,session_003507,83,1,40.99,40.99,completed,2026-01-06 21:17:53,42572
278,206,session_003546,52,1,17.99,17.99,completed,2026-01-06 22:24:35,43056
279,151,session_003561,125,1,71.99,71.99,completed,2026-01-06 22:34:32,43153
280,1002,session_003560,6,2,265.99,531.98,completed,2026-01-06 22:35:22,43159
281,1279,session_003574,164,2,13.99,27.98,completed,2026-01-06 23:06:54,43359
282,699,session_003575,143,1,43.99,43.99,completed,2026-01-06 23:10:08,43389
282,699,session_003575,135,1,41.92,41.92,completed,2026-01-06 23:10:10,43391
283,2505,session_003591,41,1,158.99,158.99,completed,2026-01-06 23:43:01,43628
283,2505,session_003591,123,1,24.99,24.99,completed,2026-01-06 23:43:03,43629
284,337,session_003590,93,2,16.95,33.9,completed,2026-01-06 23:44:01,43631
285,1901,session_003605,76,1,46.99,46.99,completed,2026-01-07 00:59:58,43815
286,2313,session_003618,2,1,263.99,263.99,completed,2026-01-07 08:17:31,43988
287,2953,session_003629,123,3,24.99,74.97,completed,2026-01-07 09:00:33,44195
288,1389,session_003659,12,1,24.99,24.99,completed,2026-01-07 10:52:55,44432
289,2933,session_003660,2,1,263.99,263.99,completed,2026-01-07 11:14:00,44521
290,215,session_003694,80,1,37.99,37.99,completed,2026-01-07 14:05:48,44921
291,1652,session_003707,48,1,43.99,43.99,completed,2026-01-07 15:04:05,45046
292,2110,session_003719,241,1,119.99,119.99,completed,2026-01-07 15:55:13,45151
293,1939,session_003755,183,1,144.99,144.99,completed,2026-01-07 18:16:32,45535
294,2875,session_003756,184,2,89.99,179.98,completed,2026-01-07 18:23:42,45556
295,2554,session_003763,49,1,15.99,15.99,completed,2026-01-07 18:36:41,45627
296,555,session_003803,41,1,158.99,158.99,completed,2026-01-07 20:18:03,46105
297,151,session_003807,244,1,168.99,168.99,completed,2026-01-07 20:37:55,46165
298,1490,session_003836,76,1,46.99,46.99,completed,2026-01-07 22:09:48,46458
299,2995,session_003857,124,2,51.99,103.98,completed,2026-01-07 23:35:14,46670
300,522,session_003863,50,1,23.99,23.99,completed,2026-01-08 00:06:00,46699
301,903,session_003893,231,1,76.99,76.99,completed,2026-01-08 08:18:52,46967
302,713,session_003899,181,1,204.99,204.99,completed,2026-01-08 08:35:35,47056
303,2868,session_003901,133,1,23.99,23.99,completed,2026-01-08 08:53:25,47105
304,1334,session_003916,74,1,36.99,36.99,completed,2026-01-08 10:17:54,47314
305,1182,session_003917,17,1,478.99,478.99,completed,2026-01-08 10:18:17,47316
306,945,session_003929,124,2,51.99,103.98,completed,2026-01-08 11:23:03,47435
307,2265,session_003936,160,3,5.49,16.47,completed,2026-01-08 11:45:06,47488
308,2602,session_003948,86,1,84.99,84.99,completed,2026-01-08 12:31:14,47602
309,2067,session_003970,172,1,165.99,165.99,completed,2026-01-08 13:45:10,47919
310,2412,session_003985,176,1,60.99,60.99,completed,2026-01-08 14:42:45,48041
311,2059,session_003991,46,1,10.99,10.99,completed,2026-01-08 15:14:16,48199
312,601,session_004022,73,1,76.99,76.99,completed,2026-01-08 16:55:14,48608
313,637,session_004027,168,1,4.49,4.49,completed,2026-01-08 17:24:39,48712
314,286,session_004035,39,1,25.99,25.99,completed,2026-01-08 17:52:26,48764
315,395,session_004046,137,1,32.99,32.99,completed,2026-01-08 18:21:04,48864
316,2774,session_004130,127,1,37.99,37.99,completed,2026-01-08 21:16:49,49811
317,185,session_004146,211,2,407.99,815.98,completed,2026-01-08 21:51:19,49993
318,1020,session_004168,184,1,89.99,89.99,completed,2026-01-08 22:37:15,50262
319,1182,session_004200,205,1,10.99,10.99,completed,2026-01-09 00:29:00,50642
319,1182,session_004200,206,1,85.99,85.99,completed,2026-01-09 00:29:02,50643
319,1182,session_004200,2,1,263.99,263.99,completed,2026-01-09 00:29:04,50644
320,2633,session_004209,30,1,34.99,34.99,completed,2026-01-09 05:11:11,50723
321,664,session_004241,6,1,265.99,265.99,completed,2026-01-09 09:22:12,51171
322,914,session_004259,218,1,64.99,64.99,completed,2026-01-09 10:11:38,51301
323,517,session_004292,207,1,32.99,32.99,completed,2026-01-09 12:11:21,51674
324,1387,session_004308,231,1,76.99,76.99,completed,2026-01-09 12:56:38,51868
325,269,session_004330,21,1,28.99,28.99,completed,2026-01-09 14:34:54,52216
326,739,session_004348,223,1,34.99,34.99,completed,2026-01-09 14:59:42,52297
327,216,session_004358,95,1,88.99,88.99,completed,2026-01-09 15:26:52,52454
328,2690,session_004369,76,1,46.99,46.99,completed,2026-01-09 16:03:11,52598
328,2690,session_004369,71,1,493.99,493.99,completed,2026-01-09 16:03:13,52599
329,748,session_004392,105,1,59.99,59.99,completed,2026-01-09 17:25:03,53030
330,1999,session_004429,208,1,57.99,57.99,completed,2026-01-09 18:48:24,53435
331,1225,session_004438,75,1,41.99,41.99,completed,2026-01-09 19:16:56,53582
331,1225,session_004438,153,2,3.49,6.98,completed,2026-01-09 19:16:58,53583
332,2683,session_004440,9,1,142.99,142.99,completed,2026-01-09 19:30:44,53654
333,1958,session_004459,29,1,87.99,87.99,completed,2026-01-09 20:03:09,53809
334,168,session_004507,247,1,15.99,15.99,completed,2026-01-09 21:54:53,54373
335,614,session_004513,172,1,165.99,165.99,completed,2026-01-09 21:59:21,54420
336,2036,session_004522,206,1,85.99,85.99,completed,2026-01-09 22:21:26,54533
337,1067,session_004525,40,1,130.99,130.99,completed,2026-01-09 22:56:51,54680
338,2382,session_004540,102,1,35.99,35.99,completed,2026-01-09 23:28:32,54806
339,1859,session_004592,205,1,10.99,10.99,completed,2026-01-10 08:58:40,55406
340,298,session_004636,110,3,9.49,28.47,completed,2026-01-10 11:21:46,55879
340,298,session_004636,12,1,24.99,24.99,completed,2026-01-10 11:21:48,55880
341,10,session_004646,32,1,32.99,32.99,completed,2026-01-10 11:45:55,56013
342,2943,session_004650,5,1,71.99,71.99,completed,2026-01-10 11:52:39,56066
343,2485,session_004651,114,1,8.49,8.49,completed,2026-01-10 11:54:51,56077
344,1484,session_004677,81,1,29.99,29.99,completed,2026-01-10 13:23:58,56365
345,277,session_004676,231,1,76.99,76.99,completed,2026-01-10 13:25:22,56384
346,319,session_004695,188,1,141.99,141.99,completed,2026-01-10 14:14:55,56651
347,1969,session_004691,184,1,89.99,89.99,completed,2026-01-10 14:15:17,56652
348,1066,session_004736,26,1,100.99,100.99,completed,2026-01-10 16:20:42,57255
349,231,session_004752,54,1,87.99,87.99,completed,2026-01-10 16:58:32,57386
349,231,session_004752,45,2,11.99,23.98,completed,2026-01-10 16:58:34,57387
350,1341,session_004748,92,1,48.99,48.99,completed,2026-01-10 17:00:49,57402
351,1793,session_004769,215,1,14.99,14.99,completed,2026-01-10 17:44:33,57665
352,745,session_004783,164,1,13.99,13.99,completed,2026-01-10 18:15:20,57845
353,464,session_004817,49,1,15.99,15.99,completed,2026-01-10 19:10:12,58260
354,1936,session_004811,52,1,17.99,17.99,completed,2026-01-10 19:28:17,58365
355,1828,session_004834,100,2,122.99,245.98,completed,2026-01-10 19:42:09,58446
356,2746,session_004845,110,1,9.49,9.49,completed,2026-01-10 20:03:39,58547
357,1647,session_004892,55,1,26.99,26.99,completed,2026-01-10 21:20:12,59161
358,1182,session_004894,214,1,582.99,582.99,completed,2026-01-10 21:26:22,59223
359,1811,session_004937,80,1,37.99,37.99,completed,2026-01-10 22:48:08,59634
360,816,session_004960,62,1,17.99,17.99,completed,2026-01-10 23:56:44,59887
361,2050,session_004984,12,1,24.99,24.99,completed,2026-01-11 05:44:09,60152
362,2846,session_005025,186,2,81.99,163.98,completed,2026-01-11 09:20:48,60743
363,256,session_005044,136,1,52.99,52.99,completed,2026-01-11 10:05:56,60919
364,476,session_005054,37,1,39.99,39.99,completed,2026-01-11 10:25:21,61058
365,1162,session_005085,145,1,10.99,10.99,completed,2026-01-11 11:48:08,61513
366,1179,session_005118,177,1,241.99,241.99,completed,2026-01-11 12:38:56,61973
367,247,session_005130,12,1,24.99,24.99,completed,2026-01-11 13:20:16,62115
368,1468,session_005138,142,1,9.49,9.49,completed,2026-01-11 13:35:16,62210
369,1267,session_005137,250,1,19.99,19.99,completed,2026-01-11 13:37:14,62224
370,619,session_005151,181,1,204.99,204.99,completed,2026-01-11 14:00:17,62317
371,1680,session_005169,52,1,17.99,17.99,completed,2026-01-11 14:40:59,62489
372,2828,session_005173,120,1,11.99,11.99,completed,2026-01-11 14:49:50,62543
373,2997,session_005168,48,1,43.99,43.99,completed,2026-01-11 14:49:54,62544
374,190,session_005219,73,1,76.99,76.99,completed,2026-01-11 16:48:23,62952
375,1175,session_005249,85,1,61.99,61.99,completed,2026-01-11 18:03:40,63377
376,337,session_005275,234,1,13.99,13.99,completed,2026-01-11 18:57:24,63802
376,337,session_005275,232,1,162.99,162.99,completed,2026-01-11 18:57:26,63804
377,1379,session_005280,124,2,51.99,103.98,completed,2026-01-11 18:58:35,63810
378,483,session_005290,200,1,30.99,30.99,completed,2026-01-11 19:26:09,64013
379,394,session_005301,27,1,81.99,81.99,completed,2026-01-11 19:34:33,64048
379,394,session_005301,224,1,76.99,76.99,completed,2026-01-11 19:34:35,64050
380,30,session_005329,115,1,9.49,9.49,completed,2026-01-11 20:15:16,64439
381,636,session_005332,127,1,37.99,37.99,completed,2026-01-11 20:23:28,64516
381,636,session_005332,1,1,185.99,185.99,completed,2026-01-11 20:23:30,64517
381,636,session_005332,20,1,253.99,253.99,completed,2026-01-11 20:23:32,64518
382,955,session_005352,62,1,17.99,17.99,completed,2026-01-11 20:40:31,64732
383,602,session_005362,41,1,158.99,158.99,completed,2026-01-11 20:50:13,64808
384,2265,session_005401,40,1,130.99,130.99,completed,2026-01-11 21:45:10,65285
385,732,session_005413,60,1,14.99,14.99,completed,2026-01-11 22:11:50,65506
385,732,session_005413,56,1,14.99,14.99,completed,2026-01-11 22:11:52,65507
385,732,session_005413,46,1,10.99,10.99,completed,2026-01-11 22:11:54,65508
386,1268,session_005423,31,1,14.99,14.99,completed,2026-01-11 22:54:14,65664
387,2773,session_005436,107,2,31.99,63.98,completed,2026-01-11 23:35:00,65790
388,2105,session_005443,49,1,15.99,15.99,completed,2026-01-12 00:00:43,65857
389,2726,session_005453,198,1,11.99,11.99,completed,2026-01-12 02:11:06,65976
390,1675,session_005459,99,1,372.99,372.99,completed,2026-01-12 04:47:34,66067
391,806,session_005465,108,1,48.99,48.99,completed,2026-01-12 07:01:28,66154
392,2132,session_005464,9,1,142.99,142.99,completed,2026-01-12 07:05:22,66168
393,2378,session_005472,41,1,158.99,158.99,completed,2026-01-12 07:32:36,66218
394,607,session_005473,39,1,25.99,25.99,completed,2026-01-12 07:49:45,66273
395,1803,session_005476,139,1,47.99,47.99,completed,2026-01-12 08:04:28,66322
395,1803,session_005476,140,1,63.99,63.99,completed,2026-01-12 08:04:30,66323
396,2939,session_005503,148,3,8.49,25.47,completed,2026-01-12 09:23:41,66631
397,1121,session_005536,198,1,11.99,11.99,completed,2026-01-12 10:39:36,66999
398,2386,session_005562,137,1,32.99,32.99,completed,2026-01-12 11:49:14,67249
399,2109,session_005584,160,1,5.49,5.49,completed,2026-01-12 12:30:53,67441
400,2366,session_005601,223,1,34.99,34.99,completed,2026-01-12 13:02:03,67650
401,1314,session_005606,148,1,8.49,8.49,completed,2026-01-12 13:36:17,67869
402,1266,session_005658,49,1,15.99,15.99,completed,2026-01-12 14:55:30,68243
402,1266,session_005658,106,1,65.99,65.99,completed,2026-01-12 14:55:32,68244
403,947,session_005664,25,1,73.99,73.99,completed,2026-01-12 15:08:20,68337
404,2423,session_005682,22,1,123.99,123.99,completed,2026-01-12 16:05:27,68621
405,2902,session_005686,63,1,20.99,20.99,completed,2026-01-12 16:38:01,68779
405,2902,session_005686,139,1,47.99,47.99,completed,2026-01-12 16:38:03,68781
405,2902,session_005686,134,1,47.99,47.99,completed,2026-01-12 16:38:05,68782
406,1018,session_005706,160,3,5.49,16.47,completed,2026-01-12 17:18:29,68913
407,2324,session_005711,231,1,76.99,76.99,completed,2026-01-12 17:52:14,69088
408,111,session_005739,121,1,22.99,22.99,completed,2026-01-12 18:52:33,69265
409,1000,session_005744,73,1,76.99,76.99,completed,2026-01-12 19:02:37,69327
409,1000,session_005744,78,1,9.49,9.49,completed,2026-01-12 19:02:39,69329
410,1341,session_005776,148,2,8.49,16.98,completed,2026-01-12 19:49:16,69743
411,927,session_005787,252,1,15.99,15.99,completed,2026-01-12 19:54:50,69784
412,2453,session_005795,210,1,76.99,76.99,completed,2026-01-12 20:09:49,69872
413,2004,session_005829,7,2,336.99,673.98,completed,2026-01-12 21:06:38,70312
414,2375,session_005846,144,1,93.99,93.99,completed,2026-01-12 21:31:57,70504
415,2286,session_005856,249,1,7.49,7.49,completed,2026-01-12 21:54:08,70671
416,2736,session_005904,70,1,251.99,251.99,completed,2026-01-12 23:54:56,71156
417,517,session_005908,241,1,119.99,119.99,completed,2026-01-13 00:18:48,71200
418,1402,session_005910,240,1,26.99,26.99,completed,2026-01-13 00:35:34,71215
419,1182,session_005924,181,1,204.99,204.99,completed,2026-01-13 04:35:49,71444
420,543,session_005926,153,2,3.49,6.98,completed,2026-01-13 05:04:37,71459
421,960,session_005931,172,1,165.99,165.99,completed,2026-01-13 06:31:35,71497
422,2556,session_005934,34,1,65.99,65.99,completed,2026-01-13 06:43:42,71527
423,1161,session_005956,200,1,30.99,30.99,completed,2026-01-13 08:35:00,71783
424,1859,session_005996,199,1,16.99,16.99,completed,2026-01-13 10:56:53,72127
425,822,session_005999,241,1,119.99,119.99,completed,2026-01-13 11:07:10,72152
426,85,session_006040,65,2,96.99,193.98,completed,2026-01-13 13:05:10,72697
427,1544,session_006060,200,1,30.99,30.99,completed,2026-01-13 13:38:07,72950
428,1422,session_006092,158,2,5.49,10.98,completed,2026-01-13 14:46:05,73194
429,1022,session_006095,148,2,8.49,16.98,completed,2026-01-13 15:13:32,73319
430,913,session_006171,133,1,23.99,23.99,completed,2026-01-13 18:04:14,74268
431,1326,session_006238,50,1,23.99,23.99,completed,2026-01-13 20:15:24,75239
432,1921,session_006274,12,1,24.99,24.99,completed,2026-01-13 21:08:16,75612
433,515,session_006305,99,2,372.99,745.98,completed,2026-01-13 21:36:06,75885
434,116,session_006307,127,1,37.99,37.99,completed,2026-01-13 21:50:57,76071
435,1127,session_006297,224,1,76.99,76.99,completed,2026-01-13 21:53:28,76099
436,829,session_006324,148,1,8.49,8.49,completed,2026-01-13 22:08:01,76233
437,2957,session_006341,217,1,90.99,90.99,completed,2026-01-13 22:45:31,76563
438,1894,session_006350,87,1,103.99,103.99,completed,2026-01-13 23:09:48,76732
438,1894,session_006350,184,1,89.99,89.99,completed,2026-01-13 23:09:50,76733
439,2040,session_006366,235,1,25.99,25.99,completed,2026-01-13 23:53:52,76897
439,2040,session_006366,198,1,11.99,11.99,completed,2026-01-13 23:53:54,76898
440,816,session_006383,101,1,67.99,67.99,completed,2026-01-14 01:55:50,77072
440,816,session_006383,85,1,61.99,61.99,completed,2026-01-14 01:55:52,77073
441,167,session_006392,27,1,81.99,81.99,completed,2026-01-14 06:18:43,77180
442,217,session_006412,12,1,24.99,24.99,completed,2026-01-14 08:29:50,77475
443,1680,session_006414,133,1,23.99,23.99,completed,2026-01-14 08:38:08,77527
444,449,session_006476,127,1,37.99,37.99,completed,2026-01-14 12:13:55,78223
444,449,session_006476,49,1,15.99,15.99,completed,2026-01-14 12:13:57,78224
445,2080,session_006495,62,1,17.99,17.99,completed,2026-01-14 12:44:24,78435
446,2149,session_006499,156,1,7.49,7.49,completed,2026-01-14 13:07:57,78561
447,2216,session_006510,55,1,26.99,26.99,completed,2026-01-14 13:16:28,78599
448,2232,session_006525,196,1,19.99,19.99,completed,2026-01-14 13:42:09,78768
449,896,session_006527,230,1,110.99,110.99,completed,2026-01-14 13:50:20,78804
450,730,session_006533,175,1,167.99,167.99,completed,2026-01-14 14:14:07,78932
450,730,session_006533,198,1,11.99,11.99,completed,2026-01-14 14:14:09,78933
451,1715,session_006542,158,1,5.49,5.49,completed,2026-01-14 14:19:18,78978
452,962,session_006556,233,1,150.99,150.99,completed,2026-01-14 15:00:42,79160
453,747,session_006569,200,1,30.99,30.99,completed,2026-01-14 15:56:33,79264
454,1462,session_006572,229,1,64.99,64.99,completed,2026-01-14 16:02:27,79291
455,142,session_006581,60,1,14.99,14.99,completed,2026-01-14 16:39:35,79499
456,2100,session_006610,227,1,46.99,46.99,completed,2026-01-14 17:47:45,79814
456,2100,session_006610,152,1,3.49,3.49,completed,2026-01-14 17:47:47,79815
456,2100,session_006610,90,1,23.99,23.99,completed,2026-01-14 17:47:49,79816
457,1182,session_006674,9,1,142.99,142.99,completed,2026-01-14 19:54:28,80681
458,476,session_006666,125,2,71.99,143.98,completed,2026-01-14 20:00:42,80721
458,476,session_006666,22,1,123.99,123.99,completed,2026-01-14 20:00:44,80722
459,1718,session_006709,187,1,277.99,277.99,completed,2026-01-14 21:17:16,81241
460,2958,session_006722,3,1,765.99,765.99,completed,2026-01-14 21:30:14,81331
461,799,session_006725,34,1,65.99,65.99,completed,2026-01-14 21:40:03,81414
462,2318,session_006736,128,1,51.99,51.99,completed,2026-01-14 21:49:39,81501
463,1818,session_006741,44,1,13.99,13.99,completed,2026-01-14 21:54:22,81523
464,974,session_006785,228,1,29.99,29.99,completed,2026-01-14 23:07:08,82032
464,974,session_006785,60,2,14.99,29.98,completed,2026-01-14 23:07:10,82033
465,2577,session_006786,68,1,116.99,116.99,completed,2026-01-14 23:16:22,82098
466,2254,session_006844,101,1,67.99,67.99,completed,2026-01-15 08:02:26,82708
467,205,session_006978,224,1,76.99,76.99,completed,2026-01-15 14:05:16,84337
468,2910,session_006985,243,1,53.99,53.99,completed,2026-01-15 14:18:00,84437
469,216,session_007021,164,1,13.99,13.99,completed,2026-01-15 15:45:33,84939
469,216,session_007021,90,1,23.99,23.99,completed,2026-01-15 15:45:35,84940
470,2266,session_007052,68,1,116.99,116.99,completed,2026-01-15 17:20:34,85336
471,956,session_007068,93,1,23.99,23.99,completed,2026-01-15 18:05:48,85586
472,2995,session_007084,112,1,65.99,65.99,completed,2026-01-15 18:38:12,85746
473,1802,session_007119,160,2,5.49,10.98,completed,2026-01-15 19:46:54,86129
474,2995,session_007123,108,1,48.99,48.99,completed,2026-01-15 19:48:35,86144
475,368,session_007127,241,1,119.99,119.99,completed,2026-01-15 19:59:34,86275
476,1008,session_007183,127,1,37.99,37.99,completed,2026-01-15 20:54:19,86912
477,758,session_007211,8,1,725.99,725.99,completed,2026-01-15 21:36:52,87266
478,823,session_007218,30,1,34.99,34.99,completed,2026-01-15 22:06:09,87499
479,656,session_007278,249,1,7.49,7.49,completed,2026-01-16 00:09:43,88176
480,1962,session_007273,36,1,117.99,117.99,completed,2026-01-16 00:12:09,88187
480,1962,session_007273,40,1,130.99,130.99,completed,2026-01-16 00:12:11,88188
481,638,session_007281,150,1,7.49,7.49,completed,2026-01-16 00:40:25,88269
482,2095,session_007299,110,3,9.49,28.47,completed,2026-01-16 03:26:56,88468
483,2307,session_007305,52,1,17.99,17.99,completed,2026-01-16 06:17:57,88552
484,290,session_007336,132,1,8.49,8.49,completed,2026-01-16 08:52:06,88902
485,221,session_007343,105,1,59.99,59.99,completed,2026-01-16 09:06:19,88922
486,770,session_007352,76,1,46.99,46.99,completed,2026-01-16 09:22:19,89037
487,1267,session_007364,133,1,23.99,23.99,completed,2026-01-16 09:52:33,89223
488,2381,session_007369,184,1,89.99,89.99,completed,2026-01-16 09:59:22,89277
489,1533,session_007384,97,1,32.99,32.99,completed,2026-01-16 10:41:42,89392
490,388,session_007402,30,2,34.99,69.98,completed,2026-01-16 11:31:56,89685
491,1281,session_007405,13,1,17.99,17.99,completed,2026-01-16 11:34:49,89703
492,2095,session_007420,85,1,61.99,61.99,completed,2026-01-16 12:02:05,89827
493,66,session_007438,125,1,71.99,71.99,completed,2026-01-16 12:37:16,90048
494,2870,session_007475,124,1,51.99,51.99,completed,2026-01-16 14:25:06,90477
495,1018,session_007478,65,1,96.99,96.99,completed,2026-01-16 14:40:32,90558
496,395,session_007542,137,1,32.99,32.99,completed,2026-01-16 17:32:10,91286
497,799,session_007549,12,1,24.99,24.99,completed,2026-01-16 17:52:14,91440
498,141,session_007571,251,1,32.99,32.99,completed,2026-01-16 18:35:11,91658
498,141,session_007571,87,2,103.99,207.98,completed,2026-01-16 18:35:13,91659
499,1940,session_007598,60,1,14.99,14.99,completed,2026-01-16 19:22:04,91932
500,688,session_007650,61,1,24.99,24.99,completed,2026-01-16 20:50:50,92490
501,244,session_007641,120,2,11.99,23.98,completed,2026-01-16 20:52:31,92504
502,1263,session_007667,37,1,39.99,39.99,completed,2026-01-16 21:32:09,92800
503,356,session_007734,92,1,48.99,48.99,completed,2026-01-17 00:02:23,93500
504,2979,session_007768,183,1,144.99,144.99,completed,2026-01-17 07:00:13,93770
505,2401,session_007772,181,1,204.99,204.99,completed,2026-01-17 07:29:41,93857
506,230,session_007777,61,1,24.99,24.99,completed,2026-01-17 08:01:56,93923
506,230,session_007777,136,1,52.99,52.99,completed,2026-01-17 08:01:58,93924
507,764,session_007789,50,2,23.99,47.98,completed,2026-01-17 08:53:07,94128
507,764,session_007789,52,1,17.99,17.99,completed,2026-01-17 08:53:09,94129
507,764,session_007789,49,1,15.99,15.99,completed,2026-01-17 08:53:11,94130
508,2175,session_007814,127,1,37.99,37.99,completed,2026-01-17 10:10:59,94381
508,2175,session_007814,47,1,30.99,30.99,completed,2026-01-17 10:11:01,94382
509,2146,session_007823,2,1,263.99,263.99,completed,2026-01-17 10:36:47,94529
510,793,session_007829,90,1,23.99,23.99,completed,2026-01-17 10:50:18,94572
511,1844,session_007836,216,1,19.99,19.99,completed,2026-01-17 11:15:06,94762
512,2132,session_007905,200,1,30.99,30.99,completed,2026-01-17 13:32:58,95530
513,605,session_007919,177,1,241.99,241.99,completed,2026-01-17 14:08:19,95643
514,2505,session_007942,37,1,39.99,39.99,completed,2026-01-17 15:13:27,95939
515,2090,session_007985,137,2,32.99,65.98,completed,2026-01-17 17:25:25,96433
515,2090,session_007985,133,1,23.99,23.99,completed,2026-01-17 17:25:27,96434
516,266,session_007992,71,1,493.99,493.99,completed,2026-01-17 17:49:04,96614
517,2368,session_008039,80,1,37.99,37.99,completed,2026-01-17 19:05:36,97090
517,2368,session_008039,161,1,5.49,5.49,completed,2026-01-17 19:05:38,97092
518,1876,session_008065,65,1,96.99,96.99,completed,2026-01-17 19:44:22,97508
519,2734,session_008079,93,2,23.99,47.98,completed,2026-01-17 20:01:59,97665
520,468,session_008096,32,1,32.99,32.99,completed,2026-01-17 20:43:06,98069
520,468,session_008096,80,2,37.99,75.98,completed,2026-01-17 20:43:08,98070
521,1900,session_008134,3,1,765.99,765.99,completed,2026-01-17 21:20:57,98352
522,1330,session_008137,157,2,8.49,16.98,completed,2026-01-17 21:22:04,98364
523,911,session_008139,119,3,5.49,16.47,completed,2026-01-17 21:30:56,98399
524,396,session_008143,121,1,22.99,22.99,completed,2026-01-17 21:37:43,98439
525,919,session_008160,219,1,181.99,181.99,completed,2026-01-17 22:03:07,98686
526,1941,session_008173,26,1,100.99,100.99,completed,2026-01-17 22:34:02,98908
527,1462,session_008181,229,1,64.99,64.99,completed,2026-01-17 22:42:52,99013
528,1077,session_008190,97,1,32.99,32.99,completed,2026-01-17 22:52:46,99081
529,373,session_008204,52,1,17.99,17.99,completed,2026-01-17 23:31:00,99293
530,2135,session_008207,20,1,253.99,253.99,completed,2026-01-17 23:34:04,99334
531,1213,session_008210,177,1,241.99,241.99,completed,2026-01-17 23:34:05,99335
530,2135,session_008207,237,1,34.99,34.99,completed,2026-01-17 23:34:06,99336
532,2875,session_008241,177,1,241.99,241.99,completed,2026-01-18 04:10:41,99670
533,2525,session_008331,206,1,85.99,85.99,completed,2026-01-18 11:12:23,100635
534,60,session_008341,161,1,5.49,5.49,completed,2026-01-18 11:44:48,100820
535,1465,session_008352,35,1,17.99,17.99,completed,2026-01-18 11:54:46,100948
536,1182,session_008356,7,1,336.99,336.99,completed,2026-01-18 12:04:20,101033
537,318,session_008383,184,1,89.99,89.99,completed,2026-01-18 12:47:54,101339
538,822,session_008429,177,1,241.99,241.99,completed,2026-01-18 14:30:04,102104
539,1847,session_008451,169,1,440.99,440.99,completed,2026-01-18 15:21:31,102406
540,1929,session_008458,80,1,37.99,37.99,completed,2026-01-18 15:33:07,102508
540,1929,session_008458,148,2,8.49,16.98,completed,2026-01-18 15:33:09,102509
541,519,session_008482,73,1,76.99,76.99,completed,2026-01-18 16:11:51,102714
542,1097,session_008494,251,1,32.99,32.99,completed,2026-01-18 16:32:06,102879
543,2339,session_008518,132,1,8.49,8.49,completed,2026-01-18 17:50:50,103173
544,395,session_008530,49,1,15.99,15.99,completed,2026-01-18 17:56:25,103208
545,1137,session_008542,222,1,272.99,272.99,completed,2026-01-18 18:23:35,103430
546,2995,session_008544,41,1,158.99,158.99,completed,2026-01-18 18:28:46,103453
547,547,session_008545,31,1,14.99,14.99,completed,2026-01-18 18:30:15,103468
547,547,session_008545,27,1,81.99,81.99,completed,2026-01-18 18:30:17,103469
548,2910,session_008568,243,1,53.99,53.99,completed,2026-01-18 19:06:16,103697
549,2467,session_008588,157,1,8.49,8.49,completed,2026-01-18 19:50:39,103971
550,1190,session_008629,125,3,71.99,215.97,completed,2026-01-18 20:49:18,104368
551,1554,session_008655,127,1,37.99,37.99,completed,2026-01-18 21:31:49,104771
552,775,session_008682,93,1,23.99,23.99,completed,2026-01-18 22:21:37,105118
553,2466,session_008681,218,1,64.99,64.99,completed,2026-01-18 22:22:20,105121
553,2466,session_008681,121,3,22.99,68.97,completed,2026-01-18 22:22:22,105123
554,1457,session_008684,167,2,3.49,6.98,completed,2026-01-18 22:34:14,105263
555,2132,session_008690,214,1,582.99,582.99,completed,2026-01-18 22:38:20,105311
556,195,session_008706,12,2,24.99,49.98,completed,2026-01-18 23:07:54,105448
557,1009,session_008713,183,1,144.99,144.99,completed,2026-01-18 23:39:29,105623
558,1018,session_008723,73,1,76.99,76.99,completed,2026-01-19 00:09:34,105703
559,2533,session_008743,110,1,9.49,9.49,completed,2026-01-19 05:36:34,105939
560,699,session_008769,44,1,13.99,13.99,completed,2026-01-19 08:24:35,106281
561,2953,session_008799,124,1,51.99,51.99,completed,2026-01-19 09:50:49,106593
562,1390,session_008812,103,1,13.99,13.99,completed,2026-01-19 10:20:26,106708
563,1593,session_008824,238,1,15.99,15.99,completed,2026-01-19 10:53:11,106808
564,167,session_008842,243,1,53.99,53.99,completed,2026-01-19 12:05:57,107061
565,1543,session_008865,43,1,23.99,23.99,completed,2026-01-19 12:42:40,107358
566,1330,session_008950,17,1,478.99,478.99,completed,2026-01-19 16:03:05,108424
567,1848,session_008964,147,1,17.99,17.99,completed,2026-01-19 16:16:59,108552
568,306,session_008992,105,1,59.99,59.99,completed,2026-01-19 17:13:27,108843
569,375,session_009026,206,1,85.99,85.99,completed,2026-01-19 18:35:00,109231
570,564,session_009022,156,1,7.49,7.49,completed,2026-01-19 18:37:44,109249
571,160,session_009068,230,1,110.99,110.99,completed,2026-01-19 19:44:12,109907
572,1356,session_009075,137,1,32.99,32.99,completed,2026-01-19 19:44:25,109908
573,2870,session_009082,110,2,9.49,18.98,completed,2026-01-19 20:01:20,110048
574,1137,session_009102,50,1,23.99,23.99,completed,2026-01-19 20:30:25,110335
574,1137,session_009102,52,1,17.99,17.99,completed,2026-01-19 20:30:27,110336
575,1185,session_009111,86,1,84.99,84.99,completed,2026-01-19 20:42:38,110478
576,1117,session_009127,150,1,7.49,7.49,completed,2026-01-19 21:02:14,110657
577,1910,session_009131,12,1,24.99,24.99,completed,2026-01-19 21:16:49,110712
578,1067,session_009133,9,1,142.99,142.99,completed,2026-01-19 21:29:16,110834
578,1067,session_009133,2,2,263.99,527.98,completed,2026-01-19 21:29:18,110835
578,1067,session_009133,20,1,253.99,253.99,completed,2026-01-19 21:29:20,110837
578,1067,session_009133,76,1,46.99,46.99,completed,2026-01-19 21:29:22,110838
578,1067,session_009133,184,2,89.99,179.98,completed,2026-01-19 21:29:24,110839
579,793,session_009161,113,2,72.99,145.98,completed,2026-01-19 22:08:58,111231
579,793,session_009161,82,1,25.99,25.99,completed,2026-01-19 22:09:00,111232
580,1067,session_009200,226,1,24.99,24.99,completed,2026-01-19 23:04:04,111667
581,2213,session_009203,66,1,54.99,54.99,completed,2026-01-19 23:24:27,111751
581,2213,session_009203,68,1,116.99,116.99,completed,2026-01-19 23:24:29,111752
582,1798,session_009213,101,1,67.99,67.99,completed,2026-01-19 23:42:04,111871
583,2216,session_009218,127,1,37.99,37.99,completed,2026-01-19 23:47:09,111920
583,2216,session_009218,142,1,9.49,9.49,completed,2026-01-19 23:47:11,111922
584,456,session_009236,193,1,92.99,92.99,completed,2026-01-20 02:18:12,112118
585,1082,session_009242,205,1,10.99,10.99,completed,2026-01-20 03:38:35,112157
585,1082,session_009242,198,1,11.99,11.99,completed,2026-01-20 03:38:37,112158
586,1470,session_009261,215,1,14.99,14.99,completed,2026-01-20 07:37:32,112343
587,2453,session_009265,9,1,142.99,142.99,completed,2026-01-20 08:02:38,112390
587,2453,session_009265,2,1,263.99,263.99,completed,2026-01-20 08:02:40,112391
588,2042,session_009280,184,1,89.99,89.99,completed,2026-01-20 09:02:42,112594
589,1229,session_009285,164,1,13.99,13.99,completed,2026-01-20 09:30:40,112743
590,913,session_009322,37,1,39.99,39.99,completed,2026-01-20 11:34:26,113289
591,2801,session_009328,200,1,30.99,30.99,completed,2026-01-20 11:39:45,113330
591,2801,session_009328,38,1,31.99,31.99,completed,2026-01-20 11:39:47,113331
592,706,session_009378,231,1,76.99,76.99,completed,2026-01-20 13:25:33,113824
593,405,session_009383,8,1,725.99,725.99,completed,2026-01-20 13:49:57,113939
594,2446,session_009385,76,1,46.99,46.99,completed,2026-01-20 13:55:49,113952
595,2111,session_009408,23,1,109.99,109.99,completed,2026-01-20 15:17:20,114263
596,216,session_009448,156,1,7.49,7.49,completed,2026-01-20 16:53:15,114806
597,2934,session_009458,67,1,45.99,45.99,completed,2026-01-20 17:25:12,114910
598,1341,session_009461,204,1,6.49,6.49,completed,2026-01-20 17:35:22,114959
599,1595,session_009508,243,1,53.99,53.99,completed,2026-01-20 19:14:59,115476
600,1803,session_009513,8,1,725.99,725.99,completed,2026-01-20 19:22:51,115516
601,595,session_009528,49,2,15.99,31.98,completed,2026-01-20 19:58:10,115758
602,1965,session_009567,90,1,23.99,23.99,completed,2026-01-20 20:53:33,116139
603,1175,session_009587,121,2,22.99,45.98,completed,2026-01-20 21:35:42,116345
604,449,session_009594,22,1,123.99,123.99,completed,2026-01-20 21:46:40,116410
605,461,session_009639,96,1,243.99,243.99,completed,2026-01-20 23:43:23,116938
606,2044,session_009652,173,1,321.99,321.99,completed,2026-01-21 00:13:14,117052
607,2542,session_009665,184,1,89.99,89.99,completed,2026-01-21 02:41:37,117179
608,1143,session_009669,74,1,36.99,36.99,completed,2026-01-21 04:34:20,117211
609,2171,session_009679,219,1,181.99,181.99,completed,2026-01-21 07:09:57,117321
610,2532,session_009689,123,3,24.99,74.97,completed,2026-01-21 08:07:00,117471
611,927,session_009728,195,1,108.99,108.99,completed,2026-01-21 10:20:11,117848
612,2786,session_009735,141,1,17.99,17.99,completed,2026-01-21 10:54:31,117924
613,927,session_009741,2,1,263.99,263.99,completed,2026-01-21 11:07:34,118020
614,1184,session_009742,115,1,9.49,9.49,completed,2026-01-21 11:12:03,118046
615,2673,session_009744,109,3,31.99,95.97,completed,2026-01-21 11:14:38,118056
615,2673,session_009744,106,2,65.99,131.98,completed,2026-01-21 11:14:40,118057
616,1629,session_009761,198,1,11.99,11.99,completed,2026-01-21 12:00:57,118223
617,181,session_009772,200,1,30.99,30.99,completed,2026-01-21 12:10:23,118276
618,1330,session_009775,156,1,7.49,7.49,completed,2026-01-21 12:20:41,118326
619,2216,session_009777,2,1,263.99,263.99,completed,2026-01-21 12:25:19,118344
620,1380,session_009805,9,1,142.99,142.99,completed,2026-01-21 13:42:32,118640
621,476,session_009820,121,2,22.99,45.98,completed,2026-01-21 14:15:38,118820
621,476,session_009820,90,1,23.99,23.99,completed,2026-01-21 14:15:40,118822
622,46,session_009833,60,1,14.99,14.99,completed,2026-01-21 15:00:35,118920
623,767,session_009839,28,1,109.99,109.99,completed,2026-01-21 15:20:54,118995
624,151,session_009838,170,1,591.99,591.99,completed,2026-01-21 15:22:03,118996
625,1742,session_009876,31,1,14.99,14.99,completed,2026-01-21 16:57:02,119444
626,350,session_009895,234,1,13.99,13.99,completed,2026-01-21 18:05:41,119705
626,350,session_009895,237,1,34.99,34.99,completed,2026-01-21 18:05:43,119706
627,517,session_009908,199,1,16.99,16.99,completed,2026-01-21 18:32:28,119948
627,517,session_009908,244,1,168.99,168.99,completed,2026-01-21 18:32:30,119949
628,773,session_009923,47,1,30.99,30.99,completed,2026-01-21 18:41:12,120005
629,519,session_009943,200,1,30.99,30.99,completed,2026-01-21 19:17:36,120309
630,406,session_009990,30,2,34.99,69.98,completed,2026-01-21 20:48:15,120822
631,187,session_010013,198,1,11.99,11.99,completed,2026-01-21 21:22:34,121040
632,764,session_010015,52,1,17.99,17.99,completed,2026-01-21 21:37:49,121217
633,1265,session_010065,181,1,204.99,204.99,completed,2026-01-21 22:56:52,121764
634,1007,session_010076,108,1,48.99,48.99,completed,2026-01-21 23:11:54,121819
635,1386,session_010088,30,1,34.99,34.99,completed,2026-01-22 00:05:02,121966
636,1269,session_010112,109,1,31.99,31.99,completed,2026-01-22 06:03:40,122213
637,169,session_010244,10,1,200.99,200.99,completed,2026-01-22 13:31:56,123694
638,1972,session_010264,181,1,204.99,204.99,completed,2026-01-22 14:03:30,123886
639,477,session_010278,30,1,34.99,34.99,completed,2026-01-22 14:34:23,124002
640,1379,session_010287,37,1,39.99,39.99,completed,2026-01-22 15:03:45,124173
640,1379,session_010287,27,1,81.99,81.99,completed,2026-01-22 15:03:47,124174
641,1465,session_010305,22,1,123.99,123.99,completed,2026-01-22 15:47:01,124360
642,2461,session_010309,44,1,13.99,13.99,completed,2026-01-22 15:53:43,124403
643,150,session_010308,125,2,71.99,143.98,completed,2026-01-22 15:54:36,124410
644,108,session_010329,217,1,90.99,90.99,completed,2026-01-22 17:21:58,124668
645,1175,session_010339,181,1,204.99,204.99,completed,2026-01-22 17:45:27,124769
646,2118,session_010343,174,1,190.99,190.99,completed,2026-01-22 18:05:14,124890
647,1712,session_010355,63,1,20.99,20.99,completed,2026-01-22 18:13:47,124927
648,189,session_010370,189,1,56.99,56.99,completed,2026-01-22 18:52:08,125150
649,536,session_010417,148,2,8.49,16.98,completed,2026-01-22 19:59:02,125619
650,167,session_010450,128,1,51.99,51.99,completed,2026-01-22 20:54:48,125979
651,1712,session_010503,51,1,11.99,11.99,completed,2026-01-22 22:28:27,126502
652,298,session_010526,111,1,8.49,8.49,completed,2026-01-22 23:29:37,126798
653,1386,session_010553,27,1,81.99,81.99,completed,2026-01-23 01:33:43,127130
654,2324,session_010551,13,1,17.99,17.99,completed,2026-01-23 01:47:23,127158
655,30,session_010626,67,1,45.99,45.99,completed,2026-01-23 10:20:54,128170
656,2676,session_010631,116,2,85.99,171.98,completed,2026-01-23 10:20:56,128171
657,634,session_010634,105,1,59.99,59.99,completed,2026-01-23 10:43:44,128211
658,2797,session_010636,138,1,14.99,14.99,completed,2026-01-23 10:57:21,128241
659,2580,session_010638,218,1,64.99,64.99,completed,2026-01-23 11:05:35,128299
660,1611,session_010642,109,1,31.99,31.99,completed,2026-01-23 11:12:00,128319
661,602,session_010653,23,1,109.99,109.99,completed,2026-01-23 11:43:02,128410
662,595,session_010672,49,1,15.99,15.99,completed,2026-01-23 12:31:29,128679
663,2548,session_010694,80,1,37.99,37.99,completed,2026-01-23 13:34:17,129065
664,23,session_010745,102,1,35.99,35.99,completed,2026-01-23 15:22:44,129578
665,2360,session_010762,194,1,154.99,154.99,completed,2026-01-23 16:04:21,129856
665,2360,session_010762,178,1,561.99,561.99,completed,2026-01-23 16:04:23,129857
666,2887,session_010776,223,1,34.99,34.99,completed,2026-01-23 16:38:37,129996
667,1271,session_010779,110,1,9.49,9.49,completed,2026-01-23 16:48:22,130011
668,2571,session_010817,223,1,34.99,34.99,completed,2026-01-23 18:34:34,130538
669,2100,session_010864,40,1,130.99,130.99,completed,2026-01-23 20:09:43,131078
670,2753,session_010881,124,1,51.99,51.99,completed,2026-01-23 20:34:39,131301
671,2445,session_010897,37,1,39.99,39.99,completed,2026-01-23 21:10:36,131551
672,1671,session_010909,2,2,263.99,527.98,completed,2026-01-23 21:20:42,131652
673,1704,session_010984,168,2,4.49,8.98,completed,2026-01-23 23:59:49,132501
674,1979,session_011008,6,1,265.99,265.99,completed,2026-01-24 02:14:17,132764
675,699,session_011011,127,1,37.99,37.99,completed,2026-01-24 02:31:54,132805
676,2083,session_011028,12,1,24.99,24.99,completed,2026-01-24 07:51:42,133005
677,2423,session_011050,49,1,15.99,15.99,completed,2026-01-24 09:27:08,133246
678,230,session_011057,43,1,23.99,23.99,completed,2026-01-24 09:54:00,133324
679,1309,session_011069,130,2,57.99,115.98,completed,2026-01-24 10:32:24,133462
679,1309,session_011069,146,1,7.49,7.49,completed,2026-01-24 10:32:26,133463
680,2157,session_011100,200,1,30.99,30.99,completed,2026-01-24 12:08:20,133797
681,2297,session_011125,6,1,265.99,265.99,completed,2026-01-24 12:53:51,133997
682,1558,session_011143,154,1,7.49,7.49,completed,2026-01-24 13:42:32,134257
683,1137,session_011147,231,1,76.99,76.99,completed,2026-01-24 13:58:25,134301
684,1660,session_011161,110,1,9.49,9.49,completed,2026-01-24 14:47:27,134488
685,2214,session_011163,239,1,8.49,8.49,completed,2026-01-24 14:52:13,134519
686,728,session_011166,197,1,10.99,10.99,completed,2026-01-24 14:54:27,134532
687,2328,session_011195,171,1,235.99,235.99,completed,2026-01-24 16:04:43,134894
688,1976,session_011223,209,1,106.99,106.99,completed,2026-01-24 16:50:50,135191
689,274,session_011258,167,2,3.49,6.98,completed,2026-01-24 17:48:54,135611
690,895,session_011268,231,1,76.99,76.99,completed,2026-01-24 18:02:53,135763
691,719,session_011363,181,1,204.99,204.99,completed,2026-01-24 20:24:51,136928
692,421,session_011373,145,1,10.99,10.99,completed,2026-01-24 20:45:25,137050
693,2313,session_011380,216,1,19.99,19.99,completed,2026-01-24 20:54:23,137126
694,1586,session_011509,72,1,129.99,129.99,completed,2026-01-25 07:19:48,138594
695,409,session_011510,232,1,162.99,162.99,completed,2026-01-25 07:20:53,138599
695,409,session_011510,203,1,19.99,19.99,completed,2026-01-25 07:20:55,138600
696,2046,session_011513,44,1,13.99,13.99,completed,2026-01-25 07:41:44,138723
696,2046,session_011513,52,1,17.99,17.99,completed,2026-01-25 07:41:46,138724
697,2316,session_011523,177,1,241.99,241.99,completed,2026-01-25 08:20:47,138826
698,2224,session_011549,148,1,8.49,8.49,completed,2026-01-25 09:08:06,139070
699,2738,session_011559,9,1,142.99,142.99,completed,2026-01-25 09:38:22,139200
700,1002,session_011579,184,1,89.99,89.99,completed,2026-01-25 10:35:35,139424
700,1002,session_011579,87,1,103.99,103.99,completed,2026-01-25 10:35:37,139425
701,1250,session_011616,21,1,28.99,28.99,completed,2026-01-25 11:24:53,139867
702,1342,session_011638,110,2,9.49,18.98,completed,2026-01-25 11:59:14,140085
703,1595,session_011644,203,1,19.99,19.99,completed,2026-01-25 12:15:16,140183
704,601,session_011657,206,1,85.99,85.99,completed,2026-01-25 12:33:49,140331
705,762,session_011710,236,2,36.99,73.98,completed,2026-01-25 14:05:10,140799
706,2815,session_011714,161,3,5.49,16.47,completed,2026-01-25 14:31:13,141040
707,962,session_011759,148,2,8.49,16.98,completed,2026-01-25 15:47:50,141554
708,2999,session_011850,148,3,8.49,25.47,completed,2026-01-25 18:09:23,142559
708,2999,session_011850,160,2,5.49,10.98,completed,2026-01-25 18:09:25,142560
709,2958,session_011893,160,2,5.49,10.98,completed,2026-01-25 19:03:55,143057
710,1833,session_011929,231,1,76.99,76.99,completed,2026-01-25 19:35:52,143425
711,979,session_011931,17,1,478.99,478.99,completed,2026-01-25 19:49:24,143603
712,2447,session_012022,158,1,5.49,5.49,completed,2026-01-25 21:20:22,144383
713,217,session_012032,198,1,11.99,11.99,completed,2026-01-25 21:41:28,144550
714,2978,session_012035,118,3,6.49,19.47,completed,2026-01-25 21:54:34,144614
715,2050,session_012075,235,1,25.99,25.99,completed,2026-01-25 22:52:17,145067
716,1419,session_012077,85,1,61.99,61.99,completed,2026-01-25 22:54:24,145075
717,544,session_012082,234,1,13.99,13.99,completed,2026-01-25 23:10:21,145175
718,1804,session_012105,200,1,30.99,30.99,completed,2026-01-25 23:57:16,145364
719,2984,session_012114,65,1,96.99,96.99,completed,2026-01-26 00:21:57,145480
720,2873,session_012119,68,2,116.99,233.98,completed,2026-01-26 00:58:06,145518
721,1030,session_012135,150,1,7.49,7.49,completed,2026-01-26 04:02:44,145705
722,2018,session_012140,2,2,263.99,527.98,completed,2026-01-26 05:06:58,145739
723,2799,session_012164,184,2,89.99,179.98,completed,2026-01-26 07:47:15,145999
724,1718,session_012170,41,1,158.99,158.99,completed,2026-01-26 08:13:30,146037
725,1662,session_012183,2,1,263.99,263.99,completed,2026-01-26 09:17:19,146204
725,1662,session_012183,160,2,5.49,10.98,completed,2026-01-26 09:17:21,146205
726,2676,session_012190,148,1,8.49,8.49,completed,2026-01-26 09:38:36,146351
727,277,session_012195,223,1,34.99,34.99,completed,2026-01-26 09:39:12,146359
728,394,session_012201,6,1,265.99,265.99,completed,2026-01-26 10:02:36,146436
728,394,session_012201,203,1,19.99,19.99,completed,2026-01-26 10:02:38,146438
729,215,session_012206,160,1,5.49,5.49,completed,2026-01-26 10:16:16,146487
730,1892,session_012216,18,1,373.99,373.99,completed,2026-01-26 10:29:16,146572
730,1892,session_012216,37,1,39.99,39.99,completed,2026-01-26 10:29:18,146573
731,2387,session_012222,206,1,85.99,85.99,completed,2026-01-26 10:53:15,146675
732,2309,session_012259,60,1,14.99,14.99,completed,2026-01-26 11:52:01,146929
733,204,session_012298,93,1,23.99,23.99,completed,2026-01-26 13:07:45,147440
734,1429,session_012303,148,1,8.49,8.49,completed,2026-01-26 13:12:36,147513
735,130,session_012330,190,1,183.99,183.99,completed,2026-01-26 14:03:31,147805
736,1275,session_012341,223,1,34.99,34.99,completed,2026-01-26 14:31:08,147947
736,1275,session_012341,215,1,14.99,14.99,completed,2026-01-26 14:31:10,147948
737,2036,session_012362,184,1,89.99,89.99,completed,2026-01-26 15:12:57,148196
738,1241,session_012370,228,1,29.99,29.99,completed,2026-01-26 15:37:53,148264
739,2107,session_012378,1,1,185.99,185.99,completed,2026-01-26 15:59:30,148353
739,2107,session_012378,7,1,336.99,336.99,completed,2026-01-26 15:59:32,148354
740,2311,session_012404,90,1,23.99,23.99,completed,2026-01-26 17:00:44,148697
741,2873,session_012436,76,1,46.99,46.99,completed,2026-01-26 17:45:30,148943
742,375,session_012438,243,1,53.99,53.99,completed,2026-01-26 17:46:09,148947
743,1219,session_012441,127,1,37.99,37.99,completed,2026-01-26 17:49:48,148959
744,2254,session_012461,26,1,100.99,100.99,completed,2026-01-26 18:30:44,149300
745,125,session_012477,49,1,15.99,15.99,completed,2026-01-26 19:03:22,149464
746,2879,session_012474,215,1,14.99,14.99,completed,2026-01-26 19:04:13,149470
747,834,session_012493,225,1,9.49,9.49,completed,2026-01-26 19:23:59,149645
748,2798,session_012494,2,1,263.99,263.99,completed,2026-01-26 19:42:42,149839
749,2913,session_012538,177,1,241.99,241.99,completed,2026-01-26 20:26:40,150309
750,1219,session_012536,128,1,51.99,51.99,completed,2026-01-26 20:40:48,150493
751,2414,session_012582,115,2,9.49,18.98,completed,2026-01-26 21:05:03,150847
752,908,session_012630,85,1,61.99,61.99,completed,2026-01-26 22:06:38,151315
753,69,session_012639,200,2,30.99,61.98,completed,2026-01-26 22:26:57,151421
754,149,session_012634,168,1,4.49,4.49,completed,2026-01-26 22:27:07,151424
755,658,session_012644,65,1,96.99,96.99,completed,2026-01-26 22:36:46,151533
756,1760,session_012650,90,1,23.99,23.99,completed,2026-01-26 22:54:08,151681
757,193,session_012669,19,1,140.99,140.99,completed,2026-01-26 23:20:05,151774
758,620,session_012683,133,1,23.99,23.99,completed,2026-01-27 00:08:57,151884
759,515,session_012726,208,1,57.99,57.99,completed,2026-01-27 08:02:24,152393
759,515,session_012726,52,1,17.99,17.99,completed,2026-01-27 08:02:26,152394
760,2427,session_012735,133,1,23.99,23.99,completed,2026-01-27 08:07:05,152432
761,638,session_012740,74,1,36.99,36.99,completed,2026-01-27 08:28:30,152508
762,2831,session_012741,87,1,103.99,103.99,completed,2026-01-27 08:46:17,152565
763,2298,session_012765,21,1,28.99,28.99,completed,2026-01-27 10:18:34,152816
764,2466,session_012796,208,1,57.99,57.99,completed,2026-01-27 11:29:35,153142
764,2466,session_012796,223,1,34.99,34.99,completed,2026-01-27 11:29:37,153143
765,2111,session_012798,89,1,32.99,32.99,completed,2026-01-27 11:48:52,153288
766,1712,session_012834,238,1,15.99,15.99,completed,2026-01-27 12:40:56,153606
767,2075,session_012833,52,1,17.99,17.99,completed,2026-01-27 12:46:36,153625
767,2075,session_012833,49,1,15.99,15.99,completed,2026-01-27 12:46:38,153627
768,2549,session_012849,184,1,89.99,89.99,completed,2026-01-27 13:03:57,153755
769,180,session_012851,52,1,17.99,17.99,completed,2026-01-27 13:14:36,153790
770,1165,session_012853,160,2,5.49,10.98,completed,2026-01-27 13:24:03,153841
771,395,session_012862,18,1,373.99,373.99,completed,2026-01-27 13:42:22,153996
772,1964,session_012883,229,1,64.99,64.99,completed,2026-01-27 14:02:06,154203
773,2799,session_012881,158,2,5.49,10.98,completed,2026-01-27 14:02:49,154210
774,2146,session_012885,97,1,32.99,32.99,completed,2026-01-27 14:13:22,154245
775,2382,session_012961,12,1,24.99,24.99,completed,2026-01-27 17:37:46,155104
776,2967,session_012963,125,1,71.99,71.99,completed,2026-01-27 17:38:46,155105
777,2900,session_012967,1,1,185.99,185.99,completed,2026-01-27 17:56:48,155232
778,1503,session_012969,82,1,25.99,25.99,completed,2026-01-27 17:58:55,155245
779,519,session_013009,148,2,8.49,16.98,completed,2026-01-27 18:55:34,155634
780,2375,session_013032,140,1,63.99,63.99,completed,2026-01-27 19:33:54,156000
781,1229,session_013031,85,1,61.99,61.99,completed,2026-01-27 19:41:38,156102
782,1067,session_013057,223,1,34.99,34.99,completed,2026-01-27 19:59:16,156299
783,2740,session_013063,189,1,56.99,56.99,completed,2026-01-27 20:01:19,156315
784,2382,session_013059,56,1,14.99,14.99,completed,2026-01-27 20:06:05,156356
785,1660,session_013074,37,1,39.99,39.99,completed,2026-01-27 20:16:53,156482
785,1660,session_013074,108,1,48.99,48.99,completed,2026-01-27 20:16:55,156483
786,1175,session_013083,85,1,61.99,61.99,completed,2026-01-27 20:33:22,156612
787,1009,session_013100,125,1,71.99,71.99,completed,2026-01-27 21:01:36,156844
788,1962,session_013103,65,1,96.99,96.99,completed,2026-01-27 21:15:22,156925
789,2216,session_013112,134,1,47.99,47.99,completed,2026-01-27 21:16:13,156929
789,2216,session_013112,133,1,23.99,23.99,completed,2026-01-27 21:16:15,156930
790,2423,session_013130,63,1,20.99,20.99,completed,2026-01-27 21:46:19,157110
791,2846,session_013202,234,1,13.99,13.99,completed,2026-01-28 00:49:51,157868
792,637,session_013233,108,3,48.99,146.97,completed,2026-01-28 07:51:18,158217
793,1753,session_013236,76,1,46.99,46.99,completed,2026-01-28 08:06:16,158248
794,2876,session_013257,118,2,6.49,12.98,completed,2026-01-28 09:26:44,158476
795,806,session_013308,111,1,8.49,8.49,completed,2026-01-28 11:43:04,159000
796,1802,session_013360,83,1,40.99,40.99,completed,2026-01-28 13:36:40,159701
797,525,session_013381,148,2,8.49,16.98,completed,2026-01-28 14:34:49,160082
798,1766,session_013383,161,2,5.49,10.98,completed,2026-01-28 14:39:42,160132
799,2453,session_013411,231,1,76.99,76.99,completed,2026-01-28 15:52:38,160282
800,961,session_013466,27,1,81.99,81.99,completed,2026-01-28 18:09:50,160883
801,281,session_013546,181,1,204.99,204.99,completed,2026-01-28 20:20:45,161718
802,2654,session_013547,9,1,142.99,142.99,completed,2026-01-28 20:21:45,161721
803,277,session_013590,154,1,7.49,7.49,completed,2026-01-28 21:06:01,162231
804,1660,session_013628,52,1,17.99,17.99,completed,2026-01-28 22:05:58,162735
805,706,session_013626,137,1,32.99,32.99,completed,2026-01-28 22:07:13,162740
806,446,session_013633,25,1,73.99,73.99,completed,2026-01-28 22:21:41,162847
807,69,session_013650,94,1,50.99,50.99,completed,2026-01-28 22:54:17,163141
808,2340,session_013666,86,1,84.99,84.99,completed,2026-01-28 23:01:14,163199
809,260,session_013667,212,1,172.99,172.99,completed,2026-01-28 23:05:13,163221
810,795,session_013689,36,1,117.99,117.99,completed,2026-01-29 00:48:47,163458
811,2819,session_013707,137,2,32.99,65.98,completed,2026-01-29 02:43:57,163623
812,396,session_013716,37,1,39.99,39.99,completed,2026-01-29 06:34:22,163760
813,2740,session_013736,100,1,122.99,122.99,completed,2026-01-29 08:06:11,163916
814,2804,session_013737,207,2,32.99,65.98,completed,2026-01-29 08:10:14,163925
815,2984,session_013742,200,1,30.99,30.99,completed,2026-01-29 08:38:43,164035
816,787,session_013754,41,2,158.99,317.98,completed,2026-01-29 08:54:00,164129
817,2505,session_013779,107,1,31.99,31.99,completed,2026-01-29 09:48:10,164456
818,314,session_013795,161,2,5.49,10.98,completed,2026-01-29 10:40:43,164705
819,1030,session_013798,73,1,76.99,76.99,completed,2026-01-29 10:58:48,164767
820,1465,session_013809,37,1,39.99,39.99,completed,2026-01-29 11:33:20,164921
821,571,session_013869,160,3,5.49,16.47,completed,2026-01-29 13:26:41,165463
822,896,session_013891,28,1,109.99,109.99,completed,2026-01-29 14:25:22,165744
823,1330,session_013897,179,1,763.99,763.99,completed,2026-01-29 14:42:34,165799
824,903,session_013904,37,1,39.99,39.99,completed,2026-01-29 14:56:20,165873
825,2917,session_013915,177,1,241.99,241.99,completed,2026-01-29 15:13:32,165975
826,37,session_013919,200,1,30.99,30.99,completed,2026-01-29 15:29:13,166108
826,37,session_013919,194,1,154.99,154.99,completed,2026-01-29 15:29:15,166109
827,1802,session_013921,109,1,31.99,31.99,completed,2026-01-29 15:39:15,166170
828,912,session_013925,58,1,8.49,8.49,completed,2026-01-29 15:41:56,166211
829,1391,session_013929,243,1,53.99,53.99,completed,2026-01-29 15:49:39,166298
830,2453,session_013943,9,1,142.99,142.99,completed,2026-01-29 16:08:52,166376
831,2376,session_014013,208,1,57.99,57.99,completed,2026-01-29 18:37:59,167230
832,818,session_014021,87,1,103.99,103.99,completed,2026-01-29 18:41:18,167264
833,394,session_014036,127,1,37.99,37.99,completed,2026-01-29 19:12:05,167629
834,1432,session_014046,221,1,149.99,149.99,completed,2026-01-29 19:34:14,167779
835,2919,session_014055,184,1,89.99,89.99,completed,2026-01-29 19:41:37,167846
836,1503,session_014060,76,1,46.99,46.99,completed,2026-01-29 19:46:05,167904
836,1503,session_014060,80,1,37.99,37.99,completed,2026-01-29 19:46:07,167905
837,1671,session_014092,231,1,76.99,76.99,completed,2026-01-29 20:35:51,168206
838,1670,session_014125,20,2,253.99,507.98,completed,2026-01-29 21:27:43,168625
839,766,session_014149,236,1,36.99,36.99,completed,2026-01-29 22:06:21,168946
840,67,session_014157,127,1,37.99,37.99,completed,2026-01-29 22:14:18,169026
841,629,session_014180,76,1,46.99,46.99,completed,2026-01-29 23:04:24,169308
842,1063,session_014204,127,1,37.99,37.99,completed,2026-01-30 00:11:05,169503
843,724,session_014250,174,1,190.99,190.99,completed,2026-01-30 08:29:04,170152
843,724,session_014250,156,1,7.49,7.49,completed,2026-01-30 08:29:06,170153
844,1152,session_014264,184,1,89.99,89.99,completed,2026-01-30 09:06:15,170354
844,1152,session_014264,174,1,190.99,190.99,completed,2026-01-30 09:06:17,170355
845,1161,session_014331,96,1,243.99,243.99,completed,2026-01-30 12:08:28,171222
846,2693,session_014350,111,3,8.49,25.47,completed,2026-01-30 12:41:17,171422
847,1378,session_014355,49,1,15.99,15.99,completed,2026-01-30 12:50:44,171480
848,1738,session_014365,175,1,167.99,167.99,completed,2026-01-30 12:54:39,171497
849,417,session_014388,184,1,89.99,89.99,completed,2026-01-30 13:46:09,171808
850,2638,session_014395,74,1,36.99,36.99,completed,2026-01-30 13:55:08,171880
851,399,session_014423,74,1,36.99,36.99,completed,2026-01-30 14:45:32,172233
852,1325,session_014439,252,1,15.99,15.99,completed,2026-01-30 15:53:55,172464
853,2466,session_014450,185,1,98.99,98.99,completed,2026-01-30 16:17:13,172594
854,2979,session_014457,105,1,59.99,59.99,completed,2026-01-30 16:34:15,172688
855,1061,session_014578,232,1,162.99,162.99,completed,2026-01-30 19:29:54,174006
856,488,session_014663,169,1,440.99,440.99,completed,2026-01-30 21:44:33,175071
857,235,session_014669,63,1,20.99,20.99,completed,2026-01-30 21:47:46,175087
858,409,session_014680,68,1,116.99,116.99,completed,2026-01-30 22:00:37,175176
859,204,session_014721,179,1,763.99,763.99,completed,2026-01-30 23:42:00,175610
860,2036,session_014720,188,1,141.99,141.99,completed,2026-01-30 23:44:27,175615
861,1900,session_014729,99,1,372.99,372.99,completed,2026-01-31 00:17:36,175701
862,93,session_014763,52,1,17.99,17.99,completed,2026-01-31 04:45:40,176024
863,140,session_014762,225,1,9.49,9.49,completed,2026-01-31 05:01:30,176051
863,140,session_014762,231,1,76.99,76.99,completed,2026-01-31 05:01:32,176052
863,140,session_014762,160,1,5.49,5.49,completed,2026-01-31 05:01:34,176053
864,1330,session_014765,193,1,92.99,92.99,completed,2026-01-31 05:44:54,176088
865,2739,session_014784,249,1,7.49,7.49,completed,2026-01-31 07:51:10,176390
866,2799,session_014835,101,1,67.99,67.99,completed,2026-01-31 09:38:53,176934
867,1790,session_014826,223,2,34.99,69.98,completed,2026-01-31 09:49:38,176961
868,2076,session_014852,80,1,37.99,37.99,completed,2026-01-31 10:22:58,177153
869,2580,session_014854,141,1,17.99,17.99,completed,2026-01-31 10:26:12,177182
870,1803,session_014870,219,1,181.99,181.99,completed,2026-01-31 11:10:34,177408
871,2318,session_014878,80,1,37.99,37.99,completed,2026-01-31 11:23:08,177486
872,277,session_014932,110,1,9.49,9.49,completed,2026-01-31 12:50:47,178188
873,1419,session_014962,21,1,28.99,28.99,completed,2026-01-31 13:55:43,178663
873,1419,session_014962,3,1,765.99,765.99,completed,2026-01-31 13:55:45,178664
873,1419,session_014962,16,1,180.99,180.99,completed,2026-01-31 13:55:47,178665
874,1190,session_014972,148,1,8.49,8.49,completed,2026-01-31 14:01:54,178708
875,231,session_015044,169,1,440.99,440.99,completed,2026-01-31 16:18:20,179657
876,773,session_015056,125,3,71.99,215.97,completed,2026-01-31 16:40:57,179761
876,773,session_015056,100,1,122.99,122.99,completed,2026-01-31 16:40:59,179762
877,599,session_015081,90,1,23.99,23.99,completed,2026-01-31 17:14:42,180042
878,2075,session_015098,52,1,17.99,17.99,completed,2026-01-31 17:33:39,180246
879,74,session_015088,37,2,39.99,79.98,completed,2026-01-31 17:35:56,180265
879,74,session_015088,27,1,81.99,81.99,completed,2026-01-31 17:35:58,180266
880,2875,session_015125,63,1,20.99,20.99,completed,2026-01-31 18:27:30,180562
881,1213,session_015128,110,2,9.49,18.98,completed,2026-01-31 18:38:56,180659
881,1213,session_015128,129,1,16.99,16.99,completed,2026-01-31 18:38:58,180660
882,2919,session_015149,133,1,23.99,23.99,completed,2026-01-31 18:49:54,180743
883,2896,session_015168,6,1,265.99,265.99,completed,2026-01-31 19:35:04,181078
884,1490,session_015232,127,1,37.99,37.99,completed,2026-01-31 20:48:15,181791
885,585,session_015254,66,1,54.99,54.99,completed,2026-01-31 21:15:23,182111
886,893,session_015267,66,1,54.99,54.99,completed,2026-01-31 21:27:39,182279
887,1384,session_015320,103,1,13.99,13.99,completed,2026-01-31 22:33:28,182951
888,2926,session_015335,40,1,130.99,130.99,completed,2026-01-31 22:59:46,183142
889,938,session_015328,191,1,65.99,65.99,completed,2026-01-31 23:01:50,183151
889,938,session_015328,31,1,14.99,14.99,completed,2026-01-31 23:01:52,183152
890,306,session_015336,181,1,204.99,204.99,completed,2026-01-31 23:02:57,183154
891,2740,session_015350,105,1,59.99,59.99,completed,2026-01-31 23:32:34,183340
892,2736,session_015346,24,2,106.99,213.98,completed,2026-01-31 23:35:04,183343
893,66,session_015357,2,1,263.99,263.99,completed,2026-01-31 23:59:10,183459
```

### data/products.csv

```
product_id,name,slug,description,img_url,category_id,price,created_at
1,Smartphone Compact 686,smartphone-compact-686,"5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",/images/products/smartphone-compact-686.jpg,1,185.99,2025-05-14
2,Smartphone Compact 854,smartphone-compact-854,"5G smartphone with OLED display, dual camera and fast charging. Compact line, red.",/images/products/smartphone-compact-854.jpg,1,263.99,2025-10-15
3,Laptop Compact 775,laptop-compact-775,"Lightweight laptop for work and study, SSD storage, long battery life. Compact line, grey.",/images/products/laptop-compact-775.jpg,1,765.99,2025-08-20
4,Laptop Classic 505,laptop-classic-505,"Lightweight laptop for work and study, SSD storage, long battery life. Classic line, silver.",/images/products/laptop-classic-505.jpg,1,1393.99,2025-04-21
5,Headphones Deluxe 350,headphones-deluxe-350,"Wireless over-ear headphones with noise cancelling and 30h battery. Deluxe line, grey.",/images/products/headphones-deluxe-350.jpg,1,71.99,2025-07-02
6,Headphones Compact 103,headphones-compact-103,"Wireless over-ear headphones with noise cancelling and 30h battery. Compact line, grey.",/images/products/headphones-compact-103.jpg,1,265.99,2025-03-04
7,Tablet Compact 853,tablet-compact-853,"10-inch tablet for streaming, reading and video calls. Compact line, red.",/images/products/tablet-compact-853.jpg,1,336.99,2025-10-09
8,Tablet Essential 949,tablet-essential-949,"10-inch tablet for streaming, reading and video calls. Essential line, red.",/images/products/tablet-essential-949.jpg,1,725.99,2025-11-07
9,Monitor Premium 997,monitor-premium-997,"27-inch IPS monitor, full HD, slim bezel, for office and gaming. Premium line, black.",/images/products/monitor-premium-997.jpg,1,142.99,2025-10-20
10,Monitor Classic 784,monitor-classic-784,"27-inch IPS monitor, full HD, slim bezel, for office and gaming. Classic line, white.",/images/products/monitor-classic-784.jpg,1,200.99,2025-10-15
11,Keyboard Everyday 369,keyboard-everyday-369,"Mechanical keyboard with backlight, quiet switches. Everyday line, red.",/images/products/keyboard-everyday-369.jpg,1,21.99,2025-08-30
12,Keyboard Classic 505,keyboard-classic-505,"Mechanical keyboard with backlight, quiet switches. Classic line, red.",/images/products/keyboard-classic-505.jpg,1,24.99,2025-07-14
13,Mouse Deluxe 406,mouse-deluxe-406,"Ergonomic wireless mouse with silent clicks. Deluxe line, red.",/images/products/mouse-deluxe-406.jpg,1,17.99,2025-07-31
14,Mouse Eco 475,mouse-eco-475,"Ergonomic wireless mouse with silent clicks. Eco line, blue.",/images/products/mouse-eco-475.jpg,1,11.99,2025-09-05
15,Speaker Pro 628,speaker-pro-628,"Portable bluetooth speaker, waterproof, deep bass. Pro line, black.",/images/products/speaker-pro-628.jpg,1,101.99,2025-10-04
16,Speaker Eco 174,speaker-eco-174,"Portable bluetooth speaker, waterproof, deep bass. Eco line, red.",/images/products/speaker-eco-174.jpg,1,180.99,2025-05-06
17,Camera Compact 359,camera-compact-359,"Mirrorless camera with 4K video and interchangeable lens. Compact line, black.",/images/products/camera-compact-359.jpg,1,478.99,2025-04-25
18,Camera Everyday 481,camera-everyday-481,"Mirrorless camera with 4K video and interchangeable lens. Everyday line, red.",/images/products/camera-everyday-481.jpg,1,373.99,2025-08-20
19,Smartwatch Premium 103,smartwatch-premium-103,"Fitness smartwatch with heart rate, GPS and sleep tracking. Premium line, beige.",/images/products/smartwatch-premium-103.jpg,1,140.99,2025-10-22
20,Smartwatch Everyday 615,smartwatch-everyday-615,"Fitness smartwatch with heart rate, GPS and sleep tracking. Everyday line, beige.",/images/products/smartwatch-everyday-615.jpg,1,253.99,2025-04-04
21,Keyboard Compact 874,keyboard-compact-874,"Mechanical keyboard with backlight, quiet switches. Compact line, grey.",/images/products/keyboard-compact-874.jpg,1,28.99,2025-04-11
22,Jacket Compact 350,jacket-compact-350,"Warm winter jacket, water-repellent, hooded. Compact line, silver.",/images/products/jacket-compact-350.jpg,2,123.99,2025-08-11
23,Jacket Essential 819,jacket-essential-819,"Warm winter jacket, water-repellent, hooded. Essential line, silver.",/images/products/jacket-essential-819.jpg,2,109.99,2025-10-10
24,Jeans Premium 253,jeans-premium-253,"Slim fit denim jeans, stretch cotton. Premium line, silver.",/images/products/jeans-premium-253.jpg,2,106.99,2025-07-14
25,Jeans Essential 168,jeans-essential-168,"Slim fit denim jeans, stretch cotton. Essential line, grey.",/images/products/jeans-essential-168.jpg,2,73.99,2025-08-30
26,Sneakers Deluxe 539,sneakers-deluxe-539,"Everyday sneakers, breathable mesh, cushioned sole. Deluxe line, silver.",/images/products/sneakers-deluxe-539.jpg,2,100.99,2025-09-02
27,Sneakers Compact 248,sneakers-compact-248,"Everyday sneakers, breathable mesh, cushioned sole. Compact line, green.",/images/products/sneakers-compact-248.jpg,2,81.99,2025-06-16
28,Dress Essential 892,dress-essential-892,"Midi dress for office and evening, soft fabric. Essential line, white.",/images/products/dress-essential-892.jpg,2,109.99,2025-08-21
29,Dress Pro 538,dress-pro-538,"Midi dress for office and evening, soft fabric. Pro line, beige.",/images/products/dress-pro-538.jpg,2,87.99,2025-07-23
30,T-shirt Everyday 987,t-shirt-everyday-987,"Basic cotton t-shirt, regular fit. Everyday line, red.",/images/products/t-shirt-everyday-987.jpg,2,34.99,2025-04-29
31,T-shirt Classic 854,t-shirt-classic-854,"Basic cotton t-shirt, regular fit. Classic line, grey.",/images/products/t-shirt-classic-854.jpg,2,14.99,2025-08-25
32,Scarf Eco 733,scarf-eco-733,"Knitted wool scarf for winter. Eco line, silver.",/images/products/scarf-eco-733.jpg,2,32.99,2025-11-24
33,Scarf Eco 599,scarf-eco-599,"Knitted wool scarf for winter. Eco line, green.",/images/products/scarf-eco-599.jpg,2,37.99,2025-09-13
34,Belt Eco 953,belt-eco-953,"Genuine leather belt with metal buckle. Eco line, grey.",/images/products/belt-eco-953.jpg,2,65.99,2025-11-07
35,Belt Eco 785,belt-eco-785,"Genuine leather belt with metal buckle. Eco line, red.",/images/products/belt-eco-785.jpg,2,17.99,2025-09-14
36,Backpack Classic 759,backpack-classic-759,"City backpack with laptop sleeve, water-resistant. Classic line, silver.",/images/products/backpack-classic-759.jpg,2,117.99,2025-09-25
37,Backpack Compact 926,backpack-compact-926,"City backpack with laptop sleeve, water-resistant. Compact line, grey.",/images/products/backpack-compact-926.jpg,2,39.99,2025-05-24
38,Cap Compact 731,cap-compact-731,"Cotton baseball cap, adjustable. Compact line, white.",/images/products/cap-compact-731.jpg,2,31.99,2025-08-20
39,Cap Everyday 356,cap-everyday-356,"Cotton baseball cap, adjustable. Everyday line, red.",/images/products/cap-everyday-356.jpg,2,25.99,2025-10-24
40,Boots Compact 582,boots-compact-582,"Leather winter boots, non-slip sole. Compact line, black.",/images/products/boots-compact-582.jpg,2,130.99,2025-11-13
41,Boots Compact 911,boots-compact-911,"Leather winter boots, non-slip sole. Compact line, black.",/images/products/boots-compact-911.jpg,2,158.99,2025-08-31
42,Jacket Pro 710,jacket-pro-710,"Warm winter jacket, water-repellent, hooded. Pro line, blue.",/images/products/jacket-pro-710.jpg,2,216.99,2025-07-09
43,Novel Premium 556,novel-premium-556,"Bestselling contemporary novel, paperback. Premium line, red.",/images/products/novel-premium-556.jpg,3,23.99,2025-08-03
44,Novel Premium 964,novel-premium-964,"Bestselling contemporary novel, paperback. Premium line, green.",/images/products/novel-premium-964.jpg,3,13.99,2025-07-14
45,Thriller Compact 230,thriller-compact-230,"Crime thriller, gripping page-turner. Compact line, black.",/images/products/thriller-compact-230.jpg,3,11.99,2025-05-12
46,Thriller Premium 108,thriller-premium-108,"Crime thriller, gripping page-turner. Premium line, beige.",/images/products/thriller-premium-108.jpg,3,10.99,2025-11-21
47,Cookbook Premium 243,cookbook-premium-243,"Cookbook with healthy everyday recipes. Premium line, blue.",/images/products/cookbook-premium-243.jpg,3,30.99,2025-04-10
48,Cookbook Essential 136,cookbook-essential-136,"Cookbook with healthy everyday recipes. Essential line, white.",/images/products/cookbook-essential-136.jpg,3,43.99,2025-11-18
49,Biography Deluxe 648,biography-deluxe-648,"Biography of a famous entrepreneur. Deluxe line, silver.",/images/products/biography-deluxe-648.jpg,3,15.99,2025-05-21
50,Biography Essential 819,biography-essential-819,"Biography of a famous entrepreneur. Essential line, white.",/images/products/biography-essential-819.jpg,3,23.99,2025-05-16
51,Fantasy Premium 823,fantasy-premium-823,"Epic fantasy saga, first book in the series. Premium line, white.",/images/products/fantasy-premium-823.jpg,3,11.99,2025-09-30
52,Fantasy Pro 681,fantasy-pro-681,"Epic fantasy saga, first book in the series. Pro line, blue.",/images/products/fantasy-pro-681.jpg,3,17.99,2025-11-24
53,Textbook Deluxe 723,textbook-deluxe-723,"University textbook on marketing and statistics. Deluxe line, beige.",/images/products/textbook-deluxe-723.jpg,3,56.99,2025-10-20
54,Textbook Eco 847,textbook-eco-847,"University textbook on marketing and statistics. Eco line, silver.",/images/products/textbook-eco-847.jpg,3,87.99,2025-03-03
55,Guide Everyday 453,guide-everyday-453,"Travel guide with maps and itineraries. Everyday line, white.",/images/products/guide-everyday-453.jpg,3,26.99,2025-11-03
56,Guide Eco 397,guide-eco-397,"Travel guide with maps and itineraries. Eco line, beige.",/images/products/guide-eco-397.jpg,3,14.99,2025-04-15
57,Children's Book Premium 257,childrens-book-premium-257,"Illustrated picture book for children. Premium line, blue.",/images/products/childrens-book-premium-257.jpg,3,9.49,2025-04-29
58,Children's Book Deluxe 173,childrens-book-deluxe-173,"Illustrated picture book for children. Deluxe line, silver.",/images/products/childrens-book-deluxe-173.jpg,3,8.49,2025-05-25
59,Poetry Classic 204,poetry-classic-204,"Collection of modern poetry. Classic line, white.",/images/products/poetry-classic-204.jpg,3,8.49,2025-10-07
60,Poetry Everyday 604,poetry-everyday-604,"Collection of modern poetry. Everyday line, beige.",/images/products/poetry-everyday-604.jpg,3,14.99,2025-04-15
61,Dictionary Essential 458,dictionary-essential-458,"English-Serbian dictionary, updated edition. Essential line, beige.",/images/products/dictionary-essential-458.jpg,3,24.99,2025-08-11
62,Dictionary Compact 106,dictionary-compact-106,"English-Serbian dictionary, updated edition. Compact line, blue.",/images/products/dictionary-compact-106.jpg,3,17.99,2025-04-25
63,Cookbook Compact 232,cookbook-compact-232,"Cookbook with healthy everyday recipes. Compact line, white.",/images/products/cookbook-compact-232.jpg,3,20.99,2025-07-18
64,Running Shoes Pro 936,running-shoes-pro-936,"Running shoes with responsive cushioning. Pro line, blue.",/images/products/running-shoes-pro-936.jpg,4,104.99,2025-11-08
65,Running Shoes Deluxe 803,running-shoes-deluxe-803,"Running shoes with responsive cushioning. Deluxe line, beige.",/images/products/running-shoes-deluxe-803.jpg,4,96.99,2025-11-20
66,Yoga Mat Premium 817,yoga-mat-premium-817,"Non-slip yoga mat, eco-friendly material. Premium line, green.",/images/products/yoga-mat-premium-817.jpg,4,54.99,2025-03-14
67,Yoga Mat Everyday 759,yoga-mat-everyday-759,"Non-slip yoga mat, eco-friendly material. Everyday line, grey.",/images/products/yoga-mat-everyday-759.jpg,4,45.99,2025-07-12
68,Dumbbell Set Premium 193,dumbbell-set-premium-193,"Adjustable dumbbell set for home workouts. Premium line, silver.",/images/products/dumbbell-set-premium-193.jpg,4,116.99,2025-10-17
69,Dumbbell Set Pro 352,dumbbell-set-pro-352,"Adjustable dumbbell set for home workouts. Pro line, blue.",/images/products/dumbbell-set-pro-352.jpg,4,90.99,2025-09-01
70,Bicycle Compact 781,bicycle-compact-781,"City and trekking bicycle, aluminium frame, 21 gears. Compact line, black.",/images/products/bicycle-compact-781.jpg,4,251.99,2025-07-13
71,Bicycle Everyday 242,bicycle-everyday-242,"City and trekking bicycle, aluminium frame, 21 gears. Everyday line, green.",/images/products/bicycle-everyday-242.jpg,4,493.99,2025-11-21
72,Tent Classic 324,tent-classic-324,"Lightweight camping tent for two, waterproof. Classic line, black.",/images/products/tent-classic-324.jpg,4,129.99,2025-08-19
73,Tent Classic 332,tent-classic-332,"Lightweight camping tent for two, waterproof. Classic line, beige.",/images/products/tent-classic-332.jpg,4,76.99,2025-07-05
74,Football Deluxe 883,football-deluxe-883,"Official size football, durable. Deluxe line, black.",/images/products/football-deluxe-883.jpg,4,36.99,2025-07-09
75,Football Premium 903,football-premium-903,"Official size football, durable. Premium line, black.",/images/products/football-premium-903.jpg,4,41.99,2025-03-23
76,Tennis Racket Compact 416,tennis-racket-compact-416,"Graphite tennis racket for intermediate players. Compact line, grey.",/images/products/tennis-racket-compact-416.jpg,4,46.99,2025-09-26
77,Tennis Racket Classic 374,tennis-racket-classic-374,"Graphite tennis racket for intermediate players. Classic line, grey.",/images/products/tennis-racket-classic-374.jpg,4,47.99,2025-11-01
78,Sports Bottle Pro 464,sports-bottle-pro-464,"Insulated sports water bottle, leak-proof. Pro line, grey.",/images/products/sports-bottle-pro-464.jpg,4,9.49,2025-05-14
79,Sports Bottle Premium 411,sports-bottle-premium-411,"Insulated sports water bottle, leak-proof. Premium line, silver.",/images/products/sports-bottle-premium-411.jpg,4,6.49,2025-08-31
80,Fitness Band Eco 108,fitness-band-eco-108,"Resistance bands set for strength training. Eco line, blue.",/images/products/fitness-band-eco-108.jpg,4,37.99,2025-07-23
81,Fitness Band Deluxe 954,fitness-band-deluxe-954,"Resistance bands set for strength training. Deluxe line, red.",/images/products/fitness-band-deluxe-954.jpg,4,29.99,2025-07-10
82,Ski Gloves Eco 904,ski-gloves-eco-904,"Insulated ski gloves, waterproof. Eco line, beige.",/images/products/ski-gloves-eco-904.jpg,4,25.99,2025-03-10
83,Ski Gloves Premium 117,ski-gloves-premium-117,"Insulated ski gloves, waterproof. Premium line, black.",/images/products/ski-gloves-premium-117.jpg,4,40.99,2025-05-26
84,Bicycle Eco 162,bicycle-eco-162,"City and trekking bicycle, aluminium frame, 21 gears. Eco line, grey.",/images/products/bicycle-eco-162.jpg,4,552.99,2025-07-21
85,Blender Classic 334,blender-classic-334,"Kitchen blender for smoothies and soups. Classic line, beige.",/images/products/blender-classic-334.jpg,5,61.99,2025-05-01
86,Blender Everyday 283,blender-everyday-283,"Kitchen blender for smoothies and soups. Everyday line, red.",/images/products/blender-everyday-283.jpg,5,84.99,2025-06-23
87,Coffee Maker Pro 639,coffee-maker-pro-639,"Espresso coffee maker with milk frother. Pro line, green.",/images/products/coffee-maker-pro-639.jpg,5,103.99,2025-10-23
88,Coffee Maker Compact 260,coffee-maker-compact-260,"Espresso coffee maker with milk frother. Compact line, silver.",/images/products/coffee-maker-compact-260.jpg,5,176.99,2025-09-17
89,Table Lamp Deluxe 218,table-lamp-deluxe-218,"LED table lamp with dimmer, warm light. Deluxe line, white.",/images/products/table-lamp-deluxe-218.jpg,5,32.99,2025-11-04
90,Table Lamp Eco 643,table-lamp-eco-643,"LED table lamp with dimmer, warm light. Eco line, silver.",/images/products/table-lamp-eco-643.jpg,5,23.99,2025-09-02
91,Bedding Set Everyday 737,bedding-set-everyday-737,"Cotton bedding set, soft and breathable. Everyday line, silver.",/images/products/bedding-set-everyday-737.jpg,5,45.99,2025-04-09
92,Bedding Set Everyday 735,bedding-set-everyday-735,"Cotton bedding set, soft and breathable. Everyday line, white.",/images/products/bedding-set-everyday-735.jpg,5,48.99,2025-04-04
93,Towel Set Eco 365,towel-set-eco-365,"Absorbent bath towel set. Eco line, blue.",/images/products/towel-set-eco-365.jpg,5,23.99,2025-09-26
94,Towel Set Pro 801,towel-set-pro-801,"Absorbent bath towel set. Pro line, red.",/images/products/towel-set-pro-801.jpg,5,50.99,2025-03-25
95,Cookware Set Premium 431,cookware-set-premium-431,"Non-stick cookware set, induction compatible. Premium line, grey.",/images/products/cookware-set-premium-431.jpg,5,88.99,2025-08-12
96,Cookware Set Premium 319,cookware-set-premium-319,"Non-stick cookware set, induction compatible. Premium line, green.",/images/products/cookware-set-premium-319.jpg,5,243.99,2025-03-09
97,Rug Pro 262,rug-pro-262,"Soft living room rug, easy to clean. Pro line, black.",/images/products/rug-pro-262.jpg,5,32.99,2025-10-22
98,Rug Everyday 138,rug-everyday-138,"Soft living room rug, easy to clean. Everyday line, blue.",/images/products/rug-everyday-138.jpg,5,151.99,2025-06-27
99,Vacuum Cleaner Eco 407,vacuum-cleaner-eco-407,"Bagless vacuum cleaner with HEPA filter. Eco line, blue.",/images/products/vacuum-cleaner-eco-407.jpg,5,372.99,2025-08-31
100,Vacuum Cleaner Classic 924,vacuum-cleaner-classic-924,"Bagless vacuum cleaner with HEPA filter. Classic line, black.",/images/products/vacuum-cleaner-classic-924.jpg,5,122.99,2025-07-01
101,Kettle Deluxe 984,kettle-deluxe-984,"Electric kettle, 1.7 litre, auto shut-off. Deluxe line, beige.",/images/products/kettle-deluxe-984.jpg,5,67.99,2025-04-26
102,Kettle Pro 822,kettle-pro-822,"Electric kettle, 1.7 litre, auto shut-off. Pro line, blue.",/images/products/kettle-pro-822.jpg,5,35.99,2025-03-30
103,Candle Everyday 732,candle-everyday-732,"Scented candle, vanilla and amber. Everyday line, green.",/images/products/candle-everyday-732.jpg,5,13.99,2025-11-07
104,Candle Deluxe 106,candle-deluxe-106,"Scented candle, vanilla and amber. Deluxe line, silver.",/images/products/candle-deluxe-106.jpg,5,9.49,2025-11-21
105,Bedding Set Everyday 147,bedding-set-everyday-147,"Cotton bedding set, soft and breathable. Everyday line, green.",/images/products/bedding-set-everyday-147.jpg,5,59.99,2025-05-04
106,Face Cream Deluxe 613,face-cream-deluxe-613,"Hydrating face cream for daily use. Deluxe line, white.",/images/products/face-cream-deluxe-613.jpg,6,65.99,2025-03-28
107,Face Cream Everyday 865,face-cream-everyday-865,"Hydrating face cream for daily use. Everyday line, white.",/images/products/face-cream-everyday-865.jpg,6,31.99,2025-05-05
108,Serum Essential 226,serum-essential-226,"Vitamin C serum for radiant skin. Essential line, blue.",/images/products/serum-essential-226.jpg,6,48.99,2025-06-24
109,Serum Everyday 923,serum-everyday-923,"Vitamin C serum for radiant skin. Everyday line, black.",/images/products/serum-everyday-923.jpg,6,31.99,2025-10-10
110,Shampoo Everyday 111,shampoo-everyday-111,"Nourishing shampoo for dry hair. Everyday line, red.",/images/products/shampoo-everyday-111.jpg,6,9.49,2025-07-27
111,Shampoo Classic 190,shampoo-classic-190,"Nourishing shampoo for dry hair. Classic line, grey.",/images/products/shampoo-classic-190.jpg,6,8.49,2025-06-28
112,Perfume Classic 324,perfume-classic-324,"Eau de parfum, floral and woody notes. Classic line, black.",/images/products/perfume-classic-324.jpg,6,65.99,2025-03-09
113,Perfume Pro 986,perfume-pro-986,"Eau de parfum, floral and woody notes. Pro line, red.",/images/products/perfume-pro-986.jpg,6,72.99,2025-11-05
114,Lipstick Compact 868,lipstick-compact-868,"Long-lasting matte lipstick. Compact line, grey.",/images/products/lipstick-compact-868.jpg,6,8.49,2025-03-01
115,Lipstick Eco 829,lipstick-eco-829,"Long-lasting matte lipstick. Eco line, beige.",/images/products/lipstick-eco-829.jpg,6,9.49,2025-06-25
116,Hair Dryer Deluxe 707,hair-dryer-deluxe-707,"Ionic hair dryer, fast drying. Deluxe line, silver.",/images/products/hair-dryer-deluxe-707.jpg,6,85.99,2025-03-07
117,Hair Dryer Everyday 502,hair-dryer-everyday-502,"Ionic hair dryer, fast drying. Everyday line, blue.",/images/products/hair-dryer-everyday-502.jpg,6,80.99,2025-05-23
118,Body Lotion Deluxe 734,body-lotion-deluxe-734,"Body lotion with shea butter. Deluxe line, beige.",/images/products/body-lotion-deluxe-734.jpg,6,6.49,2025-09-28
119,Body Lotion Everyday 438,body-lotion-everyday-438,"Body lotion with shea butter. Everyday line, blue.",/images/products/body-lotion-everyday-438.jpg,6,5.49,2025-11-02
120,Sunscreen Eco 737,sunscreen-eco-737,"Sunscreen SPF 50, water-resistant. Eco line, green.",/images/products/sunscreen-eco-737.jpg,6,11.99,2025-10-24
121,Sunscreen Classic 799,sunscreen-classic-799,"Sunscreen SPF 50, water-resistant. Classic line, silver.",/images/products/sunscreen-classic-799.jpg,6,22.99,2025-11-02
122,Makeup Brush Set Eco 513,makeup-brush-set-eco-513,"Makeup brush set, soft synthetic bristles. Eco line, black.",/images/products/makeup-brush-set-eco-513.jpg,6,37.99,2025-11-10
123,Makeup Brush Set Pro 675,makeup-brush-set-pro-675,"Makeup brush set, soft synthetic bristles. Pro line, beige.",/images/products/makeup-brush-set-pro-675.jpg,6,24.99,2025-10-07
124,Beard Trimmer Pro 366,beard-trimmer-pro-366,"Rechargeable beard trimmer with combs. Pro line, black.",/images/products/beard-trimmer-pro-366.jpg,6,51.99,2025-05-19
125,Beard Trimmer Premium 354,beard-trimmer-premium-354,"Rechargeable beard trimmer with combs. Premium line, grey.",/images/products/beard-trimmer-premium-354.jpg,6,71.99,2025-09-16
126,Body Lotion Classic 808,body-lotion-classic-808,"Body lotion with shea butter. Classic line, green.",/images/products/body-lotion-classic-808.jpg,6,7.49,2025-05-21
127,Building Blocks Premium 126,building-blocks-premium-126,"Building blocks set, creative construction toy. Premium line, grey.",/images/products/building-blocks-premium-126.jpg,7,37.99,2025-10-30
128,Building Blocks Deluxe 813,building-blocks-deluxe-813,"Building blocks set, creative construction toy. Deluxe line, beige.",/images/products/building-blocks-deluxe-813.jpg,7,51.99,2025-08-13
129,Board Game Deluxe 308,board-game-deluxe-308,"Family board game for 2-6 players. Deluxe line, green.",/images/products/board-game-deluxe-308.jpg,7,16.99,2025-08-13
130,Board Game Essential 786,board-game-essential-786,"Family board game for 2-6 players. Essential line, grey.",/images/products/board-game-essential-786.jpg,7,57.99,2025-10-22
131,Puzzle Essential 352,puzzle-essential-352,"1000-piece jigsaw puzzle. Essential line, grey.",/images/products/puzzle-essential-352.jpg,7,29.99,2025-08-20
132,Puzzle Everyday 336,puzzle-everyday-336,"1000-piece jigsaw puzzle. Everyday line, silver.",/images/products/puzzle-everyday-336.jpg,7,8.49,2025-11-15
133,Doll Eco 977,doll-eco-977,"Fashion doll with accessories. Eco line, beige.",/images/products/doll-eco-977.jpg,7,23.99,2025-10-30
134,Doll Classic 843,doll-classic-843,"Fashion doll with accessories. Classic line, silver.",/images/products/doll-classic-843.jpg,7,47.99,2025-11-12
135,RC Car Deluxe 276,rc-car-deluxe-276,"Remote control car, rechargeable. Deluxe line, black.",/images/products/rc-car-deluxe-276.jpg,7,55.99,2025-08-12
136,RC Car Essential 980,rc-car-essential-980,"Remote control car, rechargeable. Essential line, blue.",/images/products/rc-car-essential-980.jpg,7,52.99,2025-03-09
137,Plush Toy Classic 439,plush-toy-classic-439,"Soft plush teddy bear. Classic line, red.",/images/products/plush-toy-classic-439.jpg,7,32.99,2025-05-21
138,Plush Toy Premium 855,plush-toy-premium-855,"Soft plush teddy bear. Premium line, black.",/images/products/plush-toy-premium-855.jpg,7,14.99,2025-05-19
139,Robot Kit Premium 136,robot-kit-premium-136,"Programmable robot kit, STEM learning. Premium line, grey.",/images/products/robot-kit-premium-136.jpg,7,47.99,2025-10-25
140,Robot Kit Essential 218,robot-kit-essential-218,"Programmable robot kit, STEM learning. Essential line, green.",/images/products/robot-kit-essential-218.jpg,7,63.99,2025-11-07
141,Paint Set Classic 369,paint-set-classic-369,"Kids paint set with brushes. Classic line, red.",/images/products/paint-set-classic-369.jpg,7,17.99,2025-08-18
142,Paint Set Deluxe 295,paint-set-deluxe-295,"Kids paint set with brushes. Deluxe line, white.",/images/products/paint-set-deluxe-295.jpg,7,9.49,2025-04-25
143,Toy Train Deluxe 965,toy-train-deluxe-965,"Wooden toy train set. Deluxe line, blue.",/images/products/toy-train-deluxe-965.jpg,7,43.99,2025-07-06
144,Toy Train Pro 565,toy-train-pro-565,"Wooden toy train set. Pro line, green.",/images/products/toy-train-pro-565.jpg,7,93.99,2025-10-04
145,Card Game Essential 324,card-game-essential-324,"Fast card game for kids and adults. Essential line, black.",/images/products/card-game-essential-324.jpg,7,10.99,2025-05-29
146,Card Game Eco 736,card-game-eco-736,"Fast card game for kids and adults. Eco line, blue.",/images/products/card-game-eco-736.jpg,7,7.49,2025-04-10
147,Paint Set Everyday 573,paint-set-everyday-573,"Kids paint set with brushes. Everyday line, green.",/images/products/paint-set-everyday-573.jpg,7,17.99,2025-10-18
148,Coffee Beans Pro 813,coffee-beans-pro-813,"Arabica coffee beans, medium roast. Pro line, white.",/images/products/coffee-beans-pro-813.jpg,8,8.49,2025-07-18
149,Coffee Beans Pro 200,coffee-beans-pro-200,"Arabica coffee beans, medium roast. Pro line, silver.",/images/products/coffee-beans-pro-200.jpg,8,8.49,2025-03-26
150,Green Tea Deluxe 321,green-tea-deluxe-321,"Organic green tea, loose leaf. Deluxe line, blue.",/images/products/green-tea-deluxe-321.jpg,8,7.49,2025-10-20
151,Green Tea Eco 344,green-tea-eco-344,"Organic green tea, loose leaf. Eco line, white.",/images/products/green-tea-eco-344.jpg,8,10.99,2025-05-05
152,Dark Chocolate Premium 512,dark-chocolate-premium-512,"Dark chocolate 70% cocoa. Premium line, green.",/images/products/dark-chocolate-premium-512.jpg,8,3.49,2025-08-17
153,Dark Chocolate Essential 370,dark-chocolate-essential-370,"Dark chocolate 70% cocoa. Essential line, silver.",/images/products/dark-chocolate-essential-370.jpg,8,3.49,2025-09-20
154,Olive Oil Everyday 426,olive-oil-everyday-426,"Extra virgin olive oil, cold pressed. Everyday line, white.",/images/products/olive-oil-everyday-426.jpg,8,7.49,2025-04-03
155,Olive Oil Deluxe 890,olive-oil-deluxe-890,"Extra virgin olive oil, cold pressed. Deluxe line, grey.",/images/products/olive-oil-deluxe-890.jpg,8,10.99,2025-08-12
156,Honey Everyday 491,honey-everyday-491,"Natural forest honey. Everyday line, white.",/images/products/honey-everyday-491.jpg,8,7.49,2025-10-24
157,Honey Compact 112,honey-compact-112,"Natural forest honey. Compact line, grey.",/images/products/honey-compact-112.jpg,8,8.49,2025-03-29
158,Pasta Eco 942,pasta-eco-942,"Durum wheat pasta. Eco line, black.",/images/products/pasta-eco-942.jpg,8,5.49,2025-07-27
159,Pasta Premium 123,pasta-premium-123,"Durum wheat pasta. Premium line, blue.",/images/products/pasta-premium-123.jpg,8,2.49,2025-05-24
160,Granola Premium 789,granola-premium-789,"Crunchy granola with nuts and honey. Premium line, blue.",/images/products/granola-premium-789.jpg,8,5.49,2025-06-19
161,Granola Deluxe 683,granola-deluxe-683,"Crunchy granola with nuts and honey. Deluxe line, red.",/images/products/granola-deluxe-683.jpg,8,5.49,2025-07-09
162,Spice Set Pro 698,spice-set-pro-698,"Gourmet spice set for grilling and cooking. Pro line, white.",/images/products/spice-set-pro-698.jpg,8,26.99,2025-05-23
163,Spice Set Premium 106,spice-set-premium-106,"Gourmet spice set for grilling and cooking. Premium line, green.",/images/products/spice-set-premium-106.jpg,8,9.49,2025-08-14
164,Protein Bar Box Compact 478,protein-bar-box-compact-478,"Protein bars box, 12 pieces. Compact line, red.",/images/products/protein-bar-box-compact-478.jpg,8,13.99,2025-07-19
165,Protein Bar Box Deluxe 678,protein-bar-box-deluxe-678,"Protein bars box, 12 pieces. Deluxe line, white.",/images/products/protein-bar-box-deluxe-678.jpg,8,27.99,2025-06-29
166,Juice Eco 447,juice-eco-447,"Fresh orange juice, no added sugar. Eco line, red.",/images/products/juice-eco-447.jpg,8,2.49,2025-07-08
167,Juice Everyday 509,juice-everyday-509,"Fresh orange juice, no added sugar. Everyday line, white.",/images/products/juice-everyday-509.jpg,8,3.49,2025-04-11
168,Juice Everyday 512,juice-everyday-512,"Fresh orange juice, no added sugar. Everyday line, white.",/images/products/juice-everyday-512.jpg,8,4.49,2025-06-22
169,Sofa Essential 990,sofa-essential-990,"Three-seat sofa, fabric upholstery. Essential line, beige.",/images/products/sofa-essential-990.jpg,9,440.99,2025-05-05
170,Sofa Everyday 232,sofa-everyday-232,"Three-seat sofa, fabric upholstery. Everyday line, white.",/images/products/sofa-everyday-232.jpg,9,591.99,2025-05-09
171,Office Chair Deluxe 707,office-chair-deluxe-707,"Ergonomic office chair with lumbar support. Deluxe line, silver.",/images/products/office-chair-deluxe-707.jpg,9,235.99,2025-08-30
172,Office Chair Classic 995,office-chair-classic-995,"Ergonomic office chair with lumbar support. Classic line, beige.",/images/products/office-chair-classic-995.jpg,9,165.99,2025-09-18
173,Desk Eco 120,desk-eco-120,"Home office desk, wooden top. Eco line, silver.",/images/products/desk-eco-120.jpg,9,321.99,2025-09-14
174,Desk Compact 268,desk-compact-268,"Home office desk, wooden top. Compact line, white.",/images/products/desk-compact-268.jpg,9,190.99,2025-08-01
175,Bookshelf Eco 371,bookshelf-eco-371,"Five-tier bookshelf. Eco line, blue.",/images/products/bookshelf-eco-371.jpg,9,167.99,2025-03-13
176,Bookshelf Compact 435,bookshelf-compact-435,"Five-tier bookshelf. Compact line, grey.",/images/products/bookshelf-compact-435.jpg,9,60.99,2025-11-03
177,Bed Frame Eco 577,bed-frame-eco-577,"Double bed frame with storage. Eco line, grey.",/images/products/bed-frame-eco-577.jpg,9,241.99,2025-04-17
178,Bed Frame Essential 340,bed-frame-essential-340,"Double bed frame with storage. Essential line, white.",/images/products/bed-frame-essential-340.jpg,9,561.99,2025-03-04
179,Wardrobe Eco 520,wardrobe-eco-520,"Two-door wardrobe with mirror. Eco line, white.",/images/products/wardrobe-eco-520.jpg,9,763.99,2025-06-17
180,Wardrobe Classic 848,wardrobe-classic-848,"Two-door wardrobe with mirror. Classic line, red.",/images/products/wardrobe-classic-848.jpg,9,591.99,2025-03-23
181,Coffee Table Eco 857,coffee-table-eco-857,"Coffee table, oak finish. Eco line, white.",/images/products/coffee-table-eco-857.jpg,9,204.99,2025-06-06
182,Coffee Table Pro 626,coffee-table-pro-626,"Coffee table, oak finish. Pro line, black.",/images/products/coffee-table-pro-626.jpg,9,56.99,2025-03-27
183,Nightstand Classic 778,nightstand-classic-778,"Nightstand with drawer. Classic line, grey.",/images/products/nightstand-classic-778.jpg,9,144.99,2025-05-24
184,Nightstand Everyday 721,nightstand-everyday-721,"Nightstand with drawer. Everyday line, silver.",/images/products/nightstand-everyday-721.jpg,9,89.99,2025-10-24
185,Dining Chair Classic 954,dining-chair-classic-954,"Upholstered dining chair. Classic line, black.",/images/products/dining-chair-classic-954.jpg,9,98.99,2025-07-25
186,Dining Chair Essential 421,dining-chair-essential-421,"Upholstered dining chair. Essential line, blue.",/images/products/dining-chair-essential-421.jpg,9,81.99,2025-10-07
187,Armchair Eco 684,armchair-eco-684,"Reading armchair, velvet. Eco line, white.",/images/products/armchair-eco-684.jpg,9,277.99,2025-05-18
188,Armchair Classic 733,armchair-classic-733,"Reading armchair, velvet. Classic line, white.",/images/products/armchair-classic-733.jpg,9,141.99,2025-10-31
189,Nightstand Pro 841,nightstand-pro-841,"Nightstand with drawer. Pro line, grey.",/images/products/nightstand-pro-841.jpg,9,56.99,2025-10-13
190,Winter Tires Essential 210,winter-tires-essential-210,"Winter tire, excellent grip on snow and ice. Essential line, grey.",/images/products/winter-tires-essential-210.jpg,10,183.99,2025-08-20
191,Winter Tires Deluxe 474,winter-tires-deluxe-474,"Winter tire, excellent grip on snow and ice. Deluxe line, white.",/images/products/winter-tires-deluxe-474.jpg,10,65.99,2025-10-22
192,Car Battery Premium 115,car-battery-premium-115,"12V car battery, long life. Premium line, blue.",/images/products/car-battery-premium-115.jpg,10,147.99,2025-10-30
193,Car Battery Deluxe 488,car-battery-deluxe-488,"12V car battery, long life. Deluxe line, white.",/images/products/car-battery-deluxe-488.jpg,10,92.99,2025-07-21
194,Dash Cam Compact 583,dash-cam-compact-583,"Full HD dash cam with night vision. Compact line, silver.",/images/products/dash-cam-compact-583.jpg,10,154.99,2025-11-14
195,Dash Cam Eco 784,dash-cam-eco-784,"Full HD dash cam with night vision. Eco line, red.",/images/products/dash-cam-eco-784.jpg,10,108.99,2025-07-16
196,Phone Holder Pro 656,phone-holder-pro-656,"Magnetic car phone holder. Pro line, black.",/images/products/phone-holder-pro-656.jpg,10,19.99,2025-06-09
197,Phone Holder Pro 706,phone-holder-pro-706,"Magnetic car phone holder. Pro line, green.",/images/products/phone-holder-pro-706.jpg,10,10.99,2025-06-24
198,Car Charger Everyday 607,car-charger-everyday-607,"Fast USB-C car charger. Everyday line, blue.",/images/products/car-charger-everyday-607.jpg,10,11.99,2025-10-16
199,Car Charger Everyday 299,car-charger-everyday-299,"Fast USB-C car charger. Everyday line, beige.",/images/products/car-charger-everyday-299.jpg,10,16.99,2025-06-14
200,Floor Mats Everyday 949,floor-mats-everyday-949,"Rubber car floor mats, all-weather. Everyday line, silver.",/images/products/floor-mats-everyday-949.jpg,10,30.99,2025-04-29
201,Floor Mats Pro 348,floor-mats-pro-348,"Rubber car floor mats, all-weather. Pro line, beige.",/images/products/floor-mats-pro-348.jpg,10,28.99,2025-09-17
202,Engine Oil Compact 508,engine-oil-compact-508,"Synthetic engine oil 5W-30. Compact line, beige.",/images/products/engine-oil-compact-508.jpg,10,27.99,2025-05-06
203,Engine Oil Eco 775,engine-oil-eco-775,"Synthetic engine oil 5W-30. Eco line, beige.",/images/products/engine-oil-eco-775.jpg,10,19.99,2025-07-05
204,Ice Scraper Eco 750,ice-scraper-eco-750,"Ice scraper with snow brush. Eco line, beige.",/images/products/ice-scraper-eco-750.jpg,10,6.49,2025-09-27
205,Ice Scraper Deluxe 739,ice-scraper-deluxe-739,"Ice scraper with snow brush. Deluxe line, grey.",/images/products/ice-scraper-deluxe-739.jpg,10,10.99,2025-05-26
206,Car Vacuum Deluxe 348,car-vacuum-deluxe-348,"Handheld car vacuum cleaner. Deluxe line, silver.",/images/products/car-vacuum-deluxe-348.jpg,10,85.99,2025-09-27
207,Car Vacuum Everyday 954,car-vacuum-everyday-954,"Handheld car vacuum cleaner. Everyday line, white.",/images/products/car-vacuum-everyday-954.jpg,10,32.99,2025-10-25
208,Jump Starter Essential 942,jump-starter-essential-942,"Portable jump starter with power bank. Essential line, green.",/images/products/jump-starter-essential-942.jpg,10,57.99,2025-10-25
209,Jump Starter Compact 635,jump-starter-compact-635,"Portable jump starter with power bank. Compact line, white.",/images/products/jump-starter-compact-635.jpg,10,106.99,2025-08-25
210,Dash Cam Premium 877,dash-cam-premium-877,"Full HD dash cam with night vision. Premium line, white.",/images/products/dash-cam-premium-877.jpg,10,76.99,2025-07-31
211,Acoustic Guitar Everyday 144,acoustic-guitar-everyday-144,"Acoustic guitar, spruce top. Everyday line, blue.",/images/products/acoustic-guitar-everyday-144.jpg,11,407.99,2025-11-01
212,Acoustic Guitar Compact 849,acoustic-guitar-compact-849,"Acoustic guitar, spruce top. Compact line, silver.",/images/products/acoustic-guitar-compact-849.jpg,11,172.99,2025-10-24
213,Digital Piano Deluxe 132,digital-piano-deluxe-132,"88-key digital piano with weighted keys. Deluxe line, green.",/images/products/digital-piano-deluxe-132.jpg,11,623.99,2025-10-03
214,Digital Piano Premium 233,digital-piano-premium-233,"88-key digital piano with weighted keys. Premium line, green.",/images/products/digital-piano-premium-233.jpg,11,582.99,2025-10-05
215,Guitar Strings Compact 500,guitar-strings-compact-500,"Steel guitar strings, light gauge. Compact line, grey.",/images/products/guitar-strings-compact-500.jpg,11,14.99,2025-06-11
216,Guitar Strings Essential 403,guitar-strings-essential-403,"Steel guitar strings, light gauge. Essential line, black.",/images/products/guitar-strings-essential-403.jpg,11,19.99,2025-07-01
217,Studio Headphones Essential 159,studio-headphones-essential-159,"Closed-back studio monitoring headphones. Essential line, silver.",/images/products/studio-headphones-essential-159.jpg,11,90.99,2025-05-29
218,Studio Headphones Pro 770,studio-headphones-pro-770,"Closed-back studio monitoring headphones. Pro line, green.",/images/products/studio-headphones-pro-770.jpg,11,64.99,2025-05-08
219,Microphone Essential 454,microphone-essential-454,"USB condenser microphone for podcasts and vocals. Essential line, red.",/images/products/microphone-essential-454.jpg,11,181.99,2025-09-24
220,Microphone Eco 278,microphone-eco-278,"USB condenser microphone for podcasts and vocals. Eco line, silver.",/images/products/microphone-eco-278.jpg,11,76.99,2025-03-05
221,Guitar Amp Classic 781,guitar-amp-classic-781,"Practice guitar amplifier, 20W. Classic line, black.",/images/products/guitar-amp-classic-781.jpg,11,149.99,2025-08-08
222,Guitar Amp Eco 862,guitar-amp-eco-862,"Practice guitar amplifier, 20W. Eco line, red.",/images/products/guitar-amp-eco-862.jpg,11,272.99,2025-09-17
223,Ukulele Premium 117,ukulele-premium-117,"Soprano ukulele for beginners. Premium line, black.",/images/products/ukulele-premium-117.jpg,11,34.99,2025-08-21
224,Ukulele Essential 759,ukulele-essential-759,"Soprano ukulele for beginners. Essential line, beige.",/images/products/ukulele-essential-759.jpg,11,76.99,2025-06-22
225,Drum Sticks Pro 333,drum-sticks-pro-333,"Hickory drum sticks. Pro line, blue.",/images/products/drum-sticks-pro-333.jpg,11,9.49,2025-05-12
226,Drum Sticks Eco 816,drum-sticks-eco-816,"Hickory drum sticks. Eco line, blue.",/images/products/drum-sticks-eco-816.jpg,11,24.99,2025-11-21
227,Music Stand Everyday 471,music-stand-everyday-471,"Foldable music stand. Everyday line, blue.",/images/products/music-stand-everyday-471.jpg,11,46.99,2025-04-04
228,Music Stand Pro 759,music-stand-pro-759,"Foldable music stand. Pro line, white.",/images/products/music-stand-pro-759.jpg,11,29.99,2025-06-15
229,Effects Pedal Essential 260,effects-pedal-essential-260,"Distortion effects pedal. Essential line, grey.",/images/products/effects-pedal-essential-260.jpg,11,64.99,2025-10-31
230,Effects Pedal Eco 176,effects-pedal-eco-176,"Distortion effects pedal. Eco line, white.",/images/products/effects-pedal-eco-176.jpg,11,110.99,2025-08-30
231,Studio Headphones Classic 686,studio-headphones-classic-686,"Closed-back studio monitoring headphones. Classic line, red.",/images/products/studio-headphones-classic-686.jpg,11,76.99,2025-05-24
232,Cordless Drill Classic 499,cordless-drill-classic-499,"Cordless drill driver with two batteries. Classic line, grey.",/images/products/cordless-drill-classic-499.jpg,12,162.99,2025-03-22
233,Cordless Drill Everyday 416,cordless-drill-everyday-416,"Cordless drill driver with two batteries. Everyday line, green.",/images/products/cordless-drill-everyday-416.jpg,12,150.99,2025-05-12
234,Screwdriver Set Eco 897,screwdriver-set-eco-897,"Precision screwdriver set. Eco line, beige.",/images/products/screwdriver-set-eco-897.jpg,12,13.99,2025-07-08
235,Screwdriver Set Pro 103,screwdriver-set-pro-103,"Precision screwdriver set. Pro line, black.",/images/products/screwdriver-set-pro-103.jpg,12,25.99,2025-05-12
236,Hammer Essential 301,hammer-essential-301,"Claw hammer with fiberglass handle. Essential line, red.",/images/products/hammer-essential-301.jpg,12,36.99,2025-05-31
237,Hammer Essential 102,hammer-essential-102,"Claw hammer with fiberglass handle. Essential line, blue.",/images/products/hammer-essential-102.jpg,12,34.99,2025-06-04
238,Tape Measure Pro 133,tape-measure-pro-133,"5 metre tape measure. Pro line, blue.",/images/products/tape-measure-pro-133.jpg,12,15.99,2025-08-29
239,Tape Measure Premium 980,tape-measure-premium-980,"5 metre tape measure. Premium line, blue.",/images/products/tape-measure-premium-980.jpg,12,8.49,2025-09-25
240,Toolbox Premium 215,toolbox-premium-215,"Toolbox with 100 hand tools. Premium line, black.",/images/products/toolbox-premium-215.jpg,12,26.99,2025-06-04
241,Toolbox Compact 854,toolbox-compact-854,"Toolbox with 100 hand tools. Compact line, green.",/images/products/toolbox-compact-854.jpg,12,119.99,2025-06-10
242,Ladder Everyday 810,ladder-everyday-810,"Aluminium step ladder. Everyday line, beige.",/images/products/ladder-everyday-810.jpg,12,194.99,2025-10-16
243,Ladder Deluxe 713,ladder-deluxe-713,"Aluminium step ladder. Deluxe line, green.",/images/products/ladder-deluxe-713.jpg,12,53.99,2025-11-22
244,Circular Saw Deluxe 150,circular-saw-deluxe-150,"Circular saw, 1200W. Deluxe line, beige.",/images/products/circular-saw-deluxe-150.jpg,12,168.99,2025-04-23
245,Circular Saw Pro 650,circular-saw-pro-650,"Circular saw, 1200W. Pro line, red.",/images/products/circular-saw-pro-650.jpg,12,120.99,2025-10-24
246,Spirit Level Pro 357,spirit-level-pro-357,"Spirit level, 60 cm. Pro line, blue.",/images/products/spirit-level-pro-357.jpg,12,21.99,2025-09-17
247,Spirit Level Eco 157,spirit-level-eco-157,"Spirit level, 60 cm. Eco line, silver.",/images/products/spirit-level-eco-157.jpg,12,15.99,2025-05-28
248,Work Gloves Pro 810,work-gloves-pro-810,"Protective work gloves. Pro line, silver.",/images/products/work-gloves-pro-810.jpg,12,9.49,2025-05-17
249,Work Gloves Compact 227,work-gloves-compact-227,"Protective work gloves. Compact line, white.",/images/products/work-gloves-compact-227.jpg,12,7.49,2025-06-07
250,Glue Gun Deluxe 657,glue-gun-deluxe-657,"Hot glue gun with glue sticks. Deluxe line, silver.",/images/products/glue-gun-deluxe-657.jpg,12,19.99,2025-06-22
251,Glue Gun Eco 799,glue-gun-eco-799,"Hot glue gun with glue sticks. Eco line, silver.",/images/products/glue-gun-eco-799.jpg,12,32.99,2025-11-11
252,Spirit Level Classic 425,spirit-level-classic-425,"Spirit level, 60 cm. Classic line, beige.",/images/products/spirit-level-classic-425.jpg,12,15.99,2025-10-22
```

### data/README.md

# Day 1 podaci — sintetički dataset

Deterministički, seeded (seed `42`), **byte-for-byte reproduktivan**. Jedini
izvor istine za podatke kursa — kasniji dani referenciraju ove fajlove, ne
dupliraju ih. Kompletna dokumentacija (parametri, šema, značenje polja,
sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `customers.csv` | 3000 korisnika sa personama (primarna + sekundarna) | 3000 |
| `products.csv` | 252 proizvoda u 12 kategorija (realni cenovni rasponi po tipu proizvoda, EUR) | 252 |
| `events.csv` | 183 468 behavioral događaja (8 tipova), januar 2026 | 183 468 |
| `orders.csv` | 1 045 stavki u 893 porudžbine (jedan red po stavci = jedan `purchase` događaj; stavke iste porudžbine dele `order_id`) | 1 045 |
| `categories.csv` | 12 kategorija | 12 |
| `metadata.json` | seed, parametri, značenje polja, sha256 manifest | — |

## Persone (preklapajuće, sa šumom)

* **high\_value** — česti kupci, visoka tolerancija cene, česte kupovine.
* **price\_sensitive** — traže jeftino: puno pregleda, retka kupovina.
* **category\_focused** — 1–2 omiljene kategorije, duboka aktivnost tamo.
* **occasional** — retke sesije, uglavnom pregledi.
* **new\_user** — tek se pridružio, malo događaja u poslednjim danima.

Preklapanje je namerno (15% „aspirativnih" pregleda van cene/kategorije,
sekundarna persona sa verovatnoćom 0.35, per-korisnički jitter) — inače bi
segmentacija (Day 2), predikcija (Day 3) i preporuke (Day 5+) bile trivijalne.

## Levak (stanje u ovom seed-u)

* događaja ukupno: **183 468** · sesija: **15 361** (od toga sa kupovinom: **893**)
* pregledi proizvoda: **94 220** · dodavanja u korpu: **3 159** · kupovine (stavke): **1 045**
* porudžbina: **893** (≈ 1.17 stavke po porudžbini) · prihod **95,378.18 EUR** · AOV **106.81 EUR**
* stopa konverzije: **≈ 0.058** (sesije sa kupovinom / sve sesije) · napuštene korpe: **≈ 0.67**
  (sesije sa korpom bez kupovine / sesije sa korpom) — u rasponu tipičnom za e-commerce

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_dataset --seed 42
.venv/bin/python -m app.data.verify_dataset
```

Dva pokretanja sa istim seed-om daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`). Promena seed-a menja podatke — isti kod
radi, ali brojevi u README-ju više ne odgovaraju.

## Značenje ključnih polja (events)

* `event_type`: `product_view` | `category_view` | `search` | `add_to_cart` |
  `remove_from_cart` | `purchase` | `recommendation_impression` |
  `recommendation_click`
* `user_session`: identifikator sesije (`session_000001`, ...) — osnova za
  funnel i kasnije feature-e po sesiji.
* `product_id`/`category_id`: prazno (`NA`) tamo gde događaj nije vezan
  (npr. `search`, `category_view`).
* `price`: cena u trenutku događaja (za AOV i osetljivost na cenu).
* `source`: koja stranica je emitovala događaj
  (`product_page`, `category_page`, `shop`, `search_page`, `cart`,
  `recommendation`).
* `timestamp`: normalizovan `YYYY-MM-DD HH:MM:SS`, bez vremenske zone;
  redosled događaja je smislen (funnel unutar sesije).
* `recommendation_source`/`recommendation_position`: za događaje preporuka
  (Day 9 CTR, Day 12 evaluacija).

## Šta ovi podaci NE dokazuju

Pun event tabela nije analitika, nije segmentacija i nije AI — to je preduslov.
Broj konverzije opisuje *ovaj sintetički dataset*, ne nameru stvarnih
korisnika.

### examples/demo\_analytics.py

```
"""Demo: analitika na seeded podacima (Day 1).

Pokretanje (bilo gde):

    python3 "Day 1/examples/demo_analytics.py"

Prikazuje: funnel brojeve, stopu konverzije, udeo po kategoriji i
najgledanije proizvode.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.analytics import (
    average_order_value,
    calculate_conversion_rate,
    calculate_funnel_counts,
    get_product_view_count,
    share_by_category,
)
from app.data.events import EventStore
from app.data.paths import dataset_path


def main() -> None:
    store = EventStore.load_seeded()
    events = store.events_dataframe()
    products = pd.read_csv(dataset_path("products.csv"))
    orders = pd.read_csv(dataset_path("orders.csv"))

    funnel = calculate_funnel_counts(events)
    print("Levak (funnel):")
    for k, v in funnel.items():
        print(f"  {k:22s} {v:>7,}")

    cr = calculate_conversion_rate(events)
    print(f"\nStopa konverzije (sesije sa kupovinom / sve sesije): {cr:.4f}")

    print("\nTržišni udeo kategorija po pregledima (share-by-category):")
    share = share_by_category(events, products, metric="view")
    categories = pd.read_csv(dataset_path("categories.csv"))
    cat_names = categories.set_index("category_id")["name"]
    share["category"] = share["category_id"].map(cat_names)
    print(share[["category", "count", "share"]].to_string(index=False))

    print("\nTop 5 proizvoda po broju pregleda:")
    view_counts = events[events["event_type"] == "product_view"]["product_id"].value_counts().head(5)
    for pid, n in view_counts.items():
        pid = int(pid)  # Int64 key -> int za prikaz i upit
        p = products[products["product_id"] == pid].iloc[0]
        print(f"  #{pid} {p['name']:<28s} views={n:<5,}  cena={p['price']:>8.2f}")

    print("\nPorudžbine:", orders["order_id"].nunique(), f"({len(orders)} stavki)",
          "  prosečna vrednost porudžbine (AOV):", average_order_value(orders))

    # Provera: sum(per-product views) == total views (interna konzistentnost)
    total_via_products = sum(
        get_product_view_count(events, pid) for pid in products["product_id"]
    )
    print(f"\nInterna provera: suma po proizvodima ({total_via_products:,}) "
          f"== ukupni pregledi ({funnel['views']:,}) -> {total_via_products == funnel['views']}")


if __name__ == "__main__":
    main()
```

### examples/demo\_events.py

```
"""Demo: event layer na seeded podacima (Day 1).

Pokretanje (bilo gde):

    python3 "Day 1/examples/demo_events.py"

Prikazuje: učitavanje seeded store-a, upite po sesiji/proizvodu/korisniku,
i round-trip (save_event -> get_customer_events).
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.data.events import VALID_EVENT_TYPES, EventStore, create_event
from app.data.analytics import calculate_funnel_counts


def main() -> None:
    store = EventStore.load_seeded()
    events = store.events_dataframe()
    print(f"Ukupno događaja u seeded datasetu: {len(events):,}")
    print(f"Dozvoljeni tipovi događaja: {sorted(VALID_EVENT_TYPES)}")

    # Upit po sesiji
    first_session = events["user_session"].iloc[0]
    session_df = store.get_session_events(first_session)
    print(f"\nPrimer sesije {first_session}: {len(session_df)} događaja")
    print(session_df[["event_id", "event_type", "product_id", "timestamp"]].to_string(index=False))

    # Upit po proizvodu i korisniku
    pid = int(events["product_id"].dropna().iloc[0])
    print(f"\nDogađaji za proizvod {pid}: {len(store.get_product_events(pid))}")
    uid = int(events["user_id"].iloc[0])
    print(f"Događaji za korisnika {uid}: {len(store.get_customer_events(uid))}")

    # Round-trip: save_event -> get_customer_events
    ev = create_event(
        "search",
        user_id=uid,
        user_session="demo_session_1",
        source="search_page",
        timestamp="2026-01-15 12:00:00",
    )
    saved = store.save_event(ev)
    print(f"\nRound-trip: sačuvan događaj event_id={saved['event_id']}")
    found = store.get_customer_events(uid)
    hit = found[found["event_id"] == saved["event_id"]]
    print(f"get_customer_events({uid}) sadrži sačuvan događaj: {len(hit) == 1}")
    print(hit[["event_id", "event_type", "source", "timestamp"]].to_string(index=False))


if __name__ == "__main__":
    main()
```

### lab/README.md

# Lab — Dan 1: implementacija event sloja i konverzije

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/data/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne
menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` (`pip install pandas` ili `.venv` iz `dm-ml/`).
* Generisan seeded dataset: `Day 1/data/events.csv` (već postoji u repou;
  regenerišeš sa `python -m app.data.generate_dataset --seed 42` iz `dm-ml/`).

## Zadatak (koraci)

1. **`create_event`** — vrati dict događaja sa normalizovanim `timestamp`
   (format `YYYY-MM-DD HH:MM:SS`), podrazumevanim `source` po tipu, i
   `quantity >= 1`. Nepoznat `event_type` -> `ValueError`.
2. **`EventStore.save_event`** — dodeli `event_id` (sledeći), dodaj red u
   `self.events` i vrati sačuvan dict. Ovo je **round-trip ugovor**.
3. **Upiti** — `get_session_events`, `get_product_events`, `get_customer_events`
   (filter po koloni; sort po `timestamp`).
4. **`calculate_funnel_counts` i `calculate_conversion_rate`** —
   konverzija = sesije sa kupovinom / sve sesije; prazan dataset -> `0.0`.
5. **Vežba (nezavisna):** dodaj `average_order_value(orders)` (prosek
   `total_price`) i upit `get_search_events(store)` (svi `search` događaji).

## Provera

```
# iz Day 1/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: ručnu implementaciju skladišta i analitike nad CSV-om.
* Ne radiš: MySQL, API, generator — to je u `dm-ml/` i koristi se u narednim
  danima. Generator je *jedini izvor istine* za podatke; ovaj lab ga samo čita.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.

### lab/starter.py

```
"""Starter za Day 1 lab.

Implementiraj funkcije/metode označene sa ``raise NotImplementedError``.
Kolone u ``events.csv`` (12): event_id, event_type, user_id, user_session,
product_id, category_id, price, quantity, source, timestamp,
recommendation_source, recommendation_position.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

VALID_EVENT_TYPES = frozenset({
    "product_view", "category_view", "search", "add_to_cart",
    "remove_from_cart", "purchase", "recommendation_impression",
    "recommendation_click",
})

PRODUCT_EVENT_TYPES = frozenset({
    "product_view", "add_to_cart", "remove_from_cart", "purchase",
    "recommendation_click",
})

EVENT_COLUMNS = [
    "event_id", "event_type", "user_id", "user_session", "product_id",
    "category_id", "price", "quantity", "source", "timestamp",
    "recommendation_source", "recommendation_position",
]

DEFAULT_SOURCE = {
    "product_view": "product_page",
    "category_view": "category_page",
    "search": "search_page",
    "add_to_cart": "product_page",
    "remove_from_cart": "cart",
    "purchase": "product_page",
    "recommendation_impression": "recommendation",
    "recommendation_click": "recommendation",
}


def create_event(
    event_type: str,
    user_id: Optional[int] = None,
    product_id: Optional[int] = None,
    user_session: Optional[str] = None,
    category_id: Optional[int] = None,
    quantity: int = 1,
    price: Optional[float] = None,
    source: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Kreira događaj kao dict (bez event_id). TODO: implementirati.

    Zahtevi:
    - nepoznat event_type -> ValueError
    - proizvodni tip bez product_id -> ValueError
    - quantity >= 1
    - timestamp: None -> trenutni UTC "YYYY-MM-DD HH:MM:SS"; string -> skrati
      na 19 karaktera (T -> razmak)
    - source: podrazumevano iz DEFAULT_SOURCE
    """
    raise NotImplementedError("implementiraj create_event")


class EventStore:
    def __init__(self, events: Optional[pd.DataFrame] = None):
        if events is None or len(events) == 0:
            events = pd.DataFrame(columns=EVENT_COLUMNS)
        self.events = events.reindex(columns=EVENT_COLUMNS).reset_index(drop=True)
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        if len(self.events) and self.events["event_id"].notna().any():
            return int(self.events["event_id"].max()) + 1
        return 1

    def save_event(self, event: dict) -> dict:
        """TODO: dodeli event_id, dodaj u self.events, vrati sačuvan dict."""
        raise NotImplementedError("implementiraj save_event")

    def get_session_events(self, session_id: str) -> pd.DataFrame:
        """TODO: događaji sesije, sortirani po timestamp."""
        raise NotImplementedError("implementiraj get_session_events")

    def get_product_events(self, product_id: int) -> pd.DataFrame:
        """TODO: svi događaji za proizvod."""
        raise NotImplementedError("implementiraj get_product_events")

    def get_customer_events(self, user_id: int) -> pd.DataFrame:
        """TODO: svi događaji korisnika, sortirani po timestamp."""
        raise NotImplementedError("implementiraj get_customer_events")

    @classmethod
    def from_csv(cls, path) -> "EventStore":
        return cls(pd.read_csv(path))


def load_seeded() -> EventStore:
    """Učitava ``Day 1/data/events.csv`` (path relativan na ovaj fajl)."""
    default_path = Path(__file__).resolve().parents[1] / "data" / "events.csv"
    return EventStore.from_csv(default_path)


def calculate_funnel_counts(events_df: pd.DataFrame) -> dict:
    """TODO: views/carts/purchases/sessions/sessions_with_purchase."""
    raise NotImplementedError("implementiraj calculate_funnel_counts")


def calculate_conversion_rate(events_df: pd.DataFrame) -> float:
    """TODO: sesije sa kupovinom / sve sesije; prazno -> 0.0."""
    raise NotImplementedError("implementiraj calculate_conversion_rate")


# --- Vežba (nezavisna) ------------------------------------------------------ #
def average_order_value(orders_df: pd.DataFrame) -> float:
    """TODO (vežba): prihod (suma total_price) / broj različitih order_id; prazno -> 0.0."""
    raise NotImplementedError("implementiraj average_order_value")


def get_search_events(store: EventStore) -> pd.DataFrame:
    """TODO (vežba): svi search događaji iz store-a."""
    raise NotImplementedError("implementiraj get_search_events")
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

DATA = Path(__file__).resolve().parents[1] / "data"


def test_create_event_validation():
    e = lab.create_event("product_view", user_id=1, product_id=5, timestamp="2026-01-05T10:00:00.123Z")
    assert e["timestamp"] == "2026-01-05 10:00:00" and e["source"] == "product_page"
    with pytest.raises(ValueError):
        lab.create_event("bogus")
    with pytest.raises(ValueError):
        lab.create_event("add_to_cart", user_id=1)
    with pytest.raises(ValueError):
        lab.create_event("purchase", product_id=1, quantity=0)
    assert len(lab.create_event("search")["timestamp"]) == 19


def test_store_roundtrip():
    s = lab.EventStore()
    a = s.save_event(lab.create_event("product_view", user_id=1, product_id=2, user_session="s1",
                                      timestamp="2026-01-02 00:00:00"))
    b = s.save_event(lab.create_event("product_view", user_id=1, product_id=3, user_session="s1",
                                      timestamp="2026-01-01 00:00:00"))
    assert (a["event_id"], b["event_id"]) == (1, 2)
    assert list(s.get_session_events("s1")["product_id"]) == [3, 2]
    assert len(s.get_product_events(2)) == 1 and len(s.get_customer_events(1)) == 2


def test_funnel_on_seed():
    ev = pd.read_csv(DATA / "events.csv")
    f = lab.calculate_funnel_counts(ev)
    assert f == {"views": 94220, "carts": 3159, "purchases": 1045, "sessions": 15361,
                 "sessions_with_purchase": 893}
    assert round(lab.calculate_conversion_rate(ev), 4) == round(893 / 15361, 4)
    assert lab.calculate_conversion_rate(ev.iloc[0:0]) == 0.0


def test_exercises():
    o = pd.read_csv(DATA / "orders.csv")
    assert lab.average_order_value(o) == pytest.approx(o["total_price"].sum() / o["order_id"].nunique())
    assert lab.average_order_value(o.iloc[0:0]) == 0.0
    s = lab.load_seeded()
    assert (lab.get_search_events(s)["event_type"] == "search").all()
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 1 lab-a (prvo probaj sam!)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import starter as _s
from starter import DEFAULT_SOURCE, EVENT_COLUMNS, PRODUCT_EVENT_TYPES, VALID_EVENT_TYPES  # noqa: F401


def create_event(event_type, user_id=None, product_id=None, user_session=None, category_id=None,
                 quantity=1, price=None, source=None, timestamp=None) -> dict:
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"nepoznat event_type: {event_type!r}")
    if event_type in PRODUCT_EVENT_TYPES and product_id is None:
        raise ValueError(f"{event_type} zahteva product_id")
    if quantity is None or int(quantity) < 1:
        raise ValueError("quantity mora biti >= 1")
    if timestamp is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts = str(timestamp).replace("T", " ")[:19]
    return {"event_type": event_type, "user_id": user_id, "user_session": user_session,
            "product_id": product_id, "category_id": category_id, "price": price, "quantity": int(quantity),
            "source": source or DEFAULT_SOURCE[event_type], "timestamp": ts,
            "recommendation_source": None, "recommendation_position": None}


class EventStore(_s.EventStore):
    def save_event(self, event: dict) -> dict:
        saved = {**{c: None for c in EVENT_COLUMNS}, **event, "event_id": self._next_id}
        self._next_id += 1
        row = pd.DataFrame([saved], columns=EVENT_COLUMNS)
        self.events = row if len(self.events) == 0 else pd.concat([self.events, row], ignore_index=True)
        return saved

    def _sorted(self, mask):
        return self.events[mask].sort_values("timestamp", kind="stable").reset_index(drop=True)

    def get_session_events(self, session_id):
        return self._sorted(self.events["user_session"] == session_id)

    def get_product_events(self, product_id):
        return self.events[pd.to_numeric(self.events["product_id"], errors="coerce") == product_id].reset_index(drop=True)

    def get_customer_events(self, user_id):
        return self._sorted(pd.to_numeric(self.events["user_id"], errors="coerce") == user_id)


def load_seeded() -> EventStore:
    return EventStore.from_csv(Path(__file__).resolve().parents[1] / "data" / "events.csv")


def calculate_funnel_counts(events_df):
    t = events_df["event_type"] if len(events_df) else pd.Series(dtype=str)
    return {"views": int((t == "product_view").sum()), "carts": int((t == "add_to_cart").sum()),
            "purchases": int((t == "purchase").sum()),
            "sessions": int(events_df["user_session"].nunique()) if len(events_df) else 0,
            "sessions_with_purchase": int(events_df.loc[t == "purchase", "user_session"].nunique()) if len(events_df) else 0}


def calculate_conversion_rate(events_df):
    f = calculate_funnel_counts(events_df)
    return f["sessions_with_purchase"] / f["sessions"] if f["sessions"] else 0.0


def average_order_value(orders_df):
    if orders_df is None or len(orders_df) == 0:
        return 0.0
    # jedan red = jedna stavka; stavke iste porudžbine dele order_id
    total = pd.to_numeric(orders_df["total_price"], errors="coerce").sum()
    return float(total / orders_df["order_id"].nunique())


def get_search_events(store):
    return store.events[store.events["event_type"] == "search"].reset_index(drop=True)
```

### data/events.csv i data/customers.csv (napomena)

Ova dva fajla nisu ugrađena u stranicu (`events.csv` ima 183 468 redova, `customers.csv` 3 000). Generišite ih lokalno:

```
cd dm-ml
.venv/bin/python -m app.data.generate_dataset --seed 42
.venv/bin/python -m app.data.verify_dataset
```

Generator je deterministički (seed 42): svako pokretanje daje bajt-po-bajt iste fajlove, a
`verify_dataset` proverava sha256 iz `data/metadata.json`. Svi brojevi u ovoj lekciji
(15 361 sesija, 893 porudžbine / 1 045 stavki, AOV 106.81) potiču iz tog izlaza.
