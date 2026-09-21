"""Risk, anomaly, opportunity, and action routes for FinGuard AI."""

import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml import AnomalyDetectionService, FinancialRiskClassifier
from app.schemas import ActionItem, AnomalyRecord, OpportunityItem, RiskScore
from app.services import RiskOpportunityActionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("/overview")
def get_risk_overview(
    db: Session = Depends(get_db),
) -> dict:
    """
    Risk overview.

    Returns the ML-derived risk score (with indicators) plus the
    full list of evidence-based risk signals from the analytics engine.
    """
    try:
        classifier = FinancialRiskClassifier(db)
        engine = RiskOpportunityActionEngine(db)

        risk_score: RiskScore = classifier.predict_current_risk()
        risk_indicators = engine._get_risk_indicators()

        return {
            "risk_score": risk_score.model_dump(),
            "risk_indicators": risk_indicators,
        }
    except Exception as exc:
        logger.exception("Risk overview failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve risk overview") from exc


@router.get("/anomalies/expenses")
def get_expense_anomalies(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum anomaly records to return"),
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Expense anomaly detection.

    Returns a ranked list of anomalous expense records detected via IQR
    analysis within each expense category.
    """
    try:
        svc = AnomalyDetectionService(db)
        records: List[AnomalyRecord] = svc.get_expense_anomalies(start_date, end_date, limit)
        return [r.model_dump() for r in records]
    except Exception as exc:
        logger.exception("Expense anomalies failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve expense anomalies") from exc


@router.get("/anomalies/transactions")
def get_transaction_anomalies(
    start_date: Optional[date] = Query(default=None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Inclusive end date (YYYY-MM-DD)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum anomaly records to return"),
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Transaction anomaly detection.

    Returns a ranked list of anomalous transaction records detected via
    z-score analysis within each transaction category.
    """
    try:
        svc = AnomalyDetectionService(db)
        records: List[AnomalyRecord] = svc.get_transaction_anomalies(start_date, end_date, limit)
        return [r.model_dump() for r in records]
    except Exception as exc:
        logger.exception("Transaction anomalies failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve transaction anomalies") from exc


@router.get("/anomalies/summary")
def get_anomaly_summary(
    db: Session = Depends(get_db),
) -> dict:
    """
    Anomaly summary.

    Returns aggregated anomaly counts and breakdown by severity
    across expenses and transactions.
    """
    try:
        svc = AnomalyDetectionService(db)
        return svc.get_anomaly_summary()
    except Exception as exc:
        logger.exception("Anomaly summary failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve anomaly summary") from exc


@router.get("/opportunities")
def get_opportunities(
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Opportunities.

    Returns a list of evidence-based financial opportunities derived
    from current analytics signals (growth, margin, budget, receivables).
    """
    try:
        engine = RiskOpportunityActionEngine(db)
        items: List[OpportunityItem] = engine.get_opportunities()
        return [i.model_dump() for i in items]
    except Exception as exc:
        logger.exception("Opportunities failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve opportunities") from exc


@router.get("/actions")
def get_recommended_actions(
    db: Session = Depends(get_db),
) -> List[dict]:
    """
    Recommended actions.

    Returns a prioritised list of evidence-based recommended actions
    generated only when the underlying analytics signal is present.
    """
    try:
        engine = RiskOpportunityActionEngine(db)
        items: List[ActionItem] = engine.get_recommended_actions()
        return [i.model_dump() for i in items]
    except Exception as exc:
        logger.exception("Recommended actions failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve recommended actions") from exc
