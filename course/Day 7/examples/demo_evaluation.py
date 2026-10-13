"""Demo: recommendation evaluation framework (Day 7).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 7/examples/demo_evaluation.py"

Prikazuje:
  1) temporal split — train/test po VREMENU (anti-leakage), sa brojevima;
  2) test cases — sesija → (query, targets) iz test perioda;
  3) ručno izračunate metrike na jednom primeru (P@K, R@K, HR@K, NDCG@K);
  4) **comparison report** — popularity/category/content/collaborative
     (P@5/R@5/HR@5/NDCG@5/coverage);
  5) tumačenje: category najprecizniji, popularity najniži coverage
     (popularity bias), content coverage 1.0.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.paths import course_root, dataset_path
from app.recommenders.evaluation import (
    build_comparison_report,
    extract_test_cases,
    metrics_at_k,
    temporal_split,
)

K = 5
SPLIT_RATIO = 0.8


def main() -> None:
    print("=== Day 7 — Recommendation Evaluation Framework ===\n")

    events = pd.read_csv(dataset_path("events.csv"))
    products = pd.read_csv(course_root() / "Day 5" / "data" / "products_text.csv")

    # --- 1) Temporal split --------------------------------------------------- #
    train, test, split = temporal_split(events, split_ratio=SPLIT_RATIO)
    print(f"[1] Temporal split (NE random): granica = {split}")
    print(f"    train={len(train)} događaja · test={len(test)} događaja · "
          f"test sesija={test['user_session'].nunique()}")
    print("    Random split bi promešao prošlost i budućnost (leakage); ovako se")
    print("    preporučivači treniraju SAMO na prošlosti.\n")

    # --- 2) Test cases ------------------------------------------------------- #
    cases = extract_test_cases(test, min_session_items=2)
    print(f"[2] Test cases (sesija → query → targets): {len(cases)}")
    for c in cases[:3]:
        print(f"    {c['session_id']}: query={c['query_product_id']} "
              f"targets={c['target_product_ids']}")
    print("    query = prvi proizvod koji sesija vidi u test periodu;")
    print("    targets = proizvodi viđeni KASNIJE u istoj sesiji.\n")

    # --- 3) Ručno izračunate metrike na jednom primeru ----------------------- #
    case = cases[0]
    ranked = [case["target_product_ids"][0], 999, 998, 997, 996]  # hipotetički top-5
    m = metrics_at_k(ranked, case["target_product_ids"], K)
    print("[3] Metrike na jednom primeru:")
    print(f"    query={case['query_product_id']} targets={case['target_product_ids']}")
    print(f"    hipotetički top-5 = {ranked}")
    for name, val in m.items():
        print(f"      {name}: {val:.4f}")
    print("    P@K udeo relevantnih u top-K · R@K udeo relevantnih uhvaćen ·")
    print("    HR@K bar jedan pogodak · NDCG@K kažnjava duboke pozicije.\n")

    # --- 4) Comparison report ------------------------------------------------ #
    print(f"[4] Comparison report (k={K}, split_ratio={SPLIT_RATIO}):")
    report = build_comparison_report(events, products, k=K, split_ratio=SPLIT_RATIO)
    header = f"{'metod':14s} {'P@5':>6s} {'R@5':>6s} {'HR@5':>6s} {'NDCG@5':>8s} {'coverage':>9s}"
    print("    " + header)
    for row in report["comparison"]:
        print(
            f"    {row['method']:14s} {row['precision_at_k']:6.3f} "
            f"{row['recall_at_k']:6.3f} {row['hit_rate_at_k']:6.3f} "
            f"{row['ndcg_at_k']:8.3f} {row['catalog_coverage']:9.3f}"
        )
    print(f"\n    n_test_cases = {report['n_test_cases']}")

    # --- 5) Tumačenje -------------------------------------------------------- #
    print("\n[5] Tumačenje:")
    print("    - category ima najviši P@5/HR@5: sesije ostaju u kategoriji.")
    print("    - popularity ima najniži coverage (2%): popularity bias — uvek isti")
    print("      'blockbusteri'; dobra metrika ne znači korisnu raznolikost.")
    print("    - content coverage 1.0: preporučuje ceo katalog (raznolikost, ne i")
    print("      nužno relevantnost).")
    print("    - Metrike su sočivo, ne presuda: bolji P@5 ovde ≠ bolji preporučivač")
    print("      u pravom store-u.")


if __name__ == "__main__":
    main()
