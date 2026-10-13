# Day 5 podaci — product text korpus (izvedena tabela)

Deterministička, **byte-for-byte reproduktivna** tabela **izvedena** iz Day 1
seeded kataloga (ne duplira ga). Kompletna dokumentacija (izvor, parametri,
značenje polja, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Redova |
| --- | --- | --- |
| `products_text.csv` | 252 proizvoda: katalog + `product_text` (za TF-IDF) + `popularity` (baseline skor) | 252 |
| `metadata.json` | izvor, counts, značenja polja, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 1/data/products.csv` + `Day 1/data/categories.csv` +
  `Day 1/data/events.csv` (jedini izvor istine).
* Tekst: `prepare_product_text` (`app/recommenders/content.py`) —
  `category_name + name + description` (kategorija je token).
* Popularnost: `_popularity_from_events` — težinski zbir događaja po proizvodu
  (`product_view`=1, `add_to_cart`=3, `purchase`=5).
* Generator: `app/data/generate_product_text.py` (upisuje CSV + metadata).

## Ključne kolone (`products_text.csv`)

| Kolona | Značenje |
| --- | --- |
| `product_id` | FK -> `products.product_id` |
| `category_id` / `category_name` | kategorija (name je i token u tekstu) |
| `name` / `slug` / `description` | katalog (iz Day 1) |
| `img_url` / `price` | slika / cena (za product page) |
| `product_text` | tekst za TF-IDF: `category + name + description` |
| `popularity` | težinski zbir događaja — popularity baseline skor |

## Stanje u ovom seed-u

* proizvoda: **252** (12 kategorija × 21)
* proizvoda sa događajima: **252**
* popularnost: min **70** · med **288** · max **2115**
* top-5 po popularnosti: **90, 184, 110, 12, 49**

## Regeneracija (byte-for-byte)

```
cd dm-ml
.venv/bin/python -m app.data.generate_product_text
```

Dva pokretanja daju identične fajlove (isti sha256, vidi
`metadata.json → manifest.sha256`).

## Šta ovi podaci NE dokazuju

`product_text` je *ulaz* za content preporuke, ne rezultat. Sličan tekst nije
isto što i dobra preporuka (vidi Day 5 README, „What the result does NOT
prove"). Popularnost je baseline za poređenje, ne istina o kvalitetu proizvoda.
