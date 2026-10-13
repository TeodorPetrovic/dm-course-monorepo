"""Day 12 — IntegratedPlatformService: orkestracija Day 1–11 modula sa fallback-om po modulu."""
from __future__ import annotations

import json

import pandas as pd

from app.data.paths import day_data
from app.ml.segmentation import manual_rfm_buckets
from app.services.store import get_store, load_orders, load_products_text

_REGISTRY_FILE = day_data(12, "module-registry.json")
MODULE_REGISTRY = [{k: v for k, v in m.items() if k != "available"}
                   for m in json.loads(_REGISTRY_FILE.read_text())["modules"]]
_BY_ID = {m["id"]: m for m in MODULE_REGISTRY}
SECTIONS = [("hero", "generative_ai"), ("recommended_for_you", "hybrid"), ("continue_session", "session"),
            ("similar_products", "embeddings"), ("bought_together", "collaborative"),
            ("seo_meta", "seo_template")]


def _cls(mid):
    return _BY_ID[mid]["class"]


class IntegratedPlatformService:
    def __init__(self):
        self.products = load_products_text()
        self.events = get_store().events_dataframe()
        self.orders = load_orders()
        self._svc: dict = {}

    def _get(self, name):
        if name not in self._svc:
            from app.services import ai, conversion, hybrid, segmentation, semantic, session
            self._svc[name] = {"seg": segmentation.SegmentationService, "conv": conversion.ConversionService,
                               "hybrid": hybrid.HybridRecommenderService, "session": session.SessionRecommenderService,
                               "semantic": semantic.SemanticService, "ai": ai.AIService}[name]()
        return self._svc[name]

    def _ensure_models(self):
        for n in ("seg", "conv"):
            s = self._get(n)
            if not s.is_trained():
                s.train()

    def _available(self, mid) -> bool:
        try:
            if mid in ("kmeans_segmentation", "ml_targeting"):
                return self._get("seg").is_trained() and (mid != "ml_targeting" or self._get("conv").is_trained())
            if mid == "conversion_model":
                return self._get("conv").is_trained()
            if mid == "generative_ai":
                p = self._get("ai").provider
                return p is not None and p.available()
            if mid == "embeddings":
                return day_data(10, "embeddings.npz").exists()
            if mid == "evaluation":
                return day_data(7, "comparison.csv").exists()
            return True
        except Exception:
            return False

    def _buckets(self) -> dict:
        if "buckets" not in self._svc:
            from app.ml.features import build_customer_features
            f = build_customer_features(self.events, self.orders)
            self._svc["buckets"] = dict(zip(f["user_id"].astype(int), manual_rfm_buckets(f)))
        return self._svc["buckets"]

    def module_status(self) -> dict:
        self._ensure_models()
        mods = [{**m, "available": self._available(m["id"])} for m in MODULE_REGISTRY]
        n = sum(m["available"] for m in mods)
        return {"modules": mods, "summary": {"total": len(mods), "available": n, "unavailable": len(mods) - n}}

    def profile_for_user(self, user_id: int) -> dict:
        self._ensure_models()
        seg = self._get("seg").get_customer_segment(user_id)
        conv = self._get("conv").get_customer_probability(user_id)
        ev = self.events[self.events["user_id"] == user_id]
        od = self.orders[self.orders["user_id"] == user_id]
        bucket = None
        if len(od):
            b = self._buckets()
            bucket = b.get(user_id)
        top = (ev.dropna(subset=["category_id"]).groupby("category_id").size()
               .sort_values(ascending=False, kind="stable").head(5))
        hint = ("visoka verovatnoća kupovine -> cross-sell kampanja" if conv["probability"] >= 0.5 else
                "niska verovatnoća -> reaktivacija / popust") if not conv["fallback"] else \
            "nema istorije -> popularity onboarding"
        return {"user_id": user_id,
                "segment": {"label": seg["segment"], "fallback": seg["fallback"], "fallback_reason": seg["reason"],
                            "module_class": _cls("kmeans_segmentation")},
                "conversion": {"probability": float(conv["probability"]), "base_rate": float(conv["base_rate"]),
                               "fallback": conv["fallback"], "fallback_reason": conv["reason"],
                               "module_class": _cls("conversion_model")},
                "rfm": {"bucket": bucket, "fallback": bucket is None,
                        "fallback_reason": None if bucket else "no_history", "module_class": _cls("rfm")},
                "history": {"n_events": int(len(ev)), "n_purchases": int(len(od)),
                            "top_categories": [{"category_id": int(c), "n_events": int(n)} for c, n in top.items()],
                            "module_class": "statistical"},
                "targeting_hint": {"reason": hint, "module_class": _cls("rule_targeting")}}

    def _overall_ctr(self) -> dict:
        imp = int((self.events["event_type"] == "recommendation_impression").sum())
        clk = int((self.events["event_type"] == "recommendation_click").sum())
        return {"impressions": imp, "clicks": clk, "ctr": round(clk / imp, 4) if imp else 0.0}

    def homepage_payload(self, user_id: int, session_id=None, limit: int = 5) -> dict:
        prof = self.profile_for_user(user_id)
        recs = self._get("hybrid").recommend_for_user(user_id, limit)
        recs["module_class"] = _cls("hybrid") if not recs["fallback"] else _cls("popularity")
        sess = None
        if session_id:
            sess = self._get("session").recommend_for_session(session_id, limit)
            sess["module_class"] = _cls("session")
        sem = None
        if recs["recommendations"]:
            sem = self._get("semantic").recommendations_for_product(recs["recommendations"][0]["product_id"], limit)
            sem["module_class"] = _cls("embeddings")
        seg = prof["segment"]["label"]
        hero = self._get("ai").generate_campaign_copy(
            {"name": "Welcome back", "goal": f"Recommend products for segment {seg}", "target_segments": seg})
        top = self.products[self.products["product_id"] == (recs["recommendations"] or [{"product_id": 1}])[0]["product_id"]]
        feat = self._get("ai").generate_product_description(
            {"name": top["name"].iloc[0], "description": top["description"].iloc[0],
             "category": top["category_name"].iloc[0] if "category_name" in top else ""})
        used = ["events", "rfm", "kmeans_segmentation", "conversion_model", "hybrid", "session", "embeddings",
                "generative_ai", "ctr"]
        return {"user_id": user_id, "session_id": session_id, "profile": prof,
                "hero": {**hero.model_dump(), "module_class": _cls("generative_ai")},
                "recommendations": recs, "session_recommendations": sess, "semantic": sem,
                "featured_content": {"kind": feat.kind, "source": feat.source, "fallback": feat.fallback,
                                     "content": feat.content},
                "evaluation_summary": {"available": True, "overall": self._overall_ctr(),
                                       "module_class": _cls("ctr")},
                "modules_used": [{"id": i, "name": _BY_ID[i]["name"], "class": _cls(i)} for i in used]}

    def product_page_payload(self, product_id: int) -> dict:
        p = self.products[self.products["product_id"] == product_id]
        if p.empty:
            raise KeyError(product_id)
        r = p.iloc[0]
        cat = r.get("category_name", "") if "category_name" in p else ""
        prod = {"name": r["name"], "description": r["description"], "category": cat}
        ai = self._get("ai")
        return {"product": {"product_id": int(product_id), "name": r["name"], "category_id": int(r["category_id"]),
                            "price": float(r["price"])},
                "ai_description": ai.generate_product_description(prod).model_dump(),
                "ai_seo": ai.generate_seo_metadata(prod).model_dump(),
                "sections": [{"section": s, "module_id": m, "class": _cls(m)} for s, m in SECTIONS]}
