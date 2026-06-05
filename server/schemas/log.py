"""
server/schemas/log.py

LogCreate  : activity_type + start_time + end_time + timezone → BE tính logged_at (UTC) và duration_hours
LogUpdate  : tất cả fields optional; start_time / end_time / timezone phải gửi đủ bộ 3 hoặc không gửi gì
LogResponse: serialized ActivityLog trả về client

ActivityType enum định nghĩa ở đây — models/log.py nên import từ đây.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Self

from pydantic import BaseModel, model_validator


class ActivityType(str, Enum):
    work = "work"
    sleep = "sleep"
    exercise = "exercise"
    social = "social"
    recovery = "recovery"


class LogCreate(BaseModel):
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    timezone: str  # IANA, e.g. "Asia/Ho_Chi_Minh"
    note: str | None = None
    media_url: str | None = None  # URL sau khi client upload trực tiếp lên Cloudinary

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        if self.end_time < self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class LogUpdate(BaseModel):
    activity_type: ActivityType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    note: str | None = None
    media_url: str | None = None

    @model_validator(mode="after")
    def validate_time_fields_together(self) -> Self:
        # start_time / end_time / timezone phải gửi đủ bộ 3
        time_fields = [self.start_time, self.end_time, self.timezone]
        provided_count = sum(1 for f in time_fields if f is not None)
        if 0 < provided_count < 3:
            raise ValueError("start_time, end_time, and timezone must all be provided together")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class LogResponse(BaseModel):
    id: UUID
    user_id: UUID
    activity_type: ActivityType
    duration_hours: float
    note: str | None
    media_url: str | None
    logged_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}