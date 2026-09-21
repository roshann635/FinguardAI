# Database

FinGuard AI uses PostgreSQL. The schema is defined via SQLAlchemy ORM models in `backend/app/models/`.

---

## 1. ER Diagram

```mermaid
erDiagram
    CATEGORIES ||--o{ PRODUCTS : "categorizes"
    CATEGORIES ||--o{ TRANSACTIONS : "categorizes"
    CATEGORIES ||--o{ EXPENSES : "categorizes"
    CATEGORIES ||--o{ BUDGETS : "categorizes"
    CATEGORIES ||--o{ CASH_FLOWS : "categorizes"
    REGIONS ||--o{ CUSTOMERS : "located in"
    REGIONS ||--o{ VENDORS : "located in"
    REGIONS ||--o{ TRANSACTIONS : "occurs in"
    DEPARTMENTS ||--o{ TRANSACTIONS : "belongs to"
    DEPARTMENTS ||--o{ EXPENSES : "belongs to"
    DEPARTMENTS ||--o{ BUDGETS : "belongs to"
    CUSTOMERS ||--o{ TRANSACTIONS : "makes"
    CUSTOMERS ||--o{ INVOICES : "receives"
    VENDORS ||--o{ TRANSACTIONS : "fulfills"
    VENDORS ||--o{ EXPENSES : "billed by"
    PRODUCTS ||--o{ TRANSACTIONS : "sold in"
    CATEGORIES {
        serial category_id PK
        varchar name
        varchar type
    }
    TRANSACTIONS {
        uuid transaction_id PK
        date transaction_date
        int customer_id FK
        int vendor_id FK
        int product_id FK
        int category_id FK
        int region_id FK
        int department_id FK
        varchar transaction_type
        numeric amount
        numeric cost
        int quantity
        numeric discount_pct
        varchar payment_method
        varchar status
    }
    EXPENSES {
        uuid expense_id PK
        date expense_date
        int category_id FK
        int department_id FK
        int vendor_id FK
        numeric amount
        varchar description
        varchar status
    }
    BUDGETS {
        uuid budget_id PK
        int period_year
        int period_month
        int category_id FK
        int department_id FK
        numeric budget_amount
    }
    INVOICES {
        uuid invoice_id PK
        int customer_id FK
        date invoice_date
        date due_date
        numeric invoice_amount
        numeric paid_amount
        date payment_date
        varchar payment_status
    }
    CASH_FLOWS {
        uuid cashflow_id PK
        date flow_date
        varchar flow_type
        int category_id FK
        int department_id FK
        numeric amount
        varchar description
    }
```

---

## 2. Table Descriptions

### `categories`
**Purpose:** Reference table classifying all financial line items. Every transaction, expense, budget, and cash flow record must belong to a category.

**Business rules:**
- `type` must be one of `'revenue'`, `'expense'`, or `'mixed'`
- Name is globally unique (case-sensitive in PostgreSQL)
- `ondelete="RESTRICT"` on all FK references — you cannot delete a category that has associated records

### `regions`
**Purpose:** Geographic dimension for customers, vendors, and transactions. Enables regional P&L breakdown.

**Business rules:**
- Name is globally unique
- `ondelete="RESTRICT"` on all FK references

### `departments`
**Purpose:** Internal organisational unit dimension for transactions, expenses, and budgets. Enables departmental cost centre analysis.

**Business rules:**
- Name is globally unique
- `ondelete="RESTRICT"` on all FK references

### `customers`
**Purpose:** Entity that purchases products and receives invoices.

**Business rules:**
- `segment` must be one of `'enterprise'`, `'mid-market'`, `'smb'`
- `region_id` is required; `ondelete="RESTRICT"`
- `is_active` flag — inactive customers are retained in history
- `signup_date` enables cohort analysis

### `vendors`
**Purpose:** External supplier that fulfills orders and bills expenses.

**Business rules:**
- Each vendor has a primary `category_id` (their primary business category) and a `region_id`
- `is_active` flag preserves historical vendor records

### `products`
**Purpose:** SKU-level product catalogue. Stores cost and selling price for margin calculations.

**Business rules:**
- `unit_cost >= 0` and `selling_price >= 0` enforced via CHECK constraints
- `category_id` required; `ondelete="RESTRICT"`
- `is_active` flag for soft deletion

### `transactions`
**Purpose:** Core revenue-generating table. Records each sale, refund, or adjustment event.

**Business rules:**
- `transaction_type` ∈ `{'sale', 'refund', 'adjustment'}`
- `status` ∈ `{'completed', 'pending', 'cancelled'}`
- `payment_method` ∈ `{'bank_transfer', 'credit_card', 'cash', 'cheque'}`
- Revenue KPIs use only `transaction_type='sale'` AND `status='completed'`
- `discount_pct` is `BETWEEN 0 AND 100`; net amount = `amount × (1 − discount_pct / 100)`
- `cost >= 0`; COGS = `cost × quantity`
- `customer_id` and `vendor_id` are `SET NULL` on delete (historical records preserved)

### `expenses`
**Purpose:** Operational expenses — vendor bills, internal costs, overheads.

**Business rules:**
- `amount > 0` (positive values only; refunds not modelled here)
- `status` ∈ `{'approved', 'pending', 'rejected'}`
- Only `status='approved'` expenses are included in KPI calculations
- `vendor_id` is nullable (`SET NULL` on delete) — expenses can be internal

