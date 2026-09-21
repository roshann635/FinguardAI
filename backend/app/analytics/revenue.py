"""Revenue analytics service for FinGuard AI."""

import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Category, Customer, Region, Transaction
from app.schemas import CategoryBreakdown, RegionBreakdown, TimeSeriesPoint
from app.utils.formatters import safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)


class RevenueAnalyticsService:
    """Granular revenue analysis: trends, breakdowns, and growth."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _net_amount_expr():
        """SQLAlchemy expression for net revenue (amount after discount)."""
        return Transaction.amount * (1 - Transaction.discount_pct / 100)

    def _base_revenue_filters(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list:
        filters = [
            Transaction.transaction_type == "sale",
            Transaction.status == "completed",
        ]
        if start_date:
            filters.append(Transaction.transaction_date >= start_date)
        if end_date:
            filters.append(Transaction.transaction_date <= end_date)
        return filters

    # ------------------------------------------------------------------
    # Revenue trend
    # ------------------------------------------------------------------

    def get_revenue_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        granularity: str = "monthly",
    ) -> List[TimeSeriesPoint]:
        """Aggregated revenue time series at monthly, weekly, or quarterly granularity."""
        try:
            if granularity == "weekly":
                trunc = "week"
            elif granularity == "quarterly":
                trunc = "quarter"
            else:
                trunc = "month"

            stmt = text(
                f"""
                SELECT
                    DATE_TRUNC('{trunc}', transaction_date)::date AS period,
                    SUM(amount * (1 - discount_pct / 100.0))     AS revenue
                FROM transactions
                WHERE transaction_type = 'sale'
                  AND status = 'completed'
                  {('AND transaction_date >= :start_date' if start_date else '')}
                  {('AND transaction_date <= :end_date'   if end_date   else '')}
                GROUP BY period
                ORDER BY period
                """
            )
            params: dict = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            rows = self.db.execute(stmt, params).fetchall()
            return [
                TimeSeriesPoint(
                    date=row.period.isoformat(),
                    value=float(row.revenue or 0),
                    label=row.period.strftime("%b %Y"),
                )
                for row in rows
            ]
        except Exception:
            logger.exception("get_revenue_trend failed")
            return []

    # ------------------------------------------------------------------
    # Revenue by category
    # ------------------------------------------------------------------

    def get_revenue_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CategoryBreakdown]:
        """Revenue grouped by category with share of total."""
        try:
            filters = self._base_revenue_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Category.name,
                    func.sum(self._net_amount_expr()).label("revenue"),
                )
                .join(Transaction, Transaction.category_id == Category.category_id)
                .filter(*filters)
                .group_by(Category.name)
                .order_by(func.sum(self._net_amount_expr()).desc())
                .all()
            )

            total = sum(float(r.revenue or 0) for r in rows)
            results: List[CategoryBreakdown] = []
            for row in rows:
                val = float(row.revenue or 0)
                results.append(
                    CategoryBreakdown(
                        category=row.name,
                        value=val,
                        pct_of_total=round(safe_divide(val, total) * 100, 2),
                        change_pct=None,  # growth requires prior period — use get_revenue_growth_trend
                    )
                )
            return results
        except Exception:
            logger.exception("get_revenue_by_category failed")
            return []

    # ------------------------------------------------------------------
    # Revenue by region
    # ------------------------------------------------------------------

    def get_revenue_by_region(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RegionBreakdown]:
        """Revenue grouped by region with share of total."""
        try:
            filters = self._base_revenue_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Region.name,
                    func.sum(self._net_amount_expr()).label("revenue"),
                )
                .join(Transaction, Transaction.region_id == Region.region_id)
                .filter(*filters)
                .group_by(Region.name)
                .order_by(func.sum(self._net_amount_expr()).desc())
                .all()
            )

            total = sum(float(r.revenue or 0) for r in rows)
            results: List[RegionBreakdown] = []
            for row in rows:
                val = float(row.revenue or 0)
                results.append(
                    RegionBreakdown(
                        region=row.name,
                        value=val,
                        pct_of_total=round(safe_divide(val, total) * 100, 2),
                        change_pct=None,
                    )
                )
            return results
        except Exception:
            logger.exception("get_revenue_by_region failed")
            return []

    # ------------------------------------------------------------------
    # Top revenue contributors
    # ------------------------------------------------------------------

    def get_top_revenue_contributors(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
    ) -> List[dict]:
        """Top customers ranked by revenue contribution."""
        try:
            filters = self._base_revenue_filters(start_date, end_date)
            rows = (
                self.db.query(
                    Customer.customer_id,
                    Customer.name,
                    Customer.segment,
                    func.sum(self._net_amount_expr()).label("revenue"),
                    func.count(Transaction.transaction_id).label("tx_count"),
                )
                .join(Transaction, Transaction.customer_id == Customer.customer_id)
                .filter(*filters)
                .group_by(Customer.customer_id, Customer.name, Customer.segment)
                .order_by(func.sum(self._net_amount_expr()).desc())
                .limit(limit)
                .all()
            )

            total_q = (
                self.db.query(func.sum(self._net_amount_expr()))
                .filter(*filters)
                .scalar()
            )
            total = float(total_q or 0)

            return [
                {
                    "customer_id": row.customer_id,
                    "customer_name": row.name,
                    "segment": row.segment,
                    "revenue": float(row.revenue or 0),
                    "transaction_count": int(row.tx_count or 0),
                    "pct_of_total": round(safe_divide(float(row.revenue or 0), total) * 100, 2),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_top_revenue_contributors failed")
            return []

    # ------------------------------------------------------------------
    # Revenue growth trend
    # ------------------------------------------------------------------

    def get_revenue_growth_trend(self, months: int = 12) -> List[dict]:
        """Month-over-month revenue growth percentage for the last N months."""
        try:
            # NOTE: bind param inside INTERVAL needs casting — use format instead
            stmt = text(
                f"""
                WITH monthly AS (
                    SELECT
                        DATE_TRUNC('month', transaction_date)::date AS period,
                        SUM(amount * (1 - discount_pct / 100.0))   AS revenue
                    FROM transactions
                    WHERE transaction_type = 'sale'
                      AND status = 'completed'
                      AND transaction_date >= DATE_TRUNC('month', :as_of_date::date)
                                             - INTERVAL '{int(months)} months'
                    GROUP BY period
                )
                SELECT
                    period,
                    revenue,
                    LAG(revenue) OVER (ORDER BY period) AS prev_revenue
                FROM monthly
                ORDER BY period
                """
            )

            rows = self.db.execute(stmt, {"as_of_date": get_as_of_date()}).fetchall()
            results = []
            for row in rows:
                revenue = float(row.revenue or 0)
                prev = float(row.prev_revenue or 0)
                growth = safe_divide(revenue - prev, prev) * 100 if prev else None
                results.append(
                    {
                        "period": row.period.isoformat(),
                        "label": row.period.strftime("%b %Y"),
                        "revenue": revenue,
                        "growth_pct": round(growth, 2) if growth is not None else None,
                    }
                )
            return results
        except Exception:
            logger.exception("get_revenue_growth_trend failed")
            return []
