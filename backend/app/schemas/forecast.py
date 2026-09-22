from typing import List, Optional

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: str
    forecast: Optional[float] = None
    actual: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    is_actual: bool = True
    is_forecast: bool = False


class ForecastResult(BaseModel):
    horizon_days: int
    method: str
    mae: float
    rmse: float
    mape: Optional[float] = None
    points: List[ForecastPoint]
    disclaimer: str
    generated_at: str
