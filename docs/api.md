# API Reference

FinGuard AI exposes a RESTful JSON API built with FastAPI.

**Base URL:** `http://localhost:8000/api/v1`

Interactive documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 1. Endpoint Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/overview` | Executive KPIs + insight cards |
| GET | `/analytics/revenue` | Revenue analytics |
| GET | `/analytics/profit` | Profitability analytics |
| GET | `/analytics/expenses` | Expense analytics |
| GET | `/analytics/cashflow` | Cash flow analytics |
| GET | `/analytics/budget` | Budget vs actual |
| GET | `/analytics/receivables` | Receivables aging |
| GET | `/risk/overview` | Risk score + indicators |
| GET | `/risk/anomalies/expenses` | Expense anomalies |
| GET | `/risk/anomalies/transactions` | Transaction anomalies |
| GET | `/risk/anomalies/summary` | Anomaly counts |
| GET | `/risk/opportunities` | Detected opportunities |
| GET | `/risk/actions` | Recommended actions |
| GET | `/forecast/revenue` | Revenue forecast |
| GET | `/data-quality/` | Data quality report |
| POST | `/ai/ask` | Ask AI analyst |
| POST | `/ai/executive-brief` | Generate executive brief |
| GET | `/health` | Health check |

---

## 2. Query Parameters

### Common Date Range Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | `YYYY-MM-DD` | None (last 12 months) | Inclusive start date |
| `end_date` | `YYYY-MM-DD` | None (today) | Inclusive end date |
| `period` | `string` | `last_12_months` | Named period: `last_30_days`, `last_90_days`, `last_12_months`, `ytd`, `last_year` |

### Endpoint-Specific Parameters

| Endpoint | Parameter | Type | Default | Description |
|----------|-----------|------|---------|-------------|
| `/analytics/revenue` | `granularity` | `string` | `monthly` | Time series bucketing: `monthly`, `weekly`, `quarterly` |
| `/analytics/budget` | `year` | `integer` | current year | Budget year to analyse |
| `/forecast/revenue` | `horizon_days` | `integer` | `90` | Forecast horizon in days |
| `/risk/anomalies/expenses` | `start_date`, `end_date`, `limit` | — | last 12 months, 50 | Date range and result cap |
| `/risk/anomalies/transactions` | `start_date`, `end_date`, `limit` | — | last 12 months, 50 | Date range and result cap |
| `/ai/ask` | — | — | — | Body params: `question`, `context_period` |
| `/ai/executive-brief` | — | — | — | Body param: `period` |

---

## 3. Endpoint Details and Example Responses

> **Note:** All monetary values below use INR (₹). The dataset is synthetic demonstration data.

---

### `GET /dashboard/overview`

Returns executive KPI summary and insight cards for the period.

**Query params:** `period`

**Example response:**
```json
{
  "kpis": {
    "total_revenue": {
      "value": 48250000.00,
      "formatted": "₹4.83 Cr",
      "previous_value": 43100000.00,
      "change_abs": 5150000.00,
      "change_pct": 11.95,
      "direction": "up",
      "interpretation": "Revenue growing strongly"
    },
    "net_profit": {
      "value": 8640000.00,
      "formatted": "₹86.40 L",
      "previous_value": 7200000.00,
      "change_abs": 1440000.00,
      "change_pct": 20.00,
      "direction": "up",
      "interpretation": "Profitability improving"
    },
    "profit_margin": {
      "value": 17.91,
      "formatted": "17.91%",
      "previous_value": 16.70,
      "change_pct": 7.25,
      "direction": "up",
      "interpretation": "Margin expansion — efficiency improving"
    },
    "total_expenses": {
      "value": 12300000.00,
      "formatted": "₹1.23 Cr",
      "change_pct": 8.10,
      "direction": "up",
      "interpretation": "Expenses rising — monitor for budget overrun"
    },
    "net_cash_flow": {
      "value": 5900000.00,
      "formatted": "₹59.00 L",
      "direction": "up",
      "interpretation": "Cash position strengthening"
    },
    "revenue_growth_pct": {
      "value": 11.95,
      "formatted": "11.95%",
      "direction": "up",
      "interpretation": "Strong revenue growth momentum"
    },
    "outstanding_receivables": {
      "value": 3200000.00,
      "formatted": "₹32.00 L",
      "interpretation": "Monitor ageing — high receivables strain cash flow"
    },
    "period_label": "Last 12 Months",
    "as_of_date": "2025-01-15"
  },
  "insight_cards": [
    {
      "type": "risk",
      "title": "Low gross margin",
      "body": "Gross margin is 14.2% (threshold: 20%)",
      "severity": "MEDIUM",
      "evidence": "Gross margin is 14.2% (threshold: 20%)",
      "metric_source": "margin"
    }
  ]
}
```

---

### `GET /analytics/revenue`

**Query params:** `start_date`, `end_date`, `granularity`

**Example response:**
```json
{
  "revenue_trend": [
    {"date": "2024-08-01", "value": 3820000.00},
    {"date": "2024-09-01", "value": 4110000.00},
    {"date": "2024-10-01", "value": 4350000.00},
    {"date": "2024-11-01", "value": 4280000.00},
    {"date": "2024-12-01", "value": 4900000.00},
    {"date": "2025-01-01", "value": 4020000.00}
  ],
  "by_category": [
    {"category": "Software Licenses", "value": 14200000.00, "pct_of_total": 29.43},
    {"category": "Professional Services", "value": 11500000.00, "pct_of_total": 23.83},
    {"category": "Hardware", "value": 9800000.00, "pct_of_total": 20.31}
  ],
  "by_region": [
    {"region": "North", "value": 18400000.00, "pct_of_total": 38.13},
    {"region": "South", "value": 14600000.00, "pct_of_total": 30.26},
    {"region": "West", "value": 9200000.00, "pct_of_total": 19.07},
    {"region": "East", "value": 6050000.00, "pct_of_total": 12.54}
  ],
  "growth_trend": [
    {"month": "2024-08", "growth_pct": 4.2},
    {"month": "2024-09", "growth_pct": 7.6},
    {"month": "2024-10", "growth_pct": 9.1},
    {"month": "2024-11", "growth_pct": 8.4},
    {"month": "2024-12", "growth_pct": 15.3},
    {"month": "2025-01", "growth_pct": 5.2}
  ],
  "top_contributors": [
    {"name": "Acme Corp", "type": "customer", "value": 4200000.00},
    {"name": "TechStart Ltd", "type": "customer", "value": 3100000.00}
  ]
}
```

---

### `GET /analytics/profit`

**Query params:** `start_date`, `end_date`

**Example response:**
```json
{
  "profit_trend": [
    {"date": "2024-08-01", "gross_profit": 1720000.00, "net_profit": 860000.00},
    {"date": "2024-09-01", "gross_profit": 1850000.00, "net_profit": 920000.00}
  ],
  "margin_trend": [
    {"date": "2024-08-01", "gross_margin_pct": 15.1, "net_margin_pct": 7.5},
    {"date": "2024-09-01", "gross_margin_pct": 15.8, "net_margin_pct": 7.9}
  ],
  "by_category": [
    {"category": "Software Licenses", "gross_margin_pct": 68.0, "net_margin_pct": 42.0}
  ],
  "by_region": [
    {"region": "North", "gross_margin_pct": 18.2, "net_margin_pct": 10.1}
  ]
}
```

---

### `GET /analytics/expenses`

**Query params:** `start_date`, `end_date`

**Example response:**
```json
{
  "expense_trend": [
    {"date": "2024-08-01", "value": 960000.00},
    {"date": "2024-09-01", "value": 1020000.00}
  ],
  "by_category": [
    {"category": "Payroll", "value": 5400000.00, "pct_of_total": 43.9},
    {"category": "Infrastructure", "value": 2100000.00, "pct_of_total": 17.1},
    {"category": "Marketing", "value": 1800000.00, "pct_of_total": 14.6}
  ],
  "by_department": [
    {"department": "Engineering", "value": 4800000.00, "pct_of_total": 39.0},
    {"department": "Sales", "value": 3200000.00, "pct_of_total": 26.0}
  ],
  "expense_revenue_ratio": 25.49
}
```

---

### `GET /analytics/cashflow`

**Query params:** `start_date`, `end_date`

**Example response:**
```json
{
  "cashflow_trend": [
    {"date": "2024-08-01", "inflow": 3900000.00, "outflow": 3100000.00, "net": 800000.00},
    {"date": "2024-09-01", "inflow": 4200000.00, "outflow": 3400000.00, "net": 800000.00}
  ],
  "by_category": [
    {"category": "Sales Revenue", "inflow": 42000000.00, "outflow": 0},
    {"category": "Payroll", "inflow": 0, "outflow": 5400000.00}
  ],
  "cumulative": [
    {"date": "2024-08-01", "cumulative_net": 800000.00},
    {"date": "2024-09-01", "cumulative_net": 1600000.00}
  ]
}
```

---

### `GET /analytics/budget`

**Query params:** `year`

**Example response:**
```json
{
  "year": 2025,
  "budget_vs_actual": [
    {
      "category": "Marketing",
      "department": "Sales",
      "budget": 2000000.00,
      "actual": 2380000.00,
      "variance": 380000.00,
      "variance_pct": 19.0
    }
  ],
  "budget_trend": [
    {"month": "2025-01", "budget": 1020000.00, "actual": 980000.00}
  ],
  "overspending": [
    {"category": "Marketing", "department": "Sales", "budget": 2000000.00, "actual": 2380000.00, "variance": 380000.00, "variance_pct": 19.0}
  ],
  "underutilized": [
    {"category": "Training", "department": "HR", "budget": 500000.00, "actual": 180000.00, "variance": -320000.00, "variance_pct": -64.0}
  ]
}
```

---

### `GET /analytics/receivables`

**Example response:**
```json
{
  "aging_summary": {
    "total_outstanding": 3200000.00,
    "bucket_0_30": 1400000.00,
    "bucket_31_60": 740000.00,
    "bucket_61_90": 420000.00,
    "bucket_90_plus": 640000.00
  },
  "aging_trend": [
    {"month": "2024-11", "bucket_90_plus": 820000.00},
    {"month": "2024-12", "bucket_90_plus": 720000.00},
    {"month": "2025-01", "bucket_90_plus": 640000.00}
  ],
  "top_overdue": [
    {
      "customer": "Global Tech Pvt Ltd",
      "invoice_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "invoice_amount": 480000.00,
      "paid_amount": 0.00,
      "due_date": "2024-09-30",
      "days_overdue": 107
    }
  ],
  "collection_efficiency": [
    {"month": "2024-11", "efficiency_pct": 82.4},
    {"month": "2024-12", "efficiency_pct": 85.1},
    {"month": "2025-01", "efficiency_pct": 87.3}
  ]
}
```

---

### `GET /risk/overview`

**Example response:**
```json
{
  "risk_score": {
    "level": "MEDIUM",
    "score": 1,
    "confidence": 0.72,
    "methodology": "XGBoost multi-class classifier trained on 24 months of rolling financial features. Risk is derived from revenue growth, margin health, cash flow, and operational efficiency signals.",
    "indicators": [
      {
        "feature": "Gross Margin Level",
        "value": 14.2,
        "threshold": 20.0,
        "evidence": "Gross margin is 14.2% (threshold: 20%)",
        "contributing": true
      },
      {
        "feature": "Revenue Growth Trend",
        "value": 11.95,
        "threshold": 0.0,
        "evidence": "Revenue growth is 11.95%",
        "contributing": false
      }
    ],
    "generated_at": "2025-01-15T10:30:00Z"
  }
}
```

---

### `GET /risk/anomalies/expenses`

**Query params:** `start_date`, `end_date`, `limit`

**Example response:**
```json
[
  {
    "record_id": "7a3b5c21-1234-5678-abcd-ef9876543210",
    "date": "2025-01-08",
    "category": "Infrastructure",
    "department": "Engineering",
    "amount": 480000.00,
    "expected_range_low": 42000.00,
    "expected_range_high": 195000.00,
    "anomaly_score": 4.2304,
    "severity": "high",
    "reason": "Amount of ₹4,80,000 significantly exceeds the expected range of ₹42,000–₹1,95,000 for Infrastructure",
    "requires_investigation": true
  }
]
```

---

### `GET /risk/anomalies/transactions`

**Query params:** `start_date`, `end_date`, `limit`

**Example response:**
```json
[
  {
    "record_id": "1f2e3d4c-abcd-1234-5678-0987654321ab",
    "date": "2025-01-10",
    "category": "Software Licenses",
    "department": null,
    "amount": 9200000.00,
    "expected_range_low": 180000.00,
    "expected_range_high": 1840000.00,
    "anomaly_score": 3.1562,
    "severity": "high",
    "reason": "Amount of ₹92,00,000 significantly exceeds the expected range of ₹1,80,000–₹18,40,000 for Software Licenses",
    "requires_investigation": true
  }
]
```

---

### `GET /risk/anomalies/summary`

**Example response:**
```json
{
  "total_expense_anomalies": 7,
  "total_transaction_anomalies": 3,
  "high_severity": 4,
  "total_flagged_amount": 18420000.00
}
```

---

### `GET /risk/opportunities`

**Example response:**
```json
[
  {
    "title": "High-growth high-margin category: Software Licenses",
    "description": "Software Licenses shows above-average margin (68.0%) during a high-growth period.",
    "supporting_metric": "Category margin: 68.0% vs avg 22.4%",
    "estimated_impact": "Revenue and margin expansion potential",
    "recommended_action": "Prioritise investment in Software Licenses to capitalise on growth momentum."
  },
  {
    "title": "Budget capacity available: Training / HR",
    "description": "Training (HR) has spent ₹1,80,000 against a budget of ₹5,00,000 (64.0% under budget).",
    "supporting_metric": "Budget utilisation: 36.0%",
    "estimated_impact": "Reallocation opportunity",
    "recommended_action": "Consider reallocating unused Training budget to higher-priority areas."
  }
]
```

---

### `GET /risk/actions`

**Example response:**
```json
[
  {
    "priority": "high",
    "title": "Investigate flagged expense items",
    "rationale": "7 anomalous expense records detected (4 high-severity).",
    "supporting_evidence": "Expense anomalies: 7 total, 4 high-severity",
    "action_type": "investigate"
  },
  {
    "priority": "medium",
    "title": "Review cost structure and pricing",
    "rationale": "Gross margin declined by 2.3 percentage points year-over-year.",
    "supporting_evidence": "Current margin: 14.2%, Prior period: 16.5%",
    "action_type": "monitor"
  }
]
```

---

### `GET /forecast/revenue`

**Query params:** `horizon_days` (default: `90`)

**Example response:**
```json
{
  "horizon_days": 90,
  "method": "Holt-Winters Exponential Smoothing (additive trend, additive seasonality)",
  "mae": 182400.50,
  "rmse": 241800.75,
  "mape": 4.82,
  "points": [
    {
      "date": "2024-02-01",
      "forecast": 3540000.00,
      "lower_bound": 3540000.00,
      "upper_bound": 3540000.00,
      "is_actual": true
    },
    {
      "date": "2025-02-01",
      "forecast": 4820000.00,
      "lower_bound": 4345160.00,
      "upper_bound": 5294840.00,
      "is_actual": false
    },
    {
      "date": "2025-03-01",
      "forecast": 5120000.00,
      "lower_bound": 4645160.00,
      "upper_bound": 5594840.00,
      "is_actual": false
    }
  ],
  "disclaimer": "This forecast is a statistical estimate based on historical patterns. It does not account for market disruptions, strategic changes, or external events. Use as one input among many in your planning process.",
  "generated_at": "2025-01-15T10:30:00Z"
}
```

---

### `GET /data-quality/`

**Example response:**
```json
{
  "overall_score": 97.84,
  "completeness": 99.80,
  "consistency": 100.00,
  "validity": 100.00,
  "duplicate_rate": 0.0012,
  "missing_value_rate": 0.0020,
  "total_records": 42000,
  "issues": [],
  "generated_at": "2025-01-15T10:30:00Z"
}
```

---

### `POST /ai/ask`

**Request body:**
```json
{
  "question": "Why did gross margin decline last quarter?",
  "context_period": "last_90_days"
}
```

**Example response:**
```json
{
  "summary": "Based on the available data, gross margin for the last 90 days stands at 13.8%, compared to 16.5% in the prior period — a decline of 2.7 percentage points.",
  "facts": [
    "Current gross margin: 13.8%",
    "Prior period gross margin: 16.5%",
    "COGS increased by 18.3% period-over-period",
    "Revenue grew by 9.1% in the same period"
  ],
  "insights": [
    "The data indicates that costs grew faster than revenue, compressing the margin.",
    "One possible contributor is the Infrastructure category, which shows elevated expense anomalies in the period."
  ],
  "risks": [
    "If the margin compression trend continues, net profitability will come under pressure."
  ],
  "opportunities": [
    "The Software Licenses category maintains a 68% gross margin — prioritising this segment could offset compression elsewhere."
  ],
  "actions": [
    "Review COGS drivers in the Hardware category, which accounts for the largest absolute cost increase.",
    "Investigate the 4 high-severity expense anomalies flagged in the period."
  ],
  "limitations": [
    "This analysis is based on the last 90 days of data. External cost drivers (supplier price changes, logistics) are not captured in the dataset."
  ],
  "raw_context_period": "last_90_days",
  "generated_at": "2025-01-15T10:30:00Z"
}
```

---

### `POST /ai/executive-brief`

**Request body:**
```json
{
  "period": "last_12_months"
}
```

**Example response:**
```json
{
  "financial_health": "The business is in moderate financial health — revenue growth is strong at 11.95%, but gross margin compression and elevated overdue receivables warrant immediate attention.",
  "key_findings": [
    "Revenue reached ₹4.83 Cr, growing 11.95% year-over-year",
    "Net profit margin stands at 17.91%, up from 16.70% in the prior period",
    "Gross margin has compressed from 16.5% to 14.2% over the last 12 months",
    "₹32.00 L in outstanding receivables, with 20% overdue more than 90 days",
    "7 expense anomalies detected, 4 of which are high-severity"
  ],
  "major_risks": [
    "Gross margin at 14.2% — below the 20% healthy threshold (MEDIUM risk)",
    "₹6.40 L in 90+ day overdue receivables — potential write-off exposure",
    "Marketing/Sales department is 19% over budget for the year"
  ],
  "key_opportunities": [
    "Software Licenses category shows 68% gross margin — investment prioritisation opportunity",
    "Training budget is 64% unutilised — can be reallocated to growth initiatives"
  ],
  "areas_requiring_attention": [
    "COGS drivers in the Hardware and Infrastructure categories",
    "Collections process for 90+ day overdue accounts",
    "Marketing spend vs budget in the Sales department"
  ],
  "forecast_summary": "Statistical projections based on 24 months of historical data suggest revenue of approximately ₹4.82–5.12 Cr in the next 1–3 months, assuming current trends continue. These are estimates and do not account for structural changes.",
  "recommended_investigation_areas": [
    "4 high-severity expense anomalies in Infrastructure — review against vendor contracts",
    "Global Tech Pvt Ltd invoice of ₹4.80 L — 107 days overdue, escalation recommended",
    "Marketing overspend of 19% vs budget — validate spend authorisation"
  ],
  "generated_at": "2025-01-15T10:30:00Z",
  "disclaimer": "This executive brief is generated by AI based on verified financial analytics. It is a decision-support tool and does not constitute regulated financial advice."
}
```

---

### `GET /health`

**Example response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 4. Error Responses

All errors follow a consistent JSON envelope:

```json
{
  "error": "<short error type>",
  "detail": "<human-readable explanation>"
}
```

### Standard HTTP Error Codes

| Code | When | Example body |
|------|------|-------------|
| `400 Bad Request` | Invalid query parameter type or value | `{"error": "Bad Request", "detail": "Invalid date format for start_date"}` |
| `404 Not Found` | Path does not exist | `{"error": "Not found", "detail": "The requested path '/api/v1/xyz' does not exist."}` |
| `500 Internal Server Error` | Unhandled server exception | `{"error": "Internal server error", "detail": "An unexpected error occurred. Please try again later."}` |
| `422 Unprocessable Entity` | FastAPI request validation failure (wrong body schema) | FastAPI default validation error format with field-level details |

### Analytics Endpoint Errors

Analytics endpoints return `500` with a specific detail message when the underlying service fails:

```json
{"detail": "Failed to retrieve revenue analytics"}
```

### AI Endpoint Errors

AI endpoints **never return 5xx**. Failures return a valid `AIResponse` or `ExecutiveBriefResponse` with a degraded summary. See [AI Integration — Failure Modes](./ai.md#6-failure-modes-and-graceful-degradation).

---

## 5. Authentication

Authentication is **not currently implemented**. All endpoints are publicly accessible on the local development server.

### Adding JWT Bearer Token Authentication

To add authentication in production:

1. **Install dependency:** `pip install python-jose[cryptography] passlib[bcrypt]`

2. **Create an auth router** at `backend/app/api/v1/auth.py` with `/login` returning a signed JWT.

3. **Add a dependency** to protected routers:
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import OAuth2PasswordBearer

   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

   async def get_current_user(token: str = Depends(oauth2_scheme)):
       # verify token, raise 401 if invalid
       ...
   ```

4. **Inject the dependency** into each router that requires authentication:
   ```python
   @router.get("/dashboard/overview", dependencies=[Depends(get_current_user)])
   def get_dashboard_overview(...):
       ...
   ```

5. **Frontend:** Store the token in memory (not `localStorage`) and attach as:
   ```
   Authorization: Bearer <token>
   ```

6. **Environment variables to add:**
   - `JWT_SECRET_KEY` — long random string
   - `JWT_ALGORITHM` — `"HS256"`
   - `JWT_EXPIRE_MINUTES` — e.g. `480`
