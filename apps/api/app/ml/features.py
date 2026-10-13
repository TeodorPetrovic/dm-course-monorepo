"""Day 2 — feature-i po korisniku (RFM + brojači) i skaliranje."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

SEGMENT_FEATURE_COLUMNS = ["recency_days", "frequency", "monetary", "aov", "conversion"]
FEATURE_COLUMNS = ["user_id", "recency_days", "frequency", "monetary", "product_views",
                   "cart_adds", "sessions", "aov", "conversion", "favorite_category"]


def _ts(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def reference_time(events: pd.DataFrame, orders: Optional[pd.DataFrame] = None) -> pd.Timestamp:
    cands = []
    if events is not None and len(events):
        cands.append(_ts(events["timestamp"]).max())
    if orders is not None and len(orders):
        cands.append(_ts(orders["timestamp"]).max())
    cands = [c for c in cands if pd.notna(c)]
    if not cands:
        raise ValueError("nema vremenskih žigova za referencu")
    return max(cands)


def calculate_rfm(events: pd.DataFrame, orders: Optional[pd.DataFrame] = None,
                  reference: Optional[pd.Timestamp] = None, user_ids=None) -> pd.DataFrame:
    """R/F/M po korisniku sa eksplicitnim fallback-ovima (vidi lekciju Day 2)."""
    cols = ["user_id", "recency_days", "frequency", "monetary"]
    if (events is None or len(events) == 0) and (orders is None or len(orders) == 0):
        return pd.DataFrame(columns=cols)
    orders = orders if orders is not None else pd.DataFrame(columns=["user_id", "total_price", "timestamp"])
    ref = pd.Timestamp(reference) if reference is not None else reference_time(events, orders)
    ev_users = pd.to_numeric(events["user_id"], errors="coerce").dropna().astype(int) if len(events) else pd.Series(dtype=int)
    if user_ids is None:
        users = sorted(set(ev_users) | set(pd.to_numeric(orders["user_id"]).astype(int)))
    else:
        users = sorted(int(u) for u in user_ids)
    out = pd.DataFrame({"user_id": users}).set_index("user_id")
    if len(orders):
        o = orders.assign(_t=_ts(orders["timestamp"]), user_id=pd.to_numeric(orders["user_id"]).astype(int))
        g = o.groupby("user_id")
        # frequency = broj porudžbina (stavke iste porudžbine dele order_id); bez order_id -> broj redova
        out["frequency"] = g["order_id"].nunique() if "order_id" in o.columns else g.size()
        out["monetary"] = g["total_price"].sum()
        last_buy = g["_t"].max()
    else:
        out["frequency"] = 0; out["monetary"] = 0.0; last_buy = pd.Series(dtype="datetime64[ns]")
    out["frequency"] = out["frequency"].fillna(0).astype(int)
    out["monetary"] = out["monetary"].fillna(0.0).astype(float).round(2)
    if len(events):
        e = events.assign(_t=_ts(events["timestamp"]), user_id=pd.to_numeric(events["user_id"], errors="coerce"))
        last_act = e.dropna(subset=["user_id"]).groupby(e["user_id"].dropna().astype(int))["_t"].max()
        earliest = e["_t"].min()
    else:
        last_act = pd.Series(dtype="datetime64[ns]"); earliest = ref
    last = last_buy.reindex(out.index).fillna(last_act.reindex(out.index))
    cold = int((ref - earliest).days) + 1
    rec = (ref - last).dt.days
    out["recency_days"] = rec.fillna(cold).astype(int)
    return out.reset_index()[cols]


def build_customer_features(events: pd.DataFrame, orders: Optional[pd.DataFrame] = None,
                            reference: Optional[pd.Timestamp] = None, user_ids=None) -> pd.DataFrame:
    """RFM + brojači + AOV + konverzija + omiljena kategorija (po korisniku)."""
    rfm = calculate_rfm(events, orders, reference=reference, user_ids=user_ids)
    if len(rfm) == 0:
        return pd.DataFrame(columns=FEATURE_COLUMNS)
    f = rfm.set_index("user_id")
    e = events.assign(user_id=pd.to_numeric(events["user_id"], errors="coerce")).dropna(subset=["user_id"])
    e["user_id"] = e["user_id"].astype(int)
    et = e["event_type"]
    f["product_views"] = e[et == "product_view"].groupby("user_id").size().reindex(f.index).fillna(0).astype(int)
    f["cart_adds"] = e[et == "add_to_cart"].groupby("user_id").size().reindex(f.index).fillna(0).astype(int)
    f["sessions"] = e.groupby("user_id")["user_session"].nunique().reindex(f.index).fillna(0).astype(int)
    buy_sess = e[et == "purchase"].groupby("user_id")["user_session"].nunique().reindex(f.index).fillna(0)
    f["aov"] = np.where(f["frequency"] > 0, f["monetary"] / f["frequency"].replace(0, 1), 0.0).round(2)
    f["conversion"] = np.where(f["sessions"] > 0, buy_sess / f["sessions"].replace(0, 1), 0.0).round(4)
    v = e[et == "product_view"].dropna(subset=["category_id"])
    if len(v):
        cnt = v.groupby(["user_id", "category_id"]).size().reset_index(name="n")
        cnt = cnt.sort_values(["user_id", "n", "category_id"], ascending=[True, False, True])
        fav = cnt.drop_duplicates("user_id").set_index("user_id")["category_id"].astype(float)
        f["favorite_category"] = fav.reindex(f.index)
    else:
        f["favorite_category"] = np.nan
    return f.reset_index()[FEATURE_COLUMNS]


def scale_customer_features(features: pd.DataFrame, feature_columns=None, scaler=None):
    """``scaler=None`` -> fit; dat scaler -> **transform only** (nikad refit)."""
    cols = list(feature_columns or SEGMENT_FEATURE_COLUMNS)
    missing = [c for c in cols if c not in features.columns]
    if missing:
        raise ValueError(f"nedostaju kolone: {missing}")
    X = features[cols].astype(float)
    if scaler is None:
        scaler = StandardScaler().fit(X.values)
    scaled = pd.DataFrame(scaler.transform(X.values), columns=cols, index=features.index)
    return scaled, scaler
