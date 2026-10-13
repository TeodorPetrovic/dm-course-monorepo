"""Starter za Day 3 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 3/lab/``):

    python3 -m pytest test_lab.py                # tvoj starter
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # rešenje
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# Feature kolone modela (numeričke). ``build_features`` je DATA (Day 2
# materijal) — ne implementiraš je.
FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "product_views",
    "cart_adds",
    "sessions",
    "aov",
    "conversion",
]
LABEL_COLUMN = "will_purchase"


def build_features(
    events_df: pd.DataFrame,
    orders_df: Optional[pd.DataFrame] = None,
    reference=None,
) -> pd.DataFrame:
    """Pojednostavljena feature tabela po korisniku (data — ne implementiraš je).

    Vraća ``user_id`` + ``FEATURE_COLUMNS``. Ako je ``reference`` dat, recency
    se računa u odnosu na njega (inače na max timestamp prosleđenih podataka).
    """
    orders_df = pd.DataFrame() if orders_df is None else orders_df
    if reference is None:
        parts = []
        if len(events_df):
            parts.append(pd.to_datetime(events_df["timestamp"]))
        if len(orders_df):
            parts.append(pd.to_datetime(orders_df["timestamp"]))
        reference = pd.concat(parts).max() if parts else pd.NaT
    if pd.isna(reference):
        return pd.DataFrame(columns=["user_id"] + FEATURE_COLUMNS)

    users = pd.concat(
        [events_df["user_id"], orders_df["user_id"]]
    ).dropna().astype("int64").unique()

    # recency: poslednja kupovina / poslednja aktivnost (ili najhladniji fallback)
    act = (
        events_df.assign(_ts=pd.to_datetime(events_df["timestamp"]))
        .groupby("user_id")["_ts"].max()
        if len(events_df)
        else pd.Series(dtype="datetime64[ns]")
    )
    if len(orders_df):
        od = orders_df.assign(
            _ts=pd.to_datetime(orders_df["timestamp"]),
            _tot=pd.to_numeric(orders_df["total_price"], errors="coerce").fillna(0.0),
        ).groupby("user_id")
        last_buy = od["_ts"].max()
        frequency = od.size().astype("int64")
        monetary = od["_tot"].sum()
    else:
        last_buy = pd.Series(dtype="datetime64[ns]")
        frequency = pd.Series(dtype="int64")
        monetary = pd.Series(dtype="float64")

    window_start = pd.to_datetime(events_df["timestamp"]).min() if len(events_df) else reference
    rows = []
    for uid in users:
        uid = int(uid)
        lb = last_buy.get(uid, pd.NaT)
        la = act.get(uid, pd.NaT)
        if pd.notna(lb):
            recency = int((reference - lb).days)
        elif pd.notna(la):
            recency = int((reference - la).days)
        else:
            recency = int((reference - window_start).days) + 1
        rows.append({
            "user_id": uid,
            "recency_days": recency,
            "frequency": int(frequency.get(uid, 0)),
            "monetary": round(float(monetary.get(uid, 0.0)), 2),
        })
    base = pd.DataFrame(rows)

    # brojači + AOV + konverzija
    if len(events_df):
        counts = events_df.assign(
            _view=(events_df["event_type"] == "product_view"),
            _cart=(events_df["event_type"] == "add_to_cart"),
        ).groupby("user_id").agg(
            product_views=("_view", "sum"),
            cart_adds=("_cart", "sum"),
            sessions=("user_session", "nunique"),
        )
        buy_sessions = (
            events_df[events_df["event_type"] == "purchase"]
            .groupby("user_id")["user_session"].nunique()
        )
        base = base.merge(counts, on="user_id", how="left")
        base["product_views"] = base["product_views"].fillna(0).astype("int64")
        base["cart_adds"] = base["cart_adds"].fillna(0).astype("int64")
        base["sessions"] = base["sessions"].fillna(0).astype("int64")
        base["aov"] = np.where(base["frequency"] > 0, base["monetary"] / base["frequency"], 0.0)
        base["aov"] = base["aov"].round(2)
        base["conversion"] = (
            base["user_id"].map(buy_sessions).fillna(0).astype("int64") / base["sessions"]
        ).round(4)
        base["conversion"] = base["conversion"].where(base["sessions"] > 0, 0.0)
    else:
        base["product_views"] = 0
        base["cart_adds"] = 0
        base["sessions"] = 0
        base["aov"] = 0.0
        base["conversion"] = 0.0
    return base[["user_id"] + FEATURE_COLUMNS]


def build_training_dataset(
    events_df: pd.DataFrame,
    orders_df: Optional[pd.DataFrame] = None,
    window_days: int = 7,
    leaky: bool = False,
) -> pd.DataFrame:
    """Gradi labeled training dataset po korisniku. TODO: implementirati.

    Zahtevi (definicije su deo zadatka — moraju biti eksplicitne):
    - **cutoff** = ``reference - window_days``, gde je ``reference`` najskoriji
      događaj/porudžbina u datasetu.
    - **Labela** ``will_purchase``: 1 ako je korisnik kupio u ``[cutoff,
      reference]``, inače 0.
    - **Clean** (``leaky=False``): feature-i SAMO na istoriji pre ``cutoff``-a
      (``build_features`` pozovi sa ``reference=cutoff``) — model NE SME da
      vidi window.
    - **Leaky** (``leaky=True``): feature-i iz CELE istorije (``reference``).
    - Vrati DataFrame ``user_id`` + ``FEATURE_COLUMNS`` + ``will_purchase``
      (bez indeksa sortiran po ``user_id``).
    """
    raise NotImplementedError("implementiraj build_training_dataset")


def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.3,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stratifikovan train/test split po labeli. TODO: implementirati.

    Zahtevi:
    - ``LABEL_COLUMN`` mora postojati (inače ``ValueError``).
    - ``train_test_split`` sa ``stratify=df[LABEL_COLUMN]`` i istim
      ``random_state`` -> deterministički.
    - Vrati ``(train_df, test_df)`` sa resetovanim indeksima.
    """
    raise NotImplementedError("implementiraj split_dataset")


