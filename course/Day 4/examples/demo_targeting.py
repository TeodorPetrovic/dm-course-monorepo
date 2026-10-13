"""Demo: ML-assisted campaign targeting (Day 4).

Pokretanje (bilo gde):

    python3 "Day 4/examples/demo_targeting.py"

Prikazuje:
  1) targeting profil (segment + verovatnoća + vrednost) iz ``Day 4/data``;
  2) **prediction vs decision** — korisnik sa NAJVEĆOM verovatnoćom NIJE najbolja
     odluka (očekivana vrednost);
  3) rule-based vs ML-assisted poređenje za svaku kampanju (seeded profil,
     deterministički — isti brojevi kao README);
  4) live API putanju: ako su Day 2/3 modeli trenirani -> ML publika; ako nisu ->
     **definisan fallback** (mode=rule, fallback=true, untrained_model).
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.campaigns import load_campaigns
from app.data.paths import course_root
from app.ml.targeting import compare_rule_vs_ml, select_target_customers, rank_target_customers
from app.services.targeting import TargetingService

DAY4_DATA = course_root() / "Day 4" / "data"


def main() -> None:
    print("=== Day 4 — ML-Assisted Campaign Targeting (demo) ===\n")

    profiles = pd.read_csv(DAY4_DATA / "customer_profiles.csv")
    campaigns = {c["campaign_id"]: c for c in load_campaigns()}
    print(f"Profil: {len(profiles)} korisnika sa istorijom pre cut-off-a")
    print(f"  po RFM bucket-u: "
          f"{ {str(k): int(v) for k, v in profiles['rfm_bucket'].value_counts().items()} }")
    print(f"  po K-Means segmentu: "
          f"{ {str(k): int(v) for k, v in profiles['segment'].value_counts().items()} }")
    print()

    # --- 1) Prediction vs decision (kampanja 1: VIP reaktivacija) ---------- #
    c1 = campaigns[1]
    sel1 = select_target_customers(profiles, c1)
    ranked1 = rank_target_customers(sel1, c1, limit=None)
    top_prob = ranked1.loc[ranked1["probability"].idxmax()]
    top_decision = ranked1.iloc[0]
    print("[1] Prediction vs decision (kampanja 1 — VIP reaktivacija):")
    print(f"    najveća VEROVATNOĆA: user {int(top_prob['user_id'])}  "
          f"P={top_prob['probability']:.4f}  vrednost={top_prob['monetary']:.2f}  "
          f"skor={top_prob['score']:.4f}  (rank {int(top_prob['rank'])})")
    print(f"    najbolja ODLUKA:     user {int(top_decision['user_id'])}  "
          f"P={top_decision['probability']:.4f}  vrednost={top_decision['monetary']:.2f}  "
          f"skor={top_decision['score']:.4f}  (rank 1)")
    # Par u top-30 sa najvećom razlikom u P gde je VEROVATNIJI korisnik ipak rangiran NIŽE.
    top = ranked1.head(30).to_dict("records")
    pairs = [(a["probability"] - b["probability"], a, b) for a in top for b in top
             if a["probability"] > b["probability"] and a["score"] < b["score"]]
    if pairs:
        _, a, b = max(pairs, key=lambda x: (x[0], -x[1]["user_id"]))
        cost = c1["cost_per_contact"]
        print(f"    inverzija: user {a['user_id']} (P={a['probability']:.4f}, rank {a['rank']}) vs "
              f"user {b['user_id']} (P={b['probability']:.4f}, rank {b['rank']})")
        print(f"    model kaže {a['probability']:.2f} > {b['probability']:.2f}; odluka kaže "
              f"{a['probability']:.2f}×{a['monetary']:.0f} − {cost} = {a['score']:.1f} < "
              f"{b['probability']:.2f}×{b['monetary']:.0f} − {cost} = {b['score']:.1f}")
    print()

    # --- 2) Rule vs ML poređenje po kampanji (seeded profil, logistic) ----- #
    print("[2] Rule-based vs ML-assisted (seed profil, logistic_regression):")
    print(f"    {'kampanja':<12} {'limita':>6} {'rule_conv':>10} {'ml_conv':>10} "
          f"{'lift':>7} {'overlap':>8} {'jaccard':>8}")
    for cid in sorted(campaigns):
        camp = campaigns[cid]
        cmp = compare_rule_vs_ml(profiles, camp, limit=None)
        m = cmp["metrics"]
        print(f"    {camp['name'][:12]:<12} {cmp['limit']:>6} "
              f"{m['rule']['expected_conversions']:>10.1f} "
              f"{m['ml']['expected_conversions']:>10.1f} "
              f"{str(m['lift_expected_conversions']):>7} {m['overlap']:>8} {m['jaccard']:>8.2f}")
    print()

    # --- 3) Live API putanja: ML publika ili fallback ---------------------- #
    print("[3] Live targeting (servis + modeli u app/models/):")
    svc = TargetingService()
    if svc._ml_available():
        print("    Day 2/3 modeli su trenirani -> ML-assisted publika.")
    else:
        print("    Day 2/3 modeli NISU trenirani -> fallback na rule targeting.")
    for cid in (1, 3):
        res = svc.recommended_audience(cid, limit=5, mode="ml")
        print(f"    kampanja {cid}: mode={res['mode']} fallback={res['fallback']} "
              f"selected={res['selected']} returned={res['returned']}")
        if res["audience"]:
            a = res["audience"][0]
            print(f"      #1 user {a['user_id']}  P={a['probability']}  "
                  f"score={a['score']}  {a['reasons'][-1]}")
    print()

    print("Gotovo. Vizualizacija: python3 \"Day 4/examples/visualize_targeting.py\"")


if __name__ == "__main__":
    main()
