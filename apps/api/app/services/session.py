"""Day 9 — SessionRecommenderService + CTR dashboard (Day 9/data impression log)."""
from __future__ import annotations

import pandas as pd

from app.data.paths import day_data
from app.recommenders.content import envelope, recommend_popular
from app.recommenders.session import (_group_ctr, recommend_for_session, recommendation_ctr,
                                      session_features)
from app.services.store import get_store, load_products_text


class SessionRecommenderService:
    def __init__(self, products=None, store=None):
        self.products = products if products is not None else load_products_text()
        self.store = store or get_store()
        self.cats = dict(zip(self.products["product_id"].astype(int), self.products["category_id"].astype(int)))
        self._sim = None

    def _similarity(self):
        if self._sim is None:
            from app.services.collaborative import CollaborativeRecommenderService
            c = CollaborativeRecommenderService(products=self.products)
            self._sim = (c._similarity().toarray(), c._interaction().products)
        return self._sim

    def recommend_for_session(self, session_id: str, limit: int = 5) -> dict:
        # TEACH d09: SessionRecommenderService.recommend_for_session
        ev = self.store.get_session_events(session_id)
        ev = pd.DataFrame(ev) if not isinstance(ev, pd.DataFrame) else ev
        if ev.empty or not ev["event_type"].isin(["product_view", "add_to_cart", "purchase"]).any():
            env = envelope(None, "fallback", recommend_popular(self.products, limit=limit), "no_session_signal")
            env["session_id"] = session_id
            return env
        f = session_features(ev, self.cats)
        sim, ids = self._similarity()
        recs = recommend_for_session(f, self.products, sim, ids, limit)
        pub = {k: v for k, v in f.items() if not k.startswith("_")}
        return {"session_id": session_id, "method": "session", "fallback": False, "fallback_reason": None,
                "returned": len(recs), "recommendations": recs, "session_features": pub,
                "excluded_seen": len(f["seen_product_ids"])}
        # /TEACH

    @staticmethod
    def impression_log() -> pd.DataFrame:
        return pd.read_csv(day_data(9, "impressions.csv"))

    def ctr_dashboard(self) -> dict:
        log = self.impression_log()
        imps = log.to_dict("records"); clicks = [r for r in imps if r["clicked"] == 1]
        for r in imps:
            r["position"] = str(r["position"])
        rn = lambda rows, key: [{"group": r[key], **{k: r[k] for k in ("impressions", "clicks", "ctr")}}
                                for r in rows]
        return {"overall": {"impressions": len(imps), "clicks": len(clicks),
                            "ctr": recommendation_ctr(imps, clicks)},
                "by_algorithm": {"groups": rn(_group_ctr(imps, clicks, "algorithm"), "algorithm")},
                "by_position": {"groups": rn(_group_ctr(imps, clicks, "position"), "position")}}

    def popular_vs_personalized_comparison(self) -> dict:
        log = self.impression_log()
        rows = []
        for alg in ["popular", "personalized"]:
            g = log[log["algorithm"] == alg]
            rows.append({"algorithm": alg, "impressions": len(g), "clicks": int(g["clicked"].sum()),
                         "ctr": round(g["clicked"].mean(), 6) if len(g) else 0.0})
        return {"n_sessions": int(log["session_id"].nunique()), "n_impressions": len(log), "comparison": rows}
