import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))


def test_normalize():
    assert lab.normalize_scores([2, 4]) == [0.5, 1.0]
    assert lab.normalize_scores([0, 0]) == [0.0, 0.0]
    assert lab.normalize_scores([3, 3]) == [1.0, 1.0]
    assert lab.normalize_scores([]) == []


def test_merge_and_rank():
    m = lab.merge_candidates({"a": [{"product_id": 1, "score": 10}, {"product_id": 2, "score": 5}],
                              "b": [{"product_id": 2, "score": 0.9}]}, {"a": 1, "b": 1})
    by = {c["product_id"]: c for c in m}
    assert by[2]["sources"] == ["a", "b"] and by[2]["score"] == pytest.approx(0.75)
    assert by[1]["score"] == pytest.approx(0.5)
    assert [c["product_id"] for c in lab.rank_candidates(m)] == [2, 1]
    assert lab.merge_candidates({}, {"a": 1}) == []
    with pytest.raises(ValueError):
        lab.merge_candidates({"a": [{"product_id": 1, "score": 1}]}, {"a": 0})
    tie = lab.rank_candidates([{"product_id": 5, "score": 1}, {"product_id": 3, "score": 1}])
    assert [c["product_id"] for c in tie] == [3, 5]


def test_rules_and_diversity():
    r = [{"product_id": i, "score": 1 - i / 10, "category_id": c} for i, c in enumerate([1, 1, 1, 2, 3], 1)]
    res = lab.apply_business_rules(r, {"available_ids": {1, 2, 3, 4}, "exclude_ids": {2}})
    assert [c["product_id"] for c in res["ranked"]] == [1, 3, 4]
    assert {c["product_id"] for c in res["removed"]} == {2, 5}
    assert lab.apply_business_rules([], {}) == {"ranked": [], "removed": []}
    d = lab.diversify_results(r, 4, max_per_category=2)
    assert [c["product_id"] for c in d] == [1, 2, 4, 5]
    assert len(lab.diversify_results(r[:3], 3, max_per_category=1)) == 3   # fill, don't truncate
