"""Starter za Day 5 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 5/lab/``, koristi dm-ml venv — ima sklearn):

    dm-ml/.venv/bin/python -m pytest test_lab.py                          # tvoj starter
    LAB_MODULE=reference_solutions dm-ml/.venv/bin/python -m pytest test_lab.py  # rešenje
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Kolone koje sve preporuke vraćaju (product_info + score).
RECOMMENDATION_COLUMNS = [
    "product_id", "name", "slug", "description", "img_url",
    "category_id", "price", "score",
]


def recommend_popular(products_df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Top-N proizvoda po popularnosti (baseline bez ML-a). TODO: implementirati.

    Zahtevi:
    - ``products_df`` ima kolonu ``popularity`` (skor po proizvodu).
    - Sortiraj opadajuće po ``popularity`` (tie-break po ``product_id`` rastuće),
      uzmi prvih ``limit``, i vrati kolone ``RECOMMENDATION_COLUMNS`` gde je
      ``score`` = ``popularity``.
    """
    raise NotImplementedError("implementiraj recommend_popular")


def recommend_same_category(
    products_df: pd.DataFrame,
    product_id: int,
    limit: int = 5,
) -> pd.DataFrame:
    """Top-N iz ISTE kategorije kao ``product_id`` (baseline). TODO: implementirati.

    Zahtevi:
    - ``product_id`` mora postojati u ``products_df`` (inače ``ValueError``).
    - Zadrži samo proizvode iste kategorije, ISKLJUČI sam target, sortiraj po
      ``popularity`` opadajuće (tie-break po ``product_id``) i vrati top-``limit``
      sa ``RECOMMENDATION_COLUMNS`` (``score`` = ``popularity``).
    """
    raise NotImplementedError("implementiraj recommend_same_category")


def prepare_product_text(
    products_df: pd.DataFrame,
    include_category: bool = True,
) -> pd.Series:
    """Tekstualna reprezentacija proizvoda za TF-IDF. TODO: implementirati.

    Zahtevi:
    - Tekst = ``name`` + razmak + ``description``.
    - Ako je ``include_category``, dodaj ispred i ``category_name`` (npr.
      ``"Electronics Smartphone 5102 Smartphone for electronics"``).
    - Vrati ``pd.Series`` indeksiranu po ``product_id`` (kolona ``product_id``).
    """
    raise NotImplementedError("implementiraj prepare_product_text")


def build_tfidf_matrix(
    products_df: pd.DataFrame,
    text_column: str = "product_text",
) -> tuple:
    """TF-IDF matrica nad kolonom teksta. TODO: implementirati.

    Zahtevi:
    - Ako ``products_df`` nema ``text_column``, napravi je pozivom
      ``prepare_product_text``.
    - ``TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)``
      fit_transform nad tekstovima -> ``(matrix, vectorizer)``. Matrica je
      poravnata sa ``products_df`` (red i = proizvod i).
    """
    raise NotImplementedError("implementiraj build_tfidf_matrix")


def calculate_product_similarity(tfidf_matrix, index: int) -> np.ndarray:
    """Kosinusne sličnosti reda ``index`` sa svim redovima. TODO: implementirati.

    Zahtevi: ``cosine_similarity(tfidf_matrix[index:index+1], tfidf_matrix)``
    vrati ``.flatten()``. Red ``index`` (uključujući sebe) -> niz dužine
    ``tfidf_matrix.shape[0]``. TfidfVectorizer normalizuje redove, pa je kosinus
    = skalarni proizvod normalizovanih vektora (ne poredi raw counts!).
    """
    raise NotImplementedError("implementiraj calculate_product_similarity")


def recommend_similar_products(
    products_df: pd.DataFrame,
    product_id: int,
    tfidf_matrix,
    limit: int = 5,
) -> pd.DataFrame:
    """Content preporuke po kosinusnoj sličnosti, BEZ targeta. TODO: implementirati.

    Zahtevi:
    - Ako ``product_id`` NIJE u ``products_df`` (cold start / nov proizvod) ->
      fallback: vrati ``recommend_popular(products_df, limit)`` (baseline —
      nikad prazan rezultat bez objašnjenja).
    - Inače: izračunaj sličnosti (``calculate_product_similarity``), ISKLJUČI
      target iz kandidata (najsličniji ne sme biti sam target), sortiraj
      opadajuće po ``score`` (tie-break ``product_id``) i vrati top-``limit``
      sa ``RECOMMENDATION_COLUMNS`` (``score`` = kosinusna sličnost).
    """
    raise NotImplementedError("implementiraj recommend_similar_products")
