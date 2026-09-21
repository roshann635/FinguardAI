"""AI Analyst routes for FinGuard AI — /api/v1/ai."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import GeminiClient
from app.database import get_db
from app.schemas.ai import (
    AIQueryRequest,
    AIResponse,
    ExecutiveBriefRequest,
    ExecutiveBriefResponse,
)
from app.services.context_builder import FinancialContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analyst"])


@router.post("/ask", response_model=AIResponse)
async def ask_finguard_ai(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
) -> AIResponse:
    """Answer a financial question grounded in verified analytics.

    Flow:
    1. Build financial context via FinancialContextBuilder.
    2. Forward question + context to GeminiClient.ask_question().
    3. Return structured AIResponse.

    If Gemini is unavailable the endpoint still returns a valid AIResponse
    whose summary explains the outage — the context period is preserved so
    the caller can display it alongside dashboard data.
    """
    period: str = request.context_period or "last_12_months"
    logger.info("AI ask — period=%s question_length=%d", period, len(request.question))

    try:
        context_builder = FinancialContextBuilder(db)
        context = context_builder.build_query_context(request.question, period)
    except Exception:
        logger.exception("Context build failed for ask_finguard_ai.")
        context = {"period": period}

    client = GeminiClient()
    return client.ask_question(request.question, context)


@router.post("/executive-brief", response_model=ExecutiveBriefResponse)
async def generate_executive_brief(
    request: ExecutiveBriefRequest,
    db: Session = Depends(get_db),
) -> ExecutiveBriefResponse:
    """Generate a comprehensive AI executive financial brief.

    Flow:
    1. Build full financial context via FinancialContextBuilder.
    2. Forward context to GeminiClient.generate_executive_brief().
    3. Return structured ExecutiveBriefResponse (always includes disclaimer).

    If Gemini is unavailable the endpoint returns a graceful fallback
    ExecutiveBriefResponse — the endpoint itself never raises a 5xx.
    """
    period: str = request.period or "last_12_months"
    logger.info("AI executive-brief — period=%s", period)

    try:
        context_builder = FinancialContextBuilder(db)
        context = context_builder.build_context(period)
    except Exception:
        logger.exception("Context build failed for generate_executive_brief.")
        context = {"period": period}

    client = GeminiClient()
    return client.generate_executive_brief(context)
