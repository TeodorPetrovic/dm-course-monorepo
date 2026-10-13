"""Demo: content-based product recommender (Day 5).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 5/examples/demo_content_recommender.py"

Prikazuje:
  1) product text korpus (broj proizvoda, kategorije, popularnost);
  2) **baseline-ove** — popularity top-5 i category top-5 za proizvod;
  3) **content preporuke** (TF-IDF + kosinusna sličnost) — najsličniji bez
     targeta, sa skorom;
  4) **cold-start fallback** — nov proizvod (bez TF-IDF reda) -> popularity
     baseline sa ``fallback=true``, ne tihi ``[]``;
  5) **baseline comparison** — content vs category vs popular za nekoliko
     proizvoda (overlap) — tabela koju README citira.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.recommender import RecommenderService

EXAMPLES = [1, 2, 23, 144, 232]  # pokrivaju različite kategorije i rečnike


def main() -> None:
    print("=== Day 5 — Content-Based Product Recommender (demo) ===\n")
    svc = RecommenderService()

    products = svc.products
    print(f"[0] Product text korpus: {len(products)} proizvoda, "
          f"{products['category_id'].nunique()} kategorija")
    print(f"    popularnost (baseline skor iz događaja): "
          f"min {products['popularity'].min():.0f} · med {products['popularity'].median():.0f} · "
          f"max {products['popularity'].max():.0f}")
    print()

    # --- 1) Baselines ------------------------------------------------------ #
    print("[1] Baselines (obavezne referentne tačke):")
    pop = svc.popular_recommendations(5)
    print("    /recommendations/popular (top-5):")
    for r in pop["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} pop={r['score']:.0f}")
    pid = 1
    cat = svc.category_recommendations(pid, 5)
    print(f"    /recommendations/category/{pid} (top-5, bez targeta):")
    for r in cat["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} pop={r['score']:.0f}")
    print()

    # --- 2) Content preporuke --------------------------------------------- #
    print("[2] Content preporuke (TF-IDF + kosinusna sličnost):")
    content = svc.content_recommendations(pid, 5)
    print(f"    /recommendations/content/{pid}: method={content['method']} "
          f"fallback={content['fallback']}")
    for r in content["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} score={r['score']:.4f}")
    ids = [r["product_id"] for r in content["recommendations"]]
    print(f"    target {pid} isključen: {pid not in ids}")
    print()

    # --- 3) Cold-start fallback ------------------------------------------- #
    print("[3] Cold-start fallback (nov proizvod bez TF-IDF reda):")
    cs = svc.content_recommendations(99999, 5)
    print(f"    /recommendations/content/99999: method={cs['method']} "
          f"fallback={cs['fallback']} reason={cs['fallback_reason']}")
    print(f"    -> popularity baseline, {cs['returned']} preporuka (NIKAD tihi [])")
    print()

    # --- 4) Baseline comparison ------------------------------------------- #
    print("[4] Baseline comparison (content vs category vs popular):")
    print(f"    {'target':>6} {'content top-5':<34} {'category top-5':<34} {'overlap c∩cat':<14}")
    for pid in EXAMPLES:
        comp = svc.baseline_comparison(pid, 5)
        c = ",".join(str(r["product_id"]) for r in comp["content"]["recommendations"])
        cat_ids = ",".join(str(r["product_id"]) for r in comp["category"]["recommendations"])
        ov = ",".join(str(x) for x in comp["overlap"]["content_vs_category"]) or "—"
        print(f"    {pid:>6} {c:<34} {cat_ids:<34} {ov:<14}")
    print()

    print("Gotovo. Vizualizacija: python3 \"Day 5/examples/visualize_content.py\"")


if __name__ == "__main__":
    main()
