import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import math

import pandas as pd


def test_precision_recall_hr():
    assert lab.precision_at_k([1, 2, 3, 4, 5], [1, 3], 5) == pytest.approx(0.4)
    assert lab.precision_at_k([1, 2], [1], 5) == pytest.approx(0.5)    # imenilac min(k, len(top))
    assert lab.precision_at_k([1, 1, 2], [1], 3) == pytest.approx(0.5)  # duplikati jednom
    assert lab.recall_at_k([1, 2, 3], [1, 9], 3) == pytest.approx(0.5)
    assert lab.recall_at_k([1], [], 3) == 0.0 and lab.precision_at_k([], [1], 3) == 0.0
    assert lab.hit_rate_at_k([5, 6, 1], [1], 3) == 1.0 and lab.hit_rate_at_k([5, 6, 1], [1], 2) == 0.0
    for f in (lab.precision_at_k, lab.recall_at_k, lab.hit_rate_at_k, lab.ndcg_at_k):
        with pytest.raises(ValueError):
            f([1], [1], 0)


def test_ndcg():
    assert lab.ndcg_at_k([1, 2], [1], 2) == pytest.approx(1.0)
    assert lab.ndcg_at_k([2, 1], [1], 2) == pytest.approx(1 / math.log2(3))
    assert lab.ndcg_at_k([], [1], 3) == 0.0


def test_coverage_and_split():
    assert lab.catalog_coverage([1, 1, 2], 4) == 0.5
    with pytest.raises(ValueError):
        lab.catalog_coverage([1], 0)
    df = pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-03", "2026-01-02"], "x": [1, 2, 3]})
    tr, te = lab.temporal_split(df, "2026-01-02")
    assert list(tr["x"]) == [1] and list(te["x"]) == [2, 3]
