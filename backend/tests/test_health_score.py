"""Unit tests for FinancialHealthService."""

import pytest
from app.services.health_service import FinancialHealthService


def test_health_service_direct(db, sample_data):
    svc = FinancialHealthService(db)
    result = svc.calculate_health_score()

    assert "composite_score" in result
    assert 0.0 <= result["composite_score"] <= 100.0
    assert result["grade"] in ("A", "B", "C", "D")
    assert "status" in result
    assert "summary" in result
    assert "pillars" in result

    pillars = result["pillars"]
    for p_key in ("liquidity", "profitability", "credit", "stability"):
        assert p_key in pillars
        p = pillars[p_key]
        assert 0.0 <= p["score"] <= 100.0
        assert p["status"] in ("Excellent", "Good", "Fair", "Critical")
        assert len(p["metrics"]) > 0


def test_health_service_pillars_weighting(db, sample_data):
    svc = FinancialHealthService(db)
    result = svc.calculate_health_score()
    pillars = result["pillars"]

    expected_composite = round(
        0.30 * pillars["liquidity"]["score"]
        + 0.25 * pillars["profitability"]["score"]
        + 0.25 * pillars["credit"]["score"]
        + 0.20 * pillars["stability"]["score"],
        1,
    )
    assert result["composite_score"] == pytest.approx(expected_composite, abs=0.1)
