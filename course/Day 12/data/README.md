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
