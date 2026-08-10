import asyncio
import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.tasks import start_booking_sweeper
from app.db.session import engine

# Ensure media directory exists before mounting
MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    # 1. Uygulama Baslarken (Startup): Arka plan gorevini atesle
    sweeper_task = asyncio.create_task(start_booking_sweeper())

    yield  # FastAPI gelen istekleri bu arada karsilar

    # 2. Uygulama Kapanirken (Shutdown): Gorevi guvenlice oldur
    sweeper_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await sweeper_task

    await engine.dispose()


app = FastAPI(
    title="Çorlu Travel & Armonitex Booking API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
