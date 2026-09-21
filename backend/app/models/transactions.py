import datetime
import uuid

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('sale', 'refund', 'adjustment')",
            name="ck_transactions_type",
        ),
        CheckConstraint("cost >= 0", name="ck_transactions_cost"),
        CheckConstraint("quantity >= 0", name="ck_transactions_quantity"),
        CheckConstraint(
            "discount_pct BETWEEN 0 AND 100",
            name="ck_transactions_discount_pct",
        ),
        CheckConstraint(
            "payment_method IN ('bank_transfer', 'credit_card', 'cash', 'cheque')",
            name="ck_transactions_payment_method",
        ),
        CheckConstraint(
            "status IN ('completed', 'pending', 'cancelled')",
            name="ck_transactions_status",
        ),
        Index("idx_txn_date_cat_region", "transaction_date", "category_id", "region_id"),
        Index("idx_txn_type_status", "transaction_type", "status"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.customer_id", ondelete="SET NULL"), nullable=True, index=True
    )
    vendor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.product_id", ondelete="SET NULL"), nullable=True, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False
    )
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(15), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="transactions")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="transactions")
    product: Mapped["Product"] = relationship("Product", back_populates="transactions")
    category: Mapped["Category"] = relationship("Category", back_populates="transactions")
    region: Mapped["Region"] = relationship("Region", back_populates="transactions")
    department: Mapped["Department"] = relationship("Department", back_populates="transactions")


