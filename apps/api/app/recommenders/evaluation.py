"""Day 7 — offline evaluacija preporučivača (temporal split, P/R/HR/NDCG@K, coverage)."""
from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd

from app.data.events import PRODUCT_EVENT_TYPES

METRIC_NAMES = ["precision_at_k", "recall_at_k", "hit_rate_at_k", "ndcg_at_k"]


def _check(k):
    if k <= 0:
        raise ValueError("k mora biti > 0")


def precision_at_k(ranked_ids, relevant_ids, k):
    """Imenilac je min(k, len(top)) — namerno odstupanje od standardnog P@K (= /k)."""
    # TEACH d07: precision_at_k
    _check(k); top = list(dict.fromkeys(ranked_ids[:k]))
    if not top:
        return 0.0
    return len(set(top) & set(relevant_ids)) / min(k, len(top))
    # /TEACH


def recall_at_k(ranked_ids, relevant_ids, k):
    # TEACH d07: recall_at_k
    _check(k); rel = set(relevant_ids)
    if not ranked_ids or not rel:
        return 0.0
    return len(set(ranked_ids[:k]) & rel) / len(rel)
    # /TEACH


def hit_rate_at_k(ranked_ids, relevant_ids, k):
    # TEACH d07: hit_rate_at_k
    _check(k)
    return 1.0 if set(ranked_ids[:k]) & set(relevant_ids) else 0.0
    # /TEACH


def ndcg_at_k(ranked_ids, relevant_ids, k):
    # TEACH d07: ndcg_at_k
    _check(k); rel = set(relevant_ids); top = list(ranked_ids[:k])
    if not top or not rel:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 2) for i, p in enumerate(top) if p in rel)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel), len(top))))
    return dcg / idcg
    # /TEACH


def catalog_coverage(recommended_ids, catalog_size):
    # TEACH d07: catalog_coverage
    if catalog_size <= 0:
        raise ValueError("catalog_size mora biti > 0")
    return len(set(recommended_ids)) / catalog_size if len(recommended_ids) else 0.0
    # /TEACH


def metrics_at_k(ranked_ids, relevant_ids, k) -> dict:
    return {"precision_at_k": precision_at_k(ranked_ids, relevant_ids, k),
            "recall_at_k": recall_at_k(ranked_ids, relevant_ids, k),
            "hit_rate_at_k": hit_rate_at_k(ranked_ids, relevant_ids, k),
            "ndcg_at_k": ndcg_at_k(ranked_ids, relevant_ids, k)}


def compute_split_time(events: pd.DataFrame, split_ratio: float = 0.8) -> pd.Timestamp:
    ts = pd.to_datetime(events["timestamp"]).sort_values().reset_index(drop=True)
    return ts.iloc[int(len(ts) * split_ratio)]


def temporal_split(events: pd.DataFrame, split_ratio: float = 0.8, split_time=None):
    # TEACH d07: temporal_split
    ts = pd.to_datetime(events["timestamp"])
    split = pd.Timestamp(split_time) if split_time is not None else compute_split_time(events, split_ratio)
    return events[ts < split], events[ts >= split], split
    # /TEACH


def extract_test_cases(test_events: pd.DataFrame, min_session_items: int = 2) -> list:
    # TEACH d07: extract_test_cases
    ev = test_events[test_events["event_type"].isin(PRODUCT_EVENT_TYPES)].copy()
    ev["_p"] = pd.to_numeric(ev["product_id"], errors="coerce")
    ev = ev.dropna(subset=["_p", "user_session"])
    ev["_t"] = pd.to_datetime(ev["timestamp"])
    ev = ev.sort_values(["user_session", "_t"], kind="stable")
    cases = []
    for sid, g in ev.groupby("user_session", sort=True):
        prods = list(dict.fromkeys(int(p) for p in g["_p"]))
        if len(prods) < min_session_items:
            continue
        cases.append({"session_id": sid, "query_product_id": prods[0], "target_product_ids": prods[1:],
                      "n_targets": len(prods) - 1, "query_time": str(g["_t"].iloc[0])})
    return cases
    # /TEACH


