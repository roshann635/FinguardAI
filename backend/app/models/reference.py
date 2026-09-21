from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("type IN ('revenue', 'expense', 'mixed')", name="ck_categories_type"),
        nullable=False,
    )

    # Back-references
    vendors: Mapped[list["Vendor"]] = relationship("Vendor", back_populates="category")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="category")
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship("Budget", back_populates="category")
    cash_flows: Mapped[list["CashFlow"]] = relationship("CashFlow", back_populates="category")


class Region(Base):
    __tablename__ = "regions"

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Back-references
    customers: Mapped[list["Customer"]] = relationship("Customer", back_populates="region")
    vendors: Mapped[list["Vendor"]] = relationship("Vendor", back_populates="region")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="region")


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Back-references
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="department")
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="department")
    budgets: Mapped[list["Budget"]] = relationship("Budget", back_populates="department")
    cash_flows: Mapped[list["CashFlow"]] = relationship("CashFlow", back_populates="department")


