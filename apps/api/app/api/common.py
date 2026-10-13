"""Zajedničko za sve *_routes.py module: lenji servisi, provere, store."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.data import analytics
from app.data.events import VALID_EVENT_TYPES, create_event
from app.services import store as st

_cache: dict = {}


def svc(name):
    if name not in _cache:
        from app.services import (ai, collaborative, conversion, evaluation, hybrid, platform, recommender,
                                  segmentation, semantic, session, targeting)
        _cache[name] = {"seg": segmentation.SegmentationService, "conv": conversion.ConversionService,
                        "target": targeting.TargetingService, "rec": recommender.RecommenderService,
                        "cf": collaborative.CollaborativeRecommenderService,
                        "hybrid": hybrid.HybridRecommenderService, "session": session.SessionRecommenderService,
                        "semantic": semantic.SemanticService, "ai": ai.AIService,
                        "platform": platform.IntegratedPlatformService,
                        "eval": evaluation.RecommendationEvaluationService}[name]()
    return _cache[name]


def reset_services():
    _cache.clear()


def _events():
    try:
        return st.require_events()
    except st.EmptyStoreError:
        raise HTTPException(503, "empty_store")


def _known_product(pid):
    if pid not in set(st.load_products()["product_id"]):
        raise HTTPException(404, f"unknown product {pid}")


def _seg_or_503(fn):
    from app.services.segmentation import UntrainedModelError
    try:
        return fn()
    except UntrainedModelError:
        raise HTTPException(503, "untrained_model")
