"""Day 1 — event sloj: šema, kreiranje, čuvanje i upiti nad događajima."""
from __future__ import annotations

import csv
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from app.data.paths import dataset_path

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
    "product_view": "product_page", "category_view": "category_page",
    "search": "search_page", "add_to_cart": "product_page",
    "remove_from_cart": "cart", "purchase": "product_page",
    "recommendation_impression": "recommendation",
    "recommendation_click": "recommendation",
}
EVENT_DTYPES = {"product_id": "Int64", "category_id": "Int64", "user_id": "Int64",
                "recommendation_position": "Int64", "event_id": "Int64", "quantity": "Int64"}


def normalize_timestamp(ts) -> str:
    """``YYYY-MM-DD HH:MM:SS`` bez zone (UTC ako je zona data)."""
    if ts is None:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(ts, datetime):
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    s = str(ts).strip().replace("T", " ")
    if s.endswith("Z") or "+" in s[10:]:
        t = pd.Timestamp(s)
        if t.tzinfo is not None:
            t = t.tz_convert("UTC").tz_localize(None)
        return t.strftime("%Y-%m-%d %H:%M:%S")
    s = s[:19]
    datetime.strptime(s, "%Y-%m-%d %H:%M:%S")  # ValueError za nevalidan format
    return s


def create_event(event_type: str, user_id: Optional[int] = None, product_id: Optional[int] = None,
                 user_session: Optional[str] = None, category_id: Optional[int] = None,
                 quantity: int = 1, price: Optional[float] = None, source: Optional[str] = None,
                 timestamp=None, recommendation_source: Optional[str] = None,
                 recommendation_position: Optional[int] = None) -> dict:
    """Kreira i validira događaj (dict bez ``event_id``)."""
    # TEACH d01: create_event
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"nepoznat event_type: {event_type!r}")
    if event_type in PRODUCT_EVENT_TYPES and product_id is None:
        raise ValueError(f"{event_type} zahteva product_id")
    if quantity is None or int(quantity) < 1:
        raise ValueError("quantity mora biti >= 1")
    if event_type.startswith("recommendation_"):
        if recommendation_position is not None and int(recommendation_position) < 1:
            raise ValueError("recommendation_position je 1-based")
    return {
        "event_type": event_type,
        "user_id": None if user_id is None else int(user_id),
        "user_session": user_session,
        "product_id": None if product_id is None else int(product_id),
        "category_id": None if category_id is None else int(category_id),
        "price": None if price is None else float(price),
        "quantity": int(quantity),
        "source": source or DEFAULT_SOURCE[event_type],
        "timestamp": normalize_timestamp(timestamp),
        "recommendation_source": recommendation_source,
        "recommendation_position": None if recommendation_position is None else int(recommendation_position),
    }
    # /TEACH


class EventStore:
    """Skladište događaja u memoriji (pandas) sa opcionim dopisivanjem u CSV."""

    def __init__(self, events: Optional[pd.DataFrame] = None, live_path: Optional[Path] = None,
                 n_seed: Optional[int] = None):
        if events is None or len(events) == 0:
            events = pd.DataFrame({c: pd.Series(dtype="object") for c in EVENT_COLUMNS})
        self.events = events.reindex(columns=EVENT_COLUMNS).reset_index(drop=True)
        self.live_path = Path(live_path) if live_path else None
        # broj redova iz seeded snapshot-a (sve posle njih su živi događaji)
        self.n_seed = len(self.events) if n_seed is None else int(n_seed)
        self._lock = threading.Lock()
        self._next_id = self._compute_next_id()

    def _compute_next_id(self) -> int:
        if len(self.events) and self.events["event_id"].notna().any():
            return int(pd.to_numeric(self.events["event_id"]).max()) + 1
        return 1

    def __len__(self) -> int:
        return len(self.events)

    def save_event(self, event: dict) -> dict:
        """Dodeljuje ``event_id``, čuva i vraća sačuvan događaj (round-trip)."""
        # TEACH d01: EventStore.save_event
        with self._lock:
            saved = {c: event.get(c) for c in EVENT_COLUMNS}
            saved["event_id"] = self._next_id
            self._next_id += 1
            row = pd.DataFrame([saved], columns=EVENT_COLUMNS)
            if len(self.events):
                self.events = pd.concat([self.events.astype(object), row.astype(object)], ignore_index=True)
            else:
                self.events = row.astype(object)
            if self.live_path is not None:
                new = not self.live_path.exists()
                self.live_path.parent.mkdir(parents=True, exist_ok=True)
                with self.live_path.open("a", newline="") as fh:
                    w = csv.writer(fh, lineterminator="\n")
                    if new:
                        w.writerow(EVENT_COLUMNS)
                    w.writerow(["" if saved[c] is None else saved[c] for c in EVENT_COLUMNS])
            return saved
        # /TEACH

    def _filter(self, col: str, value) -> pd.DataFrame:
        df = self.events
        if col in ("product_id", "user_id"):
            mask = pd.to_numeric(df[col], errors="coerce") == value
        else:
            mask = df[col] == value
        return df[mask].sort_values(["timestamp", "event_id"], kind="stable")

    def get_session_events(self, session_id: str) -> pd.DataFrame:
        return self._filter("user_session", session_id)

    def get_product_events(self, product_id: int) -> pd.DataFrame:
        return self._filter("product_id", int(product_id))

    def get_customer_events(self, user_id: int) -> pd.DataFrame:
        return self._filter("user_id", int(user_id))

    def events_dataframe(self) -> pd.DataFrame:
        df = self.events.copy()
        for c, t in EVENT_DTYPES.items():
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(t)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        return df

    def snapshot_dataframe(self) -> pd.DataFrame:
        """Samo seeded snapshot (bez živih događaja) — za batch trening (stabilna referenca)."""
        return self.events_dataframe().iloc[: self.n_seed].copy()

    @classmethod
    def from_csv(cls, path, live_path=None) -> "EventStore":
        df = pd.read_csv(path, dtype={"user_session": str})
        n_seed = len(df)
        if live_path and Path(live_path).exists():
            df = pd.concat([df, pd.read_csv(live_path, dtype={"user_session": str})], ignore_index=True)
        return cls(df, live_path=live_path, n_seed=n_seed)

    @classmethod
    def load_seeded(cls, path=None, live_path=None) -> "EventStore":
        p = Path(path) if path else dataset_path("events.csv")
        if not p.exists():
            raise FileNotFoundError(
                f"{p} ne postoji — generiši: python -m app.data.generate_dataset --seed 42")
        return cls.from_csv(p, live_path=live_path)
