"""
server/routers/dashboard.py — prefix: /dashboard

Provides aggregate statistics, consecutive streaks, and data processing for the UI dashboard.
Integrates pure-mathematical filters to calculate user lifestyle consistency ratios.
"""
from datetime import date as date_type, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.dependencies import get_current_user
from server.models.log import DailySummary
from server.schemas.dashboard import LBSTrendPoint, LBSTrendResponse, OverviewResponse, StreakResponse
from server.services import lbs as lbs_service
from server.utils.uuid import ensure_uuid

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_BALANCE_LBS = 65.0


def _meets_target(s: DailySummary) -> bool:
    return (
        s.status == "SUCCESS"
        and s.lbs_score is not None
        and s.lbs_score >= _BALANCE_LBS
        and s.imbalance_risk is False
    )


async def _recent_summaries(db: AsyncSession, user_id, days: int) -> list[DailySummary]:
    cutoff = date_type.today() - timedelta(days=days)
    result = await db.execute(
        select(DailySummary)
        .where(
            and_(
                DailySummary.user_id == user_id,
                DailySummary.date >= cutoff,
            )
        )
        .order_by(DailySummary.date.desc())
    )
    return result.scalars().all()


def _compute_streak(summaries: list[DailySummary]) -> int:
    """Yêu cầu mảng đầu vào sắp xếp theo thứ tự thời gian giảm dần (date DESC)."""
    streak = 0
    prev_date = None
    for s in summaries:
        if prev_date is None:
            if _meets_target(s):
                streak += 1
                prev_date = s.date
            else:
                if s.status == "SUCCESS" or s.date < date_type.today():
                    break
        else:
            if s.date == prev_date - timedelta(days=1) and _meets_target(s):
                streak += 1
                prev_date = s.date
            else:
                break
    return streak


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    today = date_type.today()

    summaries_30 = await _recent_summaries(db, user_uuid, 30)
    today_summary = next((s for s in summaries_30 if s.date == today), None)

    burnout_alert = None
    if today_summary and today_summary.status == "SUCCESS" and today_summary.acute_workload is not None:
        count_result = await db.execute(
            select(func.count(DailySummary.id)).where(
                and_(
                    DailySummary.user_id == user_uuid,
                    DailySummary.status == "SUCCESS",
                    DailySummary.date <= today,
                )
            )
        )
        day_index = count_result.scalar() or 1
        ewma = lbs_service.burnout_from_stored(
            today_summary.acute_workload,
            today_summary.chronic_workload or 0.0,
            day_index,
        )
        burnout_alert = ewma.alert

    streak = _compute_streak(summaries_30)
    total = len(summaries_30)
    target_days = sum(1 for s in summaries_30 if _meets_target(s))
    ratio = round(target_days / total, 2) if total > 0 else 0.0

    return OverviewResponse(
        date=today,
        lbs_score=today_summary.lbs_score if (today_summary and today_summary.status == "SUCCESS") else None,
        imbalance_risk=today_summary.imbalance_risk if (today_summary and today_summary.status == "SUCCESS") else None,
        burnout_alert=burnout_alert,
        current_streak=streak,
        balance_ratio=ratio,
        total_logged_days=total,
    )


@router.get("/lbs", response_model=LBSTrendResponse)
async def get_lbs_trend(
    range: str = Query(default="week", pattern="^(week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    days = 7 if range == "week" else 30
    summaries = await _recent_summaries(db, user_uuid, days)
    success_only = [s for s in summaries if s.status == "SUCCESS"]
    asc = sorted(success_only, key=lambda s: s.date)
    return LBSTrendResponse(
        range=range,
        data=[LBSTrendPoint.model_validate(s) for s in asc],
    )


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    summaries = await _recent_summaries(db, user_uuid, 30)
    streak = _compute_streak(summaries)
    total = len(summaries)
    target_days = sum(1 for s in summaries if _meets_target(s))
    ratio = round(target_days / total, 2) if total > 0 else 0.0
    return StreakResponse(
        current_streak=streak,
        balance_ratio=ratio,
        total_logged_days=total,
    )