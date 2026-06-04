"""
Auth router — prefix: /auth
Endpoints: POST /register, POST /login, POST /refresh, GET /google, GET /google/callback, POST /google/token, GET /me

Luồng xử lý Google OAuth 3 bước:
    1. GET /auth/google -> Redirect sang Google đăng nhập.
    2. GET /auth/google/callback -> Nhận auth code, xác thực tài khoản, xử lý thực thể User (đồng bộ/liên kết dữ liệu DB), trả về mã oauth_code JWT ngắn hạn.
    3. POST /auth/google/token -> Trao đổi mã oauth_code lấy cặp mã access_token và refresh_token chính thức cho Client.

Bảo mật & Phục hồi hệ thống:
    - Bẫy lỗi IntegrityError ngăn chặn Race Condition khi xảy ra xung đột đăng nhập đồng thời.
    - Che giấu lỗi sập/mất kết nối Database dưới dạng HTTP 500 ổn định.
"""
from server.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from server.database import get_db
from server.dependencies import get_current_user
from server.schemas.user import (
    OAuthCodeRequest, RefreshRequest,
    TokenResponse, UserCreate, UserLogin, UserResponse,
)
from server.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    if await auth_service.get_user_by_email(db, body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await auth_service.create_user(
        db,
        email=body.email,
        name=body.name,
        hashed_password=auth_service.hash_password(body.password),
    )
    uid = str(user.id)
    return TokenResponse(
        access_token=auth_service.create_access_token(uid),
        refresh_token=auth_service.create_refresh_token(uid),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_email(db, body.email)
    if not user or not user.hashed_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    uid = str(user.id)
    return TokenResponse(
        access_token=auth_service.create_access_token(uid),
        refresh_token=auth_service.create_refresh_token(uid),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    user_id = auth_service.decode_token(body.refresh_token, expected_type="refresh")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return TokenResponse(
        access_token=auth_service.create_access_token(user_id),
        refresh_token=auth_service.create_refresh_token(user_id),
    )


@router.get("/google")
async def google_login():
    return RedirectResponse(auth_service.get_google_auth_url())


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        info = auth_service.exchange_google_code(code)
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Google OAuth failed")

    try:
        user = await auth_service.get_user_by_google_id(db, info["google_id"])
        if not user:
            user = await auth_service.get_user_by_email(db, info["email"])
            if user:
                user.google_id = info["google_id"]
                if not user.avatar_url:
                    user.avatar_url = info["avatar_url"]
                await db.commit()
                await db.refresh(user)
            else:
                user = await auth_service.create_user(
                    db,
                    email=info["email"],
                    name=info["name"],
                    avatar_url=info["avatar_url"],
                    google_id=info["google_id"],
                )
    except IntegrityError:
        await db.rollback()
        user = await auth_service.get_user_by_google_id(db, info["google_id"])
        if not user:
            user = await auth_service.get_user_by_email(db, info["email"])
        if not user:
            raise HTTPException(
                status.HTTP_409_CONFLICT, 
                detail="Account processing conflict, please try again."
            )
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Database operation failed"
        )
        
    oauth_code = auth_service.create_oauth_code(str(user.id))
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?code={oauth_code}")


@router.post("/google/token", response_model=TokenResponse)
async def google_token(body: OAuthCodeRequest):
    user_id = auth_service.decode_oauth_code(body.code)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OAuth code")
    return TokenResponse(
        access_token=auth_service.create_access_token(user_id),
        refresh_token=auth_service.create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserResponse)
async def me(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user