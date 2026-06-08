"""
server/routers/insights.py — prefix: /insights

GET /insights/daily:
    Lazy eval — trả cache nếu SUCCESS; 202 nếu PROCESSING; trigger analyze_day nếu chưa có/FAILED.
    Race condition (concurrent requests): IntegrityError → trả trạng thái hiện tại.

POST /insights/analyze:
    Force re-analysis bất kể status hiện tại.

GET /insights/patterns:
    Gọi Gemini phân tích N ngày gần nhất (range=week|month), lưu AIInsight.
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


async def _trigger_analysis(
    db: AsyncSession,
    user_uuid,
    target_date: date_type,
    timezone: str,
    gemini,
    summary: DailySummary,
) -> DailySummary:
    logs = await log_service.get_logs_by_date(db, user_uuid, str(target_date), timezone)
    return await ai_service.analyze_day(db, user_uuid, target_date, logs, gemini, summary)


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

    if summary and summary.status == "SUCCESS":
        return summary
    if summary and summary.status == "PROCESSING":
        return DailyInsightResponse(date=target_date, status="PROCESSING")

    # Create/reset PROCESSING record
    if summary is None:
        summary = DailySummary(user_id=user_uuid, date=target_date, status="PROCESSING")
        db.add(summary)
    else:
        summary.status = "PROCESSING"

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        summary = await ai_service.get_daily_summary(db, user_uuid, target_date)
        stat = summary.status if summary else "PROCESSING"
        if summary and stat == "SUCCESS":
            return summary
        return DailyInsightResponse(date=target_date, status=stat)

    return await _trigger_analysis(db, user_uuid, target_date, timezone, request.app.state.gemini, summary)


@router.post("/analyze", response_model=DailyInsightResponse, status_code=status.HTTP_200_OK)
async def force_analyze(
    body: AnalyzeRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = ensure_uuid(current_user_id)
    target_date = date_type.fromisoformat(body.date)

    summary = await ai_service.get_daily_summary(db, user_uuid, target_date)
    if summary is None:
        summary = DailySummary(user_id=user_uuid, date=target_date, status="PROCESSING")
        db.add(summary)
    else:
        summary.status = "PROCESSING"

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Concurrent analysis in progress")

    return await _trigger_analysis(db, user_uuid, target_date, body.timezone, request.app.state.gemini, summary)


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