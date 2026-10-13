"""Day 11: generativni AI (SEO, sadržaj)."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


class SEOIn(BaseModel):
    product_name: str = Field(..., min_length=1)
    description: str = ""
    category_name: str = ""


class ContentIn(BaseModel):
    kind: Literal["product_description", "campaign_copy"]
    product_name: str = ""
    description: str = ""
    category_name: str = ""
    campaign_name: str = ""
    campaign_goal: str = ""
    campaign_audience: str = ""


@router.post("/ai/seo")
def ai_seo(b: SEOIn):
    # TEACH d11: ai_seo
    if not b.product_name.strip():
        raise HTTPException(422, "product_name je obavezan")
    return svc("ai").generate_seo_metadata({"name": b.product_name, "description": b.description,
                                            "category": b.category_name})
    # /TEACH


@router.post("/ai/content")
def ai_content(b: ContentIn):
    if b.kind == "product_description":
        if not b.product_name.strip():
            raise HTTPException(422, "product_name je obavezan")
        return svc("ai").generate_product_description({"name": b.product_name, "description": b.description,
                                                       "category": b.category_name})
    if not b.campaign_name.strip():
        raise HTTPException(422, "campaign_name je obavezan")
    return svc("ai").generate_campaign_copy({"name": b.campaign_name, "goal": b.campaign_goal,
                                             "target_segments": b.campaign_audience})
