"""Anomaly detection for expenses and transactions using IQR and z-score methods."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models import Category, Department, Expense, Transaction
from app.schemas.risk import AnomalyRecord
from app.utils.formatters import format_currency, safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

_DEFAULT_LOOKBACK_MONTHS = 12


class AnomalyDetectionService:
    """Detect statistical anomalies in expenses and transactions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # IQR-based expense anomaly detection
    # ------------------------------------------------------------------

    def _detect_expense_anomalies_iqr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag expense records whose amount exceeds Q3 + 1.5*IQR within their category.

        Returns the flagged subset with extra columns:
            expected_range_low, expected_range_high, anomaly_score
        """
        if df.empty:
            return df.iloc[0:0]  # empty DataFrame preserving columns

        flagged_parts = []
        for category, group in df.groupby("category"):
            amounts = group["amount"]
            q1 = float(amounts.quantile(0.25))
            q3 = float(amounts.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                std = float(amounts.std())
                if std > 0:
                    iqr = std
                else:
                    continue
            upper_fence = q3 + 1.5 * iqr
            lower_fence = max(0.0, q1 - 1.5 * iqr)
            outliers = group[amounts > upper_fence].copy()
            if outliers.empty:
                continue
            outliers["expected_range_low"] = round(lower_fence, 2)
            outliers["expected_range_high"] = round(upper_fence, 2)
            outliers["anomaly_score"] = ((outliers["amount"] - q3) / iqr).round(4)
            flagged_parts.append(outliers)

        if not flagged_parts:
            return df.iloc[0:0]

        return pd.concat(flagged_parts, ignore_index=True)

    # ------------------------------------------------------------------
    # Z-score-based transaction anomaly detection
    # ------------------------------------------------------------------

    def _detect_transaction_anomalies_zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag transaction records whose |z-score| > 2.5 within their category.

        Returns the flagged subset with extra columns:
            expected_range_low, expected_range_high, anomaly_score
        """
        if df.empty:
            return df.iloc[0:0]

        flagged_parts = []
        for category, group in df.groupby("category"):
            amounts = group["amount"]
            if len(amounts) < 3:
                continue
            mean = float(amounts.mean())
            std = float(amounts.std())
            if std == 0:
                continue
            z_scores = (amounts - mean) / std
            outliers = group[abs(z_scores) > 2.5].copy()
            if outliers.empty:
                continue
            lower_fence = max(0.0, mean - 2.5 * std)
            upper_fence = mean + 2.5 * std
            outliers["expected_range_low"] = round(lower_fence, 2)
            outliers["expected_range_high"] = round(upper_fence, 2)
            outliers["anomaly_score"] = abs(z_scores[outliers.index]).round(4)
            flagged_parts.append(outliers)

        if not flagged_parts:
            return df.iloc[0:0]

        return pd.concat(flagged_parts, ignore_index=True)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _severity(anomaly_score: float) -> str:
        if anomaly_score > 3:
            return "high"
        if anomaly_score >= 1.5:
            return "medium"
        return "low"

    @staticmethod
    def _reason(amount: float, low: float, high: float, category: str) -> str:
        return (
            f"Amount of {format_currency(amount)} significantly exceeds the expected "
            f"range of {format_currency(low)}–{format_currency(high)} for {category}"
        )

    def _default_date_range(
        self, start_date: Optional[date], end_date: Optional[date]
    ) -> tuple:
        if end_date is None:
            end_date = get_as_of_date()
        if start_date is None:
            start_date = end_date - timedelta(days=_DEFAULT_LOOKBACK_MONTHS * 30)
        return start_date, end_date

    # ------------------------------------------------------------------
    # Category name lookup (cached per instance call)
    # ------------------------------------------------------------------

    def _category_names(self) -> dict:
        try:
            rows = self.db.query(Category.category_id, Category.name).all()
            return {r.category_id: r.name for r in rows}
        except Exception:
            logger.debug("Category name lookup failed", exc_info=True)
            return {}

    def _department_names(self) -> dict:
        try:
            rows = self.db.query(Department.department_id, Department.name).all()
            return {r.department_id: r.name for r in rows}
        except Exception:
            logger.debug("Department name lookup failed", exc_info=True)
            return {}

    # ------------------------------------------------------------------
    # Public: expense anomalies
    # ------------------------------------------------------------------

    def get_expense_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
    ) -> List[AnomalyRecord]:
        """Detect anomalous expense records using IQR within each category."""
        start_date, end_date = self._default_date_range(start_date, end_date)
        try:
            rows = (
                self.db.query(Expense)
                .filter(
                    Expense.status == "approved",
                    Expense.expense_date >= start_date,
                    Expense.expense_date <= end_date,
                )
                .all()
            )
        except Exception:
            logger.exception("Failed to query expenses")
            return []

        if not rows:
            return []

        cat_names = self._category_names()
        dept_names = self._department_names()

        records = [
            {
                "record_id": str(r.expense_id),
                "date": r.expense_date.isoformat(),
                "category_id": r.category_id,
                "category": cat_names.get(r.category_id, str(r.category_id)),
                "department_id": r.department_id,
                "amount": float(r.amount),
            }
            for r in rows
        ]
        df = pd.DataFrame(records)
        flagged = self._detect_expense_anomalies_iqr(df)
        flagged = flagged.sort_values("anomaly_score", ascending=False).head(limit)

        results = []
        for _, row in flagged.iterrows():
            score = float(row["anomaly_score"])
            severity = self._severity(score)
            dept_name = dept_names.get(row.get("department_id"), None)
            results.append(
                AnomalyRecord(
                    record_id=str(row["record_id"]),
                    date=str(row["date"]),
                    category=str(row["category"]),
                    department=dept_name,
                    amount=round(float(row["amount"]), 2),
                    expected_range_low=round(float(row["expected_range_low"]), 2),
                    expected_range_high=round(float(row["expected_range_high"]), 2),
                    anomaly_score=round(score, 4),
                    severity=severity,
                    reason=self._reason(float(row["amount"]), float(row["expected_range_low"]), float(row["expected_range_high"]), str(row["category"])),
                    requires_investigation=severity in ("medium", "high"),
                )
            )
        return results

    # ------------------------------------------------------------------
    # Public: transaction anomalies
    # ------------------------------------------------------------------

    def get_transaction_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
    ) -> List[AnomalyRecord]:
        """Detect anomalous transaction records using z-score within each category."""
        start_date, end_date = self._default_date_range(start_date, end_date)
        try:
            rows = (
                self.db.query(Transaction)
                .filter(
                    Transaction.transaction_type == "sale",
                    Transaction.status == "completed",
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
                .all()
            )
        except Exception:
            logger.exception("Failed to query transactions")
            return []

        if not rows:
            return []

        cat_names = self._category_names()

        records = [
            {
                "record_id": str(r.transaction_id),
                "date": r.transaction_date.isoformat(),
                "category_id": r.category_id,
                "category": cat_names.get(r.category_id, str(r.category_id)),
                "amount": float(r.amount * (1 - r.discount_pct / 100)),
            }
            for r in rows
        ]
        df = pd.DataFrame(records)
        flagged = self._detect_transaction_anomalies_zscore(df)
        flagged = flagged.sort_values("anomaly_score", ascending=False).head(limit)

        results = []
        for _, row in flagged.iterrows():
            score = float(row["anomaly_score"])
            severity = self._severity(score)
            results.append(
                AnomalyRecord(
                    record_id=str(row["record_id"]),
                    date=str(row["date"]),
                    category=str(row["category"]),
                    department=None,
                    amount=round(float(row["amount"]), 2),
                    expected_range_low=round(float(row["expected_range_low"]), 2),
                    expected_range_high=round(float(row["expected_range_high"]), 2),
                    anomaly_score=round(score, 4),
                    severity=severity,
                    reason=self._reason(float(row["amount"]), float(row["expected_range_low"]), float(row["expected_range_high"]), str(row["category"])),
                    requires_investigation=severity in ("medium", "high"),
                )
            )
        return results

    # ------------------------------------------------------------------
    # Public: anomaly summary
    # ------------------------------------------------------------------

    def get_anomaly_summary(self) -> dict:
        """Return aggregate counts and flagged amounts for expenses and transactions."""
        try:
            expense_anomalies = self.get_expense_anomalies()
            transaction_anomalies = self.get_transaction_anomalies()

            all_anomalies = expense_anomalies + transaction_anomalies
            high_severity = sum(1 for a in all_anomalies if a.severity == "high")
            total_flagged_amount = sum(a.amount for a in all_anomalies)

            return {
                "total_expense_anomalies": len(expense_anomalies),
                "total_transaction_anomalies": len(transaction_anomalies),
                "high_severity": high_severity,
                "total_flagged_amount": round(total_flagged_amount, 2),
            }
        except Exception:
            logger.exception("get_anomaly_summary failed")
            return {
                "total_expense_anomalies": 0,
                "total_transaction_anomalies": 0,
                "high_severity": 0,
                "total_flagged_amount": 0.0,
            }
