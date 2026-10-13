"""Referentno rešenje Day 9 lab-a."""
from __future__ import annotations

from collections import defaultdict

from starter import EVENT_WEIGHTS  # noqa: F401


def recency_weights(n, decay):
    return [decay ** (n - 1 - i) for i in range(n)]


def recent_product_interest(events, decay=0.8):
    pe = [e for e in events if e.get("event_type") in EVENT_WEIGHTS]
    out = defaultdict(float)
    for e, w in zip(pe, recency_weights(len(pe), decay)):
        out[e["product_id"]] += EVENT_WEIGHTS[e["event_type"]] * w
    return dict(out)


def recent_category_interest(events, product_categories, decay=0.8):
    out = defaultdict(float)
    for p, v in recent_product_interest(events, decay).items():
        if p in product_categories:
            out[product_categories[p]] += v
    return dict(out)


def recommendation_ctr(impressions, clicks):
    return len(clicks) / len(impressions) if len(impressions) else 0.0


def ctr_by_algorithm(impressions, clicks):
    imp, clk = defaultdict(int), defaultdict(int)
    for r in impressions:
        imp[r["algorithm"]] += 1
    for r in clicks:
        clk[r["algorithm"]] += 1
    return [{"algorithm": a, "impressions": imp[a], "clicks": clk[a],
             "ctr": clk[a] / imp[a] if imp[a] else 0.0} for a in sorted(set(imp) | set(clk))]
