"""
server/schemas/insight.py
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from server.models.log import InsightType


class AnalyzeRequest(BaseModel):
    date: str  # YYYY-MM-DD
    timezone: str = "Asia/Ho_Chi_Minh"


class DailyInsightResponse(BaseModel):
    date: date
    status: str | None = None
    lbs_score: float | None = None
    work_score: float | None = None
    sleep_score: float | None = None
    exercise_score: float | None = None
    social_score: float | None = None
    recovery_score: float | None = None
    imbalance_risk: bool | None = None
    ai_summary: str | None = None

    model_config = {"from_attributes": True}


class AIInsightResponse(BaseModel):
    id: UUID
    insight_type: InsightType
    content: str
    reference_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}