"""Day 10 — dense embeddings (sentence-transformers ili offline HashEmbedder) + brute-force NN."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
STOPWORDS = {"a", "an", "the", "to", "and", "or", "for", "with", "of", "in", "on", "before", "something",
             "is", "it", "my", "i"}


def normalize(v):
    v = np.asarray(v, dtype=float)
    if v.ndim == 1:
        n = np.linalg.norm(v)
        return v / n if n > 0 else v
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return np.divide(v, n, out=np.zeros_like(v), where=n > 0)


def brute_force_nearest(matrix, query_vec, k=3, exclude_index=None):
    s = normalize(matrix) @ normalize(query_vec)
    order = sorted(range(len(s)), key=lambda i: (-s[i], i))
    return [(i, float(s[i])) for i in order if i != exclude_index][:k]


class HashEmbedder:
    """Deterministički offline fallback: hashing bag-of-words + seeded random projection."""

    def __init__(self, dim: int = 64, seed: int = 42, n_features: int = 2 ** 12):
        from sklearn.feature_extraction.text import HashingVectorizer
        self.dim, self.seed = dim, seed
        self.vec = HashingVectorizer(n_features=n_features, alternate_sign=False, norm="l2",
                                     stop_words="english", ngram_range=(1, 1))
        self.proj = np.random.default_rng(seed).normal(size=(n_features, dim)) / np.sqrt(dim)

    @property
    def name(self):
        return "hash"

    @property
    def params(self):
        return {"embedding_dim": self.dim, "seed": self.seed}

    def encode(self, texts):
        return normalize(np.asarray(self.vec.transform(list(texts)) @ self.proj))

    encode_texts = encode  # ime iz lekcije: encode_texts(texts) -> (n, dim)

    def descriptor(self) -> dict:
        return {"name": self.name, "params": self.params}


class STEmbedder:
    def __init__(self, model_name: str = ST_MODEL):
        from sentence_transformers import SentenceTransformer  # opciona zavisnost
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @property
    def name(self):
        return f"sentence-transformers:{self.model_name}"

    @property
    def params(self):
        return {}

    def encode(self, texts):
        return normalize(self.model.encode(list(texts), show_progress_bar=False))

    encode_texts = encode  # ime iz lekcije: encode_texts(texts) -> (n, dim)

    def descriptor(self) -> dict:
        return {"name": self.name, "params": self.params}


def make_embedder(kind: str = "auto", name: str | None = None):
    if kind == "hash" or (name or "").startswith("hash"):
        return HashEmbedder()
    try:
        model = (name or "").split(":", 1)[1] if (name or "").startswith("sentence-transformers:") else ST_MODEL
        return STEmbedder(model)
    except Exception:
        if kind == "st":
            raise
        return HashEmbedder()


def build_embedder(descriptor: dict):
    """Rekonstruiše embedder iz descriptor-a (``{"name": ..., "params": ...}``) — isti prostor kao store."""
    name = descriptor.get("name") or descriptor.get("embedder_name") or ""
    if name.startswith("hash"):
        prm = descriptor.get("params") or descriptor.get("embedder_params") or {}
        return HashEmbedder(dim=prm.get("embedding_dim", 64), seed=prm.get("seed", 42))
    return make_embedder("st", name)


def save_store(path: Path, matrix, product_ids, embedder):
    np.savez(path, matrix=matrix.astype(np.float32), product_ids=np.asarray(product_ids, dtype=np.int64),
             embedder_name=np.array(embedder.name), embedder_params=np.array(json.dumps(embedder.params)))


def load_store(path: Path) -> dict:
    z = np.load(path, allow_pickle=False)
    return {"matrix": z["matrix"].astype(float), "product_ids": [int(x) for x in z["product_ids"]],
            "embedder_name": str(z["embedder_name"]), "embedder_params": json.loads(str(z["embedder_params"]))}


def tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", str(text).lower()) if t not in STOPWORDS}


def keyword_search(products: pd.DataFrame, query: str, k: int = 3) -> list:
    q = tokens(query)
    rows = []
    pop = products["popularity"] if "popularity" in products.columns else [0.0] * len(products)
    for pid, name, cat, text, pp in zip(products["product_id"], products["name"], products["category_id"],
                                        products["product_text"], pop):
        s = len(q & tokens(text))
        if s > 0:  # tie-break: popularnost opadajuće, pa product_id
            rows.append((-s, -float(pp), int(pid), name, int(cat)))
    rows.sort()
    return [{"product_id": p, "name": n, "category_id": c, "score": float(-s)} for s, _pp, p, n, c in rows[:k]]


# imena koja Day 10 lab README pominje
def cosine_similarity_bruteforce(query_vec, matrix):
    return normalize(matrix) @ normalize(query_vec)


def find_nearest_products(matrix, query_vec, k=3, exclude_index=None):
    return brute_force_nearest(matrix, query_vec, k, exclude_index)


l2_normalize = normalize


def generate_product_embedding(embedder, text: str):
    return embedder.encode([text or ""])[0]


def generate_all_embeddings(embedder, products: pd.DataFrame, text_column: str = "product_text"):
    return embedder.encode(products[text_column].fillna(""))


def save_embeddings(path, matrix, product_ids, embedder):
    save_store(Path(path), matrix, product_ids, embedder)


def load_embeddings(path) -> dict:
    return load_store(Path(path))


def semantic_search(matrix, product_ids, query_vec, k: int = 5) -> list:
    return [(product_ids[i], s) for i, s in brute_force_nearest(matrix, query_vec, k)]
