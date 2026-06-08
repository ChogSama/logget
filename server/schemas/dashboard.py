"""
server/schemas/dashboard.py
"""
from datetime import date

from pydantic import BaseModel


class LBSTrendPoint(BaseModel):
    date: date
    lbs_score: float | None = None
    work_score: float | None = None
    sleep_score: float | None = None
    exercise_score: float | None = None
    social_score: float | None = None
    recovery_score: float | None = None

    model_config = {"from_attributes": True}


class LBSTrendResponse(BaseModel):
    range: str
    data: list[LBSTrendPoint]


class OverviewResponse(BaseModel):
    date: date
    lbs_score: float | None = None
    imbalance_risk: bool | None = None
    burnout_alert: str | None = None  # green/yellow_overload/yellow_deconditioning/red
    current_streak: int = 0
    balance_ratio: float = 0.0
    total_logged_days: int = 0


class StreakResponse(BaseModel):
    current_streak: int = 0
    balance_ratio: float = 0.0
    total_logged_days: int = 0