"""Starter za Day 6 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 6/lab/``, koristi dm-ml venv — ima sklearn):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

# Kolone koje sve preporuke vraćaju (product_info + score).
RECOMMENDATION_COLUMNS = [
    "product_id", "name", "slug", "description", "img_url",
    "category_id", "price", "score",
]

# Težine događaja (pretpostavke, ne istine — vidi Day 6 README).
EVENT_WEIGHTS = {
    "product_view": 1.0,
    "add_to_cart": 3.0,
    "purchase": 5.0,
}


def build_interaction_matrix(events_df: pd.DataFrame) -> tuple:
    """Implicitna interaction matrica (sesije × proizvodi). TODO: implementirati.

    Zahtevi:
    - Uzmi samo događaje čiji je ``event_type`` u ``EVENT_WEIGHTS`` i koji imaju
      ``user_session`` i ``product_id``.
    - Vrednost ćelije (sesija, proizvod) = **najveća** težina događaja u toj
      sesiji za taj proizvod (max-agregacija — NE zbir; brojanje interakcija kao
      ocenu je čest bag).
    - Redovi = sortirane sesije, kolone = sortirani proizvodi.
    - Vrati ``(matrix, sessions, products)`` gde je ``matrix`` ``csr_matrix``
      (sparse), ``sessions`` lista stringova, ``products`` lista int-ova.
    """
    raise NotImplementedError("implementiraj build_interaction_matrix")


def calculate_item_similarity(matrix) -> np.ndarray:
    """Item-item kosinusna sličnost. TODO: implementirati.

    Zahtevi: item vektori su **kolone** matrice (sesije × proizvodi), pa je
    ``cosine_similarity(matrix.T)`` matrica ``n_proizvoda × n_proizvoda``.
    Vrati je kao **gusti** ``np.ndarray``.
    """
    raise NotImplementedError("implementiraj calculate_item_similarity")


def recommend_similar(
    products_df: pd.DataFrame,
    product_id: int,
    matrix,
    products: list,
    limit: int = 5,
) -> pd.DataFrame:
    """Collaborative preporuke po item-item sličnosti, BEZ targeta. TODO: implementirati.

    Zahtevi:
    - Ako ``product_id`` NIJE u ``products`` (cold start / nov proizvod) ->
      fallback: vrati ``recommend_popular(products_df, limit)`` (baseline —
      nikad prazan rezultat bez objašnjenja).
    - Inače: izračunaj sličnosti (``calculate_item_similarity``), uzmi red
      targeta, ISKLJUČI target iz kandidata, sortiraj opadajuće po ``score``
      (tie-break ``product_id``) i vrati top-``limit`` sa
      ``RECOMMENDATION_COLUMNS`` (``score`` = kosinusna sličnost).
    """
    raise NotImplementedError("implementiraj recommend_similar")


def recommend_popular(products_df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Popularity baseline (za fallback). TODO: implementirati.

    Zahtevi: ``products_df`` ima kolonu ``popularity``; sortiraj opadajuće
    (tie-break po ``product_id`` rastuće), uzmi prvih ``limit``, vrati
    ``RECOMMENDATION_COLUMNS`` gde je ``score`` = ``popularity``.
    """
    raise NotImplementedError("implementiraj recommend_popular")
