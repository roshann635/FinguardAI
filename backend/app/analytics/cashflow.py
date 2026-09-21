"""Cash flow analytics service for FinGuard AI."""

import logging
from datetime import date
from typing import List, Optional

from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app.models import CashFlow, Category
from app.utils.formatters import safe_divide

logger = logging.getLogger(__name__)


class CashFlowService:
    """Cash flow trend, category breakdown and cumulative position."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _date_clauses_and_params(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
        col_alias: str = "flow_date",
    ) -> tuple[str, dict]:
        clauses = ""
        params: dict = {}
        if start_date:
            clauses += f" AND {col_alias} >= :start_date"
            params["start_date"] = start_date
        if end_date:
            clauses += f" AND {col_alias} <= :end_date"
            params["end_date"] = end_date
        return clauses, params

    # ------------------------------------------------------------------
    # Cash flow trend
    # ------------------------------------------------------------------

    def _is_sqlite(self) -> bool:
        try:
            return self.db.bind.dialect.name == "sqlite"
        except Exception:
            return False

    def get_cashflow_trend(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Monthly inflow, outflow and net cash flow (three series)."""
        try:
            date_clauses, params = self._date_clauses_and_params(start_date, end_date)
            if self._is_sqlite():
                period_sql = "strftime('%Y-%m-01', flow_date)"
            else:
                period_sql = "DATE_TRUNC('month', flow_date)::date"

            stmt = text(
                f"""
                SELECT
                    {period_sql}                                                     AS period,
                    SUM(CASE WHEN flow_type = 'inflow'  THEN amount ELSE 0 END)      AS inflow,
                    SUM(CASE WHEN flow_type = 'outflow' THEN amount ELSE 0 END)      AS outflow
                FROM cash_flows
                WHERE 1=1 {date_clauses}
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
                        period_iso = p_dt.isoformat()
                        period_label = p_dt.strftime("%b %Y")
                    except Exception:
                        period_iso = p
                        period_label = p
                else:
                    period_iso = p.isoformat()
                    period_label = p.strftime("%b %Y")

                inflow = float(row.inflow or 0)
                outflow = float(row.outflow or 0)
                results.append(
                    {
                        "date": period_iso,
                        "label": period_label,
                        "inflow": round(inflow, 2),
                        "outflow": round(outflow, 2),
                        "net_cash_flow": round(inflow - outflow, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_cashflow_trend failed")
            return []

    # ------------------------------------------------------------------
    # Cash flow by category
    # ------------------------------------------------------------------

    def get_cashflow_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Inflow, outflow and net cash flow aggregated by category."""
        try:
            filters: list = []
            if start_date:
                filters.append(CashFlow.flow_date >= start_date)
            if end_date:
                filters.append(CashFlow.flow_date <= end_date)

            rows = (
                self.db.query(
                    Category.name,
                    func.sum(
                        case(
                            (CashFlow.flow_type == "inflow", CashFlow.amount),
                            else_=0,
                        )
                    ).label("inflow"),
                    func.sum(
                        case(
                            (CashFlow.flow_type == "outflow", CashFlow.amount),
                            else_=0,
                        )
                    ).label("outflow"),
                )
                .join(CashFlow, CashFlow.category_id == Category.category_id)
                .filter(*filters)
                .group_by(Category.name)
                .order_by(func.sum(CashFlow.amount).desc())
                .all()
            )

            results = []
            for row in rows:
                inflow = float(row.inflow or 0)
                outflow = float(row.outflow or 0)
                results.append(
                    {
                        "category": row.name,
                        "inflow": round(inflow, 2),
                        "outflow": round(outflow, 2),
                        "net": round(inflow - outflow, 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_cashflow_by_category failed")
            return []

    # ------------------------------------------------------------------
    # Cumulative cash flow
    # ------------------------------------------------------------------

    def get_cumulative_cashflow(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[dict]:
        """Running cumulative net cash flow over the period (monthly)."""
        try:
            date_clauses, params = self._date_clauses_and_params(start_date, end_date)
            if self._is_sqlite():
                period_sql = "strftime('%Y-%m-01', flow_date)"
            else:
                period_sql = "DATE_TRUNC('month', flow_date)::date"

            stmt = text(
                f"""
                WITH monthly AS (
                    SELECT
                        {period_sql}                                                 AS period,
                        SUM(CASE WHEN flow_type = 'inflow'  THEN amount ELSE 0 END)  AS inflow,
                        SUM(CASE WHEN flow_type = 'outflow' THEN amount ELSE 0 END)  AS outflow
                    FROM cash_flows
                    WHERE 1=1 {date_clauses}
                    GROUP BY period
                )
                SELECT
                    period,
                    inflow,
                    outflow,
                    (inflow - outflow)                                                AS net,
                    SUM(inflow - outflow) OVER (ORDER BY period ROWS UNBOUNDED PRECEDING)
                                                                                      AS cumulative_net
                FROM monthly
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
                        period_iso = p_dt.isoformat()
                        period_label = p_dt.strftime("%b %Y")
                    except Exception:
                        period_iso = p
                        period_label = p
                else:
                    period_iso = p.isoformat()
                    period_label = p.strftime("%b %Y")

                results.append(
                    {
                        "date": period_iso,
                        "label": period_label,
                        "inflow": round(float(row.inflow or 0), 2),
                        "outflow": round(float(row.outflow or 0), 2),
                        "net": round(float(row.net or 0), 2),
                        "cumulative_net": round(float(row.cumulative_net or 0), 2),
                    }
                )
            return results
        except Exception:
            logger.exception("get_cumulative_cashflow failed")
            return []

