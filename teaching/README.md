# Nastava uživo — 12 dana × 2 × 45 min

Svaki dan: **starter** (TODO blokovi tog dana; sve ostalo radi) i **rešenje** (= kod u repou). Blokovi su označeni u kodu:
`# TEACH dNN: ...` / `# /TEACH` (Python) i `// TEACH dNN: ...` / `// /TEACH` (TS/Vue). `dNN+` = opcioni blok (samo uz `--full`).

```
scripts/teach.sh prepare            # pre prvog časa (posle ~1 min): venv, podaci, HF model, baza, bun build, zagrevanje API-ja
scripts/teach.sh start 5            # starter stanje dana 5 (samo jedan dan u isto vreme)
scripts/teach.sh start 5 --full     # + opcioni blokovi
scripts/teach.sh diff 5             # šta starter uklanja
scripts/teach.sh lines [5]          # koliko se kuca uživo
scripts/teach.sh status             # koji dan je u starter stanju
scripts/teach.sh solution [5]       # rešenje (fallback kad kasniš)
scripts/teach.sh verify [--frontend]  # svaki dan: starter se primenjuje, kompajlira, API se diže (+ Nuxt build), rešenje čisto
scripts/teach.sh check [--frontend]   # rešenje: run_all + check_commands (+ smoke_frontend)
```
`start` uvek polazi od rešenja u git HEAD-u i odbija da pregazi nesačuvane izmene (bez `--force`).

## Procena po danu

Kucanje = linije u TEACH blokovima (gust kod; ≈0.5 min/linija sa objašnjenjem → 75 linija ≈ 40 min kucanja od 90).
Vreme izvršavanja = generator + primeri tog dana (izmereno, sa keširanim modelom; `teaching/timings.json`).

| Dan | Tema | Kucanje uživo | algoritam/servis+API/frontend | opciono | izvršavanje | staje u 2×45? |
|---|---|---|---|---|---|---|
| 1 | Praćenje događaja, analitika, sintetički generator | 76 | 57/9/10 | +34 | 11.5 s | da |
| 2 | Segmentacija kupaca (RFM + K-Means) | 75 | 47/22/6 | +14 | 3.5 s | da |
| 3 | Predikcija konverzije | 74 | 49/18/7 | +23 | 4.5 s | da |
| 4 | ML-assisted targeting kampanja | 76 | 48/26/2 | +0 | 6.3 s | da |
| 5 | Content-based preporuke (TF-IDF) | 59 | 47/10/2 | +0 | 2.5 s | da |
| 6 | Collaborative preporuke (implicit feedback) | 72 | 58/12/2 | +0 | 3.4 s | da |
| 7 | Evaluacija preporuka | 66 | 60/5/1 | +0 | 15.7 s | da |
| 8 | Hibridni candidate-generation + ranking | 73 | 39/24/10 | +22 | 13.8 s | da |
| 9 | Session-aware preporuke i feedback loop | 74 | 55/15/4 | +0 | 3.7 s | da |
| 10 | Semantička pretraga i embedding preporuke | 71 | 29/35/7 | +0 | 14.0 s | da |
| 11 | Strukturisani generativni AI | 75 | 67/4/4 | +7 | 1.5 s | da |
| 12 | Integrisana platforma (capstone) | 78 | 66/5/7 | +15 | 21.1 s | da |

Planovi minut po minut: `teaching/day-NN/PLAN.md`. Regeneriši posle izmene blokova: `apps/api/.venv/bin/python teaching/build_plans.py`.

## Iskrena procena i rebalans

Pre rebalansa (sve funkcije koje lekcija gradi, kucano uživo): Dan 1 = 110 linija, Dan 3 = 97, Dan 8 = 95, Dan 12 = 93 —
**previše** za 2×45 uz teoriju i diskusiju; Dan 5 = 38, Dan 6 = 47, Dan 7 = 47, Dan 10 = 43 — **premalo** (pola časa bez kodiranja).
Šta je promenjeno:
* **Veliki dani → opcioni blokovi (`dNN+`, samo `--full`) ili walk-through:** Dan 1 (`share_by_category`, Nitro `track.post.ts`),
  Dan 2 (`profile_segments`), Dan 3 (`ConversionService.train`; leakage vežba → domaći), Dan 4 (`evaluate_campaign_rules` walk-through),
  Dan 8 (`normalize_scores`, `diversify_results`), Dan 11 (`ExternalProvider.generate`), Dan 12 (`_available`).
* **Mali dani → više uživo:** Dan 5 (+popularity iz događaja, same-category, baseline poređenje), Dan 6 (+co-occurrence heuristika,
  poređenje, interakciona matrica u servisu), Dan 7 (+izdvajanje test slučajeva, popularity/category prediktori),
  Dan 10 (+hash embedder, `make_embedder`, poređenje keyword/TF-IDF/embedding), Dan 3 (+metrike, majority baseline).
* Rezultat: svaki dan 59–78 linija uživo, frontend 1–10 linija po danu (samo blok tog dana; ostatak Nuxt aplikacije je gotov).
* Dan 1 generator (`generate_dataset.py`, ~600 linija) se **ne kuca** — samo walk-through + pokretanje (7.5 s).

Ograničenja procene: 0.5 min/liniji pretpostavlja pripremljenog predavača koji kuca sa plana; prvi put računajte +20%.
Dan 1 i Dan 12 su najgušći (76/78) — tu koristite fallback `teach.sh solution NN` bez griže savesti.
Dan 12 starter: pun profil korisnika zahteva trenirane Day 2/3 modele (stranice Segments/Conversion ili `POST .../train`).
Najsporiji koraci (instalacija, HF model ~90 MB, `bun install`/build ~45 s, regenerisanje ~60 s) idu u `teach.sh prepare`;
na času ništa ne traje duže od ~25 s (Day 12 primer + generator).
