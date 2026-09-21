# Model Card: Accounts Receivable & Credit Risk Scoring

## Model Details
- **Model Name:** FinGuard Credit & Receivables Risk Engine
- **Model Types:** Rule-based aging schedule synthesis & Gradient Boosted Decision Tree (XGBoost)
- **Version:** 1.0.0
- **Implementation:** `app/services/risk_engine.py`, `app/ml/risk_classifier.py`
- **Target Variable:** Account Delinquency Risk (`LOW`, `MEDIUM`, `HIGH`)

## Intended Use
- **Primary Use:** Evaluating customer payment timeliness, overdue invoice aging, credit line exposure, and prioritization of collection efforts.
- **Intended Users:** Credit analysts, accounts receivable managers, CFOs.
- **Out of Scope:** Individual consumer credit reporting (strictly B2B commercial accounts).

## Features & Indicators
1. **DSO & Aging Velocity:** Days sales outstanding, percentage of total outstanding debt exceeding 60 and 90 days.
2. **Limit Utilization:** Current total balance relative to contractual credit limit by segment (Enterprise, Mid-Market, SMB).
3. **Historical Payment Delay:** Days between due date and actual settlement date across past settled invoices.
4. **Concentration Risk:** Exposure percentage of top 5 debtor accounts.

## Evaluation on Seed Dataset
- Total Invoices: 1,809
- Open Invoices: 343 ($3,072,765.00)
- Accurately captures overdue concentration in late 2024 invoices (Scenario D).
- Highlights over-utilized SMB accounts (utilization $>100\%$) for immediate credit hold actions.

## Governance & Action Linking
- Automatically links high credit risk accounts into the **Action Center**:
  - `Action: Implement immediate credit holds on accounts >60 days overdue`
  - `Action: Re-evaluate credit terms for top overdue clients (e.g. Client 010 Corp)`
