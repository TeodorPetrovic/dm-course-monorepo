"""Generiše teaching/day-NN/PLAN.md i teaching/README.md iz TEACH blokova u kodu + teaching/timings.json.
Pokretanje: apps/api/.venv/bin/python teaching/build_plans.py   (posle izmene blokova)"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
import teach  # noqa: E402
TIM = json.loads((ROOT / "teaching/timings.json").read_text())

D = {  # tema, teorija (čas 1), checkpoint komande, frontend stranica, primeri, generatori, opcione ekstre, iskrena napomena
 1: dict(t="Praćenje događaja, analitika, sintetički generator", theory=["8 tipova događaja i šema (`create_event`)", "funnel view→cart→purchase, konverzija, AOV po porudžbini", "sintetički generator: sezonalnost, sesije, seed 42 (samo walk-through `generate_dataset.py`)"],
    ex=["Day 1/examples/demo_events.py", "Day 1/examples/demo_analytics.py"], gen=["generate_dataset"],
    curl=["curl -s -X POST localhost:3001/events -H 'Content-Type: application/json' -d '{\"event_type\":\"product_view\",\"user_id\":395,\"user_session\":\"s1\",\"product_id\":1}'", "curl -s localhost:3001/analytics/conversion-rate", "curl -s localhost:3001/analytics/average-order-value"],
    page="/product/<slug> pa /admin/event (događaji iz lokalne baze)", extra=["`share_by_category` (opciono, --full)", "Nitro ruta `server/api/event/track.post.ts` (opciono, --full; inače walk-through)"],
    note="AOV = suma / broj porudžbina (893), ne po stavci (1 045)."),
 2: dict(t="Segmentacija kupaca (RFM + K-Means)", theory=["RFM i skaliranje (zašto StandardScaler)", "K-Means, izbor k (silhouette)", "profil segmenta = čitljiv opis, ne ID"],
    ex=["Day 2/examples/demo_segmentation.py"], gen=["generate_features"], curl=["curl -s -X POST localhost:3001/segments/train -H 'Content-Type: application/json' -d '{\"k\":4}'", "curl -s localhost:3001/customers/395/segment"],
    page="/admin/segments → Treniraj", extra=["`profile_segments` (opciono, --full)", "`visualize_clusters.py` (PCA slika)", "manual RFM vs K-Means (ARI)"], note="Većina kupaca nema kupovinu → jedan veliki „dormant“ segment je očekivan."),
 3: dict(t="Predikcija konverzije", theory=["vremenski cutoff i prozor (bez curenja budućnosti)", "logistička regresija vs majority baseline", "precision/recall/F1 kad je klasa retka (~6%)"],
    ex=["Day 3/examples/demo_conversion.py"], gen=["generate_training"], curl=["curl -s -X POST localhost:3001/models/conversion/train -H 'Content-Type: application/json' -d '{}'", "curl -s localhost:3001/customers/395/conversion-probability"],
    page="/admin/conversion → Treniraj, GET probability", extra=["`ConversionService.train` (opciono, --full; inače walk-through)", "leakage vežba (`run_leakage_exercise`) — domaći", "`visualize_confusion.py`"], note="Accuracy baseline-a je visok zbog retke klase — gledamo recall/F1."),
 4: dict(t="ML-assisted targeting kampanja", theory=["skor odluke = P(kupovina) × vrednost − trošak kontakta", "selekcija pod budžetom (max_contacts) i rangiranje", "rule baseline i poređenje (lift, overlap)"],
    ex=["Day 4/examples/demo_targeting.py"], gen=["generate_targeting"], curl=["curl -s 'localhost:3001/campaigns/1/recommended-audience?mode=ml&limit=5'", "curl -s localhost:3001/campaigns/1/targeting-comparison"],
    page="/admin/campaigns → Prikaži publiku (ML/Rule)", extra=["`evaluate_campaign_rules` — walk-through (32 linije, ne kuca se)", "`visualize_targeting.py`"], note="ML publika je manja (lift 0.18–0.90 po broju), ali ima veći prosečni P i profit po kontaktu."),
 5: dict(t="Content-based preporuke (TF-IDF)", theory=["popularity i same-category baseline", "TF-IDF + kosinusna sličnost", "envelope odgovora (fallback, reason)"],
    ex=["Day 5/examples/demo_content_recommender.py"], gen=["generate_product_text"], curl=["curl -s 'localhost:3001/recommendations/content/1?limit=5'", "curl -s localhost:3001/recommendations/content/1/comparison"],
    page="/product/<slug> → sekcija „Recommended Products“", extra=["`visualize_content.py` (heatmap)", "vežba: min_df / bigrami"], note="Dan je lakši (≈60 linija) — ostatak vremena za lab u učionici."),
 6: dict(t="Collaborative preporuke (implicit feedback)", theory=["interakciona matrica i težine (view/cart/purchase)", "item-item kosinus", "heuristika co-occurrence vs CF"],
    ex=["Day 6/examples/demo_collaborative.py"], gen=["generate_interactions"], curl=["curl -s 'localhost:3001/recommendations/collaborative/1?limit=5'"],
    page="/product/<slug> → „Customers Also Viewed“", extra=["`toy_sgd.py` (matrix factorization od nule, 0.2 s) — opciono", "`mf_library.py` (implicit ALS)", "`visualize_weights.py`"], note="Težine događaja su ručne — weight_sensitivity pokazuje koliko menjaju rezultat."),
 7: dict(t="Evaluacija preporuka", theory=["temporalni split (bez curenja)", "P@K, recall@K, hit rate, NDCG, coverage", "poređenje metoda na istim test slučajevima"],
    ex=["Day 7/examples/demo_evaluation.py"], gen=["generate_evaluation"], curl=["curl -s localhost:3001/analytics/recommendations"],
    page="/admin/recommendations → tabela evaluacije", extra=["`make_content_predictor` / `make_collaborative_predictor` — walk-through", "`visualize_comparison.py`"], note="Kategorija je najbolja po P@5 (0.245), collaborative 0.239, content najslabiji (0.069)."),
 8: dict(t="Hibridni candidate-generation + ranking", theory=["kandidati iz više izvora, normalizacija skorova", "spajanje sa težinama (heuristika, ne učenje)", "poslovna pravila (kupljeno, dostupnost) i diverzifikacija"],
    ex=["Day 8/examples/demo_hybrid.py"], gen=["generate_hybrid"], curl=["curl -s 'localhost:3001/recommendations/395?limit=5'", "curl -s localhost:3001/analytics/recommendations/hybrid"],
    page="/shop → Personalized (bedž „For you“) i /admin/recommendations/hybrid", extra=["`normalize_scores`, `diversify_results` (opciono, --full)"], note="Popularity pobeđuje hybrid po P@5 (0.071 vs 0.058), hybrid ima mnogo veći coverage (0.504 vs 0.032)."),
 9: dict(t="Session-aware preporuke i feedback loop", theory=["signali tekuće sesije sa recency težinama", "CTR po algoritmu i poziciji", "simulacija popular vs personalized"],
    ex=["Day 9/examples/demo_session.py"], gen=["generate_session"], curl=["curl -s 'localhost:3001/recommendations/session/session_005246?limit=5'", "curl -s localhost:3001/analytics/recommendations/ctr"],
    page="/product/<slug> → „Based on your session“ i /admin/recommendations (CTR kartica)", extra=["vežba: drugačiji half-life"], note="Impression log je simuliran — CTR razlike su ilustracija, ne A/B test."),
 10: dict(t="Semantička pretraga i embedding preporuke", theory=["embedding = vektor značenja; normalizacija", "brute-force najbliži susedi (kosinus)", "keyword vs TF-IDF vs embedding"],
    ex=["Day 10/examples/demo_semantic.py"], gen=["generate_embeddings"], curl=["curl -s 'localhost:3001/search/semantic?q=wireless%20earbuds%20for%20travel&limit=3'", "curl -s 'localhost:3001/recommendations/semantic/1?limit=5'"],
    page="/search?q=wireless earbuds", extra=["vežba: kategorija u embedding ulazu"], note="Embedding gubi na „fitness and training gear“ (vraća bicikle) — pokaži to."),
 11: dict(t="Strukturisani generativni AI", theory=["strukturisan izlaz (JSON šema), validacija dužine i činjenica", "bounded retry i template fallback", "demo vs pravi provider (DeepSeek je PLAĆEN)"],
    ex=["Day 11/examples/demo_generative.py"], gen=[], curl=["curl -s -X POST localhost:3001/ai/seo -H 'Content-Type: application/json' -d '{\"product_name\":\"Smartphone Compact 686\",\"description\":\"5G smartphone with OLED display.\",\"category_name\":\"Electronics\"}'"],
    page="/admin/ai → Generate SEO", extra=["`ExternalProvider.generate` (opciono, --full)", "uživo DeepSeek: `AI_PROVIDER=deepseek` (~3 poziva, plaćeno; izlaz varira)"], note="Demo režim je deterministički; pravi LLM ponekad izostavi kategoriju → validacija + retry."),
 12: dict(t="Integrisana platforma (capstone)", theory=["orkestracija modula sa fallback-om po modulu", "profil korisnika iz Day 2–4 modela", "homepage/product payload za CMS"],
    ex=["Day 12/examples/demo_platform.py"], gen=["generate_platform"], curl=["curl -s 'localhost:3001/platform/homepage?user_id=395&session_id=session_005246&limit=5'", "curl -s localhost:3001/platform/modules"],
    page="/ (početna: hero + profil + preporuke) i /product/<slug> (Platform sekcija)", extra=["`_available` (opciono, --full)", "završna diskusija: šta je ML, šta heuristika"], note="Modul status pokazuje koji moduli rade; trening Day 2/3 modela je preduslov za pun profil."),
}

def groups(n):
    d = f"d{n:02d}"; core, opt = {"A": [], "B": [], "C": []}, []
    for p, bl in teach.day_files(d).items():
        r = teach.rel(p)
        g = "C" if r.startswith("apps/frontend") else "B" if ("app/services/" in r or "app/api/" in r) else "A"
        for bd, title, s, e, *_ in bl:
            item = (r, title, e - s - 1)
            (opt if bd.endswith("+") else core[g]).append(item)
    if not core["A"]:  # Day 11/12: "algoritam" živi u servisu
        core["A"] = [x for x in core["B"] if "app/services/" in x[0]]; core["B"] = [x for x in core["B"] if "app/api/" in x[0]]
    return core, opt

def lst(items):
    return "\n".join(f"   - `{r}` → **{t}** ({k} lin.)" for r, t, k in items) or "   - (nema)"

rows = []
for n, s in D.items():
    core, opt = groups(n); la, lb, lc = (sum(x[2] for x in core[g]) for g in "ABC"); tot = la + lb + lc
    run = sum(TIM.get(g, 0) for g in s["gen"]) + sum(TIM.get(e, 0) for e in s["ex"])
    fits = "?"
    rows.append((n, s["t"], tot, la, lb, lc, sum(x[2] for x in opt), round(run, 1), fits))
    ex = "\n".join(f'   cd course && dm-ml/.venv/bin/python "{e}"' for e in s["ex"])
    gen = ", ".join(f"`generate_{g[9:]}` {TIM.get(g, 0)} s" if g.startswith("generate_") else g for g in s["gen"]) or "—"
    R = 0.5  # min po liniji (kucanje + objašnjenje)
    ma, mb, mc = round(la * R), round(lb * R), round(lc * R)
    c1 = 17 + min(ma, 23)                       # čas 1: teorija do 17, pa algoritam
    spill = max(0, ma - 23)                     # ostatak algoritma ide na početak časa 2
    b0 = spill; b1 = b0 + mb; cb = b1 + 3; c0 = cb; c1e = c0 + mc; cc = c1e + 2
    disc = max(5, 40 - cc)
    fits = "da" if cc <= 35 else ("tesno" if cc <= 40 else "NE")
    rows[-1] = rows[-1][:-1] + (fits,)
    ex = "\n".join(f'   cd course && dm-ml/.venv/bin/python "{e}"' for e in s["ex"])
    gen = ", ".join(f"`{g}` {TIM.get(g, 0)} s" for g in s["gen"]) or "—"
    spill_txt = f"- **0–{spill}** Završi algoritam (ostatak A), pa odmah Checkpoint A.\n" if spill else ""
    cpa = "Checkpoint A (+ pitanja)" if not spill else "Rezime + pitanja (Checkpoint A pomeren na početak časa 2)"
    md = f"""# Dan {n} — {s['t']} (2 × 45 min)

