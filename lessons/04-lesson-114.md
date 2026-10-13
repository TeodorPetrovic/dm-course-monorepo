# Dan 4 — ML-Assisted Campaign Targeting

- lesson_id: 114
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:46.480 updated: 2026-09-05 20:00:28.457
- summary: Verovatnoća 0.92 nije odluka. Kombinovanje predikcije (Day 3) + segmenta (Day 2) + vrednosti korisnika + pravila kampanje u rangiranu publiku — i razlika „model kaže" vs „šaljemo". [subjects-import]


---

<!-- page_id 418 order 0 -->
## [Page] Materijal

# Dan 4 — ML-Assisted Campaign Targeting

> *Verovatnoća 0.92 nije odluka. Kombinovanje predikcije (Day 3) + segmenta
> (Day 2) + vrednosti korisnika + pravila kampanje u **rangiranu publiku** —
> i razlika „model kaže" vs „šaljemo".*

## Šta gradimo

Servis za targeting kampanja koji kombinuje **verovatnoću kupovine** (Day 3),
**segment** (Day 2), **vrednost korisnika** i **pravila kampanje** (eligibilnost,
kontakt limit, cena) u **preporučenu publiku**: `score_customer` →
`select_target_customers` → `rank_target_customers`, izloženo kroz
`GET /campaigns/{id}/recommended-audience`. Cilj dana je da razdvoji
**predikciju** (model kaže „P=0.73") od **odluke** („šaljemo, jer je
očekivana vrednost pozitivna pod pravilima").

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `score_customer` | **machine learning + rule / heuristic** (spaja predikciju i pravila) |
| `select_target_customers` | **rule / heuristic** (primenjuje pravila na profil) |
| `rank_target_customers` | **rule / heuristic** (rangira po skoru + limita) |
| `rule_based_score` / `rank_by_rule` | **rule / heuristic** (baseline bez ML-a) |
| `compare_rule_vs_ml` | **rule / heuristic** (poređenje audience) |

## Application requirement

Postojeći e-commerce sistem (Nuxt CMS `dm-frontend` + FastAPI `dm-ml`) ima
događaje (Day 1), segmente (Day 2) i verovatnoću kupovine (Day 3). Da bi
marketing *poslao* kampanju, treba da odluči **kome i po kom redosledu** —
i da objasni zašto (razlozi u publici). Day 3 kaže „ovaj korisnik će sa
verovatnoćom p kupiti"; Day 4 pretvara to u **odluku** pod eksplicitnim
pravilima: ciljani segmenti, dozvoljeni bucket-i, prag verovatnoće, prag
vrednosti, cena kontakta, kontakt limit. **Predikcija je ulaz u odluku, ne
odluka.**

## Ciljevi učenja

Do kraja dana treba da:

* razlikujete **predikciju** („P=0.73") od **odluke** („šaljemo") i date primer
  gde korisnik sa najvećom verovatnoćom NIJE najbolja odluka;
* kombinujete verovatnoću + segment + vrednost + pravila u **skor odluke**
  (očekivana vrednost `P × vrednost − cena`);
* primenite pravila kampanje kao **eksplicitna ograničenja** (eligibilnost,
  kontakt limit, budžet) — ne kao skor;
* rangirate publiku po skoru i objasnite zašto rangiranje po verovatnoći nije
  dovoljno;
* poredite **rule-based** targeting („svi visoki RFM") sa **ML-assisted** i
  izračunate kvalitet publike (očekivane konverzije, očekivani profit, lift);
* definišete **fallback za netreniran model** (rule publika sa `fallback=true`,
  ne tihi `[]`/`None`).

## Preduslovi

Day 2 segmenti (K-Means + RFM bucketi), Day 3 verovatnoća kupovine (trenirani
model), pandas/sklearn osnove, FastAPI (Day 1–3 rute).

## Postojeći sistem (šta nasleđujemo)

* **Day 1 sloj:** `POST /events`, analitika, seeded dataset (3000 korisnika,
  183.468 događaja, 893 porudžbine).
* **Day 2 sloj:** feature-i po korisniku (RFM + brojači + AOV + konverzija),
  K-Means segmentacija (k=4, silhouette 0.5726) + ručni RFM bucketi,
  `SegmentationService`.
* **Day 3 sloj:** clean training dataset, klasifikator sa verovatnoćama,
  evaluacija + majority baseline, persistencija modela, `ConversionService`.
* **Nedostaje:** bilo kakva *odluka* — „kome poslati kampanju". Day 3 vraća
  verovatnoću; Day 4 je pretvara u rangiranu publiku sa razlozima i pravilima.

## Arhitektura

```
Day 2 segment (kmeans.joblib + scaler)   Day 3 verovatnoća (model.joblib + scaler)
      │                                         │
      ▼                                         ▼
app/ml/targeting.py      score_customer (eligibilnost + očekivana vrednost)
                         select_target_customers (pravila -> kandidati)
                         rank_target_customers (skor + limita -> top-N)
                         rule_based_score / rank_by_rule (baseline)
                         compare_rule_vs_ml (poređenje)
      │
      ▼
app/services/targeting.py   TargetingService (ML profil ILI rule fallback; kampanje)
      │
      ▼
app/api/campaign_routes.py  GET /campaigns  GET /campaigns/{id}
                            GET /campaigns/{id}/recommended-audience
                            GET /campaigns/{id}/targeting-comparison
      │
      ▼
dm-frontend admin /campaigns   Nuxt admin (Nitro proxy /ml/** -> :3001)
```

## Korišćeni podaci

**Kampanje** (seeded, `Day 4/data/campaigns.csv`, jedini izvor:
`app/data/campaigns.py`) — 4 kampanje sa pravilima:

| ID | Kampanja | Ciljani segmenti | Dozvoljeni bucketi | Prag P | Min vrednost | Cena | Max kontakti |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | VIP reaktivacija | segment\_2, segment\_3 | champions, loyal | 0.20 | 50.0 | 0.5 | 200 |
| 2 | At-risk win-back | segment\_0 | at\_risk | 0.15 | 0.0 | 0.3 | 300 |

Brojevi K-Means segmenata su proizvoljni (zavise od seed-a i podataka): ovde su `segment_2`
(VIP) i `segment_3` (redovni kupci) najvredniji, a `segment_0` ima najduži recency. Ako
regenerišeš podatke, proveri profile (`GET /segments`) i ažuriraj `target_segments`.
| 3 | Široka visoko-vrednosna | — (svi) | champions, loyal, at\_risk | 0.10 | 0.0 | 0.2 | 500 |
| 4 | Dormant re-engage (pravila) | — (svi) | dormant | 0.00 | 0.0 | 0.1 | 150 |

**Targeting profil** (izveden, `Day 4/data/customer_profiles.csv`) — 2579
korisnika sa istorijom pre cut-off-a: K-Means segment (Day 2, k=4, seed 42),
RFM bucket (pravilo), verovatnoća (Day 3, logistic\_regression, seed 42),
`monetary` (istorijska vrednost), RFM komponente, AOV, konverzija, omiljena
kategorija. Stanje: kupaca **571**; po bucket-u `dormant` 1623 · `at_risk` 716 ·
`loyal` 159 · `champions` 81; po segmentu `segment_1` 1468 · `segment_0` 720 ·
`segment_3` 344 · `segment_2` 47.

## AI-ML koncept

* **Prediction vs decision.** Day 3 model vraća `P(will_purchase)` — to je
  predikcija. Odluka „šaljemo" zavisi i od *vrednosti* korisnika, *cene*
  kontakta i *pravila* kampanje. Skor odluke je **očekivana vrednost**:
  `P × vrednost − cena_po_kontaktu`. U kampanji 1 korisnik 2875 ima P=0.82 i
  vrednost 442.96 → skor 362.8; korisnik 1067 ima P=0.28 i vrednost 1342.90 → skor
  373.8 — **veća verovatnoća ne znači bolja odluka.**
* **Pravila kao ograničenja.** Ciljani segmenti, dozvoljeni bucket-i, prag
  verovatnoće i prag vrednosti su **eligibilnost** — korisnik ili ispunjava
  pravila (ušao u publiku) ili ne (0 skor, ali sa razlogom zašto). Pravila
  nisu deo skora; to je razlika između *filtra* i *rangiranja*.
* **Contact limit / kapacitet.** Kampanja ima `max_contacts` (koliko ljudi
  sme da kontaktira) — `limit` iz upita se klipuje na njega. Kapacitet je
  eksplicitno ograničenje, ne „soft" skor.
* **Očekivana vrednost i lift.** Kvalitet publike merimo očekivanim
  konverzijama (suma verovatnoća), očekivanim profitom (suma
  `P×vrednost − cena`) i **lift-om** (odnos ML/rule konverzija).
* **Rule baseline.** `rule_based_score` = prioritet bucket-a (champions 4 >
  loyal 3 > at\_risk 2 > dormant 1) × 1e6 + vrednost — rangira „visoke RFM
  korisnike" **bez** ijedne verovatnoće. ML-assisted koristi verovatnoću +
  vrednost; poređenje pokazuje šta ML dodaje.

## Implementacija (koraci)

Moduli su u `dm-ml/app/`; radni tok ispod.

### Korak 1 — Skor odluke (`app/ml/targeting.py`)

`score_customer(probability, segment, rfm_bucket, monetary, campaign)`:

* `evaluate_campaign_rules(...)` proverava **eligibilnost** (ciljani segmenti,
  dozvoljeni bucket-i, prag verovatnoće, prag vrednosti) i vraća razloge —
  jedina definicija pravila, deljena sa select/rank (ne mogu da se razmimođu).
* Neeligibilan -> `{"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": [...]}` (razlozi kažu ZAŠTO nije ušao).
* Eligibilan -> `expected_value = round(P × monetary − cost_per_contact, 4)`;
  `score = expected_value`; razlog: `"očekivana vrednost = P×vrednost − cena"`.

### Korak 2 — Selektovanje (`select_target_customers`)

Primenjuje pravila na **ceo profil** (red-po-red kroz `evaluate_campaign_rules`),
zadržava samo eligibilne i dodaje `selected_reasons`. Aktivno pravilo bez
potrebne kolone -> `ValueError` („aktivno pravilo bez podataka" je bug, ne tihi
preskok). Prazan rezultat je dozvoljen (niko ne zadovoljava pravila).

### Korak 3 — Rangiranje (`rank_target_customers`)

Računa skor za svaku vrstu, sortira opadajuće po `score` (deterministički
tie-break po `user_id`), dodaje `rank` 1..N i primenjuje **efektivni limit**:
`min(limit, max_contacts)`. Vraća top-N sa `score`, `expected_value`,
`probability`, `segment`, `rfm_bucket`, `monetary` i `reasons`.

### Korak 4 — Rule baseline (`rule_based_score`, `rank_by_rule`)

`rule_based_score(rfm_bucket, monetary)` = `prioritet × 1e6 + vrednost`.
`rank_by_rule` primenjuje samo bucket/vrednost pravila (bez ML kolona) i rangira
po rule skoru — baseline i **fallback** za netreniran model.

### Korak 5 — Servis + API (`app/services/targeting.py`, `app/api/campaign_routes.py`)

`TargetingService`:

* **ML profil** (`_ml_profile`): ako su Day 2/3 modeli trenirani, učitava
  sačuvane skalere/modele i gradi živi profil — verovatnoće na čistoj istoriji
  (cut-off iz Day 3 meta) kroz sačuvani scaler/model, segmente kroz sačuvani
  K-Means/scaler, RFM bucket kao pravilo.
* **Rule profil** (`_rule_profile`): feature-i + RFM bucket, bez ML kolona —
  koristi se za `mode="rule"` i za fallback.
* `recommended_audience(campaign_id, limit, mode)`: `mode="ml"` koristi ML
  profil ako su modeli trenirani, inače **definisan fallback** (200, ne 503):
  `mode="rule"`, `fallback=true`, `fallback_reason="untrained_model"`.
* `targeting_comparison(campaign_id, limit)`: rule vs ML na istom profilu
  (zahteva trenirane modele -> 503 ako nisu).

API rute su u `app/api/campaign_routes.py`, uključene preko `app/api/routes.py` u `app/main.py`.

## Važne funkcije

| Funkcija | Šta radi | Fajl |
| --- | --- | --- |
| `score_customer(...)` | eligibilnost + očekivana vrednost (skor odluke) | `app/ml/targeting.py` |
| `select_target_customers(...)` | pravila -> selektovani skup sa razlozima | `app/ml/targeting.py` |
| `rank_target_customers(...)` | skor + limita -> top-N publika | `app/ml/targeting.py` |
| `rule_based_score(...)` / `rank_by_rule(...)` | rule baseline bez ML-a | `app/ml/targeting.py` |
| `compare_rule_vs_ml(...)` | rule vs ML: veličina, konverzije, profit, lift | `app/ml/targeting.py` |
| `TargetingService.recommended_audience` | ML publika ili rule fallback | `app/services/targeting.py` |
| `TargetingService.targeting_comparison` | poređenje (zahteva modele) | `app/services/targeting.py` |
| `app/data/generate_targeting.py` | generiše `Day 4/data/*` (byte-for-byte) | `app/data/generate_targeting.py` |
| `app/data/campaigns.py` | jedini izvor definicija kampanja | `app/data/campaigns.py` |

## API endpoint-i

| Endpoint | Odgovor |
| --- | --- |
| `GET /campaigns` | 200: lista kampanja sa pravilima |
| `GET /campaigns/{id}` | 200: detalji kampanje; **404** nepoznata kampanja |
| `GET /campaigns/{id}/recommended-audience?limit=&mode=` | 200: `{mode, fallback, fallback_reason, rules_applied, total_candidates, selected, returned, audience[]}` — publika rangirana sa razlozima; `mode=ml` bez modela -> **fallback rule publika** (`fallback=true`); `mode=rule` uvek rule; **422** nevalidan limit/mode |
| `GET /campaigns/{id}/targeting-comparison?limit=` | 200: `{rule, ml, metrics}` (veličina, očekivane konverzije/profit, overlap, jaccard, lift); **503 untrained\_model** pre treninga; **404** nepoznata kampanja |

Pokretanje: `cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001`.

### Primer — `GET /campaigns/1/recommended-audience?mode=ml&limit=5` (sa treniranim modelima)

```
{
  "campaign_id": 1, "campaign_name": "VIP reaktivacija",
  "mode": "ml", "fallback": false, "fallback_reason": null,
  "rules_applied": { "target_segments": ["segment_2","segment_3"],
    "eligible_buckets": ["champions","loyal"], "min_probability": 0.2,
    "min_monetary": 50.0, "cost_per_contact": 0.5, "max_contacts": 200,
    "contact_limit": 5 },
  "total_candidates": 2579, "selected": 83, "returned": 5,
  "audience": [
    { "rank": 1, "user_id": 395, "score": 870.7571, "expected_value": 870.7571,
      "probability": 0.9865, "segment": "segment_2", "rfm_bucket": "champions",
      "monetary": 883.18,
      "reasons": ["segment segment_2 je u ciljanim segmentima",
                  "rfm_bucket champions je u dozvoljenim bucketima",
                  "P(0.9865) >= prag 0.2000",
                  "vrednost 883.18 >= min 50.00",
                  "očekivana vrednost = 0.9865×883.18 − 0.50 = 870.7571"] }
  ]
}
```

**Fallback (modeli nisu trenirani):** isti endpoint vraća `mode="rule"`,
`fallback=true`, `fallback_reason="untrained_model"` i publiku rangiranu po
RFM/vrednosti (bez verovatnoće). NIKAD tihi `[]`/`None` — publika postoji, ali
odgovor eksplicitno kaže da je pravila, ne model.

## CMS integracija

Admin stranica `dm-frontend/app/pages/admin/campaigns/index.vue` (vidi taj
folder):

* Lista kampanja (naziv, ciljani segmenti, pragovi, cena, limita).
* Izbor kampanje -> prikaz **preporučene publike** sa razlozima (verovatnoća,
  segment, vrednost, skor, zašto).
* Prekidač **rule vs ML** (dugme/parametar `mode`) i **targeting-comparison**
  tabela (očekivane konverzije, profit, lift).
* Ako modeli nisu trenirani -> poruka da je publika rule-based (fallback) sa
  linkom na Day 2/3 treninge — bez tihog praznog stanja.

## Testiranje

```
cd dm-ml
.venv/bin/pytest app/tests            # 9 API smoke testova (Day 1–12, svi prolaze)
cd "../Day 4/lab" && LAB_MODULE=reference_solutions ../../dm-ml/.venv/bin/pytest -q test_lab.py
```

Pokriveno: `score_customer` (eligibilnost po svakom pravilu, formula očekivane
vrednosti, predikcija-vs-odluka — P=0.9×100 < P=0.6×400, negativan skor, `None`
verovatnoća, zaokruživanje), `select_target_customers` (svaki filter,
`selected_reasons`, prazan rezultat, **ValueError za aktivno pravilo bez
kolone**), `rank_target_customers` (sort, limita ∩ max\_contacts, rank 1..N,
determinizam), `compare_rule_vs_ml` (obe publike, metrike, fair rule probs),
API (lista/detalji 200/404, ML publika rangirana sa razlozima, rule mode,
**fallback za netreniran model 200 + fallback=true**, comparison 503→200,
422 za nevalidan limit/mode).

## Experiment (šta ti radiš)

1. Pokreni demo: `dm-ml/.venv/bin/python "Day 4/examples/demo_targeting.py"` —
   vidi prediction-vs-decision primer i rule-vs-ML tabelu po kampanji.
2. Pokreni vizualizaciju: `dm-ml/.venv/bin/python "Day 4/examples/visualize_targeting.py"` —
   `audience_scatter.png` (rule vs ML top-50 za kampanju 1, anotirani najveća P i najbolja odluka — u ovom seed-u isti korisnik, 395)
   i `comparison_rule_vs_ml.png` (konverzije po kampanji + lift).
3. Treniraj Day 2/3 modele (`POST /segments/train`, `POST /models/conversion/train`)
   pa pitaj `GET /campaigns/1/recommended-audience?mode=ml&limit=10` — uporedi
   publiku pre i posle treninga (pre = rule fallback).
4. Uporedi `mode=rule` i `mode=ml` za kampanju 1 — koji korisnici su u obe, koji
   samo u jednoj? (Jaccard ≈ 0.39.)
5. Promeni prag verovatnoće kampanje (`min_probability`) u
   `app/data/campaigns.py` i ponovo generiši (`app.data.generate_targeting`) —
   kako se publika menja?

## Comparison (baseline ugao)

**Rule vs ML (seed profil, logistic\_regression, limit = max\_contacts):**

| Kampanja | Limit | Rule konverzije | ML konverzije | Rule profit | ML profit | Rule avg P | ML avg P | Lift | Overlap | Jaccard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kampanja | Limit | Rule publika | ML publika | Rule konverzije | ML konverzije | Rule profit | ML profit | Rule avg P | ML avg P | Lift | Overlap | Jaccard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VIP reaktivacija | 200 | 200 | 83 | 45.1 | 34.1 | 18318.5 | 14924.6 | 0.225 | 0.411 | 0.76 | 79 | 0.387 |
| At-risk win-back | 300 | 300 | 24 | 27.8 | 5.1 | 2693.6 | 281.2 | 0.093 | 0.213 | 0.18 | 24 | 0.080 |
| Široka visoko-vrednosna | 500 | 500 | 296 | 76.2 | 68.8 | 21360.8 | 19589.7 | 0.153 | 0.232 | 0.90 | 252 | 0.463 |
| Dormant re-engage | 150 | 150 | 150 | 8.1 | 8.1 | 77.5 | 77.5 | 0.054 | 0.054 | 1.00 | 150 | 1.000 |

Šta se vidi:

* **ML publika je manja i „gušća"**: prag verovatnoće (`min_probability`) izbacuje
  većinu kandidata, pa ML kontaktira 83 umesto 200 (kampanja 1) uz skoro duplo višu
  prosečnu P (0.41 vs 0.23). Ukupne očekivane konverzije i profit su zato **niži**
  (lift 0.76), ali profit po kontaktu je viši (≈ 180 vs ≈ 92 u kampanji 1).
* **Kampanja 2 je upozorenje:** prag 0.15 propušta samo 24 at-risk korisnika — ML
  publika je premala da bi popunila kapacitet od 300 (lift 0.18). Rule publika
  „puni" kapacitet korisnicima niske verovatnoće i zato ima veći ukupni profit.
  **Prag je poslovna odluka**, ne svojstvo modela: niži prag = veći doseg, niža preciznost.
* **Kampanja 4 (dormant, bez praga):** identične publike (Jaccard 1.0) i mali profit
  (77.5) — rule-only kampanja; ML nema šta da doda kada nema praga ni segment filtera.
* **Jaccard:** tamo gde pravila diktiraju (kampanja 4) rule i ML se potpuno poklapaju;
  tamo gde prag menja publiku (1/2/3) poklapanje je 0.08–0.46.

## Evaluacija (kako znamo da je dobro)

* **Ranking je po skoru odluke, deterministički:** isti profil + ista kampanja
  -> isti redosled (tie-break po `user_id`; test).
* **Prediction-vs-decision primer je stvaran:** u kampanji 1 najveću verovatnoću
  i najbolji skor ima isti korisnik (**395**, P=0.9865, vrednost 883.18, skor 870.8),
  ali niže u listi redosled se razilazi: user **2875** (P=0.8202, vrednost 442.96,
  skor 362.8) je rank 15, iza user-a **1067** (P=0.2787, vrednost 1342.90, skor
  373.8, rank 14). `demo_targeting.py` sam pronalazi takav par.
* **Fallback je definisan:** `recommended-audience` sa netreniranim modelima
  vraća 200, `mode="rule"`, `fallback=true`, `fallback_reason="untrained_model"`;
  nema tihog `[]`. `targeting-comparison` bez modela vraća 503 (poređenje JESTE
  ML evaluacija).
* **Pravila i skor su razdvojeni:** eligibilnost je ograničenje (0/1 sa
  razlozima), skor je rangiranje. Aktivno pravilo bez podataka -> `ValueError`,
  ne tihi preskok.
* **Determinizam podataka:** `customer_profiles.csv` byte-for-byte
  (sha256 u `metadata.json`); regeneracija sa seed 42 daje iste brojeve.

## Česti bugovi

* **Tretiranje verovatnoće kao odluke** — „P=0.92, šaljemo!" bez vrednosti,
  cene i pravila. Skor odluke je očekivana vrednost, ne verovatnoća.
* **Ignorisanje eligibilnosti / kontakt limita** — slanje kampanje svima sa
  P>0.2 bez segment filtera i bez `max_contacts` klipa. Pravila su ograničenja.
* **Rangiranje po verovatnoći umesto po skoru** — top publika po P ne
  maksimizuje profit (par 2875/1067 u kampanji 1).
* **Nema fallback-a za netreniran model** — endpoint pada (503) ili vraća
  prazno. Fallback = rule publika sa `fallback=true`, definisano.
* **Leakovanje cilja kampanje u feature-e** — verovatnoća i segment se računaju
  na istoriji PRE kampanje; ako feature-i „znaju" da je korisnik već primio
  kampanju, metrike su lažne.
* **Selekcija i skor koriste različita pravila** — eligibilnost mora biti JEDNA
  definicija (ovde `evaluate_campaign_rules`), inače select i rank mogu da se
  razmimođu.

## Šta rezultat NE dokazuje

* **Lista publike nije predikcija pojedinačnih ishoda.** To je rangiran skup
  pod eksplicitnim pravilima. User 1067 (P=0.28) verovatno neće kupiti — rang
  govori o *odluci*, ne o sudbini korisnika.
* **Model može biti u pravu, a odluka pogrešna.** Visoka P + niska vrednost +
  visoka cena = loša odluka iako model nije pogrešio. Cena, kapacitet, etika,
  budžet su deo odluke.
* **Lift 0.76 (ili bilo koji drugi) na ovom datasetu ne generalizuje.** Brojevi važe za sintetički
  seed (42); na pravom store-u signal, cene i kapacitet su drugačiji.
* **ML publika nije „tačnija" publika.** Viša prosečna P ne znači da ML pogađa
  budućnost; znači da filtrira i rangira po eksplicitnoj meti (prag + očekivana vrednost).
* **Rule publika nije „lošija".** Kampanje 1–3 pokazuju da veća rule publika daje
  veći ukupni očekivani profit — poređenje pokazuje trade-off (doseg vs preciznost),
  ne pobednika.
* **Targeting ne objašnjava uzrok** (zašto će korisnik kupiti) niti šta da se
  uradi sa rezultatom (kojim kanalom, kojom porukom) — to su naredni dani.

## Vežbe

1. **Dodaj kampanji pravilo `max_contacts`** (npr. 50) i posmatraj publiku —
   kako se menja `returned` i ko ispada sa vrha? Zašto je kapacitet ograničenje,
   ne skor?
2. **Promeni vrednosnu težinu** u `score_customer` (npr. `sqrt(monetary)` ili
   `log1p(monetary)`) i izmeri efekat na rangiranje i očekivani profit.
3. **Dodaj eligibilnost** — npr. pravilo „ne šalji dormant" u kampanju 3
   (`eligible_buckets`) i uporedi publiku pre/posle.
4. **Dokumentuj primer gde najveća verovatnoća NIJE najbolja odluka** — koristi
   `demo_targeting.py` (2875 vs 1067) ili pronađi svoj unutar druge kampanje;
   objasni zašto.
5. **Uporedi logistic vs random forest** u targetingu (treniraj `model_type=random_forest` u Day 3 pa ponovo pitaj publiku) — kako se menja rang?
6. **Fallback za netreniran model** — pokreni `recommended-audience?mode=ml`
   u svežem checkout-u (bez `app/models/`) i potvrdi `mode="rule"`,
   `fallback=true`, `untrained_model`.

## Napomena o profilu (ex-post evaluacija)

`customer_profiles.csv` kombinuje **P iz clean (pre cut-off) feature-a** sa
`segment`/`rfm_bucket`/`monetary` izračunatim iz **cele istorije** (uključujući window).
To je u redu za odluku „sada“, ali **nije pošteno za ex-post evaluaciju kampanje** —
vrednost iz window-a curi u rangiranje. Za poštenu evaluaciju sve kolone računajte
do cut-off-a.

## Sažetak

Od Day 3 predikcije napravio si **odluku**: `score_customer` (očekivana
vrednost `P×vrednost − cena`), `select_target_customers` (pravila kao
ograničenja), `rank_target_customers` (skor + kontakt limit), rule baseline
bez ML-a i `compare_rule_vs_ml` koji meri šta ML dodaje (viša prosečna P i profit po kontaktu) i
šta košta (manja publika: lift 0.18–0.90 u ukupnim konverzijama; kampanja 4 bez razlike). Centralna lekcija: **predikcija je ulaz u odluku, ne odluka** — model
kaže 0.92, aplikacija odlučuje pod pravilima i cenama. Sledeći korak: Day 5
prelazi sa *kome* poslati kampanju na *šta* preporučiti (content-based recommender) —
novi servis, ne isti targeting servis. Pitanje
danas: **kada je verovatnoća dovoljna, a kada treba i pravila i vrednost?**

---

<!-- page_id 419 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/campaigns.csv

```
campaign_id,name,description,goal,target_segments,eligible_buckets,min_probability,min_monetary,cost_per_contact,expected_revenue,budget,max_contacts,status,notes
1,VIP reaktivacija,"Ciljaj najvrednije K-Means segmente (segment_2 + segment_3: visok frequency/monetary u seed-u 42) i visoke RFM bucket-e; kontakt košta 0.5, očekivani prihod po konverziji 60.",Reaktiviraj najvrednije korisnike,"[""segment_2"", ""segment_3""]","[""champions"", ""loyal""]",0.2,50.0,0.5,60.0,150.0,200,active,ML-assisted: prag verovatnoće + ciljani segmenti.
2,At-risk win-back,"Korisnici koji klize (rfm at_risk; K-Means segment_0 = najduži recency u seed-u 42). Nizak prag verovatnoće, jeftiniji kontakt.",Vrati korisnike koji klize,"[""segment_0""]","[""at_risk""]",0.15,0.0,0.3,30.0,90.0,300,active,ML-assisted: segment filter + nizak prag.
3,Široka visoko-vrednosna kampanja,Svi osim dormant-a; nizak prag verovatnoće (0.10) i jeftin kontakt (0.2).,Širok doseg visoko-vrednosnih korisnika,[],"[""champions"", ""loyal"", ""at_risk""]",0.1,0.0,0.2,35.0,100.0,500,active,ML-assisted: samo prag verovatnoće (bez segment filtera).
4,Dormant re-engage (pravila),"Pravilima-only kampanja: dormant bucket, BEZ praga verovatnoće (min_probability=0). Pokazuje kako rule targeting radi bez modela.",Pokušaj povratka dormant korisnika po najnižoj ceni,[],"[""dormant""]",0.0,0.0,0.1,15.0,15.0,150,active,Rule-only: nema verovatnoće — rangira se po RFM/vrednosti.
```

### data/customer\_profiles.csv

```
user_id,segment,rfm_bucket,probability,monetary,frequency,recency_days,aov,conversion,favorite_category
1,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,8.0
3,segment_1,dormant,0.0339,0.0,0,2,0.0,0.0,11.0
4,segment_1,dormant,0.0241,0.0,0,6,0.0,0.0,1.0
5,segment_1,at_risk,0.0652,0.0,0,0,0.0,0.0,7.0
6,segment_3,at_risk,0.152,17.48,2,25,8.74,0.1538,8.0
7,segment_0,dormant,0.0329,0.0,0,16,0.0,0.0,2.0
8,segment_1,at_risk,0.038,0.0,0,0,0.0,0.0,3.0
9,segment_1,at_risk,0.0184,0.0,0,0,0.0,0.0,9.0
10,segment_3,at_risk,0.2967,47.97,2,21,23.98,0.0952,4.0
12,segment_1,dormant,0.0444,0.0,0,8,0.0,0.0,9.0
13,segment_1,dormant,0.0309,0.0,0,4,0.0,0.0,7.0
14,segment_1,dormant,0.0215,0.0,0,5,0.0,0.0,8.0
15,segment_0,dormant,0.0255,0.0,0,20,0.0,0.0,7.0
16,segment_0,dormant,0.0231,0.0,0,23,0.0,0.0,5.0
20,segment_1,dormant,0.0686,0.0,0,5,0.0,0.0,3.0
23,segment_3,at_risk,0.0959,35.99,1,8,35.99,0.1667,9.0
24,segment_1,at_risk,0.0288,0.0,0,0,0.0,0.0,9.0
25,segment_1,dormant,0.0492,0.0,0,5,0.0,0.0,9.0
26,segment_1,dormant,0.0277,0.0,0,5,0.0,0.0,2.0
27,segment_1,at_risk,0.0407,0.0,0,1,0.0,0.0,6.0
28,segment_0,dormant,0.0411,0.0,0,14,0.0,0.0,4.0
29,segment_1,dormant,0.0376,0.0,0,11,0.0,0.0,3.0
30,segment_3,loyal,0.1888,55.48,2,8,27.74,0.1538,6.0
31,segment_1,at_risk,0.0239,0.0,0,0,0.0,0.0,3.0
32,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,12.0
34,segment_1,dormant,0.0297,0.0,0,2,0.0,0.0,7.0
35,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,6.0
36,segment_0,dormant,0.028,0.0,0,17,0.0,0.0,7.0
37,segment_3,loyal,0.0338,185.98,1,2,185.98,0.2,10.0
38,segment_1,dormant,0.0483,0.0,0,12,0.0,0.0,7.0
39,segment_0,dormant,0.0204,0.0,0,26,0.0,0.0,9.0
40,segment_1,dormant,0.0349,0.0,0,5,0.0,0.0,6.0
41,segment_1,dormant,0.0423,0.0,0,6,0.0,0.0,12.0
42,segment_0,dormant,0.0359,0.0,0,17,0.0,0.0,11.0
43,segment_1,at_risk,0.0773,0.0,0,1,0.0,0.0,6.0
44,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,2.0
45,segment_1,dormant,0.0426,0.0,0,7,0.0,0.0,2.0
46,segment_3,at_risk,0.0596,14.99,1,10,14.99,0.5,3.0
47,segment_1,at_risk,0.0613,0.0,0,0,0.0,0.0,4.0
48,segment_1,at_risk,0.0342,0.0,0,1,0.0,0.0,12.0
49,segment_0,dormant,0.021,0.0,0,20,0.0,0.0,7.0
50,segment_0,dormant,0.0215,0.0,0,17,0.0,0.0,5.0
51,segment_1,at_risk,0.0491,0.0,0,0,0.0,0.0,6.0
52,segment_0,dormant,0.024,0.0,0,16,0.0,0.0,3.0
53,segment_1,dormant,0.0285,0.0,0,6,0.0,0.0,10.0
54,segment_0,dormant,0.0193,0.0,0,24,0.0,0.0,2.0
55,segment_1,dormant,0.0692,0.0,0,4,0.0,0.0,9.0
57,segment_1,dormant,0.0809,0.0,0,6,0.0,0.0,9.0
58,segment_1,dormant,0.0557,0.0,0,2,0.0,0.0,1.0
59,segment_1,at_risk,0.064,0.0,0,1,0.0,0.0,10.0
60,segment_3,at_risk,0.0499,5.49,1,13,5.49,1.0,8.0
61,segment_3,at_risk,0.0959,241.99,1,28,241.99,0.1,5.0
62,segment_1,dormant,0.0201,0.0,0,2,0.0,0.0,10.0
63,segment_0,dormant,0.0865,21.99,1,26,21.99,0.0909,12.0
64,segment_0,dormant,0.0722,15.99,1,29,15.99,0.1111,7.0
65,segment_1,dormant,0.0355,0.0,0,5,0.0,0.0,2.0
66,segment_3,champions,0.3142,347.97,3,0,115.99,0.1364,6.0
67,segment_3,loyal,0.0393,37.99,1,2,37.99,0.2,7.0
68,segment_1,dormant,0.0553,0.0,0,6,0.0,0.0,8.0
69,segment_3,champions,0.0342,112.97,2,3,56.48,0.4,5.0
70,segment_1,dormant,0.0297,0.0,0,9,0.0,0.0,1.0
71,segment_1,at_risk,0.0353,0.0,0,1,0.0,0.0,4.0
72,segment_1,dormant,0.052,0.0,0,5,0.0,0.0,7.0
73,segment_1,dormant,0.0586,0.0,0,7,0.0,0.0,12.0
74,segment_3,loyal,0.043,161.97,1,0,161.97,0.125,2.0
75,segment_1,dormant,0.0372,0.0,0,4,0.0,0.0,9.0
77,segment_1,dormant,0.051,0.0,0,10,0.0,0.0,9.0
78,segment_1,at_risk,0.0313,0.0,0,0,0.0,0.0,10.0
79,segment_0,dormant,0.0198,0.0,0,22,0.0,0.0,5.0
80,segment_0,dormant,0.0204,0.0,0,21,0.0,0.0,6.0
81,segment_1,dormant,0.045,0.0,0,4,0.0,0.0,9.0
83,segment_1,dormant,0.0261,0.0,0,6,0.0,0.0,2.0
84,segment_1,dormant,0.0178,0.0,0,3,0.0,0.0,2.0
85,segment_3,at_risk,0.0592,193.98,1,18,193.98,0.5,4.0
86,segment_0,dormant,0.0184,0.0,0,26,0.0,0.0,1.0
87,segment_1,at_risk,0.1007,0.0,0,1,0.0,0.0,12.0
88,segment_1,dormant,0.0288,0.0,0,8,0.0,0.0,2.0
89,segment_3,loyal,0.0591,215.19,2,28,107.6,0.4,8.0
90,segment_1,at_risk,0.0293,0.0,0,0,0.0,0.0,3.0
92,segment_1,at_risk,0.0306,0.0,0,0,0.0,0.0,3.0
93,segment_3,loyal,0.0357,17.99,1,0,17.99,0.25,3.0
94,segment_1,at_risk,0.0985,0.0,0,1,0.0,0.0,8.0
95,segment_1,dormant,0.0325,0.0,0,5,0.0,0.0,1.0
96,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,10.0
97,segment_1,at_risk,0.0586,0.0,0,0,0.0,0.0,5.0
98,segment_0,dormant,0.0224,0.0,0,19,0.0,0.0,5.0
99,segment_1,at_risk,0.0222,0.0,0,0,0.0,0.0,5.0
100,segment_1,dormant,0.0298,0.0,0,7,0.0,0.0,4.0
101,segment_0,dormant,0.0214,0.0,0,19,0.0,0.0,9.0
102,segment_1,dormant,0.0208,0.0,0,3,0.0,0.0,7.0
104,segment_1,at_risk,0.0285,0.0,0,0,0.0,0.0,9.0
106,segment_1,dormant,0.0712,0.0,0,4,0.0,0.0,10.0
107,segment_0,dormant,0.0178,0.0,0,26,0.0,0.0,10.0
108,segment_3,at_risk,0.0749,90.99,1,9,90.99,0.25,11.0
110,segment_1,at_risk,0.1163,0.0,0,0,0.0,0.0,3.0
111,segment_3,dormant,0.0457,22.99,1,19,22.99,0.25,5.0
112,segment_1,dormant,0.0268,0.0,0,11,0.0,0.0,9.0
113,segment_1,dormant,0.0401,0.0,0,6,0.0,0.0,3.0
114,segment_1,dormant,0.0748,0.0,0,3,0.0,0.0,9.0
115,segment_1,dormant,0.0644,0.0,0,2,0.0,0.0,9.0
116,segment_3,at_risk,0.0407,37.99,1,18,37.99,0.25,7.0
117,segment_0,dormant,0.0222,0.0,0,25,0.0,0.0,2.0
118,segment_0,dormant,0.0213,0.0,0,20,0.0,0.0,6.0
119,segment_0,dormant,0.0224,0.0,0,23,0.0,0.0,10.0
120,segment_3,at_risk,0.0633,265.99,1,30,265.99,0.2,1.0
121,segment_1,dormant,0.0771,0.0,0,2,0.0,0.0,2.0
123,segment_1,dormant,0.0248,0.0,0,2,0.0,0.0,7.0
124,segment_1,dormant,0.0293,0.0,0,6,0.0,0.0,11.0
125,segment_1,at_risk,0.0515,15.99,1,5,15.99,0.1429,3.0
126,segment_0,dormant,0.0164,0.0,0,26,0.0,0.0,9.0
129,segment_1,at_risk,0.0463,0.0,0,0,0.0,0.0,6.0
130,segment_3,loyal,0.1085,183.99,1,5,183.99,0.0833,7.0
131,segment_2,at_risk,0.3178,442.98,1,27,442.98,0.0625,9.0
132,segment_1,dormant,0.0199,0.0,0,2,0.0,0.0,6.0
133,segment_1,at_risk,0.0491,0.0,0,0,0.0,0.0,4.0
134,segment_1,at_risk,0.0245,0.0,0,0,0.0,0.0,5.0
135,segment_1,dormant,0.0171,0.0,0,2,0.0,0.0,5.0
136,segment_0,dormant,0.0193,0.0,0,24,0.0,0.0,5.0
137,segment_1,dormant,0.0291,0.0,0,7,0.0,0.0,7.0
138,segment_0,dormant,0.0201,0.0,0,22,0.0,0.0,12.0
139,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,5.0
140,segment_3,loyal,0.021,91.97,1,0,91.97,0.2,11.0
141,segment_3,loyal,0.0674,240.97,1,15,240.97,0.25,8.0
142,segment_0,at_risk,0.0886,14.99,1,17,14.99,0.1111,7.0
143,segment_3,at_risk,0.0364,30.99,1,25,30.99,0.5,10.0
144,segment_1,at_risk,0.0349,0.0,0,0,0.0,0.0,2.0
145,segment_1,dormant,0.0222,0.0,0,5,0.0,0.0,7.0
146,segment_3,at_risk,0.0442,103.99,1,26,103.99,0.3333,4.0
147,segment_0,dormant,0.0241,0.0,0,13,0.0,0.0,4.0
149,segment_3,at_risk,0.0332,4.49,1,5,4.49,0.3333,4.0
150,segment_2,loyal,0.1566,663.83,2,9,331.92,0.1538,2.0
151,segment_2,loyal,0.1406,832.97,3,10,277.66,0.1875,5.0
152,segment_3,loyal,0.1869,557.57,4,26,139.39,0.2667,5.0
153,segment_1,dormant,0.0384,0.0,0,7,0.0,0.0,2.0
154,segment_1,dormant,0.03,0.0,0,3,0.0,0.0,3.0
155,segment_0,dormant,0.0252,0.0,0,14,0.0,0.0,5.0
156,segment_1,dormant,0.0516,0.0,0,7,0.0,0.0,10.0
157,segment_1,at_risk,0.0222,0.0,0,0,0.0,0.0,2.0
158,segment_1,dormant,0.0526,0.0,0,12,0.0,0.0,10.0
159,segment_1,at_risk,0.0274,0.0,0,1,0.0,0.0,8.0
160,segment_3,at_risk,0.0936,110.99,1,12,110.99,0.125,7.0
161,segment_0,dormant,0.0221,0.0,0,15,0.0,0.0,7.0
162,segment_1,dormant,0.0392,0.0,0,9,0.0,0.0,3.0
164,segment_0,dormant,0.051,19.17,1,28,19.17,0.125,2.0
165,segment_1,at_risk,0.0381,0.0,0,1,0.0,0.0,2.0
166,segment_1,dormant,0.0367,0.0,0,2,0.0,0.0,2.0
167,segment_3,loyal,0.3243,187.97,3,9,62.66,0.1667,12.0
168,segment_3,dormant,0.0415,15.99,1,22,15.99,1.0,12.0
169,segment_2,loyal,0.4702,835.95,4,9,208.99,0.1429,1.0
170,segment_0,dormant,0.0175,0.0,0,27,0.0,0.0,4.0
171,segment_0,dormant,0.025,0.0,0,14,0.0,0.0,5.0
172,segment_1,at_risk,0.0274,0.0,0,0,0.0,0.0,1.0
173,segment_1,dormant,0.0382,0.0,0,3,0.0,0.0,5.0
174,segment_0,dormant,0.0244,0.0,0,16,0.0,0.0,4.0
175,segment_0,dormant,0.0299,0.0,0,13,0.0,0.0,2.0
176,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,10.0
178,segment_0,dormant,0.0253,0.0,0,20,0.0,0.0,12.0
179,segment_1,at_risk,0.0857,0.0,0,1,0.0,0.0,3.0
180,segment_3,champions,0.0343,79.98,2,4,39.99,0.6667,5.0
181,segment_1,at_risk,0.102,30.99,1,10,30.99,0.125,10.0
183,segment_1,dormant,0.036,0.0,0,7,0.0,0.0,1.0
184,segment_0,dormant,0.0193,0.0,0,24,0.0,0.0,12.0
185,segment_2,at_risk,0.2144,815.98,1,23,815.98,0.1111,11.0
186,segment_1,dormant,0.0791,0.0,0,7,0.0,0.0,11.0
187,segment_1,at_risk,0.0763,11.99,1,10,11.99,0.1111,9.0
188,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,8.0
189,segment_3,at_risk,0.0638,56.99,1,9,56.99,0.1667,9.0
190,segment_3,loyal,0.1885,196.5,3,20,65.5,0.25,2.0
191,segment_1,at_risk,0.0476,0.0,0,0,0.0,0.0,10.0
192,segment_1,dormant,0.0405,0.0,0,5,0.0,0.0,9.0
193,segment_3,loyal,0.0374,140.99,1,5,140.99,0.2,1.0
195,segment_0,at_risk,0.1387,49.98,1,13,49.98,0.0476,1.0
196,segment_1,dormant,0.2974,0.0,0,3,0.0,0.0,7.0
197,segment_1,at_risk,0.0251,0.0,0,0,0.0,0.0,1.0
198,segment_1,dormant,0.0188,0.0,0,3,0.0,0.0,8.0
199,segment_1,dormant,0.0711,0.0,0,7,0.0,0.0,1.0
200,segment_1,dormant,0.0436,0.0,0,7,0.0,0.0,7.0
201,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,7.0
202,segment_1,at_risk,0.0255,0.0,0,0,0.0,0.0,7.0
204,segment_2,champions,0.0936,787.98,2,1,393.99,0.1333,5.0
205,segment_3,loyal,0.1592,92.98,2,16,46.49,0.125,3.0
206,segment_3,dormant,0.0367,17.99,1,25,17.99,0.3333,4.0
207,segment_0,dormant,0.0179,0.0,0,26,0.0,0.0,6.0
208,segment_1,dormant,0.0711,0.0,0,2,0.0,0.0,8.0
209,segment_1,dormant,0.0672,0.0,0,2,0.0,0.0,4.0
210,segment_0,dormant,0.016,0.0,0,28,0.0,0.0,12.0
211,segment_1,at_risk,0.0387,0.0,0,1,0.0,0.0,9.0
212,segment_0,dormant,0.033,0.0,0,15,0.0,0.0,6.0
213,segment_1,dormant,0.0365,0.0,0,2,0.0,0.0,3.0
214,segment_1,dormant,0.0337,0.0,0,7,0.0,0.0,3.0
215,segment_3,loyal,0.3903,60.43,3,5,20.14,0.1304,5.0
216,segment_3,loyal,0.2835,134.46,3,11,44.82,0.1765,8.0
217,segment_3,loyal,0.1068,86.96,3,6,28.99,0.25,6.0
218,segment_1,dormant,0.0583,0.0,0,4,0.0,0.0,1.0
219,segment_0,dormant,0.0546,0.0,0,14,0.0,0.0,2.0
220,segment_0,at_risk,0.0803,46.99,1,26,46.99,0.0833,4.0
221,segment_0,at_risk,0.1442,59.99,1,15,59.99,0.0769,5.0
222,segment_3,at_risk,0.042,65.99,1,27,65.99,0.25,6.0
225,segment_1,dormant,0.024,0.0,0,2,0.0,0.0,3.0
226,segment_0,dormant,0.0152,0.0,0,30,0.0,0.0,6.0
227,segment_1,at_risk,0.0344,0.0,0,1,0.0,0.0,5.0
228,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,1.0
229,segment_1,dormant,0.0267,0.0,0,9,0.0,0.0,10.0
230,segment_3,loyal,0.4182,139.96,3,7,46.65,0.1667,3.0
231,segment_2,champions,0.049,552.96,2,0,276.48,0.2857,10.0
232,segment_1,at_risk,0.0386,0.0,0,1,0.0,0.0,8.0
233,segment_1,dormant,0.0278,0.0,0,10,0.0,0.0,10.0
234,segment_3,at_risk,0.0361,46.99,1,30,46.99,1.0,4.0
235,segment_1,loyal,0.1289,20.99,1,1,20.99,0.0667,7.0
236,segment_1,dormant,0.0267,0.0,0,4,0.0,0.0,7.0
237,segment_0,dormant,0.0305,0.0,0,19,0.0,0.0,11.0
238,segment_0,dormant,0.0183,0.0,0,25,0.0,0.0,5.0
240,segment_1,dormant,0.0447,0.0,0,12,0.0,0.0,6.0
241,segment_1,dormant,0.0697,0.0,0,6,0.0,0.0,9.0
242,segment_1,dormant,0.0533,0.0,0,8,0.0,0.0,4.0
243,segment_1,at_risk,0.0347,0.0,0,1,0.0,0.0,12.0
244,segment_0,at_risk,0.0893,23.98,1,15,23.98,0.1111,6.0
245,segment_1,dormant,0.0855,0.0,0,4,0.0,0.0,5.0
246,segment_1,dormant,0.0384,0.0,0,3,0.0,0.0,4.0
247,segment_3,dormant,0.0453,24.99,1,20,24.99,0.5,1.0
249,segment_0,dormant,0.0166,0.0,0,28,0.0,0.0,11.0
250,segment_1,at_risk,0.0268,0.0,0,0,0.0,0.0,11.0
251,segment_1,at_risk,0.0914,0.0,0,0,0.0,0.0,7.0
252,segment_1,dormant,0.0516,0.0,0,11,0.0,0.0,7.0
253,segment_1,dormant,0.0594,0.0,0,6,0.0,0.0,2.0
254,segment_1,at_risk,0.0601,0.0,0,1,0.0,0.0,5.0
255,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,1.0
256,segment_3,loyal,0.1074,145.53,2,20,72.76,0.25,7.0
257,segment_0,dormant,0.0337,0.0,0,15,0.0,0.0,7.0
260,segment_3,loyal,0.0352,172.99,1,3,172.99,0.25,11.0
261,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,3.0
262,segment_1,dormant,0.0258,0.0,0,2,0.0,0.0,9.0
264,segment_1,at_risk,0.0738,0.0,0,0,0.0,0.0,1.0
265,segment_0,dormant,0.0171,0.0,0,28,0.0,0.0,10.0
266,segment_2,loyal,0.2548,493.99,1,14,493.99,0.0667,4.0
267,segment_1,dormant,0.0213,0.0,0,2,0.0,0.0,7.0
269,segment_3,at_risk,0.0621,37.64,2,22,18.82,0.3333,10.0
270,segment_1,dormant,0.1536,0.0,0,5,0.0,0.0,4.0
271,segment_0,dormant,0.0183,0.0,0,25,0.0,0.0,5.0
272,segment_0,dormant,0.0163,0.0,0,28,0.0,0.0,1.0
273,segment_0,dormant,0.0207,0.0,0,21,0.0,0.0,9.0
274,segment_1,at_risk,0.0935,6.98,1,7,6.98,0.1,10.0
275,segment_3,at_risk,0.0425,85.99,1,26,85.99,0.2,10.0
276,segment_1,at_risk,0.0263,0.0,0,1,0.0,0.0,6.0
277,segment_3,champions,0.281,128.96,4,0,32.24,0.1538,3.0
278,segment_1,at_risk,0.0377,0.0,0,0,0.0,0.0,8.0
279,segment_0,dormant,0.0274,0.0,0,21,0.0,0.0,9.0
280,segment_1,dormant,0.0614,0.0,0,10,0.0,0.0,4.0
281,segment_3,loyal,0.0695,204.99,1,3,204.99,0.1,6.0
284,segment_1,dormant,0.0627,0.0,0,5,0.0,0.0,8.0
286,segment_0,dormant,0.0735,25.99,1,23,25.99,0.1,2.0
288,segment_1,at_risk,0.0381,0.0,0,0,0.0,0.0,2.0
290,segment_0,at_risk,0.0621,8.49,1,15,8.49,0.1667,7.0
291,segment_1,at_risk,0.0785,0.0,0,0,0.0,0.0,6.0
292,segment_1,dormant,0.0285,0.0,0,6,0.0,0.0,3.0
293,segment_1,at_risk,0.0298,0.0,0,0,0.0,0.0,3.0
294,segment_1,at_risk,0.0387,0.0,0,0,0.0,0.0,7.0
295,segment_0,dormant,0.025,0.0,0,15,0.0,0.0,11.0
296,segment_0,dormant,0.024,0.0,0,16,0.0,0.0,1.0
297,segment_1,at_risk,0.0243,0.0,0,1,0.0,0.0,10.0
298,segment_3,loyal,0.2793,267.07,3,9,89.02,0.2308,9.0
299,segment_1,dormant,0.0265,0.0,0,8,0.0,0.0,8.0
300,segment_1,dormant,0.034,0.0,0,2,0.0,0.0,6.0
301,segment_1,dormant,0.0517,0.0,0,7,0.0,0.0,5.0
303,segment_1,dormant,0.0301,0.0,0,3,0.0,0.0,3.0
304,segment_1,at_risk,0.0296,0.0,0,1,0.0,0.0,12.0
305,segment_1,dormant,0.0293,0.0,0,5,0.0,0.0,2.0
306,segment_3,champions,0.1797,264.98,2,0,132.49,0.1429,5.0
307,segment_1,dormant,0.0297,0.0,0,9,0.0,0.0,11.0
308,segment_1,at_risk,0.0257,0.0,0,0,0.0,0.0,3.0
309,segment_0,dormant,0.0229,0.0,0,18,0.0,0.0,11.0
310,segment_1,dormant,0.0295,0.0,0,9,0.0,0.0,2.0
312,segment_0,dormant,0.0421,0.0,0,15,0.0,0.0,4.0
313,segment_1,dormant,0.0454,0.0,0,5,0.0,0.0,1.0
314,segment_1,at_risk,0.0483,10.98,1,2,10.98,0.1429,8.0
315,segment_1,at_risk,0.0381,0.0,0,0,0.0,0.0,6.0
317,segment_1,dormant,0.0482,0.0,0,7,0.0,0.0,3.0
318,segment_3,at_risk,0.0883,89.99,1,13,89.99,0.1429,10.0
319,segment_3,at_risk,0.1206,141.99,1,21,141.99,0.1,5.0
320,segment_1,at_risk,0.027,0.0,0,0,0.0,0.0,1.0
321,segment_0,dormant,0.0222,0.0,0,19,0.0,0.0,3.0
323,segment_0,dormant,0.023,0.0,0,17,0.0,0.0,6.0
324,segment_0,dormant,0.0187,0.0,0,25,0.0,0.0,5.0
325,segment_1,dormant,0.029,0.0,0,8,0.0,0.0,11.0
326,segment_0,dormant,0.0836,7.76,1,28,7.76,0.0909,5.0
329,segment_1,at_risk,0.029,0.0,0,0,0.0,0.0,10.0
330,segment_0,dormant,0.0182,0.0,0,26,0.0,0.0,9.0
331,segment_1,at_risk,0.1476,0.0,0,0,0.0,0.0,12.0
332,segment_0,dormant,0.0355,0.0,0,15,0.0,0.0,7.0
333,segment_1,at_risk,0.0552,0.0,0,0,0.0,0.0,12.0
334,segment_0,dormant,0.0241,0.0,0,15,0.0,0.0,6.0
335,segment_0,dormant,0.0191,0.0,0,24,0.0,0.0,5.0
336,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,6.0
337,segment_3,loyal,0.1841,235.87,3,20,78.62,0.2308,6.0
338,segment_1,at_risk,0.0401,0.0,0,0,0.0,0.0,5.0
339,segment_0,dormant,0.0295,0.0,0,14,0.0,0.0,11.0
341,segment_1,dormant,0.0311,0.0,0,2,0.0,0.0,1.0
342,segment_1,dormant,0.0304,0.0,0,6,0.0,0.0,11.0
344,segment_0,at_risk,0.1291,61.97,1,27,61.97,0.0714,10.0
346,segment_1,at_risk,0.0439,0.0,0,0,0.0,0.0,9.0
347,segment_1,dormant,0.0263,0.0,0,12,0.0,0.0,6.0
348,segment_1,dormant,0.028,0.0,0,9,0.0,0.0,12.0
349,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,10.0
350,segment_1,at_risk,0.1763,48.98,1,10,48.98,0.0909,12.0
351,segment_1,at_risk,0.0183,0.0,0,1,0.0,0.0,8.0
353,segment_1,at_risk,0.0206,0.0,0,1,0.0,0.0,2.0
354,segment_1,dormant,0.0694,0.0,0,3,0.0,0.0,11.0
355,segment_1,dormant,0.0357,0.0,0,7,0.0,0.0,1.0
356,segment_3,at_risk,0.059,48.99,1,14,48.99,0.3333,11.0
357,segment_1,at_risk,0.0201,0.0,0,0,0.0,0.0,8.0
359,segment_1,dormant,0.0716,0.0,0,12,0.0,0.0,2.0
360,segment_1,at_risk,0.1537,0.0,0,1,0.0,0.0,1.0
361,segment_1,dormant,0.0327,0.0,0,2,0.0,0.0,10.0
362,segment_1,at_risk,0.025,0.0,0,1,0.0,0.0,1.0
363,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,6.0
364,segment_1,dormant,0.0317,0.0,0,12,0.0,0.0,8.0
365,segment_3,at_risk,0.0447,150.99,1,25,150.99,1.0,12.0
366,segment_1,dormant,0.0791,0.0,0,3,0.0,0.0,6.0
367,segment_1,at_risk,0.0344,0.0,0,1,0.0,0.0,3.0
368,segment_3,loyal,0.1558,173.98,2,16,86.99,0.1111,12.0
369,segment_1,dormant,0.0441,0.0,0,2,0.0,0.0,7.0
370,segment_1,dormant,0.0296,0.0,0,7,0.0,0.0,4.0
371,segment_1,dormant,0.0433,0.0,0,8,0.0,0.0,3.0
372,segment_1,dormant,0.039,0.0,0,8,0.0,0.0,4.0
373,segment_0,at_risk,0.0926,17.99,1,14,17.99,0.0769,3.0
375,segment_3,champions,0.1285,405.97,3,5,135.32,0.25,10.0
376,segment_1,dormant,0.057,0.0,0,8,0.0,0.0,2.0
377,segment_1,dormant,0.0402,0.0,0,11,0.0,0.0,3.0
378,segment_1,at_risk,0.0337,0.0,0,0,0.0,0.0,8.0
379,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,10.0
380,segment_0,dormant,0.04,0.0,0,13,0.0,0.0,4.0
381,segment_1,dormant,0.0283,0.0,0,3,0.0,0.0,11.0
382,segment_1,dormant,0.0271,0.0,0,12,0.0,0.0,8.0
383,segment_1,dormant,0.0397,0.0,0,2,0.0,0.0,10.0
384,segment_1,dormant,0.0327,0.0,0,6,0.0,0.0,3.0
385,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,9.0
386,segment_1,dormant,0.0278,0.0,0,10,0.0,0.0,2.0
387,segment_1,at_risk,0.069,0.0,0,0,0.0,0.0,12.0
388,segment_3,at_risk,0.0868,69.98,1,15,69.98,0.125,2.0
389,segment_1,dormant,0.0299,0.0,0,4,0.0,0.0,5.0
390,segment_3,loyal,0.0952,241.48,2,28,120.74,0.1818,6.0
391,segment_1,dormant,0.0173,0.0,0,5,0.0,0.0,8.0
392,segment_0,dormant,0.0166,0.0,0,29,0.0,0.0,2.0
393,segment_1,dormant,0.0268,0.0,0,12,0.0,0.0,9.0
394,segment_3,champions,0.6794,568.92,5,2,113.78,0.1562,11.0
395,segment_2,champions,0.9865,883.18,7,4,126.17,0.1273,3.0
396,segment_3,champions,0.5077,117.97,3,2,39.32,0.1071,6.0
397,segment_1,dormant,0.0323,0.0,0,6,0.0,0.0,12.0
398,segment_1,dormant,0.0688,0.0,0,3,0.0,0.0,6.0
399,segment_1,loyal,0.0383,36.99,1,1,36.99,0.125,12.0
400,segment_1,at_risk,0.0347,0.0,0,0,0.0,0.0,10.0
402,segment_1,dormant,0.0609,0.0,0,6,0.0,0.0,8.0
403,segment_0,dormant,0.0291,0.0,0,18,0.0,0.0,11.0
404,segment_0,dormant,0.0248,0.0,0,14,0.0,0.0,5.0
405,segment_2,loyal,0.2794,725.99,1,11,725.99,0.0909,2.0
406,segment_3,at_risk,0.0801,69.98,1,10,69.98,0.1667,6.0
407,segment_1,dormant,0.0526,0.0,0,3,0.0,0.0,3.0
408,segment_1,at_risk,0.0373,0.0,0,0,0.0,0.0,4.0
409,segment_3,champions,0.9447,441.92,4,1,110.48,0.0784,10.0
410,segment_1,dormant,0.0494,0.0,0,11,0.0,0.0,11.0
411,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,10.0
412,segment_1,dormant,0.027,0.0,0,5,0.0,0.0,8.0
414,segment_1,dormant,0.0269,0.0,0,12,0.0,0.0,5.0
415,segment_0,dormant,0.0309,0.0,0,13,0.0,0.0,1.0
416,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,7.0
417,segment_1,loyal,0.266,89.99,1,1,89.99,0.0435,9.0
419,segment_1,at_risk,0.0572,0.0,0,0,0.0,0.0,8.0
420,segment_1,dormant,0.0298,0.0,0,2,0.0,0.0,12.0
421,segment_1,at_risk,0.1478,10.99,1,7,10.99,0.1,7.0
424,segment_1,at_risk,0.0361,0.0,0,0,0.0,0.0,8.0
425,segment_1,at_risk,0.0985,0.0,0,1,0.0,0.0,3.0
426,segment_1,dormant,0.0286,0.0,0,9,0.0,0.0,1.0
427,segment_1,dormant,0.0285,0.0,0,7,0.0,0.0,1.0
428,segment_1,dormant,0.0213,0.0,0,6,0.0,0.0,3.0
430,segment_1,dormant,0.0375,0.0,0,10,0.0,0.0,5.0
433,segment_1,dormant,0.0473,0.0,0,4,0.0,0.0,7.0
434,segment_1,dormant,0.0505,0.0,0,12,0.0,0.0,9.0
435,segment_1,at_risk,0.0297,0.0,0,0,0.0,0.0,3.0
436,segment_1,dormant,0.0433,0.0,0,7,0.0,0.0,4.0
437,segment_1,dormant,0.0363,0.0,0,3,0.0,0.0,11.0
438,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,8.0
439,segment_1,at_risk,0.1609,0.0,0,1,0.0,0.0,6.0
440,segment_0,dormant,0.0208,0.0,0,21,0.0,0.0,7.0
441,segment_0,dormant,0.0192,0.0,0,21,0.0,0.0,4.0
444,segment_0,dormant,0.0588,0.0,0,14,0.0,0.0,3.0
445,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,5.0
446,segment_3,loyal,0.0265,73.99,1,3,73.99,0.2,1.0
447,segment_0,at_risk,0.0574,34.99,1,29,34.99,0.125,2.0
448,segment_1,dormant,0.0297,0.0,0,3,0.0,0.0,5.0
449,segment_3,loyal,0.7692,177.97,2,11,88.98,0.0556,2.0
450,segment_0,dormant,0.0298,0.0,0,13,0.0,0.0,9.0
453,segment_0,dormant,0.0259,0.0,0,20,0.0,0.0,10.0
454,segment_1,dormant,0.0672,0.0,0,5,0.0,0.0,10.0
455,segment_1,at_risk,0.0722,0.0,0,0,0.0,0.0,3.0
456,segment_3,at_risk,0.0854,92.99,1,11,92.99,0.2,4.0
458,segment_1,dormant,0.0396,0.0,0,5,0.0,0.0,3.0
459,segment_1,dormant,0.0684,0.0,0,8,0.0,0.0,2.0
460,segment_1,dormant,0.0777,0.0,0,8,0.0,0.0,4.0
461,segment_3,loyal,0.2772,345.98,2,11,172.99,0.125,5.0
464,segment_0,dormant,0.168,15.99,1,21,15.99,0.0833,3.0
465,segment_1,dormant,0.0412,0.0,0,4,0.0,0.0,9.0
466,segment_0,dormant,0.0225,0.0,0,18,0.0,0.0,4.0
467,segment_0,dormant,0.0315,0.0,0,19,0.0,0.0,8.0
468,segment_3,at_risk,0.0685,108.97,1,14,108.97,0.2,4.0
469,segment_1,dormant,0.0413,0.0,0,9,0.0,0.0,2.0
470,segment_1,dormant,0.0301,0.0,0,6,0.0,0.0,2.0
471,segment_1,dormant,0.0598,0.0,0,2,0.0,0.0,5.0
472,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,7.0
473,segment_0,dormant,0.0208,0.0,0,27,0.0,0.0,5.0
474,segment_1,at_risk,0.0577,0.0,0,0,0.0,0.0,10.0
475,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,5.0
476,segment_3,loyal,0.1782,478.92,4,10,119.73,0.2667,6.0
477,segment_3,loyal,0.2762,235.98,2,9,117.99,0.125,11.0
478,segment_1,dormant,0.0664,0.0,0,8,0.0,0.0,2.0
479,segment_1,dormant,0.0483,0.0,0,2,0.0,0.0,8.0
481,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,11.0
482,segment_1,dormant,0.021,0.0,0,2,0.0,0.0,3.0
483,segment_0,at_risk,0.2115,30.99,1,20,30.99,0.0625,1.0
484,segment_0,dormant,0.0171,0.0,0,28,0.0,0.0,11.0
485,segment_1,at_risk,0.0241,0.0,0,0,0.0,0.0,10.0
486,segment_3,loyal,0.2294,81.08,3,26,27.03,0.2143,4.0
488,segment_2,champions,0.0568,440.99,1,1,440.99,0.1111,9.0
489,segment_0,dormant,0.0304,0.0,0,13,0.0,0.0,4.0
490,segment_0,dormant,0.0193,0.0,0,24,0.0,0.0,1.0
491,segment_1,dormant,0.0405,0.0,0,8,0.0,0.0,10.0
492,segment_0,dormant,0.0265,0.0,0,13,0.0,0.0,11.0
493,segment_0,dormant,0.0442,0.0,0,14,0.0,0.0,10.0
494,segment_1,dormant,0.035,0.0,0,7,0.0,0.0,11.0
495,segment_1,dormant,0.0418,0.0,0,8,0.0,0.0,9.0
496,segment_1,dormant,0.0225,0.0,0,3,0.0,0.0,4.0
498,segment_0,dormant,0.0211,0.0,0,19,0.0,0.0,5.0
499,segment_1,dormant,0.0418,0.0,0,2,0.0,0.0,12.0
500,segment_1,dormant,0.0423,0.0,0,4,0.0,0.0,12.0
503,segment_0,dormant,0.0486,0.0,0,13,0.0,0.0,10.0
504,segment_1,dormant,0.0803,0.0,0,7,0.0,0.0,1.0
505,segment_1,dormant,0.0537,0.0,0,2,0.0,0.0,1.0
506,segment_0,dormant,0.0256,0.0,0,13,0.0,0.0,5.0
507,segment_1,dormant,0.0716,0.0,0,2,0.0,0.0,8.0
509,segment_1,at_risk,0.0333,0.0,0,0,0.0,0.0,9.0
510,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,4.0
512,segment_1,at_risk,0.0576,0.0,0,0,0.0,0.0,5.0
513,segment_1,dormant,0.0285,0.0,0,10,0.0,0.0,12.0
514,segment_1,dormant,0.0581,0.0,0,6,0.0,0.0,9.0
515,segment_2,champions,0.4373,1454.92,4,4,363.73,0.125,5.0
516,segment_0,dormant,0.0464,9.49,1,25,9.49,0.125,7.0
517,segment_3,loyal,0.2512,338.96,3,10,112.99,0.1667,10.0
518,segment_1,dormant,0.0461,0.0,0,4,0.0,0.0,10.0
519,segment_3,champions,0.246,238.93,4,4,59.73,0.3077,8.0
520,segment_0,dormant,0.0317,0.0,0,16,0.0,0.0,7.0
521,segment_0,dormant,0.0173,0.0,0,28,0.0,0.0,12.0
522,segment_0,dormant,0.084,23.99,1,23,23.99,0.1111,3.0
523,segment_1,dormant,0.0294,0.0,0,8,0.0,0.0,7.0
525,segment_1,at_risk,0.0343,16.98,1,3,16.98,0.2,8.0
526,segment_0,dormant,0.0209,0.0,0,19,0.0,0.0,9.0
527,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,9.0
528,segment_0,dormant,0.0206,0.0,0,27,0.0,0.0,1.0
530,segment_1,at_risk,0.0816,0.0,0,1,0.0,0.0,7.0
531,segment_3,at_risk,0.0442,150.1,1,26,150.1,0.1667,5.0
532,segment_1,at_risk,0.094,0.0,0,0,0.0,0.0,2.0
533,segment_0,dormant,0.0313,0.0,0,17,0.0,0.0,11.0
535,segment_1,dormant,0.0241,0.0,0,2,0.0,0.0,2.0
536,segment_3,at_risk,0.0654,16.98,1,9,16.98,0.25,4.0
538,segment_1,dormant,0.063,0.0,0,8,0.0,0.0,12.0
539,segment_0,dormant,0.1044,25.36,1,25,25.36,0.0769,2.0
540,segment_1,at_risk,0.0509,0.0,0,1,0.0,0.0,7.0
541,segment_0,dormant,0.0205,0.0,0,21,0.0,0.0,12.0
542,segment_1,dormant,0.0461,0.0,0,5,0.0,0.0,6.0
543,segment_3,at_risk,0.0715,76.96,2,18,38.48,0.6667,11.0
544,segment_1,at_risk,0.1159,13.99,1,6,13.99,0.0526,12.0
545,segment_0,dormant,0.0297,0.0,0,21,0.0,0.0,2.0
546,segment_0,dormant,0.028,0.0,0,16,0.0,0.0,2.0
547,segment_0,at_risk,0.2766,96.98,1,13,96.98,0.0476,2.0
549,segment_0,dormant,0.0236,0.0,0,22,0.0,0.0,7.0
550,segment_1,dormant,0.028,0.0,0,6,0.0,0.0,1.0
551,segment_0,dormant,0.0365,0.0,0,14,0.0,0.0,2.0
552,segment_0,dormant,0.0372,0.0,0,13,0.0,0.0,4.0
553,segment_1,at_risk,0.1753,0.0,0,0,0.0,0.0,2.0
554,segment_0,dormant,0.025,0.0,0,14,0.0,0.0,11.0
555,segment_3,at_risk,0.0602,158.99,1,24,158.99,0.1429,7.0
556,segment_0,dormant,0.0158,0.0,0,30,0.0,0.0,9.0
557,segment_1,dormant,0.0303,0.0,0,7,0.0,0.0,11.0
559,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,4.0
560,segment_1,dormant,0.0303,0.0,0,8,0.0,0.0,6.0
561,segment_0,dormant,0.0213,0.0,0,20,0.0,0.0,1.0
562,segment_1,dormant,0.0415,0.0,0,5,0.0,0.0,1.0
563,segment_0,dormant,0.02,0.0,0,23,0.0,0.0,8.0
564,segment_3,loyal,0.1475,72.48,2,12,36.24,0.2,8.0
566,segment_1,dormant,0.019,0.0,0,6,0.0,0.0,8.0
567,segment_0,dormant,0.0239,0.0,0,21,0.0,0.0,6.0
568,segment_0,dormant,0.0192,0.0,0,29,0.0,0.0,9.0
570,segment_1,dormant,0.0368,0.0,0,7,0.0,0.0,8.0
571,segment_1,at_risk,0.0302,16.47,1,2,16.47,0.2,3.0
572,segment_1,dormant,0.0349,0.0,0,2,0.0,0.0,7.0
573,segment_1,dormant,0.0495,0.0,0,7,0.0,0.0,9.0
574,segment_1,dormant,0.0935,0.0,0,8,0.0,0.0,8.0
575,segment_0,dormant,0.0311,0.0,0,17,0.0,0.0,5.0
576,segment_1,at_risk,0.0252,0.0,0,0,0.0,0.0,3.0
577,segment_1,dormant,0.0876,0.0,0,4,0.0,0.0,1.0
579,segment_1,dormant,0.0237,0.0,0,4,0.0,0.0,8.0
580,segment_1,dormant,0.0525,0.0,0,7,0.0,0.0,3.0
581,segment_1,at_risk,0.0901,0.0,0,1,0.0,0.0,4.0
582,segment_1,dormant,0.0356,0.0,0,9,0.0,0.0,3.0
583,segment_1,at_risk,0.0557,0.0,0,1,0.0,0.0,5.0
584,segment_1,dormant,0.0296,0.0,0,5,0.0,0.0,6.0
585,segment_3,loyal,0.0332,54.99,1,0,54.99,0.25,9.0
586,segment_1,dormant,0.0358,0.0,0,5,0.0,0.0,4.0
587,segment_1,at_risk,0.0177,0.0,0,1,0.0,0.0,7.0
588,segment_0,dormant,0.0225,0.0,0,18,0.0,0.0,9.0
592,segment_0,dormant,0.023,0.0,0,29,0.0,0.0,6.0
593,segment_1,dormant,0.0489,0.0,0,5,0.0,0.0,5.0
595,segment_3,loyal,0.103,47.97,2,8,23.98,0.4,3.0
596,segment_0,dormant,0.0203,0.0,0,19,0.0,0.0,9.0
597,segment_1,dormant,0.0261,0.0,0,12,0.0,0.0,8.0
598,segment_1,dormant,0.0345,0.0,0,9,0.0,0.0,12.0
599,segment_3,loyal,0.04,23.99,1,0,23.99,0.25,4.0
600,segment_0,at_risk,0.3922,110.99,1,28,110.99,0.0385,12.0
601,segment_3,champions,0.1385,316.96,3,6,105.65,0.2308,11.0
602,segment_3,champions,0.3301,268.98,2,8,134.49,0.1111,2.0
603,segment_1,dormant,0.028,0.0,0,10,0.0,0.0,5.0
605,segment_3,loyal,0.1401,241.99,1,14,241.99,0.125,12.0
606,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,10.0
607,segment_0,dormant,0.0444,25.99,1,19,25.99,0.1667,2.0
608,segment_1,at_risk,0.0263,0.0,0,1,0.0,0.0,7.0
610,segment_1,dormant,0.14,0.0,0,8,0.0,0.0,6.0
611,segment_1,at_risk,0.0219,0.0,0,0,0.0,0.0,1.0
612,segment_1,at_risk,0.038,0.0,0,1,0.0,0.0,10.0
613,segment_0,dormant,0.0222,0.0,0,23,0.0,0.0,4.0
614,segment_3,at_risk,0.0731,165.99,1,22,165.99,0.125,12.0
615,segment_1,dormant,0.0651,0.0,0,4,0.0,0.0,7.0
617,segment_1,at_risk,0.0773,0.0,0,0,0.0,0.0,4.0
618,segment_1,dormant,0.0411,0.0,0,9,0.0,0.0,10.0
619,segment_3,at_risk,0.0591,204.99,1,20,204.99,0.5,5.0
620,segment_3,champions,0.4106,350.95,3,4,116.98,0.1071,7.0
622,segment_0,dormant,0.0178,0.0,0,26,0.0,0.0,7.0
623,segment_0,dormant,0.0254,0.0,0,14,0.0,0.0,1.0
624,segment_0,dormant,0.0701,23.99,1,28,23.99,0.1111,7.0
625,segment_0,dormant,0.0484,14.99,1,28,14.99,0.125,3.0
626,segment_1,dormant,0.0538,0.0,0,5,0.0,0.0,3.0
627,segment_1,at_risk,0.0252,0.0,0,1,0.0,0.0,2.0
629,segment_1,loyal,0.1058,46.99,1,2,46.99,0.0714,12.0
631,segment_0,dormant,0.0802,8.49,1,26,8.49,0.0667,4.0
634,segment_1,at_risk,0.1541,59.99,1,8,59.99,0.0714,5.0
635,segment_1,dormant,0.0529,0.0,0,2,0.0,0.0,6.0
636,segment_2,at_risk,0.1413,477.97,1,20,477.97,0.1111,7.0
637,segment_3,champions,0.1285,330.99,4,3,82.75,0.3333,6.0
638,segment_3,loyal,0.2961,44.48,2,4,22.24,0.087,9.0
640,segment_1,at_risk,0.0311,0.0,0,0,0.0,0.0,9.0
641,segment_0,dormant,0.0228,0.0,0,17,0.0,0.0,4.0
642,segment_1,at_risk,0.0237,0.0,0,1,0.0,0.0,8.0
643,segment_1,dormant,0.0515,0.0,0,2,0.0,0.0,10.0
644,segment_1,dormant,0.0874,0.0,0,5,0.0,0.0,10.0
645,segment_1,dormant,0.0323,0.0,0,2,0.0,0.0,5.0
646,segment_0,dormant,0.0207,0.0,0,27,0.0,0.0,5.0
647,segment_1,dormant,0.0299,0.0,0,8,0.0,0.0,7.0
648,segment_1,at_risk,0.0436,0.0,0,0,0.0,0.0,6.0
650,segment_1,dormant,0.0693,0.0,0,3,0.0,0.0,9.0
651,segment_1,at_risk,0.054,0.0,0,1,0.0,0.0,6.0
653,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,5.0
655,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,3.0
656,segment_0,at_risk,0.1106,7.49,1,15,7.49,0.1,12.0
657,segment_0,dormant,0.0191,0.0,0,24,0.0,0.0,3.0
658,segment_3,champions,0.2827,414.97,2,5,207.48,0.0769,4.0
659,segment_1,dormant,0.0222,0.0,0,6,0.0,0.0,3.0
660,segment_1,dormant,0.0302,0.0,0,11,0.0,0.0,6.0
661,segment_1,dormant,0.04,0.0,0,4,0.0,0.0,1.0
662,segment_1,at_risk,0.0362,0.0,0,1,0.0,0.0,8.0
663,segment_1,dormant,0.0366,0.0,0,3,0.0,0.0,2.0
664,segment_3,at_risk,0.1203,265.99,1,22,265.99,0.1111,11.0
665,segment_1,at_risk,0.0205,0.0,0,1,0.0,0.0,9.0
666,segment_1,dormant,0.0301,0.0,0,2,0.0,0.0,4.0
667,segment_1,dormant,0.0529,0.0,0,6,0.0,0.0,3.0
668,segment_1,dormant,0.0561,0.0,0,5,0.0,0.0,5.0
669,segment_0,dormant,0.0213,0.0,0,27,0.0,0.0,9.0
670,segment_1,at_risk,0.028,0.0,0,0,0.0,0.0,1.0
671,segment_1,dormant,0.0341,0.0,0,7,0.0,0.0,3.0
672,segment_1,dormant,0.0352,0.0,0,2,0.0,0.0,5.0
674,segment_0,dormant,0.0188,0.0,0,24,0.0,0.0,7.0
675,segment_1,at_risk,0.0428,0.0,0,1,0.0,0.0,1.0
677,segment_0,dormant,0.0314,0.0,0,23,0.0,0.0,3.0
678,segment_0,dormant,0.0289,0.0,0,22,0.0,0.0,12.0
679,segment_1,dormant,0.0416,0.0,0,3,0.0,0.0,3.0
680,segment_1,dormant,0.0319,0.0,0,3,0.0,0.0,11.0
681,segment_1,dormant,0.0317,0.0,0,11,0.0,0.0,6.0
682,segment_0,at_risk,0.0729,116.55,1,27,116.55,0.1111,4.0
683,segment_0,dormant,0.0257,0.0,0,13,0.0,0.0,7.0
684,segment_1,dormant,0.0313,0.0,0,5,0.0,0.0,12.0
685,segment_0,dormant,0.0241,0.0,0,13,0.0,0.0,2.0
687,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,11.0
688,segment_0,at_risk,0.068,24.99,1,15,24.99,0.125,6.0
689,segment_0,dormant,0.0226,0.0,0,18,0.0,0.0,9.0
690,segment_1,dormant,0.019,0.0,0,5,0.0,0.0,12.0
691,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,8.0
692,segment_0,dormant,0.2153,16.98,1,29,16.98,0.0435,8.0
694,segment_1,dormant,0.0295,0.0,0,9,0.0,0.0,1.0
695,segment_0,dormant,0.0241,0.0,0,21,0.0,0.0,4.0
696,segment_1,dormant,0.025,0.0,0,5,0.0,0.0,11.0
697,segment_3,loyal,0.3902,108.06,2,25,54.03,0.0741,2.0
699,segment_3,loyal,0.6862,161.88,4,7,40.47,0.1739,3.0
700,segment_1,dormant,0.0426,0.0,0,2,0.0,0.0,4.0
701,segment_1,dormant,0.0473,0.0,0,5,0.0,0.0,7.0
702,segment_0,dormant,0.104,9.49,1,26,9.49,0.0769,6.0
703,segment_0,dormant,0.0182,0.0,0,26,0.0,0.0,12.0
704,segment_1,dormant,0.0717,0.0,0,7,0.0,0.0,12.0
705,segment_1,dormant,0.0285,0.0,0,9,0.0,0.0,9.0
706,segment_3,champions,0.4775,109.98,2,3,54.99,0.0769,11.0
707,segment_1,dormant,0.0306,0.0,0,8,0.0,0.0,4.0
709,segment_1,dormant,0.0251,0.0,0,3,0.0,0.0,12.0
710,segment_1,at_risk,0.0515,0.0,0,0,0.0,0.0,9.0
711,segment_1,dormant,0.0331,0.0,0,11,0.0,0.0,11.0
712,segment_1,at_risk,0.0341,0.0,0,0,0.0,0.0,10.0
713,segment_3,at_risk,0.0552,204.99,1,23,204.99,1.0,9.0
714,segment_1,dormant,0.0467,0.0,0,3,0.0,0.0,12.0
716,segment_0,dormant,0.0616,23.99,1,28,23.99,0.1111,5.0
717,segment_0,dormant,0.0167,0.0,0,26,0.0,0.0,10.0
718,segment_1,at_risk,0.0261,0.0,0,0,0.0,0.0,1.0
719,segment_3,loyal,0.08,204.99,1,7,204.99,0.5,9.0
721,segment_1,dormant,0.0311,0.0,0,3,0.0,0.0,6.0
722,segment_1,at_risk,0.0273,0.0,0,1,0.0,0.0,2.0
723,segment_1,at_risk,0.0371,0.0,0,0,0.0,0.0,5.0
724,segment_3,loyal,0.2334,198.48,1,1,198.48,0.0417,5.0
725,segment_1,at_risk,0.0449,0.0,0,0,0.0,0.0,9.0
726,segment_1,dormant,0.0395,0.0,0,8,0.0,0.0,5.0
727,segment_1,at_risk,0.0381,0.0,0,1,0.0,0.0,9.0
728,segment_3,at_risk,0.0624,10.99,1,7,10.99,0.3333,1.0
729,segment_1,dormant,0.0226,0.0,0,3,0.0,0.0,12.0
730,segment_3,at_risk,0.0785,179.98,1,17,179.98,0.1111,9.0
731,segment_0,dormant,0.0361,0.0,0,17,0.0,0.0,10.0
732,segment_3,loyal,0.0872,471.05,2,20,235.52,0.1667,1.0
734,segment_1,dormant,0.0272,0.0,0,4,0.0,0.0,1.0
735,segment_0,dormant,0.0301,0.0,0,19,0.0,0.0,5.0
736,segment_1,at_risk,0.04,0.0,0,0,0.0,0.0,1.0
737,segment_1,dormant,0.026,0.0,0,11,0.0,0.0,7.0
739,segment_0,at_risk,0.1554,34.99,1,22,34.99,0.0526,11.0
740,segment_1,at_risk,0.0604,0.0,0,0,0.0,0.0,12.0
741,segment_1,dormant,0.0182,0.0,0,6,0.0,0.0,1.0
743,segment_0,dormant,0.0217,0.0,0,25,0.0,0.0,8.0
744,segment_0,dormant,0.0382,0.0,0,14,0.0,0.0,6.0
745,segment_3,at_risk,0.2007,51.98,2,21,25.99,0.1667,5.0
746,segment_1,dormant,0.0208,0.0,0,4,0.0,0.0,3.0
747,segment_0,at_risk,0.1662,30.99,1,17,30.99,0.0667,5.0
748,segment_3,at_risk,0.0402,59.99,1,22,59.99,1.0,5.0
750,segment_1,dormant,0.0648,0.0,0,3,0.0,0.0,5.0
751,segment_0,dormant,0.0286,0.0,0,20,0.0,0.0,6.0
754,segment_1,at_risk,0.0579,0.0,0,0,0.0,0.0,7.0
755,segment_0,at_risk,0.1054,61.99,1,29,61.99,0.0769,9.0
758,segment_2,loyal,0.7098,1040.34,4,16,260.08,0.1081,1.0
759,segment_1,dormant,0.0253,0.0,0,4,0.0,0.0,12.0
760,segment_3,dormant,0.0357,9.15,1,27,9.15,1.0,3.0
761,segment_1,dormant,0.0246,0.0,0,3,0.0,0.0,10.0
762,segment_2,champions,0.5339,904.95,3,6,301.65,0.0882,1.0
764,segment_3,loyal,0.1681,99.95,2,10,49.98,0.1333,3.0
766,segment_1,loyal,0.0435,36.99,1,2,36.99,0.1667,9.0
767,segment_3,at_risk,0.0836,109.99,1,10,109.99,0.2,2.0
768,segment_1,dormant,0.1007,0.0,0,3,0.0,0.0,5.0
769,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,12.0
770,segment_0,at_risk,0.1628,46.99,1,15,46.99,0.0833,4.0
772,segment_2,at_risk,0.0802,389.98,1,29,389.98,0.1,9.0
773,segment_3,champions,0.0852,369.95,2,0,184.98,0.2,3.0
774,segment_1,dormant,0.0277,0.0,0,9,0.0,0.0,3.0
775,segment_3,at_risk,0.0528,23.99,1,13,23.99,0.2,5.0
776,segment_1,dormant,0.0299,0.0,0,5,0.0,0.0,4.0
777,segment_1,at_risk,0.0896,0.0,0,1,0.0,0.0,3.0
778,segment_1,at_risk,0.0204,0.0,0,0,0.0,0.0,6.0
779,segment_0,dormant,0.0164,0.0,0,30,0.0,0.0,2.0
780,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,12.0
781,segment_0,dormant,0.0173,0.0,0,27,0.0,0.0,3.0
782,segment_1,at_risk,0.0332,0.0,0,0,0.0,0.0,11.0
783,segment_1,at_risk,0.0235,0.0,0,0,0.0,0.0,5.0
784,segment_0,at_risk,0.0456,37.99,1,27,37.99,0.1667,1.0
785,segment_0,dormant,0.0164,0.0,0,28,0.0,0.0,2.0
786,segment_1,at_risk,0.0176,0.0,0,1,0.0,0.0,1.0
787,segment_3,loyal,0.0274,317.98,1,2,317.98,0.5,2.0
788,segment_0,dormant,0.0271,0.0,0,18,0.0,0.0,3.0
789,segment_1,at_risk,0.0275,0.0,0,1,0.0,0.0,6.0
790,segment_1,dormant,0.0356,0.0,0,9,0.0,0.0,10.0
792,segment_1,dormant,0.0331,0.0,0,5,0.0,0.0,1.0
793,segment_3,loyal,0.0785,195.96,2,12,97.98,0.4,4.0
794,segment_1,at_risk,0.0974,0.0,0,0,0.0,0.0,12.0
795,segment_3,loyal,0.0522,117.99,1,2,117.99,0.1429,5.0
796,segment_1,at_risk,0.1009,0.0,0,0,0.0,0.0,12.0
797,segment_0,dormant,0.0241,0.0,0,22,0.0,0.0,2.0
798,segment_0,dormant,0.0172,0.0,0,27,0.0,0.0,12.0
799,segment_3,loyal,0.4541,90.98,2,15,45.49,0.0741,6.0
801,segment_1,at_risk,0.0441,0.0,0,1,0.0,0.0,2.0
802,segment_0,dormant,0.0282,0.0,0,13,0.0,0.0,4.0
803,segment_1,at_risk,0.0326,0.0,0,0,0.0,0.0,2.0
804,segment_0,dormant,0.055,0.0,0,16,0.0,0.0,11.0
805,segment_1,at_risk,0.0333,0.0,0,0,0.0,0.0,5.0
806,segment_3,champions,0.4192,187.47,3,3,62.49,0.12,4.0
807,segment_1,dormant,0.0478,0.0,0,4,0.0,0.0,3.0
808,segment_1,dormant,0.0334,0.0,0,8,0.0,0.0,11.0
809,segment_1,at_risk,0.0287,0.0,0,0,0.0,0.0,9.0
810,segment_0,dormant,0.0245,0.0,0,15,0.0,0.0,5.0
811,segment_1,at_risk,0.025,0.0,0,0,0.0,0.0,11.0
812,segment_1,dormant,0.1738,0.0,0,5,0.0,0.0,4.0
813,segment_1,at_risk,0.0205,0.0,0,0,0.0,0.0,11.0
815,segment_0,dormant,0.0251,0.0,0,15,0.0,0.0,8.0
816,segment_3,loyal,0.2032,147.97,2,17,73.98,0.1333,5.0
818,segment_3,loyal,0.0322,103.99,1,2,103.99,0.2,4.0
819,segment_1,dormant,0.0323,0.0,0,10,0.0,0.0,2.0
820,segment_0,at_risk,0.1531,126.27,1,26,126.27,0.05,3.0
821,segment_3,at_risk,0.0931,130.99,1,29,130.99,0.1111,2.0
822,segment_3,loyal,0.1355,361.98,2,13,180.99,0.2,9.0
823,segment_0,at_risk,0.0723,34.99,1,16,34.99,0.1667,6.0
824,segment_1,at_risk,0.0671,0.0,0,0,0.0,0.0,12.0
825,segment_0,dormant,0.0223,0.0,0,18,0.0,0.0,8.0
826,segment_0,dormant,0.025,0.0,0,13,0.0,0.0,8.0
827,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,5.0
829,segment_3,dormant,0.0469,8.49,1,18,8.49,0.5,8.0
830,segment_1,dormant,0.0355,0.0,0,8,0.0,0.0,4.0
831,segment_1,dormant,0.0309,0.0,0,12,0.0,0.0,5.0
832,segment_1,at_risk,0.0268,0.0,0,0,0.0,0.0,11.0
834,segment_1,at_risk,0.1058,9.49,1,5,9.49,0.0667,10.0
835,segment_1,at_risk,0.2448,0.0,0,0,0.0,0.0,1.0
838,segment_1,at_risk,0.1226,0.0,0,1,0.0,0.0,5.0
840,segment_0,dormant,0.0224,0.0,0,16,0.0,0.0,2.0
841,segment_1,at_risk,0.0312,0.0,0,0,0.0,0.0,8.0
842,segment_0,dormant,0.0317,0.0,0,19,0.0,0.0,1.0
844,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,9.0
845,segment_1,at_risk,0.0962,0.0,0,1,0.0,0.0,8.0
846,segment_0,dormant,0.0297,0.0,0,13,0.0,0.0,5.0
847,segment_1,dormant,0.0472,0.0,0,10,0.0,0.0,1.0
848,segment_1,dormant,0.0322,0.0,0,3,0.0,0.0,5.0
850,segment_1,dormant,0.0171,0.0,0,6,0.0,0.0,1.0
852,segment_1,at_risk,0.0213,0.0,0,1,0.0,0.0,1.0
853,segment_1,at_risk,0.0689,0.0,0,0,0.0,0.0,6.0
854,segment_0,dormant,0.0163,0.0,0,30,0.0,0.0,11.0
855,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,1.0
856,segment_1,at_risk,0.0645,0.0,0,0,0.0,0.0,4.0
857,segment_1,at_risk,0.0862,0.0,0,1,0.0,0.0,1.0
858,segment_0,dormant,0.0203,0.0,0,28,0.0,0.0,4.0
859,segment_1,dormant,0.0334,0.0,0,5,0.0,0.0,5.0
860,segment_0,dormant,0.023,0.0,0,17,0.0,0.0,8.0
862,segment_1,at_risk,0.0316,0.0,0,0,0.0,0.0,3.0
863,segment_1,at_risk,0.048,0.0,0,1,0.0,0.0,5.0
864,segment_1,dormant,0.0368,0.0,0,7,0.0,0.0,12.0
865,segment_1,dormant,0.0775,0.0,0,6,0.0,0.0,8.0
866,segment_1,dormant,0.0396,0.0,0,10,0.0,0.0,3.0
867,segment_1,dormant,0.0317,0.0,0,4,0.0,0.0,6.0
868,segment_1,dormant,0.0466,0.0,0,2,0.0,0.0,7.0
869,segment_1,dormant,0.0215,0.0,0,5,0.0,0.0,3.0
870,segment_0,at_risk,0.0849,76.99,1,30,76.99,0.0833,11.0
873,segment_0,dormant,0.0207,0.0,0,21,0.0,0.0,2.0
874,segment_1,dormant,0.0396,0.0,0,10,0.0,0.0,7.0
875,segment_1,dormant,0.0403,0.0,0,4,0.0,0.0,8.0
876,segment_1,at_risk,0.0366,0.0,0,0,0.0,0.0,10.0
877,segment_1,at_risk,0.028,0.0,0,1,0.0,0.0,6.0
878,segment_1,at_risk,0.0489,0.0,0,1,0.0,0.0,5.0
879,segment_1,dormant,0.0321,0.0,0,11,0.0,0.0,5.0
880,segment_1,dormant,0.0531,0.0,0,10,0.0,0.0,2.0
881,segment_1,at_risk,0.0336,0.0,0,1,0.0,0.0,9.0
883,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,2.0
885,segment_1,at_risk,0.0351,0.0,0,1,0.0,0.0,9.0
886,segment_0,dormant,0.0265,0.0,0,13,0.0,0.0,6.0
887,segment_1,dormant,0.0401,0.0,0,9,0.0,0.0,9.0
888,segment_1,dormant,0.046,0.0,0,4,0.0,0.0,2.0
889,segment_1,dormant,0.0581,0.0,0,7,0.0,0.0,10.0
890,segment_1,at_risk,0.022,0.0,0,0,0.0,0.0,12.0
891,segment_3,at_risk,0.1736,158.99,1,27,158.99,0.0625,4.0
892,segment_1,dormant,0.0241,0.0,0,4,0.0,0.0,5.0
893,segment_3,champions,0.2405,122.98,2,0,61.49,0.08,9.0
895,segment_3,at_risk,0.1275,76.99,1,7,76.99,0.1,3.0
896,segment_3,champions,0.2515,220.98,2,2,110.49,0.1053,6.0
897,segment_0,dormant,0.0295,0.0,0,13,0.0,0.0,11.0
898,segment_0,dormant,0.0169,0.0,0,28,0.0,0.0,2.0
899,segment_1,at_risk,0.1071,0.0,0,1,0.0,0.0,12.0
900,segment_1,at_risk,0.0397,0.0,0,0,0.0,0.0,1.0
901,segment_3,at_risk,0.035,44.55,1,27,44.55,0.5,8.0
902,segment_1,dormant,0.0407,0.0,0,3,0.0,0.0,5.0
903,segment_3,champions,0.0714,116.98,2,2,58.49,0.1667,2.0
904,segment_1,at_risk,0.0295,0.0,0,0,0.0,0.0,1.0
905,segment_1,at_risk,0.022,0.0,0,1,0.0,0.0,11.0
906,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,2.0
908,segment_3,at_risk,0.0532,61.99,1,5,61.99,0.1429,5.0
910,segment_0,at_risk,0.0903,65.99,1,25,65.99,0.1111,10.0
911,segment_3,at_risk,0.053,16.47,1,14,16.47,1.0,6.0
912,segment_1,at_risk,0.112,8.49,1,2,8.49,0.0625,3.0
913,segment_3,loyal,0.2685,63.98,2,11,31.99,0.1,2.0
914,segment_3,at_risk,0.0448,64.99,1,22,64.99,0.25,11.0
915,segment_3,at_risk,0.0501,281.26,1,28,281.26,0.3333,5.0
916,segment_1,dormant,0.0416,0.0,0,6,0.0,0.0,11.0
917,segment_1,at_risk,0.0258,0.0,0,1,0.0,0.0,1.0
918,segment_1,dormant,0.0417,0.0,0,8,0.0,0.0,8.0
919,segment_3,at_risk,0.0648,181.99,1,14,181.99,0.3333,3.0
920,segment_1,dormant,0.034,0.0,0,9,0.0,0.0,4.0
921,segment_0,dormant,0.0186,0.0,0,24,0.0,0.0,6.0
922,segment_1,dormant,0.035,0.0,0,6,0.0,0.0,12.0
923,segment_1,at_risk,0.0469,0.0,0,0,0.0,0.0,9.0
924,segment_0,at_risk,0.0965,54.99,1,26,54.99,0.0769,3.0
925,segment_3,dormant,0.0365,8.92,1,27,8.92,1.0,8.0
926,segment_1,dormant,0.0525,0.0,0,11,0.0,0.0,2.0
927,segment_3,loyal,0.3135,388.97,3,10,129.66,0.1579,5.0
928,segment_1,dormant,0.0333,0.0,0,10,0.0,0.0,5.0
929,segment_0,dormant,0.0174,0.0,0,27,0.0,0.0,8.0
930,segment_0,dormant,0.0256,0.0,0,13,0.0,0.0,5.0
932,segment_1,dormant,0.0372,0.0,0,8,0.0,0.0,6.0
933,segment_1,dormant,0.0417,0.0,0,9,0.0,0.0,6.0
934,segment_1,at_risk,0.0537,0.0,0,1,0.0,0.0,9.0
935,segment_0,dormant,0.0368,0.0,0,18,0.0,0.0,8.0
937,segment_1,at_risk,0.0198,0.0,0,0,0.0,0.0,5.0
938,segment_3,loyal,0.0323,80.98,1,0,80.98,0.25,12.0
940,segment_1,at_risk,0.0998,0.0,0,0,0.0,0.0,10.0
941,segment_1,dormant,0.0458,0.0,0,9,0.0,0.0,4.0
942,segment_1,dormant,0.0293,0.0,0,6,0.0,0.0,2.0
943,segment_1,at_risk,0.0322,0.0,0,1,0.0,0.0,5.0
945,segment_3,at_risk,0.0537,103.98,1,23,103.98,0.2,6.0
946,segment_0,dormant,0.0256,0.0,0,13,0.0,0.0,7.0
947,segment_3,loyal,0.0708,170.98,2,19,85.49,0.4,2.0
948,segment_1,dormant,0.0641,0.0,0,7,0.0,0.0,3.0
949,segment_1,dormant,0.068,0.0,0,10,0.0,0.0,6.0
950,segment_0,dormant,0.023,0.0,0,18,0.0,0.0,11.0
951,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,7.0
952,segment_1,dormant,0.0197,0.0,0,6,0.0,0.0,5.0
953,segment_0,dormant,0.0198,0.0,0,21,0.0,0.0,4.0
954,segment_1,at_risk,0.0838,0.0,0,1,0.0,0.0,11.0
955,segment_0,dormant,0.077,17.99,1,20,17.99,0.1,10.0
956,segment_3,loyal,0.0785,53.87,2,16,26.94,0.5,8.0
958,segment_1,dormant,0.0476,0.0,0,7,0.0,0.0,3.0
960,segment_3,at_risk,0.1549,165.99,1,18,165.99,0.0714,5.0
961,segment_3,loyal,0.035,81.99,1,3,81.99,0.3333,2.0
962,segment_2,champions,0.2285,1183.94,4,6,295.98,0.1538,1.0
963,segment_1,dormant,0.0427,0.0,0,7,0.0,0.0,10.0
964,segment_1,dormant,0.058,0.0,0,4,0.0,0.0,2.0
965,segment_0,dormant,0.0242,0.0,0,16,0.0,0.0,11.0
966,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,6.0
967,segment_0,at_risk,0.1587,65.99,1,28,65.99,0.0833,6.0
969,segment_1,dormant,0.0789,0.0,0,3,0.0,0.0,10.0
970,segment_3,at_risk,0.1401,201.98,1,25,201.98,0.0833,4.0
971,segment_1,dormant,0.0308,0.0,0,7,0.0,0.0,5.0
972,segment_2,at_risk,0.1152,763.99,1,27,763.99,0.1429,9.0
973,segment_1,dormant,0.0459,0.0,0,6,0.0,0.0,8.0
974,segment_0,at_risk,0.2094,59.97,1,17,59.97,0.0526,9.0
975,segment_1,dormant,0.0626,0.0,0,8,0.0,0.0,9.0
976,segment_1,dormant,0.0256,0.0,0,4,0.0,0.0,3.0
977,segment_1,dormant,0.0263,0.0,0,2,0.0,0.0,10.0
978,segment_1,at_risk,0.0482,0.0,0,0,0.0,0.0,12.0
979,segment_2,loyal,0.0465,478.99,1,6,478.99,0.1667,11.0
980,segment_1,at_risk,0.0411,0.0,0,0,0.0,0.0,4.0
981,segment_0,dormant,0.0172,0.0,0,27,0.0,0.0,11.0
982,segment_1,dormant,0.0409,0.0,0,5,0.0,0.0,2.0
983,segment_1,dormant,0.0449,0.0,0,3,0.0,0.0,3.0
984,segment_1,dormant,0.0294,0.0,0,8,0.0,0.0,3.0
987,segment_0,dormant,0.0269,0.0,0,16,0.0,0.0,10.0
988,segment_1,dormant,0.036,0.0,0,7,0.0,0.0,6.0
990,segment_1,dormant,0.0267,0.0,0,12,0.0,0.0,2.0
991,segment_1,dormant,0.031,0.0,0,2,0.0,0.0,9.0
992,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,7.0
994,segment_0,dormant,0.0249,0.0,0,15,0.0,0.0,3.0
995,segment_0,dormant,0.0222,0.0,0,18,0.0,0.0,12.0
996,segment_1,dormant,0.0535,0.0,0,8,0.0,0.0,7.0
997,segment_1,at_risk,0.0324,0.0,0,1,0.0,0.0,7.0
998,segment_0,dormant,0.025,0.0,0,14,0.0,0.0,10.0
999,segment_1,dormant,0.0343,0.0,0,10,0.0,0.0,6.0
1000,segment_3,at_risk,0.055,86.48,1,19,86.48,0.3333,4.0
1001,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,11.0
1002,segment_2,champions,0.6797,802.95,3,6,267.65,0.0811,5.0
1003,segment_1,dormant,0.03,0.0,0,4,0.0,0.0,2.0
1005,segment_1,at_risk,0.0311,0.0,0,1,0.0,0.0,11.0
1006,segment_0,dormant,0.023,0.0,0,18,0.0,0.0,10.0
1007,segment_3,at_risk,0.0615,48.99,1,10,48.99,0.5,11.0
1008,segment_0,at_risk,0.0886,37.99,1,16,37.99,0.1429,7.0
1009,segment_3,champions,0.2769,318.96,3,4,106.32,0.1429,5.0
1010,segment_1,dormant,0.0322,0.0,0,12,0.0,0.0,4.0
1011,segment_1,dormant,0.0706,0.0,0,5,0.0,0.0,6.0
1012,segment_1,dormant,0.0563,0.0,0,3,0.0,0.0,4.0
1014,segment_0,dormant,0.0384,0.0,0,14,0.0,0.0,7.0
1015,segment_1,at_risk,0.1035,0.0,0,1,0.0,0.0,9.0
1016,segment_1,dormant,0.0266,0.0,0,10,0.0,0.0,6.0
1017,segment_0,dormant,0.0289,0.0,0,16,0.0,0.0,9.0
1018,segment_3,loyal,0.5644,361.4,5,12,72.28,0.2,4.0
1019,segment_0,dormant,0.0307,0.0,0,13,0.0,0.0,4.0
1020,segment_3,at_risk,0.0503,89.99,1,23,89.99,0.25,5.0
1022,segment_0,dormant,0.1844,16.98,1,18,16.98,0.0667,1.0
1023,segment_1,dormant,0.0413,0.0,0,9,0.0,0.0,3.0
1024,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,7.0
1025,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,3.0
1026,segment_1,dormant,0.0354,0.0,0,2,0.0,0.0,9.0
1027,segment_1,dormant,0.0277,0.0,0,9,0.0,0.0,7.0
1028,segment_1,dormant,0.0434,0.0,0,6,0.0,0.0,6.0
1029,segment_1,at_risk,0.0662,0.0,0,1,0.0,0.0,4.0
1030,segment_3,champions,0.1094,261.47,3,2,87.16,0.1875,5.0
1031,segment_0,dormant,0.0208,0.0,0,20,0.0,0.0,2.0
1032,segment_1,dormant,0.0281,0.0,0,11,0.0,0.0,12.0
1033,segment_3,at_risk,0.0807,63.8,2,25,31.9,0.2857,3.0
1034,segment_1,dormant,0.033,0.0,0,9,0.0,0.0,7.0
1036,segment_1,dormant,0.0274,0.0,0,5,0.0,0.0,4.0
1037,segment_1,dormant,0.0261,0.0,0,4,0.0,0.0,7.0
1038,segment_1,at_risk,0.084,0.0,0,1,0.0,0.0,1.0
1039,segment_1,dormant,0.0389,0.0,0,12,0.0,0.0,2.0
1040,segment_0,dormant,0.0246,0.0,0,14,0.0,0.0,1.0
1041,segment_0,dormant,0.0252,0.0,0,14,0.0,0.0,1.0
1042,segment_1,dormant,0.0383,0.0,0,5,0.0,0.0,10.0
1043,segment_1,dormant,0.0303,0.0,0,3,0.0,0.0,9.0
1044,segment_0,at_risk,0.0954,78.95,1,29,78.95,0.0714,12.0
1045,segment_0,dormant,0.0215,0.0,0,26,0.0,0.0,6.0
1046,segment_0,dormant,0.0276,0.0,0,17,0.0,0.0,4.0
1047,segment_1,at_risk,0.0217,0.0,0,0,0.0,0.0,5.0
1048,segment_0,dormant,0.0414,0.0,0,21,0.0,0.0,7.0
1049,segment_1,dormant,0.0446,0.0,0,9,0.0,0.0,10.0
1050,segment_1,dormant,0.0484,0.0,0,3,0.0,0.0,3.0
1051,segment_1,dormant,0.0245,0.0,0,2,0.0,0.0,8.0
1052,segment_1,dormant,0.048,0.0,0,12,0.0,0.0,5.0
1053,segment_0,dormant,0.025,0.0,0,13,0.0,0.0,8.0
1054,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,4.0
1055,segment_1,at_risk,0.0249,0.0,0,0,0.0,0.0,10.0
1056,segment_1,dormant,0.0314,0.0,0,5,0.0,0.0,9.0
1057,segment_1,dormant,0.0482,0.0,0,5,0.0,0.0,6.0
1058,segment_0,dormant,0.0182,0.0,0,25,0.0,0.0,3.0
1059,segment_0,dormant,0.0236,0.0,0,23,0.0,0.0,7.0
1060,segment_0,dormant,0.0212,0.0,0,19,0.0,0.0,2.0
1061,segment_3,loyal,0.0463,162.99,1,1,162.99,0.0909,6.0
1062,segment_1,dormant,0.0288,0.0,0,4,0.0,0.0,10.0
1063,segment_3,champions,0.1372,176.8,3,1,58.93,0.25,7.0
1064,segment_0,dormant,0.0171,0.0,0,28,0.0,0.0,2.0
1065,segment_1,dormant,0.0307,0.0,0,7,0.0,0.0,3.0
1066,segment_0,at_risk,0.1682,100.99,1,21,100.99,0.0476,6.0
1067,segment_2,champions,0.2787,1342.9,4,4,335.72,0.1333,11.0
1068,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,3.0
1069,segment_1,dormant,0.0787,0.0,0,6,0.0,0.0,1.0
1070,segment_1,at_risk,0.0348,0.0,0,0,0.0,0.0,5.0
1071,segment_1,dormant,0.0411,0.0,0,6,0.0,0.0,1.0
1072,segment_1,dormant,0.0299,0.0,0,8,0.0,0.0,3.0
1073,segment_1,dormant,0.0451,0.0,0,8,0.0,0.0,6.0
1075,segment_1,at_risk,0.1368,0.0,0,1,0.0,0.0,3.0
1076,segment_1,at_risk,0.0449,0.0,0,1,0.0,0.0,5.0
1077,segment_3,at_risk,0.0555,32.99,1,14,32.99,1.0,5.0
1078,segment_1,dormant,0.0311,0.0,0,7,0.0,0.0,5.0
1079,segment_1,dormant,0.0265,0.0,0,2,0.0,0.0,1.0
1080,segment_1,at_risk,0.0956,0.0,0,0,0.0,0.0,12.0
1082,segment_0,at_risk,0.0758,22.98,1,11,22.98,0.1429,8.0
1086,segment_1,dormant,0.0355,0.0,0,6,0.0,0.0,6.0
1087,segment_1,at_risk,0.0172,0.0,0,1,0.0,0.0,5.0
1088,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,7.0
1089,segment_1,at_risk,0.0338,0.0,0,0,0.0,0.0,7.0
1090,segment_1,at_risk,0.0221,0.0,0,0,0.0,0.0,12.0
1091,segment_1,at_risk,0.0759,0.0,0,1,0.0,0.0,4.0
1092,segment_0,dormant,0.0277,0.0,0,19,0.0,0.0,1.0
1093,segment_1,at_risk,0.0305,0.0,0,0,0.0,0.0,5.0
1095,segment_1,dormant,0.0312,0.0,0,2,0.0,0.0,3.0
1096,segment_1,dormant,0.0282,0.0,0,9,0.0,0.0,11.0
1097,segment_0,at_risk,0.116,32.99,1,13,32.99,0.1111,12.0
1098,segment_1,dormant,0.0365,0.0,0,7,0.0,0.0,2.0
1099,segment_1,at_risk,0.056,0.0,0,0,0.0,0.0,1.0
1100,segment_0,dormant,0.0244,0.0,0,16,0.0,0.0,7.0
1101,segment_1,dormant,0.0321,0.0,0,10,0.0,0.0,3.0
1103,segment_1,dormant,0.0315,0.0,0,6,0.0,0.0,11.0
1104,segment_0,dormant,0.0219,0.0,0,23,0.0,0.0,3.0
1105,segment_1,at_risk,0.0427,0.0,0,1,0.0,0.0,10.0
1107,segment_1,dormant,0.0296,0.0,0,7,0.0,0.0,9.0
1108,segment_1,dormant,0.0244,0.0,0,3,0.0,0.0,2.0
1109,segment_1,at_risk,0.0281,0.0,0,1,0.0,0.0,10.0
1110,segment_1,dormant,0.0229,0.0,0,6,0.0,0.0,1.0
1111,segment_0,dormant,0.0225,0.0,0,18,0.0,0.0,2.0
1112,segment_0,at_risk,0.0566,61.99,1,28,61.99,0.1429,7.0
1113,segment_0,dormant,0.0333,0.0,0,21,0.0,0.0,9.0
1114,segment_1,dormant,0.0297,0.0,0,9,0.0,0.0,6.0
1115,segment_1,at_risk,0.0265,0.0,0,0,0.0,0.0,9.0
1117,segment_0,at_risk,0.0946,7.49,1,12,7.49,0.125,1.0
1118,segment_1,dormant,0.0292,0.0,0,6,0.0,0.0,8.0
1120,segment_1,at_risk,0.0398,0.0,0,0,0.0,0.0,9.0
1121,segment_3,loyal,0.1135,97.98,2,19,48.99,0.2222,10.0
1122,segment_1,dormant,0.0296,0.0,0,8,0.0,0.0,6.0
1125,segment_2,at_risk,0.1299,664.98,1,28,664.98,0.1429,1.0
1126,segment_1,dormant,0.0316,0.0,0,12,0.0,0.0,12.0
1127,segment_0,at_risk,0.0727,76.99,1,18,76.99,0.1111,3.0
1128,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,10.0
1129,segment_1,at_risk,0.0233,0.0,0,0,0.0,0.0,3.0
1130,segment_1,dormant,0.0224,0.0,0,4,0.0,0.0,8.0
1131,segment_1,dormant,0.0432,0.0,0,5,0.0,0.0,11.0
1132,segment_1,dormant,0.0526,0.0,0,4,0.0,0.0,8.0
1133,segment_1,at_risk,0.0182,0.0,0,1,0.0,0.0,6.0
1134,segment_1,dormant,0.0276,0.0,0,10,0.0,0.0,5.0
1136,segment_0,dormant,0.0186,0.0,0,24,0.0,0.0,10.0
1137,segment_3,champions,0.4185,391.96,3,7,130.65,0.15,10.0
1138,segment_1,dormant,0.0384,0.0,0,10,0.0,0.0,4.0
1139,segment_1,at_risk,0.0229,0.0,0,0,0.0,0.0,1.0
1140,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,2.0
1141,segment_0,at_risk,0.0637,34.99,1,25,34.99,0.125,10.0
1143,segment_3,at_risk,0.0606,36.99,1,10,36.99,0.25,2.0
1144,segment_0,dormant,0.0219,0.0,0,19,0.0,0.0,8.0
1145,segment_1,at_risk,0.047,0.0,0,1,0.0,0.0,3.0
1148,segment_0,dormant,0.0174,0.0,0,27,0.0,0.0,10.0
1149,segment_1,at_risk,0.0418,0.0,0,1,0.0,0.0,1.0
1150,segment_1,at_risk,0.054,0.0,0,0,0.0,0.0,4.0
1151,segment_1,dormant,0.0363,0.0,0,10,0.0,0.0,9.0
1153,segment_1,dormant,0.0385,0.0,0,11,0.0,0.0,5.0
1155,segment_1,dormant,0.0447,0.0,0,7,0.0,0.0,5.0
1156,segment_0,dormant,0.0389,10.99,1,27,10.99,0.25,11.0
1157,segment_1,dormant,0.0435,0.0,0,3,0.0,0.0,7.0
1158,segment_0,dormant,0.0328,0.0,0,17,0.0,0.0,9.0
1159,segment_0,dormant,0.0319,0.0,0,18,0.0,0.0,1.0
1160,segment_1,at_risk,0.0766,0.0,0,0,0.0,0.0,8.0
1161,segment_3,champions,0.2534,457.25,3,1,152.42,0.1579,10.0
1162,segment_3,loyal,0.213,183.98,2,20,91.99,0.1176,7.0
1163,segment_1,at_risk,0.0526,0.0,0,0,0.0,0.0,1.0
1165,segment_3,loyal,0.0432,16.47,2,4,8.24,0.2857,8.0
1166,segment_1,dormant,0.0246,0.0,0,5,0.0,0.0,5.0
1167,segment_0,dormant,0.0224,0.0,0,19,0.0,0.0,11.0
1168,segment_0,dormant,0.0189,0.0,0,25,0.0,0.0,12.0
1170,segment_0,dormant,0.0221,0.0,0,19,0.0,0.0,10.0
1171,segment_0,dormant,0.0235,0.0,0,17,0.0,0.0,2.0
1172,segment_1,dormant,0.0407,0.0,0,5,0.0,0.0,7.0
1173,segment_1,at_risk,0.0229,0.0,0,0,0.0,0.0,4.0
1174,segment_1,dormant,0.0601,0.0,0,3,0.0,0.0,1.0
1175,segment_3,champions,0.2046,491.93,5,4,98.39,0.4167,9.0
1176,segment_0,dormant,0.0187,0.0,0,23,0.0,0.0,10.0
1177,segment_1,dormant,0.047,0.0,0,2,0.0,0.0,1.0
1178,segment_1,dormant,0.0598,0.0,0,5,0.0,0.0,6.0
1179,segment_3,at_risk,0.0633,241.99,1,20,241.99,1.0,9.0
1181,segment_0,dormant,0.0235,0.0,0,16,0.0,0.0,8.0
1182,segment_2,loyal,0.1084,2454.41,8,13,306.8,0.2286,1.0
1183,segment_0,dormant,0.0245,0.0,0,15,0.0,0.0,11.0
1184,segment_3,loyal,0.1406,34.48,2,10,17.24,0.2222,10.0
1185,segment_3,at_risk,0.0887,84.99,1,12,84.99,0.1667,6.0
1186,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,3.0
1187,segment_1,at_risk,0.426,0.0,0,0,0.0,0.0,3.0
1188,segment_1,dormant,0.0357,0.0,0,7,0.0,0.0,9.0
1189,segment_1,dormant,0.039,0.0,0,10,0.0,0.0,12.0
1190,segment_3,champions,0.1207,224.46,2,0,112.23,0.1429,8.0
1191,segment_0,dormant,0.0212,0.0,0,19,0.0,0.0,2.0
1192,segment_1,at_risk,0.0299,0.0,0,0,0.0,0.0,8.0
1194,segment_1,dormant,0.0341,0.0,0,6,0.0,0.0,6.0
1195,segment_1,at_risk,0.0378,0.0,0,1,0.0,0.0,4.0
1198,segment_1,dormant,0.0281,0.0,0,4,0.0,0.0,4.0
1199,segment_0,dormant,0.025,0.0,0,14,0.0,0.0,9.0
1202,segment_0,dormant,0.0185,0.0,0,25,0.0,0.0,4.0
1203,segment_1,dormant,0.0465,0.0,0,9,0.0,0.0,1.0
1204,segment_1,dormant,0.0309,0.0,0,2,0.0,0.0,8.0
1205,segment_1,dormant,0.0313,0.0,0,5,0.0,0.0,1.0
1206,segment_1,at_risk,0.0765,0.0,0,0,0.0,0.0,2.0
1210,segment_0,dormant,0.0195,0.0,0,23,0.0,0.0,4.0
1211,segment_1,dormant,0.0295,0.0,0,9,0.0,0.0,3.0
1212,segment_0,dormant,0.0434,0.0,0,14,0.0,0.0,11.0
1213,segment_3,champions,0.1027,277.96,2,0,138.98,0.2857,9.0
1214,segment_1,at_risk,0.0702,0.0,0,1,0.0,0.0,9.0
1215,segment_1,dormant,0.0306,0.0,0,4,0.0,0.0,12.0
1216,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,4.0
1217,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,11.0
1218,segment_1,dormant,0.0888,0.0,0,3,0.0,0.0,5.0
1219,segment_3,loyal,0.0256,89.98,2,5,44.99,0.4,7.0
1220,segment_1,dormant,0.0292,0.0,0,5,0.0,0.0,3.0
1221,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,7.0
1222,segment_1,dormant,0.0359,0.0,0,11,0.0,0.0,2.0
1223,segment_1,at_risk,0.0784,0.0,0,0,0.0,0.0,5.0
1224,segment_1,dormant,0.0231,0.0,0,6,0.0,0.0,11.0
1225,segment_0,at_risk,0.0534,48.97,1,22,48.97,0.1429,6.0
1226,segment_1,dormant,0.0271,0.0,0,8,0.0,0.0,4.0
1227,segment_0,dormant,0.0165,0.0,0,29,0.0,0.0,2.0
1228,segment_1,at_risk,0.0209,0.0,0,1,0.0,0.0,11.0
1229,segment_3,loyal,0.0566,75.98,2,4,37.99,0.3333,5.0
1230,segment_1,dormant,0.0507,0.0,0,4,0.0,0.0,8.0
1231,segment_1,dormant,0.0271,0.0,0,12,0.0,0.0,7.0
1232,segment_0,dormant,0.0256,0.0,0,18,0.0,0.0,10.0
1234,segment_1,at_risk,0.0356,0.0,0,0,0.0,0.0,3.0
1235,segment_0,at_risk,0.0595,84.74,1,29,84.74,0.0909,5.0
1236,segment_1,dormant,0.0299,0.0,0,3,0.0,0.0,6.0
1237,segment_0,dormant,0.0165,0.0,0,29,0.0,0.0,7.0
1238,segment_0,dormant,0.02,0.0,0,23,0.0,0.0,9.0
1239,segment_0,dormant,0.0164,0.0,0,27,0.0,0.0,7.0
1242,segment_1,at_risk,0.0475,0.0,0,0,0.0,0.0,11.0
1243,segment_1,dormant,0.0403,0.0,0,6,0.0,0.0,3.0
1244,segment_1,at_risk,0.0502,0.0,0,1,0.0,0.0,1.0
1245,segment_0,dormant,0.0428,25.99,1,26,25.99,0.1667,12.0
1246,segment_1,at_risk,0.0346,0.0,0,0,0.0,0.0,12.0
1247,segment_1,dormant,0.0316,0.0,0,3,0.0,0.0,5.0
1248,segment_1,dormant,0.0643,0.0,0,5,0.0,0.0,5.0
1249,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,7.0
1250,segment_3,at_risk,0.0316,28.99,1,6,28.99,0.25,1.0
1251,segment_1,at_risk,0.1116,0.0,0,0,0.0,0.0,3.0
1252,segment_0,dormant,0.0173,0.0,0,28,0.0,0.0,5.0
1253,segment_0,dormant,0.0191,0.0,0,24,0.0,0.0,7.0
1255,segment_1,dormant,0.0303,0.0,0,7,0.0,0.0,5.0
1258,segment_0,dormant,0.0329,0.0,0,14,0.0,0.0,7.0
1259,segment_0,dormant,0.0251,0.0,0,14,0.0,0.0,9.0
1262,segment_1,dormant,0.088,0.0,0,3,0.0,0.0,12.0
1263,segment_3,loyal,0.3153,116.98,2,15,58.49,0.0952,11.0
1264,segment_1,dormant,0.0204,0.0,0,3,0.0,0.0,9.0
1265,segment_3,loyal,0.0832,204.99,1,10,204.99,0.2,9.0
1266,segment_3,at_risk,0.0518,81.98,1,19,81.98,1.0,3.0
1267,segment_3,loyal,0.7571,59.97,3,15,19.99,0.1034,7.0
1268,segment_0,dormant,0.0693,14.99,1,20,14.99,0.125,4.0
1269,segment_1,at_risk,0.1058,31.99,1,9,31.99,0.125,10.0
1270,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,4.0
1271,segment_3,loyal,0.1134,120.48,2,8,60.24,0.4,11.0
1272,segment_1,dormant,0.0444,0.0,0,4,0.0,0.0,8.0
1273,segment_1,dormant,0.0356,0.0,0,6,0.0,0.0,1.0
1274,segment_1,dormant,0.0985,0.0,0,3,0.0,0.0,12.0
1277,segment_1,dormant,0.0477,0.0,0,3,0.0,0.0,5.0
1278,segment_1,dormant,0.0238,0.0,0,2,0.0,0.0,4.0
1279,segment_0,at_risk,0.267,27.98,1,25,27.98,0.0588,5.0
1281,segment_0,at_risk,0.0945,17.99,1,15,17.99,0.1,1.0
1282,segment_1,dormant,0.0536,0.0,0,6,0.0,0.0,8.0
1283,segment_1,at_risk,0.0591,0.0,0,0,0.0,0.0,5.0
1284,segment_1,dormant,0.0265,0.0,0,5,0.0,0.0,1.0
1285,segment_1,at_risk,0.0514,0.0,0,1,0.0,0.0,3.0
1286,segment_1,dormant,0.0222,0.0,0,2,0.0,0.0,11.0
1287,segment_1,dormant,0.0475,0.0,0,5,0.0,0.0,3.0
1289,segment_1,at_risk,0.029,0.0,0,0,0.0,0.0,12.0
1290,segment_1,at_risk,0.0519,0.0,0,1,0.0,0.0,7.0
1291,segment_2,at_risk,0.107,561.99,1,27,561.99,0.125,12.0
1292,segment_1,at_risk,0.1477,0.0,0,0,0.0,0.0,4.0
1294,segment_1,dormant,0.0195,0.0,0,3,0.0,0.0,3.0
1295,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,10.0
1296,segment_0,dormant,0.0164,0.0,0,30,0.0,0.0,11.0
1298,segment_1,dormant,0.0328,0.0,0,2,0.0,0.0,2.0
1300,segment_1,dormant,0.028,0.0,0,10,0.0,0.0,7.0
1301,segment_3,at_risk,0.0832,55.91,2,25,27.96,0.3333,4.0
1302,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,2.0
1304,segment_1,dormant,0.0387,0.0,0,6,0.0,0.0,5.0
1305,segment_1,dormant,0.0273,0.0,0,2,0.0,0.0,7.0
1306,segment_3,at_risk,0.1743,176.99,1,27,176.99,0.0556,5.0
1307,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,4.0
1308,segment_1,dormant,0.0747,0.0,0,5,0.0,0.0,5.0
1309,segment_3,loyal,0.121,123.47,1,7,123.47,0.0909,3.0
1310,segment_0,dormant,0.0371,0.0,0,13,0.0,0.0,8.0
1312,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,7.0
1313,segment_1,dormant,0.0212,0.0,0,4,0.0,0.0,1.0
1314,segment_0,dormant,0.067,8.49,1,19,8.49,0.125,5.0
1315,segment_1,dormant,0.0349,0.0,0,7,0.0,0.0,1.0
1316,segment_1,at_risk,0.0377,0.0,0,1,0.0,0.0,9.0
1317,segment_1,dormant,0.0384,0.0,0,4,0.0,0.0,10.0
1318,segment_1,at_risk,0.0795,0.0,0,0,0.0,0.0,6.0
1319,segment_1,at_risk,0.0341,0.0,0,1,0.0,0.0,1.0
1320,segment_1,dormant,0.033,0.0,0,9,0.0,0.0,2.0
1321,segment_1,dormant,0.0605,0.0,0,6,0.0,0.0,5.0
1322,segment_0,dormant,0.0368,0.0,0,17,0.0,0.0,2.0
1323,segment_1,dormant,0.0402,0.0,0,9,0.0,0.0,9.0
1326,segment_0,dormant,0.0577,23.99,1,18,23.99,0.1667,7.0
1327,segment_0,dormant,0.0313,0.0,0,17,0.0,0.0,10.0
1328,segment_1,at_risk,0.0319,0.0,0,1,0.0,0.0,5.0
1329,segment_0,dormant,0.0233,0.0,0,23,0.0,0.0,5.0
1330,segment_2,champions,0.5958,1360.44,5,0,272.09,0.1613,8.0
1331,segment_1,at_risk,0.0394,0.0,0,1,0.0,0.0,6.0
1332,segment_0,at_risk,0.0533,39.98,1,26,39.98,0.0714,3.0
1333,segment_1,dormant,0.0532,0.0,0,2,0.0,0.0,10.0
1334,segment_0,at_risk,0.1282,36.99,1,23,36.99,0.0667,2.0
1335,segment_1,dormant,0.0692,0.0,0,3,0.0,0.0,7.0
1336,segment_0,dormant,0.0292,0.0,0,14,0.0,0.0,5.0
1337,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,7.0
1339,segment_1,dormant,0.0427,0.0,0,7,0.0,0.0,2.0
1340,segment_1,at_risk,0.0283,0.0,0,1,0.0,0.0,5.0
1341,segment_3,loyal,0.3629,94.45,4,11,23.61,0.1739,5.0
1342,segment_3,at_risk,0.0278,18.98,1,6,18.98,0.3333,6.0
1343,segment_1,dormant,0.0379,0.0,0,3,0.0,0.0,5.0
1344,segment_1,dormant,0.0403,0.0,0,4,0.0,0.0,3.0
1345,segment_1,dormant,0.0238,0.0,0,2,0.0,0.0,11.0
1346,segment_3,at_risk,0.1562,298.98,1,29,298.98,0.0556,1.0
1347,segment_0,dormant,0.0548,0.0,0,13,0.0,0.0,10.0
1348,segment_1,dormant,0.031,0.0,0,7,0.0,0.0,4.0
1349,segment_1,dormant,0.035,0.0,0,8,0.0,0.0,12.0
1350,segment_1,dormant,0.0209,0.0,0,5,0.0,0.0,12.0
1351,segment_0,dormant,0.0205,0.0,0,21,0.0,0.0,6.0
1352,segment_1,dormant,0.037,0.0,0,11,0.0,0.0,5.0
1353,segment_1,dormant,0.0255,0.0,0,12,0.0,0.0,7.0
1354,segment_1,dormant,0.0397,0.0,0,10,0.0,0.0,1.0
1355,segment_1,dormant,0.0934,0.0,0,4,0.0,0.0,3.0
1356,segment_3,at_risk,0.0578,32.99,1,12,32.99,1.0,7.0
1357,segment_1,dormant,0.0315,0.0,0,12,0.0,0.0,3.0
1358,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,6.0
1359,segment_1,dormant,0.0165,0.0,0,4,0.0,0.0,7.0
1360,segment_1,at_risk,0.0392,0.0,0,1,0.0,0.0,4.0
1363,segment_1,at_risk,0.0334,0.0,0,0,0.0,0.0,12.0
1364,segment_1,dormant,0.0198,0.0,0,5,0.0,0.0,9.0
1365,segment_1,dormant,0.0227,0.0,0,6,0.0,0.0,1.0
1366,segment_1,dormant,0.0415,0.0,0,3,0.0,0.0,10.0
1368,segment_1,dormant,0.0271,0.0,0,12,0.0,0.0,4.0
1369,segment_1,dormant,0.0257,0.0,0,12,0.0,0.0,11.0
1370,segment_0,dormant,0.0338,0.0,0,14,0.0,0.0,9.0
1371,segment_1,at_risk,0.0774,0.0,0,1,0.0,0.0,4.0
1372,segment_1,at_risk,0.0941,0.0,0,0,0.0,0.0,6.0
1374,segment_0,dormant,0.0223,0.0,0,18,0.0,0.0,12.0
1375,segment_0,dormant,0.0457,0.0,0,14,0.0,0.0,1.0
1377,segment_1,at_risk,0.0169,0.0,0,0,0.0,0.0,3.0
1378,segment_1,loyal,0.0375,15.99,1,1,15.99,0.2,5.0
1379,segment_3,loyal,0.1571,225.96,2,9,112.98,0.1538,6.0
1380,segment_2,loyal,0.2041,479.98,2,10,239.99,0.1538,11.0
1383,segment_1,dormant,0.0291,0.0,0,4,0.0,0.0,11.0
1384,segment_1,loyal,0.0416,13.99,1,0,13.99,0.1667,9.0
1385,segment_1,dormant,0.0743,0.0,0,2,0.0,0.0,4.0
1386,segment_3,loyal,0.2166,116.98,2,8,58.49,0.1538,2.0
1387,segment_0,at_risk,0.0829,76.99,1,22,76.99,0.1,1.0
1388,segment_0,dormant,0.0435,17.99,1,26,17.99,0.25,3.0
1389,segment_0,dormant,0.0869,24.99,1,24,24.99,0.0909,1.0
1390,segment_0,at_risk,0.0824,13.99,1,12,13.99,0.1429,9.0
1391,segment_1,loyal,0.0867,53.99,1,2,53.99,0.0909,5.0
1392,segment_0,dormant,0.0355,0.0,0,14,0.0,0.0,5.0
1393,segment_1,dormant,0.0385,0.0,0,8,0.0,0.0,12.0
1394,segment_1,dormant,0.0281,0.0,0,3,0.0,0.0,11.0
1395,segment_0,dormant,0.0489,0.0,0,13,0.0,0.0,10.0
1396,segment_1,at_risk,0.0584,0.0,0,0,0.0,0.0,5.0
1397,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,1.0
1398,segment_1,at_risk,0.0469,0.0,0,1,0.0,0.0,3.0
1399,segment_1,dormant,0.0502,0.0,0,11,0.0,0.0,5.0
1400,segment_1,dormant,0.0384,0.0,0,10,0.0,0.0,8.0
1401,segment_1,dormant,0.0302,0.0,0,6,0.0,0.0,10.0
1402,segment_0,dormant,0.2569,26.99,1,18,26.99,0.0476,9.0
1403,segment_1,dormant,0.0281,0.0,0,2,0.0,0.0,1.0
1404,segment_1,dormant,0.0544,0.0,0,11,0.0,0.0,5.0
1405,segment_0,dormant,0.0178,0.0,0,26,0.0,0.0,2.0
1406,segment_0,dormant,0.0182,0.0,0,25,0.0,0.0,10.0
1407,segment_1,dormant,0.034,0.0,0,9,0.0,0.0,2.0
1408,segment_1,dormant,0.028,0.0,0,3,0.0,0.0,4.0
1409,segment_0,dormant,0.0233,0.0,0,17,0.0,0.0,1.0
1410,segment_1,dormant,0.0321,0.0,0,2,0.0,0.0,1.0
1411,segment_0,dormant,0.0257,0.0,0,13,0.0,0.0,5.0
1412,segment_1,dormant,0.0493,0.0,0,2,0.0,0.0,11.0
1413,segment_0,dormant,0.0222,0.0,0,19,0.0,0.0,5.0
1414,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,2.0
1415,segment_0,dormant,0.0471,17.99,1,28,17.99,0.2,7.0
1416,segment_1,dormant,0.0561,0.0,0,3,0.0,0.0,5.0
1417,segment_0,dormant,0.0274,0.0,0,20,0.0,0.0,7.0
1419,segment_2,champions,0.0527,1139.95,3,0,379.98,0.3333,1.0
1420,segment_1,at_risk,0.1524,0.0,0,1,0.0,0.0,6.0
1421,segment_0,dormant,0.03,0.0,0,14,0.0,0.0,2.0
1422,segment_3,at_risk,0.1251,52.9,2,18,26.45,0.1538,3.0
1423,segment_1,at_risk,0.0249,0.0,0,0,0.0,0.0,2.0
1425,segment_1,dormant,0.04,0.0,0,4,0.0,0.0,5.0
1426,segment_1,dormant,0.0457,0.0,0,12,0.0,0.0,11.0
1427,segment_1,at_risk,0.059,0.0,0,0,0.0,0.0,2.0
1428,segment_1,at_risk,0.0227,0.0,0,0,0.0,0.0,9.0
1429,segment_1,at_risk,0.064,8.49,1,5,8.49,0.1111,8.0
1430,segment_3,at_risk,0.048,93.98,1,25,93.98,0.2,4.0
1431,segment_1,dormant,0.0322,0.0,0,12,0.0,0.0,4.0
1432,segment_3,loyal,0.059,149.99,1,2,149.99,0.125,6.0
1433,segment_1,at_risk,0.0361,0.0,0,1,0.0,0.0,5.0
1434,segment_1,dormant,0.0293,0.0,0,8,0.0,0.0,2.0
1435,segment_1,at_risk,0.0263,0.0,0,1,0.0,0.0,1.0
1436,segment_0,dormant,0.0208,0.0,0,16,0.0,0.0,3.0
1437,segment_1,dormant,0.0263,0.0,0,4,0.0,0.0,6.0
1438,segment_1,dormant,0.0359,0.0,0,6,0.0,0.0,5.0
1439,segment_1,dormant,0.0231,0.0,0,5,0.0,0.0,6.0
1440,segment_1,dormant,0.0287,0.0,0,2,0.0,0.0,4.0
1441,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,7.0
1443,segment_3,at_risk,0.0878,144.99,1,29,144.99,0.1,12.0
1444,segment_0,dormant,0.0265,0.0,0,17,0.0,0.0,11.0
1446,segment_0,dormant,0.0229,0.0,0,18,0.0,0.0,3.0
1447,segment_0,dormant,0.0364,0.0,0,13,0.0,0.0,11.0
1448,segment_0,dormant,0.0226,0.0,0,17,0.0,0.0,2.0
1449,segment_1,at_risk,0.063,0.0,0,1,0.0,0.0,12.0
1450,segment_1,dormant,0.0461,0.0,0,7,0.0,0.0,5.0
1451,segment_1,dormant,0.0325,0.0,0,9,0.0,0.0,10.0
1453,segment_0,dormant,0.0237,0.0,0,16,0.0,0.0,4.0
1454,segment_0,dormant,0.0161,0.0,0,29,0.0,0.0,11.0
1457,segment_0,at_risk,0.1042,6.98,1,13,6.98,0.1111,3.0
1459,segment_1,at_risk,0.0508,0.0,0,0,0.0,0.0,7.0
1460,segment_0,dormant,0.0256,0.0,0,14,0.0,0.0,8.0
1461,segment_0,dormant,0.019,0.0,0,24,0.0,0.0,5.0
1462,segment_3,loyal,0.1711,129.98,2,14,64.99,0.1818,11.0
1463,segment_3,loyal,0.0833,266.98,2,27,133.49,0.2222,5.0
1464,segment_0,dormant,0.0249,0.0,0,19,0.0,0.0,1.0
1465,segment_3,champions,0.6906,289.45,5,2,57.89,0.1389,2.0
1466,segment_1,dormant,0.0303,0.0,0,8,0.0,0.0,7.0
1467,segment_1,dormant,0.0326,0.0,0,11,0.0,0.0,6.0
1468,segment_3,dormant,0.05,9.49,1,20,9.49,0.3333,7.0
1469,segment_1,dormant,0.0514,0.0,0,6,0.0,0.0,1.0
1470,segment_0,at_risk,0.1594,14.99,1,11,14.99,0.0833,1.0
1472,segment_1,dormant,0.0268,0.0,0,11,0.0,0.0,10.0
1473,segment_1,dormant,0.0743,0.0,0,10,0.0,0.0,5.0
1474,segment_0,dormant,0.0649,0.0,0,14,0.0,0.0,10.0
1476,segment_0,dormant,0.019,0.0,0,22,0.0,0.0,8.0
1477,segment_3,at_risk,0.0377,59.99,1,27,59.99,0.3333,5.0
1478,segment_1,at_risk,0.0777,0.0,0,1,0.0,0.0,7.0
1479,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,2.0
1480,segment_1,dormant,0.0437,0.0,0,5,0.0,0.0,2.0
1481,segment_1,at_risk,0.1284,0.0,0,0,0.0,0.0,5.0
1483,segment_1,dormant,0.0318,0.0,0,11,0.0,0.0,6.0
1484,segment_3,at_risk,0.1231,46.94,2,21,23.47,0.1667,5.0
1485,segment_1,dormant,0.0408,0.0,0,11,0.0,0.0,12.0
1487,segment_1,at_risk,0.0169,0.0,0,0,0.0,0.0,7.0
1488,segment_1,dormant,0.0433,0.0,0,3,0.0,0.0,1.0
1489,segment_0,dormant,0.022,0.0,0,19,0.0,0.0,5.0
1490,segment_3,champions,0.0808,84.98,2,0,42.49,0.1818,7.0
1491,segment_0,dormant,0.0182,0.0,0,26,0.0,0.0,12.0
1493,segment_0,dormant,0.0222,0.0,0,16,0.0,0.0,11.0
1494,segment_1,at_risk,0.095,0.0,0,1,0.0,0.0,3.0
1496,segment_1,dormant,0.0268,0.0,0,2,0.0,0.0,8.0
1500,segment_1,dormant,0.0545,0.0,0,2,0.0,0.0,9.0
1501,segment_1,dormant,0.0288,0.0,0,5,0.0,0.0,2.0
1502,segment_1,dormant,0.084,0.0,0,2,0.0,0.0,5.0
1503,segment_3,champions,0.1183,119.46,3,2,39.82,0.1429,4.0
1504,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,8.0
1505,segment_1,dormant,0.0567,0.0,0,8,0.0,0.0,7.0
1506,segment_3,at_risk,0.0344,77.0,1,27,77.0,0.3333,7.0
1507,segment_0,dormant,0.0158,0.0,0,30,0.0,0.0,3.0
1508,segment_1,dormant,0.0314,0.0,0,3,0.0,0.0,2.0
1509,segment_1,at_risk,0.0423,0.0,0,0,0.0,0.0,1.0
1510,segment_1,dormant,0.0727,0.0,0,2,0.0,0.0,5.0
1511,segment_1,dormant,0.0193,0.0,0,4,0.0,0.0,10.0
1512,segment_0,dormant,0.0211,0.0,0,20,0.0,0.0,9.0
1513,segment_1,dormant,0.0159,0.0,0,2,0.0,0.0,7.0
1514,segment_1,dormant,0.0293,0.0,0,2,0.0,0.0,6.0
1515,segment_1,at_risk,0.031,0.0,0,0,0.0,0.0,2.0
1516,segment_0,dormant,0.025,0.0,0,14,0.0,0.0,8.0
1517,segment_1,dormant,0.0328,0.0,0,2,0.0,0.0,10.0
1518,segment_1,dormant,0.0315,0.0,0,7,0.0,0.0,12.0
1519,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,8.0
1521,segment_0,dormant,0.0184,0.0,0,26,0.0,0.0,12.0
1522,segment_1,dormant,0.0571,0.0,0,5,0.0,0.0,5.0
1523,segment_1,dormant,0.1,0.0,0,2,0.0,0.0,10.0
1525,segment_0,dormant,0.0183,0.0,0,25,0.0,0.0,12.0
1526,segment_0,dormant,0.0167,0.0,0,29,0.0,0.0,2.0
1527,segment_0,dormant,0.0245,0.0,0,15,0.0,0.0,12.0
1528,segment_0,dormant,0.0191,0.0,0,23,0.0,0.0,1.0
1529,segment_1,dormant,0.0337,0.0,0,6,0.0,0.0,2.0
1530,segment_1,dormant,0.0654,0.0,0,12,0.0,0.0,8.0
1531,segment_0,dormant,0.0227,0.0,0,22,0.0,0.0,5.0
1532,segment_1,dormant,0.0203,0.0,0,5,0.0,0.0,12.0
1533,segment_0,at_risk,0.1824,32.99,1,15,32.99,0.05,5.0
1534,segment_1,dormant,0.1499,0.0,0,3,0.0,0.0,11.0
1535,segment_1,dormant,0.0533,0.0,0,8,0.0,0.0,1.0
1536,segment_1,dormant,0.0309,0.0,0,4,0.0,0.0,8.0
1537,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,9.0
1538,segment_1,at_risk,0.0788,0.0,0,0,0.0,0.0,9.0
1539,segment_1,dormant,0.0442,0.0,0,7,0.0,0.0,4.0
1540,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,1.0
1542,segment_1,dormant,0.0318,0.0,0,10,0.0,0.0,2.0
1543,segment_3,at_risk,0.0514,23.99,1,12,23.99,1.0,3.0
1544,segment_3,at_risk,0.0503,30.99,1,18,30.99,0.3333,9.0
1545,segment_1,dormant,0.0333,0.0,0,5,0.0,0.0,3.0
1547,segment_0,dormant,0.0177,0.0,0,26,0.0,0.0,3.0
1548,segment_1,dormant,0.0548,0.0,0,3,0.0,0.0,5.0
1549,segment_1,at_risk,0.0334,0.0,0,0,0.0,0.0,10.0
1550,segment_1,at_risk,0.0242,0.0,0,0,0.0,0.0,10.0
1551,segment_1,dormant,0.0472,0.0,0,9,0.0,0.0,4.0
1552,segment_0,dormant,0.0249,0.0,0,15,0.0,0.0,10.0
1554,segment_3,loyal,0.227,92.43,2,13,46.22,0.1111,7.0
1556,segment_1,dormant,0.0611,0.0,0,3,0.0,0.0,12.0
1557,segment_1,at_risk,0.0481,0.0,0,0,0.0,0.0,5.0
1558,segment_1,at_risk,0.0847,7.49,1,7,7.49,0.1667,8.0
1559,segment_1,dormant,0.0321,0.0,0,2,0.0,0.0,2.0
1561,segment_1,dormant,0.0323,0.0,0,12,0.0,0.0,2.0
1562,segment_0,dormant,0.021,0.0,0,20,0.0,0.0,1.0
1563,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,9.0
1564,segment_1,dormant,0.0344,0.0,0,5,0.0,0.0,2.0
1565,segment_0,dormant,0.0161,0.0,0,29,0.0,0.0,10.0
1566,segment_1,dormant,0.0363,0.0,0,8,0.0,0.0,7.0
1568,segment_0,dormant,0.0168,0.0,0,28,0.0,0.0,7.0
1569,segment_1,at_risk,0.0465,0.0,0,0,0.0,0.0,7.0
1570,segment_1,dormant,0.0427,0.0,0,5,0.0,0.0,11.0
1571,segment_1,at_risk,0.0467,0.0,0,0,0.0,0.0,2.0
1573,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,5.0
1574,segment_1,dormant,0.1165,0.0,0,3,0.0,0.0,5.0
1575,segment_1,dormant,0.0275,0.0,0,11,0.0,0.0,1.0
1576,segment_0,dormant,0.0433,10.99,1,25,10.99,0.0909,8.0
1577,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,11.0
1578,segment_1,at_risk,0.0313,0.0,0,0,0.0,0.0,7.0
1579,segment_1,dormant,0.1025,0.0,0,2,0.0,0.0,6.0
1580,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,1.0
1581,segment_0,dormant,0.0167,0.0,0,29,0.0,0.0,8.0
1583,segment_0,dormant,0.0193,0.0,0,28,0.0,0.0,5.0
1584,segment_1,dormant,0.0189,0.0,0,2,0.0,0.0,4.0
1585,segment_1,dormant,0.0962,0.0,0,4,0.0,0.0,9.0
1586,segment_3,loyal,0.0401,189.98,2,6,94.99,0.4,4.0
1587,segment_1,dormant,0.0338,0.0,0,4,0.0,0.0,9.0
1588,segment_1,dormant,0.0684,0.0,0,11,0.0,0.0,2.0
1589,segment_1,dormant,0.0441,0.0,0,5,0.0,0.0,2.0
1591,segment_1,dormant,0.0466,0.0,0,3,0.0,0.0,6.0
1593,segment_3,loyal,0.1304,44.98,2,12,22.49,0.25,1.0
1594,segment_0,dormant,0.0207,0.0,0,19,0.0,0.0,5.0
1595,segment_3,loyal,0.1937,192.62,4,6,48.16,0.3333,12.0
1596,segment_1,dormant,0.0303,0.0,0,8,0.0,0.0,6.0
1597,segment_0,dormant,0.0178,0.0,0,25,0.0,0.0,5.0
1598,segment_1,dormant,0.0233,0.0,0,3,0.0,0.0,3.0
1599,segment_0,dormant,0.0223,0.0,0,19,0.0,0.0,10.0
1600,segment_1,dormant,0.023,0.0,0,3,0.0,0.0,2.0
1601,segment_0,dormant,0.0214,0.0,0,19,0.0,0.0,2.0
1603,segment_1,dormant,0.0365,0.0,0,6,0.0,0.0,11.0
1604,segment_1,dormant,0.0168,0.0,0,6,0.0,0.0,2.0
1605,segment_0,dormant,0.0185,0.0,0,25,0.0,0.0,9.0
1606,segment_1,dormant,0.0313,0.0,0,2,0.0,0.0,2.0
1607,segment_0,dormant,0.0194,0.0,0,24,0.0,0.0,10.0
1608,segment_1,dormant,0.0281,0.0,0,11,0.0,0.0,10.0
1609,segment_1,dormant,0.0299,0.0,0,11,0.0,0.0,12.0
1611,segment_1,at_risk,0.0988,31.99,1,8,31.99,0.1667,9.0
1612,segment_1,dormant,0.0447,0.0,0,8,0.0,0.0,11.0
1613,segment_1,dormant,0.0273,0.0,0,12,0.0,0.0,12.0
1614,segment_1,dormant,0.0482,0.0,0,9,0.0,0.0,2.0
1615,segment_0,dormant,0.0239,0.0,0,15,0.0,0.0,9.0
1616,segment_0,dormant,0.0246,0.0,0,13,0.0,0.0,6.0
1617,segment_1,dormant,0.0621,0.0,0,2,0.0,0.0,2.0
1618,segment_0,dormant,0.0193,0.0,0,24,0.0,0.0,11.0
1620,segment_1,dormant,0.0454,0.0,0,3,0.0,0.0,5.0
1621,segment_0,dormant,0.0237,0.0,0,13,0.0,0.0,6.0
1622,segment_1,dormant,0.0465,0.0,0,4,0.0,0.0,3.0
1624,segment_0,dormant,0.0168,0.0,0,28,0.0,0.0,10.0
1625,segment_1,dormant,0.0326,0.0,0,10,0.0,0.0,5.0
1626,segment_0,dormant,0.0743,23.32,1,28,23.32,0.0909,5.0
1627,segment_1,dormant,0.033,0.0,0,9,0.0,0.0,9.0
1628,segment_1,dormant,0.0368,0.0,0,12,0.0,0.0,7.0
1629,segment_1,at_risk,0.1277,11.99,1,10,11.99,0.0909,2.0
1630,segment_1,dormant,0.0903,0.0,0,6,0.0,0.0,3.0
1635,segment_1,dormant,0.0264,0.0,0,5,0.0,0.0,6.0
1636,segment_1,at_risk,0.0462,0.0,0,1,0.0,0.0,7.0
1638,segment_1,at_risk,0.0904,0.0,0,1,0.0,0.0,12.0
1639,segment_0,dormant,0.0233,0.0,0,17,0.0,0.0,9.0
1640,segment_1,dormant,0.0415,0.0,0,3,0.0,0.0,7.0
1641,segment_0,dormant,0.0172,0.0,0,27,0.0,0.0,11.0
1642,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,5.0
1644,segment_1,at_risk,0.024,0.0,0,0,0.0,0.0,1.0
1645,segment_1,dormant,0.0405,0.0,0,7,0.0,0.0,4.0
1647,segment_3,dormant,0.0454,26.99,1,21,26.99,1.0,3.0
1649,segment_1,dormant,0.0285,0.0,0,10,0.0,0.0,9.0
1650,segment_1,dormant,0.0469,0.0,0,10,0.0,0.0,11.0
1651,segment_0,dormant,0.0189,0.0,0,25,0.0,0.0,4.0
1652,segment_0,at_risk,0.0585,43.99,1,24,43.99,0.1111,6.0
1653,segment_1,at_risk,0.0368,0.0,0,1,0.0,0.0,9.0
1654,segment_1,at_risk,0.025,0.0,0,0,0.0,0.0,10.0
1655,segment_0,dormant,0.0168,0.0,0,28,0.0,0.0,8.0
1656,segment_1,dormant,0.0292,0.0,0,9,0.0,0.0,5.0
1657,segment_1,dormant,0.058,0.0,0,4,0.0,0.0,5.0
1658,segment_1,dormant,0.1129,0.0,0,5,0.0,0.0,1.0
1659,segment_1,dormant,0.0486,0.0,0,9,0.0,0.0,4.0
1660,segment_3,champions,0.3105,116.46,3,3,38.82,0.1579,4.0
1661,segment_0,dormant,0.016,0.0,0,29,0.0,0.0,5.0
1664,segment_0,dormant,0.0218,0.0,0,20,0.0,0.0,9.0
1665,segment_1,dormant,0.0633,0.0,0,3,0.0,0.0,9.0
1666,segment_0,dormant,0.0323,0.0,0,14,0.0,0.0,11.0
1668,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,2.0
1669,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,3.0
1670,segment_2,loyal,0.2437,507.98,1,2,507.98,0.0435,5.0
1671,segment_2,champions,0.7628,744.94,3,2,248.31,0.0833,2.0
1672,segment_1,at_risk,0.0162,0.0,0,0,0.0,0.0,4.0
1673,segment_1,dormant,0.067,0.0,0,3,0.0,0.0,9.0
1674,segment_1,at_risk,0.0375,0.0,0,0,0.0,0.0,5.0
1675,segment_2,at_risk,0.1079,372.99,1,19,372.99,0.125,2.0
1677,segment_0,at_risk,0.0567,117.99,1,30,117.99,0.125,2.0
1678,segment_1,at_risk,0.035,0.0,0,0,0.0,0.0,4.0
1679,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,7.0
1680,segment_3,loyal,0.1119,41.98,2,17,20.99,0.2,11.0
1681,segment_0,dormant,0.0463,0.0,0,18,0.0,0.0,11.0
1682,segment_0,dormant,0.0179,0.0,0,25,0.0,0.0,7.0
1683,segment_1,dormant,0.0427,0.0,0,2,0.0,0.0,3.0
1684,segment_1,at_risk,0.0194,0.0,0,0,0.0,0.0,9.0
1685,segment_1,at_risk,0.0966,0.0,0,0,0.0,0.0,3.0
1687,segment_1,at_risk,0.0465,0.0,0,0,0.0,0.0,5.0
1688,segment_1,at_risk,0.0466,0.0,0,0,0.0,0.0,1.0
1689,segment_1,at_risk,0.0385,0.0,0,1,0.0,0.0,11.0
1690,segment_1,dormant,0.0414,0.0,0,10,0.0,0.0,1.0
1691,segment_1,at_risk,0.0601,0.0,0,0,0.0,0.0,1.0
1692,segment_1,at_risk,0.0625,0.0,0,0,0.0,0.0,1.0
1694,segment_0,dormant,0.0288,0.0,0,16,0.0,0.0,5.0
1695,segment_0,dormant,0.0246,0.0,0,14,0.0,0.0,5.0
1696,segment_1,dormant,0.0376,0.0,0,3,0.0,0.0,3.0
1697,segment_1,at_risk,0.0438,0.0,0,0,0.0,0.0,11.0
1698,segment_1,dormant,0.0312,0.0,0,11,0.0,0.0,6.0
1699,segment_1,at_risk,0.056,0.0,0,1,0.0,0.0,9.0
1701,segment_0,dormant,0.0237,0.0,0,16,0.0,0.0,8.0
1703,segment_0,dormant,0.049,14.99,1,29,14.99,0.2,3.0
1704,segment_1,at_risk,0.0897,8.98,1,7,8.98,0.1111,5.0
1705,segment_0,dormant,0.0529,0.0,0,17,0.0,0.0,9.0
1706,segment_1,dormant,0.0605,0.0,0,4,0.0,0.0,7.0
1707,segment_1,dormant,0.0462,0.0,0,2,0.0,0.0,1.0
1708,segment_3,at_risk,0.0323,34.99,1,29,34.99,1.0,1.0
1709,segment_0,dormant,0.0536,7.76,1,29,7.76,0.1,2.0
1711,segment_1,dormant,0.0409,0.0,0,5,0.0,0.0,10.0
1712,segment_3,loyal,0.4503,48.97,3,4,16.32,0.1154,3.0
1713,segment_1,dormant,0.0629,0.0,0,10,0.0,0.0,2.0
1715,segment_3,at_risk,0.0476,5.49,1,17,5.49,0.3333,8.0
1716,segment_1,dormant,0.0388,0.0,0,12,0.0,0.0,12.0
1717,segment_1,dormant,0.0528,0.0,0,3,0.0,0.0,6.0
1718,segment_3,champions,0.138,476.97,3,5,158.99,0.2308,2.0
1719,segment_0,dormant,0.021,0.0,0,20,0.0,0.0,2.0
1720,segment_0,dormant,0.0189,0.0,0,25,0.0,0.0,2.0
1723,segment_0,dormant,0.0178,0.0,0,26,0.0,0.0,1.0
1724,segment_0,dormant,0.0306,0.0,0,13,0.0,0.0,3.0
1725,segment_1,dormant,0.0355,0.0,0,4,0.0,0.0,4.0
1726,segment_1,dormant,0.0311,0.0,0,10,0.0,0.0,1.0
1727,segment_1,dormant,0.0436,0.0,0,2,0.0,0.0,2.0
1728,segment_1,dormant,0.0392,0.0,0,9,0.0,0.0,3.0
1729,segment_1,at_risk,0.0564,0.0,0,0,0.0,0.0,11.0
1730,segment_1,dormant,0.0399,0.0,0,5,0.0,0.0,1.0
1731,segment_1,dormant,0.0287,0.0,0,3,0.0,0.0,12.0
1732,segment_1,dormant,0.1162,0.0,0,5,0.0,0.0,3.0
1733,segment_0,dormant,0.0184,0.0,0,26,0.0,0.0,9.0
1734,segment_0,dormant,0.0411,0.0,0,15,0.0,0.0,6.0
1735,segment_1,dormant,0.0303,0.0,0,6,0.0,0.0,4.0
1737,segment_1,dormant,0.0467,0.0,0,11,0.0,0.0,9.0
1738,segment_3,loyal,0.1107,167.99,1,1,167.99,0.0588,9.0
1739,segment_1,at_risk,0.0394,0.0,0,0,0.0,0.0,1.0
1740,segment_1,dormant,0.0292,0.0,0,12,0.0,0.0,5.0
1741,segment_1,dormant,0.0379,0.0,0,5,0.0,0.0,10.0
1742,segment_1,at_risk,0.131,14.99,1,10,14.99,0.1,3.0
1743,segment_1,at_risk,0.0343,0.0,0,1,0.0,0.0,5.0
1744,segment_1,dormant,0.0339,0.0,0,8,0.0,0.0,5.0
1746,segment_0,dormant,0.0231,0.0,0,17,0.0,0.0,7.0
1747,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,6.0
1748,segment_1,dormant,0.0408,0.0,0,10,0.0,0.0,11.0
1749,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,2.0
1750,segment_1,dormant,0.0233,0.0,0,3,0.0,0.0,3.0
1751,segment_1,at_risk,0.0401,0.0,0,0,0.0,0.0,4.0
1752,segment_1,at_risk,0.0339,0.0,0,1,0.0,0.0,5.0
1753,segment_3,loyal,0.0188,46.99,1,3,46.99,0.25,4.0
1754,segment_1,dormant,0.0727,0.0,0,2,0.0,0.0,2.0
1755,segment_2,at_risk,0.0843,561.99,1,28,561.99,0.1667,3.0
1756,segment_1,at_risk,0.019,0.0,0,0,0.0,0.0,6.0
1757,segment_1,dormant,0.0347,0.0,0,12,0.0,0.0,8.0
1758,segment_1,dormant,0.1326,0.0,0,4,0.0,0.0,5.0
1759,segment_1,at_risk,0.0583,0.0,0,1,0.0,0.0,10.0
1760,segment_1,at_risk,0.0414,23.99,1,5,23.99,0.125,10.0
1761,segment_1,dormant,0.0191,0.0,0,2,0.0,0.0,1.0
1763,segment_0,dormant,0.02,0.0,0,23,0.0,0.0,10.0
1764,segment_0,dormant,0.0229,0.0,0,18,0.0,0.0,7.0
1765,segment_1,at_risk,0.0534,0.0,0,0,0.0,0.0,10.0
1766,segment_1,at_risk,0.0736,10.98,1,3,10.98,0.0667,6.0
1767,segment_0,dormant,0.0202,0.0,0,20,0.0,0.0,4.0
1768,segment_0,dormant,0.042,15.52,1,28,15.52,0.1667,6.0
1769,segment_1,at_risk,0.081,0.0,0,0,0.0,0.0,5.0
1770,segment_0,dormant,0.0366,0.0,0,16,0.0,0.0,11.0
1771,segment_3,at_risk,0.0554,76.99,1,27,76.99,0.2,1.0
1773,segment_1,at_risk,0.074,0.0,0,1,0.0,0.0,5.0
1774,segment_1,dormant,0.0312,0.0,0,3,0.0,0.0,11.0
1775,segment_1,dormant,0.0289,0.0,0,10,0.0,0.0,9.0
1776,segment_0,dormant,0.032,0.0,0,16,0.0,0.0,12.0
1777,segment_1,dormant,0.0414,0.0,0,7,0.0,0.0,6.0
1778,segment_1,dormant,0.024,0.0,0,6,0.0,0.0,3.0
1779,segment_1,at_risk,0.0177,0.0,0,1,0.0,0.0,1.0
1780,segment_0,dormant,0.1598,23.99,1,28,23.99,0.0588,11.0
1781,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,10.0
1782,segment_1,dormant,0.0502,0.0,0,7,0.0,0.0,1.0
1783,segment_1,at_risk,0.0281,0.0,0,1,0.0,0.0,4.0
1784,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,9.0
1785,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,9.0
1786,segment_1,dormant,0.0255,0.0,0,2,0.0,0.0,9.0
1787,segment_1,at_risk,0.0516,0.0,0,1,0.0,0.0,10.0
1788,segment_1,dormant,0.0274,0.0,0,3,0.0,0.0,2.0
1789,segment_1,dormant,0.0753,0.0,0,10,0.0,0.0,3.0
1790,segment_3,champions,0.1486,163.95,2,0,81.98,0.1111,11.0
1791,segment_1,at_risk,0.2837,0.0,0,0,0.0,0.0,9.0
1792,segment_1,at_risk,0.0231,0.0,0,1,0.0,0.0,8.0
1793,segment_3,at_risk,0.1127,44.98,2,21,22.49,0.2,11.0
1794,segment_1,at_risk,0.022,0.0,0,0,0.0,0.0,10.0
1795,segment_1,at_risk,0.0458,0.0,0,0,0.0,0.0,2.0
1796,segment_1,dormant,0.0416,0.0,0,10,0.0,0.0,3.0
1798,segment_3,loyal,0.1223,88.77,2,12,44.38,0.1818,12.0
1799,segment_0,dormant,0.0225,0.0,0,18,0.0,0.0,8.0
1800,segment_0,dormant,0.0229,0.0,0,16,0.0,0.0,3.0
1801,segment_1,at_risk,0.0259,0.0,0,1,0.0,0.0,4.0
1802,segment_3,champions,0.1273,83.96,3,2,27.99,0.1875,6.0
1803,segment_2,champions,0.8342,1019.96,3,0,339.99,0.0732,7.0
1805,segment_1,dormant,0.0282,0.0,0,9,0.0,0.0,1.0
1806,segment_1,dormant,0.0555,0.0,0,8,0.0,0.0,12.0
1807,segment_1,dormant,0.0411,0.0,0,2,0.0,0.0,7.0
1808,segment_0,dormant,0.0184,0.0,0,26,0.0,0.0,11.0
1809,segment_0,at_risk,0.1442,36.98,1,27,36.98,0.0667,7.0
1810,segment_1,dormant,0.0285,0.0,0,10,0.0,0.0,8.0
1811,segment_0,at_risk,0.1714,37.99,1,21,37.99,0.0625,4.0
1812,segment_1,dormant,0.0408,0.0,0,4,0.0,0.0,3.0
1813,segment_1,dormant,0.0303,0.0,0,7,0.0,0.0,3.0
1814,segment_1,dormant,0.0514,0.0,0,3,0.0,0.0,8.0
1816,segment_1,dormant,0.0326,0.0,0,12,0.0,0.0,9.0
1817,segment_0,dormant,0.0278,0.0,0,19,0.0,0.0,4.0
1818,segment_0,at_risk,0.2442,13.99,1,17,13.99,0.0435,11.0
1819,segment_0,dormant,0.0222,0.0,0,16,0.0,0.0,4.0
1820,segment_1,dormant,0.0344,0.0,0,6,0.0,0.0,6.0
1821,segment_1,dormant,0.0344,0.0,0,7,0.0,0.0,4.0
1822,segment_0,dormant,0.029,0.0,0,13,0.0,0.0,2.0
1823,segment_1,at_risk,0.0317,0.0,0,1,0.0,0.0,3.0
1824,segment_1,dormant,0.0406,0.0,0,10,0.0,0.0,7.0
1825,segment_0,dormant,0.0169,0.0,0,28,0.0,0.0,5.0
1826,segment_1,at_risk,0.0424,0.0,0,0,0.0,0.0,7.0
1827,segment_1,dormant,0.0696,0.0,0,3,0.0,0.0,5.0
1828,segment_3,at_risk,0.0604,245.98,1,21,245.98,0.5,5.0
1831,segment_0,dormant,0.0182,0.0,0,26,0.0,0.0,4.0
1832,segment_1,dormant,0.0381,0.0,0,4,0.0,0.0,9.0
1833,segment_3,at_risk,0.0565,76.99,1,6,76.99,0.1111,11.0
1834,segment_1,at_risk,0.0665,0.0,0,0,0.0,0.0,8.0
1835,segment_0,dormant,0.0212,0.0,0,21,0.0,0.0,5.0
1836,segment_1,dormant,0.1167,0.0,0,2,0.0,0.0,10.0
1838,segment_0,dormant,0.1286,21.36,1,28,21.36,0.0714,5.0
1839,segment_1,dormant,0.1101,0.0,0,2,0.0,0.0,5.0
1840,segment_1,at_risk,0.0488,0.0,0,0,0.0,0.0,6.0
1841,segment_1,dormant,0.0402,0.0,0,7,0.0,0.0,8.0
1842,segment_1,at_risk,0.0484,0.0,0,0,0.0,0.0,2.0
1843,segment_0,dormant,0.0219,0.0,0,19,0.0,0.0,9.0
1844,segment_0,at_risk,0.0844,19.99,1,14,19.99,0.0833,3.0
1846,segment_1,dormant,0.0742,0.0,0,10,0.0,0.0,6.0
1847,segment_2,loyal,0.3692,440.99,1,13,440.99,0.0476,7.0
1848,segment_0,at_risk,0.1059,17.99,1,12,17.99,0.0909,7.0
1850,segment_0,dormant,0.0174,0.0,0,27,0.0,0.0,5.0
1851,segment_1,dormant,0.032,0.0,0,2,0.0,0.0,4.0
1852,segment_3,dormant,0.0356,23.99,1,25,23.99,0.5,9.0
1853,segment_1,dormant,0.0376,0.0,0,5,0.0,0.0,2.0
1854,segment_1,dormant,0.0361,0.0,0,5,0.0,0.0,6.0
1855,segment_0,dormant,0.0416,0.0,0,13,0.0,0.0,6.0
1856,segment_0,dormant,0.0249,0.0,0,15,0.0,0.0,12.0
1857,segment_1,dormant,0.0251,0.0,0,2,0.0,0.0,3.0
1858,segment_1,dormant,0.0314,0.0,0,11,0.0,0.0,9.0
1859,segment_3,at_risk,0.2501,44.93,3,18,14.98,0.2143,10.0
1860,segment_1,at_risk,0.0417,0.0,0,1,0.0,0.0,2.0
1861,segment_1,dormant,0.0401,0.0,0,2,0.0,0.0,5.0
1862,segment_1,at_risk,0.0235,0.0,0,1,0.0,0.0,11.0
1864,segment_1,at_risk,0.0926,0.0,0,1,0.0,0.0,4.0
1865,segment_1,at_risk,0.1348,0.0,0,1,0.0,0.0,1.0
1867,segment_0,dormant,0.0246,0.0,0,14,0.0,0.0,4.0
1868,segment_0,dormant,0.0855,25.36,1,25,25.36,0.0909,6.0
1869,segment_0,dormant,0.0216,0.0,0,20,0.0,0.0,6.0
1870,segment_1,dormant,0.0186,0.0,0,3,0.0,0.0,12.0
1871,segment_1,dormant,0.0278,0.0,0,7,0.0,0.0,9.0
1873,segment_1,dormant,0.0602,0.0,0,3,0.0,0.0,5.0
1874,segment_1,dormant,0.0327,0.0,0,10,0.0,0.0,8.0
1875,segment_1,at_risk,0.2833,0.0,0,0,0.0,0.0,1.0
1876,segment_3,at_risk,0.0597,96.99,1,14,96.99,1.0,4.0
1877,segment_1,dormant,0.0271,0.0,0,2,0.0,0.0,6.0
1878,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,9.0
1879,segment_0,dormant,0.0172,0.0,0,26,0.0,0.0,1.0
1880,segment_0,at_risk,0.1203,41.99,1,27,41.99,0.0909,2.0
1881,segment_1,dormant,0.0384,0.0,0,12,0.0,0.0,11.0
1883,segment_1,dormant,0.0314,0.0,0,4,0.0,0.0,2.0
1884,segment_1,dormant,0.0172,0.0,0,6,0.0,0.0,1.0
1885,segment_0,dormant,0.0198,0.0,0,23,0.0,0.0,3.0
1886,segment_0,at_risk,0.1496,47.99,1,28,47.99,0.0588,1.0
1887,segment_1,dormant,0.0509,0.0,0,8,0.0,0.0,12.0
1889,segment_1,at_risk,0.0382,0.0,0,0,0.0,0.0,7.0
1890,segment_1,dormant,0.0307,0.0,0,7,0.0,0.0,3.0
1891,segment_1,dormant,0.0284,0.0,0,4,0.0,0.0,2.0
1892,segment_2,loyal,0.1075,413.98,1,5,413.98,0.0833,1.0
1893,segment_1,at_risk,0.0235,0.0,0,0,0.0,0.0,12.0
1894,segment_3,at_risk,0.1298,193.98,1,18,193.98,0.0714,9.0
1895,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,1.0
1896,segment_1,dormant,0.0404,0.0,0,10,0.0,0.0,2.0
1897,segment_1,dormant,0.0233,0.0,0,6,0.0,0.0,11.0
1899,segment_1,dormant,0.0424,0.0,0,6,0.0,0.0,9.0
1900,segment_2,champions,0.2629,1138.98,2,0,569.49,0.2222,5.0
1901,segment_0,at_risk,0.1351,46.99,1,24,46.99,0.0625,4.0
1902,segment_0,dormant,0.0203,0.0,0,22,0.0,0.0,9.0
1903,segment_1,dormant,0.036,0.0,0,5,0.0,0.0,3.0
1904,segment_1,dormant,0.0362,0.0,0,6,0.0,0.0,6.0
1906,segment_1,at_risk,0.0559,0.0,0,0,0.0,0.0,4.0
1908,segment_1,at_risk,0.0598,0.0,0,0,0.0,0.0,5.0
1910,segment_0,at_risk,0.1576,24.99,1,12,24.99,0.0625,1.0
1912,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,6.0
1913,segment_1,dormant,0.0369,0.0,0,2,0.0,0.0,11.0
1914,segment_1,dormant,0.0507,0.0,0,5,0.0,0.0,4.0
1915,segment_0,dormant,0.0217,0.0,0,18,0.0,0.0,6.0
1916,segment_1,dormant,0.0383,0.0,0,12,0.0,0.0,6.0
1917,segment_0,at_risk,0.0635,49.02,1,29,49.02,0.1,6.0
1918,segment_1,dormant,0.0226,0.0,0,4,0.0,0.0,1.0
1919,segment_1,dormant,0.0264,0.0,0,11,0.0,0.0,6.0
1921,segment_3,dormant,0.0499,24.99,1,18,24.99,0.25,1.0
1922,segment_1,dormant,0.0337,0.0,0,9,0.0,0.0,5.0
1923,segment_1,dormant,0.0688,0.0,0,2,0.0,0.0,7.0
1924,segment_0,dormant,0.0279,0.0,0,16,0.0,0.0,10.0
1925,segment_1,at_risk,0.036,0.0,0,0,0.0,0.0,5.0
1926,segment_1,dormant,0.0271,0.0,0,12,0.0,0.0,1.0
1927,segment_1,dormant,0.0305,0.0,0,5,0.0,0.0,2.0
1928,segment_1,dormant,0.0439,0.0,0,6,0.0,0.0,11.0
1929,segment_0,at_risk,0.0858,54.97,1,13,54.97,0.125,3.0
1931,segment_1,dormant,0.0284,0.0,0,4,0.0,0.0,5.0
1932,segment_1,dormant,0.0363,0.0,0,12,0.0,0.0,6.0
1935,segment_0,dormant,0.0213,0.0,0,20,0.0,0.0,9.0
1936,segment_0,dormant,0.0556,17.99,1,21,17.99,0.125,11.0
1937,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,5.0
1938,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,11.0
1939,segment_2,loyal,0.0538,628.97,2,24,314.48,0.3333,9.0
1940,segment_3,at_risk,0.0474,14.99,1,15,14.99,1.0,7.0
1941,segment_3,at_risk,0.0516,100.99,1,14,100.99,0.1667,2.0
1942,segment_1,dormant,0.0538,0.0,0,9,0.0,0.0,11.0
1943,segment_1,at_risk,0.0282,0.0,0,0,0.0,0.0,2.0
1944,segment_0,dormant,0.0344,0.0,0,15,0.0,0.0,3.0
1945,segment_1,dormant,0.0357,0.0,0,7,0.0,0.0,9.0
1946,segment_1,at_risk,0.0211,0.0,0,0,0.0,0.0,4.0
1947,segment_0,dormant,0.0265,0.0,0,13,0.0,0.0,2.0
1948,segment_1,at_risk,0.0202,0.0,0,0,0.0,0.0,6.0
1949,segment_1,dormant,0.0473,0.0,0,3,0.0,0.0,9.0
1950,segment_1,dormant,0.0282,0.0,0,9,0.0,0.0,2.0
1951,segment_0,dormant,0.0247,0.0,0,21,0.0,0.0,7.0
1953,segment_0,dormant,0.0478,2.3,1,29,2.3,0.1429,5.0
1955,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,3.0
1956,segment_1,dormant,0.039,0.0,0,3,0.0,0.0,12.0
1957,segment_0,dormant,0.0182,0.0,0,26,0.0,0.0,11.0
1958,segment_3,at_risk,0.0487,87.99,1,22,87.99,0.3333,4.0
1959,segment_1,at_risk,0.0538,0.0,0,0,0.0,0.0,1.0
1960,segment_1,at_risk,0.0222,0.0,0,0,0.0,0.0,7.0
1961,segment_3,at_risk,0.0405,105.98,1,28,105.98,0.5,10.0
1962,segment_3,champions,0.5025,345.97,2,4,172.98,0.0769,2.0
1964,segment_1,loyal,0.085,64.99,1,4,64.99,0.0833,1.0
1965,segment_3,at_risk,0.0518,23.99,1,11,23.99,0.5,5.0
1966,segment_1,dormant,0.035,0.0,0,8,0.0,0.0,6.0
1967,segment_0,dormant,0.0325,0.0,0,14,0.0,0.0,1.0
1968,segment_0,dormant,0.0194,0.0,0,24,0.0,0.0,9.0
1969,segment_3,at_risk,0.0502,89.99,1,21,89.99,0.25,9.0
1970,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,12.0
1971,segment_1,at_risk,0.0358,0.0,0,1,0.0,0.0,3.0
1972,segment_3,loyal,0.2651,294.11,2,9,147.06,0.1111,12.0
1973,segment_1,dormant,0.0306,0.0,0,8,0.0,0.0,9.0
1974,segment_1,at_risk,0.038,0.0,0,0,0.0,0.0,5.0
1975,segment_0,dormant,0.0347,0.0,0,15,0.0,0.0,3.0
1976,segment_3,loyal,0.2318,106.99,1,7,106.99,0.0625,2.0
1977,segment_0,dormant,0.0551,0.0,0,14,0.0,0.0,11.0
1978,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,11.0
1979,segment_3,loyal,0.1399,265.99,1,7,265.99,0.1667,9.0
1980,segment_1,dormant,0.0503,0.0,0,3,0.0,0.0,11.0
1982,segment_1,dormant,0.0404,0.0,0,9,0.0,0.0,4.0
1983,segment_1,at_risk,0.1939,0.0,0,1,0.0,0.0,6.0
1984,segment_3,at_risk,0.1404,157.98,1,25,157.98,0.0667,1.0
1985,segment_1,at_risk,0.0513,0.0,0,0,0.0,0.0,5.0
1986,segment_0,dormant,0.0331,0.0,0,13,0.0,0.0,5.0
1987,segment_1,dormant,0.0339,0.0,0,4,0.0,0.0,11.0
1988,segment_1,at_risk,0.2681,0.0,0,0,0.0,0.0,9.0
1989,segment_0,dormant,0.0216,0.0,0,20,0.0,0.0,2.0
1990,segment_1,at_risk,0.1396,0.0,0,1,0.0,0.0,10.0
1991,segment_1,dormant,0.1101,0.0,0,4,0.0,0.0,11.0
1993,segment_1,dormant,0.0316,0.0,0,10,0.0,0.0,4.0
1995,segment_1,at_risk,0.0925,0.0,0,0,0.0,0.0,7.0
1996,segment_1,at_risk,0.0304,0.0,0,1,0.0,0.0,4.0
1997,segment_1,dormant,0.0378,0.0,0,8,0.0,0.0,9.0
1998,segment_1,dormant,0.0686,0.0,0,4,0.0,0.0,12.0
1999,segment_0,at_risk,0.08,57.99,1,22,57.99,0.0909,1.0
2002,segment_1,at_risk,0.1772,0.0,0,0,0.0,0.0,6.0
2004,segment_2,at_risk,0.1224,673.98,1,19,673.98,0.1667,6.0
2005,segment_1,at_risk,0.049,0.0,0,1,0.0,0.0,6.0
2006,segment_0,dormant,0.0223,0.0,0,17,0.0,0.0,6.0
2008,segment_0,dormant,0.0225,0.0,0,18,0.0,0.0,3.0
2009,segment_0,dormant,0.0246,0.0,0,20,0.0,0.0,2.0
2010,segment_0,dormant,0.0235,0.0,0,16,0.0,0.0,10.0
2011,segment_1,dormant,0.0178,0.0,0,2,0.0,0.0,9.0
2012,segment_1,dormant,0.029,0.0,0,9,0.0,0.0,3.0
2013,segment_1,dormant,0.0422,0.0,0,2,0.0,0.0,7.0
2014,segment_1,at_risk,0.0703,0.0,0,0,0.0,0.0,8.0
2015,segment_1,dormant,0.0247,0.0,0,4,0.0,0.0,2.0
2017,segment_3,at_risk,0.1161,144.99,1,29,144.99,0.1111,5.0
2019,segment_1,dormant,0.0354,0.0,0,7,0.0,0.0,11.0
2020,segment_1,dormant,0.0457,0.0,0,4,0.0,0.0,12.0
2021,segment_0,dormant,0.0318,0.0,0,17,0.0,0.0,7.0
2022,segment_3,at_risk,0.0388,46.99,1,28,46.99,1.0,4.0
2023,segment_1,dormant,0.0307,0.0,0,7,0.0,0.0,1.0
2024,segment_3,at_risk,0.1441,204.99,1,27,204.99,0.0714,12.0
2025,segment_1,dormant,0.058,0.0,0,5,0.0,0.0,11.0
2026,segment_1,dormant,0.028,0.0,0,9,0.0,0.0,7.0
2028,segment_1,dormant,0.0347,0.0,0,2,0.0,0.0,7.0
2030,segment_0,dormant,0.0189,0.0,0,25,0.0,0.0,11.0
2031,segment_0,dormant,0.0308,0.0,0,18,0.0,0.0,4.0
2032,segment_1,dormant,0.0557,0.0,0,8,0.0,0.0,9.0
2033,segment_0,dormant,0.0178,0.0,0,26,0.0,0.0,2.0
2035,segment_0,dormant,0.0223,0.0,0,18,0.0,0.0,9.0
2036,segment_3,champions,0.1127,317.97,3,1,105.99,0.2143,12.0
2037,segment_0,dormant,0.0302,0.0,0,13,0.0,0.0,6.0
2038,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,6.0
2040,segment_0,at_risk,0.184,37.98,1,18,37.98,0.0526,10.0
2042,segment_3,at_risk,0.0819,89.99,1,11,89.99,0.25,9.0
2043,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,5.0
2044,segment_2,loyal,0.124,526.98,2,10,263.49,0.1818,12.0
2045,segment_1,dormant,0.0394,0.0,0,2,0.0,0.0,6.0
2046,segment_3,loyal,0.0489,69.97,2,6,34.98,0.2857,7.0
2047,segment_1,dormant,0.0772,0.0,0,6,0.0,0.0,10.0
2048,segment_1,dormant,0.0275,0.0,0,11,0.0,0.0,6.0
2049,segment_0,dormant,0.018,0.0,0,25,0.0,0.0,9.0
2050,segment_3,loyal,0.0957,50.98,2,6,25.49,0.1538,10.0
2051,segment_1,dormant,0.086,0.0,0,5,0.0,0.0,1.0
2052,segment_0,dormant,0.0377,0.0,0,13,0.0,0.0,6.0
2054,segment_1,at_risk,0.0323,0.0,0,0,0.0,0.0,6.0
2055,segment_1,dormant,0.0342,0.0,0,6,0.0,0.0,6.0
2057,segment_1,dormant,0.07,0.0,0,4,0.0,0.0,1.0
2059,segment_0,dormant,0.0458,10.99,1,23,10.99,0.2,7.0
2060,segment_1,dormant,0.025,0.0,0,11,0.0,0.0,6.0
2063,segment_1,dormant,0.0336,0.0,0,6,0.0,0.0,3.0
2064,segment_1,at_risk,0.0562,0.0,0,1,0.0,0.0,3.0
2065,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,2.0
2066,segment_1,at_risk,0.0489,0.0,0,0,0.0,0.0,1.0
2067,segment_3,at_risk,0.131,165.99,1,23,165.99,0.0909,9.0
2068,segment_1,dormant,0.0439,0.0,0,12,0.0,0.0,8.0
2069,segment_1,at_risk,0.1531,0.0,0,1,0.0,0.0,1.0
2070,segment_1,dormant,0.0252,0.0,0,11,0.0,0.0,12.0
2071,segment_1,dormant,0.0163,0.0,0,2,0.0,0.0,5.0
2072,segment_0,dormant,0.0265,0.0,0,13,0.0,0.0,5.0
2073,segment_1,dormant,0.0186,0.0,0,5,0.0,0.0,7.0
2074,segment_1,dormant,0.038,0.0,0,2,0.0,0.0,2.0
2075,segment_3,champions,0.2556,195.95,3,0,65.32,0.1364,4.0
2076,segment_1,loyal,0.0741,37.99,1,0,37.99,0.0714,2.0
2077,segment_1,dormant,0.0391,0.0,0,2,0.0,0.0,2.0
2078,segment_1,at_risk,0.0424,0.0,0,0,0.0,0.0,8.0
2079,segment_0,dormant,0.0158,0.0,0,30,0.0,0.0,7.0
2080,segment_3,loyal,0.1269,55.98,2,17,27.99,0.2,4.0
2081,segment_1,dormant,0.0506,0.0,0,4,0.0,0.0,5.0
2082,segment_0,at_risk,0.0484,90.99,1,25,90.99,0.1429,2.0
2083,segment_3,loyal,0.1473,45.98,2,7,22.99,0.2222,1.0
2084,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,3.0
2085,segment_1,dormant,0.04,0.0,0,8,0.0,0.0,1.0
2086,segment_1,dormant,0.0363,0.0,0,7,0.0,0.0,9.0
2087,segment_1,at_risk,0.0574,0.0,0,0,0.0,0.0,5.0
2088,segment_1,dormant,0.0337,0.0,0,4,0.0,0.0,9.0
2089,segment_1,dormant,0.0387,0.0,0,10,0.0,0.0,10.0
2090,segment_3,at_risk,0.0589,89.97,1,14,89.97,1.0,7.0
2092,segment_1,dormant,0.0345,0.0,0,3,0.0,0.0,6.0
2094,segment_1,at_risk,0.0467,0.0,0,0,0.0,0.0,4.0
2095,segment_3,loyal,0.1942,295.45,3,15,98.48,0.2143,5.0
2096,segment_1,dormant,0.0289,0.0,0,10,0.0,0.0,9.0
2097,segment_1,at_risk,0.1125,0.0,0,0,0.0,0.0,5.0
2098,segment_1,dormant,0.0304,0.0,0,2,0.0,0.0,1.0
2099,segment_0,dormant,0.0256,0.0,0,13,0.0,0.0,5.0
2100,segment_3,champions,0.1403,205.46,2,8,102.73,0.25,2.0
2101,segment_1,dormant,0.0306,0.0,0,10,0.0,0.0,5.0
2102,segment_1,at_risk,0.1001,0.0,0,0,0.0,0.0,1.0
2103,segment_1,dormant,0.0313,0.0,0,4,0.0,0.0,1.0
2104,segment_0,at_risk,0.3609,126.98,1,26,126.98,0.04,3.0
2105,segment_3,dormant,0.0504,15.99,1,19,15.99,0.3333,9.0
2106,segment_1,dormant,0.018,0.0,0,5,0.0,0.0,4.0
2107,segment_2,loyal,0.0557,522.98,1,5,522.98,0.1111,1.0
2108,segment_1,dormant,0.0307,0.0,0,7,0.0,0.0,8.0
2109,segment_3,dormant,0.044,5.49,1,19,5.49,0.5,6.0
2110,segment_3,loyal,0.1299,230.98,2,24,115.49,0.2,10.0
2111,segment_3,champions,0.1538,142.98,2,4,71.49,0.1538,2.0
2112,segment_1,dormant,0.0289,0.0,0,8,0.0,0.0,3.0
2113,segment_1,at_risk,0.0298,0.0,0,1,0.0,0.0,3.0
2114,segment_1,dormant,0.0672,0.0,0,4,0.0,0.0,9.0
2115,segment_1,dormant,0.0603,0.0,0,4,0.0,0.0,9.0
2117,segment_1,dormant,0.0321,0.0,0,11,0.0,0.0,7.0
2118,segment_3,at_risk,0.5145,190.99,1,9,190.99,0.0476,9.0
2119,segment_1,dormant,0.0449,0.0,0,2,0.0,0.0,5.0
2120,segment_1,dormant,0.0331,0.0,0,11,0.0,0.0,10.0
2121,segment_0,dormant,0.0261,0.0,0,19,0.0,0.0,2.0
2122,segment_1,at_risk,0.0449,0.0,0,0,0.0,0.0,4.0
2123,segment_1,at_risk,0.043,0.0,0,1,0.0,0.0,9.0
2125,segment_0,dormant,0.0235,0.0,0,16,0.0,0.0,6.0
2126,segment_0,dormant,0.0174,0.0,0,27,0.0,0.0,12.0
2127,segment_1,dormant,0.0299,0.0,0,7,0.0,0.0,7.0
2128,segment_1,at_risk,0.633,0.0,0,0,0.0,0.0,5.0
2129,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,2.0
2130,segment_1,dormant,0.0401,0.0,0,2,0.0,0.0,6.0
2131,segment_0,dormant,0.0254,0.0,0,14,0.0,0.0,9.0
2132,segment_2,loyal,0.1633,811.41,4,13,202.85,0.2353,11.0
2133,segment_0,dormant,0.0267,0.0,0,20,0.0,0.0,6.0
2134,segment_1,dormant,0.0381,0.0,0,10,0.0,0.0,6.0
2135,segment_3,loyal,0.1178,288.98,1,14,288.98,0.0909,7.0
2136,segment_1,dormant,0.0275,0.0,0,2,0.0,0.0,6.0
2138,segment_1,dormant,0.0299,0.0,0,8,0.0,0.0,5.0
2139,segment_1,at_risk,0.0573,0.0,0,1,0.0,0.0,5.0
2140,segment_1,dormant,0.0361,0.0,0,2,0.0,0.0,2.0
2141,segment_1,dormant,0.0294,0.0,0,7,0.0,0.0,8.0
2142,segment_1,dormant,0.0413,0.0,0,9,0.0,0.0,9.0
2143,segment_1,dormant,0.0392,0.0,0,9,0.0,0.0,2.0
2144,segment_1,dormant,0.0213,0.0,0,4,0.0,0.0,4.0
2145,segment_1,dormant,0.0261,0.0,0,6,0.0,0.0,2.0
2146,segment_3,champions,0.1199,400.97,3,4,133.66,0.2727,5.0
2148,segment_1,dormant,0.0287,0.0,0,5,0.0,0.0,4.0
2149,segment_3,at_risk,0.0401,7.49,1,17,7.49,0.25,5.0
2150,segment_1,at_risk,0.1383,0.0,0,0,0.0,0.0,4.0
2151,segment_0,dormant,0.0249,0.0,0,15,0.0,0.0,7.0
2153,segment_1,dormant,0.039,0.0,0,10,0.0,0.0,1.0
2154,segment_1,dormant,0.0572,0.0,0,3,0.0,0.0,2.0
2155,segment_1,at_risk,0.0318,0.0,0,0,0.0,0.0,2.0
2157,segment_3,at_risk,0.0636,30.99,1,7,30.99,1.0,10.0
2158,segment_0,dormant,0.0188,0.0,0,21,0.0,0.0,7.0
2160,segment_0,dormant,0.0194,0.0,0,24,0.0,0.0,4.0
2161,segment_1,dormant,0.0267,0.0,0,12,0.0,0.0,4.0
2162,segment_1,at_risk,0.0653,0.0,0,0,0.0,0.0,11.0
2163,segment_0,dormant,0.0178,0.0,0,25,0.0,0.0,3.0
2164,segment_1,at_risk,0.025,0.0,0,0,0.0,0.0,4.0
2165,segment_1,dormant,0.0365,0.0,0,5,0.0,0.0,11.0
2168,segment_0,dormant,0.0216,0.0,0,19,0.0,0.0,11.0
2169,segment_1,at_risk,0.231,0.0,0,0,0.0,0.0,6.0
2170,segment_1,dormant,0.0625,0.0,0,2,0.0,0.0,5.0
2171,segment_3,at_risk,0.076,181.99,1,10,181.99,1.0,11.0
2172,segment_1,at_risk,0.0454,0.0,0,0,0.0,0.0,6.0
2173,segment_1,dormant,0.0317,0.0,0,2,0.0,0.0,7.0
2175,segment_3,at_risk,0.0545,68.98,1,14,68.98,0.3333,11.0
2176,segment_1,dormant,0.0519,0.0,0,3,0.0,0.0,12.0
2177,segment_1,at_risk,0.0753,0.0,0,0,0.0,0.0,6.0
2179,segment_1,dormant,0.0309,0.0,0,12,0.0,0.0,2.0
2180,segment_0,dormant,0.0207,0.0,0,21,0.0,0.0,8.0
2182,segment_1,dormant,0.0501,0.0,0,7,0.0,0.0,8.0
2183,segment_1,at_risk,0.1058,0.0,0,0,0.0,0.0,3.0
2184,segment_0,dormant,0.0407,0.0,0,14,0.0,0.0,7.0
2185,segment_0,dormant,0.0508,0.0,0,14,0.0,0.0,6.0
2186,segment_0,dormant,0.0204,0.0,0,22,0.0,0.0,10.0
2188,segment_1,dormant,0.0354,0.0,0,9,0.0,0.0,2.0
2189,segment_0,dormant,0.0205,0.0,0,21,0.0,0.0,1.0
2190,segment_1,at_risk,0.0462,0.0,0,0,0.0,0.0,9.0
2192,segment_1,at_risk,0.0354,0.0,0,0,0.0,0.0,3.0
2193,segment_0,dormant,0.0189,0.0,0,23,0.0,0.0,4.0
2194,segment_1,at_risk,0.0216,0.0,0,0,0.0,0.0,1.0
2195,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,4.0
2196,segment_0,dormant,0.0268,0.0,0,21,0.0,0.0,11.0
2198,segment_3,at_risk,0.0652,89.99,1,27,89.99,0.1667,12.0
2199,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,2.0
2200,segment_1,dormant,0.045,0.0,0,2,0.0,0.0,7.0
2201,segment_1,at_risk,0.031,0.0,0,0,0.0,0.0,8.0
2202,segment_1,at_risk,0.0285,0.0,0,0,0.0,0.0,7.0
2203,segment_1,at_risk,0.0414,0.0,0,1,0.0,0.0,2.0
2204,segment_1,dormant,0.025,0.0,0,4,0.0,0.0,2.0
2205,segment_3,at_risk,0.0842,305.64,1,25,305.64,0.1429,4.0
2206,segment_0,dormant,0.0213,0.0,0,20,0.0,0.0,9.0
2208,segment_1,dormant,0.0689,0.0,0,8,0.0,0.0,5.0
2209,segment_1,dormant,0.1033,0.0,0,7,0.0,0.0,4.0
2210,segment_1,dormant,0.0662,0.0,0,7,0.0,0.0,10.0
2211,segment_1,at_risk,0.042,0.0,0,1,0.0,0.0,7.0
2212,segment_0,dormant,0.0208,0.0,0,20,0.0,0.0,1.0
2213,segment_3,at_risk,0.1528,171.98,1,12,171.98,0.1,4.0
2214,segment_3,at_risk,0.0593,8.49,1,7,8.49,1.0,11.0
2215,segment_1,dormant,0.0178,0.0,0,5,0.0,0.0,7.0
2216,segment_3,champions,0.4202,486.42,5,4,97.28,0.2,2.0
2217,segment_1,dormant,0.052,0.0,0,7,0.0,0.0,2.0
2218,segment_0,dormant,0.0355,0.0,0,16,0.0,0.0,4.0
2220,segment_1,dormant,0.0464,0.0,0,8,0.0,0.0,9.0
2221,segment_0,dormant,0.0242,0.0,0,16,0.0,0.0,3.0
2223,segment_1,dormant,0.0845,0.0,0,4,0.0,0.0,6.0
2224,segment_3,loyal,0.0621,70.48,2,6,35.24,0.2222,9.0
2225,segment_1,dormant,0.028,0.0,0,10,0.0,0.0,8.0
2226,segment_0,dormant,0.0167,0.0,0,26,0.0,0.0,9.0
2227,segment_1,dormant,0.0194,0.0,0,4,0.0,0.0,12.0
2228,segment_0,dormant,0.0238,0.0,0,16,0.0,0.0,9.0
2229,segment_0,dormant,0.0166,0.0,0,28,0.0,0.0,10.0
2230,segment_1,dormant,0.0364,0.0,0,10,0.0,0.0,4.0
2231,segment_0,dormant,0.0255,0.0,0,20,0.0,0.0,10.0
2232,segment_0,at_risk,0.0612,19.99,1,17,19.99,0.1,10.0
2233,segment_1,dormant,0.0191,0.0,0,5,0.0,0.0,3.0
2234,segment_0,dormant,0.0173,0.0,0,26,0.0,0.0,8.0
2235,segment_1,at_risk,0.114,0.0,0,1,0.0,0.0,10.0
2237,segment_1,at_risk,0.1173,0.0,0,1,0.0,0.0,8.0
2238,segment_1,dormant,0.0354,0.0,0,6,0.0,0.0,12.0
2239,segment_1,at_risk,0.0465,0.0,0,0,0.0,0.0,8.0
2240,segment_1,dormant,0.0313,0.0,0,2,0.0,0.0,1.0
2241,segment_1,dormant,0.0314,0.0,0,4,0.0,0.0,7.0
2243,segment_1,dormant,0.0432,0.0,0,6,0.0,0.0,4.0
2244,segment_0,dormant,0.0158,0.0,0,30,0.0,0.0,7.0
2245,segment_1,at_risk,0.0186,0.0,0,0,0.0,0.0,2.0
2246,segment_0,dormant,0.025,0.0,0,19,0.0,0.0,2.0
2247,segment_1,dormant,0.016,0.0,0,5,0.0,0.0,9.0
2248,segment_0,dormant,0.0256,0.0,0,17,0.0,0.0,6.0
2249,segment_0,dormant,0.0196,0.0,0,22,0.0,0.0,9.0
2250,segment_1,dormant,0.0731,0.0,0,7,0.0,0.0,5.0
2251,segment_1,at_risk,0.1223,0.0,0,1,0.0,0.0,6.0
2252,segment_0,dormant,0.0308,0.0,0,17,0.0,0.0,4.0
2253,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,8.0
2254,segment_3,loyal,0.1655,168.98,2,5,84.49,0.1538,2.0
2255,segment_0,at_risk,0.0872,76.99,1,28,76.99,0.1111,2.0
2257,segment_1,dormant,0.0272,0.0,0,11,0.0,0.0,8.0
2258,segment_0,dormant,0.0269,0.0,0,17,0.0,0.0,8.0
2259,segment_1,dormant,0.0303,0.0,0,8,0.0,0.0,6.0
2260,segment_0,dormant,0.0508,13.99,1,29,13.99,0.1,2.0
2261,segment_0,dormant,0.0256,0.0,0,14,0.0,0.0,2.0
2262,segment_1,at_risk,0.0493,0.0,0,1,0.0,0.0,4.0
2263,segment_1,dormant,0.031,0.0,0,5,0.0,0.0,1.0
2264,segment_1,dormant,0.0267,0.0,0,12,0.0,0.0,11.0
2265,segment_3,loyal,0.1566,147.46,2,20,73.73,0.1538,3.0
2266,segment_3,at_risk,0.0622,116.99,1,16,116.99,0.25,6.0
2269,segment_1,at_risk,0.0228,0.0,0,1,0.0,0.0,10.0
2270,segment_0,dormant,0.023,0.0,0,17,0.0,0.0,9.0
2271,segment_1,dormant,0.032,0.0,0,2,0.0,0.0,12.0
2272,segment_1,dormant,0.0505,0.0,0,6,0.0,0.0,7.0
2273,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,2.0
2274,segment_1,dormant,0.0467,0.0,0,3,0.0,0.0,1.0
2277,segment_1,at_risk,0.0484,0.0,0,0,0.0,0.0,3.0
2278,segment_0,dormant,0.0244,0.0,0,16,0.0,0.0,6.0
2279,segment_1,at_risk,0.0673,0.0,0,0,0.0,0.0,4.0
2280,segment_0,dormant,0.0302,0.0,0,15,0.0,0.0,3.0
2282,segment_0,dormant,0.0274,0.0,0,17,0.0,0.0,3.0
2283,segment_1,dormant,0.0336,0.0,0,11,0.0,0.0,5.0
2285,segment_1,at_risk,0.0688,0.0,0,1,0.0,0.0,8.0
2286,segment_3,at_risk,0.0772,25.48,2,19,12.74,0.2857,1.0
2287,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,4.0
2288,segment_1,dormant,0.0204,0.0,0,5,0.0,0.0,7.0
2289,segment_0,dormant,0.0515,0.0,0,13,0.0,0.0,1.0
2290,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,10.0
2292,segment_1,at_risk,0.0516,0.0,0,0,0.0,0.0,5.0
2293,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,10.0
2295,segment_0,dormant,0.0329,0.0,0,15,0.0,0.0,5.0
2296,segment_0,dormant,0.0206,0.0,0,22,0.0,0.0,8.0
2297,segment_3,loyal,0.109,265.99,1,7,265.99,0.2,12.0
2298,segment_3,loyal,0.0329,28.99,1,4,28.99,0.25,7.0
2299,segment_0,at_risk,0.1627,46.99,1,27,46.99,0.05,2.0
2300,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,6.0
2301,segment_1,at_risk,0.0216,0.0,0,0,0.0,0.0,10.0
2302,segment_1,dormant,0.022,0.0,0,5,0.0,0.0,4.0
2303,segment_0,dormant,0.0205,0.0,0,20,0.0,0.0,1.0
2304,segment_1,at_risk,0.0605,0.0,0,0,0.0,0.0,11.0
2306,segment_0,dormant,0.0206,0.0,0,22,0.0,0.0,5.0
2307,segment_0,at_risk,0.1273,17.99,1,15,17.99,0.0588,2.0
2308,segment_1,dormant,0.0289,0.0,0,10,0.0,0.0,3.0
2309,segment_3,at_risk,0.0254,14.99,1,5,14.99,0.5,3.0
2310,segment_0,dormant,0.0332,0.0,0,13,0.0,0.0,12.0
2311,segment_3,at_risk,0.0251,23.99,1,5,23.99,0.5,5.0
2313,segment_3,champions,0.1795,469.85,3,7,156.62,0.1667,11.0
2314,segment_1,dormant,0.0243,0.0,0,6,0.0,0.0,6.0
2316,segment_3,loyal,0.0979,241.99,1,6,241.99,0.0625,9.0
2317,segment_1,dormant,0.0494,0.0,0,7,0.0,0.0,8.0
2318,segment_3,champions,0.4589,130.97,3,0,43.66,0.1071,3.0
2319,segment_0,dormant,0.0214,0.0,0,27,0.0,0.0,2.0
2320,segment_1,dormant,0.0867,0.0,0,4,0.0,0.0,6.0
2321,segment_1,dormant,0.0283,0.0,0,12,0.0,0.0,11.0
2322,segment_1,dormant,0.0175,0.0,0,5,0.0,0.0,11.0
2324,segment_3,champions,0.2939,201.03,4,8,50.26,0.2353,4.0
2325,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,9.0
2327,segment_1,dormant,0.0429,0.0,0,8,0.0,0.0,3.0
2328,segment_3,loyal,0.1911,235.99,1,7,235.99,0.0769,2.0
2329,segment_1,at_risk,0.0773,0.0,0,0,0.0,0.0,9.0
2330,segment_1,dormant,0.0428,0.0,0,9,0.0,0.0,4.0
2331,segment_1,at_risk,0.233,0.0,0,1,0.0,0.0,12.0
2333,segment_1,dormant,0.0185,0.0,0,4,0.0,0.0,2.0
2334,segment_1,at_risk,0.0391,0.0,0,1,0.0,0.0,10.0
2335,segment_1,dormant,0.0269,0.0,0,2,0.0,0.0,12.0
2336,segment_1,at_risk,0.0325,0.0,0,0,0.0,0.0,2.0
2338,segment_1,dormant,0.0538,0.0,0,6,0.0,0.0,3.0
2339,segment_3,at_risk,0.0579,8.49,1,13,8.49,0.25,11.0
2341,segment_1,at_risk,0.0386,0.0,0,0,0.0,0.0,8.0
2342,segment_1,dormant,0.0241,0.0,0,5,0.0,0.0,1.0
2343,segment_1,at_risk,0.0512,0.0,0,0,0.0,0.0,10.0
2344,segment_0,dormant,0.0196,0.0,0,21,0.0,0.0,9.0
2345,segment_1,at_risk,0.0441,0.0,0,0,0.0,0.0,1.0
2346,segment_0,dormant,0.0235,0.0,0,16,0.0,0.0,2.0
2347,segment_1,dormant,0.0452,0.0,0,7,0.0,0.0,5.0
2348,segment_1,dormant,0.0392,0.0,0,9,0.0,0.0,2.0
2349,segment_1,at_risk,0.0194,0.0,0,1,0.0,0.0,1.0
2350,segment_0,dormant,0.0222,0.0,0,22,0.0,0.0,7.0
2351,segment_1,dormant,0.1272,0.0,0,5,0.0,0.0,9.0
2352,segment_1,dormant,0.1082,0.0,0,2,0.0,0.0,2.0
2353,segment_1,dormant,0.0464,0.0,0,2,0.0,0.0,11.0
2354,segment_1,dormant,0.0391,0.0,0,12,0.0,0.0,6.0
2355,segment_1,dormant,0.0338,0.0,0,2,0.0,0.0,8.0
2356,segment_1,dormant,0.0377,0.0,0,3,0.0,0.0,6.0
2357,segment_1,dormant,0.0296,0.0,0,8,0.0,0.0,7.0
2358,segment_0,dormant,0.03,0.0,0,14,0.0,0.0,8.0
2360,segment_2,champions,0.62,813.14,2,8,406.57,0.0588,5.0
2362,segment_1,dormant,0.0194,0.0,0,2,0.0,0.0,2.0
2363,segment_0,dormant,0.0196,0.0,0,22,0.0,0.0,1.0
2364,segment_1,at_risk,0.0432,0.0,0,0,0.0,0.0,12.0
2365,segment_0,dormant,0.0425,0.0,0,13,0.0,0.0,10.0
2366,segment_3,at_risk,0.05,34.99,1,19,34.99,0.25,11.0
2367,segment_0,dormant,0.0172,0.0,0,28,0.0,0.0,4.0
2368,segment_0,at_risk,0.1243,43.48,1,14,43.48,0.0667,2.0
2369,segment_1,dormant,0.1143,0.0,0,2,0.0,0.0,9.0
2370,segment_0,dormant,0.0192,0.0,0,23,0.0,0.0,11.0
2372,segment_1,dormant,0.0248,0.0,0,3,0.0,0.0,4.0
2373,segment_1,dormant,0.0401,0.0,0,7,0.0,0.0,8.0
2375,segment_3,champions,0.487,223.97,3,4,74.66,0.1,7.0
2376,segment_1,loyal,0.0547,57.99,1,2,57.99,0.125,10.0
2377,segment_1,at_risk,0.0527,0.0,0,1,0.0,0.0,4.0
2378,segment_3,at_risk,0.0675,158.99,1,19,158.99,0.1111,5.0
2379,segment_1,dormant,0.0327,0.0,0,4,0.0,0.0,7.0
2380,segment_1,at_risk,0.0187,0.0,0,1,0.0,0.0,5.0
2381,segment_3,at_risk,0.0903,89.99,1,15,89.99,0.1667,10.0
2382,segment_3,champions,0.1982,137.96,4,4,34.49,0.2353,5.0
2383,segment_1,dormant,0.046,0.0,0,3,0.0,0.0,2.0
2384,segment_0,dormant,0.0181,0.0,0,26,0.0,0.0,9.0
2385,segment_1,at_risk,0.079,0.0,0,1,0.0,0.0,11.0
2386,segment_3,at_risk,0.0786,50.98,2,19,25.49,0.3333,3.0
2387,segment_3,loyal,0.0608,85.99,1,5,85.99,0.125,10.0
2388,segment_1,dormant,0.0325,0.0,0,11,0.0,0.0,2.0
2389,segment_0,dormant,0.0249,0.0,0,20,0.0,0.0,2.0
2390,segment_0,dormant,0.0249,0.0,0,16,0.0,0.0,7.0
2391,segment_1,dormant,0.045,0.0,0,10,0.0,0.0,2.0
2392,segment_3,at_risk,0.0781,131.26,1,25,131.26,0.125,10.0
2393,segment_1,dormant,0.0187,0.0,0,3,0.0,0.0,9.0
2394,segment_1,dormant,0.0314,0.0,0,4,0.0,0.0,2.0
2395,segment_1,dormant,0.0166,0.0,0,6,0.0,0.0,12.0
2396,segment_1,at_risk,0.0336,0.0,0,1,0.0,0.0,8.0
2397,segment_1,dormant,0.041,0.0,0,3,0.0,0.0,3.0
2398,segment_0,dormant,0.0286,0.0,0,16,0.0,0.0,4.0
2399,segment_0,dormant,0.0348,0.0,0,14,0.0,0.0,12.0
2400,segment_1,at_risk,0.0751,0.0,0,0,0.0,0.0,8.0
2401,segment_3,loyal,0.147,204.99,1,14,204.99,0.1111,12.0
2402,segment_1,dormant,0.0217,0.0,0,6,0.0,0.0,4.0
2403,segment_1,at_risk,0.0673,0.0,0,0,0.0,0.0,3.0
2404,segment_1,dormant,0.0303,0.0,0,8,0.0,0.0,1.0
2405,segment_1,dormant,0.0473,0.0,0,6,0.0,0.0,12.0
2406,segment_1,at_risk,0.0803,0.0,0,1,0.0,0.0,12.0
2407,segment_0,dormant,0.0169,0.0,0,29,0.0,0.0,3.0
2408,segment_1,dormant,0.0288,0.0,0,9,0.0,0.0,3.0
2410,segment_0,dormant,0.0342,0.0,0,16,0.0,0.0,7.0
2411,segment_1,dormant,0.0324,0.0,0,11,0.0,0.0,2.0
2412,segment_0,at_risk,0.0542,60.99,1,23,60.99,0.1667,10.0
2413,segment_1,at_risk,0.0651,0.0,0,0,0.0,0.0,10.0
2415,segment_0,dormant,0.0143,0.0,0,28,0.0,0.0,1.0
2416,segment_1,dormant,0.025,0.0,0,5,0.0,0.0,10.0
2418,segment_3,at_risk,0.0442,92.99,1,28,92.99,0.25,10.0
2419,segment_1,at_risk,0.3509,0.0,0,0,0.0,0.0,12.0
2421,segment_1,dormant,0.0278,0.0,0,10,0.0,0.0,10.0
2423,segment_3,champions,0.2822,160.97,3,4,53.66,0.1765,11.0
2424,segment_0,dormant,0.0246,0.0,0,13,0.0,0.0,3.0
2425,segment_1,at_risk,0.0272,0.0,0,1,0.0,0.0,7.0
2426,segment_1,dormant,0.0879,0.0,0,5,0.0,0.0,2.0
2427,segment_1,at_risk,0.0492,23.99,1,4,23.99,0.1667,7.0
2428,segment_1,dormant,0.0385,0.0,0,6,0.0,0.0,2.0
2429,segment_0,dormant,0.0235,0.0,0,17,0.0,0.0,9.0
2430,segment_1,dormant,0.0546,0.0,0,4,0.0,0.0,5.0
2431,segment_1,dormant,0.0295,0.0,0,9,0.0,0.0,5.0
2432,segment_1,at_risk,0.0343,0.0,0,0,0.0,0.0,5.0
2433,segment_0,dormant,0.0187,0.0,0,25,0.0,0.0,7.0
2434,segment_1,dormant,0.0471,0.0,0,5,0.0,0.0,4.0
2435,segment_1,dormant,0.0498,0.0,0,4,0.0,0.0,9.0
2436,segment_1,at_risk,0.0313,0.0,0,1,0.0,0.0,9.0
2437,segment_0,dormant,0.024,0.0,0,16,0.0,0.0,9.0
2438,segment_1,dormant,0.066,0.0,0,2,0.0,0.0,8.0
2439,segment_3,at_risk,0.1543,157.37,1,25,157.37,0.0667,2.0
2440,segment_1,dormant,0.0187,0.0,0,3,0.0,0.0,8.0
2441,segment_1,at_risk,0.0392,0.0,0,0,0.0,0.0,6.0
2442,segment_0,dormant,0.0231,0.0,0,16,0.0,0.0,9.0
2443,segment_1,at_risk,0.0334,0.0,0,0,0.0,0.0,3.0
2445,segment_3,loyal,0.1827,76.98,2,8,38.49,0.1333,2.0
2446,segment_3,at_risk,0.0615,46.99,1,11,46.99,1.0,4.0
2447,segment_3,loyal,0.2266,21.01,2,6,10.5,0.0909,6.0
2448,segment_1,dormant,0.0289,0.0,0,10,0.0,0.0,4.0
2449,segment_1,at_risk,0.0323,0.0,0,0,0.0,0.0,11.0
2450,segment_1,dormant,0.0174,0.0,0,2,0.0,0.0,6.0
2451,segment_0,dormant,0.0213,0.0,0,21,0.0,0.0,8.0
2452,segment_1,dormant,0.0336,0.0,0,10,0.0,0.0,2.0
2453,segment_2,champions,0.2087,703.95,4,2,175.99,0.2,2.0
2454,segment_0,dormant,0.0289,0.0,0,15,0.0,0.0,1.0
2456,segment_1,dormant,0.0385,0.0,0,11,0.0,0.0,10.0
2457,segment_1,at_risk,0.0886,0.0,0,0,0.0,0.0,5.0
2458,segment_1,at_risk,0.0267,0.0,0,1,0.0,0.0,7.0
2459,segment_1,dormant,0.0219,0.0,0,5,0.0,0.0,1.0
2460,segment_0,dormant,0.0284,0.0,0,16,0.0,0.0,6.0
2461,segment_1,at_risk,0.4636,13.99,1,9,13.99,0.0417,2.0
2462,segment_1,at_risk,0.0293,0.0,0,1,0.0,0.0,5.0
2463,segment_1,dormant,0.0924,0.0,0,9,0.0,0.0,9.0
2464,segment_1,dormant,0.0648,0.0,0,5,0.0,0.0,5.0
2465,segment_0,at_risk,0.0559,64.99,1,26,64.99,0.1429,12.0
2466,segment_3,champions,0.106,325.93,3,1,108.64,0.25,11.0
2467,segment_0,at_risk,0.3231,8.49,1,13,8.49,0.0588,7.0
2468,segment_1,at_risk,0.0616,0.0,0,0,0.0,0.0,4.0
2469,segment_1,dormant,0.0448,0.0,0,10,0.0,0.0,1.0
2471,segment_1,at_risk,0.0417,0.0,0,0,0.0,0.0,9.0
2472,segment_1,at_risk,0.2377,0.0,0,0,0.0,0.0,3.0
2473,segment_0,dormant,0.0187,0.0,0,25,0.0,0.0,2.0
2474,segment_1,dormant,0.0562,0.0,0,3,0.0,0.0,3.0
2475,segment_0,dormant,0.019,0.0,0,23,0.0,0.0,4.0
2476,segment_1,dormant,0.0371,0.0,0,8,0.0,0.0,1.0
2478,segment_1,dormant,0.091,0.0,0,4,0.0,0.0,10.0
2479,segment_1,dormant,0.0284,0.0,0,5,0.0,0.0,6.0
2480,segment_1,dormant,0.0312,0.0,0,7,0.0,0.0,2.0
2481,segment_0,dormant,0.0228,0.0,0,16,0.0,0.0,4.0
2482,segment_1,dormant,0.0751,0.0,0,2,0.0,0.0,11.0
2483,segment_0,dormant,0.0213,0.0,0,20,0.0,0.0,1.0
2484,segment_1,at_risk,0.1017,0.0,0,0,0.0,0.0,10.0
2485,segment_0,dormant,0.0798,8.49,1,21,8.49,0.1,6.0
2486,segment_1,at_risk,0.0177,0.0,0,1,0.0,0.0,9.0
2487,segment_0,at_risk,0.0564,34.99,1,26,34.99,0.1,1.0
2488,segment_0,dormant,0.0224,0.0,0,19,0.0,0.0,10.0
2489,segment_1,at_risk,0.0397,0.0,0,1,0.0,0.0,8.0
2490,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,9.0
2491,segment_1,dormant,0.0329,0.0,0,11,0.0,0.0,11.0
2492,segment_1,at_risk,0.0227,0.0,0,0,0.0,0.0,4.0
2493,segment_1,dormant,0.0571,0.0,0,3,0.0,0.0,12.0
2494,segment_1,at_risk,0.034,0.0,0,0,0.0,0.0,12.0
2495,segment_1,dormant,0.0352,0.0,0,4,0.0,0.0,2.0
2496,segment_1,at_risk,0.1309,0.0,0,0,0.0,0.0,11.0
2497,segment_1,dormant,0.0269,0.0,0,6,0.0,0.0,3.0
2498,segment_0,dormant,0.0186,0.0,0,19,0.0,0.0,12.0
2500,segment_0,at_risk,0.2256,39.99,1,26,39.99,0.0526,4.0
2502,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,4.0
2503,segment_0,dormant,0.0172,0.0,0,25,0.0,0.0,7.0
2504,segment_1,at_risk,0.0356,0.0,0,1,0.0,0.0,4.0
2505,segment_3,champions,0.1102,255.96,3,2,85.32,0.3333,6.0
2506,segment_1,dormant,0.0721,0.0,0,4,0.0,0.0,4.0
2507,segment_1,dormant,0.0333,0.0,0,8,0.0,0.0,2.0
2508,segment_1,dormant,0.0445,0.0,0,10,0.0,0.0,2.0
2509,segment_0,dormant,0.0273,0.0,0,14,0.0,0.0,3.0
2510,segment_1,dormant,0.0348,0.0,0,3,0.0,0.0,1.0
2511,segment_0,dormant,0.0337,0.0,0,15,0.0,0.0,4.0
2512,segment_1,dormant,0.0922,0.0,0,3,0.0,0.0,6.0
2513,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,2.0
2514,segment_0,dormant,0.0213,0.0,0,27,0.0,0.0,6.0
2515,segment_0,dormant,0.0203,0.0,0,22,0.0,0.0,11.0
2516,segment_1,dormant,0.0293,0.0,0,9,0.0,0.0,8.0
2517,segment_1,dormant,0.0276,0.0,0,6,0.0,0.0,1.0
2519,segment_3,loyal,0.2301,96.98,2,26,48.49,0.1053,5.0
2520,segment_1,dormant,0.0305,0.0,0,3,0.0,0.0,2.0
2521,segment_0,dormant,0.0298,0.0,0,14,0.0,0.0,5.0
2522,segment_0,dormant,0.0221,0.0,0,19,0.0,0.0,8.0
2523,segment_1,dormant,0.0426,0.0,0,5,0.0,0.0,3.0
2524,segment_1,dormant,0.0492,0.0,0,4,0.0,0.0,6.0
2525,segment_3,at_risk,0.1001,85.99,1,13,85.99,0.1111,10.0
2526,segment_1,at_risk,0.0493,0.0,0,0,0.0,0.0,1.0
2528,segment_1,dormant,0.0267,0.0,0,6,0.0,0.0,10.0
2529,segment_1,dormant,0.0548,0.0,0,7,0.0,0.0,4.0
2530,segment_0,dormant,0.0263,0.0,0,13,0.0,0.0,10.0
2531,segment_1,dormant,0.0392,0.0,0,4,0.0,0.0,5.0
2532,segment_3,at_risk,0.1187,74.97,1,10,74.97,0.1,5.0
2533,segment_0,at_risk,0.1566,9.49,1,12,9.49,0.0714,6.0
2534,segment_3,at_risk,0.0447,205.98,1,29,205.98,0.5,4.0
2536,segment_1,dormant,0.0252,0.0,0,4,0.0,0.0,7.0
2537,segment_1,at_risk,0.0171,0.0,0,0,0.0,0.0,3.0
2539,segment_1,dormant,0.0654,0.0,0,10,0.0,0.0,7.0
2541,segment_1,dormant,0.0469,0.0,0,6,0.0,0.0,4.0
2542,segment_3,at_risk,0.08,89.99,1,10,89.99,0.2,1.0
2543,segment_0,dormant,0.0647,7.76,1,28,7.76,0.1111,6.0
2544,segment_1,dormant,0.0306,0.0,0,6,0.0,0.0,2.0
2545,segment_1,dormant,0.0385,0.0,0,11,0.0,0.0,6.0
2546,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,2.0
2547,segment_1,at_risk,0.1984,0.0,0,1,0.0,0.0,6.0
2548,segment_1,at_risk,0.067,37.99,1,8,37.99,0.1429,8.0
2549,segment_3,loyal,0.0532,89.99,1,4,89.99,0.1,9.0
2551,segment_0,dormant,0.0226,0.0,0,17,0.0,0.0,9.0
2553,segment_1,at_risk,0.0322,0.0,0,1,0.0,0.0,4.0
2554,segment_0,dormant,0.0539,15.99,1,24,15.99,0.1429,7.0
2555,segment_1,dormant,0.0395,0.0,0,9,0.0,0.0,1.0
2556,segment_0,at_risk,0.1385,65.99,1,18,65.99,0.0909,2.0
2557,segment_1,dormant,0.0251,0.0,0,3,0.0,0.0,10.0
2558,segment_0,dormant,0.0175,0.0,0,24,0.0,0.0,3.0
2559,segment_1,dormant,0.0876,0.0,0,4,0.0,0.0,6.0
2560,segment_1,dormant,0.0371,0.0,0,7,0.0,0.0,1.0
2561,segment_1,at_risk,0.0491,0.0,0,1,0.0,0.0,5.0
2562,segment_1,dormant,0.051,0.0,0,6,0.0,0.0,7.0
2563,segment_1,dormant,0.0314,0.0,0,7,0.0,0.0,8.0
2565,segment_0,dormant,0.0177,0.0,0,26,0.0,0.0,7.0
2566,segment_0,dormant,0.0237,0.0,0,17,0.0,0.0,1.0
2567,segment_0,dormant,0.0196,0.0,0,22,0.0,0.0,12.0
2568,segment_0,dormant,0.0219,0.0,0,19,0.0,0.0,3.0
2569,segment_1,at_risk,0.0229,0.0,0,0,0.0,0.0,1.0
2570,segment_1,dormant,0.0377,0.0,0,9,0.0,0.0,8.0
2571,segment_3,at_risk,0.0562,34.99,1,8,34.99,0.2,4.0
2572,segment_3,at_risk,0.0587,112.17,1,28,112.17,0.2,9.0
2573,segment_0,dormant,0.0351,0.0,0,17,0.0,0.0,7.0
2574,segment_0,dormant,0.0179,0.0,0,26,0.0,0.0,5.0
2575,segment_0,dormant,0.0227,0.0,0,18,0.0,0.0,5.0
2576,segment_1,at_risk,0.0842,0.0,0,1,0.0,0.0,2.0
2577,segment_3,loyal,0.1248,180.98,2,17,90.49,0.1667,1.0
2578,segment_1,at_risk,0.0407,0.0,0,1,0.0,0.0,5.0
2579,segment_1,dormant,0.0452,0.0,0,2,0.0,0.0,10.0
2580,segment_3,champions,0.1291,152.96,3,0,50.99,0.2727,3.0
2581,segment_1,dormant,0.0407,0.0,0,3,0.0,0.0,10.0
2582,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,5.0
2583,segment_1,at_risk,0.0292,0.0,0,0,0.0,0.0,1.0
2586,segment_1,dormant,0.0315,0.0,0,8,0.0,0.0,5.0
2587,segment_1,dormant,0.1487,0.0,0,5,0.0,0.0,4.0
2588,segment_0,dormant,0.0366,0.0,0,18,0.0,0.0,9.0
2589,segment_1,dormant,0.0687,0.0,0,3,0.0,0.0,12.0
2590,segment_1,dormant,0.0282,0.0,0,10,0.0,0.0,5.0
2592,segment_0,dormant,0.0171,0.0,0,28,0.0,0.0,2.0
2593,segment_1,at_risk,0.049,0.0,0,0,0.0,0.0,4.0
2595,segment_1,dormant,0.0425,0.0,0,3,0.0,0.0,10.0
2596,segment_1,dormant,0.0833,0.0,0,2,0.0,0.0,9.0
2597,segment_0,dormant,0.0321,0.0,0,18,0.0,0.0,5.0
2598,segment_1,dormant,0.031,0.0,0,7,0.0,0.0,9.0
2600,segment_1,dormant,0.0501,0.0,0,2,0.0,0.0,6.0
2601,segment_1,dormant,0.0285,0.0,0,10,0.0,0.0,4.0
2602,segment_3,at_risk,0.0505,84.99,1,23,84.99,0.1667,5.0
2603,segment_0,dormant,0.07,23.99,1,27,23.99,0.0667,5.0
2604,segment_0,dormant,0.0284,0.0,0,14,0.0,0.0,4.0
2605,segment_1,dormant,0.0325,0.0,0,2,0.0,0.0,2.0
2606,segment_1,dormant,0.0333,0.0,0,8,0.0,0.0,12.0
2607,segment_0,dormant,0.016,0.0,0,30,0.0,0.0,7.0
2608,segment_1,dormant,0.0256,0.0,0,6,0.0,0.0,7.0
2609,segment_0,dormant,0.0248,0.0,0,14,0.0,0.0,4.0
2610,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,8.0
2611,segment_0,dormant,0.0151,0.0,0,29,0.0,0.0,1.0
2612,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,2.0
2613,segment_1,dormant,0.0373,0.0,0,5,0.0,0.0,2.0
2614,segment_0,dormant,0.1667,15.52,1,27,15.52,0.0526,5.0
2615,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,3.0
2616,segment_1,at_risk,0.0163,0.0,0,0,0.0,0.0,3.0
2617,segment_1,at_risk,0.0423,0.0,0,0,0.0,0.0,6.0
2618,segment_0,dormant,0.0161,0.0,0,30,0.0,0.0,1.0
2619,segment_1,at_risk,0.0399,0.0,0,1,0.0,0.0,7.0
2620,segment_0,dormant,0.0808,18.98,1,28,18.98,0.0588,10.0
2621,segment_0,dormant,0.0185,0.0,0,25,0.0,0.0,9.0
2622,segment_1,dormant,0.0545,0.0,0,8,0.0,0.0,11.0
2623,segment_1,dormant,0.0484,0.0,0,6,0.0,0.0,9.0
2624,segment_1,dormant,0.0331,0.0,0,11,0.0,0.0,3.0
2625,segment_0,dormant,0.0315,0.0,0,17,0.0,0.0,6.0
2626,segment_0,dormant,0.0421,0.0,0,19,0.0,0.0,11.0
2627,segment_0,dormant,0.0172,0.0,0,27,0.0,0.0,5.0
2628,segment_1,dormant,0.0295,0.0,0,9,0.0,0.0,2.0
2629,segment_1,at_risk,0.0371,0.0,0,0,0.0,0.0,2.0
2630,segment_3,at_risk,0.2315,314.98,1,28,314.98,0.05,1.0
2631,segment_1,dormant,0.0522,0.0,0,5,0.0,0.0,1.0
2632,segment_1,dormant,0.0205,0.0,0,6,0.0,0.0,2.0
2633,segment_2,loyal,0.0435,1085.96,2,22,542.98,0.3333,12.0
2634,segment_1,dormant,0.0715,0.0,0,2,0.0,0.0,4.0
2635,segment_0,dormant,0.0232,0.0,0,17,0.0,0.0,4.0
2636,segment_2,at_risk,0.0953,440.99,1,27,440.99,0.1429,9.0
2637,segment_0,dormant,0.0442,23.99,1,28,23.99,0.1429,8.0
2638,segment_1,loyal,0.0591,36.99,1,1,36.99,0.1429,4.0
2639,segment_1,at_risk,0.0357,0.0,0,0,0.0,0.0,4.0
2640,segment_1,dormant,0.0681,0.0,0,7,0.0,0.0,5.0
2641,segment_0,dormant,0.0224,0.0,0,20,0.0,0.0,4.0
2642,segment_1,dormant,0.0358,0.0,0,11,0.0,0.0,2.0
2643,segment_1,at_risk,0.0344,0.0,0,1,0.0,0.0,4.0
2644,segment_0,dormant,0.0245,0.0,0,15,0.0,0.0,11.0
2645,segment_1,dormant,0.0428,0.0,0,2,0.0,0.0,6.0
2646,segment_1,dormant,0.0288,0.0,0,3,0.0,0.0,2.0
2647,segment_0,dormant,0.0222,0.0,0,19,0.0,0.0,2.0
2649,segment_1,dormant,0.0479,0.0,0,5,0.0,0.0,2.0
2650,segment_1,dormant,0.0319,0.0,0,8,0.0,0.0,10.0
2651,segment_1,dormant,0.028,0.0,0,9,0.0,0.0,9.0
2652,segment_1,dormant,0.0433,0.0,0,2,0.0,0.0,11.0
2653,segment_1,at_risk,0.0221,0.0,0,1,0.0,0.0,10.0
2654,segment_3,loyal,0.0294,142.99,1,3,142.99,0.2,6.0
2655,segment_0,dormant,0.0168,0.0,0,28,0.0,0.0,9.0
2656,segment_1,dormant,0.0399,0.0,0,9,0.0,0.0,5.0
2657,segment_0,dormant,0.02,0.0,0,23,0.0,0.0,12.0
2658,segment_1,dormant,0.0223,0.0,0,6,0.0,0.0,2.0
2660,segment_0,dormant,0.0837,11.99,1,27,11.99,0.1,10.0
2661,segment_1,at_risk,0.0379,0.0,0,1,0.0,0.0,5.0
2663,segment_1,dormant,0.0301,0.0,0,2,0.0,0.0,7.0
2664,segment_0,dormant,0.0284,0.0,0,16,0.0,0.0,5.0
2665,segment_0,dormant,0.0199,0.0,0,28,0.0,0.0,10.0
2667,segment_0,dormant,0.0627,0.0,0,17,0.0,0.0,9.0
2669,segment_1,at_risk,0.0428,0.0,0,0,0.0,0.0,9.0
2670,segment_1,dormant,0.0276,0.0,0,10,0.0,0.0,9.0
2671,segment_0,dormant,0.0183,0.0,0,25,0.0,0.0,11.0
2672,segment_1,dormant,0.0372,0.0,0,10,0.0,0.0,8.0
2673,segment_3,loyal,0.3758,227.95,1,10,227.95,0.0526,6.0
2674,segment_0,dormant,0.0268,0.0,0,15,0.0,0.0,5.0
2675,segment_1,dormant,0.0629,0.0,0,6,0.0,0.0,9.0
2676,segment_3,champions,0.5367,235.46,3,5,78.49,0.1111,2.0
2677,segment_1,dormant,0.021,0.0,0,2,0.0,0.0,3.0
2678,segment_0,dormant,0.0208,0.0,0,20,0.0,0.0,1.0
2679,segment_1,at_risk,0.0497,0.0,0,0,0.0,0.0,11.0
2680,segment_1,dormant,0.0571,0.0,0,4,0.0,0.0,8.0
2682,segment_1,dormant,0.0501,0.0,0,8,0.0,0.0,7.0
2683,segment_3,at_risk,0.1125,142.99,1,22,142.99,0.0833,4.0
2684,segment_0,dormant,0.0232,0.0,0,17,0.0,0.0,6.0
2685,segment_1,at_risk,0.0198,0.0,0,1,0.0,0.0,5.0
2686,segment_1,dormant,0.0273,0.0,0,12,0.0,0.0,6.0
2687,segment_0,dormant,0.0243,0.0,0,15,0.0,0.0,2.0
2688,segment_1,dormant,0.057,0.0,0,10,0.0,0.0,5.0
2689,segment_1,dormant,0.0358,0.0,0,6,0.0,0.0,7.0
2690,segment_2,at_risk,0.1484,540.98,1,22,540.98,0.1111,10.0
2691,segment_1,dormant,0.0311,0.0,0,2,0.0,0.0,1.0
2692,segment_1,at_risk,0.0676,0.0,0,1,0.0,0.0,3.0
2693,segment_1,loyal,0.0522,25.47,1,1,25.47,0.1429,3.0
2694,segment_1,at_risk,0.0257,0.0,0,0,0.0,0.0,12.0
2696,segment_0,dormant,0.0221,0.0,0,16,0.0,0.0,5.0
2697,segment_1,dormant,0.0226,0.0,0,5,0.0,0.0,9.0
2698,segment_1,at_risk,0.0148,0.0,0,1,0.0,0.0,7.0
2699,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,10.0
2700,segment_3,dormant,0.0359,8.92,1,26,8.92,1.0,8.0
2701,segment_1,at_risk,0.0238,0.0,0,0,0.0,0.0,10.0
2702,segment_1,dormant,0.032,0.0,0,12,0.0,0.0,9.0
2703,segment_0,dormant,0.0192,0.0,0,23,0.0,0.0,5.0
2704,segment_0,dormant,0.0162,0.0,0,29,0.0,0.0,12.0
2706,segment_1,dormant,0.0586,0.0,0,4,0.0,0.0,6.0
2707,segment_1,at_risk,0.0626,0.0,0,1,0.0,0.0,8.0
2708,segment_0,dormant,0.1016,9.49,1,26,9.49,0.1,4.0
2709,segment_0,dormant,0.0229,0.0,0,18,0.0,0.0,7.0
2710,segment_1,at_risk,0.0229,0.0,0,1,0.0,0.0,1.0
2711,segment_1,at_risk,0.0571,0.0,0,1,0.0,0.0,4.0
2713,segment_1,at_risk,0.0946,0.0,0,1,0.0,0.0,7.0
2714,segment_0,dormant,0.0297,0.0,0,15,0.0,0.0,6.0
2715,segment_0,dormant,0.0178,0.0,0,25,0.0,0.0,6.0
2716,segment_1,at_risk,0.0263,0.0,0,0,0.0,0.0,1.0
2717,segment_0,dormant,0.0257,0.0,0,14,0.0,0.0,7.0
2718,segment_1,at_risk,0.0353,0.0,0,0,0.0,0.0,11.0
2719,segment_1,dormant,0.0333,0.0,0,4,0.0,0.0,10.0
2720,segment_0,dormant,0.0186,0.0,0,25,0.0,0.0,1.0
2721,segment_0,dormant,0.0282,0.0,0,14,0.0,0.0,2.0
2723,segment_1,at_risk,0.0377,0.0,0,1,0.0,0.0,11.0
2725,segment_0,dormant,0.0171,0.0,0,27,0.0,0.0,1.0
2726,segment_0,dormant,0.1206,11.99,1,19,11.99,0.0833,2.0
2727,segment_1,dormant,0.0402,0.0,0,5,0.0,0.0,3.0
2728,segment_0,dormant,0.0206,0.0,0,22,0.0,0.0,2.0
2729,segment_1,dormant,0.042,0.0,0,7,0.0,0.0,1.0
2730,segment_0,dormant,0.0195,0.0,0,23,0.0,0.0,5.0
2731,segment_0,dormant,0.0309,0.0,0,16,0.0,0.0,2.0
2732,segment_1,at_risk,0.0212,0.0,0,1,0.0,0.0,9.0
2733,segment_1,at_risk,0.0159,0.0,0,0,0.0,0.0,5.0
2734,segment_3,at_risk,0.0752,47.98,1,14,47.98,0.2,2.0
2735,segment_1,at_risk,0.0388,0.0,0,1,0.0,0.0,7.0
2736,segment_3,champions,0.0786,465.97,2,0,232.98,0.2857,4.0
2737,segment_1,at_risk,0.0554,0.0,0,1,0.0,0.0,5.0
2738,segment_3,loyal,0.0189,142.99,1,6,142.99,0.2,1.0
2739,segment_3,loyal,0.0218,7.49,1,0,7.49,0.3333,12.0
2740,segment_3,champions,0.0819,321.94,4,0,80.48,0.2857,12.0
2742,segment_1,dormant,0.0171,0.0,0,2,0.0,0.0,1.0
2744,segment_1,at_risk,0.0474,0.0,0,0,0.0,0.0,6.0
2745,segment_3,at_risk,0.0479,76.99,1,27,76.99,0.2,1.0
2746,segment_0,dormant,0.218,9.49,1,21,9.49,0.05,2.0
2747,segment_1,dormant,0.0896,0.0,0,4,0.0,0.0,2.0
2748,segment_1,dormant,0.0373,0.0,0,2,0.0,0.0,9.0
2749,segment_1,dormant,0.018,0.0,0,2,0.0,0.0,3.0
2750,segment_0,dormant,0.0202,0.0,0,20,0.0,0.0,4.0
2751,segment_1,at_risk,0.043,0.0,0,1,0.0,0.0,11.0
2753,segment_1,at_risk,0.1845,51.99,1,8,51.99,0.0526,6.0
2754,segment_1,at_risk,0.0229,0.0,0,1,0.0,0.0,10.0
2756,segment_1,dormant,0.0643,0.0,0,2,0.0,0.0,4.0
2758,segment_0,dormant,0.0261,0.0,0,13,0.0,0.0,8.0
2759,segment_0,dormant,0.024,0.0,0,16,0.0,0.0,7.0
2762,segment_1,dormant,0.0535,0.0,0,10,0.0,0.0,6.0
2763,segment_1,dormant,0.1039,0.0,0,5,0.0,0.0,10.0
2765,segment_1,dormant,0.021,0.0,0,6,0.0,0.0,7.0
2766,segment_0,dormant,0.0169,0.0,0,23,0.0,0.0,5.0
2767,segment_1,at_risk,0.0392,0.0,0,1,0.0,0.0,5.0
2768,segment_0,dormant,0.0241,0.0,0,15,0.0,0.0,10.0
2769,segment_0,dormant,0.0199,0.0,0,21,0.0,0.0,10.0
2770,segment_1,dormant,0.0168,0.0,0,4,0.0,0.0,10.0
2771,segment_1,at_risk,0.0234,0.0,0,1,0.0,0.0,3.0
2772,segment_1,at_risk,0.0672,0.0,0,1,0.0,0.0,10.0
2773,segment_3,at_risk,0.0445,63.98,1,20,63.98,0.2,6.0
2774,segment_3,loyal,0.0759,223.98,2,23,111.99,0.2857,11.0
2775,segment_1,dormant,0.0715,0.0,0,4,0.0,0.0,1.0
2776,segment_1,dormant,0.0379,0.0,0,8,0.0,0.0,1.0
2777,segment_0,dormant,0.016,0.0,0,30,0.0,0.0,2.0
2778,segment_1,dormant,0.0301,0.0,0,12,0.0,0.0,5.0
2779,segment_0,dormant,0.0362,0.0,0,14,0.0,0.0,12.0
2780,segment_0,dormant,0.02,0.0,0,23,0.0,0.0,2.0
2781,segment_1,dormant,0.0277,0.0,0,11,0.0,0.0,1.0
2782,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,4.0
2783,segment_1,dormant,0.0238,0.0,0,3,0.0,0.0,8.0
2784,segment_1,at_risk,0.0533,0.0,0,1,0.0,0.0,8.0
2785,segment_1,dormant,0.0587,0.0,0,4,0.0,0.0,6.0
2786,segment_1,at_risk,0.0852,17.99,1,10,17.99,0.1429,7.0
2787,segment_1,at_risk,0.1342,0.0,0,0,0.0,0.0,2.0
2788,segment_1,at_risk,0.0302,0.0,0,0,0.0,0.0,3.0
2790,segment_1,dormant,0.0271,0.0,0,12,0.0,0.0,8.0
2791,segment_1,dormant,0.029,0.0,0,9,0.0,0.0,11.0
2794,segment_1,dormant,0.024,0.0,0,3,0.0,0.0,9.0
2795,segment_1,dormant,0.0538,0.0,0,9,0.0,0.0,8.0
2796,segment_1,dormant,0.0359,0.0,0,3,0.0,0.0,3.0
2797,segment_1,at_risk,0.0987,14.99,1,8,14.99,0.0909,2.0
2799,segment_3,champions,0.6909,315.45,6,0,52.58,0.1714,4.0
2800,segment_0,dormant,0.022,0.0,0,18,0.0,0.0,3.0
2801,segment_3,at_risk,0.0589,62.98,1,11,62.98,0.1667,2.0
2802,segment_1,at_risk,0.02,0.0,0,1,0.0,0.0,1.0
2803,segment_1,at_risk,0.0564,0.0,0,0,0.0,0.0,8.0
2804,segment_1,loyal,0.1161,65.98,1,2,65.98,0.0526,10.0
2806,segment_0,dormant,0.0252,0.0,0,14,0.0,0.0,2.0
2807,segment_1,dormant,0.0289,0.0,0,3,0.0,0.0,7.0
2811,segment_1,dormant,0.029,0.0,0,9,0.0,0.0,9.0
2812,segment_1,dormant,0.0302,0.0,0,11,0.0,0.0,2.0
2813,segment_1,at_risk,0.0333,0.0,0,0,0.0,0.0,5.0
2814,segment_1,dormant,0.0358,0.0,0,8,0.0,0.0,12.0
2816,segment_1,dormant,0.0287,0.0,0,2,0.0,0.0,5.0
2817,segment_1,dormant,0.0398,0.0,0,9,0.0,0.0,8.0
2818,segment_0,dormant,0.0355,0.0,0,13,0.0,0.0,1.0
2819,segment_3,loyal,0.0218,65.98,1,2,65.98,0.25,9.0
2820,segment_1,dormant,0.0264,0.0,0,6,0.0,0.0,8.0
2821,segment_1,dormant,0.0276,0.0,0,4,0.0,0.0,8.0
2822,segment_1,dormant,0.0375,0.0,0,2,0.0,0.0,9.0
2823,segment_1,dormant,0.0296,0.0,0,8,0.0,0.0,2.0
2824,segment_1,dormant,0.0206,0.0,0,5,0.0,0.0,8.0
2826,segment_1,dormant,0.0519,0.0,0,5,0.0,0.0,8.0
2827,segment_0,dormant,0.0285,0.0,0,15,0.0,0.0,12.0
2828,segment_3,at_risk,0.1549,62.39,2,20,31.2,0.1176,2.0
2829,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,5.0
2830,segment_1,dormant,0.0248,0.0,0,5,0.0,0.0,5.0
2831,segment_3,loyal,0.0932,103.99,1,4,103.99,0.1,9.0
2832,segment_1,dormant,0.0348,0.0,0,7,0.0,0.0,1.0
2833,segment_1,at_risk,0.0232,0.0,0,0,0.0,0.0,1.0
2834,segment_1,at_risk,0.0474,0.0,0,1,0.0,0.0,5.0
2836,segment_1,at_risk,0.04,0.0,0,0,0.0,0.0,1.0
2838,segment_1,dormant,0.0281,0.0,0,4,0.0,0.0,2.0
2839,segment_1,dormant,0.0239,0.0,0,6,0.0,0.0,9.0
2840,segment_1,at_risk,0.0237,0.0,0,0,0.0,0.0,7.0
2842,segment_1,dormant,0.0305,0.0,0,7,0.0,0.0,6.0
2843,segment_1,dormant,0.0276,0.0,0,2,0.0,0.0,5.0
2844,segment_1,at_risk,0.1031,0.0,0,1,0.0,0.0,3.0
2845,segment_1,dormant,0.0642,0.0,0,3,0.0,0.0,5.0
2846,segment_3,champions,0.126,177.97,2,3,88.98,0.1429,7.0
2847,segment_1,dormant,0.0397,0.0,0,6,0.0,0.0,12.0
2848,segment_0,dormant,0.0244,0.0,0,16,0.0,0.0,6.0
2849,segment_0,dormant,0.0371,0.0,0,14,0.0,0.0,3.0
2850,segment_1,at_risk,0.0356,0.0,0,1,0.0,0.0,11.0
2852,segment_3,loyal,0.1536,270.15,2,27,135.07,0.1333,11.0
2853,segment_0,dormant,0.0201,0.0,0,24,0.0,0.0,2.0
2854,segment_1,dormant,0.0353,0.0,0,10,0.0,0.0,5.0
2855,segment_0,dormant,0.0174,0.0,0,27,0.0,0.0,1.0
2856,segment_0,dormant,0.0259,0.0,0,13,0.0,0.0,6.0
2857,segment_1,dormant,0.0288,0.0,0,9,0.0,0.0,1.0
2858,segment_1,dormant,0.0171,0.0,0,3,0.0,0.0,7.0
2859,segment_1,dormant,0.0174,0.0,0,4,0.0,0.0,11.0
2860,segment_1,dormant,0.0502,0.0,0,5,0.0,0.0,5.0
2861,segment_0,dormant,0.0223,0.0,0,18,0.0,0.0,5.0
2862,segment_0,dormant,0.0203,0.0,0,22,0.0,0.0,1.0
2863,segment_1,at_risk,0.0195,0.0,0,0,0.0,0.0,8.0
2866,segment_3,at_risk,0.0569,265.99,1,25,265.99,0.5,11.0
2867,segment_0,dormant,0.0234,0.0,0,15,0.0,0.0,2.0
2868,segment_0,dormant,0.0977,23.99,1,23,23.99,0.0625,2.0
2870,segment_3,loyal,0.3209,70.97,2,12,35.48,0.1111,6.0
2871,segment_1,dormant,0.0346,0.0,0,3,0.0,0.0,5.0
2872,segment_0,dormant,0.1405,14.99,1,27,14.99,0.0667,12.0
2873,segment_3,champions,0.0983,280.97,2,5,140.49,0.1538,4.0
2874,segment_1,dormant,0.0249,0.0,0,2,0.0,0.0,9.0
2875,segment_3,champions,0.8202,442.96,3,0,147.65,0.075,2.0
2877,segment_1,dormant,0.0383,0.0,0,9,0.0,0.0,3.0
2878,segment_1,dormant,0.0237,0.0,0,3,0.0,0.0,2.0
2879,segment_1,at_risk,0.1167,14.99,1,5,14.99,0.0588,5.0
2880,segment_1,dormant,0.0279,0.0,0,11,0.0,0.0,3.0
2881,segment_1,at_risk,0.0779,0.0,0,0,0.0,0.0,5.0
2883,segment_1,at_risk,0.038,0.0,0,1,0.0,0.0,8.0
2884,segment_1,dormant,0.0179,0.0,0,5,0.0,0.0,3.0
2885,segment_0,dormant,0.0233,0.0,0,17,0.0,0.0,5.0
2886,segment_1,dormant,0.087,0.0,0,2,0.0,0.0,1.0
2887,segment_3,at_risk,0.0641,34.99,1,8,34.99,1.0,1.0
2888,segment_1,at_risk,0.0169,0.0,0,0,0.0,0.0,6.0
2889,segment_1,dormant,0.0225,0.0,0,5,0.0,0.0,7.0
2890,segment_0,dormant,0.0785,7.76,1,25,7.76,0.0833,11.0
2891,segment_1,dormant,0.0284,0.0,0,2,0.0,0.0,1.0
2892,segment_1,dormant,0.0276,0.0,0,5,0.0,0.0,10.0
2893,segment_1,at_risk,0.0277,0.0,0,0,0.0,0.0,10.0
2894,segment_1,dormant,0.0307,0.0,0,5,0.0,0.0,10.0
2895,segment_0,dormant,0.0431,3.49,1,29,3.49,0.25,8.0
2896,segment_3,champions,0.0763,265.99,1,0,265.99,0.1,1.0
2897,segment_1,dormant,0.039,0.0,0,7,0.0,0.0,5.0
2898,segment_0,dormant,0.0243,0.0,0,15,0.0,0.0,9.0
2899,segment_1,dormant,0.0374,0.0,0,8,0.0,0.0,7.0
2900,segment_3,loyal,0.0971,185.99,1,4,185.99,0.1,10.0
2901,segment_1,dormant,0.1187,0.0,0,9,0.0,0.0,2.0
2902,segment_2,loyal,0.3263,644.95,2,19,322.48,0.0769,7.0
2903,segment_0,dormant,0.0476,17.99,1,26,17.99,0.25,3.0
2905,segment_1,at_risk,0.045,0.0,0,1,0.0,0.0,11.0
2906,segment_1,dormant,0.0363,0.0,0,6,0.0,0.0,12.0
2907,segment_1,at_risk,0.0325,0.0,0,0,0.0,0.0,12.0
2908,segment_1,at_risk,0.1113,0.0,0,0,0.0,0.0,1.0
2909,segment_0,dormant,0.0227,0.0,0,27,0.0,0.0,5.0
2910,segment_3,loyal,0.7489,309.74,3,13,103.25,0.0857,2.0
2911,segment_1,dormant,0.0287,0.0,0,10,0.0,0.0,3.0
2913,segment_3,loyal,0.0467,241.99,1,5,241.99,0.1667,5.0
2914,segment_1,dormant,0.0564,0.0,0,6,0.0,0.0,7.0
2915,segment_0,dormant,0.0249,0.0,0,21,0.0,0.0,1.0
2916,segment_0,dormant,0.0247,0.0,0,15,0.0,0.0,8.0
2917,segment_3,champions,0.1699,384.07,3,2,128.02,0.1875,7.0
2918,segment_1,dormant,0.0282,0.0,0,6,0.0,0.0,7.0
2919,segment_3,champions,0.1161,113.98,2,0,56.99,0.1053,3.0
2920,segment_0,dormant,0.0242,0.0,0,14,0.0,0.0,12.0
2921,segment_0,dormant,0.015,0.0,0,29,0.0,0.0,6.0
2922,segment_0,at_risk,0.2138,56.99,1,30,56.99,0.05,3.0
2923,segment_1,at_risk,0.0563,0.0,0,0,0.0,0.0,2.0
2925,segment_1,dormant,0.1905,0.0,0,4,0.0,0.0,2.0
2926,segment_3,loyal,0.1136,130.99,1,0,130.99,0.0455,2.0
2927,segment_1,at_risk,0.0631,0.0,0,1,0.0,0.0,6.0
2928,segment_1,dormant,0.0634,0.0,0,5,0.0,0.0,12.0
2929,segment_0,dormant,0.0177,0.0,0,27,0.0,0.0,9.0
2930,segment_0,dormant,0.0176,0.0,0,27,0.0,0.0,7.0
2931,segment_0,dormant,0.0178,0.0,0,27,0.0,0.0,6.0
2932,segment_1,at_risk,0.0294,0.0,0,0,0.0,0.0,1.0
2933,segment_3,at_risk,0.0557,263.99,1,24,263.99,1.0,1.0
2934,segment_3,at_risk,0.0945,45.99,1,11,45.99,0.1667,2.0
2935,segment_1,at_risk,0.0478,0.0,0,0,0.0,0.0,9.0
2936,segment_3,at_risk,0.0432,39.99,1,26,39.99,0.3333,3.0
2939,segment_0,dormant,0.1069,25.47,1,19,25.47,0.0714,12.0
2940,segment_1,at_risk,0.0347,0.0,0,0,0.0,0.0,11.0
2941,segment_0,dormant,0.0236,0.0,0,13,0.0,0.0,10.0
2942,segment_1,dormant,0.0477,0.0,0,2,0.0,0.0,10.0
2943,segment_0,at_risk,0.2542,71.99,1,21,71.99,0.05,6.0
2944,segment_1,at_risk,0.0419,0.0,0,1,0.0,0.0,6.0
2945,segment_0,dormant,0.0206,0.0,0,20,0.0,0.0,8.0
2946,segment_0,dormant,0.0172,0.0,0,27,0.0,0.0,2.0
2947,segment_0,dormant,0.0263,0.0,0,18,0.0,0.0,6.0
2948,segment_1,at_risk,0.0447,0.0,0,1,0.0,0.0,2.0
2949,segment_0,dormant,0.0282,0.0,0,14,0.0,0.0,4.0
2950,segment_1,dormant,0.1222,0.0,0,5,0.0,0.0,11.0
2951,segment_1,dormant,0.0297,0.0,0,9,0.0,0.0,4.0
2952,segment_0,dormant,0.0187,0.0,0,24,0.0,0.0,7.0
2953,segment_3,loyal,0.1767,303.95,3,12,101.32,0.2308,5.0
2954,segment_1,dormant,0.0318,0.0,0,6,0.0,0.0,7.0
2955,segment_1,dormant,0.0312,0.0,0,3,0.0,0.0,8.0
2956,segment_1,at_risk,0.0462,0.0,0,1,0.0,0.0,6.0
2957,segment_3,loyal,0.3294,128.98,2,18,64.49,0.0909,7.0
2958,segment_2,champions,0.5074,776.97,2,6,388.48,0.087,3.0
2959,segment_1,at_risk,0.0277,0.0,0,1,0.0,0.0,2.0
2960,segment_1,dormant,0.041,0.0,0,2,0.0,0.0,9.0
2961,segment_0,dormant,0.0253,0.0,0,16,0.0,0.0,9.0
2962,segment_0,dormant,0.0236,0.0,0,15,0.0,0.0,3.0
2963,segment_1,dormant,0.0383,0.0,0,3,0.0,0.0,7.0
2964,segment_1,at_risk,0.065,0.0,0,0,0.0,0.0,5.0
2965,segment_1,dormant,0.0494,0.0,0,6,0.0,0.0,6.0
2966,segment_0,dormant,0.021,0.0,0,20,0.0,0.0,5.0
2967,segment_1,loyal,0.0649,71.99,1,4,71.99,0.1111,3.0
2968,segment_1,at_risk,0.035,0.0,0,0,0.0,0.0,8.0
2969,segment_3,loyal,0.2943,408.98,2,27,204.49,0.087,1.0
2971,segment_1,dormant,0.0416,0.0,0,5,0.0,0.0,7.0
2973,segment_0,dormant,0.0281,0.0,0,17,0.0,0.0,10.0
2974,segment_1,at_risk,0.0806,0.0,0,0,0.0,0.0,5.0
2975,segment_1,dormant,0.0283,0.0,0,9,0.0,0.0,5.0
2976,segment_1,dormant,0.0768,0.0,0,9,0.0,0.0,4.0
2977,segment_0,dormant,0.0304,0.0,0,13,0.0,0.0,12.0
2978,segment_1,at_risk,0.0713,19.47,1,6,19.47,0.0667,8.0
2979,segment_3,champions,0.0775,204.98,2,1,102.49,0.3333,1.0
2980,segment_1,dormant,0.0327,0.0,0,5,0.0,0.0,10.0
2981,segment_0,dormant,0.0227,0.0,0,17,0.0,0.0,2.0
2983,segment_0,dormant,0.0217,0.0,0,18,0.0,0.0,8.0
2984,segment_3,champions,0.0235,127.98,2,2,63.99,0.4,12.0
2985,segment_1,at_risk,0.1294,0.0,0,1,0.0,0.0,2.0
2986,segment_1,dormant,0.029,0.0,0,9,0.0,0.0,5.0
2987,segment_0,dormant,0.0359,0.0,0,14,0.0,0.0,7.0
2988,segment_1,dormant,0.0545,0.0,0,2,0.0,0.0,12.0
2989,segment_1,dormant,0.0446,0.0,0,4,0.0,0.0,8.0
2990,segment_1,dormant,0.0376,0.0,0,6,0.0,0.0,2.0
2992,segment_1,dormant,0.0322,0.0,0,5,0.0,0.0,9.0
2993,segment_0,dormant,0.0214,0.0,0,20,0.0,0.0,5.0
2994,segment_0,dormant,0.023,0.0,0,25,0.0,0.0,10.0
2995,segment_3,loyal,0.5465,556.41,6,13,92.74,0.2609,6.0
2996,segment_1,dormant,0.0316,0.0,0,6,0.0,0.0,11.0
2997,segment_3,at_risk,0.0401,43.99,1,20,43.99,0.5,6.0
2998,segment_1,at_risk,0.0274,0.0,0,0,0.0,0.0,5.0
2999,segment_1,at_risk,0.0455,36.45,1,6,36.45,0.1429,8.0
3000,segment_1,dormant,0.0587,0.0,0,2,0.0,0.0,5.0
```

### data/metadata.json

```
{
  "dataset": "dm_targeting_profiles_v1",
  "description": "Seeded campaign-targeting profile derived from Day 1 events + orders: Day 2 K-Means segment + manual RFM bucket + Day 3 conversion probability + customer value. Seeded campaigns table with rules (target segments, eligible buckets, probability/value thresholds, cost, budget, contact limit).",
  "source": "derived",
  "derived_from": {
    "events": "Day 1/data/events.csv",
    "orders": "Day 1/data/orders.csv",
    "module": "app.data.generate_targeting",
    "function": "generate_targeting",
    "profile_builder": "app.data.generate_targeting.build_targeting_profile",
    "segment_builder": "app.ml.segmentation.train_segmentation_model",
    "conversion_builder": "app.ml.conversion.train_conversion_model",
    "rfm_builder": "app.ml.segmentation.manual_rfm_buckets"
  },
  "seed": {
    "seed": 42,
    "k": 4,
    "window_days": 7,
    "model_type": "logistic_regression",
    "note": "isti seed kao Day 2 (K-Means k=4) i Day 3 (logistic_regression) — reproduktivno"
  },
  "reference_date": "2026-01-31 23:59:38",
  "cutoff_date": "2026-01-24 23:59:38",
  "columns": [
    "user_id",
    "segment",
    "rfm_bucket",
    "probability",
    "monetary",
    "frequency",
    "recency_days",
    "aov",
    "conversion",
    "favorite_category"
  ],
  "counts": {
    "customers": 2579,
    "by_rfm_bucket": {
      "dormant": 1623,
      "at_risk": 716,
      "loyal": 159,
      "champions": 81
    },
    "by_segment": {
      "segment_1": 1468,
      "segment_0": 720,
      "segment_3": 344,
      "segment_2": 47
    },
    "buyers": 571
  },
  "campaigns": 4,
  "fields": {
    "user_id": "int, stabilan ID korisnika (FK -> customers.user_id)",
    "segment": "K-Means labela segmenta (segment_0..3; Day 2, k=4, seed 42)",
    "rfm_bucket": "ručni RFM bucket (champions/loyal/at_risk/dormant; pravilo)",
    "probability": "float 0..1, P(kupovina u prediction window-u) iz Day 3 modela (logistic_regression, seed 42)",
    "monetary": "float, ukupna vrednost porudžbina (istorijska vrednost korisnika)",
    "frequency": "int, broj porudžbina",
    "recency_days": "int, dani od reference do poslednje kupovine (ili aktivnosti)",
    "aov": "float, prosečna vrednost porudžbine (0.0 za ne-kupce)",
    "conversion": "float 0..1, sesije sa kupovinom / sve sesije",
    "favorite_category": "float ili NaN, modus kategorije po product_view"
  },
  "campaign_fields": {
    "campaign_id": "int, stabilan ID kampanje",
    "name": "str, naziv kampanje",
    "description": "str, kratak opis",
    "goal": "str, cilj kampanje",
    "target_segments": "JSON lista ciljanih K-Means segmenta (prazno = svi)",
    "eligible_buckets": "JSON lista dozvoljenih RFM bucket-a (prazno = svi)",
    "min_probability": "float, prag verovatnoće (0 = nije aktivan)",
    "min_monetary": "float, prag istorijske vrednosti (0 = nije aktivan)",
    "cost_per_contact": "float, cena jednog kontakta",
    "expected_revenue": "float, očekivani prihod po konverziji",
    "budget": "float, ukupan budžet kampanje",
    "max_contacts": "int, kontakt limit (kapacitet)",
    "status": "str, active/draft",
    "notes": "str, napomena (koje pravilo se demonstrira)"
  },
  "created": "2026-08-19",
  "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte reproducible, so the sidecar must not change between runs. Regenerate with the same seed to reproduce all files.",
  "manifest": {
    "sha256": {
      "customer_profiles.csv": "75ba700a9b62e2f20aaf1f1c58d68cf4f94eae7f8d82bcbf04583ae46c234b98",
      "campaigns.csv": "6942cae2a347fbf3decb57f5e5d6382726afa86c6b17dbbeca8bfccebd198f27"
    }
  }
}
```

### data/README.md

# Day 4 podaci — targeting profili i kampanje (izvedene tabele)

Determinističke, **byte-for-byte reproduktivne** tabele **izvedene** iz Day 1
seeded događaja i porudžbina (ne dupliraju ih). Kompletna dokumentacija
(izvor, parametri, značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `customer_profiles.csv` | 2579 korisnika (čista istorija): K-Means segment + RFM bucket + verovatnoća kupovine + vrednost + RFM komponente | 2579 |
| `campaigns.csv` | 4 seeded kampanje sa pravilima (ciljani segmenti, bucket-i, pragovi, cene, limita) | 4 |
| `metadata.json` | izvor, cutoff/reference, counts, značenja polja, sha256 | — |

## Kako nastaju (izvedene tabele)

* Ulaz: `Day 1/data/events.csv` + `Day 1/data/orders.csv` (jedini izvor istine).
* Graditelj profila: `app.data.generate_targeting.build_targeting_profile` —
  iste funkcije kao Day 2/3 (isti seed **42**, `k=4`, `logistic_regression`):
  + **Verovatnoća** — clean training dataset (labela iz 7-dnevnog window-a) →
    split → skaliranje (fit na trening) → logistic regression → verovatnoće na
    **čistoj** istoriji (feature-i pre cut-off-a).
  + **Segment** — K-Means (k=4) nad skaliranim feature-ima cele istorije.
  + **RFM bucket** — `manual_rfm_buckets` (pravilo, bez ML-a).
* Generator: `app/data/generate_targeting.py` (upisuje CSV + metadata).
* Kampanje: `app/data/campaigns.py` (jedini izvor definicija kampanja).
* `reference_date = 2026-01-31 23:24:05`, `cutoff_date = 2026-01-24 23:24:05`.

## Ključne kolone (`customer_profiles.csv`)

| Kolona | Značenje |
| --- | --- |
| `user_id` | FK -> `customers.user_id` |
| `segment` | K-Means labela (segment\_0..3; Day 2, k=4, seed 42) |
| `rfm_bucket` | ručni RFM bucket (champions/loyal/at\_risk/dormant; pravilo) |
| `probability` | P(kupovina u window-u) iz Day 3 modela (logistic, seed 42) |
| `monetary` | ukupna vrednost porudžbina (istorijska vrednost korisnika) |
| `frequency` / `recency_days` | broj porudžbina / dani od reference do poslednje kupovine |
| `aov` / `conversion` | prosečna porudžbina / sesije sa kupovinom |
| `favorite_category` | modus kategorije po pregledima (NaN ako ih nema) |

## Stanje u ovom seed-u

* korisnika sa istorijom pre cut-off-a: **2579** (od 3000)
* kupaca (monetary > 0): **571**
* po RFM bucket-u: `dormant` 1623 · `at_risk` 716 · `loyal` 159 · `champions` 81
* po K-Means segmentu: `segment_1` 1468 · `segment_0` 720 · `segment_3` 344 · `segment_2` 47
* prosek verovatnoće po bucket-u: champions **0.290** · loyal **0.168** · at\_risk **0.072** · dormant **0.037**
  (Day 2/3 README imaju modele i metrike).

## Kampanje (`campaigns.csv`)

| ID | Naziv | Ciljani segmenti | Dozvoljeni bucketi | Prag P | Cena | Max kontakti |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | VIP reaktivacija | segment\_2, segment\_3 | champions, loyal | 0.20 | 0.5 | 200 |
| 2 | At-risk win-back | segment\_0 | at\_risk | 0.15 | 0.3 | 300 |
| 3 | Široka visoko-vrednosna | — (svi) | champions, loyal, at\_risk | 0.10 | 0.2 | 500 |
| 4 | Dormant re-engage (pravila) | — (svi) | dormant | 0.00 | 0.1 | 150 |

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_targeting --seed 42
```

Dva pokretanja sa istim seed-om daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

Profil je *ulaz* za targeting, ne rezultat. Visoka prosečna verovatnoća u
champions bucket-u ne znači „pošalji svima" — to je predikcija, a odluka zavisi
od pravila (cena, kapacitet, budžet) i vrednosti korisnika (vidi Day 4 README,
„What the result does NOT prove"). Segmenti i verovatnoće su računati na
sintetičkom seed-u (42); na pravom store-u raspodela je drugačija.

### examples/demo\_targeting.py

```
"""Demo: ML-assisted campaign targeting (Day 4).

Pokretanje (bilo gde):

    python3 "Day 4/examples/demo_targeting.py"

Prikazuje:
  1) targeting profil (segment + verovatnoća + vrednost) iz ``Day 4/data``;
  2) **prediction vs decision** — korisnik sa NAJVEĆOM verovatnoćom NIJE najbolja
     odluka (očekivana vrednost);
  3) rule-based vs ML-assisted poređenje za svaku kampanju (seeded profil,
     deterministički — isti brojevi kao README);
  4) live API putanju: ako su Day 2/3 modeli trenirani -> ML publika; ako nisu ->
     **definisan fallback** (mode=rule, fallback=true, untrained_model).
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.campaigns import load_campaigns
from app.data.paths import course_root
from app.ml.targeting import compare_rule_vs_ml, select_target_customers, rank_target_customers
from app.services.targeting import TargetingService

DAY4_DATA = course_root() / "Day 4" / "data"


def main() -> None:
    print("=== Day 4 — ML-Assisted Campaign Targeting (demo) ===\n")

    profiles = pd.read_csv(DAY4_DATA / "customer_profiles.csv")
    campaigns = {c["campaign_id"]: c for c in load_campaigns()}
    print(f"Profil: {len(profiles)} korisnika sa istorijom pre cut-off-a")
    print(f"  po RFM bucket-u: "
          f"{ {str(k): int(v) for k, v in profiles['rfm_bucket'].value_counts().items()} }")
    print(f"  po K-Means segmentu: "
          f"{ {str(k): int(v) for k, v in profiles['segment'].value_counts().items()} }")
    print()

    # --- 1) Prediction vs decision (kampanja 1: VIP reaktivacija) ---------- #
    c1 = campaigns[1]
    sel1 = select_target_customers(profiles, c1)
    ranked1 = rank_target_customers(sel1, c1, limit=None)
    top_prob = ranked1.loc[ranked1["probability"].idxmax()]
    top_decision = ranked1.iloc[0]
    print("[1] Prediction vs decision (kampanja 1 — VIP reaktivacija):")
    print(f"    najveća VEROVATNOĆA: user {int(top_prob['user_id'])}  "
          f"P={top_prob['probability']:.4f}  vrednost={top_prob['monetary']:.2f}  "
          f"skor={top_prob['score']:.4f}  (rank {int(top_prob['rank'])})")
    print(f"    najbolja ODLUKA:     user {int(top_decision['user_id'])}  "
          f"P={top_decision['probability']:.4f}  vrednost={top_decision['monetary']:.2f}  "
          f"skor={top_decision['score']:.4f}  (rank 1)")
    # Par u top-30 sa najvećom razlikom u P gde je VEROVATNIJI korisnik ipak rangiran NIŽE.
    top = ranked1.head(30).to_dict("records")
    pairs = [(a["probability"] - b["probability"], a, b) for a in top for b in top
             if a["probability"] > b["probability"] and a["score"] < b["score"]]
    if pairs:
        _, a, b = max(pairs, key=lambda x: (x[0], -x[1]["user_id"]))
        cost = c1["cost_per_contact"]
        print(f"    inverzija: user {a['user_id']} (P={a['probability']:.4f}, rank {a['rank']}) vs "
              f"user {b['user_id']} (P={b['probability']:.4f}, rank {b['rank']})")
        print(f"    model kaže {a['probability']:.2f} > {b['probability']:.2f}; odluka kaže "
              f"{a['probability']:.2f}×{a['monetary']:.0f} − {cost} = {a['score']:.1f} < "
              f"{b['probability']:.2f}×{b['monetary']:.0f} − {cost} = {b['score']:.1f}")
    print()

    # --- 2) Rule vs ML poređenje po kampanji (seeded profil, logistic) ----- #
    print("[2] Rule-based vs ML-assisted (seed profil, logistic_regression):")
    print(f"    {'kampanja':<12} {'limita':>6} {'rule_conv':>10} {'ml_conv':>10} "
          f"{'lift':>7} {'overlap':>8} {'jaccard':>8}")
    for cid in sorted(campaigns):
        camp = campaigns[cid]
        cmp = compare_rule_vs_ml(profiles, camp, limit=None)
        m = cmp["metrics"]
        print(f"    {camp['name'][:12]:<12} {cmp['limit']:>6} "
              f"{m['rule']['expected_conversions']:>10.1f} "
              f"{m['ml']['expected_conversions']:>10.1f} "
              f"{str(m['lift_expected_conversions']):>7} {m['overlap']:>8} {m['jaccard']:>8.2f}")
    print()

    # --- 3) Live API putanja: ML publika ili fallback ---------------------- #
    print("[3] Live targeting (servis + modeli u app/models/):")
    svc = TargetingService()
    if svc._ml_available():
        print("    Day 2/3 modeli su trenirani -> ML-assisted publika.")
    else:
        print("    Day 2/3 modeli NISU trenirani -> fallback na rule targeting.")
    for cid in (1, 3):
        res = svc.recommended_audience(cid, limit=5, mode="ml")
        print(f"    kampanja {cid}: mode={res['mode']} fallback={res['fallback']} "
              f"selected={res['selected']} returned={res['returned']}")
        if res["audience"]:
            a = res["audience"][0]
            print(f"      #1 user {a['user_id']}  P={a['probability']}  "
                  f"score={a['score']}  {a['reasons'][-1]}")
    print()

    print("Gotovo. Vizualizacija: python3 \"Day 4/examples/visualize_targeting.py\"")


if __name__ == "__main__":
    main()
```

### examples/visualize\_targeting.py

```
"""Vizualizacija targetinga (Day 4, supporting material).

Dve slike u ``Day 4/examples/``:

    - ``audience_scatter.png`` — za kampanju 1 (VIP): svaki eligibilni korisnik
      kao tačka (P × vrednost), obojena po segmentu; naglašeni top-50 rule
      audience (skor = prioritet bucket-a + vrednost) i top-50 ML audience
      (skor = očekivana vrednost P×vrednost − cena). Anotirani: najveća
      verovatnoća i najbolja odluka (ID-jevi se ispisuju u konzoli) — prediction vs decision.
    - ``comparison_rule_vs_ml.png`` — očekivane konverzije (suma verovatnoća)
      rule vs ML po kampanji, sa lift-om iznad svake grupe.

Ovo je *eksploratorni* materijal — skripta za učenike, ne primarni deliverable
(vidi DAY-BRIEFS House Rules).

Pokretanje:

    python3 "Day 4/examples/visualize_targeting.py"

Zahteva ``matplotlib`` (u ``dm-ml/requirements.txt``).
"""

import sys
from pathlib import Path

# dm-ml na sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import matplotlib

matplotlib.use("Agg")  # bez GUI — čuvamo PNG fajlove
import matplotlib.pyplot as plt
import pandas as pd

from app.data.campaigns import load_campaigns
from app.data.paths import course_root
from app.ml.targeting import (
    compare_rule_vs_ml,
    rank_by_rule,
    rank_target_customers,
    select_target_customers,
)

OUT_DIR = Path(__file__).resolve().parent
DAY4_DATA = course_root() / "Day 4" / "data"

SEGMENT_COLORS = {
    "segment_0": "#94a3b8",
    "segment_1": "#3b82f6",
    "segment_2": "#f59e0b",
    "segment_3": "#10b981",
}


def scatter_audience(profiles: pd.DataFrame, campaign: dict) -> None:
    """Scatter P × vrednost za eligibilne korisnike + top-50 rule/ML publika."""
    sel = select_target_customers(profiles, campaign)
    ranked_ml = rank_target_customers(sel, campaign, limit=50)
    ranked_rule = rank_by_rule(profiles, campaign, limit=50)
    ml_ids = set(ranked_ml["user_id"])
    rule_ids = set(ranked_rule["user_id"])

    fig, ax = plt.subplots(figsize=(8.5, 6))
    for seg, grp in sel.groupby("segment", sort=True):
        ax.scatter(grp["probability"], grp["monetary"], s=14, alpha=0.55,
                   color=SEGMENT_COLORS.get(seg, "#64748b"), label=f"{seg} (n={len(grp)})")

    # Top-50 publike (rule i ML) preko pozadine.
    ax.scatter(ranked_rule["probability"], ranked_rule["monetary"], s=22,
               facecolors="none", edgecolors="#dc2626", linewidths=1.2,
               label=f"rule top-50 (n={len(ranked_rule)})")
    ax.scatter(ranked_ml["probability"], ranked_ml["monetary"], s=22,
               facecolors="none", edgecolors="#000000", linewidths=1.2,
               label=f"ML top-50 (n={len(ranked_ml)})")

    # Prediction vs decision primer.
    top_prob = ranked_ml.loc[ranked_ml["probability"].idxmax()]
    top_dec = ranked_ml.iloc[0]
    print(f"  najveća P: user {int(top_prob['user_id'])} (P={top_prob['probability']:.3f}) · "
          f"najbolja odluka: user {int(top_dec['user_id'])} (P={top_dec['probability']:.3f})")
    ax.annotate(f"najveća P ({int(top_prob['user_id'])})", xy=(top_prob["probability"], top_prob["monetary"]),
                xytext=(top_prob["probability"] - 0.28, top_prob["monetary"] + 250),
                arrowprops=dict(arrowstyle="->", color="#111827"), fontsize=8)
    ax.annotate(f"najbolja odluka ({int(top_dec['user_id'])})", xy=(top_dec["probability"], top_dec["monetary"]),
                xytext=(top_dec["probability"] - 0.30, top_dec["monetary"] - 320),
                arrowprops=dict(arrowstyle="->", color="#111827"), fontsize=8)

    ax.set_xlabel("P(kupovina) — Day 3 model")
    ax.set_ylabel("istorijska vrednost (monetary)")
    ax.set_title(f"Kampanja 1 — VIP reaktivacija: rule vs ML publika (top-50)")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "audience_scatter.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'audience_scatter.png'}")


def comparison_bars(profiles: pd.DataFrame, campaigns: dict) -> None:
    """Gruisane trake: očekivane konverzije rule vs ML po kampanji + lift."""
    names, rule_conv, ml_conv, lifts = [], [], [], []
    for cid in sorted(campaigns):
        camp = campaigns[cid]
        cmp = compare_rule_vs_ml(profiles, camp, limit=None)
        m = cmp["metrics"]
        names.append(camp["name"])
        rule_conv.append(m["rule"]["expected_conversions"])
        ml_conv.append(m["ml"]["expected_conversions"])
        lifts.append(m["lift_expected_conversions"])

    x = range(len(names))
    w = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar([i - w / 2 for i in x], rule_conv, w, label="rule (RFM/vrednost)", color="#94a3b8")
    b2 = ax.bar([i + w / 2 for i in x], ml_conv, w, label="ML (očekivana vrednost)", color="#3b82f6")
    for i, (rc, mc, lift) in enumerate(zip(rule_conv, ml_conv, lifts)):
        ax.text(i - w / 2, rc + 2, f"{rc:.0f}", ha="center", fontsize=8)
        ax.text(i + w / 2, mc + 2, f"{mc:.0f}", ha="center", fontsize=8)
        if lift is not None:
            ax.text(i, max(rc, mc) + 12, f"lift {lift:.2f}", ha="center", fontsize=8, color="#111827")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("očekivane konverzije (suma P)")
    ax.set_title("Rule-based vs ML-assisted targeting — očekivane konverzije")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "comparison_rule_vs_ml.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'comparison_rule_vs_ml.png'}")


def main() -> None:
    print("=== Day 4 — targeting vizualizacija ===")
    profiles = pd.read_csv(DAY4_DATA / "customer_profiles.csv")
    campaigns = {c["campaign_id"]: c for c in load_campaigns()}
    scatter_audience(profiles, campaigns[1])
    comparison_bars(profiles, campaigns)
    print("Gotovo.")


if __name__ == "__main__":
    main()
```

### lab/README.md

# Lab — Dan 4: prediction-vs-decision, eligibilnost i rangiranje publike

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne menjaš
`dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` (`dm-ml/.venv` ih ima).
* Lab radi na malim, ručno napravljenim profilima — nema seeded CSV-a.

## Zadatak (koraci)

Kampanja je dict pravila (`target_segments`, `eligible_buckets`,
`min_probability`, `min_monetary`, `cost_per_contact`, `max_contacts`). Profil
je DataFrame po korisniku (`user_id`, `segment`, `rfm_bucket`, `probability`,
`monetary`). Pomoćna funkcija `_eligibility` je data (vraća
`(eligible, reasons)`).

1. **`score_customer(probability, segment, rfm_bucket, monetary, campaign)`** —
   skor odluke za jednog korisnika:

   * Neeligibilan -> `{"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": [...]}`.
   * Eligibilan -> `expected_value = probability*monetary − cost_per_contact`
     (zaokruži na 4 decimale), `score = expected_value`, i dodaj razlog
     `f"očekivana vrednost = {p}*{value} - {cost} = {ev}"`.
   * Ovo je **prediction-vs-decision**: korisnik sa najvećom verovatnoćom nije
     nužno najbolja odluka (npr. P=0.9×100 < P=0.6×400).
2. **`select_target_customers(profiles, campaign)`** — primeni pravila na ceo
   profil (koristi `_eligibility` red-po-red), zadrži samo eligibilne, dodaj
   kolonu `selected_reasons`, sortiraj po `user_id`. Prazan ulaz -> prazan
   DataFrame.
3. **`rank_target_customers(selected, campaign, limit=None)`** — izračunaj
   `score_customer` za svaku vrstu, sortiraj po `score` opadajuće (tie-break po
   `user_id`), dodaj `rank` 1..N, klipuj `limit` na `max_contacts` i vrati
   `head` najboljih sa kolonama `rank`, `user_id`, `score`, `expected_value`,
   `probability`, `segment`, `rfm_bucket`, `monetary`, `reasons`.
4. **`rule_based_score(rfm_bucket, monetary)`** — rule baseline bez ML-a:
   `BUCKET_PRIORITY[rfm_bucket] * 1_000_000 + monetary`.

## Provera

```
# iz Day 4/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: eligibilnost + skor odluke (očekivana vrednost), selektovanje po
  pravilima, rangiranje + limita, rule-based baseline.
* Ne radiš: ceo `dm-ml` servis, API, modele (segment/konverzija), perzistenciju,
  `compare_rule_vs_ml` — to koristi tvoje funkcije u `app/ml/` i servisu.
  `_eligibility` je data (kao što je `build_features` bio dat u Day 3 lab-u).

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.

### lab/starter.py

```
"""Starter za Day 4 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 4/lab/``):

    python3 -m pytest test_lab.py                # tvoj starter
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # rešenje
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

# Prioritet RFM bucket-a za rule-based skor (baseline — bez ML-a).
BUCKET_PRIORITY = {
    "champions": 4,
    "loyal": 3,
    "at_risk": 2,
    "dormant": 1,
}


def _eligibility(
    probability: Optional[float],
    segment: Optional[str],
    rfm_bucket: Optional[str],
    monetary: Optional[float],
    campaign: dict,
) -> tuple[bool, list[str]]:
    """Eligibilnost po pravilima kampanje (DATA — ne implementiraš je).

    Pravila (svako proizvodi razlog):
      - ``target_segments``  — segment mora biti u listi (ako nije prazna).
      - ``eligible_buckets`` — rfm_bucket mora biti u listi (ako nije prazna).
      - ``min_probability``  — ``probability >= prag`` (ako je prag > 0).
      - ``min_monetary``     — ``monetary >= prag`` (ako je prag > 0).

    Vraća ``(eligible, reasons)`` — reasons je lista opisa (na srpskom).
    """
    reasons: list[str] = []

    target_segments = campaign.get("target_segments") or []
    if target_segments:
        ok = segment is not None and segment in set(target_segments)
        reasons.append(
            f"segment {segment} {'je' if ok else 'nije'} u ciljanim segmentima"
        )
        if not ok:
            return False, reasons

    eligible_buckets = campaign.get("eligible_buckets") or []
    if eligible_buckets:
        ok = rfm_bucket is not None and rfm_bucket in set(eligible_buckets)
        reasons.append(
            f"rfm_bucket {rfm_bucket} {'je' if ok else 'nije'} u dozvoljenim"
        )
        if not ok:
            return False, reasons

    min_probability = float(campaign.get("min_probability", 0.0) or 0.0)
    if min_probability > 0.0:
        if probability is None:
            reasons.append("nema verovatnoće")
            return False, reasons
        ok = float(probability) >= min_probability
        reasons.append(f"P({float(probability):.4f}) {'>=' if ok else '<'} {min_probability:.4f}")
        if not ok:
            return False, reasons

    min_monetary = float(campaign.get("min_monetary", 0.0) or 0.0)
    if min_monetary > 0.0:
        value = 0.0 if monetary is None else float(monetary)
        ok = value >= min_monetary
        reasons.append(f"vrednost {value:.2f} {'>=' if ok else '<'} {min_monetary:.2f}")
        if not ok:
            return False, reasons

    return True, reasons


def score_customer(
    probability: Optional[float],
    segment: Optional[str],
    rfm_bucket: Optional[str],
    monetary: Optional[float],
    campaign: dict,
) -> dict:
    """Skor odluke za jednog korisnika. TODO: implementirati.

    Zahtevi (definicije su deo zadatka):
    - Ako je korisnik neeligibilan (``_eligibility``) -> vrati
      ``{"eligible": False, "score": 0.0, "expected_value": 0.0,
      "reasons": reasons}``.
    - Ako je eligibilan -> ``expected_value = probability*monetary −
      campaign["cost_per_contact"]`` (``0.0`` za ``None``), ``score =
      expected_value`` (zaokruži na 4 decimale) i dodaj razlog
      ``f"očekivana vrednost = {p}*{value} - {cost} = {ev}"``.
    """
    raise NotImplementedError("implementiraj score_customer")


def select_target_customers(
    profiles: pd.DataFrame,
    campaign: dict,
) -> pd.DataFrame:
    """Primeni pravila kampanje na profil -> skup kandidata. TODO: implementirati.

    Zahtevi:
    - Za svaku vrstu pozovi ``_eligibility``; zadrži samo eligibilne.
    - Dodaj kolonu ``selected_reasons`` (lista razloga — samo za one koji su
      prošli; za ne-eligibilne razlozi su prazna lista).
    - Vrati DataFrame samo sa eligibilnim vrstama, sortiran po ``user_id``.
    - Ako je ``profiles`` prazan -> vrati prazan DataFrame (``pd.DataFrame()``).
    """
    raise NotImplementedError("implementiraj select_target_customers")


def rank_target_customers(
    selected: pd.DataFrame,
    campaign: dict,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Rangiraj po skoru i primeni limitu. TODO: implementirati.

    Zahtevi:
    - Računaj ``score_customer`` za svaku vrstu (kolone ``score``,
      ``expected_value``, ``reasons``).
    - Sortiraj po ``score`` opadajuće, tie-break po ``user_id`` rastuće.
    - Dodaj ``rank`` = 1..N (pre limita).
    - ``limit`` klipuj na ``campaign["max_contacts"]`` (ako je definisan);
      vrati ``head`` najboljih. Ako ``limit`` nije dat -> ``max_contacts``.
    - Vrati kolone: ``rank``, ``user_id``, ``score``, ``expected_value``,
      ``probability``, ``segment``, ``rfm_bucket``, ``monetary``, ``reasons``.
    """
    raise NotImplementedError("implementiraj rank_target_customers")


def rule_based_score(rfm_bucket: Optional[str], monetary: Optional[float]) -> float:
    """Rule-based skor (baseline — bez ML-a). TODO: implementirati.

    Zahtevi: ``BUCKET_PRIORITY[rfm_bucket] * 1_000_000 + monetary``
    (``0.0`` za ``None``). Rangira „visoke RFM korisnike" bez verovatnoće.
    """
    raise NotImplementedError("implementiraj rule_based_score")
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

CAMP = {"target_segments": ["segment_1"], "eligible_buckets": [], "min_probability": 0.3, "min_monetary": 0,
        "cost_per_contact": 1.0, "max_contacts": 2}
PROF = pd.DataFrame({"user_id": [3, 1, 2, 4], "probability": [0.9, 0.5, 0.2, 0.9],
                     "segment": ["segment_1", "segment_1", "segment_1", "segment_0"],
                     "rfm_bucket": ["loyal", "champions", "loyal", "dormant"], "monetary": [100.0, 300.0, 50.0, 999.0]})


def test_score_customer():
    s = lab.score_customer(0.5, "segment_1", "loyal", 300.0, CAMP)
    assert s["eligible"] and s["expected_value"] == 149.0 and "očekivana vrednost" in s["reasons"][-1]
    n = lab.score_customer(0.1, "segment_1", "loyal", 300.0, CAMP)
    assert n == {"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": n["reasons"]}


def test_select_and_rank():
    sel = lab.select_target_customers(PROF, CAMP)
    assert list(sel["user_id"]) == [1, 3]
    assert lab.select_target_customers(PROF.iloc[0:0], CAMP).empty
    r = lab.rank_target_customers(sel, CAMP, limit=10)
    assert list(r["user_id"]) == [1, 3] and list(r["rank"]) == [1, 2]   # limit klipovan na max_contacts=2
    assert len(lab.rank_target_customers(sel, CAMP, limit=1)) == 1


def test_rule_based_score():
    assert lab.rule_based_score("champions", 10.0) == 4_000_010.0
    assert lab.rule_based_score("loyal", None) == 3_000_000.0
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 4 lab-a."""
from __future__ import annotations

import pandas as pd

from starter import BUCKET_PRIORITY, _eligibility  # noqa: F401


def score_customer(probability, segment, rfm_bucket, monetary, campaign):
    ok, reasons = _eligibility(probability, segment, rfm_bucket, monetary, campaign)
    if not ok:
        return {"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": reasons}
    p = 0.0 if probability is None else float(probability)
    v = 0.0 if monetary is None else float(monetary)
    cost = float(campaign.get("cost_per_contact", 0.0) or 0.0)
    ev = round(p * v - cost, 4)
    return {"eligible": True, "score": ev, "expected_value": ev,
            "reasons": reasons + [f"očekivana vrednost = {p}*{v} - {cost} = {ev}"]}


def select_target_customers(profiles, campaign):
    if profiles is None or len(profiles) == 0:
        return pd.DataFrame()
    keep, why = [], []
    for r in profiles.itertuples(index=False):
        ok, reasons = _eligibility(getattr(r, "probability", None), getattr(r, "segment", None),
                                   getattr(r, "rfm_bucket", None), getattr(r, "monetary", None), campaign)
        keep.append(ok); why.append(reasons if ok else [])
    out = profiles.assign(selected_reasons=why)[keep]
    return out.sort_values("user_id").reset_index(drop=True)


def rank_target_customers(selected, campaign, limit=None):
    cols = ["rank", "user_id", "score", "expected_value", "probability", "segment", "rfm_bucket", "monetary", "reasons"]
    if selected is None or len(selected) == 0:
        return pd.DataFrame(columns=cols)
    sc = [score_customer(r.probability, r.segment, r.rfm_bucket, r.monetary, campaign)
          for r in selected.itertuples(index=False)]
    df = selected.assign(score=[s["score"] for s in sc], expected_value=[s["expected_value"] for s in sc],
                         reasons=[s["reasons"] for s in sc])
    df = df.sort_values(["score", "user_id"], ascending=[False, True]).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    mx = campaign.get("max_contacts")
    lim = mx if limit is None else (min(int(limit), int(mx)) if mx else int(limit))
    return (df.head(int(lim)) if lim is not None else df)[cols]


def rule_based_score(rfm_bucket, monetary):
    return BUCKET_PRIORITY.get(rfm_bucket, 0) * 1_000_000 + (0.0 if monetary is None else float(monetary))
```
