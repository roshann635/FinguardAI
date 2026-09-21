"""KPI calculation service for FinGuard AI executive dashboards."""

import logging
from datetime import date, datetime, timedelta

from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Budget, CashFlow, Expense, Invoice, Transaction
from app.schemas import ExecutiveKPIs, KPIValue
from app.utils.date_utils import get_as_of_date
from app.utils.formatters import (
    format_currency,
    format_percentage,
    get_direction,
    get_period_label,
    safe_divide,
)

logger = logging.getLogger(__name__)


def _date_filter(start_date: Optional[date], end_date: Optional[date], col):
    """Return a list of filter expressions for an optional date range."""
    filters = []
    if start_date:
        filters.append(col >= start_date)
    if end_date:
        filters.append(col <= end_date)
    return filters


class KPIService:
    """Compute core financial KPIs from the database."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Revenue & COGS
    # ------------------------------------------------------------------

    def calculate_revenue(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        """SUM of net sale amounts (after discount) for completed sales."""
        try:
            q = self.db.query(
                func.sum(
                    Transaction.amount * (1 - Transaction.discount_pct / 100)
                )
            ).filter(
                Transaction.transaction_type == "sale",
                Transaction.status == "completed",
                *_date_filter(start_date, end_date, Transaction.transaction_date),
            )
            result = q.scalar()
            return float(result or 0)
        except Exception:
            logger.exception("calculate_revenue failed")
            return 0.0

    def calculate_cogs(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        """SUM of (cost × quantity) for completed sales."""
        try:
            q = self.db.query(
                func.sum(Transaction.cost * Transaction.quantity)
            ).filter(
                Transaction.transaction_type == "sale",
                Transaction.status == "completed",
                *_date_filter(start_date, end_date, Transaction.transaction_date),
            )
            result = q.scalar()
            return float(result or 0)
        except Exception:
            logger.exception("calculate_cogs failed")
            return 0.0

    def calculate_gross_profit(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        return self.calculate_revenue(start_date, end_date) - self.calculate_cogs(start_date, end_date)

    def calculate_gross_margin(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        revenue = self.calculate_revenue(start_date, end_date)
        gross_profit = self.calculate_gross_profit(start_date, end_date)
        return safe_divide(gross_profit, revenue) * 100

    # ------------------------------------------------------------------
    # Expenses & Operating metrics
    # ------------------------------------------------------------------

    def calculate_total_expenses(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        """SUM of approved expenses in the period."""
        try:
            q = self.db.query(func.sum(Expense.amount)).filter(
                Expense.status == "approved",
                *_date_filter(start_date, end_date, Expense.expense_date),
            )
            result = q.scalar()
            return float(result or 0)
        except Exception:
            logger.exception("calculate_total_expenses failed")
            return 0.0

    def calculate_operating_profit(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        return self.calculate_gross_profit(start_date, end_date) - self.calculate_total_expenses(start_date, end_date)

    def calculate_net_profit(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        return self.calculate_revenue(start_date, end_date) - self.calculate_total_expenses(start_date, end_date)

    def calculate_net_margin(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        revenue = self.calculate_revenue(start_date, end_date)
        net_profit = self.calculate_net_profit(start_date, end_date)
        return safe_divide(net_profit, revenue) * 100

    # ------------------------------------------------------------------
    # Cash flow
    # ------------------------------------------------------------------

    def calculate_cash_inflow(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        try:
            q = self.db.query(func.sum(CashFlow.amount)).filter(
                CashFlow.flow_type == "inflow",
                *_date_filter(start_date, end_date, CashFlow.flow_date),
            )
            return float(q.scalar() or 0)
        except Exception:
            logger.exception("calculate_cash_inflow failed")
            return 0.0

    def calculate_cash_outflow(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        try:
            q = self.db.query(func.sum(CashFlow.amount)).filter(
                CashFlow.flow_type == "outflow",
                *_date_filter(start_date, end_date, CashFlow.flow_date),
            )
            return float(q.scalar() or 0)
        except Exception:
            logger.exception("calculate_cash_outflow failed")
            return 0.0

    def calculate_net_cash_flow(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        return self.calculate_cash_inflow(start_date, end_date) - self.calculate_cash_outflow(start_date, end_date)

    # ------------------------------------------------------------------
    # Budget variance
    # ------------------------------------------------------------------

    def calculate_budget_variance(
        self,
        year: int,
        month: Optional[int] = None,
    ) -> dict:
        """Compare actual approved expenses vs budgeted amount for a period."""
        try:
            budget_q = self.db.query(func.sum(Budget.budget_amount)).filter(
                Budget.period_year == year,
                *([] if month is None else [Budget.period_month == month]),
            )
            budget_total = float(budget_q.scalar() or 0)

            exp_start = date(year, month or 1, 1)
            if month is None:
                exp_end = date(year, 12, 31)
            else:
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                exp_end = date(year, month, last_day)

            actual = self.calculate_total_expenses(exp_start, exp_end)
            variance = actual - budget_total
            variance_pct = safe_divide(actual - budget_total, budget_total) * 100

            return {
                "budget": budget_total,
                "actual": actual,
                "variance": variance,
                "variance_pct": variance_pct,
            }
        except Exception:
            logger.exception("calculate_budget_variance failed")
            return {"budget": 0.0, "actual": 0.0, "variance": 0.0, "variance_pct": 0.0}

    # ------------------------------------------------------------------
    # Growth & averages
    # ------------------------------------------------------------------

    def calculate_revenue_growth(
        self,
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date,
    ) -> float:
        current = self.calculate_revenue(current_start, current_end)
        previous = self.calculate_revenue(previous_start, previous_end)
        return safe_divide(current - previous, previous) * 100

    def calculate_avg_transaction_value(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> float:
        revenue = self.calculate_revenue(start_date, end_date)
        try:
            count_q = self.db.query(func.count(Transaction.transaction_id)).filter(
                Transaction.transaction_type == "sale",
                Transaction.status == "completed",
                *_date_filter(start_date, end_date, Transaction.transaction_date),
            )
            count = int(count_q.scalar() or 0)
        except Exception:
            logger.exception("calculate_avg_transaction_value count failed")
            count = 0
        return safe_divide(revenue, count)

    def calculate_outstanding_receivables(self) -> float:
        """SUM(invoice_amount - paid_amount) for unpaid / partial / overdue invoices."""
        try:
            q = self.db.query(
                func.sum(Invoice.invoice_amount - Invoice.paid_amount)
            ).filter(
                Invoice.payment_status.in_(["unpaid", "partial", "overdue"])
            )
            return float(q.scalar() or 0)
        except Exception:
            logger.exception("calculate_outstanding_receivables failed")
            return 0.0

    # ------------------------------------------------------------------
    # Period helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_period(period: str) -> tuple[date, date, date, date]:
        """Return (curr_start, curr_end, prev_start, prev_end) for a named period."""
        today = get_as_of_date()
        if period == "last_30_days":
            curr_end = today
            curr_start = today - timedelta(days=29)
            prev_end = curr_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=29)
        elif period == "last_90_days":
            curr_end = today
            curr_start = today - timedelta(days=89)
            prev_end = curr_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=89)
        elif period == "ytd":
            curr_start = date(today.year, 1, 1)
            curr_end = today
            prev_start = date(today.year - 1, 1, 1)
            prev_end = date(today.year - 1, today.month, today.day)
        elif period == "last_year":
            curr_start = date(today.year - 1, 1, 1)
            curr_end = date(today.year - 1, 12, 31)
            prev_start = date(today.year - 2, 1, 1)
            prev_end = date(today.year - 2, 12, 31)
        else:  # last_12_months (default)
            curr_end = today
            curr_start = today - timedelta(days=364)
            prev_end = curr_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=364)
        return curr_start, curr_end, prev_start, prev_end

    # ------------------------------------------------------------------
    # Executive KPI summary
    # ------------------------------------------------------------------

    def get_executive_kpis(self, period: str = "last_12_months") -> ExecutiveKPIs:
        """Build the full ExecutiveKPIs response for the dashboard."""
        cs, ce, ps, pe = self._resolve_period(period)

        curr_revenue = self.calculate_revenue(cs, ce)
        prev_revenue = self.calculate_revenue(ps, pe)
        curr_net_profit = self.calculate_net_profit(cs, ce)
        prev_net_profit = self.calculate_net_profit(ps, pe)
        curr_margin = self.calculate_net_margin(cs, ce)
        prev_margin = self.calculate_net_margin(ps, pe)
        curr_expenses = self.calculate_total_expenses(cs, ce)
        prev_expenses = self.calculate_total_expenses(ps, pe)
        curr_ncf = self.calculate_net_cash_flow(cs, ce)
        prev_ncf = self.calculate_net_cash_flow(ps, pe)
        bv = self.calculate_budget_variance(ce.year)
        curr_bv_pct = bv["variance_pct"]
        prev_bv = self.calculate_budget_variance(pe.year)
        prev_bv_pct = prev_bv["variance_pct"]
        rev_growth = self.calculate_revenue_growth(cs, ce, ps, pe)
        prev_rev_growth = 0.0  # no prior-prior period computed here
        receivables = self.calculate_outstanding_receivables()

        def _kpi(
            curr: float,
            prev: float,
            fmt_fn,
            interp_up: str = "Positive trend",
            interp_down: str = "Needs attention",
            higher_is_better: bool = True,
        ) -> KPIValue:
            change_abs = curr - prev
            change_pct = safe_divide(curr - prev, abs(prev)) * 100 if prev != 0 else 0.0
            direction = get_direction(change_pct)
            if direction == "up":
                interpretation = interp_up if higher_is_better else interp_down
            elif direction == "down":
                interpretation = interp_down if higher_is_better else interp_up
            else:
                interpretation = "Stable"
            return KPIValue(
                value=curr,
                formatted=fmt_fn(curr),
                previous_value=prev,
                change_abs=round(change_abs, 2),
                change_pct=round(change_pct, 2),
                direction=direction,
                interpretation=interpretation,
            )

        exp_to_rev_curr = safe_divide(curr_expenses, curr_revenue) * 100
        exp_to_rev_prev = safe_divide(prev_expenses, prev_revenue) * 100

        profit_kpi = _kpi(
            curr_net_profit, prev_net_profit, format_currency,
            interp_up="Profitability improving",
            interp_down="Profit under pressure — investigate cost drivers",
        )
        growth_kpi = _kpi(
            rev_growth, prev_rev_growth, lambda v: format_percentage(v),
            interp_up="Strong revenue growth momentum",
            interp_down="Revenue growth slowing",
        )
        receivables_kpi = KPIValue(
            value=receivables,
            formatted=format_currency(receivables),
            interpretation="Monitor ageing — high receivables strain cash flow" if receivables > 0 else "No outstanding receivables",
        )
        exp_rev_kpi = _kpi(
            exp_to_rev_curr, exp_to_rev_prev, lambda v: format_percentage(v),
            interp_up="Expense-to-revenue ratio increased",
            interp_down="Expense-to-revenue ratio improved",
            higher_is_better=False,
        )

        return ExecutiveKPIs(
            total_revenue=_kpi(
                curr_revenue, prev_revenue, format_currency,
                interp_up="Revenue growing strongly",
                interp_down="Revenue declining — review sales pipeline",
            ),
            net_profit=profit_kpi,
            total_profit=profit_kpi,
            profit_margin=_kpi(
                curr_margin, prev_margin, lambda v: format_percentage(v),
                interp_up="Margin expansion — efficiency improving",
                interp_down="Margin compression — review pricing and costs",
            ),
            total_expenses=_kpi(
                curr_expenses, prev_expenses, format_currency,
                interp_up="Expenses rising — monitor for budget overrun",
                interp_down="Expense reduction achieved",
                higher_is_better=False,
            ),
            net_cash_flow=_kpi(
                curr_ncf, prev_ncf, format_currency,
                interp_up="Cash position strengthening",
                interp_down="Cash flow deteriorating — review collections",
            ),
            budget_variance_pct=_kpi(
                curr_bv_pct, prev_bv_pct, lambda v: format_percentage(v),
                interp_up="Overspending vs budget — tighten controls",
                interp_down="Spending below budget",
                higher_is_better=False,
            ),
            revenue_growth_pct=growth_kpi,
            revenue_growth_rate=growth_kpi,
            outstanding_receivables=receivables_kpi,
            accounts_receivable=receivables_kpi,
            expense_to_revenue_ratio=exp_rev_kpi,
            period_label=get_period_label(period),
            as_of_date=get_as_of_date().isoformat(),
        )
