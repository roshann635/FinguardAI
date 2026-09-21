"""FinGuard AI — SQLite Seed Generator using SQLAlchemy ORM.

Generates the complete synthetic financial dataset (Jan 2023 – Mar 2025)
matching the exact SQLAlchemy schema for offline/local execution.
"""

import datetime
import os
import random
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, event, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Setup UUID mapping for SQLite
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, TypeDecorator

class _UUIDString(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def __init__(self, as_uuid=True, *args, **kwargs):
        self.as_uuid = as_uuid
        super().__init__()
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

import sqlalchemy.dialects.postgresql as _pg_dialect
_pg_dialect.UUID = _UUIDString

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.database.connection import Base
from app.models import (
    Budget,
    CashFlow,
    Category,
    Customer,
    Department,
    Expense,
    Invoice,
    Product,
    Region,
    Transaction,
    Vendor,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQLITE_PATH = BASE_DIR / "data" / "finguard_demo.sqlite"


def generate_sqlite_db():
    print(f"Creating SQLite database at: {SQLITE_PATH}")
    if SQLITE_PATH.exists():
        try:
            os.remove(SQLITE_PATH)
        except Exception:
            pass

    engine = create_engine(
        f"sqlite:///{SQLITE_PATH}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    from sqlalchemy import CheckConstraint
    for table in Base.metadata.tables.values():
        table.constraints = {c for c in table.constraints if not isinstance(c, CheckConstraint)}

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    rng = np.random.default_rng(42)
    random.seed(42)

    START_DATE = datetime.date(2023, 1, 1)
    END_DATE = datetime.date(2025, 3, 31)

    def random_date(start, end):
        delta = (end - start).days
        return start + datetime.timedelta(days=int(rng.integers(0, delta + 1)))

    # 1. Categories
    CATEGORIES = [
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
    for cid, name, ctype in CATEGORIES:
        session.add(Category(category_id=cid, name=name, type=ctype))

    # 2. Regions
    REGIONS = [(1, "North"), (2, "South"), (3, "East"), (4, "West"), (5, "Central")]
    for rid, name in REGIONS:
        session.add(Region(region_id=rid, name=name))

    # 3. Departments
    DEPARTMENTS = [
        (1, "Sales"), (2, "Marketing"), (3, "Operations"),
        (4, "Finance"), (5, "HR"), (6, "IT"), (7, "R&D")
    ]
    for did, name in DEPARTMENTS:
        session.add(Department(department_id=did, name=name))

    session.flush()

    # 4. Customers
    SEGMENTS = ["enterprise", "mid-market", "smb"]
    customers = []
    for i in range(1, 51):
        c = Customer(
            customer_id=i,
            name=f"Client {i:03d} Corp",
            region_id=int(rng.integers(1, 6)),
            segment=str(rng.choice(SEGMENTS)),
            signup_date=random_date(datetime.date(2018, 1, 1), datetime.date(2022, 12, 31)),
            is_active=True,
        )
        customers.append(c)
        session.add(c)

    # 5. Vendors
    vendors = []
    for i in range(1, 21):
        v = Vendor(
            vendor_id=i,
            name=f"Vendor {i:02d} Ltd",
            category_id=int(rng.integers(6, 11)),
            region_id=int(rng.integers(1, 6)),
            is_active=True,
        )
        vendors.append(v)
        session.add(v)

    # 6. Products
    PRODUCT_TEMPLATES = [
        ("Enterprise Server", 4, 1800, 3200),
        ("Network Switch Pro", 4, 400, 750),
        ("SaaS Platform License", 2, 120, 450),
        ("Cloud Storage Suite", 2, 60, 180),
        ("Analytics Dashboard", 2, 90, 320),
        ("4K Display", 1, 280, 550),
        ("Laptop Workstation", 1, 900, 1600),
        ("Smart UPS", 1, 350, 650),
        ("Consulting Package Basic", 5, 200, 800),
        ("Consulting Package Pro", 5, 500, 1800),
        ("IT Audit Service", 3, 400, 1200),
        ("Security Assessment", 3, 600, 2000),
        ("Data Migration Service", 3, 300, 1000),
        ("Managed IT Support", 9, 150, 600),
        ("VPN Gateway", 4, 250, 480),
        ("Server Rack", 4, 700, 1300),
        ("CRM Software", 2, 100, 350),
        ("ERP Module", 2, 200, 700),
        ("Drone Sensor Kit", 1, 600, 1100),
        ("Tablet Bundle", 1, 400, 780),
        ("Training Workshop", 5, 150, 500),
        ("Cloud Backup", 2, 50, 160),
        ("Firewall Appliance", 4, 450, 900),
        ("R&D Lab Equipment", 10, 1500, 2800),
        ("Marketing Analytics Tool", 2, 80, 280),
        ("Legal Compliance Module", 3, 350, 1100),
        ("GPU Compute Card", 1, 1200, 2100),
        ("Wireless Access Point", 4, 120, 240),
        ("HR Software Suite", 2, 110, 380),
        ("IoT Gateway", 1, 300, 580),
    ]
    products = []
    for pid, (pname, cat_id, base_cost, base_price) in enumerate(PRODUCT_TEMPLATES, 1):
        p = Product(
            product_id=pid,
            name=pname,
            category_id=cat_id,
            unit_cost=float(base_cost),
            selling_price=float(base_price),
            is_active=True,
        )
        products.append(p)
        session.add(p)

    session.flush()

    # 7. Transactions & Invoices & Cash Flows (Jan 2023 – Mar 2025)
    days_range = pd.date_range("2023-01-01", "2025-03-31")
    txns = []
    invs = []
    cfs = []

    for day_ts in days_range:
        day = day_ts.date()
        q = (day.month - 1) // 3 + 1
        season = {1: 0.75, 2: 1.0, 3: 1.0, 4: 1.35}[q]
        yoy = 1.0 if day.year == 2023 else (1.15 if day.year == 2024 else 1.25)
        n_sales = int(rng.poisson(lam=4.5 * season * yoy))

        for _ in range(n_sales):
            p = products[int(rng.integers(0, len(products)))]
            qty = int(rng.integers(1, 4))
            discount = float(rng.choice([0.0, 0.05, 0.10, 0.15], p=[0.6, 0.2, 0.15, 0.05]))
            
            unit_cost = p.unit_cost
            unit_price = p.selling_price
            if p.category_id == 1 and day.year == 2024 and day.month >= 7:
                unit_cost *= 1.25
            if p.category_id == 2 and day.year == 2024:
                unit_price *= 1.15

            amount = round(unit_price * qty, 2)
            cost = round(unit_cost * qty, 2)
            cid = int(rng.integers(1, 51))
            rid = int(rng.integers(1, 6))
            tid = uuid.uuid4()

            t = Transaction(
                transaction_id=tid,
                transaction_date=day,
                customer_id=cid,
                product_id=p.product_id,
                category_id=p.category_id,
                region_id=rid,
                department_id=1,
                transaction_type="sale",
                amount=amount,
                cost=cost,
                quantity=qty,
                discount_pct=round(discount * 100, 2),
                payment_method=str(rng.choice(["bank_transfer", "credit_card", "cash", "cheque"])),
                status="completed",
            )
            session.add(t)
            txns.append(t)

            # Invoices
            if rng.random() < 0.45:
                due = day + datetime.timedelta(days=30)
                if day.year == 2024 and day.month in (10, 11, 12):
                    paid = 0.0 if rng.random() < 0.35 else amount
                else:
                    paid = amount if rng.random() < 0.85 else 0.0

                pstatus = "paid" if paid >= amount else ("overdue" if day < datetime.date(2025, 3, 1) else "unpaid")
                inv = Invoice(
                    invoice_id=uuid.uuid4(),
                    customer_id=cid,
                    invoice_date=day,
                    due_date=due,
                    invoice_amount=amount,
                    paid_amount=paid,
                    payment_date=day + datetime.timedelta(days=15) if paid > 0 else None,
                    payment_status=pstatus,
                )
                session.add(inv)
                invs.append(inv)

    # 8. Expenses
    exps = []
    for day_ts in days_range:
        day = day_ts.date()
        n_exp = int(rng.integers(1, 4))
        for _ in range(n_exp):
            cat_id = int(rng.integers(6, 11))
            dept_id = int(rng.integers(2, 8))
            vid = int(rng.integers(1, 21))
            base_amt = float(rng.uniform(300, 3500))

            if day.year == 2024 and day.month == 10 and dept_id == 3:
                base_amt *= 3.2
            if day.year == 2024 and day.month in (7, 8, 9):
                base_amt *= 1.30

            amt = round(base_amt, 2)
            e = Expense(
                expense_id=uuid.uuid4(),
                expense_date=day,
                category_id=cat_id,
                department_id=dept_id,
                vendor_id=vid,
                amount=amt,
                status="approved",
                description=f"Operational expense {day.strftime('%b %Y')}",
            )
            session.add(e)
            exps.append(e)

    # 9. Budgets
    for yr in [2023, 2024, 2025]:
        for mo in range(1, 13):
            if yr == 2025 and mo > 3:
                continue
            for cat_id in range(6, 11):
                for dept_id in [2, 3, 6, 7]:
                    b_amt = 15000.0 * (1.1 if yr == 2024 else 1.0)
                    b = Budget(
                        budget_id=uuid.uuid4(),
                        period_year=yr,
                        period_month=mo,
                        category_id=cat_id,
                        department_id=dept_id,
                        budget_amount=b_amt,
                    )
                    session.add(b)

    # 10. Cash Flows
    for t in txns[::3]:
        cf = CashFlow(
            cashflow_id=uuid.uuid4(),
            flow_date=t.transaction_date,
            flow_type="inflow",
            amount=t.amount,
            category_id=t.category_id,
            department_id=t.department_id,
            description="Customer transaction settlement",
            reference_id=t.transaction_id,
        )
        session.add(cf)

    for e in exps[::2]:
        cf = CashFlow(
            cashflow_id=uuid.uuid4(),
            flow_date=e.expense_date,
            flow_type="outflow",
            amount=e.amount,
            category_id=e.category_id,
            department_id=e.department_id,
            description="Vendor expense disbursement",
            reference_id=e.expense_id,
        )
        session.add(cf)

    session.commit()
    print(f"Successfully seeded {len(txns)} transactions, {len(exps)} expenses, {len(invs)} invoices into {SQLITE_PATH}.")
    session.close()


if __name__ == "__main__":
    generate_sqlite_db()
