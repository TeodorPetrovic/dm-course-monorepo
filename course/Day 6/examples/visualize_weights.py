"""Vizualizacija collaborative preporuka (Day 6, supporting material).

Dve slike u ``Day 6/examples/``:

    - ``weight_sensitivity.png`` — za target proizvod, koliko se top-5 preporuka
      poklapa sa default šemom težina po različitim šemama. Mali overlap =
      težine menjaju izlaz = težine su pretpostavke, ne istine.
    - ``item_similarity_heatmap.png`` — item-item kosinusna sličnost za uzorak
      proizvoda (24 iz više kategorija): blokovi po kategoriji (proizvodi koje
      iste sesije gledaju zajedno) + dijagonalni parovi.

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/visualize_weights.py"

Zahteva ``matplotlib`` (u ``dm-ml/requirements.txt``).
"""

import sys
from pathlib import Path

# dm-ml na sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import matplotlib

matplotlib.use("Agg")  # bez GUI — čuvamo PNG fajlove
import matplotlib.pyplot as plt
import numpy as np

from app.recommenders.collaborative import calculate_item_similarity
from app.services.collaborative import CollaborativeRecommenderService

OUT_DIR = Path(__file__).resolve().parent
TARGET = 1
SAMPLE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
              22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]


def weight_sensitivity_plot(svc: CollaborativeRecommenderService) -> None:
    """Bars: overlap sa default šemom po šemi težina za target."""
    ws = svc.weight_sensitivity(TARGET, limit=5)
    rows = ws["rows"]
    names = [r["name"] for r in rows]
    overlaps = [r["overlap_with_default"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(range(len(names)), overlaps, color="#3b82f6")
    for i, (bar, r) in enumerate(zip(bars, rows)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"top: {r['top_ids'][0]}", ha="center", fontsize=8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=7, rotation=18, ha="right")
    ax.set_ylabel("overlap sa default težinama (od top-5)")
    ax.set_ylim(0, 5.5)
    ax.set_title(f"Weight sensitivity — target {TARGET} (težine su pretpostavke)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "weight_sensitivity.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'weight_sensitivity.png'}")


def item_similarity_heatmap(svc: CollaborativeRecommenderService) -> None:
    """Heatmap item-item kosinusne sličnosti za uzorak proizvoda."""
    inter = svc._interaction()
    products = svc.products
    sample = products[products["product_id"].isin(SAMPLE_IDS)].sort_values("product_id")
    sample_ids = sorted(int(x) for x in sample["product_id"])
    idx = [inter.products.index(p) for p in sample_ids]
    sim = calculate_item_similarity(inter)
    sub = sim[np.ix_(idx, idx)].toarray()

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(sub, cmap="viridis", vmin=0, vmax=1)
    labels = [f"{p}:{products.loc[products['product_id']==p, 'name'].iloc[0].split()[0][:8]}" for p in sample_ids]
    ax.set_xticks(range(len(sample_ids)))
    ax.set_yticks(range(len(sample_ids)))
    ax.set_xticklabels(labels, fontsize=5.5, rotation=90)
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_title("Item-item kosinusna sličnost (implicit feedback)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "item_similarity_heatmap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'item_similarity_heatmap.png'}")


def main() -> None:
    print("=== Day 6 — collaborative recommender vizualizacija ===")
    svc = CollaborativeRecommenderService()
    weight_sensitivity_plot(svc)
    item_similarity_heatmap(svc)
    print("Gotovo.")


if __name__ == "__main__":
    main()
