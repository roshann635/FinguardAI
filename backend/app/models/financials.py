import datetime
import uuid

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount"),
        CheckConstraint(
            "status IN ('approved', 'pending', 'rejected')",
            name="ck_expenses_status",
        ),
        Index("idx_exp_date_cat_dept", "expense_date", "category_id", "department_id"),
        Index("idx_exp_status", "status"),
    )

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    expense_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False
    )
    vendor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="expenses")
    department: Mapped["Department"] = relationship("Department", back_populates="expenses")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="expenses")


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("period_year BETWEEN 2000 AND 2100", name="ck_budgets_period_year"),
        CheckConstraint("period_month BETWEEN 1 AND 12", name="ck_budgets_period_month"),
        CheckConstraint("budget_amount >= 0", name="ck_budgets_budget_amount"),
        UniqueConstraint(
            "period_year", "period_month", "category_id", "department_id",
            name="uq_budget_period_cat_dept",
        ),
        Index("idx_budget_period_cat_dept", "period_year", "period_month", "category_id", "department_id"),
    )

    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False
    )
    budget_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="budgets")
    department: Mapped["Department"] = relationship("Department", back_populates="budgets")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("invoice_amount > 0", name="ck_invoices_invoice_amount"),
        CheckConstraint("paid_amount >= 0", name="ck_invoices_paid_amount"),
        CheckConstraint("paid_amount <= invoice_amount", name="chk_paid_lte_invoice"),
        CheckConstraint(
            "payment_status IN ('unpaid', 'partial', 'paid', 'overdue')",
            name="ck_invoices_payment_status",
        ),
        Index("idx_inv_status_due", "payment_status", "due_date"),
        Index("idx_inv_invoice_date", "invoice_date"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    invoice_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    invoice_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    payment_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    payment_status: Mapped[str] = mapped_column(String(15), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")


class CashFlow(Base):
    __tablename__ = "cash_flows"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_cash_flows_amount"),
        CheckConstraint("flow_type IN ('inflow', 'outflow')", name="ck_cash_flows_flow_type"),
        Index("idx_cf_date_type", "flow_date", "flow_type"),
        Index("idx_cf_reference", "reference_id"),
    )

    cashflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    flow_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    flow_type: Mapped[str] = mapped_column(String(10), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True, index=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="cash_flows")
    department: Mapped["Department"] = relationship("Department", back_populates="cash_flows")


