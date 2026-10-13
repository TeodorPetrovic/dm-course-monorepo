"""Demo: analitika na seeded podacima (Day 1).

Pokretanje (bilo gde):

    python3 "Day 1/examples/demo_analytics.py"

Prikazuje: funnel brojeve, stopu konverzije, udeo po kategoriji i
najgledanije proizvode.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.analytics import (
    average_order_value,
    calculate_conversion_rate,
    calculate_funnel_counts,
    get_product_view_count,
    share_by_category,
)
from app.data.events import EventStore
from app.data.paths import dataset_path


def main() -> None:
    store = EventStore.load_seeded()
    events = store.events_dataframe()
    products = pd.read_csv(dataset_path("products.csv"))
    orders = pd.read_csv(dataset_path("orders.csv"))

    funnel = calculate_funnel_counts(events)
    print("Levak (funnel):")
    for k, v in funnel.items():
        print(f"  {k:22s} {v:>7,}")

    cr = calculate_conversion_rate(events)
    print(f"\nStopa konverzije (sesije sa kupovinom / sve sesije): {cr:.4f}")

    print("\nTržišni udeo kategorija po pregledima (share-by-category):")
    share = share_by_category(events, products, metric="view")
    categories = pd.read_csv(dataset_path("categories.csv"))
    cat_names = categories.set_index("category_id")["name"]
    share["category"] = share["category_id"].map(cat_names)
    print(share[["category", "count", "share"]].to_string(index=False))

    print("\nTop 5 proizvoda po broju pregleda:")
    view_counts = events[events["event_type"] == "product_view"]["product_id"].value_counts().head(5)
    for pid, n in view_counts.items():
        pid = int(pid)  # Int64 key -> int za prikaz i upit
        p = products[products["product_id"] == pid].iloc[0]
        print(f"  #{pid} {p['name']:<28s} views={n:<5,}  cena={p['price']:>8.2f}")

    print("\nPorudžbine:", orders["order_id"].nunique(), f"({len(orders)} stavki)",
          "  prosečna vrednost porudžbine (AOV):", average_order_value(orders))

    # Provera: sum(per-product views) == total views (interna konzistentnost)
    total_via_products = sum(
        get_product_view_count(events, pid) for pid in products["product_id"]
    )
    print(f"\nInterna provera: suma po proizvodima ({total_via_products:,}) "
          f"== ukupni pregledi ({funnel['views']:,}) -> {total_via_products == funnel['views']}")


if __name__ == "__main__":
    main()
