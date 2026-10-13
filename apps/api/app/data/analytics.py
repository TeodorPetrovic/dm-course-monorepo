"""Day 1 — analitika (deskriptivna statistika; nema ML-a)."""
from __future__ import annotations

import pandas as pd


def _count(events: pd.DataFrame, product_id: int, etype: str) -> int:
    if len(events) == 0:
        return 0
    pid = pd.to_numeric(events["product_id"], errors="coerce")
    return int(((events["event_type"] == etype) & (pid == int(product_id))).sum())


def get_product_view_count(events: pd.DataFrame, product_id: int) -> int:
    return _count(events, product_id, "product_view")


def get_cart_count(events: pd.DataFrame, product_id: int) -> int:
    return _count(events, product_id, "add_to_cart")


def get_purchase_count(events: pd.DataFrame, product_id: int) -> int:
    return _count(events, product_id, "purchase")


def calculate_funnel_counts(events: pd.DataFrame) -> dict:
    # TEACH d01: calculate_funnel_counts
    if len(events) == 0:
        return {"views": 0, "carts": 0, "purchases": 0, "sessions": 0, "sessions_with_purchase": 0}
    et = events["event_type"]
    return {
        "views": int((et == "product_view").sum()),
        "carts": int((et == "add_to_cart").sum()),
        "purchases": int((et == "purchase").sum()),
        "sessions": int(events["user_session"].nunique()),
        "sessions_with_purchase": int(events.loc[et == "purchase", "user_session"].nunique()),
    }
    # /TEACH


def calculate_conversion_rate(events: pd.DataFrame) -> float:
    """Sesije sa kupovinom / sve sesije; prazan skup -> 0.0 (nikad None)."""
    # TEACH d01: calculate_conversion_rate
    f = calculate_funnel_counts(events)
    return 0.0 if f["sessions"] == 0 else f["sessions_with_purchase"] / f["sessions"]
    # /TEACH


METRIC_EVENT = {"view": "product_view", "cart": "add_to_cart", "purchase": "purchase"}


def share_by_category(events: pd.DataFrame, products: pd.DataFrame, metric: str = "view") -> pd.DataFrame:
    # TEACH d01+: share_by_category
    if metric not in METRIC_EVENT:
        raise ValueError(f"metric mora biti jedan od {sorted(METRIC_EVENT)}")
    ev = events[events["event_type"] == METRIC_EVENT[metric]]
    pid = pd.to_numeric(ev["product_id"], errors="coerce").dropna().astype(int)
    cat = pid.map(products.set_index("product_id")["category_id"]).dropna().astype(int)
    counts = cat.value_counts().rename_axis("category_id").reset_index(name="count")
    counts = counts.sort_values(["count", "category_id"], ascending=[False, True]).reset_index(drop=True)
    total = counts["count"].sum()
    counts["share"] = (counts["count"] / total).round(4) if total else 0.0
    return counts
    # /TEACH


def share_by_product(events: pd.DataFrame, metric: str = "view") -> pd.DataFrame:
    if metric not in METRIC_EVENT:
        raise ValueError(f"metric mora biti jedan od {sorted(METRIC_EVENT)}")
    ev = events[events["event_type"] == METRIC_EVENT[metric]]
    pid = pd.to_numeric(ev["product_id"], errors="coerce").dropna().astype(int)
    counts = pid.value_counts().rename_axis("product_id").reset_index(name="count")
    total = counts["count"].sum()
    counts["share"] = (counts["count"] / total).round(4) if total else 0.0
    return counts


def average_order_value(orders: pd.DataFrame) -> float:
    # TEACH d01: average_order_value
    if orders is None or len(orders) == 0:
        return 0.0
    # orders.csv ima jedan red po STAVCI; AOV = prihod / broj različitih porudžbina
    n = orders["order_id"].nunique() if "order_id" in orders.columns else len(orders)
    return round(float(orders["total_price"].sum()) / n, 2) if n else 0.0
    # /TEACH


def get_search_events(store) -> pd.DataFrame:
    df = store.events
    return df[df["event_type"] == "search"].sort_values("timestamp", kind="stable")


def searches_per_day(events: pd.DataFrame) -> dict:
    s = events[events["event_type"] == "search"]
    if len(s) == 0:
        return {}
    return s["timestamp"].astype(str).str[:10].value_counts().sort_index().to_dict()
