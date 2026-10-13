import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import pandas as pd

CAMP = {"target_segments": ["segment_1"], "eligible_buckets": [], "min_probability": 0.3, "min_monetary": 0,
        "cost_per_contact": 1.0, "max_contacts": 2}
PROF = pd.DataFrame({"user_id": [3, 1, 2, 4], "probability": [0.9, 0.5, 0.2, 0.9],
                     "segment": ["segment_1", "segment_1", "segment_1", "segment_0"],
                     "rfm_bucket": ["loyal", "champions", "loyal", "dormant"], "monetary": [100.0, 300.0, 50.0, 999.0]})


def test_score_customer():
    s = lab.score_customer(0.5, "segment_1", "loyal", 300.0, CAMP)
    assert s["eligible"] and s["expected_value"] == 149.0 and "očekivana vrednost" in s["reasons"][-1]
    n = lab.score_customer(0.1, "segment_1", "loyal", 300.0, CAMP)
    assert n == {"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": n["reasons"]}


def test_select_and_rank():
    sel = lab.select_target_customers(PROF, CAMP)
    assert list(sel["user_id"]) == [1, 3]
    assert lab.select_target_customers(PROF.iloc[0:0], CAMP).empty
    r = lab.rank_target_customers(sel, CAMP, limit=10)
    assert list(r["user_id"]) == [1, 3] and list(r["rank"]) == [1, 2]   # limit klipovan na max_contacts=2
    assert len(lab.rank_target_customers(sel, CAMP, limit=1)) == 1


def test_rule_based_score():
    assert lab.rule_based_score("champions", 10.0) == 4_000_010.0
    assert lab.rule_based_score("loyal", None) == 3_000_000.0
