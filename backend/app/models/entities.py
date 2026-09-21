import datetime

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("segment IN ('enterprise', 'mid-market', 'smb')", name="ck_customers_segment"),
    )

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    segment: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    signup_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    region: Mapped["Region"] = relationship("Region", back_populates="customers")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="customer")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="vendors")
    region: Mapped["Region"] = relationship("Region", back_populates="vendors")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="vendor")
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="vendor")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_cost >= 0", name="ck_products_unit_cost"),
        CheckConstraint("selling_price >= 0", name="ck_products_selling_price"),
    )

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    unit_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    selling_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="product")


