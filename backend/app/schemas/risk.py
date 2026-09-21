from typing import List, Optional

from pydantic import BaseModel


class RiskIndicator(BaseModel):
    name: str
    level: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    value: Optional[float] = None
    threshold: Optional[float] = None
    description: str
    evidence: str


class RiskScore(BaseModel):
    overall_level: str
    overall_score: float  # 0-100
    indicators: List[RiskIndicator]
    methodology: str
    generated_at: str


class AnomalyRecord(BaseModel):
    record_id: str
    date: str
    category: str
    department: Optional[str] = None
    amount: float
    expected_range_low: float
    expected_range_high: float
    anomaly_score: float
    severity: str  # "low" | "medium" | "high"
    reason: str
    requires_investigation: bool
