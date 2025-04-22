"""
Voice service router
"""
from fastapi import APIRouter

from app.api.v1 import webhooks, realtime

router = APIRouter(prefix="/api/v1")

# Include all API endpoint routers
router.include_router(realtime.router, prefix="", tags=["Voice"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
