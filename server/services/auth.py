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

    OAUTHLIB_INSECURE_TRANSPORT=1: bypass HTTPS check trên redirect URI. An toàn vì
    bảo mật thực nằm ở server-side code exchange, không phải redirect URI scheme.

Password: pwdlib[bcrypt]
CRUD: get_user_by_email, get_user_by_id, get_user_by_google_id, create_user
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from google_auth_oauthlib.flow import Flow
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import settings
from server.models.user import User

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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

def _make_google_flow() -> Flow:
    config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(config, scopes=_GOOGLE_SCOPES, redirect_uri=settings.GOOGLE_REDIRECT_URI)


def get_google_auth_url() -> str:
    url, _ = _make_google_flow().authorization_url(prompt="consent")
    return url


def exchange_google_code(code: str) -> dict:
    """Return {google_id, email, name, avatar_url}. Blocking — acceptable cho OAuth flow."""
    flow = _make_google_flow()
    flow.fetch_token(code=code)
    info = google_id_token.verify_oauth2_token(
        flow.credentials.id_token,
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