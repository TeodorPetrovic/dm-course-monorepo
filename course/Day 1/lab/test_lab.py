import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def test_create_event_validation():
    e = lab.create_event("product_view", user_id=1, product_id=5, timestamp="2026-01-05T10:00:00.123Z")
    assert e["timestamp"] == "2026-01-05 10:00:00" and e["source"] == "product_page"
    with pytest.raises(ValueError):
        lab.create_event("bogus")
    with pytest.raises(ValueError):
        lab.create_event("add_to_cart", user_id=1)
    with pytest.raises(ValueError):
        lab.create_event("purchase", product_id=1, quantity=0)
    assert len(lab.create_event("search")["timestamp"]) == 19


def test_store_roundtrip():
    s = lab.EventStore()
    a = s.save_event(lab.create_event("product_view", user_id=1, product_id=2, user_session="s1",
                                      timestamp="2026-01-02 00:00:00"))
    b = s.save_event(lab.create_event("product_view", user_id=1, product_id=3, user_session="s1",
                                      timestamp="2026-01-01 00:00:00"))
    assert (a["event_id"], b["event_id"]) == (1, 2)
    assert list(s.get_session_events("s1")["product_id"]) == [3, 2]
    assert len(s.get_product_events(2)) == 1 and len(s.get_customer_events(1)) == 2


def test_funnel_on_seed():
    ev = pd.read_csv(DATA / "events.csv")
    f = lab.calculate_funnel_counts(ev)
    assert f == {"views": 94220, "carts": 3159, "purchases": 1045, "sessions": 15361,
                 "sessions_with_purchase": 893}
    assert round(lab.calculate_conversion_rate(ev), 4) == round(893 / 15361, 4)
    assert lab.calculate_conversion_rate(ev.iloc[0:0]) == 0.0


def test_exercises():
    o = pd.read_csv(DATA / "orders.csv")
    assert lab.average_order_value(o) == pytest.approx(o["total_price"].sum() / o["order_id"].nunique())
    assert lab.average_order_value(o.iloc[0:0]) == 0.0
    s = lab.load_seeded()
    assert (lab.get_search_events(s)["event_type"] == "search").all()
