"""Day 8 — HybridRecommenderService (GET /recommendations/user/{user_id})."""
from __future__ import annotations

import pandas as pd

from app.recommenders.content import envelope, recommend_popular
from app.recommenders.evaluation import evaluate_recommender, temporal_split
from app.recommenders.hybrid import MERGE_WEIGHTS, HybridModels, user_test_cases
from app.services.store import get_store, load_products_text

DEMO_USER_IDS = [395, 1465, 409, 1182, 2360]  # 5 najaktivnijih korisnika (seed 42)


class HybridRecommenderService:
    merge_weights = MERGE_WEIGHTS

    def __init__(self, products=None, events=None, split_ratio=0.8, max_per_category=2):
        self.products = products if products is not None else load_products_text()
        self.events = events if events is not None else get_store().events_dataframe()
        self.split_ratio = split_ratio; self.max_per_category = max_per_category
        self.train, self.test, self.split_time = temporal_split(self.events, split_ratio)
        self._models = None

    @property
    def models(self) -> HybridModels:
        if self._models is None:
            self._models = HybridModels(self.products, self.train)
        return self._models

    def recommend_for_user(self, user_id: int, limit: int = 5, include_pipeline: bool = False) -> dict:
        m = self.models
        res = m.recommend(user_id, limit, max_per_category=self.max_per_category)
        if res is None:
            env = envelope(None, "fallback", recommend_popular(self.products, limit=limit), "unknown_user")
            env.update(user_id=user_id, rules=None, max_per_category=self.max_per_category)
            return env
        price = dict(zip(self.products["product_id"], self.products["price"]))
        recs = [{"product_id": c["product_id"], "name": c.get("name"), "category_id": c.get("category_id"),
                 "price": float(price.get(c["product_id"])) if c["product_id"] in price else None,
                 "score": round(c["score"], 6), "sources": c["sources"]} for c in res["final"]]
        out = {"user_id": user_id, "method": "hybrid", "fallback": False, "fallback_reason": None,
               "returned": len(recs), "recommendations": recs,
               "n_signal_products": res["n_signal"], "n_user_events": int(m.user_events.get(user_id, 0)),
               "candidate_counts": {s: len(v) for s, v in res["candidates"].items()},
               "n_candidates": sum(len(v) for v in res["candidates"].values()),
               "merge_weights": dict(MERGE_WEIGHTS),
               "rules": ["exclude_purchased", "availability"], "n_available": len(m.available_ids),
               "n_after_rules": len(res["ruled"]["ranked"]), "max_per_category": self.max_per_category}
        if include_pipeline:
            out["pipeline"] = {"n_candidates_before_merge": sum(len(v) for v in res["candidates"].values()),
                               "n_merged": len(res["merged"]), "n_removed_by_rules": len(res["ruled"]["removed"]),
                               "n_after_rules": len(res["ruled"]["ranked"])}
        return out

    def user_based_comparison(self, k: int = 5, max_test_users=None) -> dict:
        m = self.models
        cases = user_test_cases(self.train, self.test)
        if max_test_users:
            cases = cases[:max_test_users]
        conv = [{"query_product_id": c["user_id"], "target_product_ids": c["target_product_ids"]} for c in cases]
        rows = []
        for name, src in [("hybrid", None), ("popularity", ["popularity"]), ("category", ["category"]),
                          ("content", ["content"]), ("collaborative", ["collaborative"])]:
            def pred(u, kk, src=src):
                r = m.recommend(u, kk, sources=src, max_per_category=self.max_per_category,
                                diversify=src is None)
                return [c["product_id"] for c in r["final"]] if r else []
            rows.append({"method": name, **evaluate_recommender(pred, conv, k, len(self.products))})
        return {"k": k, "n_test_users": len(cases), "split_time": str(self.split_time), "comparison": rows}
