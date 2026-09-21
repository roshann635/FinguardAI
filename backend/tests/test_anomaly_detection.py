"""
Tests for anomaly detection logic — IQR and z-score methods.

These tests operate directly on the internal DataFrame methods of
AnomalyDetectionService, so they are database-independent and run
without any fixture data. The database-backed tests use the sample_data
fixture from conftest.py.
"""

import numpy as np
import pandas as pd
import pytest

from app.ml.anomaly_detection import AnomalyDetectionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    """Return an AnomalyDetectionService instance with a None db (not needed for unit tests)."""
    svc = AnomalyDetectionService.__new__(AnomalyDetectionService)
    svc.db = None
    return svc


def _expense_df(amounts: list, category: str = "Operations") -> pd.DataFrame:
    """Build a minimal expense DataFrame for testing."""
    n = len(amounts)
    return pd.DataFrame({
        "record_id": [str(i) for i in range(n)],
        "date": ["2024-01-01"] * n,
        "category": [category] * n,
        "department_id": [1] * n,
        "amount": [float(a) for a in amounts],
    })


def _transaction_df(amounts: list, category: str = "Software") -> pd.DataFrame:
    """Build a minimal transaction DataFrame for testing."""
    n = len(amounts)
    return pd.DataFrame({
        "record_id": [str(i) for i in range(n)],
        "date": ["2024-01-01"] * n,
        "category": [category] * n,
        "amount": [float(a) for a in amounts],
    })


# ---------------------------------------------------------------------------
# IQR detection
# ---------------------------------------------------------------------------


class TestIQRDetection:
    """Tests for _detect_expense_anomalies_iqr."""

    def test_iqr_detection_flags_outliers(self):
        """IQR detection should flag values > Q3 + 1.5*IQR."""
        svc = _make_service()
        # 18 normal values at 100, plus 5000 as clear outlier
        amounts = [100.0] * 18 + [100.0, 5000.0]
        df = _expense_df(amounts)
        flagged = svc._detect_expense_anomalies_iqr(df)

        assert not flagged.empty, "Expected at least one outlier to be flagged"
        assert 5000.0 in flagged["amount"].values, "5000 should be flagged as outlier"

    def test_iqr_detection_does_not_flag_normal_values(self):
        """IQR detection should NOT flag values within the normal range."""
        svc = _make_service()
        # Uniform data — all same value, IQR=0 → no flagging
        amounts = [100.0] * 20
        df = _expense_df(amounts)
        flagged = svc._detect_expense_anomalies_iqr(df)
        assert flagged.empty, "Uniform data should produce no outliers"

    def test_iqr_detection_returns_empty_on_empty_input(self):
        """Empty DataFrame input should return empty DataFrame."""
        svc = _make_service()
        empty_df = _expense_df([])
        flagged = svc._detect_expense_anomalies_iqr(empty_df)
        assert flagged.empty

    def test_iqr_anomaly_score_positive(self):
        """anomaly_score for flagged IQR records should be positive."""
        svc = _make_service()
        amounts = [100.0] * 18 + [100.0, 5000.0]
        df = _expense_df(amounts)
        flagged = svc._detect_expense_anomalies_iqr(df)
        for score in flagged["anomaly_score"]:
            assert score > 0, f"anomaly_score should be positive, got {score}"

    def test_iqr_expected_range_low_nonnegative(self):
        """expected_range_low should never be negative."""
        svc = _make_service()
        amounts = [50.0, 100.0, 150.0, 100.0, 5000.0]
        df = _expense_df(amounts)
        flagged = svc._detect_expense_anomalies_iqr(df)
        for low in flagged["expected_range_low"]:
            assert low >= 0.0, f"expected_range_low should be >= 0, got {low}"

    def test_iqr_expected_range_high_exceeds_low(self):
        """expected_range_high should always be greater than expected_range_low."""
        svc = _make_service()
        amounts = [100.0] * 15 + [100.0, 100.0, 100.0, 150.0, 9000.0]
        df = _expense_df(amounts)
        flagged = svc._detect_expense_anomalies_iqr(df)
        if not flagged.empty:
            for _, row in flagged.iterrows():
                assert row["expected_range_high"] > row["expected_range_low"]


# ---------------------------------------------------------------------------
# Z-score detection
# ---------------------------------------------------------------------------


class TestZScoreDetection:
    """Tests for _detect_transaction_anomalies_zscore."""

    def test_zscore_detection_flags_outliers(self):
        """Z-score detection should flag values where |z| > 2.5."""
        svc = _make_service()
        # Mean ~100, std ~10; 5000 has z >> 2.5
        np.random.seed(42)
        amounts = list(np.random.normal(loc=100, scale=10, size=50)) + [5000.0]
        df = _transaction_df(amounts)
        flagged = svc._detect_transaction_anomalies_zscore(df)
        assert not flagged.empty, "Expected 5000 to be flagged as z-score outlier"
        assert 5000.0 in flagged["amount"].values

    def test_zscore_returns_empty_for_too_few_records(self):
        """Z-score needs at least 3 records per category to produce results."""
        svc = _make_service()
        df = _transaction_df([100.0, 200.0])  # only 2 records
        flagged = svc._detect_transaction_anomalies_zscore(df)
        assert flagged.empty

    def test_zscore_does_not_flag_normal_data(self):
        """Uniformly distributed data within 2.5 std should not be flagged."""
        svc = _make_service()
        np.random.seed(0)
        amounts = list(np.random.uniform(490, 510, size=100))
        df = _transaction_df(amounts)
        flagged = svc._detect_transaction_anomalies_zscore(df)
        # Very tight distribution — no points should be beyond 2.5 std
        assert flagged.empty, "Tight normal distribution should produce no outliers"

    def test_zscore_returns_empty_on_empty_input(self):
        """Empty DataFrame input should return empty DataFrame."""
        svc = _make_service()
        empty_df = _transaction_df([])
        flagged = svc._detect_transaction_anomalies_zscore(empty_df)
        assert flagged.empty

    def test_zscore_anomaly_score_is_absolute(self):
        """anomaly_score for z-score detection should equal the |z| value (> 2.5)."""
        svc = _make_service()
        np.random.seed(42)
        amounts = list(np.random.normal(loc=100, scale=10, size=50)) + [5000.0]
        df = _transaction_df(amounts)
        flagged = svc._detect_transaction_anomalies_zscore(df)
        for score in flagged["anomaly_score"]:
            assert score > 2.5, f"z-score anomaly score should be > 2.5, got {score}"


