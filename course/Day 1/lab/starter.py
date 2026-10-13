"""Starter za Day 1 lab.

Implementiraj funkcije/metode označene sa ``raise NotImplementedError``.
Kolone u ``events.csv`` (12): event_id, event_type, user_id, user_session,
product_id, category_id, price, quantity, source, timestamp,
recommendation_source, recommendation_position.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

VALID_EVENT_TYPES = frozenset({
    "product_view", "category_view", "search", "add_to_cart",
    "remove_from_cart", "purchase", "recommendation_impression",
    "recommendation_click",
})

PRODUCT_EVENT_TYPES = frozenset({
    "product_view", "add_to_cart", "remove_from_cart", "purchase",
    "recommendation_click",
})

EVENT_COLUMNS = [
    "event_id", "event_type", "user_id", "user_session", "product_id",
    "category_id", "price", "quantity", "source", "timestamp",
    "recommendation_source", "recommendation_position",
]

DEFAULT_SOURCE = {
    "product_view": "product_page",
    "category_view": "category_page",
    "search": "search_page",
    "add_to_cart": "product_page",
    "remove_from_cart": "cart",
    "purchase": "product_page",
    "recommendation_impression": "recommendation",
    "recommendation_click": "recommendation",
}


def create_event(
    event_type: str,
    user_id: Optional[int] = None,
    product_id: Optional[int] = None,
    user_session: Optional[str] = None,
    category_id: Optional[int] = None,
    quantity: int = 1,
    price: Optional[float] = None,
    source: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Kreira događaj kao dict (bez event_id). TODO: implementirati.

    Zahtevi:
    - nepoznat event_type -> ValueError
    - proizvodni tip bez product_id -> ValueError
    - quantity >= 1
    - timestamp: None -> trenutni UTC "YYYY-MM-DD HH:MM:SS"; string -> skrati
      na 19 karaktera (T -> razmak)
    - source: podrazumevano iz DEFAULT_SOURCE
    """
    raise NotImplementedError("implementiraj create_event")


class EventStore:
    def __init__(self, events: Optional[pd.DataFrame] = None):
        if events is None or len(events) == 0:
            events = pd.DataFrame(columns=EVENT_COLUMNS)
        self.events = events.reindex(columns=EVENT_COLUMNS).reset_index(drop=True)
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        if len(self.events) and self.events["event_id"].notna().any():
            return int(self.events["event_id"].max()) + 1
        return 1

    def save_event(self, event: dict) -> dict:
        """TODO: dodeli event_id, dodaj u self.events, vrati sačuvan dict."""
        raise NotImplementedError("implementiraj save_event")

    def get_session_events(self, session_id: str) -> pd.DataFrame:
        """TODO: događaji sesije, sortirani po timestamp."""
        raise NotImplementedError("implementiraj get_session_events")

    def get_product_events(self, product_id: int) -> pd.DataFrame:
        """TODO: svi događaji za proizvod."""
        raise NotImplementedError("implementiraj get_product_events")

    def get_customer_events(self, user_id: int) -> pd.DataFrame:
        """TODO: svi događaji korisnika, sortirani po timestamp."""
        raise NotImplementedError("implementiraj get_customer_events")

    @classmethod
    def from_csv(cls, path) -> "EventStore":
        return cls(pd.read_csv(path))


def load_seeded() -> EventStore:
    """Učitava ``Day 1/data/events.csv`` (path relativan na ovaj fajl)."""
    default_path = Path(__file__).resolve().parents[1] / "data" / "events.csv"
    return EventStore.from_csv(default_path)


def calculate_funnel_counts(events_df: pd.DataFrame) -> dict:
    """TODO: views/carts/purchases/sessions/sessions_with_purchase."""
    raise NotImplementedError("implementiraj calculate_funnel_counts")


def calculate_conversion_rate(events_df: pd.DataFrame) -> float:
    """TODO: sesije sa kupovinom / sve sesije; prazno -> 0.0."""
    raise NotImplementedError("implementiraj calculate_conversion_rate")


# --- Vežba (nezavisna) ------------------------------------------------------ #
def average_order_value(orders_df: pd.DataFrame) -> float:
    """TODO (vežba): prihod (suma total_price) / broj različitih order_id; prazno -> 0.0."""
    raise NotImplementedError("implementiraj average_order_value")


def get_search_events(store: EventStore) -> pd.DataFrame:
    """TODO (vežba): svi search događaji iz store-a."""
    raise NotImplementedError("implementiraj get_search_events")
