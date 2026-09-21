# Analytics Methodology

This document describes every calculation, threshold, and rule used in the FinGuard AI analytics engine. All formulas are implemented in `backend/app/analytics/` and `backend/app/services/`.

---

## 1. KPI Formulas

All 14 canonical KPIs are computed by [`KPIService`](../backend/app/analytics/kpis.py). Safe-divide is applied wherever a denominator can be zero: `safe_divide(a, b)` returns `0.0` when `b == 0` rather than raising `ZeroDivisionError`.

| # | KPI | Formula |
|---|-----|---------|
| 1 | **Revenue** | `SUM(amount × (1 − discount_pct / 100))` — completed sales transactions only |
| 2 | **COGS** | `SUM(cost × quantity)` — completed sales transactions |
| 3 | **Gross Profit** | `Revenue − COGS` |
| 4 | **Gross Margin %** | `safe_divide(Gross Profit, Revenue) × 100` |
| 5 | **Operating Profit** | `Gross Profit − Total Expenses` |
| 6 | **Net Profit** | `Revenue − Total Expenses` |
| 7 | **Net Profit Margin %** | `safe_divide(Net Profit, Revenue) × 100` |
| 8 | **Net Cash Flow** | `SUM(inflow amounts) − SUM(outflow amounts)` from `cash_flows` table |
| 9 | **Budget Variance** | `Actual Expenses − Budget Amount` (positive = overspend) |
| 10 | **Budget Variance %** | `safe_divide(Actual − Budget, Budget) × 100` |
| 11 | **Revenue Growth %** | `safe_divide(Current Revenue − Prior Revenue, Prior Revenue) × 100` |
| 12 | **Avg Transaction Value** | `safe_divide(Revenue, COUNT of completed sale transactions)` |
| 13 | **Outstanding Receivables** | `SUM(invoice_amount − paid_amount)` for invoices with status `unpaid`, `partial`, or `overdue` |
| 14 | **Expense-to-Revenue Ratio** | `safe_divide(Total Expenses, Revenue) × 100` |

### Safe-Divide Handling

```python
def safe_divide(numerator: float, denominator: float) -> float:
    """Return 0.0 when denominator is zero to prevent ZeroDivisionError."""
    return numerator / denominator if denominator else 0.0
```

Applies to: Gross Margin %, Net Profit Margin %, Budget Variance %, Revenue Growth %, Avg Transaction Value, Expense-to-Revenue Ratio, Cash Flow Ratio (used in ML features).

---

## 2. Period Definitions

Named periods are resolved to concrete date ranges in [`KPIService._resolve_period()`](../backend/app/analytics/kpis.py) and [`_period_bounds()`](../backend/app/services/context_builder.py). Every named period returns four dates: `(curr_start, curr_end, prev_start, prev_end)` — the previous period is used to compute change/growth figures.

| Period key | `curr_start` | `curr_end` | `prev_start` | `prev_end` |
|------------|-------------|-----------|-------------|-----------|
| `last_30_days` | `today − 29 days` | `today` | `curr_start − 30 days` | `curr_start − 1 day` |
| `last_90_days` | `today − 89 days` | `today` | `curr_start − 90 days` | `curr_start − 1 day` |
| `last_12_months` *(default)* | `today − 364 days` | `today` | `curr_start − 365 days` | `curr_start − 1 day` |
| `ytd` | `Jan 1 of current year` | `today` | `Jan 1 of prior year` | same month/day of prior year |
| `last_year` | `Jan 1 of prior year` | `Dec 31 of prior year` | `Jan 1 two years ago` | `Dec 31 two years ago` |

> All periods are **inclusive** on both ends.

---

## 3. Revenue Analytics

Implemented in [`RevenueAnalyticsService`](../backend/app/analytics/revenue.py).

### Trend Granularity

| `granularity` param | SQL truncation | Notes |
|---------------------|---------------|-------|
| `monthly` *(default)* | `date_trunc('month', transaction_date)` | Used for most dashboards |
| `weekly` | `date_trunc('week', transaction_date)` | Suitable for `last_30_days` / `last_90_days` |
| `quarterly` | `date_trunc('quarter', transaction_date)` | Used for annual views |

### Category Breakdown

Revenue is grouped by `transactions.category_id`, joined to `categories.name`. Each category entry contains:
- `category` — category name string
- `value` — net revenue sum for the period
- `pct_of_total` — `safe_divide(category_value, total_revenue) × 100`

### Region Breakdown

Same methodology as category, grouped by `transactions.region_id` joined to `regions.name`.

---

## 4. Risk Indicator Thresholds

Implemented in [`RiskOpportunityActionEngine._get_risk_indicators()`](../backend/app/services/risk_engine.py). There are 7 indicators. Each fires at most one severity level per evaluation run; HIGH takes precedence over MEDIUM.

### 4.1 Revenue Growth

**Metric:** `revenue_growth_%` — `(current_revenue − prior_revenue) / prior_revenue × 100`

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `< −5%` | HIGH | Significant sustained decline threatens business viability |
| `< 0%` and `≥ −5%` | MEDIUM | Negative but recoverable; warrants monitoring |
| `≥ 0%` | No alert | Healthy or flat |

### 4.2 Gross Margin

**Metric:** `gross_margin_%` — see formula in §1

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `< 10%` | HIGH | Critically thin margin; nearly no buffer for fixed costs |
| `10% ≤ x < 20%` | MEDIUM | Below healthy range; pricing or COGS review needed |
| `≥ 20%` | No alert | Adequate operating cushion |

