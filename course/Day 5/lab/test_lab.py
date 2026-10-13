import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import pandas as pd

P = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "products_text.csv")


def test_popular_and_category():
    assert list(lab.recommend_popular(P, 5)["product_id"]) == [90, 184, 110, 12, 49]
    assert list(lab.recommend_popular(P, 3).columns) == lab.RECOMMENDATION_COLUMNS
    c = lab.recommend_same_category(P, 1, 5)
    assert 1 not in set(c["product_id"]) and set(P.set_index("product_id").loc[c["product_id"], "category_id"]) == {1}
    with pytest.raises(ValueError):
        lab.recommend_same_category(P, 99999)


def test_text_and_tfidf():
    t = lab.prepare_product_text(P.drop(columns=["product_text"]))
    assert t.loc[1] == "Electronics Smartphone Compact 686 5G smartphone with OLED display, dual camera and fast charging. Compact line, black."
    m, vec = lab.build_tfidf_matrix(P)
    assert m.shape[0] == len(P)
    sims = lab.calculate_product_similarity(m, 0)
    assert len(sims) == len(P) and sims[0] == pytest.approx(1.0)


def test_similar_excludes_target_and_cold_start():
    m, _ = lab.build_tfidf_matrix(P)
    r = lab.recommend_similar_products(P, 1, m, 5)
    assert 1 not in set(r["product_id"]) and r["score"].is_monotonic_decreasing
    cold = lab.recommend_similar_products(P, 99999, m, 5)
    assert list(cold["product_id"]) == [90, 184, 110, 12, 49]
