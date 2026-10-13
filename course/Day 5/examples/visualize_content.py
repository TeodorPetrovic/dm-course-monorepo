"""Vizualizacija content preporuka (Day 5, supporting material).

Dve slike u ``Day 5/examples/``:

    - ``cosine_heatmap.png`` — kosinusna sličnost između uzorka proizvoda
      (24 proizvoda iz 2 kategorije): blokovska struktura po kategoriji +
      „hot" dijagonalni parovi (proizvodi sa istim rečnikom su skoro duplikati —
      overspecialization).
    - ``baseline_overlap.png`` — za nekoliko targeta, koliko od top-5 content
      preporuka se poklapa sa category top-5 i popularity top-5 (baseline
      comparison).

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 5/examples/visualize_content.py"

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

from app.recommenders.content import build_tfidf_matrix, calculate_product_similarity
from app.services.recommender import RecommenderService, TFIDF_KWARGS

OUT_DIR = Path(__file__).resolve().parent
SAMPLE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
              22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]  # Electronics + Fashion


def cosine_heatmap(svc: RecommenderService) -> None:
    """Heatmap kosinusne sličnosti za uzorak proizvoda (2 kategorije)."""
    products = svc.products
    sample = products[products["product_id"].isin(SAMPLE_IDS)].sort_values("product_id")
    matrix, _ = build_tfidf_matrix(sample, **TFIDF_KWARGS)
    full = np.zeros((len(sample), len(sample)))
    for i in range(len(sample)):
        full[i] = calculate_product_similarity(matrix, i)

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(full, cmap="viridis", vmin=0, vmax=1)
    labels = [f"{int(r['product_id'])}:{r['name'].split()[0][:8]}" for _, r in sample.iterrows()]
    ax.set_xticks(range(len(sample)))
    ax.set_yticks(range(len(sample)))
    ax.set_xticklabels(labels, fontsize=5.5, rotation=90)
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_title("Kosinusna sličnost teksta proizvoda (Electronics + Fashion)")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "cosine_heatmap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'cosine_heatmap.png'}")


def baseline_overlap(svc: RecommenderService) -> None:
    """Trakice: overlap content∩category i content∩popular po targetu."""
    targets = [1, 2, 23, 144, 232]
    cat_overlap, pop_overlap = [], []
    for pid in targets:
        comp = svc.baseline_comparison(pid, 5)
        cat_overlap.append(len(comp["overlap"]["content_vs_category"]))
        pop_overlap.append(len(comp["overlap"]["content_vs_popular"]))

    x = range(len(targets))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.5))
    b1 = ax.bar([i - w / 2 for i in x], cat_overlap, w, label="content ∩ category", color="#3b82f6")
    b2 = ax.bar([i + w / 2 for i in x], pop_overlap, w, label="content ∩ popular", color="#94a3b8")
    for i, (c, p) in enumerate(zip(cat_overlap, pop_overlap)):
        ax.text(i - w / 2, c + 0.05, str(c), ha="center", fontsize=9)
        ax.text(i + w / 2, p + 0.05, str(p), ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"p{pid}" for pid in targets])
    ax.set_ylabel("overlap (od top-5)")
    ax.set_title("Content vs baselines — poklapanje top-5 preporuka")
    ax.set_ylim(0, 5)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "baseline_overlap.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'baseline_overlap.png'}")


def main() -> None:
    print("=== Day 5 — content recommender vizualizacija ===")
    svc = RecommenderService()
    cosine_heatmap(svc)
    baseline_overlap(svc)
    print("Gotovo.")


if __name__ == "__main__":
    main()
