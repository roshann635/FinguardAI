"""Central API v1 router — combines all sub-routers under /api/v1."""

from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.data_quality import router as data_quality_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.risk import router as risk_router
from app.api.v1.system import router as system_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(risk_router)
api_router.include_router(forecast_router)
api_router.include_router(data_quality_router)
api_router.include_router(ai_router)
api_router.include_router(system_router)
