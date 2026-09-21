# FinGuard AI — Corporate Data Dictionary

This document provides a comprehensive technical schema specification for the FinGuard AI analytical database (Jan 2023 – Mar 2025 synthetic demonstration dataset).

---

## 1. Reference & Dimension Tables

### 1.1 `categories`
Categorization for product revenue lines and operational expense centers.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `category_id` | `INTEGER` | `PRIMARY KEY` | Unique category identifier |
| `name` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | Category title (e.g. Software/SaaS, Electronics, Operations) |
| `type` | `VARCHAR(20)` | `CHECK IN ('revenue', 'expense', 'mixed')` | Category accounting nature |

### 1.2 `departments`
Organizational business units incurring operating costs or driving sales.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `department_id` | `INTEGER` | `PRIMARY KEY` | Unique department identifier |
| `name` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | Department name (e.g. Sales, Marketing, Operations) |
| `budget_code` | `VARCHAR(20)` | `NOT NULL, UNIQUE` | General ledger cost-center code |

### 1.3 `regions`
Geographic sales territories.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `region_id` | `INTEGER` | `PRIMARY KEY` | Unique region identifier |
| `name` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Territory name (North, South, East, West, Central) |
| `code` | `VARCHAR(10)` | `NOT NULL, UNIQUE` | Short regional ISO code |

---

## 2. Master Entity Tables

### 2.1 `customers`
Commercial B2B client accounts.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `customer_id` | `INTEGER` | `PRIMARY KEY` | Unique customer account ID |
| `name` | `VARCHAR(150)` | `NOT NULL` | Registered commercial corporate entity name |
| `industry` | `VARCHAR(100)` | `NOT NULL` | Industry vertical (Technology, Healthcare, Finance, etc.) |
| `segment` | `VARCHAR(20)` | `CHECK IN ('enterprise', 'mid-market', 'smb')` | Client account scale tier |
| `credit_limit` | `NUMERIC(15,2)` | `CHECK > 0` | Approved commercial credit facility ($) |
| `payment_terms` | `INTEGER` | `DEFAULT 30` | Contractual payment terms (e.g. Net 30, Net 60) |

### 2.2 `vendors`
Commercial suppliers and service providers.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `vendor_id` | `INTEGER` | `PRIMARY KEY` | Unique vendor account ID |
| `name` | `VARCHAR(150)` | `NOT NULL` | Vendor corporate trade name |
| `category_id` | `INTEGER` | `FK -> categories` | Primary procurement category |
| `payment_terms` | `INTEGER` | `DEFAULT 30` | Disbursement agreement terms (days) |

### 2.3 `products`
Product catalog and service line items.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `product_id` | `INTEGER` | `PRIMARY KEY` | Unique product identifier |
| `name` | `VARCHAR(150)` | `NOT NULL` | Product name or service description |
| `category_id` | `INTEGER` | `FK -> categories` | Product revenue classification |
| `unit_price` | `NUMERIC(15,2)` | `CHECK > 0` | Standard gross selling price |
| `unit_cost` | `NUMERIC(15,2)` | `CHECK >= 0` | Cost of goods sold (COGS) base |

---

## 3. Financial Fact & Transaction Tables

### 3.1 `transactions`
Individual commercial sales transactions and adjustments.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `transaction_id` | `UUID` | `PRIMARY KEY` | Unique transaction UUID |
| `transaction_date` | `DATE` | `NOT NULL, INDEXED` | Commercial transaction date |
| `customer_id` | `INTEGER` | `FK -> customers` | Purchasing customer account |
| `product_id` | `INTEGER` | `FK -> products` | Item or subscription purchased |
| `category_id` | `INTEGER` | `FK -> categories` | Revenue category classification |
| `region_id` | `INTEGER` | `FK -> regions` | Originating sales region |
| `department_id` | `INTEGER` | `FK -> departments` | Sales business unit |
| `transaction_type`| `VARCHAR(20)` | `CHECK IN ('sale', 'refund', 'adjustment')` | Transaction classification |
| `amount` | `NUMERIC(15,2)` | `CHECK > 0 for sales` | Net transaction value ($) |
| `cost` | `NUMERIC(15,2)` | `CHECK >= 0` | Cost of goods sold for transaction ($) |
| `quantity` | `INTEGER` | `CHECK > 0` | Number of units purchased |
| `discount_pct` | `NUMERIC(5,2)` | `CHECK 0 TO 100` | Commercial discount percentage applied |
| `payment_method` | `VARCHAR(20)` | `CHECK IN ('bank_transfer', 'credit_card', 'cash', 'cheque')` | Settlement channel |
| `status` | `VARCHAR(15)` | `CHECK IN ('completed', 'pending', 'cancelled')` | Order fulfillment status |

