# Dan 3 — Purchase / Conversion Prediction API

- lesson_id: 113
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:46.215 updated: 2026-09-05 20:00:28.214
- summary: Hoće li ovaj korisnik kupiti? Feature-i → train/test split → klasifikator → verovatnoća → evaluacija → persistencija — i lekcija o data leakage-u. [subjects-import]


---

<!-- page_id 416 order 0 -->
## [Page] Materijal

# Dan 3 — Purchase / Conversion Prediction API

> *Hoće li ovaj korisnik kupiti? Feature-i → train/test split → klasifikator →
> verovatnoća → evaluacija → persistencija — i lekcija o **data leakage**-u.*

## Šta gradimo

ML pipeline koji iz istorije ponašanja (Day 1 događaji) i feature-a (Day 2)
predviđa **verovatnoću kupovine**: clean labeled training dataset (labela iz
prediction window-a) → stratifikovan split → klasifikator (logistička regresija
ili random forest) → verovatnoće → evaluacija (confusion matrix / precision /
recall / F1) → **persistencija modela** (joblib) — izloženo kroz FastAPI.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `build_training_dataset` | **statistical method** (agregacija + definicija labele) |
| `split_dataset` | **statistical method** (slučajni stratifikovani split) |
| `train_conversion_model` | **machine learning** (uči iz podataka) |
| `predict_conversion_probability` | **machine learning** (koristi naučeni model) |
| `majority_class_baseline` | **rule / heuristic** (baseline) |

## Application requirement

Postojeći e-commerce sistem (Nuxt CMS `dm-frontend` + FastAPI `dm-ml`) ima
događaje i analitiku (Day 1) i segmente (Day 2). Da bi marketing mogao da
odluči *kome da pošalje kampanju*, potrebna je **procena verovatnoće kupovine**
— model koji iz istorije kaže „ovaj korisnik će sa verovatnoćom p verovatno
kupiti u narednih 7 dana". Ovaj dan gradi taj servis; **odluku** (kome poslati
kampanju) pravi Day 4 targeting — model daje *ulaz*, ne odluku.

## Ciljevi učenja

Do kraja dana treba da:

* razlikujete **feature-e** od **labela** i objasnite zašto je labela u
  predikciji kupovine vremenski definisana (prediction window);
* izgradite supervised training dataset iz istorije (feature-i **pre**
  cut-off-a, labela iz window-a) bez **data leakage-a**;
* podelite podatke na train/test (stratifikovano) i objasnite zašto „random
  split koji vidi budućnost" vara;
* trenirate klasifikator (logistička regresija / random forest) i vratite
  **verovatnoću**, ne klasu;
* evaluirate confusion matrix / precision / recall / F1 i uporedite sa
  **majority-class baseline-om**;
* prepoznate **overfitting** i **leakage** i izmerite ih (before/after);
* perzistirate i ponovo učitate model (joblib) i koristite ga na novom
  korisniku.

## Preduslovi

Day 1 događaji (store + `events.csv`/`orders.csv`), Day 2 feature builder
(`app/ml/features.py`), pandas/sklearn osnove, FastAPI (Day 1–2 rute).

## Postojeći sistem (šta nasleđujemo)

* **Day 1 sloj:** `POST /events`, analitika, seeded dataset (3000 korisnika,
  183.468 događaja, 893 porudžbine).
* **Day 2 sloj:** feature-i po korisniku (RFM + brojači + AOV + konverzija),
  K-Means segmentacija, ručni RFM baseline, `SegmentationService`.
* **Nedostaje:** bilo kakva *nadgledana* predikcija — „ko će kupiti". Day 2
  segmentacija je *nenadgledana* (nema labele); Day 3 dodaje klasifikaciju i verovatnoće.

## Arhitektura

```
Day 1 događaji (events.csv, orders.csv)
      │
      ▼
app/ml/conversion.py     build_training_dataset (labela iz window-a, leaky flag)
                         split_dataset · train_conversion_model · evaluate_model
                         majority_class_baseline · predict_conversion_probability
                         run_leakage_exercise
      │
      ▼
app/services/conversion.py   ConversionService (pipeline + persistencija + fallback-i)
      │
      ▼
app/api/conversion_routes.py POST /models/conversion/train
                             GET /models/conversion/status
                             GET /customers/{id}/conversion-probability
      │
      ▼
dm-frontend admin /conversion   Nuxt admin (Nitro proxy /ml/** -> :3001)
```

## Korišćeni podaci

Izveden **labeled training dataset** iz Day 1 događaja + porudžbina — vidi
`data/README.md` i `metadata.json`:

| Kolona | Značenje (clean verzija) |
| --- | --- |
| `recency_days` | dani od **cut-off-a** do poslednje kupovine (ili aktivnosti) pre window-a |
| `frequency` / `monetary` | porudžbine **pre** cut-off-a (broj / ukupna vrednost) |
| `product_views` / `cart_adds` / `sessions` | brojači iz događaja pre cut-off-a |
| `aov` | prosečna porudžbina pre cut-off-a |
| `conversion` | sesije sa kupovinom / sve sesije pre cut-off-a |
| `will_purchase` | **labela**: 1 ako je korisnik kupio u 7-dnevnom prediction window-u |

Stanje (window = 7 dana): **2579** korisnika sa istorijom pre cut-off-a,
**163** kupca u window-u (pozitivna stopa **0.063**). Leaky verzija: **3000**
korisnika (uključuje i one koji su se „pojavili" tek u window-u).

## AI-ML koncept

* **Konverzija kao klasifikacija.** „Hoće li kupiti?" je binarno pitanje.
  Feature-i opisuju istoriju; **labela** je ono što predviđamo (kupovina u
  window-u). Ovo je **nadgledano učenje** (za razliku od K-Means u Day 2).
* **Vremenski cut-off.** Da bismo pošteno predvideli budućnost, feature-i se
  računaju **isključivo** na istoriji pre cut-off-a, a labela na periodu posle
  njega. Ako feature-i obuhvate window, model „vidi budućnost" — **leakage**.
* **Šta znači verovatnoća.** Logistička regresija vraća `P(will_purchase=1)`
  kroz logističku funkciju `σ(z) = 1/(1+e^{-z})`. Verovatnoća **nije** odluka —
  to je ulaz u odluku (Day 4).
* **Majority baseline.** Najprostiji model: „uvek predviđaj većinsku klasu".
  Na iskrivljenom skupu to daje visoku accuracy, ali precision/recall/F1 = 0 —
  „accuracy trap". Poređenje sa baseline-om je obavezno.
* **Confusion matrix / P/R/F1.** `[[tn, fp], [fn, tp]]`; precision = tp/(tp+fp),
  recall = tp/(tp+fn), F1 = harmonijska sredina. F1 je najbolji jedan broj za
  iskrivljene skupove.

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Clean training dataset (`app/ml/conversion.py`)

`build_training_dataset(events, orders, window_days=7, leaky=False)`:

* `cutoff = reference − window_days`, gde je `reference` najskoriji
  događaj/porudžbina (`2026-01-31 23:59:38` → cutoff `2026-01-24 23:59:38`).
* **Labela** `will_purchase`: 1 ako je korisnik kupio u `[cutoff, reference]`.
* **Clean** (`leaky=False`): feature-i na istoriji **pre** cut-off-a (recency u
  odnosu na cutoff). Model ne vidi window.
* **Leaky** (`leaky=True`): feature-i na **celoj** istoriji — `recency_days`
  direktno kodira labelu (kupac u window-u ima recency 0–6). Namerni bug.

### Korak 2 — Split

`split_dataset(df, test_size=0.3, random_state=42)` — stratifikovan
`train_test_split` po labeli (isti udeo pozitivnih u oba skupa). Budući da je
red = korisnik, a labela vremenski definisana, nasumični split je korektan
JEDINO ako su feature-i čisti.

### Korak 3 — Skaliranje + trening

* `scale_customer_features(features, feature_columns)` — **scaler se fit-uje na trening
  splitu**, a na test (i na nove korisnike) ide **transform-only** (ista
  disciplina kao Day 2; skaliranje na celom datasetu pre splita je čest bug).
* `train_conversion_model(X_train, y_train, model_type)` — `logistic_regression`
  (podrazumevano) ili `random_forest`; vraća fit-ovan sklearn estimator.

### Korak 4 — Evaluacija + baseline

* `evaluate_model(model, X, y)` (pozvan sa test splitom) — accuracy, confusion matrix,
  precision/recall/F1 (zaokruženo na 4 decimale).
* `majority_class_baseline(y)` — iste metrike za „uvek većinska klasa".

### Korak 5 — Leakage vežba

`run_leakage_exercise(events, orders, ...)` — isti model, isti split, clean vs
leaky feature-i; vraća metrike pre/posle (vidi „Comparison").

### Korak 6 — Servis + API

`ConversionService` orkestrira pipeline, perzistira artifacte u `app/models/`
(`conversion_model.joblib`, `conversion_scaler.joblib`, `conversion_meta.json`)
i servira status + verovatnoću korisnika. API rute u
`app/api/conversion_routes.py`.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `build_training_dataset(...)` | clean/leaky labeled dataset (labela iz window-a) | `app/ml/conversion.py` |
| `split_dataset(...)` | stratifikovan train/test split | `app/ml/conversion.py` |
| `train_conversion_model(...)` | logistic regression / random forest | `app/ml/conversion.py` |
| `evaluate_model(model, X, y)` | confusion matrix + precision/recall/F1 | `app/ml/conversion.py` |
| `majority_class_baseline(y)` | „uvek većinska klasa" (baseline) | `app/ml/conversion.py` |
| `predict_conversion_probability(model, scaled_row)` | verovatnoća `will_purchase=1` | `app/ml/conversion.py` |
| `run_leakage_exercise(...)` | clean vs leaky metrike (before/after) | `app/ml/conversion.py` |
| `ConversionService.train/get_status/get_customer_probability` | pipeline + persistencija + fallback-i | `app/services/conversion.py` |
| `app/data/generate_training.py` | generiše `Day 3/data/*` (byte-for-byte) | `app/data/generate_training.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `POST /models/conversion/train` | 200: `{model_type, metrics, baseline, leakage, ...}`; 422 nevalidan `model_type`/parametri; 503 prazan store |
| `GET /models/conversion/status` | 200: sažetak iz meta; **503 untrained\_model** (prvo treniraj) |
| `GET /customers/{id}/conversion-probability` | 200: `{user_id, probability, fallback, reason, base_rate}`; korisnik bez istorije → `probability=base_rate` (fallback, **nije greška**); 503 untrained\_model |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

## CMS integracija

Admin stranica `dm-frontend/app/pages/admin/conversion/index.vue`:

* **Treniraj** dugme → `POST /ml/models/conversion/train` (Nitro proxy `/ml/**`
  → `:3001`).
* Prikazuje metrike modela (accuracy/precision/recall/F1 + confusion matrix),
  majority baseline i **leakage before/after** poređenje.
* **Predikcija po korisniku:** unos `user_id` → `GET /ml/customers/{id}/conversion-probability`
  (prikazuje verovatnoću i fallback `base_rate` ako korisnik nema istoriju).
* Ako model nije treniran → poruka sa dugmetom (bez tihog praznog stanja).

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 3/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno: `build_training_dataset` (clean/leaky, recency do cut-off-a, isključivanje
window-only korisnika), `split_dataset` (stratifikacija, determinizam), `evaluate_model`
(perfektan model → P/R/F1=1; uvek-negativan → 0; poklapanje sa `sklearn.metrics`),
`majority_class_baseline` (accuracy trap), **`predict_conversion_probability`**
(untrained model → `ValueError`; prazan red → `ValueError`), leakage vežba
(leaky > clean, deterministički), API (train 200/422/503, status 503→200,
predikcija poznat/nepoznat, untrained 503, **model perzistiran i reloadovan**).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 3/examples/demo_conversion.py"`.
2. Pokreni vizualizaciju: `dm-ml/.venv/bin/python "Day 3/examples/visualize_confusion.py"` —
   `confusion_clean_vs_leaky.png` u `examples/`.
3. Pošalji `POST /models/conversion/train` pa pitaj `GET /customers/{id}/conversion-probability`
   za poznatog (npr. `2`) i nepoznatog korisnika.
4. Vidi `GET /models/conversion/status` pre treninga (503 — svesni fallback).
5. Pregledaj `Day 3/data/leaky_training_dataset.csv` i **pronađi leak**:
   koji feature direktno odaje labelu? (Odgovor: `recency_days` — kupac u
   window-u ima recency 0–6.)

## Comparison (baseline ugao)

**Majority baseline vs klasifikator** (test, logistic regression):

|  | accuracy | precision | recall | F1 |
| --- | --- | --- | --- | --- |
| majority baseline (uvek 0) | 0.9367 | 0.0 | 0.0 | 0.0 |
| logistic regression (clean) | 0.9393 | 0.6250 | 0.1020 | 0.1754 |
| random forest (clean) | 0.9380 | 0.5556 | 0.1020 | 0.1724 |

Baseline ima skoro istu accuracy (klasa je retka: 6.3 % pozitivnih) ali **nula** precision/recall/F1 — ne proglasi
nikoga pozitivnim. Klasifikator je „korisniji" (nađe neke buduće kupce) ali je
signala malo.

**Leakage before/after** (isti model, isti split, test):

|  | clean F1 | leaky F1 | ΔF1 |
| --- | --- | --- | --- |
| logistic\_regression | 0.1754 | 0.7619 | **+0.587** |
| random\_forest | 0.1724 | 1.0000 | **+0.828** |

Leaky model izgleda „savršeno" (RF F1=1.0!) jer feature-i vide window
(`recency_days` direktno kodira labelu). Poređenje je poenta vežbe: **ako je
F1 sumnjivo visok, prvo posumnjaj u leakage**.

## Evaluacija (kako znamo da je dobro)

* **Confusion matrix** (logistic, clean test, 774 korisnika): `[[722, 3], [44, 5]]` —
  model pronađe 5 od 49 pravih pozitivnih; precision 0.625, recall 0.102.
  F1 = 0.1754 — pošteno, slab signal.
* **Determinizam:** isti seed → isti split, isti model, iste metrike (test);
  `training_dataset.csv` byte-for-byte (sha256 u `metadata.json`).
* **Persistencija/reload:** `POST /models/conversion/train` upiše `*.joblib` +
  meta; predikcija **učitava model sa diska** (test + `Experiment` 3).
* **Fallback:** untrained → 503; korisnik bez istorije → `base_rate` sa
  `fallback=true, reason="no_history"`. Nema tihog `None`/`[]`.

## Česti bugovi

* **Leakovanje labele u feature-e** — najopasniji bug dana: `recency_days`/
  `frequency`/`monetary` iz **cele** istorije kada predviđaš kupovinu u
  window-u. Clean verzija računa feature-e do **cut-off-a**.
* **Random split koji vidi budućnost** — split je korektan samo ako su feature-i
  čisti; ako si feature-e gradio na celom datasetu, i split i metrike su lažni.
* **Evaluacija na trening skupu** — uvek evaluiraj na **test** splitu.
* **Predikcija klase umesto verovatnoće** — endpoint vraća `probability`
  (0..1), ne klasu; klasu bira aplikacija (Day 4).
* **Ne reloadovanje perzistiranog modela** — predikcija mora učitati `*.joblib`
  sa diska; ako radi sa modelom iz trening poziva, nisi dokazao persistenciju.
* **Scaler fit na celom datasetu** — fit na **trening** splitu, transform-only
  za test i nove korisnike.

## Šta rezultat NE dokazuje

* **Verovatnoća 0.36 nije odluka.** `P(will_purchase)=0.36` je ulaz u odluku —
  da li poslati kampanju, kome i po kojoj ceni odlučuje Day 4 (targeting).
* **Visok F1 na ovom datasetu ne generalizuje.** Brojevi važe za sintetički
  seed (42); na pravom store-u raspodela i signal su drugačiji.
* **Nizak F1 clean modela ne znači da je predikcija nemoguća.** Znači da je na
  ovom skupu signal slab; drugačiji feature-i, duži window ili više podataka bi
  dali druge brojeve.
* **Leaky F1=1.0 ne znači „odličan model".** Upravo suprotno — znači da je
  pokvaren. Leakage vežba pokazuje *zašto* se metrike gledaju sa sumnjom.
* **Klasifikacija ne objašnjava uzrok** (zašto će korisnik kupiti) i ne kaže šta
  da se uradi — to je posao analize i targetinga.

## Vežbe

1. **Dodaj feature i izmeri efekat** — npr. `days_since_last_purchase` (broj
   dana od poslednje kupovine pre cut-off-a, eksplicitno `-1`/NaN za ne-kupce);
   uporedi F1 pre/posle.
2. **Pronađi i ispravi posađeni leak** — uporedi `training_dataset.csv` i
   `leaky_training_dataset.csv`; objasni koji feature odaje labelu i pokaži
   ΔF1 pre/posle popravke.
3. **Uporedi logistic regression i random forest na istom splitu** — koristi
   `model_type="random_forest"` i objasni razliku u F1 (i zašto RF leaky daje
   F1=1.0 a logistička 0.76).
4. **Fallback za netreniran model** — testiraj `GET /customers/{id}/conversion-probability`
   pre treninga (503) i potvrdi da ne vraća tihi `null`.

## Sažetak

Iz Day 1 događaja i Day 2 feature-a napravio si **nadgledanu predikciju**:
clean labeled training dataset (labela iz prediction window-a), stratifikovan
split, klasifikator sa verovatnoćama, evaluaciju (confusion matrix /
precision / recall / F1) uz obavezan **majority baseline**, persistenciju i
reload modela — i izmerio **data leakage** (F1 0.18 → 0.76 logistička, → 1.0
RF) koji pokazuje koliko „gledanje u budućnost" ume da ulepša rezultat. Sledeći
korak: Day 4 tu verovatnoću pretvara u **odluku** (targeting). Pitanje koje
danas postavljaš: **kada metrike verovati, a kada posumnjati da model vara?**

---

<!-- page_id 417 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/leakage\_metrics.json

```
{
  "model_type": "logistic_regression",
  "window_days": 7,
  "test_size": 0.3,
  "random_state": 42,
  "n_test": 774,
  "clean": {
    "accuracy": 0.9393,
    "precision": 0.625,
    "recall": 0.102,
    "f1": 0.1754,
    "confusion_matrix": [
      [
        722,
        3
      ],
      [
        44,
        5
      ]
    ],
    "n": 774,
    "positive_class": 1
  },
  "leaky": {
    "accuracy": 0.9742,
    "precision": 0.9143,
    "recall": 0.6531,
    "f1": 0.7619,
    "confusion_matrix": [
      [
        722,
        3
      ],
      [
        17,
        32
      ]
    ],
    "n": 774,
    "positive_class": 1
  },
  "delta_f1": 0.5865
}
```

### data/leaky\_training\_dataset.csv

```
user_id,recency_days,frequency,monetary,product_views,cart_adds,sessions,aov,conversion,will_purchase
1,13,0,0.0,2,0,1,0.0,0.0,0
2,4,0,0.0,1,0,1,0.0,0.0,0
3,2,0,0.0,28,0,5,0.0,0.0,0
4,6,0,0.0,11,0,3,0.0,0.0,0
5,0,0,0.0,82,3,12,0.0,0.0,0
6,25,2,17.48,77,3,13,8.74,0.1538,0
7,16,0,0.0,11,0,3,0.0,0.0,0
8,0,0,0.0,20,0,5,0.0,0.0,0
9,0,0,0.0,8,0,3,0.0,0.0,0
10,21,2,47.97,164,8,21,23.98,0.0952,0
11,1,0,0.0,8,0,2,0.0,0.0,0
12,8,0,0.0,51,1,5,0.0,0.0,0
13,4,0,0.0,8,1,4,0.0,0.0,0
14,5,0,0.0,17,0,2,0.0,0.0,0
15,20,0,0.0,30,0,3,0.0,0.0,0
16,23,0,0.0,7,0,2,0.0,0.0,0
17,5,0,0.0,8,0,1,0.0,0.0,0
18,4,0,0.0,3,0,1,0.0,0.0,0
19,0,0,0.0,19,0,3,0.0,0.0,0
20,5,0,0.0,22,1,7,0.0,0.0,0
21,0,0,0.0,17,0,4,0.0,0.0,0
22,5,0,0.0,4,0,1,0.0,0.0,0
23,8,1,35.99,34,2,6,35.99,0.1667,0
24,0,0,0.0,14,0,3,0.0,0.0,0
25,5,0,0.0,40,4,6,0.0,0.0,0
26,5,0,0.0,10,0,3,0.0,0.0,0
27,1,0,0.0,29,0,5,0.0,0.0,0
28,14,0,0.0,14,0,4,0.0,0.0,0
29,11,0,0.0,12,0,3,0.0,0.0,0
30,8,2,55.48,116,4,13,27.74,0.1538,0
31,0,0,0.0,37,1,8,0.0,0.0,0
32,7,0,0.0,5,0,1,0.0,0.0,0
33,2,0,0.0,3,0,1,0.0,0.0,0
34,2,0,0.0,22,2,3,0.0,0.0,0
35,11,0,0.0,2,0,1,0.0,0.0,0
36,17,0,0.0,4,0,2,0.0,0.0,0
37,2,1,185.98,23,2,5,185.98,0.2,1
38,12,0,0.0,74,0,7,0.0,0.0,0
39,26,0,0.0,12,0,2,0.0,0.0,0
40,5,0,0.0,35,0,4,0.0,0.0,0
41,6,0,0.0,41,2,6,0.0,0.0,0
42,17,0,0.0,21,1,4,0.0,0.0,0
43,1,0,0.0,38,1,8,0.0,0.0,0
44,25,0,0.0,3,0,1,0.0,0.0,0
45,7,0,0.0,35,0,4,0.0,0.0,0
46,10,1,14.99,5,1,2,14.99,0.5,0
47,0,0,0.0,69,1,10,0.0,0.0,0
48,1,0,0.0,20,0,5,0.0,0.0,0
49,20,0,0.0,6,0,1,0.0,0.0,0
50,17,0,0.0,14,0,1,0.0,0.0,0
51,0,0,0.0,31,0,8,0.0,0.0,0
52,16,0,0.0,3,0,1,0.0,0.0,0
53,6,0,0.0,13,0,3,0.0,0.0,0
54,24,0,0.0,2,0,1,0.0,0.0,0
55,4,0,0.0,21,0,7,0.0,0.0,0
56,0,0,0.0,6,0,1,0.0,0.0,0
57,6,0,0.0,54,1,9,0.0,0.0,0
58,2,0,0.0,21,0,6,0.0,0.0,0
59,1,0,0.0,40,0,8,0.0,0.0,0
60,13,1,5.49,16,2,1,5.49,1.0,0
61,28,1,241.99,79,2,10,241.99,0.1,0
62,2,0,0.0,12,1,3,0.0,0.0,0
63,26,1,21.99,55,3,11,21.99,0.0909,0
64,29,1,15.99,50,4,9,15.99,0.1111,0
65,5,0,0.0,17,0,4,0.0,0.0,0
66,0,3,347.97,143,4,22,115.99,0.1364,1
67,2,1,37.99,35,1,5,37.99,0.2,1
68,6,0,0.0,12,0,6,0.0,0.0,0
69,3,2,112.97,36,3,5,56.48,0.4,1
70,9,0,0.0,1,0,1,0.0,0.0,0
71,1,0,0.0,24,1,5,0.0,0.0,0
72,5,0,0.0,79,1,9,0.0,0.0,0
73,7,0,0.0,17,0,5,0.0,0.0,0
74,0,1,161.97,46,2,8,161.97,0.125,1
75,4,0,0.0,35,0,5,0.0,0.0,0
76,0,0,0.0,7,0,1,0.0,0.0,0
77,10,0,0.0,25,1,5,0.0,0.0,0
78,0,0,0.0,22,1,4,0.0,0.0,0
79,22,0,0.0,6,0,1,0.0,0.0,0
80,21,0,0.0,6,0,1,0.0,0.0,0
81,4,0,0.0,20,0,5,0.0,0.0,0
82,3,0,0.0,3,0,1,0.0,0.0,0
83,6,0,0.0,18,0,2,0.0,0.0,0
84,3,0,0.0,10,0,2,0.0,0.0,0
85,18,1,193.98,16,1,2,193.98,0.5,0
86,26,0,0.0,1,0,1,0.0,0.0,0
87,1,0,0.0,64,1,12,0.0,0.0,0
88,8,0,0.0,9,0,1,0.0,0.0,0
89,28,2,215.19,28,2,5,107.6,0.4,0
90,0,0,0.0,11,0,3,0.0,0.0,0
91,2,0,0.0,6,0,1,0.0,0.0,0
92,0,0,0.0,55,2,5,0.0,0.0,0
93,0,1,17.99,18,1,4,17.99,0.25,1
94,1,0,0.0,58,0,13,0.0,0.0,0
95,5,0,0.0,58,0,5,0.0,0.0,0
96,7,0,0.0,2,0,1,0.0,0.0,0
97,0,0,0.0,14,0,7,0.0,0.0,0
98,19,0,0.0,1,0,1,0.0,0.0,0
99,0,0,0.0,3,0,2,0.0,0.0,0
100,7,0,0.0,8,0,1,0.0,0.0,0
101,19,0,0.0,7,0,1,0.0,0.0,0
102,3,0,0.0,7,0,2,0.0,0.0,0
103,1,0,0.0,2,0,1,0.0,0.0,0
104,0,0,0.0,4,0,2,0.0,0.0,0
105,5,0,0.0,1,0,1,0.0,0.0,0
106,4,0,0.0,99,2,13,0.0,0.0,0
107,26,0,0.0,5,0,1,0.0,0.0,0
108,9,1,90.99,30,1,4,90.99,0.25,0
109,1,0,0.0,3,0,1,0.0,0.0,0
110,0,0,0.0,82,3,13,0.0,0.0,0
111,19,1,22.99,25,1,4,22.99,0.25,0
112,11,0,0.0,7,0,1,0.0,0.0,0
113,6,0,0.0,24,3,5,0.0,0.0,0
114,3,0,0.0,71,3,10,0.0,0.0,0
115,2,0,0.0,83,2,12,0.0,0.0,0
116,18,1,37.99,40,1,4,37.99,0.25,0
117,25,0,0.0,5,0,2,0.0,0.0,0
118,20,0,0.0,4,0,1,0.0,0.0,0
119,23,0,0.0,11,0,2,0.0,0.0,0
120,30,1,265.99,14,3,5,265.99,0.2,0
121,2,0,0.0,73,2,14,0.0,0.0,0
122,1,0,0.0,3,0,1,0.0,0.0,0
123,2,0,0.0,11,0,2,0.0,0.0,0
124,6,0,0.0,8,0,2,0.0,0.0,0
125,5,1,15.99,28,2,7,15.99,0.1429,1
126,26,0,0.0,16,0,1,0.0,0.0,0
127,2,0,0.0,5,0,1,0.0,0.0,0
128,4,0,0.0,3,0,1,0.0,0.0,0
129,0,0,0.0,36,0,7,0.0,0.0,0
130,5,1,183.99,66,3,12,183.99,0.0833,1
131,27,1,442.98,83,5,16,442.98,0.0625,0
132,2,0,0.0,7,0,2,0.0,0.0,0
133,0,0,0.0,114,5,11,0.0,0.0,0
134,0,0,0.0,23,1,5,0.0,0.0,0
135,2,0,0.0,9,0,2,0.0,0.0,0
136,24,0,0.0,2,0,1,0.0,0.0,0
137,7,0,0.0,11,0,1,0.0,0.0,0
138,22,0,0.0,29,0,2,0.0,0.0,0
139,9,0,0.0,3,0,1,0.0,0.0,0
140,0,1,91.97,39,3,5,91.97,0.2,1
141,15,1,240.97,21,4,4,240.97,0.25,0
142,17,1,14.99,65,2,9,14.99,0.1111,0
143,25,1,30.99,19,2,2,30.99,0.5,0
144,0,0,0.0,52,1,5,0.0,0.0,0
145,5,0,0.0,13,0,3,0.0,0.0,0
146,26,1,103.99,21,2,3,103.99,0.3333,0
147,13,0,0.0,14,1,1,0.0,0.0,0
148,0,0,0.0,19,2,1,0.0,0.0,0
149,5,1,4.49,30,1,3,4.49,0.3333,1
150,9,2,663.83,73,5,13,331.92,0.1538,0
151,10,3,832.97,92,10,16,277.66,0.1875,0
152,26,4,557.57,91,6,15,139.39,0.2667,0
153,7,0,0.0,24,0,3,0.0,0.0,0
154,3,0,0.0,8,0,3,0.0,0.0,0
155,14,0,0.0,4,0,1,0.0,0.0,0
156,7,0,0.0,34,0,5,0.0,0.0,0
157,0,0,0.0,23,0,3,0.0,0.0,0
158,12,0,0.0,13,0,5,0.0,0.0,0
159,1,0,0.0,26,0,4,0.0,0.0,0
160,12,1,110.99,86,4,8,110.99,0.125,0
161,15,0,0.0,18,1,1,0.0,0.0,0
162,9,0,0.0,14,0,3,0.0,0.0,0
163,2,0,0.0,3,0,1,0.0,0.0,0
164,28,1,19.17,53,2,8,19.17,0.125,0
165,1,0,0.0,26,0,4,0.0,0.0,0
166,2,0,0.0,6,0,4,0.0,0.0,0
167,9,3,187.97,138,8,18,62.66,0.1667,0
168,22,1,15.99,9,1,1,15.99,1.0,0
169,9,4,835.95,133,10,28,208.99,0.1429,0
170,27,0,0.0,4,1,1,0.0,0.0,0
171,14,0,0.0,5,0,1,0.0,0.0,0
172,0,0,0.0,18,0,6,0.0,0.0,0
173,3,0,0.0,27,0,4,0.0,0.0,0
174,16,0,0.0,1,0,1,0.0,0.0,0
175,13,0,0.0,10,0,2,0.0,0.0,0
176,13,0,0.0,2,0,1,0.0,0.0,0
177,2,0,0.0,5,0,1,0.0,0.0,0
178,20,0,0.0,6,0,2,0.0,0.0,0
179,1,0,0.0,43,1,10,0.0,0.0,0
180,4,2,79.98,23,2,3,39.99,0.6667,1
181,10,1,30.99,48,1,8,30.99,0.125,0
182,3,0,0.0,17,0,4,0.0,0.0,0
183,7,0,0.0,8,0,2,0.0,0.0,0
184,24,0,0.0,2,0,1,0.0,0.0,0
185,23,1,815.98,44,3,9,815.98,0.1111,0
186,7,0,0.0,51,2,8,0.0,0.0,0
187,10,1,11.99,48,3,9,11.99,0.1111,0
188,20,0,0.0,3,0,1,0.0,0.0,0
189,9,1,56.99,59,3,6,56.99,0.1667,0
190,20,3,196.5,65,5,12,65.5,0.25,0
191,0,0,0.0,33,2,9,0.0,0.0,0
192,5,0,0.0,10,0,5,0.0,0.0,0
193,5,1,140.99,42,1,5,140.99,0.2,1
194,3,0,0.0,16,0,4,0.0,0.0,0
195,13,1,49.98,189,4,21,49.98,0.0476,0
196,3,0,0.0,151,2,23,0.0,0.0,0
197,0,0,0.0,17,1,3,0.0,0.0,0
198,3,0,0.0,8,1,2,0.0,0.0,0
199,7,0,0.0,40,0,7,0.0,0.0,0
200,7,0,0.0,7,0,3,0.0,0.0,0
201,13,0,0.0,30,2,2,0.0,0.0,0
202,0,0,0.0,33,1,3,0.0,0.0,0
203,2,0,0.0,4,0,1,0.0,0.0,0
204,1,2,787.98,70,5,15,393.99,0.1333,1
205,16,2,92.98,99,3,16,46.49,0.125,0
206,25,1,17.99,17,1,3,17.99,0.3333,0
207,26,0,0.0,4,0,1,0.0,0.0,0
208,2,0,0.0,88,2,11,0.0,0.0,0
209,2,0,0.0,79,0,10,0.0,0.0,0
210,28,0,0.0,12,1,1,0.0,0.0,0
211,1,0,0.0,38,1,5,0.0,0.0,0
212,15,0,0.0,15,1,3,0.0,0.0,0
213,2,0,0.0,59,5,8,0.0,0.0,0
214,7,0,0.0,17,1,2,0.0,0.0,0
215,5,3,60.43,194,6,23,20.14,0.1304,1
216,11,3,134.46,138,7,17,44.82,0.1765,0
217,6,3,86.96,86,4,12,28.99,0.25,1
218,4,0,0.0,20,0,6,0.0,0.0,0
219,14,0,0.0,50,0,7,0.0,0.0,0
220,26,1,46.99,91,2,12,46.99,0.0833,0
221,15,1,59.99,68,4,13,59.99,0.0769,0
222,27,1,65.99,24,3,4,65.99,0.25,0
223,2,0,0.0,6,0,2,0.0,0.0,0
224,6,0,0.0,3,0,1,0.0,0.0,0
225,2,0,0.0,22,1,2,0.0,0.0,0
226,30,0,0.0,11,1,1,0.0,0.0,0
227,1,0,0.0,71,2,8,0.0,0.0,0
228,10,0,0.0,4,0,1,0.0,0.0,0
229,9,0,0.0,15,0,1,0.0,0.0,0
230,7,3,139.96,97,6,18,46.65,0.1667,0
231,0,2,552.96,69,3,7,276.48,0.2857,1
232,1,0,0.0,18,0,4,0.0,0.0,0
233,10,0,0.0,6,0,1,0.0,0.0,0
234,30,1,46.99,4,1,1,46.99,1.0,0
235,1,1,20.99,101,5,15,20.99,0.0667,1
236,4,0,0.0,13,0,3,0.0,0.0,0
237,19,0,0.0,10,0,3,0.0,0.0,0
238,25,0,0.0,5,0,1,0.0,0.0,0
239,2,0,0.0,5,0,1,0.0,0.0,0
240,12,0,0.0,10,0,4,0.0,0.0,0
241,6,0,0.0,45,2,8,0.0,0.0,0
242,8,0,0.0,26,0,5,0.0,0.0,0
243,1,0,0.0,26,0,4,0.0,0.0,0
244,15,1,23.98,66,4,9,23.98,0.1111,0
245,4,0,0.0,40,2,10,0.0,0.0,0
246,3,0,0.0,17,0,4,0.0,0.0,0
247,20,1,24.99,8,2,2,24.99,0.5,0
248,0,0,0.0,2,0,1,0.0,0.0,0
249,28,0,0.0,7,0,1,0.0,0.0,0
250,0,0,0.0,30,1,4,0.0,0.0,0
251,0,0,0.0,131,2,16,0.0,0.0,0
252,11,0,0.0,44,0,6,0.0,0.0,0
253,6,0,0.0,99,0,10,0.0,0.0,0
254,1,0,0.0,40,2,7,0.0,0.0,0
255,9,0,0.0,3,0,1,0.0,0.0,0
256,20,2,145.53,52,4,8,72.76,0.25,0
257,15,0,0.0,12,1,3,0.0,0.0,0
258,4,0,0.0,21,0,3,0.0,0.0,0
259,3,0,0.0,8,0,1,0.0,0.0,0
260,3,1,172.99,15,1,4,172.99,0.25,1
261,10,0,0.0,4,0,1,0.0,0.0,0
262,2,0,0.0,9,0,3,0.0,0.0,0
263,2,0,0.0,3,0,1,0.0,0.0,0
264,0,0,0.0,119,3,12,0.0,0.0,0
265,28,0,0.0,3,0,1,0.0,0.0,0
266,14,1,493.99,75,1,15,493.99,0.0667,0
267,2,0,0.0,17,2,4,0.0,0.0,0
268,4,0,0.0,3,0,1,0.0,0.0,0
269,22,2,37.64,79,2,6,18.82,0.3333,0
270,5,0,0.0,71,2,15,0.0,0.0,0
271,25,0,0.0,5,0,1,0.0,0.0,0
272,28,0,0.0,9,0,1,0.0,0.0,0
273,21,0,0.0,4,0,1,0.0,0.0,0
274,7,1,6.98,85,2,10,6.98,0.1,0
275,26,1,85.99,43,1,5,85.99,0.2,0
276,1,0,0.0,43,1,5,0.0,0.0,0
277,0,4,128.96,149,12,26,32.24,0.1538,1
278,0,0,0.0,16,2,4,0.0,0.0,0
279,21,0,0.0,17,1,3,0.0,0.0,0
280,10,0,0.0,49,0,7,0.0,0.0,0
281,3,1,204.99,44,3,10,204.99,0.1,1
282,1,0,0.0,1,0,1,0.0,0.0,0
283,2,0,0.0,1,0,1,0.0,0.0,0
284,5,0,0.0,54,3,8,0.0,0.0,0
285,2,0,0.0,26,0,1,0.0,0.0,0
286,23,1,25.99,78,2,10,25.99,0.1,0
287,2,0,0.0,4,0,1,0.0,0.0,0
288,0,0,0.0,59,1,5,0.0,0.0,0
289,4,0,0.0,12,0,1,0.0,0.0,0
290,15,1,8.49,40,1,6,8.49,0.1667,0
291,0,0,0.0,27,1,9,0.0,0.0,0
292,6,0,0.0,21,0,2,0.0,0.0,0
293,0,0,0.0,14,1,3,0.0,0.0,0
294,0,0,0.0,27,0,4,0.0,0.0,0
295,15,0,0.0,2,1,1,0.0,0.0,0
296,16,0,0.0,3,0,1,0.0,0.0,0
297,1,0,0.0,10,0,2,0.0,0.0,0
298,9,3,267.07,68,5,13,89.02,0.2308,0
299,8,0,0.0,20,1,1,0.0,0.0,0
300,2,0,0.0,14,2,3,0.0,0.0,0
301,7,0,0.0,9,0,4,0.0,0.0,0
302,5,0,0.0,2,0,1,0.0,0.0,0
303,3,0,0.0,5,1,2,0.0,0.0,0
304,1,0,0.0,12,1,3,0.0,0.0,0
305,5,0,0.0,10,0,3,0.0,0.0,0
306,0,2,264.98,66,4,14,132.49,0.1429,1
307,9,0,0.0,1,0,1,0.0,0.0,0
308,0,0,0.0,12,0,3,0.0,0.0,0
309,18,0,0.0,2,0,1,0.0,0.0,0
310,9,0,0.0,2,0,1,0.0,0.0,0
311,2,0,0.0,3,0,1,0.0,0.0,0
312,15,0,0.0,7,0,4,0.0,0.0,0
313,5,0,0.0,20,0,5,0.0,0.0,0
314,2,1,10.98,19,2,7,10.98,0.1429,1
315,0,0,0.0,50,1,5,0.0,0.0,0
316,0,0,0.0,5,0,1,0.0,0.0,0
317,7,0,0.0,19,1,4,0.0,0.0,0
318,13,1,89.99,40,2,7,89.99,0.1429,0
319,21,1,141.99,48,2,10,141.99,0.1,0
320,0,0,0.0,21,0,2,0.0,0.0,0
321,19,0,0.0,2,0,1,0.0,0.0,0
322,6,0,0.0,1,0,1,0.0,0.0,0
323,17,0,0.0,5,0,1,0.0,0.0,0
324,25,0,0.0,2,0,1,0.0,0.0,0
325,8,0,0.0,8,0,1,0.0,0.0,0
326,28,1,7.76,50,3,11,7.76,0.0909,0
327,1,0,0.0,3,0,1,0.0,0.0,0
328,3,0,0.0,6,0,1,0.0,0.0,0
329,0,0,0.0,9,1,3,0.0,0.0,0
330,26,0,0.0,2,0,1,0.0,0.0,0
331,0,0,0.0,123,2,16,0.0,0.0,0
332,15,0,0.0,5,0,3,0.0,0.0,0
333,0,0,0.0,47,1,7,0.0,0.0,0
334,15,0,0.0,6,0,1,0.0,0.0,0
335,24,0,0.0,3,0,1,0.0,0.0,0
336,26,0,0.0,3,0,1,0.0,0.0,0
337,20,3,235.87,105,7,13,78.62,0.2308,0
338,0,0,0.0,78,1,9,0.0,0.0,0
339,14,0,0.0,8,0,2,0.0,0.0,0
340,4,0,0.0,8,1,1,0.0,0.0,0
341,2,0,0.0,31,2,4,0.0,0.0,0
342,6,0,0.0,30,1,3,0.0,0.0,0
343,1,0,0.0,7,0,1,0.0,0.0,0
344,27,1,61.97,80,3,14,61.97,0.0714,0
345,5,0,0.0,2,0,1,0.0,0.0,0
346,0,0,0.0,41,1,8,0.0,0.0,0
347,12,0,0.0,6,0,1,0.0,0.0,0
348,9,0,0.0,9,0,1,0.0,0.0,0
349,20,0,0.0,1,0,1,0.0,0.0,0
350,10,1,48.98,61,5,11,48.98,0.0909,0
351,1,0,0.0,8,0,2,0.0,0.0,0
352,4,0,0.0,8,0,1,0.0,0.0,0
353,1,0,0.0,19,5,2,0.0,0.0,0
354,3,0,0.0,44,0,8,0.0,0.0,0
355,7,0,0.0,9,0,2,0.0,0.0,0
356,14,1,48.99,15,1,3,48.99,0.3333,0
357,0,0,0.0,18,3,6,0.0,0.0,0
358,1,0,0.0,3,0,1,0.0,0.0,0
359,12,0,0.0,21,1,7,0.0,0.0,0
360,1,0,0.0,72,1,17,0.0,0.0,0
361,2,0,0.0,21,1,4,0.0,0.0,0
362,1,0,0.0,12,0,4,0.0,0.0,0
363,7,0,0.0,1,0,1,0.0,0.0,0
364,12,0,0.0,6,0,2,0.0,0.0,0
365,25,1,150.99,15,1,1,150.99,1.0,0
366,3,0,0.0,67,2,10,0.0,0.0,0
367,1,0,0.0,18,0,5,0.0,0.0,0
368,16,2,173.98,115,3,18,86.99,0.1111,0
369,2,0,0.0,27,1,6,0.0,0.0,0
370,7,0,0.0,9,0,1,0.0,0.0,0
371,8,0,0.0,79,1,6,0.0,0.0,0
372,8,0,0.0,43,0,4,0.0,0.0,0
373,14,1,17.99,128,6,13,17.99,0.0769,0
374,5,0,0.0,2,0,1,0.0,0.0,0
375,5,3,405.97,80,7,12,135.32,0.25,1
376,8,0,0.0,17,0,5,0.0,0.0,0
377,11,0,0.0,3,0,3,0.0,0.0,0
378,0,0,0.0,22,2,4,0.0,0.0,0
379,20,0,0.0,1,0,1,0.0,0.0,0
380,13,0,0.0,21,0,4,0.0,0.0,0
381,3,0,0.0,26,1,4,0.0,0.0,0
382,12,0,0.0,2,0,1,0.0,0.0,0
383,2,0,0.0,29,1,4,0.0,0.0,0
384,6,0,0.0,6,1,3,0.0,0.0,0
385,7,0,0.0,2,0,1,0.0,0.0,0
386,10,0,0.0,6,0,1,0.0,0.0,0
387,0,0,0.0,64,6,12,0.0,0.0,0
388,15,1,69.98,57,1,8,69.98,0.125,0
389,4,0,0.0,11,1,4,0.0,0.0,0
390,28,2,241.48,75,5,11,120.74,0.1818,0
391,5,0,0.0,5,0,2,0.0,0.0,0
392,29,0,0.0,3,0,1,0.0,0.0,0
393,12,0,0.0,28,0,2,0.0,0.0,0
394,2,5,568.92,161,15,32,113.78,0.1562,1
395,4,7,883.18,296,12,55,126.17,0.1273,1
396,2,3,117.97,159,9,28,39.32,0.1071,1
397,6,0,0.0,63,0,5,0.0,0.0,0
398,3,0,0.0,78,1,9,0.0,0.0,0
399,1,1,36.99,65,4,8,36.99,0.125,1
400,0,0,0.0,70,1,7,0.0,0.0,0
401,3,0,0.0,4,0,1,0.0,0.0,0
402,6,0,0.0,43,1,7,0.0,0.0,0
403,18,0,0.0,20,0,3,0.0,0.0,0
404,14,0,0.0,6,0,1,0.0,0.0,0
405,11,1,725.99,94,2,11,725.99,0.0909,0
406,10,1,69.98,40,1,6,69.98,0.1667,0
407,3,0,0.0,78,0,9,0.0,0.0,0
408,0,0,0.0,30,1,7,0.0,0.0,0
409,1,4,441.92,254,19,51,110.48,0.0784,1
410,11,0,0.0,26,2,5,0.0,0.0,0
411,7,0,0.0,1,0,1,0.0,0.0,0
412,5,0,0.0,21,1,3,0.0,0.0,0
413,2,0,0.0,3,0,1,0.0,0.0,0
414,12,0,0.0,3,0,1,0.0,0.0,0
415,13,0,0.0,6,0,2,0.0,0.0,0
416,29,0,0.0,6,0,1,0.0,0.0,0
417,1,1,89.99,121,3,23,89.99,0.0435,1
418,1,0,0.0,6,0,1,0.0,0.0,0
419,0,0,0.0,59,2,8,0.0,0.0,0
420,2,0,0.0,8,0,3,0.0,0.0,0
421,7,1,10.99,44,1,10,10.99,0.1,0
422,0,0,0.0,8,0,1,0.0,0.0,0
423,2,0,0.0,1,0,1,0.0,0.0,0
424,0,0,0.0,40,1,6,0.0,0.0,0
425,1,0,0.0,106,1,15,0.0,0.0,0
426,9,0,0.0,6,0,1,0.0,0.0,0
427,7,0,0.0,14,0,1,0.0,0.0,0
428,6,0,0.0,8,1,2,0.0,0.0,0
429,0,0,0.0,2,0,1,0.0,0.0,0
430,10,0,0.0,16,0,3,0.0,0.0,0
431,0,0,0.0,9,0,1,0.0,0.0,0
432,2,0,0.0,2,0,1,0.0,0.0,0
433,4,0,0.0,16,1,5,0.0,0.0,0
434,12,0,0.0,45,4,6,0.0,0.0,0
435,0,0,0.0,4,0,2,0.0,0.0,0
436,7,0,0.0,8,0,3,0.0,0.0,0
437,3,0,0.0,54,1,6,0.0,0.0,0
438,15,0,0.0,3,0,1,0.0,0.0,0
439,1,0,0.0,108,2,15,0.0,0.0,0
440,21,0,0.0,3,0,1,0.0,0.0,0
441,21,0,0.0,14,0,1,0.0,0.0,0
442,3,0,0.0,6,0,1,0.0,0.0,0
443,4,0,0.0,11,0,1,0.0,0.0,0
444,14,0,0.0,40,0,7,0.0,0.0,0
445,27,0,0.0,1,0,1,0.0,0.0,0
446,3,1,73.99,24,1,5,73.99,0.2,1
447,29,1,34.99,51,1,8,34.99,0.125,0
448,3,0,0.0,10,1,4,0.0,0.0,0
449,11,2,177.97,220,11,36,88.98,0.0556,0
450,13,0,0.0,36,2,3,0.0,0.0,0
451,3,0,0.0,2,0,1,0.0,0.0,0
452,0,0,0.0,18,0,2,0.0,0.0,0
453,20,0,0.0,3,0,2,0.0,0.0,0
454,5,0,0.0,20,1,7,0.0,0.0,0
455,0,0,0.0,70,1,9,0.0,0.0,0
456,11,1,92.99,27,1,5,92.99,0.2,0
457,6,0,0.0,1,0,1,0.0,0.0,0
458,5,0,0.0,16,0,5,0.0,0.0,0
459,8,0,0.0,43,3,7,0.0,0.0,0
460,8,0,0.0,24,0,7,0.0,0.0,0
461,11,2,345.98,80,5,16,172.99,0.125,0
462,2,0,0.0,12,0,1,0.0,0.0,0
463,6,0,0.0,3,0,1,0.0,0.0,0
464,21,1,15.99,45,4,12,15.99,0.0833,0
465,4,0,0.0,18,1,5,0.0,0.0,0
466,18,0,0.0,4,0,1,0.0,0.0,0
467,19,0,0.0,6,0,3,0.0,0.0,0
468,14,1,108.97,50,2,5,108.97,0.2,0
469,9,0,0.0,7,0,3,0.0,0.0,0
470,6,0,0.0,8,1,3,0.0,0.0,0
471,2,0,0.0,53,0,7,0.0,0.0,0
472,7,0,0.0,1,0,1,0.0,0.0,0
473,27,0,0.0,6,0,2,0.0,0.0,0
474,0,0,0.0,25,0,6,0.0,0.0,0
475,20,0,0.0,3,0,1,0.0,0.0,0
476,10,4,478.92,100,7,15,119.73,0.2667,0
477,9,2,235.98,82,6,16,117.99,0.125,0
478,8,0,0.0,21,0,6,0.0,0.0,0
479,2,0,0.0,25,0,6,0.0,0.0,0
480,6,0,0.0,1,0,1,0.0,0.0,0
481,27,0,0.0,2,0,1,0.0,0.0,0
482,2,0,0.0,11,0,3,0.0,0.0,0
483,20,1,30.99,74,3,16,30.99,0.0625,0
484,28,0,0.0,3,1,1,0.0,0.0,0
485,0,0,0.0,19,1,2,0.0,0.0,0
486,26,3,81.08,77,4,14,27.03,0.2143,0
487,0,0,0.0,9,0,1,0.0,0.0,0
488,1,1,440.99,73,2,9,440.99,0.1111,1
489,13,0,0.0,8,0,2,0.0,0.0,0
490,24,0,0.0,2,0,1,0.0,0.0,0
491,8,0,0.0,14,2,3,0.0,0.0,0
492,13,0,0.0,1,0,1,0.0,0.0,0
493,14,0,0.0,29,0,5,0.0,0.0,0
494,7,0,0.0,12,1,2,0.0,0.0,0
495,8,0,0.0,9,0,3,0.0,0.0,0
496,3,0,0.0,5,0,2,0.0,0.0,0
497,4,0,0.0,14,0,1,0.0,0.0,0
498,19,0,0.0,9,0,1,0.0,0.0,0
499,2,0,0.0,17,0,4,0.0,0.0,0
500,4,0,0.0,60,1,6,0.0,0.0,0
501,5,0,0.0,1,0,1,0.0,0.0,0
502,6,0,0.0,4,0,1,0.0,0.0,0
503,13,0,0.0,20,0,5,0.0,0.0,0
504,7,0,0.0,48,0,8,0.0,0.0,0
505,2,0,0.0,47,5,8,0.0,0.0,0
506,13,0,0.0,6,0,1,0.0,0.0,0
507,2,0,0.0,105,1,11,0.0,0.0,0
508,5,0,0.0,18,1,1,0.0,0.0,0
509,0,0,0.0,25,1,6,0.0,0.0,0
510,29,0,0.0,6,0,1,0.0,0.0,0
511,2,0,0.0,1,0,1,0.0,0.0,0
512,0,0,0.0,70,1,9,0.0,0.0,0
513,10,0,0.0,3,0,1,0.0,0.0,0
514,6,0,0.0,62,0,8,0.0,0.0,0
515,4,4,1454.92,160,9,32,363.73,0.125,1
516,25,1,9.49,56,3,8,9.49,0.125,0
517,10,3,338.96,130,4,18,112.99,0.1667,0
518,4,0,0.0,29,1,6,0.0,0.0,0
519,4,4,238.93,83,7,13,59.73,0.3077,1
520,16,0,0.0,16,0,3,0.0,0.0,0
521,28,0,0.0,1,0,1,0.0,0.0,0
522,23,1,23.99,67,4,9,23.99,0.1111,0
523,8,0,0.0,6,0,1,0.0,0.0,0
524,5,0,0.0,1,0,1,0.0,0.0,0
525,3,1,16.98,30,3,5,16.98,0.2,1
526,19,0,0.0,10,0,1,0.0,0.0,0
527,20,0,0.0,1,0,1,0.0,0.0,0
528,27,0,0.0,7,0,2,0.0,0.0,0
529,3,0,0.0,2,0,1,0.0,0.0,0
530,1,0,0.0,28,0,10,0.0,0.0,0
531,26,1,150.1,78,5,6,150.1,0.1667,0
532,0,0,0.0,74,0,12,0.0,0.0,0
533,17,0,0.0,14,0,3,0.0,0.0,0
534,3,0,0.0,2,0,1,0.0,0.0,0
535,2,0,0.0,14,0,3,0.0,0.0,0
536,9,1,16.98,15,1,4,16.98,0.25,0
537,6,0,0.0,6,1,1,0.0,0.0,0
538,8,0,0.0,29,2,6,0.0,0.0,0
539,25,1,25.36,68,3,13,25.36,0.0769,0
540,1,0,0.0,69,2,8,0.0,0.0,0
541,21,0,0.0,5,0,1,0.0,0.0,0
542,5,0,0.0,19,0,5,0.0,0.0,0
543,18,2,76.96,26,2,3,38.48,0.6667,0
544,6,1,13.99,181,3,19,13.99,0.0526,1
545,21,0,0.0,6,0,3,0.0,0.0,0
546,16,0,0.0,8,1,2,0.0,0.0,0
547,13,1,96.98,168,5,21,96.98,0.0476,0
548,0,0,0.0,6,0,1,0.0,0.0,0
549,22,0,0.0,8,0,2,0.0,0.0,0
550,6,0,0.0,29,0,5,0.0,0.0,0
551,14,0,0.0,5,0,3,0.0,0.0,0
552,13,0,0.0,6,0,3,0.0,0.0,0
553,0,0,0.0,151,4,23,0.0,0.0,0
554,14,0,0.0,5,0,1,0.0,0.0,0
555,24,1,158.99,28,4,7,158.99,0.1429,0
556,30,0,0.0,6,0,1,0.0,0.0,0
557,7,0,0.0,6,0,1,0.0,0.0,0
558,2,0,0.0,1,0,1,0.0,0.0,0
559,13,0,0.0,3,0,1,0.0,0.0,0
560,8,0,0.0,2,0,1,0.0,0.0,0
561,20,0,0.0,4,0,1,0.0,0.0,0
562,5,0,0.0,24,0,5,0.0,0.0,0
563,23,0,0.0,1,0,1,0.0,0.0,0
564,12,2,72.48,50,4,10,36.24,0.2,0
565,5,0,0.0,10,0,1,0.0,0.0,0
566,6,0,0.0,16,0,2,0.0,0.0,0
567,21,0,0.0,10,0,2,0.0,0.0,0
568,29,0,0.0,9,1,2,0.0,0.0,0
569,1,0,0.0,9,0,1,0.0,0.0,0
570,7,0,0.0,5,0,2,0.0,0.0,0
571,2,1,16.47,27,2,5,16.47,0.2,1
572,2,0,0.0,31,1,4,0.0,0.0,0
573,7,0,0.0,15,0,4,0.0,0.0,0
574,8,0,0.0,23,0,8,0.0,0.0,0
575,17,0,0.0,15,0,3,0.0,0.0,0
576,0,0,0.0,16,1,4,0.0,0.0,0
577,4,0,0.0,110,3,14,0.0,0.0,0
578,1,0,0.0,3,0,1,0.0,0.0,0
579,4,0,0.0,17,1,2,0.0,0.0,0
580,7,0,0.0,7,0,4,0.0,0.0,0
581,1,0,0.0,68,0,12,0.0,0.0,0
582,9,0,0.0,2,0,2,0.0,0.0,0
583,1,0,0.0,88,2,9,0.0,0.0,0
584,5,0,0.0,36,2,5,0.0,0.0,0
585,0,1,54.99,36,1,4,54.99,0.25,1
586,5,0,0.0,9,1,4,0.0,0.0,0
587,1,0,0.0,26,0,4,0.0,0.0,0
588,18,0,0.0,4,0,1,0.0,0.0,0
589,6,0,0.0,10,0,1,0.0,0.0,0
590,1,0,0.0,9,1,1,0.0,0.0,0
591,6,0,0.0,14,1,1,0.0,0.0,0
592,29,0,0.0,11,2,3,0.0,0.0,0
593,5,0,0.0,44,1,7,0.0,0.0,0
594,1,0,0.0,2,0,1,0.0,0.0,0
595,8,2,47.97,36,3,5,23.98,0.4,0
596,19,0,0.0,14,0,1,0.0,0.0,0
597,12,0,0.0,7,0,1,0.0,0.0,0
598,9,0,0.0,6,0,2,0.0,0.0,0
599,0,1,23.99,25,2,4,23.99,0.25,1
600,28,1,110.99,134,5,26,110.99,0.0385,0
601,6,3,316.96,63,4,13,105.65,0.2308,1
602,8,2,268.98,104,4,18,134.49,0.1111,0
603,10,0,0.0,5,0,1,0.0,0.0,0
604,4,0,0.0,4,0,1,0.0,0.0,0
605,14,1,241.99,46,2,8,241.99,0.125,0
606,11,0,0.0,2,0,1,0.0,0.0,0
607,19,1,25.99,40,1,6,25.99,0.1667,0
608,1,0,0.0,17,2,3,0.0,0.0,0
609,2,0,0.0,5,0,1,0.0,0.0,0
610,8,0,0.0,89,1,13,0.0,0.0,0
611,0,0,0.0,17,0,3,0.0,0.0,0
612,1,0,0.0,20,0,6,0.0,0.0,0
613,23,0,0.0,12,0,2,0.0,0.0,0
614,22,1,165.99,43,4,8,165.99,0.125,0
615,4,0,0.0,55,0,10,0.0,0.0,0
616,4,0,0.0,7,0,1,0.0,0.0,0
617,0,0,0.0,68,1,12,0.0,0.0,0
618,9,0,0.0,8,1,3,0.0,0.0,0
619,20,1,204.99,13,1,2,204.99,0.5,0
620,4,3,350.95,145,9,28,116.98,0.1071,1
621,2,0,0.0,5,0,1,0.0,0.0,0
622,26,0,0.0,5,0,1,0.0,0.0,0
623,14,0,0.0,3,0,1,0.0,0.0,0
624,28,1,23.99,73,3,9,23.99,0.1111,0
625,28,1,14.99,66,3,8,14.99,0.125,0
626,5,0,0.0,44,0,8,0.0,0.0,0
627,1,0,0.0,13,0,3,0.0,0.0,0
628,1,0,0.0,2,0,1,0.0,0.0,0
629,2,1,46.99,103,4,14,46.99,0.0714,1
630,3,0,0.0,6,0,1,0.0,0.0,0
631,26,1,8.49,114,4,15,8.49,0.0667,0
632,3,0,0.0,10,0,1,0.0,0.0,0
633,5,0,0.0,1,0,1,0.0,0.0,0
634,8,1,59.99,97,4,14,59.99,0.0714,0
635,2,0,0.0,93,2,10,0.0,0.0,0
636,20,1,477.97,64,4,9,477.97,0.1111,0
637,3,4,330.99,74,5,12,82.75,0.3333,1
638,4,2,44.48,155,6,23,22.24,0.087,1
639,0,0,0.0,2,0,1,0.0,0.0,0
640,0,0,0.0,13,0,3,0.0,0.0,0
641,17,0,0.0,6,0,1,0.0,0.0,0
642,1,0,0.0,11,2,4,0.0,0.0,0
643,2,0,0.0,14,1,6,0.0,0.0,0
644,5,0,0.0,71,0,10,0.0,0.0,0
645,2,0,0.0,16,1,4,0.0,0.0,0
646,27,0,0.0,7,1,2,0.0,0.0,0
647,8,0,0.0,4,0,1,0.0,0.0,0
648,0,0,0.0,10,0,4,0.0,0.0,0
649,2,0,0.0,5,0,1,0.0,0.0,0
650,3,0,0.0,21,0,7,0.0,0.0,0
651,1,0,0.0,58,1,8,0.0,0.0,0
652,5,0,0.0,2,0,1,0.0,0.0,0
653,10,0,0.0,4,0,1,0.0,0.0,0
654,3,0,0.0,1,0,1,0.0,0.0,0
655,20,0,0.0,3,0,1,0.0,0.0,0
656,15,1,7.49,67,3,10,7.49,0.1,0
657,24,0,0.0,3,0,1,0.0,0.0,0
658,5,2,414.97,138,6,26,207.48,0.0769,1
659,6,0,0.0,7,0,2,0.0,0.0,0
660,11,0,0.0,16,0,2,0.0,0.0,0
661,4,0,0.0,19,2,5,0.0,0.0,0
662,1,0,0.0,29,2,5,0.0,0.0,0
663,3,0,0.0,7,0,3,0.0,0.0,0
664,22,1,265.99,68,3,9,265.99,0.1111,0
665,1,0,0.0,14,0,3,0.0,0.0,0
666,2,0,0.0,13,0,4,0.0,0.0,0
667,6,0,0.0,28,0,6,0.0,0.0,0
668,5,0,0.0,78,5,8,0.0,0.0,0
669,27,0,0.0,3,1,2,0.0,0.0,0
670,0,0,0.0,19,0,4,0.0,0.0,0
671,7,0,0.0,15,0,2,0.0,0.0,0
672,2,0,0.0,38,0,5,0.0,0.0,0
673,0,0,0.0,4,0,1,0.0,0.0,0
674,24,0,0.0,5,0,1,0.0,0.0,0
675,1,0,0.0,8,0,4,0.0,0.0,0
676,2,0,0.0,5,0,2,0.0,0.0,0
677,23,0,0.0,16,0,4,0.0,0.0,0
678,22,0,0.0,6,0,3,0.0,0.0,0
679,3,0,0.0,50,0,9,0.0,0.0,0
680,3,0,0.0,19,1,6,0.0,0.0,0
681,11,0,0.0,10,0,2,0.0,0.0,0
682,27,1,116.55,90,3,9,116.55,0.1111,0
683,13,0,0.0,5,0,1,0.0,0.0,0
684,5,0,0.0,17,0,4,0.0,0.0,0
685,13,0,0.0,14,1,1,0.0,0.0,0
686,2,0,0.0,9,0,2,0.0,0.0,0
687,13,0,0.0,3,0,1,0.0,0.0,0
688,15,1,24.99,65,2,8,24.99,0.125,0
689,18,0,0.0,4,1,1,0.0,0.0,0
690,5,0,0.0,7,0,2,0.0,0.0,0
691,27,0,0.0,3,0,1,0.0,0.0,0
692,29,1,16.98,102,5,23,16.98,0.0435,0
693,5,0,0.0,1,0,1,0.0,0.0,0
694,9,0,0.0,2,0,1,0.0,0.0,0
695,21,0,0.0,9,1,2,0.0,0.0,0
696,5,0,0.0,10,0,2,0.0,0.0,0
697,25,2,108.06,196,4,27,54.03,0.0741,0
698,5,0,0.0,1,0,1,0.0,0.0,0
699,7,4,161.88,142,10,23,40.47,0.1739,0
700,2,0,0.0,50,0,8,0.0,0.0,0
701,5,0,0.0,19,0,5,0.0,0.0,0
702,26,1,9.49,84,5,13,9.49,0.0769,0
703,26,0,0.0,2,0,1,0.0,0.0,0
704,7,0,0.0,15,2,6,0.0,0.0,0
705,9,0,0.0,7,1,1,0.0,0.0,0
706,3,2,109.98,121,6,26,54.99,0.0769,1
707,8,0,0.0,1,0,1,0.0,0.0,0
708,0,0,0.0,3,0,1,0.0,0.0,0
709,3,0,0.0,52,2,4,0.0,0.0,0
710,0,0,0.0,31,2,7,0.0,0.0,0
711,11,0,0.0,4,0,2,0.0,0.0,0
712,0,0,0.0,17,0,4,0.0,0.0,0
713,23,1,204.99,5,1,1,204.99,1.0,0
714,3,0,0.0,46,0,7,0.0,0.0,0
715,1,0,0.0,4,0,1,0.0,0.0,0
716,28,1,23.99,71,4,9,23.99,0.1111,0
717,26,0,0.0,14,1,1,0.0,0.0,0
718,0,0,0.0,41,5,5,0.0,0.0,0
719,7,1,204.99,14,1,2,204.99,0.5,0
720,6,0,0.0,6,0,1,0.0,0.0,0
721,3,0,0.0,11,0,3,0.0,0.0,0
722,1,0,0.0,21,0,5,0.0,0.0,0
723,0,0,0.0,29,2,5,0.0,0.0,0
724,1,1,198.48,124,5,24,198.48,0.0417,1
725,0,0,0.0,42,1,7,0.0,0.0,0
726,8,0,0.0,17,1,3,0.0,0.0,0
727,1,0,0.0,16,1,6,0.0,0.0,0
728,7,1,10.99,11,1,3,10.99,0.3333,0
729,3,0,0.0,22,1,3,0.0,0.0,0
730,17,1,179.98,78,6,9,179.98,0.1111,0
731,17,0,0.0,45,1,5,0.0,0.0,0
732,20,2,471.05,94,6,12,235.52,0.1667,0
733,0,0,0.0,20,0,2,0.0,0.0,0
734,4,0,0.0,18,0,4,0.0,0.0,0
735,19,0,0.0,12,0,3,0.0,0.0,0
736,0,0,0.0,34,0,6,0.0,0.0,0
737,11,0,0.0,11,0,1,0.0,0.0,0
738,0,0,0.0,7,0,1,0.0,0.0,0
739,22,1,34.99,97,3,19,34.99,0.0526,0
740,0,0,0.0,99,1,11,0.0,0.0,0
741,6,0,0.0,3,0,2,0.0,0.0,0
742,3,0,0.0,7,0,1,0.0,0.0,0
743,25,0,0.0,34,4,3,0.0,0.0,0
744,14,0,0.0,24,1,4,0.0,0.0,0
745,21,2,51.98,39,3,12,25.99,0.1667,0
746,4,0,0.0,18,0,3,0.0,0.0,0
747,17,1,30.99,95,3,15,30.99,0.0667,0
748,22,1,59.99,22,1,1,59.99,1.0,0
749,4,0,0.0,1,0,1,0.0,0.0,0
750,3,0,0.0,45,0,8,0.0,0.0,0
751,20,0,0.0,15,0,3,0.0,0.0,0
752,0,0,0.0,5,1,1,0.0,0.0,0
753,0,0,0.0,1,0,1,0.0,0.0,0
754,0,0,0.0,22,1,6,0.0,0.0,0
755,29,1,61.99,81,4,13,61.99,0.0769,0
756,0,0,0.0,6,0,1,0.0,0.0,0
757,6,0,0.0,1,0,1,0.0,0.0,0
758,16,4,1040.34,180,10,37,260.08,0.1081,0
759,4,0,0.0,16,0,3,0.0,0.0,0
760,27,1,9.15,9,1,1,9.15,1.0,0
761,3,0,0.0,16,0,4,0.0,0.0,0
762,6,3,904.95,147,9,34,301.65,0.0882,1
763,2,0,0.0,2,0,1,0.0,0.0,0
764,10,2,99.95,154,8,15,49.98,0.1333,0
765,4,0,0.0,1,0,1,0.0,0.0,0
766,2,1,36.99,45,1,6,36.99,0.1667,1
767,10,1,109.99,38,3,5,109.99,0.2,0
768,3,0,0.0,66,0,11,0.0,0.0,0
769,25,0,0.0,3,0,1,0.0,0.0,0
770,15,1,46.99,57,2,12,46.99,0.0833,0
771,1,0,0.0,14,0,1,0.0,0.0,0
772,29,1,389.98,73,3,10,389.98,0.1,0
773,0,2,369.95,65,6,10,184.98,0.2,1
774,9,0,0.0,10,0,1,0.0,0.0,0
775,13,1,23.99,22,1,5,23.99,0.2,0
776,5,0,0.0,17,1,4,0.0,0.0,0
777,1,0,0.0,100,2,13,0.0,0.0,0
778,0,0,0.0,27,0,4,0.0,0.0,0
779,30,0,0.0,1,0,1,0.0,0.0,0
780,13,0,0.0,2,0,1,0.0,0.0,0
781,27,0,0.0,5,0,1,0.0,0.0,0
782,0,0,0.0,46,0,5,0.0,0.0,0
783,0,0,0.0,15,0,3,0.0,0.0,0
784,27,1,37.99,42,2,6,37.99,0.1667,0
785,28,0,0.0,8,0,1,0.0,0.0,0
786,1,0,0.0,8,1,2,0.0,0.0,0
787,2,1,317.98,22,1,2,317.98,0.5,1
788,18,0,0.0,5,1,2,0.0,0.0,0
789,1,0,0.0,21,0,5,0.0,0.0,0
790,9,0,0.0,2,0,2,0.0,0.0,0
791,1,0,0.0,2,0,1,0.0,0.0,0
792,5,0,0.0,42,3,5,0.0,0.0,0
793,12,2,195.96,62,3,5,97.98,0.4,0
794,0,0,0.0,33,2,11,0.0,0.0,0
795,2,1,117.99,21,1,7,117.99,0.1429,1
796,0,0,0.0,145,1,18,0.0,0.0,0
797,22,0,0.0,5,0,2,0.0,0.0,0
798,27,0,0.0,6,0,1,0.0,0.0,0
799,15,2,90.98,161,5,27,45.49,0.0741,0
800,5,0,0.0,6,0,1,0.0,0.0,0
801,1,0,0.0,14,0,6,0.0,0.0,0
802,13,0,0.0,18,0,2,0.0,0.0,0
803,0,0,0.0,10,0,4,0.0,0.0,0
804,16,0,0.0,17,0,6,0.0,0.0,0
805,0,0,0.0,34,2,5,0.0,0.0,0
806,3,3,187.47,146,6,25,62.49,0.12,1
807,4,0,0.0,25,1,8,0.0,0.0,0
808,8,0,0.0,15,2,2,0.0,0.0,0
809,0,0,0.0,40,1,6,0.0,0.0,0
810,15,0,0.0,4,0,1,0.0,0.0,0
811,0,0,0.0,54,2,6,0.0,0.0,0
812,5,0,0.0,111,0,16,0.0,0.0,0
813,0,0,0.0,7,0,3,0.0,0.0,0
814,2,0,0.0,2,0,1,0.0,0.0,0
815,15,0,0.0,1,0,1,0.0,0.0,0
816,17,2,147.97,53,4,15,73.98,0.1333,0
817,3,0,0.0,1,0,1,0.0,0.0,0
818,2,1,103.99,47,2,5,103.99,0.2,1
819,10,0,0.0,11,0,2,0.0,0.0,0
820,26,1,126.27,160,7,20,126.27,0.05,0
821,29,1,130.99,52,4,9,130.99,0.1111,0
822,13,2,361.98,46,4,10,180.99,0.2,0
823,16,1,34.99,43,1,6,34.99,0.1667,0
824,0,0,0.0,22,1,7,0.0,0.0,0
825,18,0,0.0,5,0,1,0.0,0.0,0
826,13,0,0.0,9,0,1,0.0,0.0,0
827,13,0,0.0,2,0,1,0.0,0.0,0
828,2,0,0.0,5,0,1,0.0,0.0,0
829,18,1,8.49,11,2,2,8.49,0.5,0
830,8,0,0.0,6,0,2,0.0,0.0,0
831,12,0,0.0,10,1,2,0.0,0.0,0
832,0,0,0.0,27,1,5,0.0,0.0,0
833,6,0,0.0,12,0,1,0.0,0.0,0
834,5,1,9.49,104,3,15,9.49,0.0667,1
835,0,0,0.0,190,1,23,0.0,0.0,0
836,1,0,0.0,3,0,1,0.0,0.0,0
837,1,0,0.0,5,0,1,0.0,0.0,0
838,1,0,0.0,56,0,13,0.0,0.0,0
839,1,0,0.0,5,0,1,0.0,0.0,0
840,16,0,0.0,12,0,1,0.0,0.0,0
841,0,0,0.0,38,0,7,0.0,0.0,0
842,19,0,0.0,5,0,3,0.0,0.0,0
843,6,0,0.0,3,0,1,0.0,0.0,0
844,20,0,0.0,1,0,1,0.0,0.0,0
845,1,0,0.0,31,0,11,0.0,0.0,0
846,13,0,0.0,11,0,2,0.0,0.0,0
847,10,0,0.0,60,1,6,0.0,0.0,0
848,3,0,0.0,7,0,3,0.0,0.0,0
849,5,0,0.0,8,1,1,0.0,0.0,0
850,6,0,0.0,6,0,2,0.0,0.0,0
851,0,0,0.0,1,0,1,0.0,0.0,0
852,1,0,0.0,23,0,3,0.0,0.0,0
853,0,0,0.0,90,0,13,0.0,0.0,0
854,30,0,0.0,2,0,1,0.0,0.0,0
855,28,0,0.0,2,0,1,0.0,0.0,0
856,0,0,0.0,72,1,9,0.0,0.0,0
857,1,0,0.0,100,2,14,0.0,0.0,0
858,28,0,0.0,5,0,2,0.0,0.0,0
859,5,0,0.0,29,0,5,0.0,0.0,0
860,17,0,0.0,5,0,1,0.0,0.0,0
861,6,0,0.0,5,0,1,0.0,0.0,0
862,0,0,0.0,13,2,4,0.0,0.0,0
863,1,0,0.0,13,1,5,0.0,0.0,0
864,7,0,0.0,5,0,2,0.0,0.0,0
865,6,0,0.0,39,0,9,0.0,0.0,0
866,10,0,0.0,9,0,3,0.0,0.0,0
867,4,0,0.0,7,0,3,0.0,0.0,0
868,2,0,0.0,58,1,7,0.0,0.0,0
869,5,0,0.0,10,0,3,0.0,0.0,0
870,30,1,76.99,90,3,12,76.99,0.0833,0
871,2,0,0.0,4,0,1,0.0,0.0,0
872,5,0,0.0,1,0,1,0.0,0.0,0
873,21,0,0.0,4,0,1,0.0,0.0,0
874,10,0,0.0,9,0,3,0.0,0.0,0
875,4,0,0.0,18,0,4,0.0,0.0,0
876,0,0,0.0,15,0,5,0.0,0.0,0
877,1,0,0.0,22,0,5,0.0,0.0,0
878,1,0,0.0,93,2,9,0.0,0.0,0
879,11,0,0.0,8,0,2,0.0,0.0,0
880,10,0,0.0,19,0,5,0.0,0.0,0
881,1,0,0.0,15,1,5,0.0,0.0,0
882,6,0,0.0,3,0,1,0.0,0.0,0
883,7,0,0.0,2,0,1,0.0,0.0,0
884,4,0,0.0,1,0,1,0.0,0.0,0
885,1,0,0.0,20,0,3,0.0,0.0,0
886,13,0,0.0,1,0,1,0.0,0.0,0
887,9,0,0.0,11,0,3,0.0,0.0,0
888,4,0,0.0,20,2,6,0.0,0.0,0
889,7,0,0.0,18,0,5,0.0,0.0,0
890,0,0,0.0,34,0,3,0.0,0.0,0
891,27,1,158.99,83,4,16,158.99,0.0625,0
892,4,0,0.0,15,0,4,0.0,0.0,0
893,0,2,122.98,160,6,25,61.49,0.08,1
894,6,0,0.0,3,0,1,0.0,0.0,0
895,7,1,76.99,67,4,10,76.99,0.1,0
896,2,2,220.98,99,3,19,110.49,0.1053,1
897,13,0,0.0,12,0,2,0.0,0.0,0
898,28,0,0.0,4,0,1,0.0,0.0,0
899,1,0,0.0,83,0,13,0.0,0.0,0
900,0,0,0.0,112,2,10,0.0,0.0,0
901,27,1,44.55,19,1,2,44.55,0.5,0
902,3,0,0.0,14,0,5,0.0,0.0,0
903,2,2,116.98,98,3,12,58.49,0.1667,1
904,0,0,0.0,28,1,4,0.0,0.0,0
905,1,0,0.0,49,1,3,0.0,0.0,0
906,7,0,0.0,1,0,1,0.0,0.0,0
907,2,0,0.0,13,0,1,0.0,0.0,0
908,5,1,61.99,36,2,7,61.99,0.1429,1
909,2,0,0.0,11,0,1,0.0,0.0,0
910,25,1,65.99,58,4,9,65.99,0.1111,0
911,14,1,16.47,6,1,1,16.47,1.0,0
912,2,1,8.49,121,1,16,8.49,0.0625,1
913,11,2,63.98,143,2,20,31.99,0.1,0
914,22,1,64.99,15,1,4,64.99,0.25,0
915,28,1,281.26,32,1,3,281.26,0.3333,0
916,6,0,0.0,49,1,7,0.0,0.0,0
917,1,0,0.0,28,3,3,0.0,0.0,0
918,8,0,0.0,59,0,5,0.0,0.0,0
919,14,1,181.99,34,3,3,181.99,0.3333,0
920,9,0,0.0,8,0,2,0.0,0.0,0
921,24,0,0.0,7,0,1,0.0,0.0,0
922,6,0,0.0,12,0,3,0.0,0.0,0
923,0,0,0.0,29,0,6,0.0,0.0,0
924,26,1,54.99,82,2,13,54.99,0.0769,0
925,27,1,8.92,6,1,1,8.92,1.0,0
926,11,0,0.0,17,0,5,0.0,0.0,0
927,10,3,388.97,125,4,19,129.66,0.1579,0
928,10,0,0.0,7,0,2,0.0,0.0,0
929,27,0,0.0,4,0,1,0.0,0.0,0
930,13,0,0.0,6,1,1,0.0,0.0,0
931,0,0,0.0,8,0,1,0.0,0.0,0
932,8,0,0.0,51,4,4,0.0,0.0,0
933,9,0,0.0,31,1,4,0.0,0.0,0
934,1,0,0.0,69,1,8,0.0,0.0,0
935,18,0,0.0,39,1,5,0.0,0.0,0
936,2,0,0.0,1,0,1,0.0,0.0,0
937,0,0,0.0,55,1,4,0.0,0.0,0
938,0,1,80.98,43,2,4,80.98,0.25,1
939,5,0,0.0,3,0,1,0.0,0.0,0
940,0,0,0.0,126,1,15,0.0,0.0,0
941,9,0,0.0,18,0,4,0.0,0.0,0
942,6,0,0.0,21,0,3,0.0,0.0,0
943,1,0,0.0,19,1,5,0.0,0.0,0
944,0,0,0.0,5,0,1,0.0,0.0,0
945,23,1,103.98,28,1,5,103.98,0.2,0
946,13,0,0.0,6,0,1,0.0,0.0,0
947,19,2,170.98,52,3,5,85.49,0.4,0
948,7,0,0.0,79,0,8,0.0,0.0,0
949,10,0,0.0,35,0,7,0.0,0.0,0
950,18,0,0.0,1,0,1,0.0,0.0,0
951,7,0,0.0,5,0,1,0.0,0.0,0
952,6,0,0.0,15,1,2,0.0,0.0,0
953,21,0,0.0,10,0,1,0.0,0.0,0
954,1,0,0.0,140,3,18,0.0,0.0,0
955,20,1,17.99,79,2,10,17.99,0.1,0
956,16,2,53.87,37,4,4,26.94,0.5,0
957,5,0,0.0,5,0,1,0.0,0.0,0
958,7,0,0.0,45,0,5,0.0,0.0,0
959,5,0,0.0,5,0,1,0.0,0.0,0
960,18,1,165.99,66,4,14,165.99,0.0714,0
961,3,1,81.99,14,1,3,81.99,0.3333,1
962,6,4,1183.94,181,8,26,295.98,0.1538,1
963,7,0,0.0,10,0,3,0.0,0.0,0
964,4,0,0.0,43,0,9,0.0,0.0,0
965,16,0,0.0,2,0,1,0.0,0.0,0
966,28,0,0.0,2,0,1,0.0,0.0,0
967,28,1,65.99,37,2,12,65.99,0.0833,0
968,6,0,0.0,3,0,1,0.0,0.0,0
969,3,0,0.0,64,0,12,0.0,0.0,0
970,25,1,201.98,95,4,12,201.98,0.0833,0
971,7,0,0.0,4,1,1,0.0,0.0,0
972,27,1,763.99,43,3,7,763.99,0.1429,0
973,6,0,0.0,19,0,5,0.0,0.0,0
974,17,1,59.97,153,4,19,59.97,0.0526,0
975,8,0,0.0,29,0,6,0.0,0.0,0
976,4,0,0.0,18,0,2,0.0,0.0,0
977,2,0,0.0,14,0,2,0.0,0.0,0
978,0,0,0.0,101,5,11,0.0,0.0,0
979,6,1,478.99,33,2,6,478.99,0.1667,1
980,0,0,0.0,34,1,5,0.0,0.0,0
981,27,0,0.0,6,0,1,0.0,0.0,0
982,5,0,0.0,18,1,4,0.0,0.0,0
983,3,0,0.0,19,0,5,0.0,0.0,0
984,8,0,0.0,6,0,1,0.0,0.0,0
985,3,0,0.0,11,1,1,0.0,0.0,0
986,5,0,0.0,13,0,1,0.0,0.0,0
987,16,0,0.0,38,1,3,0.0,0.0,0
988,7,0,0.0,8,0,2,0.0,0.0,0
989,5,0,0.0,1,0,1,0.0,0.0,0
990,12,0,0.0,4,0,1,0.0,0.0,0
991,2,0,0.0,11,0,2,0.0,0.0,0
992,15,0,0.0,3,0,1,0.0,0.0,0
993,4,0,0.0,4,0,1,0.0,0.0,0
994,15,0,0.0,2,0,1,0.0,0.0,0
995,18,0,0.0,6,0,1,0.0,0.0,0
996,8,0,0.0,26,1,5,0.0,0.0,0
997,1,0,0.0,15,0,5,0.0,0.0,0
998,14,0,0.0,5,0,1,0.0,0.0,0
999,10,0,0.0,3,0,2,0.0,0.0,0
1000,19,1,86.48,14,2,3,86.48,0.3333,0
1001,11,0,0.0,5,0,1,0.0,0.0,0
1002,6,3,802.95,192,7,37,267.65,0.0811,1
1003,4,0,0.0,29,1,4,0.0,0.0,0
1004,0,0,0.0,11,0,2,0.0,0.0,0
1005,1,0,0.0,87,1,8,0.0,0.0,0
1006,18,0,0.0,1,0,1,0.0,0.0,0
1007,10,1,48.99,8,2,2,48.99,0.5,0
1008,16,1,37.99,39,1,7,37.99,0.1429,0
1009,4,3,318.96,171,11,21,106.32,0.1429,1
1010,12,0,0.0,4,0,2,0.0,0.0,0
1011,5,0,0.0,46,0,8,0.0,0.0,0
1012,3,0,0.0,94,3,10,0.0,0.0,0
1013,6,0,0.0,4,0,1,0.0,0.0,0
1014,14,0,0.0,23,0,4,0.0,0.0,0
1015,1,0,0.0,121,3,14,0.0,0.0,0
1016,10,0,0.0,12,0,1,0.0,0.0,0
1017,16,0,0.0,4,1,2,0.0,0.0,0
1018,12,5,361.4,218,13,25,72.28,0.2,0
1019,13,0,0.0,7,1,2,0.0,0.0,0
1020,23,1,89.99,32,1,4,89.99,0.25,0
1021,3,0,0.0,3,0,1,0.0,0.0,0
1022,18,1,16.98,82,1,15,16.98,0.0667,0
1023,9,0,0.0,7,0,3,0.0,0.0,0
1024,29,0,0.0,6,0,1,0.0,0.0,0
1025,27,0,0.0,1,0,1,0.0,0.0,0
1026,2,0,0.0,16,0,4,0.0,0.0,0
1027,9,0,0.0,10,0,1,0.0,0.0,0
1028,6,0,0.0,31,0,5,0.0,0.0,0
1029,1,0,0.0,34,2,8,0.0,0.0,0
1030,2,3,261.47,98,4,16,87.16,0.1875,1
1031,20,0,0.0,7,0,1,0.0,0.0,0
1032,11,0,0.0,1,0,1,0.0,0.0,0
1033,25,2,63.8,59,7,7,31.9,0.2857,0
1034,9,0,0.0,12,0,2,0.0,0.0,0
1035,3,0,0.0,6,1,1,0.0,0.0,0
1036,5,0,0.0,12,0,3,0.0,0.0,0
1037,4,0,0.0,10,0,4,0.0,0.0,0
1038,1,0,0.0,64,0,10,0.0,0.0,0
1039,12,0,0.0,29,1,4,0.0,0.0,0
1040,14,0,0.0,7,0,1,0.0,0.0,0
1041,14,0,0.0,4,0,1,0.0,0.0,0
1042,5,0,0.0,11,1,4,0.0,0.0,0
1043,3,0,0.0,40,2,6,0.0,0.0,0
1044,29,1,78.95,100,5,14,78.95,0.0714,0
1045,26,0,0.0,5,0,2,0.0,0.0,0
1046,17,0,0.0,6,0,2,0.0,0.0,0
1047,0,0,0.0,8,0,2,0.0,0.0,0
1048,21,0,0.0,12,1,5,0.0,0.0,0
1049,9,0,0.0,22,1,4,0.0,0.0,0
1050,3,0,0.0,49,0,6,0.0,0.0,0
1051,2,0,0.0,20,0,3,0.0,0.0,0
1052,12,0,0.0,27,4,5,0.0,0.0,0
1053,13,0,0.0,9,0,1,0.0,0.0,0
1054,7,0,0.0,5,0,1,0.0,0.0,0
1055,0,0,0.0,5,0,3,0.0,0.0,0
1056,5,0,0.0,6,0,2,0.0,0.0,0
1057,5,0,0.0,44,1,6,0.0,0.0,0
1058,25,0,0.0,6,0,1,0.0,0.0,0
1059,23,0,0.0,4,0,2,0.0,0.0,0
1060,19,0,0.0,8,0,1,0.0,0.0,0
1061,1,1,162.99,64,1,11,162.99,0.0909,1
1062,4,0,0.0,18,0,3,0.0,0.0,0
1063,1,3,176.8,64,4,12,58.93,0.25,1
1064,28,0,0.0,3,1,1,0.0,0.0,0
1065,7,0,0.0,4,0,1,0.0,0.0,0
1066,21,1,100.99,228,3,21,100.99,0.0476,0
1067,4,4,1342.9,225,13,30,335.72,0.1333,1
1068,28,0,0.0,2,0,1,0.0,0.0,0
1069,6,0,0.0,32,0,8,0.0,0.0,0
1070,0,0,0.0,20,1,4,0.0,0.0,0
1071,6,0,0.0,34,1,5,0.0,0.0,0
1072,8,0,0.0,4,0,1,0.0,0.0,0
1073,8,0,0.0,24,1,4,0.0,0.0,0
1074,2,0,0.0,4,0,1,0.0,0.0,0
1075,1,0,0.0,116,1,18,0.0,0.0,0
1076,1,0,0.0,56,0,6,0.0,0.0,0
1077,14,1,32.99,3,1,1,32.99,1.0,0
1078,7,0,0.0,3,1,1,0.0,0.0,0
1079,2,0,0.0,3,0,2,0.0,0.0,0
1080,0,0,0.0,113,2,16,0.0,0.0,0
1081,5,0,0.0,10,0,2,0.0,0.0,0
1082,11,1,22.98,48,2,7,22.98,0.1429,0
1083,4,0,0.0,6,0,1,0.0,0.0,0
1084,5,0,0.0,10,0,1,0.0,0.0,0
1085,4,0,0.0,1,0,1,0.0,0.0,0
1086,6,0,0.0,17,0,4,0.0,0.0,0
1087,1,0,0.0,3,0,2,0.0,0.0,0
1088,7,0,0.0,2,0,1,0.0,0.0,0
1089,0,0,0.0,12,0,6,0.0,0.0,0
1090,0,0,0.0,16,1,4,0.0,0.0,0
1091,1,0,0.0,74,2,11,0.0,0.0,0
1092,19,0,0.0,23,1,3,0.0,0.0,0
1093,0,0,0.0,20,1,3,0.0,0.0,0
1094,4,0,0.0,3,0,1,0.0,0.0,0
1095,2,0,0.0,4,1,2,0.0,0.0,0
1096,9,0,0.0,8,0,1,0.0,0.0,0
1097,13,1,32.99,37,4,9,32.99,0.1111,0
1098,7,0,0.0,6,0,2,0.0,0.0,0
1099,0,0,0.0,35,1,10,0.0,0.0,0
1100,16,0,0.0,1,0,1,0.0,0.0,0
1101,10,0,0.0,12,0,2,0.0,0.0,0
1102,0,0,0.0,2,0,1,0.0,0.0,0
1103,6,0,0.0,19,1,4,0.0,0.0,0
1104,23,0,0.0,15,2,2,0.0,0.0,0
1105,1,0,0.0,22,0,6,0.0,0.0,0
1106,2,0,0.0,16,0,4,0.0,0.0,0
1107,7,0,0.0,9,0,1,0.0,0.0,0
1108,3,0,0.0,31,2,2,0.0,0.0,0
1109,1,0,0.0,43,1,5,0.0,0.0,0
1110,6,0,0.0,11,0,2,0.0,0.0,0
1111,18,0,0.0,4,0,1,0.0,0.0,0
1112,28,1,61.99,62,3,7,61.99,0.1429,0
1113,21,0,0.0,16,0,4,0.0,0.0,0
1114,9,0,0.0,1,0,1,0.0,0.0,0
1115,0,0,0.0,20,0,3,0.0,0.0,0
1116,3,0,0.0,13,0,1,0.0,0.0,0
1117,12,1,7.49,42,2,8,7.49,0.125,0
1118,6,0,0.0,21,0,4,0.0,0.0,0
1119,0,0,0.0,3,0,1,0.0,0.0,0
1120,0,0,0.0,29,1,4,0.0,0.0,0
1121,19,2,97.98,59,2,9,48.99,0.2222,0
1122,8,0,0.0,5,0,1,0.0,0.0,0
1123,2,0,0.0,2,0,1,0.0,0.0,0
1124,1,0,0.0,2,0,1,0.0,0.0,0
1125,28,1,664.98,49,2,7,664.98,0.1429,0
1126,12,0,0.0,7,1,2,0.0,0.0,0
1127,18,1,76.99,87,1,9,76.99,0.1111,0
1128,7,0,0.0,1,0,1,0.0,0.0,0
1129,0,0,0.0,20,2,5,0.0,0.0,0
1130,4,0,0.0,8,1,3,0.0,0.0,0
1131,5,0,0.0,36,0,5,0.0,0.0,0
1132,4,0,0.0,85,3,8,0.0,0.0,0
1133,1,0,0.0,7,0,2,0.0,0.0,0
1134,10,0,0.0,7,0,1,0.0,0.0,0
1135,5,0,0.0,3,0,1,0.0,0.0,0
1136,24,0,0.0,7,0,1,0.0,0.0,0
1137,7,3,391.96,96,8,20,130.65,0.15,0
1138,10,0,0.0,13,0,3,0.0,0.0,0
1139,0,0,0.0,6,0,2,0.0,0.0,0
1140,27,0,0.0,3,0,1,0.0,0.0,0
1141,25,1,34.99,37,1,8,34.99,0.125,0
1142,1,0,0.0,5,0,2,0.0,0.0,0
1143,10,1,36.99,14,1,4,36.99,0.25,0
1144,19,0,0.0,4,0,1,0.0,0.0,0
1145,1,0,0.0,19,1,5,0.0,0.0,0
1146,0,0,0.0,4,0,1,0.0,0.0,0
1147,4,0,0.0,3,0,2,0.0,0.0,0
1148,27,0,0.0,4,0,1,0.0,0.0,0
1149,1,0,0.0,22,2,5,0.0,0.0,0
1150,0,0,0.0,40,1,10,0.0,0.0,0
1151,10,0,0.0,45,0,4,0.0,0.0,0
1152,1,1,280.98,6,2,2,280.98,0.5,1
1153,11,0,0.0,9,0,3,0.0,0.0,0
1154,4,0,0.0,6,0,1,0.0,0.0,0
1155,7,0,0.0,29,1,4,0.0,0.0,0
1156,27,1,10.99,17,1,4,10.99,0.25,0
1157,3,0,0.0,35,3,6,0.0,0.0,0
1158,17,0,0.0,8,0,3,0.0,0.0,0
1159,18,0,0.0,8,0,3,0.0,0.0,0
1160,0,0,0.0,28,0,8,0.0,0.0,0
1161,1,3,457.25,152,7,19,152.42,0.1579,1
1162,20,2,183.98,133,5,17,91.99,0.1176,0
1163,0,0,0.0,40,0,7,0.0,0.0,0
1164,6,0,0.0,8,1,1,0.0,0.0,0
1165,4,2,16.47,30,3,7,8.24,0.2857,1
1166,5,0,0.0,12,0,3,0.0,0.0,0
1167,19,0,0.0,1,0,1,0.0,0.0,0
1168,25,0,0.0,1,0,1,0.0,0.0,0
1169,0,0,0.0,1,0,1,0.0,0.0,0
1170,19,0,0.0,3,0,1,0.0,0.0,0
1171,17,0,0.0,2,0,1,0.0,0.0,0
1172,5,0,0.0,34,0,5,0.0,0.0,0
1173,0,0,0.0,18,1,2,0.0,0.0,0
1174,3,0,0.0,44,1,7,0.0,0.0,0
1175,4,5,491.93,75,8,12,98.39,0.4167,1
1176,23,0,0.0,10,0,1,0.0,0.0,0
1177,2,0,0.0,43,1,7,0.0,0.0,0
1178,5,0,0.0,36,1,7,0.0,0.0,0
1179,20,1,241.99,5,1,1,241.99,1.0,0
1180,0,0,0.0,2,0,1,0.0,0.0,0
1181,16,0,0.0,6,0,1,0.0,0.0,0
1182,13,8,2454.41,226,19,35,306.8,0.2286,0
1183,15,0,0.0,4,0,1,0.0,0.0,0
1184,10,2,34.48,66,4,9,17.24,0.2222,0
1185,12,1,84.99,40,2,6,84.99,0.1667,0
1186,11,0,0.0,5,0,1,0.0,0.0,0
1187,0,0,0.0,176,8,26,0.0,0.0,0
1188,7,0,0.0,34,1,3,0.0,0.0,0
1189,10,0,0.0,11,0,3,0.0,0.0,0
1190,0,2,224.46,95,2,14,112.23,0.1429,1
1191,19,0,0.0,8,0,1,0.0,0.0,0
1192,0,0,0.0,17,0,4,0.0,0.0,0
1193,2,0,0.0,7,0,1,0.0,0.0,0
1194,6,0,0.0,22,0,4,0.0,0.0,0
1195,1,0,0.0,33,1,6,0.0,0.0,0
1196,5,0,0.0,2,0,1,0.0,0.0,0
1197,5,0,0.0,5,0,1,0.0,0.0,0
1198,4,0,0.0,20,0,4,0.0,0.0,0
1199,14,0,0.0,5,0,1,0.0,0.0,0
1200,1,0,0.0,8,0,1,0.0,0.0,0
1201,4,0,0.0,4,0,1,0.0,0.0,0
1202,25,0,0.0,4,0,1,0.0,0.0,0
1203,9,0,0.0,16,0,4,0.0,0.0,0
1204,2,0,0.0,18,0,3,0.0,0.0,0
1205,5,0,0.0,5,0,3,0.0,0.0,0
1206,0,0,0.0,122,2,12,0.0,0.0,0
1207,1,0,0.0,2,0,1,0.0,0.0,0
1208,1,0,0.0,3,0,1,0.0,0.0,0
1209,4,0,0.0,4,0,1,0.0,0.0,0
1210,23,0,0.0,4,0,1,0.0,0.0,0
1211,9,0,0.0,2,0,1,0.0,0.0,0
1212,14,0,0.0,57,2,6,0.0,0.0,0
1213,0,2,277.96,32,3,7,138.98,0.2857,1
1214,1,0,0.0,56,3,10,0.0,0.0,0
1215,4,0,0.0,11,0,2,0.0,0.0,0
1216,7,0,0.0,2,0,1,0.0,0.0,0
1217,26,0,0.0,3,0,1,0.0,0.0,0
1218,3,0,0.0,35,0,9,0.0,0.0,0
1219,5,2,89.98,41,3,5,44.99,0.4,1
1220,5,0,0.0,12,1,3,0.0,0.0,0
1221,27,0,0.0,2,0,1,0.0,0.0,0
1222,11,0,0.0,18,0,3,0.0,0.0,0
1223,0,0,0.0,42,3,11,0.0,0.0,0
1224,6,0,0.0,10,0,2,0.0,0.0,0
1225,22,1,48.97,35,2,7,48.97,0.1429,0
1226,8,0,0.0,17,1,1,0.0,0.0,0
1227,29,0,0.0,4,0,1,0.0,0.0,0
1228,1,0,0.0,29,0,3,0.0,0.0,0
1229,4,2,75.98,51,3,6,37.99,0.3333,1
1230,4,0,0.0,46,0,8,0.0,0.0,0
1231,12,0,0.0,2,0,1,0.0,0.0,0
1232,18,0,0.0,12,0,2,0.0,0.0,0
1233,6,0,0.0,21,0,1,0.0,0.0,0
1234,0,0,0.0,21,0,6,0.0,0.0,0
1235,29,1,84.74,84,3,11,84.74,0.0909,0
1236,3,0,0.0,8,0,2,0.0,0.0,0
1237,29,0,0.0,4,0,1,0.0,0.0,0
1238,23,0,0.0,1,0,1,0.0,0.0,0
1239,27,0,0.0,37,0,2,0.0,0.0,0
1240,0,0,0.0,15,0,2,0.0,0.0,0
1241,5,1,29.99,6,1,1,29.99,1.0,1
1242,0,0,0.0,14,1,6,0.0,0.0,0
1243,6,0,0.0,17,1,4,0.0,0.0,0
1244,1,0,0.0,18,1,5,0.0,0.0,0
1245,26,1,25.99,75,1,6,25.99,0.1667,0
1246,0,0,0.0,17,0,3,0.0,0.0,0
1247,3,0,0.0,30,0,4,0.0,0.0,0
1248,5,0,0.0,51,0,8,0.0,0.0,0
1249,9,0,0.0,3,0,1,0.0,0.0,0
1250,6,1,28.99,16,1,4,28.99,0.25,1
1251,0,0,0.0,156,3,18,0.0,0.0,0
1252,28,0,0.0,1,0,1,0.0,0.0,0
1253,24,0,0.0,3,0,1,0.0,0.0,0
1254,4,0,0.0,9,0,1,0.0,0.0,0
1255,7,0,0.0,6,0,1,0.0,0.0,0
1256,6,0,0.0,5,0,1,0.0,0.0,0
1257,4,0,0.0,5,0,1,0.0,0.0,0
1258,14,0,0.0,45,4,4,0.0,0.0,0
1259,14,0,0.0,5,1,1,0.0,0.0,0
1260,3,0,0.0,5,0,1,0.0,0.0,0
1261,5,0,0.0,7,1,1,0.0,0.0,0
1262,3,0,0.0,94,3,14,0.0,0.0,0
1263,15,2,116.98,141,4,21,58.49,0.0952,0
1264,3,0,0.0,10,0,2,0.0,0.0,0
1265,10,1,204.99,27,1,5,204.99,0.2,0
1266,19,1,81.98,4,2,1,81.98,1.0,0
1267,15,3,59.97,144,7,29,19.99,0.1034,0
1268,20,1,14.99,62,2,8,14.99,0.125,0
1269,9,1,31.99,63,2,8,31.99,0.125,0
1270,27,0,0.0,1,0,1,0.0,0.0,0
1271,8,2,120.48,26,4,5,60.24,0.4,0
1272,4,0,0.0,67,0,8,0.0,0.0,0
1273,6,0,0.0,39,0,4,0.0,0.0,0
1274,3,0,0.0,91,2,12,0.0,0.0,0
1275,5,1,49.98,20,2,4,49.98,0.25,1
1276,0,0,0.0,22,0,1,0.0,0.0,0
1277,3,0,0.0,61,1,7,0.0,0.0,0
1278,2,0,0.0,8,0,2,0.0,0.0,0
1279,25,1,27.98,79,2,17,27.98,0.0588,0
1280,5,0,0.0,5,0,1,0.0,0.0,0
1281,15,1,17.99,59,3,10,17.99,0.1,0
1282,6,0,0.0,14,1,6,0.0,0.0,0
1283,0,0,0.0,82,1,10,0.0,0.0,0
1284,5,0,0.0,2,0,2,0.0,0.0,0
1285,1,0,0.0,51,0,7,0.0,0.0,0
1286,2,0,0.0,16,1,2,0.0,0.0,0
1287,5,0,0.0,30,1,6,0.0,0.0,0
1288,3,0,0.0,5,0,1,0.0,0.0,0
1289,0,0,0.0,5,0,2,0.0,0.0,0
1290,1,0,0.0,36,0,7,0.0,0.0,0
1291,27,1,561.99,66,2,8,561.99,0.125,0
1292,0,0,0.0,120,1,18,0.0,0.0,0
1293,6,0,0.0,13,2,1,0.0,0.0,0
1294,3,0,0.0,18,0,3,0.0,0.0,0
1295,20,0,0.0,1,0,1,0.0,0.0,0
1296,30,0,0.0,1,0,1,0.0,0.0,0
1297,5,0,0.0,5,0,1,0.0,0.0,0
1298,2,0,0.0,14,1,4,0.0,0.0,0
1299,4,0,0.0,1,0,1,0.0,0.0,0
1300,10,0,0.0,5,0,1,0.0,0.0,0
1301,25,2,55.91,36,2,6,27.96,0.3333,0
1302,7,0,0.0,1,0,1,0.0,0.0,0
1303,4,0,0.0,4,0,1,0.0,0.0,0
1304,6,0,0.0,21,1,4,0.0,0.0,0
1305,2,0,0.0,21,0,2,0.0,0.0,0
1306,27,1,176.99,107,5,18,176.99,0.0556,0
1307,9,0,0.0,3,0,1,0.0,0.0,0
1308,5,0,0.0,66,2,10,0.0,0.0,0
1309,7,1,123.47,41,3,11,123.47,0.0909,0
1310,13,0,0.0,31,0,4,0.0,0.0,0
1311,3,0,0.0,4,0,1,0.0,0.0,0
1312,13,0,0.0,3,0,1,0.0,0.0,0
1313,4,0,0.0,16,0,3,0.0,0.0,0
1314,19,1,8.49,62,2,8,8.49,0.125,0
1315,7,0,0.0,12,0,2,0.0,0.0,0
1316,1,0,0.0,26,1,5,0.0,0.0,0
1317,4,0,0.0,18,1,4,0.0,0.0,0
1318,0,0,0.0,163,3,14,0.0,0.0,0
1319,1,0,0.0,12,0,4,0.0,0.0,0
1320,9,0,0.0,12,0,2,0.0,0.0,0
1321,6,0,0.0,43,4,7,0.0,0.0,0
1322,17,0,0.0,18,1,4,0.0,0.0,0
1323,9,0,0.0,11,1,3,0.0,0.0,0
1324,1,0,0.0,2,0,1,0.0,0.0,0
1325,1,1,15.99,19,1,2,15.99,0.5,1
1326,18,1,23.99,48,1,6,23.99,0.1667,0
1327,17,0,0.0,14,0,3,0.0,0.0,0
1328,1,0,0.0,10,0,3,0.0,0.0,0
1329,23,0,0.0,6,0,2,0.0,0.0,0
1330,0,5,1360.44,185,14,31,272.09,0.1613,1
1331,1,0,0.0,29,0,5,0.0,0.0,0
1332,26,1,39.98,120,4,14,39.98,0.0714,0
1333,2,0,0.0,35,2,7,0.0,0.0,0
1334,23,1,36.99,101,2,15,36.99,0.0667,0
1335,3,0,0.0,23,1,7,0.0,0.0,0
1336,14,0,0.0,10,1,2,0.0,0.0,0
1337,28,0,0.0,2,0,1,0.0,0.0,0
1338,6,0,0.0,1,0,1,0.0,0.0,0
1339,7,0,0.0,10,0,3,0.0,0.0,0
1340,1,0,0.0,29,0,4,0.0,0.0,0
1341,11,4,94.45,227,8,23,23.61,0.1739,0
1342,6,1,18.98,20,2,3,18.98,0.3333,1
1343,3,0,0.0,13,0,5,0.0,0.0,0
1344,4,0,0.0,32,1,4,0.0,0.0,0
1345,2,0,0.0,12,0,3,0.0,0.0,0
1346,29,1,298.98,116,3,18,298.98,0.0556,0
1347,13,0,0.0,54,2,7,0.0,0.0,0
1348,7,0,0.0,3,0,1,0.0,0.0,0
1349,8,0,0.0,8,0,2,0.0,0.0,0
1350,5,0,0.0,11,0,3,0.0,0.0,0
1351,21,0,0.0,5,0,1,0.0,0.0,0
1352,11,0,0.0,14,0,3,0.0,0.0,0
1353,12,0,0.0,10,0,1,0.0,0.0,0
1354,10,0,0.0,34,2,4,0.0,0.0,0
1355,4,0,0.0,78,3,11,0.0,0.0,0
1356,12,1,32.99,5,1,1,32.99,1.0,0
1357,12,0,0.0,7,0,2,0.0,0.0,0
1358,20,0,0.0,3,0,1,0.0,0.0,0
1359,4,0,0.0,19,0,3,0.0,0.0,0
1360,1,0,0.0,17,0,4,0.0,0.0,0
1361,6,0,0.0,4,0,1,0.0,0.0,0
1362,6,0,0.0,2,0,1,0.0,0.0,0
1363,0,0,0.0,64,4,8,0.0,0.0,0
1364,5,0,0.0,5,0,2,0.0,0.0,0
1365,6,0,0.0,27,0,2,0.0,0.0,0
1366,3,0,0.0,32,0,5,0.0,0.0,0
1367,3,0,0.0,2,0,1,0.0,0.0,0
1368,12,0,0.0,2,0,1,0.0,0.0,0
1369,12,0,0.0,9,0,1,0.0,0.0,0
1370,14,0,0.0,15,0,3,0.0,0.0,0
1371,1,0,0.0,89,2,12,0.0,0.0,0
1372,0,0,0.0,94,2,14,0.0,0.0,0
1373,0,0,0.0,12,1,2,0.0,0.0,0
1374,18,0,0.0,6,1,1,0.0,0.0,0
1375,14,0,0.0,25,1,5,0.0,0.0,0
1376,1,0,0.0,1,0,1,0.0,0.0,0
1377,0,0,0.0,3,0,2,0.0,0.0,0
1378,1,1,15.99,51,2,5,15.99,0.2,1
1379,9,2,225.96,91,5,13,112.98,0.1538,0
1380,10,2,479.98,76,5,13,239.99,0.1538,0
1381,6,0,0.0,9,0,1,0.0,0.0,0
1382,1,0,0.0,9,0,1,0.0,0.0,0
1383,4,0,0.0,10,2,3,0.0,0.0,0
1384,0,1,13.99,46,2,6,13.99,0.1667,1
1385,2,0,0.0,50,0,9,0.0,0.0,0
1386,8,2,116.98,99,4,13,58.49,0.1538,0
1387,22,1,76.99,69,7,10,76.99,0.1,0
1388,26,1,17.99,26,1,4,17.99,0.25,0
1389,24,1,24.99,92,2,11,24.99,0.0909,0
1390,12,1,13.99,43,2,7,13.99,0.1429,0
1391,2,1,53.99,66,2,11,53.99,0.0909,1
1392,14,0,0.0,9,1,3,0.0,0.0,0
1393,8,0,0.0,20,0,3,0.0,0.0,0
1394,3,0,0.0,31,0,4,0.0,0.0,0
1395,13,0,0.0,19,0,5,0.0,0.0,0
1396,0,0,0.0,12,0,6,0.0,0.0,0
1397,13,0,0.0,2,0,1,0.0,0.0,0
1398,1,0,0.0,78,4,8,0.0,0.0,0
1399,11,0,0.0,23,0,5,0.0,0.0,0
1400,10,0,0.0,13,0,3,0.0,0.0,0
1401,6,0,0.0,23,1,4,0.0,0.0,0
1402,18,1,26.99,115,7,21,26.99,0.0476,0
1403,2,0,0.0,13,0,3,0.0,0.0,0
1404,11,0,0.0,63,3,7,0.0,0.0,0
1405,26,0,0.0,5,0,1,0.0,0.0,0
1406,25,0,0.0,6,0,1,0.0,0.0,0
1407,9,0,0.0,8,0,2,0.0,0.0,0
1408,3,0,0.0,35,1,4,0.0,0.0,0
1409,17,0,0.0,3,0,1,0.0,0.0,0
1410,2,0,0.0,72,1,8,0.0,0.0,0
1411,13,0,0.0,5,0,1,0.0,0.0,0
1412,2,0,0.0,24,2,6,0.0,0.0,0
1413,19,0,0.0,2,0,1,0.0,0.0,0
1414,25,0,0.0,4,2,1,0.0,0.0,0
1415,28,1,17.99,11,2,5,17.99,0.2,0
1416,3,0,0.0,79,1,11,0.0,0.0,0
1417,20,0,0.0,21,1,3,0.0,0.0,0
1418,4,0,0.0,7,0,1,0.0,0.0,0
1419,0,3,1139.95,94,6,9,379.98,0.3333,1
1420,1,0,0.0,148,0,19,0.0,0.0,0
1421,14,0,0.0,6,0,2,0.0,0.0,0
1422,18,2,52.9,61,3,13,26.45,0.1538,0
1423,0,0,0.0,18,1,3,0.0,0.0,0
1424,6,0,0.0,5,0,1,0.0,0.0,0
1425,4,0,0.0,64,2,6,0.0,0.0,0
1426,12,0,0.0,7,0,4,0.0,0.0,0
1427,0,0,0.0,75,5,9,0.0,0.0,0
1428,0,0,0.0,13,2,3,0.0,0.0,0
1429,5,1,8.49,60,1,9,8.49,0.1111,1
1430,25,1,93.98,30,2,5,93.98,0.2,0
1431,12,0,0.0,4,0,2,0.0,0.0,0
1432,2,1,149.99,41,2,8,149.99,0.125,1
1433,1,0,0.0,38,1,5,0.0,0.0,0
1434,8,0,0.0,7,1,1,0.0,0.0,0
1435,1,0,0.0,11,0,2,0.0,0.0,0
1436,16,0,0.0,22,0,1,0.0,0.0,0
1437,4,0,0.0,20,0,4,0.0,0.0,0
1438,6,0,0.0,14,0,4,0.0,0.0,0
1439,5,0,0.0,31,0,2,0.0,0.0,0
1440,2,0,0.0,7,0,4,0.0,0.0,0
1441,27,0,0.0,2,0,1,0.0,0.0,0
1442,3,0,0.0,6,0,2,0.0,0.0,0
1443,29,1,144.99,48,2,10,144.99,0.1,0
1444,17,0,0.0,11,0,2,0.0,0.0,0
1445,2,0,0.0,4,0,1,0.0,0.0,0
1446,18,0,0.0,2,0,1,0.0,0.0,0
1447,13,0,0.0,9,0,3,0.0,0.0,0
1448,17,0,0.0,7,0,1,0.0,0.0,0
1449,1,0,0.0,40,2,7,0.0,0.0,0
1450,7,0,0.0,25,1,4,0.0,0.0,0
1451,9,0,0.0,14,0,2,0.0,0.0,0
1452,3,0,0.0,7,0,1,0.0,0.0,0
1453,16,0,0.0,5,0,1,0.0,0.0,0
1454,29,0,0.0,7,0,1,0.0,0.0,0
1455,1,0,0.0,5,1,1,0.0,0.0,0
1456,1,0,0.0,5,0,1,0.0,0.0,0
1457,13,1,6.98,69,1,9,6.98,0.1111,0
1458,2,0,0.0,4,1,1,0.0,0.0,0
1459,0,0,0.0,69,2,8,0.0,0.0,0
1460,14,0,0.0,2,0,1,0.0,0.0,0
1461,24,0,0.0,4,0,1,0.0,0.0,0
1462,14,2,129.98,70,4,11,64.99,0.1818,0
1463,27,2,266.98,41,4,9,133.49,0.2222,0
1464,19,0,0.0,12,0,2,0.0,0.0,0
1465,2,5,289.45,289,14,36,57.89,0.1389,1
1466,8,0,0.0,2,0,1,0.0,0.0,0
1467,11,0,0.0,6,0,2,0.0,0.0,0
1468,20,1,9.49,7,1,3,9.49,0.3333,0
1469,6,0,0.0,68,3,8,0.0,0.0,0
1470,11,1,14.99,71,3,12,14.99,0.0833,0
1471,4,0,0.0,3,0,1,0.0,0.0,0
1472,11,0,0.0,7,0,1,0.0,0.0,0
1473,10,0,0.0,48,1,8,0.0,0.0,0
1474,14,0,0.0,27,1,7,0.0,0.0,0
1475,1,0,0.0,5,0,1,0.0,0.0,0
1476,22,0,0.0,12,1,1,0.0,0.0,0
1477,27,1,59.99,29,1,3,59.99,0.3333,0
1478,1,0,0.0,136,0,14,0.0,0.0,0
1479,28,0,0.0,2,0,1,0.0,0.0,0
1480,5,0,0.0,14,0,5,0.0,0.0,0
1481,0,0,0.0,39,0,12,0.0,0.0,0
1482,0,0,0.0,5,0,1,0.0,0.0,0
1483,11,0,0.0,10,1,2,0.0,0.0,0
1484,21,2,46.94,78,3,12,23.47,0.1667,0
1485,11,0,0.0,26,0,4,0.0,0.0,0
1486,6,0,0.0,2,0,1,0.0,0.0,0
1487,0,0,0.0,6,0,2,0.0,0.0,0
1488,3,0,0.0,10,0,4,0.0,0.0,0
1489,19,0,0.0,4,1,1,0.0,0.0,0
1490,0,2,84.98,37,4,11,42.49,0.1818,1
1491,26,0,0.0,2,0,1,0.0,0.0,0
1492,4,0,0.0,4,1,1,0.0,0.0,0
1493,16,0,0.0,13,0,1,0.0,0.0,0
1494,1,0,0.0,104,1,16,0.0,0.0,0
1495,0,0,0.0,3,0,1,0.0,0.0,0
1496,2,0,0.0,34,1,4,0.0,0.0,0
1497,4,0,0.0,2,0,1,0.0,0.0,0
1498,2,0,0.0,4,0,1,0.0,0.0,0
1499,4,0,0.0,7,0,2,0.0,0.0,0
1500,2,0,0.0,63,0,8,0.0,0.0,0
1501,5,0,0.0,14,0,2,0.0,0.0,0
1502,2,0,0.0,58,0,11,0.0,0.0,0
1503,2,3,119.46,179,9,21,39.82,0.1429,1
1504,15,0,0.0,3,0,1,0.0,0.0,0
1505,8,0,0.0,18,1,5,0.0,0.0,0
1506,27,1,77.0,44,3,3,77.0,0.3333,0
1507,30,0,0.0,6,0,1,0.0,0.0,0
1508,3,0,0.0,26,1,5,0.0,0.0,0
1509,0,0,0.0,55,0,6,0.0,0.0,0
1510,2,0,0.0,61,0,9,0.0,0.0,0
1511,4,0,0.0,11,1,3,0.0,0.0,0
1512,20,0,0.0,5,0,1,0.0,0.0,0
1513,2,0,0.0,9,0,2,0.0,0.0,0
1514,2,0,0.0,11,1,3,0.0,0.0,0
1515,0,0,0.0,37,0,5,0.0,0.0,0
1516,14,0,0.0,5,0,1,0.0,0.0,0
1517,2,0,0.0,32,1,4,0.0,0.0,0
1518,7,0,0.0,1,1,1,0.0,0.0,0
1519,10,0,0.0,2,0,1,0.0,0.0,0
1520,1,0,0.0,23,0,2,0.0,0.0,0
1521,26,0,0.0,1,0,1,0.0,0.0,0
1522,5,0,0.0,70,2,8,0.0,0.0,0
1523,2,0,0.0,75,0,12,0.0,0.0,0
1524,3,0,0.0,6,0,1,0.0,0.0,0
1525,25,0,0.0,5,0,1,0.0,0.0,0
1526,29,0,0.0,2,0,1,0.0,0.0,0
1527,15,0,0.0,4,0,1,0.0,0.0,0
1528,23,0,0.0,7,0,1,0.0,0.0,0
1529,6,0,0.0,12,0,3,0.0,0.0,0
1530,12,0,0.0,59,3,8,0.0,0.0,0
1531,22,0,0.0,13,0,2,0.0,0.0,0
1532,5,0,0.0,15,1,3,0.0,0.0,0
1533,15,1,32.99,178,1,20,32.99,0.05,0
1534,3,0,0.0,34,1,12,0.0,0.0,0
1535,8,0,0.0,76,1,7,0.0,0.0,0
1536,4,0,0.0,34,0,4,0.0,0.0,0
1537,9,0,0.0,3,0,1,0.0,0.0,0
1538,0,0,0.0,75,2,13,0.0,0.0,0
1539,7,0,0.0,30,0,4,0.0,0.0,0
1540,11,0,0.0,5,0,1,0.0,0.0,0
1541,5,0,0.0,6,0,1,0.0,0.0,0
1542,10,0,0.0,63,1,4,0.0,0.0,0
1543,12,1,23.99,19,1,1,23.99,1.0,0
1544,18,1,30.99,18,1,3,30.99,0.3333,0
1545,5,0,0.0,45,3,5,0.0,0.0,0
1546,0,0,0.0,6,0,1,0.0,0.0,0
1547,26,0,0.0,6,0,1,0.0,0.0,0
1548,3,0,0.0,60,0,9,0.0,0.0,0
1549,0,0,0.0,23,1,3,0.0,0.0,0
1550,0,0,0.0,23,1,3,0.0,0.0,0
1551,9,0,0.0,14,0,4,0.0,0.0,0
1552,15,0,0.0,2,0,1,0.0,0.0,0
1553,6,0,0.0,6,0,1,0.0,0.0,0
1554,13,2,92.43,154,5,18,46.22,0.1111,0
1555,3,0,0.0,13,0,2,0.0,0.0,0
1556,3,0,0.0,94,1,9,0.0,0.0,0
1557,0,0,0.0,30,1,8,0.0,0.0,0
1558,7,1,7.49,49,1,6,7.49,0.1667,0
1559,2,0,0.0,15,0,3,0.0,0.0,0
1560,3,0,0.0,3,0,1,0.0,0.0,0
1561,12,0,0.0,4,1,2,0.0,0.0,0
1562,20,0,0.0,6,0,1,0.0,0.0,0
1563,13,0,0.0,3,0,1,0.0,0.0,0
1564,5,0,0.0,15,0,3,0.0,0.0,0
1565,29,0,0.0,7,0,1,0.0,0.0,0
1566,8,0,0.0,3,0,2,0.0,0.0,0
1567,3,0,0.0,11,0,3,0.0,0.0,0
1568,28,0,0.0,5,0,1,0.0,0.0,0
1569,0,0,0.0,49,0,7,0.0,0.0,0
1570,5,0,0.0,19,0,5,0.0,0.0,0
1571,0,0,0.0,20,0,5,0.0,0.0,0
1572,1,0,0.0,7,0,1,0.0,0.0,0
1573,25,0,0.0,3,0,1,0.0,0.0,0
1574,3,0,0.0,83,5,14,0.0,0.0,0
1575,11,0,0.0,4,0,1,0.0,0.0,0
1576,25,1,10.99,84,2,11,10.99,0.0909,0
1577,27,0,0.0,2,0,1,0.0,0.0,0
1578,0,0,0.0,11,1,2,0.0,0.0,0
1579,2,0,0.0,92,4,14,0.0,0.0,0
1580,11,0,0.0,2,0,1,0.0,0.0,0
1581,29,0,0.0,2,0,1,0.0,0.0,0
1582,4,0,0.0,1,0,1,0.0,0.0,0
1583,28,0,0.0,12,0,2,0.0,0.0,0
1584,2,0,0.0,11,0,5,0.0,0.0,0
1585,4,0,0.0,97,4,12,0.0,0.0,0
1586,6,2,189.98,41,2,5,94.99,0.4,1
1587,4,0,0.0,32,1,5,0.0,0.0,0
1588,11,0,0.0,31,1,7,0.0,0.0,0
1589,5,0,0.0,15,0,6,0.0,0.0,0
1590,5,0,0.0,6,0,1,0.0,0.0,0
1591,3,0,0.0,17,0,5,0.0,0.0,0
1592,1,0,0.0,8,0,2,0.0,0.0,0
1593,12,2,44.98,67,4,8,22.49,0.25,0
1594,19,0,0.0,12,1,1,0.0,0.0,0
1595,6,4,192.62,93,6,12,48.16,0.3333,1
1596,8,0,0.0,2,0,1,0.0,0.0,0
1597,25,0,0.0,9,0,1,0.0,0.0,0
1598,3,0,0.0,26,0,4,0.0,0.0,0
1599,19,0,0.0,2,1,1,0.0,0.0,0
1600,3,0,0.0,8,0,2,0.0,0.0,0
1601,19,0,0.0,7,0,1,0.0,0.0,0
1602,6,0,0.0,3,0,1,0.0,0.0,0
1603,6,0,0.0,7,0,3,0.0,0.0,0
1604,6,0,0.0,7,0,2,0.0,0.0,0
1605,25,0,0.0,4,1,1,0.0,0.0,0
1606,2,0,0.0,9,1,3,0.0,0.0,0
1607,24,0,0.0,1,0,1,0.0,0.0,0
1608,11,0,0.0,1,0,1,0.0,0.0,0
1609,11,0,0.0,18,1,2,0.0,0.0,0
1610,3,0,0.0,3,0,1,0.0,0.0,0
1611,8,1,31.99,29,2,6,31.99,0.1667,0
1612,8,0,0.0,25,0,4,0.0,0.0,0
1613,12,0,0.0,1,0,1,0.0,0.0,0
1614,9,0,0.0,11,0,4,0.0,0.0,0
1615,15,0,0.0,8,1,1,0.0,0.0,0
1616,13,0,0.0,11,0,1,0.0,0.0,0
1617,2,0,0.0,27,1,7,0.0,0.0,0
1618,24,0,0.0,2,0,1,0.0,0.0,0
1619,4,0,0.0,4,0,1,0.0,0.0,0
1620,3,0,0.0,13,1,5,0.0,0.0,0
1621,13,0,0.0,16,0,1,0.0,0.0,0
1622,4,0,0.0,17,0,5,0.0,0.0,0
1623,0,0,0.0,6,0,1,0.0,0.0,0
1624,28,0,0.0,5,0,1,0.0,0.0,0
1625,10,0,0.0,10,0,2,0.0,0.0,0
1626,28,1,23.32,91,1,11,23.32,0.0909,0
1627,9,0,0.0,12,0,2,0.0,0.0,0
1628,12,0,0.0,11,0,3,0.0,0.0,0
1629,10,1,11.99,96,1,11,11.99,0.0909,0
1630,6,0,0.0,46,1,10,0.0,0.0,0
1631,2,0,0.0,3,0,1,0.0,0.0,0
1632,2,0,0.0,1,0,1,0.0,0.0,0
1633,6,0,0.0,1,0,1,0.0,0.0,0
1634,1,0,0.0,11,0,1,0.0,0.0,0
1635,5,0,0.0,12,0,3,0.0,0.0,0
1636,1,0,0.0,48,0,9,0.0,0.0,0
1637,6,0,0.0,4,0,1,0.0,0.0,0
1638,1,0,0.0,40,2,12,0.0,0.0,0
1639,17,0,0.0,3,0,1,0.0,0.0,0
1640,3,0,0.0,24,0,5,0.0,0.0,0
1641,27,0,0.0,6,0,1,0.0,0.0,0
1642,25,0,0.0,3,0,1,0.0,0.0,0
1643,4,0,0.0,7,1,1,0.0,0.0,0
1644,0,0,0.0,4,0,2,0.0,0.0,0
1645,7,0,0.0,17,0,3,0.0,0.0,0
1646,2,0,0.0,5,0,2,0.0,0.0,0
1647,21,1,26.99,3,1,1,26.99,1.0,0
1648,4,0,0.0,2,0,1,0.0,0.0,0
1649,10,0,0.0,3,0,1,0.0,0.0,0
1650,10,0,0.0,11,0,4,0.0,0.0,0
1651,25,0,0.0,1,0,1,0.0,0.0,0
1652,24,1,43.99,35,1,9,43.99,0.1111,0
1653,1,0,0.0,7,0,3,0.0,0.0,0
1654,0,0,0.0,21,0,3,0.0,0.0,0
1655,28,0,0.0,5,0,1,0.0,0.0,0
1656,9,0,0.0,29,2,2,0.0,0.0,0
1657,4,0,0.0,30,2,7,0.0,0.0,0
1658,5,0,0.0,53,0,12,0.0,0.0,0
1659,9,0,0.0,10,0,4,0.0,0.0,0
1660,3,3,116.46,109,10,19,38.82,0.1579,1
1661,29,0,0.0,8,0,1,0.0,0.0,0
1662,5,1,274.97,7,3,1,274.97,1.0,1
1663,0,0,0.0,3,0,1,0.0,0.0,0
1664,20,0,0.0,1,0,1,0.0,0.0,0
1665,3,0,0.0,94,3,10,0.0,0.0,0
1666,14,0,0.0,21,0,3,0.0,0.0,0
1667,6,0,0.0,1,0,1,0.0,0.0,0
1668,29,0,0.0,6,0,1,0.0,0.0,0
1669,26,0,0.0,3,0,1,0.0,0.0,0
1670,2,1,507.98,139,7,23,507.98,0.0435,1
1671,2,3,744.94,193,7,36,248.31,0.0833,1
1672,0,0,0.0,28,0,5,0.0,0.0,0
1673,3,0,0.0,43,2,8,0.0,0.0,0
1674,0,0,0.0,23,0,5,0.0,0.0,0
1675,19,1,372.99,56,2,8,372.99,0.125,0
1676,1,0,0.0,3,0,1,0.0,0.0,0
1677,30,1,117.99,52,1,8,117.99,0.125,0
1678,0,0,0.0,16,1,4,0.0,0.0,0
1679,27,0,0.0,3,0,1,0.0,0.0,0
1680,17,2,41.98,76,4,10,20.99,0.2,0
1681,18,0,0.0,33,1,6,0.0,0.0,0
1682,25,0,0.0,8,0,1,0.0,0.0,0
1683,2,0,0.0,33,0,6,0.0,0.0,0
1684,0,0,0.0,5,0,2,0.0,0.0,0
1685,0,0,0.0,177,2,18,0.0,0.0,0
1686,2,0,0.0,1,0,1,0.0,0.0,0
1687,0,0,0.0,22,0,6,0.0,0.0,0
1688,0,0,0.0,77,2,8,0.0,0.0,0
1689,1,0,0.0,64,2,7,0.0,0.0,0
1690,10,0,0.0,3,0,3,0.0,0.0,0
1691,0,0,0.0,70,1,8,0.0,0.0,0
1692,0,0,0.0,52,0,9,0.0,0.0,0
1693,3,0,0.0,2,0,1,0.0,0.0,0
1694,16,0,0.0,4,0,2,0.0,0.0,0
1695,14,0,0.0,7,0,1,0.0,0.0,0
1696,3,0,0.0,26,0,8,0.0,0.0,0
1697,0,0,0.0,31,1,7,0.0,0.0,0
1698,11,0,0.0,12,0,2,0.0,0.0,0
1699,1,0,0.0,41,0,7,0.0,0.0,0
1700,3,0,0.0,5,0,2,0.0,0.0,0
1701,16,0,0.0,5,0,1,0.0,0.0,0
1702,0,0,0.0,14,0,2,0.0,0.0,0
1703,29,1,14.99,21,2,5,14.99,0.2,0
1704,7,1,8.98,54,3,9,8.98,0.1111,0
1705,17,0,0.0,19,1,6,0.0,0.0,0
1706,4,0,0.0,63,0,8,0.0,0.0,0
1707,2,0,0.0,33,2,7,0.0,0.0,0
1708,29,1,34.99,20,1,1,34.99,1.0,0
1709,29,1,7.76,74,4,10,7.76,0.1,0
1710,3,0,0.0,4,0,1,0.0,0.0,0
1711,5,0,0.0,14,0,4,0.0,0.0,0
1712,4,3,48.97,115,7,26,16.32,0.1154,1
1713,10,0,0.0,21,0,6,0.0,0.0,0
1714,0,0,0.0,6,0,2,0.0,0.0,0
1715,17,1,5.49,24,1,3,5.49,0.3333,0
1716,12,0,0.0,4,0,3,0.0,0.0,0
1717,3,0,0.0,72,0,8,0.0,0.0,0
1718,5,3,476.97,86,4,13,158.99,0.2308,1
1719,20,0,0.0,6,0,1,0.0,0.0,0
1720,25,0,0.0,1,0,1,0.0,0.0,0
1721,0,0,0.0,9,0,1,0.0,0.0,0
1722,2,0,0.0,13,0,2,0.0,0.0,0
1723,26,0,0.0,5,0,1,0.0,0.0,0
1724,13,0,0.0,7,0,2,0.0,0.0,0
1725,4,0,0.0,32,0,4,0.0,0.0,0
1726,10,0,0.0,16,0,2,0.0,0.0,0
1727,2,0,0.0,15,0,5,0.0,0.0,0
1728,9,0,0.0,14,0,3,0.0,0.0,0
1729,0,0,0.0,28,0,7,0.0,0.0,0
1730,5,0,0.0,55,0,7,0.0,0.0,0
1731,3,0,0.0,11,0,3,0.0,0.0,0
1732,5,0,0.0,53,2,12,0.0,0.0,0
1733,26,0,0.0,1,0,1,0.0,0.0,0
1734,15,0,0.0,35,0,5,0.0,0.0,0
1735,6,0,0.0,6,0,2,0.0,0.0,0
1736,4,0,0.0,5,1,1,0.0,0.0,0
1737,11,0,0.0,8,0,4,0.0,0.0,0
1738,1,1,167.99,100,5,17,167.99,0.0588,1
1739,0,0,0.0,44,0,5,0.0,0.0,0
1740,12,0,0.0,17,0,2,0.0,0.0,0
1741,5,0,0.0,13,0,4,0.0,0.0,0
1742,10,1,14.99,58,2,10,14.99,0.1,0
1743,1,0,0.0,102,1,7,0.0,0.0,0
1744,8,0,0.0,12,0,2,0.0,0.0,0
1745,5,0,0.0,7,0,1,0.0,0.0,0
1746,17,0,0.0,5,1,1,0.0,0.0,0
1747,7,0,0.0,5,0,1,0.0,0.0,0
1748,10,0,0.0,5,0,3,0.0,0.0,0
1749,13,0,0.0,4,0,1,0.0,0.0,0
1750,3,0,0.0,8,0,3,0.0,0.0,0
1751,0,0,0.0,44,1,6,0.0,0.0,0
1752,1,0,0.0,24,0,7,0.0,0.0,0
1753,3,1,46.99,33,1,4,46.99,0.25,1
1754,2,0,0.0,46,0,9,0.0,0.0,0
1755,28,1,561.99,55,3,6,561.99,0.1667,0
1756,0,0,0.0,22,1,5,0.0,0.0,0
1757,12,0,0.0,19,0,3,0.0,0.0,0
1758,4,0,0.0,138,1,17,0.0,0.0,0
1759,1,0,0.0,79,3,12,0.0,0.0,0
1760,5,1,23.99,69,1,8,23.99,0.125,1
1761,2,0,0.0,7,0,2,0.0,0.0,0
1762,2,0,0.0,13,0,2,0.0,0.0,0
1763,23,0,0.0,1,0,1,0.0,0.0,0
1764,18,0,0.0,2,0,1,0.0,0.0,0
1765,0,0,0.0,49,5,9,0.0,0.0,0
1766,3,1,10.98,134,3,15,10.98,0.0667,1
1767,20,0,0.0,11,0,1,0.0,0.0,0
1768,28,1,15.52,47,1,6,15.52,0.1667,0
1769,0,0,0.0,53,1,13,0.0,0.0,0
1770,16,0,0.0,47,1,5,0.0,0.0,0
1771,27,1,76.99,24,1,5,76.99,0.2,0
1772,2,0,0.0,10,0,1,0.0,0.0,0
1773,1,0,0.0,137,2,14,0.0,0.0,0
1774,3,0,0.0,22,1,4,0.0,0.0,0
1775,10,0,0.0,1,0,1,0.0,0.0,0
1776,16,0,0.0,15,0,3,0.0,0.0,0
1777,7,0,0.0,14,0,3,0.0,0.0,0
1778,6,0,0.0,4,0,2,0.0,0.0,0
1779,1,0,0.0,12,0,2,0.0,0.0,0
1780,28,1,23.99,127,1,17,23.99,0.0588,0
1781,13,0,0.0,4,0,1,0.0,0.0,0
1782,7,0,0.0,13,0,4,0.0,0.0,0
1783,1,0,0.0,9,0,2,0.0,0.0,0
1784,15,0,0.0,3,0,1,0.0,0.0,0
1785,11,0,0.0,5,0,1,0.0,0.0,0
1786,2,0,0.0,22,0,3,0.0,0.0,0
1787,1,0,0.0,25,1,9,0.0,0.0,0
1788,3,0,0.0,25,2,3,0.0,0.0,0
1789,10,0,0.0,21,0,7,0.0,0.0,0
1790,0,2,163.95,110,7,18,81.98,0.1111,1
1791,0,0,0.0,179,4,25,0.0,0.0,0
1792,1,0,0.0,29,2,3,0.0,0.0,0
1793,21,2,44.98,46,3,10,22.49,0.2,0
1794,0,0,0.0,13,0,2,0.0,0.0,0
1795,0,0,0.0,23,0,5,0.0,0.0,0
1796,10,0,0.0,79,6,6,0.0,0.0,0
1797,5,0,0.0,3,0,1,0.0,0.0,0
1798,12,2,88.77,79,5,11,44.38,0.1818,0
1799,18,0,0.0,4,0,1,0.0,0.0,0
1800,16,0,0.0,9,0,1,0.0,0.0,0
1801,1,0,0.0,15,0,2,0.0,0.0,0
1802,2,3,83.96,125,8,16,27.99,0.1875,1
1803,0,3,1019.96,217,10,41,339.99,0.0732,1
1804,6,1,30.99,8,1,2,30.99,0.5,1
1805,9,0,0.0,8,0,1,0.0,0.0,0
1806,8,0,0.0,21,1,5,0.0,0.0,0
1807,2,0,0.0,17,0,7,0.0,0.0,0
1808,26,0,0.0,1,0,1,0.0,0.0,0
1809,27,1,36.98,103,5,15,36.98,0.0667,0
1810,10,0,0.0,3,0,1,0.0,0.0,0
1811,21,1,37.99,112,2,16,37.99,0.0625,0
1812,4,0,0.0,56,1,6,0.0,0.0,0
1813,7,0,0.0,6,0,1,0.0,0.0,0
1814,3,0,0.0,66,4,9,0.0,0.0,0
1815,0,0,0.0,4,0,1,0.0,0.0,0
1816,12,0,0.0,27,0,3,0.0,0.0,0
1817,19,0,0.0,22,0,3,0.0,0.0,0
1818,17,1,13.99,125,5,23,13.99,0.0435,0
1819,16,0,0.0,13,0,1,0.0,0.0,0
1820,6,0,0.0,13,0,5,0.0,0.0,0
1821,7,0,0.0,14,0,2,0.0,0.0,0
1822,13,0,0.0,15,2,2,0.0,0.0,0
1823,1,0,0.0,51,1,6,0.0,0.0,0
1824,10,0,0.0,6,1,3,0.0,0.0,0
1825,28,0,0.0,4,0,1,0.0,0.0,0
1826,0,0,0.0,84,0,8,0.0,0.0,0
1827,3,0,0.0,25,2,7,0.0,0.0,0
1828,21,1,245.98,9,1,2,245.98,0.5,0
1829,1,0,0.0,2,0,1,0.0,0.0,0
1830,2,0,0.0,5,0,1,0.0,0.0,0
1831,26,0,0.0,2,0,1,0.0,0.0,0
1832,4,0,0.0,27,0,4,0.0,0.0,0
1833,6,1,76.99,66,1,9,76.99,0.1111,1
1834,0,0,0.0,60,4,9,0.0,0.0,0
1835,21,0,0.0,1,0,1,0.0,0.0,0
1836,2,0,0.0,96,2,13,0.0,0.0,0
1837,5,0,0.0,1,0,1,0.0,0.0,0
1838,28,1,21.36,91,5,14,21.36,0.0714,0
1839,2,0,0.0,103,0,17,0.0,0.0,0
1840,0,0,0.0,58,1,8,0.0,0.0,0
1841,7,0,0.0,18,0,3,0.0,0.0,0
1842,0,0,0.0,74,2,8,0.0,0.0,0
1843,19,0,0.0,4,0,1,0.0,0.0,0
1844,14,1,19.99,130,2,12,19.99,0.0833,0
1845,2,0,0.0,1,0,1,0.0,0.0,0
1846,10,0,0.0,23,0,7,0.0,0.0,0
1847,13,1,440.99,202,5,21,440.99,0.0476,0
1848,12,1,17.99,85,2,11,17.99,0.0909,0
1849,4,0,0.0,10,0,1,0.0,0.0,0
1850,27,0,0.0,4,0,1,0.0,0.0,0
1851,2,0,0.0,6,0,3,0.0,0.0,0
1852,25,1,23.99,20,1,2,23.99,0.5,0
1853,5,0,0.0,35,0,4,0.0,0.0,0
1854,5,0,0.0,55,1,6,0.0,0.0,0
1855,13,0,0.0,16,0,4,0.0,0.0,0
1856,15,0,0.0,2,0,1,0.0,0.0,0
1857,2,0,0.0,3,1,2,0.0,0.0,0
1858,11,0,0.0,11,0,2,0.0,0.0,0
1859,18,3,44.93,77,5,14,14.98,0.2143,0
1860,1,0,0.0,36,0,5,0.0,0.0,0
1861,2,0,0.0,36,1,7,0.0,0.0,0
1862,1,0,0.0,3,0,2,0.0,0.0,0
1863,4,0,0.0,3,0,1,0.0,0.0,0
1864,1,0,0.0,75,2,11,0.0,0.0,0
1865,1,0,0.0,99,3,17,0.0,0.0,0
1866,0,0,0.0,10,0,4,0.0,0.0,0
1867,14,0,0.0,7,0,1,0.0,0.0,0
1868,25,1,25.36,62,3,11,25.36,0.0909,0
1869,20,0,0.0,2,0,1,0.0,0.0,0
1870,3,0,0.0,16,0,4,0.0,0.0,0
1871,7,0,0.0,17,0,1,0.0,0.0,0
1872,3,0,0.0,7,0,1,0.0,0.0,0
1873,3,0,0.0,62,1,10,0.0,0.0,0
1874,10,0,0.0,10,1,2,0.0,0.0,0
1875,0,0,0.0,163,3,22,0.0,0.0,0
1876,14,1,96.99,6,1,1,96.99,1.0,0
1877,2,0,0.0,21,1,4,0.0,0.0,0
1878,10,0,0.0,2,0,1,0.0,0.0,0
1879,26,0,0.0,10,1,1,0.0,0.0,0
1880,27,1,41.99,53,3,11,41.99,0.0909,0
1881,12,0,0.0,6,1,3,0.0,0.0,0
1882,5,0,0.0,7,0,1,0.0,0.0,0
1883,4,0,0.0,16,2,4,0.0,0.0,0
1884,6,0,0.0,7,0,2,0.0,0.0,0
1885,23,0,0.0,2,0,1,0.0,0.0,0
1886,28,1,47.99,89,5,17,47.99,0.0588,0
1887,8,0,0.0,33,2,5,0.0,0.0,0
1888,0,0,0.0,16,0,2,0.0,0.0,0
1889,0,0,0.0,36,0,6,0.0,0.0,0
1890,7,0,0.0,4,0,1,0.0,0.0,0
1891,4,0,0.0,15,0,3,0.0,0.0,0
1892,5,1,413.98,59,2,12,413.98,0.0833,1
1893,0,0,0.0,28,0,5,0.0,0.0,0
1894,18,1,193.98,94,3,14,193.98,0.0714,0
1895,28,0,0.0,2,0,1,0.0,0.0,0
1896,10,0,0.0,56,1,5,0.0,0.0,0
1897,6,0,0.0,18,0,3,0.0,0.0,0
1898,0,0,0.0,10,0,1,0.0,0.0,0
1899,6,0,0.0,13,0,4,0.0,0.0,0
1900,0,2,1138.98,66,4,9,569.49,0.2222,1
1901,24,1,46.99,106,6,16,46.99,0.0625,0
1902,22,0,0.0,3,0,1,0.0,0.0,0
1903,5,0,0.0,11,0,4,0.0,0.0,0
1904,6,0,0.0,45,1,5,0.0,0.0,0
1905,3,0,0.0,3,0,1,0.0,0.0,0
1906,0,0,0.0,66,1,8,0.0,0.0,0
1907,1,0,0.0,3,0,1,0.0,0.0,0
1908,0,0,0.0,90,1,10,0.0,0.0,0
1909,2,0,0.0,7,1,1,0.0,0.0,0
1910,12,1,24.99,109,2,16,24.99,0.0625,0
1911,2,0,0.0,9,0,1,0.0,0.0,0
1912,10,0,0.0,4,0,1,0.0,0.0,0
1913,2,0,0.0,31,2,4,0.0,0.0,0
1914,5,0,0.0,19,3,5,0.0,0.0,0
1915,18,0,0.0,9,0,1,0.0,0.0,0
1916,12,0,0.0,6,0,3,0.0,0.0,0
1917,29,1,49.02,46,4,10,49.02,0.1,0
1918,4,0,0.0,15,1,4,0.0,0.0,0
1919,11,0,0.0,9,0,1,0.0,0.0,0
1920,3,0,0.0,14,1,1,0.0,0.0,0
1921,18,1,24.99,23,1,4,24.99,0.25,0
1922,9,0,0.0,9,0,2,0.0,0.0,0
1923,2,0,0.0,56,2,9,0.0,0.0,0
1924,16,0,0.0,8,0,2,0.0,0.0,0
1925,0,0,0.0,78,0,8,0.0,0.0,0
1926,12,0,0.0,2,0,1,0.0,0.0,0
1927,5,0,0.0,6,0,4,0.0,0.0,0
1928,6,0,0.0,16,1,5,0.0,0.0,0
1929,13,1,54.97,69,4,8,54.97,0.125,0
1930,0,0,0.0,4,0,1,0.0,0.0,0
1931,4,0,0.0,9,0,2,0.0,0.0,0
1932,12,0,0.0,13,0,3,0.0,0.0,0
1933,1,0,0.0,8,1,1,0.0,0.0,0
1934,1,0,0.0,9,0,3,0.0,0.0,0
1935,20,0,0.0,4,0,1,0.0,0.0,0
1936,21,1,17.99,70,1,8,17.99,0.125,0
1937,15,0,0.0,3,0,1,0.0,0.0,0
1938,27,0,0.0,2,0,1,0.0,0.0,0
1939,24,2,628.97,46,3,6,314.48,0.3333,0
1940,15,1,14.99,17,1,1,14.99,1.0,0
1941,14,1,100.99,89,3,6,100.99,0.1667,0
1942,9,0,0.0,21,0,5,0.0,0.0,0
1943,0,0,0.0,19,0,5,0.0,0.0,0
1944,15,0,0.0,9,0,3,0.0,0.0,0
1945,7,0,0.0,9,0,2,0.0,0.0,0
1946,0,0,0.0,38,1,3,0.0,0.0,0
1947,13,0,0.0,1,0,1,0.0,0.0,0
1948,0,0,0.0,16,0,3,0.0,0.0,0
1949,3,0,0.0,17,0,5,0.0,0.0,0
1950,9,0,0.0,8,0,1,0.0,0.0,0
1951,21,0,0.0,6,1,2,0.0,0.0,0
1952,0,0,0.0,10,1,1,0.0,0.0,0
1953,29,1,2.3,57,2,7,2.3,0.1429,0
1954,3,0,0.0,15,0,1,0.0,0.0,0
1955,11,0,0.0,2,0,1,0.0,0.0,0
1956,3,0,0.0,49,1,6,0.0,0.0,0
1957,26,0,0.0,2,0,1,0.0,0.0,0
1958,22,1,87.99,19,1,3,87.99,0.3333,0
1959,0,0,0.0,39,1,8,0.0,0.0,0
1960,0,0,0.0,21,0,3,0.0,0.0,0
1961,28,1,105.98,9,2,2,105.98,0.5,0
1962,4,2,345.97,223,8,26,172.98,0.0769,1
1963,3,0,0.0,5,0,1,0.0,0.0,0
1964,4,1,64.99,57,3,12,64.99,0.0833,1
1965,11,1,23.99,22,1,2,23.99,0.5,0
1966,8,0,0.0,8,0,2,0.0,0.0,0
1967,14,0,0.0,21,2,3,0.0,0.0,0
1968,24,0,0.0,1,0,1,0.0,0.0,0
1969,21,1,89.99,41,4,4,89.99,0.25,0
1970,11,0,0.0,5,0,1,0.0,0.0,0
1971,1,0,0.0,7,0,3,0.0,0.0,0
1972,9,2,294.11,87,4,18,147.06,0.1111,0
1973,8,0,0.0,1,0,1,0.0,0.0,0
1974,0,0,0.0,20,0,4,0.0,0.0,0
1975,15,0,0.0,8,0,3,0.0,0.0,0
1976,7,1,106.99,74,3,16,106.99,0.0625,0
1977,14,0,0.0,24,0,6,0.0,0.0,0
1978,27,0,0.0,1,0,1,0.0,0.0,0
1979,7,1,265.99,29,1,6,265.99,0.1667,0
1980,3,0,0.0,112,0,10,0.0,0.0,0
1981,4,0,0.0,8,0,1,0.0,0.0,0
1982,9,0,0.0,10,0,3,0.0,0.0,0
1983,1,0,0.0,79,2,17,0.0,0.0,0
1984,25,1,157.98,74,3,15,157.98,0.0667,0
1985,0,0,0.0,29,0,6,0.0,0.0,0
1986,13,0,0.0,22,1,3,0.0,0.0,0
1987,4,0,0.0,46,0,6,0.0,0.0,0
1988,0,0,0.0,79,2,19,0.0,0.0,0
1989,20,0,0.0,2,0,1,0.0,0.0,0
1990,1,0,0.0,74,2,17,0.0,0.0,0
1991,4,0,0.0,62,2,13,0.0,0.0,0
1992,2,0,0.0,4,0,1,0.0,0.0,0
1993,10,0,0.0,14,0,2,0.0,0.0,0
1994,3,0,0.0,6,0,2,0.0,0.0,0
1995,0,0,0.0,31,1,9,0.0,0.0,0
1996,1,0,0.0,16,1,4,0.0,0.0,0
1997,8,0,0.0,23,1,3,0.0,0.0,0
1998,4,0,0.0,65,5,10,0.0,0.0,0
1999,22,1,57.99,96,1,11,57.99,0.0909,0
2000,4,0,0.0,4,0,1,0.0,0.0,0
2001,2,0,0.0,1,0,1,0.0,0.0,0
2002,0,0,0.0,143,2,20,0.0,0.0,0
2003,5,0,0.0,3,0,1,0.0,0.0,0
2004,19,1,673.98,44,1,6,673.98,0.1667,0
2005,1,0,0.0,53,3,9,0.0,0.0,0
2006,17,0,0.0,9,0,1,0.0,0.0,0
2007,1,0,0.0,4,0,2,0.0,0.0,0
2008,18,0,0.0,4,0,1,0.0,0.0,0
2009,20,0,0.0,10,0,2,0.0,0.0,0
2010,16,0,0.0,6,0,1,0.0,0.0,0
2011,2,0,0.0,10,1,2,0.0,0.0,0
2012,9,0,0.0,4,0,1,0.0,0.0,0
2013,2,0,0.0,57,1,8,0.0,0.0,0
2014,0,0,0.0,45,1,8,0.0,0.0,0
2015,4,0,0.0,8,0,2,0.0,0.0,0
2016,0,0,0.0,1,0,1,0.0,0.0,0
2017,29,1,144.99,22,1,9,144.99,0.1111,0
2018,5,1,527.98,3,1,1,527.98,1.0,1
2019,7,0,0.0,10,0,2,0.0,0.0,0
2020,4,0,0.0,60,0,7,0.0,0.0,0
2021,17,0,0.0,12,0,3,0.0,0.0,0
2022,28,1,46.99,2,1,1,46.99,1.0,0
2023,7,0,0.0,4,0,1,0.0,0.0,0
2024,27,1,204.99,115,3,14,204.99,0.0714,0
2025,5,0,0.0,20,1,6,0.0,0.0,0
2026,9,0,0.0,9,0,1,0.0,0.0,0
2027,0,0,0.0,2,0,1,0.0,0.0,0
2028,2,0,0.0,24,2,4,0.0,0.0,0
2029,1,0,0.0,3,0,1,0.0,0.0,0
2030,25,0,0.0,1,0,1,0.0,0.0,0
2031,18,0,0.0,13,1,3,0.0,0.0,0
2032,8,0,0.0,20,0,5,0.0,0.0,0
2033,26,0,0.0,5,0,1,0.0,0.0,0
2034,0,0,0.0,2,0,1,0.0,0.0,0
2035,18,0,0.0,5,0,1,0.0,0.0,0
2036,1,3,317.97,97,4,14,105.99,0.2143,1
2037,13,0,0.0,9,0,2,0.0,0.0,0
2038,27,0,0.0,3,0,1,0.0,0.0,0
2039,4,0,0.0,2,0,1,0.0,0.0,0
2040,18,1,37.98,194,4,19,37.98,0.0526,0
2041,4,0,0.0,3,0,1,0.0,0.0,0
2042,11,1,89.99,10,1,4,89.99,0.25,0
2043,10,0,0.0,2,0,1,0.0,0.0,0
2044,10,2,526.98,68,3,11,263.49,0.1818,0
2045,2,0,0.0,19,0,4,0.0,0.0,0
2046,6,2,69.97,54,4,7,34.98,0.2857,1
2047,6,0,0.0,29,0,8,0.0,0.0,0
2048,11,0,0.0,4,0,1,0.0,0.0,0
2049,25,0,0.0,7,0,1,0.0,0.0,0
2050,6,2,50.98,61,5,13,25.49,0.1538,1
2051,5,0,0.0,50,2,9,0.0,0.0,0
2052,13,0,0.0,29,0,4,0.0,0.0,0
2053,4,0,0.0,3,0,1,0.0,0.0,0
2054,0,0,0.0,19,0,5,0.0,0.0,0
2055,6,0,0.0,27,0,4,0.0,0.0,0
2056,0,0,0.0,10,0,2,0.0,0.0,0
2057,4,0,0.0,29,0,9,0.0,0.0,0
2058,0,0,0.0,12,0,1,0.0,0.0,0
2059,23,1,10.99,51,1,5,10.99,0.2,0
2060,11,0,0.0,16,0,1,0.0,0.0,0
2061,1,0,0.0,4,0,1,0.0,0.0,0
2062,3,0,0.0,4,1,1,0.0,0.0,0
2063,6,0,0.0,7,0,3,0.0,0.0,0
2064,1,0,0.0,32,1,8,0.0,0.0,0
2065,26,0,0.0,3,0,1,0.0,0.0,0
2066,0,0,0.0,23,1,5,0.0,0.0,0
2067,23,1,165.99,61,3,11,165.99,0.0909,0
2068,12,0,0.0,13,1,4,0.0,0.0,0
2069,1,0,0.0,69,2,14,0.0,0.0,0
2070,11,0,0.0,15,0,1,0.0,0.0,0
2071,2,0,0.0,8,0,2,0.0,0.0,0
2072,13,0,0.0,1,0,1,0.0,0.0,0
2073,5,0,0.0,22,1,2,0.0,0.0,0
2074,2,0,0.0,56,2,6,0.0,0.0,0
2075,0,3,195.95,93,9,22,65.32,0.1364,1
2076,0,1,37.99,130,3,14,37.99,0.0714,1
2077,2,0,0.0,53,1,5,0.0,0.0,0
2078,0,0,0.0,47,0,6,0.0,0.0,0
2079,30,0,0.0,6,1,1,0.0,0.0,0
2080,17,2,55.98,70,3,10,27.99,0.2,0
2081,4,0,0.0,14,0,5,0.0,0.0,0
2082,25,1,90.99,47,3,7,90.99,0.1429,0
2083,7,2,45.98,75,4,9,22.99,0.2222,0
2084,13,0,0.0,4,0,1,0.0,0.0,0
2085,8,0,0.0,15,0,3,0.0,0.0,0
2086,7,0,0.0,7,1,2,0.0,0.0,0
2087,0,0,0.0,25,0,7,0.0,0.0,0
2088,4,0,0.0,63,1,7,0.0,0.0,0
2089,10,0,0.0,12,0,3,0.0,0.0,0
2090,14,1,89.97,7,2,1,89.97,1.0,0
2091,0,0,0.0,10,0,1,0.0,0.0,0
2092,3,0,0.0,12,0,3,0.0,0.0,0
2093,0,0,0.0,17,0,1,0.0,0.0,0
2094,0,0,0.0,69,1,8,0.0,0.0,0
2095,15,3,295.45,98,5,14,98.48,0.2143,0
2096,10,0,0.0,1,0,1,0.0,0.0,0
2097,0,0,0.0,82,1,14,0.0,0.0,0
2098,2,0,0.0,27,0,5,0.0,0.0,0
2099,13,0,0.0,6,1,1,0.0,0.0,0
2100,8,2,205.46,42,5,8,102.73,0.25,0
2101,10,0,0.0,18,0,2,0.0,0.0,0
2102,0,0,0.0,84,1,12,0.0,0.0,0
2103,4,0,0.0,21,2,5,0.0,0.0,0
2104,26,1,126.98,145,7,25,126.98,0.04,0
2105,19,1,15.99,11,1,3,15.99,0.3333,0
2106,5,0,0.0,25,0,3,0.0,0.0,0
2107,5,1,522.98,75,6,9,522.98,0.1111,1
2108,7,0,0.0,4,0,1,0.0,0.0,0
2109,19,1,5.49,11,2,2,5.49,0.5,0
2110,24,2,230.98,36,3,10,115.49,0.2,0
2111,4,2,142.98,84,6,13,71.49,0.1538,1
2112,8,0,0.0,9,1,1,0.0,0.0,0
2113,1,0,0.0,34,0,6,0.0,0.0,0
2114,4,0,0.0,117,2,12,0.0,0.0,0
2115,4,0,0.0,15,0,6,0.0,0.0,0
2116,6,0,0.0,5,0,1,0.0,0.0,0
2117,11,0,0.0,8,0,2,0.0,0.0,0
2118,9,1,190.99,94,2,21,190.99,0.0476,0
2119,2,0,0.0,39,1,7,0.0,0.0,0
2120,11,0,0.0,4,0,2,0.0,0.0,0
2121,19,0,0.0,6,0,2,0.0,0.0,0
2122,0,0,0.0,25,0,5,0.0,0.0,0
2123,1,0,0.0,18,2,5,0.0,0.0,0
2124,0,0,0.0,2,0,1,0.0,0.0,0
2125,16,0,0.0,6,0,1,0.0,0.0,0
2126,27,0,0.0,4,0,1,0.0,0.0,0
2127,7,0,0.0,8,1,1,0.0,0.0,0
2128,0,0,0.0,156,5,34,0.0,0.0,0
2129,10,0,0.0,4,0,1,0.0,0.0,0
2130,2,0,0.0,36,2,5,0.0,0.0,0
2131,14,0,0.0,28,0,2,0.0,0.0,0
2132,13,4,811.41,118,7,17,202.85,0.2353,0
2133,20,0,0.0,24,0,3,0.0,0.0,0
2134,10,0,0.0,14,0,3,0.0,0.0,0
2135,14,1,288.98,78,2,11,288.98,0.0909,0
2136,2,0,0.0,41,0,5,0.0,0.0,0
2137,5,0,0.0,5,0,2,0.0,0.0,0
2138,8,0,0.0,4,0,1,0.0,0.0,0
2139,1,0,0.0,76,1,9,0.0,0.0,0
2140,2,0,0.0,110,1,8,0.0,0.0,0
2141,7,0,0.0,10,0,1,0.0,0.0,0
2142,9,0,0.0,7,0,3,0.0,0.0,0
2143,9,0,0.0,14,0,3,0.0,0.0,0
2144,4,0,0.0,19,0,3,0.0,0.0,0
2145,6,0,0.0,7,0,2,0.0,0.0,0
2146,4,3,400.97,52,3,11,133.66,0.2727,1
2147,2,0,0.0,2,0,1,0.0,0.0,0
2148,5,0,0.0,5,0,2,0.0,0.0,0
2149,17,1,7.49,47,5,4,7.49,0.25,0
2150,0,0,0.0,93,1,17,0.0,0.0,0
2151,15,0,0.0,2,0,1,0.0,0.0,0
2152,5,0,0.0,3,0,1,0.0,0.0,0
2153,10,0,0.0,11,0,3,0.0,0.0,0
2154,3,0,0.0,82,1,9,0.0,0.0,0
2155,0,0,0.0,39,1,4,0.0,0.0,0
2156,2,0,0.0,5,0,1,0.0,0.0,0
2157,7,1,30.99,10,1,1,30.99,1.0,0
2158,21,0,0.0,17,1,1,0.0,0.0,0
2159,2,0,0.0,4,0,1,0.0,0.0,0
2160,24,0,0.0,1,0,1,0.0,0.0,0
2161,12,0,0.0,4,0,1,0.0,0.0,0
2162,0,0,0.0,36,0,8,0.0,0.0,0
2163,25,0,0.0,9,0,1,0.0,0.0,0
2164,0,0,0.0,13,1,4,0.0,0.0,0
2165,5,0,0.0,9,0,3,0.0,0.0,0
2166,0,0,0.0,3,0,1,0.0,0.0,0
2167,0,0,0.0,1,0,1,0.0,0.0,0
2168,19,0,0.0,6,0,1,0.0,0.0,0
2169,0,0,0.0,200,2,26,0.0,0.0,0
2170,2,0,0.0,75,3,8,0.0,0.0,0
2171,10,1,181.99,5,1,1,181.99,1.0,0
2172,0,0,0.0,36,2,7,0.0,0.0,0
2173,2,0,0.0,9,0,3,0.0,0.0,0
2174,4,0,0.0,10,0,1,0.0,0.0,0
2175,14,1,68.98,17,3,3,68.98,0.3333,0
2176,3,0,0.0,69,1,9,0.0,0.0,0
2177,0,0,0.0,54,0,10,0.0,0.0,0
2178,1,0,0.0,2,0,1,0.0,0.0,0
2179,12,0,0.0,10,1,2,0.0,0.0,0
2180,21,0,0.0,4,0,1,0.0,0.0,0
2181,0,0,0.0,11,0,1,0.0,0.0,0
2182,7,0,0.0,39,2,5,0.0,0.0,0
2183,0,0,0.0,78,0,12,0.0,0.0,0
2184,14,0,0.0,15,0,4,0.0,0.0,0
2185,14,0,0.0,36,2,6,0.0,0.0,0
2186,22,0,0.0,2,0,1,0.0,0.0,0
2187,2,0,0.0,4,0,1,0.0,0.0,0
2188,9,0,0.0,52,0,4,0.0,0.0,0
2189,21,0,0.0,5,0,1,0.0,0.0,0
2190,0,0,0.0,79,2,7,0.0,0.0,0
2191,5,0,0.0,5,0,1,0.0,0.0,0
2192,0,0,0.0,25,0,6,0.0,0.0,0
2193,23,0,0.0,8,0,1,0.0,0.0,0
2194,0,0,0.0,12,0,4,0.0,0.0,0
2195,10,0,0.0,2,0,1,0.0,0.0,0
2196,21,0,0.0,20,1,3,0.0,0.0,0
2197,3,0,0.0,4,0,1,0.0,0.0,0
2198,27,1,89.99,28,2,6,89.99,0.1667,0
2199,26,0,0.0,3,0,1,0.0,0.0,0
2200,2,0,0.0,24,2,5,0.0,0.0,0
2201,0,0,0.0,32,0,4,0.0,0.0,0
2202,0,0,0.0,25,1,5,0.0,0.0,0
2203,1,0,0.0,12,1,5,0.0,0.0,0
2204,4,0,0.0,10,1,3,0.0,0.0,0
2205,25,1,305.64,50,3,7,305.64,0.1429,0
2206,20,0,0.0,4,0,1,0.0,0.0,0
2207,1,0,0.0,2,0,1,0.0,0.0,0
2208,8,0,0.0,41,1,7,0.0,0.0,0
2209,7,0,0.0,63,2,10,0.0,0.0,0
2210,7,0,0.0,25,0,6,0.0,0.0,0
2211,1,0,0.0,23,0,5,0.0,0.0,0
2212,20,0,0.0,7,0,1,0.0,0.0,0
2213,12,1,171.98,75,3,10,171.98,0.1,0
2214,7,1,8.49,15,1,1,8.49,1.0,0
2215,5,0,0.0,14,0,2,0.0,0.0,0
2216,4,5,486.42,128,9,25,97.28,0.2,1
2217,7,0,0.0,33,0,5,0.0,0.0,0
2218,16,0,0.0,26,0,4,0.0,0.0,0
2219,3,0,0.0,17,1,1,0.0,0.0,0
2220,8,0,0.0,20,0,4,0.0,0.0,0
2221,16,0,0.0,2,0,1,0.0,0.0,0
2222,3,0,0.0,8,0,2,0.0,0.0,0
2223,4,0,0.0,49,2,9,0.0,0.0,0
2224,6,2,70.48,47,2,9,35.24,0.2222,1
2225,10,0,0.0,5,0,1,0.0,0.0,0
2226,26,0,0.0,13,0,1,0.0,0.0,0
2227,4,0,0.0,16,1,3,0.0,0.0,0
2228,16,0,0.0,4,0,1,0.0,0.0,0
2229,28,0,0.0,7,0,1,0.0,0.0,0
2230,10,0,0.0,20,0,3,0.0,0.0,0
2231,20,0,0.0,5,0,2,0.0,0.0,0
2232,17,1,19.99,75,2,10,19.99,0.1,0
2233,5,0,0.0,6,0,2,0.0,0.0,0
2234,26,0,0.0,9,1,1,0.0,0.0,0
2235,1,0,0.0,132,2,16,0.0,0.0,0
2236,5,0,0.0,3,0,1,0.0,0.0,0
2237,1,0,0.0,43,2,13,0.0,0.0,0
2238,6,0,0.0,11,0,4,0.0,0.0,0
2239,0,0,0.0,20,0,6,0.0,0.0,0
2240,2,0,0.0,35,0,4,0.0,0.0,0
2241,4,0,0.0,20,0,3,0.0,0.0,0
2242,3,0,0.0,3,0,1,0.0,0.0,0
2243,6,0,0.0,36,0,5,0.0,0.0,0
2244,30,0,0.0,6,1,1,0.0,0.0,0
2245,0,0,0.0,4,0,2,0.0,0.0,0
2246,19,0,0.0,12,1,2,0.0,0.0,0
2247,5,0,0.0,13,0,4,0.0,0.0,0
2248,17,0,0.0,16,1,2,0.0,0.0,0
2249,22,0,0.0,7,0,1,0.0,0.0,0
2250,7,0,0.0,37,2,7,0.0,0.0,0
2251,1,0,0.0,152,5,20,0.0,0.0,0
2252,17,0,0.0,16,0,3,0.0,0.0,0
2253,27,0,0.0,3,0,1,0.0,0.0,0
2254,5,2,168.98,64,3,13,84.49,0.1538,1
2255,28,1,76.99,31,2,9,76.99,0.1111,0
2256,6,0,0.0,3,0,1,0.0,0.0,0
2257,11,0,0.0,5,0,1,0.0,0.0,0
2258,17,0,0.0,9,0,2,0.0,0.0,0
2259,8,0,0.0,2,0,1,0.0,0.0,0
2260,29,1,13.99,82,4,10,13.99,0.1,0
2261,14,0,0.0,2,0,1,0.0,0.0,0
2262,1,0,0.0,21,1,5,0.0,0.0,0
2263,5,0,0.0,40,0,5,0.0,0.0,0
2264,12,0,0.0,4,0,1,0.0,0.0,0
2265,20,2,147.46,58,5,13,73.73,0.1538,0
2266,16,1,116.99,18,1,4,116.99,0.25,0
2267,4,0,0.0,7,0,1,0.0,0.0,0
2268,3,0,0.0,3,0,1,0.0,0.0,0
2269,1,0,0.0,20,3,3,0.0,0.0,0
2270,17,0,0.0,5,0,1,0.0,0.0,0
2271,2,0,0.0,14,0,3,0.0,0.0,0
2272,6,0,0.0,20,1,6,0.0,0.0,0
2273,13,0,0.0,4,0,1,0.0,0.0,0
2274,3,0,0.0,22,0,6,0.0,0.0,0
2275,3,0,0.0,1,0,1,0.0,0.0,0
2276,1,0,0.0,7,0,1,0.0,0.0,0
2277,0,0,0.0,75,3,8,0.0,0.0,0
2278,16,0,0.0,1,0,1,0.0,0.0,0
2279,0,0,0.0,28,0,9,0.0,0.0,0
2280,15,0,0.0,26,0,3,0.0,0.0,0
2281,2,0,0.0,8,0,1,0.0,0.0,0
2282,17,0,0.0,7,0,2,0.0,0.0,0
2283,11,0,0.0,2,0,2,0.0,0.0,0
2284,2,0,0.0,3,0,1,0.0,0.0,0
2285,1,0,0.0,56,1,10,0.0,0.0,0
2286,19,2,25.48,75,3,7,12.74,0.2857,0
2287,28,0,0.0,2,0,1,0.0,0.0,0
2288,5,0,0.0,20,0,2,0.0,0.0,0
2289,13,0,0.0,12,0,5,0.0,0.0,0
2290,11,0,0.0,2,0,1,0.0,0.0,0
2291,0,0,0.0,3,0,1,0.0,0.0,0
2292,0,0,0.0,50,2,7,0.0,0.0,0
2293,13,0,0.0,3,0,1,0.0,0.0,0
2294,5,0,0.0,4,0,2,0.0,0.0,0
2295,15,0,0.0,15,0,3,0.0,0.0,0
2296,22,0,0.0,1,0,1,0.0,0.0,0
2297,7,1,265.99,31,1,5,265.99,0.2,0
2298,4,1,28.99,39,1,4,28.99,0.25,1
2299,27,1,46.99,148,5,20,46.99,0.05,0
2300,26,0,0.0,3,0,1,0.0,0.0,0
2301,0,0,0.0,9,0,2,0.0,0.0,0
2302,5,0,0.0,7,0,3,0.0,0.0,0
2303,20,0,0.0,9,0,1,0.0,0.0,0
2304,0,0,0.0,97,3,12,0.0,0.0,0
2305,4,0,0.0,8,1,1,0.0,0.0,0
2306,22,0,0.0,1,0,1,0.0,0.0,0
2307,15,1,17.99,166,4,17,17.99,0.0588,0
2308,10,0,0.0,1,0,1,0.0,0.0,0
2309,5,1,14.99,9,1,2,14.99,0.5,1
2310,13,0,0.0,21,0,3,0.0,0.0,0
2311,5,1,23.99,8,1,2,23.99,0.5,1
2312,1,0,0.0,3,0,1,0.0,0.0,0
2313,7,3,469.85,157,9,18,156.62,0.1667,0
2314,6,0,0.0,8,0,3,0.0,0.0,0
2315,6,0,0.0,3,0,1,0.0,0.0,0
2316,6,1,241.99,116,5,16,241.99,0.0625,1
2317,7,0,0.0,66,3,6,0.0,0.0,0
2318,0,3,130.97,179,8,28,43.66,0.1071,1
2319,27,0,0.0,2,0,2,0.0,0.0,0
2320,4,0,0.0,63,0,10,0.0,0.0,0
2321,12,0,0.0,21,0,2,0.0,0.0,0
2322,5,0,0.0,10,2,2,0.0,0.0,0
2323,4,0,0.0,1,0,1,0.0,0.0,0
2324,8,4,201.03,145,9,17,50.26,0.2353,0
2325,20,0,0.0,3,0,1,0.0,0.0,0
2326,0,0,0.0,2,0,1,0.0,0.0,0
2327,8,0,0.0,56,2,5,0.0,0.0,0
2328,7,1,235.99,90,3,13,235.99,0.0769,0
2329,0,0,0.0,96,2,12,0.0,0.0,0
2330,9,0,0.0,27,0,4,0.0,0.0,0
2331,1,0,0.0,179,6,22,0.0,0.0,0
2332,2,0,0.0,3,0,1,0.0,0.0,0
2333,4,0,0.0,13,0,2,0.0,0.0,0
2334,1,0,0.0,20,0,4,0.0,0.0,0
2335,2,0,0.0,22,0,3,0.0,0.0,0
2336,0,0,0.0,28,1,6,0.0,0.0,0
2337,1,0,0.0,5,0,1,0.0,0.0,0
2338,6,0,0.0,23,0,6,0.0,0.0,0
2339,13,1,8.49,18,1,4,8.49,0.25,0
2340,3,1,84.99,3,1,1,84.99,1.0,1
2341,0,0,0.0,44,0,6,0.0,0.0,0
2342,5,0,0.0,43,0,4,0.0,0.0,0
2343,0,0,0.0,99,2,7,0.0,0.0,0
2344,21,0,0.0,11,0,1,0.0,0.0,0
2345,0,0,0.0,28,2,7,0.0,0.0,0
2346,16,0,0.0,6,0,1,0.0,0.0,0
2347,7,0,0.0,27,0,4,0.0,0.0,0
2348,9,0,0.0,14,0,3,0.0,0.0,0
2349,1,0,0.0,13,0,3,0.0,0.0,0
2350,22,0,0.0,16,0,2,0.0,0.0,0
2351,5,0,0.0,107,3,14,0.0,0.0,0
2352,2,0,0.0,36,3,11,0.0,0.0,0
2353,2,0,0.0,70,0,7,0.0,0.0,0
2354,12,0,0.0,28,0,4,0.0,0.0,0
2355,2,0,0.0,9,0,3,0.0,0.0,0
2356,3,0,0.0,52,2,6,0.0,0.0,0
2357,8,0,0.0,5,0,1,0.0,0.0,0
2358,14,0,0.0,6,0,2,0.0,0.0,0
2359,1,0,0.0,11,0,1,0.0,0.0,0
2360,8,2,813.14,231,10,34,406.57,0.0588,0
2361,1,0,0.0,5,0,1,0.0,0.0,0
2362,2,0,0.0,8,0,2,0.0,0.0,0
2363,22,0,0.0,7,0,1,0.0,0.0,0
2364,0,0,0.0,73,0,6,0.0,0.0,0
2365,13,0,0.0,13,0,4,0.0,0.0,0
2366,19,1,34.99,17,1,4,34.99,0.25,0
2367,28,0,0.0,2,0,1,0.0,0.0,0
2368,14,1,43.48,126,4,15,43.48,0.0667,0
2369,2,0,0.0,81,4,13,0.0,0.0,0
2370,23,0,0.0,6,0,1,0.0,0.0,0
2371,5,0,0.0,6,0,1,0.0,0.0,0
2372,3,0,0.0,13,0,2,0.0,0.0,0
2373,7,0,0.0,43,0,4,0.0,0.0,0
2374,1,0,0.0,2,0,1,0.0,0.0,0
2375,4,3,223.97,147,6,30,74.66,0.1,1
2376,2,1,57.99,62,1,8,57.99,0.125,1
2377,1,0,0.0,36,1,7,0.0,0.0,0
2378,19,1,158.99,47,2,9,158.99,0.1111,0
2379,4,0,0.0,9,1,3,0.0,0.0,0
2380,1,0,0.0,4,0,2,0.0,0.0,0
2381,15,1,89.99,27,1,6,89.99,0.1667,0
2382,4,4,137.96,122,5,17,34.49,0.2353,1
2383,3,0,0.0,24,0,7,0.0,0.0,0
2384,26,0,0.0,3,0,1,0.0,0.0,0
2385,1,0,0.0,32,1,8,0.0,0.0,0
2386,19,2,50.98,52,2,6,25.49,0.3333,0
2387,5,1,85.99,29,1,8,85.99,0.125,1
2388,11,0,0.0,7,1,2,0.0,0.0,0
2389,20,0,0.0,8,0,2,0.0,0.0,0
2390,16,0,0.0,23,0,2,0.0,0.0,0
2391,10,0,0.0,17,1,4,0.0,0.0,0
2392,25,1,131.26,25,2,8,131.26,0.125,0
2393,3,0,0.0,25,0,3,0.0,0.0,0
2394,4,0,0.0,19,1,3,0.0,0.0,0
2395,6,0,0.0,6,0,2,0.0,0.0,0
2396,1,0,0.0,37,2,4,0.0,0.0,0
2397,3,0,0.0,10,0,4,0.0,0.0,0
2398,16,0,0.0,5,0,2,0.0,0.0,0
2399,14,0,0.0,11,0,3,0.0,0.0,0
2400,0,0,0.0,75,1,10,0.0,0.0,0
2401,14,1,204.99,55,1,9,204.99,0.1111,0
2402,6,0,0.0,6,0,3,0.0,0.0,0
2403,0,0,0.0,59,1,9,0.0,0.0,0
2404,8,0,0.0,2,0,1,0.0,0.0,0
2405,6,0,0.0,29,0,6,0.0,0.0,0
2406,1,0,0.0,128,1,14,0.0,0.0,0
2407,29,0,0.0,1,0,1,0.0,0.0,0
2408,9,0,0.0,5,0,1,0.0,0.0,0
2409,2,0,0.0,5,0,1,0.0,0.0,0
2410,16,0,0.0,6,0,3,0.0,0.0,0
2411,11,0,0.0,7,0,2,0.0,0.0,0
2412,23,1,60.99,62,2,6,60.99,0.1667,0
2413,0,0,0.0,68,7,10,0.0,0.0,0
2414,5,1,18.98,10,1,1,18.98,1.0,1
2415,28,0,0.0,26,0,1,0.0,0.0,0
2416,5,0,0.0,22,0,5,0.0,0.0,0
2417,3,0,0.0,5,0,1,0.0,0.0,0
2418,28,1,92.99,32,2,4,92.99,0.25,0
2419,0,0,0.0,212,3,28,0.0,0.0,0
2420,2,0,0.0,11,0,2,0.0,0.0,0
2421,10,0,0.0,6,0,1,0.0,0.0,0
2422,2,0,0.0,9,1,1,0.0,0.0,0
2423,4,3,160.97,96,4,17,53.66,0.1765,1
2424,13,0,0.0,11,0,1,0.0,0.0,0
2425,1,0,0.0,7,0,2,0.0,0.0,0
2426,5,0,0.0,87,2,11,0.0,0.0,0
2427,4,1,23.99,30,2,6,23.99,0.1667,1
2428,6,0,0.0,16,1,4,0.0,0.0,0
2429,17,0,0.0,2,0,1,0.0,0.0,0
2430,4,0,0.0,30,1,6,0.0,0.0,0
2431,9,0,0.0,2,0,1,0.0,0.0,0
2432,0,0,0.0,10,0,3,0.0,0.0,0
2433,25,0,0.0,2,0,1,0.0,0.0,0
2434,5,0,0.0,26,1,5,0.0,0.0,0
2435,4,0,0.0,93,1,8,0.0,0.0,0
2436,1,0,0.0,39,1,5,0.0,0.0,0
2437,16,0,0.0,3,0,1,0.0,0.0,0
2438,2,0,0.0,51,1,8,0.0,0.0,0
2439,25,1,157.37,91,5,15,157.37,0.0667,0
2440,3,0,0.0,16,1,3,0.0,0.0,0
2441,0,0,0.0,25,0,4,0.0,0.0,0
2442,16,0,0.0,8,0,1,0.0,0.0,0
2443,0,0,0.0,20,0,7,0.0,0.0,0
2444,4,0,0.0,2,0,1,0.0,0.0,0
2445,8,2,76.98,110,2,15,38.49,0.1333,0
2446,11,1,46.99,3,1,1,46.99,1.0,0
2447,6,2,21.01,112,3,22,10.5,0.0909,1
2448,10,0,0.0,1,0,1,0.0,0.0,0
2449,0,0,0.0,23,1,4,0.0,0.0,0
2450,2,0,0.0,12,0,2,0.0,0.0,0
2451,21,0,0.0,26,2,2,0.0,0.0,0
2452,10,0,0.0,6,0,2,0.0,0.0,0
2453,2,4,703.95,103,9,20,175.99,0.2,1
2454,15,0,0.0,7,0,2,0.0,0.0,0
2455,4,0,0.0,9,0,1,0.0,0.0,0
2456,11,0,0.0,9,0,3,0.0,0.0,0
2457,0,0,0.0,55,2,11,0.0,0.0,0
2458,1,0,0.0,11,0,3,0.0,0.0,0
2459,5,0,0.0,26,0,3,0.0,0.0,0
2460,16,0,0.0,6,0,2,0.0,0.0,0
2461,9,1,13.99,113,3,24,13.99,0.0417,0
2462,1,0,0.0,19,0,3,0.0,0.0,0
2463,9,0,0.0,47,3,9,0.0,0.0,0
2464,5,0,0.0,35,1,7,0.0,0.0,0
2465,26,1,64.99,29,1,7,64.99,0.1429,0
2466,1,3,325.93,91,6,12,108.64,0.25,1
2467,13,1,8.49,85,2,17,8.49,0.0588,0
2468,0,0,0.0,50,3,10,0.0,0.0,0
2469,10,0,0.0,42,0,5,0.0,0.0,0
2470,3,0,0.0,9,0,2,0.0,0.0,0
2471,0,0,0.0,69,1,10,0.0,0.0,0
2472,0,0,0.0,110,4,19,0.0,0.0,0
2473,25,0,0.0,2,0,1,0.0,0.0,0
2474,3,0,0.0,33,1,6,0.0,0.0,0
2475,23,0,0.0,8,1,1,0.0,0.0,0
2476,8,0,0.0,25,0,3,0.0,0.0,0
2477,6,0,0.0,3,0,1,0.0,0.0,0
2478,4,0,0.0,82,0,11,0.0,0.0,0
2479,5,0,0.0,13,0,4,0.0,0.0,0
2480,7,0,0.0,2,0,1,0.0,0.0,0
2481,16,0,0.0,10,1,1,0.0,0.0,0
2482,2,0,0.0,107,3,11,0.0,0.0,0
2483,20,0,0.0,4,0,1,0.0,0.0,0
2484,0,0,0.0,118,3,15,0.0,0.0,0
2485,21,1,8.49,58,3,10,8.49,0.1,0
2486,1,0,0.0,13,0,2,0.0,0.0,0
2487,26,1,34.99,120,2,10,34.99,0.1,0
2488,19,0,0.0,1,0,1,0.0,0.0,0
2489,1,0,0.0,77,1,7,0.0,0.0,0
2490,7,0,0.0,5,0,1,0.0,0.0,0
2491,11,0,0.0,5,0,2,0.0,0.0,0
2492,0,0,0.0,8,0,2,0.0,0.0,0
2493,3,0,0.0,27,1,8,0.0,0.0,0
2494,0,0,0.0,44,1,5,0.0,0.0,0
2495,4,0,0.0,8,0,3,0.0,0.0,0
2496,0,0,0.0,58,3,12,0.0,0.0,0
2497,6,0,0.0,12,1,2,0.0,0.0,0
2498,19,0,0.0,26,2,1,0.0,0.0,0
2499,1,0,0.0,1,0,1,0.0,0.0,0
2500,26,1,39.99,117,7,19,39.99,0.0526,0
2501,1,0,0.0,6,0,1,0.0,0.0,0
2502,13,0,0.0,3,0,1,0.0,0.0,0
2503,25,0,0.0,13,0,1,0.0,0.0,0
2504,1,0,0.0,62,1,7,0.0,0.0,0
2505,2,3,255.96,40,5,9,85.32,0.3333,1
2506,4,0,0.0,62,2,9,0.0,0.0,0
2507,8,0,0.0,15,1,2,0.0,0.0,0
2508,10,0,0.0,44,3,5,0.0,0.0,0
2509,14,0,0.0,19,1,2,0.0,0.0,0
2510,3,0,0.0,7,0,3,0.0,0.0,0
2511,15,0,0.0,37,1,4,0.0,0.0,0
2512,3,0,0.0,68,0,11,0.0,0.0,0
2513,27,0,0.0,3,0,1,0.0,0.0,0
2514,27,0,0.0,3,0,2,0.0,0.0,0
2515,22,0,0.0,3,0,1,0.0,0.0,0
2516,9,0,0.0,3,0,1,0.0,0.0,0
2517,6,0,0.0,14,0,3,0.0,0.0,0
2518,0,0,0.0,9,1,3,0.0,0.0,0
2519,26,2,96.98,166,5,19,48.49,0.1053,0
2520,3,0,0.0,31,2,5,0.0,0.0,0
2521,14,0,0.0,7,0,2,0.0,0.0,0
2522,19,0,0.0,3,0,1,0.0,0.0,0
2523,5,0,0.0,35,1,5,0.0,0.0,0
2524,4,0,0.0,63,2,8,0.0,0.0,0
2525,13,1,85.99,28,1,9,85.99,0.1111,0
2526,0,0,0.0,56,0,9,0.0,0.0,0
2527,4,0,0.0,4,0,1,0.0,0.0,0
2528,6,0,0.0,8,0,3,0.0,0.0,0
2529,7,0,0.0,26,0,5,0.0,0.0,0
2530,13,0,0.0,2,0,1,0.0,0.0,0
2531,4,0,0.0,27,0,5,0.0,0.0,0
2532,10,1,74.97,58,1,10,74.97,0.1,0
2533,12,1,9.49,83,1,14,9.49,0.0714,0
2534,29,1,205.98,14,2,2,205.98,0.5,0
2535,2,0,0.0,8,0,1,0.0,0.0,0
2536,4,0,0.0,14,0,2,0.0,0.0,0
2537,0,0,0.0,8,0,2,0.0,0.0,0
2538,6,0,0.0,2,0,1,0.0,0.0,0
2539,10,0,0.0,16,1,6,0.0,0.0,0
2540,0,0,0.0,11,0,1,0.0,0.0,0
2541,6,0,0.0,24,0,5,0.0,0.0,0
2542,10,1,89.99,19,1,5,89.99,0.2,0
2543,28,1,7.76,68,6,9,7.76,0.1111,0
2544,6,0,0.0,4,0,2,0.0,0.0,0
2545,11,0,0.0,9,0,3,0.0,0.0,0
2546,27,0,0.0,2,0,1,0.0,0.0,0
2547,1,0,0.0,91,2,19,0.0,0.0,0
2548,8,1,37.99,75,2,7,37.99,0.1429,0
2549,4,1,89.99,44,2,10,89.99,0.1,1
2550,1,0,0.0,4,0,1,0.0,0.0,0
2551,17,0,0.0,7,0,1,0.0,0.0,0
2552,2,0,0.0,4,0,1,0.0,0.0,0
2553,1,0,0.0,8,0,3,0.0,0.0,0
2554,24,1,15.99,55,3,7,15.99,0.1429,0
2555,9,0,0.0,13,0,3,0.0,0.0,0
2556,18,1,65.99,70,2,11,65.99,0.0909,0
2557,3,0,0.0,17,0,4,0.0,0.0,0
2558,24,0,0.0,15,1,1,0.0,0.0,0
2559,4,0,0.0,56,4,10,0.0,0.0,0
2560,7,0,0.0,4,0,2,0.0,0.0,0
2561,1,0,0.0,34,0,6,0.0,0.0,0
2562,6,0,0.0,38,1,7,0.0,0.0,0
2563,7,0,0.0,1,0,1,0.0,0.0,0
2564,0,0,0.0,2,0,1,0.0,0.0,0
2565,26,0,0.0,6,1,1,0.0,0.0,0
2566,17,0,0.0,1,0,1,0.0,0.0,0
2567,22,0,0.0,7,0,1,0.0,0.0,0
2568,19,0,0.0,4,0,1,0.0,0.0,0
2569,0,0,0.0,16,0,3,0.0,0.0,0
2570,9,0,0.0,19,0,3,0.0,0.0,0
2571,8,1,34.99,60,1,5,34.99,0.2,0
2572,28,1,112.17,20,2,5,112.17,0.2,0
2573,17,0,0.0,24,1,4,0.0,0.0,0
2574,26,0,0.0,4,0,1,0.0,0.0,0
2575,18,0,0.0,3,0,1,0.0,0.0,0
2576,1,0,0.0,90,3,12,0.0,0.0,0
2577,17,2,180.98,89,4,12,90.49,0.1667,0
2578,1,0,0.0,17,0,5,0.0,0.0,0
2579,2,0,0.0,50,0,6,0.0,0.0,0
2580,0,3,152.96,72,4,11,50.99,0.2727,1
2581,3,0,0.0,36,4,6,0.0,0.0,0
2582,15,0,0.0,3,0,1,0.0,0.0,0
2583,0,0,0.0,32,0,4,0.0,0.0,0
2584,4,0,0.0,2,0,1,0.0,0.0,0
2585,1,0,0.0,1,0,1,0.0,0.0,0
2586,8,0,0.0,22,1,2,0.0,0.0,0
2587,5,0,0.0,131,0,16,0.0,0.0,0
2588,18,0,0.0,15,1,4,0.0,0.0,0
2589,3,0,0.0,25,0,8,0.0,0.0,0
2590,10,0,0.0,4,0,1,0.0,0.0,0
2591,5,0,0.0,3,0,1,0.0,0.0,0
2592,28,0,0.0,3,0,1,0.0,0.0,0
2593,0,0,0.0,62,0,8,0.0,0.0,0
2594,6,0,0.0,2,0,1,0.0,0.0,0
2595,3,0,0.0,47,1,7,0.0,0.0,0
2596,2,0,0.0,59,2,12,0.0,0.0,0
2597,18,0,0.0,7,0,3,0.0,0.0,0
2598,7,0,0.0,3,0,1,0.0,0.0,0
2599,2,0,0.0,3,0,1,0.0,0.0,0
2600,2,0,0.0,62,2,8,0.0,0.0,0
2601,10,0,0.0,3,0,1,0.0,0.0,0
2602,23,1,84.99,23,2,6,84.99,0.1667,0
2603,27,1,23.99,137,6,15,23.99,0.0667,0
2604,14,0,0.0,13,0,2,0.0,0.0,0
2605,2,0,0.0,22,0,4,0.0,0.0,0
2606,8,0,0.0,15,1,2,0.0,0.0,0
2607,30,0,0.0,4,0,1,0.0,0.0,0
2608,6,0,0.0,7,0,2,0.0,0.0,0
2609,14,0,0.0,6,0,1,0.0,0.0,0
2610,27,0,0.0,1,0,1,0.0,0.0,0
2611,29,0,0.0,15,0,1,0.0,0.0,0
2612,20,0,0.0,3,0,1,0.0,0.0,0
2613,5,0,0.0,8,1,4,0.0,0.0,0
2614,27,1,15.52,121,1,19,15.52,0.0526,0
2615,29,0,0.0,7,2,1,0.0,0.0,0
2616,0,0,0.0,4,0,2,0.0,0.0,0
2617,0,0,0.0,48,1,9,0.0,0.0,0
2618,30,0,0.0,3,0,1,0.0,0.0,0
2619,1,0,0.0,31,0,6,0.0,0.0,0
2620,28,1,18.98,146,3,17,18.98,0.0588,0
2621,25,0,0.0,4,0,1,0.0,0.0,0
2622,8,0,0.0,23,0,5,0.0,0.0,0
2623,6,0,0.0,25,1,6,0.0,0.0,0
2624,11,0,0.0,29,0,3,0.0,0.0,0
2625,17,0,0.0,13,0,3,0.0,0.0,0
2626,19,0,0.0,17,0,5,0.0,0.0,0
2627,27,0,0.0,6,0,1,0.0,0.0,0
2628,9,0,0.0,2,0,1,0.0,0.0,0
2629,0,0,0.0,25,1,6,0.0,0.0,0
2630,28,1,314.98,180,3,20,314.98,0.05,0
2631,5,0,0.0,44,1,7,0.0,0.0,0
2632,6,0,0.0,12,0,2,0.0,0.0,0
2633,22,2,1085.96,51,3,6,542.98,0.3333,0
2634,2,0,0.0,17,1,7,0.0,0.0,0
2635,17,0,0.0,4,0,1,0.0,0.0,0
2636,27,1,440.99,43,5,7,440.99,0.1429,0
2637,28,1,23.99,44,1,7,23.99,0.1429,0
2638,1,1,36.99,47,2,7,36.99,0.1429,1
2639,0,0,0.0,21,0,5,0.0,0.0,0
2640,7,0,0.0,22,2,6,0.0,0.0,0
2641,20,0,0.0,22,0,2,0.0,0.0,0
2642,11,0,0.0,20,3,3,0.0,0.0,0
2643,1,0,0.0,16,0,3,0.0,0.0,0
2644,15,0,0.0,4,0,1,0.0,0.0,0
2645,2,0,0.0,15,0,7,0.0,0.0,0
2646,3,0,0.0,15,1,3,0.0,0.0,0
2647,19,0,0.0,2,0,1,0.0,0.0,0
2648,6,0,0.0,7,0,1,0.0,0.0,0
2649,5,0,0.0,16,0,5,0.0,0.0,0
2650,8,0,0.0,20,0,2,0.0,0.0,0
2651,9,0,0.0,9,0,1,0.0,0.0,0
2652,2,0,0.0,78,5,8,0.0,0.0,0
2653,1,0,0.0,5,0,2,0.0,0.0,0
2654,3,1,142.99,60,1,5,142.99,0.2,1
2655,28,0,0.0,5,0,1,0.0,0.0,0
2656,9,0,0.0,12,1,3,0.0,0.0,0
2657,23,0,0.0,1,0,1,0.0,0.0,0
2658,6,0,0.0,5,1,2,0.0,0.0,0
2659,6,0,0.0,4,0,1,0.0,0.0,0
2660,27,1,11.99,52,1,10,11.99,0.1,0
2661,1,0,0.0,42,2,8,0.0,0.0,0
2662,0,0,0.0,1,0,1,0.0,0.0,0
2663,2,0,0.0,27,0,4,0.0,0.0,0
2664,16,0,0.0,6,0,2,0.0,0.0,0
2665,28,0,0.0,8,0,2,0.0,0.0,0
2666,3,0,0.0,9,0,1,0.0,0.0,0
2667,17,0,0.0,71,3,9,0.0,0.0,0
2668,0,0,0.0,6,0,1,0.0,0.0,0
2669,0,0,0.0,60,1,7,0.0,0.0,0
2670,10,0,0.0,7,0,1,0.0,0.0,0
2671,25,0,0.0,5,0,1,0.0,0.0,0
2672,10,0,0.0,17,0,3,0.0,0.0,0
2673,10,1,227.95,117,5,19,227.95,0.0526,0
2674,15,0,0.0,17,0,2,0.0,0.0,0
2675,6,0,0.0,105,4,10,0.0,0.0,0
2676,5,3,235.46,186,10,27,78.49,0.1111,1
2677,2,0,0.0,8,0,2,0.0,0.0,0
2678,20,0,0.0,7,0,1,0.0,0.0,0
2679,0,0,0.0,16,1,5,0.0,0.0,0
2680,4,0,0.0,66,3,8,0.0,0.0,0
2681,2,0,0.0,7,0,1,0.0,0.0,0
2682,8,0,0.0,10,1,4,0.0,0.0,0
2683,22,1,142.99,71,3,12,142.99,0.0833,0
2684,17,0,0.0,4,0,1,0.0,0.0,0
2685,1,0,0.0,11,1,3,0.0,0.0,0
2686,12,0,0.0,1,0,1,0.0,0.0,0
2687,15,0,0.0,5,0,1,0.0,0.0,0
2688,10,0,0.0,10,1,5,0.0,0.0,0
2689,6,0,0.0,9,0,3,0.0,0.0,0
2690,22,1,540.98,38,3,9,540.98,0.1111,0
2691,2,0,0.0,38,1,4,0.0,0.0,0
2692,1,0,0.0,51,0,8,0.0,0.0,0
2693,1,1,25.47,45,1,7,25.47,0.1429,1
2694,0,0,0.0,12,0,2,0.0,0.0,0
2695,4,0,0.0,7,0,1,0.0,0.0,0
2696,16,0,0.0,14,0,1,0.0,0.0,0
2697,5,0,0.0,9,0,4,0.0,0.0,0
2698,1,0,0.0,29,3,3,0.0,0.0,0
2699,7,0,0.0,5,0,1,0.0,0.0,0
2700,26,1,8.92,12,1,1,8.92,1.0,0
2701,0,0,0.0,13,2,2,0.0,0.0,0
2702,12,0,0.0,5,0,2,0.0,0.0,0
2703,23,0,0.0,6,0,1,0.0,0.0,0
2704,29,0,0.0,6,0,1,0.0,0.0,0
2705,3,0,0.0,11,1,2,0.0,0.0,0
2706,4,0,0.0,54,0,8,0.0,0.0,0
2707,1,0,0.0,43,0,8,0.0,0.0,0
2708,26,1,9.49,50,3,10,9.49,0.1,0
2709,18,0,0.0,2,0,1,0.0,0.0,0
2710,1,0,0.0,4,0,2,0.0,0.0,0
2711,1,0,0.0,68,5,8,0.0,0.0,0
2712,1,0,0.0,5,0,2,0.0,0.0,0
2713,1,0,0.0,84,3,12,0.0,0.0,0
2714,15,0,0.0,4,1,2,0.0,0.0,0
2715,25,0,0.0,9,0,1,0.0,0.0,0
2716,0,0,0.0,19,0,3,0.0,0.0,0
2717,14,0,0.0,2,1,1,0.0,0.0,0
2718,0,0,0.0,57,0,6,0.0,0.0,0
2719,4,0,0.0,23,0,3,0.0,0.0,0
2720,25,0,0.0,3,0,1,0.0,0.0,0
2721,14,0,0.0,14,0,2,0.0,0.0,0
2722,1,0,0.0,5,0,1,0.0,0.0,0
2723,1,0,0.0,12,0,5,0.0,0.0,0
2724,1,0,0.0,6,0,2,0.0,0.0,0
2725,27,0,0.0,7,1,1,0.0,0.0,0
2726,19,1,11.99,69,3,12,11.99,0.0833,0
2727,5,0,0.0,21,0,5,0.0,0.0,0
2728,22,0,0.0,1,0,1,0.0,0.0,0
2729,7,0,0.0,12,0,3,0.0,0.0,0
2730,23,0,0.0,4,0,1,0.0,0.0,0
2731,16,0,0.0,20,1,3,0.0,0.0,0
2732,1,0,0.0,19,1,4,0.0,0.0,0
2733,0,0,0.0,31,0,3,0.0,0.0,0
2734,14,1,47.98,25,2,5,47.98,0.2,0
2735,1,0,0.0,10,0,4,0.0,0.0,0
2736,0,2,465.97,62,3,7,232.98,0.2857,1
2737,1,0,0.0,129,3,11,0.0,0.0,0
2738,6,1,142.99,32,1,5,142.99,0.2,1
2739,0,1,7.49,10,1,3,7.49,0.3333,1
2740,0,4,321.94,97,6,14,80.48,0.2857,1
2741,2,0,0.0,9,0,1,0.0,0.0,0
2742,2,0,0.0,54,2,4,0.0,0.0,0
2743,5,0,0.0,5,0,1,0.0,0.0,0
2744,0,0,0.0,17,1,5,0.0,0.0,0
2745,27,1,76.99,44,2,5,76.99,0.2,0
2746,21,1,9.49,108,4,20,9.49,0.05,0
2747,4,0,0.0,32,0,9,0.0,0.0,0
2748,2,0,0.0,20,1,4,0.0,0.0,0
2749,2,0,0.0,18,0,3,0.0,0.0,0
2750,20,0,0.0,11,0,1,0.0,0.0,0
2751,1,0,0.0,34,2,5,0.0,0.0,0
2752,1,0,0.0,8,1,2,0.0,0.0,0
2753,8,1,51.99,127,2,19,51.99,0.0526,0
2754,1,0,0.0,13,0,3,0.0,0.0,0
2755,1,0,0.0,8,0,2,0.0,0.0,0
2756,2,0,0.0,41,0,8,0.0,0.0,0
2757,1,0,0.0,5,0,1,0.0,0.0,0
2758,13,0,0.0,3,0,1,0.0,0.0,0
2759,16,0,0.0,3,0,1,0.0,0.0,0
2760,4,0,0.0,7,0,1,0.0,0.0,0
2761,3,0,0.0,15,0,2,0.0,0.0,0
2762,10,0,0.0,18,0,5,0.0,0.0,0
2763,5,0,0.0,38,1,10,0.0,0.0,0
2764,4,0,0.0,9,2,1,0.0,0.0,0
2765,6,0,0.0,9,0,2,0.0,0.0,0
2766,23,0,0.0,23,0,1,0.0,0.0,0
2767,1,0,0.0,20,0,6,0.0,0.0,0
2768,15,0,0.0,6,0,1,0.0,0.0,0
2769,21,0,0.0,9,0,1,0.0,0.0,0
2770,4,0,0.0,48,3,3,0.0,0.0,0
2771,1,0,0.0,29,2,4,0.0,0.0,0
2772,1,0,0.0,83,2,12,0.0,0.0,0
2773,20,1,63.98,51,2,5,63.98,0.2,0
2774,23,2,223.98,49,5,7,111.99,0.2857,0
2775,4,0,0.0,140,0,15,0.0,0.0,0
2776,8,0,0.0,22,0,3,0.0,0.0,0
2777,30,0,0.0,4,0,1,0.0,0.0,0
2778,12,0,0.0,13,0,2,0.0,0.0,0
2779,14,0,0.0,6,0,3,0.0,0.0,0
2780,23,0,0.0,1,0,1,0.0,0.0,0
2781,11,0,0.0,28,1,2,0.0,0.0,0
2782,10,0,0.0,2,0,1,0.0,0.0,0
2783,3,0,0.0,7,0,2,0.0,0.0,0
2784,1,0,0.0,20,0,7,0.0,0.0,0
2785,4,0,0.0,75,2,9,0.0,0.0,0
2786,10,1,17.99,26,1,7,17.99,0.1429,0
2787,0,0,0.0,100,3,16,0.0,0.0,0
2788,0,0,0.0,61,1,5,0.0,0.0,0
2789,0,0,0.0,3,0,1,0.0,0.0,0
2790,12,0,0.0,2,0,1,0.0,0.0,0
2791,9,0,0.0,4,0,1,0.0,0.0,0
2792,0,0,0.0,8,0,1,0.0,0.0,0
2793,3,0,0.0,2,0,1,0.0,0.0,0
2794,3,0,0.0,11,0,2,0.0,0.0,0
2795,9,0,0.0,21,0,5,0.0,0.0,0
2796,3,0,0.0,10,0,4,0.0,0.0,0
2797,8,1,14.99,101,5,11,14.99,0.0909,0
2798,5,1,263.99,25,1,1,263.99,1.0,1
2799,0,6,315.45,216,10,35,52.58,0.1714,1
2800,18,0,0.0,7,0,1,0.0,0.0,0
2801,11,1,62.98,27,3,6,62.98,0.1667,0
2802,1,0,0.0,21,1,3,0.0,0.0,0
2803,0,0,0.0,39,0,8,0.0,0.0,0
2804,2,1,65.98,142,6,19,65.98,0.0526,1
2805,0,0,0.0,1,0,1,0.0,0.0,0
2806,14,0,0.0,4,0,1,0.0,0.0,0
2807,3,0,0.0,6,0,2,0.0,0.0,0
2808,6,0,0.0,2,0,1,0.0,0.0,0
2809,6,0,0.0,4,0,1,0.0,0.0,0
2810,4,0,0.0,3,0,1,0.0,0.0,0
2811,9,0,0.0,4,0,1,0.0,0.0,0
2812,11,0,0.0,16,0,2,0.0,0.0,0
2813,0,0,0.0,39,2,4,0.0,0.0,0
2814,8,0,0.0,5,0,2,0.0,0.0,0
2815,6,1,16.47,11,1,1,16.47,1.0,1
2816,2,0,0.0,45,2,5,0.0,0.0,0
2817,9,0,0.0,37,1,4,0.0,0.0,0
2818,13,0,0.0,13,2,3,0.0,0.0,0
2819,2,1,65.98,26,2,4,65.98,0.25,1
2820,6,0,0.0,11,0,3,0.0,0.0,0
2821,4,0,0.0,51,1,6,0.0,0.0,0
2822,2,0,0.0,53,2,5,0.0,0.0,0
2823,8,0,0.0,5,0,1,0.0,0.0,0
2824,5,0,0.0,15,0,3,0.0,0.0,0
2825,6,0,0.0,1,0,1,0.0,0.0,0
2826,5,0,0.0,34,1,6,0.0,0.0,0
2827,15,0,0.0,9,0,2,0.0,0.0,0
2828,20,2,62.39,150,6,17,31.2,0.1176,0
2829,27,0,0.0,3,0,1,0.0,0.0,0
2830,5,0,0.0,7,0,2,0.0,0.0,0
2831,4,1,103.99,67,2,10,103.99,0.1,1
2832,7,0,0.0,37,0,3,0.0,0.0,0
2833,0,0,0.0,8,0,2,0.0,0.0,0
2834,1,0,0.0,18,0,5,0.0,0.0,0
2835,4,0,0.0,12,0,1,0.0,0.0,0
2836,0,0,0.0,22,0,5,0.0,0.0,0
2837,4,0,0.0,1,0,1,0.0,0.0,0
2838,4,0,0.0,5,0,2,0.0,0.0,0
2839,6,0,0.0,10,0,3,0.0,0.0,0
2840,0,0,0.0,36,1,5,0.0,0.0,0
2841,2,0,0.0,11,0,1,0.0,0.0,0
2842,7,0,0.0,5,0,1,0.0,0.0,0
2843,2,0,0.0,15,1,2,0.0,0.0,0
2844,1,0,0.0,64,1,14,0.0,0.0,0
2845,3,0,0.0,69,0,9,0.0,0.0,0
2846,3,2,177.97,105,3,14,88.98,0.1429,1
2847,6,0,0.0,23,1,4,0.0,0.0,0
2848,16,0,0.0,1,0,1,0.0,0.0,0
2849,14,0,0.0,28,1,4,0.0,0.0,0
2850,1,0,0.0,41,1,8,0.0,0.0,0
2851,0,0,0.0,13,0,4,0.0,0.0,0
2852,27,2,270.15,107,5,15,135.07,0.1333,0
2853,24,0,0.0,22,1,2,0.0,0.0,0
2854,10,0,0.0,25,2,3,0.0,0.0,0
2855,27,0,0.0,4,0,1,0.0,0.0,0
2856,13,0,0.0,4,0,1,0.0,0.0,0
2857,9,0,0.0,5,0,1,0.0,0.0,0
2858,3,0,0.0,15,0,3,0.0,0.0,0
2859,4,0,0.0,7,0,2,0.0,0.0,0
2860,5,0,0.0,18,0,5,0.0,0.0,0
2861,18,0,0.0,6,1,1,0.0,0.0,0
2862,22,0,0.0,3,0,1,0.0,0.0,0
2863,0,0,0.0,16,3,3,0.0,0.0,0
2864,6,0,0.0,1,0,1,0.0,0.0,0
2865,5,0,0.0,12,1,2,0.0,0.0,0
2866,25,1,265.99,7,1,2,265.99,0.5,0
2867,15,0,0.0,10,0,1,0.0,0.0,0
2868,23,1,23.99,129,1,16,23.99,0.0625,0
2869,3,0,0.0,2,0,1,0.0,0.0,0
2870,12,2,70.97,106,3,18,35.48,0.1111,0
2871,3,0,0.0,33,1,5,0.0,0.0,0
2872,27,1,14.99,100,3,15,14.99,0.0667,0
2873,5,2,280.97,57,2,13,140.49,0.1538,1
2874,2,0,0.0,9,0,3,0.0,0.0,0
2875,0,3,442.96,190,6,40,147.65,0.075,1
2876,3,1,12.98,6,1,1,12.98,1.0,1
2877,9,0,0.0,17,0,3,0.0,0.0,0
2878,3,0,0.0,13,0,2,0.0,0.0,0
2879,5,1,14.99,145,4,17,14.99,0.0588,1
2880,11,0,0.0,2,0,1,0.0,0.0,0
2881,0,0,0.0,83,3,14,0.0,0.0,0
2882,0,0,0.0,5,0,1,0.0,0.0,0
2883,1,0,0.0,26,1,4,0.0,0.0,0
2884,5,0,0.0,7,0,2,0.0,0.0,0
2885,17,0,0.0,28,0,2,0.0,0.0,0
2886,2,0,0.0,62,2,10,0.0,0.0,0
2887,8,1,34.99,6,1,1,34.99,1.0,0
2888,0,0,0.0,2,0,2,0.0,0.0,0
2889,5,0,0.0,18,0,3,0.0,0.0,0
2890,25,1,7.76,101,5,12,7.76,0.0833,0
2891,2,0,0.0,9,0,3,0.0,0.0,0
2892,5,0,0.0,25,1,3,0.0,0.0,0
2893,0,0,0.0,15,0,4,0.0,0.0,0
2894,5,0,0.0,9,1,3,0.0,0.0,0
2895,29,1,3.49,13,1,4,3.49,0.25,0
2896,0,1,265.99,81,5,10,265.99,0.1,1
2897,7,0,0.0,22,0,3,0.0,0.0,0
2898,15,0,0.0,5,0,1,0.0,0.0,0
2899,8,0,0.0,24,0,3,0.0,0.0,0
2900,4,1,185.99,61,3,10,185.99,0.1,1
2901,9,0,0.0,60,1,11,0.0,0.0,0
2902,19,2,644.95,174,10,26,322.48,0.0769,0
2903,26,1,17.99,14,1,4,17.99,0.25,0
2904,1,0,0.0,3,0,1,0.0,0.0,0
2905,1,0,0.0,7,0,4,0.0,0.0,0
2906,6,0,0.0,22,0,4,0.0,0.0,0
2907,0,0,0.0,39,1,5,0.0,0.0,0
2908,0,0,0.0,118,2,18,0.0,0.0,0
2909,27,0,0.0,19,0,3,0.0,0.0,0
2910,13,3,309.74,217,11,35,103.25,0.0857,0
2911,10,0,0.0,2,0,1,0.0,0.0,0
2912,1,0,0.0,5,0,1,0.0,0.0,0
2913,5,1,241.99,40,1,6,241.99,0.1667,1
2914,6,0,0.0,28,0,6,0.0,0.0,0
2915,21,0,0.0,5,1,2,0.0,0.0,0
2916,15,0,0.0,3,0,1,0.0,0.0,0
2917,2,3,384.07,64,5,16,128.02,0.1875,1
2918,6,0,0.0,7,0,3,0.0,0.0,0
2919,0,2,113.98,168,6,19,56.99,0.1053,1
2920,14,0,0.0,10,1,1,0.0,0.0,0
2921,29,0,0.0,16,0,1,0.0,0.0,0
2922,30,1,56.99,83,4,20,56.99,0.05,0
2923,0,0,0.0,37,3,9,0.0,0.0,0
2924,1,0,0.0,38,1,3,0.0,0.0,0
2925,4,0,0.0,42,2,16,0.0,0.0,0
2926,0,1,130.99,98,9,22,130.99,0.0455,1
2927,1,0,0.0,45,3,9,0.0,0.0,0
2928,5,0,0.0,87,0,9,0.0,0.0,0
2929,27,0,0.0,2,0,1,0.0,0.0,0
2930,27,0,0.0,3,0,1,0.0,0.0,0
2931,27,0,0.0,1,0,1,0.0,0.0,0
2932,0,0,0.0,23,0,3,0.0,0.0,0
2933,24,1,263.99,12,1,1,263.99,1.0,0
2934,11,1,45.99,27,2,6,45.99,0.1667,0
2935,0,0,0.0,44,2,7,0.0,0.0,0
2936,26,1,39.99,11,2,3,39.99,0.3333,0
2937,1,0,0.0,1,0,1,0.0,0.0,0
2938,0,0,0.0,21,2,3,0.0,0.0,0
2939,19,1,25.47,109,1,14,25.47,0.0714,0
2940,0,0,0.0,15,0,5,0.0,0.0,0
2941,13,0,0.0,17,2,1,0.0,0.0,0
2942,2,0,0.0,42,3,6,0.0,0.0,0
2943,21,1,71.99,127,4,20,71.99,0.05,0
2944,1,0,0.0,54,1,7,0.0,0.0,0
2945,20,0,0.0,8,0,1,0.0,0.0,0
2946,27,0,0.0,6,0,1,0.0,0.0,0
2947,18,0,0.0,9,1,2,0.0,0.0,0
2948,1,0,0.0,34,0,9,0.0,0.0,0
2949,14,0,0.0,14,0,2,0.0,0.0,0
2950,5,0,0.0,70,5,14,0.0,0.0,0
2951,9,0,0.0,1,0,1,0.0,0.0,0
2952,24,0,0.0,6,0,1,0.0,0.0,0
2953,12,3,303.95,109,6,13,101.32,0.2308,0
2954,6,0,0.0,43,1,5,0.0,0.0,0
2955,3,0,0.0,9,0,4,0.0,0.0,0
2956,1,0,0.0,64,2,8,0.0,0.0,0
2957,18,2,128.98,177,6,22,64.49,0.0909,0
2958,6,2,776.97,107,5,23,388.48,0.087,1
2959,1,0,0.0,14,0,3,0.0,0.0,0
2960,2,0,0.0,25,0,4,0.0,0.0,0
2961,16,0,0.0,21,0,2,0.0,0.0,0
2962,15,0,0.0,9,0,1,0.0,0.0,0
2963,3,0,0.0,13,0,4,0.0,0.0,0
2964,0,0,0.0,30,1,7,0.0,0.0,0
2965,6,0,0.0,69,1,7,0.0,0.0,0
2966,20,0,0.0,6,0,1,0.0,0.0,0
2967,4,1,71.99,63,3,9,71.99,0.1111,1
2968,0,0,0.0,26,1,7,0.0,0.0,0
2969,27,2,408.98,123,5,23,204.49,0.087,0
2970,5,0,0.0,9,0,1,0.0,0.0,0
2971,5,0,0.0,13,1,4,0.0,0.0,0
2972,4,0,0.0,3,0,1,0.0,0.0,0
2973,17,0,0.0,28,0,3,0.0,0.0,0
2974,0,0,0.0,26,0,9,0.0,0.0,0
2975,9,0,0.0,8,1,1,0.0,0.0,0
2976,9,0,0.0,22,0,7,0.0,0.0,0
2977,13,0,0.0,8,0,2,0.0,0.0,0
2978,6,1,19.47,136,3,15,19.47,0.0667,1
2979,1,2,204.98,48,3,6,102.49,0.3333,1
2980,5,0,0.0,15,0,3,0.0,0.0,0
2981,17,0,0.0,7,1,1,0.0,0.0,0
2982,2,0,0.0,1,0,1,0.0,0.0,0
2983,18,0,0.0,9,0,1,0.0,0.0,0
2984,2,2,127.98,42,2,5,63.99,0.4,1
2985,1,0,0.0,159,3,18,0.0,0.0,0
2986,9,0,0.0,4,0,1,0.0,0.0,0
2987,14,0,0.0,7,0,3,0.0,0.0,0
2988,2,0,0.0,36,0,7,0.0,0.0,0
2989,4,0,0.0,35,0,6,0.0,0.0,0
2990,6,0,0.0,25,1,4,0.0,0.0,0
2991,6,0,0.0,3,0,1,0.0,0.0,0
2992,5,0,0.0,42,1,5,0.0,0.0,0
2993,20,0,0.0,3,0,1,0.0,0.0,0
2994,25,0,0.0,25,0,3,0.0,0.0,0
2995,13,6,556.41,164,9,23,92.74,0.2609,0
2996,6,0,0.0,30,0,3,0.0,0.0,0
2997,20,1,43.99,27,1,2,43.99,0.5,0
2998,0,0,0.0,7,0,3,0.0,0.0,0
2999,6,1,36.45,51,3,7,36.45,0.1429,1
3000,2,0,0.0,35,1,8,0.0,0.0,0
```

### data/metadata.json

```
{
  "dataset": "dm_conversion_training_v1",
  "description": "Seeded labeled training dataset for purchase/conversion prediction: per-customer features computed BEFORE the prediction window + will_purchase label (bought in the window). Leaky variant included for the leakage exercise.",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "orders": "Day 1/data/orders.csv",
    "module": "app.data.generate_training",
    "function": "generate_training",
    "builder": "app.ml.conversion.build_training_dataset"
  },
  "seed": {
    "seed": 42,
    "note": "features/labels are deterministic functions of the Day 1 seed (42); seed is the random_state for the leakage-exercise split+model"
  },
  "window_days": 7,
  "reference_date": "2026-01-31 23:59:38",
  "cutoff_date": "2026-01-24 23:59:38",
  "feature_columns": [
    "recency_days",
    "frequency",
    "monetary",
    "product_views",
    "cart_adds",
    "sessions",
    "aov",
    "conversion"
  ],
  "label_column": "will_purchase",
  "counts": {
    "customers_clean": 2579,
    "buyers_in_window_clean": 163,
    "positive_rate_clean": 0.0632,
    "customers_leaky": 3000,
    "buyers_in_window_leaky": 175
  },
  "leakage_exercise": {
    "model_type": "logistic_regression",
    "test_size": 0.3,
    "random_state": 42,
    "summary": {
      "clean_f1": 0.1754,
      "leaky_f1": 0.7619,
      "delta_f1": 0.5865,
      "leaky_looks_better": true
    },
    "details": {
      "model_type": "logistic_regression",
      "window_days": 7,
      "test_size": 0.3,
      "random_state": 42,
      "n_test": 774,
      "clean": {
        "accuracy": 0.9393,
        "precision": 0.625,
        "recall": 0.102,
        "f1": 0.1754,
        "confusion_matrix": [
          [
            722,
            3
          ],
          [
            44,
            5
          ]
        ],
        "n": 774,
        "positive_class": 1
      },
      "leaky": {
        "accuracy": 0.9742,
        "precision": 0.9143,
        "recall": 0.6531,
        "f1": 0.7619,
        "confusion_matrix": [
          [
            722,
            3
          ],
          [
            17,
            32
          ]
        ],
        "n": 774,
        "positive_class": 1
      },
      "delta_f1": 0.5865
    }
  },
  "fields": {
    "user_id": "int, stabilan ID korisnika (FK -> customers.user_id)",
    "recency_days": "int, dani od cut-off-a do poslednje kupovine (ili aktivnosti) PRE window-a; u leaky verziji od reference do poslednje kupovine (uklj. window)",
    "frequency": "int, broj porudžbina pre cut-off-a (0 za ne-kupce); u leaky verziji ukupan broj porudžbina",
    "monetary": "float, ukupna vrednost porudžbina pre cut-off-a; u leaky verziji uključuje window",
    "product_views": "int, broj product_view događaja pre cut-off-a",
    "cart_adds": "int, broj add_to_cart događaja pre cut-off-a",
    "sessions": "int, broj jedinstvenih sesija pre cut-off-a",
    "aov": "float, prosečna vrednost porudžbine pre cut-off-a; 0.0 za ne-kupce",
    "conversion": "float 0..1, sesije sa kupovinom / sve sesije pre cut-off-a",
    "will_purchase": "int 0/1, labela: 1 ako je korisnik kupio u prediction window-u (poslednjih window_days dana dataset-a)"
  },
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "training_dataset.csv": "966728b451496fa97a336ec44935bf30561ba8f4e30f0e54f42d6b2b134ca72d",
      "leaky_training_dataset.csv": "695bdfe9fa51c2adce2ad2b68b242f5f5804782729b6bcb61160aa44397e944a"
    }
  }
}
```

### data/README.md

# Day 3 podaci — labeled training dataset za predikciju kupovine

Deterministički, **byte-for-byte reproduktivni** labeled training dataset,
**izveden** iz Day 1 seeded događaja i porudžbina (ne duplira ih). Kompletna
dokumentacija (izvor, parametri, značenje polja, sha256) je u
`metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `training_dataset.csv` | **clean** verzija: feature-i po korisniku **pre** cut-off-a + labela `will_purchase` (kupovina u 7-dnevnom window-u) | 2579 |
| `leaky_training_dataset.csv` | **leaky** verzija: feature-i iz CELE istorije (uključujući window — namerni bug) + ista labela | 3000 |
| `leakage_metrics.json` | before/after metrike: isti model, isti split, clean vs leaky | — |
| `metadata.json` | izvor, cutoff/reference, značenja polja, counts, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/events.csv` + `Day 1/data/orders.csv` (jedini izvor istine).
* Graditelj: `app.ml.conversion.build_training_dataset` (ista funkcija koju koristi
  `POST /models/conversion/train`).
* Generator: `app/data/generate_training.py` (upisuje CSV + leakage + metadata).
* `reference_date = 2026-01-31 23:24:05`, `cutoff_date = 2026-01-24 23:24:05`
  (window = poslednjih 7 dana dataset-a).

## Labela i window (definicije)

* **cutoff** = `reference − window_days` = `2026-01-24 23:24:05`.
* **Labela** `will_purchase`: 1 ako je korisnik kupio u `[cutoff, reference]`,
  inače 0.
* **Clean feature-i** se računaju SAMO na događajima/porudžbinama **pre**
  cut-off-a (recency u odnosu na cutoff) — model ne vidi period koji predviđa.
* **Leaky feature-i** se računaju na celoj istoriji: `recency_days` direktno
  kodira labelu (kupac u window-u ima recency 0–6), `frequency`/`monetary`/
  `conversion` uključuju window kupovine. Ovo je namerni bug za vežbu.

## Stanje u ovom seed-u (window = 7 dana)

* clean: **2579** korisnika (aktivni pre cut-off-a), **163** kupaca u window-u (pozitivna stopa **0.063**)
* leaky: **3000** korisnika, **175** kupaca u window-u

## Leakage (before/after) — logistic\_regression, test\_size 0.3

| Verzija | Accuracy | Precision | Recall | F1 | Confusion matrix |
| --- | --- | --- | --- | --- | --- |
| **clean** (feature-i pre cut-off-a) | 0.9393 | 0.6250 | 0.1020 | 0.1754 | [[722, 3], [44, 5]] |
| **leaky** (feature-i iz cele istorije) | 0.9742 | 0.9143 | 0.6531 | 0.7619 | [[722, 3], [17, 32]] |

Leaky model izgleda daleko bolje (`ΔF1 = +0.587`) jer **vara** — feature-i vide
kupovine iz samog window-a koji predviđa. Clean model ima nizak recall: pozitivna
klasa je retka (≈ 6.3 %), pa je ovo realan, težak problem — ne bug.
Test skup: **774** korisnika (`test_size` 0.3, `random_state` 42).

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_training --seed 42
```

Dva pokretanja sa istim seed-om daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Labela i feature-i su *ulaz* za model, ne rezultat. Visoke metrike leaky
verzije ne znače da je model „dobar" — znače da je pokvaren (vidi
`leakage_metrics.json`). Ni clean metrike (F1 ≈ 0.05–0.16) ne znače da je
predikcija „nemoguća" — znače da je na ovom sintetičkom skupu signal slab
(vidi Day 3 README, „What the result does NOT prove").

### data/training\_dataset.csv

```
user_id,recency_days,frequency,monetary,product_views,cart_adds,sessions,aov,conversion,will_purchase
1,6,0,0.0,2,0,1,0.0,0.0,0
3,1,0,0.0,12,0,2,0.0,0.0,0
4,15,0,0.0,5,0,2,0.0,0.0,0
5,1,0,0.0,49,2,7,0.0,0.0,0
6,18,2,17.48,68,2,11,8.74,0.1818,0
7,9,0,0.0,11,0,3,0.0,0.0,0
8,9,0,0.0,17,0,4,0.0,0.0,0
9,19,0,0.0,1,0,1,0.0,0.0,0
10,14,2,47.97,144,8,18,23.98,0.1111,0
12,1,0,0.0,51,1,5,0.0,0.0,0
13,13,0,0.0,5,1,3,0.0,0.0,0
14,10,0,0.0,14,0,1,0.0,0.0,0
15,13,0,0.0,30,0,3,0.0,0.0,0
16,16,0,0.0,7,0,2,0.0,0.0,0
20,1,0,0.0,17,1,6,0.0,0.0,0
23,1,1,35.99,34,2,6,35.99,0.1667,0
24,1,0,0.0,9,0,1,0.0,0.0,0
25,0,0,0.0,17,3,4,0.0,0.0,0
26,9,0,0.0,9,0,2,0.0,0.0,0
27,6,0,0.0,19,0,4,0.0,0.0,0
28,7,0,0.0,14,0,4,0.0,0.0,0
29,4,0,0.0,12,0,3,0.0,0.0,0
30,1,2,55.48,96,4,11,27.74,0.1818,0
31,17,0,0.0,24,1,3,0.0,0.0,0
32,0,0,0.0,5,0,1,0.0,0.0,0
34,5,0,0.0,15,1,2,0.0,0.0,0
35,4,0,0.0,2,0,1,0.0,0.0,0
36,10,0,0.0,4,0,2,0.0,0.0,0
37,7,0,0.0,15,0,3,0.0,0.0,1
38,5,0,0.0,74,0,7,0.0,0.0,0
39,19,0,0.0,12,0,2,0.0,0.0,0
40,1,0,0.0,33,0,3,0.0,0.0,0
41,1,0,0.0,33,2,4,0.0,0.0,0
42,10,0,0.0,21,1,4,0.0,0.0,0
43,0,0,0.0,29,1,7,0.0,0.0,0
44,18,0,0.0,3,0,1,0.0,0.0,0
45,0,0,0.0,35,0,4,0.0,0.0,0
46,3,1,14.99,5,1,2,14.99,0.5,0
47,1,0,0.0,57,1,7,0.0,0.0,0
48,13,0,0.0,16,0,4,0.0,0.0,0
49,13,0,0.0,6,0,1,0.0,0.0,0
50,10,0,0.0,14,0,1,0.0,0.0,0
51,0,0,0.0,16,0,4,0.0,0.0,0
52,9,0,0.0,3,0,1,0.0,0.0,0
53,8,0,0.0,9,0,2,0.0,0.0,0
54,17,0,0.0,2,0,1,0.0,0.0,0
55,0,0,0.0,19,0,6,0.0,0.0,0
57,0,0,0.0,47,0,8,0.0,0.0,0
58,1,0,0.0,20,0,5,0.0,0.0,0
59,5,0,0.0,36,0,7,0.0,0.0,0
60,6,1,5.49,16,2,1,5.49,1.0,0
61,21,1,241.99,73,2,9,241.99,0.1111,0
62,20,0,0.0,11,1,2,0.0,0.0,0
63,19,1,21.99,51,3,9,21.99,0.1111,0
64,22,1,15.99,40,4,8,15.99,0.125,0
65,5,0,0.0,16,0,3,0.0,0.0,0
66,8,2,83.98,78,3,15,41.99,0.1333,1
67,0,0,0.0,21,0,3,0.0,0.0,1
68,4,0,0.0,10,0,5,0.0,0.0,0
69,7,0,0.0,14,1,3,0.0,0.0,1
70,2,0,0.0,1,0,1,0.0,0.0,0
71,5,0,0.0,17,1,3,0.0,0.0,0
72,7,0,0.0,57,1,7,0.0,0.0,0
73,0,0,0.0,17,0,5,0.0,0.0,0
74,4,0,0.0,19,0,4,0.0,0.0,1
75,2,0,0.0,21,0,3,0.0,0.0,0
77,3,0,0.0,25,1,5,0.0,0.0,0
78,6,0,0.0,4,0,2,0.0,0.0,0
79,15,0,0.0,6,0,1,0.0,0.0,0
80,14,0,0.0,6,0,1,0.0,0.0,0
81,4,0,0.0,13,0,4,0.0,0.0,0
83,5,0,0.0,7,0,1,0.0,0.0,0
84,19,0,0.0,5,0,1,0.0,0.0,0
85,11,1,193.98,12,1,1,193.98,1.0,0
86,19,0,0.0,1,0,1,0.0,0.0,0
87,0,0,0.0,41,0,9,0.0,0.0,0
88,1,0,0.0,9,0,1,0.0,0.0,0
89,21,2,215.19,20,2,4,107.6,0.5,0
90,2,0,0.0,3,0,1,0.0,0.0,0
92,2,0,0.0,22,0,2,0.0,0.0,0
93,0,0,0.0,9,0,2,0.0,0.0,1
94,3,0,0.0,33,0,9,0.0,0.0,0
95,7,0,0.0,45,0,4,0.0,0.0,0
96,0,0,0.0,2,0,1,0.0,0.0,0
97,8,0,0.0,12,0,6,0.0,0.0,0
98,12,0,0.0,1,0,1,0.0,0.0,0
99,12,0,0.0,2,0,1,0.0,0.0,0
100,0,0,0.0,8,0,1,0.0,0.0,0
101,12,0,0.0,7,0,1,0.0,0.0,0
102,14,0,0.0,3,0,1,0.0,0.0,0
104,3,0,0.0,3,0,1,0.0,0.0,0
106,3,0,0.0,54,1,8,0.0,0.0,0
107,19,0,0.0,5,0,1,0.0,0.0,0
108,2,1,90.99,30,1,4,90.99,0.25,0
110,0,0,0.0,46,2,10,0.0,0.0,0
111,12,1,22.99,9,1,2,22.99,0.5,0
112,4,0,0.0,7,0,1,0.0,0.0,0
113,9,0,0.0,10,1,4,0.0,0.0,0
114,4,0,0.0,69,3,9,0.0,0.0,0
115,6,0,0.0,57,2,8,0.0,0.0,0
116,11,1,37.99,31,1,2,37.99,0.5,0
117,18,0,0.0,5,0,2,0.0,0.0,0
118,13,0,0.0,4,0,1,0.0,0.0,0
119,16,0,0.0,11,0,2,0.0,0.0,0
120,23,1,265.99,11,2,4,265.99,0.25,0
121,2,0,0.0,47,2,8,0.0,0.0,0
123,6,0,0.0,10,0,1,0.0,0.0,0
124,2,0,0.0,3,0,1,0.0,0.0,0
125,0,0,0.0,10,1,4,0.0,0.0,1
126,19,0,0.0,16,0,1,0.0,0.0,0
129,5,0,0.0,30,0,5,0.0,0.0,0
130,0,0,0.0,56,2,10,0.0,0.0,1
131,20,1,442.98,76,5,15,442.98,0.0667,0
132,15,0,0.0,5,0,1,0.0,0.0,0
133,3,0,0.0,106,5,8,0.0,0.0,0
134,18,0,0.0,17,1,3,0.0,0.0,0
135,21,0,0.0,3,0,1,0.0,0.0,0
136,17,0,0.0,2,0,1,0.0,0.0,0
137,0,0,0.0,11,0,1,0.0,0.0,0
138,15,0,0.0,29,0,2,0.0,0.0,0
139,2,0,0.0,3,0,1,0.0,0.0,0
140,18,0,0.0,12,0,2,0.0,0.0,1
141,8,1,240.97,16,3,2,240.97,0.5,0
142,10,1,14.99,55,2,8,14.99,0.125,0
143,18,1,30.99,19,2,2,30.99,0.5,0
144,4,0,0.0,47,1,4,0.0,0.0,0
145,18,0,0.0,5,0,2,0.0,0.0,0
146,19,1,103.99,21,2,3,103.99,0.3333,0
147,6,0,0.0,14,1,1,0.0,0.0,0
149,1,0,0.0,15,0,2,0.0,0.0,1
150,2,2,663.83,58,5,10,331.92,0.2,0
151,3,3,832.97,62,6,11,277.66,0.2727,0
152,19,4,557.57,76,6,13,139.39,0.3077,0
153,0,0,0.0,24,0,3,0.0,0.0,0
154,7,0,0.0,6,0,2,0.0,0.0,0
155,7,0,0.0,4,0,1,0.0,0.0,0
156,0,0,0.0,34,0,5,0.0,0.0,0
157,15,0,0.0,16,0,2,0.0,0.0,0
158,5,0,0.0,13,0,5,0.0,0.0,0
159,7,0,0.0,18,0,2,0.0,0.0,0
160,5,1,110.99,86,4,8,110.99,0.125,0
161,8,0,0.0,18,1,1,0.0,0.0,0
162,2,0,0.0,14,0,3,0.0,0.0,0
164,21,1,19.17,43,1,6,19.17,0.1667,0
165,0,0,0.0,25,0,3,0.0,0.0,0
166,7,0,0.0,4,0,3,0.0,0.0,0
167,2,3,187.97,124,8,15,62.66,0.2,0
168,15,1,15.99,9,1,1,15.99,1.0,0
169,2,4,835.95,104,7,21,208.99,0.1905,0
170,20,0,0.0,4,1,1,0.0,0.0,0
171,7,0,0.0,5,0,1,0.0,0.0,0
172,11,0,0.0,3,0,2,0.0,0.0,0
173,1,0,0.0,21,0,3,0.0,0.0,0
174,9,0,0.0,1,0,1,0.0,0.0,0
175,6,0,0.0,10,0,2,0.0,0.0,0
176,6,0,0.0,2,0,1,0.0,0.0,0
178,13,0,0.0,6,0,2,0.0,0.0,0
179,2,0,0.0,32,1,8,0.0,0.0,0
180,22,1,61.99,18,1,2,61.99,0.5,1
181,3,1,30.99,40,1,7,30.99,0.1429,0
183,0,0,0.0,8,0,2,0.0,0.0,0
184,17,0,0.0,2,0,1,0.0,0.0,0
185,16,1,815.98,39,3,7,815.98,0.1429,0
186,0,0,0.0,51,2,8,0.0,0.0,0
187,3,1,11.99,31,3,5,11.99,0.2,0
188,13,0,0.0,3,0,1,0.0,0.0,0
189,2,1,56.99,46,3,4,56.99,0.25,0
190,13,3,196.5,54,4,10,65.5,0.3,0
191,3,0,0.0,9,0,4,0.0,0.0,0
192,3,0,0.0,6,0,3,0.0,0.0,0
193,1,0,0.0,24,0,3,0.0,0.0,1
195,6,1,49.98,109,1,12,49.98,0.0833,0
196,1,0,0.0,116,2,19,0.0,0.0,0
197,7,0,0.0,5,1,1,0.0,0.0,0
198,17,0,0.0,6,1,1,0.0,0.0,0
199,0,0,0.0,40,0,7,0.0,0.0,0
200,0,0,0.0,7,0,3,0.0,0.0,0
201,6,0,0.0,30,2,2,0.0,0.0,0
202,5,0,0.0,10,0,1,0.0,0.0,0
204,4,0,0.0,37,1,9,0.0,0.0,1
205,9,2,92.98,66,3,10,46.49,0.2,0
206,18,1,17.99,15,1,2,17.99,0.5,0
207,19,0,0.0,4,0,1,0.0,0.0,0
208,1,0,0.0,61,0,8,0.0,0.0,0
209,1,0,0.0,44,0,7,0.0,0.0,0
210,21,0,0.0,12,1,1,0.0,0.0,0
211,3,0,0.0,12,0,3,0.0,0.0,0
212,8,0,0.0,15,1,3,0.0,0.0,0
213,6,0,0.0,35,4,4,0.0,0.0,0
214,0,0,0.0,17,1,2,0.0,0.0,0
215,17,2,54.94,151,4,21,27.47,0.0952,1
216,4,3,134.46,125,7,14,44.82,0.2143,0
217,10,2,74.97,52,3,7,37.48,0.2857,1
218,1,0,0.0,14,0,5,0.0,0.0,0
219,7,0,0.0,50,0,7,0.0,0.0,0
220,19,1,46.99,66,2,9,46.99,0.1111,0
221,8,1,59.99,50,3,10,59.99,0.1,0
222,20,1,65.99,16,1,3,65.99,0.3333,0
225,7,0,0.0,11,1,1,0.0,0.0,0
226,23,0,0.0,11,1,1,0.0,0.0,0
227,6,0,0.0,42,2,4,0.0,0.0,0
228,3,0,0.0,4,0,1,0.0,0.0,0
229,2,0,0.0,15,0,1,0.0,0.0,0
230,0,3,139.96,86,5,15,46.65,0.2,0
231,14,1,111.97,48,2,4,111.97,0.25,1
232,2,0,0.0,16,0,3,0.0,0.0,0
233,3,0,0.0,6,0,1,0.0,0.0,0
234,23,1,46.99,4,1,1,46.99,1.0,0
235,0,0,0.0,81,3,12,0.0,0.0,1
236,10,0,0.0,10,0,2,0.0,0.0,0
237,12,0,0.0,10,0,3,0.0,0.0,0
238,18,0,0.0,5,0,1,0.0,0.0,0
240,5,0,0.0,10,0,4,0.0,0.0,0
241,1,0,0.0,40,2,7,0.0,0.0,0
242,1,0,0.0,26,0,5,0.0,0.0,0
243,5,0,0.0,19,0,3,0.0,0.0,0
244,8,1,23.98,64,4,8,23.98,0.125,0
245,3,0,0.0,29,2,8,0.0,0.0,0
246,3,0,0.0,13,0,3,0.0,0.0,0
247,13,1,24.99,7,2,1,24.99,1.0,0
249,21,0,0.0,7,0,1,0.0,0.0,0
250,5,0,0.0,4,1,1,0.0,0.0,0
251,0,0,0.0,105,2,11,0.0,0.0,0
252,4,0,0.0,44,0,6,0.0,0.0,0
253,2,0,0.0,82,0,8,0.0,0.0,0
254,0,0,0.0,39,2,6,0.0,0.0,0
255,2,0,0.0,3,0,1,0.0,0.0,0
256,13,2,145.53,36,4,7,72.76,0.2857,0
257,8,0,0.0,12,1,3,0.0,0.0,0
260,1,0,0.0,7,0,2,0.0,0.0,1
261,3,0,0.0,4,0,1,0.0,0.0,0
262,7,0,0.0,1,0,1,0.0,0.0,0
264,2,0,0.0,103,3,10,0.0,0.0,0
265,21,0,0.0,3,0,1,0.0,0.0,0
266,7,1,493.99,50,1,10,493.99,0.1,0
267,13,0,0.0,4,1,1,0.0,0.0,0
269,15,2,37.64,67,2,5,18.82,0.4,0
270,6,0,0.0,57,2,13,0.0,0.0,0
271,18,0,0.0,5,0,1,0.0,0.0,0
272,21,0,0.0,9,0,1,0.0,0.0,0
273,14,0,0.0,4,0,1,0.0,0.0,0
274,0,1,6.98,59,2,7,6.98,0.1429,0
275,19,1,85.99,22,1,3,85.99,0.3333,0
276,13,0,0.0,26,1,3,0.0,0.0,0
277,14,1,76.99,96,5,17,76.99,0.0588,1
278,4,0,0.0,12,1,3,0.0,0.0,0
279,14,0,0.0,17,1,3,0.0,0.0,0
280,3,0,0.0,49,0,7,0.0,0.0,0
281,3,0,0.0,32,0,7,0.0,0.0,1
284,2,0,0.0,51,3,7,0.0,0.0,0
286,16,1,25.99,61,2,8,25.99,0.125,0
288,0,0,0.0,25,0,3,0.0,0.0,0
290,8,1,8.49,39,1,5,8.49,0.2,0
291,2,0,0.0,19,0,7,0.0,0.0,0
292,3,0,0.0,3,0,1,0.0,0.0,0
293,7,0,0.0,7,0,2,0.0,0.0,0
294,0,0,0.0,23,0,3,0.0,0.0,0
295,8,0,0.0,2,1,1,0.0,0.0,0
296,9,0,0.0,3,0,1,0.0,0.0,0
297,7,0,0.0,9,0,1,0.0,0.0,0
298,2,3,267.07,66,5,12,89.02,0.25,0
299,1,0,0.0,20,1,1,0.0,0.0,0
300,2,0,0.0,9,2,2,0.0,0.0,0
301,0,0,0.0,9,0,4,0.0,0.0,0
303,1,0,0.0,3,0,1,0.0,0.0,0
304,1,0,0.0,5,0,1,0.0,0.0,0
305,7,0,0.0,9,0,2,0.0,0.0,0
306,5,1,59.99,52,3,11,59.99,0.0909,1
307,2,0,0.0,1,0,1,0.0,0.0,0
308,6,0,0.0,5,0,1,0.0,0.0,0
309,11,0,0.0,2,0,1,0.0,0.0,0
310,2,0,0.0,2,0,1,0.0,0.0,0
312,8,0,0.0,7,0,4,0.0,0.0,0
313,2,0,0.0,19,0,4,0.0,0.0,0
314,9,0,0.0,10,1,5,0.0,0.0,1
315,3,0,0.0,39,1,4,0.0,0.0,0
317,0,0,0.0,19,1,4,0.0,0.0,0
318,6,1,89.99,38,2,6,89.99,0.1667,0
319,14,1,141.99,46,2,9,141.99,0.1111,0
320,3,0,0.0,10,0,1,0.0,0.0,0
321,12,0,0.0,2,0,1,0.0,0.0,0
323,10,0,0.0,5,0,1,0.0,0.0,0
324,18,0,0.0,2,0,1,0.0,0.0,0
325,1,0,0.0,8,0,1,0.0,0.0,0
326,21,1,7.76,45,2,9,7.76,0.1111,0
329,9,0,0.0,3,0,2,0.0,0.0,0
330,19,0,0.0,2,0,1,0.0,0.0,0
331,0,0,0.0,110,2,14,0.0,0.0,0
332,8,0,0.0,5,0,3,0.0,0.0,0
333,3,0,0.0,39,1,6,0.0,0.0,0
334,8,0,0.0,6,0,1,0.0,0.0,0
335,17,0,0.0,3,0,1,0.0,0.0,0
336,19,0,0.0,3,0,1,0.0,0.0,0
337,13,3,235.87,100,7,12,78.62,0.25,0
338,3,0,0.0,32,0,4,0.0,0.0,0
339,7,0,0.0,8,0,2,0.0,0.0,0
341,8,0,0.0,23,2,3,0.0,0.0,0
342,1,0,0.0,27,1,2,0.0,0.0,0
344,20,1,61.97,71,3,12,61.97,0.0833,0
346,2,0,0.0,24,1,4,0.0,0.0,0
347,5,0,0.0,6,0,1,0.0,0.0,0
348,2,0,0.0,9,0,1,0.0,0.0,0
349,13,0,0.0,1,0,1,0.0,0.0,0
350,3,1,48.98,61,5,11,48.98,0.0909,0
351,18,0,0.0,5,0,1,0.0,0.0,0
353,15,0,0.0,1,0,1,0.0,0.0,0
354,2,0,0.0,36,0,7,0.0,0.0,0
355,0,0,0.0,9,0,2,0.0,0.0,0
356,7,1,48.99,15,1,3,48.99,0.3333,0
357,22,0,0.0,3,1,2,0.0,0.0,0
359,5,0,0.0,21,1,7,0.0,0.0,0
360,0,0,0.0,54,1,12,0.0,0.0,0
361,7,0,0.0,20,1,3,0.0,0.0,0
362,14,0,0.0,4,0,2,0.0,0.0,0
363,0,0,0.0,1,0,1,0.0,0.0,0
364,5,0,0.0,6,0,2,0.0,0.0,0
365,18,1,150.99,15,1,1,150.99,1.0,0
366,0,0,0.0,51,2,8,0.0,0.0,0
367,8,0,0.0,9,0,3,0.0,0.0,0
368,9,2,173.98,64,3,10,86.99,0.2,0
369,4,0,0.0,16,1,4,0.0,0.0,0
370,0,0,0.0,9,0,1,0.0,0.0,0
371,1,0,0.0,79,1,6,0.0,0.0,0
372,1,0,0.0,43,0,4,0.0,0.0,0
373,7,1,17.99,61,3,8,17.99,0.125,0
375,5,2,351.98,50,6,8,175.99,0.25,1
376,1,0,0.0,17,0,5,0.0,0.0,0
377,4,0,0.0,3,0,3,0.0,0.0,0
378,2,0,0.0,9,0,2,0.0,0.0,0
379,13,0,0.0,1,0,1,0.0,0.0,0
380,6,0,0.0,21,0,4,0.0,0.0,0
381,11,0,0.0,24,1,3,0.0,0.0,0
382,5,0,0.0,2,0,1,0.0,0.0,0
383,0,0,0.0,20,1,3,0.0,0.0,0
384,5,0,0.0,2,0,2,0.0,0.0,0
385,0,0,0.0,2,0,1,0.0,0.0,0
386,3,0,0.0,6,0,1,0.0,0.0,0
387,5,0,0.0,26,1,7,0.0,0.0,0
388,8,1,69.98,52,1,7,69.98,0.1429,0
389,13,0,0.0,9,0,3,0.0,0.0,0
390,21,2,241.48,64,5,9,120.74,0.2222,0
391,21,0,0.0,1,0,1,0.0,0.0,0
392,22,0,0.0,3,0,1,0.0,0.0,0
393,5,0,0.0,28,0,2,0.0,0.0,0
394,13,3,244.95,105,10,24,81.65,0.125,1
395,6,6,509.19,233,11,44,84.86,0.1364,1
396,7,2,77.98,102,6,20,38.99,0.1,1
397,5,0,0.0,53,0,4,0.0,0.0,0
398,1,0,0.0,66,1,8,0.0,0.0,0
399,2,0,0.0,43,3,4,0.0,0.0,1
400,6,0,0.0,40,0,4,0.0,0.0,0
402,2,0,0.0,29,0,6,0.0,0.0,0
403,11,0,0.0,20,0,3,0.0,0.0,0
404,7,0,0.0,6,0,1,0.0,0.0,0
405,4,1,725.99,68,2,9,725.99,0.1111,0
406,3,1,69.98,35,1,5,69.98,0.2,0
407,7,0,0.0,55,0,7,0.0,0.0,0
408,10,0,0.0,16,1,4,0.0,0.0,0
409,20,2,141.95,188,15,40,70.97,0.05,1
410,4,0,0.0,26,2,5,0.0,0.0,0
411,0,0,0.0,1,0,1,0.0,0.0,0
412,9,0,0.0,13,1,2,0.0,0.0,0
414,5,0,0.0,3,0,1,0.0,0.0,0
415,6,0,0.0,6,0,2,0.0,0.0,0
416,22,0,0.0,6,0,1,0.0,0.0,0
417,0,0,0.0,90,2,17,0.0,0.0,1
419,1,0,0.0,42,2,6,0.0,0.0,0
420,7,0,0.0,7,0,2,0.0,0.0,0
421,0,1,10.99,41,1,9,10.99,0.1111,0
424,9,0,0.0,24,1,4,0.0,0.0,0
425,3,0,0.0,83,1,11,0.0,0.0,0
426,2,0,0.0,6,0,1,0.0,0.0,0
427,0,0,0.0,14,0,1,0.0,0.0,0
428,13,0,0.0,4,1,1,0.0,0.0,0
430,3,0,0.0,16,0,3,0.0,0.0,0
433,2,0,0.0,14,1,4,0.0,0.0,0
434,5,0,0.0,45,4,6,0.0,0.0,0
435,2,0,0.0,1,0,1,0.0,0.0,0
436,0,0,0.0,8,0,3,0.0,0.0,0
437,9,0,0.0,23,0,4,0.0,0.0,0
438,8,0,0.0,3,0,1,0.0,0.0,0
439,0,0,0.0,97,2,14,0.0,0.0,0
440,14,0,0.0,3,0,1,0.0,0.0,0
441,14,0,0.0,14,0,1,0.0,0.0,0
444,7,0,0.0,40,0,7,0.0,0.0,0
445,20,0,0.0,1,0,1,0.0,0.0,0
446,10,0,0.0,11,0,2,0.0,0.0,1
447,22,1,34.99,50,1,7,34.99,0.1429,0
448,14,0,0.0,6,0,3,0.0,0.0,0
449,4,2,177.97,179,8,29,88.98,0.069,0
450,6,0,0.0,36,2,3,0.0,0.0,0
453,13,0,0.0,3,0,2,0.0,0.0,0
454,2,0,0.0,16,1,6,0.0,0.0,0
455,0,0,0.0,63,1,8,0.0,0.0,0
456,4,1,92.99,27,1,5,92.99,0.2,0
458,8,0,0.0,15,0,4,0.0,0.0,0
459,1,0,0.0,43,3,7,0.0,0.0,0
460,1,0,0.0,24,0,7,0.0,0.0,0
461,4,2,345.98,75,5,14,172.99,0.1429,0
464,14,1,15.99,45,4,12,15.99,0.0833,0
465,7,0,0.0,14,1,4,0.0,0.0,0
466,11,0,0.0,4,0,1,0.0,0.0,0
467,12,0,0.0,6,0,3,0.0,0.0,0
468,7,1,108.97,50,2,5,108.97,0.2,0
469,2,0,0.0,7,0,3,0.0,0.0,0
470,7,0,0.0,6,1,2,0.0,0.0,0
471,0,0,0.0,39,0,6,0.0,0.0,0
472,0,0,0.0,1,0,1,0.0,0.0,0
473,20,0,0.0,6,0,2,0.0,0.0,0
474,0,0,0.0,19,0,5,0.0,0.0,0
475,13,0,0.0,3,0,1,0.0,0.0,0
476,3,4,478.92,89,7,10,119.73,0.4,0
477,2,2,235.98,66,5,13,117.99,0.1538,0
478,1,0,0.0,21,0,6,0.0,0.0,0
479,7,0,0.0,17,0,5,0.0,0.0,0
481,20,0,0.0,2,0,1,0.0,0.0,0
482,19,0,0.0,8,0,2,0.0,0.0,0
483,13,1,30.99,64,3,14,30.99,0.0714,0
484,21,0,0.0,3,1,1,0.0,0.0,0
485,7,0,0.0,10,0,1,0.0,0.0,0
486,19,3,81.08,65,4,12,27.03,0.25,0
488,2,0,0.0,39,1,6,0.0,0.0,1
489,6,0,0.0,8,0,2,0.0,0.0,0
490,17,0,0.0,2,0,1,0.0,0.0,0
491,1,0,0.0,14,2,3,0.0,0.0,0
492,6,0,0.0,1,0,1,0.0,0.0,0
493,7,0,0.0,29,0,5,0.0,0.0,0
494,0,0,0.0,12,1,2,0.0,0.0,0
495,1,0,0.0,9,0,3,0.0,0.0,0
496,11,0,0.0,4,0,1,0.0,0.0,0
498,12,0,0.0,9,0,1,0.0,0.0,0
499,1,0,0.0,9,0,3,0.0,0.0,0
500,6,0,0.0,39,1,5,0.0,0.0,0
503,6,0,0.0,20,0,5,0.0,0.0,0
504,0,0,0.0,48,0,8,0.0,0.0,0
505,0,0,0.0,30,3,5,0.0,0.0,0
506,6,0,0.0,6,0,1,0.0,0.0,0
507,0,0,0.0,89,1,9,0.0,0.0,0
509,9,0,0.0,10,1,3,0.0,0.0,0
510,22,0,0.0,6,0,1,0.0,0.0,0
512,3,0,0.0,58,1,7,0.0,0.0,0
513,3,0,0.0,3,0,1,0.0,0.0,0
514,1,0,0.0,39,0,6,0.0,0.0,0
515,11,3,1378.94,113,6,26,459.65,0.1154,1
516,18,1,9.49,42,2,5,9.49,0.2,0
517,3,3,338.96,93,4,13,112.99,0.2308,0
518,0,0,0.0,25,1,4,0.0,0.0,0
519,3,3,221.95,68,6,11,73.98,0.2727,1
520,9,0,0.0,16,0,3,0.0,0.0,0
521,21,0,0.0,1,0,1,0.0,0.0,0
522,16,1,23.99,67,4,9,23.99,0.1111,0
523,1,0,0.0,6,0,1,0.0,0.0,0
525,12,0,0.0,20,2,4,0.0,0.0,1
526,12,0,0.0,10,0,1,0.0,0.0,0
527,13,0,0.0,1,0,1,0.0,0.0,0
528,20,0,0.0,7,0,2,0.0,0.0,0
530,0,0,0.0,21,0,7,0.0,0.0,0
531,19,1,150.1,52,5,4,150.1,0.25,0
532,2,0,0.0,68,0,10,0.0,0.0,0
533,10,0,0.0,14,0,3,0.0,0.0,0
535,14,0,0.0,9,0,2,0.0,0.0,0
536,2,1,16.98,13,1,3,16.98,0.3333,0
538,1,0,0.0,29,2,6,0.0,0.0,0
539,18,1,25.36,53,3,10,25.36,0.1,0
540,0,0,0.0,36,0,5,0.0,0.0,0
541,14,0,0.0,5,0,1,0.0,0.0,0
542,2,0,0.0,17,0,4,0.0,0.0,0
543,11,2,76.96,15,2,2,38.48,1.0,0
544,1,0,0.0,117,2,13,0.0,0.0,1
545,14,0,0.0,6,0,3,0.0,0.0,0
546,9,0,0.0,8,1,2,0.0,0.0,0
547,6,1,96.98,107,3,16,96.98,0.0625,0
549,15,0,0.0,8,0,2,0.0,0.0,0
550,14,0,0.0,14,0,3,0.0,0.0,0
551,7,0,0.0,5,0,3,0.0,0.0,0
552,6,0,0.0,6,0,3,0.0,0.0,0
553,0,0,0.0,109,3,15,0.0,0.0,0
554,7,0,0.0,5,0,1,0.0,0.0,0
555,17,1,158.99,19,3,4,158.99,0.25,0
556,23,0,0.0,6,0,1,0.0,0.0,0
557,0,0,0.0,6,0,1,0.0,0.0,0
559,6,0,0.0,3,0,1,0.0,0.0,0
560,1,0,0.0,2,0,1,0.0,0.0,0
561,13,0,0.0,4,0,1,0.0,0.0,0
562,5,0,0.0,20,0,4,0.0,0.0,0
563,16,0,0.0,1,0,1,0.0,0.0,0
564,5,2,72.48,47,4,8,36.24,0.25,0
566,15,0,0.0,11,0,1,0.0,0.0,0
567,14,0,0.0,10,0,2,0.0,0.0,0
568,22,0,0.0,9,1,2,0.0,0.0,0
570,0,0,0.0,5,0,2,0.0,0.0,0
571,5,0,0.0,13,1,2,0.0,0.0,1
572,3,0,0.0,26,1,3,0.0,0.0,0
573,0,0,0.0,15,0,4,0.0,0.0,0
574,1,0,0.0,23,0,8,0.0,0.0,0
575,10,0,0.0,15,0,3,0.0,0.0,0
576,7,0,0.0,4,0,1,0.0,0.0,0
577,2,0,0.0,104,3,11,0.0,0.0,0
579,8,0,0.0,9,1,1,0.0,0.0,0
580,0,0,0.0,7,0,4,0.0,0.0,0
581,1,0,0.0,53,0,9,0.0,0.0,0
582,2,0,0.0,2,0,2,0.0,0.0,0
583,4,0,0.0,59,1,7,0.0,0.0,0
584,10,0,0.0,22,1,3,0.0,0.0,0
585,3,0,0.0,32,0,3,0.0,0.0,1
586,7,0,0.0,8,1,3,0.0,0.0,0
587,20,0,0.0,2,0,1,0.0,0.0,0
588,11,0,0.0,4,0,1,0.0,0.0,0
592,22,0,0.0,11,2,3,0.0,0.0,0
593,8,0,0.0,37,1,6,0.0,0.0,0
595,1,2,47.97,28,2,4,23.98,0.5,0
596,12,0,0.0,14,0,1,0.0,0.0,0
597,5,0,0.0,7,0,1,0.0,0.0,0
598,2,0,0.0,6,0,2,0.0,0.0,0
599,0,0,0.0,19,1,3,0.0,0.0,1
600,21,1,110.99,111,4,21,110.99,0.0476,0
601,16,2,230.97,52,3,10,115.48,0.2,1
602,1,2,268.98,83,4,15,134.49,0.1333,0
603,3,0,0.0,5,0,1,0.0,0.0,0
605,7,1,241.99,46,2,8,241.99,0.125,0
606,4,0,0.0,2,0,1,0.0,0.0,0
607,12,1,25.99,30,1,3,25.99,0.3333,0
608,10,0,0.0,13,2,2,0.0,0.0,0
610,1,0,0.0,89,1,13,0.0,0.0,0
611,12,0,0.0,4,0,1,0.0,0.0,0
612,5,0,0.0,7,0,3,0.0,0.0,0
613,16,0,0.0,12,0,2,0.0,0.0,0
614,15,1,165.99,23,2,5,165.99,0.2,0
615,3,0,0.0,41,0,7,0.0,0.0,0
617,1,0,0.0,50,1,8,0.0,0.0,0
618,2,0,0.0,8,1,3,0.0,0.0,0
619,13,1,204.99,7,1,1,204.99,1.0,0
620,18,2,326.96,96,8,20,163.48,0.1,1
622,19,0,0.0,5,0,1,0.0,0.0,0
623,7,0,0.0,3,0,1,0.0,0.0,0
624,21,1,23.99,73,3,9,23.99,0.1111,0
625,21,1,14.99,50,3,6,14.99,0.1667,0
626,3,0,0.0,42,0,6,0.0,0.0,0
627,7,0,0.0,4,0,1,0.0,0.0,0
629,1,0,0.0,81,3,11,0.0,0.0,1
631,19,1,8.49,83,3,10,8.49,0.1,0
634,1,1,59.99,66,3,10,59.99,0.1,0
635,9,0,0.0,72,1,8,0.0,0.0,0
636,13,1,477.97,47,4,7,477.97,0.1429,0
637,16,3,184.02,57,4,8,61.34,0.375,1
638,8,1,7.49,119,4,18,7.49,0.0556,1
640,6,0,0.0,5,0,2,0.0,0.0,0
641,10,0,0.0,6,0,1,0.0,0.0,0
642,10,0,0.0,1,0,1,0.0,0.0,0
643,0,0,0.0,10,1,4,0.0,0.0,0
644,0,0,0.0,61,0,9,0.0,0.0,0
645,9,0,0.0,14,1,3,0.0,0.0,0
646,20,0,0.0,7,1,2,0.0,0.0,0
647,1,0,0.0,4,0,1,0.0,0.0,0
648,0,0,0.0,7,0,3,0.0,0.0,0
650,1,0,0.0,15,0,6,0.0,0.0,0
651,1,0,0.0,49,0,6,0.0,0.0,0
653,3,0,0.0,4,0,1,0.0,0.0,0
655,13,0,0.0,3,0,1,0.0,0.0,0
656,8,1,7.49,54,3,9,7.49,0.1111,0
657,17,0,0.0,3,0,1,0.0,0.0,0
658,21,1,317.98,93,5,16,317.98,0.0625,1
659,12,0,0.0,2,0,1,0.0,0.0,0
660,4,0,0.0,16,0,2,0.0,0.0,0
661,2,0,0.0,12,2,3,0.0,0.0,0
662,4,0,0.0,18,2,3,0.0,0.0,0
663,1,0,0.0,2,0,2,0.0,0.0,0
664,15,1,265.99,68,3,9,265.99,0.1111,0
665,14,0,0.0,5,0,1,0.0,0.0,0
666,12,0,0.0,12,0,3,0.0,0.0,0
667,1,0,0.0,27,0,5,0.0,0.0,0
668,6,0,0.0,51,2,7,0.0,0.0,0
669,20,0,0.0,3,1,2,0.0,0.0,0
670,10,0,0.0,4,0,2,0.0,0.0,0
671,0,0,0.0,15,0,2,0.0,0.0,0
672,2,0,0.0,28,0,3,0.0,0.0,0
674,17,0,0.0,5,0,1,0.0,0.0,0
675,1,0,0.0,6,0,3,0.0,0.0,0
677,16,0,0.0,16,0,4,0.0,0.0,0
678,15,0,0.0,6,0,3,0.0,0.0,0
679,7,0,0.0,37,0,5,0.0,0.0,0
680,12,0,0.0,4,0,3,0.0,0.0,0
681,4,0,0.0,10,0,2,0.0,0.0,0
682,20,1,116.55,90,3,9,116.55,0.1111,0
683,6,0,0.0,5,0,1,0.0,0.0,0
684,5,0,0.0,8,0,2,0.0,0.0,0
685,6,0,0.0,14,1,1,0.0,0.0,0
687,6,0,0.0,3,0,1,0.0,0.0,0
688,8,1,24.99,30,1,5,24.99,0.2,0
689,11,0,0.0,4,1,1,0.0,0.0,0
690,17,0,0.0,4,0,1,0.0,0.0,0
691,20,0,0.0,3,0,1,0.0,0.0,0
692,22,1,16.98,74,3,16,16.98,0.0625,0
694,2,0,0.0,2,0,1,0.0,0.0,0
695,14,0,0.0,9,1,2,0.0,0.0,0
696,7,0,0.0,5,0,1,0.0,0.0,0
697,18,2,108.06,168,3,22,54.03,0.0909,0
699,0,4,161.88,131,9,21,40.47,0.1905,0
700,8,0,0.0,30,0,5,0.0,0.0,0
701,3,0,0.0,10,0,4,0.0,0.0,0
702,19,1,9.49,71,3,11,9.49,0.0909,0
703,19,0,0.0,2,0,1,0.0,0.0,0
704,0,0,0.0,15,2,6,0.0,0.0,0
705,2,0,0.0,7,1,1,0.0,0.0,0
706,4,1,76.99,73,3,19,76.99,0.0526,1
707,1,0,0.0,1,0,1,0.0,0.0,0
709,11,0,0.0,40,2,3,0.0,0.0,0
710,0,0,0.0,10,1,4,0.0,0.0,0
711,4,0,0.0,4,0,2,0.0,0.0,0
712,7,0,0.0,14,0,3,0.0,0.0,0
713,16,1,204.99,5,1,1,204.99,1.0,0
714,9,0,0.0,39,0,6,0.0,0.0,0
716,21,1,23.99,67,4,8,23.99,0.125,0
717,19,0,0.0,14,1,1,0.0,0.0,0
718,11,0,0.0,10,1,2,0.0,0.0,0
719,0,1,204.99,14,1,2,204.99,0.5,0
721,6,0,0.0,5,0,2,0.0,0.0,0
722,9,0,0.0,11,0,2,0.0,0.0,0
723,5,0,0.0,10,0,3,0.0,0.0,0
724,0,0,0.0,87,1,16,0.0,0.0,1
725,6,0,0.0,31,1,5,0.0,0.0,0
726,1,0,0.0,17,1,3,0.0,0.0,0
727,5,0,0.0,7,1,3,0.0,0.0,0
728,0,1,10.99,9,1,2,10.99,0.5,0
729,15,0,0.0,14,1,2,0.0,0.0,0
730,10,1,179.98,58,3,6,179.98,0.1667,0
731,10,0,0.0,45,1,5,0.0,0.0,0
732,13,2,471.05,68,6,8,235.52,0.25,0
734,15,0,0.0,14,0,3,0.0,0.0,0
735,12,0,0.0,12,0,3,0.0,0.0,0
736,1,0,0.0,15,0,3,0.0,0.0,0
737,4,0,0.0,11,0,1,0.0,0.0,0
739,15,1,34.99,81,3,13,34.99,0.0769,0
740,2,0,0.0,80,1,8,0.0,0.0,0
741,19,0,0.0,2,0,1,0.0,0.0,0
743,18,0,0.0,34,4,3,0.0,0.0,0
744,7,0,0.0,24,1,4,0.0,0.0,0
745,14,2,51.98,38,3,11,25.99,0.1818,0
746,20,0,0.0,6,0,2,0.0,0.0,0
747,10,1,30.99,88,2,13,30.99,0.0769,0
748,15,1,59.99,22,1,1,59.99,1.0,0
750,0,0,0.0,28,0,6,0.0,0.0,0
751,13,0,0.0,15,0,3,0.0,0.0,0
754,0,0,0.0,19,1,5,0.0,0.0,0
755,22,1,61.99,69,4,11,61.99,0.0909,0
758,9,4,1040.34,154,10,31,260.08,0.129,0
759,12,0,0.0,10,0,2,0.0,0.0,0
760,20,1,9.15,9,1,1,9.15,1.0,0
761,13,0,0.0,10,0,2,0.0,0.0,0
762,18,2,830.97,97,6,24,415.48,0.0833,1
764,3,2,99.95,129,7,12,49.98,0.1667,0
766,7,0,0.0,31,0,5,0.0,0.0,1
767,3,1,109.99,38,3,5,109.99,0.2,0
768,1,0,0.0,62,0,10,0.0,0.0,0
769,18,0,0.0,3,0,1,0.0,0.0,0
770,8,1,46.99,53,2,11,46.99,0.0909,0
772,22,1,389.98,53,3,6,389.98,0.1667,0
773,3,1,30.99,43,4,6,30.99,0.1667,1
774,2,0,0.0,10,0,1,0.0,0.0,0
775,6,1,23.99,12,1,2,23.99,0.5,0
776,6,0,0.0,10,0,2,0.0,0.0,0
777,4,0,0.0,93,2,11,0.0,0.0,0
778,16,0,0.0,23,0,2,0.0,0.0,0
779,23,0,0.0,1,0,1,0.0,0.0,0
780,6,0,0.0,2,0,1,0.0,0.0,0
781,20,0,0.0,5,0,1,0.0,0.0,0
782,7,0,0.0,42,0,4,0.0,0.0,0
783,14,0,0.0,12,0,2,0.0,0.0,0
784,20,1,37.99,20,1,4,37.99,0.25,0
785,21,0,0.0,8,0,1,0.0,0.0,0
786,20,0,0.0,3,1,1,0.0,0.0,0
787,0,0,0.0,19,0,1,0.0,0.0,1
788,11,0,0.0,5,1,2,0.0,0.0,0
789,16,0,0.0,9,0,3,0.0,0.0,0
790,2,0,0.0,2,0,2,0.0,0.0,0
792,11,0,0.0,29,3,4,0.0,0.0,0
793,5,2,195.96,62,3,5,97.98,0.4,0
794,5,0,0.0,28,2,9,0.0,0.0,0
795,5,0,0.0,14,0,5,0.0,0.0,1
796,2,0,0.0,108,1,12,0.0,0.0,0
797,15,0,0.0,5,0,2,0.0,0.0,0
798,20,0,0.0,6,0,1,0.0,0.0,0
799,8,2,90.98,124,4,20,45.49,0.1,0
801,5,0,0.0,12,0,4,0.0,0.0,0
802,6,0,0.0,18,0,2,0.0,0.0,0
803,4,0,0.0,6,0,2,0.0,0.0,0
804,9,0,0.0,17,0,6,0.0,0.0,0
805,7,0,0.0,17,0,3,0.0,0.0,0
806,12,2,178.98,122,5,20,89.49,0.1,1
807,7,0,0.0,19,1,5,0.0,0.0,0
808,1,0,0.0,15,2,2,0.0,0.0,0
809,16,0,0.0,28,0,4,0.0,0.0,0
810,8,0,0.0,4,0,1,0.0,0.0,0
811,14,0,0.0,29,0,3,0.0,0.0,0
812,0,0,0.0,109,0,15,0.0,0.0,0
813,21,0,0.0,4,0,2,0.0,0.0,0
815,8,0,0.0,1,0,1,0.0,0.0,0
816,10,2,147.97,45,4,11,73.98,0.1818,0
818,4,0,0.0,33,1,3,0.0,0.0,1
819,3,0,0.0,11,0,2,0.0,0.0,0
820,19,1,126.27,113,7,14,126.27,0.0714,0
821,22,1,130.99,52,4,9,130.99,0.1111,0
822,6,2,361.98,37,4,8,180.99,0.25,0
823,9,1,34.99,43,1,6,34.99,0.1667,0
824,1,0,0.0,20,1,6,0.0,0.0,0
825,11,0,0.0,5,0,1,0.0,0.0,0
826,6,0,0.0,9,0,1,0.0,0.0,0
827,6,0,0.0,2,0,1,0.0,0.0,0
829,11,1,8.49,6,1,1,8.49,1.0,0
830,1,0,0.0,6,0,2,0.0,0.0,0
831,5,0,0.0,10,1,2,0.0,0.0,0
832,4,0,0.0,7,0,1,0.0,0.0,0
834,2,0,0.0,76,0,11,0.0,0.0,1
835,0,0,0.0,178,1,20,0.0,0.0,0
838,6,0,0.0,40,0,11,0.0,0.0,0
840,9,0,0.0,12,0,1,0.0,0.0,0
841,8,0,0.0,22,0,3,0.0,0.0,0
842,12,0,0.0,5,0,3,0.0,0.0,0
844,13,0,0.0,1,0,1,0.0,0.0,0
845,1,0,0.0,19,0,8,0.0,0.0,0
846,6,0,0.0,11,0,2,0.0,0.0,0
847,3,0,0.0,60,1,6,0.0,0.0,0
848,5,0,0.0,4,0,2,0.0,0.0,0
850,21,0,0.0,3,0,1,0.0,0.0,0
852,15,0,0.0,21,0,2,0.0,0.0,0
853,7,0,0.0,68,0,9,0.0,0.0,0
854,23,0,0.0,2,0,1,0.0,0.0,0
855,21,0,0.0,2,0,1,0.0,0.0,0
856,3,0,0.0,67,0,8,0.0,0.0,0
857,0,0,0.0,88,1,10,0.0,0.0,0
858,21,0,0.0,5,0,2,0.0,0.0,0
859,5,0,0.0,24,0,3,0.0,0.0,0
860,10,0,0.0,5,0,1,0.0,0.0,0
862,11,0,0.0,10,2,3,0.0,0.0,0
863,2,0,0.0,12,1,4,0.0,0.0,0
864,0,0,0.0,5,0,2,0.0,0.0,0
865,4,0,0.0,38,0,8,0.0,0.0,0
866,3,0,0.0,9,0,3,0.0,0.0,0
867,5,0,0.0,6,0,2,0.0,0.0,0
868,3,0,0.0,37,1,5,0.0,0.0,0
869,18,0,0.0,9,0,2,0.0,0.0,0
870,23,1,76.99,74,3,10,76.99,0.1,0
873,14,0,0.0,4,0,1,0.0,0.0,0
874,3,0,0.0,9,0,3,0.0,0.0,0
875,1,0,0.0,14,0,3,0.0,0.0,0
876,5,0,0.0,12,0,3,0.0,0.0,0
877,14,0,0.0,14,0,3,0.0,0.0,0
878,0,0,0.0,66,0,6,0.0,0.0,0
879,4,0,0.0,8,0,2,0.0,0.0,0
880,3,0,0.0,19,0,5,0.0,0.0,0
881,10,0,0.0,5,1,3,0.0,0.0,0
883,0,0,0.0,2,0,1,0.0,0.0,0
885,0,0,0.0,11,0,2,0.0,0.0,0
886,6,0,0.0,1,0,1,0.0,0.0,0
887,2,0,0.0,11,0,3,0.0,0.0,0
888,3,0,0.0,14,1,4,0.0,0.0,0
889,0,0,0.0,18,0,5,0.0,0.0,0
890,12,0,0.0,28,0,2,0.0,0.0,0
891,20,1,158.99,71,4,13,158.99,0.0769,0
892,8,0,0.0,6,0,1,0.0,0.0,0
893,22,1,67.99,116,5,18,67.99,0.0556,1
895,0,1,76.99,53,3,8,76.99,0.125,0
896,10,1,110.99,62,2,14,110.99,0.0714,1
897,6,0,0.0,12,0,2,0.0,0.0,0
898,21,0,0.0,4,0,1,0.0,0.0,0
899,0,0,0.0,57,0,10,0.0,0.0,0
900,2,0,0.0,62,1,5,0.0,0.0,0
901,20,1,44.55,19,1,2,44.55,0.5,0
902,2,0,0.0,9,0,3,0.0,0.0,0
903,16,1,76.99,51,1,7,76.99,0.1429,1
904,9,0,0.0,26,1,3,0.0,0.0,0
905,10,0,0.0,11,1,1,0.0,0.0,0
906,0,0,0.0,1,0,1,0.0,0.0,0
908,2,0,0.0,23,1,5,0.0,0.0,1
910,18,1,65.99,58,4,9,65.99,0.1111,0
911,7,1,16.47,6,1,1,16.47,1.0,0
912,0,0,0.0,100,0,12,0.0,0.0,1
913,4,2,63.98,122,2,15,31.99,0.1333,0
914,15,1,64.99,9,1,2,64.99,0.5,0
915,21,1,281.26,32,1,3,281.26,0.3333,0
916,6,0,0.0,41,1,5,0.0,0.0,0
917,4,0,0.0,12,0,1,0.0,0.0,0
918,1,0,0.0,59,0,5,0.0,0.0,0
919,7,1,181.99,12,1,1,181.99,1.0,0
920,2,0,0.0,8,0,2,0.0,0.0,0
921,17,0,0.0,7,0,1,0.0,0.0,0
922,1,0,0.0,8,0,2,0.0,0.0,0
923,0,0,0.0,22,0,4,0.0,0.0,0
924,19,1,54.99,66,2,10,54.99,0.1,0
925,20,1,8.92,6,1,1,8.92,1.0,0
926,4,0,0.0,17,0,5,0.0,0.0,0
927,3,3,388.97,94,4,15,129.66,0.2,0
928,3,0,0.0,7,0,2,0.0,0.0,0
929,20,0,0.0,4,0,1,0.0,0.0,0
930,6,0,0.0,6,1,1,0.0,0.0,0
932,1,0,0.0,51,4,4,0.0,0.0,0
933,2,0,0.0,31,1,4,0.0,0.0,0
934,5,0,0.0,60,1,7,0.0,0.0,0
935,11,0,0.0,39,1,5,0.0,0.0,0
937,12,0,0.0,42,1,2,0.0,0.0,0
938,0,0,0.0,22,0,2,0.0,0.0,1
940,1,0,0.0,88,0,11,0.0,0.0,0
941,2,0,0.0,18,0,4,0.0,0.0,0
942,6,0,0.0,13,0,2,0.0,0.0,0
943,5,0,0.0,4,0,2,0.0,0.0,0
945,16,1,103.98,26,1,4,103.98,0.25,0
946,6,0,0.0,6,0,1,0.0,0.0,0
947,12,2,170.98,52,3,5,85.49,0.4,0
948,0,0,0.0,79,0,8,0.0,0.0,0
949,3,0,0.0,35,0,7,0.0,0.0,0
950,11,0,0.0,1,0,1,0.0,0.0,0
951,0,0,0.0,5,0,1,0.0,0.0,0
952,14,0,0.0,11,1,1,0.0,0.0,0
953,14,0,0.0,10,0,1,0.0,0.0,0
954,2,0,0.0,85,2,10,0.0,0.0,0
955,13,1,17.99,64,2,8,17.99,0.125,0
956,9,2,53.87,37,4,4,26.94,0.5,0
958,0,0,0.0,45,0,5,0.0,0.0,0
960,11,1,165.99,50,4,10,165.99,0.1,0
961,2,0,0.0,4,0,2,0.0,0.0,1
962,10,3,1166.96,150,6,21,388.99,0.1429,1
963,0,0,0.0,10,0,3,0.0,0.0,0
964,3,0,0.0,32,0,6,0.0,0.0,0
965,9,0,0.0,2,0,1,0.0,0.0,0
966,21,0,0.0,2,0,1,0.0,0.0,0
967,21,1,65.99,37,2,12,65.99,0.0833,0
969,6,0,0.0,53,0,9,0.0,0.0,0
970,18,1,201.98,95,4,12,201.98,0.0833,0
971,0,0,0.0,4,1,1,0.0,0.0,0
972,20,1,763.99,18,2,3,763.99,0.3333,0
973,3,0,0.0,14,0,4,0.0,0.0,0
974,10,1,59.97,132,4,16,59.97,0.0625,0
975,1,0,0.0,29,0,6,0.0,0.0,0
976,4,0,0.0,13,0,1,0.0,0.0,0
977,5,0,0.0,6,0,1,0.0,0.0,0
978,8,0,0.0,64,2,7,0.0,0.0,0
979,1,0,0.0,20,1,4,0.0,0.0,1
980,3,0,0.0,29,1,4,0.0,0.0,0
981,20,0,0.0,6,0,1,0.0,0.0,0
982,0,0,0.0,16,1,3,0.0,0.0,0
983,3,0,0.0,17,0,4,0.0,0.0,0
984,1,0,0.0,6,0,1,0.0,0.0,0
987,9,0,0.0,38,1,3,0.0,0.0,0
988,0,0,0.0,8,0,2,0.0,0.0,0
990,5,0,0.0,4,0,1,0.0,0.0,0
991,0,0,0.0,3,0,1,0.0,0.0,0
992,8,0,0.0,3,0,1,0.0,0.0,0
994,8,0,0.0,2,0,1,0.0,0.0,0
995,11,0,0.0,6,0,1,0.0,0.0,0
996,1,0,0.0,26,1,5,0.0,0.0,0
997,4,0,0.0,7,0,2,0.0,0.0,0
998,7,0,0.0,5,0,1,0.0,0.0,0
999,3,0,0.0,3,0,2,0.0,0.0,0
1000,12,1,86.48,14,2,3,86.48,0.3333,0
1001,4,0,0.0,5,0,1,0.0,0.0,0
1002,18,2,608.97,155,4,29,304.48,0.069,1
1003,6,0,0.0,10,1,2,0.0,0.0,0
1005,11,0,0.0,61,1,5,0.0,0.0,0
1006,11,0,0.0,1,0,1,0.0,0.0,0
1007,3,1,48.99,8,2,2,48.99,0.5,0
1008,9,1,37.99,39,1,7,37.99,0.1429,0
1009,6,2,246.97,149,9,17,123.48,0.1176,1
1010,5,0,0.0,4,0,2,0.0,0.0,0
1011,0,0,0.0,41,0,7,0.0,0.0,0
1012,1,0,0.0,69,2,7,0.0,0.0,0
1014,7,0,0.0,23,0,4,0.0,0.0,0
1015,0,0,0.0,87,1,11,0.0,0.0,0
1016,3,0,0.0,12,0,1,0.0,0.0,0
1017,9,0,0.0,4,1,2,0.0,0.0,0
1018,5,5,361.4,156,9,20,72.28,0.25,0
1019,6,0,0.0,7,1,2,0.0,0.0,0
1020,16,1,89.99,32,1,4,89.99,0.25,0
1022,11,1,16.98,65,1,13,16.98,0.0769,0
1023,2,0,0.0,7,0,3,0.0,0.0,0
1024,22,0,0.0,6,0,1,0.0,0.0,0
1025,20,0,0.0,1,0,1,0.0,0.0,0
1026,0,0,0.0,10,0,2,0.0,0.0,0
1027,2,0,0.0,10,0,1,0.0,0.0,0
1028,2,0,0.0,25,0,4,0.0,0.0,0
1029,0,0,0.0,26,2,6,0.0,0.0,0
1030,23,1,176.99,58,2,10,176.99,0.1,1
1031,13,0,0.0,7,0,1,0.0,0.0,0
1032,4,0,0.0,1,0,1,0.0,0.0,0
1033,18,2,63.8,41,5,6,31.9,0.3333,0
1034,2,0,0.0,12,0,2,0.0,0.0,0
1036,10,0,0.0,7,0,2,0.0,0.0,0
1037,12,0,0.0,6,0,2,0.0,0.0,0
1038,1,0,0.0,38,0,8,0.0,0.0,0
1039,5,0,0.0,29,1,4,0.0,0.0,0
1040,7,0,0.0,7,0,1,0.0,0.0,0
1041,7,0,0.0,4,0,1,0.0,0.0,0
1042,4,0,0.0,10,1,3,0.0,0.0,0
1043,9,0,0.0,22,0,3,0.0,0.0,0
1044,22,1,78.95,87,5,11,78.95,0.0909,0
1045,19,0,0.0,5,0,2,0.0,0.0,0
1046,10,0,0.0,6,0,2,0.0,0.0,0
1047,12,0,0.0,5,0,1,0.0,0.0,0
1048,14,0,0.0,12,1,5,0.0,0.0,0
1049,2,0,0.0,22,1,4,0.0,0.0,0
1050,1,0,0.0,39,0,5,0.0,0.0,0
1051,8,0,0.0,4,0,1,0.0,0.0,0
1052,5,0,0.0,27,4,5,0.0,0.0,0
1053,6,0,0.0,9,0,1,0.0,0.0,0
1054,0,0,0.0,5,0,1,0.0,0.0,0
1055,8,0,0.0,2,0,1,0.0,0.0,0
1056,0,0,0.0,1,0,1,0.0,0.0,0
1057,1,0,0.0,40,1,5,0.0,0.0,0
1058,18,0,0.0,6,0,1,0.0,0.0,0
1059,16,0,0.0,4,0,2,0.0,0.0,0
1060,12,0,0.0,8,0,1,0.0,0.0,0
1061,9,0,0.0,40,0,6,0.0,0.0,1
1062,6,0,0.0,15,0,2,0.0,0.0,0
1063,22,2,138.81,61,3,11,69.4,0.1818,1
1064,21,0,0.0,3,1,1,0.0,0.0,0
1065,0,0,0.0,4,0,1,0.0,0.0,0
1066,14,1,100.99,184,3,17,100.99,0.0588,0
1067,5,3,1307.91,188,10,24,435.97,0.125,1
1068,21,0,0.0,2,0,1,0.0,0.0,0
1069,0,0,0.0,26,0,7,0.0,0.0,0
1070,2,0,0.0,5,0,2,0.0,0.0,0
1071,3,0,0.0,29,1,4,0.0,0.0,0
1072,1,0,0.0,4,0,1,0.0,0.0,0
1073,1,0,0.0,24,1,4,0.0,0.0,0
1075,3,0,0.0,85,1,13,0.0,0.0,0
1076,1,0,0.0,49,0,5,0.0,0.0,0
1077,7,1,32.99,3,1,1,32.99,1.0,0
1078,0,0,0.0,3,1,1,0.0,0.0,0
1079,6,0,0.0,1,0,1,0.0,0.0,0
1080,1,0,0.0,95,2,11,0.0,0.0,0
1082,4,1,22.98,30,2,5,22.98,0.2,0
1086,5,0,0.0,16,0,3,0.0,0.0,0
1087,21,0,0.0,2,0,1,0.0,0.0,0
1088,0,0,0.0,2,0,1,0.0,0.0,0
1089,10,0,0.0,4,0,3,0.0,0.0,0
1090,12,0,0.0,3,0,1,0.0,0.0,0
1091,2,0,0.0,24,1,7,0.0,0.0,0
1092,12,0,0.0,23,1,3,0.0,0.0,0
1093,3,0,0.0,19,1,2,0.0,0.0,0
1095,0,0,0.0,2,0,1,0.0,0.0,0
1096,2,0,0.0,8,0,1,0.0,0.0,0
1097,6,1,32.99,36,4,8,32.99,0.125,0
1098,0,0,0.0,6,0,2,0.0,0.0,0
1099,0,0,0.0,23,0,5,0.0,0.0,0
1100,9,0,0.0,1,0,1,0.0,0.0,0
1101,3,0,0.0,12,0,2,0.0,0.0,0
1103,10,0,0.0,13,0,3,0.0,0.0,0
1104,16,0,0.0,15,2,2,0.0,0.0,0
1105,12,0,0.0,15,0,5,0.0,0.0,0
1107,0,0,0.0,9,0,1,0.0,0.0,0
1108,3,0,0.0,24,2,1,0.0,0.0,0
1109,8,0,0.0,11,0,2,0.0,0.0,0
1110,9,0,0.0,9,0,1,0.0,0.0,0
1111,11,0,0.0,4,0,1,0.0,0.0,0
1112,21,1,61.99,62,3,7,61.99,0.1429,0
1113,14,0,0.0,16,0,4,0.0,0.0,0
1114,2,0,0.0,1,0,1,0.0,0.0,0
1115,6,0,0.0,1,0,1,0.0,0.0,0
1117,5,1,7.49,39,2,7,7.49,0.1429,0
1118,12,0,0.0,16,0,3,0.0,0.0,0
1120,2,0,0.0,12,0,3,0.0,0.0,0
1121,12,2,97.98,57,2,8,48.99,0.25,0
1122,1,0,0.0,5,0,1,0.0,0.0,0
1125,21,1,664.98,43,2,6,664.98,0.1667,0
1126,5,0,0.0,7,1,2,0.0,0.0,0
1127,11,1,76.99,67,1,7,76.99,0.1429,0
1128,0,0,0.0,1,0,1,0.0,0.0,0
1129,16,0,0.0,6,0,2,0.0,0.0,0
1130,18,0,0.0,4,1,2,0.0,0.0,0
1131,3,0,0.0,22,0,4,0.0,0.0,0
1132,3,0,0.0,46,2,6,0.0,0.0,0
1133,19,0,0.0,2,0,1,0.0,0.0,0
1134,3,0,0.0,7,0,1,0.0,0.0,0
1136,17,0,0.0,7,0,1,0.0,0.0,0
1137,0,3,391.96,72,7,16,130.65,0.1875,0
1138,3,0,0.0,13,0,3,0.0,0.0,0
1139,11,0,0.0,2,0,1,0.0,0.0,0
1140,20,0,0.0,3,0,1,0.0,0.0,0
1141,18,1,34.99,27,1,6,34.99,0.1667,0
1143,3,1,36.99,7,1,2,36.99,0.5,0
1144,12,0,0.0,4,0,1,0.0,0.0,0
1145,2,0,0.0,15,1,4,0.0,0.0,0
1148,20,0,0.0,4,0,1,0.0,0.0,0
1149,5,0,0.0,20,2,4,0.0,0.0,0
1150,6,0,0.0,31,1,6,0.0,0.0,0
1151,3,0,0.0,45,0,4,0.0,0.0,0
1153,4,0,0.0,9,0,3,0.0,0.0,0
1155,0,0,0.0,29,1,4,0.0,0.0,0
1156,20,1,10.99,15,1,3,10.99,0.3333,0
1157,2,0,0.0,26,3,4,0.0,0.0,0
1158,10,0,0.0,8,0,3,0.0,0.0,0
1159,11,0,0.0,8,0,3,0.0,0.0,0
1160,1,0,0.0,26,0,7,0.0,0.0,0
1161,11,2,213.26,122,5,16,106.63,0.125,1
1162,13,2,183.98,121,5,15,91.99,0.1333,0
1163,6,0,0.0,34,0,6,0.0,0.0,0
1165,20,1,5.49,21,2,4,5.49,0.25,1
1166,13,0,0.0,10,0,2,0.0,0.0,0
1167,12,0,0.0,1,0,1,0.0,0.0,0
1168,18,0,0.0,1,0,1,0.0,0.0,0
1170,12,0,0.0,3,0,1,0.0,0.0,0
1171,10,0,0.0,2,0,1,0.0,0.0,0
1172,3,0,0.0,30,0,4,0.0,0.0,0
1173,10,0,0.0,6,1,1,0.0,0.0,0
1174,1,0,0.0,35,1,6,0.0,0.0,0
1175,2,4,429.94,58,7,9,107.48,0.4444,1
1176,16,0,0.0,10,0,1,0.0,0.0,0
1177,3,0,0.0,36,1,5,0.0,0.0,0
1178,2,0,0.0,32,1,6,0.0,0.0,0
1179,13,1,241.99,5,1,1,241.99,1.0,0
1181,9,0,0.0,6,0,1,0.0,0.0,0
1182,6,8,2454.41,183,17,26,306.8,0.3077,0
1183,8,0,0.0,4,0,1,0.0,0.0,0
1184,3,2,34.48,41,4,7,17.24,0.2857,0
1185,5,1,84.99,40,2,6,84.99,0.1667,0
1186,4,0,0.0,5,0,1,0.0,0.0,0
1187,0,0,0.0,124,6,22,0.0,0.0,0
1188,0,0,0.0,34,1,3,0.0,0.0,0
1189,3,0,0.0,11,0,3,0.0,0.0,0
1190,6,1,215.97,42,1,7,215.97,0.1429,1
1191,12,0,0.0,8,0,1,0.0,0.0,0
1192,1,0,0.0,4,0,1,0.0,0.0,0
1194,8,0,0.0,10,0,3,0.0,0.0,0
1195,1,0,0.0,23,1,3,0.0,0.0,0
1198,8,0,0.0,11,0,2,0.0,0.0,0
1199,7,0,0.0,5,0,1,0.0,0.0,0
1202,18,0,0.0,4,0,1,0.0,0.0,0
1203,2,0,0.0,16,0,4,0.0,0.0,0
1204,4,0,0.0,13,0,2,0.0,0.0,0
1205,6,0,0.0,4,0,2,0.0,0.0,0
1206,3,0,0.0,94,2,10,0.0,0.0,0
1210,16,0,0.0,4,0,1,0.0,0.0,0
1211,2,0,0.0,2,0,1,0.0,0.0,0
1212,7,0,0.0,57,2,6,0.0,0.0,0
1213,7,1,241.99,20,1,5,241.99,0.2,1
1214,0,0,0.0,43,3,7,0.0,0.0,0
1215,1,0,0.0,1,0,1,0.0,0.0,0
1216,0,0,0.0,2,0,1,0.0,0.0,0
1217,19,0,0.0,3,0,1,0.0,0.0,0
1218,0,0,0.0,34,0,8,0.0,0.0,0
1219,11,0,0.0,12,0,2,0.0,0.0,1
1220,7,0,0.0,10,1,2,0.0,0.0,0
1221,20,0,0.0,2,0,1,0.0,0.0,0
1222,4,0,0.0,18,0,3,0.0,0.0,0
1223,0,0,0.0,27,1,7,0.0,0.0,0
1224,9,0,0.0,8,0,1,0.0,0.0,0
1225,15,1,48.97,20,2,4,48.97,0.25,0
1226,1,0,0.0,17,1,1,0.0,0.0,0
1227,22,0,0.0,4,0,1,0.0,0.0,0
1228,19,0,0.0,9,0,2,0.0,0.0,0
1229,4,1,13.99,25,2,3,13.99,0.3333,1
1230,6,0,0.0,39,0,6,0.0,0.0,0
1231,5,0,0.0,2,0,1,0.0,0.0,0
1232,11,0,0.0,12,0,2,0.0,0.0,0
1234,11,0,0.0,18,0,4,0.0,0.0,0
1235,22,1,84.74,56,3,7,84.74,0.1429,0
1236,1,0,0.0,4,0,1,0.0,0.0,0
1237,22,0,0.0,4,0,1,0.0,0.0,0
1238,16,0,0.0,1,0,1,0.0,0.0,0
1239,20,0,0.0,37,0,2,0.0,0.0,0
1242,9,0,0.0,12,0,5,0.0,0.0,0
1243,1,0,0.0,14,0,3,0.0,0.0,0
1244,0,0,0.0,13,0,4,0.0,0.0,0
1245,19,1,25.99,75,1,6,25.99,0.1667,0
1246,0,0,0.0,13,0,2,0.0,0.0,0
1247,11,0,0.0,9,0,3,0.0,0.0,0
1248,4,0,0.0,39,0,7,0.0,0.0,0
1249,2,0,0.0,3,0,1,0.0,0.0,0
1250,11,0,0.0,9,0,3,0.0,0.0,1
1251,3,0,0.0,115,2,13,0.0,0.0,0
1252,21,0,0.0,1,0,1,0.0,0.0,0
1253,17,0,0.0,3,0,1,0.0,0.0,0
1255,0,0,0.0,6,0,1,0.0,0.0,0
1258,7,0,0.0,45,4,4,0.0,0.0,0
1259,7,0,0.0,5,1,1,0.0,0.0,0
1262,4,0,0.0,46,2,9,0.0,0.0,0
1263,8,2,116.98,100,4,16,58.49,0.125,0
1264,15,0,0.0,2,0,1,0.0,0.0,0
1265,3,1,204.99,14,1,3,204.99,0.3333,0
1266,12,1,81.98,4,2,1,81.98,1.0,0
1267,8,3,59.97,126,7,25,19.99,0.12,0
1268,13,1,14.99,54,2,7,14.99,0.1429,0
1269,2,1,31.99,63,2,8,31.99,0.125,0
1270,20,0,0.0,1,0,1,0.0,0.0,0
1271,1,2,120.48,10,3,4,60.24,0.5,0
1272,7,0,0.0,53,0,6,0.0,0.0,0
1273,0,0,0.0,34,0,3,0.0,0.0,0
1274,1,0,0.0,66,2,10,0.0,0.0,0
1277,0,0,0.0,20,0,4,0.0,0.0,0
1278,9,0,0.0,4,0,1,0.0,0.0,0
1279,18,1,27.98,79,2,17,27.98,0.0588,0
1281,8,1,17.99,54,2,8,17.99,0.125,0
1282,5,0,0.0,11,1,5,0.0,0.0,0
1283,1,0,0.0,62,1,7,0.0,0.0,0
1284,6,0,0.0,1,0,1,0.0,0.0,0
1285,1,0,0.0,31,0,5,0.0,0.0,0
1286,9,0,0.0,13,0,1,0.0,0.0,0
1287,5,0,0.0,27,1,5,0.0,0.0,0
1289,2,0,0.0,4,0,1,0.0,0.0,0
1290,2,0,0.0,26,0,5,0.0,0.0,0
1291,20,1,561.99,54,2,6,561.99,0.1667,0
1292,2,0,0.0,102,1,14,0.0,0.0,0
1294,20,0,0.0,14,0,2,0.0,0.0,0
1295,13,0,0.0,1,0,1,0.0,0.0,0
1296,23,0,0.0,1,0,1,0.0,0.0,0
1298,9,0,0.0,12,1,3,0.0,0.0,0
1300,3,0,0.0,5,0,1,0.0,0.0,0
1301,18,2,55.91,36,2,6,27.96,0.3333,0
1302,0,0,0.0,1,0,1,0.0,0.0,0
1304,2,0,0.0,16,1,3,0.0,0.0,0
1305,1,0,0.0,16,0,1,0.0,0.0,0
1306,20,1,176.99,74,4,13,176.99,0.0769,0
1307,2,0,0.0,3,0,1,0.0,0.0,0
1308,5,0,0.0,65,2,9,0.0,0.0,0
1309,0,1,123.47,22,2,6,123.47,0.1667,0
1310,6,0,0.0,31,0,4,0.0,0.0,0
1312,6,0,0.0,3,0,1,0.0,0.0,0
1313,18,0,0.0,11,0,2,0.0,0.0,0
1314,12,1,8.49,61,2,7,8.49,0.1429,0
1315,0,0,0.0,12,0,2,0.0,0.0,0
1316,2,0,0.0,19,0,3,0.0,0.0,0
1317,2,0,0.0,17,1,3,0.0,0.0,0
1318,4,0,0.0,85,2,10,0.0,0.0,0
1319,8,0,0.0,10,0,3,0.0,0.0,0
1320,2,0,0.0,12,0,2,0.0,0.0,0
1321,1,0,0.0,35,3,6,0.0,0.0,0
1322,10,0,0.0,18,1,4,0.0,0.0,0
1323,2,0,0.0,11,1,3,0.0,0.0,0
1326,11,1,23.99,41,1,5,23.99,0.2,0
1327,10,0,0.0,14,0,3,0.0,0.0,0
1328,4,0,0.0,9,0,2,0.0,0.0,0
1329,16,0,0.0,6,0,2,0.0,0.0,0
1330,3,3,503.46,124,10,23,167.82,0.1304,1
1331,1,0,0.0,17,0,3,0.0,0.0,0
1332,19,1,39.98,49,2,6,39.98,0.1667,0
1333,1,0,0.0,27,2,5,0.0,0.0,0
1334,16,1,36.99,81,1,12,36.99,0.0833,0
1335,0,0,0.0,19,0,6,0.0,0.0,0
1336,7,0,0.0,10,1,2,0.0,0.0,0
1337,21,0,0.0,2,0,1,0.0,0.0,0
1339,0,0,0.0,10,0,3,0.0,0.0,0
1340,8,0,0.0,10,0,2,0.0,0.0,0
1341,4,4,94.45,156,8,15,23.61,0.2667,0
1342,2,0,0.0,10,1,1,0.0,0.0,1
1343,4,0,0.0,11,0,3,0.0,0.0,0
1344,0,0,0.0,18,1,3,0.0,0.0,0
1345,15,0,0.0,7,0,2,0.0,0.0,0
1346,22,1,298.98,83,3,12,298.98,0.0833,0
1347,6,0,0.0,54,2,7,0.0,0.0,0
1348,0,0,0.0,3,0,1,0.0,0.0,0
1349,1,0,0.0,8,0,2,0.0,0.0,0
1350,20,0,0.0,5,0,2,0.0,0.0,0
1351,14,0,0.0,5,0,1,0.0,0.0,0
1352,4,0,0.0,14,0,3,0.0,0.0,0
1353,5,0,0.0,10,0,1,0.0,0.0,0
1354,3,0,0.0,34,2,4,0.0,0.0,0
1355,1,0,0.0,74,3,10,0.0,0.0,0
1356,5,1,32.99,5,1,1,32.99,1.0,0
1357,5,0,0.0,7,0,2,0.0,0.0,0
1358,13,0,0.0,3,0,1,0.0,0.0,0
1359,22,0,0.0,4,0,1,0.0,0.0,0
1360,2,0,0.0,14,0,3,0.0,0.0,0
1363,1,0,0.0,14,0,2,0.0,0.0,0
1364,16,0,0.0,2,0,1,0.0,0.0,0
1365,5,0,0.0,25,0,1,0.0,0.0,0
1366,2,0,0.0,31,0,4,0.0,0.0,0
1368,5,0,0.0,2,0,1,0.0,0.0,0
1369,5,0,0.0,9,0,1,0.0,0.0,0
1370,7,0,0.0,15,0,3,0.0,0.0,0
1371,1,0,0.0,75,2,9,0.0,0.0,0
1372,3,0,0.0,65,2,10,0.0,0.0,0
1374,11,0,0.0,6,1,1,0.0,0.0,0
1375,7,0,0.0,25,1,5,0.0,0.0,0
1377,22,0,0.0,1,0,1,0.0,0.0,0
1378,1,0,0.0,24,1,3,0.0,0.0,1
1379,2,2,225.96,62,4,9,112.98,0.2222,0
1380,3,2,479.98,73,5,12,239.99,0.1667,0
1383,8,0,0.0,7,2,2,0.0,0.0,0
1384,3,0,0.0,27,0,4,0.0,0.0,1
1385,0,0,0.0,34,0,7,0.0,0.0,0
1386,1,2,116.98,94,4,12,58.49,0.1667,0
1387,15,1,76.99,60,6,8,76.99,0.125,0
1388,19,1,17.99,26,1,4,17.99,0.25,0
1389,17,1,24.99,58,2,9,24.99,0.1111,0
1390,5,1,13.99,36,2,6,13.99,0.1667,0
1391,2,0,0.0,55,1,9,0.0,0.0,1
1392,7,0,0.0,9,1,3,0.0,0.0,0
1393,1,0,0.0,20,0,3,0.0,0.0,0
1394,4,0,0.0,1,0,1,0.0,0.0,0
1395,6,0,0.0,19,0,5,0.0,0.0,0
1396,2,0,0.0,10,0,5,0.0,0.0,0
1397,6,0,0.0,2,0,1,0.0,0.0,0
1398,2,0,0.0,66,4,6,0.0,0.0,0
1399,4,0,0.0,23,0,5,0.0,0.0,0
1400,3,0,0.0,13,0,3,0.0,0.0,0
1401,10,0,0.0,19,1,3,0.0,0.0,0
1402,11,1,26.99,89,7,16,26.99,0.0625,0
1403,8,0,0.0,11,0,2,0.0,0.0,0
1404,4,0,0.0,63,3,7,0.0,0.0,0
1405,19,0,0.0,5,0,1,0.0,0.0,0
1406,18,0,0.0,6,0,1,0.0,0.0,0
1407,2,0,0.0,8,0,2,0.0,0.0,0
1408,7,0,0.0,15,0,2,0.0,0.0,0
1409,10,0,0.0,3,0,1,0.0,0.0,0
1410,10,0,0.0,36,1,4,0.0,0.0,0
1411,6,0,0.0,5,0,1,0.0,0.0,0
1412,0,0,0.0,16,1,4,0.0,0.0,0
1413,12,0,0.0,2,0,1,0.0,0.0,0
1414,18,0,0.0,4,2,1,0.0,0.0,0
1415,21,1,17.99,8,1,4,17.99,0.25,0
1416,6,0,0.0,50,0,7,0.0,0.0,0
1417,13,0,0.0,21,1,3,0.0,0.0,0
1419,22,1,101.99,52,2,6,101.99,0.1667,1
1420,0,0,0.0,129,0,15,0.0,0.0,0
1421,7,0,0.0,6,0,2,0.0,0.0,0
1422,11,2,52.9,27,3,7,26.45,0.2857,0
1423,11,0,0.0,16,1,2,0.0,0.0,0
1425,3,0,0.0,58,2,5,0.0,0.0,0
1426,5,0,0.0,7,0,4,0.0,0.0,0
1427,1,0,0.0,64,5,7,0.0,0.0,0
1428,11,0,0.0,3,0,1,0.0,0.0,0
1429,2,0,0.0,47,0,7,0.0,0.0,1
1430,18,1,93.98,11,1,3,93.98,0.3333,0
1431,5,0,0.0,4,0,2,0.0,0.0,0
1432,3,0,0.0,30,1,6,0.0,0.0,1
1433,1,0,0.0,29,1,3,0.0,0.0,0
1434,1,0,0.0,7,1,1,0.0,0.0,0
1435,5,0,0.0,6,0,1,0.0,0.0,0
1436,9,0,0.0,22,0,1,0.0,0.0,0
1437,10,0,0.0,12,0,2,0.0,0.0,0
1438,7,0,0.0,7,0,3,0.0,0.0,0
1439,9,0,0.0,8,0,1,0.0,0.0,0
1440,3,0,0.0,2,0,1,0.0,0.0,0
1441,20,0,0.0,2,0,1,0.0,0.0,0
1443,22,1,144.99,38,2,8,144.99,0.125,0
1444,10,0,0.0,11,0,2,0.0,0.0,0
1446,11,0,0.0,2,0,1,0.0,0.0,0
1447,6,0,0.0,9,0,3,0.0,0.0,0
1448,10,0,0.0,7,0,1,0.0,0.0,0
1449,1,0,0.0,29,2,6,0.0,0.0,0
1450,0,0,0.0,25,1,4,0.0,0.0,0
1451,2,0,0.0,14,0,2,0.0,0.0,0
1453,9,0,0.0,5,0,1,0.0,0.0,0
1454,22,0,0.0,7,0,1,0.0,0.0,0
1457,6,1,6.98,69,1,9,6.98,0.1111,0
1459,4,0,0.0,47,2,6,0.0,0.0,0
1460,7,0,0.0,2,0,1,0.0,0.0,0
1461,17,0,0.0,4,0,1,0.0,0.0,0
1462,7,2,129.98,60,3,10,64.99,0.2,0
1463,20,2,266.98,38,4,7,133.49,0.2857,0
1464,12,0,0.0,12,0,2,0.0,0.0,0
1465,2,4,249.46,202,11,25,62.36,0.16,1
1466,1,0,0.0,2,0,1,0.0,0.0,0
1467,4,0,0.0,6,0,2,0.0,0.0,0
1468,13,1,9.49,7,1,3,9.49,0.3333,0
1469,1,0,0.0,57,3,6,0.0,0.0,0
1470,4,1,14.99,65,3,11,14.99,0.0909,0
1472,4,0,0.0,7,0,1,0.0,0.0,0
1473,3,0,0.0,48,1,8,0.0,0.0,0
1474,7,0,0.0,27,1,7,0.0,0.0,0
1476,15,0,0.0,12,1,1,0.0,0.0,0
1477,20,1,59.99,29,1,3,59.99,0.3333,0
1478,0,0,0.0,102,0,10,0.0,0.0,0
1479,21,0,0.0,2,0,1,0.0,0.0,0
1480,5,0,0.0,13,0,4,0.0,0.0,0
1481,5,0,0.0,37,0,11,0.0,0.0,0
1483,4,0,0.0,10,1,2,0.0,0.0,0
1484,14,2,46.94,65,3,9,23.47,0.2222,0
1485,4,0,0.0,26,0,4,0.0,0.0,0
1487,21,0,0.0,4,0,1,0.0,0.0,0
1488,0,0,0.0,8,0,3,0.0,0.0,0
1489,12,0,0.0,4,1,1,0.0,0.0,0
1490,17,1,46.99,25,3,7,46.99,0.1429,1
1491,19,0,0.0,2,0,1,0.0,0.0,0
1493,9,0,0.0,13,0,1,0.0,0.0,0
1494,6,0,0.0,77,1,11,0.0,0.0,0
1496,6,0,0.0,25,1,2,0.0,0.0,0
1500,2,0,0.0,44,0,6,0.0,0.0,0
1501,1,0,0.0,9,0,1,0.0,0.0,0
1502,5,0,0.0,48,0,9,0.0,0.0,0
1503,21,1,8.49,144,6,15,8.49,0.0667,1
1504,8,0,0.0,3,0,1,0.0,0.0,0
1505,1,0,0.0,18,1,5,0.0,0.0,0
1506,20,1,77.0,29,3,2,77.0,0.5,0
1507,23,0,0.0,6,0,1,0.0,0.0,0
1508,10,0,0.0,14,1,3,0.0,0.0,0
1509,4,0,0.0,21,0,4,0.0,0.0,0
1510,1,0,0.0,58,0,8,0.0,0.0,0
1511,22,0,0.0,8,0,2,0.0,0.0,0
1512,13,0,0.0,5,0,1,0.0,0.0,0
1513,23,0,0.0,5,0,1,0.0,0.0,0
1514,2,0,0.0,3,0,1,0.0,0.0,0
1515,5,0,0.0,9,0,2,0.0,0.0,0
1516,7,0,0.0,5,0,1,0.0,0.0,0
1517,5,0,0.0,27,1,3,0.0,0.0,0
1518,0,0,0.0,1,1,1,0.0,0.0,0
1519,3,0,0.0,2,0,1,0.0,0.0,0
1521,19,0,0.0,1,0,1,0.0,0.0,0
1522,1,0,0.0,67,2,7,0.0,0.0,0
1523,1,0,0.0,63,0,10,0.0,0.0,0
1525,18,0,0.0,5,0,1,0.0,0.0,0
1526,22,0,0.0,2,0,1,0.0,0.0,0
1527,8,0,0.0,4,0,1,0.0,0.0,0
1528,16,0,0.0,7,0,1,0.0,0.0,0
1529,2,0,0.0,9,0,2,0.0,0.0,0
1530,5,0,0.0,59,3,8,0.0,0.0,0
1531,15,0,0.0,13,0,2,0.0,0.0,0
1532,19,0,0.0,13,1,2,0.0,0.0,0
1533,8,1,32.99,130,1,15,32.99,0.0667,0
1534,0,0,0.0,33,1,11,0.0,0.0,0
1535,1,0,0.0,76,1,7,0.0,0.0,0
1536,3,0,0.0,17,0,2,0.0,0.0,0
1537,2,0,0.0,3,0,1,0.0,0.0,0
1538,4,0,0.0,61,1,9,0.0,0.0,0
1539,0,0,0.0,30,0,4,0.0,0.0,0
1540,4,0,0.0,5,0,1,0.0,0.0,0
1542,3,0,0.0,63,1,4,0.0,0.0,0
1543,5,1,23.99,19,1,1,23.99,1.0,0
1544,11,1,30.99,18,1,3,30.99,0.3333,0
1545,6,0,0.0,21,1,3,0.0,0.0,0
1547,19,0,0.0,6,0,1,0.0,0.0,0
1548,1,0,0.0,47,0,6,0.0,0.0,0
1549,0,0,0.0,18,1,2,0.0,0.0,0
1550,11,0,0.0,20,1,2,0.0,0.0,0
1551,2,0,0.0,14,0,4,0.0,0.0,0
1552,8,0,0.0,2,0,1,0.0,0.0,0
1554,6,2,92.43,94,5,13,46.22,0.1538,0
1556,3,0,0.0,50,1,7,0.0,0.0,0
1557,7,0,0.0,18,1,5,0.0,0.0,0
1558,0,1,7.49,49,1,6,7.49,0.1667,0
1559,4,0,0.0,8,0,2,0.0,0.0,0
1561,5,0,0.0,4,1,2,0.0,0.0,0
1562,13,0,0.0,6,0,1,0.0,0.0,0
1563,6,0,0.0,3,0,1,0.0,0.0,0
1564,0,0,0.0,14,0,2,0.0,0.0,0
1565,22,0,0.0,7,0,1,0.0,0.0,0
1566,1,0,0.0,3,0,2,0.0,0.0,0
1568,21,0,0.0,5,0,1,0.0,0.0,0
1569,7,0,0.0,47,0,6,0.0,0.0,0
1570,0,0,0.0,10,0,3,0.0,0.0,0
1571,1,0,0.0,19,0,4,0.0,0.0,0
1573,18,0,0.0,3,0,1,0.0,0.0,0
1574,1,0,0.0,42,2,10,0.0,0.0,0
1575,4,0,0.0,4,0,1,0.0,0.0,0
1576,18,1,10.99,51,1,5,10.99,0.2,0
1577,20,0,0.0,2,0,1,0.0,0.0,0
1578,0,0,0.0,2,1,1,0.0,0.0,0
1579,0,0,0.0,65,4,10,0.0,0.0,0
1580,4,0,0.0,2,0,1,0.0,0.0,0
1581,22,0,0.0,2,0,1,0.0,0.0,0
1583,21,0,0.0,12,0,2,0.0,0.0,0
1584,18,0,0.0,1,0,1,0.0,0.0,0
1585,1,0,0.0,95,4,11,0.0,0.0,0
1586,21,1,59.99,17,1,3,59.99,0.3333,1
1587,5,0,0.0,23,1,3,0.0,0.0,0
1588,4,0,0.0,31,1,7,0.0,0.0,0
1589,5,0,0.0,12,0,4,0.0,0.0,0
1591,3,0,0.0,12,0,4,0.0,0.0,0
1593,5,2,44.98,67,4,8,22.49,0.25,0
1594,12,0,0.0,12,1,1,0.0,0.0,0
1595,4,3,172.63,64,5,9,57.54,0.3333,1
1596,1,0,0.0,2,0,1,0.0,0.0,0
1597,18,0,0.0,9,0,1,0.0,0.0,0
1598,14,0,0.0,13,0,2,0.0,0.0,0
1599,12,0,0.0,2,1,1,0.0,0.0,0
1600,10,0,0.0,5,0,1,0.0,0.0,0
1601,12,0,0.0,7,0,1,0.0,0.0,0
1603,0,0,0.0,6,0,2,0.0,0.0,0
1604,21,0,0.0,5,0,1,0.0,0.0,0
1605,18,0,0.0,4,1,1,0.0,0.0,0
1606,0,0,0.0,2,1,1,0.0,0.0,0
1607,17,0,0.0,1,0,1,0.0,0.0,0
1608,4,0,0.0,1,0,1,0.0,0.0,0
1609,4,0,0.0,18,1,2,0.0,0.0,0
1611,1,1,31.99,29,2,6,31.99,0.1667,0
1612,1,0,0.0,25,0,4,0.0,0.0,0
1613,5,0,0.0,1,0,1,0.0,0.0,0
1614,2,0,0.0,11,0,4,0.0,0.0,0
1615,8,0,0.0,8,1,1,0.0,0.0,0
1616,6,0,0.0,11,0,1,0.0,0.0,0
1617,3,0,0.0,23,1,6,0.0,0.0,0
1618,17,0,0.0,2,0,1,0.0,0.0,0
1620,4,0,0.0,12,1,4,0.0,0.0,0
1621,6,0,0.0,16,0,1,0.0,0.0,0
1622,2,0,0.0,16,0,4,0.0,0.0,0
1624,21,0,0.0,5,0,1,0.0,0.0,0
1625,3,0,0.0,10,0,2,0.0,0.0,0
1626,21,1,23.32,64,1,9,23.32,0.1111,0
1627,2,0,0.0,12,0,2,0.0,0.0,0
1628,5,0,0.0,11,0,3,0.0,0.0,0
1629,3,1,11.99,76,1,10,11.99,0.1,0
1630,4,0,0.0,42,1,9,0.0,0.0,0
1635,11,0,0.0,8,0,2,0.0,0.0,0
1636,11,0,0.0,33,0,6,0.0,0.0,0
1638,8,0,0.0,27,1,9,0.0,0.0,0
1639,10,0,0.0,3,0,1,0.0,0.0,0
1640,5,0,0.0,20,0,4,0.0,0.0,0
1641,20,0,0.0,6,0,1,0.0,0.0,0
1642,18,0,0.0,3,0,1,0.0,0.0,0
1644,9,0,0.0,3,0,1,0.0,0.0,0
1645,0,0,0.0,17,0,3,0.0,0.0,0
1647,14,1,26.99,3,1,1,26.99,1.0,0
1649,3,0,0.0,3,0,1,0.0,0.0,0
1650,3,0,0.0,11,0,4,0.0,0.0,0
1651,18,0,0.0,1,0,1,0.0,0.0,0
1652,17,1,43.99,21,1,5,43.99,0.2,0
1653,0,0,0.0,5,0,2,0.0,0.0,0
1654,11,0,0.0,15,0,2,0.0,0.0,0
1655,21,0,0.0,5,0,1,0.0,0.0,0
1656,2,0,0.0,29,2,2,0.0,0.0,0
1657,4,0,0.0,29,2,6,0.0,0.0,0
1658,2,0,0.0,42,0,10,0.0,0.0,0
1659,2,0,0.0,10,0,4,0.0,0.0,0
1660,0,1,9.49,92,6,16,9.49,0.0625,1
1661,22,0,0.0,8,0,1,0.0,0.0,0
1664,13,0,0.0,1,0,1,0.0,0.0,0
1665,0,0,0.0,82,3,8,0.0,0.0,0
1666,7,0,0.0,21,0,3,0.0,0.0,0
1668,22,0,0.0,6,0,1,0.0,0.0,0
1669,19,0,0.0,3,0,1,0.0,0.0,0
1670,1,0,0.0,77,3,16,0.0,0.0,1
1671,1,2,667.95,161,4,29,333.98,0.069,1
1672,21,0,0.0,10,0,1,0.0,0.0,0
1673,3,0,0.0,38,2,7,0.0,0.0,0
1674,3,0,0.0,16,0,3,0.0,0.0,0
1675,12,1,372.99,44,1,6,372.99,0.1667,0
1677,23,1,117.99,41,1,6,117.99,0.1667,0
1678,2,0,0.0,4,0,2,0.0,0.0,0
1679,20,0,0.0,3,0,1,0.0,0.0,0
1680,10,2,41.98,48,4,7,20.99,0.2857,0
1681,11,0,0.0,33,1,6,0.0,0.0,0
1682,18,0,0.0,8,0,1,0.0,0.0,0
1683,0,0,0.0,10,0,3,0.0,0.0,0
1684,17,0,0.0,1,0,1,0.0,0.0,0
1685,1,0,0.0,143,2,13,0.0,0.0,0
1687,2,0,0.0,16,0,4,0.0,0.0,0
1688,1,0,0.0,45,2,5,0.0,0.0,0
1689,0,0,0.0,24,1,3,0.0,0.0,0
1690,3,0,0.0,3,0,3,0.0,0.0,0
1691,2,0,0.0,56,1,7,0.0,0.0,0
1692,0,0,0.0,33,0,6,0.0,0.0,0
1694,9,0,0.0,4,0,2,0.0,0.0,0
1695,7,0,0.0,7,0,1,0.0,0.0,0
1696,4,0,0.0,12,0,3,0.0,0.0,0
1697,8,0,0.0,27,1,5,0.0,0.0,0
1698,4,0,0.0,12,0,2,0.0,0.0,0
1699,0,0,0.0,23,0,5,0.0,0.0,0
1701,9,0,0.0,5,0,1,0.0,0.0,0
1703,22,1,14.99,21,2,5,14.99,0.2,0
1704,0,1,8.98,42,3,6,8.98,0.1667,0
1705,10,0,0.0,19,1,6,0.0,0.0,0
1706,3,0,0.0,51,0,7,0.0,0.0,0
1707,1,0,0.0,21,1,4,0.0,0.0,0
1708,22,1,34.99,20,1,1,34.99,1.0,0
1709,22,1,7.76,55,4,7,7.76,0.1429,0
1711,1,0,0.0,12,0,3,0.0,0.0,0
1712,2,2,32.98,79,5,17,16.49,0.1176,1
1713,3,0,0.0,21,0,6,0.0,0.0,0
1715,10,1,5.49,24,1,3,5.49,0.3333,0
1716,5,0,0.0,4,0,3,0.0,0.0,0
1717,1,0,0.0,52,0,6,0.0,0.0,0
1718,10,2,317.98,69,3,10,158.99,0.2,1
1719,13,0,0.0,6,0,1,0.0,0.0,0
1720,18,0,0.0,1,0,1,0.0,0.0,0
1723,19,0,0.0,5,0,1,0.0,0.0,0
1724,6,0,0.0,7,0,2,0.0,0.0,0
1725,2,0,0.0,27,0,3,0.0,0.0,0
1726,3,0,0.0,16,0,2,0.0,0.0,0
1727,0,0,0.0,7,0,3,0.0,0.0,0
1728,2,0,0.0,14,0,3,0.0,0.0,0
1729,0,0,0.0,22,0,5,0.0,0.0,0
1730,8,0,0.0,39,0,5,0.0,0.0,0
1731,3,0,0.0,2,0,1,0.0,0.0,0
1732,1,0,0.0,42,1,10,0.0,0.0,0
1733,19,0,0.0,1,0,1,0.0,0.0,0
1734,8,0,0.0,35,0,5,0.0,0.0,0
1735,1,0,0.0,2,0,1,0.0,0.0,0
1737,4,0,0.0,8,0,4,0.0,0.0,0
1738,1,0,0.0,75,4,11,0.0,0.0,1
1739,2,0,0.0,38,0,4,0.0,0.0,0
1740,5,0,0.0,17,0,2,0.0,0.0,0
1741,4,0,0.0,11,0,3,0.0,0.0,0
1742,3,1,14.99,49,2,9,14.99,0.1111,0
1743,3,0,0.0,53,1,4,0.0,0.0,0
1744,1,0,0.0,12,0,2,0.0,0.0,0
1746,10,0,0.0,5,1,1,0.0,0.0,0
1747,0,0,0.0,5,0,1,0.0,0.0,0
1748,3,0,0.0,5,0,3,0.0,0.0,0
1749,6,0,0.0,4,0,1,0.0,0.0,0
1750,16,0,0.0,6,0,2,0.0,0.0,0
1751,3,0,0.0,32,0,4,0.0,0.0,0
1752,13,0,0.0,17,0,4,0.0,0.0,0
1753,19,0,0.0,23,0,2,0.0,0.0,1
1754,0,0,0.0,37,0,7,0.0,0.0,0
1755,21,1,561.99,39,3,4,561.99,0.25,0
1756,17,0,0.0,4,0,1,0.0,0.0,0
1757,5,0,0.0,19,0,3,0.0,0.0,0
1758,2,0,0.0,118,1,14,0.0,0.0,0
1759,8,0,0.0,63,2,8,0.0,0.0,0
1760,5,0,0.0,45,0,5,0.0,0.0,1
1761,17,0,0.0,3,0,1,0.0,0.0,0
1763,16,0,0.0,1,0,1,0.0,0.0,0
1764,11,0,0.0,2,0,1,0.0,0.0,0
1765,1,0,0.0,28,5,5,0.0,0.0,0
1766,1,0,0.0,82,2,9,0.0,0.0,1
1767,13,0,0.0,11,0,1,0.0,0.0,0
1768,21,1,15.52,45,1,5,15.52,0.2,0
1769,4,0,0.0,32,0,8,0.0,0.0,0
1770,9,0,0.0,47,1,5,0.0,0.0,0
1771,20,1,76.99,24,1,5,76.99,0.2,0
1773,1,0,0.0,106,2,10,0.0,0.0,0
1774,6,0,0.0,5,1,2,0.0,0.0,0
1775,3,0,0.0,1,0,1,0.0,0.0,0
1776,9,0,0.0,15,0,3,0.0,0.0,0
1777,0,0,0.0,14,0,3,0.0,0.0,0
1778,9,0,0.0,3,0,1,0.0,0.0,0
1779,19,0,0.0,6,0,1,0.0,0.0,0
1780,21,1,23.99,125,1,16,23.99,0.0625,0
1781,6,0,0.0,4,0,1,0.0,0.0,0
1782,0,0,0.0,13,0,4,0.0,0.0,0
1783,4,0,0.0,1,0,1,0.0,0.0,0
1784,8,0,0.0,3,0,1,0.0,0.0,0
1785,4,0,0.0,5,0,1,0.0,0.0,0
1786,5,0,0.0,10,0,1,0.0,0.0,0
1787,5,0,0.0,16,1,5,0.0,0.0,0
1788,8,0,0.0,14,0,2,0.0,0.0,0
1789,3,0,0.0,21,0,7,0.0,0.0,0
1790,21,1,93.97,53,3,12,93.97,0.0833,1
1791,0,0,0.0,129,4,19,0.0,0.0,0
1792,9,0,0.0,8,0,1,0.0,0.0,0
1793,14,2,44.98,31,2,7,22.49,0.2857,0
1794,11,0,0.0,7,0,1,0.0,0.0,0
1795,2,0,0.0,18,0,4,0.0,0.0,0
1796,3,0,0.0,79,6,6,0.0,0.0,0
1798,5,2,88.77,74,5,8,44.38,0.25,0
1799,11,0,0.0,4,0,1,0.0,0.0,0
1800,9,0,0.0,9,0,1,0.0,0.0,0
1801,6,0,0.0,4,0,1,0.0,0.0,0
1802,9,1,10.98,80,5,11,10.98,0.0909,1
1803,4,2,837.97,157,7,32,418.98,0.0625,1
1805,2,0,0.0,8,0,1,0.0,0.0,0
1806,1,0,0.0,21,1,5,0.0,0.0,0
1807,8,0,0.0,10,0,4,0.0,0.0,0
1808,19,0,0.0,1,0,1,0.0,0.0,0
1809,20,1,36.98,75,5,13,36.98,0.0769,0
1810,3,0,0.0,3,0,1,0.0,0.0,0
1811,14,1,37.99,94,1,14,37.99,0.0714,0
1812,4,0,0.0,51,1,5,0.0,0.0,0
1813,0,0,0.0,6,0,1,0.0,0.0,0
1814,1,0,0.0,57,3,6,0.0,0.0,0
1816,5,0,0.0,27,0,3,0.0,0.0,0
1817,12,0,0.0,22,0,3,0.0,0.0,0
1818,10,1,13.99,97,3,16,13.99,0.0625,0
1819,9,0,0.0,13,0,1,0.0,0.0,0
1820,15,0,0.0,8,0,4,0.0,0.0,0
1821,0,0,0.0,14,0,2,0.0,0.0,0
1822,6,0,0.0,15,2,2,0.0,0.0,0
1823,7,0,0.0,24,1,3,0.0,0.0,0
1824,3,0,0.0,6,1,3,0.0,0.0,0
1825,21,0,0.0,4,0,1,0.0,0.0,0
1826,6,0,0.0,63,0,6,0.0,0.0,0
1827,1,0,0.0,15,1,6,0.0,0.0,0
1828,14,1,245.98,9,1,2,245.98,0.5,0
1831,19,0,0.0,2,0,1,0.0,0.0,0
1832,0,0,0.0,25,0,3,0.0,0.0,0
1833,1,0,0.0,43,0,6,0.0,0.0,1
1834,0,0,0.0,51,4,7,0.0,0.0,0
1835,14,0,0.0,1,0,1,0.0,0.0,0
1836,0,0,0.0,95,2,12,0.0,0.0,0
1838,21,1,21.36,85,5,13,21.36,0.0769,0
1839,0,0,0.0,53,0,10,0.0,0.0,0
1840,0,0,0.0,42,1,5,0.0,0.0,0
1841,0,0,0.0,18,0,3,0.0,0.0,0
1842,6,0,0.0,46,2,6,0.0,0.0,0
1843,12,0,0.0,4,0,1,0.0,0.0,0
1844,7,1,19.99,98,2,9,19.99,0.1111,0
1846,3,0,0.0,23,0,7,0.0,0.0,0
1847,6,1,440.99,172,5,18,440.99,0.0556,0
1848,5,1,17.99,73,2,9,17.99,0.1111,0
1850,20,0,0.0,4,0,1,0.0,0.0,0
1851,5,0,0.0,5,0,2,0.0,0.0,0
1852,18,1,23.99,20,1,2,23.99,0.5,0
1853,0,0,0.0,27,0,3,0.0,0.0,0
1854,5,0,0.0,39,1,4,0.0,0.0,0
1855,6,0,0.0,16,0,4,0.0,0.0,0
1856,8,0,0.0,2,0,1,0.0,0.0,0
1857,8,0,0.0,1,0,1,0.0,0.0,0
1858,4,0,0.0,11,0,2,0.0,0.0,0
1859,11,3,44.93,62,4,11,14.98,0.2727,0
1860,1,0,0.0,34,0,4,0.0,0.0,0
1861,7,0,0.0,17,0,4,0.0,0.0,0
1862,10,0,0.0,2,0,1,0.0,0.0,0
1864,2,0,0.0,71,2,10,0.0,0.0,0
1865,0,0,0.0,74,2,12,0.0,0.0,0
1867,7,0,0.0,7,0,1,0.0,0.0,0
1868,18,1,25.36,57,3,9,25.36,0.1111,0
1869,13,0,0.0,2,0,1,0.0,0.0,0
1870,18,0,0.0,3,0,1,0.0,0.0,0
1871,0,0,0.0,17,0,1,0.0,0.0,0
1873,3,0,0.0,52,1,7,0.0,0.0,0
1874,3,0,0.0,10,1,2,0.0,0.0,0
1875,0,0,0.0,128,1,19,0.0,0.0,0
1876,7,1,96.99,6,1,1,96.99,1.0,0
1877,15,0,0.0,15,1,3,0.0,0.0,0
1878,3,0,0.0,2,0,1,0.0,0.0,0
1879,19,0,0.0,10,1,1,0.0,0.0,0
1880,20,1,41.99,53,3,11,41.99,0.0909,0
1881,5,0,0.0,6,1,3,0.0,0.0,0
1883,11,0,0.0,11,2,3,0.0,0.0,0
1884,21,0,0.0,2,0,1,0.0,0.0,0
1885,16,0,0.0,2,0,1,0.0,0.0,0
1886,21,1,47.99,68,5,13,47.99,0.0769,0
1887,1,0,0.0,33,2,5,0.0,0.0,0
1889,1,0,0.0,21,0,3,0.0,0.0,0
1890,0,0,0.0,4,0,1,0.0,0.0,0
1891,7,0,0.0,13,0,2,0.0,0.0,0
1892,2,0,0.0,49,0,10,0.0,0.0,1
1893,18,0,0.0,22,0,3,0.0,0.0,0
1894,11,1,193.98,81,2,10,193.98,0.1,0
1895,21,0,0.0,2,0,1,0.0,0.0,0
1896,3,0,0.0,56,1,5,0.0,0.0,0
1897,14,0,0.0,13,0,2,0.0,0.0,0
1899,0,0,0.0,11,0,3,0.0,0.0,0
1900,7,1,765.99,52,3,8,765.99,0.125,1
1901,17,1,46.99,72,2,12,46.99,0.0833,0
1902,15,0,0.0,3,0,1,0.0,0.0,0
1903,0,0,0.0,8,0,2,0.0,0.0,0
1904,7,0,0.0,31,1,4,0.0,0.0,0
1906,6,0,0.0,51,1,7,0.0,0.0,0
1908,8,0,0.0,84,1,9,0.0,0.0,0
1910,5,1,24.99,89,2,12,24.99,0.0833,0
1912,3,0,0.0,4,0,1,0.0,0.0,0
1913,3,0,0.0,19,2,3,0.0,0.0,0
1914,0,0,0.0,13,3,4,0.0,0.0,0
1915,11,0,0.0,9,0,1,0.0,0.0,0
1916,5,0,0.0,6,0,3,0.0,0.0,0
1917,22,1,49.02,40,3,7,49.02,0.1429,0
1918,17,0,0.0,6,0,2,0.0,0.0,0
1919,4,0,0.0,9,0,1,0.0,0.0,0
1921,11,1,24.99,18,1,3,24.99,0.3333,0
1922,2,0,0.0,9,0,2,0.0,0.0,0
1923,0,0,0.0,45,1,7,0.0,0.0,0
1924,9,0,0.0,8,0,2,0.0,0.0,0
1925,2,0,0.0,25,0,3,0.0,0.0,0
1926,5,0,0.0,2,0,1,0.0,0.0,0
1927,7,0,0.0,4,0,2,0.0,0.0,0
1928,5,0,0.0,13,1,4,0.0,0.0,0
1929,6,1,54.97,59,3,7,54.97,0.1429,0
1931,2,0,0.0,7,0,1,0.0,0.0,0
1932,5,0,0.0,13,0,3,0.0,0.0,0
1935,13,0,0.0,4,0,1,0.0,0.0,0
1936,14,1,17.99,57,1,6,17.99,0.1667,0
1937,8,0,0.0,3,0,1,0.0,0.0,0
1938,20,0,0.0,2,0,1,0.0,0.0,0
1939,17,2,628.97,41,3,5,314.48,0.4,0
1940,8,1,14.99,17,1,1,14.99,1.0,0
1941,7,1,100.99,87,2,5,100.99,0.2,0
1942,2,0,0.0,21,0,5,0.0,0.0,0
1943,14,0,0.0,13,0,3,0.0,0.0,0
1944,8,0,0.0,9,0,3,0.0,0.0,0
1945,0,0,0.0,9,0,2,0.0,0.0,0
1946,12,0,0.0,9,0,1,0.0,0.0,0
1947,6,0,0.0,1,0,1,0.0,0.0,0
1948,19,0,0.0,13,0,2,0.0,0.0,0
1949,3,0,0.0,10,0,4,0.0,0.0,0
1950,2,0,0.0,8,0,1,0.0,0.0,0
1951,14,0,0.0,6,1,2,0.0,0.0,0
1953,22,1,2.3,45,2,6,2.3,0.1667,0
1955,4,0,0.0,2,0,1,0.0,0.0,0
1956,7,0,0.0,46,1,5,0.0,0.0,0
1957,19,0,0.0,2,0,1,0.0,0.0,0
1958,15,1,87.99,19,1,3,87.99,0.3333,0
1959,6,0,0.0,31,0,6,0.0,0.0,0
1960,15,0,0.0,16,0,2,0.0,0.0,0
1961,21,1,105.98,9,2,2,105.98,0.5,0
1962,8,1,248.98,205,7,24,248.98,0.0417,1
1964,0,0,0.0,41,2,8,0.0,0.0,1
1965,4,1,23.99,22,1,2,23.99,0.5,0
1966,1,0,0.0,8,0,2,0.0,0.0,0
1967,7,0,0.0,21,2,3,0.0,0.0,0
1968,17,0,0.0,1,0,1,0.0,0.0,0
1969,14,1,89.99,41,4,4,89.99,0.25,0
1970,4,0,0.0,5,0,1,0.0,0.0,0
1971,1,0,0.0,5,0,2,0.0,0.0,0
1972,2,2,294.11,69,4,13,147.06,0.1538,0
1973,1,0,0.0,1,0,1,0.0,0.0,0
1974,2,0,0.0,18,0,3,0.0,0.0,0
1975,8,0,0.0,8,0,3,0.0,0.0,0
1976,0,1,106.99,63,2,12,106.99,0.0833,0
1977,7,0,0.0,24,0,6,0.0,0.0,0
1978,20,0,0.0,1,0,1,0.0,0.0,0
1979,0,1,265.99,29,1,6,265.99,0.1667,0
1980,8,0,0.0,107,0,9,0.0,0.0,0
1982,2,0,0.0,10,0,3,0.0,0.0,0
1983,0,0,0.0,68,2,14,0.0,0.0,0
1984,18,1,157.98,61,3,11,157.98,0.0909,0
1985,0,0,0.0,10,0,4,0.0,0.0,0
1986,6,0,0.0,22,1,3,0.0,0.0,0
1987,9,0,0.0,32,0,4,0.0,0.0,0
1988,0,0,0.0,63,0,16,0.0,0.0,0
1989,13,0,0.0,2,0,1,0.0,0.0,0
1990,4,0,0.0,54,2,12,0.0,0.0,0
1991,2,0,0.0,46,1,10,0.0,0.0,0
1993,3,0,0.0,14,0,2,0.0,0.0,0
1995,1,0,0.0,25,1,8,0.0,0.0,0
1996,6,0,0.0,8,0,2,0.0,0.0,0
1997,1,0,0.0,23,1,3,0.0,0.0,0
1998,5,0,0.0,53,4,8,0.0,0.0,0
1999,15,1,57.99,83,1,9,57.99,0.1111,0
2002,1,0,0.0,78,1,14,0.0,0.0,0
2004,12,1,673.98,41,1,4,673.98,0.25,0
2005,4,0,0.0,27,2,5,0.0,0.0,0
2006,10,0,0.0,9,0,1,0.0,0.0,0
2008,11,0,0.0,4,0,1,0.0,0.0,0
2009,13,0,0.0,10,0,2,0.0,0.0,0
2010,9,0,0.0,6,0,1,0.0,0.0,0
2011,19,0,0.0,5,0,1,0.0,0.0,0
2012,2,0,0.0,4,0,1,0.0,0.0,0
2013,7,0,0.0,35,0,5,0.0,0.0,0
2014,0,0,0.0,42,1,7,0.0,0.0,0
2015,8,0,0.0,3,0,1,0.0,0.0,0
2017,22,1,144.99,22,1,9,144.99,0.1111,0
2019,0,0,0.0,10,0,2,0.0,0.0,0
2020,2,0,0.0,43,0,5,0.0,0.0,0
2021,10,0,0.0,12,0,3,0.0,0.0,0
2022,21,1,46.99,2,1,1,46.99,1.0,0
2023,0,0,0.0,4,0,1,0.0,0.0,0
2024,20,1,204.99,108,3,13,204.99,0.0769,0
2025,1,0,0.0,15,1,5,0.0,0.0,0
2026,2,0,0.0,9,0,1,0.0,0.0,0
2028,6,0,0.0,16,2,3,0.0,0.0,0
2030,18,0,0.0,1,0,1,0.0,0.0,0
2031,11,0,0.0,13,1,3,0.0,0.0,0
2032,1,0,0.0,20,0,5,0.0,0.0,0
2033,19,0,0.0,5,0,1,0.0,0.0,0
2035,11,0,0.0,5,0,1,0.0,0.0,0
2036,15,1,85.99,65,2,10,85.99,0.1,1
2037,6,0,0.0,9,0,2,0.0,0.0,0
2038,20,0,0.0,3,0,1,0.0,0.0,0
2040,11,1,37.98,169,4,17,37.98,0.0588,0
2042,4,1,89.99,10,1,4,89.99,0.25,0
2043,3,0,0.0,2,0,1,0.0,0.0,0
2044,3,2,526.98,50,3,8,263.49,0.25,0
2045,1,0,0.0,17,0,3,0.0,0.0,0
2046,18,1,37.99,18,1,4,37.99,0.25,1
2047,1,0,0.0,25,0,7,0.0,0.0,0
2048,4,0,0.0,4,0,1,0.0,0.0,0
2049,18,0,0.0,7,0,1,0.0,0.0,0
2050,13,1,24.99,36,4,8,24.99,0.125,1
2051,2,0,0.0,31,0,8,0.0,0.0,0
2052,6,0,0.0,29,0,4,0.0,0.0,0
2054,10,0,0.0,10,0,3,0.0,0.0,0
2055,5,0,0.0,21,0,3,0.0,0.0,0
2057,2,0,0.0,10,0,6,0.0,0.0,0
2059,16,1,10.99,51,1,5,10.99,0.2,0
2060,4,0,0.0,16,0,1,0.0,0.0,0
2063,3,0,0.0,6,0,2,0.0,0.0,0
2064,6,0,0.0,25,0,6,0.0,0.0,0
2065,19,0,0.0,3,0,1,0.0,0.0,0
2066,0,0,0.0,17,1,4,0.0,0.0,0
2067,16,1,165.99,56,3,10,165.99,0.1,0
2068,5,0,0.0,13,1,4,0.0,0.0,0
2069,0,0,0.0,55,2,12,0.0,0.0,0
2070,4,0,0.0,15,0,1,0.0,0.0,0
2071,22,0,0.0,5,0,1,0.0,0.0,0
2072,6,0,0.0,1,0,1,0.0,0.0,0
2073,17,0,0.0,7,0,1,0.0,0.0,0
2074,0,0,0.0,51,2,4,0.0,0.0,0
2075,19,1,143.98,58,4,15,143.98,0.0667,1
2076,0,0,0.0,109,1,10,0.0,0.0,1
2077,1,0,0.0,43,1,4,0.0,0.0,0
2078,6,0,0.0,38,0,5,0.0,0.0,0
2079,23,0,0.0,6,1,1,0.0,0.0,0
2080,10,2,55.98,51,2,8,27.99,0.25,0
2081,0,0,0.0,12,0,4,0.0,0.0,0
2082,18,1,90.99,30,1,4,90.99,0.25,0
2083,0,2,45.98,67,3,8,22.99,0.25,0
2084,6,0,0.0,4,0,1,0.0,0.0,0
2085,1,0,0.0,15,0,3,0.0,0.0,0
2086,0,0,0.0,7,1,2,0.0,0.0,0
2087,1,0,0.0,16,0,5,0.0,0.0,0
2088,9,0,0.0,33,1,4,0.0,0.0,0
2089,3,0,0.0,12,0,3,0.0,0.0,0
2090,7,1,89.97,7,2,1,89.97,1.0,0
2092,2,0,0.0,6,0,2,0.0,0.0,0
2094,5,0,0.0,54,1,6,0.0,0.0,0
2095,8,3,295.45,76,4,11,98.48,0.2727,0
2096,3,0,0.0,1,0,1,0.0,0.0,0
2097,3,0,0.0,64,1,11,0.0,0.0,0
2098,15,0,0.0,24,0,4,0.0,0.0,0
2099,6,0,0.0,6,1,1,0.0,0.0,0
2100,1,2,205.46,38,5,7,102.73,0.2857,0
2101,3,0,0.0,18,0,2,0.0,0.0,0
2102,0,0,0.0,67,1,10,0.0,0.0,0
2103,6,0,0.0,4,0,2,0.0,0.0,0
2104,19,1,126.98,114,4,20,126.98,0.05,0
2105,12,1,15.99,11,1,3,15.99,0.3333,0
2106,18,0,0.0,7,0,1,0.0,0.0,0
2107,8,0,0.0,45,3,7,0.0,0.0,1
2108,0,0,0.0,4,0,1,0.0,0.0,0
2109,12,1,5.49,11,2,2,5.49,0.5,0
2110,17,2,230.98,34,3,9,115.49,0.2222,0
2111,4,1,109.99,41,3,9,109.99,0.1111,1
2112,1,0,0.0,9,1,1,0.0,0.0,0
2113,9,0,0.0,24,0,3,0.0,0.0,0
2114,3,0,0.0,87,2,9,0.0,0.0,0
2115,0,0,0.0,13,0,5,0.0,0.0,0
2117,4,0,0.0,8,0,2,0.0,0.0,0
2118,2,1,190.99,84,2,19,190.99,0.0526,0
2119,6,0,0.0,31,1,5,0.0,0.0,0
2120,4,0,0.0,4,0,2,0.0,0.0,0
2121,12,0,0.0,6,0,2,0.0,0.0,0
2122,3,0,0.0,17,0,4,0.0,0.0,0
2123,5,0,0.0,16,2,4,0.0,0.0,0
2125,9,0,0.0,6,0,1,0.0,0.0,0
2126,20,0,0.0,4,0,1,0.0,0.0,0
2127,0,0,0.0,8,1,1,0.0,0.0,0
2128,0,0,0.0,115,5,26,0.0,0.0,0
2129,3,0,0.0,4,0,1,0.0,0.0,0
2130,4,0,0.0,29,2,4,0.0,0.0,0
2131,7,0,0.0,28,0,2,0.0,0.0,0
2132,6,4,811.41,95,7,13,202.85,0.3077,0
2133,13,0,0.0,24,0,3,0.0,0.0,0
2134,3,0,0.0,14,0,3,0.0,0.0,0
2135,7,1,288.98,57,2,7,288.98,0.1429,0
2136,5,0,0.0,25,0,2,0.0,0.0,0
2138,1,0,0.0,4,0,1,0.0,0.0,0
2139,4,0,0.0,55,1,7,0.0,0.0,0
2140,5,0,0.0,88,0,6,0.0,0.0,0
2141,0,0,0.0,10,0,1,0.0,0.0,0
2142,2,0,0.0,7,0,3,0.0,0.0,0
2143,2,0,0.0,14,0,3,0.0,0.0,0
2144,18,0,0.0,10,0,2,0.0,0.0,0
2145,6,0,0.0,3,0,1,0.0,0.0,0
2146,7,2,367.98,27,2,7,183.99,0.2857,1
2148,3,0,0.0,2,0,1,0.0,0.0,0
2149,10,1,7.49,31,2,2,7.49,0.5,0
2150,0,0,0.0,45,1,11,0.0,0.0,0
2151,8,0,0.0,2,0,1,0.0,0.0,0
2153,3,0,0.0,11,0,3,0.0,0.0,0
2154,3,0,0.0,59,1,7,0.0,0.0,0
2155,8,0,0.0,20,1,3,0.0,0.0,0
2157,0,1,30.99,10,1,1,30.99,1.0,0
2158,14,0,0.0,17,1,1,0.0,0.0,0
2160,17,0,0.0,1,0,1,0.0,0.0,0
2161,5,0,0.0,4,0,1,0.0,0.0,0
2162,0,0,0.0,27,0,6,0.0,0.0,0
2163,18,0,0.0,9,0,1,0.0,0.0,0
2164,13,0,0.0,8,1,2,0.0,0.0,0
2165,0,0,0.0,6,0,2,0.0,0.0,0
2168,12,0,0.0,6,0,1,0.0,0.0,0
2169,1,0,0.0,135,2,18,0.0,0.0,0
2170,0,0,0.0,59,3,7,0.0,0.0,0
2171,3,1,181.99,5,1,1,181.99,1.0,0
2172,2,0,0.0,19,0,4,0.0,0.0,0
2173,5,0,0.0,6,0,2,0.0,0.0,0
2175,7,1,68.98,14,3,2,68.98,0.5,0
2176,3,0,0.0,47,0,6,0.0,0.0,0
2177,8,0,0.0,52,0,9,0.0,0.0,0
2179,5,0,0.0,10,1,2,0.0,0.0,0
2180,14,0,0.0,4,0,1,0.0,0.0,0
2182,0,0,0.0,39,2,5,0.0,0.0,0
2183,1,0,0.0,55,0,10,0.0,0.0,0
2184,7,0,0.0,15,0,4,0.0,0.0,0
2185,7,0,0.0,36,2,6,0.0,0.0,0
2186,15,0,0.0,2,0,1,0.0,0.0,0
2188,2,0,0.0,52,0,4,0.0,0.0,0
2189,14,0,0.0,5,0,1,0.0,0.0,0
2190,3,0,0.0,63,1,6,0.0,0.0,0
2192,0,0,0.0,10,0,2,0.0,0.0,0
2193,16,0,0.0,8,0,1,0.0,0.0,0
2194,13,0,0.0,2,0,1,0.0,0.0,0
2195,3,0,0.0,2,0,1,0.0,0.0,0
2196,14,0,0.0,20,1,3,0.0,0.0,0
2198,20,1,89.99,28,2,6,89.99,0.1667,0
2199,19,0,0.0,3,0,1,0.0,0.0,0
2200,0,0,0.0,3,0,3,0.0,0.0,0
2201,6,0,0.0,30,0,3,0.0,0.0,0
2202,18,0,0.0,22,1,4,0.0,0.0,0
2203,2,0,0.0,7,1,3,0.0,0.0,0
2204,14,0,0.0,4,0,2,0.0,0.0,0
2205,18,1,305.64,44,3,6,305.64,0.1667,0
2206,13,0,0.0,4,0,1,0.0,0.0,0
2208,1,0,0.0,41,1,7,0.0,0.0,0
2209,0,0,0.0,63,2,10,0.0,0.0,0
2210,0,0,0.0,25,0,6,0.0,0.0,0
2211,0,0,0.0,12,0,3,0.0,0.0,0
2212,13,0,0.0,7,0,1,0.0,0.0,0
2213,5,1,171.98,75,3,10,171.98,0.1,0
2214,0,1,8.49,15,1,1,8.49,1.0,0
2215,18,0,0.0,9,0,1,0.0,0.0,0
2216,3,4,414.44,89,7,16,103.61,0.25,1
2217,0,0,0.0,33,0,5,0.0,0.0,0
2218,9,0,0.0,26,0,4,0.0,0.0,0
2220,1,0,0.0,20,0,4,0.0,0.0,0
2221,9,0,0.0,2,0,1,0.0,0.0,0
2223,1,0,0.0,38,2,8,0.0,0.0,0
2224,18,1,61.99,36,1,6,61.99,0.1667,1
2225,3,0,0.0,5,0,1,0.0,0.0,0
2226,19,0,0.0,13,0,1,0.0,0.0,0
2227,16,0,0.0,5,0,1,0.0,0.0,0
2228,9,0,0.0,4,0,1,0.0,0.0,0
2229,21,0,0.0,7,0,1,0.0,0.0,0
2230,3,0,0.0,20,0,3,0.0,0.0,0
2231,13,0,0.0,5,0,2,0.0,0.0,0
2232,10,1,19.99,36,1,5,19.99,0.2,0
2233,17,0,0.0,3,0,1,0.0,0.0,0
2234,19,0,0.0,9,1,1,0.0,0.0,0
2235,1,0,0.0,119,1,13,0.0,0.0,0
2237,4,0,0.0,30,2,10,0.0,0.0,0
2238,7,0,0.0,9,0,3,0.0,0.0,0
2239,2,0,0.0,16,0,4,0.0,0.0,0
2240,6,0,0.0,29,0,3,0.0,0.0,0
2241,4,0,0.0,11,0,2,0.0,0.0,0
2243,0,0,0.0,33,0,4,0.0,0.0,0
2244,23,0,0.0,6,1,1,0.0,0.0,0
2245,18,0,0.0,3,0,1,0.0,0.0,0
2246,12,0,0.0,12,1,2,0.0,0.0,0
2247,23,0,0.0,4,0,1,0.0,0.0,0
2248,10,0,0.0,16,1,2,0.0,0.0,0
2249,15,0,0.0,7,0,1,0.0,0.0,0
2250,0,0,0.0,37,2,7,0.0,0.0,0
2251,0,0,0.0,89,4,12,0.0,0.0,0
2252,10,0,0.0,16,0,3,0.0,0.0,0
2253,20,0,0.0,3,0,1,0.0,0.0,0
2254,9,1,67.99,51,2,11,67.99,0.0909,1
2255,21,1,76.99,29,2,8,76.99,0.125,0
2257,4,0,0.0,5,0,1,0.0,0.0,0
2258,10,0,0.0,9,0,2,0.0,0.0,0
2259,1,0,0.0,2,0,1,0.0,0.0,0
2260,22,1,13.99,63,3,7,13.99,0.1429,0
2261,7,0,0.0,2,0,1,0.0,0.0,0
2262,0,0,0.0,16,1,4,0.0,0.0,0
2263,1,0,0.0,24,0,2,0.0,0.0,0
2264,5,0,0.0,4,0,1,0.0,0.0,0
2265,13,2,147.46,51,5,10,73.73,0.2,0
2266,9,1,116.99,14,1,3,116.99,0.3333,0
2269,10,0,0.0,7,2,1,0.0,0.0,0
2270,10,0,0.0,5,0,1,0.0,0.0,0
2271,5,0,0.0,5,0,2,0.0,0.0,0
2272,5,0,0.0,19,1,5,0.0,0.0,0
2273,6,0,0.0,4,0,1,0.0,0.0,0
2274,1,0,0.0,19,0,4,0.0,0.0,0
2277,2,0,0.0,36,2,5,0.0,0.0,0
2278,9,0,0.0,1,0,1,0.0,0.0,0
2279,1,0,0.0,19,0,6,0.0,0.0,0
2280,8,0,0.0,26,0,3,0.0,0.0,0
2282,10,0,0.0,7,0,2,0.0,0.0,0
2283,4,0,0.0,2,0,2,0.0,0.0,0
2285,0,0,0.0,45,1,7,0.0,0.0,0
2286,12,2,25.48,71,3,6,12.74,0.3333,0
2287,21,0,0.0,2,0,1,0.0,0.0,0
2288,12,0,0.0,13,0,1,0.0,0.0,0
2289,6,0,0.0,12,0,5,0.0,0.0,0
2290,4,0,0.0,2,0,1,0.0,0.0,0
2292,2,0,0.0,27,1,5,0.0,0.0,0
2293,6,0,0.0,3,0,1,0.0,0.0,0
2295,8,0,0.0,15,0,3,0.0,0.0,0
2296,15,0,0.0,1,0,1,0.0,0.0,0
2297,0,1,265.99,20,1,4,265.99,0.25,0
2298,5,0,0.0,26,0,3,0.0,0.0,1
2299,20,1,46.99,82,2,14,46.99,0.0714,0
2300,19,0,0.0,3,0,1,0.0,0.0,0
2301,12,0,0.0,6,0,1,0.0,0.0,0
2302,18,0,0.0,6,0,2,0.0,0.0,0
2303,13,0,0.0,9,0,1,0.0,0.0,0
2304,2,0,0.0,30,0,6,0.0,0.0,0
2306,15,0,0.0,1,0,1,0.0,0.0,0
2307,8,1,17.99,158,4,14,17.99,0.0714,0
2308,3,0,0.0,1,0,1,0.0,0.0,0
2309,6,0,0.0,7,0,1,0.0,0.0,1
2310,6,0,0.0,21,0,3,0.0,0.0,0
2311,8,0,0.0,1,0,1,0.0,0.0,1
2313,0,3,469.85,116,7,12,156.62,0.25,0
2314,15,0,0.0,4,0,2,0.0,0.0,0
2316,0,0,0.0,71,3,10,0.0,0.0,1
2317,0,0,0.0,66,3,6,0.0,0.0,0
2318,10,2,92.98,114,4,20,46.49,0.1,1
2319,20,0,0.0,2,0,2,0.0,0.0,0
2320,0,0,0.0,62,0,9,0.0,0.0,0
2321,5,0,0.0,21,0,2,0.0,0.0,0
2322,20,0,0.0,4,1,1,0.0,0.0,0
2324,1,4,201.03,115,8,12,50.26,0.3333,0
2325,13,0,0.0,3,0,1,0.0,0.0,0
2327,1,0,0.0,56,2,5,0.0,0.0,0
2328,0,1,235.99,72,3,10,235.99,0.1,0
2329,0,0,0.0,78,0,9,0.0,0.0,0
2330,2,0,0.0,27,0,4,0.0,0.0,0
2331,0,0,0.0,139,6,18,0.0,0.0,0
2333,18,0,0.0,4,0,1,0.0,0.0,0
2334,1,0,0.0,18,0,3,0.0,0.0,0
2335,9,0,0.0,13,0,2,0.0,0.0,0
2336,13,0,0.0,23,1,4,0.0,0.0,0
2338,2,0,0.0,21,0,5,0.0,0.0,0
2339,6,1,8.49,13,1,3,8.49,0.3333,0
2341,3,0,0.0,37,0,4,0.0,0.0,0
2342,13,0,0.0,37,0,3,0.0,0.0,0
2343,0,0,0.0,35,0,5,0.0,0.0,0
2344,14,0,0.0,11,0,1,0.0,0.0,0
2345,0,0,0.0,6,1,3,0.0,0.0,0
2346,9,0,0.0,6,0,1,0.0,0.0,0
2347,0,0,0.0,27,0,4,0.0,0.0,0
2348,2,0,0.0,14,0,3,0.0,0.0,0
2349,16,0,0.0,5,0,1,0.0,0.0,0
2350,15,0,0.0,16,0,2,0.0,0.0,0
2351,1,0,0.0,104,3,13,0.0,0.0,0
2352,0,0,0.0,32,3,9,0.0,0.0,0
2353,3,0,0.0,62,0,6,0.0,0.0,0
2354,5,0,0.0,28,0,4,0.0,0.0,0
2355,3,0,0.0,5,0,2,0.0,0.0,0
2356,7,0,0.0,51,2,5,0.0,0.0,0
2357,1,0,0.0,5,0,1,0.0,0.0,0
2358,7,0,0.0,6,0,2,0.0,0.0,0
2360,1,2,813.14,166,8,26,406.57,0.0769,0
2362,16,0,0.0,5,0,1,0.0,0.0,0
2363,15,0,0.0,7,0,1,0.0,0.0,0
2364,0,0,0.0,58,0,5,0.0,0.0,0
2365,6,0,0.0,13,0,4,0.0,0.0,0
2366,12,1,34.99,16,1,3,34.99,0.3333,0
2367,21,0,0.0,2,0,1,0.0,0.0,0
2368,7,1,43.48,97,4,11,43.48,0.0909,0
2369,1,0,0.0,70,3,11,0.0,0.0,0
2370,16,0,0.0,6,0,1,0.0,0.0,0
2372,7,0,0.0,6,0,1,0.0,0.0,0
2373,0,0,0.0,43,0,4,0.0,0.0,0
2375,12,2,159.98,87,2,20,79.99,0.1,1
2376,0,0,0.0,51,0,6,0.0,0.0,1
2377,1,0,0.0,28,1,5,0.0,0.0,0
2378,12,1,158.99,21,1,4,158.99,0.25,0
2379,5,0,0.0,2,0,2,0.0,0.0,0
2380,18,0,0.0,2,0,1,0.0,0.0,0
2381,8,1,89.99,27,1,6,89.99,0.1667,0
2382,15,2,97.98,81,2,13,48.99,0.1538,1
2383,8,0,0.0,20,0,5,0.0,0.0,0
2384,19,0,0.0,3,0,1,0.0,0.0,0
2385,0,0,0.0,26,1,7,0.0,0.0,0
2386,12,2,50.98,45,2,5,25.49,0.4,0
2387,0,0,0.0,12,0,5,0.0,0.0,1
2388,4,0,0.0,7,1,2,0.0,0.0,0
2389,13,0,0.0,8,0,2,0.0,0.0,0
2390,9,0,0.0,23,0,2,0.0,0.0,0
2391,3,0,0.0,17,1,4,0.0,0.0,0
2392,18,1,131.26,19,2,6,131.26,0.1667,0
2393,20,0,0.0,20,0,2,0.0,0.0,0
2394,4,0,0.0,11,0,2,0.0,0.0,0
2395,22,0,0.0,3,0,1,0.0,0.0,0
2396,4,0,0.0,27,0,3,0.0,0.0,0
2397,2,0,0.0,8,0,3,0.0,0.0,0
2398,9,0,0.0,5,0,2,0.0,0.0,0
2399,7,0,0.0,11,0,3,0.0,0.0,0
2400,1,0,0.0,54,1,8,0.0,0.0,0
2401,7,1,204.99,55,1,9,204.99,0.1111,0
2402,19,0,0.0,4,0,2,0.0,0.0,0
2403,0,0,0.0,48,1,7,0.0,0.0,0
2404,1,0,0.0,2,0,1,0.0,0.0,0
2405,0,0,0.0,21,0,4,0.0,0.0,0
2406,5,0,0.0,79,0,10,0.0,0.0,0
2407,22,0,0.0,1,0,1,0.0,0.0,0
2408,2,0,0.0,5,0,1,0.0,0.0,0
2410,9,0,0.0,6,0,3,0.0,0.0,0
2411,4,0,0.0,7,0,2,0.0,0.0,0
2412,16,1,60.99,62,2,6,60.99,0.1667,0
2413,4,0,0.0,39,4,7,0.0,0.0,0
2415,21,0,0.0,26,0,1,0.0,0.0,0
2416,19,0,0.0,10,0,3,0.0,0.0,0
2418,21,1,92.99,32,2,4,92.99,0.25,0
2419,1,0,0.0,159,2,22,0.0,0.0,0
2421,3,0,0.0,6,0,1,0.0,0.0,0
2423,0,2,139.98,75,3,13,69.99,0.1538,1
2424,6,0,0.0,11,0,1,0.0,0.0,0
2425,4,0,0.0,5,0,1,0.0,0.0,0
2426,1,0,0.0,82,2,10,0.0,0.0,0
2427,4,0,0.0,26,1,5,0.0,0.0,1
2428,3,0,0.0,13,1,3,0.0,0.0,0
2429,10,0,0.0,2,0,1,0.0,0.0,0
2430,0,0,0.0,27,1,5,0.0,0.0,0
2431,2,0,0.0,2,0,1,0.0,0.0,0
2432,2,0,0.0,7,0,2,0.0,0.0,0
2433,18,0,0.0,2,0,1,0.0,0.0,0
2434,0,0,0.0,22,1,4,0.0,0.0,0
2435,2,0,0.0,81,0,7,0.0,0.0,0
2436,8,0,0.0,22,1,3,0.0,0.0,0
2437,9,0,0.0,3,0,1,0.0,0.0,0
2438,1,0,0.0,47,1,7,0.0,0.0,0
2439,18,1,157.37,72,5,12,157.37,0.0833,0
2440,18,0,0.0,3,1,1,0.0,0.0,0
2441,2,0,0.0,14,0,3,0.0,0.0,0
2442,9,0,0.0,8,0,1,0.0,0.0,0
2443,9,0,0.0,9,0,3,0.0,0.0,0
2445,1,2,76.98,75,2,10,38.49,0.2,0
2446,4,1,46.99,3,1,1,46.99,1.0,0
2447,19,1,15.52,76,2,16,15.52,0.0625,1
2448,3,0,0.0,1,0,1,0.0,0.0,0
2449,10,0,0.0,10,0,3,0.0,0.0,0
2450,19,0,0.0,8,0,1,0.0,0.0,0
2451,14,0,0.0,26,2,2,0.0,0.0,0
2452,3,0,0.0,6,0,2,0.0,0.0,0
2453,4,2,483.97,41,4,11,241.98,0.1818,1
2454,8,0,0.0,7,0,2,0.0,0.0,0
2456,4,0,0.0,9,0,3,0.0,0.0,0
2457,1,0,0.0,31,1,8,0.0,0.0,0
2458,5,0,0.0,4,0,1,0.0,0.0,0
2459,14,0,0.0,21,0,2,0.0,0.0,0
2460,9,0,0.0,6,0,2,0.0,0.0,0
2461,2,1,13.99,99,2,20,13.99,0.05,0
2462,6,0,0.0,13,0,2,0.0,0.0,0
2463,2,0,0.0,47,3,9,0.0,0.0,0
2464,0,0,0.0,28,0,6,0.0,0.0,0
2465,19,1,64.99,24,1,5,64.99,0.2,0
2466,6,1,133.96,45,3,7,133.96,0.1429,1
2467,6,1,8.49,85,2,17,8.49,0.0588,0
2468,1,0,0.0,32,2,6,0.0,0.0,0
2469,3,0,0.0,42,0,5,0.0,0.0,0
2471,5,0,0.0,44,0,5,0.0,0.0,0
2472,2,0,0.0,77,2,16,0.0,0.0,0
2473,18,0,0.0,2,0,1,0.0,0.0,0
2474,0,0,0.0,23,1,5,0.0,0.0,0
2475,16,0,0.0,8,1,1,0.0,0.0,0
2476,1,0,0.0,25,0,3,0.0,0.0,0
2478,0,0,0.0,80,0,10,0.0,0.0,0
2479,9,0,0.0,6,0,2,0.0,0.0,0
2480,0,0,0.0,2,0,1,0.0,0.0,0
2481,9,0,0.0,10,1,1,0.0,0.0,0
2482,3,0,0.0,97,3,10,0.0,0.0,0
2483,13,0,0.0,4,0,1,0.0,0.0,0
2484,2,0,0.0,83,3,11,0.0,0.0,0
2485,14,1,8.49,53,1,8,8.49,0.125,0
2486,20,0,0.0,2,0,1,0.0,0.0,0
2487,19,1,34.99,64,2,7,34.99,0.1429,0
2488,12,0,0.0,1,0,1,0.0,0.0,0
2489,6,0,0.0,72,1,6,0.0,0.0,0
2490,0,0,0.0,5,0,1,0.0,0.0,0
2491,4,0,0.0,5,0,2,0.0,0.0,0
2492,11,0,0.0,3,0,1,0.0,0.0,0
2493,2,0,0.0,13,0,5,0.0,0.0,0
2494,2,0,0.0,33,1,3,0.0,0.0,0
2495,1,0,0.0,7,0,2,0.0,0.0,0
2496,0,0,0.0,54,3,11,0.0,0.0,0
2497,4,0,0.0,7,1,1,0.0,0.0,0
2498,12,0,0.0,26,2,1,0.0,0.0,0
2500,19,1,39.99,108,6,17,39.99,0.0588,0
2502,6,0,0.0,3,0,1,0.0,0.0,0
2503,18,0,0.0,13,0,1,0.0,0.0,0
2504,3,0,0.0,48,1,4,0.0,0.0,0
2505,7,2,223.97,27,4,6,111.98,0.3333,1
2506,1,0,0.0,60,2,8,0.0,0.0,0
2507,1,0,0.0,15,1,2,0.0,0.0,0
2508,3,0,0.0,44,3,5,0.0,0.0,0
2509,7,0,0.0,19,1,2,0.0,0.0,0
2510,2,0,0.0,5,0,2,0.0,0.0,0
2511,8,0,0.0,37,1,4,0.0,0.0,0
2512,3,0,0.0,67,0,10,0.0,0.0,0
2513,20,0,0.0,3,0,1,0.0,0.0,0
2514,20,0,0.0,3,0,2,0.0,0.0,0
2515,15,0,0.0,3,0,1,0.0,0.0,0
2516,2,0,0.0,3,0,1,0.0,0.0,0
2517,8,0,0.0,13,0,2,0.0,0.0,0
2519,19,2,96.98,165,5,18,48.49,0.1111,0
2520,9,0,0.0,22,2,3,0.0,0.0,0
2521,7,0,0.0,7,0,2,0.0,0.0,0
2522,12,0,0.0,3,0,1,0.0,0.0,0
2523,2,0,0.0,28,1,4,0.0,0.0,0
2524,0,0,0.0,41,1,5,0.0,0.0,0
2525,6,1,85.99,19,1,6,85.99,0.1667,0
2526,3,0,0.0,29,0,5,0.0,0.0,0
2528,12,0,0.0,3,0,2,0.0,0.0,0
2529,0,0,0.0,26,0,5,0.0,0.0,0
2530,6,0,0.0,2,0,1,0.0,0.0,0
2531,6,0,0.0,24,0,4,0.0,0.0,0
2532,3,1,74.97,51,1,8,74.97,0.125,0
2533,5,1,9.49,62,1,11,9.49,0.0909,0
2534,22,1,205.98,12,2,1,205.98,1.0,0
2536,7,0,0.0,4,0,1,0.0,0.0,0
2537,21,0,0.0,3,0,1,0.0,0.0,0
2539,3,0,0.0,16,1,6,0.0,0.0,0
2541,0,0,0.0,22,0,4,0.0,0.0,0
2542,3,1,89.99,17,1,4,89.99,0.25,0
2543,21,1,7.76,58,6,8,7.76,0.125,0
2544,1,0,0.0,1,0,1,0.0,0.0,0
2545,4,0,0.0,9,0,3,0.0,0.0,0
2546,20,0,0.0,2,0,1,0.0,0.0,0
2547,0,0,0.0,64,1,14,0.0,0.0,0
2548,1,1,37.99,61,2,5,37.99,0.2,0
2549,2,0,0.0,23,1,5,0.0,0.0,1
2551,10,0,0.0,7,0,1,0.0,0.0,0
2553,5,0,0.0,4,0,2,0.0,0.0,0
2554,17,1,15.99,50,2,6,15.99,0.1667,0
2555,2,0,0.0,13,0,3,0.0,0.0,0
2556,11,1,65.99,70,2,11,65.99,0.0909,0
2557,13,0,0.0,7,0,2,0.0,0.0,0
2558,17,0,0.0,15,1,1,0.0,0.0,0
2559,2,0,0.0,55,4,9,0.0,0.0,0
2560,0,0,0.0,4,0,2,0.0,0.0,0
2561,0,0,0.0,16,0,4,0.0,0.0,0
2562,7,0,0.0,35,1,6,0.0,0.0,0
2563,0,0,0.0,1,0,1,0.0,0.0,0
2565,19,0,0.0,6,1,1,0.0,0.0,0
2566,10,0,0.0,1,0,1,0.0,0.0,0
2567,15,0,0.0,7,0,1,0.0,0.0,0
2568,12,0,0.0,4,0,1,0.0,0.0,0
2569,11,0,0.0,2,0,1,0.0,0.0,0
2570,2,0,0.0,19,0,3,0.0,0.0,0
2571,1,1,34.99,41,1,3,34.99,0.3333,0
2572,21,1,112.17,20,2,5,112.17,0.2,0
2573,10,0,0.0,24,1,4,0.0,0.0,0
2574,19,0,0.0,4,0,1,0.0,0.0,0
2575,11,0,0.0,3,0,1,0.0,0.0,0
2576,0,0,0.0,67,2,9,0.0,0.0,0
2577,10,2,180.98,69,3,9,90.49,0.2222,0
2578,2,0,0.0,9,0,3,0.0,0.0,0
2579,4,0,0.0,37,0,5,0.0,0.0,0
2580,1,2,134.97,54,3,7,67.48,0.2857,1
2581,11,0,0.0,26,2,5,0.0,0.0,0
2582,8,0,0.0,3,0,1,0.0,0.0,0
2583,10,0,0.0,23,0,3,0.0,0.0,0
2586,1,0,0.0,22,1,2,0.0,0.0,0
2587,0,0,0.0,108,0,14,0.0,0.0,0
2588,11,0,0.0,15,1,4,0.0,0.0,0
2589,0,0,0.0,20,0,6,0.0,0.0,0
2590,3,0,0.0,4,0,1,0.0,0.0,0
2592,21,0,0.0,3,0,1,0.0,0.0,0
2593,8,0,0.0,61,0,7,0.0,0.0,0
2595,5,0,0.0,42,1,5,0.0,0.0,0
2596,1,0,0.0,40,2,8,0.0,0.0,0
2597,11,0,0.0,7,0,3,0.0,0.0,0
2598,0,0,0.0,3,0,1,0.0,0.0,0
2600,1,0,0.0,60,2,6,0.0,0.0,0
2601,3,0,0.0,3,0,1,0.0,0.0,0
2602,16,1,84.99,10,1,3,84.99,0.3333,0
2603,20,1,23.99,102,5,10,23.99,0.1,0
2604,7,0,0.0,13,0,2,0.0,0.0,0
2605,7,0,0.0,20,0,3,0.0,0.0,0
2606,1,0,0.0,15,1,2,0.0,0.0,0
2607,23,0,0.0,4,0,1,0.0,0.0,0
2608,7,0,0.0,2,0,1,0.0,0.0,0
2609,7,0,0.0,6,0,1,0.0,0.0,0
2610,20,0,0.0,1,0,1,0.0,0.0,0
2611,22,0,0.0,15,0,1,0.0,0.0,0
2612,13,0,0.0,3,0,1,0.0,0.0,0
2613,6,0,0.0,6,1,3,0.0,0.0,0
2614,20,1,15.52,96,1,15,15.52,0.0667,0
2615,22,0,0.0,7,2,1,0.0,0.0,0
2616,23,0,0.0,2,0,1,0.0,0.0,0
2617,2,0,0.0,29,1,4,0.0,0.0,0
2618,23,0,0.0,3,0,1,0.0,0.0,0
2619,4,0,0.0,29,0,4,0.0,0.0,0
2620,21,1,18.98,101,3,11,18.98,0.0909,0
2621,18,0,0.0,4,0,1,0.0,0.0,0
2622,1,0,0.0,23,0,5,0.0,0.0,0
2623,6,0,0.0,21,1,5,0.0,0.0,0
2624,4,0,0.0,29,0,3,0.0,0.0,0
2625,10,0,0.0,13,0,3,0.0,0.0,0
2626,12,0,0.0,17,0,5,0.0,0.0,0
2627,20,0,0.0,6,0,1,0.0,0.0,0
2628,2,0,0.0,2,0,1,0.0,0.0,0
2629,5,0,0.0,10,0,3,0.0,0.0,0
2630,21,1,314.98,175,3,18,314.98,0.0556,0
2631,4,0,0.0,43,1,6,0.0,0.0,0
2632,14,0,0.0,5,0,1,0.0,0.0,0
2633,15,2,1085.96,47,3,5,542.98,0.4,0
2634,0,0,0.0,15,1,6,0.0,0.0,0
2635,10,0,0.0,4,0,1,0.0,0.0,0
2636,20,1,440.99,23,2,5,440.99,0.2,0
2637,21,1,23.99,40,1,5,23.99,0.2,0
2638,0,0,0.0,41,1,6,0.0,0.0,1
2639,0,0,0.0,9,0,2,0.0,0.0,0
2640,0,0,0.0,22,2,6,0.0,0.0,0
2641,13,0,0.0,22,0,2,0.0,0.0,0
2642,4,0,0.0,20,3,3,0.0,0.0,0
2643,1,0,0.0,10,0,2,0.0,0.0,0
2644,8,0,0.0,4,0,1,0.0,0.0,0
2645,6,0,0.0,12,0,4,0.0,0.0,0
2646,9,0,0.0,4,0,2,0.0,0.0,0
2647,12,0,0.0,2,0,1,0.0,0.0,0
2649,2,0,0.0,12,0,4,0.0,0.0,0
2650,1,0,0.0,20,0,2,0.0,0.0,0
2651,2,0,0.0,9,0,1,0.0,0.0,0
2652,1,0,0.0,56,5,5,0.0,0.0,0
2653,12,0,0.0,3,0,1,0.0,0.0,0
2654,6,0,0.0,37,0,3,0.0,0.0,1
2655,21,0,0.0,5,0,1,0.0,0.0,0
2656,2,0,0.0,12,1,3,0.0,0.0,0
2657,16,0,0.0,1,0,1,0.0,0.0,0
2658,12,0,0.0,2,1,1,0.0,0.0,0
2660,20,1,11.99,49,1,9,11.99,0.1111,0
2661,7,0,0.0,25,1,4,0.0,0.0,0
2663,9,0,0.0,23,0,3,0.0,0.0,0
2664,9,0,0.0,6,0,2,0.0,0.0,0
2665,21,0,0.0,8,0,2,0.0,0.0,0
2667,10,0,0.0,71,3,9,0.0,0.0,0
2669,1,0,0.0,31,1,4,0.0,0.0,0
2670,3,0,0.0,7,0,1,0.0,0.0,0
2671,18,0,0.0,5,0,1,0.0,0.0,0
2672,3,0,0.0,17,0,3,0.0,0.0,0
2673,3,1,227.95,112,5,17,227.95,0.0588,0
2674,8,0,0.0,17,0,2,0.0,0.0,0
2675,3,0,0.0,97,4,9,0.0,0.0,0
2676,1,2,226.97,150,9,22,113.48,0.0909,1
2677,13,0,0.0,6,0,1,0.0,0.0,0
2678,13,0,0.0,7,0,1,0.0,0.0,0
2679,1,0,0.0,11,1,4,0.0,0.0,0
2680,0,0,0.0,46,2,6,0.0,0.0,0
2682,1,0,0.0,10,1,4,0.0,0.0,0
2683,15,1,142.99,53,3,9,142.99,0.1111,0
2684,10,0,0.0,4,0,1,0.0,0.0,0
2685,16,0,0.0,2,0,1,0.0,0.0,0
2686,5,0,0.0,1,0,1,0.0,0.0,0
2687,8,0,0.0,5,0,1,0.0,0.0,0
2688,3,0,0.0,10,1,5,0.0,0.0,0
2689,1,0,0.0,5,0,2,0.0,0.0,0
2690,15,1,540.98,21,3,6,540.98,0.1667,0
2691,5,0,0.0,34,1,3,0.0,0.0,0
2692,0,0,0.0,47,0,7,0.0,0.0,0
2693,2,0,0.0,25,0,5,0.0,0.0,1
2694,5,0,0.0,9,0,1,0.0,0.0,0
2696,9,0,0.0,14,0,1,0.0,0.0,0
2697,17,0,0.0,6,0,2,0.0,0.0,0
2698,23,0,0.0,15,2,1,0.0,0.0,0
2699,0,0,0.0,5,0,1,0.0,0.0,0
2700,19,1,8.92,12,1,1,8.92,1.0,0
2701,8,0,0.0,9,2,1,0.0,0.0,0
2702,5,0,0.0,5,0,2,0.0,0.0,0
2703,16,0,0.0,6,0,1,0.0,0.0,0
2704,22,0,0.0,6,0,1,0.0,0.0,0
2706,5,0,0.0,48,0,7,0.0,0.0,0
2707,1,0,0.0,29,0,6,0.0,0.0,0
2708,19,1,9.49,50,3,10,9.49,0.1,0
2709,11,0,0.0,2,0,1,0.0,0.0,0
2710,11,0,0.0,2,0,1,0.0,0.0,0
2711,0,0,0.0,46,2,6,0.0,0.0,0
2713,0,0,0.0,75,1,10,0.0,0.0,0
2714,8,0,0.0,4,1,2,0.0,0.0,0
2715,18,0,0.0,9,0,1,0.0,0.0,0
2716,12,0,0.0,5,0,2,0.0,0.0,0
2717,7,0,0.0,2,1,1,0.0,0.0,0
2718,4,0,0.0,45,0,4,0.0,0.0,0
2719,0,0,0.0,18,0,2,0.0,0.0,0
2720,18,0,0.0,3,0,1,0.0,0.0,0
2721,7,0,0.0,14,0,2,0.0,0.0,0
2723,5,0,0.0,8,0,3,0.0,0.0,0
2725,20,0,0.0,7,1,1,0.0,0.0,0
2726,12,1,11.99,51,1,10,11.99,0.1,0
2727,8,0,0.0,13,0,4,0.0,0.0,0
2728,15,0,0.0,1,0,1,0.0,0.0,0
2729,0,0,0.0,12,0,3,0.0,0.0,0
2730,16,0,0.0,4,0,1,0.0,0.0,0
2731,9,0,0.0,20,1,3,0.0,0.0,0
2732,12,0,0.0,8,0,1,0.0,0.0,0
2733,21,0,0.0,12,0,1,0.0,0.0,0
2734,7,1,47.98,25,2,5,47.98,0.2,0
2735,4,0,0.0,8,0,3,0.0,0.0,0
2736,12,1,251.99,41,1,5,251.99,0.2,1
2737,4,0,0.0,110,3,9,0.0,0.0,0
2738,20,0,0.0,18,0,2,0.0,0.0,1
2739,13,0,0.0,1,0,1,0.0,0.0,1
2740,18,1,81.97,74,2,9,81.97,0.1111,1
2742,20,0,0.0,32,2,2,0.0,0.0,0
2744,3,0,0.0,10,1,4,0.0,0.0,0
2745,20,1,76.99,44,2,5,76.99,0.2,0
2746,14,1,9.49,76,4,15,9.49,0.0667,0
2747,1,0,0.0,29,0,8,0.0,0.0,0
2748,4,0,0.0,13,0,3,0.0,0.0,0
2749,17,0,0.0,11,0,1,0.0,0.0,0
2750,13,0,0.0,11,0,1,0.0,0.0,0
2751,1,0,0.0,31,2,4,0.0,0.0,0
2753,1,1,51.99,85,2,12,51.99,0.0833,0
2754,15,0,0.0,12,0,2,0.0,0.0,0
2756,0,0,0.0,29,0,6,0.0,0.0,0
2758,6,0,0.0,3,0,1,0.0,0.0,0
2759,9,0,0.0,3,0,1,0.0,0.0,0
2762,3,0,0.0,18,0,5,0.0,0.0,0
2763,0,0,0.0,37,1,9,0.0,0.0,0
2765,13,0,0.0,6,0,1,0.0,0.0,0
2766,16,0,0.0,23,0,1,0.0,0.0,0
2767,14,0,0.0,19,0,5,0.0,0.0,0
2768,8,0,0.0,6,0,1,0.0,0.0,0
2769,14,0,0.0,9,0,1,0.0,0.0,0
2770,13,0,0.0,36,3,1,0.0,0.0,0
2771,10,0,0.0,3,1,1,0.0,0.0,0
2772,1,0,0.0,45,2,7,0.0,0.0,0
2773,13,1,63.98,34,2,3,63.98,0.3333,0
2774,16,2,223.98,46,4,6,111.99,0.3333,0
2775,2,0,0.0,106,0,10,0.0,0.0,0
2776,1,0,0.0,22,0,3,0.0,0.0,0
2777,23,0,0.0,4,0,1,0.0,0.0,0
2778,5,0,0.0,13,0,2,0.0,0.0,0
2779,7,0,0.0,6,0,3,0.0,0.0,0
2780,16,0,0.0,1,0,1,0.0,0.0,0
2781,4,0,0.0,28,1,2,0.0,0.0,0
2782,3,0,0.0,2,0,1,0.0,0.0,0
2783,9,0,0.0,4,0,1,0.0,0.0,0
2784,4,0,0.0,15,0,5,0.0,0.0,0
2785,0,0,0.0,67,2,7,0.0,0.0,0
2786,3,1,17.99,16,1,5,17.99,0.2,0
2787,0,0,0.0,75,3,12,0.0,0.0,0
2788,8,0,0.0,26,0,3,0.0,0.0,0
2790,5,0,0.0,2,0,1,0.0,0.0,0
2791,2,0,0.0,4,0,1,0.0,0.0,0
2794,9,0,0.0,3,0,1,0.0,0.0,0
2795,2,0,0.0,21,0,5,0.0,0.0,0
2796,7,0,0.0,7,0,3,0.0,0.0,0
2797,1,1,14.99,74,4,8,14.99,0.125,0
2799,18,3,56.5,156,6,26,18.83,0.1154,1
2800,11,0,0.0,7,0,1,0.0,0.0,0
2801,4,1,62.98,13,2,2,62.98,0.5,0
2802,18,0,0.0,18,0,2,0.0,0.0,0
2803,3,0,0.0,11,0,5,0.0,0.0,0
2804,0,0,0.0,97,5,12,0.0,0.0,1
2806,7,0,0.0,4,0,1,0.0,0.0,0
2807,3,0,0.0,1,0,1,0.0,0.0,0
2811,2,0,0.0,4,0,1,0.0,0.0,0
2812,4,0,0.0,16,0,2,0.0,0.0,0
2813,4,0,0.0,29,2,3,0.0,0.0,0
2814,1,0,0.0,5,0,2,0.0,0.0,0
2816,10,0,0.0,26,1,3,0.0,0.0,0
2817,2,0,0.0,37,1,4,0.0,0.0,0
2818,6,0,0.0,13,2,3,0.0,0.0,0
2819,16,0,0.0,15,1,2,0.0,0.0,1
2820,11,0,0.0,8,0,2,0.0,0.0,0
2821,14,0,0.0,16,0,3,0.0,0.0,0
2822,1,0,0.0,49,2,4,0.0,0.0,0
2823,1,0,0.0,5,0,1,0.0,0.0,0
2824,19,0,0.0,11,0,2,0.0,0.0,0
2826,1,0,0.0,30,1,5,0.0,0.0,0
2827,8,0,0.0,9,0,2,0.0,0.0,0
2828,13,2,62.39,82,5,11,31.2,0.1818,0
2829,20,0,0.0,3,0,1,0.0,0.0,0
2830,7,0,0.0,6,0,1,0.0,0.0,0
2831,2,0,0.0,45,1,9,0.0,0.0,1
2832,0,0,0.0,37,0,3,0.0,0.0,0
2833,10,0,0.0,4,0,1,0.0,0.0,0
2834,1,0,0.0,17,0,4,0.0,0.0,0
2836,1,0,0.0,15,0,3,0.0,0.0,0
2838,4,0,0.0,1,0,1,0.0,0.0,0
2839,15,0,0.0,6,0,2,0.0,0.0,0
2840,19,0,0.0,17,0,3,0.0,0.0,0
2842,0,0,0.0,5,0,1,0.0,0.0,0
2843,2,0,0.0,11,1,1,0.0,0.0,0
2844,4,0,0.0,48,1,10,0.0,0.0,0
2845,4,0,0.0,64,0,8,0.0,0.0,0
2846,13,1,163.98,72,2,10,163.98,0.1,1
2847,0,0,0.0,20,1,3,0.0,0.0,0
2848,9,0,0.0,1,0,1,0.0,0.0,0
2849,7,0,0.0,28,1,4,0.0,0.0,0
2850,5,0,0.0,16,1,3,0.0,0.0,0
2852,20,2,270.15,92,5,13,135.07,0.1538,0
2853,17,0,0.0,22,1,2,0.0,0.0,0
2854,3,0,0.0,25,2,3,0.0,0.0,0
2855,20,0,0.0,4,0,1,0.0,0.0,0
2856,6,0,0.0,4,0,1,0.0,0.0,0
2857,2,0,0.0,5,0,1,0.0,0.0,0
2858,19,0,0.0,10,0,1,0.0,0.0,0
2859,20,0,0.0,4,0,1,0.0,0.0,0
2860,0,0,0.0,13,0,4,0.0,0.0,0
2861,11,0,0.0,6,1,1,0.0,0.0,0
2862,15,0,0.0,3,0,1,0.0,0.0,0
2863,21,0,0.0,12,3,2,0.0,0.0,0
2866,18,1,265.99,6,1,1,265.99,1.0,0
2867,8,0,0.0,10,0,1,0.0,0.0,0
2868,16,1,23.99,93,1,11,23.99,0.0909,0
2870,5,2,70.97,86,3,15,35.48,0.1333,0
2871,10,0,0.0,26,1,4,0.0,0.0,0
2872,20,1,14.99,98,3,14,14.99,0.0714,0
2873,2,0,0.0,37,0,9,0.0,0.0,1
2874,13,0,0.0,8,0,2,0.0,0.0,0
2875,6,2,421.97,139,5,30,210.98,0.0667,1
2877,2,0,0.0,17,0,3,0.0,0.0,0
2878,7,0,0.0,12,0,1,0.0,0.0,0
2879,1,0,0.0,116,2,13,0.0,0.0,1
2880,4,0,0.0,2,0,1,0.0,0.0,0
2881,10,0,0.0,66,3,10,0.0,0.0,0
2883,2,0,0.0,18,0,3,0.0,0.0,0
2884,19,0,0.0,4,0,1,0.0,0.0,0
2885,10,0,0.0,28,0,2,0.0,0.0,0
2886,2,0,0.0,55,2,9,0.0,0.0,0
2887,1,1,34.99,6,1,1,34.99,1.0,0
2888,22,0,0.0,1,0,1,0.0,0.0,0
2889,15,0,0.0,14,0,2,0.0,0.0,0
2890,18,1,7.76,90,4,10,7.76,0.1,0
2891,9,0,0.0,6,0,2,0.0,0.0,0
2892,1,0,0.0,15,1,1,0.0,0.0,0
2893,4,0,0.0,3,0,1,0.0,0.0,0
2894,6,0,0.0,7,1,2,0.0,0.0,0
2895,22,1,3.49,13,1,4,3.49,0.25,0
2896,0,0,0.0,56,2,8,0.0,0.0,1
2897,0,0,0.0,22,0,3,0.0,0.0,0
2898,8,0,0.0,5,0,1,0.0,0.0,0
2899,1,0,0.0,24,0,3,0.0,0.0,0
2900,0,0,0.0,47,2,9,0.0,0.0,1
2901,2,0,0.0,60,1,11,0.0,0.0,0
2902,12,2,644.95,143,6,20,322.48,0.1,0
2903,19,1,17.99,14,1,4,17.99,0.25,0
2905,0,0,0.0,3,0,3,0.0,0.0,0
2906,5,0,0.0,13,0,3,0.0,0.0,0
2907,7,0,0.0,20,0,3,0.0,0.0,0
2908,2,0,0.0,94,1,12,0.0,0.0,0
2909,20,0,0.0,19,0,3,0.0,0.0,0
2910,6,3,309.74,175,9,28,103.25,0.1071,0
2911,3,0,0.0,2,0,1,0.0,0.0,0
2913,1,0,0.0,19,0,4,0.0,0.0,1
2914,0,0,0.0,22,0,5,0.0,0.0,0
2915,14,0,0.0,5,1,2,0.0,0.0,0
2916,8,0,0.0,3,0,1,0.0,0.0,0
2917,20,2,142.08,36,3,11,71.04,0.1818,1
2918,10,0,0.0,3,0,2,0.0,0.0,0
2919,4,0,0.0,156,4,15,0.0,0.0,1
2920,7,0,0.0,10,1,1,0.0,0.0,0
2921,22,0,0.0,16,0,1,0.0,0.0,0
2922,23,1,56.99,55,3,15,56.99,0.0667,0
2923,1,0,0.0,20,3,5,0.0,0.0,0
2925,3,0,0.0,35,2,13,0.0,0.0,0
2926,1,0,0.0,47,5,10,0.0,0.0,1
2927,0,0,0.0,33,3,6,0.0,0.0,0
2928,2,0,0.0,73,0,8,0.0,0.0,0
2929,20,0,0.0,2,0,1,0.0,0.0,0
2930,20,0,0.0,3,0,1,0.0,0.0,0
2931,20,0,0.0,1,0,1,0.0,0.0,0
2932,0,0,0.0,10,0,1,0.0,0.0,0
2933,17,1,263.99,12,1,1,263.99,1.0,0
2934,4,1,45.99,27,2,6,45.99,0.1667,0
2935,3,0,0.0,34,2,5,0.0,0.0,0
2936,19,1,39.99,11,2,3,39.99,0.3333,0
2939,12,1,25.47,71,1,10,25.47,0.1,0
2940,8,0,0.0,8,0,3,0.0,0.0,0
2941,6,0,0.0,17,2,1,0.0,0.0,0
2942,2,0,0.0,38,2,5,0.0,0.0,0
2943,14,1,71.99,112,4,17,71.99,0.0588,0
2944,7,0,0.0,36,0,5,0.0,0.0,0
2945,13,0,0.0,8,0,1,0.0,0.0,0
2946,20,0,0.0,6,0,1,0.0,0.0,0
2947,11,0,0.0,9,1,2,0.0,0.0,0
2948,5,0,0.0,10,0,4,0.0,0.0,0
2949,7,0,0.0,14,0,2,0.0,0.0,0
2950,2,0,0.0,57,4,11,0.0,0.0,0
2951,2,0,0.0,1,0,1,0.0,0.0,0
2952,17,0,0.0,6,0,1,0.0,0.0,0
2953,5,3,303.95,78,6,10,101.32,0.3,0
2954,10,0,0.0,37,1,4,0.0,0.0,0
2955,0,0,0.0,2,0,1,0.0,0.0,0
2956,4,0,0.0,35,2,5,0.0,0.0,0
2957,11,2,128.98,154,6,19,64.49,0.1053,0
2958,10,1,765.99,76,3,15,765.99,0.0667,1
2959,9,0,0.0,9,0,2,0.0,0.0,0
2960,2,0,0.0,8,0,3,0.0,0.0,0
2961,9,0,0.0,21,0,2,0.0,0.0,0
2962,8,0,0.0,9,0,1,0.0,0.0,0
2963,5,0,0.0,6,0,3,0.0,0.0,0
2964,0,0,0.0,28,1,6,0.0,0.0,0
2965,0,0,0.0,65,1,6,0.0,0.0,0
2966,13,0,0.0,6,0,1,0.0,0.0,0
2967,2,0,0.0,46,2,7,0.0,0.0,1
2968,0,0,0.0,12,1,2,0.0,0.0,0
2969,20,2,408.98,98,4,18,204.49,0.1111,0
2971,1,0,0.0,10,1,3,0.0,0.0,0
2973,10,0,0.0,28,0,3,0.0,0.0,0
2974,1,0,0.0,19,0,7,0.0,0.0,0
2975,2,0,0.0,8,1,1,0.0,0.0,0
2976,2,0,0.0,22,0,7,0.0,0.0,0
2977,6,0,0.0,8,0,2,0.0,0.0,0
2978,2,0,0.0,57,0,8,0.0,0.0,1
2979,7,1,144.99,40,1,5,144.99,0.2,1
2980,2,0,0.0,13,0,2,0.0,0.0,0
2981,10,0,0.0,7,1,1,0.0,0.0,0
2983,11,0,0.0,9,0,1,0.0,0.0,0
2984,14,0,0.0,12,0,2,0.0,0.0,1
2985,1,0,0.0,101,2,13,0.0,0.0,0
2986,2,0,0.0,4,0,1,0.0,0.0,0
2987,7,0,0.0,7,0,3,0.0,0.0,0
2988,5,0,0.0,33,0,6,0.0,0.0,0
2989,4,0,0.0,14,0,4,0.0,0.0,0
2990,3,0,0.0,16,1,3,0.0,0.0,0
2992,6,0,0.0,25,0,3,0.0,0.0,0
2993,13,0,0.0,3,0,1,0.0,0.0,0
2994,18,0,0.0,25,0,3,0.0,0.0,0
2995,6,6,556.41,134,9,19,92.74,0.3158,0
2996,3,0,0.0,14,0,2,0.0,0.0,0
2997,13,1,43.99,27,1,2,43.99,0.5,0
2998,11,0,0.0,3,0,2,0.0,0.0,0
2999,4,0,0.0,36,0,5,0.0,0.0,1
3000,4,0,0.0,27,1,6,0.0,0.0,0
```

### examples/demo\_conversion.py

```
"""Demo: purchase / conversion prediction pipeline (Day 3).

Pokretanje (bilo gde):

    python3 "Day 3/examples/demo_conversion.py"

Prikazuje: clean training dataset (labela iz prediction window-a) -> split ->
skaliranje (fit na trening) -> logistic regression vs random forest -> evaluacija
(confusion matrix/precision/recall/F1) + majority baseline -> leakage vežba
(before/after) -> verovatnoća poznatog i nepoznatog korisnika.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.events import EventStore
from app.data.paths import dataset_path
from app.ml.conversion import (
    CONVERSION_FEATURE_COLUMNS,
    build_training_dataset,
    evaluate_model,
    majority_class_baseline,
    predict_conversion_probability,
    run_leakage_exercise,
    split_dataset,
    train_conversion_model,
)
from app.ml.features import build_customer_features, scale_customer_features

WINDOW_DAYS = 7
TEST_SIZE = 0.3
RANDOM_STATE = 42


def main() -> None:
    print("=== Day 3 — Purchase / Conversion Prediction (demo) ===\n")

    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    events = store.events_dataframe()
    print(f"Događaja: {len(events):,}  porudžbina: {orders['order_id'].nunique():,} ({len(orders):,} stavki)")

    # 1) Clean training dataset (feature-i pre cut-off-a; labela iz window-a)
    dataset = build_training_dataset(
        events, orders, window_days=WINDOW_DAYS, leaky=False
    )
    pos = int(dataset["will_purchase"].sum())
    print(f"\n[1] Clean training dataset: {len(dataset):,} korisnika, "
          f"pozitivnih (kupovina u {WINDOW_DAYS}-dnevnom window-u): {pos} "
          f"({pos / len(dataset):.1%})")
    print(dataset.head(5).to_string(index=False))

    # 2) Split + skaliranje (scaler fit na TREINING splitu)
    train_df, test_df = split_dataset(dataset, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    scaled_train, scaler = scale_customer_features(train_df, CONVERSION_FEATURE_COLUMNS)
    scaled_test, _ = scale_customer_features(test_df, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
    print(f"\n[2] Split: train={len(train_df)}, test={len(test_df)} "
          f"(pozitivnih u testu: {int(test_df['will_purchase'].sum())})")

    # 3) Logistic regression vs random forest (ista podešavanja, isti split)
    baseline = majority_class_baseline(test_df["will_purchase"].to_numpy())
    print("\n[3] Majority-class baseline (predict 0 za sve):")
    print(f"    accuracy={baseline['accuracy']}  precision/recall/F1="
          f"{baseline['precision']}/{baseline['recall']}/{baseline['f1']} "
          f"(0 — baseline nikog ne proglašava pozitivnim)")
    for model_type in ("logistic_regression", "random_forest"):
        model = train_conversion_model(
            scaled_train.to_numpy(),
            train_df["will_purchase"].to_numpy(),
            model_type=model_type,
            random_state=RANDOM_STATE,
        )
        m = evaluate_model(model, scaled_test.to_numpy(), test_df["will_purchase"].to_numpy())
        print(f"    {model_type:>19}: accuracy={m['accuracy']} precision={m['precision']} "
              f"recall={m['recall']} F1={m['f1']}")

    # 4) Leakage vežba: clean vs leaky feature-i
    print("\n[4] Leakage vežba (isti model, isti split):")
    leakage = run_leakage_exercise(
        events, orders, window_days=WINDOW_DAYS,
        test_size=TEST_SIZE, random_state=RANDOM_STATE, model_type="logistic_regression",
    )
    c, l = leakage["clean"], leakage["leaky"]
    print(f"    clean (feature-i pre cut-off-a): accuracy={c['accuracy']} precision={c['precision']} "
          f"recall={c['recall']} F1={c['f1']}")
    print(f"    leaky (feature-i iz cele istorije): accuracy={l['accuracy']} precision={l['precision']} "
          f"recall={l['recall']} F1={l['f1']}")
    print(f"    delta_F1 = {leakage['delta_f1']:+.3f} — leaky izgleda bolje jer VARA "
          "(feature-i vide budućnost)")

    # 5) Verovatnoća jednog korisnika (iste feature definicije kao trening)
    print("\n[5] Verovatnoća kupovine (scaler transform-only, cut-off kao trening):")
    reference = pd.to_datetime(pd.concat(
        [events["timestamp"], orders["timestamp"]]
    )).max()
    cutoff = reference - pd.Timedelta(days=WINDOW_DAYS)
    model = train_conversion_model(
        scaled_train.to_numpy(), train_df["will_purchase"].to_numpy(),
        model_type="logistic_regression", random_state=RANDOM_STATE,
    )
    for uid in (2, 999999):
        ev2 = events[pd.to_datetime(events["timestamp"]) < cutoff]
        od2 = orders[pd.to_datetime(orders["timestamp"]) < cutoff]
        cust_ev = ev2[ev2["user_id"] == uid]
        cust_od = od2[od2["user_id"] == uid]
        if len(cust_ev) == 0 and len(cust_od) == 0:
            print(f"    user {uid:>7}: P(will_purchase) = {dataset['will_purchase'].mean():.4f} "
                  "(fallback base_rate — bez istorije pre cut-off-a)")
            continue
        feats = build_customer_features(cust_ev, cust_od, reference=cutoff)
        scaled_row, _ = scale_customer_features(feats, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        prob = predict_conversion_probability(model, scaled_row.iloc[0])
        print(f"    user {uid:>7}: P(will_purchase) = {prob:.4f}")

    print("\nGotovo. Vizualizacija: python3 \"Day 3/examples/visualize_confusion.py\"")


if __name__ == "__main__":
    main()
```

### examples/visualize\_confusion.py

```
"""Vizualizacija: confusion matrice clean vs leaky modela (Day 3).

Pokretanje (bilo gde):

    python3 "Day 3/examples/visualize_confusion.py"

Gradi clean i leaky training dataset-e (isti split, isti model), trenira oba i
crtá confusion matrice jedna pored druge u ``confusion_clean_vs_leaky.png``
(pored ``examples/``). Crveni znak: leaky model izgleda „savršeno" jer vidi
budućnost — ne zato što je dobar.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.data.events import EventStore
from app.data.paths import dataset_path
from app.ml.conversion import (
    CONVERSION_FEATURE_COLUMNS,
    build_training_dataset,
    evaluate_model,
    split_dataset,
    train_conversion_model,
)
from app.ml.features import scale_customer_features

WINDOW_DAYS = 7
TEST_SIZE = 0.3
RANDOM_STATE = 42
OUT_PNG = Path(__file__).resolve().parent / "confusion_clean_vs_leaky.png"


def main() -> None:
    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    events = store.events_dataframe()

    clean = build_training_dataset(events, orders, window_days=WINDOW_DAYS, leaky=False)
    leaky = build_training_dataset(events, orders, window_days=WINDOW_DAYS, leaky=True)
    clean_users = set(clean["user_id"])
    leaky = leaky[leaky["user_id"].isin(clean_users)].reset_index(drop=True)

    train_df, test_df = split_dataset(clean, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_users = set(train_df["user_id"])
    test_users = set(test_df["user_id"])

    def _fit_eval(df: pd.DataFrame):
        tr = df[df["user_id"].isin(train_users)].reset_index(drop=True)
        te = df[df["user_id"].isin(test_users)].reset_index(drop=True)
        scaled_tr, scaler = scale_customer_features(tr, CONVERSION_FEATURE_COLUMNS)
        scaled_te, _ = scale_customer_features(te, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        model = train_conversion_model(
            scaled_tr.to_numpy(), tr["will_purchase"].to_numpy(),
            model_type="logistic_regression", random_state=RANDOM_STATE,
        )
        return evaluate_model(model, scaled_te.to_numpy(), te["will_purchase"].to_numpy())

    clean_m = _fit_eval(clean)
    leaky_m = _fit_eval(leaky)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    panels = [
        (f"Clean (feature-i pre cut-off-a)\nF1={clean_m['f1']}, recall={clean_m['recall']}", clean_m),
        (f"Leaky (feature-i iz cele istorije)\nF1={leaky_m['f1']}, recall={leaky_m['recall']}", leaky_m),
    ]
    for ax, (title, m) in zip(axes, panels):
        cm = m["confusion_matrix"]
        ax.imshow(cm, cmap="Blues", interpolation="nearest")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i][j]), ha="center", va="center", fontsize=16)
        ax.set_xticks([0, 1], ["pred 0", "pred 1"])
        ax.set_yticks([0, 1], ["stvarno 0", "stvarno 1"])
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Predviđeno")
        ax.set_ylabel("Stvarno")
    fig.suptitle("Day 3 — confusion matrix: clean vs leaky model", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Sačuvano: {OUT_PNG}")
    print(f"clean F1={clean_m['f1']}  leaky F1={leaky_m['f1']} "
          f"(leaky je bolji jer VARA — feature-i vide window)")


if __name__ == "__main__":
    main()
```

### lab/README.md

# Lab — Dan 3: labeled training dataset, split, evaluacija i fallback

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne menjaš
`dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas`, `numpy`, `scikit-learn` (`dm-ml/.venv` ih ima).
* Seeded dataset: `Day 1/data/events.csv` + `orders.csv` (jedini izvor istine).

## Zadatak (koraci)

1. **`build_training_dataset(events, orders, window_days=7, leaky=False)`** —
   labeled dataset po korisniku:

   * **cutoff** = `reference − window_days` (reference = najskoriji događaj/
     porudžbina).
   * **Labela** `will_purchase`: 1 ako je korisnik kupio u `[cutoff, reference]`, inače 0.
   * **Clean** (`leaky=False`): feature-i se računaju SAMO na istoriji *pre*
     cutoff-a (sa `reference=cutoff` za recency) — model ne sme da vidi window.
   * **Leaky** (`leaky=True`): feature-i iz CELE istorije (uključujući window)
     — namerni bug za vežbu.
   * Vrati DataFrame: `user_id`, feature kolone (`FEATURE_COLUMNS`),
     `will_purchase`.
2. **`split_dataset(df, test_size=0.3, random_state=42)`** — stratifikovan
   train/test split po `will_purchase` (isti udeo pozitivnih u oba skupa);
   resetuj indekse.
3. **`evaluate_model(model, X, y)`** — vrati dict: `accuracy`, `precision`,
   `recall`, `f1`, `confusion_matrix` ([[tn, fp], [fn, tp]]), `n`. Koristi
   `sklearn.metrics` sa `zero_division=0`.
4. **`predict_conversion_probability(model, scaled_row)`** — vrati
   verovatnoću `will_purchase=1` (zaokruži na 4 decimale):

   * `model is None` -> `ValueError` („model not trained").
   * prazan `scaled_row` -> `ValueError` („prazna feature vrsta").

## Provera

```
# iz Day 3/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: definiciju labele + temporalni window + leaky flag, stratifikovan
  split, evaluaciju (confusion/P/R/F1) i untrained fallback.
* Ne radiš: celokupan `dm-ml` servis, API, perzistenciju modela, skaliranje —
  to koristi tvoje funkcije u `app/ml/` i servisu. Feature builder
  (`build_features`) je dat u `starter.py` (to je Day 2 materijal).

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.

### lab/starter.py

```
"""Starter za Day 3 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 3/lab/``):

    python3 -m pytest test_lab.py                # tvoj starter
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # rešenje
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# Feature kolone modela (numeričke). ``build_features`` je DATA (Day 2
# materijal) — ne implementiraš je.
FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "product_views",
    "cart_adds",
    "sessions",
    "aov",
    "conversion",
]
LABEL_COLUMN = "will_purchase"


def build_features(
    events_df: pd.DataFrame,
    orders_df: Optional[pd.DataFrame] = None,
    reference=None,
) -> pd.DataFrame:
    """Pojednostavljena feature tabela po korisniku (data — ne implementiraš je).

    Vraća ``user_id`` + ``FEATURE_COLUMNS``. Ako je ``reference`` dat, recency
    se računa u odnosu na njega (inače na max timestamp prosleđenih podataka).
    """
    orders_df = pd.DataFrame() if orders_df is None else orders_df
    if reference is None:
        parts = []
        if len(events_df):
            parts.append(pd.to_datetime(events_df["timestamp"]))
        if len(orders_df):
            parts.append(pd.to_datetime(orders_df["timestamp"]))
        reference = pd.concat(parts).max() if parts else pd.NaT
    if pd.isna(reference):
        return pd.DataFrame(columns=["user_id"] + FEATURE_COLUMNS)

    users = pd.concat(
        [events_df["user_id"], orders_df["user_id"]]
    ).dropna().astype("int64").unique()

    # recency: poslednja kupovina / poslednja aktivnost (ili najhladniji fallback)
    act = (
        events_df.assign(_ts=pd.to_datetime(events_df["timestamp"]))
        .groupby("user_id")["_ts"].max()
        if len(events_df)
        else pd.Series(dtype="datetime64[ns]")
    )
    if len(orders_df):
        od = orders_df.assign(
            _ts=pd.to_datetime(orders_df["timestamp"]),
            _tot=pd.to_numeric(orders_df["total_price"], errors="coerce").fillna(0.0),
        ).groupby("user_id")
        last_buy = od["_ts"].max()
        frequency = od.size().astype("int64")
        monetary = od["_tot"].sum()
    else:
        last_buy = pd.Series(dtype="datetime64[ns]")
        frequency = pd.Series(dtype="int64")
        monetary = pd.Series(dtype="float64")

    window_start = pd.to_datetime(events_df["timestamp"]).min() if len(events_df) else reference
    rows = []
    for uid in users:
        uid = int(uid)
        lb = last_buy.get(uid, pd.NaT)
        la = act.get(uid, pd.NaT)
        if pd.notna(lb):
            recency = int((reference - lb).days)
        elif pd.notna(la):
            recency = int((reference - la).days)
        else:
            recency = int((reference - window_start).days) + 1
        rows.append({
            "user_id": uid,
            "recency_days": recency,
            "frequency": int(frequency.get(uid, 0)),
            "monetary": round(float(monetary.get(uid, 0.0)), 2),
        })
    base = pd.DataFrame(rows)

    # brojači + AOV + konverzija
    if len(events_df):
        counts = events_df.assign(
            _view=(events_df["event_type"] == "product_view"),
            _cart=(events_df["event_type"] == "add_to_cart"),
        ).groupby("user_id").agg(
            product_views=("_view", "sum"),
            cart_adds=("_cart", "sum"),
            sessions=("user_session", "nunique"),
        )
        buy_sessions = (
            events_df[events_df["event_type"] == "purchase"]
            .groupby("user_id")["user_session"].nunique()
        )
        base = base.merge(counts, on="user_id", how="left")
        base["product_views"] = base["product_views"].fillna(0).astype("int64")
        base["cart_adds"] = base["cart_adds"].fillna(0).astype("int64")
        base["sessions"] = base["sessions"].fillna(0).astype("int64")
        base["aov"] = np.where(base["frequency"] > 0, base["monetary"] / base["frequency"], 0.0)
        base["aov"] = base["aov"].round(2)
        base["conversion"] = (
            base["user_id"].map(buy_sessions).fillna(0).astype("int64") / base["sessions"]
        ).round(4)
        base["conversion"] = base["conversion"].where(base["sessions"] > 0, 0.0)
    else:
        base["product_views"] = 0
        base["cart_adds"] = 0
        base["sessions"] = 0
        base["aov"] = 0.0
        base["conversion"] = 0.0
    return base[["user_id"] + FEATURE_COLUMNS]


def build_training_dataset(
    events_df: pd.DataFrame,
    orders_df: Optional[pd.DataFrame] = None,
    window_days: int = 7,
    leaky: bool = False,
) -> pd.DataFrame:
    """Gradi labeled training dataset po korisniku. TODO: implementirati.

    Zahtevi (definicije su deo zadatka — moraju biti eksplicitne):
    - **cutoff** = ``reference - window_days``, gde je ``reference`` najskoriji
      događaj/porudžbina u datasetu.
    - **Labela** ``will_purchase``: 1 ako je korisnik kupio u ``[cutoff,
      reference]``, inače 0.
    - **Clean** (``leaky=False``): feature-i SAMO na istoriji pre ``cutoff``-a
      (``build_features`` pozovi sa ``reference=cutoff``) — model NE SME da
      vidi window.
    - **Leaky** (``leaky=True``): feature-i iz CELE istorije (``reference``).
    - Vrati DataFrame ``user_id`` + ``FEATURE_COLUMNS`` + ``will_purchase``
      (bez indeksa sortiran po ``user_id``).
    """
    raise NotImplementedError("implementiraj build_training_dataset")


def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.3,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stratifikovan train/test split po labeli. TODO: implementirati.

    Zahtevi:
    - ``LABEL_COLUMN`` mora postojati (inače ``ValueError``).
    - ``train_test_split`` sa ``stratify=df[LABEL_COLUMN]`` i istim
      ``random_state`` -> deterministički.
    - Vrati ``(train_df, test_df)`` sa resetovanim indeksima.
    """
    raise NotImplementedError("implementiraj split_dataset")


def train_conversion_model(X_train, y_train, model_type="logistic_regression", random_state=42):
    """Trenira klasifikator (data — ne implementiraš je).

    ``model_type``: ``logistic_regression`` ili ``random_forest``.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    X = np.asarray(X_train)
    y = np.asarray(y_train)
    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=2000, random_state=random_state)
    elif model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=200, random_state=random_state)
    else:
        raise ValueError(f"nepoznat model_type: {model_type!r}")
    model.fit(X, y)
    return model


def evaluate_model(model, X, y) -> dict:
    """Evaluacija: accuracy + confusion matrix + precision/recall/F1. TODO: implementirati.

    Zahtevi:
    - ``model.predict(X)`` -> predikcije.
    - Vrati dict: ``accuracy``, ``precision``, ``recall``, ``f1``
      (``sklearn.metrics`` sa ``zero_division=0``), ``confusion_matrix``
      ([[tn, fp], [fn, tp]]), ``n``. Vrednosti zaokruži na 4 decimale.
    """
    raise NotImplementedError("implementiraj evaluate_model")


def predict_conversion_probability(model, scaled_row) -> float:
    """Verovatnoća ``will_purchase=1`` za jednu skaliranu vrstu. TODO: implementirati.

    Zahtevi (failure handling je deo kursa):
    - ``model is None`` -> ``ValueError`` („model not trained").
    - ``scaled_row`` je ``None`` ili prazan -> ``ValueError`` („prazna feature
      vrsta").
    - inače -> ``round(model.predict_proba(X)[0, 1], 4)``.
    """
    raise NotImplementedError("implementiraj predict_conversion_probability")
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
from sklearn.preprocessing import StandardScaler

D1 = Path(__file__).resolve().parents[2] / "Day 1" / "data"


@pytest.fixture(scope="module")
def seed():
    return pd.read_csv(D1 / "events.csv"), pd.read_csv(D1 / "orders.csv")


def test_clean_dataset_matches_lesson(seed):
    ds = lab.build_training_dataset(*seed, window_days=7)
    assert len(ds) == 2579 and int(ds[lab.LABEL_COLUMN].sum()) == 163
    assert list(ds.columns) == ["user_id"] + lab.FEATURE_COLUMNS + [lab.LABEL_COLUMN]


def test_leaky_differs(seed):
    clean = lab.build_training_dataset(*seed, leaky=False).set_index("user_id")
    leaky = lab.build_training_dataset(*seed, leaky=True).set_index("user_id")
    common = clean.index.intersection(leaky.index)
    assert (leaky.loc[common, "frequency"] >= clean.loc[common, "frequency"]).all()
    assert (leaky.loc[common, "frequency"] > clean.loc[common, "frequency"]).any()


def test_split_and_evaluate(seed):
    ds = lab.build_training_dataset(*seed)
    tr, te = lab.split_dataset(ds)
    assert len(te) == 774 and abs(tr[lab.LABEL_COLUMN].mean() - te[lab.LABEL_COLUMN].mean()) < 0.01
    with pytest.raises(ValueError):
        lab.split_dataset(ds.drop(columns=[lab.LABEL_COLUMN]))
    sc = StandardScaler().fit(tr[lab.FEATURE_COLUMNS])
    m = lab.train_conversion_model(sc.transform(tr[lab.FEATURE_COLUMNS]), tr[lab.LABEL_COLUMN])
    ev = lab.evaluate_model(m, sc.transform(te[lab.FEATURE_COLUMNS]), te[lab.LABEL_COLUMN])
    assert ev["n"] == 774 and sum(map(sum, ev["confusion_matrix"])) == 774
    p = lab.predict_conversion_probability(m, sc.transform(te[lab.FEATURE_COLUMNS])[0])
    assert 0 <= p <= 1
    with pytest.raises(ValueError):
        lab.predict_conversion_probability(None, [1.0])
    with pytest.raises(ValueError):
        lab.predict_conversion_probability(m, [])
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 3 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from starter import FEATURE_COLUMNS, LABEL_COLUMN, build_features, train_conversion_model  # noqa: F401


def build_training_dataset(events_df, orders_df=None, window_days=7, leaky=False):
    orders_df = pd.DataFrame(columns=["user_id", "timestamp", "total_price"]) if orders_df is None else orders_df
    ev_t = pd.to_datetime(events_df["timestamp"]); od_t = pd.to_datetime(orders_df["timestamp"])
    reference = pd.concat([ev_t, od_t]).max()
    cutoff = reference - pd.Timedelta(days=window_days)
    buyers = set(orders_df.loc[(od_t >= cutoff) & (od_t <= reference), "user_id"].astype(int))
    if leaky:
        feats = build_features(events_df, orders_df, reference=reference)
    else:
        feats = build_features(events_df[ev_t < cutoff], orders_df[od_t < cutoff], reference=cutoff)
    feats[LABEL_COLUMN] = feats["user_id"].isin(buyers).astype(int)
    return feats.sort_values("user_id").reset_index(drop=True)


def split_dataset(df, test_size=0.3, random_state=42):
    if LABEL_COLUMN not in df.columns:
        raise ValueError(f"nedostaje {LABEL_COLUMN}")
    tr, te = train_test_split(df, test_size=test_size, random_state=random_state, stratify=df[LABEL_COLUMN])
    return tr.reset_index(drop=True), te.reset_index(drop=True)


def evaluate_model(model, X, y):
    p = model.predict(np.asarray(X)); y = np.asarray(y)
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    r4 = lambda v: round(float(v), 4)
    return {"accuracy": r4(accuracy_score(y, p)), "precision": r4(precision_score(y, p, zero_division=0)),
            "recall": r4(recall_score(y, p, zero_division=0)), "f1": r4(f1_score(y, p, zero_division=0)),
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]], "n": int(len(y))}


def predict_conversion_probability(model, scaled_row):
    if model is None:
        raise ValueError("model not trained")
    if scaled_row is None or len(scaled_row) == 0:
        raise ValueError("prazna feature vrsta")
    X = np.asarray(scaled_row, dtype=float).reshape(1, -1)
    return round(float(model.predict_proba(X)[0, 1]), 4)
```
