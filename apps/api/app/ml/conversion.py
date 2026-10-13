"""Day 3 — predikcija kupovine (nadgledano učenje) + leakage vežba."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split

from app.ml.features import build_customer_features, reference_time, scale_customer_features

CONVERSION_FEATURE_COLUMNS = ["recency_days", "frequency", "monetary", "product_views",
                              "cart_adds", "sessions", "aov", "conversion"]
LABEL_COLUMN = "will_purchase"
MODEL_TYPES = ("logistic_regression", "random_forest")


def compute_cutoff(events, orders, window_days: int = 7):
    ref = reference_time(events, orders)
    return ref, ref - pd.Timedelta(days=window_days)


def build_training_dataset(events: pd.DataFrame, orders: pd.DataFrame, window_days: int = 7,
                           leaky: bool = False) -> pd.DataFrame:
    """Labeled dataset: feature-i (clean = pre cut-off-a) + labela iz window-a."""
    # TEACH d03: build_training_dataset
    if window_days <= 0:
        raise ValueError("window_days mora biti > 0")
    if len(events) == 0 and len(orders) == 0:
        return pd.DataFrame(columns=["user_id"] + CONVERSION_FEATURE_COLUMNS + [LABEL_COLUMN])
    ref, cutoff = compute_cutoff(events, orders, window_days)
    ots = pd.to_datetime(orders["timestamp"])
    buyers = set(pd.to_numeric(orders.loc[(ots >= cutoff) & (ots <= ref), "user_id"]).astype(int))
    if leaky:
        feats = build_customer_features(events, orders, reference=ref)
    else:
        ev = events[pd.to_datetime(events["timestamp"]) < cutoff]
        od = orders[ots < cutoff]
        feats = build_customer_features(ev, od, reference=cutoff)
    feats = feats.drop(columns=["favorite_category"], errors="ignore")
    feats[LABEL_COLUMN] = feats["user_id"].isin(buyers).astype(int)
    return feats[["user_id"] + CONVERSION_FEATURE_COLUMNS + [LABEL_COLUMN]].reset_index(drop=True)
    # /TEACH


def split_dataset(df: pd.DataFrame, test_size: float = 0.3, random_state: int = 42):
    # TEACH d03: split_dataset
    if not 0 < test_size < 1:
        raise ValueError("test_size mora biti u (0, 1)")
    tr, te = train_test_split(df, test_size=test_size, random_state=random_state,
                              stratify=df[LABEL_COLUMN])
    return tr.reset_index(drop=True), te.reset_index(drop=True)
    # /TEACH


def train_conversion_model(X_train, y_train, model_type: str = "logistic_regression",
                           random_state: int = 42):
    # TEACH d03: train_conversion_model
    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=1000, random_state=random_state)
    elif model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=200, random_state=random_state)
    else:
        raise ValueError(f"nepoznat model_type: {model_type!r}")
    return model.fit(X_train, y_train)
    # /TEACH


def _metrics(y, pred) -> dict:
    # TEACH d03: _metrics
    y = np.asarray(y); pred = np.asarray(pred)
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
        "n": int(len(y)),
        "positive_class": 1,
    }
    # /TEACH


def evaluate_model(model, X, y) -> dict:
    return _metrics(y, model.predict(X))


def majority_class_baseline(y) -> dict:
    # TEACH d03: majority_class_baseline
    y = np.asarray(y)
    maj = int(np.bincount(y.astype(int), minlength=2).argmax()) if len(y) else 0
    out = _metrics(y, np.full(len(y), maj))
    out["majority_class"] = maj
    return out
    # /TEACH


def predict_conversion_probability(model, scaled_row) -> float:
    # TEACH d03: predict_conversion_probability
    if model is None:
        raise ValueError("model not trained")
    if scaled_row is None or len(scaled_row) == 0:
        raise ValueError("prazna feature vrsta")
    x = np.asarray(scaled_row, dtype=float).reshape(1, -1)
    return round(float(model.predict_proba(x)[0, 1]), 4)
    # /TEACH


def run_leakage_exercise(events, orders, window_days: int = 7, test_size: float = 0.3,
                         random_state: int = 42, model_type: str = "logistic_regression") -> dict:
    """Isti model, isti split (po korisnicima clean skupa): clean vs leaky."""
    clean = build_training_dataset(events, orders, window_days, leaky=False)
    leaky = build_training_dataset(events, orders, window_days, leaky=True)
    leaky = leaky[leaky["user_id"].isin(set(clean["user_id"]))].reset_index(drop=True)
    tr, te = split_dataset(clean, test_size, random_state)
    tr_u, te_u = set(tr["user_id"]), set(te["user_id"])

    def fit_eval(df):
        a = df[df["user_id"].isin(tr_u)].sort_values("user_id").reset_index(drop=True)
        a = df.set_index("user_id").loc[tr["user_id"]].reset_index()
        b = df.set_index("user_id").loc[te["user_id"]].reset_index()
        sa, sc = scale_customer_features(a, CONVERSION_FEATURE_COLUMNS)
        sb, _ = scale_customer_features(b, CONVERSION_FEATURE_COLUMNS, scaler=sc)
        m = train_conversion_model(sa.to_numpy(), a[LABEL_COLUMN].to_numpy(), model_type, random_state)
        return evaluate_model(m, sb.to_numpy(), b[LABEL_COLUMN].to_numpy())

    c, l = fit_eval(clean), fit_eval(leaky)
    return {"model_type": model_type, "window_days": window_days, "test_size": test_size,
            "random_state": random_state, "n_test": len(te), "clean": c, "leaky": l,
            "delta_f1": round(l["f1"] - c["f1"], 4)}
