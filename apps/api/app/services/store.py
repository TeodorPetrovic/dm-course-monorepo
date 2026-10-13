"""Deljeni pristup podacima za servise (lazy, keširano, resetabilno u testovima)."""
from __future__ import annotations

import os
import threading
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.data.events import EventStore
from app.data.paths import dataset_path, day_data

_lock = threading.Lock()
_store = None


class EmptyStoreError(RuntimeError):
    """Nema podataka (prazan store / nedostaje fajl) -> API 503."""


def live_events_path():
    p = os.environ.get("DM_LIVE_EVENTS")
    return Path(p) if p else None


def get_store() -> EventStore:
    global _store
    with _lock:
        if _store is None:
            try:
                _store = EventStore.load_seeded(live_path=live_events_path())
            except FileNotFoundError:
                _store = EventStore(live_path=live_events_path())
        return _store


def set_store(store) -> None:
    global _store
    with _lock:
        _store = store
    load_orders.cache_clear(); load_products.cache_clear(); load_products_text.cache_clear()


def require_events(include_live: bool = True) -> pd.DataFrame:
    """Svi događaji (seed + živi). ``include_live=False`` -> samo seeded snapshot: batch trening
    (Day 2–4) ne sme da zavisi od živih događaja sa današnjim timestamp-om (pomerili bi referencu)."""
    s = get_store()
    if len(s) == 0:
        raise EmptyStoreError("empty_store")
    if not include_live and getattr(s, "n_seed", None) and s.n_seed < len(s):
        return s.snapshot_dataframe()
    return s.events_dataframe()


@lru_cache(maxsize=1)
def load_orders() -> pd.DataFrame:
    p = dataset_path("orders.csv")
    return pd.read_csv(p) if p.exists() else pd.DataFrame(columns=["order_id", "user_id", "user_session", "product_id", "quantity", "unit_price", "total_price", "status", "timestamp", "event_id"])


@lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    p = dataset_path("products.csv")
    return pd.read_csv(p) if p.exists() else pd.DataFrame(columns=["product_id", "category_id", "name", "price"])


@lru_cache(maxsize=1)
def load_products_text() -> pd.DataFrame:
    p = day_data(5, "products_text.csv")
    if not p.exists():
        raise EmptyStoreError("missing products_text.csv")
    return pd.read_csv(p)