# --- prediktori (trenirani SAMO na train delu) --------------------------------
def _pop_order(products, train):
    from app.recommenders.content import popularity_from_events
    pop = products["product_id"].map(popularity_from_events(train)).fillna(0.0)
    return products.assign(_pop=pop).sort_values(["_pop", "product_id"], ascending=[False, True])


def make_popularity_predictor(products, train, **_) -> Callable:
    # TEACH d07: make_popularity_predictor
    order = [int(p) for p in _pop_order(products, train)["product_id"]]
    return lambda q, k: [p for p in order if p != q][:k]
    # /TEACH


def make_category_predictor(products, train, **_) -> Callable:
    # TEACH d07: make_category_predictor
    df = _pop_order(products, train)
    cat = dict(zip(products["product_id"], products["category_id"]))
    by_cat = {c: [int(p) for p in g["product_id"]] for c, g in df.groupby("category_id", sort=False)}
    return lambda q, k: [p for p in by_cat.get(cat.get(q), []) if p != q][:k]
    # /TEACH


def make_content_predictor(products, train, **_) -> Callable:
    from app.recommenders.content import build_tfidf_matrix
    from app.services.recommender import TFIDF_KWARGS
    from sklearn.metrics.pairwise import cosine_similarity
    m, _v = build_tfidf_matrix(products, **TFIDF_KWARGS)
    sim = cosine_similarity(m)
    ids = np.asarray(products["product_id"]).astype(int); pos = {p: i for i, p in enumerate(ids)}

    def predict(q, k):
        if q not in pos:
            return []
        s = pd.Series(sim[pos[q]], index=ids).drop(q)
        s = s.reset_index().sort_values([0, "index"], ascending=[False, True])
        return [int(x) for x in s["index"].head(k)]
    return predict


def make_collaborative_predictor(products, train, **_) -> Callable:
    from app.recommenders.collaborative import build_interaction_matrix, calculate_item_similarity
    inter = build_interaction_matrix(train, products=products["product_id"])
    sim = calculate_item_similarity(inter).toarray()
    ids = np.asarray(inter.products); pos = {p: i for i, p in enumerate(ids)}
    nnz = np.asarray((inter.matrix > 0).sum(axis=0)).ravel()

    def predict(q, k):
        if q not in pos or nnz[pos[q]] == 0:
            return []  # cold start: evaluator broji kao promašaj (bez fallback-a)
        s = pd.Series(sim[pos[q]], index=ids).drop(q)
        s = s[s > 0].reset_index().sort_values([0, "index"], ascending=[False, True])
        return [int(x) for x in s["index"].head(k)]
    return predict


PREDICTOR_FACTORIES = {"popularity": make_popularity_predictor, "category": make_category_predictor,
                       "content": make_content_predictor, "collaborative": make_collaborative_predictor}


def evaluate_recommender(predict: Callable, cases: list, k: int, catalog_size: int) -> dict:
    # TEACH d07: evaluate_recommender
    sums = dict.fromkeys(METRIC_NAMES, 0.0); recommended = []
    for c in cases:
        ranked = predict(c["query_product_id"], k)
        recommended.extend(ranked)
        for n, v in metrics_at_k(ranked, c["target_product_ids"], k).items():
            sums[n] += v
    n = max(len(cases), 1)
    out = {m: round(sums[m] / n, 6) for m in METRIC_NAMES}
    out["catalog_coverage"] = round(catalog_coverage(recommended, catalog_size), 6)
    return out
    # /TEACH


def build_comparison_report(events, products, k: int = 5, split_ratio: float = 0.8,
                            min_session_items: int = 2, methods=None) -> dict:
    # TEACH d07: build_comparison_report
    train, test, split = temporal_split(events, split_ratio)
    cases = extract_test_cases(test, min_session_items)
    rows = []
    for name in (methods or PREDICTOR_FACTORIES):
        pred = PREDICTOR_FACTORIES[name](products, train)
        rows.append({"method": name, **evaluate_recommender(pred, cases, k, len(products))})
    return {"k": k, "split_ratio": split_ratio, "split_time": str(split), "n_train_events": len(train),
            "n_test_events": len(test), "n_test_sessions": int(test["user_session"].nunique()),
            "n_test_cases": len(cases), "comparison": rows, "test_cases": cases}
    # /TEACH
