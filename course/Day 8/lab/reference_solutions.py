"""Referentno rešenje Day 8 lab-a."""
from __future__ import annotations

from collections import Counter


def normalize_scores(scores):
    s = [float(x) for x in scores]
    if not s:
        return []
    mx, mn = max(s), min(s)
    if mx == 0:
        return [0.0] * len(s)
    if mx == mn:
        return [1.0] * len(s)
    return [x / mx for x in s]


def merge_candidates(candidate_lists, weights):
    if not candidate_lists or not any(candidate_lists.values()):
        return []
    tot = sum(weights.get(k, 0.0) for k in candidate_lists)
    if tot <= 0:
        raise ValueError("zbir težina mora biti > 0")
    out = {}
    for src, cands in candidate_lists.items():
        w = weights.get(src, 0.0) / tot
        for c, n in zip(cands, normalize_scores([c["score"] for c in cands])):
            m = out.setdefault(c["product_id"], {**c, "score": 0.0, "sources": set()})
            m["score"] += w * n; m["sources"].add(src)
    return [{**m, "sources": sorted(m["sources"])} for m in out.values()]


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: (-c["score"], c["product_id"]))


def apply_business_rules(ranked, rules):
    kept, removed = [], []
    rules = rules or {}
    for c in ranked:
        why = []
        if rules.get("available_ids") is not None and c["product_id"] not in rules["available_ids"]:
            why.append("unavailable")
        if c["product_id"] in (rules.get("exclude_ids") or set()):
            why.append("excluded")
        if rules.get("min_score") is not None and c["score"] < rules["min_score"]:
            why.append("below_min_score")
        (removed.append({**c, "removed_by": why}) if why else kept.append(c))
    return {"ranked": kept, "removed": removed}


def diversify_results(ranked, k, max_per_category=2):
    out, rest, cnt = [], [], Counter()
    for c in ranked:
        cat = c.get("category_id")
        if len(out) < k and (cat is None or cnt[cat] < max_per_category):
            out.append(c); cnt[cat] += 1
        else:
            rest.append(c)
    out += rest[: max(0, k - len(out))]
    return out[:k]