### 3.2 `expenses`
Operational expenditures incurred across departments.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `expense_id` | `UUID` | `PRIMARY KEY` | Unique expense disbursement UUID |
| `expense_date` | `DATE` | `NOT NULL, INDEXED` | Incurred expense booking date |
| `category_id` | `INTEGER` | `FK -> categories` | Operating expense category |
| `department_id` | `INTEGER` | `FK -> departments` | Incurring department cost center |
| `vendor_id` | `INTEGER` | `FK -> vendors` | Paid supplier or contractor |
| `amount` | `NUMERIC(15,2)` | `CHECK > 0` | Bill disbursement amount ($) |
| `status` | `VARCHAR(15)` | `DEFAULT 'approved'` | Expense approval workflow status |
| `description` | `TEXT` | `NULLABLE` | Line-item business purpose |

### 3.3 `invoices`
Commercial trade accounts receivable.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `invoice_id` | `UUID` | `PRIMARY KEY` | Unique commercial invoice identifier |
| `customer_id` | `INTEGER` | `FK -> customers` | Invoiced client account |
| `invoice_date` | `DATE` | `NOT NULL, INDEXED` | Date invoice was issued |
| `due_date` | `DATE` | `NOT NULL, INDEXED` | Contractual payment deadline |
| `invoice_amount` | `NUMERIC(15,2)` | `CHECK > 0` | Total invoiced amount ($) |
| `paid_amount` | `NUMERIC(15,2)` | `CHECK >= 0, <= invoice_amount` | Total amount collected to date ($) |
| `payment_date` | `DATE` | `NULLABLE` | Date payment was settled |
| `payment_status` | `VARCHAR(15)` | `CHECK IN ('unpaid', 'partial', 'paid', 'overdue')` | Collection workflow status |

### 3.4 `cash_flows`
Direct cash inflows and disbursements tracking liquidity.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `flow_id` | `UUID` | `PRIMARY KEY` | Unique cash flow journal UUID |
| `flow_date` | `DATE` | `NOT NULL, INDEXED` | Cash value settlement date |
| `flow_type` | `VARCHAR(10)` | `CHECK IN ('inflow', 'outflow')` | Direction of funds movement |
| `category_id` | `INTEGER` | `FK -> categories` | Cash allocation category |
| `department_id` | `INTEGER` | `FK -> departments` | Responsible organizational unit |
| `amount` | `NUMERIC(15,2)` | `CHECK > 0` | Settled cash volume ($) |
| `description` | `TEXT` | `NULLABLE` | Settlement memo |
| `reference_id` | `UUID` | `NULLABLE` | Linked transaction or expense ID |

### 3.5 `budgets`
Quarterly departmental budget allocations and actual spend tracking.

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| `budget_id` | `UUID` | `PRIMARY KEY` | Budget allocation line identifier |
| `fiscal_year` | `INTEGER` | `NOT NULL` | Fiscal budget year (2023, 2024, 2025) |
| `quarter` | `INTEGER` | `CHECK 1 TO 4` | Fiscal quarter (Q1–Q4) |
| `category_id` | `INTEGER` | `FK -> categories` | Allocated expense category |
| `department_id` | `INTEGER` | `FK -> departments` | Assigned department |
| `budgeted_amount`| `NUMERIC(15,2)` | `CHECK > 0` | Target ceiling allocation ($) |
| `actual_amount` | `NUMERIC(15,2)` | `CHECK >= 0` | Realized spend booked to date ($) |
