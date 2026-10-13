"""Starter za Day 4 lab.

Implementiraj funkcije označene sa ``raise NotImplementedError``. Cilj: do
kraja lab-a tvoj ``starter.py`` prolazi ``test_lab.py``.

Pokretanje testova (iz ``Day 4/lab/``):

    python3 -m pytest test_lab.py                # tvoj starter
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # rešenje
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

# Prioritet RFM bucket-a za rule-based skor (baseline — bez ML-a).
BUCKET_PRIORITY = {
    "champions": 4,
    "loyal": 3,
    "at_risk": 2,
    "dormant": 1,
}


def _eligibility(
    probability: Optional[float],
    segment: Optional[str],
    rfm_bucket: Optional[str],
    monetary: Optional[float],
    campaign: dict,
) -> tuple[bool, list[str]]:
    """Eligibilnost po pravilima kampanje (DATA — ne implementiraš je).

    Pravila (svako proizvodi razlog):
      - ``target_segments``  — segment mora biti u listi (ako nije prazna).
      - ``eligible_buckets`` — rfm_bucket mora biti u listi (ako nije prazna).
      - ``min_probability``  — ``probability >= prag`` (ako je prag > 0).
      - ``min_monetary``     — ``monetary >= prag`` (ako je prag > 0).

    Vraća ``(eligible, reasons)`` — reasons je lista opisa (na srpskom).
    """
    reasons: list[str] = []

    target_segments = campaign.get("target_segments") or []
    if target_segments:
        ok = segment is not None and segment in set(target_segments)
        reasons.append(
            f"segment {segment} {'je' if ok else 'nije'} u ciljanim segmentima"
        )
        if not ok:
            return False, reasons

    eligible_buckets = campaign.get("eligible_buckets") or []
    if eligible_buckets:
        ok = rfm_bucket is not None and rfm_bucket in set(eligible_buckets)
        reasons.append(
            f"rfm_bucket {rfm_bucket} {'je' if ok else 'nije'} u dozvoljenim"
        )
        if not ok:
            return False, reasons

    min_probability = float(campaign.get("min_probability", 0.0) or 0.0)
    if min_probability > 0.0:
        if probability is None:
            reasons.append("nema verovatnoće")
            return False, reasons
        ok = float(probability) >= min_probability
        reasons.append(f"P({float(probability):.4f}) {'>=' if ok else '<'} {min_probability:.4f}")
        if not ok:
            return False, reasons

    min_monetary = float(campaign.get("min_monetary", 0.0) or 0.0)
    if min_monetary > 0.0:
        value = 0.0 if monetary is None else float(monetary)
        ok = value >= min_monetary
        reasons.append(f"vrednost {value:.2f} {'>=' if ok else '<'} {min_monetary:.2f}")
        if not ok:
            return False, reasons

    return True, reasons


def score_customer(
    probability: Optional[float],
    segment: Optional[str],
    rfm_bucket: Optional[str],
    monetary: Optional[float],
    campaign: dict,
) -> dict:
    """Skor odluke za jednog korisnika. TODO: implementirati.

    Zahtevi (definicije su deo zadatka):
    - Ako je korisnik neeligibilan (``_eligibility``) -> vrati
      ``{"eligible": False, "score": 0.0, "expected_value": 0.0,
      "reasons": reasons}``.
    - Ako je eligibilan -> ``expected_value = probability*monetary −
      campaign["cost_per_contact"]`` (``0.0`` za ``None``), ``score =
      expected_value`` (zaokruži na 4 decimale) i dodaj razlog
      ``f"očekivana vrednost = {p}*{value} - {cost} = {ev}"``.
    """
    raise NotImplementedError("implementiraj score_customer")


def select_target_customers(
    profiles: pd.DataFrame,
    campaign: dict,
) -> pd.DataFrame:
    """Primeni pravila kampanje na profil -> skup kandidata. TODO: implementirati.

    Zahtevi:
    - Za svaku vrstu pozovi ``_eligibility``; zadrži samo eligibilne.
    - Dodaj kolonu ``selected_reasons`` (lista razloga — samo za one koji su
      prošli; za ne-eligibilne razlozi su prazna lista).
    - Vrati DataFrame samo sa eligibilnim vrstama, sortiran po ``user_id``.
    - Ako je ``profiles`` prazan -> vrati prazan DataFrame (``pd.DataFrame()``).
    """
    raise NotImplementedError("implementiraj select_target_customers")


def rank_target_customers(
    selected: pd.DataFrame,
    campaign: dict,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Rangiraj po skoru i primeni limitu. TODO: implementirati.

    Zahtevi:
    - Računaj ``score_customer`` za svaku vrstu (kolone ``score``,
      ``expected_value``, ``reasons``).
    - Sortiraj po ``score`` opadajuće, tie-break po ``user_id`` rastuće.
    - Dodaj ``rank`` = 1..N (pre limita).
    - ``limit`` klipuj na ``campaign["max_contacts"]`` (ako je definisan);
      vrati ``head`` najboljih. Ako ``limit`` nije dat -> ``max_contacts``.
    - Vrati kolone: ``rank``, ``user_id``, ``score``, ``expected_value``,
      ``probability``, ``segment``, ``rfm_bucket``, ``monetary``, ``reasons``.
    """
    raise NotImplementedError("implementiraj rank_target_customers")


def rule_based_score(rfm_bucket: Optional[str], monetary: Optional[float]) -> float:
    """Rule-based skor (baseline — bez ML-a). TODO: implementirati.

    Zahtevi: ``BUCKET_PRIORITY[rfm_bucket] * 1_000_000 + monetary``
    (``0.0`` za ``None``). Rangira „visoke RFM korisnike" bez verovatnoće.
    """
    raise NotImplementedError("implementiraj rule_based_score")
