# Day 11 podaci — template-vs-LLM SEO poređenje

Deterministički, **byte-for-byte reproduktivni** `comparison.csv` **izveden** iz
Day 5 kataloga (ne duplira ga). Kompletna dokumentacija (izvor, provider,
parametri, counts, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Oblik |
| --- | --- | --- |
| `comparison.csv` | **template vs LLM SEO** na 6 proizvoda — za svaki: template red (rule/heuristic baseline) i llm red (generisani), oba kroz iste provere (dužine / obavezna polja / product facts) | 12 redova |
| `metadata.json` | izvor, provider, parametri, summary, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 5/data/products_text.csv` (katalog sa nazivom, opisom, kategorijom).
* Za svaki proizvod iz determinističkog uzorka (svaki 42-i red, prvih 6):
  1. **template** red: `template_seo_metadata` (`app.services.templates`) —
     rule/heuristic baseline, uvek strukturno validan;
  2. **llm** red: `AIProvider.generate(seo_prompt(product))` → `parse_json_output`
     → iste provere (`compare_outputs`). Provider se bira preko
     `--provider demo|local|external|auto`.
* Generator: `app/data/generate_ai_comparison.py`.

## `comparison.csv` — šta poredi i šta validacija hvata

Provere su iste za obe strane (`compare_outputs`):

| Kolona | Značenje |
| --- | --- |
| `method` | `template` | `llm` |
| `source` | ko je generisao red: `template`, `demo:valid`, `demo:length_fail`, `demo:facts_fail`, `local`, `external`, `<name> (invalid)` |
| `title_len` / `desc_len` | dužine generisanog SEO naslova / opisa |
| `title_ok` | `title_len <= 60` (Google limit) |
| `desc_ok` | `desc_len <= 155` (Google limit) |
| `fields_ok` | sva obavezna polja prisutna (`seo_title`, `seo_description`, `keywords`) |
| `facts_ok` | naziv/kategorija proizvoda se pojavljuju u tekstu (slaba provera istinitosti) |
| `valid` | sve provere prolaze |

Committed uzorak koristi `--provider demo` — **scripted teaching double**
(NAPIŠEN U `metadata.json`), ne pravi LLM. Varijante (po poziciji u uzorku):

| Varijanta | Šta pokazuje |
| --- | --- |
| `demo:valid` | naslov kratak i sadrži naziv → prolazi sve provere |
| `demo:length_fail` | naslov sadrži naziv ali je **predugačak** (90+ > 60) → `title_ok=False` |
| `demo:facts_fail` | generički naslov/opis, **naziv se nigde ne pojavljuje** → `facts_ok=False` |

Template redovi su uvek `valid=True` (struktura je garantovana kodom), dok
LLM redovi pokazuju šta validacija mora da uhvati.

## Reprodukcija

```
cd dm-ml
.venv/bin/python -m app.data.generate_ai_comparison --provider demo   # committed (offline)
.venv/bin/python -m app.data.generate_ai_comparison --provider auto   # pravi provider ako je konfigurisan
.venv/bin/python -m app.data.generate_ai_comparison --provider external --sample 10
```

Isti provider + isti ulaz → identični fajlovi (sha256 u `metadata.json`).
Ako pokušaš `local`/`external` bez konfigurisanog providera, generator upozorava
i koristi demo (to beleži `metadata.provider_used`).
