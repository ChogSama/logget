"""
server/routers/logs.py
"""
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.dependencies import get_current_user, get_db
from server.schemas.log import LogCreate, LogResponse, LogUpdate
from server.services import log as log_service
from server.services.storage import generate_signed_params
from server.utils.uuid import ensure_uuid

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/upload-sign")
async def get_upload_sign(_: any = Depends(get_current_user)):
    return generate_signed_params()


@router.get("", response_model=list[LogResponse])
async def get_logs(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD"),
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    return await log_service.get_logs_by_date(db, ensure_uuid(current_user_id), date, timezone)


@router.post("", response_model=LogResponse, status_code=201)
async def create_log(
    data: LogCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    return await log_service.create_log(db, ensure_uuid(current_user_id), data)


@router.patch("/{log_id}", response_model=LogResponse)
async def update_log(
    log_id: UUID,
    data: LogUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    return await log_service.update_log(db, log_id, ensure_uuid(current_user_id), data, background_tasks)


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    await log_service.delete_log(db, log_id, ensure_uuid(current_user_id), background_tasks)