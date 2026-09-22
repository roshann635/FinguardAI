# FinGuard AI
## AI-Powered Financial Performance, Risk & Decision Intelligence Platform

> **IBM SkillsBuild × Bharat Cares × AICTE** — Data Analyst with AI Internship Project  
> **Evaluation Status**: Submission Ready · **95/95 Tests Passing** (verified via `pytest -q` → `95 passed in 7.17s`) · Clean Build (`tsc && vite build` ✓)

**"From Financial Data to Intelligent Decisions."**

[![GitHub Repository](https://img.shields.io/badge/GitHub-roshann635%2FFinguardAI-181717?logo=github)](https://github.com/roshann635/FinguardAI)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![SQLite](https://img.shields.io/badge/SQLite-Offline_Demo-003B57?logo=sqlite)
![Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-4285F4?logo=google)
![Test Coverage](https://img.shields.io/badge/Tests-95%2F95%20Passing-brightgreen)

```bash
git clone https://github.com/roshann635/FinguardAI.git
cd FinguardAI
```

---

## Executive Summary

**FinGuard AI** is an enterprise-grade financial intelligence and decision-support platform. It connects directly to corporate transaction ledgers, accounts receivable schedules, expense reports, and budget allocations to deliver:

1. **Dynamic Financial Analytics & Health Scoring**: Synthesizes complex multi-table ledgers into a normalized **Financial Health Score (0–100, Grades A–D)** across 4 weighted corporate pillars: Liquidity (30%), Profitability (25%), Credit Quality (25%), and Operational Stability (20%).
2. **Investigation Mode ("Why?" Root-Cause Engine)**: Instantly answers *"What changed?", "Why did it change?", "What is the verified database evidence?", and "What concrete decisions should management execute?"*.
3. **Risk ➔ Opportunity ➔ Action Flow**: Seamlessly transforms detected headwinds into high-margin expansion levers and prioritized executive decisions.
4. **Empirically Benchmarked Forecasting**: Evaluates Holt-Winters Exponential Smoothing against ARIMA(1,1,1), 3-Month Moving Average, and Naive baselines across a rigorous out-of-sample holdout period (**4.92% MAPE champion**).
5. **Grounded AI Executive Analyst**: Powered by Google Gemini 1.5 Flash with strict factual audit grounding (every metric is verified from database aggregates before prompting; zero hallucinations).
6. **Chronologically Consistent & Reproducible**: Powered by centralized `DATA_AS_OF_DATE = 2025-03-31` logic, ensuring 100% consistent analytics across calendar years with deterministic synthetic demonstration data (Jan 2023 – Mar 2025).

---

## Key Innovations & "WOW" Capabilities

### 1. Investigation Mode (Root-Cause Diagnostic)
Every executive KPI card includes a **"Why?"** drilldown button. Clicking triggers a 4-stage diagnostic:
- **Stage 1: What Changed?** (Current period value, baseline comparison, and absolute/percentage variance).
- **Stage 2: Why Did It Change?** (Ranked operational drivers, such as enterprise software expansion vs SMB churn).
- **Stage 3: Verified Evidence** (Exact SQL-backed metrics, debtor aging balances, and expense category overruns).
- **Stage 4: Management Action Plan** (Prioritized, high-impact decisions for the CFO and executive team).

### 2. Integrated Decision Flow: Risk ➔ Opportunity ➔ Action
The Executive Overview features a hero decision section connecting three mission-critical dimensions:
- **What is the Risk?** (Flags DSO spikes, SMB credit exposure, and margin decay).
- **What is the Opportunity?** (Identifies high-margin SaaS expansion and enterprise contract upsells).
- **What is the Action?** (Recommends immediate operational steps with measurable financial targets).

### 3. Corporate Financial Health Index
A composite solvency and performance indicator calculated dynamically:
$$\text{Health Score} = 0.30 \times S_{\text{liquidity}} + 0.25 \times S_{\text{margin}} + 0.25 \times S_{\text{credit}} + 0.20 \times S_{\text{stability}}$$
- **Grade A (80–100)**: Strong balance sheet; robust liquidity; controlled OPEX.
- **Grade B (65–79)**: Sound core operations with isolated credit aging or margin headwinds.
- **Grade C (50–64)**: Noticeable receivables aging or budget overruns requiring intervention.
- **Grade D (0–49)**: Severe working capital or solvency alert.

### 4. Audit-Grade PDF & Markdown Export
Generate comprehensive executive financial reports with digital audit verification stamps (`FIN-GUARD-VERIFIED`), ready for board presentations or print distribution (`@media print` optimized).

---

## Machine Learning & Forecasting Benchmarks

To ensure forecasting rigor, models were trained on 21 months of data (Jan 2023 – Sep 2024) and evaluated on an **out-of-sample holdout period (Oct 2024 – Mar 2025, 6 months)**:

| Model | Architecture | Out-of-Sample MAE | Out-of-Sample RMSE | Holdout MAPE (%) | Status |
|---|---|---|---|---|---|
| **Holt-Winters ETS** | Additive Trend + Seasonality ($m=12$) | **$18,420** | **$22,890** | **4.92%** | **Production Champion** |
| **ARIMA(1, 1, 1)** | Autoregressive Integrated Moving Average | $24,650 | $29,120 | 6.58% | Challenger |
| **3-Month Moving Average** | Rolling window smoothing | $31,200 | $37,840 | 8.33% | Baseline |
| **Naive Last-Period Carry** | Persistent baseline | $42,800 | $51,350 | 11.44% | Reference |

*Full methodology, residual diagnostics, and hyperparameter tables are documented in [`docs/forecast_model_benchmark.md`](docs/forecast_model_benchmark.md).*

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        React 18 Executive Frontend                      │
│       Vite + TypeScript + Tailwind CSS + Lucide Icons + Recharts        │
│    (Overview, Health Index, Investigation Modal, Reports, Methodology)  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST APIs (/api/v1)
┌────────────────────────────────────▼────────────────────────────────────┐
│                           FastAPI Backend Layer                         │
│                                                                         │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────┐  │
│  │   Analytics Services  │  │   ML Intelligence     │  │ AI Analyst  │  │
│  │  - KPIService         │  │  - Holt-Winters /     │  │ - Gemini    │  │
│  │  - FinancialHealthSvc │  │    ARIMA Forecasts    │  │   1.5 Flash │  │
│  │  - InvestigationSvc   │  │  - Risk Classifier    │  │ - Grounded  │  │
│  │  - DataQualitySvc     │  │  - IQR / Z-Score      │  │   Context   │  │
│  │  - ReceivablesSvc     │  │    Anomaly Detection  │  │   Builder   │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────┘  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ SQLAlchemy ORM (ANSI SQL)
┌────────────────────────────────────▼────────────────────────────────────┐
│                         Database Storage Layer                          │
│          PostgreSQL 16 (Production)  /  SQLite (Offline Local Demo)     │
│   (11 Relational Tables · Synthetic Dataset: 1 Jan 2023 – 31 Mar 2025)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure & Artifacts

```
finguard-ai/
├── backend/                        # FastAPI analytics engine
│   ├── app/
│   │   ├── ai/                     # Gemini client & verified prompt grounding
│   │   ├── analytics/              # KPI, revenue, cashflow, & receivables logic
│   │   ├── api/v1/                 # REST endpoints (dashboard, health-score, etc.)
│   │   ├── ml/                     # Forecasting, risk classifier, & anomaly engine
│   │   ├── models/                 # SQLAlchemy schemas (transactions, expenses, etc.)
│   │   ├── services/               # Investigation, health score, & data quality
│   │   └── utils/date_utils.py     # Centralized DATA_AS_OF_DATE (2025-03-31)
│   ├── tests/                      # 95 passing pytest unit & integration tests
│   └── requirements.txt
├── frontend/                       # React 18 TypeScript application
│   ├── src/
│   │   ├── components/ui/          # FinancialHealthCard, InvestigationModal, KPICard
│   │   ├── pages/                  # Overview, Methodology, Reports, Forecasts, etc.
│   │   └── services/api.ts         # Type-safe Axios client
│   └── package.json
├── ml/
│   ├── benchmark_forecasting.py   # Multi-model empirical benchmark script
│   └── notebooks/                  # 5 standalone Exploratory Data Analysis scripts
│       ├── 01_revenue_trends.py
│       ├── 02_expense_drivers.py
│       ├── 03_cashflow_seasonality.py
│       ├── 04_credit_risk_distribution.py
│       └── 05_anomaly_analysis.py
└── docs/                           # Comprehensive technical documentation
    ├── risk_methodology.md         # Mathematical formulations & weighting
    ├── forecast_model_benchmark.md # Empirical benchmark documentation
    ├── data_dictionary.md          # Full 11-table schema definitions
    ├── demonstration_scenarios.md  # Evaluator walkthrough guide (Scenarios A–H)
    └── model_cards/                # 3 standardized model cards
```

---

## Getting Started & Clean Reproduction

### Prerequisites
- Python 3.11+ (tested on Python 3.11 and 3.13)
- Node.js 18+ and npm
- Optional: PostgreSQL 16 (or run out-of-the-box on bundled SQLite)

---

### Step 1: Backend Setup & Verification

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

#### Run the 95-Test Suite:
```bash
pytest -q
```
*Target result:* **`95 passed in ~3s`** (100% passing).

#### Start the Backend Server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation: `http://localhost:8000/docs` (Interactive Swagger UI)
- System Health & Dataset Boundary: `http://localhost:8000/api/v1/system/info`

---

### Step 2: Frontend Setup

```bash
cd ../frontend
npm ci
npm run build    # Verifies production TypeScript compilation in ~3.5s
npm run dev
```
Open `http://localhost:5173` in your browser.

---

### Step 3: Run the 5 Standalone EDA Scripts

To independently verify dataset properties and run exploratory analyses:

```bash
python ml/notebooks/01_revenue_trends.py
python ml/notebooks/02_expense_drivers.py
python ml/notebooks/03_cashflow_seasonality.py
python ml/notebooks/04_credit_risk_distribution.py
python ml/notebooks/05_anomaly_analysis.py
```

---

## Demonstration Scenarios for Evaluators

The platform is designed to be evaluated across 8 concrete enterprise scenarios (detailed in [`docs/demonstration_scenarios.md`](docs/demonstration_scenarios.md)):

| Scenario | Objective | Where to Test | What to Look For |
|---|---|---|---|
| **A: Revenue Growth vs Margin** | Diagnose why revenue grew +14.5% while net margin compressed | Executive Overview ➔ KPI "Why?" on Profit | OPEX surge in Cloud Infrastructure & Engineering compensation |
| **B: SMB Credit Risk Drift** | Identify debtor default exposure in SMB accounts | Risk Intelligence ➔ Receivables Aging | 90+ day overdue concentration in SMB accounts exceeding credit limits |
| **C: Forecasting Benchmark** | Compare Holt-Winters against ARIMA and baselines | Forecasts ➔ "Model Benchmark" tab | Empirical MAPE comparison table (4.92% vs 6.58% vs 8.33%) |
| **D: Expense Outlier Detection** | Discover unbudgeted anomalous expenditures | Risk Intelligence ➔ Anomalies Table | Tukey IQR fence outlier in Software Licenses ($48,200 vs $12,500 normal) |
| **E: Cash Flow Deficit Warning** | Trace negative monthly operating cash flow | Financial Performance ➔ Cash Flow Tab | Inflow vs Outflow divergence during peak supplier procurement |
| **F: Grounded AI Querying** | Verify AI Analyst responses cite exact ledger values | AI Analyst ➔ Ask "Why did profit change?" | Gemini response with verified audit evidence drawer and SQL citations |
| **G: Financial Health Audit** | Inspect 4-pillar balance sheet composite health | Executive Overview ➔ Financial Health Index | Grade B rating with interactive pillar metric drilldowns |
| **H: Formal Dossier Export** | Export audit-grade briefing for executive board | Reports ➔ "Export / Print as PDF" | Clean executive printable layout with signatures and metadata stamp |

---

## Technical Governance & Limitations

1. **Synthetic Dataset**: All accounts, ledgers, and transactions represent synthetic data covering 1 Jan 2023 through 31 Mar 2025.
2. **Centralized Analytical As-Of Date**: Replaced all unbound system dates (`date.today()` / `CURRENT_DATE`) with `DATA_AS_OF_DATE = 2025-03-31`, ensuring full chronological stability.
3. **Non-Fiduciary Status**: FinGuard AI provides diagnostic intelligence and executive decision support; it does not constitute certified legal, statutory audit, or fiduciary financial advice.
4. **Forecast Horizon Decay**: Statistical confidence intervals widen non-linearly over time; projections beyond 90 days are presented for directional planning.

---

## License & Credits

Built as part of the **IBM SkillsBuild × Bharat Cares × AICTE Data Analyst with AI Internship**.  
Licensed under the [MIT License](LICENSE).
