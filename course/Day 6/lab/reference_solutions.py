"""Referentno rešenje Day 6 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from starter import EVENT_WEIGHTS, RECOMMENDATION_COLUMNS  # noqa: F401


def build_interaction_matrix(events_df):
    ev = events_df[events_df["event_type"].isin(EVENT_WEIGHTS)].dropna(subset=["user_session", "product_id"])
    ev = ev.assign(_w=ev["event_type"].map(EVENT_WEIGHTS).astype(float), product_id=ev["product_id"].astype(int))
    agg = ev.groupby(["user_session", "product_id"])["_w"].max().reset_index()  # MAX, ne zbir
    sessions = sorted(agg["user_session"].astype(str).unique()); products = sorted(int(p) for p in agg["product_id"].unique())
    si = {s: i for i, s in enumerate(sessions)}; pi = {p: i for i, p in enumerate(products)}
    m = csr_matrix((agg["_w"], (agg["user_session"].astype(str).map(si), agg["product_id"].map(pi))),
                   shape=(len(sessions), len(products)))
    return m, sessions, products


def calculate_item_similarity(matrix):
    return np.asarray(cosine_similarity(matrix.T))


def _out(df, score):
    df = df.copy(); df["score"] = list(score)
    for c in RECOMMENDATION_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[RECOMMENDATION_COLUMNS].reset_index(drop=True)


def recommend_popular(products_df, limit=5):
    d = products_df.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def recommend_similar(products_df, product_id, matrix, products, limit=5):
    if product_id not in products:
        return recommend_popular(products_df, limit)
    row = calculate_item_similarity(matrix)[products.index(product_id)]
    s = pd.Series(row, index=products).drop(product_id)
    d = products_df.assign(_s=products_df["product_id"].map(s)).dropna(subset=["_s"])
    d = d.sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["_s"])
