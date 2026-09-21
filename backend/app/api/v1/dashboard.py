"""Dashboard routes for FinGuard AI."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics import KPIService
from app.database import get_db
from app.services import RiskOpportunityActionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def get_dashboard_overview(
    period: str = Query(default="last_12_months", description="Period key: last_12_months | last_90_days | last_30_days | ytd | last_year"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Executive dashboard overview.

    Returns the full ExecutiveKPIs snapshot, top insight cards,
    top 3 risks, top 3 opportunities, and top 3 recommended actions.
    """
    try:
        kpi_svc = KPIService(db)
        engine = RiskOpportunityActionEngine(db)

        kpis = kpi_svc.get_executive_kpis(period)
        insight_cards = engine.get_insight_cards()
        risks = engine.get_risks()[:3]
        opportunities = engine.get_opportunities()[:3]
        actions = engine.get_recommended_actions()[:3]

        return {
            "kpis": kpis.model_dump(),
            "insight_cards": [c.model_dump() for c in insight_cards],
            "risks": [r.model_dump() for r in risks],
            "opportunities": [o.model_dump() for o in opportunities],
            "actions": [a.model_dump() for a in actions],
            "period": period,
        }
    except Exception as exc:
        logger.exception("Dashboard overview failed")
        raise HTTPException(status_code=500, detail="Failed to build dashboard overview") from exc


@router.get("/health-summary")
def get_health_summary(
    db: Session = Depends(get_db),
) -> dict:
    """
    Financial health indicator summary.

    Returns a set of named health signals derived from current KPIs
    and risk indicators.
    """
    try:
        kpi_svc = KPIService(db)
        engine = RiskOpportunityActionEngine(db)

        kpis = kpi_svc.get_executive_kpis("last_12_months")
        risks = engine.get_risks()

        critical_count = sum(1 for r in risks if r.severity == "CRITICAL")
        high_count = sum(1 for r in risks if r.severity == "HIGH")
        medium_count = sum(1 for r in risks if r.severity == "MEDIUM")

        # Overall health: GREEN / AMBER / RED
        if critical_count > 0 or high_count >= 3:
            overall_health = "RED"
        elif high_count >= 1 or medium_count >= 3:
            overall_health = "AMBER"
        else:
            overall_health = "GREEN"

        return {
            "overall_health": overall_health,
            "critical_risk_count": critical_count,
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "revenue_direction": kpis.revenue_growth_pct.direction,
            "profit_margin_pct": kpis.profit_margin.value,
            "net_cash_flow": kpis.net_cash_flow.value,
            "budget_variance_pct": kpis.budget_variance_pct.value,
            "outstanding_receivables": kpis.outstanding_receivables.value,
            "as_of_date": kpis.as_of_date,
        }
    except Exception as exc:
        logger.exception("Health summary failed")
        raise HTTPException(status_code=500, detail="Failed to build health summary") from exc


@router.get("/health-score")
def get_financial_health_score(
    db: Session = Depends(get_db),
) -> dict:
    """
    Composite Financial Health Score.

    Evaluates solvency, liquidity, margin defense, credit quality,
    and operational stability on a 0-100 scale across 4 core pillars.
    """
    try:
        from app.services.health_service import FinancialHealthService
        svc = FinancialHealthService(db)
        return svc.calculate_health_score()
    except Exception as exc:
        logger.exception("Health score calculation failed")
        raise HTTPException(status_code=500, detail="Failed to calculate financial health score") from exc



@router.get("/investigation")
def get_kpi_investigation(
    kpi: str = Query(default="profit", description="Target KPI key: profit | revenue | receivables | expenses"),
    period: str = Query(default="last_12_months", description="Period key"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Investigation Mode drilldown.

    Returns structured root-cause diagnostic:
    1. What changed? (Headline metric change, baseline comparison)
    2. Why did it change? (Ranked primary root causes with verified drivers)
    3. Evidence (Exact database numbers, SQL sources, benchmarks)
    4. What should management do? (Prioritized concrete actionable decisions)
    """
    try:
        from app.services.investigation import InvestigationService
        svc = InvestigationService(db)
        return svc.investigate_kpi(kpi=kpi, period=period)
    except Exception as exc:
        logger.exception("Investigation drilldown failed for kpi=%s", kpi)
        raise HTTPException(status_code=500, detail="Failed to run KPI investigation drilldown") from exc

