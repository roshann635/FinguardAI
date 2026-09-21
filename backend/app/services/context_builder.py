"""Financial context builder for FinGuard AI — assembles structured data for Gemini."""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.analytics import (
    BudgetAnalyticsService,
    CashFlowService,
    ExpenseAnalyticsService,
    KPIService,
    ProfitabilityService,
    ReceivablesService,
    RevenueAnalyticsService,
)
from app.ml import AnomalyDetectionService
from app.services.risk_engine import RiskOpportunityActionEngine
from app.utils.formatters import safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

_DATA_NOTE = "Synthetic demonstration dataset — FinGuard AI"


def _period_bounds(period: str) -> tuple[date, date, date, date]:
    """Return (curr_start, curr_end, prev_start, prev_end) for the named period."""
    today = get_as_of_date()
    if period == "last_30_days":
        curr_end = today
        curr_start = today - timedelta(days=29)
    elif period == "last_90_days":
        curr_end = today
        curr_start = today - timedelta(days=89)
    elif period == "ytd":
        curr_end = today
        curr_start = date(today.year, 1, 1)
    elif period == "last_year":
        curr_end = date(today.year - 1, 12, 31)
        curr_start = date(today.year - 1, 1, 1)
    else:  # last_12_months (default)
        curr_end = today
        curr_start = today - timedelta(days=364)
    prev_end = curr_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=364)
    return curr_start, curr_end, prev_start, prev_end


class FinancialContextBuilder:
    """
    Builds the verified financial context object sent to Gemini.
    Gemini ONLY receives this structured context, never raw DB data.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_context(self, period: str = "last_12_months") -> dict:
        """
        Returns a comprehensive structured context object with KPIs, trends,
        risks, opportunities, anomaly summary, budget summary, receivables
        summary, and top category breakdowns.
        """
        cs, ce, ps, pe = _period_bounds(period)

        kpi_svc = KPIService(self.db)
        rev_svc = RevenueAnalyticsService(self.db)
        exp_svc = ExpenseAnalyticsService(self.db)
        prof_svc = ProfitabilityService(self.db)
        cf_svc = CashFlowService(self.db)
        budget_svc = BudgetAnalyticsService(self.db)
        rec_svc = ReceivablesService(self.db)
        anomaly_svc = AnomalyDetectionService(self.db)
        engine = RiskOpportunityActionEngine(self.db)

        # KPIs
        kpis: dict = {}
        try:
            curr_rev = kpi_svc.calculate_revenue(cs, ce)
            prev_rev = kpi_svc.calculate_revenue(ps, pe)
            curr_profit = kpi_svc.calculate_net_profit(cs, ce)
            prev_profit = kpi_svc.calculate_net_profit(ps, pe)
            curr_exp = kpi_svc.calculate_total_expenses(cs, ce)
            gross_margin = kpi_svc.calculate_gross_margin(cs, ce)
            net_margin = kpi_svc.calculate_net_margin(cs, ce)
            net_cf = kpi_svc.calculate_net_cash_flow(cs, ce)
            rev_growth = safe_divide(curr_rev - prev_rev, prev_rev) * 100 if prev_rev else 0.0
            receivables = kpi_svc.calculate_outstanding_receivables()

            kpis = {
                "revenue": {"value": round(curr_rev, 2), "previous": round(prev_rev, 2)},
                "net_profit": {"value": round(curr_profit, 2), "previous": round(prev_profit, 2)},
                "gross_margin_pct": round(gross_margin, 2),
                "net_margin_pct": round(net_margin, 2),
                "total_expenses": round(curr_exp, 2),
                "net_cash_flow": round(net_cf, 2),
                "revenue_growth_pct": round(rev_growth, 2),
                "outstanding_receivables": round(receivables, 2),
            }
        except Exception:
            logger.exception("KPI context build failed")

        # Trends — last 6 months summaries
        trends: dict = {}
        try:
            six_months_ago = ce - timedelta(days=180)
            trends["revenue_trend"] = [
                {"date": p.date, "value": p.value}
                for p in rev_svc.get_revenue_trend(six_months_ago, ce, "monthly")
            ]
            trends["expense_trend"] = [
                {"date": p.date, "value": p.value}
                for p in exp_svc.get_expense_trend(six_months_ago, ce)
            ]
            trends["margin_trend"] = prof_svc.get_margin_trend(six_months_ago, ce)
            trends["cashflow_trend"] = cf_svc.get_cashflow_trend(six_months_ago, ce)
        except Exception:
            logger.exception("Trend context build failed")

        # Risks & opportunities from engine
        risks_raw: list = []
        opportunities_raw: list = []
        try:
            risks_raw = [r.model_dump() for r in engine.get_risks()]
            opportunities_raw = [o.model_dump() for o in engine.get_opportunities()]
        except Exception:
            logger.exception("Risk/opportunity context build failed")

        # Anomaly summary
        anomaly_summary: dict = {}
        try:
            anomaly_summary = anomaly_svc.get_anomaly_summary()
        except Exception:
            logger.exception("Anomaly summary context build failed")

        # Budget summary
        budget_summary: dict = {}
        try:
            year = get_as_of_date().year
            overruns = budget_svc.get_overspending_areas(year)
            underutilized = budget_svc.get_underutilized_budget(year)
            budget_summary = {
                "year": year,
                "overspending_count": len(overruns),
                "underutilized_count": len(underutilized),
                "top_overruns": [
                    {"category": i.category, "department": i.department, "variance_pct": i.variance_pct}
                    for i in overruns[:3]
                ],
            }
        except Exception:
            logger.exception("Budget summary context build failed")

        # Receivables summary
        receivables_summary: dict = {}
        try:
            aging = rec_svc.get_aging_summary()
            receivables_summary = aging.model_dump()
        except Exception:
            logger.exception("Receivables summary context build failed")

        # Top category breakdowns (top 5)
        top_expense_categories: list = []
        top_revenue_categories: list = []
        try:
            top_expense_categories = [
                {"category": c.category, "value": c.value, "pct_of_total": c.pct_of_total}
                for c in exp_svc.get_expense_by_category(cs, ce)[:5]
            ]
            top_revenue_categories = [
                {"category": c.category, "value": c.value, "pct_of_total": c.pct_of_total}
                for c in rev_svc.get_revenue_by_category(cs, ce)[:5]
            ]
        except Exception:
            logger.exception("Category breakdown context build failed")

        return {
            "period": period,
            "as_of_date": get_as_of_date().isoformat(),
            "data_note": _DATA_NOTE,
            "kpis": kpis,
            "trends": trends,
            "risks": risks_raw,
            "opportunities": opportunities_raw,
            "anomaly_summary": anomaly_summary,
            "budget_summary": budget_summary,
            "receivables_summary": receivables_summary,
            "top_expense_categories": top_expense_categories,
            "top_revenue_categories": top_revenue_categories,
        }

    def build_query_context(self, question: str, period: str = "last_12_months") -> dict:
        """Builds context enriched with question-specific data."""
        ctx = self.build_context(period)
        ctx["user_question"] = question
        return ctx
