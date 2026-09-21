from typing import Optional

from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None


class CategoryBreakdown(BaseModel):
    category: str
    value: float
    pct_of_total: float
    change_pct: Optional[float] = None


class RegionBreakdown(BaseModel):
    region: str
    value: float
    pct_of_total: float
    change_pct: Optional[float] = None


class BudgetVarianceItem(BaseModel):
    category: str
    department: str
    budget: float
    actual: float
    variance: float
    variance_pct: float
    status: str  # "under_budget" | "near_budget" | "over_budget"


class ReceivablesAging(BaseModel):
    bucket_0_30: float
    bucket_31_60: float
    bucket_61_90: float
    bucket_90_plus: float
    total_outstanding: float
    overdue_amount: float
    overdue_pct: float