Lekcija: `lessons/{n:02d}-*.md`. Kucanje uživo: **{tot} linija** (algoritam {la}, servis+API {lb}, frontend {lc});
opciono još {sum(x[2] for x in opt)} (`--full`). Izvršavanje primera + generatora ≈ {round(run,1)} s (sa kešom iz `teach.sh prepare`).
Procena: ≈{ma + mb + mc} min kucanja od 90 → **staje: {fits}**.

## Pre časa
```
scripts/teach.sh prepare              # jednom (venv, podaci, HF model, baza, frontend build)
cd apps/api && .venv/bin/uvicorn app.main:app --port 3001 --reload     # terminal 1 (reload hvata kucanje)
cd apps/frontend && bun run dev                                         # terminal 2 (http://localhost:3000)
```
Generator(i) za ovaj dan: {gen}. Podaci su već u repou — na času se ništa sporo ne generiše.

## Čas 1 (0–45)
- **0–5** Cilj dana: u stanju rešenja pokaži `{s['page']}`; zatim `scripts/teach.sh start {n}` i `scripts/teach.sh diff {n}` (šta ćemo napisati).
- **5–17** Teorija:
""" + "\n".join(f"   - {x}" for x in s["theory"]) + f"""
- **17–{c1}** Kucaj algoritam (A, {la} lin., ≈{ma} min):
{lst(core['A'])}
- **{c1}–45 {cpa}**:
```
{ex}
```
  Ako kasniš: `git checkout HEAD -- <fajl>` za jedan fajl, ili `scripts/teach.sh solution {n}` za ceo dan.

