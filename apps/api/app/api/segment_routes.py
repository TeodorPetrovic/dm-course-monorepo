"""Day 2: segmentacija."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


class TrainSeg(BaseModel):
    k: int = Field(4, ge=2, le=10)


@router.post("/segments/train")
def seg_train(body: TrainSeg = TrainSeg()):
    # TEACH d02: seg_train
    _events()
    return svc("seg").train(k=body.k)
    # /TEACH




@router.get("/segments")
def segments():
    # TEACH d02: segments
    return _seg_or_503(lambda: svc("seg").get_segments())
    # /TEACH


@router.get("/customers/{uid}/segment")
@router.get("/segments/customer/{uid}")
def cust_segment(uid: int):
    # TEACH d02: cust_segment
    return _seg_or_503(lambda: svc("seg").get_customer_segment(uid))
    # /TEACH
