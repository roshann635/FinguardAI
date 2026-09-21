"""
Shared pytest fixtures for FinGuard AI backend tests.

Uses an in-memory SQLite database so tests run without a live PostgreSQL instance.
SQLAlchemy's PostgreSQL-specific dialect types (UUID, ARRAY, etc.) are overridden
where necessary via dialect-level workarounds.
"""

import datetime
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# ------------------------------------------------------------------
# Patch: SQLite does not support UUID(as_uuid=True) natively.
# Register a String affinity so columns render correctly.
# ------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String
from sqlalchemy.engine import Engine

# Make SQLite accept UUID columns as TEXT
from sqlalchemy import TypeDecorator


class _UUIDString(TypeDecorator):
    """Store UUIDs as TEXT in SQLite."""
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


# Monkey-patch PG_UUID so SQLite uses the String-based type
import sqlalchemy.dialects.postgresql as _pg_dialect
_orig_pg_uuid = _pg_dialect.UUID

# Only patch if running under SQLite (safe because tests always use SQLite)
_pg_dialect.UUID = _UUIDString  # type: ignore[assignment]

# NOW import app models (they reference UUID(as_uuid=True) at definition time)
from app.database.connection import Base
from app.models import (  # noqa: E402 — must come after patch
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

SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine and create all tables."""
    e = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    from sqlalchemy import CheckConstraint

    # SQLite: enable foreign keys
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Strip CHECK constraints for SQLite test tables so that data-quality
    # tests can insert deliberate violation rows to verify detection logic.
    for table in Base.metadata.tables.values():
        table.constraints = {c for c in table.constraints if not isinstance(c, CheckConstraint)}

    Base.metadata.create_all(bind=e)
    return e


@pytest.fixture(scope="function")
def db(engine, sample_data):
    """Yield a per-test session; roll back after each test to isolate state."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="session")
def sample_data(engine):
    """
    Insert a minimal but complete set of reference and transactional data.

    Covers:
      - completed sales (to test revenue calculation)
      - cancelled / refund transactions (must be excluded from revenue)
      - approved and pending expenses (only approved count)
      - budget rows (for budget variance)
      - invoices with varying payment_status (unpaid, partial, overdue, paid)
      - cash-flow inflow and outflow records
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    # ---- Reference data -----------------------------------------------
    cat_revenue = Category(category_id=1, name="Software Licenses", type="revenue")
    cat_expense = Category(category_id=2, name="Operations", type="expense")
    region = Region(region_id=1, name="North")
    dept = Department(department_id=1, name="Sales")

    session.add_all([cat_revenue, cat_expense, region, dept])
    session.flush()

    # ---- Entity data --------------------------------------------------
    customer = Customer(
        customer_id=1, name="Acme Corp", region_id=1,
        segment="enterprise", signup_date=datetime.date(2022, 1, 1),
    )
    vendor = Vendor(
        vendor_id=1, name="Infra Vendor", category_id=2, region_id=1,
    )
    product = Product(
        product_id=1, name="Core Suite", category_id=1,
        unit_cost=500.00, selling_price=1000.00,
    )
    session.add_all([customer, vendor, product])
    session.flush()

    # ---- Transactions -------------------------------------------------
    _base = dict(
        category_id=1, region_id=1, department_id=1,
        cost=500.00, quantity=1, discount_pct=0,
        payment_method="bank_transfer",
        transaction_date=datetime.date(2024, 3, 15),
    )
    t_sale1 = Transaction(
        transaction_id=uuid.uuid4(), transaction_type="sale",
        amount=1000.00, status="completed", **_base,
    )
    t_sale2 = Transaction(
        transaction_id=uuid.uuid4(), transaction_type="sale",
        amount=2000.00, status="completed", **_base,
    )
    t_cancelled = Transaction(
        transaction_id=uuid.uuid4(), transaction_type="sale",
        amount=999.00, status="cancelled", **_base,
    )
    t_refund = Transaction(
        transaction_id=uuid.uuid4(), transaction_type="refund",
        amount=500.00, status="completed", **_base,
    )
    session.add_all([t_sale1, t_sale2, t_cancelled, t_refund])

    # ---- Expenses -----------------------------------------------------
    _ebase = dict(
        category_id=2, department_id=1, vendor_id=1,
        expense_date=datetime.date(2024, 3, 10),
    )
    e_approved1 = Expense(expense_id=uuid.uuid4(), amount=300.00, status="approved", **_ebase)
    e_approved2 = Expense(expense_id=uuid.uuid4(), amount=200.00, status="approved", **_ebase)
    e_pending = Expense(expense_id=uuid.uuid4(), amount=9999.00, status="pending", **_ebase)
    session.add_all([e_approved1, e_approved2, e_pending])

    # ---- Budgets ------------------------------------------------------
    b1 = Budget(
        budget_id=uuid.uuid4(), period_year=2024, period_month=3,
        category_id=2, department_id=1, budget_amount=400.00,
    )
    session.add(b1)

    # ---- Invoices -----------------------------------------------------
    _ibase = dict(
        customer_id=1,
        invoice_date=datetime.date(2024, 2, 1),
        due_date=datetime.date(2024, 3, 1),
        invoice_amount=1000.00,
    )
    inv_unpaid = Invoice(
        invoice_id=uuid.uuid4(), paid_amount=0.00,
        payment_status="unpaid", **_ibase,
    )
    inv_partial = Invoice(
        invoice_id=uuid.uuid4(), paid_amount=400.00,
        payment_status="partial", **_ibase,
    )
    inv_overdue = Invoice(
        invoice_id=uuid.uuid4(), paid_amount=0.00,
        payment_status="overdue", **_ibase,
    )
    inv_paid = Invoice(
        invoice_id=uuid.uuid4(), paid_amount=1000.00,
        payment_status="paid", payment_date=datetime.date(2024, 3, 5), **_ibase,
    )
    session.add_all([inv_unpaid, inv_partial, inv_overdue, inv_paid])

    # ---- Cash flows ---------------------------------------------------
    cf_in1 = CashFlow(
        cashflow_id=uuid.uuid4(), flow_date=datetime.date(2024, 3, 15),
        flow_type="inflow", amount=3000.00, category_id=1, department_id=1,
    )
    cf_out1 = CashFlow(
        cashflow_id=uuid.uuid4(), flow_date=datetime.date(2024, 3, 15),
        flow_type="outflow", amount=1200.00, category_id=2, department_id=1,
    )
    session.add_all([cf_in1, cf_out1])

    session.commit()
    session.close()
