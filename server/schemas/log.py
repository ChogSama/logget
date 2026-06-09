"""
server/schemas/log.py
"""
from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, field_validator, model_validator


class ActivityType(str, Enum):
    work = "work"
    sleep = "sleep"
    exercise = "exercise"
    social = "social"
    recovery = "recovery"


class IntensityType(str, Enum):
    moderate = "moderate"
    vigorous = "vigorous"


def _check_iana(v: str) -> str:
    try:
        ZoneInfo(v)
    except (ZoneInfoNotFoundError, Exception):
        raise ValueError(f"Invalid IANA timezone: {v}")
    return v


class LogCreate(BaseModel):
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    timezone: str
    intensity: IntensityType | None = None
    note: str | None = None
    media_url: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        return _check_iana(v)

    @model_validator(mode="after")
    def validate_time_and_intensity(self) -> Self:
        if self.end_time < self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.activity_type == ActivityType.exercise:
            if self.intensity is None:
                self.intensity = IntensityType.moderate
        else:
            self.intensity = None
        return self


class LogUpdate(BaseModel):
    activity_type: ActivityType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    intensity: IntensityType | None = None
    note: str | None = None
    media_url: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            return _check_iana(v)
        return v
    
    @model_validator(mode="after")
    def validate_time_and_intensity(self) -> Self:
        has_start = self.start_time is not None
        has_end = self.end_time is not None
        has_tz = self.timezone is not None
        if (has_start or has_end) and not has_tz:
            raise ValueError("timezone is required when updating start_time or end_time")
        if has_start and has_end and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if self.activity_type is not None:
            if self.activity_type == ActivityType.exercise:
                if self.intensity is None:
                    self.intensity = IntensityType.moderate
            else:
                self.intensity = None
        return self


class LogResponse(BaseModel):
    id: UUID
    user_id: UUID
    activity_type: ActivityType
    duration_hours: float | None
    intensity: IntensityType | None
    note: str | None
    media_url: str | None
    logged_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}