"""
Khởi tạo ứng dụng FastAPI, cấu hình middleware và vòng đời lifespan.
"""
import cloudinary
from google import genai
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import settings
from server.routers.auth import router as auth_router
from server.routers.logs import router as logs_router
from server.routers.insights import router as insights_router
from server.routers.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )
    app.state.gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(logs_router)
app.include_router(insights_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    return {"status": "ok"}