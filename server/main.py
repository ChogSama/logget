from contextlib import asynccontextmanager
from fastapi import FastAPI
from server.database import engine, Base
from server.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(items.router)


@app.get("/health")
async def health():
    return {"status": "ok"}