"""Demo: customer segmentation pipeline (Day 2).

Pokretanje (bilo gde):

    python3 "Day 2/examples/demo_segmentation.py"

Prikazuje: feature-e (RFM) -> skaliranje -> K-Means + silhouette -> profiling ->
manual RFM bucketi (baseline) -> poređenje -> dodela segmenta poznatom i
nepoznatom korisniku.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.events import EventStore
from app.ml.features import (
    SEGMENT_FEATURE_COLUMNS,
    build_customer_features,
    scale_customer_features,
)
from app.ml.segmentation import (
    assign_segment,
    compare_manual_vs_kmeans,
    manual_rfm_buckets,
    profile_segments,
    train_segmentation_model,
)
from app.data.paths import dataset_path


def main() -> None:
    print("=== Day 2 — Customer Segmentation (demo) ===\n")

    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    events = store.events_dataframe()
    print(f"Događaja: {len(events):,}  porudžbina: {orders['order_id'].nunique():,} ({len(orders):,} stavki)")

    # 1) Feature-i
    features = build_customer_features(events, orders)
    print(f"\n[1] Feature tabela: {len(features):,} korisnika")
    rfm_cols = ["user_id", "recency_days", "frequency", "monetary"]
    print(features[rfm_cols].head(6).to_string(index=False))
    buyers = int((features["frequency"] > 0).sum())
    print(f"    kupaca: {buyers:,}  zero-spend: {len(features) - buyers:,}")

    # 2) Skaliranje + K-Means
    scaled, scaler = scale_customer_features(features, SEGMENT_FEATURE_COLUMNS)
    k = 4
    result = train_segmentation_model(scaled, k=k, random_state=42)
    print(f"\n[2] K-Means k={result.k}: silhouette={result.silhouette}")
    print("    raspodela:", pd.Series(result.labels).value_counts().sort_index().to_dict())

    # 3) Profilisanje
    profiles = profile_segments(features, result.labels, scaled_df=scaled)
    print("\n[3] Profili segmenta:")
    cols = ["segment", "count", "share", "recency_days", "frequency", "monetary", "aov", "conversion", "profile"]
    print(profiles[cols].to_string(index=False))

    # 4) Manual RFM baseline + poređenje
    manual = manual_rfm_buckets(features)
    print("\n[4] Manual RFM bucketi (baseline):")
    print(manual.value_counts().to_string())
    comparison = compare_manual_vs_kmeans(features, result.labels, manual)
    print(f"\n    ARI (sličnost particija): {comparison['ari']}")
    print("    dominantni klaster po bucketu:", comparison["dominant_cluster"])

    # 5) Dodela segmenta
    print("\n[5] Dodela segmenta:")
    row = scaled[features["user_id"] == 2].iloc[0]
    print(f"    poznat korisnik 2  -> {assign_segment(result.model, row)}")
    print(f"    nepoznat korisnik  -> {assign_segment(result.model, pd.Series(dtype=float))} (fallback)")

    print("\nGotovo. Vizualizacija: python3 \"Day 2/examples/visualize_clusters.py\"")


if __name__ == "__main__":
    main()
