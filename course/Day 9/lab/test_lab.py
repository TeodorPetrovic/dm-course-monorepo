import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))


def test_recency():
    assert lab.recency_weights(3, 0.5) == [0.25, 0.5, 1.0]
    assert lab.recency_weights(0, 0.8) == []


def test_interest():
    ev = [{"event_type": "product_view", "product_id": 1}, {"event_type": "search", "product_id": None},
          {"event_type": "add_to_cart", "product_id": 2}]
    pi = lab.recent_product_interest(ev, decay=0.5)
    assert pi == {1: pytest.approx(0.5), 2: pytest.approx(3.0)}
    ci = lab.recent_category_interest(ev, {1: 10, 2: 10}, decay=0.5)
    assert ci == {10: pytest.approx(3.5)}
    assert lab.recent_product_interest([{"event_type": "search", "product_id": None}]) == {}


def test_ctr():
    assert lab.recommendation_ctr([1, 2, 3, 4], [1]) == 0.25
    assert lab.recommendation_ctr([], []) == 0.0
    imps = [{"algorithm": "popular"}] * 4 + [{"algorithm": "personalized"}] * 2
    rows = lab.ctr_by_algorithm(imps, [{"algorithm": "personalized"}])
    assert [r["algorithm"] for r in rows] == ["personalized", "popular"]   # rastuće po imenu
    assert rows[0]["ctr"] == 0.5 and rows[1]["ctr"] == 0.0
