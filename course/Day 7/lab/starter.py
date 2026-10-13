"""Starter za Day 7 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 7/lab/``, koristi dm-ml venv):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

import math

import pandas as pd


def precision_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """P@K — udeo relevantnih u prvih K preporuka. TODO: implementirati.

    Zahtevi:
    - ``top = ranked_ids[:k]``; imenilac je ``min(k, len(top))`` (broj stvarno
      serviranih), NIKAD broj relevantnih.
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    - duplikati se broje jednom (``set``).
    """
    raise NotImplementedError("implementiraj precision_at_k")


def recall_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """R@K — udeo relevantnih uhvaćen. TODO: implementirati.

    Zahtevi:
    - ``hits / len(relevant_ids)`` (imenilac je broj relevantnih, ne k).
    - nula relevantnih (``0/0``) -> ``0.0`` (definisano).
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    """
    raise NotImplementedError("implementiraj recall_at_k")


def hit_rate_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """HR@K — 1.0 ako je bar jedan relevantan u top-K, inače 0.0. TODO: implementirati.

    Zahtevi:
    - prazna lista preporuka -> ``0.0``; ``k <= 0`` -> ``ValueError``.
    """
    raise NotImplementedError("implementiraj hit_rate_at_k")


def ndcg_at_k(ranked_ids: list, relevant_ids: list, k: int) -> float:
    """NDCG@K — DCG/IDCG (log discount po poziciji). TODO: implementirati.

    Zahtevi:
    - DCG@K = sum(rel_i / log2(i + 2)) za i u 0..len(top)-1, rel_i = 1 ako je
      ``top[i]`` relevantan.
    - IDCG@K = DCG idealnog poretka: svi relevantni prvo, ograničeno na
      ``min(len(relevant), len(top))`` mesta.
    - prazna lista preporuka ili nula relevantnih -> ``0.0``; ``k <= 0`` ->
      ``ValueError``.
    """
    raise NotImplementedError("implementiraj ndcg_at_k")


def catalog_coverage(recommended_ids: list, catalog_size: int) -> float:
    """Udeo kataloga koji se UOPŠTE preporuči. TODO: implementirati.

    Zahtevi:
    - ``len(set(recommended_ids)) / catalog_size``.
    - ``catalog_size <= 0`` -> ``ValueError``; prazne preporuke -> ``0.0``.
    """
    raise NotImplementedError("implementiraj catalog_coverage")


def temporal_split(
    events_df: pd.DataFrame,
    split_time: str,
    timestamp_column: str = "timestamp",
) -> tuple:
    """Podeli događaje na train/test po vremenu. TODO: implementirati.

    Zahtevi:
    - događaji sa ``timestamp < split_time`` idu u train, ``>= split_time`` u test.
    - vrati ``(train_df, test_df)`` (DataFrame-ovi, redosled redova očuvan).
    """
    raise NotImplementedError("implementiraj temporal_split")
