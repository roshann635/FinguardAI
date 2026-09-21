#!/usr/bin/env python3
"""
FinGuard AI — Synthetic Data Seed Generator
============================================
Generates ~3-4 years of realistic financial data (Jan 2023 – Mar 2025) that
embeds the following analytical scenarios:

  A  Revenue growing +15 % YoY
  B  Expenses growing faster than revenue in Q3 2024 → margin compression
  C  Gross margin declining in Electronics in H2 2024
  D  Receivables aging increasing — invoices 61-90+ days overdue
  E  Software/SaaS outperforming all other categories in 2024
  F  Unusual expense spike in Oct 2024 (Operations dept, ~3x normal)
  G  Seasonal revenue — Q4 high, Q1 low
  H  Budget overruns in Marketing and Operations Q3-Q4 2024

Usage:
    pip install -r requirements.txt
    python generate_seed.py

DATABASE_URL must be set in the environment or in a .env file.
"""

import os
import sys
import uuid
import random
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd
from faker import Faker
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL is not set. Check your .env file.")

fake = Faker()
rng = np.random.default_rng(42)
random.seed(42)
Faker.seed(42)

# ---------------------------------------------------------------------------
# Reference / master data definitions
# ---------------------------------------------------------------------------

CATEGORIES = [
    # name,                    type
    ("Electronics",            "mixed"),
    ("Software/SaaS",          "mixed"),
    ("Professional Services",  "mixed"),
    ("Hardware",               "mixed"),
    ("Consulting",             "mixed"),
    ("Marketing Expenses",     "expense"),
    ("Operations",             "expense"),
    ("HR",                     "expense"),
    ("IT Infrastructure",      "expense"),
    ("R&D",                    "expense"),
]

REGIONS = ["North", "South", "East", "West", "Central"]

DEPARTMENTS = ["Sales", "Marketing", "Operations", "Finance", "HR", "IT", "R&D"]

SEGMENTS = ["enterprise", "mid-market", "smb"]

PAYMENT_METHODS = ["bank_transfer", "credit_card", "cash", "cheque"]

# Category indices (0-based inside CATEGORIES list) for revenue-generating categories
REVENUE_CATEGORY_NAMES = {"Electronics", "Software/SaaS", "Professional Services", "Hardware", "Consulting"}
EXPENSE_CATEGORY_NAMES = {"Marketing Expenses", "Operations", "HR", "IT Infrastructure", "R&D"}

# ---------------------------------------------------------------------------
# Date range helpers
# ---------------------------------------------------------------------------

START_DATE = date(2023, 1, 1)
END_DATE   = date(2025, 3, 31)

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=int(rng.integers(0, delta + 1)))

