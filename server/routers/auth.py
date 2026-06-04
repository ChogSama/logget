"""
Auth router — prefix: /auth
Endpoints:  POST /register, POST /login, POST /refresh,
            GET  /google, GET /google/callback,
            POST /google/token, GET /me
"""
from server.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
    """
    Google redirect về đây. Sau khi xử lý user, tạo oauth_code (5min JWT)
    và redirect sang React để React tự đổi lấy token qua POST /auth/google/token.
    """
    try:
        info = auth_service.exchange_google_code(code)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Google OAuth failed")

    user = await auth_service.get_user_by_google_id(db, info["google_id"])
    if not user:
        user = await auth_service.get_user_by_email(db, info["email"])
        if user:
            # Link Google ID vào tài khoản email đã tồn tại
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

    oauth_code = auth_service.create_oauth_code(str(user.id))
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?code={oauth_code}")


@router.post("/google/token", response_model=TokenResponse)
async def google_token(body: OAuthCodeRequest):
    """React gửi oauth_code nhận được từ redirect → trả access + refresh token."""
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