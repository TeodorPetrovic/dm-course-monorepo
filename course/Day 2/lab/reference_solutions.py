"""Referentno rešenje Day 2 lab-a."""
from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler

from starter import SEGMENT_FEATURE_COLUMNS  # noqa: F401


def calculate_rfm(events_df, orders_df=None):
    cols = ["user_id", "recency_days", "frequency", "monetary"]
    orders_df = pd.DataFrame(columns=["user_id", "timestamp", "total_price"]) if orders_df is None else orders_df
    if len(events_df) == 0 and len(orders_df) == 0:
        return pd.DataFrame(columns=cols)
    ev_ts = pd.to_datetime(events_df["timestamp"]) if len(events_df) else pd.Series(dtype="datetime64[ns]")
    od_ts = pd.to_datetime(orders_df["timestamp"]) if len(orders_df) else pd.Series(dtype="datetime64[ns]")
    ref = pd.concat([ev_ts, od_ts]).max()
    start = ev_ts.min() if len(ev_ts) else ref
    users = sorted(pd.concat([events_df["user_id"], orders_df["user_id"]]).dropna().astype(int).unique())
    last_act = events_df.assign(_t=ev_ts).groupby("user_id")["_t"].max() if len(events_df) else {}
    od = orders_df.assign(_t=od_ts, _p=pd.to_numeric(orders_df["total_price"], errors="coerce").fillna(0.0))
    g = od.groupby("user_id")
    cnt = (g["order_id"].nunique() if "order_id" in od.columns else g.size()) if len(od) else {}
    last_buy, freq, mon = (g["_t"].max(), cnt, g["_p"].sum()) if len(od) else ({}, {}, {})
    rows = []
    for u in users:
        lb, la = last_buy.get(u, pd.NaT), last_act.get(u, pd.NaT)
        rec = (ref - lb).days if pd.notna(lb) else (ref - la).days if pd.notna(la) else (ref - start).days + 1
        rows.append({"user_id": u, "recency_days": int(rec), "frequency": int(freq.get(u, 0)),
                     "monetary": round(float(mon.get(u, 0.0)), 2)})
    return pd.DataFrame(rows, columns=cols)


def scale_customer_features(features_df, feature_columns, scaler=None):
    missing = [c for c in feature_columns if c not in features_df.columns]
    if missing:
        raise ValueError(f"nedostaju kolone: {missing}")
    X = features_df[feature_columns].astype(float)
    if scaler is None:
        scaler = StandardScaler().fit(X)
    return pd.DataFrame(scaler.transform(X), columns=feature_columns, index=features_df.index), scaler


def assign_segment(model, scaled_row, fallback_label="unsegmented"):
    if model is None:
        raise ValueError("model not trained")
    if scaled_row is None or len(scaled_row) == 0:
        return fallback_label
    X = pd.DataFrame([list(scaled_row.values)]).to_numpy()
    return f"segment_{int(model.predict(X)[0])}"
