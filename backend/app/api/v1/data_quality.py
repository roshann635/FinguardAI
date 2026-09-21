"""Data quality routes for FinGuard AI."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DataQualityReport
from app.services import DataQualityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


@router.get("/")
def get_data_quality_report(
    db: Session = Depends(get_db),
) -> dict:
    """
    Data quality report.

    Runs completeness, consistency, validity, and duplicate checks
    across all main financial tables and returns a weighted overall
    quality score along with a list of identified issues.
    """
    try:
        svc = DataQualityService(db)
        report: DataQualityReport = svc.get_full_report()
        return report.model_dump()
    except Exception as exc:
        logger.exception("Data quality report failed")
        raise HTTPException(status_code=500, detail="Failed to generate data quality report") from exc
