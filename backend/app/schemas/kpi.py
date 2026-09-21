from typing import Optional

from pydantic import BaseModel


class KPIValue(BaseModel):
    value: float
    formatted: str
    previous_value: Optional[float] = None
    change_abs: Optional[float] = None
    change_pct: Optional[float] = None
    direction: Optional[str] = None  # "up" | "down" | "flat"
    interpretation: Optional[str] = None


class ExecutiveKPIs(BaseModel):
    total_revenue: KPIValue
    net_profit: KPIValue
    profit_margin: KPIValue
    total_expenses: KPIValue
    net_cash_flow: KPIValue
    budget_variance_pct: KPIValue
    revenue_growth_pct: KPIValue
    outstanding_receivables: KPIValue
    total_profit: Optional[KPIValue] = None
    accounts_receivable: Optional[KPIValue] = None
    expense_to_revenue_ratio: Optional[KPIValue] = None
    revenue_growth_rate: Optional[KPIValue] = None
    period_label: str
    as_of_date: str
