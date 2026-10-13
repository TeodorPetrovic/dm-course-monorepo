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
