"""
server/services/log.py

Time handling:
    - Client gửi start_time + end_time (naive datetime, theo timezone của user) + timezone (IANA string).
    - BE convert start_time → UTC lưu vào logged_at; tính duration_hours = (end - start).
    - GET /logs?date filter theo khoảng UTC tương ứng với ngày đó trong timezone của user.

Ownership: mọi mutation kiểm tra log.user_id == requesting user_id → 403 nếu không khớp.

PATCH media: nếu media_url thay đổi (kể cả set null), file cũ trên Cloudinary bị xóa qua BackgroundTask.
"""
from datetime import datetime, date, time as time_type, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.log import ActivityLog
from server.schemas.log import LogCreate, LogUpdate
from server.services.storage import delete_media
from server.utils.uuid import ensure_uuid

_UTC = ZoneInfo("UTC")


def _parse_tz(tz_str: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_str)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=422, detail=f"Unknown timezone: {tz_str}")


def _to_utc(dt: datetime, tz: ZoneInfo) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(_UTC).replace(tzinfo=None)


def _naive_utc(dt: datetime) -> datetime:
    """Chuẩn hóa datetime về naive UTC để dùng trong phép toán thời gian."""
    if dt.tzinfo is not None:
        return dt.astimezone(_UTC).replace(tzinfo=None)
    return dt


def _day_utc_range(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime.combine(d, time_type.min, tzinfo=tz)
    end_local = datetime.combine(d, time_type.max, tzinfo=tz)
    return start_local.astimezone(_UTC), end_local.astimezone(_UTC)


async def _get_owned_log(db: AsyncSession, log_id: UUID, user_id: UUID) -> ActivityLog:
    result = await db.execute(select(ActivityLog).where(ActivityLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    if log.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return log


async def get_logs_by_date(
    db: AsyncSession, user_id: UUID, date_str: str, timezone: str
) -> list[ActivityLog]:
    tz = _parse_tz(timezone)
    d = date.fromisoformat(date_str)
    start, end = _day_utc_range(d, tz)
    result = await db.execute(
        select(ActivityLog)
        .where(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.logged_at >= start,
                ActivityLog.logged_at <= end,
            )
        )
        .order_by(ActivityLog.logged_at)
    )
    return result.scalars().all()


async def create_log(db: AsyncSession, user_id: UUID, data: LogCreate) -> ActivityLog:
    tz = _parse_tz(data.timezone)
    logged_at = _to_utc(data.start_time, tz)
    duration_hours = (data.end_time - data.start_time).total_seconds() / 3600

    log = ActivityLog(
        user_id=ensure_uuid(user_id),
        activity_type=data.activity_type,
        duration_hours=round(duration_hours, 4),
        intensity=data.intensity,
        note=data.note,
        media_url=data.media_url,
        logged_at=logged_at,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def update_log(
    db: AsyncSession,
    log_id: UUID,
    user_id: UUID,
    data: LogUpdate,
    background_tasks: BackgroundTasks,
) -> ActivityLog:
    log = await _get_owned_log(db, log_id, user_id)
    updated_fields = data.model_fields_set

    if "media_url" in updated_fields and log.media_url and log.media_url != data.media_url:
        background_tasks.add_task(delete_media, log.media_url)

    for field in updated_fields - {"start_time", "end_time", "timezone"}:
        setattr(log, field, getattr(data, field))

    if "start_time" in updated_fields or "end_time" in updated_fields:
        tz = _parse_tz(data.timezone)  # schema đã validate, _parse_tz là safety net
        has_new_start = "start_time" in updated_fields
        has_new_end = "end_time" in updated_fields

        existing_start = _naive_utc(log.logged_at)
        existing_end = existing_start + timedelta(hours=log.duration_hours or 0)

        if has_new_start and has_new_end:
            new_start = _to_utc(data.start_time, tz)
            new_end = _to_utc(data.end_time, tz)
            log.logged_at = new_start
            log.duration_hours = round((new_end - new_start).total_seconds() / 3600, 4)
        elif has_new_start:
            new_start = _to_utc(data.start_time, tz)
            new_duration = (existing_end - new_start).total_seconds() / 3600
            if new_duration <= 0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "new start_time must be before existing end_time")
            log.logged_at = new_start
            log.duration_hours = round(new_duration, 4)
        else:  # has_new_end only
            new_end = _to_utc(data.end_time, tz)
            new_duration = (new_end - existing_start).total_seconds() / 3600
            if new_duration <= 0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "new end_time must be after existing start_time")
            log.duration_hours = round(new_duration, 4)

    await db.commit()
    await db.refresh(log)
    return log


async def delete_log(
    db: AsyncSession,
    log_id: UUID,
    user_id: UUID,
    background_tasks: BackgroundTasks,
) -> None:
    log = await _get_owned_log(db, log_id, user_id)
    if log.media_url:
        background_tasks.add_task(delete_media, log.media_url)
    await db.delete(log)
    await db.commit()