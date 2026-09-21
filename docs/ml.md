# ML Pipeline

FinGuard AI uses three distinct ML/statistical models: a Holt-Winters forecaster for revenue, an XGBoost classifier for financial risk scoring, and IQR/z-score methods for anomaly detection. All models are implemented in `backend/app/ml/`.

---

## 1. Revenue Forecasting

**Implementation:** [`RevenueForecastService`](../backend/app/ml/forecasting.py)

### Method

**Holt-Winters Exponential Smoothing** with additive trend and additive seasonality.

```python
ExponentialSmoothing(
    series,
    trend="add",
    seasonal="add",
    seasonal_periods=12,   # 12 when ≥ 24 months of data, else 6
    initialization_method="estimated",
)
```

Model parameters are optimised automatically (`fit(optimized=True)`) via maximum likelihood estimation.

### Why Holt-Winters Was Chosen

- Handles both trend and seasonality transparently without black-box neural networks
- Parameters (level, trend, season smoothing factors) are directly interpretable
- Performs robustly on short time series (12–24 months) where deep models underfit
- Produces natural confidence intervals from residual standard deviation

### Validation

**TimeSeriesSplit cross-validation** — strictly chronological, no random shuffling.

```python
TimeSeriesSplit(n_splits=3)
```

Each fold trains on earlier data and tests on the immediately following held-out window. This mimics the real-world forecasting scenario where future data is unavailable.

### Evaluation Metrics

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| MAE | `mean(|actual − predicted|)` | Average absolute error in currency units |
| RMSE | `sqrt(mean((actual − predicted)²))` | Penalises large errors more than MAE |
| MAPE | `mean(|actual − predicted| / actual) × 100` | Percentage error; `None` if actuals contain zeros |

Metrics are averaged across all CV folds and returned with every `ForecastResult`.

### Confidence Intervals

```
lower_bound = max(0, forecast − 1.96 × residual_std)
upper_bound = forecast + 1.96 × residual_std
```

`residual_std` is the standard deviation of in-sample residuals from the final fitted model. This corresponds approximately to a 95% confidence interval under the normality assumption.

Historical data points have `lower_bound == upper_bound == actual` (no interval on actuals).

### Minimum Data Requirement

**12 months** of completed-sale revenue data is required. If fewer than 12 monthly data points are available, the service returns a `ForecastResult` with `points = []` and an explanatory disclaimer — no model is fitted.

### Limitations

- Assumes that historical patterns (trend and seasonality) persist into the future
- Sensitive to structural breaks: acquisitions, product launches, major market shifts
- Does not incorporate external macroeconomic signals
- Seasonal decomposition uses a fixed period; irregular seasonality is not handled
- Always accompanied by disclaimer: *"This forecast is a statistical estimate based on historical patterns. It does not account for market disruptions, strategic changes, or external events."*

---

## 2. Financial Risk Classification

**Implementation:** [`FinancialRiskClassifier`](../backend/app/ml/risk_classifier.py)

### Method

**XGBoostClassifier** with **StratifiedKFold (k=5)** cross-validation.

```python
XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
              use_label_encoder=False, eval_metric="mlogloss")
```

### Risk Classes

| Label | Integer | Meaning |
|-------|---------|---------|
| LOW | 0 | No significant financial risk signals |
| MEDIUM | 1 | One or more warning-level indicators present |
| HIGH | 2 | Multiple or severe risk indicators present |

### Features (10 total)

Features are extracted per calendar month by [`_extract_features_for_month()`](../backend/app/ml/risk_classifier.py). The feature vector must always be in this exact column order:

| # | Feature Key | Human-Readable Name | Formula |
|---|-------------|---------------------|---------|
| 1 | `revenue_growth_3m` | Revenue Growth Trend | `(rev_curr − rev_3m_ago) / rev_3m_ago × 100` |
| 2 | `expense_growth_3m` | Expense Growth Rate | `(exp_curr − exp_3m_ago) / exp_3m_ago × 100` |
| 3 | `gross_margin` | Gross Margin Level | `gross_profit / revenue × 100` |
| 4 | `margin_change_3m` | Margin Compression | `gross_margin_curr − gross_margin_3m_ago` (percentage points) |
| 5 | `net_margin` | Net Margin Level | `net_profit / revenue × 100` |
| 6 | `cash_flow_ratio` | Cash Flow Health | `net_cash_flow / revenue × 100` |
| 7 | `expense_revenue_ratio` | Expense-to-Revenue Ratio | `total_expenses / revenue × 100` |
| 8 | `receivables_aging_score` | Receivables Aging | Weighted bucket score 0–100: `(b31×25 + b61×50 + b90×100) / total_ar` — capped at 100 |
| 9 | `budget_overrun_score` | Budget Overrun Level | Max `variance_pct` across overspending areas, or 0 if none |
| 10 | `revenue_volatility` | Revenue Stability | Standard deviation of monthly revenue over the last 6 months, normalised by mean |

All missing values are filled with `0.0` before inference.

### Label Generation

Labels are **deterministic and rule-based** — not from expert annotation of real business data. For each month in the training window, a label is assigned by evaluating feature thresholds:

- **HIGH** if: `revenue_growth_3m < −10` OR `gross_margin < 10` OR `net_margin < 0` OR `cash_flow_ratio < −5` OR `receivables_aging_score > 60` OR `budget_overrun_score > 30`
- **MEDIUM** if: `revenue_growth_3m < 0` OR `gross_margin < 20` OR `cash_flow_ratio < 5` OR `receivables_aging_score > 30` OR `budget_overrun_score > 15` OR `expense_growth_3m > 15`
- **LOW** otherwise

