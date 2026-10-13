"""Referentno rešenje Day 7 lab-a."""
from __future__ import annotations

import math

import pandas as pd


def _chk(k):
    if k <= 0:
        raise ValueError("k mora biti > 0")


def precision_at_k(ranked_ids, relevant_ids, k):
    _chk(k); top = list(dict.fromkeys(ranked_ids[:k]))
    return len(set(top) & set(relevant_ids)) / min(k, len(top)) if top else 0.0


def recall_at_k(ranked_ids, relevant_ids, k):
    _chk(k); rel = set(relevant_ids)
    return len(set(ranked_ids[:k]) & rel) / len(rel) if ranked_ids and rel else 0.0


def hit_rate_at_k(ranked_ids, relevant_ids, k):
    _chk(k)
    return 1.0 if set(ranked_ids[:k]) & set(relevant_ids) else 0.0


def ndcg_at_k(ranked_ids, relevant_ids, k):
    _chk(k); rel = set(relevant_ids); top = list(ranked_ids[:k])
    if not top or not rel:
        return 0.0
    dcg = sum(1 / math.log2(i + 2) for i, p in enumerate(top) if p in rel)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(rel), len(top))))
    return dcg / idcg


def catalog_coverage(recommended_ids, catalog_size):
    if catalog_size <= 0:
        raise ValueError("catalog_size mora biti > 0")
    return len(set(recommended_ids)) / catalog_size if len(recommended_ids) else 0.0


def temporal_split(events_df, split_time, timestamp_column="timestamp"):
    ts = pd.to_datetime(events_df[timestamp_column]); t = pd.Timestamp(split_time)
    return events_df[ts < t], events_df[ts >= t]
