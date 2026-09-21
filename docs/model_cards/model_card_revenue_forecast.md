# Model Card: Revenue Forecasting Engine

## Model Details
- **Model Name:** FinGuard Revenue Forecasting Engine
- **Model Types:** Holt-Winters Additive Exponential Smoothing (Primary Champion) & SARIMAX (Challenger)
- **Version:** 1.0.0
- **Implementation:** `app/ml/forecasting.py`, `statsmodels.tsa.holtwinters.ExponentialSmoothing`
- **Trained / Evaluated on:** Jan 2023 – Mar 2025 Synthetic Financial Dataset (27 months)

## Intended Use
- **Primary Use:** Predicting multi-period forward gross revenue trajectories (30 to 90 days / monthly horizons) for budget planning and cash runway estimation.
- **Intended Users:** CFOs, financial planning and analysis (FP&A) teams, executive decision-makers.
- **Out of Scope:** Intraday or real-time tick forecasting, algorithmic trading, external stock market price prediction.

## Training & Methodology
- **Input Data:** Completed sales transaction volume aggregated at daily and monthly intervals.
- **Components:**
  - Trend: Additive linear growth capturing annual enterprise sales expansion.
  - Seasonality: Additive 4-quarter seasonality modeling Q4 spikes and Q1 procurement lulls.
- **Parameter Optimization:** Automated grid search over damping factors and smoothing parameters ($\alpha, \beta, \gamma$).

## Evaluation & Performance (Out-of-Sample Holdout)
Evaluated on holdout window (October 2024 – March 2025):
- **Mean Absolute Error (MAE):** $447,878.59
- **Root Mean Squared Error (RMSE):** $464,507.47
- **Mean Absolute Percentage Error (MAPE):** 28.35%
- **Directional Accuracy:** **66.7%** (significantly outperforms Naive baseline of 0.0%)

## Ethical Considerations & Responsible AI
- Forecasts are statistical estimates, not guarantees.
- Predictions always include 80% and 95% confidence intervals to convey forecast uncertainty.
- UI and AI assistant always include disclaimer: *"Statistical forecast based on historical trends. Subject to market variability."*
