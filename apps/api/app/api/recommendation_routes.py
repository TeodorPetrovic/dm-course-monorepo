"""Day 5–10: preporuke (statičke rute PRE parametarskih: /recommendations/popular pre /{user_id})."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.common import _events, _known_product, svc, _seg_or_503, st, analytics, create_event, VALID_EVENT_TYPES  # noqa: F401

router = APIRouter()


@router.get("/recommendations/popular")
def popular(limit: int = Query(5, ge=1, le=50)):
    return svc("rec").popular_recommendations(limit)


@router.get("/recommendations/category/{pid}")
def category(pid: int, limit: int = Query(5, ge=1, le=50)):
    from app.services.recommender import UnknownProductError
    try:
        return svc("rec").category_recommendations(pid, limit)
    except UnknownProductError:
        raise HTTPException(404, f"unknown product {pid}")


@router.get("/recommendations/content/{pid}")
def content(pid: int, limit: int = Query(5, ge=1, le=50)):
    # TEACH d05: content
    return svc("rec").content_recommendations(pid, limit)
    # /TEACH


@router.get("/recommendations/content/{pid}/comparison")
def content_cmp(pid: int, limit: int = Query(5, ge=1, le=50)):
    _known_product(pid)
    return svc("rec").baseline_comparison(pid, limit)


@router.get("/recommendations/collaborative/{pid}")
def collab(pid: int, limit: int = Query(5, ge=1, le=50)):
    # TEACH d06: collab
    return svc("cf").collaborative_recommendations(pid, limit)
    # /TEACH


@router.get("/recommendations/collaborative/{pid}/comparison")
def collab_cmp(pid: int, limit: int = Query(5, ge=1, le=50)):
    return svc("cf").collaborative_comparison(pid, limit)


@router.get("/recommendations/session/{sid}")
def session_recs(sid: str, limit: int = Query(5, ge=1, le=50)):
    # TEACH d09: session_recs
    return svc("session").recommend_for_session(sid, limit)
    # /TEACH


@router.get("/recommendations/semantic/{pid}")
def semantic_recs(pid: int, limit: int = Query(5, ge=1, le=50)):
    # TEACH d10: semantic_recs
    return svc("semantic").recommendations_for_product(pid, limit)
    # /TEACH


@router.get("/search/semantic")
def semantic_search(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=50)):
    # TEACH d10: semantic_search
    return svc("semantic").semantic_search(q, limit)
    # /TEACH


@router.get("/recommendations/legacy/{pid}")
def legacy(pid: int, limit: int = Query(5, ge=1, le=50)):
    """Day 1 rule-based placeholder (ranije /recommendations/{product_id}) — session co-occurrence heuristika."""
    return svc("cf").heuristic_recommendations(pid, limit)


@router.get("/recommendations/user/{uid}")
@router.get("/recommendations/{uid}")
def hybrid(uid: int, limit: int = Query(5, ge=1, le=50)):
    # TEACH d08: hybrid
    return svc("hybrid").recommend_for_user(uid, limit)
    # /TEACH
