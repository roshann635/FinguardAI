# FinGuard AI — Financial Risk Scoring Methodology

This document details the mathematical formulation, weighting rationale, threshold calibration, and action triggers used by the **FinGuard AI Risk Engine** (`app/services/risk_engine.py` and `app/ml/risk_classifier.py`).

---

## 1. Overview & Objectives

The FinGuard Risk Engine synthesises complex multi-table corporate financial signals into an interpretable **Composite Financial Risk Score** on a normalized $[0, 100]$ scale.

The primary objective is early warning detection: alerting financial executives to emerging margin compression, liquidity crunches, or receivable defaults **before** they manifest as cash crises.

```
       ┌─────────────────────────────────────────────────────────┐
       │             Composite Risk Score (0–100)               │
       └───────────────────────────┬─────────────────────────────┘
                                   │
       ┌──────────────┬────────────┴───────────┬──────────────┐
       │ (30%)        │ (25%)                  │ (25%)        │ (20%)
┌──────▼──────┐┌──────▼──────┐          ┌──────▼──────┐┌──────▼──────┐
│  Liquidity  ││ Margin Decay│          │ Credit Risk ││   Anomaly   │
│ & Cash Flow ││ & Overrun   │          │ & Aging AR  ││  Density   │
└─────────────┘└─────────────┘          └─────────────┘└─────────────┘
```

---

## 2. Pillar Decomposition & Weighting

| Risk Pillar | Weight | Underlying Primary Metrics | Detection Target |
|---|---|---|---|
| **1. Liquidity & Cash Flow** | **30%** | Net monthly cash flow, outflow-to-inflow ratio, burn velocity | Operating deficits, working capital depletion |
| **2. Margin & Profitability** | **25%** | Expense-to-revenue ratio, MoM gross margin delta, budget overrun % | Structural margin erosion, uncontrolled OPEX |
| **3. Credit & Receivables** | **25%** | DSO (Days Sales Outstanding), % AR in >60 days bucket, limit utilization | Late-paying debtors, collection bottlenecks |
| **4. Anomaly Density** | **20%** | Z-score count ($|z| > 2.5$), IQR outlier volume, severity-weighted score | Operational irregularities, unbudgeted spikes |

---

## 3. Mathematical Formulation

The composite risk score $R_{\text{composite}}$ is calculated as:

$$R_{\text{composite}} = \min\left(100, \max\left(0, \sum_{i=1}^{4} w_i \cdot S_i\right)\right)$$

where $w = [0.30, 0.25, 0.25, 0.20]$ and each sub-score $S_i \in [0, 100]$.

### 3.1 Pillar 1: Liquidity Sub-Score ($S_{\text{liquidity}}$)
$$S_{\text{liquidity}} = 50 \times \left(1 - \tanh\left(\frac{\text{Net Cash Flow}}{0.25 \times \text{Monthly Revenue}}\right)\right) + 20 \times \mathbb{I}(\text{Outflow} > \text{Inflow})$$
- When net cash flow is strongly positive ($>25\%$ of revenue), $S_{\text{liquidity}} \to 0$.
- When net cash flow turns negative, $S_{\text{liquidity}} \to 70–100$.

### 3.2 Pillar 2: Margin Decay Sub-Score ($S_{\text{margin}}$)
$$S_{\text{margin}} = 100 \times \sigma\left(10 \times \left(\frac{\text{OPEX}}{\text{Revenue}} - 0.70\right)\right)$$
- If operating expenses consume $>70\%$ of revenue, margin risk scales exponentially toward 100.
- Additional $+15$ penalty points are applied if quarterly budget overrun exceeds $10\%$.

### 3.3 Pillar 3: Credit Risk Sub-Score ($S_{\text{credit}}$)
$$S_{\text{credit}} = 100 \times \left(0.50 \cdot \frac{\text{AR}_{>60\text{d}}}{\text{Total AR}} + 0.30 \cdot \frac{\text{AR}_{>90\text{d}}}{\text{Total AR}} + 0.20 \cdot \text{LimitUtilization}_{\text{SMB}}\right)$$
- Overdue receivables older than 60 and 90 days heavily penalize the score.
- SMB segment over-utilization ($>100\%$ of credit limit) contributes directly to exposure.

### 3.4 Pillar 4: Anomaly Density Sub-Score ($S_{\text{anomaly}}$)
$$S_{\text{anomaly}} = \min\left(100, 15 \times N_{\text{high}} + 8 \times N_{\text{medium}} + 3 \times N_{\text{low}}\right)$$
- Weighted sum of statistical outliers detected by the IQR and Z-Score engines within the analysis window.

---

## 4. Threshold Calibration & Classification Bands

| Score Range | Risk Tier | Executive Meaning | Automated System Action |
|---|---|---|---|
| **0 – 39** | `LOW` (🟢) | Healthy financial profile. Key indicators within normal operating boundaries. | Standard monitoring. No escalations. |
| **40 – 69** | `MEDIUM` (🟡) | Emerging headwind. Margin compression or receivable aging observed. | Flags Opportunity & Action recommendations in Executive Dashboard. |
| **70 – 100** | `HIGH` (🔴) | Critical financial risk. Liquidity pressure, heavy overdue debt, or massive expense surge. | Immediate escalation: Alert banner, prioritized Action items, executive briefing trigger. |

---

## 5. Machine Learning Extension: Gradient-Boosted Risk Classifier

In addition to deterministic rules, FinGuard provides an ML classifier (`app/ml/risk_classifier.py`) trained using XGBoost / Random Forest on engineered features:
- `dso_days`: Rolling Days Sales Outstanding
- `expense_growth_mom`: Month-over-month OPEX growth velocity
- `margin_decay_qoq`: Quarter-over-quarter gross margin erosion
- `cash_burn_ratio`: Monthly cash outflow divided by average balance
- `concentration_ratio`: Share of top 3 customers in outstanding receivables

The model provides **SHAP-inspired feature attribution** so executives understand exactly *why* a particular risk level was assigned.
