"""
Kịch bản kiểm tra tích hợp cốt lõi.
"""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:mock@localhost:5432/db"
os.environ["SECRET_KEY"] = "mock_secret"
os.environ["GOOGLE_CLIENT_ID"] = "mock_client"
os.environ["GOOGLE_CLIENT_SECRET"] = "mock_secret"
os.environ["GOOGLE_REDIRECT_URI"] = "mock_uri"
os.environ["CLOUDINARY_CLOUD_NAME"] = "mock_cloud"
os.environ["CLOUDINARY_API_KEY"] = "mock_key"
os.environ["CLOUDINARY_API_SECRET"] = "mock_secret"
os.environ["GEMINI_API_KEY"] = "mock_gemini"
os.environ["FRONTEND_URL"] = "http://localhost"


async def check():
    from server.config import settings
    assert settings.GEMINI_API_KEY == "mock_gemini"

    from server.main import app
    async with app.router.lifespan_context(app):
        assert app.state.gemini is not None

    from server.database import get_db
    db_gen = get_db()
    session = await db_gen.__anext__()
    assert session is not None
    await db_gen.aclose()

    from fastapi import HTTPException
    from server.dependencies import get_current_user

    mock_db = AsyncMock()
    mock_cred = MagicMock()
    
    mock_cred.credentials = "valid"
    assert await get_current_user(mock_cred, mock_db) == "mock_user"

    mock_cred.credentials = "invalid"
    try:
        await get_current_user(mock_cred, mock_db)
        raise AssertionError("Failed")
    except HTTPException as e:
        assert e.status_code == 401

    print("SUCCESS: Core files operate correctly.")

if __name__ == "__main__":
    asyncio.run(check())