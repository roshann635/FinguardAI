"""
Tests for app.utils.formatters — pure utility functions with no DB dependency.
All tests are stateless; no fixtures required.
"""

import pytest

from app.utils.formatters import (
    format_currency,
    format_number,
    format_percentage,
    get_direction,
    get_period_label,
    safe_divide,
)


# ---------------------------------------------------------------------------
# format_currency
# ---------------------------------------------------------------------------


def test_format_currency_millions():
    """Values >= 1,000,000 should be shown as ₹X.XM."""
    result = format_currency(1_000_000)
    assert "₹" in result
    assert "1.0M" in result


def test_format_currency_billions():
    """Values >= 1,000,000,000 should be shown as ₹X.XB."""
    result = format_currency(1_500_000_000)
    assert "₹" in result
    assert "1.5B" in result


def test_format_currency_thousands():
    """Values >= 1,000 but < 1,000,000 should be shown as ₹X.XK."""
    result = format_currency(500_000)
    assert "₹" in result
    assert "500.0K" in result


def test_format_currency_small():
    """Values < 1,000 should be shown as ₹X (no abbreviation)."""
    result = format_currency(500)
    assert "₹" in result
    # Should not contain K, M, or B suffix
    assert "K" not in result
    assert "M" not in result
    assert "B" not in result


def test_format_currency_zero():
    """Zero should render as ₹0."""
    result = format_currency(0)
    assert "₹" in result
    assert "0" in result


def test_format_currency_negative():
    """Negative values should include a minus sign before the symbol."""
    result = format_currency(-500_000)
    assert "-" in result
    assert "₹" in result
    assert "500.0K" in result


def test_format_currency_exactly_one_billion():
    """Boundary value: exactly 1B."""
    result = format_currency(1_000_000_000)
    assert "1.0B" in result


def test_format_currency_exactly_one_million():
    """Boundary value: exactly 1M."""
    result = format_currency(1_000_000)
    assert "1.0M" in result


def test_format_currency_exactly_one_thousand():
    """Boundary value: exactly 1K."""
    result = format_currency(1_000)
    assert "1.0K" in result


# ---------------------------------------------------------------------------
# format_percentage
# ---------------------------------------------------------------------------


def test_format_percentage_positive():
    """Positive values should include a '+' sign."""
    result = format_percentage(12.4)
    assert "+" in result
    assert "12.4" in result
    assert "%" in result


def test_format_percentage_negative():
    """Negative values should include a '-' sign (no '+')."""
    result = format_percentage(-5.2)
    assert "-" in result
    assert "5.2" in result
    assert "+" not in result


def test_format_percentage_zero():
    """Zero should render without a '+' sign (edge case)."""
    result = format_percentage(0.0)
    assert "%" in result
    assert "+" not in result
    assert "0.0" in result


def test_format_percentage_decimals_respected():
    """Custom decimals parameter should control precision."""
    result = format_percentage(7.654321, decimals=2)
    assert "7.65" in result


# ---------------------------------------------------------------------------
# safe_divide
# ---------------------------------------------------------------------------


def test_safe_divide_normal():
    """Normal division should return the correct quotient."""
    assert safe_divide(10, 2) == pytest.approx(5.0)


def test_safe_divide_zero_denominator():
    """Division by zero should return the default value (0.0)."""
    assert safe_divide(10, 0) == 0.0


def test_safe_divide_custom_default():
    """Division by zero with custom default should return that default."""
    assert safe_divide(10, 0, default=-1.0) == -1.0


def test_safe_divide_zero_numerator():
    """Zero numerator with non-zero denominator should return 0.0."""
    assert safe_divide(0, 5) == pytest.approx(0.0)


def test_safe_divide_both_zero():
    """Both zero should return default without raising."""
    assert safe_divide(0, 0) == 0.0
    assert safe_divide(0, 0, default=99.0) == 99.0


def test_safe_divide_float_result():
    """Result type should always be float."""
    result = safe_divide(7, 3)
    assert isinstance(result, float)


# ---------------------------------------------------------------------------
# get_direction
# ---------------------------------------------------------------------------


def test_get_direction_up():
    """Positive change > +1% should be 'up'."""
    assert get_direction(5.0) == "up"


def test_get_direction_down():
    """Negative change < -1% should be 'down'."""
    assert get_direction(-5.0) == "down"


def test_get_direction_flat_positive():
    """Change within +1% should be 'flat'."""
    assert get_direction(0.5) == "flat"


def test_get_direction_flat_negative():
    """Change within -1% should be 'flat'."""
    assert get_direction(-0.9) == "flat"


def test_get_direction_flat_zero():
    """Zero change should be 'flat'."""
    assert get_direction(0.0) == "flat"


def test_get_direction_boundary_exactly_one():
    """Exactly +1.0 is NOT above threshold → 'flat'."""
    assert get_direction(1.0) == "flat"


def test_get_direction_just_above_boundary():
    """1.001 is above the 1% threshold → 'up'."""
    assert get_direction(1.001) == "up"


# ---------------------------------------------------------------------------
# format_number
# ---------------------------------------------------------------------------


def test_format_number_millions():
    assert "1.5M" in format_number(1_500_000)


def test_format_number_thousands():
    assert "23.4K" in format_number(23_400)


def test_format_number_small():
    result = format_number(800)
    assert "800" in result
    assert "K" not in result


# ---------------------------------------------------------------------------
# get_period_label
# ---------------------------------------------------------------------------


def test_get_period_label_known_keys():
    assert get_period_label("last_12_months") == "Last 12 Months"
    assert get_period_label("last_6_months") == "Last 6 Months"
    assert get_period_label("ytd") == "Year to Date"
    assert get_period_label("last_year") == "Last Year"


def test_get_period_label_unknown_falls_back():
    """Unknown keys should be title-cased with underscores replaced."""
    result = get_period_label("custom_period_key")
    assert result == "Custom Period Key"
