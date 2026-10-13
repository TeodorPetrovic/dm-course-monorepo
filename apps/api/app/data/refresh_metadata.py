"""Osvežava ``Day 2–12/data/metadata.json`` iz trenutno generisanih fajlova (brojevi, sažeci, sha256).

Struktura i opisna polja ostaju; menjaju se samo izvedene vrednosti. Deterministički (bez wall-clock vremena).
Pokretanje: ``python -m app.data.refresh_metadata`` (posle generatora; deo ``scripts/regenerate_all.sh``).
"""
from __future__ import annotations

import json

import pandas as pd

from app.data.generators import sha
from app.data.paths import day_data


def _load(d):
    return json.loads(day_data(d, "metadata.json").read_text())


def _save(d, m, files):
    m.pop("reconstruction_note", None)
    m["manifest"] = {"sha256": {f: sha(day_data(d, f)) for f in files}}
    day_data(d, "metadata.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n")


def refresh():
    from app.ml.features import reference_time
    ev = pd.read_csv(day_data(1, "events.csv")); od = pd.read_csv(day_data(1, "orders.csv"))
    ref = reference_time(ev, od); cut = ref - pd.Timedelta(days=7)

    m = _load(2); f = pd.read_csv(day_data(2, "customer_features.csv"))
    m["reference_date"] = str(ref)
    m["counts"] = {"customers": len(f), "buyers": int((f.frequency > 0).sum()), "zero_spend": int((f.frequency == 0).sum()),
                   "with_favorite_category": int(f.favorite_category.notna().sum())}
    _save(2, m, ["customer_features.csv"])

    m = _load(3); c = pd.read_csv(day_data(3, "training_dataset.csv")); lk = pd.read_csv(day_data(3, "leaky_training_dataset.csv"))
    lab = m.get("label_column", "will_purchase")
    m["reference_date"] = str(ref); m["cutoff_date"] = str(cut)
    m["counts"] = {"customers_clean": len(c), "buyers_in_window_clean": int(c[lab].sum()),
                   "positive_rate_clean": round(float(c[lab].mean()), 4), "customers_leaky": len(lk),
                   "buyers_in_window_leaky": int(lk[lab].sum())}
    le = json.loads(day_data(3, "leakage_metrics.json").read_text())
    det = le.get("details", le)
    m["leakage_exercise"]["summary"] = {"clean_f1": det["clean"]["f1"], "leaky_f1": det["leaky"]["f1"],
                                        "delta_f1": det["delta_f1"],
                                        "leaky_looks_better": bool(det["leaky"]["f1"] > det["clean"]["f1"])}
    m["leakage_exercise"]["details"] = det
    _save(3, m, ["training_dataset.csv", "leaky_training_dataset.csv"])

    m = _load(4); p = pd.read_csv(day_data(4, "customer_profiles.csv"))
    m["reference_date"] = str(ref); m["cutoff_date"] = str(cut)
    cnt = {"customers": len(p)}
    if "rfm_bucket" in p: cnt["by_rfm_bucket"] = {k: int(v) for k, v in p["rfm_bucket"].value_counts().items()}
    if "segment" in p: cnt["by_segment"] = {k: int(v) for k, v in p["segment"].value_counts().items()}
    if "frequency" in p: cnt["buyers"] = int((p["frequency"] > 0).sum())
    m["counts"] = cnt
    _save(4, m, ["customer_profiles.csv", "campaigns.csv"])

    m = _load(5); t = pd.read_csv(day_data(5, "products_text.csv"))
    m["counts"] = {"products": len(t), "categories": int(t.category_id.nunique()),
                   "by_category": {str(k): int(v) for k, v in t.category_id.value_counts().sort_index().items()},
                   "products_with_events": int((t.popularity > 0).sum()), "total_popularity": float(t.popularity.sum()),
                   "top_popular": [int(x) for x in t.sort_values(["popularity", "product_id"], ascending=[False, True]).product_id[:5]]}
    _save(5, m, ["products_text.csv"])

    m = _load(6); it = pd.read_csv(day_data(6, "interactions.csv"))
    scol = [c for c in it.columns if "session" in c][0]; pcol = "product_id"; vcol = [c for c in it.columns if c not in (scol, pcol)][0]
    ns, nnz = it[scol].nunique(), len(it)
    tv = it.groupby(pcol)[vcol].sum().sort_values(ascending=False, kind="stable")
    m["counts"] = {"sessions": int(ns), "products_total": 252, "products_with_interactions": int(it[pcol].nunique()),
                   "nnz": int(nnz), "density": round(nnz / (ns * 252), 6), "total_value": float(it[vcol].sum()),
                   "top_by_value": [int(x) for x in tv.index[:5]],
                   "sessions_with_2_plus_products": int((it.groupby(scol).size() >= 2).sum())}
    _save(6, m, ["interactions.csv"])

    from app.recommenders.evaluation import build_comparison_report
    r = build_comparison_report(ev, t)
    m = _load(7)
    m["parameters"]["split_time"] = r["split_time"]
    m["counts"] = {"n_train_events": r["n_train_events"], "n_test_events": r["n_test_events"],
                   "n_test_sessions": r["n_test_sessions"], "n_test_cases": r["n_test_cases"],
                   "methods": [x["method"] for x in r["comparison"]]}
    m["comparison"] = pd.read_csv(day_data(7, "comparison.csv")).to_dict("records")
    _save(7, m, ["test_cases.csv", "comparison.csv"])

    from app.services.hybrid import DEMO_USER_IDS, HybridRecommenderService
    s = HybridRecommenderService(products=t, events=ev); hm = s.models
    ub = s.user_based_comparison(5)
    m = _load(8)
    m["parameters"]["split_time"] = r["split_time"]; m["parameters"]["demo_user_ids"] = DEMO_USER_IDS
    m["parameters"]["available_ids_count"] = len(hm.available_ids)
    prof = {}
    for u in DEMO_USER_IDS:
        sig = hm.user_signal.get(u)
        prof[str(u)] = {"n_train_events": int(hm.user_events.get(u, 0)), "n_train_products": int(len(sig)) if sig is not None else 0,
                        "n_purchases": len(hm.user_purchased.get(u, set()))}
    m["counts"] = {"n_train_events": r["n_train_events"], "n_test_events": r["n_test_events"],
                   "n_test_users": ub.get("n_test_users", ub.get("n_users")),
                   "n_candidate_rows": len(pd.read_csv(day_data(8, "candidates.csv"))),
                   "n_ranking_rows": len(pd.read_csv(day_data(8, "ranking.csv"))), "n_catalog": 252, "profiles": prof}
    m["comparison"] = pd.read_csv(day_data(8, "comparison.csv")).to_dict("records")
    _save(8, m, ["candidates.csv", "ranking.csv", "comparison.csv"])

    from app.data.generators import CLICK_MODEL
    m = _load(9); im = pd.read_csv(day_data(9, "impressions.csv"))
    m["parameters"]["click_model"] = CLICK_MODEL
    m["description"] = ("Simulated experiment-ready log for the popular-vs-personalized CTR comparison. impressions.csv "
                        "logs k impressions per algorithm per sampled session with a DETERMINISTIC simulated click "
                        "(seed 42). The SAME click model is used for both algorithms (relevant_base if the product is "
                        "in the session's top-2 categories, else base, times a position factor), so the CTR difference "
                        "comes only from which products each algorithm ranks where. Data collection for an A/B "
                        "experiment, not a significance test.")
    m["counts"] = {"n_sessions": int(im.session_id.nunique()), "n_impressions": len(im),
                   "n_popular_impressions": int((im.algorithm == "popular").sum()),
                   "n_personalized_impressions": int((im.algorithm == "personalized").sum()),
                   "n_clicks": int(im.clicked.sum()), "n_catalog": 252}
    m["comparison"] = pd.read_csv(day_data(9, "comparison.csv")).to_dict("records")
    _save(9, m, ["impressions.csv", "ctr.csv", "comparison.csv"])

    m = _load(10); cmp_ = pd.read_csv(day_data(10, "comparison.csv")); emb = json.loads(day_data(10, "embeddings.json").read_text())
    import numpy as np
    z = np.load(day_data(10, "embeddings.npz"), allow_pickle=True)
    mat = z[[k for k in z.files if z[k].ndim == 2][0]]
    m["embedder"] = emb["embedder"]
    m["counts"] = {"n_products": int(mat.shape[0]), "dim": int(mat.shape[1]), "n_queries": int(cmp_["query"].nunique()),
                   "n_comparison_rows": len(cmp_)}
    m["summary"] = [{"query": q, "top": {meth: list(g[g.method == meth].sort_values("rank").name)
                                         for meth in ("keyword", "tfidf", "embedding")}}
                    for q, g in cmp_.groupby("query", sort=False)]
    _save(10, m, ["embeddings.npz", "embeddings.json", "comparison.csv"])

    m = _load(11); a = pd.read_csv(day_data(11, "comparison.csv"))
    tpl, llm = a[a.method == "template"], a[a.method == "llm"]
    m["summary"] = {"rows": len(a), "template_valid": int(tpl.valid.sum()), "llm_valid": int(llm.valid.sum()),
                    "title_over_60": int((~a.title_ok).sum()), "desc_over_155": int((~a.desc_ok).sum()),
                    "facts_missing": int((~a.facts_ok).sum())}
    _save(11, m, ["comparison.csv"])

    m = _load(12); reg = json.loads(day_data(12, "module-registry.json").read_text())
    snap = json.loads(day_data(12, "homepage-snapshot.json").read_text())
    m["parameters"]["users"] = [x["user_id"] for x in snap["snapshots"]]
    m["parameters"]["sessions"] = [x["session_id"] for x in snap["snapshots"]]
    mods = reg["modules"]
    m["counts"] = {"n_modules": len(mods), "n_available": sum(x["available"] for x in mods),
                   "n_unavailable": sum(not x["available"] for x in mods), "n_snapshots": len(snap["snapshots"])}
    m["summary"] = {"modules": [{"id": x["id"], "class": x["class"], "available": x["available"],
                                 "fallback": x.get("fallback")} for x in mods]}
    _save(12, m, ["module-registry.json", "homepage-snapshot.json"])
    print("metadata.json osveženi: Day 2–12")


if __name__ == "__main__":
    refresh()
