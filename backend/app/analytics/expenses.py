"""Expense analytics service for FinGuard AI."""

import logging
from datetime import date
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Category, Department, Expense, Transaction
from app.schemas import CategoryBreakdown, TimeSeriesPoint
from app.utils.formatters import safe_divide

logger = logging.getLogger(__name__)


class ExpenseAnalyticsService:
    """Expense trends, category/department breakdowns and efficiency ratios."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _expense_date_filters(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list:
        filters: list = [Expense.status == "approved"]
        if start_date:
            filters.append(Expense.expense_date >= start_date)
        if end_date:
            filters.append(Expense.expense_date <= end_date)
        return filters

    # ------------------------------------------------------------------
    # Expense trend
    # ------------------------------------------------------------------

    def get_expense_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TimeSeriesPoint]:
        """Monthly total approved expenses time series."""
        try:
            params: dict = {}
            date_clauses = ""
            if start_date:
                date_clauses += " AND expense_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_clauses += " AND expense_date <= :end_date"
                params["end_date"] = end_date

            stmt = text(
                f"""
                SELECT
                    DATE_TRUNC('month', expense_date)::date AS period,
                    SUM(amount)                             AS total
                FROM expenses
                WHERE status = 'approved'
                  {date_clauses}
                GROUP BY period
                ORDER BY period
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            return [
                TimeSeriesPoint(
                    date=row.period.isoformat(),
                    value=float(row.total or 0),
                    label=row.period.strftime("%b %Y"),
                )
                for row in rows
            ]
        except Exception:
            logger.exception("get_expense_trend failed")
            return []

    # ------------------------------------------------------------------
    # Expense by category
    # ------------------------------------------------------------------

    def get_expense_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CategoryBreakdown]:
        """Approved expenses grouped by category."""
        try:
            filters = self._expense_date_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Category.name,
                    func.sum(Expense.amount).label("total"),
                )
                .join(Expense, Expense.category_id == Category.category_id)
                .filter(*filters)
                .group_by(Category.name)
                .order_by(func.sum(Expense.amount).desc())
                .all()
            )
            grand_total = sum(float(r.total or 0) for r in rows)
            return [
                CategoryBreakdown(
                    category=row.name,
                    value=float(row.total or 0),
                    pct_of_total=round(safe_divide(float(row.total or 0), grand_total) * 100, 2),
                )
                for row in rows
            ]
        except Exception:
            logger.exception("get_expense_by_category failed")
            return []

    # ------------------------------------------------------------------
    # Expense by department
    # ------------------------------------------------------------------

    def get_expense_by_department(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Approved expenses grouped by department."""
        try:
            filters = self._expense_date_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Department.name,
                    func.sum(Expense.amount).label("total"),
                    func.count(Expense.expense_id).label("count"),
                )
                .join(Expense, Expense.department_id == Department.department_id)
                .filter(*filters)
                .group_by(Department.name)
                .order_by(func.sum(Expense.amount).desc())
                .all()
            )
            grand_total = sum(float(r.total or 0) for r in rows)
            return [
                {
                    "department": row.name,
                    "total": round(float(row.total or 0), 2),
                    "count": int(row.count or 0),
                    "pct_of_total": round(
                        safe_divide(float(row.total or 0), grand_total) * 100, 2
                    ),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_expense_by_department failed")
            return []

    # ------------------------------------------------------------------
    # Expense-to-revenue ratio
    # ------------------------------------------------------------------

    def get_expense_to_revenue_ratio(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Monthly ratio of approved expenses to net revenue (as a percentage)."""
        try:
            params: dict = {}
            exp_start = "AND e.expense_date >= :start_date" if start_date else ""
            exp_end   = "AND e.expense_date <= :end_date"   if end_date   else ""
            rev_start = "AND t.transaction_date >= :start_date" if start_date else ""
            rev_end   = "AND t.transaction_date <= :end_date"   if end_date   else ""
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            stmt = text(
                f"""
                WITH monthly_expenses AS (
                    SELECT
                        DATE_TRUNC('month', expense_date)::date AS period,
                        SUM(amount)                             AS total_expenses
                    FROM expenses
                    WHERE status = 'approved'
                      {exp_start} {exp_end}
                    GROUP BY period
                ),
                monthly_revenue AS (
                    SELECT
                        DATE_TRUNC('month', transaction_date)::date             AS period,
                        SUM(amount * (1 - discount_pct / 100.0))               AS total_revenue
                    FROM transactions
                    WHERE transaction_type = 'sale'
                      AND status = 'completed'
                      {rev_start} {rev_end}
                    GROUP BY period
                )
                SELECT
                    COALESCE(e.period, r.period)               AS period,
                    COALESCE(e.total_expenses, 0)              AS total_expenses,
                    COALESCE(r.total_revenue, 0)               AS total_revenue
                FROM monthly_expenses e
                FULL OUTER JOIN monthly_revenue r USING (period)
                ORDER BY period
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            return [
                {
                    "date": row.period.isoformat(),
                    "label": row.period.strftime("%b %Y"),
                    "total_expenses": round(float(row.total_expenses or 0), 2),
                    "total_revenue": round(float(row.total_revenue or 0), 2),
                    "expense_to_revenue_pct": round(
                        safe_divide(
                            float(row.total_expenses or 0),
                            float(row.total_revenue or 0),
                        ) * 100,
                        2,
                    ),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_expense_to_revenue_ratio failed")
            return []

    # ------------------------------------------------------------------
    # Top expense items
    # ------------------------------------------------------------------

    def get_top_expense_items(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
    ) -> List[dict]:
        """Top individual approved expense records by amount."""
        try:
            filters = self._expense_date_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Expense.expense_id,
                    Expense.expense_date,
                    Expense.amount,
                    Expense.description,
                    Category.name.label("category"),
                    Department.name.label("department"),
                )
                .join(Category, Category.category_id == Expense.category_id)
                .join(Department, Department.department_id == Expense.department_id)
                .filter(*filters)
                .order_by(Expense.amount.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "expense_id": str(row.expense_id),
                    "expense_date": row.expense_date.isoformat(),
                    "amount": round(float(row.amount or 0), 2),
                    "description": row.description or "",
                    "category": row.category,
                    "department": row.department,
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_top_expense_items failed")
            return []
