"""Day 4 — targeting: predikcija (ulaz) -> odluka (očekivana vrednost pod pravilima)."""
from __future__ import annotations

from typing import Optional

import pandas as pd

BUCKET_PRIORITY = {"champions": 4, "loyal": 3, "at_risk": 2, "dormant": 1}
AUDIENCE_COLUMNS = ["rank", "user_id", "score", "expected_value", "probability", "segment",
                    "rfm_bucket", "monetary", "reasons"]


def _nan(v):
    return v is None or (isinstance(v, float) and v != v)


def evaluate_campaign_rules(probability, segment, rfm_bucket, monetary, campaign: dict):
    """JEDINA definicija eligibilnosti (deli je select/rank). Vraća (eligible, reasons)."""
    reasons: list[str] = []
    ts = campaign.get("target_segments") or []
    if ts:
        ok = segment is not None and segment in set(ts)
        reasons.append(f"segment {segment} {'je' if ok else 'nije'} u ciljanim segmentima")
        if not ok:
            return False, reasons
    eb = campaign.get("eligible_buckets") or []
    if eb:
        ok = rfm_bucket is not None and rfm_bucket in set(eb)
        reasons.append(f"rfm_bucket {rfm_bucket} {'je' if ok else 'nije'} u dozvoljenim bucketima")
        if not ok:
            return False, reasons
    mp = float(campaign.get("min_probability") or 0.0)
    if mp > 0:
        if _nan(probability):
            reasons.append("nema verovatnoće (model nije dostupan)")
            return False, reasons
        ok = float(probability) >= mp
        reasons.append(f"P({float(probability):.4f}) {'>=' if ok else '<'} prag {mp:.4f}")
        if not ok:
            return False, reasons
    mm = float(campaign.get("min_monetary") or 0.0)
    if mm > 0:
        v = 0.0 if _nan(monetary) else float(monetary)
        ok = v >= mm
        reasons.append(f"vrednost {v:.2f} {'>=' if ok else '<'} min {mm:.2f}")
        if not ok:
            return False, reasons
    return True, reasons


def score_customer(probability, segment, rfm_bucket, monetary, campaign: dict) -> dict:
    # TEACH d04: score_customer
    ok, reasons = evaluate_campaign_rules(probability, segment, rfm_bucket, monetary, campaign)
    if not ok:
        return {"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": reasons}
    p = 0.0 if _nan(probability) else float(probability)
    v = 0.0 if _nan(monetary) else float(monetary)
    cost = float(campaign.get("cost_per_contact") or 0.0)
    ev = round(p * v - cost, 4)
    reasons = reasons + [f"očekivana vrednost = {p:.4f}×{v:.2f} − {cost:.2f} = {ev:.4f}"]
    return {"eligible": True, "score": ev, "expected_value": ev, "reasons": reasons}
    # /TEACH


def _required(campaign):
    req = []
    if campaign.get("target_segments"):
        req.append("segment")
    if campaign.get("eligible_buckets"):
        req.append("rfm_bucket")
    if float(campaign.get("min_probability") or 0) > 0:
        req.append("probability")
    if float(campaign.get("min_monetary") or 0) > 0:
        req.append("monetary")
    return req


def select_target_customers(profiles: pd.DataFrame, campaign: dict) -> pd.DataFrame:
    # TEACH d04: select_target_customers
    if profiles is None or len(profiles) == 0:
        return pd.DataFrame()
    missing = [c for c in _required(campaign) if c not in profiles.columns]
    if missing:
        raise ValueError(f"aktivno pravilo bez podataka: nedostaju kolone {missing}")
    keep, reasons = [], []
    for r in profiles.itertuples(index=False):
        d = r._asdict()
        ok, rs = evaluate_campaign_rules(d.get("probability"), d.get("segment"), d.get("rfm_bucket"),
                                         d.get("monetary"), campaign)
        keep.append(ok); reasons.append(rs if ok else [])
    out = profiles.copy()
    out["selected_reasons"] = reasons
    return out[keep].sort_values("user_id").reset_index(drop=True)
    # /TEACH


def effective_limit(limit: Optional[int], campaign: dict) -> int:
    mc = campaign.get("max_contacts")
    if limit is None:
        return int(mc) if mc else 10**9
    if int(limit) < 1:
        raise ValueError("limit mora biti >= 1")
    return min(int(limit), int(mc)) if mc else int(limit)


