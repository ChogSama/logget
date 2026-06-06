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

router = APIRouter(prefix="/logs", tags=["logs"])


def _ensure_uuid(user_id: any) -> UUID:
    """Hàm bổ trợ ép kiểu dữ liệu sang UUID đối tượng."""
    if isinstance(user_id, UUID):
        return user_id
    return UUID(str(user_id))


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
    user_uuid = _ensure_uuid(current_user_id)
    return await log_service.get_logs_by_date(db, user_uuid, date, timezone)


@router.post("", response_model=LogResponse, status_code=201)
async def create_log(
    data: LogCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = _ensure_uuid(current_user_id)
    return await log_service.create_log(db, user_uuid, data)


@router.patch("/{log_id}", response_model=LogResponse)
async def update_log(
    log_id: UUID,
    data: LogUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = _ensure_uuid(current_user_id)
    return await log_service.update_log(db, log_id, user_uuid, data, background_tasks)


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: any = Depends(get_current_user),
):
    user_uuid = _ensure_uuid(current_user_id)
    await log_service.delete_log(db, log_id, user_uuid, background_tasks)