"""FastAPI application entry point.

Creates the app instance with lifespan management (apscheduler start/stop),
attaches middleware (CORS, structured logging, error handling), and registers
all routers.

All imports are from the app.* namespace — no sys.path manipulation needed.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.background.scheduler import run_reconciliation, run_credential_expiry_check
from app.middleware.cors import setup_cors
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import setup_exception_handlers
from app.services.video_sync_service import run_video_sync
from app.routers import (
    health,
    auth,
    progress,
    user,
    discord,
    stripe,
    admin,
    content,
    refresh,
    contact,
    public,
    certification,
    certification_admin,
    videos,
    videos_admin,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    Startup: starts the apscheduler for periodic Discord reconciliation.
    Shutdown: gracefully stops the scheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_reconciliation,
        "interval",
        minutes=5,
        id="discord_reconciliation",
    )
    scheduler.add_job(
        run_credential_expiry_check,
        "interval",
        hours=24,
        id="credential_expiry_check",
    )
    scheduler.add_job(
        run_video_sync,
        "interval",
        minutes=10,
        id="video_sync",
    )
    # Run sync once at startup to catch any new videos immediately
    scheduler.add_job(
        run_video_sync,
        "date",
        id="video_sync_startup",
    )
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="DSB Platform API", lifespan=lifespan)

# Middleware (order matters: last added = first executed)
setup_cors(app)
app.add_middleware(LoggingMiddleware)
setup_exception_handlers(app)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(progress.router)
app.include_router(user.router)
app.include_router(discord.router)
app.include_router(stripe.router)
app.include_router(admin.router)
app.include_router(content.router)
app.include_router(refresh.router)
app.include_router(contact.router)
app.include_router(public.router)
app.include_router(certification.router)
app.include_router(certification_admin.router)
app.include_router(videos.router)
app.include_router(videos_admin.router)
