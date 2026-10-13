"""Day 1: događaji (POST /events) + deskriptivna analitika (GET /analytics/...)."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


class EventIn(BaseModel):
    event_type: str
    user_id: Optional[int] = None
    user_session: Optional[str] = None
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    source: Optional[str] = None
    timestamp: Optional[str] = None
    recommendation_source: Optional[str] = None
    recommendation_position: Optional[int] = None

    @field_validator("event_type")
    @classmethod
    def _vt(cls, v):
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"nepoznat event_type: {v}")
        return v


@router.post("/events", status_code=201)
def post_event(e: EventIn):
    data = {k: v for k, v in e.model_dump().items() if v is not None}
    try:
        ev = create_event(**data)
    except (ValueError, TypeError) as ex:
        raise HTTPException(422, str(ex))
    return st.get_store().save_event(ev)


@router.post("/recommendations/events", status_code=201)
def post_rec_event(e: EventIn):
    if e.event_type not in ("recommendation_impression", "recommendation_click"):
        raise HTTPException(422, "samo recommendation_impression / recommendation_click")
    return post_event(e)


@router.get("/analytics/summary")
def summary():
    ev = _events()
    f = analytics.calculate_funnel_counts(ev)
    return {**f, "conversion_rate": analytics.calculate_conversion_rate(ev), "n_events": len(ev)}


@router.get("/analytics/products/{pid}/views")
def pviews(pid: int):
    ev = _events(); _known_product(pid)
    return {"product_id": pid, "views": analytics.get_product_view_count(ev, pid)}


@router.get("/analytics/products/{pid}/carts")
def pcarts(pid: int):
    ev = _events(); _known_product(pid)
    return {"product_id": pid, "carts": analytics.get_cart_count(ev, pid)}


@router.get("/analytics/products/{pid}/purchases")
def ppurch(pid: int):
    ev = _events(); _known_product(pid)
    return {"product_id": pid, "purchases": analytics.get_purchase_count(ev, pid)}


@router.get("/analytics/products/{pid}")
def pall(pid: int):
    ev = _events(); _known_product(pid)
    return {"product_id": pid, "views": analytics.get_product_view_count(ev, pid),
            "carts": analytics.get_cart_count(ev, pid), "purchases": analytics.get_purchase_count(ev, pid)}


@router.get("/analytics/conversion-rate")
def conv_rate():
    ev = _events()
    return {**analytics.calculate_funnel_counts(ev), "conversion_rate": analytics.calculate_conversion_rate(ev)}


@router.get("/analytics/share-by-category")
def share(metric: Literal["view", "cart", "purchase"] = "view"):
    return {"metric": metric,
            "shares": analytics.share_by_category(_events(), st.load_products(), metric).to_dict("records")}


@router.get("/analytics/average-order-value")
def aov():
    return {"average_order_value": analytics.average_order_value(st.load_orders())}


@router.get("/analytics/searches")
def searches():
    return {"per_day": analytics.searches_per_day(_events())}
