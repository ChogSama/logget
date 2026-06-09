"""
SQLAlchemy models — tables: activity_logs, daily_summaries, ai_insights

activity_logs:
    intensity — nullable, chỉ có nghĩa khi activity_type=exercise (moderate/vigorous).
    Validator trong LogCreate/LogUpdate ép intensity=None cho các type khác.

daily_summaries:
    status          — PROCESSING / SUCCESS / FAILED (lazy eval pipeline).
    acute_workload  — raw EWMA AW_t (λ_a=0.50), lưu để tính ACWR lần sau O(1).
    chronic_workload— raw EWMA CW_t (λ_c≈0.069), tương tự.
    Các cột *_score — lưu trực tiếp sau mỗi lần analyze, dùng cho trend chart.

UniqueConstraint: daily_summaries(user_id, date)
"""
import enum
import uuid
from datetime import date as PyDate, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey,
    String, Text, UniqueConstraint, func,
)

from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column

from server.database import Base
from server.schemas.log import ActivityType, IntensityType


class InsightType(str, enum.Enum):
    daily = "daily"
    pattern = "pattern"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType, name="activity_type_enum"), nullable=False)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity: Mapped[IntensityType | None] = mapped_column(PG_ENUM(IntensityType, name="intensity_type_enum", create_type=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DailySummary(Base):
    __tablename__ = "daily_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_summary_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[PyDate] = mapped_column(Date, nullable=False)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # PROCESSING/SUCCESS/FAILED
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    lbs_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    exercise_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    social_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    imbalance_risk: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    acute_workload: Mapped[float | None] = mapped_column(Float, nullable=True)
    chronic_workload: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_type: Mapped[InsightType] = mapped_column(Enum(InsightType, name="insight_type_enum"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference_date: Mapped[PyDate | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())