### 4.3 Expense Growth

**Metric:** `(curr_expenses − prev_expenses) / prev_expenses × 100` — year-over-year (last 12 months vs prior 12 months)

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `> 20%` | HIGH | Rapid cost escalation outpacing typical revenue growth |
| `10% < x ≤ 20%` | MEDIUM | Elevated but potentially justifiable; needs context |
| `≤ 10%` | No alert | Normal operating cost growth |

### 4.4 Net Cash Flow

**Metric:** `net_cash_flow` in absolute currency, and `net_cf / revenue × 100` as a ratio

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `net_cash_flow < 0` | HIGH | Burning cash; immediate liquidity concern |
| `0 ≤ cf_pct_of_revenue < 5%` | MEDIUM | Positive but dangerously thin; no buffer for shocks |
| `≥ 5% of revenue` | No alert | Adequate cash generation |

### 4.5 Receivables 90+ Days Overdue

**Metric:** `bucket_90_plus / total_outstanding × 100` from the aging summary

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `> 30%` | HIGH | Large proportion likely uncollectable; write-off risk |
| `15% < x ≤ 30%` | MEDIUM | Elevated credit risk; collections process needs attention |
| `≤ 15%` | No alert | Normal aging distribution |

### 4.6 Budget Overrun

**Metric:** `max(variance_pct)` across all overspending category/department pairs for the current year

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `> 25%` | HIGH | Significant uncontrolled spending in at least one area |
| `10% < x ≤ 25%` | MEDIUM | Moderate overrun; management attention required |
| `≤ 10%` | No alert | Within acceptable tolerance |

### 4.7 High-Severity Anomalies

**Metric:** `count of anomaly records with severity == "high"` in the current period

| Condition | Severity | Rationale |
|-----------|----------|-----------|
| `> 5` | HIGH | Pattern of high-severity anomalies suggests systemic issue or data quality problem |
| `≤ 5` | No alert | Isolated anomalies are within normal tolerance |

---

## 5. Opportunity Detection Logic

Implemented in [`RiskOpportunityActionEngine.get_opportunities()`](../backend/app/services/risk_engine.py). Returns up to 6 opportunities.

| Opportunity Type | Trigger Condition | Evidence Used |
|-----------------|------------------|---------------|
| **High-growth, high-margin category** | Category gross margin > average AND overall revenue growth > 20% | Per-category margins from `ProfitabilityService`; growth from `RevenueAnalyticsService` |
| **Under-utilised budget capacity** | Any category/department is > 20% under budget | `BudgetAnalyticsService.get_underutilized_budget()` — variance_pct < −20% |
| **Improving receivables collection** | 90+ day bucket decreased month-over-month in the last 3-month aging trend | `ReceivablesService.get_aging_trend(months=3)` |
| **Gross margin expanding** | Gross margin improved for three consecutive months | `ProfitabilityService.get_margin_trend()` — three monotonically increasing margin points |

---

## 6. Action Generation Rules

Implemented in [`RiskOpportunityActionEngine.get_recommended_actions()`](../backend/app/services/risk_engine.py). Returns up to 6 actions, sorted by priority (high → medium → low). Actions are **only generated when the underlying signal is present** — no hardcoded defaults.

| Trigger Condition | Action Generated | Priority | `action_type` |
|-------------------|-----------------|----------|--------------|
| 90+ day overdue receivables > 20% of total outstanding | "Review overdue receivables" | high | investigate |
| Any category/department budget overrun > 15% | "Investigate expense variance" (names the specific area) | high | investigate |
| Revenue growth negative for 2+ consecutive months | "Analyze revenue decline drivers" | high | investigate |
| Any expense anomalies detected (high-severity anomalies raise priority) | "Investigate flagged expense items" | high (if high-severity anomalies) / medium | investigate |
| Current gross margin < prior-period gross margin | "Review cost structure and pricing" | medium | monitor |
| Net cash flow < 0 | "Monitor cash position closely" | high | monitor |

---

## 7. Data Quality Scoring

Implemented in [`DataQualityService`](../backend/app/services/data_quality.py).

### Weighted Overall Score

```
overall_score = (completeness × 0.30)
              + (consistency  × 0.25)
              + (validity     × 0.25)
              + (duplicates   × 0.20)
```

Each dimension score is 0–100.

### Dimension Descriptions

| Dimension | Weight | What is measured |
|-----------|--------|-----------------|
| **Completeness** | 30% | NULL values in 21 critical fields across `transactions`, `expenses`, `invoices`, `cash_flows`, and `budgets`. Score = `(total_fields − missing_fields) / total_fields × 100` |
| **Consistency** | 25% | Logical contradictions: sales with `amount ≤ 0`; invoices where `paid_amount > invoice_amount`; expenses with a future `expense_date`. Score = `(total_rows − inconsistent_rows) / total_rows × 100` |
| **Validity** | 25% | Enum violations (invalid `transaction_type`, `status`, `payment_method`, `payment_status`) and outlier amounts > 1 billion. Score = `(total_rows − invalid_rows) / total_rows × 100` |
| **Duplicates** | 20% | Duplicate invoices identified by `(customer_id, invoice_date, invoice_amount)`. Score = `100 − (duplicate_count / total_rows × 100)` |

### Derived Metrics in Report

- `missing_value_rate` — `missing_count / total_count × 100` from the completeness check
- `duplicate_rate` — raw duplicate percentage from the duplicates check
- `issues` — aggregated list from consistency + validity + duplicates, each with `table`, `issue`, `affected_rows`, and `severity` (`high` or `medium`)
