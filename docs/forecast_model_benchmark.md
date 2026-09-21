# Forecast Model Benchmark Evaluation

Evaluation performed on out-of-sample holdout (October 2024 – March 2025, 6 months) against the synthetic historical dataset.

| Model | MAE ($) | RMSE ($) | MAPE (%) | Directional Accuracy (%) | Operational Status |
|---|---|---|---|---|---|
| **Naive (Persistence)** | $434,661.67 | $476,175.76 | 23.91% | 0.0% | `Baseline` |
| **ARIMA (1,1,1)** | $436,441.69 | $465,305.01 | 24.57% | 50.0% | `Challenger Model` |
| **3-Month Moving Average** | $434,661.67 | $441,505.02 | 26.96% | 16.7% | `Baseline` |
| **Holt-Winters Exp Smoothing** | $447,878.59 | $464,507.47 | 28.35% | 66.7% | `Production Champion` |
