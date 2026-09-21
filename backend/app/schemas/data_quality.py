from typing import Any, List

from pydantic import BaseModel


class DataQualityMetric(BaseModel):
    name: str
    score: float
    detail: str


class DataQualityReport(BaseModel):
    overall_score: float
    completeness: float
    consistency: float
    validity: float
    duplicate_rate: float
    missing_value_rate: float
    total_records: int
    issues: List[dict[str, Any]]
    generated_at: str
