"""Referentno rešenje Day 1 lab-a (prvo probaj sam!)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import starter as _s
from starter import DEFAULT_SOURCE, EVENT_COLUMNS, PRODUCT_EVENT_TYPES, VALID_EVENT_TYPES  # noqa: F401


def create_event(event_type, user_id=None, product_id=None, user_session=None, category_id=None,
                 quantity=1, price=None, source=None, timestamp=None) -> dict:
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"nepoznat event_type: {event_type!r}")
    if event_type in PRODUCT_EVENT_TYPES and product_id is None:
        raise ValueError(f"{event_type} zahteva product_id")
    if quantity is None or int(quantity) < 1:
        raise ValueError("quantity mora biti >= 1")
    if timestamp is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts = str(timestamp).replace("T", " ")[:19]
    return {"event_type": event_type, "user_id": user_id, "user_session": user_session,
            "product_id": product_id, "category_id": category_id, "price": price, "quantity": int(quantity),
            "source": source or DEFAULT_SOURCE[event_type], "timestamp": ts,
            "recommendation_source": None, "recommendation_position": None}


class EventStore(_s.EventStore):
    def save_event(self, event: dict) -> dict:
        saved = {**{c: None for c in EVENT_COLUMNS}, **event, "event_id": self._next_id}
        self._next_id += 1
        row = pd.DataFrame([saved], columns=EVENT_COLUMNS)
        self.events = row if len(self.events) == 0 else pd.concat([self.events, row], ignore_index=True)
        return saved

    def _sorted(self, mask):
        return self.events[mask].sort_values("timestamp", kind="stable").reset_index(drop=True)

    def get_session_events(self, session_id):
        return self._sorted(self.events["user_session"] == session_id)

    def get_product_events(self, product_id):
        return self.events[pd.to_numeric(self.events["product_id"], errors="coerce") == product_id].reset_index(drop=True)

    def get_customer_events(self, user_id):
        return self._sorted(pd.to_numeric(self.events["user_id"], errors="coerce") == user_id)


def load_seeded() -> EventStore:
    return EventStore.from_csv(Path(__file__).resolve().parents[1] / "data" / "events.csv")


def calculate_funnel_counts(events_df):
    t = events_df["event_type"] if len(events_df) else pd.Series(dtype=str)
    return {"views": int((t == "product_view").sum()), "carts": int((t == "add_to_cart").sum()),
            "purchases": int((t == "purchase").sum()),
            "sessions": int(events_df["user_session"].nunique()) if len(events_df) else 0,
            "sessions_with_purchase": int(events_df.loc[t == "purchase", "user_session"].nunique()) if len(events_df) else 0}


def calculate_conversion_rate(events_df):
    f = calculate_funnel_counts(events_df)
    return f["sessions_with_purchase"] / f["sessions"] if f["sessions"] else 0.0


def average_order_value(orders_df):
    if orders_df is None or len(orders_df) == 0:
        return 0.0
    # jedan red = jedna stavka; stavke iste porudžbine dele order_id
    total = pd.to_numeric(orders_df["total_price"], errors="coerce").sum()
    return float(total / orders_df["order_id"].nunique())


def get_search_events(store):
    return store.events[store.events["event_type"] == "search"].reset_index(drop=True)
