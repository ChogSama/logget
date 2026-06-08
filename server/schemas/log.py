"""
server/schemas/log.py
"""

from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator


class ActivityType(str, Enum):
    work = "work"
    sleep = "sleep"
    exercise = "exercise"
    social = "social"
    recovery = "recovery"


class IntensityType(str, Enum):
    moderate = "moderate"
    vigorous = "vigorous"


class LogCreate(BaseModel):
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    timezone: str  # IANA, e.g. "Asia/Ho_Chi_Minh"
    intensity: IntensityType | None = None
    note: str | None = None
    media_url: str | None = None

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

    @model_validator(mode="after")
    def validate_time_and_intensity(self) -> Self:
        time_fields = [self.start_time, self.end_time, self.timezone]
        provided = sum(1 for f in time_fields if f is not None)
        if 0 < provided < 3:
            raise ValueError("start_time, end_time, and timezone must all be provided together")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
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