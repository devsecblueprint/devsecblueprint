"""BackgroundTasks wrappers for Discord sync operations.

Provides enqueue_discord_sync() which is called by Stripe webhook handlers,
Discord link handlers, and admin sync handlers to trigger Discord role
synchronization without blocking the HTTP response.

Now uses sync_discord_access which includes auto-enrollment for non-guild members.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import asyncio
import logging

from fastapi import BackgroundTasks

from app.dependencies import get_settings
from app.services.discord_sync import sync_discord_access

logger = logging.getLogger("app.background.discord")


def enqueue_discord_sync(
    background_tasks: BackgroundTasks,
    user_id: str,
    operation: str,
    reason: str = "",
) -> None:
    """Enqueue a Discord sync operation as a FastAPI background task.

    Args:
        background_tasks: FastAPI BackgroundTasks instance from the request.
        user_id: DSB user identifier to sync.
        operation: Type of operation triggering the sync
            (e.g., "stripe_webhook", "discord_link", "admin_sync").
        reason: Human-readable reason for the sync.
    """
    background_tasks.add_task(_run_sync, user_id, operation, reason)


async def _run_sync(user_id: str, operation: str, reason: str) -> None:
    """Execute Discord sync via sync_discord_access. Logs errors without re-raising.

    This runs as a background task after the HTTP response has been sent.
    Errors are logged but never propagated back to the HTTP layer.

    Uses sync_discord_access which includes auto-enrollment for users not in guild.

    Requirements: 5.4, 5.5
    """
    try:
        settings = get_settings()
        logger.info(
            "Starting Discord sync: user=%s, operation=%s, reason=%s",
            user_id,
            operation,
            reason,
        )
        # Run synchronous sync_discord_access in a thread
        result = await asyncio.to_thread(sync_discord_access, user_id, settings)
        logger.info(
            "Discord sync completed",
            extra={
                "user_id": user_id,
                "operation": operation,
                "sync_status": result.sync_status,
                "guild_action": result.guild_action,
                "roles_added": len(result.roles_added),
                "roles_removed": len(result.roles_removed),
                "error_code": result.error_code,
            },
        )
    except Exception as exc:
        logger.error(
            "Discord sync failed",
            extra={
                "user_id": user_id,
                "operation": operation,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
