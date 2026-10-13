"""Day 8 — hybrid pipeline: candidate generation -> merge -> rank -> business rules -> diversity."""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

MERGE_WEIGHTS = {"popularity": 0.2, "category": 0.3, "content": 0.3, "collaborative": 0.2}


def normalize_scores(scores):
    # TEACH d08+: normalize_scores
    scores = [float(s) for s in scores]
    if not scores:
        return []
    mx, mn = max(scores), min(scores)
    if mx == 0:
        return [0.0] * len(scores)
    if mx == mn:
        return [1.0] * len(scores)
    return [s / mx for s in scores]
    # /TEACH


def merge_candidates(candidate_lists: dict, weights: dict) -> list:
    # TEACH d08: merge_candidates
    if not candidate_lists or not any(candidate_lists.values()):
        return []
    total = sum(weights.get(s, 0.0) for s in candidate_lists)
    if total <= 0:
        raise ValueError("zbir težina mora biti > 0")
    merged: dict = {}
    for src, cands in candidate_lists.items():
        w = weights.get(src, 0.0) / total
        for c, n in zip(cands, normalize_scores([c["score"] for c in cands])):
            m = merged.setdefault(int(c["product_id"]), {"product_id": int(c["product_id"]), "score": 0.0,
                                                          "sources": set()})
            m["score"] += w * n; m["sources"].add(src)
            for key in ("category_id", "name"):
                if key in c and key not in m:
                    m[key] = c[key]
    return [{**m, "sources": sorted(m["sources"])} for m in merged.values()]
    # /TEACH


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: (-c["score"], c["product_id"]))


def apply_business_rules(ranked, rules):
    # TEACH d08: apply_business_rules
    rules = rules or {}
    kept, removed = [], []
    avail, excl, mins = rules.get("available_ids"), set(rules.get("exclude_ids") or ()), rules.get("min_score")
    for c in ranked:
        why = []
        if avail is not None and c["product_id"] not in avail:
            why.append("unavailable")
        if c["product_id"] in excl:
            why.append("excluded")
        if mins is not None and c["score"] < mins:
            why.append("below_min_score")
        (removed.append({**c, "removed_by": why}) if why else kept.append(c))
    return {"ranked": kept, "removed": removed}
    # /TEACH


def diversify_results(ranked, k, max_per_category=2):
    # TEACH d08+: diversify_results
    out, rest, cnt = [], [], Counter()
    for c in ranked:
        cat = c.get("category_id")
        if cat is None or cnt[cat] < max_per_category:
            if len(out) < k:
                out.append(c); cnt[cat] += 1
                continue
        rest.append(c)
    for c in rest:  # fill, don't truncate
        if len(out) >= k:
            break
        out.append(c)
    return out[:k]
    # /TEACH