def train_conversion_model(X_train, y_train, model_type="logistic_regression", random_state=42):
    """Trenira klasifikator (data — ne implementiraš je).

    ``model_type``: ``logistic_regression`` ili ``random_forest``.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    X = np.asarray(X_train)
    y = np.asarray(y_train)
    if model_type == "logistic_regression":
        model = LogisticRegression(max_iter=2000, random_state=random_state)
    elif model_type == "random_forest":
        model = RandomForestClassifier(n_estimators=200, random_state=random_state)
    else:
        raise ValueError(f"nepoznat model_type: {model_type!r}")
    model.fit(X, y)
    return model


def evaluate_model(model, X, y) -> dict:
    """Evaluacija: accuracy + confusion matrix + precision/recall/F1. TODO: implementirati.

    Zahtevi:
    - ``model.predict(X)`` -> predikcije.
    - Vrati dict: ``accuracy``, ``precision``, ``recall``, ``f1``
      (``sklearn.metrics`` sa ``zero_division=0``), ``confusion_matrix``
      ([[tn, fp], [fn, tp]]), ``n``. Vrednosti zaokruži na 4 decimale.
    """
    raise NotImplementedError("implementiraj evaluate_model")


def predict_conversion_probability(model, scaled_row) -> float:
    """Verovatnoća ``will_purchase=1`` za jednu skaliranu vrstu. TODO: implementirati.

    Zahtevi (failure handling je deo kursa):
    - ``model is None`` -> ``ValueError`` („model not trained").
    - ``scaled_row`` je ``None`` ili prazan -> ``ValueError`` („prazna feature
      vrsta").
    - inače -> ``round(model.predict_proba(X)[0, 1], 4)``.
    """
    raise NotImplementedError("implementiraj predict_conversion_probability")
