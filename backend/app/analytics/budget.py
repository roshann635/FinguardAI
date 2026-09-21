"""Budget analytics service for FinGuard AI."""

import logging
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Budget, Category, Department, Expense
from app.schemas import BudgetVarianceItem
from app.utils.formatters import safe_divide

logger = logging.getLogger(__name__)


def _budget_status(variance_pct: float) -> str:
    """Classify a budget item based on variance percentage."""
    if variance_pct > 10.0:
        return "over_budget"
    if variance_pct >= 0.0:
        return "near_budget"
    return "under_budget"


class BudgetAnalyticsService:
    """Budget vs actual analysis with overspending and under-utilisation detection."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Budget vs actual
    # ------------------------------------------------------------------

    def get_budget_vs_actual(
        self,
        year: int,
        months: Optional[List[int]] = None,
    ) -> List[BudgetVarianceItem]:
        """Per category + department: budgeted vs approved actual expenses."""
        try:
            import calendar

            params: dict = {"year": year}
            month_filter_budget = ""
            month_filter_expense = ""

            if months:
                month_filter_budget = "AND b.period_month = ANY(:months)"
                month_filter_expense = "AND EXTRACT(MONTH FROM e.expense_date) = ANY(:months)"
                params["months"] = months
                # Build expense date range covering all requested months
                min_month = min(months)
                max_month = max(months)
                last_day = calendar.monthrange(year, max_month)[1]
                params["exp_start"] = f"{year}-{min_month:02d}-01"
                params["exp_end"] = f"{year}-{max_month:02d}-{last_day:02d}"
                expense_date_range = (
                    "AND e.expense_date BETWEEN :exp_start::date AND :exp_end::date"
                )
            else:
                params["exp_start"] = f"{year}-01-01"
                params["exp_end"] = f"{year}-12-31"
                expense_date_range = (
                    "AND e.expense_date BETWEEN :exp_start::date AND :exp_end::date"
                )

            stmt = text(
                f"""
                WITH budget_agg AS (
                    SELECT
                        b.category_id,
                        b.department_id,
                        SUM(b.budget_amount) AS budget_total
                    FROM budgets b
                    WHERE b.period_year = :year
                      {month_filter_budget}
                    GROUP BY b.category_id, b.department_id
                ),
                expense_agg AS (
                    SELECT
                        e.category_id,
                        e.department_id,
                        SUM(e.amount) AS actual_total
                    FROM expenses e
                    WHERE e.status = 'approved'
                      {expense_date_range}
                      {month_filter_expense}
                    GROUP BY e.category_id, e.department_id
                )
                SELECT
                    c.name                                           AS category,
                    d.name                                           AS department,
                    COALESCE(ba.budget_total, 0)                     AS budget,
                    COALESCE(ea.actual_total, 0)                     AS actual
                FROM budget_agg ba
                FULL OUTER JOIN expense_agg ea
                    ON ba.category_id  = ea.category_id
                   AND ba.department_id = ea.department_id
                JOIN categories  c ON c.category_id  = COALESCE(ba.category_id,  ea.category_id)
                JOIN departments d ON d.department_id = COALESCE(ba.department_id, ea.department_id)
                ORDER BY category, department
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            results: List[BudgetVarianceItem] = []
            for row in rows:
                budget = float(row.budget or 0)
                actual = float(row.actual or 0)
                variance = actual - budget
                variance_pct = round(safe_divide(variance, budget) * 100, 2)
                results.append(
                    BudgetVarianceItem(
                        category=row.category,
                        department=row.department,
                        budget=round(budget, 2),
                        actual=round(actual, 2),
                        variance=round(variance, 2),
                        variance_pct=variance_pct,
                        status=_budget_status(variance_pct),
                    )
                )
            return results
        except Exception:
            logger.exception("get_budget_vs_actual failed")
            return []

    # ------------------------------------------------------------------
    # Budget trend
    # ------------------------------------------------------------------

    def get_budget_trend(self, year: int) -> List[dict]:
        """Monthly budget vs actual spending across the year."""
        try:
            stmt = text(
                """
                WITH monthly_budget AS (
                    SELECT
                        period_month,
                        SUM(budget_amount) AS budget_total
                    FROM budgets
                    WHERE period_year = :year
                    GROUP BY period_month
                ),
                monthly_actual AS (
                    SELECT
                        EXTRACT(MONTH FROM expense_date)::int AS period_month,
                        SUM(amount)                           AS actual_total
                    FROM expenses
                    WHERE status = 'approved'
                      AND EXTRACT(YEAR FROM expense_date) = :year
                    GROUP BY period_month
                )
                SELECT
                    COALESCE(b.period_month, a.period_month)  AS month,
                    COALESCE(b.budget_total, 0)               AS budget,
                    COALESCE(a.actual_total, 0)               AS actual
                FROM monthly_budget b
                FULL OUTER JOIN monthly_actual a USING (period_month)
                ORDER BY month
                """
            )
            rows = self.db.execute(stmt, {"year": year}).fetchall()
            import calendar as cal

            return [
                {
                    "month": int(row.month),
                    "month_label": cal.month_abbr[int(row.month)],
                    "budget": round(float(row.budget or 0), 2),
                    "actual": round(float(row.actual or 0), 2),
                    "variance": round(float(row.actual or 0) - float(row.budget or 0), 2),
                    "variance_pct": round(
                        safe_divide(
                            float(row.actual or 0) - float(row.budget or 0),
                            float(row.budget or 0),
                        ) * 100,
                        2,
                    ),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_budget_trend failed")
            return []

    # ------------------------------------------------------------------
    # Overspending areas
    # ------------------------------------------------------------------

    def get_overspending_areas(self, year: int) -> List[BudgetVarianceItem]:
        """Return only over_budget items sorted by variance_pct descending."""
        try:
            all_items = self.get_budget_vs_actual(year)
            return sorted(
                [item for item in all_items if item.status == "over_budget"],
                key=lambda x: x.variance_pct,
                reverse=True,
            )
        except Exception:
            logger.exception("get_overspending_areas failed")
            return []

    # ------------------------------------------------------------------
    # Under-utilised budget
    # ------------------------------------------------------------------

    def get_underutilized_budget(self, year: int) -> List[BudgetVarianceItem]:
        """Items where actual < 80% of budget (variance_pct < -20%), sorted by variance asc."""
        try:
            all_items = self.get_budget_vs_actual(year)
            return sorted(
                [item for item in all_items if item.variance_pct < -20.0],
                key=lambda x: x.variance,
            )
        except Exception:
            logger.exception("get_underutilized_budget failed")
            return []
