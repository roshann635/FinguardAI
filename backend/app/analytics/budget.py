"""Budget analytics service for FinGuard AI."""

import logging
from datetime import date, datetime
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

    def _is_sqlite(self) -> bool:
        try:
            return self.db.bind.dialect.name == "sqlite"
        except Exception:
            return False

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

            # Query budgets
            b_query = (
                self.db.query(
                    Budget.category_id,
                    Budget.department_id,
                    func.sum(Budget.budget_amount).label("budget_total"),
                )
                .filter(Budget.period_year == year)
            )
            if months:
                b_query = b_query.filter(Budget.period_month.in_(months))
            budget_rows = b_query.group_by(Budget.category_id, Budget.department_id).all()

            # Query expenses
            min_m = min(months) if months else 1
            max_m = max(months) if months else 12
            last_d = calendar.monthrange(year, max_m)[1]
            start_date = date(year, min_m, 1)
            end_date = date(year, max_m, last_d)

            e_query = (
                self.db.query(
                    Expense.category_id,
                    Expense.department_id,
                    func.sum(Expense.amount).label("actual_total"),
                )
                .filter(
                    Expense.status == "approved",
                    Expense.expense_date >= start_date,
                    Expense.expense_date <= end_date,
                )
            )
            expense_rows = e_query.group_by(Expense.category_id, Expense.department_id).all()

            # Fetch category and department names map
            categories = {c.category_id: c.name for c in self.db.query(Category).all()}
            departments = {d.department_id: d.name for d in self.db.query(Department).all()}

            # Merge by (category_id, department_id)
            merged: dict = {}
            for row in budget_rows:
                key = (row.category_id, row.department_id)
                merged.setdefault(key, {"budget": 0.0, "actual": 0.0})
                merged[key]["budget"] = float(row.budget_total or 0)

            for row in expense_rows:
                key = (row.category_id, row.department_id)
                merged.setdefault(key, {"budget": 0.0, "actual": 0.0})
                merged[key]["actual"] = float(row.actual_total or 0)

            results: List[BudgetVarianceItem] = []
            for (cat_id, dept_id), data in merged.items():
                cat_name = categories.get(cat_id, "Unknown")
                dept_name = departments.get(dept_id, "Unknown")
                budget = data["budget"]
                actual = data["actual"]
                variance = actual - budget
                variance_pct = round(safe_divide(variance, budget) * 100, 2)
                results.append(
                    BudgetVarianceItem(
                        category=cat_name,
                        department=dept_name,
                        budget=round(budget, 2),
                        actual=round(actual, 2),
                        variance=round(variance, 2),
                        variance_pct=variance_pct,
                        status=_budget_status(variance_pct),
                    )
                )
            results.sort(key=lambda x: (x.category, x.department))
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
            import calendar as cal

            b_rows = (
                self.db.query(
                    Budget.period_month,
                    func.sum(Budget.budget_amount).label("budget_total"),
                )
                .filter(Budget.period_year == year)
                .group_by(Budget.period_month)
                .all()
            )
            budget_map = {int(r.period_month): float(r.budget_total or 0) for r in b_rows}

            start_d = date(year, 1, 1)
            end_d = date(year, 12, 31)
            expenses = (
                self.db.query(Expense.expense_date, Expense.amount)
                .filter(
                    Expense.status == "approved",
                    Expense.expense_date >= start_d,
                    Expense.expense_date <= end_d,
                )
                .all()
            )
            actual_map: dict = {}
            for exp in expenses:
                m = exp.expense_date.month if hasattr(exp.expense_date, "month") else int(str(exp.expense_date)[5:7])
                actual_map[m] = actual_map.get(m, 0.0) + float(exp.amount or 0)

            results = []
            for m in range(1, 13):
                b = budget_map.get(m, 0.0)
                a = actual_map.get(m, 0.0)
                var = a - b
                results.append(
                    {
                        "month": m,
                        "month_label": cal.month_abbr[m],
                        "budget": round(b, 2),
                        "actual": round(a, 2),
                        "variance": round(var, 2),
                        "variance_pct": round(safe_divide(var, b) * 100, 2),
                    }
                )
            return results
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
