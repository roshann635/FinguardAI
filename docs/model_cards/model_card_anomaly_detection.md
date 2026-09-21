# Model Card: Financial Anomaly Detection Engine

## Model Details
- **Model Name:** FinGuard Anomaly Detection Engine
- **Model Types:** Interquartile Range (IQR) with fallback dispersion & Normalized Within-Category Z-Score ($|z| > 2.5$)
- **Version:** 1.0.0
- **Implementation:** `app/ml/anomaly_detection.py`
- **Supported Entities:** Transactions (`transactions` table) and Operating Expenses (`expenses` table)

## Intended Use
- **Primary Use:** Detecting statistically extreme expense disbursements and transaction spikes that deviate substantially from departmental or category peers.
- **Intended Users:** Internal auditors, corporate controllers, department heads.
- **Out of Scope:** Fraud determination without human audit; legal compliance determination.

## Detection Algorithms
1. **Expense IQR Outlier Detection:**
   - Evaluates distributions within each expense category (e.g. Operations, IT, Marketing).
   - Flag threshold: $\text{Amount} > Q_3 + 1.5 \times \text{IQR}$.
   - Zero-spread fallback: When $\text{IQR} = 0$, falls back to sample standard deviation to ensure large outliers are never missed.
2. **Transaction Z-Score Outlier Detection:**
   - Standardizes amounts by category mean and standard deviation: $z = \frac{x - \mu}{\sigma}$.
   - Flag threshold: $|z| > 2.5$.
   - Requires minimum 3 records per category to avoid sample size artifacts.

## Ground Truth Validation (Scenario F)
- Evaluated against known synthetic injection: October 2024 Operations spend surge (~3x normal).
- **Result:** Successfully flags anomalous transactions (e.g. $11,081.47 and $9,058.11) with anomaly score $>3.5\times$ and high severity rating.

## Explainability & Safety Guardrails
- Every flagged anomaly produces human-readable statistical justification:
  `"Amount of $11,081.47 significantly exceeds the expected range of $0.00–$5,595.97 for Operations"`
- **Strict Prohibition:** FinGuard AI never uses the words *"fraud"*, *"theft"*, or *"illegal"*. An anomaly is an objective statistical outlier requiring managerial review.
