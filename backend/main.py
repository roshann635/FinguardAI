"""FinGuard AI — FastAPI application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config.settings import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FinGuard AI",
    version="1.0.0",
    description=(
        "FinGuard AI is an intelligent financial analytics platform that combines "
        "dynamic KPI monitoring, ML-powered anomaly detection, revenue forecasting, "
        "risk scoring, and a Gemini-backed AI assistant to help finance teams make "
        "evidence-based decisions."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(api_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Lightweight liveness probe — returns app status and version."""
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent JSON body for 404 Not Found."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "detail": f"The requested path '{request.url.path}' does not exist.",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent JSON body for unhandled 500 errors."""
    logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    """Log application start and initialise analytical date from the dataset."""
    logger.info(
        "FinGuard AI v%s started — environment: %s, debug: %s",
        settings.app_version,
        settings.environment,
        settings.debug,
    )
    # Initialise DATA_AS_OF_DATE from the dataset so analytics use the correct
    # reference date instead of the system clock.
    from app.database import get_db
    from app.utils.date_utils import init_as_of_date

    try:
        db = next(get_db())
        as_of = init_as_of_date(db)
        logger.info("Analytical as-of date: %s", as_of)
        db.close()
    except Exception:
        logger.warning("Could not initialise DATA_AS_OF_DATE; analytics may use system date", exc_info=True)