This means the XGBoost model is learning to replicate these rules — it adds value through non-linear feature interaction, not through a richer ground truth.

### Evaluation Metrics

For each of the 3 classes (LOW, MEDIUM, HIGH):

- **Precision** — `TP / (TP + FP)`
- **Recall** — `TP / (TP + FN)`
- **F1 Score** — `2 × Precision × Recall / (Precision + Recall)`
- **AUC-ROC** — one-vs-rest, macro-averaged

Returned as part of the training metrics dict when `classifier.train()` is called.

### Fallback: Rule-Based Classifier

When the serialised model artifact (`ml/artifacts/risk_classifier.pkl`) is not present, or when insufficient monthly data exists, the system falls back to [`_rule_based_risk()`](../backend/app/ml/risk_classifier.py). This applies the same threshold rules used for label generation directly against the current feature vector, returning a deterministic `(label, confidence)` tuple.

The fallback ensures the `/risk/overview` endpoint always returns a valid `RiskScore` response regardless of model availability.

### Limitations

- Trained on synthetic, rule-derived labels — not validated against real labelled financial outcomes
- The model cannot generalise beyond the patterns in the synthetic training distribution
- Training data is the same company's own historical data, so the model may overfit to company-specific patterns
- Requires a minimum of 6 months of data to extract meaningful features; fewer months result in the rule-based fallback

---

## 3. Anomaly Detection

**Implementation:** [`AnomalyDetectionService`](../backend/app/ml/anomaly_detection.py)

Two separate detectors are used, each scoped **per category** to avoid cross-category contamination.

### 3.1 Expense Anomalies — IQR Method

```
Q1   = 25th percentile of amounts within category
Q3   = 75th percentile of amounts within category
IQR  = Q3 − Q1
upper_fence = Q3 + 1.5 × IQR
lower_fence = max(0, Q1 − 1.5 × IQR)
```

An expense record is flagged if `amount > upper_fence`. Records in categories with `IQR == 0` (all values identical) are skipped.

**Anomaly score:** `(amount − Q3) / IQR` — measures how far above the upper quartile the amount sits in IQR units.

### 3.2 Transaction Anomalies — Z-Score Method

```
mean = average(amounts) within category
std  = standard deviation(amounts) within category
z    = (amount − mean) / std
```

A transaction is flagged if `|z| > 2.5`. Categories with fewer than 3 records or `std == 0` are skipped.

**Anomaly score:** `|z|`

**Net amount used:** `amount × (1 − discount_pct / 100)` — same definition as Revenue in KPIs.

### 3.3 Severity Mapping

Both detectors use the same score-to-severity mapping:

| Anomaly Score | Severity |
|--------------|----------|
| `> 3.0` | `high` |
| `1.5 ≤ score ≤ 3.0` | `medium` |
| `< 1.5` | `low` |

`requires_investigation` is set to `True` for `medium` and `high` records.

### 3.4 Language Requirements

There are no validated fraud labels in the dataset. The system must never characterise any anomaly as confirmed fraud. Correct terminology:

- ✅ `"potential anomaly detected"`
- ✅ `"requires investigation"`
- ✅ `"Amount significantly exceeds expected range for [category]"`
- ❌ `"fraud"`, `"confirmed irregular"`, `"definitely suspicious"`

The `reason` field on every `AnomalyRecord` is generated as: *"Amount of {amount} significantly exceeds the expected range of {low}–{high} for {category}".*

### 3.5 Limitations

- Univariate detection only — no multivariate or time-series correlation
- Per-category grouping requires sufficient observations per category; small categories produce few or no flags
- IQR threshold (`1.5×IQR`) is standard but configurable in principle — lower values increase sensitivity; higher values reduce false positives
- Default lookback window is 12 months; shorter windows reduce baseline stability

---

## 4. Model Explainability

### Risk Classifier

XGBoost's `.feature_importances_` (gain-based) are extracted after training and mapped to human-readable names via [`_FEATURE_NAMES`](../backend/app/ml/risk_classifier.py):

```python
_FEATURE_NAMES = {
    "revenue_growth_3m":    "Revenue Growth Trend",
    "expense_growth_3m":    "Expense Growth Rate",
    "gross_margin":         "Gross Margin Level",
    "margin_change_3m":     "Margin Compression",
    "net_margin":           "Net Margin Level",
    "cash_flow_ratio":      "Cash Flow Health",
    "expense_revenue_ratio":"Expense-to-Revenue Ratio",
    "receivables_aging_score":"Receivables Aging",
    "budget_overrun_score": "Budget Overrun Level",
    "revenue_volatility":   "Revenue Stability",
}
```

Each `RiskIndicator` in the `RiskScore` response includes:
- `feature` — the human-readable name
- `value` — the actual metric value for the current period
- `threshold` — the threshold that this indicator is compared against
- `evidence` — a plain-language string: *"Gross margin is 8.3% (threshold: 10%)"*
- `contributing` — whether this indicator is currently breaching its threshold

### Anomaly Records

Each `AnomalyRecord` includes:
- `expected_range_low` / `expected_range_high` — the statistical normal range for the category
- `amount` — the actual flagged amount
- `anomaly_score` — quantitative distance from the upper fence or mean
- `severity` — mapped severity label
- `reason` — human-readable explanation string
- `requires_investigation` — boolean flag for UI/action routing
