"""
Pydantic schemas — auth endpoints.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    name: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthCodeRequest(BaseModel):
    code: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"