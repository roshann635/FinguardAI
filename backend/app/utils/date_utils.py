"""Centralised analytical date utility for FinGuard AI.

The synthetic dataset covers Jan 2023 – Mar 2025. Any analytics code that
previously used ``date.today()`` or SQL ``CURRENT_DATE`` would return empty
results when the system clock moves beyond the data range.

This module provides a single ``get_as_of_date()`` function that the entire
analytics stack should use *instead of* ``date.today()``.

Resolution order:
    1. ``DATA_AS_OF_DATE`` environment variable (format: ``YYYY-MM-DD``)
    2. Auto-detected from the latest meaningful date in the database
    3. Fallback to ``date.today()`` if detection fails (should not happen in
       a properly seeded environment)
"""

import logging
import os
from datetime import date
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Module-level cache so we query the DB at most once per process lifetime.
_cached_as_of_date: Optional[date] = None


def _detect_from_db(db: Session) -> date:
    """Query the latest date across key tables."""
    try:
        stmt = text(
            """
            SELECT MAX(latest) AS data_as_of
            FROM (
                SELECT MAX(transaction_date) AS latest FROM transactions
                UNION ALL
                SELECT MAX(expense_date) FROM expenses
                UNION ALL
                SELECT MAX(invoice_date) FROM invoices
                UNION ALL
                SELECT MAX(flow_date) FROM cash_flows
            ) sub
            """
        )
        row = db.execute(stmt).fetchone()
        if row and row.data_as_of:
            detected = row.data_as_of
            if isinstance(detected, str):
                detected = date.fromisoformat(detected)
            logger.info("Auto-detected DATA_AS_OF_DATE from database: %s", detected)
            return detected
    except Exception:
        logger.warning("Failed to auto-detect DATA_AS_OF_DATE from database", exc_info=True)
    return date.today()


def init_as_of_date(db: Session) -> date:
    """Initialise and cache the analytical as-of date.

    Called once at application startup (or lazily on first request).
    """
    global _cached_as_of_date

    # 1. Check environment variable
    env_val = os.getenv("DATA_AS_OF_DATE")
    if env_val:
        try:
            _cached_as_of_date = date.fromisoformat(env_val)
            logger.info("DATA_AS_OF_DATE set from environment: %s", _cached_as_of_date)
            return _cached_as_of_date
        except ValueError:
            logger.warning("Invalid DATA_AS_OF_DATE env value '%s'; falling back to auto-detection", env_val)

    # 2. Auto-detect from database
    _cached_as_of_date = _detect_from_db(db)
    return _cached_as_of_date


def get_as_of_date() -> date:
    """Return the analytical as-of date.

    If ``init_as_of_date`` has been called, returns the cached value.
    Otherwise falls back to ``date.today()`` (and logs a warning).
    """
    if _cached_as_of_date is not None:
        return _cached_as_of_date

    # Fallback — should only happen during tests or if init was skipped
    env_val = os.getenv("DATA_AS_OF_DATE")
    if env_val:
        try:
            return date.fromisoformat(env_val)
        except ValueError:
            pass

    logger.warning(
        "get_as_of_date() called before init_as_of_date(); falling back to date.today(). "
        "This may produce empty analytics if the dataset does not cover today's date."
    )
    return date.today()


def get_as_of_date_iso() -> str:
    """Convenience: ISO-formatted as-of date string."""
    return get_as_of_date().isoformat()
