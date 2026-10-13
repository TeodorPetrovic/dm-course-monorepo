"""Svi API endpointi kursa (Day 1–12), po danu u zasebnim modulima; ovde se spajaju u jedan router.

Redosled je bitan: statičke rute pre parametarskih (npr. /recommendations/popular pre /recommendations/{user_id}).
"""
from fastapi import APIRouter

from app.api import (ai_routes, analytics_routes, campaign_routes, conversion_routes, event_routes, platform_routes,
                     recommendation_routes, segment_routes)
from app.api.common import reset_services, svc  # noqa: F401  (testovi koriste reset_services)

router = APIRouter()
for _m in (event_routes, segment_routes, conversion_routes, campaign_routes, analytics_routes, recommendation_routes,
           ai_routes, platform_routes):
    router.include_router(_m.router)
