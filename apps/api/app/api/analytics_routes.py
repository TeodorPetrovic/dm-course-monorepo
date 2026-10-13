"""Day 7–9: analitika preporuka (offline evaluacija, hybrid, CTR)."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


@router.get("/analytics/recommendations")
def rec_eval(k: int = Query(5, ge=1, le=20), split_ratio: float = Query(0.8, gt=0.5, lt=1.0)):
    # TEACH d07: rec_eval
    import pandas as pd
    from app.data.paths import day_data
    from app.recommenders.evaluation import build_comparison_report
    _events()
    return svc("eval").comparison_report(k, split_ratio)
    # /TEACH


@router.get("/analytics/recommendations/hybrid")
def rec_hybrid(k: int = Query(5, ge=1, le=20), max_test_users: Optional[int] = Query(None, ge=1)):
    return svc("hybrid").user_based_comparison(k, max_test_users)


@router.get("/analytics/recommendations/ctr")
def rec_ctr():
    # TEACH d09: rec_ctr
    return svc("session").ctr_dashboard()
    # /TEACH


@router.get("/analytics/recommendations/session-comparison")
def rec_session_cmp():
    return svc("session").popular_vs_personalized_comparison()
