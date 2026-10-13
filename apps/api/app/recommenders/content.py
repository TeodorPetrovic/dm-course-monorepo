"""Day 5 — baseline-i (popularity/category) + content-based (TF-IDF + kosinus)."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RECOMMENDATION_COLUMNS = ["product_id", "name", "slug", "description", "img_url",
                          "category_id", "price", "score"]
POPULARITY_WEIGHTS = {"product_view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}


def popularity_from_events(events: pd.DataFrame, weights=None) -> pd.Series:
    # TEACH d05: popularity_from_events
    w = weights or POPULARITY_WEIGHTS
    ev = events[events["event_type"].isin(w)]
    pid = pd.to_numeric(ev["product_id"], errors="coerce")
    return ev.assign(_w=ev["event_type"].map(w), _p=pid).dropna(subset=["_p"]).groupby(
        ev.assign(_p=pid).dropna(subset=["_p"])["_p"].astype(int))["_w"].sum()
    # /TEACH


def _with_score(df: pd.DataFrame, score) -> pd.DataFrame:
    out = df.copy()
    out["score"] = score
    for c in RECOMMENDATION_COLUMNS:
        if c not in out.columns:
            out[c] = None
    return out[RECOMMENDATION_COLUMNS].reset_index(drop=True)


def _popularity(products_df: pd.DataFrame, events_df: Optional[pd.DataFrame]) -> pd.Series:
    if "popularity" in products_df.columns:
        return products_df["popularity"].astype(float)
    if events_df is not None and len(events_df):
        pop = popularity_from_events(events_df)
        return products_df["product_id"].map(pop).fillna(0.0).astype(float)
    return pd.Series(1.0, index=products_df.index)


def recommend_popular(products_df: pd.DataFrame, events_df: Optional[pd.DataFrame] = None,
                      limit: int = 5, exclude=None) -> pd.DataFrame:
    # TEACH d05: recommend_popular
    df = products_df.assign(_pop=_popularity(products_df, events_df))
    if exclude:
        df = df[~df["product_id"].isin(set(exclude))]
    df = df.sort_values(["_pop", "product_id"], ascending=[False, True]).head(limit)
    return _with_score(df, df["_pop"].values)
    # /TEACH


def recommend_same_category(products_df: pd.DataFrame, product_id: int, limit: int = 5,
                            events_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    # TEACH d05: recommend_same_category
    hit = products_df[products_df["product_id"] == product_id]
    if hit.empty:
        raise ValueError(f"nepoznat proizvod {product_id}")
    cat = hit.iloc[0]["category_id"]
    df = products_df.assign(_pop=_popularity(products_df, events_df))
    df = df[(df["category_id"] == cat) & (df["product_id"] != product_id)]
    df = df.sort_values(["_pop", "product_id"], ascending=[False, True]).head(limit)
    return _with_score(df, df["_pop"].values)
    # /TEACH


def prepare_product_text(products_df: pd.DataFrame, include_category: bool = True,
                         category_tokens: Optional[dict] = None) -> pd.Series:
    # TEACH d05: prepare_product_text
    parts = products_df["name"].fillna("") + " " + products_df["description"].fillna("")
    if include_category and "category_name" in products_df.columns:
        cat = products_df["category_name"].fillna("")
        if category_tokens:
            extra = products_df["category_id"].map(category_tokens).fillna("")
            cat = (cat + " " + extra).str.strip()
        parts = cat + " " + parts
    return pd.Series(parts.str.strip().values, index=products_df["product_id"].values, name="product_text")
    # /TEACH


def build_tfidf_matrix(products_df: pd.DataFrame, text_column: str = "product_text",
                       stop_words="english", ngram_range=(1, 2), min_df=1, **kwargs):
    # TEACH d05: build_tfidf_matrix
    texts = products_df[text_column] if text_column in products_df.columns else prepare_product_text(products_df)
    vec = TfidfVectorizer(stop_words=stop_words, ngram_range=ngram_range, min_df=min_df, **kwargs)
    matrix = vec.fit_transform(list(texts.fillna("")))
    return matrix, vec
    # /TEACH


def calculate_product_similarity(tfidf_matrix, index: int) -> np.ndarray:
    # TEACH d05: calculate_product_similarity
    if not 0 <= index < tfidf_matrix.shape[0]:
        raise IndexError(f"index {index} van opsega")
    return cosine_similarity(tfidf_matrix[index:index + 1], tfidf_matrix).flatten()
    # /TEACH


def envelope(product_id, method, recs: pd.DataFrame, fallback_reason=None, **extra) -> dict:
    records = []
    for r in recs.to_dict("records"):
        records.append({k: (None if isinstance(v, float) and v != v else
                            (int(v) if k in ("product_id", "category_id") and v is not None else v))
                        for k, v in r.items()})
    out = {"product_id": product_id, "method": method, "fallback": fallback_reason is not None,
           "fallback_reason": fallback_reason, "returned": len(records), "recommendations": records}
    out.update(extra)
    return out


def recommend_similar_products(products_df: pd.DataFrame, product_id: int, tfidf_matrix,
                               limit: int = 5, events_df=None) -> dict:
    # TEACH d05: recommend_similar_products
    ids = products_df["product_id"].to_numpy()
    pos = np.where(ids == product_id)[0]
    if len(pos) == 0:
        return envelope(product_id, "fallback", recommend_popular(products_df, events_df, limit),
                        "unknown_product")
    i = int(pos[0])
    if tfidf_matrix[i].nnz == 0:
        return envelope(product_id, "fallback",
                        recommend_popular(products_df, events_df, limit, exclude=[product_id]), "no_text")
    sims = calculate_product_similarity(tfidf_matrix, i)
    df = products_df.assign(_s=np.round(sims, 4))
    df = df[df["product_id"] != product_id]  # target exclusion (ugovor)
    df = df.sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return envelope(product_id, "content", _with_score(df, df["_s"].values))
    # /TEACH
