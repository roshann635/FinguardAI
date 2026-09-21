"""Profitability analytics service for FinGuard AI."""

import logging
from datetime import date
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Category, Expense, Region, Transaction
from app.schemas import TimeSeriesPoint
from app.utils.formatters import safe_divide

logger = logging.getLogger(__name__)


class ProfitabilityService:
    """Profit trends, margin analysis and breakdowns by category / region."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _revenue_expr():
        return Transaction.amount * (1 - Transaction.discount_pct / 100)

    @staticmethod
    def _cogs_expr():
        return Transaction.cost * Transaction.quantity

    def _monthly_revenue_and_cogs(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ):
        """Return rows of (period, revenue, cogs) per month."""
        params: dict = {}
        date_clauses = ""
        if start_date:
            date_clauses += " AND transaction_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            date_clauses += " AND transaction_date <= :end_date"
            params["end_date"] = end_date

        stmt = text(
            f"""
            SELECT
                DATE_TRUNC('month', transaction_date)::date          AS period,
                SUM(amount * (1 - discount_pct / 100.0))             AS revenue,
                SUM(cost * quantity)                                  AS cogs
            FROM transactions
            WHERE transaction_type = 'sale'
              AND status = 'completed'
              {date_clauses}
            GROUP BY period
            ORDER BY period
            """
        )
        return self.db.execute(stmt, params).fetchall()

    def _monthly_expenses(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> dict:
        """Return a mapping period_iso -> total_expenses."""
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
                SUM(amount)                             AS total_expenses
            FROM expenses
            WHERE status = 'approved'
              {date_clauses}
            GROUP BY period
            """
        )
        rows = self.db.execute(stmt, params).fetchall()
        return {row.period.isoformat(): float(row.total_expenses or 0) for row in rows}

    # ------------------------------------------------------------------
    # Profit trend
    # ------------------------------------------------------------------

    def get_profit_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Monthly gross profit and net profit time series."""
        try:
            revenue_rows = self._monthly_revenue_and_cogs(start_date, end_date)
            expenses_map = self._monthly_expenses(start_date, end_date)

            results = []
            for row in revenue_rows:
                period_iso = row.period.isoformat()
                revenue = float(row.revenue or 0)
                cogs = float(row.cogs or 0)
                gross_profit = revenue - cogs
                expenses = expenses_map.get(period_iso, 0.0)
                net_profit = revenue - expenses
                results.append(
                    {
                        "date": period_iso,
                        "label": row.period.strftime("%b %Y"),
                        "gross_profit": round(gross_profit, 2),
                        "net_profit": round(net_profit, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_profit_trend failed")
            return []

    # ------------------------------------------------------------------
    # Margin trend
    # ------------------------------------------------------------------

    def get_margin_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Monthly gross margin % and net margin %."""
        try:
            revenue_rows = self._monthly_revenue_and_cogs(start_date, end_date)
            expenses_map = self._monthly_expenses(start_date, end_date)

            results = []
            for row in revenue_rows:
                period_iso = row.period.isoformat()
                revenue = float(row.revenue or 0)
                cogs = float(row.cogs or 0)
                gross_profit = revenue - cogs
                expenses = expenses_map.get(period_iso, 0.0)
                net_profit = revenue - expenses

                results.append(
                    {
                        "date": period_iso,
                        "label": row.period.strftime("%b %Y"),
                        "gross_margin_pct": round(safe_divide(gross_profit, revenue) * 100, 2),
                        "net_margin_pct": round(safe_divide(net_profit, revenue) * 100, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_margin_trend failed")
            return []

    # ------------------------------------------------------------------
    # Profit by category
    # ------------------------------------------------------------------

    def get_profit_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Gross profit and margin per revenue category."""
        try:
            params: dict = {}
            date_clauses = ""
            if start_date:
                date_clauses += " AND t.transaction_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_clauses += " AND t.transaction_date <= :end_date"
                params["end_date"] = end_date

            stmt = text(
                f"""
                SELECT
                    c.name                                             AS category,
                    SUM(t.amount * (1 - t.discount_pct / 100.0))      AS revenue,
                    SUM(t.cost * t.quantity)                           AS cogs
                FROM transactions t
                JOIN categories c ON c.category_id = t.category_id
                WHERE t.transaction_type = 'sale'
                  AND t.status = 'completed'
                  {date_clauses}
                GROUP BY c.name
                ORDER BY revenue DESC
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            results = []
            for row in rows:
                revenue = float(row.revenue or 0)
                cogs = float(row.cogs or 0)
                gross_profit = revenue - cogs
                results.append(
                    {
                        "category": row.category,
                        "revenue": round(revenue, 2),
                        "cogs": round(cogs, 2),
                        "gross_profit": round(gross_profit, 2),
                        "gross_margin_pct": round(safe_divide(gross_profit, revenue) * 100, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_profit_by_category failed")
            return []

    # ------------------------------------------------------------------
    # Profit by region
    # ------------------------------------------------------------------

    def get_profit_by_region(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Gross profit and margin per region."""
        try:
            params: dict = {}
            date_clauses = ""
            if start_date:
                date_clauses += " AND t.transaction_date >= :start_date"
                params["start_date"] = start_date
            if end_date:
                date_clauses += " AND t.transaction_date <= :end_date"
                params["end_date"] = end_date

            stmt = text(
                f"""
                SELECT
                    r.name                                             AS region,
                    SUM(t.amount * (1 - t.discount_pct / 100.0))      AS revenue,
                    SUM(t.cost * t.quantity)                           AS cogs
                FROM transactions t
                JOIN regions r ON r.region_id = t.region_id
                WHERE t.transaction_type = 'sale'
                  AND t.status = 'completed'
                  {date_clauses}
                GROUP BY r.name
                ORDER BY revenue DESC
                """
            )
            rows = self.db.execute(stmt, params).fetchall()
            results = []
            for row in rows:
                revenue = float(row.revenue or 0)
                cogs = float(row.cogs or 0)
                gross_profit = revenue - cogs
                results.append(
                    {
                        "region": row.region,
                        "revenue": round(revenue, 2),
                        "cogs": round(cogs, 2),
                        "gross_profit": round(gross_profit, 2),
                        "gross_margin_pct": round(safe_divide(gross_profit, revenue) * 100, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_profit_by_region failed")
            return []
