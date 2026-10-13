import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import numpy as np


def test_normalize_zero_row():
    n = lab.normalize(np.array([[3.0, 4.0], [0.0, 0.0]]))
    assert np.allclose(n[0], [0.6, 0.8]) and np.allclose(n[1], [0, 0]) and not np.isnan(n).any()


def test_cosine_normalizes_both():
    m = np.array([[10.0, 0.0], [0.0, 0.1], [1.0, 1.0]])
    s = lab.cosine_similarity(np.array([5.0, 0.0]), m)
    assert np.allclose(s, [1.0, 0.0, 1 / np.sqrt(2)])


def test_nearest_and_search():
    m = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]])
    r = lab.brute_force_nearest(m, m[0], k=2, exclude_index=0)
    assert [i for i, _ in r] == [1, 2]
    prods = [{"product_id": 10, "name": "a"}, {"product_id": 11, "name": "b"}, {"product_id": 12, "name": "c"}]
    hits = lab.semantic_search_lite(prods, m, np.array([0.0, 1.0]), k=1)
    assert hits[0]["product_id"] == 12 and hits[0]["score"] == pytest.approx(1.0)
