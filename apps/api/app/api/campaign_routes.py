"""Day 4: kampanje / targeting."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


@router.get("/campaigns")
def campaigns():
    return svc("target").list_campaigns()


def _campaign(fn):
    from app.services.targeting import UnknownCampaignError
    try:
        return fn()
    except UnknownCampaignError as e:
        raise HTTPException(404, f"unknown campaign {e}")
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/campaigns/{cid}")
def campaign(cid: int):
    return _campaign(lambda: svc("target").get_campaign(cid))


@router.get("/campaigns/{cid}/recommended-audience")
@router.get("/campaigns/{cid}/audience")
def audience(cid: int, limit: int = Query(20, ge=1), mode: Literal["ml", "rule"] = "ml"):
    return _campaign(lambda: svc("target").recommended_audience(cid, limit, mode))


@router.get("/campaigns/{cid}/targeting-comparison")
def tcmp(cid: int, limit: Optional[int] = Query(None, ge=1)):
    if not (svc("seg").is_trained() and svc("conv").is_trained()):
        raise HTTPException(503, "untrained_model")
    return _campaign(lambda: svc("target").targeting_comparison(cid, limit))
