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
.venv/bin/python "../Day 12/examples/demo_platform.py"       # demo
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
