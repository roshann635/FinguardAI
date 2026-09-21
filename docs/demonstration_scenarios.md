# FinGuard AI — Demonstration Scenarios Guide

This guide maps each of the **8 synthetic financial scenarios** embedded in the dataset (Jan 2023 – Mar 2025) to its exact verified metrics, UI navigation path, and recommended question to ask FinGuard AI.

---

## Scenario Summary Matrix

| Scenario | Theme | Timeframe | Primary Metric / Effect | UI Location |
|---|---|---|---|---|
| **A** | Strong YoY Revenue Growth | 2023 vs 2024 | $+19.3\%$ revenue expansion ($17.4M $\to$ $20.7M) | Overview $\to$ Revenue Trend |
| **B** | Margin Compression | Q3 2024 | Expense growth outpaced revenue; margin fell to 91.8% | Overview $\to$ Profitability |
| **C** | Hardware/Electronics Margin Decay | H2 2024 | COGS rose $+25\%$, compressing Electronics gross profit | Financial Performance $\to$ Margin |
| **D** | Receivables Aging Surge | Late 2024 / Q1 2025 | $84.5\%$ of unpaid AR concentrated in $>90$ days bucket | Risk Intelligence $\to$ Aging AR |
| **E** | Software/SaaS Expansion | 2024 Full Year | SaaS maintained highest gross margin ($>85\%$) | Performance $\to$ Categories |
| **F** | Operations Expense Spike | Oct 2024 | Operations spend jumped $1.99\times$ normal ($39.3K vs $19.7K) | Risk Intelligence $\to$ Anomalies |
| **G** | Revenue Seasonality | Annual Cycle | Q4 peak ($96.3$–$135\%$ index) vs Q1 post-holiday dip | Forecasts $\to$ Seasonal Breakdown |
| **H** | Budget Overruns | Q3–Q4 2024 | Marketing & Operations exceeded allocations by $+5.0\%$ | Financial Performance $\to$ Budget |

---

## Detailed Walkthrough & AI Prompts

### Scenario A: Revenue Growth (+19.3% YoY in 2024)
- **Where to look:** Executive Dashboard (`/overview`) $\to$ Revenue KPI Card.
- **Evidence:** FY 2023 Revenue: **$17,396,825.00** $\to$ FY 2024 Revenue: **$20,747,675.00** ($+19.3\%$).
- **Ask FinGuard AI:**
  > *"How did revenue perform in 2024 compared to 2023?"*
- **Expected AI Response:** Notes $+19.3\%$ growth, mentions strong contribution from Electronics and Professional Services, cites verified figures.

---

### Scenario B: Margin Compression in Q3 2024
- **Where to look:** Executive Dashboard (`/overview`) $\to$ Investigation Mode $\to$ Select "Margin Compression".
- **Evidence:** In Q3 2024 (July–September), monthly expenses rose from ~$105K to ~$160K, raising the expense-to-revenue ratio and compressing net operating margins.
- **Ask FinGuard AI:**
  > *"Why did profit margins compress in Q3 2024?"*
- **Expected AI Response:** Points to higher operational disbursements in July ($160K) and elevated departmental costs before holiday sales rebounded in Q4.

---

### Scenario C: Electronics Margin Erosion (H2 2024)
- **Where to look:** Financial Performance (`/financial-performance`) $\to$ Category Margin Breakdown.
- **Evidence:** Component unit costs for Electronics increased by $25\%$ starting July 2024, lowering gross margin relative to SaaS.
- **Ask FinGuard AI:**
  > *"Which product categories experienced gross margin pressure in late 2024?"*
- **Expected AI Response:** Identifies Electronics as the primary driver of margin erosion due to increased unit costs.

---

### Scenario D: Receivables Aging & Credit Risk Surge
- **Where to look:** Risk Intelligence (`/risk-intelligence`) $\to$ Receivables Aging Schedule.
- **Evidence:** Total open receivables as of 31 Mar 2025: **$3,072,765.00**. Over **$2.59M (84.5%)** is in the 90+ days overdue bucket, with top exposure in accounts like Client 010 Corp ($116K) and Client 017 Corp ($108K).
- **Ask FinGuard AI:**
  > *"What is our accounts receivable exposure and which accounts are most critical?"*
- **Expected AI Response:** Identifies $3.07M total AR, highlights $2.59M in $>90$ days overdue, and cites top overdue debtors (Client 010 Corp, Client 017 Corp).

---

### Scenario E: Software/SaaS Outperformance
- **Where to look:** Financial Performance (`/financial-performance`) $\to$ Revenue by Category.
- **Evidence:** Software/SaaS generated $4,215,995.00 with high gross margins and stable recurring billing.
- **Ask FinGuard AI:**
  > *"How did our Software/SaaS business line perform compared to hardware?"*
- **Expected AI Response:** Notes superior gross margin profile of SaaS and lower volatility relative to physical hardware.

---

### Scenario F: October 2024 Operations Expense Spike
- **Where to look:** Risk Intelligence (`/risk-intelligence`) $\to$ Statistical Anomalies table.
- **Evidence:** Two massive expense outliers on 2024-10-16 ($9,058.11, $3.67\times$ fence) and 2024-10-19 ($11,081.47, $4.56\times$ fence). Operations monthly spend jumped to $39,328.88 vs historical average of $19,721.52.
- **Ask FinGuard AI:**
  > *"Were there any major expense anomalies detected in October 2024?"*
- **Expected AI Response:** Explicitly highlights the two Operations department disbursements exceeding $9K and $11K, noting statistical deviation without ungrounded accusations.

---

### Scenario G: Revenue Seasonality
- **Where to look:** Forecasts (`/forecasts`) $\to$ Historical Trend & Holt-Winters Prediction.
- **Evidence:** Q4 peaks at ~$2.1M–$2.3M/month, followed by Q1 seasonal trough at ~$1.2M–$1.3M/month.
- **Ask FinGuard AI:**
  > *"What seasonal patterns exist in our revenue data?"*
- **Expected AI Response:** Highlights Q4 holiday procurement surge and Q1 drop, linking it to the seasonal component of the Holt-Winters forecast.

---

### Scenario H: Budget Overruns in Marketing & Operations
- **Where to look:** Financial Performance (`/financial-performance`) $\to$ Budget Variance.
- **Evidence:** FY 2024 realized spend reached **$4,620,000.00** against a **$4,400,000.00** budget ($+5.0\%$ overrun, $+\$220K$).
- **Ask FinGuard AI:**
  > *"Did any departments exceed their budget in fiscal year 2024?"*
- **Expected AI Response:** Notes the $\$220K$ overall overrun in FY 2024, specifically citing Marketing and Operations in Q3/Q4.