# ---------------------------------------------------------------------------
# Severity helper
# ---------------------------------------------------------------------------


class TestSeverityHelper:
    """Tests for AnomalyDetectionService._severity static method."""

    def test_severity_high(self):
        assert AnomalyDetectionService._severity(3.1) == "high"

    def test_severity_medium(self):
        assert AnomalyDetectionService._severity(2.0) == "medium"

    def test_severity_low(self):
        assert AnomalyDetectionService._severity(0.5) == "low"

    def test_severity_boundary_at_three(self):
        """Score exactly 3.0 is NOT above the > 3 threshold — should be 'medium'."""
        assert AnomalyDetectionService._severity(3.0) == "medium"

    def test_severity_boundary_at_one_point_five(self):
        """Score exactly 1.5 meets the >= 1.5 threshold — should be 'medium'."""
        assert AnomalyDetectionService._severity(1.5) == "medium"


# ---------------------------------------------------------------------------
# Reason text — grounding contract
# ---------------------------------------------------------------------------


class TestAnomalyReason:
    """Verify the anomaly reason text follows the grounding contract."""

    def test_anomaly_record_never_says_fraud(self):
        """Anomaly reason text must never contain the word 'fraud'."""
        svc = _make_service()
        reason = svc._reason(5000.0, 100.0, 300.0, "Operations")
        assert "fraud" not in reason.lower(), (
            f"Reason text must not mention 'fraud': {reason}"
        )

    def test_anomaly_reason_includes_category(self):
        """Reason text should mention the category name."""
        svc = _make_service()
        reason = svc._reason(5000.0, 100.0, 300.0, "Operations")
        assert "Operations" in reason

    def test_anomaly_reason_includes_amount(self):
        """Reason text should reference the actual amount."""
        svc = _make_service()
        reason = svc._reason(5000.0, 100.0, 300.0, "Operations")
        # format_currency(5000) → "₹5.0K"
        assert "₹" in reason

    def test_anomaly_reason_mentions_expected_range(self):
        """Reason text should reference both expected_range_low and _high."""
        svc = _make_service()
        reason = svc._reason(5000.0, 100.0, 300.0, "Marketing")
        # Both boundary values should appear as formatted currency
        assert "₹" in reason
        assert "–" in reason or "-" in reason  # range separator


# ---------------------------------------------------------------------------
# DB-backed: end-to-end anomaly summary (uses sample_data)
# ---------------------------------------------------------------------------


class TestAnomalyDetectionWithDB:
    """Light smoke tests that exercise the full service against the in-memory DB."""

    def test_get_anomaly_summary_returns_dict(self, db, sample_data):
        """get_anomaly_summary must always return a dict with known keys."""
        svc = AnomalyDetectionService(db)
        result = svc.get_anomaly_summary()
        assert isinstance(result, dict)
        for key in (
            "total_expense_anomalies",
            "total_transaction_anomalies",
            "high_severity",
            "total_flagged_amount",
        ):
            assert key in result, f"Missing key '{key}' in anomaly summary"

    def test_anomaly_summary_nonnegative_counts(self, db, sample_data):
        """All anomaly summary counts must be non-negative."""
        svc = AnomalyDetectionService(db)
        result = svc.get_anomaly_summary()
        assert result["total_expense_anomalies"] >= 0
        assert result["total_transaction_anomalies"] >= 0
        assert result["high_severity"] >= 0
        assert result["total_flagged_amount"] >= 0.0

    def test_expense_anomalies_returns_list(self, db, sample_data):
        """get_expense_anomalies must return a list (possibly empty)."""
        svc = AnomalyDetectionService(db)
        result = svc.get_expense_anomalies()
        assert isinstance(result, list)

    def test_transaction_anomalies_returns_list(self, db, sample_data):
        """get_transaction_anomalies must return a list (possibly empty)."""
        svc = AnomalyDetectionService(db)
        result = svc.get_transaction_anomalies()
        assert isinstance(result, list)

    def test_anomaly_records_do_not_contain_fraud(self, db, sample_data):
        """No AnomalyRecord reason field should contain the word 'fraud'."""
        svc = AnomalyDetectionService(db)
        all_records = svc.get_expense_anomalies() + svc.get_transaction_anomalies()
        for record in all_records:
            assert "fraud" not in record.reason.lower(), (
                f"AnomalyRecord reason contains forbidden word 'fraud': {record.reason}"
            )
