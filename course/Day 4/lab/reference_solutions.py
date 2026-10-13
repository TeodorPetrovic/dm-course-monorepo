"""Referentno rešenje Day 4 lab-a."""
from __future__ import annotations

import pandas as pd

from starter import BUCKET_PRIORITY, _eligibility  # noqa: F401


def score_customer(probability, segment, rfm_bucket, monetary, campaign):
    ok, reasons = _eligibility(probability, segment, rfm_bucket, monetary, campaign)
    if not ok:
        return {"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": reasons}
    p = 0.0 if probability is None else float(probability)
    v = 0.0 if monetary is None else float(monetary)
    cost = float(campaign.get("cost_per_contact", 0.0) or 0.0)
    ev = round(p * v - cost, 4)
    return {"eligible": True, "score": ev, "expected_value": ev,
            "reasons": reasons + [f"očekivana vrednost = {p}*{v} - {cost} = {ev}"]}


def select_target_customers(profiles, campaign):
    if profiles is None or len(profiles) == 0:
        return pd.DataFrame()
    keep, why = [], []
    for r in profiles.itertuples(index=False):
        ok, reasons = _eligibility(getattr(r, "probability", None), getattr(r, "segment", None),
                                   getattr(r, "rfm_bucket", None), getattr(r, "monetary", None), campaign)
        keep.append(ok); why.append(reasons if ok else [])
    out = profiles.assign(selected_reasons=why)[keep]
    return out.sort_values("user_id").reset_index(drop=True)


def rank_target_customers(selected, campaign, limit=None):
    cols = ["rank", "user_id", "score", "expected_value", "probability", "segment", "rfm_bucket", "monetary", "reasons"]
    if selected is None or len(selected) == 0:
        return pd.DataFrame(columns=cols)
    sc = [score_customer(r.probability, r.segment, r.rfm_bucket, r.monetary, campaign)
          for r in selected.itertuples(index=False)]
    df = selected.assign(score=[s["score"] for s in sc], expected_value=[s["expected_value"] for s in sc],
                         reasons=[s["reasons"] for s in sc])
    df = df.sort_values(["score", "user_id"], ascending=[False, True]).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    mx = campaign.get("max_contacts")
    lim = mx if limit is None else (min(int(limit), int(mx)) if mx else int(limit))
    return (df.head(int(lim)) if lim is not None else df)[cols]


def rule_based_score(rfm_bucket, monetary):
    return BUCKET_PRIORITY.get(rfm_bucket, 0) * 1_000_000 + (0.0 if monetary is None else float(monetary))
