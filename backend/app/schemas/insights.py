from typing import Optional

from pydantic import BaseModel


class InsightCard(BaseModel):
    type: str  # "fact" | "insight" | "risk" | "opportunity" | "action"
    title: str
    body: str
    severity: Optional[str] = None  # for risk cards
    evidence: Optional[str] = None
    metric_source: Optional[str] = None
    period: Optional[str] = None


class OpportunityItem(BaseModel):
    title: str
    description: str
    supporting_metric: str
    estimated_impact: Optional[str] = None
    recommended_action: str


class ActionItem(BaseModel):
    priority: str  # "high" | "medium" | "low"
    title: str
    rationale: str
    supporting_evidence: str
    action_type: str  # "investigate" | "monitor" | "optimize" | "escalate"
