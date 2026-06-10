"""
server/routers/insights.py — prefix: /insights
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.dependencies import get_current_user
from server.models.log import DailySummary
from server.schemas.insight import AIInsightResponse, AnalyzeRequest, DailyInsightResponse
from server.services import ai as ai_service
from server.services import log as log_service
from server.utils.uuid import ensure_uuid

router = APIRouter(prefix="/insights", tags=["insights"])


async def _run_analysis_safe(
    db: AsyncSession, user_uuid, target_date, timezone, gemini, summary: DailySummary
) -> DailySummary:
    try:
        logs = await log_service.get_logs_by_date(db, user_uuid, str(target_date), timezone)
        return await ai_service.analyze_day(db, user_uuid, target_date, logs, gemini, summary)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        summary.status = "FAILED"
        summary.ai_summary = f"Hệ thống gặp sự cố ngoại lệ tầng Router: {str(e)}"
        await db.commit()
        return summary


@router.get("/daily", response_model=DailyInsightResponse)
async def get_daily_insight(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    target_date = date_type.fromisoformat(date)

    summary = await ai_service.get_daily_summary(db, user_uuid, target_date)
    if summary:
        return summary

    summary = await ai_service.refresh_daily_summary_rule_based(db, user_uuid, target_date)
    if summary:
        return summary

    summary = DailySummary(user_id=user_uuid, date=target_date, status="INIT")
    db.add(summary)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        summary = await ai_service.get_daily_summary(db, user_uuid, target_date)
        if summary:
            return summary
        raise
    return summary


@router.post("/analyze", response_model=DailyInsightResponse, status_code=status.HTTP_200_OK)
async def force_analyze(
    body: AnalyzeRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    target_date = body.date

    summary = await ai_service.get_daily_summary(db, user_uuid, target_date)
    if summary:
        if summary.status == "PROCESSING":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Concurrent analysis in progress")
        summary.status = "INIT"
    else:
        summary = DailySummary(user_id=user_uuid, date=target_date, status="INIT")
        db.add(summary)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Concurrent analysis in progress")

    return await _run_analysis_safe(db, user_uuid, target_date, body.timezone, request.app.state.gemini, summary)


@router.get("/patterns", response_model=AIInsightResponse)
async def get_patterns(
    range: str = Query(default="week", pattern="^(week|month)$"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    days = 7 if range == "week" else 30
    insight = await ai_service.generate_pattern_insight(db, user_uuid, days, request.app.state.gemini)
    return insight
