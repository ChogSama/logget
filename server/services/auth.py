"""
Auth service — JWT, password hashing, Google OAuth, user CRUD.

JWT — payload keys: sub (user_id str), type, exp. Algorithm: HS256.
    type="access"     → 30min  — dùng bởi dependencies.py
    type="refresh"    → 7d
    type="oauth_code" → 5min   — one-time code cho Google OAuth Code Exchange Flow

Google OAuth Code Exchange Flow:
    1. GET  /auth/google            → redirect tới Google
    2. GET  /auth/google/callback   → BE exchange code với Google → tạo oauth_code JWT
                                      → redirect React: FRONTEND_URL/auth/callback?code=<oauth_code>
    3. POST /auth/google/token      → React gửi oauth_code → BE trả access + refresh token
    Hàm liên quan: get_google_auth_url(), exchange_google_code(), create_oauth_code(), decode_oauth_code()

    exchange_google_code() dùng requests trực tiếp (không dùng google-auth-oauthlib Flow để
    tránh state mismatch trong stateless FastAPI — mỗi request tạo Flow mới, state khác nhau).
    google-auth-oauthlib vẫn có trong deps nhưng chỉ dùng google.oauth2.id_token để verify.

Password: pwdlib[bcrypt]
CRUD: get_user_by_email, get_user_by_id, get_user_by_google_id, create_user
"""
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
import requests as http_requests
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import settings
from server.models.user import User

_ALGORITHM = "HS256"
_ACCESS_EXPIRE = timedelta(minutes=30)
_REFRESH_EXPIRE = timedelta(days=7)
_OAUTH_CODE_EXPIRE = timedelta(minutes=5)
_GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

_pwdlib = PasswordHash.recommended()


# --- Password ---

def hash_password(password: str) -> str:
    return _pwdlib.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwdlib.verify(plain, hashed)


# --- JWT ---

def create_access_token(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "access", "exp": datetime.now(timezone.utc) + _ACCESS_EXPIRE},
        settings.SECRET_KEY, algorithm=_ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": datetime.now(timezone.utc) + _REFRESH_EXPIRE},
        settings.SECRET_KEY, algorithm=_ALGORITHM,
    )


def create_oauth_code(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "oauth_code", "exp": datetime.now(timezone.utc) + _OAUTH_CODE_EXPIRE},
        settings.SECRET_KEY, algorithm=_ALGORITHM,
    )


def decode_token(token: str, expected_type: str = "access") -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None


def decode_oauth_code(code: str) -> str | None:
    return decode_token(code, expected_type="oauth_code")


# --- Google OAuth ---

def get_google_auth_url() -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(_GOOGLE_SCOPES),
        "prompt": "consent",
        "access_type": "offline",
    }
    return "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)


def exchange_google_code(code: str) -> dict:
    """
    Exchange authorization code lấy id_token từ Google.
    Dùng requests trực tiếp — tránh state mismatch của google-auth-oauthlib Flow.
    Blocking — acceptable cho OAuth flow (tần suất thấp).
    """
    resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    id_token_str = resp.json()["id_token"]

    info = google_id_token.verify_oauth2_token(
        id_token_str,
        GoogleRequest(),
        settings.GOOGLE_CLIENT_ID,
    )
    return {
        "google_id": info["sub"],
        "email": info.get("email", ""),
        "name": info.get("name"),
        "avatar_url": info.get("picture"),
    }


# --- User CRUD ---

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    name: str | None = None,
    avatar_url: str | None = None,
    hashed_password: str | None = None,
    google_id: str | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        name=name,
        avatar_url=avatar_url,
        hashed_password=hashed_password,
        google_id=google_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user