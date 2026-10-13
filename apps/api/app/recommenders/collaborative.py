"""Day 6 — implicit-feedback collaborative filtering (item-item) + heuristika baseline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from app.recommenders.content import _with_score, envelope, recommend_popular

DEFAULT_WEIGHTS = {"product_view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}
WEIGHT_SCHEMES = {
    "view=1 cart=3 buy=5 (default)": DEFAULT_WEIGHTS,
    "all equal (co-occurrence)": {"product_view": 1.0, "add_to_cart": 1.0, "purchase": 1.0},
    "purchase dominates": {"product_view": 1.0, "add_to_cart": 2.0, "purchase": 10.0},
    "purchases only": {"product_view": 0.0, "add_to_cart": 0.0, "purchase": 1.0},
}


@dataclass
class InteractionMatrix:
    matrix: csr_matrix
    sessions: list
    products: list

    @property
    def shape(self):
        return self.matrix.shape

    def to_long_frame(self) -> pd.DataFrame:
        coo = self.matrix.tocoo()
        df = pd.DataFrame({"session_id": np.asarray(self.sessions)[coo.row],
                           "product_id": np.asarray(self.products)[coo.col], "value": coo.data})
        return df.sort_values(["session_id", "product_id"]).reset_index(drop=True)

    @classmethod
    def from_long_frame(cls, df: pd.DataFrame, products=None) -> "InteractionMatrix":
        sessions = sorted(df["session_id"].unique())
        prods = sorted(int(p) for p in (products if products is not None else df["product_id"].unique()))
        si = {s: i for i, s in enumerate(sessions)}; pi = {p: i for i, p in enumerate(prods)}
        m = csr_matrix((df["value"].astype(float), (df["session_id"].map(si), df["product_id"].map(pi))),
                       shape=(len(sessions), len(prods)))
        return cls(m, sessions, prods)

    @classmethod
    def from_long_csv(cls, path, products=None) -> "InteractionMatrix":
        return cls.from_long_frame(pd.read_csv(Path(path)), products)


def build_interaction_matrix(events_df: pd.DataFrame, weights: Optional[dict] = None,
                             aggregation: str = "max", level: str = "session",
                             products=None) -> InteractionMatrix:
    w = weights or DEFAULT_WEIGHTS
    if aggregation not in ("max", "sum", "binary"):
        raise ValueError("aggregation mora biti max|sum|binary")
    key = {"session": "user_session", "user": "user_id"}[level]
    ev = events_df[events_df["event_type"].isin([k for k, v in w.items() if v > 0])]
    ev = ev.assign(_p=pd.to_numeric(ev["product_id"], errors="coerce")).dropna(subset=["_p", key])
    ev = ev.assign(_w=ev["event_type"].map(w).astype(float), _p=ev["_p"].astype(int))
    if len(ev) == 0:
        prods = sorted(int(p) for p in products) if products is not None else []
        return InteractionMatrix(csr_matrix((0, len(prods))), [], prods)
    g = ev.groupby([key, "_p"])["_w"]
    agg = {"max": g.max(), "sum": g.sum(), "binary": g.max().clip(upper=1.0) * 0 + 1.0}[aggregation]
    df = agg.reset_index().rename(columns={key: "session_id", "_p": "product_id", "_w": "value"})
    df["session_id"] = df["session_id"].astype(str)
    return InteractionMatrix.from_long_frame(df, products)


def calculate_item_similarity(inter, row_normalize: bool = True):
    m = inter.matrix if isinstance(inter, InteractionMatrix) else inter
    if row_normalize:
        m = normalize(m, norm="l2", axis=1)  # session-length normalization
    return cosine_similarity(m.T, dense_output=False)


def _catalog_recs(products_df, pid_scores: pd.Series, limit: int) -> pd.DataFrame:
    df = products_df.assign(_s=products_df["product_id"].map(pid_scores)).dropna(subset=["_s"])
    df = df.sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return _with_score(df, df["_s"].round(4).values)


def recommend_from_item_similarity(products_df: pd.DataFrame, product_id: int, inter: InteractionMatrix,
                                   similarity=None, limit: int = 5) -> dict:
    if product_id not in set(inter.products):
        return envelope(product_id, "fallback", recommend_popular(products_df, limit=limit), "unknown_product")
    j = inter.products.index(product_id)
    if inter.matrix[:, j].nnz == 0:
        return envelope(product_id, "fallback",
                        recommend_popular(products_df, limit=limit, exclude=[product_id]), "no_interactions")
    sim = similarity if similarity is not None else calculate_item_similarity(inter)
    row = np.asarray(sim[j].toarray()).ravel() if hasattr(sim, "toarray") else np.asarray(sim[j]).ravel()
    s = pd.Series(row, index=inter.products).drop(product_id)  # target exclusion
    return envelope(product_id, "collaborative", _catalog_recs(products_df, s, limit))


def recommend_session_cooccurrence(products_df: pd.DataFrame, events_df: pd.DataFrame, product_id: int,
                                   limit: int = 5, weights: Optional[dict] = None) -> dict:
    """Veran port seed heuristike (recomendations.py): Σ(count × weight), bez normalizacije."""
    w = weights or DEFAULT_WEIGHTS
    pid = pd.to_numeric(events_df["product_id"], errors="coerce")
    sess = set(events_df.loc[pid == product_id, "user_session"].dropna())
    if not sess:
        reason = "unknown_product" if product_id not in set(products_df["product_id"]) else "no_interactions"
        return envelope(product_id, "fallback",
                        recommend_popular(products_df, limit=limit, exclude=[product_id]), reason)
    ev = events_df[events_df["user_session"].isin(sess) & pid.notna() & (pid != product_id)]
    ev = ev.assign(_w=ev["event_type"].map(w).fillna(0.0), _p=pd.to_numeric(ev["product_id"]).astype(int))
    scores = ev.groupby("_p")["_w"].sum()
    scores = scores[scores > 0]
    return envelope(product_id, "heuristic", _catalog_recs(products_df, scores, limit))


def _ids(env):
    return [r["product_id"] for r in env["recommendations"]]


def compare_heuristic_vs_cf(products_df, events_df, inter, product_id, similarity=None, limit=5) -> dict:
    h = recommend_session_cooccurrence(products_df, events_df, product_id, limit)
    c = recommend_from_item_similarity(products_df, product_id, inter, similarity, limit)
    return {"product_id": product_id, "heuristic": h, "collaborative": c,
            "overlap": [x for x in _ids(c) if x in set(_ids(h))]}


def weight_sensitivity_experiment(products_df, events_df, product_id, schemes=None, limit=5) -> dict:
    schemes = schemes or WEIGHT_SCHEMES
    rows, default_ids = [], None
    for name, w in schemes.items():
        inter = build_interaction_matrix(events_df, w, products=products_df["product_id"])
        env = recommend_from_item_similarity(products_df, product_id, inter, limit=limit)
        ids = _ids(env)
        nonzero = sum(1 for r in env["recommendations"] if (r["score"] or 0) > 0)
        if default_ids is None:
            default_ids = ids
        rows.append({"name": name, "weights": w, "top_ids": ids, "method": env["method"],
                     "n_nonzero_scores": nonzero,
                     "overlap_with_default": len(set(ids) & set(default_ids))})
    return {"product_id": product_id, "limit": limit, "rows": rows}
