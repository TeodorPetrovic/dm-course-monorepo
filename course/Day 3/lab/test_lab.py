import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

D1 = Path(__file__).resolve().parents[2] / "Day 1" / "data"


@pytest.fixture(scope="module")
def seed():
    return pd.read_csv(D1 / "events.csv"), pd.read_csv(D1 / "orders.csv")


def test_clean_dataset_matches_lesson(seed):
    ds = lab.build_training_dataset(*seed, window_days=7)
    assert len(ds) == 2579 and int(ds[lab.LABEL_COLUMN].sum()) == 163
    assert list(ds.columns) == ["user_id"] + lab.FEATURE_COLUMNS + [lab.LABEL_COLUMN]


def test_leaky_differs(seed):
    clean = lab.build_training_dataset(*seed, leaky=False).set_index("user_id")
    leaky = lab.build_training_dataset(*seed, leaky=True).set_index("user_id")
    common = clean.index.intersection(leaky.index)
    assert (leaky.loc[common, "frequency"] >= clean.loc[common, "frequency"]).all()
    assert (leaky.loc[common, "frequency"] > clean.loc[common, "frequency"]).any()


def test_split_and_evaluate(seed):
    ds = lab.build_training_dataset(*seed)
    tr, te = lab.split_dataset(ds)
    assert len(te) == 774 and abs(tr[lab.LABEL_COLUMN].mean() - te[lab.LABEL_COLUMN].mean()) < 0.01
    with pytest.raises(ValueError):
        lab.split_dataset(ds.drop(columns=[lab.LABEL_COLUMN]))
    sc = StandardScaler().fit(tr[lab.FEATURE_COLUMNS])
    m = lab.train_conversion_model(sc.transform(tr[lab.FEATURE_COLUMNS]), tr[lab.LABEL_COLUMN])
    ev = lab.evaluate_model(m, sc.transform(te[lab.FEATURE_COLUMNS]), te[lab.LABEL_COLUMN])
    assert ev["n"] == 774 and sum(map(sum, ev["confusion_matrix"])) == 774
    p = lab.predict_conversion_probability(m, sc.transform(te[lab.FEATURE_COLUMNS])[0])
    assert 0 <= p <= 1
    with pytest.raises(ValueError):
        lab.predict_conversion_probability(None, [1.0])
    with pytest.raises(ValueError):
        lab.predict_conversion_probability(m, [])
