"""Analytics routes for FinGuard AI."""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics import (
    BudgetAnalyticsService,
    CashFlowService,
    ExpenseAnalyticsService,
    ProfitabilityService,
    ReceivablesService,
    RevenueAnalyticsService,
)
from app.database import get_db
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/revenue")
def get_revenue_analytics(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    granularity: str = Query(default="monthly", description="monthly | weekly | quarterly"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Revenue analytics.

    Returns revenue time series, breakdown by category and region,
    month-over-month growth trend, and top revenue contributors.
    """
    try:
        svc = RevenueAnalyticsService(db)
        return {
            "revenue_trend": [p.model_dump() for p in svc.get_revenue_trend(start_date, end_date, granularity)],
            "by_category": [c.model_dump() for c in svc.get_revenue_by_category(start_date, end_date)],
            "by_region": [r.model_dump() for r in svc.get_revenue_by_region(start_date, end_date)],
            "growth_trend": svc.get_revenue_growth_trend(months=12),
            "top_contributors": svc.get_top_revenue_contributors(start_date, end_date),
        }
    except Exception as exc:
        logger.exception("Revenue analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue analytics") from exc


@router.get("/profit")
def get_profit_analytics(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Profitability analytics.

    Returns profit time series, margin trend, and breakdowns by
    category and region.
    """
    try:
        svc = ProfitabilityService(db)
        return {
            "profit_trend": svc.get_profit_trend(start_date, end_date),
            "margin_trend": svc.get_margin_trend(start_date, end_date),
            "by_category": svc.get_profit_by_category(start_date, end_date),
            "by_region": svc.get_profit_by_region(start_date, end_date),
        }
    except Exception as exc:
        logger.exception("Profit analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve profit analytics") from exc


@router.get("/expenses")
def get_expense_analytics(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Expense analytics.

    Returns expense time series, breakdown by category and department,
    and the expense-to-revenue ratio.
    """
    try:
        svc = ExpenseAnalyticsService(db)
        return {
            "expense_trend": [p.model_dump() for p in svc.get_expense_trend(start_date, end_date)],
            "by_category": [c.model_dump() for c in svc.get_expense_by_category(start_date, end_date)],
            "by_department": svc.get_expense_by_department(start_date, end_date),
            "expense_revenue_ratio": svc.get_expense_to_revenue_ratio(start_date, end_date),
        }
    except Exception as exc:
        logger.exception("Expense analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve expense analytics") from exc


@router.get("/cashflow")
def get_cashflow_analytics(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Cash flow analytics.

    Returns monthly cash flow trend, breakdown by category,
    and cumulative net cash flow.
    """
    try:
        svc = CashFlowService(db)
        return {
            "cashflow_trend": svc.get_cashflow_trend(start_date, end_date),
            "by_category": svc.get_cashflow_by_category(start_date, end_date),
            "cumulative": svc.get_cumulative_cashflow(start_date, end_date),
        }
    except Exception as exc:
        logger.exception("Cash flow analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve cash flow analytics") from exc


@router.get("/budget")
def get_budget_analytics(
    year: Optional[int] = Query(default=None, description="Budget year (e.g. 2024). Defaults to data as-of year."),
    db: Session = Depends(get_db),
) -> dict:
    """
    Budget analytics.

    Returns budget vs actual variance, monthly budget trend,
    overspending areas, and underutilised budget items.
    """
    try:
        if year is None:
            year = get_as_of_date().year
        svc = BudgetAnalyticsService(db)
        return {
            "budget_vs_actual": [i.model_dump() for i in svc.get_budget_vs_actual(year)],
            "budget_trend": svc.get_budget_trend(year),
            "overspending": [i.model_dump() for i in svc.get_overspending_areas(year)],
            "underutilized": [i.model_dump() for i in svc.get_underutilized_budget(year)],
            "year": year,
        }
    except Exception as exc:
        logger.exception("Budget analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve budget analytics") from exc


@router.get("/receivables")
def get_receivables_analytics(
    db: Session = Depends(get_db),
) -> dict:
    """
    Receivables analytics.

    Returns aging summary buckets, aging trend over the last 6 months,
    top overdue accounts, and collection efficiency metrics.
    """
    try:
        svc = ReceivablesService(db)
        return {
            "aging_summary": svc.get_aging_summary().model_dump(),
            "aging_trend": svc.get_aging_trend(months=6),
            "top_overdue": svc.get_top_overdue_accounts(limit=10),
            "collection_efficiency": svc.get_collection_efficiency(months=6),
        }
    except Exception as exc:
        logger.exception("Receivables analytics failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve receivables analytics") from exc
