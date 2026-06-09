"""
server/routers/dashboard.py — prefix: /dashboard

Module định tuyến tính toán chỉ số tổng quan và xu hướng đồ thị LBS.
Xử lý thuật toán tìm chuỗi ngày cân bằng liên tục (Streak) và sắp xếp tăng dần dòng thời gian.
Tìm kiếm nhanh: GET_OVERVIEW, GET_LBS_TREND, GET_STREAK, CALCULATE_STREAK, IS_BALANCED
"""
from datetime import date as date_type, datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.dependencies import get_current_user
from server.models.log import DailySummary
from server.schemas.dashboard import LBSTrendPoint, LBSTrendResponse, OverviewResponse, StreakResponse
from server.services import lbs as lbs_service
from server.utils.uuid import ensure_uuid

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_STREAK_MIN_SCORE = 65.0


def _local_today(timezone: str) -> date_type:
    """Tính ngày địa phương của user — dùng cho mọi endpoint thay vì date_type.today()."""
    try:
        tz = pytz.timezone(timezone)
    except Exception:
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(tz).date()


def _is_balanced(s: DailySummary) -> bool:
    """Balance target: SUCCESS + lbs_score >= 65 + imbalance_risk is False (không phải None)."""
    return (
        s.status == "SUCCESS"
        and s.lbs_score is not None
        and s.lbs_score >= _STREAK_MIN_SCORE
        and s.imbalance_risk is False
    )


def _compute_streak(summary_map: dict, today: date_type) -> int:
    """
    Đếm streak liên tiếp từ today trở về quá khứ.
    Today: balanced → đếm; chưa balanced → bỏ qua (không phá streak).
    Quá khứ: không balanced → dừng.
    """
    streak = 0
    check_date = today

    if check_date in summary_map:
        if _is_balanced(summary_map[check_date]):
            streak += 1
        # Dù balanced hay không, luôn check hôm qua — không phá streak vì today chưa xong
            check_date -= timedelta(days=1)
    else:
        check_date -= timedelta(days=1)

    while check_date in summary_map:
        s = summary_map[check_date]
        if _is_balanced(s):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    local_today = _local_today(timezone)

    stmt = select(DailySummary).where(DailySummary.user_id == user_uuid).order_by(DailySummary.date.desc())
    result = await db.execute(stmt)
    summaries = result.scalars().all()

    if not summaries:
        return OverviewResponse(date=local_today, total_logged_days=0)

    summary_map = {s.date: s for s in summaries}
    success_summaries = [s for s in summaries if s.status == "SUCCESS"]
    total_success = len(success_summaries)

    balanced_days = sum(1 for s in success_summaries if _is_balanced(s))
    ratio = round(balanced_days / total_success, 4) if total_success > 0 else 0.0
    streak = _compute_streak(summary_map, local_today)

    today_summary = summary_map.get(local_today)
    burnout_alert = "green"
    if success_summaries:
        latest = success_summaries[0]
        day_index = sum(1 for s in success_summaries if s.date <= latest.date)
        ewma_res = lbs_service.burnout_from_stored(
            latest.acute_workload or 0.0,
            latest.chronic_workload or 0.0,
            day_index,
        )
        burnout_alert = ewma_res.alert

    return OverviewResponse(
        date=local_today,
        lbs_score=today_summary.lbs_score if (today_summary and today_summary.status == "SUCCESS") else None,
        imbalance_risk=today_summary.imbalance_risk if (today_summary and today_summary.status == "SUCCESS") else None,
        burnout_alert=burnout_alert,
        current_streak=streak,
        balance_ratio=ratio,
        total_logged_days=total_success,
    )


@router.get("/lbs", response_model=LBSTrendResponse)
async def get_lbs_trend(
    range_type: str = Query(default="week", alias="range", pattern="^(week|month)$"),
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    days = 7 if range_type == "week" else 30
    cutoff = _local_today(timezone) - timedelta(days=days)

    result = await db.execute(
        select(DailySummary)
        .where(and_(DailySummary.user_id == user_uuid, DailySummary.date >= cutoff))
        .order_by(DailySummary.date.asc())
    )
    summaries = result.scalars().all()
    success_only = [s for s in summaries if s.status == "SUCCESS"]

    return LBSTrendResponse(
        range=range_type,
        data=[LBSTrendPoint.model_validate(s) for s in success_only],
    )


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    local_today = _local_today(timezone)
    cutoff = local_today - timedelta(days=30)

    result = await db.execute(
        select(DailySummary)
        .where(and_(DailySummary.user_id == user_uuid, DailySummary.date >= cutoff))
        .order_by(DailySummary.date.desc())
    )
    summaries = result.scalars().all()

    if not summaries:
        return StreakResponse()

    summary_map = {s.date: s for s in summaries}
    success_summaries = [s for s in summaries if s.status == "SUCCESS"]
    total = len(success_summaries)
    streak = _compute_streak(summary_map, local_today)
    balanced = sum(1 for s in success_summaries if _is_balanced(s))
    ratio = round(balanced / total, 4) if total > 0 else 0.0

    return StreakResponse(
        current_streak=streak,
        balance_ratio=ratio,
        total_logged_days=total,
    )