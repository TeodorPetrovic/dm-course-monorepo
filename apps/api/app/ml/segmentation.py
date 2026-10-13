"""Day 2 — K-Means segmentacija, profilisanje i ručni RFM baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from app.ml.features import SEGMENT_FEATURE_COLUMNS

RFM_BUCKETS = [("dormant", 3, 6), ("at_risk", 7, 9), ("loyal", 10, 12), ("champions", 13, 15)]
BUCKET_ORDER = [b[0] for b in RFM_BUCKETS]


@dataclass
class SegmentationResult:
    model: KMeans
    labels: np.ndarray
    silhouette: float
    k: int
    feature_columns: list = field(default_factory=lambda: list(SEGMENT_FEATURE_COLUMNS))


def _X(scaled) -> np.ndarray:
    if isinstance(scaled, pd.DataFrame):
        cols = [c for c in SEGMENT_FEATURE_COLUMNS if c in scaled.columns] or list(scaled.columns)
        return scaled[cols].to_numpy(dtype=float)
    return np.asarray(scaled, dtype=float)


def train_segmentation_model(scaled, k: int = 4, random_state: int = 42, n_init: int = 10) -> SegmentationResult:
    X = _X(scaled)
    if not isinstance(k, (int, np.integer)) or k < 2:
        raise ValueError("k mora biti ceo broj >= 2")
    if len(X) <= k:
        raise ValueError("premalo korisnika za k klastera")
    model = KMeans(n_clusters=int(k), random_state=random_state, n_init=n_init).fit(X)
    sil = round(float(silhouette_score(X, model.labels_)), 4)
    return SegmentationResult(model=model, labels=model.labels_.copy(), silhouette=sil, k=int(k))


def evaluate_k_range(scaled, k_range=range(2, 7), random_state: int = 42) -> pd.DataFrame:
    rows = [{"k": k, "silhouette": train_segmentation_model(scaled, k, random_state).silhouette}
            for k in k_range]
    return pd.DataFrame(rows)


def assign_segment(model, scaled_row, fallback_label: str = "unsegmented") -> str:
    if model is None:
        raise ValueError("model not trained")
    if scaled_row is None or len(scaled_row) == 0:
        return fallback_label
    x = np.asarray(scaled_row, dtype=float).reshape(1, -1)
    return f"segment_{int(model.predict(x)[0])}"


def _describe(row: pd.Series, overall: pd.Series) -> str:
    parts = []
    for c in ["recency_days", "frequency", "monetary", "aov", "conversion"]:
        if c not in row:
            continue
        if row[c] > overall[c] * 1.25 + 1e-9:
            parts.append(f"{c}+")
        elif row[c] < overall[c] * 0.75 - 1e-9:
            parts.append(f"{c}-")
    return " ".join(parts) or "prosečan"


def profile_segments(features: pd.DataFrame, labels, scaled_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    df = features.copy()
    df["segment"] = [f"segment_{int(l)}" for l in labels]
    num = ["recency_days", "frequency", "monetary", "product_views", "cart_adds", "sessions", "aov", "conversion"]
    num = [c for c in num if c in df.columns]
    overall = df[num].mean()
    rows = []
    for seg, g in df.groupby("segment", sort=True):
        means = g[num].mean().round(3)
        fav = g["favorite_category"].dropna().mode() if "favorite_category" in g else pd.Series(dtype=float)
        rows.append({"segment": seg, "count": len(g), "share": round(len(g) / len(df), 4),
                     **means.to_dict(),
                     "favorite_category": None if fav.empty else int(fav.iloc[0]),
                     "profile": _describe(means, overall)})
    return pd.DataFrame(rows)


def _rank_score(s: pd.Series, ascending: bool = True) -> pd.Series:
    """Rank-percentil -> skor 1..5 (robustno na iskrivljene raspodele)."""
    pct = s.rank(method="average", pct=True, ascending=ascending)
    return np.ceil(pct * 5).clip(1, 5).astype(int)


def _value_score(s: pd.Series) -> pd.Series:
    """F/M skor: 0 (nije kupovao) -> 1; kupci se rangiraju MEĐUSOBNO u 2..5.

    Bez ovoga ~80% nula dobije prosečan rang (~0.4 -> skor 3), pa niko ne može u ``dormant``."""
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    out = pd.Series(1, index=s.index, dtype=int)
    pos = s > 0
    if pos.any():
        pct = s[pos].rank(method="average", pct=True)
        out[pos] = (np.ceil(pct * 4).clip(1, 4) + 1).astype(int)
    return out


def manual_rfm_buckets(features: pd.DataFrame) -> pd.Series:
    r = _rank_score(features["recency_days"], ascending=False)  # manji recency = bolje
    f = _value_score(features["frequency"])
    m = _value_score(features["monetary"])
    total = r + f + m
    bucket = pd.cut(total, bins=[2, 6, 9, 12, 15], labels=BUCKET_ORDER).astype(str)
    return pd.Series(bucket.values, index=features.index, name="rfm_bucket")


def compare_manual_vs_kmeans(features: pd.DataFrame, labels, manual: pd.Series) -> dict:
    seg = pd.Series([f"segment_{int(l)}" for l in labels], index=features.index)
    ct = pd.crosstab(manual, seg)
    dom = {}
    for b in BUCKET_ORDER:
        if b in ct.index:
            row = ct.loc[b]
            dom[b] = {"cluster": row.idxmax(), "share": round(float(row.max() / row.sum()), 3),
                      "count": int(row.sum())}
    return {"ari": round(float(adjusted_rand_score(manual, seg)), 3),
            "crosstab": ct.to_dict(), "dominant_cluster": dom}
