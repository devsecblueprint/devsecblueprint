"""BackgroundTasks wrappers for Discord sync operations.

Provides enqueue_discord_sync() which is called by Stripe webhook handlers,
Discord link handlers, and admin sync handlers to trigger Discord role
synchronization without blocking the HTTP response.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import logging

from fastapi import BackgroundTasks

from app.services.discord_sync import perform_sync

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
    """Execute Discord sync. Logs errors without re-raising.

    This runs as a background task after the HTTP response has been sent.
    Errors are logged but never propagated back to the HTTP layer.

    Requirements: 5.4, 5.5
    """
    try:
        result = await perform_sync(user_id=user_id, operation=operation, reason=reason)
        logger.info(
            "Discord sync completed",
            extra={
                "user_id": user_id,
                "operation": operation,
                "status": result.get("status"),
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
