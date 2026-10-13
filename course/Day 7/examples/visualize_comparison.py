"""Vizualizacija comparison report-a (Day 7, supporting material).

Jedna slika u ``Day 7/examples/``:

    - ``comparison.png`` — grupisani bar chart: P@5 / R@5 / HR@5 / NDCG@5 /
      coverage po metodi (popularity/category/content/collaborative). Vizuelno
      pokazuje: category najviše metrike, popularity najniži coverage
      (popularity bias), content coverage 1.0.

Ovo je *eksploratorni* materijal (vidi DAY-BRIEFS House Rules).

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 7/examples/visualize_comparison.py"

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
import pandas as pd

from app.data.paths import course_root, dataset_path
from app.recommenders.evaluation import build_comparison_report

OUT_DIR = Path(__file__).resolve().parent
METRIC_LABELS = {
    "precision_at_k": "P@5",
    "recall_at_k": "R@5",
    "hit_rate_at_k": "HR@5",
    "ndcg_at_k": "NDCG@5",
    "catalog_coverage": "coverage",
}


def main() -> None:
    events = pd.read_csv(dataset_path("events.csv"))
    products = pd.read_csv(course_root() / "Day 5" / "data" / "products_text.csv")
    report = build_comparison_report(events, products, k=5, split_ratio=0.8)

    comparison = pd.DataFrame(report["comparison"]).set_index("method")
    metrics = [m for m in METRIC_LABELS if m in comparison.columns]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(comparison))
    width = 0.15
    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"]
    for i, metric in enumerate(metrics):
        vals = comparison[metric].astype(float)
        ax.bar(x + (i - len(metrics) / 2) * width, vals, width * 0.92,
               label=METRIC_LABELS[metric], color=colors[i % len(colors)])
        for xi, v in zip(x, vals):
            ax.text(xi + (i - len(metrics) / 2) * width, v + 0.01, f"{v:.2f}",
                    ha="center", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(comparison.index)
    ax.set_ylabel("vrednost (0–1)")
    ax.set_ylim(0, 1.12)
    ax.set_title(f"Comparison report (k=5, temporal split 0.8, "
                 f"n={report['n_test_cases']} test cases)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    out = OUT_DIR / "comparison.png"
    fig.savefig(out, dpi=140)
    print(f"Sačuvano: {out}")

    # Ispis tumačenja koje slika ne pokazuje sama.
    print("\nKratko tumačenje:")
    print("  - category: najviši P@5/HR@5 — sesije ostaju u kategoriji.")
    print("  - popularity: najniži coverage (~0.02) — popularity bias (blockbusteri).")
    print("  - content: coverage 1.0 — preporučuje ceo katalog (raznolikost ≠ relevantnost).")


if __name__ == "__main__":
    main()
