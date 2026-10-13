"""Day 7 — RecommendationEvaluationService: lazy + keširan comparison report."""
from __future__ import annotations

from app.recommenders.evaluation import build_comparison_report
from app.services.store import require_events, load_products_text


class RecommendationEvaluationService:
    def __init__(self):
        self._cache: dict = {}

    def comparison_report(self, k: int = 5, split_ratio: float = 0.8) -> dict:
        key = (k, split_ratio)
        if key not in self._cache:
            r = build_comparison_report(require_events(), load_products_text(), k, split_ratio)
            r.pop("test_cases", None)
            self._cache[key] = r
        return self._cache[key]
