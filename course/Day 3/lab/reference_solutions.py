"""Referentno rešenje Day 3 lab-a."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from starter import FEATURE_COLUMNS, LABEL_COLUMN, build_features, train_conversion_model  # noqa: F401


def build_training_dataset(events_df, orders_df=None, window_days=7, leaky=False):
    orders_df = pd.DataFrame(columns=["user_id", "timestamp", "total_price"]) if orders_df is None else orders_df
    ev_t = pd.to_datetime(events_df["timestamp"]); od_t = pd.to_datetime(orders_df["timestamp"])
    reference = pd.concat([ev_t, od_t]).max()
    cutoff = reference - pd.Timedelta(days=window_days)
    buyers = set(orders_df.loc[(od_t >= cutoff) & (od_t <= reference), "user_id"].astype(int))
    if leaky:
        feats = build_features(events_df, orders_df, reference=reference)
    else:
        feats = build_features(events_df[ev_t < cutoff], orders_df[od_t < cutoff], reference=cutoff)
    feats[LABEL_COLUMN] = feats["user_id"].isin(buyers).astype(int)
    return feats.sort_values("user_id").reset_index(drop=True)


def split_dataset(df, test_size=0.3, random_state=42):
    if LABEL_COLUMN not in df.columns:
        raise ValueError(f"nedostaje {LABEL_COLUMN}")
    tr, te = train_test_split(df, test_size=test_size, random_state=random_state, stratify=df[LABEL_COLUMN])
    return tr.reset_index(drop=True), te.reset_index(drop=True)


def evaluate_model(model, X, y):
    p = model.predict(np.asarray(X)); y = np.asarray(y)
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    r4 = lambda v: round(float(v), 4)
    return {"accuracy": r4(accuracy_score(y, p)), "precision": r4(precision_score(y, p, zero_division=0)),
            "recall": r4(recall_score(y, p, zero_division=0)), "f1": r4(f1_score(y, p, zero_division=0)),
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]], "n": int(len(y))}


def predict_conversion_probability(model, scaled_row):
    if model is None:
        raise ValueError("model not trained")
    if scaled_row is None or len(scaled_row) == 0:
        raise ValueError("prazna feature vrsta")
    X = np.asarray(scaled_row, dtype=float).reshape(1, -1)
    return round(float(model.predict_proba(X)[0, 1]), 4)
