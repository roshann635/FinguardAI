"""Revenue forecasting service using Holt-Winters Exponential Smoothing."""

import logging
import math
from datetime import date, datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.model_selection import TimeSeriesSplit

from app.models import Transaction
from app.schemas.forecast import ForecastPoint, ForecastResult
from app.utils.formatters import safe_divide
from app.utils.date_utils import get_as_of_date

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "This forecast is a statistical estimate based on historical patterns. "
    "It does not account for market disruptions, strategic changes, or external events. "
    "Use as one input among many in your planning process."
)
_METHOD = "Holt-Winters Exponential Smoothing (additive trend, additive seasonality)"


class RevenueForecastService:
    """Generate revenue forecasts from completed-sale transaction history."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_monthly_revenue_series(self, months_history: int = 24) -> pd.Series:
        """Return a monthly-frequency pd.Series of net revenue (last *months_history* months)."""
        try:
            cutoff = get_as_of_date().replace(day=1) - timedelta(days=1)
            start = (cutoff.replace(day=1) - timedelta(days=(months_history - 1) * 30)).replace(day=1)

            if self.db.bind and self.db.bind.dialect.name == "sqlite":
                period_expr = func.strftime("%Y-%m-01", Transaction.transaction_date)
            else:
                period_expr = func.date_trunc("month", Transaction.transaction_date)

            rows = (
                self.db.query(
                    period_expr.label("month"),
                    func.sum(
                        Transaction.amount * (1 - Transaction.discount_pct / 100)
                    ).label("revenue"),
                )
                .filter(
                    Transaction.transaction_type == "sale",
                    Transaction.status == "completed",
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= cutoff,
                )
                .group_by(period_expr)
                .order_by(period_expr)
                .all()
            )

            if not rows:
                return pd.Series(dtype=float)

            index = pd.DatetimeIndex([r.month for r in rows], freq=None)
            values = [float(r.revenue or 0) for r in rows]
            series = pd.Series(values, index=index)
            series.index = pd.DatetimeIndex(series.index).to_period("M").to_timestamp("M")
            series = series.asfreq("MS")
            return series
        except Exception:
            logger.exception("_get_monthly_revenue_series failed")
            return pd.Series(dtype=float)


    # ------------------------------------------------------------------
    # Model evaluation
    # ------------------------------------------------------------------

    def _evaluate_model(self, series: pd.Series) -> dict:
        """Chronological cross-validation (TimeSeriesSplit, n_splits=3)."""
        tscv = TimeSeriesSplit(n_splits=3)
        maes, rmses, mapes = [], [], []

        for train_idx, test_idx in tscv.split(series):
            train = series.iloc[train_idx]
            test = series.iloc[test_idx]
            if len(train) < 4:
                continue
            try:
                seasonal_periods = 12 if len(train) >= 24 else min(len(train) // 2, 6)
                model = ExponentialSmoothing(
                    train,
                    trend="add",
                    seasonal="add" if seasonal_periods >= 2 else None,
                    seasonal_periods=seasonal_periods if seasonal_periods >= 2 else None,
                    initialization_method="estimated",
                )
                fit = model.fit(optimized=True)
                pred = fit.forecast(len(test))

                actuals = test.values
                predicted = pred.values
                mae = float(np.mean(np.abs(actuals - predicted)))
                rmse = float(np.sqrt(np.mean((actuals - predicted) ** 2)))
                nonzero = actuals != 0
                mape = float(np.mean(np.abs((actuals[nonzero] - predicted[nonzero]) / actuals[nonzero])) * 100) if nonzero.any() else 0.0
                maes.append(mae)
                rmses.append(rmse)
                mapes.append(mape)
            except Exception:
                logger.debug("CV fold skipped due to fitting error", exc_info=True)

        return {
            "mae": float(np.mean(maes)) if maes else 0.0,
            "rmse": float(np.mean(rmses)) if rmses else 0.0,
            "mape": float(np.mean(mapes)) if mapes else 0.0,
        }

    # ------------------------------------------------------------------
    # Forecast generation
    # ------------------------------------------------------------------

    def generate_forecast(self, horizon_days: int = 90) -> ForecastResult:
        """Generate a revenue forecast for the requested horizon."""
        generated_at = datetime.utcnow().isoformat() + "Z"
        series = self._get_monthly_revenue_series(months_history=24)

        if len(series) < 12:
            logger.warning("Insufficient data for forecast: %d months available", len(series))
            return ForecastResult(
                horizon_days=horizon_days,
                method=_METHOD,
                mae=0.0,
                rmse=0.0,
                mape=None,
                points=[],
                disclaimer=(
                    "Insufficient historical data to generate a reliable forecast. "
                    "At least 12 months of revenue data are required."
                ),
                generated_at=generated_at,
            )

        metrics = self._evaluate_model(series)
        horizon_months = math.ceil(horizon_days / 30)

        try:
            seasonal_periods = 12 if len(series) >= 24 else 6
            final_model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
            fit = final_model.fit(optimized=True)
            forecast_values = fit.forecast(horizon_months)

            residuals = fit.resid
            residual_std = float(residuals.std()) if len(residuals) > 1 else 0.0
            ci_half = 1.96 * residual_std
        except Exception:
            logger.exception("Final model fitting failed")
            forecast_values = pd.Series(dtype=float)
            ci_half = 0.0

        points: List[ForecastPoint] = []

        # Historical actuals
        for ts, val in series.items():
            points.append(
                ForecastPoint(
                    date=ts.strftime("%Y-%m-%d"),
                    forecast=round(float(val), 2),
                    lower_bound=round(float(val), 2),
                    upper_bound=round(float(val), 2),
                    is_actual=True,
                )
            )

        # Future forecast points
        for ts, val in forecast_values.items():
            fval = max(0.0, float(val))
            points.append(
                ForecastPoint(
                    date=ts.strftime("%Y-%m-%d"),
                    forecast=round(fval, 2),
                    lower_bound=round(max(0.0, fval - ci_half), 2),
                    upper_bound=round(fval + ci_half, 2),
                    is_actual=False,
                )
            )

        return ForecastResult(
            horizon_days=horizon_days,
            method=_METHOD,
            mae=round(metrics["mae"], 2),
            rmse=round(metrics["rmse"], 2),
            mape=round(metrics["mape"], 2) if metrics["mape"] else None,
            points=points,
            disclaimer=_DISCLAIMER,
            generated_at=generated_at,
        )
