"""Day 10 — SemanticService (GET /search/semantic, GET /recommendations/semantic/{product_id})."""
from __future__ import annotations

import pandas as pd

from app.data.paths import day_data
from app.recommenders.content import _with_score, build_tfidf_matrix, envelope, recommend_popular
from app.recommenders.embeddings import (brute_force_nearest, keyword_search, load_store, make_embedder,
                                         save_store)
from app.services.store import load_products_text


class SemanticService:
    def __init__(self, products=None, store_path=None, embedder: str = "auto"):
        self.products = products if products is not None else load_products_text()
        self.store_path = store_path or day_data(10, "embeddings.npz")
        self.kind = embedder
        self._store = None; self._embedder = None

    def _load(self):
        if self._store is None:
            if self.store_path.exists():
                self._store = load_store(self.store_path)
                self._embedder = make_embedder("auto", self._store["embedder_name"])
                if self._embedder.name != self._store["embedder_name"]:  # isti prostor ili ništa
                    self._store = None
            if self._store is None:
                self._embedder = make_embedder(self.kind)
                m = self._embedder.encode(self.products["product_text"].fillna(""))
                self._store = {"matrix": m, "product_ids": [int(x) for x in self.products["product_id"]],
                               "embedder_name": self._embedder.name, "embedder_params": self._embedder.params}
        return self._store

    def store_info(self) -> dict:
        s = self._load()
        return {"n_products": len(s["product_ids"]), "dim": int(s["matrix"].shape[1]),
                "embedder": s["embedder_name"]}

    def _rows(self, hits):
        s = self._store
        ids = [s["product_ids"][i] for i, _ in hits]
        df = self.products.set_index("product_id").loc[ids].reset_index()
        return _with_score(df, [round(sc, 4) for _, sc in hits])

    def semantic_search(self, q: str, limit: int = 5) -> dict:
        s = self._load()
        if not q or not q.strip():
            env = envelope(None, "fallback", recommend_popular(self.products, limit=limit), "empty_query")
        else:
            qv = self._embedder.encode([q])[0]
            env = envelope(None, "semantic", self._rows(brute_force_nearest(s["matrix"], qv, limit)))
        env["results"] = env.pop("recommendations"); env["query"] = q
        env["embedder"] = s["embedder_name"]; env["store"] = self.store_info()
        return env

    def recommendations_for_product(self, product_id: int, limit: int = 5) -> dict:
        s = self._load()
        if product_id not in s["product_ids"]:
            return envelope(product_id, "fallback", recommend_popular(self.products, limit=limit), "no_embedding")
        i = s["product_ids"].index(product_id)
        return envelope(product_id, "semantic",
                        self._rows(brute_force_nearest(s["matrix"], s["matrix"][i], limit, exclude_index=i)))

    def build_comparison(self, queries, k: int = 3) -> list:
        from sklearn.metrics.pairwise import cosine_similarity
        from app.services.recommender import TFIDF_KWARGS
        tf, vec = build_tfidf_matrix(self.products, **TFIDF_KWARGS)
        rows = []
        for q in queries:
            for r, h in enumerate(keyword_search(self.products, q, k), 1):
                rows.append({"query": q, "method": "keyword", "rank": r, **h})
            sims = cosine_similarity(vec.transform([q]), tf).ravel()
            order = sorted(range(len(sims)), key=lambda i: (-sims[i], i))
            order = [i for i in order if sims[i] > 0][:k]   # 0-skor nije pogodak
            for r, i in enumerate(order, 1):
                p = self.products.iloc[i]
                rows.append({"query": q, "method": "tfidf", "rank": r, "product_id": int(p.product_id),
                             "name": p["name"], "category_id": int(p.category_id), "score": round(float(sims[i]), 4)})
            for r, rec in enumerate(self.semantic_search(q, k)["results"], 1):
                rows.append({"query": q, "method": "embedding", "rank": r,
                             **{c: rec[c] for c in ("product_id", "name", "category_id", "score")}})
        return rows

    def comparison(self) -> dict:
        p = day_data(10, "comparison.csv")
        if not p.exists():
            raise FileNotFoundError(f"{p} ne postoji — pokreni python -m app.data.generate_embeddings")
        return {"comparison": pd.read_csv(p).to_dict("records")}

    def save(self, path=None):
        s = self._load()
        save_store(path or self.store_path, s["matrix"], s["product_ids"], self._embedder)
