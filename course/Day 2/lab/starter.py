"""Starter za Day 2 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 2/lab/``):

    python3 -m pytest test_lab.py                # tvoj starter
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # rešenje
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# Kolone koje K-Means koristi za segmentaciju (skalirane).
SEGMENT_FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "aov",
    "conversion",
]


def calculate_rfm(
    events_df: pd.DataFrame,
    orders_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Računa RFM (Recency/Frequency/Monetary) po korisniku. TODO: implementirati.

    Zahtevi (definicije su deo zadatka — moraju biti eksplicitne):
    - **Recency (dani):** ``(referenca − poslednja kupovina)`` za kupce; za
      korisnike bez kupovine ``(referenca − poslednja aktivnost)``; za
      korisnike bez ijednog događaja najhladniji definisani slučaj
      (``(referenca − najraniji događaj) + 1``).
      Referenca = max(timestamp) iz događaja i porudžbina.
    - **Frequency:** broj porudžbina (različiti ``order_id``; jedna porudžbina može
      imati više stavki/redova); **Monetary:** suma ``total_price``.
    - Zero-spend korisnici moraju imati frequency=0, monetary=0.0 (bez NaN).
    - Prazan ulaz -> prazan DataFrame (kolone: user_id, recency_days,
      frequency, monetary).
    """
    raise NotImplementedError("implementiraj calculate_rfm")


def scale_customer_features(
    features_df: pd.DataFrame,
    feature_columns: list[str],
    scaler=None,
) -> tuple[pd.DataFrame, object]:
    """Skalira numeričke feature-e (StandardScaler). TODO: implementirati.

    Zahtevi:
    - ``scaler is None`` -> fit-uj novi ``StandardScaler`` na
      ``features_df[feature_columns]`` i vrati ``(scaled_df, scaler)``.
    - ``scaler`` je dat -> **transform only** (NIKAD ne refit-uj na novom
      korisniku — čest bug!). Vrati ``(scaled_df, scaler)``.
    - Kolone koje nedostaju -> ``ValueError``.
    """
    raise NotImplementedError("implementiraj scale_customer_features")


def assign_segment(
    model,
    scaled_row: Optional[pd.Series],
    fallback_label: str = "unsegmented",
) -> str:
    """Dodeljuje segment jednoj skaliranoj feature vrsti. TODO: implementirati.

    Zahtevi (failure handling je deo kursa):
    - ``model is None`` -> ``ValueError`` („model not trained").
    - ``scaled_row`` je ``None`` ili prazan -> ``fallback_label`` (definisan
      fallback za korisnika bez istorije).
    - inače -> ``f"segment_{int(model.predict(row))}"``.
    """
    raise NotImplementedError("implementiraj assign_segment")
