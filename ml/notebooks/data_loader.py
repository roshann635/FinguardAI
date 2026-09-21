"""Data loader helper for FinGuard AI EDA notebooks and model benchmarks.

Provides offline-first access to FinGuard financial data:
1. Attempts to connect to PostgreSQL if DATABASE_URL is set and reachable.
2. If PostgreSQL is unreachable or not configured, creates/uses a local SQLite
   database (data/finguard_demo.sqlite) seeded with the deterministic seed generator.
"""

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQLITE_PATH = BASE_DIR / "data" / "finguard_demo.sqlite"


def get_connection():
    """Return a database connection (PostgreSQL if available, else SQLite)."""
    pg_url = os.getenv("DATABASE_URL")
    if pg_url and "postgresql" in pg_url:
        try:
            import psycopg2
            conn = psycopg2.connect(pg_url)
            # test connection
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn, "postgresql"
        except Exception:
            pass

    # Fallback to local SQLite
    os.makedirs(SQLITE_PATH.parent, exist_ok=True)
    if not SQLITE_PATH.exists():
        _generate_sqlite_seed(SQLITE_PATH)

    conn = sqlite3.connect(SQLITE_PATH)
    return conn, "sqlite"


def load_dataset() -> Dict[str, pd.DataFrame]:
    """Load all core tables as pandas DataFrames."""
    conn, engine_type = get_connection()
    try:
        tables = [
            "transactions",
            "expenses",
            "invoices",
            "cash_flows",
            "budgets",
            "customers",
            "vendors",
            "products",
            "categories",
            "departments",
            "regions",
        ]
        data = {}
        for t in tables:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {t}", conn)
                data[t] = df
            except Exception as e:
                data[t] = pd.DataFrame()

        # Type conversions for dates
        if not data["transactions"].empty and "transaction_date" in data["transactions"].columns:
            data["transactions"]["transaction_date"] = pd.to_datetime(data["transactions"]["transaction_date"])
        if not data["expenses"].empty and "expense_date" in data["expenses"].columns:
            data["expenses"]["expense_date"] = pd.to_datetime(data["expenses"]["expense_date"])
        if not data["invoices"].empty and "invoice_date" in data["invoices"].columns:
            data["invoices"]["invoice_date"] = pd.to_datetime(data["invoices"]["invoice_date"])
            data["invoices"]["due_date"] = pd.to_datetime(data["invoices"]["due_date"])
        if not data["cash_flows"].empty and "flow_date" in data["cash_flows"].columns:
            data["cash_flows"]["flow_date"] = pd.to_datetime(data["cash_flows"]["flow_date"])

        return data
    finally:
        conn.close()