## Čas 2 (0–45)
{spill_txt}- **{b0}–{b1}** Servis + API (B, {lb} lin.):
{lst(core['B'])}
- **{b1}–{cb} Checkpoint B** (API sa --reload):
```
""" + "\n".join(s["curl"]) + f"""
```
- **{c0}–{c1e}** Frontend deo (C, {lc} lin.) — dodaješ samo ovaj blok, ostatak Nuxt aplikacije je gotov:
{lst(core['C'])}
- **{c1e}–{cc} Checkpoint C**: otvori `{s['page']}`.
- **{cc}–{cc + disc}** Rezultati i diskusija: {s['note']}
- **{cc + disc}–45** Lab handoff: `course/Day {n}/lab/README.md` (starter.py + test_lab.py); domaći / opciono:
""" + "\n".join(f"   - {x}" for x in s["extra"]) + f"""

## Opcioni blokovi (`scripts/teach.sh start {n} --full`)
{lst(opt)}

## Fallback i kraj
- Kasniš > 10 min: `scripts/teach.sh solution {n}` (vraća rešenje iz git HEAD-a; tvoje kucanje se odbacuje) i nastavi od sledećeg checkpoint-a.
- Posle časa: `scripts/teach.sh solution` pa `scripts/teach.sh check` (run_all + check_commands moraju da prođu).
"""
    dd = ROOT / f"teaching/day-{n:02d}"; dd.mkdir(parents=True, exist_ok=True); (dd / "PLAN.md").write_text(md)

tbl = "\n".join(f"| {n} | {t} | {tot} | {a}/{b}/{c} | +{o} | {r} s | {f} |" for n, t, tot, a, b, c, o, r, f in rows)
(ROOT / "teaching/README.md").write_text(f"""# Nastava uživo — 12 dana × 2 × 45 min

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
{tbl}

Planovi minut po minut: `teaching/day-NN/PLAN.md`. Regeneriši posle izmene blokova: `apps/api/.venv/bin/python teaching/build_plans.py`.
""")
print("\n".join(str(r) for r in rows))
