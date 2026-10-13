"""Vizualizacija targetinga (Day 4, supporting material).

Dve slike u ``Day 4/examples/``:

    - ``audience_scatter.png`` — za kampanju 1 (VIP): svaki eligibilni korisnik
      kao tačka (P × vrednost), obojena po segmentu; naglašeni top-50 rule
      audience (skor = prioritet bucket-a + vrednost) i top-50 ML audience
      (skor = očekivana vrednost P×vrednost − cena). Anotirani: najveća
      verovatnoća i najbolja odluka (ID-jevi se ispisuju u konzoli) — prediction vs decision.
    - ``comparison_rule_vs_ml.png`` — očekivane konverzije (suma verovatnoća)
      rule vs ML po kampanji, sa lift-om iznad svake grupe.

Ovo je *eksploratorni* materijal — skripta za učenike, ne primarni deliverable
(vidi DAY-BRIEFS House Rules).

Pokretanje:

    python3 "Day 4/examples/visualize_targeting.py"

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

from app.data.campaigns import load_campaigns
from app.data.paths import course_root
from app.ml.targeting import (
    compare_rule_vs_ml,
    rank_by_rule,
    rank_target_customers,
    select_target_customers,
)

OUT_DIR = Path(__file__).resolve().parent
DAY4_DATA = course_root() / "Day 4" / "data"

SEGMENT_COLORS = {
    "segment_0": "#94a3b8",
    "segment_1": "#3b82f6",
    "segment_2": "#f59e0b",
    "segment_3": "#10b981",
}


def scatter_audience(profiles: pd.DataFrame, campaign: dict) -> None:
    """Scatter P × vrednost za eligibilne korisnike + top-50 rule/ML publika."""
    sel = select_target_customers(profiles, campaign)
    ranked_ml = rank_target_customers(sel, campaign, limit=50)
    ranked_rule = rank_by_rule(profiles, campaign, limit=50)
    ml_ids = set(ranked_ml["user_id"])
    rule_ids = set(ranked_rule["user_id"])

    fig, ax = plt.subplots(figsize=(8.5, 6))
    for seg, grp in sel.groupby("segment", sort=True):
        ax.scatter(grp["probability"], grp["monetary"], s=14, alpha=0.55,
                   color=SEGMENT_COLORS.get(seg, "#64748b"), label=f"{seg} (n={len(grp)})")

    # Top-50 publike (rule i ML) preko pozadine.
    ax.scatter(ranked_rule["probability"], ranked_rule["monetary"], s=22,
               facecolors="none", edgecolors="#dc2626", linewidths=1.2,
               label=f"rule top-50 (n={len(ranked_rule)})")
    ax.scatter(ranked_ml["probability"], ranked_ml["monetary"], s=22,
               facecolors="none", edgecolors="#000000", linewidths=1.2,
               label=f"ML top-50 (n={len(ranked_ml)})")

    # Prediction vs decision primer.
    top_prob = ranked_ml.loc[ranked_ml["probability"].idxmax()]
    top_dec = ranked_ml.iloc[0]
    print(f"  najveća P: user {int(top_prob['user_id'])} (P={top_prob['probability']:.3f}) · "
          f"najbolja odluka: user {int(top_dec['user_id'])} (P={top_dec['probability']:.3f})")
    ax.annotate(f"najveća P ({int(top_prob['user_id'])})", xy=(top_prob["probability"], top_prob["monetary"]),
                xytext=(top_prob["probability"] - 0.28, top_prob["monetary"] + 250),
                arrowprops=dict(arrowstyle="->", color="#111827"), fontsize=8)
    ax.annotate(f"najbolja odluka ({int(top_dec['user_id'])})", xy=(top_dec["probability"], top_dec["monetary"]),
                xytext=(top_dec["probability"] - 0.30, top_dec["monetary"] - 320),
                arrowprops=dict(arrowstyle="->", color="#111827"), fontsize=8)

    ax.set_xlabel("P(kupovina) — Day 3 model")
    ax.set_ylabel("istorijska vrednost (monetary)")
    ax.set_title(f"Kampanja 1 — VIP reaktivacija: rule vs ML publika (top-50)")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "audience_scatter.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'audience_scatter.png'}")


def comparison_bars(profiles: pd.DataFrame, campaigns: dict) -> None:
    """Gruisane trake: očekivane konverzije rule vs ML po kampanji + lift."""
    names, rule_conv, ml_conv, lifts = [], [], [], []
    for cid in sorted(campaigns):
        camp = campaigns[cid]
        cmp = compare_rule_vs_ml(profiles, camp, limit=None)
        m = cmp["metrics"]
        names.append(camp["name"])
        rule_conv.append(m["rule"]["expected_conversions"])
        ml_conv.append(m["ml"]["expected_conversions"])
        lifts.append(m["lift_expected_conversions"])

    x = range(len(names))
    w = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar([i - w / 2 for i in x], rule_conv, w, label="rule (RFM/vrednost)", color="#94a3b8")
    b2 = ax.bar([i + w / 2 for i in x], ml_conv, w, label="ML (očekivana vrednost)", color="#3b82f6")
    for i, (rc, mc, lift) in enumerate(zip(rule_conv, ml_conv, lifts)):
        ax.text(i - w / 2, rc + 2, f"{rc:.0f}", ha="center", fontsize=8)
        ax.text(i + w / 2, mc + 2, f"{mc:.0f}", ha="center", fontsize=8)
        if lift is not None:
            ax.text(i, max(rc, mc) + 12, f"lift {lift:.2f}", ha="center", fontsize=8, color="#111827")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("očekivane konverzije (suma P)")
    ax.set_title("Rule-based vs ML-assisted targeting — očekivane konverzije")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "comparison_rule_vs_ml.png", dpi=120)
    plt.close(fig)
    print(f"  -> {OUT_DIR / 'comparison_rule_vs_ml.png'}")


def main() -> None:
    print("=== Day 4 — targeting vizualizacija ===")
    profiles = pd.read_csv(DAY4_DATA / "customer_profiles.csv")
    campaigns = {c["campaign_id"]: c for c in load_campaigns()}
    scatter_audience(profiles, campaigns[1])
    comparison_bars(profiles, campaigns)
    print("Gotovo.")


if __name__ == "__main__":
    main()
