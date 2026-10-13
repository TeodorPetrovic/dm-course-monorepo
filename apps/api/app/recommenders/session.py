"""Day 9 — session-aware preporuke (recency-weighted interes) + CTR feedback-loop matematika."""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

EVENT_WEIGHTS = {"product_view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}


def recency_weights(n, decay):
    # TEACH d09: recency_weights
    return [decay ** (n - 1 - i) for i in range(n)]
    # /TEACH


def recent_product_interest(events, decay=0.8):
    # TEACH d09: recent_product_interest
    pe = [e for e in events if e.get("event_type") in EVENT_WEIGHTS and e.get("product_id") is not None]
    out: dict = defaultdict(float)
    for e, w in zip(pe, recency_weights(len(pe), decay)):
        out[int(e["product_id"])] += EVENT_WEIGHTS[e["event_type"]] * w
    return dict(out)
    # /TEACH


def recent_category_interest(events, product_categories, decay=0.8):
    # TEACH d09: recent_category_interest
    out: dict = defaultdict(float)
    for p, v in recent_product_interest(events, decay).items():
        if p in product_categories:
            out[product_categories[p]] += v
    return dict(out)
    # /TEACH


def recommendation_ctr(impressions, clicks):
    # TEACH d09: recommendation_ctr
    return len(clicks) / len(impressions) if len(impressions) else 0.0
    # /TEACH


def _group_ctr(impressions, clicks, key):
    # TEACH d09: _group_ctr
    imp, clk = defaultdict(int), defaultdict(int)
    for r in impressions:
        imp[r[key]] += 1
    for r in clicks:
        clk[r[key]] += 1
    return [{key: g, "impressions": imp.get(g, 0), "clicks": clk.get(g, 0),
             "ctr": clk.get(g, 0) / imp[g] if imp.get(g) else 0.0} for g in sorted(set(imp) | set(clk))]
    # /TEACH


def ctr_by_algorithm(impressions, clicks):
    return _group_ctr(impressions, clicks, "algorithm")


def session_features(session_events: pd.DataFrame, product_categories: dict, decay=0.8, top_n=2) -> dict:
    # TEACH d09: session_features
    ev = session_events.sort_values("timestamp", kind="stable")
    recs = [{"event_type": t, "product_id": (int(p) if pd.notna(p) else None)}
            for t, p in zip(ev["event_type"], pd.to_numeric(ev["product_id"], errors="coerce"))]
    pi = recent_product_interest(recs, decay)
    ci = recent_category_interest(recs, product_categories, decay)
    ts = pd.to_datetime(ev["timestamp"])
    top = lambda d, k: sorted(d.items(), key=lambda x: (-x[1], x[0]))[:k]
    return {"n_events": len(ev), "n_product_events": sum(r["event_type"] in EVENT_WEIGHTS for r in recs),
            "n_distinct_products": len(pi),
            "duration_minutes": round((ts.max() - ts.min()).total_seconds() / 60, 1) if len(ev) else 0.0,
            "top_categories": [{"category_id": int(c), "interest": round(v, 4)} for c, v in top(ci, top_n)],
            "top_products": [{"product_id": int(p), "interest": round(v, 4)} for p, v in top(pi, 3)],
            "seen_product_ids": sorted(pi), "_pi": pi, "_ci": ci}
    # /TEACH


def recommend_for_session(feats: dict, products: pd.DataFrame, similarity=None, sim_ids=None,
                          limit=5, w_category=0.5, w_similar=0.5) -> list:
    """score = 0.5·norm(interes kategorije × popularnost) + 0.5·norm(Σ interes × item-sim); viđeni isključeni."""
    # TEACH d09: recommend_for_session
    pop = dict(zip(products["product_id"].astype(int), products["popularity"].astype(float)))
    cat = dict(zip(products["product_id"].astype(int), products["category_id"].astype(int)))
    ci, pi, seen = feats["_ci"], feats["_pi"], set(feats["seen_product_ids"])
    cat_s = {p: ci.get(cat[p], 0.0) * pop[p] for p in pop if p not in seen}
    sim_s = {}
    if similarity is not None:
        pos = {p: i for i, p in enumerate(sim_ids)}
        for p in pop:
            if p in seen or p not in pos:
                continue
            sim_s[p] = sum(v * float(similarity[pos[q], pos[p]]) for q, v in pi.items() if q in pos)
    mc, ms = max(cat_s.values(), default=0) or 1, max(sim_s.values(), default=0) or 1
    scored = []
    for p in cat_s:
        a, b = cat_s[p] / mc, sim_s.get(p, 0.0) / ms
        s = w_category * a + w_similar * b
        if s > 0:
            src = [n for n, v in (("session_category", a), ("session_similar", b)) if v > 0]
            scored.append((-s, p, src))
    scored.sort()
    name = dict(zip(products["product_id"].astype(int), products["name"]))
    return [{"product_id": p, "name": name[p], "category_id": cat[p], "score": round(-s, 6), "sources": src}
            for s, p, src in scored[:limit]]
    # /TEACH


# --- imena iz lekcije (Day 9 "Važne funkcije") -----------------------------------
def get_current_session(events: pd.DataFrame, session_id: str, window_minutes=None) -> pd.DataFrame:
    """Događaji sesije sortirani po vremenu; opciono samo poslednjih ``window_minutes``."""
    ev = events[events["user_session"] == session_id].copy()
    ev["_t"] = pd.to_datetime(ev["timestamp"])
    ev = ev.sort_values("_t", kind="stable")
    if window_minutes and len(ev):
        ev = ev[ev["_t"] >= ev["_t"].max() - pd.Timedelta(minutes=window_minutes)]
    return ev.drop(columns="_t").reset_index(drop=True)


calculate_recent_product_interest = recent_product_interest
calculate_recent_category_interest = recent_category_interest
build_session_features = session_features
