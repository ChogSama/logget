"""
server/routers/logs.py

Endpoints:
    GET  /logs/upload-sign      → trả signed params để client upload trực tiếp lên Cloudinary
    GET  /logs?date&timezone    → lấy logs theo ngày (filter by logged_at trong user's timezone)
    POST /logs                  → tạo log mới
    PATCH /logs/{id}            → cập nhật log (bao gồm media; old media xóa qua BackgroundTask)
    DELETE /logs/{id}           → xóa log + media trên Cloudinary (BackgroundTask)
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.dependencies import get_current_user, get_db
from server.models.user import User
from server.schemas.log import LogCreate, LogResponse, LogUpdate
from server.services import log as log_service
from server.services.storage import generate_signed_params

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/upload-sign")
async def get_upload_sign(_: User = Depends(get_current_user)):
    return generate_signed_params()


@router.get("", response_model=list[LogResponse])
async def get_logs(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD"),
    timezone: str = Query(default="Asia/Ho_Chi_Minh"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await log_service.get_logs_by_date(db, current_user.id, date, timezone)


@router.post("", response_model=LogResponse, status_code=201)
async def create_log(
    data: LogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await log_service.create_log(db, current_user.id, data)


@router.patch("/{log_id}", response_model=LogResponse)
async def update_log(
    log_id: UUID,
    data: LogUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await log_service.update_log(db, log_id, current_user.id, data, background_tasks)


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await log_service.delete_log(db, log_id, current_user.id, background_tasks)