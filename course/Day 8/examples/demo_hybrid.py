"""Demo: hybrid candidate-generation and ranking pipeline (Day 8).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 8/examples/demo_hybrid.py"

Prikazuje:
  1) **candidate generation** — per izvor (popularity/category/content/
     collaborative), recall-orijentisana faza;
  2) **merge -> score -> rank** — normalizacija izvora i blended skor
     (težine = heuristika, ne naučen odgovor);
  3) **biznis pravila** — dostupnost (slow movers) + isključi viđeno/kupljeno;
  4) **raznovrsnost** — finalna lista;
  5) **cold-start fallback** — nepoznat korisnik -> popularity (nikad tihi []);
  6) **hybrid vs single-source comparison** (user-based protokol, Day 7 metrike).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.hybrid import DEMO_USER_IDS, HybridRecommenderService

DEMO_USER = DEMO_USER_IDS[0]  # 395 — najaktivniji korisnik


def _ids(records: list[dict]) -> str:
    return ",".join(str(r["product_id"]) for r in records)


def _scores(records: list[dict]) -> str:
    return ", ".join(f"{r['product_id']}({r['score']:.3f})" for r in records)


def main() -> None:
    print("=== Day 8 — Hybrid Candidate-Generation and Ranking Pipeline ===\n")
    svc = HybridRecommenderService()

    # --- 1) Candidate generation -------------------------------------------- #
    print(f"[1] Candidate generation (recall) za korisnika {DEMO_USER}:")
    res = svc.recommend_for_user(DEMO_USER, limit=5, include_pipeline=True)
    pipe = res["pipeline"]
    print(f"    signal proizvoda: {res['n_signal_products']}  "
          f"događaja u train: {res['n_user_events']}")
    print(f"    kandidata po izvoru: {res['candidate_counts']}")
    print(f"    ukupno pre merge-a: {pipe['n_candidates_before_merge']}  ->  "
          f"merged: {pipe['n_merged']}")
    print()

    # --- 2) Merge + score + rank -------------------------------------------- #
    print("[2] Merge -> score -> rank (normalizovani skorovi, težine "
          f"{svc.merge_weights}):")
    print(f"    težine su HEURISTIKA, ne naučen odgovor (DAY-BRIEFS).")
    for r in res["recommendations"]:
        print(f"      #{res['recommendations'].index(r) + 1}  {r['product_id']:>3}  "
              f"{r['name']:<22} score={r['score']:.4f}  "
              f"sources=[{';'.join(r['sources'])}]")
    print()

    # --- 3) Business rules --------------------------------------------------- #
    print(f"[3] Biznis pravila posle rangiranja: {res['rules']}")
    print(f"    removed: {pipe['n_removed_by_rules']}  preostalo: "
          f"{pipe['n_after_rules']}  (exclude_purchased + availability)")
    print()

    # --- 4) Diversity -------------------------------------------------------- #
    print(f"[4] Raznovrsnost (max_per_category={res['max_per_category']}): "
          f"finalna lista {_ids(res['recommendations'])}")
    print()

    # --- 5) Cold-start fallback ---------------------------------------------- #
    print("[5] Cold-start fallback (nepoznat korisnik 99999):")
    cs = svc.recommend_for_user(99999, limit=5)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-5: "
          f"{_ids(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 6) Hybrid vs single-source ------------------------------------------ #
    print("[6] Hybrid vs single-source (user-based protokol, Day 7 metrike):")
    print(f"    {'method':<14} {'P@5':>7} {'R@5':>7} {'HR@5':>7} "
          f"{'NDCG@5':>8} {'coverage':>9}")
    # brži podskup za demo (pun report je u Day 8/data/comparison.csv i na
    # GET /analytics/recommendations/hybrid)
    rep = svc.user_based_comparison(k=5, max_test_users=200)
    for row in rep["comparison"]:
        print(
            f"    {row['method']:<14} {row['precision_at_k']:>7.4f} "
            f"{row['recall_at_k']:>7.4f} {row['hit_rate_at_k']:>7.4f} "
            f"{row['ndcg_at_k']:>8.4f} {row['catalog_coverage']:>9.4f}"
        )
    print(f"    (test korisnika: {rep['n_test_users']}; pun izveštaj — "
          f"`python -m app.data.generate_hybrid`)")
    print()
    rows = {r["method"]: r for r in rep["comparison"]}
    best = max(rows.values(), key=lambda r: r["precision_at_k"])
    h = rows["hybrid"]
    print(f"Interpretacija (računato, ne napamet): najviši P@5 ima {best['method']} "
          f"({best['precision_at_k']:.4f}); hybrid ima P@5 {h['precision_at_k']:.4f} i coverage "
          f"{h['catalog_coverage']:.2f} (vs {best['catalog_coverage']:.2f}).")
    if best["method"] != "hybrid":
        print("    Hybrid sa ručnim težinama NIJE pobedio — to je pošten rezultat, ne bag; "
              "težine nisu naučene (vidi lekciju).")
    print("API: GET /recommendations/{user_id} · GET /analytics/recommendations/hybrid")


if __name__ == "__main__":
    main()
