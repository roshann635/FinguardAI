from typing import List, Optional

from pydantic import BaseModel


class AIQueryRequest(BaseModel):
    question: str
    context_period: Optional[str] = "last_12_months"


class EvidenceItem(BaseModel):
    metric: str
    value: str
    source: str
    context: Optional[str] = None


class AIResponse(BaseModel):
    summary: str
    facts: List[str]
    insights: List[str]
    risks: List[str]
    opportunities: List[str]
    actions: List[str]
    limitations: List[str]
    evidence: List[EvidenceItem] = []
    raw_context_period: str
    generated_at: str



class ExecutiveBriefRequest(BaseModel):
    period: Optional[str] = "last_12_months"


class ExecutiveBriefResponse(BaseModel):
    financial_health: str
    key_findings: List[str]
    major_risks: List[str]
    key_opportunities: List[str]
    areas_requiring_attention: List[str]
    forecast_summary: str
    recommended_investigation_areas: List[str]
    generated_at: str
    disclaimer: str
