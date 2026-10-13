"""Demo: session-aware preporuke i feedback loop (Day 9).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 9/examples/demo_session.py"

Prikazuje:
  1) **session features** — recency-weighted interes iz tekuće sesije
     (trajanje, top kategorije/proizvodi, recency);
  2) **session-aware preporuke** — ``recommend_for_session`` (kandidati iz top
     kategorija sesije, bez već viđenih, blend sa popularnošću);
  3) **cold-start fallback** — nepoznata sesija -> popularity (nikad tihi []);
  4) **CTR** — overall + po algoritmu + po poziciji iz seeded impression/click
     loga (zero-division -> 0.0);
  5) **popular vs personalized** — experiment-ready poređenje iz
     ``Day 9/data/impressions.csv`` (simulirani klik-model, NIJE A/B rezultat).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.session import SessionRecommenderService

DEMO_SESSION = "session_005246"   # bogata sesija (korisnik 395: 15 pregleda, 3 kategorije)


def _ids(records: list[dict]) -> str:
    return ",".join(str(r["product_id"]) for r in records)


def main() -> None:
    print("=== Day 9 — Session-Aware Recommendations and the Feedback Loop ===\n")
    svc = SessionRecommenderService()

    # --- 1) Session features ------------------------------------------------- #
    res = svc.recommend_for_session(DEMO_SESSION, limit=5)
    feats = res["session_features"]
    print(f"[1] Session features za sesiju {DEMO_SESSION}:")
    print(f"    n_events={feats['n_events']}  product_events="
          f"{feats['n_product_events']}  distinct_products="
          f"{feats['n_distinct_products']}  duration={feats['duration_minutes']}min")
    print(f"    top_categories: "
          f"{[(c['category_id'], c['interest']) for c in feats['top_categories']]}")
    print(f"    top_products:   "
          f"{[(p['product_id'], p['interest']) for p in feats['top_products']]}")
    print()

    # --- 2) Session-aware preporuke ------------------------------------------ #
    print(f"[2] Session-aware preporuke (k={res['returned']}, "
          f"isključeno viđenih: {res['excluded_seen']}):")
    for r in res["recommendations"]:
        print(f"      #{res['recommendations'].index(r) + 1}  {r['product_id']:>3}  "
              f"{r['name']:<22} score={r['score']:.4f}  "
              f"sources=[{';'.join(r['sources'])}]")
    print()

    # --- 3) Cold-start fallback ---------------------------------------------- #
    print("[3] Cold-start fallback (nepoznata sesija 'session_NOPE'):")
    cs = svc.recommend_for_session("session_NOPE", limit=5)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-5: "
          f"{_ids(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 4) CTR iz seeded impression/click loga ------------------------------- #
    ctr = svc.ctr_dashboard()
    print("[4] CTR iz seeded impression/click loga (zero-division -> 0.0):")
    print(f"    overall: impressions={ctr['overall']['impressions']} "
          f"clicks={ctr['overall']['clicks']} ctr={ctr['overall']['ctr']:.4f}")
    for g in ctr["by_algorithm"]["groups"]:
        print(f"      {g['group']:10s} impressions={g['impressions']:>6} "
              f"clicks={g['clicks']:>4}  ctr={g['ctr']:.4f}")
    print("    po poziciji (position-bias):")
    for g in ctr["by_position"]["groups"]:
        print(f"      position {g['group']}: impressions={g['impressions']:>6} "
              f"clicks={g['clicks']:>4}  ctr={g['ctr']:.4f}")
    print()

    # --- 5) Popular vs personalized ------------------------------------------ #
    print("[5] Popular vs personalized (experiment-ready log, Day 9/data):")
    comp = svc.popular_vs_personalized_comparison()
    print(f"    sessions={comp['n_sessions']}  impressions={comp['n_impressions']}")
    for row in comp["comparison"]:
        print(f"      {row['algorithm']:14s} impressions={row['impressions']:>5} "
              f"clicks={row['clicks']:>4}  ctr={row['ctr']:.4f}")
    print("    klikovi su SIMULIRANI (seed 42, klik-model u metadata.json) —")
    print("    CTR razlika NIJE statistički potvrđen A/B rezultat; Day 9 pravi")
    print("    *prikupljanje podataka* za eksperiment (experiment-ready).")
    print()
    print("API: GET /recommendations/session/{session_id} · "
          "POST /recommendations/events · GET /analytics/recommendations/ctr")
    print("     GET /analytics/recommendations/session-comparison")


if __name__ == "__main__":
    main()
