"""Receivables analytics service for FinGuard AI."""

import logging
from datetime import date
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import Customer, Invoice
from app.schemas import ReceivablesAging
from app.utils.formatters import safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)


class ReceivablesService:
    """Accounts-receivable ageing, trends and collection efficiency."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Aging summary
    # ------------------------------------------------------------------

    def get_aging_summary(self) -> ReceivablesAging:
        """
        Classify outstanding receivables into ageing buckets based on days past due_date.

        Buckets (days overdue):
            0–30   : bucket_0_30
            31–60  : bucket_31_60
            61–90  : bucket_61_90
            91+    : bucket_90_plus
        """
        try:
            stmt = text(
                """
                SELECT
                    SUM(CASE
                        WHEN :as_of_date - due_date <= 30
                        THEN invoice_amount - paid_amount ELSE 0
                    END) AS bucket_0_30,
                    SUM(CASE
                        WHEN :as_of_date - due_date BETWEEN 31 AND 60
                        THEN invoice_amount - paid_amount ELSE 0
                    END) AS bucket_31_60,
                    SUM(CASE
                        WHEN :as_of_date - due_date BETWEEN 61 AND 90
                        THEN invoice_amount - paid_amount ELSE 0
                    END) AS bucket_61_90,
                    SUM(CASE
                        WHEN :as_of_date - due_date > 90
                        THEN invoice_amount - paid_amount ELSE 0
                    END) AS bucket_90_plus,
                    SUM(invoice_amount - paid_amount) AS total_outstanding
                FROM invoices
                WHERE payment_status IN ('unpaid', 'partial', 'overdue')
                """
            )
            row = self.db.execute(stmt, {"as_of_date": get_as_of_date()}).fetchone()

            b0   = float(row.bucket_0_30  or 0)
            b31  = float(row.bucket_31_60 or 0)
            b61  = float(row.bucket_61_90 or 0)
            b90p = float(row.bucket_90_plus or 0)
            total = float(row.total_outstanding or 0)
            overdue = b31 + b61 + b90p  # anything past 30 days is considered overdue

            return ReceivablesAging(
                bucket_0_30=round(b0, 2),
                bucket_31_60=round(b31, 2),
                bucket_61_90=round(b61, 2),
                bucket_90_plus=round(b90p, 2),
                total_outstanding=round(total, 2),
                overdue_amount=round(overdue, 2),
                overdue_pct=round(safe_divide(overdue, total) * 100, 2),
            )
        except Exception:
            logger.exception("get_aging_summary failed")
            return ReceivablesAging(
                bucket_0_30=0.0,
                bucket_31_60=0.0,
                bucket_61_90=0.0,
                bucket_90_plus=0.0,
                total_outstanding=0.0,
                overdue_amount=0.0,
                overdue_pct=0.0,
            )

    # ------------------------------------------------------------------
    # Aging trend
    # ------------------------------------------------------------------

    def get_aging_trend(self, months: int = 6) -> List[dict]:
        """
        Monthly snapshot of ageing distribution for the last N months.
        Uses invoice_date as the time axis (approximates how the book looked that month).
        """
        try:
            stmt = text(
                f"""
                WITH monthly AS (
                    SELECT
                        DATE_TRUNC('month', invoice_date)::date              AS period,
                        SUM(CASE
                                WHEN (:as_of_date - due_date) <= 30
                                THEN invoice_amount - paid_amount ELSE 0
                            END)                                             AS bucket_0_30,
                        SUM(CASE
                                WHEN (:as_of_date - due_date) BETWEEN 31 AND 60
                                THEN invoice_amount - paid_amount ELSE 0
                            END)                                             AS bucket_31_60,
                        SUM(CASE
                                WHEN (:as_of_date - due_date) BETWEEN 61 AND 90
                                THEN invoice_amount - paid_amount ELSE 0
                            END)                                             AS bucket_61_90,
                        SUM(CASE
                                WHEN (:as_of_date - due_date) > 90
                                THEN invoice_amount - paid_amount ELSE 0
                            END)                                             AS bucket_90_plus
                    FROM invoices
                    WHERE payment_status IN ('unpaid', 'partial', 'overdue')
                      AND invoice_date >= DATE_TRUNC('month', :as_of_date::date)
                                         - INTERVAL '{int(months)} months'
                    GROUP BY period
                )
                SELECT *,
                       (bucket_0_30 + bucket_31_60 + bucket_61_90 + bucket_90_plus) AS total
                FROM monthly
                ORDER BY period
                """
            )
            rows = self.db.execute(stmt, {"as_of_date": get_as_of_date()}).fetchall()
            return [
                {
                    "date": row.period.isoformat(),
                    "label": row.period.strftime("%b %Y"),
                    "bucket_0_30": round(float(row.bucket_0_30 or 0), 2),
                    "bucket_31_60": round(float(row.bucket_31_60 or 0), 2),
                    "bucket_61_90": round(float(row.bucket_61_90 or 0), 2),
                    "bucket_90_plus": round(float(row.bucket_90_plus or 0), 2),
                    "total": round(float(row.total or 0), 2),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_aging_trend failed")
            return []

    # ------------------------------------------------------------------
    # Top overdue accounts
    # ------------------------------------------------------------------

    def get_top_overdue_accounts(self, limit: int = 10) -> List[dict]:
        """Customers with the highest overdue balances (past due_date)."""
        try:
            stmt = text(
                f"""
                SELECT
                    c.customer_id,
                    c.name                                     AS customer_name,
                    c.segment,
                    COUNT(i.invoice_id)                        AS invoice_count,
                    SUM(i.invoice_amount - i.paid_amount)      AS outstanding_balance,
                    MIN(i.due_date)                            AS oldest_due_date,
                    MAX(:as_of_date - i.due_date)              AS max_days_overdue
                FROM invoices i
                JOIN customers c ON c.customer_id = i.customer_id
                WHERE i.payment_status IN ('unpaid', 'partial', 'overdue')
                  AND i.due_date < :as_of_date
                GROUP BY c.customer_id, c.name, c.segment
                ORDER BY outstanding_balance DESC
                LIMIT {int(limit)}
                """
            )
            rows = self.db.execute(stmt, {"as_of_date": get_as_of_date()}).fetchall()
            return [
                {
                    "customer_id": row.customer_id,
                    "customer_name": row.customer_name,
                    "segment": row.segment,
                    "invoice_count": int(row.invoice_count or 0),
                    "outstanding_balance": round(float(row.outstanding_balance or 0), 2),
                    "oldest_due_date": row.oldest_due_date.isoformat() if row.oldest_due_date else None,
                    "max_days_overdue": int(row.max_days_overdue or 0),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_top_overdue_accounts failed")
            return []

    # ------------------------------------------------------------------
    # Collection efficiency
    # ------------------------------------------------------------------

    def get_collection_efficiency(self, months: int = 6) -> List[dict]:
        """Monthly invoiced amount vs collected (paid) amount."""
        try:
            stmt = text(
                f"""
                SELECT
                    DATE_TRUNC('month', invoice_date)::date  AS period,
                    SUM(invoice_amount)                      AS invoiced,
                    SUM(paid_amount)                         AS collected
                FROM invoices
                WHERE invoice_date >= DATE_TRUNC('month', :as_of_date::date)
                                     - INTERVAL '{int(months)} months'
                GROUP BY period
                ORDER BY period
                """
            )
            rows = self.db.execute(stmt, {"as_of_date": get_as_of_date()}).fetchall()
            return [
                {
                    "date": row.period.isoformat(),
                    "label": row.period.strftime("%b %Y"),
                    "invoiced": round(float(row.invoiced or 0), 2),
                    "collected": round(float(row.collected or 0), 2),
                    "collection_rate_pct": round(
                        safe_divide(float(row.collected or 0), float(row.invoiced or 0)) * 100,
                        2,
                    ),
                }
                for row in rows
            ]
        except Exception:
            logger.exception("get_collection_efficiency failed")
            return []