# --- candidate generators -------------------------------------------------------
class HybridModels:
    """Modeli izgrađeni SAMO iz train događaja (anti-leakage)."""

    def __init__(self, products: pd.DataFrame, train: pd.DataFrame):
        from sklearn.metrics.pairwise import cosine_similarity
        from app.recommenders.collaborative import build_interaction_matrix, calculate_item_similarity
        from app.recommenders.content import build_tfidf_matrix, popularity_from_events
        from app.services.recommender import TFIDF_KWARGS
        self.products = products.reset_index(drop=True)
        self.ids = self.products["product_id"].astype(int).to_numpy()
        self.pos = {p: i for i, p in enumerate(self.ids)}
        self.cat = dict(zip(self.ids, self.products["category_id"]))
        self.name = dict(zip(self.ids, self.products["name"]))
        self.pop = self.products["product_id"].map(popularity_from_events(train)).fillna(0.0).to_numpy()
        tf, _ = build_tfidf_matrix(self.products, **TFIDF_KWARGS)
        self.content_sim = cosine_similarity(tf)
        inter = build_interaction_matrix(train, products=self.ids)
        self.cf_sim = calculate_item_similarity(inter).toarray()
        np.fill_diagonal(self.content_sim, 0.0); np.fill_diagonal(self.cf_sim, 0.0)
        ev = train[train["event_type"].isin(["product_view", "add_to_cart", "purchase"])].copy()
        ev["_p"] = pd.to_numeric(ev["product_id"], errors="coerce")
        ev = ev.dropna(subset=["_p", "user_id"])
        ev["_w"] = ev["event_type"].map({"product_view": 1, "add_to_cart": 3, "purchase": 5})
        self.user_events = ev.groupby(ev["user_id"].astype(int)).size().to_dict()
        self.user_signal = {u: g.groupby(g["_p"].astype(int))["_w"].sum() for u, g in
                            ev.groupby(ev["user_id"].astype(int))}
        pur = ev[ev["event_type"] == "purchase"]
        self.user_purchased = {u: set(g["_p"].astype(int)) for u, g in pur.groupby(pur["user_id"].astype(int))}
        thr = np.quantile(self.pop, 0.2)
        self.available_ids = {int(p) for p, v in zip(self.ids, self.pop) if v > thr}

    def _top(self, scores, limit, src):
        order = sorted(((-s, int(p)) for p, s in zip(self.ids, scores) if s > 0))[:limit]
        return [{"product_id": p, "score": round(-s, 6), "source": src, "rank_in_source": i + 1,
                 "category_id": int(self.cat[p]), "name": self.name[p]} for i, (s, p) in enumerate(order)]

    def candidates(self, user_id: int, candidate_limit=30, signal_limit=15) -> dict:
        sig = self.user_signal[user_id].sort_values(ascending=False, kind="stable").head(signal_limit)
        w = np.zeros(len(self.ids))
        for p, v in sig.items():
            w[self.pos[p]] = v
        cat_aff = Counter()
        for p, v in sig.items():
            cat_aff[self.cat[p]] += v
        cat_scores = np.array([self.pop[i] * cat_aff.get(self.cat[p], 0) for i, p in enumerate(self.ids)])
        return {"popularity": self._top(self.pop, candidate_limit, "popularity"),
                "category": self._top(cat_scores, candidate_limit, "category"),
                "content": self._top(w @ self.content_sim, candidate_limit, "content"),
                "collaborative": self._top(w @ self.cf_sim, candidate_limit, "collaborative")}, len(sig)

    def recommend(self, user_id, k=5, weights=None, max_per_category=2, sources=None,
                  candidate_limit=30, signal_limit=15, diversify=True):
        # TEACH d08: HybridModels.recommend
        if user_id not in self.user_signal:
            return None
        cands, n_sig = self.candidates(user_id, candidate_limit, signal_limit)
        if sources:
            cands = {s: cands[s] for s in sources}
        merged = rank_candidates(merge_candidates(cands, weights or MERGE_WEIGHTS))
        rules = {"available_ids": self.available_ids, "exclude_ids": self.user_purchased.get(user_id, set())}
        ruled = apply_business_rules(merged, rules)
        final = diversify_results(ruled["ranked"], k, max_per_category) if diversify else ruled["ranked"][:k]
        return {"candidates": cands, "n_signal": n_sig, "merged": merged, "ruled": ruled, "final": final}
        # /TEACH


def user_test_cases(train, test) -> list:
    def prods(df):
        ev = df[df["event_type"].isin(["product_view", "add_to_cart", "purchase"])]
        p = pd.to_numeric(ev["product_id"], errors="coerce")
        ev = ev.assign(_p=p).dropna(subset=["_p", "user_id"])
        return {int(u): set(g["_p"].astype(int)) for u, g in ev.groupby("user_id")}
    tr, te = prods(train), prods(test)
    cases = []
    for u in sorted(set(tr) & set(te)):
        tg = sorted(te[u] - tr[u])
        if tg:
            cases.append({"user_id": u, "target_product_ids": tg})
    return cases


# --- imena iz lekcije (Day 8 "Važne funkcije") -----------------------------------
def generate_candidates(models: "HybridModels", user_id: int, candidate_limit=30, signal_limit=15) -> dict:
    """Kandidati PO IZVORU (recall) za korisnika; nepoznat korisnik -> {}."""
    if user_id not in models.user_signal:
        return {}
    return models.candidates(user_id, candidate_limit, signal_limit)[0]


def score_candidate(normalized_by_source: dict, weights: dict = None) -> float:
    """Blended skor jednog kandidata: Σ w_s · norm_s / Σ w (težine = heuristika)."""
    w = weights or MERGE_WEIGHTS
    tot = sum(w.get(s, 0.0) for s in normalized_by_source)
    if tot <= 0:
        raise ValueError("zbir težina mora biti > 0")
    return sum(w.get(s, 0.0) * v for s, v in normalized_by_source.items()) / tot


def recommend_for_user(models: "HybridModels", user_id: int, k: int = 5, **kw):
    """Ceo pipeline (candidates -> merge -> rank -> rules -> diversity); None za nepoznatog korisnika."""
    return models.recommend(user_id, k, **kw)


def build_user_based_comparison(products, events, k: int = 5, split_ratio: float = 0.8, max_test_users=None) -> dict:
    from app.services.hybrid import HybridRecommenderService
    return HybridRecommenderService(products=products, events=events,
                                    split_ratio=split_ratio).user_based_comparison(k, max_test_users)