### `budgets`
**Purpose:** Monthly budget allocations at the category + department granularity.

**Business rules:**
- `budget_amount >= 0`
- `period_year BETWEEN 2000 AND 2100`
- `period_month BETWEEN 1 AND 12`
- Composite UNIQUE constraint `(period_year, period_month, category_id, department_id)` — exactly one budget row per month/category/department combination

### `invoices`
**Purpose:** Accounts receivable tracking. Records what customers owe and what has been paid.

**Business rules:**
- `invoice_amount > 0`
- `paid_amount >= 0` and `paid_amount <= invoice_amount`
- `payment_status` ∈ `{'unpaid', 'partial', 'paid', 'overdue'}`
- Outstanding receivables = `SUM(invoice_amount − paid_amount)` where `payment_status IN ('unpaid', 'partial', 'overdue')`

### `cash_flows`
**Purpose:** Cash movement records (inflows and outflows) distinct from transactional revenue. Represents the cash position timeline.

**Business rules:**
- `amount > 0` (direction is expressed via `flow_type`)
- `flow_type` ∈ `{'inflow', 'outflow'}`
- `reference_id` (UUID, nullable) can optionally link to a source transaction or invoice
- Net cash flow = `SUM(inflows) − SUM(outflows)`

---

## 3. Indexes

All composite indexes are defined via `__table_args__` in the SQLAlchemy model classes.

| Index Name | Table | Columns | Rationale |
|-----------|-------|---------|-----------|
| `idx_txn_date_cat_region` | `transactions` | `(transaction_date, category_id, region_id)` | Covers most analytics queries that filter/group by date + category or region |
| `idx_txn_type_status` | `transactions` | `(transaction_type, status)` | Fast filtering for `type='sale' AND status='completed'` — the most common predicate in KPI queries |
| `idx_exp_date_cat_dept` | `expenses` | `(expense_date, category_id, department_id)` | Covers date-range expense queries grouped by category or department |
| `idx_exp_status` | `expenses` | `(status)` | Fast filter for `status='approved'` |
| `idx_inv_status_due` | `invoices` | `(payment_status, due_date)` | Covers aging queries that filter by status and sort/filter by due date |
| `idx_inv_invoice_date` | `invoices` | `(invoice_date)` | Date-range invoice lookups |
| `idx_cf_date_type` | `cash_flows` | `(flow_date, flow_type)` | Cash flow trend queries filtering by date range and inflow/outflow type |
| `idx_cf_reference` | `cash_flows` | `(reference_id)` | Lookup by reference UUID when linking back to source transactions |
| `idx_budget_period_cat_dept` | `budgets` | `(period_year, period_month, category_id, department_id)` | Covers budget vs actual queries and the unique constraint check |

Additionally, single-column indexes are created by SQLAlchemy for:
- `transactions.customer_id`, `transactions.product_id`, `transactions.department_id`
- `expenses.vendor_id`
- `invoices.customer_id`
- `cash_flows.category_id`, `cash_flows.department_id`
- `customers.region_id`, `customers.segment`
- `vendors.category_id`, `vendors.region_id`
- `products.category_id`

---

## 4. Migration Instructions

FinGuard AI uses **SQLAlchemy `Base.metadata.create_all()`** for schema creation and a Python seed script for data population. There is no Alembic migration history by default.

### Step-by-step

```bash
# 1. Create the PostgreSQL database
psql -U postgres -c "CREATE DATABASE finguard;"

# 2. Set the DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres:password@localhost:5432/finguard"
# (or copy .env.example to .env and edit it)

# 3. Navigate to the backend directory
cd finguard-ai/backend

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database migrations (creates all tables)
python -c "
from app.database.connection import Base, engine
from app.models import *  # noqa: F401,F403 — import all models to register metadata
Base.metadata.create_all(bind=engine)
print('Tables created.')
"

# 6. Seed synthetic data
python -m data.seed   # adjust path to match your seed script location
```

### To reset the database

```bash
psql -U postgres -c "DROP DATABASE finguard;"
psql -U postgres -c "CREATE DATABASE finguard;"
# Re-run steps 5 and 6
```

---

## 5. Design Decisions

### UUID Primary Keys for Transactional Tables

`transactions`, `expenses`, `budgets`, `invoices`, and `cash_flows` use `UUID(as_uuid=True)` PKs with `default=uuid.uuid4`.

**Rationale:**
- Enables distributed generation of IDs without a centralised sequence — safe for bulk imports and future sharding
- Avoids leaking record counts through sequential IDs in public-facing APIs
- UUIDs are globally unique, making it safe to merge records across environments (dev → staging)

### Serial / Auto-increment PKs for Reference Tables

`categories`, `regions`, `departments`, `customers`, `vendors`, and `products` use `Integer` PKs with `autoincrement=True`.

**Rationale:**
- Reference tables are small, managed, and not bulk-imported from external sources
- Integer FKs are smaller and faster for the joins that fan out across millions of transaction rows
- These entities are typically created interactively; sequential IDs do not pose an information-leakage concern

### Composite UNIQUE Constraint on Budgets

```sql
UNIQUE (period_year, period_month, category_id, department_id)
```

**Rationale:**
- Enforces the business rule that there is exactly one budget allocation per month per category/department pair
- Prevents double-counting in budget vs actual variance calculations
- The same composite index also accelerates the most common budget query pattern
