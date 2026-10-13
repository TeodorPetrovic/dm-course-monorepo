"""Demo: event layer na seeded podacima (Day 1).

Pokretanje (bilo gde):

    python3 "Day 1/examples/demo_events.py"

Prikazuje: učitavanje seeded store-a, upite po sesiji/proizvodu/korisniku,
i round-trip (save_event -> get_customer_events).
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.data.events import VALID_EVENT_TYPES, EventStore, create_event
from app.data.analytics import calculate_funnel_counts


def main() -> None:
    store = EventStore.load_seeded()
    events = store.events_dataframe()
    print(f"Ukupno događaja u seeded datasetu: {len(events):,}")
    print(f"Dozvoljeni tipovi događaja: {sorted(VALID_EVENT_TYPES)}")

    # Upit po sesiji
    first_session = events["user_session"].iloc[0]
    session_df = store.get_session_events(first_session)
    print(f"\nPrimer sesije {first_session}: {len(session_df)} događaja")
    print(session_df[["event_id", "event_type", "product_id", "timestamp"]].to_string(index=False))

    # Upit po proizvodu i korisniku
    pid = int(events["product_id"].dropna().iloc[0])
    print(f"\nDogađaji za proizvod {pid}: {len(store.get_product_events(pid))}")
    uid = int(events["user_id"].iloc[0])
    print(f"Događaji za korisnika {uid}: {len(store.get_customer_events(uid))}")

    # Round-trip: save_event -> get_customer_events
    ev = create_event(
        "search",
        user_id=uid,
        user_session="demo_session_1",
        source="search_page",
        timestamp="2026-01-15 12:00:00",
    )
    saved = store.save_event(ev)
    print(f"\nRound-trip: sačuvan događaj event_id={saved['event_id']}")
    found = store.get_customer_events(uid)
    hit = found[found["event_id"] == saved["event_id"]]
    print(f"get_customer_events({uid}) sadrži sačuvan događaj: {len(hit) == 1}")
    print(hit[["event_id", "event_type", "source", "timestamp"]].to_string(index=False))


if __name__ == "__main__":
    main()
