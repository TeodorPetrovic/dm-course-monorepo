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
