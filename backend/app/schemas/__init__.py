from app.schemas.ai import AIQueryRequest, AIResponse, ExecutiveBriefRequest, ExecutiveBriefResponse
from app.schemas.analytics import (
    BudgetVarianceItem,
    CategoryBreakdown,
    ReceivablesAging,
    RegionBreakdown,
    TimeSeriesPoint,
)
from app.schemas.data_quality import DataQualityMetric, DataQualityReport
from app.schemas.forecast import ForecastPoint, ForecastResult
from app.schemas.insights import ActionItem, InsightCard, OpportunityItem
from app.schemas.kpi import ExecutiveKPIs, KPIValue
from app.schemas.risk import AnomalyRecord, RiskIndicator, RiskScore

__all__ = [
    # ai
    "AIQueryRequest",
    "AIResponse",
    "ExecutiveBriefRequest",
    "ExecutiveBriefResponse",
    # analytics
    "BudgetVarianceItem",
    "CategoryBreakdown",
    "ReceivablesAging",
    "RegionBreakdown",
    "TimeSeriesPoint",
    # data_quality
    "DataQualityMetric",
    "DataQualityReport",
    # forecast
    "ForecastPoint",
    "ForecastResult",
    # insights
    "ActionItem",
    "InsightCard",
    "OpportunityItem",
    # kpi
    "ExecutiveKPIs",
    "KPIValue",
    # risk
    "AnomalyRecord",
    "RiskIndicator",
    "RiskScore",
]
