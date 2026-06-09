"""
server/schemas/insight.py
"""
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, field_validator

from server.models.log import InsightType


class AnalyzeRequest(BaseModel):
    date: date
    timezone: str = "Asia/Ho_Chi_Minh"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, Exception):
            raise ValueError(f"Invalid IANA timezone: {v}")
        return v


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