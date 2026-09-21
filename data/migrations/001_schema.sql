-- =============================================================================
-- FinGuard AI — Database Schema Migration 001
-- PostgreSQL 14+
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- Lookup / reference tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    type          VARCHAR(10)  NOT NULL CHECK (type IN ('revenue', 'expense', 'mixed'))
);

CREATE TABLE IF NOT EXISTS regions (
    region_id   SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS departments (
    department_id   SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- Entity tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS customers (
    customer_id   SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    region_id     INT          NOT NULL REFERENCES regions(region_id) ON DELETE RESTRICT,
    segment       VARCHAR(20)  NOT NULL CHECK (segment IN ('enterprise', 'mid-market', 'smb')),
    signup_date   DATE         NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_region  ON customers(region_id);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id     SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    category_id   INT          NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    region_id     INT          NOT NULL REFERENCES regions(region_id)     ON DELETE RESTRICT,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vendors_category ON vendors(category_id);
CREATE INDEX IF NOT EXISTS idx_vendors_region   ON vendors(region_id);

CREATE TABLE IF NOT EXISTS products (
    product_id      SERIAL PRIMARY KEY,
    name            VARCHAR(200)   NOT NULL,
    category_id     INT            NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    unit_cost       NUMERIC(15, 2) NOT NULL CHECK (unit_cost >= 0),
    selling_price   NUMERIC(15, 2) NOT NULL CHECK (selling_price >= 0),
    is_active       BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

-- ---------------------------------------------------------------------------
-- Transactional tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id    UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date  DATE           NOT NULL,
    customer_id       INT            REFERENCES customers(customer_id)  ON DELETE SET NULL,
    vendor_id         INT            REFERENCES vendors(vendor_id)      ON DELETE SET NULL,
    product_id        INT            REFERENCES products(product_id)    ON DELETE SET NULL,
    category_id       INT            NOT NULL REFERENCES categories(category_id)  ON DELETE RESTRICT,
    region_id         INT            NOT NULL REFERENCES regions(region_id)       ON DELETE RESTRICT,
    department_id     INT            NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    transaction_type  VARCHAR(15)    NOT NULL CHECK (transaction_type IN ('sale', 'refund', 'adjustment')),
    amount            NUMERIC(15, 2) NOT NULL,
    cost              NUMERIC(15, 2) NOT NULL DEFAULT 0 CHECK (cost >= 0),
    quantity          INT            NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    discount_pct      NUMERIC(5, 2)  NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
    payment_method    VARCHAR(20)    NOT NULL CHECK (payment_method IN ('bank_transfer', 'credit_card', 'cash', 'cheque')),
    status            VARCHAR(15)    NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled')),
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- Composite indexes for analytical queries
CREATE INDEX IF NOT EXISTS idx_txn_date_cat_region
    ON transactions(transaction_date, category_id, region_id);
CREATE INDEX IF NOT EXISTS idx_txn_customer    ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_product     ON transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_txn_department  ON transactions(department_id);
CREATE INDEX IF NOT EXISTS idx_txn_type_status ON transactions(transaction_type, status);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS expenses (
    expense_id    UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_date  DATE           NOT NULL,
    category_id   INT            NOT NULL REFERENCES categories(category_id)  ON DELETE RESTRICT,
    department_id INT            NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    vendor_id     INT            REFERENCES vendors(vendor_id) ON DELETE SET NULL,
    amount        NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    description   TEXT,
    status        VARCHAR(15)    NOT NULL CHECK (status IN ('approved', 'pending', 'rejected')),
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exp_date_cat_dept
    ON expenses(expense_date, category_id, department_id);
CREATE INDEX IF NOT EXISTS idx_exp_vendor     ON expenses(vendor_id);
CREATE INDEX IF NOT EXISTS idx_exp_status     ON expenses(status);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS budgets (
    budget_id      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    period_year    INT            NOT NULL CHECK (period_year BETWEEN 2000 AND 2100),
    period_month   INT            NOT NULL CHECK (period_month BETWEEN 1 AND 12),
    category_id    INT            NOT NULL REFERENCES categories(category_id)   ON DELETE RESTRICT,
    department_id  INT            NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    budget_amount  NUMERIC(15, 2) NOT NULL CHECK (budget_amount >= 0),
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    -- Prevent duplicate budget entries for the same period/category/dept
    CONSTRAINT uq_budget_period_cat_dept UNIQUE (period_year, period_month, category_id, department_id)
);

CREATE INDEX IF NOT EXISTS idx_budget_period_cat_dept
    ON budgets(period_year, period_month, category_id, department_id);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id       UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id      INT            NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    invoice_date     DATE           NOT NULL,
    due_date         DATE           NOT NULL,
    invoice_amount   NUMERIC(15, 2) NOT NULL CHECK (invoice_amount > 0),
    paid_amount      NUMERIC(15, 2) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    payment_date     DATE,
    payment_status   VARCHAR(15)    NOT NULL CHECK (payment_status IN ('unpaid', 'partial', 'paid', 'overdue')),
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    -- paid amount cannot exceed invoice amount
    CONSTRAINT chk_paid_lte_invoice CHECK (paid_amount <= invoice_amount)
);

CREATE INDEX IF NOT EXISTS idx_inv_status_due    ON invoices(payment_status, due_date);
CREATE INDEX IF NOT EXISTS idx_inv_customer      ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_inv_invoice_date  ON invoices(invoice_date);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cash_flows (
    cashflow_id   UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_date     DATE           NOT NULL,
    flow_type     VARCHAR(10)    NOT NULL CHECK (flow_type IN ('inflow', 'outflow')),
    category_id   INT            REFERENCES categories(category_id)   ON DELETE SET NULL,
    department_id INT            REFERENCES departments(department_id) ON DELETE SET NULL,
    amount        NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    description   TEXT,
    reference_id  UUID,          -- loose FK to transaction/invoice/expense (polymorphic)
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cf_date_type    ON cash_flows(flow_date, flow_type);
CREATE INDEX IF NOT EXISTS idx_cf_category     ON cash_flows(category_id);
CREATE INDEX IF NOT EXISTS idx_cf_department   ON cash_flows(department_id);
CREATE INDEX IF NOT EXISTS idx_cf_reference    ON cash_flows(reference_id);

-- ---------------------------------------------------------------------------
-- Trigger: auto-update updated_at on transactions and invoices
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_txn_updated_at   ON transactions;
CREATE TRIGGER trg_txn_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_inv_updated_at   ON invoices;
CREATE TRIGGER trg_inv_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- Comments
-- ---------------------------------------------------------------------------

COMMENT ON TABLE categories   IS 'Master list of revenue/expense/mixed categories';
COMMENT ON TABLE regions      IS 'Geographic regions for customers, vendors, and transactions';
COMMENT ON TABLE departments  IS 'Internal company departments';
COMMENT ON TABLE customers    IS 'Customer master with segment and region';
COMMENT ON TABLE vendors      IS 'Vendor/supplier master';
COMMENT ON TABLE products     IS 'Product catalogue with cost and selling price';
COMMENT ON TABLE transactions IS 'All sales, refunds, and adjustments';
COMMENT ON TABLE expenses     IS 'Operational expense records';
COMMENT ON TABLE budgets      IS 'Monthly budget allocations per category and department';
COMMENT ON TABLE invoices     IS 'Customer invoices with payment tracking';
COMMENT ON TABLE cash_flows   IS 'Cash inflow/outflow ledger with optional references';

COMMIT;
