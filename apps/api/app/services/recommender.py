"""Day 5 — RecommenderService: popular / category / content + baseline comparison."""
from __future__ import annotations

from app.recommenders.content import (build_tfidf_matrix, envelope, recommend_popular,
                                      recommend_same_category, recommend_similar_products)
from app.services.store import load_products_text

TFIDF_KWARGS = {"stop_words": "english", "ngram_range": (1, 2), "min_df": 2}


class UnknownProductError(KeyError):
    pass


class RecommenderService:
    def __init__(self, products=None, tfidf_kwargs=None):
        self.products = products if products is not None else load_products_text()
        self.tfidf_kwargs = tfidf_kwargs or TFIDF_KWARGS
        self._matrix = None

    @property
    def matrix(self):
        if self._matrix is None:  # lazy + keš
            self._matrix, self._vec = build_tfidf_matrix(self.products, **self.tfidf_kwargs)
        return self._matrix

    def popular_recommendations(self, limit: int = 5) -> dict:
        return envelope(None, "popular", recommend_popular(self.products, limit=limit))

    def category_recommendations(self, product_id: int, limit: int = 5) -> dict:
        try:
            recs = recommend_same_category(self.products, product_id, limit)
        except ValueError as e:
            raise UnknownProductError(product_id) from e
        return envelope(product_id, "category", recs)

    def content_recommendations(self, product_id: int, limit: int = 5) -> dict:
        return recommend_similar_products(self.products, product_id, self.matrix, limit)

    def baseline_comparison(self, product_id: int, limit: int = 5) -> dict:
        content = self.content_recommendations(product_id, limit)
        cat = self.category_recommendations(product_id, limit)
        pop = self.popular_recommendations(limit)
        ids = lambda e: [r["product_id"] for r in e["recommendations"]]
        c = ids(content)
        return {"product_id": product_id, "content": content, "category": cat, "popular": pop,
                "overlap": {"content_vs_category": [x for x in c if x in set(ids(cat))],
                            "content_vs_popular": [x for x in c if x in set(ids(pop))]}}
