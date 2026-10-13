"""Day 3 — ConversionService (pipeline + perzistencija + fallback-i)."""
from __future__ import annotations

import json

import joblib
import pandas as pd

from app.data.paths import models_dir
from app.ml.conversion import (CONVERSION_FEATURE_COLUMNS, LABEL_COLUMN, MODEL_TYPES,
                               build_training_dataset, compute_cutoff, evaluate_model,
                               majority_class_baseline, predict_conversion_probability,
                               run_leakage_exercise, split_dataset, train_conversion_model)
from app.ml.features import build_customer_features, scale_customer_features
from app.services.segmentation import UntrainedModelError
from app.services.store import load_orders, require_events


class ConversionService:
    MODEL, SCALER, META = "conversion_model.joblib", "conversion_scaler.joblib", "conversion_meta.json"

    def __init__(self, models=None):
        self.dir = models or models_dir()

    def is_trained(self) -> bool:
        return all((self.dir / f).exists() for f in (self.MODEL, self.SCALER, self.META))

    def train(self, model_type: str = "logistic_regression", window_days: int = 7,
              test_size: float = 0.3, random_state: int = 42) -> dict:
        # TEACH d03+: ConversionService.train
        if model_type not in MODEL_TYPES:
            raise ValueError(f"model_type mora biti jedan od {MODEL_TYPES}")
        if not 1 <= int(window_days) <= 28 or not 0 < test_size < 1:
            raise ValueError("nevalidni parametri (window_days 1..28, test_size u (0,1))")
        events = require_events(include_live=False); orders = load_orders()
        ds = build_training_dataset(events, orders, window_days, leaky=False)
        if ds[LABEL_COLUMN].nunique() < 2:  # npr. live događaj sa današnjim timestamp-om pomeri referencu
            raise ValueError("label prozor ima samo jednu klasu — proveri timestamp-ove (reference = max timestamp)")
        tr, te = split_dataset(ds, test_size, random_state)
        s_tr, scaler = scale_customer_features(tr, CONVERSION_FEATURE_COLUMNS)
        s_te, _ = scale_customer_features(te, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        model = train_conversion_model(s_tr.to_numpy(), tr[LABEL_COLUMN].to_numpy(), model_type, random_state)
        metrics = evaluate_model(model, s_te.to_numpy(), te[LABEL_COLUMN].to_numpy())
        ref, cutoff = compute_cutoff(events, orders, window_days)
        meta = {"model_type": model_type, "window_days": window_days, "test_size": test_size,
                "random_state": random_state, "reference": str(ref), "cutoff": str(cutoff),
                "n_train": len(tr), "n_test": len(te), "base_rate": round(float(ds[LABEL_COLUMN].mean()), 4),
                "metrics": metrics, "baseline": majority_class_baseline(te[LABEL_COLUMN].to_numpy()),
                "leakage": run_leakage_exercise(events, orders, window_days, test_size, random_state, model_type),
                "feature_columns": CONVERSION_FEATURE_COLUMNS}
        joblib.dump(model, self.dir / self.MODEL); joblib.dump(scaler, self.dir / self.SCALER)
        (self.dir / self.META).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        return meta
        # /TEACH

    def _load(self):
        if not self.is_trained():
            raise UntrainedModelError("untrained_model")
        return (joblib.load(self.dir / self.MODEL), joblib.load(self.dir / self.SCALER),
                json.loads((self.dir / self.META).read_text()))

    def get_status(self) -> dict:
        _, _, meta = self._load()
        return {k: meta[k] for k in ("model_type", "window_days", "reference", "cutoff", "n_train",
                                     "n_test", "base_rate", "metrics", "baseline")}

    def get_customer_probability(self, user_id: int) -> dict:
        # TEACH d03: ConversionService.get_customer_probability
        model, scaler, meta = self._load()  # model se UČITAVA SA DISKA (persistencija)
        events = require_events(); orders = load_orders()
        cutoff = pd.Timestamp(meta["cutoff"])
        ev = events[(events["user_id"] == user_id) & (pd.to_datetime(events["timestamp"]) < cutoff)]
        od = orders[(orders["user_id"] == user_id) & (pd.to_datetime(orders["timestamp"]) < cutoff)]
        if len(ev) == 0 and len(od) == 0:
            return {"user_id": user_id, "probability": meta["base_rate"], "fallback": True,
                    "reason": "no_history", "base_rate": meta["base_rate"]}
        feats = build_customer_features(ev, od, reference=cutoff)
        row, _ = scale_customer_features(feats, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        return {"user_id": user_id, "probability": predict_conversion_probability(model, row.iloc[0]),
                "fallback": False, "reason": None, "base_rate": meta["base_rate"]}
        # /TEACH
