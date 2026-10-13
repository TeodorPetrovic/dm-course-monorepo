"""Day 3: predikcija konverzije."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


class TrainConv(BaseModel):
    model_type: Literal["logistic_regression", "random_forest"] = "logistic_regression"
    window_days: int = Field(7, ge=1, le=30)


@router.post("/models/conversion/train")
def conv_train(body: TrainConv = TrainConv()):
    _events()
    try:
        return svc("conv").train(model_type=body.model_type, window_days=body.window_days)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/models/conversion/status")
@router.get("/analytics/conversion/status")
def conv_status():
    return _seg_or_503(lambda: svc("conv").get_status())


@router.get("/customers/{uid}/conversion-probability")
@router.get("/models/conversion/probability/{uid}")
def conv_prob(uid: int):
    return _seg_or_503(lambda: svc("conv").get_customer_probability(uid))
