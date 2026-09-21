"""System metadata and dataset information endpoint."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import (
    Budget,
    CashFlow,
    Customer,
    Expense,
    Invoice,
    Product,
    Transaction,
    Vendor,
)
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info")
def get_system_info(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Return platform, dataset metadata, and current analytical boundary.
    Used by the UI to ensure consistent dataset attribution and record counts.
    """
    settings = get_settings()
    as_of = get_as_of_date()

    counts = {}
    try:
        counts["transactions"] = db.query(func.count(Transaction.transaction_id)).scalar() or 0
        counts["expenses"] = db.query(func.count(Expense.expense_id)).scalar() or 0
        counts["invoices"] = db.query(func.count(Invoice.invoice_id)).scalar() or 0
        counts["customers"] = db.query(func.count(Customer.customer_id)).scalar() or 0
        counts["vendors"] = db.query(func.count(Vendor.vendor_id)).scalar() or 0
        counts["products"] = db.query(func.count(Product.product_id)).scalar() or 0
        counts["cash_flows"] = db.query(func.count(CashFlow.flow_id)).scalar() or 0
        counts["budgets"] = db.query(func.count(Budget.budget_id)).scalar() or 0
    except Exception as exc:
        logger.warning("Failed to query full record counts: %s", exc)
        counts = {
            "transactions": 0,
            "expenses": 0,
            "invoices": 0,
            "customers": 0,
            "vendors": 0,
            "products": 0,
            "cash_flows": 0,
            "budgets": 0,
        }

    total_records = sum(counts.values())

    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "dataset_type": "Synthetic demonstration dataset · Jan 2023 – Mar 2025",
        "dataset_period": {
            "start": "2023-01-01",
            "end": as_of.isoformat(),
            "display": "Jan 2023 – Mar 2025",
        },
        "data_as_of_date": as_of.isoformat(),
        "data_as_of_display": as_of.strftime("%d %b %Y"),
        "record_counts": counts,
        "total_records": total_records,
        "currency": "USD",
    }
