import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import numpy as np
import pandas as pd

EV = pd.DataFrame({"user_session": ["s1", "s1", "s1", "s2", "s2", "s3"],
                   "product_id": [1, 1, 2, 1, 3, 2],
                   "event_type": ["product_view", "add_to_cart", "product_view", "purchase", "product_view", "search"]})
PR = pd.DataFrame({"product_id": [1, 2, 3, 4], "name": list("abcd"), "category_id": [1, 1, 2, 2],
                   "popularity": [5.0, 9.0, 1.0, 9.0]})


def test_matrix_max_aggregation():
    m, s, p = lab.build_interaction_matrix(EV)
    assert s == ["s1", "s2"] and p == [1, 2, 3]          # search bez težine je izbačen
    d = m.toarray()
    assert d[0, 0] == 3.0                                 # max(1, 3), ne 4
    assert d[1, 0] == 5.0 and d[1, 2] == 1.0
    assert hasattr(m, "tocsr")


def test_similarity_dense_square():
    m, _, p = lab.build_interaction_matrix(EV)
    sim = lab.calculate_item_similarity(m)
    assert isinstance(sim, np.ndarray) and sim.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)


def test_recommend_similar_and_cold_start():
    m, _, p = lab.build_interaction_matrix(EV)
    r = lab.recommend_similar(PR, 1, m, p, 5)
    assert 1 not in set(r["product_id"]) and list(r.columns) == lab.RECOMMENDATION_COLUMNS
    cold = lab.recommend_similar(PR, 99, m, p, 2)
    assert list(cold["product_id"]) == [2, 4]            # popularity, tie-break po product_id
