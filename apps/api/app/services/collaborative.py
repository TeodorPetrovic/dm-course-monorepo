"""Day 6 — CollaborativeRecommenderService (lazy matrica + sličnost)."""
from __future__ import annotations

import pandas as pd

from app.data.paths import day_data
from app.recommenders.collaborative import (InteractionMatrix, build_interaction_matrix,
                                            calculate_item_similarity, compare_heuristic_vs_cf,
                                            recommend_from_item_similarity,
                                            recommend_session_cooccurrence,
                                            weight_sensitivity_experiment)
from app.services.store import EmptyStoreError, get_store, load_products_text


class CollaborativeRecommenderService:
    def __init__(self, products=None, events=None):
        self.products = products if products is not None else load_products_text()
        self._events = events
        self._inter = None; self._sim = None

    @property
    def events(self):
        if self._events is None:
            self._events = get_store().events_dataframe()
        return self._events

    def _interaction(self) -> InteractionMatrix:
        if self._inter is None:
            p = day_data(6, "interactions.csv")
            if p.exists():
                self._inter = InteractionMatrix.from_long_csv(p, products=self.products["product_id"])
            else:
                if len(self.events) == 0:
                    raise EmptyStoreError("empty_store")
                self._inter = build_interaction_matrix(self.events, products=self.products["product_id"])
        return self._inter

    def _similarity(self):
        if self._sim is None:
            self._sim = calculate_item_similarity(self._interaction())
        return self._sim

    @property
    def matrix_stats(self) -> dict:
        m = self._interaction().matrix
        rows_multi = int(((m > 0).sum(axis=1) >= 2).sum())
        return {"sessions": m.shape[0], "products": m.shape[1], "nnz": int(m.nnz),
                "density": round(m.nnz / (m.shape[0] * m.shape[1]), 6) if m.shape[0] else 0.0,
                "sessions_with_2plus": rows_multi}

    def collaborative_recommendations(self, product_id: int, limit: int = 5) -> dict:
        return recommend_from_item_similarity(self.products, product_id, self._interaction(),
                                              self._similarity(), limit)

    def heuristic_recommendations(self, product_id: int, limit: int = 5) -> dict:
        return recommend_session_cooccurrence(self.products, self.events, product_id, limit)

    def collaborative_comparison(self, product_id: int, limit: int = 5) -> dict:
        return compare_heuristic_vs_cf(self.products, self.events, self._interaction(), product_id,
                                       self._similarity(), limit)

    def weight_sensitivity(self, product_id: int, limit: int = 5) -> dict:
        return weight_sensitivity_experiment(self.products, self.events, product_id, limit=limit)
