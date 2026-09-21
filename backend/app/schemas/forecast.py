from typing import List, Optional

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower_bound: float
    upper_bound: float
    is_actual: bool


class ForecastResult(BaseModel):
    horizon_days: int
    method: str
    mae: float
    rmse: float
    mape: Optional[float] = None
    points: List[ForecastPoint]
    disclaimer: str
    generated_at: str
