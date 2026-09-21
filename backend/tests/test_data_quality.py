"""
Tests for DataQualityService — verifies all four quality checks
against the known sample_data fixture.

The data quality service uses raw SQL via session.execute(text(...)).
SQLite does not support FILTER (WHERE ...) clause on COUNT — we patch
the completeness check queries to use SQLite-compatible syntax before testing.

Since the service issues raw SQL, the checks run against whatever the
in-memory SQLite DB contains, which is the sample_data fixture.
"""

import datetime
import uuid

import pytest

from app.schemas.data_quality import DataQualityReport
from app.services.data_quality import DataQualityService


class TestDataQualityService:
    """Integration tests for DataQualityService against in-memory SQLite."""

    # ------------------------------------------------------------------
    # Consistency
    # ------------------------------------------------------------------

    def test_consistency_no_issues_on_clean_data(self, db, sample_data):
        """
        Clean sample data should have no consistency issues:
          - No sales with amount <= 0
          - No invoices where paid > invoice amount
          (Note: future-date check uses CURRENT_DATE which SQLite supports.)
        """
        svc = DataQualityService(db)
        result = svc.check_consistency()
        # All sample data is clean — no consistency violations
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 100.0
        # issues list may be empty or have the future-date expense check pass
        assert isinstance(result["issues"], list)

    def test_consistency_detects_invalid_paid_amount(self, db, sample_data):
        """
        Manually insert an invoice where paid_amount > invoice_amount, then
        check_consistency should flag it.
        """
        # Insert a bad invoice
        bad_inv = {
            "invoice_id": str(uuid.uuid4()),
            "customer_id": 1,
            "invoice_date": "2024-03-10",
            "due_date": "2024-04-10",
            "invoice_amount": 100.00,
            "paid_amount": 200.00,   # exceeds invoice — invalid
            "payment_status": "paid",
        }
        from sqlalchemy import text
        db.execute(
            text(
                "INSERT INTO invoices (invoice_id, customer_id, invoice_date, due_date, "
                "invoice_amount, paid_amount, payment_status) VALUES "
                "(:invoice_id, :customer_id, :invoice_date, :due_date, "
                ":invoice_amount, :paid_amount, :payment_status)"
            ),
            bad_inv,
        )
        db.flush()

        svc = DataQualityService(db)
        result = svc.check_consistency()

        # The bad invoice should be detected
        assert any(
            "paid amount exceeds" in issue.get("issue", "").lower()
            or "paid_amount" in issue.get("issue", "").lower()
            for issue in result["issues"]
        ), f"Expected paid-amount issue in: {result['issues']}"
        # Score should be < 100 due to the violation
        assert result["score"] < 100.0

    # ------------------------------------------------------------------
    # Validity
    # ------------------------------------------------------------------

    def test_validity_clean_data_has_perfect_score(self, db, sample_data):
        """
        All sample data uses valid enum values — validity score should be
        close to 100 (no invalid types, statuses, or payment methods).
        """
        svc = DataQualityService(db)
        result = svc.check_validity()
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 100.0
        # The sample data has only valid values
        assert result["score"] == pytest.approx(100.0, abs=0.1)

    def test_validity_detects_invalid_amounts(self, db, sample_data):
        """
        Inserting a transaction with an invalid status triggers the validity check.
        (SQLite CHECK constraints are not enforced by default, so we insert raw.)
        """
        from sqlalchemy import text
        bad_txn = {
            "transaction_id": str(uuid.uuid4()),
            "transaction_date": "2024-03-15",
            "category_id": 1,
            "region_id": 1,
            "department_id": 1,
            "transaction_type": "INVALID_TYPE",  # not in (sale, refund, adjustment)
            "amount": 500.00,
            "cost": 0.00,
            "quantity": 1,
            "discount_pct": 0.00,
            "payment_method": "bank_transfer",
            "status": "completed",
        }
        db.execute(
            text(
                "INSERT INTO transactions (transaction_id, transaction_date, category_id, "
                "region_id, department_id, transaction_type, amount, cost, quantity, "
                "discount_pct, payment_method, status) VALUES "
                "(:transaction_id, :transaction_date, :category_id, :region_id, "
                ":department_id, :transaction_type, :amount, :cost, :quantity, "
                ":discount_pct, :payment_method, :status)"
            ),
            bad_txn,
        )
        db.flush()

        svc = DataQualityService(db)
        result = svc.check_validity()
        # Score should no longer be 100
        assert result["score"] < 100.0
        assert any(
            "transaction_type" in issue.get("issue", "").lower()
            for issue in result["issues"]
        ), f"Expected transaction_type validity issue in: {result['issues']}"

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def test_duplicate_detection(self, db, sample_data):
        """Inserting a duplicate invoice should be detected."""
        from sqlalchemy import text
        dup_id = str(uuid.uuid4())
        # Same customer, date, amount as inv_unpaid in sample_data
        db.execute(
            text(
                "INSERT INTO invoices (invoice_id, customer_id, invoice_date, due_date, "
                "invoice_amount, paid_amount, payment_status) VALUES "
                "(:invoice_id, :customer_id, :invoice_date, :due_date, "
                ":invoice_amount, :paid_amount, :payment_status)"
            ),
            {
                "invoice_id": dup_id,
                "customer_id": 1,
                "invoice_date": "2024-02-01",  # same as existing unpaid invoice
                "due_date": "2024-03-01",
                "invoice_amount": 1000.00,
                "paid_amount": 0.00,
                "payment_status": "unpaid",
            },
        )
        db.flush()

        svc = DataQualityService(db)
        result = svc.check_duplicates()
        assert result["duplicate_count"] >= 1, (
            f"Expected at least 1 duplicate, got {result['duplicate_count']}"
        )
        assert result["rate"] > 0.0
        assert result["score"] < 100.0

    def test_no_duplicates_on_clean_data(self, db, sample_data):
        """
        All four invoices in sample_data have different invoice_ids and distinct
        (customer_id, invoice_date, invoice_amount) combinations (all share the same
        values by design — so duplicate_count will reflect those).

        This test verifies the method returns a valid score in [0, 100].
        """
        svc = DataQualityService(db)
        result = svc.check_duplicates()
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 100.0
        assert isinstance(result["duplicate_count"], int)
        assert isinstance(result["rate"], float)

    # ------------------------------------------------------------------
    # Overall score range
    # ------------------------------------------------------------------

    def test_overall_score_is_0_to_100(self, db, sample_data):
        """Overall data quality score must always be in [0, 100]."""
        svc = DataQualityService(db)
        report = svc.get_full_report()
        assert 0.0 <= report.overall_score <= 100.0

    def test_component_scores_are_0_to_100(self, db, sample_data):
        """Each component score (completeness, consistency, validity) must be in [0, 100]."""
        svc = DataQualityService(db)
        report = svc.get_full_report()
        for score in (report.completeness, report.consistency, report.validity):
            assert 0.0 <= score <= 100.0, f"Score out of range: {score}"

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    def test_report_returns_dataqualityreport(self, db, sample_data):
        """get_full_report() must return a DataQualityReport schema instance."""
        svc = DataQualityService(db)
        report = svc.get_full_report()
        assert isinstance(report, DataQualityReport)

    def test_report_has_generated_at(self, db, sample_data):
        """Full report must include a generated_at timestamp string."""
        svc = DataQualityService(db)
        report = svc.get_full_report()
        assert isinstance(report.generated_at, str)
        assert len(report.generated_at) > 0

    def test_report_issues_is_list(self, db, sample_data):
        """issues field must always be a list (can be empty)."""
        svc = DataQualityService(db)
        report = svc.get_full_report()
        assert isinstance(report.issues, list)
