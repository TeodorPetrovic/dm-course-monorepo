"""Day 12: integrisana platforma."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


@router.get("/platform/modules")
def p_modules():
    return svc("platform").module_status()


@router.get("/platform/profile/{uid}")
def p_profile(uid: int):
    return svc("platform").profile_for_user(uid)


@router.get("/platform/homepage")
def p_home(user_id: int, session_id: Optional[str] = None, limit: int = Query(5, ge=1, le=20)):
    # TEACH d12: p_home
    return svc("platform").homepage_payload(user_id, session_id, limit)
    # /TEACH


@router.get("/platform/product/{pid}")
def p_product(pid: int):
    # TEACH d12: p_product
    try:
        return svc("platform").product_page_payload(pid)
    except KeyError:
        raise HTTPException(404, f"unknown product {pid}")
    # /TEACH
