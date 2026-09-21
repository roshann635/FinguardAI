"""Utility functions for formatting financial values and deriving display metadata."""


def format_currency(value: float, currency: str = "INR") -> str:
    """Format a numeric value as a currency string with abbreviated magnitude.

    Examples:
        1_200_000_000 -> "₹1.2B"
        84_600_000    -> "₹84.6M"
        450_000       -> "₹450K"
        9_500         -> "₹9,500"
    """
    symbol = "₹" if currency == "INR" else currency

    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000_000:
        return f"{sign}{symbol}{abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{symbol}{abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}{symbol}{abs_val / 1_000:.1f}K"
    return f"{sign}{symbol}{abs_val:,.0f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a percentage value with an explicit sign.

    Examples:
        12.4  -> "+12.4%"
        -3.2  -> "-3.2%"
        0.0   -> "0.0%"
    """
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_number(value: float) -> str:
    """Abbreviate a large number using K / M / B suffixes.

    Examples:
        1_500_000 -> "1.5M"
        23_400    -> "23.4K"
        800       -> "800"
    """
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val / 1_000:.1f}K"
    return f"{sign}{abs_val:,.0f}"


def get_direction(change_pct: float) -> str:
    """Return a directional label for a percentage change.

    Threshold: values within ±1% are considered "flat".
    """
    if change_pct > 1.0:
        return "up"
    if change_pct < -1.0:
        return "down"
    return "flat"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide two numbers safely, returning *default* when denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def get_period_label(period: str) -> str:
    """Convert an internal period identifier to a human-readable label.

    Supported identifiers:
        "last_12_months"  -> "Last 12 Months"
        "last_6_months"   -> "Last 6 Months"
        "last_3_months"   -> "Last 3 Months"
        "last_month"      -> "Last Month"
        "ytd"             -> "Year to Date"
        "last_year"       -> "Last Year"
        Any other value is title-cased and returned as-is.
    """
    labels: dict[str, str] = {
        "last_12_months": "Last 12 Months",
        "last_6_months": "Last 6 Months",
        "last_3_months": "Last 3 Months",
        "last_month": "Last Month",
        "ytd": "Year to Date",
        "last_year": "Last Year",
    }
    return labels.get(period, period.replace("_", " ").title())
