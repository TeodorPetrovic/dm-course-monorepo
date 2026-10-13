"""Generatori izvedenih tabela Day 2–12 (sve iz Day 1 events/orders + Day 5 kataloga).

Svaki generator: ``python -m app.data.generate_<ime> [--out-dir DIR]``. Podrazumevano piše u
``Day N/data``; ``--out-dir`` piše drugde (npr. za poređenje sha256 sa committed fajlom).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import pandas as pd

from app.data.paths import day_data


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _inputs():
    return pd.read_csv(day_data(1, "events.csv")), pd.read_csv(day_data(1, "orders.csv"))


def _write(df: pd.DataFrame, out: Path, name: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / name, index=False)
    return {name: sha(out / name)}


def gen_features(out):
    from app.ml.features import build_customer_features
    ev, od = _inputs()
    return _write(build_customer_features(ev, od), out, "customer_features.csv")


def gen_training(out):
    from app.ml.conversion import build_training_dataset, run_leakage_exercise
    ev, od = _inputs()
    h = _write(build_training_dataset(ev, od, 7, leaky=False), out, "training_dataset.csv")
    h.update(_write(build_training_dataset(ev, od, 7, leaky=True), out, "leaky_training_dataset.csv"))
    (out / "leakage_metrics.json").write_text(json.dumps(run_leakage_exercise(ev, od), indent=2) + "\n")
    return h


def gen_targeting(out):
    from app.data.campaigns import write_campaigns_csv
    from app.services.conversion import ConversionService
    from app.services.segmentation import SegmentationService
    from app.services.targeting import build_targeting_profile
    import joblib
    ev, od = _inputs()
    with tempfile.TemporaryDirectory() as tmp:
        s, c = SegmentationService(Path(tmp)), ConversionService(Path(tmp))
        s.train(); c.train()
        prof = build_targeting_profile(ev, od, joblib.load(Path(tmp) / s.MODEL), joblib.load(Path(tmp) / s.SCALER),
                                       joblib.load(Path(tmp) / c.MODEL), joblib.load(Path(tmp) / c.SCALER))
    h = _write(prof, out, "customer_profiles.csv")
    write_campaigns_csv(out / "campaigns.csv"); h["campaigns.csv"] = sha(out / "campaigns.csv")
    return h


def gen_product_text(out):
    from app.recommenders.content import popularity_from_events, prepare_product_text
    ev, _ = _inputs()
    p = pd.read_csv(day_data(1, "products.csv")); cats = pd.read_csv(day_data(1, "categories.csv"))
    cat_name = dict(zip(cats.iloc[:, 0], cats["name"] if "name" in cats else cats.iloc[:, 1]))
    p.insert(2, "category_name", p["category_id"].map(cat_name))
    p["product_text"] = prepare_product_text(p).values
    p["popularity"] = p["product_id"].map(popularity_from_events(ev)).fillna(0.0)
    cols = ["product_id", "category_id", "category_name", "name", "slug", "description", "img_url", "price",
            "product_text", "popularity"]
    return _write(p[cols], out, "products_text.csv")


def gen_interactions(out):
    from app.recommenders.collaborative import build_interaction_matrix
    ev, _ = _inputs()
    p = pd.read_csv(day_data(1, "products.csv"))
    inter = build_interaction_matrix(ev, products=p["product_id"])
    return _write(inter.to_long_frame(), out, "interactions.csv")


def gen_evaluation(out):
    from app.recommenders.evaluation import build_comparison_report
    ev, _ = _inputs()
    r = build_comparison_report(ev, pd.read_csv(day_data(5, "products_text.csv")))
    tc = pd.DataFrame(r["test_cases"]); tc["target_product_ids"] = tc["target_product_ids"].map(
        lambda l: ";".join(map(str, l)))
    h = _write(tc, out, "test_cases.csv"); h.update(_write(pd.DataFrame(r["comparison"]), out, "comparison.csv"))
    return h


def gen_hybrid(out):
    from app.services.hybrid import DEMO_USER_IDS, HybridRecommenderService
    s = HybridRecommenderService(products=pd.read_csv(day_data(5, "products_text.csv")), events=_inputs()[0])
    cand, rank = [], []
    for u in DEMO_USER_IDS:
        r = s.models.recommend(u, 5)
        if r is None:
            continue
        for src, lst in r["candidates"].items():
            cand += [{"user_id": u, "source": src, "product_id": c["product_id"], "score": c["score"],
                      "rank_in_source": c["rank_in_source"]} for c in lst]
        rank += [{"user_id": u, "position": i, "product_id": c["product_id"], "name": c.get("name"),
                  "category_id": c.get("category_id"), "score": round(c["score"], 9),
                  "sources": ";".join(c["sources"])} for i, c in enumerate(r["final"], 1)]
    h = _write(pd.DataFrame(cand), out, "candidates.csv"); h.update(_write(pd.DataFrame(rank), out, "ranking.csv"))
    h.update(_write(pd.DataFrame(s.user_based_comparison(5)["comparison"]), out, "comparison.csv"))
    return h


CLICK_MODEL = {"relevant_base": 0.06, "base": 0.02, "position_factors": [1.0, 0.6, 0.4, 0.3, 0.2]}


def simulate_impressions(events, products, seed=42, n_sessions=200, k=5, min_events=2):
    """Day 9: deterministička simulacija eksperimenta popular vs personalized.

    Za svaku uzorkovanu sesiju (>= ``min_events`` product događaja) loguje se k impresija po algoritmu.
    Klik: ``p = (relevant_base ako je proizvod u top-2 kategorijama sesije, inače base) × position_factor``
    — ISTI model za oba algoritma; razlika u CTR-u dolazi samo od toga koliko relevantnih proizvoda
    algoritam stavi na koje pozicije. To je SIMULACIJA, ne ponašanje stvarnih korisnika.
    """
    import numpy as np
    from app.recommenders.content import recommend_popular
    from app.recommenders.session import recommend_for_session, session_features
    from app.services.collaborative import CollaborativeRecommenderService
    rng = np.random.default_rng(seed)
    cats = dict(zip(products["product_id"].astype(int), products["category_id"].astype(int)))
    names = dict(zip(products["product_id"].astype(int), products["name"]))
    pe = events[events["event_type"].isin(["product_view", "add_to_cart", "purchase"])]
    cnt = pe.groupby("user_session").size()
    elig = sorted(cnt[cnt >= min_events].index)
    picked = list(rng.choice(elig, size=n_sessions, replace=False))
    c = CollaborativeRecommenderService(products=products)
    sim, ids = c._similarity().toarray(), c._interaction().products
    by_s = {sid: g for sid, g in events[events["user_session"].isin(picked)].groupby("user_session")}
    rows = []
    for sid in picked:
        f = session_features(by_s[sid], cats)
        top = {t["category_id"] for t in f["top_categories"]}
        seen = f["seen_product_ids"]
        lists = {"popular": [int(x) for x in recommend_popular(products, limit=k, exclude=seen)["product_id"]],
                 "personalized": [r["product_id"] for r in recommend_for_session(f, products, sim, ids, k)]}
        for alg, lst in lists.items():
            for pos, pid in enumerate(lst, 1):
                rel = cats[pid] in top
                pr = (CLICK_MODEL["relevant_base"] if rel else CLICK_MODEL["base"]) * CLICK_MODEL["position_factors"][pos - 1]
                rows.append({"session_id": sid, "algorithm": alg, "position": pos, "product_id": pid,
                             "name": names[pid], "category_id": cats[pid], "session_top_category": rel,
                             "clicked": int(rng.random() < pr)})
    return pd.DataFrame(rows)


def gen_session(out):
    """Day 9: simulira impression log (popular vs personalized) pa računa CTR tabele."""
    from app.services.session import SessionRecommenderService
    ev, _ = _inputs()
    prods = pd.read_csv(day_data(5, "products_text.csv"))
    h = _write(simulate_impressions(ev, prods), out, "impressions.csv")
    s = SessionRecommenderService.__new__(SessionRecommenderService)
    s.impression_log = lambda: pd.read_csv(out / "impressions.csv")
    d = s.ctr_dashboard()
    rows = [{"level": "algorithm", "group": g["group"], "impressions": g["impressions"], "clicks": g["clicks"],
             "ctr": round(g["ctr"], 6)} for g in d["by_algorithm"]["groups"]]
    rows += [{"level": "position", "group": f"position_{g['group']}", "impressions": g["impressions"],
              "clicks": g["clicks"], "ctr": round(g["ctr"], 6)} for g in d["by_position"]["groups"]]
    h.update(_write(pd.DataFrame(rows), out, "ctr.csv"))
    h.update(_write(pd.DataFrame(s.popular_vs_personalized_comparison()["comparison"]), out, "comparison.csv"))
    return h


def gen_ai_comparison(out, provider="demo", sample=6):
    from app.services.ai import AIService, DemoProvider, build_default_provider, validate_generated_output
    p = pd.read_csv(day_data(5, "products_text.csv"))
    ids = list(p["product_id"])[:: max(1, len(p) // sample)][:sample]
    variants = ["valid", "length_fail", "facts_fail"]
    real = None if provider == "demo" else build_default_provider(provider)
    rows = []
    for i, pid in enumerate(ids):
        r = p[p["product_id"] == pid].iloc[0]
        prod = {"name": r["name"], "description": r["description"], "category": r["category_name"]}
        svc = AIService(provider=real)
        t = svc.template_seo(prod).model_dump()
        prov = real or DemoProvider(variants[i % 3])
        if isinstance(prov, DemoProvider):
            prov.product = prod
        from app.services.ai import parse_json_output, seo_prompt
        try:
            data = parse_json_output(prov.generate(seo_prompt(prod) if real else "seo")); src = prov.descriptor()["name"]
        except Exception:
            data, src = {}, f"{prov.descriptor()['name']} (invalid)"
        for method, d, s in (("template", t, "template"), ("llm", data, src)):
            chk = validate_generated_output(d, prod)
            kw = d.get("keywords", [])
            rows.append({"product_id": int(pid), "name": r["name"], "method": method, "source": s,
                         "seo_title": d.get("seo_title", ""), "seo_description": d.get("seo_description", ""),
                         "keywords": " | ".join(kw) if isinstance(kw, list) else str(kw),
                         "title_len": chk["title_len"], "desc_len": chk["desc_len"], "title_ok": chk["title_ok"],
                         "desc_ok": chk["desc_ok"], "fields_ok": chk["fields_ok"], "facts_ok": chk["facts_ok"],
                         "valid": chk["valid"]})
    return _write(pd.DataFrame(rows), out, "comparison.csv")


def gen_platform(out, users=(395, 1465), sessions=("session_005246", "session_001403")):
    from app.services.platform import IntegratedPlatformService
    s = IntegratedPlatformService()
    st = s.module_status()
    out.mkdir(parents=True, exist_ok=True)
    (out / "module-registry.json").write_text(json.dumps(
        {"description": "Integrated Marketing Platform — manifest arhitekture (Day 12).", "modules": st["modules"],
         "summary": st["summary"]}, ensure_ascii=False, indent=2) + "\n")
    snaps = []
    for u, sid in zip(users, sessions):
        hp = s.homepage_payload(u, sid, 5)
        snaps.append({"user_id": u, "session_id": sid, "hero": hp["hero"],
                      "recommendations": [r["product_id"] for r in hp["recommendations"]["recommendations"]],
                      "evaluation_summary": hp["evaluation_summary"]})
    (out / "homepage-snapshot.json").write_text(json.dumps({"snapshots": snaps}, ensure_ascii=False, indent=2,
                                                           default=str) + "\n")
    return {"module-registry.json": sha(out / "module-registry.json"),
            "homepage-snapshot.json": sha(out / "homepage-snapshot.json")}


GENERATORS = {"features": (2, gen_features), "training": (3, gen_training), "targeting": (4, gen_targeting),
              "product_text": (5, gen_product_text), "interactions": (6, gen_interactions),
              "evaluation": (7, gen_evaluation), "hybrid": (8, gen_hybrid), "session": (9, gen_session),
              "ai_comparison": (11, gen_ai_comparison), "platform": (12, gen_platform)}


def committed_sha(day: int) -> dict:
    m = json.loads(day_data(day, "metadata.json").read_text())
    return (m.get("manifest") or {}).get("sha256", {}) or m.get("sha256", {})


def cli(name: str, argv=None):
    ap = argparse.ArgumentParser(prog=f"generate_{name}")
    ap.add_argument("--out-dir", default=None); ap.add_argument("--seed", type=int, default=42)
    if name == "ai_comparison":
        ap.add_argument("--provider", default="demo", choices=["demo", "auto", "local", "external", "deepseek"])
        ap.add_argument("--sample", type=int, default=6)
    a = ap.parse_args(argv)
    day, fn = GENERATORS[name]
    out = Path(a.out_dir) if a.out_dir else day_data(day, "x").parent
    kw = {"provider": a.provider, "sample": a.sample} if name == "ai_comparison" else {}
    hashes = fn(out, **kw)
    ref = committed_sha(day)
    for f, h in hashes.items():
        status = "—" if f not in ref else ("MATCH (byte-for-byte)" if ref[f] == h else "DIFFERS from committed")
        print(f"{f}: sha256={h[:12]}…  {status}")
    return hashes
