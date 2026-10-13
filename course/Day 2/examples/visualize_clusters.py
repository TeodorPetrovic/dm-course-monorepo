"""Vizualizacija klastera (Day 2, supporting material).

Gradi feature-e -> skalira -> trenira K-Means (k=4) i pravi dve slike u
``Day 2/examples/``:

    - ``clusters_pca.png``  — PCA projekcija skaliranih feature-a u 2D,
      obojena po klasteru (inspekcija: da li su klasteri odvojeni?).
    - ``silhouette.png``    — bar-chart silhouette-a za k=2..6 (zašto baš k?

Ovo je *eksploratorni* materijal — notebook/skripta za učenike, ne primarni
deliverable (vidi DAY-BRIEFS House Rules).

Pokretanje:

    python3 "Day 2/examples/visualize_clusters.py"

Zahteva ``matplotlib`` (u ``dm-ml/requirements.txt``).
"""

import sys
from pathlib import Path

# dm-ml na sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import matplotlib

matplotlib.use("Agg")  # bez GUI — čuvamo PNG fajlove
import matplotlib.pyplot as plt
import pandas as pd

from app.data.events import EventStore
from app.data.paths import dataset_path
from app.ml.features import SEGMENT_FEATURE_COLUMNS, build_customer_features, scale_customer_features
from app.ml.segmentation import evaluate_k_range, train_segmentation_model
from sklearn.decomposition import PCA

OUT_DIR = Path(__file__).resolve().parent


def build():
    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    features = build_customer_features(store.events_dataframe(), orders)
    scaled, _ = scale_customer_features(features, SEGMENT_FEATURE_COLUMNS)
    return features, scaled


def plot_pca(features, scaled, labels):
    pca = PCA(n_components=2, random_state=42).fit_transform(scaled[SEGMENT_FEATURE_COLUMNS])
    df = pd.DataFrame(pca, columns=["pc1", "pc2"])
    df["segment"] = [f"segment_{l}" for l in labels]

    fig, ax = plt.subplots(figsize=(7, 5))
    for seg, grp in df.groupby("segment", sort=True):
        ax.scatter(grp["pc1"], grp["pc2"], s=8, alpha=0.6, label=f"{seg} (n={len(grp)})")
    ax.set_title("K-Means segmenti — PCA projekcija skaliranih feature-a (k=4)")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = OUT_DIR / "clusters_pca.png"
    fig.savefig(out, dpi=120)
    print(f"Snimljeno: {out}")
    plt.close(fig)


def plot_silhouette(scaled):
    table = evaluate_k_range(scaled, k_range=range(2, 7))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(table["k"].astype(str), table["silhouette"], color="#4c72b0")
    ax.set_title("Silhouette po broju klastera (k=2..6)")
    ax.set_xlabel("k")
    ax.set_ylabel("silhouette")
    ax.set_ylim(0, 1)
    for x, y in zip(table["k"].astype(str), table["silhouette"]):
        ax.text(x, y + 0.02, f"{y:.3f}", ha="center", fontsize=8)
    fig.tight_layout()
    out = OUT_DIR / "silhouette.png"
    fig.savefig(out, dpi=120)
    print(f"Snimljeno: {out}")
    plt.close(fig)


def main() -> None:
    features, scaled = build()
    result = train_segmentation_model(scaled, k=4, random_state=42)
    print(f"k=4 silhouette={result.silhouette}")
    plot_pca(features, scaled, result.labels)
    plot_silhouette(scaled)


if __name__ == "__main__":
    main()
