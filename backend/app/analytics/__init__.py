"""Analytics engine for FinGuard AI — public API."""

from app.analytics.budget import BudgetAnalyticsService
from app.analytics.cashflow import CashFlowService
from app.analytics.expenses import ExpenseAnalyticsService
from app.analytics.kpis import KPIService
from app.analytics.profitability import ProfitabilityService
from app.analytics.receivables import ReceivablesService
from app.analytics.revenue import RevenueAnalyticsService

__all__ = [
    "BudgetAnalyticsService",
    "CashFlowService",
    "ExpenseAnalyticsService",
    "KPIService",
    "ProfitabilityService",
    "ReceivablesService",
    "RevenueAnalyticsService",
]
