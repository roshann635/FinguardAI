"""Data Quality Engine for FinGuard AI."""

import logging
from datetime import date, datetime
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import DataQualityReport
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Runs four orthogonal quality checks across all main financial tables
    and synthesises a weighted overall score.

    Weights:
        completeness  = 0.30
        consistency   = 0.25
        validity      = 0.25
        duplicates    = 0.20
    """

    WEIGHTS = {
        "completeness": 0.30,
        "consistency": 0.25,
        "validity": 0.25,
        "duplicates": 0.20,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Completeness
    # ------------------------------------------------------------------

    def check_completeness(self) -> Dict[str, Any]:
        """
        Check for NULL values in critical fields across main tables.

        Returns:
            score          – 0–100, percentage of non-null critical fields
            missing_count  – total NULL field occurrences
            total_count    – total field slots checked
            details        – per-table breakdown
        """
        checks = [
            # (table, column, description)
            ("transactions",  "transaction_date",  "Transaction date"),
            ("transactions",  "amount",            "Transaction amount"),
            ("transactions",  "transaction_type",  "Transaction type"),
            ("transactions",  "status",            "Transaction status"),
            ("transactions",  "payment_method",    "Payment method"),
            ("expenses",      "expense_date",      "Expense date"),
            ("expenses",      "amount",            "Expense amount"),
            ("expenses",      "status",            "Expense status"),
            ("expenses",      "category_id",       "Expense category"),
            ("expenses",      "department_id",     "Expense department"),
            ("invoices",      "invoice_date",      "Invoice date"),
            ("invoices",      "due_date",          "Invoice due date"),
            ("invoices",      "invoice_amount",    "Invoice amount"),
            ("invoices",      "customer_id",       "Invoice customer"),
            ("invoices",      "payment_status",    "Invoice payment status"),
            ("cash_flows",    "flow_date",         "Cash flow date"),
            ("cash_flows",    "amount",            "Cash flow amount"),
            ("cash_flows",    "flow_type",         "Cash flow type"),
            ("budgets",       "budget_amount",     "Budget amount"),
            ("budgets",       "period_year",       "Budget year"),
            ("budgets",       "period_month",      "Budget month"),
        ]

        details: List[Dict[str, Any]] = []
        total_count = 0
        missing_count = 0

        for table, column, label in checks:
            try:
                result = self.db.execute(
                    text(
                        f"SELECT COUNT(*) AS total, "
                        f"COUNT(*) FILTER (WHERE {column} IS NULL) AS missing "
                        f"FROM {table}"
                    )
                ).fetchone()
                total = int(result.total or 0)
                missing = int(result.missing or 0)
                total_count += total
                missing_count += missing
                details.append(
                    {
                        "table": table,
                        "column": column,
                        "description": label,
                        "total_rows": total,
                        "missing_rows": missing,
                        "missing_pct": round(
                            (missing / total * 100) if total else 0, 2
                        ),
                    }
                )
            except Exception:
                logger.exception("completeness check failed for %s.%s", table, column)

        score = round(
            ((total_count - missing_count) / total_count * 100) if total_count else 100.0,
            2,
        )
        return {
            "score": score,
            "missing_count": missing_count,
            "total_count": total_count,
            "details": details,
        }

    # ------------------------------------------------------------------
    # Consistency
    # ------------------------------------------------------------------

    def check_consistency(self) -> Dict[str, Any]:
        """
        Detect logically inconsistent records:
          1. Sales with amount <= 0
          2. Invoices where paid_amount > invoice_amount
          3. Expenses with future expense_date
        """
        issues: List[Dict[str, Any]] = []
        total_checked = 0

        checks = [
            (
                "transactions",
                "SELECT COUNT(*) AS cnt FROM transactions "
                "WHERE transaction_type = 'sale' AND amount <= 0",
                "Sales transactions with non-positive amount",
            ),
            (
                "invoices",
                "SELECT COUNT(*) AS cnt FROM invoices "
                "WHERE paid_amount > invoice_amount",
                "Invoices where paid amount exceeds invoice amount",
            ),
            (
                "expenses",
                "SELECT COUNT(*) AS cnt FROM expenses "
                "WHERE expense_date > :as_of_date",
                "Expenses with future-dated expense_date",
            ),
        ]

        inconsistent_count = 0
        for table, sql, desc in checks:
            try:
                row = self.db.execute(text(sql), {"as_of_date": get_as_of_date()}).fetchone()
                cnt = int(row.cnt or 0)
                inconsistent_count += cnt
                if cnt > 0:
                    issues.append(
                        {
                            "table": table,
                            "issue": desc,
                            "affected_rows": cnt,
                            "severity": "high",
                        }
                    )
            except Exception:
                logger.exception("consistency check failed: %s", desc)

        # total rows across three checked tables
        for table in ("transactions", "invoices", "expenses"):
            try:
                row = self.db.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}")).fetchone()
                total_checked += int(row.cnt or 0)
            except Exception:
                logger.exception("row count failed for %s", table)

        score = round(
            ((total_checked - inconsistent_count) / total_checked * 100)
            if total_checked
            else 100.0,
            2,
        )
        return {
            "score": score,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Validity
    # ------------------------------------------------------------------

    def check_validity(self) -> Dict[str, Any]:
        """
        Validate domain constraints:
          1. Invalid transaction_type values
          2. Invalid transaction status values
          3. Invalid payment_method values
          4. Invalid invoice payment_status values
          5. Invalid expense status values
          6. Transactions with unrealistically large amounts (> 1B)
        """
        issues: List[Dict[str, Any]] = []
        invalid_count = 0
        total_checked = 0

        checks = [
            (
                "transactions",
                "SELECT COUNT(*) AS cnt FROM transactions "
                "WHERE transaction_type NOT IN ('sale', 'refund', 'adjustment')",
                "Invalid transaction_type",
            ),
            (
                "transactions",
                "SELECT COUNT(*) AS cnt FROM transactions "
                "WHERE status NOT IN ('completed', 'pending', 'cancelled')",
                "Invalid transaction status",
            ),
            (
                "transactions",
                "SELECT COUNT(*) AS cnt FROM transactions "
                "WHERE payment_method NOT IN "
                "('bank_transfer', 'credit_card', 'cash', 'cheque')",
                "Invalid payment_method",
            ),
            (
                "invoices",
                "SELECT COUNT(*) AS cnt FROM invoices "
                "WHERE payment_status NOT IN ('unpaid', 'partial', 'paid', 'overdue')",
                "Invalid invoice payment_status",
            ),
            (
                "expenses",
                "SELECT COUNT(*) AS cnt FROM expenses "
                "WHERE status NOT IN ('approved', 'pending', 'rejected')",
                "Invalid expense status",
            ),
            (
                "transactions",
                "SELECT COUNT(*) AS cnt FROM transactions WHERE amount > 1000000000",
                "Transactions with suspiciously large amount (> 1B)",
            ),
        ]

        for table, sql, desc in checks:
            try:
                row = self.db.execute(text(sql)).fetchone()
                cnt = int(row.cnt or 0)
                invalid_count += cnt
                if cnt > 0:
                    issues.append(
                        {
                            "table": table,
                            "issue": desc,
                            "affected_rows": cnt,
                            "severity": "medium",
                        }
                    )
            except Exception:
                logger.exception("validity check failed: %s", desc)

        for table in ("transactions", "invoices", "expenses"):
            try:
                row = self.db.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}")).fetchone()
                total_checked += int(row.cnt or 0)
            except Exception:
                logger.exception("row count failed for %s", table)

        score = round(
            ((total_checked - invalid_count) / total_checked * 100)
            if total_checked
            else 100.0,
            2,
        )
        return {
            "score": score,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Duplicates
    # ------------------------------------------------------------------

    def check_duplicates(self) -> Dict[str, Any]:
        """
        Detect duplicate records:
          1. Duplicate (customer_id, invoice_date, invoice_amount) in invoices
        """
        issues: List[Dict[str, Any]] = []
        duplicate_count = 0
        total_count = 0

        dup_checks = [
            (
                "invoices",
                """
                SELECT 
                    (SELECT COUNT(*) FROM invoices) - 
                    (SELECT COUNT(*) FROM (SELECT DISTINCT customer_id, invoice_date, invoice_amount FROM invoices))
                    AS duplicates,
                    (SELECT COUNT(*) FROM invoices) AS total
                """,
                "Duplicate invoices (same customer, date, amount)",
            ),
        ]

        for table, sql, desc in dup_checks:
            try:
                row = self.db.execute(text(sql)).fetchone()
                dups = int(row.duplicates or 0)
                total = int(row.total or 0)
                duplicate_count += dups
                total_count += total
                if dups > 0:
                    issues.append(
                        {
                            "table": table,
                            "issue": desc,
                            "duplicate_rows": dups,
                            "severity": "high",
                        }
                    )
            except Exception:
                logger.exception("duplicate check failed: %s", desc)

        # Count total transactions to include in denominator
        try:
            row = self.db.execute(
                text("SELECT COUNT(*) AS cnt FROM transactions")
            ).fetchone()
            total_count += int(row.cnt or 0)
        except Exception:
            logger.exception("row count failed for transactions (duplicates check)")

        rate = round(
            (duplicate_count / total_count * 100) if total_count else 0.0, 4
        )
        score = round(100.0 - rate, 2)
        return {
            "score": score,
            "duplicate_count": duplicate_count,
            "rate": rate,
        }

    # ------------------------------------------------------------------
    # Full report
    # ------------------------------------------------------------------

    def get_full_report(self) -> DataQualityReport:
        """
        Run all four checks and compute a weighted overall score.

        Weights: completeness=0.30, consistency=0.25, validity=0.25, duplicates=0.20
        """
        try:
            completeness = self.check_completeness()
            consistency  = self.check_consistency()
            validity     = self.check_validity()
            duplicates   = self.check_duplicates()

            c_score   = completeness["score"]
            co_score  = consistency["score"]
            v_score   = validity["score"]
            d_score   = duplicates["score"]

            overall = round(
                c_score  * self.WEIGHTS["completeness"]
                + co_score * self.WEIGHTS["consistency"]
                + v_score  * self.WEIGHTS["validity"]
                + d_score  * self.WEIGHTS["duplicates"],
                2,
            )

            # Aggregate all issues
            all_issues: List[Dict[str, Any]] = (
                consistency["issues"] + validity["issues"]
            )
            if duplicates["duplicate_count"] > 0:
                all_issues.append(
                    {
                        "table": "invoices",
                        "issue": "Duplicate invoice records detected",
                        "affected_rows": duplicates["duplicate_count"],
                        "severity": "high",
                    }
                )

            # Derive missing_value_rate from completeness data
            total_records = completeness.get("total_count", 0)
            missing_count = completeness.get("missing_count", 0)
            missing_value_rate = round(
                (missing_count / total_records * 100) if total_records else 0.0, 4
            )

            return DataQualityReport(
                overall_score=overall,
                completeness=c_score,
                consistency=co_score,
                validity=v_score,
                duplicate_rate=duplicates["rate"],
                missing_value_rate=missing_value_rate,
                total_records=total_records,
                issues=all_issues,
                generated_at=datetime.utcnow().isoformat() + "Z",
            )
        except Exception:
            logger.exception("get_full_report failed")
            return DataQualityReport(
                overall_score=0.0,
                completeness=0.0,
                consistency=0.0,
                validity=0.0,
                duplicate_rate=0.0,
                missing_value_rate=0.0,
                total_records=0,
                issues=[{"issue": "Report generation failed — check server logs", "severity": "critical"}],
                generated_at=datetime.utcnow().isoformat() + "Z",
            )
