"""Referentno rešenje Day 5 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from starter import RECOMMENDATION_COLUMNS  # noqa: F401


def _out(df, score):
    df = df.copy(); df["score"] = list(score)
    for c in RECOMMENDATION_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[RECOMMENDATION_COLUMNS].reset_index(drop=True)


def recommend_popular(products_df, limit=5):
    d = products_df.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def recommend_same_category(products_df, product_id, limit=5):
    hit = products_df[products_df["product_id"] == product_id]
    if hit.empty:
        raise ValueError(f"nepoznat proizvod {product_id}")
    d = products_df[(products_df["category_id"] == hit.iloc[0]["category_id"]) & (products_df["product_id"] != product_id)]
    d = d.sort_values(["popularity", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["popularity"])


def prepare_product_text(products_df, include_category=True):
    t = products_df["name"].fillna("") + " " + products_df["description"].fillna("")
    if include_category:
        t = products_df["category_name"].fillna("") + " " + t
    return pd.Series(t.str.strip().values, index=products_df["product_id"].values)


def build_tfidf_matrix(products_df, text_column="product_text"):
    texts = products_df[text_column] if text_column in products_df.columns else prepare_product_text(products_df)
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    return vec.fit_transform(list(texts.fillna(""))), vec


def calculate_product_similarity(tfidf_matrix, index):
    return cosine_similarity(tfidf_matrix[index:index + 1], tfidf_matrix).flatten()


def recommend_similar_products(products_df, product_id, tfidf_matrix, limit=5):
    pos = np.where(products_df["product_id"].to_numpy() == product_id)[0]
    if len(pos) == 0:
        return recommend_popular(products_df, limit)
    d = products_df.assign(_s=calculate_product_similarity(tfidf_matrix, int(pos[0])))
    d = d[d["product_id"] != product_id].sort_values(["_s", "product_id"], ascending=[False, True]).head(limit)
    return _out(d, d["_s"])