def rank_target_customers(selected: pd.DataFrame, campaign: dict, limit: Optional[int] = None) -> pd.DataFrame:
    # TEACH d04: rank_target_customers
    if selected is None or len(selected) == 0:
        return pd.DataFrame(columns=AUDIENCE_COLUMNS)
    df = selected.copy()
    for c in ("probability", "segment"):
        if c not in df.columns:
            df[c] = None
    scores = [score_customer(r.probability, r.segment, r.rfm_bucket, r.monetary, campaign)
              for r in df.itertuples(index=False)]
    df["score"] = [s["score"] for s in scores]
    df["expected_value"] = [s["expected_value"] for s in scores]
    df["reasons"] = [s["reasons"] for s in scores]
    df = df.sort_values(["score", "user_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df.head(effective_limit(limit, campaign))[AUDIENCE_COLUMNS].reset_index(drop=True)
    # /TEACH


def rule_based_score(rfm_bucket: Optional[str], monetary: Optional[float]) -> float:
    v = 0.0 if _nan(monetary) else float(monetary)
    return BUCKET_PRIORITY.get(rfm_bucket, 0) * 1_000_000 + v


def rank_by_rule(profiles: pd.DataFrame, campaign: dict, limit: Optional[int] = None) -> pd.DataFrame:
    """Rule baseline: samo bucket/vrednost pravila (bez ML kolona) + rule skor."""
    rule_c = {k: v for k, v in campaign.items()}
    rule_c["target_segments"] = []; rule_c["min_probability"] = 0.0
    if profiles is None or len(profiles) == 0:
        return pd.DataFrame(columns=AUDIENCE_COLUMNS)
    df = select_target_customers(profiles, rule_c)
    if len(df) == 0:
        return pd.DataFrame(columns=AUDIENCE_COLUMNS)
    df["score"] = [round(rule_based_score(b, m), 4) for b, m in zip(df["rfm_bucket"], df["monetary"])]
    df["expected_value"] = None
    df["reasons"] = [rs + [f"rule skor = prioritet({b})×1e6 + vrednost"] for rs, b in zip(df["selected_reasons"], df["rfm_bucket"])]
    for c in ("probability", "segment"):
        if c not in df.columns:
            df[c] = None
    df = df.sort_values(["score", "user_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df.head(effective_limit(limit, campaign))[AUDIENCE_COLUMNS].reset_index(drop=True)


def _audience_metrics(aud: pd.DataFrame, profiles: pd.DataFrame, cost: float) -> dict:
    p = profiles.set_index("user_id")
    ids = list(aud["user_id"])
    probs = p.loc[ids, "probability"].astype(float) if ids else pd.Series(dtype=float)
    vals = p.loc[ids, "monetary"].astype(float) if ids else pd.Series(dtype=float)
    return {"size": len(ids),
            "expected_conversions": round(float(probs.sum()), 4),
            "expected_profit": round(float((probs * vals - cost).sum()), 4),
            "avg_probability": round(float(probs.mean()), 4) if ids else 0.0}


def compare_rule_vs_ml(profiles: pd.DataFrame, campaign: dict, limit: Optional[int] = None) -> dict:
    # TEACH d04: compare_rule_vs_ml
    lim = effective_limit(limit, campaign)
    rule = rank_by_rule(profiles, campaign, lim)
    ml = rank_target_customers(select_target_customers(profiles, campaign), campaign, lim)
    cost = float(campaign.get("cost_per_contact") or 0.0)
    mr, mm = _audience_metrics(rule, profiles, cost), _audience_metrics(ml, profiles, cost)
    a, b = set(rule["user_id"]), set(ml["user_id"])
    union = a | b
    return {"campaign_id": campaign["campaign_id"], "limit": lim, "rule": rule, "ml": ml,
            "metrics": {"rule": mr, "ml": mm,
                        "lift_expected_conversions": round(mm["expected_conversions"] / mr["expected_conversions"], 2) if mr["expected_conversions"] else None,
                        "overlap": len(a & b), "jaccard": round(len(a & b) / len(union), 3) if union else 0.0}}
    # /TEACH
