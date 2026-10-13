import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

EV = pd.DataFrame({"user_id": [1, 1, 2, 3], "user_session": ["a", "a", "b", "c"],
                   "event_type": ["product_view", "purchase", "product_view", "search"],
                   "timestamp": ["2026-01-01", "2026-01-05", "2026-01-08", "2026-01-02"]})
OD = pd.DataFrame({"user_id": [1], "timestamp": ["2026-01-05"], "total_price": [100.0]})


def test_rfm_definitions():
    r = lab.calculate_rfm(EV, OD).set_index("user_id")
    assert r.loc[1, "recency_days"] == 3 and r.loc[1, "frequency"] == 1 and r.loc[1, "monetary"] == 100.0
    assert r.loc[2, "frequency"] == 0 and r.loc[2, "monetary"] == 0.0 and r.loc[2, "recency_days"] == 0
    assert r.loc[3, "recency_days"] == 6
    assert not r.isna().any().any()
    assert list(lab.calculate_rfm(EV.iloc[0:0], OD.iloc[0:0]).columns) == ["user_id", "recency_days",
                                                                           "frequency", "monetary"]


def test_scaler_transform_only():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [0.0, 0.0, 6.0]})
    s, sc = lab.scale_customer_features(df, ["a", "b"])
    assert abs(s["a"].mean()) < 1e-9
    one, sc2 = lab.scale_customer_features(pd.DataFrame({"a": [2.0], "b": [0.0]}), ["a", "b"], scaler=sc)
    assert sc2 is sc and one.iloc[0]["a"] == pytest.approx(0.0)
    with pytest.raises(ValueError):
        lab.scale_customer_features(df, ["zzz"])


def test_assign_segment_fallbacks():
    X = np.array([[0.0, 0.0], [0.1, 0.0], [10.0, 10.0], [10.1, 10.0]])
    km = KMeans(n_clusters=2, n_init=10, random_state=42).fit(X)
    lab_ = lab.assign_segment(km, pd.Series([10.0, 10.0]))
    assert lab_ == f"segment_{km.predict([[10.0, 10.0]])[0]}"
    assert lab.assign_segment(km, None) == "unsegmented"
    with pytest.raises(ValueError):
        lab.assign_segment(None, pd.Series([1.0, 1.0]))
