"""FastAPI application entry point.

Creates the app instance with lifespan management (apscheduler start/stop),
attaches middleware (CORS, structured logging, error handling), and registers
all routers.

All imports are from the app.* namespace — no sys.path manipulation needed.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.background.scheduler import run_reconciliation
from app.middleware.cors import setup_cors
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import setup_exception_handlers
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
        minutes=1,
        id="discord_reconciliation",
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