def _generate_sqlite_seed(sqlite_file: Path):
    """Seed the SQLite database with realistic deterministic financial data."""
    print(f"Generating deterministic demo dataset in {sqlite_file}...")
    rng = np.random.default_rng(42)

    conn = sqlite3.connect(sqlite_file)
    cur = conn.cursor()

    # DDL
    cur.executescript("""
        CREATE TABLE categories (category_id INTEGER PRIMARY KEY, name TEXT, type TEXT);
        CREATE TABLE departments (department_id INTEGER PRIMARY KEY, name TEXT, budget_code TEXT);
        CREATE TABLE regions (region_id INTEGER PRIMARY KEY, name TEXT, code TEXT);
        CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, industry TEXT, segment TEXT, credit_limit REAL, payment_terms INTEGER);
        CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, payment_terms INTEGER);
        CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, unit_price REAL, unit_cost REAL);
        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY, transaction_date TEXT, customer_id INTEGER,
            product_id INTEGER, category_id INTEGER, region_id INTEGER, department_id INTEGER,
            transaction_type TEXT, amount REAL, cost REAL, quantity INTEGER, discount_pct REAL,
            payment_method TEXT, status TEXT
        );
        CREATE TABLE expenses (
            expense_id TEXT PRIMARY KEY, expense_date TEXT, category_id INTEGER,
            department_id INTEGER, vendor_id INTEGER, amount REAL, status TEXT, description TEXT
        );
        CREATE TABLE invoices (
            invoice_id TEXT PRIMARY KEY, customer_id INTEGER, invoice_date TEXT, due_date TEXT,
            invoice_amount REAL, paid_amount REAL, payment_date TEXT, payment_status TEXT
        );
        CREATE TABLE cash_flows (
            flow_id TEXT PRIMARY KEY, flow_date TEXT, flow_type TEXT, category_id INTEGER,
            department_id INTEGER, amount REAL, description TEXT, reference_id TEXT
        );
        CREATE TABLE budgets (
            budget_id TEXT PRIMARY KEY, fiscal_year INTEGER, quarter INTEGER, category_id INTEGER,
            department_id INTEGER, budgeted_amount REAL, actual_amount REAL
        );
    """)

    # Seed reference data
    categories = [
        (1, "Electronics", "mixed"),
        (2, "Software/SaaS", "mixed"),
        (3, "Professional Services", "mixed"),
        (4, "Hardware", "mixed"),
        (5, "Consulting", "mixed"),
        (6, "Marketing Expenses", "expense"),
        (7, "Operations", "expense"),
        (8, "HR", "expense"),
        (9, "IT Infrastructure", "expense"),
        (10, "R&D", "expense"),
    ]
    cur.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories)

    departments = [
        (1, "Sales", "SALES-01"),
        (2, "Marketing", "MKT-01"),
        (3, "Operations", "OPS-01"),
        (4, "Finance", "FIN-01"),
        (5, "HR", "HR-01"),
        (6, "IT", "IT-01"),
        (7, "R&D", "RND-01"),
    ]
    cur.executemany("INSERT INTO departments VALUES (?, ?, ?)", departments)

    regions = [
        (1, "North", "NO"),
        (2, "South", "SO"),
        (3, "East", "EA"),
        (4, "West", "WE"),
        (5, "Central", "CE"),
    ]
    cur.executemany("INSERT INTO regions VALUES (?, ?, ?)", regions)

    # Customers (50)
    segments = ["enterprise", "mid-market", "smb"]
    industries = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"]
    customers = []
    for cid in range(1, 51):
        seg = rng.choice(segments, p=[0.25, 0.45, 0.30])
        limit = 250000.0 if seg == "enterprise" else (75000.0 if seg == "mid-market" else 20000.0)
        terms = 60 if seg == "enterprise" else 30
        customers.append((cid, f"Client {cid:03d} Corp", str(rng.choice(industries)), seg, limit, terms))
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)

    # Vendors (20)
    vendors = []
    for vid in range(1, 21):
        cat_id = int(rng.choice([6, 7, 8, 9, 10]))
        vendors.append((vid, f"Vendor {vid:02d} Ltd", cat_id, 30))
    cur.executemany("INSERT INTO vendors VALUES (?, ?, ?, ?)", vendors)

    # Products (25)
    products = []
    prod_names = [
        ("Cloud Platform Pro", 2, 1200.0, 300.0),
        ("Analytics Suite Enterprise", 2, 2500.0, 500.0),
        ("Enterprise Server Rack", 1, 8000.0, 5200.0),
        ("IoT Edge Gateway", 1, 1500.0, 950.0),
        ("AI Inference Accelerator", 1, 3500.0, 2400.0),
        ("Financial Advisory Retainer", 3, 5000.0, 2000.0),
        ("Architecture Consulting", 5, 4000.0, 1600.0),
        ("Edge Network Switch", 4, 1800.0, 1100.0),
        ("Cybersecurity Audit", 3, 6000.0, 2500.0),
        ("Data Migration Service", 5, 3000.0, 1200.0),
    ]
    for pid, (pname, cat_id, uprice, ucost) in enumerate(prod_names, 1):
        products.append((pid, pname, cat_id, uprice, ucost))
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

    # Transactions & Invoices generation (Jan 2023 – Mar 2025: 820 days)
    start_dt = pd.Timestamp("2023-01-01")
    end_dt = pd.Timestamp("2025-03-31")
    days_range = pd.date_range(start_dt, end_dt)

    transactions = []
    invoices = []
    expenses = []
    cash_flows = []

    import uuid

    inv_counter = 1
    for day in days_range:
        # Seasonality factor: Q4 high (1.35x), Q1 low (0.75x)
        q = (day.month - 1) // 3 + 1
        season = {1: 0.8, 2: 1.0, 3: 1.05, 4: 1.35}[q]
        # YoY growth factor: 2023 = 1.0, 2024 = 1.15, 2025 = 1.25
        yoy = 1.0 if day.year == 2023 else (1.15 if day.year == 2024 else 1.25)
        # Daily sales count
        n_sales = int(rng.poisson(lam=5.0 * season * yoy))

        for _ in range(n_sales):
            p_idx = int(rng.integers(0, len(products)))
            pid, pname, cat_id, unit_p, unit_c = products[p_idx]
            qty = int(rng.integers(1, 5))
            discount = float(rng.choice([0.0, 0.05, 0.10, 0.15], p=[0.6, 0.2, 0.15, 0.05]))
            gross = round(unit_p * qty, 2)
            net_amt = round(gross * (1 - discount), 2)
            cost_amt = round(unit_c * qty, 2)
            
            # Scenario C: In H2 2024, Electronics margin compresses (higher cost)
            if cat_id == 1 and day.year == 2024 and day.month >= 7:
                cost_amt = round(cost_amt * 1.25, 2)

            cid = int(rng.integers(1, 51))
            reg_id = int(rng.integers(1, 6))
            dep_id = 1  # Sales
            pmethod = str(rng.choice(["bank_transfer", "credit_card", "cash", "cheque"]))
            tx_id = str(uuid.uuid4())

            transactions.append((
                tx_id, day.strftime("%Y-%m-%d"), cid, pid, cat_id, reg_id, dep_id,
                "sale", net_amt, cost_amt, qty, discount * 100, pmethod, "completed"
            ))

            # 40% of sales generate an invoice
            if rng.random() < 0.40:
                due = day + pd.Timedelta(days=30)
                # Aging scenario: older invoices from late 2024 remain unpaid
                if day.year == 2024 and day.month in [10, 11, 12]:
                    paid = 0.0 if rng.random() < 0.35 else net_amt
                else:
                    paid = net_amt if rng.random() < 0.85 else 0.0

                status = "paid" if paid >= net_amt else ("overdue" if day < pd.Timestamp("2025-03-01") else "unpaid")
                invoices.append((
                    str(uuid.uuid4()), cid, day.strftime("%Y-%m-%d"), due.strftime("%Y-%m-%d"),
                    net_amt, paid, (day + pd.Timedelta(days=15)).strftime("%Y-%m-%d") if paid > 0 else None, status
                ))

        # Daily Expenses
        n_exp = int(rng.integers(1, 4))
        for _ in range(n_exp):
            exp_cat = int(rng.choice([6, 7, 8, 9, 10]))
            dept = int(rng.choice([2, 3, 4, 5, 6, 7]))
            base_amt = float(rng.uniform(300, 3500))

            # Scenario F: Oct 2024 Operations expense spike (~3x normal)
            if day.year == 2024 and day.month == 10 and dept == 3:
                base_amt *= 3.2

            # Scenario B: Q3 2024 expense growth outpacing revenue
            if day.year == 2024 and day.month in [7, 8, 9]:
                base_amt *= 1.30

            amt = round(base_amt, 2)
            vid = int(rng.integers(1, 21))
            expenses.append((
                str(uuid.uuid4()), day.strftime("%Y-%m-%d"), exp_cat, dept, vid,
                amt, "approved", f"Operational expense {day.strftime('%b %Y')}"
            ))

    cur.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", transactions)
    cur.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?)", invoices)
    cur.executemany("INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?, ?, ?)", expenses)

    # Cash flows (derived)
    for t in transactions[::3]:  # sample
        cash_flows.append((str(uuid.uuid4()), t[1], "inflow", t[4], t[6], t[8], "Customer receipt", t[0]))
    for e in expenses[::2]:
        cash_flows.append((str(uuid.uuid4()), e[1], "outflow", e[2], e[3], e[5], "Vendor disbursement", e[0]))
    cur.executemany("INSERT INTO cash_flows VALUES (?, ?, ?, ?, ?, ?, ?, ?)", cash_flows)

    # Budgets (2023, 2024, 2025)
    budgets = []
    for yr in [2023, 2024, 2025]:
        for qtr in [1, 2, 3, 4]:
            if yr == 2025 and qtr > 1:
                continue
            for cat_id in [6, 7, 8, 9, 10]:
                for dept_id in [2, 3, 6, 7]:
                    b_amt = 50000.0 * (1.1 if yr == 2024 else 1.0)
                    # Scenario H: Overruns in Marketing and Ops Q3-Q4 2024
                    mult = 1.35 if (yr == 2024 and qtr in [3, 4] and dept_id in [2, 3]) else 0.95
                    a_amt = round(b_amt * mult, 2)
                    budgets.append((str(uuid.uuid4()), yr, qtr, cat_id, dept_id, b_amt, a_amt))
    cur.executemany("INSERT INTO budgets VALUES (?, ?, ?, ?, ?, ?, ?)", budgets)

    conn.commit()
    conn.close()
    print(f"Generated {len(transactions)} transactions, {len(expenses)} expenses, {len(invoices)} invoices into {sqlite_file}.")


if __name__ == "__main__":
    data = load_dataset()
    for k, v in data.items():
        print(f"Loaded {k}: {len(v)} records")
