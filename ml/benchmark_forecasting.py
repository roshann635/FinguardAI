"""FinGuard AI — Forecasting Model Benchmark & Evaluation.

Compares 4 time-series forecasting approaches on historical monthly revenue (Jan 2023 – Mar 2025):
1. Naive Baseline (persistence model: y_hat_{t+h} = y_t)
2. Moving Average (3-month rolling mean)
3. Holt-Winters Exponential Smoothing (additive trend + seasonality)
4. SARIMAX / ARIMA (auto-regressive integrated moving average)

Evaluates out-of-sample accuracy across standard econometric metrics:
- MAE  (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- Directional Accuracy (% of periods where predicted change matches actual change direction)
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "ml" / "notebooks"))

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from data_loader import load_dataset


def run_forecasting_benchmark():
    print("=" * 70)
    print(" FinGuard AI — Revenue Forecasting Model Evaluation Benchmark")
    print("=" * 70)

    data = load_dataset()
    txns = data["transactions"].copy()

    sales = txns[(txns["transaction_type"] == "sale") & (txns["status"] == "completed")].copy()
    sales["month"] = sales["transaction_date"].dt.to_period("M")
    monthly = sales.groupby("month")["amount"].sum().sort_index()

    print(f"\nSeries length: {len(monthly)} months (Jan 2023 – Mar 2025)")

    # Train / Test split: Hold out last 6 months (Oct 2024 – Mar 2025) for evaluation
    train = monthly.iloc[:-6]
    test = monthly.iloc[-6:]
    h = len(test)

    print(f"Train periods: {len(train)} months ({train.index[0]} to {train.index[-1]})")
    print(f"Test periods:  {len(test)} months ({test.index[0]} to {test.index[-1]})\n")

    y_true = test.values
    y_prev_train = train.iloc[-1]

    # 1. Naive Baseline
    naive_pred = np.full(h, y_prev_train)

    # 2. Moving Average (3-period)
    ma_val = train.iloc[-3:].mean()
    ma_pred = np.full(h, ma_val)

    # 3. Holt-Winters Exponential Smoothing
    hw_model = ExponentialSmoothing(
        train.values,
        trend="add",
        seasonal="add",
        seasonal_periods=4,
        initialization_method="estimated",
    ).fit()
    hw_pred = hw_model.forecast(h)

    # 4. ARIMA(1, 1, 1)
    arima_model = ARIMA(train.values, order=(1, 1, 1)).fit()
    arima_pred = arima_model.forecast(h)

    # Metrics calculation
    models = {
        "Naive (Persistence)": naive_pred,
        "3-Month Moving Average": ma_pred,
        "Holt-Winters Exp Smoothing": hw_pred,
        "ARIMA (1,1,1)": arima_pred,
    }

    results = []
    actual_diff = np.diff(np.concatenate(([y_prev_train], y_true)))

    for name, pred in models.items():
        mae = np.mean(np.abs(y_true - pred))
        rmse = np.sqrt(np.mean((y_true - pred) ** 2))
        mape = np.mean(np.abs((y_true - pred) / y_true)) * 100
        pred_diff = np.diff(np.concatenate(([y_prev_train], pred)))
        dir_acc = np.mean(np.sign(actual_diff) == np.sign(pred_diff)) * 100

        results.append({
            "Model": name,
            "MAE ($)": mae,
            "RMSE ($)": rmse,
            "MAPE (%)": mape,
            "Directional Accuracy (%)": dir_acc,
        })

    df_res = pd.DataFrame(results).sort_values("MAPE (%)")

    print("--- Out-of-Sample Performance Comparison (Holdout: Oct 2024 – Mar 2025) ---")
    print(f"{'Model':<28} | {'MAE ($)':>12} | {'RMSE ($)':>12} | {'MAPE (%)':>10} | {'Dir Acc (%)':>12}")
    print("-" * 84)
    for _, r in df_res.iterrows():
        print(f"{r['Model']:<28} | ${r['MAE ($)']:>11,.2f} | ${r['RMSE ($)']:>11,.2f} | {r['MAPE (%)']:>9.2f}% | {r['Directional Accuracy (%)']:>11.1f}%")

    print("\n--- Month-by-Month Actual vs. Predicted (Holt-Winters) ---")
    for idx, (m, actual) in enumerate(test.items()):
        pred = hw_pred[idx]
        err_pct = ((pred - actual) / actual) * 100
        print(f"  {m}: Actual ${actual:>10,.2f} | HW Pred ${pred:>10,.2f} | Error: {err_pct:>+6.2f}%")

    # Generate Markdown Summary table for documentation
    md_content = """# Forecast Model Benchmark Evaluation

Evaluation performed on out-of-sample holdout (October 2024 – March 2025, 6 months) against the synthetic historical dataset.

| Model | MAE ($) | RMSE ($) | MAPE (%) | Directional Accuracy (%) | Operational Status |
|---|---|---|---|---|---|
"""
    for _, r in df_res.iterrows():
        status = "Production Champion" if "Holt-Winters" in r["Model"] else ("Challenger Model" if "ARIMA" in r["Model"] else "Baseline")
        md_content += f"| **{r['Model']}** | ${r['MAE ($)']:,.2f} | ${r['RMSE ($)']:,.2f} | {r['MAPE (%)']:.2f}% | {r['Directional Accuracy (%)']:.1f}% | `{status}` |\n"

    md_path = BASE_DIR / "docs" / "forecast_model_benchmark.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[Saved benchmark documentation to {md_path}]")
    print("[Forecasting Benchmark Completed Successfully]")


if __name__ == "__main__":
    run_forecasting_benchmark()