def dates_in_range(start: date, end: date):
    """Yield every date from start to end inclusive."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def seasonal_weight(d: date) -> float:
    """Scenario G: Q4 ~1.35x, Q1 ~0.75x, Q2/Q3 ~1.0x."""
    q = (d.month - 1) // 3 + 1
    return {1: 0.75, 2: 1.00, 3: 1.00, 4: 1.35}[q]

def yoy_growth_factor(d: date) -> float:
    """Scenario A: +15 % in 2024, +8 % in 2025 (partial year)."""
    if d.year == 2023:
        return 1.00
    elif d.year == 2024:
        return 1.15
    else:
        return 1.15 * 1.08

def expense_growth_factor(d: date) -> float:
    """Scenario B: expenses grow faster than revenue in Q3 2024."""
    base = yoy_growth_factor(d)
    if d.year == 2024 and (d.month in (7, 8, 9)):
        return base * 1.12   # extra 12 % on top
    return base

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def connect() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn

def batch_insert(cur, sql: str, rows: list, chunk: int = 500):
    """Insert rows in chunks using execute_values."""
    for i in range(0, len(rows), chunk):
        psycopg2.extras.execute_values(cur, sql, rows[i : i + chunk])

# ---------------------------------------------------------------------------
# Step 1 – Reference data
# ---------------------------------------------------------------------------

def seed_reference_data(cur) -> dict:
    """Insert categories, regions, departments. Return id maps."""
    print("  [1/7] Seeding reference data …")

    cur.executemany(
        "INSERT INTO categories(name, type) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
        CATEGORIES,
    )
    cur.execute("SELECT category_id, name FROM categories")
    cat_map = {row[1]: row[0] for row in cur.fetchall()}   # name → id

    cur.executemany(
        "INSERT INTO regions(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        [(r,) for r in REGIONS],
    )
    cur.execute("SELECT region_id, name FROM regions")
    reg_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.executemany(
        "INSERT INTO departments(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        [(d,) for d in DEPARTMENTS],
    )
    cur.execute("SELECT department_id, name FROM departments")
    dept_map = {row[1]: row[0] for row in cur.fetchall()}

    return {"cat": cat_map, "reg": reg_map, "dept": dept_map}

# ---------------------------------------------------------------------------
# Step 2 – Customers (50)
# ---------------------------------------------------------------------------

def seed_customers(cur, ref: dict) -> list[int]:
    print("  [2/7] Seeding 50 customers …")
    rows = []
    for _ in range(50):
        region_name  = rng.choice(REGIONS)
        segment      = rng.choice(SEGMENTS)
        signup       = random_date(date(2018, 1, 1), date(2022, 12, 31))
        is_active    = bool(rng.choice([True, True, True, False]))
        rows.append((
            fake.company(),
            ref["reg"][region_name],
            segment,
            signup,
            is_active,
        ))
    sql = """
        INSERT INTO customers(name, region_id, segment, signup_date, is_active)
        VALUES %s
        ON CONFLICT DO NOTHING
        RETURNING customer_id
    """
    psycopg2.extras.execute_values(cur, sql, rows)
    cur.execute("SELECT customer_id FROM customers ORDER BY customer_id")
    return [r[0] for r in cur.fetchall()]

# ---------------------------------------------------------------------------
# Step 3 – Vendors (20)
# ---------------------------------------------------------------------------

def seed_vendors(cur, ref: dict) -> list[int]:
    print("  [3/7] Seeding 20 vendors …")
    # Distribute vendors evenly across expense categories
    expense_cats = [c for c in EXPENSE_CATEGORY_NAMES if c in ref["cat"]]
    rows = []
    for i in range(20):
        cat_name    = expense_cats[i % len(expense_cats)]
        region_name = rng.choice(REGIONS)
        rows.append((
            fake.company() + " LLC",
            ref["cat"][cat_name],
            ref["reg"][region_name],
            True,
        ))
    sql = """
        INSERT INTO vendors(name, category_id, region_id, is_active)
        VALUES %s
        ON CONFLICT DO NOTHING
        RETURNING vendor_id
    """
    psycopg2.extras.execute_values(cur, sql, rows)
    cur.execute("SELECT vendor_id FROM vendors ORDER BY vendor_id")
    return [r[0] for r in cur.fetchall()]

# ---------------------------------------------------------------------------
# Step 4 – Products (30)
# ---------------------------------------------------------------------------

PRODUCT_TEMPLATES = [
    # name prefix,              category,               base_cost, base_price
    ("Enterprise Server",       "Hardware",              1800,  3200),
    ("Network Switch Pro",      "Hardware",               400,   750),
    ("SaaS Platform License",   "Software/SaaS",          120,   450),
    ("Cloud Storage Suite",     "Software/SaaS",           60,   180),
    ("Analytics Dashboard",     "Software/SaaS",           90,   320),
    ("4K Display",              "Electronics",             280,   550),
    ("Laptop Workstation",      "Electronics",             900,  1600),
    ("Smart UPS",               "Electronics",             350,   650),
    ("Consulting Package Basic","Consulting",              200,   800),
    ("Consulting Package Pro",  "Consulting",              500,  1800),
    ("IT Audit Service",        "Professional Services",   400,  1200),
    ("Security Assessment",     "Professional Services",   600,  2000),
    ("Data Migration Service",  "Professional Services",   300,  1000),
    ("Managed IT Support",      "IT Infrastructure",       150,   600),
    ("VPN Gateway",             "Hardware",                250,   480),
    ("Server Rack",             "Hardware",                700,  1300),
    ("CRM Software",            "Software/SaaS",           100,   350),
    ("ERP Module",              "Software/SaaS",           200,   700),
    ("Drone Sensor Kit",        "Electronics",             600,  1100),
    ("Tablet Bundle",           "Electronics",             400,   780),
    ("Training Workshop",       "Consulting",              150,   500),
    ("Cloud Backup",            "Software/SaaS",            50,   160),
    ("Firewall Appliance",      "Hardware",                450,   900),
    ("R&D Lab Equipment",       "R&D",                    1500,  2800),
    ("Marketing Analytics Tool","Software/SaaS",            80,   280),
    ("Legal Compliance Module", "Professional Services",   350,  1100),
    ("GPU Compute Card",        "Electronics",            1200,  2100),
    ("Wireless Access Point",   "Hardware",                120,   240),
    ("HR Software Suite",       "Software/SaaS",           110,   380),
    ("IoT Gateway",             "Electronics",             300,   580),
]

def seed_products(cur, ref: dict) -> list[dict]:
    print("  [3/7] Seeding 30 products …")
    rows = []
    for name, cat_name, base_cost, base_price in PRODUCT_TEMPLATES:
        # slight price jitter
        cost  = round(base_cost  * rng.uniform(0.9, 1.1), 2)
        price = round(base_price * rng.uniform(0.9, 1.1), 2)
        rows.append((name, ref["cat"][cat_name], cost, price, True))

    sql = """
        INSERT INTO products(name, category_id, unit_cost, selling_price, is_active)
        VALUES %s
        ON CONFLICT DO NOTHING
        RETURNING product_id, category_id, unit_cost, selling_price
    """
    psycopg2.extras.execute_values(cur, sql, rows)
    cur.execute("SELECT product_id, category_id, unit_cost, selling_price FROM products")
    return [
        {"product_id": r[0], "category_id": r[1], "unit_cost": float(r[2]), "selling_price": float(r[3])}
        for r in cur.fetchall()
    ]

# ---------------------------------------------------------------------------
# Step 5 – Transactions (~3 500)
# ---------------------------------------------------------------------------

def _product_margin_factor(product: dict, d: date, cat_name_map: dict) -> tuple[float, float]:
    """
    Return (cost_factor, price_factor).
    Scenario C: Electronics gross margin declines in H2 2024 by raising cost.
    Scenario E: Software/SaaS gets a price premium in 2024.
    """
    cost_f  = 1.0
    price_f = 1.0
    cat_name = cat_name_map.get(product["category_id"], "")
    if cat_name == "Electronics" and d.year == 2024 and d.month >= 7:
        cost_f = rng.uniform(1.18, 1.30)   # cost creep
    if cat_name == "Software/SaaS" and d.year == 2024:
        price_f = rng.uniform(1.10, 1.25)  # premium pricing
    return cost_f, price_f


def seed_transactions(cur, ref: dict, customers: list, products: list) -> list[uuid.UUID]:
    print("  [4/7] Seeding ~3 500 transactions …")

    cat_name_map = {v: k for k, v in ref["cat"].items()}  # id → name
    rev_cat_ids  = {ref["cat"][c] for c in REVENUE_CATEGORY_NAMES if c in ref["cat"]}
    dept_ids     = list(ref["dept"].values())
    reg_ids      = list(ref["reg"].values())

    # Revenue products only
    rev_products = [p for p in products if p["category_id"] in rev_cat_ids]

    rows = []
    target = 3500
    # Spread dates using pandas date_range for even distribution
    all_dates = pd.date_range(START_DATE, END_DATE, freq="D")
    # Weighted by seasonal factor
    weights = np.array([seasonal_weight(d.date()) * yoy_growth_factor(d.date()) for d in all_dates])
    weights /= weights.sum()
    chosen_dates = rng.choice(all_dates, size=target, replace=True, p=weights)

    for pd_date in chosen_dates:
        d = pd_date.date()
        product  = rng.choice(rev_products)
        customer = rng.choice(customers)
        qty      = int(rng.integers(1, 6))
        cost_f, price_f = _product_margin_factor(product, d, cat_name_map)
        unit_cost  = round(product["unit_cost"]    * cost_f,  2)
        unit_price = round(product["selling_price"] * price_f, 2)
        discount   = round(float(rng.choice([0, 0, 0, 5, 10, 15], p=[0.5, 0.15, 0.15, 0.1, 0.05, 0.05])), 2)
        amount     = round(unit_price * qty * (1 - discount / 100), 2)
        cost       = round(unit_cost  * qty, 2)
        txn_type   = rng.choice(["sale", "sale", "sale", "sale", "refund", "adjustment"],
                                 p=[0.80, 0.08, 0.05, 0.03, 0.03, 0.01])
        if txn_type == "refund":
            amount = -abs(amount)
            cost   = -abs(cost)
        status = rng.choice(["completed", "completed", "completed", "pending", "cancelled"],
                             p=[0.85, 0.05, 0.04, 0.04, 0.02])
        rows.append((
            str(uuid.uuid4()),
            d,
            customer,
            None,                        # vendor_id (sales have no vendor)
            product["product_id"],
            product["category_id"],
            rng.choice(reg_ids),
            rng.choice(dept_ids),
            txn_type,
            amount,
            cost,
            qty,
            discount,
            rng.choice(PAYMENT_METHODS),
            status,
        ))

    sql = """
        INSERT INTO transactions(
            transaction_id, transaction_date, customer_id, vendor_id, product_id,
            category_id, region_id, department_id, transaction_type, amount, cost,
            quantity, discount_pct, payment_method, status
        ) VALUES %s ON CONFLICT DO NOTHING
    """
    batch_insert(cur, sql, rows)
    print(f"       → {len(rows)} transactions inserted")
    return [uuid.UUID(r[0]) for r in rows]

# ---------------------------------------------------------------------------
# Step 6 – Expenses (~1 800)
# ---------------------------------------------------------------------------

def seed_expenses(cur, ref: dict, vendors: list):
    print("  [5/7] Seeding ~1 800 expenses …")

    exp_cat_ids  = [ref["cat"][c] for c in EXPENSE_CATEGORY_NAMES if c in ref["cat"]]
    dept_ids     = list(ref["dept"].values())
    ops_dept_id  = ref["dept"].get("Operations")
    mkt_dept_id  = ref["dept"].get("Marketing")
    ops_cat_id   = ref["cat"].get("Operations")

    all_dates = pd.date_range(START_DATE, END_DATE, freq="D")
    weights   = np.array([expense_growth_factor(d.date()) for d in all_dates])
    weights  /= weights.sum()
    chosen_dates = rng.choice(all_dates, size=1800, replace=True, p=weights)

    rows = []
    for pd_date in chosen_dates:
        d = pd_date.date()
        cat_id  = rng.choice(exp_cat_ids)
        dept_id = rng.choice(dept_ids)
        vendor  = rng.choice(vendors) if rng.random() < 0.65 else None

        base_amount = float(rng.uniform(200, 8000))

        # Scenario F: Oct 2024 Operations spike (~3x normal)
        if d.year == 2024 and d.month == 10 and dept_id == ops_dept_id:
            base_amount *= rng.uniform(2.8, 3.4)

        # Scenario H: Budget overruns — Marketing and Operations Q3-Q4 2024
        if d.year == 2024 and d.month >= 7:
            if dept_id in (mkt_dept_id, ops_dept_id):
                base_amount *= rng.uniform(1.3, 1.6)

        amount  = round(base_amount, 2)
        status  = rng.choice(["approved", "approved", "pending", "rejected"],
                              p=[0.75, 0.10, 0.10, 0.05])
        rows.append((
            str(uuid.uuid4()),
            d,
            cat_id,
            dept_id,
            vendor,
            amount,
            fake.sentence(nb_words=6),
            status,
        ))

    sql = """
        INSERT INTO expenses(expense_id, expense_date, category_id, department_id,
                             vendor_id, amount, description, status)
        VALUES %s ON CONFLICT DO NOTHING
    """
    batch_insert(cur, sql, rows)
    print(f"       → {len(rows)} expense records inserted")

# ---------------------------------------------------------------------------
# Step 7 – Budgets (24 months × 7 depts × categories)
# ---------------------------------------------------------------------------

def seed_budgets(cur, ref: dict):
    print("  [6/7] Seeding budgets (2023–2024) …")

    rows = []
    cat_ids  = list(ref["cat"].values())
    dept_ids = list(ref["dept"].values())

    mkt_dept_id = ref["dept"].get("Marketing")
    ops_dept_id = ref["dept"].get("Operations")

    for year in (2023, 2024):
        for month in range(1, 13):
            for dept_id in dept_ids:
                for cat_id in rng.choice(cat_ids, size=3, replace=False):
                    base = float(rng.uniform(15_000, 120_000))

                    # Scenario H: intentionally set budgets *lower* than what
                    # expenses will actually be in Q3-Q4 2024 for Marketing/Ops
                    if year == 2024 and month >= 7 and dept_id in (mkt_dept_id, ops_dept_id):
                        base *= 0.70   # budget set too low → overrun

                    rows.append((
                        str(uuid.uuid4()),
                        year,
                        month,
                        cat_id,
                        dept_id,
                        round(base, 2),
                    ))

    sql = """
        INSERT INTO budgets(budget_id, period_year, period_month, category_id, department_id, budget_amount)
        VALUES %s ON CONFLICT ON CONSTRAINT uq_budget_period_cat_dept DO NOTHING
    """
    batch_insert(cur, sql, rows)
    print(f"       → {len(rows)} budget records inserted")

# ---------------------------------------------------------------------------
# Step 8 – Invoices (~900)
# ---------------------------------------------------------------------------

def seed_invoices(cur, ref: dict, customers: list) -> list[uuid.UUID]:
    print("  [6/7] Seeding ~900 invoices …")

    rows  = []
    today = date.today()

    all_dates    = pd.date_range(START_DATE, END_DATE, freq="D")
    inv_weights  = np.array([yoy_growth_factor(d.date()) * seasonal_weight(d.date())
                             for d in all_dates])
    inv_weights /= inv_weights.sum()
    chosen_dates = rng.choice(all_dates, size=900, replace=True, p=inv_weights)

    inv_ids = []
    for pd_date in chosen_dates:
        inv_date   = pd_date.date()
        customer   = rng.choice(customers)
        net_days   = int(rng.choice([30, 45, 60], p=[0.60, 0.25, 0.15]))
        due_date   = inv_date + timedelta(days=net_days)
        amount     = round(float(rng.uniform(1_000, 80_000)), 2)
        inv_id     = str(uuid.uuid4())

        # Scenario D: late payments — increase aging in 2024 H2
        aging_bias = 1.0
        if inv_date.year == 2024 and inv_date.month >= 7:
            aging_bias = 1.6  # 60 % more likely to be overdue / partially paid

        days_past_due = (today - due_date).days

        roll = rng.random() * aging_bias
        if due_date > today:
            # Future or current — could still be unpaid or partially paid
            if roll < 0.55:
                status, paid, pay_date = "unpaid", 0.0, None
            elif roll < 0.80:
                partial = round(amount * float(rng.uniform(0.1, 0.8)), 2)
                status, paid, pay_date = "partial", partial, None
            else:
                status, paid, pay_date = "paid", amount, inv_date + timedelta(days=int(rng.integers(1, net_days)))
        elif days_past_due <= 30:
            if roll < 0.40:
                status, paid, pay_date = "paid", amount, due_date - timedelta(days=int(rng.integers(0, 5)))
            elif roll < 0.65:
                status, paid, pay_date = "overdue", 0.0, None
            else:
                partial = round(amount * float(rng.uniform(0.3, 0.9)), 2)
                status, paid, pay_date = "partial", partial, None
        elif days_past_due <= 90:
            # Scenario D materialises here
            if roll < 0.35:
                status, paid, pay_date = "paid", amount, due_date + timedelta(days=int(rng.integers(1, 30)))
            else:
                status, paid, pay_date = "overdue", 0.0, None
        else:
            # >90 days — mostly overdue / bad debt
            if roll < 0.20:
                status, paid, pay_date = "paid", amount, due_date + timedelta(days=int(rng.integers(30, 90)))
            elif roll < 0.40:
                partial = round(amount * float(rng.uniform(0.1, 0.5)), 2)
                status, paid, pay_date = "partial", partial, None
            else:
                status, paid, pay_date = "overdue", 0.0, None

        rows.append((inv_id, customer, inv_date, due_date, amount, paid, pay_date, status))
        inv_ids.append(uuid.UUID(inv_id))

    sql = """
        INSERT INTO invoices(invoice_id, customer_id, invoice_date, due_date,
                             invoice_amount, paid_amount, payment_date, payment_status)
        VALUES %s ON CONFLICT DO NOTHING
    """
    batch_insert(cur, sql, rows)
    print(f"       → {len(rows)} invoices inserted")
    return inv_ids

# ---------------------------------------------------------------------------
# Step 9 – Cash flows (~2 500)
# ---------------------------------------------------------------------------

def seed_cash_flows(cur, ref: dict, txn_ids: list, inv_ids: list):
    print("  [7/7] Seeding ~2 500 cash flow records …")

    cat_ids  = list(ref["cat"].values())
    dept_ids = list(ref["dept"].values())
    rows     = []

    # A) Inflows tied to a sample of completed transactions
    sample_txn = rng.choice(txn_ids, size=min(1200, len(txn_ids)), replace=False)
    for txn_id in sample_txn:
        d = random_date(START_DATE, END_DATE)
        rows.append((
            str(uuid.uuid4()),
            d,
            "inflow",
            rng.choice(cat_ids),
            rng.choice(dept_ids),
            round(float(rng.uniform(500, 50_000)), 2),
            "Transaction settlement",
            str(txn_id),
        ))

    # B) Outflows tied to a sample of invoices (payment received)
    sample_inv = rng.choice(inv_ids, size=min(700, len(inv_ids)), replace=False)
    for inv_id in sample_inv:
        d = random_date(START_DATE, END_DATE)
        rows.append((
            str(uuid.uuid4()),
            d,
            "outflow",
            rng.choice(cat_ids),
            rng.choice(dept_ids),
            round(float(rng.uniform(1_000, 60_000)), 2),
            "Vendor payment / expense disbursement",
            str(inv_id),
        ))

    # C) Standalone cash movements (payroll, rent, taxes, etc.)
    standalone = 600
    all_dates  = pd.date_range(START_DATE, END_DATE, freq="D")
    chosen_cf  = rng.choice(all_dates, size=standalone, replace=True)
    for pd_date in chosen_cf:
        d = pd_date.date()
        flow_type = rng.choice(["inflow", "outflow"], p=[0.45, 0.55])
        rows.append((
            str(uuid.uuid4()),
            d,
            flow_type,
            rng.choice(cat_ids) if rng.random() > 0.2 else None,
            rng.choice(dept_ids) if rng.random() > 0.2 else None,
            round(float(rng.uniform(500, 25_000)), 2),
            fake.sentence(nb_words=5),
            None,
        ))

    sql = """
        INSERT INTO cash_flows(cashflow_id, flow_date, flow_type, category_id,
                               department_id, amount, description, reference_id)
        VALUES %s ON CONFLICT DO NOTHING
    """
    batch_insert(cur, sql, rows)
    print(f"       → {len(rows)} cash flow records inserted")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  FinGuard AI — Seed Data Generator")
    print("=" * 60)

    conn = connect()
    try:
        with conn:
            cur = conn.cursor()

            ref       = seed_reference_data(cur)
            customers = seed_customers(cur, ref)
            vendors   = seed_vendors(cur, ref)
            products  = seed_products(cur, ref)
            txn_ids   = seed_transactions(cur, ref, customers, products)
            seed_expenses(cur, ref, vendors)
            seed_budgets(cur, ref)
            inv_ids   = seed_invoices(cur, ref, customers)
            seed_cash_flows(cur, ref, txn_ids, inv_ids)

        print()
        print("=" * 60)
        print("  Seed completed successfully.")
        print("=" * 60)

    except Exception as exc:
        conn.rollback()
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
