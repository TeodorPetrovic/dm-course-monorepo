"""Day 4 — TargetingService (ML profil ili rule fallback)."""
from __future__ import annotations

import joblib
import pandas as pd

from app.data.campaigns import get_campaign, load_campaigns
from app.ml.conversion import CONVERSION_FEATURE_COLUMNS, build_training_dataset
from app.ml.features import SEGMENT_FEATURE_COLUMNS, build_customer_features, scale_customer_features
from app.ml.segmentation import manual_rfm_buckets
from app.ml.targeting import compare_rule_vs_ml, rank_by_rule, rank_target_customers, select_target_customers
from app.services.conversion import ConversionService
from app.services.segmentation import SegmentationService, UntrainedModelError
from app.services.store import load_orders, require_events

PROFILE_COLUMNS = ["user_id", "segment", "rfm_bucket", "probability", "monetary", "frequency",
                   "recency_days", "aov", "conversion", "favorite_category"]


class UnknownCampaignError(KeyError):
    pass


def build_targeting_profile(events, orders, kmeans, seg_scaler, conv_model, conv_scaler, window_days=7):
    """Profil: P iz clean (pre cut-off) feature-a; segment/bucket/vrednost iz cele istorije.

    NAPOMENA: ``monetary``/``rfm_bucket``/``segment`` uključuju i window; to je
    „stanje sada" za odluku, ali NIJE pošteno za ex-post evaluaciju kampanje.
    """
    full = build_customer_features(events, orders)
    clean = build_training_dataset(events, orders, window_days, leaky=False)
    s_full, _ = scale_customer_features(full, SEGMENT_FEATURE_COLUMNS, scaler=seg_scaler)
    full["segment"] = [f"segment_{int(l)}" for l in kmeans.predict(s_full.to_numpy())]
    full["rfm_bucket"] = manual_rfm_buckets(full).values
    s_clean, _ = scale_customer_features(clean, CONVERSION_FEATURE_COLUMNS, scaler=conv_scaler)
    prob = pd.Series(conv_model.predict_proba(s_clean.to_numpy())[:, 1].round(4), index=clean["user_id"])
    prof = full[full["user_id"].isin(prob.index)].copy()
    prof["probability"] = prof["user_id"].map(prob)
    return prof[PROFILE_COLUMNS].reset_index(drop=True)


class TargetingService:
    def __init__(self, models=None):
        self.seg = SegmentationService(models); self.conv = ConversionService(models)

    def _ml_available(self) -> bool:
        return self.seg.is_trained() and self.conv.is_trained()

    def _ml_profile(self) -> pd.DataFrame:
        if not self._ml_available():
            raise UntrainedModelError("untrained_model")
        km, ss, _ = self.seg._load(); cm, cs, meta = self.conv._load()
        return build_targeting_profile(require_events(include_live=False), load_orders(), km, ss, cm, cs, meta["window_days"])

    def _rule_profile(self) -> pd.DataFrame:
        full = build_customer_features(require_events(include_live=False), load_orders())
        full["rfm_bucket"] = manual_rfm_buckets(full).values
        full["segment"] = None; full["probability"] = None
        return full[PROFILE_COLUMNS]

    def list_campaigns(self):
        return load_campaigns()

    def get_campaign(self, campaign_id: int) -> dict:
        c = get_campaign(campaign_id)
        if c is None:
            raise UnknownCampaignError(campaign_id)
        return c

    @staticmethod
    def _records(df):
        out = []
        for r in df.to_dict("records"):
            out.append({k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()})
        return out

    def recommended_audience(self, campaign_id: int, limit: int = 20, mode: str = "ml") -> dict:
        # TEACH d04: TargetingService.recommended_audience
        if mode not in ("ml", "rule"):
            raise ValueError("mode mora biti 'ml' ili 'rule'")
        if limit is not None and int(limit) < 1:
            raise ValueError("limit mora biti >= 1")
        c = self.get_campaign(campaign_id)
        fallback, reason = False, None
        if mode == "ml" and self._ml_available():
            prof = self._ml_profile()
            sel = select_target_customers(prof, c)
            aud = rank_target_customers(sel, c, limit)
        else:
            if mode == "ml":
                fallback, reason = True, "untrained_model"
            mode = "rule"
            prof = self._rule_profile()
            aud = rank_by_rule(prof, c, limit)
            sel = aud if limit is None else rank_by_rule(prof, c, None)
        lim = min(int(limit), int(c["max_contacts"])) if limit else c["max_contacts"]
        rules = {k: c[k] for k in ("target_segments", "eligible_buckets", "min_probability",
                                   "min_monetary", "cost_per_contact", "max_contacts")}
        rules["contact_limit"] = lim
        return {"campaign_id": c["campaign_id"], "campaign_name": c["name"], "mode": mode,
                "fallback": fallback, "fallback_reason": reason, "rules_applied": rules,
                "total_candidates": len(prof), "selected": len(sel), "returned": len(aud),
                "audience": self._records(aud)}
        # /TEACH

    def targeting_comparison(self, campaign_id: int, limit=None) -> dict:
        c = self.get_campaign(campaign_id)
        prof = self._ml_profile()
        cmp = compare_rule_vs_ml(prof, c, limit)
        return {"campaign_id": c["campaign_id"], "limit": cmp["limit"],
                "rule": self._records(cmp["rule"].head(20)), "ml": self._records(cmp["ml"].head(20)),
                "metrics": cmp["metrics"]}
