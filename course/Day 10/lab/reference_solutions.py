"""Referentno rešenje Day 10 lab-a (brute-force NN, bez ANN biblioteka)."""
from __future__ import annotations

import time

import numpy as np


def normalize(vectors):
    v = np.asarray(vectors, dtype=float)
    if v.ndim == 1:
        n = np.linalg.norm(v)
        return v / n if n > 0 else v.copy()
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return np.divide(v, n, out=np.zeros_like(v), where=n > 0)


def cosine_similarity(query_vec, matrix):
    return normalize(matrix) @ normalize(query_vec)


def brute_force_nearest(matrix, query_vec, k=3, exclude_index=None):
    s = cosine_similarity(query_vec, matrix)
    order = sorted(range(len(s)), key=lambda i: (-s[i], i))
    return [(i, float(s[i])) for i in order if i != exclude_index][:k]


def semantic_search_lite(products, embeddings, query_embedding, k=3):
    return [{"product_id": products[i]["product_id"], "name": products[i]["name"], "score": s}
            for i, s in brute_force_nearest(embeddings, query_embedding, k)]


def time_brute_force(n=252, dim=384, repeats=20, seed=42):
    """Vežba: izmeri brute-force na n proizvoda i linearno ekstrapoliraj na 1_000_000."""
    rng = np.random.default_rng(seed)
    m, q = rng.normal(size=(n, dim)), rng.normal(size=dim)
    t0 = time.perf_counter()
    for _ in range(repeats):
        brute_force_nearest(m, q, 3)
    per = (time.perf_counter() - t0) / repeats
    return {"n": n, "seconds_per_query": per, "extrapolated_1m_seconds": per * 1_000_000 / n}


if __name__ == "__main__":
    print(time_brute_force())
