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

    def _is_sqlite(self) -> bool:
        try:
            return self.db.bind.dialect.name == "sqlite"
        except Exception:
            return False

    def get_expense_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TimeSeriesPoint]:
        """Monthly approved expenses time series."""
        try:
            params: dict = {}
            date_clauses = ""
            if start_date:
                date_clauses += " AND expense_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_clauses += " AND expense_date <= :end_date"
                params["end_date"] = end_date

            if self._is_sqlite():
                period_sql = "strftime('%Y-%m-01', expense_date)"
            else:
                period_sql = "DATE_TRUNC('month', expense_date)::date"

            stmt = text(
                f"""
                SELECT
                    {period_sql} AS period,
                    SUM(amount)  AS total
                FROM expenses
                WHERE status = 'approved'
                  {date_clauses}
                GROUP BY period
                ORDER BY period
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            results = []
            for row in rows:
                p = row.period
                if isinstance(p, str):
                    try:
                        p_dt = date.fromisoformat(p[:10])
                        p_iso = p_dt.isoformat()
                        p_label = p_dt.strftime("%b %Y")
                    except Exception:
                        p_iso = p
                        p_label = p
                else:
                    p_iso = p.isoformat()
                    p_label = p.strftime("%b %Y")

                results.append(
                    TimeSeriesPoint(
                        date=p_iso,
                        value=float(row.total or 0),
                        label=p_label,
                    )
                )
            return results
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

            total = sum(float(r.total or 0) for r in rows)
            results: List[CategoryBreakdown] = []
            for row in rows:
                val = float(row.total or 0)
                results.append(
                    CategoryBreakdown(
                        category=row.name,
                        value=val,
                        pct_of_total=round(safe_divide(val, total) * 100, 2),
                        change_pct=None,
                    )
                )
            return results
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

            return []

    # ------------------------------------------------------------------
    # Expense-to-revenue ratio trend
    # ------------------------------------------------------------------

    def get_expense_to_revenue_ratio(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Monthly expense-to-revenue ratio."""
        try:
            params: dict = {}
            exp_start = "AND expense_date >= :start_date" if start_date else ""
            exp_end   = "AND expense_date <= :end_date"   if end_date   else ""
            rev_start = "AND transaction_date >= :start_date" if start_date else ""
            rev_end   = "AND transaction_date <= :end_date"   if end_date   else ""
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            if self._is_sqlite():
                exp_period = "strftime('%Y-%m-01', expense_date)"
                rev_period = "strftime('%Y-%m-01', transaction_date)"
            else:
                exp_period = "DATE_TRUNC('month', expense_date)::date"
                rev_period = "DATE_TRUNC('month', transaction_date)::date"

            exp_stmt = text(
                f"""
                SELECT
                    {exp_period} AS period,
                    SUM(amount)  AS total_expenses
                FROM expenses
                WHERE status = 'approved'
                  {exp_start} {exp_end}
                GROUP BY period
                """
            )
            rev_stmt = text(
                f"""
                SELECT
                    {rev_period}                             AS period,
                    SUM(amount * (1 - discount_pct / 100.0)) AS total_revenue
                FROM transactions
                WHERE transaction_type = 'sale'
                  AND status = 'completed'
                  {rev_start} {rev_end}
                GROUP BY period
                """
            )
            exp_rows = self.db.execute(exp_stmt, params).fetchall()
            rev_rows = self.db.execute(rev_stmt, params).fetchall()

            data_map: dict = {}
            for r in exp_rows:
                p_str = str(r.period)[:10]
                data_map.setdefault(p_str, {"period": r.period, "expenses": 0.0, "revenue": 0.0})
                data_map[p_str]["expenses"] = float(r.total_expenses or 0)

            for r in rev_rows:
                p_str = str(r.period)[:10]
                data_map.setdefault(p_str, {"period": r.period, "expenses": 0.0, "revenue": 0.0})
                data_map[p_str]["revenue"] = float(r.total_revenue or 0)

            results = []
            for p_str in sorted(data_map.keys()):
                entry = data_map[p_str]
                p = entry["period"]
                if isinstance(p, str):
                    try:
                        p_dt = date.fromisoformat(p[:10])
                        p_iso = p_dt.isoformat()
                        p_label = p_dt.strftime("%b %Y")
                    except Exception:
                        p_iso = p
                        p_label = p
                else:
                    p_iso = p.isoformat()
                    p_label = p.strftime("%b %Y")

                tot_exp = entry["expenses"]
                tot_rev = entry["revenue"]
                results.append(
                    {
                        "date": p_iso,
                        "label": p_label,
                        "total_expenses": round(tot_exp, 2),
                        "total_revenue": round(tot_rev, 2),
                        "expense_to_revenue_pct": round(safe_divide(tot_exp, tot_rev) * 100, 2),
                    }
                )
            return results
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
