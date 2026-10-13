"""Day 2 — SegmentationService (pipeline + perzistencija + fallback-i)."""
from __future__ import annotations

import json

import joblib
import pandas as pd

from app.data.paths import models_dir
from app.ml.features import SEGMENT_FEATURE_COLUMNS, build_customer_features, scale_customer_features
from app.ml.segmentation import (assign_segment, compare_manual_vs_kmeans, evaluate_k_range,
                                 manual_rfm_buckets, profile_segments, train_segmentation_model)
from app.services.store import load_orders, require_events


class UntrainedModelError(RuntimeError):
    pass


class SegmentationService:
    MODEL, SCALER, META = "segment_kmeans.joblib", "segment_scaler.joblib", "segment_meta.json"

    def __init__(self, models=None):
        self.dir = models or models_dir()

    def is_trained(self) -> bool:
        return all((self.dir / f).exists() for f in (self.MODEL, self.SCALER, self.META))

    def train(self, k: int = 4, random_state: int = 42) -> dict:
        # TEACH d02: SegmentationService.train
        if not isinstance(k, int) or not 2 <= k <= 10:
            raise ValueError("k mora biti ceo broj u [2, 10]")
        events = require_events(include_live=False); orders = load_orders()
        feats = build_customer_features(events, orders)
        scaled, scaler = scale_customer_features(feats, SEGMENT_FEATURE_COLUMNS)
        res = train_segmentation_model(scaled, k=k, random_state=random_state)
        profiles = profile_segments(feats, res.labels, scaled)
        manual = manual_rfm_buckets(feats)
        cmp = compare_manual_vs_kmeans(feats, res.labels, manual)
        reference = str(pd.to_datetime(pd.concat([events["timestamp"], orders["timestamp"]])).max())
        meta = {"k": k, "silhouette": res.silhouette, "n_customers": len(feats),
                "reference": reference, "feature_columns": SEGMENT_FEATURE_COLUMNS,
                "segments": profiles.to_dict("records"),
                "comparison": {"ari": cmp["ari"], "dominant_cluster": cmp["dominant_cluster"]},
                "k_silhouette": evaluate_k_range(scaled).to_dict("records")}
        joblib.dump(res.model, self.dir / self.MODEL); joblib.dump(scaler, self.dir / self.SCALER)
        (self.dir / self.META).write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
        return meta
        # /TEACH

    def _load(self):
        if not self.is_trained():
            raise UntrainedModelError("untrained_model")
        return (joblib.load(self.dir / self.MODEL), joblib.load(self.dir / self.SCALER),
                json.loads((self.dir / self.META).read_text()))

    def get_segments(self) -> dict:
        _, _, meta = self._load()
        return meta

    def get_customer_segment(self, user_id: int) -> dict:
        model, scaler, meta = self._load()
        events = require_events(); orders = load_orders()
        ev = events[events["user_id"] == user_id]; od = orders[orders["user_id"] == user_id]
        if len(ev) == 0 and len(od) == 0:
            return {"user_id": user_id, "segment": "unsegmented", "segment_id": None,
                    "fallback": True, "reason": "no_history"}
        feats = build_customer_features(ev, od, reference=pd.Timestamp(meta["reference"]))
        scaled, _ = scale_customer_features(feats, SEGMENT_FEATURE_COLUMNS, scaler=scaler)
        label = assign_segment(model, scaled.iloc[0])
        return {"user_id": user_id, "segment": label, "segment_id": int(label.split("_")[1]),
                "fallback": False, "reason": None}
